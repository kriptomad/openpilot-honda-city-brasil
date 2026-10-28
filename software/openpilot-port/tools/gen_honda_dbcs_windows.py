import os, re, sys
sys.path.insert(0, os.getcwd())
from opendbc.dbc.generator import generator as g
src = os.path.join(os.getcwd(), 'opendbc', 'dbc', 'generator', 'honda')
out = os.path.join(os.environ['TEMP'], 'gen_honda'); os.makedirs(out, exist_ok=True)
for f in sorted(os.listdir(src)):
    if f.startswith('_') or not f.endswith('.dbc'): continue
    g.create_dbc(src, f, out)
for f in sorted(os.listdir(out)):
    t = open(os.path.join(out, f)).read()
    n = len(re.findall(r'^BO_ 450 EPB_STATUS', t, re.M))
    print(f'{n} {f}')
