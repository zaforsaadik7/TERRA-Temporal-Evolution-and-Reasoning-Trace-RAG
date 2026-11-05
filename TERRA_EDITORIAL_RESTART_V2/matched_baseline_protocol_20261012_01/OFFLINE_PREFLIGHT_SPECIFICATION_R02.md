# Offline Preflight Specification for Matched-Resource Baseline (I4) — Revision 02

**Date:** 13 October 2026 (Asia/Dhaka)  
**Status:** REVISED SPECIFICATION (Pre-Implementation Review)  
**Author:** Antigravity (Context Peer & Implementation Partner)  
**Reviewer:** Codex (Implementation Lead)  
**Supersedes:** `OFFLINE_PREFLIGHT_SPECIFICATION_R01.md`  
**Governing Reviews:** [Codex-0086](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0086-offline-preflight-spec-review.md), [OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md)  
**Scope:** Specification only. Zero real-data execution, zero store access, zero graph decompression, zero tokenizer downloads, zero live API calls, zero credential reading, zero data or manuscript edits.

---

## 1. Governance, Authorship & Execution Sequence

This document defines the technical specification for an offline preflight audit of the I4 matched-resource baseline. In accordance with Codex-0086, development and execution are strictly segregated into three sequential, reviewable gates:

```
[ Gate A: Specification Freeze ]  <-- (Current Turn)
             │
             ▼
[ Gate B: Code-Only Driver Implementation + Synthetic Test Suite Audit ]
             │
             ▼
[ Gate C: Explicit Authorization for Real-Data Preflight Execution ]
```

1. **Gate A (Current Turn):** Peer review and alignment on this specification. No driver implementation, no file downloads, no store opening, no compressed graph extraction.
2. **Gate B (Next Code Step):** Implementation of the standalone diagnostic driver (`scripts/matched_baseline/offline_preflight.py`) accompanied by a fully mocked synthetic test suite exercising all preflight verification logic (`PASS`, `FAIL`, `BLOCKED` branches). Peer audit and verification by Codex.
3. **Gate C (Future Execution Step):** Only after Gate B receives explicit review approval and the user provides explicit execution authorization will the driver be run against local data copies.

---

## 2. Store Protection Protocol (Byte-Preserved Disposable Copy)

The original ChromaDB collection contains valuable experimental vector assets that must never be modified, corrupted, or altered by client initialization or schema migrations.

### Invariants:
1. **Never Open the Original Store:** Under no circumstances will any Chroma client connect directly to the active store directory.
2. **Pre-Copy Integrity Manifest:** Before any file operation, the preflight script will recursively walk the target Chroma directory, recording all filenames, file sizes, and SHA-256 hashes into `chroma_original_manifest_before.json`.
3. **Byte-Level Disposable Copy:** The entire directory hierarchy will be copied into an isolated, disposable working directory (`<run_dir>/chroma_disposable_copy/`).
4. **Isolated Client Binding:** The diagnostic Chroma client will bind strictly to `<run_dir>/chroma_disposable_copy/`.
5. **Post-Execution Integrity Manifest:** After preflight completion, a second manifest `chroma_original_manifest_after.json` will be computed on the original store and compared byte-for-byte against the initial manifest to mathematically prove zero byte drift.
6. **Offline Cache Binding for Embeddings:** 
   - Environment variables `TRANSFORMERS_OFFLINE=1` and `HF_HUB_OFFLINE=1` will be enforced.
   - The exact cached embedding model (e.g. BAAI/bge-large-en-v1.5) will be resolved strictly from local disk.
   - If the embedding model is absent from local cache, preflight terminates immediately with status **`BLOCKED`**, refusing fallback downloads.

---

## 3. Exact Corpus Parity & Layered Representation Audit

Document parity between Arm H (sparse + dense) and Arm T (graph traversal) cannot be established by ID counts or text lengths alone. Document text equality must be byte-exact.

### 1. Per-ID Byte and Hash Equality:
- Dense documents extracted from the disposable Chroma copy will be matched against sparse BM25 corpus documents on a strict per-ID basis:
  $$\forall d \in \text{Corpus}, \quad \text{SHA256}(\text{Text}_{\text{Dense}}(d)) == \text{SHA256}(\text{Text}_{\text{Sparse}}(d))$$
- Any missing ID, duplicate ID, or text hash mismatch triggers status **`FAIL`**.

### 2. Separation of Text Representation Layers:
We explicitly distinguish and audit two independent representation layers:
- **Layer 1: Ingestion Retrieval Text:** Used for dense embedding and sparse BM25 indexing (historical protocol uses legal opinion text, capped at 1,000 characters).
- **Layer 2: Serializer Evidence Payload:** Used for prompt evidence packing in both Arm H and Arm T (includes `snippet` up to 600 characters, `substantive_holding`, `thinking_trace`, `title`, `decision_date`, and `relation_context`).
- Both representation layers will be audited independently for consistency.

### 3. Authentic Graph Schema & Candidate Identity:
- **Candidate Graph Identity:** The candidate graph is pinned to the verified historical derivative `r30corr_v1` (from experiment provenance review), avoiding speculative paths.
- **Authentic Schema:** Graph nodes are indexed by dictionary key ID (e.g., `nodes[nid]`), and the presence of `case_id` will be normalized from the key if not a separate field.
- **Decompression Gate:** The graph archive (`.json.gz`) will only be decompressed in read-only streaming mode into an isolated scratch path during authorized execution; it will not be decompressed during specification or driver coding.
- **Missingness Policy:** Date or holding omissions in graph nodes will be audited against a frozen catalog missingness policy (reporting exact missingness counts) rather than silently dropping nodes or demanding artificial 100% field completeness inconsistent with the preserved corpus.

---

## 4. Annotation Parity & Evidence Charging

1. **Shared Annotation Payload:** Both Arm H and Arm T must draw from an identical query-independent relation catalog and deterministic support excerpts.
2. **Evidence Budget Charging:** All substantive metadata, procedural traces, and relation context admitted into the generator prompt are charged against the common 6,000-token evidence budget and 7,000-token prompt budget.

---

## 5. Full 350-Query Cohort & Dual-Route Envelope Feasibility

Rather than testing a small subset of 15 pilot queries, the offline preflight must verify packaging feasibility across the entire **350-query evaluation cohort**.

### Methodology (Zero Live LLM Calls):
1. **Dual-Route Simulation per Query:** For each of the 350 queries, preflight evaluates:
   - **EASY Envelope:** Arm T extracts only top 2 dense seeds (0-hop, `max_depth_override=0`); Arm H extracts RRF top 100.
   - **HARD Envelope:** Arm T expands dual-directional graph traversal up to `max_depth=2` bounded by `max_structural_chars=35000` and `max_graph_nodes=40`; Arm H extracts RRF top 100.
2. **Multi-Stage Prompt Packing Verification:**
   - **Generator Prompt:** Validates base instruction + query + evidence items fits within 7,000 tokens using candidate tokenizer.
   - **Verifier Prompt:** Evaluates epistemic consistency checking template.
   - **Dual Judge Prompts:** Evaluates Judge 1 and Judge 2 prompt templates under conservative upper-bound assumptions: generator answer length is set to the maximum allowed 4,096 tokens to verify that judge prompts do not exceed provider context windows even in worst-case generation lengths.
3. **Empirical Distribution Metrics:** Computes min, median, p95, and max for:
   - Admitted evidence items vs. dropped items.
   - Evidence token count and prompt token count.
   - Structural character count for Arm T.
4. **Controlled Traversal Disclosure:** The differences between the reviewed controlled traversal (strict depth cutoff, hub no-deeper-expansion, exact formatted character bounds) and historical traversal artifacts will be explicitly recorded.

---

## 6. Provider Endpoints, Pricing Schedule & Tokenizer Acquisition

1. **Endpoint & Context Window Evidence:**
   - The nominal 128,000 token limit is treated as unverified until pinned against official provider documentation.
   - The preflight manifest will record official dated specifications for each designated endpoint role:
     - **Generator:** LLaMA 3.3 70B Instruct.
     - **Verifier:** Designated verifier endpoint.
     - **Dual Judges:** Designated Judge 1 and Judge 2 endpoints.
     - **Router:** Fast route classifier endpoint.
2. **Comprehensive Cost Schedule:**
   - Financial reservation must account for all billable stages: Router, Verifier, Generator, Judge 1, Judge 2, plus potential retry allocations.
   - A static pricing lookup table ($/M input tokens, $/M output tokens) will be formalized in the driver.
   - Conservative pre-dispatch reservation is enforced: a full 4,096-token completion reservation is reserved in `CallLedger` before dispatch.
   - Global spending ceiling is enforced at **$100.00 USD**.
3. **Bounded Tokenizer Acquisition Gate:**
   - If LLaMA 3.3 tokenizer files are absent from the local HuggingFace cache, preflight marks the tokenizer status as **`BLOCKED`**.
   - A separate, bounded acquisition gate will specify the exact official HuggingFace repository revision, specific file list (`tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`), and expected SHA-256 digests. No automatic download is permitted during preflight.

---

## 7. Operational Manifest, Output Isolation & Disposition Statuses

### Directory Isolation:
- Each preflight execution runs in a timestamped, non-overwriting run directory:
  `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/preflight_run_<YYYYMMDD_HHMMSS>/`
- The directory contains:
  - `preflight_config.json`: Pinned configuration, hashes of input manifests, interpreter version, and git commit.
  - `chroma_original_manifest_before.json` & `chroma_original_manifest_after.json`.
  - `corpus_parity_manifest.json`: Per-ID text hash match results.
  - `query_envelope_350_summary.json`: Distribution metrics across all 350 queries.
  - `preflight_final_report.md`: Human-readable executive summary and verdict.

### Disposition Statuses:
- **`PASS`**: All 350 queries pack within budget under both envelopes, 100% corpus ID/text hash equality holds, zero byte drift on Chroma store copy, graph schema valid.
- **`FAIL`**: Contract violation (e.g. text hash mismatch, prompt token ceiling exceeded, schema violation).
- **`BLOCKED`**: External prerequisite missing (e.g. offline tokenizer artifact not in cache, embedding model not found). Preflight stops cleanly without error, reporting exactly what asset must be acquired.

---

## 8. Summary of Proposed Action Plan

1. **Present Gate A Specification (this revision)** to Codex for review and confirmation.
2. **Upon Gate A Approval:** Implement `scripts/matched_baseline/offline_preflight.py` and `tests/test_offline_preflight_synthetic.py` (Gate B, code-only).
3. **No real data will be accessed, copied, or evaluated until Gate B is fully audited and passed.**
