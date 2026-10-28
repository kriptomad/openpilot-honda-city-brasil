# -*- coding: utf-8 -*-
"""
Resolve os via-in-pad que fix_audit.py nao conseguiu (busca mais ampla, centrada na via e nao no pad).

Para cada via listada:
  a) se a rede e GND/+5V/+3V3 e o pad ja fica ligado pelo plano sem a via -> remove via + stub;
  b) senao, procura nova posicao num anel (0,1..3,5 mm) a volta da via: furo >= 0,15 mm de qualquer pad SMD,
     cobre/furo da via sem colisao com outras redes, stub pad->via no layer do pad e trilhas anexas movidas
     sem colisao. Aplica a primeira posicao valida (mais proxima da via original).
Depois refaz os zone fills e exige 0 unconnected; so entao grava.

Autor: Bruno Costa
Uso: python fix_vip_rest.py [--dry]   (python do KiCad 10)
"""
import os, sys, json, math, time
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
REPORT = os.path.join(ROOT, "hardware/reports", "fix_vip_rest.json")
DRY = "--dry" in sys.argv
HOLE_PAD_CLR = 0.15; VIA_CLR = 0.12; HOLE_CLR = 0.25; SEG_CLR = 0.10
LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
TARGETS = [("D13", "1", 127.59, 67.11), ("U1", "2", 119.00, 53.42), ("C30", "2", 121.86, 61.99),
           ("C33", "2", 132.26, 72.51), ("U9", "4", 123.02, 56.62)]

board = pcbnew.LoadBoard(PCB)
def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def P(v): return "%.2f,%.2f" % (ToMM(v.x), ToMM(v.y))
def dist(a, b): return ToMM((a - b).EuclideanNorm())
def all_pads(): return [p for f in board.GetFootprints() for p in f.Pads()]
def tracks(): return [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
def smd_layer(p): return pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline, True)
def inside_board(pos, margin=0.5):
    if not outline.Contains(pos): return False
    oc = outline.Outline(0)
    return not any(oc.CSegment(k).Distance(pos) < FromMM(margin) for k in range(oc.SegmentCount()))

class Index:
    def __init__(self, exclude=()):
        self.items = []; self.holes = []
        for p in all_pads():
            for l in LAYERS4:
                if p.IsOnLayer(l): self.items.append((p.GetBoundingBox(), l, p.GetNetCode(), p.GetEffectiveShape(l)))
            if p.GetDrillSize().x > 0: self.holes.append((p.GetPosition(), ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, p.GetNetCode()))
        for t in board.GetTracks():
            if t in exclude: continue
            if t.GetClass() == "PCB_VIA":
                for l in LAYERS4: self.items.append((t.GetBoundingBox(), l, t.GetNetCode(), t.GetEffectiveShape(l)))
                self.holes.append((t.GetPosition(), ToMM(t.GetDrill()) / 2, t.GetNetCode()))
            else: self.items.append((t.GetBoundingBox(), t.GetLayer(), t.GetNetCode(), t.GetEffectiveShape(t.GetLayer())))
        self.keep = [z for z in board.Zones() if z.GetIsRuleArea()]
    def _near(self, bb, pos, r):
        return not (bb.GetRight() + r < pos.x or bb.GetLeft() - r > pos.x or bb.GetBottom() + r < pos.y or bb.GetTop() - r > pos.y)
    def via_ok(self, pos, dia, drill, nc):
        shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2)); hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2)); R = FromMM(dia / 2 + HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowVias() and z.Outline().Collide(shp, FromMM(VIA_CLR)): return False
        for bb, l, n, s in self.items:
            if n == nc or not self._near(bb, pos, R): continue
            if s.Collide(shp, FromMM(VIA_CLR)) or s.Collide(hole, FromMM(HOLE_CLR)): return False
        for hp, hr, n in self.holes:
            if dist(hp, pos) < hr + drill / 2 + HOLE_CLR + 0.02: return False
        return True
    def seg_ok(self, a, b, w, layer, nc):
        shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(w)); bb = shp.BBox(); R = FromMM(HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(0.1)): return False
        for ib, l, n, s in self.items:
            if n == nc or l != layer: continue
            if ib.GetRight() + R < bb.GetLeft() or ib.GetLeft() - R > bb.GetRight() or ib.GetBottom() + R < bb.GetTop() or ib.GetTop() - R > bb.GetBottom(): continue
            if s.Collide(shp, FromMM(SEG_CLR)): return False
        for hp, hr, n in self.holes:
            if n == nc: continue
            if shp.Collide(pcbnew.SHAPE_CIRCLE(hp, FromMM(hr)), FromMM(HOLE_CLR)): return False
        return True

def hole_in_pad(pos, drill):
    hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2))
    return [p for p in all_pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
            and p.GetBoundingBox().Inflate(FromMM(1.0)).Contains(pos) and p.GetEffectiveShape(smd_layer(p)).Collide(hole, FromMM(HOLE_PAD_CLR))]

def refill():
    filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones()); board.BuildConnectivity()
def unconnected():
    refill(); return board.GetConnectivity().GetUnconnectedCount(True)

def find_via(x, y):
    pos = mm(x, y)
    return min((t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"), key=lambda t: dist(t.GetPosition(), pos))
def find_pad(ref, num, x, y):
    fp = board.FindFootprintByReference(ref); pos = mm(x, y)
    return min((p for p in fp.Pads() if p.GetNumber() == num), key=lambda p: dist(p.GetPosition(), pos))

def stub_paths(pad, pos, w, layer, nc, IDX):
    """caminho pad->via: inicio em 9 pontos dentro do pad (bbox encolhida), recto ou em L. Devolve lista de segmentos ou None."""
    bb = pad.GetBoundingBox(); sx = max(0, (bb.GetWidth() - FromMM(w)) // 2); sy = max(0, (bb.GetHeight() - FromMM(w)) // 2)
    c = pad.GetPosition(); starts = [c] + [VECTOR2I(c.x + int(i * sx), c.y + int(j * sy)) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)]
    starts.sort(key=lambda s: dist(s, pos))
    for s in starts:
        if IDX.seg_ok(s, pos, w, layer, nc): return [(s, pos)]
    for s in starts:
        for k in (VECTOR2I(s.x, pos.y), VECTOR2I(pos.x, s.y)):
            if IDX.seg_ok(s, k, w, layer, nc) and IDX.seg_ok(k, pos, w, layer, nc): return [(s, k), (k, pos)]
    return None

def add_track(a, b, w, layer, nc):
    t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNetCode(nc); board.Add(t); return t

rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "items": []}
base_unc = unconnected(); print("unconnected inicial:", base_unc)

for ref, num, x, y in TARGETS:
    v = find_via(x, y); pad = find_pad(ref, num, x, y)
    if dist(v.GetPosition(), mm(x, y)) > 0.05:
        rep["items"].append({"pad": f"{ref}.{num}", "result": "via nao encontrada (ja corrigida?)"}); continue
    nc = v.GetNetCode(); net = v.GetNetname(); dia = ToMM(v.GetWidth()); drill = ToMM(v.GetDrill()); old = v.GetPosition(); lay = smd_layer(pad)
    att = [t for t in tracks() if t.GetStart() == old or t.GetEnd() == old]
    item = {"pad": f"{ref}.{num}", "net": net, "via": P(old), "dia": dia, "drill": drill, "attached": len(att)}
    if not hole_in_pad(old, drill):
        item["result"] = "ja nao e via-in-pad"; rep["items"].append(item); continue

    # a) via redundante (pad ja ligado pelo plano)? apenas stubs pad<->via sao removidos junto
    if net in ("GND", "+5V", "+3V3"):
        stubs = [t for t in att if t.GetStart() == pad.GetPosition() or t.GetEnd() == pad.GetPosition()]
        others = [t for t in att if t not in stubs]
        if not others:
            for t in [v] + stubs: board.Remove(t)
            u = unconnected()
            if u <= base_unc:
                item["result"] = "via removida (pad ja ligado pelo plano)"; rep["items"].append(item); print(item); continue
            for t in [v] + stubs: board.Add(t)
            refill()

    # b) mover via
    IDX = Index(exclude=[v] + att)
    stub_w = min(0.25, ToMM(min(pad.GetSize().x, pad.GetSize().y)) * 0.8)
    cands = []
    for k in range(48):
        a = 2 * math.pi * k / 48; d = 0.1
        while d <= 3.5:
            cands.append(mm(ToMM(old.x) + d * math.cos(a), ToMM(old.y) + d * math.sin(a))); d += 0.1
    cands.sort(key=lambda p: dist(p, old))
    done = None
    for dia_try in (dia, 0.5):
        for pos in cands:
            if not inside_board(pos) or hole_in_pad(pos, drill): continue
            if not IDX.via_ok(pos, dia_try, drill, nc): continue
            if not IDX.seg_ok(pad.GetPosition(), pos, stub_w, lay, nc): continue
            ok = True
            for t in att:
                if t.GetStart() == pad.GetPosition() or t.GetEnd() == pad.GetPosition(): continue  # stub antigo sera substituido
                other = t.GetEnd() if t.GetStart() == old else t.GetStart()
                if not IDX.seg_ok(other, pos, ToMM(t.GetWidth()), t.GetLayer(), nc): ok = False; break
            if ok: done = (pos, dia_try); break
        if done: break
    if not done:
        item["result"] = "NAO RESOLVIDO"; rep["items"].append(item); print(item); continue
    pos, dia_new = done
    for t in att:
        if t.GetStart() == pad.GetPosition() or t.GetEnd() == pad.GetPosition(): board.Remove(t); continue
        if t.GetStart() == old: t.SetStart(pos)
        else: t.SetEnd(pos)
    v.SetPosition(pos); v.SetWidth(FromMM(dia_new))
    add_track(pad.GetPosition(), pos, stub_w, lay, nc)
    u = unconnected()
    item.update({"to": P(pos), "dia_new": dia_new, "stub_w": round(stub_w, 2), "unconnected": u, "result": "moved" if u <= base_unc else "moved MAS unconnected subiu"})
    rep["items"].append(item); print(item)

final_unc = unconnected(); rep["unconnected_final"] = final_unc
print("unconnected final:", final_unc)
if not DRY and final_unc <= base_unc:
    pcbnew.SaveBoard(PCB, board); print("gravado", PCB)
elif not DRY: print("NAO GRAVADO: unconnected subiu")
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as f: json.dump(rep, f, indent=1, ensure_ascii=False)
