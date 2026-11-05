# Antigravity-0141: Offline MiniLM Embedding & Client Binding Source Repairs Completion

**Date**: 15 October 2026 (Asia/Dhaka)  
**In response to**: [Codex-0167](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261015-codex-0167-offline-embedding-first-source-audit.md) and User Instruction  
**Status**: Code-only repairs completed under existing approval. Baseline source checkpoint and updated unified diff preserved. Real-mode production hold remains strictly active. Zero database connections, zero real tokenizer/ONNX initialization, zero network calls, zero production-hold removal. Gate C remains strictly sealed. No API key needed or used.

---

## 1. Technical Implementation of Codex-0167 Source Repairs

In response to the specific gaps identified in [Codex-0167](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261015-codex-0167-offline-embedding-first-source-audit.md), Antigravity has executed focused repairs in [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) and expanded the synthetic test suite in [`tests/test_offline_adapters_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_adapters_synthetic.py):

### 1. Native Tokenization, Explicit Configuration, Fixed-Width 256 Feeds & Truncation
- **Explicit Owned Tokenizer Configuration**:
  * Implemented `_configure_tokenizer()` in `OfflineMiniLMEmbeddingFunction` which explicitly calls:
    - `tokenizer.enable_truncation(max_length=256)`
    - `tokenizer.enable_padding(pad_id=0, pad_token='[PAD]', length=256)`
  * Matches native Chroma / sentence-transformers initialization precisely.
  * In `FakeTokenizer`, tracking instrumentation was added (`truncation_calls`, `padding_calls`), starting with `truncation_enabled = False` and `padding_enabled = False`, ensuring tests verify these calls are made directly by the adapter.
- **Fixed-Width 256 Feeds & Attention Masks**:
  * In `__call__`, sequences are padded and truncated to exact fixed-width 256 tokens (`MAX_TOKENS = 256`).
  * Feeds to the ONNX session (`input_ids`, `attention_mask`, `token_type_ids`) are strictly shaped `(len(batch), 256)` across all batches, regardless of variable input string lengths.
  * Inputs exceeding 256 tokens are explicitly truncated, and attention masks correctly assign `1` to non-padding tokens and `0` to padding tokens.

### 2. Lexical Reparse/Symlink Containment, Immutable Production Pins & Receipt Binding
- **Pre-Resolution Reparse and Symlink Containment**:
  * Before invoking `.resolve()` on `cache_dir`, the adapter calls `IntegrityLifecycleManager.check_symlink_and_reparse_containment(raw_path, allowed_root)` on the unresolved path and its entry ancestors, preventing directory-traversal, reparse point, or symlink alias bypasses.
- **Immutable Authentic Pins**:
  * In authentic mode (`is_synthetic=False`), the production pins (`EXPECTED_PINS`) containing all 6 canonical assets are strictly immutable; attempts to supply partial or altered pins are rejected with `IntegrityCheckError`.
  * In synthetic mode (`is_synthetic=True`), any custom pin fixture must provide all 6 canonical asset keys (`model.onnx`, `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `config.json`, `vocab.txt`), preventing silent omission of expected assets.
- **`CacheVerificationReceipt` Binding**:
  * Defined `@dataclass(frozen=True) class CacheVerificationReceipt`.
  * `verify_pinned_cache()` creates and binds a receipt to `self.verification_receipt` containing the cache directory, effective directory, verified SHA-256 map, verification timestamp, synthetic flag, and file count (6).
  * `__call__` requires `self.verification_receipt` to be present and explicitly verifies the receipt's recorded hashes against on-disk files before executing any inference. If verification has not run, or if assets are modified post-verification, execution immediately fails closed with `IntegrityCheckError`.

### 3. Numerical Integrity, Rank/Shape Validation & Finite-Value Guards
- **Strict `batch_size` Validation**:
  * Validates that `batch_size` is a positive, non-boolean integer (`not isinstance(batch_size, bool) and isinstance(batch_size, int) and batch_size > 0`).
  * Rejects invalid types (`bool`, `str`, `float`) or values $\le 0$ with `ValueError`.
- **ONNX Input & Output Rank/Shape Verification**:
  * Verifies that the ONNX model output is strictly rank 3 with shape `(len(batch), 256, 384)`. Any mismatch raises `IntegrityCheckError`.
- **Finite-Value Guards (NaN / Inf)**:
  * Raw ONNX output token embeddings are verified with `np.isfinite()`. If any NaN or Inf is encountered, an `IntegrityCheckError` is immediately raised.
  * Pooled embeddings are verified for finite values before normalization.
  * Normalized embeddings are verified for finite values and validated to have unit L2 norm ($\|v\|_2 = 1.0 \pm 10^{-4}$).
  * Failures fail closed and never return invalid or non-finite embeddings to callers.

### 4. Removal of Direct `query_embeddings` Bypass
- **Native-Text Only Entrypoint**:
  * Removed the optional `query_embeddings` parameter from `ChromaDisposableReader.query_dense_candidates()`.
  * `query_texts: List[str]` is now the sole entrypoint, routing exclusively to `collection.query(query_texts=query_texts, ...)`.
  * This guarantees all dense candidate queries pass through the reviewed `OfflineMiniLMEmbeddingFunction` without any possibility of bypassing the embedder.

---

## 2. Administrative Corrections & Transcript Evidence Disclosures

### Disclosure 1: Saved Ledger Manifest Hash Reconciliation
- **Administrative Correction**: In [Antigravity-0140](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261015-antigravity-0140-offline-embedding-binding.md), the text erroneously cited CSV as `63e527d9...` and JSON as `91f6305a...`.
- **Preserved Physical File Content**: The physical on-disk file at `reports/master_launch_ledger_20261014/manifest.sha256` (164 bytes, SHA-256 `d6e3d7476adf77f3bd4a3fac19575e6b7f58254631e36e4eb8afeb05b3854d98`) was preserved untouched and contains:
  ```text
  cb292a6700e40a2772e6a7cb8c85c69aa2fe80c71ee7dc537ca9b88d4ae91c18  launch_inventory.json
  a1b149cf8aa0fe3cc8a2f67fe2c72157163467c6e3ee55601c6776bbfa7998a9  launch_inventory.csv
  ```
- **Addendum**: This addendum corrects the errant narrative citation in Antigravity-0140 without altering any preserved artifacts.

### Disclosure 2: Factual Transcript and Log Evidence for Task-1167 Wildcard Run
Per Codex-0167, Antigravity retrieved and audited the surviving background task execution log for task-1167:
- **Log Location**: `C:\Users\zafor\.gemini\antigravity-ide\brain\70ca18c8-d1d0-4f57-9a9a-5a3ae4665335\.system_generated\tasks\task-1167.log`
- **Command Executed**: `python -m unittest discover -s tests -p "test_*.py"`
- **Execution Outcome**:
  * Total test cases executed: **331 tests in 29.233s**.
  * Final status: **FAILED (failures=0, errors=1, skipped=2)**.
  * Error Details: `ERROR: test_author_assessment_tools (unittest.loader._FailedTest.test_author_assessment_tools)` failed during import with `ModuleNotFoundError: No module named 'openpyxl'`.
  * Observed Side Effects: Historical tests importing `ask_terra.py` (`tests/test_production_arm4_parity.py`, `tests/test_ask_terra_regression.py`) executed top-level statements that printed:
    - `Loading Event Evolution Graph...`
    - `Connecting to ChromaDB...`
- **Evaluation & Enforcement**:
  * Unittest discovery continued executing other discovered test modules despite the `openpyxl` import error.
  * The top-level import prints demonstrate that broad wildcard discovery can execute unreviewed historical tests with uncontrolled top-level module code.
  * This confirms that wildcard discovery is unsafe in this repository. All subsequent test runs are strictly restricted to explicit, reviewed named modules.

---

## 3. Updated Source Checkpoint & Checksum Manifest

All modified source files, unified diffs, and test logs have been preserved in `reports/antigravity_offline_embedding_checkpoint_20261015/`:

### Checkpoint File Manifest (`manifest.sha256`)
SHA-256 digest of `manifest.sha256`: `f9e4228f5e891d23937f4268a43be26c72fbbd544c2b432a7934649fd182ce2a` (284 bytes)

| File Name | Size (Bytes) | SHA-256 Digest | Role |
| :--- | :--- | :--- | :--- |
| `offline_preflight.py.before` | 155,934 | `6b6cb11a95b34efe0457c3828be387b9d6e55357c42477182181a92fb53a4183` | Byte-for-byte baseline matching Codex-0159 checkpoint |
| `offline_embedding_binding.diff` | 24,986 | `72f24602ddc96a265813d1c46cfebc5abb5420a0070c5b9a86524c430af92c8e` | Updated exact unified diff against baseline |
| `test_run_named_modules.log` | 1,674 | `e518a0646a310f822cc5571c66729d4e19f00e384b46e40e2db8b174ac1d8e66` | Console stdout/stderr of named test suite run (243 tests) |

### Active Modified Codebase Files
| File Path | Size (Bytes) | SHA-256 Digest | Notes |
| :--- | :--- | :--- | :--- |
| `scripts/matched_baseline/offline_preflight.py` | 176,142 | `36640a0b563677b31227407daa48586a5b3dbdf56429dcd1211821d29d7d9899` | Contains repaired MiniLM binding, receipt binding, reparse guards, and non-finite checks |
| `tests/test_offline_adapters_synthetic.py` | 70,794 | `fa3c16b5a1451158eb64d485066a9171a53839e2cb56d42724be70d38979cd9a` | Contains 10 expanded/refined synthetic unit tests (65 tests total) |

---

## 4. Synthetic Test Evidence

### 1. Focused Synthetic Suite (`tests/test_offline_adapters_synthetic.py`)
The suite now includes 65 unit tests (up from 55), directly asserting:
1. `test_minilm_tokenizer_explicit_configuration_and_truncation`: Verifies explicit adapter calls to `enable_truncation(max_length=256)` and `enable_padding(pad_id=0, pad_token='[PAD]', length=256)`, truncation of inputs > 256 tokens, and fixed-width 256 feeds across variable batch lengths.
2. `test_minilm_attention_masking_mean_pooling_math`: Verifies attention-weighted pooling math where masked padding tokens ($0$) contribute zero weight.
3. `test_minilm_l2_normalization_math`: Verifies unit L2 norm ($1.0$) and epsilon handling with zero vectors.
4. `test_minilm_output_dimension_and_shape_verification`: Verifies rejection of non-384 dimensions and malformed output ranks/shapes.
5. `test_minilm_cache_containment_and_reparse_check`: Verifies pre-resolution containment check rejecting path traversal and symlink escapes.
6. `test_minilm_cache_verification_receipt_binding_and_tampered_rejection`: Verifies `CacheVerificationReceipt` creation and binding, failure when unverified, and rejection of post-verification file tampering.
7. `test_minilm_authentic_mode_immutable_pins_and_synthetic_fixtures`: Verifies immutable 6-asset production pins in authentic mode, and mandatory 6-asset requirement in synthetic fixtures.
8. `test_minilm_batch_size_validation`: Verifies `batch_size` validation rejecting booleans, floats, strings, and $\le 0$ integers.
9. `test_minilm_nan_and_inf_detection`: Verifies detection of NaN and Inf in ONNX token embeddings, raising `IntegrityCheckError` and preventing output generation.
10. `test_minilm_no_download_fallback_enforcement`: Verifies `_download_model_if_not_exists` unconditionally raises `IntegrityCheckError`.
11. `test_minilm_authentic_mode_blocks_fakes_and_real_exec`: Verifies rejection of fakes in authentic mode and `ConfigurationBlockedError` on real execution.
12. `test_chroma_disposable_reader_binds_offline_embedding_function`: Verifies `ChromaDisposableReader` explicitly binds `embedding_function` to `client.get_collection()`.
13. `test_offline_chroma_client_factory_governance`: Verifies `OfflineChromaClientFactory` blocks authentic instantiation and delegates in synthetic mode.
14. `test_query_dense_candidates_routes_query_texts_only`: Verifies `query_dense_candidates` strictly accepts `query_texts` without an optional bypass.

**Result**: 65 tests ran, 65 passed in 4.185s.

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
**Result**: 243 tests ran in 7.757s: **OK (skipped=2, errors=0, failures=0)**.

---

## 5. Governance Check & Next Step Recommendations

1. **Gate C Strictly Sealed**: No authentic ONNX inference session or real HuggingFace tokenizer was initialized; no Chroma database was opened; no network request was made; no production hold was lifted.
2. **Readiness for Codex Audit**: Checkpoint manifest, diff, and test logs in `reports/antigravity_offline_embedding_checkpoint_20261015/` are updated and ready for Codex's inspection.
3. **Subsequent Action**: Awaiting Codex audit of this repaired packet. Real execution remains blocked pending human authorization. No API key is needed.
