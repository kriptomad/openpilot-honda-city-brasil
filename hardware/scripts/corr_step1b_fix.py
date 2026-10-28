"""corr_step1b_fix.py - correcoes locais apos corr_step1_footprints.py (regressoes do DRC).

  * Q1/Q2: courtyard 3.3x3.3 -> 3.1x3.5 (centros a 3.25 mm; pads ocupam 2.5 x 3.475)
  * L3: courtyard 8.9x7.6 -> 8.9x6.8 (D11 a 0.05 mm do corpo; so cabe o corpo)
  * R24: -0.35 mm em y (courtyard x Q2) + trilhas +3V3/SBU1 refeitas
  * relay_SBU1: via (125.322,71.358) ficava a 0.12 mm do pad 3 do Q1 e a trilha F.Cu cruzava o pad 2 (+5V):
    nova via (126.9,70.0) e trilha F.Cu entre Q1.2 e Q2.1 (x = 127.175)
  * LED_RED: trilha horizontal y 71.259 -> 71.40 (pad 1 do U5 desceu 0.1 mm)
  * R6: referencia (silk) 1.0 mm sobre os pads -> 0.8/0.12 mm acima do courtyard
  * refill das zonas
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
OUT = os.path.join(ROOT, "hardware/reports", "corrections", "step1b_fix.json")
board = pcbnew.LoadBoard(PCB)
log = []
P = lambda x, y: VECTOR2I(FromMM(x), FromMM(y))


def fp(ref):
    return board.FindFootprintByReference(ref)


def net(name):
    return board.GetNetInfo().GetNetItem(name)


def seg(name, layer, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net(name))
    board.Add(t); t.thisown = 0
    log.append("+trk %s %s %s->%s w%.2f" % (name, board.GetLayerName(layer), a, b, w))
    return t


def via(name, x, y, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y)); v.SetWidth(pcbnew.PADSTACK.ALL_LAYERS, FromMM(d)) if hasattr(pcbnew, "PADSTACK") else v.SetWidth(FromMM(d))
    v.SetDrill(FromMM(drill)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(name))
    board.Add(v); v.thisown = 0
    log.append("+via %s (%.3f,%.3f)" % (name, x, y))
    return v


def find_tracks(name, layer=None, pt=None, tol=0.02):
    out = []
    for t in board.GetTracks():
        if t.GetNetname() != name:
            continue
        if layer is not None and (t.GetClass() == "PCB_VIA" or t.GetLayer() != layer):
            continue
        if pt is not None:
            ok = False
            for q in (t.GetStart(), t.GetEnd()):
                if abs(ToMM(q.x) - pt[0]) < tol and abs(ToMM(q.y) - pt[1]) < tol:
                    ok = True
            if not ok:
                continue
        out.append(t)
    return out


_removed = []


def remove(t):
    log.append("-%s %s" % (t.GetClass(), t.GetNetname()))
    _removed.append(t)
    board.RemoveNative(t)


def set_courtyard(ref, w, h):
    f = fp(ref)
    layer = pcbnew.F_CrtYd if not f.IsFlipped() else pcbnew.B_CrtYd
    c = f.GetPosition()
    for g in list(f.GraphicalItems()):
        if g.GetLayer() == layer and g.GetShape() == pcbnew.SHAPE_T_RECT:
            g.SetStart(VECTOR2I(c.x - FromMM(w / 2), c.y - FromMM(h / 2)))
            g.SetEnd(VECTOR2I(c.x + FromMM(w / 2), c.y + FromMM(h / 2)))
            log.append("%s courtyard -> %.2fx%.2f" % (ref, w, h))
            return
    raise RuntimeError("courtyard rect nao encontrado em " + ref)


# 1. courtyards
set_courtyard("Q1", 3.1, 3.5)
set_courtyard("Q2", 3.1, 3.5)
set_courtyard("L3", 8.9, 6.8)

# 2. R24 -0.35 y
r24 = fp("R24")
for t in find_tracks("+3V3", pcbnew.F_Cu, (130.675, 68.340)):
    remove(t)
for t in find_tracks("SBU1", pcbnew.F_Cu, (130.675, 69.360)):
    remove(t)
for t in find_tracks("SBU1", pcbnew.F_Cu, (128.800, 69.360)):
    remove(t)
r24.SetPosition(P(130.675, 68.50))
log.append("R24 (130.675,68.85) -> (130.675,68.50)")
seg("+3V3", pcbnew.F_Cu, (130.675, 67.99), (131.303, 68.465), 0.25)
seg("SBU1", pcbnew.F_Cu, (130.675, 69.01), (130.325, 69.36), 0.2)
seg("SBU1", pcbnew.F_Cu, (130.325, 69.36), (128.8, 69.36), 0.2)
seg("SBU1", pcbnew.F_Cu, (128.8, 69.36), (128.8, 70.349), 0.2)
seg("SBU1", pcbnew.F_Cu, (128.8, 67.303), (128.8, 69.36), 0.2)

# 3. relay_SBU1
for t in find_tracks("relay_SBU1", pcbnew.F_Cu):
    remove(t)
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "relay_SBU1" and abs(ToMM(t.GetPosition().x) - 125.322) < 0.01:
        remove(t)
        break
for t in find_tracks("relay_SBU1", pcbnew.In1_Cu, (125.322, 71.358)):
    t.SetEnd(P(126.9, 70.0)) if abs(ToMM(t.GetEnd().x) - 125.322) < 0.01 else t.SetStart(P(126.9, 70.0))
    log.append("relay_SBU1 In1 extremidade -> (126.9,70.0)")
via("relay_SBU1", 126.9, 70.0)
seg("relay_SBU1", pcbnew.F_Cu, (126.9, 70.0), (127.175, 70.275), 0.2)
seg("relay_SBU1", pcbnew.F_Cu, (127.175, 70.275), (127.175, 72.35), 0.2)
seg("relay_SBU1", pcbnew.F_Cu, (127.175, 72.35), (127.85, 72.35), 0.2)

# 4. LED_RED
for t in find_tracks("LED_RED", pcbnew.F_Cu, (106.851, 71.259)):
    remove(t)
for t in find_tracks("LED_RED", pcbnew.F_Cu, (104.325, 71.259)):
    remove(t)
seg("LED_RED", pcbnew.F_Cu, (107.303, 70.808), (106.71, 71.40), 0.2)
seg("LED_RED", pcbnew.F_Cu, (106.71, 71.40), (104.325, 71.40), 0.2)
seg("LED_RED", pcbnew.F_Cu, (104.325, 71.40), (104.325, 69.409), 0.15)

# 5. R6 referencia
r = fp("R6").Reference()
r.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); r.SetTextThickness(FromMM(0.12))
r.SetPosition(P(105.81, 47.05))
log.append("R6 ref -> (105.81,47.05) 0.8/0.12")

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"log": log}, open(OUT, "w", encoding="utf-8"), indent=1)
print("\n".join(log))
