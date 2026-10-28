# step4_verify.ps1 - rebuild schematic from pristine baseline, export netlist, ERC, parity (red_h7), selftest geometry.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path  # repository root
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$py  = Join-Path $root 'hardware\scripts\.venv\Scripts\python.exe'
$cli = 'C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe'
$sch = 'hardware\hybrid-panda\HybridPanda.kicad_sch'

& $py hardware\scripts\step4_build_schematic.py | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { throw "build failed" }
& $cli sch export netlist --format kicadxml -o hardware\reports\hybrid_HybridPanda_netlist.xml $sch | Out-Null
& $cli sch erc --format json --severity-all -o hardware\reports\hybrid_ERC.json $sch | Select-Object -Last 1
& $py -c @"
import json,collections; d=json.load(open('hardware/reports/hybrid_ERC.json',encoding='utf-8'))
v=d['sheets'][0]['violations']; c=collections.Counter((x['severity'],x['type']) for x in v); print(dict(c))
err=[x for x in v if x['severity']=='error']
for x in err: print('ERC ERROR', x['type'], x['description'][:100], [i.get('description','')[:60] for i in x['items']])
print('ERC errors =', len(err))
"@
& $py hardware\scripts\sch_geom.py $sch | Select-Object -First 1
& $py hardware\scripts\parity_check.py --netlist hardware\reports\hybrid_HybridPanda_netlist.xml --profile red_h7 | Select-String 'CAN group|Resultado'
Write-Host "parity exit = $LASTEXITCODE"
Select-String -Path hardware\reports\parity-red-h7-hybrid-hybridpanda-netlist.md -Pattern 'Resultado' | ForEach-Object Line
