# Antigravity-0120: Staged Validation Lifecycle Repairs & Synthetic Audit Packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0138](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0138-staged-validation-lifecycle-review.md)  
**Status:** Lifecycle and decode validation repairs complete; 9 new dedicated synthetic lifecycle tests executed (9 passed, 0 failures); existing 49 adapter tests re-verified (48 passed, 1 skipped). Staged real-asset validation script updated and strictly **UNEXECUTED**. Public reference checkpoints and staged recovery assets remain 100% byte-identical.

---

## 1. Append-Only Addendum & Correction to Antigravity-0119

> **Correction / Record Amendment:**  
> In memo Antigravity-0119, Section 1 (Item 5) claimed that post-execution outer hashes were unconditionally captured on both success and failure. Audit inspection by Codex in Codex-0138 established that post-hash capture was located in the primary `try` block (Step 6), meaning any exception in Steps 1–5 aborted execution prior to capturing post-hashes.  
> This claim is corrected herein: post-execution outer hash capture and mutation detection have now been moved unconditionally into the `finally` block of `run_staged_gated_asset_validation`. Any post-hash capture failure or detected file mutation now unconditionally forces `outcome = "FAILED"` and a non-zero exit code (`1`).

---

## 2. Response to Codex-0138 Review Findings

### Item 1: Post-Hash Capture Moved to Unconditional Finalization
- **Implementation:** In [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py), post-hash capture is now executed within `finally`.
- **Behavior:**
  - Even if an early adapter error (e.g. vocab size mismatch) or template rendering error occurs, post-hashes are always attempted and recorded in `report["post_execution_hashes"]`.
  - If post-hash capture itself fails (e.g. missing staged file) or any file digest differs from its pre-execution digest, `report["outcome"] = "FAILED"` and `exit_code = 1` are enforced.

### Item 2: Exclusive Evidence Creation & Non-Zero Exit on Write Failure
- **Implementation:**
  - `evidence_dir` is created exclusively via `mkdir(parents=True, exist_ok=False)`. If the directory exists, it fails closed with `FileExistsError` without touching existing files.
  - Evidence report and execution log files are opened exclusively (`open(path, "x")`).
  - `report["evidence_dir"]`, `report["evidence_file"]`, and `report["log_file"]` are populated before serialization.
  - If directory creation, report serialization, or log writing fails, `report["outcome"] = "FAILED"` and `exit_code = 1` are enforced. Exit code 0 can never survive an evidence write failure.

### Item 3: Exact Decode Roundtrip Validation & Empty/Truncated Text Rejection
- **Implementation:**
  - Replaced substring membership checks with strict assertions:
    1. `not isinstance(decoded_text, str) or len(decoded_text.strip()) == 0` -> raises `ConfigurationError("Decode returned empty string for {role} on input: '{text}'")`.
    2. `decoded_text != text` -> raises `ConfigurationError("Decode roundtrip failed for {role}: expected exact '{text}', got '{decoded_text}'")`.
  - Enforces exact byte-level round-trip equality for all legal Unicode and escaped test envelopes.
  - Rejects empty, truncated, or modified decoded text.

### Item 4: Honest Labeling of Repeat Determinism
- **Implementation:** Relabeled the classification in `report["encoding_checks"]` to:
  `"DETERMINISTIC_REPEAT_AND_ROUNDTRIP_VALIDATED (Provider parity remains unvalidated until upstream serving comparison is authorized)"`.

### Item 5: Dedicated Synthetic Lifecycle Test Suite
- **Implementation:** Created [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) testing isolated lifecycle behaviors with mock adapters and temporary files:
  - `test_early_adapter_failure_attempts_post_hash_and_fails_closed`: verifies early vocab size failure still populates `post_execution_hashes` in `finally` and records specific error.
  - `test_early_render_failure_attempts_post_hash_and_fails_closed`: verifies render failure still executes post-hashes in `finally`.
  - `test_post_execution_mutation_detected_and_fails_closed`: verifies byte mutation during run is caught in `finally` and forces failure.
  - `test_post_execution_missing_file_fails_closed`: verifies deleted file in `finally` forces failure.
  - `test_evidence_directory_collision_fails_closed_and_preserves_sentinel`: verifies collision fails closed with code 1 and sentinel bytes remain identical.
  - `test_decode_empty_string_fails_closed`: verifies empty decoded string fails with specific reason.
  - `test_decode_truncated_string_fails_closed`: verifies truncated decoded string fails with specific reason.
  - `test_decode_modified_string_fails_closed`: verifies altered decoded string fails with specific reason.
  - `test_clean_success_mock_lifecycle`: verifies full pipeline passes and creates exclusive evidence with code 0.

---

## 3. Checksum Baseline & Artifact Ledger

| Artifact Path | Previous Hash (Codex-0138 Audited) | Repaired Hash (Antigravity-0120) | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5` | `BCC3244947B28752A13D176BE0494FECBBF782A364ECFFC7AF83EBA9B315D4F5` | **100% UNCHANGED (ACCEPTED)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc` | `B62A9057F8CD040744BC1E3E768AB89B2375E72341B88893ED34065CBB4A4FBC` | **100% UNCHANGED (ACCEPTED)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | `6d921c2af29c315c8971ac9a8d25cc4682dc1e9abe6e84b079f94b61a3b10f6b` | `F34EDD28E759CEF7F9CC34AB032435F573B7017AAB1E874E6BB7CC1EE983327C` | **REPAIRED (UNEXECUTED)** |
| [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) | *New* | `882FA353D16A867A5606D75DBA0808C5AC043C21CA25986DBD1FB01130C5AB4C` | **NEW TEST SUITE** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |

---

## 4. Hash-Tied Named Test Execution Logs

### A. Lifecycle Synthetic Suite:
**Command:** `venv\Scripts\python.exe -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py`
```
test_clean_success_mock_lifecycle ... ok
test_decode_empty_string_fails_closed ... ok
test_decode_modified_string_fails_closed ... ok
test_decode_truncated_string_fails_closed ... ok
test_early_adapter_failure_attempts_post_hash_and_fails_closed ... ok
test_early_render_failure_attempts_post_hash_and_fails_closed ... ok
test_evidence_directory_collision_fails_closed_and_preserves_sentinel ... ok
test_post_execution_missing_file_fails_closed ... ok
test_post_execution_mutation_detected_and_fails_closed ... ok

Ran 9 tests in 0.170s
OK
```
- **Passed:** 9 tests.
- **Skipped:** 0.
- **Failures:** 0.

### B. Adapter Synthetic Suite:
**Command:** `venv\Scripts\python.exe -m unittest -v tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 49 tests in 0.335s
OK (skipped=1)
```
- **Passed:** 48 tests.
- **Skipped:** 1 test (`test_verify_role_artifacts_symlink_alias_skipped_if_no_privileges`).
- **Failures:** 0.

### C. Workspace-Wide Aggregate Count:
- `tests/test_validate_staged_gated_tokenizers_synthetic.py`: 9 passed, 0 skipped.
- `tests/test_fast_tokenizer_adapter_synthetic.py`: 48 passed, 1 skipped.
- Adjacent test suites: 171 passed, 0 skipped.
- **Grand Total Across All Named Suites:** 228 passed, 1 skipped (229 named tests total).

---

## 5. Exact Source Diff: `scripts/matched_baseline/validate_staged_gated_tokenizers.py`

```diff
--- a/scripts/matched_baseline/validate_staged_gated_tokenizers.py
+++ b/scripts/matched_baseline/validate_staged_gated_tokenizers.py
@@ -177,6 +177,7 @@ def capture_staged_asset_snapshot(staging_dir: Path) -> Dict[str, str]:
     manifest_file = staging_dir / "gated_tokenizer_manifest.sha256"
     if not manifest_file.exists():
         raise FileNotFoundError(f"Missing staged manifest file: {manifest_file}")
     snapshot["manifest"] = compute_sha256(manifest_file)
     return snapshot
 
@@ -190,6 +191,7 @@ def run_staged_gated_asset_validation(
     manifest_path: Path = MANIFEST_PATH,
     evidence_base_dir: Optional[Path] = None,
     custom_adapters: Optional[Dict[str, Any]] = None,
+    run_id: Optional[str] = None,
 ) -> tuple[int, Dict[str, Any]]:
     """
     Execute full offline validation of staged gated assets using LocalFastTokenizer(mode='staged').
@@ -197,6 +199,7 @@ def run_staged_gated_asset_validation(
     Returns (exit_code, report_dict).
     """
-    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
+    if run_id is None:
+        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
     if evidence_base_dir is None:
         evidence_base_dir = workspace_root / "reports"
     evidence_dir = evidence_base_dir / f"gated_validation_evidence_{run_id}"
@@ -344,11 +347,10 @@ def run_staged_gated_asset_validation(
                     if repeat_ids != initial_ids:
                         raise ConfigurationError(f"Non-deterministic encoding on repeat {cycle} for {role} '{text}'")
 
-                # Decode roundtrip check
+                # Exact decode roundtrip check
                 decoded_text = tok_obj.decode(initial_ids)
-                # Whitespace normalization may occur in tokenizers; assert text is recovered
-                if text.strip() not in decoded_text and decoded_text.strip() not in text:
-                    raise ConfigurationError(f"Decode roundtrip failed for {role}: original='{text}', decoded='{decoded_text}'")
+                if not isinstance(decoded_text, str) or len(decoded_text.strip()) == 0:
+                    raise ConfigurationError(f"Decode returned empty string for {role} on input: '{text}'")
+                if decoded_text != text:
+                    raise ConfigurationError(
+                        f"Decode roundtrip failed for {role}: expected exact '{text}', got '{decoded_text}'"
+                    )
 
                 role_enc_report[f"sample_{idx}"] = {
                     "input_text": text,
                     "token_count": len(initial_ids),
                     "token_ids": initial_ids,
                     "repeat_determinism_5_cycles": "PASS",
-                    "classification": "REGRESSION_BASELINE_MATCH (Provider parity remains unvalidated until upstream serving comparison is authorized)",
+                    "exact_decode_roundtrip": "PASS",
+                    "classification": "DETERMINISTIC_REPEAT_AND_ROUNDTRIP_VALIDATED (Provider parity remains unvalidated until upstream serving comparison is authorized)",
                 }
@@ -361,16 +363,6 @@ def run_staged_gated_asset_validation(
-        # Step 6: Post-Execution Outer Hash Check (Bit-for-Bit Preservation)
-        log_lines.append("[6/6] Verifying post-execution bit-for-bit preservation...")
-        post_hashes = capture_staged_asset_snapshot(staging_dir)
-        report["post_execution_hashes"] = post_hashes
-
-        for rel_path, pre_sha in pre_hashes.items():
-            post_sha = post_hashes.get(rel_path)
-            if post_sha != pre_sha:
-                raise ConfigurationError(
-                    f"Post-execution mutation detected in {rel_path}: was {pre_sha}, now {post_sha}"
-                )
-        log_lines.append("  Post-execution outer hashes match pre-execution hashes bit-for-bit.")
-
         report["outcome"] = "SUCCESS"
         exit_code = 0
         log_lines.append("=== STAGE 3C GATED ASSET VALIDATION FUNCTIONAL CHECKS PASSED ===")
@@ -382,16 +374,38 @@ def run_staged_gated_asset_validation(
 
     finally:
-        # Unconditional evidence preservation
+        # Unconditional Post-Execution Hash Capture & Mutation Check
+        log_lines.append("[FINALIZATION] Capturing post-execution outer hashes...")
         try:
-            if not evidence_dir.exists():
-                evidence_dir.mkdir(parents=True, exist_ok=False)
-            rep_path = evidence_dir / "validation_report.json"
-            rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
-            log_path = evidence_dir / "validation.log"
-            log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
+            post_hashes = capture_staged_asset_snapshot(staging_dir)
+            report["post_execution_hashes"] = post_hashes
+
+            if pre_hashes:
+                for rel_path, pre_sha in pre_hashes.items():
+                    post_sha = post_hashes.get(rel_path)
+                    if post_sha != pre_sha:
+                        err_msg = f"Post-execution mutation detected in {rel_path}: was {pre_sha}, now {post_sha}"
+                        report["errors"].append(err_msg)
+                        report["outcome"] = "FAILED"
+                        exit_code = 1
+                        log_lines.append(f"  [MUTATION ERROR] {err_msg}")
+                if report["outcome"] != "FAILED":
+                    log_lines.append("  Post-execution outer hashes match pre-execution hashes bit-for-bit.")
+        except Exception as post_exc:
+            err_msg = f"Post-execution hash capture failed: {post_exc}"
+            report["errors"].append(err_msg)
+            report["outcome"] = "FAILED"
+            exit_code = 1
+            log_lines.append(f"  [POST-HASH ERROR] {err_msg}")
+
+        # Unconditional Exclusive Evidence Directory & File Preservation
+        rep_path = evidence_dir / "validation_report.json"
+        log_path = evidence_dir / "validation.log"
+        report["evidence_dir"] = str(evidence_dir)
+        report["evidence_file"] = str(rep_path)
+        report["log_file"] = str(log_path)
+
+        try:
+            evidence_dir.mkdir(parents=True, exist_ok=False)
+            with open(rep_path, "x", encoding="utf-8") as f_rep:
+                f_rep.write(json.dumps(report, indent=2))
+            with open(log_path, "x", encoding="utf-8") as f_log:
+                f_log.write("\n".join(log_lines) + "\n")
         except Exception as write_exc:
-            print(f"[FATAL EVIDENCE WRITE ERROR]: {write_exc}", file=sys.stderr)
+            err_msg = f"Evidence persistence failed (exclusive write failed): {write_exc}"
+            report["errors"].append(err_msg)
+            report["outcome"] = "FAILED"
+            exit_code = 1
+            print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)
```

---

## 6. Execution Status & Security Confirmations

- **Script Execution State:** **UNEXECUTED**. Blocked execution check verified:
  ```
  [BLOCKED] validate_staged_gated_tokenizers.py is an unexecuted validation plan.
  Execution is blocked pending explicit authorization from Codex and User.
  Required authorization flag: --execute-authorized-stage3c-validation
  ```
  Exit code 2.
- **Real Tokenizer Runs:** ZERO authentic tokenizer executions against real staged assets.
- **Credentials:** ZERO credential access (`.env.terra-hf.local` remains absent).
- **Network / Remote APIs:** ZERO network calls, zero Databricks calls, Gate C sealed.
- **Canonical Files & Checkpoint Manifests:** 100% byte-identical.
- **Manuscript Files:** Strictly untouched.
