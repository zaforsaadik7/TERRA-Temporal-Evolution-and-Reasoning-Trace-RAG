#!/usr/bin/env python3
"""
scripts/audit_i1a_contemporary_gate_calibration.py
=================================================
PROPOSAL REVISED SCRIPT FOR CODEX-0015 / CLAUDE-0071 AUDIT.
DO NOT RUN WITHOUT EXPLICIT USER AUTHORIZATION.

Offline, isolated contemporary diagnostic of nearest-neighbor Chroma distances
across terra_350_benchmark.json and legacy terra_175_benchmark.json cohorts
against a disposable, hash-verified snapshot copy of dataset_20k_cap/vector_db_20k.

Audit & Security Hardening (Codex-0015):
1. Pre-resolution reparse point and symlink validation across all raw parent directories.
2. Verified binding of the installed Chroma embedding function (ONNXMiniLM_L6_V2) to the validated cache directory.
3. Unified result validator for both Benchmark 350 and Legacy 40 queries (allow_nan=False, finiteness, non-empty IDs).
4. Strict numerical policy: material negative distances (< -1e-6) abort; tiny negative distances ([-1e-6, 0.0))
   are preserved raw, flagged, and clamped only for derived sqrt.
5. Granular concordance classification distinguishing AUROC drift from threshold count discrepancies with exact deltas.
6. Fail-closed report serialization: exclusive creation ('x'), read-back verification, and terminal stderr fallback;
   any report failure forces status="FAILED" and exit code 1.
7. Verified single lifecycle runner with mockable dependency injection for comprehensive test coverage.
"""

import os
import sys
import json
import time
import uuid
import stat
import math
import shutil
import hashlib
import sqlite3
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import numpy as np

# ------------------------------------------------------------------------------
# Custom Exception Hierarchy (Guarantees Fail-Closed Operation under python -O)
# ------------------------------------------------------------------------------
class AuditSecurityError(RuntimeError):
    """Raised when security boundaries (network, paths, permissions, reparse points) are violated."""
    pass

class AuditValidationError(ValueError):
    """Raised when data schemas, cohort counts, or numerical bounds fail validation."""
    pass

class AuditIntegrityError(RuntimeError):
    """Raised when file checksums or database manifests differ from expected states."""
    pass

class AuditExecutionError(RuntimeError):
    """Raised when runtime execution, Chroma client operations, or report writes fail."""
    pass

# ------------------------------------------------------------------------------
# 1. Enforceable Fail-Closed Network Security & Telemetry Suppression
# ------------------------------------------------------------------------------
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import socket
import urllib.request

def _blocked_network_call(*args, **kwargs):
    raise AuditSecurityError("ENFORCEABLE SECURITY GUARD: Outbound network call is strictly prohibited during offline audit.")

# Monkey-patch standard socket entrypoints
socket.socket.connect = _blocked_network_call
socket.socket.connect_ex = _blocked_network_call
socket.socket.sendto = _blocked_network_call
socket.create_connection = _blocked_network_call
socket.getaddrinfo = _blocked_network_call
urllib.request.urlopen = _blocked_network_call

# Monkey-patch httpx if installed (used by Chroma ONNX downloader)
try:
    import httpx
    httpx.Client.send = _blocked_network_call
    httpx.AsyncClient.send = _blocked_network_call
    httpx.get = _blocked_network_call
    httpx.post = _blocked_network_call
    httpx.stream = _blocked_network_call
    httpx.request = _blocked_network_call
except ImportError:
    pass

def run_negative_control_network_test():
    """
    Verifies that outbound connection attempts fail closed with AuditSecurityError.
    Closes any allocated sockets cleanly in finally blocks.
    """
    # Test 1: Socket connect
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s1.connect(("127.0.0.1", 9999))
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket connect was not blocked!")
    except AuditSecurityError:
        pass
    finally:
        s1.close()

    # Test 2: Socket connect_ex
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s2.connect_ex(("127.0.0.1", 9999))
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket connect_ex was not blocked!")
    except AuditSecurityError:
        pass
    finally:
        s2.close()

    # Test 3: Socket create_connection
    try:
        socket.create_connection(("127.0.0.1", 9999), timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket create_connection was not blocked!")
    except AuditSecurityError:
        pass

    # Test 4: Socket getaddrinfo
    try:
        socket.getaddrinfo("localhost", 9999)
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket getaddrinfo was not blocked!")
    except AuditSecurityError:
        pass

    # Test 5: UDP datagram sendto
    s_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s_udp.sendto(b"test", ("127.0.0.1", 9999))
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket sendto was not blocked!")
    except AuditSecurityError:
        pass
    finally:
        s_udp.close()

    # Test 6: urllib request
    try:
        urllib.request.urlopen("http://127.0.0.1:9999", timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: urllib call was not blocked!")
    except AuditSecurityError:
        pass

    # Test 7: httpx request (if httpx is installed)
    try:
        import httpx
        with httpx.Client() as cl:
            cl.get("http://127.0.0.1:9999", timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: httpx GET call was not blocked!")
    except AuditSecurityError:
        pass
    except ImportError:
        pass

# ------------------------------------------------------------------------------
# 2. Approved Immutable Checksums & Manifests
# ------------------------------------------------------------------------------
EXPECTED_BENCHMARK_350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
EXPECTED_BENCHMARK_175_SHA256 = "8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305"
EXPECTED_SAVED_SUMMARY_SHA256 = "b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f"
REFERENCE_HISTORICAL_AUROC_SCRIPT_SHA256 = "ad6f26e858c79693e13163ccd77446bd77af7af21cb0552b262c68be6b04b5ca"

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
    "tokenizer_config.json": {
        "size": 518,
        "sha256": "7702051bbc4953b94d47fa1d61b42ed4cbb3c71b501a8dd7183a823f8bea1f20"
    },
    "tokenizer.json": {
        "size": 711661,
        "sha256": "da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0"
    },
    "vocab.txt": {
        "size": 231508,
        "sha256": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3"
    }
}

TOLERANCE_TINY_NEGATIVE = -1e-6

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def dir_manifest(path: Path) -> dict:
    manifest = {}
    for p in sorted(path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(path)).replace("\\", "/")
            st = p.stat()
            manifest[rel] = {
                "size": st.st_size,
                "sha256": file_sha256(p),
                "mtime_epoch": st.st_mtime
            }
    return manifest

def validate_safe_unresolved_path(p: Path, name: str):
    """
    Validates that the supplied (unresolved) path and none of its parent components
    are symbolic links or Windows reparse points BEFORE path resolution.
    """
    curr = p
    while curr != curr.parent:
        if os.path.islink(curr):
            raise AuditSecurityError(f"Security violation: {name} component '{curr}' is a symbolic link.")
        if curr.exists():
            st = curr.stat()
            attrs = getattr(st, "st_file_attributes", 0)
            if attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024):
                raise AuditSecurityError(f"Security violation: {name} component '{curr}' is a Windows reparse point.")
        curr = curr.parent

def check_path_isolation(orig: Path, disposable: Path, output_dir: Path, workspace: Path):
    """Enforces strict non-containment across original, disposable, and output directories."""
    orig_res = orig.resolve()
    disp_res = disposable.resolve()
    out_res = output_dir.resolve()
    ws_res = workspace.resolve()

    if disp_res == orig_res:
        raise AuditSecurityError("Disposable path must not equal original path.")
    if orig_res in disp_res.parents:
        raise AuditSecurityError("Disposable path must not reside inside original database directory.")
    if disp_res in orig_res.parents:
        raise AuditSecurityError("Original database must not reside inside disposable directory.")
    if orig_res in out_res.parents:
        raise AuditSecurityError("Output directory must not reside inside original database directory.")
    if out_res in orig_res.parents:
        raise AuditSecurityError("Original database must not reside inside output directory.")
    if ws_res not in disp_res.parents:
        raise AuditSecurityError("Disposable database must reside within workspace root.")
    if ws_res not in out_res.parents:
        raise AuditSecurityError("Output directory must reside within workspace root.")

def compute_auroc(y_true, y_scores):
    """
    Exact Mann-Whitney U pairwise concordance with half-credit ties.
    Algorithmically identical to scripts/compute_budget_and_gate_metrics.py lines 21-33.
    """
    pos = [s for y, s in zip(y_true, y_scores) if y == 1]
    neg = [s for y, s in zip(y_true, y_scores) if y == 0]
    total = len(pos) * len(neg)
    if total == 0:
        raise AuditValidationError("Cannot compute AUROC with zero positive or negative samples.")
    concordant = sum(1 for p in pos for n in neg if p > n)
    tied = sum(1 for p in pos for n in neg if p == n)
    return (concordant + 0.5 * tied) / total

def cohort_stats(arr):
    arr = np.array(arr, dtype=np.float64)
    if len(arr) == 0:
        return {}
    return {
        "n": int(len(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std_sample_ddof1": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "std_population_ddof0": float(np.std(arr, ddof=0)),
        "median": float(np.median(arr)),
        "p95": float(np.percentile(arr, 95, method="linear")),
        "percentile_method": "linear"
    }

def validate_and_transform_result(query_id: str, dist_list: Any, id_list: Any) -> Tuple[float, str, float, str]:
    """
    Unified result validator for both Benchmark 350 and Legacy 40 queries.
    Enforces shape == 1, non-empty ID, finite float, and the agreed numerical policy.
    """
    if not isinstance(dist_list, list) or len(dist_list) != 1:
        raise AuditValidationError(f"Query {query_id} returned {len(dist_list) if isinstance(dist_list, list) else type(dist_list)} distances, expected exactly 1.")
    if not isinstance(id_list, list) or len(id_list) != 1:
        raise AuditValidationError(f"Query {query_id} returned {len(id_list) if isinstance(id_list, list) else type(id_list)} ids, expected exactly 1.")

    nid = id_list[0]
    if not isinstance(nid, str) or len(nid.strip()) == 0:
        raise AuditValidationError(f"Invalid/empty nearest node ID for {query_id}: {repr(nid)}")

    d_val = dist_list[0]
    if not isinstance(d_val, (int, float)) or not np.isfinite(d_val) or math.isnan(d_val) or math.isinf(d_val):
        raise AuditValidationError(f"Non-finite distance for {query_id}: {d_val}")

    d_raw = float(d_val)
    if d_raw < TOLERANCE_TINY_NEGATIVE:
        raise AuditValidationError(f"Materially negative distance detected for {query_id}: {d_raw} < {TOLERANCE_TINY_NEGATIVE}")
    elif TOLERANCE_TINY_NEGATIVE <= d_raw < 0.0:
        anomaly_flag = "tiny_negative_clamped_for_sqrt"
        d_sqrt = 0.0
    else:
        anomaly_flag = "none"
        d_sqrt = float(np.sqrt(d_raw))

    return d_raw, nid, d_sqrt, anomaly_flag

def write_and_verify_report(report_file: Path, state: dict) -> None:
    """
    Serializes report with exclusive creation ('x'), allow_nan=False,
    and performs immediate read-back verification. Any failure raises AuditExecutionError.
    """
    try:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "x", encoding="utf-8") as f_out:
            json.dump(state, f_out, indent=2, allow_nan=False)

        # Immediate read-back verification
        with open(report_file, "r", encoding="utf-8") as f_in:
            parsed = json.load(f_in)
        if parsed.get("run_id") != state.get("run_id"):
            raise AuditExecutionError("Read-back verification failed: run_id mismatch in serialized report.")
    except Exception as exc:
        # Emit terminal failure record to stderr
        terminal_record = {
            "critical_event": "REPORT_SERIALIZATION_FAILED",
            "run_id": state.get("run_id"),
            "target_path": str(report_file),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "state_status": state.get("status")
        }
        print(f"CRITICAL: Failed to write or verify final report:\n{json.dumps(terminal_record, indent=2)}", file=sys.stderr)
        raise AuditExecutionError(f"Report serialization and read-back failed: {exc}") from exc

# ------------------------------------------------------------------------------
# 3. Guarded Execution Lifecycle Runner
# ------------------------------------------------------------------------------
def run_diagnostic_lifecycle(
    workspace_root_arg: Optional[str] = None,
    onnx_cache_dir_arg: Optional[str] = None,
    mock_overrides: Optional[Dict[str, Any]] = None,
    exit_on_complete: bool = True
) -> Tuple[int, Dict[str, Any]]:
    # Initialize timestamp and unique run identifier
    run_timestamp = int(time.time())
    run_uuid = uuid.uuid4().hex[:8]
    run_id = f"{run_timestamp}_{os.getpid()}_{run_uuid}"
    iso_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # Raw paths prior to resolution
    raw_ws_path = Path(workspace_root_arg or ".")
    raw_orig_db = raw_ws_path / "dataset_20k_cap" / "vector_db_20k"
    raw_b350 = raw_ws_path / "terra_350_benchmark.json"
    raw_b175 = raw_ws_path / "terra_175_benchmark.json"
    raw_summary = raw_ws_path / "scratch" / "budget_and_gate_summary.json"
    raw_output_dir = raw_ws_path / "TERRA_EDITORIAL_RESTART_V2" / "reviewer_I0_I1a_20261008" / "addendum_01" / "runs" / f"run_{run_id}"
    raw_report_file = raw_output_dir / f"contemporary_distance_diagnostic_{run_id}.json"
    raw_scratch_dir = raw_ws_path / "scratch" / "diagnostics" / f"run_{run_id}"
    raw_disposable_db = raw_scratch_dir / "vector_db_20k"
    raw_cache_dir = Path(onnx_cache_dir_arg or r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx")

    # State container for single status-bearing report
    workflow_state = {
        "status": "INITIALIZING",
        "run_id": run_id,
        "timestamp_utc": iso_time_utc,
        "script": {
            "path": str(Path(__file__).resolve()),
            "sha256": file_sha256(Path(__file__).resolve())
        },
        "stages_completed": [],
        "errors": [],
        "integrity_checks": {
            "source_db_invariant": False,
            "benchmark_350_invariant": False,
            "benchmark_175_invariant": False,
            "saved_summary_invariant": False,
            "onnx_cache_invariant": False,
            "all_integrity_passed": False
        },
        "metadata": {},
        "concordance": {},
        "distribution_summary_benchmark_350": {},
        "calibration_grid_benchmark_350": {},
        "legacy_sample20_diagnostic": {},
        "verification_manifests": {},
        "query_ledger_350": [],
        "legacy_sample20_query_ledger": []
    }

    orig_pre_manifest = {}
    onnx_pre_manifest = {}
    copied_manifest = {}

    try:
        print("=" * 80)
        print(f"CONTEMPORARY VECTOR DISTANCE DIAGNOSTIC (RUN ID: {run_id})")
        print("Status: Offline, Isolated, Disposable Snapshot Execution")
        print("=" * 80)

        # Stage 1: Enforceable Network Negative Control
        print("\n[Stage 1] Executing fail-closed network negative controls...")
        run_negative_control_network_test()
        workflow_state["stages_completed"].append("stage_1_network_negative_control")
        print("  PASS: Outbound network calls strictly blocked and verified.")

        # Stage 2: Pre-Resolution Reparse Point & Symlink Validation, then Path Isolation
        print("\n[Stage 2] Pre-resolution reparse point and symlink validation across parent trees...")
        validate_safe_unresolved_path(raw_ws_path, "workspace_root")
        validate_safe_unresolved_path(raw_orig_db, "orig_db_dir")
        validate_safe_unresolved_path(raw_scratch_dir, "disposable_scratch_dir")
        validate_safe_unresolved_path(raw_output_dir, "output_dir")
        validate_safe_unresolved_path(raw_cache_dir, "onnx_cache_dir")

        workspace_root = raw_ws_path.resolve()
        orig_db_dir = raw_orig_db.resolve()
        disposable_scratch_dir = raw_scratch_dir.resolve()
        disposable_db_dir = raw_disposable_db.resolve()
        output_dir = raw_output_dir.resolve()
        report_file = raw_report_file.resolve()
        cache_dir_path = raw_cache_dir.resolve()
        benchmark_350_path = raw_b350.resolve()
        benchmark_175_path = raw_b175.resolve()
        saved_summary_path = raw_summary.resolve()

        check_path_isolation(orig_db_dir, disposable_db_dir, output_dir, workspace_root)
        workflow_state["stages_completed"].append("stage_2_path_isolation_verified")
        print("  PASS: Pre-resolution reparse checks and post-resolution isolation confirmed.")

        # Stage 3: Preflight Verification of Approved Immutable Assets
        print("\n[Stage 3] Preflight verification of benchmarks and ONNX cache manifest...")
        if not benchmark_350_path.exists():
            raise AuditValidationError(f"Missing Benchmark 350: {benchmark_350_path}")
        b350_sha = file_sha256(benchmark_350_path)
        if b350_sha != EXPECTED_BENCHMARK_350_SHA256:
            raise AuditIntegrityError(f"Benchmark 350 SHA256 mismatch: {b350_sha} != {EXPECTED_BENCHMARK_350_SHA256}")

        if not benchmark_175_path.exists():
            raise AuditValidationError(f"Missing Benchmark 175: {benchmark_175_path}")
        b175_sha = file_sha256(benchmark_175_path)
        if b175_sha != EXPECTED_BENCHMARK_175_SHA256:
            raise AuditIntegrityError(f"Benchmark 175 SHA256 mismatch: {b175_sha} != {EXPECTED_BENCHMARK_175_SHA256}")

        if not saved_summary_path.exists():
            raise AuditValidationError(f"Missing Saved Summary: {saved_summary_path}")
        summary_sha = file_sha256(saved_summary_path)
        if summary_sha != EXPECTED_SAVED_SUMMARY_SHA256:
            raise AuditIntegrityError(f"Saved summary SHA256 mismatch: {summary_sha} != {EXPECTED_SAVED_SUMMARY_SHA256}")

        # Strict check against APPROVED_ONNX_CACHE_MANIFEST (both size AND SHA256)
        for fname, expected in APPROVED_ONNX_CACHE_MANIFEST.items():
            fpath = cache_dir_path / fname
            if not fpath.exists():
                raise AuditValidationError(f"Missing required ONNX cache file: {fpath}")
            act_size = fpath.stat().st_size
            if act_size != expected["size"]:
                raise AuditIntegrityError(f"ONNX asset {fname} size mismatch: {act_size} != {expected['size']}")
            act_sha = file_sha256(fpath)
            if act_sha != expected["sha256"]:
                raise AuditIntegrityError(f"ONNX asset {fname} SHA256 mismatch: {act_sha} != {expected['sha256']}")
            onnx_pre_manifest[fname] = {"size": act_size, "sha256": act_sha}

        # Dynamic check of historical AUROC reference script
        hist_script_path = workspace_root / "scripts" / "compute_budget_and_gate_metrics.py"
        hist_measured_sha = file_sha256(hist_script_path) if hist_script_path.exists() else "file_missing"

        workflow_state["stages_completed"].append("stage_3_preflight_assets_verified")
        print("  PASS: Benchmark 350, Benchmark 175, Saved Summary, and all 6 ONNX cache assets verified.")

        # Stage 4: Quiescent Source DB Manifest and Snapshot Copy
        print("\n[Stage 4] Verifying source DB quiescence and creating isolated snapshot...")
        if not orig_db_dir.exists():
            raise AuditValidationError(f"Missing original database directory: {orig_db_dir}")

        wal_file = orig_db_dir / "chroma.sqlite3-wal"
        shm_file = orig_db_dir / "chroma.sqlite3-shm"
        quiescence_info = {
            "wal_present": wal_file.exists(),
            "shm_present": shm_file.exists(),
            "quiescence_check_epoch": time.time()
        }

        orig_pre_manifest = dir_manifest(orig_db_dir)
        if len(orig_pre_manifest) == 0:
            raise AuditValidationError(f"Original database directory is empty: {orig_db_dir}")

        disposable_scratch_dir.mkdir(parents=True, exist_ok=False)

        # Support mock copy injection for unit testing
        if mock_overrides and "mock_db_copier" in mock_overrides:
            mock_overrides["mock_db_copier"](orig_db_dir, disposable_db_dir)
        else:
            shutil.copytree(orig_db_dir, disposable_db_dir)

        copied_manifest = dir_manifest(disposable_db_dir)
        orig_after_copy_manifest = dir_manifest(orig_db_dir)

        if copied_manifest != orig_pre_manifest:
            raise AuditIntegrityError("Copied database manifest does not match original pre-copy manifest.")
        if orig_after_copy_manifest != orig_pre_manifest:
            raise AuditIntegrityError("Original database files changed during copy operation!")

        workflow_state["stages_completed"].append("stage_4_snapshot_copied_and_verified")
        print(f"  PASS: Disposable snapshot created at {disposable_db_dir} with 3-way manifest parity.")

        # Stage 5: Schema Extraction Before Client Connection
        print("\n[Stage 5] Extracting active SQLite schema before Chroma connection...")
        sqlite_disposable = disposable_db_dir / "chroma.sqlite3"
        conn_pre = sqlite3.connect(str(sqlite_disposable))
        c_pre = conn_pre.cursor()
        c_pre.execute("SELECT id, name, dimension, schema_str FROM collections WHERE name = 'thinking_traces'")
        coll_row_pre = c_pre.fetchone()
        if not coll_row_pre:
            conn_pre.close()
            raise AuditValidationError("Collection 'thinking_traces' not found in disposable sqlite3 table.")
        coll_id, coll_name, coll_dim, schema_str_pre = coll_row_pre
        conn_pre.close()

        parsed_schema_pre = json.loads(schema_str_pre) if schema_str_pre else {}
        embedding_key_cfg = parsed_schema_pre.get("keys", {}).get("#embedding", {}).get("float_list", {}).get("vector_index", {}).get("config", {})
        active_space = embedding_key_cfg.get("space")
        active_hnsw = embedding_key_cfg.get("hnsw", {})

        if active_space != "l2":
            raise AuditValidationError(f"Active space is '{active_space}', expected 'l2' (squared Euclidean).")

        workflow_state["stages_completed"].append("stage_5_pre_schema_extracted")
        print(f"  PASS: Active space confirmed as '{active_space}' (squared Euclidean).")

        # Stage 6: Cohort Definitions Validation Before Expensive Invocations
        print("\n[Stage 6] Validating cohort definitions across benchmarks...")
        with open(benchmark_350_path, "r", encoding="utf-8") as f:
            bench_350 = json.load(f)
        if len(bench_350) != 350:
            raise AuditValidationError(f"Benchmark 350 query count is {len(bench_350)}, expected 350.")

        qids_350 = [q["query_id"] for q in bench_350]
        if len(set(qids_350)) != 350:
            raise AuditValidationError("Duplicate query IDs detected in Benchmark 350.")

        cat_a_qids = [q["query_id"] for q in bench_350 if q["category"] == "A_Factual"]
        cat_b_qids = [q["query_id"] for q in bench_350 if q["category"] == "B_Evolutionary"]
        ood_qids = [q["query_id"] for q in bench_350 if q["category"] == "C_OutOfContext"]
        adv_qids = [q["query_id"] for q in bench_350 if q["category"] == "D_Adversarial"]

        if len(cat_a_qids) != 100:
            raise AuditValidationError(f"Category A count is {len(cat_a_qids)}, expected 100.")
        if len(cat_b_qids) != 100:
            raise AuditValidationError(f"Category B count is {len(cat_b_qids)}, expected 100.")
        if len(ood_qids) != 75:
            raise AuditValidationError(f"Category C (OOD) count is {len(ood_qids)}, expected 75.")
        if len(adv_qids) != 75:
            raise AuditValidationError(f"Category D (Adversarial) count is {len(adv_qids)}, expected 75.")

        in_domain_qids = cat_a_qids + cat_b_qids
        if len(in_domain_qids) != 200:
            raise AuditValidationError(f"In-domain count is {len(in_domain_qids)}, expected 200.")

        # Benchmark 175 cohort validation
        with open(benchmark_175_path, "r", encoding="utf-8") as f:
            bench_175 = json.load(f)
        sample_in_175 = [q for q in bench_175 if q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
        sample_out_175 = [q for q in bench_175 if q.get("category") == "C_OutOfContext"][:20]

        if len(sample_in_175) != 20:
            raise AuditValidationError(f"Legacy sample_in_20 count is {len(sample_in_175)}, expected 20.")
        if len(sample_out_175) != 20:
            raise AuditValidationError(f"Legacy sample_out_20 count is {len(sample_out_175)}, expected 20.")

        workflow_state["stages_completed"].append("stage_6_cohorts_validated")
        print("  PASS: All Benchmark 350 and Benchmark 175 cohort definitions validated.")

        # Stage 7: Verified Cache Binding & Query Benchmark 350
        print("\n[Stage 7] Verifying embedding function cache binding and querying Benchmark 350...")
        import chromadb
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        ef_instance = ONNXMiniLM_L6_V2()
        resolved_ef_dir = (Path(ef_instance.DOWNLOAD_PATH) / ef_instance.EXTRACTED_FOLDER_NAME).resolve()
        if resolved_ef_dir != cache_dir_path:
            raise AuditSecurityError(
                f"Embedding function cache path mismatch: '{resolved_ef_dir}' != validated cache path '{cache_dir_path}'"
            )

        client = chromadb.PersistentClient(path=str(disposable_db_dir))
        coll = client.get_collection(name="thinking_traces")
        ef_name = coll._embedding_function.name() if hasattr(coll._embedding_function, "name") else ""
        if ef_name != "default" and not isinstance(coll._embedding_function, ONNXMiniLM_L6_V2):
            raise AuditSecurityError(f"Unexpected collection embedding function: {coll._embedding_function}")
        doc_count = coll.count()
        if doc_count != 20000:
            raise AuditValidationError(f"Unexpected collection document count: {doc_count}, expected 20,000.")

        texts_350 = [q["query"] for q in bench_350]

        if mock_overrides and "mock_query_fn_350" in mock_overrides:
            chroma_res_350 = mock_overrides["mock_query_fn_350"](texts_350)
        else:
            chroma_res_350 = coll.query(query_texts=texts_350, n_results=1)

        if not isinstance(chroma_res_350.get("distances"), list) or len(chroma_res_350["distances"]) != 350:
            raise AuditValidationError("Mismatch in Benchmark 350 returned distances list length.")
        if not isinstance(chroma_res_350.get("ids"), list) or len(chroma_res_350["ids"]) != 350:
            raise AuditValidationError("Mismatch in Benchmark 350 returned ids list length.")

        # Process Benchmark 350 queries under strict unified validator
        query_records_350 = []
        dists_by_qid = {}
        for i, q in enumerate(bench_350):
            qid = q["query_id"]
            if qid in dists_by_qid:
                raise AuditValidationError(f"Duplicate query ID during processing: {qid}")

            d_raw, nid, d_sqrt, anomaly_flag = validate_and_transform_result(
                qid, chroma_res_350["distances"][i], chroma_res_350["ids"][i]
            )

            dists_by_qid[qid] = d_raw
            query_records_350.append({
                "query_id": qid,
                "category": q["category"],
                "subtype": q.get("subtype", ""),
                "query": q["query"],
                "query_sha256": hashlib.sha256(q["query"].encode("utf-8")).hexdigest(),
                "nearest_node_id": nid,
                "raw_l2_squared_distance": d_raw,
                "euclidean_distance_sqrt": d_sqrt,
                "anomaly_flag": anomaly_flag
            })

        workflow_state["query_ledger_350"] = query_records_350
        workflow_state["stages_completed"].append("stage_7_benchmark_350_queried")
        print("  PASS: Embedding function bound to verified cache; Benchmark 350 evaluated.")

        # Stage 8: Query Legacy Benchmark 175 Cohorts (sample20) with Shared Validator
        print("\n[Stage 8] Querying legacy Benchmark 175 cohorts (sample20) with shared validator...")
        texts_350_set = set(texts_350)
        overlap_in = sum(1 for q in sample_in_175 if q["query"] in texts_350_set)
        overlap_out = sum(1 for q in sample_out_175 if q["query"] in texts_350_set)

        if mock_overrides and "mock_query_fn_175" in mock_overrides:
            res_in_175, res_out_175 = mock_overrides["mock_query_fn_175"](sample_in_175, sample_out_175)
        else:
            res_in_175 = coll.query(query_texts=[q["query"] for q in sample_in_175], n_results=1)
            res_out_175 = coll.query(query_texts=[q["query"] for q in sample_out_175], n_results=1)

        if not isinstance(res_in_175.get("distances"), list) or len(res_in_175["distances"]) != 20:
            raise AuditValidationError("Mismatch in legacy sample_in_20 distances list length.")
        if not isinstance(res_in_175.get("ids"), list) or len(res_in_175["ids"]) != 20:
            raise AuditValidationError("Mismatch in legacy sample_in_20 ids list length.")

        if not isinstance(res_out_175.get("distances"), list) or len(res_out_175["distances"]) != 20:
            raise AuditValidationError("Mismatch in legacy sample_out_20 distances list length.")
        if not isinstance(res_out_175.get("ids"), list) or len(res_out_175["ids"]) != 20:
            raise AuditValidationError("Mismatch in legacy sample_out_20 ids list length.")

        legacy_query_ledger = []
        dists_in_175 = []
        for i, q in enumerate(sample_in_175):
            sid = q.get("query_id", f"sample175_in_{i}")
            d_raw, nid, d_sqrt, anomaly_flag = validate_and_transform_result(
                sid, res_in_175["distances"][i], res_in_175["ids"][i]
            )
            dists_in_175.append(d_raw)
            legacy_query_ledger.append({
                "cohort": "sample_in_20",
                "cohort_index": i,
                "source_query_id": sid,
                "category": q.get("category", ""),
                "query": q["query"],
                "query_sha256": hashlib.sha256(q["query"].encode("utf-8")).hexdigest(),
                "nearest_node_id": nid,
                "raw_l2_squared_distance": d_raw,
                "euclidean_distance_sqrt": d_sqrt,
                "anomaly_flag": anomaly_flag
            })

        dists_out_175 = []
        for i, q in enumerate(sample_out_175):
            sid = q.get("query_id", f"sample175_out_{i}")
            d_raw, nid, d_sqrt, anomaly_flag = validate_and_transform_result(
                sid, res_out_175["distances"][i], res_out_175["ids"][i]
            )
            dists_out_175.append(d_raw)
            legacy_query_ledger.append({
                "cohort": "sample_out_20",
                "cohort_index": i,
                "source_query_id": sid,
                "category": q.get("category", ""),
                "query": q["query"],
                "query_sha256": hashlib.sha256(q["query"].encode("utf-8")).hexdigest(),
                "nearest_node_id": nid,
                "raw_l2_squared_distance": d_raw,
                "euclidean_distance_sqrt": d_sqrt,
                "anomaly_flag": anomaly_flag
            })

        workflow_state["legacy_sample20_query_ledger"] = legacy_query_ledger
        workflow_state["legacy_sample20_diagnostic"] = {
            "metadata_disclaimer": "Contemporary sample20 evaluation on current 20k index. Does NOT reproduce or authenticate historical 10k 0.509 claim provenance.",
            "benchmark_175_sha256": b175_sha,
            "text_overlap_with_benchmark_350": {
                "sample_in_20": f"{overlap_in}/20",
                "sample_out_20": f"{overlap_out}/20"
            },
            "sample_in_20_raw_squared": cohort_stats(dists_in_175),
            "sample_in_20_euclidean_sqrt": cohort_stats([max(0.0, d)**0.5 for d in dists_in_175]),
            "sample_out_20_raw_squared": cohort_stats(dists_out_175),
            "sample_out_20_euclidean_sqrt": cohort_stats([max(0.0, d)**0.5 for d in dists_out_175])
        }
        workflow_state["stages_completed"].append("stage_8_legacy_cohorts_evaluated")
        print("  PASS: Shared validator applied to all 40 legacy queries; ledger constructed.")

        # Stage 9: Evaluate Calibration Concordance & Granular Classification
        print("\n[Stage 9] Evaluating calibration concordance with granular classification...")
        in_dists = [dists_by_qid[qid] for qid in in_domain_qids]
        ood_dists = [dists_by_qid[qid] for qid in ood_qids]
        adv_dists = [dists_by_qid[qid] for qid in adv_qids]

        y_true = [0] * len(in_dists) + [1] * len(ood_dists)
        y_scores = in_dists + ood_dists
        diagnostic_auroc = compute_auroc(y_true, y_scores)
        if not np.isfinite(diagnostic_auroc):
            raise AuditValidationError("Diagnostic AUROC calculation yielded non-finite result.")

        tau_grid = [0.90, 1.00, 1.10, 1.20, 1.25, 1.30, 1.35, 1.40]
        diagnostic_grid = {}
        for tau in tau_grid:
            fp = sum(1 for d in in_dists if d >= tau)
            tp = sum(1 for d in ood_dists if d >= tau)
            fn = len(ood_dists) - tp
            diagnostic_grid[f"{tau:.2f}"] = {
                "tau_raw_squared": tau,
                "n_in": len(in_dists),
                "fp_count": fp,
                "fpr_pct": (fp / len(in_dists)) * 100.0,
                "n_ood": len(ood_dists),
                "tp_count": tp,
                "tpr_pct": (tp / len(ood_dists)) * 100.0,
                "fn_count": fn,
                "fnr_pct": (fn / len(ood_dists)) * 100.0
            }

        workflow_state["distribution_summary_benchmark_350"] = {
            "in_domain_200_raw_squared": cohort_stats(in_dists),
            "in_domain_200_euclidean_sqrt": cohort_stats([max(0.0, d)**0.5 for d in in_dists]),
            "ood_75_raw_squared": cohort_stats(ood_dists),
            "ood_75_euclidean_sqrt": cohort_stats([max(0.0, d)**0.5 for d in ood_dists]),
            "adv_75_raw_squared": cohort_stats(adv_dists),
            "adv_75_euclidean_sqrt": cohort_stats([max(0.0, d)**0.5 for d in adv_dists])
        }
        workflow_state["calibration_grid_benchmark_350"] = diagnostic_grid

        with open(saved_summary_path, "r", encoding="utf-8") as f:
            saved_summary = json.load(f)

        if "gate_calibration" not in saved_summary:
            raise AuditValidationError("Key 'gate_calibration' missing in saved budget_and_gate_summary.json")
        saved_gate = saved_summary["gate_calibration"]

        if "auroc" not in saved_gate or not isinstance(saved_gate["auroc"], (int, float)) or not np.isfinite(saved_gate["auroc"]):
            raise AuditValidationError("Valid finite float 'auroc' missing in saved gate_calibration summary")
        saved_auroc = float(saved_gate["auroc"])

        if "grid" not in saved_gate or not isinstance(saved_gate["grid"], dict):
            raise AuditValidationError("Valid dict 'grid' missing in saved gate_calibration summary")
        saved_grid = saved_gate["grid"]

        grid_mismatches = []
        for k, diag_val in diagnostic_grid.items():
            if k not in saved_grid:
                raise AuditValidationError(f"Threshold '{k}' missing from saved summary grid.")
            s_val = saved_grid[k]
            fp_saved = s_val.get("fp", 0)
            tp_saved = s_val.get("tp", 0)
            fn_saved = s_val.get("fn", 0)

            fp_match = (diag_val["fp_count"] == fp_saved)
            tp_match = (diag_val["tp_count"] == tp_saved)
            fn_match = (diag_val["fn_count"] == fn_saved)

            if not (fp_match and tp_match and fn_match):
                grid_mismatches.append({
                    "threshold": k,
                    "diagnostic": diag_val,
                    "saved": s_val,
                    "deltas": {
                        "fp_delta": diag_val["fp_count"] - fp_saved,
                        "tp_delta": diag_val["tp_count"] - tp_saved,
                        "fn_delta": diag_val["fn_count"] - fn_saved
                    }
                })

        auroc_diff = abs(diagnostic_auroc - saved_auroc)

        # Granular concordance classification
        if auroc_diff <= 1e-6 and len(grid_mismatches) == 0:
            classification = "EXACT_CONCORDANCE"
        elif auroc_diff > 1e-6 and len(grid_mismatches) == 0:
            classification = "AUROC_DRIFT_WITH_IDENTICAL_GRID_COUNTS"
        else:
            classification = f"GRID_COUNT_DISCORDANCE_{len(grid_mismatches)}_THRESHOLDS"

        workflow_state["concordance"] = {
            "diagnostic_auroc": diagnostic_auroc,
            "saved_auroc": saved_auroc,
            "auroc_difference": auroc_diff,
            "grid_mismatch_count": len(grid_mismatches),
            "grid_mismatches": grid_mismatches,
            "concordance_classification": classification,
            "provenance_policy": "No concordance outcome authenticates historical provenance or authorizes manuscript replacement."
        }
        workflow_state["stages_completed"].append("stage_9_concordance_evaluated")
        print(f"  PASS: Concordance evaluated. Classification: {classification} (AUROC Diff: {auroc_diff:.2e})")

        # Stage 10: Check Schema Migration & Finalize Metadata
        print("\n[Stage 10] Checking post-query SQLite schema and finalizing metadata...")
        conn_post = sqlite3.connect(str(sqlite_disposable))
        c_post = conn_post.cursor()
        c_post.execute("SELECT id, name, dimension, schema_str FROM collections WHERE name = 'thinking_traces'")
        coll_row_post = c_post.fetchone()
        conn_post.close()
        schema_str_post = coll_row_post[3] if coll_row_post else ""
        schema_migrated = (schema_str_pre != schema_str_post)

        disposable_post_manifest = dir_manifest(disposable_db_dir)

        ort_ver = "not_available"
        try:
            import onnxruntime
            ort_ver = onnxruntime.__version__
        except Exception:
            pass

        workflow_state["metadata"] = {
            "title": "Contemporary Vector Distance Diagnostic on Preserved Local Index",
            "date": iso_time_utc,
            "runtime_environment": {
                "python_version": sys.version,
                "chromadb_version": chromadb.__version__,
                "numpy_version": np.__version__,
                "onnxruntime_version": ort_ver,
                "approved_onnx_manifest": onnx_pre_manifest
            },
            "active_collection_config": {
                "collection_id": coll_id,
                "collection_name": coll_name,
                "dimension": coll_dim,
                "active_space_metric": active_space,
                "hnsw_config": active_hnsw,
                "search_semantics": "Approximate Nearest Neighbor (ANN) search via HNSWlib; unit-normalization is an architectural expectation of the MiniLM embedding model, not independently measured on stored vectors",
                "schema_migrated_during_query": schema_migrated,
                "pre_connection_schema": parsed_schema_pre,
                "post_query_schema": json.loads(schema_str_post) if schema_str_post else {}
            },
            "source_quiescence_metadata": quiescence_info,
            "historical_auroc_reference": {
                "source_script": "scripts/compute_budget_and_gate_metrics.py",
                "reference_sha256": REFERENCE_HISTORICAL_AUROC_SCRIPT_SHA256,
                "measured_sha256": hist_measured_sha,
                "algorithm": "Mann-Whitney U pairwise concordance with 0.5 ties"
            }
        }
        workflow_state["stages_completed"].append("stage_10_metadata_finalized")

    except Exception as exc:
        print(f"\n[CRITICAL ERROR] Execution failed at stage: {exc}", file=sys.stderr)
        workflow_state["errors"].append({
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        })

    finally:
        # Stage 11: Unconditional Final Integrity Verification of Original Source Assets
        print("\n[Final Stage] Executing unconditional final integrity check on original assets...")
        try:
            orig_post_manifest = dir_manifest(orig_db_dir)
            source_invariant = (orig_post_manifest == orig_pre_manifest) if orig_pre_manifest else False
            workflow_state["integrity_checks"]["source_db_invariant"] = source_invariant

            b350_post_sha = file_sha256(benchmark_350_path) if benchmark_350_path.exists() else None
            b350_invariant = (b350_post_sha == EXPECTED_BENCHMARK_350_SHA256)
            workflow_state["integrity_checks"]["benchmark_350_invariant"] = b350_invariant

            b175_post_sha = file_sha256(benchmark_175_path) if benchmark_175_path.exists() else None
            b175_invariant = (b175_post_sha == EXPECTED_BENCHMARK_175_SHA256)
            workflow_state["integrity_checks"]["benchmark_175_invariant"] = b175_invariant

            summary_post_sha = file_sha256(saved_summary_path) if saved_summary_path.exists() else None
            summary_invariant = (summary_post_sha == EXPECTED_SAVED_SUMMARY_SHA256)
            workflow_state["integrity_checks"]["saved_summary_invariant"] = summary_invariant

            onnx_post_manifest = {}
            onnx_invariant = True
            for fname, exp in APPROVED_ONNX_CACHE_MANIFEST.items():
                fpath = cache_dir_path / fname
                if not fpath.exists():
                    onnx_invariant = False
                    continue
                sha = file_sha256(fpath)
                onnx_post_manifest[fname] = {"size": fpath.stat().st_size, "sha256": sha}
                if sha != exp["sha256"]:
                    onnx_invariant = False
            workflow_state["integrity_checks"]["onnx_cache_invariant"] = onnx_invariant

            all_passed = (source_invariant and b350_invariant and b175_invariant and summary_invariant and onnx_invariant)
            workflow_state["integrity_checks"]["all_integrity_passed"] = all_passed

            workflow_state["verification_manifests"] = {
                "original_vector_db_pre_manifest": orig_pre_manifest,
                "original_vector_db_post_manifest": orig_post_manifest,
                "copied_vector_db_initial_manifest": copied_manifest if 'copied_manifest' in locals() else {},
                "disposable_store_post_manifest": disposable_post_manifest if 'disposable_post_manifest' in locals() else {},
                "disposable_copy_changes_permitted": True,
                "original_store_integrity": "strictly invariant (100% bit-identical)" if source_invariant else "INTEGRITY_VIOLATION",
                "onnx_cache_pre_manifest": onnx_pre_manifest,
                "onnx_cache_post_manifest": onnx_post_manifest,
                "analysis_copy_path": str(disposable_db_dir.relative_to(workspace_root)) if workspace_root in disposable_db_dir.parents else str(disposable_db_dir)
            }

            if not all_passed:
                workflow_state["errors"].append({
                    "error_type": "AuditIntegrityError",
                    "error_message": "CRITICAL INTEGRITY FAILURE: One or more original protected assets mutated during run!"
                })
        except Exception as integrity_exc:
            workflow_state["errors"].append({
                "error_type": "FinalIntegrityCheckError",
                "error_message": str(integrity_exc)
            })

        # Final Status Determination (SUCCESS strictly requires 0 errors and all integrity checks passed)
        if len(workflow_state["errors"]) == 0 and workflow_state["integrity_checks"]["all_integrity_passed"]:
            workflow_state["status"] = "SUCCESS"
        else:
            workflow_state["status"] = "FAILED"

        # Serialize and Read-Back Verify Exactly One Report Artifact
        try:
            if mock_overrides and "mock_report_writer" in mock_overrides:
                mock_overrides["mock_report_writer"](report_file, workflow_state)
            else:
                write_and_verify_report(report_file, workflow_state)
            print(f"\n[Final Report] Report serialized and verified at:\n  {report_file}")
            print(f"Final Outcome Status: {workflow_state['status']}")
        except Exception as write_err:
            workflow_state["status"] = "FAILED"
            workflow_state["errors"].append({
                "error_type": "ReportSerializationError",
                "error_message": str(write_err)
            })
            print(f"CRITICAL REPORT FAILURE: {write_err}", file=sys.stderr)

        print("=" * 80)

    # Clean Exit Control
    if workflow_state["status"] == "SUCCESS" and workflow_state["integrity_checks"]["all_integrity_passed"]:
        print("DIAGNOSTIC WORKFLOW COMPLETE (ZERO ASSETS MUTATED)")
        print("=" * 80)
        if exit_on_complete:
            sys.exit(0)
        return 0, workflow_state
    else:
        status_detail = "ALL ASSETS PRESERVED" if workflow_state["integrity_checks"]["all_integrity_passed"] else "INTEGRITY COMPROMISED OR UNVERIFIED"
        print(f"DIAGNOSTIC WORKFLOW FAILED ({status_detail})")
        print("=" * 80)
        if exit_on_complete:
            sys.exit(1)
        return 1, workflow_state

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contemporary Vector Distance Diagnostic on Preserved Local Assets")
    parser.add_argument("--workspace-root", type=str, default=".", help="Explicit workspace root directory")
    parser.add_argument("--onnx-cache-dir", type=str, default=r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx", help="Path to local ONNX cache directory")
    args = parser.parse_args()

    run_diagnostic_lifecycle(workspace_root_arg=args.workspace_root, onnx_cache_dir_arg=args.onnx_cache_dir)
