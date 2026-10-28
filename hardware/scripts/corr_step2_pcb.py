"""Step 2 (PCB side): PCR-2 VFBSMPS->VCAP merge + link, C64/C65 placement, PCR-1 PF9 strap via JP1.

Run with KiCad python:  python -u corr_step2_pcb.py [--dry]
Relies on step5c_fix_unrouted.py helpers (collision checks, A* router) executed as a library.
"""
import json
import math
import os
import re
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
SCH = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_sch")
REPORT = os.path.join(ROOT, "hardware/reports", "corrections", "step2_pcb.json")
FP_LIB = r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
SHEET_PATH = "/5994f1e8-15cb-459b-8e2e-160b94fba244"
DRY = "--dry" in sys.argv

board = pcbnew.LoadBoard(PCB)
rep = {"removed": [], "added": [], "nets": {}, "warnings": []}
keep = []  # python refs of removed items (RemoveNative quirk)


def mm(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def P(v):
    return (round(ToMM(v.x), 3), round(ToMM(v.y), 3))


def net(name):
    n = board.GetNetInfo().GetNetItem(name)
    if n is None or n.GetNetCode() <= 0 and name != "":
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        rep["nets"][name] = "created"
    return n


def layer_id(name):
    return board.GetLayerID(name)


def find_tracks(net_name, layer_name, a, b, tol=0.01):
    out = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetname() != net_name or board.GetLayerName(t.GetLayer()) != layer_name:
            continue
        s, e = P(t.GetStart()), P(t.GetEnd())
        if (abs(s[0] - a[0]) < tol and abs(s[1] - a[1]) < tol and abs(e[0] - b[0]) < tol and abs(e[1] - b[1]) < tol) or \
           (abs(s[0] - b[0]) < tol and abs(s[1] - b[1]) < tol and abs(e[0] - a[0]) < tol and abs(e[1] - a[1]) < tol):
            out.append(t)
    return out


def find_via(net_name, pos, tol=0.01):
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == net_name:
            p = P(t.GetPosition())
            if abs(p[0] - pos[0]) < tol and abs(p[1] - pos[1]) < tol:
                return t
    return None


def remove(item, why):
    assert item is not None, "item to remove not found: " + why
    desc = item.GetClass()
    if desc == "PCB_VIA":
        desc += " %s %s" % (item.GetNetname(), P(item.GetPosition()))
    else:
        desc += " %s %s %s->%s" % (item.GetNetname(), board.GetLayerName(item.GetLayer()), P(item.GetStart()), P(item.GetEnd()))
    keep.append(item)
    board.RemoveNative(item)
    rep["removed"].append(desc + " | " + why)


def rm_track(net_name, layer_name, a, b, why):
    ts = find_tracks(net_name, layer_name, a, b)
    assert len(ts) >= 1, "track not found %s %s %s %s" % (net_name, layer_name, a, b)
    for t in ts:
        remove(t, why)


def add_track(a, b, w, layer_name, net_name):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(mm(*a)); t.SetEnd(mm(*b)); t.SetWidth(FromMM(w)); t.SetLayer(layer_id(layer_name))
    t.SetNet(net(net_name))
    board.Add(t)
    rep["added"].append("track %s %s %s->%s w=%.2f" % (net_name, layer_name, a, b, w))
    return t


def add_via(pos, net_name, d=0.6, drill=0.3):
    ex = find_via(net_name, pos, tol=0.05)
    if ex is not None:
        rep["added"].append("via %s %s reused (already on board)" % (net_name, pos))
        return ex
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(mm(*pos)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FromMM(d)); v.SetDrill(FromMM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(net_name))
    board.Add(v)
    rep["added"].append("via %s %s d=%.2f" % (net_name, pos, d))
    return v


def sch_uuid(ref):
    txt = open(SCH, encoding="utf-8").read()
    for m in re.finditer(r'\(symbol \(lib_id "[^"]+"\)[\s\S]*?\(uuid "?([0-9a-f-]{36})"?\)[\s\S]*?\(property "Reference" "([^"]+)"', txt):
        if m.group(2) == ref:
            return m.group(1)
    raise KeyError(ref)


def place(ref, value, lib, name, pos, rot, layer_name, pad_nets, orient_rule):
    """pad_nets: {padnumber: net}; orient_rule: (padnumber, 'N'|'S'|'E'|'W') -> rotate until that pad is on that side."""
    fp = pcbnew.FootprintLoad(os.path.join(FP_LIB, lib + ".pretty"), name)
    assert fp is not None, name
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetPath(pcbnew.KIID_PATH(SHEET_PATH + "/" + sch_uuid(ref)))
    board.Add(fp); fp.thisown = 0
    fp.SetPosition(mm(*pos))
    if layer_name == "B.Cu":
        try:
            fp.Flip(mm(*pos), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        except AttributeError:
            fp.Flip(mm(*pos), False)
    fp.SetOrientationDegrees(rot)
    padno, side = orient_rule
    for _ in range(4):
        pads = {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}
        other = next(k for k in pads if k != padno)
        dx = pads[padno][0] - pads[other][0]; dy = pads[padno][1] - pads[other][1]
        ok = {"N": dy < -0.1, "S": dy > 0.1, "E": dx > 0.1, "W": dx < -0.1}[side]
        if ok:
            break
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
    else:
        raise RuntimeError("orientation rule failed for " + ref)
    for p in fp.Pads():
        p.SetNet(net(pad_nets[p.GetNumber()]))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for f in (fp.Reference(), fp.Value()):
        f.SetTextSize(VECTOR2I(FromMM(0.5), FromMM(0.5)))
    rep["added"].append("footprint %s %s %s:%s at %s rot %.0f %s pads %s" % (
        ref, value, lib, name, pos, fp.GetOrientationDegrees(), layer_name,
        {p.GetNumber(): (p.GetNetname(), P(p.GetPosition())) for p in fp.Pads()}))
    return fp


def pad_of(ref, num):
    fp = board.FindFootprintByReference(ref)
    return next(p for p in fp.Pads() if p.GetNumber() == num)


# ----------------------------------------------------------------------------- A) VFBSMPS -> VCAP
vcap = net("VCAP")
n_merged = 0
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "VFBSMPS":
            p.SetNet(vcap); n_merged += 1
for t in board.GetTracks():
    if t.GetNetname() == "VFBSMPS":
        t.SetNet(vcap); n_merged += 1
for z in board.Zones():
    if z.GetNetname() == "VFBSMPS":
        z.SetNet(vcap); n_merged += 1
rep["nets"]["VFBSMPS->VCAP items"] = n_merged
old = board.GetNetInfo().GetNetItem("VFBSMPS")
if old is not None and old.GetNetCode() > 0:
    board.RemoveNative(old)  # unused net record
    rep["nets"]["VFBSMPS"] = "removed"

# ----------------------------------------------------------------------------- B) PF9 strap (PCR-1)
# old B.Cu strap: pads 21..24 stubs to y=66.362 bus + diag to GND via (107.051,66.217); F.Cu GND diag + wall
rm_track("GND", "B.Cu", (107.25, 67.263), (107.25, 66.362), "PF9 stub (pad 23) -> lifted from GND")
rm_track("GND", "B.Cu", (108.25, 66.362), (106.75, 66.362), "GND bus over PF9 (clearance to lifted pad)")
rm_track("GND", "B.Cu", (107.75, 67.263), (107.051, 66.217), "GND diag over PF9 pad corner")
rm_track("GND", "B.Cu", (106.75, 67.263), (106.75, 66.362), "pad 24 stub (rebuilt)")
rm_track("GND", "B.Cu", (107.75, 67.263), (107.75, 66.362), "pad 22 stub (rebuilt)")
remove(find_via("GND", (107.051, 66.217)), "GND via touching lifted PF9 pad")
rm_track("GND", "F.Cu", (109.25, 68.942), (107.051, 66.217), "redundant F.Cu GND diag (plane In2 carries GND); frees pocket for C65/JP1")
rm_track("GND", "F.Cu", (109.25, 68.942), (109.15, 71.042), "redundant F.Cu GND wall (via 109.15,71.042 stays)")
# pad 21 stub is (108.25,67.263)->(108.25,66.362): keep, bus replaced by via at (108.0,65.9)
add_track((108.25, 66.362), (108.25, 65.8625), 0.25, "B.Cu", "GND")   # existing GND via at (108.25,65.8625)
add_track((107.75, 67.263), (108.25, 65.8625), 0.2, "B.Cu", "GND")  # pad 22 diagonal
add_via((106.75, 65.5), "GND")
add_track((106.75, 67.263), (106.75, 65.5), 0.2, "B.Cu", "GND")  # pad 24
# PF9 (pad 23) -> via -> F.Cu -> JP1 pad B (north)
PF9 = "Net-(JP1-B)"
net(PF9)
pad_of("U7", "23").SetNet(net(PF9))
add_track((107.25, 67.263), (107.3, 66.2), 0.2, "B.Cu", PF9)
add_via((107.3, 66.2), PF9)
add_track((107.3, 66.2), (107.72, 66.62), 0.2, "F.Cu", PF9)
add_track((107.72, 66.62), (107.72, 72.25), 0.2, "F.Cu", PF9)   # x=107.72: hole_clearance >=0.25 to LED_RED via (107.207,69.04)
jp1 = place("JP1", "HW_ID1", "Jumper", "SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm", (107.6, 72.9), 90, "F.Cu",
            {"1": "GND", "2": PF9}, ("2", "N"))
jp_pads = {p.GetNumber(): P(p.GetPosition()) for p in jp1.Pads()}
add_track(jp_pads["2"], (107.72, 72.25), 0.2, "F.Cu", PF9)
add_via((107.6, 74.4), "GND")
add_track(jp_pads["1"], (107.6, 74.4), 0.3, "F.Cu", "GND")

# ----------------------------------------------------------------------------- C) C65 4.7uF (VDDSMPS pin 16) on F.Cu pocket
c65 = place("C65", "4.7uF", "Capacitor_SMD", "C_0603_1608Metric", (109.3, 70.1), 0, "F.Cu",
            {"1": "+3V3", "2": "GND"}, ("1", "E"))   # y=70.1: courtyard clear of C47 (bottom 69.418)
c65p = {p.GetNumber(): P(p.GetPosition()) for p in c65.Pads()}
add_track(c65p["1"], (110.75, 69.062), 0.3, "F.Cu", "+3V3")      # to pin-16 via
add_track(c65p["2"], (108.5, 70.6), 0.3, "F.Cu", "GND")
add_track((108.5, 70.6), (109.15, 71.042), 0.3, "F.Cu", "GND")   # existing GND via
# C47 pad 2 lost its F.Cu GND tracks (removed above): tie it to C65 pad 2 so it keeps a solid GND path
add_track((109.25, 68.9425), (108.3, 68.9425), 0.25, "F.Cu", "GND")
add_track((108.3, 68.9425), (108.3, 69.9), 0.25, "F.Cu", "GND")
add_track((108.3, 69.9), c65p["2"], 0.25, "F.Cu", "GND")

# ----------------------------------------------------------------------------- D) C64 2.2uF (VCAP pin 103) on B.Cu north of the U7 north row
# Pocket between the SWDIO via and C54 (B.Cu). F.Cu opposite side is full (C19/C20 0805, L4 courtyard).
# - SWDIO via (115.711,43.3) -> (115.56,43.42): hole clearance 0.265 to C12 F.Cu pad and >=0.525 to the F.Cu GND diagonal.
# - C54 (0402 +3V3 decoupler) slides 0.15 mm east (117.25 -> 117.4) so the C64 courtyard does not touch it; its 4 stubs are rebuilt.
# - C64 rot 90 at (116.28,44.0): pad 1 VCAP south -> pad 103 (1.5 mm), pad 2 GND north -> GND via.
# - Pad 104 (GND) loses its stub via (it sat under the new VCAP pad); it stays tied to GND through the B.Cu GND zone.
rm_track("SWDIO", "B.Cu", (115.711, 43.3), (115.25, 43.761), "SWDIO via relocation")
rm_track("SWDIO", "In2.Cu", (115.371, 43.64), (115.711, 43.3), "SWDIO via relocation")
remove(find_via("SWDIO", (115.711, 43.3)), "SWDIO via relocation")
rm_track("GND", "B.Cu", (116.25, 45.938), (116.25, 45.038), "pad 104 GND stub (via sat under C64 pad 1)")
rm_track("GND", "B.Cu", (116.25, 45.038), (116.25, 44.438), "pad 104 GND stub (via sat under C64 pad 1)")
remove(find_via("GND", (116.25, 44.438)), "pad 104 GND via (under C64 pad 1)")
# C54 slide
rm_track("+3V3", "B.Cu", (117.25, 43.8175), (117.25, 45.9375), "C54 slide")
rm_track("+3V3", "B.Cu", (117.25, 43.8175), (117.978439, 43.63896), "C54 slide")
rm_track("GND", "B.Cu", (117.25, 42.8575), (117.618412, 42.204221), "C54 slide")
c54 = board.FindFootprintByReference("C54")
c54.SetPosition(mm(117.4, 43.3375))
rep["added"].append("C54 moved (117.25,43.3375) -> (117.4,43.3375)")
c54p = {p.GetNumber(): P(p.GetPosition()) for p in c54.Pads()}
p3, pg = (c54p["1"], c54p["2"]) if pad_of("C54", "1").GetNetname() == "+3V3" else (c54p["2"], c54p["1"])
add_track(p3, (117.25, 44.1), 0.2, "B.Cu", "+3V3")
add_track((117.25, 44.1), (117.25, 45.9375), 0.2, "B.Cu", "+3V3")
add_track(p3, (117.978439, 43.63896), 0.25, "B.Cu", "+3V3")
add_track(pg, (117.618412, 42.204221), 0.25, "B.Cu", "GND")
c64 = place("C64", "2.2uF", "Capacitor_SMD", "C_0402_1005Metric", (116.28, 44.0), 90, "B.Cu",
            {"1": "VCAP", "2": "GND"}, ("1", "S"))
c64p = {p.GetNumber(): P(p.GetPosition()) for p in c64.Pads()}
# collision helpers (step5c) loaded AFTER the new footprints exist so their pads count as obstacles
g = {"PRELOADED_BOARD": board, "AS_LIBRARY": True, "__file__": os.path.join(HERE, "step5c_fix_unrouted.py"), "__name__": "step5c_lib"}
with open(g["__file__"], encoding="utf-8") as f:
    exec(compile(f.read(), g["__file__"], "exec"), g)
def pick_via(cands, net_name, d, segs):
    """first candidate whose via and connecting segments do not collide (segs: list of (other_end, width, layer))"""
    ncode = net(net_name).GetNetCode()
    for c in cands:
        why = g["via_collides"](mm(*c), d, ncode, 0.12, drill=0.3)
        if why:
            rep["warnings"].append("via cand %s %s rejected: %s" % (net_name, c, why)); continue
        bad = None
        for other, w, lay in segs:
            bad = g["seg_collides"](mm(*c), mm(*other), w, layer_id(lay), ncode)
            if bad: break
        if bad:
            rep["warnings"].append("via cand %s %s seg rejected: %s" % (net_name, c, bad)); continue
        return c
    print("\n".join(rep["warnings"])); sys.stdout.flush()
    raise SystemExit("no via candidate for %s" % net_name)
sw_via = pick_via([(115.56, 43.42), (115.58, 43.45), (115.6, 43.4), (115.56, 43.5)], "SWDIO", 0.5,
                  [((115.371, 43.64), 0.2, "In2.Cu"), ((115.25, 43.761), 0.2, "B.Cu")])
add_track((115.371, 43.64), sw_via, 0.2, "In2.Cu", "SWDIO")
add_via(sw_via, "SWDIO", d=0.5)
add_track(sw_via, (115.25, 43.761), 0.2, "B.Cu", "SWDIO")   # joins the existing B.Cu stub (115.25,43.761)->pad 102
add_track(c64p["1"], (115.75, 45.0), 0.25, "B.Cu", "VCAP")
add_track((115.75, 45.0), (115.75, 45.938), 0.25, "B.Cu", "VCAP")
gv = pick_via([(116.28, 42.75), (116.35, 42.7), (116.2, 42.75), (116.28, 42.65), (116.1, 42.6)], "GND", 0.6, [(c64p["2"], 0.25, "B.Cu")])
add_via(gv, "GND")
add_track(c64p["2"], gv, 0.25, "B.Cu", "GND")
# ----------------------------------------------------------------------------- E) VCAP link (VFBSMPS group <-> VCAP group)
nc = vcap.GetNetCode()
_pads_all = [p for fp_ in board.GetFootprints() for p in fp_.Pads()]
def via_in_pad(vpos, d):
    """same-net pad overlap is DRC-clean but final_audit counts it as via-in-pad"""
    circ = pcbnew.SHAPE_CIRCLE(vpos, FromMM(d / 2))
    for p in _pads_all:
        for l in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(l) and p.GetEffectiveShape(l).Collide(circ, FromMM(0.05)):
                return True
    return False
best = None
starts = [((110.025, 70.263), "L5.2"), ((110.25, 67.263), "U7.17"), ((109.425, 72.752), "C42.1")]
# targets are EXACT coordinates of existing In1 VCAP copper (a 0.4 um offset left a dangling end in the first run)
targets_in1 = [(118.1934, 61.1779), (118.1934, 62.6786), (118.1934, 62.0), (113.9807, 56.9652), (113.9807, 54.0)]
# candidate via spots near the VFBSMPS group (B.Cu side), checked with step5c via_collides
via_cands = []
for (sx, sy), nm in starts:
    for d in (0.0, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0):
        for k in range(8 if d else 1):
            ang = k * math.pi / 4
            vx, vy = sx + d * math.cos(ang), sy + d * math.sin(ang)
            vpos = mm(vx, vy)
            if g["via_collides"](vpos, 0.6, nc, 0.12) or via_in_pad(vpos, 0.6):
                continue
            if d and g["seg_collides"](mm(sx, sy), vpos, 0.3, pcbnew.B_Cu, nc) is not None:
                continue
            via_cands.append(((sx, sy), (round(vx, 3), round(vy, 3)), nm))
rep["vcap_link_via_candidates"] = len(via_cands)
for (s, v, nm) in via_cands[:12]:
    for tgt in targets_in1:
        path = g["astar_route"](mm(*v), mm(*tgt), pcbnew.In1_Cu, nc, width=0.3, step=0.25, margin=3.0, max_nodes=60000)
        if path:
            length = sum(ToMM((path[i + 1] - path[i]).EuclideanNorm()) for i in range(len(path) - 1))
            if best is None or length < best[0]:
                best = (length, s, v, tgt, path, nm)
    if best and best[0] < 12:
        break
if best:
    length, s, v, tgt, path, nm = best
    if s != v:
        add_track(s, v, 0.3, "B.Cu", "VCAP")
    add_via(v, "VCAP")
    for i in range(len(path) - 1):
        add_track(P(path[i]), P(path[i + 1]), 0.3, "In1.Cu", "VCAP")
    rep["vcap_link"] = {"from": nm, "via": v, "target_in1": tgt, "length_mm": round(length, 2), "pts": [P(p) for p in path]}
else:
    rep["warnings"].append("VCAP link: no In1 A* path found; run step5c")

# ----------------------------------------------------------------------------- save
if not DRY:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board)
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1, default=str)
print(json.dumps({k: (v if k != "added" and k != "removed" else len(v)) for k, v in rep.items()}, indent=1, default=str))
sys.stdout.flush()
os._exit(0)





