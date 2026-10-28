"""Generate one Honda DBC from a given opendbc tree on Windows (generator.py's __main__ does not run here).

usage: python gen_dbc_from_tree.py <opendbc_tree> <dbc_name_without_ext> <out_dir>
"""
import os
import sys

tree, name, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, tree)
from opendbc.dbc.generator import generator as g  # noqa: E402

src = os.path.join(tree, 'opendbc', 'dbc', 'generator', 'honda')
os.makedirs(out_dir, exist_ok=True)
g.create_dbc(src, name + '.dbc', out_dir)
print('wrote', os.path.join(out_dir, name + '_generated.dbc'))
