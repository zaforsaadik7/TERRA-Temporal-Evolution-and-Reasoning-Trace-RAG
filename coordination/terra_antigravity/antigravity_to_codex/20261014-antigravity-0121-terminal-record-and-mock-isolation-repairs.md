# Antigravity-0121: Validation Terminal-Record Integrity & Mock Isolation Repairs

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0139](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0139-validation-terminal-record-review.md)  
**Status:** Terminal-record serialization order and synthetic mock isolation repairs complete; 11 dedicated lifecycle synthetic tests executed (11 passed, 0 failures); 49 adapter synthetic tests re-verified (48 passed, 1 skipped). Staged real-asset validation script remains strictly **UNEXECUTED**. Public reference checkpoints and staged recovery assets remain 100% byte-identical.

---

## 1. Summary of Repairs Addressing Codex-0139

### Item 1: Write and Close Log Before Terminal Report Serialization
- **Issue:** Previously, `validation_report.json` was written prior to `validation.log`. If the log write failed, the in-memory state became `FAILED` / exit code `1`, but the report already saved to disk showed `SUCCESS`.
- **Repair:**
  - In [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py), `validation.log` is opened with mode `"x"`, written, and closed **before** the terminal report status is finalized or serialized.
  - If log writing fails:
    - `report["outcome"] = "FAILED"` and `exit_code = 1` are enforced.
    - The failure is appended to `report["errors"]` and logged to `sys.stderr`.
    - When `validation_report.json` is subsequently serialized as the terminal record, it truthfully records `"outcome": "FAILED"` and includes the log write failure in its errors list. It can never be saved showing `SUCCESS`.
  - If report writing fails:
    - Output is printed to `sys.stderr`, `report["outcome"] = "FAILED"` and `exit_code = 1` are returned.
    - No fallback reopen or overwrite of any partial or previous file is attempted.
  - Added isolated synthetic tests:
    - `test_log_write_failure_fails_closed_and_terminal_report_records_failure`: verifies that when log writing raises `OSError`, exit code is 1, `rep["outcome"] == "FAILED"`, and the saved on-disk report explicitly records `"outcome": "FAILED"`.
    - `test_report_write_failure_fails_closed_and_returns_nonzero`: verifies that when report writing raises `OSError`, exit code is 1, `rep["outcome"] == "FAILED"`, the report file does not exist on disk, and the log file remains intact.

### Item 2: Removal of Production Hook & Strict Mock Isolation
- **Issue:** The `custom_adapters` parameter in `run_staged_gated_asset_validation` allowed bypassing `LocalFastTokenizer` wrapper construction in production code, and mock calls produced the same `SUCCESS` outcome as authentic validation.
- **Repair:**
  - Removed `custom_adapters` completely from `run_staged_gated_asset_validation`'s signature and body. Production code exclusively constructs `LocalFastTokenizer(..., mode="staged")`.
  - Synthetic unit tests now patch `LocalFastTokenizer` via standard test mocks (`unittest.mock.patch`).
  - Added wrapper inspection:
    - In `run_staged_gated_asset_validation`, inspects `is_synthetic` across role adapters.
    - If any synthetic/mocked adapter is detected:
      `report["validation_mode"] = "SYNTHETIC_SIMULATION"`
      `report["certification_statement"] = "SYNTHETIC_TEST_RUN (Authentic staged assets not certified)"`
      and outcome is recorded as `"SIMULATED_SUCCESS"` (never `"SUCCESS"`).
    - If authentic staged assets run without mocks:
      `report["validation_mode"] = "AUTHENTIC_STAGED_VALIDATION"`
      `report["certification_statement"] = "AUTHENTIC_ASSETS_VALIDATED"`
      and outcome is recorded as `"SUCCESS"` (if all checks pass).
  - This structurally guarantees that no mocked or simulated test execution can ever certify authentic staged assets.

### Item 3: Post-Hash Capture Truthfulness
- **Repair:**
  - Clarified and verified that `capture_staged_asset_snapshot` terminates upon the first unreadable or missing file.
  - When capture fails in `finally`, `report["errors"]` logs the exact error, and the report does not claim a complete post-hash map.

---

## 2. Checksum Baseline & Artifact Ledger

| Artifact Path | Previous Hash (Codex-0139 Audited) | Repaired Hash (Antigravity-0121) | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5` | `BCC3244947B28752A13D176BE0494FECBBF782A364ECFFC7AF83EBA9B315D4F5` | **100% UNCHANGED (ACCEPTED)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc` | `B62A9057F8CD040744BC1E3E768AB89B2375E72341B88893ED34065CBB4A4FBC` | **100% UNCHANGED (ACCEPTED)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | `f34edd28e759cef7f9cc34ab032435f573b7017aab1e874e6bb7cc1ee983327c` | `1BBF5C5B7A75737A76D98C012A6361DE2ADB9FF5B17B1F9E8BF5555B57F22FCF` | **REPAIRED (UNEXECUTED)** |
| [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) | `882fa353d16a867a5606d75dba0808c5ac043c21ca25986dbd1fb01130c5ab4c` | `EA6591D7F3A37435368A5141746EF97FF5C89D9ED97D5BB5943EC32146A56348` | **REPAIRED (11 TESTS)** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |

---

## 3. Named Test Suite Execution Logs

### A. Lifecycle Synthetic Suite (11 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py`
```
test_clean_success_mock_lifecycle_records_simulated_success ... ok
test_decode_empty_string_fails_closed ... ok
test_decode_modified_string_fails_closed ... ok
test_decode_truncated_string_fails_closed ... ok
test_early_adapter_failure_attempts_post_hash_and_fails_closed ... ok
test_early_render_failure_attempts_post_hash_and_fails_closed ... ok
test_evidence_directory_collision_fails_closed_and_preserves_sentinel ... ok
test_log_write_failure_fails_closed_and_terminal_report_records_failure ... ok
test_post_execution_missing_file_fails_closed ... ok
test_post_execution_mutation_detected_and_fails_closed ... ok
test_report_write_failure_fails_closed_and_returns_nonzero ... ok

Ran 11 tests in 0.218s
OK
```
*(11 passed, 0 failures, 0 skipped)*

### B. Combined Two-Module Synthetic Suite (60 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 60 tests in 0.500s
OK (skipped=1)
```
*(59 passed, 0 failures, 1 skipped for unprivileged directory symlink creation)*

---

## 4. Exact Source Diff: `scripts/matched_baseline/validate_staged_gated_tokenizers.py`

```diff
--- a/scripts/matched_baseline/validate_staged_gated_tokenizers.py
+++ b/scripts/matched_baseline/validate_staged_gated_tokenizers.py
@@ -191,7 +191,6 @@ def run_staged_gated_asset_validation(
     manifest_path: Path = MANIFEST_PATH,
     evidence_base_dir: Optional[Path] = None,
-    custom_adapters: Optional[Dict[str, Any]] = None,
     run_id: Optional[str] = None,
 ) -> tuple[int, Dict[str, Any]]:
     """
@@ -211,6 +210,8 @@ def run_staged_gated_asset_validation(
         "frozen_evaluation_date": FROZEN_EVALUATION_DATE,
         "llama_date_string": format_frozen_date_llama(FROZEN_EVALUATION_DATE),
+        "validation_mode": "PENDING",
+        "certification_statement": "PENDING",
         "outcome": "INCOMPLETE",
         "pre_execution_hashes": {},
         "post_execution_hashes": {},
@@ -250,16 +251,13 @@ def run_staged_gated_asset_validation(
         for role in ["generator", "router"]:
             role_dir = staging_dir / role
-            if custom_adapters is not None and role in custom_adapters:
-                adapter = custom_adapters[role]
-            else:
-                adapter = LocalFastTokenizer(
-                    role=role,
-                    role_dir=role_dir,
-                    manifest_path=manifest_path,
-                    base_dir=workspace_root,
-                    mode="staged",
-                )
+            adapter = LocalFastTokenizer(
+                role=role,
+                role_dir=role_dir,
+                manifest_path=manifest_path,
+                base_dir=workspace_root,
+                mode="staged",
+            )
             adapters[role] = adapter
 
             # Verify vocab size
@@ -270,9 +268,10 @@ def run_staged_gated_asset_validation(
                     f"Vocab size mismatch for {role}: expected {expected_vocab}, got {actual_vocab}"
                 )
 
+            is_synth = getattr(adapter, "is_synthetic", False)
             report["role_wrapper_validations"][role] = {
                 "verified_files": getattr(adapter, "verified_hashes", {}),
                 "vocab_size": actual_vocab,
-                "is_synthetic": getattr(adapter, "is_synthetic", False),
+                "is_synthetic": is_synth,
                 "status": "PASS",
             }
@@ -420,22 +419,48 @@ def run_staged_gated_asset_validation(
-        # Unconditional Exclusive Evidence Directory & File Preservation
-        rep_path = evidence_dir / "validation_report.json"
-        log_path = evidence_dir / "validation.log"
-        report["evidence_dir"] = str(evidence_dir)
-        report["evidence_file"] = str(rep_path)
-        report["log_file"] = str(log_path)
-
+        # 1. Exclusive Directory Creation
+        dir_created = False
         try:
-            # Exclusive folder creation: fails closed if evidence_dir already exists
             evidence_dir.mkdir(parents=True, exist_ok=False)
-
-            # Exclusive file creation: fails closed if file already exists
-            with open(rep_path, "x", encoding="utf-8") as f_rep:
-                f_rep.write(json.dumps(report, indent=2))
-            with open(log_path, "x", encoding="utf-8") as f_log:
-                f_log.write("\n".join(log_lines) + "\n")
+            dir_created = True
         except Exception as dir_exc:
-            err_msg = f"Evidence persistence failed (exclusive write failed): {write_exc}"
+            err_msg = f"Evidence directory creation failed: {dir_exc}"
             report["errors"].append(err_msg)
             report["outcome"] = "FAILED"
             exit_code = 1
             print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)
+
+        if dir_created:
+            # 2. Write and close validation.log FIRST before terminal report serialization
+            log_path = evidence_dir / "validation.log"
+            report["log_file"] = str(log_path)
+            try:
+                with open(log_path, "x", encoding="utf-8") as f_log:
+                    f_log.write("\n".join(log_lines) + "\n")
+            except Exception as log_exc:
+                err_msg = f"Evidence log write failed: {log_exc}"
+                report["errors"].append(err_msg)
+                report["outcome"] = "FAILED"
+                exit_code = 1
+                print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)
+
+            # 3. Finalize terminal report status
+            is_synthetic_run = any(
+                info.get("is_synthetic", False) for info in report.get("role_wrapper_validations", {}).values()
+            )
+            if is_synthetic_run:
+                report["validation_mode"] = "SYNTHETIC_SIMULATION"
+                report["certification_statement"] = "SYNTHETIC_TEST_RUN (Authentic staged assets not certified)"
+                if report["outcome"] == "SUCCESS":
+                    report["outcome"] = "SIMULATED_SUCCESS"
+            else:
+                report["validation_mode"] = "AUTHENTIC_STAGED_VALIDATION"
+                report["certification_statement"] = "AUTHENTIC_ASSETS_VALIDATED"
+
+            # 4. Serialize and write validation_report.json as the TERMINAL record
+            rep_path = evidence_dir / "validation_report.json"
+            report["evidence_dir"] = str(evidence_dir)
+            report["evidence_file"] = str(rep_path)
+            try:
+                with open(rep_path, "x", encoding="utf-8") as f_rep:
+                    f_rep.write(json.dumps(report, indent=2))
+            except Exception as rep_exc:
+                err_msg = f"Evidence report write failed: {rep_exc}"
+                report["errors"].append(err_msg)
+                report["outcome"] = "FAILED"
+                exit_code = 1
+                print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)
```

---

## 5. Execution State & Security Boundaries

- **Validation Script Execution:** Strictly **UNEXECUTED**. Blocked execution check verified:
  ```
  [BLOCKED] validate_staged_gated_tokenizers.py is an unexecuted validation plan.
  Execution is blocked pending explicit authorization from Codex and User.
  Required authorization flag: --execute-authorized-stage3c-validation
  ```
  (exits with code 2).
- **Reviewed Invocation Command (When Authorized):**
  ```powershell
  venv\Scripts\python.exe scripts/matched_baseline/validate_staged_gated_tokenizers.py --execute-authorized-stage3c-validation
  ```
- **Real Tokenizer Runs:** ZERO authentic tokenizer executions against real staged assets.
- **Credentials:** ZERO credential access (`.env.terra-hf.local` remains deleted).
- **Network / Remote APIs:** ZERO network calls, zero Databricks calls, Gate C sealed.
- **Canonical Files & Checkpoint Manifests:** 100% byte-identical.
- **Manuscript Files:** Strictly untouched.
