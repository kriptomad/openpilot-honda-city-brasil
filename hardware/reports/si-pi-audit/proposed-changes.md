# Alteracoes propostas (ordem de aplicacao) - auditoria SI/PI Hybrid Panda

Coordenadas em mm no sistema da placa (`HybridPanda.kicad_pcb`, contorno 91.91..142.535 x 32.01..78.76).
U7 esta em B.Cu (109.5,56.6, rot 90). Nenhuma alteracao foi aplicada nesta auditoria. Cada item traz
rede, componente, valor e posicao suficientes para um script (pcbnew / edicao s-expression do .kicad_sch).
Re-rodar DRC + ERC + netlist apos cada bloco.

## Bloco 1 - Esquematico (CRITICO / ALTO)

1. **Unir redes VFBSMPS e VCAP** (CRITICO). `.kicad_sch`: renomear o label/rede `VFBSMPS` (em C42.1,
   L5.2, U7 pino 17) para `VCAP` ou adicionar fio/label `VCAP` no no de C42.1. Resultado esperado na
   netlist: VCAP = {C39.1, C40.1, C42.1, L5.2, U7.17, U7.68, U7.103, U7.140}. Manter C42 10 uF (Cout1
   do SMPS, ESR <= 20 mohm, X7R 0805 10 V).
2. **Adicionar C64 2.2 uF 0603 X7R 10 V (ESR < 100 mohm)** entre VCAP e GND, associado ao pino U7.103.
   PCB: posicao (116.1,44.5) B.Cu, rot 90; pad 1 -> U7.103 (115.75,45.94) trilha 0.3 mm; pad 2 -> via GND
   0.5/0.3 em (116.1,43.3).
3. **Adicionar C65 4.7 uF 0603 X5R 10 V** entre +3V3 e GND junto a VDDSMPS U7.16 (110.75,67.26).
   PCB: (110.75,69.1) B.Cu, rot 90; pad 1 -> pino 16 trilha 0.3 mm (1.5 mm); pad 2 -> via GND
   (110.75,70.3)... atencao: L5 ocupa (110.75,70.26) -> colocar C65 em (112.0,69.1) e ligar ao pino 16
   com 0.3 mm, via GND em (112.6,69.1).
4. **R1 1 k -> 10 k, footprint R_0402 -> R_0603** (gate de Q4). Rede Net-(D2-A). Posicao (133.98,52.40).
5. **Adicionar D15 zener 12 V SOD-123 (BZT52C12)**: catodo em 12V_Protected (source Q4.1/2/3), anodo em
   Net-(D2-A) (gate Q4.4). PCB: (136.6,52.6) F.Cu ao lado de R1; trilhas 0.3 mm.
6. **Cin do TPS5450**: C4 e C12 2.2 uF 0805 -> 10 uF 1206 X7R 50 V (footprint C_1206); manter C6/C7
   2.2 uF 50 V. Posicoes mantidas em x = 113.635 (y 37.85 e 43.90); ajustar courtyard.
7. **R6 3.16 k**: footprint `Capacitor_SMD:C_0603_1608Metric` -> `Resistor_SMD:R_0603_1608Metric`
   (105.81,45.64).
8. **Adicionar U13 ESD USB (USBLC6-2SC6 SOT-23-6 ou PRTR5V0U2X SOT-143B)**: I/O1 = USB_R_D-, I/O2 =
   USB_R_D+, VBUS = USB_PWR, GND. PCB: (133.2,42.2) F.Cu junto a U3.2/3 (pads USB-A em ~ (135.5-137.5,
   40-42)); trilhas de 0.2 mm em serie (flow-through), sem stubs > 1 mm.
9. **D10 BAS70H** (USB_PWR -> +5V, 70 mA): decidir funcao. Se o MCU deve ligar so com USB (sem 12 V):
   substituir por Schottky 1 A (B130 SMA/SOD-123F, ex. PMEG2010ER). Caso contrario: remover (DNP).
10. **Opcional**: 100 nF 0402 em BOOT0 (U7.135) para GND junto a R14; 100 nF em VIO (pino 5) de cada
    TJA1042 (U8-U11).

## Bloco 2 - PCB potencia (ALTO / MEDIO)

11. **+5V -> U1.6 (AP22615 VIN, 117.17,54.38)**: remover trilhas In1 1.0 mm e 0.35 mm entre a via
    (120.28,46.70) e a via (116.50,54.95) e a trilha F.Cu 0.2 mm ate U1.6. Nova rota em F.Cu, largura
    1.0 mm: da zona +5V/C21.1 (118.5,47.8) -> (118.9,50.5) -> (117.6,53.6) -> U1.6. Se houver conflito
    com R9/D10 (119.8-120.9, 51.7-57.5), alternativa: 2 vias 0.6/0.3 em (119.0,48.9) e (119.6,48.9) +
    In1 2.0 mm ate 2 vias 0.6/0.3 em (116.3,55.6)/(116.9,55.6).
12. **+5V -> U12.1 (99.64,44.13)**: alargar os 3 segmentos F.Cu de 0.2 -> 0.5 mm: (112.37,45.75)->
    (109.86,45.54); (108.53,46.52)->(101.62,46.52); (101.62,46.52)->(99.64,44.55). Verificar clearance com
    C10 (109.63,47.33) e R5 (108.31,45.39).
13. **USB_PWR**: alargar trilha U1.1 (118.3,52.5) -> C17/U3.1 de 0.6 -> 1.0 mm em todo o trajeto.
14. **+3V3 saida L3.2/C16**: alargar 0.2 -> 0.4 mm nos segmentos F.Cu entre L3.2 (97.25,36.0), D11.2
    (97.26,41.27) e C16.1 (93.47,44.86) ate a zona +3V3.
15. **Pad termico U6.9 (TPS5450, 108.06,42.14)**: adicionar vias GND 0.6/0.3 em (107.41,42.14),
    (108.71,42.14), (108.71,44.09), (108.06,41.2), (108.06,43.1) (total 8); conexao de zona = solida
    (pad override `thermal_relief` -> `solid`) em F.Cu, In1, In2, B.Cu.
16. **No SW do TPS5450 (rede L4)**: mover L4 (121.19,39.58) para (113.5,37.9) (rot 0) se C4/C6 forem
    realocados para x = 116.0; ou, minimamente, substituir a trilha 2.0 mm x 11.75 mm por poligono
    minimo e apagar a zona SW 7.2 mm2; D12 (106.87,35.87) -> (109.3,38.6) rot 90 com catodo em PH; C37.2
    -> PH direto com 0.3 mm (<2 mm).
17. **Remover trilhas paralelas de potencia em camadas internas** (cortam planos): +12V In2 0.2 mm
    (138.55,53.19)->(135.69,53.19)->(134.09,54.79)->(134.09,56.18)->(135.59,57.68); 12V_Protected In1 (23
    mm) e In2 (24.5 mm) 0.2 mm; +5V In1 30 mm (substituido pelo item 11). Verificar DRC unconnected = 0.

## Bloco 3 - PCB MCU / sinais (ALTO / MEDIO)

18. **R20/R21 22 R (122.49/122.48, 48.20)**: mover para B.Cu a < 3 mm de U7.100 (PA11, 108.5,45.94) /
    U7.101 (PA12, 109.0,45.94): R20 em (108.4,44.0) rot 90, R21 em (109.2,44.0) rot 90. Lado MCU =
    USB_D-/D+ (0.2 mm, < 2.5 mm); lado conector = USB_R_D-/D+.
19. **Rotear USB_R_D-/D+ como par acoplado** 0.2 mm / gap 0.2 mm de R20/R21 ate U3.2/3 em UMA camada
    (B.Cu, referencia In2 GND), com no maximo 1 par de vias 0.5/0.3 (se necessario para chegar a F.Cu em
    U3) acompanhado de 2 vias GND a <= 1 mm. Remover todos os trechos de USB_D+/USB_D- em In1/In2
    (12.6 + 5.4 + 6.2 mm). Igualar comprimentos (skew < 0.5 mm). Passar pelo U13 (item 8).
20. **VCAP**: apos item 1/2, rotear VCAP em B.Cu 0.3 mm: C42.1 (109.43,73.70) -> U7.17 (110.25,67.26)
    (ja existe); U7.17 -> C40.1 (123.46,63.35) e U7.68 (98.84,49.85) -> C39.1 (95.63,50.36) ja existem;
    adicionar C64 (item 2) em U7.103; remover trecho VCAP em In1 (16 mm).
21. **C41 220 pF** (111.475,72.66) -> (111.6,68.9) B.Cu rot 90, pad 1 em U7.15 (111.25,67.26) com
    0.25 mm; **C42 10 uF** (109.43,73.70) -> (109.3,69.6) rot 90 se L5 permitir (L5 em 110.75,70.26, 2.0 x
    1.6 mm); caso contrario manter e encurtar a trilha para 0.4 mm.
22. **C38 100 nF (NRST)** (106.74,74.11) -> (104.6,68.9) B.Cu rot 90, pad 1 em U7.27 (104.75,67.26)
    com trilha < 2 mm; rerotear NRST ate J1.10 em B.Cu/F.Cu, removendo os 39 mm em In1 (passam sob Y1 em
    x = 105.45).
23. **Cristal Y1 / LED U5**: mover U5 FM-B1921RGBA (104.03,70.18) e R17/R18/R19 (102.66-104.68,
    67.45) para (99.0,76.0) F.Cu (regiao livre perto da borda inferior esquerda), rerotear LED_* em F.Cu
    (fora de In1/In2); OU mover Y1/C23/C24 para (100.8,65.5) B.Cu. Adicionar 4 vias GND 0.5/0.3 em
    volta de Y1 (cantos do bbox + 0.8 mm). Remover LED_RED In1 (112.35,64.40)->(107.71,69.04).
24. **C23/C24 15 pF -> 18 pF** (CL = 12 pF, Cstray ~3 pF). Confirmar com medida de frequencia no
    prototipo (alvo +-10 ppm).
25. **PESD2CAN D8** (BUS1N) -> junto a P1.B2/B3 em (133.0,55.0) F.Cu (hoje a 9.2 mm); **D5** (SBU) ->
    (132.6,59.9) junto a P1.A8/B8 (hoje 10.4 mm). Pad 3 (GND) com conexao solida e via GND a < 1 mm.
26. **Pares CAN**: uniformizar largura 0.25 mm e gap 0.2-0.25 mm em BUS0/1N/1O/2 (hoje 0.15 em um
    lado e 0.2/0.25 no outro); segmentos de 0.15 mm listados em `si_pi_dump.json["pairs"]`. Igualar
    comprimentos (skew < 0.5 mm) com pequeno meandro no lado curto.
27. **Politica In2 = GND**: mover para F.Cu/B.Cu os sinais em In2: +3V3 (31 mm), SBU1_ADC (30.5),
    BUS1O_RX (26), BUS1N_RX (25), BUS1N_STB (25), BUS1O_TX (24), LED_BLUE (23), SBU2_ADC (20), SWCLK (18),
    SWDIO (16), BUS0_TX (16); em In1: BUS1N_TX (31), relay_SBU1/2 (29+29), SBU2 (25), LED_GREEN (20),
    USB_LOAD (12). Lista completa de segmentos em `si_pi_dump.json["signal_lengths"]`.

## Bloco 4 - Zonas, vias, regras, fab (MEDIO / BAIXO)

28. **Zona GND (todas as camadas)**: `thermal_gap` 0.5 -> 0.3 mm, `thermal_bridge_width` 0.5 -> 0.4 mm,
    `min_thickness` 0.25 -> 0.2 mm; `remove_islands` = below_area 5 mm2. Pad overrides `solid`: U6.9,
    P1 pads GND (A1/A12/B1/B12 e pad 0), D5-D9 pad 3, C39/C40/C41/C42/C44/C46/C52 pad 2.
29. **U7 VSS**: adicionar via GND 0.5/0.3 a < 1 mm dos pads 6 (115.75,67.26), 69 (98.84,49.35), 89
    (108.75,45.94): em (115.75,68.9), (97.4,49.35), (108.75,44.5) com trilha 0.25 mm.
30. **Vias**: 66 vias 0.5/0.3 -> 0.6/0.3 (anel 0.15 >= 0.13 JLC); via (104.12,50.94) 0.45/0.25 -> 0.6/0.3;
    `via_min_annular` 0.05 -> 0.13; `min_clearance` 0.05 -> 0.1; `min_track` 0.1375 -> 0.127.
31. **Costura GND**: adicionar ~15 vias 0.5/0.3 onde o vizinho GND mais proximo > 5 mm (lado direito
    x > 130, y 32-50 e 64-78; regiao de L4/D12). Lista de posicoes derivavel de
    `si_pi_dump.json["gnd_vias"]`.
32. **P1 hole_clearance (8)**: editar footprint TYPE-C-31-M-04: NPTH (134.94,55.20)/(134.94,62.55) e PTH
    GND (136.18,54.75)/(136.18,63.01) -> aumentar a distancia furo-furo para >= 0.254 mm (reduzir NPTH de
    0.65 para 0.6 mm ou deslocar PTH 0.15 mm em +x), ou registrar desvio aceito com o fabricante.
33. **U3 copper_edge (2)**: deslocar U3 (136.445,39.78) 0.4 mm em -x ou estender o contorno 0.4 mm em
    +x nessa regiao; ligar shell U3.5/U3.6 a GND (direto, como no black panda, ou C 1 nF 2 kV // R 1 M).
34. **D1 SMAJ16CA** (131.2,49.8) -> (138.6,56.0) junto a P1.A4/B4 (ou manter com trilha 1.5 mm).
35. **Silk/texto**: corrigir 4 silk_overlap, 4 silk_edge, 72 text_height (< 0.8 mm -> 0.8/0.15 mm);
    atualizar 64 lib_footprint_mismatch / 10 footprint_type_mismatch.
36. **Cout do TPS5450**: trocar C21 47 uF 0805 por polimero 100 uF 6.3 V (case B/D, 7343) em
    (118.5,49.5) ou validar margem de fase com WEBENCH/medida antes da serie.

## Verificacoes apos aplicar
- Netlist: VCAP com 8 nos; VFBSMPS inexistente; ERC 0 erros.
- DRC: 0 unconnected, 0 starved_thermal, 0 hole_clearance, 0 copper_edge, 0 drill_out_of_range.
- `si_pi_dump.py` re-executado: `power_nets["+5V"].worst_segment_capacity_A` >= 2.3; USB pares com
  `vias_p + vias_n` <= 2 e gap c-c mediano <= 0.45; `u7_power_pins[103].nearest_cap` < 3 mm;
  `signal_lengths` In2 nao-GND = 0.
