"""corr_gate.py - portao DRC/ERC reutilizado pelas correcoes auditadas (corr_step*.py).

Uso:
  python -u corr_gate.py drc  [--out 06_REPORTS\\corr\\drc_<tag>.json] [--tag X]   -> resumo por tipo + delta vs baseline
  python -u corr_gate.py erc  [--tag X]
  python -u corr_gate.py backup <stepN>   -> copia .kicad_pcb/.kicad_sch/.kicad_pro para %TEMP%\\hp_backup\\stepN
  python -u corr_gate.py padnets <out.json> -> dump pad->rede de todos os footprints (para diff antes/depois)
  python -u corr_gate.py diffnets <a.json> <b.json>
Importavel: run_drc(out_json) -> dict resumo; summarize(json) -> dict.
"""
import collections
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pcb")
SCH = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_sch")
PRO = os.path.join(ROOT, "04_PROJECT", "HybridPanda", "HybridPanda.kicad_pro")
CLI = str(hp.KICAD_CLI)
CORR_DIR = os.path.join(ROOT, "06_REPORTS", "corr")
# frozen copy of the pre-correction step7 DRC (step7_validate.py rewrites hybrid_DRC_step7.json on every run)
BASELINE = os.path.join(CORR_DIR, "drc_baseline_step7_orig.json")
if not os.path.exists(BASELINE):
    BASELINE = os.path.join(ROOT, "06_REPORTS", "hybrid_DRC_step7.json")


def summarize(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    viol = d.get("violations", [])
    unc = d.get("unconnected_items", [])
    sch = d.get("schematic_parity", [])
    types = collections.Counter(v["type"] for v in viol)
    return {
        "total": len(viol) + len(unc) + len(sch),
        "violations": len(viol),
        "unconnected": len(unc),
        "schematic_parity": len(sch),
        "clearance": types.get("clearance", 0),
        "types": dict(sorted(types.items())),
    }


def run_drc(out_json, pcb=PCB, timeout=300):
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", out_json, pcb],
                   capture_output=True, text=True, timeout=timeout)
    return summarize(out_json)


def run_erc(out_json, sch=SCH, timeout=300):
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    subprocess.run([CLI, "sch", "erc", "--format", "json", "--severity-all", "--units", "mm", "-o", out_json, sch],
                   capture_output=True, text=True, timeout=timeout)
    with open(out_json, encoding="utf-8") as f:
        d = json.load(f)
    c = collections.Counter()
    for sh in d.get("sheets", []):
        for v in sh.get("violations", []):
            c[(v["severity"], v["type"])] += 1
    errors = sum(n for (s, t), n in c.items() if s == "error")
    return {"errors": errors, "warnings": sum(n for (s, t), n in c.items() if s == "warning"),
            "types": {"%s:%s" % k: n for k, n in sorted(c.items())}}


def delta(cur, base):
    out = {}
    for k in set(cur["types"]) | set(base["types"]):
        d = cur["types"].get(k, 0) - base["types"].get(k, 0)
        if d:
            out[k] = d
    if cur["unconnected"] != base["unconnected"]:
        out["unconnected_items"] = cur["unconnected"] - base["unconnected"]
    return out


def backup(step):
    dest = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "hp_backup", step)
    os.makedirs(dest, exist_ok=True)
    for p in (PCB, SCH, PRO):
        shutil.copy2(p, dest)
    print("backup -> " + dest)


def padnets(out):
    import pcbnew
    b = pcbnew.LoadBoard(PCB)
    d = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            d["%s.%s" % (fp.GetReference(), p.GetNumber())] = p.GetNetname()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, sort_keys=True)
    print("%d pads -> %s" % (len(d), out))


def diffnets(a, b):
    A = json.load(open(a, encoding="utf-8"))
    B = json.load(open(b, encoding="utf-8"))
    n = 0
    for k in sorted(set(A) | set(B)):
        if A.get(k) != B.get(k):
            n += 1
            print("  %s: %r -> %r" % (k, A.get(k), B.get(k)))
    print("pad-net differences: %d" % n)
    return n


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    cmd = a[0]
    tag = time.strftime("%H%M%S")
    if "--tag" in a:
        tag = a[a.index("--tag") + 1]
    if cmd == "drc":
        out = os.path.join(CORR_DIR, "drc_%s.json" % tag)
        if "--out" in a:
            out = a[a.index("--out") + 1]
        s = run_drc(out)
        base = summarize(BASELINE)
        print(json.dumps({"summary": s, "delta_vs_step7_baseline": delta(s, base), "file": os.path.relpath(out, ROOT)}, indent=1))
    elif cmd == "erc":
        out = os.path.join(CORR_DIR, "erc_%s.json" % tag)
        print(json.dumps(run_erc(out), indent=1))
    elif cmd == "backup":
        backup(a[1])
    elif cmd == "padnets":
        padnets(a[1])
    elif cmd == "diffnets":
        sys.exit(1 if diffnets(a[1], a[2]) else 0)


if __name__ == "__main__":
    main()
