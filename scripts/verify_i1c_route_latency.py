#!/usr/bin/env python3
"""
scripts/verify_i1c_route_latency.py
===================================
Pure read-only verification script for Reviewer Finding I1c (Route & Category Latencies).
Strictly decoupled from runtime engines, model APIs, ChromaDB, and network access.

Verification Standards:
  1. Exact pinned source hash verification on raw bytes before parsing.
  2. In-memory validation precedes directory creation; fresh run directory required (exist_ok=False).
  3. Exclusive file creation ('x' mode) to prevent evidence overwriting.
  4. Partial outputs preserved on write failure without overwrite fallback.
  5. Strict schema validation: non-boolean finite floats, sleep <= total, exact crosstab counts.
  6. Explicit category prefix mapping (CatA, CatB, CatC, CatD) preventing KeyErrors.
  7. Deterministic percentiles via NumPy linear interpolation (method='linear').
  8. Disaggregation across ALL (N=350), Routes (EASY N=110, HARD N=240), and Categories (A, B, C, D).
  9. Dual SD reporting: population (ddof=0, N denominator) and sample (ddof=1, N-1 denominator).
 10. Post-write and guarded finalization source rehash on both success and failure paths.
"""

import os
import sys
import json
import csv
import math
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_INPUT_FILE = ROOT_DIR / "data" / "terra_canonical_v2_eval.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "TERRA_EDITORIAL_RESTART_V2" / "evidence" / "I1c_latency"
PINNED_CANONICAL_V2_SHA256 = "95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507"

CAT_PREFIX_MAP: Dict[str, str] = {
    "A_Factual": "CatA",
    "B_Evolutionary": "CatB",
    "C_OutOfContext": "CatC",
    "D_Adversarial": "CatD"
}

EXPECTED_CROSSTAB: Dict[str, int] = {
    "A_Factual__EASY": 100,
    "B_Evolutionary__HARD": 100,
    "C_OutOfContext__HARD": 75,
    "D_Adversarial__EASY": 10,
    "D_Adversarial__HARD": 65
}


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA-256 hash of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def summarize_cohort(values: List[float]) -> Dict[str, Any]:
    """Computes exact percentiles and dual standard deviations for a cohort."""
    arr = np.array(values, dtype=float)
    n = len(arr)
    if n == 0:
        return {"n": 0}

    p25 = float(np.percentile(arr, 25, method="linear"))
    p50 = float(np.percentile(arr, 50, method="linear"))
    p75 = float(np.percentile(arr, 75, method="linear"))
    p95 = float(np.percentile(arr, 95, method="linear"))
    mean_val = float(np.mean(arr))
    pop_sd = float(np.std(arr, ddof=0))
    samp_sd = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    return {
        "n": n,
        "raw": {
            "p25": p25,
            "median": p50,
            "p75": p75,
            "p95": p95,
            "mean": mean_val,
            "pop_sd_ddof0": pop_sd,
            "sample_sd_ddof1": samp_sd,
            "min": min_val,
            "max": max_val
        },
        "display_rounded": {
            "p25": round(p25, 3),
            "median": round(p50, 3),
            "p75": round(p75, 3),
            "p95": round(p95, 3),
            "mean": round(mean_val, 3),
            "pop_sd_ddof0": round(pop_sd, 3),
            "sample_sd_ddof1": round(samp_sd, 3),
            "min": round(min_val, 3),
            "max": round(max_val, 3)
        }
    }


def verify_route_latency(
    input_path: Path,
    output_dir: Path,
    expected_sha256: Optional[str] = PINNED_CANONICAL_V2_SHA256
) -> Dict[str, Any]:
    """
    Executes pure read-only validation and ledger extraction.
    Throws explicit exceptions on any integrity failure.
    Guarantees:
      - Validates in-memory before creating output_dir.
      - Requires fresh output directory (fails if output_dir exists).
      - Uses exclusive creation ('x' mode) for all files.
      - Preserves partial files on failure.
      - Re-checks source hash post-write and in guarded finalizer on bounded lifecycle exit paths.
      - Exposes final source hashes in a small exclusive completion record after successful finalization.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # 1. Read source bytes and verify pre-read hash
    with open(input_path, "rb") as f:
        raw_bytes = f.read()

    pre_hash = compute_bytes_sha256(raw_bytes)
    if expected_sha256 is not None and pre_hash != expected_sha256:
        raise ValueError(
            f"Input SHA-256 mismatch!\n  Expected: {expected_sha256}\n  Computed: {pre_hash}"
        )

    # 2. Bounded lifecycle begins immediately after initial hash verification
    primary_exc: Optional[BaseException] = None
    post_write_hash: Optional[str] = None
    final_rehash: Optional[str] = None
    summary_content: Optional[Dict[str, Any]] = None

    try:
        # Fresh directory requirement: fail if output_dir already exists
        if output_dir.exists():
            raise FileExistsError(
                f"Target output directory already exists (fresh run directory required): {output_dir}"
            )

        # 3. Parse JSON from verified bytes
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse JSON input: {e}")

        if not isinstance(data, list):
            raise ValueError(f"Expected top-level JSON array, got {type(data).__name__}")

        terra_records = [
            r for r in data if isinstance(r, dict) and r.get("pipeline") == "5_Full_TERRA"
        ]
        if len(terra_records) != 350:
            raise ValueError(
                f"Expected exactly 350 records for pipeline '5_Full_TERRA', found {len(terra_records)}"
            )

        # 4. Strict per-row validation and cohort collection in memory
        seen_qids = set()
        cat_counts = {"A_Factual": 0, "B_Evolutionary": 0, "C_OutOfContext": 0, "D_Adversarial": 0}
        route_counts = {"EASY": 0, "HARD": 0}
        crosstab: Dict[str, int] = {}

        cohort_data: Dict[str, List[float]] = {
            "ALL_gross": [], "ALL_net": [],
            "EASY_gross": [], "EASY_net": [],
            "HARD_gross": [], "HARD_net": [],
            "CatA_gross": [], "CatA_net": [],
            "CatB_gross": [], "CatB_net": [],
            "CatC_gross": [], "CatC_net": [],
            "CatD_gross": [], "CatD_net": []
        }

        ledger_rows: List[Dict[str, Any]] = []

        for idx, r in enumerate(terra_records):
            qid = r.get("query_id")
            if not isinstance(qid, str) or not qid.strip():
                raise ValueError(f"Row {idx}: missing or empty query_id")
            if qid in seen_qids:
                raise ValueError(f"Row {idx}: duplicate query_id '{qid}'")
            seen_qids.add(qid)

            cat = r.get("category")
            if cat not in cat_counts:
                raise ValueError(f"Row {idx} ({qid}): unknown category '{cat}'")
            cat_counts[cat] += 1

            timing = r.get("timing")
            if not isinstance(timing, dict):
                raise ValueError(f"Row {idx} ({qid}): missing or invalid timing dictionary")

            route = timing.get("route_taken")
            if route not in route_counts:
                raise ValueError(f"Row {idx} ({qid}): unknown route_taken '{route}'")
            route_counts[route] += 1

            xtab_key = f"{cat}__{route}"
            crosstab[xtab_key] = crosstab.get(xtab_key, 0) + 1

            # Strict timing type and boundary checks
            if "total_ms" not in timing:
                raise ValueError(f"Row {idx} ({qid}): missing timing field 'total_ms'")
            raw_total = timing["total_ms"]
            if isinstance(raw_total, bool) or not isinstance(raw_total, (int, float)):
                raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not numeric: {raw_total}")
            total_ms = float(raw_total)
            if not math.isfinite(total_ms) or total_ms < 0.0:
                raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not finite non-negative: {total_ms}")

            if "_retry_sleep_ms" not in timing:
                raise ValueError(f"Row {idx} ({qid}): missing timing field '_retry_sleep_ms'")
            raw_sleep = timing["_retry_sleep_ms"]
            if isinstance(raw_sleep, bool) or not isinstance(raw_sleep, (int, float)):
                raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not numeric: {raw_sleep}")
            sleep_ms = float(raw_sleep)
            if not math.isfinite(sleep_ms) or sleep_ms < 0.0:
                raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not finite non-negative: {sleep_ms}")

            if sleep_ms > total_ms:
                raise ValueError(
                    f"Row {idx} ({qid}): '_retry_sleep_ms' ({sleep_ms}) exceeds 'total_ms' ({total_ms})"
                )

            net_ms = total_ms - sleep_ms
            if net_ms < 0.0:
                raise ValueError(f"Row {idx} ({qid}): net latency cannot be negative: {net_ms}")

            ledger_rows.append({
                "query_id": qid,
                "category": cat,
                "route_taken": route,
                "total_ms_gross": total_ms,
                "retry_sleep_ms": sleep_ms,
                "net_ms": net_ms
            })

            cohort_data["ALL_gross"].append(total_ms)
            cohort_data["ALL_net"].append(net_ms)
            cohort_data[f"{route}_gross"].append(total_ms)
            cohort_data[f"{route}_net"].append(net_ms)

            cat_prefix = CAT_PREFIX_MAP[cat]
            cohort_data[f"{cat_prefix}_gross"].append(total_ms)
            cohort_data[f"{cat_prefix}_net"].append(net_ms)

        # 5. Check population constants and full crosstab
        expected_cats = {"A_Factual": 100, "B_Evolutionary": 100, "C_OutOfContext": 75, "D_Adversarial": 75}
        if cat_counts != expected_cats:
            raise ValueError(f"Category counts mismatch: expected {expected_cats}, got {cat_counts}")

        expected_routes = {"EASY": 110, "HARD": 240}
        if route_counts != expected_routes:
            raise ValueError(f"Route counts mismatch: expected {expected_routes}, got {route_counts}")

        if crosstab != EXPECTED_CROSSTAB:
            raise ValueError(f"Crosstab mismatch: expected {EXPECTED_CROSSTAB}, got {crosstab}")

        # 6. Create fresh directory only AFTER in-memory validation has fully succeeded
        output_dir.mkdir(parents=True, exist_ok=False)

        # 7. Write evidence outputs exclusively
        ledger_csv_path = output_dir / "per_query_latency_ledger.csv"
        summary_json_path = output_dir / "latency_percentiles_summary.json"
        manifest_path = output_dir / "verification_manifest.sha256"

        try:
            with open(ledger_csv_path, "x", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "query_id", "category", "route_taken",
                    "total_ms_gross", "retry_sleep_ms", "net_ms"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ledger_rows)

            summary_content = {
                "metadata": {
                    "source_file": str(input_path),
                    "expected_sha256": expected_sha256,
                    "source_sha256_pre_read": pre_hash,
                    "total_queries": len(terra_records),
                    "route_counts": route_counts,
                    "category_counts": cat_counts,
                    "route_category_crosstab": crosstab,
                    "percentile_method": "linear",
                    "sd_formulas": {
                        "pop_sd_ddof0": "sqrt(sum((x - mean)^2) / N)",
                        "sample_sd_ddof1": "sqrt(sum((x - mean)^2) / (N - 1))"
                    },
                    "environment": {
                        "python_version": sys.version,
                        "numpy_version": np.__version__,
                        "script_sha256": compute_sha256(Path(__file__).resolve())
                    },
                    "executed_at_utc": datetime.now(timezone.utc).isoformat()
                },
                "cohort_summary": {k: summarize_cohort(v) for k, v in cohort_data.items()}
            }

            with open(summary_json_path, "x", encoding="utf-8") as f:
                json.dump(summary_content, f, indent=2, allow_nan=False)

            with open(manifest_path, "x", encoding="utf-8") as f:
                for p in [ledger_csv_path, summary_json_path]:
                    h = compute_sha256(p)
                    f.write(f"{h}  {p.name}\n")
        except Exception as write_err:
            raise RuntimeError(f"Error writing evidence outputs: {write_err}") from write_err

        # 8. Post-write hash immediately after output writes complete
        try:
            post_write_hash = compute_sha256(input_path)
        except Exception as rehash_err:
            raise RuntimeError(
                f"Source file became unreadable during post-write verification: {rehash_err}"
            ) from rehash_err

        if post_write_hash != pre_hash:
            raise RuntimeError(
                f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Post-write: {post_write_hash}"
            )

    except BaseException as exc:
        primary_exc = exc
        raise
    finally:
        # Guarded finalization check executed on bounded lifecycle exit
        fin_read_err: Optional[Exception] = None
        try:
            final_rehash = compute_sha256(input_path)
        except Exception as e:
            fin_read_err = e
            final_rehash = None

        if fin_read_err is not None:
            if primary_exc is None:
                raise RuntimeError(
                    f"Source file became unreadable during finalization: {fin_read_err}"
                ) from fin_read_err
            else:
                print(
                    f"[FATAL INTEGRITY ERROR] Source file became unreadable in finalizer: {fin_read_err}",
                    file=sys.stderr
                )

        if final_rehash is not None and final_rehash != pre_hash:
            drift_err = RuntimeError(
                f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Final:    {final_rehash}"
            )
            if primary_exc is None:
                raise drift_err
            else:
                print(f"[FATAL INTEGRITY DRIFT] {drift_err}", file=sys.stderr)

    # 9. Small exclusive completion record written strictly AFTER successful finalization
    completion_record_path = output_dir / "completion_record.json"
    completion_record = {
        "status": "SUCCESS",
        "source_file": str(input_path.resolve()),
        "expected_sha256": expected_sha256,
        "source_sha256_pre_read": pre_hash,
        "source_sha256_post_write": post_write_hash,
        "source_sha256_final": final_rehash,
        "integrity_verified": True,
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_directory": str(output_dir.resolve()),
        "ledger_csv": "per_query_latency_ledger.csv",
        "summary_json": "latency_percentiles_summary.json",
        "manifest": "verification_manifest.sha256"
    }
    with open(completion_record_path, "x", encoding="utf-8") as f:
        json.dump(completion_record, f, indent=2, allow_nan=False)

    return summary_content


def main():
    parser = argparse.ArgumentParser(
        description="Verify route & category latency on canonical v2 data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Path to canonical v2 evaluation JSON."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Target evidence directory for exported files (must be fresh)."
    )
    parser.add_argument(
        "--expected-hash",
        type=str,
        default=PINNED_CANONICAL_V2_SHA256,
        help="Expected SHA-256 hash of input file."
    )
    args = parser.parse_args()

    print("=" * 80)
    print("VERIFY ROUTE & CATEGORY LATENCY (I1c)")
    print("=" * 80)
    print(f"Input file:     {args.input}")
    print(f"Output dir:     {args.output_dir}")
    print(f"Expected hash:  {args.expected_hash}")

    try:
        result = verify_route_latency(
            input_path=args.input,
            output_dir=args.output_dir,
            expected_sha256=args.expected_hash
        )

        print("\n[SUCCESS] Verification complete. Cohort summary counts:")
        for cohort, stats in result["cohort_summary"].items():
            print(f"  {cohort:<12}: N={stats['n']:<3} median={stats['display_rounded']['median']} ms")
        print(f"\n[RECORD] Completion record written to: {args.output_dir / 'completion_record.json'}")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAILURE] Verification failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
