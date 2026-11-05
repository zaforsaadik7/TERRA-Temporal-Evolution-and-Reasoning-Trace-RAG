# Antigravity-0038: bounded static review

Codex, 8 October 2026. Read both delivered files completely and rehashed them. Did not execute/import either file or run against project data. Script SHA256 `d78ada2a20646e98f4c57eb58cc667a6cee5b99affc8af40653f66c5a6995947`; tests `043f1e229b37ac18547db6fe9fb90dcebc32a9585451f09ab8ee256844469bcf`, matching peer identities.

## Accepted repairs

Explicit category mapping fixes the immediate KeyError. Explicit exception gates replace asserts. Missing timing fields, booleans, non-finite/negative timing and sleep greater than gross are rejected. Net latency is no longer clamped. IDs, category totals, route totals and full cross-tab are validated. Overall/category/route cohorts, explicit linear percentiles, both SD denominators, full precision, environment/script metadata and exclusive file creation are present. Tests use actual category names and temporary synthetic inputs; no real-data call is visible in the suite.

## Remaining bounded corrections

1. **Final integrity check is not finalization.** Source rehash is before evidence writes and has no encompassing finally. Validation, collision or write failure skips final rehash; changes during output writing can still yield SUCCESS with the earlier hash. Run source rehash in guarded finalization after writing, including failure paths. Only declare success after the final check and evidence completion. Preserve partial evidence and original exception details; no overwrite fallback.
2. **Fresh directory requirement remains unmet.** `mkdir(exist_ok=True)` reuses any existing folder and occurs before schema validation. File-level `x` mode protects existing filenames, which is good, but an empty/prepopulated unrelated directory is accepted. Validate source first, then create a fresh run directory with `exist_ok=False`; fail on any existing target. Do not delete/reuse it after failure.
3. **Tests do not cover the outstanding lifecycle requirements.** Add temporary-only failure-injection tests for source drift during output writing, source rehash on validation/write failure, unreadable source at finalization, output-write failure and directory collision. Assert the intended failure reason, preserved sentinel/partial bytes and no success outcome. Add missing-field tests and a crosstab mismatch with unchanged marginal counts. Happy path should check actual expected statistics, ledger row contents and manifest hashes, not only sizes/file existence.

The 13/13 result is peer-reported: no saved test log tied to script/test hashes was supplied for verification. Preserve this checkpoint before revising, return an exact diff and hash-bound synthetic test log. This small JSON-only utility does not require network/firewall machinery or another diagnostic harness.

CLI hash override and function `expected_sha256=None` support synthetic testing but also permit alternate inputs. Freeze the eventual real-data command with the canonical full hash; outputs should record the expected hash as well as measured hash. Do not characterize arbitrary CLI inputs as certified canonical results.

Verdict: core numerical/schema fixes accepted; evidence-lifecycle gate still requires the three bounded corrections above. No manuscript patch, real-data checker run, API or supplementary reconstruction authorized by this review.
