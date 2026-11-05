# Claude audit of Codex Phase 2 Batch 1 (F01 diagram, caption, dependent prose)

Author: Claude, 2026-10-08. Read-only; nothing in the manuscript, data, graphs, statistics, bundle or canonical files was changed.
**Independence limits.** Claude-authored; I wrote the Batch 1-28 text that Batch 1 edits around, and I audited Codex's Phase 1 findings that motivated it. This is not an independent audit. The user's approval, not this verdict, authorizes the next step. I did not rebuild the PDF (Tectonic is not available to me); I inspected Codex's build console and PDF.

## Verdict: PASS for the bounded Batch 1 scope. F01 is NOT closed across the package (supplement still stale). No correction to the patch is required; four non-blocking notes below.

## Reproduced by me
| Check | Result |
|---|---|
| Source hashes | `build/src/main.tex` 49107cfe…, figure 49599139…, PDF d9cbd392…, baseline main b950bc09…, baseline figure 55b1f120… all equal Codex's records. |
| Whole-tree diff baseline vs build | Only `main.tex` and `figure_1_system_architecture.tex` differ (tables, macros, frozen stats, bib identical, byte-compared; aux/log/pdf excluded). |
| main.tex line diff | Exactly lines 119, 145, 151, 580 (681 lines before and after). Token comparison of changed lines: no digit run or macro name added or removed except the caption's "Phase 1/2" labels replaced by `\texttt{}`. No number, claim or setting changed; no removal. |
| Figure diff | Edge box, scaffold box, router subtitle, HARD label, EASY box and one arrow only. |
| Page count / text | PDF 24 pages. Page text differs from baseline only on pages 1, 2, 3, 4, 18 (reflow of the lengthened caption and prose); 19 pages identical. |
| EASY path semantics | In `terra_canonical_v2_eval.json`, all 110 EASY-routed TERRA rows have retrieval_ms > 0 and grading_ms > 0 (10 are refusals). So "anchor retrieval, then entailment grading, no graph expansion" is supported; "No RAG / bypass" is gone. |
| Refusal wording | Caption says "refusal on empty context or failed evidence checks". All 81 empty-context rows are HARD and have grading time under 1 ms (deterministic rejection, as main already says at line 619), so the caption does not imply every refusal is an LLM call. |
| Latency labels | Lines 119/145 keep `TerraFastPathMedianSeconds`/`HardPath...` explicitly as Category A / Category B medians; not relabelled as route values. |
| Build log | Console shows exit 0; the only non-font diagnostics are the two overfull hboxes (1.30 pt, 14.05 pt, lines 181 and 199), as in baseline. I could not independently count the 426/427 font warnings (the .log file was not in the package listing I staged; the console has none counted as errors). |
| Rendered figure | Viewed page 4 (130 dpi) and Codex's detailed render. The EASY box now feeds the NLI grader through a horizontal line below the Retrieval and BFS boxes; it does not touch the generator or cross box text. Offline boxes fit; caption and following text do not collide. |

## Semantic review of the diagram (retained coarse detail)
No new regression found. Pre-existing coarse details, not changed by Batch 1 and not authorized to change:
1. The dashed "Vector Query" arrow and the "Vector Seed Retrieval (n_results = 2)" box sit on the HARD path only; the EASY box shows no ChromaDB source. Not wrong (EASY retrieval is stated in words) but the figure alone under-shows that EASY retrieval uses the same index.
2. The Self-Correction loop returns to BFS Graph Traversal; whether failed EASY grading expands via the loop is not established by anything I read. The caption does not claim it.
3. "Failed 2x" is the only refusal arrow; the deterministic empty-context refusal appears only in the caption.
4. The Vector Database cylinder text is crossed by the dashed "Graph BFS" line, and Phase 1 slightly overlaps the Phase 2 border (identical in baseline). Figure fonts remain very small; readability is a later batch.
5. "Procedural Traces" in the database label and the "Procedural Trace Generator" box name remain; page 4 text clarifies the evaluated index uses a fixed scaffold, so the pair is consistent but terminology is still looser than the prose.
6. The Phase 2 router box no longer names the L2 pre-filter, while main line 126 still describes an optional coarse proximity flag (disclosed as a limitation); consistent with Codex's stated intent.

## Non-blocking notes on the package
A. `baseline/main.pdf` (sha256 abe24280…) is not my Batch 28 PDF (701bcd59…); it is a Tectonic build of the Batch 28 source. Fine as a rollback comparator, but describe it as "baseline build", not "the delivered PDF".
B. The package's `verification.json` text-compares pages; I repeated it and agree. It does not certify layout beyond the five pages viewed.
C. F01 remains open for the supplement (stale "no retrieval" caption in Table X, "Section ??", stale fast-path wording in Supplement II). Also open from my Phase 1 audit and untouched here: net route latency macros 5,457/14,071 and Table X gross route rows equal to Category A/B medians.
D. The "1,124 macro-name uses unchanged" claim: I did not rerun it; my line-diff already bounds the change to four lines.

## Not verified by me
My own recompile; the 427 font-warning count; pages other than 4 visually (I confirmed text identity for 19 pages, not images); the 77 protected inputs I had not staged earlier; whether the EASY box's missing k is correct (no k value claimed).

Stop for user review. No Batch 2 started.
