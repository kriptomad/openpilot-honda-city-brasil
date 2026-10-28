"""Audit 2: build proposed_patches/0002-opendbc-pyproject-restore-lf.patch (CRLF -> LF on pyproject.toml, content unchanged)
and proposed_patches/0003-openpilot-torqued-allow-honda.patch (optional parity: upstream 839a77334)."""
import os
import subprocess
import tempfile

BASE = r"C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\09_FIRMWARECITYG7_BLACKPANDA"
ODBC = os.path.join(BASE, "opendbc_firmwarecityg7")
OP = os.path.join(BASE, "openpilot_cityg7_v0.9.9")
PATCH_DIR = os.path.join(BASE, "audit2", "proposed_patches")


def no_index_diff(tmp, rel, old, new):
  for d, data in (("a", old), ("b", new)):
    p = os.path.join(tmp, d, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
      f.write(data)
  r = subprocess.run(["git", "-c", "core.quotepath=off", "-c", "core.autocrlf=false", "diff", "--no-index", "--no-prefix", "a", "b"], cwd=tmp, capture_output=True, text=True)
  out = []
  for l in r.stdout.split("\n"):
    if l.startswith(("diff --git", "--- ", "+++ ")):
      l = l.replace("\\", "/").replace('"', "")
    out.append(l)
  return "\n".join(out)


def main():
  os.makedirs(PATCH_DIR, exist_ok=True)
  tmp = tempfile.mkdtemp(prefix="audit2_p", dir=tempfile.gettempdir())

  # 0002: pyproject.toml line endings
  head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ODBC).decode().strip()
  cur = subprocess.check_output(["git", "cat-file", "-p", "HEAD:pyproject.toml"], cwd=ODBC)
  new = cur.replace(b"\r\n", b"\n")
  assert cur.count(b"\r\n") == 133 and new.count(b"\r") == 0
  diff = no_index_diff(os.path.join(tmp, "p2"), "pyproject.toml", cur, new)
  hdr = f"""From: audit2 <audit2@local>
Subject: [PATCH] pyproject.toml: restore LF line endings (content unchanged)

Base: opendbc firmwarecityg7-v0.9.9 @ {head}
Commit 5f439d78 ("ci: pin ruff to 0.11.13") rewrote all 133 lines of pyproject.toml with CRLF
(git diff --stat e370a036 HEAD shows 133/133; `git diff --ignore-all-space` shows the single intended
ruff pin). Cosmetic: tomllib/uv/pip parse CRLF fine, but it inflates every future diff against upstream.
Apply with `git apply --whitespace=nowarn` (the hunk itself removes the CRs).
---
"""
  with open(os.path.join(PATCH_DIR, "0002-opendbc-pyproject-restore-lf.patch"), "w", newline="\n") as f:
    f.write(hdr + diff)

  # 0003: torqued ALLOWED_CARS += honda (upstream openpilot 839a77334, 2025-08-06)
  head_op = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=OP).decode().strip()
  rel = "selfdrive/locationd/torqued.py"
  cur = subprocess.check_output(["git", "cat-file", "-p", f"HEAD:{rel}"], cwd=OP)
  old_line = b"ALLOWED_CARS = ['toyota', 'hyundai', 'rivian']\n"
  assert cur.count(old_line) == 1
  new = cur.replace(old_line, b"ALLOWED_CARS = ['toyota', 'hyundai', 'rivian', 'honda']\n")
  diff = no_index_diff(os.path.join(tmp, "p3"), rel, cur, new)
  hdr = f"""From: audit2 <audit2@local>
Subject: [PATCH] torqued: enable lateral accel factor learning for Honda (backport of upstream 839a77334)

Base: openpilot v0.9.9-cityg7-blackpanda @ {head_op}
Upstream openpilot 839a77334 (2025-08-06, "enable lateral accel factor learning for Honda", #35936) was
already in 09aa21390 when the City was merged, so on upstream the City's latAccelFactor/friction are
learned live by torqued (`CP.lateralTuning.which() == 'torque'` and brand honda) and the values from
override.toml ([1.2, 1.2, 0.23]) are only the starting point. The first audit left this out on purpose
(process-replay refs for torqued); it is a conscious divergence, not a correctness bug. Apply only if
full parity with upstream is wanted; then regenerate the torqued process-replay refs for the Honda
segments.
---
"""
  with open(os.path.join(PATCH_DIR, "0003-openpilot-torqued-allow-honda.patch"), "w", newline="\n") as f:
    f.write(hdr + diff)

  import shutil
  shutil.rmtree(tmp, ignore_errors=True)
  for p in ("0002-opendbc-pyproject-restore-lf.patch", "0003-openpilot-torqued-allow-honda.patch"):
    print("wrote", os.path.join(PATCH_DIR, p))


if __name__ == "__main__":
  main()
