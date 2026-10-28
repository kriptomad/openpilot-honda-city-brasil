import os,sys,pcbnew
from pcbnew import FromMM
HERE=os.path.dirname(os.path.abspath(__file__)); PCB=os.path.join(os.path.dirname(HERE),"04_PROJECT","HybridPanda","HybridPanda.kicad_pcb")
b=pcbnew.LoadBoard(PCB); u=b.FindFootprintByReference("U13"); pads={p.GetNumber():p for p in u.Pads()}
for a,c in (("1","6"),("3","4")):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pads[a].GetPosition()); t.SetEnd(pads[c].GetPosition()); t.SetWidth(FromMM(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pads[a].GetNet()); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity(); pcbnew.SaveBoard(PCB,b); print("ok"); sys.stdout.flush(); os._exit(0)
