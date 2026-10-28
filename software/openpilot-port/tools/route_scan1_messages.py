import sys, zstandard, capnp, collections
capnp.remove_import_hook()
log = capnp.load(r"C:\Users\costabr\AppData\Local\Temp\city_route\schema\log.capnp")
raw = zstandard.ZstdDecompressor().stream_reader(open(r"C:\Users\costabr\AppData\Local\Temp\city_route\rlog0.zst","rb")).read()
addrs = collections.Counter()
samples = {}
n=0
cp=None
for m in log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30):
    w = m.which()
    if w == 'can':
        for c in m.can:
            key=(c.src, c.address)
            addrs[key]+=1
            if c.address in (0x191,0x1A3) and len(samples.get(key,[]))<3:
                samples.setdefault(key,[]).append(bytes(c.dat).hex())
    elif w == 'carParams' and cp is None:
        cp = (m.carParams.carFingerprint, str(m.carParams.transmissionType), m.carParams.carFw and len(m.carParams.carFw))
    n+=1
print("events", n, "carParams", cp)
for src in sorted({k[0] for k in addrs}):
    print("bus", src, "n_addr", len([k for k in addrs if k[0]==src]))
for k in sorted(addrs):
    if k[1] in (0x191,0x1A3,0x1BE,0x1C2,0x1A6,0x17C,0x18F,0x1D0,0x1E7): print(hex(k[1]), "bus", k[0], addrs[k], samples.get(k))
