"""vpcb_a5_impedance.py - A5: microstrip impedance of the USB and CAN pairs with the file stackup and with JLCPCB JLC7628.

Autor: Bruno Costa

Formulas (implemented below, no external packages):
  * single microstrip Z0 and eps_eff: Hammerstad & Jensen 1980 ("Accurate models for microstrip computer-aided design",
    IEEE MTT-S 1980) with the Wheeler/HJ strip-thickness correction (W1 = W + dW1, Wr = W + dWr) - same closed forms used by
    IPC-2141A sec. 4 and by QUCS msline.cpp;
  * coupled microstrip (edge-coupled, same layer): Kirschning & Jansen 1984 quasi-static even/odd model
    ("Accurate wide-range design equations for the frequency-dependent characteristic of parallel coupled microstrip
    lines", IEEE Trans. MTT-32 no.1) with the Jansen finite-thickness correction; Zdiff = 2 * Zodd, Zcm = Zeven / 2;
  * cross-check: IPC-2141 approximation Zdiff ~= 2 Z0 (1 - 0.48 exp(-0.96 s/h)).
Outputs: hardware/reports/verification-pcb/impedance.md and impedance.json. Read-only unless called with --apply-can (then the CAN_DIFF
netclass in the .kicad_pro and the 0.25 mm CAN segments in the .kicad_pcb are narrowed to the computed width).
"""
import json
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp

ROOT = str(hp.OUTPUT_ROOT)
PCB = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pcb")
PRO = os.path.join(ROOT, "hardware", "hybrid-panda", "HybridPanda.kicad_pro")
OUTD = os.path.join(ROOT, "hardware", "reports", "verification-pcb")
Z_F0 = 376.730313668
MIN_TRACK = 0.127          # board min_track_width (kicad_pro) ~ JLC 5 mil
MIN_GAP = 0.127            # JLC min spacing 5 mil (board rule 0.10 mm)


# ---------------------------------------------------------------- single microstrip (Hammerstad-Jensen)
def _hj_ab(u, er):
    a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    return a, b


def _hj_er(u, er):
    a, b = _hj_ab(u, er)
    return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)


def _hj_zl(u):
    fu = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / u) ** 0.7528))
    return Z_F0 / (2 * math.pi) * math.log(fu / u + math.sqrt(1 + (2 / u) ** 2))


def microstrip(w, h, t, er):
    """Return (Z0, eps_eff) for a single microstrip, w/h/t in mm (HJ 1980 with thickness correction)."""
    u = w / h
    if t > 0:
        th = t / h
        dw1 = th / math.pi * math.log(1 + 4 * math.e / (th * (1 / math.tanh(math.sqrt(6.517 * u))) ** 2))
        dwr = 0.5 * dw1 * (1 + 1 / math.cosh(math.sqrt(er - 1)))
    else:
        dw1 = dwr = 0.0
    u1, ur = u + dw1, u + dwr
    ereff = _hj_er(ur, er) * (_hj_zl(u1) / _hj_zl(ur)) ** 2
    z0 = _hj_zl(ur) / math.sqrt(ereff)
    return z0, ereff


# ---------------------------------------------------------------- coupled microstrip (Kirschning-Jansen 1984)
def coupled_microstrip(w, h, s, t, er):
    """Return dict(Zeven, Zodd, Zdiff, Zcm, ereff_e, ereff_o) for edge-coupled microstrip; w/h/s/t in mm."""
    u, g = w / h, s / h
    ue = uo = u
    if t > 0 and s > 10 * (2 * t):
        dw = 0.0
        if u >= 1 / (2 * math.pi) and 1 / (2 * math.pi) > 2 * t / h:
            dw = t * (1 + math.log(2 * h / t)) / math.pi
        elif w > 2 * t:
            dw = t * (1 + math.log(4 * math.pi * w / t)) / math.pi
        dt = 2 * t * h / s / er
        we = w + dw * (1 - 0.5 * math.exp(-0.69 * dw / dt))
        wo = we + dt
        ue, uo = we / h, wo / h
    v = ue * (20 + g * g) / (10 + g * g) + g * math.exp(-g)
    er_e = _hj_er(v, er)
    er_s = _hj_er(uo, er)
    d = 0.593 + 0.694 * math.exp(-0.562 * uo)
    bo = 0.747 * er / (0.15 + er)
    co = bo - (bo - 0.207) * math.exp(-0.414 * uo)
    ao = 0.7287 * (er_s - (er + 1) / 2) * (1 - math.exp(-0.179 * uo))
    er_o = ((er + 1) / 2 + ao - er_s) * math.exp(-co * g ** d) + er_s
    zl1 = _hj_zl(u) / math.sqrt(er_s)
    q1 = 0.8695 * ue ** 0.194
    q2 = 1 + 0.7519 * g + 0.189 * g ** 2.31
    q3 = 0.1975 + (16.6 + (8.4 / g) ** 6) ** -0.387 + math.log(g ** 10 / (1 + (g / 3.4) ** 10)) / 241
    q4 = q1 / q2 * 2 / (math.exp(-g) * ue ** q3 + (2 - math.exp(-g)) * ue ** -q3)
    z_e = math.sqrt(er_s / er_e) * zl1 / (1 - zl1 * math.sqrt(er_s) * q4 / Z_F0)
    q5 = 1.794 + 1.14 * math.log(1 + 0.638 / (g + 0.517 * g ** 2.43))
    q6 = 0.2305 + math.log(g ** 10 / (1 + (g / 5.8) ** 10)) / 281.3 + math.log(1 + 0.598 * g ** 1.154) / 5.1
    q7 = (10 + 190 * g * g) / (1 + 82.3 * g ** 3)
    q8 = math.exp(-6.5 - 0.95 * math.log(g) - (g / 0.15) ** 5)
    q9 = math.log(q7) * (q8 + 1 / 16.5)
    q10 = (q2 * q4 - q5 * math.exp(math.log(uo) * q6 * uo ** -q9)) / q2
    z_o = math.sqrt(er_s / er_o) * zl1 / (1 - zl1 * math.sqrt(er_s) * q10 / Z_F0)
    return {"Zeven": z_e, "Zodd": z_o, "Zdiff": 2 * z_o, "Zcm": z_e / 2, "ereff_e": er_e, "ereff_o": er_o}


def ipc2141_zdiff(w, h, s, t, er):
    z0, _ = microstrip(w, h, t, er)
    return 2 * z0 * (1 - 0.48 * math.exp(-0.96 * s / h))


def solve_width(target, h, s, t, er, lo=0.08, hi=1.5):
    """Bisection on w for Zdiff(w, s) = target. Returns None if not bracketed."""
    f = lambda w: coupled_microstrip(w, h, s, t, er)["Zdiff"] - target
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def solve_gap(target, w, h, t, er, lo=0.08, hi=3.0):
    f = lambda s: coupled_microstrip(w, h, s, t, er)["Zdiff"] - target
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- stackups
def file_stackup():
    txt = open(PCB, encoding="utf-8").read()
    m = re.search(r"\(stackup(.*?)\n\s*\)\n\s*\(pad_to_mask", txt, re.S)
    stack = []
    for lm in re.finditer(r'\(layer "([^"]+)"(.*?)(?=\(layer "|\Z)', m.group(1), re.S):
        name, body = lm.group(1), lm.group(2)
        th = re.search(r"\(thickness ([\d.]+)", body)
        er = re.search(r"\(epsilon_r ([\d.]+)", body)
        stack.append((name, float(th.group(1)) if th else None, float(er.group(1)) if er else None))
    names = [s[0] for s in stack]
    i, j = names.index("F.Cu"), names.index("In1.Cu")
    h = sum(s[1] for s in stack[i + 1:j])
    er = [s[2] for s in stack[i + 1:j] if s[2]][0]
    t = stack[i][1]
    return {"name": "file (.kicad_pcb stackup)", "h_mm": h, "er": er, "t_mm": t, "layers": stack,
            "note": "outer Cu 35 um, prepreg 0.2 mm er 4.5, core 1.065 mm, inner Cu 17.5 um; total 1.59 mm"}


JLC7628 = {"name": "JLCPCB JLC7628 4-layer 1.6 mm", "h_mm": 0.2104, "er": 4.4, "er_lowfreq": 4.6, "t_mm": 0.035,
           "note": "outer Cu 1 oz (0.035 mm), prepreg 7628 0.2104 mm, er 4.4 @ 1 GHz (4.6 low frequency), core 1.065 mm, inner Cu 0.5 oz; "
                   "values from the JLCPCB impedance-calculator stackup table (not a fabricator-confirmed stackup for this order)"}


def main():
    os.makedirs(OUTD, exist_ok=True)
    pro = json.load(open(PRO, encoding="utf-8"))
    classes = {c["name"]: c for c in pro["net_settings"]["classes"]}
    can = classes["CAN_DIFF"]
    usb = classes["USB"]
    stacks = [file_stackup(), JLC7628]
    rep = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "stackups": [], "netclasses_before": {k: {x: classes[k][x] for x in ("track_width", "diff_pair_width", "diff_pair_gap")} for k in ("CAN_DIFF", "USB")}}
    for st in stacks:
        h, er, t = st["h_mm"], st["er"], st["t_mm"]
        ers = [er] + ([st["er_lowfreq"]] if st.get("er_lowfreq") else [])
        row = {"name": st["name"], "h_mm": h, "t_mm": t, "er_cases": []}
        for e in ers:
            case = {"er": e, "single": [], "pairs": [], "solutions": {}}
            for w in (0.127, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50):
                z, ee = microstrip(w, h, t, e)
                case["single"].append({"w": w, "Z0": round(z, 1), "ereff": round(ee, 2)})
            for label, w, s in (("CAN_DIFF rule now", can["diff_pair_width"], can["diff_pair_gap"]),
                                ("USB rule now", usb["diff_pair_width"], usb["diff_pair_gap"]),
                                ("0.20/0.15", 0.20, 0.15), ("0.25/0.15", 0.25, 0.15), ("0.28/0.15", 0.28, 0.15), ("0.30/0.15", 0.30, 0.15),
                                ("0.30/0.20", 0.30, 0.20), ("0.127/0.30", 0.127, 0.30), ("0.127/0.50", 0.127, 0.50), ("0.15/0.40", 0.15, 0.40)):
                kj = coupled_microstrip(w, h, s, t, e)
                case["pairs"].append({"label": label, "w": w, "s": s, "Zodd": round(kj["Zodd"], 1), "Zeven": round(kj["Zeven"], 1),
                                      "Zdiff_KJ": round(kj["Zdiff"], 1), "Zdiff_IPC2141": round(ipc2141_zdiff(w, h, s, t, e), 1),
                                      "Zcm": round(kj["Zcm"], 1)})
            for target in (90, 120):
                sols = []
                for s in (0.127, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
                    w = solve_width(target, h, s, t, e)
                    sols.append({"s": s, "w": round(w, 3) if w else None, "feasible": bool(w and w >= MIN_TRACK)})
                g_for_rule = solve_gap(target, can["diff_pair_width"], h, t, e)
                case["solutions"][str(target)] = {"by_gap": sols, "gap_for_w%.2f" % can["diff_pair_width"]: round(g_for_rule, 3) if g_for_rule else None}
            row["er_cases"].append(case)
        rep["stackups"].append(row)
    # recommendation (JLC7628, er 4.4): 90 ohm at s = 0.15 mm, width rounded to 0.01 mm
    jl = rep["stackups"][1]["er_cases"][0]
    w90 = solve_width(90, JLC7628["h_mm"], 0.15, JLC7628["t_mm"], 4.4)
    w90r = round(w90 + 1e-9, 2)
    chk = coupled_microstrip(w90r, JLC7628["h_mm"], 0.15, JLC7628["t_mm"], 4.4)
    chk46 = coupled_microstrip(w90r, JLC7628["h_mm"], 0.15, JLC7628["t_mm"], 4.6)
    chkf = coupled_microstrip(w90r, stacks[0]["h_mm"], 0.15, stacks[0]["t_mm"], stacks[0]["er"])
    rep["usb_recommendation"] = {"w_mm": w90r, "s_mm": 0.15, "Zdiff_JLC7628_er4.4": round(chk["Zdiff"], 1), "Zdiff_JLC7628_er4.6": round(chk46["Zdiff"], 1),
                                 "Zdiff_file_stackup": round(chkf["Zdiff"], 1), "Zcm": round(chk["Zcm"], 1)}
    w120 = {s: solve_width(120, JLC7628["h_mm"], s, JLC7628["t_mm"], 4.4) for s in (0.20, 0.23, 0.30, 0.40, 0.50)}
    # keep the present pair centre spacing (0.25 + 0.20 = 0.45 mm) and only narrow the copper: w + s = 0.45
    pitch = can["diff_pair_width"] + can["diff_pair_gap"]
    f = lambda w: coupled_microstrip(w, JLC7628["h_mm"], pitch - w, JLC7628["t_mm"], 4.4)["Zdiff"] - 120
    lo, hi = 0.127, pitch - 0.127
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    w_can = round((lo + hi) / 2 + 1e-9, 2)
    s_can = round(pitch - w_can, 2)
    c44 = coupled_microstrip(w_can, JLC7628["h_mm"], s_can, JLC7628["t_mm"], 4.4)["Zdiff"]
    c46 = coupled_microstrip(w_can, JLC7628["h_mm"], s_can, JLC7628["t_mm"], 4.6)["Zdiff"]
    cf = coupled_microstrip(w_can, stacks[0]["h_mm"], s_can, stacks[0]["t_mm"], stacks[0]["er"])["Zdiff"]
    rep["can_recommendation"] = {"solutions_120": {str(s): (round(w, 3) if w else None) for s, w in w120.items()},
                                 "feasible_at_min_track": any(w and w >= MIN_TRACK for w in w120.values()),
                                 "w_mm": w_can, "s_mm": s_can, "pitch_mm": pitch, "Zdiff_JLC7628_er4.4": round(c44, 1),
                                 "Zdiff_JLC7628_er4.6": round(c46, 1), "Zdiff_file_stackup": round(cf, 1)}
    if "--apply-can" in sys.argv:
        rep["can_applied"] = apply_can(w_can, s_can, can["diff_pair_width"])
    json.dump(rep, open(os.path.join(OUTD, "impedance.json"), "w", encoding="utf-8"), indent=1)
    write_md(rep, stacks, can, usb)


def apply_can(w_new, s_new, w_old):
    """Set the CAN_DIFF netclass to w_new/s_new and narrow the CAN track segments that are at w_old to w_new.
    Narrowing never reduces a clearance, so it cannot create clearance DRC items. Returns a summary dict."""
    import pcbnew
    pro = json.load(open(PRO, encoding="utf-8"))
    for c in pro["net_settings"]["classes"]:
        if c["name"] == "CAN_DIFF":
            c["track_width"] = w_new
            c["diff_pair_width"] = w_new
            c["diff_pair_gap"] = s_new
    hp.assert_inside_output(PRO)
    json.dump(pro, open(PRO, "w", encoding="utf-8"), indent=2)
    board = pcbnew.LoadBoard(PCB)
    changed = {}
    for t in board.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_TRACK" and n.startswith("BUS") and n.endswith(("_H", "_L")) and abs(pcbnew.ToMM(t.GetWidth()) - w_old) < 1e-6:
            t.SetWidth(pcbnew.FromMM(w_new))
            changed[n] = changed.get(n, 0) + 1
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    hp.assert_inside_output(PCB)
    board.Save(PCB)
    return {"netclass": {"track_width": w_new, "diff_pair_width": w_new, "diff_pair_gap": s_new}, "segments_narrowed": changed, "from_width": w_old}


def write_md(rep, stacks, can, usb):
    L = ["# A5 - Impedance of the USB and CAN pairs (file stackup vs JLCPCB JLC7628)", "",
         "Date: %s. Script: `hardware/scripts/vpcb_a5_impedance.py` (read-only). Data: `impedance.json`." % rep["date"], "",
         "## Method", "",
         "- Single microstrip (outer layer over the first inner plane): Hammerstad and Jensen 1980 closed forms for Z0 and eps_eff, with the",
         "  Wheeler/HJ strip-thickness correction (the same equations referenced by IPC-2141A section 4 and used in `step6_reports.py`).",
         "- Edge-coupled pair: Kirschning and Jansen 1984 quasi-static even/odd-mode model (IEEE Trans. MTT-32, with the Jansen finite-thickness",
         "  correction); Zdiff = 2 Zodd, Zcm = Zeven / 2. Cross-check column: IPC-2141 approximation Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 s/h)).",
         "- Reference plane assumed directly under the outer layer (F.Cu over In1.Cu, B.Cu over In2.Cu). On this board In1.Cu is GND outside the",
         "  +3V3/+5V pours (see `step6_reports.py`), In2.Cu is a continuous GND plane; the numbers are the same for both outer layers because",
         "  the prepreg is symmetric. KiCad DRC does not check impedance; nothing here is measured.", "",
         "## Stackups", "", "| Case | h (outer Cu to first plane) | er | outer Cu t | Note |", "|---|---|---|---|---|"]
    for st in stacks:
        L.append("| %s | %.4f mm | %s | %.3f mm | %s |" % (st["name"], st["h_mm"], st["er"] if not st.get("er_lowfreq") else "%.1f (1 GHz) / %.1f (low f)" % (st["er"], st["er_lowfreq"]), st["t_mm"], st["note"]))
    L += ["", "Netclasses before this pass: CAN_DIFF w/gap = %.2f/%.2f mm; USB w/gap = %.2f/%.2f mm (USB pair was not routed coupled, see `usb-reroute.md`)." % (can["diff_pair_width"], can["diff_pair_gap"], usb["diff_pair_width"], usb["diff_pair_gap"])]
    for row in rep["stackups"]:
        for case in row["er_cases"]:
            L += ["", "## %s, er = %s" % (row["name"], case["er"]), "", "### Single-ended Z0", "", "| w (mm) | Z0 (ohm) | eps_eff |", "|---|---|---|"]
            L += ["| %.3f | %.1f | %.2f |" % (r["w"], r["Z0"], r["ereff"]) for r in case["single"]]
            L += ["", "### Differential pairs", "", "| Case | w (mm) | s (mm) | Zodd | Zeven | Zdiff K-J (ohm) | Zdiff IPC-2141 (ohm) | Zcm |", "|---|---|---|---|---|---|---|---|"]
            L += ["| %s | %.3f | %.3f | %.1f | %.1f | **%.1f** | %.1f | %.1f |" % (r["label"], r["w"], r["s"], r["Zodd"], r["Zeven"], r["Zdiff_KJ"], r["Zdiff_IPC2141"], r["Zcm"]) for r in case["pairs"]]
            for target in ("90", "120"):
                sol = case["solutions"][target]
                L += ["", "### Width needed for Zdiff = %s ohm (K-J), by gap" % target, "", "| s (mm) | w (mm) | >= min track 0.127 |", "|---|---|---|"]
                L += ["| %.3f | %s | %s |" % (r["s"], ("%.3f" % r["w"]) if r["w"] else "no solution in 0.08..1.5", "yes" if r["feasible"] else "no") for r in sol["by_gap"]]
                gk = [k for k in sol if k.startswith("gap_for")][0]
                L.append("")
                L.append("Gap needed at the CAN_DIFF width %s mm: %s" % (gk.split("_w")[1], ("%.3f mm" % sol[gk]) if sol[gk] else "none (even an isolated 0.25 mm trace is below %s ohm differential)" % target))
    ur = rep["usb_recommendation"]
    cr = rep["can_recommendation"]
    L += ["", "## Results and decisions", "",
          "### USB (target 90 ohm differential, Full Speed 12 Mbit/s)", "",
          "- Chosen rule for the USB netclass (JLC7628, er 4.4 at 1 GHz, rounded to 0.01 mm): **w = %.2f mm, s = %.2f mm** -> Zdiff = %.1f ohm (er 4.6: %.1f ohm; file stackup: %.1f ohm), Zcm = %.1f ohm." % (ur["w_mm"], ur["s_mm"], ur["Zdiff_JLC7628_er4.4"], ur["Zdiff_JLC7628_er4.6"], ur["Zdiff_file_stackup"], ur["Zcm"]),
          "- The gap 0.15 mm was preferred over 0.20 mm to keep the pair narrow (2w + s = %.2f mm). Where the pair passes between the MCU" % (2 * ur["w_mm"] + ur["s_mm"]),
          "  decoupling capacitors (0.83 mm corridor, see `usb-reroute.md`) it is necked to 0.20/0.15 mm (about %.0f ohm) for a few mm; the" % rep["stackups"][1]["er_cases"][0]["pairs"][2]["Zdiff_KJ"],
          "  MCU pad stubs are 0.20 mm because the LQFP pads are 0.30 mm wide.",
          "- USB FS edges are 4-20 ns; the whole pair is about 20 mm (< 1/20 of the edge length in FR-4), so the impedance mismatch of the old",
          "  0.20 mm uncoupled tracks (about %.0f ohm single-ended on JLC7628) is electrically tolerable. The rule change is for consistency with the" % rep["stackups"][1]["er_cases"][0]["single"][2]["Z0"],
          "  fabricator stackup, not a functional fix.", "",
          "### CAN (target 120 ohm differential, classic CAN 500 kbit/s, CAN FD up to 5 Mbit/s)", "",
          "- Current CAN_DIFF rule 0.25/0.20 on JLC7628: Zdiff = %.1f ohm (er 4.4), i.e. about %.0f ohm (%.0f percent) below target - inside the" %
          (rep["stackups"][1]["er_cases"][0]["pairs"][0]["Zdiff_KJ"], 120 - rep["stackups"][1]["er_cases"][0]["pairs"][0]["Zdiff_KJ"], 100 * (120 - rep["stackups"][1]["er_cases"][0]["pairs"][0]["Zdiff_KJ"]) / 120),
          "  usual +-10 percent fabricator tolerance, so not 'far off', but correctable without moving any track.",
          "- 120 ohm on JLC7628 needs w = %s mm at s = 0.20 mm, %s mm at s = 0.30 mm, %s mm at s = 0.50 mm (all above the 0.127 mm minimum track)." %
          (cr["solutions_120"]["0.2"], cr["solutions_120"]["0.3"], cr["solutions_120"]["0.5"]),
          "- Decision: keep the present pair centre pitch (%.2f mm) and narrow the copper: **CAN_DIFF w = %.2f mm, s = %.2f mm** -> Zdiff = %.1f ohm" % (cr["pitch_mm"], cr["w_mm"], cr["s_mm"], cr["Zdiff_JLC7628_er4.4"]),
          "  (er 4.6: %.1f ohm; file stackup: %.1f ohm). Applied with `--apply-can`: netclass updated in the .kicad_pro and every CAN segment that was" % (cr["Zdiff_JLC7628_er4.6"], cr["Zdiff_file_stackup"]),
          "  0.25 mm wide was set to %.2f mm (%s). Narrowing a track never reduces a clearance, so no DRC clearance item can result; the DRC" % (cr["w_mm"], ", ".join("%s: %d" % kv for kv in sorted(rep.get("can_applied", {}).get("segments_narrowed", {}).items())) or "not applied in this run"),
          "  after the pass is in `drc-cleanup.md`. The CAN segments are 6-21 mm F.Cu stubs between transceiver and OBD-C connector with mixed",
          "  0.15-0.25 mm necks at the pads (not touched); at 500 kbit/s (and even CAN FD 5 Mbit/s, edges > 20 ns) they are far shorter than 1/10",
          "  of the edge length, so the bus sees the external 120 ohm terminations, not the PCB trace. The change is a consistency improvement,",
          "  not a functional fix. The actual gap of the existing pairs varies along the route (they were not routed as a strict coupled pair);",
          "  only the rule and the widths were normalised.", "",
          "### Limits", "",
          "- Quasi-static formulas; the stated accuracy of the K-J model is about 1 percent for 0.1 <= w/h <= 10 and 0.1 <= s/h <= 10, which the",
          "  cases above satisfy (w/h 0.6-2.4, s/h 0.6-2.4). Solder mask (about 0.01-0.02 mm, er ~3.5) typically lowers Zdiff by 2-4 ohm and is",
          "  not modelled. Copper roughness and etch factor are not modelled. The fabricator's own impedance calculator should be used before",
          "  ordering controlled impedance; nothing here was measured (no TDR, no board built).", "",
          "---", "",
          "pt-BR: Impedancia calculada analiticamente (Hammerstad-Jensen para trilha simples, Kirschning-Jansen para par acoplado) com o stackup",
          "do ficheiro e com o JLC7628 da JLCPCB. USB: regra nova w=%.2f mm, s=%.2f mm (~%.0f ohm diferencial no JLC7628). CAN: a regra 0.25/0.20 dava" % (ur["w_mm"], ur["s_mm"], ur["Zdiff_JLC7628_er4.4"]),
          "~%.0f ohm (-8 por cento); a classe CAN_DIFF passou a %.2f/%.2f mm (~%.0f ohm) mantendo o passo entre centros, e os segmentos CAN de 0.25 mm" % (rep["stackups"][1]["er_cases"][0]["pairs"][0]["Zdiff_KJ"], cr["w_mm"], cr["s_mm"], cr["Zdiff_JLC7628_er4.4"]),
          "foram estreitados para %.2f mm (estreitar nunca cria erro de clearance). Em 500 kbit/s os stubs curtos sao tolerantes; nada foi medido fisicamente." % cr["w_mm"]]
    hp.guarded_write_text(os.path.join(OUTD, "impedance.md"), "\n".join(L) + "\n")
    print("\n".join(L[-20:]))


if __name__ == "__main__":
    main()
