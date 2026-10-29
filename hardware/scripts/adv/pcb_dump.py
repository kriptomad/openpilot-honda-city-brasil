import pcbnew, json, sys
from collections import defaultdict
b = pcbnew.LoadBoard(r"C:\Users\costabr\Downloads\openpilot\openpilot-honda-city-brasil\hardware\hybrid-panda\HybridPanda.kicad_pcb")
mm = pcbnew.ToMM
out = {}
ds = b.GetDesignSettings()
print("board layers", b.GetCopperLayerCount(), "thickness", mm(ds.GetBoardThickness()))
print("min clearance", mm(ds.m_MinClearance), "min track", mm(ds.m_TrackMinWidth), "min via dia", mm(ds.m_ViasMinSize), "min through hole", mm(ds.m_MinThroughDrill), "hole-to-hole", mm(ds.m_HoleToHoleMin), "hole clearance", mm(ds.m_HoleClearance), "min annular", mm(ds.m_ViasMinAnnularWidth), "cu-edge", mm(ds.m_CopperEdgeClearance), "mask min web", mm(ds.m_SolderMaskMinWidth), "mask expansion", mm(ds.m_SolderMaskExpansion), "silk min", mm(ds.m_MinSilkTextHeight), mm(ds.m_MinSilkTextThickness))
bb = b.GetBoardEdgesBoundingBox()
print("edge bbox", mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetWidth()), mm(bb.GetHeight()))
# stackup
for i in range(b.GetCopperLayerCount()):
    pass
print("enabled layers:", [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()])
# footprints
print("\n== FOOTPRINTS ==")
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    pads = list(fp.Pads())
    ref = fp.GetReference()
    smd = sum(1 for p in pads if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD)
    th = sum(1 for p in pads if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH)
    npth = sum(1 for p in pads if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH)
    print(f"{ref} | {fp.GetValue()} | {fp.GetFPIDAsString()} | layer={b.GetLayerName(fp.GetLayer())} | pos=({mm(fp.GetPosition().x):.2f},{mm(fp.GetPosition().y):.2f}) rot={fp.GetOrientationDegrees()} | pads smd/pth/npth={smd}/{th}/{npth}")
    if ref in ("U7","U8","U6","U12","L5","P1","U3","SW1","Y1","Q1","Q4","U1","U13","D13","U5","J1","D5","D1","D12","D11","L3","L4","JP1","C23","C24","FB1"):
        for p in pads:
            sz = p.GetSize(); pos = p.GetPosition(); dr = p.GetDrillSize()
            shape = {pcbnew.PAD_SHAPE_RECT:'rect',pcbnew.PAD_SHAPE_ROUNDRECT:'rrect',pcbnew.PAD_SHAPE_OVAL:'oval',pcbnew.PAD_SHAPE_CIRCLE:'circ',pcbnew.PAD_SHAPE_CUSTOM:'custom',pcbnew.PAD_SHAPE_TRAPEZOID:'trap',pcbnew.PAD_SHAPE_CHAMFERED_RECT:'chrect'}.get(p.GetShape(), str(p.GetShape()))
            lay = [b.GetLayerName(l) for l in p.GetLayerSet().Seq() if l in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.F_Mask,pcbnew.B_Mask,pcbnew.F_Paste,pcbnew.B_Paste)]
            print(f"   pad {p.GetNumber():>4} net={p.GetNetname():<14} {shape:<6} size=({mm(sz.x):.3f},{mm(sz.y):.3f}) drill=({mm(dr.x):.2f},{mm(dr.y):.2f}) at=({mm(pos.x):.3f},{mm(pos.y):.3f}) layers={lay}")
# zones
print("\n== ZONES ==")
for z in b.Zones():
    print("zone", z.GetNetname(), [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], "filled", z.IsFilled(), "prio", z.GetAssignedPriority(), "area_mm2", round(z.GetFilledArea()/1e12,1) if hasattr(z,'GetFilledArea') else '?', "minw", mm(z.GetMinThickness()), "clr", mm(z.GetLocalClearance()) if hasattr(z,'GetLocalClearance') else '')
# tracks stats
print("\n== TRACKS ==")
widths = defaultdict(int); vias = defaultdict(int)
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        vias[(mm(t.GetWidth()), mm(t.GetDrillValue()))]+=1
    else:
        widths[(b.GetLayerName(t.GetLayer()), mm(t.GetWidth()))]+=1
print("track widths", dict(widths)); print("vias", dict(vias))
# text on copper
print("\n== TEXT ON COPPER / small silk ==")
for d in b.GetDrawings():
    if d.GetClass() in ("PCB_TEXT","PCB_TEXTBOX") and b.GetLayerName(d.GetLayer()).endswith(".Cu"):
        print("copper text:", d.GetText(), b.GetLayerName(d.GetLayer()))
for fp in b.GetFootprints():
    for it in [fp.Reference(), fp.Value()] + list(fp.GraphicalItems()):
        if it.GetClass()=="PCB_TEXT" or it.GetClass()=="PCB_FIELD":
            ln = b.GetLayerName(it.GetLayer())
            if ln.endswith(".Cu") and it.IsVisible():
                print("fp copper text", fp.GetReference(), it.GetText(), ln)
            if ln.endswith("SilkS") and it.IsVisible() and (mm(it.GetTextHeight())<0.8 or mm(it.GetTextThickness())<0.15):
                print("small silk", fp.GetReference(), repr(it.GetText()), mm(it.GetTextHeight()), mm(it.GetTextThickness()))
# edge cuts
print("\n== EDGE ==")
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.Edge_Cuts:
        print(d.GetClass(), d.GetShapeStr() if hasattr(d,'GetShapeStr') else '', mm(d.GetStart().x), mm(d.GetStart().y), mm(d.GetEnd().x), mm(d.GetEnd().y))
for fp in b.GetFootprints():
    for g in fp.GraphicalItems():
        if g.GetLayer()==pcbnew.Edge_Cuts:
            print("fp edge item", fp.GetReference(), g.GetClass())

