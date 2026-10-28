"""Run flowpilot's selfdrive/car tests on a Windows host without compiling
the Cython extensions (see fp_shims.py). Must be executed with the
10_FLOWPILOT\\.venv_fp interpreter.

  python run_car_tests.py <repo_root> [unittest args...]
"""
import os
import sys

if os.environ.get("PYTHONUTF8") != "1":
  # docs/CARS.md is UTF-8; the tests open it with the locale default encoding
  import subprocess
  env = dict(os.environ, PYTHONUTF8="1")
  sys.exit(subprocess.call([sys.executable] + sys.argv, env=env))

REPO = os.path.abspath(sys.argv[1])
os.environ["FP_REPO"] = REPO
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)  # cereal/__init__.py loads "cereal/*.capnp" relative to cwd

import fp_shims  # noqa: E402
fp_shims.install()

import unittest  # noqa: E402

if __name__ == "__main__":
  argv = [sys.argv[0]] + sys.argv[2:]
  if len(argv) == 1:
    argv += ["discover", "-s", "selfdrive/car/tests", "-t", REPO, "-p", "test_*.py", "-v"]
  unittest.main(module=None, argv=argv)
