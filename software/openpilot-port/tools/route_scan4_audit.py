"""City route scan for the v0.9.9 port audit.

Reads the public City CI rlog (segment 0) and prints:
  1. carParams fields recorded by upstream openpilot (ground truth for upstream CarParams)
  2. carFw list (ecu, addr, subAddr, fwVersion) recorded in carParams
  3. per-bus message rates (bus 0/1/2) and DLC for every address
  4. the CAN fingerprint dict {bus: {addr: dlc}} like openpilot's can_fingerprint()
  5. GEARBOX 0x191 raw byte0/byte5 pairs (v0.9.9 GEAR_SHIFTER vs upstream GEARBOX_CVT GEAR_SHIFTER)
  6. presence/counts of 0x1AB STEER_MOTOR_TORQUE, 0x1C2 EPB_STATUS, 0x1BE BRAKE_MODULE, 0x33DA, 0x18DAB0F1

usage: python route_scan4_audit.py <rlog.zst> <schema_dir> [out.json]

schema_dir must contain cereal's log.capnp, legacy.capnp, custom.capnp, include/c++.capnp (openpilot v0.9.9 tree)
plus a real copy of opendbc/car/car.capnp (in the openpilot tree cereal/car.capnp is a symlink into the
opendbc_repo submodule, which pycapnp on Windows cannot follow).
"""
import collections
import json
import sys
import warnings

import capnp
import zstandard

warnings.filterwarnings('ignore')
capnp.remove_import_hook()

rlog, schema_dir = sys.argv[1], sys.argv[2]
out_json = sys.argv[3] if len(sys.argv) > 3 else None
log = capnp.load(schema_dir + r'\log.capnp')
raw = zstandard.ZstdDecompressor().stream_reader(open(rlog, 'rb')).read()

frames = collections.defaultdict(list)   # (bus, addr) -> [(t, dat)]
cp_event = None
first_t = None
last_t = None
n_events = 0
for ev in log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30):
  n_events += 1
  w = ev.which()
  if w == 'carParams' and cp_event is None:
    cp_event = ev.carParams.to_dict()
  elif w == 'can':
    t = ev.logMonoTime
    first_t = t if first_t is None else first_t
    last_t = t
    for c in ev.can:
      frames[(c.src, c.address)].append((t, bytes(c.dat)))

dur = (last_t - first_t) / 1e9
print(f'events={n_events} can_duration={dur:.1f}s')

# 1. carParams
if cp_event:
  skip = {'carFw', 'lateralTuning', 'longitudinalTuning', 'safetyConfigs', 'lateralParams'}
  print('\n== carParams (upstream, recorded in route) ==')
  for k in sorted(cp_event):
    if k in skip:
      continue
    print(f'  {k} = {cp_event[k]!r}')
  print('  lateralParams =', cp_event.get('lateralParams'))
  print('  lateralTuning =', cp_event.get('lateralTuning'))
  print('  longitudinalTuning =', cp_event.get('longitudinalTuning'))
  print('  safetyConfigs =', cp_event.get('safetyConfigs'))
  print('\n== carFw ==')
  for fw in cp_event.get('carFw', []):
    print(f"  {fw.get('ecu')} addr=0x{fw.get('address', 0):X} sub={fw.get('subAddress')} bus={fw.get('bus')} "
          f"req={fw.get('request')} fw={bytes(fw.get('fwVersion', b''))!r} brand={fw.get('brand')} logging={fw.get('logging')}")

# 3/4. rates and fingerprint
print('\n== message rates (bus addr name? dlc count hz) ==')
fp = collections.defaultdict(dict)
rates = {}
for (bus, addr), lst in sorted(frames.items()):
  dlcs = collections.Counter(len(d) for _, d in lst)
  hz = len(lst) / dur if dur else 0
  rates[(bus, addr)] = (hz, dict(dlcs))
  if bus in (0, 1, 2):
    fp[bus][addr] = max(dlcs, key=dlcs.get)
  if bus in (0, 1, 2):
    print(f'  bus{bus} 0x{addr:X} dlc={dict(dlcs)} n={len(lst)} hz={hz:.1f}')

print('\n== fingerprint by bus (addr: dlc) ==')
for bus in sorted(fp):
  print(f'  {bus}: {{' + ', '.join(f'0x{a:X}: {l}' for a, l in sorted(fp[bus].items())) + '}')

# 5. gearbox pairs
print('\n== 0x191 GEARBOX byte0 (v0.9.9 GEAR_SHIFTER bits5..0) vs byte5 low5 (upstream GEARBOX_CVT GEAR_SHIFTER) ==')
pairs = collections.Counter()
for _, d in frames.get((0, 0x191), []):
  pairs[(d[0] & 0x3F, d[5] & 0x1F, d[0] & 0x0F)] += 1
for (b0, b5, low4), n in pairs.most_common():
  print(f'  byte0&0x3F={b0:2d} byte5&0x1F={b5:2d} (byte0 one-hot P/R/N/D bits={low4:04b}) n={n}')

# 6. presence
print('\n== presence of key addresses ==')
for addr, name in [(0x1AB, 'STEER_MOTOR_TORQUE'), (0x1C2, 'EPB_STATUS'), (0x1BE, 'BRAKE_MODULE'), (0x33DA, 'LKAS_HUD_A'),
                   (0x33DB, 'LKAS_HUD_B'), (0x1B0, 'STANDSTILL'), (0x1A3, 'GEARBOX_AUTO'), (0x191, 'GEARBOX_CVT'),
                   (0x18DAB0F1, 'radar diag'), (0x12f8bfa7, 'BSM'), (0x1FA, 'BRAKE_COMMAND'), (0x1DF, 'ACC_CONTROL'),
                   (0x1C8, 'ACC_CONTROL_ON'), (0x30C, 'ACC_HUD'), (0xE4, 'STEERING_CONTROL'), (0xE5, 'BOSCH_SUPPLEMENTAL_1'),
                   (0x33D, 'LKAS_HUD'), (0x296, 'SCM_BUTTONS'), (0x326, 'SCM_FEEDBACK'), (0x1A6, 'SCM_BUTTONS_NIDEC'),
                   (0x37C, 'CRUISE_FAULT_STATUS'), (0x3BB, 'LANE_LINES?'), (0x1F3, 'VSA_STATUS?')]:
  found = {bus: len(frames[(bus, addr)]) for bus in (0, 1, 2) if (bus, addr) in frames}
  print(f'  0x{addr:X} {name}: {found if found else "ABSENT"}')

if out_json:
  json.dump({'carParams': cp_event, 'fingerprint': {str(b): {str(a): l for a, l in d.items()} for b, d in fp.items()},
             'rates': {f'{b}:{a:#x}': r for (b, a), r in rates.items()}, 'duration': dur},
            open(out_json, 'w'), indent=1, default=str)
  print('wrote', out_json)
