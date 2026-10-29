# A8 - Inherited DRC cleanup

Date: 2026-10-28 17:07 (script run), re-checked 2026-10-29 after a fresh zone refill. Autor: Bruno Costa.
Script: `hardware/scripts/vpcb_a8_drc_cleanup.py`. Step log: `drc-cleanup.json`.
DRC reports: `drc_a8_before.json` (135 items), `drc_a8_after.json` (73 items), `drc_a9_final.json` (73 items, 2026-10-29,
`kicad-cli pcb drc --severity-all` after `pcbnew.ZONE_FILLER` refill and save).
Pre-pass snapshots: `hardware/hybrid-panda/snapshots/HybridPanda.kicad_pcb.pre_verification`, `.kicad_pro.pre_verification`.

## Before / after

| DRC type | Before | After | Note |
|---|---|---|---|
| hole_clearance | 8 | 0 | P1 peg NPTH vs shell slot pads |
| silk_edge_clearance | 4 | 0 | U3 and P1 silk outside the board edge |
| silk_over_copper | 1 | 0 | P1 silk over R1 pad 1 |
| silk_overlap | 4 | 0 | reference text over footprint silk (C11, C23/Y1, C30, C31) |
| text_height | 45 | 0 | reference fields 0.5 mm high (rule 0.8 mm) |
| lib_footprint_mismatch | 73 | 73 | intentional, see below |
| **Total** | **135** | **73** | |
| unconnected items | 0 | 0 | |
| schematic parity | 0 | 0 | |

The 2026-10-29 re-run gives the same 73 / 0 / 0.

## Change categories

### 1. P1 (USB-C receptacle, local footprint `USB-C-SMD_TYPE-C-USB-20`) - hole clearance (8 items)

The two locating-peg NPTH holes (0.8 mm) were 0.144 mm from the copper of the four shell slot pads (rule 0.25 mm, JLCPCB
hole-to-copper 0.254 mm). The HRO TYPE-C-31 family drawing and the KiCad/ai03 footprints of the same family use a 0.65 mm peg
hole, so: NPTH drill 0.8 -> 0.65 mm (2 holes) and the four slot pads' copper 1.0x1.6 -> 1.0x1.5 mm along the slot axis (drill
0.6x1.2 mm kept; annular ring 0.15 mm at the slot ends, 0.2 mm at the sides). Positions: 140.590,63.370; 136.180,63.010;
136.180,54.750; 140.590,54.390. The same edit was applied to `HybridPanda.pretty/USB-C-SMD_TYPE-C-USB-20.kicad_mod` so the
library and board copies agree for the pads (the `drc-cleanup.json` line "0/3 library edits applied" refers to the final run
finding the file already updated by the first run).

### 2. Silk outside the board edge (4 items)

The silk outlines of U3 (USB-A) and P1 (USB-C) extended beyond the east edge (x > 142.935 mm). The segments at x = 143.557 (U3)
and x = 143.107 (P1) were removed and the adjacent segments shortened in the board footprints and in the two library files
(`USB-A-TH_10.0QHHTZB6.3.kicad_mod`, `USB-C-SMD_TYPE-C-USB-20.kicad_mod`). Connectors overhanging the edge are normal; the silk
was simply drawing the shell outline beyond the copper area.

### 3. Silk over copper (1 item)

The P1 silk segment crossing R1 pad 1 was split around the pad (reported inside the `silk_edge`/`silk_over_copper` steps; after
the P1 silk trim the collision no longer exists, so the dedicated step logged no further edit).

### 4. Reference text height (45 items) and thickness (24 items)

45 visible reference fields were 0.5 mm high (OpenBlackPanda baseline); they were set to 0.8 x 0.8 mm / 0.15 mm thickness
(JLCPCB silk minimum: 0.8 mm height, 0.15 mm stroke). 24 other references already 0.8 mm high had their stroke set to 0.15 mm.
List in `drc-cleanup.json` (`text_resized_to_0.8_0.15`, `text_thickness_to_0.15`).

### 5. Reference text placement (66 refs: 54 moved, 12 hidden) - silk overlap

Bigger text collides more. Every reference that collided with footprint silk, pads, the edge, or another reference was moved to
the nearest free spot around its footprint (search radius ~3 mm, 0.5 mm steps, 4 rotations; distance moved 0.3-3.2 mm, per-ref
table in `drc-cleanup.json/steps/text_moves`). For 12 references no free spot existed inside the search radius and the field was
hidden: C12, C18, C20, C23, C24, C28, C29, C6, D2, D7, Q4, R5. These are 0402 decoupling capacitors / resistors packed around
the MCU and the crystal (C23/C24), the TVS D2/D7, the FET Q4 and R5; the assembly drawing PDF (`fabrication/pdf/*_assembly_*.pdf`)
and the CPL still identify them. Hidden references are a cosmetic cost accepted to get the silk DRC to zero.

### 6. The remaining 73 `lib_footprint_mismatch` - intentional

The board footprints differ from the project library `HybridPanda.pretty`. Per
`hardware/reports/verification/footprint-vs-datasheet.md` (section "73 DRC lib_footprint_mismatch refs - classification"):

- about 61 refs (all 0402/0603/0805 C/R, FB1, fiducials, D1, D5-D9, L3, Q4, U1, U8-U11): graphics, 3D model path
  (`${KICAD10_3DMODEL_DIR}`) or `attr` flag differences only; pads identical to the library. No fabrication impact.
- Q1, Q2, Q3, U5, Y1: the board copy carries the corrected pad geometry from the footprint audit (`corr_step1_footprints.py`);
  the library still has the old pads. The board is the good one.
- P1, U6, U12: pad layer/size differences documented in that report (P1 B-row PTH pad 0.65 vs lib 0.60; U6 mask/paste polygons;
  U12 EP on F.Cu only). The P1 pad edits of this pass were mirrored into the library, but the board copy still differs in the
  other items listed there.

This pass also moved/resized reference texts and trimmed connector silk on the board copies, which by itself keeps the mismatch
for those footprints. Updating `HybridPanda.pretty` from the board ("Update footprint library from board" in KiCad) would zero
the count; it was left for a human because the library files are also the source for the next revision and the 3D model paths
differ by install.

## What this does not show

- DRC is the KiCad rule set in `HybridPanda.kicad_pro` (clearance 0.1, hole clearance 0.25, silk 0.8/0.15), not a fabricator
  DFM run. Silk legibility, text over vias and hidden references were not reviewed by eye; see the renders in
  `gerber-render/` (A3/A4, `gerber-review.md`).
- All changes are software-only, not physically verified.

## Addendum 2026-10-29 (hand-assembly and thermal-via edits, see `hand-assembly.md`)

- `solder_mask_min_width` 0 -> 0.1 mm in `.kicad_pcb` and `.kicad_pro`. The mask-to-silk DRC then reported 2 new
  `silk_over_copper` items (C32 reference over the FID2 mask ring; U6 pin-1 circle between the C37 pads); both fixed by moving
  the silk (C32 ref to 138.3,74.052 rot 90; U6 circle to 104.7,39.45 r 0.1 w 0.15).
- `vpcb_a10_thermal_vias.py`: one GND via 0.6/0.3 mm inside each DFN exposed pad (U8, U9, U10, U11); the In2.Cu BUS1N_STB
  segment across the U8 pad was replaced by a 0.3 mm jog (y 60.609 -> 60.305 between x 126.45 and 128.6). Vias 236 -> 240,
  holes 264 -> 268, tracks 1220 -> 1223.
- DRC after the edits (`drc_a9_final.json`, zones refilled): 73 `lib_footprint_mismatch`, 0 unconnected, 0 clearance,
  0 solder_mask_bridge, 0 silk_over_copper, 0 parity. `final_audit.py`: 0 shorts, 0 via-in-pad (the 9 same-net vias inside
  the U6/U8-U11 exposed pads are listed as thermal vias), only the 121 acute-angle junctions (BAIXO, cosmetic) remain.
- `final_audit.py` itself was fixed: `PCB_VIA.GetWidth()`/`PAD.GetSize()` need a layer argument in KiCad 10 (the assert
  opened a modal dialog and hung the run), paste-only aperture pads are no longer counted as "pad of another net", and solder
  jumpers (JPx) are not required to have an MPN.

---

pt-BR: Limpeza do DRC herdado do OpenBlackPanda: 135 -> 73 itens, 0 nao conectados. Corrigidos: 8 hole_clearance (pinos guia
NPTH do P1 0.8 -> 0.65 mm e pads das fendas 1.0x1.6 -> 1.0x1.5 mm, tambem na biblioteca), 4 silk fora da borda (U3/P1),
1 silk sobre cobre (P1/R1), 45 referencias com texto 0.5 -> 0.8/0.15 mm, 24 com espessura 0.15, 54 referencias movidas e 12
ocultadas (C12, C18, C20, C23, C24, C28, C29, C6, D2, D7, Q4, R5). Os 73 lib_footprint_mismatch restantes sao intencionais:
~61 so grafica/caminho 3D, Q1/Q2/Q3/U5/Y1 com a placa corrigida e a biblioteca desatualizada, P1/U6/U12 documentados no
relatorio de footprints. Nada verificado fisicamente.
