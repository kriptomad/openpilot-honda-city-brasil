import re
import ast
import os
import sys

scan = os.path.join(os.environ['TEMP'], 'city_rlog', 'scan1.txt')
txt = open(scan).read()
route = {}
for m in re.finditer(r"^0:0x([0-9A-F]+) \{'count': (\d+), 'hz': ([\d.]+), 'dlc': \[(\d+)\]\}", txt, re.M):
    a = int(m.group(1), 16)
    if a < 0x800:
        route[a] = int(m.group(4))
src = open(os.path.join(sys.argv[1], 'selfdrive/car/honda/values.py')).read()
m = re.search(r'FINGERPRINTS = \{\s*CAR.CITY_7G: \[(\{.*?\})\]', src, re.S)
fp = ast.literal_eval(m.group(1))
print('route msgs', len(route), 'fp msgs', len(fp))
print('missing in fp:', {hex(k): v for k, v in route.items() if k not in fp})
print('dlc mismatch:', {hex(k): (v, fp.get(k)) for k, v in route.items() if k in fp and fp[k] != v})
print('extra in fp:', {hex(k): v for k, v in fp.items() if k not in route})
