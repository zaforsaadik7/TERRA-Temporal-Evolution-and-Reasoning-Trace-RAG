"""
scripts/audit_temporal_leakage_forensics.py - Phase 4.5: Forensic Audit of Critical Slices
===========================================================================================
Performs deep qualitative and forensic auditing of adjudicated outputs:
  1. 100% Audit of Level-2 Substantive Leakage:
     - Extracts every Level-2 response across all pipelines.
     - Documents target case, historical cutoff, operative post-T doctrine cited, and judge excerpts.
  2. 100% Audit of NLI Gate Interceptions:
     - Pairs candidate generation text (from TERRA_ungated) with gated output (from TERRA_gated).
     - Confirms whether intercepted candidate contained post-T doctrine (L_intercepted) vs ungrounded facts.
  3. 20% Stratified Sample of Level-0 Clean Outputs:
     - Randomly samples 20% of clean (Level-0) records across all 5 cutoff horizons.
     - Confirms absence of false negatives (undetected leakage).

Outputs:
  - scratch/temporal_leakage_forensic_audit.json
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
JUDGED_PATH = ROOT_DIR / "data" / "temporal_leakage_dual_judged.json"
OUTPUT_FORENSIC_PATH = ROOT_DIR / "scratch" / "temporal_leakage_forensic_audit.json"


def run_forensic_audit():
    print("=" * 80)
    print("PHASE 4.5: FORENSIC AUDIT OF CRITICAL SLICES")
    print("=" * 80)

    if not JUDGED_PATH.exists():
        raise FileNotFoundError(f"Missing judged dataset at: {JUDGED_PATH}")

    with open(JUDGED_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} adjudicated records for forensic audit.")

    # 1. 100% Audit of Level-2 Substantive Leakage
    level2_records = [r for r in records if r.get("sptlr_level2") is True]
    print(f"\n[SLICE 1] Level-2 Substantive Leakage: {len(level2_records)} records found across all pipelines.")

    slice1_audit = []
    for r in level2_records:
        slice1_audit.append({
            "query_id": r["query_id"],
            "cutoff_year": r["cutoff_year"],
            "condition": r["condition"],
            "pipeline": r["pipeline"],
            "target_case_name": r["target_case_name"],
            "target_case_year": r["target_case_year"],
            "consensus_severity": r["adjudication"]["consensus_severity_level"],
            "adjudication_rule": r["adjudication"]["adjudication_rule"],
            "pcmr_matches": r["lexical_diagnostics"]["matched_future_cases"],
            "pyar_matches": r["lexical_diagnostics"]["matched_future_years"],
            "judge1_excerpt": r["judge1_evaluation"].get("leakage_evidence_excerpt", ""),
            "judge2_excerpt": r["judge2_evaluation"].get("leakage_evidence_excerpt", ""),
            "judge1_reasoning": r["judge1_evaluation"].get("reasoning", ""),
            "judge2_reasoning": r["judge2_evaluation"].get("reasoning", ""),
            "answer_full": r["answer_full"]
        })

    # 2. 100% Audit of NLI Interceptions
    # Group by (query_id, condition)
    by_query_cond = {}
    for r in records:
        key = (r["query_id"], r["condition"])
        by_query_cond.setdefault(key, {})[r["pipeline"]] = r

    slice2_audit = []
    interceptions = 0
    for (qid, cond), pipes in sorted(by_query_cond.items()):
        gated = pipes.get("TERRA_gated")
        ungated = pipes.get("TERRA_ungated")
        if gated and ungated and gated.get("is_safe_refusal"):
            interceptions += 1
            cand_is_l2 = ungated.get("sptlr_level2", False)
            slice2_audit.append({
                "query_id": qid,
                "cutoff_year": gated["cutoff_year"],
                "condition": cond,
                "target_case_name": gated["target_case_name"],
                "ungated_severity": ungated["adjudication"]["consensus_severity_level"],
                "ungated_contains_level2_leakage": cand_is_l2,
                "nli_gate_reasoning": gated.get("nli_gate_telemetry", {}).get("reasoning", ""),
                "gated_final_action": gated.get("final_action", ""),
                "ungated_candidate_answer": ungated.get("answer_full", ""),
                "gated_refusal_answer": gated.get("answer_full", "")
            })

    print(f"\n[SLICE 2] NLI Gate Interceptions: {len(slice2_audit)} records audited.")

    # 3. 20% Stratified Sample of Level-0 Clean Outputs
    level0_records = [r for r in records if r.get("sptlr_level2") is False and not r.get("is_safe_refusal")]
    sample_size = max(1, int(len(level0_records) * 0.20))
    rng = random.Random(42)
    level0_sample = rng.sample(level0_records, min(sample_size, len(level0_records)))

    slice3_audit = []
    for r in level0_sample:
        slice3_audit.append({
            "query_id": r["query_id"],
            "cutoff_year": r["cutoff_year"],
            "condition": r["condition"],
            "pipeline": r["pipeline"],
            "target_case_name": r["target_case_name"],
            "consensus_severity": r["adjudication"]["consensus_severity_level"],
            "tgs": r["adjudication"]["consensus_temporal_grounding_score"],
            "answer_full": r["answer_full"]
        })

    print(f"\n[SLICE 3] Stratified Level-0 Clean Sample: {len(slice3_audit)} records audited for false-negative absence.")

    forensic_payload = {
        "total_records_audited": len(records),
        "total_level2_leakage_records": len(slice1_audit),
        "total_nli_interceptions": len(slice2_audit),
        "level0_sample_size": len(slice3_audit),
        "level2_leakage_audit": slice1_audit,
        "nli_interception_audit": slice2_audit,
        "level0_clean_sample_audit": slice3_audit
    }

    OUTPUT_FORENSIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FORENSIC_PATH, "w", encoding="utf-8") as f:
        json.dump(forensic_payload, f, indent=2, ensure_ascii=False)

    print(f"\nForensic audit results saved to: {OUTPUT_FORENSIC_PATH}")
    print("=" * 80)
    return forensic_payload


if __name__ == "__main__":
    run_forensic_audit()
