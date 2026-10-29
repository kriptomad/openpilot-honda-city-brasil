# Hybrid Panda: bill of materials

Status: design only. No part has been purchased, no LCSC code has been confirmed against
the supplier catalogue, and no board has been assembled. The machine-readable twin of this
table is [bom.csv](bom.csv), generated from the KiCad schematic and PCB by
`hardware/scripts/gen-docs-bom.py`. Portuguese version: [bom.pt-br.md](bom.pt-br.md).

## 1. BOM status

| Metric | Value | Source |
|---|---|---|
| Schematic references (in BOM) | 119 | `HybridPanda.kicad_sch`, `gen-docs-bom.py` |
| PCB-only footprints | 6 fiducials `FID1`-`FID6` (no part) | `HybridPanda.kicad_pcb` |
| References with MPN | 118 of 119 (`JP1` solder jumper has no part) | `gen-docs-bom.py` |
| References with LCSC code assigned | 117 of 119 (`JP1`, `U1` without) | `gen-docs-bom.py`; `README.md` "Hardware: Hybrid Panda" |
| LCSC codes confirmed in the JLCPCB catalogue | 0 (none confirmed in this repository) | `hardware/reports/bom-real/bom-report.md` ("STATUS: PARCIAL"), `README.md` |
| Codes flagged TO-VERIFY | `C4`/`C12` C2932476, `D15` C571379 (`C64` -> C12530 and `C23`/`C24` -> C1549 corrected 2026-10-29) | `hardware/reports/correcoes-aplicadas.md` section 4 |
| Distinct purchase lines | 55 lines when grouped by value + footprint + MPN + LCSC (48 lines / 114 components in the 2026-10-27 `BOM_HYBRIDPANDA_v1.csv` snapshot, before the correction campaign added `C64`, `C65`, `D15`, `U13`, `JP1`) | `bom.csv`; `bom-report.md` line 6 |
| Estimated component cost | USD 26.93 per board at 10-piece prices, 47 lines, without `U1`; MCU USD 15.74 (JLCPCB prices looked up 2026-10-27, not quoted) | `bom-report.md` lines 47-49 |
| Part not available at JLCPCB | `U1` AP22615AWU-7 (C2680357 removed); alternative TPS2553DBVR C55266 has the same pinout but a different ILIM resistor range, so `R27` 2.4 k would have to change | `bom-report.md` line 59 |
| JLC assembly files | `hardware/fabrication/assembly/BOM_JLC.csv`, `CPL_JLC.csv` (rotations not normalised to JLC conventions) | `hardware/fabrication/readme.md` |

"Assigned" in the tables below means the `LCSC` property is filled in the schematic
symbol. "Not confirmed" applies to every line: the codes were obtained by web search
(`bom-report.md` section on methodology) and must be checked for existence, stock and
footprint match before any order.

## 2. BOM by function

Columns: references, quantity, value, footprint (KiCad library name after the colon), MPN,
manufacturer, LCSC code, status, notes. Footprint and value strings are exactly as stored in
the schematic.

### 2.1 Microcontroller and clock

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| U7 | 1 | STM32H725ZGT6 | LQFP-144_20x20mm_P0.5mm | STM32H725ZGT6 | STMicroelectronics | C730156 | assigned / not confirmed | Bottom side. 1 MB flash required (D-02). Only -40..85 C grade found (`bom-report.md`). |
| Y1 | 1 | 25MHz X322525MOB4SI | Crystal_SMD_3225-4Pin_3.2x2.5mm | X322525MOB4SI | YXC | C9006 | assigned / not confirmed | CL 12 pF per `bom-report.md`. |
| C23, C24 | 2 | 18pF | C_0402_1005Metric | 0402CG180J500NT | Fenghua | C1549 | assigned / catalogue MPN match (2026-10-29) | 15 pF -> 18 pF (item 24). Was C1555 (= 22 pF in the JLC catalogue, `hardware/reports/verification/lcsc-confirmation.md`). Alternative C307443 in `correcoes-aplicadas.md`. |
| C39, C40 | 2 | 2.2uF | C_0603_1608Metric | CL10A225KO8NNNC | Samsung | C23630 | assigned / not confirmed | VCAP. |
| C64 | 1 | 2.2uF | C_0402_1005Metric | CL05A225MQ5NSNC | Samsung | C12530 | assigned / catalogue MPN match (2026-10-29) | VCAP at U7.103 (item 2), 0402 for space. Was CL05A225MP5NSNC / C23733 (= 4.7 uF in the catalogue); C12530 is the 6.3 V X5R Basic part (VCAP ~1.2 V). |
| L5 | 1 | 2.2uH DFE201610E-2R2M | L_Murata_DFE201610P | DFE201610E-2R2M=P2 | Murata | C337891 | assigned / not confirmed | Direct SMPS inductor. |
| C41 | 1 | 220pF | C_0402_1005Metric | 0402B221K500NT | Fenghua | C1530 | assigned / not confirmed | VLXSMPS. |
| C42 | 1 | 10uF | C_0805_2012Metric | CL21A106KAYNNNE | Samsung | C15850 | assigned / not confirmed | SMPS output (VCAP). |
| C65 | 1 | 4.7uF | C_0603_1608Metric | CL10A475KO8NNNC | Samsung | C19666 | assigned / not confirmed | VDDSMPS at U7.16 (item 3). |
| FB1 | 1 | 600R@100MHz | L_0603_1608Metric | GZ1608D601TF | Sunlord | C1002 | assigned / not confirmed | VDDA filter. |
| C43 | 1 | 1uF | C_0402_1005Metric | CL05A105KA5NQNC | Samsung | C52923 | assigned / not confirmed | VDDA. |
| C44 | 1 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | VDDA. |
| C45-C59 | 15 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | VDD decoupling, one per VDD pin pair, bottom side. |
| C60, C61, C62 | 3 | 4.7uF | C_0603_1608Metric | CL10A475KO8NNNC | Samsung | C19666 | assigned / not confirmed | +3V3 bulk near U7. |
| C63 | 1 | 1uF | C_0402_1005Metric | CL05A105KA5NQNC | Samsung | C52923 | assigned / not confirmed | +3V3. |
| C38 | 1 | 100nF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | NRST. |
| R14 | 1 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | BOOT0 pull-down. |
| SW1 | 1 | SW_Push | SW_SPST_SKQG_WithStem | SKQGAFE010 | Alps Alpine | C202424 | assigned / not confirmed | BOOT0 button. |
| J1 | 1 | SWD | PinHeader_2x05_P1.27mm_Vertical_SMD | 20021121-00010C4LF | Amphenol ICC | C150517 | assigned / not confirmed | ARM 10-pin, bottom side. |
| JP1 | 1 | HW_ID1 | SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm | - | - | - | no part (PCB feature) | PF9 strap: closed = red (7), open = hybrid (11). |

### 2.2 CAN front end

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| U8, U9, U10, U11 | 4 | TJA1042TK-3 | DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm | TJA1042TK/3/1J | NXP | C131480 | assigned / not confirmed | /3 variant (VIO 3.3 V) mandatory. HVSON8 EP 1.60x2.40 vs footprint 1.55x2.4 (`bom-report.md`). |
| D5, D6, D7, D8, D9 | 5 | PESD2CAN,215 | SOT95P230X110-3N | PESD2CAN,215 | Nexperia | C75176 | assigned / not confirmed | D5 on SBU1/SBU2, D6-D9 on the four CAN pairs. |
| R30, R31, R32, R33 | 4 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | STB pull-ups to +3V3 (D-09). |
| C26, C27, C28, C29 | 4 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | Transceiver VIO (+3V3) decoupling. |
| C30, C31, C32, C33 | 4 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | Transceiver VCC (+5V) decoupling. |

### 2.3 Power input and regulators

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| D1 | 1 | SMAJ16CA-13-F | DIOM4325X250N | SMAJ16CA | Littelfuse | C148217 | assigned / not confirmed | 16 V bidirectional TVS on +12V. |
| Q4 | 1 | HY12P03C2 | PowerPAK_SO-8_Single | HY12P03C2 | HUAYI | C358006 | assigned / not confirmed | -30 V P-FET reverse protection. |
| R1 | 1 | 10k | R_0603_1608Metric | 0603WAF1002T5E | Uniroyal | C25804 | assigned / not confirmed | 1 k -> 10 k (SI/PI item 4). |
| D2 | 1 | BAS40WS 43 | D_SOD-323 | BAS40WS 43 | Changjing | C22648 | assigned / not confirmed | Gate network of Q4. |
| D15 | 1 | BZT52C12 | D_SOD-123 | BZT52C12 | High Diode (ou equivalente) | C571379 | assigned / TO-VERIFY | 12 V zener, Vgs limit (SI/PI item 5), bottom side. |
| U6 | 1 | TPS5450DDAR | CONV_TPS5450DDAR | TPS5450DDAR | Texas Instruments | C114425 | assigned / not confirmed | 12 V -> 5 V buck, 8 thermal vias (PTH 0.3 mm). |
| L4 | 1 | 15uH | L_10.5x11.5_H4.0 | MWSA1004S-150MT | Sunlord | C151872 | assigned / not confirmed | Buck inductor. |
| D12 | 1 | SM540C | D_SMC | B540C-13-F | Diodes Inc | C72264 | assigned / not confirmed | Buck catch diode. |
| C4, C12 | 2 | 10uF | C_0805_2012Metric | CL21A106KBYQNNE | Samsung | C2932476 | assigned / TO-VERIFY | TPS5450 input, 2.2 uF -> 10 uF (item 6). 50 V X5R, derating noted in `BOM_HYBRIDPANDA_v1.csv`. |
| C6, C7 | 2 | 2.2uF | C_0805_2012Metric | CC0805KKX7R9BB225 | Yageo | C125847 | assigned / not confirmed | TPS5450 input. |
| C37 | 1 | 10nF (LOW ESR) | C_0402_1005Metric | CL05B103KB5NNNC | Samsung | C15195 | assigned / not confirmed | TPS5450 bootstrap. |
| R5 | 1 | 10K (1%) | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | 5 V feedback (VSENSE). |
| R6 | 1 | 3.16K (1%) | R_0603_1608Metric | 0603WAF3161T5E | Uniroyal | C22993 | assigned / not confirmed | 5 V feedback (VSENSE). |
| C3, C10, C18, C19, C20, C21 | 6 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | assigned / not confirmed | +5V bulk. 10 V X5R; derating at 5 V noted in `BOM_HYBRIDPANDA_v1.csv`. |
| U12 | 1 | XL1509-3.3 | Diodes_PSOP-8 | XL1509-3.3E1 | XLSEMI | C74193 | assigned / not confirmed | 5 V -> 3.3 V buck; PSOP-8 footprint with unused exposed pad (inherited). |
| L3 | 1 | 47uH 2A - SMMS0650-470M | IND-SMD_L7.3-W6.8 | SMMS0650-470M | SXN | C149588 | assigned / not confirmed | |
| D11 | 1 | B320AE-13 | D_SMA | B340A-13-F | Diodes Inc | C85098 | assigned / not confirmed | Catch diode 3.3 V buck. |
| C8 | 1 | 10uF | C_0402_1005Metric | CL05A106MP5NUNC | Samsung | C315248 | assigned / not confirmed | 0603 deferred (BOM-a): no room between U12 and L3. |
| C16 | 1 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | assigned / not confirmed | +3V3 bulk. |
| C1, C2, C5, C11, C14 | 5 | 100NF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | +3V3 decoupling (baseline). |
| R2 | 1 | 1K | R_0402_1005Metric | 0402WGF1001TCE | Uniroyal | C11702 | assigned / not confirmed | VoltageSens divider (low side). |
| R3 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | VoltageSens divider (high side). |
| R15, R16 | 2 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | 5VOUT_S divider. |

### 2.4 USB

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| U3 | 1 | 10_0_QHHTZB6_3 | USB-A-TH_10.0QHHTZB6.3 | 10.0 QHHTZB6.3 | SHOU HAN | C668591 | assigned / not confirmed | USB-A receptacle, THT shell (2.5 mm slots). |
| U1 | 1 | AP22615AWU-7 | SOT-23-6 | AP22615AWU-7 | Diodes Inc | - | MPN only / not at JLCPCB | Load switch; see section 1. |
| Q3 | 1 | PDTC114EU | SOT-323_SC-70 | PDTC114EU,115 | Nexperia | C135830 | assigned / not confirmed | USB_LOAD level shift. |
| R9 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | U1 FLG pull-up. |
| R26 | 1 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | U1 EN pull-up. |
| R27 | 1 | 2.4K | R_0402_1005Metric | 0402WGF2401TCE | Uniroyal | C25882 | assigned / not confirmed | U1 ISET; changes if U1 is replaced. |
| D10 | 1 | BAS70H 115 | D_SOD-123F | BAS70H,115 | Nexperia | C426766 | assigned / not confirmed | +5V to USB_PWR. |
| C17 | 1 | 47uF | C_0805_2012Metric | 0805X476M100NT | Fenghua | C178332 | assigned / not confirmed | USB_PWR bulk. |
| C34 | 1 | 0.1uF | C_0402_1005Metric | CL05B104KB54PNC | Samsung | C307331 | assigned / not confirmed | USB_PWR. |
| U13 | 1 | USBLC6-2SC6 | SOT-23-6 | USBLC6-2SC6 | STMicroelectronics | C7519 | assigned / not confirmed | USB ESD array (SI/PI item 8). |
| R20, R21 | 2 | 22R | R_0402_1005Metric | 0402WGF220JTCE | Uniroyal | C25092 | assigned / not confirmed | USB series resistors, bottom side near U7. |

### 2.5 Harness connector, SBU and status LED

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| P1 | 1 | TYPE-C-31-M-04 | USB-C-SMD_TYPE-C-USB-20 | TYPE-C-31-M-04 | Korean Hroparts | C129018 | assigned / not confirmed | OBD-C receptacle; footprint carries 8 inherited hole_clearance DRC items. |
| Q1, Q2 | 2 | DDTA143ECA-7-F P08 | SOT23-3 | DDTA143ECA-7-F | Diodes Inc | C460029 | assigned / not confirmed | SBU relay drivers (PC11/PC10). Pad geometry corrected in step 1. |
| R23, R24 | 2 | 10K | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | SBU2/SBU1 pull-ups to +3V3. |
| R28, R29 | 2 | 10k | R_0402_1005Metric | 0402WGF1002TCE | Uniroyal | C25744 | assigned / not confirmed | SBU series to ADC (D-12). |
| D13, D14 | 2 | BAT54S | SOT-23 | BAT54S,215 | Nexperia | C47546 | assigned / not confirmed | SBU ADC clamps (D-16). |
| U5 | 1 | FM-B1921RGBA-SH | LED-ARRAY-SMD_4P-L2.2-W2.1-BR | FM-B1921RGBA-SH | Foshan NationStar | C727904 | assigned / not confirmed | RGB LED, common anode on +3V3. |
| R17 | 1 | 180R | R_0402_1005Metric | 0402WGF1800TCE | Uniroyal | C38941 | assigned / not confirmed | Blue. |
| R18 | 1 | 110R | R_0402_1005Metric | ERJ2RKF1100X | Panasonic | C413064 | assigned / not confirmed | Green. |
| R19 | 1 | 100R | R_0402_1005Metric | 0402WGF1000TCE | Uniroyal | C25076 | assigned / not confirmed | Red. |

### 2.6 Mechanical and assembly aids

| Refs | Qty | Value | Footprint | MPN | Manufacturer | LCSC | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| FID1, FID2, FID3 | 3 | - | Fiducial_1mm_Mask2mm | - | - | - | no part | Top side fiducials. |
| FID4, FID5, FID6 | 3 | - | Fiducial_1mm_Mask2mm | - | - | - | no part | Bottom side fiducials. |

Enclosure: not part of this BOM. The baseline STL files in
`archive/baseline-original/BlackPanda/STLs/` no longer fit the enlarged outline (D-24, D-33);
a new enclosure is not designed.

## 3. Totals by package

From `bom.csv` (125 rows including fiducials):

| Footprint | Count |
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
| SOT23-3 (BlackPanda lib) | 2 |
| SOT-23 | 2 |
| All other footprints | 1 each (22 footprints) |

Assembly: 80 footprints on the top side, 45 on the bottom side (including `U7`, `Y1`,
`J1`, `L5`, VCAP and decoupling capacitors). Through-hole: `U3` shell, `P1` shell and pins,
`U6` thermal vias. Source: `HybridPanda.kicad_pcb`.

## 4. How to regenerate

```
python hardware/scripts/gen-docs-bom.py
```

The script parses the schematic and PCB S-expressions without KiCad or kiutils and writes
`docs/hardware/bom.csv` with the columns `reference, value, footprint, mpn, manufacturer,
lcsc, lcsc_status, catalog_confirmed, side, dnp, datasheet, lib_id, source`. The
`catalog_confirmed` column is always `no` until a catalogue check is recorded in
`hardware/reports/bom-real/`.

## 5. References

- `hardware/hybrid-panda/HybridPanda.kicad_sch` (properties `MPN`, `Manufacturer`, `LCSC`).
- `hardware/reports/bom-real/bom-report.md`, `BOM_HYBRIDPANDA_v1.csv`, `BOM_JLCPCB.csv`.
- `hardware/reports/hybrid_BOM.csv`, `hardware/fabrication/assembly/BOM_JLC.csv`.
- `hardware/reports/correcoes-aplicadas.md` section 4 (BOM changes and TO-VERIFY codes).
- `docs/decisions.md` D-02, D-09, D-12, D-16, D-20, D-35, D-37.
