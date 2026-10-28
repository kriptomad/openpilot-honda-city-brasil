# -*- coding: utf-8 -*-
"""
Correccao dos achados da AUDITORIA_FINAL (final_audit.py), do maior para o menor risco:

  1. via-in-pad : vias cujo FURO fica a menos de HOLE_PAD_CLR da borda de um pad SMD sao movidas para fora
                  do pad (busca radial), as trilhas ligadas a via acompanham e um stub liga pad -> via;
  2. courtyard  : D7 x U9 (desloca D7 em +X ate os courtyards nao se tocarem; trilhas ligadas acompanham);
                  D8 courtyard 0,02 mm fora da borda (desloca em -X);
  3. fiduciais  : 3 em F.Cu + 3 em B.Cu (pad 1 mm, mascara 2 mm, rule-area sem cobre) em cantos livres;
  4. +3V3 fina  : segmentos de +3V3 < 0,20 mm alargados para 0,20 mm quando a folga permite.

Autor: Bruno Costa
Uso: python fix_audit.py [--dry]  (python do KiCad 10). Relatorio: hardware\\reports\fix_audit.json
Depois correr: kicad-cli drc, step7_validate.py, step8_fabricate.py, final_audit.py.
"""
import os, sys, json, math, time, subprocess, collections
T0 = time.time()
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
REPORT = os.path.join(ROOT, "hardware/reports", "fix_audit.json")
DRY = "--dry" in sys.argv
DEBUG = sys.argv[sys.argv.index("--debug") + 1] if "--debug" in sys.argv else None
DBG = collections.Counter() if False else None
HOLE_PAD_CLR = 0.15      # folga minima furo-da-via -> borda do pad SMD (furo fora da abertura de mascara)
VIA_CLR = 0.12           # folga cobre via -> cobre de outra rede (clearance do projecto 0,05; FR usou 0,12)
LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

board = pcbnew.LoadBoard(PCB)
g = {"PRELOADED_BOARD": board, "AS_LIBRARY": True, "__file__": os.path.join(ROOT, "hardware/scripts", "step5c_fix_unrouted.py"), "__name__": "step5c_lib"}
with open(g["__file__"], encoding="utf-8") as f: exec(compile(f.read(), g["__file__"], "exec"), g)
via_collides, seg_collides, plane_ok, add_track, add_via = g["via_collides"], g["seg_collides"], g["plane_ok"], g["add_track"], g["add_via"]

HOLE_CLR = 0.25
class Index:
    """indice de cobre/furos com pre-filtro por bbox (via_collides/seg_collides do 5c sao exaustivos e lentos)."""
    def __init__(self):
        self.items = []   # (bbox, layer, netcode, shape)
        self.holes = []   # (pos, r_mm, netcode, is_via)
        for p in [q for f in board.GetFootprints() for q in f.Pads()]:
            for l in LAYERS4:
                if p.IsOnLayer(l): self.items.append((p.GetBoundingBox(), l, p.GetNetCode(), p.GetEffectiveShape(l)))
            if p.GetDrillSize().x > 0: self.holes.append((p.GetPosition(), ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, p.GetNetCode(), False))
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                for l in LAYERS4: self.items.append((t.GetBoundingBox(), l, t.GetNetCode(), t.GetEffectiveShape(l)))
                self.holes.append((t.GetPosition(), ToMM(t.GetDrill()) / 2, t.GetNetCode(), True))
            else: self.items.append((t.GetBoundingBox(), t.GetLayer(), t.GetNetCode(), t.GetEffectiveShape(t.GetLayer())))
        self.keep = [z for z in board.Zones() if z.GetIsRuleArea()]
    def _near(self, bb, pos, r):
        return not (bb.GetRight() + r < pos.x or bb.GetLeft() - r > pos.x or bb.GetBottom() + r < pos.y or bb.GetTop() - r > pos.y)
    def via_ok(self, pos, dia, drill, nc, clr=VIA_CLR, skip=None):
        shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2)); hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2)); R = FromMM(dia / 2 + max(clr, HOLE_CLR) + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowVias() and z.Outline().Collide(shp, FromMM(clr)): return False
        for bb, l, n, s in self.items:
            if n == nc or not self._near(bb, pos, R): continue
            if s.Collide(shp, FromMM(clr)) or s.Collide(hole, FromMM(HOLE_CLR)): return False
        for hp, hr, n, isv in self.holes:
            if skip is not None and hp == skip: continue
            if dist(hp, pos) < hr + drill / 2 + HOLE_CLR + 0.02: return False
        return True
    def seg_ok(self, a, b, w, layer, nc, clr=0.10):
        shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(w)); bb = shp.BBox(); R = FromMM(max(clr, HOLE_CLR) + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(0.1)): return False
        for ib, l, n, s in self.items:
            if n == nc or l != layer: continue
            if ib.GetRight() + R < bb.GetLeft() or ib.GetLeft() - R > bb.GetRight() or ib.GetBottom() + R < bb.GetTop() or ib.GetTop() - R > bb.GetBottom(): continue
            if s.Collide(shp, FromMM(clr)): return False
        for hp, hr, n, isv in self.holes:
            if n == nc: continue
            if shp.Collide(pcbnew.SHAPE_CIRCLE(hp, FromMM(hr)), FromMM(HOLE_CLR)): return False
        return True
IDX = Index()

rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "via_in_pad": [], "courtyard": [], "fiducials": [], "thin_3v3": [], "warnings": []}
W = rep["warnings"].append
def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def P(v): return "%.2f,%.2f" % (ToMM(v.x), ToMM(v.y))
def dist(a, b): return ToMM((a - b).EuclideanNorm())
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline, True)
def inside_board(pos, margin=0.5):
    if not outline.Contains(pos): return False
    oc = outline.Outline(0)
    return not any(oc.CSegment(k).Distance(pos) < FromMM(margin) for k in range(oc.SegmentCount()))
def all_pads(): return [p for f in board.GetFootprints() for p in f.Pads()]
def vias(): return [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
def tracks(): return [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
def smd_layer(p): return pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu

# ------------------------------------------------------------------ 1. via-in-pad
def hole_in_pad(v, pos=None, hclr=None):
    """pads SMD cuja borda fica a < HOLE_PAD_CLR do furo da via (em pos ou na posicao actual)."""
    pos = pos or v.GetPosition(); hole = pcbnew.SHAPE_CIRCLE(pos, v.GetDrill() // 2); hits = []
    for p in all_pads():
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
        l = smd_layer(p)
        if p.GetBoundingBox().Inflate(FromMM(1.0)).Contains(pos) and p.GetEffectiveShape(l).Collide(hole, FromMM(hclr if hclr is not None else HOLE_PAD_CLR)): hits.append(p)
    return hits

def attached_tracks(pos):
    return [(t, "S" if t.GetStart() == pos else "E") for t in tracks() if t.GetStart() == pos or t.GetEnd() == pos]

def candidates(v, pad, reach=1.6, hclr=HOLE_PAD_CLR):
    """posicoes em anel a volta do pad, ordenadas pela distancia a via original."""
    c = pad.GetPosition(); sz = pad.GetSize(); r_via = ToMM(v.GetWidth()) / 2; r_hole = ToMM(v.GetDrill()) / 2
    half = max(ToMM(sz.x), ToMM(sz.y)) / 2
    out = []
    for k in range(32):
        a = 2 * math.pi * k / 32
        d = half + r_hole + hclr + 0.02
        while d < half + r_via + reach:
            pos = mm(ToMM(c.x) + d * math.cos(a), ToMM(c.y) + d * math.sin(a)); out.append(pos); d += 0.1
    out.sort(key=lambda p: dist(p, v.GetPosition()))
    return out

def move_via(v, pad, reach=1.6, hclr=HOLE_PAD_CLR, dia_override=None):
    global IDX
    nc = v.GetNetCode(); net = v.GetNetname(); dia = dia_override or ToMM(v.GetWidth()); drill = ToMM(v.GetDrill())
    old = v.GetPosition(); att = attached_tracks(old); lay = smd_layer(pad)
    stub_w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8)
    # a via e necessaria? se so liga trilhas de uma camada e nao e ligacao a plano, mesmo assim mantemos (conservador)
    for pos in candidates(v, pad, reach, hclr):
        if not inside_board(pos): continue
        if hole_in_pad(v, pos, hclr): continue
        # cobre/furo da via vs outras redes (via original ignorada: mesma rede)
        if not IDX.via_ok(pos, dia, drill, nc, VIA_CLR, skip=old): continue
        if not plane_ok(net, pos) and net in ("+3V3", "+5V"):
            # via fora da zona do plano: so aceitavel se a via tiver trilhas em >=2 camadas (serve de transicao)
            if len({t.GetLayer() for t, _ in att}) < 2: continue
        # trilhas ligadas acompanham
        ok = True
        for t, end in att:
            a, b = (pos, t.GetEnd()) if end == "S" else (t.GetStart(), pos)
            if a == b: continue
            if not IDX.seg_ok(a, b, ToMM(t.GetWidth()), t.GetLayer(), nc): ok = False; break
        if not ok: continue
        # stub pad -> via na camada do pad
        if not IDX.seg_ok(pad.GetPosition(), pos, stub_w, lay, nc): continue
        # hole-to-hole com a propria via antiga nao conta (vai mover); vs outras vias ja em via_collides
        if DRY: return pos, "dry"
        v.SetPosition(pos); v.SetLocked(False)
        if dia_override: v.SetWidth(FromMM(dia_override))
        for t, end in att:
            (t.SetStart if end == "S" else t.SetEnd)(pos)
            if t.GetStart() == t.GetEnd(): board.Remove(t)
        add_track(pad.GetPosition(), pos, stub_w, lay, nc)
        IDX = Index()
        return pos, "moved"
    return None, "sem posicao"

def move_via_grid(v, pad, reach=3.0, hclr=0.10, dia=0.5):
    global IDX
    nc = v.GetNetCode(); net = v.GetNetname(); drill = ToMM(v.GetDrill()); old = v.GetPosition(); att = attached_tracks(old); lay = smd_layer(pad)
    stub_w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8); c = pad.GetPosition()
    cands = [mm(ToMM(c.x) + i / 10, ToMM(c.y) + j / 10) for i in range(-int(reach * 10), int(reach * 10) + 1) for j in range(-int(reach * 10), int(reach * 10) + 1)]
    cands.sort(key=lambda p: dist(p, old))
    for pos in cands:
        if not inside_board(pos) or hole_in_pad(v, pos, hclr): continue
        if not IDX.via_ok(pos, dia, drill, nc, VIA_CLR, skip=old): continue
        if net in ("+3V3", "+5V") and not plane_ok(net, pos) and len({t.GetLayer() for t, _ in att}) < 2: continue
        if not all(IDX.seg_ok(*((pos, t.GetEnd()) if e == "S" else (t.GetStart(), pos)), ToMM(t.GetWidth()), t.GetLayer(), nc) for t, e in att if (pos != (t.GetEnd() if e == "S" else t.GetStart()))): continue
        paths = [[c, pos], [c, VECTOR2I(pos.x, c.y), pos], [c, VECTOR2I(c.x, pos.y), pos]]
        path = next((pth for pth in paths if all(a == b or IDX.seg_ok(a, b, stub_w, lay, nc) for a, b in zip(pth, pth[1:]))), None)
        if path is None: continue
        v.SetPosition(pos); v.SetLocked(False); v.SetWidth(FromMM(dia))
        for t, e in att:
            (t.SetStart if e == "S" else t.SetEnd)(pos)
            if t.GetStart() == t.GetEnd(): board.Remove(t)
        for a, b in zip(path, path[1:]): add_track(a, b, stub_w, lay, nc)
        IDX = Index(); return pos, "moved"
    return None, "sem posicao"

def slide_via(v, pad, hclr=0.10, dia=0.5):
    """desliza a via ao longo de uma trilha ligada que nao esta na camada do pad; as outras trilhas ligadas
    sao reajustadas (ponta movida) e o pad e religado por stub directo/L na sua camada."""
    global IDX
    nc = v.GetNetCode(); drill = ToMM(v.GetDrill()); old = v.GetPosition(); att = attached_tracks(old); lay = smd_layer(pad)
    stub_w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8); c = pad.GetPosition()
    for rail, e in att:
        if rail.GetLayer() == lay: continue
        far = rail.GetEnd() if e == "S" else rail.GetStart(); L = dist(old, far)
        k = 0.1
        while k < L - 0.05:
            pos = VECTOR2I(int(old.x + (far.x - old.x) * k / L), int(old.y + (far.y - old.y) * k / L)); k += 0.05
            dbg = DEBUG == "%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber())
            if not inside_board(pos): dbg and print("  ", P(pos), "fora"); continue
            if hole_in_pad(v, pos, hclr): dbg and print("  ", P(pos), "in-pad", [q.GetParentFootprint().GetReference()+"."+q.GetNumber() for q in hole_in_pad(v, pos, hclr)]); continue
            if not IDX.via_ok(pos, dia, drill, nc, VIA_CLR, skip=old): dbg and print("  ", P(pos), "via colide"); continue
            others = [(t, ee) for t, ee in att if t is not rail]
            if not all(IDX.seg_ok(*((pos, t.GetEnd()) if ee == "S" else (t.GetStart(), pos)), ToMM(t.GetWidth()), t.GetLayer(), nc) for t, ee in others if not (t.GetLayer() == lay and (t.GetEnd() if ee == "S" else t.GetStart()) == c)): continue
            paths = [[c, pos], [c, VECTOR2I(pos.x, c.y), pos], [c, VECTOR2I(c.x, pos.y), pos]]
            path = next((pth for pth in paths if all(a == b or IDX.seg_ok(a, b, stub_w, lay, nc) for a, b in zip(pth, pth[1:]))), None)
            if path is None: dbg and print("  ", P(pos), "sem stub"); continue
            v.SetPosition(pos); v.SetLocked(False); v.SetWidth(FromMM(dia))
            (rail.SetStart if e == "S" else rail.SetEnd)(pos)
            for t, ee in others:
                if t.GetLayer() == lay and (t.GetEnd() if ee == "S" else t.GetStart()) == c: board.Remove(t); continue  # stub antigo pad->via
                (t.SetStart if ee == "S" else t.SetEnd)(pos)
                if t.GetStart() == t.GetEnd(): board.Remove(t)
            for a, b in zip(path, path[1:]): add_track(a, b, stub_w, lay, nc)
            IDX = Index(); return pos, "moved"
    return None, "sem posicao"

def bridge_via(v, pad, reach=2.5, hclr=0.10, dia=0.5):
    """nao roda as trilhas: acrescenta um segmento antiga->nova na camada de cada trilha ligada (excepto a camada
    do pad, onde o stub e refeito a partir do pad). Mais permissivo em zonas densas."""
    global IDX
    nc = v.GetNetCode(); drill = ToMM(v.GetDrill()); old = v.GetPosition(); att = attached_tracks(old); lay = smd_layer(pad)
    stub_w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8); c = pad.GetPosition()
    rails = {}
    for t, e in att:
        if t.GetLayer() == lay and (t.GetEnd() if e == "S" else t.GetStart()) == c: continue
        rails.setdefault(t.GetLayer(), max(rails.get(t.GetLayer(), 0), ToMM(t.GetWidth())))
    cands = [mm(ToMM(old.x) + i / 10, ToMM(old.y) + j / 10) for i in range(-int(reach * 10), int(reach * 10) + 1) for j in range(-int(reach * 10), int(reach * 10) + 1)]
    cands.sort(key=lambda p: dist(p, old))
    for pos in cands:
        if not inside_board(pos) or hole_in_pad(v, pos, hclr) or not IDX.via_ok(pos, dia, drill, nc, VIA_CLR, skip=old): continue
        if not all(IDX.seg_ok(old, pos, w, l, nc) for l, w in rails.items()): continue
        paths = [[c, pos], [c, VECTOR2I(pos.x, c.y), pos], [c, VECTOR2I(c.x, pos.y), pos]]
        path = next((pth for pth in paths if all(a == b or IDX.seg_ok(a, b, stub_w, lay, nc) for a, b in zip(pth, pth[1:]))), None)
        if path is None: continue
        for t, e in att:
            if t.GetLayer() == lay and (t.GetEnd() if e == "S" else t.GetStart()) == c: board.Remove(t)
        v.SetPosition(pos); v.SetLocked(False); v.SetWidth(FromMM(dia))
        for l, w in rails.items(): add_track(old, pos, w, l, nc)
        for a, b in zip(path, path[1:]): add_track(a, b, stub_w, lay, nc)
        IDX = Index(); return pos, "moved"
    return None, "sem posicao"

def link_to_net_copper(pad, reach=3.0):
    """trilha directa/L do pad ate pad/via/trilha da mesma rede na camada do pad (sem via nova)."""
    global IDX
    nc = pad.GetNetCode(); lay = smd_layer(pad); c = pad.GetPosition(); w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8)
    targets = []
    for p in all_pads():
        if p.GetNetCode() == nc and p is not pad and p.IsOnLayer(lay) and dist(p.GetPosition(), c) < reach: targets.append(p.GetPosition())
    for t in board.GetTracks():
        if t.GetNetCode() != nc or not t.IsOnLayer(lay): continue
        for q in ((t.GetPosition(),) if t.GetClass() == "PCB_VIA" else (t.GetStart(), t.GetEnd())):
            if dist(q, c) < reach: targets.append(q)
    targets.sort(key=lambda q: dist(q, c))
    for q in targets:
        paths = [[c, q], [c, VECTOR2I(q.x, c.y), q], [c, VECTOR2I(c.x, q.y), q]]
        path = next((pth for pth in paths if all(a == b or IDX.seg_ok(a, b, w, lay, nc) for a, b in zip(pth, pth[1:]))), None)
        if path is None: continue
        for a, b in zip(path, path[1:]): add_track(a, b, w, lay, nc)
        IDX = Index(); return True
    return False

n_vip = 0
for v in vias():
    hits = hole_in_pad(v)
    if not hits: continue
    n_vip += 1
    pad = min(hits, key=lambda p: dist(p.GetPosition(), v.GetPosition()))
    other = [p for p in hits if p.GetNetCode() != v.GetNetCode()]
    if other: W("via %s dentro de pad de OUTRA rede: %s" % (v.GetNetname(), other[0].GetParentFootprint().GetReference()))
    pos, how = move_via(v, pad)
    rep["via_in_pad"].append({"via": "%s @%s d%.2f/%.2f" % (v.GetNetname(), P(v.GetPosition() if how != "moved" else pos), ToMM(v.GetWidth()), ToMM(v.GetDrill())),
                              "pad": "%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber()), "from": P(v.GetPosition()) if how != "moved" else None,
                              "to": P(pos) if pos else None, "result": how})

def unconnected():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(True)
if not DRY:
    base_unc = unconnected()
    for x in rep["via_in_pad"]:
        if x["result"] != "sem posicao": continue
        v = next((q for q in vias() if P(q.GetPosition()) == x["from"]), None)
        if v is None: continue
        pad = min((p for f in board.GetFootprints() for p in f.Pads() if "%s.%s" % (f.GetReference(), p.GetNumber()) == x["pad"]), key=lambda p: dist(p.GetPosition(), v.GetPosition()))
        if any(min(ToMM(q.GetSize().x), ToMM(q.GetSize().y)) >= 2.0 for q in hole_in_pad(v)):
            x["result"] = "aceite (pad termico >= 2 mm; via-in-pad e pratica normal em exposed pad)"; continue
        # a) via redundante (sem trilhas ligadas) e a ligacao mantem-se sem ela -> remover
        if not attached_tracks(v.GetPosition()):
            board.Remove(v)
            if unconnected() <= base_unc:
                x["result"] = "removida (redundante)"; x["to"] = None; IDX = Index(); continue
            board.Add(v); unconnected()
        # b) via menor (0,5/0,3), folga furo-pad 0,10, raio 2,5 mm
        pos, how = move_via(v, pad, reach=2.5, hclr=0.10, dia_override=0.5)
        if how == "moved": x["result"] = "moved (passe 2: d0,50, folga 0,10)"; x["to"] = P(pos); continue
        # c) grelha 2D ate 3 mm, stub directo ou em L, via 0,5/0,3
        pos, how = move_via_grid(v, pad)
        if how == "moved": x["result"] = "moved (passe 3: grelha + stub L)"; x["to"] = P(pos); continue
        # d) deslizar a via ao longo da sua trilha que nao esta na camada do pad (encurtar = sem colisao nova)
        pos, how = slide_via(v, pad)
        if how == "moved": x["result"] = "moved (passe 4: deslizada ao longo da trilha)"; x["to"] = P(pos); continue
        # d2) via nova em posicao livre + segmento-ponte antiga->nova em cada camada das trilhas internas
        pos, how = bridge_via(v, pad)
        if how == "moved": x["result"] = "moved (passe 4b: ponte por segmento curto)"; x["to"] = P(pos); continue
        # e) GND sem trilhas ligadas: trilha na camada do pad ate cobre GND vizinho e remover a via
        if v.GetNetname() == "GND" and not attached_tracks(v.GetPosition()):
            ok = link_to_net_copper(pad)
            if ok:
                board.Remove(v)
                if unconnected() <= base_unc: x["result"] = "removida (passe 5: pad ligado por trilha ao GND vizinho)"; x["to"] = None; IDX = Index(); continue
                board.Add(v); unconnected()
        x["result"] = "NAO RESOLVIDO"
rep["via_in_pad_total"] = n_vip
rep["via_in_pad_fixed"] = sum(1 for x in rep["via_in_pad"] if x["result"].startswith(("moved", "removida")))
rep["via_in_pad_open"] = [x for x in rep["via_in_pad"] if x["result"] in ("NAO RESOLVIDO", "sem posicao")]

# ------------------------------------------------------------------ 2. courtyard / borda
def fp_move(ref, dx, dy):
    global IDX
    fp = board.FindFootprintByReference(ref); d = mm(dx, dy)
    moves = []
    for p in fp.Pads():
        shp = p.GetEffectiveShape(smd_layer(p))
        for t in tracks():
            if t.GetNetCode() != p.GetNetCode(): continue
            for end in ("S", "E"):
                e = t.GetStart() if end == "S" else t.GetEnd()
                if shp.Collide(e, FromMM(0.01)): moves.append((t, end, e + d))
    for t, end, newp in moves:
        a, b = (newp, t.GetEnd()) if end == "S" else (t.GetStart(), newp)
        if not IDX.seg_ok(a, b, ToMM(t.GetWidth()), t.GetLayer(), t.GetNetCode()): return False, "trilha %s colide apos mover" % t.GetNetname()
    if DRY: return True, "dry"
    fp.SetPosition(fp.GetPosition() + d)
    for t, end, newp in moves: (t.SetStart if end == "S" else t.SetEnd)(newp)
    IDX = Index()
    return True, "moved %d trilhas" % len(moves)

def cy_overlap(a, b):
    ca, cb = board.FindFootprintByReference(a).GetCourtyard(pcbnew.F_CrtYd), board.FindFootprintByReference(b).GetCourtyard(pcbnew.F_CrtYd)
    return ca.Collide(cb, 0)
if cy_overlap("D7", "U9"):
    d7, u9 = board.FindFootprintByReference("D7"), board.FindFootprintByReference("U9")
    gap = ToMM(u9.GetCourtyard(pcbnew.F_CrtYd).BBox().GetRight() - d7.GetCourtyard(pcbnew.F_CrtYd).BBox().GetLeft()) + 0.10
    # D-33: U9 para oeste primeiro — D7 para leste (+0,25) poe os pads do D7 sob a serigrafia do P1 (silk_over_copper)
    tries = [("U9", -gap, 0), ("D7", gap, 0), ("D7", 0, gap), ("D7", 0, -gap), ("D7", gap, gap), ("D7", gap, -gap), ("U9", 0, gap), ("U9", 0, -gap)]
    for ref, dx, dy in tries:
        ok, how = fp_move(ref, dx, dy)
        rep["courtyard"].append({"pair": "D7xU9", "ref": ref, "dx": round(dx, 3), "dy": round(dy, 3), "ok": ok, "how": how, "still_overlap": cy_overlap("D7", "U9") if ok and not DRY else None})
        if ok and (DRY or not cy_overlap("D7", "U9")): break
        if ok and not DRY: fp_move(ref, -dx, -dy); rep["courtyard"][-1]["how"] += " -> revertido"
d8 = board.FindFootprintByReference("D8"); over = ToMM(d8.GetCourtyard(pcbnew.F_CrtYd).BBox().GetRight() - outline.BBox().GetRight())
if over > -0.1:
    ok, how = fp_move("D8", -(over + 0.15), 0)
    rep["courtyard"].append({"pair": "D8 x borda", "dx": -round(over + 0.15, 3), "ok": ok, "how": how})

# ------------------------------------------------------------------ 3. fiduciais
def copper_free(pos, layer, r):
    shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(r))
    for p in all_pads():
        if p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(shp, 0): return False
    for t in board.GetTracks():
        if t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(shp, 0): return False
    for f in board.GetFootprints():
        if f.IsOnLayer(layer) or True:
            cy = f.GetCourtyard(pcbnew.F_CrtYd if layer == pcbnew.F_Cu else pcbnew.B_CrtYd)
            if cy.OutlineCount() and cy.Collide(shp, 0): return False
    return True

def add_fiducial(pos, layer, idx):
    fp = pcbnew.FOOTPRINT(board); fp.SetReference("FID%d" % idx); fp.SetValue("Fiducial"); fp.SetFPID(pcbnew.LIB_ID("Fiducial", "Fiducial_1mm_Mask2mm"))
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    pad = pcbnew.PAD(fp); pad.SetNumber(""); pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(FromMM(1.0), FromMM(1.0))); pad.SetLocalSolderMaskMargin(FromMM(0.5))
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask); pad.SetLayerSet(ls)
    fp.Add(pad); board.Add(fp); fp.SetPosition(pos)
    if layer == pcbnew.B_Cu: fp.Flip(pos, False)
    # rule area: sem pour de cobre a 1,2 mm (contraste para a camera da pick&place)
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False); z.SetLayer(layer)
    o = z.Outline(); o.NewOutline()
    for k in range(24):
        a = 2 * math.pi * k / 24; o.Append(int(pos.x + FromMM(1.2) * math.cos(a)), int(pos.y + FromMM(1.2) * math.sin(a)))
    z.SetZoneName("FID%d_nocopper" % idx); board.Add(z)
    return fp

if not any(f.GetReference().startswith("FID") for f in board.GetFootprints()):
    bb = outline.BBox(); L, T, R, B = (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
    corners = [("BL", L, B), ("TR", R, T), ("TL", L, T), ("BR", R, B)]
    idx = 1
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        placed = []
        for name, cx, cy in corners:
            if len(placed) == 3: break
            found = None
            for d in [x / 10 for x in range(20, 120, 2)]:
                for e in [x / 10 for x in range(20, 120, 2)]:
                    pos = mm(cx + (d if cx == L else -d), cy + (e if cy == T else -e))
                    if inside_board(pos, 2.0) and copper_free(pos, layer, 1.3): found = pos; break
                if found: break
            if found:
                if not DRY: add_fiducial(found, layer, idx)
                placed.append(P(found)); rep["fiducials"].append({"ref": "FID%d" % idx, "layer": board.GetLayerName(layer), "corner": name, "pos": P(found)}); idx += 1
            else: W("sem lugar para fiducial no canto %s em %s" % (name, board.GetLayerName(layer)))

# ------------------------------------------------------------------ 4. +3V3 < 0,20 mm
for t in tracks():
    if t.GetNetname() != "+3V3" or ToMM(t.GetWidth()) >= 0.20: continue
    w0 = ToMM(t.GetWidth())
    if not IDX.seg_ok(t.GetStart(), t.GetEnd(), 0.20, t.GetLayer(), t.GetNetCode()):
        rep["thin_3v3"].append({"at": P(t.GetStart()), "layer": board.GetLayerName(t.GetLayer()), "w": w0, "result": "sem folga para 0,20"}); continue
    if not DRY: t.SetWidth(FromMM(0.20))
    rep["thin_3v3"].append({"at": P(t.GetStart()), "layer": board.GetLayerName(t.GetLayer()), "w": w0, "result": "0,20"})

# ------------------------------------------------------------------ gravar
if not DRY:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    unc = board.GetConnectivity().GetUnconnectedCount(True)
    rep["unconnected_after"] = unc
    pcbnew.SaveBoard(PCB, board)
rep["seconds"] = round(time.time() - T0, 1)
with open(REPORT, "w", encoding="utf-8") as f: json.dump(rep, f, indent=1, ensure_ascii=False)
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items() if k != "date"}, ensure_ascii=False))
