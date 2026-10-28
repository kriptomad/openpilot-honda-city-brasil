"""step6_reports.py — STEP 6 (protocolo v3): relatórios de roteamento sobre a PCB final.

Mede (não altera a placa):
  * pares diferenciais CAN_DIFF (BUS0/BUS1N/BUS1O/BUS2 _H/_L) e USB (USB_D±, USB_R_D±): comprimento por camada,
    nº de vias, skew por par, largura das trilhas, estado travado;
  * impedância estimada (microstrip IPC-2141 / Hammerstad-Jensen) para as larguras encontradas — o DRC do KiCad NÃO verifica
    impedância; o valor é uma estimativa a partir do stackup do ficheiro (.kicad_pcb);
  * continuidade dos planos: nº de polígonos preenchidos e área por camada para GND (F/In2/B) e +3V3 (In1), nº de agrupamentos
    de conectividade por rede (1 = contínuo).
Saídas: hardware\\reports\\step6_reports.json e hardware\\research\\step6-roteamento-impedancia.md.
Uso: python (do KiCad) step6_reports.py [--pcb caminho]
"""
import sys, os, json, math, re, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbnew import ToMM
from hp_common import OUTPUT_ROOT, guarded_write_text

ap = argparse.ArgumentParser()
ap.add_argument("--pcb", default=str(OUTPUT_ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_pcb"))
args = ap.parse_args()

board = pcbnew.LoadBoard(args.pcb)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
conn = board.GetConnectivity()
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
LN = {l: board.GetLayerName(l) for l in LAYERS}
nets = board.GetNetsByName()
rep = {"when": time.strftime("%Y-%m-%d %H:%M"), "pcb": args.pcb}

# ---------------------------------------------------------------- stackup (lido do ficheiro)
txt = open(args.pcb, encoding="utf-8").read()
m = re.search(r"\(stackup(.*?)\n\s*\)\n\s*\(pad_to_mask", txt, re.S)
stack = []
if m:
    for lm in re.finditer(r'\(layer "([^"]+)"(.*?)(?=\(layer "|\Z)', m.group(1), re.S):
        name, body = lm.group(1), lm.group(2)
        th = re.search(r"\(thickness ([\d.]+)", body); er = re.search(r"\(epsilon_r ([\d.]+)", body)
        stack.append({"layer": name, "thickness_mm": float(th.group(1)) if th else None, "epsilon_r": float(er.group(1)) if er else None})
rep["stackup"] = stack
def dielectric_between(a, b):
    names = [s["layer"] for s in stack]
    if a not in names or b not in names: return None, None
    i, j = sorted((names.index(a), names.index(b)))
    h = sum(s["thickness_mm"] or 0 for s in stack[i + 1:j]); ers = [s["epsilon_r"] for s in stack[i + 1:j] if s["epsilon_r"]]
    return h, (sum(ers) / len(ers) if ers else None)

# ---------------------------------------------------------------- impedância (estimativas)
def z0_microstrip(w, h, t, er):
    """Hammerstad-Jensen (IPC-2141 §), w,h,t em mm. Válido grosso modo para 0,1 < w/h < 10."""
    if w <= 0 or h <= 0: return None
    weff = w + (t / math.pi) * (1 + math.log(2 * h / t)) if t > 0 else w
    u = weff / h
    a = 1 + (1 / 49) * math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) + (1 / 18.7) * math.log(1 + (u / 18.1) ** 3)
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    ereff = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / u) ** 0.7528))
    z = 60 / math.sqrt(ereff) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))
    return round(z, 1), round(ereff, 2)
def zdiff_microstrip(z0, s, h):
    """par microstrip acoplado lateralmente (aprox. IPC-2141 / National AN-905): Zdiff = 2 Z0 (1 - 0,48 e^(-0,96 s/h))."""
    return round(2 * z0 * (1 - 0.48 * math.exp(-0.96 * s / h)), 1)

# ---------------------------------------------------------------- pares
PAIRS = {"CAN_DIFF": [("BUS0_H", "BUS0_L"), ("BUS1N_H", "BUS1N_L"), ("BUS1O_H", "BUS1O_L"), ("BUS2_H", "BUS2_L")],
         "USB": [("USB_D+", "USB_D-"), ("USB_R_D+", "USB_R_D-")]}
def net_stats(name):
    if name not in nets: return None
    nc = nets[name].GetNetCode(); per = {LN[l]: 0.0 for l in LAYERS}; vias = 0; widths = set(); locked = 0; n = 0; gaps = []
    for t in board.GetTracks():
        if t.GetNetCode() != nc: continue
        if t.GetClass() == "PCB_VIA": vias += 1; continue
        n += 1; per[board.GetLayerName(t.GetLayer())] += ToMM(t.GetLength()); widths.add(round(ToMM(t.GetWidth()), 3)); locked += t.IsLocked()
    return {"segments": n, "vias": vias, "length_mm": {k: round(v, 2) for k, v in per.items() if v}, "total_mm": round(sum(per.values()), 2),
            "widths_mm": sorted(widths), "locked": locked}
def pair_gap(a, b):
    """distância centro-a-centro típica entre as trilhas do par (mediana das distâncias ponto médio -> outra net, mesma camada)."""
    if a not in nets or b not in nets: return None
    na, nb = nets[a].GetNetCode(), nets[b].GetNetCode(); ds = []
    tb = [t for t in board.GetTracks() if t.GetNetCode() == nb and t.GetClass() == "PCB_TRACK"]
    for t in board.GetTracks():
        if t.GetNetCode() != na or t.GetClass() != "PCB_TRACK": continue
        mid = pcbnew.VECTOR2I((t.GetStart().x + t.GetEnd().x) // 2, (t.GetStart().y + t.GetEnd().y) // 2)
        c = [ToMM(pcbnew.SEG(o.GetStart(), o.GetEnd()).Distance(mid)) for o in tb if o.GetLayer() == t.GetLayer()]
        if c: ds.append(min(c))
    ds.sort()
    return round(ds[len(ds) // 2], 3) if ds else None
rep["pairs"] = {}
for cls, prs in PAIRS.items():
    for a, b in prs:
        sa, sb = net_stats(a), net_stats(b)
        if sa is None or sb is None: rep["pairs"][a + "/" + b] = {"missing": [x for x, s in ((a, sa), (b, sb)) if s is None]}; continue
        rep["pairs"][a + "/" + b] = {"class": cls, a: sa, b: sb, "skew_mm": round(abs(sa["total_mm"] - sb["total_mm"]), 3),
                                     "vias_on_pair": sa["vias"] + sb["vias"], "gap_cc_mm": pair_gap(a, b),
                                     "layers": sorted(set(sa["length_mm"]) | set(sb["length_mm"]))}

# impedância para as larguras encontradas nas trilhas dos pares em F.Cu/B.Cu (referência: In1 / In2 mais próxima)
rep["impedance_estimates"] = []
for key, pr in rep["pairs"].items():
    if "class" not in pr: continue
    a, b = key.split("/")
    for lay in pr["layers"]:
        ref = "In1.Cu" if lay == "F.Cu" else "In2.Cu" if lay == "B.Cu" else None
        if ref is None: rep["impedance_estimates"].append({"pair": key, "layer": lay, "note": "camada interna: não estimado"}); continue
        h, er = dielectric_between(lay, ref)
        tcu = next((s["thickness_mm"] for s in stack if s["layer"] == lay), 0.035)
        ws = sorted(set(pr[a]["widths_mm"]) | set(pr[b]["widths_mm"]))
        for w in ws:
            z = z0_microstrip(w, h, tcu, er) if h and er else None
            gap = pr["gap_cc_mm"]; s = (gap - w) if gap else None
            rep["impedance_estimates"].append({"pair": key, "layer": lay, "ref": ref, "h_mm": round(h, 4) if h else None, "er": er, "w_mm": w,
                                               "Z0_ohm": z[0] if z else None, "eeff": z[1] if z else None, "gap_edge_mm": round(s, 3) if s else None,
                                               "Zdiff_ohm": zdiff_microstrip(z[0], s, h) if (z and s and s > 0) else None,
                                               "note": "referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior)" if ref == "In1.Cu" else ""})

# ---------------------------------------------------------------- planos
def clusters(name):
    nc = nets[name].GetNetCode(); items = []
    for t in board.GetTracks():
        if t.GetNetCode() == nc: items.append(t)
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == nc: items.append(p)
    seen = set(); groups = []
    types = pcbnew.PCB_TRACE_T, pcbnew.PCB_VIA_T, pcbnew.PCB_PAD_T, pcbnew.PCB_ZONE_T
    for it in items:
        k = it.m_Uuid.AsString()
        if k in seen: continue
        grp = conn.GetConnectedItems(it); g = [x for x in grp]
        ks = {x.m_Uuid.AsString() for x in g} | {k}
        if ks & seen: continue
        seen |= ks; groups.append(len(ks))
    return sorted(groups, reverse=True)
rep["planes"] = {}
for name, lays in (("GND", (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)), ("+3V3", (pcbnew.In1_Cu,))):
    if name not in nets: continue
    nc = nets[name].GetNetCode(); d = {"clusters": clusters(name), "layers": {}}
    for z in board.Zones():
        if z.GetNetCode() != nc or z.GetIsRuleArea(): continue
        for l in lays:
            if not z.IsOnLayer(l): continue
            polys = z.GetFilledPolysList(l); areas = []
            for i in range(polys.OutlineCount()):
                areas.append(abs(polys.Outline(i).Area()) / 1e12)
            areas.sort(reverse=True)
            tot = sum(areas)
            d["layers"][LN[l]] = {"outline_count": len(areas), "area_mm2": round(tot, 1), "largest_mm2": round(areas[0], 1) if areas else 0,
                                  "largest_fraction": round(areas[0] / tot, 3) if tot else None, "small_fragments_lt_5mm2": sum(1 for a in areas if a < 5)}
    rep["planes"][name] = d

# ---------------------------------------------------------------- vias totais / larguras
tr = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]; vi = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
rep["totals"] = {"tracks": len(tr), "vias": len(vi), "min_track_width_mm": round(min(ToMM(t.GetWidth()) for t in tr), 4),
                 "via_sizes": sorted({(round(ToMM(v.GetWidth(pcbnew.F_Cu)), 2), round(ToMM(v.GetDrillValue()), 2)) for v in vi})}

guarded_write_text(OUTPUT_ROOT / "hardware/reports" / "step6_reports.json", json.dumps(rep, indent=1, ensure_ascii=False), tag="step6")

# ---------------------------------------------------------------- markdown
L = ["# STEP 6 — Roteamento, impedância e zonas — relatório de medições", "",
     "Data: %s · Placa: `%s` · Script: `hardware\\scripts\\step6_reports.py` (só leitura) · JSON: `hardware\\reports\\step6_reports.json`" % (rep["when"], os.path.relpath(args.pcb, OUTPUT_ROOT)), "",
     "> O DRC do KiCad **não verifica impedância**. Os valores abaixo são estimativas analíticas (Hammerstad-Jensen / IPC-2141) a partir do stackup gravado no ficheiro; a referência de retorno real depende de onde há cobre em In1 (zona +3V3 só sob o MCU) — fora dela a referência é In2 (GND) a ≈1,28 mm, o que sobe Z0. Validação só com o fabricante (stackup controlado) ou TDR.", "",
     "## 1. Stackup (do ficheiro)", "| Camada | Espessura (mm) | εr |", "|---|---|---|"]
for s in stack: L.append("| %s | %s | %s |" % (s["layer"], s["thickness_mm"], s["epsilon_r"] or ""))
L += ["", "## 2. Pares diferenciais", "| Par | Classe | Camadas | Comprimento H/+ (mm) | Comprimento L/− (mm) | Skew (mm) | Vias no par | Larguras (mm) | Gap c-c (mm) | Travadas |", "|---|---|---|---|---|---|---|---|---|---|"]
for key, pr in rep["pairs"].items():
    if "class" not in pr: L.append("| %s | — | nets em falta: %s | | | | | | | |" % (key, pr["missing"])); continue
    a, b = key.split("/")
    L.append("| %s | %s | %s | %.2f | %.2f | %.3f | %d | %s | %s | %d/%d |" % (key, pr["class"], ",".join(pr["layers"]), pr[a]["total_mm"], pr[b]["total_mm"], pr["skew_mm"],
             pr["vias_on_pair"], "/".join(str(w) for w in sorted(set(pr[a]["widths_mm"]) | set(pr[b]["widths_mm"]))), pr["gap_cc_mm"], pr[a]["locked"] + pr[b]["locked"], pr[a]["segments"] + pr[b]["segments"]))
L += ["", "Critérios do protocolo (STEP 6): vias nos pares CAN = 0 → %s; pares em F.Cu → %s." % (
    "OK" if all(pr.get("vias_on_pair", 1) == 0 for k, pr in rep["pairs"].items() if pr.get("class") == "CAN_DIFF") else "FALHA",
    "OK" if all(pr.get("layers") == ["F.Cu"] for k, pr in rep["pairs"].items() if pr.get("class") == "CAN_DIFF") else "ver tabela"),
      "", "## 3. Impedância estimada", "| Par | Camada | Ref. | h (mm) | εr | w (mm) | Z0 (Ω) | gap borda (mm) | Zdiff (Ω) | Nota |", "|---|---|---|---|---|---|---|---|---|---|"]
for e in rep["impedance_estimates"]:
    L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (e["pair"], e["layer"], e.get("ref", ""), e.get("h_mm", ""), e.get("er", ""), e.get("w_mm", ""), e.get("Z0_ohm", ""), e.get("gap_edge_mm", ""), e.get("Zdiff_ohm", ""), e.get("note", "")))
L += ["", "Alvos: CAN 120 Ω diferencial (ISO 11898-2), USB FS 90 Ω diferencial. Os pares do baseline Black Panda (herdados, trilhas travadas) não foram desenhados para impedância controlada; CAN clássico/FD a ≤ 5 Mbit/s com trilhas de poucos cm tolera o desvio (comprimento ≪ λ/10) — registado como NÃO VERIFICADO fisicamente.",
      "", "## 4. Planos", "| Rede | Camada | Polígonos | Área (mm²) | Maior (mm²) | Fracção do maior | Fragmentos < 5 mm² |", "|---|---|---|---|---|---|---|"]
for name, d in rep["planes"].items():
    for lay, v in d["layers"].items():
        L.append("| %s | %s | %d | %.1f | %.1f | %s | %d |" % (name, lay, v["outline_count"], v["area_mm2"], v["largest_mm2"], v["largest_fraction"], v["small_fragments_lt_5mm2"]))
    L.append("| %s | agrupamentos de conectividade | %s | | | | |" % (name, d["clusters"]))
L += ["", "Continuidade: 1 agrupamento = rede inteiramente ligada (zonas + vias + trilhas). Fragmentos pequenos do pour são cobre isolado da zona (não são erro de ligação; o DRC acusa `isolated_copper` só quando sem ligação alguma).",
      "", "## 5. Totais", "- Trilhas: %d · Vias: %d · Largura mínima de trilha: %.4f mm · Tamanhos de via (Ø/furo): %s" % (rep["totals"]["tracks"], rep["totals"]["vias"], rep["totals"]["min_track_width_mm"], rep["totals"]["via_sizes"]),
      "", "## 6. NÃO VERIFICADO", "- Impedância por medição (TDR) e stackup real do fabricante.", "- Meandros de compensação de skew: não gerados (skew medido acima; pares do baseline mantidos como estão).", "- Integridade de sinal CAN FD a 5 Mbit/s (tempo de subida vs. stubs): fora do âmbito desta medição."]
guarded_write_text(OUTPUT_ROOT / "hardware/research" / "step6-roteamento-impedancia.md", "\n".join(L) + "\n", tag="step6")
print(json.dumps({"pairs": {k: (v.get("skew_mm"), v.get("vias_on_pair"), v.get("layers")) for k, v in rep["pairs"].items()}, "planes": {k: v["clusters"][:5] for k, v in rep["planes"].items()}, "totals": rep["totals"]}, ensure_ascii=False, default=str))
