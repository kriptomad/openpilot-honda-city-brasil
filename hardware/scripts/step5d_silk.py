"""step5d_silk.py - 5d: cosmético pós-5c (determinista, não toca em cobre).

Esconde o texto de referência (serigrafia) dos componentes ADICIONADOS no 5a (C38-C63, D13, D14, FB1, J1, L5, R28-R33):
0402/0603 colocados a 1,1 mm do LQFP-144 não têm espaço para referência sem cair sobre pads vizinhos
(DRC `silk_over_copper` / `silk_overlap`). Os componentes do baseline mantêm a serigrafia original.
Depois corre o DRC e grava hardware\\reports\hybrid_DRC_step5_final.json. Só escreve dentro de OUTPUT_ROOT.
"""
import json, os, re, subprocess, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew

PCB = str(hp.OUTPUT_ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_pcb")
OUT = str(hp.REPORT_DIR / "hybrid_DRC_step5_final.json")
ADDED = re.compile(r"^(C(3[89]|[4-5]\d|6[0-3])|D1[34]|FB1|J1|L5|R(2[89]|3[0-3]))$")
board = pcbnew.LoadBoard(PCB)
hidden = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ADDED.match(ref) and fp.Reference().IsVisible():
        fp.Reference().SetVisible(False); hidden.append(ref)
hp.assert_inside_output(PCB); board.Save(PCB)
p = subprocess.run([str(hp.KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", OUT, PCB], capture_output=True, text=True)
d = json.load(open(OUT, encoding="utf-8"))
c = collections.Counter(v["type"] for v in d["violations"])
rep = {"hidden_refs": sorted(hidden), "unconnected_items": len(d["unconnected_items"]), "violations_by_type": dict(c.most_common()), "drc_exit": p.returncode}
json.dump(rep, open(str(hp.REPORT_DIR / "step5d_silk.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(rep, indent=1))
