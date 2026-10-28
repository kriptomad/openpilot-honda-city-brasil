# -*- coding: utf-8 -*-
"""Elimina os 4 via-in-pad restantes (apos fix_audit.py / fix_vip_rest.py).

  D13.1 (GND, B.Cu)  via 127.59,67.11 + stub -> remover (pad liga a zona GND B.Cu); verificado por DRC (0 nao ligados)
  U1.2  (GND, F.Cu)  via 119.00,53.42 sem trilhas -> remover (pad liga a zona GND F.Cu)
  C30.2 (+5V, F.Cu)  C30 desloca -0.35 mm em X (extremidades de trilhas nos pads acompanham)
  C33.2 (+5V, F.Cu)  C33 desloca +0.40 mm em Y
Se a remocao de uma via GND criar item nao ligado, o script reverte essa via e reporta.

Uso: python fix_vip_final.py [--dry]
Autor: Bruno Costa
"""
import json, os, sys, subprocess, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))  # repository root
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
OUT = os.path.join(ROOT, "hardware/reports", "fix_vip_final.json")
KICAD_CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
DRY = "--dry" in sys.argv

def P(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def near(a, x, y, tol=0.02): return abs(a.x / 1e6 - x) < tol and abs(a.y / 1e6 - y) < tol

def drc(board_path):
    rep = os.path.join(tempfile.gettempdir(), "hp_drc_vip.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", rep, board_path], capture_output=True, text=True)
    d = json.load(open(rep, encoding="utf-8"))
    by = {}
    for v in d.get("violations", []): by[v["type"]] = by.get(v["type"], 0) + 1
    return {"unconnected": len(d.get("unconnected_items", [])), "total": len(d.get("violations", [])), "by_type": by,
            "errors": [(v["type"], v["description"], [i["description"] for i in v["items"]]) for v in d.get("violations", [])
                       if v["type"] in ("clearance", "items_not_allowed", "track_dangling", "shorting_items", "isolated_copper")]}

def vip_count(b):
    n = []
    for v in b.GetTracks():
        if v.GetClass() != "PCB_VIA": continue
        for f in b.Footprints():
            for p in f.Pads():
                if p.GetDrillSize().x != 0: continue
                l = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
                if not v.IsOnLayer(l): continue
                if p.GetEffectiveShape(l).Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetWidth() // 2), 0):
                    n.append("%s.%s<-%s@%.2f,%.2f" % (f.GetReference(), p.GetNumber(), v.GetNetname(), v.GetPosition().x / 1e6, v.GetPosition().y / 1e6))
    return n

b = pcbnew.LoadBoard(PCB)
log = {"before": vip_count(b), "actions": []}
tmp = os.path.join(tempfile.gettempdir(), "hp_vip_tmp.kicad_pcb")

def remove_via(x, y, net):
    removed = []
    for t in list(b.GetTracks()):
        if t.GetNetname() != net: continue
        if t.GetClass() == "PCB_VIA" and near(t.GetPosition(), x, y): removed.append(t)
        elif t.GetClass() == "PCB_TRACK" and (near(t.GetStart(), x, y) or near(t.GetEnd(), x, y)): removed.append(t)
    for t in removed: b.Remove(t)
    return removed

def try_remove(x, y, net, label):
    removed = remove_via(x, y, net)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(tmp, b)
    r = drc(tmp)
    if r["unconnected"] == 0:
        log["actions"].append({label: "via %s removida (%d itens); DRC nao ligados = 0" % (net, len(removed))})
        return True
    for t in removed: b.Add(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    log["actions"].append({label: "remocao criaria %d nao ligados -> revertido" % r["unconnected"]})
    return False

def move_fp(ref, dx, dy):
    f = b.FindFootprintByReference(ref); pos = f.GetPosition()
    ends = []
    for p in f.Pads():
        for tr in b.GetTracks():
            if tr.GetClass() == "PCB_TRACK" and tr.IsOnLayer(f.GetLayer()):
                if tr.GetStart() == p.GetPosition(): ends.append((tr, "s"))
                if tr.GetEnd() == p.GetPosition(): ends.append((tr, "e"))
    f.SetPosition(P(pos.x / 1e6 + dx, pos.y / 1e6 + dy))
    for tr, w in ends:
        q = tr.GetStart() if w == "s" else tr.GetEnd()
        (tr.SetStart if w == "s" else tr.SetEnd)(pcbnew.VECTOR2I(q.x + int(dx * 1e6), q.y + int(dy * 1e6)))
    log["actions"].append({ref: "dx=%.2f dy=%.2f, %d extremidades de trilha" % (dx, dy, len(ends))})

try_remove(127.59, 67.11, "GND", "D13.1")
try_remove(119.00, 53.42, "GND", "U1.2")
move_fp("C30", -0.35, 0.0)
move_fp("C33", 0.0, 0.40)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
log["after"] = vip_count(b)
if not DRY:
    pcbnew.SaveBoard(PCB, b)
    log["drc_after"] = drc(PCB)
json.dump(log, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(log, indent=1, ensure_ascii=False))
