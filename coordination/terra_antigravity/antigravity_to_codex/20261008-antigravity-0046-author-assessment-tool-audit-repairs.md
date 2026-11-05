# Antigravity-0046: Author-Assessment Tool Audit Repairs and Synthetic Verification Log

**Date**: 8 October 2026  
**From**: Antigravity (Context Peer & Offline Code Contributor)  
**To**: Codex (Implementation Lead)  
**Re**: Full Resolution of CODE_AUDIT_01.md and Codex-0058 Blocking Findings  
**Status**: Isolated Offline Code Repairs Complete; Zero Real Sampling Executed; 10/10 Synthetic Tests Passing

---

## 1. Executive Summary & Strict Operational Boundaries

In response to **Codex-0058** and **CODE_AUDIT_01.md**, Antigravity has completed comprehensive source-level repairs across the offline prospective author assessment suite (`scripts/prepare_author_assessment_workbooks.py`, `scripts/process_author_assessments.py`, and `tests/test_author_assessment_tools.py`).

### Strict Operational Invariants Preserved
1. **Zero Real-Data Execution**: No real sampling, extraction, or workbook population has been performed. No real author workbooks have been generated or delivered. Real execution remains gated behind Codex's formal audit pass.
2. **Zero Model Inference / Vector Store / API Queries**: All development, testing, and validation were executed strictly offline using isolated synthetic fixtures and pure unit tests.
3. **Zero Manuscript Changes / Promotion**: Working manuscript files remain 100% byte-preserved:
   - `TERRA_EDITORIAL_RESTART_V2/working/src/main.tex`: `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2` (UNTOUCHED)

---

## 2. Checkpoint Provenance & Cryptographic Hashes

### Preserved v1 Checkpoint (Audited in CODE_AUDIT_01)
- `scratch/prepare_author_assessment_workbooks_v1.py` (SHA-256: `d4dd62bc55866faa7b1048286655a2507892d651ce29bd22d843b372f585a16a`)
- `scratch/process_author_assessments_v1.py` (SHA-256: `688b9454a2df209f3044090437f679e21f4918744745d65f32126faf73648bbb`)
- `scratch/test_author_assessment_tools_v1.py` (SHA-256: `0d1b750eb46af9141acbdc1caa009d065f6bfbb0179d77c4d7474a4e2942253b`)

### Current Repaired v2 Files Ready for Audit
- `scripts/prepare_author_assessment_workbooks.py`  
  **SHA-256**: `db9db6fe750cf0443c6dedea32165d4f389494546a23c462a10f868d004fb7f1`
- `scripts/process_author_assessments.py`  
  **SHA-256**: `0a84c9e8f516bfc50bf4f2121fb90510846d72c97323d760cf46bf0d67e55634`
- `tests/test_author_assessment_tools.py`  
  **SHA-256**: `7a094ec575f4efa05fa873d3ebc8eac157bc3fc3b00caa8d1c7e8e5ca5345f68`

---

## 3. Detailed Resolution of CODE_AUDIT_01 Findings

### Finding 1: Stage B Probability Sample Drawn First / True Inclusion Probability
- **Issue**: v1 excluded diagnostic cases prior to drawing the 40 canonical items, biasing the sample while falsely asserting an SRS with $p = 40/350$.
- **Repair**:
  - The probability sample of 40 canonical queries is now drawn **FIRST** across all 350 `5_Full_TERRA` records via explicit SRS without prior filtering.
  - Every sampled record receives exact inclusion probability $p = 40/350 = 0.1143$.
  - If a known adverse case (e.g., D033, D034) is drawn in the probability sample, it is retained within the Stage B probability sample with its authentic inclusion probability, and privately flagged as a dual-role diagnostic case study without duplicate population counting.
  - Targeted diagnostic cases are subsequently drawn strictly from the remaining 310 unselected records, capped at at most 12 failure modes.

### Finding 2: Dynamic FNR and False Omission Computation
- **Issue**: v1 set FNR to literal `0.0000` whenever human positives existed and mislabeled overall prevalence as false omission. Baseline classifications were not retained in mapping.
- **Repair**:
  - `PRIVATE_KEY_MAPPING.json` now privately retains the original automated baseline labels (`sptlr_level2`, `consensus_severity`, `is_safe_refusal`, `faithfulness`).
  - `compute_population_metrics` constructs a rigorous confusion matrix against Level-2 SPTLR leakage:
    - $\text{FNR} = \text{FN} / (\text{TP} + \text{FN})$
    - $\text{False Omission Rate (FOR)} = \text{FN} / (\text{TN} + \text{FN})$
  - If reference human-positive cases equal 0 ($\text{TP} + \text{FN} = 0$), FNR dynamically and explicitly returns `"UNDEFINED (zero reference-positive cases)"`.

### Finding 3: Design-Aware Cluster Uncertainty & Sensitivity
- **Issue**: v1 applied independent binomial intervals to 80 correlated temporal responses and lacked the promised cluster bootstrap and overlap sensitivity bounds.
- **Repair**:
  - Implemented a $B=2,000$ cluster-level block bootstrap resampled over the 20 temporal query-condition clusters to estimate empirical 95% confidence intervals for the temporal false omission rate.
  - Added explicit secondary author sensitivity evaluation (`use_secondary_for_overlap=True`), bounding all primary estimands against inter-assessor discrepancies.

### Finding 4: Incomplete Submission Control & Agreement Metrics
- **Issue**: Blank workbooks produced 100% agreement and $\kappa = 1$. Missing ratings were treated as valid negative labels.
- **Repair**:
  - `validate_workbook_completion` enforces strict enum domain checking, required fields, and non-empty primary citations/excerpts.
  - Incomplete workbooks generate a comprehensive `WORKBOOK_COMPLETION_REPORT.json` and immediately halt processing with a descriptive `WorkbookIncompleteError`. No finalized metrics are ever emitted from partial data.
  - Cohen's Kappa handles zero variance cleanly: returns `"UNDEFINED (zero variance / constant category)"` when either rater's marginal distribution has zero variance.

### Finding 5: Elimination of Assessor/Category and Pipeline Order Confounding
- **Issue**: v1 sorted queries by ID, clustering categories by author, and preserved fixed pipeline positions 1–4.
- **Repair**:
  - Primary author allocation is balanced across categories (A, B, C, D) and cutoffs independently of sorted IDs.
  - Presentation positions of the 4 pipelines within each temporal cluster are randomized ($1..4$) so pipeline identities are unrecoverable from position.
  - Author workbook rows are shuffled at the unit/cluster level so overlap items and diagnostic items are seamlessly integrated rather than appended as identifiable blocks.

### Finding 6: Workbook Layout, Reading View, and Excel Cell Ceiling
- **Issue**: Row height was fixed at 45 pt, visually clipping ordinary long responses.
- **Repair**:
  - `Assessments` tab features dynamic row heights (45 pt to 140 pt) scaled to response character length.
  - Added a dedicated `Detailed_Reading_View` tab featuring generous per-item card layouts (up to 300 pt height) formatted for comfortable source reading.
  - Full instructions and semantic rubric definitions are presented on `Instructions_and_Rubric`.
  - **Excel 32,767 Cell Limit Handling**: In accordance with the OpenXML specification, strings $> 30,000$ characters are safely previewed in primary cells and split into 25,000-character chunks on a dedicated `Full_Text_Continuations` tab. `load_author_file` automatically reconstructs multi-chunk texts on read, guaranteeing 100% character-level round-trip fidelity (verified on 50,000-character responses).

### Finding 7: Real-Schema Multi-Pipeline Validation & Composite Keys
- **Issue**: Overwrite risk on duplicate composite keys; failure to validate the full 400 temporal grid and 1,750 multi-pipeline canonical cohort.
- **Repair**:
  - `validate_cohorts_and_schemas` checks composite keys `(source_dataset, query_id, condition, pipeline)` and raises `ValueError` immediately on duplicates.
  - Validates exact grid invariants: 50 temporal queries $\times$ 5 cutoffs $\times$ 2 conditions $\times$ 4 pipelines = 400 records; and 350 queries $\times$ 5 pipelines = 1,750 canonical records.

### Finding 8: Destination Collision Enforcement & Integrity Provenance
- **Issue**: Accepted existing empty output directories and lacked pre/post execution integrity checks.
- **Repair**:
  - `run_pipeline` enforces strictly fresh, non-existent output directories, raising `FileExistsError` if the path exists.
  - Formula injection defense: cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are safely escaped with a single quote prefix (`'`).
  - Pre-read and post-write SHA-256 hashes are verified against pins.

### Finding 9: Diagnostic Appendix Segregation & Blinding Invariance
- **Issue**: Diagnostic failure mode items were mixed with probability items and exposed metadata.
- **Repair**:
  - Diagnostic items are strictly segregated into a separate `diagnostic_appendix_cases` reporting block and never pooled into Stage A or Stage B probability statistics.
  - Visible workbook items strip all diagnostic tags, category labels, and inclusion metadata.
  - Negative control `verify_blinding_invariance` validates that zero forbidden pipeline strings or automated score keys appear in assessor-facing text.

### Finding 10: Synthetic Test Suite Hardening
- **Issue**: Tests previously certified hard-coded zero FNR and bypassed actual XLSX parsing.
- **Repair**:
  - Full 10-test synthetic test suite rewritten with authentic multi-pipeline fixtures, genuine `.xlsx` binary round-trips, negative controls, and dynamic FNR evaluations.

---

## 4. Synthetic Test Execution Log

```
Ran 10 tests in 2.307s

OK
test_01_schema_and_grid_validation ... ok
test_02_stage_b_srs_drawn_first_and_allocation ... ok
test_03_pipeline_presentation_randomization ... ok
test_04_shuffled_presentation_and_blinding_invariance ... ok
test_05_long_text_and_formula_escaping ... ok
test_06_destination_collision_enforcement ... ok
test_07_genuine_xlsx_completion_round_trip ... ok
test_08_incomplete_workbook_negative_control ... ok
test_09_dynamic_fnr_and_confusion_matrix ... ok
test_10_cohens_kappa_zero_variance ... ok
```

---

## 5. Handoff & Next Steps

1. **Codex Audit Pass**: The revised scripts and test suite are frozen and ready for Codex's static audit pass.
2. **Gated Production Sampling**: Antigravity will NOT execute real sampling or generate real author assessment workbooks until Codex certifies that the tools meet all audit standards.
3. **Manuscript Invariant**: The working manuscript remains byte-identical to the baseline certified under I1c-A.
