# Hybrid Panda: PCB fabrication specification

Status: design only. **DO NOT FABRICATE.** No board has been ordered, built or tested. This
document describes what the KiCad files and the generated fabrication package specify, not
what a fabricator has confirmed. Portuguese version:
[pcb-specification.pt-br.md](pcb-specification.pt-br.md).

Primary sources: `hardware/hybrid-panda/HybridPanda.kicad_pcb`, `HybridPanda.kicad_pro`,
`hardware/fabrication/readme.md`, `hardware/fabrication/drill_table.md`,
`hardware/fabrication/gerbers/HybridPanda-job.gbrjob`, `hardware/reports/hybrid_DRC_final.json`.
Numbers marked "extracted" were parsed from the KiCad S-expression files for this document.

## 1. Board summary

| Item | Value | Source |
|---|---|---|
| Project | `HybridPanda` (KiCad 10.0.7) | `.kicad_pro`, `.kicad_pcb` header |
| Form factor | OpenBlackPanda v2 outline (black panda), unchanged except for the step at the USB-A connector | D-02, D-33 (`docs/decisions.md`) |
| Nominal size | 50.625 mm x 46.75 mm | D-33; extracted Edge.Cuts bounding box |
| Edge.Cuts bounding box (outer edge, 0.1 mm stroke) | X 91.91 to 142.535 mm (142.935 mm for Y < 48.6 mm), Y 32.01 to 78.76 mm | extracted |
| Outline detail | Rounded corners; east edge has a 0.4 mm step for the USB-A receptacle (`U3`) | extracted; D-33 |
| Copper layers | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) | `.kicad_pcb` `(layers ...)` |
| Finished thickness | 1.59 mm (sum of stackup; `BoardThickness: 1.59` in the job file) | `.kicad_pcb` stackup; `HybridPanda-job.gbrjob` |
| Footprints | 125 (80 on F.Cu, 45 on B.Cu); 119 schematic references + 6 fiducials | extracted |
| Pads | 526 | extracted |
| Nets | 142 named in the PCB file (62 real nets, 80 `unconnected-*` no-connect nets) | extracted |
| Track segments | 1218 (F.Cu 628, B.Cu 352, In1.Cu 152, In2.Cu 86) | extracted |
| Vias | 242 (203 x 0.6/0.3 mm, 39 x 0.7/0.3 mm), all through-hole, no blind/buried, no via-in-pad | extracted; `fabrication/readme.md` item 9 |
| Through-hole parts | `P1` (OBD-C receptacle, 12 PTH 0.4 mm + 4 slots + 2 NPTH 0.8 mm), `U3` (USB-A, 2 PTH 2.5 mm), `U6` thermal vias (8 x 0.3 mm PTH) | `drill_table.md` |
| Copper zones | 17: GND on all four layers; +3V3 on In1.Cu; +5V on F/B/In1 (x2)/In2; +12V and 12V_Protected on B.Cu; USB_PWR on F.Cu; L4 (switch node) on F.Cu; 6 keep-out areas | extracted |
| Fiducials | 6 (`FID1`-`FID3` top, `FID4`-`FID6` bottom), PCB-only, no schematic symbol | extracted; `correcoes-aplicadas.md` |
| Panelization | None (single board) | `fabrication/readme.md` |

The baseline OpenBlackPanda v2 board (`archive/baseline-original/`) is 2 layers with 86
footprints, 838 segments and 156 vias (extracted); the Hybrid Panda is a re-layout of the
same outline in 4 layers (D-05).

## 2. Stackup

Defined in the `(stackup ...)` section of `HybridPanda.kicad_pcb` and repeated in
`HybridPanda-job.gbrjob`. The values were chosen by the project and are **not confirmed with
any fabricator** (`fabrication/readme.md` item 1).

| # | Layer | Type | Thickness | Material / notes |
|---|---|---|---|---|
| 1 | F.SilkS | silkscreen | - | colour not defined in file |
| 2 | F.Paste | paste | - | |
| 3 | F.Mask | solder mask | 0.01 mm | colour not defined in file |
| 4 | F.Cu | copper | 0.035 mm (1 oz) | signal, components |
| 5 | dielectric 1 | prepreg | 0.2 mm | FR4, er 4.5, loss tangent 0.02 |
| 6 | In1.Cu | copper | 0.0175 mm (0.5 oz) | GND pour, +3V3 pour under `U7`, USB coupled pair, some power |
| 7 | dielectric 2 | core | 1.065 mm | FR4, er 4.5, loss tangent 0.02 |
| 8 | In2.Cu | copper | 0.0175 mm (0.5 oz) | GND pour, +5V, few signals |
| 9 | dielectric 3 | prepreg | 0.2 mm | FR4, er 4.5, loss tangent 0.02 |
| 10 | B.Cu | copper | 0.035 mm (1 oz) | components, power |
| 11 | B.Mask | solder mask | 0.01 mm | |
| 12 | B.Paste | paste | - | |
| 13 | B.SilkS | silkscreen | - | |

Total: 1.59 mm. `copper_finish` is `"None"` in the file and `"Finish": "None"` in the job
file; `dielectric_constraints` is `no` (no impedance-controlled stackup requested from the
file). The stackup is intended to be a standard 4-layer 1.6 mm class build with FR-4 and
"1 oz outer / 0.5 oz inner" copper (`fabrication/readme.md`, "Intended specification").

## 3. Surface finish, mask and silkscreen

| Item | Value in files | Recommendation in repo |
|---|---|---|
| Surface finish | not defined (`copper_finish "None"`) | ENIG recommended because of the 0.5 mm pitch LQFP-144 and DFN/HVSON packages; HASL not recommended (`fabrication/readme.md`) |
| Solder mask colour | not defined | green suggested (`fabrication/readme.md`) |
| Silkscreen colour | not defined | not determined (white implied by green mask convention; not stated in repo) |
| Silkscreen coverage | 52 references have no silkscreen text (inherited from baseline, cosmetic) | `docs/final-audit.md` |
| Edge plating / castellation | none | - |

## 4. Design rules

From `HybridPanda.kicad_pro` (`board.design_settings.rules`), plus the net classes. These
are the values the DRC checked against; the tightest values actually used on the board are
in section 5.

| Rule | Value | Note |
|---|---|---|
| Minimum clearance (copper to copper) | 0.1 mm | |
| Minimum track width | 0.127 mm | 5 mil |
| Minimum via diameter | 0.4 mm | |
| Minimum via annular ring | 0.125 mm | |
| Minimum through hole | 0.3 mm | |
| Hole clearance | 0.25 mm | |
| Hole to hole | 0.25 mm | |
| Copper to board edge | 0.2 mm | |
| Minimum text height / thickness | 0.8 mm / 0.08 mm | 45 inherited `text_height` DRC warnings below this |
| Minimum connection width | not set (KiCad default) | |

Net classes:

| Class | Nets | Track | Via (dia/drill) | Diff pair width / gap |
|---|---|---|---|---|
| Default | all others | 0.2 mm | 0.7 / 0.3 mm | 0.2 / 0.25 mm |
| CAN_DIFF | BUSx_H / BUSx_L | 0.25 mm | 0.7 / 0.3 mm | 0.25 / 0.2 mm |
| USB | USB_D+/-, USB_R_D+/- | 0.2 mm | 0.7 / 0.3 mm | 0.2 / 0.25 mm |

## 5. Values used on the board

| Parameter | Value | Source |
|---|---|---|
| Minimum track width present | 0.14 mm | extracted (on neck-down segments; most signal tracks 0.2 to 0.25 mm) |
| Minimum copper clearance present | DRC passes at 0.1 mm; 0 `clearance` violations | `hybrid_DRC_final.json` |
| Minimum drill | 0.300 mm (vias and `U6` thermal vias) | `drill_table.md` |
| Via sizes used | 0.6/0.3 mm (203), 0.7/0.3 mm (39) | extracted |
| Minimum annular ring | PTH 0.125 mm, via 0.150 mm | `drill_table.md` |
| Hole count | 270 (PTH 26, NPTH 2, via 242) | `drill_table.md`, `gerber_check.json` (Excellon vs PCB 270 vs 270) |
| Slots | 4 (1.199 to 1.2 mm wide, `P1` shell) | `drill_table.md` |
| Largest holes | 2.5 mm PTH x2 (`U3`), 0.8 mm NPTH x2 (`P1`) | `drill_table.md` |
| Smallest SMD pitch | 0.5 mm (`U7` LQFP-144, `U8`-`U11` HVSON-8) | footprints |
| Smallest passives | 0402 (39 capacitors, 22 resistors) | extracted footprint counts |

## 6. Impedance requirements

The project sets targets but **no impedance was simulated or confirmed**; KiCad DRC does not
check impedance (`fabrication/readme.md` item 1).

| Pair | Target | Layer / geometry on board | Analytic estimate in repo | Status |
|---|---|---|---|---|
| CAN BUSx_H/L (4 pairs) | 120 ohm differential (bus nominal) | F.Cu / B.Cu microstrip, 0.25 mm width, 0.2 mm gap over 0.2 mm prepreg to GND | 108 to 143 ohm range reported by `step6_reports.py` | not confirmed; short traces between transceiver and `P1`, termination is in the vehicle harness, not on the board |
| USB_R_D+/D- (full speed) | 90 ohm differential | In1.Cu coupled pair, 0.2 mm width, 0.3 mm gap, single layer up to `U13` (`correcoes-aplicadas.md` item 19) | not recomputed after the re-route | not confirmed; USB FS at 12 Mbit/s is tolerant, but nothing was measured |

Note: `fabrication/readme.md` item 2 still says that USB_D+/- was routed by Freerouting with
vias and not as a coupled pair. That text predates SI/PI item 19, which re-routed
`USB_R_D+/D-` as a coupled pair on In1.Cu. The MCU-side segments `USB_D+/-` (between `U7`
and the 22 ohm series resistors `R20`/`R21`) remain as routed. Whether the gerbers in
`hardware/fabrication/` reflect the post-item-19 board was not determined from the repo
(both were imported in the same commit); regenerate the package before any order.

## 7. DRC result summary

Tool: kicad-cli 10.0.7, all severities, `hardware/reports/hybrid_DRC_final.json`
(2026-10-28T10:16:47).

| Category | Count | Nature |
|---|---|---|
| Unconnected items | 0 | |
| Schematic parity | 0 | |
| `clearance`, `shorting_items`, `courtyards_overlap`, `copper_edge_clearance`, `starved_thermal`, `drill_out_of_range`, `footprint_type_mismatch`, `track_width`, `via_dangling` | 0 | the last four categories were present in the baseline/intermediate boards and were eliminated by the correction scripts |
| `lib_footprint_mismatch` | 73 | footprints in the board differ from the library copies (local edits, KiCad 10 library versions); informational |
| `text_height` | 45 | silkscreen text below 0.8 mm, inherited from baseline (baseline had 82) |
| `hole_clearance` | 8 | inherited from baseline (8/8); around `P1` / `U3` mounting holes |
| `silk_edge_clearance` | 4 | inherited (4/4) |
| `silk_overlap` | 4 | baseline 3 |
| `silk_over_copper` | 1 | baseline 0; cosmetic |
| **Total** | **135** | down from 182 before the SI/PI corrections (`correcoes-aplicadas.md`) |

All 135 remaining items are cosmetic or library-bookkeeping; none is an electrical
violation. They were deliberately not cleared (D-37, "deferred"). A DRC run with the final
board and an updated silkscreen is recommended before any order.

## 8. Fabrication files

Directory `hardware/fabrication/`, generated 2026-10-28 10:19:21 by
`hardware/scripts/step8_fabricate.py` with KiCad 10.0.7 `kicad-cli`.

### 8.1 Gerbers (`gerbers/`, RS-274X, Protel extensions, no X2 attributes)

| File | Layer |
|---|---|
| `HybridPanda-F_Cu.gtl` | top copper |
| `HybridPanda-In1_Cu.g1` | inner 1 |
| `HybridPanda-In2_Cu.g2` | inner 2 |
| `HybridPanda-B_Cu.gbl` | bottom copper |
| `HybridPanda-F_Mask.gts` / `HybridPanda-B_Mask.gbs` | solder mask |
| `HybridPanda-F_Paste.gtp` / `HybridPanda-B_Paste.gbp` | stencil |
| `HybridPanda-F_Silkscreen.gto` / `HybridPanda-B_Silkscreen.gbo` | legend |
| `HybridPanda-Edge_Cuts.gm1` | outline |
| `HybridPanda-job.gbrjob` | job file (stackup, thickness 1.59, finish None) |

### 8.2 Drill (`drill/`)

Excellon, mm, 3:3, suppress leading zeros: `HybridPanda-PTH.drl`, `HybridPanda-NPTH.drl`,
drill map as Gerber X2 (`.gbr`) and PDF for each.

### 8.3 Assembly (`assembly/`)

| File | Content |
|---|---|
| `BOM_JLC.csv` | JLCPCB-format BOM (Comment, Designator, Footprint, LCSC) |
| `CPL_JLC.csv` | JLCPCB-format placement (Designator, Mid X/Y, Layer, Rotation); origin = drill/aux origin 0.00, 0.00 mm; **rotations not normalised to the JLC convention** |
| `pos_kicad_both.csv` | KiCad native position file, both sides |

### 8.4 Other

| File | Content |
|---|---|
| `pdf/` | schematic, copper per layer (F, In1, In2, B), fabrication drawing top/bottom, assembly drawing top/bottom |
| `3d/HybridPanda.step` | STEP export (28.2 MB; VRML-only models omitted, so some 3D bodies are missing) |
| `drill_table.md`, `drill_table.json` | hole table |
| `gerber_check.json` | syntactic gerber/Excellon check only; no viewer check was done |
| `HybridPanda_gerbers_JLC.zip` | 16 entries: the 11 gerbers, the job file, PTH and NPTH drill files and the 2 drill-map PDFs; prepared for upload but **not to be uploaded** until the blockers below are closed |

## 9. Assembly notes

- SMD on both sides: 80 footprints top (includes `U7`, the four transceivers, `U6`, `U12`,
  `U1`, `P1`, `U3`, `J1`, `SW1`, `U5`), 45 bottom (mostly 0402 decoupling under `U7`, `JP1`,
  fiducials `FID4`-`FID6`). Exact side per reference is in `docs/hardware/bom.csv` (column
  `side`).
- Through-hole / mixed: `P1` (OBD-C receptacle, SMD signal pads plus THT shell), `U3`
  (USB-A, THT shell), both top. `U6` has 8 thermal vias under the exposed pad.
- Fiducials: 3 per side (1 mm copper, 2 mm mask opening, standard KiCad fiducial
  footprints).
- Paste layers were exported for both sides; stencil thickness is not specified in the repo
  (not determined).
- Panelization: not done; no rails, tooling holes or V-cuts.
- Minimum courtyard spacing inside the CAN transceiver block is below 1 mm (D-37, deferred);
  acceptable for machine placement, tight for rework.
- `U1` (AP22615AWU-7) is not stocked by JLCPCB; the alternative TPS2553DBVR (C55266)
  requires a different `R27` value (`hardware/reports/bom-real/bom-report.md`).
- Several LCSC codes are marked "to verify"; see [bom.md](bom.md). No LCSC code is
  confirmed in the catalogue.

## 10. Status and deferred items

**DO NOT FABRICATE.** The package exists for archive and review. The blocking reasons, as
listed in `hardware/fabrication/readme.md` and `docs/decisions.md` D-37:

1. Impedance (CAN 120 ohm, USB 90 ohm) only estimated analytically; stackup not agreed
   with a fabricator.
2. Zero physical validation: no board built, assembled or measured; the red panda firmware
   has never run on this hardware.
3. BOM: 1 reference without MPN (`JP1`), 2 without LCSC (`JP1`, `U1`); "to verify" LCSC
   codes not confirmed; `U1` unavailable at JLC.
4. 135 inherited DRC items (cosmetic) not cleared; silkscreen incomplete (52 refs).
5. Gerbers not reviewed in a viewer (only syntactic check).
6. CPL rotations not normalised.
7. Possible mismatch between the fabrication export and the final board (see section 6
   note); re-export required.
8. Deferred SI/PI items (`correcoes-aplicadas.md`: 9, 10, 16, 21/22/23, 25, 27, 29, 34,
   36), `C8` package change, `U1` alternative, courtyard spacing, and a new enclosure
   (the step at the USB-A edge and the taller components were not checked against the
   original black panda case).

Nothing in this document should be read as a claim that the board is manufacturable as is.

## 11. References

- `hardware/hybrid-panda/HybridPanda.kicad_pcb`, `HybridPanda.kicad_pro`.
- `hardware/fabrication/readme.md`, `drill_table.md`, `gerber_check.json`,
  `gerbers/HybridPanda-job.gbrjob`.
- `hardware/reports/hybrid_DRC_final.json`, `hardware/reports/final_audit.json`,
  `hardware/reports/correcoes-aplicadas.md`, `hardware/reports/si-pi-audit/si-pi-audit.md`.
- `hardware/research/step5-layout-h725.md` (layout and Freerouting),
  `step6-roteamento-impedancia.md` (impedance estimate), `step7-validacao.md`,
  `step9-bringup-e-teste-veiculo.md` (planned bring-up, not executed).
- `docs/decisions.md` D-02, D-05, D-33, D-37.
- `docs/final-audit.md`.
