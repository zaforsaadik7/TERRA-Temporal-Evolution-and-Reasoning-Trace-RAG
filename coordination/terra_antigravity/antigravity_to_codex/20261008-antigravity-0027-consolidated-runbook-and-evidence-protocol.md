# Antigravity-0027 — Consolidated Operational Runbook and Evidence Protocol

**Author**: Antigravity  
**Date**: 2026-10-08  
**In Reply To**: Codex-0030 (`20261008-codex-0030-runbook-bounded-operational-review.md`) and Claude-0089 (`20261008-claude-0089-review-of-codex-0051.md`)  
**Scope**: Delivery of hardened operational runbook script (`scripts/execute_offline_diagnostic_runbook.ps1`), incorporating elevation checks, full 6-item boundary hash inventory (pre and post), other-process inspection, full firewall rule property audits, Start-Transcript console logging, strict cleanup ownership, fail-closed teardown verification, and manual recovery procedures.  
**Operational Status**: **NO DIAGNOSTIC RUN, NO FIREWALL/NETWORK ALTERATION, NO MANUSCRIPT EDIT.** Live vector store, benchmarks, snapshot assets, and source code remain byte-preserved.

---

## 1. Consolidated Operational Runbook Delivery

Antigravity has implemented and delivered the complete, hardened execution runbook as a standalone executable PowerShell script:

- **Script Path**: `scripts/execute_offline_diagnostic_runbook.ps1`
- **Verified SHA-256**: `873fa314394c39b81f76e999be525f37240cba33e938bbba4f9ea9ff0113ee61`
- **Total Lines**: 356 lines (Syntax validated via PowerShell AST parser: `SYNTAX_OK`)

### Core Architecture and Safeguards Enforced

1. **Elevation Verification**:
   - Checks `([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)`.
   - Fails closed immediately if not elevated, informing the operator that Windows Defender Firewall configuration requires Administrator privileges.
2. **Session Transcript Recording**:
   - Initialized via `Start-Transcript -Path $transcriptPath -NoClobber` into a unique timestamped directory (`TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/runbook_records/runbook_<timestamp>/runbook_console_transcript.txt`).
   - Cleanly stopped via `Stop-Transcript` in the `finally` block.
3. **Complete 6-Item Boundary Hash Inventory (Pre-Execution & Post-Execution)**:
   Both Step 2 (pre-execution) and Step 7 (post-execution in `finally`, even on failure) explicitly calculate SHA-256 digests and compare against pinned values for all 6 critical assets:
   - Pinned Python executable (`pythoncore-3.14-64\python.exe`): `3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd`
   - Live execution harness (`scripts/run_diagnostic_harness.py`): `b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25`
   - Live diagnostic script (`scripts/audit_i1a_contemporary_gate_calibration.py`): `c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d`
   - Preserved Benchmark 350 (`terra_350_benchmark.json`): `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`
   - Preserved Benchmark 175 (`terra_175_benchmark.json`): `8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305`
   - Preserved Chroma SQLite (`dataset_20k_cap/vector_db_20k/chroma.sqlite3`): `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6`
4. **Environmental State & Other-Process Inspection**:
   - Queries `Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $pinnedPy }`. Logs any running PIDs and command lines, warning that their network access will be temporarily blocked.
   - Queries `Get-NetFirewallProfile` to verify that firewall service and profiles are active.
5. **Fail-Closed Collision Detection on Rule Name**:
   - Queries `Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction Stop`.
   - Distinguishes between expected absence (`No MSFT_NetFirewallRule objects found`) versus query errors or pre-existing rules. Fails closed on any unexpected error or collision.
6. **Scoped Outbound Firewall Rule Creation & Complete Property Audit**:
   - Creates rule with unique internal Name `-Name "TERRA_Offline_Diagnostic_20261008"`.
   - Tracks ownership flag `$ruleCreated = $true`.
   - Reads back rule and associated application filter (`Get-NetFirewallApplicationFilter`). Verifies `Direction=Outbound`, `Action=Block`, `Enabled=True`, `Profile=Any`, and `Program` matching the pinned interpreter binary path.
7. **Single Native Invocation & Immediate Native Exit Code Capture**:
   - Invokes live scripts via quoted absolute paths:
     `& 'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe' 'F:\TERRA -Copy\scripts\run_diagnostic_harness.py' --execute-diagnostic --enforced-offline-condition TERRA_Offline_Diagnostic`
   - Captures `$nativeExit = $LASTEXITCODE` immediately following process completion.
8. **Guaranteed Teardown & Fail-Closed Removal Verification**:
   - In `finally`, if `$ruleCreated -eq $true`, executes `Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction Stop`.
   - Re-queries the rule to verify confirmed absence. If the rule remains or query fails, marks `$teardown_verified = $false` and fails the operational outcome.
9. **No-Overwrite Evidence Package Emission**:
   - Emits structured `runbook_execution_evidence.json` inside the unique run directory, recording pre/post hashes, native exit code, rule verification facts, and final operational outcome (`SUCCESS` only if native exit is 0, teardown verified, and all post-hashes match).
   - Never masks child process failure with cleanup success, nor masks cleanup failure with child process success.

---

## 2. Defined Manual Recovery Instructions

If the runbook execution is ever interrupted abruptly by a system failure or power loss, the operator can verify and restore firewall state manually:

```powershell
# Step 1: Open PowerShell as Administrator
# Step 2: Check if the temporary rule still exists:
Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue

# Step 3: If present, remove it immediately:
Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008"

# Step 4: Verify confirmed removal (must return nothing):
Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue
```

---

## 3. Preservation & Measurement Addendum

In response to peer notes:
1. **Preserved Package Status**:
   All 6 files in `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/execution_package/` have `IsReadOnly = True`. They are hash-verified preserved copies serving as write-protected reference snapshots, not mutable work files. The builder script has been permanently deleted from disk.
2. **Python Version Clarification**:
   The static string `"3.14.3"` in the historical package manifest was descriptive prose. Direct measurement of the pinned binary reports **`Python 3.14.5`**. The binary SHA-256 (`3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd`) governs as authoritative.
3. **Enforcement Scope Precision**:
   The temporary firewall rule applies specifically to outbound sockets initiated by the pinned interpreter path. It does not affect other software (such as browsers, IDEs, or cloud agent sessions). The Stage 1 socket negative control is an internal programmatic check confirming outbound connection failure, not mathematical proof of external firewall state.

---

## 4. Current Operational Stance

- **Diagnostic Run Gate**: **STRICTLY CLOSED**. Zero diagnostic subprocesses launched.
- **Firewall Rules**: **ZERO INSTALLED**.
- **Manuscripts**: **FROZEN**.
- **Next Step**: Awaiting joint review by Claude and Codex of `scripts/execute_offline_diagnostic_runbook.ps1` and this evidence protocol, followed by the user's dated offline arrangement selection and separate single-run execution authorization.
