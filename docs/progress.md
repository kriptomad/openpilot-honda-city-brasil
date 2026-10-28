# PROGRESS.md — checkpoint de retomada (ler PRIMEIRO ao retomar)

## >>> COMANDO "retomar" — procedimento obrigatório (ordem fixa) <<<
1. Ler integralmente `08_DOCS\PROTOCOLO_v3_COMPLETO.md` (protocolo vigente, texto do usuário), depois este PROGRESS.md, `03_RESEARCH\DECISIONS.md` e `INDEX.md` (se existir).
2. **Rebaixar (re-clonar) TODO o ecossistema commaai em `02_REFERENCE`** para ter fonte de consulta real de firmware, hardware, software e tudo:
   - `commaai/panda` (firmware + python host lib), `commaai/opendbc`, `commaai/openpilot` — clone **completo** (não depth-1; o depth-1 de 2026-10-22 falhou no checkout: "and retry with 'git restore --source=HEAD :/'", commit 8d10a9de, 972 arquivos — tratar `02_REFERENCE\openpilot` como INCOMPLETO: mover para `99_BACKUPS\openpilot_INCOMPLETO_20261022` e reclonar).
   - Buscar na organização commaai (`gh repo list commaai --limit 200`) qualquer repo de hardware/esquemático/harness/case/ferramentas (ex.: comma hardware, harness, panda_jungle, cereal, msgq, body, etc.) e clonar os relevantes; registrar os que existem e os que NÃO existem (ex.: hardware red panda publicado ou não).
   - Para cada clone: hash de commit, data, licença → `08_DOCS\LICENSES_*.md` e `00_MANIFESTS\reference_clones.sha256` regenerado; marcar somente leitura.
   - Verificar que `panda` e `opendbc` já clonados (408e14d4 / c3955753) continuam íntegros antes de decidir reclonar; se íntegros, manter e registrar.
3. Registrar toolchain (já verificado 2026-10-22): arm-none-eabi-gcc, scons, gcc, make, freerouting = NÃO ENCONTRADOS; java 8 presente; python3 presente → compilação de prova = **BLOQUEADO** (anotar em STEP 2; avaliar instalar toolchain em pasta de usuário sem tocar no sistema, se permitido).
4. Continuar os STEPs do protocolo v3 a partir do estado abaixo, sem PROCEED, "numa paulada só".

## Decisão futura registrada (NÃO decidir agora; manter em aberto)
- **Plataforma host do openpilot**: (a) smartphone/dispositivo externo via USB, ou (b) rodar "igual o comma 4" — dispositivo dedicado com tela, computação e sensores integrados no próprio aparelho. Ao retomar, levantar no clone do openpilot o que o host precisa (system/hardware, pandad, tici/comma four hardware layer, requisitos de câmera/IMU/GPS/tela) para subsidiar essa decisão. Registrar como D-06 PENDENTE em DECISIONS.md.


Última gravação: 2026-10-26 (STEP 5–9 concluídos; relatório final em `08_DOCS\RELATORIO_FINAL.md`).

## Raiz efetiva
`C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616` (ver DECISIONS.md D-01).

## Protocolo vigente
Prompt v3 em `C:\Users\costabr\.copilot\session-state\02e7dc71-63e5-4225-8c5e-968f5dc2b80b\files\paste-1792698578287.txt`
(STEP 1–9, MODO AUTÔNOMO, sem PROCEED, HRS, matriz de cobertura, tabela híbrida, verificador de paridade, DECISIONS.md, PROGRESS.md).
Prompt v2 (paste-1792696307624.txt) e prompt v1 continuam válidos onde não conflitam. Usuário: "vai numa paulada só".

## Decisões fixas do usuário
- MCU = **STM32H725** (D1). Encapsulamento escolhido por evidência: **LQFP144 (STM32H725ZGT6)** — ver DECISIONS.md D-02.
- Manter formato/conectores do Black Panda se possível; PCB nova do zero aceitável.

## Estado por STEP (protocolo v3)
| STEP | Estado | Observações |
|---|---|---|
| 1 Ambiente/base | FEITO (falta registrar toolchain ARM) | manifestos BEFORE (377), baseline copy, ERC/DRC baseline em 06_REPORTS, versões KiCad 10.0.7 / py 3.11.5 emb. / py 3.13.9 / git 2.55.0; kiutils 1.4.8 em 05_SCRIPTS\.venv |
| 2 Ingestão/HRS | FEITO (2026-10-23 08:42) | Clones RO em `02_REFERENCE`: panda 408e14d4, panda_full f62adf72 (+worktree panda_legacy_f4 @ f849893b = último com black.h/stm32f4), opendbc c3955753, **openpilot ff47f484 completo e limpo** (sem LFS — D-10; 6 submódulos; panda pinado a5919516 — D-11), hardware a42a4752, neo 9869dee9, panda_jungle b80539fc, harness_tester_challenge 069f7243, openpilot-docs 8a007654. Docs: `03_RESEARCH\HRS_red_panda.md` (HRS completo com file:line, §1–§10 + controle F4), `P2_hardware_red_panda.md` (commaai NÃO publica esquema do red panda), `P10_OBDC_harness_SBU.md` (pinout OBD-C oficial, harness box v3, lógica SBU, PC4=TT_ha), renders PNG em `03_RESEARCH\renders`, `08_DOCS\LICENSES.md`. Toolchain: arm-none-eabi-gcc/scons/make NÃO instalados → prova de compilação BLOQUEADA (registrar no relatório). `coverage_matrix.py` → 61/61 requisitos provados (`03_RESEARCH\coverage_matrix.md/.csv`, `06_REPORTS\coverage_matrix.json`). Manifests STEP2: 02_REFERENCE íntegro, ORIGINAL IDENTICAL (377). Pendente de baixa prioridade: consolidar P4–P9/P11 em docs separados (conteúdo já em HRS/P3/P10) e análise host openpilot para D-06 (layout novo: `openpilot\openpilot\selfdrive\pandad`, `openpilot\system\hardware`). Agente de pesquisa antigo descartado (sessão nova). |
| 3 Eng. reversa/tabela híbrida | FEITO (2026-10-23) | `03_RESEARCH\STEP3_engenharia_reversa_tabela_hibrida.md` (tabelas a–g + tabela híbrida). `05_SCRIPTS\parity_check.py` + `firmware_pins.json` (perfis red_h7/black_f4): controle black_f4 sobre `06_REPORTS\baseline_BlackPanda_netlist.xml` = 35/35 OK. D-13 (P1 mantido — cruzamento do cabo USB-C), D-14 (VDD33USB=3V3, VDD50USB→VDD33USB), D-15 (errata normal/OBD: PB5/6 normal xcvr2, PB12/13 OBD xcvr4). `05_SCRIPTS\README.md` escrito. Sem PIN_PARITY_CONFLICT. |
| 4 Esquemático | FEITO (2026-10-23) | `04_PROJECT\HybridPanda\HybridPanda.kicad_sch` gerado por `05_SCRIPTS\step4_build_schematic.py` (idempotente a partir de `HybridPanda.kicad_sch.baseline`; valores em `step4_bom_values.json`). Verificação única: `05_SCRIPTS\step4_verify.ps1` → **ERC 0 erros**, `parity_check --profile red_h7` **36/36 SEM DIVERGÊNCIA**, geometria 100 % ancorada. Relatório `03_RESEARCH\STEP4_esquematico_H725.md` (mapa 144 pinos, conectores, checklist CI, ERC, BOM 48 linhas). Pesquisa `03_RESEARCH\R3v2_componentes_STEP4.md` (TJA1042TK/3 = CAN FD 5 Mbit/s [F] → **transceivers reaproveitados**, D-20). D-16 (SBU 10k+BAT54S), D-17 (nets BUS*), D-18 (A1/posições), D-19 (VCAP/pin_map). PROVISÓRIOS: cristal CL/15 pF, indutor DFE201610E, FB1, MPNs de capacitores. Saídas: `06_REPORTS\hybrid_*.{xml,json,pdf,csv}`, `step4_roundtrip.*`, `step4_build_schematic.json`. |
| 5 PCB | FEITO (2026-10-28, campanha de correcao D-34..D-38) | Pipeline original (D-26..D-33) + correcoes pos-auditoria em passos com gate de DRC: commits a8b98a9 (footprints), a5d60b8 (VFBSMPS=VCAP, C64/C65, JP1), b209b08/eb14492 (SI/PI ALTO), 9305ef2 (BOM), 15e11dd (SI/PI MEDIO), final. Placa 50,625 x 46,75 mm + 0,4 mm a leste para y < 48,6. DRC final: **0 nao ligados, 0 clearance, 0 curtos, 135 itens** (hole_clearance 8 P1, lib_footprint_mismatch 73, silk 9, text_height 45). **Via-in-pad 0**. Tabela item->estado em `06_REPORTS\CORRECOES_APLICADAS.md`. O snapshot `.step5_final` esta obsoleto: a placa aceite e o HEAD de main. |
| 6 Roteamento/impedância | FEITO (2026-10-26) | `step6_reports.py` → `03_RESEARCH\STEP6_roteamento_impedancia.md`: impedância só analítica (εr 4,5 assumido), skew CAN 1,1–1,9 mm/0 vias, USB_D± 2,5 mm/4 vias não acoplado (risco), 1201 trilhas/204 vias, pour GND. |
| 7 Validação | FEITO (re-executado 2026-10-28) | `step7_validate.py` → `03_RESEARCH\STEP7_validacao.md`, `06_REPORTS\step7_validation.json`: ERC **0 erros**/373 avisos, DRC 0/0/0 (135 itens), netlist sch×pcb 0 divergências, paridade red_h7 **36/36 OK**, falhas: **nenhuma**. `final_audit.py`: curtos 0, via-in-pad 0, clearance 0, hole_hits 8 (P1). DRC/ERC finais: `06_REPORTS\hybrid_DRC_final.json`, `hybrid_ERC_final.json`. |
| 8 Fabricação | FEITO (regenerado 2026-10-28) — **NÃO FABRICAR** | `step8_fabricate.py` → `07_FABRICATION\` (gerbers, Excellon, PDFs, STEP, BOM_JLC.csv com LCSC em 117/119 refs — codigos "a verificar", CPL, zip, `LEIA-ME.txt`). |
| 9 Bring-up/relatório | FEITO (documental) | `03_RESEARCH\STEP9_bringup_e_teste_veiculo.md` (bancada 19 passos, DFU, captura passiva no City); `08_DOCS\RELATORIO_FINAL.md`. Firmware não compilado (toolchain ARM ausente — BLOQUEADO); zero validação física. |

## Fatos-chave já verificados (com fonte)
- `stm32h7/clock.h:30-47`: SYSCFG->PKGR → TFBGA100 ⇒ LDO; LQFP144/UFBGA169 ⇒ **SMPSEN** ("powered only by SMPS"); pacote desconhecido ⇒ `while(true)`. Logo pacote ≥144 pinos exige H725 (SMPS) e modo **Direct SMPS**.
- KiCad lib `STM32H723VGHx` (TFBGA100): 82 GPIO, sem PF/PG ⇒ paridade impossível em TFBGA100. DS13311 Tab.8 confirma ('-' na coluna TFBGA100 para PF7–PF11, PG9–PG11).
- DS13311 §6.3.2/6.3.3: VCAP 2×2,2 µF (ESR<100 mΩ; 3º VCAP só interligado); SMPS: Cin 4,7 µF (VDDSMPS), Cfilt 220 pF (VLXSMPS), Cout 10 µF (VFBSMPS, ESR 20 mΩ), L 2,2 µH DCR 150 mΩ Isat 1,7 A Irms 1,4 A; VDDSMPS = VDD; VDDLDO 1,62–3,6 V; fsw 2,4 MHz. Componentes detalhados: AN5419 (não baixado).
- DS Tab.8: PG9 = FDCAN3_**TX**, PG10 = FDCAN3_**RX** (firmware só define AF2). USB: PA11/PA12 = OTG_HS_DM/DP (PHY FS interno). ADC: PF11=ADC1_INP2, PC4=ADC12_INP4, PA1=ADC1_INP17, PB1=ADC12_INP5.
- LQFP144 pinos sistema: VCAP 68/103/140; VDDLDO 70/105/143; VDDSMPS 16; VSSSMPS 14; VLXSMPS 15; VFBSMPS 17; VDD50USB 90; VDD33USB 91; VREF+ 35; VDDA 36; VSSA 34; VBAT 8; BOOT0 135; NRST 27; PDR_ON 142.
- OBD-C (hardware/harness/OBD-C.sch.pdf): A2/A3 CAN0, A10/A11 CAN1, B2/B3 CAN2, B10/B11 CAN3, A8 SBU1, B8 SBU2, A4/A9/B4/B9 VIN, A1/A12/B1/B12 GND. Harness box v3 tem terminação 120 Ω e relé DG419 → panda sem terminação (D-04 confirmada). PC4 = TT_ha (não 5 V) → D-12.
- HW_TYPE RED: PF7–PF10 = 0 com pull-up interno (D-08). Firmware exige Flash 1 MB → H725**Z**G**T6**.
- P1 REFUTADA: Honda City 2023 BR = `HondaBoschPlatformConfig`, BOSCH_RADARLESS, CAN clássico; harness Bosch B.

## Próximas ações imediatas ao retomar
1. Ler `08_DOCS\RELATORIO_FINAL.md` (estado consolidado, listas NÃO VERIFICADO/BLOQUEADO, to-do manual).
2. Para revalidar sem reroutear: `step7_validate.py` (≈ 1 min), `step8_fabricate.py` (≈ 2-4 min) e `final_audit.py` com o python do KiCad. **Não** correr o pipeline 5a→5e→5d: o Freerouting é não-determinista e destruiria as correções manuais da campanha D-34 (a placa aceite é o HEAD de main, não o snapshot `.step5_final`). Qualquer edição nova passa pelo gate `05_SCRIPTS\corr_gate.py drc --tag X` (0 clearance / 0 unconnected / 0 paridade, sem categoria nova) e ERC 0. Itens deferidos e razões: `06_REPORTS\CORRECOES_APLICADAS.md` §5 e D-37.
3. Pendentes manuais (ordem sugerida): (a) confirmar os códigos LCSC "a verificar" no catálogo JLC (C23/C24 C1555 vs C307443; JP1/U1 sem LCSC); (b) decidir acoplamento USB_D± (rerotear à mão em F.Cu sem vias) e confirmar stackup com o fabricante; (c) instalar arm-none-eabi-gcc + scons e compilar `panda` (DEBUG) para prova de build; (d) revisão visual de gerbers no GerbView; (e) decidir D10 (item 9) e os itens de relayout de D-37; (f) protótipo + STEP 9 em bancada **antes** de qualquer ligação ao veículo.
4. D-06 (plataforma host do openpilot) continua PENDENTE.
