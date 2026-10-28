"""STEP 5a — Sincroniza HybridPanda.kicad_pcb com a netlist do esquemático H725 e
posiciona os componentes novos (MCU em B.Cu, D-21). Determinístico e idempotente:
parte sempre de HybridPanda.kicad_pcb.baseline.

Executar com o Python do KiCad 10:
  "C:\\Users\\costabr\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe" hardware\\scripts\\step5_update_pcb.py

Fases:
  A. remove footprints ausentes da netlist; troca U7 LQFP-64 -> LQFP-144; adiciona novos
  B. sincroniza nets de todos os pads (netlist manda); remove nets órfãs
  C. remove trilhas/vias de nets cuja composição mudou (exceto potência) e trilhas soltas
  D. posiciona: U7 em B.Cu (orientação escolhida por menor comprimento de ratsnest),
     desacoplamento por pino VDD, VCAP, cristal, SMPS, VDDA, NRST, SWD, SBU, STB
  E. relatório de distâncias (regra 0x05.2) e colisões; salva
"""
import json, math, os, shutil, sys, time, xml.etree.ElementTree as ET
from collections import defaultdict

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PRJ = os.path.join(ROOT, "hardware", "hybrid-panda")
PCB = os.path.join(PRJ, "HybridPanda.kicad_pcb")
BASE = os.path.join(PRJ, "snapshots", "HybridPanda.kicad_pcb.baseline")
NETLIST = os.path.join(ROOT, "hardware/reports", "hybrid_HybridPanda_netlist.xml")
REPORT = os.path.join(ROOT, "hardware/reports", "step5_update_pcb.json")
FPROOT = r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"

MM = pcbnew.FromMM
def mm(v): return pcbnew.ToMM(v)
def V(x, y): return pcbnew.VECTOR2I(MM(x), MM(y))

POWER_NETS = {"GND", "+3V3", "+5V", "+12V", "12V_Protected", "USB_PWR", "L4", "VDDA"}
EDGE_MARGIN = 1.0      # mm, copper-to-edge
COURTYARD_GAP = 0.30   # mm between footprint bboxes

# ----- D-21 placement parameters (mm) -----
MCU_CENTER = (109.5, 56.6)   # >=4.5 mm from every edge for the 23.35 mm LQFP-144 bbox
MCU_LAYER = pcbnew.B_Cu

report = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "phases": {}, "warnings": []}

# ------------------------------------------------------------------ baseline
if not os.path.exists(BASE):
    shutil.copy2(PCB, BASE)
    report["baseline_created"] = True
shutil.copy2(BASE, PCB)
board = pcbnew.LoadBoard(PCB)

# ------------------------------------------------------------------ netlist
root = ET.parse(NETLIST).getroot()
comps = {}
for c in root.iter("comp"):
    comps[c.get("ref")] = {"fp": c.findtext("footprint") or "", "value": c.findtext("value") or ""}
pad_net = {}          # (ref, pin) -> net
net_nodes = defaultdict(list)
for n in root.iter("net"):
    name = n.get("name")
    for node in n.findall("node"):
        pad_net[(node.get("ref"), node.get("pin"))] = name
        net_nodes[name].append((node.get("ref"), node.get("pin")))

# snapshot old pad nets (for renamed-net mapping)
old_pad_net = {}
for f in board.GetFootprints():
    for p in f.Pads():
        old_pad_net[(f.GetReference(), p.GetNumber())] = p.GetNetname()

# ------------------------------------------------------------------ phase A
def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    f = pcbnew.FootprintLoad(os.path.join(FPROOT, lib + ".pretty"), name)
    if f is None:
        raise SystemExit(f"footprint not found: {fpid}")
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    return f

pcb_fps = {f.GetReference(): f for f in board.GetFootprints()}
removed, added, replaced = [], [], []
for ref in sorted(set(pcb_fps) - set(comps)):
    board.RemoveNative(pcb_fps[ref]); removed.append(ref)
for ref in sorted(set(comps) & set(pcb_fps)):
    f = pcb_fps[ref]
    if f.GetFPIDAsString() != comps[ref]["fp"]:
        pos, rot, layer = f.GetPosition(), f.GetOrientationDegrees(), f.GetLayer()
        board.RemoveNative(f)
        nf = load_fp(comps[ref]["fp"])
        nf.SetReference(ref); nf.SetValue(comps[ref]["value"])
        nf.SetPosition(pos); nf.SetOrientationDegrees(rot)
        board.Add(nf); replaced.append(ref)
    elif f.GetValue() != comps[ref]["value"]:
        f.SetValue(comps[ref]["value"])
for ref in sorted(set(comps) - set(pcb_fps)):
    nf = load_fp(comps[ref]["fp"])
    nf.SetReference(ref); nf.SetValue(comps[ref]["value"])
    nf.SetPosition(V(60, 60))  # parked; placed in phase D
    board.Add(nf); added.append(ref)
report["phases"]["A"] = {"removed": removed, "added": added, "replaced": replaced}

# ------------------------------------------------------------------ phase B
fps = {f.GetReference(): f for f in board.GetFootprints()}
def get_net(name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n

unassigned = []
for ref, f in fps.items():
    for p in f.Pads():
        key = (ref, p.GetNumber())
        if key in pad_net:
            p.SetNet(get_net(pad_net[key]))
        else:
            p.SetNetCode(0)
            if not p.GetNumber() == "":
                unassigned.append(key)
report["phases"]["B"] = {"nets_in_netlist": len(net_nodes), "pads_without_net": unassigned}

# old net -> new net mapping via unchanged pads
old2new = defaultdict(set)
for key, old in old_pad_net.items():
    if key in pad_net and old:
        old2new[old].add(pad_net[key])

# ------------------------------------------------------------------ phase C
# nets whose membership changed (pad set differs from the baseline)
old_members = defaultdict(set)
for key, old in old_pad_net.items(): old_members[old].add(key)
new_members = defaultdict(set)
for key, new in pad_net.items(): new_members[new].add(key)

changed_nets = set()
for old, news in old2new.items():
    if len(news) != 1:
        changed_nets.add(old); continue
    new = next(iter(news))
    if old_members[old] != new_members[new]:
        changed_nets.add(old)
for old in old_members:
    if old and old not in old2new:
        changed_nets.add(old)

removed_tracks = 0; renamed_tracks = 0
for t in list(board.GetTracks()):
    old = t.GetNetname()
    if old in POWER_NETS:
        continue
    if old in changed_nets or old not in old2new:
        board.RemoveNative(t); removed_tracks += 1
    else:
        new = next(iter(old2new[old]))
        if new != old:
            t.SetNet(get_net(new)); renamed_tracks += 1
# power-net tracks: keep, but map name (none renamed) -> nothing to do

# dangling cleanup: remove segments/vias with an endpoint touching nothing
def build_index():
    idx = defaultdict(list)
    for f in board.GetFootprints():
        for p in f.Pads():
            idx[p.GetNetCode()].append(("pad", p))
    for t in board.GetTracks():
        idx[t.GetNetCode()].append(("trk", t))
    for z in board.Zones():
        if not z.GetIsRuleArea(): idx[z.GetNetCode()].append(("zone", z))
    return idx

def touches(pt, layer, item, self_item):
    if item is self_item: return False
    if item.GetClass() == "PCB_VIA":
        return item.GetPosition() == pt
    if item.GetClass() == "PCB_TRACK" or item.GetClass() == "PCB_ARC":
        if item.GetLayer() != layer: return False
        return item.GetStart() == pt or item.GetEnd() == pt
    if item.GetClass() == "ZONE":  # stub do baseline que termina dentro do cobre vertido da mesma net
        return item.IsOnLayer(layer) and item.GetFilledPolysList(layer).Contains(pt)
    # pad
    if not item.IsOnLayer(layer): return False
    return item.HitTest(pt)

dangling_removed = 0
def cleanup_dangling():
    global dangling_removed
    for _ in range(20):
        idx = build_index(); dirty = False
        for t in list(board.GetTracks()):
            if t.GetClass() == "PCB_VIA": continue
            items = [x for _, x in idx[t.GetNetCode()]]
            ok_s = any(touches(t.GetStart(), t.GetLayer(), it, t) for it in items)
            ok_e = any(touches(t.GetEnd(), t.GetLayer(), it, t) for it in items)
            if not (ok_s and ok_e):
                board.RemoveNative(t); dangling_removed += 1; dirty = True
        # vias with nothing attached on any layer
        idx = build_index()
        for t in list(board.GetTracks()):
            if t.GetClass() != "PCB_VIA": continue
            items = [x for _, x in idx[t.GetNetCode()] if x is not t]
            attached = sum(1 for it in items if it.GetClass() in ("PCB_TRACK", "PCB_ARC") and (it.GetStart() == t.GetPosition() or it.GetEnd() == t.GetPosition()))
            if attached < 2 and not any(it.GetClass() == "PCB_PAD" and it.HitTest(t.GetPosition()) for it in items) \
                    and not (attached == 1 and any(it.GetClass() == "ZONE" and any(it.IsOnLayer(L) and it.GetFilledPolysList(L).Contains(t.GetPosition()) for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)) for it in items)):
                board.RemoveNative(t); dangling_removed += 1; dirty = True
        if not dirty: break
cleanup_dangling()

# drop orphan nets (no pads)
used = {p.GetNetCode() for f in board.GetFootprints() for p in f.Pads()}
orphans = []
for name, n in list(board.GetNetInfo().NetsByName().items()):
    if n.GetNetCode() != 0 and n.GetNetCode() not in used:
        orphans.append(str(name))
# (pcbnew purges unused nets on save; just report)
report["phases"]["C"] = {"changed_nets": sorted(changed_nets), "tracks_removed": removed_tracks,
                         "tracks_renamed": renamed_tracks, "dangling_removed": dangling_removed,
                         "orphan_nets": orphans,
                         "tracks_left": len(board.GetTracks())}

# ------------------------------------------------------------------ phase E: alargar a placa para o sul
# (usuário autorizou aumentar a área; a fileira sul do U7 ficava a 6,5 mm da borda, com cristal + SMPS + Q1/Q2)
BOARD_GROW_S = 5.0   # mm acrescentados na borda inferior (y+)
_grow = {"dy": BOARD_GROW_S, "edge_points_moved": 0, "edge_before": None, "edge_after": None}
for d in board.GetDrawings():
    if d.GetLayerName() != "Edge.Cuts" or d.GetShape() != pcbnew.SHAPE_T_POLY: continue
    bb0 = board.GetBoardEdgesBoundingBox(); _grow["edge_before"] = (mm(bb0.GetBottom()))
    ymid = (bb0.GetTop() + bb0.GetBottom()) // 2
    poly = d.GetPolyShape()
    for oi in range(poly.OutlineCount()):
        ol = poly.Outline(oi)
        for i in range(ol.PointCount()):
            p = ol.CPoint(i)
            if p.y > ymid:   # só o lado sul: estica os lados retos, preserva os cantos arredondados
                ol.SetPoint(i, pcbnew.VECTOR2I(p.x, p.y + pcbnew.FromMM(BOARD_GROW_S))); _grow["edge_points_moved"] += 1
    d.SetPolyShape(poly)
_grow["edge_after"] = mm(board.GetBoardEdgesBoundingBox().GetBottom())
report["phases"]["E"] = _grow

# ------------------------------------------------------------------ phase D
fps = {f.GetReference(): f for f in board.GetFootprints()}
edge = board.GetBoardEdgesBoundingBox()
EDGE = (mm(edge.GetLeft()) + EDGE_MARGIN, mm(edge.GetTop()) + EDGE_MARGIN,
        mm(edge.GetRight()) - EDGE_MARGIN, mm(edge.GetBottom()) - EDGE_MARGIN)

def bbox_mm(f):
    bb = f.GetBoundingBox(False, False)
    return (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))

def overlaps(a, b, gap=COURTYARD_GAP):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])

def inside(a):
    return a[0] >= EDGE[0] and a[1] >= EDGE[1] and a[2] <= EDGE[2] and a[3] <= EDGE[3]

def is_th(f):
    return any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in f.Pads())

def place(f, x, y, rot, layer):
    if f.GetLayer() != layer:
        f.SetLayerAndFlip(layer)
    f.SetOrientationDegrees(0)
    f.SetPosition(V(x, y))
    f.SetOrientationDegrees(rot)

def blockers(layer, exclude=()):
    out = []
    for r, f in fps.items():
        if r in exclude: continue
        if f.GetLayer() == layer or is_th(f):
            bb = bbox_mm(f)
            if r == "U7":   # keep new parts outside the LQFP-144 courtyard (DRC courtyards_overlap)
                bb = (bb[0] - 0.25, bb[1] - 0.25, bb[2] + 0.25, bb[3] + 0.25)   # LQFP-144 courtyard
            out.append((r, bb))
    return out

def pad_pos(ref, num):
    p = fps[ref].FindPadByNumber(str(num))
    return (mm(p.GetPosition().x), mm(p.GetPosition().y))

def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

# --- D1: MCU orientation by ratsnest score
u7 = fps["U7"]
targets = defaultdict(list)   # net -> positions of non-U7 pads
for (ref, pin), net in pad_net.items():
    if ref == "U7" or net in POWER_NETS or net.startswith("unconnected") or ref not in fps or ref in added:
        continue
    targets[net].append(pad_pos(ref, pin))
best = None
for rot in (0, 90, 180, 270):
    place(u7, *MCU_CENTER, rot, MCU_LAYER)
    score = 0.0
    # support pins (SMPS, HSE, NRST, VDDA, VCAP) need room outside the pad row
    for sp in (15, 17, 25, 26, 27, 35, 36, 68, 140):
        pp = u7.FindPadByNumber(str(sp)).GetPosition()
        x, y = mm(pp.x), mm(pp.y)
        room = min(x - mm(edge.GetLeft()), mm(edge.GetRight()) - x, y - mm(edge.GetTop()), mm(edge.GetBottom()) - y)
        if room < 6.0: score += 1000
    for p in u7.Pads():
        net = p.GetNetname()
        if net in targets:
            pp = (mm(p.GetPosition().x), mm(p.GetPosition().y))
            score += min(dist(pp, t) for t in targets[net])
    if best is None or score < best[1]:
        best = (rot, score)
place(u7, *MCU_CENTER, best[0], MCU_LAYER)
report["phases"]["D"] = {"mcu": {"center": MCU_CENTER, "layer": "B.Cu", "rot": best[0], "score_mm": round(best[1], 1)}}

u7_pads = {p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in u7.Pads()}
cx, cy = MCU_CENTER
def outward(num, d):
    """point d mm outward from pad `num` (away from MCU centre), plus unit vector"""
    px, py = u7_pads[str(num)]
    dx, dy = px - cx, py - cy
    if abs(dx) > abs(dy):
        ux, uy = (1 if dx > 0 else -1), 0
    else:
        ux, uy = 0, (1 if dy > 0 else -1)
    return (px + ux * d, py + uy * d), (ux, uy)

placed_boxes = []   # for B.Cu new parts
def try_place(f, want, rot, layer, radius_step=0.5, max_r=12.0, exclude=()):
    """place f as close as possible to `want`, avoiding blockers; returns final pos"""
    blk = blockers(layer, exclude=exclude + (f.GetReference(),))
    cands = [(0, 0)]
    r = radius_step
    while r <= max_r:
        n = max(8, int(2 * math.pi * r / radius_step))
        for k in range(n):
            a = 2 * math.pi * k / n
            cands.append((r * math.cos(a), r * math.sin(a)))
        r += radius_step
    for dx, dy in cands:
        place(f, want[0] + dx, want[1] + dy, rot, layer)
        bb = bbox_mm(f)
        if not inside(bb): continue
        if any(overlaps(bb, b) for _, b in blk): continue
        return (want[0] + dx, want[1] + dy)
    report["warnings"].append(f"{f.GetReference()}: no collision-free spot near {want}")
    return None

def two_pin_rot(ux, uy, pin1_toward_mcu=True):
    """rotation for 2-pad SMD (pads along local X: pad1 at -x) so pad1 faces the MCU"""
    # local +x direction after rotation should equal outward (ux,uy) when pad1 toward mcu
    ang = math.degrees(math.atan2(-uy, ux))  # pcbnew: positive rot = CCW on screen with y down
    return ang % 360

def place_near_pin(ref, pin, d, rot_extra=0, flip_pads=False):
    want, (ux, uy) = outward(pin, d)
    rot = two_pin_rot(ux, uy)
    if flip_pads: rot = (rot + 180) % 360
    # on B.Cu the footprint is mirrored; compensate so pad1 still faces the MCU
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    for cand in (rot, (rot + 180) % 360):
        place(f, want[0], want[1], cand + rot_extra, MCU_LAYER)
        p1 = f.FindPadByNumber("1").GetPosition(); p2 = f.FindPadByNumber("2").GetPosition()
        d1 = dist((mm(p1.x), mm(p1.y)), u7_pads[str(pin)]); d2 = dist((mm(p2.x), mm(p2.y)), u7_pads[str(pin)])
        if d1 <= d2: break
    final = try_place(f, want, f.GetOrientationDegrees(), MCU_LAYER)
    return final

distances = {}
def pad_gap(pa, pb):
    """edge-to-edge gap between two pads (bounding boxes), mm"""
    a = pa.GetBoundingBox(); b = pb.GetBoundingBox()
    dx = max(0, max(a.GetLeft(), b.GetLeft()) - min(a.GetRight(), b.GetRight()))
    dy = max(0, max(a.GetTop(), b.GetTop()) - min(a.GetBottom(), b.GetBottom()))
    return math.hypot(mm(dx), mm(dy))
distances_cc = {}
def record(ref, pin, cap_pad="1"):
    pad = fps[ref].FindPadByNumber(cap_pad); p = pad.GetPosition()
    distances_cc[f"{ref}.{cap_pad}->U7.{pin}"] = round(dist((mm(p.x), mm(p.y)), u7_pads[str(pin)]), 2)
    distances[f"{ref}.{cap_pad}->U7.{pin}"] = round(pad_gap(pad, u7.FindPadByNumber(str(pin))), 2)

# --- D2: decoupling (pad1 = +3V3 side per schematic C_Small: pin1 top → net +3V3? verify from netlist)
def cap_pin_on_net(ref, net):
    for (r, pin), n in pad_net.items():
        if r == ref and n == net: return pin
    return None

VDD_PINS = [7, 13, 19, 32, 42, 56, 71, 79, 92, 106, 119, 129, 144, 91, 90]
DECOUP = [f"C{i}" for i in range(45, 60)]

# --- D3 (first, for priority): VCAP 2.2u (C39 @68, C40 @140); pin 103 fed by trace (documented)
for ref, pin in (("C39", 68), ("C40", 140)):
    place_near_pin(ref, pin, 1.8)
    record(ref, pin, cap_pin_on_net(ref, "VCAP"))
report["phases"]["D"]["vcap_note"] = "3 pinos VCAP (68,103,140), 2 capacitores no esquemático: pino 103 alimentado por trilha — verificar DS13311 §6.3.2 (um 2,2 µF por pino?)"

# --- D5 (before decoupling, for priority): SMPS L5 (VLXSMPS 15 -> VFBSMPS 17), C41 220p, C42 10u
# L5 com os pads LATERAIS (paralelos à fileira): pad1 VLXSMPS sob o pino 15, pad2 VFBSMPS sob o pino 17
place_near_pin("L5", 16, 3.0)
_lf = fps["L5"]; _lw = (mm(_lf.GetPosition().x), mm(_lf.GetPosition().y)); _lrot = _lf.GetOrientationDegrees()
for extra in (90, 270):
    place(_lf, _lw[0], _lw[1], _lrot + extra, MCU_LAYER)
    if dist(pad_pos("L5", cap_pin_on_net("L5", "VLXSMPS")), u7_pads["15"]) <= dist(pad_pos("L5", cap_pin_on_net("L5", "VFBSMPS")), u7_pads["15"]): break
try_place(_lf, _lw, _lf.GetOrientationDegrees(), MCU_LAYER)
record("L5", 15, cap_pin_on_net("L5", "VLXSMPS")); record("L5", 17, cap_pin_on_net("L5", "VFBSMPS"))
_lp = (mm(fps["L5"].GetPosition().x), mm(fps["L5"].GetPosition().y))
_w, (_ux, _uy) = outward(16, 2.4)
_px, _py = -_uy, _ux
# C41 (220 pF, VLXSMPS) e C42 (10 µF, VFBSMPS) ambos ABAIXO do L5 (para fora), cada um sob o seu pad do L5:
# deixa livre o corredor do pino 13 (+3V3) para a via ao sul da keepout do SW1 (y > 70.16)
_lvlx = pad_pos("L5", cap_pin_on_net("L5", "VLXSMPS")); _lvfb = pad_pos("L5", cap_pin_on_net("L5", "VFBSMPS"))
_c41_side = (_lvlx[0] + _ux * 1.6, _lvlx[1] + _uy * 1.6)
_c42_pos = (_lvfb[0] + _ux * 2.4, _lvfb[1] + _uy * 2.4)
for ref, pin, w, rot_base in (("C41", 15, _c41_side, two_pin_rot(_ux, _uy)), ("C42", 17, _c42_pos, two_pin_rot(_ux, _uy))):
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    hot = cap_pin_on_net(ref, "VLXSMPS" if pin == 15 else "VFBSMPS")
    tgt = pad_pos("L5", cap_pin_on_net("L5", "VLXSMPS" if pin == 15 else "VFBSMPS"))
    for cand in (rot_base, rot_base + 180):
        place(f, w[0], w[1], cand, MCU_LAYER)
        ph = pad_pos(ref, hot); po = pad_pos(ref, "2" if hot == "1" else "1")
        if dist(ph, tgt) <= dist(po, tgt): break
    try_place(f, w, f.GetOrientationDegrees(), MCU_LAYER, radius_step=0.4, max_r=5)
    record(ref, pin, hot)
    distances_cc[f"{ref}.{hot}->L5"] = round(dist(pad_pos(ref, hot), tgt), 2)

# --- D4: crystal Y1 between its load caps; caps hug the pad row (rule: < 4 mm to OSC pins)
want, (ux, uy) = outward(25, 3.75)
want2, _ = outward(26, 3.75)
yc = ((want[0] + want2[0]) / 2, (want[1] + want2[1]) / 2)
# nudge 0.5 mm away from the SMPS inductor (pin 16) so the load cap fits between Y1 and L5
_pl = (-uy, ux)
_sg = 1 if ((yc[0] - u7_pads["16"][0]) * _pl[0] + (yc[1] - u7_pads["16"][1]) * _pl[1]) > 0 else -1
yc = (yc[0] + _pl[0] * _sg * 0.5, yc[1] + _pl[1] * _sg * 0.5)
y1 = fps["Y1"]
if y1.GetLayer() != MCU_LAYER: y1.SetLayerAndFlip(MCU_LAYER)
# orient so pins 1 and 3 are nearest to 25 and 26 respectively
bestr = None
for cand in (0, 90, 180, 270):
    place(y1, yc[0], yc[1], cand, MCU_LAYER)
    bb_ = bbox_mm(y1)
    # long side (3.2 mm) must run along the MCU edge: only 5.8 mm of room to the board edge
    if (abs(ux) and (bb_[2] - bb_[0]) > (bb_[3] - bb_[1])) or (abs(uy) and (bb_[3] - bb_[1]) > (bb_[2] - bb_[0])): continue
    d = dist(pad_pos("Y1", 1), u7_pads["25"]) + dist(pad_pos("Y1", 3), u7_pads["26"])
    if bestr is None or d < bestr[0]: bestr = (d, cand)
place(y1, yc[0], yc[1], bestr[1], MCU_LAYER)
try_place(y1, yc, bestr[1], MCU_LAYER, radius_step=0.4, max_r=5)
ypos = (mm(y1.GetPosition().x), mm(y1.GetPosition().y))
px_, py_ = -uy, ux   # direction along the MCU edge
y13 = (pad_pos("Y1", 1)[0] - pad_pos("Y1", 3)[0], pad_pos("Y1", 1)[1] - pad_pos("Y1", 3)[1])
side1 = 1 if (y13[0] * px_ + y13[1] * py_) > 0 else -1   # which side (along edge) pin 1 is on
mid, _ = outward(25, 2.6)
mid2, _ = outward(26, 2.6)
mid = ((mid[0] + mid2[0]) / 2, (mid[1] + mid2[1]) / 2)
for ref, pin, sgn in (("C23", 25, side1), ("C24", 26, -side1)):
    # beside the crystal (along the MCU edge) but hugging the pad row, hot pad toward the MCU
    w = (ypos[0] * 0 + mid[0] + (ypos[0] - yc[0]) * 0 + px_ * sgn * 2.9 + (ypos[0] - (want[0] + want2[0]) / 2), mid[1] + py_ * sgn * 2.9 + (ypos[1] - (want[1] + want2[1]) / 2))
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    hot = cap_pin_on_net(ref, "HSE_IN" if pin == 25 else "HSE_OUT")
    for cand in (two_pin_rot(ux, uy), two_pin_rot(ux, uy) + 180):
        place(f, w[0], w[1], cand, MCU_LAYER)
        ph = f.FindPadByNumber(hot).GetPosition(); po = f.FindPadByNumber("2" if hot == "1" else "1").GetPosition()
        if dist((mm(ph.x), mm(ph.y)), u7_pads[str(pin)]) <= dist((mm(po.x), mm(po.y)), u7_pads[str(pin)]): break
    try_place(f, w, f.GetOrientationDegrees(), MCU_LAYER, radius_step=0.4, max_r=5)
    record(ref, pin, hot)
for yp_, mp_ in ((1, 25), (3, 26)):
    distances_cc[f"Y1.{yp_}->U7.{mp_}"] = round(dist(pad_pos("Y1", yp_), u7_pads[str(mp_)]), 2)
    distances[f"Y1.{yp_}->U7.{mp_}"] = round(pad_gap(y1.FindPadByNumber(str(yp_)), u7.FindPadByNumber(str(mp_))), 2)


# --- D6: VDDA: FB1, C43 1u, C44 100n near 35/36
place_near_pin("C44", 36, 2.6); record("C44", 36, cap_pin_on_net("C44", "VDDA"))
place_near_pin("C43", 35, 4.4); record("C43", 35, cap_pin_on_net("C43", "VDDA"))
place_near_pin("FB1", 36, 6.2); record("FB1", 36, cap_pin_on_net("FB1", "VDDA"))

# --- D7: NRST cap C38 @27
place_near_pin("C38", 27, 2.6); record("C38", 27, cap_pin_on_net("C38", "NRST"))

prev_pins = []
for ref, pin in zip(DECOUP, VDD_PINS):
    vpin = cap_pin_on_net(ref, "+3V3")
    # adjacent VDD pins (90/91/92): second/third row so the 0402s do not fight for the same spot
    near = [q for q in prev_pins if abs(pin - q) <= 3]
    d_out = 2.6 + 1.8 * len(near)
    prev_pins.append(pin)
    want, (ux, uy) = outward(pin, d_out)
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    best_rot = None
    for cand in (0, 90, 180, 270):
        place(f, want[0], want[1], cand, MCU_LAYER)
        pv = f.FindPadByNumber(vpin).GetPosition()
        dv = dist((mm(pv.x), mm(pv.y)), u7_pads[str(pin)])
        # cap axis perpendicular to the MCU edge: pad axis along (ux,uy)
        pg = f.FindPadByNumber("2" if vpin == "1" else "1").GetPosition()
        axis = (mm(pg.x) - mm(pv.x), mm(pg.y) - mm(pv.y))
        along = abs(axis[0] * ux + axis[1] * uy)
        key = (-along, dv)
        if best_rot is None or key < best_rot[0]: best_rot = (key, cand)
    place(f, want[0], want[1], best_rot[1], MCU_LAYER)
    _r = try_place(f, want, best_rot[1], MCU_LAYER, radius_step=0.4, max_r=4)
    if _r is not None:
        _pv = f.FindPadByNumber(vpin).GetPosition()
        if dist((mm(_pv.x), mm(_pv.y)), u7_pads[str(pin)]) > 4.0:
            report["warnings"].append("far"); _r = None
    if _r is None:
        # crowded row: put the cap on F.Cu right opposite the pad (via through to the pin)
        report["warnings"].pop()
        w2, _ = outward(pin, 1.2)
        f.SetLayerAndFlip(pcbnew.F_Cu)
        if try_place(f, w2, best_rot[1], pcbnew.F_Cu, radius_step=0.4, max_r=4) is None:
            report["warnings"].pop()
            f.SetLayerAndFlip(MCU_LAYER); try_place(f, want, best_rot[1], MCU_LAYER, radius_step=0.4, max_r=10)
        else:
            report["phases"]["D"].setdefault("decoupling_on_F_Cu", []).append(ref)
    record(ref, pin, vpin)

# bulk caps: 4.7u x3 at three corners-ish, 1u near VBAT(8)
for ref, pin in (("C60", 7), ("C61", 56), ("C62", 106), ("C63", 8)):
    vpin = cap_pin_on_net(ref, "+3V3")
    want, (ux, uy) = outward(pin, 4.6)
    place_near_pin(ref, pin, 4.6)
    record(ref, pin, vpin)


# --- D8: SWD J1 on B.Cu where GPS was
j1 = fps["J1"]
if j1.GetLayer() != MCU_LAYER: j1.SetLayerAndFlip(MCU_LAYER)
try_place(j1, (103.5, 40.5), 0, MCU_LAYER, max_r=8)

# --- D9: SBU conditioning near Q1/Q2 (B.Cu): R28/R29 series, D13/D14 clamps
for ref, want, rot in (("R28", (122.5, 65.0), 90), ("R29", (120.5, 65.0), 90),
                       ("D13", (125.5, 65.5), 0), ("D14", (120.0, 68.0), 0)):
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    try_place(f, want, rot, MCU_LAYER, max_r=8)

# --- D10: STB pull-ups R30..R33 under their transceiver (B.Cu)
for ref in ("R30", "R31", "R32", "R33"):
    stb_net = pad_net[(ref, "2")] if pad_net.get((ref, "2"), "").endswith("STB") else pad_net[(ref, "1")]
    tr = [r for (r, pin), n in pad_net.items() if n == stb_net and r.startswith("U") and r != "U7"]
    tp = (mm(fps[tr[0]].GetPosition().x), mm(fps[tr[0]].GetPosition().y))
    f = fps[ref]
    if f.GetLayer() != MCU_LAYER: f.SetLayerAndFlip(MCU_LAYER)
    try_place(f, tp, 90, MCU_LAYER, max_r=8)
    distances[f"{ref}->{tr[0]}"] = round(dist((mm(f.GetPosition().x), mm(f.GetPosition().y)), tp), 2)

# --- D11: clear baseline copper (any net) that now collides with pads of new/moved footprints
MOVED = set(added) | {"U7", "Y1", "C23", "C24"}
# D10b: 2-pad passives whose pad nets are swapped relative to the existing copper -> rotate 180°
swapped = []
for r, f in fps.items():
    if r in MOVED or len(list(f.Pads())) != 2 or is_th(f): continue
    p1, p2 = f.FindPadByNumber("1"), f.FindPadByNumber("2")
    if p1 is None or p2 is None: continue
    def touching_net(pad):
        nets = set()
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA" or not pad.IsOnLayer(t.GetLayer()): continue
            if pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()): nets.add(t.GetNetname())
        return nets
    n1, n2 = touching_net(p1), touching_net(p2)
    if (p2.GetNetname() in n1 and p1.GetNetname() not in n1) or (p1.GetNetname() in n2 and p2.GetNetname() not in n2):
        f.SetOrientationDegrees(f.GetOrientationDegrees() + 180); swapped.append(r)
report["phases"]["D"]["pads_swapped_rotated_180"] = swapped
cleared = 0
for r in MOVED:
    for pad in fps[r].Pads():
        box = pad.GetBoundingBox(); box.Inflate(MM(0.3))
        for t in list(board.GetTracks()):
            if t.GetNetCode() == pad.GetNetCode() and t.GetNetCode() != 0: continue
            if t.GetClass() != "PCB_VIA" and not pad.IsOnLayer(t.GetLayer()): continue
            if t.HitTest(box, False, 0):
                board.RemoveNative(t); cleared += 1
cleanup_dangling()
report["phases"]["D"]["copper_cleared_under_new_pads"] = cleared
report["phases"]["D"]["dangling_removed_total"] = dangling_removed

# ------------------------------------------------------------------ phase E
# collision report on both layers
MOVED = set(added) | {"U7", "Y1", "C23", "C24"}
coll = []
items = [(r, f.GetLayerName(), bbox_mm(f), is_th(f)) for r, f in fps.items()]

for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i], items[j]
        if (a[0] in MOVED or b[0] in MOVED) and (a[1] == b[1] or a[3] or b[3]) and overlaps(a[2], b[2], gap=0.0):
            coll.append((a[0], b[0]))
outside = [r for r, f in fps.items() if r in MOVED and not inside(bbox_mm(f))]
rules = {
    "vcap_lt_2mm": {k: v for k, v in distances.items() if k.startswith(("C39", "C40"))},
    "hse_lt_4mm": {k: v for k, v in distances.items() if k.startswith(("Y1", "C23", "C24"))},
    "decoupling": {k: v for k, v in distances.items() if k.startswith(tuple(DECOUP))},
}
viol = []
for k, v in rules["vcap_lt_2mm"].items():
    if v > 2.0: viol.append(f"{k}={v} > 2.0")
for k, v in rules["hse_lt_4mm"].items():
    if v > 4.0: viol.append(f"{k}={v} > 4.0")
report["phases"]["E"] = {"collisions": coll, "outside_edge": outside, "pad_gap_mm": distances, "center_to_center_mm": distances_cc,
                         "rule_violations": viol,
                         "footprints": len(fps), "nets": board.GetNetCount(),
                         "b_cu_footprints": sorted(r for r, f in fps.items() if f.GetLayer() == pcbnew.B_Cu)}

# zones: refill so GND pours wrap new pads
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
report["saved"] = PCB
# o snapshot do step5b (routing) passa a ser esta saída: descarta o antigo
_snap5a = os.path.join(PRJ, "snapshots", "HybridPanda.kicad_pcb.step5a")
if os.path.exists(_snap5a): os.remove(_snap5a); report["step5a_snapshot_reset"] = True
with open(REPORT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)
print(json.dumps({k: report["phases"][k] for k in ("A", "C")}, ensure_ascii=False)[:1500])
print("MCU", report["phases"]["D"]["mcu"])
print("collisions", coll); print("outside", outside); print("violations", viol)
print("warnings", report["warnings"])
print("distances", json.dumps(distances))
