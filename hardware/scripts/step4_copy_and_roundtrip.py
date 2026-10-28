"""step4_copy_and_roundtrip.py - STEP 4 pre-conditions.

1. Copy 01_BASELINE/original_copy/BlackPanda/kicad_project -> 04_PROJECT/HybridPanda (rename project files).
2. kiutils round-trip proof: load schematic and PCB with kiutils, save to temp, re-export netlist with kicad-cli
   from both original copy and round-tripped copy, compare the set of (ref, pin, net) tuples. Exact text equality
   is not required (kiutils reformats); electrical equality is.
Writes 06_REPORTS/step4_roundtrip.json/.md. Exit 0 if electrically identical.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hp_common as hp
from kiutils.schematic import Schematic
from kiutils.board import Board

SRC = hp.OUTPUT_ROOT / "01_BASELINE" / "original_copy" / "BlackPanda" / "kicad_project"
DST = hp.OUTPUT_ROOT / "04_PROJECT" / "HybridPanda"
OLD, NEW = "BlackPanda", "HybridPanda"
SKIP = {"BlackPanda.kicad_sch-bak", "untitled.kicad_pcb", "fp-info-cache", "BlackPanda.step",
        "BlackPanda.csv", "BlackPanda2.csv", "BlackPanda2.xlsx"}
SKIP_DIRS = {".history"}

PCB_RT_SCRIPT = r"""
import sys, json, pcbnew
src, dst = sys.argv[1], sys.argv[2]
def sig(b):
    fps = sorted((f.GetReference(), f.GetFPIDAsString(), round(f.GetX()), round(f.GetY())) for f in b.GetFootprints())
    pads = sorted((f.GetReference(), p.GetNumber(), p.GetNetname()) for f in b.GetFootprints() for p in f.Pads())
    trk = sorted((t.GetClass(), t.GetNetname(), round(t.GetStart().x), round(t.GetStart().y), round(t.GetEnd().x), round(t.GetEnd().y), t.GetLayer()) for t in b.GetTracks())
    zones = sorted((z.GetNetname(), z.GetLayer(), z.GetNumCorners()) for z in b.Zones())
    return fps, pads, trk, zones
b = pcbnew.LoadBoard(src); s1 = sig(b)
pcbnew.SaveBoard(dst, b)
b2 = pcbnew.LoadBoard(dst); s2 = sig(b2)
print(json.dumps({"footprints": len(s1[0]), "pads": len(s1[1]), "tracks": len(s1[2]), "zones": len(s1[3]),
                  "nets": b.GetNetCount(), "footprints_equal": s1[0]==s2[0], "pads_equal": s1[1]==s2[1],
                  "tracks_equal": s1[2]==s2[2], "zones_equal": s1[3]==s2[3], "ok": s1==s2}))
"""


def netlist_tuples(sch: Path, out_xml: Path) -> set[tuple[str, str, str]]:
    cmd = [str(hp.KICAD_CLI), "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out_xml), str(sch)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"kicad-cli failed: {r.stderr}")
    root = ET.parse(out_xml).getroot()
    tup = set()
    for net in root.iter("net"):
        name = net.get("name")
        nodes = list(net.iter("node"))
        if len(nodes) < 2:
            name = "<single>"  # single-node nets are unnamed-equivalent
        for n in nodes:
            tup.add((n.get("ref"), n.get("pin"), name))
    return tup


def copy_project(log: hp.JsonLog) -> None:
    if DST.exists():
        log.warn("04_PROJECT/HybridPanda exists; backing up and replacing")
        stamp = hp.time.strftime("%Y%m%d_%H%M%S")
        bk = hp.BACKUP_DIR / f"{stamp}_04_PROJECT_HybridPanda"
        hp.assert_inside_output(bk)
        shutil.copytree(DST, bk)
        shutil.rmtree(DST)
    hp.assert_inside_output(DST)
    n = 0
    for p in SRC.rglob("*"):
        rel = p.relative_to(SRC)
        if any(part in SKIP_DIRS for part in rel.parts) or p.name in SKIP:
            continue
        if p.is_dir():
            continue
        new_rel = Path(*[part.replace(OLD, NEW) if i == len(rel.parts) - 1 or part.startswith(OLD + ".") else part
                         for i, part in enumerate(rel.parts)])
        dest = DST / new_rel
        hp.assert_inside_output(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        n += 1
    # rename internal references in text project files
    for f in DST.glob("HybridPanda.kicad_*"):
        t = f.read_text(encoding="utf-8")
        t2 = t.replace(f"{OLD}.kicad_sch", f"{NEW}.kicad_sch").replace(f"{OLD}.kicad_pcb", f"{NEW}.kicad_pcb") \
              .replace(f'"{OLD}.pretty', f'"{NEW}.pretty').replace(f"{OLD}.3d", f"{NEW}.3d")
        if t2 != t:
            f.write_text(t2, encoding="utf-8", newline="\n")
    for tbl in ("fp-lib-table", "sym-lib-table"):
        f = DST / tbl
        if f.exists():
            t = f.read_text(encoding="utf-8")
            t2 = t.replace(f"{OLD}.pretty", f"{NEW}.pretty").replace(f"{OLD}.kicad_sym", f"{NEW}.kicad_sym")
            f.write_text(t2, encoding="utf-8", newline="\n")
    log.info("copied project", files=n, dst=str(DST))


def roundtrip(log: hp.JsonLog) -> bool:
    sch_path = DST / "HybridPanda.kicad_sch"
    pcb_path = DST / "HybridPanda.kicad_pcb"
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # schematic
        sch = Schematic.from_file(str(sch_path))
        log.info("kiutils schematic loaded", symbols=len(sch.schematicSymbols), wires=len(sch.graphicalItems),
                 labels=len(sch.labels), version=sch.version)
        rt_sch = tdp / "rt" / "HybridPanda.kicad_sch"
        rt_sch.parent.mkdir()
        sch.to_file(str(rt_sch))
        # sym-lib-table needed next to it for resolving? kicad-cli resolves embedded lib_symbols; copy tables anyway
        for tbl in ("sym-lib-table", "fp-lib-table"):
            shutil.copy2(DST / tbl, rt_sch.parent / tbl)
        a = netlist_tuples(sch_path, tdp / "a.xml")
        b = netlist_tuples(rt_sch, tdp / "b.xml")
        only_a, only_b = sorted(a - b), sorted(b - a)
        log.info("netlist compare", tuples_original=len(a), tuples_roundtrip=len(b),
                 only_original=len(only_a), only_roundtrip=len(only_b))
        for t in only_a[:20]:
            log.error("missing after round-trip", ref=t[0], pin=t[1], net=t[2])
        for t in only_b[:20]:
            log.error("new after round-trip", ref=t[0], pin=t[1], net=t[2])
        sch_ok = not only_a and not only_b
        # pcb: kiutils 1.4.8 cannot parse KiCad 10 pad nets with empty names -> use pcbnew (KiCad embedded python)
        pcb_script = tdp / "pcb_rt.py"
        pcb_script.write_text(PCB_RT_SCRIPT, encoding="utf-8")
        r = subprocess.run([str(hp.KICAD_BIN / "python.exe"), str(pcb_script), str(pcb_path), str(tdp / "rt.kicad_pcb")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log.error("pcbnew round-trip failed", stderr=r.stderr[-800:])
            pcb_ok = False
        else:
            res = json.loads(r.stdout.strip().splitlines()[-1])
            pcb_ok = bool(res.pop("ok"))
            log.info("pcbnew board round-trip", **res, ok=pcb_ok)
    return sch_ok and pcb_ok


def main() -> int:
    ap = hp.std_argparser(__doc__)
    ap.add_argument("--no-copy", action="store_true")
    args = ap.parse_args()
    hp.apply_args(args)
    log = hp.JsonLog("step4_roundtrip")
    if not args.no_copy:
        copy_project(log)
    ok = roundtrip(log)
    log.save(roundtrip_ok=ok)
    md = [f"# STEP 4 — cópia do baseline e prova de round-trip kiutils", "",
          f"- Origem: `{SRC}`", f"- Destino: `{DST}`", f"- Resultado: **{'OK' if ok else 'FALHOU'}** (ver step4_roundtrip.json)", ""]
    md += [f"- [{e['level']}] {e['msg']} " + ", ".join(f"{k}={v}" for k, v in e.items() if k not in ('t', 'level', 'msg'))
           for e in log.events]
    hp.guarded_write_text(hp.REPORT_DIR / "step4_roundtrip.md", "\n".join(md) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
