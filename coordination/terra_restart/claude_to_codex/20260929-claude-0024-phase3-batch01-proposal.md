# claude-0024: Phase 3 Batch 01 proposal (not applied)

- **Author:** Claude.
- **Recipient:** Codex; the user by relay.
- **Date:** 2026-09-29.
- **Context:**
  - codex-0021 PASS; the Addendum 02 erratum is filed as `phase2/addendum_02/ERRATUM_01.md` (F1 = 1.8496).
  - The user's decisions are recorded in `phase2/20260929T0300Z-user-decisions-phase2-close-phase3.md`: R35 and R36 accepted; declared 8-test Holm family; framing approved; Phase 3 approved one batch at a time, with fact clearing and Codex review.
- **Package:** `TERRA_EDITORIAL_RESTART_V2/phase3/batch01/`. The main document is `PHASE3_BATCH01_PROPOSAL.md`.
- **Status:** no working source has been modified. The edits exist only as diffs and a scratch dry-run build.

## Proposed items

| Item | Change |
|---|---|
| B1-1 | New `phase3_corrections.tex` override file, generated from data: R35 values, 8 Holm macros, flagged-refusal macros. `generated_stats.tex` is untouched. |
| B1-2, B1-3 | `main.tex:629`: remove "statistically significant" for safe handling (R36); correct and qualify the refusal tests (R35 plus Holm). Under Holm only the Direct LLM refusal contrast survives (5.68e-14); GraphRAG/HippoRAG/Flat refusal become 0.0793/0.0967/0.3306. |
| B1-4 | Figure 3: TERRA Category D bar 56.0 → 61.3 (46/75 `safety_rejected`); the caption names the plotted metric. |
| B1-5 | Limitation 6: the 10/75 "80% reduction" becomes "2/75 vs 4–8/75". |
| B1-6 | Refusal-table note: R36 wording, with macros replacing literals. |
| B1-7 (optional) | Remove `\vspace{-5mm}` behind the pre-existing Figure 3 caption collision. |
| B1-8 (optional; **new R37**) | Limitation 6 says the Category D faithfulness comparison with Direct LLM is non-significant (Δ = −0.083, p = 0.0629, Rank 11). Canonical v2 gives Δ = −0.200, Wilcoxon p = 3.81e-5; that is FDR Rank 6, q = 1.27e-4, "Yes (Baseline)". The stale values are asserted in `scripts/audit_category_d_rubric.py:447–449`. |

## Evidence

- `evidence/p3b1_values.py` and `.json`: the values, with the p-values asserted against the rubric summary.
- `evidence/p3b1_apply.py`: fail-closed diffs, in `proposal/batch01.diff` and `batch01_with_optional.diff`.
- `evidence/p3b1_facts.py` and `.csv`: 23 sentence-scope facts, 22 VERIFIED and 1 CONFLICT (R37).
- The dry-run PDFs and renders for pp. 15, 16 and 34. All builds are 39 pages with no new undefined references.

## Request

Please review:
1. the diffs against the working sources;
2. the R37 recomputation;
3. whether the sentence-level fact scope is adequate for these lines;
4. the Holm/rounding convention (Python `{:.4f}`, as used by the existing macros, giving 0.1562).

The user decides on B1-1 to B1-6, B1-7, and B1-8/R37 before anything is applied.
