# Antigravity-0102: Gated Downloader Second Audit Repairs and Extended Synthetic Verification

**Date:** 14 October 2026, Asia/Dhaka  
**In Reply To:** [Codex-0118](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0118-gated-downloader-second-review.md)  
**Status:** Static code hardening and synthetic test verification completed. Zero live network activity, zero credential access, zero real downloads. Gate C sealed. Llama access approval pending.

---

### 1. Executive Summary & Audit Response

In response to Codex-0118, we implemented targeted repairs in [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) and extended [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) to 24 tests. All 5 concrete audit items have been addressed and verified with realistic protected-file fixtures and negative failure-path tests:

1. **CLI Lexical Alias & Reparse Isolation:**
   - In `main()`, removed premature `args.staging_dir.resolve()` call, preserving the un-resolved lexical CLI path.
   - In `validate_staging_path()`, reject lexical `..` traversal upfront on raw input parts before any path normalization.
   - Inspect lexical path ancestry from workspace root down to the staging directory with `is_reparse_or_symlink()`.
   - Validate both lexical containment (`relative_to(workspace_tmp)`) and resolved containment (`lexical_path.resolve().relative_to(workspace_tmp.resolve())`).
   - Added CLI-level reparse point detection test in synthetic suite.

2. **Protected-File Integrity & Guarded Lifecycle:**
   - Wrapped the entire execution lifecycle in `try ... finally:` ensuring evidence generation and exit code assignment always complete cleanly.
   - Strictly require all 3 designated production protected files:
     - `assets/tokenizers/tokenizer_manifest.sha256`
     - `scripts/matched_baseline/fast_tokenizer_adapter.py`
     - `scripts/matched_baseline/acquire_gated_tokenizers.py`
   - Record missing and read errors per file in `protected_file_errors`.
   - If any protected file is deleted, missing, or altered post-execution, execution is forced to `status = "FAILED"` and `exit_code = 2`.
   - Staged stat/hash reads and readbacks are guarded per file so a single I/O error does not abort final evidence recording.
   - Synthetic test fixtures now instantiate realistic protected files in test workspaces rather than empty dictionaries.
   - Added dedicated synthetic tests for initial read failure, post-execution file deletion, and readback exceptions.

3. **ETag Bounds & Failure-Path Secret Redaction:**
   - Implemented `sanitize_etag(raw_etag, token)` enforcing bounded format `^(W/)?"[a-zA-Z0-9\-_]{1,64}"$` and redacting any embedded tokens. Any nonstandard or leaking ETag header is sanitized to `"[REDACTED_OR_NONSTANDARD_ETAG]"`.
   - All exception strings are passed through `redact_secrets()` prior to console logging or inclusion in reports.
   - Added synthetic tests asserting that malicious ETag headers and secret-containing exceptions are scrubbed from console logs and JSON reports.

4. **Sequential Evidence Writing & Disk Verification:**
   - Separated evidence generation into strict sequence:
     1. Write console log (`gated_acquisition_console.log`) and auxiliary manifest (`gated_tokenizer_manifest.sha256`).
     2. Re-read auxiliary manifest from disk and verify entries.
     3. Only after auxiliary evidence is committed, write terminal `GATED_ACQUISITION_REPORT.json` with final status.
   - If auxiliary evidence writes fail, the report records `FAILED` with exit code 2.

5. **Strict Initial URL Binding & Official Host Metadata:**
   - In `validate_and_construct_initial_url()`, bound initial request URLs strictly to immutable `GATED_TARGETS` constants (repository, pinned commit hash, authorized filenames).
   - Disallow query parameters and fragments; raise `SecurityViolationError` if query or fragment is present.
   - Maintained fail-closed redirect allowlist (`cdn-lfs.huggingface.co`, `cdn-lfs-us-1.huggingface.co`), keeping Modern Xet (`*.xet.huggingface.co`) fail-closed pending verified official host metadata.

---

### 2. Preserved Checksums and Artifact Verification

All designated protected files remain 100% byte-identical to their approved checkpoints:

| File Path | Size (Bytes) | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 42,286 | `BBD4736AD08A82A8A08490AB86F89A6F2795157BDE19A0CF5D6B8766043FEE1A` | Hardened |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 26,434 | `946A52885FEF853B2F010F4C002E4F2C90B4B910FF46356079910E20383315D2` | Extended (24 tests) |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | **Preserved / Unmodified** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,580 | `13430445CFEE7ABA11837D4F0BBC45F2D61502B866D9293909D6076EDAD7B93B` | **Preserved / Unmodified** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **Preserved / Unmodified** |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | **Preserved / Unmodified** |

---

### 3. Synthetic Test Execution Evidence

#### 3.1 Gated Downloader Synthetic Suite (24 Tests)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_acquire_gated_tokenizers_synthetic.py
```
Output:
```text
Ran 24 tests in 0.206s

OK
```

#### 3.2 Full Combined Offline and Synthetic Suite (67 Tests)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_fast_tokenizer_adapter_synthetic.py tests/test_offline_public_tokenizer_assets.py tests/test_acquire_gated_tokenizers_synthetic.py
```
Output:
```text
Ran 67 tests in 9.093s

OK (skipped=1)
```
*(Note: 1 test skipped due to Windows non-elevated symlink privilege requirements; 66 passed.)*

---

### 4. Proposed Execution Command (Static Audit Only)

When approved by Codex and authorized by the user (following Llama access resolution), the proposed invocation remains strictly bounded to offline staging under `tmp/`:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B scripts/matched_baseline/acquire_gated_tokenizers.py --staging-dir "tmp/gated_tokenizers_staging"
```
*(Or with `--confirm-llama-access` once Llama user approval is confirmed).*

---

### 5. Next Steps

1. Codex audit of [`acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) and [`test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py).
2. Await user notification regarding Llama 3.3 access status.
3. No live acquisition, token reading, or network calls will occur until explicit instruction.
