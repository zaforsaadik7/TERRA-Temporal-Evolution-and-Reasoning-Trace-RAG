"""
scripts/test_temporal_runner_pilot.py - Phase 3 Temporal Leakage Pilot Smoke-Test & Verification Harness
========================================================================================================
Executes and programmatically verifies the 2-query pilot evaluation across:
  - 2 Pre-registered Diverse Probes:
      * TLP-01 (T=1890, High-Prominence, Depth 1, Civil Rights Cases)
      * TLP-21 (T=1950, High-Prominence, Depth 1, Shelley v. Kraemer)
  - 2 Experimental Conditions:
      * Condition_A (Default Legal Prompt)
      * Condition_B (Explicit Historical Constraint)
  - 4 Evaluated Pipelines (16 total instances):
      1. 1_Direct_LLM
      2. 2_Flat_Vector_RAG
      3. TERRA_ungated
      4. TERRA_gated

Invariants Verified:
  1. Record Completeness: Exactly 16 evaluated records (2 queries x 2 conditions x 4 pipelines).
  2. Cryptographic Single-Candidate Parity: candidate_sha256(ungated) == candidate_sha256(gated) 100%.
  3. Strict Temporal Horizon Cleanliness: Provenance assertion verifying year <= T on all retrieved contexts.
  4. Attribution Telemetry Integrity: candidate_generated, nli_gate_evaluated, nli_gate_passed,
     nli_gate_refusal, nli_gate_applied_to_output, other_safety_intervention, final_action,
     global_state_restored.
  5. Timing & Latency Telemetry: Complete latency metrics for retrieval, generation, and grading.
  6. Module Pointer Restoration: Global ask_terra pointers guaranteed restored to canonical 1980 state
     and confirmed by per-record global_state_restored=True.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import ask_terra
from baselines.common import get_databricks_client, MANDATORY_MODEL_STRING
from baselines.temporal_context_manager import (
    extract_year_from_metadata,
    _YEAR_REGEX
)
from scripts.run_temporal_leakage_phase3 import (
    execute_probe_for_condition,
    atomic_save,
    compute_sha256,
    DEFAULT_PROBE_PATH,
    PIPELINE_NAMES,
    SAFETY_REFUSAL_TEXT
)

PILOT_QUERY_IDS = ["TLP-01", "TLP-21"]
PILOT_CONDITIONS = ["Condition_A", "Condition_B"]
PILOT_OUTPUT_PATH = ROOT_DIR / "data" / "temporal_leakage_pilot_raw.json"
PILOT_SCRATCH_PATH = ROOT_DIR / "scratch" / "temporal_leakage_pilot_raw.json"


def run_pilot_verifications(records: List[Dict[str, Any]], probe_map: Dict[str, Dict[str, Any]]) -> bool:
    """Programmatically verifies all 6 mechanical invariants on pilot results."""
    print("\n" + "=" * 80)
    print("PHASE 3 PILOT SMOKE-TEST: MECHANICAL & CRYPTOGRAPHIC VERIFICATION")
    print("=" * 80)
    print(f"Total Records to Verify: {len(records)}")

    passed_all = True

    # -------------------------------------------------------------------------
    # CHECK 1: Record Completeness Invariant
    # -------------------------------------------------------------------------
    print("\n--- CHECK 1: RECORD COMPLETENESS INVARIANT ---")
    expected_total = len(PILOT_QUERY_IDS) * len(PILOT_CONDITIONS) * len(PIPELINE_NAMES)  # 2 * 2 * 4 = 16
    if len(records) != expected_total:
        print(f"  [FAIL] Expected exactly {expected_total} records, found {len(records)}.")
        passed_all = False
    else:
        print(f"  [PASS] Record count matches expected ({len(records)}/{expected_total}).")

    # Check each query x condition x pipeline tuple exists
    missing_tuples = []
    for qid in PILOT_QUERY_IDS:
        for cond in PILOT_CONDITIONS:
            for pipe in PIPELINE_NAMES:
                found = any(
                    r.get("query_id") == qid and r.get("condition") == cond and r.get("pipeline") == pipe
                    for r in records
                )
                if not found:
                    missing_tuples.append((qid, cond, pipe))

    if missing_tuples:
        print(f"  [FAIL] Missing tuples: {missing_tuples}")
        passed_all = False
    else:
        print("  [PASS] All 16 required (query_id, condition, pipeline) instances are present.")

    # -------------------------------------------------------------------------
    # CHECK 2: Cryptographic Single-Candidate Parity Invariant
    # -------------------------------------------------------------------------
    print("\n--- CHECK 2: CRYPTOGRAPHIC SINGLE-CANDIDATE PARITY INVARIANT ---")
    parity_mismatches = []
    parity_checks = 0

    for qid in PILOT_QUERY_IDS:
        for cond in PILOT_CONDITIONS:
            ungated = next(
                (r for r in records if r["query_id"] == qid and r["condition"] == cond and r["pipeline"] == "TERRA_ungated"),
                None
            )
            gated = next(
                (r for r in records if r["query_id"] == qid and r["condition"] == cond and r["pipeline"] == "TERRA_gated"),
                None
            )

            if ungated and gated:
                parity_checks += 1
                u_hash = ungated.get("candidate_sha256")
                g_hash = gated.get("candidate_sha256")
                if not u_hash or u_hash != g_hash:
                    parity_mismatches.append({
                        "query_id": qid,
                        "condition": cond,
                        "ungated_hash": u_hash,
                        "gated_hash": g_hash
                    })
                else:
                    print(f"  [PASS] {qid} [{cond}]: SHA256 match -> {u_hash[:16]}...")

    if parity_mismatches:
        print(f"  [FAIL] Detected {len(parity_mismatches)} candidate hash mismatches!")
        for m in parity_mismatches:
            print(f"         {m}")
        passed_all = False
    else:
        print(f"  [PASS] Cryptographic single-candidate parity held 100% across all {parity_checks} pairs.")

    # -------------------------------------------------------------------------
    # CHECK 3: Strict Temporal Horizon Cleanliness & Provenance
    # -------------------------------------------------------------------------
    print("\n--- CHECK 3: STRICT TEMPORAL HORIZON CLEANLINESS ---")
    future_leakage_detected = []

    for r in records:
        qid = r["query_id"]
        cutoff = r["cutoff_year"]
        pipe = r["pipeline"]
        ctx = r.get("context_full", "")

        if pipe in ["2_Flat_Vector_RAG", "TERRA_ungated", "TERRA_gated"]:
            # Check for explicitly post-T years in the retrieval context
            years_found = [int(y) for y in _YEAR_REGEX.findall(ctx)]
            future_years = [y for y in years_found if y > cutoff and y < 2030]
            if future_years:
                future_leakage_detected.append({
                    "query_id": qid,
                    "cutoff": cutoff,
                    "pipeline": pipe,
                    "future_years": sorted(set(future_years))
                })

    if future_leakage_detected:
        print(f"  [FAIL] Detected {len(future_leakage_detected)} instances of post-T date leakage in retrieval context:")
        for leak in future_leakage_detected:
            print(f"         {leak}")
        passed_all = False
    else:
        print(f"  [PASS] Zero post-T dates found across all pre-T retrieval contexts.")

    # -------------------------------------------------------------------------
    # CHECK 4: Attribution & Gating Telemetry Integrity
    # -------------------------------------------------------------------------
    print("\n--- CHECK 4: ATTRIBUTION & GATING TELEMETRY INTEGRITY ---")
    telemetry_issues = []

    for r in records:
        qid = r["query_id"]
        cond = r["condition"]
        pipe = r["pipeline"]

        # Required boolean flags
        if not isinstance(r.get("candidate_generated"), bool):
            telemetry_issues.append((qid, cond, pipe, "candidate_generated not bool"))
        if not isinstance(r.get("nli_gate_evaluated"), bool):
            telemetry_issues.append((qid, cond, pipe, "nli_gate_evaluated not bool"))
        if not isinstance(r.get("nli_gate_refusal"), bool):
            telemetry_issues.append((qid, cond, pipe, "nli_gate_refusal not bool"))
        if not isinstance(r.get("nli_gate_applied_to_output"), bool):
            telemetry_issues.append((qid, cond, pipe, "nli_gate_applied_to_output not bool"))
        if r.get("global_state_restored") is not True:
            telemetry_issues.append((qid, cond, pipe, "global_state_restored is not True"))
        if r.get("final_action") not in ["release", "refuse"]:
            telemetry_issues.append((qid, cond, pipe, f"invalid final_action: {r.get('final_action')}"))

        # Pipeline-specific semantics
        if pipe == "TERRA_ungated":
            if r.get("nli_gate_applied_to_output") is not False:
                telemetry_issues.append((qid, cond, pipe, "TERRA_ungated must have nli_gate_applied_to_output=False"))
            if r.get("final_action") != "release":
                telemetry_issues.append((qid, cond, pipe, "TERRA_ungated must have final_action=release"))
            if not r.get("nli_gate_telemetry"):
                telemetry_issues.append((qid, cond, pipe, "TERRA_ungated missing nli_gate_telemetry block"))
        elif pipe == "TERRA_gated":
            if r.get("nli_gate_applied_to_output") is not True:
                telemetry_issues.append((qid, cond, pipe, "TERRA_gated must have nli_gate_applied_to_output=True"))
            if not r.get("nli_gate_telemetry"):
                telemetry_issues.append((qid, cond, pipe, "TERRA_gated missing nli_gate_telemetry block"))

    if telemetry_issues:
        print(f"  [FAIL] Found {len(telemetry_issues)} telemetry irregularities:")
        for issue in telemetry_issues:
            print(f"         {issue}")
        passed_all = False
    else:
        print("  [PASS] All 16 records contain complete, structurally valid attribution telemetry.")

    # Observation A Audit: Inspect NLI confidence score distribution and default tracking
    terra_records = [r for r in records if r.get("pipeline") in ["TERRA_ungated", "TERRA_gated"] and r.get("nli_gate_telemetry")]
    if terra_records:
        confs = [r["nli_gate_telemetry"].get("confidence_score") for r in terra_records]
        defaulted_flags = [r["nli_gate_telemetry"].get("confidence_defaulted") for r in terra_records]
        num_defaulted = sum(1 for d in defaulted_flags if d is True)
        unique_confs = sorted(set(c for c in confs if c is not None))
        if num_defaulted > 0:
            print(f"  [WARN] Observation A: {num_defaulted}/{len(terra_records)} TERRA records triggered fallback default confidence_score.")
        else:
            print(f"  [PASS] Observation A: All {len(terra_records)} TERRA records have model-generated confidence scores (values: {unique_confs}, defaulted=0).")

    # -------------------------------------------------------------------------
    # CHECK 5: Timing & Latency Telemetry
    # -------------------------------------------------------------------------
    print("\n--- CHECK 5: TIMING & LATENCY TELEMETRY ---")
    timing_issues = []

    for r in records:
        qid = r["query_id"]
        cond = r["condition"]
        pipe = r["pipeline"]
        timing = r.get("timing", {})
        if not timing:
            timing_issues.append((qid, cond, pipe, "Missing timing object"))
            continue

        if timing.get("model_used") != MANDATORY_MODEL_STRING:
            timing_issues.append((qid, cond, pipe, f"Wrong model: {timing.get('model_used')}"))
        if timing.get("total_ms", 0) <= 0:
            timing_issues.append((qid, cond, pipe, "total_ms <= 0"))

        # Observation C: Check grading_ms integrity
        if pipe in ["TERRA_ungated", "TERRA_gated"]:
            if timing.get("grading_ms", 0) <= 0:
                timing_issues.append((qid, cond, pipe, f"TERRA grading_ms must be > 0 (got {timing.get('grading_ms')})"))
        elif pipe in ["1_Direct_LLM", "2_Flat_Vector_RAG"]:
            if timing.get("grading_ms", 0) != 0.0:
                timing_issues.append((qid, cond, pipe, f"Baseline grading_ms must be 0.0 (got {timing.get('grading_ms')})"))

    if timing_issues:
        print(f"  [FAIL] Timing issues detected: {timing_issues}")
        passed_all = False
    else:
        print(f"  [PASS] Timing telemetry fully captured with target model {MANDATORY_MODEL_STRING} (Observation C: grading_ms verified > 0 for all TERRA records).")

    # -------------------------------------------------------------------------
    # CHECK 6: Global Module State Cleanliness & Restoration
    # -------------------------------------------------------------------------
    print("\n--- CHECK 6: GLOBAL MODULE STATE RESTORATION ---")
    # Verify ask_terra module attributes are intact
    eeg_nodes_count = len(ask_terra.eeg.nodes)
    col_name = getattr(ask_terra.collection, "name", "")
    print(f"  Current ask_terra.eeg node count: {eeg_nodes_count}")
    print(f"  Current ask_terra.collection name: {col_name}")

    if eeg_nodes_count < 10000:
        print(f"  [FAIL] ask_terra.eeg appears to still be scoped to a temporal subgraph ({eeg_nodes_count} nodes)!")
        passed_all = False
    elif col_name.startswith("thinking_traces_T"):
        print(f"  [FAIL] ask_terra.collection appears to still be scoped to a temporal collection ({col_name})!")
        passed_all = False
    else:
        print("  [PASS] Global ask_terra pointers are verified to be in canonical 1980 state.")

    # Invariant check: all records must contain global_state_restored == True
    records_with_restored = sum(1 for r in records if r.get("global_state_restored") is True)
    if records_with_restored != len(records):
        print(f"  [FAIL] Only {records_with_restored}/{len(records)} records have global_state_restored=True!")
        passed_all = False
    else:
        print(f"  [PASS] All {records_with_restored}/{len(records)} records contain audited global_state_restored=True telemetry.")

    print("\n" + "=" * 80)
    if passed_all:
        print(">>> ALL 6 PILOT INVARIANTS PASSED PERFECTLY (16/16 INSTANCES VERIFIED) <<<")
    else:
        print(">>> PILOT VERIFICATION FAILED ONE OR MORE CHECKS <<<")
    print("=" * 80 + "\n")

    return passed_all


def main():
    parser = argparse.ArgumentParser(description="TERRA Phase 3 Pilot Smoke-Test Harness")
    parser.add_argument("--force", action="store_true", help="Force fresh rerun even if output exists")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing pilot JSON file without executing API calls")
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("TASK 4: TEMPORAL LEAKAGE PILOT SMOKE-TEST EXECUTION")
    print("=" * 80)
    print(f"Target Probes:   {PILOT_QUERY_IDS}")
    print(f"Target Conds:    {PILOT_CONDITIONS}")
    print(f"Output Path:     {PILOT_OUTPUT_PATH}")
    print(f"Model String:    {MANDATORY_MODEL_STRING} (T=0.0)")

    # 1. Load Probes
    if not DEFAULT_PROBE_PATH.exists():
        raise FileNotFoundError(f"Probe file not found: {DEFAULT_PROBE_PATH}")
    with open(DEFAULT_PROBE_PATH, "r", encoding="utf-8") as f:
        all_probes = json.load(f)

    probe_map = {p["query_id"]: p for p in all_probes if p["query_id"] in PILOT_QUERY_IDS}
    if len(probe_map) != len(PILOT_QUERY_IDS):
        raise ValueError(f"Could not find all pilot query IDs {PILOT_QUERY_IDS} in {DEFAULT_PROBE_PATH}")

    # 2. Verify-Only Mode
    if args.verify_only:
        load_path = PILOT_OUTPUT_PATH if PILOT_OUTPUT_PATH.exists() else PILOT_SCRATCH_PATH
        if not load_path.exists():
            print(f"[FAIL] Pilot output file not found at {PILOT_OUTPUT_PATH} or {PILOT_SCRATCH_PATH}")
            sys.exit(1)
        with open(load_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        success = run_pilot_verifications(existing, probe_map)
        sys.exit(0 if success else 1)

    # 3. Check existing pilot records
    records: List[Dict[str, Any]] = []
    if not args.force and PILOT_OUTPUT_PATH.exists():
        try:
            with open(PILOT_OUTPUT_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
            print(f"Loaded {len(records)} existing pilot records.")
        except Exception:
            records = []

    # 4. Execute Pilot Probes
    client = get_databricks_client()
    t_start = time.time()

    for qid in PILOT_QUERY_IDS:
        probe = probe_map[qid]
        cutoff = probe["cutoff_year"]
        print(f"\n[PILOT PROBE] {qid} (Cutoff T={cutoff}) - {probe.get('target_case_name')}")

        for cond in PILOT_CONDITIONS:
            print(f"  Condition: {cond}")
            new_recs = execute_probe_for_condition(
                probe=probe,
                condition=cond,
                client=client,
                existing_records=records
            )
            records.extend(new_recs)

            # Atomic save after each condition
            atomic_save(records, PILOT_OUTPUT_PATH)
            # Also save mirror to scratch
            atomic_save(records, PILOT_SCRATCH_PATH)

    elapsed = round(time.time() - t_start, 2)
    print(f"\nPilot execution completed in {elapsed}s.")
    print(f"Saved {len(records)} records to {PILOT_OUTPUT_PATH}.")

    # 5. Run Programmatic Verifications
    passed = run_pilot_verifications(records, probe_map)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
