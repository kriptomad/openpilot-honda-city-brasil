# A7 - CPL rotation normalisation for JLCPCB

Date: 2026-10-28 (PCB engineering pass). Autor: Bruno Costa. Board: `hardware/hybrid-panda/HybridPanda.kicad_pcb`.

## What was done

- `hardware/scripts/step8_fabricate.py` now writes `hardware/fabrication/assembly/CPL_JLC.csv` with the rotation
  column normalised to the JLCPCB convention, plus a per-reference audit file
  `assembly/CPL_rotation_corrections.csv` (KiCad rotation, mirrored angle, matching rule, correction, JLC rotation).
  `assembly/pos_kicad_both.csv` stays the raw `kicad-cli pcb export pos` output.
- Correction table: `hardware/scripts/cpl_rotations_db.csv`, the `cpl_rotations_db.csv` of matthewlai/JLCKicadTools,
  which is the file the Bouni kicad-jlcpcb-tools plugin downloads at runtime (`correction_data.py` ->
  `CorrectionData.download`; the `corrections.py` module named in the brief does not exist in the current plugin tree).
  59 upstream rules + 5 local rules (see below) = 64 rules.
- Algorithm (same as the Bouni plugin, `fabrication.py` / `correction_data.py`):
  1. `rot = KiCad orientation`; if the footprint is on the bottom side: `rot = (180 - rot) mod 360`;
  2. the rule is searched with `re.search` on the reference, then the value, then the footprint library item name;
     the match that consumes the most characters wins;
  3. `JLC rotation = (rot + correction mod 360) mod 360`. Rule offsets (X/Y) are reported but NOT applied
     (only J1 has one, 2.54/0.635 mm; J1 is a DNP-for-assembly debug header, hand soldered).

## Corrections applied (118 CPL rows, 24 corrected)

| Footprint | Rule | Correction | Refs | Origin of the rule |
|---|---|---|---|---|
| `LQFP-144_20x20mm_P0.5mm` | `^LQFP-` | +270 | U7 (bottom) | upstream |
| `DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm` | `^DFN-` | +270 | U8, U9, U10, U11 | upstream |
| `SOT-23-6` | `^SOT-23` | -90 | U1, U13 | upstream |
| `SOT-23` | `^SOT-23` | -90 | D13, D14 (bottom) | upstream |
| `PowerPAK_SO-8_Single` | `^PowerPAK_SO-8_Single` | +270 | Q4 | upstream |
| `PinHeader_2x05_P1.27mm_Vertical_SMD` | `^PinHeader_2x05_P1\.27mm_Vertical` | +90 (offset not applied) | J1 (bottom) | upstream |
| `SOT-323_SC-70` | `^SOT-323_SC-70` | -90 | Q3 | local: same pad layout as KiCad SOT-23 (pin 1 top-left, pin 3 right) |
| `SOT95P230X110-3N` (BlackPanda) | `^SOT95P230X110-3N$` | -90 | D5-D9 | local: same pad layout as KiCad SOT-23 |
| `SOT23-3` (BlackPanda) | `^SOT23-3$` | +180 | Q1, Q2 | local: KiCad SOT-23 layout rotated -90 deg (pins 1/2 at the top, pin 3 bottom) |
| `CONV_TPS5450DDAR` (BlackPanda) | `^CONV_TPS5450DDAR$` | +270 | U6 | local: SOIC-8 PowerPAD layout, pin 1 top-left like KiCad SOIC |
| `Diodes_PSOP-8` | `^Diodes_PSOP-8` | +270 | U12 | local: KiCad library footprint, SOIC-8 layout, no upstream rule |

Local rules were derived by comparing the pad coordinates of the footprint (in its own frame) with the KiCad
library footprint that the upstream rule covers; they are added at the end of `cpl_rotations_db.csv` after a
`#` comment line (the loader skips `#` lines).

## Without a rule (rotation = KiCad rotation, mirrored on bottom) - must be checked by a human in the JLC assembly preview

| Footprint | Refs | Note |
|---|---|---|
| `C_0402/0603/0805`, `R_0402/0603`, `L_0603` | 58 C, 24 R, FB1 | non-polarised two-terminal parts: rotation irrelevant |
| `D_SOD-123`, `D_SOD-123F`, `D_SOD-323`, `D_SMA`, `D_SMC` | D15 (bottom), D10, D2, D11, D12 | polarised; no diode rule in the upstream table; cathode (pad 1) is at -X in the KiCad footprints, JLC's SOD/SMA parts place the cathode per the LCSC part drawing - verify each one |
| `DIOM4325X250N` (BlackPanda) | D1 (SMAJ16CA, bidirectional TVS) | pad 1 is at +X (opposite of KiCad `D_SMA`); part is bidirectional, orientation irrelevant electrically |
| `LED-ARRAY-SMD_4P-L2.2-W2.1-BR` (BlackPanda) | U5 | 4-pad RGB LED, pin 1 bottom-right in the footprint frame; polarised - verify |
| `Crystal_SMD_3225-4Pin_3.2x2.5mm` | Y1 (bottom) | pin 1 position matters (GND pads 2/4) - verify |
| `L_Murata_DFE201610P`, `IND-SMD_L7.3-W6.8`, `L_10.5x11.5_H4.0` | L5 (bottom), L3, L4 | non-polarised inductors; L4 is a 2-pad power inductor |
| `SW_SPST_SKQG_WithStem` | SW1 | symmetric tactile switch |
| `USB-C-SMD_TYPE-C-USB-20` (BlackPanda) | P1 | local receptacle footprint, no upstream rule (the upstream `USB_C_Receptacle_HRO_TYPE-C-31-M-12` rule is +180 for the KiCad library part); keyed by the shell - verify |
| `USB-A-TH_10.0QHHTZB6.3` (BlackPanda) | U3 | THT, keyed by shell; JLC THT assembly may not be offered for it |

## Limits

- Nothing here was compared with the JLC assembly preview or with LCSC part drawings; the table encodes the
  community convention for the KiCad library footprints and my reading of the local footprint pad layout.
- The bottom-side mirror formula `(180 - rot)` is the Bouni plugin convention; some users report JLC accepting
  `-rot` instead. If the preview shows bottom parts (U7, D13, D14, J1, Y1, D15, L5) rotated wrongly by 180 deg,
  that is the first thing to change.
- Per-row data: `hardware/fabrication/assembly/CPL_rotation_corrections.csv` (regenerated in A9).

---

pt-BR: O `CPL_JLC.csv` agora sai do `step8_fabricate.py` com a rotacao convertida para a convencao da JLCPCB
usando a mesma tabela e o mesmo algoritmo do plugin kicad-jlcpcb-tools (Bouni): 24 referencias corrigidas
(LQFP-144, DFN-8, SOT-23, SOT-23-6, SOT-323, PowerPAK, TPS5450, PSOP-8, SOT23-3 locais) e 94 sem regra, das quais
os diodos, o LED RGB, o cristal e os conectores precisam ser conferidos por uma pessoa na previa de montagem da JLC.
Nada foi conferido contra a previa real.

