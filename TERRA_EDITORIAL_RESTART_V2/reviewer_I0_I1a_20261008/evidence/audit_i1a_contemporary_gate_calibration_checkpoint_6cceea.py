#!/usr/bin/env python3
"""
scripts/audit_i1a_contemporary_gate_calibration.py
=================================================
PROPOSAL SCRIPT FOR CODEX AND CLAUDE AUDIT.
DO NOT RUN WITHOUT EXPLICIT USER AUTHORIZATION.

Offline, isolated contemporary diagnostic of nearest-neighbor Chroma distances
across terra_350_benchmark.json and legacy terra_175_benchmark.json cohorts
against a disposable, hash-verified snapshot copy of dataset_20k_cap/vector_db_20k.

Safeguards:
1. Enforceable fail-closed network ban (monkey-patched sockets/HTTP with negative control).
2. Preflight verification of all 6 local ONNX cache files and benchmark checksums.
3. Disposable timestamped snapshot copy beneath scratch/diagnostics/; zero in-place mutation.
4. Active schema extraction directly from SQLite metadata (verifies 'space': 'l2').
5. Full 350-query ledger with raw squared L2 (d^2) and derived Euclidean (d = sqrt(d^2)).
6. Invariant pre/post source hashing in a finally block to guarantee zero source database mutation.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import sqlite3
import argparse
from pathlib import Path
import numpy as np

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
    raise PermissionError("ENFORCEABLE SECURITY GUARD: Outbound network call is strictly prohibited during offline audit.")

# Monkey-patch standard socket and urllib connections
socket.socket.connect = _blocked_network_call
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
    """Verifies that outbound connection attempts fail closed with PermissionError."""
    # Test 1: Socket connect
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 9999))
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket connection was not blocked!")
    except PermissionError:
        pass
    except Exception as e:
        if not isinstance(e, PermissionError):
            raise RuntimeError(f"NEGATIVE CONTROL FAILED: Unexpected socket exception: {e}")

    # Test 2: Socket create_connection
    try:
        socket.create_connection(("127.0.0.1", 9999), timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket create_connection was not blocked!")
    except PermissionError:
        pass
    except Exception as e:
        if not isinstance(e, PermissionError):
            raise RuntimeError(f"NEGATIVE CONTROL FAILED: Unexpected create_connection exception: {e}")

    # Test 3: Socket getaddrinfo
    try:
        socket.getaddrinfo("localhost", 9999)
        raise RuntimeError("NEGATIVE CONTROL FAILED: Socket getaddrinfo was not blocked!")
    except PermissionError:
        pass
    except Exception as e:
        if not isinstance(e, PermissionError):
            raise RuntimeError(f"NEGATIVE CONTROL FAILED: Unexpected getaddrinfo exception: {e}")

    # Test 4: urllib request
    try:
        urllib.request.urlopen("http://127.0.0.1:9999", timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: urllib call was not blocked!")
    except PermissionError:
        pass
    except Exception as e:
        if not isinstance(e, PermissionError):
            raise RuntimeError(f"NEGATIVE CONTROL FAILED: Unexpected urllib exception: {e}")

    # Test 5: httpx request (if httpx is available)
    try:
        import httpx
        with httpx.Client() as cl:
            cl.get("http://127.0.0.1:9999", timeout=0.1)
        raise RuntimeError("NEGATIVE CONTROL FAILED: httpx GET call was not blocked!")
    except PermissionError:
        pass
    except ImportError:
        pass
    except Exception as e:
        if not isinstance(e, PermissionError):
            raise RuntimeError(f"NEGATIVE CONTROL FAILED: Unexpected httpx exception: {e}")

# ------------------------------------------------------------------------------
# 2. Path Declarations and Expected Checksums
# ------------------------------------------------------------------------------
WORKSPACE_ROOT = Path(".").resolve()
ORIG_DB_DIR = (WORKSPACE_ROOT / "dataset_20k_cap" / "vector_db_20k").resolve()
BENCHMARK_350_PATH = (WORKSPACE_ROOT / "terra_350_benchmark.json").resolve()
BENCHMARK_175_PATH = (WORKSPACE_ROOT / "terra_175_benchmark.json").resolve()
SAVED_SUMMARY_PATH = (WORKSPACE_ROOT / "scratch" / "budget_and_gate_summary.json").resolve()

OUTPUT_DIR = (WORKSPACE_ROOT / "TERRA_EDITORIAL_RESTART_V2" / "reviewer_I0_I1a_20261008" / "addendum_01").resolve()
OUTPUT_FILE = (OUTPUT_DIR / "contemporary_distance_diagnostic.json").resolve()

ONNX_CACHE_DIR = Path(r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx").resolve()
REQUIRED_ONNX_FILES = [
    "config.json",
    "model.onnx",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.txt"
]

EXPECTED_BENCHMARK_350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
EXPECTED_BENCHMARK_175_SHA256 = "8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305"
EXPECTED_SAVED_SUMMARY_SHA256 = "b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f"

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
            manifest[rel] = {
                "size": p.stat().st_size,
                "sha256": file_sha256(p)
            }
    return manifest

def compute_auroc(y_true, y_scores):
    pos = [s for y, s in zip(y_true, y_scores) if y == 1]
    neg = [s for y, s in zip(y_true, y_scores) if y == 0]
    total = len(pos) * len(neg)
    if total == 0:
        return 0.0
    concordant = sum(1 for p in pos for n in neg if p > n)
    tied = sum(1 for p in pos for n in neg if p == n)
    return (concordant + 0.5 * tied) / total

# ------------------------------------------------------------------------------
# 3. Main Audit Workflow
# ------------------------------------------------------------------------------
def run_diagnostic(overwrite: bool = False):
    print("=" * 80)
    print("CONTEMPORARY VECTOR DISTANCE DIAGNOSTIC & CALIBRATION AUDIT")
    print("Status: Offline, Read-Only, Isolated Disposable Snapshot Execution")
    print("=" * 80)

    # Step 1: Run Fail-Closed Network Negative Control
    print("\n[Step 1] Executing fail-closed network prohibition negative control...")
    run_negative_control_network_test()
    print("  PASS: Socket and HTTP access strictly blocked and verified.")

    # Step 2: Preflight Verification of Local Assets
    print("\n[Step 2] Preflight checksum verification of benchmark and cache assets...")
    assert BENCHMARK_350_PATH.exists(), f"Missing: {BENCHMARK_350_PATH}"
    b350_sha = file_sha256(BENCHMARK_350_PATH)
    assert b350_sha == EXPECTED_BENCHMARK_350_SHA256, f"Benchmark 350 hash mismatch: {b350_sha}"
    print(f"  PASS: Benchmark 350 verified ({b350_sha})")

    assert BENCHMARK_175_PATH.exists(), f"Missing: {BENCHMARK_175_PATH}"
    b175_sha = file_sha256(BENCHMARK_175_PATH)
    assert b175_sha == EXPECTED_BENCHMARK_175_SHA256, f"Benchmark 175 hash mismatch: {b175_sha}"
    print(f"  PASS: Benchmark 175 verified ({b175_sha})")

    assert SAVED_SUMMARY_PATH.exists(), f"Missing: {SAVED_SUMMARY_PATH}"
    summary_sha = file_sha256(SAVED_SUMMARY_PATH)
    assert summary_sha == EXPECTED_SAVED_SUMMARY_SHA256, f"Saved summary hash mismatch: {summary_sha}"
    print(f"  PASS: Saved summary verified ({summary_sha})")

    onnx_manifest = {}
    for fname in REQUIRED_ONNX_FILES:
        fpath = ONNX_CACHE_DIR / fname
        assert fpath.exists(), f"CRITICAL: Missing required ONNX cache file: {fpath}"
        onnx_manifest[fname] = {
            "size": fpath.stat().st_size,
            "sha256": file_sha256(fpath)
        }
    print(f"  PASS: All 6 ONNX cache files present and verified at: {ONNX_CACHE_DIR}")

    # Output file collision guard
    if OUTPUT_FILE.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {OUTPUT_FILE}. Use --overwrite to replace.")

    # Step 3: Quiescent Manifest of Original Database
    print("\n[Step 3] Taking preflight quiescent manifest of original vector database...")
    assert ORIG_DB_DIR.exists(), f"Missing vector DB: {ORIG_DB_DIR}"
    orig_pre_manifest = dir_manifest(ORIG_DB_DIR)
    print(f"  Captured manifest for {len(orig_pre_manifest)} files in original database.")

    # Unique run-isolated scratch directory
    run_id = f"i1a_calib_{int(time.time())}_{os.getpid()}"
    run_scratch_dir = (WORKSPACE_ROOT / "scratch" / "diagnostics" / run_id).resolve()
    disposable_db_dir = run_scratch_dir / "vector_db_20k"

    # Validate resolved paths
    assert disposable_db_dir != ORIG_DB_DIR, "Disposable DB path must not equal original path!"
    assert WORKSPACE_ROOT in disposable_db_dir.parents, "Disposable DB must reside within workspace!"
    assert ORIG_DB_DIR not in disposable_db_dir.parents, "Disposable DB must not reside inside original DB!"
    assert disposable_db_dir not in ORIG_DB_DIR.parents, "Original DB must not reside inside disposable DB!"
    assert not disposable_db_dir.is_symlink(), "Disposable path must not be a symlink!"
    assert not ORIG_DB_DIR.is_symlink(), "Original DB path must not be a symlink!"

    print(f"\n[Step 4] Copying database to disposable analysis directory: {disposable_db_dir}")
    run_scratch_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ORIG_DB_DIR, disposable_db_dir)

    # Verify copied manifest matches original pre-manifest
    copied_manifest = dir_manifest(disposable_db_dir)
    assert copied_manifest == orig_pre_manifest, "Copied DB manifest does not match original manifest!"

    # Verify source was not altered by copytree
    orig_after_copy_manifest = dir_manifest(ORIG_DB_DIR)
    assert orig_after_copy_manifest == orig_pre_manifest, "Original DB altered during copy operation!"
    print("  PASS: Snapshot integrity confirmed across original and copied stores.")

    # Wrap analysis execution in try-finally to ensure original DB integrity verification
    try:
        # Step 5: Extract Active Collection Configuration via SQLite
        print("\n[Step 5] Extracting active collection configuration from SQLite schema...")
        sqlite_path = disposable_db_dir / "chroma.sqlite3"
        conn = sqlite3.connect(str(sqlite_path))
        c = conn.cursor()
        c.execute("SELECT id, name, dimension, schema_str FROM collections WHERE name = 'thinking_traces'")
        coll_row = c.fetchone()
        assert coll_row is not None, "Collection 'thinking_traces' not found in collections table!"
        coll_id, coll_name, coll_dim, schema_str = coll_row
        conn.close()

        parsed_schema = json.loads(schema_str) if schema_str else {}
        embedding_key_config = parsed_schema.get("keys", {}).get("#embedding", {}).get("float_list", {}).get("vector_index", {}).get("config", {})
        active_space = embedding_key_config.get("space")
        active_hnsw = embedding_key_config.get("hnsw", {})

        print(f"  Collection ID: {coll_id}")
        print(f"  Dimension:     {coll_dim}")
        print(f"  Active Space:  '{active_space}' (HNSW squared Euclidean distance)")
        print(f"  HNSW Config:   {active_hnsw}")
        assert active_space == "l2", f"Expected active space 'l2', found '{active_space}'"

        # Step 6: Connect Chroma Client to Disposable Snapshot
        print("\n[Step 6] Connecting Chroma client to disposable snapshot...")
        import chromadb
        client = chromadb.PersistentClient(path=str(disposable_db_dir))
        coll = client.get_collection(name="thinking_traces")
        doc_count = coll.count()
        assert doc_count == 20000, f"Unexpected collection document count: {doc_count}"
        print(f"  Connected successfully. Verified document count: {doc_count:,}")

        # Step 7: Query All 350 Queries from Benchmark 350
        print("\n[Step 7] Querying all 350 queries from terra_350_benchmark.json...")
        with open(BENCHMARK_350_PATH, "r", encoding="utf-8") as f:
            bench_350 = json.load(f)

        assert len(bench_350) == 350, f"Expected 350 queries, found {len(bench_350)}"
        qids_350 = [q["query_id"] for q in bench_350]
        assert len(set(qids_350)) == 350, "Duplicate query IDs detected in benchmark 350!"

        texts_350 = [q["query"] for q in bench_350]
        chroma_res_350 = coll.query(query_texts=texts_350, n_results=1)

        assert len(chroma_res_350["distances"]) == 350, "Mismatch in returned distances count!"
        assert len(chroma_res_350["ids"]) == 350, "Mismatch in returned document IDs count!"

        # Step 8: Build 350-Query Ledger & Calibration Analysis
        print("\n[Step 8] Building 350-query ledger and evaluating calibration cohorts...")
        query_records_350 = []
        dists_by_qid = {}
        for i, q in enumerate(bench_350):
            qid = q["query_id"]
            assert qid not in dists_by_qid, f"Duplicate query ID detected in result processing: {qid}"
            d_raw = chroma_res_350["distances"][i][0]
            nid = chroma_res_350["ids"][i][0]
            assert isinstance(d_raw, (int, float)) and np.isfinite(d_raw) and d_raw >= 0.0, f"Invalid distance for {qid}: {d_raw}"
            assert isinstance(nid, str) and len(nid) > 0, f"Invalid document ID for {qid}: {nid}"

            dists_by_qid[qid] = float(d_raw)
            query_records_350.append({
                "query_id": qid,
                "category": q["category"],
                "subtype": q.get("subtype", ""),
                "query": q["query"],
                "query_sha256": hashlib.sha256(q["query"].encode("utf-8")).hexdigest(),
                "nearest_node_id": nid,
                "raw_l2_squared_distance": float(d_raw),
                "euclidean_distance_sqrt": float(np.sqrt(d_raw))
            })

        # Cohort Partitioning for Benchmark 350 (Explicit A100/B100/C75/D75 checks)
        cat_a_qids = [q["query_id"] for q in bench_350 if q["category"] == "A_Factual"]
        cat_b_qids = [q["query_id"] for q in bench_350 if q["category"] == "B_Evolutionary"]
        ood_qids = [q["query_id"] for q in bench_350 if q["category"] == "C_OutOfContext"]
        adv_qids = [q["query_id"] for q in bench_350 if q["category"] == "D_Adversarial"]

        assert len(cat_a_qids) == 100, f"Expected 100 Category A, found {len(cat_a_qids)}"
        assert len(cat_b_qids) == 100, f"Expected 100 Category B, found {len(cat_b_qids)}"
        assert len(ood_qids) == 75, f"Expected 75 OOD (Category C), found {len(ood_qids)}"
        assert len(adv_qids) == 75, f"Expected 75 Adversarial (Category D), found {len(adv_qids)}"

        in_domain_qids = cat_a_qids + cat_b_qids
        assert len(in_domain_qids) == 200, f"Expected 200 in-domain, found {len(in_domain_qids)}"
        assert len(ood_qids) == 75, f"Expected 75 OOD, found {len(ood_qids)}"
        assert len(adv_qids) == 75, f"Expected 75 adversarial, found {len(adv_qids)}"

        in_dists = [dists_by_qid[qid] for qid in in_domain_qids]
        ood_dists = [dists_by_qid[qid] for qid in ood_qids]
        adv_dists = [dists_by_qid[qid] for qid in adv_qids]

        # Calibration AUROC (In-domain = 0, OOD = 1)
        y_true = [0] * len(in_dists) + [1] * len(ood_dists)
        y_scores = in_dists + ood_dists
        diagnostic_auroc = compute_auroc(y_true, y_scores)

        # 8-Threshold Calibration Grid Evaluation
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

        # Step 9: Concordance Comparison with Saved Summary
        print("\n[Step 9] Concordance comparison against saved budget_and_gate_summary.json...")
        with open(SAVED_SUMMARY_PATH, "r", encoding="utf-8") as f:
            saved_summary = json.load(f)

        saved_grid = saved_summary.get("gate_calibration", {}).get("grid", {})
        saved_auroc = saved_summary.get("gate_calibration", {}).get("auroc", 0.0)

        grid_mismatches = []
        for k, diag_val in diagnostic_grid.items():
            s_val = saved_grid.get(k, {})
            fp_match = (diag_val["fp_count"] == s_val.get("fp"))
            tp_match = (diag_val["tp_count"] == s_val.get("tp"))
            fn_match = (diag_val["fn_count"] == s_val.get("fn"))
            if not (fp_match and tp_match and fn_match):
                grid_mismatches.append({
                    "threshold": k,
                    "diagnostic": diag_val,
                    "saved": s_val
                })

        auroc_diff = abs(diagnostic_auroc - saved_auroc)
        auroc_concordant = auroc_diff <= 1e-6

        print(f"  Diagnostic AUROC: {diagnostic_auroc:.6f} | Saved: {saved_auroc:.6f} (Diff: {auroc_diff:.2e})")
        print(f"  Grid Concordance: {8 - len(grid_mismatches)}/8 thresholds match exactly.")
        if grid_mismatches:
            print(f"  WARNING: {len(grid_mismatches)} threshold mismatches detected!")

        # Step 10: Legacy Benchmark 175 Diagnostic Cohort (sample20)
        print("\n[Step 10] Executing legacy benchmark 175 diagnostic cohorts (sample20)...")
        with open(BENCHMARK_175_PATH, "r", encoding="utf-8") as f:
            bench_175 = json.load(f)

        sample_in_175 = [q for q in bench_175 if q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
        sample_out_175 = [q for q in bench_175 if q.get("category") == "C_OutOfContext"][:20]
        assert len(sample_in_175) == 20, f"Expected 20 in-domain sample, found {len(sample_in_175)}"
        assert len(sample_out_175) == 20, f"Expected 20 OOD sample, found {len(sample_out_175)}"

        # Text overlap check against benchmark 350
        texts_350_set = set(texts_350)
        overlap_in = sum(1 for q in sample_in_175 if q["query"] in texts_350_set)
        overlap_out = sum(1 for q in sample_out_175 if q["query"] in texts_350_set)

        res_in_175 = coll.query(query_texts=[q["query"] for q in sample_in_175], n_results=1)
        res_out_175 = coll.query(query_texts=[q["query"] for q in sample_out_175], n_results=1)

        dists_in_175 = [r[0] for r in res_in_175["distances"]]
        dists_out_175 = [r[0] for r in res_out_175["distances"]]

        def cohort_stats(arr):
            arr = np.array(arr)
            return {
                "n": len(arr),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
                "std_sample_ddof1": float(np.std(arr, ddof=1)),
                "std_population_ddof0": float(np.std(arr, ddof=0)),
                "median": float(np.median(arr)),
                "p95": float(np.percentile(arr, 95))
            }

        sample20_summary = {
            "metadata_disclaimer": "Contemporary sample20 evaluation on current 20k index. Does NOT reproduce or authenticate historical 10k 0.509 claim provenance.",
            "benchmark_175_sha256": b175_sha,
            "text_overlap_with_benchmark_350": {
                "sample_in_20": f"{overlap_in}/20",
                "sample_out_20": f"{overlap_out}/20"
            },
            "sample_in_20_raw_squared": cohort_stats(dists_in_175),
            "sample_in_20_euclidean_sqrt": cohort_stats(np.sqrt(dists_in_175)),
            "sample_out_20_raw_squared": cohort_stats(dists_out_175),
            "sample_out_20_euclidean_sqrt": cohort_stats(np.sqrt(dists_out_175))
        }

        # Step 11: Compute Post-Execution Manifests
        orig_post_manifest = dir_manifest(ORIG_DB_DIR)
        assert orig_post_manifest == orig_pre_manifest, "CRITICAL ALERT: Original vector database was modified during execution!"

        post_onnx_manifest = {}
        for fname in REQUIRED_ONNX_FILES:
            fpath = ONNX_CACHE_DIR / fname
            assert fpath.exists(), f"CRITICAL: ONNX cache file missing: {fname}"
            sha = file_sha256(fpath)
            assert sha == onnx_manifest[fname]["sha256"], f"CRITICAL: ONNX cache file modified: {fname}"
            post_onnx_manifest[fname] = {"size": fpath.stat().st_size, "sha256": sha}

        ort_ver = "not_available"
        try:
            import onnxruntime
            ort_ver = onnxruntime.__version__
        except Exception:
            pass

        # Step 12: Serialize Comprehensive Diagnostic Output
        print("\n[Step 12] Serializing comprehensive diagnostic artifact...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        this_script_sha = file_sha256(Path(__file__).resolve())

        diagnostic_payload = {
            "metadata": {
                "title": "Contemporary Vector Distance Diagnostic on Preserved Local Index",
                "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "script": {
                    "path": str(Path(__file__).resolve().relative_to(WORKSPACE_ROOT)),
                    "sha256": this_script_sha
                },
                "runtime_environment": {
                    "python_version": sys.version,
                    "chromadb_version": chromadb.__version__,
                    "numpy_version": np.__version__,
                    "onnxruntime_version": ort_ver,
                    "local_onnx_manifest": onnx_manifest
                },
                "active_collection_config": {
                    "collection_id": coll_id,
                    "collection_name": coll_name,
                    "dimension": coll_dim,
                    "active_space_metric": active_space,
                    "hnsw_config": active_hnsw,
                    "search_semantics": "Approximate Nearest Neighbor (ANN) search via HNSWlib over unit-normalized embeddings"
                },
                "benchmark_350": {
                    "path": str(BENCHMARK_350_PATH.relative_to(WORKSPACE_ROOT)),
                    "sha256": b350_sha,
                    "total_queries": len(bench_350),
                    "in_domain_n": len(in_dists),
                    "out_of_domain_n": len(ood_dists),
                    "adversarial_n": len(adv_dists)
                },
                "saved_summary_reference": {
                    "path": str(SAVED_SUMMARY_PATH.relative_to(WORKSPACE_ROOT)),
                    "sha256": summary_sha
                }
            },
            "concordance": {
                "diagnostic_auroc": diagnostic_auroc,
                "saved_auroc": saved_auroc,
                "auroc_difference": auroc_diff,
                "auroc_concordant": auroc_concordant,
                "grid_mismatch_count": len(grid_mismatches),
                "grid_mismatches": grid_mismatches
            },
            "distribution_summary_benchmark_350": {
                "in_domain_200_raw_squared": cohort_stats(in_dists),
                "in_domain_200_euclidean_sqrt": cohort_stats(np.sqrt(in_dists)),
                "ood_75_raw_squared": cohort_stats(ood_dists),
                "ood_75_euclidean_sqrt": cohort_stats(np.sqrt(ood_dists)),
                "adv_75_raw_squared": cohort_stats(adv_dists),
                "adv_75_euclidean_sqrt": cohort_stats(np.sqrt(adv_dists))
            },
            "calibration_grid_benchmark_350": diagnostic_grid,
            "legacy_sample20_diagnostic": sample20_summary,
            "verification_manifests": {
                "original_vector_db_pre_manifest": orig_pre_manifest,
                "original_vector_db_post_manifest": orig_post_manifest,
                "copied_vector_db_manifest": copied_manifest,
                "onnx_cache_pre_manifest": onnx_manifest,
                "onnx_cache_post_manifest": post_onnx_manifest,
                "analysis_copy_path": str(disposable_db_dir.relative_to(WORKSPACE_ROOT))
            },
            "query_ledger_350": query_records_350
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
            json.dump(diagnostic_payload, out_f, indent=2)
        print(f"  PASS: Diagnostic payload successfully written to: {OUTPUT_FILE}")

    except Exception as exc:
        print(f"\n[CRITICAL ERROR] Execution failed: {exc}", file=sys.stderr)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        failure_path = OUTPUT_DIR / "contemporary_distance_diagnostic_FAILED.json"
        failure_payload = {
            "status": "FAILED",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "script": {
                "path": str(Path(__file__).resolve().relative_to(WORKSPACE_ROOT)),
                "sha256": file_sha256(Path(__file__).resolve())
            },
            "analysis_copy_path": str(disposable_db_dir.relative_to(WORKSPACE_ROOT)) if 'disposable_db_dir' in locals() else None,
            "orig_pre_manifest": orig_pre_manifest if 'orig_pre_manifest' in locals() else None,
        }
        with open(failure_path, "w", encoding="utf-8") as f_fail:
            json.dump(failure_payload, f_fail, indent=2)
        print(f"  Failure artifact written to: {failure_path}", file=sys.stderr)
        raise exc

    finally:
        # Step 13: Integrity Verification of Original Assets (Executed unconditionally)
        print("\n[Step 13] Final integrity verification of original assets...")
        orig_post_manifest = dir_manifest(ORIG_DB_DIR)
        assert orig_post_manifest == orig_pre_manifest, "CRITICAL ALERT: Original vector database was modified during execution!"
        print("  PASS: Original vector store bit-invariant (zero mutation).")

        post_b350_sha = file_sha256(BENCHMARK_350_PATH)
        assert post_b350_sha == EXPECTED_BENCHMARK_350_SHA256, "CRITICAL: Benchmark 350 modified!"

        post_b175_sha = file_sha256(BENCHMARK_175_PATH)
        assert post_b175_sha == EXPECTED_BENCHMARK_175_SHA256, "CRITICAL: Benchmark 175 modified!"

        post_summary_sha = file_sha256(SAVED_SUMMARY_PATH)
        assert post_summary_sha == EXPECTED_SAVED_SUMMARY_SHA256, "CRITICAL: Saved summary modified!"
        print("  PASS: All original benchmark and summary files confirmed bit-invariant.")

        for fname in REQUIRED_ONNX_FILES:
            fpath = ONNX_CACHE_DIR / fname
            assert fpath.exists(), f"CRITICAL: ONNX cache file missing: {fname}"
            post_sha = file_sha256(fpath)
            assert post_sha == onnx_manifest[fname]["sha256"], f"CRITICAL: ONNX cache file modified: {fname}"
        print("  PASS: All 6 ONNX cache files confirmed bit-invariant.")
        print("=" * 80)
        print("DIAGNOSTIC WORKFLOW COMPLETE (NO ORIGINAL ASSETS MUTATED)")
        print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contemporary Vector Distance Diagnostic on Preserved Local Assets")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing diagnostic output file if present")
    args = parser.parse_args()
    run_diagnostic(overwrite=args.overwrite)
