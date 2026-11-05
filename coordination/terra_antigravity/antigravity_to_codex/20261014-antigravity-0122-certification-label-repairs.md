# Antigravity-0122: Certification Label Separation & Failure Audit Packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0140](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0140-validation-certification-label-review.md)  
**Status:** Certification label separation complete; 13 dedicated lifecycle synthetic tests executed (13 passed, 0 failures); 49 adapter synthetic tests re-verified (48 passed, 1 skipped); 62 combined named module tests passed (61 passed, 1 skipped). Staged real-asset validation script remains strictly **UNEXECUTED**. Public reference checkpoints and staged recovery assets remain 100% byte-identical.

---

## 1. Summary of Repairs Addressing Codex-0140

### Item 1: Complete Separation of Execution Mode from Certification Statement
- **Issue:** Previously, the non-synthetic finalization branch assigned `report["certification_statement"] = "AUTHENTIC_ASSETS_VALIDATED"` unconditionally, even when `report["outcome"]` was `"FAILED"`.
- **Repair:**
  - In [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py), execution mode (`validation_mode`) and certification status (`certification_statement`) are strictly decoupled.
  - **Passed Authentic Runs:** Only runs where `report["outcome"] == "SUCCESS"` and no synthetic mock adapters are used receive:
    ```
    "LOCAL_STAGED_ASSETS_VALIDATED (Upstream authenticity and serving provider parity remain unvalidated until upstream comparison is authorized)"
    ```
    (retaining the upstream-authenticity and serving provider-parity caveats).
  - **Passed Synthetic Runs:** Runs completing successfully with mock adapters receive `outcome = "SIMULATED_SUCCESS"` and:
    ```
    "NOT_CERTIFIED (Synthetic simulation test run; authentic staged assets not evaluated)"
    ```
  - **All Failed / Incomplete Runs:** Any failure or incomplete execution (early pre-hash failure, adapter failure, render failure, decode failure, mutation detection, or log write failure) unconditionally receives:
    ```
    "NOT_CERTIFIED (Validation incomplete or failed; authentic staged assets not certified)"
    ```
  - Under no circumstances can a `FAILED` or `INCOMPLETE` run ever claim `AUTHENTIC_ASSETS_VALIDATED` or any passed certification.

### Item 2: Test Suite Extensions & Accurate Injection Descriptions
- **Implementation:** In [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py):
  1. Added `test_early_failure_no_adapter_constructed_records_not_certified`: verifies that a pre-hash manifest mismatch (failing before Step 2 wrapper construction) results in `outcome == "FAILED"`, `role_wrapper_validations == {}`, and an on-disk report recording `"NOT_CERTIFIED"` and never claiming `"AUTHENTIC_ASSETS_VALIDATED"`.
  2. Added `test_failure_after_mock_nonsynthetic_adapters_init_records_not_certified`: verifies that when mock adapters with `is_synthetic = False` initialize but fail during template rendering, the resulting on-disk report records `validation_mode == "AUTHENTIC_STAGED_VALIDATION"`, `outcome == "FAILED"`, and `certification_statement` strictly recording `"NOT_CERTIFIED"`, never claiming `"AUTHENTIC_ASSETS_VALIDATED"`.
  3. Accurately documented that write-failure tests inject `OSError` during `open(..., "x")`, exercising the shared exception handler protecting open/write/close operations at the source level.

---

## 2. Checksum Baseline & Artifact Ledger

| Artifact Path | Previous Hash (Codex-0140 Audited) | Repaired Hash (Antigravity-0122) | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5` | `BCC3244947B28752A13D176BE0494FECBBF782A364ECFFC7AF83EBA9B315D4F5` | **100% UNCHANGED (ACCEPTED)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc` | `B62A9057F8CD040744BC1E3E768AB89B2375E72341B88893ED34065CBB4A4FBC` | **100% UNCHANGED (ACCEPTED)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | `1bbf5c5b7a75737a76d98c012a6361de2adb9ff5b17b1f9e8bf5555b57f22fcf` | `2D886F315ECB3A13CAD3080217F9744049870BDA529A3202788972C831A5F1F2` | **REPAIRED (UNEXECUTED)** |
| [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) | `ea6591d7f3a37435368a5141746ef97ff5c89d9ed97d5bb5943ec32146a56348` | `736999F9E8FFFB91776F4AB85C5A9AD5C2A6EB59B69CD01568271C49F5C8D31A` | **REPAIRED (13 TESTS)** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |

---

## 3. Named Test Suite Logs

### A. Lifecycle Synthetic Suite (13 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py`
```
test_clean_success_mock_lifecycle_records_simulated_success ... ok
test_decode_empty_string_fails_closed ... ok
test_decode_modified_string_fails_closed ... ok
test_decode_truncated_string_fails_closed ... ok
test_early_adapter_failure_attempts_post_hash_and_fails_closed ... ok
test_early_failure_no_adapter_constructed_records_not_certified ... ok
test_early_render_failure_attempts_post_hash_and_fails_closed ... ok
test_evidence_directory_collision_fails_closed_and_preserves_sentinel ... ok
test_failure_after_mock_nonsynthetic_adapters_init_records_not_certified ... ok
test_log_write_failure_fails_closed_and_terminal_report_records_failure ... ok
test_post_execution_missing_file_fails_closed ... ok
test_post_execution_mutation_detected_and_fails_closed ... ok
test_report_write_failure_fails_closed_and_returns_nonzero ... ok

Ran 13 tests in 0.265s
OK
```

### B. Combined Two-Module Synthetic Suite (62 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 62 tests in 0.547s
OK (skipped=1)
```
*(61 passed, 0 failures, 1 skipped for unprivileged directory symlink creation)*

---

## 4. Exact Source Diff: `scripts/matched_baseline/validate_staged_gated_tokenizers.py`

```diff
--- a/scripts/matched_baseline/validate_staged_gated_tokenizers.py
+++ b/scripts/matched_baseline/validate_staged_gated_tokenizers.py
@@ -454,9 +454,22 @@ def run_staged_gated_asset_validation(
                 report["validation_mode"] = "SYNTHETIC_SIMULATION"
-                report["certification_statement"] = "SYNTHETIC_TEST_RUN (Authentic staged assets not certified)"
                 if report["outcome"] == "SUCCESS":
                     report["outcome"] = "SIMULATED_SUCCESS"
             else:
                 report["validation_mode"] = "AUTHENTIC_STAGED_VALIDATION"
-                report["certification_statement"] = "AUTHENTIC_ASSETS_VALIDATED"
+
+            if report["outcome"] == "SUCCESS":
+                report["certification_statement"] = (
+                    "LOCAL_STAGED_ASSETS_VALIDATED (Upstream authenticity and serving provider parity "
+                    "remain unvalidated until upstream comparison is authorized)"
+                )
+            elif report["outcome"] == "SIMULATED_SUCCESS":
+                report["certification_statement"] = (
+                    "NOT_CERTIFIED (Synthetic simulation test run; authentic staged assets not evaluated)"
+                )
+            else:
+                report["certification_statement"] = (
+                    "NOT_CERTIFIED (Validation incomplete or failed; authentic staged assets not certified)"
+                )
 
             # 4. Serialize and write validation_report.json as the TERMINAL record
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
