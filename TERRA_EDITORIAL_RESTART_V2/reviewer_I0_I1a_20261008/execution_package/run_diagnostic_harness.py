#!/usr/bin/env python3
"""
scripts/run_diagnostic_harness.py
=================================
Hardened execution harness and pre-run snapshot verification protocol for the
Contemporary Vector Distance Diagnostic (audit_i1a_contemporary_gate_calibration.py).

Authorship & Review History:
- Antigravity: Initial harness proposal & snapshot creation protocol (Antigravity-0017, Antigravity-0018).
- Codex: Audits & reviews (Codex-0022, Codex-0023, Codex-0024, Codex-0025, Codex-0044).
- Claude: Corroborating reviews & audits (Claude-0081, Claude-0082, Claude-0083, Claude-0084).
- Antigravity: Consolidated hardened revision (Antigravity-0022):
  1. Content-level child report validation (complete 350-query and 40-query ledgers, unique IDs,
     cohort categories, finite numerical distances, 8 canonical grid thresholds 0.90-1.40 with
     integer fp/tp/fn counts, concordance classification, empty error list, 10-stage completed sequence).
  2. Parity verification of all 4 preserved snapshot asset copies in snapshot_dir before and after.
  3. Enforced offline condition parameter whitelist checking and cross-check against child report.
  4. Recording harness_config_supplied in execution metadata with external firewall caveat.
  5. 100% fail-closed error recording, deferred one-run lock, and isolated test configurations.

DISCLOSURE OF HISTORICAL SQLITE OPENING:
During historical snapshot preparation on 2026-10-08, a read-only SQLite client connection
(file:...?mode=ro) opened original dataset_20k_cap/vector_db_20k/chroma.sqlite3 for PRAGMA integrity_check.
All 11 original vector store files were subsequently independently hashed by Codex and verified
bit-for-bit identical to reference. In accordance with Claude-0082 and Codex-0023, all future integrity
checks are strictly forbidden from connecting to or opening original store files. All future SQLite
read-only integrity checks must connect strictly to the preserved snapshot copy or disposable scratch
copies, and original-store validation is strictly restricted to external file-level SHA-256 hashing.
"""

import os
import sys
import time
import json
import math
import uuid
import shutil
import hashlib
import argparse
import subprocess
from pathlib import Path
from collections import Counter
from typing import Optional, Dict, Any, Tuple, List, Set

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_STORE_DIR = WORKSPACE_ROOT / "dataset_20k_cap" / "vector_db_20k"
ORIGINAL_SQLITE = ORIGINAL_STORE_DIR / "chroma.sqlite3"
SNAPSHOT_TARGET_DIR = WORKSPACE_ROOT / "TERRA_EDITORIAL_RESTART_V2" / "reviewer_I0_I1a_20261008" / "pre_run_snapshot_20k"
RUNS_BASE_DIR = WORKSPACE_ROOT / "TERRA_EDITORIAL_RESTART_V2" / "reviewer_I0_I1a_20261008" / "addendum_01" / "runs"
BENCHMARK_350 = WORKSPACE_ROOT / "terra_350_benchmark.json"
BENCHMARK_175 = WORKSPACE_ROOT / "terra_175_benchmark.json"
SAVED_SUMMARY = WORKSPACE_ROOT / "scratch" / "budget_and_gate_summary.json"
HISTORICAL_SCRIPT = WORKSPACE_ROOT / "scripts" / "compute_budget_and_gate_metrics.py"
DEFAULT_ONNX_CACHE = Path(r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx")

# Pinned Reference Hashes & Constraints
PINNED_INTERPRETER_PATH = Path(r"C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe")
PINNED_INTERPRETER_SHA256 = "3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd"

PINNED_DIAGNOSTIC_PATH = WORKSPACE_ROOT / "scripts" / "audit_i1a_contemporary_gate_calibration.py"
PINNED_DIAGNOSTIC_SHA256 = "c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d"

EXPECTED_SQLITE_SHA256 = "3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6"
EXPECTED_B350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
EXPECTED_B175_SHA256 = "8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305"
EXPECTED_SUMMARY_SHA256 = "b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f"
EXPECTED_HISTORICAL_SCRIPT_SHA256 = "ad6f26e858c79693e13163ccd77446bd77af7af21cb0552b262c68be6b04b5ca"

PINNED_LIBRARY_VERSIONS = {
    "chromadb": "1.5.9",
    "numpy": "2.5.1",
    "onnxruntime": "1.27.0"
}

APPROVED_OFFLINE_CONDITIONS = {
    "TERRA_Offline_Diagnostic",
    "TEST_OFFLINE_FIREWALL"
}

EXPECTED_GRID_THRESHOLD_KEYS = {
    "0.90", "1.00", "1.10", "1.20", "1.25", "1.30", "1.35", "1.40"
}

REQUIRED_STAGES = [
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

APPROVED_ONNX_CACHE_MANIFEST = {
    "config.json": {
        "size": 650,
        "sha256": "b567c7d5a55b636c95186aaf993f9a8920842b7e05a9e703e68b23cab2c3a670"
    },
    "model.onnx": {
        "size": 90387606,
        "sha256": "4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6"
    },
    "special_tokens_map.json": {
        "size": 125,
        "sha256": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3"
    },
    "tokenizer.json": {
        "size": 711661,
        "sha256": "da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0"
    },
    "tokenizer_config.json": {
        "size": 518,
        "sha256": "7702051bbc4953b94d47fa1d61b42ed4cbb3c71b501a8dd7183a823f8bea1f20"
    },
    "vocab.txt": {
        "size": 231508,
        "sha256": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3"
    }
}


def file_sha256(filepath: Path) -> str:
    """Compute standard SHA-256 of file in 1MB chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def dir_manifest(directory: Path) -> Dict[str, Dict[str, Any]]:
    """Compute recursive relative-path manifest with file size and SHA-256."""
    manifest = {}
    if not directory.exists():
        return manifest
    for f in sorted(directory.glob("**/*")):
        if f.is_file():
            rel = str(f.relative_to(directory)).replace("\\", "/")
            manifest[rel] = {
                "size": f.stat().st_size,
                "sha256": file_sha256(f)
            }
    return manifest


def measure_isolated_library_versions(py_exe: Path) -> Tuple[bool, Dict[str, str], Optional[str]]:
    """
    Measure live library versions in a clean, isolated child process to avoid
    importing chromadb or onnxruntime in the harness before network guards exist.
    """
    cmd = [
        str(py_exe),
        "-c",
        "import json, chromadb, numpy, onnxruntime; "
        "print(json.dumps({'chromadb': chromadb.__version__, 'numpy': numpy.__version__, 'onnxruntime': onnxruntime.__version__}))"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        data = json.loads(res.stdout.strip())
        return True, data, None
    except Exception as exc:
        return False, {}, str(exc)


def verify_runtime_pins(
    py_exe: Path,
    expected_py_sha256: str,
    diag_script: Path,
    expected_diag_sha256: str,
    expected_lib_versions: Dict[str, str],
    cache_dir: Path,
    onnx_manifest: Dict[str, Dict[str, Any]]
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Strictly verify interpreter, diagnostic script, libraries, and ONNX cache against pins."""
    errors = []
    facts = {}

    # 1. Pinned Interpreter
    if not py_exe.exists():
        errors.append(f"Pinned Python executable does not exist: {py_exe}")
    else:
        act_py_sha = file_sha256(py_exe)
        facts["python_executable"] = {"path": str(py_exe), "sha256": act_py_sha}
        if act_py_sha.lower() != expected_py_sha256.lower():
            errors.append(f"Python executable SHA256 mismatch: {act_py_sha} != {expected_py_sha256}")

    # 2. Pinned Diagnostic Script
    if not diag_script.exists():
        errors.append(f"Pinned diagnostic script does not exist: {diag_script}")
    else:
        act_diag_sha = file_sha256(diag_script)
        facts["diagnostic_script"] = {"path": str(diag_script), "sha256": act_diag_sha}
        if act_diag_sha.lower() != expected_diag_sha256.lower():
            errors.append(f"Diagnostic script SHA256 mismatch: {act_diag_sha} != {expected_diag_sha256}")

    # 3. Clean Subprocess Library Version Check
    if py_exe.exists() and len(errors) == 0:
        ok_ver, act_vers, ver_err = measure_isolated_library_versions(py_exe)
        if not ok_ver:
            errors.append(f"Failed to measure library versions in clean subprocess: {ver_err}")
        else:
            facts["library_versions"] = act_vers
            for lib, exp_ver in expected_lib_versions.items():
                act_ver = act_vers.get(lib)
                if act_ver != exp_ver:
                    errors.append(f"Library '{lib}' version mismatch: {act_ver} != {exp_ver}")

    # 4. ONNX Cache Manifest
    if not cache_dir.exists():
        errors.append(f"ONNX cache directory does not exist: {cache_dir}")
    else:
        onnx_facts = {}
        for fname, exp_info in onnx_manifest.items():
            fpath = cache_dir / fname
            if not fpath.exists():
                errors.append(f"Missing ONNX cache asset: {fpath}")
            else:
                sz = fpath.stat().st_size
                sha = file_sha256(fpath)
                onnx_facts[fname] = {"size": sz, "sha256": sha}
                if sz != exp_info["size"]:
                    errors.append(f"ONNX asset {fname} size mismatch: {sz} != {exp_info['size']}")
                if sha.lower() != exp_info["sha256"].lower():
                    errors.append(f"ONNX asset {fname} SHA256 mismatch: {sha} != {exp_info['sha256']}")
        facts["onnx_cache"] = onnx_facts

    return (len(errors) == 0, errors, facts)


def verify_snapshot_parity(
    store_dir: Path,
    snapshot_manifest_path: Path,
    snapshot_dir: Path,
    expected_additional: Dict[str, Dict[str, Any]]
) -> Tuple[bool, List[str], Dict[str, Any], Dict[str, Any], str]:
    """
    Verify bit-for-bit parity of source store and additional assets against snapshot manifest.
    Also verifies that the preserved snapshot copy directory itself matches the manifest.
    Returns (is_ok, errors, facts, frozen_manifest_data, manifest_sha256).
    """
    errors = []
    facts = {}
    manifest_data: Dict[str, Any] = {}
    manifest_sha = ""

    if not snapshot_manifest_path.exists():
        errors.append(f"Delivered snapshot manifest does not exist: {snapshot_manifest_path}")
        return False, errors, facts, manifest_data, manifest_sha

    try:
        manifest_sha = file_sha256(snapshot_manifest_path)
        with open(snapshot_manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except Exception as exc:
        errors.append(f"Failed to read snapshot manifest: {exc}")
        return False, errors, facts, manifest_data, manifest_sha

    expected_store_files = manifest_data.get("vector_store_manifest", {})
    if len(expected_store_files) != 11:
        errors.append(f"Snapshot manifest contains {len(expected_store_files)} store files; expected exactly 11.")

    manifest_additional = manifest_data.get("additional_assets", {})
    if len(manifest_additional) != 4:
        errors.append(f"Snapshot manifest contains {len(manifest_additional)} additional assets; expected exactly 4.")

    # 1. Verify original store files
    current_store_manifest = dir_manifest(store_dir)
    if len(current_store_manifest) != len(expected_store_files):
        errors.append(
            f"Store file count drift: current store has {len(current_store_manifest)} files, "
            f"snapshot manifest has {len(expected_store_files)}"
        )

    for rel_path, exp_info in expected_store_files.items():
        if rel_path not in current_store_manifest:
            errors.append(f"Original store missing file recorded in snapshot: {rel_path}")
        else:
            curr_info = current_store_manifest[rel_path]
            if curr_info["size"] != exp_info["size"]:
                errors.append(f"Store file {rel_path} size mismatch: {curr_info['size']} != {exp_info['size']}")
            if curr_info["sha256"].lower() != exp_info["sha256"].lower():
                errors.append(f"Store file {rel_path} SHA256 mismatch: {curr_info['sha256']} != {exp_info['sha256']}")

    for rel_path in current_store_manifest:
        if rel_path not in expected_store_files:
            errors.append(f"Original store contains unexpected extraneous file: {rel_path}")

    # 2. Verify preserved snapshot copy directory itself (vector store copy)
    snap_store_dir = snapshot_dir / "vector_db_20k"
    if not snap_store_dir.exists():
        errors.append(f"Preserved snapshot copy directory does not exist: {snap_store_dir}")
    else:
        snap_copy_manifest = dir_manifest(snap_store_dir)
        if snap_copy_manifest != expected_store_files:
            errors.append("Preserved snapshot copy directory does not match snapshot manifest!")

    # 3. Verify preserved snapshot copies of the 4 additional assets inside snapshot_dir (Codex-0025, Claude-0084)
    for aname, aexp in manifest_additional.items():
        snap_asset_copy = snapshot_dir / aname
        if not snap_asset_copy.exists():
            errors.append(f"Preserved snapshot asset copy does not exist: {snap_asset_copy}")
        else:
            act_size = snap_asset_copy.stat().st_size
            if act_size != aexp["size"]:
                errors.append(f"Preserved snapshot asset copy {aname} size mismatch: {act_size} != {aexp['size']}")
            act_sha = file_sha256(snap_asset_copy)
            if act_sha.lower() != aexp["sha256"].lower():
                errors.append(f"Preserved snapshot asset copy {aname} SHA256 mismatch against manifest: {act_sha} != {aexp['sha256']}")

    # 4. Verify live workspace additional assets against pins and snapshot manifest
    for aname, ainfo in expected_additional.items():
        apath = ainfo["path"]
        if not apath.exists():
            errors.append(f"Required asset does not exist: {apath}")
        else:
            curr_sha = file_sha256(apath)
            if curr_sha.lower() != ainfo["expected_sha256"].lower():
                errors.append(f"Asset {aname} SHA256 mismatch against pin: {curr_sha} != {ainfo['expected_sha256']}")
            if aname in manifest_additional:
                snap_sha = manifest_additional[aname]["sha256"]
                if curr_sha.lower() != snap_sha.lower():
                    errors.append(f"Asset {aname} SHA256 mismatch against snapshot: {curr_sha} != {snap_sha}")

    facts["current_store_manifest"] = current_store_manifest
    facts["snapshot_timestamp"] = manifest_data.get("timestamp_utc")
    facts["manifest_sha256"] = manifest_sha
    return (len(errors) == 0, errors, facts, manifest_data, manifest_sha)


def acquire_single_run_lock(lock_path: Path, run_id: str) -> Tuple[bool, Optional[str]]:
    """
    Acquire single-run lock file using exclusive creation ('x' mode).
    Fails closed immediately if lock already exists. Never deleted.
    """
    if lock_path.exists():
        return False, f"Single-run lock already exists at {lock_path}. Subsequent invocations are forbidden."
    try:
        with open(lock_path, "x", encoding="utf-8") as f:
            payload = {
                "locked_at_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "pid": os.getpid(),
                "harness_run_id": run_id
            }
            json.dump(payload, f, indent=2)
        return True, None
    except FileExistsError:
        return False, f"Single-run lock collision at {lock_path}."
    except Exception as exc:
        return False, f"Failed to acquire single-run lock at {lock_path}: {exc}"


def resolve_benchmark_identifier(q: dict) -> Tuple[str, str]:
    """
    Resolve identifier from benchmark record: query_id if present and nonempty, else id.
    Fails closed if neither is present or non-empty string (Codex-0026, Claude-0085).
    Returns (resolved_id, source_field).
    """
    if not isinstance(q, dict):
        raise ValueError(f"Benchmark record is not a dictionary: {type(q)}")
    qid = q.get("query_id")
    if isinstance(qid, str) and qid.strip():
        return qid.strip(), "query_id"
    alt_id = q.get("id")
    if isinstance(alt_id, str) and alt_id.strip():
        return alt_id.strip(), "id"
    raise ValueError(f"Benchmark record missing valid 'query_id' or 'id': {q}")


def validate_benchmark_schemas(
    benchmark_350_path: Path,
    benchmark_175_path: Path
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Read-only pre-launch validation of Benchmark 350 and Benchmark 175 schemas (Codex-0026, Claude-0085).
    Executed BEFORE single-run lock acquisition so input incompatibilities cannot waste the approved attempt.
    """
    errors: List[str] = []
    facts: Dict[str, Any] = {}

    # 1. Benchmark 350 Schema
    if not benchmark_350_path.exists():
        errors.append(f"Benchmark 350 file missing: {benchmark_350_path}")
    else:
        try:
            with open(benchmark_350_path, "r", encoding="utf-8") as f:
                b350 = json.load(f)
            if not isinstance(b350, list):
                errors.append(f"Benchmark 350 is not a list: {type(b350)}")
            elif len(b350) != 350:
                errors.append(f"Benchmark 350 item count is {len(b350)}, expected 350")
            else:
                qids_350 = []
                cat_counts: Dict[str, int] = {}
                for idx, entry in enumerate(b350):
                    if not isinstance(entry, dict):
                        errors.append(f"Benchmark 350 entry at index {idx} is not a dict")
                        continue
                    qid = entry.get("query_id")
                    if not isinstance(qid, str) or not qid.strip():
                        errors.append(f"Benchmark 350 entry at index {idx} missing valid 'query_id'")
                    else:
                        qids_350.append(qid.strip())
                    cat = entry.get("category")
                    if cat not in {"A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"}:
                        errors.append(f"Benchmark 350 entry at index {idx} has invalid category: {cat}")
                    else:
                        cat_counts[cat] = cat_counts.get(cat, 0) + 1
                    qtext = entry.get("query")
                    if not isinstance(qtext, str) or not qtext.strip():
                        errors.append(f"Benchmark 350 entry at index {idx} missing valid 'query' text")

                if len(set(qids_350)) != len(qids_350):
                    errors.append("Benchmark 350 contains duplicate query_ids")
                if cat_counts.get("A_Factual", 0) != 100:
                    errors.append(f"Benchmark 350 Category A count is {cat_counts.get('A_Factual', 0)}, expected 100")
                if cat_counts.get("B_Evolutionary", 0) != 100:
                    errors.append(f"Benchmark 350 Category B count is {cat_counts.get('B_Evolutionary', 0)}, expected 100")
                if cat_counts.get("C_OutOfContext", 0) != 75:
                    errors.append(f"Benchmark 350 Category C count is {cat_counts.get('C_OutOfContext', 0)}, expected 75")
                if cat_counts.get("D_Adversarial", 0) != 75:
                    errors.append(f"Benchmark 350 Category D count is {cat_counts.get('D_Adversarial', 0)}, expected 75")

                facts["b350_query_count"] = len(qids_350)
                facts["b350_unique_query_ids"] = len(set(qids_350))
                facts["b350_category_counts"] = cat_counts
        except Exception as exc:
            errors.append(f"Failed to load or parse Benchmark 350: {exc}")

    # 2. Benchmark 175 Schema
    if not benchmark_175_path.exists():
        errors.append(f"Benchmark 175 file missing: {benchmark_175_path}")
    else:
        try:
            with open(benchmark_175_path, "r", encoding="utf-8") as f:
                b175 = json.load(f)
            if not isinstance(b175, list):
                errors.append(f"Benchmark 175 is not a list: {type(b175)}")
            else:
                sample_in = [q for q in b175 if isinstance(q, dict) and q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
                sample_out = [q for q in b175 if isinstance(q, dict) and q.get("category") == "C_OutOfContext"][:20]

                if len(sample_in) != 20:
                    errors.append(f"Benchmark 175 sample_in_20 cohort count is {len(sample_in)}, expected 20")
                if len(sample_out) != 20:
                    errors.append(f"Benchmark 175 sample_out_20 cohort count is {len(sample_out)}, expected 20")

                legacy_40 = sample_in + sample_out
                leg_ids_40 = []
                leg_shas_40 = []
                leg_src_fields = []
                for idx, entry in enumerate(legacy_40):
                    try:
                        qid, src = resolve_benchmark_identifier(entry)
                        leg_ids_40.append(qid)
                        leg_src_fields.append(src)
                    except ValueError as id_err:
                        errors.append(f"Benchmark 175 legacy sample entry at index {idx} identifier error: {id_err}")
                    qtext = entry.get("query")
                    if not isinstance(qtext, str) or not qtext.strip():
                        errors.append(f"Benchmark 175 legacy sample entry at index {idx} missing valid 'query' text")
                    else:
                        leg_shas_40.append(hashlib.sha256(qtext.encode("utf-8")).hexdigest())

                if len(set(leg_ids_40)) != len(leg_ids_40):
                    errors.append("Benchmark 175 legacy sample cohorts contain duplicate identifiers")

                facts["legacy_cohort_count"] = len(legacy_40)
                facts["legacy_unique_identifiers"] = len(set(leg_ids_40))
                facts["legacy_expected_identifiers"] = leg_ids_40
                facts["legacy_expected_shas"] = leg_shas_40
                facts["legacy_source_fields"] = leg_src_fields
        except Exception as exc:
            errors.append(f"Failed to load or parse Benchmark 175: {exc}")

    is_valid = (len(errors) == 0)
    return is_valid, errors, facts


def validate_child_report(
    report_path: Path,
    expected_child_dir: Path,
    expected_diag_sha: str,
    enforced_offline_condition: str,
    benchmark_350_path: Optional[Path] = None,
    benchmark_175_path: Optional[Path] = None
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Production-shaped and content-level validation of the child report JSON (Codex-0025, Claude-0084).
    Strictly verifies:
    1. Complete production schema and empty error list (errors == []).
    2. Exact sequence of 10 completed diagnostic stages.
    3. Status == SUCCESS, run ID, filename, and diagnostic script SHA-256.
    4. Enforced offline condition alignment against harness parameter (both top-level and offline_execution_environment).
    5. Nested metadata.embedding_function_delegate.is_mock_override is boolean False.
    6. All integrity checks passed.
    7. Offline execution environment negative control passed and network guards uninstalled.
    8. Complete 350-query ledger: cardinality 350, unique query IDs, correct cohort categories
       (100 A, 100 B, 75 C, 75 D), non-empty nearest_node_id, and finite raw/sqrt numerical distances.
       If benchmark_350_path is provided and valid, verifies exact query ID sequence.
    9. Complete 40-query legacy ledger: cardinality 40, unique query IDs, correct cohorts
       (20 sample_in_20, 20 sample_out_20), non-empty nearest_node_id, and finite raw/sqrt distances.
       If benchmark_175_path is provided and valid, verifies exact query ID sequence.
    10. Complete 8-threshold calibration grid: exact thresholds ["0.90", "1.00", "1.10", "1.20", "1.25", "1.30", "1.35", "1.40"]
        with integer non-negative fp, tp, fn counts matching sample sizes.
    11. Concordance: valid concordance classification and finite AUROC values.
    """
    errors = []
    rep_data: Dict[str, Any] = {}

    if not report_path.exists():
        return False, [f"Report file does not exist: {report_path}"], rep_data

    try:
        with open(report_path, "r", encoding="utf-8") as rf:
            rep_data = json.load(rf)
    except Exception as exc:
        return False, [f"Failed to load report JSON: {exc}"], rep_data

    # 1. Required Top-Level Production Schema Keys
    required_keys = [
        "status", "run_id", "timestamp_utc", "script",
        "enforced_offline_condition", "offline_execution_environment",
        "provenance_disclaimer", "stages_completed", "errors",
        "integrity_checks", "metadata", "concordance",
        "distribution_summary_benchmark_350", "calibration_grid_benchmark_350",
        "legacy_sample20_diagnostic", "query_ledger_350", "legacy_sample20_query_ledger"
    ]
    for rk in required_keys:
        if rk not in rep_data:
            errors.append(f"Report missing required production key: '{rk}'")

    # 2. Outcome Status
    if rep_data.get("status") != "SUCCESS":
        errors.append(f"Report status is not 'SUCCESS': '{rep_data.get('status')}'")

    # 3. Empty Error List (Codex-0025, Claude-0084)
    rep_errors = rep_data.get("errors")
    if not isinstance(rep_errors, list):
        errors.append(f"Report 'errors' is not a list: {type(rep_errors).__name__}")
    elif len(rep_errors) != 0:
        errors.append(f"Report errors list is not empty ({len(rep_errors)} error(s) recorded): {rep_errors}")

    # 4. Completed Stages Full Sequence
    stages_comp = rep_data.get("stages_completed")
    if not isinstance(stages_comp, list):
        errors.append(f"Report 'stages_completed' is not a list: {type(stages_comp).__name__}")
    else:
        for st in REQUIRED_STAGES:
            if st not in stages_comp:
                errors.append(f"Report missing required stage completion: '{st}'")

    # 5. Run ID Alignment
    rep_run_id = rep_data.get("run_id")
    expected_run_id = expected_child_dir.name.replace("run_", "")
    if rep_run_id != expected_run_id:
        errors.append(f"Report run_id mismatch: '{rep_run_id}' != '{expected_run_id}'")

    expected_filename = f"contemporary_distance_diagnostic_{expected_run_id}.json"
    if report_path.name != expected_filename:
        errors.append(f"Report filename mismatch: '{report_path.name}' != '{expected_filename}'")

    # 6. Diagnostic Script SHA-256 Alignment
    script_info = rep_data.get("script", {})
    if not isinstance(script_info, dict) or "sha256" not in script_info:
        errors.append("Report missing script.sha256 entry")
    else:
        rep_script_sha = str(script_info["sha256"]).lower()
        if rep_script_sha != expected_diag_sha.lower():
            errors.append(f"Report script SHA-256 mismatch: {rep_script_sha} != {expected_diag_sha.lower()}")

    # 7. Offline Execution Condition Cross-Check (Codex-0025, Claude-0084)
    rep_offline_cond = rep_data.get("enforced_offline_condition")
    if rep_offline_cond != enforced_offline_condition:
        errors.append(
            f"Report top-level 'enforced_offline_condition' mismatch: '{rep_offline_cond}' != '{enforced_offline_condition}'"
        )

    offline_env = rep_data.get("offline_execution_environment", {})
    if not isinstance(offline_env, dict):
        errors.append("Report 'offline_execution_environment' is not a dictionary")
    else:
        env_cond = offline_env.get("enforced_offline_condition")
        if env_cond != enforced_offline_condition:
            errors.append(
                f"Report offline_execution_environment.enforced_offline_condition mismatch: '{env_cond}' != '{enforced_offline_condition}'"
            )
        if offline_env.get("negative_control_passed") is not True:
            errors.append("Report offline_execution_environment negative_control_passed is not True")
        if offline_env.get("network_guards_uninstalled") is not True:
            errors.append("Report offline_execution_environment network_guards_uninstalled is not True")

    # 8. Nested Mock Check (metadata.embedding_function_delegate.is_mock_override)
    metadata = rep_data.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("Report 'metadata' is not a dictionary")
    else:
        ef_delegate = metadata.get("embedding_function_delegate")
        if not isinstance(ef_delegate, dict):
            errors.append("Report 'metadata.embedding_function_delegate' is missing or not a dictionary")
        else:
            if "is_mock_override" not in ef_delegate:
                errors.append("Report 'metadata.embedding_function_delegate' missing mandatory 'is_mock_override' field")
            else:
                is_mock = ef_delegate["is_mock_override"]
                if not isinstance(is_mock, bool):
                    errors.append(f"Report 'is_mock_override' is not boolean: {type(is_mock).__name__}")
                elif is_mock is not False:
                    errors.append("Report 'is_mock_override' is True: mock embedding function detected")

    # 9. Integrity Checks
    integ = rep_data.get("integrity_checks", {})
    if not isinstance(integ, dict):
        errors.append("Report 'integrity_checks' is not a dictionary")
    else:
        if integ.get("all_integrity_passed") is not True:
            errors.append("Report integrity checks all_integrity_passed is not True")

    # 10. Complete 350-Query Ledger Validation
    ledger_350 = rep_data.get("query_ledger_350")
    if not isinstance(ledger_350, list):
        errors.append("Report 'query_ledger_350' is not a list")
    else:
        if len(ledger_350) != 350:
            errors.append(f"Report 'query_ledger_350' length is {len(ledger_350)}, expected 350")

        qids_350 = []
        cat_counts: Dict[str, int] = {}
        for idx, item in enumerate(ledger_350):
            if not isinstance(item, dict):
                errors.append(f"Report 'query_ledger_350' item at index {idx} is not a dict")
                continue
            qid = item.get("query_id")
            if not isinstance(qid, str) or not qid.strip():
                errors.append(f"Report 'query_ledger_350' item at index {idx} has invalid query_id: {qid}")
            else:
                qids_350.append(qid)

            cat = item.get("category")
            if not isinstance(cat, str) or cat not in {"A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"}:
                errors.append(f"Report 'query_ledger_350' item '{qid}' has invalid category: {cat}")
            else:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            nid = item.get("nearest_node_id")
            if not isinstance(nid, str) or not nid.strip():
                errors.append(f"Report 'query_ledger_350' item '{qid}' has invalid nearest_node_id: {repr(nid)}")

            d_raw = item.get("distance_raw_squared")
            if not isinstance(d_raw, (int, float)) or not math.isfinite(d_raw):
                errors.append(f"Report 'query_ledger_350' item '{qid}' distance_raw_squared is not a finite float: {d_raw}")

            d_sqrt = item.get("distance_euclidean_sqrt")
            if not isinstance(d_sqrt, (int, float)) or not math.isfinite(d_sqrt):
                errors.append(f"Report 'query_ledger_350' item '{qid}' distance_euclidean_sqrt is not a finite float: {d_sqrt}")

        if len(set(qids_350)) != len(qids_350):
            errors.append("Report 'query_ledger_350' contains duplicate query_ids")

        if cat_counts.get("A_Factual", 0) != 100:
            errors.append(f"Report 'query_ledger_350' Category A count is {cat_counts.get('A_Factual', 0)}, expected 100")
        if cat_counts.get("B_Evolutionary", 0) != 100:
            errors.append(f"Report 'query_ledger_350' Category B count is {cat_counts.get('B_Evolutionary', 0)}, expected 100")
        if cat_counts.get("C_OutOfContext", 0) != 75:
            errors.append(f"Report 'query_ledger_350' Category C (OOD) count is {cat_counts.get('C_OutOfContext', 0)}, expected 75")
        if cat_counts.get("D_Adversarial", 0) != 75:
            errors.append(f"Report 'query_ledger_350' Category D (Adversarial) count is {cat_counts.get('D_Adversarial', 0)}, expected 75")

        # Strict verification against benchmark_350_path
        if benchmark_350_path is not None:
            if not benchmark_350_path.exists():
                errors.append(f"Benchmark 350 file missing for validation: {benchmark_350_path}")
            else:
                try:
                    with open(benchmark_350_path, "r", encoding="utf-8") as bf:
                        bench_350_data = json.load(bf)
                    if not isinstance(bench_350_data, list) or len(bench_350_data) != 350:
                        errors.append(f"Benchmark 350 file has invalid structure or length != 350")
                    else:
                        exp_qids_350 = []
                        for bq in bench_350_data:
                            qid, _ = resolve_benchmark_identifier(bq)
                            exp_qids_350.append(qid)
                        if qids_350 != exp_qids_350:
                            errors.append("Report 'query_ledger_350' query_id sequence does not match Benchmark 350 input file")
                except Exception as b_err:
                    errors.append(f"Failed to read benchmark_350_path for validation: {b_err}")

    # 11. Complete 40-Query Legacy Ledger Validation
    ledger_40 = rep_data.get("legacy_sample20_query_ledger")
    if not isinstance(ledger_40, list):
        errors.append("Report 'legacy_sample20_query_ledger' is not a list")
    else:
        if len(ledger_40) != 40:
            errors.append(f"Report 'legacy_sample20_query_ledger' length is {len(ledger_40)}, expected 40")

        qids_40 = []
        actual_shas_40 = []
        actual_src_fields = []
        cohort_counts: Dict[str, int] = {}
        for idx, item in enumerate(ledger_40):
            if not isinstance(item, dict):
                errors.append(f"Report 'legacy_sample20_query_ledger' item at index {idx} is not a dict")
                continue
            qid = item.get("query_id")
            if not isinstance(qid, str) or not qid.strip():
                errors.append(f"Report 'legacy_sample20_query_ledger' item at index {idx} has invalid query_id: {qid}")
            else:
                qids_40.append(qid.strip())

            src_field = item.get("source_field")
            if src_field not in {"query_id", "id"}:
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' has invalid source_field: {repr(src_field)}")
            else:
                actual_src_fields.append(src_field)

            q_sha = item.get("query_sha256")
            if not isinstance(q_sha, str) or len(q_sha) != 64 or not all(c in "0123456789abcdefABCDEF" for c in q_sha):
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' has invalid query_sha256: {repr(q_sha)}")
            else:
                actual_shas_40.append(q_sha.lower())

            cohort = item.get("cohort")
            if cohort not in {"sample_in_20", "sample_out_20"}:
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' has invalid cohort: {cohort}")
            else:
                cohort_counts[cohort] = cohort_counts.get(cohort, 0) + 1

            nid = item.get("nearest_node_id")
            if not isinstance(nid, str) or not nid.strip():
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' has invalid nearest_node_id: {repr(nid)}")

            d_raw = item.get("distance_raw_squared")
            if not isinstance(d_raw, (int, float)) or not math.isfinite(d_raw):
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' distance_raw_squared is not a finite float: {d_raw}")

            d_sqrt = item.get("distance_euclidean_sqrt")
            if not isinstance(d_sqrt, (int, float)) or not math.isfinite(d_sqrt):
                errors.append(f"Report 'legacy_sample20_query_ledger' item '{qid}' distance_euclidean_sqrt is not a finite float: {d_sqrt}")

        if len(set(qids_40)) != len(qids_40):
            errors.append("Report 'legacy_sample20_query_ledger' contains duplicate query_ids")

        if cohort_counts.get("sample_in_20", 0) != 20:
            errors.append(f"Report 'legacy_sample20_query_ledger' sample_in_20 count is {cohort_counts.get('sample_in_20', 0)}, expected 20")
        if cohort_counts.get("sample_out_20", 0) != 20:
            errors.append(f"Report 'legacy_sample20_query_ledger' sample_out_20 count is {cohort_counts.get('sample_out_20', 0)}, expected 20")

        # Strict verification against benchmark_175_path
        if benchmark_175_path is not None:
            if not benchmark_175_path.exists():
                errors.append(f"Benchmark 175 file missing for validation: {benchmark_175_path}")
            else:
                try:
                    with open(benchmark_175_path, "r", encoding="utf-8") as bf175:
                        bench_175_data = json.load(bf175)
                    if not isinstance(bench_175_data, list):
                        errors.append(f"Benchmark 175 file is not a list: {type(bench_175_data)}")
                    else:
                        sample_in = [q for q in bench_175_data if isinstance(q, dict) and q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
                        sample_out = [q for q in bench_175_data if isinstance(q, dict) and q.get("category") == "C_OutOfContext"][:20]
                        if len(sample_in) != 20 or len(sample_out) != 20:
                            errors.append(f"Benchmark 175 sample cohort counts invalid: in={len(sample_in)}, out={len(sample_out)}, expected 20 each")
                        else:
                            exp_leg_records = sample_in + sample_out
                            exp_leg_ids = []
                            exp_leg_shas = []
                            exp_src_fields = []
                            for idx_leg, lq in enumerate(exp_leg_records):
                                try:
                                    lqid, lsrc = resolve_benchmark_identifier(lq)
                                    exp_leg_ids.append(lqid)
                                    exp_src_fields.append(lsrc)
                                except ValueError as l_err:
                                    errors.append(f"Benchmark 175 entry {idx_leg} identifier resolution failed: {l_err}")
                                ltext = lq.get("query", "")
                                exp_leg_shas.append(hashlib.sha256(ltext.encode("utf-8")).hexdigest().lower())

                            if qids_40 != exp_leg_ids:
                                errors.append("Report 'legacy_sample20_query_ledger' query_id sequence does not match Benchmark 175 sample cohorts")
                            if actual_shas_40 != exp_leg_shas:
                                errors.append("Report 'legacy_sample20_query_ledger' query_sha256 sequence does not match Benchmark 175 query texts")
                            if actual_src_fields != exp_src_fields:
                                errors.append("Report 'legacy_sample20_query_ledger' source_field sequence does not match Benchmark 175 records")
                except Exception as b_err:
                    errors.append(f"Failed to read benchmark_175_path for validation: {b_err}")

    # 12. Calibration Grid 8 Production Thresholds
    grid = rep_data.get("calibration_grid_benchmark_350")
    if not isinstance(grid, dict):
        errors.append("Report 'calibration_grid_benchmark_350' is not a dictionary")
    else:
        normalized_keys = set()
        for k in grid.keys():
            try:
                normalized_keys.add(f"{float(k):.2f}")
            except (ValueError, TypeError):
                errors.append(f"Report calibration grid contains non-numerical threshold key: '{k}'")

        if normalized_keys != EXPECTED_GRID_THRESHOLD_KEYS or len(grid) != 8:
            errors.append(
                f"Report calibration grid threshold keys mismatch: found {sorted(list(grid.keys()))}, "
                f"expected exactly 8 production thresholds {sorted(list(EXPECTED_GRID_THRESHOLD_KEYS))}"
            )

        for k, entry in grid.items():
            if not isinstance(entry, dict):
                errors.append(f"Report calibration grid entry '{k}' is not a dict")
                continue
            fp_val = entry.get("fp_count", entry.get("fp"))
            tp_val = entry.get("tp_count", entry.get("tp"))
            fn_val = entry.get("fn_count", entry.get("fn"))
            if not isinstance(fp_val, int) or fp_val < 0:
                errors.append(f"Report grid threshold '{k}' invalid or non-integer fp count: {fp_val}")
            if not isinstance(tp_val, int) or tp_val < 0:
                errors.append(f"Report grid threshold '{k}' invalid or non-integer tp count: {tp_val}")
            if not isinstance(fn_val, int) or fn_val < 0:
                errors.append(f"Report grid threshold '{k}' invalid or non-integer fn count: {fn_val}")

            if isinstance(tp_val, int) and isinstance(fn_val, int):
                if tp_val + fn_val != 75:
                    errors.append(f"Report grid threshold '{k}' tp + fn sum is {tp_val + fn_val}, expected 75 (n_ood)")
            if isinstance(fp_val, int) and fp_val > 200:
                errors.append(f"Report grid threshold '{k}' fp count {fp_val} exceeds total in-domain count (200)")

    # 13. Concordance Classification & Numerical Fields
    concordance = rep_data.get("concordance")
    if not isinstance(concordance, dict):
        errors.append("Report 'concordance' is not a dictionary")
    else:
        classification = concordance.get("concordance_classification")
        if not isinstance(classification, str) or not classification.strip():
            errors.append(f"Report 'concordance_classification' is missing or not a non-empty string: {classification}")
        else:
            valid_cls = (
                classification in {"EXACT_CONCORDANCE", "AUROC_DRIFT_WITH_IDENTICAL_GRID_COUNTS"} or
                classification.startswith("GRID_COUNT_DISCORDANCE_")
            )
            if not valid_cls:
                errors.append(f"Report 'concordance_classification' has unrecognized value: '{classification}'")

        diag_auroc = concordance.get("diagnostic_auroc")
        if not isinstance(diag_auroc, (int, float)) or not math.isfinite(diag_auroc):
            errors.append(f"Report concordance 'diagnostic_auroc' is not a finite float: {diag_auroc}")

        saved_auroc = concordance.get("saved_auroc")
        if not isinstance(saved_auroc, (int, float)) or not math.isfinite(saved_auroc):
            errors.append(f"Report concordance 'saved_auroc' is not a finite float: {saved_auroc}")

        auroc_diff = concordance.get("auroc_difference")
        if not isinstance(auroc_diff, (int, float)) or not math.isfinite(auroc_diff):
            errors.append(f"Report concordance 'auroc_difference' is not a finite float: {auroc_diff}")

        grid_mismatch_cnt = concordance.get("grid_mismatch_count")
        if not isinstance(grid_mismatch_cnt, int) or grid_mismatch_cnt < 0:
            errors.append(f"Report concordance 'grid_mismatch_count' is not a non-negative integer: {grid_mismatch_cnt}")

    return (len(errors) == 0, errors, rep_data)


# ------------------------------------------------------------------------------
# Action 1: Pre-Run Snapshot Creation (Historical / Invariant)
# ------------------------------------------------------------------------------
def action_create_snapshot(
    snapshot_target_dir: Path = SNAPSHOT_TARGET_DIR,
    store_dir: Path = ORIGINAL_STORE_DIR,
    workspace_root: Path = WORKSPACE_ROOT
) -> int:
    """
    Snapshot creation protocol.
    Fails closed if destination exists to preserve accepted evidence.
    """
    print("=" * 80)
    print("ACTION: PRE-RUN INPUT SNAPSHOT CREATION & VERIFICATION")
    print(f"Target: {snapshot_target_dir}")
    print("=" * 80)

    if snapshot_target_dir.exists():
        print(f"[STOP CONDITION] Snapshot target directory already exists: {snapshot_target_dir}", file=sys.stderr)
        print("Failing closed to prevent accidental overwrite of existing snapshot evidence.", file=sys.stderr)
        return 1

    free_bytes = shutil.disk_usage(workspace_root).free
    free_gb = free_bytes / (1024 ** 3)
    if free_gb < 10.0:
        print(f"[STOP CONDITION] Insufficient disk space ({free_gb:.2f} GB < 10.0 GB threshold)!", file=sys.stderr)
        return 1

    # Check pre-copy hashes of original store SQLite and additional assets
    sqlite_file = store_dir / "chroma.sqlite3"
    if not sqlite_file.exists():
        print(f"[STOP CONDITION] Source SQLite does not exist: {sqlite_file}", file=sys.stderr)
        return 1
    if file_sha256(sqlite_file) != EXPECTED_SQLITE_SHA256:
        print("[STOP CONDITION] Source SQLite SHA256 mismatch before copy!", file=sys.stderr)
        return 1

    b350_path = workspace_root / "terra_350_benchmark.json"
    b175_path = workspace_root / "terra_175_benchmark.json"
    sum_path = workspace_root / "scratch" / "budget_and_gate_summary.json"
    hist_path = workspace_root / "scripts" / "compute_budget_and_gate_metrics.py"

    if file_sha256(b350_path) != EXPECTED_B350_SHA256:
        print("[STOP CONDITION] Benchmark 350 SHA256 mismatch!", file=sys.stderr)
        return 1
    if file_sha256(b175_path) != EXPECTED_B175_SHA256:
        print("[STOP CONDITION] Benchmark 175 SHA256 mismatch!", file=sys.stderr)
        return 1
    if file_sha256(sum_path) != EXPECTED_SUMMARY_SHA256:
        print("[STOP CONDITION] Saved summary SHA256 mismatch!", file=sys.stderr)
        return 1
    if file_sha256(hist_path) != EXPECTED_HISTORICAL_SCRIPT_SHA256:
        print("[STOP CONDITION] Historical script SHA256 mismatch!", file=sys.stderr)
        return 1

    # Execute copy
    dest_store_dir = snapshot_target_dir / "vector_db_20k"
    dest_store_dir.mkdir(parents=True, exist_ok=False)
    shutil.copytree(store_dir, dest_store_dir, dirs_exist_ok=True)

    shutil.copy2(b350_path, snapshot_target_dir / b350_path.name)
    shutil.copy2(b175_path, snapshot_target_dir / b175_path.name)
    shutil.copy2(sum_path, snapshot_target_dir / sum_path.name)
    shutil.copy2(hist_path, snapshot_target_dir / hist_path.name)

    # Verify bit-for-bit parity
    src_manifest = dir_manifest(store_dir)
    dest_manifest = dir_manifest(dest_store_dir)
    if src_manifest != dest_manifest:
        print("[CRITICAL FAILURE] Snapshot copy manifest mismatch!", file=sys.stderr)
        return 1

    full_manifest = {
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "original_source_store": str(store_dir),
        "snapshot_directory": str(snapshot_target_dir),
        "vector_store_manifest": dest_manifest,
        "additional_assets": {
            b350_path.name: {"size": b350_path.stat().st_size, "sha256": file_sha256(snapshot_target_dir / b350_path.name)},
            b175_path.name: {"size": b175_path.stat().st_size, "sha256": file_sha256(snapshot_target_dir / b175_path.name)},
            sum_path.name: {"size": sum_path.stat().st_size, "sha256": file_sha256(snapshot_target_dir / sum_path.name)},
            hist_path.name: {"size": hist_path.stat().st_size, "sha256": file_sha256(snapshot_target_dir / hist_path.name)}
        }
    }
    manifest_file = snapshot_target_dir / "snapshot_manifest.json"
    with open(manifest_file, "x", encoding="utf-8") as f:
        json.dump(full_manifest, f, indent=2)

    print(f"\nSnapshot successfully created and verified at: {snapshot_target_dir}")
    return 0


# ------------------------------------------------------------------------------
# Action 2: Hardened Diagnostic Execution Harness
# ------------------------------------------------------------------------------
def action_execute_diagnostic(
    enforced_offline_condition: str,
    harness_config: Optional[Dict[str, Any]] = None
) -> int:
    """
    Execute single pinned diagnostic under strict, failure-safe controls.
    Supports optional harness_config for synthetic unit/integration testing.
    """
    cfg = harness_config or {}

    ws_root = Path(cfg.get("workspace_root", WORKSPACE_ROOT)).resolve()
    store_dir = Path(cfg.get("store_dir", ORIGINAL_STORE_DIR)).resolve()
    snapshot_dir = Path(cfg.get("snapshot_dir", SNAPSHOT_TARGET_DIR)).resolve()
    runs_base_dir = Path(cfg.get("runs_base_dir", RUNS_BASE_DIR)).resolve()
    diag_script = Path(cfg.get("diagnostic_script", PINNED_DIAGNOSTIC_PATH)).resolve()
    py_exe = Path(cfg.get("python_executable", PINNED_INTERPRETER_PATH)).resolve()
    py_sha = str(cfg.get("python_sha256", PINNED_INTERPRETER_SHA256))
    diag_sha = str(cfg.get("diagnostic_sha256", PINNED_DIAGNOSTIC_SHA256))
    cache_dir = Path(cfg.get("onnx_cache_dir", DEFAULT_ONNX_CACHE)).resolve()
    onnx_manifest = cfg.get("onnx_manifest", APPROVED_ONNX_CACHE_MANIFEST)
    expected_lib_versions = cfg.get("expected_lib_versions", PINNED_LIBRARY_VERSIONS)
    lock_path = Path(cfg.get("lock_path", runs_base_dir / ".single_run_lock")).resolve()

    additional_assets = cfg.get("additional_assets", {
        "terra_350_benchmark.json": {"path": ws_root / "terra_350_benchmark.json", "expected_sha256": EXPECTED_B350_SHA256},
        "terra_175_benchmark.json": {"path": ws_root / "terra_175_benchmark.json", "expected_sha256": EXPECTED_B175_SHA256},
        "budget_and_gate_summary.json": {"path": ws_root / "scratch" / "budget_and_gate_summary.json", "expected_sha256": EXPECTED_SUMMARY_SHA256},
        "compute_budget_and_gate_metrics.py": {"path": ws_root / "scripts" / "compute_budget_and_gate_metrics.py", "expected_sha256": EXPECTED_HISTORICAL_SCRIPT_SHA256}
    })

    print("=" * 80)
    print("ACTION: HARDENED CONTEMPORARY DIAGNOSTIC HARNESS EXECUTION")
    print(f"Workspace Root: {ws_root}")
    print(f"Declared Offline Condition: {enforced_offline_condition}")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 1: Validate Offline Condition Parameter against Approved Whitelist
    # --------------------------------------------------------------------------
    if not enforced_offline_condition or not enforced_offline_condition.strip():
        print("[PRE-LAUNCH GATE FAILURE] Enforced offline condition cannot be empty.", file=sys.stderr)
        return 1

    approved_conditions = set(cfg.get("approved_offline_conditions", APPROVED_OFFLINE_CONDITIONS))
    if enforced_offline_condition.strip() not in approved_conditions:
        print(
            f"[PRE-LAUNCH GATE FAILURE] Refusing execution: '{enforced_offline_condition}' "
            f"is not in approved offline execution conditions set: {sorted(list(approved_conditions))}.",
            file=sys.stderr
        )
        return 1

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 2: Verify Runtime Pins (Interpreter, Diagnostic Script, Libraries, Cache)
    # --------------------------------------------------------------------------
    pins_ok, pin_errors, pin_facts = verify_runtime_pins(
        py_exe=py_exe,
        expected_py_sha256=py_sha,
        diag_script=diag_script,
        expected_diag_sha256=diag_sha,
        expected_lib_versions=expected_lib_versions,
        cache_dir=cache_dir,
        onnx_manifest=onnx_manifest
    )
    if not pins_ok:
        print("[PRE-LAUNCH GATE FAILURE] Runtime environment pin verification failed:", file=sys.stderr)
        for err in pin_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("PASS: Pinned Python interpreter, diagnostic script, library versions, and ONNX cache verified.")

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 3: Verify Store Parity and Freeze Manifest Reference (Codex W2, Claude #3)
    # --------------------------------------------------------------------------
    snapshot_manifest_path = snapshot_dir / "snapshot_manifest.json"
    parity_ok, parity_errors, parity_facts, frozen_manifest_data, frozen_manifest_sha = verify_snapshot_parity(
        store_dir=store_dir,
        snapshot_manifest_path=snapshot_manifest_path,
        snapshot_dir=snapshot_dir,
        expected_additional=additional_assets
    )
    if not parity_ok:
        print("[PRE-LAUNCH GATE FAILURE] Store and asset parity verification against snapshot failed:", file=sys.stderr)
        for err in parity_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("PASS: Pre-launch parity confirmed across all 11 store files, snapshot copy, and additional assets.")

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 4: Read-Only Benchmark Schema Validation (Codex-0026, Claude-0085)
    # --------------------------------------------------------------------------
    b350_path = Path(additional_assets.get("terra_350_benchmark.json", {}).get("path", ws_root / "terra_350_benchmark.json")).resolve()
    b175_path = Path(additional_assets.get("terra_175_benchmark.json", {}).get("path", ws_root / "terra_175_benchmark.json")).resolve()
    bench_schemas_ok, bench_schema_errors, bench_schema_facts = validate_benchmark_schemas(b350_path, b175_path)
    if not bench_schemas_ok:
        print("[PRE-LAUNCH GATE FAILURE] Benchmark schema validation failed before lock acquisition:", file=sys.stderr)
        for err in bench_schema_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("PASS: Read-only Benchmark 350 and Benchmark 175 schemas validated (identifiers, categories, uniqueness).")

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 5: Record Pre-Existing Directory Inventory
    # --------------------------------------------------------------------------
    runs_base_dir.mkdir(parents=True, exist_ok=True)
    pre_existing_runs: Set[Path] = {p.resolve() for p in runs_base_dir.glob("run_*") if p.is_dir()}

    # --------------------------------------------------------------------------
    # Pre-Launch Gate 6: Acquire Single-Run Lock (Deferred until all preflights pass)
    # --------------------------------------------------------------------------
    run_timestamp = int(time.time())
    harness_uuid = uuid.uuid4().hex[:8]
    harness_run_id = f"{run_timestamp}_{os.getpid()}_{harness_uuid}"

    lock_ok, lock_err = acquire_single_run_lock(lock_path, harness_run_id)
    if not lock_ok:
        print(f"[PRE-LAUNCH GATE FAILURE] Single-run lock failed: {lock_err}", file=sys.stderr)
        return 1
    print(f"PASS: Single-run lock acquired at: {lock_path}")

    # --------------------------------------------------------------------------
    # Harness Execution Setup
    # --------------------------------------------------------------------------
    harness_dir = runs_base_dir / f"harness_run_{harness_run_id}"
    harness_dir.mkdir(parents=True, exist_ok=False)

    console_log_path = harness_dir / "console_output.log"
    exit_code_path = harness_dir / "exit_code.txt"
    metadata_path = harness_dir / "execution_metadata.json"

    # Execution State
    child_proc: Optional[subprocess.Popen] = None
    child_return_code: Optional[int] = None
    wrapper_exit_code: int = 1
    failure_reasons: List[str] = []
    discovered_child_dir: Optional[Path] = None
    discovered_report_file: Optional[Path] = None
    discovered_report_data: Optional[Dict[str, Any]] = None
    start_time_monotonic = time.monotonic()
    start_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # Approved Command Line Construction (Only approved options)
    cmd = [
        str(py_exe),
        str(diag_script),
        "--workspace-root", str(ws_root),
        "--onnx-cache-dir", str(cache_dir),
        "--enforced-offline-condition", enforced_offline_condition
    ]

    print(f"\nLaunching diagnostic child subprocess:\n  {' '.join(cmd)}\n")
    print(f"Harness Directory: {harness_dir}")
    print(f"Console Output Log: {console_log_path}")

    try:
        with open(console_log_path, "wb") as log_file:
            child_proc = subprocess.Popen(
                cmd,
                cwd=str(ws_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # Safe Stream Reading with Failure Protection
            try:
                if child_proc.stdout is not None:
                    for line in iter(child_proc.stdout.readline, b""):
                        if cfg.get("simulate_stream_failure", False):
                            raise RuntimeError("Simulated console stream reading failure")
                        log_file.write(line)
                        log_file.flush()
                        try:
                            sys.stdout.buffer.write(line)
                            sys.stdout.buffer.flush()
                        except Exception:
                            pass
            except Exception as stream_err:
                failure_reasons.append(f"Console stream reading failed: {stream_err}")
                if child_proc.poll() is None:
                    try:
                        child_proc.kill()
                        child_proc.wait()
                    except Exception:
                        pass
            finally:
                if child_proc.stdout is not None:
                    try:
                        child_proc.stdout.close()
                    except Exception:
                        pass

            child_return_code = child_proc.wait()

        if child_return_code != 0:
            failure_reasons.append(f"Child process exited with non-zero exit code: {child_return_code}")

        # ----------------------------------------------------------------------
        # Discover and Validate Child Report (Codex W3, Claude #1)
        # ----------------------------------------------------------------------
        post_runs: Set[Path] = {p.resolve() for p in runs_base_dir.glob("run_*") if p.is_dir()}
        new_child_runs = sorted(list(post_runs - pre_existing_runs))

        if len(new_child_runs) == 0:
            failure_reasons.append("ZERO_CHILD_RUN_DIRECTORIES_DISCOVERED")
        elif len(new_child_runs) > 1:
            names = [d.name for d in new_child_runs]
            failure_reasons.append(f"MULTIPLE_CHILD_RUN_DIRECTORIES_DISCOVERED: {names}")
        else:
            discovered_child_dir = new_child_runs[0]
            report_candidates = list(discovered_child_dir.glob("contemporary_distance_diagnostic_*.json"))
            if not report_candidates:
                report_candidates = list(discovered_child_dir.glob("*.json"))

            if len(report_candidates) == 0:
                failure_reasons.append(f"ZERO_REPORTS_IN_CHILD_DIRECTORY: {discovered_child_dir.name}")
            elif len(report_candidates) > 1:
                rnames = [r.name for r in report_candidates]
                failure_reasons.append(f"MULTIPLE_REPORTS_IN_CHILD_DIRECTORY: {rnames}")
            else:
                discovered_report_file = report_candidates[0]
                b350_in_path = additional_assets.get("terra_350_benchmark.json", {}).get("path")
                b175_in_path = additional_assets.get("terra_175_benchmark.json", {}).get("path")
                rep_valid, rep_errs, parsed_rep = validate_child_report(
                    report_path=discovered_report_file,
                    expected_child_dir=discovered_child_dir,
                    expected_diag_sha=diag_sha,
                    enforced_offline_condition=enforced_offline_condition,
                    benchmark_350_path=b350_in_path,
                    benchmark_175_path=b175_in_path
                )
                if not rep_valid:
                    for r_err in rep_errs:
                        failure_reasons.append(f"REPORT_VALIDATION_ERROR: {r_err}")
                else:
                    discovered_report_data = parsed_rep

    except Exception as exec_err:
        failure_reasons.append(f"Subprocess execution crashed: {exec_err}")

    finally:
        # Guarantee child termination if still running
        if child_proc is not None and child_proc.poll() is None:
            try:
                child_proc.kill()
                child_proc.wait()
            except Exception:
                pass
            failure_reasons.append("Child process was still active in finally; terminated forcefully.")

        end_time_monotonic = time.monotonic()
        end_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        elapsed_seconds = end_time_monotonic - start_time_monotonic

        # ----------------------------------------------------------------------
        # Complete Post-Run Invariant Re-Hashing (Codex W2, Claude #3)
        # ----------------------------------------------------------------------
        post_invariants: Dict[str, Any] = {}
        post_hash_passed = True

        # Check snapshot manifest integrity on disk against frozen hash
        try:
            if not snapshot_manifest_path.exists():
                post_hash_passed = False
                failure_reasons.append("SNAPSHOT_MANIFEST_DELETED_POST_RUN")
            else:
                post_snap_sha = file_sha256(snapshot_manifest_path)
                if post_snap_sha.lower() != frozen_manifest_sha.lower():
                    post_hash_passed = False
                    failure_reasons.append(f"SNAPSHOT_MANIFEST_MUTATED_POST_RUN: {post_snap_sha} != {frozen_manifest_sha}")
        except Exception as snap_h_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to verify snapshot manifest hash post-run: {snap_h_err}")

        # Re-hash original store files against frozen in-memory manifest (includes extras check)
        frozen_store_files = frozen_manifest_data.get("vector_store_manifest", {})
        try:
            current_post_manifest = dir_manifest(store_dir)
            if len(current_post_manifest) != len(frozen_store_files):
                post_hash_passed = False
                failure_reasons.append(
                    f"Store file count drift post-run: {len(current_post_manifest)} != {len(frozen_store_files)}"
                )

            store_post_hashes = {}
            for rel_path, exp_info in frozen_store_files.items():
                if rel_path not in current_post_manifest:
                    post_hash_passed = False
                    store_post_hashes[rel_path] = {"status": "MISSING"}
                    failure_reasons.append(f"Store file missing post-run: {rel_path}")
                else:
                    act_sha = current_post_manifest[rel_path]["sha256"]
                    match = (act_sha.lower() == exp_info["sha256"].lower())
                    if not match:
                        post_hash_passed = False
                        failure_reasons.append(f"Store file {rel_path} SHA256 mismatch post-run: {act_sha} != {exp_info['sha256']}")
                    store_post_hashes[rel_path] = {"sha256": act_sha, "match": match}

            for rel_path in current_post_manifest:
                if rel_path not in frozen_store_files:
                    post_hash_passed = False
                    failure_reasons.append(f"Unexpected extra store file post-run: {rel_path}")

            post_invariants["vector_store_files"] = store_post_hashes
        except Exception as store_inv_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to inventory store files post-run: {store_inv_err}")

        # Re-hash preserved snapshot copy directory itself
        try:
            snap_store_dir = snapshot_dir / "vector_db_20k"
            if not snap_store_dir.exists():
                post_hash_passed = False
                failure_reasons.append("Preserved snapshot copy directory missing post-run")
            else:
                snap_post_manifest = dir_manifest(snap_store_dir)
                if snap_post_manifest != frozen_store_files:
                    post_hash_passed = False
                    failure_reasons.append("Preserved snapshot copy mutated post-run")
        except Exception as snap_dir_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to check preserved snapshot directory post-run: {snap_dir_err}")

        # Re-hash preserved snapshot copies of the 4 additional assets in snapshot_dir (Codex-0025, Claude-0084)
        frozen_additional_assets = frozen_manifest_data.get("additional_assets", {})
        snap_assets_post_hashes = {}
        for aname, aexp in frozen_additional_assets.items():
            snap_copy_path = snapshot_dir / aname
            try:
                if not snap_copy_path.exists():
                    post_hash_passed = False
                    snap_assets_post_hashes[aname] = {"status": "MISSING"}
                    failure_reasons.append(f"Preserved snapshot asset copy missing post-run: {aname}")
                else:
                    act_sha = file_sha256(snap_copy_path)
                    match = (act_sha.lower() == aexp["sha256"].lower())
                    if not match:
                        post_hash_passed = False
                        failure_reasons.append(
                            f"Preserved snapshot asset copy {aname} SHA256 mismatch post-run: {act_sha} != {aexp['sha256']}"
                        )
                    snap_assets_post_hashes[aname] = {"sha256": act_sha, "match": match}
            except Exception as snap_a_err:
                post_hash_passed = False
                failure_reasons.append(f"Failed to hash preserved snapshot asset copy {aname} post-run: {snap_a_err}")
        post_invariants["snapshot_additional_assets"] = snap_assets_post_hashes

        # Re-hash live additional assets in workspace
        assets_post_hashes = {}
        for aname, ainfo in additional_assets.items():
            apath = ainfo["path"]
            try:
                if not apath.exists():
                    post_hash_passed = False
                    assets_post_hashes[aname] = {"status": "MISSING"}
                    failure_reasons.append(f"Additional asset missing post-run: {aname}")
                else:
                    act_sha = file_sha256(apath)
                    match = (act_sha.lower() == ainfo["expected_sha256"].lower())
                    if not match:
                        post_hash_passed = False
                        failure_reasons.append(f"Additional asset {aname} SHA256 mismatch post-run: {act_sha} != {ainfo['expected_sha256']}")
                    assets_post_hashes[aname] = {"sha256": act_sha, "match": match}
            except Exception as asset_err:
                post_hash_passed = False
                failure_reasons.append(f"Failed to hash additional asset {aname} post-run: {asset_err}")
        post_invariants["additional_assets"] = assets_post_hashes

        # Re-hash diagnostic script, interpreter, ONNX cache
        try:
            diag_post_sha = file_sha256(diag_script) if diag_script.exists() else "MISSING"
            diag_post_match = (diag_post_sha.lower() == diag_sha.lower())
            if not diag_post_match:
                post_hash_passed = False
                failure_reasons.append(f"Diagnostic script SHA256 mismatch post-run: {diag_post_sha} != {diag_sha}")
            post_invariants["diagnostic_script"] = {"sha256": diag_post_sha, "match": diag_post_match}
        except Exception as d_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to hash diagnostic script post-run: {d_err}")

        try:
            py_post_sha = file_sha256(py_exe) if py_exe.exists() else "MISSING"
            py_post_match = (py_post_sha.lower() == py_sha.lower())
            if not py_post_match:
                post_hash_passed = False
                failure_reasons.append(f"Python interpreter SHA256 mismatch post-run: {py_post_sha} != {py_sha}")
            post_invariants["python_executable"] = {"sha256": py_post_sha, "match": py_post_match}
        except Exception as p_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to hash Python interpreter post-run: {p_err}")

        onnx_post_hashes = {}
        try:
            if cache_dir.exists():
                for fname, exp_info in onnx_manifest.items():
                    fpath = cache_dir / fname
                    if not fpath.exists():
                        post_hash_passed = False
                        onnx_post_hashes[fname] = {"status": "MISSING"}
                        failure_reasons.append(f"ONNX cache asset missing post-run: {fname}")
                    else:
                        act_sha = file_sha256(fpath)
                        match = (act_sha.lower() == exp_info["sha256"].lower())
                        if not match:
                            post_hash_passed = False
                            failure_reasons.append(f"ONNX asset {fname} SHA256 mismatch post-run: {act_sha} != {exp_info['sha256']}")
                        onnx_post_hashes[fname] = {"sha256": act_sha, "match": match}
            else:
                post_hash_passed = False
                failure_reasons.append("ONNX cache directory missing post-run")
        except Exception as onnx_err:
            post_hash_passed = False
            failure_reasons.append(f"Failed to hash ONNX cache post-run: {onnx_err}")
        post_invariants["onnx_cache"] = onnx_post_hashes

        if not post_hash_passed:
            failure_reasons.append("POST_RUN_INVARIANT_HASH_MISMATCH")

        # ----------------------------------------------------------------------
        # Safe Hash Reads for Produced Evidence
        # ----------------------------------------------------------------------
        log_sha = None
        try:
            if console_log_path.exists():
                log_sha = file_sha256(console_log_path)
            else:
                failure_reasons.append("Console output log does not exist post-run")
        except Exception as log_h_err:
            failure_reasons.append(f"Failed to hash console output log: {log_h_err}")

        report_sha = None
        try:
            if discovered_report_file and discovered_report_file.exists():
                report_sha = file_sha256(discovered_report_file)
        except Exception as rep_h_err:
            failure_reasons.append(f"Failed to hash discovered report file: {rep_h_err}")

        # ----------------------------------------------------------------------
        # Fail-Closed Evidence Writing (Codex W1, Claude #2)
        # ----------------------------------------------------------------------
        # Determine provisional exit code
        if child_return_code == 0 and len(failure_reasons) == 0 and post_hash_passed:
            wrapper_exit_code = 0
        else:
            wrapper_exit_code = 1

        # 1. Write exit_code.txt
        if cfg.get("simulate_exit_code_write_failure", False):
            exit_w_err = RuntimeError("Simulated exit code write failure")
            failure_reasons.append(f"Failed to write exit_code.txt: {exit_w_err}")
            wrapper_exit_code = 1
        else:
            try:
                with open(exit_code_path, "w", encoding="utf-8") as f_exit:
                    f_exit.write(f"{wrapper_exit_code}\n")
            except Exception as exit_w_err:
                failure_reasons.append(f"Failed to write exit_code.txt: {exit_w_err}")
                wrapper_exit_code = 1

        # 2. Write execution_metadata.json (Exclusive 'x' mode)
        exec_metadata = {
            "harness_run_id": harness_run_id,
            "child_run_id": discovered_child_dir.name.replace("run_", "") if discovered_child_dir else None,
            "start_time_utc": start_time_utc,
            "end_time_utc": end_time_utc,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "child_return_code": child_return_code,
            "wrapper_exit_code": wrapper_exit_code,
            "success": (wrapper_exit_code == 0 and len(failure_reasons) == 0),
            "failure_reasons": list(failure_reasons),
            "enforced_offline_condition": enforced_offline_condition,
            "offline_enforcement_caveat": (
                "Recording an offline declaration certifies declared runtime configuration "
                "but does not establish or prove external network firewall enforcement."
            ),
            "harness_config_supplied": (harness_config is not None),
            "harness_config_is_none": (harness_config is None),
            "command_invoked": cmd,
            "pre_launch_facts": pin_facts,
            "benchmark_schema_validation": bench_schema_facts,
            "artifacts_produced": {
                "harness_directory": str(harness_dir),
                "console_output_log": str(console_log_path),
                "console_output_sha256": log_sha,
                "exit_code_file": str(exit_code_path),
                "metadata_file": str(metadata_path),
                "discovered_child_dir": str(discovered_child_dir) if discovered_child_dir else None,
                "discovered_report_file": str(discovered_report_file) if discovered_report_file else None,
                "discovered_report_sha256": report_sha
            },
            "post_run_invariants": {
                "all_invariants_passed": post_hash_passed,
                "details": post_invariants
            }
        }

        if cfg.get("simulate_metadata_write_failure", False):
            meta_w_err = RuntimeError("Simulated metadata write failure")
            failure_reasons.append(f"Failed to write execution_metadata.json: {meta_w_err}")
            wrapper_exit_code = 1
            terminal_record = {
                "terminal_event": "METADATA_WRITE_FAILURE",
                "wrapper_exit_code": 1,
                "child_return_code": child_return_code,
                "failure_reasons": failure_reasons
            }
            try:
                print(
                    f"CRITICAL: Primary metadata write failed: {meta_w_err}. Terminal record:\n{json.dumps(terminal_record, indent=2)}",
                    file=sys.stderr
                )
            except Exception:
                pass
        else:
            try:
                with open(metadata_path, "x", encoding="utf-8") as f_meta:
                    json.dump(exec_metadata, f_meta, indent=2)
            except Exception as meta_w_err:
                failure_reasons.append(f"Failed to write execution_metadata.json: {meta_w_err}")
                wrapper_exit_code = 1
                terminal_record = {
                    "terminal_event": "METADATA_WRITE_FAILURE",
                    "wrapper_exit_code": 1,
                    "child_return_code": child_return_code,
                    "failure_reasons": failure_reasons
                }
                try:
                    print(
                        f"CRITICAL: Primary metadata write failed: {meta_w_err}. Terminal record:\n{json.dumps(terminal_record, indent=2)}",
                        file=sys.stderr
                    )
                except Exception:
                    pass

        # Update exit_code.txt if overridden to 1 by evidence write failures
        if wrapper_exit_code != 0:
            try:
                with open(exit_code_path, "w", encoding="utf-8") as f_exit:
                    f_exit.write(f"{wrapper_exit_code}\n")
            except Exception:
                pass

        try:
            print("\n" + "=" * 80)
            print(f"DIAGNOSTIC HARNESS EXECUTION COMPLETE: Wrapper Exit Code {wrapper_exit_code} (Child: {child_return_code})")
            print(f"Elapsed: {elapsed_seconds:.2f}s")
            print(f"Console Output Log: {console_log_path}")
            print(f"Execution Metadata: {metadata_path}")
            print(f"Single-Run Lock: {lock_path}")
            if failure_reasons:
                print("FAILURE REASONS RECORDED:")
                for reason in failure_reasons:
                    print(f"  - {reason}")
            print(f"Original Asset Status: {'100% BIT-IDENTICAL' if post_hash_passed else 'INVARIANT VIOLATION'}")
            print("=" * 80)
        except Exception:
            pass

    return wrapper_exit_code


def main():
    parser = argparse.ArgumentParser(description="TERRA Hardened Diagnostic Execution Harness")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create-snapshot", action="store_true", help="Execute Pre-Run Snapshot Creation and Verification")
    group.add_argument("--execute-diagnostic", action="store_true", help="Execute Single Pinned Production Diagnostic")
    parser.add_argument("--enforced-offline-condition", type=str, default="", help="Declared Layer 1 external offline condition")
    args = parser.parse_args()

    if args.create_snapshot:
        code = action_create_snapshot()
        sys.exit(code)
    elif args.execute_diagnostic:
        code = action_execute_diagnostic(args.enforced_offline_condition)
        sys.exit(code)


if __name__ == "__main__":
    main()
