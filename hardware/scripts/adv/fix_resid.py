"""Adversarial review follow-up: close the hole_clearance 0.254 and right-edge 0.3 residuals.
(1) GND via (109.15,71.04) moved 0.02 mm away from the VCAP track on B.Cu.
(2) 1.2 mm square rule areas (no copper pour, all Cu layers) around P1's two NPTH pegs.
(3) +12V meander right end x 142.1067 -> 142.08; C28 moved 0.04 mm left with its two track ends.
Run with --write to save."""
import pcbnew, math, sys
from pcbnew import ToMM, FromMM, VECTOR2I
PCB = r"hardware\hybrid-panda\HybridPanda.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]

def move_point(old, new):
    n = 0
    for t in tracks:
        if t.GetStart() == old: t.SetStart(new); n += 1
        if t.GetEnd() == old: t.SetEnd(new); n += 1
    return n

# (1) via vs VCAP track
via = next(v for v in vias if abs(ToMM(v.GetPosition().x) - 109.15) < 0.01 and abs(ToMM(v.GetPosition().y) - 71.0425) < 0.01)
trk = next(t for t in tracks if t.GetNetname() == "VCAP" and abs(ToMM(t.GetLength()) - 5.5509) < 0.01)
vx, vy = ToMM(via.GetPosition().x), ToMM(via.GetPosition().y)
sx, sy, ex, ey = ToMM(trk.GetStart().x), ToMM(trk.GetStart().y), ToMM(trk.GetEnd().x), ToMM(trk.GetEnd().y)
dx, dy = ex - sx, ey - sy; L2 = dx * dx + dy * dy
u = max(0, min(1, ((vx - sx) * dx + (vy - sy) * dy) / L2)); nx, ny = sx + u * dx, sy + u * dy
ax, ay = vx - nx, vy - ny; d = math.hypot(ax, ay); ax, ay = ax / d, ay / d
clr_before = d - ToMM(trk.GetWidth()) / 2 - ToMM(via.GetDrillValue()) / 2
newpos = VECTOR2I(FromMM(vx + ax * 0.02), FromMM(vy + ay * 0.02))
moved = move_point(via.GetPosition(), newpos); via.SetPosition(newpos)
print(f"(1) via GND {vx:.4f},{vy:.4f} -> {ToMM(newpos.x):.4f},{ToMM(newpos.y):.4f}; hole clearance {clr_before:.4f} -> {clr_before+0.02:.4f}; track ends moved {moved}")

# (2) rule areas around NPTH pegs
p1 = b.FindFootprintByReference("P1")
cu = [b.GetLayerID(l) for l in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")]
k = 0
for pad in p1.Pads():
    if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH: continue
    k += 1
    cx, cy = pad.GetPosition().x, pad.GetPosition().y; h = FromMM(0.6)
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in cu: ls.addLayer(l)
    z.SetLayerSet(ls); z.SetZoneName(f"P1_NPTH{k}_nocopper")
    z.Outline().NewOutline()
    for (x, y) in ((cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)):
        z.Outline().Append(x, y)
    b.Add(z)
    print(f"(2) rule area P1_NPTH{k}_nocopper 1.2 mm square at {ToMM(cx):.3f},{ToMM(cy):.3f} (hole edge to copper 0.275 mm)")

# (3) +12V meander right end
n3 = 0
for t in tracks:
    if t.GetNetname() != "+12V": continue
    for getter, setter in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        p = getter()
        if abs(ToMM(p.x) - 142.1067) < 0.001:
            setter(VECTOR2I(FromMM(142.08), p.y)); n3 += 1
print(f"(3a) +12V meander endpoints x 142.1067 -> 142.08: {n3} endpoints (edge clearance +0.027 mm)")
c28 = b.FindFootprintByReference("C28")
old = [(p.GetNumber(), VECTOR2I(p.GetPosition())) for p in c28.Pads()]
c28.SetPosition(VECTOR2I(c28.GetPosition().x - FromMM(0.04), c28.GetPosition().y))
newp = {p.GetNumber(): p.GetPosition() for p in c28.Pads()}
m = sum(move_point(o, newp[n]) for n, o in old)
print(f"(3b) C28 moved -0.04 mm in x to {ToMM(c28.GetPosition().x):.4f},{ToMM(c28.GetPosition().y):.4f}; track ends moved {m}")

f = pcbnew.ZONE_FILLER(b); f.Fill(b.Zones()); print("zones refilled")
if "--write" in sys.argv:
    b.Save(PCB); print("saved")
