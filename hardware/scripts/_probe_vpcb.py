import sys, os, json, collections, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import ToMM
PCB = str(hp.OUTPUT_ROOT / "hardware/hybrid-panda/HybridPanda.kicad_pcb")
OUT = str(hp.OUTPUT_ROOT / "hardware/reports/verification-pcb/_drc_before.json")
subprocess.run([str(hp.KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", OUT, PCB], capture_output=True)
d = json.load(open(OUT, encoding="utf-8"))
c = collections.Counter(v["type"] for v in d["violations"])
print("DRC", dict(c), "unconnected", len(d["unconnected_items"]))
for v in d["violations"]:
    if v["type"] in ("hole_clearance", "silk_edge_clearance", "silk_over_copper", "silk_overlap"):
        print(v["type"], "|", v["description"][:90], "|", [(i["description"][:60], i["pos"]) for i in v["items"]])
th = [v for v in d["violations"] if v["type"] == "text_height"]
print("text_height sample:")
for v in th[:50]:
    print("  ", v["description"][:80], "|", [i["description"][:70] for i in v["items"]])
board = pcbnew.LoadBoard(PCB)
nets = board.GetNetsByName()
for n in ("USB_D+", "USB_D-", "USB_R_D+", "USB_R_D-"):
    nc = nets[n].GetNetCode()
    print("NET", n)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == nc:
                print("   pad", fp.GetReference(), p.GetNumber(), "%.3f,%.3f" % (ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)), board.GetLayerName(p.GetLayer()) if not p.IsOnLayer(pcbnew.F_Cu) or not p.IsOnLayer(pcbnew.B_Cu) else "TH", "size %.2fx%.2f" % (ToMM(p.GetSize().x), ToMM(p.GetSize().y)), "flipped" if fp.IsFlipped() else "", fp.GetFPID().GetLibItemName().wx_str(), "rot", fp.GetOrientationDegrees())
    for t in board.GetTracks():
        if t.GetNetCode() == nc:
            if t.GetClass() == "PCB_VIA":
                print("   via %.3f,%.3f" % (ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)), "d=%.2f" % ToMM(t.GetWidth()), "locked", t.IsLocked())
            else:
                print("   trk", board.GetLayerName(t.GetLayer()), "%.3f,%.3f -> %.3f,%.3f" % (ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y)), "w=%.3f" % ToMM(t.GetWidth()), "L=%.2f" % ToMM(t.GetLength()), "locked" if t.IsLocked() else "")
# zones per layer
for z in board.Zones():
    if z.GetIsRuleArea(): continue
    print("ZONE", z.GetNetname(), [board.GetLayerName(l) for l in z.GetLayerSet().Seq()], "prio", z.GetAssignedPriority(), "bbox %.1f,%.1f-%.1f,%.1f" % (ToMM(z.GetBoundingBox().GetLeft()), ToMM(z.GetBoundingBox().GetTop()), ToMM(z.GetBoundingBox().GetRight()), ToMM(z.GetBoundingBox().GetBottom())))
# P1 pads
p1 = board.FindFootprintByReference("P1")
print("P1", p1.GetFPID().GetLibItemName().wx_str(), "pos %.3f,%.3f" % (ToMM(p1.GetPosition().x), ToMM(p1.GetPosition().y)), "rot", p1.GetOrientationDegrees(), "flipped", p1.IsFlipped())
for p in p1.Pads():
    if p.GetDrillSize().x:
        print("   pad", p.GetNumber(), "attr", p.GetAttribute(), "pos %.3f,%.3f" % (ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)), "drill %.3fx%.3f" % (ToMM(p.GetDrillSize().x), ToMM(p.GetDrillSize().y)), "size %.3fx%.3f" % (ToMM(p.GetSize().x), ToMM(p.GetSize().y)), "shape", p.GetShape())
bb = board.GetBoardEdgesBoundingBox()
print("board bbox %.2f,%.2f -> %.2f,%.2f" % (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
