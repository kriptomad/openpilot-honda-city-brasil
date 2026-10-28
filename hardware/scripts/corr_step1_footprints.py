"""corr_step1_footprints.py - aplica as correcoes de footprint da auditoria (06_REPORTS/footprint_audit).

Reusa proposed_fixes.py (q3_sot323, sot23_comma, led_u5, xl1509_u12, attr_smd, model_3d, courtyard_l3) e acrescenta:
  * P1: pads THT B1-B12 0.60 -> 0.65 (datasheet TYPE-C-31-M-04: anel 0.65) + remocao dos 12 circulos F.Paste soltos
  * R6: footprint Capacitor_SMD:C_0603_1608Metric -> Resistor_SMD:R_0603_1608Metric (biblioteca KiCad 10),
    preservando posicao, rotacao, camada, referencia, valor, path e redes dos pads; tambem no .kicad_sch
Relatorio: 06_REPORTS/corr/step1_footprints.json
"""
import importlib.util
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import FromMM, ToMM

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")
SCH = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_sch")
FP_LIB = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "share", "kicad", "footprints")
OUT = os.path.join(ROOT, "06_REPORTS", "corr", "step1_footprints.json")

spec = importlib.util.spec_from_file_location(
    "proposed_fixes", os.path.join(ROOT, "06_REPORTS", "footprint_audit", "proposed_fixes.py"))
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

FIXES = ["q3_sot323", "sot23_comma", "led_u5", "xl1509_u12", "attr_smd", "model_3d", "courtyard_l3"]
report = {"fixes": [], "p1": [], "r6": {}, "pad_moves": []}


def find(board, ref):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    return None


def main():
    board = pcbnew.LoadBoard(PCB)
    before = {"%s.%s" % (fp.GetReference(), p.GetNumber()): p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads()}

    for key in FIXES:
        for ref in pf.DEFAULT_REFS[key]:
            fp = find(board, ref)
            pf.LOG.clear()
            pf.apply_fix(key, fp, dry=False)
            report["fixes"].append({"fix": key, "ref": ref, "log": list(pf.LOG)})

    # P1: anel 0.65 (datasheet) + pasta solta
    p1 = find(board, "P1")
    for pad in p1.Pads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNumber().startswith("B"):
            pad.SetSize(pcbnew.PADSTACK.ALL_LAYERS, pcbnew.VECTOR2I(FromMM(0.65), FromMM(0.65)))
            report["p1"].append("pad %s 0.60 -> 0.65 (furo 0.40, anel 0.125)" % pad.GetNumber())
    pf.LOG.clear()
    pf.remove_graphics(p1, ["F.Paste"], False, only_shape=pcbnew.SHAPE_T_CIRCLE)
    report["p1"] += pf.LOG

    # R6: troca de footprint pela biblioteca
    old = find(board, "R6")
    new = pcbnew.FootprintLoad(os.path.join(FP_LIB, "Resistor_SMD.pretty"), "R_0603_1608Metric")
    assert new is not None, "R_0603_1608Metric nao encontrado em " + FP_LIB
    new.SetFPID(pcbnew.LIB_ID("Resistor_SMD", "R_0603_1608Metric"))
    new.SetPosition(old.GetPosition())
    if old.IsFlipped():
        new.Flip(old.GetPosition(), False)
    new.SetOrientation(old.GetOrientation())
    new.SetReference(old.GetReference())
    new.SetValue(old.GetValue())
    new.SetPath(old.GetPath())
    new.SetAttributes(old.GetAttributes())
    for fld in old.GetFields():
        if fld.GetName() not in ("Reference", "Value", "Footprint"):
            f2 = next((x for x in new.GetFields() if x.GetName() == fld.GetName()), None)
            if f2 is None:
                f2 = pcbnew.PCB_FIELD(new, fld.GetName())
                new.AddField(f2)
                f2.thisown = 0
            f2.SetText(fld.GetText())
            f2.SetVisible(fld.IsVisible())
    new.Reference().SetVisible(old.Reference().IsVisible())
    new.Value().SetVisible(old.Value().IsVisible())
    new.Reference().SetPosition(old.Reference().GetPosition())
    new.Value().SetPosition(old.Value().GetPosition())
    new.Reference().SetLayer(old.Reference().GetLayer())
    new.Value().SetLayer(old.Value().GetLayer())
    oldnets = {p.GetNumber(): (p.GetNetCode(), p.GetNetname()) for p in old.Pads()}
    report["r6"] = {"old_fpid": old.GetFPID().GetUniStringLibId(), "new_fpid": new.GetFPID().GetUniStringLibId(),
                    "pos": [ToMM(old.GetPosition().x), ToMM(old.GetPosition().y)], "rot": old.GetOrientationDegrees(),
                    "layer": board.GetLayerName(old.GetLayer()), "nets": {k: v[1] for k, v in oldnets.items()},
                    "old_pads": [[ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)] for p in old.Pads()],
                    "new_pads": [[ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)] for p in new.Pads()]}
    board.Remove(old)
    board.Add(new)
    new.thisown = 0
    for p in new.Pads():
        p.SetNet(board.GetNetInfo().GetNetItem(oldnets[p.GetNumber()][0]))

    after = {"%s.%s" % (fp.GetReference(), p.GetNumber()): p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads()}
    diff = {k: (before.get(k), after.get(k)) for k in set(before) | set(after) if before.get(k) != after.get(k)}
    report["pad_net_diff"] = diff
    assert not diff, "redes de pad alteradas: %r" % diff

    pcbnew.SaveBoard(PCB, board)

    # esquematico: Footprint do R6
    with open(SCH, encoding="utf-8") as f:
        s = f.read()
    pat = re.compile(r'(\(property "Reference" "R6" .*?)\(property "Footprint" "Capacitor_SMD:C_0603_1608Metric"', re.S)
    s2, n = pat.subn(r'\1(property "Footprint" "Resistor_SMD:R_0603_1608Metric"', s, count=1)
    assert n == 1
    with open(SCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(s2)
    report["sch"] = "R6 Footprint -> Resistor_SMD:R_0603_1608Metric"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=True)
    print(json.dumps({"fixes": len(report["fixes"]), "p1": len(report["p1"]), "r6": report["r6"]["new_fpid"],
                      "pad_net_diff": len(diff)}, indent=1))


if __name__ == "__main__":
    main()
