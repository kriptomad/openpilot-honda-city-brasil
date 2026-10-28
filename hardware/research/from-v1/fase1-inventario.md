# FASE 1 — Inventário e baseline do projeto original (somente leitura)

Data: 2026-10-22. Ferramentas: KiCad 10.0.7 / kicad-cli 10.0.7 (`C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin`), Python 3.13.9, pcbnew (python do KiCad 3.11.5).

## 1.1 Identificação do projeto

| Item | Resultado | Evidência |
|---|---|---|
| Caminho original | `C:\Users\costabr\Downloads\openpilot\OpenpilotHardware-main\OpenpilotHardware-main` | existe, 342 arquivos |
| O que é | Coleção **OpenpilotHardware** de lukasloetkolben (clone comunitário, "não associado à comma.ai") | `README.md` raiz |
| Licença | MIT, "Copyright (c) 2023 Lukas" | `LICENSE` |
| Sub-projetos | BlackPanda, HarnessBox, J533-Harness, LegacyTeslaOBDC_PreAP, OBDPower, PSA-Harness, Uno | árvore |
| Status declarado do BlackPanda | "The device has been tested and works so far without problems." | `BlackPanda/README.md` |
| Manifesto SHA-256 inicial | `00_manifests/manifest_original_BEFORE.sha256` (342 arquivos) | gerado com Get-FileHash |

**Importante (FATO):** a pasta local NÃO é idêntica ao upstream GitHub (`lukasloetkolben/OpenpilotHardware`, clone em 2026-10-22):
- `BlackPanda.kicad_sch`: conteúdo idêntico (diff = 0 linhas; hash difere só por fim de linha CRLF/LF).
- `BlackPanda.kicad_pcb`: **re-salvo no KiCad 10** (`(version 20260206)`), 1.474.064 bytes vs 1.188.465 upstream. Histórico local KiCad (`.history/.git`): "Autosave" 2026-10-20 11:33 e "PCB Save" 2026-10-20 11:49 (-03:00).
- Arquivos extras locais: `BlackPanda.csv`, `BlackPanda2.csv/.xlsx` (BOM), `gerber/` (gerbers 4 camadas + Excellon), `untitled.kicad_pcb` (gerado pelo gerbview 10.0 — importação de gerber), `test/`.
- Logo, a fonte da verdade usada é a **cópia local**; as diferenças em relação ao upstream são edições do usuário (INFERÊNCIA pelo histórico).

## 1.2 Versão do KiCad e bibliotecas

| Arquivo | Formato | Observação |
|---|---|---|
| `BlackPanda.kicad_sch` | `version 20230121` (KiCad 7) | folha única, papel A2, símbolos embutidos em `lib_symbols` |
| `BlackPanda.kicad_pcb` | `version 20260206` (KiCad 10) | re-salvo localmente |
| `BlackPanda.kicad_pro` | KiCad 7→10 | |
| `sym-lib-table` | 7 libs locais: 4 **Legacy** (`.lib`: PESD2CAN_215, U.FL-R-SMT-1, SMAJ16CA, SMP4-RGB) + 3 `.kicad_sym` (10_0_QHHTZB6_3, FM-B1921RGBA-SH, TYPE-C-31-M-04) | todas presentes em `BlackPanda.symbols/` |
| `fp-lib-table` | 1 lib local `BlackPanda` → `BlackPanda.pretty` (10 footprints) | demais footprints vêm das libs padrão do KiCad |
| Modelos 3D | `BlackPanda.3d/` (12 arquivos .step/.wrl) | |

Bibliotecas ausentes: nenhuma lib referenciada está ausente. Porém ERC aponta 141 `lib_symbol_mismatch` e 6 `lib_symbol_issues` (símbolos embutidos divergem das libs KiCad 10 atuais) e DRC aponta 67 `lib_footprint_mismatch` — divergência de versão de biblioteca, não arquivos faltando.

## 1.3 Blocos funcionais (lidos da netlist exportada: `02_analysis/original_netlist.xml`)

Componentes principais (86 footprints, 106 nets):

| Ref | Função | Peça |
|---|---|---|
| U7 | MCU | **STM32F413RGTx**, LQFP-64 (bxCAN clássico, 3 controladores CAN) |
| U8, U9, U10, U11 | Transceivers CAN | TJA1042TK-3 (DFN8), VIO=3V3, VCC=5V |
| D6, D7, D8, D9 | ESD CAN | PESD2CAN,215 (SOT-23) um por barramento |
| D5 | ESD SBU1/SBU2 | PESD2CAN,215 |
| P1 | Conector do chicote (estilo USB-C 16 pinos) | TYPE-C-31-M-04 |
| D1 | TVS entrada 12 V | SMAJ16CA-13-F |
| Q4 + D2 + R1 | Proteção inversão de polaridade (P-MOSFET + zener gate) | HY12P03C2, BAS40WS, 1 kΩ |
| U6 + L4 + D12 + C37 + R5/R6 | Buck 12 V→5 V | TPS5450DDAR, 15 µH, SM540C, 10 nF, 10 k/3,16 k |
| U12 + L3 + D11 | Buck 5 V→3,3 V | XL1509-3.3, 47 µH, B320AE |
| U1 + R9/R26/R27 + D10 | Chave de carga USB-A 5 V | AP22615AWU-7, BAS70H |
| U3 + R20/R21 | USB-A (saída para o dispositivo host), 22 Ω série | 10.0QHHTZB6.3 |
| Q1, Q2 | Drivers do relé do chicote (PNP digital, emissor +5 V) | DDTA143ECA-7 |
| R23, R24 | Pull-up 10 k SBU1/SBU2 → 3V3 | |
| Q3 | Controle da chave de carga USB (NPN digital) | PDTC114EU |
| Y1 + C23/C24 | Cristal 8 MHz? (**valor não indicado no esquemático; NÃO VERIFICADO**) 3225, 10 pF | X322516MLB4SI → 16 MHz (INFERÊNCIA pelo MPN) |
| U4 + ANT1 + L1 + C15 + R10 + U2 + C9 | GPS u-blox NEO-M8M + U.FL + chave de carga SiP32431 | |
| U5 + R17/R18/R19 | LED RGB ânodo comum | FM-B1921RGBA-SH, 180/110/100 Ω |
| SW1 + R14 | Botão BOOT0 (DFU) + pull-down 10 k | |
| R2/R3 | Divisor 12V_Protected → VoltageSens (1 k / 10 k → ×11) | |
| R15/R16 | Divisor +5 V → PC4 (sensor 5 V OUT) | |
| R22 | Pull-down PB2 (BOOT1) | |

Árvore de alimentação: `+12V` (P1 A4/A9/B4/B9) → D1 TVS → Q4 (P-FET) → `12V_Protected` → U6 TPS5450 → `+5V` → U12 XL1509 → `+3V3`. `+5V` → U1 AP22615 → `USB_PWR` → USB-A VBUS. Transceivers: VCC=+5V, VIO=+3V3. Relé do chicote: +5 V via Q1/Q2 para SBU1/SBU2.

Debug: **não há header SWD** (PA13/PA14 não conectados); gravação só por DFU USB (BOOT0). UART (PA2/PA3) e SPI (PA4–PA7) só como labels sem destino.

## 1.4 Pinout do MCU original (F413) — extraído da netlist

Ver `02_analysis/original_mcu_pinout.txt` (gerado). Mapeamento CAN relevante:

| Net do esquemático | Pinos F413 | Periférico F413 | Transceiver | Pinos de P1 | Barramento panda |
|---|---|---|---|---|---|
| CAN2_RX/TX | PB8/PB9 | **CAN1** | U11 | B10 (L), B11 (H) | bus 0 |
| CAN1_RX/TX | PB12/PB13 | **CAN2** | U8 | A3 (L), A2 (H) | bus 1 |
| CAN0_RX/TX | PA8/PA15 | **CAN3** | U9 | A10 (L), A11 (H) | bus 2 |
| CAN3_RX/TX | PB5/PB6 | **CAN2 (pinos alternativos)** | U10 | B3 (L), B2 (H) | OBD (multiplexado com bus 1 — `CAN_MODE_OBD_CAN2`) |
| CANx_EN (STB) | PC1 (U11), PB10 (U8), PA0 (U9), PC13 (U10) | GPIO | | | |
| SBU1 / SBU2 | PC0 / PC3 (ADC) | | | A8 / B8 | detecção de orientação do chicote |
| relay_SBU1 / relay_SBU2 | PC10 / PC11 | | Q2 / Q1 | | relé do chicote |
| VoltageSens | PC2 (ADC) | | | | |
| USB D-/D+ | PA11/PA12 | OTG_FS | | | |

Nota: a numeração "CAN0..3" nos nomes de rede do autor do clone **não** corresponde à numeração de barramento do firmware; a correspondência acima segue o periférico do F413 (fato pela netlist) e o `board/boards/black.h` histórico do panda (INFERÊNCIA — black.h já foi removido do master atual).

## 1.5 PCB: dimensões, stackup e regras (de `original_pcb_facts.json`)

| Item | Valor |
|---|---|
| Contorno (bbox) | 47,625 × 41,750 mm (origem x=91,91, y=32,01) |
| Camadas de cobre | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) — stackup detalhado não definido no arquivo (padrão KiCad) |
| Espessura | 1,59 mm |
| Regras | clearance mín. 0,05 mm; trilha mín. 0,1375 mm; via mín. 0,4 mm; anel mín. 0,05 mm; furo mín. 0,3 mm; furo-furo 0,25 mm; cobre-borda 0,2 mm |
| Netclass Default | clearance 0,1; trilha 0,2; via 0,6/0,3 |
| Netclass USB | clearance 0,05; trilha 0,05 (!); via 0,45/0,25; par dif. 0,2 / gap 0,25 |
| Larguras usadas | 0,15 (102 seg.), 0,175 (68), 0,2 (461), 0,35–2,0 mm (potência) |
| Vias | 155× 0,6/0,3 mm; 1× 0,45/0,25 mm |
| Furos | PTH: 8× 0,3; 12× 0,4; 4× 0,6×1,2 (oblongo); 2× 0,7×2,5 (oblongo, USB-A); NPTH: 2× 0,8 (USB-A). **Nenhum furo de fixação** da placa — fixação pela caixa (STLs) |
| Zonas | GND F.Cu; +5V/+3V3 em In1; +5V em In2/B.Cu; +12V e 12V_Protected em B.Cu |
| Componentes | 86 (85 em F.Cu, 1 em B.Cu) |

## 1.6 Baseline ERC/DRC (cópia, KiCad 10.0.7)

ERC (`baseline_ERC_original.rpt`): **7 erros, 319 avisos** — endpoint_off_grid 136, lib_symbol_mismatch 141, pin_to_pin 30, power_pin_not_driven 7 (erros), isolated_pin_label 6, lib_symbol_issues 6.

DRC (`baseline_DRC_original.rpt`, com paridade com esquemático): **194 violações, 0 pads desconectados, 79 erros de footprint** — text_height 82, footprint_symbol_field_mismatch 78, lib_footprint_mismatch 67, starved_thermal 13, footprint_type_mismatch 11, hole_clearance 8, silk_edge_clearance 4, copper_edge_clearance 3, silk_overlap 3, courtyards_overlap 1, drill_out_of_range 1, isolated_copper 1, footprint_symbol_mismatch 1.

Interpretação: a maioria é divergência de biblioteca/versão e texto; as 8 `hole_clearance`, 3 `copper_edge_clearance` e 1 `drill_out_of_range` são físicas e devem ser revistas no derivado.

## 1.7 BOM × esquemático × PCB

- BOM do autor (`BlackPanda.csv`, `BlackPanda2.csv/.xlsx`) vs BOM exportada do esquemático (`original_bom_from_sch.csv`): comparação em `02_analysis/bom_crosscheck.md` (gerado adiante).
- Valor do cristal Y1 não consta no esquemático (MPN X322516MLB4SI sugere 16 MHz — a verificar).

## 1.8 Não lido / não interpretado

- `fp-info-cache` (3,2 MB, cache do KiCad) — irrelevante.
- `untitled.kicad_pcb` (3,6 MB, gerado pelo gerbview a partir de gerber) — não é projeto editável; ignorado.
- Arquivos `.xlsx` da pasta `Downloads\openpilot` fora do caminho original (cotação LCSC, pick-and-place) — não fazem parte da fonte da verdade; não lidos.
- Imagens `docs/*.png` e `docs/BlackPanda.pdf` — não inspecionados visualmente (sem necessidade; netlist é a fonte).
