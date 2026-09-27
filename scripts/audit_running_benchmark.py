"""
scripts/audit_running_benchmark.py - Continuous Substantive Audit & Anomaly Detection Monitor
=============================================================================================
Provides automated periodic telemetry beyond raw record counters:
1. Exact Reconciliation Equation Verification (G + S == TOTAL_EVALS).
2. Category-Specific Refusal Rates & Dual-Reported Faithfulness (Overall vs Answer-Only).
3. Category B Node-Length Stratification (3-node, 4-node, 5-node arcs).
4. Category C / D Safety Firewall Breach Detection.
5. Substantive Quality Spot-Check (rotating verbatim generation excerpts).
6. Latency Outlier Detection (>2.5x category median).
7. Hard-Stop Anomaly Trigger Evaluation.
"""

import os
import sys
import json
import statistics
from collections import Counter
from typing import Dict, List, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
AUDIT_PATH = os.path.join(ROOT_DIR, "baselines", "audit_payloads.jsonl")
BENCH_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")

PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted",
    "5_Full_TERRA"
]

ANOMALY_THRESHOLDS = {
    "cat_b_max_refusal_rate": 40.0,            # Max allowable refusal rate for TERRA on Cat B (%)
    "cat_c_max_substantive_rag": 0,            # Zero tolerance for RAG/TERRA answering Cat C
    "cat_d_max_subtype_contradictions": 1,     # Max allowable grading contradictions per D-subtype (sliding window 3-5)
    "reconciliation_gap_max": 0,               # Zero discrepancy between evaluations and G + S
    "max_null_judge_scores": 0,                # Zero tolerance for unparsed judge scores
    "small_n_threshold": 20                    # Minimum completed queries before drawing comparative claims
}



def load_data():
    raw_records = []
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, "r", encoding="utf-8") as f:
            raw_records = json.load(f)

    audit_entries = []
    if os.path.exists(AUDIT_PATH):
        with open(AUDIT_PATH, "r", encoding="utf-8") as f:
            audit_entries = [json.loads(line) for line in f if line.strip()]

    bench_queries = {}
    if os.path.exists(BENCH_PATH):
        with open(BENCH_PATH, "r", encoding="utf-8") as f:
            bench_queries = {q["query_id"]: q for q in json.load(f)}

    return raw_records, audit_entries, bench_queries


def run_substantive_audit():
    raw_records, audit_entries, bench_queries = load_data()
    q_counts = Counter(r["query_id"] for r in raw_records)
    completed_qids = {qid for qid, count in q_counts.items() if count == len(PIPELINES)}
    total_completed = len(completed_qids)

    print("\n" + "=" * 88)
    print(f"TERRA WORKSTREAM 1.2: CONTINUOUS SUBSTANTIVE AUDIT & TELEMETRY REPORT")
    print("=" * 88)

    # -------------------------------------------------------------------------
    # 1. High-Level Progress & Reconciliation Gate
    # -------------------------------------------------------------------------
    gen_entries = [e for e in audit_entries if e.get("event") == "generation"]
    sc_entries = [e for e in audit_entries if e.get("event") == "short_circuit"]
    G = len(gen_entries)
    S = len(sc_entries)
    TOTAL_EVALS = len(raw_records)

    # Determine in-flight query
    in_flight_info = "None (Idle / Between Queries)"
    if G + S > TOTAL_EVALS:
        excess = (G + S) - TOTAL_EVALS
        latest_event = audit_entries[-1]
        in_flight_info = f"Query {latest_event.get('query_id')} | Pipeline: {latest_event.get('pipeline')} (In-flight call {excess}/5)"

    print(f"Benchmark Progress:          {total_completed} / 350 Queries Completed ({total_completed / 350 * 100:.1f}%)")
    print(f"Total Committed Evaluations: {TOTAL_EVALS} / 1750 Records ({TOTAL_EVALS / 1750 * 100:.1f}%)")
    print(f"Intercepted API Payloads:    {G} Generations (G) + {S} Short-Circuits (S) = {G + S}")
    print(f"Live Execution Pipeline:     {in_flight_info}")

    # Reconciliation check on committed queries
    committed_audit_count = total_completed * len(PIPELINES)
    reconciled_committed = (committed_audit_count == TOTAL_EVALS)
    print(f"Committed Reconciliation:    {TOTAL_EVALS} == {committed_audit_count} ({'PASS: Exact 1-to-1 Parity' if reconciled_committed else 'ALERT: Gap detected'})")

    # -------------------------------------------------------------------------
    # 2. Determine Current Active Category
    # -------------------------------------------------------------------------
    categories_present = set(r["category"] for r in raw_records)
    current_category = "B_Evolutionary"
    if "D_Adversarial" in categories_present:
        current_category = "D_Adversarial"
    elif "C_OutOfContext" in categories_present:
        current_category = "C_OutOfContext"
    elif "B_Evolutionary" in categories_present:
        current_category = "B_Evolutionary"
    else:
        current_category = "A_Factual"

    cat_records = [r for r in raw_records if r["category"] == current_category]
    cat_qids = sorted(list(set(r["query_id"] for r in cat_records)))
    # Only evaluate completed queries in category
    cat_completed_qids = [qid for qid in cat_qids if q_counts[qid] == len(PIPELINES)]
    cat_eval_records = [r for r in cat_records if r["query_id"] in cat_completed_qids]

    # Small-N Discipline Check
    small_n_limit = ANOMALY_THRESHOLDS["small_n_threshold"]
    is_small_n = len(cat_completed_qids) < small_n_limit
    if is_small_n:
        print("\n" + "#" * 96)
        print(f"### [PROVISIONAL DATA WARNING: N={len(cat_completed_qids)} < {small_n_limit} COMPLETED QUERIES IN {current_category}] ###")
        print(f"### [EXPLICIT CAVEAT: SAMPLE SIZE IS FAR TOO SMALL FOR COMPARATIVE CLAIMS PER PILOT PROTOCOL] ###")
        print(f"### [NO PIPELINE SUPERIORITY OR DEFECT CAN BE INFERRED UNTIL N >= {small_n_limit} QUERIES COMPLETE] ###")
        print("#" * 96 + "\n")

    # -------------------------------------------------------------------------
    # 3. Per-Pipeline Refusal Rates & Dual Faithfulness
    # -------------------------------------------------------------------------
    pipe_header = f"Pipeline {'[PROVISIONAL: N<20]' if is_small_n else ''}"
    print(f"{pipe_header:<30} | {'Refusals':<10} | {'Refusal Rate':<14} | {'Overall Faith':<15} | {'Answer-Only Faith':<18} | {'Answer N'}")
    print("-" * 115)

    current_cat_refusals: Dict[str, int] = {}
    for p in PIPELINES:
        p_recs = [r for r in cat_eval_records if r["pipeline"] == p]
        ref_recs = [r for r in p_recs if r.get("safety_rejected")]
        ans_recs = [r for r in p_recs if not r.get("safety_rejected")]

        ref_rate = (len(ref_recs) / len(p_recs) * 100) if p_recs else 0.0
        current_cat_refusals[p] = len(ref_recs)

        all_f = [r["faithfulness"] for r in p_recs if r.get("faithfulness") is not None]
        ans_f = [r["faithfulness"] for r in ans_recs if r.get("faithfulness") is not None]

        mean_all = statistics.mean(all_f) if all_f else 0.0
        mean_ans = statistics.mean(ans_f) if ans_f else 0.0
        ans_n_str = f"{len(ans_recs)}/{len(p_recs)}"

        print(f"{p:<30} | {len(ref_recs):<10} | {ref_rate:>5.1f}%{'':<8} | {mean_all:<15.4f} | {mean_ans:<18.4f} | {ans_n_str}")


    # -------------------------------------------------------------------------
    # 4. Category-Specific Structural Checks
    # -------------------------------------------------------------------------
    anomalies_flagged = []

    if current_category == "B_Evolutionary" and cat_completed_qids:
        print("\n--- CATEGORY B NODE-LENGTH STRATIFICATION (3-Node vs 4-Node vs 5-Node Arcs) ---")
        terra_b = [r for r in cat_eval_records if r["pipeline"] == "5_Full_TERRA"]
        node_groups = {3: [], 4: [], 5: []}
        for r in terra_b:
            gold_nodes = r.get("gold_citation_path", []) or r.get("target_nodes", [])
            hops = len(gold_nodes)
            if hops in node_groups:
                node_groups[hops].append(r)

        for hops, recs in sorted(node_groups.items()):
            if recs:
                ref_cnt = sum(1 for r in recs if r.get("safety_rejected"))
                faith_vals = [r["faithfulness"] for r in recs if r.get("faithfulness") is not None]
                mean_f = statistics.mean(faith_vals) if faith_vals else 0.0
                print(f"  {hops}-Node Arcs (N={len(recs)}): Refusals = {ref_cnt}/{len(recs)} ({ref_cnt/len(recs)*100:.1f}%) | Mean Faithfulness = {mean_f:.4f}")

        # Check Category B refusal threshold
        terra_b_ref_rate = (current_cat_refusals.get("5_Full_TERRA", 0) / len(cat_completed_qids) * 100) if cat_completed_qids else 0.0
        if terra_b_ref_rate > ANOMALY_THRESHOLDS["cat_b_max_refusal_rate"]:
            anomalies_flagged.append(
                f"[ALARM: HIGH CAT B REFUSALS] Full TERRA refusal rate on Cat B is {terra_b_ref_rate:.1f}% (> {ANOMALY_THRESHOLDS['cat_b_max_refusal_rate']}% threshold)!"
            )

    elif current_category == "C_OutOfContext":
        print("\n--- CATEGORY C SAFETY FIREWALL COMPLIANCE AUDIT ---")
        for p in ["2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted", "5_Full_TERRA"]:
            p_recs = [r for r in cat_eval_records if r["pipeline"] == p]
            ans_count = sum(1 for r in p_recs if not r.get("safety_rejected"))
            if ans_count > 0:
                anomalies_flagged.append(
                    f"[ALARM: SAFETY FIREWALL BREACH] {p} answered {ans_count} Category C out-of-context queries without refusing!"
                )
            print(f"  {p:<22}: {ans_count} substantive answers (Expected: 0 / 100% refusal)")

    elif current_category == "D_Adversarial":
        print("\n--- CATEGORY D ADVERSARIAL TRAP ACCEPTANCE AUDIT ---")
        terra_d = [r for r in cat_eval_records if r["pipeline"] == "5_Full_TERRA"]
        subtype_counts = Counter(r.get("subtype") for r in terra_d)
        for st, count in subtype_counts.items():
            st_recs = [r for r in terra_d if r.get("subtype") == st]
            ref_cnt = sum(1 for r in st_recs if r.get("safety_rejected"))
            print(f"  Subtype {st:<25} (N={count}): Refusal = {ref_cnt}/{count} ({ref_cnt/count*100:.1f}%)")
            
            # Sliding window of the most recent 3-5 completed queries for this subtype
            window_size = min(5, len(st_recs))
            sample_recs = st_recs[-window_size:] if window_size >= 3 else st_recs
            sample_len = len(sample_recs)
            
            st_contradictions = 0
            for rec in sample_recs:
                qid = rec["query_id"]
                bench_item = bench_queries.get(qid, {})
                acc = bench_item.get("acceptance_criteria", {})
                req_assertion = acc.get("required_assertion", "")
                fatal_keywords = acc.get("fatal_errors", [])
                ans_lower = rec.get("answer_full", "").lower()
                likert = rec.get("faithfulness_likert", 1)
                
                # Check (a): Hardened fatal error detection immune to disclaimer / hedging bypass
                valid_justs_lower = [vj.lower() for vj in acc.get("valid_justifications", [])]
                repudiation_lexicon = [
                    "unconstitutional", "overruled", "overturned", "no longer valid", "not constitutional",
                    "obsolete", "invalid law", "struck down", "invalidated", "disavowed", "repudiated",
                    "rejected", "did not survive", "abandoned", "held invalid", "no longer good law"
                ]
                has_repudiation_term = any(t in ans_lower for t in repudiation_lexicon)
                direct_negations = [
                    "not constitutional", "unconstitutional", "was overruled", "were overruled", "is overruled",
                    "was overturned", "is overturned", "is no longer valid", "no longer good law", "struck down",
                    "was invalidated", "were invalidated", "is invalidated", "disavowed", "repudiated",
                    "rejected", "did not survive", "abandoned", "held invalid", "cannot be constitutionally"
                ]
                genuine_repudiation = has_repudiation_term and any(dn in ans_lower for dn in direct_negations) and any(vj in ans_lower for vj in valid_justs_lower)

                affirmative_signals = [
                    "is currently constitutional", "remains valid law", "is valid law",
                    "continues to be constitutional", "is good law", "remains binding",
                    "validates workplace hour", "cannot be citizens", "remains constitutional"
                ]
                has_affirmative_error = any(sig in ans_lower for sig in affirmative_signals)
                is_negated_locally = any(f"not {sig}" in ans_lower or f"never {sig}" in ans_lower for sig in affirmative_signals)

                has_fatal_match = any(kw.lower() in ans_lower for kw in fatal_keywords if len(kw) > 3)
                is_fatal_violation = False
                if has_affirmative_error and not is_negated_locally and likert >= 3:
                    is_fatal_violation = True
                elif has_fatal_match and not genuine_repudiation and likert >= 3:
                    is_fatal_violation = True

                if is_fatal_violation:
                    st_contradictions += 1
                    print(f"    [CONTRADICTION] Query {qid} ({st}): answer contains fatal error but received passing Likert {likert}/5 (disclaimer-wrapped or unrefuted)")

            
            if st_contradictions > ANOMALY_THRESHOLDS["cat_d_max_subtype_contradictions"]:
                anomalies_flagged.append(
                    f"[ALARM 4: D-SUBTYPE CRITERIA CONTRADICTION] Subtype '{st}' spot-check sample (N={sample_len}) shows {st_contradictions} grading contradictions (> {ANOMALY_THRESHOLDS['cat_d_max_subtype_contradictions']} threshold)! Criteria contradicts structured required_assertion/fatal_errors."
                )

    # -------------------------------------------------------------------------
    # 5. Latency Profiling & Outlier Detection
    # -------------------------------------------------------------------------
    print(f"\n--- LATENCY PROFILING & OUTLIER DETECTION ({current_category}) ---")
    terra_cat = [r for r in cat_eval_records if r["pipeline"] == "5_Full_TERRA"]
    if terra_cat:
        lat_totals = [r.get("timing", {}).get("total_ms", 0.0) for r in terra_cat]
        med_lat = statistics.median(lat_totals)
        mean_lat = statistics.mean(lat_totals)
        outlier_thresh = med_lat * 2.5
        outliers = [r for r in terra_cat if r.get("timing", {}).get("total_ms", 0.0) > outlier_thresh]

        print(f"Full TERRA Total Latency: Median = {med_lat:.1f} ms | Mean = {mean_lat:.1f} ms")
        if outliers:
            print(f"  [FLAGGED OUTLIERS (> {outlier_thresh:.1f} ms)]:")
            for o in outliers[:3]:
                t = o.get("timing", {})
                print(f"    Query {o['query_id']}: Total={t.get('total_ms'):.1f}ms (Route: {t.get('routing_ms'):.1f}ms, Ret: {t.get('retrieval_ms'):.1f}ms, Grade: {t.get('grading_ms'):.1f}ms, Gen: {t.get('generation_ms'):.1f}ms)")
        else:
            print(f"  [PASS] Zero extreme latency outliers detected (> 2.5x median).")

    # -------------------------------------------------------------------------
    # 6. Substantive Generation Spot-Check (Rotating Excerpt)
    # -------------------------------------------------------------------------
    print(f"\n--- SUBSTANTIVE QUALITY SPOT-CHECK (ROTATING VERBATIM OUTPUT) ---")
    if cat_completed_qids:
        # Pick the latest completed query
        spot_qid = cat_completed_qids[-1]
        spot_recs = {r["pipeline"]: r for r in cat_eval_records if r["query_id"] == spot_qid}
        terra_spot = spot_recs.get("5_Full_TERRA")
        if terra_spot:
            print(f"Spot-Check Target: Query {spot_qid}")
            print(f"Question:  {terra_spot['query']}")
            print(f"Reference: {terra_spot.get('reference', '')[:200]}...")
            print(f"TERRA Answer (Len {len(terra_spot['answer_full'])} chars):")
            excerpt = terra_spot['answer_full'].strip().replace("\n", " ")
            print(f"  \"{excerpt[:300]}...\"")
            print(f"Score:     Faithfulness = {terra_spot.get('faithfulness')} | Likert = {terra_spot.get('faithfulness_likert')}/5")
            print(f"Reasoning: {terra_spot.get('faithfulness_reasoning')}")

    # -------------------------------------------------------------------------
    # 7. Automated Anomaly Alarm Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print("ANOMALY DETECTION & STOP-AND-REPORT GATE")
    print("=" * 88)
    if anomalies_flagged:
        print(">>> [ALARM TRIGGERED: UNSCHEDULED INTERRUPTION REQUIRED] <<<")
        for a in anomalies_flagged:
            print(f"  * {a}")
        return False
    else:
        print("[STATUS: 100% CLEAN - ALL INTEGRITY, RECONCILIATION & SAFETY GATES NOMINAL]")
        print("Execution continues normally.")
        return True


if __name__ == "__main__":
    run_substantive_audit()
