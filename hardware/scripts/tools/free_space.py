"""ASCII occupancy map per outer layer (courtyards + tracks + vias), 0.5 mm cells.

usage: free_space.py [cell_mm] [x0 y0 x1 y1]
'#' courtyard, '+' track/via, '.' free, 'o' outside board
"""
import os
import sys

import pcbnew
from pcbnew import ToMM

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hp_common as hp  # noqa: E402

b = pcbnew.LoadBoard(os.path.join(str(hp.OUTPUT_ROOT), "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb"))
cell = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
bb = b.GetBoardEdgesBoundingBox()
if len(sys.argv) > 5:
    X0, Y0, X1, Y1 = [float(v) for v in sys.argv[2:6]]
else:
    X0, Y0, X1, Y1 = ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())
nx = int((X1 - X0) / cell) + 1
ny = int((Y1 - Y0) / cell) + 1


def mark(grid, x0, y0, x1, y1, ch):
    i0 = max(0, int((x0 - X0) / cell)); i1 = min(nx - 1, int((x1 - X0) / cell))
    j0 = max(0, int((y0 - Y0) / cell)); j1 = min(ny - 1, int((y1 - Y0) / cell))
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            if grid[j][i] == "." or ch == "#":
                grid[j][i] = ch


LAYERS = {"F": (pcbnew.F_Cu, pcbnew.F_CrtYd), "B": (pcbnew.B_Cu, pcbnew.B_CrtYd), "1": (pcbnew.In1_Cu, None), "2": (pcbnew.In2_Cu, None)}
sel = os.environ.get("FS_LAYERS", "FB")
for layer, cy in [LAYERS[k] for k in sel]:
    grid = [["." for _ in range(nx)] for _ in range(ny)]
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetLayer() == layer:
            tb = t.GetBoundingBox()
            mark(grid, ToMM(tb.GetLeft()), ToMM(tb.GetTop()), ToMM(tb.GetRight()), ToMM(tb.GetBottom()), "+")
    for fp in b.GetFootprints():
        if cy is None or fp.GetLayer() != layer:
            # THT pads block both sides
            for p in fp.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    pb = p.GetBoundingBox()
                    mark(grid, ToMM(pb.GetLeft()), ToMM(pb.GetTop()), ToMM(pb.GetRight()), ToMM(pb.GetBottom()), "#")
            continue
        c = fp.GetCourtyard(cy).BBox()
        if c.GetWidth() == 0:
            c = fp.GetBoundingBox(False, False)
        mark(grid, ToMM(c.GetLeft()), ToMM(c.GetTop()), ToMM(c.GetRight()), ToMM(c.GetBottom()), "#")
    print("=== %s  x %.1f..%.1f  y %.1f..%.1f  cell %.2f" % (b.GetLayerName(layer), X0, X1, Y0, Y1, cell))
    hdr = "      " + "".join(str(int((X0 + i * cell)) % 10) if i % 2 == 0 else " " for i in range(nx))
    print(hdr)
    for j, row in enumerate(grid):
        print("%6.1f %s" % (Y0 + j * cell, "".join(row)))


os._exit(0)
