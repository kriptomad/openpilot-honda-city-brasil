# -*- coding: utf-8 -*-
"""
si_pi_dump.py - read-only extraction from HybridPanda.kicad_pcb for the SI/PI audit.
Run with KiCad 10 python:
  "C:\\Users\\costabr\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe" -u si_pi_dump.py
Writes: si_pi_dump.json and power_nets.json in the same folder. Never writes the board.
"""
import json
import math
import os
import sys
import re
from collections import defaultdict

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PCB = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")

NM = 1e6  # nm per mm


def mm(v):
    return round(v / NM, 4)


def pt(p):
    return [mm(p.x), mm(p.y)]


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y) / NM


board = pcbnew.LoadBoard(PCB)
lname = board.GetLayerName

out = {}

# ---------------------------------------------------------------- board
bb = board.GetBoardEdgesBoundingBox()
out["board"] = {
    "file": PCB,
    "copper_layers": board.GetCopperLayerCount(),
    "bbox_mm": [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
    "size_mm": [mm(bb.GetWidth()), mm(bb.GetHeight())],
    "area_mm2": round(mm(bb.GetWidth()) * mm(bb.GetHeight()), 1),
}
ds = board.GetDesignSettings()
out["design_rules"] = {
    "min_clearance": mm(ds.m_MinClearance),
    "min_track_width": mm(ds.m_TrackMinWidth),
    "min_via_diameter": mm(ds.m_ViasMinSize),
    "min_through_drill": mm(ds.m_MinThroughDrill),
    "min_via_annular": mm(ds.m_ViasMinAnnularWidth),
    "hole_clearance": mm(ds.m_HoleClearance),
    "hole_to_hole": mm(ds.m_HoleToHoleMin),
    "copper_edge_clearance": mm(ds.m_CopperEdgeClearance),
}

# stackup from text
txt = open(PCB, "r", encoding="utf-8", errors="replace").read()
m = re.search(r"\(stackup(.*?)\n\s*\(copper_finish", txt, re.S)
stack = []
if m:
    for lm in re.finditer(r'\(layer "([^"]+)"(.*?)(?=\n\s*\(layer "|\Z)', m.group(1), re.S):
        body = lm.group(2)
        th = re.search(r"\(thickness ([0-9.]+)", body)
        er = re.search(r"\(epsilon_r ([0-9.]+)", body)
        stack.append({"layer": lm.group(1), "thickness_mm": float(th.group(1)) if th else None,
                      "er": float(er.group(1)) if er else None})
out["stackup"] = stack
cu_thick = {}
for s in stack:
    if s["layer"].endswith(".Cu") and s["thickness_mm"]:
        cu_thick[s["layer"]] = s["thickness_mm"]
out["copper_thickness_mm"] = cu_thick

# ---------------------------------------------------------------- footprints / pads
fps = {}
pads_by_net = defaultdict(list)
for fp in board.GetFootprints():
    ref = fp.GetReference()
    pads = []
    for p in fp.Pads():
        sz = p.GetSize()
        dr = p.GetDrillSize()
        pads.append({
            "num": p.GetNumber(), "net": p.GetNetname(), "pos": pt(p.GetPosition()),
            "size": [mm(sz.x), mm(sz.y)], "drill": [mm(dr.x), mm(dr.y)],
            "layers": [lname(l) for l in p.GetLayerSet().CuStack()],
            "attr": int(p.GetAttribute()),
        })
        pads_by_net[p.GetNetname()].append((ref, p))
    cy = fp.GetCourtyard(fp.GetLayer() if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_Cu)
    cyb = fp.GetBoundingBox(False, False)
    fps[ref] = {
        "value": fp.GetValue(), "layer": lname(fp.GetLayer()), "pos": pt(fp.GetPosition()),
        "rot": fp.GetOrientationDegrees(), "fpid": fp.GetFPIDAsString(),
        "bbox": [mm(cyb.GetLeft()), mm(cyb.GetTop()), mm(cyb.GetRight()), mm(cyb.GetBottom())],
        "pads": pads,
    }
out["footprints"] = fps

# ---------------------------------------------------------------- tracks / vias
tracks = []
vias = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        vias.append({
            "net": t.GetNetname(), "pos": pt(t.GetPosition()), "dia": mm(t.GetWidth()),
            "drill": mm(t.GetDrillValue()), "top": lname(t.TopLayer()), "bot": lname(t.BottomLayer()),
        })
    else:
        tracks.append({
            "net": t.GetNetname(), "layer": lname(t.GetLayer()), "w": mm(t.GetWidth()),
            "a": pt(t.GetStart()), "b": pt(t.GetEnd()), "len": mm(t.GetLength()),
            "locked": bool(t.IsLocked()),
        })
out["totals"] = {"tracks": len(tracks), "vias": len(vias)}
out["vias"] = vias

# ---------------------------------------------------------------- zones
zones = []
for z in board.Zones():
    layers = [lname(l) for l in z.GetLayerSet().CuStack()]
    areas = {}
    islands = {}
    for l in z.GetLayerSet().CuStack():
        try:
            poly = z.GetFilledPolysList(l)
            areas[lname(l)] = round(poly.Area() / NM / NM, 1)
            islands[lname(l)] = poly.OutlineCount()
        except Exception as e:  # noqa
            areas[lname(l)] = None
    zones.append({
        "net": z.GetNetname(), "layers": layers, "filled_area_mm2": areas, "outlines": islands,
        "pad_connection": int(z.GetPadConnection()), "thermal_gap": mm(z.GetThermalReliefGap()),
        "thermal_spoke": mm(z.GetThermalReliefSpokeWidth()), "min_thickness": mm(z.GetMinThickness()),
        "clearance": mm(z.GetLocalClearance()), "priority": z.GetAssignedPriority(),
        "bbox": [mm(z.GetBoundingBox().GetLeft()), mm(z.GetBoundingBox().GetTop()),
                 mm(z.GetBoundingBox().GetRight()), mm(z.GetBoundingBox().GetBottom())],
        "is_rule_area": z.GetIsRuleArea(),
    })
out["zones"] = zones

# ---------------------------------------------------------------- power nets
POWER_NETS = ["+12V", "12V_Protected", "+5V", "+3V3", "USB_PWR", "L4", "Net-(D11-K)",
              "VCAP", "VFBSMPS", "VLXSMPS", "VDDA", "GND", "SBU1", "SBU2"]


def ipc2221_width_mm(i_amp, cu_mm, dT=10.0, external=True):
    """IPC-2221 minimum trace width for current i_amp at temperature rise dT."""
    k = 0.048 if external else 0.024
    if i_amp <= 0:
        return 0.0
    area_mil2 = (i_amp / (k * dT ** 0.44)) ** (1 / 0.725)
    th_mil = cu_mm / 0.0254
    return round(area_mil2 / th_mil * 0.0254, 3)


def ipc2221_current_a(w_mm, cu_mm, dT=10.0, external=True):
    k = 0.048 if external else 0.024
    area_mil2 = (w_mm / 0.0254) * (cu_mm / 0.0254)
    return round(k * dT ** 0.44 * area_mil2 ** 0.725, 2)


power = {}
for net in POWER_NETS:
    segs = [t for t in tracks if t["net"] == net]
    vs = [v for v in vias if v["net"] == net]
    by_layer = defaultdict(lambda: {"count": 0, "len_mm": 0.0, "min_w": 99, "max_w": 0, "widths": defaultdict(float)})
    for s in segs:
        d = by_layer[s["layer"]]
        d["count"] += 1
        d["len_mm"] += s["len"]
        d["min_w"] = min(d["min_w"], s["w"])
        d["max_w"] = max(d["max_w"], s["w"])
        d["widths"][str(s["w"])] += s["len"]
    minw = min([s["w"] for s in segs], default=None)
    narrow = sorted([s for s in segs if minw is not None and s["w"] <= minw + 0.0001], key=lambda s: -s["len"])
    zs = [z for z in zones if z["net"] == net]
    power[net] = {
        "track_count": len(segs),
        "via_count": len(vs),
        "via_sizes": sorted({(v["dia"], v["drill"]) for v in vs}),
        "min_width_mm": minw,
        "min_width_segments": [{"layer": s["layer"], "a": s["a"], "b": s["b"], "len": s["len"]} for s in narrow[:12]],
        "by_layer": {k: {"count": v["count"], "len_mm": round(v["len_mm"], 1), "min_w": v["min_w"], "max_w": v["max_w"],
                         "len_by_width": {kk: round(vv, 1) for kk, vv in v["widths"].items()}} for k, v in by_layer.items()},
        "zones": [{"layers": z["layers"], "area": z["filled_area_mm2"]} for z in zs],
        "pads": sorted({r for r, p in pads_by_net[net]}),
    }
out["power_nets_raw"] = power

# ---------------------------------------------------------------- via "choke points": vias per net that are the only
# transition between two layers in a region (simplified: list all vias on power nets with their layers)

# ---------------------------------------------------------------- decoupling distances to U7
u7 = board.FindFootprintByReference("U7")
u7pads = {p.GetNumber(): p for p in u7.Pads()}
u7_by_net = defaultdict(list)
for n, p in u7pads.items():
    u7_by_net[p.GetNetname()].append(p)

dec = []
for ref, f in fps.items():
    if not re.match(r"^(C|L|FB)\d+$", ref):
        continue
    fp = board.FindFootprintByReference(ref)
    entry = {"ref": ref, "value": f["value"], "layer": f["layer"], "pos": f["pos"], "pins": []}
    relevant = False
    for p in fp.Pads():
        n = p.GetNetname()
        if n in ("+3V3", "VCAP", "VDDA", "VFBSMPS", "VLXSMPS", "GND", "HSE_IN", "HSE_OUT", "NRST"):
            cands = u7_by_net.get(n, [])
            if cands:
                best = min(cands, key=lambda q: dist(q.GetPosition(), p.GetPosition()))
                d = dist(best.GetPosition(), p.GetPosition())
                entry["pins"].append({"pad": p.GetNumber(), "net": n, "nearest_u7_pin": best.GetNumber(), "dist_mm": round(d, 2)})
                if n != "GND":
                    relevant = True
    if relevant and min(x["dist_mm"] for x in entry["pins"] if x["net"] != "GND") < 12:
        dec.append(entry)
out["u7_decoupling"] = sorted(dec, key=lambda e: e["ref"])

# U7 power pin table with nearest cap of same net
u7pow = []
for n, p in sorted(u7pads.items(), key=lambda kv: int(kv[0])):
    net = p.GetNetname()
    if net in ("+3V3", "VCAP", "VDDA", "VFBSMPS", "VLXSMPS"):
        best = None
        for ref, q in pads_by_net[net]:
            if ref.startswith("C") or ref.startswith("L"):
                d = dist(q.GetPosition(), p.GetPosition())
                if best is None or d < best[1]:
                    best = (ref + "." + q.GetNumber(), round(d, 2))
        u7pow.append({"pin": n, "net": net, "pos": pt(p.GetPosition()), "nearest_cap": best})
out["u7_power_pins"] = u7pow

# ---------------------------------------------------------------- net lengths / diff pairs
netlen = defaultdict(lambda: defaultdict(float))
netvias = defaultdict(int)
for t in tracks:
    netlen[t["net"]][t["layer"]] += t["len"]
for v in vias:
    netvias[v["net"]] += 1

PAIRS = [("USB_D+", "USB_D-"), ("USB_R_D+", "USB_R_D-"), ("BUS0_H", "BUS0_L"), ("BUS1N_H", "BUS1N_L"),
         ("BUS1O_H", "BUS1O_L"), ("BUS2_H", "BUS2_L"), ("HSE_IN", "HSE_OUT")]
pairs = []
for a, b in PAIRS:
    la = sum(netlen[a].values()); lb = sum(netlen[b].values())
    pairs.append({"p": a, "n": b, "len_p": round(la, 2), "len_n": round(lb, 2), "skew": round(abs(la - lb), 2),
                  "layers_p": {k: round(v, 2) for k, v in netlen[a].items()},
                  "layers_n": {k: round(v, 2) for k, v in netlen[b].items()},
                  "vias_p": netvias[a], "vias_n": netvias[b],
                  "widths_p": sorted({t["w"] for t in tracks if t["net"] == a}),
                  "widths_n": sorted({t["w"] for t in tracks if t["net"] == b})})
out["pairs"] = pairs

SIG = ["BUS0_TX", "BUS0_RX", "BUS1N_TX", "BUS1N_RX", "BUS1O_TX", "BUS1O_RX", "BUS2_TX", "BUS2_RX",
       "BUS0_STB", "BUS1N_STB", "BUS1O_STB", "BUS2_STB", "SWDIO", "SWCLK", "NRST", "BOOT0",
       "SBU1_ADC", "SBU2_ADC", "VoltageSens", "5VOUT_S", "LED_RED", "LED_GREEN", "LED_BLUE", "USB_LOAD",
       "relay_SBU1", "relay_SBU2", "VSENSE", "Net-(U6-BOOT)", "Net-(D2-A)", "Net-(U1-ISET)", "Net-(Q3-C)"]
out["signal_lengths"] = {n: {"len": round(sum(netlen[n].values()), 2), "layers": {k: round(v, 2) for k, v in netlen[n].items()},
                             "vias": netvias[n], "min_w": min([t["w"] for t in tracks if t["net"] == n], default=None)} for n in SIG}

# pair gap sampling: for each pair, sample points along P tracks and find nearest N track distance
def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


gaps = {}
for a, b in PAIRS:
    ta = [t for t in tracks if t["net"] == a]
    tb = [t for t in tracks if t["net"] == b]
    ds_ = []
    for t in ta:
        for k in range(5):
            f = k / 4
            p = (t["a"][0] + f * (t["b"][0] - t["a"][0]), t["a"][1] + f * (t["b"][1] - t["a"][1]))
            cands = [seg_dist(p, u["a"], u["b"]) for u in tb if u["layer"] == t["layer"]]
            if cands:
                ds_.append(min(cands))
    if ds_:
        ds_.sort()
        gaps[a + "/" + b] = {"cc_gap_min": round(ds_[0], 3), "cc_gap_median": round(ds_[len(ds_) // 2], 3),
                             "cc_gap_max": round(ds_[-1], 3), "samples": len(ds_)}
out["pair_gaps_centre_to_centre"] = gaps

# ---------------------------------------------------------------- series resistor / component placement checks
def pad_pos(ref, num):
    fp = board.FindFootprintByReference(ref)
    if not fp:
        return None
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return p.GetPosition()
    return None


def d(ref1, n1, ref2, n2):
    a = pad_pos(ref1, n1); b = pad_pos(ref2, n2)
    return round(dist(a, b), 2) if a and b else None


place = {
    "R20_to_U7.100 (USB_D-)": d("R20", 1, "U7", 100),
    "R21_to_U7.101 (USB_D+)": d("R21", 2, "U7", 101),
    "R20_to_U3.2": d("R20", 2, "U3", 2),
    "R21_to_U3.3": d("R21", 1, "U3", 3),
    "U3.2_to_U7.100 straight": d("U3", 2, "U7", 100),
    "C37(BOOT)_to_U6.1": d("C37", 1, "U6", 1),
    "C4_to_U6.7(VIN)": d("C4", 1, "U6", 7), "C6_to_U6.7": d("C6", 1, "U6", 7),
    "C7_to_U6.7": d("C7", 1, "U6", 7), "C12_to_U6.7": d("C12", 1, "U6", 7),
    "D12.1_to_U6.8(PH)": d("D12", 1, "U6", 8), "L4.1_to_U6.8": d("L4", 1, "U6", 8),
    "D12.2(GND)_to_C4.2": d("D12", 2, "C4", 2), "D12.2_to_U6.9(EP)": d("D12", 2, "U6", 9),
    "R5_to_U6.4(VSENSE)": d("R5", 1, "U6", 4), "R6_to_U6.4": d("R6", 2, "U6", 4),
    "C8_to_U12.1(VIN XL1509)": d("C8", 2, "U12", 1), "C10_to_U12.1": d("C10", 2, "U12", 1),
    "C3_to_U12.1": d("C3", 1, "U12", 1),
    "D11.1_to_U12.2(SW)": d("D11", 1, "U12", 2), "L3.1_to_U12.2": d("L3", 1, "U12", 2),
    "C16_to_L3.2(3V3 out)": d("C16", 1, "L3", 2), "C16_to_U12.3(FB)": d("C16", 1, "U12", 3),
    "C39_to_U7.68": d("C39", 1, "U7", 68), "C40_to_U7.140": d("C40", 1, "U7", 140),
    "VCAP pin103 nearest cap C39": d("C39", 1, "U7", 103), "VCAP pin103 nearest cap C40": d("C40", 1, "U7", 103),
    "L5.1_to_U7.15(VLX)": d("L5", 1, "U7", 15), "L5.2_to_U7.17(VFB)": d("L5", 2, "U7", 17),
    "C41_to_U7.15": d("C41", 1, "U7", 15), "C42_to_U7.17": d("C42", 1, "U7", 17),
    "C42.1(VFBSMPS)_to_C39.1(VCAP)": d("C42", 1, "C39", 1), "U7.17(VFB)_to_U7.68(VCAP)": d("U7", 17, "U7", 68),
    "C43_to_U7.36(VDDA)": d("C43", 1, "U7", 36), "C44_to_U7.35(VREF+)": d("C44", 1, "U7", 35), "FB1_to_U7.36": d("FB1", 1, "U7", 36),
    "C38_to_U7.27(NRST)": d("C38", 1, "U7", 27),
    "R14_to_U7.135(BOOT0)": d("R14", 1, "U7", 135),
    "Y1.1_to_U7.25": d("Y1", 1, "U7", 25), "Y1.3_to_U7.26": d("Y1", 3, "U7", 26),
    "C23_to_Y1.1": d("C23", 1, "Y1", 1), "C24_to_Y1.3": d("C24", 1, "Y1", 3),
    "C30_to_U8.3": d("C30", 2, "U8", 3), "C31_to_U9.3": d("C31", 2, "U9", 3), "C32_to_U10.3": d("C32", 2, "U10", 3), "C33_to_U11.3": d("C33", 2, "U11", 3),
    "D6_to_P1.A2 (BUS1O ESD)": d("D6", 2, "P1", "A2"), "D6_to_U8.7": d("D6", 2, "U8", 7),
    "D7_to_P1.A11 (BUS2)": d("D7", 2, "P1", "A11"), "D7_to_U9.7": d("D7", 2, "U9", 7),
    "D8_to_P1.B2 (BUS1N)": d("D8", 2, "P1", "B2"), "D8_to_U10.7": d("D8", 2, "U10", 7),
    "D9_to_P1.B11 (BUS0)": d("D9", 2, "P1", "B11"), "D9_to_U11.7": d("D9", 2, "U11", 7),
    "D5_to_P1.A8 (SBU ESD)": d("D5", 1, "P1", "A8"),
    "D1_to_P1.A4 (TVS 12V)": d("D1", 2, "P1", "A4"), "D1_to_Q4.5": d("D1", 2, "Q4", 5),
    "U8.7_to_P1.A2": d("U8", 7, "P1", "A2"), "U9.7_to_P1.A11": d("U9", 7, "P1", "A11"),
    "U10.7_to_P1.B2": d("U10", 7, "P1", "B2"), "U11.7_to_P1.B11": d("U11", 7, "P1", "B11"),
    "C17_to_U3.1(USB VBUS)": d("C17", 2, "U3", 1), "C34_to_U1.1": d("C34", 2, "U1", 1),
    "U1.6(IN +5V) nearest cap": None,
}
out["placement_distances"] = place

# ---------------------------------------------------------------- crystal keep-out check
y1 = board.FindFootprintByReference("Y1")
yb = y1.GetBoundingBox(False, False)
yb_mm = [mm(yb.GetLeft()), mm(yb.GetTop()), mm(yb.GetRight()), mm(yb.GetBottom())]
under = []
for t in tracks:
    if t["net"] in ("HSE_IN", "HSE_OUT", "GND"):
        continue
    for p in (t["a"], t["b"], [(t["a"][0] + t["b"][0]) / 2, (t["a"][1] + t["b"][1]) / 2]):
        if yb_mm[0] - 0.5 <= p[0] <= yb_mm[2] + 0.5 and yb_mm[1] - 0.5 <= p[1] <= yb_mm[3] + 0.5:
            under.append(t)
            break
out["crystal"] = {"Y1_layer": fps["Y1"]["layer"], "Y1_bbox": yb_mm,
                  "foreign_tracks_in_bbox": [{"net": t["net"], "layer": t["layer"], "a": t["a"], "b": t["b"]} for t in under],
                  "zones_under": [z["net"] + ":" + ",".join(z["layers"]) for z in zones
                                  if z["bbox"][0] <= yb_mm[0] and z["bbox"][2] >= yb_mm[2] and z["bbox"][1] <= yb_mm[1] and z["bbox"][3] >= yb_mm[3]]}

# ---------------------------------------------------------------- SW nodes copper area
def net_copper_area(net):
    a = 0.0
    for t in tracks:
        if t["net"] == net:
            a += t["len"] * t["w"]
    for ref, p in pads_by_net[net]:
        s = p.GetSize()
        a += mm(s.x) * mm(s.y)
    for z in zones:
        if z["net"] == net:
            a += sum(v for v in z["filled_area_mm2"].values() if v)
    return round(a, 1)


out["switch_nodes"] = {n: {"copper_area_mm2": net_copper_area(n), "layers": {k: round(v, 2) for k, v in netlen[n].items()},
                           "vias": netvias[n], "pads": sorted({r + "." + p.GetNumber() for r, p in pads_by_net[n]})}
                       for n in ["L4", "Net-(D11-K)", "VLXSMPS", "Net-(U6-BOOT)"]}

# ---------------------------------------------------------------- GND stitching vias
gv = [v for v in vias if v["net"] == "GND"]
nn = []
for i, v in enumerate(gv):
    best = min((math.hypot(v["pos"][0] - u["pos"][0], v["pos"][1] - u["pos"][1]) for j, u in enumerate(gv) if j != i), default=None)
    nn.append(best)
nn_sorted = sorted(x for x in nn if x is not None)
out["gnd_vias"] = {"count": len(gv), "nn_min": round(nn_sorted[0], 2) if nn_sorted else None,
                   "nn_median": round(nn_sorted[len(nn_sorted) // 2], 2) if nn_sorted else None,
                   "nn_max": round(nn_sorted[-1], 2) if nn_sorted else None,
                   "drills": sorted({v["drill"] for v in gv})}

# GND vias near USB / CAN pair layer transitions
usb_vias = [v for v in vias if v["net"] in ("USB_D+", "USB_D-")]
near = []
for v in usb_vias:
    dmin = min((math.hypot(v["pos"][0] - u["pos"][0], v["pos"][1] - u["pos"][1]) for u in gv), default=None)
    near.append({"via": v, "nearest_gnd_via_mm": round(dmin, 2) if dmin else None})
out["usb_vias"] = near

# ---------------------------------------------------------------- via / annular stats
va = defaultdict(int)
for v in vias:
    va[(v["dia"], v["drill"], round((v["dia"] - v["drill"]) / 2, 3))] += 1
out["via_stats"] = [{"dia": k[0], "drill": k[1], "annular": k[2], "count": c} for k, c in sorted(va.items())]
tw = defaultdict(float)
for t in tracks:
    tw[t["w"]] += t["len"]
out["track_width_hist_mm"] = {str(k): round(v, 1) for k, v in sorted(tw.items())}

# ---------------------------------------------------------------- IPC power table
EST_CURRENT = {
    "+12V": 3.0, "12V_Protected": 3.0, "+5V": 3.0, "USB_PWR": 2.0, "+3V3": 0.6,
    "L4": 3.0, "Net-(D11-K)": 0.6, "VCAP": 0.6, "VFBSMPS": 0.6, "VLXSMPS": 0.6, "VDDA": 0.01,
    "GND": 3.0, "SBU1": 0.1, "SBU2": 0.1,
}
pn = {}
for net, p in power.items():
    i = EST_CURRENT.get(net, 0.5)
    per_layer = {}
    worst = None
    for layer, dd in p["by_layer"].items():
        cu = cu_thick.get(layer, 0.035)
        ext = layer in ("F.Cu", "B.Cu")
        need = ipc2221_width_mm(i, cu, 10, ext)
        cap = ipc2221_current_a(dd["min_w"], cu, 10, ext)
        per_layer[layer] = {"min_w": dd["min_w"], "cu_mm": cu, "ipc_w_10C": need, "ipc_w_20C": ipc2221_width_mm(i, cu, 20, ext),
                            "i_cap_10C_at_min_w": cap, "len_mm": dd["len_mm"]}
        if worst is None or cap < worst:
            worst = cap
    via_cap = round(len([v for v in vias if v["net"] == net]) * 1.0, 1)
    pn[net] = {"est_current_A": i, "min_width_mm": p["min_width_mm"], "via_count": p["via_count"], "via_sizes": p["via_sizes"],
               "per_layer": per_layer, "worst_segment_capacity_A": worst, "zones": p["zones"],
               "min_width_segments": p["min_width_segments"][:6]}
out["power_nets_ipc"] = pn

with open(os.path.join(HERE, "si_pi_dump.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=True, default=str)
with open(os.path.join(HERE, "power_nets.json"), "w", encoding="utf-8") as f:
    json.dump({"copper_thickness_mm": cu_thick, "note": "IPC-2221 widths for estimated current, dT 10/20 C; via ~1 A per 0.3 mm drill",
               "nets": pn}, f, indent=1, ensure_ascii=True, default=str)
print("ok", out["board"], out["totals"])
