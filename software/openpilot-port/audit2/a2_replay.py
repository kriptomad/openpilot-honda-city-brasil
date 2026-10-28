"""Audit 2: run the REAL opendbc Honda code of one tree (HEAD v0.9.9 port or upstream 43006b9a) on the City CI rlog.

Usage: a2_replay.py <tree_label> <tree_root> <dbc_dir> <out_json>
  tree_label: head | up43
Produces:
  - CarParams computed by CarInterface.get_params (all fields, JSON) + compare vs logged carParams
  - CarState per CAN event (selected fields) vs logged carState (matched by order of can->carState)
  - sendcan frames produced by CarController.update fed with logged carControl vs logged sendcan
"""
import os
import sys
import json
import math
import importlib

label, root, dbc_dir, out_json = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['A2_DBC_DIR'] = dbc_dir
import pickle

sys.path.insert(0, root)
if label == 'head':
  import a2_v099_shim
  a2_v099_shim.install()
else:
  # upstream: pure python; make sure DBC_PATH points at the generated dbcs
  import opendbc
  opendbc.DBC_PATH = dbc_dir
  import opendbc.can.dbc as updbc
  updbc.DBC_PATH = dbc_dir

from opendbc.car import structs  # noqa: E402
from opendbc.car.honda.interface import CarInterface  # noqa: E402
from opendbc.car.honda.values import CAR  # noqa: E402
from opendbc.car.can_definitions import CanData  # noqa: E402

print(f"[{label}] opendbc root={root} dbc_dir={dbc_dir}")

with open(os.path.join(os.environ.get('TEMP', '.'), 'city_rlog', 'events.pkl'), 'rb') as fh:
  _d = pickle.load(fh)
events = _d['events']
cp_logged = _d['carParams']
car_fw = []
fingerprint = {0: {}, 1: {}, 2: {}, 3: {}}
for t, w, p in events:
  if w == 'can':
    for a, dat, src in p:
      if src in fingerprint:
        fingerprint[src][a] = len(dat)

for fw in cp_logged['_carFw']:
  f = structs.CarParams.CarFw()
  f.ecu = fw['ecu']
  f.fwVersion = fw['fwVersion']
  f.address = fw['address']
  f.subAddress = fw['subAddress']
  f.request = fw['request']
  f.brand = fw['brand']
  f.bus = fw['bus']
  f.logging = fw['logging']
  f.obdMultiplexing = fw['obdMultiplexing']
  car_fw.append(f)

# ---------------- CarParams ----------------
CP = CarInterface.get_params(CAR.HONDA_CITY_7G, fingerprint, car_fw, alpha_long=True, is_release=False, docs=False)
CP.carFw = car_fw


def to_plain(o):
  if hasattr(o, 'to_dict'):
    return to_plain(o.to_dict())
  if isinstance(o, dict):
    return {str(k): to_plain(v) for k, v in o.items()}
  if isinstance(o, (list, tuple)):
    return [to_plain(v) for v in o]
  if isinstance(o, bytes):
    return o.hex()
  if hasattr(o, '__dataclass_fields__'):
    return {k: to_plain(getattr(o, k)) for k in o.__dataclass_fields__}
  if isinstance(o, float):
    return round(o, 9)
  if hasattr(o, 'value') and hasattr(o, 'name'):
    return str(o)
  return o if isinstance(o, (int, str, bool, type(None))) else str(o)


cp_dict = to_plain(CP)
cp_logged_dict = to_plain({k: v for k, v in cp_logged.items() if k != '_carFw'})

# ---------------- CarState replay ----------------
CI = CarInterface(CP, None, None) if 'CarController' in CarInterface.__init__.__code__.co_varnames else None
if CI is None:
  CI = CarInterface(CP)
cs_cls = CI.CS
# can parsers
if hasattr(CI, 'can_parsers'):
  can_parsers = CI.can_parsers
else:
  can_parsers = CI.CS.get_can_parsers(CP) if hasattr(CI.CS, 'get_can_parsers') else None
print(f"[{label}] CarInterface attrs: {[a for a in dir(CI) if not a.startswith('_')][:30]}")

CS_FIELDS = ['vEgoRaw', 'standstill', 'gas', 'gasPressed', 'brake', 'brakePressed', 'brakeHoldActive', 'parkingBrake',
             'steeringAngleDeg', 'steeringRateDeg', 'steeringTorque', 'steeringTorqueEps', 'steeringPressed',
             'steerFaultTemporary', 'steerFaultPermanent', 'accFaulted', 'gearShifter', 'leftBlinker', 'rightBlinker',
             'doorOpen', 'seatbeltUnlatched', 'genericToggle', 'espDisabled', 'stockAeb', 'stockFcw', 'leftBlindspot',
             'rightBlindspot', 'cruiseState.enabled', 'cruiseState.available', 'cruiseState.speed', 'cruiseState.standstill',
             'cruiseState.nonAdaptive', 'cruiseState.speedCluster', 'canValid', 'canTimeout']


def getf(o, path):
  for p in path.split('.'):
    o = getattr(o, p) if not isinstance(o, dict) else o[p]
  return o


def norm(v):
  if hasattr(v, 'name') and not isinstance(v, (int, float, bool)):
    return str(v.name) if hasattr(v, 'name') else str(v)
  if isinstance(v, float):
    return round(v, 5)
  return v


def enum_str(v):
  s = str(v)
  if '.' in s:
    s = s.split('.')[-1]
  return s


cs_rows = []  # per can event: dict
tx_rows = []  # per carControl: list of (addr, hex, bus)
logged_cs = []
logged_cc = []
logged_sendcan = []

# Pair: upstream card.py loop: can -> CI.update -> carState; carControl -> CI.apply -> sendcan
# The rlog ordering: can event(s) then carState, carControl, sendcan.  We match sequentially.
CS_last = None
cs_hist = []
pending_cs = None
state = {'cs': 0, 'cc': 0}
mismatch_examples = []
now = 0
cc_buf = None
# pairing: each sendcan (after the first carControl) belongs to the most recent carControl before it (card.py: apply then publish)
_cc_idx = -1
_paired_cc = set()
_first_cc_t = None
for _t, _w, _p in events:
  if _w == 'carControl':
    _cc_idx += 1
    if _first_cc_t is None:
      _first_cc_t = _t
  elif _w == 'sendcan' and _first_cc_t is not None and _t > _first_cc_t:
    _paired_cc.add(_cc_idx)
print(f"[{label}] paired carControl cycles: {len(_paired_cc)}")
cc_counter = -1
latest_CC = None
prev_CC = None
LAG = int(os.environ.get('A2_CC_LAG', '1'))
_first_sc_t = min(_t for _t, _w, _p in events if _w == 'sendcan' and _t > _first_cc_t)


def g(d, path, default=None):
  for p in path.split('.'):
    if not isinstance(d, dict) or p not in d:
      return default
    d = d[p]
  return d


for t, w, p in events:
  if w == 'can':
    frames = [CanData(a, dat, src) for (a, dat, src) in p]
    CS_last = CI.update([(t, frames)])
    cs_hist.append(CS_last)
    if len(cs_hist) > 4:
      cs_hist.pop(0)
    now = t
    CC_apply = prev_CC if LAG else latest_CC
    prev_CC = latest_CC
    if CC_apply is not None and t >= _first_sc_t - 12_000_000:
      try:
        _, can_sends = CI.apply(CC_apply.as_reader() if hasattr(CC_apply, 'as_reader') else CC_apply, now)
      except Exception as ex:
        can_sends = []
        mismatch_examples.append(('apply-exception', repr(ex)[:200]))
      tx_rows.append([(a, d.hex(), b) for (a, d, b) in can_sends])
  elif w == 'carState' and CS_last is not None:
    row = {}
    for f in CS_FIELDS:
      try:
        b = g(p, f)
        b = enum_str(b) if f == 'gearShifter' else norm(b)
        cands = []
        for cs_ in reversed(cs_hist):
          a = getf(cs_, f)
          cands.append(enum_str(a) if f == 'gearShifter' else norm(a))
        # a = value at most recent can event; if any of the last 4 states equals logged -> alignment, keep that one
        a = cands[0]
        for cnd in cands:
          same = (abs(cnd - b) <= 1e-4) if isinstance(cnd, float) and isinstance(b, float) else (cnd == b)
          if same:
            a = cnd
            break
        row[f] = (a, b)
      except Exception as ex:
        row[f] = ('ERR', str(ex)[:60])
    cs_rows.append(row)
  elif w == 'carControl':
    cc = p
    CC = structs.CarControl()
    CC.enabled = cc['enabled']
    CC.latActive = cc['latActive']
    CC.longActive = cc['longActive']
    act = cc['actuators']
    CC.actuators.torque = act['torque']
    CC.actuators.accel = act['accel']
    CC.actuators.longControlState = cc['_longControlState']
    CC.actuators.speed = act['speed']
    CC.actuators.steeringAngleDeg = act['steeringAngleDeg']
    CC.actuators.torqueOutputCan = act['torqueOutputCan']
    CC.cruiseControl.cancel = cc['cruiseControl']['cancel']
    CC.cruiseControl.resume = cc['cruiseControl']['resume']
    CC.cruiseControl.override = cc['cruiseControl']['override']
    hud = cc['hudControl']
    CC.hudControl.speedVisible = hud['speedVisible']
    CC.hudControl.setSpeed = hud['setSpeed']
    CC.hudControl.lanesVisible = hud['lanesVisible']
    CC.hudControl.leadVisible = hud['leadVisible']
    CC.hudControl.visualAlert = cc['_visualAlert']
    CC.hudControl.audibleAlert = cc['_audibleAlert']
    CC.hudControl.rightLaneVisible = hud['rightLaneVisible']
    CC.hudControl.leftLaneVisible = hud['leftLaneVisible']
    CC.hudControl.rightLaneDepart = hud['rightLaneDepart']
    CC.hudControl.leftLaneDepart = hud['leftLaneDepart']
    CC.hudControl.leadDistanceBars = hud['leadDistanceBars']
    if 'leadDistance' in hud and hasattr(CC.hudControl, 'leadDistance'):
      CC.hudControl.leadDistance = hud['leadDistance']
    latest_CC = CC
  elif w == 'sendcan' and _first_cc_t is not None and t > _first_cc_t:
    logged_sendcan.append([(a, dat.hex(), src) for (a, dat, src) in p])

print(f"[{label}] cs_rows={len(cs_rows)} tx_rows={len(tx_rows)} logged_sendcan={len(logged_sendcan)}")

# ---- carState diff summary (ours vs logged) ----
cs_summary = {}
for f in CS_FIELDS:
  n = 0
  ex = []
  for i, row in enumerate(cs_rows):
    a, b = row.get(f, (None, None))
    if isinstance(a, float) and isinstance(b, float):
      bad = abs(a - b) > 1e-4
    else:
      bad = a != b
    if bad:
      n += 1
      if len(ex) < 5:
        ex.append((i, a, b))
  cs_summary[f] = {'mismatches': n, 'examples': ex}

# ---- sendcan comparison: ours (from logged carControl) vs logged sendcan ----
# Match by addr within the same index (sendcan i corresponds to carControl i: both published by card every cycle).
tx_summary = {}
n_pairs = min(len(tx_rows), len(logged_sendcan))
first_bad = []
addr_stats = {}
for i in range(n_pairs):
  ours = {a: (d, b) for (a, d, b) in tx_rows[i]}
  theirs = {a: (d, b) for (a, d, b) in logged_sendcan[i] if b in (0, 2)}
  for a in set(ours) | set(theirs):
    st = addr_stats.setdefault(a, {'both': 0, 'equal': 0, 'only_ours': 0, 'only_theirs': 0, 'diff_ex': []})
    if a in ours and a in theirs:
      st['both'] += 1
      if ours[a] == theirs[a]:
        st['equal'] += 1
      elif len(st['diff_ex']) < 6:
        st['diff_ex'].append((i, ours[a], theirs[a]))
    elif a in ours:
      st['only_ours'] += 1
    else:
      st['only_theirs'] += 1
tx_summary = {f"0x{a:X}": v for a, v in sorted(addr_stats.items())}


def masked(h):
  # drop honda counter (bits 5|4) + checksum (bits 3..0) of the last byte
  b = bytearray.fromhex(h)
  b[-1] &= 0xC0
  return b.hex()


# jitter analysis: for frames that differ, is the logged frame equal (payload-masked) to one of our frames at i-2..i+2 ?
jitter = {}
for a, st in addr_stats.items():
  ours_seq = [{aa: d for (aa, d, b) in row}.get(a) for row in tx_rows]
  theirs_seq = [{aa: d for (aa, d, b) in row if b in (0, 2)}.get(a) for row in logged_sendcan]
  n_diff = n_payload_eq = n_jit = n_real = 0
  real_ex = []
  cnt_bad = 0
  for i in range(n_pairs):
    o, th = ours_seq[i], theirs_seq[i]
    if o is None or th is None or o == th:
      continue
    n_diff += 1
    if masked(o) == masked(th):
      n_payload_eq += 1
      cnt_bad += 1
      continue
    neigh = [ours_seq[j] for j in range(max(0, i - 2), min(len(ours_seq), i + 3)) if ours_seq[j] is not None]
    if any(masked(x) == masked(th) for x in neigh):
      n_jit += 1
    else:
      n_real += 1
      if len(real_ex) < 8:
        real_ex.append((i, o, th))
  jitter[f"0x{a:X}"] = dict(n_diff=n_diff, payload_equal_counter_differs=n_payload_eq, explained_by_cc_jitter=n_jit, unexplained=n_real, unexplained_ex=real_ex)

out = {
  'label': label, 'root': root,
  'carParams_ours': cp_dict, 'carParams_logged': cp_logged_dict,
  'cs_summary': cs_summary, 'n_cs_rows': len(cs_rows),
  'tx_summary': tx_summary, 'n_tx_pairs': n_pairs, 'tx_jitter': jitter,
  'tx_rows': tx_rows, 'cs_rows_sample': cs_rows[:3],
  'cs_rows': cs_rows,
  'mismatch_examples': mismatch_examples,
  'parser_log': [getattr(p, 'log', [])[:20] for p in (can_parsers.values() if isinstance(can_parsers, dict) else [])],
}
with open(out_json, 'w') as f:
  json.dump(out, f, default=str)
print(f"[{label}] wrote {out_json}")
for f, s in cs_summary.items():
  if s['mismatches']:
    print(f"  CS {f}: {s['mismatches']} mismatches e.g. {s['examples'][:3]}")
for a, s in tx_summary.items():
  if s['both'] or s['only_ours']:
    print(f"  TX {a}: both={s['both']} equal={s['equal']} only_ours={s['only_ours']} only_theirs={s['only_theirs']} jitter={jitter.get(a)}")








