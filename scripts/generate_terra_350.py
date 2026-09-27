"""
scripts/generate_terra_350.py — Phase 3 Single-Pass Generation for 350 Full TERRA Benchmark
===========================================================================================
Generates all 350 benchmark answers under the updated TERRA architecture:
  - Decoupled Router: databricks-gemma-3-12b
  - Fast Path: Lightweight vector/node retrieval + smart_grader NLI verification gate
  - Slow Path: Deep GraphRAG BFS expansion + smart_grader NLI gate + multi-case synthesis

Outputs:
  - scratch/terra_350_new_generations.json

Telemetry per record:
  - route_taken: "EASY" or "HARD"
  - smart_grader_passed: True or False
  - is_refusal: True or False
  - _router_model_used: "databricks-gemma-3-12b"
  - _router_fallback_contaminated: False
  - full timing dictionary (retrieval_ms, grading_ms, generation_ms, total_ms)
"""

import os
import sys
import time
import json
import argparse
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ask_terra import terra_inference_engine

BENCHMARK_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
OUTPUT_CHECKPOINT = os.path.join(ROOT_DIR, "scratch", "terra_350_new_generations.json")

def load_checkpoint(filepath: str) -> List[Dict[str, Any]]:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[WARN] Failed reading checkpoint {filepath}: {e}")
    return []

def atomic_save(data: List[Dict[str, Any]], filepath: str, max_retries: int = 5):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    temp_path = f"{filepath}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    for attempt in range(max_retries):
        try:
            if os.path.exists(filepath):
                os.replace(temp_path, filepath)
            else:
                os.rename(temp_path, filepath)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[ERROR] Atomic save failed: {e}")
            time.sleep(0.2 * (attempt + 1))

def generate_with_retry(query: str, qid: str, max_retries: int = 3):
    last_err = None
    for attempt in range(max_retries):
        try:
            ans, ctx, timing = terra_inference_engine(query, return_timing=True, query_id=qid)
            if ans and len(ans.strip()) > 0:
                return ans, ctx, timing, False, None
            print(f"  [RETRY {attempt+1}/{max_retries}] Empty answer returned for {qid}. Retrying in {(attempt+1)*2}s...")
            time.sleep((attempt + 1) * 2)
        except Exception as e:
            print(f"  [RETRY {attempt+1}/{max_retries}] Exception on {qid}: {e}. Retrying in {(attempt+1)*2}s...")
            last_err = str(e)
            time.sleep((attempt + 1) * 2)
            
    print(f"  🚨 [GENERATION FAILURE PRESERVED] {qid} failed after {max_retries} attempts.")
    return f"Error: Generation failed after retries: {last_err}", "", {}, True, last_err

def run_generation(limit: int = None):
    print("=" * 80)
    print("PHASE 3: SINGLE-PASS GENERATION FOR 350 FULL TERRA BENCHMARK")
    print("=" * 80)
    
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        bench350 = json.load(f)
    print(f"Loaded {len(bench350)} queries from {BENCHMARK_PATH}")
    
    if limit:
        bench350 = bench350[:limit]
        print(f"Limited execution to {limit} queries.")
        
    existing_gens = load_checkpoint(OUTPUT_CHECKPOINT)
    done_ids = set(r["query_id"] for r in existing_gens)
    print(f"Checkpoint: {len(existing_gens)} already completed on disk.")
    
    records_out = list(existing_gens)
    
    total = len(bench350)
    start_time = time.time()
    
    for idx, q_item in enumerate(bench350):
        qid = q_item["query_id"]
        if qid in done_ids:
            continue
            
        cat = q_item.get("category", "")
        query = q_item["query"]
        
        print(f"\n[{idx+1}/{total}] ({cat}) Ingesting query {qid}: '{query[:60]}...'")
        t0 = time.time()
        
        ans, ctx, timing, has_error, err_msg = generate_with_retry(query, qid)
        elapsed = round((time.time() - t0), 2)
        
        route = timing.get("route_taken", "UNKNOWN")
        passed = timing.get("smart_grader_passed", None)
        refusal = timing.get("is_refusal", False)
        router_model = timing.get("_router_model_used")
        contaminated = timing.get("_router_fallback_contaminated", False)
        
        print(f"  -> Route: {route} (Router: {router_model}, Contam={contaminated})")
        print(f"  -> Smart Grader Passed: {passed} | Refusal: {refusal} | Time: {elapsed}s")
        print(f"  -> Answer Preview: {ans[:90]}...")
        
        record = {
            "query_id": qid,
            "category": cat,
            "subtype": q_item.get("subtype", ""),
            "pipeline": "5_Full_TERRA",
            "query": query,
            "reference": q_item.get("ground_truth_holding") or q_item.get("reference", ""),
            "target_nodes": q_item.get("target_nodes", []),
            "gold_citation_path": q_item.get("gold_citation_path", []),
            "answer_full": ans,
            "context_full": ctx,
            "route_taken": route,
            "smart_grader_passed": passed,
            "is_refusal": refusal,
            "generation_error": has_error,
            "generation_error_msg": err_msg,
            "timing": timing,
            "_router_model_used": router_model,
            "_router_fallback_contaminated": contaminated,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        records_out.append(record)
        done_ids.add(qid)
        
        # Incremental row-by-row checkpointing
        atomic_save(records_out, OUTPUT_CHECKPOINT)
        
    print("\n" + "=" * 80)
    print(f"PHASE 3 GENERATION COMPLETE: {len(records_out)}/{len(bench350)} on disk.")
    easy_count = sum(1 for r in records_out if r.get("route_taken") == "EASY")
    hard_count = sum(1 for r in records_out if r.get("route_taken") == "HARD")
    refusal_count = sum(1 for r in records_out if r.get("is_refusal"))
    easy_refusals = sum(1 for r in records_out if r.get("route_taken") == "EASY" and r.get("is_refusal"))
    print(f"Routing Distribution: EASY={easy_count} | HARD={hard_count}")
    print(f"Refusals: Total={refusal_count} | EASY Refusals={easy_refusals} ({easy_refusals/easy_count*100:.1f}% of EASY)" if easy_count > 0 else "")
    print(f"Saved checkpoint to: {OUTPUT_CHECKPOINT}")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3 TERRA 350 Generation Runner")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of queries")
    args = parser.parse_args()
    
    run_generation(limit=args.limit)
