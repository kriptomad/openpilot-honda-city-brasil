"""vpcb_a8_drc_cleanup.py - A8 of the PCB engineering pass: inherited DRC cleanup of HybridPanda.kicad_pcb.

Autor: Bruno Costa

What it does (all through the pcbnew API, then zone refill, save, kicad-cli DRC):
  1. P1 (HRO TYPE-C-31-M-04, local footprint USB-C-SMD_TYPE-C-USB-20): the two 0.8 mm locating-peg NPTH holes are
     0.144 mm from the copper of the shell slot pads (rule 0.25 mm, JLCPCB hole-to-copper 0.254 mm). The HRO TYPE-C-31
     family drawing (and the KiCad / ai03 library footprints of the same family) use a 0.65 mm peg hole, so the NPTH is
     set to 0.65 mm and the four slot pads are shortened 1.6 -> 1.5 mm along the slot axis (ring 0.15 mm at the slot
     ends, 0.2 mm at the sides). Same edit applied to HybridPanda.pretty/USB-C-SMD_TYPE-C-USB-20.kicad_mod.
  2. Silk outline segments of U3 and P1 that lie outside the board edge (x > 142.935) are clipped to x <= 142.60.
  3. The P1 silk segment crossing R1 pad 1 is split around the pad.
  4. Visible reference fields with height < 0.8 mm are set to 0.8 x 0.8 mm / 0.15 mm (JLC silk minimum); references
     already 0.8 mm high get 0.15 mm thickness. Then every reference that collides with silk, pads or the edge is moved
     to the nearest free spot around its footprint; if none exists it is hidden and listed.
  5. Repeats DRC up to 5 times using the real kicad-cli report to catch what the local collision model misses.

Usage: python vpcb_a8_drc_cleanup.py [--dry]
"""
import json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I

ROOT = hp.OUTPUT_ROOT
PCB = str(ROOT / "hardware/hybrid-panda/HybridPanda.kicad_pcb")
MOD = str(ROOT / "hardware/hybrid-panda/HybridPanda.pretty/USB-C-SMD_TYPE-C-USB-20.kicad_mod")
OUTD = ROOT / "hardware/reports/verification-pcb"
DRY = "--dry" in sys.argv
MOD_U3 = str(ROOT / "hardware/hybrid-panda/HybridPanda.pretty/USB-A-TH_10.0QHHTZB6.3.kicad_mod")
# Board outline (Edge.Cuts polygon): right edge x = 142.885 for y < 48.6, x = 142.485 below; top-right corner is an arc
# R = 1.0 centred at (141.885, 33.06). Silk must stay 0.2 mm (edge clearance) + half line width (0.125) away.
EDGE_LIMITS = {"U3_top": 142.10, "U3_bottom": 142.51, "P1": 142.11}
TXT_H, TXT_T = 0.8, 0.15


def run_drc(tag):
    out = str(OUTD / ("drc_%s.json" % tag))
    subprocess.run([hp.KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", out, PCB],
                   capture_output=True, text=True)
    d = json.load(open(out, encoding="utf-8"))
    viol = d.get("violations", []) + d.get("unconnected_items", []) + d.get("schematic_parity", [])
    by = {}
    for v in viol: by[v["type"]] = by.get(v["type"], 0) + 1
    return by, viol


def fp_by_ref(board, ref):
    return [f for f in board.GetFootprints() if f.GetReference() == ref][0]


def rect_shape(bb, grow=0):
    return pcbnew.SHAPE_RECT(bb.GetLeft() - grow, bb.GetTop() - grow, bb.GetWidth() + 2 * grow, bb.GetHeight() + 2 * grow)


class SilkIndex:
    """Obstacles for a silkscreen text on one side: other silk graphics/texts, pads (mask openings), board edge box."""

    def __init__(self, board, front):
        self.silk = pcbnew.F_SilkS if front else pcbnew.B_SilkS
        self.cu = pcbnew.F_Cu if front else pcbnew.B_Cu
        self.items = []
        for fp in board.GetFootprints():
            for g in fp.GraphicalItems():
                if g.GetLayer() == self.silk:
                    self.items.append((g.GetEffectiveShape(self.silk), "silk %s" % fp.GetReference()))
            for t in (fp.Reference(), fp.Value()):
                if t.IsVisible() and t.GetLayer() == self.silk:
                    self.items.append((rect_shape(t.GetBoundingBox()), "text %s" % fp.GetReference(), t))
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    self.items.append((p.GetEffectiveHoleShape(), "hole %s" % fp.GetReference()))
                elif p.IsOnLayer(self.cu):
                    self.items.append((p.GetEffectiveShape(self.cu), "pad %s.%s" % (fp.GetReference(), p.GetNumber())))
        for d in board.GetDrawings():
            if d.GetLayer() == self.silk:
                self.items.append((d.GetEffectiveShape(self.silk), "drawing"))
        bb = board.GetBoardEdgesBoundingBox()
        self.edge = (bb.GetLeft() + FromMM(0.35), bb.GetTop() + FromMM(0.35), bb.GetRight() - FromMM(0.35), bb.GetBottom() - FromMM(0.35))

    def hits(self, text, clr_mm=0.06):
        bb = text.GetBoundingBox()
        if bb.GetLeft() < self.edge[0] or bb.GetTop() < self.edge[1] or bb.GetRight() > self.edge[2] or bb.GetBottom() > self.edge[3]:
            return ["edge"]
        r = rect_shape(bb)
        own = "text %s" % text.GetParentFootprint().GetReference()   # SWIG wrappers are not identical objects: compare by tag
        out = []
        for it in self.items:
            if len(it) == 3 and it[1] == own: continue
            if r.Collide(it[0], FromMM(clr_mm)): out.append(it[1])
        return out

    def refresh_text(self, text, ref):
        self.items = [it for it in self.items if not (len(it) == 3 and it[1] == "text %s" % ref)]
        self.items.append((rect_shape(text.GetBoundingBox()), "text %s" % ref, text))


def pads_bbox(fp):
    bb = None
    for p in fp.Pads():
        b = p.GetBoundingBox()
        if bb is None: bb = pcbnew.BOX2I(b.GetPosition(), b.GetSize())
        else: bb.Merge(b)
    return bb if bb is not None else fp.GetBoundingBox(False, False)


def relocate(board, idx, fp, log, max_extra_mm=1.6):
    """Place the reference at the nearest free spot: centre of the pad box first (large parts), then a ring around the
    pad box, never farther than half-diagonal + max_extra_mm from the part centre. Returns 'kept'/'moved'/'hidden'."""
    t = fp.Reference()
    if not idx.hits(t): return "kept"
    body = pads_bbox(fp)
    cx, cy = body.GetCenter().x, body.GetCenter().y
    hw, hh = body.GetWidth() / 2, body.GetHeight() / 2
    limit = (hw ** 2 + hh ** 2) ** 0.5 + FromMM(max_extra_mm)
    orig_pos, orig_ang = VECTOR2I(t.GetPosition()), t.GetTextAngleDegrees()
    cands = []
    for ang in (orig_ang, (orig_ang + 90) % 180):
        t.SetTextAngleDegrees(ang)
        tb = t.GetBoundingBox(); tw, th = tb.GetWidth() / 2, tb.GetHeight() / 2
        cands.append((0, cx, cy, ang))
        import math
        for k in range(0, 12):
            step = FromMM(0.10 * k + 0.12)
            for i in range(16):
                a = math.pi * i / 8
                x = cx + math.cos(a) * (hw + tw + step); y = cy + math.sin(a) * (hh + th + step)
                for (xx, yy) in ((x, y), (cx + math.cos(a) * (hw + tw + step), cy), (cx, cy + math.sin(a) * (hh + th + step))):
                    d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                    if d <= limit: cands.append((d, xx, yy, ang))
    cands.sort(key=lambda c: (c[0], c[3] != orig_ang))
    for d, x, y, ang in cands:
        t.SetTextAngleDegrees(ang); t.SetPosition(VECTOR2I(int(x), int(y)))
        if not idx.hits(t):
            idx.refresh_text(t, fp.GetReference())
            log.append({"ref": fp.GetReference(), "action": "moved", "from": [ToMM(orig_pos.x), ToMM(orig_pos.y)], "to": [ToMM(int(x)), ToMM(int(y))], "angle": ang,
                        "dist_mm": round(ToMM(int(((x - orig_pos.x) ** 2 + (y - orig_pos.y) ** 2) ** 0.5)), 2)})
            return "moved"
    t.SetTextAngleDegrees(orig_ang); t.SetPosition(orig_pos); t.SetVisible(False)
    idx.items = [it for it in idx.items if not (len(it) == 3 and it[1] == "text %s" % fp.GetReference())]
    log.append({"ref": fp.GetReference(), "action": "hidden", "from": [ToMM(orig_pos.x), ToMM(orig_pos.y)]})
    return "hidden"

def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": DRY, "steps": {}}
    bp = OUTD / "drc_a8_before.json"
    if bp.exists():   # keep the pre-A8 baseline when the script is re-run
        d0 = json.load(open(bp, encoding="utf-8")); before = {}
        for v in d0.get("violations", []) + d0.get("unconnected_items", []): before[v["type"]] = before.get(v["type"], 0) + 1
    else:
        before, _ = run_drc("a8_before")
    rep["drc_before"] = before
    board = pcbnew.LoadBoard(PCB)

    # 1. P1 peg holes / slot pads --------------------------------------------------------------------------------
    p1 = fp_by_ref(board, "P1"); s1 = []
    for p in p1.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and abs(ToMM(p.GetDrillSize().x) - 0.8) < 1e-3:
            p.SetDrillSize(VECTOR2I(FromMM(0.65), FromMM(0.65))); p.SetSize(p.GetLayer(), VECTOR2I(FromMM(0.65), FromMM(0.65)))
            s1.append("NPTH @ %.3f,%.3f drill 0.80 -> 0.65" % (ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)))
        elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillShape() == pcbnew.PAD_DRILL_SHAPE_OBLONG and p.GetNumber() == "0":
            p.SetSize(p.GetLayer(), VECTOR2I(FromMM(1.0), FromMM(1.5)))
            s1.append("slot pad @ %.3f,%.3f copper 1.0x1.6 -> 1.0x1.5 (drill 0.6x1.2 kept)" % (ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)))
    rep["steps"]["p1_pads"] = s1
    if not DRY:
        txt = open(MOD, encoding="utf-8").read()
        txt2 = txt.replace("(size 0.8 0.8) (drill 0.8)", "(size 0.65 0.65) (drill 0.65)").replace("(size 1 1.6) (drill oval 0.6 1.19", "(size 1 1.5) (drill oval 0.6 1.19")
        if txt2 != txt: open(MOD, "w", encoding="utf-8", newline="\n").write(txt2); rep["steps"]["p1_kicad_mod"] = "updated (same pad edits)"

    # 2. silk outside the board edge (U3, P1) -------------------------------------------------------------------
    s2, to_remove = [], []   # removals deferred: FOOTPRINT.Remove() breaks later GetFootprints() iteration in this API build
    for ref in ("U3", "P1"):
        fp = fp_by_ref(board, ref)
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() != "PCB_SHAPE" or g.GetShape() != pcbnew.SHAPE_T_SEGMENT: continue
            a, b = g.GetStart(), g.GetEnd()
            ax, bx = ToMM(a.x), ToMM(b.x)
            lim = EDGE_LIMITS["P1"] if ref == "P1" else (EDGE_LIMITS["U3_top"] if ToMM(a.y) < 40 else EDGE_LIMITS["U3_bottom"])
            if ax <= lim + 1e-6 and bx <= lim + 1e-6: continue
            if ax > lim and bx > lim:
                to_remove.append((fp, g)); s2.append("%s: removed segment x=%.3f (outside edge)" % (ref, ax)); continue
            if ax > lim: g.SetStart(VECTOR2I(FromMM(lim), a.y))
            else: g.SetEnd(VECTOR2I(FromMM(lim), b.y))
            s2.append("%s: clipped segment y=%.3f to x<=%.2f" % (ref, ToMM(a.y), lim))
    if not DRY:
        # same edits in the library footprints (footprint frame: board_x = cx + local_y for the 90 deg rotation).
        # U3 cx = 136.445: 142.10 -> 5.655, 142.51 -> 6.065 ; P1 cx = 137.485: 142.11 -> 4.625.
        for path, edits in ((MOD_U3, [("(fp_line (start 7.366015 -3.047981) (end 7.366015 7.11204)", "(fp_line (start 7.366015 -3.047981) (end 7.366015 5.655)"),
                                      ("  (fp_line (start 7.366015 7.11204) (end -7.366015 7.11204) (layer F.SilkS) (width 0.254001))\n", ""),
                                      ("(fp_line (start -7.366015 7.11204) (end -7.366015 -3.047981)", "(fp_line (start -7.366015 6.065) (end -7.366015 -3.047981)")]),
                            (MOD, [("  (fp_line (start 4.5 5.622022) (end -4.5 5.622022) (layer F.SilkS) (width 0.254001))\n", ""),
                                   ("(fp_line (start -4.5 5.622022) (end -4.5 4.136119)", "(fp_line (start -4.5 4.625) (end -4.5 4.136119)"),
                                   ("(fp_line (start 4.5 5.622022) (end 4.5 4.136119)", "(fp_line (start 4.5 4.625) (end 4.5 4.136119)")])):
            txt = open(path, encoding="utf-8").read(); t2 = txt; n = 0
            for o, nw in edits:
                if o in t2: t2 = t2.replace(o, nw); n += 1
            if t2 != txt: open(path, "w", encoding="utf-8", newline="\n").write(t2)
            s2.append("%s: %d/%d library edits applied" % (os.path.basename(path), n, len(edits)))
    rep["steps"]["silk_edge"] = s2

    # 3. P1 silk over R1 pad 1 ----------------------------------------------------------------------------------
    s3 = []
    r1 = fp_by_ref(board, "R1"); pad1 = [p for p in r1.Pads() if p.GetNumber() == "1"][0]
    pb = pad1.GetBoundingBox(); keep = FromMM(0.20)
    for g in list(p1.GraphicalItems()):
        if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() != "PCB_SHAPE" or g.GetShape() != pcbnew.SHAPE_T_SEGMENT: continue
        a, b = g.GetStart(), g.GetEnd()
        if a.y != b.y: continue
        if not (pb.GetTop() - keep <= a.y <= pb.GetBottom() + keep): continue
        x0, x1 = min(a.x, b.x), max(a.x, b.x)
        if x1 <= pb.GetLeft() - keep or x0 >= pb.GetRight() + keep: continue
        g.SetStart(VECTOR2I(x0, a.y)); g.SetEnd(VECTOR2I(pb.GetLeft() - keep, a.y))
        g2 = pcbnew.PCB_SHAPE(p1, pcbnew.SHAPE_T_SEGMENT); g2.SetLayer(pcbnew.F_SilkS); g2.SetWidth(g.GetWidth())
        g2.SetStart(VECTOR2I(pb.GetRight() + keep, a.y)); g2.SetEnd(VECTOR2I(x1, a.y)); p1.Add(g2)
        s3.append("P1 segment y=%.3f split around R1 pad 1 (gap x %.3f..%.3f)" % (ToMM(a.y), ToMM(pb.GetLeft() - keep), ToMM(pb.GetRight() + keep)))
    rep["steps"]["silk_over_copper"] = s3

    # 4. reference text size + relocation -----------------------------------------------------------------------
    resized, thick = [], []
    for fp in board.GetFootprints():
        t = fp.Reference()
        if not t.IsVisible() or t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS): continue
        if ToMM(t.GetTextHeight()) < TXT_H - 1e-6:
            t.SetTextSize(VECTOR2I(FromMM(TXT_H), FromMM(TXT_H))); t.SetTextThickness(FromMM(TXT_T)); resized.append(fp.GetReference())
        elif ToMM(t.GetTextThickness()) < TXT_T - 1e-6:
            t.SetTextThickness(FromMM(TXT_T)); thick.append(fp.GetReference())
    rep["steps"]["text_resized_to_0.8_0.15"] = sorted(resized); rep["steps"]["text_thickness_to_0.15"] = sorted(thick)
    moves = []
    for front in (True, False):
        idx = SilkIndex(board, front)
        for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
            t = fp.Reference()
            if not t.IsVisible() or t.GetLayer() != idx.silk: continue
            relocate(board, idx, fp, moves)
    rep["steps"]["text_moves"] = moves

    if DRY:
        print(json.dumps(rep, indent=1)); return
    for fp, g in to_remove: fp.Remove(g)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)

    # 5. DRC loop on the real report ----------------------------------------------------------------------------
    history = []
    for it in range(5):
        by, viol = run_drc("a8_after")
        history.append(by)
        todo = []
        for v in viol:
            if v["type"] not in ("silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height", "text_thickness"): continue
            for item in v.get("items", []):
                m = re.match(r"Reference field of (\S+)", item.get("description", ""))
                if m: todo.append(m.group(1))
        todo = sorted(set(todo))
        if not todo: break
        board = pcbnew.LoadBoard(PCB)
        idxF, idxB = SilkIndex(board, True), SilkIndex(board, False)
        more = []
        for ref in todo:
            fp = fp_by_ref(board, ref); t = fp.Reference()
            idx = idxF if t.GetLayer() == pcbnew.F_SilkS else idxB
            # force a move: the current spot is bad even if the local model thinks otherwise
            t.SetPosition(VECTOR2I(t.GetPosition().x + FromMM(50), t.GetPosition().y))
            idx.refresh_text(t, ref)
            r = relocate(board, idx, fp, more)
            if r == "kept":
                t.SetVisible(False); more.append({"ref": ref, "action": "hidden", "note": "DRC still flagged it"})
        moves.extend(more)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(PCB, board)
    by, viol = run_drc("a8_after")
    rep["drc_after"] = by; rep["drc_iterations"] = history
    rep["remaining_non_mismatch"] = [{"type": v["type"], "desc": v["description"], "items": [i.get("description") for i in v.get("items", [])],
                                      "pos": [v["items"][0]["pos"]["x"], v["items"][0]["pos"]["y"]] if v.get("items") else None}
                                     for v in viol if v["type"] != "lib_footprint_mismatch"]
    board = pcbnew.LoadBoard(PCB)
    rep["hidden_refs"] = sorted(m["ref"] for m in moves if m["action"] == "hidden")
    rep["moved_refs"] = sorted(m["ref"] for m in moves if m["action"] == "moved")
    (OUTD / "drc-cleanup.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps({"before": before, "after": by, "moved": len(rep["moved_refs"]), "hidden": rep["hidden_refs"], "iters": len(history)}, indent=1))


if __name__ == "__main__":
    main()
