import subprocess, sys, re
def sh(*a): return subprocess.run(['git', *a], capture_output=True, text=True).stdout
commits = sys.argv[1:]
total_bad = 0
for c in commits:
    diff = sh('show', '-U0', '--format=', c)
    cur = None; adds = {}; dels = {}
    for ln in diff.splitlines():
        if ln.startswith('+++ b/'): cur = ln[6:]; adds.setdefault(cur, []); dels.setdefault(cur, []); continue
        if ln.startswith('--- ') or ln.startswith('@@') or ln.startswith('diff ') or ln.startswith('index '): continue
        if cur is None: continue
        if ln.startswith('+'): adds[cur].append(ln[1:])
        elif ln.startswith('-'): dels[cur].append(ln[1:])
    print(f'=== {c} {sh("log","-1","--format=%s",c).strip()}')
    for f in adds:
        head = sh('show', f'HEAD:{f}')
        hl = [l.rstrip() for l in head.splitlines()]
        miss = [a for a in adds[f] if a.strip() and a.rstrip() not in hl]
        # deleted lines still present (only if not also re-added)
        still = [d for d in dels[f] if d.strip() and d.rstrip() in hl and d.rstrip() not in [a.rstrip() for a in adds[f]]]
        status = 'OK' if not miss and not still else 'DIFF'
        print(f'  [{status}] {f}: +{len(adds[f])} -{len(dels[f])}  missing_added={len(miss)} leftover_removed={len(still)}')
        for m in miss: print(f'      MISSING: {m}')
        for s in still: print(f'      LEFTOVER: {s}')
        total_bad += len(miss) + len(still)
print('TOTAL DISCREPANCIES:', total_bad)
