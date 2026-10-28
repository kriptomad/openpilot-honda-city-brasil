"""Audit 2: line-ending / trailing newline check on every file touched by the port commits (opendbc + openpilot)."""
import os
import subprocess
import sys

# software/openpilot-port (this file lives in audit2/)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chk(repo, base, head):
  files = subprocess.check_output(['git', '-C', repo, 'diff', '--name-only', base, head]).decode().split()
  for f in files:
    try:
      b = subprocess.check_output(['git', '-C', repo, 'cat-file', '-p', f'{head}:{f}'])
    except subprocess.CalledProcessError:
      print(f"  {f}: (deleted)")
      continue
    try:
      b0 = subprocess.check_output(['git', '-C', repo, 'cat-file', '-p', f'{base}:{f}'])
    except subprocess.CalledProcessError:
      b0 = b''
    crlf, lf = b.count(b'\r\n'), b.count(b'\n')
    crlf0, lf0 = b0.count(b'\r\n'), b0.count(b'\n')
    flag = ' <-- CRLF INTRODUCED' if crlf and not crlf0 else ''
    print(f"  {f}: HEAD CRLF={crlf} LF={lf} | base CRLF={crlf0} LF={lf0} | ends-with-newline={b.endswith(b'\n')}{flag}")


print('--- opendbc e370a036..HEAD')
chk(os.path.join(BASE, "..", "opendbc-v0.9.9-city-g7"), 'e370a036', 'HEAD')
print('--- openpilot 8aadf02b..HEAD')
chk(os.path.join(BASE, "..", "openpilot-v0.9.9-city-g7"), '8aadf02b', 'HEAD')
