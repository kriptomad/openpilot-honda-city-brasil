import pcbnew, re
from pcbnew import ToMM, VECTOR2I, FromMM
b = pcbnew.LoadBoard(r"hardware\hybrid-panda\HybridPanda.kicad_pcb")
zones = [z for z in b.Zones()]
print("zones:", [(z.GetNetname(), z.GetZoneName(), [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], z.IsFilled(), z.GetIsRuleArea(), round(ToMM(z.GetFilledArea()) if hasattr(z,'GetFilledArea') else 0,1)) for z in zones])
def copper_at(layer, pt):
    lid = b.GetLayerID(layer)
    for z in zones:
        if z.GetIsRuleArea() or not z.GetLayerSet().Contains(lid): continue
        if z.GetFilledPolysList(lid).Contains(pt): return z.GetNetname()
    return None
want = re.compile(r"^(USB_D[PN]|USB_D[+-]|D[+-]|BUS\d\w*_[HL]|BUS\d\w*_(TX|RX)|VLXSMPS|VCAP)$")
import collections
stat = collections.defaultdict(lambda: collections.Counter())
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK": continue
    n = t.GetNetname()
    if not want.match(n): continue
    layer = b.GetLayerName(t.GetLayer())
    ref = {"F.Cu": "In1.Cu", "B.Cu": "In2.Cu"}.get(layer)
    if not ref: stat[(n, layer)]["inner-track"] += 1; continue
    s, e = t.GetStart(), t.GetEnd()
    for k in range(5):
        pt = VECTOR2I(int(s.x + (e.x - s.x) * k / 4), int(s.y + (e.y - s.y) * k / 4))
        stat[(n, layer)][str(copper_at(ref, pt))] += 1
for k in sorted(stat): print(k, dict(stat[k]))
# inner layer nets present
inner = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and b.GetLayerName(t.GetLayer()) in ("In1.Cu", "In2.Cu"):
        inner[(b.GetLayerName(t.GetLayer()), t.GetNetname())] += 1
print("inner tracks:", dict(inner))
# HSE: Y1 pads to U7 pins 25/26 distance
u7 = b.FindFootprintByReference("U7"); y1 = b.FindFootprintByReference("Y1")
for pn in ("25", "26"):
    p = u7.FindPadByNumber(pn); print("U7", pn, p.GetNetname(), round(ToMM(p.GetPosition().x),2), round(ToMM(p.GetPosition().y),2))
for p in y1.Pads(): print("Y1", p.GetNumber(), p.GetNetname(), round(ToMM(p.GetPosition().x),2), round(ToMM(p.GetPosition().y),2), b.GetLayerName(y1.GetLayer()))
for ref in ("C23","C24","L5","C41","C42","C39","C40","C64"):
    f = b.FindFootprintByReference(ref); print(ref, f.GetValue(), round(ToMM(f.GetPosition().x),2), round(ToMM(f.GetPosition().y),2), b.GetLayerName(f.GetLayer()))
# track length per net for HSE
L = collections.Counter()
for t in b.GetTracks():
    if t.GetClass()=="PCB_TRACK" and t.GetNetname() in ("HSE_IN","HSE_OUT","OSC_IN","OSC_OUT") or (t.GetClass()=="PCB_TRACK" and "OSC" in t.GetNetname().upper()):
        L[t.GetNetname()] += ToMM(t.GetLength())
print("HSE track lengths:", dict(L))
