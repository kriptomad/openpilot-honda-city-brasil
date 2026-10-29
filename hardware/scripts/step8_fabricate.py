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
# ---- JLCPCB rotation normalisation (A7). Table: cpl_rotations_db.csv (matthewlai/JLCKicadTools, the file downloaded by the
# Bouni kicad-jlcpcb-tools plugin). Rule selection and bottom-side mirroring follow that plugin (correction_data.find_correction
# = regex consuming the most characters wins, tried on reference, value, footprint; fabrication._rotation_for_match = bottom
# angle mirrored as (180 - rot) % 360 before the correction is added). Offsets of the table are NOT applied (only reported).
ROT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cpl_rotations_db.csv")
corrections = []
with open(ROT_DB, encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        if not row or row[0].startswith("Footprint pattern") or row[0].lstrip().startswith("#"): continue
        pat = row[0].strip()
        try: rx = re.compile(pat)
        except re.error: continue
        corrections.append({"pattern": pat, "regex": rx, "rotation": int(float(row[1])), "offset": (float(row[2]) if len(row) > 2 and row[2].strip() else 0.0, float(row[3]) if len(row) > 3 and row[3].strip() else 0.0)})
def find_correction(text):
    best, best_len = None, -1
    for c in corrections:
        m = c["regex"].search(text)
        if m and len(m.group(0)) > best_len: best, best_len = c, len(m.group(0))
    return best
def jlc_rotation(fp):
    """(kicad_rotation_used, correction_or_None, jlc_rotation) with the Bouni plugin convention."""
    rot = fp.GetOrientationDegrees()
    if fp.IsFlipped(): rot = (180 - rot) % 360
    fpname = fp.GetFPID().GetLibItemName().wx_str()
    for source, text in (("ref", fp.GetReference()), ("val", fp.GetValue()), ("fpt", fpname)):
        c = find_correction(text)
        if c: return rot, dict(c, source=source), (rot + c["rotation"] % 360) % 360
    return rot, None, rot % 360
cpl, cpl_detail = [], []
for ref, fp in sorted(fps.items()):
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES: continue
    if fp.IsDNP(): continue
    pos = fp.GetPosition() - aux
    rot_in, corr, rot_jlc = jlc_rotation(fp)
    fpname = fp.GetFPID().GetLibItemName().wx_str()
    cpl.append({"Designator": ref, "Mid X": "%.4f" % pcbnew.ToMM(pos.x), "Mid Y": "%.4f" % (-pcbnew.ToMM(pos.y)), "Layer": "Bottom" if fp.IsFlipped() else "Top",
                "Rotation": "%.1f" % rot_jlc, "Footprint": fpname, "Value": fp.GetValue()})
    cpl_detail.append({"Designator": ref, "Footprint": fpname, "Library": fp.GetFPID().GetLibNickname().wx_str(), "Layer": "Bottom" if fp.IsFlipped() else "Top",
                       "KiCad rotation": "%.1f" % fp.GetOrientationDegrees(), "Mirrored (bottom)": "%.1f" % rot_in, "Rule": corr["pattern"] if corr else "",
                       "Rule source": corr["source"] if corr else "", "Correction": corr["rotation"] if corr else 0, "Rule offset (not applied)": "%g,%g" % corr["offset"] if corr and any(corr["offset"]) else "",
                       "JLC rotation": "%.1f" % rot_jlc})
with open(os.path.join(ASM, "CPL_JLC.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation", "Footprint", "Value"]); w.writeheader(); w.writerows(cpl)
with open(os.path.join(ASM, "CPL_rotation_corrections.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(cpl_detail[0].keys())); w.writeheader(); w.writerows(cpl_detail)
run([CLI, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--use-drill-file-origin", "-o", os.path.join(ASM, "pos_kicad_both.csv"), PCB])
rot_summary = collections.OrderedDict()
for d in cpl_detail:
    k = (d["Footprint"], d["Rule"], d["Correction"]); rot_summary.setdefault(k, []).append(d["Designator"])
out["assembly"] = {"bom_lines": len(bom_rows), "bom_refs": sum(r["Qty"] for r in bom_rows), "cpl_rows": len(cpl), "cpl_top": sum(1 for c in cpl if c["Layer"] == "Top"),
                   "cpl_bottom": sum(1 for c in cpl if c["Layer"] == "Bottom"), "refs_without_LCSC": sorted(set(no_lcsc)), "refs_without_MPN": sorted(set(no_mpn)),
                   "aux_origin_mm": [pcbnew.ToMM(aux.x), pcbnew.ToMM(aux.y)],
                   "rotation_db": os.path.basename(ROT_DB), "rotation_rules": len(corrections),
                   "rotation_corrected": [{"footprint": k[0], "rule": k[1], "correction": k[2], "refs": v} for k, v in rot_summary.items() if k[1]],
                   "rotation_unmatched": [{"footprint": k[0], "refs": v} for k, v in rot_summary.items() if not k[1]],
                   "note": "CPL_JLC.csv rotation = KiCad orientation (bottom mirrored as 180-rot) + JLC correction table (cpl_rotations_db.csv, Bouni plugin convention); "
                           "detail per reference in CPL_rotation_corrections.csv; pos_kicad_both.csv is the raw KiCad export. Not checked against the JLC assembly preview. "
                           "LCSC read from the schematic 'LCSC' field (codes 'a verificar' in hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv)."}
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
if not v7: blocks.append("STEP 7 not executed (`step7_validation.json` missing).")
for fkey in v7.get("failures", []): blocks.append("STEP 7: " + fkey)
drc7 = v7.get("drc", {})
by_type = drc7.get("by_type", {})
inherited = {k: v for k, v in by_type.items() if v.get("hibrida")}
drc_txt = ", ".join("%s %d" % (k, v["hibrida"]) for k, v in sorted(inherited.items())) or "none"
A = " **Addressed by software, not physically verified**"
VP = "../reports/verification-pcb"
fa_p = os.path.join(REP, "final_audit.json")
fa = json.load(open(fa_p, encoding="utf-8")) if os.path.exists(fa_p) else {}
gr_p = os.path.join(ROOT, "hardware", "reports", "verification-pcb", "gerber-review.json")
gr = json.load(open(gr_p, encoding="utf-8")) if os.path.exists(gr_p) else {}
tv_p = os.path.join(ROOT, "hardware", "reports", "verification-pcb", "thermal-vias.json")
tv = json.load(open(tv_p, encoding="utf-8")) if os.path.exists(tv_p) else {}
if gr:
    conn = gr.get("connectivity", {})
    gerber_txt = ("Gerber review executed in software ([`%s/gerber-review.md`](%s/gerber-review.md)): %d layers rendered to PNG "
                  "(`%s/gerber-render/`), Edge.Cuts outline %s mm vs PCB %s mm, drill hits %s vs PCB holes %s, copper connectivity "
                  "rebuilt from the gerbers + drill and compared with the KiCad netlist: %s short(s), %s open(s) over %s nets.%s "
                  "A human look in KiCad GerbView is still part of the remaining checks below."
                  % (VP, VP, gr.get("layers_rendered", 0), VP, gr.get("edge_bbox_mm"), gr.get("pcb_bbox_mm"), gr.get("drill_hits"),
                     gr.get("pcb_holes"), conn.get("shorts"), conn.get("opens"), conn.get("nets_compared"), A))
else:
    gerber_txt = "Gerber viewer check: NOT executed automatically; only the syntactic check in `gerber_check.json`. Open `gerbers/` in KiCad GerbView before any order."
pcb_blocks = [
    "CAN and USB impedance/skew: analytical estimate only (`step6_reports.py`, [`%s/impedance.md`](%s/impedance.md): Hammerstad-Jensen / Kirschning-Jansen for the file stackup and for JLCPCB JLC7628; USB netclass 0.35/0.15 mm, CAN_DIFF 0.22/0.23 mm). KiCad's DRC does not check impedance; the stackup is assumed, not confirmed with the fabricator; no TDR.%s" % (VP, VP, A),
    "`USB_D+/-`: rerouted as an edge-coupled pair on B.Cu with one symmetric via pair and 0.35/0.15 mm width/gap, skew %s ([`%s/usb-reroute.md`](%s/usb-reroute.md)); previously 2 vias per net on In1.Cu. USB FS 12 Mbit/s is tolerant either way.%s" % ("< 0.3 mm", VP, VP, A),
    "DRC inherited from the OpenBlackPanda baseline: now %s ([`%s/drc-cleanup.md`](%s/drc-cleanup.md); `lib_footprint_mismatch` is intentional: local footprint edits). Clearance/unconnected/shorts/courtyards = %s/%s/%s/%s.%s" % (drc_txt, VP, VP, drc7.get("clearance"), drc7.get("unconnected_items"), drc7.get("shorting_items"), drc7.get("courtyards_overlap"), A),
    gerber_txt,
    "Via-in-pad: %s (`final_audit.py` definition: via centre inside an SMD pad of another net or of a small pad); %s same-net thermal vias inside exposed pads (U6 PowerPAD, U8-U11 DFN EP, placed by `vpcb_a10_thermal_vias.py`) are deliberate ([`%s/hand-assembly.md`](%s/hand-assembly.md)).%s" % (len(fa.get("via_in_pad", [])) if fa else "n/a", len(fa.get("thermal_vias", [])) if fa else "n/a", VP, VP, A),
    "Hand-solder friendliness: solder mask minimum web 0.1 mm (`solder_mask_min_width`), mask slivers >= 0.2 mm between U7 LQFP-144 and P1 USB-C 0.5 mm pads, DFN pin-to-EP mask 0.13 mm, one 0.6/0.3 mm GND via in each DFN exposed pad, vias tented both sides; ENIG recommended ([`%s/hand-assembly.md`](%s/hand-assembly.md)).%s" % (VP, VP, A),
    "No board was fabricated, assembled or measured: zero physical verification (continuity/isolation of the built board, impedance, power rails, USB enumeration, CAN). **Requires a built board.**",
]
asm_blocks = [
    "BOM: %d reference(s) without MPN and %d without LCSC code (of %d); U1 AP22615AWU-7 is no longer in the JLC catalogue (buy from Mouser/Digi-Key). The user buys and hand-solders every part, so LCSC codes and basic/extended status are informational only." % (len(out["assembly"]["refs_without_MPN"]), len(out["assembly"]["refs_without_LCSC"]), out["assembly"]["bom_refs"]),
    "Component rotation in `assembly/CPL_JLC.csv` is normalised with the JLC correction table (%d rules, `hardware/scripts/cpl_rotations_db.csv`): %d footprint type(s) corrected, %d without a rule ([`%s/cpl-rotation.md`](%s/cpl-rotation.md)). Only relevant if JLC assembly is ever ordered; not needed for a bare board." % (out["assembly"]["rotation_rules"], len(out["assembly"]["rotation_corrected"]), len(out["assembly"]["rotation_unmatched"]), VP, VP),
    "ARM toolchain: installed locally (Arm GNU 14.2.Rel1) but the firmware for this hardware (`hybrid-h725` branch in [`firmware/`](../../firmware)) has never run on hardware; depends on the commaai DFU/signing flow (see STEP 9). **Requires a built board.**",
]
blocks = pcb_blocks + asm_blocks
R = ["# Hybrid Panda fabrication package", "",
     "**STATUS: DO NOT FABRICATE.** This package was generated automatically for archive and",
     "review. Physical verification and human review are still missing. No board has ever been built from it.", "",
     "Hybrid Panda = black panda form factor + STM32H725ZGT6 running the red panda firmware.",
     "Generated %s by [`hardware/scripts/step8_fabricate.py`](../scripts/step8_fabricate.py)" % out["date"],
     "with KiCad 10.0.7 `kicad-cli` from [`hardware/hybrid-panda/HybridPanda.kicad_pcb`](../hybrid-panda/HybridPanda.kicad_pcb).",
     "Intended order: bare PCB only (JLCPCB), all components bought and hand-soldered by the user.",
     "Items marked \"addressed by software, not physically verified\" were changed in the PCB engineering pass of %s" % out["date"][:10],
     "(reports in [`hardware/reports/verification-pcb/`](../reports/verification-pcb/)); items marked \"requires a built board\" can only be closed after a board exists.", "",
     "## Why it must not be fabricated yet", "", "### PCB fabrication (bare board)", ""]
R += ["%d. %s" % (i + 1, b) for i, b in enumerate(pcb_blocks)]
R += ["", "### Assembly (manual, by the user)", ""]
R += ["%d. %s" % (len(pcb_blocks) + i + 1, b) for i, b in enumerate(asm_blocks)]
R += ["", "## Remaining human checks", "",
      "- Visual review of the PCB in KiCad (placement, silk legibility, polarity marks, reference designators) by a person.",
      "- Open `HybridPanda_gerbers_JLC.zip` in KiCad GerbView (or the JLCPCB online viewer) and compare with the renders in `%s/gerber-render/`." % VP,
      "- Independent review by a second person (schematic against datasheets and PCB layout).",
      "- Order a small batch of bare boards first (no assembly); continuity/isolation test with a multimeter before populating.",
      "- JLC assembly preview for rotations: only if JLC assembly is ever ordered (not planned)."]
R += ["", "## STEP 7 results (`../reports/step7_validation.json`)", "",
      "- ERC errors = %s, warnings = %s" % (v7.get("erc", {}).get("errors"), v7.get("erc", {}).get("warnings")),
      "- DRC unconnected = %s, clearance = %s, shorts = %s, courtyards = %s" % (drc7.get("unconnected_items"), drc7.get("clearance"), drc7.get("shorting_items"), drc7.get("courtyards_overlap")),
      "- Netlist divergences = %d; parity conflicts = %d" % (len(v7.get("netlist", {}).get("net_divergences", [])), len(v7.get("parity", {}).get("conflicts", []))),
      "- DRC by type (hybrid/baseline): " + (", ".join("%s %d/%d" % (k, v["hibrida"], v["baseline"]) for k, v in sorted(inherited.items())) or "none"), "",
      "## Contents", "", "| Path | Content |", "|---|---|",
      "| `gerbers/` | RS-274X (Protel extensions, no X2): F/In1/In2/B.Cu, F/B.Mask, F/B.SilkS, F/B.Paste, Edge.Cuts, job file |",
      "| `drill/` | Excellon PTH + NPTH (mm, 3:3, suppress leading), map PDF and Gerber X2 |",
      "| `assembly/` | `BOM_JLC.csv`, `CPL_JLC.csv` (origin = drill/aux origin %.2f,%.2f mm, rotation per JLC table), `CPL_rotation_corrections.csv`, `pos_kicad_both.csv` (raw KiCad) |" % tuple(out["assembly"]["aux_origin_mm"]),
      "| `pdf/` | schematic, copper per layer, fab/assembly top and bottom |",
      "| `3d/HybridPanda.step` | 3D model (missing models substituted) |",
      "| `drill_table.md` / `.json` | %d holes (%s); min drill %.3f mm; min annular ring %s |" % (len(holes), ", ".join("%s %d" % kv for kv in out["drill"]["by_kind"].items()), min_drill, ", ".join("%s %.3f" % kv for kv in min_ring.items())),
      "| `gerber_check.json` | syntactic check; Excellon holes vs PCB: %d vs %d |" % (exc_hits, len(holes)),
      "| `HybridPanda_gerbers_JLC.zip` | gerbers + drill for upload, ONLY after the blockers above are removed |", "",
      "Intended specification: 4 layers, 1.59 mm, FR-4 (er ~4.5 assumed; JLC7628 used for the impedance estimate), copper 1 oz outer / 0.5 oz",
      "inner, min track/space 0.127/0.1 mm, via 0.4/0.3 mm, min hole %.2f mm, ENIG recommended" % out["drill"]["rule_min_drill_mm"],
      "(QFN/LQFP 0.5 mm pitch), green mask, HASL not recommended.", "",
      "Generation problems: " + ("none" if not out["problems"] else "; ".join(out["problems"])) + ". Notes: " + ("none" if not out["notes"] else "; ".join(out["notes"])) + ".", "",
      "---", "",
      "pt-BR: **NAO FABRICAR.** Pacote gerado automaticamente para arquivo e revisao; nenhuma placa foi construida e",
      "falta verificacao fisica e revisao humana. A encomenda prevista e so da PCB nua (JLCPCB), com todos os componentes",
      "comprados e soldados a mao pelo utilizador. Os itens marcados \"addressed by software, not physically verified\"",
      "(impedancia com stackup JLC7628, par USB acoplado, limpeza do DRC herdado, revisao dos gerbers com comparacao de",
      "conectividade, vias termicas nos DFN, mascara minima 0.1 mm, rotacao do CPL) foram alterados apenas em software",
      "no passe de %s; os restantes (zero placas construidas, firmware nunca executado) exigem uma placa fisica." % out["date"][:10]]
open(os.path.join(FAB, "readme.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
out["readme_blocks"] = blocks
out["files"] = {d: sorted(os.listdir(os.path.join(FAB, d))) for d in ("gerbers", "drill", "assembly", "pdf", "3d")}
out["seconds"] = round(time.time() - T0, 1)
json.dump(out, open(os.path.join(REP, "step8_fabrication.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("problemas:", out["problems"]); print("-> hardware/fabrication (%.0f s)" % out["seconds"])
