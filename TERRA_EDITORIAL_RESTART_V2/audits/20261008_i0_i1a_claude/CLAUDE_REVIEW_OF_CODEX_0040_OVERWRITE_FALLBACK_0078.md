# Claude review of Codex-0040 / Codex-0020 (claude-0078)

Claude, NOT independent. Static only: nothing executed, no store opened, log not rerun.

Reviewed: script d1a603b1...0f0, tests 9bd30ba3...0f0a (as staged).

## Confirmed repaired
Cleanup now runs before status determination and serialization (lines 1136-1157). A cleanup exception is recorded as `CleanupRestorationError`, `network_guards_uninstalled` is set False, and status becomes FAILED (lines 1162-1168) before the report is written. Test 18 (line 1032) covers it through `mock_cleanup_fn`. A second idempotent `uninstall_network_guards()` in the inner `finally` is harmless.

## Confirmed remaining (Codex's condition)
Lines 1188-1195: if `write_and_verify_report` raises, the handler opens `report_file` with mode `"w"` and dumps the state. Consequences:
1. If the primary failure was exclusive-create collision (`"x"` at line 434, file already exists), the fallback truncates and overwrites a pre-existing audit report. That defeats the exclusive-creation safeguard.
2. It runs when `report_file` is non-None but without checking `path_validation_succeeded`, so it can write through a path the lifecycle already refused.
3. `json.dump(..., default=str)` bypasses the `allow_nan=False` policy, so the fallback can write non-finite or stringified values into a status-bearing report.
4. If the primary write succeeded but read-back failed, the fallback overwrites the run's own file; the failed read-back evidence is lost.

Required, as Codex asks: delete the fallback. Stderr output and nonzero exit are sufficient. Add a lifecycle test that pre-creates a sentinel file at the run's report path (via an injected deterministic run id or path), runs the lifecycle, and asserts the sentinel is byte-identical afterward, status FAILED, exit nonzero, and the error recorded.

## Gate
No other change requested. Run remains unapproved; still needed: final checkpoint, user-recorded offline arrangement, user authorization. No manuscript, data, original-store, 10k, API or promotion action is authorized. Relay to Antigravity is the user's.
