"""Dump pad positions (local coords) and silkscreen/fab graphics for polarity checks.
Read-only. Usage: python.exe polarity_dump.py <board.kicad_pcb> REF [REF ...]
"""
import sys
import pcbnew

sys.stdout.reconfigure(encoding="utf-8")
board = pcbnew.LoadBoard(sys.argv[1])
refs = set(sys.argv[2:])
mm = pcbnew.ToMM
for fp in board.GetFootprints():
    if fp.GetReference() not in refs:
        continue
    pos = fp.GetPosition()
    print(fp.GetReference(), fp.GetFPID().GetLibItemName(), "layer", board.GetLayerName(fp.GetLayer()),
          "rot", fp.GetOrientationDegrees())
    for p in fp.Pads():
        lp = p.GetPosition() - pos
        print("  pad", p.GetNumber(), p.GetNetname(), round(mm(lp.x), 3), round(mm(lp.y), 3))
    for g in fp.GraphicalItems():
        L = board.GetLayerName(g.GetLayer())
        if "Silk" not in L and "Fab" not in L:
            continue
        try:
            s = g.GetStart() - pos
            e = g.GetEnd() - pos
            print("  gfx", L, g.GetClass(), g.ShowShape() if hasattr(g, "ShowShape") else "",
                  round(mm(s.x), 2), round(mm(s.y), 2), round(mm(e.x), 2), round(mm(e.y), 2))
        except Exception as ex:
            print("  gfx", L, g.GetClass(), "err", ex)
