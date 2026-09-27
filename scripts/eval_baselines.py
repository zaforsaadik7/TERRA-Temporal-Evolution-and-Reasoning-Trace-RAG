"""
scripts/eval_baselines.py - Canonical Full-Scale 350-Query Benchmark Runner
============================================================================
Executes the full 350 pre-registered benchmark queries across all 5 pipelines:
  1. 1_Direct_LLM
  2. 2_Flat_Vector_RAG
  3. 3_GraphRAG_Adapted
  4. 4_HippoRAG_Adapted
  5. 5_Full_TERRA

Features:
  - 100% shared execution logic via baselines.runner_core
  - Strict sequential execution eliminating ChromaDB lock contention and JSONL interleaving
  - Atomic per-query checkpointing to terra_baselines_eval_raw.json
  - Support for --max-queries (hard stop for Stage 1 human review)
  - Seamless --resume capability picking up from exact last completed query
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Enforce 20k corpus paths
os.environ["TERRA_GRAPH_PATH"] = os.path.join(ROOT_DIR, "dataset_20k_cap", "terra_eeg_index_20k.json")
os.environ["TERRA_VECTOR_DB_PATH"] = os.path.join(ROOT_DIR, "dataset_20k_cap", "vector_db_20k")

from baselines.runner_core import (
    EvaluationEngines,
    execute_pipeline,
    atomic_save,
    PIPELINE_NAMES
)

DEFAULT_BENCHMARK = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
DEFAULT_OUTPUT = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")


def main():
    parser = argparse.ArgumentParser(description="TERRA 350-Query Comparative Baselines Benchmark Runner")
    parser.add_argument("--benchmark", type=str, default=DEFAULT_BENCHMARK, help="Path to 350-query benchmark JSON")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="Path to raw output evaluation JSON")
    parser.add_argument("--max-queries", type=int, default=None, help="Maximum number of queries to process before hard exit")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing checkpoint (default: True)")
    parser.add_argument("--no-resume", action="store_true", help="Overwrite existing checkpoint instead of resuming")
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("TERRA WORKSTREAM 1.2: FULL 350-QUERY COMPARATIVE BENCHMARK RUNNER")
    print("=" * 80)

    # 1. Load Benchmark Queries
    if not os.path.exists(args.benchmark):
        raise FileNotFoundError(f"Benchmark file not found: {args.benchmark}")
    with open(args.benchmark, "r", encoding="utf-8") as f:
        all_queries = json.load(f)
    print(f"Loaded {len(all_queries)} canonical benchmark queries from {args.benchmark}.")

    # 2. Checkpoint Loading & Resumption Accounting
    results = []
    completed_qids = set()
    if not args.no_resume and os.path.exists(args.output):
        try:
            with open(args.output, "r", encoding="utf-8") as f:
                results = json.load(f)
            # A query is completed only if all 5 pipelines have valid records
            from collections import Counter
            q_counts = Counter(r["query_id"] for r in results)
            completed_qids = {qid for qid, count in q_counts.items() if count == len(PIPELINE_NAMES)}
            print(f"Resuming from checkpoint: {len(results)} records ({len(completed_qids)} fully completed queries).")
        except Exception as e:
            print(f"[WARN] Failed to parse existing checkpoint: {e}. Starting fresh.")
            results = []
            completed_qids = set()

    # 3. Filter queries to run
    queries_to_run = [q for q in all_queries if q["query_id"] not in completed_qids]
    print(f"Queries remaining to execute: {len(queries_to_run)} / {len(all_queries)}")

    if not queries_to_run:
        print("\n>>> ALL 350 QUERIES ALREADY FULLY COMPLETED IN CHECKPOINT. <<<")
        print(f"Output file: {args.output} ({len(results)} total records).")
        return

    # 4. Initialize Shared Inference Engines
    engines = EvaluationEngines()

    # 5. Sequential Execution Loop
    run_start_time = time.time()
    queries_processed_this_run = 0

    print("\n" + "-" * 80)
    print(f"STARTING SEQUENTIAL EXECUTION (Mode: {'Stage 1 (Limit: ' + str(args.max_queries) + ')' if args.max_queries else 'Full Run'})")
    print("-" * 80)

    for q_idx, q_data in enumerate(queries_to_run, 1):
        if args.max_queries is not None and queries_processed_this_run >= args.max_queries:
            print(f"\n[HARD STOP REACHED] Reached requested limit of {args.max_queries} queries for this session.")
            break

        qid = q_data["query_id"]
        cat = q_data["category"]
        subtype = q_data.get("adversarial_subtype") or q_data.get("subtype")
        q_text = q_data["query"]

        print(f"\n[{q_idx}/{len(queries_to_run)}] Query {qid} ({cat} | {subtype})")
        print(f" Text: {q_text[:75]}...")

        # AMENDMENT H CODE-LEVEL PROTOCOL GATE:
        # Category C is strictly blocked until Category B is fully certified and B041 is permanently patched
        if cat == "C_OutOfContext":
            b041_rec = next((r for r in results if r.get("query_id") == "B041" and r.get("pipeline") == "5_Full_TERRA"), None)
            lock_path = os.path.join(ROOT_DIR, "Paper", "audit", "AMENDMENT_H_VERIFIED.lock")
            if not b041_rec or b041_rec.get("judge_error") is True or b041_rec.get("faithfulness") is None:
                print("\n" + "!" * 80)
                print("[FATAL PROTOCOL GATE] AMENDMENT H INVARIANT VIOLATION:")
                print("Query B041 (5_Full_TERRA) contains judge_error=True or null faithfulness score!")
                print("Category C execution is strictly blocked by protocol gate. Halting runner.")
                print("!" * 80 + "\n")
                sys.exit(1)
            if not os.path.exists(lock_path):
                print("\n" + "!" * 80)
                print("[FATAL PROTOCOL GATE] AMENDMENT H INVARIANT VIOLATION:")
                print("Paper/audit/AMENDMENT_H_VERIFIED.lock does not exist.")
                print("Category B closeout has not been certified. Halting runner.")
                print("!" * 80 + "\n")
                sys.exit(1)

        # Process each pipeline
        for pipeline in PIPELINE_NAMES:
            # Check if this specific (qid, pipeline) pair is already in results
            existing_idx = next((i for i, r in enumerate(results) if r["query_id"] == qid and r["pipeline"] == pipeline), None)
            if existing_idx is not None:
                print(f"   -> Pipeline {pipeline}: already in checkpoint. Skipping.")
                continue

            print(f"   -> Executing Pipeline: {pipeline}...")
            record = execute_pipeline(pipeline, q_data, engines)

            # Update or append
            if existing_idx is not None:
                results[existing_idx] = record
            else:
                results.append(record)

            # Telemetry print
            ans_snip = record["answer_full"][:70].replace('\n', ' ')
            tot_ms = record["timing"].get("total_ms", 0.0)
            gen_ms = record["timing"].get("generation_ms", 0.0)
            f_lik = record.get("faithfulness_likert")
            r_lik = record.get("relevance_likert")
            refused = record.get("safety_rejected")
            print(f"      [F: {f_lik}/5 | R: {r_lik}/5 | Refusal: {refused} | Gen: {gen_ms}ms | Tot: {tot_ms}ms] Ans: {ans_snip}...")

        # Atomic save after completing all 5 pipelines for this query
        atomic_save(results, args.output)
        queries_processed_this_run += 1
        print(f" -> Query {qid} completed & checkpointed. Total records: {len(results)}.")

    elapsed = round(time.time() - run_start_time, 2)
    print("\n" + "=" * 80)
    print(f"SESSION FINISHED in {elapsed}s (~{round(elapsed/60, 2)} mins).")
    print(f"Queries processed this session: {queries_processed_this_run}")
    print(f"Total records in {args.output}: {len(results)}")
    print("=" * 80 + "\n")

    if args.max_queries is not None and queries_processed_this_run >= args.max_queries:
        print(">>> HARD STOP COMPLETE: Stage 1 checkpoint reached. Exiting cleanly for human review. <<<")
        sys.exit(0)


if __name__ == "__main__":
    main()
