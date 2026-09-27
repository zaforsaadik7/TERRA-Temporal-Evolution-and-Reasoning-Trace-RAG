"""
scripts/apply_amendment_f_cat_a.py - Amendment F Execution & Regeneration Harness
=================================================================================
Remediates the fast-path negative-constraint prompt inheritance bug (Amendment F):
1. Backs up raw evaluations and audit logs.
2. Archives pre-amendment Category A Full TERRA audit payloads to audit_payloads_amendment_f_superseded.jsonl.
3. Re-evaluates all 100 Category A queries (A001-A100) under 5_Full_TERRA using the patched fast-path.
4. Updates terra_baselines_eval_raw.json with the corrected records.
5. Verifies payload parity and exact reconciliation equation (G + S == TOTAL_EVALS).
6. Outputs a formal Before vs. After audit comparison.
"""

import os
import sys
import json
import time
import shutil
import statistics
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
AUDIT_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads.jsonl")
BENCH_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")

BACKUP_RAW = os.path.join(ROOT_DIR, "terra_baselines_eval_raw_pre_amendment_f.json")
BACKUP_AUDIT = os.path.join(ROOT_DIR, "baselines", "audit_payloads_pre_amendment_f.jsonl")
SUPERSEDED_AUDIT = os.path.join(ROOT_DIR, "baselines", "audit_payloads_amendment_f_superseded.jsonl")

from baselines.runner_core import (
    EvaluationEngines,
    execute_pipeline,
    atomic_save
)


def main():
    print("=" * 80)
    print("AMENDMENT F: REGENERATING CATEGORY A FULL TERRA BENCHMARK DATA")
    print("=" * 80)

    # 1. Backups
    print("\n--- STEP 1: CREATING BACKUPS ---")
    shutil.copyfile(RAW_PATH, BACKUP_RAW)
    shutil.copyfile(AUDIT_PATH, BACKUP_AUDIT)
    print(f"Backed up raw evals to:  {BACKUP_RAW}")
    print(f"Backed up audit log to:  {BACKUP_AUDIT}")

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        existing_records = json.load(f)
    print(f"Loaded {len(existing_records)} existing records from checkpoint.")

    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        existing_audit = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(existing_audit)} existing audit entries.")

    # 2. Extract Pre-Amendment Baseline Stats for Full TERRA on Category A
    pre_terra_cat_a = [
        r for r in existing_records
        if r["pipeline"] == "5_Full_TERRA" and r["query_id"].startswith("A")
    ]
    pre_refusals = [r for r in pre_terra_cat_a if r.get("safety_rejected")]
    pre_faith = [r["faithfulness"] for r in pre_terra_cat_a if r.get("faithfulness") is not None]
    pre_tot_ms = [r.get("timing", {}).get("total_ms", 0.0) for r in pre_terra_cat_a]

    print(f"\n[PRE-AMENDMENT F STATE - Category A Full TERRA (N={len(pre_terra_cat_a)})]")
    print(f"  Refusals:         {len(pre_refusals)} / {len(pre_terra_cat_a)} ({len(pre_refusals)/len(pre_terra_cat_a)*100:.1f}%)")
    print(f"  Mean Faithfulness:{statistics.mean(pre_faith):.4f}")
    print(f"  Mean Total Lat:   {statistics.mean(pre_tot_ms):.1f} ms")

    # 3. Archive pre-amendment Category A Full TERRA audit entries
    print("\n--- STEP 2: ARCHIVING PRE-AMENDMENT AUDIT ENTRIES ---")
    superseded_entries = []
    retained_audit = []
    for e in existing_audit:
        if e.get("pipeline") == "5_Full_TERRA" and e.get("query_id", "").startswith("A"):
            superseded_entries.append(e)
        else:
            retained_audit.append(e)

    print(f"Archiving {len(superseded_entries)} superseded Category A Full TERRA entries to:")
    print(f"  {SUPERSEDED_AUDIT}")
    with open(SUPERSEDED_AUDIT, "w", encoding="utf-8") as f:
        for e in superseded_entries:
            f.write(json.dumps(e) + "\n")

    print(f"Rewriting active audit log with {len(retained_audit)} retained entries...")
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        for e in retained_audit:
            f.write(json.dumps(e) + "\n")

    # 4. Load benchmark Category A queries (A001-A100)
    print("\n--- STEP 3: INITIALIZING ENGINES & LOADING CATEGORY A BENCHMARK ---")
    with open(BENCH_PATH, "r", encoding="utf-8") as f:
        all_queries = json.load(f)
    cat_a_queries = [q for q in all_queries if q["query_id"].startswith("A")]
    print(f"Loaded {len(cat_a_queries)} Category A queries to re-evaluate.")

    engines = EvaluationEngines()

    # 5. Execute 5_Full_TERRA on all 100 Category A queries
    print("\n--- STEP 4: EXECUTING FULL TERRA ON CATEGORY A (AMENDMENT F) ---")
    new_terra_records = {}
    t0_all = time.time()

    for idx, q_data in enumerate(cat_a_queries, 1):
        qid = q_data["query_id"]
        t_start = time.time()
        record = execute_pipeline("5_Full_TERRA", q_data, engines)
        elapsed = round(time.time() - t_start, 2)
        new_terra_records[qid] = record

        ref_flag = record.get("safety_rejected", False)
        f_score = record.get("faithfulness", 0.0)
        tot_ms = record.get("timing", {}).get("total_ms", 0.0)
        ans_snippet = record.get("answer_full", "").strip().replace("\n", " ")[:60]
        print(f"[{idx:>3}/100] Query {qid} | Refusal: {ref_flag!s:<5} | Faith: {f_score:.2f} | Lat: {tot_ms:.0f}ms ({elapsed}s) | Ans: {ans_snippet}...")

    print(f"\nCompleted 100 Category A re-evaluations in {time.time() - t0_all:.2f}s.")

    # 6. Update existing_records with corrected records
    print("\n--- STEP 5: ATOMICALLY UPDATING RAW CHECKPOINT ---")
    updated_records = []
    replaced_count = 0
    for r in existing_records:
        if r["pipeline"] == "5_Full_TERRA" and r["query_id"] in new_terra_records:
            updated_records.append(new_terra_records[r["query_id"]])
            replaced_count += 1
        else:
            updated_records.append(r)

    print(f"Replaced {replaced_count} Category A Full TERRA records.")
    atomic_save(updated_records, RAW_PATH)
    print(f"Saved {len(updated_records)} total records to {RAW_PATH}.")

    # 7. Post-Amendment Verification
    print("\n--- STEP 6: POST-AMENDMENT VERIFICATION & PARITY CHECK ---")
    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        final_audit = [json.loads(line) for line in f if line.strip()]

    gen_entries = [e for e in final_audit if e.get("event") == "generation"]
    sc_entries = [e for e in final_audit if e.get("event") == "short_circuit"]
    G = len(gen_entries)
    S = len(sc_entries)
    TOTAL_EVALS = len(updated_records)

    print(f"Total Evaluations in Raw Checkpoint:       {TOTAL_EVALS}")
    print(f"Intercepted Generator API Payloads (G):    {G}")
    print(f"Logged Pre-Generation Short-Circuits (S): {S}")
    print(f"Reconciliation Equation: {G} (G) + {S} (S) = {G + S}")

    assert G + S == TOTAL_EVALS, f"[FATAL] Reconciliation gap: {G + S} != {TOTAL_EVALS}!"
    print("[PASS] EXACT RECONCILIATION: TOTAL_EVALS == G + S (Zero discrepancy).")

    post_terra_cat_a = [
        r for r in updated_records
        if r["pipeline"] == "5_Full_TERRA" and r["query_id"].startswith("A")
    ]
    post_refusals = [r for r in post_terra_cat_a if r.get("safety_rejected")]
    post_faith = [r["faithfulness"] for r in post_terra_cat_a if r.get("faithfulness") is not None]
    post_tot_ms = [r.get("timing", {}).get("total_ms", 0.0) for r in post_terra_cat_a]

    print("\n" + "=" * 80)
    print("AMENDMENT F BEFORE VS. AFTER COMPARISON (CATEGORY A FULL TERRA, N=100)")
    print("=" * 80)
    print(f"{'Metric':<30} | {'Before Amendment F':<22} | {'After Amendment F':<22}")
    print("-" * 80)
    print(f"{'Refusal Count':<30} | {len(pre_refusals)}/100 ({len(pre_refusals):.1f}%)" + f"{'':<11} | " + f"{len(post_refusals)}/100 ({len(post_refusals):.1f}%)")
    print(f"{'Mean Faithfulness':<30} | {statistics.mean(pre_faith):<22.4f} | {statistics.mean(post_faith):<22.4f}")
    print(f"{'Mean Total Latency':<30} | {statistics.mean(pre_tot_ms):<19.1f} ms | {statistics.mean(post_tot_ms):<19.1f} ms")
    print("=" * 80)


if __name__ == "__main__":
    main()
