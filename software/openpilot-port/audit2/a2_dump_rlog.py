"""Audit 2: dump the City rlog into a pickle (plain python objects) so the replay can run without pycapnp
(loading log.capnp and opendbc's car.capnp in the same process crashes pycapnp on Windows: duplicate schema ids).
Output: TEMP/city_rlog/events.pkl
"""
import os
import sys
import pickle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a2_common

OUT = os.path.join(os.environ.get('TEMP', '.'), 'city_rlog', 'events.pkl')


def plain(o):
  if hasattr(o, 'to_dict'):
    o = o.to_dict()
  if isinstance(o, dict):
    return {k: plain(v) for k, v in o.items()}
  if isinstance(o, (list, tuple)) or type(o).__name__ == '_DynamicListReader':
    return [plain(v) for v in o]
  if isinstance(o, (bytes, bytearray, memoryview)):
    return bytes(o)
  if type(o).__name__ in ('_DynamicEnum',):
    return str(o)
  return o


evs = []
cp = None
for e in a2_common.read_events():
  w = e.which()
  t = e.logMonoTime
  if w == 'can':
    evs.append((t, 'can', [(c.address, bytes(c.dat), c.src) for c in e.can]))
  elif w == 'sendcan':
    evs.append((t, 'sendcan', [(c.address, bytes(c.dat), c.src) for c in e.sendcan]))
  elif w == 'carState':
    evs.append((t, 'carState', plain(e.carState)))
  elif w == 'carControl':
    d = plain(e.carControl)
    d['_longControlState'] = int(e.carControl.actuators.longControlState.raw)
    d['_visualAlert'] = int(e.carControl.hudControl.visualAlert.raw)
    d['_audibleAlert'] = int(e.carControl.hudControl.audibleAlert.raw)
    evs.append((t, 'carControl', d))
  elif w == 'carParams' and cp is None:
    cp = plain(e.carParams)
    cp['_carFw'] = [dict(ecu=str(f.ecu), fwVersion=bytes(f.fwVersion), address=f.address, subAddress=f.subAddress,
                         request=[bytes(x) for x in f.request], brand=f.brand, bus=f.bus, logging=f.logging,
                         obdMultiplexing=f.obdMultiplexing) for f in e.carParams.carFw]
  elif w == 'pandaStates':
    evs.append((t, 'pandaStates', [dict(safetyModel=str(p.safetyModel), safetyParam=p.safetyParam, pandaType=str(p.pandaType),
                                        controlsAllowed=p.controlsAllowed, ignitionLine=p.ignitionLine, harnessStatus=str(p.harnessStatus),
                                        alternativeExperience=p.alternativeExperience, safetyRxChecksInvalid=p.safetyRxChecksInvalid,
                                        safetyTxBlocked=p.safetyTxBlocked, safetyRxInvalid=p.safetyRxInvalid, 
                                        ) for p in e.pandaStates]))

for i, ev in enumerate(evs):
  try:
    pickle.dumps(ev)
  except Exception as ex:
    print('BAD', i, ev[1], ex, [type(x) for x in (ev[2] if isinstance(ev[2], list) else [ev[2]])][:3]); break
try:
  pickle.dumps(cp)
except Exception as ex:
  print('BAD cp', ex, {k: type(v) for k, v in cp.items()})
with open(OUT, 'wb') as f:
  pickle.dump({'events': evs, 'carParams': cp}, f)
print('wrote', OUT, len(evs), 'events')




