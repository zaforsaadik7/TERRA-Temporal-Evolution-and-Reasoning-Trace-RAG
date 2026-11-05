# Stage 3D Offline Preflight Code-Only Integration and Synthetic Test Delivery

**Memo ID**: `20261014-antigravity-0131-stage3d-integration-completed`  
**Date**: 14 October 2026  
**From**: Antigravity (Implementation Peer)  
**To**: Codex (Implementation Lead / Audit Peer)  
**Relayed By**: Human User  
**Status**: Code-only integration and synthetic testing completed; awaiting Codex peer audit. Gate C sealed.

---

## 1. Governance, Authority, and Binding Constraints

1. **Governing Scope**:
   - Authorized strictly under `coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0154-integration-plan-conditional-code-scope.md` and `20261014-codex-0155-new-chat-resume-handoff.md`.
   - Scope is strictly code-only implementation and named synthetic integration testing.
2. **Strict Invariants Preserved**:
   - **Gate C Remains Sealed**: No real ChromaDB store opening, copying, or access.
   - **Zero Graph Extraction**: No real citation graph `.xz` decompression on disk.
   - **Zero Real Models / Tokenizers**: No authentic tokenizer initialization, no ONNX model execution, no sentence-transformer embeddings. Mock tokenizers and synthetic data structures used exclusively in tests.
   - **Zero Network / API Calls**: No downloads, no credential reads, no external services.
   - **No Editorial / Data Changes**: No modifications to manuscripts, statistics, datasets, or historical reports.

---

## 2. Baseline Recovery & Preservation Manifest

Before applying modifications, the interrupted baseline state was audited and preserved:

- **Original `offline_preflight.py` SHA-256**:
  `AD53E9145F1AA3A8F29B52EDA271878C0E81F5950D95841773F4C074DB57359A`  
  (Matches Codex-0155 inventory bit-for-bit).
- **Preserved Pre-edit Checkpoint**:
  - Script copy: [`reports/antigravity_stage3d_resume_20261014_02/offline_preflight.py`](file:///F:/TERRA%20-Copy/reports/antigravity_stage3d_resume_20261014_02/offline_preflight.py)
  - Manifest: [`reports/antigravity_stage3d_resume_20261014_02/manifest.sha256`](file:///F:/TERRA%20-Copy/reports/antigravity_stage3d_resume_20261014_02/manifest.sha256)
  - Unified diff: [`reports/antigravity_stage3d_resume_20261014_02/stage3d_offline_preflight.diff`](file:///F:/TERRA%20-Copy/reports/antigravity_stage3d_resume_20261014_02/stage3d_offline_preflight.diff)

---

## 3. Reconciled Code Changes in `scripts/matched_baseline/offline_preflight.py`

### A. Resolution of Duplicate / Shadowed Class Definitions
1. **`ProtectedInventoryAuditor`**:
   - Replaced duplicate implementations (previously at lines 618 and 1191) with a single, unified implementation at Section 1B.
   - Replaced rigid 28-item fixed-count assertions with dynamic, role-aware discovery of executed codebase modules, tokenizer manifests/assets, graph archive/provenance/manifest, benchmark files, ONNX cache assets, and the Python interpreter binary.
   - Generates structured, immutable `protected_input_inventory.json` completely separated from runtime output manifests (`run_dir_manifest.sha256`).
2. **`StreamingGraphArchiveLoader`**:
   - Reconciled duplicate implementation to cleanly delegate to the audited [`BoundedMemoryGraphLoader`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py), honoring uncompressed byte limits (250 MB ceiling), node count limits (25,000 max), decoder memory limits, duplicate JSON key rejections, and graph schema audits.

### B. Precedence in Corpus Parity Audit (Stage 3)
- Fixed precedence in `run_preflight()`: when synthetic mock fixtures (`mock_dense_corpus` / `mock_sparse_corpus`) are explicitly supplied, they take precedence over auto-instantiated `disposable_reader`. This enables synthetic test harnesses (such as store drift tampers) to execute deterministically without triggering phantom store reads.

### C. `BenchmarkSchemaAdapter` Integration (Stage 5)
- Wired `BenchmarkSchemaAdapter.validate_and_load()` to validate root benchmark schemas (`query_id`, `query`, `category`) and ensure exact category distribution:
  - `A_Factual`: 100
  - `B_Evolutionary`: 100
  - `C_OutOfContext`: 75
  - `D_Adversarial`: 75
  - Total queries: 350
- Enforced zero-leakage query extraction (`extract_retrieval_queries()` yields only `(query_id, query)` tuples; `category`, gold, and target fields are strictly isolated from retrieval/routing inputs).

### D. Dual Hypothetical Route Envelopes & Formatting Parity
- Replaced runtime route naming with dual hypothetical evaluation envelopes:
  - `hypothetical_envelope_0hop` (Arm T top 2 seeds, 0-hop)
  - `hypothetical_envelope_depth2` (Arm T top 40 candidates, depth-2)
- Explicitly documented in schema and summaries that these represent dual hypothetical evaluation envelopes, not observed runtime router decisions.
- Enforced exact 5-character separator literal (`\n---\n`) for inter-document evidence boundaries matching `TerraRetriever` conventions.

### E. CLI Options & Truthful Fail-Closed Production Guard
- Added CLI arguments: `--benchmark-path`, `--tokenizer-base-dir`, and explicit `--execute-authorized-real-preflight`.
- Reaffirmed truthful `--production` blocking: production mode unconditionally halts and returns `BLOCKED` under Gate B governance until explicit human Gate C authorization is recorded.

---

## 4. Synthetic Integration Test Suite Delivery

A new, comprehensive synthetic integration test suite was created at:
[`tests/test_offline_preflight_real_integration_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_preflight_real_integration_synthetic.py)

Contains 17 test cases across 5 test classes:
1. **`TestBenchmarkSchemaAdapterSynthetic`**:
   - `test_valid_benchmark_350_structure_and_counts`: Verifies authentic 350-item schema and category counts.
   - `test_extract_retrieval_queries_zero_category_leakage`: Proves category and target fields are stripped.
   - `test_negative_missing_required_keys`: Rejects records missing `query_id`, `query`, or `category`.
   - `test_negative_empty_or_whitespace_query`: Rejects blank query text.
   - `test_negative_duplicate_query_id`: Rejects collision in query identifiers.
   - `test_negative_unauthorized_category_label`: Rejects unexpected category tags.
   - `test_negative_category_count_skew`: Rejects cohorts deviating from 100/100/75/75 counts.
2. **`TestProtectedInventoryAuditorSynthetic`**:
   - `test_dynamic_asset_enumeration_and_ledger_separation`: Validates dynamic collection, SHA-256 recording, and separation from run artifacts.
   - `test_hash_file_sha256_deterministic`: Validates byte-accurate SHA-256 calculation.
3. **`TestStreamingGraphArchiveLoaderSynthetic`**:
   - `test_valid_streaming_graph_archive_load`: Verifies stream decompression and schema audit without disk extraction.
   - `test_negative_non_xz_extension_rejected`: Verifies non-`.json.xz` files fail closed.
   - `test_negative_dangling_edge_fails_closed`: Verifies schema audit detects dangling edge targets.
4. **`TestDualHypotheticalRouteEnvelopesSynthetic`**:
   - `test_route_envelope_naming_and_token_fit`: Verifies simulation records `hypothetical_envelope_0hop` and `hypothetical_envelope_depth2`.
   - `test_literal_separator_five_characters`: Validates 5-character literal `\n---\n`.
5. **`TestEndToEndRealIntegrationSyntheticDriver`**:
   - `test_synthetic_end_to_end_driver_execution_simulated_success`: End-to-end run under synthetic mocks returns `SIMULATED_SUCCESS`.
   - `test_negative_production_mode_unconditionally_blocked`: Proves `--production` flag without Gate C approval returns `BLOCKED`.
   - `test_negative_quiescence_violation_wal_shm_zero_tolerance`: Proves active SQLite WAL/SHM locks raise quiescence violation.

---

## 5. Execution Environment & Test Verification Evidence

- **Interpreter**: `F:\TERRA -Copy\venv\Scripts\python.exe`
- **Python Version**: `3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]`
- **Platform**: `Windows-10-10.0.19045-SP0`

### Test Suite Execution Results

| Test Suite | Tests Run | Result | Duration | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `tests/test_offline_preflight_real_integration_synthetic.py` | 17 | **OK** | 0.227s | All 17 new Stage 3D integration tests pass |
| `tests/test_offline_preflight_synthetic.py` | 33 | **OK** | 2.885s | All 33 legacy preflight tests pass (0 failures) |
| `tests/test_offline_adapters_synthetic.py` | 45 | **OK** | 3.441s | All 45 adapter tests pass |
| `tests/test_fast_tokenizer_adapter_synthetic.py` | 52 | **OK (skipped=1)** | 0.596s | 51 pass, 1 skipped (tokenizer model absent) |
| `tests/test_matched_baseline_synthetic.py` | 41 | **OK** | 0.112s | All 41 baseline tests pass |

---

## 6. SHA-256 Cryptographic Inventory

| File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `scripts/matched_baseline/offline_preflight.py` | `7ACE68D3DC1797407C458BD8FD56D9894E7FD7EF03C24D4C14DFBBE6244CC9E1` | Modified (Stage 3D integrated) |
| `tests/test_offline_preflight_real_integration_synthetic.py` | `6E5D7C28C0A45E08CD9E2E00AAEF1E4180A0F50168548D5D5730EF555881824C` | New (17 synthetic tests) |
| `tests/test_offline_preflight_synthetic.py` | `60F2BF4D953635A7E8DBA7D87A4A91C6B6027CDFC1A7F700B8F8B14C93367469` | Unchanged / Intact |
| `reports/antigravity_stage3d_resume_20261014_02/offline_preflight.py` | `AD53E9145F1AA3A8F29B52EDA271878C0E81F5950D95841773F4C074DB57359A` | Baseline backup snapshot |
| `reports/antigravity_stage3d_resume_20261014_02/stage3d_offline_preflight.diff` | `1762ECEB71E4EE01DFF3B806DA2247BEA499DB271DF2969DEC442F61F912C693` | Exact unified diff |

---

## 7. Known Limitations & Unimplemented Scope

1. **Gate C Sealed**: The production preflight execution against real data (`dataset_20k_cap/vector_db_20k`, real citation graph, and authentic tokenizer instances) is deliberately **NOT** executed.
2. **Context Window Ceilings Provisional**: Token limits are prospective assumptions configured for simulation and require verification when live endpoints are authorized.
3. **Serving Provider Formatting Parity**: Gated and public role tokenizers have verified local files and schemas, but hosted endpoint serving templates remain unverified until endpoint credentials/access are approved.
4. **No Code PASS Claimed**: Unit and synthetic test passes verify structural correctness, interface wiring, and fail-closed security properties. Final code acceptance belongs to Codex's independent audit.

---

## 8. Governance Handoff & Next Approval Boundary

Antigravity has completed the code-only integration and synthetic test requirements authorized under Codex-0154 and Codex-0155.

**Stopping Point**: We pause at this checkpoint for Codex's independent audit of the modified source, exact diffs, test logs, and hashes. No further execution or progression to Gate C will occur without explicit dated user instruction.
