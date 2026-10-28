"""Isola BO_ 401 GEARBOX do DBC gerado e confere o layout GEARBOX_CVT (audit2 D-1).

Uso: python tools/check_gearbox_cvt.py <honda_civic_ex_2022_can_generated.dbc>
"""
import sys

import cantools

txt = open(sys.argv[1]).read()
out = ['VERSION ""', "", "BU_: PCM EON XXX"]
keep = False
for l in txt.splitlines():
    if l.startswith("BO_ "):
        keep = l.startswith("BO_ 401 ")
    if l.startswith("VAL_ "):
        keep = l.startswith("VAL_ 401 ")
    if l.startswith("CM_"):
        continue
    if keep and l.strip():
        out.append(l)

db = cantools.database.load_string("\n".join(out), "dbc", strict=True)
m = db.get_message_by_frame_id(401)
print(m.name, sorted((s.name, s.start, s.length) for s in m.signals))
# GEAR_SHIFTER 44|5@0+ -> byte 5 low nibble+1 bit
for raw, exp in ((0x04, "D"), (0x0A, "S"), (0x07, "L"), (0x01, "P"), (0x02, "R"), (0x03, "N")):
    got = m.decode(bytes([0, 0, 0, 0, 0, raw, 0, 0]), decode_choices=True)["GEAR_SHIFTER"]
    print(f"byte5=0x{raw:02X} -> {got} (esperado {exp})")
    assert str(got) == exp, (got, exp)
# byte0 nao deve mais influenciar GEAR_SHIFTER
got = m.decode(bytes([0x08, 0, 0, 0, 0, 0x04, 0, 0]), decode_choices=True)["GEAR_SHIFTER"]
assert str(got) == "D", got
print("OK: layout GEARBOX_CVT upstream (9ef0b1fb) confirmado")
