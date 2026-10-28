"""Audit 2 - scan 1: rlog inventory + v0.9.9 parser checks.

For every (bus, addr): count, rate, dlc set. For the v0.9.9 City required list: rate >= required,
checksum failures, counter failures (update_counter_generic semantics), max gap vs check_threshold (10 periods).
Also: carParams dump, carFw, pandaStates type/safety, presence of key ids.
usage: python a2_scan1_inventory.py <head_dbc> [out_json]
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a2_common import read_events, DBC, decode, honda_checksum  # noqa: E402

# v0.9.9 carstate get_can_messages for City (Bosch radarless, cvt via GEARBOX, no EPB, no ALT_BRAKE, no BSM)
REQ_PT = {"ENGINE_DATA": 100, "WHEEL_SPEEDS": 50, "STEERING_SENSORS": 100, "SEATBELT_STATUS": 10, "CRUISE": 10,
          "POWERTRAIN_DATA": 100, "CAR_SPEED": 10, "VSA_STATUS": 50, "STEER_STATUS": 100, "STEER_MOTOR_TORQUE": 0,
          "SCM_FEEDBACK": 10, "SCM_BUTTONS": 25, "GEARBOX": 100, "CRUISE_FAULT_STATUS": 50}
REQ_CAM = {"STEERING_CONTROL": 100, "ACC_HUD": 10, "LKAS_HUD": 10}


def main():
  dbc = DBC(sys.argv[1])
  evs = read_events()
  print('events', len(evs))
  which = defaultdict(int)
  for e in evs:
    which[e.which()] += 1
  print({k: v for k, v in sorted(which.items())})

  frames = defaultdict(list)  # (src, addr) -> [(nanos, dat)]
  t0 = None
  t1 = None
  for e in evs:
    if e.which() == 'can':
      t = e.logMonoTime
      t0 = t if t0 is None else min(t0, t)
      t1 = t if t1 is None else max(t1, t)
      for c in e.can:
        frames[(c.src, c.address)].append((t, bytes(c.dat)))
  dur = (t1 - t0) / 1e9
  print(f'can span {dur:.2f}s')

  inv = {}
  for (src, addr), lst in sorted(frames.items()):
    dlcs = sorted({len(d) for _, d in lst})
    inv[f'{src}:0x{addr:X}'] = {'count': len(lst), 'hz': round(len(lst) / dur, 2), 'dlc': dlcs}
  for k, v in inv.items():
    print(k, v)

  # required list validation under v0.9.9 parser semantics
  print('\n=== v0.9.9 required messages, City ===')
  results = {}
  for bus, req in ((0, REQ_PT), (2, REQ_CAM)):
    for name, freq in req.items():
      m = dbc.by_name[name]
      lst = frames.get((bus, m.address), [])
      cs_fail = 0
      cnt_fail_events = 0
      counter_fail = 0
      max_counter_fail = 0
      prev_cnt = None
      has_cnt = any(s.is_counter for s in m.sig_list)
      dlc_mismatch = 0
      gaps = []
      prev_t = None
      for t, d in lst:
        vals, ok, cnt = decode(m, d)
        if not ok:
          cs_fail += 1
        if len(d) != m.size:
          dlc_mismatch += 1
        if has_cnt:
          if prev_cnt is not None:
            if ((prev_cnt + 1) & 3) != cnt:
              counter_fail = min(counter_fail + 1, 5)
              cnt_fail_events += 1
            elif counter_fail > 0:
              counter_fail -= 1
            max_counter_fail = max(max_counter_fail, counter_fail)
          prev_cnt = cnt
        if prev_t is not None:
          gaps.append(t - prev_t)
        prev_t = t
      thr = (1e9 / freq) * 10 if freq > 0 else None
      maxgap = max(gaps) / 1e6 if gaps else None
      r = {'bus': bus, 'addr': f'0x{m.address:X}', 'req_hz': freq, 'count': len(lst), 'hz': round(len(lst) / dur, 2),
           'dbc_dlc': m.size, 'dlc_mismatch': dlc_mismatch, 'checksum_fail': cs_fail, 'counter_fail_events': cnt_fail_events,
           'max_counter_fail_level': max_counter_fail, 'max_gap_ms': None if maxgap is None else round(maxgap, 1),
           'threshold_ms': None if thr is None else thr / 1e6,
           'ok': len(lst) > 0 and cs_fail == 0 and max_counter_fail < 5 and (thr is None or (maxgap or 0) < thr / 1e6)}
      results[name] = r
      print(name, r)

  print('\n=== key ids presence (bus 0) ===')
  for a, label in ((0x1C2, 'EPB_STATUS'), (0x191, 'GEARBOX'), (0x1AB, 'STEER_MOTOR_TORQUE'), (0x1A3, 'GEARBOX_ALT/AUTO'), (0x1BE, 'BRAKE_MODULE'),
                   (0x1B0, 'STANDSTILL'), (0x1A6, 'SCM_BUTTONS_nidec'), (0x1FA, 'LEGACY_BRAKE_COMMAND'), (0x1DF, 'ACC_CONTROL_ON'),
                   (0x1C8, 'ACC_CONTROL'), (0x30C, 'ACC_HUD'), (0x33D, 'LKAS_HUD'), (0xE4, 'STEERING_CONTROL'), (0x296, 'SCM_BUTTONS'),
                   (0x326, 'SCM_FEEDBACK'), (0x372, 'CRUISE_PARAMS'), (0x1D3, 'CRUISE_FAULT_STATUS')):
    row = {b: len(frames.get((b, a), [])) for b in range(3)}
    print(f'0x{a:X} {label}: {row}')
  ext = sorted({(s, a) for (s, a) in frames if a > 0x7FF})
  print('extended ids:', [(s, hex(a), len(frames[(s, a)])) for s, a in ext])
  print('0x33DA/0x33DB:', {b: len(frames.get((b, 0x33DA), [])) for b in range(3)}, {b: len(frames.get((b, 0x33DB), [])) for b in range(3)})
  bsm = [k for k in frames if k[1] in (0x1E3, 0x1E4, 0x1E5, 0x1E6, 0x3F8, 0x3F9)]
  print('BSM-ish ids on any bus:', bsm)

  # carParams / carFw / pandaStates
  print('\n=== carParams ===')
  cp = next(e.carParams for e in evs if e.which() == 'carParams')
  d = cp.to_dict()
  fw = d.pop('carFw', [])
  print(json.dumps(d, indent=1, default=str)[:6000])
  print('carFw:', [(f['ecu'], hex(f['address']), f.get('subAddress'), f['fwVersion'], f.get('request'), f.get('brand'), f.get('bus')) for f in fw])
  ps = [e for e in evs if e.which() == 'pandaStates']
  if ps:
    p = ps[0].pandaStates[0]
    print('pandaStates[0]:', p.pandaType, p.safetyModel, p.safetyParam, 'alt exp', p.alternativeExperience, 'harness', p.harnessStatus)
  out = sys.argv[2] if len(sys.argv) > 2 else None
  if out:
    json.dump({'inventory': inv, 'required': results, 'carParams': d, 'carFw': fw}, open(out, 'w'), indent=1, default=str)


if __name__ == '__main__':
  main()
