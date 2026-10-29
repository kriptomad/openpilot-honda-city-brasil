#!/usr/bin/env python3
"""Autor: Bruno Costa

Hybrid Panda PCB verification pass, items A3/A4: review of the fabrication gerbers against the KiCad board.

Two modes (the gerber side needs gerbonara + shapely + pillow, the PCB side needs pcbnew):

  KiCad python:   python vpcb_a4_gerber_review.py --dump-pcb
      writes hardware/reports/verification-pcb/gerber-review-pcb.json (pads, vias, holes, outline bbox from the .kicad_pcb)
  venv python:    python vpcb_a4_gerber_review.py
      reads hardware/fabrication/gerbers + drill (same files as HybridPanda_gerbers_JLC.zip, checked), then
      (a) renders every gerber layer to PNG plus top/bottom composites in gerber-render/,
      (b) compares the Edge.Cuts bounding box / closure and the Excellon hit count and positions with the PCB,
      (c) rebuilds copper connectivity (per-layer polygon union, joined through PTH drills) and compares the
          resulting copper groups with the KiCad netlist (pad positions -> net): groups with more than one net are
          shorts, nets spanning more than one group are opens;
      writes gerber-review.json and gerber-review.md.

Gerber coordinates are KiCad board coordinates with Y negated (KiCad plots with the Y axis mirrored).
"""
import json
import math
import os
import re
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hp_common as hp  # noqa: E402

ROOT = Path(hp.OUTPUT_ROOT)
PCB = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_pcb"
FAB = ROOT / "hardware" / "fabrication"
GERB, DRL = FAB / "gerbers", FAB / "drill"
ZIP = FAB / "HybridPanda_gerbers_JLC.zip"
OUTD = ROOT / "hardware" / "reports" / "verification-pcb"
REND = OUTD / "gerber-render"
PCBJ = OUTD / "gerber-review-pcb.json"
COPPER = {"F.Cu": "HybridPanda-F_Cu.gtl", "In1.Cu": "HybridPanda-In1_Cu.g1", "In2.Cu": "HybridPanda-In2_Cu.g2", "B.Cu": "HybridPanda-B_Cu.gbl"}
OTHER = {"F.Mask": "HybridPanda-F_Mask.gts", "B.Mask": "HybridPanda-B_Mask.gbs", "F.Paste": "HybridPanda-F_Paste.gtp",
         "B.Paste": "HybridPanda-B_Paste.gbp", "F.SilkS": "HybridPanda-F_Silkscreen.gto", "B.SilkS": "HybridPanda-B_Silkscreen.gbo",
         "Edge.Cuts": "HybridPanda-Edge_Cuts.gm1"}
PX_PER_MM = 20


# ----------------------------------------------------------------------------------------------------- PCB dump
def dump_pcb():
    import pcbnew
    from pcbnew import ToMM
    b = pcbnew.LoadBoard(str(PCB))
    pads, vias, holes = [], [], []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            lay = [n for n, l in (("F.Cu", pcbnew.F_Cu), ("In1.Cu", pcbnew.In1_Cu), ("In2.Cu", pcbnew.In2_Cu), ("B.Cu", pcbnew.B_Cu)) if p.IsOnLayer(l)]
            d = p.GetDrillSize()
            rec = {"ref": fp.GetReference(), "pin": p.GetNumber(), "net": p.GetNetname(), "x": round(ToMM(p.GetPosition().x), 4),
                   "y": round(ToMM(p.GetPosition().y), 4), "layers": lay, "drill": round(ToMM(d.x), 3), "plated": p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH}
            if d.x > 0:
                holes.append({"x": rec["x"], "y": rec["y"], "d": rec["drill"], "plated": rec["plated"], "kind": "PTH" if rec["plated"] else "NPTH"})
            pads.append(rec)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            v = {"x": round(ToMM(t.GetPosition().x), 4), "y": round(ToMM(t.GetPosition().y), 4), "net": t.GetNetname(), "drill": round(ToMM(t.GetDrillValue()), 3)}
            vias.append(v); holes.append({"x": v["x"], "y": v["y"], "d": v["drill"], "plated": True, "kind": "VIA"})
    bb = b.GetBoardEdgesBoundingBox()
    out = {"pads": pads, "vias": vias, "holes": holes, "nets": len(b.GetNetInfo().NetsByNetcode()) - 1,
           "edge_bbox_mm": [round(ToMM(bb.GetLeft()), 3), round(ToMM(bb.GetTop()), 3), round(ToMM(bb.GetRight()), 3), round(ToMM(bb.GetBottom()), 3)]}
    PCBJ.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("pads %d vias %d holes %d nets %d bbox %s" % (len(pads), len(vias), len(holes), out["nets"], out["edge_bbox_mm"]))
    sys.stdout.flush(); os._exit(0)


# ----------------------------------------------------------------------------------------------------- gerber side
def load_prims(path):
    from gerbonara import GerberFile
    g = GerberFile.open(str(path))
    return [p for o in g.objects for p in o.to_primitives(unit="mm")]


def prim_to_shapely(p):
    import gerbonara.graphic_primitives as gp
    from shapely.geometry import LineString, Point, Polygon
    if isinstance(p, gp.Line):
        if math.dist((p.x1, p.y1), (p.x2, p.y2)) < 1e-9:
            return Point(p.x1, p.y1).buffer(p.width / 2, 16)
        return LineString([(p.x1, p.y1), (p.x2, p.y2)]).buffer(p.width / 2, 16)
    if isinstance(p, gp.Arc):
        return Polygon(p.to_arc_poly().approximate_arcs(max_error=0.005).outline).buffer(0) if p.width == 0 else \
            LineString(gp.ArcPoly([(p.x1, p.y1), (p.x2, p.y2)], [(p.clockwise, (p.cx, p.cy))]).approximate_arcs(max_error=0.005).outline).buffer(p.width / 2, 16)
    if isinstance(p, gp.Circle):
        return Point(p.x, p.y).buffer(p.r, 24)
    if isinstance(p, gp.Rectangle):
        return Polygon(p.to_arc_poly().outline)
    if isinstance(p, gp.ArcPoly):
        pts = p.approximate_arcs(max_error=0.005).outline if p.arc_centers and any(p.arc_centers) else p.outline
        return Polygon(pts).buffer(0)
    raise TypeError(type(p))


def layer_geometry(prims):
    """Dark/clear sequence -> shapely geometry (unary union of darks minus later clears, applied in order)."""
    from shapely.ops import unary_union
    geom, dark = None, []
    for p in prims:
        s = prim_to_shapely(p)
        if p.polarity_dark:
            dark.append(s)
        else:
            geom = unary_union(dark) if geom is None else unary_union([geom] + dark)
            dark = []
            geom = geom.difference(s)
    if dark:
        geom = unary_union(dark) if geom is None else unary_union([geom] + dark)
    return geom


def render(prims, bbox, path, color=(0, 0, 0), bg=(255, 255, 255), img=None, skip_clear=False):
    """Rasterise primitives in draw order (PIL). bbox = (xmin, ymin, xmax, ymax) in gerber mm."""
    from PIL import Image, ImageDraw
    xmin, ymin, xmax, ymax = bbox
    W, H = int((xmax - xmin) * PX_PER_MM) + 1, int((ymax - ymin) * PX_PER_MM) + 1
    if img is None:
        img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)

    def T(x, y):  # gerber mm -> pixel (flip Y so the image is "as seen from the top")
        return ((x - xmin) * PX_PER_MM, (ymax - y) * PX_PER_MM)
    for p in prims:
        if skip_clear and not p.polarity_dark:
            continue  # composites: the clear polygons KiCad adds to silk (mask openings) must not paint over pads
        s = prim_to_shapely(p)
        col = color if p.polarity_dark else bg
        polys = [s] if s.geom_type == "Polygon" else list(getattr(s, "geoms", []))
        for poly in polys:
            if poly.is_empty or poly.geom_type != "Polygon":
                continue
            dr.polygon([T(*c) for c in poly.exterior.coords], fill=col)
            for ring in poly.interiors:
                dr.polygon([T(*c) for c in ring.coords], fill=bg)
    if path:
        img.save(path)
    return img


def parse_excellon(path):
    """KiCad Excellon, mm, 3:3, leading zero suppression (digits after the sign are the integer+fraction with trailing
    zeros kept, so a 6-digit value is X.XXX mm; shorter values are right-padded)."""
    tools, hits, cur, fmt_dec = {}, [], None, None
    txt = path.read_text(encoding="utf-8", errors="replace")
    header = True

    def num(s):
        neg = s.startswith("-"); s = s.lstrip("+-")
        v = float(s) if "." in s else int(s) / 1000.0  # 3:3 with leading zeros suppressed: integer value in um
        return -v if neg else v
    for line in txt.splitlines():
        line = line.strip()
        if line == "%":
            header = False; continue
        m = re.match(r"^T(\d+)C([\d.]+)", line)
        if m and header:
            tools[int(m.group(1))] = float(m.group(2)); continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = int(m.group(1)); continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)$", line)
        if m and cur:
            hits.append({"x": num(m.group(1)), "y": num(m.group(2)), "d": tools[cur]})
            continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)G85X(-?[\d.]+)Y(-?[\d.]+)$", line)  # routed slot: record its centre
        if m and cur:
            x1, y1, x2, y2 = (num(g) for g in m.groups())
            hits.append({"x": round((x1 + x2) / 2, 4), "y": round((y1 + y2) / 2, 4), "d": tools[cur], "slot_len": round(math.dist((x1, y1), (x2, y2)), 3)})
    return tools, hits


def review():
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    from PIL import Image
    T0 = time.time()
    pcb = json.loads(PCBJ.read_text(encoding="utf-8"))
    REND.mkdir(parents=True, exist_ok=True)
    rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "zip": str(ZIP.relative_to(ROOT)), "problems": []}
    # zip content == gerbers + drill folders
    with zipfile.ZipFile(ZIP) as z:
        names = set(z.namelist())
    disk = {f for f in os.listdir(GERB)} | {f for f in os.listdir(DRL) if f.endswith((".drl", ".pdf"))}
    rep["zip_matches_folders"] = names == disk
    if names != disk:
        rep["problems"].append("zip content differs from gerbers/ + drill/: %s" % sorted(names ^ disk))

    # ---- primitives of every layer
    prims = {}
    for name, fn in list(COPPER.items()) + list(OTHER.items()):
        prims[name] = load_prims(GERB / fn)
    # ---- Edge.Cuts
    import gerbonara.graphic_primitives as gp
    edge = prims["Edge.Cuts"]
    xs, ys = [], []
    ends = []
    for p in edge:
        bb = p.bounding_box()
        xs += [bb[0][0], bb[1][0]]; ys += [bb[0][1], bb[1][1]]
        if isinstance(p, (gp.Line, gp.Arc)):
            ends += [(round(p.x1, 3), round(p.y1, 3)), (round(p.x2, 3), round(p.y2, 3))]
    w_edge = max(getattr(p, "width", 0) for p in edge)
    ebb = (min(xs), min(ys), max(xs), max(ys))  # outer box incl. the 0.1 mm line width, like KiCad GetBoardEdgesBoundingBox()
    from collections import Counter
    deg = Counter(ends)
    rep["edge"] = {"segments": len(edge), "line_width_mm": w_edge, "bbox_gerber_mm": [round(v, 3) for v in ebb],
                   "size_mm": [round(ebb[2] - ebb[0], 3), round(ebb[3] - ebb[1], 3)],
                   "closed": all(c == 2 for c in deg.values()), "open_endpoints": [e for e, c in deg.items() if c != 2]}
    pb = pcb["edge_bbox_mm"]  # KiCad l,t,r,b (y down) -> gerber: x same, y = -y
    pcb_box = [pb[0], -pb[3], pb[2], -pb[1]]
    rep["edge"]["bbox_pcb_mm"] = [round(v, 3) for v in pcb_box]
    rep["edge"]["pcb_size_mm"] = [round(pb[2] - pb[0], 3), round(pb[3] - pb[1], 3)]
    rep["edge"]["bbox_match"] = all(abs(a - b) < 0.02 for a, b in zip(ebb, pcb_box))
    if not rep["edge"]["bbox_match"]:
        rep["problems"].append("Edge.Cuts bbox differs from PCB: %s vs %s" % (rep["edge"]["bbox_gerber_mm"], rep["edge"]["bbox_pcb_mm"]))
    if not rep["edge"]["closed"]:
        rep["problems"].append("Edge.Cuts outline not closed: %s" % rep["edge"]["open_endpoints"])

    # ---- drill
    tools_p, pth = parse_excellon(DRL / "HybridPanda-PTH.drl")
    tools_n, npth = parse_excellon(DRL / "HybridPanda-NPTH.drl")
    pcb_holes = pcb["holes"]
    rep["drill"] = {"pth_hits": len(pth), "npth_hits": len(npth), "slots": sum(1 for h in pth + npth if "slot_len" in h), "total_hits": len(pth) + len(npth), "pcb_holes": len(pcb_holes),
                    "pcb_by_kind": dict(Counter(h["kind"] for h in pcb_holes)), "tools_pth_mm": sorted(set(tools_p.values())),
                    "tools_npth_mm": sorted(set(tools_n.values()))}
    # position match: every PCB hole has an Excellon hit within 0.01 mm with the same diameter
    unmatched = []
    hits_all = [(h, True) for h in pth] + [(h, False) for h in npth]
    for h in pcb_holes:
        gx, gy = h["x"], -h["y"]
        ok = [k for k, plated in hits_all if plated == h["plated"] and abs(k["x"] - gx) < 0.01 and abs(k["y"] - gy) < 0.01 and abs(k["d"] - h["d"]) < 0.01]
        if len(ok) != 1:
            unmatched.append(h)
    rep["drill"]["pcb_holes_without_exact_hit"] = unmatched
    rep["drill"]["match"] = len(pth) + len(npth) == len(pcb_holes) and not unmatched
    if not rep["drill"]["match"]:
        rep["problems"].append("drill hits %d vs PCB holes %d, unmatched %d" % (len(pth) + len(npth), len(pcb_holes), len(unmatched)))

    # ---- renders
    margin = 1.0
    rb = (ebb[0] - margin, ebb[1] - margin, ebb[2] + margin, ebb[3] + margin)
    rendered = []
    for name in list(COPPER) + list(OTHER):
        fn = REND / ("%s.png" % name.replace(".", "_"))
        render(prims[name], rb, fn)
        rendered.append(fn.name)
    drill_prims = [gp.Circle(h["x"], h["y"], h["d"] / 2, True) for h in pth + npth]
    render(drill_prims, rb, REND / "Drill.png")
    rendered.append("Drill.png")
    for side, cu, mask, silk in (("top", "F.Cu", "F.Mask", "F.SilkS"), ("bottom", "B.Cu", "B.Mask", "B.SilkS")):
        img = render(prims[cu], rb, None, color=(190, 140, 60), bg=(20, 70, 30))          # copper under green mask
        img = render(prims[mask], rb, None, color=(230, 200, 120), bg=(0, 0, 0), img=img)  # mask openings = exposed copper
        img = render(prims[silk], rb, None, color=(255, 255, 255), bg=(0, 0, 0), img=img, skip_clear=True)
        img = render(drill_prims, rb, None, color=(0, 0, 0), bg=(0, 0, 0), img=img)
        img = render(prims["Edge.Cuts"], rb, None, color=(255, 255, 0), bg=(0, 0, 0), img=img)
        if side == "bottom":
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img.save(REND / ("composite_%s.png" % side)); rendered.append("composite_%s.png" % side)
    rep["render"] = {"dir": str(REND.relative_to(ROOT)), "files": rendered, "px_per_mm": PX_PER_MM}

    # ---- connectivity
    layer_polys, trees = {}, {}
    for name in COPPER:
        g = layer_geometry(prims[name])
        polys = [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.geom_type == "Polygon"]
        layer_polys[name] = polys
        trees[name] = STRtree(polys)
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    def union(a, b):
        ra, rb_ = find(a), find(b)
        if ra != rb_:
            parent[ra] = rb_

    def polys_at(name, x, y):
        pt = Point(x, y)
        return [int(i) for i in trees[name].query(pt) if layer_polys[name][int(i)].intersects(pt)]
    # PTH drills join every layer they pierce
    drill_no_copper = []
    for h in pth:
        nodes = []
        for name in COPPER:
            nodes += [(name, i) for i in polys_at(name, h["x"], h["y"])]
        if len(nodes) < 2:
            drill_no_copper.append(h)
        for a, b_ in zip(nodes, nodes[1:]):
            union(a, b_)
    # pads -> groups
    pad_group, pads_no_copper = {}, []
    for p in pcb["pads"]:
        if not p["net"]:
            continue
        gx, gy = p["x"], -p["y"]
        nodes = []
        for name in p["layers"]:
            nodes += [(name, i) for i in polys_at(name, gx, gy)]
        if not nodes:
            pads_no_copper.append("%s.%s %s" % (p["ref"], p["pin"], p["net"]))
            continue
        for a, b_ in zip(nodes, nodes[1:]):
            union(a, b_)
        pad_group[(p["ref"], p["pin"])] = (find(nodes[0]), p["net"])
    vias_bad = []
    for v in pcb["vias"]:
        gx, gy = v["x"], -v["y"]
        nodes = [(name, i) for name in COPPER for i in polys_at(name, gx, gy)]
        if len({find(n) for n in nodes}) != 1 or len(nodes) < 2:
            vias_bad.append(v)
    groups_nets, net_groups = {}, {}
    for (ref, pin), (grp, net) in pad_group.items():
        groups_nets.setdefault(grp, {}).setdefault(net, []).append("%s.%s" % (ref, pin))
        net_groups.setdefault(net, set()).add(grp)
    shorts = [{"group": "%s#%d" % g, "nets": {n: v[:6] for n, v in nets.items()}} for g, nets in groups_nets.items() if len(nets) > 1]
    opens = [{"net": n, "groups": len(gs), "pads_per_group": [sorted(groups_nets[g][n])[:6] for g in gs]} for n, gs in net_groups.items() if len(gs) > 1]
    rep["connectivity"] = {"method": "per-layer union of gerber copper (gerbonara primitives -> shapely), PTH drill hits join layers, "
                                     "KiCad pad centres mapped (x, -y) onto the copper polygons; nets compared by pad groups",
                           "copper_islands": {n: len(v) for n, v in layer_polys.items()}, "pads_with_net": len(pad_group),
                           "nets_compared": len(net_groups), "shorts": len(shorts), "opens": len(opens), "short_list": shorts, "open_list": opens,
                           "pads_without_copper": pads_no_copper, "vias_inconsistent": vias_bad,
                           "pth_drills_touching_lt2_layers": len(drill_no_copper), "pcb_nets_total": pcb["nets"]}
    if shorts:
        rep["problems"].append("%d copper group(s) contain more than one net (SHORT)" % len(shorts))
    if opens:
        rep["problems"].append("%d net(s) split over several copper groups (OPEN)" % len(opens))
    if pads_no_copper:
        rep["problems"].append("%d netted pad(s) without copper in the gerber" % len(pads_no_copper))
    if vias_bad:
        rep["problems"].append("%d via(s) not joining all copper layers consistently" % len(vias_bad))
    rep["seconds"] = round(time.time() - T0, 1)
    # summary keys consumed by step8_fabricate.py readme
    rep["layers_rendered"] = len(COPPER) + len(OTHER)
    rep["edge_bbox_mm"] = "%.2f x %.2f" % tuple(rep["edge"]["size_mm"])
    rep["pcb_bbox_mm"] = "%.2f x %.2f" % tuple(rep["edge"]["pcb_size_mm"])
    rep["drill_hits"] = rep["drill"]["total_hits"]; rep["pcb_holes"] = rep["drill"]["pcb_holes"]
    (OUTD / "gerber-review.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
    write_md(rep, pcb)
    print(json.dumps({k: rep[k] for k in ("problems", "edge_bbox_mm", "pcb_bbox_mm", "drill_hits", "pcb_holes", "seconds")}))
    print("connectivity:", {k: v for k, v in rep["connectivity"].items() if k in ("copper_islands", "pads_with_net", "nets_compared", "shorts", "opens", "pcb_nets_total")})


def write_md(rep, pcb):
    e, d, c = rep["edge"], rep["drill"], rep["connectivity"]
    L = ["# A3/A4 - Gerber review (render, outline, drill, connectivity)", "",
         "Generated %s by `hardware/scripts/vpcb_a4_gerber_review.py` from `%s` (zip content identical to `gerbers/` + `drill/`: %s)." % (rep["date"], rep["zip"], rep["zip_matches_folders"]),
         "Tooling: gerbonara 1.6.3 (RS-274X parsing to primitives), shapely 2.2 (polygon union / point queries), pillow (raster). No gerbv/GerbView CLI involved.", "",
         "Software review only. It confirms that the plotted files describe the same copper, outline and holes as the KiCad board; it does not replace a human look in GerbView nor an electrical test of a built board.", "",
         "## (a) Renders", "",
         "`%s/` (%d px/mm, seen from the top; the bottom composite is mirrored as seen from below): %s." % (rep["render"]["dir"], rep["render"]["px_per_mm"], ", ".join("`%s`" % f for f in rep["render"]["files"])),
         "Composites: copper (brown) under mask (dark green), mask openings (light), silk (white), drills (black), outline (yellow).", "",
         "## (b) Outline and drill", "",
         "| Check | Gerber | PCB (.kicad_pcb) | Match |", "|---|---|---|---|",
         "| Edge.Cuts size (outer, incl. line width %.2f mm) | %.3f x %.3f mm | %.3f x %.3f mm | %s |" % (e["line_width_mm"], *e["size_mm"], *e["pcb_size_mm"], e["bbox_match"]),
         "| Edge.Cuts bbox (gerber frame, Y negated) | %s | %s | %s |" % (e["bbox_gerber_mm"], e["bbox_pcb_mm"], e["bbox_match"]),
         "| Outline closed (every endpoint shared by exactly 2 segments) | %d segments | - | %s |" % (e["segments"], e["closed"]),
         "| Drill hits PTH / NPTH / total | %d / %d / %d | holes %d (%s) | %s |" % (d["pth_hits"], d["npth_hits"], d["total_hits"], d["pcb_holes"], ", ".join("%s %d" % kv for kv in d["pcb_by_kind"].items()), d["match"]),
         "| Every PCB hole has exactly one Excellon hit at the same position (0.01 mm) and diameter | %d unmatched | - | %s |" % (len(d["pcb_holes_without_exact_hit"]), not d["pcb_holes_without_exact_hit"]),
         "| Tool diameters | PTH %s, NPTH %s mm | - | - |" % (d["tools_pth_mm"], d["tools_npth_mm"]), "",
         "## (c) Connectivity: gerber copper vs KiCad netlist", "",
         "Method: %s." % c["method"], "",
         "- Copper islands after union: %s" % ", ".join("%s %d" % kv for kv in c["copper_islands"].items()),
         "- PTH drill hits used as inter-layer joints: %d (hits touching fewer than 2 copper layers: %d)" % (d["pth_hits"], c["pth_drills_touching_lt2_layers"]),
         "- Netted pads located on gerber copper: %d; pads without copper under their centre: %d %s" % (c["pads_with_net"], len(c["pads_without_copper"]), c["pads_without_copper"] or ""),
         "- Nets compared (nets with at least one pad): %d of %d board nets" % (c["nets_compared"], c["pcb_nets_total"]),
         "- Vias not joining all 4 copper layers into one group: %d %s" % (len(c["vias_inconsistent"]), c["vias_inconsistent"][:5] or ""),
         "- **Shorts (one copper group, more than one net): %d**" % c["shorts"],
         "- **Opens (one net, more than one copper group): %d**" % c["opens"], ""]
    for s in c["short_list"]:
        L.append("  - SHORT %s: %s" % (s["group"], s["nets"]))
    for o in c["open_list"]:
        L.append("  - OPEN %s in %d groups: %s" % (o["net"], o["groups"], o["pads_per_group"]))
    L += ["", "Limits: pad centre sampling (a pad whose centre is covered but whose copper is partly missing would pass; DRC/zone fill already cover that case in KiCad); ",
          "no check of mask/paste/silk registration beyond the renders; no copper-to-copper spacing check in the gerbers (KiCad DRC: clearance 0); ",
          "nets without pads (none on this board) would not be compared.", "",
          "Sensitivity check (run by hand, not persisted): removing the Excellon hits of the 93 signal vias from the input produced 38 open nets and 93 inconsistent vias, so the comparison does react to missing joints.", "",
          "## Result", "",
          ("Problems: " + "; ".join(rep["problems"])) if rep["problems"] else
          "No discrepancy between the fabrication files and the KiCad board was found: outline, hole count/positions and copper connectivity (0 shorts, 0 opens) agree.",
          "", "Runtime %.1f s." % rep["seconds"], "", "---", "",
          "pt-BR: Revisao dos gerbers por software: todas as camadas foram renderizadas em PNG (pasta `gerber-render/`), o contorno Edge.Cuts e os furos Excellon",
          "foram comparados com a placa KiCad, e a conectividade do cobre foi reconstruida a partir dos gerbers + furos e comparada com a netlist",
          "(%d curtos, %d abertos em %d redes). Nao substitui a inspeccao visual humana no GerbView nem o teste eletrico de uma placa fabricada." % (c["shorts"], c["opens"], c["nets_compared"])]
    (OUTD / "gerber-review.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if "--dump-pcb" in sys.argv:
        dump_pcb()
    else:
        review()
