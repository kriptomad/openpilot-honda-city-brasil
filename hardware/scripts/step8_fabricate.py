"""step8_fabricate.py - STEP 8 (protocolo v3): pacote de fabricação em hardware/fabrication.

Gera (kicad-cli 10 + pcbnew):
  gerbers/   F.Cu In1.Cu In2.Cu B.Cu, máscaras, serigrafia, pasta, Edge.Cuts (Protel ext., X2 off, p/ JLC)
  drill/     Excellon PTH/NPTH separados (mm, suppress leading, formato 3:3) + mapa PDF + relatório
  assembly/  BOM_JLC.csv (Comment,Designator,Footprint,LCSC Part #) e CPL_JLC.csv (top+bottom)
  pdf/       esquemático, camadas de cobre + fab + assembly
  3d/        HybridPanda.step
  drill_table.md / drill_table.json : furos PTH/NPTH/vias com anel anular mínimo calculado
  gerber_check.json : verificação sintática dos gerbers (RS-274X: aperturas, D-codes, M02) — NÃO substitui visualizador
  ../fabrication/readme.md : estado real ("NÃO FABRICAR" enquanto houver bloqueios) com motivos
Lê step7_validation.json para decidir o estado. Nada fora de OUTPUT_ROOT.
"""
import csv, json, os, re, subprocess, sys, time, zipfile, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew

ROOT = str(hp.OUTPUT_ROOT)
PROJ = os.path.join(ROOT, "hardware", "hybrid-panda")
SCH = os.path.join(PROJ, "HybridPanda.kicad_sch")
PCB = os.path.join(PROJ, "HybridPanda.kicad_pcb")
FAB = os.path.join(ROOT, "hardware/fabrication")
REP = os.path.join(ROOT, "hardware/reports")
CLI = str(hp.KICAD_CLI)
T0 = time.time()
out = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "commands": [], "files": {}, "problems": [], "notes": []}
for d in ("gerbers", "drill", "assembly", "pdf", "3d"):
    hp.assert_inside_output(os.path.join(FAB, d)); os.makedirs(os.path.join(FAB, d), exist_ok=True)

def run(cmd):
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    err = "\n".join(l for l in p.stderr.splitlines() if not re.search(r"swig|image handler|assert", l, re.I))
    out["commands"].append({"cmd": subprocess.list2cmdline(cmd), "exit": p.returncode, "seconds": round(time.time() - t, 1), "stderr": err[-400:]})
    print("$", subprocess.list2cmdline(cmd)[:110], "->", p.returncode)
    if p.returncode: out["problems"].append("comando falhou (exit %d): %s" % (p.returncode, subprocess.list2cmdline(cmd)[:90]))
    return p

# ------------------------------------------------------------------ gerbers
GERB = os.path.join(FAB, "gerbers")
for f in os.listdir(GERB): os.remove(os.path.join(GERB, f))
run([CLI, "pcb", "export", "gerbers", "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
     "--use-drill-file-origin", "--no-x2", "--no-netlist", "--subtract-soldermask", "--disable-aperture-macros", "-o", GERB + os.sep, PCB])
# ------------------------------------------------------------------ drill
DRL = os.path.join(FAB, "drill")
for f in os.listdir(DRL): os.remove(os.path.join(DRL, f))
run([CLI, "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot", "--excellon-separate-th", "--excellon-units", "mm",
     "--excellon-zeros-format", "suppressleading", "--generate-map", "--map-format", "pdf", "-o", DRL + os.sep, PCB])
run([CLI, "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot", "--excellon-separate-th", "--excellon-units", "mm",
     "--excellon-zeros-format", "suppressleading", "--generate-map", "--map-format", "gerberx2", "-o", DRL + os.sep, PCB])
# ------------------------------------------------------------------ PDFs
PDF = os.path.join(FAB, "pdf")
run([CLI, "sch", "export", "pdf", "-o", os.path.join(PDF, "HybridPanda_schematic.pdf"), SCH])
for name, layers in (("copper_F", "F.Cu,Edge.Cuts"), ("copper_In1", "In1.Cu,Edge.Cuts"), ("copper_In2", "In2.Cu,Edge.Cuts"), ("copper_B", "B.Cu,Edge.Cuts"),
                     ("fab_top", "F.Fab,F.SilkS,Edge.Cuts"), ("fab_bottom", "B.Fab,B.SilkS,Edge.Cuts"), ("assembly_top", "F.Fab,F.CrtYd,Edge.Cuts"), ("assembly_bottom", "B.Fab,B.CrtYd,Edge.Cuts")):
    args = [CLI, "pcb", "export", "pdf", "--layers", layers, "--include-border-title", "-o", os.path.join(PDF, "HybridPanda_%s.pdf" % name)]
    if name.endswith("bottom") or name == "copper_B": args.append("--mirror")
    run(args + [PCB])
# ------------------------------------------------------------------ STEP
step_file = os.path.join(FAB, "3d", "HybridPanda.step")
p_step = run([CLI, "pcb", "export", "step", "--subst-models", "--include-tracks", "--include-zones", "--force", "-o", step_file, PCB])
if p_step.returncode and os.path.exists(step_file) and os.path.getsize(step_file) > 1_000_000:
    # kicad-cli devolve 2 quando ignora modelos 3D VRML (footprints do baseline); o STEP é gerado na mesma, sem esses corpos
    out["problems"] = [x for x in out["problems"] if "export step" not in x]
    nvrml = out["commands"][-1]["stderr"].count("VRML")
    out["notes"].append("STEP gerado (%.1f MB) com aviso: modelos VRML ignorados (kicad-cli exit 2; %d avisos no stderr truncado) — corpos 3D desses footprints ausentes" % (os.path.getsize(step_file) / 1e6, nvrml))
# ------------------------------------------------------------------ BOM/CPL JLC
ASM = os.path.join(FAB, "assembly")
bom_src = os.path.join(ASM, "_bom_fields.csv")
run([CLI, "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${DNP},MPN,LCSC,Manufacturer", "--labels", "Reference,Value,Footprint,DNP,MPN,LCSC,Manufacturer",
     "--group-by", "Value,Footprint,MPN,LCSC", "--exclude-dnp", "-o", bom_src, SCH])
board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
def expand_refs(field):
    """'C1,C16-C21' -> ['C1','C16',...,'C21'] (o --group-by do kicad-cli comprime intervalos)."""
    outl = []
    for x in [x.strip() for x in field.split(",") if x.strip()]:
        m = re.fullmatch(r"([A-Za-z_]+)(\d+)-([A-Za-z_]+)?(\d+)", x)
        if m and (m.group(3) in (None, m.group(1))): outl += ["%s%d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(4)) + 1)]
        else: outl.append(x)
    return outl
bom_rows, no_lcsc, no_mpn = [], [], []
with open(bom_src, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        refs = expand_refs(row["Reference"])
        fpname = row["Footprint"].split(":")[-1]
        bom_rows.append({"Comment": row["Value"], "Designator": ",".join(refs), "Footprint": fpname, "LCSC Part #": row.get("LCSC", ""), "MPN": row.get("MPN", ""), "Manufacturer": row.get("Manufacturer", ""), "Qty": len(refs)})
        if not row.get("LCSC"): no_lcsc += refs
        if not row.get("MPN"): no_mpn += refs
os.remove(bom_src)
with open(os.path.join(ASM, "BOM_JLC.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #", "MPN", "Manufacturer", "Qty"]); w.writeheader(); w.writerows(bom_rows)
aux = board.GetDesignSettings().GetAuxOrigin()
cpl = []
for ref, fp in sorted(fps.items()):
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES: continue
    if fp.IsDNP(): continue
    pos = fp.GetPosition() - aux
    cpl.append({"Designator": ref, "Mid X": "%.4f" % pcbnew.ToMM(pos.x), "Mid Y": "%.4f" % (-pcbnew.ToMM(pos.y)), "Layer": "Bottom" if fp.IsFlipped() else "Top",
                "Rotation": "%.1f" % fp.GetOrientationDegrees(), "Footprint": fp.GetFPID().GetLibItemName().wx_str(), "Value": fp.GetValue()})
with open(os.path.join(ASM, "CPL_JLC.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation", "Footprint", "Value"]); w.writeheader(); w.writerows(cpl)
run([CLI, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--use-drill-file-origin", "-o", os.path.join(ASM, "pos_kicad_both.csv"), PCB])
out["assembly"] = {"bom_lines": len(bom_rows), "bom_refs": sum(r["Qty"] for r in bom_rows), "cpl_rows": len(cpl), "cpl_top": sum(1 for c in cpl if c["Layer"] == "Top"),
                   "cpl_bottom": sum(1 for c in cpl if c["Layer"] == "Bottom"), "refs_without_LCSC": sorted(set(no_lcsc)), "refs_without_MPN": sorted(set(no_mpn)),
                   "aux_origin_mm": [pcbnew.ToMM(aux.x), pcbnew.ToMM(aux.y)],
                   "note": "Rotação CPL = orientação KiCad; JLC pode exigir correção por footprint (não verificado). LCSC lido do campo 'LCSC' do esquemático (códigos 'a verificar' em hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv)."}
# ------------------------------------------------------------------ tabela de furação
holes = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        d = p.GetDrillSize()
        if d.x == 0: continue
        pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        ring = min(p.GetSize().x - d.x, p.GetSize().y - d.y) / 2 if pth else 0  # por eixo (slots: pad oblongo)
        holes.append({"kind": "PTH" if pth else "NPTH", "ref": fp.GetReference(), "pad": p.GetNumber(), "drill_mm": round(pcbnew.ToMM(max(d.x, d.y)), 3),
                      "slot": d.x != d.y, "annular_mm": round(pcbnew.ToMM(ring), 3) if pth else None, "x": round(pcbnew.ToMM(p.GetPosition().x), 3), "y": round(pcbnew.ToMM(p.GetPosition().y), 3)})
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        holes.append({"kind": "VIA", "ref": t.GetNetname(), "pad": "", "drill_mm": round(pcbnew.ToMM(t.GetDrillValue()), 3), "slot": False,
                      "annular_mm": round(pcbnew.ToMM((t.GetWidth() - t.GetDrillValue()) / 2), 3), "x": round(pcbnew.ToMM(t.GetPosition().x), 3), "y": round(pcbnew.ToMM(t.GetPosition().y), 3)})
sizes = collections.Counter((h["kind"], h["drill_mm"], h["slot"]) for h in holes)
min_ring = {k: min(h["annular_mm"] for h in holes if h["kind"] == k) for k in ("PTH", "VIA") if any(h["kind"] == k for h in holes)}
min_drill = min(h["drill_mm"] for h in holes)
ds = board.GetDesignSettings()
out["drill"] = {"total": len(holes), "by_kind": dict(collections.Counter(h["kind"] for h in holes)), "min_drill_mm": min_drill, "min_annular_mm": min_ring,
                "rule_min_annular_mm": pcbnew.ToMM(ds.m_ViasMinAnnularWidth), "rule_min_drill_mm": pcbnew.ToMM(ds.m_MinThroughDrill),
                "sizes": [{"kind": k, "drill_mm": d, "slot": s, "count": n} for (k, d, s), n in sorted(sizes.items())]}
L = ["# Tabela de furação — HybridPanda (gerada por step8_fabricate.py, %s)" % out["date"], "",
     "Total de furos: %d (%s). Menor broca: %.3f mm (regra: %.3f). Anel anular mínimo: %s (regra: %.3f mm)." %
     (len(holes), ", ".join("%s=%d" % kv for kv in out["drill"]["by_kind"].items()), min_drill, out["drill"]["rule_min_drill_mm"],
      ", ".join("%s %.3f mm" % kv for kv in min_ring.items()), out["drill"]["rule_min_annular_mm"]), "",
     "| Tipo | Broca (mm) | Slot | Qtd |", "|---|---|---|---|"]
L += ["| %s | %.3f | %s | %d |" % (k, d, "sim" if s else "não", n) for (k, d, s), n in sorted(sizes.items())]
L += ["", "## Furos PTH/NPTH de componentes", "", "| Tipo | Ref | Pad | Broca | Anel | X | Y |", "|---|---|---|---|---|---|---|"]
L += ["| %s | %s | %s | %.3f | %s | %.3f | %.3f |" % (h["kind"], h["ref"], h["pad"], h["drill_mm"], "-" if h["annular_mm"] is None else "%.3f" % h["annular_mm"], h["x"], h["y"]) for h in holes if h["kind"] != "VIA"]
L += ["", "Vias: %d (detalhe em drill_table.json). Mapa de furação: `drill\\HybridPanda-drl_map.pdf`; relatório Excellon: `drill\\HybridPanda-drl.rpt` (se gerado)." % sum(1 for h in holes if h["kind"] == "VIA")]
open(os.path.join(FAB, "drill_table.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(holes, open(os.path.join(FAB, "drill_table.json"), "w", encoding="utf-8"), indent=0)
# ------------------------------------------------------------------ verificação sintática dos gerbers
gchk = {}
for f in sorted(os.listdir(GERB)):
    if f.endswith(".gbrjob"): continue  # ficheiro JSON (Gerber Job), não é Gerber RS-274X
    txt = open(os.path.join(GERB, f), encoding="utf-8", errors="replace").read()
    gchk[f] = {"bytes": len(txt), "apertures": len(re.findall(r"%ADD\d+", txt)), "flashes_D03": txt.count("D03*"), "draws_D01": txt.count("D01*"),
               "has_M02": txt.rstrip().endswith("M02*"), "format_FS": bool(re.search(r"%FSLAX\d\dY\d\d\*%", txt)), "unit_MM": "%MOMM*%" in txt}
    if not gchk[f]["has_M02"] or not gchk[f]["format_FS"] or gchk[f]["bytes"] < 200: out["problems"].append("gerber suspeito: " + f)
    if f.endswith("Edge_Cuts.gm1") and gchk[f]["draws_D01"] < 4: out["problems"].append("Edge.Cuts com menos de 4 traços")
for f in sorted(os.listdir(DRL)):
    if f.endswith(".drl"):
        txt = open(os.path.join(DRL, f), encoding="utf-8", errors="replace").read()
        gchk[f] = {"bytes": len(txt), "tools": len(re.findall(r"^T\d+C", txt, re.M)), "hits": len(re.findall(r"^X-?\d", txt, re.M)), "has_M30": "M30" in txt, "metric": "METRIC" in txt}
        if not gchk[f]["has_M30"]: out["problems"].append("excellon sem M30: " + f)
exc_hits = sum(v.get("hits", 0) for k, v in gchk.items() if k.endswith(".drl"))
gchk["_excellon_total_hits_vs_pcb"] = {"excellon": exc_hits, "pcb_holes": len(holes), "match": exc_hits == len(holes)}
if exc_hits != len(holes): out["problems"].append("furos Excellon (%d) != furos no PCB (%d)" % (exc_hits, len(holes)))
json.dump(gchk, open(os.path.join(FAB, "gerber_check.json"), "w", encoding="utf-8"), indent=1)
out["gerber_check"] = {"files": len(gchk) - 1, "excellon_vs_pcb": gchk["_excellon_total_hits_vs_pcb"]}
# ------------------------------------------------------------------ zip p/ fabricante
zpath = os.path.join(FAB, "HybridPanda_gerbers_JLC.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in os.listdir(GERB): z.write(os.path.join(GERB, f), f)
    for f in os.listdir(DRL):
        if f.endswith((".drl", ".pdf")): z.write(os.path.join(DRL, f), f)
# ------------------------------------------------------------------ LEIA-ME
v7p = os.path.join(REP, "step7_validation.json")
v7 = json.load(open(v7p, encoding="utf-8")) if os.path.exists(v7p) else {}
blocks = []
if not v7: blocks.append("STEP 7 não executado (step7_validation.json ausente).")
for fkey in v7.get("failures", []): blocks.append("STEP 7: " + fkey)
drc7 = v7.get("drc", {})
inherited = {k: v for k, v in drc7.get("by_type", {}).items() if v.get("hibrida")}
blocks += ["Impedância/skew CAN-FD e USB: apenas estimativa analítica (step6_reports.py); o DRC do KiCad não verifica impedância; stackup 4 camadas 1.59 mm assumido, não confirmado com o fabricante.",
           "USB_D± não é par acoplado: Freerouting roteou com vias (ver hardware\\research\\step5-layout-h725.md §5/§7); FS 12 Mb/s tolera, mas não foi validado.",
           "Nenhuma placa foi fabricada, montada ou medida — zero validação física; firmware red panda oficial NUNCA foi executado neste hardware.",
           "BOM: %d referências sem MPN e %d sem código LCSC (de %d); códigos LCSC marcados 'a verificar' em hardware\\reports\\bom-real\\BOM_HYBRIDPANDA_v1.csv ainda não confirmados no catálogo JLC — montagem JLC exige confirmar." % (len(out["assembly"]["refs_without_MPN"]), len(out["assembly"]["refs_without_LCSC"]), out["assembly"]["bom_refs"]),
           "Violações DRC herdadas do baseline OpenBlackPanda não corrigidas (%s) — ver hardware\\research\\step5-layout-h725.md §7.3 e hardware\\reports\\correcoes-aplicadas.md." % (", ".join("%s %d" % (k, v["hibrida"]) for k, v in inherited.items()) or "nenhuma"),
           "Verificação em visualizador de gerber: NÃO EXECUTADA automaticamente (sem gerbv/gerbview CLI); apenas verificação sintática (gerber_check.json). Abrir gerbers/ no KiCad GerbView antes de qualquer pedido.",
           "Toolchain ARM: instalada localmente (Arm GNU 14.2.Rel1, %LOCALAPPDATA%\\arm-gnu-toolchain) mas firmware ainda NÃO compilado/assinado para este hardware; dependência do fluxo oficial de DFU/assinatura do commaai (ver STEP9).",
           "Rotação dos componentes no CPL não normalizada para a convenção JLC (requer ajuste manual por footprint no painel JLC).",
           "Via-in-pad: 0 após o relayout leste (step5e_relayout_east.py, D-33) + fix_audit.py + fix_vip_reroute.py (U8.3 +5V: via movida para a trilha F.Cu a oeste de C30 e trilha B.Cu reencaminhada). Contagem pela definição do final_audit.py (centro da via dentro da bbox de pad SMD) sobre o tabuleiro actual — reconfirmar em hardware\\reports\\final_audit.json antes de qualquer pedido."]
R = ["HYBRID PANDA (Black Panda form factor + STM32H725ZGT6 / firmware red panda) — PACOTE DE FABRICAÇÃO", "Gerado: %s por hardware\\scripts\\step8_fabricate.py (KiCad 10.0.7 kicad-cli)" % out["date"], "",
     "=" * 78, "   ESTADO: NÃO FABRICAR", "=" * 78, "",
     "Este pacote foi gerado automaticamente para arquivo/revisão. NÃO foi validado para produção. Motivos:", ""]
R += ["  %d. %s" % (i + 1, b) for i, b in enumerate(blocks)]
R += ["", "Resultados do STEP 7 (hardware\\reports\\step7_validation.json):",
      "  ERC erros=%s avisos=%s | DRC não ligados=%s clearance=%s curtos=%s courtyards=%s | netlist divergências=%s | paridade conflitos=%s" %
      (v7.get("erc", {}).get("errors"), v7.get("erc", {}).get("warnings"), drc7.get("unconnected_items"), drc7.get("clearance"), drc7.get("shorting_items"), drc7.get("courtyards_overlap"),
       len(v7.get("netlist", {}).get("net_divergences", [])), len(v7.get("parity", {}).get("conflicts", []))),
      "  DRC por tipo (híbrida/baseline): " + ", ".join("%s %d/%d" % (k, v["hibrida"], v["baseline"]) for k, v in inherited.items()), "",
      "Conteúdo:", "  gerbers\\            RS-274X (Protel ext, sem X2) — F/In1/In2/B.Cu, F/B.Mask, F/B.SilkS, F/B.Paste, Edge.Cuts",
      "  drill\\              Excellon PTH + NPTH (mm, 3:3, suppress leading), mapa PDF e Gerber X2",
      "  assembly\\           BOM_JLC.csv, CPL_JLC.csv (origem = drill/aux origin %.2f,%.2f mm), pos_kicad_both.csv" % tuple(out["assembly"]["aux_origin_mm"]),
      "  pdf\\                esquemático, cobre por camada, fab/assembly top/bottom", "  3d\\HybridPanda.step  modelo 3D (modelos substituídos quando ausentes)",
      "  drill_table.md/json  %d furos (%s); broca mín %.3f mm; anel anular mín %s" % (len(holes), ", ".join("%s=%d" % kv for kv in out["drill"]["by_kind"].items()), min_drill, ", ".join("%s %.3f" % kv for kv in min_ring.items())),
      "  gerber_check.json    verificação sintática; furos Excellon x PCB: %d x %d" % (exc_hits, len(holes)),
      "  HybridPanda_gerbers_JLC.zip  gerbers+drill prontos para upload (APENAS após remover os bloqueios acima)", "",
      "Especificação pretendida: 4 camadas, 1.59 mm, FR-4 (εr≈4.5 assumido), cobre 1 oz ext/0.5 oz int, trilha/espaço mín 0.1375/0.1 mm, via 0.4/0.3 mm, furo mín %.2f mm, ENIG recomendado (QFN/LQFP 0.5 mm), máscara verde, HASL NÃO recomendado." % out["drill"]["rule_min_drill_mm"],
      "", "Problemas na geração: " + ("nenhum" if not out["problems"] else "; ".join(out["problems"])),
      "Notas: " + ("nenhuma" if not out["notes"] else "; ".join(out["notes"]))]
open(os.path.join(FAB, "readme.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
out["readme_blocks"] = blocks
out["files"] = {d: sorted(os.listdir(os.path.join(FAB, d))) for d in ("gerbers", "drill", "assembly", "pdf", "3d")}
out["seconds"] = round(time.time() - T0, 1)
json.dump(out, open(os.path.join(REP, "step8_fabrication.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("problemas:", out["problems"]); print("-> hardware/fabrication (%.0f s)" % out["seconds"])
