# Phase 3 Batch 05 proposal: latency populations, chain-length wording, citation-metric disclosure and provenance (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Review status:** Claude self-review only (not independent); Codex must audit it later.
- **Basis:** Phase 1 R19, R10-8, R10-9, R10-14, R10-15, and the Panel A bolding noted in the Phase 3 queue.
- **Pre-state:** the Batch 04 post-state: `main.tex` `d9a10dc9…`, `table_retrieval_eval.tex` `9155c312…`, `table_citation_eval.tex` `9abd1084…`. The apply script checks all three and fails closed.
- **Scope:** wording and bolding only, in the isolated working source. No new numbers are typed in: every figure is an existing macro. No experiments.

## Raw-data facts (`evidence/p3b5_facts.py`, 7 of 7 VERIFIED)

1. The 5.83 s and 17.94 s medians are Category A and Category B gross medians. The route medians are 5.46 s (fast route, n=110) and 14.07 s (hard route, n=240). The old text called the former "fast/hard path".
2. The 1.38 s and 4.90× figures come from the 10-query pilot ablation. They are only labelled here, not re-derived (no pilot raw data was re-run).
3. Gold chains have 3, 4 and 5 nodes (63/32/5), which is 2, 3 and 4 hops. TERRA's full-path recovery is 49/63 (77.8%), 16/32 (50.0%) and 1/5 (20.0%), so it is not "invariant".
4. In Panel A the best value is Direct for Entity CP, Flat for Doctrinal CP and Citation F1, and TERRA for macro/micro recall and full paths. TERRA has the lowest Entity CP (74.25% against 89.10–90.27%).
5. The retrieval and citation numbers reproduce from the canonical v2 file (sha256 prefix `95e775e2`, confirmed), not from `terra_baselines_eval_raw.json` as the text said (Phase 1 recomputation).

## Items

| Item | Where | Change |
|---|---|---|
| B5-1 | Introduction (l.118) | "median 5.83 s on single-point factual lookups vs. 17.94 s on multi-hop chains" now says gross medians for Category A and Category B. |
| B5-2 | Section III (l.206) | "4.90× operational speedup" is marked as being in the pilot ablation. |
| B5-3 | Ablation 3 item (l.529, 2 edits) | The pilot is named. "fast sub-two-second execution" is replaced by the pilot's 1.38 s beside the canonical fast-route median 5.46 s, with a note that the populations are not comparable. |
| B5-4 | Router section (l.638) | "Ablation 3 … 4.90× penalty" is marked as a pilot result. |
| B5-5 | Chain-length item (l.811) | "Hop-Length Invariance … 3, 4, 5 hops, invariant performance" becomes "Chain-Length Dependence": 3, 4 and 5 nodes (2 to 4 hops) with the recovery rates, and no "invariant". |
| B5-6 | Retrieval provenance (l.899 and the table_retrieval_eval note) | The source is the canonical v2 evaluation file (sha prefix `95e775e2`) instead of `terra_baselines_eval_raw.json`. "guaranteeing zero retrieval drift" becomes "scored on the context the generator actually received". |
| B5-7 | `table_citation_eval` note | Entity CP now discloses that TERRA has the lowest value. Doctrinal CP is described as a judge-weighted measure, not an NLI entailment test; "certified as doctrinally entailed … pre-registered" and the raw-file name are removed. |
| B5-8 | `table_citation_eval` Panel A | The row-wide bold on TERRA is removed from the three cells where it is not best (Entity CP, Doctrinal CP, Citation F1). The best value is bolded there instead (Direct, Flat, Flat). TERRA's other cells keep their bold. |

## Dry run (scratch copy of the post-Batch 04 source)

- Build: 3 passes, **39 pages**, 0 undefined references, 2 overfull boxes (pre-existing).
- Stale strings in the sources ("sub-two-second", "Hop-Length Invariance", "invariant relative performance", the raw-file name, "certified as doctrinally entailed", "zero retrieval drift"): 0 left.
- Line endings unchanged: `main.tex` 1,107 CRLF and 16 LF; both tables fully CRLF.
- Expected hashes after apply: `EXPECTED_POST_HASHES.sha256`.
- Rendered pages viewed: p. 30 (table note and Panel A), with pp. 14 and 23 rendered too. The note reads correctly. Table XX Panel A is still very small; that layout debt is out of scope here.

## Recommendation

**Approve all 8 items.** Each replaces a mislabelled population, an inaccurate source name or an unsupported claim ("invariant", "certified entailed") with the measured value, and B5-7 and B5-8 make an adverse result (TERRA's low Entity CP) visible.

## Decision requested

Approve or decline each item (B5-1 to B5-8). Nothing has been applied; approval covers the isolated working source only.

## Still open after this batch

R09 (CaseFacts/CLERC), R21 (bibliography), the Table IX layout, the unfixed overfull boxes and tiny figure labels, and Phase 4 (cutting 39 pages to 25).
