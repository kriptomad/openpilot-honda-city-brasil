"""Structural comparison of two generated DBC files (text parse, no cantools needed).

For every message id present in either file, compares signal layouts
(start, length, byte order, signedness, factor, offset, min/max) and VAL_ tables.
Prints renames (same layout), layout changes, signals only on one side, VAL_ changes.

usage: python dbc_struct_compare.py <a.dbc> <b.dbc> [label_a] [label_b] [--only 0x158,0x17C,...]
"""
import re
import sys

SG_RE = re.compile(r'^\s*SG_\s+(\w+)\s*(M|m\d+)?\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(([^,]+),([^)]+)\)\s*\[([^|]*)\|([^\]]*)\]\s*"([^"]*)"')
BO_RE = re.compile(r'^BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+)')
VAL_RE = re.compile(r'^VAL_\s+(\d+)\s+(\w+)\s+(.*);')


def parse(path):
  msgs = {}
  vals = {}
  cur = None
  for line in open(path, encoding='utf-8', errors='replace'):
    m = BO_RE.match(line)
    if m:
      fid = int(m.group(1)) & 0x1FFFFFFF
      cur = fid
      msgs[fid] = {'name': m.group(2), 'len': int(m.group(3)), 'sigs': {}}
      continue
    m = SG_RE.match(line)
    if m and cur is not None:
      name = m.group(1)
      msgs[cur]['sigs'][name] = (int(m.group(3)), int(m.group(4)), m.group(5), m.group(6),
                                 float(m.group(7)), float(m.group(8)), m.group(9).strip(), m.group(10).strip())
      continue
    if line.strip() and not line.startswith(' '):
      cur = None if not line.startswith('BO_') else cur
    m = VAL_RE.match(line)
    if m:
      fid = int(m.group(1)) & 0x1FFFFFFF
      pairs = re.findall(r'(-?\d+)\s+"([^"]*)"', m.group(3))
      vals[(fid, m.group(2))] = {int(k): v for k, v in pairs}
  return msgs, vals


def layout(s):
  return s[:6]


def main():
  a, b = sys.argv[1], sys.argv[2]
  la = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 'A'
  lb = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 'B'
  only = None
  if '--only' in sys.argv:
    only = {int(x, 16) for x in sys.argv[sys.argv.index('--only') + 1].split(',')}
  ma, va = parse(a)
  mb, vb = parse(b)
  ids = sorted(set(ma) | set(mb))
  if only:
    ids = [i for i in ids if i in only]
  for fid in ids:
    A, B = ma.get(fid), mb.get(fid)
    if A is None or B is None:
      side = la if A else lb
      print(f'0x{fid:X}: only in {side} ({(A or B)["name"]})')
      continue
    out = []
    if A['name'] != B['name']:
      out.append(f'  msg renamed {A["name"]} -> {B["name"]}')
    if A['len'] != B['len']:
      out.append(f'  DLC differs {A["len"]} -> {B["len"]}')
    sa, sb = A['sigs'], B['sigs']
    ka = {layout(v): k for k, v in sa.items()}
    kb = {layout(v): k for k, v in sb.items()}
    for name in sorted(set(sa) & set(sb)):
      if sa[name] != sb[name]:
        out.append(f'  CHANGED {name}: {la}={sa[name]} {lb}={sb[name]}')
    for name in sorted(set(sa) - set(sb)):
      lay = layout(sa[name])
      if lay in kb:
        out.append(f'  renamed(same layout) {name} -> {kb[lay]}  {lay}')
      else:
        out.append(f'  only {la}: {name} {sa[name]}')
    for name in sorted(set(sb) - set(sa)):
      lay = layout(sb[name])
      if lay not in ka:
        out.append(f'  only {lb}: {name} {sb[name]}')
    # VAL_ tables
    for (vfid, sig), tab in sorted(va.items()):
      if vfid != fid:
        continue
      # find counterpart by name or by same layout
      other = None
      if (fid, sig) in vb:
        other = vb[(fid, sig)]
        osig = sig
      elif sig in sa and layout(sa[sig]) in kb and (fid, kb[layout(sa[sig])]) in vb:
        osig = kb[layout(sa[sig])]
        other = vb[(fid, osig)]
      if other is None:
        out.append(f'  VAL_ only {la}: {sig} {tab}')
      elif other != tab:
        out.append(f'  VAL_ CHANGED {sig}->{osig}: {la}={tab} {lb}={other}')
    for (vfid, sig), tab in sorted(vb.items()):
      if vfid != fid:
        continue
      if (fid, sig) in va:
        continue
      if sig in sb and layout(sb[sig]) in ka and (fid, ka[layout(sb[sig])]) in va:
        continue
      out.append(f'  VAL_ only {lb}: {sig} {tab}')
    if out:
      print(f'0x{fid:X} {A["name"]} / {B["name"]} (dlc {A["len"]})')
      print('\n'.join(out))


if __name__ == '__main__':
  main()
