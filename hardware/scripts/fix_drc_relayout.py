# -*- coding: utf-8 -*-
"""
Corretor orientado pelo DRC para as regressoes que o fix_audit.py deixa apos o relayout leste (step5e, D-33).
Substitui o fix_drc_regressions.py (que tinha coordenadas fixas da geometria antiga): aqui cada item e
localizado pelo relatorio DRC (uuid) e a correccao e calculada sobre a geometria actual.

  1. items_not_allowed : via dentro de rule-area (keepout do SW1) -> empurra a via em +X (passos de 0,05 mm)
                         ate sair da area; as pontas das trilhas ligadas acompanham;
  2. clearance trilha x pad : desloca o segmento perpendicularmente ao seu eixo, afastando-o do pad, pelo
                         deficit + 0,02 mm; pontas das trilhas vizinhas acompanham (verificado com seg_ok);
  3. hole_clearance via x via : afasta a via destravada (nao PTH) na direccao oposta pelo deficit + 0,02 mm;
  4. track_dangling : remove a trilha se isso nao aumentar os unconnected (ponta solta do FR/5c);
  5. fiduciais FID2/FID5 sob a serigrafia do U3 (silk_over_copper com pad FID*) -> busca em grelha de um
                         ponto livre (>= 2 mm da borda, sem cobre num raio de 1,3 mm, sem courtyard a 0,9 mm,
                         sem serigrafia a 1,3 mm) a partir do canto inferior direito; a rule-area FIDn_nocopper
                         acompanha.
Repete DRC -> correccao ate --rounds (default 3) ou ate nao haver itens tratados.

Uso: python fix_drc_relayout.py [--dry] [--rounds N]   (python do KiCad 10)
Relatorio: hardware\\reports\fix_drc_relayout.json ; DRC final: hardware\\reports\hybrid_DRC_fix_relayout.json
"""
import os, sys, json, math, time, subprocess
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
REPORT = os.path.join(ROOT, "hardware/reports", "fix_drc_relayout.json")
DRC_OUT = os.path.join(ROOT, "hardware/reports", "hybrid_DRC_fix_relayout.json")
KICAD_CLI = str(hp.KICAD_CLI)
DRY = "--dry" in sys.argv
ROUNDS = int(sys.argv[sys.argv.index("--rounds") + 1]) if "--rounds" in sys.argv else 3
hp.assert_inside_output(PCB); hp.assert_inside_output(REPORT)

LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
CLR, HOLE_CLR = 0.10, 0.25
def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def P(v): return "%.3f,%.3f" % (ToMM(v.x), ToMM(v.y))
def dist(a, b): return ToMM((a - b).EuclideanNorm())

board = pcbnew.LoadBoard(PCB)
rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": DRY, "rounds": []}

def run_drc(out):
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", out, PCB], capture_output=True, text=True)
    return json.load(open(out, encoding="utf-8"))

UUIDS = {}
def build_uuid_map():
    UUIDS.clear()
    for t in board.GetTracks(): UUIDS[t.m_Uuid.AsString()] = t
    for f in board.GetFootprints():
        for p in f.Pads(): UUIDS[p.m_Uuid.AsString()] = p
def item(uuid):
    return UUIDS.get(uuid)

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
def attached(pos, exclude=()):
    return [(t, "S" if t.GetStart() == pos else "E") for t in tracks() if t not in exclude and (t.GetStart() == pos or t.GetEnd() == pos)]

def move_endpoints(moves):
    for t, end, newp in moves: (t.SetStart if end == "S" else t.SetEnd)(newp)

def unconnected_count():
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(True)

# ------------------------------------------------------------------ 1. via em keepout
def fix_keepout_via(v, idx, log):
    old = v.GetPosition(); att = attached(old)
    for k in range(1, 13):
        pos = VECTOR2I(old.x + FromMM(0.05 * k), old.y)
        why = idx.via_ok(pos, ToMM(v.GetWidth()), ToMM(v.GetDrill()), v.GetNetCode(), skip=(v,) + tuple(t for t, _ in att))
        if why: continue
        bad = [idx.seg_ok(pos if e == "S" else t.GetStart(), t.GetEnd() if e == "S" else pos, ToMM(t.GetWidth()), t.GetLayer(), t.GetNetCode(), skip=(v,) + tuple(x for x, _ in att)) for t, e in att]
        if any(bad): continue
        log.append({"fix": "keepout_via", "net": v.GetNetname(), "from": P(old), "to": P(pos), "tracks": len(att)})
        if not DRY:
            v.SetPosition(pos); move_endpoints([(t, e, pos) for t, e in att])
        return True
    log.append({"fix": "keepout_via", "net": v.GetNetname(), "from": P(old), "result": "sem posicao"}); return False

# ------------------------------------------------------------------ 2. clearance trilha x pad
def fix_track_pad(t, pad, actual, idx, log):
    a, b = t.GetStart(), t.GetEnd(); L = (b - a).EuclideanNorm()
    if L == 0: return False
    nx, ny = -(b.y - a.y) / L, (b.x - a.x) / L               # normal unitaria
    c = pad.GetPosition(); mid = VECTOR2I((a.x + b.x) // 2, (a.y + b.y) // 2)
    side = 1 if (nx * (mid.x - c.x) + ny * (mid.y - c.y)) >= 0 else -1   # afastar do pad
    for extra in (0.02, 0.05, 0.10):
        d = FromMM(CLR - actual + extra)
        delta = VECTOR2I(int(round(side * nx * d)), int(round(side * ny * d)))
        na, nb = a + delta, b + delta
        attA, attB = attached(a, exclude=(t,)), attached(b, exclude=(t,))
        skip = (t,) + tuple(x for x, _ in attA + attB)
        if idx.seg_ok(na, nb, ToMM(t.GetWidth()), t.GetLayer(), t.GetNetCode(), skip=skip): continue
        ok = True
        for ta, e in attA:
            s, en = (na, ta.GetEnd()) if e == "S" else (ta.GetStart(), na)
            if s != en and idx.seg_ok(s, en, ToMM(ta.GetWidth()), ta.GetLayer(), ta.GetNetCode(), skip=skip): ok = False
        for tb, e in attB:
            s, en = (nb, tb.GetEnd()) if e == "S" else (tb.GetStart(), nb)
            if s != en and idx.seg_ok(s, en, ToMM(tb.GetWidth()), tb.GetLayer(), tb.GetNetCode(), skip=skip): ok = False
        if not ok: continue
        # a ponta nao pode sair do pad/via a que estava ligada (se a ponta estava sobre um pad da mesma rede)
        log.append({"fix": "track_pad", "net": t.GetNetname(), "pad": "%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber()),
                    "from": [P(a), P(b)], "to": [P(na), P(nb)], "shift_mm": round(ToMM(d), 3), "neighbours": len(attA) + len(attB)})
        if not DRY:
            t.SetStart(na); t.SetEnd(nb); move_endpoints([(x, e, na) for x, e in attA] + [(x, e, nb) for x, e in attB])
        return True
    log.append({"fix": "track_pad", "net": t.GetNetname(), "pad": "%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber()), "from": [P(a), P(b)], "result": "sem folga"}); return False

# ------------------------------------------------------------------ 3. hole_clearance via x via
def fix_via_via(v, other, actual, idx, log):
    old = v.GetPosition(); o = other.GetPosition(); L = (old - o).EuclideanNorm()
    if L == 0: return False
    ux, uy = (old.x - o.x) / L, (old.y - o.y) / L
    att = attached(old)
    for extra in (0.02, 0.05, 0.10, 0.15):
        d = FromMM(HOLE_CLR - actual + extra); pos = VECTOR2I(int(round(old.x + ux * d)), int(round(old.y + uy * d)))
        skip = (v,) + tuple(t for t, _ in att)
        if idx.via_ok(pos, ToMM(v.GetWidth()), ToMM(v.GetDrill()), v.GetNetCode(), skip=skip): continue
        if any(idx.seg_ok(pos if e == "S" else t.GetStart(), t.GetEnd() if e == "S" else pos, ToMM(t.GetWidth()), t.GetLayer(), t.GetNetCode(), skip=skip) for t, e in att): continue
        log.append({"fix": "via_via", "net": v.GetNetname(), "from": P(old), "to": P(pos), "tracks": len(att)})
        if not DRY: v.SetPosition(pos); move_endpoints([(t, e, pos) for t, e in att])
        return True
    log.append({"fix": "via_via", "net": v.GetNetname(), "from": P(old), "result": "sem posicao"}); return False

# ------------------------------------------------------------------ 5. fiduciais
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline, True)
def inside_board(pos, margin):
    if not outline.Contains(pos): return False
    oc = outline.Outline(0)
    return not any(oc.CSegment(k).Distance(pos) < FromMM(margin) for k in range(oc.SegmentCount()))
def fid_spot_free(pos, layer, fid):
    cu = pcbnew.SHAPE_CIRCLE(pos, FromMM(1.3)); cy = pcbnew.SHAPE_CIRCLE(pos, FromMM(0.9)); silk = pcbnew.SHAPE_CIRCLE(pos, FromMM(1.3))
    sl = pcbnew.F_SilkS if layer == pcbnew.F_Cu else pcbnew.B_SilkS
    for f in board.GetFootprints():
        if f.GetReference().startswith("FID"): continue
        for p in f.Pads():
            if p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(cu, 0): return False
        c = f.GetCourtyard(pcbnew.F_CrtYd if layer == pcbnew.F_Cu else pcbnew.B_CrtYd)
        if c.OutlineCount() and c.Collide(cy, 0): return False
        for g in f.GraphicalItems():
            if g.GetLayer() == sl and g.GetEffectiveShape(sl).Collide(silk, 0): return False
    for t in board.GetTracks():
        if t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(cu, 0): return False
    for d in board.GetDrawings():
        if d.GetLayer() == sl and d.GetEffectiveShape(sl).Collide(silk, 0): return False
    return True
def relocate_fid(ref, log):
    f = board.FindFootprintByReference(ref)
    if f is None: return False
    layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    bb = outline.BBox(); R, B, L, T = ToMM(bb.GetRight()), ToMM(bb.GetBottom()), ToMM(bb.GetLeft()), ToMM(bb.GetTop())
    best = None
    for corner in ((R, B), (R, T), (L, B)):
        cx, cy = corner
        for d in [x / 10 for x in range(20, 140, 2)]:
            for e in [x / 10 for x in range(20, 140, 2)]:
                pos = mm(cx - d if cx == R else cx + d, cy - e if cy == B else cy + e)
                if not inside_board(pos, 2.0) or not fid_spot_free(pos, layer, f): continue
                best = pos; break
            if best: break
        if best: break
    if best is None:
        log.append({"fix": "fiducial", "ref": ref, "result": "sem lugar"}); return False
    old = f.GetPosition(); delta = best - old
    log.append({"fix": "fiducial", "ref": ref, "layer": board.GetLayerName(layer), "from": P(old), "to": P(best)})
    if not DRY:
        f.SetPosition(best)
        for z in board.Zones():
            if z.GetZoneName() == ref + "_nocopper": z.Move(delta)
    return True

# ------------------------------------------------------------------ ciclo DRC -> correccao
for rnd in range(ROUNDS):
    d = run_drc(DRC_OUT); idx = Index(); log = []; build_uuid_map()
    by = {}
    for v in d["violations"]: by[v["type"]] = by.get(v["type"], 0) + 1
    rinfo = {"round": rnd, "drc_before": {"unconnected": len(d["unconnected_items"]), "total": len(d["violations"]), "by_type": by}, "actions": log}
    rep["rounds"].append(rinfo)
    handled = 0; fids = set(); via_via_done = set(); pads_done = set()
    for v in d["violations"]:
        t, items = v["type"], v["items"]
        try:
            if t == "items_not_allowed":
                it = item(items[0]["uuid"])
                if it is not None and it.GetClass() == "PCB_VIA" and fix_keepout_via(it, idx, log): handled += 1; idx = Index()
            elif t == "clearance":
                objs = [item(i["uuid"]) for i in items]
                trk = next((o for o in objs if o is not None and o.GetClass() == "PCB_TRACK"), None)
                pad = next((o for o in objs if o is not None and o.GetClass() == "PAD"), None)
                actual = float(v["description"].split("actual")[1].split("mm")[0].replace(",", ".").strip())
                if trk is not None and pad is not None:
                    if pad.m_Uuid.AsString() in pads_done: continue   # um segmento por pad e por rodada: o vizinho ja acompanhou
                    if fix_track_pad(trk, pad, actual, idx, log): handled += 1; idx = Index(); pads_done.add(pad.m_Uuid.AsString())
            elif t == "hole_clearance":
                objs = [item(i["uuid"]) for i in items]
                if all(o is not None and o.GetClass() == "PCB_VIA" for o in objs) and len(objs) == 2:
                    key = tuple(sorted(i["uuid"] for i in items))
                    if key in via_via_done: continue
                    via_via_done.add(key)
                    actual = float(v["description"].split("actual")[1].split("mm")[0].replace(",", ".").strip())
                    mv = next((o for o in objs if not o.IsLocked()), objs[0])
                    other = objs[1] if mv is objs[0] else objs[0]
                    if fix_via_via(mv, other, actual, idx, log): handled += 1; idx = Index()
            elif t == "track_dangling":
                it = item(items[0]["uuid"])
                if it is not None and it.GetClass() == "PCB_TRACK":
                    if DRY: log.append({"fix": "dangling", "net": it.GetNetname(), "at": P(it.GetStart()), "result": "dry"}); handled += 1; continue
                    before = unconnected_count(); board.Remove(it)
                    if unconnected_count() > before:
                        board.Add(it); log.append({"fix": "dangling", "net": it.GetNetname(), "at": P(it.GetStart()), "result": "mantida (ligava)"})
                    else: log.append({"fix": "dangling", "net": it.GetNetname(), "at": P(it.GetStart()), "result": "removida"}); handled += 1; idx = Index()
            elif t == "silk_over_copper":
                for i in items:
                    if "FID" in i["description"]:
                        ref = i["description"].split(" of ")[1].split(" ")[0]
                        fids.add(ref)
        except Exception as ex:
            log.append({"error": str(ex), "type": t})
    for ref in sorted(fids):
        if relocate_fid(ref, log): handled += 1
    rinfo["handled"] = handled
    if not DRY and handled:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(PCB, board)
    if handled == 0 or DRY: break

d = run_drc(DRC_OUT); by = {}
for v in d["violations"]: by[v["type"]] = by.get(v["type"], 0) + 1
rep["drc_after"] = {"unconnected": len(d["unconnected_items"]), "total": len(d["violations"]), "by_type": by,
                    "errors": [(v["type"], v["description"][:80], [(i["description"][:50], i["pos"]["x"], i["pos"]["y"]) for i in v["items"]]) for v in d["violations"]
                               if v["type"] in ("clearance", "items_not_allowed", "track_dangling", "shorting_items", "tracks_crossing", "hole_clearance", "silk_over_copper")]}
with open(REPORT, "w", encoding="utf-8") as f: json.dump(rep, f, indent=1, ensure_ascii=False)
print(json.dumps({"rounds": [(r["round"], r["handled"], r["actions"]) for r in rep["rounds"]], "drc_after": rep["drc_after"]}, indent=1, ensure_ascii=False))
