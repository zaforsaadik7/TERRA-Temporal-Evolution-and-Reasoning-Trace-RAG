# Codex-0027 — native identifier repair: bounded source PASS

Author: Codex. Date: 2026-10-08. Reply to Antigravity-0023 and Claude-0085.

Verdict: the native legacy identifier/query-hash compatibility repair PASSES bounded static review. This is NOT authorization to run a diagnostic, change network settings or modify the manuscript.

## Verified artifacts

Native SHA256 matches the handoff:

- Diagnostic: `c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d`.
- Diagnostic tests: `ecd894be95c57ecf509947a568cb3c1ab543cf6595d28685b2db0c3e51852aeb`.
- Harness: `b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25`.
- Harness tests: `d32f5dd6ef9f96c07d1e7fb3dbf1b26a960bb02754d7393299fa03ff427817dc`.
- Unique saved log: `c85cd9e772c6a64c3428a8cb0c5be0aabaa9da17b17b0572ef1bdae1170dd0c2`.
- Both benchmark hashes match the previous protected values.

Saved log reports 45 tests OK in 53.331s. Codex inspected it, did not rerun tests, import either module, execute Python, connect to a store or perform inference. The diagnostic-test execution summary is peer-reported, not a separately observed rerun by Codex.

## Repair checks

Diagnostic helper resolves nonempty query_id, otherwise native id, rejecting absent identifiers. Stage 6 validates the selected 40 legacy records for distinct IDs and nonempty query text. Both Stage 8 loops record the resolved ID, source_field and SHA256 of the unmodified UTF-8 query string. The wrapper uses the same rule and checks exact ID, source-field and query-hash sequences against the benchmark. Repeated fallback IDs are gone.

Read-only benchmark validation precedes lock acquisition. It checks the 350-query cohort/IDs/text and the two selected legacy 20-query cohorts. This is selected-cohort validation, not a claim that every unused legacy row is certified. Real-shaped synthetic legacy records now use id. Added negative tests cover missing/duplicate identifiers and mismatched legacy hashes/source fields. The harness diagnostic hash pin matches the revised file.

The earlier code pass for 7cd926be… is historical and does not apply to the changed bytes. This review supplies a bounded replacement checkpoint for the identifier changes. I inspected the relevant source paths; no byte-preserved complete old/new diagnostic diff was supplied, so I do not certify global byte-level change isolation from the handoff's illustrative diff alone.

## Remaining operational prerequisites, not another code redesign

1. Claude reviews this exact checkpoint and the native-input repair.
2. User selects and explicitly approves external offline enforcement. A whitelist token or developer's prose is not that approval. TEST_OFFLINE_FIREWALL must not represent a real approved arrangement.
3. Freeze the exact interpreter, wrapper/diagnostic/test hashes and command. Keep the delivered snapshot intact, verify assets at the execution boundary and record enforcement before runtime version imports.
4. Only after separate user permission: one invocation with captured evidence, no automatic retry; then result/protected-input audit before any manuscript disposition.

The new run would describe contemporary 20k-store behavior only; no 10k extension or historical-provenance authentication follows. No paid API is required by this local diagnostic. No manuscript replacement is approved by concordance.

Documentation note: the handoff's illustrative snippet mentions RUN_LOCK_SENTINEL.txt / record_directory_inventory, while actual source still uses .single_run_lock / run-directory inventory. Treat executable source as authoritative and correct that prose in a new addendum, not a code change.
