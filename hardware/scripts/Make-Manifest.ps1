<#
.SYNOPSIS
  Make-Manifest.ps1 - SHA-256 manifests and INDEX.md for HybridPanda_v2 (prompt 0x00 §4-6, Diretriz 3).
.PARAMETER Step   Step label written into the manifest/INDEX (e.g. STEP1).
.PARAMETER Original  Also (re)hash ORIGINAL_ROOT and compare with original_BEFORE.sha256.
.PARAMETER DryRun  Print what would be written, write nothing.
  All outputs go to 00_MANIFESTS and INDEX.md inside OUTPUT_ROOT only.
#>
param([string]$Step = "STEP0", [switch]$Original, [switch]$DryRun)
$ErrorActionPreference = "Stop"
# ---- constants
$OUTPUT_ROOT   = "C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616"
$ORIGINAL_ROOT = "C:\Users\costabr\Downloads\openpilot\OpenpilotHardware-main\OpenpilotHardware-main"
# ----
function Assert-InsideOutput([string]$p) {
  $rp = [IO.Path]::GetFullPath($p); $out = [IO.Path]::GetFullPath($OUTPUT_ROOT); $orig = [IO.Path]::GetFullPath($ORIGINAL_ROOT)
  if ($rp.StartsWith($orig, [StringComparison]::OrdinalIgnoreCase)) { throw "REFUSED write inside ORIGINAL: $rp" }
  if (-not $rp.StartsWith($out, [StringComparison]::OrdinalIgnoreCase)) { throw "REFUSED write outside OUTPUT_ROOT: $rp" }
  return $rp
}
function Hash-Tree([string]$root, [string[]]$exclude) {
  Get-ChildItem $root -Recurse -File -Force | Where-Object { $f=$_.FullName; -not ($exclude | Where-Object { $f -like $_ }) } |
    Sort-Object FullName | ForEach-Object { "$((Get-FileHash -Algorithm SHA256 $_.FullName).Hash)  $($_.FullName.Substring($root.Length+1))" }
}
function Write-Guarded([string]$path, $content) {
  $rp = Assert-InsideOutput $path
  if ($DryRun) { Write-Host "[dry-run] would write $rp ($(@($content).Count) lines)"; return }
  if (Test-Path $rp) { $bk = Join-Path $OUTPUT_ROOT ("99_BACKUPS\" + (Get-Date -Format yyyyMMdd_HHmmss) + "_manifest\" + $rp.Substring($OUTPUT_ROOT.Length+1)); New-Item -ItemType Directory -Force (Split-Path $bk) | Out-Null; Copy-Item $rp $bk }
  $content | Set-Content -Encoding utf8 $rp
}
$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$man = Join-Path $OUTPUT_ROOT "00_MANIFESTS\OUTPUT_ROOT_${Step}_$stamp.sha256"
$lines = Hash-Tree $OUTPUT_ROOT @("*\99_BACKUPS\*", "*\.git\*", "*\.venv\*", "*\__pycache__\*")
Write-Guarded $man $lines
Write-Host "OUTPUT_ROOT manifest: $($lines.Count) files -> $man"

$refLines = Hash-Tree $OUTPUT_ROOT @("*\.git\*") | Where-Object { $_.Substring(66) -like "02_REFERENCE\*" }
$refBase = Join-Path $OUTPUT_ROOT "00_MANIFESTS\reference_clones.sha256"
$refDiff = (Compare-Object (Get-Content $refBase) $refLines | Measure-Object).Count
Write-Host "02_REFERENCE unchanged vs reference_clones.sha256: $($refDiff -eq 0)"

$origResult = "not checked"
if ($Original) {
  $o = Hash-Tree $ORIGINAL_ROOT @()
  $before = Get-Content (Join-Path $OUTPUT_ROOT "00_MANIFESTS\original_BEFORE.sha256")
  $d = (Compare-Object $before $o | Measure-Object).Count
  Write-Guarded (Join-Path $OUTPUT_ROOT "00_MANIFESTS\original_AFTER_${Step}_$stamp.sha256") $o
  $origResult = if ($d -eq 0 -and $before.Count -eq $o.Count) { "IDENTICAL ($($o.Count) files)" } else { "DIFFERENT ($d lines)" }
  Write-Host "ORIGINAL vs BEFORE: $origResult"
}

# INDEX.md (full regeneration: relative path, purpose from INDEX_purpose.csv if present, step, sha256)
$purpose = @{}
$pc = Join-Path $OUTPUT_ROOT "00_MANIFESTS\INDEX_purpose.csv"
if (Test-Path $pc) { Import-Csv $pc | ForEach-Object { $purpose[$_.path] = $_ } }
$idx = @("# INDEX - HybridPanda_v2", "", "OUTPUT_ROOT: ``$OUTPUT_ROOT``", "Atualizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm') ($Step). Manifesto: ``$(Split-Path $man -Leaf)``. ORIGINAL: $origResult. 02_REFERENCE inalterado: $($refDiff -eq 0).", "",
        "| Caminho relativo | Finalidade | STEP | SHA-256 (16 primeiros) |", "|---|---|---|---|")
foreach ($l in $lines) {
  $h = $l.Substring(0,64); $p = $l.Substring(66)
  if ($p -like "01_BASELINE\original_copy\*" -or $p -like "02_REFERENCE\*") { continue }
  $info = $purpose[$p]; $fin = if ($info) { $info.purpose } else { "" }; $st = if ($info) { $info.step } else { "" }
  $idx += "| $p | $fin | $st | $($h.Substring(0,16)) |"
}
$idx += ""; $idx += "Pastas agregadas (nao listadas arquivo a arquivo): ``01_BASELINE\original_copy`` ($((Get-ChildItem (Join-Path $OUTPUT_ROOT '01_BASELINE\original_copy') -Recurse -File -Force).Count) arquivos, = original, ver ``00_MANIFESTS\baseline_copy.sha256``); ``02_REFERENCE`` (panda + opendbc, ver ``00_MANIFESTS\reference_clones.sha256``)."
Write-Guarded (Join-Path $OUTPUT_ROOT "INDEX.md") $idx
Write-Host "INDEX.md rows: $($idx.Count - 8)"
