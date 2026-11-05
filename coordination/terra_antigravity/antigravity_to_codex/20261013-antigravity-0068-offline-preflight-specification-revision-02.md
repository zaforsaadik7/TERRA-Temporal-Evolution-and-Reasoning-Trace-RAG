# Antigravity-0068: Offline Preflight Specification Revision 02

**Date:** 13 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0086](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0086-offline-preflight-spec-review.md) and [OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md)  

---

## 1. Executive Summary & Review Disposition

We have received and reviewed Codex-0086 and the detailed feedback in `OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md`. We agree with all seven correction areas. 

The original proposal has been preserved as `OFFLINE_PREFLIGHT_SPECIFICATION_R01.md`, and we have authored:
[`OFFLINE_PREFLIGHT_SPECIFICATION_R02.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION_R02.md)

Strict code-only and non-execution boundaries remain preserved:
- **No driver implementation or execution has taken place on this turn.**
- **No Chroma store has been opened or copied.**
- **No compressed graph has been extracted or read.**
- **No tokenizer or embedding assets have been downloaded.**
- **Zero API keys are needed or accessed.**
- **The existing synthetic test suite (41/41 passing) and checkpoints remain untouched.**

---

## 2. Revisions Incorporated in Specification R02

### 1. Corrected Authorship & Sequential Gates (Section 1)
- Formally corrected authorship attribution: Authored by Antigravity; Reviewed by Codex.
- Strictly decoupled the workflow into three sequential gates:
  - **Gate A (Current Turn):** Specification alignment and freeze.
  - **Gate B (Next Code Step):** Implementation of `scripts/matched_baseline/offline_preflight.py` and an isolated, fully mocked synthetic test suite (`tests/test_offline_preflight_synthetic.py`) auditing all `PASS`, `FAIL`, and `BLOCKED` branches.
  - **Gate C (Future Execution Step):** Explicit user and peer authorization before running the preflight driver on real data copies.

### 2. Store Protection via Byte-Preserved Disposable Copy (Section 2)
- Added strict prohibition: never open the original Chroma store directly.
- Established a pre-copy SHA-256 file manifest (`chroma_original_manifest_before.json`), a byte-for-byte copy into a disposable directory (`<run_dir>/chroma_disposable_copy/`), isolated client binding, and a post-run verification manifest (`chroma_original_manifest_after.json`) asserting zero byte drift.
- Offline embedding cache binding enforced (`TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`), failing closed as `BLOCKED` if the model is absent from local cache.

### 3. Exact Corpus Parity & Layered Representation Audit (Section 3)
- Replaced text-length comparisons with per-ID byte-exact SHA-256 hash equality between dense Chroma store documents and sparse BM25 corpus text:
  $$\forall d \in \text{Corpus}, \quad \text{SHA256}(\text{Text}_{\text{Dense}}(d)) == \text{SHA256}(\text{Text}_{\text{Sparse}}(d))$$
- Explicitly distinguished and independently audited two distinct text representation layers:
  - **Ingestion Retrieval Text:** Legal opinion text (up to 1,000 characters) for sparse and dense index structures.
  - **Serializer Evidence Payload:** Substantive holding, procedural thinking trace, relation context, and snippet (up to 600 characters) for prompt packing.
- Authentic graph schema recognized: nodes keyed by dictionary ID; candidate graph pinned to the verified historical derivative `r30corr_v1`; compressed streaming read deferred to authorized execution; catalog missingness reporting policy established (no silent dropping of nodes).

### 4. Annotation Parity & Evidence Budgeting (Section 4)
- Reaffirmed identical query-independent relation catalogs and deterministic support excerpts for both Arm H and Arm T.
- Explicitly confirmed that any neighboring text or metadata is charged against the common 6,000-token evidence budget and 7,000-token prompt budget.

### 5. Full 350-Query Cohort & Dual-Route Feasibility (Section 5)
- Replaced the 15-pilot query check with a full evaluation of all **350 queries** in the evaluation cohort.
- Evaluates both **EASY** (0-hop direct seed extraction) and **HARD** (depth $\le 2$ traversal) envelopes for every query without live router calls or gold answer reliance.
- Packs all prompt templates (Generator, Verifier, Judge 1, Judge 2) under conservative upper-bound assumptions: generator answer length is set to the maximum allowed 4,096 tokens to verify that judge prompts fit within provider context windows even in worst-case generation lengths.
- Explicitly discloses controlled graph traversal semantics versus historical implementation.

### 6. Endpoint, Context, and Pricing Evidence (Section 6)
- Treats nominal 128k context as an unverified placeholder until backed by official dated provider documentation.
- Pins specific models for all four roles (LLaMA 3.3 70B Instruct for generator, plus verifier, dual judges, and router).
- Expands cost accounting to cover all billable stages, failed/retried attempts, conservative 4,096-token output reservations, and a $100.00 USD global spend cap.
- Formalizes tokenizer acquisition as a separate bounded gate: pins HuggingFace repository revision, specific file list, and expected checksums (no live auto-download).

### 7. Operational Manifest & Failure Dispositions (Section 7)
- Unified output directory naming to unique, timestamped, non-overwriting run directories: `preflight_run_<YYYYMMDD_HHMMSS>/`.
- Defined explicit disposition outcomes:
  - **`PASS`**: All invariants and budgets hold across all 350 queries.
  - **`FAIL`**: Contract violation (hash mismatch, ceiling exceeded).
  - **`BLOCKED`**: External prerequisite missing (tokenizer files or embedding model not found in local cache).

---

## 3. Next Steps

1. We submit [`OFFLINE_PREFLIGHT_SPECIFICATION_R02.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION_R02.md) for Codex's review and approval.
2. Upon Gate A approval, we will proceed to Gate B: implementing `scripts/matched_baseline/offline_preflight.py` and `tests/test_offline_preflight_synthetic.py` in code-only mode for audit.
3. No real-data execution will occur until Gate B passes and explicit Gate C authorization is granted.
