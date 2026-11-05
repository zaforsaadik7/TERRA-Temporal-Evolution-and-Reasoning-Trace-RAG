# Author-assessment integration proposal

12 October 2026. Codex-authored proposal and source inspection, not independent peer acceptance. User authorized preparation; no manuscript insertion, compilation, API call or experiment performed.

## Baseline and evidence

Working source: `TERRA_EDITORIAL_RESTART_V2/working/src/main.tex`, SHA256 `56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2`.

Assessment evidence: `reviewer_author_validation_20261008/source_verification_20261011_01/complete_review_01/ratings_only_results_20261012_01/` beneath `TERRA_EDITORIAL_RESTART_V2/`. Its REPORT.md, verification.json and descriptive_results.csv document 76 rows per author, separate originals/reconciliations and 14 confirmed rating changes. The original workbooks remain unchanged. Supporting-text repairs were excluded by the user's revised scope; no complete supporting-source certification is claimed.

Antigravity-0051 audited earlier workbook hashes (`97258970...` and `4f005cc7...`), not the current originals identified in verification.json (`34735965...` and `ce3869f8...`). Its historical completeness verdict is not an independent acceptance of these reconciled outputs.

## Recommended placement and exact proposed wording

Keep the main addition short. Add the following paragraph at the end of Experimental Setup, before the results begin; select the exact insertion boundary in the implementation diff.

> As an exploratory assessment, two project authors, neither legally trained nor licensed to practise law, reviewed 76 assigned response instances each with AI assistance. Author 1 drafted assessments and used AI for source finding, interpretation, checking and rewriting; Author 2 reviewed and amended AI-proposed ratings and rationales. Original ratings were recorded before access to the other author's ratings; reconciliation subsequently incorporated shared ratings and source-audit feedback. The sample includes repeated questions and overlapping response instances, so the assignments are not 152 independent queries. These assessments are descriptive, not independent legal-expert validation or population estimates.

Add the following sentence to limitation 1, preserving its existing discussion of automated scoring, the separate obscure-suite spot-check and the absence of verifier validation:

> The additional two-author assessment was AI-assisted and non-expert; its reconciled ratings were not blinded and do not establish legal correctness or verifier error rates.

Do not replace the historical single-author obscure-suite spot-check with the new two-author assessment: these are distinct studies. Do not call self-reported AI model labels verified versions.

### Supplement: proposed exploratory subsection

Use the heading **Exploratory AI-assisted author assessment** in the reconstructed supplement. Include the main methods paragraph above, then:

> Each author assessed 76 assigned rows. “Non-refusal coverage” includes substantive and mixed refusal/substantive responses. “Supported-answer yield” is the number of non-refusal rows rated supported divided by all assigned rows. “Contradicted among non-refusals” divides contradicted rows by substantive-plus-mixed rows. These are rating-based descriptive proxies, not verified legal-correctness measures. Supported ratings can reflect a correct central answer despite subsidiary errors. Uncertain ratings are retained separately.

| Measure | Author 1 original | Author 1 reconciled | Author 2 original | Author 2 reconciled |
| --- | --- | --- | --- | --- |
| Non-refusal coverage | 62/76 (81.6%) | 62/76 (81.6%) | 65/76 (85.5%) | 65/76 (85.5%) |
| Supported-answer yield | 43/76 (56.6%) | 40/76 (52.6%) | 47/76 (61.8%) | 47/76 (61.8%) |
| Contradicted among non-refusals | 19/62 (30.6%) | 22/62 (35.5%) | 12/65 (18.5%) | 12/65 (18.5%) |

Proposed table note:

> Author 2 additionally rated six non-refusals uncertain; Author 1 rated none uncertain. Reconciled values apply only author-confirmed amendments. Author-specific aggregates must not be compared as system-performance estimates or pooled as independent observations. No pipeline-specific analysis, paired agreement, confidence intervals, population weighting or verifier confusion matrix is reported. Supporting-text corrections were excluded from the completed ratings-only analysis; source attribution and rationale completeness are not certified by this table.

The proposed non-refusal definition differs from the integrated plan's substantive-only coverage definition. Preserve this explicit label; do not relabel these figures as the plan's correct-answer yield or benchmark coverage. This is disclosure of the completed narrow work, not completion of the full I6 study.

## Existing supplement claim requiring disposition

`working/src/tables/table_temporal_leakage_probe.tex:43` claims that stratified checking confirms zero false negatives and gives binomial bounds. The new author-specific aggregates do not establish that claim: they are not a verified Level-0 cohort matched to automated labels. In the supplement repair batch, replace only that unsupported spot-check assertion and its associated confidence bounds with:

> Independent legal-expert validation of temporal false-negative detection was not performed. The exploratory AI-assisted author assessment is reported separately and does not estimate this rate.

Retain the preceding NGLIR denominators and values subject to their existing provenance checks. This proposal does not certify the other temporal-table notes, tests or correctness labels; those remain in the cell/wording audit scope.

## Remaining reviewer requirements and sequence

1. After user approval, apply the bounded methods/limitation disclosure and reconstruct the supplement with the exploratory subsection. Preserve all ten mapped table objects and eighteen limitation themes. Snapshot dependencies first; use separate correction macros rather than editing frozen generated statistics.
2. In that supplement batch, repair stale router counts with their distinct definitions, EASY retrieval descriptions, and every affected latency cell using the already exported row-wise route/category evidence. Audit temporal wording and source-dependent claims; do not regard the new assessment as their automatic validation.
3. Compile main and supplement, inspect actual affected pages and references, check readable table fonts and the main ceiling of 25 pages. The existing 24-page build is historical baseline evidence, not a page-count prediction for these additions.
4. Finish per-experiment graph/code/configuration provenance and generic-scaffold novelty/title corrections under the integrated plan's separate checkpoints.
5. The reviewer's matched-resource strong flat/hybrid comparison remains unperformed. Prepare a protocol before any coding or paid calls; inform the user about API requirements and replacement credentials before execution. No new run is authorized here.
6. Legal-expert evaluation remains unavailable. Present this assessment as partial exploratory evidence, not satisfaction of the expert-review request. No further expert-review request is made to the user.
7. Venue template, full-PDF inspection, references, data-availability/release checks and final submission approval remain separate gates. Do not claim submission readiness from this proposal.

## Implementation acceptance checks

- Exact approved source diff; original workbooks, raw results, graphs and frozen statistics unchanged.
- Original/reconciled denominators and adverse findings retained; no assessor ratings inferred or changed.
- Main text identifies AI assistance and non-expert status, with no independent/blinded claim for reconciliation.
- No unsupported zero-false-negative assertion retained solely on the strength of this assessment.
- Main <=25 pages in the chosen build; actual supplement objects, links and readable rendering checked.
- Implementation self-verification labelled accurately; peer review may be requested through the user but is not presumed.

Decision requested: approve this exact integration direction and the bounded supplement repair proposal before source implementation. No manuscript change has been made by preparing this document.
