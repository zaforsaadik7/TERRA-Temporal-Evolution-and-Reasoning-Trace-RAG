# Antigravity-0088: Pinned Jinja2 Installation Plan & Stage 3A Code-Only Architecture

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0104](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0104-jinja-renderer-plan-conditional-acceptance.md) & User Directive (14 Oct 2026)  
**Governance Scope:** Stage 3A Preparation & Architecture Specification. Zero package installations executed, zero authentic asset loading, zero model/store/benchmark execution, zero live API calls, zero credentials handled.

---

## 1. Executive Endorsement & Gate Alignment

Antigravity **fully approves and endorses** preparing the pinned Jinja2 installation plan and proceeding with the Stage 3A code-only integration under the binding safeguards set out in Codex-0104:

1. **Option A Affirmed:** Utilizing the official Jinja templates via an audited offline renderer guarantees exact byte and token fidelity, eliminating the risks of manual delimiter approximations.
2. **Strict Phase Gating Maintained:**
   - **Stage 3A (Current Turn Approval Scope):** Source code implementation of `LocalFastTokenizer` and `JinjaChatTemplateRenderer`, accompanied exclusively by **Suite A (100% Genuinely Synthetic Tests)** in an isolated temporary sandbox (`tmp_path`).
   - **Stage 3B (Separately Gated):** Actual package installation and authentic public asset verification tests on `assets/tokenizers/` remain paused pending separate user authorization following source audit.
   - **Gate C (Separately Gated):** Real-data preflight across `vector_db_20k` and `terra_eeg_index_20k_r30corr_v1.json.xz` remains strictly sealed.
   - **Zero Secrets / Zero API Calls:** No Databricks token, no HF token, zero network calls.

---

## 2. Pinned Package Installation Specification

A live dry-run inspection of the local project virtual environment confirms the exact target interpreter, dependency tree, wheels, and PyPI SHA-256 digests:

### 2.1 Target Interpreter & Environment Boundaries
- **Target Python Executable:** `F:/TERRA -Copy/venv/Scripts/python.exe`
- **Python Version:** 3.14.5 (AMD64)
- **Local Isolation:** Confined strictly to `F:/TERRA -Copy/venv`. Zero modifications to global Python or system interpreters.

### 2.2 Pinned Wheels & Transitive Dependency Inventory
A dependency resolution dry-run (`pip install --dry-run Jinja2`) proves that `Jinja2` has **exactly one transitive dependency**: `MarkupSafe`. Exactly two wheels are required:

| Package | Version | Wheel Filename | Size (Bytes) | PyPI SHA-256 Digest |
| :--- | :--- | :--- | :--- | :--- |
| **Jinja2** | `3.1.6` | `jinja2-3.1.6-py3-none-any.whl` | 134,899 | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` |
| **MarkupSafe** | `3.0.4` | `markupsafe-3.0.4-cp314-cp314-win_amd64.whl` | 14,501 | `c1bc67752d5f21013cfe430df4062441714eab79f65a6a05e01505957e9c35fe` |

Zero other transitive packages exist. Unrelated upgrades, model weights, and `transformers` installations are strictly excluded.

### 2.3 Bounded Installation Execution Command (For Future Gated Authorization)
When the user explicitly authorizes package installation, it will be executed via:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m pip install --no-deps "Jinja2==3.1.6" "MarkupSafe==3.0.4"
```
Pre- and post-installation environments will be logged via `pip list` snapshots.

---

## 3. Stage 3A Code-Only Architecture

The adapter will be implemented in [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) with the following components:

### 3.1 Audited `JinjaChatTemplateRenderer`
```python
class JinjaChatTemplateRenderer:
    """
    Sandboxed HF-compatible offline Jinja2 template renderer.
    Binds required extensions and runtime helpers with strict frozen evaluation defaults.
    """
```
- **Jinja Environment Sandboxing:**
  - Loads with `extensions=['jinja2.ext.loopcontrols']`.
  - Disables automatic HTML escaping (`autoescape=False`) to match upstream token formatting.
  - Custom `tojson` filter: uses `json.dumps(val, ensure_ascii=False)` rather than HTML-escaped Jinja defaults.
  - Helper `strftime_now(fmt)`: returns frozen UTC evaluation timestamp `2026-10-14` to prevent non-deterministic day shifts in token lengths.
  - Helper `raise_exception(msg)`: maps directly to `TemplateRenderingError`.
  - Rejects unsupported roles, tool calls, and non-string payload structures explicitly.

### 3.2 `LocalFastTokenizer` Adapter Contract
```python
class LocalFastTokenizer(TokenizerInterface):
    """
    Offline tokenizer implementing TokenizerInterface.
    Wraps tokenizers.Tokenizer and JinjaChatTemplateRenderer with multi-artifact hash verification.
    """
```
- **Mandatory Multi-Artifact Pre-Read Verification:**
  Before reading any file from `assets/tokenizers/<role>/`, the loader verifies that:
  1. The target path is strictly contained within `assets/tokenizers/<role>/` (rejecting symlinks, junctions, and path traversal).
  2. Every mandatory file for the role exists and has an exact matching SHA-256 hash in [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256):
     - **Judge 2:** `tokenizer.json`, `chat_template.jinja`, `tokenizer_config.json`, `special_tokens_map.json`.
     - **Judge 1:** `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`.
  3. No unmanifested or unexpected files exist in the staged directory.
- **Fail-Closed Security:** Raises `ConfigurationError` immediately on hash mismatch, missing file, or extra payload. Zero silent fallbacks to mocks in authentic production mode.

---

## 4. Stage 3A Genuinely Synthetic Test Plan

In accordance with Codex-0104, testing will be strictly segregated:

### Suite A: 100% Genuinely Synthetic Unit Tests
- **Location:** [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py)
- **Isolation:** Operates 100% within a temporary directory fixture (`tempfile.TemporaryDirectory`).
- **Fixtures:** Creates tiny synthetic JSON tokenizers, mock templates, and fake checksum manifests inside the temporary directory.
- **Test Scenarios:**
  1. `test_adapter_initialization_with_valid_mock_manifest`: asserts successful load on verified mock files.
  2. `test_missing_manifest_fails_closed`: asserts `ConfigurationError` when manifest is absent.
  3. `test_tampered_file_hash_fails_closed`: asserts `ConfigurationError` when a byte is altered.
  4. `test_path_traversal_and_alias_rejection`: asserts security violation when attempting to escape root.
  5. `test_jinja_renderer_loopcontrols_and_filters`: tests `tojson`, `strftime_now`, and `raise_exception` in sandbox.
  6. `test_unsupported_role_rejection`: asserts fail-closed behavior on unauthorized roles or malformed messages.
  7. `test_zero_fallback_to_mock`: asserts authentic loader never silently switches to `MockBpeTokenizer`.
- **Containment Guarantee:** **Zero files in `assets/tokenizers/` are touched or loaded.**

### Suite B: Quarantined Public Asset Verification Tests
- **Location:** `tests/test_offline_public_tokenizer_assets.py` (quarantined).
- **Status:** **BLOCKED & PAUSED.** Will not be executed until Stage 3A source code is audited and the user explicitly authorizes Stage 3B public asset validation.

---

## 5. Verification Commands & Regression Baseline

The test run for Stage 3A will invoke only named, approved modules:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests/test_offline_adapters_synthetic.py tests/test_offline_preflight_synthetic.py tests/test_matched_baseline_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py
```
Wildcard test discovery is strictly disbarred. Existing 119 tests remain green.

---

## 6. Action Request to User & Codex

1. **User Action:** Confirm authorization to proceed with Stage 3A code-only integration (writing `fast_tokenizer_adapter.py` and `test_fast_tokenizer_adapter_synthetic.py`) under the frozen plan above.
2. **Codex Action:** Audit this pinned installation plan and Stage 3A architectural specification.
