"""corr_step5_bom.py - Step 5 BOM impact: C23/C24 15pF -> 18pF (SI/PI item 24).

Edits 06_REPORTS/bom_real/BOM_HYBRIDPANDA_v1.csv and BOM_JLCPCB.csv, then regenerates 06_REPORTS/hybrid_BOM.csv
with the same kicad-cli command used by corr_step4_bom.py / step7_validate.py (schematic properties were already
changed by corr_step5_sch.py). Usage: python -u corr_step5_bom.py [--dry]  (system python is enough)
"""
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp  # noqa: E402

ROOT = hp.OUTPUT_ROOT
V1 = ROOT / "06_REPORTS" / "bom_real" / "BOM_HYBRIDPANDA_v1.csv"
JLC = ROOT / "06_REPORTS" / "bom_real" / "BOM_JLCPCB.csv"
HYB = ROOT / "06_REPORTS" / "hybrid_BOM.csv"
SCH = ROOT / "04_PROJECT" / "HybridPanda" / "HybridPanda.kicad_sch"

EDIT = {
    "C23,C24": {
        "Value": "18pF", "MPN": "0402CG180J500NT", "Manufacturer": "Fenghua", "LCSC": "C1555",
        "JLC_Type": "Basic (a verificar)", "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "",
        "Mouser_DigiKey_PN": "Mouser/DK: Murata GRM1555C1H180JA01D by MPN (SKU nao verificado)",
        "Datasheet": "https://www.lcsc.com/product-detail/C1555.html",
        "Alt_MPN": "CL05C180JB5NNNC (Samsung)", "Alt_LCSC": "C307443",
        "Status": "TO-VERIFY",
        "Notes": "Passo 5 (SI/PI item 24): 15pF -> 18pF. C0G 50V 5%. Y1 CL=12pF: CL_eff=(18||18)+Cstray(~3pF)=12pF. "
                 "LCSC C1555 nao confirmado na base jlcparts (pesquisa web); confirmar frequencia no prototipo (alvo +-10 ppm).",
    },
}


def rewrite(path, fn, tag):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        header, rows = rd.fieldnames, list(rd)
    n = fn(rows)
    hp.backup_before_write(path, tag)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
    return n


def main():
    dry = "--dry" in sys.argv

    def edit_v1(rows):
        n = 0
        for r in rows:
            if r["Reference"] in EDIT:
                r.update(EDIT[r["Reference"]]); n += 1
        return n

    def edit_jlc(rows):
        n = 0
        for r in rows:
            if r["Designator"] in EDIT:
                r["Comment"] = EDIT[r["Designator"]]["MPN"]; r["LCSC Part #"] = EDIT[r["Designator"]]["LCSC"]; n += 1
        return n

    if dry:
        print("dry run"); return
    print("v1 rows edited:", rewrite(V1, edit_v1, "step5_bom"))
    print("jlc rows edited:", rewrite(JLC, edit_jlc, "step5_bom"))
    hp.backup_before_write(HYB, "step5_bom")
    p = subprocess.run([str(hp.KICAD_CLI), "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${QUANTITY},${DNP},MPN,Manufacturer,Datasheet",
                        "--labels", "Reference,Value,Footprint,Qty,DNP,MPN,Manufacturer,Datasheet", "--group-by", "Value,Footprint,MPN",
                        "--exclude-dnp", "-o", str(HYB), str(SCH)], capture_output=True, text=True)
    print("hybrid_BOM.csv regenerated, exit", p.returncode)


if __name__ == "__main__":
    main()
