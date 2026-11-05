# Antigravity-0091: Stage 3A Second Audit Repairs & Hardened Verification

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0107](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0107-tokenizer-second-audit-bounded-fixes.md)  
**User Authorization:** Relay directive: *"The main repairs check out, and all 134 tests pass. Two focused issues remain: The renderer must explicitly import Jinja’s sandbox module. Path checks must detect aliases before resolving them and validate the manifest’s location. Please relay Codex-0107 to Antigravity. No packages were installed or actual tokenizers executed. No Databricks key is needed yet."*

---

## 1. Executive Summary & Closure Status

In response to [Codex-0107](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0107-tokenizer-second-audit-bounded-fixes.md), bounded repairs have been applied to [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) and thoroughly tested in [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py).

Both remaining focused audit issues and all template controls are closed:

1. **Explicit Jinja Sandbox Submodule Import & Mutable Sandbox Downgrade Prohibition:**
   - The renderer constructor explicitly executes `from jinja2.sandbox import ImmutableSandboxedEnvironment` rather than relying on top-level module attributes.
   - The factory `build_sandboxed_jinja_env()` strictly requires `ImmutableSandboxedEnvironment` and raises `ConfigurationError("Mutable SandboxedEnvironment downgrade rejected; ImmutableSandboxedEnvironment required.")` if a mutable sandbox class is supplied.
   - If a top-level-only `jinja2` stub is provided without the `.sandbox` submodule, the builder cleanly raises `ConfigurationError("jinja2.sandbox module is unavailable...")` and constructor marks `_jinja_available = False`, raising `DependencyMissingError` upon render attempt.

2. **Lexical Pre-Resolution Path Inspection, Canonical Manifest Location & Fail-Closed `lstat`:**
   - `verify_role_artifacts()` inspects lexical relative path structure against `base_dir` *before* invoking `.resolve()`, completely closing directory symlink/junction alias bypasses where an unauthorized path resolves into the canonical role directory.
   - Mandated canonical manifest location: `manifest_path` must lexically match `base_dir / "assets" / "tokenizers" / "tokenizer_manifest.sha256"` and resolve identically. Arbitrary or unapproved manifest locations fail closed with `SecurityViolationError`.
   - `is_reparse_or_symlink()` fails closed on `OSError` (e.g. inaccessible or unreadable paths) by raising `SecurityViolationError`.
   - Windows platform privilege restrictions for symlink creation are caught with explicit `self.skipTest()` rather than claiming false success; injected `lstat` fixtures independently verify reparse point detection and fail-closed error handling.

3. **Template Controls & Parameter Restriction:**
   - Caller-overridable defaults (`model_identity`, `reasoning_effort`) are forwarded while strictly rejecting unknown kwargs or `tools` schema with `ValueError`.
   - Message dictionaries are strictly validated against `ALLOWED_MESSAGE_FIELDS = {"role", "content"}`. Extra fields or prohibited `tool_calls` fail closed.

---

## 2. Itemized Audit Responses & Code Changes

### Audit Item 1: Explicit Sandbox Submodule Import & Disallowing Mutable Downgrades
- **Constructor Import:**
  ```python
  try:
      import jinja2
      import jinja2.sandbox
      from jinja2.sandbox import ImmutableSandboxedEnvironment
      self._jinja_available = True
      sandbox_cls = injected_sandbox_class or ImmutableSandboxedEnvironment
      env = self.build_sandboxed_jinja_env(
          jinja2_module=jinja2,
          sandbox_class=sandbox_cls,
          frozen_date=self.frozen_date,
      )
      if raw_template:
          self._template = env.from_string(raw_template)
  except (ImportError, AttributeError):
      if injected_sandbox_class is not None:
          self._jinja_available = True
          env = self.build_sandboxed_jinja_env(
              jinja2_module=None,
              sandbox_class=injected_sandbox_class,
              frozen_date=self.frozen_date,
          )
          if raw_template:
              self._template = env.from_string(raw_template)
      else:
          self._jinja_available = False
          self._template = None
  ```
- **Builder Mutable Rejection:**
  ```python
  cls_name = getattr(EnvClass, "__name__", "")
  if cls_name == "SandboxedEnvironment":
      raise ConfigurationError(
          "Mutable SandboxedEnvironment downgrade rejected; ImmutableSandboxedEnvironment required."
      )
  ```
- **Synthetic Unit Tests Added:**
  - `test_sandboxed_jinja_builder_top_level_only_module_fails_closed`: Verifies `ConfigurationError('jinja2.sandbox module is unavailable')` when passed a top-level-only stub.
  - `test_sandboxed_jinja_builder_mutable_downgrade_rejected`: Verifies `ConfigurationError` when mutable `SandboxedEnvironment` is supplied.
  - `test_renderer_constructor_top_level_only_jinja_submodule_missing_fails_closed`: Simulates `jinja2` without `jinja2.sandbox` in `sys.modules`, verifying constructor marks `is_available = False` and `render()` raises `DependencyMissingError`.
  - `test_renderer_constructor_injected_sandbox_class_success`: Verifies clean initialization and rendering with injected `ImmutableSandboxedEnvironment`.

### Audit Item 2: Pre-Resolution Lexical Path Checks, Canonical Manifest & Fail-Closed `lstat`
- **Lexical Structure Pre-Check:**
  ```python
  # 1. Existence Check
  if not role_dir.exists() or not role_dir.is_dir():
      raise ConfigurationError(f"Role directory does not exist or is not a directory: {role_dir}")
  if not manifest_path.exists() or not manifest_path.is_file():
      raise ConfigurationError(f"Mandatory checksum manifest not found: {manifest_path}")

  # 2. Lexical Path Containment & Structure Check BEFORE Resolution
  try:
      lexical_role_rel = role_dir.relative_to(base_dir).as_posix()
  except ValueError:
      raise SecurityViolationError(f"Role directory '{role_dir}' is not lexically contained in base '{base_dir}'")

  expected_role_rel = f"assets/tokenizers/{role}"
  if lexical_role_rel != expected_role_rel:
      raise SecurityViolationError(
          f"Role directory '{role_dir}' does not match canonical path '{base_dir / expected_role_rel}'"
      )

  # 3. Validate Canonical Manifest Path Location BEFORE Resolution
  try:
      lexical_manifest_rel = manifest_path.relative_to(base_dir).as_posix()
  except ValueError:
      raise SecurityViolationError(f"Manifest path '{manifest_path}' is not lexically contained in base '{base_dir}'")

  expected_manifest_rel = "assets/tokenizers/tokenizer_manifest.sha256"
  if lexical_manifest_rel != expected_manifest_rel:
      raise SecurityViolationError(
          f"Manifest path '{manifest_path}' does not match canonical path '{base_dir / expected_manifest_rel}'"
      )
  ```
- **Fail-Closed `lstat` Handling:**
  ```python
  def is_reparse_or_symlink(path: Path) -> bool:
      if path.is_symlink():
          return True
      try:
          st = os.lstat(str(path))
          if hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT") and hasattr(st, "st_file_attributes"):
              if st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                  return True
      except OSError as exc:
          raise SecurityViolationError(f"Failed to lstat path {path}: {exc}") from exc
      return False
  ```
- **Synthetic Unit Tests Added:**
  - `test_verify_role_artifacts_altered_manifest_location_fails_closed`: Verifies `SecurityViolationError` when `manifest_path` is relocated.
  - `test_verify_role_artifacts_lexical_alias_before_resolve_fails_closed`: Verifies unapproved alias directory is rejected lexically before `resolve()`.
  - `test_verify_role_artifacts_symlink_alias_skipped_if_no_privileges`: Safely creates symlink or skips via `self.skipTest()` if Windows user lacks privilege.
  - `test_is_reparse_or_symlink_injected_lstat_reparse_point`: Mocks `os.lstat` returning `stat.FILE_ATTRIBUTE_REPARSE_POINT` -> returns `True`.
  - `test_is_reparse_or_symlink_injected_lstat_oserror_fails_closed`: Mocks `os.lstat` raising `PermissionError` -> raises `SecurityViolationError`.
  - `test_verify_role_artifacts_inaccessible_path_lstat_fails_closed`: Mocks inaccessible path during hierarchy check -> raises `SecurityViolationError`.

### Audit Item 3: Template Overrides & Message Field Controls
- **Renderer Parameter Validation:**
  ```python
  unknown_kwargs = set(kwargs.keys()) - ALLOWED_OVERRIDE_KWARGS
  if unknown_kwargs:
      raise ValueError(
          f"Cannot override protected template arguments or unapproved parameter(s): {unknown_kwargs}. "
          f"Only {ALLOWED_OVERRIDE_KWARGS} are permitted."
      )
  ```
- **Message Field Validation:**
  ```python
  extra_fields = set(msg.keys()) - ALLOWED_MESSAGE_FIELDS
  if extra_fields:
      if "tool_calls" in extra_fields:
          raise ValueError(
              f"Message at index {idx} contains 'tool_calls', which are prohibited. "
              f"Only {ALLOWED_MESSAGE_FIELDS} are permitted."
          )
      raise ValueError(
          f"Message at index {idx} contains prohibited extra fields: {extra_fields}. "
          f"Only {ALLOWED_MESSAGE_FIELDS} are permitted."
      )
  ```
- **Synthetic Unit Tests Added:**
  - `test_renderer_allowed_overrides_and_disallowed_parameters`: Verifies `model_identity` and `reasoning_effort` pass, while `builtin_tools` and `tools` schema fail.
  - `test_renderer_message_fields_strict_validation`: Verifies extra fields like `name` or metadata are rejected.

---

## 3. Delivered Source Artifacts & Checksums

| File Path | Byte Count | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,719 bytes | `1b6cfaf961acacd6314eb8c1da812e0a6944c3bf031703bd89b1046f15e74f19` |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,066 bytes | `d2af44a62fcc48caec2595fcf850e5ce87fab03ee1c4dac2f107d64d0222c396` |

---

## 4. Synthetic Verification Evidence

### 4.1 Focused Adapter Suite (Suite A — 27 Tests)
Executed in `F:\TERRA -Copy\venv\Scripts\python.exe`:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests/test_fast_tokenizer_adapter_synthetic.py
```
Output:
```
........................s..
----------------------------------------------------------------------
Ran 27 tests in 0.149s

OK (skipped=1)
```
*(Note: 1 test gracefully skipped on Windows environment due to unprivileged un-elevated `os.symlink` creation, while injected `lstat` unit tests verified reparse point and fail-closed `lstat` execution).*

### 4.2 Full Named Synthetic Regression Run (146 Tests)
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
Ran 146 tests in 4.014s

OK (skipped=1)
```
**Exit Code:** 0.

---

## 5. Scope & Boundary Confirmations

1. **Zero Package Installations:** No packages or wheels installed. The pinned 2-wheel installation (`Jinja2` and `MarkupSafe`) remains separately gated.
2. **Zero Authentic Tokenizer Runs:** Authentic tokenizer files under `assets/tokenizers/` remain completely untouched and unexecuted.
3. **Gate C Sealed:** Real-data baseline preflight remains strictly sealed.
4. **Zero Model Execution / APIs / Credentials:** No live models run, no network calls made, and no Databricks API keys requested or needed.

Awaiting Codex's verification of the updated source and test hashes before proposing the separate wheel acquisition/installation step.
