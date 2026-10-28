# -*- coding: utf-8 -*-
"""
STEP 5b - roteamento do HybridPanda (H725 em B.Cu).

Fases:
  N  netclasses no .kicad_pro (CAN_DIFF para BUS*_H/_L, USB para USB_D*/USB_R_D*)
  Z  estende a zona +3V3 (In1.Cu) para cobrir a área do U7
  C  trilhas críticas diretas (mesma camada, sem via): VCAP, HSE, SMPS, VDDA, desacoplamento B.Cu
  V  vias GND / +3V3 junto aos pads dos capacitores de suporte
  L  trava (lock) trilhas do baseline em BUS*_H/_L + tudo criado aqui
  X  exporta DSN -> Freerouting (Java 25) -> importa SES
  F  refill de zonas, salva, relatório hardware/reports/step5b_route.json

Uso:  python step5b_route.py [--no-freerouting]
Idempotente: parte de HybridPanda.kicad_pcb.step5a (criado na 1ª execução a partir do PCB atual).
"""
import json, os, shutil, subprocess, sys, time, re
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
PRO = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pro")
SNAP = os.path.join(os.path.dirname(PCB), "snapshots", "HybridPanda.kicad_pcb.step5a")
DSN = os.path.join(ROOT, "hardware/reports", "HybridPanda_step5b.dsn")
SES = os.path.join(ROOT, "hardware/reports", "HybridPanda_step5b.ses")
REPORT = os.path.join(ROOT, "hardware/reports", "step5b_route.json")
JAVA = r"C:\Program Files\Java\jdk-25.0.4.1\bin\java.exe"
FR_JAR = os.path.join(ROOT, "hardware/scripts", "tools", "freerouting", "freerouting-2.5.0.jar")
NO_FR = "--no-freerouting" in sys.argv
INNER_POWER = "--inner-power" in sys.argv   # proibir In1/In2 ao autorouter (baseline usa In1/In2 p/ sinais; default: permitido)
FR_PASSES = int(sys.argv[sys.argv.index("--passes") + 1]) if "--passes" in sys.argv else 60
NO_PRE = "--no-pre" in sys.argv   # saltar o pré-fix de potência (fase P)
PRE_ROUNDS = int(sys.argv[sys.argv.index("--pre-rounds") + 1]) if "--pre-rounds" in sys.argv else 2

report = {"phases": {}, "warnings": []}
W = report["warnings"].append

# ---------------------------------------------------------------- N: netclasses
with open(PRO, encoding="utf-8") as f:
    pro = json.load(f)
classes = pro["net_settings"]["classes"]
names = [c["name"] for c in classes]
default = next(c for c in classes if c["name"] == "Default")
if "CAN_DIFF" not in names:
    classes.append(dict(default))
if True:
    c = classes[-1] if classes[-1].get("name") == "CAN_DIFF" else next(c for c in classes if c["name"] == "CAN_DIFF")
    c.update({"name": "CAN_DIFF", "track_width": 0.25, "clearance": 0.1,
              "diff_pair_width": 0.25, "diff_pair_gap": 0.2, "diff_pair_via_gap": 0.25,
              "via_diameter": 0.7, "via_drill": 0.3, "priority": 0})
usb = next(c for c in classes if c["name"] == "USB")
# baseline tinha 0.05 mm (abaixo do min_track_width 0.1375) -> alinha com Default
if usb["track_width"] < 0.1375:
    report["phases"]["N_usb_fixed_from"] = usb["track_width"]
    usb["track_width"] = 0.2; usb["clearance"] = 0.1
usb["via_diameter"] = 0.7; usb["via_drill"] = 0.3
default["via_diameter"] = 0.7; default["via_drill"] = 0.3
rules = pro["board"]["design_settings"]["rules"]
rules["allow_blind_buried_vias"] = False; rules["allow_microvias"] = False
rules["min_through_hole_diameter"] = 0.3; rules["min_via_diameter"] = 0.4
pats = pro["net_settings"].setdefault("netclass_patterns", [])
have = {(p["netclass"], p["pattern"]) for p in pats}
for pat in ("BUS0_H", "BUS0_L", "BUS1N_H", "BUS1N_L", "BUS1O_H", "BUS1O_L", "BUS2_H", "BUS2_L"):
    if ("CAN_DIFF", pat) not in have: pats.append({"netclass": "CAN_DIFF", "pattern": pat})
for pat in ("USB_D+", "USB_D-", "USB_R_D+", "USB_R_D-"):
    if ("USB", pat) not in have: pats.append({"netclass": "USB", "pattern": pat})
with open(PRO, "w", encoding="utf-8") as f:
    json.dump(pro, f, indent=2, ensure_ascii=False)
report["phases"]["N"] = {"classes": [c["name"] for c in classes], "patterns": len(pats)}

# ---------------------------------------------------------------- load (snapshot idempotente)
if not os.path.exists(SNAP):
    shutil.copy2(PCB, SNAP)
else:
    shutil.copy2(SNAP, PCB)
board = pcbnew.LoadBoard(PCB)
ds = board.GetDesignSettings()
ds.m_BlindBuriedViaAllowed = False; ds.m_MicroViasAllowed = False
ds.m_MinThroughDrill = FromMM(0.3); ds.m_ViasMinSize = FromMM(0.4)
fps = {f.GetReference(): f for f in board.GetFootprints()}
u7 = fps["U7"]
u7c = u7.GetPosition()
nets = board.GetNetsByName()
def net(n): return nets[n]

def mm(v): return VECTOR2I(FromMM(v[0]), FromMM(v[1]))
def pt(p): return (round(ToMM(p.x), 3), round(ToMM(p.y), 3))

# ---------------------------------------------------------------- Z: zona +3V3 In1 sob o MCU
z3 = [z for z in board.Zones() if z.GetNetname() == "+3V3" and z.IsOnLayer(pcbnew.In1_Cu)]
if z3:
    z = z3[0]
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    # faixa antiga (96.1-101 x 38.7-64.3) + bloco sob o U7 inteiro (fileira norte y=45.9 incluída);
    # x<=118.5 acima de y=47.6 para não disputar com a zona +5V In1 de prioridade 1 (x>=119, y 42.9-47.4);
    # a zona +5V In1 de prioridade 5 (108.9-122.9 x 45.0-46.7) prevalece sobre esta (prioridade 4)
    Z3_OUTLINE = [(96.1, 38.7), (118.5, 38.7), (118.5, 47.6), (130.0, 47.6), (130.0, 76.5), (96.1, 76.5)]  # leste até 130 (R30-R33 pull-ups STB em x 127-129 após o 5e, D-33)
    for v in Z3_OUTLINE:
        poly.Append(mm(v))
    z.SetOutline(poly)
    # mesma folga da zona GND (ver abaixo): com 0,508 a via de costura C55.1 (122,49;53,57) ficava fora do
    # preenchimento In1 entre a via BUS2_TX do Freerouting e uma trilha In1 vizinha.
    z.SetLocalClearance(FromMM(0.254))
    report["phases"]["Z"] = {"+3V3_In1_outline": Z3_OUTLINE, "+3V3_In1_clearance": 0.254}
else:
    W("zona +3V3 In1 não encontrada")
# zona GND (F/In2/B) do baseline: clearance 0,508 + espessura mín. 0,25 isolavam vias de costura entre vizinhos
# (ex.: via U7.128 em 122,36;57,10 ficou fora do preenchimento In2). 0,254 mm = 10 mil, bem acima do mín. 0,1 (D-28).
GND_ZONE_CLR = 0.254
zg = []
for z in board.Zones():
    if z.GetNetname() == "GND" and not z.GetIsRuleArea() and ToMM(z.GetLocalClearance()) > GND_ZONE_CLR:
        zg.append((pt(z.GetBoundingBox().GetPosition()), ToMM(z.GetLocalClearance()))); z.SetLocalClearance(FromMM(GND_ZONE_CLR))
report["phases"]["Z"]["gnd_zone_clearance"] = {"new": GND_ZONE_CLR, "changed": zg}

# ---------------------------------------------------------------- limpeza: fragmentos do baseline sem via/pad (sobras do STEP 5a)
def _touch(pt, layer, it, me):
    # tolerância 0,01 mm: pontas de trilhas e vias importadas do SES não coincidem ao nm
    near = lambda a, b: abs(a.x - b.x) <= 10000 and abs(a.y - b.y) <= 10000
    if it.m_Uuid.AsString() == me.m_Uuid.AsString(): return False
    if it.GetClass() == "PCB_VIA": return near(it.GetPosition(), pt)
    if it.GetClass() in ("PCB_TRACK", "PCB_ARC"): return it.GetLayer() == layer and (near(it.GetStart(), pt) or near(it.GetEnd(), pt))
    if it.GetClass() == "ZONE":  # ponta dentro do cobre vertido da mesma net (stub pad -> zona do baseline)
        return it.IsOnLayer(layer) and it.GetFilledPolysList(layer).Contains(pt)
    return it.IsOnLayer(layer) and it.HitTest(pt)
frag_removed = 0
_seen = set()
for t in list(board.GetTracks()):
    if t.IsLocked(): continue
    # vias empilhadas do baseline em (109,0; 53,9) diferem por < 0,05 mm -> chave arredondada a 0,05 mm
    q = lambda v: (int(round(v.x / 50000.0)), int(round(v.y / 50000.0)))
    key = (t.GetNetCode(), t.GetLayer(), t.GetClass()) + tuple(sorted([q(t.GetStart()), q(t.GetEnd())])) if t.GetClass() != "PCB_VIA" else (t.GetNetCode(), "V") + q(t.GetPosition())
    if key in _seen: board.RemoveNative(t); frag_removed += 1
    else: _seen.add(key)
report["phases"]["cleanup_duplicates_removed"] = frag_removed
def _via_layers(t, trk_by_net, pads_by_net, zones_by_net):
    """camadas em que a via toca trilha/pad/preenchimento da mesma net (via_dangling = < 2)."""
    pos = t.GetPosition(); lays = set()
    for i in trk_by_net.get(t.GetNetCode(), []):
        if i.GetClass() != "PCB_VIA" and _touch(pos, i.GetLayer(), i, t): lays.add(i.GetLayer())
    for p in pads_by_net.get(t.GetNetCode(), []):
        if p.HitTest(pos):
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(l): lays.add(l)
    for z in zones_by_net.get(t.GetNetCode(), []):
        for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(pos): lays.add(l)
    return lays
def cleanup_fragments(check_via_layers=False):
    removed = 0
    for _ in range(30):
        dirty = False
        pads_by_net = {}
        for f in board.GetFootprints():
            for p in f.Pads(): pads_by_net.setdefault(p.GetNetCode(), []).append(p)
        trk_by_net = {}
        for t in board.GetTracks(): trk_by_net.setdefault(t.GetNetCode(), []).append(t)
        zones_by_net = {}
        for z in board.Zones():
            if not z.GetIsRuleArea(): zones_by_net.setdefault(z.GetNetCode(), []).append(z)
        for t in list(board.GetTracks()):
            if t.IsLocked() or t.GetClass() == "PCB_VIA" or re.match(r"BUS\w+_[HL]$", t.GetNetname()): continue
            items = trk_by_net.get(t.GetNetCode(), []) + pads_by_net.get(t.GetNetCode(), []) + zones_by_net.get(t.GetNetCode(), [])
            if not (any(_touch(t.GetStart(), t.GetLayer(), i, t) for i in items) and any(_touch(t.GetEnd(), t.GetLayer(), i, t) for i in items)):
                board.RemoveNative(t); removed += 1; dirty = True
        for t in list(board.GetTracks()):
            if t.IsLocked() or t.GetClass() != "PCB_VIA": continue
            items = [i for i in trk_by_net.get(t.GetNetCode(), []) if i.GetClass() != "PCB_VIA"]
            att = sum(1 for i in items if _touch(t.GetPosition(), i.GetLayer(), i, t))
            if att == 0 and not any(p.HitTest(t.GetPosition()) for p in pads_by_net.get(t.GetNetCode(), [])):
                board.RemoveNative(t); removed += 1; dirty = True
            elif check_via_layers and len(_via_layers(t, trk_by_net, pads_by_net, zones_by_net)) < 2:
                board.RemoveNative(t); removed += 1; dirty = True
        if not dirty: break
    return removed
report["phases"]["cleanup_fragments_removed"] = cleanup_fragments()

# ---------------------------------------------------------------- helpers de colisão
all_pads = [p for f in board.GetFootprints() for p in f.Pads()]
base_tracks = list(board.GetTracks())

def seg_collides(a, b, width, layer, netcode, clearance=0.12):
    shp = pcbnew.SHAPE_SEGMENT(a, b, FromMM(width))
    for z in KEEPOUTS:
        # keepout só vale na própria camada (os do SW1 são F.Cu-only)
        if z.GetDoNotAllowTracks() and z.IsOnLayer(layer) and z.Outline().Collide(shp, FromMM(0.1)): return "keepout"
    for p in all_pads:
        if p.GetNetCode() == netcode or not p.IsOnLayer(layer): continue
        if p.GetEffectiveShape(layer).Collide(shp, FromMM(clearance)): return "pad %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
    for t in base_tracks + new_items:
        if t.GetNetCode() == netcode or not t.IsOnLayer(layer): continue
        if t.GetEffectiveShape(layer).Collide(shp, FromMM(clearance)): return "track %s" % t.GetNetname()
    return None

KEEPOUTS = [z for z in board.Zones() if z.GetIsRuleArea()] + [z for fp in board.GetFootprints() for z in fp.Zones() if z.GetIsRuleArea()]
HOLE_CLR = 0.25   # hole_clearance do projeto (design settings)
def via_collides(pos, dia, netcode, clearance=0.15, drill=0.3):
    shp =  pcbnew.SHAPE_CIRCLE(pos, FromMM(dia / 2)); hole = pcbnew.SHAPE_CIRCLE(pos, FromMM(drill / 2))
    for z in KEEPOUTS:
        if z.GetDoNotAllowVias() and z.Outline().Collide(shp, FromMM(clearance)): return "keepout"
    for p in all_pads:
        if p.GetNetCode() == netcode: continue
        for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(l) and (p.GetEffectiveShape(l).Collide(shp, FromMM(clearance)) or p.GetEffectiveShape(l).Collide(hole, FromMM(HOLE_CLR))): return "pad %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
    for t in base_tracks + new_items:
        if t.GetNetCode() == netcode: continue
        if t.GetClass() == "PCB_VIA" or True:
            for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if t.IsOnLayer(l) and t.GetEffectiveShape(l).Collide(shp, FromMM(clearance)): return "track %s" % t.GetNetname()
                # furo da via nova x cobre alheio: hole_clearance 0,25 (D-30). Collide() e estrito (<), igual ao DRC:
                # a via-in-pad do U1.2 fica a exatamente 0,250 mm da trilha USB_PWR e o DRC a aceita.
                if t.IsOnLayer(l) and t.GetEffectiveShape(l).Collide(hole, FromMM(HOLE_CLR)): return "hole x track %s" % t.GetNetname()
    return None

new_items = []
def add_track(a, b, width, layer, netcode):
    for t in new_items:  # dedupe
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() == layer and {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)} == {(a.x, a.y), (b.x, b.y)}:
            return t
    t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b); t.SetWidth(FromMM(width)); t.SetLayer(layer); t.SetNetCode(netcode); t.SetLocked(True)
    board.Add(t); new_items.append(t); return t
def add_via(pos, netcode, dia=0.7, drill=0.3):
    v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(netcode); v.SetLocked(True)
    board.Add(v); new_items.append(v); return v

def pad(ref, num):
    p = fps[ref].FindPadByNumber(str(num))
    if p is None: raise KeyError("%s.%s" % (ref, num))
    return p

# ---------------------------------------------------------------- C: trilhas críticas diretas
CRIT = [  # (cap ref, cap pad, U7 pin, width)
    ("C39", 1, 68, 0.3), ("C40", 1, 140, 0.3),            # VCAP
    ("Y1", 1, 25, 0.2), ("Y1", 3, 26, 0.2),               # HSE
    ("C23", 1, 25, 0.2), ("C24", 1, 26, 0.2),             # HSE load caps
    ("L5", 1, 15, 0.3), ("L5", 2, 17, 0.3), ("C41", 1, 15, 0.3), ("C42", 1, 17, 0.25),  # SMPS (C42.1 passa pelo pad L5.2, mesma net)
    ("C44", 1, 36, 0.2), ("C43", 1, 35, 0.2), ("FB1", 1, 36, 0.2),  # VDDA
    ("C38", 1, 27, 0.2),                                  # NRST
]
for r in range(45, 64):
    pass
dec_pins = {"C45": 7, "C46": 13, "C47": 19, "C48": 32, "C49": 42, "C50": 56, "C51": 71, "C52": 79, "C53": 92, "C54": 106,
            "C55": 119, "C56": 129, "C57": 144, "C58": 91, "C59": 90, "C60": 7, "C61": 56, "C62": 106, "C63": 8}
for ref, pin in dec_pins.items():
    CRIT.append((ref, 1, pin, 0.2))

routed, skipped = [], []
for ref, cp, pin, w in CRIT:
    if ref not in fps: skipped.append((ref, "ausente")); continue
    a_pad, b_pad = pad(ref, cp), pad("U7", pin)
    if a_pad.GetNetCode() != b_pad.GetNetCode():
        skipped.append((ref, "net diferente %s vs %s" % (a_pad.GetNetname(), b_pad.GetNetname()))); continue
    if not a_pad.IsOnLayer(pcbnew.B_Cu):
        skipped.append((ref, "em F.Cu -> Freerouting")); continue
    a, b = a_pad.GetPosition(), b_pad.GetPosition()
    nc = a_pad.GetNetCode()
    # tenta reto; senão L (dois segmentos, saindo do pino na direção do seu eixo)
    hit = seg_collides(a, b, w, pcbnew.B_Cu, nc)
    if hit is None:
        add_track(a, b, w, pcbnew.B_Cu, nc); routed.append((ref, pin, "reto", round(ToMM((a - b).EuclideanNorm()), 2)))
        continue
    ok = False
    for mid in (VECTOR2I(a.x, b.y), VECTOR2I(b.x, a.y)):
        if seg_collides(a, mid, w, pcbnew.B_Cu, nc) is None and seg_collides(mid, b, w, pcbnew.B_Cu, nc) is None:
            add_track(a, mid, w, pcbnew.B_Cu, nc); add_track(mid, b, w, pcbnew.B_Cu, nc)
            routed.append((ref, pin, "L", round(ToMM((a - mid).EuclideanNorm() + (mid - b).EuclideanNorm()), 2))); ok = True; break
    if not ok:
        # escape: sai do pino perpendicular à fileira (afastando do centro do U7), depois dobra até o pad
        import math
        d = VECTOR2I(b.x - u7c.x, b.y - u7c.y)
        ax = (1, 0) if abs(d.x) > abs(d.y) else (0, 1)
        sg = 1 if (d.x if ax[0] else d.y) > 0 else -1
        for e in (0.9, 1.2, 1.5, 1.9, 2.4, 3.0, 3.6):
            m1 = VECTOR2I(b.x + int(FromMM(e) * ax[0] * sg), b.y + int(FromMM(e) * ax[1] * sg))
            for m2 in (VECTOR2I(a.x, m1.y), VECTOR2I(m1.x, a.y)):
                segs = [(b, m1), (m1, m2), (m2, a)]
                if all(seg_collides(s, t, w, pcbnew.B_Cu, nc) is None for s, t in segs):
                    for s, t in segs:
                        if s != t: add_track(s, t, w, pcbnew.B_Cu, nc)
                    L = sum(ToMM((s - t).EuclideanNorm()) for s, t in segs)
                    routed.append((ref, pin, "escape%.1f" % e, round(L, 2))); ok = True; break
            if ok: break
    if not ok: skipped.append((ref, "colisão: %s" % hit))

# cristal: terminal diagonal (Y1.1) contorna o próprio pad GND pelo lado do C23, no corredor Y1.4 <-> C23.2
if ("Y1", "colisão: pad Y1.4") in skipped:
    a = pad("Y1", 1).GetPosition(); nc = pad("Y1", 1).GetNetCode()
    y1bb = fps["Y1"].GetBoundingBox(False, False); c23bb = fps["C23"].GetBoundingBox(False, False)
    xg = (max(y1bb.GetRight(), pad("Y1", 4).GetBoundingBox().GetRight()) + c23bb.GetLeft()) // 2
    hse = [t for t in new_items if t.GetNetCode() == nc and t.GetClass() == "PCB_TRACK" and t.GetStart().y == t.GetEnd().y]
    if hse:
        yj = hse[0].GetStart().y
        m1, m2 = VECTOR2I(xg, a.y), VECTOR2I(xg, yj)
        if all(seg_collides(s, t, 0.2, pcbnew.B_Cu, nc) is None for s, t in ((a, m1), (m1, m2))):
            add_track(a, m1, 0.2, pcbnew.B_Cu, nc); add_track(m1, m2, 0.2, pcbnew.B_Cu, nc)
            skipped.remove(("Y1", "colisão: pad Y1.4"))
            routed.append(("Y1", 25, "contorno x=%.2f" % ToMM(xg), round(ToMM((a - m1).EuclideanNorm() + (m1 - m2).EuclideanNorm()), 2)))
        else: W("Y1.1 contorno colide")
report["phases"]["C"] = {"routed": routed, "skipped_to_freerouting": skipped}

# ---------------------------------------------------------------- M: desvio +5V In1 (ex-M1 do 5c) + via-in-pad U1.2
# U1.2 (GND, SOT-23-6, F.Cu) ficou encurralado: a via GND do baseline (120.41, 53.18) caiu sob o pad U7.120 (B.Cu) e o
# único ponto de via (119.0, 53.42, via-in-pad 0.5) era bloqueado pelo tronco +5V In1 em x = 119.11 (1,0 mm). Desvia o
# tronco para x = 117.6: liberta a via do U1.2 e o ponto (118.5, 52.85) sob o corpo do U7 para a via +3V3 do pino 119
# (a via própria do 119 a leste caía no corredor U7.121-124 <-> U9, D-28, e a via do C55.1 fica fora do In1).
# Feito aqui (antes de V) e não no 5c para que a via do 119 já veja o tronco desviado.
def detour_5v_in1():
    v5 = net("+5V").GetNetCode(); gnd_ = net("GND").GetNetCode()
    def find(ends):
        return [t for t in base_tracks if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.In1_Cu and t.GetNetCode() == v5
                and {pt(t.GetStart()), pt(t.GetEnd())} in ends]
    seg = find(({(119.11, 51.23), (119.11, 53.96)},)); seg2 = find(({(118.54, 54.53), (119.11, 53.96)},))
    seg3 = find(({(119.11, 53.96), (121.58, 56.42)}, {(119.11, 53.96), (121.575, 56.425)}))
    p2 = pad("U1", 2) if "U1" in fps else None
    vpos = mm((119.0, 53.42))
    if not (seg and seg2 and seg3 and p2 is not None and p2.GetNetCode() == gnd_):
        return {"ok": False, "why": "geometria do baseline diferente"}
    w = ToMM(seg[0].GetWidth()); a = mm((119.11, 51.23)); k1 = mm((117.6, 52.74)); k2 = mm((117.6, 53.59)); j = mm((118.54, 54.53)); d1 = mm((119.6, 54.45))
    d2 = seg3[0].GetEnd() if ToMM((seg3[0].GetStart() - mm((119.11, 53.96))).EuclideanNorm()) < 0.05 else seg3[0].GetStart()
    old = [seg[0], seg2[0], seg3[0]]
    for t in old: board.RemoveNative(t); base_tracks.remove(t)
    segs = ((a, k1), (k1, k2), (k2, j), (j, d1), (d1, d2))
    bad = [seg_collides(s, e, w, pcbnew.In1_Cu, v5, 0.1) for s, e in segs]
    if any(bad):
        for t in old: board.Add(t); base_tracks.append(t)
        return {"ok": False, "why": bad}
    for s, e in segs: add_track(s, e, w, pcbnew.In1_Cu, v5)
    # D-33: via GND fora do pad U1.2 (centro do pad 119,45;53,425; bbox x 118,79-120,11). A oeste o corredor entre as
    # colunas do SOT-23-6 e ocupado pela trilha USB_PWR (x = 118,5) do pad 1; a leste ha a diagonal USB_PWR F.Cu
    # (120,245;54,375)->(126,92;50,7). Reencaminha essa diagonal por (121,9;54,375)->(123,0;52,858) (mesma reta a partir
    # dai) e poe a via em x ~121,4 (cobre a 0,25 mm dos pads B.Cu do U7, borda direita 120,9), ligada ao pad por toco F.Cu.
    # Ultimo recurso: via no centro do pad (via-in-pad, como antes).
    p2c = p2.GetPosition(); upw = net("USB_PWR").GetNetCode()
    diag = [t for t in base_tracks if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu and t.GetNetCode() == upw
            and {pt(t.GetStart()), pt(t.GetEnd())} == {(120.245, 54.375), (126.92, 50.7)}]
    if diag:
        dw = ToMM(diag[0].GetWidth()); board.RemoveNative(diag[0]); base_tracks.remove(diag[0])
        dsegs = ((mm((120.245, 54.375)), mm((121.9, 54.375))), (mm((121.9, 54.375)), mm((123.0, 52.858))), (mm((123.0, 52.858)), mm((126.92, 50.7))))
        dbad = [seg_collides(s, e, dw, pcbnew.F_Cu, upw, 0.1) for s, e in dsegs]
        if any(dbad):
            board.Add(diag[0]); base_tracks.append(diag[0]); diag = []
        else:
            dnew = [add_track(s, e, dw, pcbnew.F_Cu, upw) for s, e in dsegs]
            for cx, cy in ((121.4, 53.3), (121.35, 53.4), (121.45, 53.2), (121.4, 53.425)):
                c = mm((cx, cy))
                if via_collides(c, 0.5, gnd_, 0.1): continue
                if seg_collides(c, p2c, 0.3, pcbnew.F_Cu, gnd_, 0.1): continue
                add_via(c, gnd_, 0.5, 0.3); add_track(c, p2c, 0.3, pcbnew.F_Cu, gnd_)
                return {"ok": True, "x": 117.6, "u1_2_via": True, "u1_2_via_at": (cx, cy), "via_in_pad": False, "usb_pwr_rerouted": True}
            for t in dnew: board.RemoveNative(t); new_items.remove(t)
            board.Add(diag[0]); base_tracks.append(diag[0])
    hv = via_collides(vpos, 0.5, gnd_, 0.1)
    if hv:
        return {"ok": True, "x": 117.6, "u1_2_via": False, "why": hv}
    add_via(vpos, gnd_, 0.5, 0.3)
    return {"ok": True, "x": 117.6, "u1_2_via": True, "u1_2_via_at": (119.0, 53.42), "via_in_pad": True}
report["phases"]["M"] = detour_5v_in1()
if not report["phases"]["M"]["ok"]: W("M: desvio +5V In1 não aplicado: %s" % report["phases"]["M"]["why"])

# ---------------------------------------------------------------- R: pré-rotas travadas B.Cu->via->F.Cu (pares que o Freerouting falha repetidamente — D-30)
# Antes do FR a área ainda está livre: busca em grade a posição de via em que os dois segmentos
# (pino U7 em B.Cu -> via, via -> pad destino em F.Cu) ficam sem colisão. Travado para o FR respeitar.
PREROUTE = []  # (ref_a, pin_a, ref_b, pin_b, largura) — descobertos: todos os BUS*_TX/RX do U7 para o transceptor (U8–U11) da mesma rede
for _p in fps["U7"].Pads():
    _nn = _p.GetNetname()
    if not re.match(r"BUS\w+_(TX|RX)$", _nn): continue
    for _ref in ("U8", "U9", "U10", "U11"):
        if _ref not in fps: continue
        _q = next((q for q in fps[_ref].Pads() if q.GetNetname() == _nn), None)
        if _q is not None:
            PREROUTE.append((("U7", _p.GetNumber(), _ref, _q.GetNumber(), 0.15), (_p.GetPosition() - _q.GetPosition()).EuclideanNorm()))
PREROUTE = [x for x, _ in sorted(PREROUTE, key=lambda x: x[1])]  # mais curtos primeiro
def preroute_pair(ref_a, pin_a, ref_b, pin_b, w, via_dia=0.5, via_drill=0.3, step=0.1, rmax=2.0):
    pa, pb = pad(ref_a, pin_a), pad(ref_b, pin_b)
    if pa.GetNetCode() != pb.GetNetCode(): return {"ok": False, "why": "nets diferentes"}
    nc = pa.GetNetCode(); A, B = pa.GetPosition(), pb.GetPosition()
    la = pcbnew.B_Cu if pa.IsOnLayer(pcbnew.B_Cu) and not pa.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
    lb = pcbnew.F_Cu if pb.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    if la == lb:
        if seg_collides(A, B, w, la, nc) is None:
            add_track(A, B, w, la, nc); return {"ok": True, "via": None}
        return {"ok": False, "why": "mesma camada com colisão"}
    cx, cy = ToMM(B.x), ToMM(B.y)  # procurar perto do pad destino (SMD fino), expandindo em anéis
    cands = []
    n = int(rmax / step)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * step, cy + j * step
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 0.45 <= d <= rmax: cands.append((d, x, y))  # fora do pad (evita via-in-pad em pitch 0,65)
    cands.sort()
    tried = 0
    def path_ok(S, E, lay):
        """caminho direto ou com um cotovelo (horizontal/vertical primeiro, ou saída pelo eixo do pad); devolve lista de pontos ou None"""
        if seg_collides(S, E, w, lay, nc) is None: return [S, E]
        for M in (VECTOR2I(E.x, S.y), VECTOR2I(S.x, E.y)):
            if seg_collides(S, M, w, lay, nc) is None and seg_collides(M, E, w, lay, nc) is None: return [S, M, E]
        for ex in (0.8, 1.0, 1.2, 1.5, 1.8):  # saída horizontal pelo eixo do pad (LQFP lado direito/esquerdo)
            for sgn in (1, -1):
                M = VECTOR2I(S.x + FromMM(ex * sgn), S.y)
                if seg_collides(S, M, w, lay, nc) is None and seg_collides(M, E, w, lay, nc) is None: return [S, M, E]
        return None
    for d, x, y in cands:
        v = mm((x, y)); tried += 1
        if via_collides(v, via_dia, nc, 0.15): continue
        pb_path = path_ok(v, B, lb)
        if pb_path is None: continue
        pa_path = path_ok(A, v, la)
        if pa_path is None: continue
        add_via(v, nc, via_dia, via_drill)
        for s_, e_ in zip(pa_path, pa_path[1:]): add_track(s_, e_, w, la, nc)
        for s_, e_ in zip(pb_path, pb_path[1:]): add_track(s_, e_, w, lb, nc)
        return {"ok": True, "via": (round(x, 3), round(y, 3)), "tried": tried, "segs": len(pa_path) + len(pb_path) - 2}
    return {"ok": False, "why": "sem posição de via livre", "tried": tried}
report["phases"]["R"] = {}
for ra, pa_, rb, pb_, w in PREROUTE:
    key = "%s.%s<->%s.%s" % (ra, pa_, rb, pb_)
    try: report["phases"]["R"][key] = preroute_pair(ra, pa_, rb, pb_, w)
    except KeyError as e: report["phases"]["R"][key] = {"ok": False, "why": "pad ausente %s" % e}
    if not report["phases"]["R"][key]["ok"]: W("R: pré-rota %s falhou: %s" % (key, report["phases"]["R"][key]["why"]))

# ---------------------------------------------------------------- V: vias GND/+3V3 nos caps de suporte
def stitch_via(p, netname, label):
    """via a ~0.75 mm do pad, do lado oposto ao centro do U7; tenta 8 direções."""
    nc = net(netname).GetNetCode()
    if p.GetNetCode() != nc: return (label, "net %s != %s" % (p.GetNetname(), netname))
    c = p.GetPosition()
    lay = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
    # posições preferidas (deixam livre o corredor U7.121-124 <-> U9 em B.Cu, ver D-28)
    for xy in STITCH_PREF.get(label, []):
        pos = mm(xy)
        for dia in (0.7, 0.6):
            if via_collides(pos, dia, nc) or seg_collides(c, pos, 0.25, lay, nc, 0.1): continue
            if netname == "+3V3" and not _in_3v3_plane(pos): continue
            add_via(pos, nc, dia); add_track(c, pos, 0.25, lay, nc)
            return (label, "ok", pt(pos), "pref")
    d = VECTOR2I(c.x - u7c.x, c.y - u7c.y)
    import math
    ang0 = math.atan2(d.y, d.x)
    for k in (0, 1, -1, 2, -2, 3, -3, 4):
        ang = ang0 + k * math.pi / 4
        for dist in (0.75, 0.95, 1.2, 1.5, 1.9):
            pos = VECTOR2I(int(c.x + FromMM(dist) * math.cos(ang)), int(c.y + FromMM(dist) * math.sin(ang)))
            if via_collides(pos, 0.7, nc): continue
            if seg_collides(c, pos, 0.25, lay, nc, 0.1): continue
            # via +3V3 fora do contorno da zona In1 fica pendurada (via_dangling): C61.1 x=95,5 e C59.1 y=37,3
            if netname == "+3V3" and not _in_3v3_plane(pos): continue
            add_via(pos, nc); add_track(c, pos, 0.25, lay, nc)
            return (label, "ok", pt(pos))
    return (label, "sem espaço")
STITCH_PREF = {"C55.1": [(122.282, 52.1), (122.282, 52.0), (122.15, 52.1), (122.4, 52.05)]}

# vias GND de escape para os pinos GND do U7 (pitch 0.5 mm não permite spoke térmico da zona)
import math
U7_GND = [6, 12, 14, 18, 21, 22, 23, 24, 33, 34, 41, 55, 69, 80, 89, 104, 118, 128, 141]
gnd_nc = net("GND").GetNetCode(); u7v = []; U7_GND_REASONS = {}
# grupos de pinos GND consecutivos: uma ponte na ponta dos pads + uma via só
GND_GROUPS = {21: [21, 22, 23, 24], 22: None, 23: None, 24: None}
def _axis(c):
    d = VECTOR2I(c.x - u7c.x, c.y - u7c.y)
    ax = (1, 0) if abs(d.x) > abs(d.y) else (0, 1)
    return ax, (1 if (d.x if ax[0] else d.y) > 0 else -1)
def _off(c, ax, sg, along, lat):
    return VECTOR2I(c.x + int(FromMM(along) * ax[0] * sg + FromMM(lat) * -ax[1]), c.y + int(FromMM(along) * ax[1] * sg + FromMM(lat) * ax[0]))
def _in_3v3_plane(pos):
    return bool(z3) and z3[0].Outline().Contains(pos)
def _try_gnd(pin, group, ax, sg, knee_d, dists, tag, nc=None, reasons=None, plane=None):
    """tenta knee+via na direção sg (+1 = para fora do U7, -1 = por baixo do corpo, em B.Cu).
    nc/reasons/plane: net alvo (default GND), dict de motivos, teste 'via cai no plano' (default: sempre)."""
    gnd_nc = nc if nc is not None else globals()["gnd_nc"]
    U7_GND_REASONS = reasons if reasons is not None else globals()["U7_GND_REASONS"]
    knees = [_off(pad("U7", g).GetPosition(), ax, sg, knee_d, 0) for g in group]
    pre = [(pad("U7", g).GetPosition(), k) for g, k in zip(group, knees)]
    if len(group) > 1: pre.append((knees[0], knees[-1]))  # ponte entre as pontas
    hp = [seg_collides(s, t, 0.25, pcbnew.B_Cu, gnd_nc, 0.1) for s, t in pre]
    if any(hp):
        U7_GND_REASONS.setdefault(pin, {})["%s ponte" % tag] = [h for h in hp if h]; return None
    for dist in dists:
        for lat in (0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0):
            for k in knees:  # a via pode sair de qualquer pino do grupo
                pos = _off(k, ax, sg, dist - knee_d, lat)
                if plane is not None and not plane(pos): continue
                hv = via_collides(pos, 0.6, gnd_nc, 0.12) or seg_collides(k, pos, 0.25, pcbnew.B_Cu, gnd_nc, 0.1)
                if hv: U7_GND_REASONS.setdefault(pin, {}); U7_GND_REASONS[pin][hv] = U7_GND_REASONS[pin].get(hv, 0) + 1; continue
                for s, t in pre: add_track(s, t, 0.25, pcbnew.B_Cu, gnd_nc)
                add_via(pos, gnd_nc, 0.6, 0.3); add_track(k, pos, 0.25, pcbnew.B_Cu, gnd_nc)
                return (pin if len(group) == 1 else "+".join(map(str, group)), tag, dist, lat)
    return None
for i, pin in enumerate(U7_GND):
    if GND_GROUPS.get(pin, 0) is None: continue  # coberto pela ponte do grupo
    c = pad("U7", pin).GetPosition()
    ax, sg = _axis(c)
    group = GND_GROUPS.get(pin) or [pin]
    dists = (1.2, 1.5, 1.8, 2.2, 2.6, 3.0, 3.5) if i % 2 == 0 else (1.5, 1.2, 1.8, 2.2, 2.6, 3.0, 3.5)
    r = _try_gnd(pin, group, ax, sg, 0.9, dists, "fora")
    # fallback: via sob o corpo do LQFP (lado B.Cu, sem componentes), ponta interna dos pads em ~0.74 mm
    if r is None: r = _try_gnd(pin, group, ax, -sg, 0.9, (1.4, 1.7, 2.0, 2.4, 2.8), "dentro")
    if r is None: r = _try_gnd(pin, group, ax, -sg, 0.6, (1.4, 1.7, 2.0, 2.4, 2.8), "dentro-k0.6")
    u7v.append(r if r else (pin, "sem espaço"))
U7_GND_RESULT = u7v
# idem para os pinos +3V3 do U7 (via para o plano +3V3 em In1; pinos consecutivos partilham uma via)
U7_3V3 = [7, 8, 13, 16, 19, 32, 42, 56, 70, 71, 79, 90, 91, 92, 105, 106, 119, 129, 142, 143, 144]
V3_GROUPS = {7: [7, 8], 8: None, 70: [70, 71], 71: None, 90: [90, 91, 92], 91: None, 92: None, 142: [142, 143, 144], 143: None, 144: None}
v3_nc = net("+3V3").GetNetCode(); u7v3 = []; U7_3V3_REASONS = {}
for i, pin in enumerate(U7_3V3):
    if V3_GROUPS.get(pin, 0) is None: continue
    c = pad("U7", pin).GetPosition()
    ax, sg = _axis(c)
    group = V3_GROUPS.get(pin) or [pin]
    kw = dict(nc=v3_nc, reasons=U7_3V3_REASONS, plane=_in_3v3_plane)
    if pin == 119:
        # a via própria a leste caía no corredor U7.121-124 <-> U9 (D-28) e a via do C55.1 fica fora do In1 (USB_PWR F.Cu
        # + trilhas In1 do FR): via sob o corpo em (118.5, 52.85), possível só com o tronco +5V In1 desviado (fase M)
        r = _try_gnd(pin, [119], ax, -sg, 0.9, (1.66, 1.6, 1.75, 1.85), "dentro-119", **kw)
        u7v3.append(r if r else (119, "via C55.1")); continue
    r = _try_gnd(pin, group, ax, sg, 0.9, (1.2, 1.5, 1.8, 2.2, 2.6, 3.0, 3.5, 4.0, 4.5), "fora", **kw)
    if r is None: r = _try_gnd(pin, group, ax, -sg, 0.9, (1.4, 1.7, 2.0, 2.4, 2.8, 3.2), "dentro", **kw)
    if r is None: r = _try_gnd(pin, group, ax, -sg, 0.6, (1.4, 1.7, 2.0, 2.4, 2.8, 3.2), "dentro-k0.6", **kw)
    u7v3.append(r if r else (pin, "sem espaço"))
U7_3V3_RESULT = u7v3
vias = []
GND_PADS = [("C39", 2), ("C40", 2), ("C23", 2), ("C24", 2), ("Y1", 2), ("Y1", 4), ("C41", 2), ("C42", 2), ("C43", 2), ("C44", 2), ("C38", 2)]
GND_PADS += [(r, 2) for r in dec_pins]
for ref, n in GND_PADS:
    if ref in fps: vias.append(stitch_via(pad(ref, n), "GND", "%s.%s" % (ref, n)))
# +3V3: pad 1 dos desacoplamentos + FB1.2 (entrada do filtro VDDA) + VCAP não (é VCAP)
for ref in list(dec_pins) + ["FB1"]:
    if ref in fps:
        p = pad(ref, 2 if ref == "FB1" else 1)
        if p.GetNetname() == "+3V3": vias.append(stitch_via(p, "+3V3", "%s.%s" % (ref, p.GetNumber())))
report["phases"]["V"] = {"ok": sum(1 for v in vias if v[1] == "ok"), "detail": vias, "u7_gnd_vias": U7_GND_RESULT, "u7_gnd_fail_reasons": U7_GND_REASONS, "u7_3v3_vias": U7_3V3_RESULT, "u7_3v3_fail_reasons": U7_3V3_REASONS}


# ---------------------------------------------------------------- L: travar trilhas baseline CAN H/L (sem via, F.Cu)
can_locked = 0; can_vias = []
for t in base_tracks:
    nn = t.GetNetname()
    if re.match(r"BUS\w+_[HL]$", nn):
        t.SetLocked(True); can_locked += 1
        if t.GetClass() == "PCB_VIA": can_vias.append((nn, pt(t.GetPosition())))
# trava TODO o baseline antes do DSN: o export marca trilhas como "protect" mas vias destravadas como "route",
# e o Freerouting então realoca vias deixando trilhas protegidas sem transição de camada
base_unlocked = [t for t in base_tracks if not t.IsLocked()]
for t in base_unlocked: t.SetLocked(True)
report["phases"]["L"] = {"can_tracks_locked": can_locked, "can_vias_baseline": can_vias, "baseline_items_temp_locked": len(base_unlocked)}
if can_vias: W("LAYOUT_CONFLICT candidato: vias em BUS*_H/_L herdadas do baseline (protocolo 0x05: CAN só F.Cu)")

pcbnew.SaveBoard(PCB, board)

# ---------------------------------------------------------------- P: pré-fix de potência (step5c em modo --pre)
# Pads GND/+3V3/+5V que ficaram sem ligação ao plano depois do 5a (ex.: via do baseline removida por colidir com
# pad do U7) recebem via/stub ANTES do Freerouting, travados, para o autorouter os respeitar (ver D-26).
if not NO_PRE:
    g = {"PRELOADED_BOARD": board, "AS_LIBRARY": True, "__file__": os.path.join(ROOT, "hardware/scripts", "step5c_fix_unrouted.py"), "__name__": "step5c_pre"}
    with open(g["__file__"], encoding="utf-8") as f: exec(compile(f.read(), g["__file__"], "exec"), g)
    pre = g["main"](rounds=PRE_ROUNDS, power_only=True, lock=True)
    report["phases"]["P"] = {"rounds": [(r["round"], r["unconnected"], len(r["fixes"]), r["unfixed"]) for r in pre["rounds"]], "added": len(pre["added"]), "warnings": pre["warnings"]}
    alive = {t.m_Uuid.AsString() for t in board.GetTracks()}
    base_tracks = [t for t in base_tracks if t.m_Uuid.AsString() in alive]
    base_unlocked = [t for t in base_unlocked if t.m_Uuid.AsString() in alive]
    pcbnew.SaveBoard(PCB, board)

# ---------------------------------------------------------------- X: Freerouting
def count_unrouted(b):
    b.BuildConnectivity(); return b.GetConnectivity().GetUnconnectedCount(True)
report["phases"]["X"] = {"unrouted_before": count_unrouted(board)}
if not NO_FR:
    # DSN de uma cópia sem zonas de potência (Freerouting trataria +3V3/+5V como plano e omitiria vias);
    # exportado em subprocesso porque LoadBoard só funciona uma vez por processo.
    helper = r'''
import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
for z in list(b.Zones()):
    if not z.GetIsRuleArea() and z.GetNetname() != "GND": b.RemoveNative(z)
print("DSN", pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
'''
    hp = os.path.join(ROOT, "hardware/reports", "_dsn_export_helper.py")
    with open(hp, "w", encoding="utf-8") as f: f.write(helper)
    r0 = subprocess.run([sys.executable, hp, PCB, DSN], capture_output=True, text=True, timeout=600)
    os.remove(hp)
    report["phases"]["X"]["dsn_exported"] = "DSN True" in r0.stdout
    with open(DSN, encoding="utf-8") as f: dsn = f.read()
    dsn2 = re.sub(r'(\(via(?: "Via\[0-3\]_\d+:\d+_um")+\))', lambda m: m.group(1).replace(' "Via[0-3]_450:250_um"', ''), dsn, count=1)
    report["phases"]["X"]["dsn_small_via_removed"] = dsn2 != dsn
    # camadas internas = planos (+3V3 em In1, GND em In2): só o baseline pode tê-las; o autorouter não
    dsn3 = re.sub(r'\(layer (In[12]\.Cu)(\s*)\(type signal\)', r'(layer \1\2(type power)', dsn2) if INNER_POWER else dsn2
    report["phases"]["X"]["dsn_inner_layers_power"] = len(re.findall(r'\(type power\)', dsn3))
    # hole_clearance 0,25 do KiCad nao existe no DSN: via 0,5/0,3 + clearance 0,10 = 0,35 do centro, mas o furo exige
    # 0,15 + 0,25 = 0,40. Regra via<->(wire|smd|pin) = 0,16 faz o Freerouting respeitar isso (senao o 5c arranca
    # as vias do FR por hole_clearance e desfaz rotas inteiras). Freerouting: Structure.setClearanceRule aceita
    # pares <classe>_<classe> com classes wire/via/smd/pin/area. via_via idem: via 0,7 travada + via 0,5 do FR com
    # clearance 0,10 = 0,70 do centro, mas o furo exige 0,35 + 0,15 + 0,25 = 0,75 (3 pares hole_clearance via<->via no 5c).
    # NÃO usar wire_pin 160: o baseline já tem trilhas a 0,10 de pinos PTH -> 159 violações fixas e o FR trava em 28 não roteados (corrida 26-10 10:06).
    VIA_CLR = "(clearance 160 (type via_wire))(clearance 160 (type via_smd))(clearance 160 (type via_pin))(clearance 160 (type via_via))"
    dsn4, nsub = re.subn(r'(\(clearance \d+(?:\.\d+)? \(type smd_smd\)\))', r'\1' + VIA_CLR, dsn3, count=1)
    report["phases"]["X"]["dsn_via_clearance_rule"] = nsub == 1
    # a classe Default usa via 0,7 no KiCad; com a regra acima o FR teria raio efectivo 0,51 em vez dos 0,40 que o
    # furo exige -> via 0,5/0,3 para a classe Default (CAN_DIFF/USB mantêm 0,7; estão travadas)
    i0 = dsn4.find("(class kicad_default")
    i1 = dsn4.find('(use_via "Via[0-3]_700:300_um")', i0)
    if i0 >= 0 and i1 >= 0:
        dsn4 = dsn4[:i1] + '(use_via "Via[0-3]_500:300_um")' + dsn4[i1 + len('(use_via "Via[0-3]_700:300_um")'):]
    report["phases"]["X"]["dsn_default_via_500"] = i0 >= 0 and i1 >= 0
    dsn2 = dsn4
    with open(DSN, "w", encoding="utf-8") as f: f.write(dsn2)
    cmd = [JAVA, "-jar", FR_JAR, "-l", "en", "--gui.enabled=false", "-de", DSN, "-do", SES,
           "--router.autorouter.max_passes=%d" % FR_PASSES, "--router.plane_nets=GND", "--router.via_costs=80", "--router.automatic_neckdown=false", "--router.result_json=" + os.path.join(ROOT, "hardware/reports", "step5b_fr_result.json")]
    t0 = time.time()
    if os.path.exists(SES): os.remove(SES)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=os.path.dirname(DSN))
    report["phases"]["X"]["freerouting_rc"] = r.returncode
    report["phases"]["X"]["freerouting_s"] = round(time.time() - t0, 1)
    log = (r.stdout + r.stderr)
    with open(os.path.join(ROOT, "hardware/reports", "step5b_freerouting.log"), "w", encoding="utf-8") as f: f.write(log)
    report["phases"]["X"]["freerouting_tail"] = log.strip().splitlines()[-8:]
    if os.path.exists(SES):
        ok = pcbnew.ImportSpecctraSES(board, SES)
        report["phases"]["X"]["ses_imported"] = bool(ok)
    else:
        W("Freerouting não gerou SES")

# destrava o baseline (mantém travados só os itens críticos criados aqui e CAN H/L)
for t in base_unlocked:
    if not re.match(r"BUS\w+_[HL]$", t.GetNetname()): t.SetLocked(False)

# o Freerouting afunila (neck-down) junto a pads 0402 mesmo com automatic_neckdown=false (ex.: LED_GREEN 0,10,
# BLUE- 0,12) -> track_width < min_track_width 0,1375. Alarga para a maior largura sem colisão (0,1 de folga).
MIN_TW = 0.1375
def widen_thin_tracks():
    allt = list(board.GetTracks()); out = []
    for t in allt:
        if t.GetClass() != "PCB_TRACK" or t.IsLocked() or ToMM(t.GetWidth()) >= MIN_TW: continue
        lay = t.GetLayer(); nc = t.GetNetCode(); done = None
        for w in (0.2, 0.16, 0.14):
            shp = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), FromMM(w)); hit = False
            for p in all_pads:
                if p.GetNetCode() != nc and p.IsOnLayer(lay) and p.GetEffectiveShape(lay).Collide(shp, FromMM(0.1)): hit = True; break
            if not hit:
                for o in allt:
                    if o.GetNetCode() != nc and o.IsOnLayer(lay) and o.GetEffectiveShape(lay).Collide(shp, FromMM(0.1)): hit = True; break
            if not hit: t.SetWidth(FromMM(w)); done = w; break
        out.append((t.GetNetname(), pt(t.GetStart()), done))
        if done is None: W("trilha fina do FR sem largura válida: %s %s" % (t.GetNetname(), pt(t.GetStart())))
    return out
report["phases"].setdefault("X", {})["thin_tracks_widened"] = widen_thin_tracks()

# ---------------------------------------------------------------- F: refill + limpeza final + salvar
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
# sobras do baseline que só eram válidas com o pour antigo (via +3V3 (109,0; 53,9) sob o U7 ligada só em F.Cu;
# stub GND F.Cu (104,125; 51,4) cuja ponta deixou de cair no preenchimento) -> via_dangling / track_dangling
report["phases"]["F"] = {"cleanup_final_removed": cleanup_fragments(check_via_layers=True)}
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
report["phases"]["F"].update({"unrouted_after": count_unrouted(board),
                         "tracks": sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"),
                         "vias": sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")})
pcbnew.SaveBoard(PCB, board)
with open(REPORT, "w", encoding="utf-8") as f: json.dump(report, f, indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in report["phases"].items() if k != "V"}, ensure_ascii=False, default=str, indent=1))
print("V ok:", report["phases"]["V"]["ok"], "/", len(vias), [v for v in vias if v[1] != "ok"])
print("warnings:", report["warnings"])
