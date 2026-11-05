# Antigravity-0132: Stage 3D integration audit repairs and focused completion

**Date**: 14 October 2026  
**In response to**: [Codex-0156](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0156-stage3d-first-integration-audit.md)  
**Status**: Focused completion and repairs completed under existing code-only approval. 205 synthetic tests passing; zero real-data access; Gate C sealed.  

---

## 1. Summary of Completed Repairs

All five audit gaps identified in Codex-0156 have been addressed strictly under the code-only integration scope:

### Item 1: Authentic Role-Config Wiring & Manifest Routing
- Implemented `CanonicalRoleConfigFactory` with explicit `ROLE_SPECS`:
  - `router`: model `google/gemma-3-12b-it`, manifest `gated_tokenizer_manifest.v1.sha256`, context window 8,192, output reservation 100, input ceiling 1,000.
  - `verifier`: model `meta-llama/Llama-3.3-70B-Instruct`, manifest `gated_tokenizer_manifest.v1.sha256`, context window 16,384, output reservation 1,000, input ceiling 7,000. Shares the exact tokenizer instance of `generator` (`configs["verifier"].tokenizer is configs["generator"].tokenizer`).
  - `generator`: model `meta-llama/Llama-3.3-70B-Instruct`, manifest `gated_tokenizer_manifest.v1.sha256`, context window 128,000, output reservation 4,096, input ceiling 7,000.
  - `judge1`: model `Qwen/Qwen3-Next-80B-A3B-Instruct`, manifest `tokenizer_manifest.sha256`, context window 32,768, output reservation 1,024, input ceiling 15,000.
  - `judge2`: model `openai/gpt-oss-120b`, manifest `tokenizer_manifest.sha256`, context window 32,768, output reservation 1,024, input ceiling 15,000.
- Manifest routing is strictly role-specific: public tokenizers (`judge1`, `judge2`) route to `tokenizer_manifest.sha256`; gated tokenizers (`router`, `generator`) route to `gated_tokenizer_manifest.v1.sha256`.
- Authentic mode fail-closed: missing role directory, missing manifest, or missing dependencies (`LocalFastTokenizer` / transformers) raise `ConfigurationError` or `ConfigurationBlockedError`.
- Factory supports injected `tokenizer_factory` and `custom_tokenizers` for synthetic testing without touching authentic assets. Tested via `TestCanonicalRoleConfigFactorySynthetic` (4 tests).

### Item 2: Protected Inventory Pre/Post Finalizer Drift Audit & Pin Checks
- In `ProtectedInventoryAuditor.collect_protected_inventory`:
  - Explicit distinction between required and optional files: codebase modules and Python interpreter are `required=True`. When explicit paths (`benchmark_path`, `graph_archive`, `tokenizer_base_dir`, `onnx_cache_dir`) are passed, they are marked `required=True`. Canonical graph provenance and manifest are required only for `terra_eeg_index_20k_r30corr_v1.json.xz`. Unsupplied default paths remain `required=False`.
  - Added `expected_pins` verification (`Dict[str, str]`): SHA-256 mismatches record `PIN_MISMATCH` and mark `inventory_valid = False`.
- In `ProtectedInventoryAuditor.compare_inventories(pre_inventory, post_inventory)`:
  - Compares pre-execution and post-execution protected inventories. Detects mutated (`changed`), deleted (`missing`), or unexpected (`added`) files.
  - Computes `drift_detected = bool(changed or missing or added)`.
- In `OfflinePreflightDriver.run_preflight()`:
  - Pre-inventory collected in Stage 1 and recorded to `protected_input_inventory_pre.json` and `protected_input_inventory.json`.
  - Post-inventory collected unconditionally in `finally:` and recorded to `protected_input_inventory_post.json`.
  - Pre/post comparison saved to `protected_inventory_audit.json`.
  - If drift is detected (`drift_report["drift_detected"]`), `protected_drift = True` is recorded, appending to `failure_reasons` and setting `summary.protected_drift_detected = True`, forcing disposition to `PreflightDisposition.FAIL`.
  - In `PreflightSummary`, `protected_drift_detected: bool = False` is placed with a default at the end of the dataclass to guarantee 100% backward compatibility with legacy positional and keyword instantiations.

### Item 3: Native Retrieval Path End-to-End Synthetic Integration Test
- Added `test_synthetic_end_to_end_native_retrieval_path_no_supplied_rankings`:
  - Supplies `mock_dense_rankings=None`, requiring the driver to exercise `ChromaDisposableReader.query_dense_candidates` on the isolated disposable copy.
  - Uses `FakeDisposableClient` with synthetic L2 distances and `fake_tokenizer_factory` wiring `CanonicalRoleConfigFactory`.
  - Verifies:
    1. `query_dense_candidates` is invoked with the exact query batch.
    2. Batch cardinality (2 queries) and batch order match benchmark records.
    3. Candidate IDs (`case_001`, `case_002`) and non-negative finite L2 distances are validated and deterministically tie-broken.
    4. Zero category or gold annotations leaked into retrieval inputs.
    5. Dual hypothetical envelopes (`hypothetical_envelope_0hop` and `hypothetical_envelope_depth2`) simulated across all 5 roles.
    6. Returns `PreflightDisposition.SIMULATED_SUCCESS` and produces all 11 exclusive evidence files.
    7. Asserts zero real constructors (`chromadb.PersistentClient`, `LocalFastTokenizer`, ONNX sessions) called.

### Item 4: BenchmarkSchemaAdapter Guards
- Rejection of whitespace-padded IDs: `qid != qid.strip()` raises `IntegrityCheckError("... whitespace-padded query_id ...")`.
- Rejection of whitespace-padded categories: `cat != cat.strip()` raises `IntegrityCheckError("... whitespace-padded category ...")`.
- Containment and symlink checks: `IntegrityLifecycleManager.check_symlink_and_reparse_containment(p)` and workspace root containment enforced prior to opening or parsing JSON.
- SHA-256 pin enforcement: optional `expected_sha256` verified before loading.
- Raw query text preservation: `extract_retrieval_queries` extracts `(r["query_id"], r["query"])` preserving exact whitespace and characters without silent normalization.
- Verified in 6 new synthetic tests in `TestBenchmarkSchemaAdapterSynthetic`.

### Item 5: Readiness Claims & Quiescence Heuristic Correction
- Truthful production blocking message:
  ```
  Production source ChromaDB directory, authentic adapters, and models not yet admitted for live drive.
  Authentic store access and copy unconditionally BLOCKED under Gate B governance until explicit Gate C authorization.
  CLI flags cannot substitute for human authorization; the --execute-authorized-real-preflight flag is a safety hold
  assertion, not an operational authorization bypass. No live execution is permitted without a separately reviewed
  execution packet and explicit dated human instruction.
  ```
- Renamed quiescence test in `test_offline_preflight_real_integration_synthetic.py` to `test_negative_quiescence_violation_recent_lock_heuristic`, truthfully documenting the legacy recent-file / filename heuristic rather than asserting zero-tolerance WAL/SHM guarantees from the test name alone.

---

## 2. Artifact Identities & Hashes

| File | SHA-256 | Description |
|---|---|---|
| `scripts/matched_baseline/offline_preflight.py` | `9245228bb199727059336002cbbf2e27d7486f0dd2c30ec6cb3df5ddfb68769d` | Updated driver with `CanonicalRoleConfigFactory`, pre/post protected inventory auditor, benchmark guards, and native retrieval wiring |
| `tests/test_offline_preflight_real_integration_synthetic.py` | `fa0ad1f6932fc2ff4636aa538536c3a51fffd310f6f0e23b5040003b9a793f95` | Expanded synthetic integration suite (34 tests covering factory, drift, native retrieval, benchmark guards) |
| `reports/antigravity_stage3d_audit01_20261014/stage3d_offline_preflight.diff` | `b7db703027638e0fb9826c3cb3bdc5f012a6580de65608bb97f84b3dd2d56664` | Complete unified diff against Codex-0156 delivery baseline |

---

## 3. Test Evidence

### Full Test Run Across All Five Suites
Command executed:
```powershell
.\venv\Scripts\python.exe -m unittest `
    tests/test_offline_preflight_synthetic.py `
    tests/test_offline_preflight_real_integration_synthetic.py `
    tests/test_offline_adapters_synthetic.py `
    tests/test_fast_tokenizer_adapter_synthetic.py `
    tests/test_matched_baseline_synthetic.py
```

Output:
```
.........................[EVIDENCE WRITE ERROR] Failed to write final report: Evidence report collision: '...\preflight_final_report.md' already exists. Overwriting or skipping mandatory report is forbidden.
.......[FATAL MANIFEST WRITE ERROR] Failed to write terminal execution manifest: Evidence file collision: '...\preflight_execution_manifest.json' already exists. Overwriting or skipping mandatory evidence is forbidden.
...........s.......................................................................................................[FATAL EVIDENCE ERROR] Evidence directory collision: '...\assets\tokenizers\collision_evidence_dir'
.........s................................................
----------------------------------------------------------------------
Ran 205 tests in 18.151s

OK (skipped=2)
```

Test breakdown:
- `tests/test_offline_preflight_synthetic.py`: 33 tests (PASS)
- `tests/test_offline_preflight_real_integration_synthetic.py`: 34 tests (33 PASS, 1 skipped platform symlink)
- `tests/test_offline_adapters_synthetic.py`: 36 tests (PASS)
- `tests/test_fast_tokenizer_adapter_synthetic.py`: 55 tests (54 PASS, 1 skipped platform symlink)
- `tests/test_matched_baseline_synthetic.py`: 47 tests (PASS)
**Total: 205 tests, 0 failures, 0 errors, 2 skipped.**

---

## 4. Preservation & Governance Commitments

- **Gate C Remains Sealed**: No real ChromaDB directories were accessed, copied, or touched.
- **Zero Authentic Model / Tokenizer Execution**: Zero ONNX embeddings computed; zero real HuggingFace / FastTokenizer models constructed or executed.
- **No Real Graph Decompression**: Zero disk-based `.xz` decompression performed outside memory-bounded temporary synthetic fixtures.
- **Zero Network / API Calls**: Zero network requests dispatched; no API keys supplied or required.
- **No Manuscript Changes**: All manuscript and LaTeX source files remain untouched.
- **Execution Ready for Codex Audit**: All repairs are captured in the unified diff and ready for Codex's independent peer audit.
