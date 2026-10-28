# Hybrid Panda fabrication package

**STATUS: DO NOT FABRICATE.** This package was generated automatically for archive and
review. It has not been validated for production. No board has ever been built from it.

Hybrid Panda = black panda form factor + STM32H725ZGT6 running the red panda firmware.
Generated 2026-10-28 10:19:21 by [`hardware/scripts/step8_fabricate.py`](../scripts/step8_fabricate.py)
with KiCad 10.0.7 `kicad-cli` from [`hardware/hybrid-panda/HybridPanda.kicad_pcb`](../hybrid-panda/HybridPanda.kicad_pcb).

## Why it must not be fabricated yet

1. CAN-FD and USB impedance/skew: analytical estimate only (`step6_reports.py`); KiCad's DRC
   does not check impedance; the 4-layer 1.59 mm stackup is assumed, not confirmed with the
   fabricator.
2. `USB_D+/-` is not routed as a coupled pair: Freerouting routed it with vias (see
   [`step5-layout-h725.md`](../research/step5-layout-h725.md) sections 5 and 7); USB FS
   12 Mbit/s tolerates it, but it was not validated.
3. No board was fabricated, assembled or measured: zero physical validation; the official red
   panda firmware has never run on this hardware.
4. BOM: 1 reference without MPN and 2 without LCSC code (of 119); LCSC codes marked "to
   verify" in [`../reports/bom-real/BOM_HYBRIDPANDA_v1.csv`](../reports/bom-real/BOM_HYBRIDPANDA_v1.csv)
   are not confirmed in the JLC catalogue; JLC assembly requires confirming them.
5. DRC violations inherited from the OpenBlackPanda baseline not corrected (hole_clearance 8,
   lib_footprint_mismatch 73, silk_edge_clearance 4, silk_over_copper 1, silk_overlap 4,
   text_height 45); see `step5-layout-h725.md` section 7.3 and
   [`../reports/correcoes-aplicadas.md`](../reports/correcoes-aplicadas.md).
6. Gerber viewer check: NOT executed automatically (no gerbv/gerbview CLI); only the
   syntactic check in `gerber_check.json`. Open `gerbers/` in KiCad GerbView before any order.
7. ARM toolchain: installed locally (Arm GNU 14.2.Rel1) but at generation time no firmware had
   been compiled/signed for this hardware; depends on the commaai DFU/signing flow (see STEP 9).
   (The `hybrid-h725` firmware branch in [`firmware/`](../../firmware) was compiled later; it
   has still never run on hardware.)
8. Component rotation in the CPL is not normalised to the JLC convention (manual adjustment
   per footprint in the JLC panel).
9. Via-in-pad: 0 after the east relayout (`step5e_relayout_east.py`, D-33) plus `fix_audit.py`
   and `fix_vip_reroute.py` (U8.3 +5V: via moved to the F.Cu track west of C30 and B.Cu track
   rerouted). Counted with the `final_audit.py` definition (via centre inside an SMD pad
   bounding box) on the current board; reconfirm in
   [`../reports/final_audit.json`](../reports/final_audit.json) before any order.

## STEP 7 results (`../reports/step7_validation.json`)

- ERC errors = 0, warnings = 373
- DRC unconnected = 0, clearance = 0, shorts = 0, courtyards = 0
- Netlist divergences = 0; parity conflicts = 0
- DRC by type (hybrid/baseline): hole_clearance 8/8, lib_footprint_mismatch 73/67,
  silk_edge_clearance 4/4, silk_over_copper 1/0, silk_overlap 4/3, text_height 45/82

## Contents

| Path | Content |
|---|---|
| `gerbers/` | RS-274X (Protel extensions, no X2): F/In1/In2/B.Cu, F/B.Mask, F/B.SilkS, F/B.Paste, Edge.Cuts, job file |
| `drill/` | Excellon PTH + NPTH (mm, 3:3, suppress leading), map PDF and Gerber X2 |
| `assembly/` | `BOM_JLC.csv`, `CPL_JLC.csv` (origin = drill/aux origin 0.00,0.00 mm), `pos_kicad_both.csv` |
| `pdf/` | schematic, copper per layer, fab/assembly top and bottom |
| `3d/HybridPanda.step` | 3D model (missing models substituted) |
| `drill_table.md` / `.json` | 270 holes (PTH 26, NPTH 2, VIA 242); min drill 0.300 mm; min annular ring PTH 0.125, VIA 0.150 |
| `gerber_check.json` | syntactic check; Excellon holes vs PCB: 270 vs 270 |
| `HybridPanda_gerbers_JLC.zip` | gerbers + drill ready for upload, ONLY after the blockers above are removed |

Intended specification: 4 layers, 1.59 mm, FR-4 (er ~4.5 assumed), copper 1 oz outer / 0.5 oz
inner, min track/space 0.1375/0.1 mm, via 0.4/0.3 mm, min hole 0.30 mm, ENIG recommended
(QFN/LQFP 0.5 mm pitch), green mask, HASL not recommended.

Generation problems: none. Notes: STEP generated (28.2 MB) with a warning: VRML models ignored
(kicad-cli exit 2; 6 warnings in truncated stderr), so the 3D bodies of those footprints are
missing.

---

pt-BR: **NAO FABRICAR.** Pacote gerado automaticamente para arquivo e revisao, nao validado
para producao; nenhuma placa foi construida. Os nove motivos acima (impedancia so estimada,
USB nao acoplado, zero validacao fisica, BOM com codigos LCSC nao confirmados, DRC herdado,
gerbers sem revisao visual, rotacao CPL, etc.) precisam ser resolvidos antes de qualquer
pedido.
