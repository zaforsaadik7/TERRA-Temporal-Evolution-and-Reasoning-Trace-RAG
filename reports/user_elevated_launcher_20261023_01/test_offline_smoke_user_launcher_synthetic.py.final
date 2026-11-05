"""Parse source and run extracted functions on temp fixtures only.

Never dot-source/execute the launcher, its main body, native Job APIs, or models.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'scripts/matched_baseline/launch_offline_smoke_user.ps1'
PS=Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')

@unittest.skipUnless(os.name=='nt' and PS.is_file(),'Windows PowerShell parser required')
class UserLauncherTests(unittest.TestCase):
    def evaluate(self, body, *, root):
        # ParseFile does not execute source. Only FunctionDefinitionAst nodes
        # are loaded; top-level code cannot run through this harness.
        script=r'''
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($env:SYNTHETIC_LAUNCHER_SOURCE,[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) { throw ($errors | Out-String) }
$functions=$ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false)
foreach ($function in $functions) { . ([scriptblock]::Create($function.Extent.Text)) }
$root=$env:SYNTHETIC_LAUNCHER_TMP
''' + body
        encoded=base64.b64encode(script.encode('utf-16-le')).decode()
        env=dict(os.environ,SYNTHETIC_LAUNCHER_SOURCE=str(SOURCE),SYNTHETIC_LAUNCHER_TMP=str(root))
        result=subprocess.run([str(PS),'-NoProfile','-NonInteractive','-EncodedCommand',encoded],
            capture_output=True,text=True,env=env,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        return result.stdout

    def fixture(self,root):
        assets=root/'assets'; assets.mkdir()
        asset=assets/'sample.bin'; asset.write_bytes(b'fixture')
        row={'path':str(asset),'size_bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest()}
        path=root/'members.json'; raw=json.dumps([row]).encode(); path.write_bytes(raw)
        spec={'path':str(path),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
              'members':{'roots':[str(assets)],'count':1,'complete_roots':[str(assets)]}}
        (root/'spec.json').write_text(json.dumps(spec))
        return asset,row,spec

    def test_parser_only_and_source_hold(self):
        text=SOURCE.read_text()
        self.assertIn('$LaunchAdmitted = $false',text)
        self.assertIn('$LaunchRecordPath = $null',text)
        self.assertIn('$LaunchRecordSHA256 = $null',text)
        self.assertLess(text.index('if (-not $LaunchAdmitted)'),text.index('function '))
        self.assertNotIn('-Verb RunAs',text)
        with tempfile.TemporaryDirectory() as tmp:
            self.evaluate("Write-Output 'PARSE_OK'",root=Path(tmp))

    def test_exclusive_json_collision_retains_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.evaluate(r'''
$path=Join-Path $root 'record.json'
Write-NewJson $path @{value=1}
$before=[IO.File]::ReadAllBytes($path)
$caught=$false; try { Write-NewJson $path @{value=2} } catch { $caught=$true }
if (-not $caught -or [Convert]::ToBase64String($before) -cne [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))) { throw 'Overwrite regression' }
''',root=root)

    def test_pinned_json_and_byte_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            self.evaluate(r'''
$spec=Get-Content -LiteralPath (Join-Path $root 'spec.json') -Raw | ConvertFrom-Json
$rows=@(Read-PinnedJson $spec 16777216)
if ($rows.Count -ne 1) { throw 'Decode count' }
[IO.File]::AppendAllText($spec.path,' ')
$caught=$false; try { Read-PinnedJson $spec 16777216 } catch { $caught=$true }
if (-not $caught) { throw 'Tamper not detected' }
''',root=root)

    def test_full_members_and_extra_file_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            self.evaluate(r'''
$spec=Get-Content -LiteralPath (Join-Path $root 'spec.json') -Raw | ConvertFrom-Json
Assert-MemberManifests @($spec)
[IO.File]::WriteAllText((Join-Path $root 'assets\extra.txt'),'extra')
$caught=$false; try { Assert-MemberManifests @($spec) } catch { $caught=$_.Exception.Message -match 'membership changed' }
if (-not $caught) { throw 'Unexpected file not detected' }
''',root=root)

    def test_member_tamper_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            self.evaluate(r'''
$spec=Get-Content -LiteralPath (Join-Path $root 'spec.json') -Raw | ConvertFrom-Json
[IO.File]::WriteAllText((Join-Path $root 'assets\sample.bin'),'changed')
$caught=$false; try { Assert-MemberManifests @($spec) } catch { $caught=$_.Exception.Message -match 'Identity mismatch' }
if (-not $caught) { throw 'Changed member accepted' }
''',root=root)

    def test_duplicate_member_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); _,row,spec=self.fixture(root)
            raw=json.dumps([row,row]).encode(); Path(spec['path']).write_bytes(raw)
            spec.update(size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            spec['members']['count']=2
            (root/'spec.json').write_text(json.dumps(spec))
            self.evaluate(r'''
$spec=Get-Content -LiteralPath (Join-Path $root 'spec.json') -Raw | ConvertFrom-Json
$caught=$false; try { Assert-MemberManifests @($spec) } catch { $caught=$_.Exception.Message -match 'duplicate member' }
if (-not $caught) { throw 'Duplicate accepted' }
''',root=root)

    def test_bad_paths_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.evaluate(r'''
foreach ($path in @('relative','C:\synthetic\..\bad','C:\synthetic\file:stream')) {
    $caught=$false; try { Get-CanonicalPath $path } catch { $caught=$true }
    if (-not $caught) { throw 'Unsafe path accepted' }
}
''',root=Path(tmp))

    def test_unknown_fields_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.evaluate(r'''
$caught=$false
try { Assert-ExactFields ([pscustomobject]@{known=1;unknown=2}) @('known') } catch { $caught=$true }
if (-not $caught) { throw 'Unknown field accepted' }
''',root=Path(tmp))

    def test_outer_coverage_matches_packet_and_rejects_missing_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); _,row,spec=self.fixture(root)
            (root/'packet.json').write_text(json.dumps({'declared_files':{'store':spec,'driver':row}}))
            (root/'outer.json').write_text(json.dumps({'bootstrap_files':[row],'member_manifests':[spec]}))
            self.evaluate(r'''
$packet=Get-Content -LiteralPath (Join-Path $root 'packet.json') -Raw | ConvertFrom-Json
$outer=Get-Content -LiteralPath (Join-Path $root 'outer.json') -Raw | ConvertFrom-Json
Assert-LaunchCoverage $outer $packet
$outer.bootstrap_files=@()
$caught=$false; try { Assert-LaunchCoverage $outer $packet } catch { $caught=$_.Exception.Message -match 'bootstrap coverage' }
if (-not $caught) { throw 'Missing bootstrap accepted' }
''',root=root)

    def test_outer_manifest_scope_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); _,row,spec=self.fixture(root)
            (root/'packet.json').write_text(json.dumps({'declared_files':{'store':spec,'driver':row}}))
            spec['members']['complete_roots']=[]
            (root/'outer.json').write_text(json.dumps({'bootstrap_files':[row],'member_manifests':[spec]}))
            self.evaluate(r'''
$packet=Get-Content -LiteralPath (Join-Path $root 'packet.json') -Raw | ConvertFrom-Json
$outer=Get-Content -LiteralPath (Join-Path $root 'outer.json') -Raw | ConvertFrom-Json
$caught=$false; try { Assert-LaunchCoverage $outer $packet } catch { $caught=$_.Exception.Message -match 'differs from packet' }
if (-not $caught) { throw 'Changed scope accepted' }
''',root=root)

if __name__=='__main__': unittest.main()
