"""Byte-level TX equivalence check between two generated Honda DBCs (v0.9.9 port vs upstream).

Builds the frames the Honda City 7G path sends (STEERING_CONTROL 0xE4, LKAS_HUD 0x33D,
SCM_BUTTONS 0x296 spam, ACC_CONTROL 0x1C8 and ACC_HUD 0x30C when openpilot long is on)
with a self-contained big-endian packer that mimics opendbc's CANPacker (only the given
signals are written, COUNTER provided by the caller, Honda CHECKSUM computed last) and
compares the resulting bytes for a grid of input values.

usage: python tx_byte_compare.py <dbc_v099> <dbc_upstream>
"""
import re
import sys
import itertools

SG_RE = re.compile(r'^\s*SG_\s+(\w+)\s*(?:m\d+|M)?\s*:\s*(\d+)\|(\d+)@(\d)([+-])\s*\(([^,]+),([^)]+)\)')
BO_RE = re.compile(r'^BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)')


def load(path):
  msgs = {}
  cur = None
  for ln in open(path, encoding='utf-8', errors='replace'):
    m = BO_RE.match(ln)
    if m:
      cur = {'id': int(m.group(1)), 'name': m.group(2), 'size': int(m.group(3)), 'sigs': {}}
      msgs[cur['name']] = cur
      continue
    m = SG_RE.match(ln)
    if m and cur is not None:
      name, start, length, order, sign, factor, offset = m.groups()
      cur['sigs'][name] = dict(start=int(start), length=int(length), le=(order == '1'), signed=(sign == '-'),
                               factor=float(factor), offset=float(offset))
  return msgs


def honda_checksum(address, d):
  s = 0
  extended = address > 0x7FF
  addr = address
  while addr:
    s += addr & 0xF
    addr >>= 4
  for i in range(len(d)):
    x = d[i]
    if i == len(d) - 1:
      x >>= 4
    s += (x & 0xF) + (x >> 4)
  s = 8 - s
  if extended:
    s += 3
  return s & 0xF


def set_be(data, start_bit, length, value):
  # big-endian (Motorola) layout: DBC start bit is the MSB, bits run towards bit 0 of the byte, then
  # continue at bit 7 of the next byte
  bit = start_bit
  for i in range(length):
    byte, bit_in_byte = divmod(bit, 8)
    v = (value >> (length - 1 - i)) & 1
    if v:
      data[byte] |= (1 << bit_in_byte)
    else:
      data[byte] &= ~(1 << bit_in_byte) & 0xFF
    bit = bit + 15 if bit_in_byte == 0 else bit - 1


def pack(msg, values):
  data = bytearray(msg['size'])
  for name, v in values.items():
    if name not in msg['sigs']:
      raise KeyError(f"{msg['name']} has no signal {name}")
    s = msg['sigs'][name]
    assert not s['le'], 'little-endian signal unexpected in Honda DBC'
    iv = int(round((float(v) - s['offset']) / s['factor']))
    if s['signed'] and iv < 0:
      iv = (1 << s['length']) + iv
    iv &= (1 << s['length']) - 1
    set_be(data, s['start'], s['length'], iv)
  if 'CHECKSUM' in msg['sigs']:
    s = msg['sigs']['CHECKSUM']
    set_be(data, s['start'], s['length'], honda_checksum(msg['id'], data))
  return bytes(data)


def steering_control(torque, active, counter):
  return {'STEER_TORQUE': torque if active else 0, 'STEER_TORQUE_REQUEST': int(active), 'COUNTER': counter}


def lkas_hud(version, steer_required, lanes, lkas_problem, counter):
  v = {'SET_ME_X41': 0x41, 'STEERING_REQUIRED': steer_required, 'SOLID_LANES': lanes, 'BEEP': 0,
       'LANE_LINES': 3, 'DASHED_LANES': lanes, 'LKAS_PROBLEM': lkas_problem, 'COUNTER': counter}
  if version == 'v099':
    v['SET_ME_X48'] = 0x48
  else:
    v['LDW_OFF'] = 1
    v['SET_ME_X1'] = 1
  return v


def main():
  a = load(sys.argv[1])
  b = load(sys.argv[2])
  bad = 0
  n = 0

  def cmp(name, va, vb, label):
    nonlocal bad, n
    n += 1
    pa, pb = pack(a[name], va), pack(b[name], vb)
    if pa != pb:
      bad += 1
      print(f'DIFF {name} {label}: v099={pa.hex()} up={pb.hex()}')
    return pa

  # STEERING_CONTROL 0xE4
  for torque, active, counter in itertools.product([-2560, -1000, -1, 0, 1, 1234, 2560], [0, 1], range(4)):
    cmp('STEERING_CONTROL', steering_control(torque, active, counter), steering_control(torque, active, counter),
        f'torque={torque} active={active} ctr={counter}')

  # LKAS_HUD 0x33D
  for sr, lanes, prob, counter in itertools.product([0, 1], [0, 1], [0, 1], range(4)):
    ex = cmp('LKAS_HUD', lkas_hud('v099', sr, lanes, prob, counter), lkas_hud('up', sr, lanes, prob, counter),
             f'steer_req={sr} lanes={lanes} lkas_problem={prob} ctr={counter}')
  print('LKAS_HUD example bytes:', ex.hex())

  # SCM_BUTTONS 0x296 (spam_buttons_command)
  for btn, counter in itertools.product([0, 1, 2, 3, 4], range(4)):
    v = {'CRUISE_BUTTONS': btn, 'CRUISE_SETTING': 0, 'COUNTER': counter}
    cmp('SCM_BUTTONS', v, v, f'btn={btn} ctr={counter}')

  # ACC_CONTROL 0x1C8 (radarless openpilot longitudinal)
  for accel, enabled, standstill, idle, counter in itertools.product([-3.5, -1.0, 0.0, 0.5, 2.0], [0, 1], [0, 1], [0, 1], range(4)):
    v = {'ACCEL_COMMAND': accel, 'STANDSTILL': standstill, 'CONTROL_ON': enabled, 'IDLESTOP_ALLOW': idle, 'COUNTER': counter}
    cmp('ACC_CONTROL', v, v, f'accel={accel} en={enabled} ss={standstill} idle={idle} ctr={counter}')

  # ACC_HUD 0x30C (radarless openpilot longitudinal, Bosch branch)
  for vc, enabled, bars, imperial, lead, counter in itertools.product([0, 30, 100, 255], [0, 1], [0, 1, 2, 3], [0, 1], [0, 1, 2], range(4)):
    v = {'CRUISE_SPEED': vc, 'ENABLE_MINI_CAR': enabled, 'HUD_DISTANCE': bars, 'IMPERIAL_UNIT': imperial, 'HUD_LEAD': lead,
         'SET_ME_X01_2': 1, 'ACC_ON': enabled, 'FCM_OFF': 1, 'FCM_OFF_2': 1, 'COUNTER': counter}
    cmp('ACC_HUD', v, v, f'vc={vc} en={enabled} bars={bars} imp={imperial} lead={lead} ctr={counter}')

  # sanity: message ids / sizes identical for everything the City TX/RX path touches
  for name in ['STEERING_CONTROL', 'LKAS_HUD', 'SCM_BUTTONS', 'ACC_CONTROL', 'ACC_HUD', 'BOSCH_SUPPLEMENTAL_1']:
    if (a[name]['id'], a[name]['size']) != (b[name]['id'], b[name]['size']):
      bad += 1
      print('DIFF id/size', name, a[name]['id'], a[name]['size'], b[name]['id'], b[name]['size'])

  print(f'frames compared={n} differences={bad}')

  # cross-check the local packer against cantools on the v0.9.9 DBC (bit placement)
  try:
    import cantools
    import io
    # cantools chokes on some generator output: keep only BO_/SG_ lines (plus a minimal header)
    keep = ['VERSION ""', '', 'NS_ :', '', 'BS_:', '', 'BU_: XXX', '']
    skip = False
    for ln in open(sys.argv[1], encoding='utf-8', errors='replace'):
      if ln.startswith('BO_ '):
        skip = int(ln.split()[1]) > 0x7FF  # cantools rejects 29-bit ids declared as standard frames
      if skip:
        continue
      if ln.startswith('BO_ ') or ln.startswith(' SG_') or ln.startswith('SG_'):
        keep.append(ln.rstrip('\n'))
      elif keep and keep[-1].startswith(('BO_', ' SG_')) and not ln.strip():
        keep.append('')
    db = cantools.database.load(io.StringIO('\n'.join(keep)), database_format='dbc', strict=False)
    for name, vals in [('STEERING_CONTROL', steering_control(-1234, 1, 2)), ('LKAS_HUD', lkas_hud('v099', 1, 1, 0, 3)),
                       ('SCM_BUTTONS', {'CRUISE_BUTTONS': 3, 'CRUISE_SETTING': 0, 'COUNTER': 1})]:
      m = db.get_message_by_name(name)
      mine = pack(a[name], vals)
      full = {s.name: 0 for s in m.signals}
      full.update(vals)
      full['CHECKSUM'] = mine[-1] & 0xF
      try:
        ct = m.encode(full, scaling=True, padding=False, strict=False)
      except Exception as e:  # cantools cannot encode messages with overlapping signals (LKAS_HUD)
        print(f'cantools cross-check {name}: skipped ({e})')
        continue
      print(f'cantools cross-check {name}: {"ok" if ct == mine else "MISMATCH"} mine={mine.hex()} cantools={ct.hex()}')
      bad += ct != mine
  except Exception as e:  # pragma: no cover
    print('cantools cross-check skipped:', e)

  sys.exit(1 if bad else 0)


if __name__ == '__main__':
  main()


