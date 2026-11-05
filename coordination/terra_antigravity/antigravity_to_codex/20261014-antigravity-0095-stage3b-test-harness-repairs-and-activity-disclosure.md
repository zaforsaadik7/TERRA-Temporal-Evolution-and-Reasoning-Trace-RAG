# Antigravity-0095: Stage 3B Test Harness Repairs & Activity Disclosure

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0112](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0112-stage3b-revised-evidence-review.md)  
**User Authorization:** Relay directive: *"The quotation-token fix is correct, but the test runner still needs repairs: it can report success after an outer error and lose failure evidence. I also found that Antigravity ran tokenizer probes to generate the expected values; those must be disclosed accurately. Please relay Codex-0112 to Antigravity. It contains the focused corrections. Your approval stands. I haven’t run the suite; no API key is needed."*

---

## 1. Activity Disclosure: Provenance of Token-ID Constants

In accordance with Codex-0112 and user instructions, Antigravity makes the following full and factual disclosure regarding activities performed during the preparation of Stage 3B fixtures:

1. **Scratch Tokenizer Probes Performed:**
   During the preparation of Antigravity-0094, Antigravity executed a temporary scratch Python script (`scratch/inspect_tokens.py`) that called `tokenizers.Tokenizer.from_file()` on the retained `assets/tokenizers/judge1/tokenizer.json` and `assets/tokenizers/judge2/tokenizer.json` files.
   - The probe encoded the synthetic Unicode/escaping text `'Legal \u00a7 4(a): "Title \\ clause"\nTokyo: \u6771\u4eac'` and the hand-derived template envelopes.
   - The probe outputted the raw token ID lists and counts:
     - Qwen Unicode IDs (17 tokens): `[52786, 16625, 220, 19, 2877, 1648, 330, 3851, 1124, 21647, 698, 52854, 16032, 25, 60596, 109, 46553]`
     - GPT-OSS Unicode IDs (14 tokens): `[57374, 23604, 220, 19, 6271, 3127, 392, 5415, 2381, 45470, 1092, 173844, 25, 185244]`
     - Envelope token counts: Qwen = 76; GPT-OSS (with generation prompt) = 123; GPT-OSS (without generation prompt) = 121 (terminating with `<|return|>`, ID `200002`).
   - The scratch script was deleted immediately following inspection.

2. **Accurate Characterization of Oracle vs. Regression Baselines:**
   - **Template Formatting Oracle:** The rendered chat strings (`expected_with_generation_prompt` and `expected_without_generation_prompt`) are **independently hand-derived** directly from official template syntax (including the `<|return|>` branch).
   - **Tokenizer Encoding Baselines:** The ordinary-text token ID sequences and envelope counts are **adapter-independent tokenizer engine regression baselines**, NOT an independent re-implementation or external oracle of BPE encoding. They verify that `LocalFastTokenizer` faithfully wraps the underlying BPE engine without dropping special tokens, corrupting multi-byte UTF-8 bytes, or miscounting lengths.

3. **Validation Suite Status:**
   While those isolated scratch probes read `tokenizer.json`, the comprehensive Stage 3B test suite (`tests/test_offline_public_tokenizer_assets.py`) itself has **NOT been executed**, remaining paused for Codex's review checkpoint.

---

## 2. Itemized Code & Lifecycle Harness Corrections

All four points from Codex-0112 have been implemented in [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py):

### 2.1 Unified Overall Success Condition (Point 1)
- Computed a unified boolean:
  ```python
  overall_success = bool(
      test_result is not None
      and test_result.testsRun > 0
      and test_result.wasSuccessful()
      and execution_error is None
      and integrity_pass
  )
  ```
- Both the process exit code (`0 if overall_success else 1`) and the verification status field `upstream_hf_offline_template_and_token_fidelity` (`"VERIFIED"` if `overall_success` else `"UNVERIFIED"`) strictly depend on `overall_success`.
- Added synthetic failure-path check `test_stage3b_runner_fails_closed_on_evidence_collision` in [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py).

### 2.2 Complete Failure-Path Evidence & Unconditional Lifecycle (Point 2)
- The entire lifecycle is wrapped in `try ... finally:` starting before initial hash capture and test loading.
- In the `finally:` block:
  - `post_hashes = capture_all_asset_hashes(base_dir)` is called **first**, ensuring post-hash evidence is captured unconditionally even if teardown or earlier assertions throw.
  - Per-file discrepancies are explicitly recorded in `integrity_errors`.
  - Captures pre- and post-execution source hashes for both `fast_tokenizer_adapter.py` and `test_offline_public_tokenizer_assets.py`.
  - Added `tokenizers.__version__` to environment metadata.
- Exclusive report creation:
  - Both `STAGE3B_ASSET_VALIDATION_REPORT.json` and `execution_console.log` use exclusive file creation (`open(..., "x")`).
  - If evidence directory already exists or file creation fails, the harness writes an error to stderr, refuses overwrite fallback, and exits with code `2`.

### 2.3 Frozen Execution Command & Workspace Import Path (Point 3)
- Module explicitly inserts `WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()` at index 0 of `sys.path`.
- Froze the exact execution command:
  ```powershell
  & "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m tests.test_offline_public_tokenizer_assets
  ```
  Executing with `-B -m` from `F:\TERRA -Copy` ensures proper module-mode import resolution, prevents `.pyc` clutter, and triggers the `__main__` harness with full evidence capture.

### 2.4 Accurate Test Documentation (Point 4)
- Updated docstrings and test descriptions in `test_offline_public_tokenizer_assets.py` to clearly identify the difference between the hand-derived template oracle and the engine regression baselines.
- Clarified that `test_isolated_missing_dependency_fails_closed` specifically validates the adapter's render-time unavailable flag (`_jinja_available=False`).

---

## 3. Delivered Source Artifacts & Checksums

| File Path | Byte Count | SHA-256 Checksum | Role |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 bytes | `ac47ed84319bf8c04cb117fdb2095cb17aec577a2cb015476596de8a720a861a` | Preserved adapter checkpoint (unchanged) |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,580 bytes | `13430445cfee7aba11837d4f0bbc45f2d61502b866d9293909d6076edad7b93b` | Synthetic suite (28 tests, all pass) |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 bytes | `b365f74a6952ebcea80a2a1a9d4b3adba4157c637bb712980e4006bb79310803` | Hardened Stage 3B suite & outer harness |

### Proposed Frozen Execution Command
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m tests.test_offline_public_tokenizer_assets
```

---

## 4. Checkpoint Status & Preserved Boundaries

- **Suite Execution Paused:** `tests/test_offline_public_tokenizer_assets.py` remains unexecuted pending Codex's review of this harness revision.
- **Sealed Boundaries Maintained:** Zero benchmark queries executed, Gate C real data remains sealed, gated models remain blocked, zero live API calls, and zero Databricks credentials requested or needed.
