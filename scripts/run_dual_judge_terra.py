"""
scripts/run_dual_judge_terra.py — Phase 4 Dual-Judge Evaluation of New 350 Full TERRA Answers
=============================================================================================
Evaluates the 350 newly generated Full TERRA benchmark answers across two independent judges:
  - Judge 1: databricks-qwen3-next-80b-a3b-instruct
  - Judge 2: databricks-gpt-oss-120b

Safeguards:
  - 2-3 retries on transient errors / malformed JSON.
  - Denominator preservation (writes judge_error=True on unresolvable failure; never drops rows).
  - Row-by-row atomic checkpointing to scratch/terra_350_dual_judged.json.
  - Automatic resumption skipping already-evaluated query_ids.
  - Strict audit assertion: _judge_fallback_contaminated is False.
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

from eval_terra import judge_answer

SOURCE_FILE = os.path.join(ROOT_DIR, "scratch", "terra_350_new_generations.json")
CHECKPOINT_FILE = os.path.join(ROOT_DIR, "scratch", "terra_350_dual_judged.json")

JUDGE_QWEN = "databricks-qwen3-next-80b-a3b-instruct"
JUDGE_GPT_OSS = "databricks-gpt-oss-120b"

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

def evaluate_with_retry(
    query: str,
    context: str,
    answer: str,
    is_direct: bool,
    judge_model: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    last_res = None
    for attempt in range(max_retries):
        try:
            res = judge_answer(
                query=query,
                context=context,
                answer=answer,
                is_direct_llm=is_direct,
                judge_model_override=judge_model
            )
            last_res = res
            if res.get("judge_error") is not True and res.get("faithfulness_likert") is not None and res.get("relevance_likert") is not None:
                return res
            print(f"  [RETRY {attempt+1}/{max_retries}] Judge '{judge_model}' returned invalid score. Retrying...")
            time.sleep((attempt + 1) * 2)
        except Exception as e:
            print(f"  [RETRY {attempt+1}/{max_retries}] Judge '{judge_model}' threw exception: {e}. Retrying...")
            time.sleep((attempt + 1) * 2)
            last_res = {
                "faithfulness_score": None,
                "faithfulness_likert": None,
                "faithfulness_reasoning": f"EXCEPTION: {e}",
                "relevance_score": None,
                "relevance_likert": None,
                "relevance_reasoning": f"EXCEPTION: {e}",
                "_judge_model_used": judge_model,
                "_judge_fallback_contaminated": False,
                "judge_error": True
            }
            
    print(f"  🚨 [FAILURE PRESERVED] Judge '{judge_model}' failed after {max_retries} attempts.")
    if last_res is None:
        last_res = {
            "faithfulness_score": None,
            "faithfulness_likert": None,
            "faithfulness_reasoning": "Failed after max retries",
            "relevance_score": None,
            "relevance_likert": None,
            "relevance_reasoning": "Failed after max retries",
            "_judge_model_used": judge_model,
            "_judge_fallback_contaminated": False,
            "judge_error": True
        }
    return last_res

def run_judging(limit: int = None):
    print("=" * 80)
    print("PHASE 4: DUAL-JUDGE EVALUATION FOR 350 FULL TERRA ANSWERS")
    print("=" * 80)
    
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        terra_rows = json.load(f)
    print(f"Loaded {len(terra_rows)} new TERRA answers from {SOURCE_FILE}")
    
    if limit:
        terra_rows = terra_rows[:limit]
        print(f"Limited execution to {limit} rows.")
        
    existing_judged = load_checkpoint(CHECKPOINT_FILE)
    done_ids = set(r["query_id"] for r in existing_judged)
    print(f"Checkpoint: {len(existing_judged)} already completed on disk.")
    
    records_out = list(existing_judged)
    total = len(terra_rows)
    
    for idx, row in enumerate(terra_rows):
        qid = row.get("query_id")
        if qid in done_ids:
            continue
            
        cat = row.get("category", "")
        route = row.get("route_taken", "")
        query = row.get("query", "")
        ans = row.get("answer_full", "")
        ctx = row.get("context_full", "")
        is_direct = (ctx == "Direct LLM (No RAG Context)")
        
        print(f"\n[{idx+1}/{total}] ({cat} | Route: {route}) {qid}: Evaluating...")
        sys.stdout.flush()
        t0 = time.time()
        
        # Judge 1: Qwen 3 80B
        qwen_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_QWEN)
        assert qwen_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on Qwen for {qid}!"
        
        # Judge 2: GPT-OSS 120B
        gpt_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_GPT_OSS)
        assert gpt_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on GPT-OSS for {qid}!"
        
        elapsed = round((time.time() - t0), 2)
        print(f"  -> Qwen: F={qwen_res.get('faithfulness_likert')} R={qwen_res.get('relevance_likert')} | GPT: F={gpt_res.get('faithfulness_likert')} R={gpt_res.get('relevance_likert')} ({elapsed}s)")
        sys.stdout.flush()
        
        record = dict(row)
        
        # Store Qwen evaluation
        record["qwen_faithfulness"] = qwen_res.get("faithfulness_score")
        record["qwen_faithfulness_likert"] = qwen_res.get("faithfulness_likert")
        record["qwen_faithfulness_reasoning"] = qwen_res.get("faithfulness_reasoning")
        record["qwen_relevance"] = qwen_res.get("relevance_score")
        record["qwen_relevance_likert"] = qwen_res.get("relevance_likert")
        record["qwen_relevance_reasoning"] = qwen_res.get("relevance_reasoning")
        record["qwen_judge_error"] = qwen_res.get("judge_error", False)
        record["qwen_judge_model"] = qwen_res.get("_judge_model_used")
        record["qwen_contaminated"] = qwen_res.get("_judge_fallback_contaminated", False)
        
        # Store GPT-OSS evaluation
        record["gpt_faithfulness"] = gpt_res.get("faithfulness_score")
        record["gpt_faithfulness_likert"] = gpt_res.get("faithfulness_likert")
        record["gpt_faithfulness_reasoning"] = gpt_res.get("faithfulness_reasoning")
        record["gpt_relevance"] = gpt_res.get("relevance_score")
        record["gpt_relevance_likert"] = gpt_res.get("relevance_likert")
        record["gpt_relevance_reasoning"] = gpt_res.get("relevance_reasoning")
        record["gpt_judge_error"] = gpt_res.get("judge_error", False)
        record["gpt_judge_model"] = gpt_res.get("_judge_model_used")
        record["gpt_contaminated"] = gpt_res.get("_judge_fallback_contaminated", False)
        
        record["dual_judged_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        records_out.append(record)
        done_ids.add(qid)
        
        # Row-by-row checkpointing
        atomic_save(records_out, CHECKPOINT_FILE)
        
    print("\n" + "=" * 80)
    print(f"PHASE 4 COMPLETE: {len(records_out)}/{total} rows evaluated and saved to {CHECKPOINT_FILE}")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 4 Dual Judge Runner for Full TERRA Answers")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows")
    args = parser.parse_args()
    
    run_judging(limit=args.limit)
