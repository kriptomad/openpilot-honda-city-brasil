"""Step 3 (PCB side): SI/PI HIGH items 4, 5, 6 (fallback), 8, 11, 18, 19 of ../reports/si-pi-audit/proposed-changes.md.

Run with KiCad python:  python -u corr_step3_pcb.py [--dry] [--from-backup]
  --from-backup  restores %TEMP%/hp_backup/step3/HybridPanda.kicad_pcb first (replayable run)

Geometry (mm) comes from scans of the post-step-2 board (hardware/reports/corrections/_q_out.txt), not from the report,
whose U7 pad coordinates were off (pads 100/101 are at x 114.25/114.75, not 108.5/109.0).
"""
import json
import math
import os
import re
import shutil
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
SCH = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_sch")
REPORT = os.path.join(ROOT, "hardware/reports", "corrections", "step3_pcb.json")
FP_LIB = r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
SHEET_PATH = "/5994f1e8-15cb-459b-8e2e-160b94fba244"
DRY = "--dry" in sys.argv
if "--from-backup" in sys.argv:
    shutil.copy(os.path.join(os.environ["TEMP"], "hp_backup", "step3", "HybridPanda.kicad_pcb"), PCB)

board = pcbnew.LoadBoard(PCB)
rep = {"removed": [], "added": [], "nets": {}, "warnings": [], "checks": []}
keep = []


def mm(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def P(v):
    return (round(ToMM(v.x), 4), round(ToMM(v.y), 4))


def net(name):
    n = board.GetNetInfo().GetNetItem(name)
    if n is None or (n.GetNetCode() <= 0 and name != ""):
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
    elif desc == "FOOTPRINT":
        desc += " %s %s" % (item.GetReference(), P(item.GetPosition()))
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


def set_width(net_name, layer_name, a, b, w):
    ts = find_tracks(net_name, layer_name, a, b)
    assert ts, "track not found %s %s %s %s" % (net_name, layer_name, a, b)
    for t in ts:
        rep["added"].append("width %s %s %s->%s %.2f -> %.2f" % (net_name, layer_name, a, b, ToMM(t.GetWidth()), w))
        t.SetWidth(FromMM(w))


def add_track(a, b, w, layer_name, net_name):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(mm(*a)); t.SetEnd(mm(*b)); t.SetWidth(FromMM(w)); t.SetLayer(layer_id(layer_name))
    t.SetNet(net(net_name))
    board.Add(t)
    rep["added"].append("track %s %s %s->%s w=%.2f" % (net_name, layer_name, a, b, w))
    return t


def add_path(pts, w, layer_name, net_name):
    for i in range(len(pts) - 1):
        add_track(pts[i], pts[i + 1], w, layer_name, net_name)


def add_via(pos, net_name, d=0.6, drill=0.3):
    ex = find_via(net_name, pos, tol=0.05)
    if ex is not None:
        rep["added"].append("via %s %s reused" % (net_name, pos))
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


def pads_of(fp):
    return {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}


def place(ref, value, lib, name, pos, layer_name, pad_nets, want):
    """want(pads_dict) -> bool; rotation is stepped by 90 deg until it holds."""
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
    orient(fp, want)
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


def orient(fp, want):
    for _ in range(4):
        if want(pads_of(fp)):
            return
        fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 90)
    raise RuntimeError("orientation rule failed for " + fp.GetReference())


def move_to_bcu(ref, pos, want):
    fp = board.FindFootprintByReference(ref)
    if fp.GetLayer() != pcbnew.B_Cu:
        try:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        except AttributeError:
            fp.Flip(fp.GetPosition(), False)
    fp.SetPosition(mm(*pos))
    orient(fp, want)
    rep["added"].append("moved %s -> %s B.Cu rot %.0f pads %s" % (ref, pos, fp.GetOrientationDegrees(),
                                                                  {k: (pad_of(ref, k).GetNetname(), v) for k, v in pads_of(fp).items()}))
    return fp


def pad_of(ref, num):
    fp = board.FindFootprintByReference(ref)
    return next(p for p in fp.Pads() if p.GetNumber() == num)


def rename_net(old, new):
    nn = net(new)
    cnt = 0
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == old:
                p.SetNet(nn); cnt += 1
    for t in board.GetTracks():
        if t.GetNetname() == old:
            t.SetNet(nn); cnt += 1
    for z in board.Zones():
        if z.GetNetname() == old:
            z.SetNet(nn); cnt += 1
    o = board.GetNetInfo().GetNetItem(old)
    if o is not None and o.GetNetCode() > 0:
        board.RemoveNative(o)
    rep["nets"]["%s->%s" % (old, new)] = cnt


def purge_net(name, why):
    items = [t for t in board.GetTracks() if t.GetNetname() == name]
    for t in items:
        remove(t, why)
    return len(items)


# ============================================================================ 1) gate net rename (D15 added in sch)
GATE = "Net-(D15-A)"
rename_net("Net-(D2-A)", GATE)

# ============================================================================ 2) item 4: R1 1k 0402 -> 10k 0603
# R_0603 (courtyard 2.96 x 1.46) does not fit horizontally between D1 (x<=132.8) and Q4 (x>=135.005); it goes
# vertical at x 134.0 below D2 (bottom 51.895): gate pad on top (under D2.2), GND pad at the bottom next to the GND
# track that feeds P1 shell. Same net topology: D2.2 -> R1.2 -> Q4.4, R1.1 -> GND.
r1_old = board.FindFootprintByReference("R1")
old_pads = pads_of(r1_old)
for t in list(board.GetTracks()):
    if t.GetClass() == "PCB_VIA":
        continue
    for pn, pp in old_pads.items():
        s, e = P(t.GetStart()), P(t.GetEnd())
        if math.hypot(s[0] - pp[0], s[1] - pp[1]) < 0.35 or math.hypot(e[0] - pp[0], e[1] - pp[1]) < 0.35:
            remove(t, "touched old R1 pad %s" % pn)
            break
rm_track(GATE, "F.Cu", (133.95, 51.3), (134.425, 51.775), "old D2.2 -> R1.2 run (rebuilt)")
rm_track("GND", "F.Cu", (132.98, 51.915), (131.225, 51.915), "old R1.1 -> D1 GND run (would dangle)")
remove(r1_old, "R1 0402 -> 0603 (item 4)")
r1 = place("R1", "10k", "Resistor_SMD", "R_0603_1608Metric", (134.0, 53.4), "F.Cu", {"1": "GND", "2": GATE},
           lambda p: p["1"][1] - p["2"][1] > 0.5 and abs(p["2"][0] - p["1"][0]) < 0.05)
r1p = pads_of(r1)
pad_of("R1", "1").SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid to the F.Cu GND pour (no starved thermal)
add_path([(133.95, 51.3), (134.0, 51.35), r1p["2"]], 0.25, "F.Cu", GATE)              # D2.2 -> R1.2
add_path([r1p["2"], (134.81, r1p["2"][1]), (134.985, 52.4)], 0.25, "F.Cu", GATE)      # R1.2 -> existing run to Q4.4
add_path([r1p["1"], (134.190013, 54.894174)], 0.3, "F.Cu", "GND")                      # into the GND track corner (P1 shell)

# ============================================================================ 3) item 5: D15 BZT52C12 SOD-123 on B.Cu under the gate
# F.Cu around R1/D2/Q4 is full (D1, D2, Q4 courtyards, BUS2 tracks, P1). B.Cu there only holds the 12V_Protected vias.
d15 = place("D15", "BZT52C12", "Diode_SMD", "D_SOD-123", (133.9, 50.45), "B.Cu", {"1": "12V_Protected", "2": GATE},
            lambda p: p["2"][1] - p["1"][1] > 1.0 and abs(p["2"][0] - p["1"][0]) < 0.05)
d15p = pads_of(d15)
add_track(d15p["1"], (134.75, 48.6), 0.3, "B.Cu", "12V_Protected")      # existing 12V_Protected via (B.Cu side)
add_track(d15p["1"], (134.75, 49.425), 0.3, "B.Cu", "12V_Protected")
GV = (134.7, 51.5)
add_track(d15p["2"], GV, 0.3, "B.Cu", GATE)
add_via(GV, GATE, d=0.5)
add_track(GV, (134.1, 51.5), 0.25, "F.Cu", GATE)                        # into D2.2 (133.725-134.175 x 51.0-51.6)

# ============================================================================ 4) item 6 fallback: C4/C12 10uF stay 0805 (50 V X5R part)
for ref in ("C4", "C12"):
    fp = board.FindFootprintByReference(ref)
    fp.SetValue("10uF")
rep["checks"].append("C4/C12 value 10uF, footprint C_0805 kept (1206 refit blocked by SWDIO via / C7-C19 courtyard gap)")

# ============================================================================ 5) items 8/18/19: USB 22R at the MCU, ESD array at U3, coupled pair
# R20/R21 (0402) go to B.Cu in the pocket just north of U7 pads 100/101 (y 43.15 / 44.25, x 114.25), outputs west into
# two vias at x 113.635 (the only F.Cu window between the C4..C12 pad columns), then a coupled In1 pair (0.2 mm, 0.3 gap)
# at y 45.1/45.6 to x 127.9/128.8, up to U13 (SOT-23-6 flow-through) at (128.85,41.2) and on to U3 pads 2/3.
for n in ("USB_D+", "USB_D-", "USB_R_D+", "USB_R_D-"):
    rep["nets"]["purged " + n] = purge_net(n, "USB rework (item 19)")
r21 = move_to_bcu("R21", (114.25, 44.25), lambda p: p["2"][0] - p["1"][0] > 0.5 and abs(p["2"][1] - p["1"][1]) < 0.05)
r20 = move_to_bcu("R20", (114.25, 43.15), lambda p: p["1"][0] - p["2"][0] > 0.5 and abs(p["2"][1] - p["1"][1]) < 0.05)
for fp in (r20, r21):
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
r21p, r20p = pads_of(r21), pads_of(r20)
assert pad_of("R21", "2").GetNetname() == "USB_D+" and pad_of("R20", "1").GetNetname() == "USB_D-"
P101 = P(pad_of("U7", "101").GetPosition()); P100 = P(pad_of("U7", "100").GetPosition())
add_path([P101, (P101[0], r21p["2"][1])], 0.2, "B.Cu", "USB_D+")                       # straight up into R21.2
add_path([P100, (P100[0], r20p["1"][1]), r20p["1"]], 0.2, "B.Cu", "USB_D-")           # between the R21 pads into R20.1
VA = (113.635, 44.78); VB = (113.635, 42.75)          # B.Cu -> In1, inside the F.Cu window x 113.385-113.885
add_path([r21p["1"], VA], 0.2, "B.Cu", "USB_R_D+"); add_via(VA, "USB_R_D+", d=0.5)
add_path([r20p["2"], VB], 0.2, "B.Cu", "USB_R_D-"); add_via(VB, "USB_R_D-", d=0.5)
# In1 coupled pair; jog around the +3V3 via (117.0,44.74); D- north (45.1), D+ south (45.6)
VFM = (128.8, 45.1); VFP = (127.9, 45.65)
add_path([VB, (114.2, 43.315), (114.2, 44.8), (114.5, 45.1), (116.25, 45.1), (116.4, 45.25), (117.6, 45.25), (117.75, 45.1),
          VFM], 0.2, "In1.Cu", "USB_R_D-")
add_path([VA, (113.635, 45.6), (116.25, 45.6), (116.4, 45.75), (117.6, 45.75), (117.75, 45.6), (127.85, 45.6), VFP],
         0.2, "In1.Cu", "USB_R_D+")
add_via(VFM, "USB_R_D-", d=0.5); add_via(VFP, "USB_R_D+", d=0.5)
# F.Cu GND stitch (122.39,50.4)->(129.12,43.42) runs through the U13 spot: cut it at (127.47,49.64) and end it in a via
rm_track("GND", "F.Cu", (128.84, 43.7), (129.12, 43.42), "GND stitch through U13 spot")
rm_track("GND", "F.Cu", (128.84, 48.27), (128.84, 43.7), "GND stitch through U13 spot")
rm_track("GND", "F.Cu", (127.47, 49.64), (128.84, 48.27), "GND stitch through U13 spot")
remove(find_via("GND", (129.12, 43.42)), "GND stitch via (U13 spot)")
add_via((127.47, 49.64), "GND", d=0.6)
# U13 USBLC6-2SC6: rot 180 -> pins 3/4 (D+) west column, 1/6 (D-) east column, 2 (GND) north, 5 (VBUS) south
u13 = place("U13", "USBLC6-2SC6", "Package_TO_SOT_SMD", "SOT-23-6", (128.85, 41.2), "F.Cu",
            {"1": "USB_R_D-", "6": "USB_R_D-", "3": "USB_R_D+", "4": "USB_R_D+", "2": "GND", "5": "USB_PWR"},
            lambda p: p["2"][1] < p["5"][1] and p["3"][0] < p["1"][0] - 1.5 and abs(p["3"][0] - p["4"][0]) < 0.05)
u = pads_of(u13)
assert u["4"][1] > u["3"][1] and u["6"][1] > u["1"][1], u
add_path([VFP, (u["4"][0], VFP[1]), u["4"]], 0.2, "F.Cu", "USB_R_D+")                   # D+ in (south-west pad)
add_path([VFM, (u["6"][0], VFM[1] - (u["6"][0] - VFM[0])), u["6"]], 0.2, "F.Cu", "USB_R_D-")   # D- in (south-east pad)
add_path([u["3"], (u["3"][0], 39.1), (130.75, 39.1)], 0.2, "F.Cu", "USB_R_D+")          # D+ out -> U3.3 (y 38.22-39.34)
add_path([u["1"], (130.2, u["1"][1]), (130.75, u["1"][1] + 0.55)], 0.2, "F.Cu", "USB_R_D-")   # D- out -> U3.2 (y 40.22-41.34)
GAP_Y = (u["3"][1] + u["4"][1]) / 2.0                                                   # 41.2 between the rows
add_path([u["2"], (u["2"][0], GAP_Y), (127.4, GAP_Y), (126.9, GAP_Y)], 0.25, "F.Cu", "GND")
add_via((126.9, GAP_Y), "GND", d=0.5)
BV = (u["5"][0], u["5"][1] + 1.21)
add_track(u["5"], BV, 0.3, "F.Cu", "USB_PWR"); add_via(BV, "USB_PWR", d=0.5)
PWRV = (129.78, 46.5)                                # on the 1.0 mm USB_PWR F.Cu trace (129.78, 45.55-49.04)
add_path([BV, (PWRV[0], BV[1] + (PWRV[0] - BV[0])), PWRV], 0.3, "B.Cu", "USB_PWR")
add_via(PWRV, "USB_PWR", d=0.6)

# ============================================================================ 6) item 11: +5V feed to U1.6 (AP22615 VIN)
set_width("+5V", "In1.Cu", (118.54, 54.53), (116.50153, 54.95403), 1.0)
set_width("+5V", "In1.Cu", (116.50153, 54.95403), (116.12, 54.53), 0.5)
set_width("+5V", "In1.Cu", (116.12, 54.53), (115.25, 53.66), 0.5)
set_width("+5V", "F.Cu", (116.50153, 54.95403), (116.72, 54.53), 0.5)
set_width("+5V", "F.Cu", (116.72, 54.53), (117.02, 54.53), 0.5)
set_width("+5V", "F.Cu", (117.02, 54.53), (117.175, 54.375), 0.5)
V5 = (117.3, 55.0)
add_via(V5, "+5V", d=0.6)
add_track(V5, (117.3, 54.4), 0.5, "F.Cu", "+5V")      # straight up into U1.6 (116.51-117.84 x 54.075-54.675)

# ============================================================================ save
if not DRY:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board)
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1, default=str)
print(json.dumps({k: (v if k not in ("added", "removed") else len(v)) for k, v in rep.items()}, indent=1, default=str))
sys.stdout.flush()
os._exit(0)
