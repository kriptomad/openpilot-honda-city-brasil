# Hybrid Panda: descricao do esquema

Estado: apenas projeto. O esquema foi verificado por ferramenta (ERC) e por paridade de
netlist com a PCB; nao foi construido nem testado. Fonte:
`hardware/hybrid-panda/HybridPanda.kicad_sch` (S-expression do KiCad 10). Plots em PDF:
`hardware/fabrication/pdf/HybridPanda_schematic.pdf` e
`hardware/reports/hybrid_schematic.pdf`. Versao em ingles: [schematic.md](schematic.md).

## 1. Estrutura da folha

| Propriedade | Valor | Fonte |
|---|---|---|
| Folhas | 1 (plana, sem sub-folhas hierarquicas) | `HybridPanda.kicad_sch` (`sub_sheets = 0`) |
| Papel | A1 | `(paper "A1")`; D-18 |
| Origem | Gerado a partir do esquema da OpenBlackPanda v2 (A2) por `hardware/scripts/step4_build_schematic.py`, depois editado pelos scripts de correcao `corr_step*.py` | `hardware/research/step4-esquematico-h725.md`, `hardware/reports/correcoes-aplicadas.md` |
| Simbolos | 241 no total: 119 componentes, 122 simbolos de alimentacao (`#PWR`, `#FLG`) | extraido do arquivo |
| Fios / juncoes / nao conexoes | 450 / 138 / 77 | extraido do arquivo |
| Rotulos | 52 rotulos globais distintos (119 instancias); nenhum rotulo local ou hierarquico | extraido do arquivo |
| Bibliotecas de simbolos | `lib_symbols` embutidos mais `HybridPanda.symbols`; `sym-lib-table` reapontada (D-19) | `step4-esquematico-h725.md` secao 7 |

As areas funcionais sao marcadas por textos livres na folha. Os textos presentes no arquivo
sao: "OBD-C Connector", "Reverse polarity protection", "Power Regulators", "12V to 5V
Regulator", "5V to 3.3V Regulator", "USB Connector", "CAN Interface", "Microcontroller",
"Decoupling capacitors", "Ignition / SBU Detection", "HSE 25 MHz", "BOOT0", "NRST", "SWD
(ARM 10-pin)", "VCAP", "SMPS step-down", "VDDA filter", "LED drivers (PE4/PE3/PE2, active
low)", "SBU ADC conditioning (10k + BAT54S)", "5V sense (PB1)", "CAN STB pull-ups (default
standby)", "STM32H725 decoupling (VDD/VBAT/VDDLDO/VDDSMPS/VDD33USB)", "Power flags" e quatro
notas de anotacao (PCR-1 `JP1`, PCR-2 VFBSMPS -> VCAP, item SI/PI 5 `D15`, item SI/PI 8
`U13`). A area "GPS" do baseline foi removida (D-03).

## 2. Blocos funcionais

Os dados pad -> rede abaixo vem da netlist da PCB (`HybridPanda.kicad_pcb`), que a
verificacao do STEP 7 encontrou identica a netlist do esquema (119/119 componentes, 481
pads, 0 divergencias; `hardware/research/step7-validacao.md`).

### 2.1 Conector OBD-C e protecao de entrada

- `P1` TYPE-C-31-M-04 (receptaculo USB-C usado como OBD-C): A4/A9/B4/B9 = +12V; A1/A12/B1/B12
  e carcaca = GND; A2/A3 = BUS1O_H/L; B2/B3 = BUS1N_H/L; A10/A11 = BUS2_L/H; B10/B11 =
  BUS0_L/H; A8 = SBU1; B8 = SBU2. Pinos CC1/CC2 e D+/D- (A5, B5, A6, A7, B6, B7) sem ligacao.
- `D1` SMAJ16CA de +12V para GND.
- `Q4` HY12P03C2: dreno/fonte entre +12V (pads 5) e 12V_Protected (pads 1-3); gate (pad 4)
  em Net-(D15-A) com `R1` 10 k para GND, `D2` BAS40WS e `D15` BZT52C12 para 12V_Protected
  (zener limita Vgs, item SI/PI 5).
- `D5` PESD2CAN em SBU1/SBU2; `D6`-`D9` PESD2CAN nos quatro pares CAN.

### 2.2 Regulador 12 V -> 5 V

- `U6` TPS5450DDAR: pino 7 VIN = 12V_Protected, pino 8 PH = rede L4, pino 1 BOOT via `C37`
  10 nF para L4, pino 4 VSENSE do divisor `R5` 10 k (+5V) / `R6` 3,16 k (GND), pino 5 ENA
  sem ligacao, pinos 6 e 9 (pad exposto) GND.
- `L4` 15 uH de L4 para +5V; `D12` SM540C de GND para L4.
- Capacitores de entrada `C4`, `C12` 10 uF e `C6`, `C7` 2,2 uF em 12V_Protected; saida
  `C3`, `C10`, `C18`-`C21` 47 uF em +5V.

### 2.3 Regulador 5 V -> 3,3 V

- `U12` XL1509-3.3E1: pino 1 VIN = +5V, pino 2 SW = Net-(D11-K), pino 3 FB = +3V3, pinos 4-8
  GND.
- `L3` 47 uH de Net-(D11-K) para +3V3; `D11` B340A de GND para Net-(D11-K); `C8` 10 uF e
  `C16` 47 uF.

### 2.4 Porta USB-A e chave de carga

- `U1` AP22615AWU-7: pino 6 IN = +5V, pino 1 OUT = USB_PWR, pino 4 EN = Net-(Q3-C) com `R26`
  10 k para +5V, pino 3 FLG com `R9` 10 k para +5V, pino 5 ISET com `R27` 2,4 k para GND.
- `Q3` PDTC114EU: base USB_LOAD (PB14), emissor GND, coletor Net-(Q3-C). Nivel baixo em
  USB_LOAD deixa `U1` habilitado por `R26`; nivel alto liga `Q3` e desabilita `U1` (o
  comportamento com a configuracao open-drain do firmware upstream e discutido em
  `hybrid-fw-port.md`).
- `D10` BAS70H de +5V para USB_PWR; `C17` 47 uF, `C34` 100 nF em USB_PWR.
- `U3` receptaculo USB-A: pino 1 USB_PWR, pino 2 USB_R_D-, pino 3 USB_R_D+, pinos 4-6 GND
  (pinos de carcaca 5/6 ligados a GND pelo item 33b).
- `R20` 22 R USB_D- para USB_R_D-, `R21` 22 R USB_R_D+ para USB_D+.
- `U13` USBLC6-2SC6: pinos 1/6 em USB_R_D-, pinos 3/4 em USB_R_D+, pino 2 GND, pino 5 USB_PWR.

### 2.5 Interface CAN

Quatro celulas identicas (`U8` BUS1O, `U9` BUS2, `U10` BUS1N, `U11` BUS0), cada uma
TJA1042TK/3: pino 1 TXD = BUSx_TX, pino 4 RXD = BUSx_RX, pino 8 STB = BUSx_STB (pull-up
`R30`-`R33` 10 k para +3V3), pino 3 VCC = +5V (desacoplado por `C30`-`C33`), pino 5 VIO =
+3V3 (desacoplado por `C26`-`C29`), pinos 2 e 9 GND, pinos 6/7 = BUSx_L/BUSx_H para `P1`.

### 2.6 Microcontrolador

- `U7` STM32H725ZGT6. Os pinos de sinal estao listados em
  [red-panda-retrofit-on-black-panda.pt-br.md](red-panda-retrofit-on-black-panda.pt-br.md)
  secao 5.
- Alimentacao: todos os pinos VDD, VBAT, VDDLDO, VDDSMPS, VDD33USB e VDD50USB em +3V3
  (D-14); VSS, VSSA, VSSSMPS em GND; VDDA/VREF+ (pinos 35/36) em VDDA atraves de `FB1` 600 R
  com `C43` 1 uF e `C44` 100 nF.
- Alimentacao do nucleo: Direct SMPS. VLXSMPS (pino 15) -> `L5` 2,2 uH -> VCAP; `C41` 220 pF
  em VLXSMPS; `C42` 10 uF em VCAP; VFBSMPS (pino 17) ligado a rede VCAP junto com os pinos
  VCAP 68, 103, 140 (PCR-2, D-35); `C39`, `C40` 2,2 uF (0603) e `C64` 2,2 uF (0402) em VCAP;
  `C65` 4,7 uF em VDDSMPS (pino 16).
- Esquema de desacoplamento (`step4-esquematico-h725.md` secao 6): 5 x 100 nF herdados do
  baseline (`C1`, `C2`, `C5`, `C11`, `C14`) + 15 x 100 nF (`C45`-`C59`) + 3 x 4,7 uF
  (`C60`-`C62`) + 1 uF (`C63`) em +3V3; um 100 nF por par de pinos VDD colocado na face
  inferior junto a `U7`.
- Straps de HW_TYPE: PF7, PF8, PF10 (pinos 21, 22, 24) para GND; PF9 (pino 23) para o pad 2
  de `JP1`, pad 1 de `JP1` para GND (PCR-1). PD4-PD6 sem ligacao (D-08).
- HSE: `Y1` 25 MHz entre HSE_IN (PH0, pino 25) e HSE_OUT (PH1, pino 26); `C23`, `C24` 18 pF
  para GND; pinos 2/4 de `Y1` em GND.
- NRST (pino 27): `C38` 100 nF para GND e pino 10 de `J1`.
- BOOT0 (pino 135): `R14` 10 k para GND; `SW1` para +3V3.
- SWD: `J1` pino 1 +3V3, pino 2 SWDIO (PA13), pino 4 SWCLK (PA14), pinos 3/5/9 GND, pino 10
  NRST, pinos 6/7/8 sem ligacao.

### 2.7 Deteccao de ignicao / SBU

- SBU1 (`P1` A8) e SBU2 (`P1` B8) sao puxados a +3V3 por `R24` e `R23` 10 k.
- `Q2` (SBU1) e `Q1` (SBU2), transistores PNP digitais DDTA143ECA: emissor +5V, coletor na
  linha SBU, base em relay_SBU1 (PC10) / relay_SBU2 (PC11). Levar a base a nivel baixo puxa
  a linha SBU para 5 V (funcao de rele do chicote / "intercept" do firmware panda).
- Condicionamento para ADC: `R28` 10 k de SBU1 para SBU1_ADC (PC4), `R29` 10 k de SBU2 para
  SBU2_ADC (PA1); `D13`/`D14` BAT54S grampeiam SBU1_ADC/SBU2_ADC entre GND e +3V3 (D-12,
  D-16).

### 2.8 LED de estado

- `U5` FM-B1921RGBA com anodo comum em +3V3; catodos RED-, GREEN-, BLUE- atraves de `R19`
  100 R, `R18` 110 R, `R17` 180 R para LED_RED (PE4), LED_GREEN (PE3), LED_BLUE (PE2). Ativo
  baixo, saidas open-drain.

### 2.9 Divisores de medicao

- VoltageSens (PF11) = 12V_Protected x `R2` 1 k / (`R3` 10 k + `R2` 1 k).
- 5VOUT_S (PB1) = +5V x `R16` 10 k / (`R15` 10 k + `R16` 10 k).

### 2.10 Resumo de pull-ups e pull-downs

| Rede | Resistor | Para | Finalidade |
|---|---|---|---|
| BOOT0 | `R14` 10 k | GND | boot pela flash por padrao |
| BUS0_STB, BUS1N_STB, BUS1O_STB, BUS2_STB | `R30`-`R33` 10 k | +3V3 | transceptores em standby ate serem acionados (D-09) |
| SBU1, SBU2 | `R24`, `R23` 10 k | +3V3 | nivel de repouso do SBU |
| Net-(D15-A) (gate do Q4) | `R1` 10 k | GND | liga Q4 quando ha +12V |
| Net-(Q3-C) (EN do U1) | `R26` 10 k | +5V | U1 habilitado salvo se Q3 puxar para baixo |
| Net-(U1-FLG) | `R9` 10 k | +5V | pull-up da bandeira de falha open-drain |
| PF7, PF8, PF10 | direto | GND | HW_TYPE id1 = 0 |
| PF9 | `JP1` | GND quando fechado | bit de id1 de HW_TYPE (D-35) |

Pontos de teste: nenhum. O esquema nao contem referencias `TP`; os pontos de medicao sao o
header `J1`, os pads de `JP1` e os pads dos componentes.

## 3. Redes de interesse

| Rede | De | Para | Notas |
|---|---|---|---|
| +12V | `P1` A4/A9/B4/B9 | `D1`, fonte de `Q4` | alimentacao do veiculo |
| 12V_Protected | dreno de `Q4` | `U6` VIN, `C4`/`C6`/`C7`/`C12`, `R3`, `D2`, `D15` | apos a chave de inversao |
| +5V | `L4` | `U12`, `U1`, VCC de `U8`-`U11`, `Q1`/`Q2`, `R5`, `R15`, capacitores de volume | saida do buck |
| +3V3 | FB de `U12` / `L3` | alimentacoes de `U7`, VIO dos transceptores, pull-ups, `U5`, pino 1 de `J1` | trilho 3,3 V; zona em In1.Cu sob `U7` |
| USB_PWR | OUT de `U1` | pino 1 de `U3`, pino 5 de `U13`, `C17`, `C34`, `D10` | 5 V comutado para o USB-A |
| VCAP | `L5`, pinos 17/68/103/140 de `U7` | `C39`, `C40`, `C42`, `C64` | alimentacao do nucleo (saida do SMPS) |
| VLXSMPS | pino 15 de `U7` | `L5`, `C41` | no de comutacao do SMPS |
| VDDA | `FB1` | pinos 35/36 de `U7`, `C43`, `C44` | alimentacao analogica |
| BUS0_H / BUS0_L | pinos 7/6 de `U11` | `P1` B11/B10, `D9` | FDCAN1 |
| BUS1N_H / BUS1N_L | pinos 7/6 de `U10` | `P1` B2/B3, `D8` | FDCAN2 normal |
| BUS1O_H / BUS1O_L | pinos 7/6 de `U8` | `P1` A2/A3, `D6` | FDCAN2 OBD |
| BUS2_H / BUS2_L | pinos 7/6 de `U9` | `P1` A11/A10, `D7` | FDCAN3 |
| BUS0_TX / BUS0_RX | `U7` PB9 / PB8 | pinos 1 / 4 de `U11` | |
| BUS1N_TX / BUS1N_RX | `U7` PB6 / PB5 | pinos 1 / 4 de `U10` | |
| BUS1O_TX / BUS1O_RX | `U7` PB13 / PB12 | pinos 1 / 4 de `U8` | |
| BUS2_TX / BUS2_RX | `U7` PG9 / PG10 | pinos 1 / 4 de `U9` | |
| BUS0_STB, BUS1N_STB, BUS1O_STB, BUS2_STB | `U7` PG11, PB3, PB4, PD7 | pino 8 dos transceptores, `R30`-`R33` | |
| USB_D+ / USB_D- | `U7` PA12 / PA11 | `R21` / `R20` | lado do MCU |
| USB_R_D+ / USB_R_D- | `R21` / `R20` | pinos 3 / 2 de `U3`, `U13` | lado do conector, par acoplado em In1.Cu |
| SWDIO / SWCLK | `U7` PA13 / PA14 | pinos 2 / 4 de `J1` | |
| NRST | pino 27 de `U7` | pino 10 de `J1`, `C38` | |
| BOOT0 | pino 135 de `U7` | `SW1`, `R14` | |
| SBU1 / SBU2 | `P1` A8 / B8 | `R24`/`R23`, `Q2`/`Q1`, `R28`/`R29`, `D5` | linhas SBU do chicote |
| SBU1_ADC / SBU2_ADC | `R28` / `R29` | `U7` PC4 / PA1, `D13` / `D14` | |
| relay_SBU1 / relay_SBU2 | `U7` PC10 / PC11 | base de `Q2` / `Q1` | |
| VoltageSens | `R2`/`R3` | `U7` PF11 | 12 V / 11 |
| 5VOUT_S | `R15`/`R16` | `U7` PB1 | 5 V / 2 |
| USB_LOAD | `U7` PB14 | base de `Q3` | |
| HSE_IN / HSE_OUT | `U7` PH0 / PH1 | `Y1`, `C23` / `C24` | 25 MHz |
| LED_RED / LED_GREEN / LED_BLUE | `U7` PE4 / PE3 / PE2 | `R19` / `R18` / `R17` | ativo baixo |
| VSENSE | `R5`/`R6` | pino 4 de `U6` | realimentacao 5 V |
| Net-(JP1-B) | `U7` PF9 | `JP1` | strap de HW_TYPE |

Nao ha rede de deteccao de VBUS para o MCU nem rede +5V em `P1`.

## 4. Estado do ERC

| Item | Valor | Fonte |
|---|---|---|
| Ferramenta | kicad-cli 10.0.7, `--severity-all`, 2026-10-28 | `hardware/reports/hybrid_ERC_final.json` |
| Erros | 0 | idem |
| Avisos | 373: `endpoint_off_grid` 145, `lib_symbol_mismatch` 185, `pin_to_pin` 37, `lib_symbol_issues` 6 | idem |
| Interpretacao | `endpoint_off_grid` e `lib_symbol_*` sao herdados do baseline (simbolos embutidos vs bibliotecas do KiCad 10, tabelas `.lib` legadas). Os avisos `pin_to_pin` incluem VCAP power_out com power_out (D-19, severidade rebaixada para aviso no `.kicad_pro`), PF7-PF10 bidirecional com PWR_FLAG GND (strap intencional, D-08) e o simbolo de LED `U5` com pinos nao especificados. | `step4-esquematico-h725.md` secao 7 |
| Paridade de netlist com a PCB | 119 componentes / 119 footprints, 481 pads, 0 divergencias | `step7-validacao.md` |
| Paridade de pinos com o firmware | 36/36 pinos exigidos por `red.h` nos pads esperados de `U7` | `hardware/scripts/step7_validate.py`, `step7-validacao.md` |

Nao verificado: operacao eletrica de qualquer bloco, estabilidade dos reguladores,
capacitancia de carga do cristal (peca CL 12 pF com cargas de 18 pF e escolha analitica,
`correcoes-aplicadas.md` item 24), integridade de sinal USB e CAN. A placa nao foi
construida.

## 5. Referencias

- `hardware/hybrid-panda/HybridPanda.kicad_sch`, `HybridPanda.kicad_pro`.
- `hardware/fabrication/pdf/HybridPanda_schematic.pdf`, `hardware/reports/hybrid_schematic.pdf`.
- `hardware/research/step4-esquematico-h725.md` (geracao do esquema, tabela de 144 pinos, analise do ERC).
- `hardware/research/step7-validacao.md` (verificacoes de netlist e paridade).
- `hardware/reports/correcoes-aplicadas.md` (alteracoes aplicadas apos as auditorias).
- `hardware/reports/hybrid_ERC_final.json`.
- `docs/decisions.md` D-03, D-08, D-09, D-12, D-14, D-16, D-18, D-19, D-35.
