# Phase 3 Batch 06 proposal: CaseFacts and CLERC wording, labels and bolding (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Review status:** Claude self-review only (not independent); Codex must audit it later.
- **Basis:** Phase 1 R09 (R09-1 to R09-13), against the raw CaseFacts and CLERC files in `scratch/`.
- **Pre-state:** the Batch 05 post-state: `main.tex` `bd9485ee…`, `table_casefacts_eval.tex` `49cb5359…`, `table_clerc_eval.tex` `7a53168d…`. The apply script checks all three and fails closed.
- **Scope:** wording, labels and bolding only, in the isolated working source. New macros come from `evidence/p3b6_values.py`, which recomputes them from the raw files; no value is typed by hand. The frozen `generated_stats.tex` is not edited. No experiments, no scripts rerun that write protected files.

## Raw-data facts (`evidence/p3b6_facts.py`, 10 of 10 VERIFIED)

1. CaseFacts macro-F1 (TERRA 54.48 vs Flat 48.26, Direct 46.51) comes entirely from the Overruled class (n=8). Over Supported and Refuted alone TERRA is 53.16, Flat 55.72 and Direct 51.59. TERRA's Supported F1 is the lowest of the three and its Refuted F1 is below Flat's.
2. The table's "Micro-F1" column is accuracy with an out-of-corpus prediction counted as an error: TERRA 62/120, both baselines 64/120.
3. The Overruled intervals (4/8 versus 2/8) overlap heavily. The two judges agree on 120/120 labels and the "parsed label" equals the judge label, so the concordance is on an extracted label, not an independent legal judgement.
4. CLERC: TERRA's misapplication flags (OR 60, AND 45) are all among its 67 generated completions, so over generated completions the rates are 89.6% (60/67) and 67.2% (45/67); over all 120 they are 50.0% and 37.5%. Hits@10 are 13/120 versus 12/120 for Flat (one query). Citation F1: Direct 4.7%, TERRA 3.5%, Flat 1.8%. TERRA's judged soundness (1.98) is the lowest.
5. **Not recomputed:** the CLERC fabrication values (0.0%, 41.1%, 45.5%) and the in-corpus/external split (84.7%/15.3%) are literals in the project's metrics script, and `eyecite` is unavailable here. The edits disclose this rather than assert it.

## Items

| Item | Where | Change |
|---|---|---|
| B6-0 | `main.tex` preamble | Adds `\input{phase3_corrections_b6}` after the Batch 03 override, with the new macros: lifts written as "pp" (the old "+6.22%" was a percentage-point difference), the 2-class macros, accuracy counts, misapplication-among-generated and hits@10. |
| B6-1 | CaseFacts Track 1 text (4 edits) | "decisive generalization advantages" becomes "mixed". The Macro-F1 bullet is retitled and states that the gain comes entirely from the n=8 Overruled class, gives the 2-class macros and the lowest accuracy, and drops "lift". The Overruled "double the recall" gets "the intervals overlap, so this difference is not statistically significant". The 100.0% concordance is described as on labels parsed from each completion's header. |
| B6-2 | CLERC text (7 edits) | "decisive structural advantages" becomes a mixed summary (comparable retrieval, highest citation precision, lowest soundness). Hits@10 13 versus 12 is added. Direct LLM's highest Citation F1, TERRA's lowest soundness and "micro-pooled" are added. The fabrication paragraph discloses that its values were not recomputed. The misapplication rate is stated over all 120 and over the 67 generated (89.6% and 67.2%). "reliably halts" becomes "in these runs … halted generation before any citation was produced". |
| B6-3 | `table_casefacts_eval.tex` (6 edits) | "Micro-F1" becomes "Accuracy (OOC = error)". Footnote * uses pp and names the Overruled driver and the lower 2-class macro. Footnote ** adds the overlap statement. TERRA's bold is removed on Supported and Refuted F1 (not best); the best values (Direct, Flat) are bolded. |
| B6-4 | `table_clerc_eval.tex` (3 edits) | TERRA's bold is removed on ROUGE-L, Cite F1 and Soundness (not best), and Direct's are bolded. The note says the fabrication values are recorded literals not recomputed, defines the misapplication rate (all N completions, with the 67-generated rates) and says Cite F1 is micro-pooled. |

## Dry run (scratch copy of the post-Batch 05 source)

- Build: 3 passes, **39 pages**, 0 undefined references or missing items, 2 overfull boxes (pre-existing).
- Stale strings ("decisive generalization advantages", "decisive structural advantages", "Macro-$F_1$ Gains", "reliably halts", "Micro-$F_1$" header): 0 left.
- Line endings preserved: `main.tex` 1,107 → 1,108 CRLF (one new `\input` line) with 16 LF; both tables unchanged in style (LF only, as before); the override file is CRLF.
- Expected hashes after apply: `EXPECTED_POST_HASHES.sha256`.
- Rendered pages viewed: p. 24 (Table XVII and the Track 2 text) and p. 26 (Table XVIII and the CLERC bullets); both read correctly, with no overflow. Also rendered: p. 23.

## Recommendation

**Approve all of B6-0 to B6-4.** Each replaces an overstated or mislabelled statement with the figure the raw data gives, and none removes a result. The one disclosure-only item is the fabrication paragraph (B6-2 and B6-4): it keeps the 0.0% value but states that it was not recomputed. If you prefer a stronger fix, the alternative is to add a limitation sentence or recompute the audit with a committed script (a new analysis, so it is deferred).

## Decision requested

Approve or decline each item (B6-0 to B6-4). B6-1 to B6-4 need B6-0. Nothing has been applied; approval covers the isolated working source only.

## Still open after this batch

R09-6 (the Track 2 hard/disclosed split and baseline "disclosed" values are hardcoded; needs a script), R09-8 (a per-item macro F1 needs eyecite), R09-14 (verify "ACL 2026" against the bibliography), R21 (bibliography), the Table IX layout and other layout debt, and Phase 4 (39 → 25 pages).
