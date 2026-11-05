# Antigravity-0096: Stage 3B Evidence Review & Gated Tokenizer Readiness Proposal

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0113](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0113-stage3b-public-validation-completion.md)  
**User Directive:** Relay Codex-0113 to Antigravity for evidence review and the next-step proposal. Resolve missing Llama/Gemma tokenizer readiness; no Databricks key needed yet.  

---

## 1. Stage 3B Execution Evidence Audit & Concurrence

Antigravity has audited the execution evidence preserved by Codex from the Stage 3B validation run:

1. **Independent Verification of Execution Artifacts:**
   - **Command Executed:** `& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m tests.test_offline_public_tokenizer_assets`
   - **Exit Status:** `0` (clean success, verified in [`tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/exit_code.txt`](file:///F:/TERRA%20-Copy/tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/exit_code.txt)).
   - **Test Results:** 15 tests ran in 7.233s; 0 failures, 0 errors, 0 skips ([`tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/console.log`](file:///F:/TERRA%20-Copy/tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/console.log)).
   - **Runner Evidence Report:** [`tmp/stage3b_public_validation_20261013_232319/STAGE3B_ASSET_VALIDATION_REPORT.json`](file:///F:/TERRA%20-Copy/tmp/stage3b_public_validation_20261013_232319/STAGE3B_ASSET_VALIDATION_REPORT.json) confirms:
     - `overall_success: true`
     - `asset_integrity_verified: true` (0 integrity errors)
     - `upstream_hf_offline_template_and_token_fidelity: "VERIFIED"`
     - `gate_c_real_benchmark_data: "SEALED"`
     - `live_api_and_credentials: "PROHIBITED_AND_UNUSED"`
   - **Asset & Source Immutability:** Audit of [`hashes_before.csv`](file:///F:/TERRA%20-Copy/tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/hashes_before.csv) and [`hashes_after.csv`](file:///F:/TERRA%20-Copy/tmp/codex_stage3b_20261014_7b1c7b771e67412aba71ecf139186e7f/hashes_after.csv) confirms 100% byte-for-byte SHA-256 identity before and after execution across all 8 tokenizer assets, [`tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256), [`fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py), and [`test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py).

2. **Acknowledgment of Bounded Pass & Recorded Limitations:**
   - **Template Coverage:** We concur that Stage 3B certifies the tested evaluation prompt structures (system, developer, user, assistant turns, generation prompt toggle, and reasoning effort override), not every possible upstream chat template branch.
   - **Tokenizer Regression Baselines:** We reaffirm that ordinary text token IDs are engine-level regression baselines, while template formatting strings are independently hand-derived.
   - **Runner Weaknesses Noted for Future Lifecycle Work:** We formally record Codex's observations regarding runner edge cases (manifest pre/post comparison within runner loop, partial capture resilience, and report vs. log write ordering) as technical debt to address before general production deployment, while confirming none affected this flawless zero-error execution.
   - **Deprecation Notice:** The MarkupSafe `__version__` warning is noted; future maintenance can migrate to `importlib.metadata.version("markupsafe")`.

3. **Stage 3B Formally Closed:** With 15/15 tests passing, zero asset drift, and complete evidence preservation, Stage 3B is formally completed and closed.

---

## 2. Inventory of Missing Gated Tokenizers

The matched baseline architecture requires 5 logical roles across 4 model families:
- **Judge 2:** `openai/gpt-oss-120b` (Public, **ACQUIRED & VALIDATED**)
- **Judge 1:** `Qwen/Qwen3-Next-80B-A3B-Instruct` (Public, **ACQUIRED & VALIDATED**)
- **Generator & Verifier (Shared Role):** `meta-llama/Llama-3.3-70B-Instruct` (**PENDING ACQUISITION / GATED**)
- **Router:** `google/gemma-3-12b-it` (**PENDING ACQUISITION / GATED**)

Per [Antigravity-0083](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261014-antigravity-0083-databricks-acquisition-manifest-and-gate-sequence.md) and [Codex-0101](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0101-tokenizer-acquisition-bounded-recommendation.md), the specifications for the two gated model families are:

### 2.1 Shared Generator & Verifier: Llama 3.3 70B Instruct
- **Repository:** `meta-llama/Llama-3.3-70B-Instruct`
- **Pinned Commit SHA:** `6f6073b423013f6a7d4d9f39144961bfbfbc386b`
- **Destination Directory:** `assets/tokenizers/generator/`
- **Approved File Allowlist:**
  - `tokenizer.json` (~17.2 MB)
  - `tokenizer_config.json` (~56.0 KB)
  - `special_tokens_map.json` (~444 B)
- **Hard Byte Ceiling:** **22,000,000 bytes** (22 MB)
- **License / Access:** Meta Llama 3.3 Community License (Requires user agreement on Hugging Face).

### 2.2 Router: Gemma 3 12B IT
- **Repository:** `google/gemma-3-12b-it`
- **Pinned Commit SHA:** `96b6f1eccf38110c56df3a15bffe176da04bfd80`
- **Destination Directory:** `assets/tokenizers/router/`
- **Approved File Allowlist:**
  - `tokenizer.json` (~17.5 MB)
  - `tokenizer.model` (~4.3 MB)
  - `tokenizer_config.json` (~46.0 KB)
  - `special_tokens_map.json` (~846 B)
  - `chat_template.json` (~1.2 KB)
- **Hard Byte Ceiling:** **25,000,000 bytes** (25 MB)
- **License / Access:** Google Gemma Terms of Use (Requires user agreement on Hugging Face).

### 2.3 Strict Asset Exclusions (Both Models)
- Zero model weights: strictly reject `*.safetensors`, `model.safetensors.index.json`, `*.bin`, `*.pth`, `original/*`, and `metal/*`.
- Reject Git LFS pointer text or HTTP error pages.
- No mirror or unauthenticated third-party fallback repositories.

---

## 3. Proposed Acquisition Pathways for User & Codex Determination

Because Llama 3.3 and Gemma 3 are gated repositories requiring authenticated authorization from Hugging Face, we outline two explicit implementation pathways for user and Codex selection:

### Pathway A: User Manual Drop-In (Maximum Credential Isolation — Recommended)
1. **User Action (Outside Chat):**
   - The user accepts the Llama 3.3 and Gemma 3 terms on Hugging Face using their own account.
   - The user manually downloads the exact allowlisted files pinned to the specific commit SHAs above.
   - The user places them into:
     - `assets/tokenizers/generator/`
     - `assets/tokenizers/router/`
2. **Audit & Manifest Update (Agent):**
   - Prepare a bounded, offline staging verification script `scripts/matched_baseline/verify_gated_staging.py`.
   - The script verifies that only the approved files exist, checks that total directory byte counts are strictly under the 22 MB and 25 MB ceilings, computes SHA-256 digests, and generates an updated canonical manifest `tokenizer_manifest.sha256`.
3. **Safeguard Advantage:** Zero Hugging Face tokens or credentials enter the environment, workspace, or chat.

### Pathway B: User-Authorized Local Token Acquisition Script
1. **Prerequisite:** User confirms they have accepted the licenses on Hugging Face and have an active `HF_TOKEN` in their user environment variables.
2. **Script Design:** Antigravity drafts a dedicated, single-purpose acquisition script `scripts/matched_baseline/acquire_gated_tokenizers.py` subject to Codex review:
   - Reads `HF_TOKEN` exclusively from `os.environ.get("HF_TOKEN")`; never prints, logs, or saves the token to disk.
   - Requests exclusively from official URLs: `https://huggingface.co/<repo>/resolve/<pinned_commit>/<file>`.
   - Enforces hard stream chunk size checks: immediately aborts and deletes partial files if download exceeds the per-role byte ceiling.
   - Checks HTTP status 200 and validates magic bytes/JSON syntax to reject LFS pointers or error responses.
   - Staging to exclusive output directories; exits code 2 on directory collision.
   - Captures byte counts and SHA-256 digests, appending to manifest for audit.
3. **Execution Gate:** The script is reviewed and approved by Codex and the user before execution.

---

## 4. Next-Step Roadmap (Stage 3C & Gate C Readiness)

Once the gated tokenizers are staged under either Pathway A or Pathway B:

1. **Stage 3C Adapter Extension:**
   - Extend [`MANDATORY_ROLE_FILES`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py#L42) and [`PER_MODEL_ALLOWED_ROLES`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py#L57) in `fast_tokenizer_adapter.py` for `generator` and `router`.
   - Add unit tests for Llama and Gemma chat template parsing and tokenization in a dedicated offline test suite (`tests/test_offline_gated_tokenizer_assets.py`).
2. **Gate C Readiness:**
   - Once all 4 tokenizer families are verified, Gate C offline real-data preflight (evaluating token counts and envelope margins across 350 queries on disposable store copies) can be reviewed and authorized.
3. **Preserved Boundaries:**
   - Databricks keys remain unnecessary and unused.
   - Real benchmark stores and candidate graphs remain sealed.
   - Zero model inference and zero live network API calls.

---

## 5. Recommendation & Request for User / Codex Direction

We recommend **Pathway A (User Manual Drop-In)** as the cleanest and most secure path to resolve the gated tokenizers without exposing credentials or requiring network authentication scripts.

We request user and Codex review on:
1. Concurrence on Stage 3B closure.
2. Selection of Pathway A vs. Pathway B for Llama 3.3 and Gemma 3 acquisition.
