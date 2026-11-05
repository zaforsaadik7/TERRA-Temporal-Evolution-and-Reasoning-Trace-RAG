# Phase 3 Batch 09 proposal: introduction, abstract and related-work overclaims (R03) (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Basis:** R03 claim matrix (`evidence/phase1/R03_R18_R21_R23/claim_matrix.csv`), claims C02, C08, C09, C10, C11, C13, C14, C15, C16, C19, C25, C26. Claude-only review, **not independent**.
- **Why these first:** they are the OVERCLAIM/UNSUPPORTED sentences in the abstract, introduction, contributions and related work, which the later 25-page cut will rewrite. Corrected text means the cut starts from supportable wording.
- **Pre-state:** Batch 08 post-state, `main.tex` `b848d575…`. Only `main.tex` changes, no override file. Apply script `evidence/p3b9_apply.py` is fail-closed (pre-hash, each edit exactly once, 14 stale-string assertions, `--check-only`).
- **Nothing has been applied.** Each item needs your approval.

## Items

| Item | Claim | Change |
|---|---|---|
| B9-1 | C02 (+C01) abstract | Fast path described as "lighter" (retrieval and an entailment check, without graph traversal); grader called "LLM-prompted" instead of "autonomous semantic". |
| B9-2 | C08 intro | "inevitably accumulate / surface all versions / induces severe temporal hallucinations / proving entirely insufficient" becomes "can accumulate / may surface several / can lead it to state outdated law / limits their usefulness", plus one sentence that these mechanisms motivate the design and are not measured in isolation. No new citation. |
| B9-3 | C09 intro | "SHAP analyses have proven that standard evaluators act merely as..." becomes the single finding it rests on (CRAG T5 evaluator relies primarily on named-entity alignment), cited to Yalavarthi (already in `ref.bib`). The preceding "fail fundamentally on conceptual tasks" is softened to "may not capture conceptual relevance". |
| B9-4 | C10 intro | "existing query routers are largely restricted to rigid, binary-channel systems" becomes "many hybrid systems route between a small fixed set of channels; adaptive multi-strategy routing is emerging" (Hashmi, already cited, which contradicts the old claim). |
| B9-5 | C11 intro | Router described as implemented: classifies each query EASY or HARD, selecting the fast path or citation-graph traversal (not "dynamically allocating priority across chunks, subgraphs and traces"). |
| B9-6 | C13 intro | "replaces flawed heuristics, verifying the true conceptual relevance" becomes "LLM-prompted entailment grader decides whether evidence is sufficient; accuracy not independently validated". |
| B9-7 | C14, C15, C16 intro | "rigorously evaluated ... comprehensive benchmarks", "significantly mitigates attention dilution" and "substantially reduces temporal hallucinations" replaced with: four baselines on 350 queries plus a 35-query pilot ablation; attention and context-length effects not tested, and TERRA's mean context is longer (about 18,400 vs 2,900-4,100 chars); in the 50-query leakage probe TERRA did not leak less than Flat RAG (preregistered H1 not supported; Flat refused 23/50) but was more historically correct (76.0% vs 38.0%). |
| B9-8 | C19 contribution 3 | "specialized NLI grader" becomes "LLM-prompted entailment (NLI-style) grader"; adds that interception reliability is not validated beyond a 5-query pilot. |
| B9-9 | C25, C26 related work | "routers rely on superficial keyword-matching that triggers catastrophic failure" becomes "many routers select among a small set of retrieval channels"; "ensures ... semantically aligned pair" and "continuous three-way router" become "retrieves each node with its structured trace" and "binary router selecting a fast path or traversal". |

## Checks

- **Facts** (`evidence/p3b9_facts.py`, `.csv`): 5 of 5 VERIFIED against raw data: mean context lengths, fast-route timings on 100/100 Category A rows, Flat RAG 23/50 refusals, HLCR macros 76.0% and 38.0%, citation keys present. (One first-run conflict was my wrong field path for the timing columns; fixed, values unchanged.)
- **Dry run:** XeLaTeX, 3 passes, 39 pages, 0 undefined references, 2 overfull boxes (pre-existing). The 14 stale strings are absent. `main.tex` CRLF 1,105 to 1,105, bare LF 16 to 16. Planned hash `main.tex` `a24fbce1…`.
- **Rendered pages:** `render/dry_p1-01.png`, `dry_p2-02.png`, `dry_p3-03.png` viewed (abstract, introduction, contributions, related work); no overflow.

## Caveats and not included

- The H1 and HLCR statements restate what the temporal-leakage section already says; no new analysis.
- Not included, for Batch 10: C27, C29, C33, C37, C39 (discussion and results overclaims); C40 ("completely eliminates phantom case inventions"), which depends on the CLERC fabrication audit that was not recomputed; the leftover Batch 08 sentences ("Independent critic scoring", singular "LLM judge", 80B sensitivity claim); the related-work sentence at ~l.141 ("standard retrievers rely on lexical matching... flood the context window"); and C07, C17, C20, C21, C24, C28, C30-C32 (SUPPORTED-WITH-qualification items).

## Decision requested

Approve or decline B9-1 to B9-9. Recommendation: approve all. Each narrows a claim to what the paper measures, and none removes an adverse result (B9-7 makes two adverse findings more visible).
