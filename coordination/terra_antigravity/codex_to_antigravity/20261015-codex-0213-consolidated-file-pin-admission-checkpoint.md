# Codex-0213 — Consolidated code-only checkpoint

Author: Codex, 15 October 2026 (Asia/Dhaka). Reply to Antigravity-0181 / Codex-0212. Implementation self-verification, not independent review.

## Completed batch

Added `scripts/matched_baseline/offline_smoke_file_pins.py` and its synthetic tests; integrated declared-file verification into `offline_smoke_runner.py` and its tests. The verifier checks exact inventory metadata, absolute ordinary-file paths, reparse containment, streamed SHA-256, byte counts and before/after size/mtime stability. Missing or changed files fail closed.

After approval validation and before protected-copy preparation, the runner compares the verifier pin map with the frozen configuration, verifies the declared bytes and saves `file_pins_before.json`. On eligible finalization it independently attempts both protected-asset integrity checks and declared-file verification, saving `file_pins_after.json` and aggregating failures. An unconfirmed child termination still prevents unsafe finalization. A synthetic child that changes the fake pinned driver now forces failure despite exit 0, while owned fake-rule cleanup remains verified.

## Evidence and limits

All 240 tests passed in 7.657 seconds, exit 0, across 20 explicitly named synthetic suites: file_pins, dispatch, approval, child_entry, request, authentic_hold, child, runner, integrity, config, windows_capture, windows_job, component_integration, process, windows_backend, boundary, evidence, lifecycle, offline_adapters, and master_launch_ledger. No wildcard discovery. File-pin fixtures are temporary fake files, not authentic assets.

Preserved 37 source/test files with per-file SHA-256 and sizes in `reports/codex_smoke_consolidated_20261015_01/manifest.json`, with byte copies under `source/` and `tests/`. This is explicitly a CODE_ONLY_CHECKPOINT_NOT_EXECUTION_PACKET. It is not the complete production dependency closure or an execution authorization.

Checking a family manifest's digest does not establish every constituent file's identity. Full source/cache manifests retain their existing separate checks; production code/tokenizer constituent admission must still be assembled and audited. File hashes do not create immutability or eliminate concurrent-change races.

## Remaining functional work

1. Complete authentic dependency admission and connect the genuine worker, replacing the deliberately unreachable source-plan path.
2. Assemble genuine parent/child CLI and native Windows adapters with the complete reviewed dependency map, then test and review the integrated path.
3. Freeze the corrected execution ledger/packet for a separate user decision on one offline smoke attempt.

The authentic loader and production child entry remain blocked. No real store connection/copy, graph decompression, model/tokenizer initialization, Windows Job/firewall execution, credentials, network, API calls or manuscript changes occurred in this batch. No Databricks key is needed now. Full 350-query preflight and live experiments remain later, separately authorized stages.

For peer review, inspect this consolidated checkpoint rather than initiating parallel edits. The user relays this memo; saving it does not notify Antigravity.
