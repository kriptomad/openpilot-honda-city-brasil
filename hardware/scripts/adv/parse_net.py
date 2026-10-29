"""Parse KiCad s-expression netlist -> JSON {nets: {name: [(ref,pin,pinfunction)]}, comps: {ref: {value, footprint, fields}}}."""
import json, sys, re
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
out = Path(sys.argv[2])

def tokenize(s):
    tok = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+')
    for m in tok.finditer(s):
        t = m.group(0)
        if t.startswith('"'):
            yield t[1:-1].replace('\\"', '"')
        else:
            yield t

def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            l = stack.pop()
            stack[-1].append(l)
        else:
            stack[-1].append(t)
    return stack[0][0]

tree = parse(tokenize(src))

def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def first(node, key, default=None):
    f = find(node, key)
    return f[0][1] if f and len(f[0]) > 1 else default

comps = {}
for c in find(find(tree, 'components')[0], 'comp'):
    ref = first(c, 'ref')
    d = {'value': first(c, 'value'), 'footprint': first(c, 'footprint'), 'fields': {}}
    for fl in find(c, 'fields'):
        for f in find(fl, 'field'):
            name = first(f, 'name')
            d['fields'][name] = f[2] if len(f) > 2 and isinstance(f[2], str) else ''
    for p in find(c, 'property'):
        name = first(p, 'name'); val = first(p, 'value')
        d['fields'].setdefault(name, val)
    comps[ref] = d

nets = {}
for n in find(find(tree, 'nets')[0], 'net'):
    name = first(n, 'name')
    members = []
    for nd in find(n, 'node'):
        members.append((first(nd, 'ref'), first(nd, 'pin'), first(nd, 'pinfunction', ''), first(nd, 'pintype', '')))
    nets[name] = members

out.write_text(json.dumps({'comps': comps, 'nets': nets}, indent=1), encoding='utf-8')
print(len(comps), 'components', len(nets), 'nets')
