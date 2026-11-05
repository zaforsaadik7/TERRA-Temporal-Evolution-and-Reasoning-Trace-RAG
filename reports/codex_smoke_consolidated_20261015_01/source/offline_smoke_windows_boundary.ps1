# Native adapter SOURCE ONLY: not admitted for execution by the current scope.
param(
    [Parameter(Mandatory=$true)][ValidateSet('environment','query','create','remove')][string]$Operation,
    [Parameter(Mandatory=$true)][string]$PayloadBase64
)
$ErrorActionPreference = 'Stop'
$payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($PayloadBase64)) | ConvertFrom-Json
if ($payload.name -notmatch '^TERRA_Smoke_[A-Za-z0-9_-]{8,80}$') { throw 'Invalid rule name' }
if ([string]::IsNullOrWhiteSpace($payload.owner_tag)) { throw 'Missing ownership tag' }
if (-not [IO.Path]::IsPathRooted($payload.program)) { throw 'Absolute program path required' }
$program = [IO.Path]::GetFullPath($payload.program)
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
        $known = @()
        $unreadable = 0
        foreach ($proc in @(Get-CimInstance Win32_Process -ErrorAction Stop)) {
            if ([string]::IsNullOrWhiteSpace($proc.ExecutablePath)) { $unreadable++; continue }
            if ($proc.ExecutablePath -ieq $program) { $known += [int]$proc.ProcessId }
        }
        @{ administrator=$admin; service=[string]$service.Status; profiles=$profiles;
           known_other_pids=@($known); unreadable_process_count=$unreadable } | ConvertTo-Json -Depth 5 -Compress
    }
    'query' {
        $rules = @(Read-Rules)
        if ($rules.Count -gt 1) { throw 'Duplicate matching rule identities' }
        if ($rules.Count -eq 0) { Write-Output 'null' }
        else { (Read-Identity $rules[0]) | ConvertTo-Json -Compress }
    }
    'create' {
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
