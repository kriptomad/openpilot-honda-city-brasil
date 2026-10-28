import re, zstandard, capnp, collections
capnp.remove_import_hook()
log = capnp.load(r"C:\Users\costabr\AppData\Local\Temp\city_route\schema\log.capnp")
raw = zstandard.ZstdDecompressor().stream_reader(open(r"C:\Users\costabr\AppData\Local\Temp\city_route\rlog0.zst","rb")).read()
addrs = collections.Counter(); dlc={}
t0=None; t1=None
for m in log.Event.read_multiple_bytes(raw, traversal_limit_in_words=2**30):
    if m.which()=='can':
        t0 = t0 or m.logMonoTime; t1=m.logMonoTime
        for c in m.can:
            addrs[(c.src, c.address)]+=1; dlc[(c.src,c.address)]=len(c.dat)
dur=(t1-t0)/1e9
dbc=open(r"C:\Users\costabr\Downloads\openpilot\HybridPanda_v2_20261022_1616\09_FIRMWARECITYG7_BLACKPANDA\opendbc_firmwarecityg7\opendbc\dbc\honda_civic_ex_2022_can_generated.dbc").read()
msgs={n:(int(a),int(l)) for a,n,l in re.findall(r"^BO_ (\d+) (\w+): (\d+)", dbc, re.M)}
pt=["ENGINE_DATA","WHEEL_SPEEDS","STEERING_SENSORS","SEATBELT_STATUS","CRUISE","POWERTRAIN_DATA","CAR_SPEED","VSA_STATUS","STEER_STATUS","STEER_MOTOR_TORQUE","SCM_FEEDBACK","SCM_BUTTONS","GEARBOX","EPB_STATUS","CRUISE_FAULT_STATUS"]
cam=["STEERING_CONTROL","ACC_HUD","LKAS_HUD","BSM_STATUS_LEFT","BSM_STATUS_RIGHT","ACC_CONTROL","ACC_CONTROL_ON","LKAS_HUD_A","LKAS_HUD_B","STANDSTILL","CRUISE_PARAMS","BRAKE_COMMAND"]
print("segment dur %.1fs"%dur)
for bus,names in ((0,pt),(2,cam)):
    print("--- bus",bus)
    for n in names:
        a,l=msgs.get(n,(0,None))
        c=addrs.get((bus,a),0)
        print(f"{n:22s} 0x{a:03X} dlc_dbc={l} dlc_bus={dlc.get((bus,a))} n={c} freq={c/dur:.1f}Hz")
print("bus0 addrs:", " ".join(hex(a) for s,a in sorted(addrs) if s==0))
print("bus2 addrs:", " ".join(hex(a) for s,a in sorted(addrs) if s==2))
print("0x33DA anywhere:", any(a==0x33DA for s,a in addrs), " 0x12f8bfa7:", any(a==0x12f8bfa7 for s,a in addrs))

