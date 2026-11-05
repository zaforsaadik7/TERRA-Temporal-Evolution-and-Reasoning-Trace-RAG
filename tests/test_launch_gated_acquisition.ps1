<#
.SYNOPSIS
    Comprehensive Synthetic Unit Test Suite for Hardened Gated Acquisition Launcher.
.DESCRIPTION
    Validates fail-closed behavior, strict simulation isolation, staging contract,
    and teardown lifecycle guarantees responding to Codex-0123 and Codex-0124:
    - Test 1: Production rejection of non-empty test config without -SimulationTestMode
    - Test 2: Incomplete simulation (missing WorkspaceRoot) fails closed
    - Test 3: Incomplete simulation (missing MockToken) fails closed
    - Test 4: Incomplete simulation (missing SkipChild/FakeChild) fails closed
    - Test 5: Staging absence contract: launcher leaves staging target absent; fake child asserts absence
    - Test 6: Pre-execution boundary hash mismatch fails closed with evidence record
    - Test 7: Pre-execution missing protected file fails closed with evidence record
    - Test 8: Early token validation abort (empty/short token) disposes token and fails closed
    - Test 9: Transcript startup failure fails closed without leaking token or executing child
    - Test 10: Clean simulation mode produces SIMULATED_SUCCESS, exit 0, and complete record
    - Test 11: Nonzero child exit code (42) preserved distinctly in record and propagated
    - Test 12: Post-execution boundary hash mismatch sets INTEGRITY_BREACH and forces exit 1
    - Test 13: Per-file post hash error continues checking remaining files
    - Test 14: Token cleanup verification failure (stuck env variable) records failure and exits 1
    - Test 15: Transcript stop failure records failure and sets TRANSCRIPT_STOP_FAILURE
    - Test 16: Reparse point base directory rejected before run directory creation
    - Test 17: Exclusive record creation: launcher_record.json collision refuses overwrite

    Zero live network activity; zero credentials accessed or stored; zero real downloads.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Ensure Microsoft.PowerShell.Utility is loaded for Get-FileHash
if (-not (Get-Command Get-FileHash -ErrorAction SilentlyContinue)) {
    Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop
}

$launcherScript = "F:\TERRA -Copy\scripts\matched_baseline\launch_gated_acquisition.ps1"
$testScriptPath = "F:\TERRA -Copy\tests\test_launch_gated_acquisition.ps1"

$tempBase = Join-Path $env:TEMP ("terra_launcher_synth_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempBase -Force | Out-Null

$standardMockHashes = @{
    "assets\tokenizers\tokenizer_manifest.sha256" = "41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44"
    "scripts\matched_baseline\fast_tokenizer_adapter.py" = "AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A"
    "scripts\matched_baseline\acquire_gated_tokenizers.py" = "C06CC0C4C024515FF0739238B57F0794409828A84E0346B92EE54EF0EF4AEA50"
    "tests\test_offline_public_tokenizer_assets.py" = "B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803"
}

function New-MockWorkspace($wsDir) {
    New-Item -ItemType Directory -Path (Join-Path $wsDir "assets\tokenizers") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $wsDir "scripts\matched_baseline") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $wsDir "tests") -Force | Out-Null
    
    [System.IO.File]::WriteAllText((Join-Path $wsDir "assets\tokenizers\tokenizer_manifest.sha256"), "MOCK_MANIFEST", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText((Join-Path $wsDir "scripts\matched_baseline\fast_tokenizer_adapter.py"), "MOCK_ADAPTER", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText((Join-Path $wsDir "scripts\matched_baseline\acquire_gated_tokenizers.py"), "MOCK_DOWNLOADER", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText((Join-Path $wsDir "tests\test_offline_public_tokenizer_assets.py"), "MOCK_TEST_SUITE", [System.Text.Encoding]::UTF8)
}

function Get-BaseTestConfig($evidenceDir, $wsDir) {
    return @{
        "WorkspaceRoot" = $wsDir
        "EvidenceBaseDir" = $evidenceDir
        "MockToken" = "hf_synthetic_test_token_1234567890"
        "MockPreHashes" = $standardMockHashes
        "MockPostHashes" = $standardMockHashes
        "SkipChildExecution" = $true
        "MockChildExitCode" = 0
    }
}

function Invoke-LauncherTest($cfg, [bool]$passSimulationTestMode = $true) {
    $flag = if ($passSimulationTestMode) { "-SimulationTestMode" } else { "" }
    $cfgArg = ""
    if ($null -ne $cfg) {
        $jsonStr = $cfg | ConvertTo-Json -Compress -Depth 6
        $b64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($jsonStr))
        $cfgArg = "-TestConfigBase64 '$b64'"
    }
    $cmd = "& '$launcherScript' $flag $cfgArg; exit `$LASTEXITCODE"
    
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "powershell.exe"
    $pinfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true

    $p = [System.Diagnostics.Process]::Start($pinfo)
    $stdOut = $p.StandardOutput.ReadToEnd()
    $stdErr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()

    $combined = "$stdOut`n$stdErr"
    return [PSCustomObject]@{
        ExitCode = $p.ExitCode
        Output = $combined
        StdOut = $stdOut
        StdErr = $stdErr
    }
}

$testCount = 0
$passCount = 0
$failCount = 0
$skipCount = 0

function Assert-Test($name, [bool]$condition, [string]$msg, [string]$actualOutput = "") {
    $script:testCount++
    if ($condition) {
        $script:passCount++
        Write-Output "  [PASS] Test $script:testCount : $name"
    } else {
        $script:failCount++
        Write-Output "  [FAIL] Test $script:testCount : $name - $msg"
        if (-not [string]::IsNullOrWhiteSpace($actualOutput)) {
            Write-Output "    --- Output Begin ---"
            Write-Output "    $($actualOutput.Trim())"
            Write-Output "    --- Output End ---"
        }
    }
}

$lbHash = (Get-FileHash -Algorithm SHA256 $launcherScript).Hash.ToUpper()
$tsHash = (Get-FileHash -Algorithm SHA256 $testScriptPath).Hash.ToUpper()
$nowUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

Write-Output "=============================================================================="
Write-Output "SYNTHETIC TEST SUITE EXECUTION LOG: GATED ACQUISITION LAUNCHER (REVISED)"
Write-Output "Timestamp UTC      : $nowUtc"
Write-Output "PowerShell Version : $($PSVersionTable.PSVersion)"
Write-Output "OS Version         : $([System.Environment]::OSVersion.VersionString)"
Write-Output "Launcher Script    : $launcherScript"
Write-Output "Launcher SHA-256   : $lbHash"
Write-Output "Test Suite Script  : $testScriptPath"
Write-Output "Test Suite SHA-256 : $tsHash"
Write-Output "Invocation Command : powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1"
Write-Output "=============================================================================="

try {
    # --------------------------------------------------------------------------
    # Test 1: Production Mode Rejects Test Configuration Without -SimulationTestMode
    # --------------------------------------------------------------------------
    $t1Dir = Join-Path $tempBase "t1"
    $t1Ws = Join-Path $tempBase "t1_ws"
    New-MockWorkspace $t1Ws
    $t1Cfg = Get-BaseTestConfig $t1Dir $t1Ws
    $t1Res = Invoke-LauncherTest $t1Cfg -passSimulationTestMode $false
    $t1Passed = ($t1Res.ExitCode -ne 0) -and ($t1Res.Output -match "PRODUCTION VIOLATION: Test configuration parameters provided without -SimulationTestMode")
    Assert-Test "Production Mode Rejects Test Configuration Without -SimulationTestMode" $t1Passed "Expected exit non-zero and PRODUCTION VIOLATION, got exit $($t1Res.ExitCode)" $t1Res.Output

    # --------------------------------------------------------------------------
    # Test 2: Incomplete Simulation (Missing WorkspaceRoot) Fails Closed
    # --------------------------------------------------------------------------
    $t2Dir = Join-Path $tempBase "t2"
    $t2Cfg = @{
        "EvidenceBaseDir" = $t2Dir
        "MockToken" = "hf_synthetic_test_token_1234567890"
        "SkipChildExecution" = $true
    }
    $t2Res = Invoke-LauncherTest $t2Cfg
    $t2Passed = ($t2Res.ExitCode -ne 0) -and ($t2Res.Output -match "TEST CONFIG FAULT: Simulation mode requires explicit 'WorkspaceRoot'")
    Assert-Test "Incomplete Simulation (Missing WorkspaceRoot) Fails Closed" $t2Passed "Expected exit non-zero and TEST CONFIG FAULT for WorkspaceRoot" $t2Res.Output

    # --------------------------------------------------------------------------
    # Test 3: Incomplete Simulation (Missing MockToken) Fails Closed
    # --------------------------------------------------------------------------
    $t3Dir = Join-Path $tempBase "t3"
    $t3Ws = Join-Path $tempBase "t3_ws"
    New-MockWorkspace $t3Ws
    $t3Cfg = @{
        "WorkspaceRoot" = $t3Ws
        "EvidenceBaseDir" = $t3Dir
        "SkipChildExecution" = $true
    }
    $t3Res = Invoke-LauncherTest $t3Cfg
    $t3Passed = ($t3Res.ExitCode -ne 0) -and ($t3Res.Output -match "TEST CONFIG FAULT: Simulation mode requires explicit 'MockToken' or 'MockEmptyToken'")
    Assert-Test "Incomplete Simulation (Missing MockToken) Fails Closed" $t3Passed "Expected exit non-zero and TEST CONFIG FAULT for MockToken" $t3Res.Output

    # --------------------------------------------------------------------------
    # Test 4: Incomplete Simulation (Missing SkipChild/FakeChild) Fails Closed
    # --------------------------------------------------------------------------
    $t4Dir = Join-Path $tempBase "t4"
    $t4Ws = Join-Path $tempBase "t4_ws"
    New-MockWorkspace $t4Ws
    $t4Cfg = @{
        "WorkspaceRoot" = $t4Ws
        "EvidenceBaseDir" = $t4Dir
        "MockToken" = "hf_synthetic_test_token_1234567890"
    }
    $t4Res = Invoke-LauncherTest $t4Cfg
    $t4Passed = ($t4Res.ExitCode -ne 0) -and ($t4Res.Output -match "TEST CONFIG FAULT: Simulation mode requires 'SkipChildExecution' or 'FakeChildScript'")
    Assert-Test "Incomplete Simulation (Missing SkipChild/FakeChild) Fails Closed" $t4Passed "Expected exit non-zero and TEST CONFIG FAULT for child execution" $t4Res.Output

    # --------------------------------------------------------------------------
    # Test 5: Staging Absence Contract (Fake Child Verifies Staging Path Does Not Exist)
    # --------------------------------------------------------------------------
    $t5Dir = Join-Path $tempBase "t5"
    $t5Ws = Join-Path $tempBase "t5_ws"
    New-MockWorkspace $t5Ws
    $fakeChildScript = Join-Path $t5Dir "fake_child_downloader.ps1"
    New-Item -ItemType Directory -Path $t5Dir -Force | Out-Null
    $fakeChildContent = @"
param([string]`$StagingDir)
if (Test-Path -LiteralPath `$StagingDir) {
    Write-Error "CONTRACT VIOLATION: Staging directory already exists at child launch! Path: `$StagingDir"
    exit 2
}
# Child creates staging dir exclusively as Python mkdir(exist_ok=False) would
New-Item -ItemType Directory -Path `$StagingDir -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path `$StagingDir "child_proof.txt"), "STAGING_WAS_ABSENT_AT_LAUNCH")
exit 0
"@
    [System.IO.File]::WriteAllText($fakeChildScript, $fakeChildContent, [System.Text.Encoding]::UTF8)

    $t5Cfg = Get-BaseTestConfig $t5Dir $t5Ws
    $t5Cfg.Remove("SkipChildExecution")
    $t5Cfg["FakeChildScript"] = $fakeChildScript
    $t5Res = Invoke-LauncherTest $t5Cfg
    $t5RunDirs = if (Test-Path $t5Dir) { Get-ChildItem -Path $t5Dir -Directory | Where-Object { $_.Name -like "gated_run_*" } } else { @() }
    $t5ProofFile = if ($t5RunDirs.Count -gt 0) { Join-Path $t5RunDirs[0].FullName "staging\child_proof.txt" } else { "" }
    $t5ContractOk = ($t5Res.ExitCode -eq 0) -and (Test-Path $t5ProofFile) -and ((Get-Content $t5ProofFile -Raw) -match "STAGING_WAS_ABSENT_AT_LAUNCH")
    Assert-Test "Staging Absence Contract: Target absent at launch; fake child verifies absence" $t5ContractOk "Expected fake child to confirm staging was absent at launch" $t5Res.Output

    # --------------------------------------------------------------------------
    # Test 6: Pre-Execution Boundary Hash Mismatch Fails Closed with Evidence Record
    # --------------------------------------------------------------------------
    $t6Dir = Join-Path $tempBase "t6"
    $t6Ws = Join-Path $tempBase "t6_ws"
    New-MockWorkspace $t6Ws
    $t6Cfg = Get-BaseTestConfig $t6Dir $t6Ws
    $t6Cfg["MockPreHashes"] = @{
        "scripts\matched_baseline\acquire_gated_tokenizers.py" = "0000000000000000000000000000000000000000000000000000000000000000"
    }
    $t6Res = Invoke-LauncherTest $t6Cfg
    $t6RunDirs = if (Test-Path $t6Dir) { Get-ChildItem -Path $t6Dir -Directory } else { @() }
    $t6RecordFile = if ($t6RunDirs.Count -gt 0) { Join-Path $t6RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t6RecordOk = $false
    if (-not [string]::IsNullOrWhiteSpace($t6RecordFile) -and (Test-Path $t6RecordFile)) {
        $t6Json = Get-Content $t6RecordFile -Raw | ConvertFrom-Json
        $t6RecordOk = ($t6Json.wrapper_outcome -eq "PRE_EXECUTION_FAILURE") -and `
                      ($t6Json.child_executed -eq $false) -and `
                      (($t6Json.errors -join " ") -match "PRE-EXECUTION INTEGRITY ERROR")
    }
    $t6Passed = ($t6Res.ExitCode -ne 0) -and $t6RecordOk
    Assert-Test "Pre-Execution Hash Mismatch Fails Closed with Evidence Record" $t6Passed "Expected exit non-zero and PRE_EXECUTION_FAILURE in record" $t6Res.Output

    # --------------------------------------------------------------------------
    # Test 7: Pre-Execution Missing Protected File Fails Closed with Evidence Record
    # --------------------------------------------------------------------------
    $t7Dir = Join-Path $tempBase "t7"
    $t7Ws = Join-Path $tempBase "t7_ws"
    New-MockWorkspace $t7Ws
    Remove-Item (Join-Path $t7Ws "assets\tokenizers\tokenizer_manifest.sha256") -Force
    $t7Cfg = Get-BaseTestConfig $t7Dir $t7Ws
    $t7Res = Invoke-LauncherTest $t7Cfg
    $t7RunDirs = if (Test-Path $t7Dir) { Get-ChildItem -Path $t7Dir -Directory } else { @() }
    $t7RecordFile = if ($t7RunDirs.Count -gt 0) { Join-Path $t7RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t7RecordOk = $false
    if (-not [string]::IsNullOrWhiteSpace($t7RecordFile) -and (Test-Path $t7RecordFile)) {
        $t7Json = Get-Content $t7RecordFile -Raw | ConvertFrom-Json
        $t7RecordOk = ($t7Json.wrapper_outcome -eq "PRE_EXECUTION_FAILURE") -and `
                      ($t7Json.child_executed -eq $false) -and `
                      ($t7Json.pre_execution_hashes."assets\tokenizers\tokenizer_manifest.sha256" -eq "FILE_MISSING")
    }
    $t7Passed = ($t7Res.ExitCode -ne 0) -and $t7RecordOk
    Assert-Test "Pre-Execution Missing Protected File Fails Closed with Evidence Record" $t7Passed "Expected exit non-zero and FILE_MISSING recorded" $t7Res.Output

    # --------------------------------------------------------------------------
    # Test 8: Early Token Validation Abort (Empty/Short Token) Disposes Token & Fails Closed
    # --------------------------------------------------------------------------
    $t8Dir = Join-Path $tempBase "t8"
    $t8Ws = Join-Path $tempBase "t8_ws"
    New-MockWorkspace $t8Ws
    $t8Cfg = Get-BaseTestConfig $t8Dir $t8Ws
    $t8Cfg["MockToken"] = "short"
    $t8Res = Invoke-LauncherTest $t8Cfg
    $t8RunDirs = if (Test-Path $t8Dir) { Get-ChildItem -Path $t8Dir -Directory } else { @() }
    $t8RecordFile = if ($t8RunDirs.Count -gt 0) { Join-Path $t8RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t8RecordOk = $false
    if (-not [string]::IsNullOrWhiteSpace($t8RecordFile) -and (Test-Path $t8RecordFile)) {
        $t8Json = Get-Content $t8RecordFile -Raw | ConvertFrom-Json
        $t8RecordOk = ($t8Json.wrapper_outcome -eq "PRE_EXECUTION_FAILURE") -and `
                      ($t8Json.child_executed -eq $false) -and `
                      (($t8Json.errors -join " ") -match "TOKEN VALIDATION ERROR")
    }
    $t8Passed = ($t8Res.ExitCode -ne 0) -and $t8RecordOk
    Assert-Test "Early Token Validation Abort Disposes Token and Preserves Record" $t8Passed "Expected exit non-zero and TOKEN VALIDATION ERROR in record" $t8Res.Output

    # --------------------------------------------------------------------------
    # Test 9: Transcript Startup Failure Fails Closed Without Token Leak
    # --------------------------------------------------------------------------
    $t9Dir = Join-Path $tempBase "t9"
    $t9Ws = Join-Path $tempBase "t9_ws"
    New-MockWorkspace $t9Ws
    $t9Cfg = Get-BaseTestConfig $t9Dir $t9Ws
    $t9Cfg["MockTranscriptStartupFail"] = $true
    $t9Res = Invoke-LauncherTest $t9Cfg
    $t9Passed = ($t9Res.ExitCode -ne 0) -and ($t9Res.Output -match "TRANSCRIPT STARTUP ERROR")
    Assert-Test "Transcript Startup Failure Fails Closed" $t9Passed "Expected exit non-zero and TRANSCRIPT STARTUP ERROR" $t9Res.Output

    # --------------------------------------------------------------------------
    # Test 10: Clean Simulation Mode Produces SIMULATED_SUCCESS, Exit 0, & Complete Record
    # --------------------------------------------------------------------------
    $t10Dir = Join-Path $tempBase "t10"
    $t10Ws = Join-Path $tempBase "t10_ws"
    New-MockWorkspace $t10Ws
    $t10Cfg = Get-BaseTestConfig $t10Dir $t10Ws
    $t10Res = Invoke-LauncherTest $t10Cfg
    $t10RunDirs = if (Test-Path $t10Dir) { Get-ChildItem -Path $t10Dir -Directory } else { @() }
    $t10RecordFile = if ($t10RunDirs.Count -gt 0) { Join-Path $t10RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t10TranscriptFile = if ($t10RunDirs.Count -gt 0) { Join-Path $t10RunDirs[0].FullName "outer_transcript.log" } else { "" }

    $t10RecordOk = $false
    if (-not [string]::IsNullOrWhiteSpace($t10RecordFile) -and (Test-Path $t10RecordFile) -and (Test-Path $t10TranscriptFile)) {
        $t10Json = Get-Content $t10RecordFile -Raw | ConvertFrom-Json
        $t10RecordOk = ($t10Json.wrapper_outcome -eq "SIMULATED_SUCCESS") -and `
                       ($t10Json.simulation_mode -eq $true) -and `
                       ($t10Json.execution_mode -eq "SIMULATION_TEST") -and `
                       (-not [string]::IsNullOrWhiteSpace($t10Json.powershell_version)) -and `
                       ($t10Json.terminal_exit_code -eq 0) -and `
                       ($t10Json.child_executed -eq $true) -and `
                       ($t10Json.child_exit_code -eq 0) -and `
                       ($t10Json.transcript_closed_cleanly -eq $true) -and `
                       ($null -eq $t10Json.errors -or $t10Json.errors.Count -eq 0) -and `
                       (-not [string]::IsNullOrWhiteSpace($t10Json.run_id))
    }
    $t10Passed = ($t10Res.ExitCode -eq 0) -and $t10RecordOk
    Assert-Test "Clean Simulation Mode Produces SIMULATED_SUCCESS and Complete Record" $t10Passed "Expected exit 0 and SIMULATED_SUCCESS" $t10Res.Output

    # --------------------------------------------------------------------------
    # Test 11: Nonzero Child Exit Code (42) Preserved Distinctly in Record and Propagated
    # --------------------------------------------------------------------------
    $t11Dir = Join-Path $tempBase "t11"
    $t11Ws = Join-Path $tempBase "t11_ws"
    New-MockWorkspace $t11Ws
    $t11Cfg = Get-BaseTestConfig $t11Dir $t11Ws
    $t11Cfg["MockChildExitCode"] = 42
    $t11Res = Invoke-LauncherTest $t11Cfg
    $t11RunDirs = if (Test-Path $t11Dir) { Get-ChildItem -Path $t11Dir -Directory } else { @() }
    $t11RecordFile = if ($t11RunDirs.Count -gt 0) { Join-Path $t11RunDirs[0].FullName "launcher_record.json" } else { "" }

    $t11RecordOk = $false
    if (-not [string]::IsNullOrWhiteSpace($t11RecordFile) -and (Test-Path $t11RecordFile)) {
        $t11Json = Get-Content $t11RecordFile -Raw | ConvertFrom-Json
        $t11RecordOk = ($t11Json.wrapper_outcome -eq "CHILD_EXECUTION_FAILURE") -and `
                       ($t11Json.terminal_exit_code -eq 42) -and `
                       ($t11Json.child_executed -eq $true) -and `
                       ($t11Json.child_exit_code -eq 42)
    }
    $t11Passed = ($t11Res.ExitCode -eq 42) -and $t11RecordOk
    Assert-Test "Nonzero Child Exit Code (42) Preserved Distinctly and Propagated" $t11Passed "Expected exit 42 and CHILD_EXECUTION_FAILURE in record" $t11Res.Output

    # --------------------------------------------------------------------------
    # Test 12: Post-Execution Boundary Hash Mismatch Sets INTEGRITY_BREACH and Forces Exit 1
    # --------------------------------------------------------------------------
    $t12Dir = Join-Path $tempBase "t12"
    $t12Ws = Join-Path $tempBase "t12_ws"
    New-MockWorkspace $t12Ws
    $t12Cfg = Get-BaseTestConfig $t12Dir $t12Ws
    $t12Cfg["MockPostHashes"] = @{
        "scripts\matched_baseline\fast_tokenizer_adapter.py" = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    }
    $t12Res = Invoke-LauncherTest $t12Cfg
    $t12RunDirs = if (Test-Path $t12Dir) { Get-ChildItem -Path $t12Dir -Directory } else { @() }
    $t12RecordFile = if ($t12RunDirs.Count -gt 0) { Join-Path $t12RunDirs[0].FullName "launcher_record.json" } else { "" }

    $t12RecordOk = $false
    if (Test-Path $t12RecordFile) {
        $t12Json = Get-Content $t12RecordFile -Raw | ConvertFrom-Json
        $t12RecordOk = ($t12Json.wrapper_outcome -eq "INTEGRITY_BREACH") -and `
                       ($t12Json.terminal_exit_code -eq 1) -and `
                       (($t12Json.errors -join " ") -match "POST-EXECUTION INTEGRITY BREACH")
    }
    $t12Passed = ($t12Res.ExitCode -ne 0) -and $t12RecordOk
    Assert-Test "Post-Execution Boundary Hash Mismatch Sets INTEGRITY_BREACH and Forces Exit 1" $t12Passed "Expected exit 1 and INTEGRITY_BREACH in record" $t12Res.Output

    # --------------------------------------------------------------------------
    # Test 13: Per-File Post Hash Error Continues Checking Remaining Files
    # --------------------------------------------------------------------------
    $t13Dir = Join-Path $tempBase "t13"
    $t13Ws = Join-Path $tempBase "t13_ws"
    New-MockWorkspace $t13Ws
    $t13Cfg = Get-BaseTestConfig $t13Dir $t13Ws
    # Simulate thrown read error on first file to verify loop continuation across exceptions
    $t13Cfg["MockPostHashThrows"] = @("assets\tokenizers\tokenizer_manifest.sha256")
    $t13Res = Invoke-LauncherTest $t13Cfg
    $t13RunDirs = if (Test-Path $t13Dir) { Get-ChildItem -Path $t13Dir -Directory } else { @() }
    $t13RecordFile = if ($t13RunDirs.Count -gt 0) { Join-Path $t13RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t13Continued = $false
    if (Test-Path $t13RecordFile) {
        $t13Json = Get-Content $t13RecordFile -Raw | ConvertFrom-Json
        # Check that post_execution_hashes contains all 4 keys despite thrown exception on the first
        $t13Keys = $t13Json.post_execution_hashes.PSObject.Properties | ForEach-Object { $_.Name }
        $t13FirstVal = $t13Json.post_execution_hashes."assets\tokenizers\tokenizer_manifest.sha256"
        $t13Continued = ($t13Keys.Count -eq 4) -and `
                        ($t13FirstVal -match "READ_ERROR") -and `
                        ($t13Json.wrapper_outcome -eq "INTEGRITY_BREACH")
    }
    $t13Passed = ($t13Res.ExitCode -ne 0) -and $t13Continued
    Assert-Test "Per-File Post Hash Error Continues Checking Remaining Files" $t13Passed "Expected all 4 files evaluated in post_execution_hashes with READ_ERROR on first" $t13Res.Output

    # --------------------------------------------------------------------------
    # Test 14: Token Cleanup Verification Failure (Simulated Stuck Variable)
    # --------------------------------------------------------------------------
    $t14Dir = Join-Path $tempBase "t14"
    $t14Ws = Join-Path $tempBase "t14_ws"
    New-MockWorkspace $t14Ws
    $t14Cfg = Get-BaseTestConfig $t14Dir $t14Ws
    $t14Cfg["SimulateTokenCleanupFailure"] = $true
    $t14Res = Invoke-LauncherTest $t14Cfg
    $t14RunDirs = if (Test-Path $t14Dir) { Get-ChildItem -Path $t14Dir -Directory } else { @() }
    $t14RecordFile = if ($t14RunDirs.Count -gt 0) { Join-Path $t14RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t14CleanupCaught = $false
    if (Test-Path $t14RecordFile) {
        $t14Json = Get-Content $t14RecordFile -Raw | ConvertFrom-Json
        $t14CleanupCaught = (($t14Json.errors -join " ") -match "CLEANUP VERIFICATION FAILURE: HF_TOKEN") -and `
                            ($t14Json.wrapper_outcome -eq "WRAPPER_ERROR")
    }
    $t14Passed = ($t14Res.ExitCode -ne 0) -and $t14CleanupCaught
    Assert-Test "Token Cleanup Verification Failure Records Error and Exits 1" $t14Passed "Expected CLEANUP VERIFICATION FAILURE in record" $t14Res.Output

    # --------------------------------------------------------------------------
    # Test 15: Transcript Stop Failure Records Failure and Sets TRANSCRIPT_STOP_FAILURE
    # --------------------------------------------------------------------------
    $t15Dir = Join-Path $tempBase "t15"
    $t15Ws = Join-Path $tempBase "t15_ws"
    New-MockWorkspace $t15Ws
    $t15Cfg = Get-BaseTestConfig $t15Dir $t15Ws
    $t15Cfg["MockTranscriptStopFail"] = $true
    $t15Res = Invoke-LauncherTest $t15Cfg
    $t15RunDirs = if (Test-Path $t15Dir) { Get-ChildItem -Path $t15Dir -Directory } else { @() }
    $t15RecordFile = if ($t15RunDirs.Count -gt 0) { Join-Path $t15RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t15StopCaught = $false
    if (Test-Path $t15RecordFile) {
        $t15Json = Get-Content $t15RecordFile -Raw | ConvertFrom-Json
        $t15StopCaught = ($t15Json.wrapper_outcome -eq "TRANSCRIPT_STOP_FAILURE") -and `
                         ($t15Json.transcript_closed_cleanly -eq $false) -and `
                         (($t15Json.errors -join " ") -match "Simulated transcript stop failure")
    }
    $t15Passed = ($t15Res.ExitCode -ne 0) -and $t15StopCaught
    Assert-Test "Transcript Stop Failure Records Failure and Sets TRANSCRIPT_STOP_FAILURE" $t15Passed "Expected TRANSCRIPT_STOP_FAILURE in record" $t15Res.Output

    # --------------------------------------------------------------------------
    # Test 16: Reparse Point Base Directory Rejected Before Run Directory Creation
    # --------------------------------------------------------------------------
    $t16Dir = Join-Path $tempBase "t16"
    $t16Ws = Join-Path $tempBase "t16_ws"
    New-MockWorkspace $t16Ws
    $t16TargetDir = Join-Path $tempBase "t16_target"
    New-Item -ItemType Directory -Path $t16TargetDir -Force | Out-Null
    $t16Junction = Join-Path $tempBase "t16_junction"

    # Create directory junction via cmd /c mklink /J
    $mklinkOut = cmd /c "mklink /J `"$t16Junction`" `"$t16TargetDir`"" 2>&1
    if (Test-Path $t16Junction) {
        $t16Cfg = Get-BaseTestConfig $t16Junction $t16Ws
        $t16Res = Invoke-LauncherTest $t16Cfg
        $t16Passed = ($t16Res.ExitCode -ne 0) -and ($t16Res.Output -match "SECURITY ERROR") -and ($t16Res.Output -match "reparse point or symlink")
        Assert-Test "Reparse Point Base Directory Rejected Before Run Directory Creation" $t16Passed "Expected SECURITY ERROR for reparse point" $t16Res.Output
        # Remove junction
        cmd /c "rmdir `"$t16Junction`"" 2>&1 | Out-Null
    } else {
        # If filesystem privileges don't allow junction creation, label skip explicitly
        $script:testCount++
        $script:skipCount++
        Write-Output "  [SKIP] Test $script:testCount : Reparse Point Base Directory Rejected (Junction creation unprivileged, skipped)"
    }

    # --------------------------------------------------------------------------
    # Test 17: Exclusive Record Creation (CreateNew) Refuses Overwrite on Record Collision
    # --------------------------------------------------------------------------
    $t17Dir = Join-Path $tempBase "t17"
    $t17Ws = Join-Path $tempBase "t17_ws"
    New-MockWorkspace $t17Ws
    $t17FakeChild = Join-Path $tempBase "t17_fake_child.ps1"
    # The fake child script pre-creates launcher_record.json in its parent directory (the run directory)
    $fakeChildContent = @'
param($StagingDir)
$runDirectory = Split-Path $StagingDir -Parent
$recordFile = Join-Path $runDirectory "launcher_record.json"
[System.IO.File]::WriteAllText($recordFile, "PRE_EXISTING_RECORD_SENTINEL", [System.Text.Encoding]::UTF8)
exit 0
'@
    [System.IO.File]::WriteAllText($t17FakeChild, $fakeChildContent, [System.Text.Encoding]::UTF8)

    $t17Cfg = Get-BaseTestConfig $t17Dir $t17Ws
    $t17Cfg["FakeChildScript"] = $t17FakeChild
    $t17Res = Invoke-LauncherTest $t17Cfg

    $t17RunDirs = if (Test-Path $t17Dir) { Get-ChildItem -Path $t17Dir -Directory } else { @() }
    $t17RecordFile = if ($t17RunDirs.Count -gt 0) { Join-Path $t17RunDirs[0].FullName "launcher_record.json" } else { "" }
    $t17ContentPreserved = $false
    if (Test-Path $t17RecordFile) {
        $t17ContentPreserved = ((Get-Content $t17RecordFile -Raw) -eq "PRE_EXISTING_RECORD_SENTINEL")
    }
    $t17Passed = ($t17Res.ExitCode -ne 0) -and `
                 ($t17Res.Output -match "Failed to write launcher record") -and `
                 ($t17Res.Output -match "already exists") -and `
                 $t17ContentPreserved
    Assert-Test "Exclusive Creation (CreateNew) Refuses Overwrite on Record Collision" $t17Passed "Expected failure to overwrite pre-existing record and exit 1" $t17Res.Output

    Write-Output "=============================================================================="
    Write-Output "SYNTHETIC TEST RESULTS: $passCount / $testCount PASSED ($failCount FAILED, $skipCount SKIPPED)"
    Write-Output "=============================================================================="

} finally {
    Remove-Item -Path $tempBase -Recurse -Force -ErrorAction SilentlyContinue
}

if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
