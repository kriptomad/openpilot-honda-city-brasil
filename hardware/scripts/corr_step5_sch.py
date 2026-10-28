"""Step 5 schematic side (text edits, keeps the rest of the file byte-identical).

  item 24: C23/C24 15pF -> 18pF (Value, MPN, LCSC properties)
  item 33b: U3 (USB-A) shell pins 5/6 -> GND: remove the two no_connect flags and add power:GND symbols
            on the pin ends (247.523,53.721) and (247.523,76.581).
PCB side: corr_step5_pcb.py c23c24 / u3gnd.
Usage: python -u corr_step5_sch.py [--check]
"""
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp  # noqa: E402

SCH = os.path.join(str(hp.OUTPUT_ROOT), "hardware", "hybrid-panda", "HybridPanda.kicad_sch")
NEW_CAP = {"Value": "18pF", "MPN": "0402CG180J500NT", "LCSC": "C1555"}
PINS = [((247.523, 53.721), 180), ((247.523, 76.581), 0)]  # (pin end, GND symbol rotation)

GND_TPL = '''  (symbol (lib_id "power:GND") (at {x} {y} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid {u})
    (property "Reference" "{ref}" (at {x} {yr} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {x} {yv} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid {pu}))
    (instances
      (project "HybridPanda"
        (path "/5994f1e8-15cb-459b-8e2e-160b94fba244"
          (reference "{ref}") (unit 1)
        )
      )
    )
  )
'''


def sym_block(s, ref):
    """Return (start, end) of the (symbol ...) block whose Reference property is ref."""
    m = re.search(r'\(property "Reference" "%s"' % re.escape(ref), s)
    start = s.rfind("\n  (symbol ", 0, m.start()) + 1
    nl = "\r\n" if "\r\n" in s[:2000] else "\n"
    end = s.find("\n  )" + nl, m.start()) + 4 + len(nl)
    return start, end


def main():
    check = "--check" in sys.argv
    s = open(SCH, encoding="utf-8", newline="").read()
    orig = s
    nl = "\r\n" if "\r\n" in s[:2000] else "\n"
    for ref in ("C23", "C24"):
        a, e = sym_block(s, ref)
        blk = s[a:e]
        for key, val in NEW_CAP.items():
            blk, n = re.subn(r'(\(property "%s" ")[^"]*(")' % key, r'\g<1>%s\2' % val, blk, count=1)
            assert n == 1, (ref, key)
        s = s[:a] + blk + s[e:]
    for (x, y), rot in PINS:
        line = re.compile(r'\r?\n  \(no_connect \(at %.3f %.3f\) \(uuid [0-9a-f-]+\)\)' % (x, y))
        s, n = line.subn("", s, count=1)
        print("no_connect at (%.3f,%.3f) removed: %d" % (x, y, n))
    nums = [int(m) for m in re.findall(r'"#PWR0?(\d+)"', s)]
    nxt = max(nums) + 1
    blocks = ""
    for i, ((x, y), rot) in enumerate(PINS):
        ref = "#PWR0%d" % (nxt + i)
        dy = -1 if rot == 180 else 1
        blocks += GND_TPL.format(x=x, y=y, rot=rot, u=uuid.uuid4(), pu=uuid.uuid4(), ref=ref,
                                 yr="%.3f" % (y + 6.35 * dy), yv="%.3f" % (y + 3.81 * dy)).replace("\n", nl)
    tail = s.rfind("\n  (sheet_instances")
    if tail < 0:
        tail = s.rstrip().rfind("\n)")
    s = s[:tail + 1] + blocks + s[tail + 1:]
    print("added GND symbols:", ["#PWR0%d" % (nxt + i) for i in range(len(PINS))])
    if check:
        print("check only; %d chars changed" % (len(s) - len(orig)))
        return
    hp.backup_before_write(SCH, "step5_sch")
    open(SCH, "w", encoding="utf-8", newline="").write(s)
    print("saved", SCH)


if __name__ == "__main__":
    main()
