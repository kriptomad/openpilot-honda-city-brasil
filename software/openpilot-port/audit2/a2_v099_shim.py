"""Audit 2: pure-Python stand-ins for opendbc.can.parser_pyx / packer_pyx of the v0.9.9 tree.

Semantics copied from opendbc/can/parser.cc, packer.cc, dbc.cc, parser_pyx.pyx at e370a036 (v0.9.9):
 - CANParser(dbc_name, [(msg, freq), ...], bus): static list; all signals of listed msgs parsed; vl[addr] is vl[name];
   checksum + counter validated for every listed message; can_valid as UpdateValid(); freq 0 => never times out.
 - CANDefine(dbc_name).dv[msg][sig] = {int: str} (and by address)
 - CANPacker(dbc_name).make_can_msg(name_or_addr, bus, values) -> (addr, bytes, bus) with auto counter + honda checksum
DBC files are resolved in DBC_DIR (generated dbcs are not in git).
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a2_common import DBC, decode, Packer  # noqa: E402

DBC_DIR = os.environ.get('A2_DBC_DIR', os.path.join(os.environ.get('TEMP', '.'), 'audit2_dbc', 'head'))
MAX_BAD_COUNTER = 5
CAN_INVALID_CNT = 5
_dbc_cache = {}


def dbc_lookup(name):
  if name not in _dbc_cache:
    _dbc_cache[name] = DBC(os.path.join(DBC_DIR, name + '.dbc'))
  return _dbc_cache[name]


class _State:
  __slots__ = ('msg', 'check_threshold', 'counter', 'counter_fail', 'last_seen_nanos')

  def __init__(self, msg, freq):
    self.msg = msg
    self.check_threshold = int((1_000_000_000 // freq) * 10) if freq > 0 else 0
    self.counter = 0
    self.counter_fail = 0
    self.last_seen_nanos = 0


class CANParser:
  def __init__(self, dbc_name, messages, bus=0):
    self.dbc_name = dbc_name
    self.bus = bus
    self.dbc = dbc_lookup(dbc_name)
    self.vl = {}
    self.vl_all = {}
    self.states = {}
    self.first_nanos = 0
    self.last_nonempty_nanos = 0
    self.bus_timeout_threshold = 2**64 - 1
    self._bus_timeout = False
    self.can_invalid_cnt = CAN_INVALID_CNT
    self._can_valid = False
    for name_or_addr, freq in messages:
      m = self.dbc.msgs[name_or_addr] if isinstance(name_or_addr, int) else self.dbc.by_name.get(name_or_addr)
      if m is None:
        raise RuntimeError(f"could not find message {name_or_addr!r} in DBC {dbc_name}")
      if m.address in self.states:
        raise RuntimeError(f"Duplicate Message Check: {m.address}")
      st = _State(m, freq)
      if freq > 0:
        self.bus_timeout_threshold = min(self.bus_timeout_threshold, st.check_threshold)
      self.states[m.address] = st
      self.vl[m.address] = {s.name: 0.0 for s in m.sig_list}
      self.vl[m.name] = self.vl[m.address]
      self.vl_all[m.address] = defaultdict(list)
      self.vl_all[m.name] = self.vl_all[m.address]
    self.log = []  # (nanos, event)

  def update_strings(self, strings, sendcan=False):
    for a in self.states:
      self.vl_all[a].clear()
    if len(strings) and not isinstance(strings[0], (list, tuple)):
      strings = [strings]
    updated = set()
    for nanos, frames in strings:
      if self.first_nanos == 0:
        self.first_nanos = nanos
      bus_empty = True
      for address, dat, src in frames:
        if src != self.bus:
          continue
        bus_empty = False
        st = self.states.get(address)
        if st is None or len(dat) > 64:
          continue
        vals, cs_ok, cnt = decode(st.msg, dat)
        counter_failed = False
        if cnt is not None:
          if ((st.counter + 1) & 3) != cnt:
            st.counter_fail = min(st.counter_fail + 1, MAX_BAD_COUNTER)
            counter_failed = st.counter_fail >= MAX_BAD_COUNTER
            if st.counter_fail > 1:
              self.log.append((nanos, f"0x{address:X} COUNTER FAIL #{st.counter_fail} {st.counter}->{cnt}"))
          elif st.counter_fail > 0:
            st.counter_fail -= 1
          st.counter = cnt
        if not cs_ok:
          self.log.append((nanos, f"0x{address:X} checksum failed"))
        if not cs_ok or counter_failed:
          continue
        vl = self.vl[address]
        for k, v in vals.items():
          vl[k] = v
          self.vl_all[address][k].append(v)
        st.last_seen_nanos = nanos
        updated.add(address)
      if not bus_empty:
        self.last_nonempty_nanos = nanos
      self._bus_timeout = (nanos - self.last_nonempty_nanos) > self.bus_timeout_threshold
      # UpdateValid
      valid = True
      counters_valid = True
      for st in self.states.values():
        if st.counter_fail >= MAX_BAD_COUNTER:
          counters_valid = False
        missing = st.last_seen_nanos == 0
        timed_out = (nanos - st.last_seen_nanos) > st.check_threshold
        if st.check_threshold > 0 and (missing or timed_out):
          valid = False
      self.can_invalid_cnt = 0 if valid else self.can_invalid_cnt + 1
      self._can_valid = (self.can_invalid_cnt < CAN_INVALID_CNT) and counters_valid
    return updated

  @property
  def can_valid(self):
    return self._can_valid

  @property
  def bus_timeout(self):
    return self._bus_timeout


class CANDefine:
  def __init__(self, dbc_name):
    self.dbc_name = dbc_name
    dbc = dbc_lookup(dbc_name)
    dv = defaultdict(dict)
    for m in dbc.msgs.values():
      for sg, table in m.vals.items():
        # parser_pyx: values uppercased, spaces -> underscores
        t = {k: v.upper().replace(' ', '_') for k, v in table.items()}
        dv[m.name][sg] = t
        dv[m.address][sg] = t
    self.dv = dict(dv)


class CANPacker:
  def __init__(self, dbc_name):
    self.dbc = dbc_lookup(dbc_name)
    self._p = Packer(self.dbc)

  def make_can_msg(self, name_or_addr, bus, values):
    addr, dat = self._p.pack(name_or_addr, values)
    return addr, dat, bus


def install():
  import types
  m = types.ModuleType('opendbc.can.parser_pyx')
  m.CANParser = CANParser
  m.CANDefine = CANDefine
  sys.modules['opendbc.can.parser_pyx'] = m
  p = types.ModuleType('opendbc.can.packer_pyx')
  p.CANPacker = CANPacker
  sys.modules['opendbc.can.packer_pyx'] = p
