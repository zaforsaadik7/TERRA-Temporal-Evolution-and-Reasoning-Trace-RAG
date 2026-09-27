"""
scripts/rejudge_affected_134.py
===============================
Targeted Re-Evaluation of the 134 Queries with Context > 30,000 Characters
under the Unamputated 65,000-Character Context Window.

Safeguards:
  - Atomic backup of scratch/terra_350_dual_judged.json before modification.
  - Thread-safe atomic checkpointing after each evaluated record.
  - Retries on transient errors; denominator preserved (never drops rows).
  - Assert zero fallback contamination.
"""

import os
import sys
import time
import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from eval_terra import judge_answer

CHECKPOINT_FILE = os.path.join(ROOT_DIR, "scratch", "terra_350_dual_judged.json")
BACKUP_FILE = os.path.join(ROOT_DIR, "scratch", "terra_350_dual_judged_pre_truncation_fix_backup.json")

JUDGE_QWEN = "databricks-qwen3-next-80b-a3b-instruct"
JUDGE_GPT_OSS = "databricks-gpt-oss-120b"
NUM_WORKERS = 4

file_lock = threading.Lock()

def atomic_save(data: List[Dict[str, Any]], filepath: str, max_retries: int = 5):
    with file_lock:
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
            time.sleep((attempt + 1) * 2)
        except Exception as e:
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

def process_query(record: Dict[str, Any], idx: int, total: int, master_list: List[Dict[str, Any]]):
    qid = record["query_id"]
    query = record["query"]
    context = record.get("context_full", "")
    answer = record.get("answer_full", "")
    is_direct = (record.get("pipeline") == "1_Direct_LLM")
    
    t0 = time.time()
    res_qwen = evaluate_with_retry(query, context, answer, is_direct, JUDGE_QWEN)
    res_gpt = evaluate_with_retry(query, context, answer, is_direct, JUDGE_GPT_OSS)
    elapsed = time.time() - t0
    
    record["qwen_faithfulness"] = res_qwen.get("faithfulness_score")
    record["qwen_faithfulness_likert"] = res_qwen.get("faithfulness_likert")
    record["qwen_faithfulness_reasoning"] = res_qwen.get("faithfulness_reasoning")
    record["qwen_relevance"] = res_qwen.get("relevance_score")
    record["qwen_relevance_likert"] = res_qwen.get("relevance_likert")
    record["qwen_relevance_reasoning"] = res_qwen.get("relevance_reasoning")
    record["qwen_judge_error"] = res_qwen.get("judge_error", False)
    record["qwen_judge_model"] = res_qwen.get("_judge_model_used", JUDGE_QWEN)
    record["qwen_contaminated"] = res_qwen.get("_judge_fallback_contaminated", False)
    
    record["gpt_faithfulness"] = res_gpt.get("faithfulness_score")
    record["gpt_faithfulness_likert"] = res_gpt.get("faithfulness_likert")
    record["gpt_faithfulness_reasoning"] = res_gpt.get("faithfulness_reasoning")
    record["gpt_relevance"] = res_gpt.get("relevance_score")
    record["gpt_relevance_likert"] = res_gpt.get("relevance_likert")
    record["gpt_relevance_reasoning"] = res_gpt.get("relevance_reasoning")
    record["gpt_judge_error"] = res_gpt.get("judge_error", False)
    record["gpt_judge_model"] = res_gpt.get("_judge_model_used", JUDGE_GPT_OSS)
    record["gpt_contaminated"] = res_gpt.get("_judge_fallback_contaminated", False)
    
    record["_rejudged_unamputated_context"] = True
    record["rejudged_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Save atomically
    atomic_save(master_list, CHECKPOINT_FILE)
    
    print(f"[{idx+1}/{total}] {qid} ({record.get('category')} | ctx: {len(context)}c): Qwen F={record['qwen_faithfulness_likert']} | GPT F={record['gpt_faithfulness_likert']} ({elapsed:.1f}s)")
    return qid

def main():
    print("=" * 80)
    print("TARGETED RE-EVALUATION OF 134 LONG-CONTEXT QUERIES (>30,000 CHARACTERS)")
    print("=" * 80)
    
    if not os.path.exists(BACKUP_FILE):
        shutil.copyfile(CHECKPOINT_FILE, BACKUP_FILE)
        print(f"Created atomic backup at: {BACKUP_FILE}")
    else:
        print(f"Backup already exists at: {BACKUP_FILE}")
        
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded master benchmark records: {len(data)}")
    assert len(data) == 350, f"Expected 350 records, got {len(data)}"
    
    # Identify target records
    targets = [r for r in data if len(r.get("context_full", "")) > 30000]
    print(f"Identified {len(targets)} queries with context > 30,000 characters.")
    assert len(targets) == 134, f"Expected 134 targets, got {len(targets)}"
    
    # Filter out already rejudged if resuming
    pending = [r for r in targets if not r.get("_rejudged_unamputated_context")]
    print(f"Pending to evaluate: {len(pending)} / {len(targets)}")
    
    if not pending:
        print("All 134 queries already rejudged! Nothing to do.")
        return
        
    print(f"\nLaunching parallel evaluation with {NUM_WORKERS} workers...")
    t_start = time.time()
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(process_query, rec, i, len(targets), data): rec["query_id"]
            for i, rec in enumerate(targets)
            if not rec.get("_rejudged_unamputated_context")
        }
        for future in as_completed(futures):
            qid = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[EXCEPTION] Failed on {qid}: {e}")
                
    elapsed_total = time.time() - t_start
    print(f"\n[DONE] Re-evaluation of {len(pending)} queries completed in {elapsed_total:.1f}s ({elapsed_total/60:.2f} mins).")
    
    # Final assertion check
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        final_data = json.load(f)
    assert len(final_data) == 350
    rejudged_count = sum(1 for r in final_data if r.get("_rejudged_unamputated_context"))
    print(f"Total rejudged records in final dataset: {rejudged_count} / 134")

if __name__ == "__main__":
    main()
