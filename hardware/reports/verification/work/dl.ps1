param([string[]]$pairs)
# usage: .\dl.ps1 "name.pdf=https://url" "name2.pdf=https://url2"
Set-Location $PSScriptRoot
foreach ($p in $pairs) {
  $name, $url = $p -split "=", 2
  $out = Join-Path "ds" $name
  $ok = $false
  foreach ($try in 1..2) {
    if ($ok) { break }
    try {
      $r = Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -TimeoutSec 90 -Proxy "http://proxy.cat.com:9090" -ProxyUseDefaultCredentials -Headers @{"User-Agent"="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"} -PassThru
      "$name -> $($r.StatusCode) $($r.Headers['Content-Type']) $((Get-Item $out).Length)"
      $ok = $true
    } catch {
      $m = $_.Exception.Message
      "$name try $try -> ERR $($m.Substring(0,[Math]::Min(70,$m.Length)))"
      Start-Sleep 2
    }
  }
}
