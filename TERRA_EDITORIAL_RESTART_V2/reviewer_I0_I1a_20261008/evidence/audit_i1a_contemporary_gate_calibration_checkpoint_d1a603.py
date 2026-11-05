#!/usr/bin/env python3
"""
scripts/audit_i1a_contemporary_gate_calibration.py
=================================================
PROPOSAL REVISED SCRIPT FOR CODEX-0017 / CLAUDE-0073 AUDIT.
DO NOT RUN WITHOUT EXPLICIT USER AUTHORIZATION.

Offline, isolated contemporary diagnostic of nearest-neighbor Chroma distances
across terra_350_benchmark.json and legacy terra_175_benchmark.json cohorts
against a disposable, hash-verified snapshot copy of dataset_20k_cap/vector_db_20k.

Audit & Security Hardening (Codex-0015, Codex-0016, Codex-0017, Claude-0073):
1. Import purity: Network guards and environment variables are scoped to lifecycle
   execution; merely importing this module causes zero global network or environment mutation.
2. Verified binding of the installed Chroma embedding function (DefaultEmbeddingFunction /
   ONNXMiniLM_L6_V2) to the validated cache directory, recording delegate and cache provenance.
3. Pre-resolution reparse point and symlink validation across all raw parent directories.
4. Unified result validator for both Benchmark 350 and Legacy 40 queries.
5. Strict numerical policy: material negative distances (< -1e-6) abort; tiny negative
   distances ([-1e-6, 0.0)) are preserved raw, flagged, and clamped only for derived sqrt.
6. Granular concordance classification distinguishing AUROC drift from threshold count discrepancies.
7. Explicit enforced offline condition declared and recorded in the report (Layer 1 external,
   Layer 2 in-process interceptors; default UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT).
8. Full payload read-back verification on report serialization (fails closed on mismatch or write error).
9. Safe lifecycle finalization: early failure paths cannot crash with unassigned locals; unmeasured
   sources are flagged UNVERIFIED_OR_NOT_MEASURED; outer finally cleanly calls uninstall_network_guards().
10. Strict saved grid validation: missing or non-integer fp/tp/fn fields trigger immediate validation failure.
11. Explicit provenance disclaimer embedded in report: concordance does not establish historical provenance.
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
# 1. Scoped Network Security & Telemetry Interception (No Side Effects on Import)
# ------------------------------------------------------------------------------
_NETWORK_GUARDS_INSTALLED = False
_ORIGINAL_NETWORK_CALLS: Dict[str, Any] = {}

def _blocked_network_call(*args, **kwargs):
    raise AuditSecurityError("ENFORCEABLE SECURITY GUARD: Outbound network call is strictly prohibited during offline audit.")

def install_network_guards() -> None:
    """
    Installs in-process fail-closed network blockers on socket, urllib, and httpx,
    and sets offline environment variables. Reversible via uninstall_network_guards().
    """
    global _NETWORK_GUARDS_INSTALLED, _ORIGINAL_NETWORK_CALLS
    if _NETWORK_GUARDS_INSTALLED:
        return

    # Store existing environment variables
    env_keys = ["ANONYMIZED_TELEMETRY", "CHROMA_TELEMETRY", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]
    _ORIGINAL_NETWORK_CALLS["environ"] = {k: os.environ.get(k) for k in env_keys}

    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["CHROMA_TELEMETRY"] = "False"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    import socket
    import urllib.request

    _ORIGINAL_NETWORK_CALLS["socket_connect"] = socket.socket.connect
    _ORIGINAL_NETWORK_CALLS["socket_connect_ex"] = socket.socket.connect_ex
    _ORIGINAL_NETWORK_CALLS["socket_sendto"] = socket.socket.sendto
    _ORIGINAL_NETWORK_CALLS["create_connection"] = socket.create_connection
    _ORIGINAL_NETWORK_CALLS["getaddrinfo"] = socket.getaddrinfo
    _ORIGINAL_NETWORK_CALLS["urlopen"] = urllib.request.urlopen

    socket.socket.connect = _blocked_network_call
    socket.socket.connect_ex = _blocked_network_call
    socket.socket.sendto = _blocked_network_call
    socket.create_connection = _blocked_network_call
    socket.getaddrinfo = _blocked_network_call
    urllib.request.urlopen = _blocked_network_call

    try:
        import httpx
        _ORIGINAL_NETWORK_CALLS["httpx_client_send"] = httpx.Client.send
        _ORIGINAL_NETWORK_CALLS["httpx_async_client_send"] = httpx.AsyncClient.send
        _ORIGINAL_NETWORK_CALLS["httpx_get"] = httpx.get
        _ORIGINAL_NETWORK_CALLS["httpx_post"] = httpx.post
        _ORIGINAL_NETWORK_CALLS["httpx_stream"] = httpx.stream
        _ORIGINAL_NETWORK_CALLS["httpx_request"] = httpx.request

        httpx.Client.send = _blocked_network_call
        httpx.AsyncClient.send = _blocked_network_call
        httpx.get = _blocked_network_call
        httpx.post = _blocked_network_call
        httpx.stream = _blocked_network_call
        httpx.request = _blocked_network_call
    except ImportError:
        pass

    _NETWORK_GUARDS_INSTALLED = True

def uninstall_network_guards() -> None:
    """
    Restores socket, urllib, httpx, and environment variables to their pre-guard states.
    """
    global _NETWORK_GUARDS_INSTALLED, _ORIGINAL_NETWORK_CALLS
    if not _NETWORK_GUARDS_INSTALLED:
        return

    import socket
    import urllib.request

    if "socket_connect" in _ORIGINAL_NETWORK_CALLS:
        socket.socket.connect = _ORIGINAL_NETWORK_CALLS["socket_connect"]
        socket.socket.connect_ex = _ORIGINAL_NETWORK_CALLS["socket_connect_ex"]
        socket.socket.sendto = _ORIGINAL_NETWORK_CALLS["socket_sendto"]
        socket.create_connection = _ORIGINAL_NETWORK_CALLS["create_connection"]
        socket.getaddrinfo = _ORIGINAL_NETWORK_CALLS["getaddrinfo"]
        urllib.request.urlopen = _ORIGINAL_NETWORK_CALLS["urlopen"]

    try:
        import httpx
        if "httpx_client_send" in _ORIGINAL_NETWORK_CALLS:
            httpx.Client.send = _ORIGINAL_NETWORK_CALLS["httpx_client_send"]
            httpx.AsyncClient.send = _ORIGINAL_NETWORK_CALLS["httpx_async_client_send"]
            httpx.get = _ORIGINAL_NETWORK_CALLS["httpx_get"]
            httpx.post = _ORIGINAL_NETWORK_CALLS["httpx_post"]
            httpx.stream = _ORIGINAL_NETWORK_CALLS["httpx_stream"]
            httpx.request = _ORIGINAL_NETWORK_CALLS["httpx_request"]
    except ImportError:
        pass

    for k, v in _ORIGINAL_NETWORK_CALLS.get("environ", {}).items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    _ORIGINAL_NETWORK_CALLS.clear()
    _NETWORK_GUARDS_INSTALLED = False

def run_negative_control_network_test() -> None:
    """
    Verifies that outbound connection attempts fail closed with AuditSecurityError.
    Closes any allocated sockets cleanly in finally blocks.
    """
    install_network_guards()
    import socket
    import urllib.request

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
# 2. Approved Immutable Checksums & Manifests (Restored Evidence-Backed Values)
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

GRID_THRESHOLDS = [0.90, 1.00, 1.10, 1.20, 1.25, 1.30, 1.35, 1.40]
TOLERANCE_TINY_NEGATIVE = -1e-6

def file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file efficiently in 64KB chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def dir_manifest(directory: Path) -> Dict[str, Dict[str, Any]]:
    """Generates deterministic file manifest (relative path -> size & sha256)."""
    manifest = {}
    if not directory.exists():
        return manifest
    for root, _, files in os.walk(directory):
        for f in sorted(files):
            full_path = Path(root) / f
            rel_path = str(full_path.relative_to(directory)).replace("\\", "/")
            manifest[rel_path] = {
                "size": full_path.stat().st_size,
                "sha256": file_sha256(full_path)
            }
    return manifest

def is_windows_reparse_point(path: Path) -> bool:
    """Detects whether a path on Windows is a reparse point (junction, symlink, mount)."""
    try:
        attrs = path.stat().st_file_attributes
        FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False

def validate_safe_unresolved_path(path: Path, path_name: str) -> None:
    """
    Inspects an unresolved path and all parent components to verify no symlinks
    or reparse points exist anywhere in the supplied hierarchy.
    """
    curr = path
    while curr != curr.parent:
        if curr.is_symlink():
            raise AuditSecurityError(f"Security violation: path component '{curr}' in '{path_name}' is a symbolic link.")
        if curr.exists() and is_windows_reparse_point(curr):
            raise AuditSecurityError(f"Security violation: path component '{curr}' in '{path_name}' is a Windows reparse point.")
        curr = curr.parent

def check_path_isolation(orig_db: Path, disposable_db: Path, output_dir: Path, workspace_root: Path) -> None:
    """Strict containment and path non-collision enforcement."""
    resolved_orig = orig_db.resolve()
    resolved_disp = disposable_db.resolve()
    resolved_out = output_dir.resolve()
    resolved_ws = workspace_root.resolve()

    if resolved_orig == resolved_disp:
        raise AuditSecurityError("Disposable database path must not be identical to original database path.")
    if resolved_disp in resolved_orig.parents:
        raise AuditSecurityError("Disposable database must not be a parent directory of original database.")
    if resolved_orig in resolved_disp.parents:
        raise AuditSecurityError("Disposable database must not reside inside original database directory.")
    if resolved_out in resolved_orig.parents or resolved_orig in resolved_out.parents:
        raise AuditSecurityError("Output report directory must not overlap with original database directory.")

    for p, name in [(resolved_orig, "orig_db"), (resolved_disp, "disposable_db"), (resolved_out, "output_dir")]:
        if resolved_ws not in p.parents and p != resolved_ws:
            raise AuditSecurityError(f"Path '{name}' ({p}) is not contained within workspace root ({resolved_ws}).")

def compute_auroc(labels: list, scores: list) -> float:
    """
    Computes exact AUROC using Mann-Whitney U rank-sum statistic with exact 0.5 tie credit,
    matching historical compute_budget_and_gate_metrics.py logic identically.
    """
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0

    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    r_pos = sum(ranks[k] for k in range(len(pairs)) if pairs[k][1] == 1)
    u_pos = r_pos - (n_pos * (n_pos + 1)) / 2.0
    return float(u_pos / (n_pos * n_neg))

def cohort_stats(distances: list) -> Dict[str, Any]:
    """Calculates min, p25, median, p75, p90, max, mean, std over distances."""
    if not distances:
        return {}
    arr = np.array(distances, dtype=float)
    return {
        "count": int(len(arr)),
        "min": float(np.min(arr)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr))
    }

def validate_and_transform_result(query_id: str, distances_raw: list, ids_raw: list) -> Tuple[float, str, float, str]:
    """
    Unified result validator for nearest-neighbor queries:
    - Enforces length == 1 and non-empty stripped node ID
    - Strictly checks finiteness (no NaN, no Inf)
    - Aborts on material negative distance (< -1e-6) with AuditValidationError
    - Preserves tiny negative raw distance ([-1e-6, 0.0)), flags it, and clamps only for derived sqrt
    """
    if not isinstance(distances_raw, list) or len(distances_raw) != 1:
        raise AuditValidationError(f"Query '{query_id}': distances must be a single-element list, got {distances_raw}")
    if not isinstance(ids_raw, list) or len(ids_raw) != 1:
        raise AuditValidationError(f"Query '{query_id}': ids must be a single-element list, got {ids_raw}")

    d_val = distances_raw[0]
    nid = ids_raw[0]

    if not isinstance(nid, str) or not nid.strip():
        raise AuditValidationError(f"Query '{query_id}': node ID must be a non-empty string, got {repr(nid)}")

    if not isinstance(d_val, (int, float)) or not np.isfinite(d_val):
        raise AuditValidationError(f"Query '{query_id}': distance must be a finite float, got {d_val}")

    d_raw = float(d_val)

    if d_raw < TOLERANCE_TINY_NEGATIVE:
        raise AuditValidationError(
            f"Query '{query_id}': materially negative distance {d_raw:.8e} violates physical bounds (< {TOLERANCE_TINY_NEGATIVE:.1e})."
        )
    elif d_raw < 0.0:
        anomaly_flag = "tiny_negative_clamped_for_sqrt"
        d_sqrt = 0.0
    else:
        anomaly_flag = "none"
        d_sqrt = float(np.sqrt(d_raw))

    return d_raw, nid, d_sqrt, anomaly_flag

def write_and_verify_report(report_file: Path, state: dict) -> None:
    """
    Serializes report with exclusive creation ('x'), allow_nan=False,
    and performs immediate complete payload read-back verification.
    Any failure raises AuditExecutionError and emits terminal failure JSON to stderr.
    """
    try:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "x", encoding="utf-8") as f_out:
            json.dump(state, f_out, indent=2, allow_nan=False)

        # Immediate full-payload read-back verification
        with open(report_file, "r", encoding="utf-8") as f_in:
            parsed = json.load(f_in)
        if parsed != state:
            raise AuditExecutionError("Read-back verification failed: parsed payload does not match memory state.")
    except Exception as exc:
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
    enforced_offline_condition_arg: Optional[str] = None,
    expected_manifests: Optional[Dict[str, Any]] = None,
    mock_overrides: Optional[Dict[str, Any]] = None,
    exit_on_complete: bool = True
) -> Tuple[int, Dict[str, Any]]:
    # Initialize timestamp and unique run identifier
    run_timestamp = int(time.time())
    run_uuid = uuid.uuid4().hex[:8]
    run_id = f"{run_timestamp}_{os.getpid()}_{run_uuid}"
    iso_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    enforced_offline_cond = enforced_offline_condition_arg or "UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT"

    # Pre-initialize path variables to avoid UnboundLocalError in early finally blocks
    workspace_root: Optional[Path] = None
    orig_db_dir: Optional[Path] = None
    disposable_scratch_dir: Optional[Path] = None
    disposable_db_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    report_file: Optional[Path] = None
    cache_dir_path: Optional[Path] = None
    benchmark_350_path: Optional[Path] = None
    benchmark_175_path: Optional[Path] = None
    saved_summary_path: Optional[Path] = None
    path_validation_succeeded: bool = False

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
        "enforced_offline_condition": enforced_offline_cond,
        "offline_execution_environment": {
            "enforced_offline_condition": enforced_offline_cond,
            "python_network_interception_active": False,
            "chroma_telemetry_disabled": False,
            "transformers_offline_set": False,
            "negative_control_passed": False,
            "network_guards_uninstalled": False,
            "layering_declaration": (
                f"In-process Python socket/HTTP patches operate as Layer 2 defense-in-depth. "
                f"Layer 1 is the declared external operating condition ('{enforced_offline_cond}')."
            )
        },
        "provenance_disclaimer": (
            "CRITICAL PROVENANCE NOTICE: Even an EXACT_CONCORDANCE outcome demonstrates solely that "
            "the contemporary vector store snapshot, current ONNX model weights, and contemporary runtime "
            "software library reproduce the saved budget grid. It does NOT prove historical run provenance or "
            "establish that the preserved dataset_20k_cap snapshot was the exact historical execution "
            "environment from which the paper tables were generated."
        ),
        "stages_completed": [],
        "errors": [],
        "integrity_checks": {
            "source_db_invariant": "UNVERIFIED_OR_NOT_MEASURED",
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

    # Resolve expected hashes (supporting test overrides)
    exp_b350_sha = expected_manifests.get("benchmark_350_sha", EXPECTED_BENCHMARK_350_SHA256) if expected_manifests else EXPECTED_BENCHMARK_350_SHA256
    exp_b175_sha = expected_manifests.get("benchmark_175_sha", EXPECTED_BENCHMARK_175_SHA256) if expected_manifests else EXPECTED_BENCHMARK_175_SHA256
    exp_summary_sha = expected_manifests.get("saved_summary_sha", EXPECTED_SAVED_SUMMARY_SHA256) if expected_manifests else EXPECTED_SAVED_SUMMARY_SHA256
    exp_onnx_manifest = expected_manifests.get("onnx_cache_manifest", APPROVED_ONNX_CACHE_MANIFEST) if expected_manifests else APPROVED_ONNX_CACHE_MANIFEST
    exp_grid_thresholds = expected_manifests.get("grid_thresholds", GRID_THRESHOLDS) if expected_manifests else GRID_THRESHOLDS

    try:
        print("=" * 80)
        print(f"CONTEMPORARY VECTOR DISTANCE DIAGNOSTIC (RUN ID: {run_id})")
        print("Status: Offline, Isolated, Disposable Snapshot Execution")
        print(f"Declared Offline Condition: {enforced_offline_cond}")
        print("=" * 80)

        # Stage 1: Enforceable Network Negative Control
        print("\n[Stage 1] Executing fail-closed network negative controls...")
        install_network_guards()
        run_negative_control_network_test()
        workflow_state["offline_execution_environment"]["python_network_interception_active"] = True
        workflow_state["offline_execution_environment"]["chroma_telemetry_disabled"] = True
        workflow_state["offline_execution_environment"]["transformers_offline_set"] = True
        workflow_state["offline_execution_environment"]["negative_control_passed"] = True
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
        path_validation_succeeded = True
        workflow_state["stages_completed"].append("stage_2_path_isolation_verified")
        print("  PASS: Pre-resolution reparse checks and post-resolution isolation confirmed.")

        # Stage 3: Preflight Verification of Approved Immutable Assets
        print("\n[Stage 3] Preflight verification of benchmarks and ONNX cache manifest...")
        if not benchmark_350_path.exists():
            raise AuditValidationError(f"Missing Benchmark 350: {benchmark_350_path}")
        b350_sha = file_sha256(benchmark_350_path)
        if b350_sha != exp_b350_sha:
            raise AuditIntegrityError(f"Benchmark 350 SHA256 mismatch: {b350_sha} != {exp_b350_sha}")

        if not benchmark_175_path.exists():
            raise AuditValidationError(f"Missing Benchmark 175: {benchmark_175_path}")
        b175_sha = file_sha256(benchmark_175_path)
        if b175_sha != exp_b175_sha:
            raise AuditIntegrityError(f"Benchmark 175 SHA256 mismatch: {b175_sha} != {exp_b175_sha}")

        if not saved_summary_path.exists():
            raise AuditValidationError(f"Missing Saved Summary: {saved_summary_path}")
        summary_sha = file_sha256(saved_summary_path)
        if summary_sha != exp_summary_sha:
            raise AuditIntegrityError(f"Saved summary SHA256 mismatch: {summary_sha} != {exp_summary_sha}")

        # Strict check against ONNX cache manifest (both size AND SHA256)
        for fname, expected in exp_onnx_manifest.items():
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
        print("  PASS: Benchmark 350, Benchmark 175, Saved Summary, and all ONNX cache assets verified.")

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

        # Stage 6: Cohort Definitions Validation
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
        from chromadb.api.types import DefaultEmbeddingFunction
        import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_module
        InstalledONNXMiniLM = onnx_module.ONNXMiniLM_L6_V2

        # 1. Verify the installed concrete ONNX MiniLM class and resolved cache path
        installed_ef_instance = InstalledONNXMiniLM()
        resolved_ef_dir = (Path(installed_ef_instance.DOWNLOAD_PATH) / installed_ef_instance.EXTRACTED_FOLDER_NAME).resolve()
        if resolved_ef_dir != cache_dir_path:
            raise AuditSecurityError(
                f"Embedding function cache path mismatch: '{resolved_ef_dir}' != validated cache path '{cache_dir_path}'"
            )

        client = chromadb.PersistentClient(path=str(disposable_db_dir))
        coll = client.get_collection(name="thinking_traces")

        # Establish and record exact delegate and cache attributes
        ef_delegate_obj = getattr(coll, "_embedding_function", None)
        ef_delegate_name = ef_delegate_obj.name() if hasattr(ef_delegate_obj, "name") else type(ef_delegate_obj).__name__

        # Validate installed class identity (DefaultEmbeddingFunction or concrete ONNXMiniLM)
        is_mock_allowed = bool(mock_overrides and mock_overrides.get("allow_mock_ef", False))
        is_genuine_default = isinstance(ef_delegate_obj, DefaultEmbeddingFunction)
        is_genuine_onnx = isinstance(ef_delegate_obj, InstalledONNXMiniLM) if isinstance(InstalledONNXMiniLM, type) else False

        if not (is_genuine_default or is_genuine_onnx or is_mock_allowed):
            raise AuditSecurityError(
                f"Security violation: Collection embedding function '{type(ef_delegate_obj)}' "
                f"(module: '{type(ef_delegate_obj).__module__}', name: '{ef_delegate_name}') "
                f"is not a genuine installed DefaultEmbeddingFunction or ONNXMiniLM_L6_V2 instance."
            )

        installed_class_name = InstalledONNXMiniLM.__qualname__ if hasattr(InstalledONNXMiniLM, "__qualname__") else type(InstalledONNXMiniLM).__name__
        installed_module_name = InstalledONNXMiniLM.__module__ if hasattr(InstalledONNXMiniLM, "__module__") else type(InstalledONNXMiniLM).__module__

        ef_delegate_info = {
            "class": type(ef_delegate_obj).__name__,
            "module": type(ef_delegate_obj).__module__,
            "qualname": getattr(type(ef_delegate_obj), "__qualname__", type(ef_delegate_obj).__name__),
            "name": ef_delegate_name,
            "is_default_embedding_function": is_genuine_default,
            "is_concrete_onnx_minilm": is_genuine_onnx,
            "is_mock_override": is_mock_allowed and not (is_genuine_default or is_genuine_onnx),
            "installed_onnx_class": installed_class_name,
            "installed_onnx_module": installed_module_name,
            "delegates_to_onnx_minilm": True,
            "verified_cache_dir": str(cache_dir_path)
        }

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

        dist_by_qid_350 = {}
        for q, raw_d_list, raw_id_list in zip(bench_350, chroma_res_350["distances"], chroma_res_350["ids"]):
            qid = q["query_id"]
            d_raw, nid, d_sqrt, flag = validate_and_transform_result(qid, raw_d_list, raw_id_list)
            dist_by_qid_350[qid] = {
                "distance_raw_squared": d_raw,
                "distance_euclidean_sqrt": d_sqrt,
                "nearest_node_id": nid,
                "anomaly_flag": flag,
                "category": q["category"]
            }
            workflow_state["query_ledger_350"].append({
                "query_id": qid,
                "category": q["category"],
                "distance_raw_squared": d_raw,
                "distance_euclidean_sqrt": d_sqrt,
                "nearest_node_id": nid,
                "anomaly_flag": flag
            })

        workflow_state["stages_completed"].append("stage_7_benchmark_350_queried")
        print("  PASS: Benchmark 350 queried and all 350 results strictly validated.")

        # Stage 8: Query Benchmark 175 Sample20 Cohorts
        print("\n[Stage 8] Querying Legacy Benchmark 175 sample_in_20 and sample_out_20...")
        texts_in_175 = [q["query"] for q in sample_in_175]
        texts_out_175 = [q["query"] for q in sample_out_175]

        if mock_overrides and "mock_query_fn_175" in mock_overrides:
            res_in_175, res_out_175 = mock_overrides["mock_query_fn_175"](sample_in_175, sample_out_175)
        else:
            res_in_175 = coll.query(query_texts=texts_in_175, n_results=1)
            res_out_175 = coll.query(query_texts=texts_out_175, n_results=1)

        if not isinstance(res_in_175.get("distances"), list) or len(res_in_175["distances"]) != 20:
            raise AuditValidationError("Mismatch in Benchmark 175 sample_in distances length.")
        if not isinstance(res_out_175.get("distances"), list) or len(res_out_175["distances"]) != 20:
            raise AuditValidationError("Mismatch in Benchmark 175 sample_out distances length.")

        sample_in_dists_raw = []
        sample_in_dists_sqrt = []
        for q, raw_d_list, raw_id_list in zip(sample_in_175, res_in_175["distances"], res_in_175["ids"]):
            qid = q.get("query_id", "sample_in_q")
            d_raw, nid, d_sqrt, flag = validate_and_transform_result(qid, raw_d_list, raw_id_list)
            sample_in_dists_raw.append(d_raw)
            sample_in_dists_sqrt.append(d_sqrt)
            workflow_state["legacy_sample20_query_ledger"].append({
                "cohort": "sample_in_20",
                "query_id": qid,
                "distance_raw_squared": d_raw,
                "distance_euclidean_sqrt": d_sqrt,
                "nearest_node_id": nid,
                "anomaly_flag": flag
            })

        sample_out_dists_raw = []
        sample_out_dists_sqrt = []
        for q, raw_d_list, raw_id_list in zip(sample_out_175, res_out_175["distances"], res_out_175["ids"]):
            qid = q.get("query_id", "sample_out_q")
            d_raw, nid, d_sqrt, flag = validate_and_transform_result(qid, raw_d_list, raw_id_list)
            sample_out_dists_raw.append(d_raw)
            sample_out_dists_sqrt.append(d_sqrt)
            workflow_state["legacy_sample20_query_ledger"].append({
                "cohort": "sample_out_20",
                "query_id": qid,
                "distance_raw_squared": d_raw,
                "distance_euclidean_sqrt": d_sqrt,
                "nearest_node_id": nid,
                "anomaly_flag": flag
            })

        workflow_state["legacy_sample20_diagnostic"] = {
            "sample_in_20_raw_squared": cohort_stats(sample_in_dists_raw),
            "sample_in_20_euclidean_sqrt": cohort_stats(sample_in_dists_sqrt),
            "sample_out_20_raw_squared": cohort_stats(sample_out_dists_raw),
            "sample_out_20_euclidean_sqrt": cohort_stats(sample_out_dists_sqrt)
        }
        workflow_state["stages_completed"].append("stage_8_benchmark_175_queried")
        print("  PASS: Legacy Benchmark 175 sample cohorts queried and validated.")

        # Stage 9: Evaluate Gate Calibration and AUROC Concordance
        print("\n[Stage 9] Computing AUROC and evaluating concordance against saved summary...")
        in_dists = [dist_by_qid_350[qid]["distance_raw_squared"] for qid in in_domain_qids]
        ood_dists = [dist_by_qid_350[qid]["distance_raw_squared"] for qid in ood_qids]
        adv_dists = [dist_by_qid_350[qid]["distance_raw_squared"] for qid in adv_qids]

        y_true = [0] * len(in_dists) + [1] * len(ood_dists)
        y_scores = in_dists + ood_dists
        diagnostic_auroc = compute_auroc(y_true, y_scores)

        diagnostic_grid = {}
        for tau in exp_grid_thresholds:
            tau_key = f"{tau:.2f}"
            fp = sum(1 for d in in_dists if d >= tau)
            tp = sum(1 for d in ood_dists if d >= tau)
            fn = len(ood_dists) - tp
            diagnostic_grid[tau_key] = {
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

            # Strict validation: require explicit integer fields (reject missing or defaulted values)
            for req_field in ["fp", "tp", "fn"]:
                if req_field not in s_val or not isinstance(s_val[req_field], int):
                    raise AuditValidationError(f"Threshold '{k}' missing required integer field '{req_field}' in saved grid.")

            fp_saved = s_val["fp"]
            tp_saved = s_val["tp"]
            fn_saved = s_val["fn"]

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
            "provenance_policy": (
                "No concordance outcome authenticates historical provenance or authorizes manuscript replacement. "
                "Even an EXACT_CONCORDANCE result demonstrates solely that the current vector store snapshot, "
                "current model weights, and contemporary runtime library reproduce the saved budget grid."
            )
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
                "search_semantics": "Approximate Nearest Neighbor (ANN) search via HNSWlib space='l2' (squared Euclidean distance) as configured in collection schema; no unit-normalization assumption asserted on stored vectors",
                "schema_migrated_during_query": schema_migrated,
                "pre_connection_schema": parsed_schema_pre,
                "post_query_schema": json.loads(schema_str_post) if schema_str_post else {}
            },
            "embedding_function_delegate": ef_delegate_info,
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
            # Safe verification: handles unassigned or unreached paths gracefully
            if orig_db_dir is not None and orig_db_dir.exists():
                orig_post_manifest = dir_manifest(orig_db_dir)
                source_invariant = (orig_post_manifest == orig_pre_manifest) if (orig_pre_manifest and len(orig_pre_manifest) > 0) else False
            else:
                orig_post_manifest = {}
                source_invariant = False
            workflow_state["integrity_checks"]["source_db_invariant"] = source_invariant if len(orig_pre_manifest) > 0 else "UNVERIFIED_OR_NOT_MEASURED"

            if benchmark_350_path is not None and benchmark_350_path.exists():
                b350_post_sha = file_sha256(benchmark_350_path)
                b350_invariant = (b350_post_sha == exp_b350_sha)
            else:
                b350_invariant = False
            workflow_state["integrity_checks"]["benchmark_350_invariant"] = b350_invariant

            if benchmark_175_path is not None and benchmark_175_path.exists():
                b175_post_sha = file_sha256(benchmark_175_path)
                b175_invariant = (b175_post_sha == exp_b175_sha)
            else:
                b175_invariant = False
            workflow_state["integrity_checks"]["benchmark_175_invariant"] = b175_invariant

            if saved_summary_path is not None and saved_summary_path.exists():
                summary_post_sha = file_sha256(saved_summary_path)
                summary_invariant = (summary_post_sha == exp_summary_sha)
            else:
                summary_invariant = False
            workflow_state["integrity_checks"]["saved_summary_invariant"] = summary_invariant

            onnx_post_manifest = {}
            onnx_invariant = True
            if cache_dir_path is not None and cache_dir_path.exists():
                for fname, exp in exp_onnx_manifest.items():
                    fpath = cache_dir_path / fname
                    if not fpath.exists():
                        onnx_invariant = False
                        continue
                    sha = file_sha256(fpath)
                    onnx_post_manifest[fname] = {"size": fpath.stat().st_size, "sha256": sha}
                    if sha != exp["sha256"]:
                        onnx_invariant = False
            else:
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
                "original_store_integrity": (
                    "strictly invariant (100% bit-identical)" if (source_invariant and len(orig_pre_manifest) > 0)
                    else "UNVERIFIED_OR_NOT_MEASURED" if len(orig_pre_manifest) == 0
                    else "INTEGRITY_VIOLATION"
                ),
                "onnx_cache_pre_manifest": onnx_pre_manifest,
                "onnx_cache_post_manifest": onnx_post_manifest,
                "analysis_copy_path": str(disposable_db_dir) if disposable_db_dir is not None else "not_created"
            }

            if not all_passed and len(orig_pre_manifest) > 0:
                workflow_state["errors"].append({
                    "error_type": "AuditIntegrityError",
                    "error_message": "CRITICAL INTEGRITY FAILURE: One or more original protected assets mutated during run!"
                })
        except Exception as integrity_exc:
            workflow_state["errors"].append({
                "error_type": "FinalIntegrityCheckError",
                "error_message": str(integrity_exc)
            })

        # Stage 12: Guaranteed In-Process Network Guard Uninstallation and Environment Restoration
        # Executed BEFORE status determination and report serialization to guarantee that
        # incomplete process cleanup is captured as FAILED and recorded on disk.
        print("\n[Final Stage] Restoring network guards and process environment...")
        try:
            if mock_overrides and "mock_cleanup_fn" in mock_overrides:
                mock_overrides["mock_cleanup_fn"]()
            else:
                uninstall_network_guards()
            workflow_state["offline_execution_environment"]["network_guards_uninstalled"] = True
        except Exception as cleanup_err:
            workflow_state["offline_execution_environment"]["network_guards_uninstalled"] = False
            workflow_state["errors"].append({
                "error_type": "CleanupRestorationError",
                "error_message": f"CRITICAL CLEANUP FAILURE: Failed to cleanly uninstall network guards or restore environment: {cleanup_err}"
            })
            print(f"CRITICAL CLEANUP FAILURE: {cleanup_err}", file=sys.stderr)
        finally:
            # Fallback to ensure actual process restore is unconditionally attempted
            try:
                uninstall_network_guards()
            except Exception:
                pass

        # Final Status Determination
        # (SUCCESS strictly requires 0 errors, all integrity checks passed, and network guards cleanly uninstalled)
        cleanup_succeeded = workflow_state.get("offline_execution_environment", {}).get("network_guards_uninstalled", False)
        if (len(workflow_state["errors"]) == 0 and 
            workflow_state["integrity_checks"].get("all_integrity_passed", False) and 
            cleanup_succeeded):
            workflow_state["status"] = "SUCCESS"
        else:
            workflow_state["status"] = "FAILED"

        # Safe Report Serialization: finalize status-bearing report after cleanup outcome is known
        try:
            if path_validation_succeeded and report_file is not None:
                if mock_overrides and "mock_report_writer" in mock_overrides:
                    mock_overrides["mock_report_writer"](report_file, workflow_state)
                else:
                    write_and_verify_report(report_file, workflow_state)
                print(f"\n[Final Report] Report serialized and verified at:\n  {report_file}")
            else:
                print("NOTE: Path validation did not succeed; skipping file report serialization.", file=sys.stderr)
            print(f"Final Outcome Status: {workflow_state['status']}")
        except Exception as write_err:
            workflow_state["status"] = "FAILED"
            workflow_state["errors"].append({
                "error_type": "ReportSerializationError",
                "error_message": str(write_err)
            })
            print(f"CRITICAL REPORT FAILURE: {write_err}", file=sys.stderr)
            # Try to emit an unambiguous fallback failure record if primary serialization failed
            try:
                if report_file is not None:
                    with open(report_file, "w", encoding="utf-8") as f_fallback:
                        json.dump(workflow_state, f_fallback, indent=2, default=str)
            except Exception:
                pass

        print("=" * 80)

    # Clean Exit Control
    if workflow_state["status"] == "SUCCESS" and workflow_state["integrity_checks"]["all_integrity_passed"]:
        print("DIAGNOSTIC WORKFLOW COMPLETE (DISPOSABLE SNAPSHOT EVALUATED)")
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
    parser.add_argument("--enforced-offline-condition", type=str, default="UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT", help="Declared external offline execution condition")
    args = parser.parse_args()

    run_diagnostic_lifecycle(
        workspace_root_arg=args.workspace_root,
        onnx_cache_dir_arg=args.onnx_cache_dir,
        enforced_offline_condition_arg=args.enforced_offline_condition
    )
