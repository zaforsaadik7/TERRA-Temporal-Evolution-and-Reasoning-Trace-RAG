# I1c evidence reconciliation and bounded repair proposal

8 October 2026. Author: Codex. Read-only arithmetic on stored results; no pipeline, model, vector store, API or manuscript changes. User approved continuing to I1c after I1b. Numerical replacements below are proposals, not applied corrections.

## Incoming identity

Working main.tex SHA256: `1d69b864f774be4492f5c69a58a71960cffff81244fa459e8065557c6b735f14`, matching completed I1b. Current verified build: 24 pages. Raw source: `data/terra_canonical_v2_eval.json`, SHA256 `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`.

## Confirmed latency construction

Select pipeline `5_Full_TERRA`, then `timing.route_taken` EASY or HARD. Gross = `timing.total_ms`; net = gross minus the same row's `timing._retry_sleep_ms`. Percentiles: NumPy linear interpolation, 25/50/75/95. SD below uses population denominator N, explicitly distinguished from sample SD. No negative net times found. Total recorded retry sleep: 620,000 ms.

| Cohort | N | p25 | Median | p75 | p95 | Mean | Population SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| EASY gross |110|4065.298|5464.955|15955.795|18773.815|9154.168|8006.775|
| EASY net |110|4065.298|5464.955|7279.800|17907.361|7335.986|5675.314|
| HARD gross |240|3636.392|14067.480|20002.500|51093.495|16649.709|16451.572|
| HARD net |240|3636.392|14067.480|18738.470|44397.452|14899.709|14046.661|

All values are milliseconds. Gross and net medians happen to coincide; subtracting sleep per row does not necessarily change a median. Do not subtract aggregate medians.

Archived `tab:latency_percentiles` (CANONICAL_ARCHIVE/src/main.tex, beginning line 666), rendered Supplement X, uses FastPath/HardPath gross macros whose medians are 5,828/17,939: these are Category A/B medians, not EASY/HARD medians. Its net medians 5,457/14,071 fail the current row-wise construction. Other net percentile cells also differ; this is not a two-cell-only repair. Population SD reproduces the stored net mean/SD macros after rounding (7,336 +/- 5,675; 14,900 +/- 14,047). Sample SD would instead be 5,701/14,076.

Category gross medians remain A 5828.080; B 17938.505; C 2212.530; D 10144.640. Preserve category-labelled statements rather than relabelling them as routes.

## Previously repaired versus still open

- Category C/D generator counts are already overridden by `phase3_corrections_b3.tex`: 0/75 and 29/75. Current raw rows confirm these. No repeated repair proposed. This check does not certify every other budget cell.
- Router table `working/src/tables/table_router_eval.tex` still states 42 refusals / 31 refutations in its dagger note. Prior reviewed multi-class findings are 48 / 25; system-flagged pre-generation refusals are 46. Keep definitions distinct. Target this router table, not baseline specifications.
- Main line 344 falsely says temporal judge identifiers are not recorded. Each of 400 records contains nested `judge1_evaluation.judge_model` and `judge2_evaluation.judge_model`: respectively `databricks-qwen3-next-80b-a3b-instruct` and `databricks-gpt-oss-120b`. These are not top-level fields. Availability of identifiers does not certify the temporal protocol or scores.
- Main line 555 still infers non-significance from confidence-interval overlap. The previously reviewed post-hoc paired diagnostic is 3 versus 1 discordant pairs, exact McNemar p=0.625, eight Overruled items. This turn did not independently recount those labels; retain as a separately pinned evidence dependency before patching. No equivalence conclusion is justified.
- Main line 164 still says the corrected graph is released in the replication bundle. Local derivative files survive under `derived_graphs/r30corr_v1/`; existence locally is not proof of public release. Use release-pending wording unless actual public-release evidence is supplied.

## Recommended implementation split

1. **I1c-A, bounded main disclosure repairs:** temporal judge identity; release claim narrowed to “is retained as a separately versioned local derivative; public release is pending”; interval-overlap rationale replaced with explicitly post-hoc, small-sample paired evidence after its source is pinned. Snapshot, exact diff, compile, affected-page QA, <=25-page check. Do not alter experimental results or claim independence of judges from the generator beyond known model identities.
2. **I1c-B, supplementary object repair/reconstruction:** preserve the ten-object identity map and eighteen limitation themes. Reconstruct a durable supplementary parent source; correct router note and stale EASY/no-retrieval wording; render route/category latency populations separately with the row-wise construction above. Create dedicated override macros, preserving frozen generated_stats.tex and original archive. Audit all latency cells, all labels and main/supplement links; inspect actual pages. No synthetic anchors or diagnostic suppression.

Before B, archive the exact raw-ledger calculations and per-query cohort membership as rerunnable evidence. Antigravity may provide a pure offline checking script for code review; it must not import runtime pipelines or modify assets. No new live experiment is needed for this arithmetic. This report is a reconciliation checkpoint, not full budget certification or submission certification.
