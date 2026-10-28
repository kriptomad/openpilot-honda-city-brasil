"""Second patch for extract_ds_pins.py: multi-line wrapped pin names (PA13/(JTMS/\nSWDIO)) and
cross-check of system/power pins against KiCad official symbol STM32H725ZGTx (second source)."""
from pathlib import Path
p = Path(__file__).resolve().parent / "extract_ds_pins.py"
s = p.read_text(encoding="utf-8")
old = '''for i in range(len(lines) - 1):
    if row_wrap_re.match(lines[i]) and re.match(r"^P[A-K]\\d{1,2}", lines[i + 1]):
        lines[i] = lines[i] + " " + lines[i + 1]
        lines[i + 1] = ""'''
new = '''for i in range(len(lines) - 1):
    if row_wrap_re.match(lines[i]) and re.match(r"^P[A-K]\\d{1,2}", lines[i + 1]):
        j = i + 1
        merged = []
        while j < len(lines) and j <= i + 4 and "I/O" not in lines[j]:
            merged.append(lines[j].strip()); lines[j] = ""; j += 1
        if j < len(lines) and "I/O" in lines[j]:
            merged.append(lines[j].strip()); lines[j] = ""
        lines[i] = lines[i] + " " + "".join(merged[:-1]).replace(" ", "") + " " + merged[-1] if merged else lines[i]'''
assert old in s
s = s.replace(old, new)

old2 = 'md += ["", f"## Pinos exigidos ausentes no LQFP144: {missing if missing else \'nenhum\'}",'
new2 = '''# second source: KiCad official symbol (generated from ST CubeMX DB) for system/power pins
KICAD_TXT = OUTPUT_ROOT / "hardware/research" / "kicad-lib-stm32h725zgtx-pins.txt"
kicad_pins = {}
for ln in KICAD_TXT.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^(\\d+) (\\S+) (\\S+)$", ln)
    if m:
        kicad_pins.setdefault(re.sub(r"\\(.*$", "", m.group(2)), []).append(m.group(1))
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
md += ["", f"## Pinos exigidos ausentes no LQFP144: {missing if missing else 'nenhum'}",'''
assert old2 in s
s = s.replace(old2, new2)
p.write_text(s, encoding="utf-8")
print("patched2")
