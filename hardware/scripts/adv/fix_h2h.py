"""Nudge vias so that different-net drilled holes are >= 0.5 mm edge-to-edge (JLCPCB rule).
Moves the via with fewer attached track ends away from the other hole along the centre line,
and moves the matching track endpoints with it. Writes the board in place (backup made by caller)."""
import pcbnew, math, sys
from pcbnew import ToMM, FromMM, VECTOR2I
PCB = r"hardware\hybrid-panda\HybridPanda.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
MIN = 0.5 + 0.02
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
holes = [(v, ToMM(v.GetPosition().x), ToMM(v.GetPosition().y), ToMM(v.GetDrillValue()), v.GetNetname()) for v in vias]
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            holes.append((p, ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), max(ToMM(p.GetDrillSizeX()), ToMM(p.GetDrillSizeY())), p.GetNetname()))

def attached(v):
    pos = v.GetPosition()
    return [(t, "s") for t in tracks if t.GetStart() == pos] + [(t, "e") for t in tracks if t.GetEnd() == pos]

moved = []
for i, (a, ax, ay, ad, an) in enumerate(holes):
    for (c, cx, cy, cd, cn) in holes[i + 1:]:
        if an == cn: continue
        gap = math.dist((ax, ay), (cx, cy)) - ad / 2 - cd / 2
        if gap >= 0.5 or gap > 0.6: continue
        if a.GetClass() != "PCB_VIA" and c.GetClass() != "PCB_VIA":
            print("skip pad-pad", an, cn, round(gap, 3)); continue
        # choose a via to move: the one with fewer attached track ends
        cand = [h for h in ((a, ax, ay), (c, cx, cy)) if h[0].GetClass() == "PCB_VIA"]
        cand.sort(key=lambda h: len(attached(h[0])))
        mv, mx, my = cand[0]
        ox, oy = (cx, cy) if mv is a else (ax, ay)
        d = MIN - gap
        ux, uy = (mx - ox), (my - oy); n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
        delta = VECTOR2I(FromMM(ux * d), FromMM(uy * d))
        att = attached(mv)
        newpos = mv.GetPosition() + delta
        for t, end in att:
            if end == "s": t.SetStart(newpos)
            else: t.SetEnd(newpos)
        mv.SetPosition(newpos)
        moved.append((mv.GetNetname(), round(mx, 3), round(my, 3), round(ToMM(newpos.x), 3), round(ToMM(newpos.y), 3), round(gap, 3), len(att)))
        # refresh coordinates for later comparisons
        for k, h in enumerate(holes):
            if h[0] is mv: holes[k] = (mv, ToMM(newpos.x), ToMM(newpos.y), h[3], h[4])
for m in moved: print("moved via", m)
if "--write" in sys.argv:
    b.Save(PCB); print("saved")
