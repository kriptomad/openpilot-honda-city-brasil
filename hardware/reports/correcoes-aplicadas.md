# CORRECOES APLICADAS - Hybrid Panda (campanha de correcao pos-auditoria)

Data: 2026-10-28. Placa: hardware/hybrid-panda (KiCad 10.0.7). Branch main.
Fontes de verdade: hardware/reports/si-pi-audit/proposed-changes.md (36 itens),
hardware/reports/footprint-audit/footprint-audit.md, hardware/reports/bom-real/bom-report.md.
Guia de retoma por passo: hardware/reports/corrections/resume-step3.md. Log de cada edicao do passo 5:
hardware/reports/corrections/step5_pcb.json.

Regra de aceitacao usada em TODAS as edicoes (hardware/scripts/corr_gate.py): kicad-cli DRC em JSON apos
cada edicao; aceite = 0 clearance, 0 unconnected, 0 schematic_parity e nenhuma categoria de
severidade erro nova face ao baseline (hardware/reports/corrections/drc_baseline_step7_orig.json); ERC 0 erros.
Esquema e PCB alterados em conjunto (paridade de netlist 0 divergencias).

## 1. Commits

| Commit | Passo | Conteudo |
|---|---|---|
| a8b98a9 | 1 | Auditoria de footprints: Q1/Q2/Q3 pads, U5 pads, U12 EP, anel P1, R6 R_0603, atributos SMD, 3D |
| a5d60b8 | 2 | VFBSMPS unido a VCAP, C64/C65 novos, PF9 -> JP1 (HW_TYPE) |
| b209b08 | 3 WIP | SI/PI ALTO: itens 4, 5, 8/18/19, 11; item 6 parcial |
| eb14492 | 3 | Item 6 fechado (paridade C4/C12 0805), tracks_crossing U13 corrigido, item 16 deferido |
| 9305ef2 | 4 | Impacto BOM dos passos 1-3 (3 CSV + campos MPN/LCSC no esquema) |
| 15e11dd | 5 | SI/PI MEDIO: 24, 26p, 28, 30, 31, 33a/b, 35p, 12/13/14p, 17p, 20 |
| (final) | final | Item 15 (5 vias termicas U6 EP), DRC/ERC finais, exports hardware/fabrication, este documento, D-34+, PROGRESS, RELATORIO_FINAL |

## 2. Tabela item -> estado

Estado: APLICADO / PARCIAL / DEFERIDO / N-A (nao aplicavel). Evidencia = ficheiro em hardware/reports salvo indicacao.

| Item | Descricao curta | Estado | Commit | Evidencia |
|---|---|---|---|---|
| 1 | Unir redes VFBSMPS e VCAP | APLICADO | a5d60b8 | corr/drc_step2*.json, hybrid_HybridPanda_netlist.xml |
| 2 | C64 2.2uF em VCAP (U7.103) | APLICADO (0402, nao 0603: espaco) | a5d60b8 | corr/drc_step2*.json, bom_real/BOM_HYBRIDPANDA_v1.csv |
| 3 | C65 4.7uF em VDDSMPS (U7.16) | APLICADO | a5d60b8 | idem |
| 4 | R1 1k -> 10k R_0603 | APLICADO | b209b08 | corr/drc_step3c.json |
| 5 | D15 zener 12 V SOD-123 (BZT52C12) | APLICADO (B.Cu) | b209b08 | corr/drc_step3c.json |
| 6 | Cin TPS5450 C4/C12 2.2uF -> 10uF | APLICADO com desvio: 0805 50 V (1206 nao cabe) | b209b08, eb14492 | corr/drc_step3e.json, corr/corrections/resume-step3.md |
| 7 | R6 footprint C_0603 -> R_0603 | APLICADO | a8b98a9 | footprint_audit/, corr/drc_step1*.json |
| 8 | U13 ESD USB USBLC6-2SC6 | APLICADO (flow-through, F.Cu) | b209b08, eb14492 | corr/drc_step3e.json |
| 9 | D10 BAS70H funcao | DEFERIDO: decisao de arquitectura (ligar so com USB?) pertence ao dono; sem alteracao | - | si_pi_audit/si-pi-audit/proposed-changes.md |
| 10 | 100nF em BOOT0 / VIO (opcional) | DEFERIDO: opcional, exige 5 caps novos sem espaco junto ao U7 em B.Cu | - | - |
| 11 | +5V -> U1.6 alargado | APLICADO | b209b08 | corr/drc_step3c.json |
| 12 | +5V -> U12.1 0.2 -> 0.5 mm | APLICADO (9 segmentos) | 15e11dd | corr/step5_pcb.json (widen 12) |
| 13 | USB_PWR 0.6 -> 1.0 mm | PARCIAL: 1.0 mm no trajecto, 0.8 mm junto a via e 0.3 mm na entrada do pad U1.1 (curto/clearance) | 15e11dd | corr/step5_pcb.json (widen 13, widen_fix) |
| 14 | +3V3 saida L3.2 0.2 -> 0.4 mm | PARCIAL: 0.4 mm excepto 2 segmentos de entrada em U12.4 (0.2) | 15e11dd | corr/step5_pcb.json (widen 14) |
| 15 | Vias GND no pad termico U6.9 | APLICADO: 5 vias 0.6/0.3 entre os quadrados de pasta + ligacao solida; a fila inferior (3 vias) nao cabe (SWDIO em In2 a y 43.56) | (final) | corr/drc_step5r.json, corr/step5_pcb.json (u6ep) |
| 16 | No SW TPS5450: mover L4/D12/C37 | DEFERIDO: D12 na posicao proposta colide com U6; a zona SW e o unico cobre largo U6.8 -> D12.1; aproximar L4 obriga a realocar C4/C6/C7/L4 (re-floorplan); C37.2 -> PH < 2 mm impossivel (BOOT pino 1 e PH pino 8 opostos) | - | corr/corrections/resume-step3.md |
| 17 | Retirar trilhas de potencia das camadas internas | PARCIAL: +12V e 12V_Protected removidos de In2; 12V_Protected mantido em In1 (0.35/0.3/0.2 por clearance NRST e furo); trecho necessario para conectividade | 15e11dd | corr/step5_pcb.json (inner17*) |
| 18 | R20/R21 22R para B.Cu junto a U7.100/101 | APLICADO | b209b08 | corr/drc_step3c.json |
| 19 | USB_R_D+/D- par acoplado | APLICADO (In1 0.2 mm / gap 0.3, uma camada ate U13) | b209b08, eb14492 | corr/drc_step3e.json |
| 20 | VCAP em B.Cu 0.3 mm | APLICADO parcialmente: trilho In1 0.3 mm mantido (remover deixa 1 unconnected); C64 do item 2 feito | a5d60b8, 15e11dd | corr/step5_pcb.json (inner17 VCAP / restore) |
| 21 | C41/C42 mais perto de U7.15/17 | DEFERIDO: posicoes propostas colidem com L5 e com trilhos VCAP/VLXSMPS; exige rerotear o bloco SMPS | - | si_pi_audit/si-pi-audit/si-pi-audit.md |
| 22 | C38 100nF NRST junto a U7.27 | DEFERIDO: posicao proposta (104.6,68.9) ocupada por trilhos LED_*/SWD em B.Cu; exige rerotear | - | idem |
| 23 | Mover U5 LED + R17-R19 para a borda | DEFERIDO: re-floorplan + rerotear 4 redes; sem ganho de SI mensuravel | - | idem |
| 24 | C23/C24 15pF -> 18pF | APLICADO (esquema, PCB, BOM) | 15e11dd | corr/erc_step5.json, bom_real/BOM_HYBRIDPANDA_v1.csv |
| 25 | PESD2CAN D8/D5 junto a P1 | DEFERIDO: area junto a P1.B2/B3 ocupada por D1/R1/Q4/D15; mover D8 9 mm obriga a rerotear BUS1N | - | - |
| 26 | Pares CAN 0.25 mm uniformes | PARCIAL: 61 segmentos 0.15 -> 0.25; 16 em 0.20 (clearance), 9 mantidos em 0.15 (borda/P1/clearance) | 15e11dd | corr/step5_pcb.json (can, can_fix, can_revert) |
| 27 | Politica In2 = GND (mover +3V3/SBU1_ADC/...) | DEFERIDO: 60+ mm de sinais em In2 sem canal livre em F/B.Cu; exige reroteamento global | - | - |
| 28 | Zona GND thermal_gap 0.3 / bridge 0.4, ilhas | APLICADO (starved_thermal 18 -> 0) | 15e11dd | corr/drc_step5c.json |
| 29 | Vias GND junto a U7 VSS 6/69/89/104 | DEFERIDO: pads 6/89 ja tem via GND a < 1.3 mm; pad 69: unica posicao cai dentro do pad U12.6 (via-in-pad); pad 104 sem espaco | - | corr/step5_pcb.json (vss, vss_revert), final_audit.json |
| 30 | Vias 0.5 -> 0.6 (anel 0.15); regras | APLICADO: 72 vias; via 0.45/0.25 -> 0.6/0.3; regras anel 0.125 / trilha 0.1 / via 0.127 (0.13 impossivel: PTH do P1 tem anel 0.125) | 15e11dd | corr/drc_step5*.json, .kicad_pro |
| 31 | Costura GND ~15 vias | APLICADO (16 vias 0.6/0.3) | 15e11dd | corr/step5_pcb.json (stitch) |
| 32 | P1 hole_clearance (8) | DEFERIDO: deslocar PTH +0.15 mm resolve os 8 mas cria curto com BUS0_H/SBU2; desvio herdado do footprint TYPE-C-31-M-04 (aceitar com o fabricante) | - | corr/step5_pcb.json (p1hole) |
| 33 | U3 copper_edge (2) | APLICADO: contorno +0.4 mm em x para y < 48.6 (33a) e shell U3 pinos 5/6 a GND (33b) | 15e11dd | corr/drc_step5b.json, corr/erc_step5.json |
| 34 | D1 SMAJ16CA junto a P1.A4/B4 | DEFERIDO: posicao proposta (138.6,56.0) ocupada por P1/Q4; trilha actual 1.0-1.5 mm aceite | - | - |
| 35 | Silk/texto | PARCIAL: 23 refs 0.5 -> 0.8 mm; 45 mantidos em 0.5 (sobreposicao com pads/outras refs) | 15e11dd | corr/drc_step5n.json, corr/drc_step5o.json |
| 36 | Cout TPS5450 polimero 100uF 7343 | DEFERIDO: case 7343 nao cabe no local de C21 sem re-floorplan; 47uF 0805 10 V mantido | - | bom_real/bom-real/bom-report.md |
| FA | Footprints (Q1/Q2/Q3, U5, U12, P1, R6, atributos, 3D) | APLICADO | a8b98a9 | footprint_audit/footprint-audit/footprint-audit.md |
| BOM-a | C8 10uF 0402 -> 0603 | DEFERIDO: 0603 nao cabe entre U12 e L3; peca 0402 10uF 10 V X5R com derating registado | - | bom_real/bom-real/bom-report.md |
| BOM-b | U1 AP22615 -> TPS2553 (alternativa) | DEFERIDO: apenas alternativa documentada, pinagem diferente | - | idem |

## 3. Numeros finais

DRC (hardware/reports/hybrid_DRC_final.json = corr/drc_final.json): total 135 (baseline passo 7: 182-184).
- clearance 0, unconnected 0, schematic_parity 0, shorting_items 0, tracks_crossing 0.
- Restantes (todos herdados do baseline OpenBlackPanda ou avisos): hole_clearance 8 (P1, item 32),
  lib_footprint_mismatch 73 (footprints editados localmente de proposito: FA, P1, U12, fiduciais),
  silk_edge_clearance 4, silk_over_copper 1 (silk do P1 sobre R1), silk_overlap 4, text_height 45.
- Categorias eliminadas face ao baseline: copper_edge_clearance (2 -> 0), starved_thermal (18 -> 0),
  drill_out_of_range (1 -> 0), footprint_type_mismatch (10 -> 0).

ERC (hardware/reports/hybrid_ERC_final.json): 0 erros, 373 avisos (endpoint_off_grid 145, lib_symbol_issues 6, ...).

final_audit.py (hardware/reports/final_audit.json, docs/final-audit.md): curtos geometricos 0,
via-in-pad 0 (5 vias termicas no EP do U6 classificadas a parte, mesma rede), clearance real 0,
hole_hits 8 (P1), redes partidas 0, teia de mascara 0. ALTO restantes: 8x folga de furo do P1 e
BOM com 1 linha sem MPN (JP1, jumper de solda sem peca).

step7_validate.py (hardware/reports/step7_validation.json): falhas []. Paridade red_h7 36/36.

step8_fabricate.py (hardware/fabrication, hardware/reports/step8_fabrication.json): gerbers, drill, CPL, BOM_JLC.csv
(117/119 refs com LCSC; JP1 e U1 sem), PDFs, STEP (kicad-cli devolve exit 2 por modelos 3D em falta
mas o ficheiro e gerado), zip. ../fabrication/readme.md continua "NAO FABRICAR".

## 4. Delta de BOM (passos 1-5)

| Ref | Antes | Depois | LCSC | Estado |
|---|---|---|---|---|
| C4, C12 | 2.2uF 0805 | 10uF 50 V X5R 0805 CL21A106KBYQNNE | C2932476 | a verificar |
| R1 | 1k 0402 | 10k 0603 | C25804 | a verificar |
| R6 | 3.16k em C_0603 | 3.16k em R_0603 (mesma peca) | - | - |
| C64 (novo) | - | 2.2uF 0402 10 V | C23733 | a verificar |
| C65 (novo) | - | 4.7uF 0603 10 V | (BOM_HYBRIDPANDA_v1.csv) | a verificar |
| D15 (novo) | - | BZT52C12 SOD-123 | C571379 | a verificar |
| U13 (novo) | - | USBLC6-2SC6 SOT-23-6 | C7519 | a verificar |
| JP1 (novo) | - | SolderJumper_2_Open | sem peca | n-a |
| C23, C24 | 15pF | 18pF 0402 C0G (0402CG180J500NT) | C1555 | A VERIFICAR (alt. CL05C180JB5NNNC C307443) |

Ficheiros: hardware/reports/hybrid_BOM.csv, hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv, BOM_JLCPCB.csv,
hardware/fabrication/assembly/BOM_JLC.csv. Nenhum codigo LCSC foi confirmado no catalogo JLC em sessao;
todos estao marcados "a verificar".

## 5. Itens deferidos (resumo com motivo)

9 (decisao de arquitectura), 10 (opcional, sem espaco), 16 (re-floorplan do bloco SW), 21/22/23
(reroteamento do bloco SMPS/NRST/LED), 25 (area de P1 ocupada), 27 (reroteamento global de In2),
29 (via-in-pad no pad 69; restantes ja cobertos), 32 (curto com BUS0_H/SBU2 ao deslocar PTH do P1),
34 (sem espaco junto a P1), 36 (7343 nao cabe), C8 0603, U1 alternativa.
Todos exigem relayout parcial ou decisao do dono; nenhum e bloqueante para o DRC.

## 6. Nao verificado (nada foi testado em hardware)

- Nenhuma placa foi fabricada, montada ou medida. Todas as correcoes sao geometricas/estaticas.
- Impedancia CAN-FD/USB e stackup: apenas estimativa analitica; nao confirmado com o fabricante.
- Codigos LCSC: nao confirmados no catalogo (marcados "a verificar"); JP1/U1 sem LCSC.
- CL do cristal com C23/C24 18pF: confirmar por medida de frequencia.
- Thermals (item 28): soldabilidade dos pads solidos ao plano (C28.2, U9.2, U7.104, U3.5/6) nao avaliada em reflow.
- hole_clearance P1: aceitar o desvio com o fabricante ou substituir o footprint TYPE-C-31-M-04.
- Rotacao CPL para a convencao JLC nao normalizada.
- Firmware red panda nunca executado neste hardware.
- Limitacao de ambiente: step7 Make-Manifest falhou temporariamente por ficheiro bloqueado em
  software/flowpilot-port (outro agente); passou na re-execucao. final_audit.py termina com os._exit(0) para
  contornar hang no teardown do pcbnew (KiCad 10).
