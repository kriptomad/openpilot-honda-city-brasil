#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
lib_compare.py - Compare every board footprint with the library copy (pad by pad)
and optionally with a list of candidate standard footprints (to find which
standard footprint a BlackPanda:* geometry matches / whether the pinout is mirrored).

Usage:
  python.exe -u lib_compare.py <board.kicad_pcb> <out.json>

Read-only: the board is never saved.
"""
import sys, os, json, math
import pcbnew

NM = 1e6
STD = r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
PRJ = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "HybridPanda.pretty")
ORIG = r"archive\baseline-original\BlackPanda\kicad_project\BlackPanda.pretty"

# Candidate standard footprints to test against BlackPanda:* / suspicious ones
CANDIDATES = {
    "SOT95P230X110-3N": ["Package_TO_SOT_SMD/SOT-23", "Package_TO_SOT_SMD/SOT-23_Handsoldering"],
    "SOT23-3": ["Package_TO_SOT_SMD/SOT-23", "Package_TO_SOT_SMD/SOT-23_Handsoldering"],
    "DIOM4325X250N": ["Diode_SMD/D_SMA", "Diode_SMD/D_SMA_Handsoldering"],
    "CONV_TPS5450DDAR": ["Package_SO/HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm", "Package_SO/Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm", "Package_SO/SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm"],
    "LED-ARRAY-SMD_4P-L2.2-W2.1-BR": ["LED_SMD/LED_Cree-PLCC4_2x2mm_CW", "LED_SMD/LED_RGB_PLCC-4_2x2mm"],
    "IND-SMD_L7.3-W6.8": ["Inductor_SMD/L_Bourns-SRN6045", "Inductor_SMD/L_Bourns_SRN6045TA", "Inductor_SMD/L_Bourns-SRU8028_8.0x8.0mm", "Inductor_SMD/L_Taiyo-Yuden_NR-60xx"],
    "L_10.5x11.5_H4.0": ["Inductor_SMD/L_Wuerth_WE-PD-Typ-LS_10x11", "Inductor_SMD/L_Bourns-SRR1210A", "Inductor_SMD/L_Coilcraft_XAL1010"],
    "USB-C-SMD_TYPE-C-USB-20": ["Connector_USB/USB_C_Receptacle_HRO_TYPE-C-31-M-12", "Connector_USB/USB_C_Receptacle_XKB_U262-16XN-4BVC11"],
}


def mm(v):
    return round(v / NM, 4)


def pad_table(fp, flip_back=False):
    """Pads of a footprint as dict num->list of (x,y,sx,sy,shape,attr,layers) local coords (rotation 0)."""
    out = {}
    for p in fp.Pads():
        pos = p.GetPosition()
        pos = pcbnew.VECTOR2I(pos.x - fp.GetPosition().x, pos.y - fp.GetPosition().y)
        try:
            sz = p.GetSize(pcbnew.F_Cu)
        except TypeError:
            sz = p.GetSize()
        try:
            shp = p.GetShape(pcbnew.F_Cu)
        except TypeError:
            shp = p.GetShape()
        lay = p.GetLayerSet()
        layers = []
        for lid in lay.Seq():
            layers.append(pcbnew.LayerName(lid))
        out.setdefault(p.GetNumber(), []).append(dict(x=mm(pos.x), y=mm(pos.y), sx=mm(sz.x), sy=mm(sz.y), shape=int(shp), attr=int(p.GetAttribute()), layers=sorted(layers), drill=mm(p.GetDrillSize().x)))
    return out


def normalise_board_fp(fp):
    """Return a copy of the board footprint at rotation 0, on the front side, at origin."""
    c = pcbnew.FOOTPRINT(fp)  # copy
    c.SetOrientationDegrees(0)
    if c.GetLayer() == pcbnew.B_Cu:
        c.Flip(c.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        # KiCad flips around the position: after flip the footprint is on F.Cu,
        # pad local x mirrored; a second rotation set to 0 keeps consistency.
        c.SetOrientationDegrees(0)
    return c


def load_lib(lib_nick, name):
    paths = []
    if lib_nick == "BlackPanda":
        paths = [PRJ]
    else:
        paths = [os.path.join(STD, lib_nick + ".pretty")]
    for p in paths:
        try:
            fp = pcbnew.FootprintLoad(p, name)
            if fp:
                return fp
        except Exception:
            pass
    return None


def diff_tables(a, b):
    """Diff two pad tables (board vs lib). Returns list of human readable diffs."""
    diffs = []
    for num in sorted(set(a) | set(b), key=lambda s: (len(s), s)):
        pa = a.get(num, [])
        pb = b.get(num, [])
        if len(pa) != len(pb):
            diffs.append(f"pad {num!r}: count board={len(pa)} lib={len(pb)}")
            continue
        pa = sorted(pa, key=lambda d: (d["x"], d["y"]))
        pb = sorted(pb, key=lambda d: (d["x"], d["y"]))
        for i, (x, y) in enumerate(zip(pa, pb)):
            for k in ("x", "y", "sx", "sy"):
                if abs(x[k] - y[k]) > 0.005:
                    diffs.append(f"pad {num!r}[{i}] {k}: board={x[k]} lib={y[k]}")
            if x["shape"] != y["shape"]:
                diffs.append(f"pad {num!r}[{i}] shape: board={x['shape']} lib={y['shape']}")
            if x["attr"] != y["attr"]:
                diffs.append(f"pad {num!r}[{i}] attr: board={x['attr']} lib={y['attr']}")
            if x["layers"] != y["layers"]:
                diffs.append(f"pad {num!r}[{i}] layers: board={x['layers']} lib={y['layers']}")
            if abs(x["drill"] - y["drill"]) > 0.005:
                diffs.append(f"pad {num!r}[{i}] drill: board={x['drill']} lib={y['drill']}")
    return diffs


def transform(tbl, rot, mirror):
    """Apply rotation (deg, multiples of 90) and optional x-mirror to a pad table (positions only)."""
    out = {}
    a = math.radians(rot)
    c, s = round(math.cos(a)), round(math.sin(a))
    for num, lst in tbl.items():
        out[num] = []
        for d in lst:
            x, y = d["x"], d["y"]
            if mirror:
                x = -x
            nx = x * c - y * s
            ny = x * s + y * c
            e = dict(d)
            e["x"], e["y"] = round(nx, 4), round(ny, 4)
            if rot % 180:
                e["sx"], e["sy"] = d["sy"], d["sx"]
            out[num].append(e)
    return out


def best_match(board_tbl, cand_tbl):
    """Find rotation/mirror minimising pad-centre RMS for same-numbered pads."""
    best = None
    for mirror in (False, True):
        for rot in (0, 90, 180, 270):
            t = transform(cand_tbl, rot, mirror)
            err = 0.0
            n = 0
            for num in board_tbl:
                if num not in t or not num:
                    continue
                for pa in board_tbl[num]:
                    # nearest same-number pad
                    dmin = min(math.hypot(pa["x"] - pb["x"], pa["y"] - pb["y"]) for pb in t[num])
                    err += dmin * dmin
                    n += 1
            if n == 0:
                continue
            rms = math.sqrt(err / n)
            if best is None or rms < best["rms"]:
                best = dict(rot=rot, mirror=mirror, rms=round(rms, 3), n=n)
    return best


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    res = {}
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        nick = str(fp.GetFPID().GetLibNickname())
        name = str(fp.GetFPID().GetLibItemName())
        nb = normalise_board_fp(fp)
        btbl = pad_table(nb)
        entry = dict(lib=f"{nick}:{name}", pads_board=btbl)
        lib = load_lib(nick, name)
        if lib is None:
            entry["lib_diff"] = ["LIB NOT FOUND"]
        else:
            ltbl = pad_table(lib)
            entry["lib_diff"] = diff_tables(btbl, ltbl)
            entry["lib_models"] = [m.m_Filename for m in lib.Models()]
        if nick == "BlackPanda":
            try:
                o = pcbnew.FootprintLoad(ORIG, name)
                entry["orig_blackpanda_diff"] = diff_tables(btbl, pad_table(o)) if o else ["ORIG NOT FOUND"]
            except Exception as e:
                entry["orig_blackpanda_diff"] = [str(e)]
        if name in CANDIDATES:
            entry["candidates"] = {}
            for cand in CANDIDATES[name]:
                lnick, lname = cand.split("/")
                c = load_lib(lnick, lname)
                if c is None:
                    entry["candidates"][cand] = "NOT FOUND"
                    continue
                ctbl = pad_table(c)
                bm = best_match(btbl, ctbl)
                entry["candidates"][cand] = dict(best=bm, cand_pads={k: [(d["x"], d["y"], d["sx"], d["sy"]) for d in v] for k, v in ctbl.items()})
        res[ref] = entry
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    # console summary
    for ref, e in res.items():
        if e["lib_diff"]:
            print(f"--- {ref} {e['lib']}")
            for d in e["lib_diff"][:12]:
                print("   ", d)
            if len(e["lib_diff"]) > 12:
                print("    ...", len(e["lib_diff"]), "diffs total")
        if e.get("orig_blackpanda_diff"):
            print(f"    [vs original comma BlackPanda.pretty] {ref}: {e['orig_blackpanda_diff'][:6]}")
        if e.get("candidates"):
            for cand, v in e["candidates"].items():
                print(f"    cand {ref} ~ {cand}: {v if isinstance(v, str) else v['best']}")


if __name__ == "__main__":
    main()
