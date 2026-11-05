"""PS5.1 AST extraction: safe helper functions/temp files only, never main body."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests import test_offline_smoke_user_launcher_synthetic as fixtures

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'scripts/matched_baseline/launch_offline_cohort_user.ps1'


@unittest.skipUnless(os.name=='nt' and fixtures.PS.is_file(),'PS5.1 parser required')
class CohortLauncherTests(unittest.TestCase):
    def evaluate(self,body):
        harness=fixtures.UserLauncherTests()
        with tempfile.TemporaryDirectory() as tmp,patch.object(fixtures,'SOURCE',SOURCE):
            return harness.evaluate(body,root=Path(tmp))

    def test_full_parse_and_hold_precedes_native_operations(self):
        self.evaluate("Write-Output 'PARSE_OK'")
        text=SOURCE.read_text()
        self.assertLess(text.index('if (-not $LaunchAdmitted)'),text.index('[Diagnostics.Stopwatch]'))
        self.assertIn('$LaunchAdmitted = $false',text)
        self.assertIn('$PacketSha256 = $null',text)
        self.assertNotIn('-Verb RunAs',text)
        self.assertNotIn('Remove-NetFirewallRule',text)

    def test_exclusive_record_and_pinned_fixture(self):
        self.evaluate(r'''
$path=Join-Path $root 'record.json'
Write-ExclusiveJson $path @{value=1}
$before=[IO.File]::ReadAllBytes($path)
$hash=[Security.Cryptography.SHA256]::Create()
try {$sha=[BitConverter]::ToString($hash.ComputeHash($before)).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}
Assert-Pin $path $sha
$caught=$false; try {Write-ExclusiveJson $path @{value=2}} catch {$caught=$true}
if (-not $caught) {throw 'Overwrite allowed'}
[IO.File]::AppendAllText($path,' ')
$caught=$false; try {Assert-Pin $path $sha} catch {$caught=$true}
if (-not $caught) {throw 'Changed bytes accepted'}
''')

    def test_stopping_uses_only_verified_ids_with_fake_commands(self):
        self.evaluate(r'''
$global:stopped=@()
$date=[DateTime]'2026-10-24T00:00:00Z'
function Get-Process {
    param($Id,$ErrorAction)
    $p=[pscustomobject]@{Id=$Id;StartTime=$date;MainModule=[pscustomobject]@{FileName='C:\fixture\python.exe'}}
    $p | Add-Member ScriptMethod Dispose {} -Force
    return $p
}
function Get-CimInstance { param($ClassName,$Filter,$OperationTimeoutSec,$ErrorAction); return @() }
function Stop-Process { param($Id,$ErrorAction); $global:stopped+=@($Id) }
$p=[pscustomobject]@{Id=42;HasExited=$false}
$p | Add-Member ScriptMethod WaitForExit {param($timeout);return $true} -Force
Stop-OwnedController $p $date.ToUniversalTime().Ticks @('C:\fixture\python.exe')
if ($global:stopped.Count -ne 1 -or $global:stopped[0] -ne 42) {throw 'Foreign PID touched'}
$global:stopped=@()
$caught=$false; try {Stop-OwnedController $p 1 @('C:\fixture\python.exe')} catch {$caught=$true}
if (-not $caught -or $global:stopped.Count -ne 0) {throw 'Changed identity accepted'}
''')

    def test_boundary_adapter_parsed_not_executed_and_only_namespace_changed(self):
        original=(ROOT/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1').read_text()
        changed=(ROOT/'scripts/matched_baseline/offline_cohort_windows_boundary.ps1').read_text()
        expected=original.replace('^TERRA_Smoke_','^TERRA_Cohort_').replace(
            "if ([string]::IsNullOrWhiteSpace($payload.owner_tag)) { throw 'Missing ownership tag' }",
            "if ($payload.owner_tag -notmatch '^TERRA_COHORT_[A-Za-z0-9_-]{8,80}$') { throw 'Invalid cohort ownership tag' }")
        self.assertEqual(changed,expected)

    def test_complete_phase_reader_ignores_partial_tail(self):
        self.evaluate(r'''
$path=Join-Path $root 'phases.jsonl'
[IO.File]::WriteAllText($path,"{`"phase`":`"SETUP`"}`n{`"phase`":`"COPY`"}")
if ((Read-CompletePhase $path 'SETUP') -cne 'SETUP') {throw 'Partial tail admitted'}
[IO.File]::AppendAllText($path,"`n")
if ((Read-CompletePhase $path 'SETUP') -cne 'COPY') {throw 'Completed record missed'}
$caught=$false; try {Read-CompletePhase $path 'CHILD'} catch {$caught=$true}
if (-not $caught) {throw 'Backwards phase accepted'}
''')


if __name__=='__main__':unittest.main()
