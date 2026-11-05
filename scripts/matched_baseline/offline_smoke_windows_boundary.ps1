# Native adapter SOURCE ONLY: not admitted for execution by the current scope.
param(
    [Parameter(Mandatory=$true)][ValidateSet('environment','query','create','remove')][string]$Operation,
    [Parameter(Mandatory=$true)][string]$PayloadBase64
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($PayloadBase64)) | ConvertFrom-Json
if ($payload.name -notmatch '^TERRA_Smoke_[A-Za-z0-9_-]{8,80}$') { throw 'Invalid rule name' }
if ([string]::IsNullOrWhiteSpace($payload.owner_tag)) { throw 'Missing ownership tag' }
if (-not [IO.Path]::IsPathRooted($payload.program)) { throw 'Absolute program path required' }
$program = [IO.Path]::GetFullPath($payload.program)
function Read-ControllerIdentity {
    if ($null -eq $payload.controller_pid) { return $null }
    $controllerId = [int]$payload.controller_pid
    if ($controllerId -le 0) { throw 'Invalid controller PID' }
    # This PowerShell process must be the direct child of the Python controller.
    # No caller-selected unrelated PID or executable-path alias is exempted.
    $self = Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction Stop
    if ($null -eq $self -or [int]$self.ParentProcessId -ne $controllerId) { throw 'Controller is not direct parent' }
    $parent = Get-Process -Id $controllerId -ErrorAction Stop
    try {
        $image = $parent.MainModule.FileName
        $started = $parent.StartTime.ToUniversalTime().Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
        if ([string]::IsNullOrWhiteSpace($image) -or [IO.Path]::GetFullPath($image) -ine $program) {
            throw 'Controller runtime image mismatch'
        }
        if ($null -ne $payload.controller_start_ticks -and $started -cne $payload.controller_start_ticks) {
            throw 'Controller process identity changed'
        }
        return @{pid=$controllerId; program=$payload.program; start_ticks=$started}
    } finally { $parent.Dispose() }
}
$controller = Read-ControllerIdentity
function Read-InterpreterInventory {
    $known = @()
    $unreadable = 0
    foreach ($proc in @(Get-CimInstance Win32_Process -ErrorAction Stop)) {
        if ([string]::IsNullOrWhiteSpace($proc.ExecutablePath)) { $unreadable++; continue }
        if ($proc.ExecutablePath -ieq $program) { $known += [int]$proc.ProcessId }
    }
    if ($null -ne $controller -and $known -notcontains $controller.pid) { throw 'Controller absent from inventory' }
    return @{known_other_pids=@($known); unreadable_process_count=$unreadable}
}
function Read-Rules {
    # Enumerate first; absence is not inferred from an English error message.
    return @(Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction Stop |
        Where-Object { $_.Name -ceq $payload.name })
}
function Read-Identity($rule) {
    $filters = @($rule | Get-NetFirewallApplicationFilter -ErrorAction Stop)
    if ($filters.Count -ne 1) { throw 'Ambiguous application filter' }
    return @{
        name = [string]$rule.Name
        program = [string]$filters[0].Program
        owner_tag = [string]$rule.Description
        direction = [string]$rule.Direction
        action = [string]$rule.Action
        profile = [string]$rule.Profile
        enabled = ([string]$rule.Enabled -eq 'True')
    }
}
function Assert-Identity($identity) {
    if ($identity.name -cne $payload.name -or $identity.owner_tag -cne $payload.owner_tag -or
        $identity.program -ine $program -or $identity.direction -ne 'Outbound' -or
        $identity.action -ne 'Block' -or $identity.profile -ne 'Any' -or -not $identity.enabled) {
        throw 'Rule identity/property mismatch; removal forbidden'
    }
}
switch ($Operation) {
    'environment' {
        $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        $admin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        $service = Get-Service -Name mpssvc -ErrorAction Stop
        $profiles = @{}
        foreach ($profile in @(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop)) {
            if ($profiles.ContainsKey([string]$profile.Name)) { throw 'Duplicate profile' }
            $profiles[[string]$profile.Name] = ([string]$profile.Enabled -eq 'True')
        }
        $inventory = Read-InterpreterInventory
        @{ administrator=$admin; service=[string]$service.Status; profiles=$profiles;
           known_other_pids=@($inventory.known_other_pids); unreadable_process_count=$inventory.unreadable_process_count;
           verified_controller=$controller; adapter_parent_pid=$(if ($null -ne $controller) {$controller.pid} else {$null}) } | ConvertTo-Json -Depth 5 -Compress
    }
    'query' {
        $rules = @(Read-Rules)
        if ($rules.Count -gt 1) { throw 'Duplicate matching rule identities' }
        if ($rules.Count -eq 0) { Write-Output 'null' }
        else { (Read-Identity $rules[0]) | ConvertTo-Json -Compress }
    }
    'create' {
        if ($null -ne $controller -and $null -eq $payload.controller_start_ticks) {
            throw 'Prior controller identity required before creation'
        }
        $inventory = Read-InterpreterInventory
        foreach ($candidate in $inventory.known_other_pids) {
            if ($null -eq $controller -or $candidate -ne $controller.pid) { throw 'Known competing interpreter process' }
        }
        if (@(Read-Rules).Count -ne 0) { throw 'Rule collision' }
        New-NetFirewallRule -PolicyStore PersistentStore -Name $payload.name -DisplayName $payload.name `
            -Description $payload.owner_tag -Program $program -Direction Outbound -Action Block `
            -Profile Any -Enabled True -ErrorAction Stop | Out-Null
        # Outer controller owns read-back and ambiguity recovery.
        Write-Output 'null'
    }
    'remove' {
        $rules = @(Read-Rules)
        if ($rules.Count -ne 1) { throw 'Removal requires exactly one matching rule' }
        Assert-Identity (Read-Identity $rules[0])
        # Delete only the matching persistent rule, not a same-name policy rule.
        $persistent = @(Get-NetFirewallRule -PolicyStore PersistentStore -ErrorAction Stop |
            Where-Object { $_.Name -ceq $payload.name })
        if ($persistent.Count -ne 1) { throw 'Persistent ownership ambiguous' }
        Assert-Identity (Read-Identity $persistent[0])
        $persistent[0] | Remove-NetFirewallRule -ErrorAction Stop
        if (@(Read-Rules).Count -ne 0) { throw 'Removal not verified' }
        Write-Output 'null'
    }
}
