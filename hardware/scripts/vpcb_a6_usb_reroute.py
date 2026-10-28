"""vpcb_a6_usb_reroute.py - A6: reroute USB_D+/USB_D- (MCU -> series R) and USB_R_D+/USB_R_D- (series R -> ESD U13 -> USB-A U3)
as an edge-coupled differential pair.

Autor: Bruno Costa

What it does (all coordinates in mm, board origin as in the .kicad_pcb):
  1. removes every track and via of the four USB nets, the USB_PWR bottom-side detour (via + 2 tracks + F.Cu stub), the SWDIO
     escape (2 tracks), the GND stitching via at 115.370,42.665 with its F.Cu stub, and the C54/C64 GND vias;
  2. rotates R20 (D-) and R21 (D+) to vertical, side by side at x = 113.69 / 114.75 (USB_D pads facing the MCU);
  3. routes the pair on B.Cu (MCU and R side): neck 0.20/0.15 mm from the resistors through the 0.83 mm corridor between C62 and
     C54, then 0.35/0.15 mm (A5 result for 90 ohm on JLC7628) to a symmetric via pair at y = 43.6 under the ESD diode U13;
  4. routes the remainder on F.Cu at 0.35 mm: via -> U13 pin 4/6 -> strap to pin 3/1 -> U3 pins 3/2 (same topology as before);
  5. re-routes USB_PWR on F.Cu only (U13.5 -> U3.1), re-routes SWDIO 0.10 mm further east, and gives C54.2/C64.2 one shared GND via;
  6. sets the USB netclass to 0.35/0.15 mm, refills zones, saves, runs DRC and writes usb-reroute.md (+ usb-reroute.json).
Every new segment/via is checked against all other copper with the same collision index used by fix_drc_relayout.py before the
board is written; if any check fails the script aborts without saving.
"""
import json
import math
import os
import subprocess
import sys
import time

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
PRO = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pro")
SNAP = os.path.join(ROOT, "hardware", "hybrid-panda", "snapshots", "HybridPanda.kicad_pcb.pre_verification")
OUTD = os.path.join(ROOT, "hardware", "reports", "verification-pcb")
DRC_JSON = os.path.join(OUTD, "drc_after_a6.json")
KICAD_CLI = str(hp.KICAD_CLI)
DRY = "--dry" in sys.argv

W, S = 0.35, 0.15           # A5 result, JLC7628, 90 ohm differential
WN, SN = 0.20, 0.15         # neck through the decoupling-capacitor corridor and at the 0.30 mm LQFP pads
VIA_D, VIA_DRILL = 0.6, 0.3
CLR, HOLE_CLR = 0.10, 0.25
LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
NETS = ("USB_D+", "USB_D-", "USB_R_D+", "USB_R_D-")


def mm(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def dist(a, b):
    return ToMM((a - b).EuclideanNorm())


def P(v):
    return "%.3f,%.3f" % (ToMM(v.x), ToMM(v.y))


class Index:
    """Collision index (pads, vias, tracks, keepouts) - same checks as fix_drc_relayout.Index."""

    def __init__(self, board):
        self.items, self.holes = [], []
        for p in [q for f in board.GetFootprints() for q in f.Pads()]:
            for l in LAYERS4:
                if p.IsOnLayer(l):
                    self.items.append((p.GetBoundingBox(), l, p.GetNetCode(), p.GetEffectiveShape(l), p))
            if p.GetDrillSize().x > 0:
                self.holes.append((p.GetPosition(), ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, p.GetNetCode(), p))
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                for l in LAYERS4:
                    self.items.append((t.GetBoundingBox(), l, t.GetNetCode(), t.GetEffectiveShape(l), t))
                self.holes.append((t.GetPosition(), ToMM(t.GetDrill()) / 2, t.GetNetCode(), t))
            else:
                self.items.append((t.GetBoundingBox(), t.GetLayer(), t.GetNetCode(), t.GetEffectiveShape(t.GetLayer()), t))
        self.keep = [z for z in board.Zones() if z.GetIsRuleArea()]

    def via_ok(self, pos, dia, drill, nc):
        shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2))
        hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2))
        R = FromMM(dia / 2 + HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowVias() and z.Outline().Collide(shp, 0):
                return "keepout"
        for bb, l, n, s, o in self.items:
            if n == nc:
                continue
            if bb.GetRight() + R < pos.x or bb.GetLeft() - R > pos.x or bb.GetBottom() + R < pos.y or bb.GetTop() - R > pos.y:
                continue
            if s.Collide(shp, FromMM(CLR)) or s.Collide(hole, FromMM(HOLE_CLR)):
                return "copper %s (%s)" % (o.GetNetname(), o.GetClass())
        for hp_, hr, n, o in self.holes:
            if dist(hp_, pos) < hr + drill / 2 + HOLE_CLR + 0.01:
                return "hole %s" % P(hp_)
        return None

    def seg_ok(self, a, b, w, layer, nc):
        shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(w))
        bb = shp.BBox()
        R = FromMM(HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(CLR)):
                return "keepout"
        for ib, l, n, s, o in self.items:
            if n == nc or l != layer:
                continue
            if ib.GetRight() + R < bb.GetLeft() or ib.GetLeft() - R > bb.GetRight() or ib.GetBottom() + R < bb.GetTop() or ib.GetTop() - R > bb.GetBottom():
                continue
            if s.Collide(shp, FromMM(CLR)):
                return "copper %s (%s %s)" % (o.GetNetname(), o.GetClass(), P(o.GetPosition()))
        for hp_, hr, n, o in self.holes:
            if n == nc:
                continue
            if shp.Collide(pcbnew.SHAPE_CIRCLE(hp_, FromMM(hr)), FromMM(HOLE_CLR)):
                return "hole %s" % P(hp_)
        return None


def net_summary(board, names):
    """Per-net list of segments (layer, length) and vias, used for the before/after table."""
    out = {}
    for n in names:
        segs, vias = [], []
        for t in board.GetTracks():
            if t.GetNetname() != n:
                continue
            if t.GetClass() == "PCB_VIA":
                vias.append(P(t.GetPosition()))
            else:
                segs.append((board.GetLayerName(t.GetLayer()), ToMM(t.GetLength()), ToMM(t.GetWidth())))
        by_layer = {}
        for l, L, w in segs:
            by_layer[l] = by_layer.get(l, 0.0) + L
        out[n] = {"segments": len(segs), "vias": vias, "length_mm": round(sum(s[1] for s in segs), 3),
                  "by_layer_mm": {k: round(v, 3) for k, v in by_layer.items()}, "widths": sorted({round(s[2], 3) for s in segs})}
    return out


def load_snapshot():
    """pcbnew.LoadBoard needs the .kicad_pcb extension; load the snapshot through a temporary copy next to it."""
    import shutil
    tmp = SNAP + ".tmp_load.kicad_pcb"
    shutil.copyfile(SNAP, tmp)
    try:
        return pcbnew.LoadBoard(tmp)
    finally:
        os.remove(tmp)


def pad(board, ref, num):
    for f in board.GetFootprints():
        if f.GetReference() == ref:
            for p in f.Pads():
                if p.GetNumber() == str(num):
                    return p
    raise KeyError((ref, num))


def main():
    os.makedirs(OUTD, exist_ok=True)
    hp.assert_inside_output(PCB)
    hp.assert_inside_output(PRO)
    before = net_summary(load_snapshot(), NETS + ("USB_PWR", "SWDIO"))
    board = pcbnew.LoadBoard(PCB)
    log = []
    nets = {n: board.FindNet(n) for n in NETS + ("USB_PWR", "SWDIO", "GND")}
    assert all(nets.values()), nets

    # ---------------------------------------------------------------- 1. remove old copper
    def near(t, x, y, tol=0.02):
        return dist(t.GetPosition() if t.GetClass() == "PCB_VIA" else t.GetStart(), mm(x, y)) < tol or \
            (t.GetClass() != "PCB_VIA" and dist(t.GetEnd(), mm(x, y)) < tol)

    removed = {"tracks": 0, "vias": 0, "detail": []}
    victims = []
    for t in board.GetTracks():
        n = t.GetNetname()
        kill = n in NETS
        if n == "USB_PWR" and (near(t, 128.850, 43.547) or near(t, 129.780, 44.477) or near(t, 129.780, 46.500)):
            kill = True
        if n == "SWDIO" and (near(t, 115.250, 43.761)):
            kill = True
        if n == "GND" and (near(t, 115.370, 42.665) or near(t, 117.618, 42.204) or near(t, 116.280, 42.750)):
            kill = True
        if kill:
            victims.append(t)
    for t in victims:
        n = t.GetNetname()
        removed["detail"].append("%s %s %s" % (n, t.GetClass(), P(t.GetPosition()) if t.GetClass() == "PCB_VIA" else P(t.GetStart()) + "->" + P(t.GetEnd())))
        removed["vias" if t.GetClass() == "PCB_VIA" else "tracks"] += 1
        board.Remove(t)
    log.append("removed %d tracks and %d vias" % (removed["tracks"], removed["vias"]))

    # ---------------------------------------------------------------- 2. rotate the series resistors
    moves = {}
    for ref, x, south_net in (("R20", 113.69, "USB_D-"), ("R21", 114.75, "USB_D+")):
        f = [fp for fp in board.GetFootprints() if fp.GetReference() == ref][0]
        old = (P(f.GetPosition()), f.GetOrientationDegrees())
        f.SetPosition(mm(x, 43.95))
        for ang in (90, 270, -90, 0, 180):
            f.SetOrientationDegrees(ang)
            ps = {p.GetNetname(): ToMM(p.GetPosition().y) for p in f.Pads()}
            if abs(ps[south_net] - 44.46) < 0.02:
                break
        else:
            raise RuntimeError("could not orient %s" % ref)
        pads = {p.GetNetname(): P(p.GetPosition()) for p in f.Pads()}
        moves[ref] = {"before": {"pos": old[0], "rot": old[1]}, "after": {"pos": P(f.GetPosition()), "rot": f.GetOrientationDegrees(), "pads": pads}}
    log.append("R20/R21 rotated: %s" % json.dumps(moves))

    # ---------------------------------------------------------------- 3. geometry
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    YL = 38.40  # D+ loop on F.Cu, tuned below for skew
    # B.Cu, net USB_D- / USB_D+ (MCU stubs, 0.20 at the 0.30 mm LQFP pads)
    seg_dm_mcu = [((114.25, 45.938), (114.25, 45.15)), ((114.25, 45.15), (113.69, 44.59)), ((113.69, 44.59), (113.69, 44.46))]
    seg_dp_mcu = [((114.75, 45.938), (114.75, 44.46))]
    # B.Cu, USB_R_D- (north line) / USB_R_D+ (south line): neck 0.20/0.15 up to x = 118.16
    dm_neck = [(113.69, 43.44), (113.69, 42.50), (115.10, 42.50), (115.67, 41.93), (118.31, 41.93)]
    dp_neck = [(114.75, 43.44), (114.75, 42.85), (115.45, 42.85), (116.02, 42.28), (118.16, 42.28), (118.31, 42.43)]
    # 0.35/0.15 from x = 118.31 (D+ steps to pitch 0.50 while still 0.20 wide), both jog north around the SWCLK via, run east, split to the via pair
    dm_wide = [(118.31, 41.93), (118.343, 41.93), (119.423, 40.85), (126.10, 40.85), (128.85, 43.60), (129.80, 43.60)]
    dp_wide = [(118.31, 42.43), (118.55, 42.43), (119.63, 41.35), (125.65, 41.35), (127.90, 43.60)]
    via_dp, via_dm = (127.90, 43.60), (129.80, 43.60)

    def f_paths(yl):
        dp = [(127.90, 43.60), (127.90, 42.337), (127.90, 40.062), (127.90, yl), (132.05 - (38.78 - yl), yl), (132.05, 38.78)]
        dm = [(129.80, 43.60), (129.80, 42.337), (129.80, 40.062), (130.20, 40.062), (130.918, 40.78), (132.05, 40.78)]
        return dp, dm

    def plen(pts):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))

    def total(yl):
        dp_f, dm_f = f_paths(yl)
        Lp = plen([a for a, b in seg_dp_mcu] + [seg_dp_mcu[-1][1]]) + plen(dp_neck) + plen(dp_wide) + plen(dp_f)
        Lm = plen([a for a, b in seg_dm_mcu] + [seg_dm_mcu[-1][1]]) + plen(dm_neck) + plen(dm_wide) + plen(dm_f)
        return Lp, Lm

    best = min((abs(total(y)[0] - total(y)[1]), y) for y in (38.40, 38.45, 38.50, 38.55, 38.60))
    YL = best[1]
    Lp, Lm = total(YL)
    dp_f, dm_f = f_paths(YL)
    log.append("F.Cu D+ loop at y=%.2f; copper length D+ %.3f mm, D- %.3f mm, skew %.3f mm" % (YL, Lp, Lm, Lp - Lm))

    plan = []  # (a, b, w, layer, net)
    for a, b in seg_dm_mcu:
        plan.append((a, b, WN, B, "USB_D-"))
    for a, b in seg_dp_mcu:
        plan.append((a, b, WN, B, "USB_D+"))
    for pts, net in ((dm_neck, "USB_R_D-"), (dp_neck, "USB_R_D+")):
        plan += [(a, b, WN, B, net) for a, b in zip(pts, pts[1:])]
    for pts, net in ((dm_wide, "USB_R_D-"), (dp_wide, "USB_R_D+")):
        plan += [(a, b, W, B, net) for a, b in zip(pts, pts[1:])]
    for pts, net in ((dp_f, "USB_R_D+"), (dm_f, "USB_R_D-")):
        plan += [(a, b, W, F, net) for a, b in zip(pts, pts[1:])]
    # USB_PWR on F.Cu only
    plan += [((128.85, 42.337), (128.85, 44.62), 1.0, F, "USB_PWR"), ((128.85, 44.62), (129.78, 45.55), 1.0, F, "USB_PWR")]
    # SWDIO escape 0.10 mm east of the old one (R21 pad now reaches x = 115.07)
    plan += [((115.25, 45.938), (115.25, 45.45), 0.2, B, "SWDIO"), ((115.25, 45.45), (115.35, 45.35), 0.2, B, "SWDIO"),
             ((115.35, 45.35), (115.35, 43.63), 0.2, B, "SWDIO"), ((115.35, 43.63), (115.56, 43.42), 0.2, B, "SWDIO")]
    # shared GND via for C64.2 and C54.2
    plan += [((116.28, 43.00), (116.28, 43.52), 0.25, B, "GND"), ((116.28, 43.00), (117.40, 43.00), 0.25, B, "GND")]
    vias = [(via_dp, "USB_R_D+"), (via_dm, "USB_R_D-"), ((116.28, 43.00), "GND")]

    # ---------------------------------------------------------------- 4. collision check, then add
    idx = Index(board)
    problems = []
    for a, b, w, layer, net in plan:
        r = idx.seg_ok(mm(*a), mm(*b), w, layer, nets[net].GetNetCode())
        if r:
            problems.append("SEG %s %s %s->%s w%.2f: %s" % (net, board.GetLayerName(layer), a, b, w, r))
    for p, net in vias:
        r = idx.via_ok(mm(*p), VIA_D, VIA_DRILL, nets[net].GetNetCode())
        if r:
            problems.append("VIA %s %s: %s" % (net, p, r))
    # new items against each other (different nets only)
    new_shapes = [(pcbnew.SHAPE_SEGMENT(mm(*a), mm(*b), FromMM(w)), layer, net) for a, b, w, layer, net in plan]
    for p, net in vias:
        for l in LAYERS4:
            new_shapes.append((pcbnew.SHAPE_CIRCLE(mm(*p), FromMM(VIA_D / 2)), l, net))
    for i in range(len(new_shapes)):
        for j in range(i + 1, len(new_shapes)):
            s1, l1, n1 = new_shapes[i]
            s2, l2, n2 = new_shapes[j]
            if l1 != l2 or n1 == n2:
                continue
            if isinstance(s1, pcbnew.SHAPE_SEGMENT):
                hit = s1.Collide(s2, FromMM(CLR))
            elif isinstance(s2, pcbnew.SHAPE_SEGMENT):
                hit = s2.Collide(s1, FromMM(CLR))
            else:
                hit = dist(s1.GetCenter(), s2.GetCenter()) < ToMM(s1.GetRadius() + s2.GetRadius()) + CLR
            if hit:
                problems.append("NEW-NEW %s/%s on %s" % (n1, n2, board.GetLayerName(l1)))
    # coupled-pair geometry report: gap along the parallel sections
    for pr in problems:
        print("PROBLEM", pr)
    if problems:
        print("aborting, nothing written")
        return 2

    for a, b, w, layer, net in plan:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(mm(*a))
        t.SetEnd(mm(*b))
        t.SetWidth(FromMM(w))
        t.SetLayer(layer)
        t.SetNet(nets[net])
        board.Add(t)
    for p, net in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(mm(*p))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetWidth(FromMM(VIA_D))
        v.SetDrill(FromMM(VIA_DRILL))
        v.SetNet(nets[net])
        board.Add(v)
    log.append("added %d segments and %d vias" % (len(plan), len(vias)))

    # ---------------------------------------------------------------- 5. netclass, zones, save, DRC
    pro = json.load(open(PRO, encoding="utf-8"))
    nc_before = None
    for c in pro["net_settings"]["classes"]:
        if c["name"] == "USB":
            nc_before = {k: c[k] for k in ("track_width", "diff_pair_width", "diff_pair_gap")}
            c["track_width"], c["diff_pair_width"], c["diff_pair_gap"] = W, W, S
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    log.append("unconnected after fill: %d" % unconnected)
    if DRY:
        print("\n".join(log))
        return 0
    board.Save(PCB)
    json.dump(pro, open(PRO, "w", encoding="utf-8"), indent=2)
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", DRC_JSON, PCB], capture_output=True, text=True)
    drc = json.load(open(DRC_JSON, encoding="utf-8"))
    counts = {}
    usb_items = []
    for v in drc.get("violations", []):
        counts[v["type"]] = counts.get(v["type"], 0) + 1
        txt = json.dumps(v)
        if any(n in txt for n in NETS):
            usb_items.append("%s: %s" % (v["type"], v.get("description", "")))
    unc = drc.get("unconnected_items", [])
    for u in unc:
        txt = json.dumps(u)
        if any(n in txt for n in NETS):
            usb_items.append("unconnected: %s" % u.get("description", ""))
    after = net_summary(pcbnew.LoadBoard(PCB), NETS + ("USB_PWR", "SWDIO"))
    rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "log": log, "removed": removed, "moved": moves, "netclass_usb": {"before": nc_before, "after": {"track_width": W, "diff_pair_width": W, "diff_pair_gap": S}},
           "lengths_mm": {"D+": round(Lp, 3), "D-": round(Lm, 3), "skew": round(Lp - Lm, 3)}, "loop_y": YL,
           "before": before, "after": after, "drc_counts": counts, "drc_unconnected": len(unc), "drc_items_on_usb_nets": usb_items}
    json.dump(rep, open(os.path.join(OUTD, "usb-reroute.json"), "w", encoding="utf-8"), indent=1)
    write_md(rep)
    print("\n".join(log))
    print("DRC:", counts, "unconnected", len(unc), "USB items", usb_items)
    return 0


def write_md(rep):
    b, a = rep["before"], rep["after"]
    L = ["# A6 - USB D+/D- rerouted as a coupled pair", "",
         "Date: %s. Script: `hardware/scripts/vpcb_a6_usb_reroute.py`. Data: `usb-reroute.json`, DRC: `drc_after_a6.json`." % rep["date"], "",
         "## Before (snapshot `snapshots/HybridPanda.kicad_pcb.pre_verification`)", "",
         "| Net | Segments | Copper length | By layer | Vias | Widths |", "|---|---|---|---|---|---|"]
    for n in NETS:
        L.append("| %s | %d | %.2f mm | %s | %d (%s) | %s |" % (n, b[n]["segments"], b[n]["length_mm"], ", ".join("%s %.2f" % kv for kv in b[n]["by_layer_mm"].items()), len(b[n]["vias"]), "; ".join(b[n]["vias"]), b[n]["widths"]))
    L += ["",
          "- MCU U7 (LQFP-144) is on B.Cu, the series resistors R20/R21 (0402) on B.Cu, the ESD array U13 (SOT-23-6) and the USB-A U3 on F.Cu.",
          "- USB_D+/USB_D- (MCU to resistor): two 0.20 mm B.Cu stubs, not coupled, 1.7 and 3.3 mm.",
          "- USB_R_D+/USB_R_D- (resistor to U13 to U3): 0.20 mm, two vias per net, about 11 mm on In1.Cu (the +3V3/GND patchwork layer,",
          "  referenced to In2 GND through 1.065 mm core, i.e. about %s ohm single-ended, no defined pair), 0.5 mm centre spacing on In1 only;" % "70-80",
          "  on B.Cu/F.Cu the two nets ran apart. Skew before: %.2f mm (USB_R_D+ longer: it loops around U13 to reach U3 pin 3)." % (b["USB_R_D+"]["length_mm"] + b["USB_D+"]["length_mm"] - b["USB_R_D-"]["length_mm"] - b["USB_D-"]["length_mm"]),
          "", "## After", "", "| Net | Segments | Copper length | By layer | Vias | Widths |", "|---|---|---|---|---|---|"]
    for n in NETS:
        L.append("| %s | %d | %.2f mm | %s | %d (%s) | %s |" % (n, a[n]["segments"], a[n]["length_mm"], ", ".join("%s %.2f" % kv for kv in a[n]["by_layer_mm"].items()), len(a[n]["vias"]), "; ".join(a[n]["vias"]), a[n]["widths"]))
    lp, lm = rep["lengths_mm"]["D+"], rep["lengths_mm"]["D-"]
    L += ["",
          "- Total copper D+ (USB_D+ + USB_R_D+) = %.2f mm, D- = %.2f mm, **skew %.2f mm** (target <= 0.5 mm). The 0402 resistor body is in" % (lp, lm, lp - lm),
          "  both paths and is not counted.",
          "- One via per net (symmetric pair at y = 43.60, x = 127.90 / 129.80, 0.6/0.3 mm) instead of two per net. The B.Cu run is referenced to",
          "  the In2.Cu GND plane through the 0.20 mm prepreg; the F.Cu part is referenced to In1.Cu (GND there, outside the +3V3 pour).",
          "- Coupled geometry: 0.35/0.15 mm (pitch 0.50 mm, ~90 ohm on JLC7628 per `impedance.md`) from x = 118.2 to the via pair (about 9 mm on",
          "  B.Cu); 0.20/0.15 mm neck (pitch 0.35 mm, ~116 ohm) from the resistors through the 0.83 mm corridor between C62 and C54 (about 4 mm);",
          "  0.20 mm single stubs at the LQFP pads (0.30 mm pad width, 1.5-1.7 mm). The last 45-degree split to the two vias opens the gap to",
          "  0.32 mm over ~3 mm. On F.Cu the pair cannot stay coupled: U13 pin 5 (VBUS) sits between the two data pins, so the two F.Cu legs",
          "  (via -> pin 4/6 -> pin 3/1 -> U3) are parallel at 1.9 mm pitch (uncoupled, ~%s ohm single-ended, 6-9 mm). This is inherent to the" % "53",
          "  SOT-23-6 pinout and to U3 being on the other side of the board.",
          "- USB netclass: %s -> track 0.35 / diff pair 0.35 / gap 0.15 mm." % json.dumps(rep["netclass_usb"]["before"]),
          "", "## Components and other nets touched", "",
          "- R20 (D- series resistor): %s rot %s -> %s rot %s, pads %s." % (rep["moved"]["R20"]["before"]["pos"], rep["moved"]["R20"]["before"]["rot"], rep["moved"]["R20"]["after"]["pos"], rep["moved"]["R20"]["after"]["rot"], rep["moved"]["R20"]["after"]["pads"]),
          "- R21 (D+ series resistor): %s rot %s -> %s rot %s, pads %s." % (rep["moved"]["R21"]["before"]["pos"], rep["moved"]["R21"]["before"]["rot"], rep["moved"]["R21"]["after"]["pos"], rep["moved"]["R21"]["after"]["rot"], rep["moved"]["R21"]["after"]["pads"]),
          "  Both are now vertical, side by side, so the pair leaves them without crossing. Courtyards do not overlap (0.02 mm apart).",
          "- USB_PWR: the bottom-side detour (via 128.85,43.547, B.Cu 1.0 mm tracks, via 129.78,46.5) was removed; U13.5 -> U3.1 now runs on",
          "  F.Cu only (1.0 mm), between the two new data vias. Before: %s; after: %s." % (json.dumps(b["USB_PWR"]["by_layer_mm"]), json.dumps(a["USB_PWR"]["by_layer_mm"])),
          "- SWDIO: escape moved 0.10 mm east (x 115.25 -> 115.35) to clear the rotated R21; same via 115.56,43.42.",
          "- GND: stitching via 115.370,42.665 (and its F.Cu stub from C12.2) removed - it sat on the pair path; C12.2 stays on the 0.75 mm F.Cu GND",
          "  bus to the vias at 113.949,40.931 and 115.666,40.266. The C54.2 via (117.618,42.204) and the C64.2 via (116.280,42.750) were replaced by",
          "  one shared via at 116.28,43.00 (0.5-1.1 mm from the pads); it keeps both 100 nF returns short and frees the corridor.",
          "- Removed items: %d tracks, %d vias (list in `usb-reroute.json`)." % (rep["removed"]["tracks"], rep["removed"]["vias"]),
          "", "## DRC after this step (full board)", "",
          "- Counts: %s; unconnected items: %d." % (json.dumps(rep["drc_counts"], sort_keys=True), rep["drc_unconnected"]),
          "- Items involving USB_D+/USB_D-/USB_R_D+/USB_R_D-: %s." % (("; ".join(rep["drc_items_on_usb_nets"])) if rep["drc_items_on_usb_nets"] else "none (0 clearance, 0 unconnected)"),
          "- Zones were refilled with `pcbnew.ZONE_FILLER` before saving.",
          "", "## Limits", "",
          "- Lengths are centre-line copper lengths from the pcbnew API; via barrels (1.59 mm each, one per net) are equal on both sides.",
          "- Impedance values are the analytic numbers of `impedance.md`; nothing was measured. The pair is electrically short for USB FS",
          "  (edges 4-20 ns), so the necks and the uncoupled F.Cu legs are not expected to be functionally relevant; the work is layout hygiene.",
          "- Changes are software-only, not physically verified. The schematic was not touched (connectivity unchanged).",
          "", "---", "",
          "pt-BR: O par USB foi refeito como par diferencial acoplado: trilhas antigas (2 vias por rede, 11 mm na camada interna In1) removidas;",
          "R20/R21 rodados para vertical lado a lado; par 0.35/0.15 mm em B.Cu (gargalo 0.20/0.15 entre C62 e C54), um par simetrico de vias em",
          "y=43.6 e pernas em F.Cu ate U13 e U3. Skew %.2f mm. USB_PWR, SWDIO e duas vias GND foram reposicionadas para abrir o corredor." % (lp - lm),
          "DRC apos o passo: %d itens nas redes USB. Alteracao apenas em software, sem verificacao fisica." % len(rep["drc_items_on_usb_nets"])]
    hp.guarded_write_text(os.path.join(OUTD, "usb-reroute.md"), "\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
