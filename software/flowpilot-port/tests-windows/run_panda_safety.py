"""Run flowpilot/panda/tests/safety on Windows.

usage: python run_panda_safety.py <flowpilot repo> [pytest args...]

Installs the pure-Python shims (opendbc CANPacker via cantools, fcntl, ...) and then runs pytest on
panda/tests/safety. Requires panda/tests/libpanda/libpanda.so built with a host GCC (mingw-w64 on Windows).
"""
import os
import sys

repo = os.path.abspath(sys.argv[1])
args = sys.argv[2:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo)
os.chdir(repo)
os.environ.setdefault("HW_TYPE", "6")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ["FP_REPO"] = repo

import fp_shims  # noqa: E402
fp_shims.install()
fp_shims.CANPacker.RET3 = True  # panda tests expect the newer 3-tuple make_can_msg

import pytest  # noqa: E402

if not args:
  args = [os.path.join("panda", "tests", "safety")]
sys.exit(pytest.main(["-p", "no:cacheprovider", "-p", "no:xdist", "-o", "addopts=", "-q"] + args))
