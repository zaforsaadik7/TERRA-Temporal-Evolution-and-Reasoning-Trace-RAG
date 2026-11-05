# Semantic mapping repair after the failed user attempt

23 October 2026, Asia/Dhaka. Codex implementation self-verification. The user approved fixing the two defects and targeted synthetic tests only, explicitly without another run. Prior permission/packet/evidence/locks are preserved; they are not reused or overwritten.

## Corrections

1. `offline_smoke_bindings.windows_runtime_bindings` resolves the actual boundary .ps1, PowerShell executable and kernel32.dll by their exact expected paths in reviewed member identities. It cannot select the boundary list-manifest JSON as a script. `offline_smoke_production.decode_packet` now rejects non-absolute/non-.ps1 script paths before any native adapter or protected-copy construction.
2. Shared `relative_inventory` uses PureWindowsPath relative parts serialized with as_posix(). Source and cache key/rel_path values use that same function. Expected snapshot aggregation now uses these canonical slash keys. New production decoder checks reject backslashes, aliases/traversal, mismatched rel_path or invalid identity fields rather than discovering the mismatch only after a failed run.

No native adapter/lifecycle algorithm or network policy was weakened to make tests pass. The existing Manager.compute_manifest, assert_manifest_parity and issue_isolation_receipt remain authoritative for canonicalization and copy parity. Empty-map rejection remains the protected lifecycle's existing responsibility; synthetic minimal decoder fixtures are not relabelled complete inventories.

## Targeted regression coverage

New named test module: tests.test_offline_smoke_semantic_mapping_synthetic (10 tests).

- Reproduces the old backslash-key failure with real assert_manifest_parity on nested temporary fake files.
- Checks source AND cache normalized entries against real compute_manifest output.
- Builds tiny temporary synthetic snapshot/disposable copies and compares the expected aggregate with a real lifecycle-issued synthetic receipt. No SQLite engine/model is opened; ordinary fake file bytes only.
- Requires the actual boundary .ps1 row and rejects a manifest-only substitute.
- Exercises the real Windows command builder with a fake executor and asserts the -File argument selects the .ps1; no PowerShell boundary process or firewall command is executed by that test.
- Exercises the real production decoder for the exact JSON-script and source/cache separator mistakes, asserting specific rejection reasons.
- Checks a complete synthetic production-shaped packet with corrected native paths and actual normalized temporary inventories.

Focused command ran semantic-mapping plus binding modules: 19 tests, all passed in 0.125 seconds. Final command used exactly the prior 25 named modules from reports/compact_manifest_repair_20261023_01/regression_modules.txt plus bindings, user-launcher and semantic-mapping modules (28 total): **535 tests in 25.337s; 533 passed, two skipped; exit 0**. Expected collision/fatal diagnostic text is from deliberate negative fixtures, not unittest errors. Prior unmodified suites include PS5.1 parser/function-only temp tests; no launcher main or B001 attempt occurred. This is a result record, not a claim to be a full verbatim console transcript.

## New invalid draft, not a freeze

`build_repaired_draft.py` uses the corrected shared helpers and preserved inventory evidence, not new real-store/model reads. It writes fresh artifacts here without touching prior records. Source closure now lists 31 modules because the decoder uses the binding validator. Current changed code bytes are reflected; unchanged runtime/assets remain represented by saved identities, not a fresh filesystem certification.

production_shape.REPAIRED_UNAPPROVED.json is 17,946 bytes; SHA-256 28c408e7caa501c7c580a2b219d7e71c77dbbfa6bdc1a265a423c2a9e56e9cdd. Actual boundary script path and separate boundary manifest path are recorded in assembly_checks.json. Source keys, cache keys and rel_path values are forward-slash canonical. Corrected expected snapshot aggregate: d567f61720dcd645a84bb77abebb24ccb71afbcace0e52012fa7f3d7994cb519 (the change is serialization, not new source bytes).

The draft proposes fresh absent candidate paths but creates no run directories and contains null authority. Historical build_decision.py/freeze_data.py scripts and executed artifacts are retained as evidence, not current preparation entry points. Do not rerun those archived builders, reuse the previous command, or repin the failed attempt.

## Remaining gates

All Python/native/executor and PowerShell launch holds remain false; root anchors are null. Old outer attempt lock remains present. No model/tokenizer initialization, real database connection/copy, firewall query/change, Windows Job use, API call or manuscript/statistics edit in this repair. No new authentic executable packet or approval is created.

Next: static/synthetic peer review of actual changes, tests and fresh invalid draft. Any later launch needs a fresh full identity/freeze review and separately renewed dated permission; passing these tests alone does not certify full Windows lifecycle or close all possible remaining integration risks.
