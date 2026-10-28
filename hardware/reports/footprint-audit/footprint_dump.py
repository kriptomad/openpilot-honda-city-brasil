#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
footprint_dump.py - Read-only dump of every footprint on a KiCad 10 board.

Usage:
  "C:\\...\\KiCad\\10.0\\bin\\python.exe" -u footprint_dump.py <board.kicad_pcb> <out.json>

Emits, per footprint: reference, value, lib id, layer, position, rotation,
attributes (SMD/THT/...), 3D models, courtyard bbox, and for every pad:
number, net, absolute position, local offset (relative to footprint origin,
rotation removed), size, shape, attribute, drill, layers, roundrect ratio.
Also derives a compact "geometry signature" (pitch / span / EP) that is
reused by the audit to compare against datasheet land patterns.
Never writes to the board.
"""
import sys, json, math
import pcbnew

NM = 1e6

SHAPES = {
    pcbnew.PAD_SHAPE_CIRCLE: "circle",
    pcbnew.PAD_SHAPE_RECT: "rect",
    pcbnew.PAD_SHAPE_OVAL: "oval",
    pcbnew.PAD_SHAPE_TRAPEZOID: "trapezoid",
    pcbnew.PAD_SHAPE_ROUNDRECT: "roundrect",
    pcbnew.PAD_SHAPE_CHAMFERED_RECT: "chamfered_rect",
    pcbnew.PAD_SHAPE_CUSTOM: "custom",
}
ATTRS = {
    pcbnew.PAD_ATTRIB_PTH: "PTH",
    pcbnew.PAD_ATTRIB_SMD: "SMD",
    pcbnew.PAD_ATTRIB_CONN: "CONN",
    pcbnew.PAD_ATTRIB_NPTH: "NPTH",
}


def mm(v):
    return round(v / NM, 4)


def fp_attr(fp):
    a = fp.GetAttributes()
    out = []
    if a & pcbnew.FP_SMD:
        out.append("SMD")
    if a & pcbnew.FP_THROUGH_HOLE:
        out.append("THT")
    if a & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
        out.append("EXCL_POS")
    if a & pcbnew.FP_EXCLUDE_FROM_BOM:
        out.append("EXCL_BOM")
    if a & pcbnew.FP_DNP:
        out.append("DNP")
    return out or ["UNSPECIFIED"]


def layer_names(board, lset):
    names = []
    for lid in lset.Seq():
        names.append(board.GetLayerName(lid))
    return names


def local_offset(fp, pad):
    """Pad centre relative to footprint origin, footprint rotation removed."""
    p = pad.GetPosition()
    o = fp.GetPosition()
    dx = p.x - o.x
    dy = p.y - o.y
    ang = math.radians(fp.GetOrientationDegrees())
    # KiCad: y down; rotating the fp by +ang rotates pads CCW on screen.
    # Undo: rotate by -ang in the y-down frame.
    c, s = math.cos(ang), math.sin(ang)
    lx = dx * c - dy * s
    ly = dx * s + dy * c
    return mm(lx), mm(ly)


def signature(pads):
    """Derive pitch / spans from SMD/PTH pad local offsets (numbered pads only)."""
    pts = [(p["lx"], p["ly"], p["sx"], p["sy"]) for p in pads if p["attr"] in ("SMD", "PTH") and p["num"]]
    sig = {}
    if len(pts) < 2:
        return sig
    xs = sorted(set(round(p[0], 3) for p in pts))
    ys = sorted(set(round(p[1], 3) for p in pts))
    sig["unique_x"] = xs
    sig["unique_y"] = ys
    sig["span_x"] = round(xs[-1] - xs[0], 3)
    sig["span_y"] = round(ys[-1] - ys[0], 3)

    def min_step(vals):
        d = [round(b - a, 3) for a, b in zip(vals, vals[1:]) if b - a > 0.05]
        return min(d) if d else None

    sig["min_step_x"] = min_step(xs)
    sig["min_step_y"] = min_step(ys)
    return sig


def main():
    board_path, out_path = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(board_path)
    res = {"board": board_path, "footprints": []}
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        fid = fp.GetFPID()
        d = {
            "ref": fp.GetReference(),
            "value": fp.GetValue(),
            "lib": fid.GetLibNickname().wx_str() if hasattr(fid.GetLibNickname(), "wx_str") else str(fid.GetLibNickname()),
            "name": str(fid.GetLibItemName()),
            "layer": board.GetLayerName(fp.GetLayer()),
            "pos": [mm(fp.GetPosition().x), mm(fp.GetPosition().y)],
            "rot": fp.GetOrientationDegrees(),
            "attrs": fp_attr(fp),
            "models": [m.m_Filename for m in fp.Models()],
            "pads": [],
        }
        try:
            bb = fp.GetBoundingBox(False)
            d["bbox_mm"] = [mm(bb.GetWidth()), mm(bb.GetHeight())]
        except Exception:
            pass
        try:
            cy = fp.GetCourtyard(pcbnew.F_CrtYd if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
            cb = cy.BBox()
            d["courtyard_mm"] = [mm(cb.GetWidth()), mm(cb.GetHeight())]
        except Exception:
            d["courtyard_mm"] = None
        for pad in fp.Pads():
            lx, ly = local_offset(fp, pad)
            sz = pad.GetSize(pcbnew.F_Cu) if "GetSize" in dir(pad) and pad.GetSize.__code__.co_argcount > 1 else pad.GetSize()
            try:
                shp = pad.GetShape(pcbnew.F_Cu)
            except TypeError:
                shp = pad.GetShape()
            dr = pad.GetDrillSize()
            try:
                rr = pad.GetRoundRectRadiusRatio(pcbnew.F_Cu)
            except TypeError:
                rr = pad.GetRoundRectRadiusRatio()
            pd = {
                "num": pad.GetNumber(),
                "net": pad.GetNetname(),
                "x": mm(pad.GetPosition().x),
                "y": mm(pad.GetPosition().y),
                "lx": lx,
                "ly": ly,
                "sx": mm(sz.x),
                "sy": mm(sz.y),
                "shape": SHAPES.get(shp, str(shp)),
                "attr": ATTRS.get(pad.GetAttribute(), str(pad.GetAttribute())),
                "drill": [mm(dr.x), mm(dr.y)] if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else None,
                "layers": layer_names(board, pad.GetLayerSet()),
                "rr": round(rr, 3),
                "pad_rot": pad.GetOrientationDegrees() - fp.GetOrientationDegrees(),
            }
            d["pads"].append(pd)
        d["pads"].sort(key=lambda p: (len(p["num"]), p["num"]))
        d["sig"] = signature(d["pads"])
        res["footprints"].append(d)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("footprints:", len(res["footprints"]))


if __name__ == "__main__":
    main()
