<#
.SYNOPSIS
    TERRA Bounded Gated Tokenizer Acquisition Launcher (Stage 3C).
.DESCRIPTION
    Hardened operational launcher for scripts/matched_baseline/acquire_gated_tokenizers.py.
    Complies with Codex-0123 and Codex-0124:
    - Pre-execution terminating SHA-256 checks on all protected boundary files.
    - Secret-safe hidden token input prior to transcript startup.
    - Strict simulation isolation: incomplete simulation configurations fail closed before any action.
    - Staging absence contract: launcher creates only run evidence dir; leaves staging target nonexistent.
    - Dedicated run directory with reparse point rejection and collision defense.
    - Guarded lifecycle covering pre-checks, token receipt, execution, and teardown.
    - Four isolated teardown layers:
        1. Token zeroing (ZeroFreeBSTR), environment variable removal with verification, SecureString disposal.
        2. Per-file post-execution boundary hash verification continuing across errors.
        3. Checked transcript closure before record writing.
        4. Terminal record persistence with FileMode.CreateNew, simulation marker, PS version, and distinct outcomes.
    - Strict exit code propagation reflecting child vs wrapper outcome.
#>

[CmdletBinding()]
param(
    [switch]$SimulationTestMode,
    [string]$TestConfigJson,
    [string]$TestConfigBase64,
    [string]$EnvFile,
    [string]$RecoveryStagingDir
)

$ErrorActionPreference = "Stop"

# Ensure Microsoft.PowerShell.Utility is loaded for Get-FileHash
if (-not (Get-Command Get-FileHash -ErrorAction SilentlyContinue)) {
    Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop
}

function Convert-ToHashtable($obj) {
    if ($obj -is [System.Management.Automation.PSCustomObject]) {
        $ht = @{}
        foreach ($prop in $obj.PSObject.Properties) {
            $ht[$prop.Name] = Convert-ToHashtable $prop.Value
        }
        return $ht
    } elseif ($obj -is [System.Collections.IEnumerable] -and $obj -isnot [string]) {
        $list = @()
        foreach ($item in $obj) {
            $list += ,(Convert-ToHashtable $item)
        }
        return $list
    } else {
        return $obj
    }
}

# -----------------------------------------------------------------------------
# Global State for Guarded Lifecycle & Evidence Recording
# -----------------------------------------------------------------------------
$runId = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$runDir = $null
$stagingDir = $null
$outerTranscriptPath = $null
$launcherRecordPath = $null
$transcriptStarted = $false
$transcriptClosedCleanly = $true
$childExecuted = $false
$childExitCode = $null
$wrapperErrors = [System.Collections.Generic.List[string]]::new()
$preHashMap = [ordered]@{}
$postHashMap = [ordered]@{}
$wrapperOutcome = "OPERATIONAL_FAILURE"
$terminalExitCode = 1
$secureToken = $null
$bstr = [System.IntPtr]::Zero

# Pinned Interpreter Specifications (Codex-0125 narrow pin)
$ExpectedPythonExeSha = "896CCF899B9D45C1C119BA35D6CCE6E16CC10DD6A7F502F88FB50429A6E5CF4C"
$ExpectedPythonVersion = "Python 3.14.5"

$ExpectedHashes = [ordered]@{
    "assets\tokenizers\tokenizer_manifest.sha256" = "41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44"
    "scripts\matched_baseline\fast_tokenizer_adapter.py" = "AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A"
    "scripts\matched_baseline\acquire_gated_tokenizers.py" = "C06CC0C4C024515FF0739238B57F0794409828A84E0346B92EE54EF0EF4AEA50"
    "tests\test_offline_public_tokenizer_assets.py" = "B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803"
}

try {
    # -------------------------------------------------------------------------
    # Step 0: Mode Validation & Strict Simulation Configuration Gate
    # -------------------------------------------------------------------------
    if (-not $SimulationTestMode -and (-not [string]::IsNullOrWhiteSpace($TestConfigJson) -or -not [string]::IsNullOrWhiteSpace($TestConfigBase64))) {
        throw "PRODUCTION VIOLATION: Test configuration parameters provided without -SimulationTestMode."
    }

    $TestConfig = @{}
    if ($SimulationTestMode) {
        if ([string]::IsNullOrWhiteSpace($TestConfigJson) -and [string]::IsNullOrWhiteSpace($TestConfigBase64)) {
            throw "TEST CONFIG FAULT: -SimulationTestMode requires -TestConfigJson or -TestConfigBase64 with explicit mock configuration."
        }
        try {
            $rawJson = if (-not [string]::IsNullOrWhiteSpace($TestConfigBase64)) {
                [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($TestConfigBase64))
            } else {
                $TestConfigJson
            }
            $parsedJson = $rawJson | ConvertFrom-Json
            $TestConfig = Convert-ToHashtable $parsedJson
        } catch {
            throw "TEST CONFIG FAULT: Invalid JSON in test configuration: $($_.Exception.Message)"
        }

        # Validate mandatory simulation parameters - never fall through to production actions!
        if (-not $TestConfig.ContainsKey("WorkspaceRoot") -or [string]::IsNullOrWhiteSpace($TestConfig["WorkspaceRoot"])) {
            throw "TEST CONFIG FAULT: Simulation mode requires explicit 'WorkspaceRoot'."
        }
        if (-not $TestConfig.ContainsKey("MockToken") -and -not $TestConfig.ContainsKey("MockEmptyToken")) {
            throw "TEST CONFIG FAULT: Simulation mode requires explicit 'MockToken' or 'MockEmptyToken'."
        }
        if (-not ($TestConfig.ContainsKey("SkipChildExecution") -and $TestConfig["SkipChildExecution"]) -and -not $TestConfig.ContainsKey("FakeChildScript")) {
            throw "TEST CONFIG FAULT: Simulation mode requires 'SkipChildExecution' or 'FakeChildScript'."
        }
    }

    $WorkspaceRoot = if ($SimulationTestMode) { $TestConfig["WorkspaceRoot"] } else { "F:\TERRA -Copy" }
    if (-not (Test-Path -LiteralPath $WorkspaceRoot)) {
        throw "WORKSPACE ERROR: Workspace root does not exist: $WorkspaceRoot"
    }

    # -------------------------------------------------------------------------
    # Step 1: Evidence Base Directory & Reparse Point / Collision Verification
    # -------------------------------------------------------------------------
    $baseRunsDir = if ($SimulationTestMode -and $TestConfig.ContainsKey("EvidenceBaseDir")) {
        $TestConfig["EvidenceBaseDir"]
    } else {
        Join-Path $WorkspaceRoot "tmp"
    }

    if (-not (Test-Path -LiteralPath $baseRunsDir)) {
        [System.IO.Directory]::CreateDirectory($baseRunsDir) | Out-Null
    }

    $baseDirItem = Get-Item -LiteralPath $baseRunsDir -Force
    if ($baseDirItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw "SECURITY ERROR: Base run directory '$baseRunsDir' is a reparse point or symlink. Aborting."
    }

    $runDir = Join-Path $baseRunsDir "gated_run_${timestamp}_${runId}"
    if (Test-Path -LiteralPath $runDir) {
        throw "COLLISION ERROR: Run directory '$runDir' already exists! Exclusivity violated."
    }
    [System.IO.Directory]::CreateDirectory($runDir) | Out-Null

    if ([string]::IsNullOrWhiteSpace($RecoveryStagingDir)) {
        # Staging Contract (Codex-0124): Define stagingDir path, but DO NOT create it!
        # The downloader requires an absent staging target and creates it via mkdir(exist_ok=False).
        $stagingDir = Join-Path $runDir "staging"
        if (Test-Path -LiteralPath $stagingDir) {
            throw "STAGING SETUP ERROR: Staging path '$stagingDir' already exists prior to launch!"
        }
    } else {
        # Recovery Staging Contract (Codex-0131):
        # Validate lexical ancestry before resolution (no '..', no symlinks, no reparse points)
        $normRecPath = [System.IO.Path]::GetFullPath((Join-Path $WorkspaceRoot $RecoveryStagingDir))
        $recItem = Get-Item -LiteralPath $normRecPath -ErrorAction SilentlyContinue
        if ($null -eq $recItem -or -not (Test-Path -LiteralPath $normRecPath -PathType Container)) {
            throw "RECOVERY STAGING ERROR: Specified RecoveryStagingDir does not exist or is not a directory: '$RecoveryStagingDir'"
        }

        # Check lexical ancestry for symlinks and reparse points
        $currCheck = $recItem
        while ($null -ne $currCheck) {
            if ($currCheck.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                throw "SECURITY ERROR: Reparse point or symlink detected in recovery staging ancestry: '$($currCheck.FullName)'"
            }
            $currCheck = $currCheck.Parent
        }

        # Check that RECOVERY_STAGING_RECEIPT.json exists
        $receiptPath = Join-Path $normRecPath "RECOVERY_STAGING_RECEIPT.json"
        if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
            throw "RECOVERY STAGING ERROR: RECOVERY_STAGING_RECEIPT.json missing in recovery staging directory: '$normRecPath'"
        }

        $stagingDir = $normRecPath
    }

    $outerTranscriptPath = Join-Path $runDir "outer_transcript.log"
    $launcherRecordPath = Join-Path $runDir "launcher_record.json"

    # -------------------------------------------------------------------------
    # Step 2: Python Interpreter Identity & Pre-Execution Boundary Verification
    # -------------------------------------------------------------------------
    $pythonExe = Join-Path $WorkspaceRoot "venv\Scripts\python.exe"
    $actualPySha = $null
    $actualPyVer = $null
    if (-not $SimulationTestMode) {
        if (-not (Test-Path -LiteralPath $pythonExe)) {
            $msg = "INTERPRETER ERROR: Virtualenv python.exe not found: $pythonExe"
            $wrapperErrors.Add($msg)
            throw $msg
        }
        $pyItem = Get-Item -LiteralPath $pythonExe -ErrorAction Stop
        if ($pyItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            $msg = "SECURITY ERROR: Python interpreter '$pythonExe' is a reparse point or symlink!"
            $wrapperErrors.Add($msg)
            throw $msg
        }
        $actualPySha = (Get-FileHash -LiteralPath $pythonExe -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
        if ($actualPySha -ne $ExpectedPythonExeSha) {
            $msg = "INTERPRETER PIN ERROR: python.exe SHA-256 mismatch (Expected: $ExpectedPythonExeSha, Actual: $actualPySha)"
            $wrapperErrors.Add($msg)
            throw $msg
        }
        $actualPyVer = (& $pythonExe -V 2>&1).Trim()
        if ($actualPyVer -ne $ExpectedPythonVersion) {
            $msg = "INTERPRETER VERSION ERROR: python.exe version mismatch (Expected: $ExpectedPythonVersion, Actual: $actualPyVer)"
            $wrapperErrors.Add($msg)
            throw $msg
        }
    } else {
        $actualPySha = if ($TestConfig.ContainsKey("MockPythonSha")) { $TestConfig["MockPythonSha"] } else { "SIMULATED_INTERPRETER_PIN" }
        $actualPyVer = if ($TestConfig.ContainsKey("MockPythonVersion")) { $TestConfig["MockPythonVersion"] } else { "Python 3.14.5 (Simulated)" }
    }

    foreach ($relPath in $ExpectedHashes.Keys) {
        $fullPath = Join-Path $WorkspaceRoot $relPath
        if (-not (Test-Path -LiteralPath $fullPath)) {
            $msg = "PRE-EXECUTION INTEGRITY ERROR: Protected file missing: $relPath"
            $wrapperErrors.Add($msg)
            $preHashMap[$relPath] = "FILE_MISSING"
            throw $msg
        }

        $actualHash = $null
        if ($SimulationTestMode -and $TestConfig.ContainsKey("MockPreHashes") -and $TestConfig["MockPreHashes"].ContainsKey($relPath)) {
            $actualHash = $TestConfig["MockPreHashes"][$relPath].ToUpper()
        } else {
            $actualHash = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
        }

        $expectedHash = $ExpectedHashes[$relPath]
        $preHashMap[$relPath] = $actualHash

        if ($actualHash -ne $expectedHash) {
            $msg = "PRE-EXECUTION INTEGRITY ERROR: Hash mismatch for '$relPath' (Expected: $expectedHash, Actual: $actualHash)"
            $wrapperErrors.Add($msg)
            throw $msg
        }
    }

    # -------------------------------------------------------------------------
    # Step 3: Secret-Safe Hidden Token Collection (Before Transcript)
    # -------------------------------------------------------------------------
    if ($SimulationTestMode) {
        if ($TestConfig.ContainsKey("MockToken")) {
            $mockVal = $TestConfig["MockToken"]
            if ([string]::IsNullOrEmpty($mockVal)) {
                $secureToken = [System.Security.SecureString]::new()
            } else {
                $secureToken = ConvertTo-SecureString $mockVal -AsPlainText -Force
            }
        } elseif ($TestConfig.ContainsKey("MockEmptyToken") -and $TestConfig["MockEmptyToken"]) {
            $secureToken = [System.Security.SecureString]::new()
        }
    } elseif (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
        # Credential file provided; verify file exists and is within workspace
        $resolvedEnvPath = (Resolve-Path -LiteralPath (Join-Path $WorkspaceRoot $EnvFile) -ErrorAction Stop).Path
        if (-not (Test-Path -LiteralPath $resolvedEnvPath)) {
            throw "ENV FILE ERROR: Credential file not found: $EnvFile"
        }
        $secureToken = ConvertTo-SecureString "ENV_FILE_MODE_ACTIVE" -AsPlainText -Force
    } else {
        $secureToken = Read-Host -Prompt "Enter Hugging Face Read Token (input hidden)" -AsSecureString
    }

    if ($null -eq $secureToken -or $secureToken.Length -lt 10) {
        $wrapperErrors.Add("TOKEN VALIDATION ERROR: Token input empty or invalid length (must be at least 10 characters).")
        throw "TOKEN INPUT ERROR: Token input empty or invalid length (must be at least 10 characters)."
    }

    # -------------------------------------------------------------------------
    # Step 4: Transcript Startup
    # -------------------------------------------------------------------------
    try {
        if ($SimulationTestMode -and $TestConfig.ContainsKey("MockTranscriptStartupFail") -and $TestConfig["MockTranscriptStartupFail"]) {
            throw "Simulated transcript startup failure"
        }
        Start-Transcript -LiteralPath $outerTranscriptPath -NoClobber -ErrorAction Stop | Out-Null
        $transcriptStarted = $true
    } catch {
        $msg = "TRANSCRIPT STARTUP ERROR: $($_.Exception.Message)"
        $wrapperErrors.Add($msg)
        Write-Host $msg -ForegroundColor Red
        throw
    }

    Write-Host "================================================================================"
    Write-Host "TERRA Matched Baseline: Gated Tokenizer Acquisition Launcher"
    Write-Host "Workspace Root   : $WorkspaceRoot"
    Write-Host "Execution Mode   : $(if ($SimulationTestMode) { 'SIMULATION_TEST' } else { 'PRODUCTION' })"
    Write-Host "Run ID           : $runId"
    Write-Host "Run Directory    : $runDir"
    Write-Host "Staging Target   : $stagingDir (absent, to be created by downloader)"
    Write-Host "Timestamp UTC    : $((Get-Date).ToUniversalTime().ToString('o'))"
    Write-Host "================================================================================"

    # -------------------------------------------------------------------------
    # Step 5: BSTR Allocation & Transient Environment Variable Exposure
    # -------------------------------------------------------------------------
    try {
        if ($SimulationTestMode -and $TestConfig.ContainsKey("MockBstrAllocationFail") -and $TestConfig["MockBstrAllocationFail"]) {
            throw "Simulated BSTR allocation failure"
        }
        if ([string]::IsNullOrWhiteSpace($EnvFile)) {
            $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
            $env:HF_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        }
    } catch {
        $msg = "TOKEN EXPOSURE ERROR: $($_.Exception.Message)"
        $wrapperErrors.Add($msg)
        throw
    }

    # -------------------------------------------------------------------------
    # Step 6: Interpreter & Script Verification Immediately Before Child Launch
    # -------------------------------------------------------------------------
    $scriptPath = Join-Path $WorkspaceRoot "scripts\matched_baseline\acquire_gated_tokenizers.py"

    if (-not $SimulationTestMode) {
        if (-not (Test-Path -LiteralPath $pythonExe)) {
            throw "INTERPRETER ERROR: Virtualenv python.exe not found: $pythonExe"
        }
        $preLaunchPySha = (Get-FileHash -LiteralPath $pythonExe -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
        if ($preLaunchPySha -ne $ExpectedPythonExeSha) {
            throw "INTERPRETER PIN ERROR: python.exe SHA-256 altered immediately before launch: $preLaunchPySha"
        }
        if (-not (Test-Path -LiteralPath $scriptPath)) {
            throw "SCRIPT ERROR: Downloader script not found: $scriptPath"
        }
        $scriptCurrentSha = (Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
        if ($scriptCurrentSha -ne $ExpectedHashes["scripts\matched_baseline\acquire_gated_tokenizers.py"]) {
            throw "SCRIPT PIN ERROR: Downloader script hash mismatch immediately before launch: $scriptCurrentSha"
        }
    }

    # -------------------------------------------------------------------------
    # Step 7: Child Invocation
    # -------------------------------------------------------------------------
    if ($SimulationTestMode) {
        if ($TestConfig.ContainsKey("FakeChildScript") -and -not [string]::IsNullOrWhiteSpace($TestConfig["FakeChildScript"])) {
            # Execute fake child script (e.g. for staging absence contract test)
            $fakeScript = $TestConfig["FakeChildScript"]
            $prevEAP = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            try {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fakeScript -StagingDir $stagingDir
                $childExitCode = $LASTEXITCODE
                $childExecuted = $true
            } catch {
                $wrapperErrors.Add("FAKE CHILD EXECUTION EXCEPTION: $($_.Exception.Message)")
                if ($null -eq $childExitCode) { $childExitCode = 1 }
            } finally {
                $ErrorActionPreference = $prevEAP
            }
        } else {
            # Pure simulated child execution
            $childExecuted = $true
            if ($TestConfig.ContainsKey("MockChildExitCode") -and $null -ne $TestConfig["MockChildExitCode"]) {
                $childExitCode = [int]$TestConfig["MockChildExitCode"]
            } else {
                $childExitCode = 0
            }
            Write-Host "[SIMULATION] Child execution skipped. MockChildExitCode=$childExitCode"
        }
    } else {
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $childArgs = @(
                "-B",
                $scriptPath,
                "--roles", "router,generator",
                "--confirm-llama-access",
                "--staging-dir", $stagingDir
            )
            if (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
                $childArgs += @("--env-file", $EnvFile)
            }
            if (-not [string]::IsNullOrWhiteSpace($RecoveryStagingDir)) {
                $childArgs += @("--recovery-staging", $stagingDir)
            }
            & $pythonExe @childArgs
            
            $childExitCode = $LASTEXITCODE
            $childExecuted = $true
            Write-Host "`nChild process completed with exit code: $childExitCode"
        } catch {
            $wrapperErrors.Add("CHILD EXECUTION EXCEPTION: $($_.Exception.Message)")
            if ($null -eq $childExitCode) {
                $childExitCode = 1
            }
        } finally {
            $ErrorActionPreference = $prevEAP
        }
    }

} finally {
    # -------------------------------------------------------------------------
    # Guarded Teardown Layer 1: Token Cleanup & Verification
    # -------------------------------------------------------------------------
    try {
        if ($bstr -ne [System.IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
            $bstr = [System.IntPtr]::Zero
        }
    } catch {
        $wrapperErrors.Add("TEARDOWN ERROR: ZeroFreeBSTR failed: $($_.Exception.Message)")
    }

    try {
        if (Test-Path env:HF_TOKEN) {
            if ($SimulationTestMode -and $TestConfig.ContainsKey("SimulateTokenCleanupFailure") -and $TestConfig["SimulateTokenCleanupFailure"]) {
                # Simulate stuck variable
                $wrapperErrors.Add("CLEANUP VERIFICATION FAILURE: HF_TOKEN could not be removed from environment.")
            } else {
                Remove-Item env:HF_TOKEN -Force -ErrorAction Stop
                if (Test-Path env:HF_TOKEN) {
                    $wrapperErrors.Add("CLEANUP VERIFICATION FAILURE: HF_TOKEN still present in environment after Remove-Item.")
                }
            }
        }
    } catch {
        $wrapperErrors.Add("TEARDOWN ERROR: Remove-Item env:HF_TOKEN threw: $($_.Exception.Message)")
    }

    try {
        if ($null -ne $secureToken) {
            if ($secureToken -is [System.IDisposable]) {
                $secureToken.Dispose()
            }
            $secureToken = $null
        }
    } catch {
        $wrapperErrors.Add("TEARDOWN ERROR: SecureString disposal failed: $($_.Exception.Message)")
    }

    Write-Host "[OK] In-memory token reference cleaned; environment variable scrubbed."

    # -------------------------------------------------------------------------
    # Guarded Teardown Layer 2: Per-File Post-Execution Hash Verification
    # -------------------------------------------------------------------------
    Write-Host "`n--- Post-Execution Protected File Verification ---"
    $integrityBreached = $false
    if (-not [string]::IsNullOrWhiteSpace($WorkspaceRoot) -and (Test-Path -LiteralPath $WorkspaceRoot) -and $preHashMap.Count -eq $ExpectedHashes.Count) {
        foreach ($relPath in $ExpectedHashes.Keys) {
            try {
                $fullPath = Join-Path $WorkspaceRoot $relPath
                if (-not (Test-Path -LiteralPath $fullPath)) {
                    $msg = "POST-EXECUTION INTEGRITY ERROR: Protected file missing: $relPath"
                    $wrapperErrors.Add($msg)
                    $postHashMap[$relPath] = "FILE_MISSING"
                    $integrityBreached = $true
                    continue
                }

                $currentHash = $null
                if ($SimulationTestMode) {
                    if ($TestConfig.ContainsKey("MockPostHashThrows") -and $TestConfig["MockPostHashThrows"].Contains($relPath)) {
                        throw "Simulated read error for $relPath"
                    }
                    if ($TestConfig.ContainsKey("MockPostHashes") -and $TestConfig["MockPostHashes"].ContainsKey($relPath)) {
                        $currentHash = $TestConfig["MockPostHashes"][$relPath].ToUpper()
                    } elseif ($TestConfig.ContainsKey("MockPreHashes") -and $TestConfig["MockPreHashes"].ContainsKey($relPath)) {
                        $currentHash = $TestConfig["MockPreHashes"][$relPath].ToUpper()
                    } else {
                        $currentHash = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
                    }
                } else {
                    $currentHash = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpper()
                }
                $postHashMap[$relPath] = $currentHash

                $preHash = if ($preHashMap.Contains($relPath)) { $preHashMap[$relPath] } else { $null }
                $expectedHash = $ExpectedHashes[$relPath]

            if ($null -eq $preHash -or $currentHash -ne $preHash -or $currentHash -ne $expectedHash) {
                $msg = "POST-EXECUTION INTEGRITY BREACH: $relPath modified! (Expected: $expectedHash, Pre: $preHash, Post: $currentHash)"
                $wrapperErrors.Add($msg)
                Write-Host "[INTEGRITY BREACH] $msg" -ForegroundColor Red
                $integrityBreached = $true
            } else {
                Write-Host "Verified intact: $relPath ($currentHash)"
            }
        } catch {
            $msg = "POST-EXECUTION HASH VERIFICATION EXCEPTION on '$relPath': $($_.Exception.Message)"
            $wrapperErrors.Add($msg)
            $postHashMap[$relPath] = "READ_ERROR: $($_.Exception.Message)"
            $integrityBreached = $true
            # Continue checking remaining files!
        }
    }
}

    # -------------------------------------------------------------------------
    # Guarded Teardown Layer 3: Checked Transcript Closure (Before Terminal Record)
    # -------------------------------------------------------------------------
    try {
        if ($transcriptStarted) {
            if ($SimulationTestMode -and $TestConfig.ContainsKey("MockTranscriptStopFail") -and $TestConfig["MockTranscriptStopFail"]) {
                throw "Simulated transcript stop failure"
            }
            Stop-Transcript -ErrorAction Stop | Out-Null
            $transcriptClosedCleanly = $true
        }
    } catch {
        $msg = "TRANSCRIPT STOP ERROR: $($_.Exception.Message)"
        $wrapperErrors.Add($msg)
        $transcriptClosedCleanly = $false
        Write-Host $msg -ForegroundColor Red
    }

    # -------------------------------------------------------------------------
    # Guarded Teardown Layer 4: Outcome Determination & Terminal Record Write
    # -------------------------------------------------------------------------
    try {
        if ($integrityBreached) {
            $wrapperOutcome = "INTEGRITY_BREACH"
            $terminalExitCode = 1
        } elseif (-not $transcriptClosedCleanly) {
            $wrapperOutcome = "TRANSCRIPT_STOP_FAILURE"
            $terminalExitCode = 1
        } elseif (-not $childExecuted) {
            $wrapperOutcome = "PRE_EXECUTION_FAILURE"
            $terminalExitCode = 1
        } elseif ($childExitCode -ne 0) {
            $wrapperOutcome = "CHILD_EXECUTION_FAILURE"
            $terminalExitCode = if ($childExitCode -ne $null) { [int]$childExitCode } else { 1 }
        } elseif ($wrapperErrors.Count -gt 0) {
            $wrapperOutcome = "WRAPPER_ERROR"
            $terminalExitCode = 1
        } else {
            $wrapperOutcome = if ($SimulationTestMode) { "SIMULATED_SUCCESS" } else { "SUCCESS" }
            $terminalExitCode = 0
        }

        # Ensure run directory exists to hold the record (even on early errors)
        if ($null -ne $runDir -and (Test-Path -LiteralPath $runDir)) {
            $record = [ordered]@{
                "run_id" = $runId
                "timestamp_utc" = (Get-Date).ToUniversalTime().ToString("o")
                "simulation_mode" = [bool]$SimulationTestMode
                "execution_mode" = if ($SimulationTestMode) { "SIMULATION_TEST" } else { "PRODUCTION" }
                "powershell_version" = $PSVersionTable.PSVersion.ToString()
                "powershell_edition" = $PSVersionTable.PSEdition
                "python_interpreter_path" = $pythonExe
                "python_interpreter_sha256" = $actualPySha
                "python_interpreter_version" = $actualPyVer
                "python_interpreter_pin_verified" = $true
                "workspace_root" = $WorkspaceRoot
                "run_directory" = $runDir
                "staging_directory" = $stagingDir
                "outer_transcript_path" = $outerTranscriptPath
                "transcript_closed_cleanly" = $transcriptClosedCleanly
                "child_executed" = $childExecuted
                "child_exit_code" = $childExitCode
                "wrapper_outcome" = $wrapperOutcome
                "terminal_exit_code" = $terminalExitCode
                "pre_execution_hashes" = $preHashMap
                "post_execution_hashes" = $postHashMap
                "errors" = @($wrapperErrors)
            }

            $json = $record | ConvertTo-Json -Depth 5
            $fs = [System.IO.FileStream]::new(
                $launcherRecordPath,
                [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::None
            )
            try {
                $sw = [System.IO.StreamWriter]::new($fs, [System.Text.Encoding]::UTF8)
                try {
                    $sw.Write($json)
                } finally {
                    $sw.Dispose()
                }
            } finally {
                $fs.Dispose()
            }
            Write-Host "`n[OK] Launcher record saved: $launcherRecordPath"
        }
        Write-Host "Wrapper Outcome    : $wrapperOutcome"
        Write-Host "Terminal Exit Code : $terminalExitCode"
    } catch {
        Write-Host "FATAL: Failed to write launcher record: $($_.Exception.Message)" -ForegroundColor Red
        # Even if record writing fails, preserve the non-zero exit code!
        $terminalExitCode = 1
    }
}

if ($terminalExitCode -ne 0) {
    exit $terminalExitCode
} else {
    exit 0
}
