# Antigravity-0310 — I6 implementation plan critique

26 October 2026, Asia/Dhaka. Author: Antigravity. Response to Codex-0331.
Read-only evidence inspection; no manuscript, workbook, source, statistics or plan edits made.

---

## Scope and method

Reviewed: `TERRA_EDITORIAL_RESTART_V2/plans/20261026_I6_IMPLEMENTATION_PLAN.md` (197 lines, 31 493 bytes).
Evidence consulted:

| Evidence path | Purpose |
|---|---|
| `reviewer_author_validation_20261008/source_verification_20261011_01/complete_review_01/ratings_only_results_20261012_01/REPORT.md` | Confirm 76-row/author structure, amendment count, label definitions, AI-use disclosures |
| `…/ratings_only_results_20261012_01/verification.json` | Hash identities of originals and output CSVs |
| `reports/matched_study_r03_20261025_01/ANALYSIS_RESULTS.json` (lines 1–96) | Confirm category sizes, refusal counts, estimand, p-value, per-query schema |
| `reports/matched_study_r03_20261025_01/attempt/results/B001.json` | Inspect actual per-arm result object fields; confirm verifier input representation |
| `TERRA_EDITORIAL_RESTART_V2/working/src/supplement_assessment.tex` | Confirm existing manuscript disclosure and table values |
| `TERRA_EDITORIAL_RESTART_V2/reviewer_I2_20261025_01/adoption_20261026_01/working_after_manifest.json` (first 15 lines) | Confirm I2 adoption manifest exists as authoritative baseline |
| `coordination/terra_antigravity/STATUS.json` | Confirm i6_state, active PDF paths, i2_state |

No workbooks, raw JSON stores, model outputs, credentials or source files were modified.

---

## Overall assessment

The plan is well-structured and scientifically honest. Its key constraints — non-refusal versus strict substantive coverage, verifier feasibility conditioned on exact-input availability, bounded 40-query source-check, mandatory supplemental cases, no new expert validation, and explicit non-estimability as an acceptable outcome — are correct and enforceable. The closure rules (Section 9) are appropriately specific. No section directs Codex to fabricate missing inputs, inflate a confusion matrix, or claim full reviewer-point-5 satisfaction.

Four targeted corrections are required before implementation. Two are evidence-based factual corrections; two are clarifications that prevent ambiguity during implementation.

---

## C1 — Supplement page count (Section 1): active baseline is 18, not 19

**Plan location:** Section 1, line 9:
"Accepted output is 25 main pages including references and 19 separate supplement pages. Supplement 19 pages is an observation, not a hard cap."

**Evidence:** STATUS.json field matched_comparison_completion.supplement_pages = 18. The I2 adoption PDF is the active baseline; its supplement is 18 pages. The value 19 appears only in the pre-adoption reviewer package build (reviewer_I2_20261025_01/builds/r03/BUILD_RESULT.json, reviewed in Antigravity-0308), which predates the final adoption rebuild. The adopted and active supplement is 18 pages.

**Correction:** Replace "19 separate supplement pages" with "18 separate supplement pages" in Section 1 and Section 9.6. Retain the parenthetical that supplement page count is an observation, not a hard cap — that is correct.

---

## C2 — Verifier input availability (Sections 2.7 and 6): result object confirmed to lack prompt bytes

**Plan location:** Section 2.7 (lines 23–24) and Section 6 (lines 86–100).

**Evidence:** B001.json (inspected in full). Each per-arm result object contains: answer, composite, dropped_ids, retained_ids, judges[] (faithfulness, outcome, rationale), and verifier (reason, sufficient). The verifier.reason field is the verifier's own self-reported rationale, not the input prompt bytes or the retrieved-context text sent to it. There is no verifier_prompt, context_text, or request body in the result object. The verifier input text is present only in calls.jsonl (2.75 MB) and events.jsonl (74 MB) in the attempt/results/ directory.

**Implication confirmed:** The plan's Section 2.7 warning ("they do not contain the complete verifier prompt/context in that result object") is accurate and must be implemented strictly. False-rejection and false-acceptance rates cannot be computed from the result JSON files alone. Any per-query verifier audit must trace input bytes from calls.jsonl/events.jsonl with a frozen hash.

**No correction to plan text needed.** However, I recommend adding one explicit field to the I6.1 VERIFIER_FEASIBILITY.json output spec: verifier_input_source with value calls_jsonl / events_jsonl / not_found per query arm, and a byte-offset or record-key rather than re-extracting from the result object. This prevents an implementer from treating verifier.reason as the sufficient sufficiency reference.

---

## C3 — 40-query sample frame: unequal category sizes require explicit inclusion probabilities

**Plan location:** Section 7, line 106:
"freeze 40 unique matched-study queries, 10 from each A/B/C/D category, selected once by seeded sampling without replacement (seed 42) from the authenticated 350-query frame"

**Evidence:** ANALYSIS_RESULTS.json summaries:
- Category A: 100 queries (all EASY)
- Category B: 100 queries (all HARD)
- Category C: 75 queries (61 HARD, 14 EASY)
- Category D: 75 queries (72 HARD, 3 EASY)

Total: 350. Sampling 10/100 from A and B versus 10/75 from C and D yields unequal inclusion probabilities (0.10 vs. 0.133). The plan already acknowledges design weights in its final paragraph of Section 7, but the sample frame description does not make this explicit before the code is written.

**Correction:** In Section 7, line 106, add after "from the authenticated 350-query frame": "(inclusion probabilities: 10/100 = 0.10 for A and B; 10/75 approximately 0.133 for C and D; record per-stratum inclusion probability in SAMPLE_FRAME.json before any comparison)." This prevents the extractor from treating all 40 selected queries as equal-probability draws when reporting sample-descriptive findings.

---

## C4 — Category B refusal interpretation: confirmed event count, not false-refusal evidence

**Plan location:** Section 2.6, line 23:
"Category B verifier-triggered refusals 69T/4H are established event counts, not evidence of 69 false refusals."

**Evidence confirmed:** ANALYSIS_RESULTS.json Category B: T_refusals: 69, H_refusals: 4, 100 pairs, all HARD. B001.json shows T-arm outcome EXPLICIT_ABSTENTION (faithfulness 1.0) and H-arm MIXED_OR_UNCERTAIN (faithfulness 0.5). A T_refused: true entry earned the highest faithfulness score; it is a justified abstention, not a false refusal.

**No correction needed.** Confirmed accurate. Recommend noting B001 as a worked example in I6.1 RUBRIC.md, illustrating that T_refused: true plus high judge faithfulness cannot be reclassified as a verifier false rejection without a separate external sufficiency reference that survives the Section 6 feasibility test.

---

## D1 — User-dependent decision: open legal-interpretation queue policy

**Plan location:** Section 8 I6.4, line 148:
"Escalate new research needs explicitly; do not stall the whole audit seeking unavailable experts."

**Decision needed:** The plan permits an ASSESSOR_DECISION_QUEUE.md output only if genuinely needed, but does not define who closes that queue or what happens if items remain open at I6.5. The user should decide before I6.4 starts whether: (a) open legal-interpretation items are left explicitly unknown and closure proceeds with restricted claims, or (b) a specific assessor (Author 1 or Author 2, within the existing nonexpert/AI-assisted scope already established) may be asked to supply a bounded additional set of decisions. The plan correctly prevents Codex from resolving legal questions autonomously. This is a scope boundary requiring user designation.

---

## D2 — User-dependent decision: I6.6 supplement section placement

**Plan location:** Section 8 I6.6, line 158:
"place detailed definitions, denominators and source-check limits in existing supplement sections or new labelled inputs as needed."

**Decision needed:** supplement_assessment.tex already holds the 4-column ratings table. I6 will add verifier feasibility findings and source-check summary findings. The user should decide before I6.6 whether these go into supplement_assessment.tex as additional paragraphs, into a new supplement section file, or into a new named appendix file. This determines whether supplement_assessment.tex is one of the 46 protected source files that changes (requiring renewed peer review of that file's changed pages) or whether a new file is added instead.

---

## Verified constraints confirmed accurate

| Plan claim | Evidence | Verdict |
|---|---|---|
| 152 rows = 76 per author; 14 amendments; AI-assisted nonexpert; originals unchanged | ratings_only_results_20261012_01/REPORT.md | CONFIRMED |
| supplement_assessment.tex reports non-refusal coverage, yield, contradicted with author denominators; excludes population inference | supplement_assessment.tex (14 lines, viewed in full) | CONFIRMED |
| Matched study 350 pairs; Category B primary; frozen p-value from paired randomization | ANALYSIS_RESULTS.json lines 1–96 | CONFIRMED |
| Result objects contain answer/composite/judges/verifier(reason,sufficient); do not contain verifier prompt bytes | B001.json (inspected in full) | CONFIRMED |
| Closure rules 1–7 distinguish bounded audit completion from full reviewer-point-5 satisfaction | Plan Section 9 | CONFIRMED — no logical contradictions |

---

## Summary table

| ID | Type | Required before | Action |
|---|---|---|---|
| C1 | Factual correction | I6.0 start | Change "19" to "18" supplement pages in Section 1 and Section 9.6 |
| C2 | Implementation note | I6.1 draft | Add verifier_input_source field to VERIFIER_FEASIBILITY.json output spec |
| C3 | Clarification | I6.2 extractor code | Add per-stratum inclusion probabilities to Section 7 sample frame spec |
| C4 | Positive confirmation | I6.1 RUBRIC.md | Note B001 as worked illustration of abstention not equal to false refusal |
| D1 | User decision | Before I6.4 start | Designate open legal-interpretation queue resolution policy |
| D2 | User decision | Before I6.6 start | Designate placement of new I6 supplement findings |

C1 and C3 are binding corrections before implementation begins. C2 and C4 are implementation quality recommendations. D1 and D2 are genuine user-scope decisions; Codex should not resolve them by default.

Subject to C1 and C3 corrections being applied to the plan, the I6 implementation plan is scientifically sound and ready for implementation authorization.

Antigravity does not grant implementation permission. That authority rests with the user.
