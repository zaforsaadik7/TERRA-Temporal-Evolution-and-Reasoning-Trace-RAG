# Antigravity-0100: Gated Tokenizer Downloader Implementation & Synthetic Test Evidence

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0116](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0116-gated-inventory-bounded-acceptance.md)  
**User Directive:** *"Prepare the gated-tokenizer downloader and fully synthetic tests under Codex-0116’s file lists and limits. Return the source, hashes and proposed command for Codex’s audit. Do not read credentials, download files or run authentic tokenizer tests yet. Llama access remains pending; Gemma access is confirmed."*  

---

## 1. Executive Summary & Strict Containment

In compliance with the user's directive and [Codex-0116](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0116-gated-inventory-bounded-acceptance.md), Antigravity has implemented the gated tokenizer downloader and its companion fully synthetic unit test suite.

**Containment Discipline Maintained:**
- **Zero Network Activity:** No downloads were initiated; no network connections were established.
- **Zero Credential Access:** No environment variables or credentials (`HF_TOKEN`, Databricks keys, etc.) were read, logged, or processed.
- **Zero Authentic Execution:** Authentic tokenizer tests remain paused.
- **Access Differential Enforced:** Router (`google/gemma-3-12b-it`) is classified as `ACCESS_CONFIRMED`; Generator/Verifier (`meta-llama/Llama-3.3-70B-Instruct`) is classified as `ACCESS_PENDING_USER_APPROVAL`.
- **Existing Asset Immutability:** The 8-file public manifest [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) (SHA-256: `41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44`) and the Stage 3B public test suite remain 100% byte-for-byte preserved.

---

## 2. Downloader Architecture & Safeguards

The downloader is implemented in [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py):

### 2.1 File Lists & Role Limits (Strictly Enforcing Codex-0116)
- **Router (`google/gemma-3-12b-it` @ `96b6f1eccf38110c56df3a15bffe176da04bfd80`):**
  - **4 files:** `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `chat_template.json`.
  - **Excluded:** `tokenizer.model` is excluded.
  - **Hard Byte Ceiling:** **38,000,000 bytes** (38 MB).
  - **Status:** `ACCESS_CONFIRMED`.
- **Generator & Verifier (`meta-llama/Llama-3.3-70B-Instruct` @ `6f6073b423013f6a7d4d9f39144961bfbfbc386b`):**
  - **3 files:** `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`.
  - **Hard Byte Ceiling:** **22,000,000 bytes** (22 MB).
  - **Status:** `ACCESS_PENDING_USER_APPROVAL` (cleanly skipped unless explicitly authorized).

### 2.2 Operational Safeguards Implemented
1. **Safe Redirect Handler (`SafeHuggingFaceRedirectHandler`):**
   - Restricts HTTP redirects exclusively to approved domains (`huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.huggingface.co`).
   - If redirected to an unapproved domain, immediately raises `UnsafeRedirectError`.
   - Strips `Authorization` headers when redirecting from `huggingface.co` to CDN storage endpoints, preventing token forwarding.
2. **Continuous Streaming Byte-Ceiling Enforcement:**
   - Reads incoming data in 64 KB chunks. If total bytes exceed the remaining role allowance, raises `ByteCeilingExceededError` immediately and cleans up `.part` temporary files.
3. **Content Integrity Verification:**
   - Detects and rejects HTML error documents (`<!doctype html` or `<html`) via `CorruptPayloadError`.
   - Detects and rejects unexpanded Git LFS pointer text (`version https://git-lfs.github.com/spec/v1`).
   - Parses `.json` files with `json.load()` to verify syntax validity before finalizing.
4. **Staging Isolation & Non-Overwrite Enforcement:**
   - Targets fresh staging subdirectories (`<staging_dir>/router/` and `<staging_dir>/generator/`).
   - Checks for directory collision: if staging directory already exists and contains files, fails closed with exit code `2`.
   - Emits `GATED_ACQUISITION_REPORT.json` and a staging manifest `gated_tokenizer_manifest.sha256` into the isolated staging folder.
5. **Zero Credential Leakage:**
   - If a token is provided at runtime, it is injected into the HTTP request headers only; it is never printed to stdout/stderr, never written to disk, and never included in `GATED_ACQUISITION_REPORT.json`.

---

## 3. Synthetic Unit Test Evidence

The companion synthetic test suite is implemented in [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py).

### 3.1 Test Coverage (13 Tests)
- `test_safe_redirect_handler_blocks_unapproved_domain`: Verifies redirect to untrusted host raises `UnsafeRedirectError`.
- `test_safe_redirect_handler_strips_auth_header_on_cdn_redirect`: Verifies `Authorization` header is removed upon CDN redirect.
- `test_download_stream_and_validate_success`: Verifies clean download, SHA-256 calculation, and temporary file cleanup.
- `test_download_stream_rejects_html_error_page`: Verifies HTML documents are rejected and `.part` files unlinked.
- `test_download_stream_rejects_git_lfs_pointer`: Verifies Git LFS pointer text is rejected and `.part` files unlinked.
- `test_download_stream_rejects_malformed_json`: Verifies invalid JSON fails closed.
- `test_download_stream_exceeds_byte_ceiling`: Verifies ceiling breach halts stream and cleans up `.part` file.
- `test_download_stream_http_401_403_access_denied`: Verifies HTTP 401/403 maps to `GatedAccessDeniedError`.
- `test_acquire_gated_tokenizers_directory_collision_fails_closed`: Verifies existing populated staging directory returns exit code `2`.
- `test_acquire_gated_tokenizers_router_confirmed_success`: Verifies mocked successful acquisition of all 4 Gemma files produces manifest and exit code `0`.
- `test_acquire_gated_tokenizers_generator_skipped_when_access_pending`: Verifies `ACCESS_PENDING_USER_APPROVAL` roles are cleanly skipped with status `SKIPPED_PENDING_ACCESS` (exit code `3`).
- `test_acquire_gated_tokenizers_token_never_logged_or_in_report`: Verifies sensitive tokens are completely absent from report payloads.
- `test_acquire_gated_tokenizers_invalid_role_fails_closed`: Verifies unknown roles fail closed with exit code `1`.

### 3.2 Execution Result
Executed via project virtual environment:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_acquire_gated_tokenizers_synthetic.py
```
**Result:** 13/13 tests passed in 0.090s (exit code 0, 0 skips, 0 failures, 0 errors). Full combined synthetic suite passes 41/41 tests (0.542s, 1 platform symlink skip).

---

## 4. Delivered Source Artifacts & Checksums

| File Path | Byte Count | SHA-256 Checksum | Role |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 17,446 bytes | `4e31cf63b35b11e1a6d7e3f1b20ae2aa6d999f6d0c3fb27e2042260038b1ece5` | Stage 3C bounded gated downloader |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 14,553 bytes | `1b32e636e6fc9d64e8393c431ffa63e9177836f4223b13dbec16a65678c52ce2` | Fully synthetic unit test suite |

---

## 5. Proposed Execution Command (Awaiting User & Codex Authorization)

When authorized, the confirmed Gemma router role can be executed selectively:

```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m scripts.matched_baseline.acquire_gated_tokenizers --roles router
```

Or for both roles (once Llama access is confirmed):
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m scripts.matched_baseline.acquire_gated_tokenizers --roles router,generator
```

*Note: Execution remains strictly paused awaiting Codex audit and explicit user authorization.*
