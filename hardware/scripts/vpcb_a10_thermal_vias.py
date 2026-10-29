"""vpcb_a10_thermal_vias.py - A10 of the PCB engineering pass: thermal/hand-solder vias in the DFN exposed pads.

Autor: Bruno Costa

U8-U11 (TJA1042TK-3, DFN-8 3x3 mm, EP 1.55x2.4 mm on GND) had no via in the exposed pad. For a hand-assembled board
the EP cannot be reached with an iron from the top; one or two small GND vias inside the EP let the pad be heated and
wetted from the bottom (and give the usual thermal path to the In2/B.Cu GND pours). Vias are 0.6/0.3 mm (same as the
TPS5450 EP vias), tented on both sides per the board setup, placed on the EP centre line at the positions that keep
>= 0.1 mm to every other-net copper on every layer (B.Cu has signal tracks under these footprints).

Writes the board, refills zones, and reports what was placed; DRC is run by the caller.
Usage: python (KiCad) vpcb_a10_thermal_vias.py [--dry]
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I

ROOT = hp.OUTPUT_ROOT
PCB = str(ROOT / "hardware/hybrid-panda/HybridPanda.kicad_pcb")
OUTD = ROOT / "hardware/reports/verification-pcb"
DRY = "--dry" in sys.argv
REFS = ("U8", "U9", "U10", "U11")
VIA_D, VIA_DRILL, CLR = FromMM(0.6), FromMM(0.3), FromMM(0.1)
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

board = pcbnew.LoadBoard(PCB)
gnd = board.GetNetcodeFromNetname("GND")
TRACKS = list(board.GetTracks())
PADS = [p for fp in board.GetFootprints() for p in fp.Pads()]


def free(pos, ep, tracks=None, pads=None):
    """True if a via at pos keeps CLR to every other-net copper item on every copper layer."""
    tracks = TRACKS if tracks is None else tracks
    pads = PADS if pads is None else pads
    circ = pcbnew.SHAPE_CIRCLE(pos, VIA_D // 2)
    for t in tracks:
        if t.GetNetCode() != gnd and t.GetEffectiveShape().Collide(circ, CLR):
            return False
    for p in pads:
        if p is ep or p.GetNetCode() == gnd and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            continue
        for l in CU:
            if p.IsOnLayer(l) and p.GetEffectiveShape(l).Collide(circ, CLR):
                return False
    # hole-to-hole 0.25 against other drilled items
    for t in tracks:
        if t.Type() == pcbnew.PCB_VIA_T and (t.GetPosition() - pos).EuclideanNorm() < VIA_DRILL + FromMM(0.25):
            return False
    for p in pads:
        if p.GetDrillSize().x and (p.GetPosition() - pos).EuclideanNorm() < VIA_DRILL + FromMM(0.25):
            return False
    return True


rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "dry": DRY, "placed": {}, "skipped": {}, "rerouted": []}

# U8 pre-step: the In2.Cu BUS1N_STB track crossing the EP at y = 60.609 blocks every via position; jog it 0.3 mm north
# (the EP top edge is at y = 60.31, the BUS1O_STB via at 126.816,59.676 stays 0.63 mm from the new centre line).
JOG_FROM, JOG_TO = VECTOR2I(FromMM(128.904), FromMM(60.609)), VECTOR2I(FromMM(123.959), FromMM(60.609))
for t in TRACKS:
    def _near(a, bpt):
        return (a - bpt).EuclideanNorm() < FromMM(0.005)
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.In2_Cu and t.GetNetname() == "BUS1N_STB" and \
            ((_near(t.GetStart(), JOG_FROM) and _near(t.GetEnd(), JOG_TO)) or (_near(t.GetStart(), JOG_TO) and _near(t.GetEnd(), JOG_FROM))):
        pts = [JOG_FROM, VECTOR2I(FromMM(128.6), FromMM(60.305)), VECTOR2I(FromMM(126.45), FromMM(60.305)),
               VECTOR2I(FromMM(126.146), FromMM(60.609)), JOG_TO]
        w, net = t.GetWidth(), t.GetNetCode()
        if not DRY:
            board.Remove(t)
        TRACKS.remove(t)
        for a, bpt in zip(pts, pts[1:]):
            s = pcbnew.PCB_TRACK(board)
            s.SetLayer(pcbnew.In2_Cu); s.SetWidth(w); s.SetNetCode(net); s.SetStart(a); s.SetEnd(bpt)
            if not DRY:
                board.Add(s)
            TRACKS.append(s)
        rep["rerouted"].append("In2.Cu BUS1N_STB 128.904,60.609 -> 123.959,60.609 replaced by jog via y=60.305 (x 126.45..128.6)")
        print(rep["rerouted"][-1])
        break
else:
    print("U8 pre-step: In2 BUS1N_STB segment not found (already rerouted?)")

for ref in REFS:
    fp = board.FindFootprintByReference(ref)
    ep = max(fp.Pads(), key=lambda p: p.GetSize(p.GetLayer()).x * p.GetSize(p.GetLayer()).y)
    assert ep.GetNetCode() == gnd, ref
    c = ep.GetPosition()
    ebb = ep.GetBoundingBox()  # board frame (the EP is rotated on U10/U11); EP pads are rectangles
    sz = VECTOR2I(ebb.GetWidth(), ebb.GetHeight())
    # grid search inside the EP (via fully inside the pad with 0.05 mm margin), 0.05 mm steps
    hx, hy = sz.x // 2 - VIA_D // 2 - FromMM(0.05), sz.y // 2 - VIA_D // 2 - FromMM(0.05)
    step = FromMM(0.05)
    near = ep.GetBoundingBox()
    near.Inflate(FromMM(1.0))
    tr = [t for t in TRACKS if t.GetBoundingBox().Intersects(near)]
    pd = [p for p in PADS if p.GetBoundingBox().Intersects(near)]
    cands = []
    y = -hy
    while y <= hy:
        x = -hx
        while x <= hx:
            p = VECTOR2I(c.x + x, c.y + y)
            if free(p, ep, tr, pd):
                cands.append(p)
            x += step
        y += step
    placed = []
    if cands:
        # pair with the largest separation (>= 0.6 mm between via edges + 0.25 hole-to-hole), else the single most central
        best = None
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                d = (cands[i] - cands[j]).EuclideanNorm()
                if d >= VIA_D + FromMM(0.25) and (best is None or d > best[0]):
                    best = (d, cands[i], cands[j])
        if best:
            placed = [best[1], best[2]]
        else:
            placed = [min(cands, key=lambda p: (p - c).EuclideanNorm())]
    if not placed:
        rep["skipped"][ref] = "no free position inside EP"
        print(ref, "skipped: no free position")
        continue
    for p in placed:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        try:
            v.SetWidth(pcbnew.F_Cu, VIA_D)
        except TypeError:
            v.SetWidth(VIA_D)
        v.SetDrill(VIA_DRILL)
        v.SetNetCode(gnd)
        if not DRY:
            board.Add(v)
    rep["placed"][ref] = ["%.3f,%.3f" % (ToMM(p.x), ToMM(p.y)) for p in placed]
    print(ref, "EP %.2fx%.2f @ %.3f,%.3f ->" % (ToMM(sz.x), ToMM(sz.y), ToMM(c.x), ToMM(c.y)), rep["placed"][ref])

if not DRY:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB)
OUTD.mkdir(parents=True, exist_ok=True)
(OUTD / "thermal-vias.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
sys.stdout.flush()
os._exit(0)
