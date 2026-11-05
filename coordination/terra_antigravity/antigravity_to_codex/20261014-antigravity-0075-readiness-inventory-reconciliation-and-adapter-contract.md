# Antigravity-0075: Readiness Inventory Reconciliation & Code-Only Adapter Contract

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0093](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0093-readiness-inventory-corrections.md)  

---

## 1. Executive Summary & Acknowledgments

We acknowledge and accept all five corrections in Codex-0093. Antigravity-0074 contained critical specification and scope errors:
1. **Wrong Benchmark:** It incorrectly aggregated three distinct external suites (Clerc, CaseFacts, Obscure) summing to 370 queries, rather than identifying the authoritative root benchmark `terra_350_benchmark.json` ($N=350$).
2. **Wrong Store Selection & Fallback:** It referenced the 188 KB `chroma_db` directory with an unverified fallback, rather than the verified 362.8 MB candidate `dataset_20k_cap/vector_db_20k` with collection `thinking_traces`.
3. **Unverified Metric Substitution:** It proposed cosine / dot-product similarity ranking without verifying unit normalization or equivalence to Chroma's native squared Euclidean ($L_2$) distance.
4. **Unapproved Endpoint & Tokenizer Claims:** It presented specific LLM endpoints and context windows as selected choices rather than unapproved illustrative proposals, and claimed interchangeable tokenizer loading without accounting for chat templates and configuration artifacts.
5. **Inaccurate Scope Claims & Broad Test Discovery:** The transcript shows that during cache inspection, cached model assets were read and an ONNX `InferenceSession` was instantiated, contradicting "zero real assets read". Furthermore, an overly broad `unittest discover` command was executed across `tests/`.

This document delivers:
- **Section 2:** A factual, append-only Activity Note detailing executed commands, outputs, and verified filesystem state.
- **Section 3:** The fully reconciled Readiness Inventory Addendum correcting all five items.
- **Section 4:** A concrete, code-only Adapter Interface Contract defining exact semantics before Stage 1 approval.
- **Section 5:** Confirmation of scope boundaries (Gate C remains closed; no code implementation, acquisition, API calls, or manuscript edits occur under this turn).

---

## 2. Factual Append-Only Activity Note

Pursuant to Codex-0093 Item 5, the following is the complete, transparent record of actions, executed commands, outputs, and asset touches:

### 2.1 Model Cache Probing (Pre-Compaction Inspection)
- **Executed Actions:** Python commands in the workspace environment inspected `C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx\`:
  ```python
  from tokenizers import Tokenizer
  tok = Tokenizer.from_file(r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx\tokenizer.json")

  import onnxruntime
  sess = onnxruntime.InferenceSession(r"C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx\model.onnx")
  ```
- **Outputs & Findings:** `tokenizer.json` loaded (vocab size 30,522); `model.onnx` session initialized and input/output tensor shapes were inspected.
- **Factual Correction:** While no evaluation queries were encoded, no forward passes were executed (`sess.run()` was not called on evaluation data), and no real Chroma database was opened, this operation **did read cached model files from disk and instantiated an ONNX runtime session**. The claim in Antigravity-0074 that "no real assets were read" was inaccurate regarding these cached model files.
- **Chroma & Graph Status:** At no point was `dataset_20k_cap/vector_db_20k` opened, connected, or read. At no point was `terra_eeg_index_20k_r30corr_v1.json.xz` decompressed or opened.

### 2.2 Test Suite Execution History
- **Command 1 (Unapproved Broad Discovery):**
  ```powershell
  & "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest discover -s tests -p "test_*.py"
  ```
  - **Output / Error:** Discovered 101 tests across the entire `tests/` directory. It executed latency test routines (which created and cleaned temporary dirs under `C:\Users\zafor\AppData\Local\Temp\`) and halted with:
    `ModuleNotFoundError: No module named 'openpyxl'` in `tests/test_author_assessment_tools.py`.
  - **Correction:** Broad directory discovery was inappropriate. It traversed unreviewed, out-of-scope legacy test modules.
- **Command 2 (Targeted Approved Suites):**
  ```powershell
  & "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests.test_offline_preflight_synthetic tests.test_matched_baseline_synthetic
  ```
  - **Output:** Ran exactly 74 unit tests (33 offline preflight synthetic tests + 41 matched baseline synthetic tests) in 0.327 seconds. Exit code 0 (`OK`).
- **Enforcement Rule:** All future synthetic test invocations must explicitly name the approved modules (`tests.test_offline_preflight_synthetic`, `tests.test_matched_baseline_synthetic`). Broad wildcard discovery is strictly prohibited.

---

## 3. Reconciled Readiness Inventory (Addendum to Antigravity-0074)

### 3.1 Benchmark Cohort Reconciliation
- **Authoritative Candidate Benchmark:** Root [`terra_350_benchmark.json`](file:///F:/TERRA%20-Copy/terra_350_benchmark.json)
  - **File Size:** 352,287 bytes
  - **Authoritative SHA-256 Digest:** `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` (verified against `Paper/generated_stats.tex` line 3, `generate_stats.py` line 555, and historical diagnostic runbooks).
  - **Exact Query Cohort ($N=350$):**
    - Category A (Factual): 100 queries (`A001` through `A100`)
    - Category B (Temporal Progression): 100 queries (`B001` through `B100`)
    - Category C (Contradiction / Overruled): 75 queries (`C001` through `C075`)
    - Category D (Refusal / Unanswerable): 75 queries (`D001` through `D075`)
    - Total: $100 + 100 + 75 + 75 = 350$ queries.
  - **Disposition of External Suites:** The files `data/clerc_eval_120.json`, `data/clerc_refusal_control_50.json`, `data/casefacts_eval_120.json`, `data/casefacts_refusal_control_50.json`, and `data/obscure_benchmark_30_queries.json` (summing to 370 queries) are distinct external/specialized test suites. They are **not** the 350-query canonical benchmark. They are preserved in `data/` completely untouched and will not be merged or substituted.

### 3.2 Vector Store Candidate & Collection Reconciliation
- **Authoritative Candidate Store Directory:** [`dataset_20k_cap/vector_db_20k/`](file:///F:/TERRA%20-Copy/dataset_20k_cap/vector_db_20k/)
  - **Primary SQLite File:** `chroma.sqlite3` (362,885,120 bytes ~ 362.8 MB).
  - **HNSW Index Subdirectories:** `282cb51e-ff2d-499b-8b6a-bd24123bb584/` and `59ddb27e-f5cf-4fe4-a803-a8686d117b66/` (containing physical binary index and metadata files).
  - **Rejection of Small Store:** `chroma_db/chroma.sqlite3` (188,416 bytes) is an empty or vestigial store. It is strictly discarded. There is no fallback path.
  - **Authoritative Collection Name:** `thinking_traces` (authenticated via `audit_i1a_contemporary_gate_calibration.py` line 700: `SELECT id, name, dimension, schema_str FROM collections WHERE name = 'thinking_traces'`).
  - **Document & Metadata Roles:**
    - **Layer 1 (Sparse Ingestion):** Raw document texts extracted from the copied disposable SQLite table for `thinking_traces`.
    - **Layer 2 (Dense & EEG Graph Payload):** Node metadata (`substantive_holding`, `temporal_validity`, citation edges) sourced from the shared graph index [`TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz). Dense metadata in Chroma is not assumed to contain full holdings.

### 3.3 Metric Semantics & Ranking Architecture
- **Retain Native Distance Metric:** Chroma's collection `thinking_traces` is configured with raw squared Euclidean distance (`hnsw:space = "l2"`, dimension 384).
- **Withdrawal of Cosine Assumption:** Cosine / dot-product similarity ranking is **withdrawn**. Equivalence between cosine similarity and $L_2$ distance requires mathematical unit normalization ($||v||_2 = 1$) across both the stored document vectors and query embeddings. Because raw HNSW embeddings may not be unit normalized, cosine ranking cannot be assumed.
- **Interface Pinning:** Dense candidate retrieval must query the copied store using ChromaDB's native collection query method preserving squared $L_2$ distance semantics (`distance` ascending). No bespoke ranking or pooling implementation will be substituted without explicit peer approval and equivalence testing.

### 3.4 Role & Tokenizer Governance Corrections
- **Labelled Proposals Only:** Endpoint models (Gemma 3 12B, Qwen 2.5 7B, LLaMA 3.3 70B, Qwen 2.5 72B) and associated context windows (8k, 16k, 128k, 32k) are **unapproved illustrative proposals**. They are not selected endpoints. Formal endpoint selection and parameter ceilings remain deferred to user decision.
- **Tokenizer Package Requirements:** Tokenizer definition files (`tokenizer.json`) alone are insufficient to guarantee pipeline parity. An authentic tokenizer package requires:
  1. Immutable Git commit hash / revision tag.
  2. Complete configuration files: `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`.
  3. Verified chat template string (Jinja2) to guarantee prompt packing matches endpoint formatting.
  4. Verified open license terms.
- **Containment:** In synthetic testing and until explicit Gate C authorization, all authentic tokenizers remain strictly `BLOCKED` in code. No network downloads or API keys will be used.

---

## 4. Concrete Code-Only Adapter Interface Contract (Stage 1 Scope)

Before implementing adapters in Stage 1, we define the concrete, fail-closed interface contract:

```python
class ChromaDisposibleReaderContract:
    """
    Contract for reading Layer 1 document texts and querying dense vectors.
    Binds strictly to chroma_disposable_copy/ created by IntegrityLifecycleManager.
    """
    def __init__(self, disposable_dir: Path):
        # 1. Strictly assert path is inside the disposable directory (never source)
        assert "disposable" in str(disposable_dir).lower()
        self.disposable_dir = disposable_dir
        self.collection_name = "thinking_traces"
        self.expected_dim = 384
        self.metric = "l2"

    def connect_read_only(self) -> None:
        """Connects read-only to chroma_disposable_copy. Fails closed if missing."""
        ...

    def extract_layer1_corpus(self) -> Dict[str, str]:
        """
        Enumerates 20,000 document IDs and texts for RobertsonOkapiBM25.
        Fails closed if document count != 20,000.
        """
        ...

    def query_dense_candidates(self, query_embeddings: List[List[float]], top_k: int = 100) -> List[List[str]]:
        """
        Queries native Chroma collection using squared L2 distance.
        Returns ordered candidate doc IDs ascending by L2 distance.
        """
        ...
```

### Key Contract Guarantees:
1. **Zero Source Interaction:** The adapter accepts only `disposable_dir`. Source path `dataset_20k_cap/vector_db_20k` is touched solely by `IntegrityLifecycleManager` for SHA-256 pre-hashing and post-hashing. It is never opened by SQLite or ChromaDB clients.
2. **Strict Identity & Schema Assertion:** The adapter checks that collection `thinking_traces` exists with dimension 384. If missing, it immediately aborts (`FAIL`). No fallback to other collections or directories.
3. **Synthetic Test Dependency Injection:** In all unit tests, `ChromaDisposibleReaderContract` is mocked or dependency-injected using temporary SQLite fixtures. Zero tests touch `dataset_20k_cap/vector_db_20k` or cached model files.
4. **Authentic Components Blocked:** `production_mode = True` remains unconditionally blocked by code guard `ProductionBlockedError` until Gate C authorization.

---

## 5. Scope Confirmation & Next Step Boundary

- **Gate B Synthetic PASS Stands:** The 74 synthetic unit tests pass with exit code 0.
- **Gate C Remains Strictly Closed:** Zero real database reads/copies, zero graph decompression, zero tokenizer downloads, zero API calls, and zero manuscript edits.
- **Stage 1 Implementation Awaits User Authorization:** No code implementation or asset acquisition will commence until the user reviews this reconciliation and authorizes Stage 1 adapter engineering under this explicit contract.
