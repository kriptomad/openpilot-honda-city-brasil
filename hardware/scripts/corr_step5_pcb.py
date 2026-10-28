"""Step 5: MEDIUM items from 06_REPORTS/si_pi_audit/proposed_changes.md, applied one sub-command at a time.

Each sub-command edits the PCB, refills zones, saves, and appends a log entry to 06_REPORTS/corr/step5_pcb.json.
Run the DRC gate (corr_gate.py drc --tag step5x) after every sub-command.

Usage (KiCad 10 python):
  python -u corr_step5_pcb.py inspect                 -> JSON dump of geometry needed to plan the edits
  python -u corr_step5_pcb.py outline                 -> item 33a: right edge +0.4 mm for y < 48.6 (U3 pads 5/6 copper_edge)
  python -u corr_step5_pcb.py thermal                 -> items 15/28: GND zone relief 0.3/0.4, min 0.2, islands < 5 mm2, solid pads
  python -u corr_step5_pcb.py vss [pad ...]           -> item 29: extra GND via at U7 VSS pad 69
  python -u corr_step5_pcb.py can                     -> item 26: CAN tracks 0.15 -> 0.25 mm
  python -u corr_step5_pcb.py can_fix <drc.json> <w>  -> narrow the CAN segments flagged as clearance offenders to <w>
  python -u corr_step5_pcb.py widen 12|13|14          -> items 12/13/14: +5V->U12, USB_PWR, +3V3 near L3
  python -u corr_step5_pcb.py inner17 NET [NET ...]   -> item 17/20: remove <=0.2 mm inner-layer power stubs of NET
  python -u corr_step5_pcb.py p1hole                  -> item 32: P1 shell slots +0.15 mm x (hole-to-hole 0.24 -> 0.39)
  python -u corr_step5_pcb.py vias30 [keep]           -> item 30: 0.5 mm vias -> 0.6 mm (--revert x,y,... to undo)
  python -u corr_step5_pcb.py rules30                 -> item 30: tighter design rules (REJECTED: creates annular_width category)
  python -u corr_step5_pcb.py silk35                  -> item 35: small ref text 0.5 -> 0.8 mm where reasonable
  python -u corr_step5_pcb.py c23c24                  -> item 10: C23/C24 value 15pF -> 18pF (schematic done by corr_step5_sch.py)
  python -u corr_step5_pcb.py u3gnd                   -> item 33b: U3 pads 5/6 to GND (schematic done by corr_step5_sch.py)
"""
import json
import os
import sys

import pcbnew
from pcbnew import FromMM, ToMM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp  # noqa: E402

PCB = os.path.join(str(hp.OUTPUT_ROOT), "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")
LOG = os.path.join(str(hp.REPORT_DIR), "corr", "step5_pcb.json")
CAN_NETS = ["BUS0_H", "BUS0_L", "BUS1N_H", "BUS1N_L", "BUS1O_H", "BUS1O_L", "BUS2_H", "BUS2_L"]


def P(x, y):
    return pcbnew.VECTOR2I(FromMM(x), FromMM(y))


def mm(v):
    return (round(ToMM(v.x), 4), round(ToMM(v.y), 4))


def same(a, b, tol=0.02):
    return abs(ToMM(a.x) - b[0]) < tol and abs(ToMM(a.y) - b[1]) < tol


def log(entry):
    data = {"steps": []}
    if os.path.exists(LOG):
        data = json.load(open(LOG, encoding="utf-8"))
    data["steps"].append(entry)
    json.dump(data, open(LOG, "w", encoding="utf-8"), indent=1)


def save(b, tag):
    hp.backup_before_write(PCB, "step5_" + tag)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
    pcbnew.SaveBoard(PCB, b)
    print("saved (%s)" % tag)


def tracks(b, net=None, layer=None, width=None):
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        if net is not None and t.GetNetname() != net:
            continue
        if layer is not None and t.GetLayer() != layer:
            continue
        if width is not None and abs(ToMM(t.GetWidth()) - width) > 0.001:
            continue
        yield t


def add_track(b, net, a, c, w, layer):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
    return t


def add_via(b, net, pos, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(*pos)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(FromMM(d)); v.SetDrill(FromMM(drill)); v.SetNet(net); b.Add(v)
    return v


def pad(b, ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError((ref, num))


# ----------------------------------------------------------------------------- inspect
def inspect(b):
    out = {"outline": [], "can_widths": {}, "inner_power": [], "u7_vss": [], "small_text": [], "p1": [], "vias": {}}
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_POLY:
            pl = d.GetPolyShape().Outline(0)
            out["outline"] = [(round(ToMM(pl.CPoint(i).x), 4), round(ToMM(pl.CPoint(i).y), 4)) for i in range(pl.PointCount()) if ToMM(pl.CPoint(i).x) > 139]
    for n in CAN_NETS:
        for t in tracks(b, n):
            w = round(ToMM(t.GetWidth()), 3)
            out["can_widths"][w] = out["can_widths"].get(w, 0) + 1
    for n in ("+12V", "12V_Protected", "+5V", "VCAP", "+3V3"):
        for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            for t in tracks(b, n, lay):
                out["inner_power"].append((n, b.GetLayerName(lay), mm(t.GetStart()), mm(t.GetEnd()), round(ToMM(t.GetWidth()), 3)))
    u7 = b.FindFootprintByReference("U7")
    for p in u7.Pads():
        if p.GetNetname() == "GND":
            out["u7_vss"].append((p.GetNumber(), mm(p.GetPosition())))
    for fp in b.GetFootprints():
        for it in (fp.Reference(), fp.Value()):
            h = ToMM(it.GetTextHeight())
            if h < 0.8:
                out["small_text"].append((fp.GetReference(), it.GetText(), round(h, 3), round(ToMM(it.GetTextThickness()), 3), it.IsVisible()))
    for p in b.FindFootprintByReference("P1").Pads():
        sz = p.GetSize(pcbnew.PADSTACK.ALL_LAYERS); dr = p.GetDrillSize()
        out["p1"].append((p.GetNumber(), mm(p.GetPosition()), (round(ToMM(sz.x), 3), round(ToMM(sz.y), 3)), (round(ToMM(dr.x), 3), round(ToMM(dr.y), 3))))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            k = "%.2f/%.2f" % (ToMM(t.GetWidth(pcbnew.F_Cu)), ToMM(t.GetDrill()))
            out["vias"][k] = out["vias"].get(k, 0) + 1
    print(json.dumps(out, indent=1, default=str))


# ----------------------------------------------------------------------------- outline (item 33a)
def outline(b, dx=0.4, ystep=48.6):
    """Item 33a: extend the right edge by dx for y < ystep (U3 USB pads 5/6 were 0.095 mm from the edge)."""
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_POLY:
            pl = d.GetPolyShape().Outline(0)
            pts = [(pl.CPoint(i).x, pl.CPoint(i).y) for i in range(pl.PointCount())]
            if any(abs(ToMM(x) - 142.885) < 0.01 for x, y in pts):
                print("already extended"); return
            new = pcbnew.SHAPE_POLY_SET()
            new.NewOutline()
            moved = 0
            for x, y in pts:
                # right edge / top-right arc (x > 141.4) above the step: shift by dx
                if ToMM(x) > 141.4 and ToMM(y) < ystep:
                    new.Append(x + FromMM(dx), y); moved += 1
                    if abs(ToMM(y) - 33.06) < 0.01 and abs(ToMM(x) - 142.485) < 0.01:
                        new.Append(x + FromMM(dx), FromMM(ystep))
                        new.Append(x, FromMM(ystep))
                else:
                    new.Append(x, y)
            d.SetPolyShape(new)
            bb = d.GetBoundingBox()
            print("outline: %d points moved by +%.2f mm (y<%.1f); bbox (%.3f,%.3f)-(%.3f,%.3f)" % (moved, dx, ystep, ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
            log({"step": "outline", "dx": dx, "ystep": ystep, "moved_points": moved})
            save(b, "outline")
            return


# ----------------------------------------------------------------------------- thermal (items 15/28)
SOLID_PADS = [("U6", "9"), ("P1", "0"), ("P1", "A1"), ("P1", "A12"), ("P1", "B1"), ("P1", "B12"),
              ("D5", "3"), ("D6", "3"), ("D7", "3"), ("D8", "3"), ("D9", "3"),
              ("C28", "2"), ("U9", "2"), ("U7", "104"), ("U3", "5"), ("U3", "6"),
              ("C39", "2"), ("C40", "2"), ("C41", "2"), ("C42", "2"), ("C44", "2"), ("C46", "2"), ("C52", "2")]


def thermal(b):
    n = 0
    for z in b.Zones():
        if z.GetNetname() != "GND":
            continue
        z.SetThermalReliefGap(FromMM(0.3)); z.SetThermalReliefSpokeWidth(FromMM(0.4)); z.SetMinThickness(FromMM(0.2))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA); z.SetMinIslandArea(int(FromMM(5.0) * FromMM(1.0)))
        n += 1
    m = 0
    for ref, num in SOLID_PADS:
        fp = b.FindFootprintByReference(ref)
        for p in fp.Pads():
            if p.GetNumber() == num and p.GetNetname() == "GND":
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); m += 1
    print("zones %d, solid pads %d" % (n, m))
    log({"step": "thermal", "zones": n, "solid_pads": m})
    save(b, "thermal")


# ----------------------------------------------------------------------------- vss (item 29)
VSS = [("69", (97.4, 49.2))]  # pads 6 and 89 already have GND vias at 1.2/1.3 mm; pad 104 has no room (C64/pad 105)


def vss(b, only=None):
    gnd = b.FindNet("GND")
    done = []
    for num, vpos in VSS:
        if only and num not in only:
            continue
        p = pad(b, "U7", num)
        pp = mm(p.GetPosition())
        add_track(b, gnd, pp, vpos, 0.25, pcbnew.B_Cu)
        add_via(b, gnd, vpos)
        done.append((num, pp, vpos))
    print(done)
    log({"step": "vss", "added": done})
    save(b, "vss")


def vss_revert(b):
    """Undo vss(): the via at (97.4,49.2) lands inside U12.6 (F.Cu, same net) -> via-in-pad; U12 sits on the
    opposite side of U7.69 so there is no free via spot within 1.5 mm. Item 29 for pad 69 is deferred."""
    n = 0
    for num, vpos in VSS:
        pp = mm(pad(b, "U7", num).GetPosition())
        for t in list(b.GetTracks()):
            if t.GetClass() == "PCB_VIA" and same(t.GetPosition(), vpos):
                b.Remove(t); n += 1
            elif t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.B_Cu and \
                    ((same(t.GetStart(), pp) and same(t.GetEnd(), vpos)) or (same(t.GetStart(), vpos) and same(t.GetEnd(), pp))):
                b.Remove(t); n += 1
    print("vss reverted: %d items removed" % n)
    log({"step": "vss_revert", "n": n})
    save(b, "vss_revert")


# ----------------------------------------------------------------------------- u6ep (item 15)
# Positions sit in the gaps between the 0.6 mm paste squares of the U6 (TPS5450 DDA) exposed pad.
# The lower row (y >= 43.1) is excluded: SWDIO runs on In2.Cu at y ~43.56 under the EP (shorting_items).
U6EP = [(107.41, 40.84), (108.71, 40.84), (107.41, 42.14), (108.71, 42.14), (108.06, 41.2)]


def u6ep(b, revert=False):
    gnd = b.FindNet("GND")
    # U6 has 9 pads numbered "9" (EP + 8 paste squares); take the copper EP (largest)
    p = max((q for q in b.FindFootprintByReference("U6").Pads() if q.GetNumber() == "9"), key=lambda q: q.GetSize().x * q.GetSize().y)
    if revert:
        n = 0
        for t in list(b.GetTracks()):
            if t.GetClass() == "PCB_VIA" and any(same(t.GetPosition(), q) for q in U6EP):
                b.Remove(t); n += 1
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_INHERITED)
        print("u6ep reverted %d" % n); log({"step": "u6ep_revert", "n": n}); save(b, "u6ep_revert"); return
    bb = p.GetBoundingBox()
    added = []
    for q in U6EP:
        if not bb.Contains(P(*q)):
            print("skip outside EP", q); continue
        add_via(b, gnd, q, 0.6, 0.3); added.append(q)
    p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    print("u6ep vias", len(added))
    log({"step": "u6ep", "added": added})
    save(b, "u6ep")


# ----------------------------------------------------------------------------- can (item 26)
def can(b, revert=None):
    n = 0
    if revert:
        for t in list(tracks(b)):
            if t.GetNetname() in CAN_NETS and any(same(t.GetStart(), r) or same(t.GetEnd(), r) for r in revert):
                t.SetWidth(FromMM(0.15)); n += 1
        print("reverted %d" % n); log({"step": "can_revert", "n": n, "points": revert}); save(b, "can_revert"); return
    for net in CAN_NETS:
        for t in list(tracks(b, net, width=0.15)):
            t.SetWidth(FromMM(0.25)); n += 1
    print("widened %d CAN segments to 0.25" % n)
    log({"step": "can", "n": n})
    save(b, "can")


def can_fix(b, drc_json, to_width):
    """Narrow the CAN segments flagged as clearance offenders in drc_json down to to_width."""
    import re
    data = json.load(open(drc_json, encoding="utf-8"))
    n = 0
    for v in data["violations"]:
        if v["type"] != "clearance":
            continue
        for it in v["items"]:
            m = re.match(r"Track \[(\S+)\] on (\S+), length ([\d,\.]+) mm", it["description"])
            if not m or m.group(1) not in CAN_NETS:
                continue
            net, ln = m.group(1), float(m.group(3).replace(",", "."))
            pos = (it["pos"]["x"], it["pos"]["y"])
            for t in tracks(b, net):
                if ToMM(t.GetWidth()) <= to_width + 0.001:
                    continue
                if (same(t.GetStart(), pos) or same(t.GetEnd(), pos)) and abs(ToMM(t.GetLength()) - ln) < 0.02:
                    t.SetWidth(FromMM(to_width)); n += 1
    print("can_fix: %d segments -> %.2f" % (n, to_width))
    log({"step": "can_fix", "n": n, "width": to_width, "src": os.path.basename(drc_json)})
    save(b, "can_fix")


# ----------------------------------------------------------------------------- widen (items 12/13/14)
def widen(b, spec):
    """spec: list of (net, layer, width_from(None=any), width_to, bbox(x0,y0,x1,y1))"""
    changed = []
    for net, layer, wfrom, wto, bb in spec:
        for t in tracks(b, net, layer):
            s, e = mm(t.GetStart()), mm(t.GetEnd())
            inside = all(bb[0] - 0.01 <= q[0] <= bb[2] + 0.01 and bb[1] - 0.01 <= q[1] <= bb[3] + 0.01 for q in (s, e))
            if inside and (wfrom is None or abs(ToMM(t.GetWidth()) - wfrom) < 0.001) and ToMM(t.GetWidth()) < wto:
                changed.append((net, b.GetLayerName(layer), s, e, round(ToMM(t.GetWidth()), 2), wto)); t.SetWidth(FromMM(wto))
    for c in changed:
        print(c)
    return changed


WIDEN_12 = [("+5V", pcbnew.F_Cu, None, 0.5, (99.0, 43.5, 113.0, 47.0))]
WIDEN_13 = [("USB_PWR", pcbnew.F_Cu, None, 1.0, (117.0, 40.0, 133.0, 54.0)), ("USB_PWR", pcbnew.B_Cu, None, 1.0, (117.0, 40.0, 133.0, 54.0))]
WIDEN_14 = [("+3V3", pcbnew.F_Cu, None, 0.4, (92.0, 34.0, 99.0, 46.0))]


def widen_cmd(b, which, wto=None):
    spec = {"12": WIDEN_12, "13": WIDEN_13, "14": WIDEN_14}[which]
    if wto is not None:
        spec = [(n, l, wf, wto, bb) for n, l, wf, _w, bb in spec]
    ch = widen(b, spec)
    log({"step": "widen" + which, "changed": ch})
    save(b, "widen" + which)


def widen_fix(b, drc_json, to_width, nets):
    """Set the segments of `nets` flagged as clearance offenders in drc_json to to_width (undo helper for widen)."""
    import re
    data = json.load(open(drc_json, encoding="utf-8"))
    n = 0
    for v in data["violations"]:
        if v["type"] not in ("clearance", "shorting_items", "solder_mask_bridge", "hole_clearance"):
            continue
        for it in v["items"]:
            m = re.match(r"Track \[(\S+)\] on (\S+), length ([\d,\.]+) mm", it["description"])
            if not m or m.group(1) not in nets:
                continue
            net, ln = m.group(1), float(m.group(3).replace(",", "."))
            pos = (it["pos"]["x"], it["pos"]["y"])
            for t in tracks(b, net):
                if abs(ToMM(t.GetWidth()) - to_width) < 0.001:
                    continue
                if (same(t.GetStart(), pos) or same(t.GetEnd(), pos)) and abs(ToMM(t.GetLength()) - ln) < 0.02:
                    t.SetWidth(FromMM(to_width)); n += 1
    print("widen_fix: %d segments -> %.2f" % (n, to_width))
    log({"step": "widen_fix", "n": n, "width": to_width, "nets": nets, "src": os.path.basename(drc_json)})
    save(b, "widen_fix")


# ----------------------------------------------------------------------------- inner17 (items 17/20)
def inner17(b, nets):
    removed = []
    victims = []
    for n in nets:
        for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            for t in tracks(b, n, lay):
                if ToMM(t.GetWidth()) <= 0.21:
                    victims.append(t)
    for t in victims:
        removed.append((t.GetNetname(), b.GetLayerName(t.GetLayer()), mm(t.GetStart()), mm(t.GetEnd())))
    for t in victims:
        b.Remove(t)
    print("removed %d inner tracks" % len(removed))
    for r in removed:
        print(r)
    log({"step": "inner17", "removed": removed})
    save(b, "inner17")


def inner17_restore(b, net, layer_name, width=0.2):
    """Re-add the segments of net/layer removed by the last inner17 run (optionally at a wider width)."""
    data = json.load(open(LOG, encoding="utf-8"))
    entry = [s for s in data["steps"] if s["step"] == "inner17"][-1]
    lay = b.GetLayerID(layer_name)
    n = 0
    for nn, ln, s, e in entry["removed"]:
        if nn == net and ln == layer_name:
            add_track(b, b.FindNet(net), tuple(s), tuple(e), width, lay); n += 1
    print("restored %d %s segments on %s at %.2f" % (n, net, layer_name, width))
    log({"step": "inner17_restore", "net": net, "layer": layer_name, "width": width, "n": n})
    save(b, "inner17_restore")


# ----------------------------------------------------------------------------- p1hole (item 32)
def p1hole(b, dx=0.15):
    """REJECTED: +0.15 mm clears the NPTH hole (hole_clearance 8 -> 0) but shorts the shell pad into
    BUS0_H (F.Cu, x=137.18) and SBU2 (In1, x=137.23). Run with dx=-0.15 to undo."""
    moved = []
    x0 = 136.18 if dx > 0 else 136.18 - dx
    for p in b.FindFootprintByReference("P1").Pads():
        if p.GetNumber() == "0" and abs(ToMM(p.GetPosition().x) - x0) < 0.05:
            pos = p.GetPosition(); p.SetPosition(pcbnew.VECTOR2I(pos.x + FromMM(dx), pos.y)); moved.append(mm(p.GetPosition()))
    print("P1 shell slots moved:", moved)
    log({"step": "p1hole", "dx": dx, "moved": moved})
    save(b, "p1hole")


# ----------------------------------------------------------------------------- vias30 / rules30 (item 30)
def vias30(b, keep=0.5):
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and abs(ToMM(t.GetWidth(pcbnew.F_Cu)) - keep) < 0.001:
            t.SetWidth(FromMM(0.6)); n += 1
    print("vias %.2f -> 0.60: %d" % (keep, n))
    log({"step": "vias30", "n": n})
    save(b, "vias30")


def vias30_revert(b, pts):
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and any(same(t.GetPosition(), p) for p in pts):
            t.SetWidth(FromMM(0.5)); n += 1
    print("vias reverted to 0.50: %d" % n)
    log({"step": "vias30_revert", "n": n, "points": pts})
    save(b, "vias30_revert")


def drillfix(b, pos=(104.125, 50.945), d=0.6, drill=0.3):
    """Item 30b: the single 0.45/0.25 via (drill_out_of_range) -> standard d/drill."""
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and same(t.GetPosition(), pos):
            t.SetWidth(FromMM(d)); t.SetDrill(FromMM(drill)); n += 1
    print("via at %s -> %.2f/%.2f (%d)" % (pos, d, drill, n))
    log({"step": "drillfix", "pos": pos, "d": d, "drill": drill, "n": n})
    save(b, "drillfix")


def stitch(b, regions=((130.5, 33.0, 142.0, 50.0), (130.5, 64.0, 142.0, 78.0), (104.0, 33.0, 118.0, 42.0)),
           step=1.5, keepout=0.65, d=0.6, drill=0.3):
    """Item 31: GND stitching vias where the nearest GND via is > 5 mm, on a coarse grid, only where no
    copper item (track/via/pad, any layer) is within `keepout` of the via centre and the point is > 1 mm from the edge."""
    import math
    gnd = b.FindNet("GND")
    gnd_vias = [mm(t.GetPosition()) for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    items = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            items.append(("v", mm(t.GetPosition()), ToMM(t.GetWidth(pcbnew.F_Cu)) / 2, t.GetNetname()))
        else:
            items.append(("t", (mm(t.GetStart()), mm(t.GetEnd())), ToMM(t.GetWidth()) / 2, t.GetNetname()))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            items.append(("p", (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())), 0, p.GetNetname()))
    edge = b.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = ToMM(edge.GetLeft()), ToMM(edge.GetTop()), ToMM(edge.GetRight()), ToMM(edge.GetBottom())

    def seg_dist(p, a, c):
        ax, ay = a; cx, cy = c; px, py = p
        dx, dy = cx - ax, cy - ay
        if dx == dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def free(pt):
        for kind, g, r, net in items:
            if kind == "v" and math.hypot(pt[0] - g[0], pt[1] - g[1]) < r + keepout:
                return False
            if kind == "t" and seg_dist(pt, g[0], g[1]) < r + keepout:
                return False
            if kind == "p" and g[0] - keepout < pt[0] < g[2] + keepout and g[1] - keepout < pt[1] < g[3] + keepout:
                return False
        return True

    added = []
    for x0, y0, x1, y1 in regions:
        y = y0
        while y <= y1:
            x = x0
            while x <= x1:
                pt = (round(x, 3), round(y, 3))
                inside = ex0 + 1.0 < pt[0] < ex1 - 1.0 and ey0 + 1.0 < pt[1] < ey1 - 1.0
                if pt[0] > 142.0 and pt[1] > 48.6:
                    inside = False
                if inside and free(pt):
                    near = min([math.hypot(pt[0] - g[0], pt[1] - g[1]) for g in gnd_vias + added] or [99])
                    if near > 3.0:
                        add_via(b, gnd, pt, d, drill); added.append(pt)
                x += step
            y += step
    print("stitch vias added: %d -> %s" % (len(added), added))
    log({"step": "stitch", "added": added})
    save(b, "stitch")


def stitch_revert(b, pts):
    n = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND" and any(same(t.GetPosition(), p) for p in pts):
            b.Remove(t); n += 1
    print("stitch vias removed: %d" % n)
    log({"step": "stitch_revert", "n": n, "points": pts})
    save(b, "stitch_revert")


def rules30(b, ann=0.13, clr=0.1, trk=0.127):
    ds = b.GetDesignSettings()
    ds.m_ViasMinAnnularWidth = FromMM(ann); ds.m_MinClearance = FromMM(clr); ds.m_TrackMinWidth = FromMM(trk)
    print("rules: annular %.3f clearance %.3f track %.4f" % (ann, clr, trk))
    log({"step": "rules30", "ann": ann, "clr": clr, "trk": trk})
    save(b, "rules30")


# ----------------------------------------------------------------------------- silk35 (item 35)
def silk35(b, h=0.8, th=0.12, skip=("Q1", "Q2", "L4")):
    n = 0
    for fp in b.GetFootprints():
        r = fp.Reference()
        if fp.GetReference() in skip or not r.IsVisible():
            continue
        if ToMM(r.GetTextHeight()) < h and r.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            r.SetTextSize(pcbnew.VECTOR2I(FromMM(h), FromMM(h))); r.SetTextThickness(FromMM(th)); n += 1
    print("ref texts enlarged to %.2f: %d" % (h, n))
    log({"step": "silk35", "n": n, "h": h})
    save(b, "silk35")


def silk35_revert(b, drc_json, h=0.5, th=0.1):
    """Shrink back the reference fields that silk35 made collide (silk_overlap / silk_over_copper in drc_json)."""
    import re
    data = json.load(open(drc_json, encoding="utf-8"))
    refs = set()
    for v in data["violations"]:
        if v["type"] in ("silk_overlap", "silk_over_copper"):
            for it in v["items"]:
                m = re.match(r"Reference field of (\S+)", it["description"])
                if m:
                    refs.add(m.group(1))
    n = 0
    for fp in b.GetFootprints():
        if fp.GetReference() in refs:
            r = fp.Reference(); r.SetTextSize(pcbnew.VECTOR2I(FromMM(h), FromMM(h))); r.SetTextThickness(FromMM(th)); n += 1
    print("ref texts reverted to %.2f: %d -> %s" % (h, n, sorted(refs)))
    log({"step": "silk35_revert", "n": n, "refs": sorted(refs)})
    save(b, "silk35_revert")


# ----------------------------------------------------------------------------- c23c24 (item 10) / u3gnd (item 33b)
def c23c24(b, val="18pF"):
    for ref in ("C23", "C24"):
        b.FindFootprintByReference(ref).SetValue(val)
    print("C23/C24 value ->", val)
    log({"step": "c23c24", "value": val})
    save(b, "c23c24")


def u3gnd(b):
    gnd = b.FindNet("GND")
    for num in ("5", "6"):
        p = pad(b, "U3", num); p.SetNet(gnd)
    print("U3 pads 5/6 -> GND")
    log({"step": "u3gnd"})
    save(b, "u3gnd")


def parse_pts(s):
    v = [float(x) for x in s.split(",")]
    return [(v[i], v[i + 1]) for i in range(0, len(v), 2)]


def main():
    cmd = sys.argv[1]
    b = pcbnew.LoadBoard(PCB)
    a = sys.argv[2:]
    if cmd == "inspect":
        inspect(b)
    elif cmd == "outline":
        outline(b)
    elif cmd == "thermal":
        thermal(b)
    elif cmd == "u6ep":
        u6ep(b, revert=bool(a and a[0] == "--revert"))
    elif cmd == "vss":
        if a and a[0] == "--revert":
            vss_revert(b)
        else:
            vss(b, a or None)
    elif cmd == "can":
        can(b, parse_pts(a[1]) if a and a[0] == "--revert" else None)
    elif cmd == "can_fix":
        can_fix(b, a[0], float(a[1]))
    elif cmd == "widen":
        widen_cmd(b, a[0], float(a[1]) if len(a) > 1 else None)
    elif cmd == "widen_fix":
        widen_fix(b, a[0], float(a[1]), a[2:])
    elif cmd == "inner17":
        inner17(b, a)
    elif cmd == "inner17_restore":
        inner17_restore(b, a[0], a[1], float(a[2]) if len(a) > 2 else 0.2)
    elif cmd == "p1hole":
        p1hole(b, float(a[0]) if a else 0.15)
    elif cmd == "vias30":
        if a and a[0] == "--revert":
            vias30_revert(b, parse_pts(a[1]))
        else:
            vias30(b)
    elif cmd == "rules30":
        rules30(b, *[float(x) for x in a])
    elif cmd == "drillfix":
        drillfix(b, d=float(a[0]) if a else 0.6, drill=float(a[1]) if len(a) > 1 else 0.3)
    elif cmd == "stitch":
        if a and a[0] == "--revert":
            stitch_revert(b, parse_pts(a[1]))
        else:
            stitch(b)
    elif cmd == "silk35":
        silk35(b)
    elif cmd == "silk35_revert":
        silk35_revert(b, a[0])
    elif cmd == "c23c24":
        c23c24(b)
    elif cmd == "u3gnd":
        u3gnd(b)
    else:
        print("unknown command", cmd)
    sys.stdout.flush(); os._exit(0)


if __name__ == "__main__":
    main()
