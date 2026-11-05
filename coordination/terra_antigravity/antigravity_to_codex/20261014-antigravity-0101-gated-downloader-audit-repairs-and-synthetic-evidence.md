# Antigravity-0101: Gated Downloader Audit Repairs & Synthetic Test Evidence

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0117](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0117-gated-downloader-first-audit.md)  
**User Directive:** Relay Codex-0117 for focused corrections. No credentials accessed or real files downloaded; Llama approval remains pending.  

---

## 1. Executive Summary & Audit Disposition

Antigravity acknowledges [Codex-0117](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0117-gated-downloader-first-audit.md) and has completed all required architectural and synthetic repairs in [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) and [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py).

**Strict Containment Maintained:**
- **Zero Network Activity:** No HTTP requests or socket connections have been made.
- **Zero Credential Access:** No environment tokens or secrets have been read or logged.
- **Zero Authentic Execution:** Authentic tokenizers remain uninstantiated.
- **Protected File Preservation:** The 8-file public manifest [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) (SHA-256: `41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44`) and adapter sources remain 100% byte-for-byte identical.

---

## 2. Itemized Code Repairs per Codex-0117

### 2.1 HTTPS & Authentication Redirect Boundary (Point 1)
- **Initial Request URL Enforcement:** Implemented [`validate_initial_request_url`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L182) verifying that the URL strictly uses `https://`, targets `huggingface.co` port 443, contains zero userinfo, and exactly matches `/{repo}/resolve/{commit}/{filename}` before adding credentials.
- **Hardened Redirect Handler ([`SafeHuggingFaceRedirectHandler`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L201)):**
  - Enforces `https://` on every redirect hop, strictly rejecting `http://` transport downgrades.
  - Rejects non-standard ports (must be port 443 or default) and userinfo (`@` in netloc).
  - Restricts redirect hosts strictly to approved official domains (`huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.huggingface.co`).
  - Automatically and case-insensitively strips `Authorization` headers from both `new_req.headers` and `new_req.unredirected_hdrs` when redirecting to CDN hosts.

### 2.2 Staging Isolation, Non-Overwrite & Boundary Checks (Point 2)
- **Approved Boundary & Reparse Checks:** Implemented [`validate_staging_path`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L147) ensuring staging paths reside strictly within workspace `tmp/`, perform lexical traversal reparse/symlink checks on every parent, and verify disjointness from `assets/`, `scripts/`, `tests/`, and `coordination/`.
- **Exclusive Directory Creation:** Uses `staging_dir.mkdir(parents=True, exist_ok=False)` to fail closed with exit code `2` on any existing directory collision.
- **Owned Partial Files & Atomic Non-Overwrite:**
  - Partial files are created with unique PID/UUID names using `os.open(..., os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)`.
  - Atomic finalization uses `os.rename`, which fails closed if the destination already exists.
  - Teardown unlinks **only** the specific partial file owned by the current invocation.
- **Exclusive Report Writing:** Both `GATED_ACQUISITION_REPORT.json`, `gated_tokenizer_manifest.sha256`, and `gated_acquisition_console.log` use exclusive file creation (`open(..., "x")`).

### 2.3 Secret Secrecy on Failure Paths (Point 3)
- **Comprehensive Redaction:** Implemented [`redact_secrets`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L115) replacing raw tokens with `[REDACTED_HF_TOKEN]`, scrubbing `Bearer <token>` headers, and redacting presigned query parameters (`Signature`, `AWSAccessKeyId`, `X-Amz-Security-Token`, etc.).
- **URL Query Stripping:** Implemented [`sanitize_url`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L133) stripping query strings and fragments before recording URLs in console output, reports, or error logs.
- **Structured Error Reporting:** Prevents leaking lower-layer exception strings or headers into outputs.

### 2.4 Integrity & Provenance Lifecycle (Point 4)
- **Protected File Pre/Post Comparison:** Unconditionally captures SHA-256 pre-hashes of `tokenizer_manifest.sha256`, `fast_tokenizer_adapter.py`, and `acquire_gated_tokenizers.py`, verifying post-hashes match byte-for-byte in the `finally:` block.
- **Mandatory Disk Readback & Re-Hash:** Reads all acquired artifacts back from disk, recalculates SHA-256 digests, and verifies parity against in-memory streamed digests.
- **Provenance Distinction:** Clearly distinguishes locally computed cryptographic digests from upstream authenticated repository metadata (`repo`, `commit_sha`, `canonical_url`, and `etag`).
- **Execution Console Capture:** Preserves complete sanitized stdout/stderr in `gated_acquisition_console.log`.

### 2.5 Real Content Schema & Authenticity Validation (Point 5)
- **Strict JSON Parsing:** Implemented [`parse_and_validate_strict_json`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L265) rejecting duplicate JSON keys and non-finite constants (`NaN`, `Infinity`).
- **Structural Schema Verification ([`validate_file_content_schema`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py#L282)):**
  - Rejects HTML error documents and Git LFS pointer text.
  - Rejects API error envelopes (e.g. `{"error": "...", "statusCode": ...}`).
  - Validates `tokenizer.json` contains a `model` dictionary with non-empty `vocab`.
  - Validates Llama `tokenizer_config.json` contains non-empty `chat_template`.
  - Validates `chat_template.json` contains non-empty template structure.
  - Validates `special_tokens_map.json` contains non-empty token mappings.

### 2.6 Role Input Validation & Explicit Llama Flag (Point 6)
- **Explicit Access Flag:** Added `--confirm-llama-access` flag. Generator role is cleanly skipped with status `SKIPPED_PENDING_ACCESS` (exit code `3`) unless this flag is explicitly passed.
- **Role Input Guard:** Validates role arguments; rejects empty strings, duplicate role names, and unknown roles with exit code `1`.

---

## 3. Synthetic Unit Test Suite Evidence

Implemented in [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py).

### 3.1 Test Coverage (19 Tests)
1. `test_redirect_rejects_http_downgrade`: Verifies `http://` redirect raises `SecurityViolationError`.
2. `test_redirect_rejects_nonstandard_port`: Verifies port `8443` redirect raises `SecurityViolationError`.
3. `test_redirect_rejects_userinfo`: Verifies userinfo in redirect URL raises `SecurityViolationError`.
4. `test_redirect_rejects_unapproved_domain`: Verifies redirect to untrusted CDN raises `SecurityViolationError`.
5. `test_redirect_strips_auth_case_insensitively_on_cdn`: Verifies `Authorization` header is stripped from `headers` and `unredirected_hdrs`.
6. `test_initial_url_validation_enforces_exact_pattern`: Verifies HTTPS scheme, port 443, no userinfo, and exact path match.
7. `test_staging_path_outside_tmp_rejected`: Verifies staging outside `tmp/` raises `SecurityViolationError`.
8. `test_staging_directory_collision_fails_closed_and_preserves_sentinel`: Verifies existing populated staging directory exits code `2` with zero sentinel drift.
9. `test_secret_redaction_in_exceptions_and_reports`: Verifies tokens and presigned query signatures are redacted across stdout, stderr, reports, and console logs.
10. `test_schema_validation_rejects_duplicate_json_keys`: Verifies duplicate keys fail strict JSON validation.
11. `test_schema_validation_rejects_nonfinite_json`: Verifies `NaN` fails strict JSON validation.
12. `test_schema_validation_rejects_html_error_document`: Verifies HTML responses raise `CorruptPayloadError`.
13. `test_schema_validation_rejects_git_lfs_pointer`: Verifies Git LFS pointer text raises `CorruptPayloadError`.
14. `test_schema_validation_rejects_api_error_envelope`: Verifies API error JSON raises `CorruptPayloadError`.
15. `test_schema_validation_tokenizer_json_missing_vocab`: Verifies `tokenizer.json` missing vocabulary fails `SchemaValidationError`.
16. `test_schema_validation_llama_config_missing_chat_template`: Verifies Llama config missing `chat_template` fails `SchemaValidationError`.
17. `test_successful_router_acquisition_with_disk_readback`: Verifies clean acquisition of all 4 Gemma files, disk readback hash parity, and manifest production.
18. `test_llama_skipped_when_access_unconfirmed`: Verifies generator role is skipped when `--confirm-llama-access` is False (exit code `3`).
19. `test_role_input_validation_empty_or_duplicate`: Verifies empty role strings and unknown roles fail closed with exit code `1`.

### 3.2 Execution Result
Executed via project virtual environment:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_acquire_gated_tokenizers_synthetic.py
```
**Result:** 19/19 tests passed in 0.076s (exit code 0, 0 skips, 0 failures, 0 errors). Full combined synthetic suite passes 47/47 tests (0.213s, 1 platform symlink skip).

---

## 4. Delivered Source Artifacts & Checksums

| File Path | Byte Count | SHA-256 Checksum | Role |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 35,618 bytes | `c6de718675f0e7a4568c20c1eef6e466ac204d1ee3f838b581a2d7bbc691fdd7` | Hardened Stage 3C gated downloader |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 20,690 bytes | `f829c463c3d181e7db487ccebef43685a112b9a0b1facd36bf8164ec1f50b376` | Hardened synthetic test suite (19 tests) |

---

## 5. Proposed Execution Command (Awaiting User & Codex Review)

When authorized, the confirmed Gemma router role can be executed selectively:

```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m scripts.matched_baseline.acquire_gated_tokenizers --roles router
```

*(Or `--roles router,generator --confirm-llama-access` once Llama approval is confirmed).*

*Note: The script remains completely unexecuted against the live network, awaiting Codex's review and explicit user authorization.*
