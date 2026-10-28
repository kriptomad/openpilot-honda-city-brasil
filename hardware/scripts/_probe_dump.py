import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import ToMM
PCB = str(hp.OUTPUT_ROOT / "hardware/hybrid-panda/HybridPanda.kicad_pcb")
x0, y0, x1, y1 = [float(v) for v in sys.argv[1:5]]
layer_name = sys.argv[5] if len(sys.argv) > 5 else "B.Cu"
board = pcbnew.LoadBoard(PCB)
layer = board.GetLayerID(layer_name)
def inside(v): return x0 <= ToMM(v.x) <= x1 and y0 <= ToMM(v.y) <= y1
for fp in board.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnLayer(layer) or not inside(p.GetPosition()): continue
        print("PAD %s.%s net=%s pos=%.3f,%.3f size=%.2fx%.2f drill=%.2f fp=%s rot=%.0f %s" % (fp.GetReference(), p.GetNumber(), p.GetNetname(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetSize().x), ToMM(p.GetSize().y), ToMM(p.GetDrillSize().x), fp.GetFPID().GetLibItemName().wx_str(), fp.GetOrientationDegrees(), "B" if fp.IsFlipped() else "F"))
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        if inside(t.GetPosition()): print("VIA net=%s pos=%.3f,%.3f d=%.2f" % (t.GetNetname(), ToMM(t.GetPosition().x), ToMM(t.GetPosition().y), ToMM(t.GetWidth(layer))))
    elif t.GetLayer() == layer and (inside(t.GetStart()) or inside(t.GetEnd())):
        print("TRK net=%s %.3f,%.3f -> %.3f,%.3f w=%.2f %s" % (t.GetNetname(), ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y), ToMM(t.GetWidth()), "L" if t.IsLocked() else ""))
for fp in board.GetFootprints():
    if inside(fp.GetPosition()):
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd).BBox()
        print("FP %s %s side=%s pos=%.3f,%.3f rot=%.0f crtyd=%.2f,%.2f-%.2f,%.2f" % (fp.GetReference(), fp.GetFPID().GetLibItemName().wx_str(), "B" if fp.IsFlipped() else "F", ToMM(fp.GetPosition().x), ToMM(fp.GetPosition().y), fp.GetOrientationDegrees(), ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
