# Approved filesystem-only inventory. Never connects databases or loads models.
$ErrorActionPreference='Stop'
$terraTargets=@{
    store='F:\TERRA -Copy\dataset_20k_cap\vector_db_20k'
    cache='C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2'
}
$terraEvidence='F:\TERRA -Copy\reports\read_only_inventory_' + [guid]::NewGuid().ToString('N')
New-Item -ItemType Directory -Path $terraEvidence -ErrorAction Stop | Out-Null
$terraResult=@{ outcome='FAILED'; errors=@(); before=@{}; after=@{}; evidence_dir=$terraEvidence; started_utc=[DateTime]::UtcNow.ToString('o'); scope='Filesystem bytes only; no database/model/network operations' }
function Assert-NoReparse([string]$terraPath) {
    $terraWalk=[IO.Path]::GetFullPath($terraPath)
    while($terraWalk) {
        $terraItem=Get-Item -LiteralPath $terraWalk -Force -ErrorAction Stop
        if($terraItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point rejected: $terraWalk" }
        $terraWalk=[IO.Path]::GetDirectoryName($terraWalk)
    }
}
function Get-Inventory([string]$terraRoot, [bool]$terraStore) {
    Assert-NoReparse $terraRoot
    if(-not (Get-Item -LiteralPath $terraRoot).PSIsContainer) { throw "Not a directory: $terraRoot" }
    $terraDirectories=[Collections.Generic.List[string]]::new()
    $terraFiles=[Collections.Generic.List[object]]::new()
    $terraQueue=[Collections.Generic.Queue[string]]::new()
    $terraQueue.Enqueue($terraRoot)
    while($terraQueue.Count -gt 0) {
        $terraDir=$terraQueue.Dequeue()
        Assert-NoReparse $terraDir
        $terraDirectories.Add($terraDir.Substring($terraRoot.Length).TrimStart('\').Replace('\','/'))
        foreach($terraEntry in (Get-ChildItem -LiteralPath $terraDir -Force -ErrorAction Stop)) {
            if($terraEntry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse entry rejected: $($terraEntry.FullName)" }
            if($terraEntry.PSIsContainer) { $terraQueue.Enqueue($terraEntry.FullName); continue }
            if($terraStore -and $terraEntry.Name -match '(?i)(-wal|-shm|-journal|\.wal|\.lock|\.lck)$') { throw "Store journal/lock entry present: $($terraEntry.FullName)" }
            $terraLength=$terraEntry.Length
            $terraMtime=$terraEntry.LastWriteTimeUtc.Ticks
            $terraHash=(Get-FileHash -LiteralPath $terraEntry.FullName -Algorithm SHA256 -ErrorAction Stop).Hash.ToLower()
            $terraFresh=Get-Item -LiteralPath $terraEntry.FullName -Force -ErrorAction Stop
            if($terraFresh.Length -ne $terraLength -or $terraFresh.LastWriteTimeUtc.Ticks -ne $terraMtime) { throw "File changed during hash: $($terraEntry.FullName)" }
            $terraFiles.Add([pscustomobject]@{ relative_path=$terraEntry.FullName.Substring($terraRoot.Length+1).Replace('\','/'); absolute_path=$terraEntry.FullName; size_bytes=$terraLength; sha256=$terraHash; last_write_utc_ticks=$terraMtime })
        }
    }
    return @{ root=$terraRoot; directories=@($terraDirectories | Sort-Object); files=@($terraFiles | Sort-Object relative_path) }
}
try {
    foreach($terraLabel in @('store','cache')) { $terraResult.before[$terraLabel]=Get-Inventory $terraTargets[$terraLabel] ($terraLabel -eq 'store') }
    foreach($terraLabel in @('store','cache')) { $terraResult.after[$terraLabel]=Get-Inventory $terraTargets[$terraLabel] ($terraLabel -eq 'store') }
    foreach($terraLabel in @('store','cache')) {
        $terraA=$terraResult.before[$terraLabel] | ConvertTo-Json -Depth 8 -Compress
        $terraB=$terraResult.after[$terraLabel] | ConvertTo-Json -Depth 8 -Compress
        if($terraA -ne $terraB) { throw "Inventory drift detected: $terraLabel" }
    }
    $terraResult.outcome='STABLE_FILESYSTEM_INVENTORY'
} catch { $terraResult.errors += $_.Exception.Message }
$terraResult['finished_utc']=[DateTime]::UtcNow.ToString('o')
$terraCode=if($terraResult.outcome -eq 'STABLE_FILESYSTEM_INVENTORY'){0}else{1}
$terraResult['exit_code']=$terraCode
try {
    $terraWriter=[IO.StreamWriter]::new([IO.File]::Open((Join-Path $terraEvidence 'inventory.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None),[Text.UTF8Encoding]::new($false))
    try { $terraWriter.Write(($terraResult | ConvertTo-Json -Depth 8)) } finally { $terraWriter.Dispose() }
    $terraWriter=[IO.StreamWriter]::new([IO.File]::Open((Join-Path $terraEvidence 'exit_code.txt'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None))
    try { $terraWriter.Write([string]$terraCode) } finally { $terraWriter.Dispose() }
} catch { Write-Error "Evidence write failed: $_"; exit 1 }
Write-Output "EVIDENCE=$terraEvidence"
Write-Output "OUTCOME=$($terraResult.outcome) EXIT=$terraCode"
Write-Output ($terraResult.errors -join '; ')
foreach($terraLabel in @('store','cache')) { if($terraResult.before.ContainsKey($terraLabel)) { Write-Output "$terraLabel FILES=$($terraResult.before[$terraLabel].files.Count) BYTES=$(($terraResult.before[$terraLabel].files | Measure-Object size_bytes -Sum).Sum)" } }
exit $terraCode
