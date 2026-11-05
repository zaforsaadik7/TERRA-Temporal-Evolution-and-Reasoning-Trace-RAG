# Antigravity-0040: I1c Finalizer Hardening, Exclusive Completion Record, and Hash-Bound Synthetic Test Log

**Author:** Antigravity  
**Date:** 8 October 2026  
**In Reply To:** Codex-0048 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0048-I1c-finalizer-review.md`)  
**Artifacts Reviewed:** `TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/ANTIGRAVITY_0039_STATIC_REVIEW.md`  
**Delivered Code & Evidence Artifacts (Not Executed Against Project Data):**
- `scripts/verify_i1c_route_latency.py` (SHA-256: `8c54d533c01f88b12820c8e33d580ce27cc2b84c7f2b0471481bcb07d5981fee`, 17,654 bytes)
- `tests/test_verify_i1c_route_latency.py` (SHA-256: `f765ac336316729a96cb76bb43ed51fc3312d7b87e3b228fc52f8a5a377c0d8b`, 28,982 bytes)
- `logs/synthetic_test_verify_i1c_route_latency.log` (SHA-256: `ea859f64d7f9cb5d8b50830013b81918ffb06df7aa7cd90e064ed7025fc7929d`, 8,523 bytes)
**Channel:** User-relayed peer communication (read-only review; zero model/pipeline/store runs, zero project data execution, zero manuscript edits applied)

---

## 1. Summary of Delivered Finalizer Hardening & Integrity Safeguards

In response to Codex-0048 and the static review in `ANTIGRAVITY_0039_STATIC_REVIEW.md`, Antigravity has resolved both identified finalizer defects, extended the synthetic unit test suite to 26 passing tests, and introduced an exclusive post-finalization completion record:

1. **Resolution of Defect 1: Finalizer-Only Exception & Drift Propagation:**
   - Explicitly tracked primary exception state via `primary_exc: Optional[BaseException] = None` across the bounded lifecycle.
   - Inside `finally:`, final rehash error is captured cleanly into `fin_read_err`.
   - If `primary_exc is None` (i.e. normal execution completed up to finalization), any final rehash failure (`OSError`) or source hash mismatch (`final_rehash != pre_hash`) immediately raises `RuntimeError`, ensuring finalizer-only failures can **never** be swallowed or return success.
   - If `primary_exc is not None` (an earlier error occurred), the primary exception is preserved for propagation while secondary integrity errors (`[FATAL INTEGRITY ERROR]` or `[FATAL INTEGRITY DRIFT]`) are logged to `sys.stderr`.

2. **Resolution of Defect 2: Bounded Lifecycle Scope Extended Over All Work After Pre-Hash Verification:**
   - The guarded `try...finally` block now wraps the entire execution lifecycle immediately after initial source bytes and `pre_hash` are captured and verified against `expected_sha256`.
   - Directory pre-existence checks, JSON deserialization, 350-record pipeline assertions, per-row validation, population constants, and contingency crosstab validation are all inside the guarded block. Any validation or collision failure now triggers the finalizer rehash before exiting.
   - In-memory validation strictly precedes directory creation (`output_dir.mkdir(parents=True, exist_ok=False)`).

3. **Small Exclusive Completion Record (`completion_record.json`):**
   - Written exclusively (`open(..., "x")`) to `output_dir / "completion_record.json"` strictly **after successful finalization** (when both post-write rehash and final rehash have verified source integrity without error or drift).
   - Encodes observed pre-read hash, post-write hash, and final rehash along with UTC timestamp and output paths.
   - Serialized with `json.dump(..., allow_nan=False)` to guarantee rejection of non-finite values.
   - Preserves existing `latency_percentiles_summary.json` and `verification_manifest.sha256` without modification.

4. **CLI Execution Evidence in `main()`:**
   - `main()` executes under `try...except`, logging cohort counts and completion record location before exiting with `sys.exit(0)` on success.
   - Catches failures, prints `[FAILURE] Verification failed: {e}` to `sys.stderr`, and exits with `sys.exit(1)`.

5. **Targeted Synthetic Unit Tests (26/26 Passing in 0.507s):**
   - Added path-specific mocked hash tests specifically exercising Defect 1: post-write hash succeeds, but finalizer hash raises `OSError` -> asserts `RuntimeError` and verifies no success return and no `completion_record.json`.
   - Added finalizer-only drift test (`final_rehash != pre_hash` with successful post-write) asserting `RuntimeError`.
   - Added validation-failure finalization tests: verifying final rehash call executes upon `ValueError`, and verifying that secondary drift/unreadability logs to `sys.stderr` while preserving primary `ValueError`.
   - Added directory collision final rehash test.
   - Added output write failure test asserting partial CSV preservation AND final rehash execution.
   - Expanded happy-path assertions: checks all 14 cohorts present in summary, checks exact population and sample SDs (`pop_sd_ddof0`, `sample_sd_ddof1`), verifies 351 ledger rows across categories A/B/C/D, checks manifest SHA-256 parity, and verifies `completion_record.json`.
   - Added CLI `main()` exit code test verifying exit code 0 on success and exit code 1 on collision.

---

## 2. Complete, Unabridged Unified Diffs

The diffs below are complete and patchable against the Antigravity-0039 checkpoint (`scripts/verify_i1c_route_latency.py` SHA-256: `29f849dcabb6a6cb6d5f4d5fa912db36d7871980079e1846d8a7311b8aeb6280`; `tests/test_verify_i1c_route_latency.py` SHA-256: `1a09cff3aea7fcd1856e2139575be8c5ff120b2cd48ef59e7c5dd642cede6471`). There are zero ellipsis placeholders or omitted sections.

### 2.1 Complete Diff for `scripts/verify_i1c_route_latency.py`

```diff
--- scripts/verify_i1c_route_latency.py (Antigravity-0039)
+++ scripts/verify_i1c_route_latency.py (Antigravity-0040)
@@ -124,7 +124,8 @@
       - Requires fresh output directory (fails if output_dir exists).
       - Uses exclusive creation ('x' mode) for all files.
       - Preserves partial files on failure.
-      - Re-checks source hash post-write and in guarded finalizer on all exit paths.
+      - Re-checks source hash post-write and in guarded finalizer on bounded lifecycle exit paths.
+      - Exposes final source hashes in a small exclusive completion record after successful finalization.
     """
     if not input_path.is_file():
         raise FileNotFoundError(f"Input file not found: {input_path}")
@@ -139,137 +140,141 @@
             f"Input SHA-256 mismatch!\n  Expected: {expected_sha256}\n  Computed: {pre_hash}"
         )
 
-    # 2. Fresh directory requirement: fail if output_dir already exists
-    if output_dir.exists():
-        raise FileExistsError(
-            f"Target output directory already exists (fresh run directory required): {output_dir}"
-        )
-
-    # 3. Parse JSON from verified bytes
+    # 2. Bounded lifecycle begins immediately after initial hash verification
+    primary_exc: Optional[BaseException] = None
+    post_write_hash: Optional[str] = None
+    final_rehash: Optional[str] = None
+    summary_content: Optional[Dict[str, Any]] = None
+
     try:
-        data = json.loads(raw_bytes.decode("utf-8"))
-    except Exception as e:
-        raise ValueError(f"Failed to parse JSON input: {e}")
-
-    if not isinstance(data, list):
-        raise ValueError(f"Expected top-level JSON array, got {type(data).__name__}")
-
-    terra_records = [
-        r for r in data if isinstance(r, dict) and r.get("pipeline") == "5_Full_TERRA"
-    ]
-    if len(terra_records) != 350:
-        raise ValueError(
-            f"Expected exactly 350 records for pipeline '5_Full_TERRA', found {len(terra_records)}"
-        )
-
-    # 4. Strict per-row validation and cohort collection in memory
-    seen_qids = set()
-    cat_counts = {"A_Factual": 0, "B_Evolutionary": 0, "C_OutOfContext": 0, "D_Adversarial": 0}
-    route_counts = {"EASY": 0, "HARD": 0}
-    crosstab: Dict[str, int] = {}
-
-    cohort_data: Dict[str, List[float]] = {
-        "ALL_gross": [], "ALL_net": [],
-        "EASY_gross": [], "EASY_net": [],
-        "HARD_gross": [], "HARD_net": [],
-        "CatA_gross": [], "CatA_net": [],
-        "CatB_gross": [], "CatB_net": [],
-        "CatC_gross": [], "CatC_net": [],
-        "CatD_gross": [], "CatD_net": []
-    }
-
-    ledger_rows: List[Dict[str, Any]] = []
-
-    for idx, r in enumerate(terra_records):
-        qid = r.get("query_id")
-        if not isinstance(qid, str) or not qid.strip():
-            raise ValueError(f"Row {idx}: missing or empty query_id")
-        if qid in seen_qids:
-            raise ValueError(f"Row {idx}: duplicate query_id '{qid}'")
-        seen_qids.add(qid)
-
-        cat = r.get("category")
-        if cat not in cat_counts:
-            raise ValueError(f"Row {idx} ({qid}): unknown category '{cat}'")
-        cat_counts[cat] += 1
-
-        timing = r.get("timing")
-        if not isinstance(timing, dict):
-            raise ValueError(f"Row {idx} ({qid}): missing or invalid timing dictionary")
-
-        route = timing.get("route_taken")
-        if route not in route_counts:
-            raise ValueError(f"Row {idx} ({qid}): unknown route_taken '{route}'")
-        route_counts[route] += 1
-
-        xtab_key = f"{cat}__{route}"
-        crosstab[xtab_key] = crosstab.get(xtab_key, 0) + 1
-
-        # Strict timing type and boundary checks
-        if "total_ms" not in timing:
-            raise ValueError(f"Row {idx} ({qid}): missing timing field 'total_ms'")
-        raw_total = timing["total_ms"]
-        if isinstance(raw_total, bool) or not isinstance(raw_total, (int, float)):
-            raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not numeric: {raw_total}")
-        total_ms = float(raw_total)
-        if not math.isfinite(total_ms) or total_ms < 0.0:
-            raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not finite non-negative: {total_ms}")
-
-        if "_retry_sleep_ms" not in timing:
-            raise ValueError(f"Row {idx} ({qid}): missing timing field '_retry_sleep_ms'")
-        raw_sleep = timing["_retry_sleep_ms"]
-        if isinstance(raw_sleep, bool) or not isinstance(raw_sleep, (int, float)):
-            raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not numeric: {raw_sleep}")
-        sleep_ms = float(raw_sleep)
-        if not math.isfinite(sleep_ms) or sleep_ms < 0.0:
-            raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not finite non-negative: {sleep_ms}")
-
-        if sleep_ms > total_ms:
+        # Fresh directory requirement: fail if output_dir already exists
+        if output_dir.exists():
+            raise FileExistsError(
+                f"Target output directory already exists (fresh run directory required): {output_dir}"
+            )
+
+        # 3. Parse JSON from verified bytes
+        try:
+            data = json.loads(raw_bytes.decode("utf-8"))
+        except Exception as e:
+            raise ValueError(f"Failed to parse JSON input: {e}")
+
+        if not isinstance(data, list):
+            raise ValueError(f"Expected top-level JSON array, got {type(data).__name__}")
+
+        terra_records = [
+            r for r in data if isinstance(r, dict) and r.get("pipeline") == "5_Full_TERRA"
+        ]
+        if len(terra_records) != 350:
             raise ValueError(
-                f"Row {idx} ({qid}): '_retry_sleep_ms' ({sleep_ms}) exceeds 'total_ms' ({total_ms})"
+                f"Expected exactly 350 records for pipeline '5_Full_TERRA', found {len(terra_records)}"
             )
 
-        net_ms = total_ms - sleep_ms
-        if net_ms < 0.0:
-            raise ValueError(f"Row {idx} ({qid}): net latency cannot be negative: {net_ms}")
-
-        ledger_rows.append({
-            "query_id": qid,
-            "category": cat,
-            "route_taken": route,
-            "total_ms_gross": total_ms,
-            "retry_sleep_ms": sleep_ms,
-            "net_ms": net_ms
-        })
-
-        cohort_data["ALL_gross"].append(total_ms)
-        cohort_data["ALL_net"].append(net_ms)
-        cohort_data[f"{route}_gross"].append(total_ms)
-        cohort_data[f"{route}_net"].append(net_ms)
-
-        cat_prefix = CAT_PREFIX_MAP[cat]
-        cohort_data[f"{cat_prefix}_gross"].append(total_ms)
-        cohort_data[f"{cat_prefix}_net"].append(net_ms)
-
-    # 5. Check population constants and full crosstab
-    expected_cats = {"A_Factual": 100, "B_Evolutionary": 100, "C_OutOfContext": 75, "D_Adversarial": 75}
-    if cat_counts != expected_cats:
-        raise ValueError(f"Category counts mismatch: expected {expected_cats}, got {cat_counts}")
-
-    expected_routes = {"EASY": 110, "HARD": 240}
-    if route_counts != expected_routes:
-        raise ValueError(f"Route counts mismatch: expected {expected_routes}, got {route_counts}")
-
-    if crosstab != EXPECTED_CROSSTAB:
-        raise ValueError(f"Crosstab mismatch: expected {EXPECTED_CROSSTAB}, got {crosstab}")
-
-    # 6. Guarded execution of directory creation, evidence writing, and post-write rehash
-    summary_content: Optional[Dict[str, Any]] = None
-
-    try:
-        # Create fresh directory only AFTER in-memory validation has fully succeeded
+        # 4. Strict per-row validation and cohort collection in memory
+        seen_qids = set()
+        cat_counts = {"A_Factual": 0, "B_Evolutionary": 0, "C_OutOfContext": 0, "D_Adversarial": 0}
+        route_counts = {"EASY": 0, "HARD": 0}
+        crosstab: Dict[str, int] = {}
+
+        cohort_data: Dict[str, List[float]] = {
+            "ALL_gross": [], "ALL_net": [],
+            "EASY_gross": [], "EASY_net": [],
+            "HARD_gross": [], "HARD_net": [],
+            "CatA_gross": [], "CatA_net": [],
+            "CatB_gross": [], "CatB_net": [],
+            "CatC_gross": [], "CatC_net": [],
+            "CatD_gross": [], "CatD_net": []
+        }
+
+        ledger_rows: List[Dict[str, Any]] = []
+
+        for idx, r in enumerate(terra_records):
+            qid = r.get("query_id")
+            if not isinstance(qid, str) or not qid.strip():
+                raise ValueError(f"Row {idx}: missing or empty query_id")
+            if qid in seen_qids:
+                raise ValueError(f"Row {idx}: duplicate query_id '{qid}'")
+            seen_qids.add(qid)
+
+            cat = r.get("category")
+            if cat not in cat_counts:
+                raise ValueError(f"Row {idx} ({qid}): unknown category '{cat}'")
+            cat_counts[cat] += 1
+
+            timing = r.get("timing")
+            if not isinstance(timing, dict):
+                raise ValueError(f"Row {idx} ({qid}): missing or invalid timing dictionary")
+
+            route = timing.get("route_taken")
+            if route not in route_counts:
+                raise ValueError(f"Row {idx} ({qid}): unknown route_taken '{route}'")
+            route_counts[route] += 1
+
+            xtab_key = f"{cat}__{route}"
+            crosstab[xtab_key] = crosstab.get(xtab_key, 0) + 1
+
+            # Strict timing type and boundary checks
+            if "total_ms" not in timing:
+                raise ValueError(f"Row {idx} ({qid}): missing timing field 'total_ms'")
+            raw_total = timing["total_ms"]
+            if isinstance(raw_total, bool) or not isinstance(raw_total, (int, float)):
+                raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not numeric: {raw_total}")
+            total_ms = float(raw_total)
+            if not math.isfinite(total_ms) or total_ms < 0.0:
+                raise ValueError(f"Row {idx} ({qid}): 'total_ms' is not finite non-negative: {total_ms}")
+
+            if "_retry_sleep_ms" not in timing:
+                raise ValueError(f"Row {idx} ({qid}): missing timing field '_retry_sleep_ms'")
+            raw_sleep = timing["_retry_sleep_ms"]
+            if isinstance(raw_sleep, bool) or not isinstance(raw_sleep, (int, float)):
+                raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not numeric: {raw_sleep}")
+            sleep_ms = float(raw_sleep)
+            if not math.isfinite(sleep_ms) or sleep_ms < 0.0:
+                raise ValueError(f"Row {idx} ({qid}): '_retry_sleep_ms' is not finite non-negative: {sleep_ms}")
+
+            if sleep_ms > total_ms:
+                raise ValueError(
+                    f"Row {idx} ({qid}): '_retry_sleep_ms' ({sleep_ms}) exceeds 'total_ms' ({total_ms})"
+                )
+
+            net_ms = total_ms - sleep_ms
+            if net_ms < 0.0:
+                raise ValueError(f"Row {idx} ({qid}): net latency cannot be negative: {net_ms}")
+
+            ledger_rows.append({
+                "query_id": qid,
+                "category": cat,
+                "route_taken": route,
+                "total_ms_gross": total_ms,
+                "retry_sleep_ms": sleep_ms,
+                "net_ms": net_ms
+            })
+
+            cohort_data["ALL_gross"].append(total_ms)
+            cohort_data["ALL_net"].append(net_ms)
+            cohort_data[f"{route}_gross"].append(total_ms)
+            cohort_data[f"{route}_net"].append(net_ms)
+
+            cat_prefix = CAT_PREFIX_MAP[cat]
+            cohort_data[f"{cat_prefix}_gross"].append(total_ms)
+            cohort_data[f"{cat_prefix}_net"].append(net_ms)
+
+        # 5. Check population constants and full crosstab
+        expected_cats = {"A_Factual": 100, "B_Evolutionary": 100, "C_OutOfContext": 75, "D_Adversarial": 75}
+        if cat_counts != expected_cats:
+            raise ValueError(f"Category counts mismatch: expected {expected_cats}, got {cat_counts}")
+
+        expected_routes = {"EASY": 110, "HARD": 240}
+        if route_counts != expected_routes:
+            raise ValueError(f"Route counts mismatch: expected {expected_routes}, got {route_counts}")
+
+        if crosstab != EXPECTED_CROSSTAB:
+            raise ValueError(f"Crosstab mismatch: expected {EXPECTED_CROSSTAB}, got {crosstab}")
+
+        # 6. Create fresh directory only AFTER in-memory validation has fully succeeded
         output_dir.mkdir(parents=True, exist_ok=False)
 
+        # 7. Write evidence outputs exclusively
         ledger_csv_path = output_dir / "per_query_latency_ledger.csv"
         summary_json_path = output_dir / "latency_percentiles_summary.json"
         manifest_path = output_dir / "verification_manifest.sha256"
@@ -318,7 +323,7 @@
         except Exception as write_err:
             raise RuntimeError(f"Error writing evidence outputs: {write_err}") from write_err
 
-        # Post-write hash immediately after output writes complete
+        # 8. Post-write hash immediately after output writes complete
         try:
             post_write_hash = compute_sha256(input_path)
         except Exception as rehash_err:
@@ -331,27 +336,56 @@
                 f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Post-write: {post_write_hash}"
             )
 
+    except BaseException as exc:
+        primary_exc = exc
+        raise
     finally:
-        # Guarded finalization check executed on BOTH success and failure paths
+        # Guarded finalization check executed on bounded lifecycle exit
+        fin_read_err: Optional[Exception] = None
         try:
             final_rehash = compute_sha256(input_path)
-        except Exception as fin_err:
-            if sys.exc_info()[1] is None:
+        except Exception as e:
+            fin_read_err = e
+            final_rehash = None
+
+        if fin_read_err is not None:
+            if primary_exc is None:
                 raise RuntimeError(
-                    f"Source file became unreadable during finalization: {fin_err}"
-                ) from fin_err
+                    f"Source file became unreadable during finalization: {fin_read_err}"
+                ) from fin_read_err
             else:
-                print(f"[FATAL] Source file became unreadable in finalizer: {fin_err}", file=sys.stderr)
-                final_rehash = None
+                print(
+                    f"[FATAL INTEGRITY ERROR] Source file became unreadable in finalizer: {fin_read_err}",
+                    file=sys.stderr
+                )
 
         if final_rehash is not None and final_rehash != pre_hash:
             drift_err = RuntimeError(
                 f"Source file drifted on disk during execution!\n  Pre-read: {pre_hash}\n  Final:    {final_rehash}"
             )
-            if sys.exc_info()[1] is None:
+            if primary_exc is None:
                 raise drift_err
             else:
                 print(f"[FATAL INTEGRITY DRIFT] {drift_err}", file=sys.stderr)
+
+    # 9. Small exclusive completion record written strictly AFTER successful finalization
+    completion_record_path = output_dir / "completion_record.json"
+    completion_record = {
+        "status": "SUCCESS",
+        "source_file": str(input_path.resolve()),
+        "expected_sha256": expected_sha256,
+        "source_sha256_pre_read": pre_hash,
+        "source_sha256_post_write": post_write_hash,
+        "source_sha256_final": final_rehash,
+        "integrity_verified": True,
+        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
+        "output_directory": str(output_dir.resolve()),
+        "ledger_csv": "per_query_latency_ledger.csv",
+        "summary_json": "latency_percentiles_summary.json",
+        "manifest": "verification_manifest.sha256"
+    }
+    with open(completion_record_path, "x", encoding="utf-8") as f:
+        json.dump(completion_record, f, indent=2, allow_nan=False)
 
     return summary_content
 
@@ -387,15 +421,21 @@
     print(f"Output dir:     {args.output_dir}")
     print(f"Expected hash:  {args.expected_hash}")
 
-    result = verify_route_latency(
-        input_path=args.input,
-        output_dir=args.output_dir,
-        expected_sha256=args.expected_hash
-    )
-
-    print("\n[SUCCESS] Verification complete. Cohort summary counts:")
-    for cohort, stats in result["cohort_summary"].items():
-        print(f"  {cohort:<12}: N={stats['n']:<3} median={stats['display_rounded']['median']} ms")
+    try:
+        result = verify_route_latency(
+            input_path=args.input,
+            output_dir=args.output_dir,
+            expected_sha256=args.expected_hash
+        )
+
+        print("\n[SUCCESS] Verification complete. Cohort summary counts:")
+        for cohort, stats in result["cohort_summary"].items():
+            print(f"  {cohort:<12}: N={stats['n']:<3} median={stats['display_rounded']['median']} ms")
+        print(f"\n[RECORD] Completion record written to: {args.output_dir / 'completion_record.json'}")
+        sys.exit(0)
+    except Exception as e:
+        print(f"\n[FAILURE] Verification failed: {e}", file=sys.stderr)
+        sys.exit(1)
 
 
 if __name__ == "__main__":
```

### 2.2 Complete Diff for `tests/test_verify_i1c_route_latency.py`

```diff
--- tests/test_verify_i1c_route_latency.py (Antigravity-0039)
+++ tests/test_verify_i1c_route_latency.py (Antigravity-0040)
@@ -6,6 +6,7 @@
 Runs strictly in isolated temporary directories. Zero interaction with real project data.
 """
 
+import io
 import os
 import sys
 import json
@@ -21,7 +22,12 @@
 if str(ROOT_DIR) not in sys.path:
     sys.path.insert(0, str(ROOT_DIR))
 
-from scripts.verify_i1c_route_latency import verify_route_latency, compute_bytes_sha256, compute_sha256
+from scripts.verify_i1c_route_latency import (
+    verify_route_latency,
+    compute_bytes_sha256,
+    compute_sha256,
+    main
+)
 
 _orig_json_dump = json.dump
 
@@ -89,7 +95,7 @@
         self.temp_dir.cleanup()
 
     def test_happy_path_detailed_values(self):
-        """Verifies complete execution, exact calculated statistics, ledger rows, and manifest."""
+        """Verifies complete execution, exact calculated statistics, ledger rows, manifest, and completion record."""
         result = verify_route_latency(
             input_path=self.input_file,
             output_dir=self.output_dir,
@@ -97,36 +103,73 @@
         )
 
         cohorts = result["cohort_summary"]
+        expected_cohort_keys = {
+            "ALL_gross", "ALL_net", "EASY_gross", "EASY_net", "HARD_gross", "HARD_net",
+            "CatA_gross", "CatA_net", "CatB_gross", "CatB_net",
+            "CatC_gross", "CatC_net", "CatD_gross", "CatD_net"
+        }
+        self.assertEqual(set(cohorts.keys()), expected_cohort_keys)
+
         self.assertEqual(cohorts["ALL_gross"]["n"], 350)
+        self.assertEqual(cohorts["ALL_net"]["n"], 350)
         self.assertEqual(cohorts["EASY_gross"]["n"], 110)
+        self.assertEqual(cohorts["EASY_net"]["n"], 110)
         self.assertEqual(cohorts["HARD_gross"]["n"], 240)
+        self.assertEqual(cohorts["HARD_net"]["n"], 240)
         self.assertEqual(cohorts["CatA_gross"]["n"], 100)
+        self.assertEqual(cohorts["CatA_net"]["n"], 100)
         self.assertEqual(cohorts["CatB_gross"]["n"], 100)
+        self.assertEqual(cohorts["CatB_net"]["n"], 100)
         self.assertEqual(cohorts["CatC_gross"]["n"], 75)
+        self.assertEqual(cohorts["CatC_net"]["n"], 75)
         self.assertEqual(cohorts["CatD_gross"]["n"], 75)
+        self.assertEqual(cohorts["CatD_net"]["n"], 75)
 
         # Check exact synthetic statistics for CatA net (5000 + i - 100 = 4900 + i for i=1..100)
-        # Median of 4901..5000 is 4950.5
+        # Median of 4901..5000 is 4950.5, mean is 4950.5
+        # Pop SD is sqrt((100^2 - 1) / 12) = sqrt(833.25) ≈ 28.86607
+        # Sample SD (ddof=1) is sqrt(83325 / 99) = sqrt(841.6667) ≈ 29.01149
         self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["median"], 4950.5, places=3)
         self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["p25"], 4925.75, places=3)
         self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["p75"], 4975.25, places=3)
         self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["mean"], 4950.5, places=3)
+        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["pop_sd_ddof0"], math.sqrt(9999.0 / 12.0), places=3)
+        self.assertAlmostEqual(cohorts["CatA_net"]["raw"]["sample_sd_ddof1"], math.sqrt(83325.0 / 99.0), places=3)
+
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["median"], 4950.5)
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["p25"], 4925.75)
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["p75"], 4975.25)
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["mean"], 4950.5)
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["pop_sd_ddof0"], 28.866)
+        self.assertEqual(cohorts["CatA_net"]["display_rounded"]["sample_sd_ddof1"], 29.011)
 
         # Verify output files exist
         ledger_path = self.output_dir / "per_query_latency_ledger.csv"
         summary_path = self.output_dir / "latency_percentiles_summary.json"
         manifest_path = self.output_dir / "verification_manifest.sha256"
+        completion_path = self.output_dir / "completion_record.json"
 
         self.assertTrue(ledger_path.exists())
         self.assertTrue(summary_path.exists())
         self.assertTrue(manifest_path.exists())
-
-        # Check ledger lines (350 records + 1 header = 351 lines)
+        self.assertTrue(completion_path.exists())
+
+        # Check ledger lines (350 records + 1 header = 351 lines) and verify samples across categories
         with open(ledger_path, "r", encoding="utf-8") as f:
             lines = [line.strip() for line in f if line.strip()]
         self.assertEqual(len(lines), 351)
         self.assertEqual(lines[0], "query_id,category,route_taken,total_ms_gross,retry_sleep_ms,net_ms")
         self.assertEqual(lines[1], "A001,A_Factual,EASY,5001.0,100.0,4901.0")
+        self.assertEqual(lines[100], "A100,A_Factual,EASY,5100.0,100.0,5000.0")
+        self.assertEqual(lines[101], "B001,B_Evolutionary,HARD,15001.0,200.0,14801.0")
+        self.assertEqual(lines[201], "C001,C_OutOfContext,HARD,2001.0,0.0,2001.0")
+        self.assertEqual(lines[276], "D001,D_Adversarial,EASY,8001.0,50.0,7951.0")
+        self.assertEqual(lines[350], "D075,D_Adversarial,HARD,12075.0,150.0,11925.0")
+
+        # Verify all 350 queries in ledger are unique and match synthetic IDs
+        ledger_qids = [l.split(",")[0] for l in lines[1:]]
+        self.assertEqual(len(ledger_qids), 350)
+        self.assertEqual(len(set(ledger_qids)), 350)
 
         # Check manifest matches file hashes
         with open(manifest_path, "r", encoding="utf-8") as f:
@@ -136,6 +179,18 @@
         expected_summary_h = compute_sha256(summary_path)
         self.assertIn(f"{expected_ledger_h}  per_query_latency_ledger.csv", manifest_lines)
         self.assertIn(f"{expected_summary_h}  latency_percentiles_summary.json", manifest_lines)
+
+        # Check completion record contents
+        with open(completion_path, "r", encoding="utf-8") as f:
+            record = json.load(f)
+        self.assertEqual(record["status"], "SUCCESS")
+        self.assertEqual(record["source_sha256_pre_read"], self.valid_hash)
+        self.assertEqual(record["source_sha256_post_write"], self.valid_hash)
+        self.assertEqual(record["source_sha256_final"], self.valid_hash)
+        self.assertTrue(record["integrity_verified"])
+        self.assertEqual(record["ledger_csv"], "per_query_latency_ledger.csv")
+        self.assertEqual(record["summary_json"], "latency_percentiles_summary.json")
+        self.assertEqual(record["manifest"], "verification_manifest.sha256")
 
     def test_fresh_directory_requirement(self):
         """Fails with FileExistsError if output directory already exists (fresh directory required)."""
@@ -338,9 +393,7 @@
     def test_source_drift_post_write(self):
         """Detects modification of source file on disk during writing and raises RuntimeError."""
         def modify_source_during_write(*args, **kwargs):
-            # Call the real json.dump first
             _orig_json_dump(*args, **kwargs)
-            # Modify the source file right after dump, before post-write hash runs
             with open(self.input_file, "ab") as f:
                 f.write(b"drift")
 
@@ -348,35 +401,205 @@
             with self.assertRaises(RuntimeError) as ctx:
                 verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
             self.assertIn("Source file drifted on disk", str(ctx.exception))
-
-    def test_source_unreadable_at_finalization(self):
-        """Detects source becoming unreadable in post-write/finalizer and raises RuntimeError."""
-        def delete_source_during_write(*args, **kwargs):
-            _orig_json_dump(*args, **kwargs)
-            os.remove(self.input_file)
-
-        with patch("json.dump", side_effect=delete_source_during_write):
+        # Completion record must NOT have been written
+        self.assertFalse((self.output_dir / "completion_record.json").exists())
+
+    def test_finalizer_only_unreadable_raises_and_no_success(self):
+        """Specifically exercises Defect 1: post-write hash succeeds, but finalizer hash fails.
+        Must raise RuntimeError and must NOT return success or create completion_record.json."""
+        orig_compute_sha256 = compute_sha256
+        input_calls = 0
+
+        def mocked_compute_sha256(path):
+            nonlocal input_calls
+            p = Path(path).resolve()
+            if p == self.input_file.resolve():
+                input_calls += 1
+                if input_calls == 1:
+                    # 1st call on input_path is post-write check: succeeds!
+                    return orig_compute_sha256(path)
+                elif input_calls >= 2:
+                    # 2nd call on input_path is finalizer check: raises!
+                    raise OSError("Simulated finalizer-only disk unreadability")
+            return orig_compute_sha256(path)
+
+        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=mocked_compute_sha256):
             with self.assertRaises(RuntimeError) as ctx:
                 verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
-            self.assertTrue(
-                "Source file became unreadable" in str(ctx.exception)
-                or "No such file or directory" in str(ctx.exception)
-            )
-
-    def test_output_write_failure_preserves_partial(self):
-        """Ensures that write failure preserves partial outputs in output_dir without deletion."""
+            self.assertIn("Source file became unreadable during finalization", str(ctx.exception))
+
+        # Must NOT have created completion_record.json
+        self.assertFalse((self.output_dir / "completion_record.json").exists())
+
+    def test_finalizer_only_drift_raises_and_no_success(self):
+        """Specifically exercises finalizer-only drift: post-write hash succeeds, but source drifts before finalizer."""
+        orig_compute_sha256 = compute_sha256
+        input_calls = 0
+
+        def mocked_compute_sha256(path):
+            nonlocal input_calls
+            p = Path(path).resolve()
+            if p == self.input_file.resolve():
+                input_calls += 1
+                if input_calls == 1:
+                    # 1st call on input_path is post-write check: succeeds!
+                    return orig_compute_sha256(path)
+                elif input_calls >= 2:
+                    # 2nd call on input_path is finalizer check: simulated drifted hash!
+                    return "f" * 64
+            return orig_compute_sha256(path)
+
+        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=mocked_compute_sha256):
+            with self.assertRaises(RuntimeError) as ctx:
+                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
+            self.assertIn("Source file drifted on disk during execution!", str(ctx.exception))
+
+        # Must NOT have created completion_record.json
+        self.assertFalse((self.output_dir / "completion_record.json").exists())
+
+    def test_validation_failure_executes_final_rehash(self):
+        """Specifically exercises Defect 2: validation failure must still execute final rehash."""
+        bad_data = make_synthetic_350_dataset()
+        bad_data[1]["query_id"] = bad_data[0]["query_id"]  # Duplicate QID
+        bad_file = self.tmp_path / "bad_val_rehash.json"
+        raw_b = json.dumps(bad_data).encode("utf-8")
+        with open(bad_file, "wb") as f:
+            f.write(raw_b)
+
+        orig_compute_sha256 = compute_sha256
+        rehash_called = False
+
+        def spy_compute_sha256(path):
+            nonlocal rehash_called
+            if Path(path).resolve() == bad_file.resolve():
+                rehash_called = True
+            return orig_compute_sha256(path)
+
+        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
+            with self.assertRaises(ValueError) as ctx:
+                verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
+            self.assertIn("duplicate query_id", str(ctx.exception))
+
+        self.assertTrue(rehash_called, "Final rehash must execute even when validation fails!")
+        self.assertFalse(self.output_dir.exists())
+
+    def test_validation_failure_with_source_drift_preserves_primary_and_logs(self):
+        """Ensures that when validation fails and source drifts, primary exception is raised and drift is logged."""
+        bad_data = make_synthetic_350_dataset()
+        bad_data[1]["query_id"] = bad_data[0]["query_id"]
+        bad_file = self.tmp_path / "bad_val_drift.json"
+        with open(bad_file, "w", encoding="utf-8") as f:
+            json.dump(bad_data, f)
+
+        orig_compute_sha256 = compute_sha256
+
+        def drift_compute_sha256(path):
+            if Path(path).resolve() == bad_file.resolve():
+                return "d" * 64  # drifted hash
+            return orig_compute_sha256(path)
+
+        stderr_capture = io.StringIO()
+        with patch("sys.stderr", stderr_capture):
+            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=drift_compute_sha256):
+                with self.assertRaises(ValueError) as ctx:
+                    verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
+                self.assertIn("duplicate query_id", str(ctx.exception))
+
+        self.assertIn("[FATAL INTEGRITY DRIFT]", stderr_capture.getvalue())
+
+    def test_validation_failure_with_unreadable_source_preserves_primary_and_logs(self):
+        """Ensures that when validation fails and source is unreadable at finalizer, primary exception is preserved."""
+        bad_data = make_synthetic_350_dataset()
+        bad_data[1]["query_id"] = bad_data[0]["query_id"]
+        bad_file = self.tmp_path / "bad_val_unreadable.json"
+        with open(bad_file, "w", encoding="utf-8") as f:
+            json.dump(bad_data, f)
+
+        orig_compute_sha256 = compute_sha256
+
+        def unreadable_compute_sha256(path):
+            if Path(path).resolve() == bad_file.resolve():
+                raise OSError("Disk unreadable in finalizer")
+            return orig_compute_sha256(path)
+
+        stderr_capture = io.StringIO()
+        with patch("sys.stderr", stderr_capture):
+            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=unreadable_compute_sha256):
+                with self.assertRaises(ValueError) as ctx:
+                    verify_route_latency(bad_file, self.output_dir, expected_sha256=None)
+                self.assertIn("duplicate query_id", str(ctx.exception))
+
+        self.assertIn("[FATAL INTEGRITY ERROR]", stderr_capture.getvalue())
+
+    def test_directory_collision_executes_final_rehash(self):
+        """Ensures that pre-existing directory collision still triggers bounded finalization rehash."""
+        self.output_dir.mkdir(parents=True, exist_ok=True)
+        orig_compute_sha256 = compute_sha256
+        rehash_called = False
+
+        def spy_compute_sha256(path):
+            nonlocal rehash_called
+            if Path(path).resolve() == self.input_file.resolve():
+                rehash_called = True
+            return orig_compute_sha256(path)
+
+        with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
+            with self.assertRaises(FileExistsError) as ctx:
+                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
+            self.assertIn("fresh run directory required", str(ctx.exception))
+
+        self.assertTrue(rehash_called, "Final rehash must execute even when directory collision occurs!")
+
+    def test_output_write_failure_preserves_partial_and_executes_final_rehash(self):
+        """Ensures that write failure preserves partial outputs without deletion AND executes final rehash."""
+        orig_compute_sha256 = compute_sha256
+        final_rehash_called = False
+
         def fail_json_write(*args, **kwargs):
             raise IOError("Simulated disk error during JSON write")
 
+        def spy_compute_sha256(path):
+            nonlocal final_rehash_called
+            if Path(path).resolve() == self.input_file.resolve():
+                final_rehash_called = True
+            return orig_compute_sha256(path)
+
         with patch("json.dump", side_effect=fail_json_write):
-            with self.assertRaises(RuntimeError) as ctx:
-                verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
-            self.assertIn("Error writing evidence outputs", str(ctx.exception))
+            with patch("scripts.verify_i1c_route_latency.compute_sha256", side_effect=spy_compute_sha256):
+                with self.assertRaises(RuntimeError) as ctx:
+                    verify_route_latency(self.input_file, self.output_dir, expected_sha256=self.valid_hash)
+                self.assertIn("Error writing evidence outputs", str(ctx.exception))
 
         # Partial CSV output must be preserved in output_dir
         ledger_path = self.output_dir / "per_query_latency_ledger.csv"
         self.assertTrue(ledger_path.exists())
         self.assertGreater(ledger_path.stat().st_size, 0)
+        self.assertTrue(final_rehash_called, "Final rehash must execute even when write fails!")
+        self.assertFalse((self.output_dir / "completion_record.json").exists())
+
+    def test_cli_main_success_and_failure_exit_codes(self):
+        """Ensures CLI main exits with 0 on success and 1 on error, writing completion record and messages."""
+        fresh_out = self.tmp_path / "cli_fresh_out"
+        test_argv_success = [
+            "verify_i1c_route_latency.py",
+            "--input", str(self.input_file),
+            "--output-dir", str(fresh_out),
+            "--expected-hash", self.valid_hash
+        ]
+        with patch("sys.argv", test_argv_success):
+            with self.assertRaises(SystemExit) as ctx:
+                main()
+            self.assertEqual(ctx.exception.code, 0)
+        self.assertTrue((fresh_out / "completion_record.json").exists())
+
+        # Test failure: rerun on same directory (collision) must exit code 1
+        stderr_capture = io.StringIO()
+        with patch("sys.argv", test_argv_success):
+            with patch("sys.stderr", stderr_capture):
+                with self.assertRaises(SystemExit) as ctx:
+                    main()
+                self.assertEqual(ctx.exception.code, 1)
+        self.assertIn("Verification failed", stderr_capture.getvalue())
 
 
 if __name__ == "__main__":
```

---

## 3. Hash-Bound Synthetic Test Execution Log

The following is the complete, unabridged log recorded in `logs/synthetic_test_verify_i1c_route_latency.log` (SHA-256: `ea859f64d7f9cb5d8b50830013b81918ffb06df7aa7cd90e064ed7025fc7929d`):

```text
================================================================================
SYNTHETIC TEST EXECUTION LOG: verify_i1c_route_latency.py
================================================================================
Timestamp (UTC): 2026-10-08T16:08:19.716694+00:00
Python Version:  3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]
Target Script:   scripts/verify_i1c_route_latency.py (SHA-256: 8c54d533c01f88b12820c8e33d580ce27cc2b84c7f2b0471481bcb07d5981fee)
Test Suite:      tests/test_verify_i1c_route_latency.py (SHA-256: f765ac336316729a96cb76bb43ed51fc3312d7b87e3b228fc52f8a5a377c0d8b)
--------------------------------------------------------------------------------
================================================================================
VERIFY ROUTE & CATEGORY LATENCY (I1c)
================================================================================
Input file:     C:\Users\zafor\AppData\Local\Temp\tmp0ebxuoud\synthetic_canonical.json
Output dir:     C:\Users\zafor\AppData\Local\Temp\tmp0ebxuoud\cli_fresh_out
Expected hash:  10ad6c5b9701dc67cec15f6697f1153eb9768070712514ec381eb066a4b63086

[SUCCESS] Verification complete. Cohort summary counts:
  ALL_gross   : N=350 median=6550.5 ms
  ALL_net     : N=350 median=6475.5 ms
  EASY_gross  : N=110 median=5055.5 ms
  EASY_net    : N=110 median=4955.5 ms
  HARD_gross  : N=240 median=12055.5 ms
  HARD_net    : N=240 median=11905.5 ms
  CatA_gross  : N=100 median=5050.5 ms
  CatA_net    : N=100 median=4950.5 ms
  CatB_gross  : N=100 median=15050.5 ms
  CatB_net    : N=100 median=14850.5 ms
  CatC_gross  : N=75  median=2038.0 ms
  CatC_net    : N=75  median=2038.0 ms
  CatD_gross  : N=75  median=12038.0 ms
  CatD_net    : N=75  median=11888.0 ms

[RECORD] Completion record written to: C:\Users\zafor\AppData\Local\Temp\tmp0ebxuoud\cli_fresh_out\completion_record.json
================================================================================
VERIFY ROUTE & CATEGORY LATENCY (I1c)
================================================================================
Input file:     C:\Users\zafor\AppData\Local\Temp\tmp0ebxuoud\synthetic_canonical.json
Output dir:     C:\Users\zafor\AppData\Local\Temp\tmp0ebxuoud\cli_fresh_out
Expected hash:  10ad6c5b9701dc67cec15f6697f1153eb9768070712514ec381eb066a4b63086
test_boolean_in_timing (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_boolean_in_timing)
Fails with ValueError if boolean is passed as numeric timing value. ... ok
test_category_prefix_mapping (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_category_prefix_mapping)
Ensures that CatA, CatB, CatC, CatD cohort keys receive entries without KeyError. ... ok
test_cli_main_success_and_failure_exit_codes (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_cli_main_success_and_failure_exit_codes)
Ensures CLI main exits with 0 on success and 1 on error, writing completion record and messages. ... ok
test_crosstab_mismatch_identical_marginals (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_crosstab_mismatch_identical_marginals)
Fails with ValueError if crosstab is invalid even though marginal category/route totals match. ... ok
test_directory_collision_executes_final_rehash (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_directory_collision_executes_final_rehash)
Ensures that pre-existing directory collision still triggers bounded finalization rehash. ... ok
test_duplicate_query_id (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_duplicate_query_id)
Fails with ValueError if any query_id is duplicated. ... ok
test_empty_query_id (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_empty_query_id)
Fails with ValueError if a query_id is empty or whitespace. ... ok
test_finalizer_only_drift_raises_and_no_success (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_finalizer_only_drift_raises_and_no_success)
Specifically exercises finalizer-only drift: post-write hash succeeds, but source drifts before finalizer. ... ok
test_finalizer_only_unreadable_raises_and_no_success (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_finalizer_only_unreadable_raises_and_no_success)
Specifically exercises Defect 1: post-write hash succeeds, but finalizer hash fails. ... ok
test_fresh_directory_requirement (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_fresh_directory_requirement)
Fails with FileExistsError if output directory already exists (fresh directory required). ... ok
test_happy_path_detailed_values (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_happy_path_detailed_values)
Verifies complete execution, exact calculated statistics, ledger rows, manifest, and completion record. ... ok
test_hash_mismatch (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_hash_mismatch)
Fails with ValueError if expected_sha256 does not match. ... ok
test_missing_timing_field_retry_sleep_ms (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_missing_timing_field_retry_sleep_ms)
Fails with ValueError if _retry_sleep_ms is missing from timing. ... ok
test_missing_timing_field_total_ms (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_missing_timing_field_total_ms)
Fails with ValueError if total_ms is missing from timing. ... ok
test_nan_in_timing (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_nan_in_timing)
Fails with ValueError if NaN is in timing (via raw float). ... ok
test_negative_retry_sleep_ms (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_negative_retry_sleep_ms)
Fails with ValueError if _retry_sleep_ms is negative. ... ok
test_negative_total_ms (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_negative_total_ms)
Fails with ValueError if total_ms is negative. ... ok
test_output_write_failure_preserves_partial_and_executes_final_rehash (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_output_write_failure_preserves_partial_and_executes_final_rehash)
Ensures that write failure preserves partial outputs without deletion AND executes final rehash. ... ok
test_sleep_exceeds_total_ms (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_sleep_exceeds_total_ms)
Fails with ValueError if _retry_sleep_ms > total_ms. ... ok
test_source_drift_post_write (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_source_drift_post_write)
Detects modification of source file on disk during writing and raises RuntimeError. ... [FATAL INTEGRITY DRIFT] Source file drifted on disk during execution!
  Pre-read: 10ad6c5b9701dc67cec15f6697f1153eb9768070712514ec381eb066a4b63086
  Final:    05cad3a91b138a5cc3089ddeb3b23caeb52fc6825759b615e8a707dba00148bc
ok
test_unknown_category (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_unknown_category)
Fails with ValueError if a category is unrecognized. ... ok
test_unknown_route (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_unknown_route)
Fails with ValueError if a route_taken is unrecognized. ... ok
test_validation_failure_executes_final_rehash (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_validation_failure_executes_final_rehash)
Specifically exercises Defect 2: validation failure must still execute final rehash. ... ok
test_validation_failure_with_source_drift_preserves_primary_and_logs (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_validation_failure_with_source_drift_preserves_primary_and_logs)
Ensures that when validation fails and source drifts, primary exception is raised and drift is logged. ... ok
test_validation_failure_with_unreadable_source_preserves_primary_and_logs (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_validation_failure_with_unreadable_source_preserves_primary_and_logs)
Ensures that when validation fails and source is unreadable at finalizer, primary exception is preserved. ... ok
test_validation_happens_before_directory_creation (tests.test_verify_i1c_route_latency.TestVerifyI1cRouteLatency.test_validation_happens_before_directory_creation)
Ensures that invalid data fails before creating any output directory on disk. ... ok

----------------------------------------------------------------------
Ran 26 tests in 0.507s

OK
```

---

## 4. Current Coordination State & Operational Posture

- **Current State:** `I1C_SCRIPT_FINALIZER_HARDENED_COMPLETION_RECORD_READY`
- **Execution Boundaries Fully Maintained:**
  - Zero execution against real project data (`data/terra_canonical_v2_eval.json`).
  - Zero manuscript files modified.
  - Zero pipeline runs, model inference, vector store queries, or API calls.
  - All tests executed in isolated temporary directories (`tempfile.TemporaryDirectory`).
- **Next Steps:**
  - Await Codex static review of the hardened finalizer, complete diffs, and synthetic test execution log.
  - Upon certification by Codex and explicit authorization from the user, the utility is prepared for single-pass verification run against `data/terra_canonical_v2_eval.json`.
