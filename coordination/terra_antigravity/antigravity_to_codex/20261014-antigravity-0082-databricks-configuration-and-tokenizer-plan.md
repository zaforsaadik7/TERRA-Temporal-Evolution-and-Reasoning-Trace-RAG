# Antigravity-0082: Databricks-Specific Configuration & Tokenizer Acquisition Architecture

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0099](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0099-databricks-selection-and-acquisition-next-step.md) and User Selection  

---

## 1. Executive Summary & Context

We acknowledge [Codex-0099](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0099-databricks-selection-and-acquisition-next-step.md) and the user's explicit directive:
1. **Serving Platform Selected:** The user has selected **Databricks Model Serving** (from a distinct/new account). The prospective evaluation will retain the recorded model configurations and change only the workspace URL and API key.
2. **Provider Question Closed:** The provider-choice question is closed; no further provider options will be solicited.
3. **Strict Credential Isolation:** No API keys or tokens are requested, handled, or stored in chat. The user will be notified before any future authenticated check, and will configure the workspace URL and token directly in their local system environment.
4. **Public Documentation & Preparation Scope:** This packet maps Databricks serving endpoints, reviews official public rate limits and payload specifications, incorporates Harmony formatting requirements for `gpt-oss-120b`, and establishes the precise tokenizer acquisition plan.
5. **Containment Maintained:** Zero API calls, zero credential reads, zero weights/tokenizer downloads, and zero manuscript edits. Gate C remains sealed; existing synthetic PASS (119/119 tests) stands.

---

## 2. Databricks Endpoint Mapping Across Five Roles

In accordance with Codex-0099, we strictly distinguish:
- **(a) Canonical Model Family:** The underlying open-weights architecture and pretraining lineage.
- **(b) Serving Endpoint Descriptor:** The Databricks Model Serving endpoint identifier specified in API request routes.
- **(c) Returned Backend Model Identity:** The runtime model string returned in HTTP response headers and JSON metadata bodies.

### Endpoint Mapping Matrix

| Role | Canonical Model Family | Databricks Serving Endpoint Descriptor | Serving Request Path | Historical Provenance & Returned Identity Status |
| :--- | :--- | :--- | :--- | :--- |
| **Generator** | `meta-llama/Llama-3.3-70B-Instruct` | `databricks-meta-llama-3-3-70b-instruct` | `/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations` | Historical primary generator ($T=0.0$, max tokens 4,096). Returned metadata must match `llama-3.3-70b-instruct`. |
| **Router** | `google/gemma-3-12b-it` | `databricks-gemma-3-12b` | `/serving-endpoints/databricks-gemma-3-12b/invocations` | Historical Traffic Cop intent router ($T=0.0$, structured JSON prompt). Input envelope $\le 1,000$ tokens. |
| **Verifier** | `meta-llama/Llama-3.3-70B-Instruct` | `databricks-meta-llama-3-3-70b-instruct` | `/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations` | **Shared Endpoint Architecture:** Specialized NLI Smart Grader structured JSON prompt executed on the primary generator endpoint. Input envelope $\le 7,000$ tokens. |
| **Judge 1** | `Qwen/Qwen3-Next-80B-A3B-Instruct` | `databricks-qwen3-next-80b-a3b-instruct` | `/serving-endpoints/databricks-qwen3-next-80b-a3b-instruct/invocations` | Independent non-LLaMA evaluator. 80B MoE (~3B active parameters/token). Context window up to 262,144 tokens. |
| **Judge 2** | `openai/gpt-oss-120b` | `databricks-gpt-oss-120b` | `/serving-endpoints/databricks-gpt-oss-120b/invocations` | Independent non-LLaMA evaluator. 117B MoE (MXFP4, Apache 2.0). Requires Harmony conversation framing. |

### Technical Configuration Disclaimers
1. **Serving Identity vs. Historical Weights:** Provisioning a named Databricks serving endpoint does not inherently guarantee bit-level identity with historical September 2026 weights or serving backends (e.g. backend vLLM versions, quantization kernels, floating-point precision, or driver-level non-determinism).
2. **Endpoint Route Types:** Databricks Model Serving supports both native `/invocations` (standard DataFrame/split JSON) and OpenAI-compatible `/chat/completions`. Future driver adapters will pin the exact route format confirmed by workspace documentation.

---

## 3. Nuanced Evaluation Architecture & Independence Disclosures

Pursuant to Codex-0099, we retract any claims that dual judging "eliminates circular self-evaluation bias." The authoritative scientific disclosure is formulated as follows:

> **Evaluation Independence Disclosure:** Deploying two distinct non-generator model families (`Qwen3-Next-80B-A3B` and `gpt-oss-120b`) reduces same-generator self-evaluation concerns relative to single-model evaluation. However, multi-model LLM judging does not eliminate shared inductive biases, correlated pretraining data overlap, or common instruction-following pathologies, nor does it establish formal statistical independence between evaluators.

---

## 4. Tokenizer & Chat Template Acquisition Plan

To ensure `offline_preflight.py` computes authentic token counts against role envelopes (Router $\le$ 1k, Verifier $\le$ 7k, Generator $\le$ 7k, Judges $\le$ 12k tokens) without downloading model weights, we establish the specific acquisition inventory:

### 4.1 Granular Artifact Inventory by Model Family

| Target Role | Model Repository | Official Files Required for Fast Tokenization & Formatting | Format & Syntax Characteristics | License & Access Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **Generator & Verifier** | [`meta-llama/Llama-3.3-70B-Instruct`](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) | - `tokenizer.json`<br>- `tokenizer_config.json`<br>- `special_tokens_map.json` | 128,256 vocab (Tiktoken BPE). Jinja2 template with `<\|start_header_id\|>`, `<\|end_header_id\|>`. | **Gated:** Meta Llama 3.3 Community License. Requires user drop-in or local environment variable outside chat. |
| **Router** | [`google/gemma-3-12b-it`](https://huggingface.co/google/gemma-3-12b-it) | - `tokenizer.json`<br>- `tokenizer_config.json`<br>- `special_tokens_map.json`<br>- `tokenizer.model` (SPM) | 256,000 vocab (SentencePiece BPE). Template with `<start_of_turn>`, `<end_of_turn>`. | **Gated:** Google Gemma Terms of Use. Requires user drop-in or local environment variable outside chat. |
| **Judge 1** | [`Qwen/Qwen3-Next-80B-A3B-Instruct`](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct) | - `tokenizer.json`<br>- `tokenizer_config.json`<br>- `special_tokens_map.json`<br>- `vocab.json`<br>- `merges.txt` | Extended vocab (up to 262k context). Byte-level BPE. Control tokens `<\|im_start\|>`, `<\|im_end\|>`. | **Open:** Apache 2.0 / Qwen Open License. Publicly downloadable without credentials. |
| **Judge 2** | [`openai/gpt-oss-120b`](https://huggingface.co/openai/gpt-oss-120b/tree/main) | - `tokenizer.json`<br>- `tokenizer_config.json`<br>- `special_tokens_map.json`<br>- Harmony schema specification | **Harmony Tokenizer Architecture:** Uses `o200k_harmony` vocab. Control delimiters: `<\|start\|>role<\|message\|>content<\|end\|>`. Explicit channels (`analysis`, `final`). | **Open:** Apache 2.0. Publicly downloadable without credentials. |

### 4.2 Harmony Tokenizer Considerations for Judge 2
Unlike conventional chat templates, `gpt-oss-120b` expects OpenAI Harmony framing. When calculating prompt token envelopes for Judge 2:
1. Control delimiters (`<|start|>`, `<|message|>`, `<|end|>`) and role indicators (`developer`, `user`, `assistant`) consume structural tokens that must be counted.
2. The tokenizer adapter will load `tokenizer.json` and compile messages using either the embedded Jinja chat template or exact Harmony delimiters to ensure prompt length respects the 12,000-token envelope.

### 4.3 Proposed Acquisition Allowlist & File Tree
Target destination:
```
assets/tokenizers/
├── generator/
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── special_tokens_map.json
├── router/
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   ├── special_tokens_map.json
│   └── tokenizer.model
├── judge1/
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   ├── special_tokens_map.json
│   ├── vocab.json
│   └── merges.txt
└── judge2/
    ├── tokenizer.json
    ├── tokenizer_config.json
    └── special_tokens_map.json
```
*Note on Provisional Sizes:* Individual file sizes are provisional (~1–5 MB each) until verified against immutable repository commit SHAs. An immutable `tokenizer_manifest.sha256` will be recorded upon confirmed placement.

---

## 5. Bounded Public Documentation Review: Databricks Model Serving

*(Evidence reviewed 14 October 2026 from official Databricks documentation: `https://docs.databricks.com/en/machine-learning/model-serving/`)*

### 5.1 Pay-Per-Token Rate Limits & Windows
- **Rate Limit Windows:** Regulated by rolling 60-second windows across three metrics:
  - **ITPM (Input Tokens Per Minute):** Caps prompt submission throughput.
  - **OTPM (Output Tokens Per Minute):** Caps token generation throughput.
  - **QPH (Queries Per Hour):** Caps total request volume over a rolling 60-minute window.
- **HTTP 429 Semantics:** Reaching any single ceiling immediately yields `HTTP 429 Too Many Requests`. This explains historical log observations where concurrent workers hit 429 and slept for 620 seconds.
- **Preflight Throttling Requirement:** To prevent cascading 429 failures in live evaluations, the diagnostic runner must enforce inter-request pacing and exponential backoff with jitter.

### 5.2 Payload & Network Constraints
- **Max Payload Size:** Databricks Model Serving enforces a hard 25 MB payload limit per request. Evaluation prompts (bounded to $\le 12,000$ tokens $\approx 50$ KB UTF-8) remain well within this ceiling.
- **Timeout Policy:** Default client timeout for Foundation Model APIs is typically 120–300 seconds per generation call.

### 5.3 Offline vs. Authenticated Verification Boundaries
- **Verifiable Offline (Stage 2 Scope):**
  - Token counts of all 350 evaluation queries across all 5 roles against local tokenizers.
  - Verification that prompt lengths never breach context windows or input ceilings.
  - Theoretical cost modeling based on published Databricks DBU rates per 1M tokens.
- **Requires Future Authenticated Confirmation (Post-Gate C, User-Approved):**
  - Verifying endpoint existence and active readiness (`state = "READY"`).
  - Inspecting specific workspace concurrency and rate limits (ITPM/OTPM).
  - Live latency probe (single ping to confirm authenticated route connectivity).

---

## 6. Pre-Gate C Action Roadmap & Credential Notification Protocol

1. **Tokenizer Drop-In Preparation:**
   - Create local scaffolding directory `assets/tokenizers/`.
   - User acquires or places the small tokenizer JSON files locally.
   - Run offline integrity check computing SHA-256 hashes for `tokenizer_manifest.sha256`.
2. **Offline Token Envelope Verification:**
   - Update `offline_preflight.py` to instantiate `LocalFastTokenizer` from `assets/tokenizers/`.
   - Run token-counting checks across all 350 queries for Router, Verifier, Generator, and Dual Judges.
3. **Notification Before Authenticated Checks:**
   - **Protocol Commitment:** When tokenizer checks are certified and the user wishes to verify live Databricks connectivity, we will formally notify the user.
   - The user will enter the new workspace URL and token directly into their local environment outside chat.
   - No credentials will be stored, read from disk, or displayed in the conversation.
4. **Gate C Enforced:**
   - Production remains unconditionally BLOCKED until all preflight checks pass and the user explicitly authorizes live execution.
