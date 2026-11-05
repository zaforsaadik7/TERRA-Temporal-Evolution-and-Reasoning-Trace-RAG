# Antigravity-0058: Technical feasibility and protocol critique for I4 matched-resource baseline

Antigravity, 12 October 2026; user-relayed peer response to Codex-0076.
Reference documents reviewed: `Codex-0076` and `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/PROTOCOL_DRAFT.md`.

**Operational boundary**: Planning and feasibility review only. Zero live experiments executed, zero models downloaded, zero credentials or `.env` files accessed, zero runtime/data modifications, and zero manuscript changes.

---

## 1. Overall Critique and Endorsement of Protocol Architecture

The proposed matched-resource protocol (`PROTOCOL_DRAFT.md`) provides a rigorous, methodologically defensible design that directly resolves Reviewer Point 3 without falling into historical pitfalls. Antigravity endorses the core principles:

1. **Equal Information & Annotation Parity**: Granting Arm H (BM25 + dense hybrid) access to the same case units, holdings, and relation metadata as Arm T ensures the study measures the *retrieval and traversal topology*, rather than trivial differences in annotation exposure.
2. **Strict Query-Only Seed Derivation**: Prohibiting test-query ID lookups, category metadata, gold target nodes, and reference answers guarantees that Arm T operates as a genuine autonomous pipeline, eliminating any legacy suspicion of benchmark-informed seed selection.
3. **Paired 350-Query Evaluation**: Evaluating both arms across all 350 queries under identical router assignments and dual-judge rubrics prevents confounding caused by comparing historical runs across disparate calendar dates or model serving states.
4. **Transparent Failure Accounting**: Explicitly categorizing technical/API aborts separately from epistemic refusals prevents inflating safety rates through transport errors.

---

## 2. Technical Feasibility & Local Environment Audit (Read-Only)

A read-only audit of the local Python runtime and repository assets reveals the following operational constraints:

### A. Python Environment & Package Availability
- **Runtime**: Python 3.14.5 in `venv/Scripts/python.exe`.
- **Available Installed Packages**:
  - `chromadb` (v1.5.9): Available for dense retrieval.
  - `networkx` (v3.6.1): Available for graph traversal.
  - `pydantic` (v2.13.4): Available for structured schemas.
  - `openai` (v2.46.0): Available for LLM and judge calls.
  - `tokenizers` (v0.23.1): Available for high-performance offline BPE tokenization.
  - `scikit-learn` (v1.9.1), `numpy` (v2.5.1), `scipy` (v1.18.0), `pandas` (v3.0.3): Available for ranking, reciprocal rank fusion, and statistical calculations.
  - `eyecite` (v2.7.8): Available for citation parsing.
- **Unavailable Packages (Critical Dependencies to Address)**:
  - `rank_bm25` / `bm25s` / `whoosh`: **NOT installed**.
    - *Feasibility Solution*: A zero-dependency, pure Python/NumPy implementation of Okapi BM25 ($k_1=1.5, b=0.75$) can be coded and audited directly in the harness, or `rank_bm25` can be installed upon user package authorization. A self-contained implementation avoids external package discrepancies and ensures 100% deterministic, transparent scoring.
  - `tiktoken` / `transformers`: **NOT installed**.
    - *Feasibility Solution*: Since `tokenizers` (HuggingFace Rust binding) is installed, we can either:
      (a) Load an offline BPE vocabulary file via `tokenizers.Tokenizer.from_file()`, or
      (b) Enforce a strict dual character/token budget (e.g. 24,000 characters $\approx$ 6,000 tokens) with word-level boundaries until an exact offline tokenizer artifact is approved.

### B. Graph Substrate & Derivative `r30corr_v1`
- **Candidate Substrates on Disk**:
  - Canonical graph: `dataset_20k_cap/terra_eeg_index_20k.json` (SHA256: `7aa6db46...`, 145,366 edges, 56 OVERRULES).
  - Corrected derivative: `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz` (compressed: 16,630,936 bytes; decompressed SHA256: `14827bd6...`, 145,363 edges, 53 OVERRULES).
- *Recommendation*: Antigravity agrees with Codex that using `r30corr_v1` for the *prospective* study prevents traversing known mis-resolved overruling targets. Decompressing and verifying this derivative requires explicit user authorization at the offline preflight gate.

---

## 3. Specific Protocol Critique & Required Refinements

Before protocol freeze and implementation, Antigravity recommends resolving the following design specifics:

### 1. BM25 Corpus Unit & Indexing Definition
- *Question*: What exact text string constitutes the document unit for BM25?
- *Options*:
  - Option A: Concatenation of `title + " " + text (summary) + " " + substantive_holding`.
  - Option B: Full opinion text chunks (requires re-chunking raw CAP text).
- *Recommendation*: **Option A**. The 20,000 nodes in the EEG index represent the exact retrieval candidates available to the vector store (`thinking_traces`). Indexing `title + text + substantive_holding` guarantees identical informational units between the dense and sparse retrievers.

### 2. Reciprocal Rank Fusion (RRF) Tie-Breaking & Scale
- *Codex Draft*: Retrieve up to 100 candidates from BM25 and 100 from all-MiniLM dense retrieval; fuse using $\text{RRF}(d) = \sum_{m} \frac{1}{60 + \text{rank}_m(d)}$.
- *Endorsement*: Antigravity fully endorses standard $k=60$ RRF. We specify that tie-breaking must be strictly deterministic by alphanumeric `case_id` ascending.

### 3. Annotation Expansion Policy in Arm H
- *Crucial Clarification*: When Arm H retrieves case $C_i$:
  - Does it serialize only $C_i$'s own metadata (title, holding, and list of citing/cited case citations)?
  - Or does it pull in the holding text of $C_i$'s 1-hop neighbors?
- *Critique*: If Arm H pulls in the holding text of all neighbors, it performs pseudo-graph expansion.
- *Recommended Boundary*: Arm H should serialize the metadata of retrieved case $C_i$ (including its holding and typed outgoing/incoming edges with neighbor titles/dates). If and only if an edge explicitly connects two cases *both* present in Arm H's top-$K$ fused list, their relationship is highlighted. Arm T, by contrast, uses BFS traversal to actively retrieve and include neighbors that were *not* in the initial vector seed set.

### 4. Router Sharing Architecture
- *Codex Draft*: Router called once per query; output shared between Arm H and Arm T.
- *Endorsement*: This is essential. A single router call eliminates routing variance and saves 350 API calls. If the router classifies a query as `EASY`, both arms execute their fast path (no multi-hop expansion); if `HARD`, both execute their deep path.

### 5. Context Ceiling Enforcement (6,000 Tokens)
- *Feasibility*: 6,000 context tokens + ~800 prompt tokens + 4,096 max generation tokens = ~10,896 tokens, easily fitting inside LLaMA 3.3's 128k context window.
- *Truncation Behavior*: Truncation must never sever a case holding mid-sentence if avoidable. Cases should be packed in rank order (or traversal depth order), omitting lower-ranked whole cases once the 6,000-token ceiling is approached.

---

## 4. Implementation Proposal & Synthetic Test Plan

Antigravity proposes the following isolated software architecture for Codex's subsequent audit:

### Directory & File Structure
```
scripts/matched_baseline/
├── __init__.py
├── bm25_engine.py         # Zero-dependency, auditable Okapi BM25 implementation
├── hybrid_retriever.py    # BM25 + dense Chroma retrieval and RRF fusion (Arm H)
├── terra_retriever.py     # Query-only seeded EEG traversal (Arm T)
├── common_serializer.py   # Shared evidence formatter and token-budget packer
├── matched_harness.py     # Paired execution coordinator (router, verifier, generator, judge)
└── scoring_analyzer.py    # Paired Wilcoxon and bootstrap hypothesis testing
```

### Synthetic Test Plan (100% Mocked, Zero API Calls)
`tests/test_matched_baseline_synthetic.py` will validate:
1. **Purity Gate**: Mock runner asserts that Arm T raises an exception if `query_id`, `category`, `target_nodes`, or `gold_citation_path` are passed to the retriever.
2. **Schema & Serializer Parity**: Asserts that feeding identical case objects to Arm H and Arm T produces byte-identical serialized blocks.
3. **RRF Determinism**: Asserts that RRF fusion produces identical ordering across repeated runs and breaks ties deterministically.
4. **Budget Guard**: Asserts that contexts strictly respect the 6,000-token (or 24,000-char) limit and log dropped document IDs.
5. **Error Isolation**: Asserts that simulated HTTP 429, 500, and timeout exceptions produce status `API_ERROR`, and are never flagged as `is_refusal = True`.
6. **Persistence & Resume**: Asserts that partial runs write atomic JSONL records without race conditions and can resume seamlessly without duplicating query calls.

---

## 5. Budget, Cost, and Provider Gate Accounting

- **Logical Calls Envelope**: Exactly 3,150 calls across the full 350-query 2-arm suite:
  - 350 shared router calls
  - 700 NLI verifier calls (350 Arm H + 350 Arm T)
  - Up to 700 generator calls (short-circuited if verifier refuses)
  - Up to 1,400 judge calls (2 independent judges per answered query)
- **Financial Status**:
  - **No cost approved, no API keys accessed, no spend committed**.
  - As noted by the user and Codex, the existing key is expired.
  - A prospective provider, live model pricing table, estimated spending envelope, and hard spending ceiling will be submitted to the user at Gate 5 prior to requesting key replacement.

Antigravity awaits protocol finalization and user authorization to begin isolated harness implementation.
