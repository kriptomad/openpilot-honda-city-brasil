# Auditoria final — PCB, esquemático e BOM (independente do DRC)

Data: 2026-10-29 16:44:23 · `hardware\scripts\final_audit.py` (10 s) · placa `hardware\hybrid-panda\HybridPanda.kicad_pcb` · JSON `hardware\reports\final_audit.json`

## Resumo por gravidade

| Gravidade | Qtd |
|---|---|
| CRITICO | 0 |
| ALTO | 0 |
| MEDIO | 0 |
| BAIXO | 1 |
| INFO | 20 |

## A. Teste de curtos virtuais (geométrico, folga 0)

- Pares cobre×cobre de redes diferentes testados (caixas a < 0,10 mm): **751** → sobreposições (curto): **0**; folga < 0,10 mm: 0
- Zona×cobre de outra rede: curtos **0**, folga < 0,10: 0
- Furos (vias+PTH) × cobre de outra rede: furo dentro de cobre **0**, folga < 0,20: 0
- Conectividade: KiCad unconnected = **0**; redes com pads isolados = **0** (de 63 redes com ≥ 2 pads)

## B. Montagem / fabrico

| Gravidade | Área | Achado |
|---|---|---|
| INFO | montagem | 0 vias dentro de pads SMD (via-in-pad): risco de sucção de solda/tombstone em 0402 — exigir vias tapadas (plugged/capped, IPC-4761 tipo VI/VII) ou aceitar retrabalho; sem isso, montagem por refluxo pode falhar nesses pads  |
| INFO | montagem | 9 vias térmicas (mesma rede) em pads expostos (CONV_TPS5450DDAR, DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm): voiding/sucção de solda no EP é esperado; posicionadas entre os quadrados de pasta  |
| INFO | montagem | footprints sem courtyard (sem verificação de colisão possível): U5, FID2, FID3, U3, FID1, P1, FID4, FID6, FID5  |
| INFO | montagem | 124 vias sob corpos de componentes (tenting F/B = True/True)  |
| INFO | montagem | 125 componentes, 45 no lado B (C38, FB1, D14, C52, C42, C63, C23, C50, R28, C62, D15, C53…), THT: U6, U3, P1; 64 referências sem serigrafia (identificação só pelo CPL)  |
| INFO | montagem | polaridade/pino 1 a confirmar visualmente no render/F.Fab: D12, D7, U12, D2, U9, U1, U8, D11, D9, Q1, D5, D6, Q2, D8, U6, U5, D10, Q3, Q4, U10, U11, D1, U3, P1, U13, JP1, D14, D15, D13, U7, J1, Y1  |
| BAIXO | fabrico | 121 junções de trilha com ângulo agudo (< 90°) — 'acid traps' cosméticos em processo moderno; o Freerouting gera 45°/90° mas o A* do 5c pode gerar outros  |
| INFO | fabrico | trilha mín 0.1400 mm, broca mín 0.30 mm (regra 0,30 — 1 via herdada 0,25); folga mín testada 0,10 mm  |

### Via-in-pad (lista)

| Via | Pad | Mesma rede |
|---|---|---|

### Trilhas de potência

| Rede | Trilhas | Larg. mín (mm) @ | Larg. máx | Comp. (mm) | Vias |
|---|---|---|---|---|---|
| +12V | 30 | 0.200 @ 141.40,51.11 F.Cu | 1.500 | 34.1 | 4 |
| +3V3 | 244 | 0.200 @ 136.64,68.46 F.Cu | 1.000 | 320.0 | 49 |
| +5V | 95 | 0.200 @ 125.47,55.57 F.Cu | 1.000 | 131.3 | 15 |
| GND | 221 | 0.200 @ 97.94,63.39 F.Cu | 0.800 | 214.1 | 98 |
| USB_PWR | 18 | 0.200 @ 119.08,54.38 F.Cu | 1.000 | 30.1 | 0 |

## C. Esquemático

| Gravidade | Achado |
|---|---|
| INFO | U7 BOOT0 → ['BOOT0'] ; outros nós: [('R14', '1'), ('SW1', '1')]  |
| INFO | U7 NRST → ['NRST'] ; outros nós: [('C38', '1'), ('J1', '10')]  |
| INFO | U7 PDR_ON → ['+3V3'] ; outros nós: [('C1', '1'), ('C11', '1'), ('C14', '1'), ('C16', '1'), ('C2', '1'), ('C26', '1'), ('C27', '1'), ('C28', '1')]  |
| INFO | U7 VBAT → ['+3V3'] ; outros nós: [('C1', '1'), ('C11', '1'), ('C14', '1'), ('C16', '1'), ('C2', '1'), ('C26', '1'), ('C27', '1'), ('C28', '1')]  |
| INFO | U7 VDD50USB → ['+3V3'] ; outros nós: [('C1', '1'), ('C11', '1'), ('C14', '1'), ('C16', '1'), ('C2', '1'), ('C26', '1'), ('C27', '1'), ('C28', '1')]  |
| INFO | U7 VDD33USB → ['+3V3'] ; outros nós: [('C1', '1'), ('C11', '1'), ('C14', '1'), ('C16', '1'), ('C2', '1'), ('C26', '1'), ('C27', '1'), ('C28', '1')]  |
| INFO | U7 VREF+ → ['VDDA'] ; outros nós: [('C43', '1'), ('C44', '1'), ('FB1', '1')]  |
| INFO | U7 VDDA → ['VDDA'] ; outros nós: [('C43', '1'), ('C44', '1'), ('FB1', '1')]  |
| INFO | U8 TJA1042: {'1': 'BUS1O_TX', '2': 'GND', '3': '+5V', '4': 'BUS1O_RX', '5': '+3V3', '6': 'BUS1O_L', '7': 'BUS1O_H', '8': 'BUS1O_STB'}  |
| INFO | U9 TJA1042: {'1': 'BUS2_TX', '2': 'GND', '3': '+5V', '4': 'BUS2_RX', '5': '+3V3', '6': 'BUS2_L', '7': 'BUS2_H', '8': 'BUS2_STB'}  |
| INFO | U10 TJA1042: {'1': 'BUS1N_TX', '2': 'GND', '3': '+5V', '4': 'BUS1N_RX', '5': '+3V3', '6': 'BUS1N_L', '7': 'BUS1N_H', '8': 'BUS1N_STB'}  |
| INFO | U11 TJA1042: {'1': 'BUS0_TX', '2': 'GND', '3': '+5V', '4': 'BUS0_RX', '5': '+3V3', '6': 'BUS0_L', '7': 'BUS0_H', '8': 'BUS0_STB'}  |

Pinos de sistema do U7 → rede: VCAP=VCAP; VDDLDO=+3V3; VDDSMPS=+3V3; VSSSMPS=GND; VLXSMPS=VLXSMPS; VFBSMPS=VCAP; VDD50USB=+3V3; VDD33USB=+3V3; VREF+=VDDA; VDDA=VDDA; VSSA=GND; VBAT=+3V3; BOOT0=BOOT0; NRST=NRST; PDR_ON=+3V3; PH0/OSC_IN=HSE_IN; PH1/OSC_OUT=HSE_OUT; PF7=GND; PF8=GND; PF9=Net-(JP1-B); PF10=GND

## D. BOM (54 linhas)

| Refs | Valor | Footprint | Qtd | Notas |
|---|---|---|---|---|
| C1,C2,C5,C11,C14,C26-C33 | 100NF | C_0402_1005Metric | 13 |  |
| C3,C10,C16-C21 | 47uF | C_0805_2012Metric | 8 |  |
| C4,C12 | 10uF | C_0805_2012Metric | 2 |  |
| C6,C7 | 2.2uF | C_0805_2012Metric | 2 |  |
| C8 | 10uF | C_0402_1005Metric | 1 |  |
| C23,C24 | 18pF | C_0402_1005Metric | 2 |  |
| C34 | 0.1uF | C_0402_1005Metric | 1 |  |
| C37 | 10nF (LOW ESR) | C_0402_1005Metric | 1 |  |
| C38,C44-C59 | 100nF | C_0402_1005Metric | 17 | VCAP: exigir ESR < 100 mΩ, X7R/X5R, ≥6,3 V (DS13311 §6.3.2) |
| C39,C40 | 2.2uF | C_0603_1608Metric | 2 | VCAP: exigir ESR < 100 mΩ, X7R/X5R, ≥6,3 V (DS13311 §6.3.2) |
| C41 | 220pF | C_0402_1005Metric | 1 | SMPS Cin/Cfilt (DS13311 §6.3.3) |
| C42 | 10uF | C_0805_2012Metric | 1 | SMPS Cout 10 µF ESR 20 mΩ (DS13311 §6.3.3) |
| C43,C63 | 1uF | C_0402_1005Metric | 2 |  |
| C60-C62,C65 | 4.7uF | C_0603_1608Metric | 4 |  |
| C64 | 2.2uF | C_0402_1005Metric | 1 |  |
| D1 | SMAJ16CA-13-F | DIOM4325X250N | 1 |  |
| D2 | BAS40WS 43 | D_SOD-323 | 1 |  |
| D5-D9 | PESD2CAN,215 | SOT95P230X110-3N | 5 |  |
| D10 | BAS70H 115 | D_SOD-123F | 1 |  |
| D11 | B320AE-13 | D_SMA | 1 |  |
| D12 | SM540C | D_SMC | 1 |  |
| D13,D14 | BAT54S | SOT-23 | 2 |  |
| D15 | BZT52C12 | D_SOD-123 | 1 |  |
| FB1 | 600R@100MHz | L_0603_1608Metric | 1 | ferrite VDDA: PROVISÓRIO (ex. BLM18 600 Ω/100 MHz) |
| J1 | SWD | PinHeader_2x05_P1.27mm_Vertical_SMD | 1 |  |
| JP1 | HW_ID1 | SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm | 1 |  |
| L3 | 47uH 2A - SMMS0650-470M | IND-SMD_L7.3-W6.8 | 1 |  |
| L4 | 15uH | L_10.5x11.5_H4.0 | 1 |  |
| L5 | 2.2uH DFE201610E-2R2M | L_Murata_DFE201610P | 1 | DFE201610E 2,2 µH: Isat ≥ 1,7 A / DCR ≤ 150 mΩ (PROVISÓRIO) |
| P1 | TYPE-C-31-M-04 | USB-C-SMD_TYPE-C-USB-20 | 1 |  |
| Q1,Q2 | DDTA143ECA-7-F P08 | SOT23-3 | 2 |  |
| Q3 | PDTC114EU | SOT-323_SC-70 | 1 |  |
| Q4 | HY12P03C2 | PowerPAK_SO-8_Single | 1 |  |
| R1 | 10k | R_0603_1608Metric | 1 |  |
| R2 | 1K | R_0402_1005Metric | 1 |  |
| R3,R9,R23,R24,R26 | 10K | R_0402_1005Metric | 5 |  |
| R5 | 10K (1%) | R_0402_1005Metric | 1 |  |
| R6 | 3.16K (1%) | R_0603_1608Metric | 1 |  |
| R14-R16,R28-R33 | 10k | R_0402_1005Metric | 9 |  |
| R17 | 180R | R_0402_1005Metric | 1 |  |
| R18 | 110R | R_0402_1005Metric | 1 |  |
| R19 | 100R | R_0402_1005Metric | 1 |  |
| R20,R21 | 22R | R_0402_1005Metric | 2 |  |
| R27 | 2.4K | R_0402_1005Metric | 1 |  |
| SW1 | SW_Push | SW_SPST_SKQG_WithStem | 1 |  |
| U1 | AP22615AWU-7 | SOT-23-6 | 1 |  |
| U3 | 10_0_QHHTZB6_3 | USB-A-TH_10.0QHHTZB6.3 | 1 |  |
| U5 | FM-B1921RGBA-SH | LED-ARRAY-SMD_4P-L2.2-W2.1-BR | 1 |  |
| U6 | TPS5450DDAR | CONV_TPS5450DDAR | 1 |  |
| U7 | STM32H725ZGT6 | LQFP-144_20x20mm_P0.5mm | 1 |  |
| U8-U11 | TJA1042TK-3 | DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm | 4 |  |
| U12 | XL1509-3.3 | Diodes_PSOP-8 | 1 |  |
| U13 | USBLC6-2SC6 | SOT-23-6 | 1 |  |
| Y1 | 25MHz X322525MOB4SI | Crystal_SMD_3225-4Pin_3.2x2.5mm | 1 | 25 MHz: CL = 2·(C_load − C_stray) — C de carga 15 pF PROVISÓRIO; validar com CL do cristal escolhido |

## Veredicto honesto

Curtos virtuais: ver §A (0 = nenhum item de cobre de redes diferentes se sobrepõe na geometria real da placa, incluindo preenchimentos de zona e furos). Isto é prova **geométrica estática**; não substitui teste eléctrico de continuidade/isolamento na placa fabricada (flying probe do fabricante ou multímetro no bring-up — STEP 9 passos 1–3).
Os achados ALTO/MEDIO de montagem (via-in-pad, teia de máscara, fiduciais, BOM sem MPN) têm de ser resolvidos antes de qualquer encomenda. **Não fabricar** nesta revisão.
