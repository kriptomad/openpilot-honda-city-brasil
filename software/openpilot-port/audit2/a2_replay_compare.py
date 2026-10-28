"""Audit 2: compare replay outputs of the two trees (head v0.9.9 port vs upstream 43006b9a): CarParams, CarState rows, TX frames."""
import json
import os
import sys

T = os.environ.get('TEMP', '.')
h = json.load(open(os.path.join(T, 'city_rlog', 'replay_head.json')))
u = json.load(open(os.path.join(T, 'city_rlog', 'replay_up43.json')))
out = []
P = out.append

# ---- CarParams ours(head) vs ours(up43) vs logged
def flat(d, prefix=''):
  r = {}
  if isinstance(d, dict):
    for k, v in d.items():
      r.update(flat(v, f"{prefix}{k}."))
  elif isinstance(d, list):
    for i, v in enumerate(d):
      r.update(flat(v, f"{prefix}{i}."))
  else:
    r[prefix[:-1]] = d
  return r


ch, cu, cl = flat(h['carParams_ours']), flat(u['carParams_ours']), flat(h['carParams_logged'])
P("== CarParams: head(get_params) vs up43(get_params) ==")
keys = sorted(set(ch) | set(cu))
nd = 0
for k in keys:
  if k.startswith('carFw'):
    continue
  a, b = ch.get(k, '<absent>'), cu.get(k, '<absent>')
  if a != b and not (isinstance(a, float) and isinstance(b, float) and abs(a - b) < 1e-9):
    nd += 1
    P(f"  DIFF {k}: head={a!r} up43={b!r}")
P(f"  total compared keys={len(keys)} diffs={nd}")
P("== CarParams: head(get_params) vs logged upstream carParams (route) ==")
nd = 0
for k in sorted(set(ch) | set(cl)):
  if k.startswith('carFw') or k.endswith('DEPRECATED'):
    continue
  a, b = ch.get(k, '<absent>'), cl.get(k, '<absent>')
  if a != b and not (isinstance(a, float) and isinstance(b, float) and abs(a - b) < 1e-6):
    nd += 1
    P(f"  DIFF {k}: head={a!r} logged={b!r}")
P(f"  diffs={nd}")

# ---- CarState rows: head vs up43 (value at most recent can event, i.e. element 0 of tuple)
P("== CarState: head vs up43 per field (same CAN input) ==")
rows_h, rows_u = h['cs_rows'], u['cs_rows']
assert len(rows_h) == len(rows_u)
fields = sorted(set(rows_h[0]) | set(rows_u[0]))
for f in fields:
  n = 0
  ex = []
  for i, (rh, ru) in enumerate(zip(rows_h, rows_u)):
    a = rh.get(f, [None])[0]
    b = ru.get(f, [None])[0]
    if a != b and not (isinstance(a, float) and isinstance(b, float) and abs(a - b) < 1e-6):
      n += 1
      if len(ex) < 4:
        ex.append((i, a, b))
  P(f"  {f}: diffs={n} {ex}")
# vs logged (for reference, identical for both trees)
P("== CarState: head vs LOGGED upstream carState (time-aligned, window 4) ==")
for f, s in h['cs_summary'].items():
  P(f"  {f}: mismatches={s['mismatches']} ex={s['examples'][:3]}")

# ---- TX frames head vs up43
P("== TX frames: head vs up43 (same carControl schedule) ==")
th, tu = h['tx_rows'], u['tx_rows']
P(f"  cycles head={len(th)} up43={len(tu)}")
stats = {}
for i, (a, b) in enumerate(zip(th, tu)):
  da = {x[0]: (x[1], x[2]) for x in a}
  db = {x[0]: (x[1], x[2]) for x in b}
  for addr in set(da) | set(db):
    s = stats.setdefault(addr, [0, 0, []])
    s[0] += 1
    if da.get(addr) == db.get(addr):
      s[1] += 1
    elif len(s[2]) < 5:
      s[2].append((i, da.get(addr), db.get(addr)))
for addr in sorted(stats):
  s = stats[addr]
  P(f"  0x{addr:X}: frames={s[0]} identical={s[1]} diff_ex={s[2]}")
P("== TX vs logged sendcan (both trees give identical statistics -> harness scheduling only) ==")
for k in h['tx_jitter']:
  P(f"  head {k}: {h['tx_jitter'][k]}")
  P(f"  up43 {k}: {u['tx_jitter'][k]}")
P(f"  head tx_summary: { {k: {kk: vv for kk, vv in v.items() if kk != 'diff_ex'} for k, v in h['tx_summary'].items() if v['both']} }")
P(f"  up43 tx_summary: { {k: {kk: vv for kk, vv in v.items() if kk != 'diff_ex'} for k, v in u['tx_summary'].items() if v['both']} }")
P(f"apply exceptions head={len(h['mismatch_examples'])} up43={len(u['mismatch_examples'])}")
txt = "\n".join(out)
open(os.path.join(T, 'city_rlog', 'replay_compare.txt'), 'w').write(txt)
print(txt)
