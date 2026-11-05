# SOURCE ONLY. External user-paste hash must pin this final launcher independently.
$LaunchAdmitted = $true
$PacketPath = 'F:\TERRA -Copy\reports\cohort_controlled_freeze_20261024_01\execution_packet.json'
$PacketSha256 = '343b88b51d0c550e547e4336a7129ce4af3af6a972ba377d22b765d9de5cf477'
$AnchorPath = 'F:\TERRA -Copy\scripts\matched_baseline\offline_cohort_anchor.py'
$AnchorSha256 = 'aa1a844670e465c0e7f854a8322031f1bc6722b7cd7773c140d760d512b4ac7a'
$FrozenOuterSeconds = 2400
if (-not $LaunchAdmitted) { Write-Output 'BLOCKED: cohort launcher freeze/authority pending'; exit 2 }
$ErrorActionPreference = 'Stop'
$clock = [Diagnostics.Stopwatch]::StartNew()
function Assert-NoReparse([string]$path) {
    $current = [IO.Path]::GetFullPath($path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'Reparse path rejected'
            }
        }
        $parent = [IO.Path]::GetDirectoryName($current)
        if ($parent -eq $current) { break }; $current = $parent
    }
}
function Assert-Pin([string]$path,[string]$expected) {
    if (-not [IO.Path]::IsPathRooted($path) -or $expected -cnotmatch '^[a-f0-9]{64}$') { throw 'Invalid external pin' }
    Assert-NoReparse $path
    $hash = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try { $actual = [BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $hash.Dispose() }
    if ($actual -cne $expected) { throw 'External file identity mismatch' }
}
function Write-ExclusiveJson([string]$path,$value) {
    $raw = [Text.Encoding]::UTF8.GetBytes(($value | ConvertTo-Json -Depth 8 -Compress))
    if ($raw.Length -gt 4096) { throw 'Outer record bound exceeded' }
    $file = [IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try { $file.Write($raw,0,$raw.Length); $file.Flush($true) } finally { $file.Dispose() }
}
function Read-CompletePhase([string]$path,[string]$previous) {
    if (-not (Test-Path -LiteralPath $path)) {return $previous}
    Assert-NoReparse $path
    $file=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
    try {
        if ($file.Length -gt 65536) {throw 'Phase artifact ceiling'}
        $buffer=New-Object byte[] ([int]$file.Length)
        $count=$file.Read($buffer,0,$buffer.Length)
        $text=[Text.Encoding]::UTF8.GetString($buffer,0,$count)
    } finally {$file.Dispose()}
    $parts=$text.Split([char]10)
    # Last element may be an in-progress write; use only newline-ended records.
    if ($parts.Length -lt 2) {return $previous}
    $value=$parts[$parts.Length-2] | ConvertFrom-Json
    $order=@('SETUP','COPY','HASH','CHILD','CLEANUP')
    if ($order -cnotcontains $value.phase -or [array]::IndexOf($order,$value.phase) -lt [array]::IndexOf($order,$previous)) {
        throw 'Invalid/backwards controller phase'
    }
    return [string]$value.phase
}
function Stop-OwnedController($process,[long]$started,[string[]]$allowedImages) {
    if ($process.HasExited) { throw 'Root exited; descendant termination not certified' }
    $same = Get-Process -Id $process.Id -ErrorAction Stop
    try {
        if ($same.StartTime.ToUniversalTime().Ticks -ne $started -or
            $allowedImages -inotcontains $same.MainModule.FileName) { throw 'Owned root identity changed' }
    } finally { $same.Dispose() }
    # Venv redirectors may own one base-Python runtime. Record its identity
    # before stopping the root; never kill by executable name or wildcard.
    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" -OperationTimeoutSec 5 -ErrorAction Stop)
    $owned = @()
    foreach ($candidate in $children) {
        if ($allowedImages -inotcontains $candidate.ExecutablePath) { throw 'Unknown controller child retained' }
        $child = Get-Process -Id $candidate.ProcessId -ErrorAction Stop
        try { $owned += @{id=$child.Id; ticks=$child.StartTime.ToUniversalTime().Ticks; image=$child.MainModule.FileName} }
        finally { $child.Dispose() }
    }
    if ($owned.Count -gt 1) { throw 'Ambiguous direct descendants retained' }
    Stop-Process -Id $process.Id -ErrorAction Stop
    foreach ($identity in $owned) {
        $child = Get-Process -Id $identity.id -ErrorAction SilentlyContinue
        if ($null -ne $child) {
            try {
                if ($child.StartTime.ToUniversalTime().Ticks -ne $identity.ticks -or
                    $child.MainModule.FileName -ine $identity.image) { throw 'Owned child identity changed' }
                Stop-Process -Id $identity.id -ErrorAction Stop
            } finally { $child.Dispose() }
        }
    }
    if (-not $process.WaitForExit(5000)) { throw 'Controller stop unconfirmed' }
}
$process = $null; $capture = $null; $directory = $null; $outcome = 'FAIL'; $failure = $null
try {
    if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Administrator PS5.1 required' }
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator required' }
    Assert-Pin $PacketPath $PacketSha256; Assert-Pin $AnchorPath $AnchorSha256
    if ((Get-Item -LiteralPath $PacketPath).Length -gt 16777216) { throw 'Packet size ceiling' }
    $packet = Get-Content -Raw -LiteralPath $PacketPath | ConvertFrom-Json
    $body = $packet.body; $command = $body.command; $roles = @{}
    foreach ($pair in $body.launch.artifacts) { $roles[$pair[0]] = $pair[1] }
    if ($command.executable -cne $roles.controller_image.path -or
        $command.argv[3] -cne $roles.controller_entry.path -or
        $command.argv[1] -cne '-I' -or $command.argv[2] -cne '-B') { throw 'Controller role/argv mismatch' }
    if ((@($command.environment.PSObject.Properties.Name | Sort-Object) -join ',') -cne 'PATH,SYSTEMROOT,USERPROFILE,WINDIR') {
        throw 'Unreviewed controller environment keys'
    }
    if ($FrozenOuterSeconds -le 0 -or $FrozenOuterSeconds -ne $body.launch.parent.resources.outer_seconds) { throw 'Unfrozen deadline' }
    Assert-Pin $roles.controller_image.path $roles.controller_image.sha256
    Assert-Pin $roles.controller_entry.path $roles.controller_entry.sha256
    Assert-NoReparse $body.launch.allocation.root
    $directory = Join-Path $body.launch.allocation.root 'outer'
    New-Item -ItemType Directory -Path $directory -ErrorAction Stop | Out-Null
    Write-ExclusiveJson (Join-Path $directory 'outer.single_attempt.lock') @{packet_sha256=$PacketSha256; max_attempts=1}
    $capture = [IO.File]::Open((Join-Path $directory 'outer_output.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $command.executable; $info.Arguments = $body.native_arguments
    $info.WorkingDirectory = $command.cwd; $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $info.EnvironmentVariables.Clear()
    foreach ($property in $command.environment.PSObject.Properties) { $info.EnvironmentVariables[$property.Name] = [string]$property.Value }
    $process = New-Object Diagnostics.Process; $process.StartInfo = $info
    if (-not $process.Start()) { throw 'Controller start failed' }
    $started = $process.StartTime.ToUniversalTime().Ticks
    $outBuffer = New-Object byte[] 4096; $errBuffer = New-Object byte[] 4096
    $outTask = $process.StandardOutput.BaseStream.ReadAsync($outBuffer,0,4096)
    $errTask = $process.StandardError.BaseStream.ReadAsync($errBuffer,0,4096)
    $outDone = $false; $errDone = $false; [long]$captured = 0; $phase='SETUP'; $shutdownAt=$null
    $phasePath=Join-Path $body.launch.allocation.root 'parent\phases.jsonl'
    while (-not $process.HasExited -or -not $outDone -or -not $errDone) {
        $phase=Read-CompletePhase $phasePath $phase
        if ($clock.Elapsed.TotalSeconds -ge $FrozenOuterSeconds) { throw 'Outer finalization deadline exceeded' }
        $workDeadline=$FrozenOuterSeconds-$body.launch.parent.resources.finalization_reserve_seconds
        if ($phase -cne 'CLEANUP' -and $clock.Elapsed.TotalSeconds -ge $workDeadline) {
            if ($null -eq $shutdownAt) {
                Write-ExclusiveJson (Join-Path $directory 'shutdown_request.json') @{status='SHUTDOWN_REQUESTED';packet_sha256=$PacketSha256}
                $shutdownAt=$clock.Elapsed.TotalSeconds
            }
            if ($clock.Elapsed.TotalSeconds-$shutdownAt -ge $body.launch.parent.resources.termination_wait_seconds) {
                throw 'Controller did not enter cleanup during bounded shutdown grace'
            }
        }
        foreach ($kind in @('out','err')) {
            if ($kind -eq 'out') { $task=$outTask; $buffer=$outBuffer; $done=$outDone }
            else { $task=$errTask; $buffer=$errBuffer; $done=$errDone }
            if (-not $done -and $task.IsCompleted) {
                $count = $task.GetAwaiter().GetResult()
                if ($captured + $count -gt $body.launch.parent.resources.capture_bytes) { throw 'Outer capture ceiling' }
                if ($count -gt 0) { $capture.Write($buffer,0,$count); $capture.Flush(); $captured += $count }
                if ($kind -eq 'out') {
                    if ($count -eq 0) {$outDone=$true} else {$outTask=$process.StandardOutput.BaseStream.ReadAsync($outBuffer,0,4096)}
                } else {
                    if ($count -eq 0) {$errDone=$true} else {$errTask=$process.StandardError.BaseStream.ReadAsync($errBuffer,0,4096)}
                }
            }
        }
        Start-Sleep -Milliseconds 100
    }
    $phase=Read-CompletePhase $phasePath $phase
    if ($process.ExitCode -eq 0 -and $phase -ceq 'CLEANUP') { $outcome='CONTROLLER_EXIT_ZERO_REQUIRES_POSTRUN_AUDIT' }
} catch {
    $failure = $_.Exception.GetType().FullName
    if ($null -ne $process) {
        try { Stop-OwnedController $process $started @($roles.controller_image.path,$roles.firewall_image.path) }
        catch { $failure += ';OWNED_STOP_UNCONFIRMED' }
    }
    # No firewall removal here. Unknown controller/Job stop needs recovery review.
} finally {
    if ($null -ne $capture) { $capture.Flush($true); $capture.Dispose() }
    if ($null -ne $directory -and (Test-Path -LiteralPath $directory)) {
        Write-ExclusiveJson (Join-Path $directory 'outer_terminal.json') @{status=$outcome; failure_type=$failure; elapsed_seconds=$clock.Elapsed.TotalSeconds; packet_sha256=$PacketSha256; firewall_removal_attempted=$false}
    }
    if ($null -ne $process) {$process.Dispose()}
}
Write-Output ('COHORT WRAPPER OUTCOME: '+$outcome)
if ($outcome -eq 'CONTROLLER_EXIT_ZERO_REQUIRES_POSTRUN_AUDIT') {exit 0} else {exit 1}
