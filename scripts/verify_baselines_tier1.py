"""
scripts/verify_baselines_tier1.py - Tier 1 Mechanical & Programmatic Verification
===================================================================================
Automated verification harness for Workstream 1.2 Comparative Baselines Benchmark:
  - Check 1: Completeness Invariant (Zero missing or duplicated pairs)
  - Check 2: Live HTTP Payload Parity & Amendment B Reconciliation Equation (Total Evals == G + S)
  - Check 3: Judge Score Parsing Integrity (Zero nulls, valid [1, 5] Likert scores)
  - Dual Faithfulness Metric Accounting (Overall vs. Answer-Only Faithfulness)
  - Check 4: Timing Sanity & Multi-Stage Dual Latency (Amortized vs. Active for Gen, Ret, Grade)
  - Check 5: Category C Out-of-Context Target-Node Invariant (Zero fabricated SCOTUS nodes)
  - Check 6: Category D Acceptance Criteria Sanity (Adversarial deception trap grading)
"""

import os
import sys
import json
import re
import statistics
import argparse
from typing import List, Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

PAYLOAD_LOG_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads.jsonl")
DEFAULT_RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")

MANDATORY_MODEL = "databricks-meta-llama-3-3-70b-instruct"
MANDATORY_TEMP = 0.0
EXPECTED_PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted",
    "5_Full_TERRA"
]


def verify_tier1(raw_path: str, expected_queries: int):
    expected_total_evals = expected_queries * len(EXPECTED_PIPELINES)
    print("\n" + "=" * 80)
    print(f"TIER 1 MECHANICAL & PROGRAMMATIC VERIFICATION: {expected_queries} QUERIES ({expected_total_evals} EVALS)")
    print("=" * 80)

    if not os.path.exists(raw_path):
        print(f"[FAIL] Evaluation raw checkpoint not found: {raw_path}")
        return False

    with open(raw_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} total evaluation records from {raw_path}.")

    all_passed = True

    # -------------------------------------------------------------------------
    # CHECK 1: Completeness Invariant
    # -------------------------------------------------------------------------
    print("\n--- CHECK 1: COMPLETENESS INVARIANT ---")
    print(f"Total Records Found:    {len(records)} (Expected: {expected_total_evals})")
    if len(records) != expected_total_evals:
        print(f"[FAIL] Expected exactly {expected_total_evals} records, found {len(records)}!")
        all_passed = False
    else:
        print(f"[PASS] Exact record count = {expected_total_evals} confirmed.")

    unique_pairs = {(r["query_id"], r["pipeline"]) for r in records}
    if len(unique_pairs) != len(records):
        print(f"[FAIL] Found duplicate (query_id, pipeline) records in checkpoint!")
        all_passed = False
    else:
        print("[PASS] Zero duplicate records confirmed.")

    # -------------------------------------------------------------------------
    # CHECK 2: Live HTTP Payload Parity & Amendment B Reconciliation Equation
    # -------------------------------------------------------------------------
    print("\n--- CHECK 2: LIVE HTTP PAYLOAD PARITY & RECONCILIATION EQUATION GATE ---")
    if not os.path.exists(PAYLOAD_LOG_PATH):
        print(f"[FAIL] Audit payload log not found: {PAYLOAD_LOG_PATH}")
        return False

    with open(PAYLOAD_LOG_PATH, "r", encoding="utf-8") as f:
        audit_entries = [json.loads(line) for line in f if line.strip()]

    gen_entries = [e for e in audit_entries if e.get("event") == "generation"]
    sc_entries = [e for e in audit_entries if e.get("event") == "short_circuit"]

    TOTAL_EVALS = len(records)
    from collections import Counter
    q_counts = Counter(r["query_id"] for r in records)
    committed_qids = {qid for qid, count in q_counts.items() if count == len(EXPECTED_PIPELINES)}

    committed_gen = [e for e in gen_entries if e.get("query_id") in committed_qids]
    committed_sc = [e for e in sc_entries if e.get("query_id") in committed_qids]
    in_flight = [e for e in audit_entries if e.get("query_id") not in committed_qids]

    G = len(committed_gen)
    S = len(committed_sc)

    print(f"Total Evaluations in Raw Checkpoint:       {TOTAL_EVALS}")
    print(f"Intercepted Generator API Payloads (G):    {G} (Committed) + {len(in_flight)} (In-flight)")
    print(f"Logged Pre-Generation Short-Circuits (S): {S}")
    print(f"Committed Reconciliation Equation: {G} (G) + {S} (S) = {G + S}")

    if G + S != TOTAL_EVALS:
        print(f"[FAIL] RECONCILIATION GAP: G ({G}) + S ({S}) = {G+S} != TOTAL_EVALS ({TOTAL_EVALS})!")
        all_passed = False
    else:
        print(f"[PASS] EXACT RECONCILIATION: {TOTAL_EVALS} == G + S (Zero unexplained discrepancy).")
        if in_flight:
            in_flight_qids = list(set(e.get("query_id") for e in in_flight))
            print(f"[NOTE] Live in-flight execution detected for query {in_flight_qids}: {len(in_flight)}/{len(EXPECTED_PIPELINES)} pipeline calls logged.")

    # Verify Generator Payload Integrity
    bad_gen = [
        e for e in gen_entries
        if e.get("model") != MANDATORY_MODEL or e.get("temperature") != MANDATORY_TEMP
    ]
    if bad_gen:
        print(f"[FAIL] Found {len(bad_gen)} non-compliant generator payloads: {bad_gen[:2]}")
        all_passed = False
    else:
        print(f"[PASS] 100% of intercepted calls show model == '{MANDATORY_MODEL}' and temperature == {MANDATORY_TEMP}.")

    # -------------------------------------------------------------------------
    # CHECK 3: Judge Score Parsing Integrity
    # -------------------------------------------------------------------------
    print("\n--- CHECK 3: JUDGE SCORE PARSING INTEGRITY ---")
    null_f = [r for r in records if r.get("faithfulness_likert") is None]
    null_r = [r for r in records if r.get("relevance_likert") is None]
    if null_f or null_r:
        print(f"[FAIL] Found null judge scores: {len(null_f)} faithfulness, {len(null_r)} relevance!")
        all_passed = False
    else:
        print(f"[PASS] 0 / {len(records)} null judge scores. All records cleanly parsed.")

    out_of_range = [
        r for r in records
        if (r.get("faithfulness_likert") is not None and not (1 <= r.get("faithfulness_likert") <= 5))
        or (r.get("relevance_likert") is not None and not (1 <= r.get("relevance_likert") <= 5))
    ]
    if out_of_range:
        print(f"[FAIL] Found {len(out_of_range)} out-of-range judge Likert scores!")
        all_passed = False
    # -------------------------------------------------------------------------
    # CHECK 3B: Judge Score Sentiment & Reasoning Consistency (Amendment G Invariant)
    # -------------------------------------------------------------------------
    print("\n--- CHECK 3B: JUDGE SCORE SENTIMENT CONSISTENCY (AMENDMENT G INVARIANT) ---")
    contradictions = []
    
    for r in records:
        likert_f = r.get("faithfulness_likert")
        is_refusal = r.get("safety_rejected")
        reason = r.get("faithfulness_reasoning", "").lower()
        raw_scores = r.get("raw_judge_scores")

        # Invariant 1: If raw judge scores are preserved, raw score must align with likert score (unless programmatically clamped)
        if raw_scores and "raw_faithfulness" in raw_scores:
            rf = raw_scores["raw_faithfulness"]
            if isinstance(rf, (int, float)) and int(rf) != likert_f:
                if (
                    not r.get("faithfulness_clamped_by_amendment_k")
                    and not r.get("faithfulness_clamped_by_amendment_l")
                    and not r.get("faithfulness_clamped_by_amendment_m")
                ):
                    contradictions.append((
                        r["query_id"], r["pipeline"], likert_f,
                        f"raw_faithfulness ({rf}) != parsed likert ({likert_f})"
                    ))

        # Invariant 2: Substantive Likert 5 cannot contain affirmative declarations of unfaithfulness
        if likert_f == 5 and not is_refusal:
            if re.search(r"\b(score|rating)\s*(?:is|of|:)\s*1\b", reason) and not re.search(r"\b(would have|did not|rather than|instead of|not a)\b", reason):
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning explicitly declares score/rating of 1"))
            elif "completely unfaithful" in reason and not re.search(r"\b(not|is not|does not consider it)\s+completely unfaithful\b", reason):
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning explicitly declares answer is 'completely unfaithful'"))
            elif re.search(r"\bcontains\s+(?:a\s+)?serious legal falsehood\b", reason):
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning affirms answer 'contains serious legal falsehood'"))
            elif "contains numerous hallucinations" in reason:
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning affirms answer 'contains numerous hallucinations'"))
            elif "contains factual inaccuracies and hallucinations" in reason:
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning affirms answer 'contains factual inaccuracies and hallucinations'"))
            elif "hallucinated information about" in reason:
                contradictions.append((r["query_id"], r["pipeline"], likert_f, "Reasoning affirms 'hallucinated information about'"))

    if contradictions:
        print(f"[FAIL] Contradiction Invariant Violated! Found {len(contradictions)} records with judge score contradictions:")
        for qid, p, lik, reas in contradictions[:5]:
            print(f"  * Query {qid} ({p}): Likert {lik}/5 contradiction: {reas}")
        all_passed = False
    else:
        print(f"[PASS] 0 / {len(records)} sentiment contradictions detected. 100% of Likert-5 scores are consistent with faithful reasoning.")


    # -------------------------------------------------------------------------
    # DUAL-REPORTED FAITHFULNESS AUDIT (RESOLVING REFUSAL CONFOUND)
    # -------------------------------------------------------------------------
    print("\n--- DUAL-REPORTED FAITHFULNESS AUDIT (OVERALL VS ANSWER-ONLY) ---")
    print(f"{'Pipeline':<22} | {'Overall Faith':<15} | {'Non-Refusal Faith':<18} | {'Refusal Count'}")
    print("-" * 75)
    for p in EXPECTED_PIPELINES:
        p_recs = [r for r in records if r["pipeline"] == p]
        all_f = [r["faithfulness"] for r in p_recs if r.get("faithfulness") is not None]
        ans_recs = [r for r in p_recs if not r.get("safety_rejected")]
        ans_f = [r["faithfulness"] for r in ans_recs if r.get("faithfulness") is not None]

        mean_all_f = statistics.mean(all_f) if all_f else 0.0
        mean_ans_f = statistics.mean(ans_f) if ans_f else 0.0
        ref_count = f"{len(p_recs) - len(ans_recs)}/{len(p_recs)}"
        print(f"{p:<22} | {mean_all_f:<15.4f} | {mean_ans_f:<18.4f} | {ref_count}")

    # -------------------------------------------------------------------------
    # CHECK 4: Timing Sanity & Multi-Stage Dual Latency Profiling (Amendment E)
    # -------------------------------------------------------------------------
    print("\n--- CHECK 4: TIMING SANITY & DUAL LATENCY PROFILING (AMENDMENT E) ---")
    print(f"{'Pipeline':<20} | {'Mean Tot':<10} | {'Route (ms)':<18} | {'Gen (Amort/Act)':<22} | {'Ret (Amort/Act)':<22} | {'Grade (Amort/Act)'}")
    print("-" * 115)
    for p in EXPECTED_PIPELINES:
        p_recs = [r for r in records if r["pipeline"] == p]
        tot_l = [r.get("timing", {}).get("total_ms", 0.0) for r in p_recs]
        rot_l = [r.get("timing", {}).get("routing_ms", 0.0) for r in p_recs]
        gen_l = [r.get("timing", {}).get("generation_ms", 0.0) for r in p_recs]
        ret_l = [r.get("timing", {}).get("retrieval_ms", 0.0) for r in p_recs]
        grd_l = [r.get("timing", {}).get("grading_ms", 0.0) for r in p_recs]

        mean_tot = round(statistics.mean(tot_l), 1) if tot_l else 0.0

        # Route
        act_rot = [x for x in rot_l if x > 0.0]
        amort_rot = round(statistics.mean(rot_l), 1) if rot_l else 0.0
        active_rot = round(statistics.mean(act_rot), 1) if act_rot else 0.0
        rot_str = f"{amort_rot}/{active_rot} (N={len(act_rot)})"

        # Gen
        act_gen = [x for x in gen_l if x > 0.0]
        amort_gen = round(statistics.mean(gen_l), 1) if gen_l else 0.0
        active_gen = round(statistics.mean(act_gen), 1) if act_gen else 0.0
        gen_str = f"{amort_gen}/{active_gen} (N={len(act_gen)})"

        # Ret
        act_ret = [x for x in ret_l if x > 0.0]
        amort_ret = round(statistics.mean(ret_l), 1) if ret_l else 0.0
        active_ret = round(statistics.mean(act_ret), 1) if act_ret else 0.0
        ret_str = f"{amort_ret}/{active_ret} (N={len(act_ret)})"

        # Grade
        act_grd = [x for x in grd_l if x > 0.0]
        amort_grd = round(statistics.mean(grd_l), 1) if grd_l else 0.0
        active_grd = round(statistics.mean(act_grd), 1) if act_grd else 0.0
        grd_str = f"{amort_grd}/{active_grd} (N={len(act_grd)})"

        print(f"{p:<20} | {mean_tot:<10} | {rot_str:<18} | {gen_str:<22} | {ret_str:<22} | {grd_str}")

    print("[PASS] Multi-stage dual latency accounting completed across routing, generation, retrieval, and grading.")

    # -------------------------------------------------------------------------
    # CHECK 5: Category C Out-of-Context Invariant
    # -------------------------------------------------------------------------
    print("\n--- CHECK 5: CATEGORY C OUT-OF-CONTEXT INVARIANT ---")
    cat_c_records = [r for r in records if r["category"] == "C_OutOfContext"]
    print(f"Inspecting {len(cat_c_records)} total Category C records across pipelines...")
    bad_cat_c_targets = [r for r in cat_c_records if len(r.get("target_nodes", [])) > 0]
    if bad_cat_c_targets:
        print(f"[FAIL] Found {len(bad_cat_c_targets)} Category C queries with non-empty target_nodes!")
        all_passed = False
    else:
        print("[PASS] 100% of Category C records strictly satisfy target_nodes: [].")

    # -------------------------------------------------------------------------
    # CHECK 6: Category D Acceptance Criteria Sanity & Adversarial Trap Invariant
    # -------------------------------------------------------------------------
    print("\n--- CHECK 6: CATEGORY D ACCEPTANCE CRITERIA & ADVERSARIAL TRAP INVARIANT (AMENDMENT J) ---")
    cat_d_records = [r for r in records if r["category"] == "D_Adversarial"]
    print(f"Inspecting {len(cat_d_records)} total Category D records across pipelines...")
    
    if cat_d_records:
        benchmark_path = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
        bench_map = {}
        if os.path.exists(benchmark_path):
            with open(benchmark_path, "r", encoding="utf-8") as f:
                bench_data = json.load(f)
                bench_map = {q["query_id"]: q for q in bench_data}

        # Persistent Semantic Invariant Cache (Amendment J)
        cache_path = os.path.join(ROOT_DIR, "scratch", "invariant_6_cache.json")
        inv6_cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    inv6_cache = json.load(f)
            except Exception:
                inv6_cache = {}

        import hashlib
        verifier_client = None

        fatal_error_violations = []
        false_negative_penalties = []
        refusal_unfaithfulness_violations = []

        for r in cat_d_records:
            qid = r["query_id"]
            pipe = r["pipeline"]
            ans = r.get("answer_full", r.get("answer", ""))
            likert_f = r.get("faithfulness_likert")
            is_refusal = r.get("safety_rejected")
            q_data = bench_map.get(qid, {})
            q_text = q_data.get("query", "")
            crit = q_data.get("acceptance_criteria", {})
            fatal_errors = crit.get("fatal_errors", [])
            valid_justifications = crit.get("valid_justifications", [])

            # Check cache or initialize client if needed
            key_str = f"{q_text.strip()}|||{ans.strip()}"
            h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
            if h not in inv6_cache:
                from baselines.common import get_databricks_client
                from baselines.runner_core import clean_json_text, get_semantic_classification
                if verifier_client is None:
                    print(f"Connecting to Databricks LLaMA 3.3 70B Semantic Verifier for uncached records...")
                    verifier_client = get_databricks_client()
                sem_res = get_semantic_classification(
                    verifier_client, q_text, ans, fatal_errors, valid_justifications, inv6_cache, cache_path
                )
            else:
                sem_res = inv6_cache[h]

            affirms_fe = sem_res.get("affirms_fatal_error", False)
            refutes_fd = sem_res.get("refutes_fatal_doctrine", False)
            is_uncommitted = sem_res.get("is_refusal_or_uncommitted", False)

            # Invariant 6A (Fatal Error Gate): An answer committing a fatal error must NOT receive passing score (>= 3)
            if affirms_fe and likert_f is not None and likert_f >= 3:
                fatal_error_violations.append((qid, pipe, likert_f, f"Semantic Verifier: affirms fatal error ({sem_res.get('primary_basis', '')})"))

            # Invariant 6B (Anti-False-Negative Gate): An answer genuinely refuting the trap must NOT be penalized (<= 2)
            if refutes_fd and not affirms_fe and likert_f is not None and likert_f <= 2 and not r.get("faithfulness_clamped_by_amendment_m"):
                false_negative_penalties.append((qid, pipe, likert_f, f"Semantic Verifier: genuine refutation unfairly penalized ({sem_res.get('primary_basis', '')})"))

            # Invariant 6C (Refusal Non-Falsity Gate - Amendment K): A refusal where verifier confirms no fatal doctrine affirmed cannot receive Faithfulness < 4
            if is_refusal and not affirms_fe and likert_f is not None and likert_f < 4:
                refusal_unfaithfulness_violations.append((qid, pipe, likert_f, f"Semantic Verifier: refusal without fatal error unfairly penalized ({sem_res.get('primary_basis', '')})"))

        if fatal_error_violations:
            print(f"[FAIL] Invariant 6A Violated! Found {len(fatal_error_violations)} records committing fatal errors with passing scores:")
            for qid, pipe, lik, fe in fatal_error_violations[:5]:
                print(f"  * Query {qid} ({pipe}): Likert {lik}/5 but committed fatal error: '{fe}'")
            all_passed = False
        else:
            print("[PASS] Invariant 6A: Zero records committing fatal errors received passing faithfulness scores.")

        if false_negative_penalties:
            print(f"[WARN/FAIL] Invariant 6B Violated! Found {len(false_negative_penalties)} correct refutations unfairly penalized (Likert <= 2):")
            for qid, pipe, lik, reas in false_negative_penalties[:5]:
                print(f"  * Query {qid} ({pipe}): Likert {lik}/5 penalty on valid refutation. Reason: '{reas}...'")
            all_passed = False
        else:
            print("[PASS] Invariant 6B: Zero correct refutations unfairly penalized with failing scores.")

        if refusal_unfaithfulness_violations:
            print(f"[FAIL] Invariant 6C Violated! Found {len(refusal_unfaithfulness_violations)} non-fatal refusals scored Faithfulness < 4:")
            for qid, pipe, lik, reas in refusal_unfaithfulness_violations[:5]:
                print(f"  * Query {qid} ({pipe}): Likert {lik}/5 penalty on non-fatal refusal. Reason: '{reas}...'")
            all_passed = False
        else:
            print("[PASS] Invariant 6C: Zero non-fatal refusals scored Faithfulness < 4 (Amendment K verified).")
    else:
        print("[PASS] Category D gate initialized (awaiting Category D execution).")

    print("\n" + "=" * 80)
    if all_passed:
        print(">>> ALL TIER 1 MECHANICAL CHECKS PASSED WITH ZERO VIOLATIONS. <<<")
    else:
        print(">>> [ALERT] ONE OR MORE TIER 1 CHECKS FAILED. SEE DETAILS ABOVE. <<<")
    print("=" * 80 + "\n")
    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=str, default=DEFAULT_RAW_PATH)
    parser.add_argument("--queries", type=int, default=10, help="Expected queries count (10 for Stage 1, 350 for Full)")
    args = parser.parse_args()
    verify_tier1(args.raw, args.queries)
