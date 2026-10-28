"""corr_step4_bom.py - Step 4: propagate the BOM impact of correction steps 1-3.

  1. rewrites hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv (line split / new lines / footprint fixes, see DELTA)
  2. regenerates hardware/reports/bom-real/BOM_JLCPCB.csv (Comment,Designator,Footprint,LCSC Part #) from the v1 file
  3. writes MPN / Manufacturer / LCSC properties into every schematic symbol listed in the v1 file (hidden fields)
     and fixes the D10 datasheet URL (was onsemi MBR1020)
  4. regenerates hardware/reports/hybrid_BOM.csv with the same kicad-cli command step7_validate.py uses
Usage: python -u corr_step4_bom.py [--dry]
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hp_common as hp  # noqa: E402
from kiutils.schematic import Schematic  # noqa: E402
from kiutils.items.common import Position, Effects, Font, Property  # noqa: E402

ROOT = hp.OUTPUT_ROOT
SCH = ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_sch"
V1 = ROOT / "hardware/reports" / "bom-real" / "BOM_HYBRIDPANDA_v1.csv"
JLC = ROOT / "hardware/reports" / "bom-real" / "BOM_JLCPCB.csv"
HYB = ROOT / "hardware/reports" / "hybrid_BOM.csv"
REPORT = ROOT / "hardware/reports" / "corrections" / "step4_bom.json"
CLI = str(hp.KICAD_CLI)

DS_D10 = "https://assets.nexperia.com/documents/data-sheet/BAS70H.pdf"

# --------------------------------------------------------------------------- BOM delta (steps 1-3)
# ref-field -> replacement row dict (only keys given are changed); None = delete the line
DELTA_EDIT = {
    "C4,C6,C7,C12": {"Reference": "C6,C7", "Qty": "2",
                     "Notes": "Passo 3 item 6: C4/C12 passaram a 10uF (linha propria). C6/C7 mantem 2.2uF 50V X7R. 50V X7R = >2x da tensao clampada (SMAJ16CA Vc~26V)."},
    "R1,R2": {"Reference": "R2", "Qty": "1", "Notes": "1% 1/16W. R1 saiu desta linha no passo 3 (item 4: 10k R_0603)."},
    "R6": {"Footprint": "Resistor_SMD:R_0603_1608Metric", "Function": "resistor 1% 0603",
           "Status": "OK", "Notes": "Passo 1 (footprint audit): footprint corrigido de C_0603 para R_0603 no esquema e no PCB. Valor 3.16k com 10k da 5.08V (TPS5450 Vref 1.221V)."},
    "C60-C62": {"Reference": "C60-C62,C65", "Qty": "4",
                "Net_VoltageClass": "+3V3 (C60-C62) / +3V3 em VDDSMPS U7.16 (C65)",
                "Notes": "16V X5R. C65 adicionado no passo 2 (SI/PI item 3: 4.7uF junto ao VDDSMPS, pino 16 do U7)."},
    "D10": {"Notes": "Datasheet do hybrid_BOM (onsemi MBR1020) estava errado; corrigido no esquema (passo 4). SI/PI item 9 (funcao do D10: Schottky 1 A ou DNP) DEFERIDO - decisao de sistema, ver hardware/reports/correcoes-aplicadas.md."},
}
DS_LCSC = "https://www.lcsc.com/product-detail/%s.html"
DELTA_NEW = [
    {"Reference": "C4,C12", "Qty": "2", "Value": "10uF", "Footprint": "Capacitor_SMD:C_0805_2012Metric",
     "Net_VoltageClass": "12V_Protected (entrada TPS5450, apos P-FET e TVS 16V)", "Function": "Cin TPS5450 (SI/PI item 6)",
     "MPN": "CL21A106KBYQNNE", "Manufacturer": "Samsung", "Package": "0805", "LCSC": "C2932476", "JLC_Type": "Extended (a verificar)",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "Mouser/DK: Murata GRM21BR61H106KE43 (10uF 50V X5R 0805) by MPN (SKU nao verificado)",
     "Datasheet": "https://www.samsungsem.com/global/support/product-search/mlcc/CL21A106KBYQNNE.do", "AEC": "",
     "Alt_MPN": "GRM21BR61H106KE43 (Murata, 50V X5R 0805)", "Alt_LCSC": "", "Status": "TO-VERIFY",
     "Notes": "Passo 3 item 6: 2.2uF -> 10uF para Cin do TPS5450. 1206 nao cabe em x=113.635 (L4/C6), mantido 0805 -> 10uF 50V so existe em X5R (derating em 12-14V: ~5-6uF efetivo cada, 2 pcs + C6/C7). LCSC C2932476 obtido por busca web - confirmar numero e estoque antes de encomendar."},
    {"Reference": "R1", "Qty": "1", "Value": "10k", "Footprint": "Resistor_SMD:R_0603_1608Metric",
     "Net_VoltageClass": "gate Q4 (12V_Protected - Net-(D15-A))", "Function": "pull-down gate P-FET (SI/PI item 4)",
     "MPN": "0603WAF1002T5E", "Manufacturer": "Uniroyal", "Package": "0603", "LCSC": "C25804", "JLC_Type": "Basic",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "Mouser/DK: Yageo RC0603FR-0710KL (SKU nao verificado)",
     "Datasheet": DS_LCSC % "C25804", "AEC": "", "Alt_MPN": "RC0603FR-0710KL", "Alt_LCSC": "", "Status": "OK",
     "Notes": "Passo 3 item 4: 1k 0402 -> 10k 0603 (dissipacao e Vgs do Q4 com D15). LCSC C25804 e parte Basic classica da JLC (confirmar estoque)."},
    {"Reference": "C64", "Qty": "1", "Value": "2.2uF", "Footprint": "Capacitor_SMD:C_0402_1005Metric",
     "Net_VoltageClass": "VCAP (~1.2V) junto a U7.103", "Function": "decoupling VCAP (SI/PI item 2)",
     "MPN": "CL05A225MP5NSNC", "Manufacturer": "Samsung", "Package": "0402", "LCSC": "C23733", "JLC_Type": "Basic (a verificar)",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "Mouser/DK: by MPN CL05A225MP5NSNC (SKU nao verificado)",
     "Datasheet": "https://www.samsungsem.com/resources/file/global/support/product/ds/mlcc/CL05A225MP5NSNC.pdf", "AEC": "",
     "Alt_MPN": "CL05A225KP5NSNC", "Alt_LCSC": "", "Status": "TO-VERIFY",
     "Notes": "Passo 2 (SI/PI item 2): o item propunha 0603; no PCB so coube 0402 em (116.1,44.5) B.Cu. 10V X5R a 1.2V: sem derating relevante; ESR MLCC < 100 mohm OK (DS13311 6.3)."},
    {"Reference": "D15", "Qty": "1", "Value": "BZT52C12", "Footprint": "Diode_SMD:D_SOD-123",
     "Net_VoltageClass": "12V_Protected (K) - gate Q4 (A)", "Function": "zener 12V limita Vgs do Q4 (SI/PI item 5)",
     "MPN": "BZT52C12", "Manufacturer": "High Diode (ou equivalente)", "Package": "SOD-123", "LCSC": "C571379", "JLC_Type": "Basic (a verificar)",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "Mouser/DK: Diodes BZT52C12-7-F / Nexperia BZT52H-C12 by MPN (SKU nao verificado)",
     "Datasheet": DS_LCSC % "C571379", "AEC": "", "Alt_MPN": "BZT52C12-7-F (Diodes)", "Alt_LCSC": "", "Status": "TO-VERIFY",
     "Notes": "Passo 3 item 5. Qualquer BZT52C12 SOD-123 (12V 500mW) serve. LCSC C571379 obtido por busca web - confirmar."},
    {"Reference": "U13", "Qty": "1", "Value": "USBLC6-2SC6", "Footprint": "Package_TO_SOT_SMD:SOT-23-6",
     "Net_VoltageClass": "USB_PWR (5V) / USB_R_D+ / USB_R_D-", "Function": "ESD array USB 2.0 (SI/PI item 8)",
     "MPN": "USBLC6-2SC6", "Manufacturer": "STMicroelectronics", "Package": "SOT-23-6", "LCSC": "C7519", "JLC_Type": "Extended",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "Mouser 511-USBLC6-2SC6 / DK 497-5235-1-ND (SKU nao verificado)",
     "Datasheet": "https://www.st.com/resource/en/datasheet/usblc6-2sc6.pdf", "AEC": "",
     "Alt_MPN": "USBLC6-2SC6Y (AEC-Q101)", "Alt_LCSC": "", "Status": "OK",
     "Notes": "Passo 3 item 8. Flow-through: pinos 1/3 lado conector (U3), pinos 6/4 lado MCU (R20/R21). LCSC C7519 confirmado (lcsc.com/product-detail/C7519.html)."},
    {"Reference": "JP1", "Qty": "1", "Value": "HW_ID1", "Footprint": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm",
     "Net_VoltageClass": "+3V3 / PF9", "Function": "solder jumper HW_ID (passo 2, PCR-1)",
     "MPN": "", "Manufacturer": "", "Package": "solder jumper (so cobre)", "LCSC": "", "JLC_Type": "N/A",
     "JLC_Stock_2026-10-27": "", "JLC_Price10_USD": "", "Mouser_DigiKey_PN": "", "Datasheet": "", "AEC": "",
     "Alt_MPN": "", "Alt_LCSC": "", "Status": "NO-PART",
     "Notes": "Sem componente: jumper de solda aberto no PCB (fechar com estanho para HW_ID). Nao entra na BOM JLC."},
]

JLC_SKIP = {"JP1"}


def expand_refs(field):
    out = []
    for x in [x.strip() for x in field.split(",") if x.strip()]:
        m = re.fullmatch(r"([A-Za-z_]+)(\d+)-([A-Za-z_]+)?(\d+)", x)
        if m and (m.group(3) in (None, m.group(1))):
            out += ["%s%d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(4)) + 1)]
        else:
            out.append(x)
    return out


def write_csv(path, header, rows):
    hp.backup_before_write(path, "step4_bom")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


def sort_key(ref_field):
    first = expand_refs(ref_field)[0]
    m = re.match(r"([A-Za-z_]+)(\d+)", first)
    return (m.group(1), int(m.group(2))) if m else (first, 0)


def main():
    dry = "--dry" in sys.argv
    with open(V1, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        header = rd.fieldnames
        rows = list(rd)
    log = {"edited": [], "added": [], "deleted": []}
    for r in rows:
        key = r["Reference"]
        if key in DELTA_EDIT:
            ed = DELTA_EDIT[key]
            if ed is None:
                log["deleted"].append(key); r["_del"] = True; continue
            r.update(ed); log["edited"].append(key)
    rows = [r for r in rows if not r.get("_del")]
    existing = {x for r in rows for x in expand_refs(r["Reference"])}
    for n in DELTA_NEW:
        if any(x in existing for x in expand_refs(n["Reference"])):
            raise SystemExit("ref already present: " + n["Reference"])
        rows.append(n); log["added"].append(n["Reference"])
    rows.sort(key=lambda r: sort_key(r["Reference"]))
    # ---- JLC csv
    jlc_rows = []
    for r in rows:
        if any(x in JLC_SKIP for x in expand_refs(r["Reference"])) or not r.get("MPN"):
            continue
        jlc_rows.append({"Comment": r["MPN"], "Designator": r["Reference"], "Footprint": r["Footprint"].split(":")[-1], "LCSC Part #": r.get("LCSC", "") if r.get("LCSC", "").startswith("C") else ""})
    # ---- schematic properties
    per_ref = {}
    for r in rows:
        for x in expand_refs(r["Reference"]):
            per_ref[x] = r
    sch = Schematic.from_file(str(SCH))
    touched = 0
    for s in sch.schematicSymbols:
        ref = next((p.value for p in s.properties if p.key == "Reference"), "")
        if ref not in per_ref:
            continue
        r = per_ref[ref]
        vals = {"MPN": r.get("MPN", ""), "Manufacturer": r.get("Manufacturer", ""),
                "LCSC": r.get("LCSC", "") if r.get("LCSC", "").startswith("C") and " " not in r.get("LCSC", "") else ""}
        for key, val in vals.items():
            if not val:
                continue
            p = next((p for p in s.properties if p.key == key), None)
            if p is None:
                s.properties.append(Property(key=key, value=val, position=Position(s.position.X, s.position.Y, 0),
                                             effects=Effects(font=Font(height=1.27, width=1.27), hide=True)))
            else:
                p.value = val
        if ref == "D10":
            p = next((p for p in s.properties if p.key == "Datasheet"), None)
            if p is not None:
                p.value = DS_D10
        touched += 1
    log["symbols_with_mpn"] = touched
    print(json.dumps(log, indent=1))
    if dry:
        return
    write_csv(V1, header, rows)
    write_csv(JLC, ["Comment", "Designator", "Footprint", "LCSC Part #"], jlc_rows)
    hp.backup_before_write(SCH, "step4_bom")
    sch.to_file(str(SCH))
    hp.backup_before_write(HYB, "step4_bom")
    p = subprocess.run([CLI, "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${QUANTITY},${DNP},MPN,Manufacturer,Datasheet",
                        "--labels", "Reference,Value,Footprint,Qty,DNP,MPN,Manufacturer,Datasheet", "--group-by", "Value,Footprint,MPN",
                        "--exclude-dnp", "-o", str(HYB), str(SCH)], capture_output=True, text=True)
    log["kicad_cli_bom_exit"] = p.returncode
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print("written:", V1.name, JLC.name, HYB.name, "exit", p.returncode)


if __name__ == "__main__":
    main()
