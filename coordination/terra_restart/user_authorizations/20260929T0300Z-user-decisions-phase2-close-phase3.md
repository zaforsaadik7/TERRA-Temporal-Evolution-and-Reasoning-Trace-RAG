# User decisions: Phase 2 close and Phase 3 authorization

- **Recorded by:** Claude.
- **Date:** 2026-09-29.
- **Source:** the user's answers to the structured decision prompt, given after codex-0021 (Addendum 02 PASS). The answers are quoted verbatim.

| Question | User's answer (verbatim) |
|---|---|
| R35 / R36 | "Accept both (Recommended)". Both are accepted as correction findings; the values change only in Phase 3. |
| Category D multiplicity | "Declared 8-test family (Recommended)". Exact p-values plus Holm-adjusted values across all eight McNemar tests (4 refusal + 4 safe-handling), treated as a secondary family. |
| Framing | "Approve as proposed (Recommended)". This approves RQ1–RQ3, the three contributions (Addendum 01 §5) and narrow-and-disclose for R05, R06 and R12, with the missing-validation limitations kept visible and no new experiments. |
| Phase 3 | "I approve Phase 3 under those conditions". |

**The conditions of the Phase 3 approval**, as stated in the question:
- the work is applied one batch at a time;
- each batch clears its own blocked facts;
- each batch returns for a Codex source-diff and PDF review.

**How Claude will run Phase 3.**
- For each batch, Claude first proposes the exact diffs and stops for review before applying them. This was stated in the option text the user was shown.
- The graph, data and generated-statistics files stay untouched. Any value correction is bound through a separate, auditable override file.
- All writing is append-only.
- No experiments are run.
- All 18 limitations are kept.
