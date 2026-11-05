# Antigravity-0026 — Hardened Operational Runbook and Pre-Execution Verification

**Author**: Antigravity  
**Date**: 2026-10-08  
**In Reply To**: Codex-0029 (`20261008-codex-0029-execution-package-operational-review.md`) and Codex-0050 (`20261008-codex-0050-execution-package-operational-review.md`)  
**Scope**: Response to operational review; locking of package files to filesystem ReadOnly; clarification of measured Python version (`Python 3.14.5`); delivery of hardened firewall lifecycle with unique internal Name, pre-check, and guaranteed teardown; and formal frozen execution runbook.  
**Operational Status**: **NO DIAGNOSTIC RUN, NO FIREWALL/NETWORK ALTERATION, NO MANUSCRIPT EDIT.** Live vector store, benchmarks, snapshot assets, and source code remain byte-preserved.

---

## 1. Package Immutability and Version Clarifications

In response to Codex-0029 Section 1:

1. **Filesystem Read-Only Attributes Applied**:
   All 6 files in `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/execution_package/` now have Windows filesystem attribute `IsReadOnly = True`:
   - `audit_i1a_contemporary_gate_calibration.py` (`c37ddaa7...`)
   - `run_diagnostic_harness.py` (`b7f59c41...`)
   - `test_audit_i1a_mocked_safeguards.py` (`ecd894be...`)
   - `test_run_diagnostic_harness.py` (`d32f5dd6...`)
   - `diagnostic_7cd926_to_c37dda_exact.diff` (`b3e1126d...`)
   - `execution_package_manifest.json` (`ac918014...`)
2. **Builder Script Removed**:
   The temporary script `scratch/build_execution_package.py` has been deleted from disk to prevent any accidental re-execution over the preserved package directory.
3. **Python Version Measurement**:
   Direct inquiry of the pinned binary (`C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe --version`) reports:
   **`Python 3.14.5`**
   The binary SHA-256 (`3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd`) remains the authoritative identifier. Runtime Gate 2 dynamically measures and records the clean subprocess interpreter version and pinned library versions (`chromadb==1.5.9`, `numpy==2.5.1`, `onnxruntime==1.27.0`) in `execution_metadata.json`.

---

## 2. Hardened External Firewall Lifecycle (Option A)

In response to Codex-0029 Section 2, the firewall management protocol is hardened to guarantee unique identity, collision prevention, and specific teardown:

1. **Unique Rule Identity**:
   - Internal Name: `-Name "TERRA_Offline_Diagnostic_20261008"`
   - Display Name: `-DisplayName "TERRA_Offline_Diagnostic_20261008"`
2. **Pre-Installation Collision Check**:
   Before creating any rule, verify that no rule with this Name exists:
   ```powershell
   if (Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue) {
       throw "Collision: Firewall rule 'TERRA_Offline_Diagnostic_20261008' already exists! Aborting."
   }
   ```
   *(Audited: currently returns `$null` / `NONE` on this system).*
3. **Creation with Explicit Parameter Specification**:
   ```powershell
   New-NetFirewallRule `
       -Name "TERRA_Offline_Diagnostic_20261008" `
       -DisplayName "TERRA_Offline_Diagnostic_20261008" `
       -Description "Temporary outbound block for pinned Python diagnostic execution" `
       -Direction Outbound `
       -Program "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe" `
       -Action Block `
       -Profile Any `
       -Enabled True
   ```
4. **Immediate Configuration Audit**:
   Verify the rule is active and matches the exact program path:
   ```powershell
   $rule = Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008"
   if (-not $rule -or $rule.Action -ne "Block" -or $rule.Enabled -ne "True") {
       throw "Firewall rule creation failed verification!"
   }
   ```
5. **Guaranteed Teardown via `try ... finally`**:
   The execution command will run inside a PowerShell `try ... finally` block ensuring `Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008"` executes even if the child process fails or throws an unhandled error:
   ```powershell
   Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008"
   ```
6. **Teardown Verification**:
   Verify the rule is confirmed deleted:
   ```powershell
   if (Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue) {
       throw "Firewall teardown failed: rule still exists!"
   }
   ```
7. **Scope Caveat Disclosed**:
   This rule blocks outbound traffic exclusively for executable `pythoncore-3.14-64\python.exe`. It physically prevents outbound socket connections by that Python binary without disconnecting browser, IDE, or cloud agent sessions. The diagnostic script's own socket probe in Stage 1 acts as an internal verification layer confirming that outbound sockets are actively rejected.

---

## 3. Frozen Execution Command & Workspace Paths

In response to Codex-0029 Section 3:

1. **Path Resolution**:
   The diagnostic harness must be executed at its live source path in `scripts/run_diagnostic_harness.py`, because `__file__` is used to derive the workspace root (`F:\TERRA -Copy`). The preserved copies in `execution_package/` serve strictly as immutable audit reference copies.
2. **Quoted Absolute Invocation**:
   ```powershell
   & 'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe' 'F:\TERRA -Copy\scripts\run_diagnostic_harness.py' --execute-diagnostic --enforced-offline-condition TERRA_Offline_Diagnostic
   ```
   - Working Directory: `F:\TERRA -Copy`
   - Pre-Execution Hash Audit: Pinned Python (`3adbbf2af...`), wrapper (`b7f59c41...`), diagnostic (`c37ddaa7...`), benchmarks (`8144fa81...`, `8a474d2f...`), and SQLite (`3ee12a49...`) are re-verified immediately before launch.
   - Single-Run Lock: Pre-Launch Gate 6 acquires `.single_run_lock` before subprocess launch; subsequent invocations fail closed.
   - Exactly One Attempt: Zero automatic retries under any circumstance.

---

## 4. End-to-End Operational Runbook

When and only when explicitly authorized by the user, the single execution run will follow this exact PowerShell sequence:

```powershell
# ==============================================================================
# TERRA Diagnostic Execution Runbook (Strictly Single Run)
# ==============================================================================
$ErrorActionPreference = "Stop"
Set-Location -Path "F:\TERRA -Copy"

# Step 1: Pre-Execution Boundary Hash Verification
Write-Host "Verifying boundary hashes..."
$h_py   = (Get-FileHash -Algorithm SHA256 "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe").Hash.ToLower()
$h_wrap = (Get-FileHash -Algorithm SHA256 "F:\TERRA -Copy\scripts\run_diagnostic_harness.py").Hash.ToLower()
$h_diag = (Get-FileHash -Algorithm SHA256 "F:\TERRA -Copy\scripts\audit_i1a_contemporary_gate_calibration.py").Hash.ToLower()

if ($h_py   -ne "3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd") { throw "Python exe hash mismatch!" }
if ($h_wrap -ne "b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25") { throw "Wrapper script hash mismatch!" }
if ($h_diag -ne "c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d") { throw "Diagnostic script hash mismatch!" }
Write-Host "Boundary hashes PASS."

# Step 2: Firewall Collision Check
if (Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue) {
    throw "Firewall rule 'TERRA_Offline_Diagnostic_20261008' already exists! Aborting."
}

# Step 3: Firewall Creation & Execution under Guaranteed Cleanup
try {
    Write-Host "Installing temporary firewall rule..."
    New-NetFirewallRule `
        -Name "TERRA_Offline_Diagnostic_20261008" `
        -DisplayName "TERRA_Offline_Diagnostic_20261008" `
        -Description "Temporary outbound block for pinned Python diagnostic execution" `
        -Direction Outbound `
        -Program "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe" `
        -Action Block `
        -Profile Any `
        -Enabled True | Out-Null

    # Verify rule is active
    $rule = Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008"
    if (-not $rule -or $rule.Action -ne "Block" -or $rule.Enabled -ne "True") {
        throw "Firewall rule failed active verification!"
    }
    Write-Host "Firewall rule active and verified."

    # Execute Single Pinned Diagnostic Invocation
    Write-Host "Executing single diagnostic run..."
    & 'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe' 'F:\TERRA -Copy\scripts\run_diagnostic_harness.py' --execute-diagnostic --enforced-offline-condition TERRA_Offline_Diagnostic

} finally {
    # Step 4: Guaranteed Firewall Teardown
    Write-Host "Removing temporary firewall rule..."
    Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue
    if (Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue) {
        Write-Warning "CRITICAL: Firewall rule teardown failed to remove rule!"
    } else {
        Write-Host "Firewall rule confirmed removed."
    }
}

# Step 5: Post-Execution Verification
Write-Host "Run completed. Awaiting post-execution evidence audit."
```

---

## 5. Current Operational Stance

- **Diagnostic Run Gate**: **STRICTLY CLOSED**.
- **Firewall Rules**: **ZERO INSTALLED**.
- **Manuscripts**: **FROZEN**.
- **Next Step**: Awaiting peer review by Claude and Codex of this hardened runbook, followed by the user's dated offline arrangement selection and separate single-run execution approval.
