#!/usr/bin/env python3
"""
tests/test_verify_i1c_route_latency.py
======================================
Comprehensive synthetic unit test suite for scripts/verify_i1c_route_latency.py.
Runs strictly in isolated temporary directories. Zero interaction with real project data.
"""

import io
import os
import sys
import json
import math
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.verify_i1c_route_latency import (
    verify_route_latency,
    compute_bytes_sha256,
    compute_sha256,
    main
)

_orig_json_dump = json.dump


def make_synthetic_350_dataset() -> list[dict]:
    """Generates a valid synthetic 350-query dataset meeting all schema constraints."""
    records = []
    # A_Factual: 100 EASY
    for i in range(1, 101):
        records.append({
            "pipeline": "5_Full_TERRA",
            "query_id": f"A{i:03d}",
            "category": "A_Factual",
            "timing": {"route_taken": "EASY", "total_ms": 5000.0 + i, "_retry_sleep_ms": 100.0}
        })
    # B_Evolutionary: 100 HARD
    for i in range(1, 101):
        records.append({
            "pipeline": "5_Full_TERRA",
            "query_id": f"B{i:03d}",
            "category": "B_Evolutionary",
            "timing": {"route_taken": "HARD", "total_ms": 15000.0 + i, "_retry_sleep_ms": 200.0}
        })
    # C_OutOfContext: 75 HARD
    for i in range(1, 76):
        records.append({
            "pipeline": "5_Full_TERRA",
            "query_id": f"C{i:03d}",
            "category": "C_OutOfContext",
            "timing": {"route_taken": "HARD", "total_ms": 2000.0 + i, "_retry_sleep_ms": 0.0}
        })
    # D_Adversarial: 10 EASY, 65 HARD
    for i in range(1, 11):
        records.append({
            "pipeline": "5_Full_TERRA",
            "query_id": f"D{i:03d}",
            "category": "D_Adversarial",
            "timing": {"route_taken": "EASY", "total_ms": 8000.0 + i, "_retry_sleep_ms": 50.0}
        })
    for i in range(11, 76):
        records.append({
            "pipeline": "5_Full_TERRA",
            "query_id": f"D{i:03d}",
            "category": "D_Adversarial",
            "timing": {"route_taken": "HARD", "total_ms": 12000.0 + i, "_retry_sleep_ms": 150.0}
        })
    return records


class TestVerifyI1cRouteLatency(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)
        self.valid_data = make_synthetic_350_dataset()
        self.input_file = self.tmp_path / "synthetic_canonical.json"
        self.output_dir = self.tmp_path / "evidence_out"

        raw_bytes = json.dumps(self.valid_data).encode("utf-8")
        with open(self.input_file, "wb") as f:
            f.write(raw_bytes)
        self.valid_hash = compute_bytes_sha256(raw_bytes)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_happy_path_detailed_values(self):
        """Verifies complete execution, exact calculated statistics, ledger rows, manifest, and completion record."""
        result = verify_route_latency(
            input_path=self.input_file,
            output_dir=self.output_dir,
            expected_sha256=self.valid_hash
        )

        cohorts = result["cohort_summary"]
        expected_cohort_keys = {
            "ALL_gross", "ALL_net", "EASY_gross", "EASY_net", "HARD_gross", "HARD_net",
            "CatA_gross", "CatA_net", "CatB_gross", "CatB_net",
            "CatC_gross", "CatC_net", "CatD_gross", "CatD_net"
        }
        self.assertEqual(set(cohorts.keys()), expected_cohort_keys)

        self.assertEqual(cohorts["ALL_gross"]["n"], 350)
        self.assertEqual(cohorts["ALL_net"]["n"], 350)
        self.assertEqual(cohorts["EASY_gross"]["n"], 110)
        self.assertEqual(cohorts["EASY_net"]["n"], 110)
        self.assertEqual(cohorts["HARD_gross"]["n"], 240)
        self.assertEqual(cohorts["HARD_net"]["n"], 240)
        self.assertEqual(cohorts["CatA_gross"]["n"], 100)
        self.assertEqual(cohorts["CatA_net"]["n"], 100)
        self.assertEqual(cohorts["CatB_gross"]["n"], 100)
        self.assertEqual(cohorts["CatB_net"]["n"], 100)
        self.assertEqual(cohorts["CatC_gross"]["n"], 75)
        self.assertEqual(cohorts["CatC_net"]["n"], 75)
        self.assertEqual(cohorts["CatD_gross"]["n"], 75)
        self.assertEqual(cohorts["CatD_net"]["n"], 75)

        # Check exact synthetic statistics for CatA net (5000 + i - 100 = 4900 + i for i=1..100)
        # Median of 4901..5000 is 4950.5, mean is 4950.5
        # Pop SD is sqrt((100^2 - 1) / 12) = sqrt(833.25) ≈ 28.86607
        # Sample SD (ddof=1) is sqrt(83325 / 99) = sqrt(841.6667) ≈ 29.01149
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["median"], 4950.5, places=3)
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["p25"], 4925.75, places=3)
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["p75"], 4975.25, places=3)
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["mean"], 4950.5, places=3)
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["pop_sd_ddof0"], math.sqrt(9999.0 / 12.0), places=3)
        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["sample_sd_ddof1"], math.sqrt(83325.0 / 99.0), places=3)

        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["median"], 4950.5)
        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["p25"], 4925.75)
        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["p75"], 4975.25)
        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["mean"], 4950.5)
        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["pop_sd_ddof0"], 28.866)
        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["sample_sd_ddof1"], 29.011)

        # Verify output files exist
        ledger_path = self.output_dir / "per_query_latency_ledger.csv"
        summary_path = self.output_dir / "latency_percentiles_summary.json"
        manifest_path = self.output_dir / "verification_manifest.sha256"
        completion_path = self.output_dir / "completion_record.json"

        self.assertTrue(ledger_path.exists())
        self.assertTrue(summary_path.exists())
        self.assertTrue(manifest_path.exists())
        self.assertTrue(completion_path.exists())

        # Check ledger lines (350 records + 1 header = 351 lines) and verify samples across categories
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 351)
        self.assertEqual(lines[0], "query_id,category,route_taken,total_ms_gross,retry_sleep_ms,net_ms")
        self.assertEqual(lines[1], "A001,A_Factual,EASY,5001.0,100.0,4901.0")
        self.assertEqual(lines[100], "A100,A_Factual,EASY,5100.0,100.0,5000.0")
        self.assertEqual(lines[101], "B001,B_Evolutionary,HARD,15001.0,200.0,14801.0")
        self.assertEqual(lines[201], "C001,C_OutOfContext,HARD,2001.0,0.0,2001.0")
        self.assertEqual(lines[276], "D001,D_Adversarial,EASY,8001.0,50.0,7951.0")
        self.assertEqual(lines[350], "D075,D_Adversarial,HARD,12075.0,150.0,11925.0")

        # Verify all 350 queries in ledger are unique and match synthetic IDs
        ledger_qids = [l.split(",")[0] for l in lines[1:]]
        self.assertEqual(len(ledger_qids), 350)
        self.assertEqual(len(set(ledger_qids)), 350)

        # Check manifest matches file hashes
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(manifest_lines), 2)
        expected_ledger_h = compute_sha256(ledger_path)
        expected_summary_h = compute_sha256(summary_path)
        self.assertIn(f"{expected_ledger_h}  per_query_latency_ledger.csv", manifest_lines)
        self.assertIn(f"{expected_summary_h}  latency_percentiles_summary.json", manifest_lines)

        # Check completion record contents
        with open(completion_path, "r", encoding="utf-8") as f:
            record = json.load(f)
        self.assertEqual(record["status"], "SUCCESS")
        self.assertEqual(record["source_sha256_pre_read"], self.valid_hash)
        self.assertEqual(record["source_sha256_post_write"], self.valid_hash)
        self.assertEqual(record["source_sha256_final"], self.valid_hash)
        self.assertTrue(record["integrity_verified"])
        self.assertEqual(record["ledger_csv"], "per_query_latency_ledger.csv")
        self.assertEqual(record["summary_json"], "latency_percentiles_summary.json")
        self.assertEqual(record["manifest"], "verification_manifest.sha256")

    def test_fresh_directory_requirement(self):
        """Fails with FileExistsError if output directory already exists (fresh directory required)."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(FileExistsError) as ctx:
            verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
        self.assertIn("fresh run directory required", str(ctx.exception))

    def test_validation_happens_before_directory_creation(self):
        """Ensures that invalid data fails before creating any output directory on disk."""
        bad_data = make_synthetic_350_dataset()
        bad_data[1]["query_id"] = bad_data[0]["query_id"]  # Duplicate QID
        bad_file = self.tmp_path / "dup_before_mkdir.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        target_dir = self.tmp_path / "must_not_be_created"
        with self.assertRaises(ValueError):
            verify_route_latency(bad_file, target_dir, expected_sha256=None)
        self.assertFalse(target_dir.exists())

    def test_category_prefix_mapping(self):
        """Ensures that CatA, CatB, CatC, CatD cohort keys receive entries without KeyError."""
        result = verify_route_latency(
            input_path=self.input_file,
            output_dir=self.output_dir,
            expected_sha256=self.valid_hash
        )
        self.assertEqual(result["cohort_summary"]["CatA_gross"]["n"], 100)
        self.assertEqual(result["cohort_summary"]["CatB_gross"]["n"], 100)
        self.assertEqual(result["cohort_summary"]["CatC_gross"]["n"], 75)
        self.assertEqual(result["cohort_summary"]["CatD_gross"]["n"], 75)

    def test_duplicate_query_id(self):
        """Fails with ValueError if any query_id is duplicated."""
        bad_data = make_synthetic_350_dataset()
        bad_data[1]["query_id"] = bad_data[0]["query_id"]
        bad_file = self.tmp_path / "dup_qid.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("duplicate query_id", str(ctx.exception))

    def test_empty_query_id(self):
        """Fails with ValueError if a query_id is empty or whitespace."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["query_id"] = "   "
        bad_file = self.tmp_path / "empty_qid.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("missing or empty query_id", str(ctx.exception))

    def test_unknown_category(self):
        """Fails with ValueError if a category is unrecognized."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["category"] = "UnknownCategory"
        bad_file = self.tmp_path / "bad_cat.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("unknown category", str(ctx.exception))

    def test_unknown_route(self):
        """Fails with ValueError if a route_taken is unrecognized."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["route_taken"] = "MEDIUM"
        bad_file = self.tmp_path / "bad_route.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("unknown route_taken", str(ctx.exception))

    def test_missing_timing_field_total_ms(self):
        """Fails with ValueError if total_ms is missing from timing."""
        bad_data = make_synthetic_350_dataset()
        del bad_data[0]["timing"]["total_ms"]
        bad_file = self.tmp_path / "missing_total.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("missing timing field 'total_ms'", str(ctx.exception))

    def test_missing_timing_field_retry_sleep_ms(self):
        """Fails with ValueError if _retry_sleep_ms is missing from timing."""
        bad_data = make_synthetic_350_dataset()
        del bad_data[0]["timing"]["_retry_sleep_ms"]
        bad_file = self.tmp_path / "missing_sleep.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("missing timing field '_retry_sleep_ms'", str(ctx.exception))

    def test_negative_total_ms(self):
        """Fails with ValueError if total_ms is negative."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["total_ms"] = -5.0
        bad_file = self.tmp_path / "neg_total.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("is not finite non-negative", str(ctx.exception))

    def test_negative_retry_sleep_ms(self):
        """Fails with ValueError if _retry_sleep_ms is negative."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["_retry_sleep_ms"] = -1.0
        bad_file = self.tmp_path / "neg_sleep.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("is not finite non-negative", str(ctx.exception))

    def test_sleep_exceeds_total_ms(self):
        """Fails with ValueError if _retry_sleep_ms > total_ms."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["total_ms"] = 100.0
        bad_data[0]["timing"]["_retry_sleep_ms"] = 200.0
        bad_file = self.tmp_path / "sleep_exceeds.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("exceeds 'total_ms'", str(ctx.exception))

    def test_boolean_in_timing(self):
        """Fails with ValueError if boolean is passed as numeric timing value."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["total_ms"] = True
        bad_file = self.tmp_path / "bool_timing.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("is not numeric", str(ctx.exception))

    def test_nan_in_timing(self):
        """Fails with ValueError if NaN is in timing (via raw float)."""
        bad_data = make_synthetic_350_dataset()
        bad_data[0]["timing"]["total_ms"] = float("nan")
        bad_file = self.tmp_path / "nan_timing.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(bad_data).replace('NaN', 'NaN'))

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("is not finite non-negative", str(ctx.exception))

    def test_hash_mismatch(self):
        """Fails with ValueError if expected_sha256 does not match."""
        wrong_hash = "0" * 64
        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(
                input_path=self.input_file,
                output_dir=self.output_dir,
                expected_sha256=wrong_hash
            )
        self.assertIn("Input SHA-256 mismatch", str(ctx.exception))

    def test_crosstab_mismatch_identical_marginals(self):
        """Fails with ValueError if crosstab is invalid even though marginal category/route totals match."""
        bad_data = make_synthetic_350_dataset()
        # Find one A_Factual (EASY) and switch it to HARD
        for r in bad_data:
            if r["category"] == "A_Factual":
                r["timing"]["route_taken"] = "HARD"
                break
        # Find one B_Evolutionary (HARD) and switch it to EASY
        for r in bad_data:
            if r["category"] == "B_Evolutionary":
                r["timing"]["route_taken"] = "EASY"
                break

        bad_file = self.tmp_path / "xtab_mismatch.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        with self.assertRaises(ValueError) as ctx:
            verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
        self.assertIn("Crosstab mismatch", str(ctx.exception))

    def test_source_drift_post_write(self):
        """Detects modification of source file on disk during writing and raises RuntimeError."""
        def modify_source_during_write(*args, **kwargs):
            _orig_json_dump(*args, **kwargs)
            with open(self.input_file, "ab") as f:
                f.write(b"drift")

        with patch("json.dump", side_effect=modify_source_during_write):
            with self.assertRaises(RuntimeError) as ctx:
                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
            self.assertIn("Source file drifted on disk", str(ctx.exception))
        # Completion record must NOT have been written
        self.assertFalse((self.output_dir / "completion_record.json").exists())

    def test_finalizer_only_unreadable_raises_and_no_success(self):
        """Specifically exercises Defect 1: post-write hash succeeds, but finalizer hash fails.
        Must raise RuntimeError and must NOT return success or create completion_record.json."""
        orig_compute_sha256 = compute_sha256
        input_calls = 0

        def mocked_compute_sha256(path):
            nonlocal input_calls
            p = Path(path).resolve()
            if p == self.input_file.resolve():
                input_calls += 1
                if input_calls == 1:
                    # 1st call on input_path is post-write check: succeeds!
                    return orig_compute_sha256(path)
                elif input_calls >= 2:
                    # 2nd call on input_path is finalizer check: raises!
                    raise OSError("Simulated finalizer-only disk unreadability")
            return orig_compute_sha256(path)

        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=mocked_compute_sha256):
            with self.assertRaises(RuntimeError) as ctx:
                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
            self.assertIn("Source file became unreadable during finalization", str(ctx.exception))

        # Must NOT have created completion_record.json
        self.assertFalse((self.output_dir / "completion_record.json").exists())

    def test_finalizer_only_drift_raises_and_no_success(self):
        """Specifically exercises finalizer-only drift: post-write hash succeeds, but source drifts before finalizer."""
        orig_compute_sha256 = compute_sha256
        input_calls = 0

        def mocked_compute_sha256(path):
            nonlocal input_calls
            p = Path(path).resolve()
            if p == self.input_file.resolve():
                input_calls += 1
                if input_calls == 1:
                    # 1st call on input_path is post-write check: succeeds!
                    return orig_compute_sha256(path)
                elif input_calls >= 2:
                    # 2nd call on input_path is finalizer check: simulated drifted hash!
                    return "f" * 64
            return orig_compute_sha256(path)

        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=mocked_compute_sha256):
            with self.assertRaises(RuntimeError) as ctx:
                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
            self.assertIn("Source file drifted on disk during execution!", str(ctx.exception))

        # Must NOT have created completion_record.json
        self.assertFalse((self.output_dir / "completion_record.json").exists())

    def test_validation_failure_executes_final_rehash(self):
        """Specifically exercises Defect 2: validation failure must still execute final rehash."""
        bad_data = make_synthetic_350_dataset()
        bad_data[1]["query_id"] = bad_data[0]["query_id"]  # Duplicate QID
        bad_file = self.tmp_path / "bad_val_rehash.json"
        raw_b = json.dumps(bad_data).encode("utf-8")
        with open(bad_file, "wb") as f:
            f.write(raw_b)

        orig_compute_sha256 = compute_sha256
        rehash_called = False

        def spy_compute_sha256(path):
            nonlocal rehash_called
            if Path(path).resolve() == bad_file.resolve():
                rehash_called = True
            return orig_compute_sha256(path)

        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
            with self.assertRaises(ValueError) as ctx:
                verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
            self.assertIn("duplicate query_id", str(ctx.exception))

        self.assertTrue(rehash_called, "Final rehash must execute even when validation fails!")
        self.assertFalse(self.output_dir.exists())

    def test_validation_failure_with_source_drift_preserves_primary_and_logs(self):
        """Ensures that when validation fails and source drifts, primary exception is raised and drift is logged."""
        bad_data = make_synthetic_350_dataset()
        bad_data[1]["query_id"] = bad_data[0]["query_id"]
        bad_file = self.tmp_path / "bad_val_drift.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        orig_compute_sha256 = compute_sha256

        def drift_compute_sha256(path):
            if Path(path).resolve() == bad_file.resolve():
                return "d" * 64  # drifted hash
            return orig_compute_sha256(path)

        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=drift_compute_sha256):
                with self.assertRaises(ValueError) as ctx:
                    verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
                self.assertIn("duplicate query_id", str(ctx.exception))

        self.assertIn("[FATAL INTEGRITY DRIFT]", stderr_capture.getvalue())

    def test_validation_failure_with_unreadable_source_preserves_primary_and_logs(self):
        """Ensures that when validation fails and source is unreadable at finalizer, primary exception is preserved."""
        bad_data = make_synthetic_350_dataset()
        bad_data[1]["query_id"] = bad_data[0]["query_id"]
        bad_file = self.tmp_path / "bad_val_unreadable.json"
        with open(bad_file, "w", encoding="utf-8") as f:
            json.dump(bad_data, f)

        orig_compute_sha256 = compute_sha256

        def unreadable_compute_sha256(path):
            if Path(path).resolve() == bad_file.resolve():
                raise OSError("Disk unreadable in finalizer")
            return orig_compute_sha256(path)

        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=unreadable_compute_sha256):
                with self.assertRaises(ValueError) as ctx:
                    verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
                self.assertIn("duplicate query_id", str(ctx.exception))

        self.assertIn("[FATAL INTEGRITY ERROR]", stderr_capture.getvalue())

    def test_directory_collision_executes_final_rehash(self):
        """Ensures that pre-existing directory collision still triggers bounded finalization rehash."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        orig_compute_sha256 = compute_sha256
        rehash_called = False

        def spy_compute_sha256(path):
            nonlocal rehash_called
            if Path(path).resolve() == self.input_file.resolve():
                rehash_called = True
            return orig_compute_sha256(path)

        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
            with self.assertRaises(FileExistsError) as ctx:
                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
            self.assertIn("fresh run directory required", str(ctx.exception))

        self.assertTrue(rehash_called, "Final rehash must execute even when directory collision occurs!")

    def test_output_write_failure_preserves_partial_and_executes_final_rehash(self):
        """Ensures that write failure preserves partial outputs without deletion AND executes final rehash."""
        orig_compute_sha256 = compute_sha256
        final_rehash_called = False

        def fail_json_write(*args, **kwargs):
            raise IOError("Simulated disk error during JSON write")

        def spy_compute_sha256(path):
            nonlocal final_rehash_called
            if Path(path).resolve() == self.input_file.resolve():
                final_rehash_called = True
            return orig_compute_sha256(path)

        with patch("json.dump", side_effect=fail_json_write):
            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
                with self.assertRaises(RuntimeError) as ctx:
                    verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
                self.assertIn("Error writing evidence outputs", str(ctx.exception))

        # Partial CSV output must be preserved in output_dir
        ledger_path = self.output_dir / "per_query_latency_ledger.csv"
        self.assertTrue(ledger_path.exists())
        self.assertGreater(ledger_path.stat().st_size, 0)
        self.assertTrue(final_rehash_called, "Final rehash must execute even when write fails!")
        self.assertFalse((self.output_dir / "completion_record.json").exists())

    def test_cli_main_success_and_failure_exit_codes(self):
        """Ensures CLI main exits with 0 on success and 1 on error, writing completion record and messages."""
        fresh_out = self.tmp_path / "cli_fresh_out"
        test_argv_success = [
            "verify_i1c_route_latency.py",
            "--input", str(self.input_file),
            "--output-dir", str(fresh_out),
            "--expected-hash", self.valid_hash
        ]
        with patch("sys.argv", test_argv_success):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 0)
        self.assertTrue((fresh_out / "completion_record.json").exists())

        # Test failure: rerun on same directory (collision) must exit code 1
        stderr_capture = io.StringIO()
        with patch("sys.argv", test_argv_success):
            with patch("sys.stderr", stderr_capture):
                with self.assertRaises(SystemExit) as ctx:
                    main()
                self.assertEqual(ctx.exception.code, 1)
        self.assertIn("Verification failed", stderr_capture.getvalue())


if __name__ == "__main__":
    unittest.main()
