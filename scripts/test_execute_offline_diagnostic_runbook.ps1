<#
.SYNOPSIS
    Comprehensive Synthetic Unit Test Suite for Hardened Operational Runbook (scripts/execute_offline_diagnostic_runbook.ps1).
.DESCRIPTION
    Validates all fail-closed modes, guardrails, and simulation lifecycle states addressing Codex-0031,
    Codex-0032, Codex-0033, and Claude-0090/0091/0092:
    - Production mode rejection of non-empty test configuration parameters
    - Strict test mode isolation (missing mocks fail closed before real operations)
    - Complete firewall profile set enforcement (Domain, Private, Public)
    - Disabled firewall service and profile fail-closed behavior
    - Shared rule property validation (profile coverage, program path)
    - Mandatory transcript startup failure and stop failure agreement
    - Live AST-extracted Save-Exclusive-Record sentinel collision protection (unchanged bytes and error)
    - Control 1: FileMode.CreateNew defense-in-depth protection without Test-Path guard
    - Control 2: Unsafe FileMode.Create overwrite demonstration (proving test sensitivity)
    - Non-zero native child exit code preservation without masking
    - Process inspection on pinned interpreter and fail-closed stopping
    - Pre- and post-execution boundary hash verification
    - Clean simulation mode identity and operational status serialization

    Zero real firewall rules created or deleted; zero Python subprocesses run.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$runbookScript = "F:\TERRA -Copy\scripts\execute_offline_diagnostic_runbook.ps1"
$testScriptPath = "F:\TERRA -Copy\scripts\test_execute_offline_diagnostic_runbook.ps1"

$tempBase = Join-Path $env:TEMP ("terra_runbook_test_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempBase -Force | Out-Null

$expPySha = "3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd"
$expWrapSha = "b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25"
$expDiagSha = "c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d"
$expB350Sha = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
$expB175Sha = "8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305"
$expSqliteSha = "3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6"

$standardPreHashes = @{
    "python_exe" = $expPySha
    "run_diagnostic_harness" = $expWrapSha
    "audit_i1a_contemporary" = $expDiagSha
    "terra_350_benchmark" = $expB350Sha
    "terra_175_benchmark" = $expB175Sha
    "chroma_sqlite3" = $expSqliteSha
}

$standardRuleFacts = @{
    "Name" = "TERRA_Offline_Diagnostic_20261008"
    "DisplayName" = "TERRA_Offline_Diagnostic_20261008"
    "Direction" = "Outbound"
    "Action" = "Block"
    "Enabled" = "True"
    "Profile" = "Any"
    "Program" = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe"
}

$standardProfiles = @(
    @{ Name = "Domain"; Enabled = "True"; DefaultOutboundAction = "Allow" },
    @{ Name = "Private"; Enabled = "True"; DefaultOutboundAction = "Allow" },
    @{ Name = "Public"; Enabled = "True"; DefaultOutboundAction = "Allow" }
)

function Get-BaseMockConfig($dir) {
    return @{
        "EvidenceBaseDir" = $dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockOtherProcesses" = @()
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "MockCollision" = $false
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "SkipActualExecution" = $true
    }
}

function Invoke-RunbookTest($cfg, [bool]$passSimulationTestMode = $true) {
    $jsonStr = $cfg | ConvertTo-Json -Compress -Depth 6
    $escapedJson = $jsonStr.Replace('"', '\"')
    $flag = if ($passSimulationTestMode) { "-SimulationTestMode" } else { "" }
    $cmd = "& '$runbookScript' $flag -TestConfigJson '$escapedJson'"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
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
    } finally {
        $ErrorActionPreference = $prevEAP
    }
}

$testCount = 0
$passCount = 0
$failCount = 0

function Assert-Test($name, [bool]$condition, [string]$msg) {
    $script:testCount++
    if ($condition) {
        $script:passCount++
        Write-Output "  [PASS] Test $script:testCount : $name"
    } else {
        $script:failCount++
        Write-Output "  [FAIL] Test $script:testCount : $name - $msg"
    }
}

$rbHash = (Get-FileHash -Algorithm SHA256 $runbookScript).Hash.ToLower()
$tsHash = (Get-FileHash -Algorithm SHA256 $testScriptPath).Hash.ToLower()
$nowUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

Write-Output "=============================================================================="
Write-Output "SYNTHETIC TEST SUITE EXECUTION LOG: OPERATIONAL RUNBOOK"
Write-Output "Timestamp UTC      : $nowUtc"
Write-Output "PowerShell Version : $($PSVersionTable.PSVersion)"
Write-Output "PowerShell Edition : $($PSVersionTable.PSEdition)"
Write-Output "OS Version         : $([System.Environment]::OSVersion.VersionString)"
Write-Output "Runbook Script     : $runbookScript"
Write-Output "Runbook SHA-256    : $rbHash"
Write-Output "Test Suite Script  : $testScriptPath"
Write-Output "Test Suite SHA-256 : $tsHash"
Write-Output "Invocation Command : powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test_execute_offline_diagnostic_runbook.ps1"
Write-Output "=============================================================================="

try {
    # --------------------------------------------------------------------------
    # Test 1: Production Rejection of Non-empty Test Configuration
    # --------------------------------------------------------------------------
    $t1Dir = Join-Path $tempBase "t1"
    $t1Cfg = Get-BaseMockConfig $t1Dir
    $t1Res = Invoke-RunbookTest $t1Cfg -passSimulationTestMode $false
    $t1Passed = ($t1Res.ExitCode -ne 0) -and ($t1Res.Output -match "PRODUCTION VIOLATION: Test configuration parameters")
    Assert-Test "Production Rejection of Non-empty Test Configuration" $t1Passed "Expected exit 1 and PRODUCTION VIOLATION, got exit $($t1Res.ExitCode)"

    # --------------------------------------------------------------------------
    # Test 2: Missing MockOtherProcesses in Test Mode Fails Closed
    # --------------------------------------------------------------------------
    $t2Dir = Join-Path $tempBase "t2"
    $t2Cfg = Get-BaseMockConfig $t2Dir
    $t2Cfg.Remove("MockOtherProcesses")
    $t2Res = Invoke-RunbookTest $t2Cfg
    $t2Passed = ($t2Res.ExitCode -ne 0) -and ($t2Res.Output -match "TEST CONFIG FAULT: Test configuration omitted 'MockOtherProcesses'")
    Assert-Test "Missing MockOtherProcesses Fails Closed" $t2Passed "Expected exit 1 and TEST CONFIG FAULT for MockOtherProcesses"

    # --------------------------------------------------------------------------
    # Test 3: Missing MockPostHashes in Test Mode Fails Closed
    # --------------------------------------------------------------------------
    $t3Dir = Join-Path $tempBase "t3"
    $t3Cfg = Get-BaseMockConfig $t3Dir
    $t3Cfg.Remove("MockPostHashes")
    $t3Res = Invoke-RunbookTest $t3Cfg
    $t3Passed = ($t3Res.ExitCode -ne 0) -and ($t3Res.Output -match "TEST CONFIG FAULT: Test configuration omitted 'MockPostHashes'")
    Assert-Test "Missing MockPostHashes Fails Closed" $t3Passed "Expected exit 1 and TEST CONFIG FAULT for MockPostHashes"

    # --------------------------------------------------------------------------
    # Test 4: Missing MockPreHashes in Test Mode Fails Closed
    # --------------------------------------------------------------------------
    $t4Dir = Join-Path $tempBase "t4"
    $t4Cfg = Get-BaseMockConfig $t4Dir
    $t4Cfg.Remove("MockPreHashes")
    $t4Res = Invoke-RunbookTest $t4Cfg
    $t4Passed = ($t4Res.ExitCode -ne 0) -and ($t4Res.Output -match "TEST CONFIG FAULT: Test configuration omitted 'MockPreHashes'")
    Assert-Test "Missing MockPreHashes Fails Closed" $t4Passed "Expected exit 1 and TEST CONFIG FAULT for MockPreHashes"

    # --------------------------------------------------------------------------
    # Test 5: Firewall Service Stopped Fails Closed
    # --------------------------------------------------------------------------
    $t5Dir = Join-Path $tempBase "t5"
    $t5Cfg = Get-BaseMockConfig $t5Dir
    $t5Cfg["MockServiceStatus"] = "Stopped"
    $t5Res = Invoke-RunbookTest $t5Cfg
    $t5Passed = ($t5Res.ExitCode -ne 0) -and ($t5Res.Output -match "FIREWALL SERVICE NOT RUNNING")
    Assert-Test "Firewall Service Stopped Fails Closed" $t5Passed "Expected exit 1 and FIREWALL SERVICE NOT RUNNING error"

    # --------------------------------------------------------------------------
    # Test 6: Incomplete Firewall Profiles (Missing Public) Fails Closed
    # --------------------------------------------------------------------------
    $t6Dir = Join-Path $tempBase "t6"
    $t6Cfg = Get-BaseMockConfig $t6Dir
    $t6Cfg["MockProfiles"] = @(
        @{ Name = "Domain"; Enabled = "True"; DefaultOutboundAction = "Allow" },
        @{ Name = "Private"; Enabled = "True"; DefaultOutboundAction = "Allow" }
    )
    $t6Res = Invoke-RunbookTest $t6Cfg
    $t6Passed = ($t6Res.ExitCode -ne 0) -and ($t6Res.Output -match "FIREWALL PROFILES INCOMPLETE: Missing expected profile\(s\) \[Public\]")
    Assert-Test "Incomplete Firewall Profiles Set Fails Closed" $t6Passed "Expected exit 1 and FIREWALL PROFILES INCOMPLETE error"

    # --------------------------------------------------------------------------
    # Test 7: Empty Firewall Profiles Set Fails Closed
    # --------------------------------------------------------------------------
    $t7Dir = Join-Path $tempBase "t7"
    $t7Cfg = Get-BaseMockConfig $t7Dir
    $t7Cfg["MockProfiles"] = @()
    $t7Res = Invoke-RunbookTest $t7Cfg
    $t7Passed = ($t7Res.ExitCode -ne 0) -and ($t7Res.Output -match "FIREWALL PROFILES INCOMPLETE: Missing expected profile\(s\) \[Domain, Private, Public\]")
    Assert-Test "Empty Firewall Profiles Set Fails Closed" $t7Passed "Expected exit 1 and empty profiles error"

    # --------------------------------------------------------------------------
    # Test 8: Disabled Firewall Profile Fails Closed
    # --------------------------------------------------------------------------
    $t8Dir = Join-Path $tempBase "t8"
    $t8Cfg = Get-BaseMockConfig $t8Dir
    $t8Cfg["MockProfiles"] = @(
        @{ Name = "Domain"; Enabled = "True"; DefaultOutboundAction = "Allow" },
        @{ Name = "Private"; Enabled = "True"; DefaultOutboundAction = "Allow" },
        @{ Name = "Public"; Enabled = "False"; DefaultOutboundAction = "Allow" }
    )
    $t8Res = Invoke-RunbookTest $t8Cfg
    $t8Passed = ($t8Res.ExitCode -ne 0) -and ($t8Res.Output -match "FIREWALL PROFILE DISABLED: Profile\(s\) \[Public\] are disabled!")
    Assert-Test "Disabled Firewall Profile Fails Closed" $t8Passed "Expected exit 1 and FIREWALL PROFILE DISABLED error"

    # --------------------------------------------------------------------------
    # Test 9: Shared Rule Validation: Profile Coverage Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t9Dir = Join-Path $tempBase "t9"
    $t9Cfg = Get-BaseMockConfig $t9Dir
    $t9BadRule = @{
        "Name" = "TERRA_Offline_Diagnostic_20261008"
        "DisplayName" = "TERRA_Offline_Diagnostic_20261008"
        "Direction" = "Outbound"
        "Action" = "Block"
        "Enabled" = "True"
        "Profile" = "Private" # Mismatch
        "Program" = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    }
    $t9Cfg["MockRuleFacts"] = $t9BadRule
    $t9Res = Invoke-RunbookTest $t9Cfg
    $t9Passed = ($t9Res.ExitCode -ne 0) -and ($t9Res.Output -match "Rule Profile coverage mismatch: Private")
    Assert-Test "Rule Profile Coverage Mismatch Fails Closed" $t9Passed "Expected exit 1 and Profile coverage mismatch"

    # --------------------------------------------------------------------------
    # Test 10: Shared Rule Validation: Program Path Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t10Dir = Join-Path $tempBase "t10"
    $t10Cfg = Get-BaseMockConfig $t10Dir
    $t10BadProg = @{
        "Name" = "TERRA_Offline_Diagnostic_20261008"
        "DisplayName" = "TERRA_Offline_Diagnostic_20261008"
        "Direction" = "Outbound"
        "Action" = "Block"
        "Enabled" = "True"
        "Profile" = "Any"
        "Program" = "C:\Windows\System32\notepad.exe" # Bad program
    }
    $t10Cfg["MockRuleFacts"] = $t10BadProg
    $t10Res = Invoke-RunbookTest $t10Cfg
    $t10Passed = ($t10Res.ExitCode -ne 0) -and ($t10Res.Output -match "Rule Program mismatch:")
    Assert-Test "Rule Program Path Mismatch Fails Closed" $t10Passed "Expected exit 1 and Program mismatch error"

    # --------------------------------------------------------------------------
    # Test 11: Transcript Startup Failure Fails Closed
    # --------------------------------------------------------------------------
    $t11Dir = Join-Path $tempBase "t11"
    $t11Cfg = Get-BaseMockConfig $t11Dir
    $t11Cfg["MockTranscriptFailure"] = $true
    $t11Res = Invoke-RunbookTest $t11Cfg
    $t11Passed = ($t11Res.ExitCode -ne 0) -and ($t11Res.Output -match "MANDATORY TRANSCRIPT FAILURE")
    Assert-Test "Transcript Startup Failure Fails Closed" $t11Passed "Expected exit 1 and MANDATORY TRANSCRIPT FAILURE"

    # --------------------------------------------------------------------------
    # Test 12: Transcript Stop Failure Recorded Cleanly with Disk Agreement
    # --------------------------------------------------------------------------
    $t12Dir = Join-Path $tempBase "t12"
    $t12Cfg = Get-BaseMockConfig $t12Dir
    $t12Cfg["MockTranscriptStopFailure"] = $true
    $t12Res = Invoke-RunbookTest $t12Cfg
    $t12RunDirs = Get-ChildItem -Path $t12Dir -Directory
    $t12TermFile = Join-Path $t12RunDirs[0].FullName "runbook_terminal_record.json"
    $t12DiskStatusMatch = $false
    if (Test-Path $t12TermFile) {
        $t12Json = Get-Content $t12TermFile -Raw | ConvertFrom-Json
        $t12DiskStatusMatch = ($t12Json.operational_status -eq "OPERATIONAL_FAILURE") -and `
                              ($t12Json.transcript_closed_cleanly -eq $false) -and `
                              (($t12Json.errors -join " ") -match "Stop-Transcript failed")
    }
    $t12Passed = ($t12Res.ExitCode -ne 0) -and ($t12Res.Output -match "TRANSCRIPT STOP ERROR") -and $t12DiskStatusMatch
    Assert-Test "Transcript Stop Failure Leaves Failure on Disk and Exits 1" $t12Passed "Expected transcript stop error and matching OPERATIONAL_FAILURE on disk"

    # --------------------------------------------------------------------------
    # Test 13: Rule Collision Fails Closed Without Mutation
    # --------------------------------------------------------------------------
    $t13Dir = Join-Path $tempBase "t13"
    $t13Cfg = Get-BaseMockConfig $t13Dir
    $t13Cfg["MockCollision"] = $true
    $t13Res = Invoke-RunbookTest $t13Cfg
    $t13Passed = ($t13Res.ExitCode -ne 0) -and ($t13Res.Output -match "COLLISION: Firewall rule 'TERRA_Offline_Diagnostic_20261008' already exists!")
    Assert-Test "Rule Collision Fails Closed" $t13Passed "Expected exit 1 and COLLISION error"

    # --------------------------------------------------------------------------
    # Test 14: Nonzero Native Child Exit Code (42) Preserved Without Masking
    # --------------------------------------------------------------------------
    $t14Dir = Join-Path $tempBase "t14"
    $t14Cfg = Get-BaseMockConfig $t14Dir
    $t14Cfg["MockChildExitCode"] = 42
    $t14Res = Invoke-RunbookTest $t14Cfg
    $t14RunDirs = Get-ChildItem -Path $t14Dir -Directory
    $t14TermFile = Join-Path $t14RunDirs[0].FullName "runbook_terminal_record.json"
    $t14ChildCodeMatch = $false
    if (Test-Path $t14TermFile) {
        $t14Json = Get-Content $t14TermFile -Raw | ConvertFrom-Json
        $t14ChildCodeMatch = ($t14Json.native_exit_code -eq 42) -and ($t14Json.operational_status -eq "OPERATIONAL_FAILURE")
    }
    $t14Passed = ($t14Res.ExitCode -ne 0) -and $t14ChildCodeMatch
    Assert-Test "Nonzero Native Exit Code Preserved in Terminal Record" $t14Passed "Expected exit 42 recorded and OPERATIONAL_FAILURE"

    # --------------------------------------------------------------------------
    # Test 15: Teardown Failure Fails Closed
    # --------------------------------------------------------------------------
    $t15Dir = Join-Path $tempBase "t15"
    $t15Cfg = Get-BaseMockConfig $t15Dir
    $t15Cfg["MockTeardownFailure"] = $true
    $t15Res = Invoke-RunbookTest $t15Cfg
    $t15Passed = ($t15Res.ExitCode -ne 0) -and ($t15Res.Output -match "SIMULATED TEARDOWN FAILURE")
    Assert-Test "Teardown Failure Fails Closed" $t15Passed "Expected exit 1 and teardown failure recorded"

    # --------------------------------------------------------------------------
    # Test 16: Other Interpreter Processes Detected Fails Closed
    # --------------------------------------------------------------------------
    $t16Dir = Join-Path $tempBase "t16"
    $t16Cfg = Get-BaseMockConfig $t16Dir
    $t16Cfg["MockOtherProcesses"] = @(
        @{ ProcessId = 99999; ExecutablePath = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe" }
    )
    $t16Res = Invoke-RunbookTest $t16Cfg
    $t16Passed = ($t16Res.ExitCode -ne 0) -and ($t16Res.Output -match "KNOWN OTHER INTERPRETER PROCESSES DETECTED")
    Assert-Test "Other Interpreter Processes Detected Fails Closed" $t16Passed "Expected exit 1 and process conflict"

    # --------------------------------------------------------------------------
    # Test 17: Pre-Execution Hash Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t17Dir = Join-Path $tempBase "t17"
    $t17Cfg = Get-BaseMockConfig $t17Dir
    $t17BadPre = $standardPreHashes.Clone()
    $t17BadPre["run_diagnostic_harness"] = "0000000000000000000000000000000000000000000000000000000000000000"
    $t17Cfg["MockPreHashes"] = $t17BadPre
    $t17Res = Invoke-RunbookTest $t17Cfg
    $t17Passed = ($t17Res.ExitCode -ne 0) -and ($t17Res.Output -match "Harness wrapper SHA-256 mismatch")
    Assert-Test "Pre-Execution Hash Mismatch Fails Closed" $t17Passed "Expected exit 1 and wrapper hash mismatch"

    # --------------------------------------------------------------------------
    # Test 18: Post-Execution Hash Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t18Dir = Join-Path $tempBase "t18"
    $t18Cfg = Get-BaseMockConfig $t18Dir
    $t18BadPost = $standardPreHashes.Clone()
    $t18BadPost["terra_350_benchmark"] = "0000000000000000000000000000000000000000000000000000000000000000"
    $t18Cfg["MockPostHashes"] = $t18BadPost
    $t18Res = Invoke-RunbookTest $t18Cfg
    $t18Passed = ($t18Res.ExitCode -ne 0) -and ($t18Res.Output -match "Post-execution boundary hash verification failed")
    Assert-Test "Post-Execution Hash Mismatch Fails Closed" $t18Passed "Expected exit 1 and post-hash failure"

    # --------------------------------------------------------------------------
    # Test 19: Real Save-Exclusive-Record AST: Sentinel Collision Refused & Untouched
    # --------------------------------------------------------------------------
    $t19Dir = Join-Path $tempBase "t19"
    New-Item -ItemType Directory -Path $t19Dir -Force | Out-Null
    $t19SentinelFile = Join-Path $t19Dir "runbook_pre_execution_record.json"
    $t19SentinelContent = "SENTINEL_PRE_RECORD_BYTES_REMAIN_IDENTICAL_DO_NOT_ALTER"
    [System.IO.File]::WriteAllText($t19SentinelFile, $t19SentinelContent, [System.Text.Encoding]::UTF8)
    $t19HashBefore = (Get-FileHash -Algorithm SHA256 $t19SentinelFile).Hash.ToLower()

    # Extract live Save-Exclusive-Record function AST directly from runbook script
    $rbAst = [System.Management.Automation.Language.Parser]::ParseFile($runbookScript, [ref]$null, [ref]$null)
    $funcAst = $rbAst.Find({
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq "Save-Exclusive-Record"
    }, $true)
    $liveWriterSb = $funcAst.Body.GetScriptBlock()

    # Set invocation context matching the live script environment
    $runEvidenceDir = $t19Dir
    $evidence = [ordered]@{ "errors" = @() }
    $isTestMode = $false
    $TestConfig = @{}

    $t19WriteResult = & $liveWriterSb "runbook_pre_execution_record.json" @{ "status" = "ATTEMPTED_OVERWRITE_DATA" }

    $t19ContentAfter = [System.IO.File]::ReadAllText($t19SentinelFile, [System.Text.Encoding]::UTF8)
    $t19HashAfter = (Get-FileHash -Algorithm SHA256 $t19SentinelFile).Hash.ToLower()
    $t19Siblings = (Get-ChildItem -Path $t19Dir).Count

    $t19Passed = ($t19WriteResult -eq $false) -and `
                 ($evidence["errors"].Count -gt 0) -and `
                 (($evidence["errors"] -join " ") -match "COLLISION: Evidence file '.*runbook_pre_execution_record\.json' already exists! Overwrite forbidden\.") -and `
                 ($t19ContentAfter -eq $t19SentinelContent) -and `
                 ($t19HashAfter -eq $t19HashBefore) -and `
                 ($t19Siblings -eq 1)

    Assert-Test "Real Save-Exclusive-Record AST: Sentinel Collision Refused & Bytes Untouched" $t19Passed "Expected false return, explicit collision error naming path, unchanged bytes, and no siblings"

    # --------------------------------------------------------------------------
    # Test 20: Control 1: CreateNew Alone Refuses Overwrite & Preserves Sentinel
    # --------------------------------------------------------------------------
    $t20Dir = Join-Path $tempBase "t20"
    New-Item -ItemType Directory -Path $t20Dir -Force | Out-Null
    $t20SentinelFile = Join-Path $t20Dir "sentinel_createnew_control.json"
    $t20SentinelContent = "SENTINEL_CREATENEW_CONTROL_BYTES_DO_NOT_ALTER"
    [System.IO.File]::WriteAllText($t20SentinelFile, $t20SentinelContent, [System.Text.Encoding]::UTF8)
    $t20HashBefore = (Get-FileHash -Algorithm SHA256 $t20SentinelFile).Hash.ToLower()

    # In-memory writer omitting the Test-Path check to isolate FileMode.CreateNew defense-in-depth
    $writerNoTestPath = {
        param($fileName, $payload)
        try {
            $filePath = Join-Path $runEvidenceDir $fileName
            # Note: Test-Path pre-check intentionally omitted to isolate FileMode.CreateNew
            $json = $payload | ConvertTo-Json -Depth 6
            $fileStream = [System.IO.FileStream]::new(
                $filePath,
                [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::None
            )
            try {
                $writer = [System.IO.StreamWriter]::new($fileStream, [System.Text.Encoding]::UTF8)
                try {
                    $writer.Write($json)
                } finally {
                    $writer.Dispose()
                }
            } finally {
                $fileStream.Dispose()
            }
            return $true
        } catch {
            $evidence["errors"] += "CreateNew threw: $($_.Exception.Message)"
            return $false
        }
    }

    $runEvidenceDir = $t20Dir
    $evidence = [ordered]@{ "errors" = @() }

    $t20WriteResult = & $writerNoTestPath "sentinel_createnew_control.json" @{ "status" = "ATTEMPTED_OVERWRITE" }

    $t20ContentAfter = [System.IO.File]::ReadAllText($t20SentinelFile, [System.Text.Encoding]::UTF8)
    $t20HashAfter = (Get-FileHash -Algorithm SHA256 $t20SentinelFile).Hash.ToLower()

    $t20Passed = ($t20WriteResult -eq $false) -and `
                 ($evidence["errors"].Count -gt 0) -and `
                 (($evidence["errors"] -join " ") -match "The file '.*' already exists\.") -and `
                 ($t20ContentAfter -eq $t20SentinelContent) -and `
                 ($t20HashAfter -eq $t20HashBefore)

    Assert-Test "Control 1: CreateNew Alone Refuses Overwrite & Preserves Sentinel" $t20Passed "CreateNew alone failed to protect sentinel without Test-Path"

    # --------------------------------------------------------------------------
    # Test 21: Control 2: Unsafe Overwrite Writer Overwrites Sentinel (Sensitivity Proof)
    # --------------------------------------------------------------------------
    $t21Dir = Join-Path $tempBase "t21"
    New-Item -ItemType Directory -Path $t21Dir -Force | Out-Null
    $t21SentinelFile = Join-Path $t21Dir "sentinel_unsafe_control.json"
    $t21SentinelContent = "SENTINEL_UNSAFE_ORIGINAL_BYTES"
    [System.IO.File]::WriteAllText($t21SentinelFile, $t21SentinelContent, [System.Text.Encoding]::UTF8)
    $t21HashBefore = (Get-FileHash -Algorithm SHA256 $t21SentinelFile).Hash.ToLower()

    # Intentionally unsafe writer using FileMode.Create (permitting overwrite)
    $unsafeWriter = {
        param($fileName, $payload)
        try {
            $filePath = Join-Path $runEvidenceDir $fileName
            $json = $payload | ConvertTo-Json -Depth 6
            # Unsafe: FileMode.Create replaces/overwrites existing file
            $fileStream = [System.IO.FileStream]::new(
                $filePath,
                [System.IO.FileMode]::Create,
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::None
            )
            try {
                $writer = [System.IO.StreamWriter]::new($fileStream, [System.Text.Encoding]::UTF8)
                try {
                    $writer.Write($json)
                } finally {
                    $writer.Dispose()
                }
            } finally {
                $fileStream.Dispose()
            }
            return $true
        } catch {
            $evidence["errors"] += "Unsafe threw: $($_.Exception.Message)"
            return $false
        }
    }

    $runEvidenceDir = $t21Dir
    $evidence = [ordered]@{ "errors" = @() }

    $t21WriteResult = & $unsafeWriter "sentinel_unsafe_control.json" @{ "status" = "SUCCESSFULLY_OVERWRITTEN" }

    $t21ContentAfter = [System.IO.File]::ReadAllText($t21SentinelFile, [System.Text.Encoding]::UTF8)
    $t21HashAfter = (Get-FileHash -Algorithm SHA256 $t21SentinelFile).Hash.ToLower()

    # Proves the test harness detects overwrites when safeguards are absent
    $t21Overwritten = ($t21WriteResult -eq $true) -and `
                      ($t21ContentAfter -ne $t21SentinelContent) -and `
                      ($t21HashAfter -ne $t21HashBefore)

    Assert-Test "Control 2: Unsafe Overwrite Writer Overwrites Sentinel (Proving Sensitivity)" $t21Overwritten "Unsafe writer unexpectedly preserved sentinel"

    # --------------------------------------------------------------------------
    # Test 22: Clean Simulation Mode Lifecycle & Complete Identity Proof
    # --------------------------------------------------------------------------
    $t22Dir = Join-Path $tempBase "t22"
    $t22Cfg = Get-BaseMockConfig $t22Dir
    $t22Res = Invoke-RunbookTest $t22Cfg
    $t22RunDirs = Get-ChildItem -Path $t22Dir -Directory
    $t22TermFile = Join-Path $t22RunDirs[0].FullName "runbook_terminal_record.json"
    $t22PreFile = Join-Path $t22RunDirs[0].FullName "runbook_pre_execution_record.json"
    $t22TransFile = Join-Path $t22RunDirs[0].FullName "runbook_console_transcript.txt"

    $t22IdentOk = $false
    if ((Test-Path $t22TermFile) -and (Test-Path $t22PreFile) -and (Test-Path $t22TransFile)) {
        $t22Json = Get-Content $t22TermFile -Raw | ConvertFrom-Json
        $t22PreJson = Get-Content $t22PreFile -Raw | ConvertFrom-Json

        $statusOk = ($t22Json.operational_status -eq "SIMULATED_SUCCESS")
        $modeOk = ($t22Json.execution_mode -eq "SIMULATION_TEST") -and ($t22Json.simulation_mode -eq $true)
        $noLiveEnforce = ($t22Json.actual_firewall_enforced -eq $false) -and ($t22Json.actual_native_invoked -eq $false)
        $simNative = ($t22Json.simulated_native_execution -eq $true) -and ($t22Json.native_execution_attempted -eq $false)
        $transOk = ($t22Json.transcript_closed_cleanly -eq $true)
        $timingOk = (-not [string]::IsNullOrWhiteSpace($t22Json.native_execution_start_utc))
        $preAttempted = ($t22PreJson.pre_execution_record_attempted -eq $true)
        $termAttempted = ($t22Json.terminal_record_attempted -eq $true)
        $boundParamsOk = ($t22Json.bound_parameters -contains "SimulationTestMode")

        $t22IdentOk = $statusOk -and $modeOk -and $noLiveEnforce -and $simNative -and `
                      $transOk -and $timingOk -and $preAttempted -and $termAttempted -and $boundParamsOk
    }

    $t22Passed = ($t22Res.ExitCode -eq 0) -and $t22IdentOk
    Assert-Test "Clean Simulation Lifecycle with Complete Identity Proof" $t22Passed "Simulation lifecycle failed or identity fields incorrect"

    Write-Output "=============================================================================="
    Write-Output "SYNTHETIC TEST RESULTS: $passCount / $testCount PASSED ($failCount FAILED)"
    Write-Output "=============================================================================="

} finally {
    Remove-Item -Path $tempBase -Recurse -Force -ErrorAction SilentlyContinue
}

if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
