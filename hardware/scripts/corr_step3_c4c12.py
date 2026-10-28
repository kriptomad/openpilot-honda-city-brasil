"""Step 3 (item 6 closure): C4/C12 schematic Footprint field back to C_0805_2012Metric.

The 10 uF Cin of the TPS5450 stays physically 0805 (a 1206 does not fit at x = 113.635 without moving
C6/L4); the BOM part is a 10 uF 50 V X5R 0805 (e.g. Murata GRM21BR61H106KE43). The PCB already has 0805,
so the schematic field must match to keep schematic parity / lib_footprint_mismatch at zero.

Usage: python corr_step3_c4c12.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hp_common as hp  # noqa: E402

SCH = hp.OUTPUT_ROOT / "hardware" / "hybrid-panda" / "HybridPanda.kicad_sch"


def main():
    txt = SCH.read_text(encoding="utf-8")
    n = 0
    for ref in ("C4", "C12"):
        pat = re.compile(r'(\(property "Reference" "%s" .*?\(property "Footprint" ")Capacitor_SMD:C_1206_3216Metric"' % ref, re.S)
        txt, k = pat.subn(r'\1Capacitor_SMD:C_0805_2012Metric"', txt, count=1)
        n += k
        print("%s: %d replacement(s)" % (ref, k))
    if n:
        hp.backup_before_write(SCH, "step3_c4c12")
        SCH.write_text(txt, encoding="utf-8")
    print("done, %d changes" % n)


if __name__ == "__main__":
    main()
