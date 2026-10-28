"""parity_check.py - firmware x hardware pin parity verifier (protocol v3 STEP 3 / STEP 7).

Inputs
  --netlist  KiCad XML netlist exported with `kicad-cli sch export netlist --format kicadxml`
  --profile  red_h7 | black_f4  (tables in firmware_pins.json, copied from commaai/panda with file:line)
  --mcu      MCU reference (default: first component whose value matches the profile regex)

Checks (structural, independent of net names)
  * every firmware pin: connected / not connected
  * CAN groups: RX and TX nets must land on the same non-MCU component (the transceiver); the STB pin net must
    reach that same transceiver -> otherwise DIVERGENTE
  * USB DM/DP: must reach a connector/ESD/resistor path (any non-MCU component)
  * hwtype straps: expected low -> net must be GND; expected float_or_high -> must be unconnected or a non-GND net
  * power pins of the MCU: VDD*/VSS*/VCAP/VREF/VDDA/VBAT reported for completeness
  * MCU pins connected in the netlist but absent from the firmware table -> SEM_USO (informational)

Output: 06_REPORTS/parity_<profile>_<netlist-stem>.{md,json}. Exit code 1 if any DIVERGENTE / NAO_CONECTADO
(non-optional) so STEP 7 can gate on it.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import hp_common as hp

GND_RX = re.compile(r"^(GND|GNDA|AGND|DGND|GNDREF|/?GND\w*)$", re.I)
POWER_PIN_RX = re.compile(r"^(VDD\w*|VSS\w*|VCAP\w*|VREF\+?|VDDA|VSSA|VBAT|VDDLDO|VDDSMPS|VLXSMPS|VFBSMPS|VSSSMPS|VDD33USB|VDD50USB|PDR_ON|NRST)$", re.I)
PORT_RX = re.compile(r"^(P[A-K]\d{1,2})(?:[_/(-]|$)")  # H7 symbol names JTAG-capable pins "PB4(NJTRST)"


def load_netlist(path: Path):
    root = ET.parse(path).getroot()
    comps = {c.get("ref"): {"value": (c.findtext("value") or ""), "footprint": (c.findtext("footprint") or "")}
             for c in root.find("components")}
    pin_net: dict[tuple[str, str], str] = {}
    net_nodes: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    pin_names: dict[tuple[str, str], str] = {}
    for net in root.find("nets"):
        name = net.get("name")
        for node in net:
            ref, pin = node.get("ref"), node.get("pin")
            pf = node.get("pinfunction") or ""
            pin_net[(ref, pin)] = name
            pin_names[(ref, pin)] = pf
            net_nodes[name].append((ref, pin, pf))
    return comps, pin_net, pin_names, net_nodes


def is_unconnected(net: str | None) -> bool:
    return net is None or net.startswith("unconnected-") or net == ""


def port_of(pinfunction: str) -> str | None:
    m = PORT_RX.match(pinfunction)
    if m:
        return m.group(1)
    m = re.match(r"^(BOOT0|NRST|PDR_ON|VBAT|VDD\w*?|VSS\w*?|VCAP_?\d?|VREF\+?|VDDA|VSSA)(?:_\d+)?$", pinfunction)
    if m:
        return m.group(1)
    return None


def main():
    ap = hp.std_argparser("firmware x hardware pin parity")
    ap.add_argument("--netlist", required=True)
    ap.add_argument("--profile", required=True, choices=["red_h7", "black_f4"])
    ap.add_argument("--mcu", default=None)
    ap.add_argument("--h7-lib-pins", default=str(hp.OUTPUT_ROOT / "03_RESEARCH" / "kicad_lib_STM32H725ZGTx_pins.txt"),
                    help="fallback pad->port table when the symbol pinfunction lacks the port name")
    args = ap.parse_args()
    hp.apply_args(args)

    netlist = Path(args.netlist)
    fw = json.loads((Path(__file__).parent / "firmware_pins.json").read_text(encoding="utf-8"))["profiles"][args.profile]
    log = hp.JsonLog(f"parity_{args.profile}_{netlist.stem}")
    comps, pin_net, pin_names, net_nodes = load_netlist(netlist)

    mcu = args.mcu
    if not mcu:
        rx = re.compile(fw["mcu_value_regex"], re.I)
        cands = [r for r, c in comps.items() if rx.search(c["value"])]
        if not cands:
            log.error("MCU not found", regex=fw["mcu_value_regex"])
            log.save(result="MCU_NOT_FOUND")
            sys.exit(2)
        mcu = sorted(cands)[0]
    log.info("MCU", ref=mcu, value=comps[mcu]["value"], footprint=comps[mcu]["footprint"])

    # port name -> (pad, net)
    port_map: dict[str, tuple[str, str | None]] = {}
    fallback = {}
    lib = Path(args.h7_lib_pins)
    if lib.exists() and fw["package"] == "LQFP144" and "144" in comps[mcu]["footprint"]:
        for line in lib.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^(\d+)\s+(\S+)\s+", line)
            if m:
                fallback[m.group(1)] = m.group(2)
    mcu_pads = {pad: net for (ref, pad), net in pin_net.items() if ref == mcu}
    for pad, net in mcu_pads.items():
        pf = pin_names[(mcu, pad)]
        port = port_of(pf) or port_of(fallback.get(pad, "")) or pf or pad
        if POWER_PIN_RX.match(port):
            port = f"{port}#{pad}"  # keep every VDD/VSS pad
        port_map[port] = (pad, net)

    def comps_on_net(net: str, exclude: str) -> set[str]:
        return {ref for ref, _, _ in net_nodes.get(net, []) if ref != exclude}

    rows = []
    groups: dict[str, dict[str, dict]] = defaultdict(dict)
    for entry in fw["pins"]:
        pin = entry["pin"]
        pad, net = port_map.get(pin, (None, None))
        row = {"pin": pin, "pad": pad, "role": entry["role"], "signal": entry.get("signal", entry.get("group", "")),
               "net": net, "status": "", "detail": "", "src": entry["src"], "optional": entry.get("optional", False)}
        if pad is None:
            row["status"], row["detail"] = "PINO_INEXISTENTE", "port not present on this MCU symbol/package"
        elif is_unconnected(net):
            if entry["role"] == "hwtype":
                ok = entry["expect"] in ("float_or_high", "float_or_low")
                row["status"] = "OK" if ok else "DIVERGENTE"
                row["detail"] = f"floating; expect={entry['expect']}"
            elif entry["role"] in ("analog_nc", "swd") or entry.get("optional"):
                row["status"], row["detail"] = "SEM_USO", "not connected (optional in firmware)"
            else:
                row["status"] = "NAO_CONECTADO"
        else:
            others = comps_on_net(net, mcu)
            if entry["role"] == "hwtype":
                gnd = bool(GND_RX.match(net))
                exp = entry["expect"]
                ok = (exp == "low" and gnd) or (exp in ("float_or_high", "float_or_low") and not gnd) or (exp == "float_or_low" and gnd)
                row["status"] = "OK" if ok else "DIVERGENTE"
                row["detail"] = f"net={net}; expect={exp}"
            elif entry["role"] in ("can_rx", "can_tx", "can_stb"):
                groups[entry["group"]][entry["role"]] = {"pin": pin, "net": net, "comps": others}
                row["status"] = "PENDENTE_GRUPO"
            else:
                row["status"] = "OK" if others else "DIVERGENTE"
                row["detail"] = "reaches " + ",".join(sorted(others)) if others else "net has no other component"
                if entry["role"] in ("usb_dm", "usb_dp", "adc", "relay", "led", "hse", "boot0") and GND_RX.match(net):
                    row["status"], row["detail"] = "DIVERGENTE", "signal pin tied to GND"
        rows.append(row)

    # CAN group resolution
    for g, parts in groups.items():
        rx, tx, stb = parts.get("can_rx"), parts.get("can_tx"), parts.get("can_stb")
        xcvr = (rx["comps"] & tx["comps"]) if rx and tx else set()
        xcvr = {c for c in xcvr if not re.match(r"^(R|C|L|D|TP|J|P)\d", c)} or xcvr
        detail = f"xcvr={','.join(sorted(xcvr)) or 'none'}"
        stb_ok = bool(stb and xcvr and (stb["comps"] & xcvr))
        for role, part in parts.items():
            for row in rows:
                if row["pin"] == part["pin"] and row["status"] == "PENDENTE_GRUPO":
                    if role in ("can_rx", "can_tx"):
                        row["status"] = "OK" if xcvr else "DIVERGENTE"
                        row["detail"] = detail + ("" if xcvr else "; RX/TX do not share a transceiver")
                    else:
                        row["status"] = "OK" if stb_ok else "DIVERGENTE"
                        row["detail"] = detail + ("; STB reaches the same transceiver" if stb_ok else "; STB does not reach that transceiver")
        log.info(f"CAN group {g}", xcvr=sorted(xcvr), stb_ok=stb_ok)

    # MCU pins used by hardware but not by firmware
    fw_pins = {e["pin"] for e in fw["pins"]}
    extra = []
    POWER_KEY_RX = re.compile(r"^(" + POWER_PIN_RX.pattern[2:-2] + r")#\d+$", re.I)
    for port, (pad, net) in sorted(port_map.items(), key=lambda kv: int(kv[1][0]) if kv[1][0].isdigit() else 0):
        if port in fw_pins or POWER_KEY_RX.match(port) or is_unconnected(net):
            continue
        extra.append({"pin": port, "pad": pad, "net": net, "comps": sorted(comps_on_net(net, mcu))})
    power = [{"pin": p.split("#")[0], "pad": pad, "net": net} for p, (pad, net) in port_map.items() if POWER_KEY_RX.match(p)]

    bad = [r for r in rows if r["status"] in ("DIVERGENTE", "NAO_CONECTADO", "PINO_INEXISTENTE") and not r["optional"]]
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1

    out_md = hp.REPORT_DIR / f"parity_{args.profile}_{netlist.stem}.md"
    md = [f"# Paridade firmware x hardware — perfil `{args.profile}` — netlist `{netlist.name}`", "",
          f"Firmware: {fw['repo']} @ {fw['commit']}. MCU: {mcu} ({comps[mcu]['value']}, {comps[mcu]['footprint']}).",
          f"Resultado: **{'SEM DIVERGÊNCIA' if not bad else f'{len(bad)} PROBLEMA(S)'}** — " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())), "",
          "| Pino FW | Pad | Papel | Sinal/grupo | Net | Status | Detalhe | Fonte firmware |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['pin']} | {r['pad'] or '-'} | {r['role']} | {r['signal']} | `{r['net'] or '-'}` | **{r['status']}** | {r['detail']} | {r['src']} |")
    md += ["", "## Pinos do MCU ligados no hardware mas sem função no firmware (SEM_USO no firmware)", "",
           "| Pino | Pad | Net | Componentes |", "|---|---|---|---|"]
    md += [f"| {e['pin']} | {e['pad']} | `{e['net']}` | {', '.join(e['comps'])} |" for e in extra] or ["| - | - | - | - |"]
    md += ["", "## Pinos de alimentação do MCU", "", "| Pino | Pad | Net |", "|---|---|---|"]
    md += [f"| {p['pin']} | {p['pad']} | `{p['net']}` |" for p in sorted(power, key=lambda p: int(p['pad']) if p['pad'].isdigit() else 0)]
    hp.guarded_write_text(out_md, "\n".join(md) + "\n", "parity")
    log.save(result="OK" if not bad else "DIVERGENCES", problems=len(bad), counts=dict(counts), rows=rows, extra=extra, power=power, report=str(out_md))
    print(f"report -> {out_md}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
