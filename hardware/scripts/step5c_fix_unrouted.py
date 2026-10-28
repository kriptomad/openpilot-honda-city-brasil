# -*- coding: utf-8 -*-
"""
STEP 5c - pos-passe guiado pelo DRC: fecha as conexoes que o Freerouting deixou abertas.

Autor: Bruno Costa

Roda em ciclos: kicad-cli DRC -> JSON -> para cada par "unconnected" aplica, em ordem:
  A) pad de potencia (GND/+3V3/+5V): via de stitch perto do pad (plano GND em In2/B.Cu, +3V3 em In1,
     +5V nas zonas +5V) - para pinos do U7 a via vai por baixo do corpo do LQFP quando nao ha espaco fora;
  B) trilha com ponta solta em transicao de camada: via na ponta (ou recua ao longo da trilha);
  C) dois itens de sinal: via na ponta da trilha + trilha ate o pad / conexao direta reta ou em L;
  D) ilha de zona GND sem via: via no interior da ilha (liga ao plano In2).
Nunca toca itens travados (criticos do step5b, CAN H/L). Para quando nada mais muda ou unconnected == 0.
Uso:  python step5c_fix_unrouted.py [--rounds N] [--dry] [--pre]
  --pre : modo pre-Freerouting (chamado pelo step5b): so redes de potencia (GND/+3V3/+5V), sem rip-up,
          itens adicionados ficam travados para o Freerouting os respeitar.
Tambem importavel: step5b executa este ficheiro com PRELOADED_BOARD/AS_LIBRARY definidos e chama main().
"""
import json, os, re, subprocess, sys, math
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")
KICAD_CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
DRC_TMP = os.path.join(ROOT, "06_REPORTS", "tmp_drc_5c.json")
REPORT = os.path.join(ROOT, "06_REPORTS", "step5c_fix.json")
ROUNDS = int(sys.argv[sys.argv.index("--rounds") + 1]) if "--rounds" in sys.argv else 5
DRY = "--dry" in sys.argv
POWER_ONLY = "--pre" in sys.argv
LOCK_ADDED = POWER_ONLY
if POWER_ONLY: REPORT = os.path.join(ROOT, "06_REPORTS", "step5c_pre.json")
PLANE_NETS = {"GND": None, "+3V3": "In1.Cu"}  # via em qualquer lugar liga ao GND; +3V3 so dentro da zona In1
LAYERS4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

board = globals().get("PRELOADED_BOARD") or pcbnew.LoadBoard(PCB)
u7 = board.FindFootprintByReference("U7"); u7c = u7.GetPosition()
nets = board.GetNetsByName()
report = {"rounds": [], "warnings": []}
W = report["warnings"].append

def mmv(x, y): return VECTOR2I(FromMM(x), FromMM(y))
def pt(p): return (round(ToMM(p.x), 3), round(ToMM(p.y), 3))
def dist(a, b): return ToMM((a - b).EuclideanNorm())

# ---------------------------------------------------------------- colisao (mesma logica do step5b)
all_pads = [p for f in board.GetFootprints() for p in f.Pads()]
KEEPOUTS = [z for z in board.Zones() if z.GetIsRuleArea()] + [z for fp in board.GetFootprints() for z in fp.Zones() if z.GetIsRuleArea()]
def tracks(): return list(board.GetTracks())
def seg_collides(a, b, width, layer, netcode, clearance=0.12):
    shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(width))
    for z in KEEPOUTS:
        if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(0.1)): return "keepout"
    for p in all_pads:
        if p.GetNetCode() == netcode or not p.IsOnLayer(layer): continue
        if p.GetEffectiveShape(layer).Collide(shp, FromMM(clearance)): return "pad %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
    for t in tracks():
        if t.GetNetCode() == netcode or not t.IsOnLayer(layer): continue
        if t.GetEffectiveShape(layer).Collide(shp, FromMM(clearance)): return "track %s" % t.GetNetname()
        if t.GetClass() == "PCB_VIA":  # furo da via: hole_clearance 0,25 (D-30: trilhas do 5c geravam hole_clearance e o fix_holes arrancava vias do FR)
            if shp.Collide(pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetDrill() // 2), FromMM(HOLE_CLR)): return "via-hole %s" % t.GetNetname()
    for p in all_pads:
        if p.GetNetCode() == netcode or p.GetDrillSize().x == 0: continue
        if shp.Collide(pcbnew.SHAPE_CIRCLE(p.GetPosition(), max(p.GetDrillSize().x, p.GetDrillSize().y) // 2), FromMM(HOLE_CLR)): return "pth-hole %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
    return None
HOLE_CLR = 0.25   # hole_clearance / hole_to_hole do projeto (design settings)
def via_collides(pos, dia, netcode, clearance=0.15, drill=0.3):
    shp = pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2))
    hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2))
    for z in KEEPOUTS:
        if z.GetDoNotAllowVias() and z.Outline().Collide(shp, FromMM(clearance)): return "keepout"
    for p in all_pads:
        if p.GetNetCode() == netcode: continue
        for l in LAYERS4:
            if p.IsOnLayer(l) and (p.GetEffectiveShape(l).Collide(shp, FromMM(clearance)) or p.GetEffectiveShape(l).Collide(hole, FromMM(HOLE_CLR))):
                return "pad %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
    for t in tracks():
        if t.GetNetCode() == netcode: continue
        for l in LAYERS4:
            if t.IsOnLayer(l) and (t.GetEffectiveShape(l).Collide(shp, FromMM(clearance)) or t.GetEffectiveShape(l).Collide(hole, FromMM(HOLE_CLR))):
                return "track %s" % t.GetNetname()
    for t in tracks():
        if t.GetClass() == "PCB_VIA" and dist(t.GetPosition(), pos) < (ToMM(t.GetDrill()) + drill) / 2 + HOLE_CLR + 0.02: return "hole_to_hole via"
    for p in all_pads:
        if p.GetDrillSize().x > 0 and dist(p.GetPosition(), pos) < (ToMM(p.GetDrillSize().x) + drill) / 2 + HOLE_CLR + 0.02: return "hole_to_hole pad"
    return None

added = []
def add_track(a, b, width, layer, netcode):
    if a == b: return None
    t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b); t.SetWidth(FromMM(width)); t.SetLayer(layer); t.SetNetCode(netcode)
    t.SetLocked(LOCK_ADDED); board.Add(t); added.append(("track", pt(a), pt(b), board.GetLayerName(layer))); return t
def add_via(pos, netcode, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(netcode)
    v.SetLocked(LOCK_ADDED); board.Add(v); added.append(("via", pt(pos))); return v

def zone_contains(netname, layer, pos):
    """pos esta dentro do contorno de alguma zona (nao-keepout) dessa net nessa camada?"""
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != netname or not z.IsOnLayer(layer): continue
        if z.Outline().Contains(pos): return True
    return False
def plane_ok(netname, pos):
    if netname == "GND": return True
    if netname == "+3V3": return zone_contains("+3V3", pcbnew.In1_Cu, pos)
    if netname == "+5V": return any(zone_contains("+5V", l, pos) for l in LAYERS4)
    return False

def item_layer(p):
    if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu): return pcbnew.B_Cu
    return pcbnew.F_Cu

# ---------------------------------------------------------------- parsing do DRC
RX_PAD = re.compile(r"^(PTH pad|Pad) (\S+) \[(.+?)\] of (\S+)(?: on (\S+))?")
RX_TRK = re.compile(r"^Track \[(.+?)\] on (\S+), length ([\d.,]+) mm")
RX_VIA = re.compile(r"^Via \[(.+?)\]")
RX_ZONE = re.compile(r"^Zone \[(.+?)\]")
def parse(it):
    d = it["description"]; pos = mmv(it["pos"]["x"], it["pos"]["y"])
    m = RX_PAD.match(d)
    if m:
        fp = board.FindFootprintByReference(m.group(4)); pad = fp.FindPadByNumber(m.group(2)) if fp else None
        if pad is None:  # pads duplicados com mesmo numero (SW1): escolhe o mais proximo
            pass
        if fp and pad is not None and dist(pad.GetPosition(), pos) > 0.05:
            pad = min((p for p in fp.Pads() if p.GetNumber() == m.group(2)), key=lambda p: dist(p.GetPosition(), pos))
        return {"kind": "pad", "net": m.group(3), "ref": m.group(4), "num": m.group(2), "pos": pos, "obj": pad, "pth": m.group(1) == "PTH pad"}
    m = RX_TRK.match(d)
    if m:
        lay = board.GetLayerID(m.group(2)); L = float(m.group(3).replace(",", "."))
        cands = [t for t in tracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == m.group(1) and t.GetLayer() == lay
                 and (dist(t.GetStart(), pos) < 0.02 or dist(t.GetEnd(), pos) < 0.02)]
        cands.sort(key=lambda t: abs(ToMM(t.GetLength()) - L))
        return {"kind": "track", "net": m.group(1), "layer": lay, "pos": pos, "obj": cands[0] if cands else None}
    m = RX_VIA.match(d)
    if m:
        v = [t for t in tracks() if t.GetClass() == "PCB_VIA" and dist(t.GetPosition(), pos) < 0.02]
        return {"kind": "via", "net": m.group(1), "pos": pos, "obj": v[0] if v else None}
    m = RX_ZONE.match(d)
    if m: return {"kind": "zone", "net": m.group(1), "pos": pos, "obj": None}
    return {"kind": "?", "net": None, "pos": pos, "obj": None, "desc": d}

def run_drc():
    r = subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", DRC_TMP, PCB], capture_output=True, text=True, timeout=600)
    with open(DRC_TMP, encoding="utf-8") as f: return json.load(f)

# ---------------------------------------------------------------- estrategias
def attached(E, layer, netcode, me):
    """ponta E (na camada) toca algo da mesma net alem de 'me'?"""
    for p in all_pads:
        if p.GetNetCode() == netcode and p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(E, FromMM(0.01)): return True
    for t in tracks():
        if t.GetNetCode() != netcode or t.m_Uuid.AsString() == me.m_Uuid.AsString(): continue
        if t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(E, FromMM(0.01)): return True
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetCode() == netcode and z.IsOnLayer(layer) and z.GetFilledPolysList(layer).Contains(E): return True
    return False

def free_ends(t):
    lay = t.GetLayer(); nc = t.GetNetCode()
    return [E for E in (t.GetStart(), t.GetEnd()) if not attached(E, lay, nc, t)]

def try_via_at(pos, netcode, netname, dia=0.6):
    if via_collides(pos, dia, netcode, 0.12): return None
    return add_via(pos, netcode, dia, 0.3)

def stitch_pad(pad, netname):
    """via de stitch a 0.6..2.2 mm do pad, 8 direcoes; para pinos do U7 tenta fora e depois por baixo do corpo."""
    nc = pad.GetNetCode(); c = pad.GetPosition(); lay = item_layer(pad)
    if pad.GetParentFootprint().GetReference() == "U7":
        d = VECTOR2I(c.x - u7c.x, c.y - u7c.y)
        ax = (1, 0) if abs(d.x) > abs(d.y) else (0, 1)
        sg = 1 if (d.x if ax[0] else d.y) > 0 else -1
        for s in (sg, -sg):
            for along in (1.2, 1.5, 1.8, 2.2, 2.6):
                for lat in (0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75):
                    pos = VECTOR2I(c.x + int(FromMM(along) * ax[0] * s + FromMM(lat) * -ax[1]), c.y + int(FromMM(along) * ax[1] * s + FromMM(lat) * ax[0]))
                    knee = VECTOR2I(c.x + int(FromMM(0.9) * ax[0] * s), c.y + int(FromMM(0.9) * ax[1] * s))
                    if not plane_ok(netname, pos): continue
                    if via_collides(pos, 0.6, nc, 0.12) or seg_collides(c, knee, 0.25, lay, nc, 0.1) or seg_collides(knee, pos, 0.25, lay, nc, 0.1): continue
                    add_track(c, knee, 0.25, lay, nc); add_track(knee, pos, 0.25, lay, nc); add_via(pos, nc, 0.6, 0.3)
                    return "stitch U7 %s" % ("fora" if s == sg else "dentro")
        return None
    ang0 = math.atan2(c.y - u7c.y, c.x - u7c.x)
    for d_ in (0.6, 0.75, 0.95, 1.2, 1.5, 1.9, 2.2):
        for k in (0, 1, -1, 2, -2, 3, -3, 4):
            ang = ang0 + k * math.pi / 4
            pos = VECTOR2I(int(c.x + FromMM(d_) * math.cos(ang)), int(c.y + FromMM(d_) * math.sin(ang)))
            if not plane_ok(netname, pos): continue
            if via_collides(pos, 0.6, nc, 0.12) or seg_collides(c, pos, 0.25, lay, nc, 0.1): continue
            add_via(pos, nc, 0.6, 0.3); add_track(c, pos, 0.25, lay, nc)
            return "stitch %.2f" % d_
    # via-in-pad (pad SMD encurralado, ex.: U1.2 entre trilhas e os pads do U7 em B.Cu)
    sz = pad.GetSize(); long_ax = (1, 0) if sz.x >= sz.y else (0, 1); half = ToMM(max(sz.x, sz.y)) / 2
    for dia in (0.6, 0.5):
        for off in (0, 0.2, -0.2, 0.35, -0.35, half - dia / 2 - 0.05, -(half - dia / 2 - 0.05)):
            pos = VECTOR2I(c.x + int(FromMM(off) * long_ax[0]), c.y + int(FromMM(off) * long_ax[1]))
            if not pad.HitTest(pos) or not plane_ok(netname, pos): continue
            if via_collides(pos, dia, nc, 0.1): continue
            add_via(pos, nc, dia, 0.3); return "via-in-pad %.1f" % dia
    # trilha curta ate o cobre vertido da mesma net na mesma camada (pad com thermal faminto junto ao pour)
    # so vale se o contorno vertido que recebe a trilha estiver ele proprio ligado ao plano (via/PTH da net dentro);
    # senao e uma ilha e a "correcao" repete a cada rodada sem efeito
    outlines = []
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != nc or not z.IsOnLayer(lay): continue
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()): outlines.append(polys.Outline(i))
    anchors = [t.GetPosition() for t in tracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == nc and plane_ok(netname, t.GetPosition())]
    anchors += [p.GetPosition() for p in all_pads if p.GetNetCode() == nc and p.GetDrillSize().x > 0 and plane_ok(netname, p.GetPosition())]
    good = [ol for ol in outlines if any(ol.PointInside(a) for a in anchors)]
    for d_ in (0.5, 0.7, 1.0, 1.3, 1.6):
        for k in range(8):
            ang = ang0 + k * math.pi / 4
            pos = VECTOR2I(int(c.x + FromMM(d_) * math.cos(ang)), int(c.y + FromMM(d_) * math.sin(ang)))
            if not any(ol.PointInside(pos) for ol in good): continue
            if seg_collides(c, pos, 0.25, lay, nc, 0.1): continue
            add_track(c, pos, 0.25, lay, nc); return "trilha->pour %.1f" % d_
    return None

def connect_direct(a, b, layer, netcode, width=0.2):
    """reto, depois L (2 variantes)."""
    if seg_collides(a, b, width, layer, netcode) is None:
        add_track(a, b, width, layer, netcode); return "reto"
    for mid in (VECTOR2I(a.x, b.y), VECTOR2I(b.x, a.y)):
        if seg_collides(a, mid, width, layer, netcode) is None and seg_collides(mid, b, width, layer, netcode) is None:
            add_track(a, mid, width, layer, netcode); add_track(mid, b, width, layer, netcode); return "L"
    return connect_z(a, b, layer, netcode, width)

def nearest_same_net_copper(pos, layer, netcode, exclude_uuid=None, rmax=4.0):
    """ponto mais proximo em trilha/pad da mesma net nessa camada (ja conectado ao resto, idealmente)."""
    best = None
    for t in tracks():
        if t.GetNetCode() != netcode or t.GetClass() != "PCB_TRACK" or t.GetLayer() != layer: continue
        if exclude_uuid and t.m_Uuid.AsString() == exclude_uuid: continue
        for E in (t.GetStart(), t.GetEnd()):
            d_ = dist(E, pos)
            if d_ < rmax and (best is None or d_ < best[0]): best = (d_, E)
    for p in all_pads:
        if p.GetNetCode() != netcode or not p.IsOnLayer(layer): continue
        d_ = dist(p.GetPosition(), pos)
        if d_ < rmax and (best is None or d_ < best[0]): best = (d_, p.GetPosition())
    return best[1] if best else None

def island_items(obj):
    """todos os itens (trilhas/vias/pads) ligados galvanicamente a obj (sem zonas)."""
    conn = board.GetConnectivity(); seen = {}; stack = [obj]
    while stack:
        it = stack.pop(); k = it.m_Uuid.AsString()
        if k in seen: continue
        seen[k] = it
        try:
            stack.extend(conn.GetConnectedTracks(it)); stack.extend(conn.GetConnectedPads(it))
        except Exception: pass
    return list(seen.values())

def island_has_plane(items, netname):
    for it in items:
        if it.GetClass() == "PCB_VIA" and plane_ok(netname, it.GetPosition()): return True
        if it.GetClass() == "PAD" and it.GetDrillSize().x > 0 and plane_ok(netname, it.GetPosition()): return True
    return False

def island_via(obj, netname, nc):
    """via para o plano em qualquer ponto das trilhas (ou perto dos pads) da ilha de obj."""
    items = island_items(obj)
    if island_has_plane(items, netname): return None
    cands = []
    for it in items:
        if it.GetClass() == "PCB_TRACK":
            a, b = it.GetStart(), it.GetEnd(); L = dist(a, b); n = max(1, int(L / 0.4))
            for i in range(n + 1):
                cands.append(VECTOR2I(int(a.x + (b.x - a.x) * i / n), int(a.y + (b.y - a.y) * i / n)))
    for c in cands:
        if plane_ok(netname, c) and try_via_at(c, nc, netname): return "via ilha %s" % (pt(c),)
    for it in items:
        if it.GetClass() == "PAD":
            r = stitch_pad(it, netname)
            if r: return "%s %s.%s (ilha)" % (r, it.GetParentFootprint().GetReference(), it.GetNumber())
    return None

def connect_any(a, la, b, lb, nc, width=0.2):
    """liga ponto a (camada la) ao ponto b (camada lb): direto/L; senao via(s) e trilha na outra camada."""
    if la == lb:
        r = connect_direct(a, b, la, nc, width)
        if r: return r
    other = pcbnew.B_Cu if la == pcbnew.F_Cu else pcbnew.F_Cu
    for d_ in (0.0, 0.6, 0.8, 1.0, 1.3, 1.6):
        for k in range(8 if d_ else 1):
            ang = k * math.pi / 4
            va = VECTOR2I(int(a.x + FromMM(d_) * math.cos(ang)), int(a.y + FromMM(d_) * math.sin(ang)))
            if d_ and seg_collides(a, va, width, la, nc) is not None: continue
            if via_collides(va, 0.6, nc, 0.12): continue
            # lado b: mesma camada da via -> direto; senao segunda via perto de b
            if lb == other:
                if seg_collides(va, b, width, other, nc) is None:
                    add_via(va, nc)
                    if d_: add_track(a, va, width, la, nc)
                    add_track(va, b, width, other, nc); return "via+reto"
                for mid in (VECTOR2I(va.x, b.y), VECTOR2I(b.x, va.y)):
                    if seg_collides(va, mid, width, other, nc) is None and seg_collides(mid, b, width, other, nc) is None:
                        add_via(va, nc)
                        if d_: add_track(a, va, width, la, nc)
                        add_track(va, mid, width, other, nc); add_track(mid, b, width, other, nc); return "via+L"
            else:
                for e_ in (0.0, 0.6, 0.8, 1.0, 1.3):
                    for j in range(8 if e_ else 1):
                        ang2 = j * math.pi / 4
                        vb = VECTOR2I(int(b.x + FromMM(e_) * math.cos(ang2)), int(b.y + FromMM(e_) * math.sin(ang2)))
                        if e_ and seg_collides(b, vb, width, lb, nc) is not None: continue
                        if via_collides(vb, 0.6, nc, 0.12) or dist(va, vb) < 0.7: continue
                        for rl in (other, pcbnew.In2_Cu, pcbnew.In1_Cu):  # baseline usa In1/In2 para sinais
                            path = None
                            if seg_collides(va, vb, width, rl, nc) is None: path = [(va, vb)]
                            else:
                                for mid in (VECTOR2I(va.x, vb.y), VECTOR2I(vb.x, va.y)):
                                    if seg_collides(va, mid, width, rl, nc) is None and seg_collides(mid, vb, width, rl, nc) is None:
                                        path = [(va, mid), (mid, vb)]; break
                            if path is None: continue
                            add_via(va, nc); add_via(vb, nc)
                            if d_: add_track(a, va, width, la, nc)
                            if e_: add_track(b, vb, width, lb, nc)
                            for s, e in path: add_track(s, e, width, rl, nc)
                            return "2 vias+%s" % board.GetLayerName(rl)
    return None

def connect_z(a, b, layer, nc, width=0.2):
    """a -> b em 3 segmentos ortogonais (varre a coordenada intermediaria); mesma camada."""
    ax_, ay_, bx_, by_ = ToMM(a.x), ToMM(a.y), ToMM(b.x), ToMM(b.y)
    lo, hi = min(ay_, by_) - 2.0, max(ay_, by_) + 2.0
    ys = sorted([lo + i * 0.25 for i in range(int((hi - lo) / 0.25) + 1)], key=lambda y: abs(y - (ay_ + by_) / 2))
    for ym in ys:
        m1, m2 = VECTOR2I(a.x, FromMM(ym)), VECTOR2I(b.x, FromMM(ym))
        if all(seg_collides(s, e, width, layer, nc) is None for s, e in ((a, m1), (m1, m2), (m2, b))):
            for s, e in ((a, m1), (m1, m2), (m2, b)): add_track(s, e, width, layer, nc)
            return "Z y=%.2f" % ym
    lo, hi = min(ax_, bx_) - 2.0, max(ax_, bx_) + 2.0
    xs = sorted([lo + i * 0.25 for i in range(int((hi - lo) / 0.25) + 1)], key=lambda x: abs(x - (ax_ + bx_) / 2))
    for xm in xs:
        m1, m2 = VECTOR2I(FromMM(xm), a.y), VECTOR2I(FromMM(xm), b.y)
        if all(seg_collides(s, e, width, layer, nc) is None for s, e in ((a, m1), (m1, m2), (m2, b))):
            for s, e in ((a, m1), (m1, m2), (m2, b)): add_track(s, e, width, layer, nc)
            return "Z x=%.2f" % xm
    return None

def astar_route(a, b, layer, nc, width=0.2, step=0.25, margin=2.5, max_nodes=20000):
    """roteador A* em grelha (8 vizinhos) numa unica camada, dentro da bbox a-b inflada; usa so os itens locais."""
    import heapq
    x0, x1 = min(a.x, b.x) - FromMM(margin), max(a.x, b.x) + FromMM(margin)
    y0, y1 = min(a.y, b.y) - FromMM(margin), max(a.y, b.y) + FromMM(margin)
    box = pcbnew.BOX2I(VECTOR2I(x0, y0), VECTOR2I(x1 - x0, y1 - y0))
    obst = []
    for p_ in all_pads:
        if p_.GetNetCode() != nc and p_.IsOnLayer(layer) and p_.GetBoundingBox().Intersects(box): obst.append(p_.GetEffectiveShape(layer))
    for t in tracks():
        if t.GetNetCode() != nc and t.IsOnLayer(layer) and t.GetBoundingBox().Intersects(box): obst.append(t.GetEffectiveShape(layer))
    # furos (via/PTH) de outras redes: hole_clearance 0,25 > clearance 0,12 -> circulo inflado (D-30)
    holes = []
    for t in tracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() != nc and t.GetBoundingBox().Intersects(box): holes.append(pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetDrill() // 2))
    for p_ in all_pads:
        if p_.GetNetCode() != nc and p_.GetDrillSize().x > 0 and p_.GetBoundingBox().Intersects(box): holes.append(pcbnew.SHAPE_CIRCLE(p_.GetPosition(), max(p_.GetDrillSize().x, p_.GetDrillSize().y) // 2))
    keep = [z for z in KEEPOUTS if z.GetDoNotAllowTracks() and z.IsOnLayer(layer)]
    clr = FromMM(0.12); hclr = FromMM(HOLE_CLR)
    def free(p_, q_):
        shp = pcbnew.SHAPE_SEGMENT(p_, q_, FromMM(width))
        if any(z.Outline().Collide(shp, FromMM(0.1)) for z in keep): return False
        if any(shp.Collide(hh, hclr) for hh in holes): return False
        return not any(o.Collide(shp, clr) for o in obst)
    st = FromMM(step)
    def snap(v): return (round((v.x - a.x) / st), round((v.y - a.y) / st))
    def unsnap(g): return VECTOR2I(a.x + g[0] * st, a.y + g[1] * st)
    goal = snap(b); gpos = b
    def h(g): return math.hypot(g[0] - goal[0], g[1] - goal[1])
    start = (0, 0); openq = [(h(start), 0.0, start)]; came = {start: None}; cost = {start: 0.0}; n = 0
    while openq and n < max_nodes:
        _, c, g = heapq.heappop(openq); n += 1
        if h(g) < 1.5 and free(unsnap(g), gpos):
            path = [gpos, unsnap(g)]
            while came[g] is not None: g = came[g]; path.append(unsnap(g))
            path.reverse(); path[0] = a
            # simplifica colineares
            out = [path[0]]
            for i in range(1, len(path) - 1):
                d1 = (path[i].x - out[-1].x, path[i].y - out[-1].y); d2 = (path[i + 1].x - path[i].x, path[i + 1].y - path[i].y)
                if d1[0] * d2[1] - d1[1] * d2[0] != 0: out.append(path[i])
            out.append(path[-1])
            return out
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not dx and not dy: continue
                ng = (g[0] + dx, g[1] + dy); np_ = unsnap(ng)
                if not box.Contains(np_): continue
                nc_ = c + math.hypot(dx, dy)
                if ng in cost and cost[ng] <= nc_: continue
                if not free(unsnap(g), np_): continue
                cost[ng] = nc_; came[ng] = g; heapq.heappush(openq, (nc_ + h(ng), nc_, ng))
    return None

def blockers(shapes_by_layer, netcode, drill_pos=None, drill=0.3):
    """devolve a lista de itens (pads/trilhas/vias/'keepout') que colidem com as formas dadas [(shape, layer, clearance)]."""
    out = []
    hole = pcbnew.SHAPE_CIRCLE(drill_pos, FromMM(drill / 2)) if drill_pos is not None else None
    bb = pcbnew.BOX2I(); [bb.Merge(shp.BBox()) for shp, _, _ in shapes_by_layer]; bb.Inflate(FromMM(0.6))
    pads_n = [p_ for p_ in all_pads if p_.GetNetCode() != netcode and p_.GetBoundingBox().Intersects(bb)]
    trk_n = [t for t in tracks() if t.GetNetCode() != netcode and t.GetBoundingBox().Intersects(bb)]
    for shp, layer, clr in shapes_by_layer:
        for z in KEEPOUTS:
            if (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()) and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(0.1)): out.append("keepout")
        for p_ in pads_n:
            if not p_.IsOnLayer(layer): continue
            if p_.GetEffectiveShape(layer).Collide(shp, FromMM(clr)) or (hole is not None and p_.GetEffectiveShape(layer).Collide(hole, FromMM(HOLE_CLR))): out.append(p_)
        for t in trk_n:
            if not t.IsOnLayer(layer): continue
            if t.GetEffectiveShape(layer).Collide(shp, FromMM(clr)) or (hole is not None and t.GetEffectiveShape(layer).Collide(hole, FromMM(HOLE_CLR))): out.append(t)
    if drill_pos is not None:
        for t in tracks():
            if t.GetClass() == "PCB_VIA" and t.GetNetCode() != netcode and dist(t.GetPosition(), drill_pos) < (ToMM(t.GetDrill()) + drill) / 2 + HOLE_CLR + 0.02: out.append(t)
        for p_ in all_pads:
            if p_.GetDrillSize().x > 0 and p_.GetNetCode() != netcode and dist(p_.GetPosition(), drill_pos) < (ToMM(p_.GetDrillSize().x) + drill) / 2 + HOLE_CLR + 0.02: out.append(p_)
    return out

def uid(x): return x.m_Uuid.AsString()   # id() de proxies swig nao e estavel
def track_chain(t0):
    """cadeia de trilhas destravadas (mesma rede, mesma camada) ligadas a t0; devolve (trilhas, ancoras=[(ponto, item)]) ou None se ramificar."""
    conn = board.GetConnectivity(); lay = t0.GetLayer(); nc = t0.GetNetCode()
    chain = {uid(t0): t0}; todo = [t0]; anchors = []
    while todo:
        t = todo.pop()
        for end in (t.GetStart(), t.GetEnd()):
            touching = [x for x in conn.GetConnectedItems(t) if x.GetClass() in ("PCB_TRACK", "PCB_VIA", "PAD") and x.GetNetCode() == nc and x.HitTest(end, FromMM(0.02))]
            touching = [x for x in touching if uid(x) != uid(t)]
            for x in touching:
                if x.GetClass() == "PCB_TRACK" and x.GetLayer() == lay and not x.IsLocked():
                    if uid(x) not in chain: chain[uid(x)] = x; todo.append(x)
                else:
                    anchors.append((end, x))
            if not touching: anchors.append((end, None))
    pts_ = []
    for a_, it in anchors:
        if not any(dist(a_, b_) < 0.02 for b_, _ in pts_): pts_.append((a_, it))
    if len(pts_) != 2: return None
    return list(chain.values()), pts_

def ripup_reroute(pad, target_pos, target_layers, net_name):
    """pad SMD encurralado: procura um ponto de via perto do pad cujo unico bloqueio seja uma cadeia de trilhas destravadas de
    outra rede de sinal; remove-a, poe via + stub + A* interno para a rede do pad e re-roteia a outra rede por A* na mesma camada."""
    nc = pad.GetNetCode(); play = item_layer(pad); pc = pad.GetPosition()
    cands = []
    grid = sorted(((math.hypot(dx, dy), dx, dy) for dx in range(-12, 13) for dy in range(-12, 13) if 0.45 <= math.hypot(dx, dy) / 10.0 <= 1.25))
    for d_, dx, dy in grid:
            va = VECTOR2I(pc.x + FromMM(dx / 10.0), pc.y + FromMM(dy / 10.0))
            for dia in (0.6, 0.5):
                bl = blockers([(pcbnew.SHAPE_CIRCLE(va, FromMM(dia / 2)), l, 0.12) for l in LAYERS4] + [(pcbnew.SHAPE_SEGMENT(pc, va, FromMM(0.2)), play, 0.12)], nc, va, 0.3)
                if not bl: continue   # sem bloqueio -> outras estrategias ja teriam resolvido
                if any(not (hasattr(b, "GetClass") and b.GetClass() == "PCB_TRACK" and not b.IsLocked() and b.GetNetname() not in ("GND", "+3V3", "+5V", "VBUS", "USB_PWR")) for b in bl): continue
                nets_b = {b.GetNetCode() for b in bl}
                if len(nets_b) != 1: continue
                cands.append((d_, dia, va, bl)); break
    seen = set()
    for d_, dia, va, bl in cands:
        key = tuple(sorted(uid(b) for b in bl))
        if key in seen: continue
        seen.add(key)
        ch = track_chain(bl[0])
        if ch is None: continue
        chain, anchors = ch
        if not all(uid(b) in {uid(c) for c in chain} for b in bl): continue
        onc = chain[0].GetNetCode(); olay = chain[0].GetLayer(); ow = ToMM(chain[0].GetWidth()); oname = chain[0].GetNetname()
        for t in chain: board.RemoveNative(t)
        n0 = len(added); ok = False
        try:
            if via_collides(va, dia, nc, 0.12) is None and seg_collides(pc, va, 0.2, play, nc) is None:
                add_track(pc, va, 0.2, play, nc); add_via(va, nc, dia, 0.3)
                path = None
                for rl in target_layers:
                    path = astar_route(va, target_pos, rl, nc)
                    if path:
                        for s_, e_ in zip(path, path[1:]): add_track(s_, e_, 0.2, rl, nc)
                        break
                if path:
                    path2 = astar_route(anchors[0][0], anchors[1][0], olay, onc, ow)
                    if path2:
                        for s_, e_ in zip(path2, path2[1:]): add_track(s_, e_, ow, olay, onc)
                        ok = True
        finally:
            if not ok:
                for t in tracks():
                    pass
                # desfaz o que foi adicionado nesta tentativa
                newitems = [t for t in tracks() if not t.IsLocked()]
                while len(added) > n0:
                    rec = added.pop()
                    for t in newitems:
                        if rec[0] == "via" and t.GetClass() == "PCB_VIA" and pt(t.GetPosition()) == rec[1]: board.RemoveNative(t); break
                        if rec[0] == "track" and t.GetClass() == "PCB_TRACK" and {pt(t.GetStart()), pt(t.GetEnd())} == {rec[1], rec[2]} and board.GetLayerName(t.GetLayer()) == rec[3]: board.RemoveNative(t); break
                for t in chain: board.Add(t)
        if ok: return "ripup %s (%d seg) + via %.1f %s + A*" % (oname, len(chain), dia, pt(va))
    return None

def route_astar(a, b, layer, nc, width=0.2):
    path = astar_route(a, b, layer, nc, width)
    if not path: return None
    for s_, e_ in zip(path, path[1:]): add_track(s_, e_, width, layer, nc)
    return "A* %d seg" % (len(path) - 1)

def fix_pair(A, B):
    net = A["net"] or B["net"]
    if net is None or net not in nets: return "net?"
    nc = nets[net].GetNetCode()
    if POWER_ONLY and net not in ("GND", "+3V3", "+5V"): return None
    kinds = (A["kind"], B["kind"])
    # D) zona x zona / zona x pad PTH: ilha -> via dentro da ilha tratada em fix_islands
    if kinds == ("zone", "zone"): return "island (ver D)"
    # A0) potencia: via para o plano em qualquer ponto da ilha que ainda nao toca o plano
    if net in ("GND", "+3V3", "+5V"):
        for it in (A, B):
            if it["kind"] in ("pad", "track", "via") and it["obj"] is not None:
                r = island_via(it["obj"], net, nc)
                if r: return r
    # A) pads de potencia
    for it in (A, B):
        if it["kind"] == "pad" and it["obj"] is not None and net in ("GND", "+3V3", "+5V"):
            r = stitch_pad(it["obj"], net)
            if r: return "%s %s.%s" % (r, it["ref"], it["num"])
    # B) trilha(s) com ponta solta -> via na ponta (potencia ou transicao de camada)
    trk = [it for it in (A, B) if it["kind"] == "track" and it["obj"] is not None and not it["obj"].IsLocked()]
    if len(trk) == 2 and A["layer"] != B["layer"]:
        ea, eb = free_ends(A["obj"]), free_ends(B["obj"])
        pairs = sorted(((dist(x, y), x, y) for x in (ea or [A["obj"].GetStart(), A["obj"].GetEnd()]) for y in (eb or [B["obj"].GetStart(), B["obj"].GetEnd()])), key=lambda k: k[0])
        for d_, x, y in pairs:
            if d_ > 1.5: break
            for cand in (x, y, VECTOR2I((x.x + y.x) // 2, (x.y + y.y) // 2)):
                if try_via_at(cand, nc, net):
                    if cand != x: add_track(x, cand, 0.2, A["layer"], nc)
                    if cand != y: add_track(y, cand, 0.2, B["layer"], nc)
                    return "via transicao %s" % (pt(cand),)
    for it in trk:
        t = it["obj"]
        for E in free_ends(t):
            if net in PLANE_NETS or net == "+5V":
                if plane_ok(net, E) and try_via_at(E, nc, net): return "via ponta %s" % (pt(E),)
                # recua ao longo da trilha
                O = t.GetEnd() if E == t.GetStart() else t.GetStart(); L = dist(E, O)
                for back in (0.35, 0.7, 1.0):
                    if back >= L: break
                    P = VECTOR2I(int(E.x + (O.x - E.x) * back / L), int(E.y + (O.y - E.y) * back / L))
                    if plane_ok(net, P) and try_via_at(P, nc, net): return "via recuo %s" % (pt(P),)
    # C) sinal: trilha x pad em camadas diferentes -> via na ponta + trilha ate o pad; mesma camada -> direto
    padit = next((it for it in (A, B) if it["kind"] == "pad" and it["obj"] is not None), None)
    other = B if padit is A else A
    if padit and other["kind"] in ("track", "via") and other["obj"] is not None:
        p = padit["obj"]; play = item_layer(p); pc = p.GetPosition()
        if other["kind"] == "via":
            r = connect_direct(other["pos"], pc, play, nc)
            if r: return "via->pad %s" % r
        else:
            t = other["obj"]
            ends = free_ends(t) or [t.GetStart(), t.GetEnd()]
            if t.GetLayer() == play:
                for E in sorted(ends, key=lambda e: dist(e, pc)):
                    r = connect_direct(E, pc, play, nc)
                    if r: return "trilha->pad %s" % r
            else:
                for E in sorted(ends, key=lambda e: dist(e, pc)):
                    v = try_via_at(E, nc, net)
                    if v:
                        r = connect_direct(E, pc, play, nc)
                        if r: return "via ponta + %s" % r
                        board.RemoveNative(v); added.pop()
    # fallback: ligar cada item ao cobre mais proximo da mesma net na propria camada
    # C2) sinal: pad x pad / pad x trilha com vias e trilha na outra camada
    if True:
        pts = []
        for it in (A, B):
            if it["obj"] is None: continue
            if it["kind"] == "pad": pts.append((it["obj"].GetPosition(), item_layer(it["obj"])))
            elif it["kind"] == "track":
                t = it["obj"]; ends = free_ends(t) or [t.GetStart(), t.GetEnd()]
                pts.append((ends[0], t.GetLayer()))
            elif it["kind"] == "via": pts.append((it["pos"], pcbnew.F_Cu))
        if len(pts) == 2:
            r = connect_any(pts[0][0], pts[0][1], pts[1][0], pts[1][1], nc)
            if r: return "connect_any %s" % r
    if net not in ("GND", "+3V3", "+5V"):
        padit = next((it for it in (A, B) if it["kind"] == "pad" and it["obj"] is not None), None)
        other = B if padit is A else A
        # pad x pad (ex.: U7.123 B.Cu x U9.4 F.Cu): tenta a partir dos dois pads
        orders = [(padit, other)] + ([(other, padit)] if padit is not None and other["kind"] == "pad" and other["obj"] is not None else [])
        for padit, other in orders:
          if padit is not None and other["obj"] is not None or (padit is not None and other["kind"] == "via"):
              p = padit["obj"]; play = item_layer(p); pc = p.GetPosition()
              tgts = []
              if other["kind"] == "via": tgts = [(other["pos"], play)]
              elif other["kind"] == "track":
                  t = other["obj"]; tgts = [(E, t.GetLayer()) for E in (free_ends(t) or [t.GetStart(), t.GetEnd()])]
              elif other["kind"] == "pad": tgts = [(other["obj"].GetPosition(), item_layer(other["obj"]))]
              for tp, tl in tgts:
                  if tl == play:
                      r = route_astar(pc, tp, play, nc)
                      if r: return "pad A* %s" % r
              # pad SMD x via: coloca via perto do pad (trilha curta na camada do pad) e A* numa camada interna ate a via alvo
              for d_ in (0.6, 0.8, 1.0, 1.3, 1.6, 2.0):
                  for k in range(8):
                      ang = k * math.pi / 4; va = VECTOR2I(int(pc.x + FromMM(d_) * math.cos(ang)), int(pc.y + FromMM(d_) * math.sin(ang)))
                      if seg_collides(pc, va, 0.2, play, nc) is not None or via_collides(va, 0.6, nc, 0.12) is not None: continue
                      for tp, tl in tgts:
                          # alvo = via (todas as camadas) ou ponta de trilha (so a camada dela)
                          layers = [pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.B_Cu if play == pcbnew.F_Cu else pcbnew.F_Cu] if other["kind"] == "via" else [tl]
                          for rl in layers:
                              if rl == play: continue
                              path = astar_route(va, tp, rl, nc)
                              if path:
                                  add_track(pc, va, 0.2, play, nc); add_via(va, nc, 0.6, 0.3)
                                  for s_, e_ in zip(path, path[1:]): add_track(s_, e_, 0.2, rl, nc)
                                  return "pad via + A* %s %d seg" % (board.GetLayerName(rl), len(path) - 1)
              # ultimo recurso: rip-up de uma trilha de sinal destravada que encurrala o pad
              if other["kind"] == "via":
                  r = ripup_reroute(p, other["pos"], (pcbnew.In1_Cu, pcbnew.In2_Cu), net)
                  if r: return r
              elif other["kind"] in ("track", "pad"):
                  for tp, tl in tgts:
                      r = ripup_reroute(p, tp, (tl,), net)
                      if r: return r
              # camada diferente: via perto do alvo (ponta de trilha) e A* na camada do pad
              for tp, tl in tgts:
                  if tl != play and try_via_at(tp, nc, net):
                      r = route_astar(pc, tp, play, nc)
                      if r: return "via alvo + A* %s" % r
                      v = [t for t in tracks() if t.GetClass() == "PCB_VIA" and dist(t.GetPosition(), tp) < 0.01]
                      for x in v: board.RemoveNative(x)
                      added.pop()
    for it in (A, B):
        if it["kind"] == "pad" and it["obj"] is not None:
            lay = item_layer(it["obj"]); pc = it["obj"].GetPosition()
            tgt = nearest_same_net_copper(pc, lay, nc)
            if tgt is not None and dist(tgt, pc) > 0.05:
                r = connect_direct(pc, tgt, lay, nc)
                if r: return "pad->cobre %s" % r
        if it["kind"] == "track" and it["obj"] is not None:
            t = it["obj"]
            for E in free_ends(t):
                tgt = nearest_same_net_copper(E, t.GetLayer(), nc, t.m_Uuid.AsString())
                if tgt is not None:
                    r = connect_direct(E, tgt, t.GetLayer(), nc)
                    if r: return "ponta->cobre %s" % r
    return None

def fix_islands():
    """ilhas da zona GND em F.Cu/B.Cu sem via/PTH GND -> via no interior (liga ao plano In2)."""
    gnd = nets["GND"].GetNetCode(); n = 0
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    gvias = [t.GetPosition() for t in tracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd]
    gpth = [p.GetPosition() for p in all_pads if p.GetNetCode() == gnd and p.GetDrillSize().x > 0]
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != gnd: continue
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(lay): continue
            polys = z.GetFilledPolysList(lay)
            for i in range(polys.OutlineCount()):
                ol = polys.Outline(i)
                if ol.Area() < FromMM(1.0) * FromMM(1.0): continue
                if any(ol.PointInside(v) for v in gvias + gpth): continue
                # candidatos: centroide e pontos ao longo do contorno encolhido
                bb = ol.BBox(); cands = [VECTOR2I((bb.GetLeft() + bb.GetRight()) // 2, (bb.GetTop() + bb.GetBottom()) // 2)]
                for k in range(0, ol.PointCount(), max(1, ol.PointCount() // 24)):
                    v = ol.CPoint(k); cands.append(VECTOR2I(int(v.x + (cands[0].x - v.x) * 0.25), int(v.y + (cands[0].y - v.y) * 0.25)))
                for c in cands:
                    if ol.PointInside(c) and via_collides(c, 0.6, gnd, 0.15) is None:
                        add_via(c, gnd, 0.6, 0.3); n += 1; break
    return n

def net_clusters(netname):
    """agrupamentos galvanicos (pads/trilhas/vias + zonas) da net; o maior primeiro."""
    nc = nets[netname].GetNetCode(); conn = board.GetConnectivity()
    items = [p for p in all_pads if p.GetNetCode() == nc] + [t for t in tracks() if t.GetNetCode() == nc]
    seen = {}; clusters = []
    for it in items:
        if uid(it) in seen: continue
        try: cl = list(conn.GetConnectedItems(it, [pcbnew.PCB_PAD_T, pcbnew.PCB_VIA_T, pcbnew.PCB_TRACE_T, pcbnew.PCB_ARC_T]))
        except TypeError: cl = list(conn.GetConnectedItems(it))
        members = {uid(it): it}
        for c in cl:
            if c.GetClass() in ("PAD", "PCB_VIA", "PCB_TRACK", "PCB_ARC"): members[uid(c)] = c
        for k in members: seen[k] = True
        clusters.append(list(members.values()))
    clusters.sort(key=len, reverse=True)
    return clusters

def main_fill_outlines(netname, layers, main_items):
    """contornos do preenchimento (por camada) que contem alguma via/PTH do agrupamento principal."""
    out = {}
    anchors = [it.GetPosition() for it in main_items if it.GetClass() == "PCB_VIA" or (it.GetClass() == "PAD" and it.GetDrillSize().x > 0)]
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != netname: continue
        for lay in layers:
            if not z.IsOnLayer(lay): continue
            polys = z.GetFilledPolysList(lay)
            for i in range(polys.OutlineCount()):
                ol = polys.Outline(i)
                if any(ol.PointInside(a_) for a_ in anchors):
                    out.setdefault(lay, []).append((ol, [polys.Hole(i, j) for j in range(polys.HoleCount(i))]))
    return out

def fill_free_at(fills, pos, margin=0.55):
    """pos esta dentro de um contorno 'principal' e a >= margin de qualquer borda (furos incluidos)?"""
    m = FromMM(margin)
    for ol, holes in fills:
        if not ol.PointInside(pos) or ol.Distance(pos, True) < m: continue
        if any(h.PointInside(pos) or h.Distance(pos, True) < m for h in holes): continue
        return True
    return False

def fix_clusters(netname, width=0.3):
    """agrupamentos da net isolados do principal (ilhas cercadas por trilhas internas do Freerouting): via nova num ponto
    do preenchimento principal (F/In2/B p/ GND; In1 p/ +3V3) + trilha F.Cu/B.Cu a partir de uma via/pad/trilha da ilha."""
    nc = nets[netname].GetNetCode(); fixes = []
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    cls = net_clusters(netname)
    if len(cls) < 2: return fixes
    main = cls[0]
    plane_layers = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if netname == "GND" else ((pcbnew.In1_Cu,) if netname == "+3V3" else ())
    fills = main_fill_outlines(netname, plane_layers, main)
    fill_any = [f for lay in fills for f in fills[lay]]
    if not fill_any: return fixes
    for cl in cls[1:]:
        srcs = []   # (ponto, camada) de partida na ilha
        for it in cl:
            if it.GetClass() == "PCB_VIA": srcs += [(it.GetPosition(), pcbnew.F_Cu), (it.GetPosition(), pcbnew.B_Cu)]
        for it in cl:
            if it.GetClass() == "PAD":
                for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if it.IsOnLayer(lay): srcs.append((it.GetPosition(), lay))
        for it in cl:
            if it.GetClass() == "PCB_TRACK" and it.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
                srcs += [(it.GetStart(), it.GetLayer()), (it.GetEnd(), it.GetLayer())]
        done = None
        # candidatos (via nova no preenchimento principal) ordenados pela distancia a cada fonte; via 0,6 e depois 0,5
        def cands_for(P, rmax=5.0):
            out = []; seen_ = set()
            for i_ in range(3, int(rmax / 0.2) + 1):
                r_ = i_ * 0.2
                for k in range(24):
                    ang = k * math.pi / 12
                    c = VECTOR2I(int(P.x + FromMM(r_) * math.cos(ang)), int(P.y + FromMM(r_) * math.sin(ang)))
                    key = (c.x // FromMM(0.1), c.y // FromMM(0.1))
                    if key in seen_ or not fill_free_at(fill_any, c, 0.4): continue
                    seen_.add(key)
                    for dia in (0.6, 0.5):
                        if via_collides(c, dia, nc, 0.15) is None: out.append((c, dia)); break
            return out
        for P, lay in srcs:
            for c, dia in cands_for(P):
                if seg_collides(P, c, width, lay, nc) is None:
                    add_via(c, nc, dia, 0.3); add_track(P, c, width, lay, nc); done = "ponte %s %s->%s via %.1f" % (board.GetLayerName(lay), pt(P), pt(c), dia); break
                r = connect_z(P, c, lay, nc, width) if dist(P, c) < 2.5 else None
                if r: add_via(c, nc, dia, 0.3); done = "ponte %s %s %s->%s via %.1f" % (board.GetLayerName(lay), r, pt(P), pt(c), dia); break
            if done: break
        if not done:
            for P, lay in srcs[:8]:
                for c, dia in cands_for(P)[:12]:
                    path = astar_route(P, c, lay, nc, width, step=0.2, margin=1.5, max_nodes=8000)
                    if path:
                        add_via(c, nc, dia, 0.3)
                        for s_, e_ in zip(path, path[1:]): add_track(s_, e_, width, lay, nc)
                        done = "ponte A* %s %s->%s via %.1f" % (board.GetLayerName(lay), pt(P), pt(c), dia); break
                if done: break
        if not done:
            # D-30: sem ponto livre no preenchimento -> trilha direta ate item do agrupamento principal em F/B.Cu (sem via nova)
            tgts = []
            for it in main:
                if it.GetClass() == "PCB_VIA": tgts += [(it.GetPosition(), pcbnew.F_Cu), (it.GetPosition(), pcbnew.B_Cu)]
                elif it.GetClass() == "PAD":
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if it.IsOnLayer(lay): tgts.append((it.GetPosition(), lay))
                elif it.GetClass() == "PCB_TRACK" and it.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
                    tgts += [(it.GetStart(), it.GetLayer()), (it.GetEnd(), it.GetLayer())]
            pairs = sorted(((dist(P, T), P, T, lay) for P, lay in srcs for T, lt in tgts if lt == lay and dist(P, T) < 6.0), key=lambda x: x[0])
            for w_ in (width, 0.2, 0.15):
                for d_, P, T, lay in pairs[:60]:
                    if seg_collides(P, T, w_, lay, nc) is None:
                        add_track(P, T, w_, lay, nc); done = "trilha direta %s %s->%s w%.2f" % (board.GetLayerName(lay), pt(P), pt(T), w_); break
                    r = connect_z(P, T, lay, nc, w_) if d_ < 3.0 else None
                    if r: done = "trilha %s %s %s->%s w%.2f" % (board.GetLayerName(lay), r, pt(P), pt(T), w_); break
                if done: break
            if not done:
                for d_, P, T, lay in pairs[:20]:
                    path = astar_route(P, T, lay, nc, 0.2, step=0.2, margin=1.5, max_nodes=8000)
                    if path:
                        for s_, e_ in zip(path, path[1:]): add_track(s_, e_, 0.2, lay, nc)
                        done = "trilha A* %s %s->%s" % (board.GetLayerName(lay), pt(P), pt(T)); break
        desc = "%s ilha %d itens @%s" % (netname, len(cl), pt(cl[0].GetPosition()))
        if done: fixes.append((desc, done)); print("   ", desc, "->", done)
        else: W("sem ponte para " + desc)
    return fixes

# ---------------------------------------------------------------- H: violacoes de furo deixadas pelo Freerouting
def remove_via_and_stubs(v):
    """remove a via (destravada) e as trilhas destravadas que ficarem com ponta solta."""
    nc = v.GetNetCode(); pos = v.GetPosition(); board.RemoveNative(v); n = 1
    for _ in range(6):
        ch = False
        for t in tracks():
            if t.GetClass() != "PCB_TRACK" or t.IsLocked() or t.GetNetCode() != nc: continue
            if free_ends(t): board.RemoveNative(t); n += 1; ch = True
        if not ch: break
    return n

def fix_holes(drc):
    out = fix_track_vs_hole(drc)   # D-30: afunilar primeiro; só depois arrancar vias
    for v in drc.get("violations", []):
        if v["type"] not in ("hole_to_hole", "hole_clearance") or v.get("handled"): continue
        A, B = parse(v["items"][0]), parse(v["items"][1])
        vias = [x for x in (A, B) if x["kind"] == "via" and x["obj"] is not None and not x["obj"].IsLocked()]
        both = [x for x in (A, B) if x["kind"] == "via" and x["obj"] is not None]
        if not both: continue
        if v["type"] == "hole_to_hole" and len(both) == 2 and A["net"] == B["net"]:
            # vias da mesma net coladas: remove a destravada (ou a com menos trilhas) e religa as suas trilhas na outra
            keep, drop = sorted(both, key=lambda x: (not x["obj"].IsLocked(), len(board.GetConnectivity().GetConnectedTracks(x["obj"]))), reverse=True)
            kp, dp = keep["obj"].GetPosition(), drop["obj"].GetPosition(); nc = keep["obj"].GetNetCode()
            att = [t for t in board.GetConnectivity().GetConnectedTracks(drop["obj"]) if t.GetClass() == "PCB_TRACK"]
            board.RemoveNative(drop["obj"])
            for t in att:
                E = t.GetStart() if dist(t.GetStart(), dp) < 0.02 else t.GetEnd()
                if dist(E, kp) > 0.02: add_track(E, kp, ToMM(t.GetWidth()), t.GetLayer(), nc)
            out.append(("merge vias", pt(dp), "->", pt(kp))); continue
        if not vias: continue
        if v["type"] == "hole_clearance" and len(vias) == 1:
            # trilha do FR (outra net) sobre o furo da minha via de stitch: remove via + stubs; proxima rodada re-stitcha
            other = B if vias[0] is A else A
            if other["kind"] == "track" and other["obj"] is not None and not other["obj"].IsLocked():
                n = remove_via_and_stubs(vias[0]["obj"]); out.append(("remove via (hole_clearance)", pt(vias[0]["pos"]), "%d itens" % n))
    out += fix_shorts(drc)
    return out

def _remove_track_and_stubs(t):
    nc = t.GetNetCode(); board.RemoveNative(t); n = 1
    for _ in range(6):
        ch = False
        for s in tracks():
            if s.GetClass() != "PCB_TRACK" or s.IsLocked() or s.GetNetCode() != nc: continue
            if free_ends(s): board.RemoveNative(s); n += 1; ch = True
        if not ch: break
    return n

def fix_shorts(drc):
    """shorting_items / clearance entre itens destravados do Freerouting (visto em 26-10: via BUS1O_RX x trilha SBU1_ADC In2 a
    0,09 mm do centro — saída do próprio FR, D-30). Remove a via (ou a trilha) destravada + stubs; a rodada seguinte religa via fix_pair."""
    out = []
    for v in drc.get("violations", []):
        if v["type"] not in ("shorting_items", "clearance"): continue
        A, B = parse(v["items"][0]), parse(v["items"][1])
        if A.get("net") == B.get("net"): continue
        unl = [x for x in (A, B) if x["kind"] in ("via", "track") and x["obj"] is not None and not x["obj"].IsLocked()]
        if not unl: continue
        x = next((u for u in unl if u["kind"] == "via"), unl[0])
        if x["kind"] == "via": n = remove_via_and_stubs(x["obj"]); out.append(("remove via (%s)" % v["type"], x["net"], pt(x["pos"]), "%d itens" % n))
        else: n = _remove_track_and_stubs(x["obj"]); out.append(("remove trilha (%s)" % v["type"], x["net"], pt(x["pos"]), "%d itens" % n))
    return out

RX_ACT = re.compile(r"clearance ([\d.,]+) mm; actual ([\d.,]+) mm")
def fix_track_vs_hole(drc):
    """hole_clearance trilha destravada (FR) x pad PTH do baseline (ex.: +12V In2 x P1.B7, 0,2317 < 0,25): o DSN não
    exprime folga trilha->furo (wire_pin 160 trava o FR — ver D-29). Afunila a trilha o estritamente necessário (>= 0,1375)."""
    out = []
    for v in drc.get("violations", []):
        if v["type"] != "hole_clearance": continue
        A, B = parse(v["items"][0]), parse(v["items"][1])
        trk = next((x for x in (A, B) if x["kind"] == "track"), None)
        pad = next((x for x in (A, B) if x["kind"] == "pad" and x.get("pth")), None)
        if pad is None: pad = next((x for x in (A, B) if x["kind"] == "via" and x["obj"] is not None), None)  # D-30: também furo de via
        if trk is None or pad is None: continue
        m = RX_ACT.search(v.get("description", ""))
        if not m: continue
        deficit = float(m.group(1).replace(",", ".")) - float(m.group(2).replace(",", "."))
        pos = trk["pos"]
        cands = [t for t in tracks() if t.GetClass() == "PCB_TRACK" and not t.IsLocked() and t.GetNetname() == trk["net"]
                 and t.GetLayer() == trk["layer"]]
        if not cands: continue
        t = min(cands, key=lambda t: ToMM(pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pos)))
        if ToMM(pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pos)) > ToMM(t.GetWidth()): continue
        neww = round(ToMM(t.GetWidth()) - 2 * (deficit + 0.01), 3)
        if neww < 0.1375:
            if not t.IsLocked() and trk["net"] not in ("GND",):
                n = _remove_track_and_stubs(t); v["handled"] = True
                out.append(("remove trilha (hole_clearance, afunilar daria %.3f)" % neww, trk["net"], pt(pos), "%d itens" % n)); continue
            W("hole_clearance %s x %s: afunilar daria %.3f < 0,1375" % (trk["net"], pad.get("ref", pad.get("net")), neww)); continue
        t.SetWidth(FromMM(neww)); v["handled"] = True; out.append(("afunila trilha", trk["net"], pt(pos), "%.3f" % neww))
    return out

# ---------------------------------------------------------------- M: ajustes manuais documentados (geometria do baseline)
def manual_fixes():
    out = []
    # M1: U1.2 (GND, SOT-23-6, F.Cu) ficou encurralado: a via GND do baseline (120.41, 53.18) caiu sob o pad U7.120 (B.Cu)
    # e o unico ponto de via (119.0, 53.42, via-in-pad 0.5) e bloqueado pelo furo x trilha +5V In1 em x = 119.11.
    # Desvia o segmento vertical dessa trilha +5V In1 para x = 117.6 e coloca a via-in-pad (normalmente ja feito pela fase M do 5b; aqui so como fallback).
    # (x = 118.3 deixava a borda da trilha de 1,0 mm a 118,8 > borda da via a 118,75 -> shorting_items; a via era
    # verificada antes de os novos segmentos existirem.)
    gnd = nets["GND"].GetNetCode(); v5 = nets["+5V"].GetNetCode()
    seg = [t for t in tracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.In1_Cu and t.GetNetCode() == v5
           and {pt(t.GetStart()), pt(t.GetEnd())} == {(119.11, 51.23), (119.11, 53.96)}]
    seg2 = [t for t in tracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.In1_Cu and t.GetNetCode() == v5
            and {pt(t.GetStart()), pt(t.GetEnd())} == {(118.54, 54.53), (119.11, 53.96)}]
    seg3 = [t for t in tracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.In1_Cu and t.GetNetCode() == v5
            and {pt(t.GetStart()), pt(t.GetEnd())} in ({(119.11, 53.96), (121.58, 56.42)}, {(119.11, 53.96), (121.575, 56.425)})]
    u1 = board.FindFootprintByReference("U1"); p2 = [p for p in u1.Pads() if p.GetNumber() == "2"][0] if u1 else None
    vpos = mmv(119.0, 53.42)
    if seg and seg2 and seg3 and p2 is not None and p2.GetNetCode() == gnd and not any(t.GetClass() == "PCB_VIA" and dist(t.GetPosition(), vpos) < 0.3 for t in tracks()):
        w = ToMM(seg[0].GetWidth()); a = mmv(119.11, 51.23); k1 = mmv(117.6, 52.74); k2 = mmv(117.6, 53.59); j = mmv(118.54, 54.53); d1 = mmv(119.6, 54.45)
        d2 = seg3[0].GetEnd() if dist(seg3[0].GetStart(), mmv(119.11, 53.96)) < 0.05 else seg3[0].GetStart()
        old = [seg[0], seg2[0], seg3[0]]
        for t in old: board.RemoveNative(t)
        segs = ((a, k1, w), (k1, k2, w), (k2, j, w), (j, d1, w), (d1, d2, w))
        ok = all(seg_collides(s_, e_, w_, pcbnew.In1_Cu, v5, 0.1) is None for s_, e_, w_ in segs)
        new = [add_track(s_, e_, w_, pcbnew.In1_Cu, v5) for s_, e_, w_ in segs] if ok else []
        vc = via_collides(vpos, 0.5, gnd, 0.1) if ok else "segmentos"
        if ok and vc is None:
            add_via(vpos, gnd, 0.5, 0.3); out.append("M1 U1.2 via-in-pad 0.5 + desvio +5V In1 (x=117.6, diagonal encurtada)")
        else:
            for t in new:
                if t is not None: board.RemoveNative(t)
            del added[len(added) - len([t for t in new if t is not None]):]
            for t in old: board.Add(t)
            W("M1 nao aplicavel: colisao no desvio +5V In1 ou na via U1.2: %s" % ([seg_collides(s_, e_, w_, pcbnew.In1_Cu, v5, 0.1) for s_, e_, w_ in segs] + [vc]))
    return out

# ---------------------------------------------------------------- ciclo
def main(rounds=None, power_only=None, lock=None):
  global ROUNDS, POWER_ONLY, LOCK_ADDED, REPORT
  if rounds is not None: ROUNDS = rounds
  if power_only is not None: POWER_ONLY = power_only; REPORT = os.path.join(ROOT, "06_REPORTS", "step5c_pre.json" if power_only else "step5c_fix.json")
  if lock is not None: LOCK_ADDED = lock
  for rnd in range(ROUNDS):
      pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
      pcbnew.SaveBoard(PCB, board)
      drc = run_drc()
      unc = drc["unconnected_items"]
      rr = {"round": rnd, "unconnected": len(unc), "fixes": [], "unfixed": []}
      print("round %d: unconnected %d" % (rnd, len(unc)))
      nholes = sum(1 for v in drc.get("violations", []) if v["type"] in ("hole_to_hole", "hole_clearance") and any(parse(i)["kind"] == "via" and parse(i)["obj"] is not None for i in v["items"]))
      ntrk = sum(1 for v in drc.get("violations", []) if v["type"] == "hole_clearance" and rnd < 2
                 and any(parse(i)["kind"] == "track" for i in v["items"]) and any(parse(i).get("pth") for i in v["items"]))
      print("   violacoes de furo com via destravada:", nholes, "| trilha x PTH:", ntrk)
      nshort = sum(1 for v in drc.get("violations", []) if v["type"] in ("shorting_items", "clearance")
                   and any(parse(i)["kind"] in ("via", "track") and parse(i)["obj"] is not None and not parse(i)["obj"].IsLocked() for i in v["items"]))
      if nshort: print("   curtos/clearance com item destravado:", nshort)
      if (not unc and nholes == 0 and ntrk == 0 and nshort == 0) or DRY: report["rounds"].append(rr); break
      before = len(added)
      if rnd == 0:
          mf = manual_fixes()
          if mf: rr["fixes"].append(("manual", mf)); print("   manual:", mf); before = -1
      hf = fix_holes(drc)
      if hf: rr["fixes"].append(("furos", hf)); print("   furos:", hf); before = -1
      for u in unc:
          A, B = parse(u["items"][0]), parse(u["items"][1])
          desc = " <> ".join(i["description"] for i in u["items"])
          try:
              r = fix_pair(A, B)
          except Exception as e:
              r = None; W("exc %s: %s" % (desc, e))
          (rr["fixes"] if r else rr["unfixed"]).append((desc, r) if r else desc)
          print("  ", "OK " if r else "-- ", desc[:110], "->", r)
      ni = fix_islands()
      if ni: rr["fixes"].append(("ilhas GND", "%d vias" % ni)); print("   ilhas GND: %d vias" % ni)
      if not POWER_ONLY:
          for nn in ("GND", "+3V3"):
              fc = fix_clusters(nn)
              if fc: rr["fixes"].append(("pontes " + nn, fc))
      report["rounds"].append(rr)
      if len(added) == before:
          print("nada mais a fazer"); break
  report["added"] = added
  # D-30: vias destravadas que ficaram ligadas numa só camada (restos de rip-up/remove_via_and_stubs) -> via_dangling na DRC
  pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
  cn = board.GetConnectivity(); ndang = 0
  for v in [t for t in tracks() if t.GetClass() == "PCB_VIA" and not t.IsLocked()]:
      lays = set()
      for t in cn.GetConnectedTracks(v):
          if t.GetClass() == "PCB_TRACK": lays.add(t.GetLayer())
      for p in cn.GetConnectedPads(v):
          for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
              if p.IsOnLayer(l): lays.add(l)
      for z in board.Zones():
          if z.GetNetCode() != v.GetNetCode() or z.GetIsRuleArea(): continue
          for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
              if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(v.GetPosition()): lays.add(l)
      if len(lays) <= 1: remove_via_and_stubs(v); ndang += 1
  report["dangling_vias_removed"] = ndang
  # D-30: remover micro-segmentos (< 0,02 mm) destravados criados por junções (viram track_dangling na DRC)
  nmicro = 0
  for t in tracks():
      if t.GetClass() == "PCB_TRACK" and t.GetLength() < FromMM(0.02):
          board.RemoveNative(t); nmicro += 1
  report["micro_segments_removed"] = nmicro
  pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
  pcbnew.SaveBoard(PCB, board)
  report["unrouted_final"] = board.GetConnectivity().GetUnconnectedCount(True)
  with open(REPORT, "w", encoding="utf-8") as f: json.dump(report, f, indent=1, ensure_ascii=False, default=str)
  if os.path.exists(DRC_TMP): os.remove(DRC_TMP)
  print("unrouted_final:", report["unrouted_final"], "| added:", len(added), "| warnings:", report["warnings"])
  return report

if not globals().get("AS_LIBRARY"):
    main()
