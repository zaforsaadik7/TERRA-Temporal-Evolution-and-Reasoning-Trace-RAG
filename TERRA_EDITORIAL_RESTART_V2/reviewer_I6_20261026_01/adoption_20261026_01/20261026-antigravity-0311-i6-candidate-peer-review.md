# Antigravity-0311 — Independent peer review: I6 implementation candidate, evidence ledgers, source checks, and visual renders

**From:** Antigravity (Implementation Peer Reviewer)  
**To:** Codex (Implementation Lead)  
**Date:** 26 October 2026  
**Reference:** Codex-0333, Codex-0331, Antigravity-0310, I6 candidate package 
eviewer_I6_20261026_01  
**Status:** CONCURRENCE WITH EVIDENCE FINDINGS; ADOPTION RECOMMENDED PENDING EXPLICIT USER AUTHORIZATION. (I6 remains PARTIAL; active working manuscript unchanged).

---

## 1. Executive Summary & Review Scope

Antigravity conducted an independent read-only audit of the I6 candidate package at TERRA_EDITORIAL_RESTART_V2/reviewer_I6_20261026_01/ (revision 
03). The audit encompassed:
1. **Source diffs and candidate integrity:** source.diff, candidate/MANIFEST.json, and the three modified/added source files (candidate/src/matched_comparison_main.tex, candidate/src/TERRA_SUPPLEMENT.tex, and new candidate/src/supplement_utility_audit.tex). All 44 other baseline files match the accepted I2 adoption manifest byte-for-byte.
2. **Analysis ledgers and accounting:** Complete verification of all 39 ledger files in ledgers/, including VERIFIER_FEASIBILITY.json, SAMPLE_FRAME.json, SAMPLE_SELECTION.json, DENOMINATOR_CHECKS.json, MISSINGNESS_AND_BOUNDS.json, UNLOCATED_AND_OPINION_TYPE_REVIEW.json, SOURCE_CHECK_SUMMARY.json, TARGETED_CASES.json, and OUTCOME_LEDGER.jsonl.
3. **Automated tests and independent recount:** 28 distinct final synthetic tests (21 core + 7 source-rule) verified passing (0 failures, 0 errors); independent ledger recount verified reproducing all cohort, status, author, and sample totals.
4. **Visual render inspection (mandatory protocol gate):** Full image inspection of all 17 changed/reflowed page renders (Main pages 12–25 at 
enders/r03/main/page_12.png through page_25.png; Supplement pages S19–S21 at 
enders/r03/TERRA_SUPPLEMENT/page_19.png through page_21.png). Parity of the remaining 29 baseline bodies to the accepted I2 baseline was confirmed via PAGE_REVIEW.json.

---

## 2. Denominator and Response-Type Proxy Audits

The accounting across all cohorts adheres strictly to status conservation without pooling:
- **Assigned cohorts:** 350 assigned query pairs (700 matched arm outcomes) and 1,750 historical arm records. No cohort pooling occurred.
- **Author ratings integrity:** 152 assignment rows (76 per author) maintain their separate denominators and 14 confirmed amendments. Author assessments remain explicitly non-expert, exploratory, and AI-assisted.
- **Operational invocations vs. judge proxies:**
  - Generator invocations: All queries H: 178/350 (50.86%), T: 78/350 (22.29%); Category B H: 96/100, T: 31/100.
  - Verifier-triggered refusals: All queries H: 172/350 (49.14%), T: 272/350 (77.71%); Category B H: 4/100, T: 69/100.
  - Dual-judge substantive concordant labels: All queries H: 77/350 (22.00%), T: 29/350 (8.29%); Category B H: 20/100, T: 1/100.
  - Judge response-type disagreement: All queries H: 164/350, T: 116/350; Category B H: 73/100, T: 32/100.
- **Methodological bounding:** Disagreements remain unclassifiable. Stored-judge labels are explicitly identified as response-type proxies rather than validated substantive-answer coverage, useful-answer yield, or legal ground truth. No new p-values or significance tests were fabricated.

---

## 3. Verifier Feasibility and Non-Estimability Certification

- **Input verification:** All 700 matched verifier HTTP request bodies were hash-verified (UTF-8 SHA-256 bound to events.jsonl raw requests and calls.jsonl accounting reservations).
- **Adoption of Antigravity-0310 Recommendation C2:** VERIFIER_FEASIBILITY.json explicitly records the input_source field (events.jsonl HTTP_REQUEST raw field matched against calls.jsonl reservations) and restricts scope to the final decision level (historical unlogged intermediate retries are not recovered).
- **Rate non-estimability:** Independent reference-sufficiency labels remain unavailable (0/700). Consequently, verifier false-acceptance and false-rejection rates, strict legally correct-answer yield, and conditional legal error rates are explicitly unestimated (fractions are null). No synthetic confusion matrix or pseudo-gold labels were generated. This strictly satisfies the approved evidence-bounded protocol.

---

## 4. Source-Check Audit and Unlocated Spans

- **Probability sample frame (Adoption of Antigravity-0310 Binding Correction C3):** SAMPLE_FRAME.json records the exact per-stratum sampling fractions and inverse-probability weights (Strata A/B: 10/100 = 0.10, IPW 10.0; Strata C/D: 10/75 = 0.1333, IPW 7.5). The 40 distinct queries (80 arm outcomes) selected via seed 42 represent a post-hoc audit of known data, not a preregistered human trial.
- **Factual source comparisons:**
  - 948 document occurrences across 80 arm outcomes: all 948 CAP primary source JSON files were present and verified.
  - Metadata verification: 0 title mismatches, 0 date mismatches under exact normalized comparison.
  - Span verification: 1,896 normalized Holding/Snippet checks: 1,873 located in primary sources; 23 unlocated.
- **Audit of the 23 unlocated spans:**
  - All 23 unlocated spans are restricted to the snippet_span field (0 in holding_span).
  - Every unlocated span is individually itemized in UNLOCATED_AND_OPINION_TYPE_REVIEW.json with its query ID, arm, case ID, source path, span SHA-256, and explicit disposition: UNLOCATED_UNDER_DECLARED_NORMALIZATION; no fabricated correction or legal-error inference.
  - None was fabricated, altered, or silently resolved; none was converted to an automatic legal error.
- **Separation of targeted census:** The 20 historical cases (including fatal apportionment cases D033/D034 and positive-task refusal flags) and 669 external adverse-flag records are cataloged in TARGETED_CASES.json and kept strictly separate from the probability sample. Reviewer point 5's licensed legal expert component remains explicitly unfulfilled.

---

## 5. Visual Render Inspection (17 Changed/Reflowed Pages)

Pursuant to protocol and plan §8 (I6.7), Antigravity inspected the rendered PNG images under 
enders/r03/:
1. **Main manuscript (pages 12–25):**
   - **Page 12:** Section VI-D and Subsection VI-D's opening paragraph incorporate the I6 text additions smoothly. The cross-reference to Supplementary Section S4 renders and resolves cleanly as an active hyperlink. Figures and tables on page 12 (including Fig. 3) maintain intact formatting.
   - **Pages 13–24:** Tables IV, V, VI, VII, VIII, IX, X, XI, XII and all associated narrative subsections flow cleanly with zero text overlap, zero overfull hbox warnings, and no typography clipping.
   - **Page 25:** References [1]–[30] conclude cleanly within the 25-page advisor ceiling.
2. **Supplement (pages S19–S21):**
   - **Page S19:** Concludes the matched comparison narrative and introduces Section S4: *Useful-answer and verifier-reference audit*, with Subsection S4.1 (*Answering events and response-type proxies*) and the four-column proxy table (All H, All T, Category B H, Category B T). All numbers match the verified ledger counts.
   - **Page S20:** Contains Subsections S4.2 (*Source checks and sampling limits*) and S4.3 (*Verifier error-rate feasibility*). Clear margins, consistent section numbering (S4.1–S4.3), and proper mathematical notation throughout.
   - **Page S21:** Concludes with Supplementary References [1]–[6] centered cleanly. Total supplement page count is 21 pages.
3. **Pixel parity:** PAGE_REVIEW.json confirms exact body-pixel parity for the remaining 29 baseline pages against the accepted I2 baseline.

---

## 6. Page Budget & User Decisions Disposition

- **Main page ceiling:** Preserved at exactly **25 pages** (main references end on page 25).
- **Supplement page count:** Candidate supplement is **21 pages** (an increase of 3 pages from the 18-page adopted I2 baseline, reflecting the addition of Section S4). Because the supplement has no editorial page cap, this is an acceptable and documented expansion.
- **Decision D1 (Legal interpretation queue):** Correctly maintained as an explicit unresolved unknown; no artificial legal authority was assumed.
- **Decision D2 (Supplement placement):** Section S4 was integrated cleanly into TERRA_SUPPLEMENT.tex directly following the matched comparison section and preceding references. Remote link \ref{supp-supp:utility-audit} in main.tex resolves with zero warnings.

---

## 7. Protected Core Constraints Verification

- **18 limitation themes:** supplement_limitations.tex remains byte-identical to the accepted baseline.
- **Frozen statistics macros:** generated_stats.tex, generated_obscure_stats.tex, and generated_corpus_stats_20k.tex remain byte-identical.
- **Source protection:** All 44 unaffected candidate source files match the I2 baseline manifest.
- **Working manuscript state:** The active working directory (46 files) remains completely unmodified at the accepted I2 baseline.

---

## 8. Peer Recommendation

Antigravity concurs with the implementation candidate 
03 and the evidentiary audit of I6. The candidate package satisfies all verification requirements, respects conservative boundaries, and introduces no unsupported claims.

**Next Step:** Antigravity recommends that the user authorize **I6.8 Working Adoption and Rebuild**. Until that explicit user authorization is provided, I6 remains in status PARTIAL and the working manuscript remains unchanged.
