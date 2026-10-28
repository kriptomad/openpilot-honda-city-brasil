# -*- coding: utf-8 -*-
"""STEP 5e - relayout do bloco leste (transceptores CAN / USB-C / USB-A) com alargamento da placa.

Motivo (D-33): o aglomerado U8/U9/D6/D7/P1/U11/U10/C30/C33/D13 nao deixava posicao de via fora dos pads
0402 (4 via-in-pad restantes apos fix_audit: D13.1, U1.2, C30.2, C33.2). O dono autorizou aumentar a
placa ("pode aumentar o tamanho da pcb ... vamos deixar mais tranquilo ao inves de lotar a placa").

O que faz (deterministico; corre DEPOIS de step5_update_pcb.py e ANTES de step5b_route.py):
  1. contorno Edge.Cuts: vertices com x > EDGE_SPLIT deslocam +DX (lado leste inteiro, cantos redondos preservados)
  2. bloco leste: todo footprint com centro x >= X_CUT desloca +DX (P1 e U3 continuam rentes a nova borda)
  3. trilhas/vias do baseline: extremidade sobre pad de footprint deslocado acompanha o footprint; extremidade
     livre com x >= X_CUT desloca +DX; o resto fica -> segmentos que atravessam X_CUT sao "esticados"
  4. zonas de cobre (nao GND geral, nao rule areas): vertices x >= X_CUT deslocam +DX; zona +5V In2 (C32/C33) desce
  5. ajustes finos EXTRA (folga entre courtyards): C30/C31 +2.0 mm (ficam a ~1,5 mm do pino 3 do transceptor),
     C33/C32 +1.0 mm ao sul (livra a via do pino 3), D13 +0.5/+0.3, Q1/Q2 -0.5/+0.6, R24 +1.0/-0.5
  6. desenhos (serigrafia, textos) com centro x >= X_CUT acompanham o bloco
  7. refill, grava HybridPanda.kicad_pcb, apaga o snapshot .step5a (o 5b cria um novo a partir desta saida),
     DRC rapido (kicad-cli) e relatorio hardware/reports/step5e_relayout_east.json

Idempotente: na 1.a execucao guarda HybridPanda.kicad_pcb.step5e_in (saida do 5a); depois parte sempre dele.
Uso: "C:\\Users\\costabr\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe" hardware\\scripts\\step5e_relayout_east.py [--dry] [--no-drc]
"""
import json, os, shutil, subprocess, sys, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
SNAP_IN = PCB + ".step5e_in"
SNAP_5A = os.path.join(os.path.dirname(PCB), "snapshots", "HybridPanda.kicad_pcb.step5a")
REPORT = os.path.join(ROOT, "hardware/reports", "step5e_relayout_east.json")
DRC_OUT = os.path.join(ROOT, "hardware/reports", "hybrid_DRC_step5e.json")
DRY = "--dry" in sys.argv
NO_DRC = "--no-drc" in sys.argv

# ----------------------------------------------------------------- parametros (mm)
DX = 3.0            # alargamento da placa para leste
EDGE_SPLIT = 115.0  # vertices do contorno com x > EDGE_SPLIT deslocam (lado leste; a placa vai de 91,9 a 139,5)
X_CUT = 123.0       # footprints com centro x >= X_CUT deslocam +DX. Fica entre os desacoplamentos B.Cu do U7
                    # (C55/C56/C57/C40 em x = 122,76) e Q1 (123,15) / R32 (123,76) / U8-U9 (124,1)
EXTRA = {           # ref: (dx, dy) ADICIONAIS ao deslocamento do bloco
    "C30": (2.0, 0.0),    # desacoplamento +5V do U8.3: 121,46 -> 123,46 (pad 2 a 1,5 mm do pino 3, via livre a oeste)
    "C31": (2.0, 0.0),    # idem U9.3
    "C33": (0.0, 1.0),    # desacoplamento +5V do U11.3: courtyard encostava ao U11 (via caia entre os dois pads)
    "C32": (0.0, 1.0),    # idem U10.3
    "D13": (0.5, 0.3),    # BAT54S B.Cu: afasta de R28 (0,55 -> 1,05 mm) e abre espaco para a via GND do pad 1
    "Q1": (-0.6, 0.0),    # transistores SBU: afastam-se de R24/U11 (sem dy: a trilha +5V F.Cu em y = 73,2 ficaria sob o pad 1;
    "Q2": (-0.6, 0.0),    # -1,0 encostava o pad 1 do Q2 a ponta de trilha +5V em 127,13;71,66)
    "R24": (0.0, -0.8),   # pull-up SBU1: bbox sobrepunha Q2 (sem dx: trilha +3V3 F.Cu vertical em x = 131,39)
}
KEEP = {"C40"}      # suporte do U7 (VCAP pino 140, B.Cu, centro em 123,46): nunca acompanha o bloco
DETACH = {"Q1", "Q2", "R24", "C30", "C31"}   # ajustes EXTRA cujas trilhas do baseline "esticadas" davam curto ou zig-zag
                               # (Q1/Q2/R24: SBU x +5V/+3V3; C30/C31: +5V U9.3 -> 121,9 -> C31.2 em zig-zag, tracks_crossing):
                               # as trilhas ligadas aos seus pads (e o que ficar pendurado) sao removidas -> Freerouting/5c religam
ZONE_5V_IN2_GROW_S = 1.5   # zona +5V In2 (alimenta C32/C33/U10.3/U11.3): desce para acompanhar C32/C33
CLUSTER = ["U8", "U9", "U10", "U11", "D5", "D6", "D7", "D8", "D9", "D13", "C26", "C27", "C28", "C29", "C30", "C31", "C32", "C33",
           "R24", "R28", "R29", "R30", "R31", "R32", "R33", "Q1", "Q2", "P1", "U3", "D14", "R23"]

def P(v): return (round(ToMM(v.x), 3), round(ToMM(v.y), 3))
def V(x, y): return VECTOR2I(FromMM(x), FromMM(y))

rep = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "params": {"DX": DX, "EDGE_SPLIT": EDGE_SPLIT, "X_CUT": X_CUT, "EXTRA": EXTRA,
                                                              "ZONE_5V_IN2_GROW_S": ZONE_5V_IN2_GROW_S}, "warnings": []}
W = rep["warnings"].append

# ----------------------------------------------------------------- snapshot de entrada (idempotencia)
hp.assert_inside_output(PCB)
if not os.path.exists(SNAP_IN):
    shutil.copy2(PCB, SNAP_IN); rep["snapshot_in_created"] = True
else:
    shutil.copy2(SNAP_IN, PCB); rep["snapshot_in_restored"] = True
board = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in board.GetFootprints()}
bb0 = board.GetBoardEdgesBoundingBox()
rep["edge_before"] = {"min": P(bb0.GetOrigin()), "max": P(bb0.GetEnd())}

# ----------------------------------------------------------------- deslocamento por footprint
disp = {}
for ref, f in fps.items():
    dx, dy = (DX, 0.0) if (ToMM(f.GetPosition().x) >= X_CUT and ref not in KEEP) else (0.0, 0.0)
    ex, ey = EXTRA.get(ref, (0.0, 0.0))
    if (dx + ex, dy + ey) != (0.0, 0.0): disp[ref] = (dx + ex, dy + ey)
for ref in EXTRA:
    if ref not in fps: W("EXTRA: %s nao existe" % ref)
rep["footprints_moved"] = {}

# pads (posicao ANTES de mover) para classificar extremidades de trilhas
pads = [(p, f.GetReference()) for f in board.GetFootprints() for p in f.Pads()]
def pad_at(pt, layer):
    """footprint cujo pad contem o ponto nessa camada (vias: qualquer camada de cobre)"""
    for p, ref in pads:
        if layer is not None and not p.IsOnLayer(layer): continue
        if p.GetBoundingBox().Contains(pt) and p.HitTest(pt, FromMM(0.005)): return ref
    return None
def node_disp(pt, layer):
    ref = pad_at(pt, layer)
    if ref is not None: return disp.get(ref, (0.0, 0.0)), ref
    return ((DX, 0.0) if ToMM(pt.x) >= X_CUT else (0.0, 0.0)), None

# ----------------------------------------------------------------- 3a. destacar trilhas dos footprints DETACH (antes de mover)
def _touch(pt, layer, it, me):
    if it is me: return False
    c = it.GetClass()
    if c == "PCB_VIA": return (it.GetPosition() - pt).EuclideanNorm() <= FromMM(0.01)
    if c in ("PCB_TRACK", "PCB_ARC"):
        if it.GetLayer() != layer: return False
        return (it.GetStart() - pt).EuclideanNorm() <= FromMM(0.01) or (it.GetEnd() - pt).EuclideanNorm() <= FromMM(0.01)
    if c == "ZONE": return it.IsOnLayer(layer) and it.GetFilledPolysList(layer).Contains(pt)
    return it.IsOnLayer(layer) and it.HitTest(pt, FromMM(0.005))   # pad
detached = []
if DETACH:
    det_pads = [p for p, ref in pads if ref in DETACH]
    det_nets = {p.GetNetCode() for p in det_pads}
    for t in list(board.GetTracks()):
        if t.GetClass() == "PCB_VIA": continue
        for p in det_pads:
            if p.IsOnLayer(t.GetLayer()) and (p.HitTest(t.GetStart(), FromMM(0.005)) or p.HitTest(t.GetEnd(), FromMM(0.005))):
                detached.append({"net": t.GetNetname(), "layer": board.GetLayerName(t.GetLayer()), "seg": [P(t.GetStart()), P(t.GetEnd())], "pad": p.GetParentFootprint().GetReference()})
                board.RemoveNative(t); break
    for _ in range(30):   # o que ficou pendurado nessas redes
        items = collections.defaultdict(list)
        for p, ref in pads: items[p.GetNetCode()].append(p)
        for t in board.GetTracks(): items[t.GetNetCode()].append(t)
        for z in board.Zones():
            if not z.GetIsRuleArea(): items[z.GetNetCode()].append(z)
        dirty = False
        for t in list(board.GetTracks()):
            if t.GetClass() == "PCB_VIA" or t.GetNetCode() not in det_nets: continue
            its = items[t.GetNetCode()]
            ok_s = any(_touch(t.GetStart(), t.GetLayer(), it, t) for it in its)
            ok_e = any(_touch(t.GetEnd(), t.GetLayer(), it, t) for it in its)
            if not (ok_s and ok_e):
                detached.append({"net": t.GetNetname(), "layer": board.GetLayerName(t.GetLayer()), "seg": [P(t.GetStart()), P(t.GetEnd())], "pad": None})
                board.RemoveNative(t); dirty = True
        if not dirty: break
rep["detached_tracks"] = detached

# ----------------------------------------------------------------- 3. trilhas e vias
stretched, moved_trk, moved_via = [], 0, 0
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        (dx, dy), ref = node_disp(t.GetPosition(), None)
        if (dx, dy) != (0.0, 0.0):
            t.SetPosition(t.GetPosition() + V(dx, dy)); moved_via += 1
        continue
    (dsx, dsy), rs = node_disp(t.GetStart(), t.GetLayer())
    (dex, dey), re_ = node_disp(t.GetEnd(), t.GetLayer())
    if (dsx, dsy) == (dex, dey) == (0.0, 0.0): continue
    if (dsx, dsy) != (dex, dey):
        stretched.append({"net": t.GetNetname(), "layer": board.GetLayerName(t.GetLayer()), "from": [P(t.GetStart()), P(t.GetEnd())],
                          "d_start": (dsx, dsy), "d_end": (dex, dey), "pad_start": rs, "pad_end": re_, "w": round(ToMM(t.GetWidth()), 3)})
    if (dsx, dsy) != (0.0, 0.0): t.SetStart(t.GetStart() + V(dsx, dsy))
    if (dex, dey) != (0.0, 0.0): t.SetEnd(t.GetEnd() + V(dex, dey))
    moved_trk += 1
rep["tracks"] = {"moved_or_stretched": moved_trk, "vias_moved": moved_via, "stretched": stretched}

# ----------------------------------------------------------------- 2. footprints
for ref, (dx, dy) in disp.items():
    f = fps[ref]; old = f.GetPosition()
    f.SetPosition(old + V(dx, dy))
    rep["footprints_moved"][ref] = {"from": P(old), "to": P(f.GetPosition()), "d": (dx, dy), "layer": f.GetLayerName(), "value": f.GetValue()}

# ----------------------------------------------------------------- 1. contorno
edge_pts = 0
for d in board.GetDrawings():
    if d.GetLayerName() != "Edge.Cuts": continue
    if d.GetShape() == pcbnew.SHAPE_T_POLY:
        poly = d.GetPolyShape()
        for oi in range(poly.OutlineCount()):
            ol = poly.Outline(oi)
            for i in range(ol.PointCount()):
                p = ol.CPoint(i)
                if ToMM(p.x) > EDGE_SPLIT: ol.SetPoint(i, VECTOR2I(p.x + FromMM(DX), p.y)); edge_pts += 1
        d.SetPolyShape(poly)
    elif d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        s, e = d.GetStart(), d.GetEnd()
        if ToMM(s.x) > EDGE_SPLIT: d.SetStart(VECTOR2I(s.x + FromMM(DX), s.y)); edge_pts += 1
        if ToMM(e.x) > EDGE_SPLIT: d.SetEnd(VECTOR2I(e.x + FromMM(DX), e.y)); edge_pts += 1
    else:
        W("Edge.Cuts com forma %s nao tratada" % d.GetShapeStr())
# ----------------------------------------------------------------- 6. outros desenhos (serigrafia/textos) do bloco
drw_moved = 0
for d in board.GetDrawings():
    if d.GetLayerName() == "Edge.Cuts": continue
    c = d.GetBoundingBox().GetCenter()
    if ToMM(c.x) >= X_CUT: d.Move(V(DX, 0)); drw_moved += 1
bb1 = board.GetBoardEdgesBoundingBox()
rep["edge_after"] = {"min": P(bb1.GetOrigin()), "max": P(bb1.GetEnd()), "vertices_moved": edge_pts,
                     "size_mm": (round(ToMM(bb1.GetWidth()), 3), round(ToMM(bb1.GetHeight()), 3))}
rep["drawings_moved"] = drw_moved

# ----------------------------------------------------------------- 4. zonas
zones_changed = []
for z in board.Zones():
    if z.GetIsRuleArea(): continue
    zb = z.GetBoundingBox()
    if ToMM(zb.GetWidth()) > 50: continue   # zona GND geral (maior que a placa): nao precisa de alteracao
    ol = z.Outline(); n = 0
    grow_s = z.GetNetname() == "+5V" and z.IsOnLayer(pcbnew.In2_Cu) and ToMM(zb.GetTop()) > 68
    ymid = ToMM((zb.GetTop() + zb.GetBottom()) // 2)
    for oi in range(ol.OutlineCount()):
        o = ol.Outline(oi)
        for i in range(o.PointCount()):
            p = o.CPoint(i); nx, ny = p.x, p.y
            if ToMM(p.x) >= X_CUT: nx = p.x + FromMM(DX); n += 1
            if grow_s and ToMM(p.y) > ymid: ny = p.y + FromMM(ZONE_5V_IN2_GROW_S); n += 1
            if (nx, ny) != (p.x, p.y): o.SetPoint(i, VECTOR2I(nx, ny))
    if n:
        z.HatchBorder()
        if hasattr(z, "CacheBoundingBox"): z.CacheBoundingBox()
        zones_changed.append({"net": z.GetNetname(), "layers": [board.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                              "bbox_before": [P(zb.GetOrigin()), P(zb.GetEnd())], "bbox_after": [P(z.GetBoundingBox().GetOrigin()), P(z.GetBoundingBox().GetEnd())],
                              "vertices_changed": n, "grow_s": ZONE_5V_IN2_GROW_S if grow_s else 0})
rep["zones"] = zones_changed

# ----------------------------------------------------------------- verificacoes geometricas
def crt(f):
    c = f.GetCourtyard(pcbnew.F_CrtYd if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd)
    if c.OutlineCount() == 0:
        return f.GetBoundingBox(False, False)
    return c.BBox()
def gap(a, b):
    dx = max(0, max(a.GetLeft(), b.GetLeft()) - min(a.GetRight(), b.GetRight()))
    dy = max(0, max(a.GetTop(), b.GetTop()) - min(a.GetBottom(), b.GetBottom()))
    return round(ToMM(int((dx * dx + dy * dy) ** 0.5)), 3)
gaps = []
cl = [r for r in CLUSTER if r in fps]
for i in range(len(cl)):
    for j in range(i + 1, len(cl)):
        a, b = fps[cl[i]], fps[cl[j]]
        if a.GetLayer() != b.GetLayer(): continue
        g = gap(crt(a), crt(b))
        if g < 1.0: gaps.append({"a": cl[i], "b": cl[j], "layer": a.GetLayerName(), "gap_mm": g})
rep["courtyard_gaps_below_1mm"] = sorted(gaps, key=lambda x: x["gap_mm"])
L, T, R, B = ToMM(bb1.GetLeft()), ToMM(bb1.GetTop()), ToMM(bb1.GetRight()), ToMM(bb1.GetBottom())
outside = []
for ref, f in fps.items():
    b = f.GetBoundingBox(False, False)
    if ToMM(b.GetRight()) > R or ToMM(b.GetLeft()) < L or ToMM(b.GetTop()) < T or ToMM(b.GetBottom()) > B:
        outside.append({"ref": ref, "bbox": [P(b.GetOrigin()), P(b.GetEnd())]})
rep["footprints_bbox_outside_edge"] = outside   # esperado: P1 e U3 (conectores de borda, como no baseline)
# distancia desacoplamento -> pino VDD do transceptor (pad a pad, centro a centro)
def pad(ref, n): return next(p for p in fps[ref].Pads() if p.GetNumber() == str(n))
rep["decoupling_cc_mm"] = {}
for cap, ic, pin in (("C30", "U8", 3), ("C31", "U9", 3), ("C33", "U11", 3), ("C32", "U10", 3), ("C26", "U8", 5), ("C27", "U9", 5), ("C29", "U11", 5), ("C28", "U10", 5)):
    pc = next((p for p in fps[cap].Pads() if p.GetNetname() == pad(ic, pin).GetNetname()), None)
    if pc is None: W("%s sem pad na rede de %s.%d" % (cap, ic, pin)); continue
    rep["decoupling_cc_mm"]["%s.%s->%s.%d" % (cap, pc.GetNumber(), ic, pin)] = round(ToMM((pc.GetPosition() - pad(ic, pin).GetPosition()).EuclideanNorm()), 2)

# ----------------------------------------------------------------- 7. refill, gravar, DRC
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
rep["unconnected_after"] = board.GetConnectivity().GetUnconnectedCount(True)
if not DRY:
    pcbnew.SaveBoard(PCB, board)
    if os.path.exists(SNAP_5A): os.remove(SNAP_5A); rep["step5a_snapshot_removed"] = True
    if not NO_DRC:
        r = subprocess.run([str(hp.KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", DRC_OUT, PCB], capture_output=True, text=True)
        d = json.load(open(DRC_OUT, encoding="utf-8"))
        c = collections.Counter(v["type"] for v in d["violations"])
        rep["drc"] = {"unconnected_items": len(d["unconnected_items"]), "by_type": dict(c.most_common()),
                      "copper_issues": [(v["type"], v["description"], [P(VECTOR2I(int(i["pos"]["x"] * 1e6), int(i["pos"]["y"] * 1e6))) for i in v["items"] if "pos" in i])
                                        for v in d["violations"] if v["type"] in ("clearance", "shorting_items", "hole_clearance", "copper_edge_clearance", "courtyards_overlap", "track_dangling", "via_dangling", "tracks_crossing")]}
        ref5a = os.path.join(ROOT, "hardware/reports", "hybrid_DRC_step5a.json")
        if os.path.exists(ref5a):
            c0 = collections.Counter(v["type"] for v in json.load(open(ref5a, encoding="utf-8"))["violations"])
            rep["drc"]["delta_vs_step5a"] = {k: c[k] - c0.get(k, 0) for k in set(c) | set(c0) if c[k] != c0.get(k, 0)}
with open(REPORT, "w", encoding="utf-8") as fh: json.dump(rep, fh, indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in rep.items() if k not in ("tracks", "footprints_moved", "zones")}, indent=1, ensure_ascii=False, default=str))
print("moved footprints:", len(rep["footprints_moved"]), "stretched tracks:", len(stretched), "zones changed:", len(zones_changed))
