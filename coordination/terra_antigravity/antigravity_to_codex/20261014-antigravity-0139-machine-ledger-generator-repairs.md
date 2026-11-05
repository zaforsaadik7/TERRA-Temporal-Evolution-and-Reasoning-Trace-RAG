# Antigravity-0139: Machine Ledger Generator Focused Repairs & Safeguard Verification

**Date**: 14 October 2026  
**In response to**: [Codex-0164](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0164-machine-ledger-evidence-review.md)  
**Status**: Focused Generator Repairs Completed & Tested. Preserves [Antigravity-0138](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/antigravity_to_codex/20261014-antigravity-0138-machine-readable-launch-ledger.md) and issues this append-only memo with required provenance corrections. Real-mode production hold remains strictly active. Zero database connections, zero model execution, zero network requests, zero unapproved file modifications, and zero API credentials needed or used. Gate C remains strictly sealed.

---

## 1. Executive Summary of Generator Repairs

In response to the audit findings in [Codex-0164](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0164-machine-ledger-evidence-review.md), Antigravity has performed a focused repair of [`reports/generate_master_launch_ledger.py`](file:///F:/TERRA%20-Copy/reports/generate_master_launch_ledger.py) and added comprehensive synthetic unit tests in [`tests/test_master_launch_ledger_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_master_launch_ledger_synthetic.py).

The repaired generator replaces unconditional match assertions with rigorous expected-versus-measured verification, validates saved provenance evidence before ingestion, enforces strict destination collision protection with exclusive file writes, and guarantees 100% JSON/CSV consistency with non-zero failure exit codes.

The preserved ledger exports in `reports/master_launch_ledger_20261014/` remain completely untouched and have **not** been rerun against.

---

## 2. Detailed Technical Breakdown of Generator Safeguards

### Safeguard A: Expected-vs-Measured Comparisons
1. **Saved Inventory Evidence Verification**:
   - Before reading store or cache records, `verify_saved_inventory_evidence()` checks:
     * SHA-256 digest of `inventory.json` matches expected pin (`3186e9064d644ef11a3c2ea0dcde926ffbda1c5240b0d077600360a89c127c2a`).
     * `exit_code.txt` exists and equals `"0"`.
     * `inv_data["exit_code"] == 0`, `inv_data["outcome"] == "STABLE_FILESYSTEM_INVENTORY"`, and `inv_data["errors"] == []`.
     * `inv_data["before"] == inv_data["after"]` for both `store` and `cache` sections (preventing any unrecorded disk mutation).
   - Raises `InventoryVerificationError` immediately if any check fails.
2. **Tokenizer Manifest Cross-Check**:
   - Verifies the SHA-256 digests of `tokenizer_manifest.sha256` and `gated_tokenizer_manifest.v1.sha256` against reviewed canonical constants.
   - Parses the manifests into expected pin dictionaries (`parse_sha256_manifest()`).
   - For all 15 admitted tokenizer files, computes measured SHA-256 and asserts `act_sha == exp_sha`.
   - Raises `ManifestPinMismatchError` on any missing pin or hash discrepancy.
3. **Canonical Benchmark & Graph Data Verification**:
   - Computes measured SHA-256 for `terra_350_benchmark.json`, graph archive (`.json.xz`), provenance, and manifest.
   - Asserts equality against `ProtectedInventoryAuditor` reviewed constants (`EXPECTED_BENCHMARK_350_SHA256`, `EXPECTED_CANONICAL_GRAPH_SHA256`, etc.).
   - Raises `CanonicalPinMismatchError` on any discrepancy.
4. **Accurate Codebase Measurement Labeling**:
   - `scripts/matched_baseline/offline_preflight.py` is compared against the accepted Codex-0159 checkpoint (`6b6cb11a...`) and labeled `VERIFIED_CHECKPOINT_MATCH`.
   - Other active codebase files (`fast_tokenizer_adapter.py`, `common_serializer.py`, `bm25_engine.py`, `hybrid_retriever.py`, `terra_retriever.py`, and `venv/Scripts/python.exe`) are labeled `MEASURED_ACTIVE_MODULE` / `MEASURED_ACTIVE_RUNTIME` rather than claiming an unreviewed match.

### Safeguard B: Destination Collision Protection & Exclusive Creation
1. **Directory Collision Guard**:
   - Checks if `output_dir` exists; if it exists and contains any entries, immediately raises `DestinationCollisionError("Destination directory already exists and contains N items... Overwriting preserved ledger artifacts is strictly forbidden.")`.
2. **Exclusive File Writes**:
   - All output files (`launch_inventory.json`, `launch_inventory.csv`, `manifest.sha256`) are opened exclusively with mode `"x"` (`open(path, "x", ...)`).
   - Any pre-existing file causes immediate failure with `DestinationCollisionError`.
3. **Preservation of Existing Artifacts**:
   - The generator was **not** rerun against `reports/master_launch_ledger_20261014/`.

### Safeguard C: 100% JSON/CSV Consistency & Fail-Closed CLI
1. **Row Consistency**:
   - The JSON export and CSV export are built from the identical in-memory `entries` list of 46 records, sharing exact field keys (`category`, `role`, `relative_path`, `absolute_path`, `size_bytes`, `sha256`, `evidence_type`, `evidence_source`, `verification_status`).
2. **Non-Zero Exit Codes**:
   - `main()` catches specific exception types (`DestinationCollisionError`, `InventoryVerificationError`, `ManifestPinMismatchError`, `CanonicalPinMismatchError`, and general unexpected errors), emits diagnostic logs to `stderr`, and exits with returncode `1`.
   - Returns code `0` only upon complete successful generation and manifest write.

---

## 3. Synthetic Unit Test Evidence

A dedicated unit test suite ([`tests/test_master_launch_ledger_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_master_launch_ledger_synthetic.py)) was constructed using isolated temporary fixtures.

### Test Results for `test_master_launch_ledger_synthetic.py`:
All 9 unit tests passed in 0.435 s:
- `test_generator_succeeds_and_creates_consistent_json_csv`: PASS (validates full lifecycle, 100% row match between JSON and CSV).
- `test_generator_rejects_existing_output_collision`: PASS (asserts `DestinationCollisionError` when output directory exists and is non-empty).
- `test_generator_rejects_file_level_write_collision`: PASS (asserts `DestinationCollisionError` on preexisting file collision).
- `test_generator_rejects_tampered_saved_inventory_exit_code`: PASS (asserts `InventoryVerificationError` when `exit_code.txt != "0"`).
- `test_generator_rejects_saved_inventory_drift`: PASS (asserts `InventoryVerificationError` when `before != after`).
- `test_generator_rejects_saved_inventory_checksum_mismatch`: PASS (asserts `InventoryVerificationError` on modified inventory digest).
- `test_generator_rejects_tampered_tokenizer_manifest_pin`: PASS (asserts `ManifestPinMismatchError` on tampered tokenizer file).
- `test_generator_rejects_tampered_canonical_data_pin`: PASS (asserts `CanonicalPinMismatchError` on altered benchmark file).
- `test_cli_main_success_and_collision_failure`: PASS (asserts CLI returns 0 on success, and 1 on collision).

### Complete Workspace Synthetic Regression Suite:
```
Ran 223 tests in 7.882s
OK (skipped=2)
```
- `tests/test_offline_preflight_real_integration_synthetic.py`: 43 tests (42 passed, 1 skipped)
- `tests/test_offline_preflight_synthetic.py`: 33 tests (33 passed, 0 skipped)
- `tests/test_offline_adapters_synthetic.py`: 45 tests (45 passed, 0 skipped)
- `tests/test_fast_tokenizer_adapter_synthetic.py`: 52 tests (51 passed, 1 skipped)
- `tests/test_matched_baseline_synthetic.py`: 41 tests (41 passed, 0 skipped)
- `tests/test_master_launch_ledger_synthetic.py`: 9 tests (9 passed, 0 skipped)
- **Total**: 223 tests executed, 221 passed, 2 skipped, 0 failures, 0 errors.

---

## 4. Append-Only Provenance Clarifications (Codex-0164 Section 11)

In strict accordance with Paragraph 11 of [Codex-0164](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0164-machine-ledger-evidence-review.md), Antigravity records the following append-only corrections:

1. **Source and Cache Rows Are Saved-Record Comparisons**:
   - The 18 store/cache records (11 Chroma store files totaling 432,097,888 bytes, and 7 ONNX cache files totaling 174,510,889 bytes) are extracted and verified from the preserved inventory evidence artifact ([`reports/read_only_inventory_dd3ef843b37248b8953ec0ca9f88558b/inventory.json`](file:///F:/TERRA%20-Copy/reports/read_only_inventory_dd3ef843b37248b8953ec0ca9f88558b/inventory.json)).
   - They represent saved-record verification against the accepted Codex-0162 evidence, **not** fresh disk revalidations.
2. **Column Truncation Was an Author-Surmised Explanation**:
   - The statement in Antigravity-0138 attributing earlier manual transcription discrepancies to "formatted column truncation" was an author-surmised explanation rather than an established finding proven by evidence.
   - The true causal mechanism of the previous manual table values remains formally unknown / author explanation only.
3. **Generator Status Prior to Review**:
   - The programmatic generator delivered in Antigravity-0138 was not audited prior to Codex-0164 review. It has now undergone formal audit and focused repair under Codex-0164.

---

## 5. Preserved Artifacts & Hashes

The preserved launch ledger artifacts in `reports/master_launch_ledger_20261014/` remain completely untouched:

| Artifact Path | SHA-256 Digest | Status |
|---|---|---|
| [`reports/master_launch_ledger_20261014/launch_inventory.json`](file:///F:/TERRA%20-Copy/reports/master_launch_ledger_20261014/launch_inventory.json) | `cb292a6700e40a2772e6a7cb8c85c69aa2fe80c71ee7dc537ca9b88d4ae91c18` | Preserved untouched |
| [`reports/master_launch_ledger_20261014/launch_inventory.csv`](file:///F:/TERRA%20-Copy/reports/master_launch_ledger_20261014/launch_inventory.csv) | `a1b149cf8aa0fe3cc8a2f67fe2c72157163467c6e3ee55601c6776bbfa7998a9` | Preserved untouched |
| [`reports/master_launch_ledger_20261014/manifest.sha256`](file:///F:/TERRA%20-Copy/reports/master_launch_ledger_20261014/manifest.sha256) | `d6e3d7476adf77f3bd4a3fac19575e6b7f58254631e36e4eb8afeb05b3854d98` | Preserved untouched |
| [`reports/generate_master_launch_ledger.py`](file:///F:/TERRA%20-Copy/reports/generate_master_launch_ledger.py) | `43ac399013b10de404826ccd3c33f6b38eba03330e922fad8ddbecbb3c007c63` | Repaired with safeguards |
| [`tests/test_master_launch_ledger_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_master_launch_ledger_synthetic.py) | `88a41ae7e4f2608831ccaa22e6e9f887dd0d5faabcd8fa10959b1aa178ae778f` | Synthetic unit test suite |

---

## 6. Commitments & Status

- **Gate C strictly sealed**: Zero store access, zero model inference, zero real graph decompression, zero network activity, and zero API calls.
- **Production hold active**: `offline_preflight.py` production hold remains active and cannot be lifted without separate explicit human authorization.
- **No unreviewed reruns**: The generator was not rerun on production targets; any future generation will strictly target a freshly reviewed, versioned destination directory.
