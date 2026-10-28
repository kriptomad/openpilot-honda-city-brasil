"""One-off patch helper for extract_ds_pins.py (kept for traceability). Run once."""
import re
from pathlib import Path
p = Path(__file__).resolve().parent / "extract_ds_pins.py"
s = p.read_text(encoding="utf-8")
rep = [
 ('("PA11", "stm32h7/peripherals.h", "USB_OTG_FS_DM AF10", "USB_DM")', '("PA11", "stm32h7/peripherals.h", "OTG_HS_DM AF10 (USB FS PHY interno; DS nomeia OTG_HS)", "USB_DM")'),
 ('("PA12", "stm32h7/peripherals.h", "USB_OTG_FS_DP AF10", "USB_DP")', '("PA12", "stm32h7/peripherals.h", "OTG_HS_DP AF10", "USB_DP")'),
 ('("PG9",  "stm32h7/peripherals.h", "FDCAN3_RX AF2", "FDCAN3_RX")', '("PG9",  "stm32h7/peripherals.h", "FDCAN3_TX AF2 (firmware só define AF2; direção pelo DS)", "FDCAN3_TX")'),
 ('("PG10", "stm32h7/peripherals.h", "FDCAN3_TX AF2", "FDCAN3_TX")', '("PG10", "stm32h7/peripherals.h", "FDCAN3_RX AF2", "FDCAN3_RX")'),
 ('"ADC analog (5VOUT_S)"', '"ADC12_INP5 analog (5VOUT_S; red.h só MODE_ANALOG)"'),
 ('"ADC1_INP4 (SBU1)"', '"ADC12_INP4 ADC1 ch4 (SBU1)"'),
 ('"ADC1_INP17 (SBU2)"', '"ADC1_INP17 ADC1 ch17 (SBU2)"'),
 ('"ADC1_INP2 (VOLT_S)"', '"ADC1_INP2 ADC1 ch2 (VOLT_S)"'),
 ('"HW_TYPE id1 bit0 (input pull-up; RED=0)"', '"GPIO in pull-up: HW_TYPE id1 bit0 (RED=0)"'),
 ('"HW_TYPE id1 bit1 (RED=0)"', '"GPIO in: HW_TYPE id1 bit1 (RED=0)"'),
 ('"HW_TYPE id1 bit2 (RED=0)"', '"GPIO in: HW_TYPE id1 bit2 (RED=0)"'),
 ('"HW_TYPE id1 bit3 (RED=0)"', '"GPIO in: HW_TYPE id1 bit3 (RED=0)"'),
 ('"HW_TYPE id2 bit0 (must NOT read 1 together with PD5)"', '"GPIO in pull-up: HW_TYPE id2 bit0 (PD4..PD6 != 0b011)"'),
 ('"HW_TYPE id2 bit1"', '"GPIO in: HW_TYPE id2 bit1"'),
 ('"HW_TYPE id2 bit2"', '"GPIO in: HW_TYPE id2 bit2"'),
 ('"OSC_IN (HSE 25 MHz)"', '"OSC_IN (HSE 25 MHz) pino PH0-OSC_IN"'),
 ('"OSC_OUT (HSE 25 MHz)"', '"OSC_OUT (HSE 25 MHz) pino PH1-OSC_OUT"'),
 ('"SPI4_NSS unused"', '"GPIO (SPI4_NSS) unused"'), ('"SPI4_SCK unused"', '"GPIO (SPI4_SCK) unused"'),
 ('"SPI4_MISO unused"', '"GPIO (SPI4_MISO) unused"'), ('"SPI4_MOSI unused"', '"GPIO (SPI4_MOSI) unused"'),
]
for a, b in rep:
    assert a in s, a
    s = s.replace(a, b)

old_re = s[s.index('row_re = re.compile('):s.index('\n', s.index('row_re = re.compile('))]
new_re = ('row_re = re.compile(r"^(\\S+) (\\S+) (\\S+) (\\S+) (\\S+) (\\S+) (\\S+) (\\S+) '
          '(P[A-K]\\d{1,2}(?:_C)?(?:-OSC_IN|-OSC_OUT|\\([^)]*\\)?)?|BOOT0|NRST|PDR_ON|VCAP|VDDLDO|VDDSMPS|VLXSMPS|VFBSMPS|VSSSMPS|VDD33USB|VDD50USB|VREF\\+|VDDA|VSSA|VBAT|VDD|VSS)'
          '\\s*(I/O|S|RST|I|O|B)?\\b(.*)$", re.M)\n'
          'TABLE8_START = text.find("Table 8. STM32H725 pin and ball descriptions")\n'
          'TABLE8_END = text.find("Table 9.", TABLE8_START + 100)')
s = s.replace(old_re, new_re)
s = s.replace('lines = text.splitlines()\n# normalise', 'lines = text[TABLE8_START:TABLE8_END].splitlines()\n# normalise')
s = s.replace('    name = cols[8].replace("_C", "")',
              '    name = re.sub(r"(_C|-OSC_IN|-OSC_OUT|\\(.*)$", "", cols[8])\n'
              '    if cols[9] is None and name.startswith("P"):\n        continue  # not a Table 8 row (pin type column missing)')
s = s.replace('"raw": (cols[8] + cols[9]).strip()', '"raw": (cols[8] + " " + (cols[10] or "")).strip()')
start = s.index('    key = need.split()[0]')
end = s.index('    out.append({"pin": pin, "lqfp144": r["lqfp144"]')
s = s[:start] + ('    key = need.split()[0]\n'
                 '    blob = r["raw"] + " " + r["funcs"]\n'
                 '    if key == "GPIO":\n        af_ok = True  # I/O pin exists in LQFP144 column\n'
                 '    elif key in ("SWDIO", "SWCLK"):\n        af_ok = ("JTMS" in blob) if key == "SWDIO" else ("JTCK" in blob)\n'
                 '    else:\n        af_ok = key in blob\n') + s[end:]
p.write_text(s, encoding="utf-8")
print("patched")
