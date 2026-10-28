# Hybrid Panda - footprint vs datasheet land pattern (software-only)

Status: verified by software only. Nothing was physically verified. No board was assembled or measured.

Machine-readable result: `footprint-vs-datasheet.csv` (one row per footprint used on the board: 33 footprints, 125 placed footprints incl. 6 fiducials and JP1). Columns: footprint, lib, refs, qty, pad_count, pad_sizes_mm, pad_x/y_positions (mm, footprint-local), min_pitch_mm, courtyard_mm, attr, drc_lib_mismatch, reference_source, reference_pattern, verdict, detail.

## Method

1. PCB snapshot: `work/snapshot.kicad_pcb` = copy of `hardware/hybrid-panda/HybridPanda.kicad_pcb` at 2026-10-28 15:36 (SHA-256 `BB274802...63AD`, git HEAD `0b4802a`, worktree had uncommitted gerber changes by another agent). The other agent keeps editing the PCB; this report describes that snapshot only.
2. Geometry extracted with KiCad 10 pcbnew Python (S-expression parsed by KiCad itself, not by regex): `hardware/reports/footprint-audit/footprint_dump.py` -> `work/board_dump.json`; pads + mask/paste graphics for EP parts with `work/gfx_dump.py`; `kicad-cli pcb drc --severity-all` -> `work/drc_snapshot.json` (135 violations: 73 lib_footprint_mismatch, 45 text_height, 8 hole_clearance, 4 silk_edge_clearance, 4 silk_overlap, 1 silk_over_copper); board-vs-project-library pad diff with `lib_compare.py` -> `work/lib_compare_snapshot.json`.
3. Reference land patterns, in this order of preference: (a) existing repo audits `hardware/reports/footprint-audit/footprint-audit.md` and its datasheet PNGs (TYPE-C-31-M-04, FM-B1921, NXP SOT782-1), (b) `hardware/reference/datasheets/DS13313_text.txt` (STM32H725 LQFP144), (c) manufacturer PDFs fetched to `work/ds/` (TI TPS5450 + DDA0008J mechanical, Diodes B340A, Diodes DDTA143ECA, Murata DFE201610E/P), (d) KiCad 10 standard library / IPC-7351 nominal values for JEDEC packages (0402/0603/0805, SOT-23, SOT-23-6, SC-70, SOD-123/123F/323, SMA/SMC, PowerPAK SO-8, 3225 crystal, SKQG, 1.27 mm header).
4. Network: corporate proxy blocks jlcpcb.com, lcsc.com, nexperia, nxp, st.com, littelfuse, amphenol CDN, xlsemi, vishay. 7 PDFs obtained; one (DS30021 for D12) turned out to be the B2x0 SMB series and was discarded for comparison.

Verdict scale: `OK` = matches manufacturer pattern within 0.1 mm; `OK (lib)` = identical to the KiCad standard library pattern for a JEDEC package, manufacturer PDF not opened; `minor deviation` = differs from the reference by a stated amount, judged solderable; `MISMATCH` = pad count/pitch/position wrong or mask/paste error that would block assembly; `not checked` = no reference obtained.

## Counts (33 footprints)

| Verdict | Footprints | Placed refs |
|---|---:|---:|
| OK | 12 | 98 |
| OK (lib) | 10 | 11 |
| minor deviation | 8 | 13 |
| MISMATCH | 0 | 0 |
| not checked | 3 | 3 |

No MISMATCH was found on the current snapshot. The pad-position errors reported by the earlier audit (Q1/Q2 SOT23-3 square pads, Q3 SC-70 offset, U5 LED y-spacing) are corrected on the board copy of the footprints; the project library `HybridPanda.pretty` still carries the old versions, which is why DRC flags them as `lib_footprint_mismatch`.

## 73 DRC `lib_footprint_mismatch` refs - classification

| Class | Refs | What differs (board vs project lib) | Assessment |
|---|---|---|---|
| Graphics / 3D model path / attribute only, pads identical | C1-C8, C10-C12, C14, C16-C21, C23, C24, C26-C34, C37 (0402/0805), R2, R3, R5, R9, R14-R21, R23, R24, R26, R27 (0402), FID1-6, D1, D5-D9, L3, Q4, U1, U8-U11 | silk/fab/courtyard lines, `${KICAD10_3DMODEL_DIR}` model path, `attr` flags | cosmetic; no fab impact |
| Board copy corrected, library stale | Q1, Q2 (SOT23-3: board 0.6x1.475 pads, lib 0.914 sq), U5 (board y +-0.60, lib +-0.50), Q3, Y1 (rect vs roundrect, same size) | pad geometry | board is the good one; library should be updated by the PCB agent so DRC goes clean |
| Pad differences with fab meaning | P1 (B-row PTH pad 0.65 vs lib 0.60), U6 (via pads 9 vs lib 9..17, pins without F.Mask), U12 (pad 9 EP layers F.Cu only) | pad layers/sizes | see detailed items below |

## Priority items

### U6 TPS5450DDAR - `CONV_TPS5450DDAR` (PowerPAD SO-8, exposed pad) - minor deviation
Reference: TI DDA0008J mechanical drawing (`work/ds/ti_dda_mech.pdf`): 8 pads 1.55x0.6 mm, pitch 1.27, row centers 5.4 apart; thermal pad 2.95x4.9; solder mask/stencil opening 2.6x3.1 over EP; 9 vias 0.2 mm drill on 1.3 mm grid.
Board: pads 1-8 1.55x0.6 at pitch 1.27, rows 5.4 apart = match. EP pad 2.95x4.9 F.Cu = match. Via pads 0.6/0.3 drill at (+-0.65, +-0.65/+-1.95) and center = TI positions, drill 0.3 vs 0.2 (acceptable, larger wicking risk). Deviations: pins 1-8 are on F.Cu + F.Paste but NOT on F.Mask; the mask opening is instead drawn as eight F.Mask polygons 1.70x0.75 and the EP mask/paste openings are F.Mask/F.Paste polygons 2.61x3.11 (centre). The result in gerbers is equivalent to TI's recommendation, but the footprint depends on graphic polygons for mask/paste (fragile when edited, invisible to pad-level DRC). Footprint `attr` is THT, so U6 is treated as a through-hole part by BOM/CPL exports and DRC rules. Recommendation for the PCB agent: convert to a normal SMD footprint with pads on F.Mask, EP pad with paste ratio or explicit paste pads, attr SMD. Not blocking.

### U12 XL1509-3.3E1 - `Diodes_PSOP-8` - minor deviation
Catalog package for C74193 is plain SOP-8 (no exposed pad), confirmed by the XLSEMI datasheet pinout (pins 5-8 GND, no EP). Board pads 1-8 1.5x0.65 at pitch 1.27, span 5.4 = JEDEC MS-012 150 mil, OK. The 4 "pad 9" EP pads (1.35x1.8) are F.Cu only, without mask or paste: covered copper under the body, electrically connected to GND. Harmless; could be removed or left as heat spreader.

### U8-U11 TJA1042TK/3/1J - `DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm` - minor deviation
Reference: NXP SOT782-1 reflow pattern (from `footprint-audit.md`): pad 0.30x0.525, pitch 0.65, outer span 3.25, inner 2.20, EP 2.45x1.65, paste 4x 1.10x0.65.
Board (KiCad generic 3x3 DFN): pad 0.35x0.65 at x +-1.55 (outer span 3.45 = +0.20 mm, inner 2.75 = +0.55 mm vs NXP i.e. pads sit further out), EP 1.55x2.4 (-0.10/-0.05), paste 4x 0.6x1.0 (~40% of EP). Pitch and pin count correct. Solderable with the longer toe; the inner edge of the pads is 0.275 mm farther from the EP than NXP recommends, which reduces the bridging risk. No change required; a dedicated SOT782-1 footprint would be closer to the vendor pattern.

### Q4 HY12P03C2 - `PowerPAK_SO-8_Single` - OK (lib)
Identical to KiCad library; catalog package PPAK5x6-8L. HUAYI drawing not fetched; the PowerPAK SO-8 / PDFN5x6 land pattern is an industry-standard outline. DRC mismatch is the 3D model path only.

### U7 STM32H725ZGT6 - `LQFP-144_20x20mm_P0.5mm` (B.Cu) - minor deviation
Reference: ST DS13311/DS13313 Figure 82 footprint example: pad 0.35x1.35, pitch 0.50, outer span 22.60, inner 19.90.
Board (KiCad lib): pad 0.30x1.475 at centre +-10.6625 -> outer 22.80 (+0.20), inner 19.85 (-0.05), width 0.30 (-0.05). Within IPC nominal; 144 pads, pitch 0.5, numbering CCW from pin 1 at the marked corner. Pin-1 chamfer is in the footprint silk/fab.

### L5 DFE201610E-2R2M - `L_Murata_DFE201610P` - OK
Murata recommended pattern 2.0 x 1.6 total, 0.9 gap -> pads 0.55x1.6 at +-0.725: exact match with the board.

### D1 SMAJ16CA-13-F TVS - `DIOM4325X250N` - minor deviation
Diodes SMA pattern (from B340A DS): pads 2.5 long x 1.7 wide at +-2.0 (span 6.5). Board: 2.12x1.5 at +-2.115 (span 6.35). Pad 0.38 mm shorter and 0.2 mm narrower than vendor pattern. Solderable; a plain KiCad `D_SMA` (as used for D11) would be the better choice.

### D11 B340A-13-F - `D_SMA` - OK (2.5x1.8 vs 2.5x1.7). D12 B540C-13-F - `D_SMC` - OK (lib) (3.3x2.5 at +-3.4; Diodes SMC PDF not obtained).

### Q1/Q2 DDTA143ECA-7-F - `SOT23-3` (project lib, edited on board) - minor deviation
Diodes SOT23 pad layout (fetched): pad 0.8 x 0.9, pitch 0.95, row span 2.0, overall 2.9. Board: 0.6x1.475 at (+-0.95, -1.0) / (0, +1.0): row span 2.0 OK, pitch 0.95 OK, pad narrower by 0.2 and longer by 0.575 (KiCad-style). Pin numbering 1,2 bottom row, 3 top = SOT-23 standard. Project library still has 0.914 mm square pads at the old positions -> update library.

### D5-D9 PESD2CAN - `SOT95P230X110-3N` - OK (1.0x0.6 at x +-1.15, y 0/+-0.95; IPC SOT23 pattern). D13/D14 BAT54S - `SOT-23` (KiCad) - minor deviation vs Diodes/Nexperia pattern (0.6 vs 0.8 wide), standard library.

### Connectors
- P1 TYPE-C-31-M-04 - `USB-C-SMD_TYPE-C-USB-20` - minor deviation. HRO drawing (audit PNG): SMD 0.3x0.9 pitch 0.5 (match), PTH drill 0.4 (match; board annular pad 0.65 vs project lib 0.60 -> DRC mismatch; 0.65 is better), shell slots: vendor hole 0.5x1.1, board drill 0.6x1.2 pad 1.0x1.6 (+0.1 mm each side, acceptable), 2 NPTH 0.8 locating pegs. No courtyard defined (should be added). attr THT is acceptable for a hybrid part but JLC places it as SMT; the CPL lists it on Top.
- U3 USB-A 10.0 QHHTZB6.3 - `USB-A-TH_10.0QHHTZB6.3` - not checked: vendor drawing only behind the blocked JLC link. Board: 4 SMD signal pads 1.12x2.88 at x +-1.0/+-3.5 (pitch 2.0/2.5 - the standard USB-A 2.0 mm pitch), 2 oval PTH 1.2x3.1 drill 0.7x2.5 at x +-6.45 for the shell (span 12.9), no courtyard. Geometry is consistent with the usual "SMD USB-A with THT shell" family, but the specific MPN is not verified. Human: open the LCSC drawing for C668591 and compare shell slot spacing 12.9 and pad row offset 4.395 from the shell holes.
- SW1 SKQGAFE010 - `SW_SPST_SKQG_WithStem` - OK (lib): KiCad footprint follows the Alps SKQG drawing (pads 1.8x1.1 at +-3.1/+-1.85); PDF not fetched.
- J1 SWD 1.27 mm header - OK (lib); Amphenol drawing not fetched.

### Inductors L3/L4 - not checked
Vendor drawings (SXN SMMS0650, Sunlord MWSA1004S) are only behind blocked JLC links. Board patterns (2.35x3.5 at +-3.0; 3.5x4.0 at +-4.75) are plausible for 6.6x7.1 and 10x11 shielded drum inductors. Human to compare against the LCSC drawings.

### Passives
All 0402/0603/0805 capacitors and resistors, FB1 and the fiducials are identical to the KiCad 10 library pads (IPC-7351 nominal). The 61 lib_footprint_mismatch hits on passives are graphics/3D-path differences only.

## Pin-1 orientation and CPL rotation (report only)

- CPL (`hardware/fabrication/assembly/CPL_JLC.csv`, 118 refs) was compared to the board snapshot: every X/Y matches the board position exactly (offset 0.0), every layer matches, and every rotation equals the KiCad footprint rotation (no difference on any ref). The CPL therefore carries KiCad rotations, not JLC-corrected rotations. JLC's component library orientation differs from KiCad for many package families (commonly SOT-23, SOT-23-6, SOIC/SOP, QFN/DFN, LQFP, diodes, electrolytic). This cannot be verified by software from the repo; JLC's online viewer must be used before ordering. Affected polarized/multi-pin refs and their current CPL rotations: D1 90, D2 -90, D5 -90, D6 180, D7 180, D8 -90, D9 -90, D10 180, D11 180, D12 180, D13 0, D14 0, D15 -90, J1 0, L5 180, P1 90, Q1 180, Q2 180, Q3 0, Q4 0, SW1 0, U1 180, U3 90, U5 0, U6 0, U7 90 (bottom), U8 0, U9 0, U10 90, U11 90, U12 -90, U13 -90, Y1 180.
- Pin-1 / cathode netlist sanity (pad 1 = cathode in KiCad diode footprints): D10 pad1 = +5V (K), D11 pad1 = K, D12 pad1 = K, D15 (zener BZT52C12) pad1 = 12V_Protected (K, anode to GND = correct clamp direction), D2 BAS40WS pad1 = 12V_Protected (cathode) - plausible for a reverse/clamp function but not verified against the schematic intent. D1 SMAJ16CA is bidirectional (no polarity). Fab-layer polarity marks exist in the footprints (silk bar / fab line on the cathode side for D_SOD-123, SOD-123F, SMA, SMC, SOD-323 KiCad footprints; project `DIOM4325X250N` has its own marks). Whether the physical reel orientation matches is a JLC-side check (not verified).
- EP/IC pin-1: U6 pin 1 at (-2.7,-1.905) with the TI chamfer side; U7 pin 1 at the chamfered corner of the LQFP silk; U8-U11 pin 1 marked by the KiCad DFN dot. Not verified against assembly.

## Open items for a human

1. Update `HybridPanda.pretty` copies of SOT23-3, LED-ARRAY, SOT-323, Crystal 3225, TYPE-C so DRC lib_footprint_mismatch is only cosmetic (or accept the warnings).
2. Rebuild `CONV_TPS5450DDAR` as a proper SMD footprint (pads on F.Mask, EP paste handled by pads, attr SMD).
3. Add courtyards to P1, U3, U5.
4. Fetch and compare the LCSC drawings for U3 (C668591), L3 (C149588), L4 (C151872) - not reachable from this network.
5. Run the JLC online CPL preview for rotation of all polarized/multi-pin parts; the CPL in the repo has raw KiCad rotations.

## Resumo (pt-BR)

Comparacao por software das 33 footprints da placa (125 posicoes) com os padroes de solda do fabricante ou da biblioteca KiCad/IPC. Resultado: 12 OK, 10 OK (igual a biblioteca KiCad, PDF do fabricante nao aberto), 8 com desvio menor (U6 TPS5450 construido com poligonos de mascara/pasta e attr THT; U8-U11 DFN generico vs NXP SOT782-1, span +0,2 mm; U7 LQFP144 span +0,2 mm; U12 pads EP so em cobre; D1 pad menor que o padrao SMA; Q1/Q2 e D13/D14 pads estilo KiCad; P1 slots +0,1 mm e sem courtyard), 3 nao verificadas (U3 USB-A, L3, L4: desenho do fabricante inacessivel). Nenhum MISMATCH encontrado. Os 73 avisos lib_footprint_mismatch do DRC sao em sua maioria so grafica/modelo 3D; em Q1, Q2, Q3, U5 e Y1 a placa esta corrigida e a biblioteca do projeto esta desatualizada. O CPL tem as rotacoes brutas do KiCad (iguais a placa); a correcao de rotacao para a convencao JLC nao foi verificada. Nada foi verificado fisicamente.
