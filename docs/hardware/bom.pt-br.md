# Hybrid Panda: lista de materiais (BOM)

Estado: apenas projeto. Nenhuma peca foi comprada, nenhum codigo LCSC foi confirmado no
catalogo do fornecedor e nenhuma placa foi montada. A versao legivel por maquina desta
tabela e [bom.csv](bom.csv), gerada a partir do esquema e da PCB KiCad por
`hardware/scripts/gen-docs-bom.py`. Versao em ingles: [bom.md](bom.md).

## 1. Estado da BOM

| Metrica | Valor | Fonte |
|---|---|---|
| Referencias do esquema (na BOM) | 119 | `HybridPanda.kicad_sch`, `gen-docs-bom.py` |
| Footprints apenas na PCB | 6 fiduciais `FID1`-`FID6` (sem peca) | `HybridPanda.kicad_pcb` |
| Referencias com MPN | 118 de 119 (o jumper de solda `JP1` nao tem peca) | `gen-docs-bom.py` |
| Referencias com codigo LCSC atribuido | 117 de 119 (`JP1`, `U1` sem codigo) | `gen-docs-bom.py`; `README.md` "Hardware: Hybrid Panda" |
| Codigos LCSC confirmados no catalogo JLCPCB | 0 (nenhum confirmado neste repositorio) | `hardware/reports/bom-real/bom-report.md` ("STATUS: PARCIAL"), `README.md` |
| Codigos marcados TO-VERIFY | `C64` C23733, `C4`/`C12` C2932476, `D15` C571379, `C23`/`C24` C1555 | `hardware/reports/correcoes-aplicadas.md` secao 4 |
| Linhas de compra distintas | 55 linhas agrupando por valor + footprint + MPN + LCSC (48 linhas / 114 componentes no snapshot `BOM_HYBRIDPANDA_v1.csv` de 2026-10-27, antes de a campanha de correcao adicionar `C64`, `C65`, `D15`, `U13`, `JP1`) | `bom.csv`; `bom-report.md` linha 6 |
| Custo estimado de componentes | USD 26,93 por placa a precos de 10 pecas, 47 linhas, sem `U1`; MCU USD 15,74 (precos JLCPCB consultados em 2026-10-27, nao cotados) | `bom-report.md` linhas 47-49 |
| Peca indisponivel na JLCPCB | `U1` AP22615AWU-7 (C2680357 removido); a alternativa TPS2553DBVR C55266 tem a mesma pinagem mas outra faixa de resistor ILIM, logo `R27` 2,4 k teria de mudar | `bom-report.md` linha 59 |
| Arquivos de montagem JLC | `hardware/fabrication/assembly/BOM_JLC.csv`, `CPL_JLC.csv` (rotacoes nao normalizadas para a convencao JLC) | `hardware/fabrication/readme.md` |

"Atribuido" nas tabelas abaixo significa que a propriedade `LCSC` esta preenchida no
simbolo do esquema. "Nao confirmado" se aplica a todas as linhas: os codigos foram obtidos
por busca na web (`bom-report.md`, secao de metodologia) e precisam ser verificados quanto a
existencia, estoque e compatibilidade de footprint antes de qualquer pedido.

## 2. BOM por funcao

Colunas: referencias, quantidade, valor, footprint (nome na biblioteca KiCad apos os dois
pontos), MPN, fabricante, codigo LCSC, estado, notas. Os textos de footprint e valor sao
exatamente os armazenados no esquema.

### 2.1 Microcontrolador e clock

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| U7 | 1 | STM32H725ZGT6 | LQFP-144_20x20mm_P0.5mm | STM32H725ZGT6 | STMicroelectronics | C730156 | atribuido / nao confirmado | Face inferior. 1 MB flash exigido (D-02). So o grau -40..85 C foi encontrado (`bom-report.md`). |
| Y1 | 1 | 25MHz X322525MOB4SI | Crystal_SMD_3225-4Pin_3.2x2.5mm | X322525MOB4SI | YXC | C9006 | atribuido / nao confirmado | CL 12 pF segundo `bom-report.md`. |
| C23, C24 | 2 | 18pF | C_0402_1005Metric | 0402CG180J500NT | Fenghua | C1555 | atribuido / TO-VERIFY | 15 pF -> 18 pF (item 24). Alternativa C307443 em `correcoes-aplicadas.md`. |
| C39, C40 | 2 | 2.2uF | C_0603_1608Metric | CL10A225KO8NNNC | Samsung | C23630 | atribuido / nao confirmado | VCAP. |
| C64 | 1 | 2.2uF | C_0402_1005Metric | CL05A225MP5NSNC | Samsung | C23733 | atribuido / TO-VERIFY | VCAP em U7.103 (item 2), 0402 por espaco. |
| L5 | 1 | 2.2uH DFE201610E-2R2M | L_Murata_DFE201610P | DFE201610E-2R2M=P2 | Murata | C337891 | atribuido / nao confirmado | Indutor do Direct SMPS. |
| C41 | 1 | 220pF | C_0402_1005Metric | 0402B221K500NT | Fenghua | C1530 | atribuido / nao confirmado | VLXSMPS. |
| C42 | 1 | 10uF | C_0805_2012Metric | CL21A106KAYNNNE | Samsung | C15850 | atribuido / nao confirmado | Saida do SMPS (VCAP). |
| C65 | 1 | 4.7uF | C_0603_1608Metric | CL10A475KO8NNNC | Samsung | C19666 | atribuido / nao confirmado | VDDSMPS em U7.16 (item 3). |
| FB1 | 1 | 600R@100MHz | L_0603_1608Metric | GZ1608D601TF | Sunlord | C1002 | atribuido / nao confirmado | Filtro VDDA. |
| C43 | 1 | 1uF | C_0402_1005Metric | CL05A105KA5NQNC | Samsung | C52923 | atribuido / nao confirmado | VDDA. |
| C44 | 1 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | VDDA. |
| C45-C59 | 15 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | Desacoplamento VDD, um por par de pinos VDD, face inferior. |
| C60, C61, C62 | 3 | 4.7uF | C_0603_1608Metric | CL10A475KO8NNNC | Samsung | C19666 | atribuido / nao confirmado | Volume +3V3 junto a U7. |
| C63 | 1 | 1uF | C_0402_1005Metric | CL05A105KA5NQNC | Samsung | C52923 | atribuido / nao confirmado | +3V3. |
| C38 | 1 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | NRST. |
| R14 | 1 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Pull-down de BOOT0. |
| SW1 | 1 | SW_Push | SW_SPST_SKQG_WithStem | SKQGAFE010 | Alps Alpine | C202424 | atribuido / nao confirmado | Botao BOOT0. |
| J1 | 1 | SWD | PinHeader_2x05_P1.27mm_Vertical_SMD | 20021121-00010C4LF | Amphenol ICC | C150517 | atribuido / nao confirmado | ARM 10 pinos, face inferior. |
| JP1 | 1 | HW_ID1 | SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm | - | - | - | sem peca (recurso da PCB) | Strap de PF9: fechado = red (7), aberto = hybrid (11). |

### 2.2 Front end CAN

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| U8, U9, U10, U11 | 4 | TJA1042TK-3 | DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm | TJA1042TK/3/1J | NXP | C131480 | atribuido / nao confirmado | Variante /3 (VIO 3,3 V) obrigatoria. EP do HVSON8 1,60x2,40 vs footprint 1,55x2,4 (`bom-report.md`). |
| D5, D6, D7, D8, D9 | 5 | PESD2CAN,215 | SOT95P230X110-3N | PESD2CAN,215 | Nexperia | C75176 | atribuido / nao confirmado | D5 em SBU1/SBU2, D6-D9 nos quatro pares CAN. |
| R30, R31, R32, R33 | 4 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Pull-ups de STB para +3V3 (D-09). |
| C26, C27, C28, C29 | 4 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | Desacoplamento VIO (+3V3) dos transceptores. |
| C30, C31, C32, C33 | 4 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | Desacoplamento VCC (+5V) dos transceptores. |

### 2.3 Entrada de energia e reguladores

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| D1 | 1 | SMAJ16CA-13-F | DIOM4325X250N | SMAJ16CA | Littelfuse | C148217 | atribuido / nao confirmado | TVS bidirecional 16 V em +12V. |
| Q4 | 1 | HY12P03C2 | PowerPAK_SO-8_Single | HY12P03C2 | HUAYI | C358006 | atribuido / nao confirmado | P-FET -30 V contra inversao. |
| R1 | 1 | 10k | R_0603_1608Metric | 0603WAF1002T5E | Uniroyal | C25804 | atribuido / nao confirmado | 1 k -> 10 k (item SI/PI 4). |
| D2 | 1 | BAS40WS 43 | D_SOD-323 | BAS40WS 43 | Changjing | C22648 | atribuido / nao confirmado | Rede de gate do Q4. |
| D15 | 1 | BZT52C12 | D_SOD-123 | BZT52C12 | High Diode (ou equivalente) | C571379 | atribuido / TO-VERIFY | Zener 12 V, limite de Vgs (item SI/PI 5), face inferior. |
| U6 | 1 | TPS5450DDAR | CONV_TPS5450DDAR | TPS5450DDAR | Texas Instruments | C114425 | atribuido / nao confirmado | Buck 12 V -> 5 V, 8 vias termicas (PTH 0,3 mm). |
| L4 | 1 | 15uH | L_10.5x11.5_H4.0 | MWSA1004S-150MT | Sunlord | C151872 | atribuido / nao confirmado | Indutor do buck. |
| D12 | 1 | SM540C | D_SMC | B540C-13-F | Diodes Inc | C72264 | atribuido / nao confirmado | Diodo de roda livre do buck. |
| C4, C12 | 2 | 10uF | C_0805_2012Metric | CL21A106KBYQNNE | Samsung | C2932476 | atribuido / TO-VERIFY | Entrada do TPS5450, 2,2 uF -> 10 uF (item 6). 50 V X5R, derating anotado em `BOM_HYBRIDPANDA_v1.csv`. |
| C6, C7 | 2 | 2.2uF | C_0805_2012Metric | CC0805KKX7R9BB225 | Yageo | C125847 | atribuido / nao confirmado | Entrada do TPS5450. |
| C37 | 1 | 10nF (LOW ESR) | C_0402_1005Metric | CL05B103KB5NNNC | Samsung | C15195 | atribuido / nao confirmado | Bootstrap do TPS5450. |
| R5 | 1 | 10K (1%) | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Realimentacao 5 V (VSENSE). |
| R6 | 1 | 3.16K (1%) | R_0603_1608Metric | 0603WAF3161T5E | Uniroyal | C22993 | atribuido / nao confirmado | Realimentacao 5 V (VSENSE). |
| C3, C10, C18, C19, C20, C21 | 6 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | atribuido / nao confirmado | Volume +5V. 10 V X5R; derating em 5 V anotado em `BOM_HYBRIDPANDA_v1.csv`. |
| U12 | 1 | XL1509-3.3 | Diodes_PSOP-8 | XL1509-3.3E1 | XLSEMI | C74193 | atribuido / nao confirmado | Buck 5 V -> 3,3 V; footprint PSOP-8 com pad exposto sem uso (herdado). |
| L3 | 1 | 47uH 2A - SMMS0650-470M | IND-SMD_L7.3-W6.8 | SMMS0650-470M | SXN | C149588 | atribuido / nao confirmado | |
| D11 | 1 | B320AE-13 | D_SMA | B340A-13-F | Diodes Inc | C85098 | atribuido / nao confirmado | Diodo de roda livre do buck 3,3 V. |
| C8 | 1 | 10uF | C_0402_1005Metric | CL05A106MP5NUNC | Samsung | C315248 | atribuido / nao confirmado | 0603 deferido (BOM-a): sem espaco entre U12 e L3. |
| C16 | 1 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | atribuido / nao confirmado | Volume +3V3. |
| C1, C2, C5, C11, C14 | 5 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | Desacoplamento +3V3 (baseline). |
| R2 | 1 | 1K | R_0402_1005Metric | 0402WGF1001TCE | Uniroyal | C11702 | atribuido / nao confirmado | Divisor VoltageSens (lado baixo). |
| R3 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Divisor VoltageSens (lado alto). |
| R15, R16 | 2 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Divisor 5VOUT_S. |

### 2.4 USB

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| U3 | 1 | 10_0_QHHTZB6_3 | USB-A-TH_10.0QHHTZB6.3 | 10.0 QHHTZB6.3 | SHOU HAN | C668591 | atribuido / nao confirmado | Receptaculo USB-A, carcaca THT (slots 2,5 mm). |
| U1 | 1 | AP22615AWU-7 | SOT-23-6 | AP22615AWU-7 | Diodes Inc | - | so MPN / fora da JLCPCB | Chave de carga; ver secao 1. |
| Q3 | 1 | PDTC114EU | SOT-323_SC-70 | PDTC114EU,115 | Nexperia | C135830 | atribuido / nao confirmado | Deslocador de nivel USB_LOAD. |
| R9 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Pull-up FLG do U1. |
| R26 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Pull-up EN do U1. |
| R27 | 1 | 2.4K | R_0402_1005Metric | 0402WGF2401TCE | Uniroyal | C25882 | atribuido / nao confirmado | ISET do U1; muda se U1 for substituido. |
| D10 | 1 | BAS70H 115 | D_SOD-123F | BAS70H,115 | Nexperia | C426766 | atribuido / nao confirmado | +5V para USB_PWR. |
| C17 | 1 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | atribuido / nao confirmado | Volume USB_PWR. |
| C34 | 1 | 0.1uF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | atribuido / nao confirmado | USB_PWR. |
| U13 | 1 | USBLC6-2SC6 | SOT-23-6 | USBLC6-2SC6 | STMicroelectronics | C7519 | atribuido / nao confirmado | Matriz ESD USB (item SI/PI 8). |
| R20, R21 | 2 | 22R | R_0402_1005Metric | 0402WGF220JTCE | Uniroyal | C25092 | atribuido / nao confirmado | Resistores serie USB, face inferior junto a U7. |

### 2.5 Conector de chicote, SBU e LED de estado

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| P1 | 1 | TYPE-C-31-M-04 | USB-C-SMD_TYPE-C-USB-20 | TYPE-C-31-M-04 | Korean Hroparts | C129018 | atribuido / nao confirmado | Receptaculo OBD-C; footprint com 8 itens DRC hole_clearance herdados. |
| Q1, Q2 | 2 | DDTA143ECA-7-F P08 | SOT23-3 | DDTA143ECA-7-F | Diodes Inc | C460029 | atribuido / nao confirmado | Drivers de rele SBU (PC11/PC10). Geometria dos pads corrigida no passo 1. |
| R23, R24 | 2 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Pull-ups SBU2/SBU1 para +3V3. |
| R28, R29 | 2 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | atribuido / nao confirmado | Serie SBU para ADC (D-12). |
| D13, D14 | 2 | BAT54S | SOT-23 | BAT54S,215 | Nexperia | C47546 | atribuido / nao confirmado | Grampos dos ADC SBU (D-16). |
| U5 | 1 | FM-B1921RGBA-SH | LED-ARRAY-SMD_4P-L2.2-W2.1-BR | FM-B1921RGBA-SH | Foshan NationStar | C727904 | atribuido / nao confirmado | LED RGB, anodo comum em +3V3. |
| R17 | 1 | 180R | R_0402_1005Metric | 0402WGF1800TCE | Uniroyal | C38941 | atribuido / nao confirmado | Azul. |
| R18 | 1 | 110R | R_0402_1005Metric | ERJ2RKF1100X | Panasonic | C413064 | atribuido / nao confirmado | Verde. |
| R19 | 1 | 100R | R_0402_1005Metric | 0402WGF1000TCE | Uniroyal | C25076 | atribuido / nao confirmado | Vermelho. |

### 2.6 Mecanica e auxiliares de montagem

| Refs | Qtd | Valor | Footprint | MPN | Fabricante | LCSC | Estado | Notas |
|---|---|---|---|---|---|---|---|---|
| FID1, FID2, FID3 | 3 | - | Fiducial_1mm_Mask2mm | - | - | - | sem peca | Fiduciais da face superior. |
| FID4, FID5, FID6 | 3 | - | Fiducial_1mm_Mask2mm | - | - | - | sem peca | Fiduciais da face inferior. |

Caixa: nao faz parte desta BOM. As STL do baseline em
`archive/baseline-original/BlackPanda/STLs/` nao servem mais para o contorno ampliado
(D-24, D-33); uma caixa nova nao foi projetada.

## 3. Totais por encapsulamento

De `bom.csv` (125 linhas incluindo fiduciais):

| Footprint | Quantidade |
|---|---|
| C_0402_1005Metric | 39 |
| R_0402_1005Metric | 22 |
| C_0805_2012Metric | 13 |
| C_0603_1608Metric | 6 |
| Fiducial_1mm_Mask2mm | 6 |
| SOT95P230X110-3N (PESD2CAN) | 5 |
| DFN-8-1EP_3x3mm (TJA1042) | 4 |
| R_0603_1608Metric | 2 |
| SOT-23-6 | 2 |
| SOT23-3 (biblioteca BlackPanda) | 2 |
| SOT-23 | 2 |
| Demais footprints | 1 cada (22 footprints) |

Montagem: 80 footprints na face superior, 45 na face inferior (incluindo `U7`, `Y1`, `J1`,
`L5`, capacitores VCAP e de desacoplamento). Through-hole: carcaca de `U3`, carcaca e pinos
de `P1`, vias termicas de `U6`. Fonte: `HybridPanda.kicad_pcb`.

## 4. Como regenerar

```
python hardware/scripts/gen-docs-bom.py
```

O script interpreta as S-expressions do esquema e da PCB sem KiCad nem kiutils e escreve
`docs/hardware/bom.csv` com as colunas `reference, value, footprint, mpn, manufacturer,
lcsc, lcsc_status, catalog_confirmed, side, dnp, datasheet, lib_id, source`. A coluna
`catalog_confirmed` e sempre `no` ate que uma verificacao de catalogo seja registrada em
`hardware/reports/bom-real/`.

## 5. Referencias

- `hardware/hybrid-panda/HybridPanda.kicad_sch` (propriedades `MPN`, `Manufacturer`, `LCSC`).
- `hardware/reports/bom-real/bom-report.md`, `BOM_HYBRIDPANDA_v1.csv`, `BOM_JLCPCB.csv`.
- `hardware/reports/hybrid_BOM.csv`, `hardware/fabrication/assembly/BOM_JLC.csv`.
- `hardware/reports/correcoes-aplicadas.md` secao 4 (alteracoes de BOM e codigos TO-VERIFY).
- `docs/decisions.md` D-02, D-09, D-12, D-16, D-20, D-35, D-37.
