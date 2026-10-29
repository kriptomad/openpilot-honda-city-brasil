# A3/A4 - Gerber review (render, outline, drill, connectivity)

Generated 2026-10-29 16:00:47 by `hardware/scripts/vpcb_a4_gerber_review.py` from `hardware\fabrication\HybridPanda_gerbers_JLC.zip` (zip content identical to `gerbers/` + `drill/`: True).
Tooling: gerbonara 1.6.3 (RS-274X parsing to primitives), shapely 2.2 (polygon union / point queries), pillow (raster). No gerbv/GerbView CLI involved.

Software review only. It confirms that the plotted files describe the same copper, outline and holes as the KiCad board; it does not replace a human look in GerbView nor an electrical test of a built board.

## (a) Renders

`hardware\reports\verification-pcb\gerber-render/` (20 px/mm, seen from the top; the bottom composite is mirrored as seen from below): `F_Cu.png`, `In1_Cu.png`, `In2_Cu.png`, `B_Cu.png`, `F_Mask.png`, `B_Mask.png`, `F_Paste.png`, `B_Paste.png`, `F_SilkS.png`, `B_SilkS.png`, `Edge_Cuts.png`, `Drill.png`, `composite_top.png`, `composite_bottom.png`.
Composites: copper (brown) under mask (dark green), mask openings (light), silk (white), drills (black), outline (yellow).

## (b) Outline and drill

| Check | Gerber | PCB (.kicad_pcb) | Match |
|---|---|---|---|
| Edge.Cuts size (outer, incl. line width 0.10 mm) | 51.025 x 46.750 mm | 51.025 x 46.750 mm | True |
| Edge.Cuts bbox (gerber frame, Y negated) | [91.91, -78.76, 142.935, -32.01] | [91.91, -78.76, 142.935, -32.01] | True |
| Outline closed (every endpoint shared by exactly 2 segments) | 266 segments | - | True |
| Drill hits PTH / NPTH / total | 266 / 2 / 268 | holes 268 (PTH 26, NPTH 2, VIA 240) | True |
| Every PCB hole has exactly one Excellon hit at the same position (0.01 mm) and diameter | 0 unmatched | - | True |
| Tool diameters | PTH [0.3, 0.4, 0.6, 0.7], NPTH [0.65] mm | - | - |

## (c) Connectivity: gerber copper vs KiCad netlist

Method: per-layer union of gerber copper (gerbonara primitives -> shapely), PTH drill hits join layers, KiCad pad centres mapped (x, -y) onto the copper polygons; nets compared by pad groups.

- Copper islands after union: F.Cu 156, In1.Cu 138, In2.Cu 128, B.Cu 209
- PTH drill hits used as inter-layer joints: 266 (hits touching fewer than 2 copper layers: 0)
- Netted pads located on gerber copper: 481; pads without copper under their centre: 0 
- Nets compared (nets with at least one pad): 142 of 142 board nets
- Vias not joining all 4 copper layers into one group: 0 
- **Shorts (one copper group, more than one net): 0**
- **Opens (one net, more than one copper group): 0**


Limits: pad centre sampling (a pad whose centre is covered but whose copper is partly missing would pass; DRC/zone fill already cover that case in KiCad); 
no check of mask/paste/silk registration beyond the renders; no copper-to-copper spacing check in the gerbers (KiCad DRC: clearance 0); 
nets without pads (none on this board) would not be compared.

Sensitivity check (run by hand, not persisted): removing the Excellon hits of the 93 signal vias from the input produced 38 open nets and 93 inconsistent vias, so the comparison does react to missing joints.

## Result

No discrepancy between the fabrication files and the KiCad board was found: outline, hole count/positions and copper connectivity (0 shorts, 0 opens) agree.

Runtime 2.0 s.

---

pt-BR: Revisao dos gerbers por software: todas as camadas foram renderizadas em PNG (pasta `gerber-render/`), o contorno Edge.Cuts e os furos Excellon
foram comparados com a placa KiCad, e a conectividade do cobre foi reconstruida a partir dos gerbers + furos e comparada com a netlist
(0 curtos, 0 abertos em 142 redes). Nao substitui a inspeccao visual humana no GerbView nem o teste eletrico de uma placa fabricada.
