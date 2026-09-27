"""
scripts/apply_amendment_g.py - Amendment G: Judge Likert-1 Parsing Inversion Correction
========================================================================================
Formal protocol implementation for Amendment G:
1. Creates immutable backup of terra_baselines_eval_raw.json before modification.
2. Quarantines mid-query uncommitted B008 entries from audit_payloads.jsonl into
   baselines/audit_payloads_amendment_g_superseded.jsonl, restoring 1-to-1 parity.
3. Re-evaluates all non-refusal Likert-5 records using the skeptical critic judge
   under Databricks Llama 3.3 70B with temperature 0.0 and corrected parse_likert.
4. Preserves raw_judge_scores in the updated records for permanent auditability.
5. Produces exact before/after shift tables for Category A and Category B.
6. Atomically updates terra_baselines_eval_raw.json.
"""

import os
import sys
import json
import time
import shutil
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

from baselines.common import get_databricks_client
from baselines.runner_core import judge_single_prompt, parse_likert

RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
BACKUP_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw_pre_amendment_g.json")
AUDIT_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads.jsonl")
AUDIT_BACKUP = os.path.join(ROOT_DIR, "baselines", "audit_payloads_pre_amendment_g.jsonl")
SUPERSEDED_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads_amendment_g_superseded.jsonl")

PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted",
    "5_Full_TERRA"
]


def step1_backups_and_orphan_quarantine():
    print("\n" + "=" * 80)
    print("STEP 1: IMMUTABLE BACKUPS & ORPHAN AUDIT QUARANTINE")
    print("=" * 80)

    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(RAW_PATH, BACKUP_PATH)
        print(f"Backed up raw evaluation file to: {BACKUP_PATH}")
    else:
        print(f"Using existing immutable backup: {BACKUP_PATH}")

    if not os.path.exists(AUDIT_BACKUP):
        shutil.copy2(AUDIT_PATH, AUDIT_BACKUP)
        print(f"Backed up audit payload log to:   {AUDIT_BACKUP}")
    else:
        print(f"Using existing audit backup:     {AUDIT_BACKUP}")

    # Inspect audit payloads
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        audit_entries = [json.loads(line) for line in f if line.strip()]

    # Load raw records from clean backup
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        raw_records = json.load(f)


    print(f"Current raw records: {len(raw_records)}")
    print(f"Current audit entries: {len(audit_entries)}")

    # Uncommitted records are those for queries not fully completed in raw
    from collections import Counter
    q_counts = Counter(r["query_id"] for r in raw_records)
    committed_qids = {qid for qid, count in q_counts.items() if count == len(PIPELINES)}

    active_audit = []
    superseded_audit = []
    for e in audit_entries:
        if e.get("query_id") in committed_qids:
            active_audit.append(e)
        else:
            superseded_audit.append(e)

    print(f"Committed query IDs in raw: {len(committed_qids)}")
    print(f"Active audit entries matching committed queries: {len(active_audit)}")
    print(f"Uncommitted/Orphan entries to quarantine:        {len(superseded_audit)}")

    if superseded_audit:
        with open(SUPERSEDED_PATH, "a", encoding="utf-8") as f:
            for e in superseded_audit:
                e["quarantine_reason"] = "Amendment G: Mid-query task kill uncommitted payload"
                e["quarantined_at"] = datetime.utcnow().isoformat() + "Z"
                f.write(json.dumps(e) + "\n")
        print(f"Appended {len(superseded_audit)} entries to: {SUPERSEDED_PATH}")

        # Rewrite active audit log with exact 1-to-1 parity
        with open(AUDIT_PATH, "w", encoding="utf-8") as f:
            for e in active_audit:
                f.write(json.dumps(e) + "\n")
        print(f"Rewrote {AUDIT_PATH} with {len(active_audit)} active records.")

    print(f"Reconciliation check: {len(active_audit)} == {len(raw_records)} ({'PASS' if len(active_audit) == len(raw_records) else 'FAIL'})")
    return raw_records


CACHE_PATH = os.path.join(ROOT_DIR, "scratch", "amendment_g_rejudge_cache.json")


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            clean = {k: v for k, v in data.items() if not v.get("judge_error") and v.get("faithfulness_likert") is not None}
            return clean
        except Exception:
            return {}
    return {}


def save_cache(cache):
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CACHE_PATH)


def rejudge_worker(record, judge_client, cache):
    qid = record["query_id"]
    pipe = record["pipeline"]
    key = f"{qid}::{pipe}"

    if key in cache:
        return record, cache[key]

    query = record["query"]
    context = record.get("context_full", "")
    answer = record["answer_full"]
    is_direct = (pipe == "1_Direct_LLM") or (context == "Direct LLM (No RAG Context)")


    for attempt in range(4):
        eval_res = judge_single_prompt(
            judge_client=judge_client,
            query=query,
            context=context,
            answer=answer,
            is_direct_llm=is_direct
        )
        if not eval_res.get("judge_error") and eval_res.get("faithfulness_likert") is not None:
            return record, eval_res
        time.sleep(3 * (attempt + 1))

    return record, eval_res


def step2_rejudge_candidates(raw_records):
    print("\n" + "=" * 80, flush=True)
    print("STEP 2: RE-EVALUATION OF CANDIDATE RECORDS UNDER PATCHED PARSER", flush=True)
    print("=" * 80, flush=True)

    judge_client = get_databricks_client()
    cache = load_cache()
    print(f"Loaded {len(cache)} validated evaluations from cache (purged any transient 429s)", flush=True)

    candidate_indices = []
    for idx, r in enumerate(raw_records):
        if not r.get("safety_rejected"):
            if r.get("faithfulness_likert") == 5 or r.get("category") == "B_Evolutionary":
                candidate_indices.append(idx)

    print(f"Total committed records:           {len(raw_records)}", flush=True)
    print(f"Candidate records to re-evaluate:  {len(candidate_indices)}", flush=True)
    remaining_to_call = [idx for idx in candidate_indices if f"{raw_records[idx]['query_id']}::{raw_records[idx]['pipeline']}" not in cache]
    print(f"Remaining calls to execute:        {len(remaining_to_call)}", flush=True)

    corrected_records = list(raw_records)
    changes = []

    print(f"Launching rate-limit-safe re-evaluation (max_workers=3)...", flush=True)
    start_time = time.time()

    cache_dirty = False
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(rejudge_worker, raw_records[i], judge_client, cache): i
            for i in candidate_indices
        }


        completed_count = 0
        for fut in as_completed(futures):
            orig_idx = futures[fut]
            orig_rec, eval_res = fut.result()
            completed_count += 1

            key = f"{orig_rec['query_id']}::{orig_rec['pipeline']}"
            if key not in cache:
                cache[key] = eval_res
                cache_dirty = True
                if completed_count % 10 == 0:
                    save_cache(cache)


            old_likert = orig_rec.get("faithfulness_likert")
            old_faith = orig_rec.get("faithfulness")
            new_likert = eval_res.get("faithfulness_likert")
            new_faith = eval_res.get("faithfulness_score")

            # Check if this record changed
            if old_likert != new_likert or old_faith != new_faith:
                changes.append({
                    "query_id": orig_rec["query_id"],
                    "category": orig_rec["category"],
                    "pipeline": orig_rec["pipeline"],
                    "old_likert": old_likert,
                    "new_likert": new_likert,
                    "old_faith": old_faith,
                    "new_faith": new_faith,
                    "raw_judge_scores": eval_res.get("raw_judge_scores"),
                    "reasoning_snippet": eval_res.get("faithfulness_reasoning", "")[:100]
                })

            # Update the record in memory
            updated = dict(orig_rec)
            updated["faithfulness"] = new_faith
            updated["faithfulness_likert"] = new_likert
            updated["faithfulness_reasoning"] = eval_res.get("faithfulness_reasoning")
            updated["relevance"] = eval_res.get("relevance_score")
            updated["relevance_likert"] = eval_res.get("relevance_likert")
            updated["relevance_reasoning"] = eval_res.get("relevance_reasoning")
            updated["raw_judge_scores"] = eval_res.get("raw_judge_scores")
            updated["judge_error"] = eval_res.get("judge_error", False)
            updated["_amendment_g_rejudged"] = True
            corrected_records[orig_idx] = updated

            if completed_count % 25 == 0 or completed_count == len(candidate_indices):
                print(f"  Progress: {completed_count}/{len(candidate_indices)} re-evaluated ({completed_count/len(candidate_indices)*100:.1f}%) in {time.time()-start_time:.1f}s", flush=True)

    if cache_dirty:
        save_cache(cache)
        print(f"Saved {len(cache)} evaluations to cache: {CACHE_PATH}", flush=True)

    print(f"\nRe-evaluation completed in {time.time()-start_time:.1f}s.", flush=True)
    print(f"Total records modified by Amendment G: {len(changes)} / {len(raw_records)}", flush=True)

    return corrected_records, changes



def step3_report_and_save(orig_records, corrected_records, changes):
    print("\n" + "=" * 80)
    print("STEP 3: AMENDMENT G BEFORE/AFTER SHIFT ANALYSIS")
    print("=" * 80)

    print(f"\nItemized Corrections ({len(changes)} records shifted):")
    print(f"{'Query':<8} | {'Category':<15} | {'Pipeline':<22} | {'Old Likert':<12} | {'New Likert':<12} | {'Raw Judge'}")
    print("-" * 88)
    for c in sorted(changes, key=lambda x: (x["category"], x["query_id"], x["pipeline"])):
        raw_s = str((c.get("raw_judge_scores") or {}).get("raw_faithfulness", "N/A"))
        print(f"{c['query_id']:<8} | {c['category']:<15} | {c['pipeline']:<22} | {str(c['old_likert']) + '/5':<12} | {str(c['new_likert']) + '/5':<12} | {raw_s}", flush=True)


    # Pipeline-level summary for Category A
    print("\n" + "-" * 88)
    print("CATEGORY A (SINGLE-POINT FACTUAL, N=100) - BEFORE VS AFTER AMENDMENT G")
    print("-" * 88)
    print(f"{'Pipeline':<22} | {'Old Overall':<14} | {'New Overall':<14} | {'Old Ans-Only':<15} | {'New Ans-Only':<15} | {'Shift'}")
    print("-" * 88)

    for p in PIPELINES:
        old_p = [r for r in orig_records if r["category"] == "A_Factual" and r["pipeline"] == p]
        new_p = [r for r in corrected_records if r["category"] == "A_Factual" and r["pipeline"] == p]

        old_ans = [r["faithfulness"] for r in old_p if not r.get("safety_rejected") and r.get("faithfulness") is not None]
        new_ans = [r["faithfulness"] for r in new_p if not r.get("safety_rejected") and r.get("faithfulness") is not None]

        old_all = [r["faithfulness"] for r in old_p if r.get("faithfulness") is not None]
        new_all = [r["faithfulness"] for r in new_p if r.get("faithfulness") is not None]

        m_old_all = statistics.mean(old_all) if old_all else 0.0
        m_new_all = statistics.mean(new_all) if new_all else 0.0
        m_old_ans = statistics.mean(old_ans) if old_ans else 0.0
        m_new_ans = statistics.mean(new_ans) if new_ans else 0.0

        diff = m_new_ans - m_old_ans
        print(f"{p:<22} | {m_old_all:<14.4f} | {m_new_all:<14.4f} | {m_old_ans:<15.4f} | {m_new_ans:<15.4f} | {diff:>+6.4f}")

    # Category B summary
    print("\n" + "-" * 88)
    print("CATEGORY B (EVOLUTIONARY DOCTRINE, N=7 COMPLETED) - BEFORE VS AFTER AMENDMENT G")
    print("-" * 88)
    print(f"{'Pipeline':<22} | {'Old Overall':<14} | {'New Overall':<14} | {'Old Ans-Only':<15} | {'New Ans-Only':<15} | {'Shift'}")
    print("-" * 88)

    for p in PIPELINES:
        old_p = [r for r in orig_records if r["category"] == "B_Evolutionary" and r["pipeline"] == p]
        new_p = [r for r in corrected_records if r["category"] == "B_Evolutionary" and r["pipeline"] == p]

        old_ans = [r["faithfulness"] for r in old_p if not r.get("safety_rejected") and r.get("faithfulness") is not None]
        new_ans = [r["faithfulness"] for r in new_p if not r.get("safety_rejected") and r.get("faithfulness") is not None]

        old_all = [r["faithfulness"] for r in old_p if r.get("faithfulness") is not None]
        new_all = [r["faithfulness"] for r in new_p if r.get("faithfulness") is not None]

        m_old_all = statistics.mean(old_all) if old_all else 0.0
        m_new_all = statistics.mean(new_all) if new_all else 0.0
        m_old_ans = statistics.mean(old_ans) if old_ans else 0.0
        m_new_ans = statistics.mean(new_ans) if new_ans else 0.0

        diff = m_new_ans - m_old_ans
        print(f"{p:<22} | {m_old_all:<14.4f} | {m_new_all:<14.4f} | {m_old_ans:<15.4f} | {m_new_ans:<15.4f} | {diff:>+6.4f}")

    # Atomic write
    tmp_path = RAW_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(corrected_records, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, RAW_PATH)
    print(f"\n[PASS] Atomically saved corrected records to: {RAW_PATH}")


def main():
    orig_records = step1_backups_and_orphan_quarantine()
    corrected_records, changes = step2_rejudge_candidates(orig_records)
    step3_report_and_save(orig_records, corrected_records, changes)


if __name__ == "__main__":
    main()
