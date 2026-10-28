"""Compute the Honda City 7G CarParams with the opendbc tree of the port branch (v0.9.9 base)
and compare them field by field with the carParams event logged by upstream in the CI route.

usage: python carparams_compare.py <opendbc_root> <route_scan4.json> [--alpha-long]

The Cython CAN parser is not built on Windows, so opendbc.can.parser_pyx is stubbed.
"""
import json
import sys
import types
import dataclasses


def stub_parser():
  for mod in ('opendbc.can.parser_pyx', 'opendbc.can.packer_pyx'):
    m = types.ModuleType(mod)
    for n in ('CANDefine', 'CANParser', 'CANPacker'):
      setattr(m, n, type(n, (), {'__init__': lambda self, *a, **k: None}))
    sys.modules[mod] = m


def to_plain(obj):
  if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
    return {f.name: to_plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
  if isinstance(obj, (list, tuple)):
    return [to_plain(x) for x in obj]
  if isinstance(obj, dict):
    return {k: to_plain(v) for k, v in obj.items()}
  if hasattr(obj, 'name') and hasattr(obj, 'value'):  # enum
    return obj.name
  return obj


def flatten(d, prefix=''):
  out = {}
  if isinstance(d, dict):
    for k, v in d.items():
      out.update(flatten(v, f'{prefix}{k}.'))
  elif isinstance(d, list) and d and isinstance(d[0], dict):
    for i, v in enumerate(d):
      out.update(flatten(v, f'{prefix}{i}.'))
  else:
    out[prefix[:-1]] = d
  return out


def main():
  root, scan = sys.argv[1], sys.argv[2]
  alpha_long = '--alpha-long' in sys.argv
  sys.path.insert(0, root)
  stub_parser()
  from opendbc.car import structs
  from opendbc.car.honda.interface import CarInterface
  from opendbc.car.honda.values import CAR
  from opendbc.car.honda.fingerprints import FW_VERSIONS

  d = json.load(open(scan))
  fp = {int(b): {int(a): dlc for a, dlc in addrs.items()} for b, addrs in d['fingerprint'].items()}
  up = d['carParams']

  car_fw = []
  for (ecu, addr, sub), fws in FW_VERSIONS[CAR.HONDA_CITY_7G].items():
    car_fw.append(structs.CarParams.CarFw(ecu=ecu, fwVersion=fws[0], address=addr, subAddress=sub or 0, brand='honda'))

  cp = CarInterface.get_params(CAR.HONDA_CITY_7G, fp, car_fw, alpha_long=alpha_long, is_release=False, docs=False)
  port = flatten(cp.to_dict())
  upf = flatten(up)

  # lateralTuning union -> upstream log shows {'torque': {...}}
  lat = {}
  for k, v in list(port.items()):
    if k.startswith('lateralTuning.'):
      lat[k] = v
  if cp.lateralTuning.which == 'torque' if hasattr(cp.lateralTuning, 'which') else True:
    pass

  keys = sorted(set(port) | set(upf))
  same = diff = only = 0
  print(f'{"field":45s} {"port v0.9.9":>28s} {"upstream route":>28s}  status')
  for k in keys:
    a = port.get(k, '<absent>')
    b = upf.get(k, '<absent>')
    if a == '<absent>' or b == '<absent>':
      status = 'ONLY-ONE'
      only += 1
    else:
      eq = (abs(a - b) < 1e-5) if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) else (a == b)
      status = 'ok' if eq else 'DIFF'
      same += eq
      diff += not eq
    if status != 'ok':
      print(f'{k:45s} {str(a)[:28]:>28s} {str(b)[:28]:>28s}  {status}')
  print(f'\nequal={same} diff={diff} only-one-side={only}')


if __name__ == '__main__':
  main()

