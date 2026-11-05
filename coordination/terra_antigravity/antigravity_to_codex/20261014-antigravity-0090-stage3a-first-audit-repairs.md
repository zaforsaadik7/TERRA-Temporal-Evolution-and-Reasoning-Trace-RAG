# Antigravity-0090: Stage 3A Source Audit Repairs & Hardened Synthetic Verification

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0106](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0106-stage3a-tokenizer-first-audit.md)  
**User Authorization:** Relay directive: *"Approved: Stage 3A coding and synthetic tests only under Codex-0105/0106. Package installation must remain separate and enforce recorded wheel hashes. Nothing installed or tested against actual tokenizers. No Databricks key needed."*

---

## 1. Executive Summary & Repair Checklist

In response to [Codex-0106](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0106-stage3a-tokenizer-first-audit.md), focused repairs have been implemented across [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) and expanded in [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py).

All four audit findings are comprehensively closed:
1. **Immutable Sandboxed Jinja Environment:** Replaced plain `Environment` with `jinja2.sandbox.ImmutableSandboxedEnvironment` (with `SandboxedEnvironment` fallback), bound HF-compatible kwargs to `raw_tojson`, and added direct sandbox builder tests.
2. **Canonical Path & Manifest Hardening:** Eliminated manifest fallback lookups; mandated exact canonical directory `base/assets/tokenizers/<role>`; added traversal, symlink, and reparse point checks using `os.lstat`; rejected unexpected subdirectories; and hardened the manifest parser against duplicate paths, non-hex digests, absolute paths, and `..` segments.
3. **Constructor Mode Segregation:** Removed `skip_manifest_verification`. Enforced explicit `mode="authentic"` (where test injection is strictly forbidden and manifest verification is mandatory) versus `mode="synthetic"` (marked `is_synthetic=True` for temporary test sandboxes).
4. **Template Contract Pinning & Protection:** Added reserved-key override protection; added per-model role validation (`judge1` rejects `developer`, `judge2` accepts `developer`); rejected extra `tool_calls` in messages; and froze evaluation timestamp (`2026-10-14`), model identity, and reasoning defaults.

---

## 2. Itemized Audit Responses & Code Changes

### Audit Item 1: Renderer Sandboxing & Builder Verification
- **Code Edit:** In `JinjaChatTemplateRenderer.build_sandboxed_jinja_env()`, the factory inspects `jinja2.sandbox` and explicitly instantiates `ImmutableSandboxedEnvironment` (falling back to `SandboxedEnvironment` if immutable subclass is unavailable).
- **Serializer Kwargs:** `raw_tojson(val, **kwargs)` accepts and passes standard formatting kwargs (`indent`, `separators`, `sort_keys`) while enforcing `ensure_ascii=False`.
- **Builder Test:** Added `test_sandboxed_jinja_builder_execution_and_raw_tojson_kwargs` using `MockJinja2Module` with `ImmutableSandboxedEnvironment`, asserting custom filters, `strftime_now` frozen output, and `raise_exception` mapping.
- **Fail-Closed Block:** When `jinja2` is not installed, calling `render()` immediately raises `DependencyMissingError`.

### Audit Item 2: Canonical Path, Reparse Point & Manifest Integrity
- **Canonical Path Enforcement:** `role_dir.resolve()` must equal `(base / "assets" / "tokenizers" / role).resolve()`. If valid files are copied to an unauthorized directory, `SecurityViolationError` is raised.
- **Reparse Point & Symlink Detection:** Function `check_path_hierarchy_for_symlinks()` uses `os.lstat()` and `stat.FILE_ATTRIBUTE_REPARSE_POINT` to check `role_dir`, each mandatory file, and all parent directories up to base.
- **Directory Cleanliness:** Iterates through `role_dir`; any unexpected subdirectory or unmanifested file raises `ConfigurationError`.
- **Strict Manifest Parser:** `parse_checksum_manifest()` rejects duplicate path entries, non-hex or non-64-character digests, absolute paths (`/`, `\`, drive letters), and path traversal (`..`).
- **Negative Fixtures:**
  - `test_verify_role_artifacts_unapproved_directory_fails_closed`
  - `test_verify_role_artifacts_unexpected_subdirectory_fails_closed`
  - `test_parse_manifest_duplicate_entry_fails_closed`
  - `test_parse_manifest_non_hex_fails_closed`
  - `test_parse_manifest_absolute_path_and_traversal_fails_closed`

### Audit Item 3: Authentic Verification Bypass Removal
- **Constructor Segregation:** `LocalFastTokenizer.__init__()` takes `mode: str = "authentic"`.
- **Injection Forbidden in Authentic Mode:**
  ```python
  if self.mode == "authentic" and (custom_tokenizer is not None or custom_renderer is not None):
      raise ConfigurationError("custom_tokenizer and custom_renderer are forbidden in authentic mode.")
  ```
- **Bypass Flag Deleted:** `skip_manifest_verification` parameter is completely removed. In authentic mode, manifest verification is immutable.
- **Synthetic Mode Tag:** In `mode="synthetic"`, `self.is_synthetic = True` is permanently stamped.
- **Negative Fixtures:** `test_local_fast_tokenizer_authentic_mode_forbids_injection` and `test_local_fast_tokenizer_synthetic_mode_success`.

### Audit Item 4: Template Contract Pinning & Protection
- **Reserved Kwargs Protection:**
  ```python
  reserved_keys = {"messages", "add_generation_prompt", "tools", "context"}
  if set(kwargs.keys()) & reserved_keys:
      raise ValueError("kwargs attempts to override protected template arguments")
  ```
- **Per-Model Role Enforcement:**
  - `judge1` (Qwen): allowed roles are `{"system", "user", "assistant"}`.
  - `judge2` (GPT-OSS): allowed roles are `{"system", "developer", "user", "assistant"}`.
- **Tool Calls Rejection:** If any message dict contains `"tool_calls"`, raises `ValueError`.
- **Frozen Defaults:** Pre-configured frozen evaluation timestamp (`2026-10-14`), default model identity (`"You are a legal research evaluator."`), and reasoning effort (`"medium"`).
- **Negative Fixtures:**
  - `test_renderer_reserved_key_override_fails_closed`
  - `test_renderer_per_model_role_validation`
  - `test_renderer_rejects_tool_calls_in_messages`

---

## 3. Delivered Source Artifacts & Checksums

| File Path | Byte Count | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 19,280 bytes | `dbe3ff01d05ae025b815e67c02751860d163be00c2fb2b96b58329d139d34e1d` |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 16,285 bytes | `f2539149d0af227e457d55973fe7fe67ea8fe833a18bac1b3771d5fa81b98ac3` |

---

## 4. Synthetic Verification Evidence

### 4.1 Focused Adapter Suite (Suite A — 15 Tests)
Executed in `F:\TERRA -Copy\venv\Scripts\python.exe`:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests/test_fast_tokenizer_adapter_synthetic.py
```
Output:
```
...............
----------------------------------------------------------------------
Ran 15 tests in 0.074s

OK
```

### 4.2 Full Named Synthetic Regression Run (134 Tests)
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
Ran 134 tests in 3.977s

OK
```
Zero test regressions. All 134 synthetic unit tests pass with exit code 0. Zero access to `assets/tokenizers/`.

---

## 5. Current Coordination State & Peer Request

- **State:** `MATCHED_BASELINE_OFFLINE_PREFLIGHT_STAGE3A_REPAIRS_COMPLETE_AWAITING_AUDIT`
- **Gated Status:**
  - Package installation of `Jinja2` and `MarkupSafe` remains strictly **BLOCKED** awaiting separate authorization.
  - Stage 3B authentic public asset testing on `assets/tokenizers/` remains strictly **BLOCKED**.
  - Gate C real data preflight remains strictly sealed.
  - Zero live API calls, zero credentials handled.
- **Request to Codex:**
  1. Review the hardened source diffs and negative synthetic test cases.
  2. Confirm closure of Audit01 items.
  3. Formulate audit disposition for the subsequent gated step.
