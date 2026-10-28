# STEP 7 — Validação automatizada (logs reais em `06_REPORTS`)

Data: 2026-10-28 10:16:52. Gerado por `05_SCRIPTS\step7_validate.py` (148 s).

## Resumo

- **Falhas persistentes**: nenhuma
- Nota: 1 referências sem MPN na BOM (PROVISÓRIO — ver STEP4/R3v2)

## 1. ERC (`hybrid_ERC_step7.json`)

- Erros: **0** · Avisos: 373
  - warning/endpoint_off_grid: 145
  - warning/lib_symbol_issues: 6
  - warning/lib_symbol_mismatch: 185
  - warning/pin_to_pin: 37

## 2. DRC (`hybrid_DRC_step7.json`) vs baseline (`baseline_DRC.json`)

- Itens não ligados: **0** · clearance: **0** · curtos: **0** · courtyards_overlap: 0 (baseline 1) · track_width: 0

| Tipo | Híbrida | Baseline |
|---|---|---|
| copper_edge_clearance | 0 | 3 |
| courtyards_overlap | 0 | 1 |
| drill_out_of_range | 0 | 1 |
| footprint_type_mismatch | 0 | 11 |
| hole_clearance | 8 | 8 |
| isolated_copper | 0 | 1 |
| lib_footprint_mismatch | 73 | 67 |
| silk_edge_clearance | 4 | 4 |
| silk_over_copper | 1 | 0 |
| silk_overlap | 4 | 3 |
| starved_thermal | 0 | 13 |
| text_height | 45 | 82 |

Violações cuja assinatura (tipo + itens) **não existe no baseline**: 19
- lib_footprint_mismatch [warning]: Footprint 'SOT95P230X110-3N' does not match copy in library 'BlackPanda' — Footprint D7
- lib_footprint_mismatch [warning]: Footprint 'SOT95P230X110-3N' does not match copy in library 'BlackPanda' — Footprint D9
- lib_footprint_mismatch [warning]: Footprint 'SOT23-3' does not match copy in library 'BlackPanda' — Footprint Q1
- lib_footprint_mismatch [warning]: Footprint 'SOT95P230X110-3N' does not match copy in library 'BlackPanda' — Footprint D5
- lib_footprint_mismatch [warning]: Footprint 'SOT95P230X110-3N' does not match copy in library 'BlackPanda' — Footprint D6
- lib_footprint_mismatch [warning]: Footprint 'SOT23-3' does not match copy in library 'BlackPanda' — Footprint Q2
- lib_footprint_mismatch [warning]: Footprint 'SOT95P230X110-3N' does not match copy in library 'BlackPanda' — Footprint D8
- lib_footprint_mismatch [warning]: Footprint 'LED-ARRAY-SMD_4P-L2.2-W2.1-BR' does not match copy in library 'BlackPanda' — Footprint U5
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID2
- lib_footprint_mismatch [warning]: Footprint 'IND-SMD_L7.3-W6.8' does not match copy in library 'BlackPanda' — Footprint L3
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID3
- lib_footprint_mismatch [warning]: Footprint 'DIOM4325X250N' does not match copy in library 'BlackPanda' — Footprint D1
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID1
- lib_footprint_mismatch [warning]: Footprint 'USB-C-SMD_TYPE-C-USB-20' does not match copy in library 'BlackPanda' — Footprint P1
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID4
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID6
- lib_footprint_mismatch [warning]: Footprint 'Fiducial_1mm_Mask2mm' does not match copy in library 'Fiducial' — Footprint FID5
- silk_over_copper [warning]: Silkscreen clipped by solder mask — Segment of P1 on F.Silkscreen <> Pad 1 [GND] of R1 on F.Cu
- silk_overlap [warning]: Silkscreen clearance — Reference field of C23 <> Segment of Y1 on B.Silkscreen

Nota: quase todas as 'novas' são do mesmo tipo das herdadas (text_height/lib_footprint_mismatch/silk) com itens renomeados (U7, C38–C63, R28–R33, J1, L5, D13/D14, FB1) ou deslocados pela placa +5 mm; as de cobre relevantes estão discutidas em `STEP5_layout_H725.md` §7.

## 3. Netlist esquemático × PCB

- Componentes no esquemático: 119 · footprints no PCB: 119 · só no esquemático: — · só no PCB: —
- Pads comparados: 481 · **redes divergentes: 0** · footprints divergentes: 0 · valores divergentes: 0
- Pinos/pads sem correspondência (informativo, ex.: pinos NC do símbolo ou pads mecânicos): 1

## 4. BOM × esquemático × PCB (`hybrid_BOM.csv`)

- Referências na BOM: 119 · DNP no esquemático (excluídos): — · só na BOM: — · no esquemático e fora da BOM: —
- Valores BOM≠sch: 0 · footprints BOM≠pcb: 0 · **sem MPN (PROVISÓRIO)**: 1 → JP1

## 5. Paridade firmware × hardware (`06_REPORTS\parity_red_h7_hybrid_HybridPanda_netlist.md`)

- Código de saída: 0 · estados: {'OK': 36} · **PIN_PARITY_CONFLICT: 0**

## 6. Skew / comprimentos / impedância

- Ver `03_RESEARCH\STEP6_roteamento_impedancia.md` e `06_REPORTS\step6_reports.json` (gerados por `step6_reports.py`). **O DRC do KiCad não verifica impedância**; os valores são estimativas analíticas (Hammerstad–Jensen) sobre o stackup declarado, não medidos.

## 7. Manifestos

- `Make-Manifest.ps1 -Step STEP7 -Original` exit 0:
  - OUTPUT_ROOT manifest: 20789 files -> C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\00_MANIFESTS\OUTPUT_ROOT_STEP7_20261028_1017.sha256
  - 02_REFERENCE unchanged vs reference_clones.sha256: False
  - ORIGINAL vs BEFORE: IDENTICAL (377 files)
  - INDEX.md rows: 14938

## 8. Comandos executados

| Comando | Exit | s | Log |
|---|---|---|---|
| `C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe sch erc --format json --severity-all -o C:\Users\costabr\Downloads\openpilot\HybridPanda_v2` | 0 | 3.9 | step7_erc.log |
| `C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe pcb drc --format json --severity-all --units mm -o C:\Users\costabr\Downloads\openpilot\Hyb` | 0 | 5.6 | step7_drc.log |
| `C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe sch export netlist --format kicadxml -o C:\Users\costabr\Downloads\openpilot\HybridPanda_v2` | 0 | 0.7 | step7_netlist.log |
| `C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe sch export bom --fields Reference,Value,Footprint,${QUANTITY},${DNP},MPN,Manufacturer,Datas` | 0 | 0.7 | step7_bom.log |
| `C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\05_SCRIPTS\.venv\Scripts\python.exe C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_202610` | 0 | 0.4 | step7_parity.log |
| `powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\05_SCRIPTS\Make-Manifest.ps1 -Step STEP7 -` | 0 | 136.3 | step7_manifest.log |
