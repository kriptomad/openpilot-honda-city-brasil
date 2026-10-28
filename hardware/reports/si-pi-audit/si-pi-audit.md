# Auditoria SI/PI e revisao de esquematico - Hybrid Panda (STM32H725ZGT6, KiCad 10)

Data: 2026-02 (sessao de auditoria). Fontes: `hardware\hybrid-panda\HybridPanda.kicad_pcb` /
`.kicad_sch` (somente leitura), `hardware\reports\hybrid_HybridPanda_netlist.xml`, `hardware\reports\hybrid_BOM.csv`,
`hardware\reference\panda\board\**` (firmware red panda), `hardware\reference\datasheets\DS13313_text.txt`
(STM32H725 DS), `hardware\research\STEP4/5/6*.md`. Medidas extraidas com `si_pi_dump.py` (saida em
`si_pi_dump.json`, `power_nets.json`) e DRC fresco em `drc_audit.json` (182 violacoes, 0 nao conectados).
Nada foi alterado na placa ou no esquematico.

Resumo da placa: 4 camadas (F.Cu 35 um / preg 0.2 / In1 17.5 um / core 1.065 / In2 17.5 um / preg 0.2 /
B.Cu 35 um, 1.59 mm, er 4.5). In2 = plano GND (1867.7 mm2 de 2366 mm2 = 79%), In1 = zona +3V3 (880 mm2
sob U7) + sinais. Contorno 91.91..142.535 x 32.01..78.76 mm (50.6 x 46.75 mm). 1208 trilhas, 214 vias
(0.45/0.25 x1, 0.5/0.3 x66, 0.6/0.3 x103, 0.7/0.3 x44). Cobre externo 1 oz, interno 0.5 oz.

Severidades: CRITICO (nao liga / destrutivo), ALTO (falha provavel em campo ou fora de spec),
MEDIO (margem insuficiente / EMI / robustez), BAIXO (boa pratica).

Convencao IPC-2221: I = k * dT^0.44 * A^0.725 (k = 0.048 externo, 0.024 interno). Capacidades usadas:
0.2 mm 1 oz = 0.74 A @10 C; 0.5 mm = 1.45 A; 0.6 mm = 1.65 A; 0.75 mm = 1.9 A; 1.0 mm = 2.3 A;
0.2 mm 0.5 oz interno = 0.23 A; 0.35 mm 0.5 oz = 0.34 A; 1.0 mm 0.5 oz = 0.8 A; via furo 0.3 mm ~1.0-1.6 A.

---------------------------------------------------------------------------------------------------

## BLOQUEADORES PARA PROTOTIPO (resolver antes de fabricar)

| # | Sev. | Item | Evidencia | Correcao |
|---|------|------|-----------|----------|
| B1 | CRITICO | VFBSMPS nao ligado a VCAP (MCU nao alimenta VCORE no modo SMPS direto que o firmware red panda programa) | netlist: VCAP = {C39.1, C40.1, U7.68, U7.103, U7.140}; VFBSMPS = {C42.1, L5.2, U7.17}; redes distintas. clock.h: LQFP144 -> `PWR->CR3 = SMPSEN` (LDO desligado). DS13313 Fig.17 "Direct SMPS": VFBSMPS deve ser ligado externamente a VCAP | Esquematico: unir redes (label VCAP em C42.1/L5.2/U7.17). PCB: trilha 0.3 mm B.Cu de C42.1 (109.43,73.70) ate C40.1 (123.46,63.35)/pino 140, ou curto ate novo capacitor; ver proposed_changes #1 |
| B2 | CRITICO | VCAP pino 103 sem capacitor (18.7 mm ate C40) e VCAP roteado 27.6 mm B.Cu + 16 mm In1 0.2 mm | u7_power_pins: pino 103 (115.75,45.94) nearest_cap C40.1 18.74 mm | Adicionar C 2.2 uF 0603 X7R (ESR < 100 mohm) em (116.0,44.6) B.Cu, ligado a U7.103 e GND (via 0.5/0.3). Manter 3 pinos VCAP interligados com trilha >= 0.3 mm |
| B3 | ALTO | +5V para U1.6 (AP22615, ILIM 2.08 A) por 1 via + In1 0.35 mm 0.5 oz + F.Cu 0.2 mm | via unica 0.6/0.3 em (120.28,46.70); In1 1.0 mm ~12 mm e 0.35 mm ~3.9 mm (0.34 A @10 C); via (116.50,54.95); F.Cu 0.2 mm ate U1.6 (117.17,54.38) | Re-rotear em F.Cu com >= 1.0 mm da zona +5V (C20/C21 em y 47.8) ate U1.6, ou 2+ vias 0.6/0.3 e In1 >= 2.0 mm |
| B4 | ALTO | R1 (gate de Q4) 1 k 0402 em 12-14.5 V dissipa 144-210 mW (0402 = 63 mW) | R1 1K R_0402 em (133.98,52.40), Net-(D2-A) = {D2.2, Q4.4, R1.2}, R1.1 = GND | Trocar por 10 k 0603 (14-21 mW) e adicionar zener 12 V SOD-323 gate-source (ver B5) |
| B5 | ALTO | Vgs de Q4 (HY12P03C2, +-20 V max) nao limitado: Vgs = -Vin; com load dump e SMAJ16CA grampeando em ate 26 V -> Vgs < -20 V | D2 BAS40WS esta com anodo no gate e catodo em 12V_Protected (nao limita Vgs negativo); nao ha zener | Zener 12-15 V (ex. BZT52C12, SOD-123) entre gate e 12V_Protected; R1 10 k; opcional 100 nF gate-source para controlar inrush |
| B6 | ALTO | USB D+/D- sem protecao ESD, resistores serie 22 R no meio do trajeto, par desacoplado com 5 vias e 4 camadas | pairs: USB_D+ 21.5 mm (F 3.2 / B 5.7 / In2 12.6), USB_D- 19.4 mm (F 4.6 / B 3.2 / In1 6.2 / In2 5.4), skew 2.1 mm, gap c-c mediano 2.27 mm (min 0.5), 2+3 vias; R20/R21 em (122.49,48.20) a 7-8 mm de U7.100/101 e 12.7-13.4 mm de U3.2/3 | Mover R20/R21 para < 3 mm de U7.100/101 (ex. 112.5,47.0 B.Cu), rotear par acoplado (0.2 mm / gap 0.2 mm) em uma camada (B.Cu) com 0 ou 1 par de vias, adicionar PRTR5V0U2X/USBLC6-2SC6 em U3 (ex. 133.5,42.0) |
| B7 | ALTO | Entrada do TPS5450: 4 x 2.2 uF 0805 (8.8 uF nominal, ~4 uF efetivos com polarizacao 12-14.5 V) abaixo do minimo TI (>= 10 uF ceramico ou eletrolitico) | C4/C6/C7/C12 2.2uF C_0805 em x = 113.6 | Trocar por 2 x 10 uF 1206 X7R 50 V + manter 2 x 2.2 uF; opcional 100 uF/25 V eletrolitico em 12V_Protected |

---------------------------------------------------------------------------------------------------

## A. Arvore de alimentacao e integridade de potencia (PI)

### A.1 Larguras / cobre vs corrente por rede (ver `power_nets.json`)

Correntes estimadas: +5V total ate 2.7 A (USB_PWR ate 2.08 A limitado por R27 + MCU/transceptores ~0.6 A);
+12V ~1.5 A (eta 0.85); +3V3 ~0.6 A; XL1509 Iout ~0.5 A.

| Rede | Caminho principal | Largura min (camada) | Capacidade @10 C | Vias | Veredito |
|------|-------------------|----------------------|------------------|------|----------|
| +12V | P1.A4/A9/B4/B9 (134.4-135.6, 57.6-60.1) -> B.Cu 0.5 mm -> zona B.Cu 29.9 mm2 -> 4 vias 0.6/0.3 (138.55..140.74, 53.0-53.2) -> 4 x 0.5 mm F.Cu -> Q4.5 (139.29,50.48) | 0.5 mm B.Cu / 4x0.5 F.Cu; paralelo 0.2 mm In2 8.6 mm | 1.45 A x4 = 5.8 A; vias 4 x ~1.2 A | 4 | OK. **BAIXO**: remover paralelo 0.2 mm em In2 (corta plano GND) |
| 12V_Protected | Q4.1/2/3 (135.93,48.6-51.1) -> 5 vias -> zona B.Cu 108 mm2 (112.2-136.6 x 34.9-51.4) -> 5 vias (112.7-115.4, 36.1-36.65) -> F.Cu 0.75 mm x=112.69 -> C4/C6/C7/C12 -> 0.5 mm (1.54 mm) -> U6.7 (110.76,41.51) | 0.75 / 0.5 mm F.Cu | 1.9 A / 1.45 A (>1.5 A) | 10 | OK para 1.5 A. **BAIXO**: paralelos 0.2 mm In1 (23 mm) e In2 (24.5 mm) cortam planos - remover |
| +5V tronco | L4.2 -> C18..C21 (112.4-118.5, 46.7-47.8) -> zona F.Cu 29.8 mm2 | zona | - | - | OK |
| +5V -> U1.6 | via (120.28,46.70) -> In1 1.0 mm -> In1 0.35 mm -> via (116.50,54.95) -> F.Cu 0.2 mm -> U1.6 | 0.35 mm 0.5 oz / 0.2 mm 1 oz | 0.34 A / 0.74 A vs 2.1 A | 1+1 | **ALTO** (B3) |
| +5V -> U12.1 | (112.37,45.75)->(109.86,45.54) 2.5 mm; (108.53,46.52)->(101.62,46.52) 6.9 mm; ->(99.64,44.55) 2.8 mm, F.Cu 0.2 mm | 0.2 mm | 0.74 A vs ~0.5-0.6 A | 0 | **MEDIO**: alargar para 0.5 mm (dT 10 C -> ~4 C) |
| +5V -> U8..U11.3 | B.Cu 0.2 mm ~13 mm | 0.2 mm | 0.74 A vs 4 x 70 mA = 0.28 A | - | OK |
| USB_PWR | U1.1 -> U3.1: 0.6 mm F.Cu depois 1.0 mm; C17 47 uF a 8.8 mm de U3.1 | 0.6 mm | 1.65 A vs 2.08 A | 0 | **MEDIO**: 1.0 mm em todo o trajeto |
| +3V3 | L3.2/C16 (93.47,44.86) -> zona F.Cu -> vias -> plano In1 880 mm2 | 0.2 mm F.Cu trecho curto | 0.74 A vs 0.6 A | 10+ | **BAIXO**: alargar saida de L3 para 0.4 mm |
| GND | plano In2 79% + zonas F/B/In1; 73 vias GND (NN mediano 1.87 mm, max 10.25 mm) | - | - | 73 | OK para corrente; ver B.4 |

Transicoes de via unica em redes de potencia: +5V -> U1.6 (B3). As demais usam 4-5 vias em paralelo.
Nenhuma rede de potencia usa via 0.45/0.25.

### A.2 Conversores

**TPS5450 (U6, 108.06,42.14, F.Cu), 12 V -> 5 V, 500 kHz**
- Realimentacao: R5 10 k (1%) / R6 3.16 k (1%): Vout = 1.221 * (1 + 10/3.16) = 5.08 V. OK (+1.6%).
  **BAIXO**: R6 usa footprint `Capacitor_SMD:C_0603` (105.81,45.64) - trocar por R_0603 para evitar
  erro de montagem/BOM.
- Indutor L4 15 uH (BlackPanda:L_10.5x11.5_H4.0, 121.19,39.58). TI (SLVS633) para 12 V -> 5 V / 3 A
  recomenda 10-15 uH (ripple ~0.5-0.9 A pp). OK. Confirmar Isat >= 3.5 A do MPN escolhido (MWSA1004S-150MT
  Isat ~3.6 A - OK). L3 47 uH 2 A (SMMS0650-470M) esta no XL1509, nao no TPS5450 - correto.
- Diodo de roda livre D12 SM540C (5 A / 40 V, SMC) a 4.39 mm de PH e 5.85 mm do EP/GND. OK eletricamente;
  **MEDIO** (EMI): laco PH-D12-GND-Cin alongado; aproximar catodo de D12 do PH e anodo da ilha GND dos
  Cin (ver B.5).
- Entrada: C7 2.2 uF a 1.96 mm, C6 2.53, C12 3.07, C4 4.13 mm de VIN. Posicao boa, **capacitancia
  insuficiente** (B7). Corrente RMS de entrada ~1.4 A: 0805 X7R 2.2 uF/50 V suportam ~0.6-0.8 A cada.
- Saida: C18..C21 4 x 47 uF 0805 (X5R 6.3 V presumido) -> ~75-100 uF efetivos a 5 V. O TPS5450 e
  compensado internamente para Cout >= 100 uF com ESR 15-150 mohm (polo/zero da compensacao). Com
  ceramicos puros (ESR ~3 mohm) a margem de fase pode cair. **MEDIO**: substituir um 47 uF por polimero
  100 uF / 6.3 V (ESR ~20-30 mohm, ex. 6TPE100MAZB) ou verificar com TI WEBENCH / medir Bode.
- BOOT: C37 10 nF 0402 (103.80,40.23) a 1.63 mm de U6.1 - OK; porem o retorno do BOOT (C37.2 -> PH)
  percorre 8.4 mm em 0.2 mm ate o no SW. **BAIXO**: ligar C37.2 diretamente ao pad PH (108.9,40.4) com
  trilha 0.3 mm < 2 mm.
- ENA (pino 5) flutuante = sempre ligado (pull-up interno 5 uA). OK. Pinos 2/3 NC. OK.
- Pad termico U6.9: 3 vias (107.41,40.19), (108.71,40.19), (107.41,44.09) com thermal starved em In1
  (DRC). **MEDIO**: 6-9 vias 0.3 mm no EP com conexao solida (sem relief) em todas as camadas; o EP e
  o unico retorno GND do CI.
- Zona SW "L4": 57.9 mm2 de cobre em F.Cu (zona 7.2 mm2 + trilha 2.0 mm x 24 mm). PH -> L4.1 = 11.75 mm.
  **MEDIO**: reduzir; L4 deveria estar a < 4 mm do PH (ver B.5).

**XL1509-3.3 (U12, 97.74,46.83, PSOP-8), 5 V -> 3.3 V, 150 kHz**
- Pinagem usada: 1 VIN(+5V), 2 OUT/SW, 3 FB ligado a +3V3 (versao fixa 3.3 V, Vref 1.23 V interno
  com divisor interno), 4-8 GND (inclui ON/OFF em GND = sempre ligado). Heranca do black panda (projeto
  comprovado). Datasheet XL1509 nao esta em hardware/reference - **BAIXO**: anexar e confirmar pino 3 = FB,
  pino 5 = ON/OFF.
- L3 47 uH 2 A, D11 B320AE (3 A / 20 V, SMA) em (97.26,41.27), C16 47 uF 0805 saida, C3 47 uF entrada.
  Para 150 kHz / 0.6 A, 47 uH da ripple ~0.1 A pp - OK. Cout 47 uF 0805 a 3.3 V (~30 uF efetivo) +
  plano In1: OK para 150 kHz; **BAIXO**: adicionar 22 uF 0805 X7R 10 V em paralelo a C16.
- Zona SW Net-(D11-K): 19 mm2 / 8.9 mm de trilha. Aceitavel para 150 kHz.
- Entrada 5 V em 0.2 mm (A.1) - **MEDIO**.

### A.3 Alimentacao do STM32H725 (U7, B.Cu, 109.5,56.6, rot 90) - esquema LDO vs SMPS

**Veredito: a placa esta fiada para "SMPS direto" (VDDSMPS = +3V3, L5 2.2 uH DFE201610E-2R2M, C41
220 pF em VLXSMPS, C42 10 uF em VFBSMPS, VDDLDO = +3V3), que e o esquema que o firmware red panda
programa para LQFP144 (clock.h: PKGR 0b0101/0b0111 -> `PWR->CR3 = SMPSEN`, LDO off). Porem a saida
do SMPS (VFBSMPS) NAO esta ligada aos pinos VCAP -> VCORE nao recebe alimentacao -> o MCU nao sai do
reset. Alem disso CR3 (byte baixo) e write-once: se a bootrom/bootstub gravar SMPSEN e o hardware nao
corresponder, o nucleo trava e exige DFU a frio. CRITICO (B1).**

Detalhes (DS13313 Tab.15/16 e Fig.17):
- VDDSMPS (pino 16, 110.75,67.26): Cin 4.7 uF requerido; o capacitor mais proximo e C47 100 nF a
  1.66 mm; os 4.7 uF (C60 115.75,72.73 / C61 95.31,57.54 / C62 116.75,40.47) estao a 4.7-6.3 mm de outros
  pinos VDD. **ALTO**: adicionar 4.7 uF 0603 a < 2 mm do pino 16 (ex. 110.75,69.0 B.Cu).
- VLXSMPS (pino 15): L5.1 a 3.01 mm, C41 220 pF a 4.93 mm. **MEDIO**: C41 deve ficar a < 2 mm do
  pino 15 (filtro de borda, AN5419); mover para (111.25,68.9).
- VFBSMPS (pino 17): C42 10 uF 0805 a 5.55 mm (ESR exigido <= 20 mohm - X7R 0805 OK). Mover para
  < 3 mm (110.25,69.5). L5 DCR 150 mohm max exigido; DFE201610E-2R2M DCR ~60 mohm, Isat ~1.8 A: OK.
- VCAP (pinos 68/103/140): C39 2.2 uF 0603 a 2.49 mm (pino 68) e C40 a 2.52 mm (pino 140): OK. Pino 103
  sem capacitor: **CRITICO** (B2). C40.2 (GND) com thermal starved (DRC) - **MEDIO**: conexao solida.
- VDDLDO (70/105/143) = +3V3: OK (DS exige VDDLDO ligado a VDD mesmo com LDO off).
- VDD50USB (90) e VDD33USB (91) = +3V3: correto porque o firmware nao habilita USB33DEN (regulador USB
  interno desligado -> VDD50USB deve ser ligado a VDD33USB). Capacitor mais proximo C58 a 3.1-3.5 mm.
  **BAIXO**: 100 nF a < 2 mm dos pinos 90/91 (109.5,44.0).
- PDR_ON (142) = +3V3: OK (PDR interno ativo).
- VBAT (pino 6?) = +3V3 direto: OK (sem RTC backup). BAIXO: nada a fazer.
- VDDA/VREF+ (35/36): FB1 600 R @100 MHz (99.88,73.96) + C43 1 uF (4.81 mm) + C44 100 nF (2.12 mm).
  OK. **BAIXO**: mover C43 para < 3 mm.
- Decoupling VDD: 100 nF em todos os pares VDD/VSS a 0.7-2.3 mm (pinos 7, 8, 13, 19, 32, 42, 56, 70/71,
  79, 92, 105/106, 119, 129, 142-144); pinos 90/91/92 a 3.1-3.5 mm. Bulk 3 x 4.7 uF + 1 uF (C63). OK.
  Thermal starved em U7.6/69/89 (GND) - **MEDIO**: pads GND do LQFP com conexao solida ou vias GND
  dedicadas a < 1 mm.
- VOS1 (clock.h) com SMPS direto: a saida do SMPS em VOS1 e ~1.2 V(DS permite SMPS direto ate VOS1;
  VOS0 exige LDO). OK.

### A.4 Reset / Boot
- NRST: C38 100 nF (106.74,74.11, B.Cu) a 6.54 mm do pino 27; a rede NRST percorre 39 mm em In1 e passa
  sob Y1 (105.45, 64.4-73.0). Pull-up interno 30-50 k, J1.10 leva NRST ao SWD. **MEDIO**: mover C38
  para < 2 mm do pino 27 (104.75,68.9 B.Cu) e rotear curto em B.Cu; retirar NRST de In1 sob o cristal.
- BOOT0: R14 10 k para GND (113.56,58.10, F.Cu) a 7.63 mm do pino 135; SW1 liga BOOT0 a +3V3
  (SKQG). OK: BOOT0 baixo em operacao normal; DFU do panda e feita por comando USB -> bootstub salta
  para 0x1FF09804 (system memory) sem depender de BOOT0; SW1 e o caminho de recuperacao manual.
  **BAIXO**: R14 a < 3 mm do pino; adicionar 100 nF em BOOT0 (imunidade a ruido durante power-up).

### A.5 Cristal Y1 25 MHz 3225 (X322525MOB4SI, CL = 12 pF)
- Capacitores C23/C24 15 pF: CL_eff = 15/2 + Cstray(~3-4 pF) = 10.5-11.5 pF vs 12 pF nominal -> desvio
  de frequencia +~10-20 ppm e drive um pouco alto. **BAIXO**: usar 18 pF (CL_eff ~12-13 pF) ou medir.
- Trilhas HSE_IN 9.55 mm / HSE_OUT 8.89 mm (skew 0.66 mm), B.Cu, 0 vias: OK. Y1.1 -> pino 25 4.61 mm,
  Y1.3 -> pino 26 3.2 mm: aceitavel (< 10 mm). Distancia > 5 mm do pino nao e ideal; manter.
- Sinais sob o cristal (bbox 103.4-107.6 x 69.3-72.7, Y1 em B.Cu): em F.Cu passam LED_RED, LED_GREEN,
  RED-/GREEN-/BLUE- e +3V3 (U5 LED fica em 104.03,70.18 exatamente oposto ao cristal); em In1 passam
  NRST e LED_RED. Planos GND em In2/F/B sob o cristal. **MEDIO**: os LEDs sao PWM (comutacao) a 1.6 mm
  do cristal atraves do laminado; mover U5/R17-R19 ou Y1 (ex. Y1 para 100.5,66.0 B.Cu) e retirar NRST/
  LED_RED de In1 nessa regiao; adicionar anel GND com 4 vias em volta de Y1.
- Sem LSE (nao usado pelo panda). HSE bypass nao usado. OK.

### A.6 Sequenciamento / protecoes
- D1 SMAJ16CA (131.2,49.8) em +12V a 12.8 mm de P1.A4 via 1.5 mm F.Cu: OK (Vbr 17.8 V, Vclamp 26 V @
  23 A). **BAIXO**: mover para junto de P1/Q4.
- Polaridade reversa: Q4 HY12P03C2 (-30 V, +-20 V Vgs, 10 mohm) como P-FET ideal diode com gate em
  GND por R1 1 k. Problemas: dissipacao de R1 (B4) e Vgs sem limite (B5). Sem fusivel - igual ao black
  panda (harness protege). **BAIXO**: prever PTC 3 A 1812 em +12V (opcional, nao presente no original).
- Inrush: sem controle (gate instantaneo). Cin + 108 mm2 de zona: inrush limitado pelo cabo. BAIXO.
- AP22615 (U1): R27 2.4 k -> ILIM = 5000/2.4 = 2.08 A (faixa 0.4-4 A). Adequado para porta USB-A 5 V;
  acima do que a trilha +5V suporta (B3). EN via Q3 (PDTC114EU) comandado por PB14 (USB_LOAD) com R26
  10 k; FLG com R9 10 k para +5V (nao vai ao MCU - flag de falha nao lida). C34 100 nF a 3.19 mm de U1.1.
  D10 BAS70H (USB_PWR -> +5V) permite retroalimentar +5V a partir do USB_PWR quando o cabo USB fornece
  5 V (modo "alimentado pelo host"): BAS70H e 70 mA - **MEDIO**: se a intencao e alimentar o MCU pelo
  USB sem 12 V, 70 mA e insuficiente para MCU + 4 transceptores (~0.6 A); usar Schottky 1 A (ex. B130)
  ou remover.
- D13/D14 BAT54S: grampo duplo (GND/+3V3) das entradas ADC SBU1_ADC/SBU2_ADC apos R28/R29 10 k. OK
  (I_clamp max = (12-3.3)/10 k = 0.9 mA quando o harness aplica 12 V no SBU).

---------------------------------------------------------------------------------------------------

## B. Integridade de sinal

### B.1 USB 2.0 Full-Speed (porta USB-A U3 <-> PA11/PA12)
- Topologia: U3.2/3 -> USB_R_D-/D+ (17.5 / 17.5 mm, F.Cu, 0.2 mm, gap c-c 0.45 mm = acoplado, skew 0)
  -> R20/R21 22 R (122.49,48.20) -> USB_D-/D+ (19.4 / 21.5 mm, 5 vias no total, 4 camadas, gap mediano
  2.27 mm = desacoplado) -> U7.100/101. Comprimento total ~37-39 mm, skew 2.1 mm (FS tolera, mas
  desnecessario). Z_diff estimada do trecho acoplado: 0.2 mm / gap 0.45 mm sobre preg 0.2 mm -> ~85-90
  ohm (alvo 90). **ALTO** (B6): os resistores devem estar a < 3 mm dos pinos do MCU (sao terminacao
  serie do driver), o par deve ser acoplado em toda a extensao e com <= 1 troca de camada.
- Vias USB: 5 vias (0.7/0.3 e 0.5/0.3) com via GND mais proxima a 0.85-5.95 mm; a via em (124.01,46.63)
  esta a 5.95 mm de qualquer via GND -> retorno interrompido. Trechos em In2 (12.6 + 5.4 mm) cortam o
  plano GND que e referencia dos demais sinais.
- ESD: nenhum dispositivo nas linhas D+/D- do USB-A (o black panda tambem nao tem, mas o conector USB-A
  e exposto). **ALTO** (B6): adicionar PRTR5V0U2X (SOT-143B) ou USBLC6-2SC6 junto a U3.
- VBUS: nao ha divisor para deteccao de VBUS (firmware red panda usa BVALOEN/BVALOVAL forcando
  B-valid - nao requer sensing). OK.
- CC1/CC2: P1 e o conector do harness (nao USB) - A5/B5 nao conectados, coerente com o black panda.
  OK.
- Blindagem: U3.5/6 (shell) nao conectados e com DRC copper_edge (140.84,46.23 / 140.84,33.33).
  **MEDIO**: ligar shell a GND via 1 nF 2 kV + 1 M em paralelo (ou direto, como no black panda), e
  afastar U3 >= 0.3 mm da borda ou editar o footprint.

### B.2 Barramentos CAN (TJA1042TK/3 x4)
| Bus | Xcvr -> conector | Len H/L (mm) | Skew | Gap c-c med/min | Larguras | ESD -> P1 |
|-----|------------------|--------------|------|-----------------|----------|-----------|
| BUS0 (FDCAN1 PB8/PB9) | U11 (134.98,70.37) -> P1.B11/B10, 7.7 mm | 8.96 / 10.12 | 1.16 | 0.65 / 0.30 | 0.15 + 0.2/0.25 | D9 3.8 mm |
| BUS1N (FDCAN2 PB5/PB6) | U10 -> P1.B2/B3, 12.7 mm | 19.01 / 20.72 | 1.71 | 0.80 / 0.32 | 0.15 + 0.25 | D8 9.2 mm |
| BUS1O (FDCAN2 PB12/PB13) | U8 (127.12,61.51) -> P1.A2/A3, 5.7 mm | 12.06 / 13.83 | 1.77 | 0.84 / 0.50 | 0.15 + 0.175/0.25 | D6 2.05 mm |
| BUS2 (FDCAN3 PG9/PG10) | U9 -> P1.A11/A10, 6.1 mm | 7.59 / 6.46 | 1.13 | 0.65 / 0.43 | 0.15 + 0.25 | D7 3.07 mm |

- Todos os pares em F.Cu, 0 vias: bom. Larguras misturadas (0.15 mm em um lado, 0.2-0.25 no outro)
  violam a netclass CAN_DIFF (0.25 / gap 0.2) e dao assimetria de Zodd. **MEDIO**: uniformizar 0.25 mm,
  gap 0.2-0.25 mm, skew < 0.5 mm. Para CAN-FD 2-5 Mbit/s o stub de 6-13 mm e irrelevante (< 1% do
  comprimento de onda); o skew de 1-1.8 mm equivale a ~10 ps - desprezivel, mas o ganho esta em
  rejeicao de modo comum/EMI.
- PESD2CAN: D8 (BUS1N) a 9.2 mm de P1.B2 e D5 (SBU) a 10.4 mm de P1.A8 - **MEDIO**: ESD deve ficar a
  < 3 mm do conector, antes do transceptor, com pad GND solido (D6.3 tem thermal starved -> retorno ESD
  por 2 spokes de 0.5 mm; usar conexao solida).
- Terminacao: nenhuma (correto: o panda e no de rede, a terminacao esta no veiculo). OK.
- STB (pino 8) de cada TJA1042: pull-up 10 k R30-R33 para +3V3 + GPIO (PG11/PB3/PD7/PB4) -> standby ate o
  firmware liberar (red_enable_can_transceiver). OK e igual ao red panda.
- VIO (pino 5) = +3V3 em todos: correto para o /3 (nivel logico 3.3 V).
- VCC (pino 3) = +5V com 100 nF a 1.86-2.11 mm cada: OK. Decoupling de VIO nao previsto (DS recomenda
  100 nF em VIO): **BAIXO**.
- TXD/RXD: comprimentos ate 25-31 mm com trechos em In2/In1 (BUS1N_RX/TX, BUS1O_RX/TX, BUS0_TX,
  BUS1N_STB cortam o plano GND em In2 por 16-26 mm cada). Sinais de 2-5 Mbit/s com bordas de ~10 ns:
  eletricamente OK, mas cada corte em In2 remove retorno de outros sinais. **MEDIO** (ver B.4).
- Mapa do conector (P1 TYPE-C 16 pinos como harness, igual ao black panda): A2/A3 BUS1O, A4/A9/B4/B9
  +12V, A8/B8 SBU1/SBU2, A10/A11 BUS2, B2/B3 BUS1N, B10/B11 BUS0, A1/A12/B1/B12 GND; A5-A7/B5-B7 NC.
  Coerente com o harness comma (CAN0 = B10/11, CAN1 obd/normal = A2/A3 + B2/B3, CAN2 = A10/A11).

### B.3 SWD, LED, straps, ADC harness
- SWD J1 (B.Cu 99.13,38.07): SWDIO 16 mm e SWCLK 18 mm em In2 (cortam plano). Sem pull-ups externos
  (internos no H7 OK). NRST em J1.10. **BAIXO**.
- HW_TYPE: PF7-PF10 (pinos 21-24) em GND -> id1 = 0 -> HW_TYPE_RED_PANDA; PD4-PD6 NC, PD7 = STB com
  pull-up -> id2 = 0xF (nao e cuatro). Coerente com board.h.
- SBU: SBU1 = P1.A8 -> R24 10 k pull-up 3V3, Q2 (DDTA143ECA, relay_SBU1 PC10) injeta +5V, R28 10 k ->
  SBU1_ADC (PC4, ADC1_INP4) com D13 BAT54S; SBU2 = P1.B8 -> R23/Q1/R29 -> PA1 (ADC1_INP17) com D14.
  Igual ao red panda (adc_signal_SBU1 = ADC1 ch4, SBU2 = ADC1 ch17). Impedancia de fonte 10 k: o
  firmware red ja usa tempo de amostragem longo. OK.
- VoltageSens: R3 10 k (12V_Protected) / R2 1 k (GND) -> PF11 (ADC1_INP2) x 11 = igual a
  red_read_voltage_mV (ADC1 ch2 * 11). OK. R3 0402 dissipa 13-20 mW: OK.
- 5VOUT_S: R15/R16 10 k / 10 k -> PB1 (ADC1_INP5): igual ao red (PB1 analogico). OK.
- LED: PE4/PE3/PE2 -> R19 100 R / R18 110 R / R17 180 R -> U5 FM-B1921RGBA: igual ao red (led_pin
  {4,3,2}). Correntes ~10-15 mA. OK. SBU1_ADC (30.5 mm) e SBU2_ADC (20 mm) em In2 e LED_BLUE 23 mm em
  In2 - mover para camadas externas.
- Pinos nao usados do MCU: deixados NC (firmware configura como analogico/pull-down em
  common_init_gpio). OK.

### B.4 Integridade de GND
- Plano In2: 1867.7 mm2 (79%) em 3 contornos; porem 337 mm de trilhas nao-GND em In2 (+3V3 31,
  SBU1_ADC 30.5, BUS1O_RX 26, BUS1N_RX 25, BUS1N_STB 25, 12V_Protected 24.5, BUS1O_TX 24, LED_BLUE 23,
  SBU2_ADC 20, SWCLK 18, SWDIO 16, BUS0_TX 16, USB_D+ 12.6, +12V 8.6, USB_D- 5.4 ...) e 290 mm em In1
  (NRST 39, BUS1N_TX 31, +5V 30, relay_SBU1/2 29+29, SBU2 25, 12V_Protected 23, LED_GREEN 20, VCAP 16,
  USB_LOAD 12). Cada trilha em In2 abre uma fenda de ~0.45 mm no plano de referencia de F.Cu/B.Cu.
  **MEDIO**: politica "In2 = GND exclusivo"; mover esses sinais para F/B.Cu (ha espaco: ocupacao de
  F/B < 50%).
- Zonas GND: F.Cu 1337.9 mm2 em 21 contornos, B.Cu 1491.8 mm2 em 15, In1 1025 mm2 em 43 contornos ->
  muitas ilhas pequenas; ilhas sem via sao antenas. **BAIXO**: habilitar "remove islands < 5 mm2" ou
  adicionar via em cada ilha.
- Vias de costura: 73 vias GND, vizinho mais proximo mediano 1.87 mm, maximo 10.25 mm. Para 25 MHz
  (lambda/20 ~ 30 cm) OK; para bordas de 1 ns dos LEDs/CAN-FD o alvo pratico e <= 5 mm. **BAIXO**:
  adicionar ~15 vias GND nas regioes com NN > 5 mm (lado direito, x > 130) e ao longo das trocas de
  camada dos sinais.
- Thermal starved (17, DRC fresco): U6.9 EP x3 (107.41,40.19 / 108.71,40.19 / 107.41,44.09), P1 pad 0
  GND x2 (136.18,54.75), P1.B1 (135.59,56.08), P1.A1 (134.38,61.63), C10.1 (110.58,47.33), C28.2
  (141.91,70.04), C52.2 (102.95,42.86), U9.2 (125.47,54.92), C46.2 (113.05,70.34), U7.6 (115.75,67.26),
  U7.69 (98.84,49.35), U7.89 (108.75,45.94), D6.3 (130.07,62.46), C40.2 (124.24,63.35). Risco: pads
  GND com 1 spoke (de 4) -> alta indutancia de retorno (D6 ESD, C40 VCAP, C46/C52 decoupling, U7
  VSS) e, no EP de U6/P1, dissipacao termica deficiente. **MEDIO**: (a) zona GND: `thermal_gap` 0.5 ->
  0.3 mm, `thermal_bridge_width` 0.5 -> 0.4 mm; (b) conexao solida (pad override) em U6.9, P1 pads
  GND, D5-D9 pino 3, C39/C40/C41/C42 pad 2; (c) para U7 VSS, via GND dedicada a < 1 mm de cada pad.
- Retorno sob USB e CAN: pares CAN em F.Cu sobre In1 (zona +3V3 / sinais) a 0.2 mm e In2 GND a 1.3 mm
  -> a referencia dominante e In1 (+3V3) na regiao do MCU; fora do MCU, In1 e fragmentado (43
  contornos). Aceitavel para CAN; para USB, os trechos em In2 nao tem referencia continua. Ver B6.

### B.5 EMI
- No SW do TPS5450 (rede L4): 57.9 mm2 de cobre, trilha 2.0 mm x 11.75 mm ate L4, zona 7.2 mm2.
  dV/dt ~ 12 V / 20 ns. **MEDIO**: encolher para < 15 mm2: mover L4 para ~(112.5,38.5) junto ao PH, D12
  com catodo encostado em PH (laco PH-D12-GND < 40 mm2), C37 com retorno direto em PH.
- Laco de entrada: Cin a 2-4 mm, GND dos Cin via zona F.Cu ate EP (5.9 mm): OK-ish; melhora com 10 uF.
- XL1509 SW: 19 mm2 / 150 kHz: OK.
- SMPS interno H7 (VLXSMPS, 4 mm2, 7.9 mm): C41 220 pF longe (4.93 mm) - mover (A.3).
- LED RGB U5 colado ao cristal (lado oposto) - A.5.
- Cabo USB: sem ferrite/ESD em D+/D-; shell de U3 flutuante - B.1. **BAIXO**: prever ferrite 0603 em
  USB_PWR (opcional).
- Cabo harness (P1): CAN sem choke de modo comum (igual ao black panda). BAIXO: footprint opcional
  para ACT45B.

---------------------------------------------------------------------------------------------------

## C. Revisao de esquematico (netlist) e requisitos para firmware hibrido

### C.1 Pinos de CI por datasheet
- U7 STM32H725ZGT6: todos VDD/VSS/VDDA/VSSA/VBAT/VDDLDO/VDD33USB/VDD50USB/PDR_ON/VDDSMPS ligados;
  VLXSMPS/VFBSMPS com L5/C41/C42; **VFBSMPS nao ligado a VCAP (CRITICO)**; VCAP x3 interligados;
  NRST/BOOT0 OK; HSE PH0/PH1 OK; PF7-10 strap GND OK.
- U6 TPS5450: 1 BOOT C37, 4 VSENSE divisor, 5 ENA NC (OK), 6/9 GND, 7 VIN, 8 PH, 2/3 NC. OK.
- U12 XL1509-3.3: ver A.2.
- U1 AP22615: 1 OUT, 2 GND, 3 FLG (R9 10 k -> +5V), 4 EN (Q3 -> +5V via R26 10 k; EN ativo alto
  AP22615AW... confirmar variante "AWU-7" = EN ativo alto; se fosse AL = ativo baixo o load switch
  ficaria invertido), 5 ISET R27 2.4 k, 6 IN +5V. **BAIXO**: confirmar variante.
- U8-U11 TJA1042TK/3: 1 TXD, 2 GND, 3 VCC 5 V, 4 RXD, 5 VIO 3V3, 6 CANL, 7 CANH, 8 STB. OK.
- U5 LED: anodo comum em +3V3 (pino 1), catodos via R17-R19. OK.
- D5-D9 PESD2CAN: pino 3 GND. OK (thermal starved em D6.3).
- Q1/Q2 DDTA143ECA (PNP digital, R1 4.7 k): base = relay_SBU PC10/PC11, emissor +5V, coletor SBU.
  Igual ao red panda. OK.
- J1 SWD 2x5 1.27 mm: 1 VCC 3V3, 2 SWDIO, 4 SWCLK, 10 NRST, 3/5/9 GND, 6/7/8 NC. OK.
- P1: A5/B5 (CC), A6/A7/B6/B7 (USB D) NC: OK para harness.

### C.2 Mapa de pinos: placa vs firmware red panda (hardware\reference\panda\board)

| Funcao | Pino H725 na placa (netlist) | Pino no red panda (firmware) | Acao |
|--------|------------------------------|------------------------------|------|
| FDCAN1 RX / TX (BUS0) | PB8 (136) / PB9 (137) | PB8 / PB9 AF9 (peripherals.h) | nenhuma |
| FDCAN2 RX / TX normal (BUS1N) | PB5 (132) / PB6 (133) | PB5 / PB6 AF9 | nenhuma |
| FDCAN2 RX / TX OBD (BUS1O) | PB12 (72) / PB13 (73) | PB12 / PB13 AF9 (red_set_can_mode) | nenhuma |
| FDCAN3 RX / TX (BUS2) | PG9 (122) / PG10 (123) | PG9 / PG10 AF2 | nenhuma |
| STB xcvr CAN0/1N/2/1O | PG11 (124) / PB3 (130) / PD7 (121) / PB4 (131) | G11, B3, D7, B4 (red_enable_can_transceiver) | nenhuma |
| USB OTG_HS (FS PHY) DM / DP | PA11 (100) / PA12 (101) | PA11 / PA12 AF10 | nenhuma |
| SBU1 / SBU2 ADC | PC4 (47) ADC1_INP4 / PA1 (38) ADC1_INP17 | ADC1 ch4 / ch17 (red_harness_config) | nenhuma |
| relay_SBU1 / relay_SBU2 | PC10 (109) / PC11 (110) | PC10 / PC11 | nenhuma |
| LED R/G/B | PE4 (3) / PE3 (2) / PE2 (1) | GPIOE 4/3/2 | nenhuma |
| VoltageSens (x11) | PF11 (52) ADC1_INP2 | ADC1 ch2 * 11 (red_read_voltage_mV) | nenhuma (divisor 10k/1k = 11) |
| 5VOUT_S | PB1 (50) | PB1 analogico (red_init) | nenhuma; firmware red nao le - opcional em hibrido |
| USB_LOAD (EN AP22615 via Q3) | PB14 (74) -> Q3 PDTC114EU (B=PB14, E=GND, C=EN/R26 10 k->+5V) | PB14 open-drain + PULL_UP, nivel 1 ("obsoleto no red") | **firmware hibrido**: com open-drain=1 o pino fica em Hi-Z com pull-up interno (~40 k); Vbase = 3.3 * 10/(40+10+10) ~ 0.55 V -> Q3 no limiar (pode conduzir com temperatura) -> EN para GND -> USB_PWR DESLIGADO. Definir PB14 push-pull = 0 para porta ligada (EN = +5V via R26) e = 1 para desligar; expor no USB control (como o black panda) |
| HW_TYPE strap | PF7-PF10 (21-24) = GND; PD4-PD6 NC | id1 = 0 -> RED_PANDA | nenhuma |
| SWD | PA13 (102) / PA14 (107) | padrao | nenhuma |
| HSE | PH0 (25) / PH1 (26) 25 MHz | HSE 25 MHz (clock.h) | nenhuma |
| NRST / BOOT0 | pino 27 / pino 135 | padrao | nenhuma |
| Esquema de alimentacao | SMPS direto (VDDSMPS=3V3, L5) **sem VFBSMPS->VCAP** | SMPSEN (LQFP144) | **hardware**: ligar VFBSMPS a VCAP (B1). Firmware: nenhuma |
| FLG do AP22615 | nao vai ao MCU | red nao usa | nenhuma |
| SPI (tres/cuatro) PE11-PE14 | nao usados | nao usado no red | nenhuma |
| Fan / IR / siren / bootkick | ausentes | unused_* no red | nenhuma |

Resultado: nenhuma divergencia de pino entre a placa e `red.h`/`peripherals.h`. Requisitos para o
firmware hibrido: (1) PB14 (USB_LOAD): o red deixa open-drain=1 com pull-up, o que coloca Q3 no limiar
e tende a DESLIGAR a porta USB-A; o firmware hibrido deve configurar PB14 push-pull e nivel 0 por
padrao (porta ligada), com comando USB para desligar (nivel 1), como no black panda; (2) opcional: expor 5VOUT_S
(PB1) na telemetria; (3) nenhum ajuste de ADC/CAN/USB necessario.

---------------------------------------------------------------------------------------------------

## D. Manufaturabilidade (vs JLCPCB 4 camadas padrao: trilha/espaco 0.09/0.09 mm (recomendado
0.127), via furo >= 0.2 (recomendado 0.3) / anel >= 0.13 mm, furo-cobre 0.254 mm, cobre-borda 0.3 mm)

| Item | Medido | Veredito |
|------|--------|----------|
| Trilha minima | 0.14 mm (0.3 mm de trilha), 0.15 mm (134 mm), 0.2 mm (1324 mm) | OK (>= 0.127). BAIXO: substituir os 0.14/0.15 por 0.15/0.2 |
| Clearance minima | regra 0.05 mm (netclass 0.1) | **MEDIO**: regra de placa 0.05 mm esta abaixo da capacidade (0.09); subir `min_clearance` para 0.1 mm e re-rodar DRC |
| Vias | 0.5/0.3 (anel 0.10), 0.6/0.3 (0.15), 0.7/0.3 (0.20), 1 via 0.45/0.25 em (104.12,50.94) GND | **MEDIO**: via 0.45/0.25 viola a regra (drill_out_of_range) e anel 0.10 esta abaixo do recomendado 0.13 -> usar 0.56/0.3 ou 0.6/0.3 em todas as 66 vias 0.5/0.3 |
| Hole clearance | 8 erros P1: PTH GND (136.18,54.75 / 136.18,63.01) vs NPTH (134.94,55.20 / 134.94,62.55), 0.144 mm | **MEDIO**: geometria do footprint TYPE-C-31-M-04 (herdado). Fab aceita >= 0.254 mm furo-furo; editar footprint: reduzir NPTH ou mover PTH 0.15 mm, ou aceitar com nota ao fabricante (risco de rompimento) |
| Cobre-borda | U3 pads 5/6 (140.84,46.23 / 140.84,33.33) tocam Edge.Cuts | **MEDIO**: deslocar U3 0.4 mm para -x ou recortar o contorno; shell de U3 esta NC |
| LQFP144 0.5 mm | pads 0.3 x 1.5; escape em B.Cu com 0.15-0.2 mm | OK |
| DFN/EP pasta | U6 EP (PowerPAD): verificar mascara de pasta 50-70%; U7 sem EP; TJA1042 HVSON8? (TK = HVSON8 com EP GND) | **BAIXO**: confirmar EP dos TJA1042TK ligado a GND (netlist mostra pad 9? nao listado) -> se footprint nao tem EP, trocar para HVSON-8 com EP |
| Silkscreen | 4 silk_overlap, 4 silk_edge, 72 text_height (< 0.8 mm) | BAIXO: limpar antes dos gerbers |
| Footprint mismatches | 64 lib_footprint_mismatch, 10 footprint_type_mismatch (THT vs SMD) | BAIXO: atualizar da biblioteca / corrigir atributo |
| Capacitores 0402 100 nF | 25+ | OK para montagem JLC |

---------------------------------------------------------------------------------------------------

## Lista consolidada por severidade

CRITICO
1. VFBSMPS nao ligado a VCAP (B1) - MCU nao liga com firmware red (SMPS direto).
2. Pino VCAP 103 sem capacitor; rede VCAP longa (B2).

ALTO
3. +5V -> U1.6 subdimensionado (via unica, 0.35 mm 0.5 oz, 0.2 mm) para ILIM 2.08 A (B3).
4. R1 1 k 0402 no gate de Q4 sobre-dissipado (B4).
5. Vgs de Q4 sem limite (B5).
6. USB: sem ESD, 22 R longe do MCU, par desacoplado com 5 vias e trechos em In2 (B6).
7. Cin do TPS5450 insuficiente (B7).
8. 4.7 uF ausente junto a VDDSMPS pino 16 (A.3).

MEDIO
9. +5V -> U12 em 0.2 mm; USB_PWR 0.6 mm (A.1).
10. Cout do TPS5450 100% ceramico (A.2).
11. Pad termico U6 com 3 vias e thermal starved (A.2).
12. No SW do TPS5450 grande / L4 a 11.75 mm (B.5).
13. C41 220 pF e C42 10 uF longe dos pinos SMPS (A.3).
14. C40.2/D6.3/U7 VSS/decoupling com thermal starved (B.4).
15. NRST C38 a 6.5 mm e NRST em In1 sob o cristal (A.4).
16. LED RGB e sinais PWM sob o cristal (A.5).
17. D10 BAS70H 70 mA como retroalimentacao +5V (A.6).
18. Shell de U3 flutuante + copper_edge (B.1).
19. CAN: larguras assimetricas 0.15/0.25; D8/D5 ESD longe de P1 (B.2).
20. 337 mm de sinais em In2 / 290 mm em In1 (B.4).
21. Regras: min_clearance 0.05 mm; via 0.45/0.25; anel 0.10 (D).
22. P1 hole_clearance x8 (D).

BAIXO
23. Paralelos +12V/12V_Protected em In1/In2; R6 footprint C_0603; BOOT return; C23/C24 15 -> 18 pF;
    D1 longe de P1; VIO sem 100 nF; 100 nF em BOOT0; ilhas GND; costura > 5 mm; silk/text; variante
    AP22615 (EN ativo alto) e logica PB14.

## Scripts
- `si_pi_dump.py`: extracao read-only via pcbnew (KiCad 10 python). Saida `si_pi_dump.json`,
  `power_nets.json`. Execucao: `"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\python.exe" -u si_pi_dump.py`.
- `drc_audit.json`: `kicad-cli pcb drc --format json --severity-all --units mm`.
