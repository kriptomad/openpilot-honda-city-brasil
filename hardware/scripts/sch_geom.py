"""sch_geom.py - geometry helpers for kiutils schematics (shared by STEP 4 scripts).

Pin connection point of a placed symbol:  abs = pos + Rot(angle) * Mirror(m) * (px, -py)
(lib coordinates are y-up, schematic is y-down; KiCad rotates counter-clockwise as seen on screen).
selftest(): every pin end of every symbol in the baseline must coincide with a wire end, label,
no-connect, junction or another pin -> proves the transform before it is used to build anything.
"""
from __future__ import annotations

import math
from pathlib import Path

from kiutils.schematic import Schematic
from kiutils.items.common import Position

GRID = 1.27


def r2(v: float) -> float:
    return round(v + 0.0, 4)


def lib_pins(sch: Schematic, lib_id: str, unit: int | None = None):
    for ls in sch.libSymbols:
        if ls.libId == lib_id:
            pins = []
            for u in ls.units:
                if unit is not None and u.unitId not in (0, unit):
                    continue
                pins.extend(u.pins)
            return pins
    raise KeyError(lib_id)


def transform(px: float, py: float, sx: float, sy: float, angle: float, mirror: str | None):
    x, y = px, -py  # to y-down
    a = math.radians(angle or 0)
    # screen-CCW rotation in a y-down system, then mirror (verified against baseline: Q3/Q4 mirror x + 90 deg)
    xr = x * math.cos(a) + y * math.sin(a)
    yr = -x * math.sin(a) + y * math.cos(a)
    if mirror == "x":
        yr = -yr
    elif mirror == "y":
        xr = -xr
    return r2(sx + xr), r2(sy + yr)


def pin_points(sch: Schematic, sym) -> dict[str, tuple[float, float]]:
    """pin number -> absolute connection point."""
    out = {}
    for p in lib_pins(sch, sym.libId, sym.unit):
        out[p.number] = transform(p.position.X, p.position.Y, sym.position.X, sym.position.Y,
                                  sym.position.angle, sym.mirror)
    return out


def all_anchor_points(sch: Schematic) -> set[tuple[float, float]]:
    pts = set()
    for g in sch.graphicalItems:
        if g.__class__.__name__ == "Connection":
            for p in g.points:
                pts.add((r2(p.X), r2(p.Y)))
    for coll in (sch.globalLabels, sch.labels, sch.hierarchicalLabels, sch.noConnects, sch.junctions):
        for it in coll:
            pts.add((r2(it.position.X), r2(it.position.Y)))
    return pts


def selftest(sch_path: Path) -> tuple[int, int, list]:
    sch = Schematic.from_file(str(sch_path))
    anchors = all_anchor_points(sch)
    pin_pts = {}
    for sym in sch.schematicSymbols:
        ref = next(p.value for p in sym.properties if p.key == "Reference")
        for num, pt in pin_points(sch, sym).items():
            pin_pts.setdefault(pt, []).append(f"{ref}.{num}")
    ok = bad = 0
    missing = []
    for pt, owners in pin_pts.items():
        if pt in anchors or len(owners) > 1:
            ok += 1
        else:
            # power symbols have a single hidden pin that may sit on a wire *middle*: check collinearity
            on_wire = False
            for g in sch.graphicalItems:
                if g.__class__.__name__ != "Connection":
                    continue
                (x1, y1), (x2, y2) = (g.points[0].X, g.points[0].Y), (g.points[-1].X, g.points[-1].Y)
                if min(x1, x2) - 1e-3 <= pt[0] <= max(x1, x2) + 1e-3 and min(y1, y2) - 1e-3 <= pt[1] <= max(y1, y2) + 1e-3:
                    if abs((x2 - x1) * (pt[1] - y1) - (y2 - y1) * (pt[0] - x1)) < 1e-3:
                        on_wire = True
                        break
            if on_wire:
                ok += 1
            else:
                bad += 1
                missing.append((owners, pt))
    return ok, bad, missing


if __name__ == "__main__":
    import sys
    ok, bad, missing = selftest(Path(sys.argv[1]))
    print(f"pins anchored: {ok}, unanchored: {bad}")
    for m in missing[:40]:
        print("  ", m)
