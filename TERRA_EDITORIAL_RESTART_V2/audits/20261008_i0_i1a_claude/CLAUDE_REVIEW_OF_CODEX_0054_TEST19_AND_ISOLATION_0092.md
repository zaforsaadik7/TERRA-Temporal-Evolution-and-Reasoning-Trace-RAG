# Claude review of Codex-0054 / Antigravity-0029: production isolation and the Test 19 collision claim (claude-0092)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I did not execute or parse PowerShell, run Python or the suite, query the firewall, or open any Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

## 1. Identity and diff provenance (reproduced)

| Artifact | My SHA-256 | Size |
| --- | --- | --- |
| scripts/execute_offline_diagnostic_runbook.ps1 | 5891dea40628e63ec9de38ec1ff36d2f0cbac83b86b2fe8c9a15ef2f4d686021 | 775 lines, 38,441 B |
| scripts/test_execute_offline_diagnostic_runbook.ps1 | ebf5194afc2abcb84c77d24f872fbb117f1897494c33372da6138bc220da28a0 | 438 lines, 23,859 B |
| evidence/execute_offline_diagnostic_runbook_checkpoint_6b2e3a.ps1 | 6b2e3abf803e7453a10b9096b8fd8a1de24bb400b5bc1381e01754f05399ccb9 | 30,449 B |
| evidence/runbook_6b2e3a_to_5891de_exact.diff | 63be8ed8983bd10ec6a079fddb45b64bf34c28c556a3bb4449c562e6ef03e9a9 | 36,303 B |
| evidence/test_execute_offline_diagnostic_runbook_log_0032.txt | fdd1e923092ba5abd102ce752b114016a0d82da2776f21d10e416807dfdbb96d | 2,313 B |

All match Codex-0054. Codex noted that a hash-verified diff is not a round-trip certification and that none was done. I did one: applying the saved diff with `patch` to the preserved 6b2e3abf checkpoint produced a file whose SHA-256 is exactly 5891dea4.... So the diff is complete and sufficient for that pair of runbook versions. That says nothing about the test file's own history (no preserved test checkpoint diff was in scope here).

The saved log is bound to the exact hashes of both files, records PowerShell 5.1.19041.7725 (Desktop), the OS version, a timestamp and the invocation line, and reports 20/20. That is a real improvement over the prior log. I did not rerun anything; it remains a peer-produced record.

## 2. Source repairs: accepted at source level (read, not run)

- **Production rejects test configuration** (lines 96-117): without `-SimulationTestMode`, any non-empty `-TestConfig/-TestConfigJson` exits 1 before any action. With the switch but no config, it also exits 1. This closes my claude-0091 finding A: in a production invocation `$TestConfig` is necessarily empty, so every `ContainsKey` hook is inert. An explicitly bound empty `-TestConfig @{}` is allowed and harmless; the eventual command should still be parameterless, as Codex says.
- **Simulation cannot fall through to live operations.** In test mode, missing `MockPreHashes`, `MockOtherProcesses`, `MockServiceStatus`, `MockProfiles`, `MockPostHashes` throw (lines 317, 362, 411, 428, 661); the collision step throws unless mocked (482-484); rule creation throws unless `SkipActualFirewall` is true (513-515); the native call throws unless `SkipActualExecution` or `MockChildExitCode` is given (567-577). The real `New-NetFirewallRule` and `& $pinnedPy` sit only in the `else` of `if ($isTestMode)`.
- **Simulation identity is recorded**: execution mode, bound parameter names, mock parameter names (153-168), `SIMULATED_SUCCESS` as a distinct status (741), `actual_firewall_enforced`/`actual_native_invoked` false in simulation.
- **Transcript closes before the terminal status is decided and serialized** (705-727, then 730-760), and a transcript-stop failure now yields `OPERATIONAL_FAILURE` in the record and exit 1. The circular saved flags were replaced by `terminal_record_attempted`.
- **All expected profiles required**, and a **shared rule check** (`Assert-Rule-Properties`, 198-218) is used by both branches.

I did not verify the profile-completeness code in detail or any runtime behavior.

## 3. Test 19: Codex's blocker is correct

Test 19 (test file lines 373-391) creates `runbook_mock_sentinel_run/runbook_pre_execution_record.json` with sentinel bytes, calls `Invoke-RunbookTest` once, and then rereads and rehashes the sentinel. The runbook builds its own run directory from timestamp, PID and GUID (script 114-122), so it never targets the sentinel's directory. The call's result `$t19Res` is never used, there is no assertion on exit code, error text or the attempted path, and the in-test comment itself says "let's test Save-Exclusive-Record directly" but the test never does. The test therefore passes whatever the writer does. The log line "Pre-Execution Sentinel File Unchanged on Disk" is accurate as worded, but any claim that it shows collision protection is unsupported.

Related gap: Test 13 is a mocked rule-name collision (`MockCollision`), not an evidence-file collision. Neither the file-level guard (`Test-Path` plus `FileMode.CreateNew`, script 221-249) nor the directory-level guard (273-276) has a test that actually triggers it.

## 4. How to repair it (narrow, no production hooks)

Running the whole script cannot reach the file guard: the directory guard at 273-276 fires first, and the run ID cannot be fixed. Two clean options:

1. **Test the real function body.** In the test file, parse the runbook with the PowerShell AST (`[System.Management.Automation.Language.Parser]::ParseFile`), extract the `Save-Exclusive-Record` function definition from the live script bytes, define it in the test scope with the few variables it reads (`$runEvidenceDir`, `$evidence`, `$isTestMode`, `$TestConfig`), and call it on the exact pre-existing sentinel path in a temporary tree. Assert: it returns false; the error list contains the collision reason naming that path; a second call does not alter bytes; the sentinel's SHA-256 is unchanged; no sibling or fallback file was created.
2. **Add the directory-collision case** by invoking the runbook in simulation with a pre-existing directory of the same run ID only if a test-mode run-ID override is added; I do not recommend adding production surface for this, so prefer extracting that guard into the same AST-tested form or accepting that it is covered by inspection and said so.

Controls required: (a) a mutated copy of the function with the `Test-Path` guard removed must still leave the sentinel intact (shows `CreateNew` is itself protective); (b) a mutated copy with both the guard removed and `CreateNew` replaced by `Create` must overwrite the sentinel and fail the assertion, proving the test can detect a regression. The mutations are done on an in-memory copy of the extracted text, never on the live file.

Also issue an addendum correcting any statement that Test 19 shows "Exit 1 + sentinel untouched", preserve the current test checkpoint, and return new hashes plus a bound log.

## 5. Notes (not blockers)

- `actual_firewall_enforced` is set to true right after `New-NetFirewallRule` returns and before read-back (script ~535), and `actual_native_invoked` before the call. They mean "attempted". Rename them or document that. I agree with Codex.
- The transcript is closed before the final outcome banner and the terminal-record save, so the transcript does not contain them; the terminal JSON is the record of the outcome. Optionally compute the transcript's SHA-256 after closure and include it in the terminal record.
- `SIMULATED_SUCCESS` exits 0, same as a real success. The distinction lives only in the record and banner; anyone reading only the exit code must not treat a simulated run as a real one.
- `Test-Path` followed by `CreateNew` is redundant but harmless; `CreateNew` is the authoritative guard.
- Unreadable-process visibility remains only a recorded warning; do not promise no effect on other processes. Manual recovery still starts with a suppressed query, and a failed query is not proof of absence (as Codex says).
- The synthetic suite still performs temporary file and transcript operations and reads script hashes; "synthetic" here means no firewall, no Python launch, no protected-file access.
- Simulation without an `EvidenceBaseDir` override would default to the project evidence path; this suite supplies temporary paths.

## 6. Verdict and boundaries

Runbook source: the earlier defects (claude-0090/0091 and Codex-0052/0053) are repaired at source level in my reading, including the production test-hook exposure. Operational gate: pending the one Test 19 correction, then a joint close. Diagnostic and harness gates are not reopened.

A runbook is a proposal, not authorization. No run, firewall install or removal, network change, 10k run, API call, threshold tuning, manuscript edit or promotion is authorized. Still needed from the user after the gate closes: a dated offline-arrangement choice, a decision on any other `python.exe` processes found at launch, and a separate single-run permission. Historical calibration (main line 210) stays OPEN. Relaying this to Antigravity is the user's.
