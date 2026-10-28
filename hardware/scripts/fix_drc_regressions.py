# -*- coding: utf-8 -*-
"""Corrige regressoes de DRC introduzidas por fix_audit.py / fix_vip_rest.py.

  1. Via +3V3 em 115.250,68.752 encosta no keepout de SW1  -> desloca +0.05 mm em X (e extremidades das trilhas ligadas)
  2. D7 (TVS BUS2) a 0.066 mm da trilha BUS2_H                -> desloca o segmento vertical da trilha (+0.08 mm); TVS nao se move
  3. D8 (TVS BUS1N) a 0.020 mm da trilha BUS1N_L              -> re-dobra a trilha acima do pad (y 64.27); TVS nao se move
  4. Trilha +5V In2.Cu 118.918..120.167,46.592 pendurada      -> remove
  5. FID2/FID5 dentro do silk de U3                           -> realoca para 128.41,74.51 (canto inf. direito), keepout 2.2 mm
  (mover D7/D8 foi tentado e gerou 6 novas clearances: TVS encaixotados entre trilhas)

Uso: python fix_drc_regressions.py [--dry]
Autor: Bruno Costa
"""
import json, math, os, sys, subprocess, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PCB = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")
OUT = os.path.join(ROOT, "06_REPORTS", "fix_drc_regressions.json")
KICAD_CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
DRY = "--dry" in sys.argv

def P(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def near(a, bx, by, tol=0.02): return abs(a.x / 1e6 - bx) < tol and abs(a.y / 1e6 - by) < tol

b = pcbnew.LoadBoard(PCB)
log = {"actions": []}

# 1. via +3V3 no keepout de SW1 (+0.05 mm em X; GND via fica a ~0.16 mm)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "+3V3" and near(t.GetPosition(), 115.250, 68.752):
        new = P(115.300, 68.752); moved = 0
        for tr in b.GetTracks():
            if tr.GetClass() == "PCB_TRACK" and tr.GetNetname() == "+3V3":
                if near(tr.GetStart(), 115.250, 68.752): tr.SetStart(new); moved += 1
                if near(tr.GetEnd(), 115.250, 68.752): tr.SetEnd(new); moved += 1
        t.SetPosition(new)
        log["actions"].append({"via_3v3": "115.250,68.752 -> 115.300,68.752", "track_ends_moved": moved})

# 2. D7: segmento vertical BUS2_H x=130.28 -> 130.36 (pad 1 BUS2_L termina em x=130.14)
def move_pt(net, layer, ox, oy, nx, ny):
    n = 0
    for tr in b.GetTracks():
        if tr.GetClass() == "PCB_TRACK" and tr.GetNetname() == net and tr.GetLayerName() == layer:
            if near(tr.GetStart(), ox, oy): tr.SetStart(P(nx, ny)); n += 1
            if near(tr.GetEnd(), ox, oy): tr.SetEnd(P(nx, ny)); n += 1
    return n
n = move_pt("BUS2_H", "F.Cu", 130.280, 55.179, 130.360, 55.179) + move_pt("BUS2_H", "F.Cu", 130.280, 56.120, 130.360, 56.120)
log["actions"].append({"BUS2_H": "vertical x 130.28 -> 130.36", "ends": n})

# 3. D8: BUS1N_L passa pelo canto do pad 2 BUS1N_H (136.29,64.57). Novo caminho: 136.07,64.655 -> 136.07,64.27 -> 137.96,64.27
n = move_pt("BUS1N_L", "F.Cu", 136.355, 64.370, 136.070, 64.270) + move_pt("BUS1N_L", "F.Cu", 137.960, 64.370, 137.960, 64.270)
log["actions"].append({"BUS1N_L": "bend 136.355,64.37 -> 136.07,64.27 ; 137.96,64.37 -> 137.96,64.27", "ends": n})

# 4. trilha +5V pendurada
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "+5V" and t.GetLayerName() == "In2.Cu":
        if (near(t.GetStart(), 118.918, 46.592) and near(t.GetEnd(), 120.167, 46.592)) or \
           (near(t.GetEnd(), 118.918, 46.592) and near(t.GetStart(), 120.167, 46.592)):
            b.Remove(t); log["actions"].append({"removed_dangling_5v": "118.918..120.167,46.592 In2.Cu"})

# 5. FID2 (F.Cu) / FID5 (B.Cu): sob o silk do U3 -> (128.41,74.51), local livre (busca em grade: footprints >0.9 mm, cobre F/B >1.1 mm). Keepout 2.4 -> 2.2 mm
NX, NY, KEEP = 128.41, 74.51, 2.2
for ref in ("FID2", "FID5"):
    f = b.FindFootprintByReference(ref); oldp = f.GetPosition()
    f.SetPosition(P(NX, NY))
    for zn in b.Zones():
        if zn.GetZoneName() == ref + "_nocopper":
            ol = zn.Outline(); ol.RemoveAllContours()
            ol.NewOutline()
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                ol.Append(P(NX + dx * KEEP / 2, NY + dy * KEEP / 2))
            zn.HatchBorder()
    log["actions"].append({ref: "%.3f,%.3f -> %.3f,%.3f (keepout %.1f mm)" % (oldp.x / 1e6, oldp.y / 1e6, NX, NY, KEEP)})

# refill zones + DRC rapido
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
if not DRY:
    pcbnew.SaveBoard(PCB, b)
    rep = os.path.join(tempfile.gettempdir(), "hp_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", rep, PCB],
                   capture_output=True, text=True)
    d = json.load(open(rep, encoding="utf-8"))
    by = {}
    for v in d.get("violations", []): by[v["type"]] = by.get(v["type"], 0) + 1
    log["drc_after"] = {"unconnected": len(d.get("unconnected_items", [])), "total": len(d.get("violations", [])), "by_type": by,
                        "errors": [ (v["type"], v["description"]) for v in d.get("violations", []) if v["type"] in ("clearance", "items_not_allowed", "track_dangling", "shorting_items")]}
json.dump(log, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(log, indent=1, ensure_ascii=False))
