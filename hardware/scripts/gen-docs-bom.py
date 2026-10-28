#!/usr/bin/env python3
"""Gera docs/hardware/bom.csv a partir do esquema e da PCB do Hybrid Panda.

Autor: Bruno Costa

Le `hardware/hybrid-panda/HybridPanda.kicad_sch` (propriedades Reference, Value,
Footprint, Datasheet, MPN, Manufacturer, LCSC, flags dnp/in_bom) e
`hardware/hybrid-panda/HybridPanda.kicad_pcb` (lado de montagem por referencia) e
escreve uma linha por referencia em `docs/hardware/bom.csv` (LF, UTF-8).

Nao depende de kiutils nem do KiCad: usa um parser minimo de S-expressions.
Simbolos de alimentacao (#PWR, #FLG) sao ignorados. Fiduciais existem apenas na
PCB e sao listados com `source=pcb-only`.

A coluna `lcsc_status` vale `assigned` quando o simbolo tem a propriedade LCSC
preenchida e `not assigned` caso contrario. Nenhum codigo LCSC foi confirmado no
catalogo do fabricante; a coluna `catalog_confirmed` e sempre `no` ate que essa
verificacao seja feita e registada em `hardware/reports/bom-real/`.

Uso:
    python hardware/scripts/gen-docs-bom.py [--out docs/hardware/bom.csv]
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCH = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_sch"
PCB = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_pcb"
OUT = ROOT / "docs" / "hardware" / "bom.csv"

COLUMNS = [
    "reference",
    "value",
    "footprint",
    "mpn",
    "manufacturer",
    "lcsc",
    "lcsc_status",
    "catalog_confirmed",
    "side",
    "dnp",
    "datasheet",
    "lib_id",
    "source",
]


def tokenize(text: str):
    """Tokenizer minimo de S-expression (parenteses, strings, atomos)."""
    for m in re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text):
        tok = m.group(0)
        if tok.startswith('"'):
            yield ("str", tok[1:-1].replace('\\"', '"'))
        else:
            yield ("atom", tok)


def parse(text: str):
    stack = [[]]
    for kind, tok in tokenize(text):
        if kind == "atom" and tok == "(":
            stack.append([])
        elif kind == "atom" and tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    return stack[0]


def children(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            yield c


def first(node, name, default=None):
    for c in children(node, name):
        return c
    return default


def natural_key(ref: str):
    m = re.match(r"([A-Za-z#]+)(\d*)", ref)
    if not m:
        return (ref, 0)
    return (m.group(1), int(m.group(2) or 0))


def read_schematic(path: Path):
    root = parse(path.read_text(encoding="utf-8"))
    sch = next(n for n in root if isinstance(n, list) and n[0] == "kicad_sch")
    rows = {}
    for sym in children(sch, "symbol"):
        props = {}
        for p in children(sym, "property"):
            if len(p) >= 3:
                props[p[1]] = p[2]
        ref = props.get("Reference", "")
        if not ref or ref.startswith("#"):
            continue
        lib_id = first(sym, "lib_id", [None, ""])[1]
        dnp = first(sym, "dnp", [None, "no"])[1]
        in_bom = first(sym, "in_bom", [None, "yes"])[1]
        if in_bom == "no":
            continue
        rows[ref] = {
            "reference": ref,
            "value": props.get("Value", ""),
            "footprint": props.get("Footprint", ""),
            "mpn": props.get("MPN", ""),
            "manufacturer": props.get("Manufacturer", props.get("MANUFACTURER", "")),
            "lcsc": props.get("LCSC", ""),
            "dnp": "yes" if dnp == "yes" else "no",
            "datasheet": props.get("Datasheet", ""),
            "lib_id": lib_id,
            "source": "schematic",
        }
    return rows


def read_pcb_sides(path: Path):
    root = parse(path.read_text(encoding="utf-8"))
    pcb = next(n for n in root if isinstance(n, list) and n[0] == "kicad_pcb")
    sides = {}
    fps = {}
    for fp in children(pcb, "footprint"):
        layer = first(fp, "layer", [None, ""])[1]
        ref = ""
        for p in children(fp, "property"):
            if len(p) >= 3 and p[1] == "Reference":
                ref = p[2]
        if not ref:
            continue
        sides[ref] = "top" if layer == "F.Cu" else "bottom" if layer == "B.Cu" else layer
        fps[ref] = fp[1] if len(fp) > 1 and isinstance(fp[1], str) else ""
    return sides, fps


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)

    rows = read_schematic(SCH)
    sides, pcb_fps = read_pcb_sides(PCB)

    for ref, fpname in pcb_fps.items():
        if ref not in rows:
            rows[ref] = {
                "reference": ref,
                "value": "",
                "footprint": fpname,
                "mpn": "",
                "manufacturer": "",
                "lcsc": "",
                "dnp": "no",
                "datasheet": "",
                "lib_id": "",
                "source": "pcb-only",
            }

    out_rows = []
    for ref in sorted(rows, key=natural_key):
        r = dict(rows[ref])
        r["side"] = sides.get(ref, "not placed")
        r["lcsc_status"] = "assigned" if r["lcsc"] else "not assigned"
        r["catalog_confirmed"] = "no"
        out_rows.append({k: r.get(k, "") for k in COLUMNS})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    sch_refs = [r for r in out_rows if r["source"] == "schematic"]
    with_lcsc = sum(1 for r in sch_refs if r["lcsc"])
    with_mpn = sum(1 for r in sch_refs if r["mpn"])
    print(f"wrote {args.out.relative_to(ROOT)}: {len(out_rows)} rows "
          f"({len(sch_refs)} schematic refs, {len(out_rows) - len(sch_refs)} pcb-only)")
    print(f"schematic refs with MPN: {with_mpn}/{len(sch_refs)}; "
          f"with LCSC: {with_lcsc}/{len(sch_refs)}")
    print("without LCSC:", ", ".join(r["reference"] for r in sch_refs if not r["lcsc"]) or "-")
    print("without MPN:", ", ".join(r["reference"] for r in sch_refs if not r["mpn"]) or "-")
    return 0


if __name__ == "__main__":
    sys.exit(main())
