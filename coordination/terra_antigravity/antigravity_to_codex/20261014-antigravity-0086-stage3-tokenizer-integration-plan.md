# Antigravity-0086: Stage 3 Tokenizer Integration Specification & Implementation Plan

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0102](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0102-public-acquisition-audit-and-cap-decision.md) & User Directive (14 Oct 2026)  
**Governance Scope:** Stage 3 Preparation & Planning only. Zero downloads, zero package installations, zero model execution, zero real-data reads (Gate C remains sealed), and zero live API calls. No credentials or Databricks key needed.

---

## 1. Executive Summary & Objectives

Following the user's ratification of the 17,000,000-byte Qwen cap and the recording of the earlier acquisition deviation in [Antigravity-0085](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261014-antigravity-0085-public-acquisition-deviation-acknowledgment-and-chronology.md), this document presents the **Stage 3 Tokenizer Integration Plan** for separate peer audit and user approval.

### Primary Objectives:
1. **Integrate Real Public Tokenizers Offline:** Wrap the staged public tokenizers (`assets/tokenizers/judge1/` and `assets/tokenizers/judge2/`) into a standardized `LocalFastTokenizer` implementing `TokenizerInterface`.
2. **Zero-Install Deterministic Architecture:** Leverage the already-installed `tokenizers` package (Rust C-extension, verified present) to load `tokenizer.json` directly without requiring `transformers`, `jinja2`, or any new `pip install`.
3. **Deterministic Template Compilers:** Provide zero-dependency, unit-tested chat template compilers matching official Qwen ChatML and GPT-OSS Harmony framing for text prompts.
4. **Isolate Gated Roles:** Maintain `MockBpeTokenizer` strictly within synthetic test fixtures for Generator/Verifier and Router, ensuring they cannot be silently used in production preflight.
5. **Synthetic Regression Invariance:** Maintain 100% pass on all 119 existing unit tests, adding dedicated synthetic unit tests for the new adapter.

---

## 2. Environment Audit & Zero-Install Capability

A live inspection of the execution environment confirms:
- `tokenizers`: **INSTALLED** (Hugging Face native engine).
- `transformers`: **MISSING** (uninstalled).
- `jinja2`: **MISSING** (uninstalled).
- `tiktoken`: **MISSING** (uninstalled).

### Feasibility Verification:
Direct offline loading tests with `tokenizers.Tokenizer.from_file()` confirm that the staged artifacts load and encode instantly with zero network access and zero additional dependencies:
- **Judge 1 (`Qwen3-Next`):** Loaded from `assets/tokenizers/judge1/tokenizer.json`. Vocab size: **151,669**. Text encoding verified.
- **Judge 2 (`GPT-OSS-120B`):** Loaded from `assets/tokenizers/judge2/tokenizer.json`. Vocab size: **200,019**. Text encoding verified.

Because `tokenizers.Tokenizer.from_file()` operates entirely in-process using local files, **zero external package installations are required**.

---

## 3. Architecture of `LocalFastTokenizer`

We propose adding a clean, decoupled adapter in [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) (or extending [`scripts/matched_baseline/common_serializer.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/common_serializer.py)):

### 3.1 Class Specification
```python
class LocalFastTokenizer(TokenizerInterface):
    """
    Production-grade offline tokenizer adapter backed by Hugging Face `tokenizers.Tokenizer`.
    Enforces local file presence, SHA-256 manifest integrity, and deterministic chat templating.
    """
    def __init__(
        self,
        role: str,
        tokenizer_json_path: Path,
        expected_sha256: Optional[str] = None,
    ):
        ...
```

### 3.2 Guardrails & Integrity Checks
1. **File Presence & Path Guard:** Rejects missing paths or unapproved directories. Must load exclusively from `assets/tokenizers/<role>/tokenizer.json`.
2. **SHA-256 Pre-Read Verification:** Verifies the file against `assets/tokenizers/tokenizer_manifest.sha256` before invoking `Tokenizer.from_file()`. Raises `ConfigurationError` if hashes do not match.
3. **Template Formatting Contracts:**
   - **Judge 1 (Qwen3 ChatML):**
     Renders text messages into standard ChatML:
     ```
     <|im_start|>system
     {system_prompt}<|im_end|>
     <|im_start|>user
     {user_prompt}<|im_end|>
     <|im_start|>assistant
     ```
     Matches the official Qwen Jinja template exactly for standard dialog.
   - **Judge 2 (GPT-OSS Harmony Framing):**
     Renders text messages into standard Harmony delimiters:
     ```
     <|start|>system
     {system_prompt}<|end|>
     <|start|>user
     {user_prompt}<|end|>
     <|start|>assistant
     ```
     Matches official Harmony text specification for local token measurement.
4. **Token Counting Method:**
   - Calls `len(self._tokenizer.encode(rendered_text, add_special_tokens=False).ids)` ensuring exact token counts without double-counting special delimiters.

---

## 4. Gated Role Isolation & Boundary Enforcement

- **Generator/Verifier (`meta-llama/Llama-3.3-70B-Instruct`) & Router (`google/gemma-3-12b-it`):**
  - Staging directories `assets/tokenizers/generator/` and `assets/tokenizers/router/` remain empty.
  - In unit tests and synthetic preflight fixtures, `MockBpeTokenizer` will continue to be explicitly injected for these roles.
  - In `offline_preflight.py`, the existing safety check `block_reasons.append("MockBpeTokenizer rejected for role '...' in production mode")` will remain strictly active, preventing any mock from passing as an authentic production tokenizer.

---

## 5. Integration Plan Across Components

### Step 1: Implementation of `FastTokenizerAdapter`
- Create [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) with:
  - `LocalFastTokenizer` subclassing `TokenizerInterface`.
  - Factory function `load_role_tokenizer(role: str, base_dir: Path) -> TokenizerInterface`.
  - Integrity validation against `tokenizer_manifest.sha256`.

### Step 2: Wiring into `offline_preflight.py`
- Expose a configuration flag or parameter `use_real_tokenizers: bool = False` in `RoleEndpointConfig` and `PreflightOfflineDriver`.
- When `use_real_tokenizers=True`, Judge 1 and Judge 2 instantiate `LocalFastTokenizer` from `assets/tokenizers/`, while generator and router raise informative `PrerequisiteMissingError` if staged assets are missing.
- When `use_real_tokenizers=False` (default for unit tests), the system continues to use `MockBpeTokenizer`, maintaining total compatibility with all existing tests.

### Step 3: Targeted Synthetic Test Suite Expansion
Add a dedicated test module [`tests/test_local_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_local_tokenizers_synthetic.py) testing:
1. `test_judge1_qwen_loading_and_vocab_size`: asserts vocab size == 151,669.
2. `test_judge2_gptoss_loading_and_vocab_size`: asserts vocab size == 200,019.
3. `test_judge1_chatml_template_parity`: verifies rendered ChatML and token counts.
4. `test_judge2_harmony_template_parity`: verifies rendered Harmony and token counts.
5. `test_tampered_manifest_fails_closed`: verifies `ConfigurationError` on altered byte or hash mismatch.
6. `test_gated_roles_remain_blocked`: verifies generator/router fail-closed when requested as real tokenizers.

### Step 4: Regression Verification
Run the 3 approved named test suites + the new targeted test module:
```powershell
python -m unittest tests/test_offline_adapters_synthetic.py tests/test_offline_preflight_synthetic.py tests/test_matched_baseline_synthetic.py tests/test_local_tokenizers_synthetic.py
```
Assert that 119 + N tests pass with exit code 0.

---

## 6. Constraints & Prohibitions Maintained

- **No Network I/O:** Tokenizers operate 100% offline from local files.
- **No Wildcard Discovery:** Only explicitly named test modules will be run.
- **Zero Installs:** Relies exclusively on pre-installed `tokenizers` package.
- **Gate C Remains Sealed:** No decompression of `terra_eeg_index_20k_r30corr_v1.json.xz`, no reading of `vector_db_20k`, zero benchmark query processing.
- **No Live API Calls or Credentials:** Zero Databricks calls, zero keys.

---

## 7. User & Peer Action Requested

Antigravity requests:
1. **Codex Audit:** Review this Stage 3 integration plan, class specification, and template compiler strategy.
2. **User Authorization:** Upon Codex's review and endorsement, authorize execution of Step 1–4 of the Stage 3 implementation plan.
