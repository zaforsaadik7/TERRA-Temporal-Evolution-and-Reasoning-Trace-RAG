# Antigravity-0089: Stage 3A Source Implementation & Synthetic Test Evidence

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0105](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0105-stage3a-code-scope-and-install-hash-control.md) & User Directive (14 Oct 2026)  
**Governance Scope:** Stage 3A Code & Synthetic Tests Only. Zero package installations executed, zero authentic asset loading (assets/tokenizers/ untouched), zero model execution, zero real-data reads (Gate C sealed), zero live API calls, zero credentials handled.

---

## 1. Executive Summary & Delivery Checklist

Under user authorization and the binding controls of Codex-0105, Stage 3A source code and 100% genuinely synthetic unit tests have been implemented, verified, and delivered:

1. **Delivered Source Modules:**
   - [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) (14,562 bytes, SHA-256: `75319bdeac4922249baeec826bb06f61f5ac67c65203db77f0ec65dc3df78377`).
   - [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) (12,050 bytes, SHA-256: `6bb9690aca47ad6315d133aeac1fd09f9de64815d000e764f434f7ee3a13f05f`).
2. **100% Genuinely Synthetic Isolation:**
   - Suite A operates exclusively inside temporary fixture sandboxes (`tempfile.TemporaryDirectory`).
   - Zero files in `assets/tokenizers/` were accessed, loaded, or modified.
3. **Fail-Closed Block When Jinja is Absent:**
   - With `jinja2` uninstalled, `JinjaChatTemplateRenderer` correctly reports `is_available=False`. Calling `render()` raises `DependencyMissingError` with an explicit diagnostic message.
   - Zero attempts were made to install Jinja2 or bypass template execution.
4. **All 130 Synthetic Tests Pass:**
   - All 11 new adapter synthetic tests pass in 0.105s.
   - All 4 approved named synthetic test modules pass collectively: **130 tests pass in 3.998s** (exit code 0).
5. **Gated Status Maintained:**
   - Two-wheel package installation remains separately gated.
   - Stage 3B authentic public asset testing remains separately gated.
   - Gate C real data preflight remains sealed.

---

## 2. Technical Architecture Delivered

### 2.1 Multi-Artifact Pre-Read Verification (`verify_role_artifacts`)
- **Mandatory File Inventories:**
  - `judge2`: `tokenizer.json`, `chat_template.jinja`, `tokenizer_config.json`, `special_tokens_map.json`.
  - `judge1`: `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`.
- **Path Containment & Security:** Asserts that `role_dir` resolves within `base_dir` and each file resolves strictly inside `role_dir`. Symlinks, junctions, or directory traversal attempts raise `SecurityViolationError` or `ConfigurationError`.
- **Full Manifest Hash Checking:** Computes SHA-256 for each mandatory file and compares against [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256). Any mismatch or missing file raises `ConfigurationError`.
- **Extraneous Artifact Detection:** Scans the directory for unmanifested extra files; presence of any unexpected file raises `ConfigurationError`.

### 2.2 Sandboxed `JinjaChatTemplateRenderer`
- **Dependency Guard:** Verifies availability of `jinja2`. If absent, raises `DependencyMissingError`.
- **Sandboxed Jinja Environment:**
  - Loads with `extensions=['jinja2.ext.loopcontrols']`.
  - Disables HTML auto-escaping (`autoescape=False`) to preserve raw prompt tokens.
  - Filters: `tojson` maps to `json.dumps(val, ensure_ascii=False)` matching HF upstream behavior rather than Jinja default HTML escaping.
  - Globals:
    - `strftime_now(fmt)`: returns frozen UTC evaluation timestamp `2026-10-14` to prevent time-based token drift.
    - `raise_exception(msg)`: maps to `TemplateRenderingError`.
- **Strict Input Validation:** Enforces list-of-dicts message schema; checks role in `{"system", "user", "assistant", "developer"}`; enforces string contents; explicitly rejects tool calls and unconfigured schemas.

### 2.3 `LocalFastTokenizer`
- Subclasses [`TokenizerInterface`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/common_serializer.py#L69-L86).
- Supports dependency injection (`custom_tokenizer`, `custom_renderer`) for synthetic test isolation.
- Enforces multi-artifact verification prior to engine instantiation.
- `count_tokens(text)`: encodes text via `Tokenizer.encode(text, add_special_tokens=False)` and counts IDs without double-counting special tokens.
- **Zero Mock Fallback:** Never falls back to `MockBpeTokenizer` in authentic mode.

---

## 3. Synthetic Test Suite Evidence (`Suite A`)

The test suite in [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) executes 11 isolated test cases:

```
test_parse_manifest_success                                      ... ok
test_parse_manifest_malformed_fails_closed                       ... ok
test_verify_role_artifacts_success                               ... ok
test_verify_role_artifacts_missing_file_fails_closed              ... ok
test_verify_role_artifacts_tampered_hash_fails_closed             ... ok
test_verify_role_artifacts_extra_unmanifested_file_fails_closed   ... ok
test_verify_role_artifacts_path_traversal_fails_closed            ... ok
test_renderer_blocks_when_jinja_missing                          ... ok
test_renderer_injected_mock_env_evaluation                       ... ok
test_renderer_message_validation_rejects_unsupported             ... ok
test_local_fast_tokenizer_with_injected_components               ... ok
----------------------------------------------------------------------
Ran 11 tests in 0.105s (OK)
```

### Full Named Synthetic Regression Run:
Command:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest `
    tests/test_offline_adapters_synthetic.py `
    tests/test_offline_preflight_synthetic.py `
    tests/test_matched_baseline_synthetic.py `
    tests/test_fast_tokenizer_adapter_synthetic.py
```
Output:
```
----------------------------------------------------------------------
Ran 130 tests in 3.998s

OK
```
Zero test regressions. All 130 synthetic unit tests pass with exit code 0.

---

## 4. Strengthened Package Installation Specification (Codex-0105 Adopted)

Pursuant to Codex-0105, we have updated the installation plan to enforce wheel hashes and disallow source distribution fallbacks:

1. **Factual Dry-Run Record:** In the previous planning turn, `pip install --dry-run Jinja2` was executed to inspect dependency resolution. Pip cached wheel metadata in its local cache; zero wheels were installed into the project venv.
2. **Local Wheelhouse Staging (`assets/wheelhouse/`):**
   Prior to installation, the two exact binary wheels will be fetched to an isolated directory:
   - `jinja2-3.1.6-py3-none-any.whl` (SHA-256: `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67`)
   - `markupsafe-3.0.4-cp314-cp314-win_amd64.whl` (SHA-256: `c1bc67752d5f21013cfe430df4062441714eab79f65a6a05e01505957e9c35fe`)
3. **Hardened Installation Command (Awaiting User Gate Authorization):**
   ```powershell
   & "F:\TERRA -Copy\venv\Scripts\python.exe" -m pip install `
       --no-index `
       --find-links assets/wheelhouse `
       --only-binary=:all: `
       --no-deps `
       --require-hashes `
       -r assets/wheelhouse/requirements.txt
   ```
   This guarantees:
   - Zero network access during pip install (`--no-index`).
   - Zero compilation or source distribution fallback (`--only-binary=:all:`).
   - Zero unreviewed transitive packages (`--no-deps`).
   - Mandatory hash verification (`--require-hashes`).

---

## 5. Current State & Peer Action Requested

- **State:** `MATCHED_BASELINE_OFFLINE_PREFLIGHT_STAGE3A_COMPLETE_AWAITING_AUDIT`
- **Synthetic Unit Baseline:** 130/130 tests pass (exit 0).
- **Staged Tokenizers:** Untouched in `assets/tokenizers/`.
- **Request to Codex:**
  1. Audit the delivered Stage 3A source code in [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py).
  2. Audit the 100% synthetic unit test suite in [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py).
  3. Formulate audit disposition for subsequent user gating of the wheel installation and Stage 3B authentic public asset validation.
