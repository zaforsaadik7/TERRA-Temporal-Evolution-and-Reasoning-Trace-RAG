# Ratings-only assessment completion report

12 October 2026, Asia/Dhaka. Codex self-verification. Completed within the user's revised scope excluding quotation and supporting-explanation repairs.

## Delivered

original_ratings.csv preserves the original G–L labels plus assessment IDs, author, original row, cluster, task and cutoff metadata. reconciled_ratings.csv applies only the 14 author-confirmed rating amendments. Neither file contains queries, candidate answers, court passages, rationale text, assessor-name cells or original timestamps. The source workbooks retain all original content unchanged.

descriptive_results.csv contains each categorical rating count with its explicit author-specific denominator, for original and reconciled versions. verification.json identifies originals and output SHA256 hashes. normalization_log.csv is empty except for its header: the current originals required no syntax normalization. Historical reports of six malformed labels do not describe these current hashes.

## Verification

152 rows, 76 unique expected IDs per author, no missing or duplicate assessment IDs. Every amendment's original value and cell/row mapping were checked before applying it. Re-read output CSVs in a separate check: exactly 14 changes, consisting of seven citation ratings, three refusal ratings, three correctness ratings and one responsiveness rating. All metadata fields are unchanged. Both original XLSX hashes match their preserved values before and after processing. No XLSX was edited or rendered.

An initial validation stopped before export because the analysis helper omitted the valid mixed-refusal/substantive-answer label from its enum. This was corrected to accept the existing label, not change any rating. The subsequent run completed successfully in a fresh output directory; existing outputs cannot be overwritten by rerunning the builder.

## Descriptive results for the assessed rows

These are author-specific descriptive proxies, not verified legal-correctness rates, pipeline-specific benchmark comparisons, independent samples, or population estimates. Do not pool the two denominators as 152 independent queries. Some queries/answers repeat and some pairs overlap between authors. No matching by item number across authors, agreement statistic, confidence interval, significance test, automated-judge comparison or weighting was performed.

Non-refusal coverage includes both substantive answers and mixed refusal/substantive answers. Supported-answer yield counts non-refusal rows rated supported over all assigned rows. Contradicted-among-non-refusals counts rows rated contradicted over substantive-plus-mixed rows. Uncertain ratings are not recoded as contradicted. These definitions do not establish that every sentence is accurate or that a verifier caused an error.

| Metric | Author 1 original | Author 1 reconciled | Author 2 original | Author 2 reconciled |
| --- | --- | --- | --- | --- |
| Non-refusal coverage | 62/76 (81.6%) | 62/76 (81.6%) | 65/76 (85.5%) | 65/76 (85.5%) |
| Supported-answer yield | 43/76 (56.6%) | 40/76 (52.6%) | 47/76 (61.8%) | 47/76 (61.8%) |
| Contradicted among non-refusals | 19/62 (30.6%) | 22/62 (35.5%) | 12/65 (18.5%) | 12/65 (18.5%) |

Author 2 has six uncertain correctness ratings among the 65 non-refusals. Author 1 has none. Thus the Author 2 figures must not be interpreted as all remaining non-refusals supported; supported plus contradicted does not exhaust that denominator.

## Interpretation and authorship

Both authors report no formal legal education/research experience or licence. AI assisted assessment and reconciliation. Author 2 states AI proposed ratings before he drafted any personal assessment, and later saw Author 1's ratings during reconciliation. Original and reconciled versions are separate; the latter cannot be described as still blinded or independent. Model names are self-reported, unverified labels. Author 2's supplied confirmation date was explicitly corrected to 12 October 2026 in the separate date addendum.

Some supported ratings intentionally reflect correctness of the central answer despite errors in subsidiary assertions. Preserve this limitation; do not retrospectively redefine the rubric or equate supported with an error-free answer. Evidence limitations for municipal applicability and exact-scenario sources remain in prior audit records. This work does not satisfy a blinded licensed legal-expert evaluation or certify legal reliability.

## Scope closure and next task

The ratings-only export, amendment verification and per-author original-versus-reconciled descriptive summaries are complete. Supporting-text repairs are excluded at the user's direction, not completed or silently certified. No full corrected quotation-containing workbook is claimed. No manuscript, graph, model output, original workbook or scientific statistics file changed.

The next substantive task is deciding which narrowly described assessment findings to integrate into the manuscript and which reviewer requirements remain unmet. A pipeline-specific or paired-agreement analysis would require the preserved private mapping and a separately specified analysis, rather than comparing these author-level aggregates as system performance. No manuscript insertion or new experiment was performed by this completion.
