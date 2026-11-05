# Phase 3 Batch 10 proposal: discussion, results and conclusion overclaims; Batch 08 leftovers (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Basis:** R03 claim matrix claims C27, C29, C33, C37, C39 (and C40 in scoped form), plus the leftovers from Batch 08 and one related-work sentence. Claude-only review, **not independent**.
- **Pre-state:** Batch 09 post-state, `main.tex` `a24fbce1…`. Only `main.tex` changes. Apply script `evidence/p3b10_apply.py` is fail-closed (pre-hash, each edit exactly once, 10 stale-string assertions, `--check-only`).
- **Nothing has been applied.** Each item needs your approval. Your "approve" arrived before this proposal existed, so I treated it as a go-ahead to draft only.

## Items

| Item | Claim | Change |
|---|---|---|
| B10-1 | C27 Discussion opener | "validates that TERRA addresses fundamental failure modes" becomes a statement of where TERRA helps (Category B retrieval coverage, out-of-domain refusal) and where it does not (Category B faithfulness against Direct LLM; obscure precedents without curated labels). |
| B10-2 | C29 | "Three core design innovations drive TERRA's performance" becomes "Three design choices distinguish TERRA (examined only in a 35-query pilot ablation)". |
| B10-3 | C33 | "Removing NLI in ablation reduced adversarial safety to 0.0%, so the grader is necessary" now names the pilot: 35-query pilot, safety scored as refusal, five Category D queries, "necessary there". |
| B10-4 | C37 Conclusion | "Citation graphs grounded with procedural traces preserve longitudinal stability" becomes "In a standalone traversal test over four snapshot expansions, pooled recall shifted by 0.03 +/- 0.16" (existing macro). |
| B10-5 | C39 Results | "These findings confirm ... fundamentally anchored in direct evidence retrieval quality" becomes "We did not test causally whether TERRA's results stem from retrieval quality; Direct LLM's higher Category B faithfulness shows retrieval alone does not explain faithfulness." |
| B10-6 | Batch 08 leftover | "Independent critic scoring utilizes" becomes "Dual-judge scoring uses". |
| B10-7 | Batch 08 leftover | "the LLM judge as a full substitute" becomes "the LLM judges". |
| B10-8 | Batch 08 leftover (80B check) | "confirmed invariant relative rankings" becomes "gave the same system ordering on this small subset (no statistical test; not re-verified)". |
| B10-9 | Related work (~l.141) | "Because standard retrievers rely on lexical matching, they flood the context window... current systems lack the genuine NLI capabilities" becomes "Retrievers that rank by lexical or embedding similarity can return overruled precedents alongside current ones without marking which has been overturned. These findings motivate an explicit entailment check, tested below." |
| B10-10 | C40 (scoped) | "Grounding generations on authentic graph subgraphs completely eliminates phantom case inventions" becomes "In the audited CLERC completions we found no fabricated case captions". |

## Checks

- **Facts** (`evidence/p3b10_facts.py`, `.csv`): 4 of 4 VERIFIED. Direct LLM Category B faithfulness 0.335 vs TERRA 0.254 (canonical v2, 350 per pipeline); the recall macro exists; the ablation Category D set is 5 unique queries on the 35-query pilot; all referenced labels exist.
- **Page count:** my first wording grew the paper to 40 pages (the references spilled onto a new page); the edits were tightened and the build is back to **39 pages**, 0 undefined references, 2 pre-existing overfull boxes. This is fragile: any later text growth near the appendix reflows the pages, which Phase 4 will change anyway. `main.tex` CRLF 1,105 to 1,105, bare LF 16 to 16. Planned hash `fe5e235a…`.
- **Rendered pages:** `render/dry_p29-29.png`, `dry_p33-33.png`, `dry_p37-37.png` (results, discussion, conclusion) viewed; all edits read correctly.

## Caveats

- **B10-3** carries the "safety scored as refusal" and "five queries" facts from Phase 1 (R18); the five-query count matches the paper's own macro, the scoring definition was not re-verified.
- **B10-8:** the 80B subset numbers (1.000 vs 0.900 vs 0.800; 100% vs 40% vs 0%) are unchanged and remain unverified (R22 is blocked); the edit only drops the word "confirmed".
- **B10-10:** the underlying 0/120 fabrication audit was not recomputed (eyecite unavailable, disclosed in Batch 06). The edit narrows the claim and states no new number, but it still relies on that audit. Decline it if you prefer to wait.
- Not included: C07, C17, C20, C21, C24, C28, C30-C32 (supported with qualification), and the other open register items.

## Decision requested

Approve or decline B10-1 to B10-10. Recommendation: approve all; each narrows a claim to what the paper measures, and none removes an adverse result.
