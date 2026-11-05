# r13 main pages 23–44 and architecture figure: Codex self-verification

Date: 25 October 2026. Author: Codex. Verdict: **CORRECTIONS REQUIRED**.

This is implementation self-verification by Codex, including review of Codex's own architecture redesign. It is not external independent review. No source changes, compilation, model/API calls, or data/statistics changes were performed. The only file written for this review is this report.

## Artifacts and exact coverage

Root: `F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/reviewer_I9_20261025_01/`.

- PDF inspected through its supplied full-page renders: `builds/r13/main.pdf`, 66 pages; SHA-256 `59d86545c5f3df0d072a3a59cc11eb357967077908663384ef29d4be36dde208` (locally hashed, matching BUILD_RESULT.json).
- Scientific text read: `builds/r13/main.txt`, SHA-256 `85f257f582a79a5975a0a5a14b016b913458fbe4b50e8263956ec6b5032f2671`.
- Each actual full-page PNG was opened with `view_image`: `renders/r13/main/page_23.png`, `page_24.png`, `page_25.png`, `page_26.png`, `page_27.png`, `page_28.png`, `page_29.png`, `page_30.png`, `page_31.png`, `page_32.png`, `page_33.png`, `page_34.png`, `page_35.png`, `page_36.png`, `page_37.png`, `page_38.png`, `page_39.png`, `page_40.png`, `page_41.png`, `page_42.png`, `page_43.png`, `page_44.png`, and additionally `page_65.png`.
- All extracted text for PDF pages 23–44 and 65 was read. Page 5 text was also read while locating the diagram; its mention of Phase 1 is prose, not the figure. **Page 5 image was not inspected.** The actual Figure 1 is on PDF/printed page 65, confirmed by the full-page image and its caption.
- Used the existing r13 full-page render of page 65; no new render file was created, respecting the instruction to write only this report. No contact sheet or extracted text was substituted for viewing any assigned image.
- Also read the r13 figure source, relevant layout lines of r13 main.tex, BUILD_RESULT.json, and the output-summary line in main.log for context. The build reports no overfull/undefined/duplicate diagnostics, but those diagnostics do not override the visible problems below.

## Required corrections

### 1. High: page 25 extends far below the normal text area

`page_25.png` contains a nearly full-sheet wall of scientific prose ending around the bottom edge of the image, whereas neighboring pages stop well above their footer. The normal page-25 footer is absent from the visible sheet. The final Category C paragraph sits far below the normal body baseline limit. This is a direct visual defect even though the build's overfull list is empty. In r13 main.tex, line 452 contains `\enlargethispage{14\baselineskip}` near this results passage; this is a strong source-level lead for the parent, not a separately tested diagnosis.

Required disposition: restore the normal Springer text-area/footer geometry and let the results break across pages. Preserve all text and scientific qualifications; do not shrink the passage to hide overflow. Reinspect all resulting pages after pagination changes. I do not claim text is missing from main.txt; the confirmed problem is the rendered placement.

### 2. High: Figure 1 page 65 has visible line/text and border/text collisions

The figure fits horizontally on the displayed sheet, and the caption is readable, but the actual rendering is not acceptable yet:

- The horizontal parser-to-scaffold branch at the bottom of row one passes through the corpus's final `opinion precedents` line and the parser's example region. Corpus and parser cards nearly touch the next row because their rendered text is taller than the reserved lane.
- The graph-store G port overlaps the bottom line containing `145,366 edges`/the store boundary. The V port is also tightly attached to the vector-store boundary; neither port has comfortable separation.
- The lower Phase 2 border runs through/touches the `Store interfaces:` legend. This is especially clear across the first legend line.
- Excessive wrapping breaks short phrases and identifiers across multiple lines (`authen-/tic`, `scaf-/fold`, `OVER-/RULES`, and the generator identifier). Text is readable in principle but the design loses the intended compact hierarchy and consumes the arrow clearance.

These are defects in my implementation's actual integration/rendering, not a claim that the prior unrendered source estimates were validated. The parent should reserve clear lanes using actual rendered node bounds, give the corpus/parser row more height, separate database ports from node text, and move the legend below the container with explicit clearance. Keep native 8.5/9 pt labels and the user's width/height constraints. Re-render before accepting.

The scientific correction is visible and retained: `Length-filtered opinion precedents`, generated links `(audited, imperfect)`, the 145,366 edge value through the macro, and an explicit historical-run caveat. The first-failure route enters self-correction and returns at the left to vector retrieval, then passes through BFS; it no longer returns directly to BFS. EASY feeds the shared grader. No diagram logic rewrite is requested beyond keeping these relations unambiguous while repairing clearance.

### 3. Medium: table pagination fragments scientific comparisons

- Table 7, pages 32–33: the Flat Vector RAG versus Direct LLM secondary test is split after its p-value. Page 33 starts a separate continued block with only its gate-status/conclusion. Keep that test's p-value and CLOSED/descriptive-only status together so the qualification cannot be missed.
- Table 7, pages 34–35: Full TERRA and primary-test sensitivity are broken between Judge One on page 34 and Judge Two/consensus on page 35. Repeated headers help, but the four pipeline columns are already split across multiple blocks. Prefer whole judge blocks or a compact restructuring that retains direct evaluator comparison.
- Table 10, page 44: three baseline columns appear in one block and Full TERRA alone in the next, with the entire metric stub repeated. This is legible but weakens immediate comparison and adds substantial space. Prefer one native-width comparison block if possible without reducing font size.

Table 7 occupies pages 31–35 within this scope. Preserve the failed primary test and closed secondary gate throughout any reflow. These are readability/pagination findings, not requests to delete evidence.

### 4. Medium: duplicated percentage expansions on pages 39–40

The CaseFacts Track 2 narrative visibly repeats percentages, for example `50/50(100.0%) (100.0%)`, `(46/50(92.0%), 92.0%)`, and `(40/50(80.0%), 80.0%)` on page 39. The pattern continues on page 40 with `0/50(0.0%) (0.0%)`, `10/50(20.0%) (20.0%)` and `4/50(8.0%) (8.0%)`. Remove the duplicate prose suffix when the macro already includes the percentage. Preserve all counts and values.

### 5. Medium: reversed section range on page 40

The CLERC introduction identifies the internal benchmark as `Sections 6.4–6.1`. This reversed range is visibly printed and also appears in extracted text. Resolve against the intended endpoints rather than simply reversing it without checking coverage.

### 6. Low: editorial process residue in Table 8

The caption on page 38 says `(Fix 1)`, and notes on page 39 say `Per Fix 1`. These are internal remediation labels, not self-contained scientific descriptions. Replace the process labels with the already stated substantive qualification: the eight-item Overruled result is diagnostic with exact binomial intervals. Do not remove that qualification.

## Page-by-page inspection record

- **23:** Table 4 continuation and Table 5 Panel A are legible, contained, and have repeated headers. System-flagged Category D refusal is 46/75 for TERRA; this is explicitly distinguished in the next page's note from the audited legal-outcome classification. No new numerical contradiction established.
- **24:** Panel B readable; lengthy notes continue to page 25 mid-sentence. TERRA 48 refusals + 25 refutations + 2 fatal + 0 hedges = 75; safe handling 73/75 is consistent. Holm qualification and D033/D034 disclosure are present.
- **25:** Severe bottom-margin/footer failure (issue 1). Text retains answer-subset caveat, Direct LLM's stronger Category B/D faithfulness, false refusals, adjusted non-significance, and absence of independent legal validation. Several count/percentage strings lack a space before `(`; cosmetic, secondary to overflow.
- **26:** Router and latency prose is readable, with 340/350 correct, ten Category D misroutes, and a properly qualified ten-query downstream-safety observation. TERRA's slower latency and non-like-for-like harness caveat continue on page 27.
- **27:** Table 6 legible. The row labelled `Wilcoxon p` includes a daggered Fisher result for Category C; the explicit footnote on page 28 explains the exception. A generic `Test p` label would be clearer, but no unsupported test substitution is inferred.
- **28:** Table 6 continuation and notes readable; FDR family, Direct LLM counter-result and exploratory temporal-probe scope retained. No clipping seen.
- **29:** Temporal rubric, judge disagreement, missing 85 evaluations, unknown missingness direction, refusal and correctness-label distinctions readable and retained.
- **30:** Failed H1 expressly retained; complete-case and bounded contrasts distinguished. Six gate interventions are reported with small-sample/underpower qualifications. Existing explanations should remain observational; this review does not recompute the historical bounds.
- **31:** Table 7 caption/Panel A readable; Full TERRA is isolated into a second block. Outcome counts and safe-rate intervals visible. No clipping seen.
- **32:** Primary gate CLOSED and secondary descriptive status visible; final secondary test split at page boundary (issue 3).
- **33:** Orphaned secondary gate status at top (issue 3); sensitivity subsets and cross-suite panel readable. Cross-suite risk differences, intervals and Fisher tests are explicitly descriptive.
- **34:** Cross-suite Full TERRA and per-judge blocks readable, but Judge One section splits from remaining judges (issue 3).
- **35:** Judge Two/consensus and extended Table 7 notes readable. Primary non-rejection, closed secondary gates, non-equivalence and unverifiable-quote disclosure retained. Note defines this suite's Rref as recognition of overruling, whereas Table 5 uses explicit refusal: readers need to retain the suite-specific definition; I do not equate these counts across suites.
- **36:** Oracle-dependent context construction, inability to isolate the tag, judge sensitivity, small cross-suite samples, imperfect blinding and non-practitioner spot-check limitations visible and preserved. No layout collision seen.
- **37:** External CaseFacts protocol readable. The 284 distinct-node arithmetic is consistent with 100+151+58 minus the stated 25 overlap; no inference of random selection is warranted. The prose explicitly says label-header concordance is not independent legal judgment.
- **38:** Table 8 readable within the page. Caption contains process residue (issue 6). Long notes continue to page 39. Lower TERRA accuracy/soundness and wide eight-item intervals are visible.
- **39:** CaseFacts notes and mixed findings retained, including lower accuracy and p=0.625 diagnostic. Duplicated percentage text (issue 4); process residue (issue 6).
- **40:** Duplicated percentages and reversed range (issues 4–5). CLERC protocol clearly identifies the second track as a TERRA-specific control rather than a native benchmark task; broader holding-extraction screening gap is retained.
- **41:** Table 9 legible; adverse low citation F1 and lowest TERRA soundness visible. Panel B continues on page 42 with repeated headers; no clipping seen.
- **42:** Caption-membership metric explicitly distinguished from fabrication. Full-N versus generated-only misapplication denominators and omission of refused items from precision are disclosed. No visual collision seen.
- **43:** Withdrawal of unsupported 0% fabrication retained; generated-only 60/67 and 45/67 misapplication rates retained. Retrieval section explicitly defines full-path recovery as target ID/title coverage, not independently verified connected-path recovery.
- **44:** Table 10 readable but split comparison blocks (issue 3). Distinction between canonical-v2 66/100, older 62/100 and separate bounded diagnostic remains in the caption.
- **65 (additional architecture page):** Actual Figure 1 inspected in full, including caption, legend, labels and return/failure arrows. Native placement does not by itself establish compliance; collisions in issue 2 prevent acceptance.

## Bounds of this verdict

No raw-result reanalysis, fresh legal-source validation, reference-link clicking, or independent numerical replication was performed. I reviewed the rendered scientific presentation and extracted text for the stated pages, not the entire 66-page main paper or supplement. The 66-page build is also above the recorded 25-page advisor ceiling; this is a package-level constraint for the parent to reconcile, not something this assigned page slice can certify away. The absence of overfull warnings is not a visual PASS. Reinspection of affected pages and the architecture image is required after the parent repairs the issues.