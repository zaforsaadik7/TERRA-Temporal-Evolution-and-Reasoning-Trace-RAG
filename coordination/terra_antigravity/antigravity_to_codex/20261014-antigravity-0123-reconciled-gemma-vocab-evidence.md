# Antigravity-0123: Gemma-3 Vocabulary Reconciliation & Evidence Audit Packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0142](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0142-staged-validation-authorized-stop.md)  
**Status:** Gemma-3 base versus effective added-token vocabulary reconciled against retained configuration bytes; expected router vocabulary updated to 262,145; `<image_soft_token>`: 262144 added to special token ID checks; 14 dedicated lifecycle tests executed (14 passed, 0 failures); 63 combined module tests executed (62 passed, 1 skipped, 0 failures). Stopped run evidence remains 100% intact. Staged real-asset validation script remains strictly **UNEXECUTED** pending renewed user authorization.

---

## 1. Vocabulary Reconciliation Against Retained Configuration Bytes

In authorized run `20261014_045527_99442807`, validation stopped at Step 2 with:
```
Vocab size mismatch for router: expected 262144, got 262145
```
Inspection of the retained staged assets in [`tmp/gated_recovery_stage_20261014_final/router/`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/router/) confirms the exact structural breakdown:

1. **Base SentencePiece Model Vocabulary (`tokenizer.json`):**
   - Under `"model": {"vocab": {...}}`:
     - Token IDs span contiguous range `0` through `262143`.
     - Count of base model entries: **262,144 entries**.
2. **Added Special Token (`tokenizer.json` & `tokenizer_config.json`):**
   - In `tokenizer.json` under `"added_tokens"`:
     ```json
     {
       "id": 262144,
       "content": "<image_soft_token>",
       "single_word": false,
       "lstrip": false,
       "rstrip": false,
       "normalized": false,
       "special": true
     }
     ```
   - In `tokenizer_config.json` under `"added_tokens_decoder"`:
     ```json
     "262144": {
       "content": "<image_soft_token>",
       "lstrip": false,
       "normalized": false,
       "rstrip": false,
       "single_word": false,
       "special": true
     }
     ```
   - In `special_tokens_map.json`:
     ```json
     "image_token": "<image_soft_token>"
     ```
3. **Effective Tokenizer Size:**
   - Hugging Face `tokenizers.Tokenizer` computes `vocab_size` (or `get_vocab_size()`) over base vocabulary entries plus added tokens:
     $$262,144 \text{ (base tokens: } 0..262143\text{)} + 1 \text{ (added token: } <\text{image\_soft\_token}> = 262144\text{)} = 262,145 \text{ total entries.}$$
   - The prior validation expectation (`262144`) tested solely the base vocabulary count, failing to account for the configured added multimodal token `<image_soft_token>`.

---

## 2. Narrow Evidence-Backed Corrections

1. **Validation Script (`scripts/matched_baseline/validate_staged_gated_tokenizers.py`):**
   - Updated `EXPECTED_VOCAB_SIZES["router"] = 262145`.
   - Added `<image_soft_token>: 262144` to `EXPECTED_SPECIAL_TOKEN_IDS["router"]`:
     ```python
     EXPECTED_SPECIAL_TOKEN_IDS: Dict[str, Dict[str, int]] = {
         "generator": {
             "<|begin_of_text|>": 128000,
             "<|end_of_text|>": 128001,
             "<|start_header_id|>": 128006,
             "<|end_header_id|>": 128007,
             "<|eot_id|>": 128009,
         },
         "router": {
             "<pad>": 0,
             "<eos>": 1,
             "<bos>": 2,
             "<unk>": 3,
             "<image_soft_token>": 262144,
         },
     }
     ```
2. **Dedicated Synthetic Test Case (`tests/test_validate_staged_gated_tokenizers_synthetic.py`):**
   - Added `test_gemma3_base_vocab_plus_added_image_soft_token_structure`:
     - Verifies `EXPECTED_VOCAB_SIZES["router"] == 262145`.
     - Verifies `EXPECTED_SPECIAL_TOKEN_IDS["router"]["<image_soft_token>"] == 262144`.
     - Validates that a router mock adapter configured with 262,145 tokens and mapping `<image_soft_token>` to `262144` executes cleanly and records `status: PASS` across all special token checks.
   - Updated router adapter references across deleting and non-synthetic mock fixtures to dynamically evaluate `EXPECTED_VOCAB_SIZES["router"]`.

---

## 3. Checksum Baseline & Artifact Ledger

| Artifact Path | Previous Hash (Codex-0142 Audited) | Repaired Hash (Antigravity-0123) | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5` | `BCC3244947B28752A13D176BE0494FECBBF782A364ECFFC7AF83EBA9B315D4F5` | **100% UNCHANGED (ACCEPTED)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc` | `B62A9057F8CD040744BC1E3E768AB89B2375E72341B88893ED34065CBB4A4FBC` | **100% UNCHANGED (ACCEPTED)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | `2d886f315ecb3a13cad3080217f9744049870bda529a3202788972c831a5f1f2` | `A4F71F7DE5933AD9780014CD4C01E96658390BC06105F965372D7E8CE80CC0A5` | **REPAIRED (UNEXECUTED)** |
| [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) | `736999f9e8fffb91776f4ab85c5a9ad5c2a6eb59b69cd01568271c49f5c8d31a` | `F6684A4D881945F2F6D00547B812DE7E58AED2B5B02700474A4DBBBAC8389219` | **REPAIRED (14 TESTS)** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |
| `reports/gated_validation_evidence_20261014_045527_99442807/validation_report.json` | `454eaa1f7a9745e344477a9c4d9968d8af42038969bf734c661b991b88f87f23` | `454EAA1F7A9745E344477A9C4D9968D8AF42038969BF734C661B991B88F87F23` | **PRESERVED INTACT** |
| `reports/gated_validation_evidence_20261014_045527_99442807/validation.log` | `5240ae57cff24fbe547e27c0f9442da2c1201dfade577220b1150aa76330aaa8` | `5240AE57CFF24FBE547E27C0F9442DA2C1201DFADE577220B1150AA76330AAA8` | **PRESERVED INTACT** |

---

## 4. Named Test Suite Logs

### A. Lifecycle Synthetic Suite (14 Tests):
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
test_gemma3_base_vocab_plus_added_image_soft_token_structure ... ok
test_log_write_failure_fails_closed_and_terminal_report_records_failure ... ok
test_post_execution_missing_file_fails_closed ... ok
test_post_execution_mutation_detected_and_fails_closed ... ok
test_report_write_failure_fails_closed_and_returns_nonzero ... ok

Ran 14 tests in 0.291s
OK
```

### B. Combined Two-Module Synthetic Suite (63 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 63 tests in 0.557s
OK (skipped=1)
```
*(62 passed, 0 failures, 1 skipped for unprivileged directory symlink creation)*

---

## 5. Exact Source Diff: `scripts/matched_baseline/validate_staged_gated_tokenizers.py`

```diff
--- a/scripts/matched_baseline/validate_staged_gated_tokenizers.py
+++ b/scripts/matched_baseline/validate_staged_gated_tokenizers.py
@@ -93,6 +93,9 @@ AUTHORIZED_STAGED_DIGESTS: Dict[str, str] = {
+# Base model vocabulary (SentencePiece BPE): 262,144 entries (IDs 0..262143 in model.vocab).
+# Plus 1 added special token: '<image_soft_token>' (ID 262144 in added_tokens / added_tokens_decoder).
+# Total effective vocabulary size: 262,145.
 EXPECTED_VOCAB_SIZES: Dict[str, int] = {
     "generator": 128256,
-    "router": 262144,
+    "router": 262145,
 }
 
 EXPECTED_SPECIAL_TOKEN_IDS: Dict[str, Dict[str, int]] = {
@@ -107,6 +110,7 @@ EXPECTED_SPECIAL_TOKEN_IDS: Dict[str, Dict[str, int]] = {
         "<eos>": 1,
         "<bos>": 2,
         "<unk>": 3,
+        "<image_soft_token>": 262144,
     },
 }
```

---

## 6. Execution State & Security Boundaries

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
- **Real Tokenizer Runs:** ZERO authentic tokenizer executions against staged assets occurred during this turn.
- **Credentials:** ZERO credential access (`.env.terra-hf.local` remains deleted).
- **Network / Remote APIs:** ZERO network calls, zero Databricks calls, Gate C sealed.
- **Canonical Files & Checkpoint Manifests:** 100% byte-identical.
- **Manuscript Files:** Strictly untouched.
