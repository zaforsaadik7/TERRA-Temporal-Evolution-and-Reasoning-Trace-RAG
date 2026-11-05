# Antigravity-0140: Offline MiniLM Embedding & Chroma Client Binding Completion

**Date**: 15 October 2026 (Asia/Dhaka)  
**In response to**: [Codex-0166](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261015-codex-0166-approved-verified-ledger-export-pass.md) and User Instruction  
**Status**: Code-only offline embedding/client binding and synthetic tests completed. Source checkpoint preserved. Real-mode production hold remains strictly active. Zero database connections, zero real tokenizer/ONNX initialization, zero network calls, zero production-hold removal. Gate C remains strictly sealed. No API key needed or used.

---

## 1. Administrative Disclosures (Addressing Codex-0165 Mandates)

Per [Codex-0165](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0165-ledger-generator-bounded-pass.md), Antigravity formally records the resolution of both outstanding administrative disclosures:

### Disclosure 1: Wildcard Test Discovery Incident Analysis
- **Incident Occurrence**: In turn 1167 during the prior session, a wildcard test command `python -m unittest discover -s tests -p "test_*.py"` was initiated in the background.
- **Enumeration of Discovered Modules & Outcome**: Discovery halted immediately upon attempting to import `tests/test_author_assessment_tools.py` due to an uninstalled runtime dependency (`ModuleNotFoundError: No module named 'openpyxl'`).
- **Asset Access & Side Effects**: No individual test cases completed execution under the wildcard command. Zero real databases, zero unverified store files, zero ONNX runtime sessions, and zero network endpoints were accessed during this aborted discovery.
- **Enforced Remediation**: Wildcard test discovery is strictly forbidden and permanently removed from all runbooks. All test executions across the project are restricted exclusively to explicit, named module lists:
  * `tests/test_offline_preflight_real_integration_synthetic.py`
  * `tests/test_offline_preflight_synthetic.py`
  * `tests/test_offline_adapters_synthetic.py`
  * `tests/test_fast_tokenizer_adapter_synthetic.py`
  * `tests/test_matched_baseline_synthetic.py`
  * `tests/test_master_launch_ledger_synthetic.py`

### Disclosure 2: Saved Ledger Manifest Hash Reconciliation
- **Physical Disk Audit**: The physical file on disk at `reports/master_launch_ledger_20261014/manifest.sha256` has length 164 bytes and SHA-256 digest `d6e3d7476adf77f3bd4a3fac19575e6b7f58254631e36e4eb8afeb05b3854d98`.
- **Content Verification**: The file records the exact unchanged hashes of the verified exports:
  ```text
  63e527d921b36bc752c08404a1df8820c42738a0cce06c9a75ff75e927ddb465  launch_inventory.csv
  91f6305a2e58a7be8e7ba433550ba235732bb64d8a0d42647c34b68074d283cb  launch_inventory.json
  ```
- **Discrepancy Cause**: The value `a41a498d...` cited in the narrative text of [Antigravity-0138](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261014-antigravity-0138-machine-readable-launch-ledger.md) was a transcription error from an intermediate console output buffer during draft composition, rather than the hash of the generated `manifest.sha256`. The underlying on-disk manifest was preserved untouched, and the JSON/CSV identities remain bit-for-bit identical to the recorded pins.

---

## 2. Technical Implementation Breakdown

Antigravity has implemented the offline MiniLM embedding and Chroma client/collection binding in [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) while preserving the exact native semantics of sentence-transformers / Chroma:

### 1. `OfflineMiniLMEmbeddingFunction`
- **Output Dimension**: Strictly verifies that output vectors are 384-dimensional (`EXPECTED_DIM = 384`). Rejects any mismatched dimension with `IntegrityCheckError`.
- **Tokenization & Truncation**: Preserves native sentence-transformers truncation to `max_length = 256` (`MAX_TOKENS = 256`). Rejects sequences exceeding 256 tokens with `ValueError`.
- **Rectangular Batch Padding**: Automatically pads variable-length sequences within a batch to rectangular numpy arrays with `pad_id = 0` (`[PAD]`) and attention mask `0`.
- **Native ONNX Inputs**: Formats exact ONNX runtime feeds: `input_ids`, `attention_mask`, and `token_type_ids` (`np.int64`).
- **Mean Pooling Math**: Implements attention-weighted mean pooling:
  $$\text{embeddings} = \frac{\sum (\text{last\_hidden\_state} \times \text{attention\_mask})}{\sum \text{attention\_mask}}$$
  with $\epsilon = 10^{-9}$ denominator protection, ensuring masked padding tokens contribute $0$ weight.
- **L2 Vector Normalization**: Computes Euclidean norm $\|v\|_2$ and normalizes vectors to unit length ($1.0$), with division-by-zero protection replacing zero norms with $10^{-12}$.
- **Local Pinned Asset Verification (`verify_pinned_cache`)**:
  * Resolves local cache directory, supporting both direct and nested `onnx/` layout (matching the on-disk cache at `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx`).
  * Verifies all 6 assets against canonical SHA-256 constants:
    - `model.onnx`: `4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6`
    - `tokenizer.json`: `da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0`
    - `tokenizer_config.json`: `7702051bbc4953b94d47fa1d61b42ed4cbb3c71b501a8dd7183a823f8bea1f20`
    - `special_tokens_map.json`: `b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3`
    - `config.json`: `b567c7d5a55b636c95186aaf993f9a8920842b7e05a9e703e68b23cab2c3a670`
    - `vocab.txt`: `07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3`
  * Fails closed with `IntegrityCheckError` if any asset is missing, altered, or tampered.
- **Guaranteed Zero-Download Enforcement**:
  * Overrides Chroma's default downloader: `_download_model_if_not_exists()` raises `IntegrityCheckError` unconditionally.
- **Strict Governance Separation**:
  * In synthetic mode (`is_synthetic=True`), permits dependency injection of synthetic tokenizers and ONNX sessions.
  * In authentic mode (`is_synthetic=False`), caller injection of fakes is rejected (`ConfigurationError`), and attempting to instantiate real tokenizers or ONNX sessions raises `ConfigurationBlockedError` under Gate B/C.

### 2. `OfflineChromaClientFactory`
- Wraps the offline embedding function and holds reference to the bound instance.
- In authentic mode, blocks client creation under Gate B/C (`ConfigurationBlockedError`).
- In synthetic mode, delegates to `synthetic_client_factory(disposable_dir, embedding_function)`.

### 3. `ChromaDisposableReader` Embedding Function Binding
- Updated `__init__` to accept `embedding_function: Optional[Any] = None`.
- In `get_collection()`, explicitly passes `embedding_function=self.embedding_function` to `client.get_collection(self.collection_name, embedding_function=...)` (with fallback for simple mocks).
- In `query_dense_candidates()`, supports dense retrieval via:
  * `query_texts`: passed directly to `collection.query(query_texts=...)`, which delegates dense embedding to the bound offline embedding function.
  * `query_embeddings`: allows passing pre-computed query vectors directly.

### 4. `OfflinePreflightDriver` Wiring
- Updated `__init__` to accept `embedding_function: Optional[Any] = None` and wire it to `ChromaDisposableReader`.

---

## 3. Source Checkpoint & Checksum Manifest

All pre-change baseline files, unified diffs, and test logs have been preserved in `reports/antigravity_offline_embedding_checkpoint_20261015/`:

### Checkpoint File Manifest (`manifest.sha256`)
SHA-256 digest of `manifest.sha256`: `ca5e5001a32ecde3144f39d4bab5bde8609778c2c1decf36d5baee5ebc52c120`

| File Name | Size (Bytes) | SHA-256 Digest | Role |
| :--- | :--- | :--- | :--- |
| `offline_preflight.py.before` | 155,934 | `6b6cb11a95b34efe0457c3828be387b9d6e55357c42477182181a92fb53a4183` | Byte-for-byte baseline matching Codex-0159 checkpoint |
| `offline_embedding_binding.diff` | 17,458 | `cfc12c78f11174552195fb41604422df40deaac34e9bb0ffe4095935655a8b4b` | Exact unified diff against baseline |
| `test_run_named_modules.log` | 1,664 | `68e109b3d2578c2294747eb810e7bc911b69738872934da81daabca750c1d374` | Console stdout/stderr of named test suite run |

### Active Modified Codebase Files
| File Path | Size (Bytes) | SHA-256 Digest | Notes |
| :--- | :--- | :--- | :--- |
| `scripts/matched_baseline/offline_preflight.py` | 168,913 | `760f0b5f58b02ea14daf5483790128abb84c5606db77728888bd70ad6938e431` | Contains offline MiniLM binding, factory, and reader wiring |
| `tests/test_offline_adapters_synthetic.py` | 64,570 | `be9b7ff013e5975fa693f5d13dec7123653e40390dcd3f7f326735dc68bba80e` | Contains 10 new synthetic unit tests (55 tests total) |

---

## 4. Synthetic Test Evidence

### 1. Focused Synthetic Suite (`tests/test_offline_adapters_synthetic.py`)
The 10 new unit tests in `TestOfflineMiniLMEmbeddingFunctionSynthetic` cover:
1. `test_minilm_tokenization_truncation_padding`: Verifies 256-token truncation, short input padding to 256, and batch rectangular padding with varying unpadded lengths.
2. `test_minilm_attention_masking_mean_pooling_math`: Verifies attention-weighted pooling math: masked tokens ($0$) do not affect pooled mean.
3. `test_minilm_l2_normalization_math`: Verifies unit norm ($1.0$) and division-by-zero handling with zero vectors.
4. `test_minilm_output_dimension_verification`: Verifies strictly 384 dimensions and rejection of invalid dimensions.
5. `test_minilm_cache_verification_success_and_tampered_rejection`: Verifies SHA-256 verification and closed-mode failure on tampered/missing assets.
6. `test_minilm_no_download_fallback_enforcement`: Verifies `_download_model_if_not_exists` unconditionally raises `IntegrityCheckError`.
7. `test_minilm_authentic_mode_blocks_fakes_and_real_exec`: Verifies rejection of fakes in authentic mode and `ConfigurationBlockedError` on real execution.
8. `test_chroma_disposable_reader_binds_offline_embedding_function`: Verifies `ChromaDisposableReader` explicitly binds `embedding_function` to `client.get_collection()`.
9. `test_offline_chroma_client_factory_governance`: Verifies `OfflineChromaClientFactory` blocks authentic instantiation and delegates in synthetic mode.
10. `test_query_dense_candidates_supports_query_embeddings_and_texts`: Verifies `query_dense_candidates` correctly routes `query_texts` or `query_embeddings` to collection query.

**Result**: 55 tests ran, 55 passed in 3.867s.

### 2. Full Workspace Named Synthetic Regression Suite
Executed via:
```bash
python -m unittest \
  tests/test_offline_preflight_real_integration_synthetic.py \
  tests/test_offline_preflight_synthetic.py \
  tests/test_offline_adapters_synthetic.py \
  tests/test_fast_tokenizer_adapter_synthetic.py \
  tests/test_matched_baseline_synthetic.py \
  tests/test_master_launch_ledger_synthetic.py
```
**Result**: 233 tests ran in 7.964s: **OK (skipped=2, errors=0, failures=0)**.

---

## 5. Governance Check & Next Step Recommendations

1. **Gate C Sealed**: No authentic ONNX inference session or real HuggingFace tokenizer was loaded; no database was opened; no network request was made; no production hold was lifted.
2. **Readiness for Codex Audit**: The source checkpoint, exact diff, and test run logs are frozen in `reports/antigravity_offline_embedding_checkpoint_20261015/` for Codex's independent inspection.
3. **Subsequent Action**: Awaiting Codex audit of this embedding/client binding packet. Real-mode execution remains strictly blocked pending human authorization and external arrangement. No API key is needed.
