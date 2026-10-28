# Hybrid Panda: schematic description

Status: design only. The schematic has been checked by tool (ERC) and by netlist parity
against the PCB; it has not been built or tested. Source:
`hardware/hybrid-panda/HybridPanda.kicad_sch` (KiCad 10 S-expression). PDF plots:
`hardware/fabrication/pdf/HybridPanda_schematic.pdf` and
`hardware/reports/hybrid_schematic.pdf`. Portuguese version:
[schematic.pt-br.md](schematic.pt-br.md).

## 1. Sheet structure

| Property | Value | Source |
|---|---|---|
| Sheets | 1 (flat, no hierarchical sub-sheets) | `HybridPanda.kicad_sch` (`sub_sheets = 0`) |
| Paper | A1 | `(paper "A1")`; D-18 |
| Origin | Generated from the OpenBlackPanda v2 schematic (A2) by `hardware/scripts/step4_build_schematic.py`, then edited by the `corr_step*.py` correction scripts | `hardware/research/step4-esquematico-h725.md`, `hardware/reports/correcoes-aplicadas.md` |
| Symbols | 241 total: 119 components, 122 power symbols (`#PWR`, `#FLG`) | parsed from the file |
| Wires / junctions / no-connects | 450 / 138 / 77 | parsed from the file |
| Labels | 52 distinct global labels (119 instances); no local or hierarchical labels | parsed from the file |
| Symbol libraries | embedded `lib_symbols` plus `HybridPanda.symbols`; `sym-lib-table` repointed (D-19) | `step4-esquematico-h725.md` section 7 |

Functional areas are marked by free text on the sheet. The texts present in the file are:
"OBD-C Connector", "Reverse polarity protection", "Power Regulators", "12V to 5V Regulator",
"5V to 3.3V Regulator", "USB Connector", "CAN Interface", "Microcontroller",
"Decoupling capacitors", "Ignition / SBU Detection", "HSE 25 MHz", "BOOT0", "NRST",
"SWD (ARM 10-pin)", "VCAP", "SMPS step-down", "VDDA filter",
"LED drivers (PE4/PE3/PE2, active low)", "SBU ADC conditioning (10k + BAT54S)",
"5V sense (PB1)", "CAN STB pull-ups (default standby)",
"STM32H725 decoupling (VDD/VBAT/VDDLDO/VDDSMPS/VDD33USB)", "Power flags", and four
annotation notes (PCR-1 `JP1`, PCR-2 VFBSMPS to VCAP, SI/PI item 5 `D15`, SI/PI item 8 `U13`).
The baseline "GPS" area was removed (D-03).

## 2. Functional blocks

Pad-to-net data below is taken from the PCB netlist (`HybridPanda.kicad_pcb`), which the
STEP 7 check found identical to the schematic netlist (119/119 components, 481 pads,
0 divergences; `hardware/research/step7-validacao.md`).

### 2.1 OBD-C connector and input protection

- `P1` TYPE-C-31-M-04 (USB-C receptacle used as OBD-C): A4/A9/B4/B9 = +12V; A1/A12/B1/B12 and
  shell = GND; A2/A3 = BUS1O_H/L; B2/B3 = BUS1N_H/L; A10/A11 = BUS2_L/H; B10/B11 = BUS0_L/H;
  A8 = SBU1; B8 = SBU2. CC1/CC2 and D+/D- pins (A5, B5, A6, A7, B6, B7) are no-connect.
- `D1` SMAJ16CA from +12V to GND.
- `Q4` HY12P03C2: drain/source between +12V (pads 5) and 12V_Protected (pads 1-3); gate
  (pad 4) on Net-(D15-A) with `R1` 10 k to GND, `D2` BAS40WS and `D15` BZT52C12 to
  12V_Protected (zener limits Vgs, SI/PI item 5).
- `D5` PESD2CAN on SBU1/SBU2; `D6`-`D9` PESD2CAN on the four CAN pairs.

### 2.2 12 V to 5 V regulator

- `U6` TPS5450DDAR: pin 7 VIN = 12V_Protected, pin 8 PH = net L4, pin 1 BOOT via `C37`
  10 nF to L4, pin 4 VSENSE from divider `R5` 10 k (+5V) / `R6` 3.16 k (GND), pin 5 ENA
  unconnected, pins 6 and 9 (exposed pad) GND.
- `L4` 15 uH from L4 to +5V; `D12` SM540C from GND to L4.
- Input capacitors `C4`, `C12` 10 uF and `C6`, `C7` 2.2 uF on 12V_Protected; output
  `C3`, `C10`, `C18`-`C21` 47 uF on +5V.

### 2.3 5 V to 3.3 V regulator

- `U12` XL1509-3.3E1: pin 1 VIN = +5V, pin 2 SW = Net-(D11-K), pin 3 FB = +3V3, pins 4-8 GND.
- `L3` 47 uH from Net-(D11-K) to +3V3; `D11` B340A from GND to Net-(D11-K); `C8` 10 uF and
  `C16` 47 uF.

### 2.4 USB-A port and load switch

- `U1` AP22615AWU-7: pin 6 IN = +5V, pin 1 OUT = USB_PWR, pin 4 EN = Net-(Q3-C) with `R26`
  10 k to +5V, pin 3 FLG with `R9` 10 k to +5V, pin 5 ISET with `R27` 2.4 k to GND.
- `Q3` PDTC114EU: base USB_LOAD (PB14), emitter GND, collector Net-(Q3-C). A low level on
  USB_LOAD leaves `U1` enabled through `R26`; a high level turns `Q3` on and disables `U1`
  (behaviour with the upstream open-drain setting is discussed in `hybrid-fw-port.md`).
- `D10` BAS70H from +5V to USB_PWR; `C17` 47 uF, `C34` 100 nF on USB_PWR.
- `U3` USB-A receptacle: pin 1 USB_PWR, pin 2 USB_R_D-, pin 3 USB_R_D+, pins 4-6 GND
  (shell pins 5/6 tied to GND by item 33b).
- `R20` 22 R USB_D- to USB_R_D-, `R21` 22 R USB_R_D+ to USB_D+.
- `U13` USBLC6-2SC6: pins 1/6 on USB_R_D-, pins 3/4 on USB_R_D+, pin 2 GND, pin 5 USB_PWR.

### 2.5 CAN interface

Four identical cells (`U8` BUS1O, `U9` BUS2, `U10` BUS1N, `U11` BUS0), each TJA1042TK/3:
pin 1 TXD = BUSx_TX, pin 4 RXD = BUSx_RX, pin 8 STB = BUSx_STB (pull-up `R30`-`R33` 10 k to
+3V3), pin 3 VCC = +5V (decoupled by `C30`-`C33`), pin 5 VIO = +3V3 (decoupled by
`C26`-`C29`), pins 2 and 9 GND, pins 6/7 = BUSx_L/BUSx_H to `P1`.

### 2.6 Microcontroller

- `U7` STM32H725ZGT6. Signal pins are listed in
  [red-panda-retrofit-on-black-panda.md](red-panda-retrofit-on-black-panda.md) section 5.
- Power: all VDD, VBAT, VDDLDO, VDDSMPS, VDD33USB and VDD50USB pins on +3V3 (D-14); VSS,
  VSSA, VSSSMPS on GND; VDDA/VREF+ (pins 35/36) on VDDA through `FB1` 600 R with `C43` 1 uF
  and `C44` 100 nF.
- Core supply: Direct SMPS. VLXSMPS (pin 15) to `L5` 2.2 uH to VCAP; `C41` 220 pF on
  VLXSMPS; `C42` 10 uF on VCAP; VFBSMPS (pin 17) connected to the VCAP net together with
  the VCAP pins 68, 103, 140 (PCR-2, D-35); `C39`, `C40` 2.2 uF (0603) and `C64` 2.2 uF (0402)
  on VCAP; `C65` 4.7 uF at VDDSMPS (pin 16).
- Decoupling scheme (`step4-esquematico-h725.md` section 6): 5 x 100 nF inherited from the
  baseline (`C1`, `C2`, `C5`, `C11`, `C14`) + 15 x 100 nF (`C45`-`C59`) + 3 x 4.7 uF
  (`C60`-`C62`) + 1 uF (`C63`) on +3V3; one 100 nF per VDD pin pair placed on the bottom
  side next to `U7`.
- HW_TYPE straps: PF7, PF8, PF10 (pins 21, 22, 24) to GND; PF9 (pin 23) to `JP1` pad 2,
  `JP1` pad 1 to GND (PCR-1). PD4-PD6 no-connect (D-08).
- HSE: `Y1` 25 MHz between HSE_IN (PH0, pin 25) and HSE_OUT (PH1, pin 26); `C23`, `C24`
  18 pF to GND; `Y1` pins 2/4 GND.
- NRST (pin 27): `C38` 100 nF to GND and `J1` pin 10.
- BOOT0 (pin 135): `R14` 10 k to GND; `SW1` to +3V3.
- SWD: `J1` pin 1 +3V3, pin 2 SWDIO (PA13), pin 4 SWCLK (PA14), pins 3/5/9 GND, pin 10 NRST,
  pins 6/7/8 no-connect.

### 2.7 Ignition / SBU detection

- SBU1 (`P1` A8) and SBU2 (`P1` B8) are pulled to +3V3 by `R24` and `R23` 10 k.
- `Q2` (SBU1) and `Q1` (SBU2) DDTA143ECA digital PNP transistors: emitter +5V, collector to
  the SBU line, base from relay_SBU1 (PC10) / relay_SBU2 (PC11). Driving the base low pulls
  the SBU line to 5 V (harness relay / "intercept" function of the panda firmware).
- ADC conditioning: `R28` 10 k from SBU1 to SBU1_ADC (PC4), `R29` 10 k from SBU2 to SBU2_ADC
  (PA1); `D13`/`D14` BAT54S clamp SBU1_ADC/SBU2_ADC between GND and +3V3 (D-12, D-16).

### 2.8 Status LED

- `U5` FM-B1921RGBA common anode on +3V3; cathodes RED-, GREEN-, BLUE- through `R19` 100 R,
  `R18` 110 R, `R17` 180 R to LED_RED (PE4), LED_GREEN (PE3), LED_BLUE (PE2). Active low,
  open-drain outputs.

### 2.9 Sense dividers

- VoltageSens (PF11) = 12V_Protected x `R2` 1 k / (`R3` 10 k + `R2` 1 k).
- 5VOUT_S (PB1) = +5V x `R16` 10 k / (`R15` 10 k + `R16` 10 k).

### 2.10 Pull-ups and pull-downs summary

| Net | Resistor | To | Purpose |
|---|---|---|---|
| BOOT0 | `R14` 10 k | GND | boot from flash by default |
| BUS0_STB, BUS1N_STB, BUS1O_STB, BUS2_STB | `R30`-`R33` 10 k | +3V3 | transceivers in standby until driven (D-09) |
| SBU1, SBU2 | `R24`, `R23` 10 k | +3V3 | SBU idle level |
| Net-(D15-A) (Q4 gate) | `R1` 10 k | GND | turn Q4 on when +12V present |
| Net-(Q3-C) (U1 EN) | `R26` 10 k | +5V | U1 enabled unless Q3 pulls low |
| Net-(U1-FLG) | `R9` 10 k | +5V | open-drain fault flag pull-up |
| PF7, PF8, PF10 | direct | GND | HW_TYPE id1 = 0 |
| PF9 | `JP1` | GND when closed | HW_TYPE id1 bit (D-35) |

Test points: none. The schematic contains no `TP` references; probing points are the
`J1` header, `JP1` pads and component pads.

## 3. Nets of interest

| Net | From | To | Notes |
|---|---|---|---|
| +12V | `P1` A4/A9/B4/B9 | `D1`, `Q4` source | vehicle supply |
| 12V_Protected | `Q4` drain | `U6` VIN, `C4`/`C6`/`C7`/`C12`, `R3`, `D2`, `D15` | after reverse-polarity switch |
| +5V | `L4` | `U12`, `U1`, `U8`-`U11` VCC, `Q1`/`Q2`, `R5`, `R15`, bulk caps | buck output |
| +3V3 | `U12` FB / `L3` | `U7` supplies, transceivers VIO, pull-ups, `U5`, `J1` pin 1 | 3.3 V rail; In1.Cu zone under `U7` |
| USB_PWR | `U1` OUT | `U3` pin 1, `U13` pin 5, `C17`, `C34`, `D10` | switched 5 V to USB-A |
| VCAP | `L5`, `U7` pins 17/68/103/140 | `C39`, `C40`, `C42`, `C64` | core supply (SMPS output) |
| VLXSMPS | `U7` pin 15 | `L5`, `C41` | SMPS switch node |
| VDDA | `FB1` | `U7` pins 35/36, `C43`, `C44` | analog supply |
| BUS0_H / BUS0_L | `U11` pins 7/6 | `P1` B11/B10, `D9` | FDCAN1 |
| BUS1N_H / BUS1N_L | `U10` pins 7/6 | `P1` B2/B3, `D8` | FDCAN2 normal |
| BUS1O_H / BUS1O_L | `U8` pins 7/6 | `P1` A2/A3, `D6` | FDCAN2 OBD |
| BUS2_H / BUS2_L | `U9` pins 7/6 | `P1` A11/A10, `D7` | FDCAN3 |
| BUS0_TX / BUS0_RX | `U7` PB9 / PB8 | `U11` pins 1 / 4 | |
| BUS1N_TX / BUS1N_RX | `U7` PB6 / PB5 | `U10` pins 1 / 4 | |
| BUS1O_TX / BUS1O_RX | `U7` PB13 / PB12 | `U8` pins 1 / 4 | |
| BUS2_TX / BUS2_RX | `U7` PG9 / PG10 | `U9` pins 1 / 4 | |
| BUS0_STB, BUS1N_STB, BUS1O_STB, BUS2_STB | `U7` PG11, PB3, PB4, PD7 | transceiver pin 8, `R30`-`R33` | |
| USB_D+ / USB_D- | `U7` PA12 / PA11 | `R21` / `R20` | MCU side |
| USB_R_D+ / USB_R_D- | `R21` / `R20` | `U3` pins 3 / 2, `U13` | connector side, coupled pair on In1.Cu |
| SWDIO / SWCLK | `U7` PA13 / PA14 | `J1` pins 2 / 4 | |
| NRST | `U7` pin 27 | `J1` pin 10, `C38` | |
| BOOT0 | `U7` pin 135 | `SW1`, `R14` | |
| SBU1 / SBU2 | `P1` A8 / B8 | `R24`/`R23`, `Q2`/`Q1`, `R28`/`R29`, `D5` | harness SBU lines |
| SBU1_ADC / SBU2_ADC | `R28` / `R29` | `U7` PC4 / PA1, `D13` / `D14` | |
| relay_SBU1 / relay_SBU2 | `U7` PC10 / PC11 | `Q2` / `Q1` base | |
| VoltageSens | `R2`/`R3` | `U7` PF11 | 12 V / 11 |
| 5VOUT_S | `R15`/`R16` | `U7` PB1 | 5 V / 2 |
| USB_LOAD | `U7` PB14 | `Q3` base | |
| HSE_IN / HSE_OUT | `U7` PH0 / PH1 | `Y1`, `C23` / `C24` | 25 MHz |
| LED_RED / LED_GREEN / LED_BLUE | `U7` PE4 / PE3 / PE2 | `R19` / `R18` / `R17` | active low |
| VSENSE | `R5`/`R6` | `U6` pin 4 | 5 V feedback |
| Net-(JP1-B) | `U7` PF9 | `JP1` | HW_TYPE strap |

There is no VBUS-sense net to the MCU and no +5V net on `P1`.

## 4. ERC status

| Item | Value | Source |
|---|---|---|
| Tool | kicad-cli 10.0.7, `--severity-all`, 2026-10-28 | `hardware/reports/hybrid_ERC_final.json` |
| Errors | 0 | same |
| Warnings | 373: `endpoint_off_grid` 145, `lib_symbol_mismatch` 185, `pin_to_pin` 37, `lib_symbol_issues` 6 | same |
| Interpretation | `endpoint_off_grid` and `lib_symbol_*` are inherited from the baseline (embedded symbols vs KiCad 10 libraries, legacy `.lib` tables). `pin_to_pin` warnings include VCAP power_out to power_out (D-19, severity lowered to warning in `.kicad_pro`), PF7-PF10 bidirectional to PWR_FLAG GND (intentional strap, D-08) and the `U5` LED symbol with unspecified pins. | `step4-esquematico-h725.md` section 7 |
| Netlist parity with PCB | 119 components / 119 footprints, 481 pads, 0 divergences | `step7-validacao.md` |
| Firmware pin parity | 36/36 pins required by `red.h` on the expected `U7` pads | `hardware/scripts/step7_validate.py`, `step7-validacao.md` |

Not verified: electrical operation of any block, regulator stability, crystal load
capacitance (CL 12 pF part with 18 pF loads is an analytic choice, `correcoes-aplicadas.md`
item 24), USB and CAN signal integrity. The board has not been built.

## 5. References

- `hardware/hybrid-panda/HybridPanda.kicad_sch`, `HybridPanda.kicad_pro`.
- `hardware/fabrication/pdf/HybridPanda_schematic.pdf`, `hardware/reports/hybrid_schematic.pdf`.
- `hardware/research/step4-esquematico-h725.md` (schematic generation, 144-pin table, ERC analysis).
- `hardware/research/step7-validacao.md` (netlist and parity checks).
- `hardware/reports/correcoes-aplicadas.md` (changes applied after the audits).
- `hardware/reports/hybrid_ERC_final.json`.
- `docs/decisions.md` D-03, D-08, D-09, D-12, D-14, D-16, D-18, D-19, D-35.
