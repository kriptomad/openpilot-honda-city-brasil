"""Closing check (audit2 sec. 11): evaluate CP.lateralTuning.which() on the v0.9.9 opendbc tree
for the Honda platforms used by openpilot process-replay (HONDA_CIVIC, HONDA_ACCORD) and the City,
and derive what torqued.py (8be62bc95) would do with use_params.

Usage: a2_closing_lattune.py <v0.9.9 opendbc tree root> <generated dbc dir>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
root, dbc_dir = sys.argv[1:3]
os.environ['A2_DBC_DIR'] = dbc_dir
sys.path.insert(0, HERE)
sys.path.insert(0, root)
import a2_v099_shim  # noqa: E402
a2_v099_shim.install()

from opendbc.car.honda.interface import CarInterface  # noqa: E402
from opendbc.car.honda.values import CAR  # noqa: E402

ALLOWED_CARS = ['toyota', 'hyundai', 'rivian', 'honda']  # torqued.py @ 8be62bc95

# fingerprint: City needs 0x191 for cvt; Accord/Civic plain Bosch/Nidec defaults
fps = {
  CAR.HONDA_CITY_7G: {0: {0x191: 8, 0x1BE: 8}, 1: {}, 2: {}, 3: {}},
  CAR.HONDA_ACCORD: {0: {}, 1: {}, 2: {}, 3: {}},
  CAR.HONDA_CIVIC: {0: {}, 1: {}, 2: {}, 3: {}},
}
for cand, fp in fps.items():
  CP = CarInterface.get_params(cand, fp, [], alpha_long=False, is_release=False, docs=False)
  which = CP.lateralTuning.which()
  use_params = (CP.brand in ALLOWED_CARS) and (which == 'torque')
  extra = ''
  if which == 'torque':
    t = CP.lateralTuning.torque
    extra = f" kp={t.kp} ki={t.ki} friction={t.friction} latAccelFactor={t.latAccelFactor} useSteeringAngle={t.useSteeringAngle}"
  print(f"{str(cand):22s} brand={CP.brand:6s} lateralTuning.which()={which:7s} torqued.use_params={use_params}{extra}")
