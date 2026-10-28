# step4_verify.ps1 - rebuild schematic from pristine baseline, export netlist, ERC, parity (red_h7), selftest geometry.
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$py  = Join-Path $root '05_SCRIPTS\.venv\Scripts\python.exe'
$cli = 'C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe'
$sch = '04_PROJECT\HybridPanda\HybridPanda.kicad_sch'

& $py 05_SCRIPTS\step4_build_schematic.py | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { throw "build failed" }
& $cli sch export netlist --format kicadxml -o 06_REPORTS\hybrid_HybridPanda_netlist.xml $sch | Out-Null
& $cli sch erc --format json --severity-all -o 06_REPORTS\hybrid_ERC.json $sch | Select-Object -Last 1
& $py -c @"
import json,collections; d=json.load(open('06_REPORTS/hybrid_ERC.json',encoding='utf-8'))
v=d['sheets'][0]['violations']; c=collections.Counter((x['severity'],x['type']) for x in v); print(dict(c))
err=[x for x in v if x['severity']=='error']
for x in err: print('ERC ERROR', x['type'], x['description'][:100], [i.get('description','')[:60] for i in x['items']])
print('ERC errors =', len(err))
"@
& $py 05_SCRIPTS\sch_geom.py $sch | Select-Object -First 1
& $py 05_SCRIPTS\parity_check.py --netlist 06_REPORTS\hybrid_HybridPanda_netlist.xml --profile red_h7 | Select-String 'CAN group|Resultado'
Write-Host "parity exit = $LASTEXITCODE"
Select-String -Path 06_REPORTS\parity_red_h7_hybrid_HybridPanda_netlist.md -Pattern 'Resultado' | ForEach-Object Line
