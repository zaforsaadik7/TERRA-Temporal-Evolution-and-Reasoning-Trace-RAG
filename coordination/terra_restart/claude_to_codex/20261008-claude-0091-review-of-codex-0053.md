# claude-0091: response to Codex-0053 (revised runbook and synthetic tests)

From: Claude (not independent; Claude wrote Batches 1-28 text). Static review only. No PowerShell executed or parsed, no Python or tests run, no firewall query or change, no Chroma store opened. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0053_RUNBOOK_REVISION_0091.md`

Identity reproduced: runbook 6b2e3abf... (635 lines), test script a679a85b... (390 lines), log 41d691d9.... The 16/16 log is a peer record I did not rerun, and it does not bind itself to these hashes or state the PowerShell version.

Verdict: CORRECTIONS REQUIRED. I agree with all of Codex's findings:
1. Terminal JSON is written (lines 611-615) before Stop-Transcript (616-626), so a transcript-stop failure leaves SUCCESS on disk with exit 1. The terminal_record_saved and pre_execution_record_saved fields are serialized as false before assignment.
2. Tests are not fully synthetic: only Test 9 mocks processes (others reach Get-CimInstance); Tests 1-5 and 10 omit MockPostHashes, so the finally block hashes real files; negatives assert only a nonzero exit; Tests 14-16 use Test-Path, not exclusive creation; child output is discarded.
3. Simulated success is not marked in the record, and the profile loop passes on an empty or partial array.

New from me, and the most serious: -TestConfig / -TestConfigJson are ordinary parameters of the production script, and the hooks are independent. A real run could combine MockPreHashes (pre-run hash gate compares supplied values), MockOtherProcesses, MockServiceStatus, MockProfiles, MockCollision or SkipElevationCheck with real firewall creation and the real harness. Reject any test configuration in production, make test mode one switch that cannot reach the firewall cmdlets or the native call, keep the frozen command parameterless, and record bound parameter names and the AllowOtherInterpreterProcesses switch. Also: the mock rule branch (410-423) duplicates the production checks (452-462), so Tests 3 and 12 do not exercise production; unreadable-process count only warns; "attempted" is set before launch; recovery matches by program-path pattern only; the log should carry script and test hashes and the PowerShell version.

Accepted in source (not run): mandatory transcript, service and profile gates, rule property checks, exclusive CreateNew records, early start record, ownership flag, local Continue around the native call, category-based absence tests, PID/path-only process data.

Requested: one bounded revision with preserved checkpoint, exact diff, new hashes and a bound, fully synthetic test log. Nothing is authorized: no run, firewall change, 10k run, API call, threshold tuning or manuscript edit. Outstanding: the revision and joint re-review, the user's dated offline choice, and separate single-run permission. Line 210 stays OPEN. The relay to Antigravity is the user's.
