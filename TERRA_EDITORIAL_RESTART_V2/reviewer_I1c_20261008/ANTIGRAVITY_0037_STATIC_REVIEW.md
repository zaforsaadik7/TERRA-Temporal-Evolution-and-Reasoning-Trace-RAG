# Static review of Antigravity-0037

8 October 2026. Codex. Read the complete proposed script embedded in Antigravity-0037; did not execute, save as executable, import runtime engines or modify manuscript/data. Verdict: evidence direction supported; proposed script requires corrections before execution.

## Blocking defects

1. Category keys do not agree. `cohort_data` defines `CatA_gross` etc., but `cat.split('_')[0]` returns `A` for `A_Factual`; lookup becomes `A_gross` and raises KeyError on the first row. Use an explicit exact-category mapping. Include a synthetic fixture using actual canonical category names, not invented keys.
2. The fixed output directory uses `exist_ok=True` and files open in `w` mode. A repeat overwrites evidence. Validate inputs before creating a unique new output directory; exclusive-create every output and fail on collision. Preserve partial outputs on failure rather than deleting or overwriting them.
3. `assert` is not an integrity gate: optimized Python disables it. Use explicit exceptions/nonzero termination. Require the pinned full source hash, 350 unique nonempty query IDs, exact category counts 100/100/75/75, route counts 110/240 and full expected category/route cross-tab.
4. Default missing total/sleep to zero and UNKNOWN routes can silently produce false measurements. Require fields and finite numeric values, reject booleans, nonnegative gross/sleep, and sleep <= gross. Do not clamp negative net latency with `max`; record invalid data and fail instead. The reviewed canonical construction has no clamp.
5. Only a pre-read hash is checked. Read/hash the same source bytes used for parsing, then rehash in a guarded finalization path even on failure. Record before/after identity and fail on drift; do not print SUCCESS without completed evidence writes and integrity checks.

## Reproducibility requirements

Use explicit percentile `method='linear'`; record Python/NumPy versions, script SHA256, SD denominators and formulas. Retain full-precision ledger/summary values (rounding for display separately) and serialize JSON with `allow_nan=False`. Include overall gross/net and category cohorts as well as routes so all TERRA latency cells can be checked. Baseline cells need their own evidence check later; a TERRA-only export must not certify the whole supplement table.

Synthetic tests should cover real category keys; missing/duplicate IDs; unknown category/route; missing, NaN, negative and invalid sleep values; wrong input hash; output collision; source drift; output failure. Tests must use temporary synthetic files, never the real data/store. No firewall, model or vector-store harness is needed for pure JSON arithmetic.

## Accuracy corrections to the peer report

- Section 1.3's “0/75 refusals” and “29/75 refusals” are generator calls, not refusal counts. Category C has 0 generated; Category D 29 generated; their refusal measures are distinct.
- “Zero code runs” conflicts with the relayed transcript's inline Python arithmetic. Describe this as read-only arithmetic, no runtime/model experiments.
- NumPy is a third-party dependency; “zero runtime dependencies” is inaccurate. The relevant claim is no pipeline/model/store dependencies.
- Category/route numerical correspondence establishes a population-label mismatch, not definitive historical author intent or the exact generator lineage. Avoid “exact root cause discovered” unless the historical generation code is traced.
- Lack of local public-release evidence supports withdrawing the release claim; it does not prove no public copy exists anywhere.
- Adding post-hoc p=0.625 is a new reported statistic, albeit derived from existing data; it is not literally zero numerical-text change. Pin paired-label evidence and obtain bounded wording approval before applying it.

Main disclosure proposal remains appropriate. No execution, manuscript patch, numerical override, supplement reconstruction or promotion performed by this review.
