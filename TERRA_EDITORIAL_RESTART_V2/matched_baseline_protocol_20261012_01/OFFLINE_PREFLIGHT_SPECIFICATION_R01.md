# Offline Preflight Specification for Matched-Resource Baseline (I4)

**Date:** 13 October 2026  
**Status:** PROPOSED SPECIFICATION (Pre-Execution Review)  
**Authors:** Antigravity & Codex  
**Scope:** Read-only inspection, asset inventory, corpus parity checks, and configuration freeze. Zero live API calls, zero downloads, zero key access, zero real store modifications, and zero manuscript changes.

---

## 1. Executive Objective & Governance Boundaries

The purpose of this offline preflight is to verify that all prospective data assets, tokenizer files, graph representations, and provider configurations for the I4 matched-resource baseline protocol are verified, compatible, and aligned *before* requesting user API keys, budget authorization, or execution permission.

### Fail-Closed Governance Rules:
1. **Zero External Network / API Calls:** No network requests will be dispatched.
2. **Zero API Key Access:** No `.env` files, environment keys, or user credentials will be inspected or requested during this stage.
3. **Strict Read-Only Data Operations:** All candidate databases, graph archives, and corpus directories are accessed in strictly read-only mode (`r` / `rb`), never modified, relocated, or overwritten.
4. **Isolated Diagnostic Outputs:** Any generated diagnostic logs or manifests will be written exclusively to an isolated scratch folder (`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/preflight_scratch/`).
5. **Fail-Closed Gate Checks:** If any parity mismatch, hash discrepancy, or schema violation is observed, preflight halts immediately with a diagnostic failure report.

---

## 2. Asset & Configuration Inventory Matrix (Present vs. Missing)

| Domain | In Codebase / Repository (Present) | Required for Execution (Missing / Gaps) | Preflight Resolution Strategy |
| :--- | :--- | :--- | :--- |
| **1. Tokenizer & Chat Template** | `TokenizerInterface`, `MockBpeTokenizer` (synthetic mock), `ProductionTokenizer` (fail-closed placeholder). | Exact local tokenizer artifact (e.g. `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`) for LLaMA 3.3 70B Instruct; byte-accurate BPE token counter. | Search local environment / HuggingFace cache for existing offline tokenizer weights; if absent, define bounded, checksum-verified download gate for tokenizer files only. |
| **2. Endpoint & Context Limits** | Context ceiling formulas: prompt $\le 7,000$, output reservation $= 4,096$, window $= 128,000$ tokens in `CommonSerializer`. | Final provider selection (e.g., DeepInfra, Together, OpenRouter, Groq) and verified advertised context window / rate-limits. | Document target provider context window specifications and per-request token ceilings in static manifest. |
| **3. Prospective Graph Identity** | Dual-directional traversal engine (`TerraRetriever`) with 50-degree hub logic, 75/25 cap, recency sorting, and depth boundary. | Definite identity and SHA-256 hash of the prospective production EEG graph archive (e.g. `eeg_graph.json` or `.gz`). | Locate existing local graph files; verify SHA-256 hash, record node count, edge count, and field schema without modifying the archive. |
| **4. Sparse/Dense Corpus Parity** | `RobertsonOkapiBM25` (sparse), `HybridRetriever` (RRF fusion), verified evidence formatting. | Verification that document IDs and text representations in the sparse BM25 corpus match the dense ChromaDB store. | Execute read-only ID intersection and text length comparison between ChromaDB metadata and BM25 index corpus. |
| **5. Controlled Traversal Differences** | Arm H: Dense 100 + BM25 100 $\to$ RRF $\to$ token packing. Arm T: Dense seeds (top 2) $\to$ graph traversal (depth $\le 2$, or 0 on EASY) $\to$ token packing. | Test sample queries against candidate graph to verify traversal node counts, tie-breaking, and memory footprint under real scale. | Run offline traversal dry-runs on candidate queries without LLM callbacks. |
| **6. Token Budget Packaging** | Strict `CommonSerializer` packing: 6,000 evidence tokens, 7,000 prompt tokens, immutable `PackedEvidence`. | Real-query empirical token distributions: fraction of retrieved documents retained vs. dropped across Arm H and Arm T. | Run offline serialization across query cohort to measure token retention distributions using candidate tokenizer. |
| **7. Cost & Usage Accounting** | Two-phase pre-call reservation (`CallLedger`), financial breach detection (`BUDGET_BREACH`), monotonic reload replay. | Production HTTP response adapter: mapping provider usage JSON (`usage.prompt_tokens`, `usage.completion_tokens`) to ledger settlement. | Specify provider-specific pricing schedule ($/M prompt tokens, $/M completion tokens) and JSON response parser schema. |

---

## 3. Step-by-Step Offline Preflight Plan

### Step 1: Local Tokenizer Inventory & Chat-Template Verification
- **Input:** Local cache directories (`~/.cache/huggingface/hub/` or local model assets).
- **Checks:**
  1. Check for availability of LLaMA 3 / 3.3 tokenizer files locally.
  2. If found, verify checksums and instantiate offline BPE tokenizer.
  3. Verify token counts against standardized benchmark strings (e.g. Latin legal terms, Case citations).
  4. Verify exact chat template rendering without BOS duplication or trailing token errors.
- **Stop Condition:** If no compatible local tokenizer is present, document exact missing artifact paths and hash requirements for a subsequent bounded acquisition approval.

### Step 2: Read-Only Graph Inventory & Schema Verification
- **Input:** Existing graph archives in workspace (e.g. `data/` or historical experiment outputs).
- **Checks:**
  1. Compute SHA-256 hash of graph archive file.
  2. Parse nodes and edges in read-only streaming mode.
  3. Validate node schema: presence of `case_id`, `decision_date` (parseable date), `substantive_holding`, `thinking_trace`.
  4. Validate edge schema: `source`, `target`, `relation`.
  5. Check graph topology: count high-degree hub nodes ($> 50$) and verify hub distribution.
- **Stop Condition:** Halt if any node lacks `case_id`, if dates are unparseable, or if edge references point to missing nodes.

### Step 3: Sparse/Dense Corpus Parity Audit
- **Input:** Existing ChromaDB store and BM25 candidate corpus.
- **Checks:**
  1. Extract doc IDs from ChromaDB in read-only mode (`get(include=['metadatas'])`).
  2. Extract doc IDs from BM25 corpus text files.
  3. Compute set intersection: verify $\text{IDs}_{\text{Dense}} \equiv \text{IDs}_{\text{Sparse}} \equiv \text{Nodes}_{\text{Graph}}$.
  4. Compare document text length distribution: ensure Arm H and Arm T draw from identical underlying substantive text.
- **Stop Condition:** Halt if ID overlap is less than 100% or if text representations diverge.

### Step 4: Dry-Run Traversal & Packaging Analysis (Zero LLM Calls)
- **Input:** Candidate query cohort (e.g., 15 pilot queries or evaluation query IDs).
- **Checks:**
  1. Retrieve dense candidates (top 100) and sparse candidates (top 100).
  2. Compute RRF fusion for Arm H.
  3. Run `TerraRetriever` for Arm T using top 2 dense seeds.
  4. Apply `CommonSerializer.pack_and_serialize` to both candidate lists.
  5. Measure retained vs. dropped document counts, prompt token counts, and structural character counts.
- **Stop Condition:** Halt if prompt tokens exceed 7,000 or if structural characters exceed 35,000.

### Step 5: Production Provider Pricing Schedule & Response Schema Specification
- **Specification:**
  - Define static pricing lookup table:
    - LLaMA 3.3 70B Instruct: Prompt rate ($/1M tokens), Completion rate ($/1M tokens).
    - Provider response JSON schema mapping:
      ```json
      {
        "prompt_tokens": "response['usage']['prompt_tokens']",
        "completion_tokens": "response['usage']['completion_tokens']",
        "cost_usd": "(prompt_tokens * prompt_rate + completion_tokens * completion_rate) / 1e6"
      }
      ```
  - Verify that `CallLedger.settle_call()` accurately logs these computed costs and enforces spend caps.

---

## 4. Preflight Execution Script & Outputs

- **Preflight Driver Script:** `scripts/matched_baseline/run_offline_preflight.py` (read-only, diagnostic mode only).
- **Isolated Artifact Output Directory:**
  `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/preflight_results/`
  Containing:
  - `preflight_summary.json`: Status, hashes, node counts, parity rates, and token distributions.
  - `preflight_report.md`: Human-readable audit report with pass/fail dispositions per gate.

---

## 5. Next Steps

1. Review and refine this specification with Codex.
2. Upon user and peer alignment, implement the read-only preflight driver script and run purely local inspection.
3. No live calls or API keys will be requested or used until the offline preflight report is reviewed and approved.
