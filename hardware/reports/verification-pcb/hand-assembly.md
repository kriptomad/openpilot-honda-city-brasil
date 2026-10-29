# A10 - Hand-assembly review (bare PCB from JLCPCB, all parts hand-soldered)

Date: 2026-10-29. Scope: the board will be ordered as a bare PCB; every component is bought and soldered by the user.
This report lists the parts that are hard to hand-solder, checks the PCB for hand-solder friendliness and records the
PCB edits made for it. Software review only; nothing was soldered.

Sources: `HybridPanda.kicad_pcb` (pcbnew 10.0.7), the plotted gerbers in `hardware/fabrication/gerbers/` (mask openings
measured with gerbonara + shapely, see `gerber-review.md`), `../verification/footprint-vs-datasheet.md`.

## 1. Parts that are hard to hand-solder

| Ref | Package | Side | Difficulty | What the PCB offers | Suggested method |
|---|---|---|---|---|---|
| U7 STM32H725ZGT6 | LQFP-144, 0.5 mm pitch, 144 pins | B | High (pitch) | copper gap between pads 0.20 mm; mask slivers between every pair of pad openings 0.200 mm (>= 0.1 mm rule); pin-1 corner marked on silk | tack two corners, drag-solder with flux, wick bridges; no exposed pad |
| P1 USB-C receptacle (TYPE-C-31-M-04) | 0.5 mm pitch SMD pins A1-A12/B1-B12 + 4 PTH shell slots + 2 NPTH pegs 0.65 mm | F (pins), slots through | High (pitch, shell) | mask slivers between pin openings 0.155 mm (>= 0.1 mm); slot pads 1.0x1.5 mm, slots 1.0 x 1.8 / 0.6 x 1.0 mm; pegs locate the part | pegs first, solder shell slots to fix the part, then drag-solder the pins |
| U8, U9, U10, U11 TJA1042 (CAN) | DFN-8 / SOT782-1, 0.65 mm pitch, exposed pad 1.55x2.4 mm (GND) | F | High (EP under body) | one 0.6/0.3 mm GND via inside each EP (placed 2026-10-29, `vpcb_a10_thermal_vias.py`), exposed on top inside the EP mask opening and tented on the bottom; pin-to-EP copper gap 0.133 mm, mask gap pin opening to EP opening 0.30 mm | hot air or: pre-tin EP lightly, place, heat from the bottom through the via with the iron (via is 0.3 mm, solder wicks up and anchors the EP); or solder paste + hot air |
| U6 TPS5450DDAR | PowerPAD SO-8 (DDA), exposed pad 2.95x4.9 mm (GND) | F | High (EP, thermal) | EP mask opening 2.6x3.1 mm; 9 PTH 0.6/0.3 mm GND via-pads on a 1.3 mm grid: the centre one and the 4 at +-0.65 mm are inside the opening (exposed on top, tented on bottom), the 4 at +-1.95 mm are under mask; 8 pins 1.55x0.6 at 1.27 mm pitch | hot air with paste, or iron through the exposed centre via-pads from the top; the pad must be soldered (3 A buck, PowerPAD is the thermal path) |
| Q4 | PowerPAK SO-8 (exposed pad, +12V) | F | Medium | EP without vias (not GND, no thermal via needed for the input FET duty); large pad | hot air or large iron tip on the pad edge |
| U12 XL1509-3.3E1 | SOP-8 (footprint `Diodes_PSOP-8`) | F | Low | the 4 "pad 9" EP copper rectangles are F.Cu only, without mask opening: nothing to solder there. The XL1509 package has no exposed pad (pins 5-8 are GND); the copper is a covered heat spreader | normal SOP-8 soldering |
| U1 AP22615AWU-7 | TSOT-25 / SOT-23-5 | F | Low | - | normal; part is no longer in the JLC catalogue, buy from Mouser/Digi-Key |
| 0402 passives (Cxx, Rxx) | 0402 | F/B | Medium (size) | 0402 pads from the KiCad library | tweezers, pre-tin one pad |
| Y1 crystal | 3225 4-pad | B | Medium (pads under body) | 4 pads | hot air, or iron on the pad ends |
| L3, L4, L5 inductors | 2016 / 2520 / power inductor | F | Medium (pads under body) | - | hot air or iron on the exposed pad ends |

No QFN other than the DFN-8 transceivers is on the board. No BGA.

## 2. PCB checks for hand-solder friendliness

| Check | Result | Status |
|---|---|---|
| Solder mask minimum web (`solder_mask_min_width`) | was 0 in `.kicad_pcb` / `.kicad_pro`; set to 0.1 mm on 2026-10-29 (JLCPCB minimum 0.1 mm). DRC `solder_mask_bridge` = error, 0 violations after the change (two silk-over-mask items it created were fixed: C32 reference moved, U6 pin-1 circle moved) | fixed |
| Mask expansion (`pad_to_mask_clearance`) | 0 (pad-sized openings, JLC adds its own expansion) | kept |
| Mask slivers between U7 pads (0.5 mm pitch) | 0.200 mm in the B.Mask gerber, 144 openings for 144 pads | OK |
| Mask slivers between P1 pins (0.5 mm pitch) | 0.155 mm in F.Mask | OK (>= 0.1) |
| Mask slivers around U8-U11 (DFN pins vs EP) | 0.30 mm between pin openings and EP opening; 9 openings per part | OK |
| Thermal vias under exposed pads | U6: 9 via-pads 0.3 mm drill (5 exposed inside the EP opening); U8/U9/U10/U11: 1 via 0.6/0.3 mm each, added on 2026-10-29 (positions 127.543,60.910 / 126.695,55.245 / 140.245,70.375 / 135.580,70.347; In2.Cu BUS1N_STB track jogged 0.3 mm north to free the U8 position). More than one via per DFN EP does not fit: R30/R31 (0402 pull-ups on B.Cu), In2 CAN tracks and the B.Cu USB pair occupy the rest of the 1.55x2.4 mm area | fixed (minimum) |
| Via tenting under EPs | board setup tents vias both sides; the via inside a mask opening is necessarily exposed on top; the bottom is covered (checked in B.Mask gerber for the 4 DFN vias and the U6 centre via-pad) | OK, limits wicking to the bottom |
| Via size inside EPs | 0.3 mm drill (JLC minimum for 4-layer), so the amount of solder that can wick into the barrel is small | OK |
| Paste layer | irrelevant for hand assembly (no stencil); F/B.Paste gerbers are still in the package for a future stencil | n/a |
| Finish | ENIG recommended (flat pads for the 0.5 mm pitch U7 and P1 and for the DFN EPs; HASL not recommended). Not a design-file setting: select at order time | recommendation |
| Fiducials | FID1, FID2, FID3 (F.Cu) and FID4, FID5, FID6 (B.Cu), 1 mm copper dot with 2 mm mask opening, no drill, no net: harmless for a bare-board order (bare copper dots), they do not participate in DRC/connectivity | OK |
| Tooling / NPTH | 2 NPTH 0.65 mm pegs under P1 (part locating pegs), no other NPTH or mounting holes; panelisation and tooling holes are added by JLC on their rail | OK |
| Copper under U12 "EP" | F.Cu only, no mask opening: nothing to solder, no bridging risk | OK |

## 3. PCB edits made in this review

- `solder_mask_min_width` 0 -> 0.1 mm (`HybridPanda.kicad_pcb` setup, `HybridPanda.kicad_pro` design settings).
- C32 reference text moved to (138.3, 74.052) rot 90 (was over the FID2 mask ring); U6 pin-1 silk circle moved to (104.7, 39.45), r 0.1, w 0.15 (was between C37 pads).
- Four GND vias 0.6/0.3 mm added inside the U8-U11 exposed pads; In2.Cu BUS1N_STB segment 128.904,60.609 -> 123.959,60.609 replaced by a jog through y = 60.305 (x 126.45..128.6).
- After the edits: DRC 73 `lib_footprint_mismatch` (intentional), 0 unconnected, 0 clearance, 0 mask bridges; `final_audit.py` 0 shorts, 0 via-in-pad, 9 thermal vias recognised; vias 240, holes 268.

## 4. Open items for assembly (not PCB)

- None of the above has been soldered; the hand-solder methods are suggestions.
- U1 AP22615AWU-7 must be bought outside JLC/LCSC.
- A stencil (paste layer) is not needed but the gerbers include F/B.Paste if one is ordered later.

---

pt-BR: Revisao para montagem manual (PCB nua da JLCPCB, componentes soldados a mao pelo utilizador). Pecas dificeis:
U7 LQFP-144 passo 0,5 mm (frestas de mascara 0,20 mm), P1 USB-C passo 0,5 mm (0,155 mm), U8-U11 DFN-8 com pad exposto
(agora com uma via GND 0,6/0,3 mm em cada pad, exposta em cima e tapada em baixo), U6 TPS5450 PowerPAD (abertura 2,6x3,1 mm
com 5 vias expostas), Q4 PowerPAK. Largura minima de mascara passou de 0 para 0,1 mm; recomenda-se acabamento ENIG.
Fiduciais e os 2 NPTH do P1 sao inofensivos para encomenda de placa nua. Nada foi soldado; metodos sao sugestoes.
