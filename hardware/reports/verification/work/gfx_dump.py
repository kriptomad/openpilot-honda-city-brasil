"""Read-only dump of footprint graphics (silk/fab/mask/paste) with bbox in local
coords, plus pads, for polarity / mask-opening checks.
Usage: kicad python.exe gfx_dump.py <board> REF [REF...]
"""
import sys
import pcbnew

sys.stdout.reconfigure(encoding="utf-8")
board = pcbnew.LoadBoard(sys.argv[1])
refs = set(sys.argv[2:])
mm = pcbnew.ToMM
for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
    if refs and fp.GetReference() not in refs:
        continue
    pos = fp.GetPosition()
    print("==", fp.GetReference(), fp.GetFPID().GetLibItemName(), "layer", board.GetLayerName(fp.GetLayer()),
          "rot", fp.GetOrientationDegrees(), "pos", round(mm(pos.x), 3), round(mm(pos.y), 3))
    for p in fp.Pads():
        lp = p.GetPosition() - pos
        print("  pad", p.GetNumber(), p.GetNetname(), "abs", round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3),
              "rel", round(mm(lp.x), 3), round(mm(lp.y), 3))
    for g in fp.GraphicalItems():
        L = board.GetLayerName(g.GetLayer())
        bb = g.GetBoundingBox()
        c = bb.GetCenter() - pos
        kind = g.GetClass()
        extra = ""
        if kind == "PCB_SHAPE":
            extra = g.ShowShape()
            try:
                extra += f" w={mm(g.GetWidth()):.2f} fill={g.IsFilled()}"
            except Exception:
                pass
        elif kind in ("PCB_TEXT", "PCB_FIELD"):
            extra = repr(g.GetText())[:30]
        print(f"  gfx {L:14s} {kind:10s} {extra:28s} bbox_center_rel=({mm(c.x):.2f},{mm(c.y):.2f}) size=({mm(bb.GetWidth()):.2f}x{mm(bb.GetHeight()):.2f})")
