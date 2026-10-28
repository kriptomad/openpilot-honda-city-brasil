"""step7_validate.py - STEP 7 (protocolo v3): validação automatizada com logs reais.

Executa (python do KiCad 10: ...\KiCad\10.0\bin\python.exe):
  1. kicad-cli sch erc (JSON)  -> hardware\\reports\hybrid_ERC_step7.json
  2. kicad-cli pcb drc (JSON)  -> hardware\\reports\hybrid_DRC_step7.json   (comparado com baseline_DRC.json)
  3. netlist esquemático (kicadxml) x PCB (pcbnew): pad->rede, footprints, valores
  4. BOM (hardware\\reports\hybrid_BOM.csv) x esquemático x PCB
  5. parity_check.py --profile red_h7 (subprocesso, python da .venv)
  6. Make-Manifest.ps1 -Step STEP7 -Original (subprocesso)
Saídas: hardware\\reports\step7_validation.json, hardware\\research\step7-validacao.md. Nada fora de OUTPUT_ROOT.
Código de saída 0 mesmo com falhas (as falhas ficam registadas — protocolo: "o que persistir fica como falha").
"""
import csv, json, os, subprocess, sys, time, collections, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew

ROOT = str(hp.OUTPUT_ROOT)
PROJ = os.path.join(ROOT, "hardware", "hybrid-panda")
SCH = os.path.join(PROJ, "HybridPanda.kicad_sch")
PCB = os.path.join(PROJ, "HybridPanda.kicad_pcb")
REP = os.path.join(ROOT, "hardware/reports")
CLI = str(hp.KICAD_CLI)
VENV_PY = os.path.join(ROOT, "hardware/scripts", ".venv", "Scripts", "python.exe")
T0 = time.time()
out = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "commands": [], "failures": [], "notes": []}

def run(cmd, log_name=None, env=None):
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
    rec = {"cmd": cmd if isinstance(cmd, str) else subprocess.list2cmdline(cmd), "exit": p.returncode, "seconds": round(time.time() - t, 1)}
    if log_name:
        hp.assert_inside_output(os.path.join(REP, log_name))
        with open(os.path.join(REP, log_name), "w", encoding="utf-8") as f: f.write(p.stdout + "\n--- stderr ---\n" + p.stderr)
        rec["log"] = log_name
    out["commands"].append(rec); print("$", rec["cmd"][:120], "->", p.returncode)
    return p

# ---------------------------------------------------------------- 1. ERC
erc_json = os.path.join(REP, "hybrid_ERC_step7.json")
run([CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", erc_json, SCH], "step7_erc.log")
erc = json.load(open(erc_json, encoding="utf-8"))
erc_v = [v for s in erc.get("sheets", []) for v in s.get("violations", [])]
erc_c = collections.Counter((v["severity"], v["type"]) for v in erc_v)
out["erc"] = {"errors": sum(1 for v in erc_v if v["severity"] == "error"), "warnings": sum(1 for v in erc_v if v["severity"] == "warning"),
              "by_type": {"%s/%s" % k: n for k, n in sorted(erc_c.items())},
              "error_items": [(v["type"], v["description"][:120]) for v in erc_v if v["severity"] == "error"]}
if out["erc"]["errors"]: out["failures"].append("ERC: %d erro(s)" % out["erc"]["errors"])

# ---------------------------------------------------------------- 2. DRC
drc_json = os.path.join(REP, "hybrid_DRC_step7.json")
run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", drc_json, PCB], "step7_drc.log")
drc = json.load(open(drc_json, encoding="utf-8"))
base = json.load(open(os.path.join(REP, "baseline_DRC.json"), encoding="utf-8"))
def by_type(d): return collections.Counter(v["type"] for v in d.get("violations", []))
hc, bc = by_type(drc), by_type(base)
def sig(v): return (v["type"], tuple(sorted(i["description"] for i in v["items"])))
base_sigs = set(sig(v) for v in base.get("violations", []))
new_v = [v for v in drc.get("violations", []) if sig(v) not in base_sigs]
out["drc"] = {"unconnected_items": len(drc.get("unconnected_items", [])),
              "unconnected_list": [" <> ".join(i["description"] for i in u["items"]) for u in drc.get("unconnected_items", [])],
              "violations_total": len(drc.get("violations", [])), "baseline_total": len(base.get("violations", [])),
              "by_type": {t: {"hibrida": hc.get(t, 0), "baseline": bc.get(t, 0)} for t in sorted(set(hc) | set(bc))},
              "new_vs_baseline": [{"type": v["type"], "severity": v["severity"], "desc": v["description"][:100],
                                   "items": [i["description"] for i in v["items"]]} for v in new_v],
              "clearance": hc.get("clearance", 0), "shorting_items": hc.get("shorting_items", 0),
              "courtyards_overlap": hc.get("courtyards_overlap", 0), "track_width": hc.get("track_width", 0)}
if out["drc"]["unconnected_items"]: out["failures"].append("DRC: %d item(ns) não ligado(s)" % out["drc"]["unconnected_items"])
if out["drc"]["clearance"] or out["drc"]["shorting_items"]: out["failures"].append("DRC: clearance %d / curtos %d" % (out["drc"]["clearance"], out["drc"]["shorting_items"]))
if out["drc"]["courtyards_overlap"]:
    out["notes"].append("courtyards_overlap %d — herdado do baseline (D7/U9), ver hardware\\research\\step5-layout-h725.md §7.3" % out["drc"]["courtyards_overlap"])
    if bc.get("courtyards_overlap", 0) < out["drc"]["courtyards_overlap"]: out["failures"].append("DRC: courtyards_overlap novo")

# ---------------------------------------------------------------- 3. netlist sch x pcb
net_xml = os.path.join(REP, "hybrid_HybridPanda_netlist.xml")
run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", net_xml, SCH], "step7_netlist.log")
tree = ET.parse(net_xml); rootx = tree.getroot()
sch_comp = {}
for c in rootx.iter("comp"):
    sch_comp[c.get("ref")] = {"value": (c.findtext("value") or "").strip(), "footprint": (c.findtext("footprint") or "").strip()}
sch_pin_net = {}
for n in rootx.iter("net"):
    name = n.get("name")
    for node in n.iter("node"): sch_pin_net[(node.get("ref"), node.get("pin"))] = name
board = pcbnew.LoadBoard(PCB)
pcb_comp, pcb_pin_net = {}, {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if fp.GetAttributes() & pcbnew.FP_BOARD_ONLY: continue  # fiduciais etc.: só PCB, sem símbolo no esquemático
    pcb_comp[ref] = {"value": fp.GetValue(), "footprint": str(fp.GetFPID().GetUniStringLibId())}
    for p in fp.Pads():
        if p.GetNumber() == "": continue
        pcb_pin_net[(ref, p.GetNumber())] = p.GetNetname()
def norm(n):
    # KiCad netlist XML usa "Net-(C1-Pad1)"/"unconnected-(...)"; o PCB usa os mesmos nomes; "" no PCB = sem rede
    return "" if (n is None or n.startswith("unconnected-")) else n
only_sch = sorted(set(sch_comp) - set(pcb_comp)); only_pcb = sorted(set(pcb_comp) - set(sch_comp))
val_diff = [(r, sch_comp[r]["value"], pcb_comp[r]["value"]) for r in sorted(set(sch_comp) & set(pcb_comp)) if sch_comp[r]["value"] != pcb_comp[r]["value"]]
fp_diff = [(r, sch_comp[r]["footprint"], pcb_comp[r]["footprint"]) for r in sorted(set(sch_comp) & set(pcb_comp)) if sch_comp[r]["footprint"] != pcb_comp[r]["footprint"]]
net_diff = []
for k in sorted(set(sch_pin_net) | set(pcb_pin_net)):
    a, b = norm(sch_pin_net.get(k)), norm(pcb_pin_net.get(k))
    if k not in pcb_pin_net:
        # pads que existem no símbolo mas não no footprint (ex.: pinos NC do símbolo) — registar separadamente
        net_diff.append({"ref": k[0], "pin": k[1], "sch": a, "pcb": None, "kind": "pino sem pad no PCB"}); continue
    if k not in sch_pin_net:
        net_diff.append({"ref": k[0], "pin": k[1], "sch": None, "pcb": b, "kind": "pad sem pino no esquemático"}); continue
    if a != b: net_diff.append({"ref": k[0], "pin": k[1], "sch": a, "pcb": b, "kind": "rede divergente"})
real_div = [d for d in net_diff if d["kind"] == "rede divergente"]
out["netlist"] = {"sch_components": len(sch_comp), "pcb_footprints": len(pcb_comp), "only_in_sch": only_sch, "only_in_pcb": only_pcb,
                  "value_diff": val_diff, "footprint_diff": fp_diff, "pads_compared": len(set(sch_pin_net) & set(pcb_pin_net)),
                  "net_divergences": real_div, "other_pin_pad_notes": [d for d in net_diff if d["kind"] != "rede divergente"][:50],
                  "other_pin_pad_notes_count": sum(1 for d in net_diff if d["kind"] != "rede divergente")}
if only_sch or only_pcb or real_div or fp_diff: out["failures"].append("Netlist sch x pcb: só_sch %d / só_pcb %d / redes %d / footprints %d" % (len(only_sch), len(only_pcb), len(real_div), len(fp_diff)))

# ---------------------------------------------------------------- 4. BOM x sch x pcb
bom_csv = os.path.join(REP, "hybrid_BOM.csv")
run([CLI, "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${QUANTITY},${DNP},MPN,Manufacturer,Datasheet",
     "--labels", "Reference,Value,Footprint,Qty,DNP,MPN,Manufacturer,Datasheet", "--group-by", "Value,Footprint,MPN", "--exclude-dnp", "-o", bom_csv, SCH], "step7_bom.log")
def expand_refs(field):
    """'C1,C16-C21,U8-U11' -> ['C1','C16',...,'C21','U8',...,'U11'] (o --group-by do kicad-cli comprime intervalos)."""
    import re
    out = []
    for x in [x.strip() for x in field.split(",") if x.strip()]:
        m = re.fullmatch(r"([A-Za-z_]+)(\d+)-([A-Za-z_]+)?(\d+)", x)
        if m and (m.group(3) in (None, m.group(1))):
            out += ["%s%d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(4)) + 1)]
        else: out.append(x)
    return out
bom_refs = {}
with open(bom_csv, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        for r in expand_refs(row.get("Reference", "")):
            bom_refs[r] = {"value": row.get("Value", "").strip(), "footprint": row.get("Footprint", "").strip(), "mpn": row.get("MPN", "").strip()}
dnp_sch = [c.get("ref") for c in rootx.iter("comp") if any(p.get("name") == "dnp" for p in c.iter("property"))]
bom_only = sorted(set(bom_refs) - set(sch_comp)); sch_only = sorted(set(sch_comp) - set(bom_refs) - set(dnp_sch))
bom_val = [(r, bom_refs[r]["value"], sch_comp[r]["value"]) for r in sorted(set(bom_refs) & set(sch_comp)) if bom_refs[r]["value"] != sch_comp[r]["value"]]
bom_pcb = [(r, bom_refs[r]["footprint"], pcb_comp[r]["footprint"]) for r in sorted(set(bom_refs) & set(pcb_comp)) if bom_refs[r]["footprint"] != pcb_comp[r]["footprint"]]
no_mpn = sorted(r for r in bom_refs if not bom_refs[r]["mpn"])
out["bom"] = {"lines_refs": len(bom_refs), "dnp_in_sch": dnp_sch, "only_in_bom": bom_only, "sch_not_in_bom": sch_only,
              "value_diff_bom_sch": bom_val, "footprint_diff_bom_pcb": bom_pcb, "refs_without_MPN": no_mpn}
if bom_only or sch_only or bom_val or bom_pcb: out["failures"].append("BOM x sch x pcb inconsistente")
if no_mpn: out["notes"].append("%d referências sem MPN na BOM (PROVISÓRIO — ver STEP4/R3v2)" % len(no_mpn))

# ---------------------------------------------------------------- 5. paridade firmware x hardware
pyexe = VENV_PY if os.path.exists(VENV_PY) else sys.executable
p = run([pyexe, os.path.join(ROOT, "hardware/scripts", "parity_check.py"), "--netlist", net_xml, "--profile", "red_h7"], "step7_parity.log")
par_md = os.path.join(REP, "parity-red-h7-hybrid-hybridpanda-netlist.md")
par_json = os.path.join(REP, "parity_red_h7_hybrid_HybridPanda_netlist.json")
par = json.load(open(par_json, encoding="utf-8")).get("summary", {}) if os.path.exists(par_json) else {}
rows = par.get("rows", [])
out["parity"] = {"exit": p.returncode, "result": par.get("result"), "status_counts": par.get("counts", {}), "report_md": os.path.relpath(par_md, ROOT),
                 "conflicts": [r for r in rows if r.get("status") in ("DIVERGENTE", "NAO_CONECTADO", "PINO_INEXISTENTE") and not r.get("optional")],
                 "optional_not_ok": [r for r in rows if r.get("status") not in ("OK", "SEM_USO") and r.get("optional")]}
if p.returncode != 0 or out["parity"]["conflicts"]: out["failures"].append("PIN_PARITY_CONFLICT: %d" % len(out["parity"]["conflicts"]))

# ---------------------------------------------------------------- 6. manifestos
# o python do KiCad altera PSModulePath e o powershell perde Get-FileHash -> limpar a variável para o subprocesso
_env = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEPATH"}
p = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(ROOT, "hardware/scripts", "Make-Manifest.ps1"), "-Step", "STEP7", "-Original"], "step7_manifest.log", env=_env)
out["manifests"] = {"exit": p.returncode, "tail": p.stdout.strip().splitlines()[-6:]}
if p.returncode != 0: out["failures"].append("Make-Manifest falhou")

# ---------------------------------------------------------------- relatório
out["seconds"] = round(time.time() - T0, 1)
hp.assert_inside_output(os.path.join(REP, "step7_validation.json"))
with open(os.path.join(REP, "step7_validation.json"), "w", encoding="utf-8") as f: json.dump(out, f, indent=1, ensure_ascii=False, default=str)

L = ["# STEP 7 — Validação automatizada (logs reais em `hardware/reports`)", "", "Data: %s. Gerado por `hardware\\scripts\\step7_validate.py` (%.0f s)." % (out["date"], out["seconds"]), ""]
L += ["## Resumo", ""]
L += ["- **Falhas persistentes**: %s" % ("nenhuma" if not out["failures"] else "; ".join(out["failures"]))]
for n in out["notes"]: L.append("- Nota: " + n)
L += ["", "## 1. ERC (`hybrid_ERC_step7.json`)", "", "- Erros: **%d** · Avisos: %d" % (out["erc"]["errors"], out["erc"]["warnings"])]
for k, n in out["erc"]["by_type"].items(): L.append("  - %s: %d" % (k, n))
L += ["", "## 2. DRC (`hybrid_DRC_step7.json`) vs baseline (`baseline_DRC.json`)", "",
      "- Itens não ligados: **%d** · clearance: **%d** · curtos: **%d** · courtyards_overlap: %d (baseline %d) · track_width: %d" %
      (out["drc"]["unconnected_items"], out["drc"]["clearance"], out["drc"]["shorting_items"], out["drc"]["courtyards_overlap"], bc.get("courtyards_overlap", 0), out["drc"]["track_width"]), "",
      "| Tipo | Híbrida | Baseline |", "|---|---|---|"]
for t, d in out["drc"]["by_type"].items(): L.append("| %s | %d | %d |" % (t, d["hibrida"], d["baseline"]))
L += ["", "Violações cuja assinatura (tipo + itens) **não existe no baseline**: %d" % len(out["drc"]["new_vs_baseline"])]
for v in out["drc"]["new_vs_baseline"][:60]: L.append("- %s [%s]: %s — %s" % (v["type"], v["severity"], v["desc"], " <> ".join(v["items"])))
if len(out["drc"]["new_vs_baseline"]) > 60: L.append("- … (+%d, ver JSON)" % (len(out["drc"]["new_vs_baseline"]) - 60))
L += ["", "Nota: quase todas as 'novas' são do mesmo tipo das herdadas (text_height/lib_footprint_mismatch/silk) com itens renomeados (U7, C38–C63, R28–R33, J1, L5, D13/D14, FB1) ou deslocados pela placa +5 mm; as de cobre relevantes estão discutidas em `../research/step5-layout-h725.md` §7.",
      "", "## 3. Netlist esquemático × PCB", "",
      "- Componentes no esquemático: %d · footprints no PCB: %d · só no esquemático: %s · só no PCB: %s" % (out["netlist"]["sch_components"], out["netlist"]["pcb_footprints"], out["netlist"]["only_in_sch"] or "—", out["netlist"]["only_in_pcb"] or "—"),
      "- Pads comparados: %d · **redes divergentes: %d** · footprints divergentes: %d · valores divergentes: %d" % (out["netlist"]["pads_compared"], len(real_div), len(fp_diff), len(val_diff)),
      "- Pinos/pads sem correspondência (informativo, ex.: pinos NC do símbolo ou pads mecânicos): %d" % out["netlist"]["other_pin_pad_notes_count"]]
for d in real_div[:40]: L.append("  - %s.%s: sch `%s` × pcb `%s`" % (d["ref"], d["pin"], d["sch"], d["pcb"]))
for r, a, b in fp_diff[:20]: L.append("  - footprint %s: sch `%s` × pcb `%s`" % (r, a, b))
for r, a, b in val_diff[:20]: L.append("  - valor %s: sch `%s` × pcb `%s`" % (r, a, b))
L += ["", "## 4. BOM × esquemático × PCB (`hybrid_BOM.csv`)", "",
      "- Referências na BOM: %d · DNP no esquemático (excluídos): %s · só na BOM: %s · no esquemático e fora da BOM: %s" % (out["bom"]["lines_refs"], dnp_sch or "—", bom_only or "—", sch_only or "—"),
      "- Valores BOM≠sch: %d · footprints BOM≠pcb: %d · **sem MPN (PROVISÓRIO)**: %d → %s" % (len(bom_val), len(bom_pcb), len(no_mpn), ", ".join(no_mpn) if no_mpn else "—")]
L += ["", "## 5. Paridade firmware × hardware (`%s`)" % out["parity"]["report_md"], "",
      "- Código de saída: %d · estados: %s · **PIN_PARITY_CONFLICT: %d**" % (out["parity"]["exit"], out["parity"]["status_counts"], len(out["parity"]["conflicts"]))]
L += ["", "## 6. Skew / comprimentos / impedância", "",
      "- Ver `hardware\\research\\step6-roteamento-impedancia.md` e `hardware\\reports\\step6_reports.json` (gerados por `step6_reports.py`). **O DRC do KiCad não verifica impedância**; os valores são estimativas analíticas (Hammerstad–Jensen) sobre o stackup declarado, não medidos."]
L += ["", "## 7. Manifestos", "", "- `Make-Manifest.ps1 -Step STEP7 -Original` exit %d:" % out["manifests"]["exit"]] + ["  - " + x for x in out["manifests"]["tail"]]
L += ["", "## 8. Comandos executados", "", "| Comando | Exit | s | Log |", "|---|---|---|---|"]
for c in out["commands"]: L.append("| `%s` | %d | %s | %s |" % (c["cmd"].replace("|", "\\|")[:160], c["exit"], c["seconds"], c.get("log", "")))
md = os.path.join(ROOT, "hardware/research", "step7-validacao.md")
hp.assert_inside_output(md)
with open(md, "w", encoding="utf-8") as f: f.write("\n".join(L) + "\n")
print("falhas:", out["failures"]); print("->", md)
