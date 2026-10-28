"""Step 3 (schematic side): SI/PI HIGH items from hardware/reports/si-pi-audit/proposed-changes.md.

  item 4  R1 1k -> 10k, R_0402 -> R_0603 (Q4 gate)
  item 5  D15 zener 12 V BZT52C12 SOD-123, cathode 12V_Protected (Q4 source), anode Net-(D2-A) (Q4 gate)
  item 6  C4/C12 2.2uF 0805 -> 10uF 1206 X7R 50V (TPS5450 Cin)
  item 8  U13 USBLC6-2SC6 ESD array: I/O1 = USB_R_D-, I/O2 = USB_R_D+, VBUS = USB_PWR, GND
  item 18 R20/R21 22R stay in the schematic (PCB-only move)

Usage: python corr_step3_sch.py --inspect | --apply
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_build_schematic import Builder, SHEET_PATH  # noqa: E402
from kiutils.schematic import Schematic  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]  # repository root
SCH = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_sch"
REPORT = ROOT / "hardware/reports" / "corrections" / "step3_sch.json"


def ref_of(s):
    return next((p.value for p in s.properties if p.key == "Reference"), "")


def prop(s, key):
    return next((p for p in s.properties if p.key == key), None)


def main():
    apply = "--apply" in sys.argv
    sch = Schematic.from_file(str(SCH))
    b = Builder(sch)
    syms = {ref_of(s): s for s in sch.schematicSymbols}
    info = {}
    for r in ("R1", "Q4", "D2", "C4", "C12", "R20", "R21", "U3", "U1", "D10", "C17"):
        s = syms.get(r)
        if s is None:
            info[r] = None
            continue
        info[r] = {"pos": [s.position.X, s.position.Y, s.position.angle], "value": prop(s, "Value").value,
                   "fp": prop(s, "Footprint").value, "pins": b.pins_abs(s)}
    info["labels"] = [(g.text, g.position.X, g.position.Y, g.position.angle) for g in sch.globalLabels
                      if any(k in g.text for k in ("USB_R_D", "USB_PWR", "12V_Protected", "USB_D"))]
    info["local_labels"] = [(g.text, g.position.X, g.position.Y, g.position.angle) for g in sch.labels
                            if any(k in g.text for k in ("USB_R_D", "USB_PWR", "12V_Protected", "USB_D"))]
    def near(x, y, dx=12, dy=12):
        ws = [(w.points[0].X, w.points[0].Y, w.points[1].X, w.points[1].Y) for w in sch.graphicalItems
              if getattr(w, "type", "") == "wire" and any(abs(p.X - x) < dx and abs(p.Y - y) < dy for p in w.points)]
        js = [(j.position.X, j.position.Y) for j in sch.junctions if abs(j.position.X - x) < dx and abs(j.position.Y - y) < dy]
        return {"wires": ws, "junctions": js}
    for r in ("R1", "R20", "U3"):
        if info.get(r):
            info["near_" + r] = near(*info[r]["pos"][:2])
    print(json.dumps(info, indent=1, default=str))
    if not apply:
        return
    changes = []
    # ---- item 4: R1 10k R_0603
    r1 = syms["R1"]
    prop(r1, "Value").value = "10k"
    prop(r1, "Footprint").value = "Resistor_SMD:R_0603_1608Metric"
    changes.append("R1 1k R_0402 -> 10k R_0603")
    # ---- item 6: C4/C12 10uF C_1206
    for r in ("C4", "C12"):
        c = syms[r]
        prop(c, "Value").value = "10uF"
        prop(c, "Footprint").value = "Capacitor_SMD:C_1206_3216Metric"
        changes.append("%s 2.2uF C_0805 -> 10uF C_1206 (X7R 50V)" % r)
    # ---- item 5: D15 zener across Q4 gate-source (cathode = source = 12V_Protected, anode = gate = Net-(D2-A))
    # placed with global labels so it does not depend on the local wiring around Q4
    dx, dy = D15_POS
    d15 = b.symbol("Device", "D_Zener", "D", "BZT52C12", "Diode_SMD:D_SOD-123", dx, dy, 90, ref="D15")
    dp = b.pins_abs(d15)
    if dp["1"][1] > dp["2"][1]:          # want K (pin 1) on top
        d15.position.angle = 270
        dp = b.pins_abs(d15)
    k, a = dp["1"], dp["2"]
    # cathode -> 12V_Protected (Q4 source) through a global label; anode -> gate node (junction R1.2 / D2.2 / Q4.4)
    b.wire(k[0], k[1], k[0], k[1] - 2.54); b.label("12V_Protected", k[0], k[1] - 2.54, 90, shape="input")
    b.wire(a[0], a[1], a[0], GATE_Y); b.wire(a[0], GATE_Y, GATE_X, GATE_Y)
    b.text("Item 5 SI/PI: D15 zener 12 V limita Vgs de Q4 (K = 12V_Protected, A = gate)", dx - 25, dy + 14)
    changes.append("D15 BZT52C12 SOD-123 added at (%.2f,%.2f)" % (dx, dy))
    # ---- item 8: U13 USBLC6-2SC6 (SOT-23-6)
    ux, uy = U13_POS
    u13 = b.symbol("Power_Protection", "USBLC6-2P6", "U", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", ux, uy, 0, ref="U13")
    up = b.pins_abs(u13)
    # USBLC6-2SC6 pins: 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1
    for num, text, ang in (("1", "USB_R_D-", 180), ("3", "USB_R_D+", 180), ("4", "USB_R_D+", 0), ("6", "USB_R_D-", 0)):
        x, y = up[num]
        ex = x - 2.54 if ang == 180 else x + 2.54
        b.wire(x, y, ex, y); b.label(text, ex, y, ang, shape="bidirectional")
    x, y = up["5"]; b.wire(x, y, x, y - 2.54); b.label("USB_PWR", x, y - 2.54, 90, shape="input")
    x, y = up["2"]; b.wire(x, y, x, y + 2.54); b.pwr("GND", x, y + 2.54)
    b.text("Item 8 SI/PI: U13 ESD array USB (flow-through: lado conector pinos 1/3, lado MCU pinos 6/4)", ux - 30, uy + 14)
    changes.append("U13 USBLC6-2SC6 added at (%.2f,%.2f)" % (ux, uy))
    sch.to_file(str(SCH))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"changes": changes, "info": info}, indent=1, default=str), encoding="utf-8")
    print(json.dumps(changes, indent=1))


D15_POS = (47.0, 147.0)           # free column left of R1 (57.277,146.431)
GATE_X, GATE_Y = 57.277, 152.781  # existing junction on the Q4 gate node (R1.2 / D2.2 / Q4.4)
U13_POS = (305.0, 62.0)           # free area right of the USB block (R20/R21 at x=283)

if __name__ == "__main__":
    main()



