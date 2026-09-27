"""
scripts/run_dual_judge_baselines.py — Phase 2 Dual-Judge Baseline & Before-Control Evaluation
=============================================================================================
Evaluates:
  1. The 1,400 immutable baseline answers (Direct_LLM, Flat_Vector_RAG, GraphRAG_Adapted, HippoRAG_Adapted)
  2. The 350 legacy TERRA answers (as the diagnostic 'before' control for Category A lift analysis)
Evaluated across two independent foundation model families:
  - Judge 1: databricks-qwen3-next-80b-a3b-instruct
  - Judge 2: databricks-gpt-oss-120b

Safeguards:
  - 2-3 retries with exponential backoff on invalid/malformed JSON.
  - Failure preservation (never drops rows; writes judge_error=True with raw error to preserve denominator).
  - Atomic, row-by-row incremental disk checkpointing.
  - Automatic resumption skipping already-judged (query_id, pipeline) pairs.
  - Strict audit assertion on _judge_fallback_contaminated == False.
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

SOURCE_FILE = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
BASELINES_CHECKPOINT = os.path.join(ROOT_DIR, "scratch", "baselines_1400_dual_judged.json")
LEGACY_CONTROL_CHECKPOINT = os.path.join(ROOT_DIR, "scratch", "terra_350_legacy_before_control.json")

JUDGE_QWEN = "databricks-qwen3-next-80b-a3b-instruct"
JUDGE_GPT_OSS = "databricks-gpt-oss-120b"

NON_TERRA_PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted"
]

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
            
            # Validation check: must have valid likert scores and not be an unhandled error
            if res.get("judge_error") is not True and res.get("faithfulness_likert") is not None and res.get("relevance_likert") is not None:
                return res
            
            print(f"  [RETRY {attempt+1}/{max_retries}] Judge '{judge_model}' returned invalid/missing score. Retrying in {(attempt+1)*2}s...")
            time.sleep((attempt + 1) * 2)
        except Exception as e:
            print(f"  [RETRY {attempt+1}/{max_retries}] Judge '{judge_model}' threw exception: {e}. Retrying in {(attempt+1)*2}s...")
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
            
    # If all retries exhausted, preserve row with judge_error=True
    print(f"  🚨 [FAILURE PRESERVED] Judge '{judge_model}' failed after {max_retries} attempts. Preserving error row.")
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

def run_phase2(limit: int = None, run_control_only: bool = False, run_baselines_only: bool = False):
    print("=" * 80)
    print("PHASE 2: DUAL-JUDGE BASELINE & 'BEFORE' CONTROL EVALUATION")
    print("=" * 80)
    
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    print(f"Loaded {len(all_data)} records from {SOURCE_FILE}")
    
    # ── PART A: 1,400 Immutable Baseline Answers ────────────────────────────
    if not run_control_only:
        baseline_rows = [r for r in all_data if r.get("pipeline") in NON_TERRA_PIPELINES]
        if limit:
            baseline_rows = baseline_rows[:limit]
        print(f"\n[PART A] Processing {len(baseline_rows)} Baseline Answers...")
        
        existing_baselines = load_checkpoint(BASELINES_CHECKPOINT)
        done_keys = set((r["query_id"], r["pipeline"]) for r in existing_baselines)
        print(f"  Checkpoint: {len(existing_baselines)} already completed on disk.")
        
        baselines_out = list(existing_baselines)
        
        for idx, row in enumerate(baseline_rows):
            qid = row.get("query_id")
            pipe = row.get("pipeline")
            key = (qid, pipe)
            if key in done_keys:
                continue
                
            query = row.get("query", "")
            ans = row.get("answer_full") or row.get("answer", "")
            ctx = row.get("context_full") or row.get("context", "")
            cat = row.get("category", "")
            is_direct = (pipe == "1_Direct_LLM") or (ctx == "Direct LLM (No RAG Context)")
            
            print(f"[{idx+1}/{len(baseline_rows)}] {qid} | {pipe} | Evaluating...")
            t0 = time.time()
            
            # Judge 1: Qwen 3 80B
            qwen_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_QWEN)
            assert qwen_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on Qwen for {key}!"
            
            # Judge 2: GPT-OSS 120B
            gpt_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_GPT_OSS)
            assert gpt_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on GPT-OSS for {key}!"
            
            elapsed = round((time.time() - t0), 2)
            print(f"  -> Qwen: F={qwen_res.get('faithfulness_likert')} R={qwen_res.get('relevance_likert')} | GPT: F={gpt_res.get('faithfulness_likert')} R={gpt_res.get('relevance_likert')} ({elapsed}s)")
            
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
            
            baselines_out.append(record)
            done_keys.add(key)
            
            # Save checkpoint every row
            atomic_save(baselines_out, BASELINES_CHECKPOINT)
            
        print(f"[PART A DONE] {len(baselines_out)} records saved to {BASELINES_CHECKPOINT}")

    # ── PART B: 350 Legacy TERRA Answers (Before Control) ───────────────────
    if not run_baselines_only:
        legacy_rows = [r for r in all_data if r.get("pipeline") == "5_Full_TERRA"]
        if limit:
            legacy_rows = legacy_rows[:limit]
        print(f"\n[PART B] Processing {len(legacy_rows)} Legacy TERRA Answers (Before-Control Baseline)...")
        
        existing_control = load_checkpoint(LEGACY_CONTROL_CHECKPOINT)
        control_done_keys = set((r["query_id"], r["pipeline"]) for r in existing_control)
        print(f"  Checkpoint: {len(existing_control)} already completed on disk.")
        
        control_out = list(existing_control)
        
        for idx, row in enumerate(legacy_rows):
            qid = row.get("query_id")
            pipe = row.get("pipeline")
            key = (qid, pipe)
            if key in control_done_keys:
                continue
                
            query = row.get("query", "")
            ans = row.get("answer_full") or row.get("answer", "")
            ctx = row.get("context_full") or row.get("context", "")
            is_direct = (ctx == "Direct LLM (No RAG Context)")
            
            print(f"[{idx+1}/{len(legacy_rows)}] {qid} | Legacy TERRA | Evaluating...")
            t0 = time.time()
            
            # Judge 1: Qwen 3 80B
            qwen_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_QWEN)
            assert qwen_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on Qwen for {key}!"
            
            # Judge 2: GPT-OSS 120B
            gpt_res = evaluate_with_retry(query, ctx, ans, is_direct, JUDGE_GPT_OSS)
            assert gpt_res.get("_judge_fallback_contaminated") is False, f"Contamination detected on GPT-OSS for {key}!"
            
            elapsed = round((time.time() - t0), 2)
            print(f"  -> Qwen: F={qwen_res.get('faithfulness_likert')} R={qwen_res.get('relevance_likert')} | GPT: F={gpt_res.get('faithfulness_likert')} R={gpt_res.get('relevance_likert')} ({elapsed}s)")
            
            record = dict(row)
            record["_diagnostic_control"] = True
            record["_architecture"] = "legacy_zero_retrieval_fast_path"
            
            record["qwen_faithfulness"] = qwen_res.get("faithfulness_score")
            record["qwen_faithfulness_likert"] = qwen_res.get("faithfulness_likert")
            record["qwen_faithfulness_reasoning"] = qwen_res.get("faithfulness_reasoning")
            record["qwen_relevance"] = qwen_res.get("relevance_score")
            record["qwen_relevance_likert"] = qwen_res.get("relevance_likert")
            record["qwen_relevance_reasoning"] = qwen_res.get("relevance_reasoning")
            record["qwen_judge_error"] = qwen_res.get("judge_error", False)
            record["qwen_judge_model"] = qwen_res.get("_judge_model_used")
            record["qwen_contaminated"] = qwen_res.get("_judge_fallback_contaminated", False)
            
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
            
            control_out.append(record)
            control_done_keys.add(key)
            
            atomic_save(control_out, LEGACY_CONTROL_CHECKPOINT)
            
        print(f"[PART B DONE] {len(control_out)} records saved to {LEGACY_CONTROL_CHECKPOINT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2 Dual Judge Baseline Runner")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows for testing")
    parser.add_argument("--control-only", action="store_true", help="Run only Part B (Legacy TERRA Before Control)")
    parser.add_argument("--baselines-only", action="store_true", help="Run only Part A (1,400 Baselines)")
    args = parser.parse_args()
    
    run_phase2(limit=args.limit, run_control_only=args.control_only, run_baselines_only=args.baselines_only)
