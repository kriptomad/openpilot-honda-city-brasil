# Hybrid Panda - independent adversarial hardware review (bare 4-layer JLCPCB order + hand assembly)

Date: 2026-10-29. Reviewer: independent pass, nothing from earlier reports was reused as evidence; every number
below was re-derived from the design files, the firmware sources and the datasheets listed here.
Everything is software/desk review. No board exists. This document does not declare the design fit for anything.

Scope: `hardware/hybrid-panda/HybridPanda.kicad_sch|.kicad_pcb|.kicad_pro|HybridPanda.pretty/`,
`hardware/fabrication/`. Tools: KiCad 10.0.7 (`kicad-cli`, pcbnew python; note: installed at
`C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\`, not under Program Files), gerbonara + shapely in
`.venv_gerber`. Helper scripts written for this review live in `hardware/scripts/adv/` (`parse_net.py`, `pcb_dump.py`,
`pads_dump.py`, `ref_planes.py`, `gerber_conn.py`, `fix_h2h.py`, `fix_resid.py`, `inspect_resid.py`,
`jlc_4layer.kicad_dru`); raw evidence is in `hardware/reports/verification-pcb/adv/`
(netlist `net.json`/`nets.txt`, pad geometry `pcb_dump.txt`/`pads.json`, DRC json before/after, gerber
connectivity output `gerber_conn*.txt`, firmware headers `fw/`). Pre-review PCB:
`hardware/hybrid-panda/snapshots/HybridPanda.kicad_pcb.pre_adversarial`.

Firmware truth: commaai/panda @ 408e14d46ebb7da45a7d21f8db315922e10242a8 (`board/boards/red.h`,
`board_declarations.h`, `stm32h7/llfdcan.h`, `board.h`, `peripherals.h`, `clock.h`, `lladc.h`, `llusb.h`,
`drivers/harness.h`; `lluart.h` does not exist at that commit) and fork kriptomad/panda@hybrid-h725
(`board/boards/hybrid.h`, `stm32h7/board.h`). Datasheet: `hardware/reference/datasheets/DS13313_text.txt`.

## Summary table

| # | Item | Verdict | Evidence (short) |
|---|------|---------|------------------|
| 1a | U7 signal pins vs red.h/hybrid.h | PASS | All FDCAN/STB/LED/SBU/relay/USB/HSE/BOOT0/NRST/SWD/HW-id nets land on the pins the firmware drives (table below). |
| 1b | U7 power pins, direct SMPS topology | PASS | All 13 VDD, VBAT, VDDSMPS, 3x VDDLDO, PDR_ON -> +3V3; all VSS/VSSSMPS/VSSA -> GND; VLXSMPS(15) -> L5 2.2 uH -> VCAP net = VFBSMPS(17) + VCAP 68/103/140; C41 220 pF on VLXSMPS, C42 10 uF + 3x 2.2 uF on VCAP; VREF+/VDDA via FB1. Matches DS13313 direct-SMPS figure / Table 16. No floating power pin. |
| 1c | HW_TYPE id | NOTE | PF7/PF8/PF10 = GND, PF9 = JP1 (open). Open => id1 = 4 = HW_TYPE_HYBRID only in the fork `stm32h7/board.h`; upstream panda reports UNKNOWN. JP1 closed => red panda id. Works only with the fork firmware or JP1 bridged. |
| 2 | HSE 25 MHz | PASS | Y1 X322525MOB4SI, CL = 12 pF (LCSC C9006 listing). C23/C24 = 18 pF -> 9 pF + ~3 pF stray = 12 pF. No series R (none in red panda either). Y1 on B.Cu 4.6 mm from U7 pins 25/26 (also B.Cu side via); HSE_IN 9.5 mm, HSE_OUT 8.9 mm of track. GND pads of Y1 on GND. |
| 3a | 12 V input protection | NOTE | D1 SMAJ16CA (bidirectional, 400 W, Vbr 17.8 V, Vc 26 V). Adequate for normal 12-14.4 V and short transients; will not survive an unsuppressed ISO 7637 load dump. Same as black panda. Q4 HY12P03C2 reverse-polarity PMOS, gate R1 10k to GND, D15 BZT52C12 clamps Vgs to -12 V (Vgs max +-20 V). |
| 3b | TPS5450 12 -> 5 V | PASS | VSENSE R5 10k / R6 3.16k: Vout = 1.221 x (1 + 10/3.16) = 5.085 V. BOOT C37 10 nF, L4 15 uH (MWSA1004S-150MT, 5 A class), D12 B540C catch, 5x 47 uF 10 V X5R 0805 output, ENA floating (internal pull-up, allowed by TI DS). |
| 3c | XL1509-3.3 5 -> 3.3 V | NOTE | Fixed-3.3 V part, FB tied to +3V3, EN (pin 4, active low) to GND, L3 47 uH, D11 catch. D11 value field says `B320AE-13` but MPN/LCSC are `B340A-13-F`/C85098 - inconsistent text only; either part works. Vin 5.085 V is inside the XL1509 4.5-40 V range. |
| 3d | Current budget | PASS | Rough worst case: H725 ~0.25 A @3V3 (SMPS, ~0.2 A @5 V), 4x TJA1042 dominant ~70 mA each = 0.28 A @5 V, LEDs ~30 mA, USB load switch up to the AP22615 limit. TPS5450 (5 A) and XL1509 (2 A) have margin. |
| 3e | VDD33USB / VDDA | PASS | VDD50USB(90) and VDD33USB(91) both on +3V3: allowed by DS13313 Table 13 (USB regulator OFF -> VDD50USB = VDD33USB); firmware sets USB33DEN only, never USBREGEN. VDDA/VREF+ via FB1 600R + C43 1 uF + C44 100 nF. |
| 4 | USB device port | PASS | PA11 (OTG DM) -> R20 22R -> U13 USBLC6-2SC6 -> U3.2 (D-); PA12 -> R21 -> U13 -> U3.3 (D+). U3.1 = USB_PWR from U1 AP22615 (EN via Q3 from PB14 USB_LOAD). No VBUS sense: `llusb.h` clears VBDEN, so none needed. Netclass USB 0.35/0.15 mm, pair on B.Cu with one via each. |
| 5a | CAN transceivers supply | PASS | TJA1042TK/3: VCC = +5V, VIO = +3V3 (correct for the /3 variant), STB pins PG11/PB3/PD7/PB4 with 10k pull-ups to 3V3 (safe standby at power-up; firmware drives low to enable). |
| 5b | CAN TX/RX pins and AF | PASS | PB8(136) FDCAN1_RX / PB9(137) FDCAN1_TX AF9 -> U11; PB5(132)/PB6(133) FDCAN2 AF9 -> U10 (BUS1 normal); PB12(72)/PB13(73) FDCAN2 AF9 -> U8 (BUS1 OBD); PG9(122) FDCAN3_TX / PG10(123) FDCAN3_RX AF2 -> U9. Pin numbers and AFs from the DS13313 pin table and AF table (lines 5529-5541, 7689-7690). |
| 5c | Bus to P1 mapping | PASS | BUS0 -> B10/B11, BUS1 normal -> B3/B2, BUS1 OBD -> A3/A2, BUS2 -> A10/A11, SBU1 A8, SBU2 B8, VBUS A4/A9/B4/B9. Through a full-featured USB-C cable the SSTX/SSRX pairs cross (A2/A3 <-> B11/B10, A10/A11 <-> B3/B2), so this matches the comma harness-box table in `p10-obdc-harness-sbu.md` (CAN0 = car on A2/A3 at the harness side). Orientation is handled by the firmware (harness.h). PESD2CAN D5-D9 on each pair; no 120 R on board (correct, termination is in the harness). |
| 6 | SBU / ignition / relays | PASS | SBU1 -> R28 10k -> PC4 (ADC1_INP4) with D13 BAT54S clamp to 3V3/GND; SBU2 -> R29 -> PA1 (ADC1_INP17) with D14. red.h harness config uses exactly PC4/ch4 and PA1/ch17. Relays: PC10 -> Q2, PC11 -> Q1 (DDTA143E PNP, E = +5V, C = SBU): firmware open-drain, low = drive -> consistent. |
| 7 | BOOT0 / NRST / SWD | PASS | BOOT0 R14 10k to GND, SW1 to 3V3. NRST C38 100 nF + J1.10. J1 2x5 1.27 mm: 1 = 3V3, 2 = SWDIO (PA13), 4 = SWCLK (PA14), 3/5/9 = GND, 10 = NRST (ARM 10-pin standard). |
| 8 | LEDs | PASS | U5 FM-B1921RGBA-SH common anode pin 1 on 3V3; PE4/PE3/PE2 sink through R19 100R / R18 110R / R17 180R (active low as in red.h). ~10-13 mA per channel, inside GPIO limits. |
| 9a | DRC, project rules | PASS | 73 violations, all `lib_footprint_mismatch` (local edits of library footprints); 0 unconnected; 0 clearance/short/courtyard. |
| 9b | DRC, JLC 4-layer rules (`scripts/adv/jlc_4layer.kicad_dru`) | NOTE | Before fixes: 97 rule hits. After the two fix passes (section 3): annular_width 12, hole_clearance 0, copper_edge_clearance 4, hole_to_hole 56 (none between different-net vias). Residuals are listed in section 4. |
| 9c | Inner layers / reference | NOTE | No solid GND plane: In1 is mostly a +3V3 zone plus GND fill and ~30 signal tracks; In2 mixed GND/+5V fill plus signal tracks. Sampling CAN pairs and USB pair against the adjacent inner layer: USB D+/D- ~65 % over GND, CAN pairs 35-95 % over GND, rest over +3V3 or voids. Tolerable at USB FS / CAN-FD on a 50 mm board; impedance figures in earlier reports assume a solid reference and are therefore optimistic. |
| 9d | Zones, islands, copper text | PASS | All 9 copper zones filled (refilled by this review); 8 copper islands without a net: 2x 4.86 mm2 unnetted EP copper under U12 (PSOP-8 footprint on a plain SOP-8, mask-covered), 6x fiducial dots. No text on copper layers. |
| 9e | Drill / gerber consistency | PASS | PTH.drl 266 objects (260 holes + 6 G85 slots: 4x P1 shell 0.6x1.2, 2x U3 shell 0.7x2.5) + NPTH 2 = 268 = PCB. Single closed Edge.Cuts polygon 51.02 x 46.75 mm. Job file layer order L1 Top / L2 Inr / L3 Inr / L4 Bot, 1.59 mm. |
| 10 | Independent gerber connectivity | PASS | Own script `adv/gerber_conn.py` (own Excellon parser): copper rebuilt from 4 gerbers, linked through PTH/via holes, labelled with the 526 pads: 0 shorts, 0 opens over 142 nets, 0 pads off copper, 0 vias off their net, every PTH hole touches >= 2 copper layers. Rerun on the regenerated package: identical. |
| 11 | Footprints for hand soldering | PASS/NOTE | See footprint table. No mismatch requiring a footprint edit was found; three items could not be confirmed offline (LCSC datasheet server unreachable). |
| 12 | Silk / polarity / mechanics | NOTE | No silk text below 0.8 mm / 0.15 mm. References hidden on silk for Q1/Q2 (F.Fab only), D2, D7, Q4, U13, JP1, D13, D14, D15, J1 - hand assembly needs the fab PDFs. No mounting holes at all (only P1's 2 NPTH pegs); enclosure fit not checked. |

## 1. Pin-by-pin table (netlist `adv/nets.txt` vs firmware)

| Function (firmware) | Port/pin (red.h / hybrid.h) | LQFP-144 pin | Net | OK |
|---|---|---|---|---|
| FDCAN1 RX/TX (bus 0) | PB8 / PB9 AF9 | 136 / 137 | BUS0_RX -> U11.4, BUS0_TX -> U11.1 | yes |
| FDCAN2 RX/TX normal (bus 1) | PB5 / PB6 AF9 | 132 / 133 | BUS1N_RX -> U10.4, BUS1N_TX -> U10.1 | yes |
| FDCAN2 RX/TX OBD (bus 1) | PB12 / PB13 AF9 | 72 / 73 | BUS1O_RX -> U8.4, BUS1O_TX -> U8.1 | yes |
| FDCAN3 TX/RX (bus 2) | PG9 TX / PG10 RX AF2 | 122 / 123 | BUS2_TX -> U9.1, BUS2_RX -> U9.4 | yes |
| CAN STB 0 / 1N / 1O / 2 | PG11 / PB3 / PD7 / PB4 | 124 / 130 / 121 / 131 | 10k pull-ups R30-R33 to 3V3; U11/U10/U9/U8 pin 8 | yes |
| LEDs R/G/B (active low) | PE4 / PE3 / PE2 | 3 / 2 / 1 | RED-/GREEN-/BLUE- via R19/R18/R17 to U5 | yes |
| SBU1 / SBU2 ADC | PC4 ch4 / PA1 ch17 | 47 / 38 | via R28/R29 10k + BAT54S clamps | yes |
| Relay SBU1 / SBU2 | PC10 / PC11 | 109 / 110 | Q2 / Q1 base (PNP, 10k) | yes |
| VoltageSens | PF11 ch2 | 52 | R3 10k / R2 1k from 12V_Protected (x11) | yes |
| 5VOUT_S | PB1 ch5 | 50 | R15/R16 10k/10k from +5V | yes |
| USB load switch | PB14 | 74 | Q3 -> U1 EN | yes |
| USB DM / DP | PA11 / PA12 | 100 / 101 | R20/R21 22R -> U13 -> U3 | yes |
| HSE | PH0 / PH1 | 25 / 26 | Y1, C23/C24 18 pF | yes |
| BOOT0 / NRST | - | 135 / 27 | R14 10k GND + SW1; C38 + J1.10 | yes |
| SWDIO / SWCLK | PA13 / PA14 | 102 / 107 | J1.2 / J1.4 | yes |
| HW id1 (PF7 PF8 PF9 PF10) | board.h | 21 22 23 24 | GND GND JP1 GND | note 1c |
| HW id2 (PD4 PD5 PD6) | board.h | 116 117 120 | unconnected | yes |
| fan / siren / SOM / SPI | not used by red | - | all unconnected | yes |

(Exact LQFP-144 pin numbers for every net are in `adv/net.json`; the ones that matter - 72/73, 122/123, 132/133,
136/137, 90/91, 15/16/17, 68/103/140, 70/105/143, 142 - were cross-read against DS13313; the other numbers in the
table are the U7 pad numbers from the exported netlist.)

## 2. Footprints vs datasheets (hand-solder parts)

| Ref | Footprint on board | Reference | Result |
|---|---|---|---|
| U7 | LQFP-144_20x20mm_P0.5mm (KiCad): pads 1.475 x 0.3 mm, 0.5 pitch | ST / IPC nominal | PASS |
| U8-U11 | DFN-8-1EP 3x3 P0.65, pads 0.65 x 0.35, EP 1.55 x 2.4, 1 GND via in EP | NXP SOT782-1: body 3x3, pitch 0.65, die pad 1.65 x 2.45 (min 1.55 x 2.35) | PASS (EP slightly smaller than die pad: fine for hand soldering, less wicking) |
| U6 | CONV_TPS5450DDAR: pins 1.55 x 0.6, PowerPAD copper 2.95 x 4.9 with 2.61 x 3.11 mask window, 8 GND vias | TI DDA (SO PowerPAD 8) | PASS |
| U12 | Diodes_PSOP-8 used for SOP-8 XL1509-3.3E1: row pitch 5.4, pad pitch 1.27 | SOP-8 | PASS (extra mask-covered copper under body is harmless) |
| L5 | L_Murata_DFE201610P: 2 pads 0.55 x 1.6 at 1.45 mm pitch | DFE201610E-2R2M=P2 is the same 2.0 x 1.6 body family | NOTE - E-variant land drawing not fetched (LCSC offline); P-variant land accepted |
| P1 | TYPE-C-31-M-04 hybrid: 12 SMD A-row 0.3 x 0.9 @0.5, 12 PTH B-row 0.4 drill/0.65 pad, 4 oval shell slots 0.6 x 1.2, 2 NPTH 0.65 | Hroparts drawing clips in `footprint-audit/datasheets/png/TYPEC31M04_p1*.png` | PASS (B12 under A1, slots as G85) |
| U3 | USB-A 10.0 QHHTZB6.3: 4 SMD 1.12 x 2.88 at 2.5/2.0/2.5 pitch, 2 shell slots 0.7 x 2.5 | SHOU HAN C668591: SMD signals + TH shell | PASS on construction and pitch; pin-1 side vs receptacle not verified from a drawing (see "cannot determine") |
| SW1 | SW_SPST_SKQG_WithStem (KiCad, drawn for SKQGAFE010) | Alps SKQGAFE010 | PASS |
| Y1 | Crystal_SMD_3225-4Pin | X322525MOB4SI 3.2 x 2.5 | PASS |
| SOT-23 / SOT-23-6 / SC-70 / SOD-123 / SOD-323 / SMA / SMC / 0402 / 0603 / 0805 | KiCad standard | - | PASS |
| U5 | LED-ARRAY-SMD_4P-L2.2-W2.1 (black panda lib) | FM-B1921RGBA-SH | NOTE - pad geometry inherited from the black panda design; datasheet not fetched |
| J1 | PinHeader_2x05_P1.27mm_Vertical_SMD | 20021121-00010C4LF | PASS |

## 3. Edits made by this review

1. `hardware/hybrid-panda/HybridPanda.kicad_pcb`, pass 1 - six vias moved 0.02-0.09 mm to reach >= 0.52 mm
   hole-to-hole against a different-net hole (script `hardware/scripts/adv/fix_h2h.py`, also moves the track ends
   attached to the via):
   GREEN- (99.276,69.262) -> (99.293,69.230); GND (116.000,68.462) -> (116.058,68.439);
   GND (121.662,52.100) -> (121.664,52.129); GND (122.362,57.100) -> (122.341,57.105);
   GND (125.485,53.009) -> (125.499,52.925); BUS0_TX (118.831,62.316) -> (118.906,62.273).
2. `hardware/hybrid-panda/HybridPanda.kicad_pcb`, pass 2 (`hardware/scripts/adv/fix_resid.py`):
   a. GND via (109.150,71.0425) -> (109.130,71.0395), 0.02 mm away from the VCAP track on B.Cu; hole-to-copper
      0.251 -> 0.271 mm (its one attached GND track end moved with it).
   b. Two rule areas `P1_NPTH1_nocopper` / `P1_NPTH2_nocopper`: 1.2 mm squares, "no copper pour", on all four
      copper layers, centred on P1's NPTH pegs (134.940,62.555) and (134.940,55.205); hole edge to GND fill
      0.2505 -> 0.275 mm.
   c. +12V meander on F.Cu at the right edge: the 10 track endpoints at x = 142.1067 moved to x = 142.080
      (edge clearance 0.278 -> 0.305 mm; the meander keeps its 0.2 mm width and its connections).
   d. C28 (0402, +3V3/GND) moved 0.04 mm in -x to (141.8725,69.562) together with its two track ends
      (pad-to-edge 0.2625 -> 0.3025 mm).
   Not touched on purpose: the three BUS1N_H segments (0.21-0.235 mm) and the GND zone edge (0.2005 mm), per
   the project's 0.2 mm edge rule.
   Zones refilled with pcbnew ZONE_FILLER after each pass. Project-rule DRC after both passes: 73
   lib_footprint_mismatch, 0 unconnected, 0 clearance. JLC-rule DRC: hole_clearance 0, no different-net via pair
   below 0.5 mm.
3. `hardware/fabrication/` regenerated after each pass: `step7_validate.py` (falhas: []), `final_audit.py`
   (0 shorts, 0 via-in-pad, INFO 20 / BAIXO 1), `step8_fabricate.py` (problemas: []; readme timestamp
   2026-10-29 16:44:34; the STEP export returned code 2 as before, the script tolerates it). Independent gerber
   connectivity (`scripts/adv/gerber_conn.py`) rerun on the final package: 268 holes, 0 shorts, 0 opens.
4. `hardware/fabrication/readme.md` - paragraph added after the intro (`step8_fabricate.py` rewrites the file;
   the paragraph was re-added after the second run and must be re-added after any future run).
5. `hardware/reports/correcoes-aplicadas.md` - section 8 (pt-BR) added and updated.
6. Temporary `hardware/hybrid-panda/HybridPanda.kicad_dru` was created for the DRC runs and deleted afterwards;
   the rule set is kept as `hardware/scripts/adv/jlc_4layer.kicad_dru`. Pre-review PCB saved as
   `hardware/hybrid-panda/snapshots/HybridPanda.kicad_pcb.pre_adversarial`; no other backup copies remain.
No schematic, footprint library or BOM file was changed. Nothing was committed.

## 4. Residual rule misses against the JLC numbers in the brief (not fixed)

| Rule | Count | Where | Assessment |
|---|---|---|---|
| hole_to_hole 0.5 mm, different nets | 15 | P1 B-row PTH pads, 0.40-0.41 mm (0.4 mm drills on 0.8 / 0.7 mm pitch) | Inherent to every TYPE-C-31-M-04 footprint; JLC builds this connector routinely. May raise an engineering query. |
| hole_to_hole 0.5 mm, same net | 41 | via-to-via and U6 PowerPAD via array, min 0.279 mm | JLC same-net limit is 0.254 mm: none below it. |
| annular_width 0.13 mm | 12 | P1 B-row: 0.65 pad / 0.4 drill = 0.125 mm | 5 um short; enlarging the pads would break the 0.4 mm pad-to-pad gap. Accept or ask JLC. |
| hole_clearance 0.254 mm | 0 | - | Closed by edits 2a/2b. |
| copper_edge_clearance 0.3 mm | 4 | BUS1N_H tracks 0.21-0.235 mm (3 segments), GND zone 0.2005 mm (right edge) | Project rule is 0.2 mm, which is JLC's published trace-to-outline figure for routed boards; the brief asked for 0.3. Left as-is by instruction; +12V meander and C28 were closed (edits 2c/2d). |

## 5. Final numbers

- ERC (`step7`): 0 errors, 373 warnings (unchanged; no schematic edit).
- DRC project rules: 73 (all lib_footprint_mismatch), 0 unconnected, 0 schematic-parity errors (118 "missing
  MPN field in footprint" + 1 JP1 BOM-attribute warnings when run with `--schematic-parity --severity-all`).
- DRC JLC rules after both passes: 145 total = 73 lib_footprint_mismatch + 72 rule hits listed in section 4
  (was 170 before any edit).
- Gerbers (package of 16:44:34): 268 holes (266 PTH objects incl. 6 G85 slots + 2 NPTH), 0 shorts, 0 opens,
  526 pads all on copper, min copper-to-edge 0.20 mm (GND zone), outline closed.
- final_audit: shorts 0, zone_shorts 0, unconn 0, via-in-pad 0.

## 6. What cannot be determined without a built board

- Whether the H725 direct-SMPS start-up actually works with this L5/C42 placement (L5 is 4.1 mm from pin 15 with the
  VCAP return partly on In1.Cu); the DS layout rules are met on paper only.
- HSE start-up margin with CL 12 pF crystal and 18 pF caps (stray assumed 3 pF).
- USB enumeration (pair over a non-continuous reference) and CAN-FD eye at 2-5 Mbit/s.
- U3 USB-A pin-1 orientation: pads 1-4 are in the standard order and pitch, but the drawing that ties pin 1 to
  one shell slot could not be downloaded (LCSC blocked). Check VBUS continuity to the receptacle contact before
  powering a host device.
- U5 RGB LED pin-1 / common-anode position vs the FM-B1921RGBA-SH drawing (black panda inherited geometry).
- L5 DFE201610E land pattern (P-variant footprint used).
- HW id: the fork firmware (id1 = 4) must be flashed; upstream panda will not recognise the board unless JP1 is bridged.
- Thermal behaviour of U6 and the TJA1042 pads with the hand-soldered EP vias.
- 12 V transient survival (SMAJ16CA only).

## Resumo (pt-BR)

Revisao adversarial independente do Hybrid Panda, refazendo netlist, firmware (red.h/hybrid.h @408e14d),
DS13313, DRC com regras JLC de 4 camadas e conectividade dos gerbers com script proprio. Nao foi encontrado
erro fatal de pinagem nem de alimentacao: todos os pinos VDD/VSS/VCAP/VLXSMPS/VFBSMPS/VDDLDO/VDDSMPS/VDD33USB/
PDR_ON do H725 estao ligados conforme o modo SMPS direto; FDCAN1/2/3, STB, SBU, reles, USB, HSE, BOOT0, SWD e
LEDs batem com o firmware. Correcoes aplicadas na PCB: 6 pares de vias de redes diferentes com furo-a-furo entre
0,43 e 0,50 mm deslocados (0,02-0,09 mm); via GND afastada da trilha VCAP (folga furo-cobre 0,251 -> 0,271 mm);
areas sem cobre de 1,2 mm nos dois pinos NPTH de P1 (0,2505 -> 0,275 mm); meandro +12V e C28 recuados da borda
direita (>= 0,30 mm). Zonas repreenchidas e pacote de fabricacao regenerado (268 furos, 0 curtos, 0 abertos).
Ficam em aberto, de proposito: trilhas BUS1N_H e borda da zona GND a 0,20-0,235 mm da borda (regra do projeto
0,2 mm; brief pedia 0,30), anel anular 0,125 mm e furo-a-furo 0,40 mm na fileira B do conector P1 (inerentes ao
TYPE-C-31-M-04). Camadas internas nao sao planos continuos. Nada foi testado em hardware; a lista do que so
uma placa montada pode responder esta na secao 6.
