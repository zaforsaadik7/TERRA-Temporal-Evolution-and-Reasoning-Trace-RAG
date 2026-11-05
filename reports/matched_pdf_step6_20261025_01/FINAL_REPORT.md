# Step 6: compilation, rendered inspection and page-budget audit

Codex implementation self-verification, 25 October 2026. User approved the previously reserved Step 6. **PASS: main paper 25 pages including references; separate supplement 18 pages.** This checks the advisor's main-paper ceiling, not an unverified journal combined-length rule.

## Builds and layout

Tectonic 0.17.0 ran with `-C -k --keep-logs` (cached assets only). Both the pre-study baseline and integrated source were built separately with supplement/main/supplement/main sequencing to resolve external references. Every compilation exited zero. The integrated main already fitted 25 pages, versus 25 for the pre-study baseline; supplement increased from 17 to 18 pages. Baseline and unmodified integrated builds/logs/PDFs are retained.

Rendered overviews were inspected for all 25 main and 18 supplement pages, with full-page inspection of the new results (main 11, supplement 17–18), conclusion (main 24) and equation areas (main 4–5). The new numerical result, interval, refusal tradeoff, limitations and supplement table render without clipping. All three figures and historical table layouts remain present. Existing dense table typography was not reduced to obtain the page count.

Two pre-existing equations exceeded their columns, including the routing case overlapping adjacent text on page 5. Three bounded changes were made **only in final_src/main.tex**: wrapping the document serialization expression; stacking the unchanged AND/OR routing conditions; and changing duplicated capitalized “Among” to “among” in the conclusion. No numbers, thresholds, results, figure/table assets, fonts, margins or limitation content were removed or rescaled. `layout_source.diff` records these changes. The first refinement helper stopped on mixed newline matching before edits; its original and untouched copy are preserved, and the corrected helper completed all builds.

Final main and supplement have zero overfull boxes, undefined references/citations, multiply defined labels or “??” markers. Main retains 76 underfull warnings; supplement 209, primarily spacing in existing tables. They are not suppressed. Extracted word bounds show no text outside pages; this complements rather than replaces rendered inspection. Final main pages 4, 5 and 24 changed in pixels and were inspected at full page size; the other 22 main pages and all 18 supplement pages are pixel-identical to the inspected unmodified integrated rendering.

## Preservation and deliverables

All 46 working-source files remain byte-identical to their pre-Step-6 snapshot. Authored isolated edits are limited to main.tex as described. The compiler also regenerates main.bbl from the unchanged ref.bib and current citations: its bytes equal the unmodified integrated build's generated bibliography, all cited keys resolve, and generated_bibliography.diff records the difference from the stale input bbl. No bibliography entry was manually fabricated or edited. All 660 sealed study manifest rows and the seal digest were reverified. No APIs, credentials, model execution, statistics regeneration, manuscript working-source replacement or canonical promotion occurred.

Final PDFs: `output/pdf/main.pdf` and `output/pdf/TERRA_SUPPLEMENT.pdf`. Reproducible isolated source: `final_src/`. Machine checks and identities: `AUDIT_RESULT.json`, `FINAL_BUILD_RESULTS.json`, `manifest.json`; logs and before/after source receipts are preserved alongside the renders. The old sealed Steps 1–5 package was not edited.

**Step 6 is complete as implementation self-verification.** Antigravity should inspect final PDFs (especially main 4–5, 11–12, 24 and supplement 17–18), the three-region source diff, numerical qualifications and compiler logs. Peer acceptance of these PDFs is not yet claimed. Working-source incorporation of the isolated formatting patch and canonical release remain distinct from this isolated build; no publication or promotion has occurred. The result still measures gated pipeline faithfulness with 69 versus 4 Category B refusals, not verified legal correctness or superior coverage. Reference costs are not audited invoices.
