"""Pure-Python stand-ins for the Cython extensions of the flowpilot tree
(common.params_pyx, opendbc.can.parser_pyx, opendbc.can.packer_pyx).

They exist only so that selfdrive/car/tests can run on a Windows host that
has no C/C++ compiler. They are NOT used on the device. The CAN parser/packer
are backed by cantools, so every signal/message/frequency referenced by
carstate.py is checked against the generated DBC exactly like the real
CANParser constructor would (missing signal/message -> RuntimeError).
"""
import os
import sys
import types
import struct

import cantools

REPO = os.environ["FP_REPO"]
DBC_DIR = os.path.join(REPO, "opendbc")

_dbc_cache = {}


def load_dbc(name):
  if name not in _dbc_cache:
    path = os.path.join(DBC_DIR, name + ".dbc")
    if not os.path.exists(path) and name.endswith("_generated"):
      # the panda safety tests (newer opendbc naming) ask for *_generated; this older opendbc only has the plain file
      alt = os.path.join(DBC_DIR, name[:-len("_generated")] + ".dbc")
      if os.path.exists(alt):
        path = alt
    if not os.path.exists(path):
      raise RuntimeError(f"DBC not found: {path}")
    import re
    with open(path, encoding="utf-8", errors="replace") as f:
      txt = f.read()
    # opendbc's C++ parser ignores comments; some Honda CM_ lines are malformed for cantools
    txt = re.sub(r'^CM_ [^\n]*"[ \t]*;?[ \t]*$', "", txt, flags=re.M)  # single-line (with or without ';')
    txt = re.sub(r'^CM_\b.*?";[ \t]*$', "", txt, flags=re.S | re.M)   # multi-line
    # cantools' tokenizer rejects factors/offsets like "(.25,-500)"; opendbc's strtod accepts them
    txt = re.sub(r"([(,|\[])(-?)\.(\d)", r"\g<1>\g<2>0.\3", txt)
    # VAL_ lines missing the trailing ';' (toyota) and message names starting with a digit (mazda) are
    # accepted by opendbc's parser but not by cantools' grammar
    txt = re.sub(r'^(VAL_ .*")[ \t]*$', r"\1;", txt, flags=re.M)
    txt = re.sub(r"^(BO_ \d+ )(\d)", r"\1M_\2", txt, flags=re.M)
    txt = re.sub(r"^( SG_ )(\d)", r"\1S_\2", txt, flags=re.M)

    # opendbc stores 29-bit ids without the extended flag bit; cantools insists on it
    def _ext(m):
      i = int(m.group(1))
      if 0x7FF < i < 0x80000000:
        i |= 0x80000000
      return f"BO_ {i} "
    txt = re.sub(r"^BO_ (\d+) ", _ext, txt, flags=re.M)
    for _ in range(3):
      try:
        _dbc_cache[name] = cantools.database.load_string(txt, database_format="dbc", strict=False)
        break
      except cantools.database.errors.UnsupportedDatabaseFormatError as e:
        # VAL_ entries pointing at non-existent signals are ignored by opendbc's parser
        bad = re.findall(r"VAL_ (\d+) (\w+)", str(e))
        if not bad:
          raise
        for mid, sig in bad:
          txt = re.sub(rf"^VAL_ {mid} {sig} .*$", "", txt, flags=re.M)
    else:
      raise RuntimeError(f"could not load {name}")
  return _dbc_cache[name]


def fid(msg):
  return msg.frame_id & 0x1FFFFFFF


def by_id(db, addr):
  try:
    return db.get_message_by_frame_id(addr)
  except KeyError:
    return db.get_message_by_frame_id(addr | 0x80000000)


# ---------------------------------------------------------------- params
class ParamKeyType:
  PERSISTENT = 1
  CLEAR_ON_MANAGER_START = 2
  CLEAR_ON_PANDA_DISCONNECT = 4
  CLEAR_ON_IGNITION_ON = 8
  CLEAR_ON_IGNITION_OFF = 16
  DONT_LOG = 32
  ALL = 0xFFFFFFFF


class UnknownKeyName(Exception):
  pass


class Params:
  _store = {}

  def __init__(self, d=""):
    pass

  def clear_all(self, tx_type=ParamKeyType.ALL):
    Params._store.clear()

  def check_key(self, key):
    return key

  def get(self, key, block=False, encoding=None):
    v = Params._store.get(key)
    if v is not None and encoding is not None:
      return v.decode(encoding)
    return v

  def get_bool(self, key, block=False):
    return Params._store.get(key) == b"1"

  def put(self, key, dat):
    if isinstance(dat, str):
      dat = dat.encode()
    Params._store[key] = dat

  def put_bool(self, key, val):
    Params._store[key] = b"1" if val else b"0"

  def remove(self, key):
    Params._store.pop(key, None)

  def get_param_path(self, key=""):
    return key


def put_nonblocking(key, val, d=""):
  Params().put(key, val)


def put_bool_nonblocking(key, val, d=""):
  Params().put_bool(key, val)


params_mod = types.ModuleType("common.params_pyx")
params_mod.Params = Params
params_mod.ParamKeyType = ParamKeyType
params_mod.UnknownKeyName = UnknownKeyName
params_mod.put_nonblocking = put_nonblocking
params_mod.put_bool_nonblocking = put_bool_nonblocking


# ---------------------------------------------------------------- CANDefine
class CANDefine:
  def __init__(self, dbc_name):
    db = load_dbc(dbc_name)
    self.dv = {}
    for msg in db.messages:
      d = {}
      for sig in msg.signals:
        if sig.choices:
          d[sig.name] = {int(k): str(v) for k, v in sig.choices.items()}
      if d:
        self.dv[msg.name] = d
        self.dv[fid(msg)] = d


# ---------------------------------------------------------------- CANParser
class CANParser:
  def __init__(self, dbc_name, signals, checks=None, bus=0, enforce_checks=True):
    checks = checks or []
    self.dbc_name = dbc_name
    self.bus = bus
    self.db = load_dbc(dbc_name)
    self.vl = {}
    self.vl_all = {}
    self.ts_nanos = {}
    self.can_valid = False
    self.bus_timeout = False
    self._msgs = {}

    def resolve(m):
      try:
        return self.db.get_message_by_name(m) if isinstance(m, str) else by_id(self.db, m)
      except KeyError:
        raise RuntimeError(f"could not find message {m!r} in DBC {dbc_name}") from None

    checked = set()
    for m, freq in checks:
      msg = resolve(m)
      checked.add(fid(msg))
      self._msgs[fid(msg)] = msg

    for sig in signals:
      s, m = sig[0], sig[1]  # older (signal, message, default) 3-tuples still exist (VW PQ)
      msg = resolve(m)
      if msg.get_signal_by_name(s) is None if hasattr(msg, "get_signal_by_name") else s not in [x.name for x in msg.signals]:
        raise RuntimeError(f"could not find signal {s!r} in message {m!r} ({dbc_name})")
      self._msgs[fid(msg)] = msg
      if enforce_checks and fid(msg) not in checked:
        raise RuntimeError(f"Message {m!r} is used but has no check (enforce_checks)")

    for msg in self._msgs.values():
      d = {sig.name: 0.0 for sig in msg.signals}
      self.vl[msg.name] = d
      self.vl[fid(msg)] = d
      da = {sig.name: [] for sig in msg.signals}
      self.vl_all[msg.name] = da
      self.vl_all[fid(msg)] = da
      self.ts_nanos[msg.name] = {sig.name: 0 for sig in msg.signals}
      self.ts_nanos[fid(msg)] = self.ts_nanos[msg.name]

  def update_strings(self, strings, sendcan=False):
    updated = set()
    for s in strings:
      try:
        from cereal import log
        evt = log.Event.from_bytes(s)
        can = evt.sendcan if sendcan else evt.can
      except Exception:
        continue
      for c in can:
        if c.src != self.bus or c.address not in self._msgs:
          continue
        msg = self._msgs[c.address]
        dat = bytes(c.dat)
        try:
          dec = msg.decode(dat, decode_choices=False, scaling=True)
        except Exception:
          continue
        for k, v in dec.items():
          self.vl[msg.name][k] = float(v)
          self.vl_all[msg.name][k].append(float(v))
        updated.add(c.address)
    return updated


# ---------------------------------------------------------------- CANPacker
def _set_value(msg, sig, ival):
  """Port of opendbc/can/packer.cc set_value (sig: cantools signal)."""
  size = sig.length
  if size < 64:
    ival &= (1 << size) - 1
  # opendbc lsb: little endian -> start bit; big endian -> computed from DBC msb numbering
  if sig.byte_order == "little_endian":
    lsb = sig.start
  else:
    msb = sig.start
    # DBC big-endian start bit is the msb in "sawtooth" numbering; convert like opendbc dbc.cc
    b = msb // 8
    bit = msb % 8
    pos = b * 8 + (7 - bit)        # linear msb position
    pos_lsb = pos + size - 1       # linear lsb position
    lsb = (pos_lsb // 8) * 8 + (7 - pos_lsb % 8)
  i = lsb // 8
  bits = size
  while 0 <= i < len(msg) and bits > 0:
    shift = lsb % 8 if (lsb // 8) == i else 0
    sz = min(bits, 8 - shift)
    msg[i] &= ~(((1 << sz) - 1) << shift) & 0xFF
    msg[i] |= (ival & ((1 << sz) - 1)) << shift
    bits -= sz
    ival >>= sz
    i = i + 1 if sig.byte_order == "little_endian" else i - 1


def _honda_checksum(address, d):
  s = 0
  extended = address > 0x7FF
  a = address
  while a:
    s += a & 0xF
    a >>= 4
  for i, x in enumerate(d):
    if i == len(d) - 1:
      x >>= 4
    s += (x & 0xF) + (x >> 4)
  s = 8 - s
  if extended:
    s += 3
  return s & 0xF


def _toyota_checksum(address, d):
  s = len(d)
  a = address
  while a:
    s += a & 0xFF
    a >>= 8
  s += sum(d[:-1])
  return s & 0xFF


def _subaru_checksum(address, d):
  s = 0
  a = address
  while a:
    s += a & 0xFF
    a >>= 8
  s += sum(d[1:])
  return s & 0xFF


def _chrysler_checksum(address, d):
  checksum = 0xFF
  for j in range(len(d) - 1):
    shift = 0x80
    curr = d[j]
    for _ in range(8):
      bit_sum = curr & shift
      temp_chk = checksum & 0x80
      if bit_sum != 0:
        bit_sum = 0x1C
        if temp_chk != 0:
          bit_sum = 1
        checksum = (checksum << 1) & 0xFF
        temp_chk = checksum | 1
        bit_sum ^= temp_chk
      else:
        if temp_chk != 0:
          bit_sum = 0x1D
        checksum = (checksum << 1) & 0xFF
        bit_sum ^= checksum
      checksum = bit_sum & 0xFF
      shift >>= 1
  return ~checksum & 0xFF


def _xor_checksum(address, d, checksum_byte):
  c = 0
  for i, x in enumerate(d):
    if i != checksum_byte:
      c ^= x
  return c


def _pedal_checksum(address, d):
  crc = 0xFF
  poly = 0xD5
  for i in range(len(d) - 2, -1, -1):
    crc ^= d[i]
    for _ in range(8):
      crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
  return crc


def _crc8_lut(poly):
  lut = []
  for i in range(256):
    crc = i
    for _ in range(8):
      crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    lut.append(crc)
  return lut


def _crc16_lut(poly):
  lut = []
  for i in range(256):
    crc = i << 8
    for _ in range(8):
      crc = ((crc << 1) ^ poly) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    lut.append(crc)
  return lut


_CRC8_8H2F = _crc8_lut(0x2F)
_CRC16_XMODEM = _crc16_lut(0x1021)

_VW_MQB_MAGIC = {
  0x86: [0x86] * 16, 0x9F: [0xF5] * 16,
  0xAD: [0x3F, 0x69, 0x39, 0xDC, 0x94, 0xF9, 0x14, 0x64, 0xD8, 0x6A, 0x34, 0xCE, 0xA2, 0x55, 0xB5, 0x2C],
  0xFD: [0xB4, 0xEF, 0xF8, 0x49, 0x1E, 0xE5, 0xC2, 0xC0, 0x97, 0x19, 0x3C, 0xC9, 0xF1, 0x98, 0xD6, 0x61],
  0x106: [0x07] * 16, 0x117: [0x16] * 16,
  0x120: [0xC4, 0xE2, 0x4F, 0xE4, 0xF8, 0x2F, 0x56, 0x81, 0x9F, 0xE5, 0x83, 0x44, 0x05, 0x3F, 0x97, 0xDF],
  0x121: [0xE9, 0x65, 0xAE, 0x6B, 0x7B, 0x35, 0xE5, 0x5F, 0x4E, 0xC7, 0x86, 0xA2, 0xBB, 0xDD, 0xEB, 0xB4],
  0x122: [0x37, 0x7D, 0xF3, 0xA9, 0x18, 0x46, 0x6D, 0x4D, 0x3D, 0x71, 0x92, 0x9C, 0xE5, 0x32, 0x10, 0xB9],
  0x126: [0xDA] * 16,
  0x12B: [0x6A, 0x38, 0xB4, 0x27, 0x22, 0xEF, 0xE1, 0xBB, 0xF8, 0x80, 0x84, 0x49, 0xC7, 0x9E, 0x1E, 0x2B],
  0x12E: [0xF8, 0xE5, 0x97, 0xC9, 0xD6, 0x07, 0x47, 0x21, 0x66, 0xDD, 0xCF, 0x6F, 0xA1, 0x94, 0x74, 0x63],
  0x187: [0x7F, 0xED, 0x17, 0xC2, 0x7C, 0xEB, 0x44, 0x21, 0x01, 0xFA, 0xDB, 0x15, 0x4A, 0x6B, 0x23, 0x05],
  0x30C: [0x0F] * 16, 0x30F: [0x0C] * 16, 0x324: [0x27] * 16, 0x3C0: [0xC3] * 16,
  0x65D: [0xAC, 0xB3, 0xAB, 0xEB, 0x7A, 0xE1, 0x3B, 0xF7, 0x73, 0xBA, 0x7C, 0x9E, 0x06, 0x5F, 0x02, 0xD9],
}


def _vw_mqb_checksum(address, d):
  crc = 0xFF
  for x in d[1:]:
    crc ^= x
    crc = _CRC8_8H2F[crc]
  counter = d[1] & 0x0F
  crc ^= _VW_MQB_MAGIC.get(address, [0] * 16)[counter]
  crc = _CRC8_8H2F[crc]
  return crc ^ 0xFF


def _hkg_can_fd_checksum(address, d):
  crc = 0
  for x in list(d[2:]) + [address & 0xFF, (address >> 8) & 0xFF]:
    crc = ((crc << 8) ^ _CRC16_XMODEM[((crc >> 8) ^ x) & 0xFF]) & 0xFFFF
  crc ^= {8: 0x5F29, 16: 0x041D, 24: 0x819D, 32: 0x9F5B}.get(len(d), 0)
  return crc


def _checksum_fn(dbc_name):
  """Mirror of opendbc/can/dbc.cc get_checksum(): returns f(address, data, checksum_sig) or None."""
  if dbc_name.startswith(("honda_", "acura_")):
    return lambda a, d, s: _honda_checksum(a, d)
  if dbc_name.startswith(("toyota_", "lexus_")):
    return lambda a, d, s: _toyota_checksum(a, d)
  if dbc_name.startswith("hyundai_canfd"):
    return lambda a, d, s: _hkg_can_fd_checksum(a, d)
  if dbc_name.startswith("vw_mqb_2010"):
    return lambda a, d, s: _vw_mqb_checksum(a, d)
  if dbc_name.startswith("vw_golf_mk4"):
    return lambda a, d, s: _xor_checksum(a, d, s.start // 8)
  if dbc_name.startswith("subaru_global_"):
    return lambda a, d, s: _subaru_checksum(a, d)
  if dbc_name.startswith("chrysler_"):
    return lambda a, d, s: _chrysler_checksum(a, d)
  if dbc_name.startswith("comma_body"):
    return lambda a, d, s: _pedal_checksum(a, d)
  return None


class CANPacker:
  """Port of opendbc/can/packer.cc on top of cantools metadata (COUNTER auto-increment and
  Honda CHECKSUM included). RET3 selects the 3-tuple return of the newer opendbc used by panda tests."""
  RET3 = False

  def __init__(self, dbc_name):
    self.db = load_dbc(dbc_name)
    self.dbc_name = dbc_name
    self.counters = {}
    self.calc_checksum = _checksum_fn(dbc_name)

  def make_can_msg(self, name_or_addr, bus, values):
    try:
      msg = self.db.get_message_by_name(name_or_addr) if isinstance(name_or_addr, str) else by_id(self.db, name_or_addr)
    except KeyError:
      raise RuntimeError(f"could not find message {name_or_addr!r}") from None
    sigs = {s.name: s for s in msg.signals}
    addr = fid(msg)
    ret = bytearray(msg.length)
    counter_set = False
    for k, v in values.items():
      sig = sigs.get(k)
      if sig is None:
        continue  # C++ packer only warns
      ival = int(round((v - sig.offset) / sig.scale))
      if ival < 0:
        ival = (1 << sig.length) + ival
      _set_value(ret, sig, ival)
      counter_set = counter_set or (k == "COUNTER")
      if counter_set:
        self.counters[addr] = v
    if not counter_set and "COUNTER" in sigs:
      sig = sigs["COUNTER"]
      c = self.counters.get(addr, 0)
      _set_value(ret, sig, int(c))
      self.counters[addr] = (int(c) + 1) % (1 << sig.length)
    if self.calc_checksum is not None and "CHECKSUM" in sigs:
      _set_value(ret, sigs["CHECKSUM"], self.calc_checksum(addr, ret, sigs["CHECKSUM"]))
    if CANPacker.RET3:
      return (addr, bytes(ret), bus)
    return [addr, 0, bytes(ret), bus]


parser_mod = types.ModuleType("opendbc.can.parser_pyx")
parser_mod.CANParser = CANParser
parser_mod.CANDefine = CANDefine
packer_mod = types.ModuleType("opendbc.can.packer_pyx")
packer_mod.CANPacker = CANPacker


# ---------------------------------------------------------------- KF1D / clock
class KF1D:
  """Line-by-line Python version of common/kalman/simple_kalman_impl.pyx."""

  def __init__(self, x0, A, C, K):
    self.x0_0 = x0[0][0]
    self.x1_0 = x0[1][0]
    self.A0_0, self.A0_1, self.A1_0, self.A1_1 = A[0][0], A[0][1], A[1][0], A[1][1]
    self.C0_0, self.C0_1 = C[0], C[1]
    self.K0_0, self.K1_0 = K[0][0], K[1][0]
    self.A_K_0 = self.A0_0 - self.K0_0 * self.C0_0
    self.A_K_1 = self.A0_1 - self.K0_0 * self.C0_1
    self.A_K_2 = self.A1_0 - self.K1_0 * self.C0_0
    self.A_K_3 = self.A1_1 - self.K1_0 * self.C0_1

  def update(self, meas):
    x0_0 = self.A_K_0 * self.x0_0 + self.A_K_1 * self.x1_0 + self.K0_0 * meas
    x1_0 = self.A_K_2 * self.x0_0 + self.A_K_3 * self.x1_0 + self.K1_0 * meas
    self.x0_0, self.x1_0 = x0_0, x1_0
    return [self.x0_0, self.x1_0]

  @property
  def x(self):
    return [[self.x0_0], [self.x1_0]]

  @x.setter
  def x(self, x):
    self.x0_0 = x[0][0]
    self.x1_0 = x[1][0]


kalman_mod = types.ModuleType("common.kalman.simple_kalman_impl")
kalman_mod.KF1D = KF1D


# ---------------------------------------------------------------- messaging (no-op sockets)
class MessagingError(Exception):
  pass


class MultiplePublishersError(MessagingError):
  pass


class Context:
  def term(self):
    pass


class Poller:
  def __init__(self):
    self.socks = []

  def registerSocket(self, s):
    self.socks.append(s)

  def poll(self, timeout):
    return []


class SubSocket:
  def connect(self, context, endpoint, address="127.0.0.1", conflate=False):
    pass

  def setTimeout(self, t):
    pass

  def receive(self, non_blocking=False):
    return None


class PubSocket:
  def connect(self, context, endpoint):
    pass

  def send(self, data):
    pass

  def all_readers_updated(self):
    return True


msg_mod = types.ModuleType("cereal.messaging.messaging_pyx")
for _c in (MessagingError, MultiplePublishersError, Context, Poller, SubSocket, PubSocket):
  setattr(msg_mod, _c.__name__, _c)


# ---------------------------------------------------------------- transformations (import-only)
def _not_needed(*a, **k):
  raise NotImplementedError("common.transformations is not available in the Windows test shim")


xf_mod = types.ModuleType("common.transformations.transformations")
for _n in ("euler2quat_single", "quat2euler_single", "quat2rot_single", "rot2quat_single", "euler2rot_single",
           "rot2euler_single", "rot_matrix", "ecef_euler_from_ned_single", "ned_euler_from_ecef_single",
           "geodetic2ecef_single", "ecef2geodetic_single", "LocalCoord_single"):
  setattr(xf_mod, _n, _not_needed)


# ---------------------------------------------------------------- boardd_api_impl
def can_list_to_can_capnp(can_msgs, msgtype='can', valid=True):
  from cereal import log
  dat = log.Event.new_message()
  dat.valid = valid
  can = dat.init(msgtype, len(can_msgs))
  for i, m in enumerate(can_msgs):
    can[i].address = m[0]
    can[i].busTime = m[1]
    can[i].dat = bytes(m[2])
    can[i].src = m[3]
  return dat.to_bytes()


boardd_mod = types.ModuleType("selfdrive.boardd.boardd_api_impl")
boardd_mod.can_list_to_can_capnp = can_list_to_can_capnp

import time  # noqa: E402
clock_mod = types.ModuleType("common.clock")
clock_mod.monotonic_time = time.monotonic
clock_mod.sec_since_boot = time.monotonic


def install():
  # interfaces.get_interface_attr / test_fingerprints split os.walk paths on '/'
  _walk = os.walk

  def walk_fwd(top, *a, **k):
    for dirpath, dirnames, filenames in _walk(top, *a, **k):
      yield dirpath.replace("\\", "/"), dirnames, filenames
  os.walk = walk_fwd

  if "fcntl" not in sys.modules:
    fcntl_mod = types.ModuleType("fcntl")
    fcntl_mod.flock = _not_needed
    fcntl_mod.LOCK_EX = 2
    fcntl_mod.LOCK_UN = 8
    sys.modules["fcntl"] = fcntl_mod
  sys.modules["selfdrive.boardd.boardd_api_impl"] = boardd_mod
  sys.modules["common.transformations.transformations"] = xf_mod
  sys.modules["cereal.messaging.messaging_pyx"] = msg_mod
  sys.modules["common.kalman.simple_kalman_impl"] = kalman_mod
  sys.modules["common.clock"] = clock_mod
  sys.modules["common.params_pyx"] = params_mod
  sys.modules["opendbc.can.parser_pyx"] = parser_mod
  sys.modules["opendbc.can.packer_pyx"] = packer_mod
  # BASEDIR is hardcoded to the Android app path in common/path.py
  import common.path as cp
  cp.flowpilot_root = lambda: REPO
  cp.BASEDIR = REPO
