$ErrorActionPreference = 'Stop'
$terraRoot = 'F:\TERRA -Copy'
$terraSource = Join-Path $terraRoot 'tmp\gated_recovery_stage_20261014_final'
$terraAssets = Join-Path $terraRoot 'assets\tokenizers'
$terraNewManifest = Join-Path $terraAssets 'gated_tokenizer_manifest.v1.sha256'
$terraEvidence = Join-Path $terraRoot ('reports\gated_admission_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $terraEvidence | Out-Null
$terraOwned = @()
$terraRecord = @{ outcome='NOT_ADMITTED'; errors=@(); evidence_dir=$terraEvidence; provenance='Local validation only; Gemma upstream receipt unresolved; provider parity unverified' }
function Assert-SafePath([string]$terraPath) {
    $terraFull = [IO.Path]::GetFullPath($terraPath)
    if (-not $terraFull.StartsWith($terraRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $terraFull" }
    $terraWalk = $terraFull
    while ($terraWalk -and $terraWalk.Length -ge $terraRoot.Length) {
        if (Test-Path -LiteralPath $terraWalk) {
            if ((Get-Item -LiteralPath $terraWalk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $terraWalk" }
        }
        $terraWalk = [IO.Path]::GetDirectoryName($terraWalk)
    }
}
function Read-PinnedManifest([string]$terraPath, [string]$terraPin, [string]$terraBase) {
    Assert-SafePath $terraPath
    if ((Get-FileHash -LiteralPath $terraPath).Hash.ToLower() -ne $terraPin) { throw "Manifest pin mismatch: $terraPath" }
    $terraMap = @{}
    foreach ($terraLine in [IO.File]::ReadAllLines($terraPath)) {
        if ($terraLine -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw 'Invalid manifest row' }
        $terraRel = $Matches[2]; $terraDigest = $Matches[1].ToLower()
        if ($terraMap.ContainsKey($terraRel)) { throw 'Duplicate manifest row' }
        $terraFile = Join-Path $terraBase $terraRel
        Assert-SafePath $terraFile
        if ((Get-FileHash -LiteralPath $terraFile).Hash.ToLower() -ne $terraDigest) { throw "File mismatch: $terraFile" }
        $terraMap[$terraRel]=$terraDigest
    }
    return $terraMap
}
try {
    foreach ($terraRole in @('generator','router')) { $terraDir=Join-Path $terraAssets $terraRole; Assert-SafePath $terraDir; if (Test-Path -LiteralPath $terraDir) { throw "Destination exists: $terraDir" } }
    Assert-SafePath $terraNewManifest
    if (Test-Path -LiteralPath $terraNewManifest) { throw 'New manifest already exists' }
    $terraPublicPath=Join-Path $terraAssets 'tokenizer_manifest.sha256'
    $terraStagePath=Join-Path $terraSource 'gated_tokenizer_manifest.sha256'
    $terraPublicPin='41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44'
    $terraStagePin='d8c29decbdfc869519e94789c8b49efb14cd172c7d36de5713eb8fac43dbabe6'
    $terraPublic=Read-PinnedManifest $terraPublicPath $terraPublicPin $terraRoot
    $terraStage=Read-PinnedManifest $terraStagePath $terraStagePin $terraSource
    if ($terraPublic.Count -ne 8 -or $terraStage.Count -ne 7) { throw 'Unexpected file counts' }
    $terraRecord['source_before']=$terraStage; $terraRecord['public_before']=$terraPublic
    foreach ($terraRole in @('generator','router')) { $terraDir=Join-Path $terraAssets $terraRole; New-Item -ItemType Directory -Path $terraDir | Out-Null; $terraOwned += $terraDir }
    $terraDestHashes=@{}
    foreach ($terraRel in ($terraStage.Keys | Sort-Object)) {
        $terraFrom=Join-Path $terraSource $terraRel; $terraTo=Join-Path $terraAssets $terraRel
        Assert-SafePath $terraFrom; Assert-SafePath $terraTo
        $terraIn=[IO.File]::OpenRead($terraFrom)
        try { $terraOut=[IO.File]::Open($terraTo,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None); try { $terraIn.CopyTo($terraOut) } finally { $terraOut.Dispose() } } finally { $terraIn.Dispose() }
        $terraHash=(Get-FileHash -LiteralPath $terraTo).Hash.ToLower()
        if ($terraHash -ne $terraStage[$terraRel]) { throw "Copy mismatch: $terraRel" }
        $terraDestHashes[$terraRel]=$terraHash
    }
    $terraRecord['source_after']=Read-PinnedManifest $terraStagePath $terraStagePin $terraSource
    $terraRecord['public_after']=Read-PinnedManifest $terraPublicPath $terraPublicPin $terraRoot
    $terraRecord['destination_hashes']=$terraDestHashes
    $terraText=(($terraStage.Keys | Sort-Object | ForEach-Object { $terraStage[$_] + '  assets/tokenizers/' + $_ }) -join "`n") + "`n"
    $terraWriter=[IO.StreamWriter]::new([IO.File]::Open($terraNewManifest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None),[Text.UTF8Encoding]::new($false))
    try { $terraWriter.Write($terraText) } finally { $terraWriter.Dispose() }
    $terraRecord['new_manifest_sha256']=(Get-FileHash -LiteralPath $terraNewManifest).Hash.ToLower()
    $terraRecord['outcome']='ADMITTED_FILES_ONLY'
} catch {
    $terraRecord['errors'] += $_.Exception.Message
    if ($terraOwned.Count -gt 0 -and -not (Test-Path -LiteralPath $terraNewManifest)) {
        try { $terraQuarantine=Join-Path $terraAssets ('.failed_admission_' + [guid]::NewGuid().ToString('N') + '_NOT_ADMITTED'); Assert-SafePath $terraQuarantine; New-Item -ItemType Directory -Path $terraQuarantine | Out-Null
            foreach ($terraDir in $terraOwned) { Assert-SafePath $terraDir; $terraTarget=Join-Path $terraQuarantine ([IO.Path]::GetFileName($terraDir)); Assert-SafePath $terraTarget; Move-Item -LiteralPath $terraDir -Destination $terraTarget }
            $terraRecord['quarantine']=$terraQuarantine
        } catch { $terraRecord['errors'] += $_.Exception.Message; $terraRecord['remaining_partial_paths']=$terraOwned }
    }
} finally {
    foreach ($terraCheck in @(@('source_final',$terraStagePath,$terraStagePin,$terraSource),@('public_final',$terraPublicPath,$terraPublicPin,$terraRoot))) {
        if ($terraCheck[1]) { try { $terraRecord[$terraCheck[0]]=Read-PinnedManifest $terraCheck[1] $terraCheck[2] $terraCheck[3] } catch { $terraRecord['errors'] += $_.Exception.Message; $terraRecord['outcome']='NOT_ADMITTED' } }
    }
    $terraLog=Join-Path $terraEvidence 'admission_record.json'
    $terraWriter=[IO.StreamWriter]::new([IO.File]::Open($terraLog,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None))
    try { $terraWriter.Write(($terraRecord | ConvertTo-Json -Depth 8)) } finally { $terraWriter.Dispose() }
}
Write-Output ($terraRecord | ConvertTo-Json -Depth 8)
if ($terraRecord.outcome -ne 'ADMITTED_FILES_ONLY') { exit 1 }
