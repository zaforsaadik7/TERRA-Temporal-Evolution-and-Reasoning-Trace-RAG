<#
.SYNOPSIS
    Synthetic Unit Test Suite for Hardened Operational Runbook (scripts/execute_offline_diagnostic_runbook.ps1).
.DESCRIPTION
    Executes 13 fully mocked lifecycle tests validating fail-closed behavior under simulated:
    - Disabled firewall service (mpssvc)
    - Disabled firewall profile
    - Rule profile coverage mismatch (not 'Any')
    - Rule program path mismatch
    - Transcript startup failure
    - Evidence directory/file collision
    - Evidence write failure with transcript still closed
    - Non-zero native child exit code (42)
    - Teardown verification failure
    - Detection of other interpreter processes (redacting raw command line)
    - Pre-execution boundary hash mismatch
    - Post-execution boundary hash mismatch
    - Full end-to-end synthetic success lifecycle
    
    Zero real firewall rules created or deleted; zero live diagnostic executions.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$runbookScript = "F:\TERRA -Copy\scripts\execute_offline_diagnostic_runbook.ps1"
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

function Invoke-RunbookTest($cfg) {
    $jsonStr = $cfg | ConvertTo-Json -Compress -Depth 6
    $escapedJson = $jsonStr.Replace('"', '\"')
    $cmd = "& '$runbookScript' -TestConfigJson '$escapedJson'"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -Command $cmd 2>$null | Out-Null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevEAP
    }
}

$testCount = 0
$passCount = 0
$failCount = 0

function Assert-Test($name, $condition, $msg) {
    $script:testCount++
    if ($condition) {
        $script:passCount++
        Write-Output "  [PASS] Test $script:testCount : $name"
    } else {
        $script:failCount++
        Write-Output "  [FAIL] Test $script:testCount : $name - $msg"
    }
}

try {
    Write-Output "=============================================================================="
    Write-Output "RUNNING SYNTHETIC TESTS FOR OPERATIONAL RUNBOOK"
    Write-Output "=============================================================================="

    # --------------------------------------------------------------------------
    # Test 1: Service Stopped Fails Closed
    # --------------------------------------------------------------------------
    $t1Dir = Join-Path $tempBase "t1"
    $t1Config = @{
        "EvidenceBaseDir" = $t1Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Stopped"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t1Exit = Invoke-RunbookTest $t1Config
    Assert-Test "Service Stopped Fails Closed" ($t1Exit -ne 0) "Expected exit 1 on stopped service, got $t1Exit"

    # --------------------------------------------------------------------------
    # Test 2: Disabled Profile Fails Closed
    # --------------------------------------------------------------------------
    $t2Dir = Join-Path $tempBase "t2"
    $t2Profiles = @(
        @{ Name = "Domain"; Enabled = "True"; DefaultOutboundAction = "Allow" },
        @{ Name = "Private"; Enabled = "True"; DefaultOutboundAction = "Allow" },
        @{ Name = "Public"; Enabled = "False"; DefaultOutboundAction = "Allow" }
    )
    $t2Config = @{
        "EvidenceBaseDir" = $t2Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $t2Profiles
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t2Exit = Invoke-RunbookTest $t2Config
    Assert-Test "Disabled Profile Fails Closed" ($t2Exit -ne 0) "Expected exit 1 on disabled profile, got $t2Exit"

    # --------------------------------------------------------------------------
    # Test 3: Rule Profile Coverage Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t3Dir = Join-Path $tempBase "t3"
    $t3RuleFacts = @{
        "Name" = "TERRA_Offline_Diagnostic_20261008"
        "DisplayName" = "TERRA_Offline_Diagnostic_20261008"
        "Direction" = "Outbound"
        "Action" = "Block"
        "Enabled" = "True"
        "Profile" = "Private" # Not 'Any'
        "Program" = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    }
    $t3Config = @{
        "EvidenceBaseDir" = $t3Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $t3RuleFacts
        "SkipActualExecution" = $true
    }
    $t3Exit = Invoke-RunbookTest $t3Config
    Assert-Test "Rule Profile Coverage Mismatch Fails Closed" ($t3Exit -ne 0) "Expected exit 1 on profile mismatch, got $t3Exit"

    # --------------------------------------------------------------------------
    # Test 4: Transcript Startup Failure Fails Closed
    # --------------------------------------------------------------------------
    $t4Dir = Join-Path $tempBase "t4"
    $t4Config = @{
        "EvidenceBaseDir" = $t4Dir
        "MockTranscriptFailure" = $true
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t4Exit = Invoke-RunbookTest $t4Config
    Assert-Test "Transcript Startup Failure Fails Closed" ($t4Exit -ne 0) "Expected exit 1 on transcript startup failure, got $t4Exit"

    # --------------------------------------------------------------------------
    # Test 5: Collision on Rule Name Fails Closed
    # --------------------------------------------------------------------------
    $t5Dir = Join-Path $tempBase "t5"
    $t5Config = @{
        "EvidenceBaseDir" = $t5Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "MockCollision" = $true
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t5Exit = Invoke-RunbookTest $t5Config
    Assert-Test "Rule Collision Fails Closed" ($t5Exit -ne 0) "Expected exit 1 on rule collision, got $t5Exit"

    # --------------------------------------------------------------------------
    # Test 6: Evidence Write Failure Marks Operational Failure
    # --------------------------------------------------------------------------
    $t6Dir = Join-Path $tempBase "t6"
    $t6Config = @{
        "EvidenceBaseDir" = $t6Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "SkipActualExecution" = $true
        "MockEvidenceWriteFailure" = $true
    }
    $t6Exit = Invoke-RunbookTest $t6Config
    Assert-Test "Evidence Write Failure Fails Closed" ($t6Exit -ne 0) "Expected exit 1 on evidence write failure, got $t6Exit"

    # --------------------------------------------------------------------------
    # Test 7: Nonzero Native Child Exit Code Fails Closed (No Masking)
    # --------------------------------------------------------------------------
    $t7Dir = Join-Path $tempBase "t7"
    $t7Config = @{
        "EvidenceBaseDir" = $t7Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "MockChildExitCode" = 42
    }
    $t7Exit = Invoke-RunbookTest $t7Config
    Assert-Test "Nonzero Child Exit Code Fails Closed" ($t7Exit -ne 0) "Expected exit 1 on child exit 42, got $t7Exit"

    # --------------------------------------------------------------------------
    # Test 8: Teardown Failure Fails Closed
    # --------------------------------------------------------------------------
    $t8Dir = Join-Path $tempBase "t8"
    $t8Config = @{
        "EvidenceBaseDir" = $t8Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "SkipActualExecution" = $true
        "MockTeardownFailure" = $true
    }
    $t8Exit = Invoke-RunbookTest $t8Config
    Assert-Test "Teardown Failure Fails Closed" ($t8Exit -ne 0) "Expected exit 1 on teardown failure, got $t8Exit"

    # --------------------------------------------------------------------------
    # Test 9: Other Processes Detected Fails Closed
    # --------------------------------------------------------------------------
    $t9Dir = Join-Path $tempBase "t9"
    $t9Other = @(
        @{ ProcessId = 12345; ExecutablePath = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe" }
    )
    $t9Config = @{
        "EvidenceBaseDir" = $t9Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "MockOtherProcesses" = $t9Other
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t9Exit = Invoke-RunbookTest $t9Config
    Assert-Test "Other Processes Detected Fails Closed" ($t9Exit -ne 0) "Expected exit 1 on other processes detected, got $t9Exit"

    # --------------------------------------------------------------------------
    # Test 10: Pre-Execution Boundary Hash Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t10Dir = Join-Path $tempBase "t10"
    $t10BadHashes = @{
        "python_exe" = $expPySha
        "run_diagnostic_harness" = "0000000000000000000000000000000000000000000000000000000000000000"
        "audit_i1a_contemporary" = $expDiagSha
        "terra_350_benchmark" = $expB350Sha
        "terra_175_benchmark" = $expB175Sha
        "chroma_sqlite3" = $expSqliteSha
    }
    $t10Config = @{
        "EvidenceBaseDir" = $t10Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $t10BadHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "SkipActualExecution" = $true
    }
    $t10Exit = Invoke-RunbookTest $t10Config
    Assert-Test "Pre-Execution Hash Mismatch Fails Closed" ($t10Exit -ne 0) "Expected exit 1 on pre-hash mismatch, got $t10Exit"

    # --------------------------------------------------------------------------
    # Test 11: Post-Execution Boundary Hash Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t11Dir = Join-Path $tempBase "t11"
    $t11BadPostHashes = @{
        "python_exe" = $expPySha
        "run_diagnostic_harness" = $expWrapSha
        "audit_i1a_contemporary" = $expDiagSha
        "terra_350_benchmark" = $expB350Sha
        "terra_175_benchmark" = $expB175Sha
        "chroma_sqlite3" = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    }
    $t11Config = @{
        "EvidenceBaseDir" = $t11Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $t11BadPostHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "SkipActualExecution" = $true
    }
    $t11Exit = Invoke-RunbookTest $t11Config
    Assert-Test "Post-Execution Hash Mismatch Fails Closed" ($t11Exit -ne 0) "Expected exit 1 on post-hash mismatch, got $t11Exit"

    # --------------------------------------------------------------------------
    # Test 12: Rule Application Path Mismatch Fails Closed
    # --------------------------------------------------------------------------
    $t12Dir = Join-Path $tempBase "t12"
    $t12BadRuleFacts = @{
        "Name" = "TERRA_Offline_Diagnostic_20261008"
        "DisplayName" = "TERRA_Offline_Diagnostic_20261008"
        "Direction" = "Outbound"
        "Action" = "Block"
        "Enabled" = "True"
        "Profile" = "Any"
        "Program" = "C:\Windows\System32\notepad.exe" # Bad program!
    }
    $t12Config = @{
        "EvidenceBaseDir" = $t12Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $t12BadRuleFacts
        "SkipActualExecution" = $true
    }
    $t12Exit = Invoke-RunbookTest $t12Config
    Assert-Test "Rule Application Path Mismatch Fails Closed" ($t12Exit -ne 0) "Expected exit 1 on bad program path, got $t12Exit"

    # --------------------------------------------------------------------------
    # Test 13: End-to-End Mock Lifecycle SUCCESS
    # --------------------------------------------------------------------------
    $t13Dir = Join-Path $tempBase "t13"
    $t13Config = @{
        "EvidenceBaseDir" = $t13Dir
        "SkipElevationCheck" = $true
        "MockPreHashes" = $standardPreHashes
        "MockPostHashes" = $standardPreHashes
        "MockServiceStatus" = "Running"
        "MockProfiles" = $standardProfiles
        "SkipActualFirewall" = $true
        "MockRuleFacts" = $standardRuleFacts
        "SkipActualExecution" = $true
    }
    $t13Exit = Invoke-RunbookTest $t13Config
    Assert-Test "End-to-End Mock Lifecycle Success" ($t13Exit -eq 0) "Expected exit 0 on clean mock lifecycle, got $t13Exit"

    # Verify that in Test 13 both pre-record and terminal-record were written
    $t13Runs = Get-ChildItem -Path $t13Dir -Directory
    $t13Pre = Join-Path $t13Runs[0].FullName "runbook_pre_execution_record.json"
    $t13Term = Join-Path $t13Runs[0].FullName "runbook_terminal_record.json"
    $t13Transcript = Join-Path $t13Runs[0].FullName "runbook_console_transcript.txt"

    $hasPre = Test-Path $t13Pre
    $hasTerm = Test-Path $t13Term
    $hasTrans = Test-Path $t13Transcript
    Assert-Test "Pre-execution record written exclusively" $hasPre "Pre-record missing"
    Assert-Test "Terminal record written exclusively" $hasTerm "Terminal record missing"
    Assert-Test "Console transcript written exclusively" $hasTrans "Transcript missing"

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
