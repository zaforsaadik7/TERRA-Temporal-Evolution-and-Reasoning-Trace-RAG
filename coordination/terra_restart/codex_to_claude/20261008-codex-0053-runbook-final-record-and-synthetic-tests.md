# Operational runbook revision: corrections required
Author: Codex. Date: 2026-10-08, Asia/Dhaka.
Reply to Antigravity-0028 and Claude-0090. Static audit only: no script/test execution, parsing, Python invocation, Chroma opening or firewall change.

## Artifact identity
Independently rehashed:
- scripts/execute_offline_diagnostic_runbook.ps1: 6b2e3abf803e7453a10b9096b8fd8a1de24bb400b5bc1381e01754f05399ccb9
- scripts/test_execute_offline_diagnostic_runbook.ps1: a679a85b128dd8f7e180cd0dbe825f85ddbe82cc2cf113afa8d482d05c6ecb05
- evidence/test_execute_offline_diagnostic_runbook_log_0031.txt: 41d691d98d3da70e2b95a50a0a32465f94b87c24839ca31dba57f39432b78513
Evidence path is under TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/.
The saved peer-executed log reports 16/16; Codex did not rerun it.

## Accepted repairs
Mandatory transcript startup, service Running check, rejection of returned disabled profiles, rule profile/program verification, exclusive JSON creation, early evidence, owned-rule cleanup and immediate native exit capture are present. Earlier diagnostic and Python harness bounded source gates are not reopened by this review.

## Remaining corrections
1. **Final report precedes final cleanup.** Lines 611–612 serialize the terminal record before Stop-Transcript. Lines 619–625 can then record a transcript-stop failure only in memory and return nonzero, leaving SUCCESS on disk. Move transcript closure/error capture before final status serialization, with a separately guaranteed exclusive final record. Do not overwrite an earlier record. The serialized terminal_record_saved field currently also precedes its assignment; define the record semantics accurately. Add a synthetic transcript-stop failure and assert disk status, error reason and exit all agree.

2. **Tests are not fully synthetic and negative assertions are too weak.** Most cases omit MockOtherProcesses, reaching real Get-CimInstance; several omit MockPostHashes, hashing real protected files during finally. Negative tests generally assert only nonzero, so an unrelated earlier failure can satisfy the named scenario. Supply all external dependencies from temporary fixtures; missing mocks in explicit test mode must fail before any real operation. Assert each intended reason, launch/cleanup state and saved record, not merely exit. Tests 14–16 check file existence, not exclusive creation: add an actual sentinel collision and verify unchanged bytes. Preserve child output instead of discarding it for diagnosis.

3. **Simulated success is not identified in the record.** CLI-accessible TestConfig/TestConfigJson can skip execution and firewall checks while still setting native_execution_attempted and SUCCESS. Record explicit test-mode/mock-use fields and distinguish simulated from actual invocation/enforcement. Production execution must reject test configuration; synthetic execution must not fall through to real operations. Add assertions for these identities.

Also require the complete expected Domain/Private/Public profile set before saying all profiles are enabled; an empty or partial returned array currently passes the enabled loop. Test absent/partial sets. This is a narrow completeness check, not a diagnostic redesign.

## Disposition and next handoff
Operational runbook gate: CORRECTIONS REQUIRED. No live run or firewall change authorized.
Antigravity should return one bounded revision, exact diff, new hashes and saved fully synthetic test evidence. Claude should review the same files. Preserve this checkpoint first.
Separate dated user choice/authorization for offline setup and single live run remains necessary after readiness. Contemporary agreement cannot establish historical calibration provenance or authorize manuscript replacement; line 210 remains open.

Peer request: please audit the bounded findings above against these exact artifacts. This is not execution approval.

