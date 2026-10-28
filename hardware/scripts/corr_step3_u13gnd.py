"""Step 3 closure: fix tracks_crossing at U13 (GND stub crossed the USB_R_D+ flow-through link).

Before: U13.2 (GND) -> (128.85,41.2) -> (127.4,41.2) -> via (126.9,41.2) crossed the F.Cu D+ link at x = 127.9.
After:  D+ connector-side track moved from y = 39.1 to y = 38.4 (still inside U3.3, pad spans y 38.22..39.34);
        U13.2 exits upward to a GND via 0.5/0.3 at (128.85,39.2) (0.45 mm from the D+ track).
Usage: python -u corr_step3_u13gnd.py
"""
import os
import sys

import pcbnew
from pcbnew import FromMM, ToMM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp  # noqa: E402

PCB = os.path.join(str(hp.OUTPUT_ROOT), "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")


def P(x, y):
    return pcbnew.VECTOR2I(FromMM(x), FromMM(y))


def same(a, b, tol=0.01):
    return abs(ToMM(a.x) - b[0]) < tol and abs(ToMM(a.y) - b[1]) < tol


def remove_tracks(b, specs):
    n = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            for s in specs:
                if s[0] == "via" and same(t.GetPosition(), s[1]):
                    b.Remove(t); n += 1
        else:
            for s in specs:
                if s[0] == "trk" and ((same(t.GetStart(), s[1]) and same(t.GetEnd(), s[2])) or
                                      (same(t.GetStart(), s[2]) and same(t.GetEnd(), s[1]))):
                    b.Remove(t); n += 1
    return n


def add_track(b, net, a, c, w, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)


def add_via(b, net, pos, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(*pos)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(FromMM(d)); v.SetDrill(FromMM(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v)


def main():
    hp.backup_before_write(PCB, "step3_u13gnd")
    b = pcbnew.LoadBoard(PCB)
    gnd = b.FindNet("GND"); dp = b.FindNet("USB_R_D+")
    n = remove_tracks(b, [
        ("trk", (128.85, 40.0625), (128.85, 41.2)), ("trk", (128.85, 41.2), (127.4, 41.2)), ("trk", (127.4, 41.2), (126.9, 41.2)),
        ("via", (126.9, 41.2)),
        ("trk", (127.9, 40.0625), (127.9, 39.1)), ("trk", (127.9, 39.1), (130.75, 39.1)),
    ])
    print("removed", n)
    add_track(b, dp, (127.9, 40.0625), (127.9, 38.4), 0.2)
    add_track(b, dp, (127.9, 38.4), (130.9, 38.4), 0.2)
    add_track(b, gnd, (128.85, 40.0625), (128.85, 39.2), 0.25)
    add_via(b, gnd, (128.85, 39.2))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
    pcbnew.SaveBoard(PCB, b)
    print("saved"); sys.stdout.flush(); os._exit(0)


if __name__ == "__main__":
    main()
