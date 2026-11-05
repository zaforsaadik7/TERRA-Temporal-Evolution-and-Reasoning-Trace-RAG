# Antigravity-0125: Reconciled No-Tools Chat Template Context & Diff Evidence Audit Packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0144](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0144-staged-template-validation-stop.md)  
**Status:** Narrow no-tools context reconciled across all four role templates; `tools: None` passed to prevent unintended activation of `is not none` branches; bounded rendered/golden difference evidence capture added to Step 4; 15 dedicated lifecycle synthetic tests passed; 50 adapter tests passed (49 passed, 1 skipped); 65 combined module tests passed (64 passed, 1 skipped). Both stopped runs remain 100% intact. Staged real-asset validation script remains strictly **UNEXECUTED** pending renewed user authorization.

---

## 1. No-Tools Context Analysis Across All Four Role Templates

Static analysis of the chat templates across all four baseline roles confirms:

| Role | Model | Tool Condition in Template | Behavior with `tools: []` | Behavior with `tools: None` | Regression Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`generator`** | `meta-llama/Llama-3.3-70B-Instruct` | `{%- if builtin_tools is defined or tools is not none %}` and `{%- if tools_in_user_message and not tools is none %}` | **MISMATCH:** `[] is not none` is `True`; injects `Environment: ipython` and custom tool guidance into prompt. | **PASS:** `None is not none` is `False`; correctly formats standard conversational prompt matching golden oracle. | None. Fixes false-positive tool activation. |
| **`judge1`** | `Qwen/Qwen2.5-72B-Instruct` | `{%- if tools %}` | `[]` is falsy; no tools rendered. | `None` is falsy; no tools rendered. | **Zero regression.** Output is bit-identical. |
| **`judge2`** | `openai/gpt-oss-12b` | `{%- if tools %}` and `{%- if developer_message or tools %}` | `[]` is falsy; no tools rendered. | `None` is falsy; no tools rendered. | **Zero regression.** Output is bit-identical. |
| **`router`** | `google/gemma-3-12b-it` | No tool references in template | No effect. | No effect. | **Zero regression.** Output is bit-identical. |

**Conclusion:** Passing `"tools": None` in `context` correctly deactivates tool-mode instructions for Llama 3.3 while preserving identical non-tool behavior for Qwen 2.5, GPT-OSS, and Gemma 3.

---

## 2. Implemented Source Modifications

1. **Adapter Context Fix (`scripts/matched_baseline/fast_tokenizer_adapter.py`):**
   - Changed `"tools": []` to `"tools": None` in `JinjaChatTemplateRenderer.render`.
2. **Diagnostic Bounded Diff Evidence (`scripts/matched_baseline/validate_staged_gated_tokenizers.py`):**
   - Implemented helper `_check_rendered(role_name, rendered, golden, with_gen)` in Step 4.
   - If a template mismatch occurs on any future run, it automatically captures:
     - `role` and `with_generation_prompt` flag.
     - `rendered_len` and `golden_len`.
     - `first_diff_index` (first differing character position).
     - `rendered_context` and `golden_context` (bounded 60-character snippet around first diff).
   - This evidence is recorded in `report["template_diff_evidence"]` and written to `validation.log` and `validation_report.json` before failing closed.
3. **Synthetic Tests:**
   - In [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py):
     - Added `test_renderer_no_tools_context_does_not_activate_is_not_none_or_truthiness_branches`: validates that a template containing both `is not none` and truthiness branches outputs neither when `tools=None`.
   - In [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py):
     - Added `test_template_mismatch_captures_bounded_diff_evidence`: validates that simulated template mismatch records bounded diff evidence in memory and on disk while exiting with code 1 and `NOT_CERTIFIED`.

---

## 3. Checksum Baseline & Artifact Ledger

| Artifact Path | Previous Hash (Codex-0144 Audited) | Repaired Hash (Antigravity-0125) | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | `bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5` | `48CCC37AE8B82AC990005B47D580427EA7262309D211E2A4C099E5EE85FD27CA` | **REPAIRED (`tools: None`)** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | `b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc` | `6B2EB3199BB67235061187A80D69A01FB33520289301231A42757139C1C7F6EC` | **REPAIRED (50 TESTS)** |
| [`scripts/matched_baseline/validate_staged_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/validate_staged_gated_tokenizers.py) | `a4f71f7de5933ad9780014cd4c01e96658390bc06105f965372d7e8ce80cc0a5` | `3915A075EB7658DFE598ED71A775F4E48A52E71510C133A4F919C125AD6E1ECE` | **REPAIRED (DIFF EVIDENCE)** |
| [`tests/test_validate_staged_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_validate_staged_gated_tokenizers_synthetic.py) | `f6684a4d881945f2f6d00547b812de7e58aed2b5b02700474a4dbbbac8389219` | `8AB06A93600FDF5E8C92715FA60A1E5B6D437972DD7870560296A830CBD4F491` | **REPAIRED (15 TESTS)** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **100% UNCHANGED** |
| [`tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256) | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | `D8C29DECBDFC869519E94789C8B49EFB14CD172C7D36DE5713EB8FAC43DBABE6` | **100% UNCHANGED** |
| `reports/gated_validation_evidence_20261014_045527_99442807/validation_report.json` | `454eaa1f7a9745e344477a9c4d9968d8af42038969bf734c661b991b88f87f23` | `454EAA1F7A9745E344477A9C4D9968D8AF42038969BF734C661B991B88F87F23` | **PRESERVED INTACT (RUN 1)** |
| `reports/gated_validation_evidence_20261014_045527_99442807/validation.log` | `5240ae57cff24fbe547e27c0f9442da2c1201dfade577220b1150aa76330aaa8` | `5240AE57CFF24FBE547E27C0F9442DA2C1201DFADE577220B1150AA76330AAA8` | **PRESERVED INTACT (RUN 1)** |
| `reports/gated_validation_evidence_20261014_050236_25103c20/validation_report.json` | `751283f67e847b072a8ecb6b272df2b87435d37e699ce401a3ef0f4820aa527d` | `751283F67E847B072A8ECB6B272DF2B87435D37E699CE401A3EF0F4820AA527D` | **PRESERVED INTACT (RUN 2)** |
| `reports/gated_validation_evidence_20261014_050236_25103c20/validation.log` | `d42f539916aa599ff53ea2f3ccc8527c5387a158ee05a499147d0022d9e32a50` | `D42F539916AA599FF53EA2F3CCC8527C5387A158EE05A499147D0022D9E32A50` | **PRESERVED INTACT (RUN 2)** |

---

## 4. Named Test Suite Logs

### A. Lifecycle Synthetic Suite (15 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py`
```
Ran 15 tests in 0.301s
OK
```
*(15 passed, 0 failures)*

### B. Adapter Synthetic Suite (50 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 50 tests in 0.341s
OK (skipped=1)
```
*(49 passed, 0 failures, 1 skipped for unprivileged directory symlink creation)*

### C. Combined Two-Module Synthetic Suite (65 Tests):
**Command:** `venv\Scripts\python.exe -B -m unittest -v tests/test_validate_staged_gated_tokenizers_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py`
```
Ran 65 tests in 0.679s
OK (skipped=1)
```
*(64 passed, 0 failures, 1 skipped for unprivileged directory symlink creation)*

---

## 5. Source Diffs

### A. `scripts/matched_baseline/fast_tokenizer_adapter.py`
```diff
--- a/scripts/matched_baseline/fast_tokenizer_adapter.py
+++ b/scripts/matched_baseline/fast_tokenizer_adapter.py
@@ -744,7 +744,7 @@ class JinjaChatTemplateRenderer:
         context = {
             "messages": messages,
             "add_generation_prompt": add_generation_prompt,
-            "tools": [],
+            "tools": None,
             "model_identity": kwargs.get("model_identity", FROZEN_MODEL_IDENTITY),
             "reasoning_effort": kwargs.get("reasoning_effort", FROZEN_REASONING_EFFORT),
             "date_string": self.date_string,
```

### B. `scripts/matched_baseline/validate_staged_gated_tokenizers.py`
```diff
--- a/scripts/matched_baseline/validate_staged_gated_tokenizers.py
+++ b/scripts/matched_baseline/validate_staged_gated_tokenizers.py
@@ -309,6 +309,24 @@ def run_staged_gated_asset_validation(
         # Step 4: Chat Template Rendering Against Hand-Derived Golden Fixtures
         log_lines.append("[4/5] Testing chat template rendering against golden oracles...")
 
+        def _check_rendered(role_name: str, rendered_text: str, golden_text: str, with_gen: bool):
+            if rendered_text != golden_text:
+                first_diff = next(
+                    (i for i, (c1, c2) in enumerate(zip(rendered_text, golden_text)) if c1 != c2),
+                    min(len(rendered_text), len(golden_text)),
+                )
+                start_idx = max(0, first_diff - 30)
+                diff_evidence = {
+                    "role": role_name,
+                    "with_generation_prompt": with_gen,
+                    "rendered_len": len(rendered_text),
+                    "golden_len": len(golden_text),
+                    "first_diff_index": first_diff,
+                    "rendered_context": repr(rendered_text[start_idx:first_diff + 30]),
+                    "golden_context": repr(golden_text[start_idx:first_diff + 30]),
+                }
+                report["template_diff_evidence"] = diff_evidence
+                log_lines.append(f"  [TEMPLATE DIFF] {diff_evidence}")
+                raise ConfigurationError(
+                    f"{role_name.capitalize()} rendered template mismatch (with_gen={with_gen}) at index {first_diff}: "
+                    f"rendered={diff_evidence['rendered_context']} vs golden={diff_evidence['golden_context']}"
+                )
+
         # Generator (Llama-3.3)
         gen_adapter = adapters["generator"]
         gen_rendered_prompt = gen_adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES, add_generation_prompt=True)
@@ -316,6 +334,4 @@ def run_staged_gated_asset_validation(
-        if gen_rendered_prompt != GOLDEN_LLAMA3_WITH_GEN_PROMPT:
-            raise ConfigurationError("Generator rendered template mismatch with generation prompt")
-        if gen_rendered_no_prompt != GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT:
-            raise ConfigurationError("Generator rendered template mismatch without generation prompt")
+        _check_rendered("generator", gen_rendered_prompt, GOLDEN_LLAMA3_WITH_GEN_PROMPT, True)
+        _check_rendered("generator", gen_rendered_no_prompt, GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT, False)
```

---

## 6. Security Boundaries & Execution State

- **Script Execution State:** Strictly **UNEXECUTED**. Blocked execution entrypoint verified (exits with code 1, prints `[BLOCKED]` message requiring `--execute-authorized-stage3c-validation`).
- **Stopped Run Evidence:** Runs `20261014_045527_99442807` and `20261014_050236_25103c20` preserved completely intact.
- **Authentic Tokenizer Runs:** ZERO authentic tokenizer executions against staged assets occurred during this turn.
- **Credentials:** ZERO credential access (`.env.terra-hf.local` remains deleted).
- **Network / Remote APIs:** ZERO network calls, zero Databricks calls, Gate C sealed.
- **Canonical Files & Checkpoint Manifests:** 100% byte-identical.
- **Manuscript Files:** Strictly untouched.
