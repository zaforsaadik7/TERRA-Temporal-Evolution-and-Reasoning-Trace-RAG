# Creates an EMPTY ignored credential file; never reads or displays a token.
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$path = Join-Path $workspace '.env.terra-databricks.local'
if (Test-Path -LiteralPath $path) { throw 'File already exists; no overwrite performed.' }
$stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
$stream.Dispose()
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = New-Object Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true, $false)
$acl.SetOwner($sid)
$rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'Allow')
$acl.AddAccessRule($rule)
$systemSid = New-Object Security.Principal.SecurityIdentifier('S-1-5-18')
$systemRule = New-Object Security.AccessControl.FileSystemAccessRule($systemSid, 'FullControl', 'Allow')
$acl.AddAccessRule($systemRule)
Set-Acl -LiteralPath $path -AclObject $acl
# The tool host can be a sandbox account, so also grant the verified human profile.
$profileMatches = @(Get-ChildItem -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList' | Where-Object {
    (Get-ItemProperty -LiteralPath $_.PSPath).ProfileImagePath -eq 'C:\Users\zafor'
})
if ($profileMatches.Count -ne 1) { throw 'Human profile identity unresolved; leave file empty.' }
$humanSid = $profileMatches[0].PSChildName
& "$env:SystemRoot\System32\icacls.exe" $path '/grant' "*$($humanSid):(F)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Human file access not granted; leave file empty.' }
[IO.File]::WriteAllText($path, "DATABRICKS_TOKEN=`r`n", [Text.UTF8Encoding]::new($false))
Write-Host 'Empty token file prepared for human profile user, setup owner and SYSTEM.'
Write-Host $path
Write-Host 'Open it yourself, paste the token after DATABRICKS_TOKEN=, and save. Do not paste it into chat.'
