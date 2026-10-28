"""Dump every track/via/pad of the given nets (all layers) to 06_REPORTS/corr/net_dump.txt.

Usage: python -u tools/net_dump.py NET [NET ...]
(stdout is redirected to the file; pcbnew asserts on PCB_VIA.GetWidth() without a layer, hence GetWidth(F_Cu))
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "06_REPORTS", "corr", "net_dump.txt")
sys.stdout = open(OUT, "w", encoding="utf-8")
import pcbnew  # noqa: E402

M = pcbnew.ToMM
b = pcbnew.LoadBoard(os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb"))
nets = set(sys.argv[1:])
for t in b.GetTracks():
    if t.GetNetname() not in nets:
        continue
    if t.GetClass() == "PCB_TRACK":
        s, e = t.GetStart(), t.GetEnd()
        print("TRK %s %s (%.4f,%.4f)-(%.4f,%.4f) w%.3f len%.2f" % (t.GetNetname(), t.GetLayerName(), M(s.x), M(s.y), M(e.x), M(e.y),
                                                                M(t.GetWidth()), M(t.GetLength())))
    else:
        p = t.GetPosition()
        print("VIA %s (%.4f,%.4f) d%.2f/%.2f" % (t.GetNetname(), M(p.x), M(p.y), M(t.GetWidth(pcbnew.F_Cu)), M(t.GetDrill())))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() in nets:
            pos = p.GetPosition(); sz = p.GetSize()
            print("PAD %s %s.%s (%.4f,%.4f) %.2fx%.2f %s rot%.0f" % (p.GetNetname(), fp.GetReference(), p.GetNumber(), M(pos.x), M(pos.y),
                                                                 M(sz.x), M(sz.y), fp.GetLayerName(), fp.GetOrientationDegrees()))
sys.stdout.close()
os._exit(0)
