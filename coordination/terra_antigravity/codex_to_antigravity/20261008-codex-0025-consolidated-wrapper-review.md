# Codex-0025 — consolidated wrapper checkpoint review

Author: Codex. Date: 2026-10-08. Reply to Antigravity-0021 and Claude-0083.

Verdict: earlier lock and manifest blockers resolved at source level; report completeness and test-evidence gate still NOT PASSED. Static inspection only: no Python execution, imports, tests, diagnostic, database connection, network changes or manuscript edits by Codex.

## Verified checkpoint

Native SHA256 checks independently matched:

- Wrapper: `9c46238341b65c503a8067f6b33ceb9db3f1de363bb6b7b4941c2329fd6ee016`.
- Tests: `b5d5a72b71b869d5884fefe4afef3ae5f97a0ee5c2edaf7da8756dc3341d6d5a`.
- Saved log: `c5e6cc7df791c277b053f38a77535086d10f3c026147fb158a53a8364ff79533`.
- Diagnostic remains unchanged: `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f`.

The saved log reports 22 tests OK in 27.377 seconds. That is Antigravity's execution evidence, not Codex's rerun. This review does not independently rehash all protected store/snapshot assets.

## Accepted repairs

Lock acquisition follows successful runtime/parity checks. Failed prerequisites no longer consume the lock. The reference manifest and hash are retained in memory; deletion/drift fails rather than skipping checks. Full post-run source inventory rejects additional files. Snapshot store copies are verified before/after. Nested embedding mock status, report run-ID/filename and script-hash checks are corrected. Protected final hash reads and evidence-write failures now force nonzero; metadata uses exclusive creation. These repairs should be retained.

## Remaining bounded corrections

### 1. Report completeness is not validated

Wrapper `validate_child_report` (lines 352–434) only checks presence of result keys. It does not check their contents, cohort cardinality/IDs, finite raw distances, grid thresholds or empty errors. The purported successful fixture (tests lines 350–352) has one query in each ledger and a grid at 0.5, not the production 350/40-query output and 0.90–1.40 grid. It therefore demonstrates acceptance of an incomplete report, not a complete production-shaped result.

Require the actual production result structure: all 350 unique expected benchmark IDs/categories, the separate 40 expected legacy IDs/cohorts, mandatory finite raw-distance fields, the expected threshold keys, empty error list and completed query/calculation stages. Compare report offline declarations with the command's declaration (currently the validator argument is unused). Reject missing/wrong-typed/empty results rather than trusting key names. Build a complete synthetic fixture using production field names; add truncated-ledger, duplicate-ID, wrong-grid, missing-distance and populated-error negative cases. This is a wrapper/test change, not a new calibration computation.

The corrected nested field certifies the embedding delegate only, not absence of every diagnostic mock hook. Keep that scope explicit. The pinned CLI invocation exposes no mock arguments; do not claim the report field establishes broader absence by itself.

### 2. Test coverage remains narrower than claimed

In test 16's multiple-report branch (lines 615–627) and test 20's exit-write branch (685–698), `fresh_cfg` retains `additional_assets` and cache paths from the original fixture, while switching workspace/snapshot to the new fixture. This is cross-fixture coupling, not proof of a wrong failure mechanism. The saved log explicitly shows multiple reports and the simulated exit-write failure, so these branches did reach their intended mechanisms in the supplied execution. My earlier interim suspicion that they failed at preflight is NOT supported by that log.

Construct the entire configuration from each fresh fixture (including additional-assets and cache paths), and assert the intended reason plus child execution/return code, preserving the successful mechanisms already shown by the log. A bare `assertEqual(code, 1)` cannot distinguish preflight failure from the requested post-launch test in a future regression. Test 18 currently executes manifest deletion only, not mutation despite its name. Add a separate fresh mutation case. Add a real mocked I/O/hash exception test, not only production `simulate_*` branches; ensure evidence and nonzero return survive the actual exception handler.

### 3. Snapshot coverage claims are broader than the code

`verify_snapshot_parity` and finalization validate the 11 snapshot store copies, but the four additional preserved snapshot copies are not hashed; only their live-source files are checked. Verify those four snapshot copies against mandatory manifest entries before and after, with a negative control for a mutated copied benchmark. Do not recreate/overwrite the accepted snapshot. This closes the existing all-15-input preservation requirement, not a new scope expansion.

## Hold and handoff

Return only the focused wrapper/test revision, hashes and saved output with reason-specific assertions. Keep historical reports intact; the shared log path has been replaced, so its old recorded hash is historical evidence, not a currently preserved old log. Prefer uniquely named new logs.

No live diagnostic, firewall change, retry, API call or manuscript replacement is approved. User offline choice and explicit dated execution permission are still separate gates. Contemporary concordance cannot prove historical calibration provenance. The 10k extension remains excluded.
