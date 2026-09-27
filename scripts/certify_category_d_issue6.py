"""
scripts/certify_category_d_issue6.py
====================================
Category D certification for deployed TERRA (Issue #6, N=75).
Calls get_semantic_classification from baselines/runner_core.py on exactly the
29 substantive Category D completions in scratch/terra_350_issue6_dual_judged.json.
Caches results to scratch/invariant_6_cache_issue6.json.
Does NOT touch scratch/invariant_6_cache.json.

Produces:
  - scratch/category_d_rubric_summary_v2.json
  - logs/catd_v2.txt (comparison against provisional 46/25/2/2 counts)
"""

import os
import sys
import json
import hashlib
import time
from typing import Dict, Any, List
import scipy.stats as stats

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from baselines.runner_core import get_semantic_classification
from baselines.common import get_databricks_client, compute_file_sha256

BENCHMARK_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
ISSUE6_TERRA_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_issue6_dual_judged.json")
EXISTING_RUBRIC_PATH = os.path.join(ROOT_DIR, "scratch", "category_d_rubric_summary.json")
LEGACY_CACHE_PATH = os.path.join(ROOT_DIR, "scratch", "invariant_6_cache.json")

NEW_CACHE_PATH = os.path.join(ROOT_DIR, "scratch", "invariant_6_cache_issue6.json")
OUTPUT_RUBRIC_V2_PATH = os.path.join(ROOT_DIR, "scratch", "category_d_rubric_summary_v2.json")
LOG_PATH = os.path.join(ROOT_DIR, "logs", "catd_v2.txt")


def compute_exact_two_tailed_mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    one_tailed = stats.binom.cdf(k, n, 0.5)
    two_tailed = min(1.0, 2.0 * float(one_tailed))
    return float(two_tailed)


def main():
    log_lines: List[str] = []
    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("CATEGORY D CERTIFICATION: DEPLOYED TERRA (ISSUE #6 RUN)")
    log("Semantic Verifier: get_semantic_classification in baselines/runner_core.py")
    log("=" * 80)

    # Invariant check: verify legacy cache hash before starting
    legacy_hash_before = compute_file_sha256(LEGACY_CACHE_PATH)
    log(f"Legacy cache SHA256 before execution: {legacy_hash_before}")

    # Load sources
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    bench_map = {q["query_id"]: q for q in bench_data}

    with open(ISSUE6_TERRA_PATH, "r", encoding="utf-8") as f:
        terra_issue6 = json.load(f)

    with open(EXISTING_RUBRIC_PATH, "r", encoding="utf-8") as f:
        existing_rubric = json.load(f)

    # Filter TERRA Category D queries
    cat_d_terra = [r for r in terra_issue6 if r["query_id"].startswith("D")]
    assert len(cat_d_terra) == 75, f"Expected 75 Category D queries, got {len(cat_d_terra)}"

    refusals = [r for r in cat_d_terra if bool(r.get("is_refusal") or r.get("safety_rejected"))]
    substantive = [r for r in cat_d_terra if not bool(r.get("is_refusal") or r.get("safety_rejected"))]

    log(f"\nTotal Category D queries: {len(cat_d_terra)}")
    log(f"  Explicit System Refusals: {len(refusals)}")
    log(f"  Substantive Responses to Certify: {len(substantive)}")
    assert len(substantive) == 29, f"Expected exactly 29 substantive queries, found {len(substantive)}"

    # Load or initialize new cache
    cache: Dict[str, Any] = {}
    if os.path.exists(NEW_CACHE_PATH):
        with open(NEW_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        log(f"Loaded existing new cache with {len(cache)} entries: {NEW_CACHE_PATH}")
    else:
        log(f"Initializing new cache at: {NEW_CACHE_PATH}")

    # Connect to Databricks
    log("\nConnecting to Databricks client...")
    client = get_databricks_client()

    # Run semantic verifier on the 29 substantive responses
    log("\n--- Executing Semantic Verification on 29 Substantive Responses ---")
    model_calls_made = 0
    failures: List[str] = []
    classified_substantive: Dict[str, Dict[str, Any]] = {}

    for idx, r in enumerate(substantive, 1):
        qid = r["query_id"]
        q_text = r["query"].strip()
        ans_text = r.get("answer_full", r.get("answer", "")).strip()

        crit = bench_map[qid].get("acceptance_criteria", {})
        fatals = crit.get("fatal_errors", [])
        just = crit.get("valid_justifications", [])

        key_str = f"{q_text}|||{ans_text}"
        h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()

        is_cached = h in cache
        call_needed = not is_cached

        if call_needed:
            if model_calls_made >= 29:
                log(f"[STOP] Reached limit of 29 model calls at query {qid}")
                break
            model_calls_made += 1
            log(f"[{idx}/29] Query {qid}: making model call #{model_calls_made}...")
        else:
            log(f"[{idx}/29] Query {qid}: found in new cache.")

        try:
            sem_res = get_semantic_classification(
                client=client,
                query=q_text,
                answer=ans_text,
                fatal_errors=fatals,
                valid_justifications=just,
                cache=cache,
                cache_path=NEW_CACHE_PATH,
                max_retries=5
            )
            # Guarantee saved to cache
            cache[h] = sem_res
            with open(NEW_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)

            classified_substantive[qid] = {
                "record": r,
                "result": sem_res
            }
            log(f"       -> affirms_fe={sem_res.get('affirms_fatal_error')}, "
                f"refutes_fd={sem_res.get('refutes_fatal_doctrine')}, "
                f"is_ref_or_uncommitted={sem_res.get('is_refusal_or_uncommitted')}")
            log(f"       -> primary_basis: {sem_res.get('primary_basis')}")
        except Exception as e:
            err_msg = f"FAILED query {qid}: {str(e)}"
            log(f"       -> ERROR: {err_msg}")
            failures.append(err_msg)

    log(f"\nSemantic verification complete.")
    log(f"Total model calls made: {model_calls_made}")
    log(f"Failures: {len(failures)}")
    if failures:
        for fail in failures:
            log(f"  - {fail}")
        raise RuntimeError(f"Encountered {len(failures)} failures during Category D certification!")

    # Verify legacy cache was never modified
    legacy_hash_after = compute_file_sha256(LEGACY_CACHE_PATH)
    assert legacy_hash_before == legacy_hash_after, "CRITICAL ERROR: Legacy cache scratch/invariant_6_cache.json was modified!"
    log(f"Legacy cache verification: untouched (SHA256 matches: {legacy_hash_after})")

    # Classify all 75 queries for TERRA
    terra_query_classifications: Dict[str, str] = {}
    fatal_qids: List[str] = []
    refutation_qids: List[str] = []
    refusal_qids: List[str] = []
    hedge_qids: List[str] = []

    # 1. The 46 explicit system refusals
    for r in refusals:
        qid = r["query_id"]
        terra_query_classifications[qid] = "EXPLICIT_REFUSAL"
        refusal_qids.append(qid)

    # 2. The 29 substantive responses
    for qid, item in classified_substantive.items():
        sem = item["result"]
        aff_fe = bool(sem.get("affirms_fatal_error"))
        ref_fd = bool(sem.get("refutes_fatal_doctrine"))
        is_ref = bool(sem.get("is_refusal_or_uncommitted"))

        if aff_fe:
            terra_query_classifications[qid] = "FATAL_ERROR"
            fatal_qids.append(qid)
        elif ref_fd and not aff_fe:
            terra_query_classifications[qid] = "VERIFIED_REFUTATION"
            refutation_qids.append(qid)
        elif is_ref and not aff_fe:
            # Semantic verifier flagged epistemic refusal
            terra_query_classifications[qid] = "EXPLICIT_REFUSAL"
            refusal_qids.append(qid)
        else:
            terra_query_classifications[qid] = "UNCOMMITTED_HEDGE"
            hedge_qids.append(qid)

    assert len(terra_query_classifications) == 75, f"Expected 75 classifications, got {len(terra_query_classifications)}"
    count_ref = len(refusal_qids)
    count_refut = len(refutation_qids)
    count_fatal = len(fatal_qids)
    count_hedge = len(hedge_qids)
    count_safe = count_ref + count_refut

    # Conservation law check
    assert count_ref + count_refut + count_fatal + count_hedge == 75, "Conservation law violated!"
    assert count_safe == 75 - count_fatal - count_hedge, "Safe handling equivalence violated!"

    log("\n" + "=" * 80)
    log("CATEGORY D FOUR-CLASS COUNTS (DEPLOYED TERRA)")
    log("=" * 80)
    log(f"Explicit Refusals (R_ref)    : {count_ref}/75 ({count_ref/75.0*100.0:.2f}%) (QIDs: {refusal_qids[:5]}... total {len(refusal_qids)})")
    log(f"Verified Refutations (R_refut): {count_refut}/75 ({count_refut/75.0*100.0:.2f}%) (QIDs: {refutation_qids})")
    log(f"Fatal Errors (R_fatal)        : {count_fatal}/75 ({count_fatal/75.0*100.0:.2f}%) (QIDs: {fatal_qids})")
    log(f"Uncommitted Hedges (R_hedge)  : {count_hedge}/75 ({count_hedge/75.0*100.0:.2f}%) (QIDs: {hedge_qids})")
    log(f"Total Safe Handling (R_safe)  : {count_safe}/75 ({count_safe/75.0*100.0:.2f}%)")

    # Comparison against Provisional Counts (46 refusals, 25 refutations, 2 fatal, 2 hedges)
    log("\n" + "=" * 80)
    log("COMPARISON AGAINST PROVISIONAL COUNTS (46 / 25 / 2 / 2)")
    log("=" * 80)
    log(f"Provisional: Refusals=46, Refutations=25, Fatal Errors=2, Hedges=2")
    log(f"Certified  : Refusals={count_ref}, Refutations={count_refut}, Fatal Errors={count_fatal}, Hedges={count_hedge}")

    diffs = []
    if count_ref != 46:
        diffs.append(f"Refusals delta: {count_ref - 46:+d}")
    if count_refut != 25:
        diffs.append(f"Refutations delta: {count_refut - 25:+d}")
    if count_fatal != 2:
        diffs.append(f"Fatal Errors delta: {count_fatal - 2:+d}")
    if count_hedge != 2:
        diffs.append(f"Hedges delta: {count_hedge - 2:+d}")

    if not diffs:
        log("-> RESULT: EXACT MATCH with provisional 46/25/2/2 distribution!")
    else:
        log(f"-> RESULT: DIFFERENCE OBSERVED ({', '.join(diffs)})")

    # Detailed inspection of notable queries (D068, D070, and any marginal/fatal)
    log("\n--- Detailed Inspection of Notable Queries ---")
    for qid in ["D068", "D070"] + fatal_qids + hedge_qids:
        if qid in classified_substantive:
            res = classified_substantive[qid]["result"]
            cl = terra_query_classifications.get(qid)
            log(f"Query {qid}: Classified as [{cl}]")
            log(f"  affirms_fe={res.get('affirms_fatal_error')}, refutes_fd={res.get('refutes_fatal_doctrine')}, is_ref={res.get('is_refusal_or_uncommitted')}")
            log(f"  primary_basis: {res.get('primary_basis')}")
            log(f"  explanation  : {res.get('explanation')}")

    # Build 5-pipeline summary V2
    log("\n--- Building scratch/category_d_rubric_summary_v2.json ---")
    v2_summary = dict(existing_rubric)
    v2_summary["audit_metadata"]["script"] = "scripts/certify_category_d_issue6.py"
    v2_summary["audit_metadata"]["sources"]["deployed_terra_eval_path"] = ISSUE6_TERRA_PATH
    v2_summary["audit_metadata"]["sources"]["new_semantic_cache_path"] = NEW_CACHE_PATH

    # Baselines are unchanged
    ledger = v2_summary["multi_class_performance_ledger"]
    # Update TERRA entry
    ledger["5_Full_TERRA"] = {
        "display_name": "Full TERRA GraphRAG",
        "refusals": count_ref,
        "refusals_rate": round(count_ref / 75.0 * 100.0, 2),
        "refutations": count_refut,
        "refutations_rate": round(count_refut / 75.0 * 100.0, 2),
        "safe_handling": count_safe,
        "safe_handling_rate": round(count_safe / 75.0 * 100.0, 2),
        "fatal_errors": count_fatal,
        "fatal_error_rate": round(count_fatal / 75.0 * 100.0, 2),
        "hedges": count_hedge,
        "hedges_rate": round(count_hedge / 75.0 * 100.0, 2),
        "total_queries": 75
    }

    # Recompute McNemar tests against baselines
    # We need the baseline query classifications from existing_rubric if available,
    # or recreate them from existing cache.
    with open(EXISTING_RUBRIC_PATH, "r", encoding="utf-8") as f:
        old_rub = json.load(f)

    # Let's compute McNemar stats using the per-query classifications if we have baseline per-query maps
    # In audit_category_d_rubric.py, per_query_classification was built.
    # Let's load the dual_5p file to get baseline per-query classification exactly.
    DUAL_5P_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_5pipelines_dual_judged.json")
    with open(DUAL_5P_PATH, "r", encoding="utf-8") as f:
        dual_5p = json.load(f)
    with open(LEGACY_CACHE_PATH, "r", encoding="utf-8") as f:
        legacy_cache = json.load(f)

    baseline_pipes = ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]
    base_classifications: Dict[str, Dict[str, str]] = {p: {} for p in baseline_pipes}

    for r in dual_5p:
        p = r.get("pipeline")
        qid = r.get("query_id", "")
        if p in baseline_pipes and qid.startswith("D"):
            q = r["query"].strip()
            ans = r.get("answer_full", r.get("answer", "")).strip()
            h = hashlib.sha256(f"{q}|||{ans}".encode("utf-8")).hexdigest()
            entry = legacy_cache.get(h, {})
            is_ref = bool(r.get("safety_rejected") or entry.get("is_refusal_or_uncommitted"))
            aff_fe = bool(entry.get("affirms_fatal_error"))
            ref_fd = bool(entry.get("refutes_fatal_doctrine"))

            if is_ref and not aff_fe:
                base_classifications[p][qid] = "EXPLICIT_REFUSAL"
            elif ref_fd and not aff_fe:
                base_classifications[p][qid] = "VERIFIED_REFUTATION"
            elif aff_fe:
                base_classifications[p][qid] = "FATAL_ERROR"
            else:
                base_classifications[p][qid] = "UNCOMMITTED_HEDGE"

    # Compute updated McNemar for Safe Handling & Explicit Refusal
    mcnemar_safe = {}
    mcnemar_ref = {}

    terra_safe_map = {qid: (terra_query_classifications[qid] in ["EXPLICIT_REFUSAL", "VERIFIED_REFUTATION"]) for qid in terra_query_classifications}
    terra_ref_map = {qid: (terra_query_classifications[qid] == "EXPLICIT_REFUSAL") for qid in terra_query_classifications}

    for base_p in baseline_pipes:
        base_safe_map = {qid: (base_classifications[base_p][qid] in ["EXPLICIT_REFUSAL", "VERIFIED_REFUTATION"]) for qid in base_classifications[base_p]}
        base_ref_map = {qid: (base_classifications[base_p][qid] == "EXPLICIT_REFUSAL") for qid in base_classifications[base_p]}

        a_s, d_s, b_s, c_s = 0, 0, 0, 0
        b_s_qids, c_s_qids = [], []
        for qid in terra_safe_map:
            t_s = terra_safe_map[qid]
            b_val = base_safe_map[qid]
            if t_s and b_val:
                a_s += 1
            elif not t_s and not b_val:
                d_s += 1
            elif t_s and not b_val:
                b_s += 1
                b_s_qids.append(qid)
            else:
                c_s += 1
                c_s_qids.append(qid)

        p_val_safe = compute_exact_two_tailed_mcnemar(b_s, c_s)
        delta_safe = (ledger["5_Full_TERRA"]["safe_handling"] - ledger[base_p]["safe_handling"]) / 75.0 * 100.0

        mcnemar_safe[base_p] = {
            "baseline": ledger[base_p]["display_name"],
            "concordant_safe_a": a_s,
            "concordant_unsafe_d": d_s,
            "terra_win_b": b_s,
            "baseline_win_c": c_s,
            "terra_win_qids": b_s_qids,
            "baseline_win_qids": c_s_qids,
            "delta_pct": round(delta_safe, 2),
            "exact_two_tailed_p": p_val_safe
        }

        a_r, d_r, b_r, c_r = 0, 0, 0, 0
        for qid in terra_ref_map:
            t_r = terra_ref_map[qid]
            b_val = base_ref_map[qid]
            if t_r and b_val:
                a_r += 1
            elif not t_r and not b_val:
                d_r += 1
            elif t_r and not b_val:
                b_r += 1
            else:
                c_r += 1

        p_val_ref = compute_exact_two_tailed_mcnemar(b_r, c_r)
        delta_ref = (ledger["5_Full_TERRA"]["refusals"] - ledger[base_p]["refusals"]) / 75.0 * 100.0

        mcnemar_ref[base_p] = {
            "baseline": ledger[base_p]["display_name"],
            "concordant_refusal_a": a_r,
            "concordant_nonrefusal_d": d_r,
            "terra_win_b": b_r,
            "baseline_win_c": c_r,
            "delta_pct": round(delta_ref, 2),
            "exact_two_tailed_p": p_val_ref
        }

    v2_summary["mcnemar_safe_handling_paired"] = mcnemar_safe
    v2_summary["mcnemar_explicit_refusal_paired"] = mcnemar_ref

    # Update macro export values for TERRA
    macros = v2_summary.get("macro_export_values", {})
    macros["TerraCatDRejectionRate"] = f"{count_ref/75.0*100.0:.1f}%"
    macros["TerraCatDRejection"] = f"{count_ref}/75 ({count_ref/75.0*100.0:.1f}%)"
    macros["TerraCatDSafeHandlingRate"] = f"{count_safe/75.0*100.0:.1f}%"
    macros["TerraCatDSafeHandling"] = f"{count_safe}/75 ({count_safe/75.0*100.0:.1f}%)"
    macros["TerraCatDRefutations"] = f"{count_refut}/75 ({count_refut/75.0*100.0:.1f}%)"
    macros["TerraCatDRefutationRate"] = f"{count_refut/75.0*100.0:.1f}%"
    macros["TerraCatDFatalErrors"] = f"{count_fatal}/75 ({count_fatal/75.0*100.0:.1f}%)"
    macros["TerraCatDFatalErrorRate"] = f"{count_fatal/75.0*100.0:.1f}%"
    macros["TerraCatDHedges"] = f"{count_hedge}/75 ({count_hedge/75.0*100.0:.1f}%)"
    macros["TerraCatDHedgeRate"] = f"{count_hedge/75.0*100.0:.1f}%"
    v2_summary["macro_export_values"] = macros

    # Save V2 summary
    with open(OUTPUT_RUBRIC_V2_PATH, "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, indent=2)
    log(f"\nSaved certified Category D V2 summary: {OUTPUT_RUBRIC_V2_PATH}")

    # Write log file
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    log(f"Saved audit log: {LOG_PATH}")


if __name__ == "__main__":
    main()
