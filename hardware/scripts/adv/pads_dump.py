import json, pcbnew
from pcbnew import ToMM
b = pcbnew.LoadBoard(r"hardware\hybrid-panda\HybridPanda.kicad_pcb")
out = {"pads": [], "vias": []}
for fp in b.GetFootprints():
    for p in fp.Pads():
        ls = p.GetLayerSet()
        layers = [l for l in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu") if ls.Contains(b.GetLayerID(l))]
        out["pads"].append({"ref": fp.GetReference(), "pad": p.GetNumber(), "net": p.GetNetname(),
                            "x": ToMM(p.GetPosition().x), "y": ToMM(p.GetPosition().y),
                            "layers": layers, "th": p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,),
                            "npth": p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
                            "drill": ToMM(p.GetDrillSizeX()) if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else 0})
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        out["vias"].append({"net": t.GetNetname(), "x": ToMM(t.GetPosition().x), "y": ToMM(t.GetPosition().y), "drill": ToMM(t.GetDrillValue())})
json.dump(out, open(r"hardware\reports\verification-pcb\adv\pads.json", "w"), indent=0)
print(len(out["pads"]), len(out["vias"]))
