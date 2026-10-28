# STEP 3 — Engenharia reversa do baseline (OpenBlackPanda F413) e tabela híbrida para STM32H725ZGT6

Fontes: `hardware\reports\baseline_BlackPanda_netlist.xml` (exportada com kicad-cli 10.0.7 de `archive\baseline-original\BlackPanda\kicad_project\BlackPanda.kicad_sch`), `hardware\research\from-v1\fase1-inventario.md`, `hrs-red-panda.md`, `p10-obdc-harness-sbu.md`, `hardware\scripts\firmware_pins.json`.
Verificador: `hardware\scripts\parity_check.py --profile black_f4` sobre o baseline → **35/35 OK, 0 divergências** (`hardware\reports\parity-black-f4-baseline-blackpanda-netlist.md`) — prova de que o método reconhece um projeto que o firmware legado aceita. **[F]**
Legenda: **[F]** fato · **[I]** inferência · **NV** não verificado.

---
## (a) Periférico × pino F413 (baseline) × pino exigido pelo firmware no H725 × rede

| Função firmware | F413 pino (pad) | Rede no baseline | Componente destino | H725 pino (LQFP144 pad) | Rede proposta (hardware) | Fonte H7 |
|---|---|---|---|---|---|---|
| USB D− / D+ | PA11 (44) / PA12 (45) | USB_D− / USB_D+ | R20/R21 22 Ω → U3 USB-A | PA11 (100) / PA12 (101) | USB_D− / USB_D+ | peripherals.h:8-9 |
| bus0 CAN RX/TX (xcvr 1) | PB8 (61) / PB9 (62) — CAN1 | CAN2_RX / CAN2_TX | U11 TJA1042 → P1 B10/B11 | PB8 (136) / PB9 (137) — FDCAN1 AF9 | BUS0_RX / BUS0_TX | peripherals.h:31-32 |
| bus0 STB | PC1 (9) | CAN2_EN | U11 STB | PG11 (124) | BUS0_STB | red.h:11 |
| bus1 normal RX/TX (xcvr 2) | PB5 (57) / PB6 (58) — CAN2 | CAN3_RX / CAN3_TX | U10 → P1 B2/B3 | PB5 (132) / PB6 (133) — FDCAN2 AF9 | BUS1N_RX / BUS1N_TX | red.h:40-41 |
| bus1 normal STB | PC13 (2) | CAN3_EN | U10 STB | PB3 (130) | BUS1N_STB | red.h:14 |
| bus1 OBD RX/TX (xcvr 4) | PB12 (33) / PB13 (34) — CAN2 alt | CAN1_RX / CAN1_TX | U8 → P1 A2/A3 | PB12 (72) / PB13 (73) — FDCAN2 AF9 | BUS1O_RX / BUS1O_TX | red.h:53-54 |
| bus1 OBD STB | PB10 (29) | CAN1_EN | U8 STB | PB4 (131) | BUS1O_STB | red.h:20 |
| bus2 CAN RX/TX (xcvr 3) | PA8 (41) / PA15 (50) — CAN3 | CAN0_RX / CAN0_TX | U9 → P1 A10/A11 | PG10 (123) RX / PG9 (122) TX — FDCAN3 AF2 | BUS2_RX / BUS2_TX | peripherals.h:46-47; DS Tab.8 |
| bus2 STB | PA0 (14) | CAN0_EN | U9 STB | PD7 (121) | BUS2_STB | red.h:17 |
| VOLT_S (×11) | PC2 (10) ADC ch12 | VoltageSens | R2 1 k / R3 10 k de 12V_Protected | PF11 (52) ADC1 INP2 | VOLT_S | red.h:71 |
| SBU1 ADC | PC0 (8) ch10 | SBU1 | P1 A8, R24 10 k→3V3, D5, Q2 | PC4 (47) ADC1 INP4 — **TT_ha, não 5 V** | SBU1_ADC (via divisor — D-12) | red.h:110 |
| SBU2 ADC | PC3 (11) ch13 | SBU2 | P1 B8, R23 10 k→3V3, D5, Q1 | PA1 (38) ADC1 INP17 — FT_ha | SBU2_ADC (divisor simétrico) | red.h:111 |
| relay SBU1 / SBU2 (OD) | PC10 (51) / PC11 (52) | relay_SBU1 / relay_SBU2 | Q2 / Q1 DDTA143ECA (PNP digital, E=+5V) → SBU | PC10 (109) / PC11 (110) | relay_SBU1 / relay_SBU2 | red.h:106-108 |
| LED R / G / B (OD, ativo-baixo) | PC9 (40) / PC7 (38) / PC6 (37) | Net-(U7-PCx) | R19/R18/R17 → U5 RGB ânodo comum | PE4 (3) / PE3 (2) / PE2 (1) | LED_R / LED_G / LED_B | red.h:124-125 |
| USB load switch | PB1 (27) ativo-baixo | USB_LOAD | Q3 → U1 AP22615 EN | PB14 (74) OD pull-up "obsolete" | USB_LOAD (manter via pull-up; ver §g) | red.h:96-98 |
| 5VOUT_S | PC4 (24) (não lido pelo black.h) | Net-(U7-PC4) | R15/R16 divisor +5V | PB1 (50) analog, não lido | 5VOUT_S (divisor reaproveitado) | red.h:92 |
| HSE | PH0 (5) / PH1 (6) | Net-(U7-PH0/PH1) | Y1 X322516MLB4SI (16 MHz [I]) + C23/C24 10 pF | PH0 (25) / PH1 (26) | HSE_IN / HSE_OUT — **cristal 25 MHz** | clock.h:66 |
| BOOT0 | BOOT0 (60) | Net-(U7-BOOT0) | SW1 + R14 10 k pull-down | BOOT0 (135) | BOOT0 | DS pino 135 |
| BOOT1 | PB2 (28) | Net-(U7-PB2) | R22 pull-down | — (H7 não tem BOOT1) | remover | — |
| GPS | PC14, PC5, PB0, PA9, PA10, PC12 | GPS_* | U4 NEO-M8M, U2, ANT1, L1 | — | **remover** (D-03) | red.h não usa |
| UART / SPI labels | PA2/PA3, PA4–PA7 | UART_*, SPI_* | sem destino | PE11–PE14 (SPI4, has_spi=false) | não rotear | peripherals.h:14-19 |
| SWD | PA13 (46) / PA14 (49) | não conectados | — | PA13 (102) / PA14 (107) | **novo header SWD** (opcional; recomendado) | — |

## (b) HW_TYPE

| | Baseline F413 (black) | H725 (red) |
|---|---|---|
| Mecanismo | exclusão: PB1&PB7 não ambos baixos (DOS), PA4–7 não altos (WHITE), PA13 não alto (GREY), PB15 não baixo (UNO) → BLACK | `id1 = PF7..PF10` com pull-up: RED exige **0b0000**; `id2 = PD4..PD7` ≠ 3 |
| Estado no hardware | PB7, PA13, PB15 flutuando; PA4–7 labels sem destino; PB1 = USB_LOAD (alto em repouso) → BLACK ✓ (parity_check OK) | PF7, PF8, PF9, PF10 → **GND** (0 Ω); PD4, PD5, PD6 → **NC** (D-08) |
| Fonte | panda_legacy_f4 stm32f4/board.h:20-37 | panda stm32h7/board.h:25-50 |

## (c) Clock

| | Baseline | H725 |
|---|---|---|
| Cristal | Y1 X322516MLB4SI (MPN sugere 16 MHz; valor não indicado no esquemático — NV), C23/C24 10 pF | **25 MHz** obrigatório (clock.h:66, CSS ligado); 3225, CL conforme datasheet do cristal escolhido (STEP 4); caps de carga recalculados |
| USB | PLL do HSE | HSI48 interno (sem cristal dedicado) |
| LSE | ausente | ausente (firmware usa LSI) — VBAT pode ir a 3V3 como no baseline |
| Core | 96/100 MHz (F413) | 240 MHz, PLL1 M=5 N=48; FDCAN 80 MHz |

## (d) Boot / gravação

| | Baseline | H725 |
|---|---|---|
| BOOT0 | SW1 botão + R14 10 k pull-down → DFU por botão ✓ | idem (pino 135); firmware também entra em DFU por software (early_init.h) |
| BOOT1 | R22 pull-down em PB2 | não existe no H7 → remover |
| Bootloader | 0x1FFF0000 (F4) | 0x1FF09804 (stm32h7_config.h:12) |
| Flash | app 0x08004000 (F4, setor 16 K) | bootstub 128 K; app **0x08020000**; provisioning 0x080FFFC0 → **1 MB (ZG)** |
| Assinatura | RSA (release/debug) | idem; build DEBUG completo necessário em placa própria (HRS §7) |
| SWD | sem header | adicionar header (PA13/PA14/NRST/GND/3V3) — recomendação; firmware não o impede |

## (e) Alimentação e VCAP

| Trilho | Baseline | H725 (DS13311 §6.3) | Classificação |
|---|---|---|---|
| +12V → 12V_Protected | D1 SMAJ16CA + Q4 HY12P03C2 + D2 BAS40WS + R1 1 k | igual | Reaproveitado |
| +5V | U6 TPS5450 (3 A) + L4 15 µH + D12 SM540C + C37 + R5/R6 | igual (consumo H7 ≈ 150–250 mA a 240 MHz [I, NV] + 4 transceivers + USB-A 5 V saída) | Reaproveitado |
| +3V3 | U12 XL1509-3.3 + L3 47 µH + D11 B320AE | igual, verificar ripple para VDDA (ADC 16 bit) → **adicionar filtro LC/ferrite + 1 µF/100 nF em VDDA/VREF+** | Adaptado |
| VDD core (interno) | F413: regulador interno LDO, 1× VCAP 2,2 µF (pad 30) | H725 LQFP144: **SMPS obrigatório** (PWR_CR3_SMPSEN) — VDDSMPS (16) 4,7 µF; VLXSMPS (15) → L 2,2 µH (Isat 1,7 A) → VFBSMPS (17) 10 µF; 220 pF VLX; VDDLDO (70/105/143) = 3V3; **VCAP 68/103/140: 2× 2,2 µF** (3º só interligado) | Novo |
| VDD / VSS | 4 pares + VDDA/VSSA + VBAT | VDD ×~10 pads, 100 nF cada + 4,7 µF bulk; VDDA (36)/VREF+ (35)/VSSA (34); VBAT (8) → 3V3; VDD33USB (91) = 3V3; VDD50USB (90) → **ligado a VDD33USB (3V3)**: o firmware red só liga `USB33DEN` (clock.h:121), nunca `USBREGEN` (apenas tres.h:106) ⇒ regulador USB interno OFF ⇒ DS13311 §3.7 (texto l.1459-1460) e Tab. operating conditions (l.8453-8455: "USB regulator OFF → VDD33USB") **[F]**; PDR_ON (142) → VDD | Adaptado |
| Transceivers | TJA1042TK-3: VCC 5 V, VIO 3V3 | **Mantido TJA1042TK/3** — datasheet NXP garante CAN FD até 5 Mbit/s (R3v2 §3.1 [F]); alternativas TCAN1042HGV-Q1 / MCP2562FD (NV). D-20 | Reaproveitado |

## (f) Tabela híbrida (obrigatória — protocolo v3 §H)

| Bloco | Baseline (F413) | Classificação | Justificativa / evidência HRS |
|---|---|---|---|
| MCU | U7 STM32F413RGTx LQFP64 | **Substituído** | STM32H725ZGT6 LQFP144 — HRS §2, §6; D-02 |
| Clock | Y1 16 MHz [I] + 2×10 pF | **Substituído** | 25 MHz obrigatório — HRS §2 (clock.h:66) |
| Alimentação do núcleo | LDO interno + 1 VCAP | **Novo** | SMPS externo (L 2,2 µH + caps) + 2 VCAP — HRS §2, DS §6.3.3; D-02 |
| Entrada 12 V e proteções | D1 TVS, Q4 P-FET, D2, R1 | **Reaproveitado** | independe do MCU; harness box já tem SMF16A (P10) |
| Regulador 5 V | U6 TPS5450 + L4 + D12 | **Reaproveitado** | margem de corrente suficiente [I]; verificar térmica STEP 5 |
| Regulador 3,3 V | U12 XL1509 + L3 + D11 | **Adaptado** | adicionar filtragem VDDA/VREF+ para ADC 16 bit (lladc.h) |
| Transceivers CAN | 4× TJA1042TK/3 | **Reaproveitado** (atualizado no STEP 4, D-20) | TJA1042 é CAN FD até 5 Mbit/s (datasheet NXP, R3v2 §3.1); default firmware `500k/2M` atendido; premissa "CAN clássico" do STEP 3 estava errada |
| Terminação | ausente | **Novo (DNP)** | footprints 120 Ω DNP para bancada; harness box já termina — D-04, P10 §2 |
| Conector harness (P1) | TYPE-C-31-M-04 16 pinos | **Reaproveitado** | mapeamento confere com OBD-C oficial via cruzamento TX↔RX do cabo (ver §g-1) |
| USB (host) | U3 USB-A + R20/R21 22 Ω + U1 AP22615 | **Adaptado** | PA11/PA12 iguais; PHY FS interno; load switch: controle PB14 OD "obsolete" → ligar EN a pull-up fixo e opcionalmente a PB14 (HRS §3) |
| SWD | ausente | **Novo** | header 2×5 1,27 mm ou 4 pinos — bring-up/recuperação (recomendação, opcional ao firmware) |
| LEDs | U5 RGB ânodo comum + R17–R19 | **Adaptado** | pinos PE2/PE3/PE4 OD ativo-baixo — compatível com ânodo comum; recalcular resistores para 3V3 |
| Identificação da placa | implícita (nenhum strap) | **Novo** | PF7–PF10 → GND — HRS §1; D-08 |
| Sensor de tensão | R2 1 k / R3 10 k → PC2 | **Adaptado** | mesmo divisor ÷11 → PF11 (red.h:71) |
| Sensor 5VOUT | R15/R16 → PC4 | **Adaptado** | → PB1 (red.h:92), firmware não lê; manter |
| Sensor de corrente | ausente | — | red: `read_current = unused` — não aplicável |
| Ventoinha | ausente | — | has_fan=false — não aplicável |
| Harness SBU + relé | R23/R24 10 k pull-up, D5 ESD, Q1/Q2 PNP para +5V | **Adaptado** | lógica igual (harness.h); PC4 TT_ha exige divisor/clamp — D-12; relé: pino OD baixo → PNP conduz → SBU = 5 V ✓ coerente com harness box (SBU1 "driven high to 5 V") |
| GPS | U4 NEO-M8M, U2, ANT1, L1, C15, R10 | **Removido** | red panda não tem GPS — hardware/panda/README.md; D-03 |
| Headers | nenhum | **Novo** | SWD (acima) |
| BOOT | SW1 + R14; R22 (BOOT1) | **Adaptado** | manter BOOT0; remover BOOT1 |

## (g) Conflitos e riscos (regra 9 — PIN_PARITY_CONFLICT)

**g-0. PIN_PARITY_CONFLICT: nenhum identificado.** Todos os 36 pinos exigidos pelo firmware red (firmware_pins.json) existem no LQFP144 com a AF correta (P3 39/39; coverage 61/61). Será confirmado pelo `parity_check.py --profile red_h7` sobre a netlist do hardware no STEP 4/7.

**g-1. Mapeamento P1 ↔ OBD-C oficial [F + I].** Baseline (netlist): bus0 (xcvr U11) → P1 **B10/B11**; bus1-normal (U10) → **B2/B3**; bus1-OBD (U8) → **A2/A3**; bus2 (U9) → **A10/A11**; SBU1 A8, SBU2 B8; VIN A4/A9/B4/B9. O pinout oficial da *harness side* (P10 §1) tem CAN0=A2/A3, CAN1=A10/A11, CAN2=B2/B3, CAN3=B10/B11. Num cabo USB-C full-featured, TX1± (A2/A3) de um plugue liga a RX1± (B11/B10) do outro, RX2± (A11/A10) ↔ TX2± (B2/B3) e SBU1 ↔ SBU2 (USB Type-C spec, cabo "fully connected" exigido pela comma — hardware/harness/README.md). Logo, na orientação normal: panda B10/B11 → harness A2/A3 = **CAN0 = carro** (bus0 ✓); panda B2/B3 → harness A10/A11 = **CAN1 = radar** (bus1 normal ✓); panda A2/A3 → harness B10/B11 = **CAN3 = comma power / OBD** (bus1 em modo OBD ✓ — explica o nome `CAN_MODE_OBD_CAN2`); panda A10/A11 → harness B2/B3 = **CAN2 = câmera** (bus2 ✓); panda SBU1 (A8) → harness SBU2 = ignição; panda SBU2 (B8) → harness SBU1 = relé — exatamente o comentário em harness.h:71-73 ("orientation normal: PANDA_SBU2→HARNESS_SBU1(relay), PANDA_SBU1→HARNESS_SBU2(ign)"). **Conclusão: manter a pinagem de P1 do baseline sem alteração.** Caso invertido tratado pelo firmware (bus0↔bus2 e xcvr 2↔4).

**g-2. PC4 não 5 V-tolerante** (D-12) — risco médio; resolvido em esquemático (divisor/clamp). Verificar que, com divisor, `avdd/2` continua discriminando 240 Ω / 1 kΩ / aberto.

**g-3. VDD50USB** — resolvido [F]: regulador USB interno não é habilitado pelo firmware red (clock.h:121 só `USB33DEN`; `USBREGEN` apenas em tres.h) → VDD33USB alimentado por 3V3 externo; VDD50USB ligado a VDD33USB (DS13311 l.8453-8455). Registrado em D-14.

**g-4. Compilação do firmware** — toolchain ARM ausente no PC → prova de build BLOQUEADA. Compatibilidade será descrita apenas como "em análise estática".

**g-5. Consumo H725 a 240 MHz** — NV (tabela de consumo do DS não extraída); TPS5450 3 A dá margem larga [I]. Verificar no STEP 5 (térmica) com DS Tab. "Current consumption".

**g-6. Área da PCB** — LQFP144 (22×22 mm com pads) + SMPS vs. LQFP64 (12×12) numa placa de 47,6×41,8 mm; GPS removido libera ~15×15 mm. Risco de layout ALTO; decidir no STEP 5 se mantém contorno ou cresce (DECISIONS futura).

**g-7. ERC/DRC herdados** — 7 erros ERC `power_pin_not_driven`, 8 `hole_clearance`, 3 `copper_edge_clearance`, 1 `drill_out_of_range` no baseline (FASE1 §1.6): corrigir no derivado.
