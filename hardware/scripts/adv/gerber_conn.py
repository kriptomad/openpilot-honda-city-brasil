"""Independent gerber connectivity recompute (gerbonara + shapely).
Copper layers -> shapely islands; PTH drill hits + via hits -> inter-layer links;
pads (from pads.json) -> net labels. Reports islands with >1 net (shorts), nets split over
>1 cluster (opens), islands with no pad (floating copper), drill count, slots, outline."""
import json, math, sys, os
from pathlib import Path
from gerbonara import GerberFile, ExcellonFile
import gerbonara.graphic_primitives as gp
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

G = Path(r"hardware\fabrication\gerbers"); D = Path(r"hardware\fabrication\drill")
LAYERS = {"F.Cu": "HybridPanda-F_Cu.gtl", "In1.Cu": "HybridPanda-In1_Cu.g1", "In2.Cu": "HybridPanda-In2_Cu.g2", "B.Cu": "HybridPanda-B_Cu.gbl"}

def prim_to_shapely(p):
    if isinstance(p, gp.Line):
        if math.dist((p.x1, p.y1), (p.x2, p.y2)) < 1e-9:
            return Point(p.x1, p.y1).buffer(p.width / 2, 16)
        return LineString([(p.x1, p.y1), (p.x2, p.y2)]).buffer(p.width / 2, 16)
    if isinstance(p, gp.Arc):
        if p.width == 0:
            return Polygon(p.to_arc_poly().approximate_arcs(max_error=0.005).outline).buffer(0)
        return LineString(gp.ArcPoly([(p.x1, p.y1), (p.x2, p.y2)], [(p.clockwise, (p.cx, p.cy))]).approximate_arcs(max_error=0.005).outline).buffer(p.width / 2, 16)
    if isinstance(p, gp.Circle):
        return Point(p.x, p.y).buffer(p.r, 24)
    if isinstance(p, gp.Rectangle):
        return Polygon(p.to_arc_poly().outline)
    if isinstance(p, gp.ArcPoly):
        pts = p.approximate_arcs(max_error=0.005).outline if p.arc_centers and any(p.arc_centers) else p.outline
        return Polygon(pts).buffer(0)
    raise TypeError(type(p))

def layer_geom(path):
    gf = GerberFile.open(str(path))
    prims = [p for o in gf.objects for p in o.to_primitives(unit="mm")]
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
    return geom, len(prims)

pads = json.load(open(r"hardware\reports\verification-pcb\adv\pads.json"))
# gerber Y is positive-up; KiCad Y is positive-down -> gerber y = -kicad y
islands = []  # (layer, polygon)
for lname, fn in LAYERS.items():
    g, n = layer_geom(G / fn)
    polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    print(f"{lname}: {n} primitives -> {len(polys)} islands, area {g.area:.1f} mm2")
    islands += [(lname, p) for p in polys]

# union-find over islands
parent = list(range(len(islands)))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[ra] = rb

trees = {}
for lname in LAYERS:
    idx = [i for i, (l, _) in enumerate(islands) if l == lname]
    trees[lname] = (idx, STRtree([islands[i][1] for i in idx]))
def hit(lname, x, y):
    idx, tr = trees[lname]
    pt = Point(x, y)
    res = [idx[j] for j in tr.query(pt) if islands[idx[j]][1].intersects(pt)]
    return res

# drill hits (PTH file) link all 4 layers; own Excellon parser (3:3 metric, TZ)
import re
def parse_drl(path):
    tools, hits, cur, hdr = {}, [], None, True
    def num(s):
        neg = s.startswith("-"); s = s.lstrip("+-")
        v = float(s) if "." in s else int(s) / 1000.0
        return -v if neg else v
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line == "%": hdr = False; continue
        m = re.match(r"^T(\d+)C([\d.]+)", line)
        if m and hdr: tools[int(m.group(1))] = float(m.group(2)); continue
        m = re.match(r"^T(\d+)$", line)
        if m: cur = int(m.group(1)); continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)$", line)
        if m and cur: hits.append((num(m.group(1)), num(m.group(2)), tools[cur], 0)); continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)G85X(-?[\d.]+)Y(-?[\d.]+)$", line)
        if m and cur:
            x1, y1, x2, y2 = (num(g) for g in m.groups())
            hits.append(((x1 + x2) / 2, (y1 + y2) / 2, tools[cur], math.dist((x1, y1), (x2, y2))))
    return hits
holes = parse_drl(D / "HybridPanda-PTH.drl"); nholes = parse_drl(D / "HybridPanda-NPTH.drl")
slots = sum(1 for h in holes if h[3] > 0)
print(f"PTH drill objects {len(holes)} (slots {slots}: {[ (round(h[0],2), round(h[1],2), h[2], round(h[3],2)) for h in holes if h[3]>0]}), NPTH {len(nholes)}, total {len(holes)+len(nholes)}")
unlinked = 0
for (x, y, d, sl) in holes:
    hits = []
    for lname in LAYERS:
        hits += hit(lname, x, y)
    if len(hits) < 2: unlinked += 1
    for h in hits[1:]:
        union(hits[0], h)
print("PTH holes touching <2 copper layers:", unlinked)

# assign pads
cluster_nets = {}; net_clusters = {}; unmatched = []
for p in pads["pads"]:
    if p["npth"] or not p["net"]: continue
    gx, gy = p["x"], -p["y"]
    found = set()
    for lname in p["layers"]:
        for i in hit(lname, gx, gy): found.add(find(i))
    if not found:
        unmatched.append((p["ref"], p["pad"], p["net"])); continue
    for c in found:
        cluster_nets.setdefault(c, set()).add(p["net"])
        net_clusters.setdefault(p["net"], set()).add(c)
# recompute roots after unions (pads were assigned by root at the time; all unions already done)
shorts = {c: n for c, n in cluster_nets.items() if len(n) > 1}
opens = {n: c for n, c in net_clusters.items() if len(c) > 1}
print("pads not on any copper (should be 0):", len(unmatched), unmatched[:10])
print("SHORTS (clusters with >1 net):", len(shorts))
for c, n in shorts.items(): print("  ", sorted(n))
print("OPENS (nets split over >1 cluster):", len(opens))
for n, c in opens.items(): print("  ", n, len(c))
# vias: check each via sits on copper of its net cluster
viabad = 0
for v in pads["vias"]:
    hits = set(find(i) for i in hit("F.Cu", v["x"], -v["y"]) + hit("B.Cu", v["x"], -v["y"]))
    nets = set().union(*[cluster_nets.get(c, set()) for c in hits]) if hits else set()
    if v["net"] not in nets: viabad += 1
print("vias whose copper cluster does not carry their net:", viabad)
# floating copper islands (no pad, no via) with area > 0.5 mm2
roots_with_pads = set(cluster_nets)
float_is = [(l, p.area, p.representative_point().coords[0]) for i, (l, p) in enumerate(islands) if find(i) not in roots_with_pads and p.area > 0.3]
print("copper islands with no pad/net (area>0.3mm2):", len(float_is))
for f in sorted(float_is, key=lambda t: -t[1])[:40]: print("  ", f[0], round(f[1], 2), tuple(round(c, 2) for c in f[2]))
# outline
edge = GerberFile.open(G / "HybridPanda-Edge_Cuts.gm1")
ep = [p for o in edge.objects for p in o.to_primitives(unit="mm")]
from shapely.ops import linemerge
lines = [LineString([(p.x1, p.y1), (p.x2, p.y2)]) for p in ep if isinstance(p, gp.Line)]
arcs = [p for p in ep if isinstance(p, gp.Arc)]
for a in arcs:
    lines.append(LineString(gp.ArcPoly([(a.x1, a.y1), (a.x2, a.y2)], [(a.clockwise, (a.cx, a.cy))]).approximate_arcs(max_error=0.005).outline))
m = linemerge(lines)
print("edge primitives", len(ep), "merged ->", m.geom_type, "closed:", getattr(m, "is_ring", None) if m.geom_type == "LineString" else [g.is_ring for g in m.geoms], "bounds", [round(b, 2) for b in m.bounds])
# copper to edge: min distance from any copper island to outline ring
outl = Polygon(m.coords) if m.geom_type == "LineString" else None
if outl:
    ring = outl.exterior
    mind = min(ring.distance(p) for _, p in islands)
    outside = sum(1 for _, p in islands if not outl.buffer(0.01).contains(p))
    print("min copper-to-edge (mm):", round(mind, 3), " islands outside outline:", outside)
