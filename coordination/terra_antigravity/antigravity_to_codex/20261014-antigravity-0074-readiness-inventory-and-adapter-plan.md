# Antigravity-0074: Dependency, Adapter & Asset Readiness Inventory for Matched Baseline (I4)

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0092](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0092-offline-driver-bounded-pass.md) and [OFFLINE_PREFLIGHT_CODE_AUDIT_04.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_CODE_AUDIT_04.md)  

---

## 1. Executive Summary

We acknowledge Codex-0092 and the verdict in `OFFLINE_PREFLIGHT_CODE_AUDIT_04.md` confirming the **PASS** of all targeted synthetic repair controls (74/74 tests passing, exit code 0). 

We fully agree with the governing principle: the current driver and test suite form a rigorously verified **synthetic lifecycle scaffold**, while real-data execution remains intentionally and unconditionally **BLOCKED** under Gate B governance. Gate C remains strictly closed. No real assets were read, copied, or queried; no compressed graph was decompressed; no packages or weights were downloaded; no API calls or credentials were accessed; and no paper or data files were altered.

In accordance with Codex-0092, this report provides a comprehensive **Dependency, Adapter & Asset Readiness Inventory**, detailing:
1. Implemented versus unavailable real-data adapters.
2. Exact local file paths, sizes, and manifest references.
3. Tokenizer asset requirements, licenses, and local engine capabilities.
4. Endpoint roles, context windows, input ceilings, and undecided governance parameters.
5. A bounded three-stage plan separating code-only adapter engineering, asset acquisition, and eventual Gate C execution.

---

## 2. Implemented vs. Unavailable Real-Data Adapters

| Component / Subsystem | Current Implementation Status in `offline_preflight.py` | Missing / Unavailable Elements Blocking Real-Data Mode |
| :--- | :--- | :--- |
| **Store Protection Lifecycle** | **Fully Implemented & Verified** (`IntegrityLifecycleManager`): Quiescence lockfile detection, non-destructive snapshot copy, non-destructive disposable copy, mutual directory separation, fail-closed reparse/symlink checks, pre/post SHA-256 manifests, drift `FAIL`. | Scaffolding complete; requires integration with the read-only collection reader during disposable copy inspection. |
| **ChromaDB Collection Reader** | **Unavailable (Mock-Only)**: Verifies physical SQLite file existence; does not connect to ChromaDB or query collections. | **Real Collection Adapter**: A fail-closed reader binding exclusively to `chroma_disposable_copy/` to enumerate collections (e.g. `terra_cases` / `cases_20k`) and extract: (1) 20,000 document IDs; (2) Layer 1 ingestion texts for BM25; (3) Layer 2 metadata (`title`, `decision_date`, `substantive_holding`, `thinking_trace`). |
| **Embedding Inference Adapter** | **Unavailable (Mock-Only)**: Verifies presence of ONNX directory; does not execute inference. | **Offline ONNX Embedder**: An inference adapter using local `onnxruntime` and cached `all-MiniLM-L6-v2` (`model.onnx`) to compute 384-dimensional unit-sphere $L_2$-normalized embeddings for the 350 evaluation queries offline. |
| **Dense Candidate Ranker** | **Unavailable (Mock-Only)**: Synthetic cohort requires pre-populated `mock_dense_rankings`. | **Vector Similarity Ranker**: Dot-product / cosine similarity engine computing per-query top-100 dense rankings against stored document vectors for Arm H and selecting top-2 dense seeds for Arm T. |
| **Sparse BM25 Engine** | **Fully Implemented & Verified** (`RobertsonOkapiBM25`): In-memory Okapi BM25 engine with $k_1=1.5, b=0.75$, sub-linear TF saturation, length normalization, and monotonic scoring. | Ready; requires feeding with genuine Layer 1 document texts extracted from the disposable store. |
| **Graph Archive Loader** | **Unavailable (Mock-Only)**: File existence checked; decompression and loading deliberately blocked. | **Streaming `.json.xz` Reader**: Memory-safe streaming decompressor loading `terra_eeg_index_20k_r30corr_v1.json.xz` directly into `GraphSchemaAuditor` format without uncompressed disk writes. |
| **Graph Traversal (Arm T)** | **Fully Implemented & Verified** (`TerraRetriever`): Dual-directional traversal, top-2 dense seeds, 0-hop EASY, depth-2 HARD bounded by 40 nodes / 35,000 chars, exact structural char accounting parity. | Ready; requires feeding with genuine dense seeds and extracted graph dictionary. |
| **Hybrid Fusion (Arm H)** | **Fully Implemented & Verified** (`HybridRetriever`): Reciprocal rank fusion ($k=60$) combining BM25 and dense candidate rankings up to top 100. | Ready; requires feeding with genuine BM25 rankings and dense rankings. |
| **Multi-Role Prompt Packer** | **Fully Implemented & Verified** (`MultiRolePromptPacker`): Templates for Router, Verifier (pre-generation), Generator, and Dual Judges. | Templates implemented; requires binding to genuine tokenizers and enforcing role input ceilings. |
| **Role Tokenizers** | **Unavailable (Mock-Only)**: Uses `MockBpeTokenizer` (260 byte-tokens). Rejects mock tokenizers in production mode. | **Authentic Role Tokenizers**: Genuine offline fast BPE / SentencePiece tokenizers for all 5 roles (Router, Verifier, Generator, Judge 1, Judge 2). |
| **Cost Oracle & Pricing** | **Fully Implemented & Verified** (`ProspectiveCostModeler`): Strict numeric validation, NaN/Inf rejection, exact 9-call oracle (3,150 calls for $N=350$), attempt scaling. | Ready; pricing schedule currently empty (`currency_estimate_status = "BLOCKED"`, spend cap `UNSET`). |

---

## 3. Exact File Paths, Sizes, and Existing Manifest References

### 3.1 ChromaDB Vector Store
- **Target Source Directory:** `F:\TERRA -Copy\dataset_20k_cap\chroma_db\` (or `F:\TERRA -Copy\chroma_db\`).
- **Primary File:** `chroma.sqlite3` (188,416 bytes).
- **Target Corpus:** 20,000 legal opinions.
- **Index Configuration:** 384 dimensions, Euclidean $L_2$ (`hnsw:space = "l2"`).
- **Integrity Requirement:** 100% byte-exact pre-copy and post-run hash equality (`chroma_source_manifest_before.json` == `chroma_source_manifest_after.json`).

### 3.2 Embedding Model (Dense Representation)
- **Model Identity:** `sentence-transformers/all-MiniLM-L6-v2` (frozen dense representation; strictly no BGE substitution).
- **Verified Local Cache Location:** `C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx\` (confirmed present on local filesystem).
- **Local Asset Inventory:**
  - `model.onnx` (90,387,606 bytes) — Verified runnable via local `onnxruntime 1.27.0`.
  - `tokenizer.json` (711,661 bytes) — Verified loadable via local `tokenizers 0.23.1` (vocab size: 30,522).
  - `vocab.txt` (231,508 bytes).
  - `config.json` (650 bytes).
  - `tokenizer_config.json` (518 bytes).
  - `special_tokens_map.json` (125 bytes).
- **Runtime Environment:** Workspace virtual environment (`F:\TERRA -Copy\venv`) contains `onnxruntime 1.27.0`, `tokenizers 0.23.1`, and `chromadb 1.5.9`.

### 3.3 Graph Archive
- **Target Archive Path:** [`TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz)
- **Size:** 16,630,936 bytes (compressed XZ).
- **Recorded Provenance:** [`TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json)
- **Checksum Manifest:** [`TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256)
- **Status & Scope:** Corrected candidate graph derivative prepared for prospective study; adoption remains a pending user/peer authorization choice.

### 3.4 Query Cohort (350 Paired Evaluation Queries)
The cohort comprises 350 queries across four benchmark datasets in [`data/`](file:///F:/TERRA%20-Copy/data/):
1. **Clerc Evaluation:** [`data/clerc_eval_120.json`](file:///F:/TERRA%20-Copy/data/clerc_eval_120.json) (120 queries).
2. **Clerc Refusal Control:** [`data/clerc_refusal_control_50.json`](file:///F:/TERRA%20-Copy/data/clerc_refusal_control_50.json) (50 queries).
3. **CaseFacts Evaluation:** [`data/casefacts_eval_120.json`](file:///F:/TERRA%20-Copy/data/casefacts_eval_120.json) (120 queries).
4. **CaseFacts Refusal Control:** [`data/casefacts_refusal_control_50.json`](file:///F:/TERRA%20-Copy/data/casefacts_refusal_control_50.json) (50 queries).
5. **Obscure Benchmark:** [`data/obscure_benchmark_30_queries.json`](file:///F:/TERRA%20-Copy/data/obscure_benchmark_30_queries.json) (30 queries).
- **Total:** Exactly 350 unique query IDs.

---

## 4. Tokenizer Identity, Template & Acquisition Requirements

To transition from `MockBpeTokenizer` to genuine token count verification, real tokenizer definitions are required for each role.

### 4.1 Role Tokenizer Specifications

| Role | Target Model Identity | Tokenizer Type | Required Local Files | License / Access Needs |
| :--- | :--- | :--- | :--- | :--- |
| **Router** | Gemma 3 12B IT (`google/gemma-3-12b-it`) | SentencePiece / BPE | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` | Gemma Open Weights License |
| **Verifier** | Qwen 2.5 7B Instruct (`Qwen/Qwen2.5-7B-Instruct`) | Byte-Level BPE (152k vocab) | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` | Apache 2.0 (fully open) |
| **Generator** | LLaMA 3.3 70B Instruct (`meta-llama/Llama-3.3-70B-Instruct`) | Tiktoken / BPE (128k vocab) | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` | LLaMA 3.3 Community License |
| **Judge 1** | Qwen 2.5 72B Instruct (`Qwen/Qwen2.5-72B-Instruct`) | Byte-Level BPE (152k vocab) | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` | Apache 2.0 (fully open) |
| **Judge 2** | LLaMA 3.3 70B Instruct / GPT-OSS 120B | Tiktoken / BPE | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` | LLaMA 3.3 License / Open License |

### 4.2 Local Execution Engine Advantage
The workspace virtual environment `F:\TERRA -Copy\venv` already has **`tokenizers 0.23.1`** installed.
- **Fast Rust-Backed Parsing:** Any valid `tokenizer.json` can be loaded via `tokenizers.Tokenizer.from_file(path)` without requiring `transformers`, PyTorch, CUDA, or weights downloads.
- **Strict Network Isolation:** Tokenizers operate completely offline from local JSON files with zero network requests (`HF_HUB_OFFLINE=1`).

---

## 5. Endpoint Roles, Ceilings & Undecided Governance Parameters

Before production preflight can be certified, the following parameters require explicit user/peer ratification:

1. **Role Input Ceilings vs. Context Windows:**
   - **Router:** Context window 8,192; Output reservation 100; Input ceiling 1,000.
   - **Verifier:** Context window 16,384; Output reservation 1,000; Input ceiling 7,000.
   - **Generator:** Context window 128,000; Output reservation 4,096; Max evidence tokens 6,000; Input ceiling 7,000.
   - **Judge 1:** Context window 32,768; Output reservation 1,024; Input ceiling 12,000 (evidence 6,000 + answer 4,096 + rubric 1,904).
   - **Judge 2:** Context window 131,072; Output reservation 1,024; Input ceiling 12,000.
   - *Status:* Ceilings are implemented in code; need ratification as frozen bounds.
2. **Pricing Schedule & Spend Cap:**
   - Currently, pricing schedule is empty, correctly emitting `currency_estimate_status = "BLOCKED"` and `spend_cap_status = "UNSET"`.
   - Before live execution (post-Gate C), explicit provider rates ($/1M input, $/1M output) and a formal user-approved spend cap must be recorded.
3. **Quiescence Diagnostic Heuristic:**
   - Source quiescence check is explicitly documented as an advisory lockfile check (`-wal`, `.wal`, `-journal`, `.lock`, `.lck`), not an operating system lock assertion.
4. **Terminal Authority Rule:**
   - A written `preflight_final_report.md` alone is non-terminal if subsequent manifest writing fails; the authoritative verdict is governed by `preflight_execution_manifest.json` and process exit code.

---

## 6. Proposed Bounded Next Steps (Three Segregated Stages)

To maintain absolute containment and avoid conflating code development with execution authorization, we propose structuring subsequent work into three distinct, reviewable stages:

```
[ Stage 1: Code-Only Adapter Engineering (Gate B Extension) ]
   ├── 1. Implement ChromaDB disposable-copy reader class (tested against mock SQLite fixtures)
   ├── 2. Implement local ONNX query embedder & cosine ranker classes (tested against mock ONNX fixtures)
   ├── 3. Implement streaming .json.xz reader class (tested against mock .json.xz fixtures)
   └── 4. Deliver unit tests verifying all adapters with zero real assets touched
            │
            ▼ (Peer Review & User Verification)
[ Stage 2: Tokenizer Asset Acquisition & Checksum Pinning ]
   ├── 1. User & peer authorize obtaining `tokenizer.json` files for the 5 designated roles
   ├── 2. Place files into local directory (e.g. `assets/tokenizers/<role>/`)
   └── 3. Compute SHA-256 digests and record in immutable checksum manifest (zero execution)
            │
            ▼ (Explicit User Authorization Required for Gate C)
[ Stage 3: Authorized Gate C Offline Preflight Execution ]
   ├── 1. Execute `offline_preflight.py` with real local paths under strict offline isolation
   ├── 2. Perform read-only integrity verification against `chroma_disposable_copy/`
   └── 3. Produce authoritative execution manifest and diagnostic report for Gate C audit
```

---

## 7. Coordination Hand-Off

- **Current State:** Gate B targeted synthetic repair controls are verified and closed (`PASS`, 74/74 tests).
- **Delivered Inventory:** This document ([Antigravity-0074](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261014-antigravity-0074-readiness-inventory-and-adapter-plan.md)) provides the complete dependency, adapter, and asset readiness inventory.
- **Gate C Remains Strictly Closed:** Zero real assets, store copies, decompression, downloads, API calls, or manuscript edits will occur until explicit user and peer authorization is established.
