# Approved assessment integration and supplement reconstruction

12 October 2026. Codex implementation self-verification, not independent expert or peer acceptance.

## Authority and outcome

The user replied “I approve” to `plans/20261012_AUTHOR_ASSESSMENT_INTEGRATION_PROPOSAL.md`. Applied the bounded assessment disclosure and supplement repairs to `working/src/`, not the canonical archive. No model inference, paid API call, benchmark rerun, threshold change or graph edit occurred. Standard LaTeX package/font downloads were required to build the PDFs; these were compiler dependency fetches, not research API calls.

Main: **25 pages**, SHA256 `88aacae730f664692b52dcaaa1643fc3ddec261edf5cbf6200156ce3e49aaffc`.
Supplement: **17 landscape A4 pages**, SHA256 `4c13030ad5c54b1c8219e7cffd0f32fe5a8d939f37f575403b7ee2bfde50fe9c`.
Final outputs are in `applied_build/main.pdf` and `applied_build/TERRA_SUPPLEMENT.pdf` beside this report. Historical PDFs were not overwritten. The six-page historical supplement is superseded for this working checkpoint, not deleted.

## Source changes

The only changed pre-existing working source is main.tex (before `56b79e1f...`, after `a69b8b5fb9a1d97d8ac3579e222c7a9567162a6a37a2089af3bd00fe6b631d50`). All other pre-existing working files match baseline_manifest.json, including frozen generated statistics, bibliography, figures and original standalone tables.

Main adds the approved exploratory methods subsection and limitation sentence. The historical obscure-suite single-author spot-check remains distinct. Added standard xr external-reference support. Removed the six-baseline page-stretch immediately preceding the new methods subsection: retaining it caused an out-of-page annotation in the trial build. This is a layout repair, not an omission of scientific content.

Fourteen new TeX sources provide a durable supplementary parent, ten table representations, detailed limitations, assessment disclosure and supplement-only latency overrides. Parent SHA256 `b1289ebb4c7835a598b0c0a1d604df60d6a1f5a73eb29199bd3a0fbc63fc72f2`.

## Scientific dispositions

- The assessment is explicitly AI-assisted, non-expert and descriptive. Original and reconciled ratings remain separate; no pipeline accuracy, expert validation, population estimate, confidence interval or agreement statistic is invented. The source/rationale repair exclusion survives in the supplementary note.
- Ten authenticated table objects survive as S1–S10; longtable handles page breaks without downscaling. Tables use natural 9-point text and 8-point notes; limitations use 10-point body text. The expanded supplement page count reflects this readable layout and the restored detailed limitations, not new experiments.
- Router note now distinguishes 48 refusals/25 refutations under four-class scoring from 46 system-flagged pre-generation refusals. EASY descriptions record retrieval and grading. Feature comparison identifies generic scaffolds, not case-specific issue/test/holding analyses.
- Thirty-five supplementary latency overrides match named fields in the pinned approved export. Linear percentiles, sample SD (ddof=1), raw milliseconds and decimal half-up rounding to two places are explicit. EASY median 5464.96 ms and HARD median 14067.48 ms are separate from Category A/B medians 5828.08/17938.50 ms. Original omitted p75 category cells remain omitted. Baseline latency cells remain unchanged; this batch does not independently recalculate them.
- Graph table retains original active graph identity (145,366 edges), using the reviewed undirected-largest-WCC diameter 13 and average path 4.305. It is not credited to the 145,363-edge derivative.
- Temporal false-negative spot-check assertion and associated confidence bounds were removed as unsupported, not replaced with the author assessment. Automated HLCR differences are not called expert-validated legal accuracy. Temporal comparisons are labelled exploratory; no preregistration or exhaustive-enumeration certification is inferred from prose.
- The FDR table retains all 20 rows and adverse directions. Corrected its stale no-retrieval/rank interpretation; disclosed that bootstrap intervals in rows 2, 6 and 12–17 lack verified original settings. Numeric cells were not regenerated here.
- Eighteen limitation entries remain. Unchanged detailed paragraphs were retained where consistent; L03, L06, L10 and L13 were restated to avoid false ceiling-resolution, stale safety/statistical figures, route/category confusion and wrong judge descriptions. L01, L07, L11, L12 and L17 received bounded qualification/format/reference corrections. All original detailed texts are preserved separately in preserved_limitation_texts.json for peer semantic comparison; preserving eighteen themes is not independent proof that every historical qualification is valid.

## Build and visual checks

Tectonic 0.17.0, cached final builds, arguments `-C -k --keep-logs`. Final sequence: supplement, main, supplement, main in applied_build, with actual saved AUX files for external references. Four exits 0. Every final reference/citation resolves; no “Float too large” warning. Supplement has zero overfull boxes. Main retains two overfull boxes from the existing layout; this batch is not full main-paper readability certification.

Initially failed builds (wrong initial directory, uncached xr/font resources, and an attempted override of an undefined omitted category-p75 macro) are not success evidence. Their saved records remain where captured. The final successful run is recorded separately in timestamped build_execution/console files. No diagnostic suppression or artificial label records were used.

Viewed all seventeen supplement pages via rendered contact sheets, with full-size inspection of the assessment and latency pages; inspected main pages 10 and 23 carrying the new passages. Rendered bounding checks found no out-of-page text. Final applied-build page text and raster pixels match the reviewed candidate on every page of both PDFs; PDF bytes differ because builds are not asserted byte-deterministic. This was not a full scientific reading of every main page.

## Evidence and rollback

- baseline_src/ and baseline_manifest.json: byte-preserved pre-edit source dependency snapshot.
- source.diff: final applied-build versus baseline TeX source differences.
- build_verification.json, timestamped execution/console files and applied_build/*.log: compilation identities and diagnostics.
- latency_cell_check.csv: 35 named-field override checks against the unchanged approved export (hash `9cefb5a3...`).
- object_and_value_checks.json: ten unique table labels, eighteen limitation entries and approved assessment summary values.
- render_review.json and rendered/: page images and bounds checks.
- Canonical evaluation SHA256 remains `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`. Original workbooks were not edited. No canonical promotion occurred.

## Remaining tasks

This closes the approved bounded integration/reconstruction implementation, subject to peer review. It does not establish submission readiness or satisfy the licensed-expert or matched-resource baseline requests. Next: per-experiment graph/code/configuration provenance and remaining generic-scaffold title/claim consistency; then matched-baseline protocol and explicit API/cost approval before any new run. Venue-template pagination, small main-table readability, full-PDF audit, reference/release checks and final promotion remain separate gates.
