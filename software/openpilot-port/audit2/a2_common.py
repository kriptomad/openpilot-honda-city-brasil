"""Audit 2: shared helpers - rlog loading (cereal from openpilot v0.9.9 tree), minimal v0.9.9-faithful DBC parse.

The DBC layer re-implements opendbc/can/dbc.cc + parser.cc + packer.cc (v0.9.9) semantics in Python:
 - big-endian lsb/msb from start bit via be_bits table (dbc.cc)
 - get_raw_value / sign extension (parser.cc)
 - honda_checksum (common.cc) and ChecksumState{4,2,3,5} assignment (dbc.cc get_checksum)
 - set_value / pack (packer.cc) with C round() (half away from zero)
"""
import os
import re
import sys
import zstandard

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OP_TREE = os.path.join(BASE, 'openpilot_cityg7_v0.9.9')
RLOG = os.path.join(os.environ.get('TEMP', '.'), 'city_rlog', 'rlog.zst')


def load_log_schema():
  import capnp
  import warnings
  warnings.filterwarnings('ignore')
  capnp.remove_import_hook()
  # schema dir: cereal/*.capnp from the openpilot v0.9.9 tree + a real copy of opendbc/car/car.capnp
  # (cereal/car.capnp is a symlink into opendbc_repo that pycapnp on Windows cannot follow -> access violation)
  schema = os.path.join(os.environ.get('TEMP', '.'), 'audit2_schema')
  return capnp.load(os.path.join(schema, 'log.capnp'))


def read_events(path=RLOG):
  log = load_log_schema()
  with open(path, 'rb') as f:
    raw = zstandard.ZstdDecompressor().decompressobj().decompress(f.read())
  return list(log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30))


# ---------------------------------------------------------------- DBC (v0.9.9 C++ semantics)
BE_BITS = [j + i * 8 for i in range(64) for j in range(7, -1, -1)]

SG_RE = re.compile(r'^SG_ (\w+) : (\d+)\|(\d+)@(\d+)([\+|\-]) \(([0-9.+\-eE]+),([0-9.+\-eE]+)\) \[([0-9.+\-eE]+)\|([0-9.+\-eE]+)\] \"(.*)\" (.*)')
BO_RE = re.compile(r'^BO_ (\w+) (\w+) *: (\w+) (\w+)')
VAL_RE = re.compile(r'^VAL_ (\w+) (\w+) (.*);')


class Sig:
  __slots__ = ('name', 'start_bit', 'size', 'is_little_endian', 'is_signed', 'factor', 'offset', 'lsb', 'msb', 'is_checksum', 'is_counter')

  def __init__(self, name, start_bit, size, little, signed, factor, offset):
    self.name, self.start_bit, self.size = name, start_bit, size
    self.is_little_endian, self.is_signed = little, signed
    self.factor, self.offset = factor, offset
    if little:
      self.lsb = start_bit
      self.msb = start_bit + size - 1
    else:
      idx = BE_BITS.index(start_bit)
      self.lsb = BE_BITS[idx + size - 1]
      self.msb = start_bit
    self.is_checksum = name == 'CHECKSUM'
    self.is_counter = name == 'COUNTER'


class Msg:
  def __init__(self, name, address, size):
    self.name, self.address, self.size = name, address, size
    self.sigs = {}
    self.sig_list = []
    self.vals = {}  # sig name -> {int: str}


class DBC:
  def __init__(self, path, honda=True):
    self.msgs = {}
    self.by_name = {}
    cur = None
    for line in open(path, encoding='utf-8'):
      line = line.strip()
      m = BO_RE.match(line)
      if m:
        addr = int(m.group(1))
        cur = Msg(m.group(2), addr, int(m.group(3)))
        self.msgs[addr] = cur
        self.by_name[cur.name] = cur
        continue
      m = SG_RE.match(line)
      if m and cur is not None:
        s = Sig(m.group(1), int(m.group(2)), int(m.group(3)), m.group(4) == '1', m.group(5) == '-', float(m.group(6)), float(m.group(7)))
        if honda:
          if s.is_checksum:
            assert s.size == 4 and s.start_bit % 8 == 3, (cur.name, s.name, s.start_bit, s.size)
          if s.is_counter:
            assert s.size == 2 and s.start_bit % 8 == 5, (cur.name, s.name, s.start_bit, s.size)
        cur.sigs[s.name] = s
        cur.sig_list.append(s)
        continue
      m = VAL_RE.match(line)
      if m:
        addr = int(m.group(1))
        if addr in self.msgs:
          toks = re.findall(r'(\d+) "([^"]*)"', m.group(3))
          self.msgs[addr].vals[m.group(2)] = {int(k): v for k, v in toks}


def honda_checksum(address, d):
  s = 0
  extended = address > 0x7FF
  a = address
  while a:
    s += a & 0xF
    a >>= 4
  for i in range(len(d)):
    x = d[i]
    if i == len(d) - 1:
      x >>= 4
    s += (x & 0xF) + (x >> 4)
  s = 8 - s
  if extended:
    s += 3
  return s & 0xF


def get_raw_value(msg, sig):
  ret = 0
  i = sig.msb // 8
  bits = sig.size
  while 0 <= i < len(msg) and bits > 0:
    lsb = sig.lsb if (sig.lsb // 8) == i else i * 8
    msb = sig.msb if (sig.msb // 8) == i else (i + 1) * 8 - 1
    size = msb - lsb + 1
    d = (msg[i] >> (lsb - i * 8)) & ((1 << size) - 1)
    ret |= d << (bits - size)
    bits -= size
    i = i - 1 if sig.is_little_endian else i + 1
  return ret


def decode(m: Msg, dat: bytes):
  """returns (values dict, checksum_ok, raw counter or None)"""
  out = {}
  cs_ok = True
  counter = None
  for sig in m.sig_list:
    tmp = get_raw_value(dat, sig)
    if sig.is_signed and (tmp >> (sig.size - 1)) & 1:
      tmp -= 1 << sig.size
    if sig.is_checksum and honda_checksum(m.address, dat) != tmp:
      cs_ok = False
    if sig.is_counter:
      counter = tmp
    out[sig.name] = tmp * sig.factor + sig.offset
  return out, cs_ok, counter


def c_round(x):
  # C round(): half away from zero
  import math
  return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)


def set_value(msg: bytearray, sig: Sig, ival: int):
  i = sig.lsb // 8
  bits = sig.size
  if sig.size < 64:
    ival &= (1 << sig.size) - 1
  while 0 <= i < len(msg) and bits > 0:
    shift = sig.lsb % 8 if (sig.lsb // 8) == i else 0
    size = min(bits, 8 - shift)
    msg[i] &= ~(((1 << size) - 1) << shift) & 0xFF
    msg[i] |= (ival & ((1 << size) - 1)) << shift
    bits -= size
    ival >>= size
    i = i + 1 if sig.is_little_endian else i - 1


class Packer:
  """packer.cc semantics. counters dict persists per address."""

  def __init__(self, dbc: DBC):
    self.dbc = dbc
    self.counters = {}

  def pack(self, name_or_addr, values):
    m = self.dbc.by_name[name_or_addr] if isinstance(name_or_addr, str) else self.dbc.msgs[name_or_addr]
    ret = bytearray(m.size)
    counter_set = False
    for n, v in values.items():
      sig = m.sigs.get(n)
      if sig is None:
        raise KeyError(f"undefined signal {n} in {m.name}")
      ival = c_round((v - sig.offset) / sig.factor)
      if ival < 0:
        ival = (1 << sig.size) + ival
      set_value(ret, sig, ival)
      if sig.is_counter:
        self.counters[m.address] = v
        counter_set = True
    cnt = next((s for s in m.sig_list if s.is_counter), None)
    if cnt is not None and not counter_set:
      c = self.counters.get(m.address, 0)
      set_value(ret, cnt, int(c))
      self.counters[m.address] = (c + 1) % (1 << cnt.size)
    cs = next((s for s in m.sig_list if s.is_checksum), None)
    if cs is not None:
      set_value(ret, cs, honda_checksum(m.address, ret))
    return m.address, bytes(ret)
