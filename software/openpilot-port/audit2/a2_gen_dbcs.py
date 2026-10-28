"""Audit 2: generate Honda DBCs from several opendbc trees (Windows-safe, no subprocess).

usage: python a2_gen_dbcs.py <out_root> <label>=<tree> [<label>=<tree> ...]
Generates every honda/*.dbc (non-underscore) into <out_root>/<label>/.
"""
import importlib
import os
import sys

out_root = sys.argv[1]
for spec in sys.argv[2:]:
  label, tree = spec.split('=', 1)
  tree = os.path.abspath(tree)
  # fresh import per tree
  for m in [k for k in sys.modules if k.startswith('opendbc')]:
    del sys.modules[m]
  sys.path.insert(0, tree)
  g = importlib.import_module('opendbc.dbc.generator.generator')
  src = os.path.join(tree, 'opendbc', 'dbc', 'generator', 'honda')
  out_dir = os.path.join(out_root, label)
  os.makedirs(out_dir, exist_ok=True)
  n = 0
  for f in sorted(os.listdir(src)):
    if f.endswith('.dbc') and not f.startswith('_'):
      g.create_dbc(src, f, out_dir)
      n += 1
  sys.path.remove(tree)
  print(label, tree, n, 'dbcs ->', out_dir)
