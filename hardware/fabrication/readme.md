# Hybrid Panda fabrication package

**STATUS: SOFTWARE-VERIFIED, NOT PHYSICALLY VERIFIED. Bare-PCB order is at the owner's discretion (small batch first).**
Every check that can be done in software has been run and passed (DRC/ERC, gerber-rebuilt connectivity 0 short / 0 open,
drill count, outline, pin-by-pin review against the panda firmware and the STM32H725 datasheet, footprint review for hand
soldering). What remains cannot be closed without a built board. No board has ever been built from this package; the
Hybrid Panda is unproven hardware.

Hybrid Panda = black panda form factor + STM32H725ZGT6 running the red panda firmware.
Generated 2026-10-29 16:44:34 by [`hardware/scripts/step8_fabricate.py`](../scripts/step8_fabricate.py)
with KiCad 10.0.7 `kicad-cli` from [`hardware/hybrid-panda/HybridPanda.kicad_pcb`](../hybrid-panda/HybridPanda.kicad_pcb).
Intended order: bare PCB only (JLCPCB), all components bought and hand-soldered by the user.
Items marked "addressed by software, not physically verified" were changed in the PCB engineering pass of 2026-10-29
(reports in [`hardware/reports/verification-pcb/`](../reports/verification-pcb/)); items marked "requires a built board" can only be closed after a board exists.

Independent adversarial review 2026-10-29 ([`../reports/verification-pcb/adversarial-review.md`](../reports/verification-pcb/adversarial-review.md), helper scripts in [`hardware/scripts/adv/`](../scripts/adv/)):
DRC rerun with a JLCPCB 4-layer rule set (`scripts/adv/jlc_4layer.kicad_dru`: 0.09/0.09 mm, via 0.45/0.2, annular 0.13, hole-to-copper 0.254, hole-to-hole 0.5, edge 0.3).
PCB edits from that review, all regenerated into this package: six different-net via pairs nudged to >= 0.5 mm hole-to-hole; GND via near the VCAP track moved so hole-to-copper >= 0.27 mm; 1.2 mm no-pour rule areas around P1's two NPTH pegs (hole-to-copper 0.275 mm); +12V meander and C28 pulled back from the right edge to >= 0.3 mm. Pre-review PCB kept as `../hybrid-panda/snapshots/HybridPanda.kicad_pcb.pre_adversarial`.
Still below the brief's JLC numbers and deliberately left as-is: BUS1N_H tracks at 0.21-0.235 mm and GND zone at 0.20 mm from the right edge (project rule 0.2 mm = JLC's published trace-to-outline figure for routed boards; the brief asked 0.3), P1 B-row PTH annular ring 0.125 mm and B-row hole-to-hole 0.40 mm (inherent to the TYPE-C-31-M-04 footprint). Expect a possible engineering query from JLC on these; none is a functional defect.

## Status of each former blocker

### PCB fabrication (bare board)

1. CAN and USB impedance/skew: analytical estimate only (`step6_reports.py`, [`../reports/verification-pcb/impedance.md`](../reports/verification-pcb/impedance.md): Hammerstad-Jensen / Kirschning-Jansen for the file stackup and for JLCPCB JLC7628; USB netclass 0.35/0.15 mm, CAN_DIFF 0.22/0.23 mm). KiCad's DRC does not check impedance; the stackup is assumed, not confirmed with the fabricator; no TDR. **Addressed by software, not physically verified**
2. `USB_D+/-`: rerouted as an edge-coupled pair on B.Cu with one symmetric via pair and 0.35/0.15 mm width/gap, skew < 0.3 mm ([`../reports/verification-pcb/usb-reroute.md`](../reports/verification-pcb/usb-reroute.md)); previously 2 vias per net on In1.Cu. USB FS 12 Mbit/s is tolerant either way. **Addressed by software, not physically verified**
3. DRC inherited from the OpenBlackPanda baseline: now lib_footprint_mismatch 73 ([`../reports/verification-pcb/drc-cleanup.md`](../reports/verification-pcb/drc-cleanup.md); `lib_footprint_mismatch` is intentional: local footprint edits). Clearance/unconnected/shorts/courtyards = 0/0/0/0. **Addressed by software, not physically verified**
4. Gerber review executed in software ([`../reports/verification-pcb/gerber-review.md`](../reports/verification-pcb/gerber-review.md)): 11 layers rendered to PNG (`../reports/verification-pcb/gerber-render/`), Edge.Cuts outline 51.02 x 46.75 mm vs PCB 51.02 x 46.75 mm, drill hits 268 vs PCB holes 268, copper connectivity rebuilt from the gerbers + drill and compared with the KiCad netlist: 0 short(s), 0 open(s) over 142 nets. **Addressed by software, not physically verified** A human look in KiCad GerbView is still part of the remaining checks below.
5. Via-in-pad: 0 (`final_audit.py` definition: via centre inside an SMD pad of another net or of a small pad); 9 same-net thermal vias inside exposed pads (U6 PowerPAD, U8-U11 DFN EP, placed by `vpcb_a10_thermal_vias.py`) are deliberate ([`../reports/verification-pcb/hand-assembly.md`](../reports/verification-pcb/hand-assembly.md)). **Addressed by software, not physically verified**
6. Hand-solder friendliness: solder mask minimum web 0.1 mm (`solder_mask_min_width`), mask slivers >= 0.2 mm between U7 LQFP-144 and P1 USB-C 0.5 mm pads, DFN pin-to-EP mask 0.13 mm, one 0.6/0.3 mm GND via in each DFN exposed pad, vias tented both sides; ENIG recommended ([`../reports/verification-pcb/hand-assembly.md`](../reports/verification-pcb/hand-assembly.md)). **Addressed by software, not physically verified**
7. No board was fabricated, assembled or measured: zero physical verification (continuity/isolation of the built board, impedance, power rails, USB enumeration, CAN). **Requires a built board.**

### Assembly (manual, by the user)

8. BOM: 1 reference(s) without MPN and 2 without LCSC code (of 119); U1 AP22615AWU-7 is no longer in the JLC catalogue (buy from Mouser/Digi-Key). The user buys and hand-solders every part, so LCSC codes and basic/extended status are informational only.
9. Component rotation in `assembly/CPL_JLC.csv` is normalised with the JLC correction table (64 rules, `hardware/scripts/cpl_rotations_db.csv`): 11 footprint type(s) corrected, 20 without a rule ([`../reports/verification-pcb/cpl-rotation.md`](../reports/verification-pcb/cpl-rotation.md)). Only relevant if JLC assembly is ever ordered; not needed for a bare board.
10. ARM toolchain: installed locally (Arm GNU 14.2.Rel1) but the firmware for this hardware (`hybrid-h725` branch in [`firmware/`](../../firmware)) has never run on hardware; depends on the commaai DFU/signing flow (see STEP 9). **Requires a built board.**

## Remaining human checks

- Visual review of the PCB in KiCad (placement, silk legibility, polarity marks, reference designators) by a person.
- Open `HybridPanda_gerbers_JLC.zip` in KiCad GerbView (or the JLCPCB online viewer) and compare with the renders in `../reports/verification-pcb/gerber-render/`.
- Independent review by a second person (schematic against datasheets and PCB layout).
- Order a small batch of bare boards first (no assembly); continuity/isolation test with a multimeter before populating.
- JLC assembly preview for rotations: only if JLC assembly is ever ordered (not planned).

## STEP 7 results (`../reports/step7_validation.json`)

- ERC errors = 0, warnings = 373
- DRC unconnected = 0, clearance = 0, shorts = 0, courtyards = 0
- Netlist divergences = 0; parity conflicts = 0
- DRC by type (hybrid/baseline): lib_footprint_mismatch 73/67

## Contents

| Path | Content |
|---|---|
| `gerbers/` | RS-274X (Protel extensions, no X2): F/In1/In2/B.Cu, F/B.Mask, F/B.SilkS, F/B.Paste, Edge.Cuts, job file |
| `drill/` | Excellon PTH + NPTH (mm, 3:3, suppress leading), map PDF and Gerber X2 |
| `assembly/` | `BOM_JLC.csv`, `CPL_JLC.csv` (origin = drill/aux origin 0.00,0.00 mm, rotation per JLC table), `CPL_rotation_corrections.csv`, `pos_kicad_both.csv` (raw KiCad) |
| `pdf/` | schematic, copper per layer, fab/assembly top and bottom |
| `3d/HybridPanda.step` | 3D model (missing models substituted) |
| `drill_table.md` / `.json` | 268 holes (PTH 26, NPTH 2, VIA 240); min drill 0.300 mm; min annular ring PTH 0.125, VIA 0.150 |
| `gerber_check.json` | syntactic check; Excellon holes vs PCB: 268 vs 268 |
| `HybridPanda_gerbers_JLC.zip` | gerbers + drill for upload (bare PCB); read the status and the remaining human checks above first |

Intended specification: 4 layers, 1.59 mm, FR-4 (er ~4.5 assumed; JLC7628 used for the impedance estimate), copper 1 oz outer / 0.5 oz
inner, min track/space 0.127/0.1 mm, via 0.4/0.3 mm, min hole 0.30 mm, ENIG recommended
(QFN/LQFP 0.5 mm pitch), green mask, HASL not recommended.

Generation problems: none. Notes: STEP gerado (28.2 MB) com aviso: modelos VRML ignorados (kicad-cli exit 2; 6 avisos no stderr truncado) — corpos 3D desses footprints ausentes.

---

pt-BR: **VERIFICADO POR SOFTWARE, NAO VERIFICADO FISICAMENTE.** Pedido de PCB nua a criterio do dono (lote pequeno primeiro). Nenhuma placa foi construida e
falta verificacao fisica e revisao humana. A encomenda prevista e so da PCB nua (JLCPCB), com todos os componentes
comprados e soldados a mao pelo utilizador. Os itens marcados "addressed by software, not physically verified"
(impedancia com stackup JLC7628, par USB acoplado, limpeza do DRC herdado, revisao dos gerbers com comparacao de
conectividade, vias termicas nos DFN, mascara minima 0.1 mm, rotacao do CPL) foram alterados apenas em software
no passe de 2026-10-29; os restantes (zero placas construidas, firmware nunca executado) exigem uma placa fisica.
