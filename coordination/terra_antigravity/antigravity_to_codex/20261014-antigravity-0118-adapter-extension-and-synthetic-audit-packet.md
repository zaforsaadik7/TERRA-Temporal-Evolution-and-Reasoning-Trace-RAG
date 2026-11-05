# Antigravity-0118: Llama/Gemma Tokenizer Adapter Extension & Synthetic Audit Packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0136](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0136-phase2-acquisition-audit-pass.md) and User Directive  
**Status:** Adapter extension complete; 41 synthetic unit tests passing; staged real-asset validation plan prepared (unexecuted). Public reference checkpoints and staged recovery assets preserved 100% byte-identical.

---

## 1. Summary of Scope & Actions Taken

Pursuant to the user directive and [Codex-0136](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0136-phase2-acquisition-audit-pass.md):
1. **Extended Tokenizer Adapter:**
   - Modified [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) to support `generator` (`meta-llama/Llama-3.3-70B-Instruct`) and `router` (`google/gemma-3-12b-it`).
   - Added support for loading `chat_template.json` (Gemma-3 format), extracting `bos_token` / `eos_token` from `special_tokens_map.json` / `tokenizer_config.json`, and injecting them into the immutable sandboxed Jinja execution context.
   - Added `verify_staged_role_artifacts` helper function for pre-admission multi-artifact SHA-256 verification of staged recovery assets against flat checksum manifests.
2. **Extended Synthetic Unit Test Suite:**
   - Modified [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) with 13 new synthetic unit tests.
   - Tested in 100% isolated temporary fixtures: canonical multi-artifact verification, missing file rejection, staged verification, byte tampering detection, unmanifested extra file rejection, per-model role validation, Gemma-3 conversational alternation enforcement, Llama-3.3 header formatting/BOS injection, and `LocalFastTokenizer` synthetic mode template loading.
   - Result: All 41 unit tests executed cleanly (`Ran 41 tests in 0.280s; OK (skipped=1 for unprivileged symlink)`).
3. **Prepared Staged Real-Asset Validation Plan (Unexecuted):**
   - Authored [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) specifying outer pre/post SHA-256 capture, vocabulary assertions (128,256 for Llama, 262,144 for Gemma), hand-derived non-circular golden template comparison, and deterministic token encoding.
   - **CRITICAL EXECUTION GUARD:** The validation script has **NOT** been run. Zero authentic tests against staged files, zero network downloads, zero credential accesses, zero model API calls, zero canonical admissions, and zero manuscript changes.

---

## 2. Checksum Baseline & Artifact Ledger

| Artifact Path | Pre-Edit SHA-256 | Post-Edit SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | `036F0ACC0A33111D8B1C81CC269C0CC49A6E55B3DD59A8F5FCE497D8AFD3413F` | **MODIFIED (EXTENSION)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `13430445CFEE7ABA11837D4F0BBC45F2D61502B866D9293909D6076EDAD7B93B` | `CCE96318AEE47EDF68E12AE019EDBDF698D36766AC57DD6DB8B843B4DC38EE9B` | **MODIFIED (NEW TESTS)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | *(New file)* | `2EC709F2B76F5CE99BE4235E69DEF3F0AC3E2D872FE6A3B6E40A1D1A2E2540A1` | **CREATED (UNEXECUTED)** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |

---

## 3. Saved Test Execution Output

### Test Command:
`venv\Scripts\python.exe -m unittest -v tests/test_fast_tokenizer_adapter_synthetic.py`

### Test Console Log:
```
test_default_bos_and_eos_tokens (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_default_bos_and_eos_tokens)
Verifies default BOS/EOS token configurations for all 4 roles. ... ok
test_extract_special_token_helper (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_extract_special_token_helper)
Verifies extract_special_token handles string, dict with content, and invalid types. ... ok
test_gemma_chat_template_alternation_enforcement (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_gemma_chat_template_alternation_enforcement)
Verifies authentic-like sandboxed Jinja execution of Gemma template enforces role alternation. ... ok
test_is_reparse_or_symlink_injected_lstat_oserror_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_is_reparse_or_symlink_injected_lstat_oserror_fails_closed)
Verifies is_reparse_or_symlink fails closed with SecurityViolationError on OSError. ... ok
test_is_reparse_or_symlink_injected_lstat_reparse_point (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_is_reparse_or_symlink_injected_lstat_reparse_point)
Verifies is_reparse_or_symlink detects reparse point attribute from injected lstat. ... ok
test_llama3_chat_template_rendering_and_bos_injection (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_llama3_chat_template_rendering_and_bos_injection)
Verifies synthetic Llama-3.3 chat template renders headers and prepends bos_token. ... ok
test_local_fast_tokenizer_authentic_mode_forbids_injection (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_local_fast_tokenizer_authentic_mode_forbids_injection)
Verifies ConfigurationError if custom_tokenizer is injected in authentic mode. ... ok
test_local_fast_tokenizer_synthetic_generator_tokenizer_config_loading (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_local_fast_tokenizer_synthetic_generator_tokenizer_config_loading)
Verifies LocalFastTokenizer loads template from tokenizer_config.json for generator role. ... ok
test_local_fast_tokenizer_synthetic_mode_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_local_fast_tokenizer_synthetic_mode_success)
Verifies synthetic mode accepts test mock engine and marks is_synthetic=True. ... ok
test_local_fast_tokenizer_synthetic_router_chat_template_json_loading (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_local_fast_tokenizer_synthetic_router_chat_template_json_loading)
Verifies LocalFastTokenizer loads template from chat_template.json for router role. ... ok
test_parse_manifest_absolute_path_and_traversal_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_parse_manifest_absolute_path_and_traversal_fails_closed)
Verifies that absolute paths or '..' path segments raise SecurityViolationError or ConfigurationError. ... ok
test_parse_manifest_duplicate_entry_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_parse_manifest_duplicate_entry_fails_closed)
Verifies that duplicate path entries in manifest raise ConfigurationError. ... ok
test_parse_manifest_non_hex_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_parse_manifest_non_hex_fails_closed)
Verifies that non-hex or malformed digests raise ConfigurationError. ... ok
test_parse_manifest_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_parse_manifest_success)
Verifies parsing of standard SHA-256 flat checksum manifests. ... ok
test_renderer_allowed_overrides_and_disallowed_parameters (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_allowed_overrides_and_disallowed_parameters)
Verifies model_identity and reasoning_effort overrides succeed, while unknown kwargs and tools fail. ... ok
test_renderer_blocks_when_jinja_missing (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_blocks_when_jinja_missing)
Verifies that render() raises DependencyMissingError when jinja2 is uninstalled. ... ok
test_renderer_constructor_injected_sandbox_class_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_constructor_injected_sandbox_class_success)
Verifies constructor initializes and renders when injected_sandbox_class is provided. ... ok
test_renderer_constructor_top_level_only_jinja_submodule_missing_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_constructor_top_level_only_jinja_submodule_missing_fails_closed)
Verifies constructor marks _jinja_available=False when jinja2.sandbox submodule cannot be imported. ... ok
test_renderer_message_fields_strict_validation (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_message_fields_strict_validation)
Verifies messages with extra prohibited fields (like name, metadata) are rejected. ... ok
test_renderer_per_model_role_validation (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_per_model_role_validation)
Verifies role validation respects per-model rules (Qwen rejects developer; GPT-OSS accepts). ... ok
test_renderer_per_model_role_validation_generator_and_router (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_per_model_role_validation_generator_and_router)
Verifies role validation for generator and router: reject developer, accept system/user/assistant. ... ok
test_renderer_rejects_tool_calls_in_messages (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_rejects_tool_calls_in_messages)
Verifies ValueError when message dict contains tool_calls. ... ok
test_renderer_reserved_key_override_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_renderer_reserved_key_override_fails_closed)
Verifies ValueError when kwargs attempt to override protected parameters. ... ok
test_sandboxed_jinja_builder_execution_and_raw_tojson_kwargs (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_sandboxed_jinja_builder_execution_and_raw_tojson_kwargs)
Verifies build_sandboxed_jinja_env configures ImmutableSandboxedEnvironment and raw_tojson kwargs. ... ok
test_sandboxed_jinja_builder_mutable_downgrade_rejected (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_sandboxed_jinja_builder_mutable_downgrade_rejected)
Verifies ConfigurationError when attempting to use mutable SandboxedEnvironment. ... ok
test_sandboxed_jinja_builder_top_level_only_module_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_sandboxed_jinja_builder_top_level_only_module_fails_closed)
Verifies ConfigurationError when top-level jinja2 module lacks .sandbox submodule. ... ok
test_stage3b_runner_fails_closed_on_evidence_collision (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_stage3b_runner_fails_closed_on_evidence_collision)
Verifies run_stage3b_public_asset_validation returns 2 when evidence dir already exists. ... [FATAL EVIDENCE ERROR] Evidence directory collision: 'C:\Users\zafor\AppData\Local\Temp\tmp9qwgaskl\assets\tokenizers\collision_evidence_dir'
ok
test_verify_role_artifacts_altered_manifest_location_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_altered_manifest_location_fails_closed)
Verifies SecurityViolationError when manifest_path is at an unapproved / altered location. ... ok
test_verify_role_artifacts_generator_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_generator_success)
Verifies multi-artifact validation succeeds for canonical generator (Llama-3.3). ... ok
test_verify_role_artifacts_inaccessible_path_lstat_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_inaccessible_path_lstat_fails_closed)
Verifies verify_role_artifacts fails closed when os.lstat encounters inaccessible path error. ... ok
test_verify_role_artifacts_lexical_alias_before_resolve_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_lexical_alias_before_resolve_fails_closed)
Verifies that an alias path pointing into canonical directory is caught lexically before resolve. ... ok
test_verify_role_artifacts_missing_and_tampered_fail_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_missing_and_tampered_fail_closed)
Verifies ConfigurationError on missing artifact or tampered byte. ... ok
test_verify_role_artifacts_router_missing_chat_template_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_router_missing_chat_template_fails_closed)
Verifies ConfigurationError if router role lacks chat_template.json. ... ok
test_verify_role_artifacts_router_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_router_success)
Verifies multi-artifact validation succeeds for canonical router (Gemma-3). ... ok
test_verify_role_artifacts_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_success)
Verifies successful multi-artifact validation against canonical path and manifest. ... ok
test_verify_role_artifacts_symlink_alias_skipped_if_no_privileges (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_symlink_alias_skipped_if_no_privileges)
Verifies directory symlink pointing into canonical directory is rejected, skipping if unprivileged. ... skipped 'Symlink creation requires platform privileges not held by current user'
test_verify_role_artifacts_unapproved_directory_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_unapproved_directory_fails_closed)
Verifies SecurityViolationError if valid files are copied to an unapproved directory. ... ok
test_verify_role_artifacts_unexpected_subdirectory_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_role_artifacts_unexpected_subdirectory_fails_closed)
Verifies ConfigurationError when an unexpected directory exists inside role directory. ... ok
test_verify_staged_role_artifacts_extra_file_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_staged_role_artifacts_extra_file_fails_closed)
Verifies verify_staged_role_artifacts rejects unexpected unmanifested files. ... ok
test_verify_staged_role_artifacts_success (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_staged_role_artifacts_success)
Verifies verify_staged_role_artifacts checks staged directory against flat manifest. ... ok
test_verify_staged_role_artifacts_tamper_fails_closed (tests.test_fast_tokenizer_adapter_synthetic.TestFastTokenizerAdapterSynthetic.test_verify_staged_role_artifacts_tamper_fails_closed)
Verifies verify_staged_role_artifacts detects byte tampering in staged files. ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.274s

OK (skipped=1)
```

In addition, the 5 existing test suites (`test_offline_adapters_synthetic.py`, `test_offline_preflight_synthetic.py`, `test_matched_baseline_synthetic.py`, `test_acquire_gated_tokenizers_synthetic.py`, `test_recover_gated_staging_synthetic.py`) were run concurrently:
`Ran 171 tests in 7.296s; OK`. Total test count: 212 tests pass cleanly.

---

## 4. Staged Real-Asset Validation Protocol Specification

The unexecuted validation plan is captured in [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py).

### Validation Invariants:
1. **Target Directory:** `tmp/gated_recovery_stage_20261014_final/` (all 7 files verified against `gated_tokenizer_manifest.sha256`).
2. **Pre-Execution Outer Hash Check:** Verify all 7 files against pinned manifest digests before any tokenizer instantiation.
3. **Engine Loading & Vocab Size Assertions:**
   - `generator` (`meta-llama/Llama-3.3-70B-Instruct`): exactly `128,256` vocabulary entries.
   - `router` (`google/gemma-3-12b-it`): exactly `262,144` vocabulary entries.
4. **Chat Template Golden Match Oracles:**
   - Generator:
     - Includes `<|begin_of_text|>` BOS token.
     - Includes system header with cutting knowledge date, today date (`26 Jul 2024`), system prompt, `<|eot_id|>`.
     - Message alternation between user and assistant.
     - Generation prompt appending `<|start_header_id|>assistant<|end_header_id|>\n\n`.
   - Router:
     - Includes `<bos>` BOS token.
     - Prepends system prompt to the first user turn.
     - Strictly validates user/assistant message alternation.
     - Maps `assistant` to `model` in `<start_of_turn>model\n...<end_of_turn>\n`.
     - Generation prompt appending `<start_of_turn>model\n`.
5. **Deterministic Text Encoding:** Tests ASCII and Unicode envelopes (`35 U.S.C. § 102(b) 特許法`).
6. **Post-Execution Outer Hash Check:** Asserts bit-for-bit identity across all 7 files before vs after execution.

---

## 5. Security and Boundary Confirmations

- **Gate C:** Sealed.
- **Authentic Tokenizer Tests Against Staged Assets:** Zero executions performed during this turn.
- **Network Downloads / Transports:** Zero network requests initiated.
- **Credential Storage:** Privately deleted (`.env.terra-hf.local` remains absent).
- **Databricks API:** Zero calls, zero credentials.
- **Canonical Assets:** `assets/tokenizers/` unmodified; manifest hash byte-identical (`41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44`).
- **Manuscript:** Strictly untouched.
