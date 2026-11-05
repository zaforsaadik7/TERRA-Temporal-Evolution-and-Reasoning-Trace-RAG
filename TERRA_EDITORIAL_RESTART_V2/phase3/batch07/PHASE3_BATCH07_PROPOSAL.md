# Phase 3 Batch 07 proposal: bibliography corrections and citing-sentence fixes (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Review status:** Claude self-review only (not independent); Codex must audit it later.
- **Basis:** Phase 1 R21 (with R03 where a citing sentence overclaims). The Phase 1 findings were re-read against the publisher pages today (`proposal/p3b7_source_checks.csv` lists every page read).
- **Pre-state:** the Batch 06 post-state: `main.tex` `bf435feb…`, `ref.bib` `cbde3195…`, `main.bbl` `7be341df…`. The apply script checks all three and fails closed.
- **Scope:** `ref.bib` metadata, the matching sentences in `main.tex`, and the regenerated `main.bbl`. No reference is added, and none is invented: every correction comes from a page read today. No experiments.
- **Note on your last message:** "yes I approve all" arrived as the answer to my question whether to draft this batch, before any edit existed. I have treated it as a request to draft, not as approval of the edits. Please approve below.

## Items

| Item | Where | Change |
|---|---|---|
| B7-1 | `ref.bib` metadata | Think-on-Graph: correct title and the 9 real authors (the bib listed four non-authors). Self-RAG: correct authors (the bib listed the authors of a different paper). Hoenig and Heisey: title corrected. CLERC: pages 7913–7928 and the published title ("U.S."). GraphRAG: adds the two omitted authors. Judging LLM-as-a-Judge: Datasets and Benchmarks track. LegalGraphRAG: adds pages. |
| B7-2 | `ref.bib` venues | Five arXiv-only entries become the published versions: E2RAG (EACL 2026), Chronos (Findings of ACL 2026), CoT-RAG (Findings of EMNLP 2025), the System 1/2 survey (Findings of IJCNLP-AACL 2025), HippoRAG (NeurIPS 2024). Authors and titles keep the arXiv form except where the publisher title differs (E2RAG, singular "Knowledge Graph"). |
| B7-3 | `main.tex` Related Work (9 edits) | Chronos is described as a knowledge-drift benchmark plus a time-aware method. LegalGraphRAG is described as a Researcher/Auditor/Adjudicator system over a hierarchical legal graph; the unsupported "tripartite … statutory civil and criminal law" is removed and the contrast with statutory systems is softened. The CoT-RAG claim is reduced to what its abstract reports (4.0% to 44.3% gains). CLERC is described as case retrieval and analysis generation, and the claim that the benchmarks "confirm" retrievers surface superseded authority is replaced by "as we read them, neither benchmark specifically targets superseded or overruled authority". The CRAG paragraph drops "mathematically proving", the unverified 88.3% and 5.0% figures, and "fundamentally flawed". The faithfulness-judge citation moves from RIKER (a different method) to Zheng et al. The CLERC acronym expansion is dropped. The closing sentence no longer cites GraphRAG, Think-on-Graph and Judging LLM-as-a-Judge for an unrelated stability claim. |
| B7-4 | `main.bbl` | The BibTeX output of the new `ref.bib`, so a build without a BibTeX pass still shows the corrected list. The dry-run build regenerates it identically. |

## Checks

- **Mechanical** (`evidence/p3b7_checks.py`, 5 of 5 VERIFIED): the same 27 keys; every cited key exists; only the intended citation changes (RIKER removed, and the closing citations of GraphRAG and Think-on-Graph removed); BibTeX reproduces the delivered `main.bbl` exactly with 0 warnings; the RIKER entry stays in `ref.bib` but is now uncited.
- **Dry run:** 39 pages, 0 undefined references or citations, 2 overfull boxes (pre-existing). Line endings preserved (`ref.bib` all CRLF; `main.tex` 1,108 CRLF and 16 LF; `main.bbl` LF as before).
- **Pages viewed:** p. 3 (the edited related-work paragraphs) and p. 39 (the reference list), both correct. The reference list's odd two-column balance (a gap above the first column) is identical in the baseline and is added to the layout debt.
- Expected hashes after apply: `EXPECTED_POST_HASHES.sha256`.

## Not done, with the reason

- **Hashmi (adaptive routing):** the arXiv page returned a rate-limit refusal and was not fetched again, so the sentence is unchanged and unverified.
- **Lin et al. author list:** the arXiv page does not show the full list, so the repeated "Hui Liu" is unresolved.
- **Hoenig and Heisey:** the publisher page returned 403 and was not bypassed. The title correction rests on the Phase 1 record and a search result showing the same title.
- **Judge model named on the faithfulness line:** the line still names the Llama critic. That belongs to R06 (judge protocol), a separate batch.
- **Other sentences that overclaim** ("current systems lack genuine NLI capabilities", standard retrievers "flood the context window with noisy, overruled precedents") belong to R03.
- **Additional related work:** Phase 1 suggested some verified additions. Adding them changes the paper's argument and adds pages, so it is deferred until after the 25-page cut.

## Recommendation

**Approve all four items.** B7-1 and B7-2 correct factual errors in the bibliography against the publisher pages; B7-3 replaces claims the sources do not make; B7-4 keeps the compiled list in step.

## Decision requested

Approve or decline each item (B7-1 to B7-4). B7-4 needs B7-1 and B7-2. Nothing has been applied; approval covers the isolated working source only.

## Still open after this batch

R06 (judge protocol), R03 (the other overclaims), the Table IX layout and other layout debt (now including the reference-column balance), and Phase 4 (39 to 25 pages).
