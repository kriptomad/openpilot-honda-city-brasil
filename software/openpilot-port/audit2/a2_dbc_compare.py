"""Audit 2: full structural DBC compare (cantools), message-by-message, signal-by-signal.

usage: python a2_dbc_compare.py <a.dbc> <b.dbc> [used_msgs_csv]
Prints every difference: messages only on one side, dlc, signals (start, length, byte_order, signed,
scale, offset, min, max, unit, receivers, choices), checksum/counter presence, senders.
If used_msgs_csv (comma-separated names/ids) is given, diffs are tagged USED/unused.
"""
import sys
import cantools


def _fix_id(m):
  i = int(m.group(2))
  if 0x7FF < i < 0x80000000:
    i |= 0x80000000
  return f"{m.group(1)}{i}"


def load(p):
  # drop single-line CM_ comments: v0.9.9 generator emits a malformed `CM_ SG_ 304 "..."` (no signal name)
  # opendbc writes 29-bit ids (0x33DA etc.) without the DBC extended bit; set it so cantools accepts them
  import re
  txt = open(p, encoding='utf-8').read()
  out = []
  for l in txt.splitlines():
    if l.startswith('CM_') and l.rstrip().endswith('";'):
      continue
    l = re.sub(r'^(BO_ |VAL_ |SIG_VALTYPE_ |BA_ "[^"]+" (?:BO_|SG_) )(\d+)', _fix_id, l)
    out.append(l)
  return cantools.database.load_string('\n'.join(out) + '\n', database_format='dbc', strict=False)


def sig_tuple(s):
  return (s.start, s.length, s.byte_order, s.is_signed, float(s.scale), float(s.offset),
          s.minimum, s.maximum, s.unit, tuple(sorted(s.receivers or [])),
          tuple(sorted((int(k), str(v)) for k, v in (s.choices or {}).items())),
          s.is_multiplexer, s.multiplexer_ids and tuple(s.multiplexer_ids))


def main():
  a, b = load(sys.argv[1]), load(sys.argv[2])
  used = set()
  if len(sys.argv) > 3:
    for tok in sys.argv[3].split(','):
      tok = tok.strip()
      if tok:
        used.add(int(tok, 0) if tok.lower().startswith('0x') or tok.isdigit() else tok)
  am = {m.frame_id: m for m in a.messages}
  bm = {m.frame_id: m for m in b.messages}
  diffs = []

  def tag(mid, name):
    return 'USED' if (mid in used or name in used) else '....'

  for mid in sorted(set(am) | set(bm)):
    if mid not in am:
      diffs.append((tag(mid, bm[mid].name), f"0x{mid:X} {bm[mid].name}: only in B"))
      continue
    if mid not in bm:
      diffs.append((tag(mid, am[mid].name), f"0x{mid:X} {am[mid].name}: only in A"))
      continue
    ma, mb = am[mid], bm[mid]
    t = tag(mid, ma.name)
    if ma.name != mb.name:
      diffs.append((t, f"0x{mid:X}: name {ma.name} -> {mb.name}"))
    if ma.length != mb.length:
      diffs.append((t, f"0x{mid:X} {ma.name}: dlc {ma.length} -> {mb.length}"))
    if sorted(ma.senders) != sorted(mb.senders):
      diffs.append((t, f"0x{mid:X} {ma.name}: senders {ma.senders} -> {mb.senders}"))
    sa = {s.name: s for s in ma.signals}
    sb = {s.name: s for s in mb.signals}
    # match by name
    for n in sorted(set(sa) | set(sb)):
      if n not in sa:
        s = sb[n]
        diffs.append((t, f"0x{mid:X} {ma.name}.{n}: only in B (start {s.start} len {s.length})"))
      elif n not in sb:
        s = sa[n]
        diffs.append((t, f"0x{mid:X} {ma.name}.{n}: only in A (start {s.start} len {s.length})"))
      else:
        ta, tb = sig_tuple(sa[n]), sig_tuple(sb[n])
        if ta != tb:
          fields = ['start', 'length', 'byte_order', 'signed', 'scale', 'offset', 'min', 'max', 'unit', 'receivers', 'choices', 'mux', 'muxids']
          d = [f"{f}: {x} -> {y}" for f, x, y in zip(fields, ta, tb) if x != y]
          diffs.append((t, f"0x{mid:X} {ma.name}.{n}: " + '; '.join(d)))
    # bit-position match: same (start,len) different names -> rename
    pa = {(s.start, s.length): s.name for s in ma.signals}
    pb = {(s.start, s.length): s.name for s in mb.signals}
    for k in sorted(set(pa) & set(pb)):
      if pa[k] != pb[k]:
        diffs.append((t, f"0x{mid:X} {ma.name}: bits {k} named {pa[k]} (A) vs {pb[k]} (B) [rename]"))
  for t, d in diffs:
    print(t, d)
  print(f"total diffs: {len(diffs)}; USED: {sum(1 for t, _ in diffs if t == 'USED')}")


if __name__ == '__main__':
  main()
