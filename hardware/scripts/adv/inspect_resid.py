"""Inspect the right-edge / hole-clearance residuals (read-only)."""
import pcbnew, math
from pcbnew import ToMM
b = pcbnew.LoadBoard(r"hardware\hybrid-panda\HybridPanda.kicad_pcb")
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
# board outline right edge
bb = b.GetBoardEdgesBoundingBox(); print("edge bbox", ToMM(bb.GetLeft()), ToMM(bb.GetRight()), ToMM(bb.GetTop()), ToMM(bb.GetBottom()))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_SHAPE" and b.GetLayerName(d.GetLayer()) == "Edge.Cuts":
        print("edge shape", d.ShowShape(), "width", ToMM(d.GetWidth()), "bbox right", ToMM(d.GetBoundingBox().GetRight()))
print("--- tracks with x > 141.0")
for t in tracks:
    s, e = t.GetStart(), t.GetEnd()
    if max(s.x, e.x) > pcbnew.FromMM(141.0):
        print(t.GetNetname(), b.GetLayerName(t.GetLayer()), (round(ToMM(s.x),4), round(ToMM(s.y),4)), (round(ToMM(e.x),4), round(ToMM(e.y),4)), "w", ToMM(t.GetWidth()))
print("--- vias with x > 140.5")
for v in vias:
    p = v.GetPosition()
    if p.x > pcbnew.FromMM(140.5): print(v.GetNetname(), round(ToMM(p.x),3), round(ToMM(p.y),3), "dia", ToMM(v.GetWidth(pcbnew.F_Cu)))
c28 = b.FindFootprintByReference("C28")
print("C28", ToMM(c28.GetPosition().x), ToMM(c28.GetPosition().y), c28.GetOrientationDegrees(), c28.GetFPID().GetLibItemName())
for p in c28.Pads():
    print("  pad", p.GetNumber(), p.GetNetname(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetSize(pcbnew.F_Cu).x), ToMM(p.GetSize(pcbnew.F_Cu).y))
    for t in tracks:
        if t.GetStart() == p.GetPosition() or t.GetEnd() == p.GetPosition(): print("     track end", t.GetNetname(), b.GetLayerName(t.GetLayer()))
# GND via near VCAP track
for v in vias:
    p = v.GetPosition()
    if abs(ToMM(p.x) - 109.15) < 0.01 and abs(ToMM(p.y) - 71.04) < 0.01:
        print("via", v.GetNetname(), ToMM(p.x), ToMM(p.y), "drill", ToMM(v.GetDrillValue()))
        att = [t for t in tracks if t.GetStart() == p or t.GetEnd() == p]; print("  attached", [(t.GetNetname(), b.GetLayerName(t.GetLayer())) for t in att])
for t in tracks:
    if t.GetNetname() == "VCAP" and b.GetLayerName(t.GetLayer()) == "B.Cu" and abs(ToMM(t.GetLength()) - 5.5509) < 0.01:
        s, e = t.GetStart(), t.GetEnd(); print("VCAP track", (ToMM(s.x), ToMM(s.y)), (ToMM(e.x), ToMM(e.y)), "w", ToMM(t.GetWidth()))
