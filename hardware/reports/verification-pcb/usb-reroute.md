# A6 - USB D+/D- rerouted as a coupled pair

Date: 2026-10-28 16:41:10. Script: `hardware/scripts/vpcb_a6_usb_reroute.py`. Data: `usb-reroute.json`, DRC: `drc_after_a6.json`.

## Before (snapshot `snapshots/HybridPanda.kicad_pcb.pre_verification`)

| Net | Segments | Copper length | By layer | Vias | Widths |
|---|---|---|---|---|---|
| USB_D+ | 1 | 1.69 mm | B.Cu 1.69 | 0 () | [0.2] |
| USB_D- | 2 | 3.30 mm | B.Cu 3.30 | 0 () | [0.2] |
| USB_R_D+ | 13 | 26.02 mm | F.Cu 10.25, B.Cu 0.54, In1.Cu 15.23 | 2 (113.635,44.780; 127.900,45.650) | [0.2] |
| USB_R_D- | 14 | 24.18 mm | F.Cu 6.63, B.Cu 0.41, In1.Cu 17.13 | 2 (128.800,45.100; 113.635,42.750) | [0.2] |

- MCU U7 (LQFP-144) is on B.Cu, the series resistors R20/R21 (0402) on B.Cu, the ESD array U13 (SOT-23-6) and the USB-A U3 on F.Cu.
- USB_D+/USB_D- (MCU to resistor): two 0.20 mm B.Cu stubs, not coupled, 1.7 and 3.3 mm.
- USB_R_D+/USB_R_D- (resistor to U13 to U3): 0.20 mm, two vias per net, about 11 mm on In1.Cu (the +3V3/GND patchwork layer,
  referenced to In2 GND through 1.065 mm core, i.e. about 70-80 ohm single-ended, no defined pair), 0.5 mm centre spacing on In1 only;
  on B.Cu/F.Cu the two nets ran apart. Skew before: 0.23 mm (USB_R_D+ longer: it loops around U13 to reach U3 pin 3).

## After

| Net | Segments | Copper length | By layer | Vias | Widths |
|---|---|---|---|---|---|
| USB_D+ | 1 | 1.48 mm | B.Cu 1.48 | 0 () | [0.2] |
| USB_D- | 3 | 1.71 mm | B.Cu 1.71 | 0 () | [0.2] |
| USB_R_D+ | 14 | 24.93 mm | F.Cu 9.51, B.Cu 15.42 | 1 (127.900,43.600) | [0.2, 0.35] |
| USB_R_D- | 14 | 24.96 mm | F.Cu 6.08, B.Cu 18.87 | 1 (129.800,43.600) | [0.2, 0.35] |

- Total copper D+ (USB_D+ + USB_R_D+) = 26.40 mm, D- = 26.67 mm, **skew -0.27 mm** (target <= 0.5 mm). The 0402 resistor body is in
  both paths and is not counted.
- One via per net (symmetric pair at y = 43.60, x = 127.90 / 129.80, 0.6/0.3 mm) instead of two per net. The B.Cu run is referenced to
  the In2.Cu GND plane through the 0.20 mm prepreg; the F.Cu part is referenced to In1.Cu (GND there, outside the +3V3 pour).
- Coupled geometry: 0.35/0.15 mm (pitch 0.50 mm, ~90 ohm on JLC7628 per `impedance.md`) from x = 118.2 to the via pair (about 9 mm on
  B.Cu); 0.20/0.15 mm neck (pitch 0.35 mm, ~116 ohm) from the resistors through the 0.83 mm corridor between C62 and C54 (about 4 mm);
  0.20 mm single stubs at the LQFP pads (0.30 mm pad width, 1.5-1.7 mm). The last 45-degree split to the two vias opens the gap to
  0.32 mm over ~3 mm. On F.Cu the pair cannot stay coupled: U13 pin 5 (VBUS) sits between the two data pins, so the two F.Cu legs
  (via -> pin 4/6 -> pin 3/1 -> U3) are parallel at 1.9 mm pitch (uncoupled, ~53 ohm single-ended, 6-9 mm). This is inherent to the
  SOT-23-6 pinout and to U3 being on the other side of the board.
- USB netclass: {"track_width": 0.2, "diff_pair_width": 0.2, "diff_pair_gap": 0.25} -> track 0.35 / diff pair 0.35 / gap 0.15 mm.

## Components and other nets touched

- R20 (D- series resistor): 114.250,43.150 rot 180.0 -> 113.690,43.950 rot 90.0, pads {'USB_D-': '113.690,44.460', 'USB_R_D-': '113.690,43.440'}.
- R21 (D+ series resistor): 114.250,44.250 rot 0.0 -> 114.750,43.950 rot -90.0, pads {'USB_R_D+': '114.750,43.440', 'USB_D+': '114.750,44.460'}.
  Both are now vertical, side by side, so the pair leaves them without crossing. Courtyards do not overlap (0.02 mm apart).
- USB_PWR: the bottom-side detour (via 128.85,43.547, B.Cu 1.0 mm tracks, via 129.78,46.5) was removed; U13.5 -> U3.1 now runs on
  F.Cu only (1.0 mm), between the two new data vias. Before: {"F.Cu": 27.735, "B.Cu": 3.338}; after: {"F.Cu": 30.123}.
- SWDIO: escape moved 0.10 mm east (x 115.25 -> 115.35) to clear the rotated R21; same via 115.56,43.42.
- GND: stitching via 115.370,42.665 (and its F.Cu stub from C12.2) removed - it sat on the pair path; C12.2 stays on the 0.75 mm F.Cu GND
  bus to the vias at 113.949,40.931 and 115.666,40.266. The C54.2 via (117.618,42.204) and the C64.2 via (116.280,42.750) were replaced by
  one shared via at 116.28,43.00 (0.5-1.1 mm from the pads); it keeps both 100 nF returns short and frees the corridor.
- Removed items: 38 tracks, 9 vias (list in `usb-reroute.json`).

## DRC after this step (full board)

- Counts: {"hole_clearance": 8, "lib_footprint_mismatch": 73, "silk_edge_clearance": 4, "silk_over_copper": 1, "silk_overlap": 4, "text_height": 45}; unconnected items: 0.
- Items involving USB_D+/USB_D-/USB_R_D+/USB_R_D-: none (0 clearance, 0 unconnected).
- Zones were refilled with `pcbnew.ZONE_FILLER` before saving.

## Limits

- Lengths are centre-line copper lengths from the pcbnew API; via barrels (1.59 mm each, one per net) are equal on both sides.
- Impedance values are the analytic numbers of `impedance.md`; nothing was measured. The pair is electrically short for USB FS
  (edges 4-20 ns), so the necks and the uncoupled F.Cu legs are not expected to be functionally relevant; the work is layout hygiene.
- Changes are software-only, not physically verified. The schematic was not touched (connectivity unchanged).

---

pt-BR: O par USB foi refeito como par diferencial acoplado: trilhas antigas (2 vias por rede, 11 mm na camada interna In1) removidas;
R20/R21 rodados para vertical lado a lado; par 0.35/0.15 mm em B.Cu (gargalo 0.20/0.15 entre C62 e C54), um par simetrico de vias em
y=43.6 e pernas em F.Cu ate U13 e U3. Skew -0.27 mm. USB_PWR, SWDIO e duas vias GND foram reposicionadas para abrir o corredor.
DRC apos o passo: 0 itens nas redes USB. Alteracao apenas em software, sem verificacao fisica.
