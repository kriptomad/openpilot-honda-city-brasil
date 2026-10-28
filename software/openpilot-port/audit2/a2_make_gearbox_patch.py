"""Audit 2: build proposed-patches/0001-honda-civic-ex-2022-gearbox-cvt-layout.patch (DBC-only) and verify it.

Replaces the legacy byte0 one-hot GEARBOX 0x191 layout in honda_civic_ex_2022_can.dbc (used by HONDA_CITY_7G and
HONDA_HRV_3G on v0.9.9) with the upstream GEARBOX_CVT bit layout from opendbc 9ef0b1fb (_gearbox_common.dbc),
keeping the message name GEARBOX so carstate.py is untouched. Then: copies the HEAD generator tree to %TEMP%,
applies the patch, regenerates the DBC, decodes all 0x191 frames of the CI route and checks the gear decode
against the upstream-generated DBC.
"""
import os
import pickle
import shutil
import subprocess
import sys
import tempfile

AUDIT2 = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AUDIT2)  # software/openpilot-port
REPO = os.path.join(BASE, "..", "opendbc-v0.9.9-city-g7")
PATCH_DIR = os.path.join(AUDIT2, "proposed-patches")
TMP = os.path.join(tempfile.gettempdir(), "audit2_gearbox")
GEN_REL = "opendbc/dbc/generator/honda/honda_civic_ex_2022_can.dbc"

OLD_BO = """BO_ 401 GEARBOX: 8 PCM
 SG_ GEAR_SHIFTER : 5|6@0+ (1,0) [0|63] "" EON
 SG_ BOH : 45|6@0+ (1,0) [0|63] "" XXX
 SG_ GEAR2 : 31|8@0+ (1,0) [0|1] "" XXX
 SG_ GEAR : 39|8@0+ (1,0) [0|255] "" XXX
 SG_ ZEROS_BOH : 47|2@0+ (1,0) [0|3] "" XXX
 SG_ COUNTER : 61|2@0+ (1,0) [0|3] "" EON
 SG_ CHECKSUM : 59|4@0+ (1,0) [0|15] "" EON
"""
# upstream _gearbox_common.dbc GEARBOX_CVT (opendbc 9ef0b1fb), message name kept as GEARBOX for v0.9.9 carstate.py
NEW_BO = """BO_ 401 GEARBOX: 8 PCM
 SG_ SELECTED_P : 0|1@0+ (1,0) [0|1] "" XXX
 SG_ SELECTED_R : 1|1@0+ (1,0) [0|1] "" XXX
 SG_ SELECTED_N : 2|1@0+ (1,0) [0|1] "" XXX
 SG_ SELECTED_D : 3|1@0+ (1,0) [0|1] "" XXX
 SG_ FORWARD_DRIVING_MODE : 23|1@0+ (1,0) [0|1] "" XXX
 SG_ CVT_UNKNOWN_1 : 31|8@0+ (1,0) [0|255] "" XXX
 SG_ CVT_UNKNOWN_2 : 39|8@0+ (1,0) [0|255] "" XXX
 SG_ GEAR_SHIFTER : 44|5@0+ (1,0) [0|31] "" XXX
 SG_ SHIFTER_POSITION_VALID : 45|1@0+ (1,0) [0|1] "" XXX
 SG_ NOT_FORWARD_GEAR : 48|1@0+ (1,0) [0|1] "" XXX
 SG_ CVT_UNKNOWN_3 : 53|2@0+ (1,0) [0|3] "" XXX
 SG_ CHECKSUM : 59|4@0+ (1,0) [0|15] "" EON
 SG_ COUNTER : 61|2@0+ (1,0) [0|3] "" EON
"""
OLD_VAL = """VAL_ 401 GEAR_SHIFTER 32 "L" 16 "S" 8 "D" 4 "N" 2 "R" 1 "P";
VAL_ 401 GEAR 7 "L" 10 "S" 4 "D" 3 "N" 2 "R" 1 "P";
"""
NEW_VAL = """VAL_ 401 GEAR_SHIFTER 1 "P" 2 "R" 3 "N" 4 "D" 7 "L" 10 "S";
"""
OLD_CM = """CM_ 446 "If exists, describes cruise faults and what the PCM uses for brake press detection.";
"""
NEW_CM = """CM_ 446 "If exists, describes cruise faults and what the PCM uses for brake press detection.";
CM_ SG_ 401 CVT_UNKNOWN_1 "Probably measured/actual CVT ratio";
CM_ SG_ 401 CVT_UNKNOWN_2 "Probably target/commanded CVT ratio";
"""


def git(*a, cwd=REPO):
  return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


def main():
  os.makedirs(PATCH_DIR, exist_ok=True)
  if os.path.isdir(TMP):
    shutil.rmtree(TMP)
  os.makedirs(TMP)
  head = git("rev-parse", "--short", "HEAD").strip()
  orig = subprocess.run(["git", "cat-file", "-p", f"HEAD:{GEN_REL}"], cwd=REPO, capture_output=True, check=True).stdout.decode()
  assert orig.count(OLD_BO) == 1 and orig.count(OLD_VAL) == 1 and orig.count(OLD_CM) == 1, "generator file layout changed; patch not applicable"
  new = orig.replace(OLD_BO, NEW_BO).replace(OLD_VAL, NEW_VAL).replace(OLD_CM, NEW_CM)

  a = os.path.join(TMP, "a", GEN_REL.replace("/", os.sep))
  b = os.path.join(TMP, "b", GEN_REL.replace("/", os.sep))
  for p, txt in ((a, orig), (b, new)):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
      f.write(txt)
  r = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--no-index", "--no-prefix", "a", "b"], cwd=TMP, capture_output=True, text=True)
  # git --no-index --no-prefix emits "a/<path>" / "b/<path>" from the cwd-relative dirs (-p1 style); unquote header lines only
  diff = "\n".join((l.replace("\\", "/").replace('"', "") if l.startswith(("diff --git", "--- ", "+++ ")) else l)
                   for l in r.stdout.split("\n"))
  header = f"""From: audit2 <audit2@local>
Subject: [PATCH] Honda: civic_ex_2022 DBC: decode GEARBOX 0x191 with the upstream GEARBOX_CVT layout

Base: opendbc firmwarecityg7-v0.9.9 @ {head}
Source: upstream opendbc 9ef0b1fb (_gearbox_common.dbc, GEARBOX_CVT), applied DBC-only to
honda_civic_ex_2022_can.dbc (consumers on v0.9.9: HONDA_CITY_7G and HONDA_HRV_3G; HONDA_CIVIC_2022
reads 0x1A3/0x1DD instead). Message name kept as GEARBOX so opendbc/car/honda/carstate.py is unchanged.

Why: on v0.9.9 GEAR_SHIFTER is byte0 bits 5..0 with VAL 16=S 32=L; upstream (and the City/HR-V 3G routes in
upstream CI) decode GEAR_SHIFTER from byte5 bits 4..0 with VAL 1 P 2 R 3 N 4 D 7 L 10 S. P/R/N/D are
equivalent on the CI route (byte0=0x08, byte5&0x1F=4 on 6116/6116 frames) but S and L are not: with the
v0.9.9 layout, S is reported as drive (if byte0 stays 0x08) or unknown -> wrongGear.

CHECKSUM/COUNTER bit positions are unchanged (59|4, 61|2). Signals BOH/GEAR2/GEAR/ZEROS_BOH were not read
by any v0.9.9 code (grep opendbc/car/honda). Regenerate opendbc/dbc/honda_civic_ex_2022_can_generated.dbc
after applying (scons / generator.py).
---
"""
  patch_path = os.path.join(PATCH_DIR, "0001-honda-civic-ex-2022-gearbox-cvt-layout.patch")
  with open(patch_path, "w", newline="\n") as f:
    f.write(header + diff)
  print("wrote", patch_path)

  # --- verification: patched generator tree -> generated DBC -> decode route 0x191 frames
  gen_src = os.path.join(TMP, "gen")
  subprocess.run(["git", "archive", "--format=tar", "HEAD", "opendbc/dbc/generator", "opendbc/dbc/__init__.py"], cwd=REPO,
                 stdout=open(os.path.join(TMP, "gen.tar"), "wb"), check=True)
  os.makedirs(gen_src)
  subprocess.run(["tar", "-xf", os.path.join(TMP, "gen.tar"), "-C", gen_src], check=True)
  with open(os.path.join(gen_src, GEN_REL.replace("/", os.sep)), "w", newline="\n") as f:
    f.write(new)
  sys.path.insert(0, os.path.join(gen_src, "opendbc", "dbc", "generator"))
  import generator  # noqa: E402
  out_dir = os.path.join(TMP, "out")
  os.makedirs(out_dir)
  src_dir = os.path.join(gen_src, "opendbc", "dbc", "generator", "honda")
  generator.create_dbc(src_dir, "honda_civic_ex_2022_can.dbc", out_dir)
  gen_dbc = os.path.join(out_dir, "honda_civic_ex_2022_can_generated.dbc")

  import cantools  # noqa: F401
  sys.path.insert(0, AUDIT2)
  from a2_dbc_compare import load  # same sanitiser used for the DBC comparison (malformed CM_, 29-bit ids)

  db_new = load(gen_dbc)
  up_dbc = os.path.join(tempfile.gettempdir(), "audit2_dbc", "up43", "honda_civic_ex_2022_can_generated.dbc")
  db_up = load(up_dbc)
  m_new, m_up = db_new.get_message_by_frame_id(0x191), db_up.get_message_by_frame_id(0x191)
  sig = lambda m: sorted((s.name, s.start, s.length, s.byte_order, s.is_signed, s.scale, s.offset) for s in m.signals)
  print("message names:", m_new.name, "/", m_up.name)
  print("signal layout identical to upstream GEARBOX_CVT:", sig(m_new) == sig(m_up))
  ch_new = {s.name: s.choices for s in m_new.signals if s.choices}
  ch_up = {s.name: s.choices for s in m_up.signals if s.choices}
  print("VAL tables identical:", {k: dict(v) for k, v in ch_new.items()} == {k: dict(v) for k, v in ch_up.items()}, ch_new)

  ev = pickle.load(open(os.path.join(tempfile.gettempdir(), "city_rlog", "events.pkl"), "rb"))["events"]
  from collections import Counter
  c = Counter()
  n = 0
  for e in ev:
    if e[1] != "can":
      continue
    for addr, dat, bus in e[2]:
      if addr == 0x191 and bus == 0 and len(dat) == 8:
        n += 1
        dn = m_new.decode(dat, decode_choices=False)
        du = m_up.decode(dat, decode_choices=False)
        c[(int(dn["GEAR_SHIFTER"]), int(du["GEAR_SHIFTER"]), int(dn["SHIFTER_POSITION_VALID"]), int(dn["SELECTED_D"]))] += 1
  print(f"route 0x191 bus0 frames: {n}; (new GEAR_SHIFTER, upstream GEAR_SHIFTER, SHIFTER_POSITION_VALID, SELECTED_D) counts: {dict(c)}")
  shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
  main()
