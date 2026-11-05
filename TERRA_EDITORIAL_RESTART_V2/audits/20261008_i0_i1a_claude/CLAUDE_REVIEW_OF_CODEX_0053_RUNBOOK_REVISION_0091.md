# Claude review of Codex-0053 / Antigravity-0028: revised runbook and synthetic tests (claude-0091)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I did not execute or parse PowerShell, run Python or tests, query the firewall, or open any Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

## 1. Identity (reproduced)

| Artifact | My SHA-256 | Lines / bytes |
| --- | --- | --- |
| scripts/execute_offline_diagnostic_runbook.ps1 | 6b2e3abf803e7453a10b9096b8fd8a1de24bb400b5bc1381e01754f05399ccb9 | 635 / 30,449 |
| scripts/test_execute_offline_diagnostic_runbook.ps1 | a679a85b128dd8f7e180cd0dbe825f85ddbe82cc2cf113afa8d482d05c6ecb05 | 390 / 16,761 |
| evidence/test_execute_offline_diagnostic_runbook_log_0031.txt | 41d691d98d3da70e2b95a50a0a32465f94b87c24839ca31dba57f39432b78513 | 1,323 B |

All three match Codex-0053. The log reports 16/16 passed. I did not rerun anything; the log is a peer-produced record I cannot verify. It does not state the hash of the script under test, the PowerShell version, a command line or timestamps, so it is not bound to these exact bytes except by file timing.

## 2. Accepted repairs (read in source, not executed)

Mandatory transcript (lines 207-217); firewall service `mpssvc` must be Running (333-344); returned disabled profiles are rejected (353-367); rule Direction, Action, Enabled, Profile and Program are checked on the real path (452-462); exclusive record creation with `FileMode.CreateNew` (152-185); early pre-execution record before rule creation (373-377); unique run ID with PID and GUID, no `-Force` (114-122, 202-205); ownership flag set after creation returns (435); local `Continue` around the one native call with immediate `$LASTEXITCODE` capture (472-486); category-based absence tests (393, 524); PID and path only for other processes (292-311); stop on known other interpreter processes unless explicitly allowed (318-323); improved manual recovery that checks the program path (23-53).

## 3. Codex's findings: all three reproduced

1. **Terminal record precedes final cleanup.** Lines 611-615 write `runbook_terminal_record.json` before `Stop-Transcript` (616-626). A transcript-stop failure then changes only the in-memory status and exit code; the file on disk keeps `SUCCESS`. Also, `terminal_record_saved` is serialized as `false` and only assigned `true` afterwards (611-612), and `pre_execution_record_saved` is likewise `false` inside the pre-record (373-374). The saved flags therefore never describe the saved file; define them as "this write succeeded", set outside the record.
2. **Tests are not fully synthetic and negatives are weak.** Reproduced from the test file: no test passes `MockOtherProcesses` except Test 9, so the other tests reach the real `Get-CimInstance Win32_Process` (script 300); Tests 1 to 5 and 10 omit `MockPostHashes`, so the `finally` block hashes real files, including the multi-hundred-megabyte SQLite file (script 559-564); every negative test asserts only `exit -ne 0`, so any unrelated earlier failure satisfies it; Tests 14-16 only check that files exist (`Test-Path`), not exclusive creation or unchanged bytes; child output is discarded (`2>$null | Out-Null`, test line 70). Test 3 and Test 12 feed `MockRuleFacts` into a separate branch that re-implements the rule checks (script 410-423), so the real checks at 452-462 are not exercised.
3. **Simulated success is not identified.** `SkipActualFirewall`, `SkipActualExecution`, `SkipElevationCheck` and the `Mock*` keys all produce `native_execution_attempted = true` and `SUCCESS` with nothing marking the run as simulated. The profile-set completeness issue is also real: the profile loop (353-367) passes on an empty or partial array.

## 4. Additional findings from me

**A. Test hooks can bypass real gates in the production script.** `-TestConfig` and `-TestConfigJson` are ordinary parameters (56-60). The hooks are independent, so a real run could be combined with, for example, `MockPreHashes` (the pre-run hash gate then compares supplied values, not the files), `MockServiceStatus`, `MockProfiles`, `MockOtherProcesses` (hides running interpreter processes), `MockCollision` or `SkipElevationCheck`, while firewall creation and the real harness still execute. Neither the run record nor the frozen command prevents or reveals this. This is the same class of defect as the diagnostic's in-production mock hooks. Required: in a production invocation, any non-empty test configuration must be rejected before any action; a test mode, if kept, must be an explicit single switch that can only select fully synthetic behavior and can never reach `New-NetFirewallRule`, `Remove-NetFirewallRule` or the native call; and the frozen command should be exactly the parameterless one. Separately, record `$PSBoundParameters` (names only) in the evidence. `-AllowOtherInterpreterProcesses` is also not recorded.

**B. Rule-check logic is duplicated.** Because the mock branch re-implements the checks, passing tests do not show that the production branch is correct. Move the checks into one function that both branches call, with the mock supplying only the input object.

**C. Process-visibility uncertainty is only a warning.** An unreadable-process count above zero (328-330) does not stop the run. That is acceptable only if the user is told in plain words and the count is in the evidence; the checks cannot see processes they cannot read.

**D. "Attempted" is set before the launch** (470). If the interpreter fails to start, the record says an execution was attempted. Rename or set it at the actual launch point, and record the start and end times of the native call.

**E. Manual recovery.** The ownership test matches the rule by program-path pattern only (`-like "*pythoncore-3.14-64\python.exe*"`). Also compare the Description text and require the exact Name; keep the absence check by error category, as written.

**F. Test log binding.** The log should include the SHA-256 of the script and test file, the PowerShell edition and version, the invocation line, and per-test the specific reason asserted.

**G. Test file header** says 13 tests; the run reports 16 assertions. Immaterial, but it shows the header was not updated with the code.

## 5. Verdict

Operational runbook gate: CORRECTIONS REQUIRED (I agree with Codex). The core firewall lifecycle logic now reads well, but I cannot support certification while the production script accepts live-gate-bypassing test hooks (A), the saved terminal record can disagree with the exit status (3.1), and the tests prove only "non-zero exit" (3.2). I verified none of the runtime behavior.

Requested next revision, one bounded change: reject test configuration in production; mark simulated runs in the record; define saved-flag semantics; close the transcript before the terminal record is written, with a separate exclusive final record that cannot overwrite; require the full Domain, Private and Public profile set; one shared rule-check function; fully synthetic tests (every external call mocked, missing mocks fail before any real operation); assertions on the specific reason, record contents, launch and cleanup state, and a real sentinel-collision test that checks unchanged bytes; child output preserved; a bound test log. Preserve the current checkpoint first and provide an exact diff and new hashes.

## 6. Boundaries

A runbook is a proposal, not authorization. No run, firewall install or removal, network change, 10k run, API call, threshold tuning, manuscript edit or promotion is authorized. Still needed from the user: a dated offline-arrangement choice and separate single-run permission, after a joint re-review. Historical calibration (main line 210) stays OPEN. Relaying this to Antigravity is the user's.
