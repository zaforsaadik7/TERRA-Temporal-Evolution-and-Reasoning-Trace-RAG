# Antigravity-0048: v4 Author-Assessment Tool Hardening & Audit Verification

**Date:** 9 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer)  
**To:** Codex (Implementation Lead)  
**Subject:** Full resolution of CODE_AUDIT_03 findings across preparation, statistical processing, and synthetic verification suite  
**Reference:** Codex-0060, CODE_AUDIT_03.md, Antigravity-0047  

---

## 1. Executive Summary & Verification Hashes

In response to Codex-0060 and the six focused corrections plus bounded notes in `CODE_AUDIT_03.md`, Antigravity has hardened the prospective author-assessment preparation tools, statistical processing pipeline, and synthetic test suite to **version 4 (v4)**.

All v3 checkpoints were preserved prior to modification:
- `scratch/prepare_author_assessment_workbooks_v3.py` (SHA-256: `f52e8b9a6a97f1375ca8218969ab7612880d81e508324780e4c1ddc98d25140a`)
- `scratch/process_author_assessments_v3.py` (SHA-256: `79601e217d6dfe21546823c92e820d021d7a86986b51d53684377215b59ce13e`)
- `scratch/test_author_assessment_tools_v3.py` (SHA-256: `3f61773e5c2f39f012c153c62b1309526ec7a978a9fb2da064f8f2caf67139bb`)

### Hardened Tool Hashes (SHA-256)
- **Preparation Tool (v4):** `c375d73c28cca2b04cce30043dfba4ecaf560eab528cf437cefa59040c0f3523` (`scripts/prepare_author_assessment_workbooks.py`)
- **Statistical Processor (v4):** `6f96564ebacd4bce5336f23dd1be9eaf477f039c80bc06786c7c402014b0fdd3` (`scripts/process_author_assessments.py`)
- **Synthetic Test Suite (v4):** `52dbfc8c515e7d8b760483a16ef52357d73b7435de8c72440cc0dfe4c3fec0dd` (`tests/test_author_assessment_tools.py`)
- **Preserved Working Manuscript:** `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2` (`TERRA_EDITORIAL_RESTART_V2/working/src/main.tex`) — **100% byte-identical, 0 modifications**.

### Synthetic Test Suite Execution
- **Interpreter:** Python 3.14.5 (tags/v3.14.5:5607950) AMD64 on Windows 10
- **Test Result:** **15/15 tests PASS in 5.201s (OK)** (expanded from 13 to 15 comprehensive unit tests)
- **Saved Execution Log:** Preserved at `TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/TEST_EXECUTION_LOG_03.txt` with environment metadata, source hashes, and complete CLI command outputs.

**Strict Operational Boundaries Maintained:**
- Zero real extraction, sampling, or author workbook distribution has taken place.
- Zero model, API, or vector database calls were executed.
- Zero working manuscript edits were made.

---

## 2. Detailed Point-by-Point Resolutions to CODE_AUDIT_03 Findings

### 1. Reversible Escaping & Raw Text Identity (Finding 1)
- **Raw In-Memory & Hash Identity:** In `scripts/prepare_author_assessment_workbooks.py`, sampled items retain raw, unescaped text in `item["query_text"]` and `item["response_text"]`. The private key mapping (`q_sha`, `r_sha`, `item_digest`) and companion HTML/TXT files operate strictly on verbatim raw source text.
- **Symmetric Reversible Storage Contract:** Escaping is applied strictly upon writing cells to `.xlsx` or rows to `.tsv`:
  - Leading apostrophes are doubled: `'` $\rightarrow$ `''` (e.g., `'Marbury v. Madison'` $\rightarrow$ `''Marbury v. Madison'`).
  - Leading formula / trigger prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`, `\n`) are prefixed with `'`.
  - In `scripts/process_author_assessments.py`, `unescape_formula` reverses this transformation symmetrically without altering subsequent characters or stripping whitespace: if `s.startswith("''")`, returns `s[1:]`; if `s.startswith("'")` and `s[1] in ("=", "+", "-", "@", "\t", "\r", "\n")`, returns `s[1:]`.
- **Targeted Round-Trip Testing:** `test_06_companion_reading_views_and_multiline_fidelity` verifies exact reversible round trips for every trigger prefix (`=`, `+`, `-`, `@`, `\t`, `\r`, `\n`, `'`) across XLSX and TSV exports, confirming loaded texts match raw originals byte-for-byte and verify against cryptographic SHA-256 hashes.

### 2. Immutable Field Validation & Fail-Closed Gates (Finding 2)
- **Mandatory Mapping Hashes:** In `scripts/process_author_assessments.py`, `validate_author_records_against_mapping` fails closed: if `query_text_sha256`, `response_text_sha256`, or `item_digest` is missing from the mapping schema, a `ValueError` is raised immediately.
- **All Assessor-Visible Immutable Fields Verified:** In addition to query/response SHA-256 hashes, the validator strictly verifies `cluster_id`, `as_of_cutoff_year`, `task_type`, and reconstructs the composite `item_digest`. Any discrepancy raises `ItemTamperingError`.
- **Preservation of Returned Originals:** `process_author_assessments` immediately creates `output_dir / "preserved_originals"` and copies `author1_input`, `author2_input`, and `mapping_path` before parsing or evaluating. Preserved file hashes are recorded in the terminal manifest.
- **Negative Test Controls:** `test_08_tampering_detection_negative_control` explicitly verifies that altered cutoff years, modified cluster IDs, altered query texts, and absent mapping hashes trigger immediate validation failures.

### 3. Full Lifecycle Integrity & Failure-Path Handling (Finding 3)
- **Unconditional `try ... except ... finally` Lifecycle:** Both preparation and statistical processing pipelines now wrap operations in unconditional `try ... finally` blocks.
- **Terminal Status Manifest:** `EXECUTION_INTEGRITY_MANIFEST.json` is written unconditionally in `finally` with terminal status (`COMPLETED_AND_VERIFIED`, `INCOMPLETE`, `FAILED`, or `FAILED_INPUT_MUTATION`), terminal input hashes, error diagnostics, and output artifact digests.
- **Metrics Emission Gate:** Final metrics (`merged_author_assessments.json`, `assessment_statistical_summary.json`) are only generated after all completions and pre/post input hash verifications succeed. If an input drifts or workbooks are incomplete, provisional metrics are never written to disk, preventing downstream consumption of unverified metrics.
- **Failure Path Testing:** `test_15_processor_lifecycle_failure_paths` verifies that:
  - Incomplete workbooks halt with exit code 2, write `EXECUTION_INTEGRITY_MANIFEST.json` with status `"INCOMPLETE"`, preserve originals, and write zero metrics files.
  - Tampered workbooks halt with exit code 3, write `EXECUTION_INTEGRITY_MANIFEST.json` with status `"FAILED"`, and write zero metrics files.

### 4. Production Hash Verification & Segregated Test Fixtures (Finding 4)
- **Removal of `--no-verify-hash`:** The bypass flag `--no-verify-hash` has been completely eliminated from `scripts/prepare_author_assessment_workbooks.py`.
- **Enforced Production Pins:** Production CLI execution strictly enforces the authoritative pinned SHA-256 hashes for temporal (`PINNED_HASHES["temporal"]`) and canonical (`PINNED_HASHES["canonical"]`) datasets, regardless of path spelling.
- **Segregated Fixture Mode:** For synthetic test suites, `--test-fixture-mode` allows test execution while explicitly labeling artifacts as non-production in `EXTRACTION_MANIFEST.json`:
  - `execution_mode: "SYNTHETIC_TEST_FIXTURE_NON_PRODUCTION"`
  - `certified_for_production: False`
  - Explicit warning string preventing production acceptance.
- **Negative Control:** `test_13_cli_execution_and_integrity_manifest` verifies that running the CLI without `--test-fixture-mode` against synthetic data fails immediately with a hash mismatch error.

### 5. Mixed Useful-Answer Accounting in Stage B Canonical Metrics (Finding 5)
- **Strict Yield across All Substantive Answers:** In `compute_population_metrics`, mixed refusal/substantive responses that are source-supported and responsive now enter strict supported-and-responsive yield alongside pure answers:
  - `strict_supported_and_responsive_pure_count` & `strict_supported_and_responsive_yield_pure`
  - `strict_supported_and_responsive_all_substantive_count` & `strict_supported_and_responsive_yield_all_substantive`
  - `broad_supported_and_responsive_count` & `broad_supported_and_responsive_yield_all`
- **Uncertainty Tracking & Legal Disclaimer:**
  - Reports `correctness_uncertain_count`, `correctness_uncertain_proportion`, `responsiveness_uncertain_count`, and `responsiveness_uncertain_proportion`.
  - Emits explicit `legal_status_caveat`: `"Empirical source-grounded judgments evaluate factual agreement with controlling historical authorities and do not constitute formal legal advice or licensed legal certification."`
- **Unit Test Coverage:** `test_11_mixed_refusal_accounting_in_canonical_metrics` asserts the full breakdown across pure and all-substantive strict yields, broad yields, and legal caveats.

### 6. Exact Boolean Schema Validation (Finding 6)
- **Strict `type(val) is bool`:** Replaced all `in (True, False)` membership checks with strict `type(val) is bool`. In Python, numeric `0` and `1` satisfy `0 in (True, False)`, which previously created divergence between point classification and bootstrap replicate filters.
- **Unavailable vs. Schema Error:** In `compute_population_metrics`, `sptlr_level2 is None` is treated as unavailable and tracked in `missing_or_unlabeled_automated_count`. Numeric `0`/`1` or string `"True"`/`"False"` trigger immediate `ValueError` schema errors.
- **Pre-Sampling Dataset Validation:** `validate_cohorts_and_schemas` similarly enforces `type(val) is bool` on `sptlr_level2`, `is_safe_refusal`, and `safety_rejected`.
- **Unit Test Coverage:** `test_14_exact_boolean_schema_validation` verifies that numeric `0`, `1`, and string `"True"` trigger immediate `ValueError` across both metric calculation and dataset validation routines.

---

## 3. Bounded Notes Resolutions

1. **Authoritative Reading Route Designation:** The workbook instructions sheet and companion HTML views now explicitly designate `READING_VIEW_AUTHOR_X.html` as the **authoritative reading route** for multi-paragraph responses and full legal analysis, making clear that Excel cards are an alternate tabular view subject to row height caps.
2. **Temporal Leakage Alignment with `sptlr_level2`:** Rubric instructions explicitly define temporal leakage as severe, operative temporal leakage where controlling judicial doctrine or statutory amendments originating strictly after the as-of cutoff year are asserted as governing legal rules to answer the query, matching the exact severity definition of benchmark `sptlr_level2`.
3. **Temporal Leakage Evidence Requirement:** In `validate_workbook_completion`, temporal leakage `"yes"` requires either primary source citation / excerpt or an explicit explanation in rationale (e.g., `"unavailable"`, `"cannot locate"`).

---

## 4. Current Repository & Verification State

| Artifact | Version | SHA-256 | Test / Audit Status |
| :--- | :--- | :--- | :--- |
| `scripts/prepare_author_assessment_workbooks.py` | v4 | `c375d73c28cca2b04cce30043dfba4ecaf560eab528cf437cefa59040c0f3523` | Hardened (Audited) |
| `scripts/process_author_assessments.py` | v4 | `6f96564ebacd4bce5336f23dd1be9eaf477f039c80bc06786c7c402014b0fdd3` | Hardened (Audited) |
| `tests/test_author_assessment_tools.py` | v4 | `52dbfc8c515e7d8b760483a16ef52357d73b7435de8c72440cc0dfe4c3fec0dd` | 15/15 PASS (Audited) |
| `TERRA_EDITORIAL_RESTART_V2/working/src/main.tex` | - | `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2` | Byte-Preserved (0 edits) |
| `TEST_EXECUTION_LOG_03.txt` | v4 Log | Verified | Preserved |

---

## 5. Next Steps

With the offline preparation and processing tools fully hardened against all CODE_AUDIT_03 requirements, 15 synthetic unit tests passing, and the complete execution log recorded:
1. Ready for Codex review of the v4 changes and test evidence.
2. Upon user and Codex clearance, real offline prospective sampling and workbook extraction can be executed against the pinned production datasets.
3. No real sampling, API calls, or manuscript edits will proceed prior to that explicit authorization.
