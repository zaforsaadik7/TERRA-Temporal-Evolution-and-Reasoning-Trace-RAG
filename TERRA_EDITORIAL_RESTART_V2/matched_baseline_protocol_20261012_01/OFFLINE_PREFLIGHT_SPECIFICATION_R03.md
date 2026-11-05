# Offline Preflight Specification for Matched-Resource Baseline (I4) — Revision 03

**Date:** 13 October 2026 (Asia/Dhaka)  
**Status:** REVISED SPECIFICATION (Pre-Implementation Review)  
**Author:** Antigravity (Context Peer & Implementation Partner)  
**Reviewer:** Codex (Implementation Lead)  
**Supersedes:** `OFFLINE_PREFLIGHT_SPECIFICATION_R02.md`, `OFFLINE_PREFLIGHT_SPECIFICATION_R01.md`  
**Governing Reviews:** [Codex-0087](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0087-preflight-R02-review.md), [OFFLINE_PREFLIGHT_SPEC_REVIEW_02.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPEC_REVIEW_02.md), [Codex-0086](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0086-offline-preflight-spec-review.md), [OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPEC_REVIEW_01.md)  
**Scope:** Specification only. Zero driver implementation, zero real-data execution, zero store access, zero graph decompression, zero asset downloads, zero live API calls, zero credential reading, zero data or manuscript edits.

---

## 1. Governance, Authorship & Three-Gate Execution Sequence

This document formalizes the technical specification for the offline preflight audit of the I4 matched-resource baseline. In strict compliance with Codex reviews (Review 01 and Review 02), project development and execution are segregated into three sequential, reviewable gates:

```
[ Gate A: Specification Freeze (R03) ]  <-- (Current Turn: Specification Refinement Only)
                   │
                   ▼
[ Gate B: Code-Only Driver Implementation + Synthetic Test Suite Audit ]
                   │
                   ▼
[ Gate C: Explicit User Authorization for Real-Data Preflight Execution ]
```

1. **Gate A (Current Turn):** Refinement and formal freeze of this technical specification. No driver code is executed or implemented, no files are downloaded, no stores are opened, and no compressed graph archives are decompressed.
2. **Gate B (Next Code Step):** Implementation of the standalone diagnostic driver (`scripts/matched_baseline/offline_preflight.py`) and a fully mocked synthetic test suite (`tests/test_offline_preflight_synthetic.py`) exercising 100% of the verification logic, error branches, and disposition outcomes (`PASS`, `FAIL`, and `BLOCKED`). Peer audit and verification by Codex.
3. **Gate C (Future Execution Step):** Only after Gate B receives explicit peer approval and the user provides explicit execution authorization will the driver be run against local data copies.

---

## 2. Store Protection & Complete Integrity Lifecycle Protocol

The original ChromaDB collection contains valuable experimental vector assets that must remain pristine. Under no circumstances may client initialization, SQLite connection, or schema migrations mutate the original store.

### 2.1 Complete Integrity Lifecycle Chain

```
[ Source Store ] ──(Quiescence Check + Manifest Before)
       │
       ▼ (Read-Only Copy)
[ Preserved Snapshot ] ──(Verify 100% Parity with Source Before)
       │
       ▼ (Working Copy)
[ Disposable Copy ] ──(Verify 100% Parity Before Chroma Client Binding)
       │
       ▼ (Client Operations: Diagnostic Querying Only)
[ Chroma Diagnostic Client ]
       │
       ▼ (Guaranteed Finally Block: Regardless of Outcome)
[ Post-Run Verification ]:
   ├── Source Store: Re-manifest After == Manifest Before (Zero Drift Required)
   ├── Preserved Snapshot: Re-manifest After == Manifest Before (Zero Drift Required)
   └── Disposable Copy: Record and Report Any SQLite WAL/Migration Mutations
```

1. **Source Quiescence Verification:** Prior to any file operations, the preflight process verifies that no background writers, indexing processes, or external locks are active on the target Chroma store directory (`dataset_20k_cap/vector_db_20k`).
2. **Pre-Copy Source Manifest:** Recursively walk the source Chroma store directory, computing file sizes and SHA-256 digests for all files into `chroma_source_manifest_before.json`.
3. **Preserved Snapshot Creation:** Perform a byte-exact copy of the entire directory into an immutable, read-only snapshot directory: `<run_dir>/chroma_preserved_snapshot/`. Compute `chroma_preserved_snapshot_manifest.json` and verify 100% byte-for-byte parity against the source store before proceeding.
4. **Disposable Working Copy:** Copy the preserved snapshot into an isolated working directory: `<run_dir>/chroma_disposable_copy/`. Verify 100% hash parity against the preserved snapshot prior to initializing any database client.
5. **Reparse Point & Symlink Containment:** All file traversal, hashing, and copy routines must strictly reject symlinks, junctions, reparse points, or path traversal escapes.
6. **Isolated Client Binding:** The diagnostic Chroma client binds strictly and exclusively to `<run_dir>/chroma_disposable_copy/`. Under no condition is a client initialized against the source store or the preserved snapshot.
7. **Guaranteed Finalization Lifecycle:** A guaranteed `finally` block executes regardless of normal completion, assertion failure, or uncaught exception:
   - **Source Store Integrity:** Compute `chroma_source_manifest_after.json` on the source store and assert exact byte-for-byte equality with `chroma_source_manifest_before.json`. Any drift triggers immediate `FAIL`.
   - **Preserved Snapshot Integrity:** Re-manifest `<run_dir>/chroma_preserved_snapshot/` and assert exact byte-for-byte equality with `chroma_preserved_snapshot_manifest.json`. Any drift triggers immediate `FAIL`.
   - **Disposable Copy Migration Reporting:** Chroma client startup or querying may perform legitimate internal SQLite WAL writes, journal lock files, or schema checks on the disposable copy. The specification **does not forbid** internal writes to the disposable copy (which would falsely fail a valid read-only client startup), but **mandates** that all file mutations, additions, or migrations observed on `chroma_disposable_copy/` between before and after are explicitly recorded, hashed, and detailed in `chroma_disposable_mutation_report.json`.
8. **Missing Checks Prevent PASS:** Any skipped, unperformed, or incomplete integrity verification step strictly prevents a `PASS` disposition.

### 2.2 Embedding Representation Binding & Explicit No-Download Guard

1. **Binding Approved Dense Representation (No Model Substitution):**
   - The approved dense retrieval arm strictly uses the existing **`sentence-transformers/all-MiniLM-L6-v2`** representation (384 dimensions, ChromaDB Euclidean $L_2$ index setting).
   - **Strict Prohibition:** No substitution with BAAI/bge-large-en-v1.5 or any alternative model is permitted. No re-embedding or rebuilding of vector collections is permitted.
   - The diagnostic client must bind directly to the copied collection's existing embedding function configuration and compatible local ONNX assets.
2. **Explicit No-Download Guard:**
   - Setting environment variables `TRANSFORMERS_OFFLINE=1` and `HF_HUB_OFFLINE=1` is necessary but **insufficient**, as ChromaDB's internal ONNX runtime download mechanism can independently attempt network downloads when resolving default embedding functions.
   - Preflight enforces an explicit local cache binding: assets must reside in the local ONNX cache directory (default: `C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx`, configurable via `--onnx-cache-dir`).
   - Prior to Chroma client initialization, the preflight script explicitly verifies the physical existence of required ONNX assets (`model.onnx`, `tokenizer.json`, `vocab.txt`, configuration files) on disk.
   - If any required asset is missing, or if an attempt to invoke a network downloader would occur, preflight immediately halts and emits status **`BLOCKED`**, detailing the exact missing local asset path.
3. **Externally Enforced Offline Prerequisite:**
   - Preflight mandates the presence of the externally enforced offline condition flag (`--enforced-offline-condition`) as established in Review 01, confirming network isolation before store interaction.

---

## 3. Exact Corpus Parity & Layered Representation Audit

Parity between Arm H (hybrid sparse + dense) and Arm T (graph traversal) cannot be established by aggregate document counts or character lengths. Document text equality must be mathematically byte-exact on a per-ID basis.

### 3.1 Per-ID Byte-Exact Text Parity
1. Documents extracted from the disposable Chroma store copy will be cross-referenced against sparse BM25 corpus documents:
   $$\forall d \in \text{Corpus}, \quad \text{SHA256}(\text{Text}_{\text{Dense}}(d)) == \text{SHA256}(\text{Text}_{\text{Sparse}}(d))$$
2. The audit records:
   - Total documents evaluated (expected: 20,000 cases).
   - Duplicate IDs detected (must be 0).
   - Missing IDs between stores (must be 0).
   - Per-ID SHA-256 match rate (must be 100%).
3. Any mismatch, omission, or unmapped ID results in status **`FAIL`**.

### 3.2 Dual Representation Layers
The audit independently evaluates and reports two distinct text layers:
- **Layer 1: Ingestion Retrieval Text:** Raw legal opinion text (truncated to 1,000 characters during ingestion) used for sparse BM25 indexing and dense embedding indexing.
- **Layer 2: Serializer Evidence Payload:** Formatted evidence text packaged into LLM prompts (including `snippet` up to 600 characters, `substantive_holding`, `procedural_trace`, `title`, `decision_date`, and `relation_context`).
- Both layers are checked independently for structural integrity, character limits, and deterministic formatting.

### 3.3 Authentic Graph File, Schema & Missingness Policy
1. **Authentic Derivative Path:** The candidate graph derivative is pinned to:
   - Archive Path: `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz` (strictly `.json.xz`, not `.gz`).
   - Recorded Provenance: `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json`.
   - Verified Checksum Manifest: `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256`.
2. **Status Disclosure & Pending Adoption Choice:**
   - `terra_eeg_index_20k_r30corr_v1.json.xz` is an audited, corrected derivative prepared for future prospective study use; it is **not** the historical evaluated graph.
   - Its adoption for prospective experimental use remains a **pending choice** awaiting explicit user and peer authorization.
3. **Zero Decompression Gate:** No decompression of the `.json.xz` archive will occur during specification freeze (Gate A) or driver coding (Gate B). In Gate C (if authorized), decompression will occur only via streaming read into an isolated scratch buffer without altering the archive.
4. **Authentic Keyed Schema:** Graph nodes are indexed by dictionary ID (`nodes[node_id]`). The audit validates node keys, directed edge relations (`CITES`, `OVERRULES`), and node attribute structures without assuming an invented schema.
5. **Frozen Missingness Policy:** Missing dates, jurisdictions, or holdings are audited and tallied against a frozen catalog missingness policy (reporting exact counts of absent fields) rather than silently dropping nodes or demanding artificial 100% field completeness that contradicts historical legal corpus realities.

---

## 4. Annotation Parity & Shared Evidence Charging

1. **Deterministic Relation Catalog:** Arm H and Arm T must draw from an identical, query-independent relation catalog and deterministic support excerpts.
2. **Unified Evidence Budget Charging:**
   - All substantive holdings, procedural traces, relation annotations, and case facts admitted into the prompt must be charged against the common **6,000-token evidence budget**.
   - The total prompt (including system prompt, query context, and admitted evidence) must pack within the common **7,000-token prompt budget**.
3. **Structural Ceiling vs Token Budget Distinction:**
   - The **35,000-character structural ceiling** applies specifically to Arm T's graph traversal representation (governing seed expansion and formatted structural character count).
   - The **6,000-token evidence ceiling** and **7,000-token prompt ceiling** apply equally and symmetrically to both Arm H and Arm T.

---

## 5. Full 350-Query Cohort & Dual-Route Feasibility Simulation

Rather than sampling an unrepresentative subset of queries, the offline preflight verifies packing feasibility across the entire **350-query evaluation cohort** (`terra_350_benchmark.json`).

### 5.1 Dual-Route Feasibility per Query (Zero Live Calls)
For every query $q \in \{1 \dots 350\}$, the preflight script evaluates prompt packing under two route envelopes without invoking any live router or relying on historical gold answer labels:
1. **EASY Envelope (Fast Path Simulation):**
   - Arm T: Direct seed extraction only (0-hop, `max_depth_override=0`, top-2 dense seeds).
   - Arm H: Top-100 RRF hybrid candidate retrieval.
2. **HARD Envelope (Deep Traversal Simulation):**
   - Arm T: Dual-directional graph traversal up to depth 2 (`max_depth=2`, `max_structural_chars=35000`, `max_graph_nodes=40`).
   - Arm H: Top-100 RRF hybrid candidate retrieval.

### 5.2 Multi-Role Prompt Templates & References Policy
Prompt packaging is validated across five distinct functional roles:
1. **Intent Router:** Fast route classification prompt (evaluating Pydantic schema constraints).
2. **Generator:** LLaMA 3.3 70B Instruct generation template (evaluating system prompt, query, and evidence packing within 7,000 tokens).
3. **Verifier:** Epistemic consistency check template (evaluating generator output verification).
4. **Judge 1 & Judge 2:** Evaluative scoring templates under the frozen rubric.
5. **References Policy:** References and citation lists are included only in accordance with frozen rubric guidelines and are explicitly charged against the evidence token budget.

### 5.3 Conservative Upper-Bound Judge Envelope & Tokenizer Context Interpretation
1. **Worst-Case 4,096-Token Answer Simulation:** Prior to live generation, the actual generator answer does not exist. Preflight packs judge prompts using a synthetic worst-case 4,096-token generator response.
2. **Judge Context Window Interpretation:**
   - **Critical Rule:** Measuring whether a judge prompt exceeds a judge endpoint's context limit requires evaluating token counts using the **judge endpoint's specific tokenizer and context interpretation**, not the generator tokenizer's token count.
   - Preflight verifies that under a maximum 4,096-token answer, the complete judge evaluation prompt fits within each judge's certified context window.

### 5.4 Empirical Distribution Reporting
Preflight compiles and records exact distribution statistics (min, median, p95, max) across all 350 queries for:
- Admitted evidence items vs. dropped items.
- Formatted evidence character counts and token counts.
- Total prompt token counts for Generator, Verifier, Judge 1, and Judge 2.
- Traversal structural characters for Arm T.

---

## 6. Prospective Cost Scheduling, Unset Budgets & Tokenizer Governance

### 6.1 Unset Spending Cap & Blocked Live Execution
1. **No Invented Financial Authorization:** The historical $100.00 figure is strictly an unapproved prototype/speculative default, **not** an authorized user spending ceiling.
2. **Spend Cap Status: `UNSET`:** The actual financial ceiling is marked as `UNSET`. Live execution remains strictly **`BLOCKED`** until official provider price schedules are verified and explicit user budget authorization is documented.
3. **Prospective Cost Modeling Only:** The preflight driver performs zero billable dispatches and zero live API calls. Its financial function is strictly prospective: modeling worst-case cost allocations across all 350 queries under dual routes.

### 6.2 Role-Specific Cost Manifest Inputs
The preflight manifest formally defines prospective cost parameters for every billable stage:
- **Router Role:** Unspecified candidate endpoint (input/output rates $/M tokens).
- **Generator Role:** LLaMA 3.3 70B Instruct candidate endpoint (`databricks-meta-llama-3-3-70b-instruct`).
- **Verifier Role:** Unspecified candidate endpoint.
- **Judge 1 Role:** Unspecified candidate endpoint.
- **Judge 2 Role:** Unspecified candidate endpoint.
- **Accounting Invariants:**
  - Every prospective billable attempt (including potential retries) must be modeled.
  - Conservative pre-dispatch reservation: full 4,096-token completion reserved in `CallLedger`.
  - Missing-Usage Policy: If a provider response lacks token usage metadata, the ledger charges the full 4,096-token completion reservation.

### 6.3 Pinned Tokenizer Governance & Asset Acquisition Gate
1. **Tokenizer Identity & Revision:**
   - Generator Tokenizer: `meta-llama/Llama-3.3-70B-Instruct` (pinned to official HuggingFace repository revision, chat template, BOS/EOS tokens, and special token behavior).
   - Do **not** guess expected SHA-256 hashes for absent files.
2. **Production Tokenizer Availability:**
   - Passing synthetic test suites in Gate B does **not** make `ProductionTokenizer` available.
   - If official tokenizer assets are absent from local cache, preflight terminates cleanly with status **`BLOCKED`**, reporting the exact repository revision and file list (`tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`) required for acquisition under a separately authorized gate. No automatic network downloads are permitted.

---

## 7. Operational Isolation, Disposition Semantics & Synthetic Verification

### 7.1 Collision-Proof Exclusive Directory Isolation
- Timestamps alone do not guarantee collision resistance. Preflight enforces atomic, exclusive directory creation (`mkdir` with `O_EXCL` semantics) using a timestamp plus random hex suffix:
  `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/preflight_run_<YYYYMMDD_HHMMSS>_<hex8>/`
- If the directory already exists, execution halts immediately with an error.

### 7.2 Run Directory Artifact Inventory
Each run directory produces an isolated, immutable record:
1. `preflight_config.json`: Pinned configuration, input manifest hashes, Python interpreter details, environment flags.
2. `chroma_source_manifest_before.json` & `chroma_source_manifest_after.json`.
3. `chroma_preserved_snapshot_manifest.json`.
4. `chroma_disposable_mutation_report.json`: Detailed log of any SQLite WAL/migration changes observed on the disposable copy.
5. `corpus_parity_manifest.json`: Per-ID text hash verification across all 20,000 cases.
6. `query_envelope_350_summary.json`: Distribution metrics across all 350 queries under both EASY and HARD envelopes.
7. `prospective_cost_estimate.json`: Detailed financial modeling across all stages and retries.
8. `preflight_final_report.md`: Human-readable audit report and disposition summary.

### 7.3 Strict Disposition Outcomes
- **`PASS`**: 
  - 100% per-ID text hash parity between dense and sparse stores across all 20,000 cases.
  - Zero byte drift on source store and zero byte drift on preserved snapshot.
  - All 350 queries successfully pack within token ceilings under both EASY and HARD envelopes.
  - All judge prompts fit within judge context windows under worst-case 4,096-token answer reservation.
  - Authentic graph schema verified; missingness policy satisfied.
- **`FAIL`**: Contract violation (e.g., text hash mismatch, token budget exceeded, source store byte drift, schema corruption).
- **`BLOCKED`**: Non-success disposition indicating a missing external prerequisite (e.g., offline tokenizer not cached, ONNX embedding model absent, spend cap unset, offline condition flag omitted).
  - **Important:** `BLOCKED` is **not** an exit 0 masquerading as successful completion; it emits a non-zero diagnostic exit code and halts the pipeline cleanly.

### 7.4 Gate B Synthetic Lifecycle Verification
Prior to any real-data execution authorization, Gate B requires implementing a comprehensive synthetic test suite (`tests/test_offline_preflight_synthetic.py`) covering:
- Clean `PASS` execution on mocked stores.
- Store drift detection and failure handling in `finally` block.
- Per-ID corpus text hash mismatch detection (`FAIL`).
- Token ceiling overflow handling (`FAIL`).
- Missing asset and offline enforcement interception (`BLOCKED`).
- Exclusive directory collision handling.

---

## 8. Summary of Revisions (R02 $\rightarrow$ R03)

| Correction Area | R02 State | R03 Corrected State | Governing Review Point |
| :--- | :--- | :--- | :--- |
| **1. Embedding Model Binding** | Speculatively named BAAI/bge-large-en-v1.5 | Strictly preserves existing `all-MiniLM-L6-v2` dense representation. Adds explicit no-download guard for Chroma ONNX runtime and offline condition requirement. | Review 02, Point 1 |
| **2. Financial Authorization** | Stated $100.00 USD global spending ceiling | Explicitly marks $100 as unapproved prototype default; marks spend cap `UNSET` and live mode `BLOCKED`. Driver role clarified as prospective estimation only. Candidate roles marked unspecified. | Review 02, Point 2 |
| **3. Authentic Graph Derivative** | Named `.json.gz` graph path | Corrected to `terra_eeg_index_20k_r30corr_v1.json.xz` with provenance and manifest. Formally disclosed as corrected derivative with pending adoption choice. | Review 02, Point 3 |
| **4. Complete Integrity Lifecycle** | Stated simple copy and before/after on copy | Added source quiescence, source $\rightarrow$ preserved snapshot $\rightarrow$ disposable copy parity chain, symlink containment, failure-proof finalization, disposable copy migration reporting, exclusive mkdir, and non-zero `BLOCKED` disposition. | Review 02, Point 4 |
| **5. Tokenizer & Multi-Role Prompts** | Generic packing check; generator tokenizer used | Pinned official revision identity without guessing hashes. Specified 5 call role templates and references policy. Enforced judge tokenizer context interpretation for conservative 4,096-token answer envelope. | Review 02, Point 5 |

---

## 9. Next Steps & Approval Workflow

1. **Submit Specification R03 (this document)** to Codex for peer review and alignment.
2. **Upon Codex Approval of Gate A:** Proceed to Gate B (code-only implementation of `scripts/matched_baseline/offline_preflight.py` and `tests/test_offline_preflight_synthetic.py`).
3. **No real-data access, store copying, or execution will occur until Gate B is fully audited and passed, and explicit Gate C authorization is granted by the user.**
