#!/usr/bin/env python3
"""
scripts/test_run_diagnostic_harness.py
======================================
Comprehensive synthetic unit and lifecycle test suite for the hardened execution harness
(scripts/run_diagnostic_harness.py).

Review Alignment (Codex-0025, Claude-0084):
1. Complete Content-Level Report Validation:
   - Validates complete 350-query ledger: cardinality 350, unique query IDs, cohort breakdown
     (100 A, 100 B, 75 C, 75 D), non-empty nearest_node_id, finite numerical distances.
   - Validates complete 40-query legacy ledger: cardinality 40, unique query IDs, cohort breakdown
     (20 sample_in_20, 20 sample_out_20), non-empty nearest_node_id, finite numerical distances.
   - Validates exactly the 8 production threshold keys (0.90 to 1.40) with integer fp/tp/fn counts.
   - Validates concordance classification, finite AUROCs, empty error list, and 10 completed stages.
2. Preserved Snapshot Copy Parity:
   - Verifies all 4 additional preserved copies in snapshot_dir against mandatory manifest entries
     before launch (pre-flight) and after execution (finally:).
   - Negative controls for pre-flight and post-flight mutated preserved asset copies.
3. Offline Condition Whitelist & Report Cross-Check:
   - Rejects unapproved free-text offline conditions pre-flight without taking lock.
   - Cross-checks report declared condition against harness parameter.
4. Isolated Test Configurations & Specific Failure Asserts:
   - All fixtures completely isolated (build_fixture_config rebuilds all paths per fixture).
   - Every negative test asserts specific failure reason strings and child return codes.
   - Separate tests for snapshot manifest deletion vs mutation.
   - Real mocked I/O exception tests using unittest.mock.patch.
5. Metadata Test Configuration Recording:
   - Verifies harness_config_supplied is recorded in metadata.
"""

import os
import sys
import json
import math
import time
import uuid
import shutil
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from typing import Optional, Dict, Any, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.run_diagnostic_harness import (
    action_execute_diagnostic,
    file_sha256,
    dir_manifest,
    acquire_single_run_lock,
    verify_runtime_pins,
    verify_snapshot_parity,
    validate_child_report,
    resolve_benchmark_identifier,
    validate_benchmark_schemas,
    PINNED_INTERPRETER_PATH,
    PINNED_INTERPRETER_SHA256,
    PINNED_DIAGNOSTIC_PATH,
    PINNED_DIAGNOSTIC_SHA256,
    PINNED_LIBRARY_VERSIONS,
    APPROVED_OFFLINE_CONDITIONS,
    EXPECTED_GRID_THRESHOLD_KEYS,
    REQUIRED_STAGES,
    APPROVED_ONNX_CACHE_MANIFEST,
    SNAPSHOT_TARGET_DIR,
    ORIGINAL_STORE_DIR,
    EXPECTED_B350_SHA256,
    EXPECTED_B175_SHA256
)


def make_synthetic_fixture(tmp_dir: Path) -> dict:
    """Create a fully isolated synthetic workspace fixture with mock assets."""
    ws = tmp_dir / "workspace"
    ws.mkdir()
    store = ws / "dataset_20k_cap" / "vector_db_20k"
    store.mkdir(parents=True)
    snap = ws / "pre_run_snapshot_20k"
    snap.mkdir(parents=True)
    snap_store = snap / "vector_db_20k"
    snap_store.mkdir(parents=True)
    runs_dir = ws / "addendum_01" / "runs"
    runs_dir.mkdir(parents=True)
    onnx_dir = ws / "onnx_cache"
    onnx_dir.mkdir()
    scratch_dir = ws / "scratch"
    scratch_dir.mkdir(parents=True)
    scripts_dir = ws / "scripts"
    scripts_dir.mkdir(parents=True)

    # 11 synthetic vector store files
    store_files = [
        "chroma.sqlite3",
        "282cb51e-ff2d-499b-8b6a-bd24123bb584/data_level0.bin",
        "282cb51e-ff2d-499b-8b6a-bd24123bb584/header.bin",
        "282cb51e-ff2d-499b-8b6a-bd24123bb584/index_metadata.pickle",
        "282cb51e-ff2d-499b-8b6a-bd24123bb584/length.bin",
        "282cb51e-ff2d-499b-8b6a-bd24123bb584/link_lists.bin",
        "59ddb27e-f5cf-4fe4-a803-a8686d117b66/data_level0.bin",
        "59ddb27e-f5cf-4fe4-a803-a8686d117b66/header.bin",
        "59ddb27e-f5cf-4fe4-a803-a8686d117b66/index_metadata.pickle",
        "59ddb27e-f5cf-4fe4-a803-a8686d117b66/length.bin",
        "59ddb27e-f5cf-4fe4-a803-a8686d117b66/link_lists.bin"
    ]
    vector_store_manifest = {}
    for sf in store_files:
        p = store / sf
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"synthetic_store_bytes_{sf}".encode("utf-8")
        p.write_bytes(content)
        sha = hashlib.sha256(content).hexdigest()
        vector_store_manifest[sf] = {"size": len(content), "sha256": sha}

        # Also populate preserved snapshot copy directory
        sp = snap_store / sf
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_bytes(content)

    # Benchmark 350 JSON
    b350_items = []
    for i in range(1, 351):
        if i <= 100:
            cat = "A_Factual"
        elif i <= 200:
            cat = "B_Evolutionary"
        elif i <= 275:
            cat = "C_OutOfContext"
        else:
            cat = "D_Adversarial"
        b350_items.append({
            "query_id": f"bench350_q{i:03d}",
            "category": cat,
            "query": f"synthetic benchmark 350 query text {i}"
        })
    b350_bytes = json.dumps(b350_items, indent=2).encode("utf-8")
    (ws / "terra_350_benchmark.json").write_bytes(b350_bytes)

    # Benchmark 175 JSON (mirrors real schema: 'id', 'category', 'query', 'reference', 'set')
    b175_items = []
    for i in range(1, 11):
        b175_items.append({
            "id": f"S1_A{i:02d}",
            "set": 1,
            "category": "A_Factual",
            "query": f"synthetic legacy in query text A {i}",
            "reference": f"synthetic reference A {i}"
        })
    for i in range(1, 11):
        b175_items.append({
            "id": f"S1_B{i:02d}",
            "set": 1,
            "category": "B_Evolutionary",
            "query": f"synthetic legacy in query text B {i}",
            "reference": f"synthetic reference B {i}"
        })
    for i in range(1, 21):
        b175_items.append({
            "id": f"S1_C{i:02d}",
            "set": 1,
            "category": "C_OutOfContext",
            "query": f"synthetic legacy out query text C {i}",
            "reference": f"synthetic reference C {i}"
        })
    b175_bytes = json.dumps(b175_items, indent=2).encode("utf-8")
    (ws / "terra_175_benchmark.json").write_bytes(b175_bytes)

    # Summary JSON with gate_calibration grid
    summary_grid = {}
    for tau_str in ["0.90", "1.00", "1.10", "1.20", "1.25", "1.30", "1.35", "1.40"]:
        summary_grid[tau_str] = {
            "tau": float(tau_str),
            "fp": 0,
            "fpr": 0.0,
            "tp": 75,
            "tpr": 100.0,
            "fn": 0,
            "fnr": 0.0,
            "n_in": 200,
            "n_ood": 75
        }
    summary_obj = {
        "gate_calibration": {
            "auroc": 0.9901333333333333,
            "grid": summary_grid
        }
    }
    summary_bytes = json.dumps(summary_obj, indent=2).encode("utf-8")
    (scratch_dir / "budget_and_gate_summary.json").write_bytes(summary_bytes)

    # Historical script
    hist_script_bytes = b"# synthetic historical script content\n"
    (scripts_dir / "compute_budget_and_gate_metrics.py").write_bytes(hist_script_bytes)

    # Additional assets manifest and copy to snapshot
    additional_manifest = {}
    add_assets_config = {}
    asset_defs = [
        ("terra_350_benchmark.json", ws / "terra_350_benchmark.json", b350_bytes),
        ("terra_175_benchmark.json", ws / "terra_175_benchmark.json", b175_bytes),
        ("budget_and_gate_summary.json", scratch_dir / "budget_and_gate_summary.json", summary_bytes),
        ("compute_budget_and_gate_metrics.py", scripts_dir / "compute_budget_and_gate_metrics.py", hist_script_bytes)
    ]
    for aname, ap, abytes in asset_defs:
        sha = hashlib.sha256(abytes).hexdigest()
        additional_manifest[aname] = {"size": len(abytes), "sha256": sha}
        add_assets_config[aname] = {"path": ap, "expected_sha256": sha}
        # Copy additional assets to snapshot directory
        (snap / aname).write_bytes(abytes)

    # Snapshot manifest JSON
    snapshot_manifest_payload = {
        "timestamp_utc": "2026-10-08 00:00:00 UTC",
        "original_source_store": str(store),
        "snapshot_directory": str(snap),
        "vector_store_manifest": vector_store_manifest,
        "additional_assets": additional_manifest
    }
    (snap / "snapshot_manifest.json").write_text(json.dumps(snapshot_manifest_payload, indent=2), encoding="utf-8")

    # 6 ONNX cache assets
    onnx_manifest = {}
    onnx_files = ["config.json", "model.onnx", "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt"]
    for of in onnx_files:
        op = onnx_dir / of
        ocontent = f"synthetic_onnx_{of}".encode("utf-8")
        op.write_bytes(ocontent)
        onnx_manifest[of] = {"size": len(ocontent), "sha256": hashlib.sha256(ocontent).hexdigest()}

    return {
        "workspace_root": ws,
        "store_dir": store,
        "snapshot_dir": snap,
        "runs_base_dir": runs_dir,
        "onnx_cache_dir": onnx_dir,
        "onnx_manifest": onnx_manifest,
        "additional_assets": add_assets_config,
        "lock_path": runs_dir / ".single_run_lock"
    }


def build_fixture_config(fixture: dict, child_script: Path, **overrides) -> dict:
    """Build a completely isolated, self-contained configuration dictionary for a given fixture."""
    py_exe = Path(sys.executable).resolve()
    cfg = {
        "workspace_root": fixture["workspace_root"],
        "store_dir": fixture["store_dir"],
        "snapshot_dir": fixture["snapshot_dir"],
        "runs_base_dir": fixture["runs_base_dir"],
        "diagnostic_script": child_script,
        "diagnostic_sha256": file_sha256(child_script),
        "python_executable": py_exe,
        "python_sha256": file_sha256(py_exe),
        "onnx_cache_dir": fixture["onnx_cache_dir"],
        "onnx_manifest": fixture["onnx_manifest"],
        "expected_lib_versions": PINNED_LIBRARY_VERSIONS,
        "lock_path": fixture["lock_path"],
        "additional_assets": fixture["additional_assets"],
        "approved_offline_conditions": {"TEST_OFFLINE_FIREWALL"}
    }
    cfg.update(overrides)
    return cfg


def make_production_shaped_report_dict(
    run_id: str,
    script_sha: str,
    is_mock: bool = False,
    status: str = "SUCCESS",
    omit_mock_field: bool = False,
    omit_top_key: Optional[str] = None
) -> dict:
    """Generate a production-shaped diagnostic report dictionary with all 350 and 40 queries and 8-grid thresholds."""
    ledger_350 = []
    for i in range(1, 351):
        if i <= 100:
            cat = "A_Factual"
        elif i <= 200:
            cat = "B_Evolutionary"
        elif i <= 275:
            cat = "C_OutOfContext"
        else:
            cat = "D_Adversarial"
        ledger_350.append({
            "query_id": f"bench350_q{i:03d}",
            "category": cat,
            "distance_raw_squared": 0.5,
            "distance_euclidean_sqrt": 0.7071067811865476,
            "nearest_node_id": f"node_bench350_{i:03d}",
            "anomaly_flag": "none"
        })

    ledger_40 = []
    for i in range(1, 11):
        qtext = f"synthetic legacy in query text A {i}"
        ledger_40.append({
            "cohort": "sample_in_20",
            "query_id": f"S1_A{i:02d}",
            "source_field": "id",
            "query_sha256": hashlib.sha256(qtext.encode("utf-8")).hexdigest(),
            "distance_raw_squared": 0.5,
            "distance_euclidean_sqrt": 0.7071067811865476,
            "nearest_node_id": f"node_leg_in_A_{i:02d}",
            "anomaly_flag": "none"
        })
    for i in range(1, 11):
        qtext = f"synthetic legacy in query text B {i}"
        ledger_40.append({
            "cohort": "sample_in_20",
            "query_id": f"S1_B{i:02d}",
            "source_field": "id",
            "query_sha256": hashlib.sha256(qtext.encode("utf-8")).hexdigest(),
            "distance_raw_squared": 0.5,
            "distance_euclidean_sqrt": 0.7071067811865476,
            "nearest_node_id": f"node_leg_in_B_{i:02d}",
            "anomaly_flag": "none"
        })
    for i in range(1, 21):
        qtext = f"synthetic legacy out query text C {i}"
        ledger_40.append({
            "cohort": "sample_out_20",
            "query_id": f"S1_C{i:02d}",
            "source_field": "id",
            "query_sha256": hashlib.sha256(qtext.encode("utf-8")).hexdigest(),
            "distance_raw_squared": 1.5,
            "distance_euclidean_sqrt": 1.224744871391589,
            "nearest_node_id": f"node_leg_out_C_{i:02d}",
            "anomaly_flag": "none"
        })

    grid_350 = {}
    for tau_str in ["0.90", "1.00", "1.10", "1.20", "1.25", "1.30", "1.35", "1.40"]:
        grid_350[tau_str] = {
            "tau_raw_squared": float(tau_str),
            "n_in": 200,
            "fp_count": 0,
            "fpr_pct": 0.0,
            "n_ood": 75,
            "tp_count": 75,
            "tpr_pct": 100.0,
            "fn_count": 0,
            "fnr_pct": 0.0
        }

    rep = {
        "status": status,
        "run_id": run_id,
        "timestamp_utc": "2026-10-08 00:00:00 UTC",
        "script": {
            "path": "/fake/scripts/audit_i1a_contemporary_gate_calibration.py",
            "sha256": script_sha
        },
        "enforced_offline_condition": "TEST_OFFLINE_FIREWALL",
        "offline_execution_environment": {
            "enforced_offline_condition": "TEST_OFFLINE_FIREWALL",
            "python_network_interception_active": True,
            "chroma_telemetry_disabled": True,
            "transformers_offline_set": True,
            "negative_control_passed": True,
            "network_guards_uninstalled": True,
            "layering_declaration": "Layer 1 external, Layer 2 in-process"
        },
        "provenance_disclaimer": "Diagnostic provenance notice",
        "stages_completed": list(REQUIRED_STAGES),
        "errors": [] if status == "SUCCESS" else [{"error_type": "SimulatedError"}],
        "integrity_checks": {
            "source_db_invariant": True,
            "benchmark_350_invariant": True,
            "benchmark_175_invariant": True,
            "saved_summary_invariant": True,
            "onnx_cache_invariant": True,
            "all_integrity_passed": (status == "SUCCESS")
        },
        "metadata": {
            "title": "Contemporary Vector Distance Diagnostic on Preserved Local Index",
            "date": "2026-10-08",
            "embedding_function_delegate": {
                "class": "ONNXMiniLM_L6_V2",
                "module": "chromadb.utils.embedding_functions",
                "qualname": "ONNXMiniLM_L6_V2",
                "name": "default",
                "is_default_embedding_function": True,
                "is_concrete_onnx_minilm": True,
                "installed_onnx_class": "ONNXMiniLM_L6_V2",
                "installed_onnx_module": "chromadb.utils.embedding_functions",
                "delegates_to_onnx_minilm": True,
                "verified_cache_dir": "/fake/cache"
            }
        },
        "concordance": {
            "diagnostic_auroc": 0.9901333333333333,
            "saved_auroc": 0.9901333333333333,
            "auroc_difference": 0.0,
            "grid_mismatch_count": 0,
            "grid_mismatches": [],
            "concordance_classification": "EXACT_CONCORDANCE"
        },
        "distribution_summary_benchmark_350": {
            "in_domain_200_raw_squared": {"count": 200, "mean": 0.5},
            "in_domain_200_euclidean_sqrt": {"count": 200, "mean": 0.707},
            "ood_75_raw_squared": {"count": 75, "mean": 1.5},
            "ood_75_euclidean_sqrt": {"count": 75, "mean": 1.22},
            "adv_75_raw_squared": {"count": 75, "mean": 1.6},
            "adv_75_euclidean_sqrt": {"count": 75, "mean": 1.26}
        },
        "calibration_grid_benchmark_350": grid_350,
        "legacy_sample20_diagnostic": {
            "sample_in_20_raw_squared": {"count": 20, "mean": 0.5},
            "sample_in_20_euclidean_sqrt": {"count": 20, "mean": 0.707},
            "sample_out_20_raw_squared": {"count": 20, "mean": 1.5},
            "sample_out_20_euclidean_sqrt": {"count": 20, "mean": 1.22}
        },
        "verification_manifests": {},
        "query_ledger_350": ledger_350,
        "legacy_sample20_query_ledger": ledger_40
    }
    if not omit_mock_field:
        rep["metadata"]["embedding_function_delegate"]["is_mock_override"] = is_mock
    if omit_top_key and omit_top_key in rep:
        del rep[omit_top_key]
    return rep


def write_fake_child_script(script_path: Path, behavior: str = "success"):
    """Generate a fake diagnostic child script simulating various runtime outcomes."""
    code = f'''
import sys
import os
import time
import json
import uuid
import hashlib
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--workspace-root", type=str)
parser.add_argument("--onnx-cache-dir", type=str)
parser.add_argument("--enforced-offline-condition", type=str)
args = parser.parse_args()

behavior = "{behavior}"

if behavior == "nonzero_exit":
    print("[FAKE CHILD] Simulated non-zero exit.", file=sys.stderr)
    sys.exit(2)

if behavior == "sleep_forever":
    print("[FAKE CHILD] Sleeping forever...")
    time.sleep(30)
    sys.exit(0)

child_run_id = f"{{int(time.time())}}_{{os.getpid()}}_{{uuid.uuid4().hex[:8]}}"
runs_dir = Path(args.workspace_root) / "addendum_01" / "runs"
child_run_dir = runs_dir / f"run_{{child_run_id}}"
child_run_dir.mkdir(parents=True, exist_ok=True)

if behavior == "mutate_store":
    store_file = Path(args.workspace_root) / "dataset_20k_cap" / "vector_db_20k" / "chroma.sqlite3"
    with open(store_file, "ab") as f:
        f.write(b"MUTATION_BYTES")

if behavior == "delete_manifest":
    man_file = Path(args.workspace_root) / "pre_run_snapshot_20k" / "snapshot_manifest.json"
    if man_file.exists():
        man_file.unlink()

if behavior == "mutate_manifest":
    man_file = Path(args.workspace_root) / "pre_run_snapshot_20k" / "snapshot_manifest.json"
    if man_file.exists():
        with open(man_file, "ab") as f:
            f.write(b"MUTATE_MANIFEST")

if behavior == "mutate_snapshot_asset_copy":
    asset_file = Path(args.workspace_root) / "pre_run_snapshot_20k" / "terra_350_benchmark.json"
    if asset_file.exists():
        with open(asset_file, "ab") as f:
            f.write(b"MUTATED_ASSET_COPY")

if behavior == "extra_store_file":
    extra_file = Path(args.workspace_root) / "dataset_20k_cap" / "vector_db_20k" / "extra_unrecorded.bin"
    extra_file.write_bytes(b"EXTRA_DATA")

report_file = child_run_dir / f"contemporary_distance_diagnostic_{{child_run_id}}.json"

if behavior == "zero_reports":
    sys.exit(0)

if behavior == "multiple_reports":
    rep1 = {{"status": "SUCCESS", "run_id": child_run_id}}
    rep2 = {{"status": "SUCCESS", "run_id": f"alt_{{child_run_id}}"}}
    report_file.write_text(json.dumps(rep1), encoding="utf-8")
    (child_run_dir / f"contemporary_distance_diagnostic_extra_{{child_run_id}}.json").write_text(json.dumps(rep2), encoding="utf-8")
    sys.exit(0)

# Build complete 350-query and 40-query ledgers
ledger_350 = []
for i in range(1, 351):
    if i <= 100:
        cat = "A_Factual"
    elif i <= 200:
        cat = "B_Evolutionary"
    elif i <= 275:
        cat = "C_OutOfContext"
    else:
        cat = "D_Adversarial"
    ledger_350.append({{
        "query_id": f"bench350_q{{i:03d}}",
        "category": cat,
        "distance_raw_squared": 0.5,
        "distance_euclidean_sqrt": 0.7071067811865476,
        "nearest_node_id": f"node_bench350_{{i:03d}}",
        "anomaly_flag": "none"
    }})

b175_file = Path(args.workspace_root) / "terra_175_benchmark.json"
with open(b175_file, "r", encoding="utf-8") as f_b175:
    b175_raw = json.load(f_b175)
sample_in_recs = [q for q in b175_raw if q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
sample_out_recs = [q for q in b175_raw if q.get("category") == "C_OutOfContext"][:20]

ledger_40 = []
for q in sample_in_recs:
    qid = q.get("query_id") or q.get("id")
    src = "query_id" if "query_id" in q else "id"
    q_sha = hashlib.sha256(q["query"].encode("utf-8")).hexdigest()
    ledger_40.append({{
        "cohort": "sample_in_20",
        "query_id": qid,
        "source_field": src,
        "query_sha256": q_sha,
        "distance_raw_squared": 0.5,
        "distance_euclidean_sqrt": 0.7071067811865476,
        "nearest_node_id": f"node_leg_{{qid}}",
        "anomaly_flag": "none"
    }})
for q in sample_out_recs:
    qid = q.get("query_id") or q.get("id")
    src = "query_id" if "query_id" in q else "id"
    q_sha = hashlib.sha256(q["query"].encode("utf-8")).hexdigest()
    ledger_40.append({{
        "cohort": "sample_out_20",
        "query_id": qid,
        "source_field": src,
        "query_sha256": q_sha,
        "distance_raw_squared": 1.5,
        "distance_euclidean_sqrt": 1.224744871391589,
        "nearest_node_id": f"node_leg_{{qid}}",
        "anomaly_flag": "none"
    }})

grid_350 = {{}}
for tau_str in ["0.90", "1.00", "1.10", "1.20", "1.25", "1.30", "1.35", "1.40"]:
    grid_350[tau_str] = {{
        "tau_raw_squared": float(tau_str),
        "n_in": 200,
        "fp_count": 0,
        "fpr_pct": 0.0,
        "n_ood": 75,
        "tp_count": 75,
        "tpr_pct": 100.0,
        "fn_count": 0,
        "fnr_pct": 0.0
    }}

required_stages = [
    "stage_1_network_negative_control",
    "stage_2_path_isolation_verified",
    "stage_3_preflight_assets_verified",
    "stage_4_snapshot_copied_and_verified",
    "stage_5_pre_schema_extracted",
    "stage_6_cohorts_validated",
    "stage_7_benchmark_350_queried",
    "stage_8_benchmark_175_queried",
    "stage_9_concordance_evaluated",
    "stage_10_metadata_finalized"
]

rep = {{
    "status": "SUCCESS",
    "run_id": child_run_id,
    "timestamp_utc": "2026-10-08 00:00:00 UTC",
    "script": {{
        "path": str(Path(__file__).resolve()),
        "sha256": "PLACEHOLDER_SCRIPT_SHA"
    }},
    "enforced_offline_condition": args.enforced_offline_condition,
    "offline_execution_environment": {{
        "enforced_offline_condition": args.enforced_offline_condition,
        "python_network_interception_active": True,
        "chroma_telemetry_disabled": True,
        "transformers_offline_set": True,
        "negative_control_passed": True,
        "network_guards_uninstalled": True,
        "layering_declaration": "Layer 1 external, Layer 2 in-process"
    }},
    "provenance_disclaimer": "Diagnostic provenance notice",
    "stages_completed": required_stages,
    "errors": [],
    "integrity_checks": {{
        "source_db_invariant": True,
        "benchmark_350_invariant": True,
        "benchmark_175_invariant": True,
        "saved_summary_invariant": True,
        "onnx_cache_invariant": True,
        "all_integrity_passed": True
    }},
    "metadata": {{
        "title": "Contemporary Vector Distance Diagnostic on Preserved Local Index",
        "date": "2026-10-08",
        "embedding_function_delegate": {{
            "class": "ONNXMiniLM_L6_V2",
            "module": "chromadb.utils.embedding_functions",
            "qualname": "ONNXMiniLM_L6_V2",
            "name": "default",
            "is_default_embedding_function": True,
            "is_concrete_onnx_minilm": True,
            "is_mock_override": False,
            "installed_onnx_class": "ONNXMiniLM_L6_V2",
            "installed_onnx_module": "chromadb.utils.embedding_functions",
            "delegates_to_onnx_minilm": True,
            "verified_cache_dir": str(args.onnx_cache_dir)
        }}
    }},
    "concordance": {{
        "diagnostic_auroc": 0.9901333333333333,
        "saved_auroc": 0.9901333333333333,
        "auroc_difference": 0.0,
        "grid_mismatch_count": 0,
        "grid_mismatches": [],
        "concordance_classification": "EXACT_CONCORDANCE"
    }},
    "distribution_summary_benchmark_350": {{
        "in_domain_200_raw_squared": {{"count": 200, "mean": 0.5}},
        "in_domain_200_euclidean_sqrt": {{"count": 200, "mean": 0.707}},
        "ood_75_raw_squared": {{"count": 75, "mean": 1.5}},
        "ood_75_euclidean_sqrt": {{"count": 75, "mean": 1.22}},
        "adv_75_raw_squared": {{"count": 75, "mean": 1.6}},
        "adv_75_euclidean_sqrt": {{"count": 75, "mean": 1.26}}
    }},
    "calibration_grid_benchmark_350": grid_350,
    "legacy_sample20_diagnostic": {{
        "sample_in_20_raw_squared": {{"count": 20, "mean": 0.5}},
        "sample_in_20_euclidean_sqrt": {{"count": 20, "mean": 0.707}},
        "sample_out_20_raw_squared": {{"count": 20, "mean": 1.5}},
        "sample_out_20_euclidean_sqrt": {{"count": 20, "mean": 1.22}}
    }},
    "verification_manifests": {{}},
    "query_ledger_350": ledger_350,
    "legacy_sample20_query_ledger": ledger_40
}}

if behavior == "nested_mock_override":
    rep["metadata"]["embedding_function_delegate"]["is_mock_override"] = True

if behavior == "missing_nested_mock":
    del rep["metadata"]["embedding_function_delegate"]["is_mock_override"]

if behavior == "script_hash_mismatch":
    rep["script"]["sha256"] = "0" * 64

if behavior == "run_id_mismatch":
    rep["run_id"] = f"mismatched_{{child_run_id}}"

if behavior == "missing_top_key":
    del rep["concordance"]

if behavior == "failed_status":
    rep["status"] = "FAILED"
    rep["integrity_checks"]["all_integrity_passed"] = False

if behavior == "populated_errors":
    rep["errors"] = [{{"error_type": "ChildInternalError", "error_message": "Simulated error recorded"}}]

if behavior == "missing_stage":
    rep["stages_completed"].remove("stage_10_metadata_finalized")

if behavior == "offline_condition_mismatch":
    rep["enforced_offline_condition"] = "MISMATCHED_CONDITION"
    rep["offline_execution_environment"]["enforced_offline_condition"] = "MISMATCHED_CONDITION"

if behavior == "truncated_ledger_350":
    rep["query_ledger_350"] = rep["query_ledger_350"][:349]

if behavior == "duplicate_qid_ledger_350":
    rep["query_ledger_350"][1]["query_id"] = rep["query_ledger_350"][0]["query_id"]

if behavior == "nonfinite_distance":
    rep["query_ledger_350"][0]["distance_raw_squared"] = float("nan")

if behavior == "truncated_legacy_ledger":
    rep["legacy_sample20_query_ledger"] = rep["legacy_sample20_query_ledger"][:39]

if behavior == "legacy_missing_source_field":
    del rep["legacy_sample20_query_ledger"][0]["source_field"]

if behavior == "legacy_sha_mismatch":
    rep["legacy_sample20_query_ledger"][0]["query_sha256"] = "0" * 64

if behavior == "legacy_id_mismatch":
    rep["legacy_sample20_query_ledger"][0]["query_id"] = "mismatched_leg_id"

if behavior == "wrong_grid_thresholds":
    rep["calibration_grid_benchmark_350"] = {{"0.50": {{"fp": 0, "tp": 75, "fn": 0}}}}

if rep["script"]["sha256"] == "PLACEHOLDER_SCRIPT_SHA":
    import hashlib
    with open(__file__, "rb") as f_self:
        rep["script"]["sha256"] = hashlib.sha256(f_self.read()).hexdigest()

report_file.write_text(json.dumps(rep, indent=2), encoding="utf-8")
print("[FAKE CHILD] Serialized report to:", report_file)
sys.exit(0)
'''
    script_path.write_text(code, encoding="utf-8")


class TestRunDiagnosticHarnessSynthetic(unittest.TestCase):
    """Synthetic unit and lifecycle tests for the hardened execution harness."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)
        self.fixture = make_synthetic_fixture(self.tmp_path)
        self.child_script = self.fixture["workspace_root"] / "fake_child.py"
        write_fake_child_script(self.child_script, behavior="success")
        self.base_cfg = build_fixture_config(self.fixture, self.child_script)

    def tearDown(self):
        self.temp_dir.cleanup()

    # --------------------------------------------------------------------------
    # Group 1: Lock Timing & Pre-Flight Gate Failures (Lock Remains Unused)
    # --------------------------------------------------------------------------
    def test_01_rejects_empty_offline_condition_leaves_lock_unused(self):
        """Pre-flight gate: rejects empty condition without creating lock."""
        code_empty = action_execute_diagnostic("", harness_config=self.base_cfg)
        self.assertEqual(code_empty, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_02_rejects_unconfirmed_condition_literal_leaves_lock_unused(self):
        """Pre-flight gate: rejects unconfirmed environment literal without creating lock."""
        code_unconf = action_execute_diagnostic(
            "UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT",
            harness_config=self.base_cfg
        )
        self.assertEqual(code_unconf, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_03_rejects_unapproved_free_text_condition_leaves_lock_unused(self):
        """Pre-flight gate: rejects unapproved free text like 'ok' without creating lock."""
        code_free = action_execute_diagnostic("ok", harness_config=self.base_cfg)
        self.assertEqual(code_free, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_04_pinned_interpreter_hash_mismatch_aborts_leaves_lock_unused(self):
        """Pre-flight gate: bad interpreter SHA-256 aborts without creating lock."""
        bad_cfg = dict(self.base_cfg)
        bad_cfg["python_sha256"] = "0" * 64

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=bad_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_05_pinned_diagnostic_script_hash_mismatch_aborts_leaves_lock_unused(self):
        """Pre-flight gate: bad diagnostic script SHA-256 aborts without creating lock."""
        bad_cfg = dict(self.base_cfg)
        bad_cfg["diagnostic_sha256"] = "f" * 64

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=bad_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_06_missing_store_file_aborts_leaves_lock_unused(self):
        """Pre-flight parity gate: missing store file aborts without creating lock."""
        sqlite_file = self.fixture["store_dir"] / "chroma.sqlite3"
        sqlite_file.unlink()

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_07_mutated_store_file_aborts_leaves_lock_unused(self):
        """Pre-flight parity gate: mutated store file aborts without creating lock."""
        sqlite_file = self.fixture["store_dir"] / "chroma.sqlite3"
        sqlite_file.write_bytes(b"MUTATED_BEFORE_RUN")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_08_extra_store_file_aborts_leaves_lock_unused(self):
        """Pre-flight parity gate: unrecorded extraneous store file aborts without creating lock."""
        extra_file = self.fixture["store_dir"] / "extra_unrecorded.bin"
        extra_file.write_bytes(b"EXTRANEOUS_STORE_FILE")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_09_mutated_preserved_snapshot_asset_copy_aborts_leaves_lock_unused(self):
        """Pre-flight parity gate: mutated preserved copy of benchmark in snapshot_dir aborts without creating lock."""
        snap_copy = self.fixture["snapshot_dir"] / "terra_350_benchmark.json"
        snap_copy.write_bytes(b"MUTATED_PRESERVED_COPY")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())

    def test_09b_pre_launch_b175_missing_identifier_leaves_lock_unused(self):
        """Pre-launch gate: Benchmark 175 missing identifier aborts pre-flight without creating single-run lock."""
        ws_b175 = self.fixture["workspace_root"] / "terra_175_benchmark.json"
        snap_b175 = self.fixture["snapshot_dir"] / "terra_175_benchmark.json"
        with open(ws_b175, "r", encoding="utf-8") as f:
            data = json.load(f)
        del data[0]["id"]
        if "query_id" in data[0]:
            del data[0]["query_id"]
        mutated_bytes = json.dumps(data, indent=2).encode("utf-8")
        ws_b175.write_bytes(mutated_bytes)
        snap_b175.write_bytes(mutated_bytes)
        new_sha = file_sha256(ws_b175)
        self.base_cfg["additional_assets"]["terra_175_benchmark.json"]["expected_sha256"] = new_sha
        manifest_path = self.fixture["snapshot_dir"] / "snapshot_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        man_data["additional_assets"]["terra_175_benchmark.json"]["sha256"] = new_sha
        man_data["additional_assets"]["terra_175_benchmark.json"]["size"] = len(mutated_bytes)
        manifest_path.write_text(json.dumps(man_data, indent=2), encoding="utf-8")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())
        self.assertEqual(len(list(self.fixture["runs_base_dir"].glob("harness_run_*"))), 0)

    def test_09c_pre_launch_b175_duplicate_identifier_leaves_lock_unused(self):
        """Pre-launch gate: Benchmark 175 duplicate identifiers abort pre-flight without creating single-run lock."""
        ws_b175 = self.fixture["workspace_root"] / "terra_175_benchmark.json"
        snap_b175 = self.fixture["snapshot_dir"] / "terra_175_benchmark.json"
        with open(ws_b175, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[1]["id"] = data[0]["id"]
        mutated_bytes = json.dumps(data, indent=2).encode("utf-8")
        ws_b175.write_bytes(mutated_bytes)
        snap_b175.write_bytes(mutated_bytes)
        new_sha = file_sha256(ws_b175)
        self.base_cfg["additional_assets"]["terra_175_benchmark.json"]["expected_sha256"] = new_sha
        manifest_path = self.fixture["snapshot_dir"] / "snapshot_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        man_data["additional_assets"]["terra_175_benchmark.json"]["sha256"] = new_sha
        man_data["additional_assets"]["terra_175_benchmark.json"]["size"] = len(mutated_bytes)
        manifest_path.write_text(json.dumps(man_data, indent=2), encoding="utf-8")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())
        self.assertEqual(len(list(self.fixture["runs_base_dir"].glob("harness_run_*"))), 0)

    def test_09d_pre_launch_b175_insufficient_cohort_count_leaves_lock_unused(self):
        """Pre-launch gate: Benchmark 175 insufficient cohort count aborts pre-flight without creating lock."""
        ws_b175 = self.fixture["workspace_root"] / "terra_175_benchmark.json"
        snap_b175 = self.fixture["snapshot_dir"] / "terra_175_benchmark.json"
        with open(ws_b175, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = data[1:]
        mutated_bytes = json.dumps(data, indent=2).encode("utf-8")
        ws_b175.write_bytes(mutated_bytes)
        snap_b175.write_bytes(mutated_bytes)
        new_sha = file_sha256(ws_b175)
        self.base_cfg["additional_assets"]["terra_175_benchmark.json"]["expected_sha256"] = new_sha
        manifest_path = self.fixture["snapshot_dir"] / "snapshot_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        man_data["additional_assets"]["terra_175_benchmark.json"]["sha256"] = new_sha
        man_data["additional_assets"]["terra_175_benchmark.json"]["size"] = len(mutated_bytes)
        manifest_path.write_text(json.dumps(man_data, indent=2), encoding="utf-8")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())
        self.assertEqual(len(list(self.fixture["runs_base_dir"].glob("harness_run_*"))), 0)

    def test_09e_pre_launch_b350_duplicate_query_id_leaves_lock_unused(self):
        """Pre-launch gate: Benchmark 350 duplicate query_ids abort pre-flight without creating lock."""
        ws_b350 = self.fixture["workspace_root"] / "terra_350_benchmark.json"
        snap_b350 = self.fixture["snapshot_dir"] / "terra_350_benchmark.json"
        with open(ws_b350, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[1]["query_id"] = data[0]["query_id"]
        mutated_bytes = json.dumps(data, indent=2).encode("utf-8")
        ws_b350.write_bytes(mutated_bytes)
        snap_b350.write_bytes(mutated_bytes)
        new_sha = file_sha256(ws_b350)
        self.base_cfg["additional_assets"]["terra_350_benchmark.json"]["expected_sha256"] = new_sha
        manifest_path = self.fixture["snapshot_dir"] / "snapshot_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)
        man_data["additional_assets"]["terra_350_benchmark.json"]["sha256"] = new_sha
        man_data["additional_assets"]["terra_350_benchmark.json"]["size"] = len(mutated_bytes)
        manifest_path.write_text(json.dumps(man_data, indent=2), encoding="utf-8")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture["lock_path"].exists())
        self.assertEqual(len(list(self.fixture["runs_base_dir"].glob("harness_run_*"))), 0)

    # --------------------------------------------------------------------------
    # Group 2: Single-Run Lock Collision & Persistence
    # --------------------------------------------------------------------------
    def test_10_single_run_lock_collision_fails_closed(self):
        """Single-run lock: fail closed if lock already exists when all gates pass."""
        self.fixture["lock_path"].write_text("PRE_EXISTING_LOCK", encoding="utf-8")

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

    def test_11_single_run_lock_acquired_only_after_preflight_blocks_second_run(self):
        """Single-run lock: acquired only on committed execution, permanently blocking second run."""
        self.assertFalse(self.fixture["lock_path"].exists())

        # First run succeeds and acquires lock
        code1 = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code1, 0)
        self.assertTrue(self.fixture["lock_path"].exists())

        # Second run is blocked by retained lock
        code2 = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code2, 1)

    # --------------------------------------------------------------------------
    # Group 3: Production-Shaped Child Report Validation (Codex-0025, Claude-0084)
    # --------------------------------------------------------------------------
    def test_12_successful_run_with_production_shaped_report(self):
        """Lifecycle: fake child writes complete production-shaped report, exit code 0, all invariants pass."""
        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 0)

        harness_dirs = list(self.fixture["runs_base_dir"].glob("harness_run_*"))
        self.assertEqual(len(harness_dirs), 1)
        harness_dir = harness_dirs[0]

        self.assertEqual((harness_dir / "exit_code.txt").read_text().strip(), "0")

        with open(harness_dir / "execution_metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["wrapper_exit_code"], 0)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(meta["success"])
        self.assertEqual(len(meta["failure_reasons"]), 0)
        self.assertTrue(meta["post_run_invariants"]["all_invariants_passed"])
        self.assertTrue(meta["harness_config_supplied"])
        self.assertFalse(meta["harness_config_is_none"])
        self.assertIn("offline_enforcement_caveat", meta)

    def test_13_child_report_nested_mock_override_detected_fails_closed(self):
        """Report validation: nested is_mock_override=True detected and rejected."""
        write_fake_child_script(self.child_script, behavior="nested_mock_override")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("is_mock_override" in r or "mock embedding function detected" in r for r in meta["failure_reasons"]))

    def test_14_child_report_missing_nested_mock_field_fails_closed(self):
        """Report validation: missing is_mock_override in delegate detected and rejected."""
        write_fake_child_script(self.child_script, behavior="missing_nested_mock")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("missing mandatory 'is_mock_override'" in r for r in meta["failure_reasons"]))

    def test_15_child_report_script_hash_mismatch_fails_closed(self):
        """Report validation: child report script.sha256 mismatch detected and rejected."""
        write_fake_child_script(self.child_script, behavior="script_hash_mismatch")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("script SHA-256 mismatch" in r for r in meta["failure_reasons"]))

    def test_16_child_report_run_id_mismatch_fails_closed(self):
        """Report validation: child report run_id mismatch against directory detected."""
        write_fake_child_script(self.child_script, behavior="run_id_mismatch")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("run_id mismatch" in r for r in meta["failure_reasons"]))

    def test_17_child_report_missing_top_level_key_fails_closed(self):
        """Report validation: report missing required top-level production key fails closed."""
        write_fake_child_script(self.child_script, behavior="missing_top_key")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("missing required production key" in r for r in meta["failure_reasons"]))

    def test_18_child_report_populated_errors_list_fails_closed(self):
        """Report validation: report containing errors in errors list fails closed."""
        write_fake_child_script(self.child_script, behavior="populated_errors")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("errors list is not empty" in r for r in meta["failure_reasons"]))

    def test_19_child_report_missing_stage_fails_closed(self):
        """Report validation: report missing required completed stage fails closed."""
        write_fake_child_script(self.child_script, behavior="missing_stage")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("missing required stage completion" in r for r in meta["failure_reasons"]))

    def test_20_child_report_offline_condition_mismatch_fails_closed(self):
        """Report validation: report offline condition not matching harness parameter fails closed."""
        write_fake_child_script(self.child_script, behavior="offline_condition_mismatch")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("enforced_offline_condition' mismatch" in r for r in meta["failure_reasons"]))

    def test_21_child_report_truncated_ledger_350_fails_closed(self):
        """Report validation: report query_ledger_350 with length < 350 fails closed."""
        write_fake_child_script(self.child_script, behavior="truncated_ledger_350")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("query_ledger_350' length is 349, expected 350" in r for r in meta["failure_reasons"]))

    def test_22_child_report_duplicate_qid_ledger_350_fails_closed(self):
        """Report validation: duplicate query_id in query_ledger_350 fails closed."""
        write_fake_child_script(self.child_script, behavior="duplicate_qid_ledger_350")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("duplicate query_ids" in r for r in meta["failure_reasons"]))

    def test_23_child_report_nonfinite_distance_fails_closed(self):
        """Report validation: non-finite distance (NaN/Inf) in ledger fails closed."""
        write_fake_child_script(self.child_script, behavior="nonfinite_distance")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("finite float" in r for r in meta["failure_reasons"]))

    def test_24_child_report_truncated_legacy_ledger_fails_closed(self):
        """Report validation: report legacy_sample20_query_ledger with length < 40 fails closed."""
        write_fake_child_script(self.child_script, behavior="truncated_legacy_ledger")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("legacy_sample20_query_ledger' length is 39, expected 40" in r for r in meta["failure_reasons"]))

    def test_24b_child_report_legacy_ledger_missing_source_field_fails_closed(self):
        """Report validation: legacy ledger row missing source_field fails closed."""
        write_fake_child_script(self.child_script, behavior="legacy_missing_source_field")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("invalid source_field" in r for r in meta["failure_reasons"]))

    def test_24c_child_report_legacy_ledger_sha_mismatch_fails_closed(self):
        """Report validation: legacy ledger row query_sha256 mismatch against benchmark query text fails closed."""
        write_fake_child_script(self.child_script, behavior="legacy_sha_mismatch")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("query_sha256 sequence does not match" in r for r in meta["failure_reasons"]))

    def test_24d_child_report_legacy_ledger_id_mismatch_fails_closed(self):
        """Report validation: legacy ledger row query_id sequence mismatch against benchmark fails closed."""
        write_fake_child_script(self.child_script, behavior="legacy_id_mismatch")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("query_id sequence does not match" in r for r in meta["failure_reasons"]))

    def test_25_child_report_wrong_grid_thresholds_fails_closed(self):
        """Report validation: calibration grid threshold keys mismatch fails closed."""
        write_fake_child_script(self.child_script, behavior="wrong_grid_thresholds")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertEqual(meta["child_return_code"], 0)
        self.assertTrue(any("threshold keys mismatch" in r for r in meta["failure_reasons"]))

    # --------------------------------------------------------------------------
    # Group 4: Child Process Lifecycle & Anomalies
    # --------------------------------------------------------------------------
    def test_26_child_nonzero_exit_fails_closed(self):
        """Lifecycle: fake child exit code 2 captured, wrapper returns 1."""
        write_fake_child_script(self.child_script, behavior="nonzero_exit")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["child_return_code"], 2)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("non-zero exit code: 2" in r for r in meta["failure_reasons"]))

    def test_27_child_anomaly_zero_and_multiple_reports_fails_closed(self):
        """Lifecycle anomalies: zero reports and multiple reports detected and rejected with isolated configs."""
        # Case A: Zero reports
        write_fake_child_script(self.child_script, behavior="zero_reports")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)
        code_zero = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code_zero, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta_zero = json.load(f)
        self.assertTrue(any("ZERO_REPORTS" in r for r in meta_zero["failure_reasons"]))

        # Case B: Multiple reports in completely isolated fresh fixture
        with tempfile.TemporaryDirectory() as fresh_tmp:
            fresh_fixture = make_synthetic_fixture(Path(fresh_tmp))
            fresh_child = fresh_fixture["workspace_root"] / "fake_child.py"
            write_fake_child_script(fresh_child, behavior="multiple_reports")
            fresh_cfg = build_fixture_config(fresh_fixture, fresh_child)

            code_multi = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=fresh_cfg)
            self.assertEqual(code_multi, 1)

            with open(list(fresh_fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
                meta_multi = json.load(f)
            self.assertEqual(meta_multi["wrapper_exit_code"], 1)
            self.assertTrue(any("MULTIPLE_REPORTS" in r for r in meta_multi["failure_reasons"]))

    def test_28_child_stream_failure_terminates_child_cleanly(self):
        """Lifecycle safety: child stream failure terminates child cleanly and forces nonzero exit."""
        bad_cfg = dict(self.base_cfg)
        bad_cfg["simulate_stream_failure"] = True
        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=bad_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("Console stream reading failed" in r for r in meta["failure_reasons"]))

    # --------------------------------------------------------------------------
    # Group 5: Post-Run Invariants & Parity (Codex W2, Claude #3)
    # --------------------------------------------------------------------------
    def test_29_post_run_store_mutation_caught_in_finally_fails_closed(self):
        """Invariants: store file mutated during run detected in post-run finally re-hash."""
        write_fake_child_script(self.child_script, behavior="mutate_store")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertFalse(meta["post_run_invariants"]["all_invariants_passed"])
        self.assertTrue(any("POST_RUN_INVARIANT_HASH_MISMATCH" in r or "Store file" in r for r in meta["failure_reasons"]))

    def test_30_post_run_manifest_deletion_fails_closed(self):
        """Invariants: snapshot manifest deleted post-run caught against in-memory frozen hash."""
        write_fake_child_script(self.child_script, behavior="delete_manifest")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("SNAPSHOT_MANIFEST_DELETED_POST_RUN" in r for r in meta["failure_reasons"]))

    def test_31_post_run_manifest_mutation_fails_closed(self):
        """Invariants: snapshot manifest drifted post-run caught against in-memory frozen hash."""
        write_fake_child_script(self.child_script, behavior="mutate_manifest")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("SNAPSHOT_MANIFEST_MUTATED_POST_RUN" in r for r in meta["failure_reasons"]))

    def test_32_post_run_extra_store_file_caught_in_finally_fails_closed(self):
        """Invariants: extra store file added post-run caught by full post-inventory check."""
        write_fake_child_script(self.child_script, behavior="extra_store_file")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("Unexpected extra store file post-run" in r for r in meta["failure_reasons"]))

    def test_33_post_run_preserved_snapshot_asset_copy_mutation_fails_closed(self):
        """Invariants: preserved benchmark copy inside snapshot_dir mutated post-run detected in finally."""
        write_fake_child_script(self.child_script, behavior="mutate_snapshot_asset_copy")
        self.base_cfg["diagnostic_sha256"] = file_sha256(self.child_script)

        code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
        self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("Preserved snapshot asset copy terra_350_benchmark.json SHA256 mismatch post-run" in r for r in meta["failure_reasons"]))

    # --------------------------------------------------------------------------
    # Group 6: Reliable Evidence Writing Failures & Real Mocked I/O Exceptions
    # --------------------------------------------------------------------------
    def test_34_evidence_write_failures_reliably_force_nonzero(self):
        """Evidence safety: metadata/exit_code write failures force wrapper_exit_code = 1 with isolated configs."""
        # Case A: Injected metadata write failure
        bad_cfg = dict(self.base_cfg)
        bad_cfg["simulate_metadata_write_failure"] = True
        code_meta = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=bad_cfg)
        self.assertEqual(code_meta, 1)

        # Case B: Injected exit_code.txt write failure in completely isolated fresh fixture
        with tempfile.TemporaryDirectory() as fresh_tmp:
            fresh_fixture = make_synthetic_fixture(Path(fresh_tmp))
            fresh_child = fresh_fixture["workspace_root"] / "fake_child.py"
            write_fake_child_script(fresh_child, behavior="success")
            fresh_cfg = build_fixture_config(
                fresh_fixture,
                fresh_child,
                simulate_exit_code_write_failure=True
            )

            code_exit = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=fresh_cfg)
            self.assertEqual(code_exit, 1)

            with open(list(fresh_fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
                meta = json.load(f)
            self.assertEqual(meta["wrapper_exit_code"], 1)
            self.assertTrue(any("Failed to write exit_code.txt" in r for r in meta["failure_reasons"]))

    def test_35_real_mocked_io_exception_during_post_run_inventory_fails_closed(self):
        """Exception safety: real mocked OSError during post-run store inventory is caught and forces nonzero exit."""
        orig_dir_manifest = dir_manifest

        call_count = 0
        def mocked_dir_manifest(path):
            nonlocal call_count
            call_count += 1
            # First call is during pre-flight store check, let it pass
            if call_count <= 2:
                return orig_dir_manifest(path)
            # Subsequent calls (during post-run store re-hash) raise simulated OSError
            raise OSError("Simulated post-run disk I/O error during store inventory")

        with patch("scripts.run_diagnostic_harness.dir_manifest", side_effect=mocked_dir_manifest):
            code = action_execute_diagnostic("TEST_OFFLINE_FIREWALL", harness_config=self.base_cfg)
            self.assertEqual(code, 1)

        with open(list(self.fixture["runs_base_dir"].glob("harness_run_*"))[0] / "execution_metadata.json", "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["wrapper_exit_code"], 1)
        self.assertTrue(any("Simulated post-run disk I/O error" in r for r in meta["failure_reasons"]))

    # --------------------------------------------------------------------------
    # Group 7: Read-Only Audit of Production Constants
    # --------------------------------------------------------------------------
    def test_36_production_constants_read_only_audit(self):
        """Read-only verification of real workspace production pins without executing child."""
        self.assertTrue(PINNED_INTERPRETER_PATH.exists())
        self.assertEqual(file_sha256(PINNED_INTERPRETER_PATH), PINNED_INTERPRETER_SHA256)

        self.assertTrue(PINNED_DIAGNOSTIC_PATH.exists())
        self.assertEqual(file_sha256(PINNED_DIAGNOSTIC_PATH), PINNED_DIAGNOSTIC_SHA256)

        snap_manifest = SNAPSHOT_TARGET_DIR / "snapshot_manifest.json"
        self.assertTrue(snap_manifest.exists())

        with open(snap_manifest, "r", encoding="utf-8") as f:
            snap_data = json.load(f)
        expected_store = snap_data["vector_store_manifest"]
        self.assertEqual(len(expected_store), 11)

        real_manifest = dir_manifest(ORIGINAL_STORE_DIR)
        self.assertEqual(real_manifest, expected_store)

        # Check that all 4 additional assets exist in snapshot_dir and match manifest
        add_manifest = snap_data["additional_assets"]
        self.assertEqual(len(add_manifest), 4)
        for aname, aexp in add_manifest.items():
            scopy = SNAPSHOT_TARGET_DIR / aname
            self.assertTrue(scopy.exists())
            self.assertEqual(scopy.stat().st_size, aexp["size"])
            self.assertEqual(file_sha256(scopy), aexp["sha256"])

    def test_37_benchmark_schemas_real_workspace_read_only_audit(self):
        """Read-only verification that real workspace benchmark files strictly conform to schemas."""
        b350_path = WORKSPACE_ROOT / "terra_350_benchmark.json"
        b175_path = WORKSPACE_ROOT / "terra_175_benchmark.json"
        self.assertTrue(b350_path.exists())
        self.assertTrue(b175_path.exists())
        self.assertEqual(file_sha256(b350_path), EXPECTED_B350_SHA256)
        self.assertEqual(file_sha256(b175_path), EXPECTED_B175_SHA256)

        is_valid, errs, facts = validate_benchmark_schemas(b350_path, b175_path)
        self.assertTrue(is_valid, f"Validation errors: {errs}")
        self.assertEqual(len(errs), 0)
        self.assertEqual(facts["b350_query_count"], 350)
        self.assertEqual(facts["b350_unique_query_ids"], 350)
        self.assertEqual(facts["b350_category_counts"]["A_Factual"], 100)
        self.assertEqual(facts["b350_category_counts"]["B_Evolutionary"], 100)
        self.assertEqual(facts["b350_category_counts"]["C_OutOfContext"], 75)
        self.assertEqual(facts["b350_category_counts"]["D_Adversarial"], 75)
        self.assertEqual(facts["legacy_cohort_count"], 40)
        self.assertEqual(facts["legacy_unique_identifiers"], 40)
        self.assertEqual(len(facts["legacy_expected_identifiers"]), 40)
        self.assertEqual(len(facts["legacy_expected_shas"]), 40)
        # Verify that all 40 legacy records in the authentic benchmark resolved via native 'id'
        self.assertTrue(all(sf == "id" for sf in facts["legacy_source_fields"]))

    def test_38_resolve_benchmark_identifier_contract(self):
        """Direct unit test for resolve_benchmark_identifier behavior and error handling."""
        # query_id only
        qid, src = resolve_benchmark_identifier({"query_id": "qid_001"})
        self.assertEqual(qid, "qid_001")
        self.assertEqual(src, "query_id")

        # id only
        qid2, src2 = resolve_benchmark_identifier({"id": "S1_A01"})
        self.assertEqual(qid2, "S1_A01")
        self.assertEqual(src2, "id")

        # both: query_id takes priority
        qid3, src3 = resolve_benchmark_identifier({"query_id": "priority_qid", "id": "alt_id"})
        self.assertEqual(qid3, "priority_qid")
        self.assertEqual(src3, "query_id")

        # whitespace query_id falls back to id
        qid4, src4 = resolve_benchmark_identifier({"query_id": "   ", "id": "fallback_id"})
        self.assertEqual(qid4, "fallback_id")
        self.assertEqual(src4, "id")

        # missing both raises ValueError
        with self.assertRaises(ValueError):
            resolve_benchmark_identifier({"other": "field"})

        # empty both raises ValueError
        with self.assertRaises(ValueError):
            resolve_benchmark_identifier({"query_id": "", "id": "  "})

        # non-dict raises ValueError
        with self.assertRaises(ValueError):
            resolve_benchmark_identifier(["not", "a", "dict"])


if __name__ == "__main__":
    unittest.main()
