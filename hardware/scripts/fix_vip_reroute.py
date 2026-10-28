# -*- coding: utf-8 -*-
"""
Ultimo recurso para via-in-pad (mesma definicao do final_audit.py: centro da via dentro da bbox de um pad SMD).
O fix_audit.py so desloca a via na vizinhanca imediata do pad; quando todas as posicoes perto do pad estao
ocupadas (caso U8.3 apos o relayout leste, D-33) este script:

  1. percorre as trilhas da mesma rede na camada do pad a partir da via (ate MAX_WALK mm) e amostra
     candidatos a cada STEP mm, fora de qualquer bbox de pad SMD;
  2. para cada candidato verifica a via (cobre + furos, 4 camadas, rule-areas) e tenta re-ligar cada
     trilha da(s) outra(s) camada(s) que chegava a via antiga: segmento directo ou com um ponto
     intermedio (grelha WAY_STEP mm) validado por seg_ok;
  3. aplica a solucao de menor comprimento adicionado, divide a trilha de topo no ponto da via,
     re-enche as zonas e confirma que o numero de unconnected nao aumentou (senao reverte).

Uso: python fix_vip_reroute.py [--dry]   (python do KiCad 10)
Relatorio: hardware\\reports\fix_vip_reroute.json ; DRC final: hardware\\reports\hybrid_DRC_fix_vip.json
"""
import os, sys, json, math, time, subprocess
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
REPORT = os.path.join(ROOT, "hardware/reports", "fix_vip_reroute.json")
DRC_OUT = os.path.join(ROOT, "hardware/reports", "hybrid_DRC_fix_vip.json")
KICAD_CLI = str(hp.KICAD_CLI)
DRY = "--dry" in sys.argv
hp.assert_inside_output(PCB); hp.assert_inside_output(REPORT)

LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
CLR, HOLE_CLR = 0.10, 0.25
MAX_WALK, STEP, WAY_STEP, WAY_PAD = 8.0, 0.10, 0.25, 2.0
def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def P(v): return "%.3f,%.3f" % (ToMM(v.x), ToMM(v.y))
def dist(a, b): return ToMM((a - b).EuclideanNorm())

board = pcbnew.LoadBoard(PCB)
rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": DRY, "found": [], "actions": []}

class Index:
    def __init__(self):
        self.items, self.holes = [], []
        for p in [q for f in board.GetFootprints() for q in f.Pads()]:
            for l in LAYERS4:
                if p.IsOnLayer(l): self.items.append((p.GetBoundingBox(), l, p.GetNetCode(), p.GetEffectiveShape(l), p))
            if p.GetDrillSize().x > 0: self.holes.append((p.GetPosition(), ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2, p.GetNetCode(), p))
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                for l in LAYERS4: self.items.append((t.GetBoundingBox(), l, t.GetNetCode(), t.GetEffectiveShape(l), t))
                self.holes.append((t.GetPosition(), ToMM(t.GetDrill()) / 2, t.GetNetCode(), t))
            else: self.items.append((t.GetBoundingBox(), t.GetLayer(), t.GetNetCode(), t.GetEffectiveShape(t.GetLayer()), t))
        self.keep = [z for z in board.Zones() if z.GetIsRuleArea()]
        self.smd = [(p.GetBoundingBox(), p) for f in board.GetFootprints() for p in f.Pads() if p.GetDrillSize().x == 0]
    def in_smd(self, pos):
        return any(bb.Contains(pos) for bb, p in self.smd)
    def via_ok(self, pos, dia, drill, nc, skip=()):
        shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2)); hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2)); R = FromMM(dia / 2 + HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowVias() and z.Outline().Collide(shp, 0): return "keepout"
        for bb, l, n, s, o in self.items:
            if n == nc or o in skip: continue
            if bb.GetRight() + R < pos.x or bb.GetLeft() - R > pos.x or bb.GetBottom() + R < pos.y or bb.GetTop() - R > pos.y: continue
            if s.Collide(shp, FromMM(CLR)) or s.Collide(hole, FromMM(HOLE_CLR)): return "copper %s" % o.GetNetname()
        for hp_, hr, n, o in self.holes:
            if o in skip: continue
            if dist(hp_, pos) < hr + drill / 2 + HOLE_CLR + 0.01: return "hole %s" % P(hp_)
        return None
    def seg_ok(self, a, b, w, layer, nc, skip=()):
        shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(w)); bb = shp.BBox(); R = FromMM(HOLE_CLR + 0.05)
        for z in self.keep:
            if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(CLR)): return "keepout"
        for ib, l, n, s, o in self.items:
            if n == nc or l != layer or o in skip: continue
            if ib.GetRight() + R < bb.GetLeft() or ib.GetLeft() - R > bb.GetRight() or ib.GetBottom() + R < bb.GetTop() or ib.GetTop() - R > bb.GetBottom(): continue
            if s.Collide(shp, FromMM(CLR)): return "copper %s" % o.GetNetname()
        for hp_, hr, n, o in self.holes:
            if n == nc or o in skip: continue
            if shp.Collide(pcbnew.SHAPE_CIRCLE(hp_, FromMM(hr)), FromMM(HOLE_CLR)): return "hole %s" % P(hp_)
        return None

def tracks(): return [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
def unconnected_count():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(True)

def find_vip():
    out = []
    for v in [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetDrillSize().x == 0 and p.GetBoundingBox().Contains(v.GetPosition()):
                    out.append((v, p, f))
    return out

def walk_candidates(v, layer, idx):
    """Pontos ao longo das trilhas da mesma rede em `layer` ligadas (em cadeia) a via, ordenados por distancia percorrida."""
    nc = v.GetNetCode(); seen = set(); cands = []; frontier = [(v.GetPosition(), 0.0)]
    while frontier:
        pos, d0 = frontier.pop(0)
        for t in tracks():
            if t.GetNetCode() != nc or t.GetLayer() != layer or t.m_Uuid.AsString() in seen: continue
            if t.GetStart() == pos: a, b = t.GetStart(), t.GetEnd()
            elif t.GetEnd() == pos: a, b = t.GetEnd(), t.GetStart()
            else: continue
            seen.add(t.m_Uuid.AsString()); L = dist(a, b)
            if L < 1e-6: continue
            n = int(L / STEP)
            for i in range(1, n + 1):
                s = i * STEP
                if d0 + s > MAX_WALK: break
                c = VECTOR2I(int(a.x + (b.x - a.x) * s / L), int(a.y + (b.y - a.y) * s / L))
                if not idx.in_smd(c): cands.append((d0 + s, c, t))
            if d0 + L <= MAX_WALK: frontier.append((b, d0 + L))
    cands.sort(key=lambda x: x[0]); return cands

def route(idx, a, b, w, layer, nc, skip):
    if idx.seg_ok(a, b, w, layer, nc, skip) is None: return [a, b]
    x0, x1 = sorted((ToMM(a.x), ToMM(b.x))); y0, y1 = sorted((ToMM(a.y), ToMM(b.y)))
    best = None
    x = x0 - WAY_PAD
    while x <= x1 + WAY_PAD:
        y = y0 - WAY_PAD
        while y <= y1 + WAY_PAD:
            wpt = mm(x, y); L = dist(a, wpt) + dist(wpt, b)
            if (best is None or L < best[0]) and idx.seg_ok(a, wpt, w, layer, nc, skip) is None and idx.seg_ok(wpt, b, w, layer, nc, skip) is None:
                best = (L, wpt)
            y += WAY_STEP
        x += WAY_STEP
    return [a, best[1], b] if best else None

def fix_one(v, pad, fp):
    nc = v.GetNetCode(); top = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    att = [t for t in tracks() if t.GetNetCode() == nc and (t.GetStart() == v.GetPosition() or t.GetEnd() == v.GetPosition())]
    others = [t for t in att if t.GetLayer() != top]
    if not others: return {"result": "sem trilhas noutra camada (via de costura?)"}
    idx = Index(); cands = walk_candidates(v, top, idx)
    dia, drill = ToMM(v.GetWidth()), ToMM(v.GetDrill())
    skip = [v] + others
    for d0, c, host in cands:
        if idx.via_ok(c, dia, drill, nc, skip): continue
        paths = []
        for t in others:
            far = t.GetEnd() if t.GetStart() == v.GetPosition() else t.GetStart()
            pth = route(idx, c, far, ToMM(t.GetWidth()), t.GetLayer(), nc, skip)
            if pth is None: break
            paths.append((t, pth))
        if len(paths) != len(others): continue
        info = {"via": P(v.GetPosition()), "pad": "%s.%s" % (fp.GetReference(), pad.GetNumber()), "net": v.GetNetname(), "new_via": P(c), "walk_mm": round(d0, 2),
                "paths": [[P(q) for q in pth] for t, pth in paths]}
        if DRY: info["result"] = "dry"; return info
        before = unconnected_count()
        # aplicar
        oldpos = v.GetPosition(); v.SetPosition(c)
        hs, he = host.GetStart(), host.GetEnd(); host.SetEnd(c)
        t2 = pcbnew.PCB_TRACK(board); t2.SetStart(c); t2.SetEnd(he); t2.SetWidth(host.GetWidth()); t2.SetLayer(host.GetLayer()); t2.SetNetCode(nc); board.Add(t2)
        new = []
        for t, pth in paths:
            for i in range(len(pth) - 1):
                n = pcbnew.PCB_TRACK(board); n.SetStart(pth[i]); n.SetEnd(pth[i + 1]); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNetCode(nc); board.Add(n); new.append(n)
            board.Remove(t)
        # trilhas de topo que terminavam na via antiga ficam ligadas pelo pad (mesma rede): nada a fazer
        after = unconnected_count()
        if after > before:
            for n in new: board.Remove(n)
            for t, pth in paths: board.Add(t)
            board.Remove(t2); host.SetEnd(he); v.SetPosition(oldpos)
            info["result"] = "revertido: unconnected %d -> %d" % (before, after); continue
        info["result"] = "ok"; info["unconnected"] = after; return info
    return {"via": P(v.GetPosition()), "pad": "%s.%s" % (fp.GetReference(), pad.GetNumber()), "net": v.GetNetname(), "result": "sem candidato", "candidatos": len(cands)}

vip = find_vip()
rep["found"] = [{"via": P(v.GetPosition()), "pad": "%s.%s" % (f.GetReference(), p.GetNumber()), "net": v.GetNetname()} for v, p, f in vip]
print("via-in-pad:", len(vip))
changed = False
for v, p, f in vip:
    r = fix_one(v, p, f); rep["actions"].append(r); print(r)
    changed |= r.get("result") == "ok"
if changed and not DRY:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(PCB, board)
rep["via_in_pad_after"] = len(find_vip())
if not DRY:
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", DRC_OUT, PCB], capture_output=True, text=True)
    d = json.load(open(DRC_OUT, encoding="utf-8")); by = {}
    for x in d["violations"]: by[x["type"]] = by.get(x["type"], 0) + 1
    rep["drc_after"] = {"unconnected": len(d["unconnected_items"]), "total": len(d["violations"]), "by_type": by}
    print("DRC:", rep["drc_after"])
with open(REPORT, "w", encoding="utf-8") as fh: json.dump(rep, fh, indent=1, ensure_ascii=False)
