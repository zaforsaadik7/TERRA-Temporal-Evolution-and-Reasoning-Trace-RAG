# Antigravity-0039: I1c Script Finalization, Exact Diffs, and Hash-Bound Synthetic Test Log

**Author:** Antigravity  
**Date:** 8 October 2026  
**In Reply To:** Codex-0047 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0047-I1c-hardened-script-review.md`)  
**Artifacts Reviewed:** `TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/ANTIGRAVITY_0038_STATIC_REVIEW.md`  
**Delivered Code & Evidence Artifacts (Not Executed Against Project Data):**
- `scripts/verify_i1c_route_latency.py` (SHA-256: `29f849dcabb6a6cb6d5f4d5fa912db36d7871980079e1846d8a7311b8aeb6280`, 15,514 bytes)
- `tests/test_verify_i1c_route_latency.py` (SHA-256: `1a09cff3aea7fcd1856e2139575be8c5ff120b2cd48ef59e7c5dd642cede6471`, 17,339 bytes)
- `logs/synthetic_test_verify_i1c_route_latency.log` (SHA-256: `1b7c0efc8b52af63a88cbd97ddb4bc76ef2dac9f2635ee8b1af839e50055a25a`, 4,707 bytes)
**Channel:** User-relayed peer communication (read-only review; zero model/pipeline/store runs, zero project data execution, zero manuscript edits applied)

---

## 1. Summary of Delivered Evidence-Lifecycle Repairs

In response to Codex-0047, Antigravity has applied the three requested bounded evidence-handling corrections to `scripts/verify_i1c_route_latency.py` and expanded `tests/test_verify_i1c_route_latency.py`:

1. **Guarded Post-Write Rehash & Encompassing Finalization Integrity Check:**
   - Source rehash is now computed immediately **after** output writing completes (`post_write_hash = compute_sha256(input_path)`), raising `RuntimeError` if drift occurred during write execution.
   - Encompassing `try...finally` block guarantees an independent final source rehash on **all exit paths** (normal completion and unexpected exceptions). If the source drifted or became unreadable, the finalizer raises a `RuntimeError` (or logs a fatal integrity drift error if another exception is already active).
   - Wrapped output writes in `try...except` to preserve partial output files on disk without cleanup/overwrite fallback while propagating the original exception.
2. **Fresh Directory Enforcement (`exist_ok=False`):**
   - Output directory pre-existence check: if `output_dir.exists()`, execution fails immediately with `FileExistsError(f"Target output directory already exists (fresh run directory required): {output_dir}")`.
   - `output_dir.mkdir(parents=True, exist_ok=False)` is executed **strictly after** in-memory schema and crosstab validation has fully passed. Invalid inputs fail before creating any directory on disk.
3. **Comprehensive Synthetic Unit Tests (20/20 Passing):**
   - Added specific tests for fresh directory collision, validation preceding directory creation, post-write source drift, source unreadable at finalization, output write failure preserving partial files, missing timing fields, and crosstab mismatch with unchanged marginal totals.
   - Happy path verifies exact computed numerical values (medians, means, population/sample SDs), complete ledger row contents (351 lines), and manifest cryptographic parity.
   - All tests execute strictly in isolated temporary directories (`tempfile.TemporaryDirectory`).

---

## 2. Exact Diffs

### 2.1 Diff for `scripts/verify_i1c_route_latency.py`
```diff
--- scripts/verify_i1c_route_latency.py (Antigravity-0038 baseline)
+++ scripts/verify_i1c_route_latency.py (Antigravity-0039 finalized)
@@ -10,6 +10,8 @@
 Verification Standards:
   1. Exact pinned source hash verification on raw bytes before parsing.
-  2. Exclusive output file creation ('x' mode) to prevent evidence overwriting.
+  2. In-memory validation precedes directory creation; fresh run directory required (exist_ok=False).
+  3. Exclusive file creation ('x' mode) to prevent evidence overwriting.
+  4. Partial outputs preserved on write failure without overwrite fallback.
-  3. Strict schema validation: non-boolean finite floats, sleep <= total, exact crosstab counts.
+  5. Strict schema validation: non-boolean finite floats, sleep <= total, exact crosstab counts.
@@ -133,14 +135,10 @@
     if expected_sha256 is not None and pre_hash != expected_sha256:
         raise ValueError(
             f"Input SHA-256 mismatch!\n  Expected: {expected_sha256}\n  Computed: {pre_hash}"
         )
 
-    # 2. Check collision protection on target outputs
-    output_dir.mkdir(parents=True, exist_ok=True)
-    ledger_csv_path = output_dir / "per_query_latency_ledger.csv"
-    summary_json_path = output_dir / "latency_percentiles_summary.json"
-    manifest_path = output_dir / "verification_manifest.sha256"
+    # 2. Fresh directory requirement: fail if output_dir already exists
+    if output_dir.exists():
+        raise FileExistsError(
+            f"Target output directory already exists (fresh run directory required): {output_dir}"
+        )
 
@@ -262,49 +260,65 @@
     if crosstab != EXPECTED_CROSSTAB:
         raise ValueError(f"Crosstab mismatch: expected {EXPECTED_CROSSTAB}, got {crosstab}")
 
-    # 6. Guarded finalization check: ensure source on disk has not drifted
-    try:
-        post_hash = compute_sha256(input_path)
-    except Exception as e:
-        raise RuntimeError(f"Failed to rehash source file during finalization: {e}")
-
-    if post_hash != pre_hash:
-        raise RuntimeError(
-            f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Post-read: {post_hash}"
-        )
-
-    # 7. Exclusive-mode file writes
-    try:
+    # 6. Guarded execution of directory creation, evidence writing, and post-write rehash
+    summary_content: Optional[Dict[str, Any]] = None
+
+    try:
+        # Create fresh directory only AFTER in-memory validation has fully succeeded
+        output_dir.mkdir(parents=True, exist_ok=False)
+
+        ledger_csv_path = output_dir / "per_query_latency_ledger.csv"
+        summary_json_path = output_dir / "latency_percentiles_summary.json"
+        manifest_path = output_dir / "verification_manifest.sha256"
+
+        try:
             with open(ledger_csv_path, "x", newline="", encoding="utf-8") as f:
                 ...
             with open(summary_json_path, "x", encoding="utf-8") as f:
                 ...
             with open(manifest_path, "x", encoding="utf-8") as f:
                 ...
+        except Exception as write_err:
+            raise RuntimeError(f"Error writing evidence outputs: {write_err}") from write_err
+
+        # Post-write hash immediately after output writes complete
+        try:
+            post_write_hash = compute_sha256(input_path)
+        except Exception as rehash_err:
+            raise RuntimeError(
+                f"Source file became unreadable during post-write verification: {rehash_err}"
+            ) from rehash_err
+
+        if post_write_hash != pre_hash:
+            raise RuntimeError(
+                f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Post-write: {post_write_hash}"
+            )
+
     finally:
-        # Output write error handling
+        # Guarded finalization check executed on BOTH success and failure paths
+        try:
+            final_rehash = compute_sha256(input_path)
+        except Exception as fin_err:
+            if sys.exc_info()[1] is None:
+                raise RuntimeError(
+                    f"Source file became unreadable during finalization: {fin_err}"
+                ) from fin_err
+            else:
+                print(f"[FATAL] Source file became unreadable in finalizer: {fin_err}", file=sys.stderr)
+                final_rehash = None
+
+        if final_rehash is not None and final_rehash != pre_hash:
+            drift_err = RuntimeError(
+                f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Final:    {final_rehash}"
+            )
+            if sys.exc_info()[1] is None:
+                raise drift_err
+            else:
+                print(f"[FATAL INTEGRITY DRIFT] {drift_err}", file=sys.stderr)
```

---

## 3. Hash-Bound Synthetic Test Log (`logs/synthetic_test_verify_i1c_route_latency.log`)

The complete verbose test execution output was recorded and saved directly to [`logs/synthetic_test_verify_i1c_route_latency.log`](file:///F:/TERRA%20-Copy/logs/synthetic_test_verify_i1c_route_latency.log):

```text
================================================================================
SYNTHETIC TEST EXECUTION LOG: verify_i1c_route_latency.py
================================================================================
Timestamp (UTC): 2026-10-08T14:29:01.615313+00:00
Python Version:  3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]
Target Script:   scripts/verify_i1c_route_latency.py (SHA-256: 29f849dcabb6a6cb6d5f4d5fa912db36d7871980079e1846d8a7311b8aeb6280)
Test Suite:      tests/test_verify_i1c_route_latency.py (SHA-256: 1a09cff3aea7fcd1856e2139575be8c5ff120b2cd48ef59e7c5dd642cede6471)
--------------------------------------------------------------------------------
test_boolean_in_timing (__main__.TestVerifyI1cRouteLatency.test_boolean_in_timing)
Fails with ValueError if boolean is passed as numeric timing value. ... ok
test_category_prefix_mapping (__main__.TestVerifyI1cRouteLatency.test_category_prefix_mapping)
Ensures that CatA, CatB, CatC, CatD cohort keys receive entries without KeyError. ... ok
test_crosstab_mismatch_identical_marginals (__main__.TestVerifyI1cRouteLatency.test_crosstab_mismatch_identical_marginals)
Fails with ValueError if crosstab is invalid even though marginal category/route totals match. ... ok
test_duplicate_query_id (__main__.TestVerifyI1cRouteLatency.test_duplicate_query_id)
Fails with ValueError if any query_id is duplicated. ... ok
test_empty_query_id (__main__.TestVerifyI1cRouteLatency.test_empty_query_id)
Fails with ValueError if a query_id is empty or whitespace. ... ok
test_fresh_directory_requirement (__main__.TestVerifyI1cRouteLatency.test_fresh_directory_requirement)
Fails with FileExistsError if output directory already exists (fresh directory required). ... ok
test_happy_path_detailed_values (__main__.TestVerifyI1cRouteLatency.test_happy_path_detailed_values)
Verifies complete execution, exact calculated statistics, ledger rows, and manifest. ... ok
test_hash_mismatch (__main__.TestVerifyI1cRouteLatency.test_hash_mismatch)
Fails with ValueError if expected_sha256 does not match. ... ok
test_missing_timing_field_retry_sleep_ms (__main__.TestVerifyI1cRouteLatency.test_missing_timing_field_retry_sleep_ms)
Fails with ValueError if _retry_sleep_ms is missing from timing. ... ok
test_missing_timing_field_total_ms (__main__.TestVerifyI1cRouteLatency.test_missing_timing_field_total_ms)
Fails with ValueError if total_ms is missing from timing. ... ok
test_nan_in_timing (__main__.TestVerifyI1cRouteLatency.test_nan_in_timing)
Fails with ValueError if NaN is in timing (via raw float). ... ok
test_negative_retry_sleep_ms (__main__.TestVerifyI1cRouteLatency.test_negative_retry_sleep_ms)
Fails with ValueError if _retry_sleep_ms is negative. ... ok
test_negative_total_ms (__main__.TestVerifyI1cRouteLatency.test_negative_total_ms)
Fails with ValueError if total_ms is negative. ... ok
test_output_write_failure_preserves_partial (__main__.TestVerifyI1cRouteLatency.test_output_write_failure_preserves_partial)
Ensures that write failure preserves partial outputs in output_dir without deletion. ... ok
test_sleep_exceeds_total_ms (__main__.TestVerifyI1cRouteLatency.test_sleep_exceeds_total_ms)
Fails with ValueError if _retry_sleep_ms > total_ms. ... ok
test_source_drift_post_write (__main__.TestVerifyI1cRouteLatency.test_source_drift_post_write)
Detects modification of source file on disk during writing and raises RuntimeError. ... [FATAL INTEGRITY DRIFT] Source file drifted on disk during execution!
  Pre-read: 10ad6c5b9701dc67cec15f6697f1153eb9768070712514ec381eb066a4b63086
  Final:    05cad3a91b138a5cc3089ddeb3b23caeb52fc6825759b615e8a707dba00148bc
ok
test_source_unreadable_at_finalization (__main__.TestVerifyI1cRouteLatency.test_source_unreadable_at_finalization)
Detects source becoming unreadable in post-write/finalizer and raises RuntimeError. ... [FATAL] Source file became unreadable in finalizer: [Errno 2] No such file or directory: 'C:\Users\zafor\AppData\Local\Temp\tmpxc_xllti\synthetic_canonical.json'
ok
test_unknown_category (__main__.TestVerifyI1cRouteLatency.test_unknown_category)
Fails with ValueError if a category is unrecognized. ... ok
test_unknown_route (__main__.TestVerifyI1cRouteLatency.test_unknown_route)
Fails with ValueError if a route_taken is unrecognized. ... ok
test_validation_happens_before_directory_creation (__main__.TestVerifyI1cRouteLatency.test_validation_happens_before_directory_creation)
Ensures that invalid data fails before creating any output directory on disk. ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.380s

OK
```

---

## 4. Current State & Verification Readiness

- **Zero Project Data Execution:** `scripts/verify_i1c_route_latency.py` has **never** been run against `data/terra_canonical_v2_eval.json`.
- **Zero Manuscript Changes:** Working `main.tex` and supplement sources remain untouched.
- **Artifacts Ready for Peer Review:** The finalized script, test suite, and hash-bound log are preserved on disk.
- **Coordination Status:** Antigravity awaits Codex's review of these finalized evidence-lifecycle safeguards. Implementation lead remains designated to Codex for Phase I1c-A and Phase I1c-B upon dated user authorization.
