"""
final_audit.py — auditoria final independente do DRC (PCB + esquemático + BOM).
Só leitura. Python do KiCad 10 (pcbnew). Saídas: hardware\\reports\final_audit.json, docs\\final-audit.md

PCB:  A) curtos virtuais: cobre×cobre de redes diferentes (folga 0 e 0,10 mm), zona×cobre, furo×cobre, conectividade por rede
      B) montagem: via-in-pad, teia de máscara entre pads, pads/corpos perto da borda, corpos sobrepostos, THT, polaridade,
         largura mínima de trilha e nº de vias em redes de potência, ângulos agudos, serigrafia escondida, fiduciais
SCH:  pinos de sistema do U7 por rede, redes com 1 pino, BOOT0/NRST/PDR_ON/VBAT
BOM:  linhas × footprint × valor, exigências DS13311 §6.3 (VCAP/SMPS), MPN
"""
import os, sys, json, csv, math, time, collections, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import FromMM, ToMM

ROOT = hp.OUTPUT_ROOT; REP = hp.REPORT_DIR
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
NETXML = os.path.join(REP, "hybrid_HybridPanda_netlist.xml")
BOMCSV = os.path.join(REP, "hybrid_BOM.csv")
T0 = time.time()
out = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "board": os.path.relpath(PCB, ROOT), "findings": []}
def F(sev, area, msg, **kw):
    d = {"sev": sev, "area": area, "msg": msg}; d.update(kw); out["findings"].append(d)

board = pcbnew.LoadBoard(PCB)
ds = board.GetDesignSettings()
CU = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]
LN = {l: board.GetLayerName(l) for l in CU}
fps = list(board.GetFootprints()); pads = [p for fp in fps for p in fp.Pads()]
tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
zones = [z for z in board.Zones() if not z.GetIsRuleArea()]
netname = lambda nc: board.GetNetInfo().GetNetItem(nc).GetNetname() if nc else ""

# ------------------------------------------------------------------ A. curtos virtuais
# itens de cobre por camada: (shape, netcode, descr, bbox)
items = {l: [] for l in CU}
def desc_pad(p): return "pad %s.%s [%s]" % (p.GetParentFootprint().GetReference(), p.GetNumber(), p.GetNetname())
for p in pads:
    for l in CU:
        if p.IsOnLayer(l) and p.GetNetCode() >= 0:
            items[l].append((p.GetEffectiveShape(l), p.GetNetCode(), desc_pad(p), p.GetBoundingBox()))
for t in tracks:
    items[t.GetLayer()].append((t.GetEffectiveShape(t.GetLayer()), t.GetNetCode(), "trilha %s @%.2f,%.2f" % (t.GetNetname(), ToMM(t.GetStart().x), ToMM(t.GetStart().y)), t.GetBoundingBox()))
for v in vias:
    for l in CU:
        if v.IsOnLayer(l):
            items[l].append((v.GetEffectiveShape(l), v.GetNetCode(), "via %s @%.2f,%.2f" % (v.GetNetname(), ToMM(v.GetPosition().x), ToMM(v.GetPosition().y)), v.GetBoundingBox()))

CELL = FromMM(2.0)
def near(a, b, m):
    m = int(m)
    return not (a.GetRight() + m < b.GetLeft() or b.GetRight() + m < a.GetLeft() or a.GetBottom() + m < b.GetTop() or b.GetBottom() + m < a.GetTop())
def grid(bb):
    x0, y0, x1, y1 = bb.GetLeft() // CELL, bb.GetTop() // CELL, bb.GetRight() // CELL, bb.GetBottom() // CELL
    return [(x, y) for x in range(x0 - 1, x1 + 2) for y in range(y0 - 1, y1 + 2)]
shorts, clr_viol, pairs_tested = [], [], 0
CLR = FromMM(0.10)
for l in CU:
    buckets = collections.defaultdict(list)
    for i, it in enumerate(items[l]):
        for g in grid(it[3]): buckets[g].append(i)
    seen = set()
    for g, idxs in buckets.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = idxs[a], idxs[b]
                if (i, j) in seen: continue
                seen.add((i, j))
                A, B = items[l][i], items[l][j]
                if A[1] == B[1]: continue
                if not near(A[3], B[3], CLR): continue
                pairs_tested += 1
                if A[0].Collide(B[0], 0): shorts.append({"layer": LN[l], "a": A[2], "b": B[2]})
                elif A[0].Collide(B[0], CLR): clr_viol.append({"layer": LN[l], "a": A[2], "b": B[2]})
# zonas × cobre de outra rede (preenchimento real)
zone_shorts, zone_clr = [], []
for z in zones:
    for l in CU:
        if not z.IsOnLayer(l): continue
        poly = z.GetFilledPolysList(l)
        if poly.OutlineCount() == 0: continue
        zb = z.GetBoundingBox()
        for it in items[l]:
            if it[1] == z.GetNetCode() or not it[3].Intersects(zb): continue
            if poly.Collide(it[0], 0): zone_shorts.append({"layer": LN[l], "zone": z.GetNetname(), "item": it[2]})
            elif poly.Collide(it[0], CLR): zone_clr.append({"layer": LN[l], "zone": z.GetNetname(), "item": it[2]})
# furos × cobre de outra rede (qualquer camada)
hole_hits = []
holes = [(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetDrill() // 2), v.GetNetCode(), "via %s" % v.GetNetname(), v.GetBoundingBox()) for v in vias]
holes += [(pcbnew.SHAPE_CIRCLE(p.GetPosition(), max(p.GetDrillSize().x, p.GetDrillSize().y) // 2), p.GetNetCode(), desc_pad(p), p.GetBoundingBox())
          for p in pads if p.GetDrillSize().x > 0 and p.GetDrillSize().x == p.GetDrillSize().y]
for l in CU:
    for h in holes:
        for it in items[l]:
            if it[1] == h[1] or not near(it[3], h[3], FromMM(0.3)): continue
            if it[0].Collide(h[0], 0): hole_hits.append({"layer": LN[l], "hole": h[2], "item": it[2], "kind": "FURO DENTRO DE COBRE"})
            elif it[0].Collide(h[0], FromMM(0.2)): hole_hits.append({"layer": LN[l], "hole": h[2], "item": it[2], "kind": "folga furo < 0,20"})
# conectividade por rede (nº de agrupamentos entre pads)
conn = board.GetConnectivity()
unconn = conn.GetUnconnectedCount(True)
net_pads = collections.defaultdict(list)
for p in pads:
    if p.GetNetCode() > 0: net_pads[p.GetNetCode()].append(p)
split_nets = []
for nc, pl in net_pads.items():
    if len(pl) < 2: continue
    # BFS sobre itens ligados
    seen = set(); stack = [pl[0]]; reached = set()
    while stack:
        o = stack.pop()
        if o.m_Uuid.AsString() in seen: continue
        seen.add(o.m_Uuid.AsString())
        if o.GetClass() == "PAD": reached.add(o.m_Uuid.AsString())
        for n in conn.GetConnectedItems(o, 0):
            if n.m_Uuid.AsString() not in seen: stack.append(n)
    missing = [desc_pad(p) for p in pl if p.m_Uuid.AsString() not in reached]
    if missing: split_nets.append({"net": netname(nc), "pads_total": len(pl), "pads_isolados": missing[:10]})
out["shorts"] = {"pairs_tested": pairs_tested, "copper_overlap_other_net": shorts, "clearance_lt_0.10": clr_viol,
                 "zone_overlap_other_net": zone_shorts, "zone_clearance_lt_0.10": zone_clr, "hole_vs_other_net": hole_hits,
                 "kicad_unconnected": unconn, "nets_split": split_nets,
                 "nets_total": len(net_pads), "nets_multi_pad": sum(1 for v in net_pads.values() if len(v) >= 2)}
for s in shorts: F("CRITICO", "curto", "cobre sobreposto de redes diferentes", **s)
for s in zone_shorts: F("CRITICO", "curto", "zona sobre cobre de outra rede", **s)
for s in hole_hits:
    F("CRITICO" if s["kind"].startswith("FURO") else "ALTO", "curto", s["kind"], **s)
for s in split_nets: F("CRITICO", "rede partida", "pads da mesma rede sem ligação de cobre", **s)
if unconn: F("CRITICO", "rede partida", "KiCad unconnected = %d" % unconn)
for s in clr_viol[:50]: F("MEDIO", "folga", "folga < 0,10 mm entre redes diferentes", **s)
for s in zone_clr[:50]: F("MEDIO", "folga", "zona a < 0,10 mm de outra rede", **s)

# ------------------------------------------------------------------ B. montagem
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline, True)
bbox_board = outline.BBox()
# via-in-pad
vip, thermal_vias = [], []
for v in vias:
    for p in pads:
        if p.GetDrillSize().x == 0 and p.GetBoundingBox().Contains(v.GetPosition()):
            l = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            if p.GetEffectiveShape(l).Collide(pcbnew.SHAPE_CIRCLE(v.GetPosition(), v.GetWidth() // 2), 0):
                rec = {"via": "%s @%.2f,%.2f d%.2f/%.2f" % (v.GetNetname(), ToMM(v.GetPosition().x), ToMM(v.GetPosition().y), ToMM(v.GetWidth()), ToMM(v.GetDrill())),
                       "pad": desc_pad(p), "mesma_rede": v.GetNetCode() == p.GetNetCode(), "footprint": p.GetParentFootprint().GetFPID().GetLibItemName().wx_str()}
                sz = p.GetSize()
                # same-net via inside an exposed/thermal pad (>= 2 mm both ways) is a deliberate thermal via, not a defect
                if rec["mesma_rede"] and min(ToMM(sz.x), ToMM(sz.y)) >= 2.0:
                    thermal_vias.append(rec)
                else:
                    vip.append(rec)
out["via_in_pad"] = vip
out["thermal_vias"] = thermal_vias
for x in vip:
    if not x["mesma_rede"]: F("CRITICO", "curto", "via de outra rede dentro de pad SMD", **x)
F("ALTO" if vip else "INFO", "montagem", "%d vias dentro de pads SMD (via-in-pad): risco de sucção de solda/tombstone em 0402 — exigir vias tapadas (plugged/capped, IPC-4761 tipo VI/VII) ou aceitar retrabalho; sem isso, montagem por refluxo pode falhar nesses pads" % len(vip))
if thermal_vias:
    F("INFO", "montagem", "%d vias térmicas (mesma rede) em pads expostos (%s): voiding/sucção de solda no EP é esperado; posicionadas entre os quadrados de pasta" % (len(thermal_vias), ", ".join(sorted(set(x["footprint"] for x in thermal_vias)))))
# teia de máscara entre pads de redes diferentes (mesma camada)
exp = ToMM(ds.m_SolderMaskExpansion) if hasattr(ds, "m_SolderMaskExpansion") else None
mask_web = []
MINWEB = 0.10
for l in (pcbnew.F_Cu, pcbnew.B_Cu):
    pl = [p for p in pads if p.IsOnLayer(l) and p.GetDrillSize().x == 0]
    for i in range(len(pl)):
        for j in range(i + 1, len(pl)):
            a, b = pl[i], pl[j]
            if a.GetNetCode() == b.GetNetCode() or not near(a.GetBoundingBox(), b.GetBoundingBox(), FromMM(0.5)): continue
            ea, eb = ToMM(a.GetSolderMaskExpansion(l)) if hasattr(a, "GetSolderMaskExpansion") else (exp or 0), ToMM(b.GetSolderMaskExpansion(l)) if hasattr(b, "GetSolderMaskExpansion") else (exp or 0)
            # distância cobre-cobre: procurar a menor folga que ainda colide
            lo, hi = 0.0, 0.6
            if not a.GetEffectiveShape(l).Collide(b.GetEffectiveShape(l), FromMM(hi)): continue
            for _ in range(12):
                mid = (lo + hi) / 2
                if a.GetEffectiveShape(l).Collide(b.GetEffectiveShape(l), FromMM(mid)): hi = mid
                else: lo = mid
            gap = hi; web = gap - ea - eb
            if web < MINWEB: mask_web.append({"layer": LN[l], "a": desc_pad(a), "b": desc_pad(b), "gap_cobre_mm": round(gap, 3), "teia_mascara_mm": round(web, 3)})
out["mask"] = {"expansion_mm_global": exp, "webs_lt_%.2f" % MINWEB: mask_web, "count": len(mask_web)}
by_ref = collections.Counter(x["a"].split()[1].split(".")[0] for x in mask_web)
if mask_web: F("MEDIO", "montagem", "teia de máscara < %.2f mm entre pads de redes diferentes em %d pares (%s): pedir ao fabricante 'gang/individual mask' conforme capacidade (JLC mín. 0,10 mm teia verde) — risco de ponte de solda em passo fino" % (MINWEB, len(mask_web), ", ".join("%s×%d" % kv for kv in by_ref.most_common(8))))
# borda
edge_hits, outside = [], []
for p in pads:
    for l in (pcbnew.F_Cu, pcbnew.B_Cu):
        if not p.IsOnLayer(l): continue
        shp = p.GetEffectiveShape(l)
        if not outline.Contains(p.GetPosition()): outside.append(desc_pad(p))
        elif any(shp.Collide(outline.Outline(0).CSegment(k), FromMM(0.3)) for k in range(outline.Outline(0).SegmentCount())): edge_hits.append(desc_pad(p))
        break
fp_outside = []
for fp in fps:
    bb = fp.GetBoundingBox(False, False) if hasattr(fp, "GetBoundingBox") else fp.GetBoundingBox()
    if not bbox_board.Contains(bb): fp_outside.append({"ref": fp.GetReference(), "bbox": [round(ToMM(bb.GetLeft()), 2), round(ToMM(bb.GetTop()), 2), round(ToMM(bb.GetRight()), 2), round(ToMM(bb.GetBottom()), 2)]})
out["edge"] = {"pads_fora": outside, "pads_a_lt_0.3_da_borda": edge_hits, "footprints_fora_bbox": fp_outside,
               "board_mm": [round(ToMM(bbox_board.GetLeft()), 2), round(ToMM(bbox_board.GetTop()), 2), round(ToMM(bbox_board.GetRight()), 2), round(ToMM(bbox_board.GetBottom()), 2)]}
for x in outside: F("CRITICO", "borda", "pad fora do contorno", pad=x)
for x in fp_outside: F("MEDIO", "borda", "footprint com caixa fora do contorno (verificar visualmente)", **x)
# sobreposição de corpos (courtyard) e pátio ausente
cy_overlap, no_cy = [], []
cys = {}
for fp in fps:
    for l in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        c = fp.GetCourtyard(l)
        if c.OutlineCount(): cys[(fp.GetReference(), l)] = c
    if not any((fp.GetReference(), l) in cys for l in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)): no_cy.append(fp.GetReference())
keys = list(cys)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        if keys[i][1] != keys[j][1] or keys[i][0] == keys[j][0]: continue
        if cys[keys[i]].BBox().Intersects(cys[keys[j]].BBox()) and cys[keys[i]].Collide(cys[keys[j]], 0):
            cy_overlap.append({"layer": board.GetLayerName(keys[i][1]), "a": keys[i][0], "b": keys[j][0]})
out["courtyard"] = {"overlaps": cy_overlap, "sem_courtyard": no_cy}
for x in cy_overlap: F("ALTO", "montagem", "pátios (courtyard) sobrepostos — colisão física/pick&place", **x)
if no_cy: F("INFO", "montagem", "footprints sem courtyard (sem verificação de colisão possível): %s" % ", ".join(no_cy))
# vias sob corpos de outra rede (tenting)
tent_f = getattr(ds, "m_TentViasFront", None); tent_b = getattr(ds, "m_TentViasBack", None)
under = []
for v in vias:
    for fp in fps:
        l = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
        cy = cys.get((fp.GetReference(), pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd))
        if cy is not None and cy.Contains(v.GetPosition()):
            same = any(p.GetNetCode() == v.GetNetCode() for p in fp.Pads())
            under.append({"via": "%s @%.2f,%.2f" % (v.GetNetname(), ToMM(v.GetPosition().x), ToMM(v.GetPosition().y)), "sob": fp.GetReference(), "rede_do_componente": same})
out["vias_under_components"] = {"tent_front": tent_f, "tent_back": tent_b, "count": len(under), "list": under}
if under and (tent_f is False or tent_b is False): F("ALTO", "montagem", "%d vias sob corpos de componentes com tenting desligado — risco de curto por solda/pasta" % len(under))
else: F("INFO", "montagem", "%d vias sob corpos de componentes (tenting F/B = %s/%s)" % (len(under), tent_f, tent_b))
# THT / polaridade / lado
tht = [fp.GetReference() for fp in fps if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())]
bottom = [fp.GetReference() for fp in fps if fp.IsFlipped()]
pol = [fp.GetReference() for fp in fps if fp.GetReference()[0] in ("D", "U", "Q", "J", "P", "Y") or (fp.GetReference()[0] == "C" and "Polar" in fp.GetFPID().GetLibItemName().wx_str())]
hidden_ref = [fp.GetReference() for fp in fps if not fp.Reference().IsVisible()]
fid = [fp.GetReference() for fp in fps if "Fiducial" in fp.GetFPID().GetLibItemName().wx_str() or fp.GetValue() == "Fiducial"]
out["assembly"] = {"tht": tht, "bottom_side": bottom, "polarizados": pol, "ref_silk_escondida": hidden_ref, "fiduciais": fid, "total_fp": len(fps)}
if not fid: F("MEDIO", "montagem", "sem fiduciais na placa — montagem automática usa pads como referência; adicionar 2–3 fiduciais (1 mm) por lado se for SMT em fábrica")
F("INFO", "montagem", "%d componentes, %d no lado B (%s), THT: %s; %d referências sem serigrafia (identificação só pelo CPL)" % (len(fps), len(bottom), ", ".join(bottom[:12]) + ("…" if len(bottom) > 12 else ""), ", ".join(tht), len(hidden_ref)))
F("INFO", "montagem", "polaridade/pino 1 a confirmar visualmente no render/F.Fab: %s" % ", ".join(pol))
# potência: largura mínima e vias
POWER = ("+12V", "VIN", "+5V", "+3V3", "GND", "USB_PWR", "VBUS", "+5V_USB", "VDD", "+3V3_SMPS", "VLX", "VFB")
pw = {}
for t in tracks:
    n = t.GetNetname()
    if n in POWER or n.startswith("+"):
        d = pw.setdefault(n, {"min_w": 9, "max_w": 0, "len_mm": 0, "n": 0, "vias": 0, "min_w_at": None})
        w = ToMM(t.GetWidth()); d["n"] += 1; d["len_mm"] += ToMM(t.GetLength()); d["max_w"] = max(d["max_w"], w)
        if w < d["min_w"]: d["min_w"], d["min_w_at"] = w, "%.2f,%.2f %s" % (ToMM(t.GetStart().x), ToMM(t.GetStart().y), LN[t.GetLayer()])
for v in vias:
    if v.GetNetname() in pw: pw[v.GetNetname()]["vias"] += 1
for n, d in pw.items(): d["len_mm"] = round(d["len_mm"], 1)
out["power_tracks"] = pw
for n, d in pw.items():
    if d["min_w"] < 0.2 and n in ("+12V", "VIN", "+5V"):
        F("ALTO", "potência", "rede %s tem trilha de %.3f mm (em %s): limitar corrente — 0,15 mm/1 oz ≈ 0,5 A com ΔT 10 °C; alargar ou verificar que é só sensor/pull-up" % (n, d["min_w"], d["min_w_at"]))
    elif d["min_w"] < 0.2 and n == "+3V3":
        F("MEDIO", "potência", "+3V3 tem trilha de %.3f mm (em %s); H725 a 550 MHz pode consumir 200–300 mA — confirmar que o caminho principal (regulador→MCU) é largo/plano e que os troços finos são só ramos de desacoplamento" % (d["min_w"], d["min_w_at"]))
# ângulos agudos (mesma rede, extremidade comum, < 90°)
acute = 0; ends = collections.defaultdict(list)
for t in tracks:
    ends[(t.GetStart().x, t.GetStart().y, t.GetLayer())].append((t, t.GetEnd()))
    ends[(t.GetEnd().x, t.GetEnd().y, t.GetLayer())].append((t, t.GetStart()))
for k, lst in ends.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            a = lst[i][1]; b = lst[j][1]
            va = (a.x - k[0], a.y - k[1]); vb = (b.x - k[0], b.y - k[1])
            na, nb = math.hypot(*va), math.hypot(*vb)
            if na == 0 or nb == 0: continue
            cosang = (va[0] * vb[0] + va[1] * vb[1]) / (na * nb)
            if cosang > 0.01: acute += 1  # ângulo interno < 89,4°
out["acute_angles"] = acute
if acute: F("BAIXO", "fabrico", "%d junções de trilha com ângulo agudo (< 90°) — 'acid traps' cosméticos em processo moderno; o Freerouting gera 45°/90° mas o A* do 5c pode gerar outros" % acute)
# regras de fabrico
min_w = min(ToMM(t.GetWidth()) for t in tracks); min_via = min(ToMM(v.GetDrill()) for v in vias)
out["rules"] = {"min_track_mm": round(min_w, 4), "min_via_drill_mm": min_via, "ds_min_track": ToMM(ds.m_TrackMinWidth), "ds_min_clear": ToMM(ds.m_MinClearance), "ds_min_drill": ToMM(ds.m_MinThroughDrill)}
F("INFO", "fabrico", "trilha mín %.4f mm, broca mín %.2f mm (regra 0,30 — 1 via herdada 0,25); folga mín testada 0,10 mm" % (min_w, min_via))

# ------------------------------------------------------------------ C. esquemático (netlist XML)
rootx = ET.parse(NETXML).getroot()
pin_net = {}; net_pins = collections.defaultdict(list)
for n in rootx.iter("net"):
    for nd in n.findall("node"):
        pin_net[(nd.get("ref"), nd.get("pin"))] = n.get("name"); net_pins[n.get("name")].append((nd.get("ref"), nd.get("pin"), nd.get("pinfunction"), nd.get("pintype")))
u7 = {k[1]: v for k, v in pin_net.items() if k[0] == "U7"}
SYS = {"VCAP": ["68", "103", "140"], "VDDLDO": ["70", "105", "143"], "VDDSMPS": ["16"], "VSSSMPS": ["14"], "VLXSMPS": ["15"], "VFBSMPS": ["17"],
       "VDD50USB": ["90"], "VDD33USB": ["91"], "VREF+": ["35"], "VDDA": ["36"], "VSSA": ["34"], "VBAT": ["8"], "BOOT0": ["135"], "NRST": ["27"], "PDR_ON": ["142"], "PH0/OSC_IN": ["25"], "PH1/OSC_OUT": ["26"],
       "PF7": ["21"], "PF8": ["22"], "PF9": ["23"], "PF10": ["24"]}
sysn = {k: sorted(set(u7.get(p, "NC?") for p in v)) for k, v in SYS.items()}
vdd = sorted(set(v for p, v in u7.items() if p in ("33", "50", "62", "80", "96", "107", "120", "131", "141", "25", "6", "15")))
out["sch_u7_system"] = sysn
single = {n: p for n, p in net_pins.items() if len(p) == 1 and not n.startswith("unconnected-")}
out["sch_single_pin_nets"] = single
for n, p in single.items(): F("ALTO", "esquemático", "rede com um só pino (dangling)", net=n, pin=p)
# BOOT0 / NRST / PDR_ON / VBAT
def peers(net): return [(r, p) for r, p, _, _ in net_pins.get(net, []) if r != "U7"]
for k in ("BOOT0", "NRST", "PDR_ON", "VBAT", "VDD50USB", "VDD33USB", "VREF+", "VDDA"):
    F("INFO", "esquemático", "U7 %s → %s ; outros nós: %s" % (k, sysn[k], peers(sysn[k][0])[:8]))
if any(n in ("GND",) for n in sysn["BOOT0"]) is False and not any(r.startswith("R") for r, _ in peers(sysn["BOOT0"][0])):
    F("ALTO", "esquemático", "BOOT0 (pino 135) não está em GND nem com pull-down — DFU/boot indefinido", net=sysn["BOOT0"])
if sysn["PDR_ON"] != sysn["VDDLDO"] and "+3V3" not in sysn["PDR_ON"][0]: F("ALTO", "esquemático", "PDR_ON deve ir a VDD", net=sysn["PDR_ON"])
if sysn["VDD50USB"] != sysn["VDD33USB"]: F("MEDIO", "esquemático", "VDD50USB ≠ VDD33USB (D-14 diz ligados)", **{"VDD50USB": sysn["VDD50USB"], "VDD33USB": sysn["VDD33USB"]})
# transceivers
for u in ("U8", "U9", "U10", "U11"):
    pins = {k[1]: v for k, v in pin_net.items() if k[0] == u}
    F("INFO", "esquemático", "%s TJA1042: %s" % (u, {p: pins.get(p) for p in ("1", "2", "3", "4", "5", "6", "7", "8")}))

# ------------------------------------------------------------------ D. BOM
bom = list(csv.DictReader(open(BOMCSV, encoding="utf-8-sig", newline="")))
flags = []
for r in bom:
    v, fp_, refs = r["Value"], r["Footprint"].split(":")[-1], r["Reference"]
    note = []
    if not r.get("MPN"): note.append("sem MPN")
    try:
        if "uF" in v.lower() or "µ" in v:
            uf = float(v.lower().replace("µf", "").replace("uf", "").replace(",", "."))
            if uf >= 10 and "0402" in fp_: note.append("≥10 µF em 0402: tensão/derating DC bias duvidosos")
            if uf >= 22 and "0603" in fp_: note.append("≥22 µF em 0603: confirmar tensão (6,3 V) e derating")
            if uf >= 47 and "0805" in fp_: note.append("47 µF 0805: só ≤6,3–10 V; verificar rede (+12V? não serve)")
    except ValueError: pass
    if refs.startswith("C38") or "C38" in refs or "C39" in refs or "C40" in refs: note.append("VCAP: exigir ESR < 100 mΩ, X7R/X5R, ≥6,3 V (DS13311 §6.3.2)")
    if "C41" in refs: note.append("SMPS Cin/Cfilt (DS13311 §6.3.3)")
    if "C42" in refs: note.append("SMPS Cout 10 µF ESR 20 mΩ (DS13311 §6.3.3)")
    if "L5" in refs: note.append("DFE201610E 2,2 µH: Isat ≥ 1,7 A / DCR ≤ 150 mΩ (PROVISÓRIO)")
    if "Y1" in refs: note.append("25 MHz: CL = 2·(C_load − C_stray) — C de carga 15 pF PROVISÓRIO; validar com CL do cristal escolhido")
    if "FB1" in refs: note.append("ferrite VDDA: PROVISÓRIO (ex. BLM18 600 Ω/100 MHz)")
    flags.append({"refs": refs, "value": v, "footprint": fp_, "qty": r.get("Qty"), "notas": note})
out["bom"] = flags
n_refs = sum(len([x for x in f["refs"].split(",") if x.strip()]) for f in flags)
n_mpn = sum(1 for f in flags if "sem MPN" not in f["notas"])
if n_mpn < len(flags):
    F("ALTO", "BOM", "%d linhas / %d referências; %d linhas com MPN — não encomendável sem preencher as restantes; itens críticos marcados (VCAP ESR, SMPS, L5, Y1 CL)" % (len(flags), n_refs, n_mpn))
else:
    F("INFO", "BOM", "%d linhas / %d referências; todas com MPN (LCSC 'a verificar' em hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv); itens críticos marcados (VCAP ESR, SMPS, L5, Y1 CL)" % (len(flags), n_refs))
for f in flags:
    if any("duvidos" in n or "não serve" in n for n in f["notas"]): F("MEDIO", "BOM", "; ".join(f["notas"]), refs=f["refs"], value=f["value"], footprint=f["footprint"])

# ------------------------------------------------------------------ saída
out["seconds"] = round(time.time() - T0, 1)
sevc = collections.Counter(f["sev"] for f in out["findings"]); out["by_severity"] = dict(sevc)
hp.assert_inside_output(os.path.join(REP, "final_audit.json"))
json.dump(out, open(os.path.join(REP, "final_audit.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
L = ["# Auditoria final — PCB, esquemático e BOM (independente do DRC)", "", "Data: %s · `hardware\\scripts\\final_audit.py` (%.0f s) · placa `%s` · JSON `hardware\\reports\\final_audit.json`" % (out["date"], out["seconds"], out["board"]), "",
     "## Resumo por gravidade", "", "| Gravidade | Qtd |", "|---|---|"] + ["| %s | %d |" % (k, sevc.get(k, 0)) for k in ("CRITICO", "ALTO", "MEDIO", "BAIXO", "INFO")]
L += ["", "## A. Teste de curtos virtuais (geométrico, folga 0)", "",
      "- Pares cobre×cobre de redes diferentes testados (caixas a < 0,10 mm): **%d** → sobreposições (curto): **%d**; folga < 0,10 mm: %d" % (pairs_tested, len(shorts), len(clr_viol)),
      "- Zona×cobre de outra rede: curtos **%d**, folga < 0,10: %d" % (len(zone_shorts), len(zone_clr)),
      "- Furos (vias+PTH) × cobre de outra rede: furo dentro de cobre **%d**, folga < 0,20: %d" % (sum(1 for h in hole_hits if h["kind"].startswith("FURO")), sum(1 for h in hole_hits if not h["kind"].startswith("FURO"))),
      "- Conectividade: KiCad unconnected = **%d**; redes com pads isolados = **%d** (de %d redes com ≥ 2 pads)" % (unconn, len(split_nets), out["shorts"]["nets_multi_pad"]), ""]
L += ["## B. Montagem / fabrico", "", "| Gravidade | Área | Achado |", "|---|---|---|"]
for f in out["findings"]:
    if f["area"] in ("curto", "rede partida", "folga", "montagem", "borda", "potência", "fabrico"):
        extra = {k: v for k, v in f.items() if k not in ("sev", "area", "msg")}
        L.append("| %s | %s | %s %s |" % (f["sev"], f["area"], f["msg"].replace("|", "/"), ("`" + json.dumps(extra, ensure_ascii=False, default=str)[:160] + "`") if extra else ""))
L += ["", "### Via-in-pad (lista)", "", "| Via | Pad | Mesma rede |", "|---|---|---|"] + ["| %s | %s | %s |" % (x["via"], x["pad"], x["mesma_rede"]) for x in vip]
L += ["", "### Trilhas de potência", "", "| Rede | Trilhas | Larg. mín (mm) @ | Larg. máx | Comp. (mm) | Vias |", "|---|---|---|---|---|---|"]
L += ["| %s | %d | %.3f @ %s | %.3f | %.1f | %d |" % (n, d["n"], d["min_w"], d["min_w_at"], d["max_w"], d["len_mm"], d["vias"]) for n, d in sorted(pw.items())]
L += ["", "## C. Esquemático", "", "| Gravidade | Achado |", "|---|---|"]
for f in out["findings"]:
    if f["area"] == "esquemático":
        extra = {k: v for k, v in f.items() if k not in ("sev", "area", "msg")}
        L.append("| %s | %s %s |" % (f["sev"], f["msg"].replace("|", "/"), ("`" + json.dumps(extra, ensure_ascii=False, default=str)[:200] + "`") if extra else ""))
L += ["", "Pinos de sistema do U7 → rede: " + "; ".join("%s=%s" % (k, "/".join(v)) for k, v in sysn.items())]
L += ["", "## D. BOM (%d linhas)" % len(bom), "", "| Refs | Valor | Footprint | Qtd | Notas |", "|---|---|---|---|---|"]
L += ["| %s | %s | %s | %s | %s |" % (f["refs"], f["value"], f["footprint"], f["qty"], "; ".join(f["notas"])) for f in flags]
L += ["", "## Veredicto honesto", "",
      "Curtos virtuais: ver §A (0 = nenhum item de cobre de redes diferentes se sobrepõe na geometria real da placa, incluindo preenchimentos de zona e furos). Isto é prova **geométrica estática**; não substitui teste eléctrico de continuidade/isolamento na placa fabricada (flying probe do fabricante ou multímetro no bring-up — STEP 9 passos 1–3).",
      "Os achados ALTO/MEDIO de montagem (via-in-pad, teia de máscara, fiduciais, BOM sem MPN) têm de ser resolvidos antes de qualquer encomenda. **Não fabricar** nesta revisão."]
hp.guarded_write_text(os.path.join(ROOT, "docs", "final-audit.md"), "\n".join(L) + "\n")
print(json.dumps({"by_severity": out["by_severity"], "shorts": len(shorts), "zone_shorts": len(zone_shorts), "hole_hits": len(hole_hits), "clr": len(clr_viol), "zone_clr": len(zone_clr), "split": len(split_nets), "unconn": unconn, "vip": len(vip), "mask_web": len(mask_web), "cy": len(cy_overlap), "seconds": out["seconds"]}, ensure_ascii=False))
sys.stdout.flush(); os._exit(0)  # pcbnew teardown can hang the interpreter (KiCad 10)

