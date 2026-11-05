<#
.SYNOPSIS
    Hardened Operational Runbook for Single Offline Contemporary Diagnostic Execution.
.DESCRIPTION
    Strictly single-run execution script implementing all safeguards from Codex-0029,
    Codex-0030, Codex-0031, Codex-0032, Claude-0087 through Claude-0091:
    1. Elevation check (requires Administrator privileges for Windows Firewall management).
    2. Mandatory Start-Transcript console logging to a unique noncolliding path; fails closed if startup fails.
    3. Pre-execution boundary hash verification across interpreter, wrapper, diagnostic, benchmarks, and SQLite.
    4. Process inspection on pinned interpreter (redacting command lines); fails closed on known other PIDs
       unless -AllowOtherInterpreterProcesses is passed; tracks uncertain process visibility.
    5. Firewall service (mpssvc) running check and complete all-profile (Domain, Private, Public) enablement verification.
    6. Collision detection on exact rule Name using locale-independent ObjectNotFound category check.
    7. Exclusive pre-execution start record written before firewall modification or execution.
    8. Scoped outbound block creation on pinned interpreter with shared property verification function (Direction, Action, Enabled, Profile=Any, Program).
    9. Single native invocation with local Continue preference protecting exit code capture, tracking start/end UTC.
    10. Immediate capture of native $LASTEXITCODE and PSVersionTable recording.
    11. Guaranteed teardown in finally block with fail-closed removal verification (ObjectNotFound).
    12. Post-execution boundary rehash against pins, including on execution failure.
    13. Clean Stop-Transcript closure executed and error-captured BEFORE terminal status determination.
    14. Exclusive terminal JSON evidence emission with guarded failure handling; separate simulated vs production status.
    15. Strict production vs simulation separation: production rejects test config; simulation strictly prohibits live operations.

MANUAL RECOVERY INSTRUCTIONS:
If this runbook is aborted abnormally or interrupted by a system/power event:
1. Open PowerShell as Administrator.
2. Check if rule exists and inspect properties to establish ownership before deletion:
   $rule = Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction SilentlyContinue
   if ($rule) {
       $filter = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue
       Write-Host "Rule found: Name=$($rule.Name), Description=$($rule.Description), Program=$($filter.Program)"
       # Confirm ownership: exact Name, Description, and pinned Python path
       $nameMatch = ($rule.Name -eq "TERRA_Offline_Diagnostic_20261008")
       $descMatch = ($rule.Description -eq "Temporary outbound block for pinned Python diagnostic execution")
       $progMatch = ($filter.Program -eq "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe")
       if ($nameMatch -and $descMatch -and $progMatch) {
           Write-Host "Ownership confirmed. Removing temporary rule..."
           Remove-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction Stop
           Write-Host "Temporary rule removed."
       } else {
           Write-Error "ABORT: Rule exists but does not match expected Name, Description, or Program! Manual review required."
       }
   } else {
       Write-Host "Rule 'TERRA_Offline_Diagnostic_20261008' does not exist. No cleanup needed."
   }
3. Verify confirmed absence:
   try {
       Get-NetFirewallRule -Name "TERRA_Offline_Diagnostic_20261008" -ErrorAction Stop
       Write-Error "ERROR: Rule still exists!"
   } catch {
       if ($_.CategoryInfo.Category -eq 'ObjectNotFound' -or $_.FullyQualifiedErrorId -match 'ObjectNotFound') {
           Write-Host "Confirmed: Rule does not exist."
       } else {
           Write-Error "Query error: $($_.Exception.Message)"
       }
   }
#>

[CmdletBinding()]
param(
    [switch]$SimulationTestMode,
    [hashtable]$TestConfig = @{},
    [string]$TestConfigJson = "",
    [switch]$AllowOtherInterpreterProcesses
)

$ErrorActionPreference = "Stop"

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

if (-not [string]::IsNullOrWhiteSpace($TestConfigJson)) {
    try {
        $parsedJson = $TestConfigJson | ConvertFrom-Json
        $TestConfig = Convert-ToHashtable $parsedJson
    } catch {
        throw "Failed to parse -TestConfigJson: $($_.Exception.Message)"
    }
}

$hasTestConfig = ($TestConfig -ne $null -and $TestConfig.Count -gt 0)

# ------------------------------------------------------------------------------
# Strict Production vs. Simulation Separation
# ------------------------------------------------------------------------------
if (-not $SimulationTestMode) {
    if ($hasTestConfig) {
        $msg = "PRODUCTION VIOLATION: Test configuration parameters (-TestConfig / -TestConfigJson) are strictly forbidden in production mode. Pass -SimulationTestMode if running synthetic tests."
        [Console]::Error.WriteLine("[RUNBOOK FAULT] " + $msg)
        Write-Output "[RUNBOOK FAULT] $msg"
        exit 1
    }
} else {
    if (-not $hasTestConfig) {
        $msg = "TEST CONFIG FAULT: -SimulationTestMode was specified, but no test configuration was supplied."
        [Console]::Error.WriteLine("[RUNBOOK FAULT] " + $msg)
        Write-Output "[RUNBOOK FAULT] $msg"
        exit 1
    }
}

$isTestMode = [bool]$SimulationTestMode

$workspaceRoot = "F:\TERRA -Copy"
if ($isTestMode -and $TestConfig.ContainsKey("WorkspaceRoot")) {
    $workspaceRoot = $TestConfig["WorkspaceRoot"]
}
Set-Location -Path $workspaceRoot

$pinnedPy = "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$liveHarness = "F:\TERRA -Copy\scripts\run_diagnostic_harness.py"
$liveDiag = "F:\TERRA -Copy\scripts\audit_i1a_contemporary_gate_calibration.py"
$b350Path = "F:\TERRA -Copy\terra_350_benchmark.json"
$b175Path = "F:\TERRA -Copy\terra_175_benchmark.json"
$sqlitePath = "F:\TERRA -Copy\dataset_20k_cap\vector_db_20k\chroma.sqlite3"

$expPySha = "3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd"
$expWrapSha = "b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25"
$expDiagSha = "c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d"
$expB350Sha = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
$expB175Sha = "8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305"
$expSqliteSha = "3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6"

$ruleName = "TERRA_Offline_Diagnostic_20261008"
$ruleDisplayName = "TERRA_Offline_Diagnostic_20261008"
$ruleDescription = "Temporary outbound block for pinned Python diagnostic execution"

$runTimestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$guidPart = [guid]::NewGuid().ToString("N").Substring(0, 8)
$runId = "{0}_{1}_{2}" -f $runTimestampUtc, $PID, $guidPart

$evidenceBaseDir = "F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\reviewer_I0_I1a_20261008\evidence\runbook_records"
if ($isTestMode -and $TestConfig.ContainsKey("EvidenceBaseDir")) {
    $evidenceBaseDir = $TestConfig["EvidenceBaseDir"]
}
$runEvidenceDir = Join-Path $evidenceBaseDir ("runbook_" + $runId)

$boundParamNames = @($PSBoundParameters.Keys | Sort-Object)

$evidence = [ordered]@{
    "runbook_version" = "3.2.0"
    "timestamp_utc" = $runTimestampUtc
    "run_id" = $runId
    "workspace_root" = $workspaceRoot
    "ps_version" = $PSVersionTable.PSVersion.ToString()
    "execution_mode" = if ($isTestMode) { "SIMULATION_TEST" } else { "PRODUCTION_LIVE" }
    "simulation_mode" = $isTestMode
    "simulation_mock_applied" = $isTestMode
    "bound_parameters" = $boundParamNames
    "allow_other_interpreter_processes_flag" = [bool]$AllowOtherInterpreterProcesses
    "actual_firewall_enforced" = $false
    "actual_native_invoked" = $false
    "mock_parameters_supplied" = if ($isTestMode) { @($TestConfig.Keys | Sort-Object) } else { @() }
    "rule_name" = $ruleName
    "elevation_checked" = $false
    "transcript_started" = $false
    "transcript_closed_cleanly" = $false
    "pre_execution_hashes" = @{}
    "known_other_interpreter_processes" = @()
    "unreadable_processes_count" = 0
    "firewall_service_status" = ""
    "firewall_profiles_status" = @{}
    "pre_execution_record_attempted" = $false
    "rule_created_by_this_run" = $false
    "rule_verification_facts" = @{}
    "native_execution_attempted" = $false
    "simulated_native_execution" = $false
    "native_execution_start_utc" = $null
    "native_execution_end_utc" = $null
    "native_exit_code" = $null
    "teardown_attempted" = $false
    "teardown_verified" = $false
    "post_execution_hashes" = @{}
    "post_hashes_passed" = $false
    "terminal_record_attempted" = $false
    "operational_status" = "INITIALIZED"
    "errors" = @()
}

# ------------------------------------------------------------------------------
# Shared Rule-Check Validation Function
# ------------------------------------------------------------------------------
function Assert-Rule-Properties($ruleFacts, $expectedPinnedPy) {
    if (-not $ruleFacts) {
        throw "Rule audit failed: Rule verification facts object is null or empty."
    }
    if ($ruleFacts["Direction"] -ne "Outbound") {
        throw "Rule Direction mismatch: $($ruleFacts['Direction']) != Outbound"
    }
    if ($ruleFacts["Action"] -ne "Block") {
        throw "Rule Action mismatch: $($ruleFacts['Action']) != Block"
    }
    if ($ruleFacts["Enabled"] -ne "True") {
        throw "Rule Enabled mismatch: $($ruleFacts['Enabled']) != True"
    }
    $profStr = [string]$ruleFacts["Profile"]
    if ($profStr -ne "Any" -and $profStr -notmatch "Domain.*Private.*Public") {
        throw "Rule Profile coverage mismatch: $profStr"
    }
    $progPath = [string]$ruleFacts["Program"]
    if ([string]::IsNullOrWhiteSpace($progPath) -or $progPath.ToLower() -ne $expectedPinnedPy.ToLower()) {
        throw "Rule Program mismatch: $progPath != $expectedPinnedPy"
    }
}

function Save-Exclusive-Record {
    param(
        [string]$fileName,
        $payload
    )
    try {
        $filePath = Join-Path $runEvidenceDir $fileName
        if (Test-Path $filePath) {
            throw "COLLISION: Evidence file '$filePath' already exists! Overwrite forbidden."
        }
        if ($isTestMode -and $TestConfig.ContainsKey("MockEvidenceWriteFailure") -and $TestConfig["MockEvidenceWriteFailure"]) {
            throw "SIMULATED EVIDENCE WRITE FAILURE"
        }
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
        Write-Host "Evidence record saved: $filePath"
        return $true
    } catch {
        [Console]::Error.WriteLine("[EVIDENCE SAVE ERROR] " + $_.Exception.Message)
        $evidence["errors"] += "Evidence save failed ($fileName): $($_.Exception.Message)"
        return $false
    }
}

Write-Host "=============================================================================="
Write-Host "TERRA HARDENED OPERATIONAL RUNBOOK EXECUTION"
Write-Host "Run ID: $runId"
Write-Host "Start UTC: $runTimestampUtc"
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)"
Write-Host "Execution Mode: $($evidence['execution_mode'])"
Write-Host "=============================================================================="

$ruleCreated = $false
$transcriptStarted = $false
$transcriptPath = Join-Path $runEvidenceDir "runbook_console_transcript.txt"

try {
    # Ensure run evidence directory exists without -Force overwrite
    if (Test-Path $runEvidenceDir) {
        throw "COLLISION: Run directory '$runEvidenceDir' already exists! Aborting without modifications."
    }
    [System.IO.Directory]::CreateDirectory($runEvidenceDir) | Out-Null

    # --------------------------------------------------------------------------
    # Mandatory Start-Transcript (Fails Closed if Unavailable)
    # --------------------------------------------------------------------------
    try {
        if ($isTestMode -and $TestConfig.ContainsKey("MockTranscriptFailure") -and $TestConfig["MockTranscriptFailure"]) {
            throw "Simulated transcript startup error."
        }
        Start-Transcript -Path $transcriptPath -NoClobber -ErrorAction Stop | Out-Null
        $transcriptStarted = $true
        $evidence["transcript_started"] = $true
    } catch {
        throw "MANDATORY TRANSCRIPT FAILURE: Could not start console session transcript: $($_.Exception.Message)"
    }

    # --------------------------------------------------------------------------
    # Step 1: Elevation Check
    # --------------------------------------------------------------------------
    Write-Host "[STEP 1/7] Verifying Administrative Elevation..."
    $isAdmin = $false
    if ($isTestMode -and $TestConfig.ContainsKey("SkipElevationCheck") -and $TestConfig["SkipElevationCheck"]) {
        $isAdmin = $true
    } else {
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    $evidence["elevation_checked"] = $isAdmin
    if (-not $isAdmin) {
        throw "ELEVATION REQUIRED: Operational runbook requires an elevated PowerShell session (Run as Administrator) to manage Windows Defender Firewall rules."
    }
    Write-Host "PASS: Running with verified Administrator privileges."

    # --------------------------------------------------------------------------
    # Step 2: Pre-Execution Boundary Hash Verification
    # --------------------------------------------------------------------------
    Write-Host "[STEP 2/7] Verifying Pre-Execution Boundary Hashes..."
    $hPy     = ""
    $hWrap   = ""
    $hDiag   = ""
    $hB350   = ""
    $hB175   = ""
    $hSqlite = ""

    if ($isTestMode) {
        if (-not $TestConfig.ContainsKey("MockPreHashes")) {
            throw "TEST CONFIG FAULT: Test configuration omitted 'MockPreHashes'. Fall-through to real disk hashing is prohibited in test mode."
        }
        $mh = $TestConfig["MockPreHashes"]
        $hPy     = $mh["python_exe"]
        $hWrap   = $mh["run_diagnostic_harness"]
        $hDiag   = $mh["audit_i1a_contemporary"]
        $hB350   = $mh["terra_350_benchmark"]
        $hB175   = $mh["terra_175_benchmark"]
        $hSqlite = $mh["chroma_sqlite3"]
    } else {
        $hPy     = (Get-FileHash -Algorithm SHA256 $pinnedPy).Hash.ToLower()
        $hWrap   = (Get-FileHash -Algorithm SHA256 $liveHarness).Hash.ToLower()
        $hDiag   = (Get-FileHash -Algorithm SHA256 $liveDiag).Hash.ToLower()
        $hB350   = (Get-FileHash -Algorithm SHA256 $b350Path).Hash.ToLower()
        $hB175   = (Get-FileHash -Algorithm SHA256 $b175Path).Hash.ToLower()
        $hSqlite = (Get-FileHash -Algorithm SHA256 $sqlitePath).Hash.ToLower()
    }

    $evidence["pre_execution_hashes"] = [ordered]@{
        "python_exe" = @{ "actual" = $hPy; "expected" = $expPySha }
        "run_diagnostic_harness" = @{ "actual" = $hWrap; "expected" = $expWrapSha }
        "audit_i1a_contemporary" = @{ "actual" = $hDiag; "expected" = $expDiagSha }
        "terra_350_benchmark" = @{ "actual" = $hB350; "expected" = $expB350Sha }
        "terra_175_benchmark" = @{ "actual" = $hB175; "expected" = $expB175Sha }
        "chroma_sqlite3" = @{ "actual" = $hSqlite; "expected" = $expSqliteSha }
    }

    if ($hPy -ne $expPySha) { throw "Interpreter SHA-256 mismatch: $hPy != $expPySha" }
    if ($hWrap -ne $expWrapSha) { throw "Harness wrapper SHA-256 mismatch: $hWrap != $expWrapSha" }
    if ($hDiag -ne $expDiagSha) { throw "Diagnostic script SHA-256 mismatch: $hDiag != $expDiagSha" }
    if ($hB350 -ne $expB350Sha) { throw "Benchmark 350 SHA-256 mismatch: $hB350 != $expB350Sha" }
    if ($hB175 -ne $expB175Sha) { throw "Benchmark 175 SHA-256 mismatch: $hB175 != $expB175Sha" }
    if ($hSqlite -ne $expSqliteSha) { throw "Chroma SQLite SHA-256 mismatch: $hSqlite != $expSqliteSha" }
    Write-Host "PASS: All 6 boundary assets verified against pins."

    # --------------------------------------------------------------------------
    # Step 3: Environmental State (Other Processes, Service, Profiles)
    # --------------------------------------------------------------------------
    Write-Host "[STEP 3/7] Inspecting Process and Firewall Environment..."

    # Process Inspection
    $knownOtherProcs = @()
    $unreadableCount = 0
    if ($isTestMode) {
        if (-not $TestConfig.ContainsKey("MockOtherProcesses")) {
            throw "TEST CONFIG FAULT: Test configuration omitted 'MockOtherProcesses'. Fall-through to real Get-CimInstance is prohibited in test mode."
        }
        $mProcs = $TestConfig["MockOtherProcesses"]
        foreach ($p in $mProcs) {
            $knownOtherProcs += [ordered]@{
                "ProcessId" = $p["ProcessId"]
                "ExecutablePath" = $p["ExecutablePath"]
            }
        }
        if ($TestConfig.ContainsKey("MockUnreadableProcessesCount")) {
            $unreadableCount = [int]$TestConfig["MockUnreadableProcessesCount"]
        }
    } else {
        $allProcs = Get-CimInstance Win32_Process
        foreach ($p in $allProcs) {
            if ($p.ProcessId -eq $PID) { continue }
            $pPath = $p.ExecutablePath
            if ([string]::IsNullOrWhiteSpace($pPath)) {
                $unreadableCount++
            } elseif ($pPath.ToLower() -eq $pinnedPy.ToLower()) {
                $knownOtherProcs += [ordered]@{
                    "ProcessId" = $p.ProcessId
                    "ExecutablePath" = $pPath
                }
            }
        }
    }

    $evidence["known_other_interpreter_processes"] = $knownOtherProcs
    $evidence["unreadable_processes_count"] = $unreadableCount

    if ($knownOtherProcs.Count -gt 0) {
        if (-not $AllowOtherInterpreterProcesses) {
            throw "KNOWN OTHER INTERPRETER PROCESSES DETECTED: Found $($knownOtherProcs.Count) other process(es) running the pinned Python executable. Stop pending user awareness/approval (or pass -AllowOtherInterpreterProcesses)."
        } else {
            Write-Warning "Found $($knownOtherProcs.Count) other process(es) running the pinned interpreter. Explicitly permitted by parameter."
        }
    } else {
        Write-Host "PASS: Zero other known processes currently using pinned interpreter."
    }

    if ($unreadableCount -gt 0) {
        Write-Warning "Uncertain process visibility: $unreadableCount system/protected processes could not be inspected. Stored in evidence record."
    }

    # Verify Firewall Service (mpssvc) is Running
    $svcStatus = ""
    if ($isTestMode) {
        if (-not $TestConfig.ContainsKey("MockServiceStatus")) {
            throw "TEST CONFIG FAULT: Test configuration omitted 'MockServiceStatus'. Fall-through to real Get-Service is prohibited in test mode."
        }
        $svcStatus = $TestConfig["MockServiceStatus"]
    } else {
        $svc = Get-Service -Name "mpssvc" -ErrorAction Stop
        $svcStatus = [string]$svc.Status
    }
    $evidence["firewall_service_status"] = $svcStatus
    if ($svcStatus -ne "Running") {
        throw "FIREWALL SERVICE NOT RUNNING: Windows Defender Firewall service (mpssvc) status is '$svcStatus', expected 'Running'."
    }
    Write-Host "PASS: Windows Defender Firewall service (mpssvc) is Running."

    # Verify Complete Set of Firewall Profiles are Present and Enabled
    $profiles = $null
    if ($isTestMode) {
        if (-not $TestConfig.ContainsKey("MockProfiles")) {
            throw "TEST CONFIG FAULT: Test configuration omitted 'MockProfiles'. Fall-through to real Get-NetFirewallProfile is prohibited in test mode."
        }
        $profiles = $TestConfig["MockProfiles"]
    } else {
        $profiles = Get-NetFirewallProfile -ErrorAction Stop
    }

    $expectedProfiles = @("Domain", "Private", "Public")
    $foundProfiles = @{}
    $disabledProfiles = @()
    foreach ($prof in $profiles) {
        $pName = [string]$prof.Name
        $foundProfiles[$pName] = $prof
        $pEnabled = [string]$prof.Enabled
        $evidence["firewall_profiles_status"][$pName] = [ordered]@{
            "Enabled" = $pEnabled
            "DefaultOutboundAction" = [string]$prof.DefaultOutboundAction
        }
        if ($pEnabled -ne "True") {
            $disabledProfiles += $pName
        }
    }

    $missingProfiles = @()
    foreach ($exp in $expectedProfiles) {
        if (-not $foundProfiles.ContainsKey($exp)) {
            $missingProfiles += $exp
        }
    }

    if ($missingProfiles.Count -gt 0) {
        throw "FIREWALL PROFILES INCOMPLETE: Missing expected profile(s) [$($missingProfiles -join ', ')]. All three profiles (Domain, Private, Public) must be present and inspected."
    }
    if ($disabledProfiles.Count -gt 0) {
        throw "FIREWALL PROFILE DISABLED: Profile(s) [$($disabledProfiles -join ', ')] are disabled! All firewall profiles must be Enabled for verified enforcement."
    }
    Write-Host "PASS: All three Windows Firewall profiles (Domain, Private, Public) are present and Enabled."

    # --------------------------------------------------------------------------
    # Step 3b: Save Exclusive Pre-Execution Start Record
    # --------------------------------------------------------------------------
    $evidence["pre_execution_record_attempted"] = $true
    $preRecSaved = Save-Exclusive-Record "runbook_pre_execution_record.json" $evidence
    if (-not $preRecSaved) {
        throw "START RECORD FAILURE: Could not write exclusive pre-execution evidence record."
    }

    # --------------------------------------------------------------------------
    # Step 4: Rule Collision Check (Locale-Independent)
    # --------------------------------------------------------------------------
    Write-Host "[STEP 4/7] Checking for Existing Firewall Rule Collision..."
    $collision = $false
    if ($isTestMode) {
        if (-not $TestConfig.ContainsKey("MockCollision") -and -not ($TestConfig.ContainsKey("SkipActualFirewall") -and $TestConfig["SkipActualFirewall"])) {
            throw "TEST CONFIG FAULT: Test configuration omitted 'MockCollision'. Fall-through to real firewall rule query is prohibited in test mode."
        }
        if ($TestConfig.ContainsKey("MockCollision")) {
            $collision = [bool]$TestConfig["MockCollision"]
        } else {
            $collision = $false
        }
    } else {
        try {
            $existing = Get-NetFirewallRule -Name $ruleName -ErrorAction Stop
            if ($existing) { $collision = $true }
        } catch {
            if ($_.CategoryInfo.Category -eq 'ObjectNotFound' -or $_.FullyQualifiedErrorId -match 'ObjectNotFound') {
                $collision = $false
            } else {
                throw "Firewall query failed unexpectedly during collision check: $($_.Exception.Message)"
            }
        }
    }

    if ($collision) {
        throw "COLLISION: Firewall rule '$ruleName' already exists! Aborting without modifying rules."
    }
    Write-Host "PASS: No pre-existing rule with Name '$ruleName'."

    # --------------------------------------------------------------------------
    # Step 5: Firewall Creation and Strict Property Audit
    # --------------------------------------------------------------------------
    Write-Host "[STEP 5/7] Creating Temporary Scoped Firewall Rule..."
    if ($isTestMode) {
        if (-not ($TestConfig.ContainsKey("SkipActualFirewall") -and $TestConfig["SkipActualFirewall"])) {
            throw "TEST CONFIG FAULT: Test configuration did not specify 'SkipActualFirewall: true'. Real firewall mutation is strictly prohibited in test mode."
        }
        $ruleCreated = $true
        $evidence["rule_created_by_this_run"] = $true
        $evidence["actual_firewall_enforced"] = $false
        $mFacts = $TestConfig["MockRuleFacts"]
        $evidence["rule_verification_facts"] = $mFacts
        Assert-Rule-Properties $mFacts $pinnedPy
    } else {
        $newRule = New-NetFirewallRule `
            -Name $ruleName `
            -DisplayName $ruleDisplayName `
            -Description $ruleDescription `
            -Direction Outbound `
            -Program $pinnedPy `
            -Action Block `
            -Profile Any `
            -ErrorAction Stop

        $ruleCreated = $true
        $evidence["rule_created_by_this_run"] = $true
        $evidence["actual_firewall_enforced"] = $true

        # Query back and verify all required properties using shared function
        $verifiedRule = Get-NetFirewallRule -Name $ruleName -ErrorAction Stop
        $appFilter = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $verifiedRule -ErrorAction Stop

        $liveFacts = [ordered]@{
            "Name" = $verifiedRule.Name
            "DisplayName" = $verifiedRule.DisplayName
            "Direction" = [string]$verifiedRule.Direction
            "Action" = [string]$verifiedRule.Action
            "Enabled" = [string]$verifiedRule.Enabled
            "Profile" = [string]$verifiedRule.Profile
            "Program" = $appFilter.Program
        }
        $evidence["rule_verification_facts"] = $liveFacts
        Assert-Rule-Properties $liveFacts $pinnedPy
    }
    Write-Host "PASS: Firewall rule '$ruleName' verified."

    # --------------------------------------------------------------------------
    # Step 6: Native Diagnostic Invocation (Local Continue Preference)
    # --------------------------------------------------------------------------
    Write-Host "[STEP 6/7] Invoking Single Pinned Diagnostic Harness..."

    $nativeExit = -1
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $nativeStartUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $evidence["native_execution_start_utc"] = $nativeStartUtc
    try {
        if ($isTestMode) {
            if ($TestConfig.ContainsKey("MockChildExitCode")) {
                $nativeExit = [int]$TestConfig["MockChildExitCode"]
                $evidence["simulated_native_execution"] = $true
                $evidence["native_execution_attempted"] = $false
                $evidence["actual_native_invoked"] = $false
            } elseif ($TestConfig.ContainsKey("SkipActualExecution") -and $TestConfig["SkipActualExecution"]) {
                $nativeExit = 0
                $evidence["simulated_native_execution"] = $true
                $evidence["native_execution_attempted"] = $false
                $evidence["actual_native_invoked"] = $false
            } else {
                throw "TEST CONFIG FAULT: Test configuration did not specify 'SkipActualExecution: true' or 'MockChildExitCode'. Real diagnostic execution is strictly prohibited in test mode."
            }
        } else {
            $evidence["native_execution_attempted"] = $true
            $evidence["actual_native_invoked"] = $true
            $evidence["simulated_native_execution"] = $false
            & $pinnedPy $liveHarness --execute-diagnostic --enforced-offline-condition TERRA_Offline_Diagnostic
            $nativeExit = $LASTEXITCODE
        }
    } finally {
        $ErrorActionPreference = $prevEAP
        $nativeEndUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
        $evidence["native_execution_end_utc"] = $nativeEndUtc
    }

    $evidence["native_exit_code"] = $nativeExit
    Write-Host "Native invocation completed with exit code: $nativeExit"
    if ($nativeExit -ne 0) {
        $evidence["errors"] += "Diagnostic harness exited with non-zero exit code: $nativeExit"
    }

} catch {
    $evidence["errors"] += $_.Exception.Message
    [Console]::Error.WriteLine("[RUNBOOK FAULT] " + $_.Exception.Message)
    Write-Output "[RUNBOOK FAULT] $($_.Exception.Message)"
} finally {
    # --------------------------------------------------------------------------
    # Step 7: Guaranteed Teardown and Post-Execution Boundary Rehash
    # --------------------------------------------------------------------------
    try {
        Write-Host "[STEP 7/7] Executing Teardown and Post-Execution Boundary Rehash..."

        # Teardown rule only if this invocation created it
        if ($ruleCreated) {
            $evidence["teardown_attempted"] = $true
            if ($isTestMode) {
                if ($TestConfig.ContainsKey("MockTeardownFailure") -and $TestConfig["MockTeardownFailure"]) {
                    $evidence["errors"] += "SIMULATED TEARDOWN FAILURE: Removal failed."
                    $evidence["teardown_verified"] = $false
                    [Console]::Error.WriteLine("[RUNBOOK FAULT] SIMULATED TEARDOWN FAILURE: Removal failed.")
                    Write-Output "[RUNBOOK FAULT] SIMULATED TEARDOWN FAILURE: Removal failed."
                } else {
                    $evidence["teardown_verified"] = $true
                    Write-Host "PASS: Simulated firewall rule '$ruleName' confirmed removed."
                }
            } else {
                try {
                    Write-Host "Removing temporary firewall rule '$ruleName'..."
                    Remove-NetFirewallRule -Name $ruleName -ErrorAction Stop

                    # Verify removal (Locale-independent ObjectNotFound check)
                    try {
                        $checkPost = Get-NetFirewallRule -Name $ruleName -ErrorAction Stop
                        $evidence["errors"] += "Teardown verification failed: rule '$ruleName' still exists!"
                        $evidence["teardown_verified"] = $false
                    } catch {
                        if ($_.CategoryInfo.Category -eq 'ObjectNotFound' -or $_.FullyQualifiedErrorId -match 'ObjectNotFound') {
                            $evidence["teardown_verified"] = $true
                            Write-Host "PASS: Firewall rule '$ruleName' confirmed removed."
                        } else {
                            $evidence["errors"] += "Teardown verification encountered query error: $($_.Exception.Message)"
                            $evidence["teardown_verified"] = $false
                        }
                    }
                } catch {
                    $evidence["errors"] += "Teardown failed: $($_.Exception.Message)"
                    $evidence["teardown_verified"] = $false
                }
            }
        } else {
            Write-Host "No firewall rule created by this invocation; skipping removal."
        }

        # Post-Execution Rehash of Live Assets
        try {
            $postHPy     = ""
            $postHWrap   = ""
            $postHDiag   = ""
            $postHB350   = ""
            $postHB175   = ""
            $postHSqlite = ""

            if ($isTestMode) {
                if (-not $TestConfig.ContainsKey("MockPostHashes")) {
                    throw "TEST CONFIG FAULT: Test configuration omitted 'MockPostHashes'. Fall-through to real disk hashing is prohibited in test mode."
                }
                $mph = $TestConfig["MockPostHashes"]
                $postHPy     = $mph["python_exe"]
                $postHWrap   = $mph["run_diagnostic_harness"]
                $postHDiag   = $mph["audit_i1a_contemporary"]
                $postHB350   = $mph["terra_350_benchmark"]
                $postHB175   = $mph["terra_175_benchmark"]
                $postHSqlite = $mph["chroma_sqlite3"]
            } else {
                $postHPy     = (Get-FileHash -Algorithm SHA256 $pinnedPy).Hash.ToLower()
                $postHWrap   = (Get-FileHash -Algorithm SHA256 $liveHarness).Hash.ToLower()
                $postHDiag   = (Get-FileHash -Algorithm SHA256 $liveDiag).Hash.ToLower()
                $postHB350   = (Get-FileHash -Algorithm SHA256 $b350Path).Hash.ToLower()
                $postHB175   = (Get-FileHash -Algorithm SHA256 $b175Path).Hash.ToLower()
                $postHSqlite = (Get-FileHash -Algorithm SHA256 $sqlitePath).Hash.ToLower()
            }

            $evidence["post_execution_hashes"] = [ordered]@{
                "python_exe" = @{ "actual" = $postHPy; "expected" = $expPySha }
                "run_diagnostic_harness" = @{ "actual" = $postHWrap; "expected" = $expWrapSha }
                "audit_i1a_contemporary" = @{ "actual" = $postHDiag; "expected" = $expDiagSha }
                "terra_350_benchmark" = @{ "actual" = $postHB350; "expected" = $expB350Sha }
                "terra_175_benchmark" = @{ "actual" = $postHB175; "expected" = $expB175Sha }
                "chroma_sqlite3" = @{ "actual" = $postHSqlite; "expected" = $expSqliteSha }
            }

            $postOk = ($postHPy -eq $expPySha) -and `
                      ($postHWrap -eq $expWrapSha) -and `
                      ($postHDiag -eq $expDiagSha) -and `
                      ($postHB350 -eq $expB350Sha) -and `
                      ($postHB175 -eq $expB175Sha) -and `
                      ($postHSqlite -eq $expSqliteSha)

            $evidence["post_hashes_passed"] = $postOk
            if (-not $postOk) {
                $evidence["errors"] += "Post-execution boundary hash verification failed!"
                [Console]::Error.WriteLine("[RUNBOOK FAULT] Post-execution boundary hash verification failed!")
                Write-Output "[RUNBOOK FAULT] Post-execution boundary hash verification failed!"
            } else {
                Write-Host "PASS: Post-execution boundary hashes confirmed bit-identical."
            }
        } catch {
            $evidence["errors"] += "Post-execution hash verification crashed: $($_.Exception.Message)"
            $evidence["post_hashes_passed"] = $false
            [Console]::Error.WriteLine("[RUNBOOK FAULT] Post-execution hash verification crashed: " + $_.Exception.Message)
            Write-Output "[RUNBOOK FAULT] Post-execution hash verification crashed: $($_.Exception.Message)"
        }

    } finally {
        # ----------------------------------------------------------------------
        # Stop-Transcript Closure Executed BEFORE Terminal Status Determination
        # ----------------------------------------------------------------------
        if ($transcriptStarted) {
            try {
                if ($isTestMode -and $TestConfig.ContainsKey("MockTranscriptStopFailure") -and $TestConfig["MockTranscriptStopFailure"]) {
                    throw "Simulated transcript stop error."
                }
                Stop-Transcript -ErrorAction Stop | Out-Null
                [Console]::Error.WriteLine("Console transcript saved to: $transcriptPath")
                $evidence["transcript_closed_cleanly"] = $true
            } catch {
                [Console]::Error.WriteLine("[TRANSCRIPT STOP ERROR] " + $_.Exception.Message)
                Write-Output "[TRANSCRIPT STOP ERROR] $($_.Exception.Message)"
                $evidence["errors"] += "Stop-Transcript failed: $($_.Exception.Message)"
                $evidence["transcript_closed_cleanly"] = $false
            }
        }

        # ----------------------------------------------------------------------
        # Determine Final Operational Status with Clean Transcript Agreement
        # ----------------------------------------------------------------------
        $transcriptOk = (-not $transcriptStarted) -or ($evidence["transcript_closed_cleanly"] -eq $true)
        $execOk = ($evidence["native_exit_code"] -eq 0)
        $cleanOk = (-not $ruleCreated) -or ($evidence["teardown_verified"] -eq $true)
        $hashesOk = ($evidence["post_hashes_passed"] -eq $true)

        if ($execOk -and $cleanOk -and $hashesOk -and $transcriptOk -and ($evidence["errors"].Count -eq 0)) {
            if ($isTestMode) {
                $evidence["operational_status"] = "SIMULATED_SUCCESS"
                Write-Host "=============================================================================="
                Write-Host "RUNBOOK OUTCOME: SIMULATED_SUCCESS"
                Write-Host "=============================================================================="
            } else {
                $evidence["operational_status"] = "SUCCESS"
                Write-Host "=============================================================================="
                Write-Host "RUNBOOK OUTCOME: SUCCESS"
                Write-Host "=============================================================================="
            }
        } else {
            $evidence["operational_status"] = "OPERATIONAL_FAILURE"
            Write-Host "=============================================================================="
            Write-Host "RUNBOOK OUTCOME: OPERATIONAL_FAILURE"
            Write-Host "=============================================================================="
        }

        # ----------------------------------------------------------------------
        # Serialize Terminal Evidence Record (CreateNew Exclusive Write)
        # ----------------------------------------------------------------------
        $evidence["terminal_record_attempted"] = $true
        $termSaved = Save-Exclusive-Record "runbook_terminal_record.json" $evidence
        if (-not $termSaved) {
            $evidence["operational_status"] = "OPERATIONAL_FAILURE"
            [Console]::Error.WriteLine("[TERMINAL RECORD SAVE ERROR] Could not save exclusive terminal record.")
        }
    }
}

# If any stage failed, exit with non-zero exit code
if ($evidence["operational_status"] -ne "SUCCESS" -and $evidence["operational_status"] -ne "SIMULATED_SUCCESS") {
    exit 1
} else {
    exit 0
}
