"""Step 2 (schematic side): PCR-2 VFBSMPS->VCAP link, C64/C65, PCR-1 PF9 strap jumper.

Usage: .venv python corr_step2_sch.py [--inspect] [--apply]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from step4_build_schematic import Builder, SHEET_PATH  # noqa: E402
from sch_geom import r2  # noqa: E402
from kiutils.schematic import Schematic  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]  # repository root
SCH = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_sch"
REPORT = ROOT / "hardware/reports" / "corrections" / "step2_sch.json"


def ref_of(s):
    return next(p.value for p in s.properties if p.key == "Reference")


def main():
    inspect = "--inspect" in sys.argv
    apply = "--apply" in sys.argv
    sch = Schematic.from_file(str(SCH))
    b = Builder(sch)
    u7 = next(s for s in sch.schematicSymbols if ref_of(s) == "U7")
    pins = b.pins_abs(u7)
    info = {"u7_pos": [u7.position.X, u7.position.Y], "pf9": pins["23"], "pf7": pins.get("21"), "pf8": pins.get("22"),
            "pf10": pins.get("24")}
    px, py = pins["23"]
    near_wires = [(w.points[0].X, w.points[0].Y, w.points[1].X, w.points[1].Y) for w in sch.graphicalItems
                  if getattr(w, "type", "") == "wire" and any(abs(p.X - px) < 8 and abs(p.Y - py) < 12 for p in w.points)]
    near_j = [(j.position.X, j.position.Y) for j in sch.junctions if abs(j.position.X - px) < 8 and abs(j.position.Y - py) < 12]
    near_pwr = [(ref_of(s), s.position.X, s.position.Y, s.position.angle) for s in sch.schematicSymbols
                if ref_of(s).startswith("#PWR") and abs(s.position.X - px) < 8 and abs(s.position.Y - py) < 12]
    info["near_wires"] = near_wires
    info["near_junctions"] = near_j
    info["near_pwr"] = near_pwr
    vfb = [(g.text, g.position.X, g.position.Y) for g in sch.globalLabels if g.text == "VFBSMPS"]
    info["vfbsmps_labels"] = vfb
    print(json.dumps(info, indent=1, default=str))
    if inspect or not apply:
        return

    changes = []
    # --- PCR-2: VFBSMPS global labels -> VCAP (merge nets)
    for g in sch.globalLabels:
        if g.text == "VFBSMPS":
            g.text = "VCAP"
            changes.append({"label_renamed": [g.position.X, g.position.Y]})
    # explanatory note near the SMPS block
    b.text("PCR-2: VFBSMPS ligado a VCAP (AN5419 direct SMPS)", 790.0, 306.0)

    # --- C64 2.2uF 0603 extra VCAP cap (pin 103 side) in the VCAP block, x=807.72
    c64 = b.cap("2.2uF", 807.72, 297.18, fp="Capacitor_SMD:C_0603_1608Metric", ref="C64")
    cp = b.pins_abs(c64)
    b.wire(800.10, 292.10, 807.72, 292.10); b.junction(800.10, 292.10)
    b.wire(807.72, 292.10, *cp["1"]); b.wire(*cp["2"], 807.72, 302.26); b.pwr("GND", 807.72, 302.26)
    changes.append({"added": "C64 2.2uF C_0603 VCAP"})

    # --- C65 4.7uF 0603 at VDDSMPS: hung on the +3V3 rail of the decoupling bank (x = 266.70+19*5.08)
    x65 = r2(266.70 + 19 * 5.08)
    c65 = b.cap("4.7uF", x65, 284.48, fp="Capacitor_SMD:C_0603_1608Metric", ref="C65")
    cp = b.pins_abs(c65)
    xprev = r2(266.70 + 18 * 5.08)
    b.wire(xprev, 279.40, x65, 279.40); b.wire(xprev, 289.56, x65, 289.56)
    b.junction(xprev, 279.40); b.junction(xprev, 289.56)
    b.wire(x65, 279.40, *cp["1"]); b.wire(*cp["2"], x65, 289.56)
    # the GND power symbol sat at xprev,289.56 (end of the rail); it stays, junction added above
    changes.append({"added": "C65 4.7uF C_0603 +3V3/VDDSMPS"})

    # --- PCR-1: PF9 strap through a solder jumper (closed = RED id1==0, open = HYBRID id1==4)
    # PF9 stub ends at (px+5.08, py) and joins the vertical GND strap at x=gx. Break the vertical
    # strap around PF9 and insert JP1 horizontally between the stub and GND.
    # Geometry (from --inspect): PF pins on the left side at x=652.78, stubs to x=647.70, vertical GND
    # strap at x=647.70 from 241.30 (GND symbol) to 251.46 (PF10), junctions at PF7/PF8/PF9 rows.
    gx = px - 5.08
    n_j = len(sch.junctions)
    sch.junctions = [j for j in sch.junctions if not (abs(j.position.X - gx) < 1e-3 and abs(j.position.Y - py) < 1e-3)]
    assert len(sch.junctions) == n_j - 1, "PF9 junction not found"
    n_w = len(sch.graphicalItems)
    def _is_stub(w):
        if getattr(w, "type", "") != "wire" or len(w.points) != 2:
            return False
        xs = sorted(p.X for p in w.points)
        return all(abs(p.Y - py) < 1e-3 for p in w.points) and abs(xs[0] - gx) < 1e-3 and abs(xs[1] - px) < 1e-3
    sch.graphicalItems = [w for w in sch.graphicalItems if not _is_stub(w)]
    assert len(sch.graphicalItems) == n_w - 1, "PF9 stub not found"
    # The strap keeps passing through (gx, py) without junction/endpoint -> no connection there.
    # PF9 wire now crosses the strap and lands on JP1 (left of the label column).
    jp = b.symbol("Jumper", "SolderJumper_2_Open", "JP", "HW_ID1", "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
                  632.46, py, 0, ref="JP1")
    jpp = b.pins_abs(jp)
    right = max(jpp.values(), key=lambda t: t[0]); left = min(jpp.values(), key=lambda t: t[0])
    assert right == (637.54, py) and left == (627.38, py), jpp
    b.wire(px, py, right[0], right[1])
    b.wire(left[0], left[1], left[0], left[1] - 2.54); b.pwr("GND", left[0], left[1] - 2.54, 180)
    b.text("PCR-1: JP1 fechado = RED (id1=0); aberto = HYBRID (id1=4)", 600.0, 236.0)
    changes.append({"added": "JP1 SolderJumper_2_Open PF9-GND"})

    sch.to_file(str(SCH))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"info": info, "changes": changes, "added": b.added}, indent=1, default=str))
    print("applied", len(changes), "changes")


if __name__ == "__main__":
    main()
