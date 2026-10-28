"""
Extract LQFP144 pin numbers + alternate/additional functions for the pins the panda
firmware (red.h / stm32h7/peripherals.h / stm32h7/board.h) requires, from the ST datasheet
DS13311 Rev 5 text dump (02_REFERENCE/datasheets/DS13313_text.txt).

Output: 03_RESEARCH/P3_tabela_pinos_LQFP144_vs_firmware.md + JSON log in 06_REPORTS.
Read-only on the datasheet; writes only inside OUTPUT_ROOT (hp_common guard).
"""
import re, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import OUTPUT_ROOT, assert_inside_output, JsonLog

DS_TXT = OUTPUT_ROOT / "02_REFERENCE" / "datasheets" / "DS13313_text.txt"
OUT_MD = OUTPUT_ROOT / "03_RESEARCH" / "P3_tabela_pinos_LQFP144_vs_firmware.md"
OUT_JSON = OUTPUT_ROOT / "03_RESEARCH" / "P3_pinos_LQFP144.json"
DRY = "--dry-run" in sys.argv

# (port pin, firmware source, function required, net name in new schematic)
REQUIRED = [
    ("PA11", "stm32h7/peripherals.h", "OTG_HS_DM AF10 (USB FS PHY interno; DS nomeia OTG_HS)", "USB_DM"),
    ("PA12", "stm32h7/peripherals.h", "OTG_HS_DP AF10", "USB_DP"),
    ("PF11", "stm32h7/peripherals.h", "ADC1_INP2 ADC1 ch2 (VOLT_S)", "VOLT_S"),
    ("PB8",  "stm32h7/peripherals.h", "FDCAN1_RX AF9", "FDCAN1_RX"),
    ("PB9",  "stm32h7/peripherals.h", "FDCAN1_TX AF9", "FDCAN1_TX"),
    ("PB12", "stm32h7/peripherals.h", "FDCAN2_RX AF9 (normal)", "FDCAN2_RX"),
    ("PB13", "stm32h7/peripherals.h", "FDCAN2_TX AF9 (normal)", "FDCAN2_TX"),
    ("PB5",  "stm32h7/peripherals.h", "FDCAN2_RX AF9 (OBD)", "FDCAN2OBD_RX"),
    ("PB6",  "stm32h7/peripherals.h", "FDCAN2_TX AF9 (OBD)", "FDCAN2OBD_TX"),
    ("PG9",  "stm32h7/peripherals.h", "FDCAN3_TX AF2 (firmware só define AF2; direção pelo DS)", "FDCAN3_TX"),
    ("PG10", "stm32h7/peripherals.h", "FDCAN3_RX AF2", "FDCAN3_RX"),
    ("PG11", "boards/red.h", "GPIO out: CAN0 transceiver STB (bus0)", "CAN0_STB"),
    ("PB3",  "boards/red.h", "GPIO out: OBD transceiver STB", "CAN_OBD_STB"),
    ("PD7",  "boards/red.h", "GPIO out: CAN2 transceiver STB (bus2)", "CAN2_STB"),
    ("PB4",  "boards/red.h", "GPIO out: CAN1 transceiver STB (bus1)", "CAN1_STB"),
    ("PB1",  "boards/red.h", "ADC12_INP5 analog (5VOUT_S; red.h só MODE_ANALOG)", "5VOUT_S"),
    ("PB14", "boards/red.h", "GPIO OD pull-up: USB_LOAD_EN", "USB_LOAD_EN"),
    ("PC4",  "boards/red.h", "ADC12_INP4 ADC1 ch4 (SBU1)", "SBU1"),
    ("PA1",  "boards/red.h", "ADC1_INP17 ADC1 ch17 (SBU2)", "SBU2"),
    ("PC10", "boards/red.h", "GPIO out active-low: relay SBU1", "RELAY_SBU1"),
    ("PC11", "boards/red.h", "GPIO out active-low: relay SBU2", "RELAY_SBU2"),
    ("PE4",  "boards/red.h", "GPIO OD: LED red", "LED_R"),
    ("PE3",  "boards/red.h", "GPIO OD: LED green", "LED_G"),
    ("PE2",  "boards/red.h", "GPIO OD: LED blue", "LED_B"),
    ("PF7",  "stm32h7/board.h", "GPIO in pull-up: HW_TYPE id1 bit0 (RED=0)", "HWID1_0"),
    ("PF8",  "stm32h7/board.h", "GPIO in: HW_TYPE id1 bit1 (RED=0)", "HWID1_1"),
    ("PF9",  "stm32h7/board.h", "GPIO in: HW_TYPE id1 bit2 (RED=0)", "HWID1_2"),
    ("PF10", "stm32h7/board.h", "GPIO in: HW_TYPE id1 bit3 (RED=0)", "HWID1_3"),
    ("PD4",  "stm32h7/board.h", "GPIO in pull-up: HW_TYPE id2 bit0 (PD4..PD6 != 0b011)", "HWID2_0"),
    ("PD5",  "stm32h7/board.h", "GPIO in: HW_TYPE id2 bit1", "HWID2_1"),
    ("PD6",  "stm32h7/board.h", "GPIO in: HW_TYPE id2 bit2", "HWID2_2"),
    ("PH0",  "stm32h7/clock.h", "OSC_IN (HSE 25 MHz) pino PH0-OSC_IN", "HSE_IN"),
    ("PH1",  "stm32h7/clock.h", "OSC_OUT (HSE 25 MHz) pino PH1-OSC_OUT", "HSE_OUT"),
    ("PA13", "-", "SWDIO (debug)", "SWDIO"),
    ("PA14", "-", "SWCLK (debug)", "SWCLK"),
    ("PE11", "boards/red.h (has_spi=false)", "GPIO (SPI4_NSS) unused", "NC"),
    ("PE12", "boards/red.h", "GPIO (SPI4_SCK) unused", "NC"),
    ("PE13", "boards/red.h", "GPIO (SPI4_MISO) unused", "NC"),
    ("PE14", "boards/red.h", "GPIO (SPI4_MOSI) unused", "NC"),
]

text = DS_TXT.read_text(encoding="utf-8")
# Table 8 rows start with 8 package columns then pin name. Column order (page 63):
# VFQFPN68, LQFP100, TFBGA100, LQFP144, WLCSP115, UFBGA169, UFBGA176+25, LQFP176
row_re = re.compile(r"^(\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (P[A-K]\d{1,2}(?:_C)?(?:-OSC_IN|-OSC_OUT|\([^)]*\)?)?|BOOT0|NRST|PDR_ON|VCAP|VDDLDO|VDDSMPS|VLXSMPS|VFBSMPS|VSSSMPS|VDD33USB|VDD50USB|VREF\+|VDDA|VSSA|VBAT|VDD|VSS)\s*(I/O|S|RST|I|O|B)?\b(.*)$", re.M)
TABLE8_START = text.find("Table 8. STM32H725 pin and ball descriptions \n")
TABLE8_END = text.find("Table 9. STM32H725 pin alternate functions \n", TABLE8_START)
# rows where the pin name wrapped onto the next line (e.g. "58 89 B6 130 H7 F7 A6 162" / "PB3(JTDO/")
row_wrap_re = re.compile(r"^(\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)$")

lines = text[TABLE8_START:TABLE8_END].splitlines()
# normalise wrapped rows in place: merge "<8 cols>" + "<pinname...>" into one line
for i in range(len(lines) - 1):
    if row_wrap_re.match(lines[i]) and re.match(r"^P[A-K]\d{1,2}", lines[i + 1]):
        j = i + 1
        merged = []
        while j < len(lines) and j <= i + 4 and "I/O" not in lines[j]:
            merged.append(lines[j].strip()); lines[j] = ""; j += 1
        if j < len(lines) and "I/O" in lines[j]:
            merged.append(lines[j].strip()); lines[j] = ""
        lines[i] = lines[i] + " " + "".join(merged[:-1]).replace(" ", "") + " " + merged[-1] if merged else lines[i]
rows = {}
for i, ln in enumerate(lines):
    m = row_re.match(ln)
    if not m:
        continue
    cols = m.groups()
    name = re.sub(r"(_C|-OSC_IN|-OSC_OUT|\(.*)$", "", cols[8])
    if cols[9] is None and name.startswith("P"):
        continue  # not a Table 8 row (pin type column missing)
    lqfp144 = cols[3]
    tfbga100 = cols[2]
    # collect following lines until next row or page break => AF list + additional functions
    buf = []
    j = i + 1
    while j < len(lines) and not row_re.match(lines[j]) and not lines[j].startswith("=====") and len(buf) < 25:
        buf.append(lines[j].strip())
        j += 1
    blob = " ".join(buf)
    rows.setdefault(name, []).append({"line": i + 1, "lqfp144": lqfp144, "tfbga100": tfbga100,
                                      "raw": (cols[8] + " " + (cols[10] or "")).strip(), "funcs": blob})

out = []
missing = []
for pin, src, need, net in REQUIRED:
    r = rows.get(pin)
    if not r:
        missing.append(pin)
        out.append({"pin": pin, "lqfp144": "NÃO ENCONTRADO", "tfbga100": "-", "need": need, "src": src, "net": net, "af_ok": None, "funcs": ""})
        continue
    r = r[0]
    key = need.split()[0]
    blob = r["raw"] + " " + r["funcs"]
    if key == "GPIO":
        af_ok = True  # I/O pin exists in LQFP144 column
    elif key in ("SWDIO", "SWCLK"):
        af_ok = ("JTMS" in blob) if key == "SWDIO" else ("JTCK" in blob)
    else:
        af_ok = key in blob
    out.append({"pin": pin, "lqfp144": r["lqfp144"], "tfbga100": r["tfbga100"], "need": need, "src": src,
                "net": net, "af_ok": bool(af_ok), "funcs": r["funcs"][:400], "ds_line": r["line"]})

power = {k: [x["lqfp144"] for x in v] for k, v in rows.items() if k in
         ("VCAP", "VDDLDO", "VDDSMPS", "VLXSMPS", "VFBSMPS", "VSSSMPS", "VDD33USB", "VDD50USB", "VREF+", "VDDA", "VSSA", "VBAT", "VDD", "VSS", "BOOT0", "NRST", "PDR_ON")}

md = ["# P3 — Tabela pino LQFP144 (STM32H725ZG) × função exigida pelo firmware × rede",
      "",
      "Fonte: ST **DS13311 Rev 5 (Nov/2023)** 'STM32H725xE/G', Tabela 8 (pin and ball descriptions), "
      "arquivo `02_REFERENCE/datasheets/DS13313_STM32H725_ae.pdf` (SHA-256 3953CF96…3AA14), texto extraído com pypdf em "
      "`DS13313_text.txt`. Firmware: `02_REFERENCE/panda` @ 408e14d4. Gerado por `05_SCRIPTS/extract_ds_pins.py` (não editado à mão).",
      "",
      "Coluna 'AF/ADC confirmado' = a função exigida aparece literalmente na lista de funções alternativas/adicionais do pino no datasheet.",
      "",
      "| Porta | LQFP144 pino | TFBGA100 | Função exigida | Fonte firmware | Rede | AF/ADC confirmado | Linha DS |",
      "|---|---|---|---|---|---|---|---|"]
for o in out:
    md.append(f"| {o['pin']} | {o['lqfp144']} | {o['tfbga100']} | {o['need']} | {o['src']} | {o['net']} | "
              f"{'SIM' if o['af_ok'] else ('NÃO ENCONTRADO' if o['af_ok'] is None else '**NÃO**')} | {o.get('ds_line','')} |")
md += ["", "## Pinos de alimentação / sistema (LQFP144)", "", "| Nome | Pinos LQFP144 |", "|---|---|"]
for k, v in power.items():
    md.append(f"| {k} | {', '.join(v)} |")
# second source: KiCad official symbol (generated from ST CubeMX DB) for system/power pins
KICAD_TXT = OUTPUT_ROOT / "03_RESEARCH" / "kicad_lib_STM32H725ZGTx_pins.txt"
kicad_pins = {}
for ln in KICAD_TXT.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^(\d+) (\S+) (\S+)$", ln)
    if m:
        kicad_pins.setdefault(re.sub(r"\(.*$", "", m.group(2)), []).append(m.group(1))
md += ["", "## Cruzamento com a biblioteca oficial do KiCad (MCU_ST_STM32H7:STM32H725ZGTx)", "",
       "| Nome | DS13311 Tabela 8 (parser) | KiCad lib | Igual? |", "|---|---|---|---|"]
for k in ("VDD", "VSS", "VBAT", "VDDSMPS", "VSSSMPS", "VLXSMPS", "VFBSMPS", "NRST", "VSSA", "VREF+", "VDDA", "VCAP", "VDDLDO", "VDD50USB", "VDD33USB", "BOOT0", "PDR_ON"):
    a = sorted({x for x in power.get(k, []) if x.isdigit()}, key=int)
    b = sorted(kicad_pins.get(k, []), key=int)
    md.append(f"| {k} | {', '.join(a) or '(linha ilegível no PDF)'} | {', '.join(b)} | {'SIM' if a == b else ('parcial (PDF ilegível)' if set(a) <= set(b) else '**NÃO**')} |")
for o in out:
    kb = kicad_pins.get(o["pin"], [])
    o["kicad_lib_pin"] = kb[0] if kb else "-"
    o["kicad_match"] = (o["lqfp144"] == o["kicad_lib_pin"])
md += ["", "GPIO exigidos: DS × KiCad lib divergentes: " + (", ".join(f"{o['pin']} (DS {o['lqfp144']} / lib {o['kicad_lib_pin']})" for o in out if not o["kicad_match"]) or "nenhum")]
md += ["", f"## Pinos exigidos ausentes no LQFP144: {missing if missing else 'nenhum'}",
       "", "## Observação TFBGA100",
       "Na coluna TFBGA100, '-' indica que o pino NÃO existe nesse encapsulamento. Todos os PFx/PGx exigidos pelo firmware "
       "aparecem como '-' → paridade 1:1 impossível em TFBGA100 (fato, Tabela 8)."]

log = JsonLog("extract_ds_pins")
log.info("rows_parsed", n=len(rows))
log.info("missing", pins=missing)
if DRY:
    print("\n".join(md)); print("[dry-run] nothing written")
else:
    assert_inside_output(OUT_MD); assert_inside_output(OUT_JSON)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"required": out, "power": power}, indent=1, ensure_ascii=False), encoding="utf-8")
    log.info("written", files=[str(OUT_MD.relative_to(OUTPUT_ROOT)), str(OUT_JSON.relative_to(OUTPUT_ROOT))])
    print("\n".join(md))
log.save(rows=len(rows), missing=missing, not_confirmed=[o["pin"] for o in out if not o["af_ok"]])
