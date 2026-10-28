import zstandard, capnp, collections
capnp.remove_import_hook()
log = capnp.load(r"C:\Users\costabr\AppData\Local\Temp\city_route\schema\log.capnp")
raw = zstandard.ZstdDecompressor().stream_reader(open(r"C:\Users\costabr\AppData\Local\Temp\city_route\rlog0.zst","rb")).read()
vals = collections.Counter(); gears=collections.Counter(); fw=None
for m in log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30):
    w=m.which()
    if w=='can':
        for c in m.can:
            if c.src==0 and c.address==0x191:
                d=bytes(c.dat); vals[(d[0]&0x3f, d[5]&0x1f, d[4])]+=1
    elif w=='carState': gears[str(m.carState.gearShifter)]+=1
    elif w=='carParams' and fw is None:
        fw=[(str(f.ecu), f.address, f.subAddress, bytes(f.fwVersion)) for f in m.carParams.carFw]
print("GEARBOX byte0&0x3f (v0.9.9 one-hot), byte5&0x1f (HEAD GEAR_SHIFTER), byte4 (v0.9.9 GEAR):", dict(vals))
print("carState.gearShifter:", dict(gears))
print("carFw:", fw)
