# Claude review of Codex-0052 / Codex-0031 / Antigravity-0027: runbook script (claude-0090)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I did not execute PowerShell, parse the script, query the firewall, run Python or tests, or open any Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

Read in full: `scripts/execute_offline_diagnostic_runbook.ps1` (my SHA-256 873fa314394c39b81f76e999be525f37240cba33e938bbba4f9ea9ff0113ee61, matching Codex-0052/0031 and Antigravity-0027; 355 newline-terminated lines, Antigravity says 356), Codex-0052, Codex-0031, Antigravity-0027.

## 1. Codex's defects: all reproduced from the source

| # | Codex claim | Where I see it |
| --- | --- | --- |
| 1 | Profile enumeration never rejects a disabled profile; no service check; PASS text overclaims | Lines 164-171: `Get-NetFirewallProfile` results are only copied into evidence; line 171 prints "service and profile states verified". No `MpsSvc`/`Get-Service` call anywhere. Header item 5 ("Firewall profile enablement verification") and Antigravity-0027 item 4 ("verify that firewall service and profiles are active") are not what the code does. |
| 2 | `-Profile Any` recorded, not validated | Line 224 records Profile; checks at 228-231 cover Direction, Action, Enabled, Program only. Antigravity-0027 item 6 says Profile=Any is verified; it is not. |
| 3 | Transcript startup failure continues | Lines 63-68: catch only warns. |
| 4 | Evidence directory can be reused; JSON overwritten | Line 56 uses second-resolution time; line 59 `New-Item -Force`; line 94 `WriteAllText` truncates an existing file. `-NoClobber` on the transcript does not protect the JSON. |
| 5 | `Save-Evidence` failure skips transcript cleanup | Line 340 is unguarded and precedes `Stop-Transcript` (342-347); Stop-Transcript failure is silently swallowed (`catch {}`). |
| 6 | Outer catch `Write-Error` under `Stop` | Lines 249-251: with global `$ErrorActionPreference = "Stop"`, `Write-Error` is terminating; the explicit status/`exit` logic after `finally` (350-355) is then not reliably reached. |
| 7 | Other interpreter processes only warn; raw command lines saved | Lines 151-162: warning only, execution continues; line 156 stores `CommandLine`, which can contain secrets. |

Antigravity's "Both stop-and-verify claims are met" is therefore not supported for items 1, 2 and 7 in the source.

## 2. Additional findings from me

**A. Native-call robustness.** Line 240 runs the child under `$ErrorActionPreference = "Stop"`. Whether stderr output from a native program becomes a terminating error depends on the PowerShell edition and how output is captured (Windows PowerShell 5.1 versus PowerShell 7). The wrapper and diagnostic do write to stderr on failure paths. If that raises inside the `try`, `native_exit_code` stays null while the child may already have started or finished. Set `$ErrorActionPreference = "Continue"` only around the one native call, restore it, capture `$LASTEXITCODE` on the next statement, and record `$PSVersionTable` in the evidence. The script does not say which PowerShell edition is required.

**B. Locale-fragile absence test.** Lines 182 and 271 identify "rule not found" by matching the English message "No MSFT_NetFirewallRule objects found". On another message text this would fail closed before creation (safe), but after a successful removal at teardown it would mark `teardown_verified = false` and fail the outcome although the rule is gone. Test the error category (ObjectNotFound) or `FullyQualifiedErrorId`, and treat anything else as unverified.

**C. Evidence only at the end.** Nothing is written before the firewall rule is created and the child is launched. A crash, power loss or window close during the run leaves only the transcript. Create an exclusive "STARTED" record (with hashes, rule identity and PowerShell version) before creating the rule, and write the terminal record as a new, differently named file, never replacing the first.

**D. Directory created before any gate.** Lines 56-59 create the evidence directory and transcript before the elevation and hash gates. That is harmless to the protected inputs, but a failed gate then leaves partial records. It is acceptable only if the record is explicitly an attempt record and is never overwritten; a non-colliding name (timestamp plus random suffix, `New-Item` without `-Force`) is required.

**E. "Zero other processes" is not established.** `Get-CimInstance Win32_Process` can return a null `ExecutablePath` for processes the caller cannot inspect, and the filter compares by exact path. A "PASS: Zero other processes" message is stronger than the check. Record the count of processes with an unreadable path, and make any hit stop the run unless the user has already approved it. Save PID and path only.

**F. Manual recovery.** Lines 20-28 and Antigravity-0027 section 2 use `-ErrorAction SilentlyContinue` for the existence check (the pattern Codex asked to remove) and delete by Name without establishing that the rule is the one this runbook created. Recovery should show the rule's Description, program path and creation facts first, and delete only on a match.

**G. Enforcement not independent.** No check proves the rule is effective for the active network profile, that no third-party firewall is in control, or that the child is actually blocked. The Python-level socket guard is not firewall proof. Say this in the evidence and in the user-facing summary instead of printing "verified".

**H. Over-claim persists.** Antigravity-0027 section 3.3 says the rule "does not affect other software (such as browsers, IDEs, or cloud agent sessions)". Its own script warns at line 159 that other processes using that interpreter will be blocked. Only processes running that exact `python.exe` are affected, but I cannot see which tools those are. Remove the unconditional wording.

**I. Minor.** The handoff's Benchmark-350 hash transcription error that Codex noted: the script constant at line 49 is correct (8144fa81...). Line count 355 vs 356 is immaterial.

## 3. What I agree is fixed

Elevation gate (110-116); six pre-run and six post-run hashes of the interpreter, wrapper, diagnostic, both benchmarks and the SQLite file; exact rule Name; the `$ruleCreated` ownership flag, set only after `New-NetFirewallRule` returns (211), so a duplicate-name failure does not trigger removal; application-path read-back (216-231); immediate `$LASTEXITCODE` capture (241); removal with `-ErrorAction Stop` and an explicit verification step (259-282); and an outcome that cannot be SUCCESS if exit code, teardown or post-hashes fail (324-338). I did not verify these by running anything.

## 4. Requested revision and tests (agree with Codex)

Bounded runbook fixes only; the accepted diagnostic and wrapper are not reopened. Required: reject disabled applicable profiles and a stopped firewall service before the first Python launch; validate profile coverage; stop on other interpreter processes unless pre-approved (PID and path only); make transcript start mandatory; exclusive unique evidence paths with exclusive file creation; guarded `Save-Evidence` with nested transcript closure; nonterminating error reporting in the outer catch with an explicit terminal status; local `Continue` around the native call; error-category absence tests; a start record before rule creation; and corrected user-facing wording.

Tests must be fully mocked, in a temporary path, with no NetFirewall mutation and no Python launch: disabled profile; stopped service; wrong profile coverage; transcript start failure; evidence-path collision; evidence write failure with transcript closure still attempted; rule creation failure (no removal attempted); cleanup failure; nonzero child exit not masked by clean teardown; and clean teardown not masked by a zero exit when post-hashes differ. A syntax parse does not establish lifecycle safety.

## 5. Verdict and boundaries

Runbook script: NOT certifiable as it stands. The remaining defects are in the executable source, not the accepted diagnostic code. I have not verified any behaviour by execution.

A runbook is a proposal, not authorization. No run, firewall install or removal, network change, 10k run, API call, threshold tuning, manuscript edit or promotion is authorized. The user's dated offline choice and separate single-run permission are still outstanding. Historical calibration (main line 210) stays OPEN. Relaying this to Antigravity is the user's.
