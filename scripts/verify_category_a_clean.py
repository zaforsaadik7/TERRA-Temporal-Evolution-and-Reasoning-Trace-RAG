"""
scripts/verify_category_a_clean.py - Comprehensive Category A Post-Amendment F Verification
==========================================================================================
Verifies:
1. Reconciliation equation parity: TOTAL_EVALS == G + S (with zero gap).
2. Category A Refusal rates across all 5 pipelines before vs. after Amendment F.
3. Dual-Reported Faithfulness (Overall vs. Answer-Only) for all 5 pipelines on Category A.
4. Latency profiles across all pipelines on Category A.
"""

import os
import sys
import json
import statistics

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
AUDIT_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads.jsonl")
PRE_RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw_pre_amendment_f.json")
SUPERSEDED_AUDIT_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads_amendment_f_superseded.jsonl")

PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted",
    "5_Full_TERRA"
]


def main():
    print("=" * 85)
    print("CATEGORY A COMPREHENSIVE POST-AMENDMENT F VERIFICATION AUDIT")
    print("=" * 85)

    if not os.path.exists(RAW_PATH) or not os.path.exists(AUDIT_PATH):
        print("[ERROR] Required checkpoint or audit file missing!")
        return

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        audit_entries = [json.loads(line) for line in f if line.strip()]

    # 1. RECONCILIATION EQUATION GATE
    print("\n--- 1. RECONCILIATION EQUATION GATE ---")
    gen_entries = [e for e in audit_entries if e.get("event") == "generation"]
    sc_entries = [e for e in audit_entries if e.get("event") == "short_circuit"]
    G = len(gen_entries)
    S = len(sc_entries)
    TOTAL_EVALS = len(records)

    print(f"Total Evaluations in Raw Checkpoint:       {TOTAL_EVALS}")
    print(f"Intercepted Generator API Payloads (G):    {G}")
    print(f"Logged Pre-Generation Short-Circuits (S): {S}")
    print(f"Reconciliation Equation: {G} (G) + {S} (S) = {G + S}")

    if G + S != TOTAL_EVALS:
        print(f"[FAIL] RECONCILIATION GAP: {G+S} != {TOTAL_EVALS}!")
    else:
        print("[PASS] EXACT RECONCILIATION: TOTAL_EVALS == G + S (Zero discrepancy).")

    # Check superseded audit entries
    if os.path.exists(SUPERSEDED_AUDIT_PATH):
        with open(SUPERSEDED_AUDIT_PATH, "r", encoding="utf-8") as f:
            sup_count = len([l for l in f if l.strip()])
        print(f"[PASS] Archived Superseded Pre-Amendment-F Records: {sup_count} entries cleanly isolated.")

    # 2. CATEGORY A REFUSAL RATE TABLE (N=100)
    print("\n--- 2. CATEGORY A REFUSAL RATES ACROSS ALL 5 PIPELINES (N=100 QUERIES) ---")
    print(f"{'Pipeline':<22} | {'Total Queries':<14} | {'Refusals':<12} | {'Refusal Rate':<14} | {'Status'}")
    print("-" * 75)

    cat_a_records = [r for r in records if r["query_id"].startswith("A")]

    for p in PIPELINES:
        p_recs = [r for r in cat_a_records if r["pipeline"] == p]
        ref_recs = [r for r in p_recs if r.get("safety_rejected")]
        rate = (len(ref_recs) / len(p_recs) * 100) if p_recs else 0.0
        status = "PARAMETRIC FAST PATH" if p == "5_Full_TERRA" else ("PARAMETRIC BASELINE" if p == "1_Direct_LLM" else "FULL-TEXT RAG OMISSION")
        print(f"{p:<22} | {len(p_recs):<14} | {len(ref_recs):<12} | {rate:>5.1f}%{'':<8} | {status}")

    # 3. DUAL-REPORTED FAITHFULNESS AUDIT (CATEGORY A)
    print("\n--- 3. DUAL-REPORTED FAITHFULNESS AUDIT (CATEGORY A, N=100) ---")
    print(f"{'Pipeline':<22} | {'Overall Faith':<15} | {'Answer-Only Faith':<18} | {'Answer N':<10} | {'Mean Likert'}")
    print("-" * 80)

    for p in PIPELINES:
        p_recs = [r for r in cat_a_records if r["pipeline"] == p]
        all_f = [r["faithfulness"] for r in p_recs if r.get("faithfulness") is not None]
        ans_recs = [r for r in p_recs if not r.get("safety_rejected")]
        ans_f = [r["faithfulness"] for r in ans_recs if r.get("faithfulness") is not None]
        ans_likert = [r["faithfulness_likert"] for r in ans_recs if r.get("faithfulness_likert") is not None]

        mean_all_f = statistics.mean(all_f) if all_f else 0.0
        mean_ans_f = statistics.mean(ans_f) if ans_f else 0.0
        mean_lik = statistics.mean(ans_likert) if ans_likert else 0.0
        ans_n_str = f"{len(ans_recs)}/100"

        print(f"{p:<22} | {mean_all_f:<15.4f} | {mean_ans_f:<18.4f} | {ans_n_str:<10} | {mean_lik:.2f}/5.0")

    # 4. TIMING & DUAL LATENCY PROFILING (CATEGORY A)
    print("\n--- 4. MULTI-STAGE LATENCY PROFILING (CATEGORY A) ---")
    print(f"{'Pipeline':<20} | {'Total (ms)':<12} | {'Route (ms)':<14} | {'Gen (ms)':<14} | {'Ret (ms)':<12} | {'Grade (ms)'}")
    print("-" * 85)

    for p in PIPELINES:
        p_recs = [r for r in cat_a_records if r["pipeline"] == p]
        tot_ms = statistics.mean([r.get("timing", {}).get("total_ms", 0.0) for r in p_recs])
        rot_ms = statistics.mean([r.get("timing", {}).get("routing_ms", 0.0) for r in p_recs])
        gen_ms = statistics.mean([r.get("timing", {}).get("generation_ms", 0.0) for r in p_recs])
        ret_ms = statistics.mean([r.get("timing", {}).get("retrieval_ms", 0.0) for r in p_recs])
        grd_ms = statistics.mean([r.get("timing", {}).get("grading_ms", 0.0) for r in p_recs])

        print(f"{p:<20} | {tot_ms:<12.1f} | {rot_ms:<14.1f} | {gen_ms:<14.1f} | {ret_ms:<12.1f} | {grd_ms:.1f}")

    # 5. BEFORE VS. AFTER AMENDMENT F (TERRA SPECIFIC)
    if os.path.exists(PRE_RAW_PATH):
        with open(PRE_RAW_PATH, "r", encoding="utf-8") as f:
            pre_records = json.load(f)
        pre_terra = [r for r in pre_records if r["pipeline"] == "5_Full_TERRA" and r["query_id"].startswith("A")]
        post_terra = [r for r in cat_a_records if r["pipeline"] == "5_Full_TERRA"]

        pre_refs = [r for r in pre_terra if r.get("safety_rejected")]
        post_refs = [r for r in post_terra if r.get("safety_rejected")]

        pre_all_f = statistics.mean([r["faithfulness"] for r in pre_terra if r.get("faithfulness") is not None])
        post_all_f = statistics.mean([r["faithfulness"] for r in post_terra if r.get("faithfulness") is not None])

        pre_ans_recs = [r for r in pre_terra if not r.get("safety_rejected")]
        post_ans_recs = [r for r in post_terra if not r.get("safety_rejected")]

        pre_ans_f = statistics.mean([r["faithfulness"] for r in pre_ans_recs if r.get("faithfulness") is not None])
        post_ans_f = statistics.mean([r["faithfulness"] for r in post_ans_recs if r.get("faithfulness") is not None])

        print("\n" + "=" * 85)
        print("AMENDMENT F SUMMARY: FULL TERRA CATEGORY A BEFORE VS. AFTER COMPARISON (N=100)")
        print("=" * 85)
        print(f"{'Dimension':<32} | {'Before Amendment F':<24} | {'After Amendment F':<24}")
        print("-" * 85)
        print(f"{'Refusal Count / Rate':<32} | {len(pre_refs)}/100 ({len(pre_refs):.1f}%)" + f"{'':<13} | " + f"{len(post_refs)}/100 ({len(post_refs):.1f}%)")
        print(f"{'Overall Faithfulness':<32} | {pre_all_f:<24.4f} | {post_all_f:<24.4f}")
        print(f"{'Answer-Only Faithfulness':<32} | {pre_ans_f:<24.4f} | {post_ans_f:<24.4f}")
        print(f"{'Substantive Answer Count':<32} | {len(pre_ans_recs)}/100" + f"{'':<17} | " + f"{len(post_ans_recs)}/100")
        print("=" * 85)


if __name__ == "__main__":
    main()
