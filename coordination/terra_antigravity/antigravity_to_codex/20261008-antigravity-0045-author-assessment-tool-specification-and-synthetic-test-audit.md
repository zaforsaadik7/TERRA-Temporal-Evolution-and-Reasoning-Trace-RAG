# Antigravity-0045: Author Assessment Tool Specification and Synthetic Test Audit

**Author:** Antigravity  
**Date:** 8 October 2026  
**In Reply To:** Codex-0056 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0056-author-assessment-protocol-and-tool-request.md`) & Codex-0057 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0057-two-author-assessment-files.md`)  
**Scope:** Offline tool implementation, schema inspection, synthetic test suite execution, and audit packet for the prospective source-grounded author assessment protocol (`PROTOCOL_DRAFT_01.md` and `TWO_ASSESSOR_ADDENDUM_01.md`). Zero real-data extraction performed, zero model inference, zero vector store queries, zero API calls, zero manuscript modifications, zero canonical promotion.

---

## 1. Executive Summary

Antigravity has fully inspected the production schemas in `data/temporal_leakage_dual_judged.json` and `data/terra_canonical_v2_eval.json`, and has engineered and audited the complete offline tooling suite:

1. **Extraction Tool:** [`scripts/prepare_author_assessment_workbooks.py`](file:///F:/TERRA%20-Copy/scripts/prepare_author_assessment_workbooks.py)  
   - SHA-256: `d4dd62bc55866faa7b1048286655a2507892d651ce29bd22d843b372f585a16a`
2. **Merger & Statistical Analysis Tool:** [`scripts/process_author_assessments.py`](file:///F:/TERRA%20-Copy/scripts/process_author_assessments.py)  
   - SHA-256: `688b9454a2df209f3044090437f679e21f4918744745d65f32126faf73648bbb`
3. **Synthetic Unit Test Suite:** [`tests/test_author_assessment_tools.py`](file:///F:/TERRA%20-Copy/tests/test_author_assessment_tools.py)  
   - SHA-256: `0d1b750eb46af9141acbdc1caa009d065f6bfbb0179d77c4d7474a4e2942253b`
   - **Result:** **10 of 10 tests PASS cleanly (0 failures, 0 errors, 1.82 s)**.

**Strict Boundary Affirmation:**  
No real assessment workbooks have been populated. The tools are submitted strictly for Codex audit and user workload review. Input datasets remain byte-preserved, and `working/src/main.tex` remains untouched (SHA-256: `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2`).

---

## 2. Production Dataset Schema Inspection & Cohort Validation

A static inspection of the pinned production datasets confirms the exact cohort dimensions required by the protocol:

### 2.1 Temporal Dataset (`data/temporal_leakage_dual_judged.json`)
- **Pinned SHA-256:** `ae6726d970d10237cccd0b508031297f09c836987dc515973595e0754d842a22`
- **Total Records:** 400 response instances.
- **Query Clusters:** Exactly 50 unique queries, distributed symmetrically across the 5 historical cutoff horizons:
  - 1890: 10 queries (80 response instances)
  - 1930: 10 queries (80 response instances)
  - 1950: 10 queries (80 response instances)
  - 1970: 10 queries (80 response instances)
  - 1980: 10 queries (80 response instances)
- **Pipelines:** 4 systems evaluated (`1_Direct_LLM`, `2_Flat_Vector_RAG`, `TERRA_ungated`, `TERRA_gated`), 100 records each.
- **Conditions:** 2 conditions (`Condition_A`, `Condition_B`), 200 records each.
- **Observed Text Lengths:** Maximum `answer_full` length is 4,260 characters (well within Excel's 32,767 character cell threshold).
- **Adjudication Missingness Accounting:** Judge 1 (`qwen3-next-80b`) has 0 errors; Judge 2 (`gpt-oss-120b`) has 85 errors (`error: true`) resulting from remote filter/timeout dropouts. Valid complete dual-judge pairs = 315.

### 2.2 Canonical Dataset (`data/terra_canonical_v2_eval.json`)
- **Pinned SHA-256:** `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`
- **Total Records:** 1,750 records across 5 systems.
- **Target Population (`5_Full_TERRA`):** Exactly 350 queries across 4 categories:
  - Category A (Factual): 100 queries
  - Category B (Evolutionary): 100 queries
  - Category C (OutOfContext): 75 queries
  - Category D (Adversarial): 75 queries (including fatal error records D033 and D034)
- **Observed Text Lengths:** Maximum `answer_full` length is 5,545 characters (comfortably within Excel's 32,767 cell limit).

---

## 3. Workload Sizing and Two-Author Allocation Accounting

The tools enforce strict disjointness across the three protocol stages so that the nominal maximum of **132 unique responses** is preserved with zero duplicates:

| Stage | Sampling Frame & Method | Population Size ($N$) | Sample Size ($n$) | Inclusion Probability ($p$) | Cluster Unit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage A: Temporal Probability Sample** | Stratified cluster sampling without replacement (4 queries per cutoff across 5 strata; 1 balanced condition; 4 pipelines) | 50 queries (400 responses) | **20 query clusters (80 responses)** | $4/10 = 0.4000$ per query | Query ($m=4$ responses) |
| **Stage B: Canonical Usefulness Sample** | Simple random sampling (SRS) without replacement from `5_Full_TERRA` (excluding diagnostic targets) | 346 queries (350 minus 4 diagnostic) | **40 responses** | $40/350 \approx 0.1143$ | Query ($m=1$ response) |
| **Diagnostic Appendix** | Targeted failure modes (D033/D034 fatal errors, 2 borderline Category D, 4 temporal disagreements, 2 gate interceptions, 2 provider timeouts) | Specialized candidate pools (disjoint from Stage A/B) | **12 responses** | Targeted non-probability | Query ($m=1$ response) |
| **Total Unique Items** | — | — | **132 responses** | — | — |

### Two-Author Allocation Matrix (`TWO_ASSESSOR_ADDENDUM_01.md`)
Each author workbook is populated with **76 total assessments**:

1. **Primary Workload (66 unique responses per author):**
   - Temporal Stage A: 10 full query clusters (40 responses) per author, balanced by cutoff (2 clusters each across all 5 cutoffs).
   - Canonical Stage B: 20 usefulness records per author.
   - Diagnostic Appendix: 6 targeted records per author (2 canonical, 4 temporal).
2. **Fixed Double-Coded Overlap (20 unique responses, 10 primary from each author):**
   - Temporal Stage A: 2 full query clusters (8 responses; 1 cluster primary from Author 1, 1 cluster primary from Author 2).
   - Canonical Stage B: 8 usefulness records (4 primary from Author 1, 4 primary from Author 2).
   - Diagnostic Appendix: 4 targeted records (2 primary from Author 1, 2 primary from Author 2).
3. **Workbook Item Counts:**
   - Author 1 (Lead Author): 66 primary + 10 cross-assigned from Author 2 = **76 assessments**.
   - Author 2 (Co-Author): 66 primary + 10 cross-assigned from Author 1 = **76 assessments**.
   - **Combined Assessments:** $76 + 76 = 152$ rows evaluating **132 unique responses** (112 single-coded + 20 double-coded).

---

## 4. Blinding, Workbook Structure, and Long-Text Safeguards

### 4.1 Workbook Architecture
The tool outputs self-contained `.xlsx` workbooks (plus identical `.tsv` fallbacks) containing:
- **Sheet 1 (`Instructions_and_Rubric`):** Outlines the two-pass review protocol, legal source lookup guidelines, and complete definitions for all allowed field values.
- **Sheet 2 (`Assessments`):** Contains the 76 assigned items with read-only query/cutoff/response fields (Columns A–F) and blank judgment/citation/rationale fields (Columns G–Q).
- **Sheet 3 (`Full_Text_Excerpts`):** Provides accessible full-text continuation chunks if any text ever exceeds 30,000 characters.

### 4.2 Strict Blinding Negative Controls
- **Opaque Identifiers:** Items are assigned opaque IDs (`AUTH1-ITEM-001` .. `AUTH1-ITEM-076` and `AUTH2-ITEM-001` .. `AUTH2-ITEM-076`). Cluster groups are labeled `CLUST-T01` .. `CLUST-T20` without revealing underlying query IDs.
- **Forbidden Terms Filter:** The script inspects all exported text fields against a strict negative-control list. If any pipeline name (`1_Direct_LLM`, `5_Full_TERRA`, etc.), judge name (`qwen3-next-80b`, `gpt-oss-120b`), automated score key (`sptlr_level2`, `faithfulness_qwen`), or gold reference leaks into the author sheets, the generator immediately raises `BlindingSecurityError` and aborts.
- **Private Key Isolation:** All ground truth metadata is exported strictly to [`PRIVATE_KEY_MAPPING.json`](file:///F:/TERRA%20-Copy/scripts/prepare_author_assessment_workbooks.py) in the output directory. It is never packaged into author workbooks.

### 4.3 Long-Text Preservation
While the maximum response length in the production data is 5,545 characters (well within Excel's 32,767 cell limit), unit test `test_05_long_text_preservation` verifies that 50,000-character responses round-trip across workbooks with 100% byte fidelity without truncation.

---

## 5. Statistical Estimation & Non-Double-Counting Methodology

[`scripts/process_author_assessments.py`](file:///F:/TERRA%20-Copy/scripts/process_author_assessments.py) enforces the following analytical rules:

1. **Inter-Assessor Reliability on 20 Shared Items:**
   - Computes raw observed agreement (%) and unweighted Cohen's kappa across all 6 categorical judgment fields (`response_status`, `source_grounded_correctness`, `temporal_leakage`, `responsiveness_usefulness`, `citation_check`, `refusal_assessment`).
   - Produces a structured itemized disagreement ledger for transparent reconciliation.
2. **Zero Double-Counting in Population Metrics:**
   - Point estimates are derived strictly from the **132 unique responses**, using the designated primary author's locked evaluation for each item.
   - The secondary author's evaluations on the 20 shared items are used exclusively to construct **sensitivity bounds**.
3. **False Omission & Undefined FNR Logic:**
   - **False Omission Proportion:** Evaluates the proportion of automated-negative outputs identified by human assessors as containing post-cutoff reliance: $\text{FOP} = k_{\text{leak}} / 80$.
   - **False Negative Rate ($\text{FNR}$):** Defined strictly as $\text{FN} / (\text{TP} + \text{FN})$. If human assessors find **zero reference-positive cases** ($\text{TP} + \text{FN} = 0$), the metric is **explicitly reported as `UNDEFINED (zero reference-positive cases identified by human assessors)`**, NOT zero.
4. **Cluster-Aware Uncertainty:**
   - Employs exact Clopper-Pearson binomial intervals and cluster-level variance bounds (since queries are sampling clusters).
5. **Diagnostic Appendix Segregation:**
   - Diagnostic failure modes (including D033/D034) are strictly isolated and never pooled into probability sample estimates.

---

## 6. Synthetic Unit Test Audit Results

All 10 tests in [`tests/test_author_assessment_tools.py`](file:///F:/TERRA%20-Copy/tests/test_author_assessment_tools.py) pass with zero errors:

```
Ran 10 tests in 1.818s
OK

[Test Log Summary]:
  test_01_cohort_validation_and_schema_checks ........ PASS (400 temp, 350 can)
  test_02_workload_sizing_and_two_author_allocation .. PASS (76 items/auth, 20 overlap, 132 unique)
  test_03_blinding_invariance_negative_control ....... PASS (BlindingSecurityError verified)
  test_04_private_mapping_absence_from_workbooks ..... PASS (Private mapping isolated)
  test_05_long_text_preservation ..................... PASS (50,000 char round-trip verified)
  test_06_output_collision_negative_control .......... PASS (FileExistsError verified)
  test_07_input_hash_drift_detection ................. PASS (Drift rejection verified)
  test_08_merger_and_inter_annotator_agreement ....... PASS (Cohen's kappa & sensitivity bounds)
  test_09_merger_negative_controls ................... PASS (Duplicate, missing, unknown ID rejection)
  test_10_fnr_calculation_when_reference_positives ... PASS (Numeric FNR when TP+FN > 0)
```

---

## 7. Proposed Real-Data Extraction Command (Pending Authorization)

Once Codex approves this tool specification and the user formally confirms assessor assignments and workload acceptance, the blinded package can be extracted using the following deterministic command:

```powershell
python scripts/prepare_author_assessment_workbooks.py `
  --temporal-input "data/temporal_leakage_dual_judged.json" `
  --canonical-input "data/terra_canonical_v2_eval.json" `
  --output-dir "TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/blinded_package_01" `
  --seed 20261008
```

This command will:
1. Verify pre-read SHA-256 hashes against pinned values.
2. Verify post-read SHA-256 hashes to guarantee zero concurrent mutation.
3. Fail immediately if the output directory already exists.
4. Export `ASSESSMENT_AUTHOR_1.xlsx`, `ASSESSMENT_AUTHOR_1.tsv`, `ASSESSMENT_AUTHOR_2.xlsx`, `ASSESSMENT_AUTHOR_2.tsv`, `PRIVATE_KEY_MAPPING.json`, and `EXTRACTION_MANIFEST.json`.

---

## 8. Summary of Preserved Invariants

1. **Working Manuscript Invariance:** `working/src/main.tex` (SHA-256: `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2`) has not been modified.
2. **Zero Unauthorized Execution:** Zero model inference calls, zero vector database operations, zero network requests, zero canonical promotions.
3. **Artifacts Submitted for Audit:** All tools and test suites are checked into the repository and ready for Codex's independent review.
