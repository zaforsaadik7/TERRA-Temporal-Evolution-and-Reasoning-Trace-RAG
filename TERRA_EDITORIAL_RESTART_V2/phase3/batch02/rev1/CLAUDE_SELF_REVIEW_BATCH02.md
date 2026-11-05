# Claude's own review of the Batch 02 proposal, and rev1

- **Author:** Claude. **Date:** 2026-10-05.
- **Why this exists:** the user asked Claude to review Batch 02 itself and recommend approve or decline, because Codex is out of usage. Claude wrote the proposal, so this is **not** an independent audit. It checks the proposal against the raw data, not against Claude's own earlier outputs. Codex should still audit it when available.
- **Status:** nothing is applied. The working source is unchanged (hashes re-verified: main.tex 2ddb18a7…, table_citation_eval.tex 73c50145…).

## What was re-checked independently

| Check | Result |
|---|---|
| Apply script run on the real device bytes (check-only) | Passes. The diff is byte-identical to the proposed one, and the planned hashes are reproduced. |
| Diameter and average shortest path | Recomputed with exact BFS from every node of the largest weakly connected component (18,558 nodes) of the active graph (7aa6db46, 145,366 edges): **diameter 13, ASPL 4.30495 → 4.305.** This does not use Phase 1's output. |
| Citation F₁ and ratios | The frozen macros match Phase 1: 16.02 / 15.02 / 21.15 / 12.17, ratios 1.07 / 0.76 / 1.32. TERRA is below Flat Vector RAG. |
| Category C | From the raw v2 data: 75 TERRA probes, **0** contain a /case/ link, and **74** have empty retrieved context. |
| Broken links | The paper's 4 comes from the project's own validator. This review found a **wording problem** (see below). |
| Other stale values | A search of main.tex, tables and figures finds no remaining 15 hops, 4.713, 20/20, 47.8, 1,042, 72/75 or "Harmonic". The surviving 5/5 values are in the labelled historical-sensitivity rows, which are not in scope. |

## Problems found (all in Claude's own draft or in adjacent text)

1. **B2-5 and B2-7 wording would mislead.** The draft said 4 links "do not resolve as written". The project's validator (scripts/audit_citation_correctness.py) accepts a link if its identifier exists, or if its URL text or anchor caption equals an indexed title or alias. By that rule 660/664 pass, but only **644/664 (97.0%) have an identifier that exists as written**, and 16 more are accepted on caption match. The paper's "resolve directly to authentic opinion nodes" overstates this. Rev1 states the validator rule and discloses 644/664.
2. **B2-6** said the containment reflects empty retrieval. That holds for 74 of the 75 probes, so rev1 says "largely".
3. **New B2-8 (R10-7, HIGH in the Phase 1 register).** The Doctrinal Support Precision bullet calls Flat Vector RAG's 14.15% a baseline weakness against TERRA's 9.30%. On this judge-weighted metric Flat is the highest. Rev1 states the ordering. It says "judge-weighted" so it does not contradict the earlier sentence where TERRA leads on the grounded variant.

## Recommendation

| Item | Recommendation |
|---|---|
| B2-0 override include | **Approve** (needed for B2-1 and B2-2) |
| B2-1 Table III 15 → 13, 4.713 → 4.305, labels | **Approve** |
| B2-2 5-node CI [0.5%, 71.6%] | **Approve** |
| B2-3 seed-anchoring rewrite | **Approve** |
| B2-4 citation F₁ with direction | **Approve** |
| B2-5 hyperlink item | **Decline the original; approve the rev1 version** |
| B2-6 Category C item | **Approve the rev1 version** ("largely") |
| B2-7 table note † | **Decline the original; approve the rev1 version** |
| B2-8 doctrinal precision (new) | **Approve** (corrects a text-versus-number contradiction) |

**Overall: approve rev1 as a whole.** Every item corrects a confirmed stale or wrong value, or an overstatement, and none removes an adverse result. The changes make three adverse findings more visible (Flat's F₁ and doctrinal precision above TERRA's, and the stricter 97.0% link match).

## Rev1 verification

- Check-only and real apply on a scratch copy of the device source both pass. Planned hashes: main.tex `af093e96eeaf6fe76cd7fc1e0838b7bbf88ae8910ed83bd35ce86862bde8aa55`; table_citation_eval.tex `9abd10843c3bb3a6d97fe42557d022f604408008439376e5b13016ac074dae78`. Line endings are preserved (1,111 → 1,112 CRLF; 16 bare LF unchanged; table 40 CRLF).
- Facts: the original 9 of 9 VERIFIED plus 4 of 4 new (B2R-F01..F04).
- Build in the sandbox: 39 pages, 0 undefined references. One overfull box was already present in the first dry run. The strings "resolve directly", "achieving only", "1,042" and "20/20" do not appear in the PDF.
- Rendered pages 29 and 30 were viewed and read correctly.

## Not fixed here (flagged for later batches)

- The Panel A table row for TERRA is bold in every column, including F₁, Doctrinal CP and Entity CP, where TERRA is not the best.
- R10-9: TERRA has the lowest Entity CP (74.25% against 89–90%) and the text does not say so.
- R10-8 (which citation metric is primary) and R10-15 (the provenance wording for the retrieval source).
- The 5-node paragraph still says "topological feasibility" beside the new CI [0.5%, 71.6%]. It is hedged as descriptive, but it could be narrowed further.
