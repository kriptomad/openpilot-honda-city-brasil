# P10 — Conector OBD-C, harness box v3 e lógica SBU (fonte oficial commaai/hardware)

Fontes: `hardware\reference\hardware` @ a42a4752dc5872a8a1136dee0cf0636aa6da57d6 (sem LICENSE; folha de rosto diz "comma.ai — you can copy this!"):
- `harness\OBD-C.sch.pdf` → render `hardware\research\renders\OBDC_sch_p1.png`
- `harness\v3\Harness_Box.pdf` ("car harness v3", 20 Aug 2024) → `renders\HarnessBox_p1.png`
- `harness\v3\Honda_Bosch_B_Harness.pdf` → `renders\HondaBoschB_p1.png`
- Firmware: `hardware\reference\panda\board\drivers\harness.h`, `boards\red.h` @408e14d4.
Legenda: **[F]** fato · **[I]** inferência · **NV** não verificado.

## 1. Pinout OBD-C (lado harness, fêmea USB-C) **[F]** — OBD-C.sch.pdf

| Pino | Sinal | Pino | Sinal |
|---|---|---|---|
| A1 | GND | B1 | GND |
| A2 | CAN0_H | B2 | CAN2_H |
| A3 | CAN0_L | B3 | CAN2_L |
| A4 | VIN | B4 | VIN |
| A5 | — (CC1 n/c) | B5 | — (CC2 n/c) |
| A6 | — (D+ n/c) | B6 | — |
| A7 | — (D− n/c) | B7 | — |
| A8 | SBU1 | B8 | SBU2 |
| A9 | VIN | B9 | VIN |
| A10 | CAN1_L | B10 | CAN3_L |
| A11 | CAN1_H | B11 | CAN3_H |
| A12 | GND | B12 | GND |

Shield A/B → GND (Harness_Box.pdf, J3 DX07S024XJ1R1100). Cabo reversível: a rotação troca A↔B, logo **CAN0↔CAN2, CAN1↔CAN3, SBU1↔SBU2** — exatamente a troca `bus0↔bus2` que o firmware faz quando `harness.status == FLIPPED` (drivers/can_common.h:130-134) **[F]**. CAN1↔CAN3 sob flip: o red panda só usa CAN1 (FDCAN2 "OBD" pinos) e o firmware trata via `set_can_mode(... flipped ...)` (red.h:36-62).

Mapeamento semântico (Harness_Box.pdf): **CAN0 = CAR, CAN1 = RADAR, CAN2 = CAMERA, CAN3 = COMMA POWER**.

## 2. Harness box v3 — o que fica do lado do harness **[F]**

| Bloco | Componentes | Implicação para a placa panda |
|---|---|---|
| "Relay" solid-state | 2× DG419LEDY (U1 CAN_H, U2 CAN_L): COM=CAN2, NC=CAN0, NO=CAN0'/CAN2' (lado terminado); IN ← SBU1; V+ = VIN | A desconexão CAN0↔CAN2 acontece **no harness**; a panda só precisa levar SBU1 a nível alto |
| Divisor SBU1 | R3 120 Ω + R2 120 Ω = **240 Ω** SBU1→GND (o texto do OBD-C.sch diz "~100 Ω"; o esquema v3 mostra 240 Ω) | A panda lê SBU1 "baixo" via ADC → identifica lado do relé |
| Ignição | IGN_12 → R4 1k / R5 1k → gate Q6 DMN3200U-7; dreno → R1 1k → SBU2 | Ignição ON ⇒ SBU2 puxado a GND por 1 kΩ; OFF ⇒ SBU2 flutuando |
| Terminação CAN | R6 120 Ω CAN0' (lado câmera, após relé), R7 + R8 120 Ω em CAN2/CAN2'' | **Terminação já existe no harness** → placa panda **sem** terminação populada (confirma D-04) |
| Proteção | D4 SMF16A (VIN), D2/D3 BAS40SDW em CAN0 e CAN2 | Panda ainda deve ter ESD/TVS próprios no OBD-C (defesa em profundidade) **[I]** |
| Comma power | J2 212528-0400: CAN3_H/L, VIN, GND; D1 STPS2H100 IGN_12→VIN | CAN3 só é usado com comma power (red panda não liga FDCAN a CAN3 do OBD-C ⇒ **NV** se o red panda sequer roteia B10/B11) |

## 3. Lógica SBU no firmware **[F]** → requisitos da placa **[I]**

| Firmware (harness.h) | Comportamento | Requisito de hardware derivado |
|---|---|---|
| `harness_init`: relay pins OD, saída **1** (Hi-Z) | relé não acionado por padrão | Linhas SBU precisam de **pull-up na panda** (para ler "alto" quando a harness está desconectada e para que 240 Ω/1 kΩ leiam baixo). Com Rpu = 10 kΩ para 3,3 V: 240 Ω → 77 mV; 1 kΩ → 300 mV; aberto → 3,3 V. Valor **NV** (não publicado) |
| `harness_detect_orientation`: SBUx em ANALOG, lê mV; limiar `avdd/2 = 1650 mV`; menor tensão = lado relé; depois volta a MODE_INPUT "pins are not 5V tolerant in ADC mode" | orientação | Linha SBU pode atingir **5 V** (quando o relé é acionado). DS13311 Tab. 8: **PA1 = FT_ha** (5 V tolerante, DS13313_text.txt:4253) mas **PC4 = TT_ha** (3,6 V máx., **não** 5 V tolerante, :4444); PC10/PC11 = FT_fh (:5377,:5389). ⇒ a linha SBU **não pode** ir direto a PC4: exige divisor resistivo ou resistor série + clamp a 3,3 V no caminho ADC (afeta a escala lida: com divisor, o limiar 1650 mV passa a referir-se à tensão dividida — dimensionar para que 240 Ω/1 kΩ continuem < 1650 mV e "aberto" > 1650 mV) **[F pin type / I circuito]** |
| `set_intercept_relay(true)`: escreve **0** (OD baixo) no relay pin do lado relé | harness diz "SBU1 is driven high to 5V to disconnect" | Logo o pino OD **baixo** deve levar a linha SBU a **5 V** ⇒ estágio inversor na panda (ex.: P-MOSFET com gate puxado por PC10/PC11, fonte em 5 V) **[I]**; DG419 IN tem limiar lógico TTL (V+ = VIN 12 V, VL = VIN) → 5 V é "high" **[F DG419 NV datasheet]** |
| `harness_check_ignition`: `!get_gpio_input(SBU do lado ignição)` | 1 kΩ→GND = ignição ON | Pull-up da panda deve ser ≫ 1 kΩ para garantir VIL (3,3·1k/(1k+Rpu) < ~1 V ⇒ Rpu > 2,3 kΩ) |
| Normal: PANDA_SBU1→HARNESS_SBU2(ign), PANDA_SBU2→HARNESS_SBU1(relay) | convenção USB-C: SBU1↔SBU2 cruzam no cabo | — |

## 4. Honda Bosch B harness (City 2023 BR usa Bosch B — ver P1) **[F]** Honda_Bosch_B_Harness.pdf
- Conector câmera: JAE **MX34M12SF1** (12 vias, pinos M34S75C4F1); lado carro: Molex **501646-1200**; para harness box: Molex **501646-1800** (18 vias, pinos 501648-1000), fio UL1007 26 AWG.
- Sinais: IGN (marrom), GND (preto), **CAN2_H/L** (laranja/verde) = câmera, **CAN0_H/L** = carro, PT3/PT4 (amarelo/roxo) pass-through, loopback cinza 40 mm.
- Só **2 barramentos CAN** passam pelo harness Honda Bosch B (CAN0 carro, CAN2 câmera); CAN1 (radar) não é usado → consistente com `BOSCH_RADARLESS` (P1).

## 5. Pendências (NV)
- Esquema real do red panda não está em `hardware` → valores de pull-up/divisor/ESD do lado panda são inferências. Registrado em P2.
- ~~Confirmar FT/5 V-tolerância de PC4 e PA1~~ → feito: PC4 **TT_ha** (não 5 V), PA1 FT_ha. Consequência de projeto: caminho SBU→PC4 precisa de divisor/clamp (ver §3).
- Confirmar se o red panda conecta CAN3 (B10/B11) — hipótese: não (3 transceivers em CAN0/CAN1/CAN2 + 1 mux) **[H]**.
