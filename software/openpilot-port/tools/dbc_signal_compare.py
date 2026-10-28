import zstandard, capnp, collections, cantools, warnings
warnings.filterwarnings("ignore")
capnp.remove_import_hook()
log = capnp.load(r"C:\Users\costabr\AppData\Local\Temp\city_route\schema\log.capnp")
raw = zstandard.ZstdDecompressor().stream_reader(open(r"C:\Users\costabr\AppData\Local\Temp\city_route\rlog0.zst","rb")).read()
def ld(p):
    import re as _re
    lines=open(p,encoding="utf-8").read().splitlines(); out=[]; skip=False
    for l in lines:
        if l.startswith("BO_ "):
            fid=int(l.split()[1]); skip = fid>=2048 and fid<0x80000000 and fid not in (0x33da,0x33db)
            if fid in (0x33da,0x33db): skip=True
        elif not l.startswith(" SG_"): skip=False
        if skip or l.startswith(("CM_","BA_","VAL_","SIG_")): continue
        out.append(l)
    txt="\n".join(out)
    return cantools.database.load_string(txt, "dbc", strict=False)
old = ld(r"C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\09_FIRMWARECITYG7_BLACKPANDA\opendbc_firmwarecityg7\opendbc\dbc\honda_civic_ex_2022_can_generated.dbc")
new = ld(r"C:\Users\costabr\AppData\Local\Temp\city_route\head_bosch_radarless.dbc")
frames = collections.defaultdict(list)
for m in log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30):
    if m.which()=='can':
        for c in m.can:
            if c.src in (0,2): frames[(c.src, c.address)].append(bytes(c.dat))
def msgmap(db): return {m.frame_id: m for m in db.messages}
om, nm = msgmap(old), msgmap(new)
report = []
for (src, addr), datas in sorted(frames.items()):
    o, n = om.get(addr), nm.get(addr)
    if o is None and n is None: continue
    if o is None or n is None:
        report.append(f"bus{src} 0x{addr:03X}: only in {'v0.9.9' if o else 'HEAD'} ({(o or n).name})"); continue
    osig = {s.name:s for s in o.signals}; nsig = {s.name:s for s in n.signals}
    # structural compare by (start,length,byte_order,scale,offset,signed)
    def key(s): return (s.start, s.length, s.byte_order, s.scale, s.offset, s.is_signed)
    nk = {key(s): s.name for s in n.signals}; ok = {key(s): s.name for s in o.signals}
    renamed = [(ok[k], nk[k]) for k in ok if k in nk and ok[k]!=nk[k]]
    only_old = [ok[k] for k in ok if k not in nk]
    only_new = [nk[k] for k in nk if k not in ok]
    # value-level compare for same-name signals with different layout
    diffs = []
    common = set(osig)&set(nsig)
    for name in sorted(common):
        if key(osig[name]) == key(nsig[name]): continue
        cnt=0; tot=0; ex=None
        for d in datas[:2000]:
            try:
                ov = o.decode(d, decode_choices=False, allow_truncated=True).get(name)
                nv = n.decode(d, decode_choices=False, allow_truncated=True).get(name)
            except Exception as e: continue
            tot+=1
            if ov != nv: cnt+=1; ex = ex or (ov,nv)
        diffs.append(f"{name}: layout differs, {cnt}/{tot} values differ e.g. {ex}")
    line = f"bus{src} 0x{addr:03X} {o.name}->{n.name} n={len(datas)}"
    if renamed or only_old or only_new or diffs:
        report.append(line)
        if renamed: report.append("   renamed(same layout): " + ", ".join(f"{a}->{b}" for a,b in renamed))
        if only_old: report.append("   only v0.9.9: " + ", ".join(only_old))
        if only_new: report.append("   only HEAD: " + ", ".join(only_new))
        for d in diffs: report.append("   SEMANTIC: "+d)
print("\n".join(report))

