"""
scripts/eval_baselines_pilot.py - Workstream 1.2 Phase 2 Pilot Smoke Test Runner
================================================================================
Executes the pre-registered 10 stratified queries across all 5 pipelines:
  1. 1_Direct_LLM
  2. 2_Flat_Vector_RAG
  3. 3_GraphRAG_Adapted
  4. 4_HippoRAG_Adapted
  5. 5_Full_TERRA

Features:
  - 100% shared execution logic via baselines.runner_core
  - Strict PayloadParityInterceptor routing for all inference calls
  - LLaMA 3.3 70B Skeptical Critic Judge with 1-5 Likert score parsing
  - Atomic per-query checkpointing to terra_pilot_smoke_test_raw.json
  - Sequential per-query execution to maintain clean latency isolation
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Enforce 20k corpus paths for TERRA
os.environ["TERRA_GRAPH_PATH"] = os.path.join(ROOT_DIR, "dataset_20k_cap", "terra_eeg_index_20k.json")
os.environ["TERRA_VECTOR_DB_PATH"] = os.path.join(ROOT_DIR, "dataset_20k_cap", "vector_db_20k")

from baselines.runner_core import (
    EvaluationEngines,
    execute_pipeline,
    atomic_save,
    PIPELINE_NAMES
)

PILOT_QUERY_IDS = [
    "A001", "A005",  # Category A: Single-point factual
    "B005", "B081",  # Category B: 3-node shallow & 5-node deep multi-hop
    "C031", "C001",  # Category C: Near-OOD municipal & Far-OOD astrophysics
    "D001", "D020", "D039", "D058"  # Category D: D1, D2, D3, D4 precedent traps
]

BENCHMARK_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
RAW_OUTPUT_PATH = os.path.join(ROOT_DIR, "terra_pilot_smoke_test_raw.json")


def main():
    print("\n" + "=" * 75)
    print("WORKSTREAM 1.2: PHASE 2 PILOT SMOKE TEST RUNNER (10-QUERY STRATIFIED)")
    print("=" * 75)

    # 1. Load benchmark & select 10 pre-registered queries
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        all_bench = json.load(f)
    bench_by_id = {q["query_id"]: q for q in all_bench}

    selected_queries = []
    for qid in PILOT_QUERY_IDS:
        if qid not in bench_by_id:
            raise KeyError(f"Pre-registered query_id '{qid}' not found in {BENCHMARK_PATH}!")
        selected_queries.append(bench_by_id[qid])

    print(f"Loaded {len(selected_queries)} pre-registered pilot queries:")
    for sq in selected_queries:
        st = sq.get("adversarial_subtype") or sq.get("subtype")
        print(f"  [{sq['query_id']}] {sq['category']} ({st}): {sq['query'][:65]}...")

    # 2. Initialize Shared Components
    engines = EvaluationEngines()

    # Check for existing checkpoint
    results = []
    completed_qids = set()
    if os.path.exists(RAW_OUTPUT_PATH):
        try:
            with open(RAW_OUTPUT_PATH, "r", encoding="utf-8") as f:
                results = json.load(f)
            completed_qids = {r["query_id"] for r in results}
            print(f"Resuming from checkpoint: {len(results)} records ({len(completed_qids)} queries completed).")
        except Exception:
            results = []

    print("\n" + "-" * 75)
    print("BEGINNING SEQUENTIAL INFERENCE & EVALUATION ACROSS ALL 5 PIPELINES")
    print("-" * 75)

    total_start_time = time.time()

    for q_idx, q_data in enumerate(selected_queries, 1):
        qid = q_data["query_id"]
        category = q_data["category"]
        subtype = q_data.get("adversarial_subtype") or q_data.get("subtype")
        query_text = q_data["query"]

        print(f"\n[{q_idx}/10] Processing Query {qid} ({category} | {subtype})")
        print(f" Query: {query_text}")

        # Check if already processed
        q_records = [r for r in results if r["query_id"] == qid]
        if len(q_records) == 5:
            print(f" -> Query {qid} already has 5 complete records in checkpoint. Skipping.")
            continue

        for pipeline in PIPELINE_NAMES:
            print(f"   -> Executing Pipeline: {pipeline}...")
            record = execute_pipeline(pipeline, q_data, engines)

            # Update or append record
            existing_idx = next((i for i, r in enumerate(results) if r["query_id"] == qid and r["pipeline"] == pipeline), None)
            if existing_idx is not None:
                results[existing_idx] = record
            else:
                results.append(record)

            ans = record["answer_full"]
            print(f"      Ans ({len(ans)} chars): {ans[:80]}...")
            print(f"      Faithfulness: {record.get('faithfulness_likert')}/5 | Relevance: {record.get('relevance_likert')}/5 | Refusal: {record.get('safety_rejected')} | Total: {record.get('timing', {}).get('total_ms', 0)}ms")

        # Atomic per-query checkpointing
        atomic_save(results, RAW_OUTPUT_PATH)
        print(f" -> Checkpointed Query {qid} to disk ({len(results)} total records persisted).")

    total_elapsed = round(time.time() - total_start_time, 2)
    print("\n" + "=" * 75)
    print(f"PHASE 2 PILOT SMOKE TEST EXECUTION COMPLETE in {total_elapsed}s (~{round(total_elapsed/60, 1)} mins)")
    print(f"Total Records Persisted: {len(results)} in {RAW_OUTPUT_PATH}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
