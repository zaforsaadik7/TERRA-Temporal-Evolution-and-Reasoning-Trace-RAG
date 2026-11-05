# Correction dispositions — proposed only

No accepted source changes. Proposed diff is unbuilt and does not establish a25-page corrected result. F02 is conditional on peer confirmation of the accepted20-test family; never silently edit frozen statistics.

## I11-F01 — Scientific disclosure extends below the physical bottom of main page12

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:462; main12.

Evidence: 87 text spans cross the physical page boundary by more than1pt in infinite-rectangle extraction. Normal extraction omits part of the refusal/clamping paragraph; actual raster ends at “counting unflagged textual”. Source explicitly enlarges page by14 baselines. No other audited page crosses this bound.

Proposed action: Remove the 14-baseline enlargement in an isolated correction candidate and reflow. Preserve all refusal and raw/clamped disclosures. If this yields26pages, repair layout locally with evidence retained; do not shrink until unreadable or silently discard text.

Closure: All paragraph text must be visibly rendered within the page; inspect page12 and every reflowed page, text/layout parity for unaffected pages, main<=25 with readable type.

## I11-F02 — Two CategoryA FDR q values disagree between main and complete-family table

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:463; main12, supplementS2.

Evidence: Resolved CatATerraVsFlatRAGAdjQ=0.0177 and CatATerraVsHippoRAGAdjQ=0.3623; TableS1 ranks12/15 show0.0189/0.3865. Raw p values agree0.0114/0.2898. These are not rounding equivalents.

Proposed action: Use the reviewed M20 family as a single reporting source. Proposed local correction-layer overrides0.0189/0.3865 align the existing full-family table without editing generated_stats or rerunning tests. Peer must confirm family identity before adoption; significance decisions unchanged.

Closure: Trace all20 family inputs to accepted derivation; every occurrence must agree on family, p and q; no empirical/statistical regeneration in this audit.

## I11-F03 — ROUGE explanation claims longer TERRA answers despite the displayed shorter mean

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:423; main11.

Evidence: TableIII reports TERRA415 words, Flat481, Graph477, Hippo470 and Direct612. Prose attributes Flat higher F1/precision to TERRA writing longer chronological syntheses. Answered-only TERRA490 has a different denominator and does not identify this causal explanation.

Proposed action: Delete the unsupported causal clause. Keep length sensitivity definition, all means and separately qualified answered-only comparison. Do not supply another untested causal story.

Closure: Read paragraph/TableIII together and check no unsupported length-cause claim remains.

## I11-F04 — Chain counts acquire a duplicate /100 and recall lifts have wrong units

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:597; main19, main21.

Evidence: FullPathCount macros already include denominators, yielding66/100/100 and1/100/100. Main19 calls +62.1% and+20.4% recall lifts; displayed recall differences are percentage points. Main21 similarly says “+13.97% to+16.75% points”.

Proposed action: Drop duplicate /100 suffixes; label differences62.1 and20.4 percentage points and citation-recall differences13.97 to16.75percentage points. Keep original counts/macros unchanged.

Closure: Rendered source/paragraph count conventions consistent; no /100/100 strings; distinguish ratios from differences.

## I11-F05 — Bold emphasis does not implement table notes

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:444; main11, main13.

Evidence: TableIV CatA bolds Hippo0.910 but not TERRA0.941, despite note saying top among RAG. TableIII bolds Direct recall/wordcount under a RAG-only rule and all three TERRA win rates although only73% is largest. Mean words is descriptive, not a benefit direction.

Proposed action: Move TableIV CatA bold to TERRA. For TableIII remove metric-cell bold and state cells are descriptive, with TERRA row named for identification; alternatively define each direction explicitly and apply consistently.

Closure: Inspect both tables and captions at readable zoom against numeric extrema, excluding Direct only when note says so.

## I11-F06 — Figure3 is cited as if it depicted the different rubric refusal measure

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:465; main12, main13.

Evidence: Prose describing48/75=64.0% rubric refusals cites Figure3, whose TERRA CategoryD system-flag bar is46/75=61.3%. TableV preserves both definitions.

Proposed action: Remove Figure3 from that rubric-rate sentence, or explicitly say it shows the distinct system-flag outcome. Keep both actual values and definitions.

Closure: Sentence/figure/table endpoints and denominators must match after rebuild.

## I11-F07 — Limitation7 mislabels CLERC doctrinal-misapplication rates as precedent omission

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\supplement_limitations.tex:14; supplementS16, main18-19.

Evidence: 50.0%/37.5% in CLERC TableIX and prose are OR/AND dual-judge doctrinal-misapplication rates over120 completions; they are not a measured gold-precedent omission rate.

Proposed action: Use the correct endpoint label with120 denominator and preserve incomplete-context explanation as a hypothesis, not a causal finding.

Closure: L7, TableIX and CLERC prose must name identical endpoints and populations.

## I11-F08 — Claimed prebenchmark hyperparameter freeze is not established by the qualified provenance records

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:352; main10, main22, supplementS17.

Evidence: SectionV-D.4,TableXIIcaption,L17 assert parameters frozen before benchmark with Augustpilot and chronological audit. I2 E01-E03 unknown time/code/index and TableS9 pilot date-not-recorded do not authenticate this chronology. Present-day code and mtimes are insufficient. Not a finding that the chronology is false.

Proposed action: Qualify as recovered design rationale/current source settings; date and execution order unverified. Preserve benchmark-overlap audit separately because zero overlap is not proof of temporal precedence. Reinstate strong chronology only with contemporaneous authenticated records.

Closure: Either produce hash-linked contemporaneous records establishing sequence or consistently qualify all three claims; no mtime-to-run inference.

## I11-F09 — Essential main-paper tables and Figure1 are illegibly small at normal physical size

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:154; main4, main11, main13, main14, main16, main18-22.

Evidence: Font spans include Figure1minimum2.18pt and table content/notes around2.54-4.87pt on several pages. Full-page and 3x closeups reviewed. No overfull-box warning proves readability; known I9 deferral cannot certify this away.

Proposed action: Plan measured local repagination/rebalancing with essential summaries readable in main and detailed supporting cells readable in supplement; preserve all objects/18limits and<=25main. Do not restart Springerconversion or globally shrink.

Closure: Inspect actual-size pages and closeups after chosen local design; pagecap and retained-cell checks both pass. User-deferred I9 remains explicit.

## I11-F10 — SAT-Graph mechanism and bibliography are incorrect

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\supplement_tables\table_system_comparison.tex:19; supplementS7, main25, supplementS21.

Evidence: S5 says propositional SAT solver. Publisher paper DOI10.3233/FAIA251598 defines Structure-Aware Temporal graph and deterministic structural/version/provenance primitives, not Boolean satisfiability. Publisher PDF pp282-287; official IOS book volume416, whereas ref.bib says395/586-591.

Proposed action: Replace cell by deterministic structural/temporal retrieval and provenance primitives, no SAT-solver claim. Correct only this bib entry to volume416/pages282--287 against linked primary sources.

Closure: Inspect full cited paper and official volume metadata, then verify both bibliography renderings and S5cell.

## I11-F11 — Redundant count formatting and a dangling conclusion value impair clarity

Location: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src\main.tex:682; main17-19, main24, supplementS8.

Evidence: Repeated count macros plus literal percentages produce strings such as50/50(100.0%)(100.0%). Conclusion parentheses end with unlabelled0.586. S6 all-cohort “safe handling” is not a validated legal-safety measure for ordinary A/B answers.

Proposed action: Remove duplicated textual percentages without changing macros. Label0.586 explicitly as historical answered-subset faithfulness. Qualify S6 aggregation as rubric/no-recorded-fatal-outcome accounting, not legal safety.

Closure: Read rendered sentences for unique count/percent reporting and endpoint labels; no numeric/ratings changes.

For F09, a concrete layout repair needs a separate isolated build: remove the page12 expansion, measure reflow, use readable main summary tables while retaining full cells in the existing supplement, enlarge Figure1 labels, and inspect every changed page. Do not claim these design choices meet25pages until built. F11 minor duplicates and TableIII emphasis also require a deliberate local copyedit. No experiment or API rerun is indicated by these reporting defects.
