# Parser and extracted function definitions only. Never invokes wrapper main.
$ErrorActionPreference='Stop'
$root='F:\TERRA -Copy'
$out=Join-Path $root 'reports\profile_user_b001_freeze_20261023_01'
$tokens=$null; $parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'scripts\matched_baseline\launch_offline_smoke_user.ps1'),[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -ne 0) { throw 'Wrapper parse failure' }
$definitions=$ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false)
foreach ($definition in $definitions) { . ([scriptblock]::Create($definition.Extent.Text)) }
$record=Get-Content -LiteralPath (Join-Path $out 'launch_record.json') -Raw | ConvertFrom-Json
$packet=Read-PinnedJson $record.packet 8388608
Assert-LaunchCoverage $record $packet
foreach ($spec in @($record.packet,$record.authorization,$record.entry_anchor)) { Assert-Identity $spec }
$zone=@(Get-Item -LiteralPath (Join-Path $root 'scripts\matched_baseline\launch_offline_smoke_user.ps1') -Stream Zone.Identifier -ErrorAction SilentlyContinue)
if ($zone.Count -ne 0) { throw 'Launcher has Zone.Identifier; stop without policy bypass' }
$result=@{launcher_zone_identifier_present=$false;policy_changed=$false;status='PS51_PARSE_AND_EXTRACTED_COVERAGE_PASS';main_invoked=$false;firewall_operations=$false;function_count=@($definitions).Count;version=$PSVersionTable.PSVersion.ToString()}
Write-NewJson (Join-Path $out 'wrapper_validation.json') $result
$result | ConvertTo-Json -Compress
