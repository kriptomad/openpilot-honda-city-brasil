"""step4_build_schematic.py - STEP 4: rebuild 04_PROJECT/HybridPanda/HybridPanda.kicad_sch around the STM32H725ZGT6.

What it does (deterministic, re-runnable from the baseline copy made by step4_copy_and_roundtrip.py):
  1. deletes the F413 block (U7 + HSE/BOOT/VCAP/LED resistors/labels), the 5V-sense divider and the GPS block
  2. renames CANx_* labels to the firmware bus naming (BUS0/BUS1N/BUS1O/BUS2, EN->STB)
  3. enlarges the sheet to A1 and places the H725 (unit 1) with stubs, global labels, power rails and no-connects
  4. adds support blocks: HSE 25 MHz, BOOT0, NRST, SWD header, VCAP, SMPS inductor, VDDA filter, LED resistors,
     SBU ADC conditioning (series R + BAT54S clamp), HW_ID straps, 5VOUT_S divider, STB pull-ups,
     decoupling bank, PWR_FLAG cluster
  5. renames project instances BlackPanda -> HybridPanda and writes the file (backup first via hp_common)
Pin facts come from 05_SCRIPTS/firmware_pins.json (profile red_h7) and 03_RESEARCH/STEP3_* table (a).
"""
from __future__ import annotations

import json
import re
import sys
import uuid
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hp_common import OUTPUT_ROOT, KICAD_BIN, backup_before_write, assert_inside_output, JsonLog  # noqa: E402
from sch_geom import transform, lib_pins, r2, all_anchor_points  # noqa: E402

from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.common import Position, Effects, Font, Justify, Property, PageSettings
from kiutils.items.schitems import (Connection, GlobalLabel, Junction, NoConnect, SchematicSymbol,
                                    SymbolProjectInstance, SymbolProjectPath, Text)

PROJ = OUTPUT_ROOT / "04_PROJECT" / "HybridPanda"
SCH = PROJ / "HybridPanda.kicad_sch"
KICAD_SYMS = Path(r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\symbols")
SHEET_PATH = "/5994f1e8-15cb-459b-8e2e-160b94fba244"
PROJECT_NAME = "HybridPanda"
G = 1.27  # grid

# ----------------------------------------------------------------------------- MCU pin plan (port -> net label)
# labels are global labels; shape per KiCad semantics
MCU_LABELS: dict[str, tuple[str, str]] = {
    "PB9": ("BUS0_TX", "bidirectional"), "PB8": ("BUS0_RX", "bidirectional"), "PG11": ("BUS0_STB", "bidirectional"),
    "PB6": ("BUS1N_TX", "bidirectional"), "PB5": ("BUS1N_RX", "bidirectional"), "PB3": ("BUS1N_STB", "bidirectional"),
    "PB13": ("BUS1O_TX", "bidirectional"), "PB12": ("BUS1O_RX", "bidirectional"), "PB4": ("BUS1O_STB", "bidirectional"),
    "PG9": ("BUS2_TX", "bidirectional"), "PG10": ("BUS2_RX", "bidirectional"), "PD7": ("BUS2_STB", "bidirectional"),
    "PA11": ("USB_D-", "bidirectional"), "PA12": ("USB_D+", "bidirectional"),
    "PB14": ("USB_LOAD", "output"),
    "PF11": ("VoltageSens", "input"),
    "PC4": ("SBU1_ADC", "input"), "PA1": ("SBU2_ADC", "input"),
    "PC10": ("relay_SBU1", "output"), "PC11": ("relay_SBU2", "output"),
    "PE4": ("LED_RED", "output"), "PE3": ("LED_GREEN", "output"), "PE2": ("LED_BLUE", "output"),
    "PB1": ("5VOUT_S", "input"),
    "PH0": ("HSE_IN", "passive"), "PH1": ("HSE_OUT", "passive"),
    "PA13": ("SWDIO", "bidirectional"), "PA14": ("SWCLK", "input"),
    # pin-name keys for non-port pins
    "BOOT0": ("BOOT0", "passive"), "NRST": ("NRST", "passive"),
    "VLXSMPS": ("VLXSMPS", "passive"), "VFBSMPS": ("VFBSMPS", "passive"), "VREF+": ("VDDA", "passive"),
    "VCAP": ("VCAP", "passive"),
}
MCU_TO_3V3 = {"PDR_ON"}
# hw-type straps: board.h detects with internal pull-up, RED = all four read low -> hard-wired to GND
MCU_TO_GND = {"PF7", "PF8", "PF9", "PF10"}

# deletion regions (x0, x1, y0, y1)
REGIONS = [(258, 382, 228, 326), (238, 258, 255, 282), (105, 200, 265, 350)]
LABEL_RENAME = {"CAN2": "BUS0", "CAN3": "BUS1N", "CAN1": "BUS1O", "CAN0": "BUS2"}
SUFFIX_RENAME = {"EN": "STB"}

log = JsonLog("step4_build_schematic")


def nid() -> str:
    return str(uuid.uuid4())


def inside(x, y) -> bool:
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in REGIONS)


def ref_of(sym) -> str:
    return next(p.value for p in sym.properties if p.key == "Reference")


# ----------------------------------------------------------------------------- builder
class Builder:
    def __init__(self, sch: Schematic):
        self.sch = sch
        self.refcount: dict[str, int] = {}
        for s in sch.schematicSymbols:
            m = re.match(r"^(#?[A-Z]+)(\d+)$", ref_of(s))
            if m:
                self.refcount[m.group(1)] = max(self.refcount.get(m.group(1), 0), int(m.group(2)))
        self.added: list[dict] = []

    # --- library symbols
    def ensure_lib(self, lib: str, name: str):
        lib_id = f"{lib}:{name}"
        if any(ls.libId == lib_id for ls in self.sch.libSymbols):
            return lib_id
        sl = SymbolLib.from_file(str(KICAD_SYMS / f"{lib}.kicad_sym"))
        src = next(s for s in sl.symbols if s.entryName == name)
        if src.extends:
            parent = next(s for s in sl.symbols if s.entryName == src.extends)
            merged = deepcopy(parent)
            merged.properties = deepcopy(src.properties)
            src = merged
        sym = deepcopy(src)
        sym.libId = lib_id  # unit ids stay "Name_unit_style" exactly as in the baseline file
        self.sch.libSymbols.append(sym)
        log.info("lib symbol added", lib_id=lib_id)
        return lib_id

    def next_ref(self, prefix: str) -> str:
        self.refcount[prefix] = self.refcount.get(prefix, 0) + 1
        return f"{prefix}{self.refcount[prefix]}"

    # --- primitives
    def wire(self, x1, y1, x2, y2):
        self.sch.graphicalItems.append(Connection(type="wire", points=[Position(r2(x1), r2(y1)), Position(r2(x2), r2(y2))], uuid=nid()))

    def junction(self, x, y):
        self.sch.junctions.append(Junction(position=Position(r2(x), r2(y)), uuid=nid()))

    def nc(self, x, y):
        self.sch.noConnects.append(NoConnect(position=Position(r2(x), r2(y)), uuid=nid()))

    def label(self, text, x, y, angle=0, shape="bidirectional"):
        just = {0: "left", 180: "right", 90: "left", 270: "right"}[angle]
        gl = GlobalLabel(text=text, shape=shape, fieldsAutoplaced=True,
                         position=Position(r2(x), r2(y), angle),
                         effects=Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally=just)),
                         uuid=nid(),
                         properties=[Property(key="Intersheetrefs", value="${INTERSHEET_REFS}",
                                              position=Position(r2(x), r2(y), angle),
                                              effects=Effects(font=Font(height=1.27, width=1.27),
                                                              justify=Justify(horizontally=just), hide=True))])
        self.sch.globalLabels.append(gl)

    def text(self, s, x, y):
        self.sch.texts.append(Text(text=s, position=Position(r2(x), r2(y), 0),
                                   effects=Effects(font=Font(height=2.54, width=2.54, bold=True)), uuid=nid()))

    def symbol(self, lib, name, ref_prefix, value, footprint, x, y, angle=0, mirror=None, unit=1, ref=None,
               hide_value=False, datasheet="~"):
        lib_id = self.ensure_lib(lib, name)
        ref = ref or self.next_ref(ref_prefix)
        is_power = ref.startswith("#")
        props = [
            Property(key="Reference", value=ref, position=Position(r2(x), r2(y + (6.35 if is_power else -3.81)), 0),
                     effects=Effects(font=Font(height=1.27, width=1.27), hide=is_power)),
            Property(key="Value", value=value, position=Position(r2(x), r2(y + (5.08 if is_power else 3.81)), 0),
                     effects=Effects(font=Font(height=1.27, width=1.27), hide=hide_value)),
            Property(key="Footprint", value=footprint, position=Position(r2(x), r2(y), 0),
                     effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
            Property(key="Datasheet", value=datasheet, position=Position(r2(x), r2(y), 0),
                     effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        ]
        pins = {p.number: nid() for p in lib_pins(self.sch, lib_id, unit)}
        sym = SchematicSymbol(libraryNickname=lib, entryName=name, position=Position(r2(x), r2(y), angle),
                              unit=unit, inBom=not is_power, onBoard=True, dnp=False, fieldsAutoplaced=True,
                              uuid=nid(), properties=props, pins=pins, mirror=mirror,
                              instances=[SymbolProjectInstance(name=PROJECT_NAME,
                                                               paths=[SymbolProjectPath(sheetInstancePath=SHEET_PATH,
                                                                                        reference=ref, unit=unit)])])
        self.sch.schematicSymbols.append(sym)
        self.added.append({"ref": ref, "lib_id": lib_id, "value": value, "footprint": footprint, "pos": [r2(x), r2(y)]})
        return sym

    def pins_abs(self, sym) -> dict[str, tuple[float, float]]:
        out = {}
        for p in lib_pins(self.sch, sym.libId, sym.unit):
            out[p.number] = transform(p.position.X, p.position.Y, sym.position.X, sym.position.Y, sym.position.angle, sym.mirror)
        return out

    # --- power helpers
    def pwr(self, name, x, y, angle=0):
        return self.symbol("power", name, "#PWR", name, "", x, y, angle, hide_value=False)

    def flag(self, x, y, angle=0):
        return self.symbol("power", "PWR_FLAG", "#FLG", "PWR_FLAG", "", x, y, angle)

    # two-pin vertical part (C_Small/R_Small): pin1 at y-2.54, pin2 at y+2.54 (angle 0)
    def cap(self, value, x, y, fp="Capacitor_SMD:C_0402_1005Metric", ref=None):
        return self.symbol("Device", "C_Small", "C", value, fp, x, y, 0, ref=ref)

    def res(self, value, x, y, angle=0, fp="Resistor_SMD:R_0402_1005Metric", ref=None):
        return self.symbol("Device", "R_Small", "R", value, fp, x, y, angle, ref=ref)


# ----------------------------------------------------------------------------- phases
def phase_delete(sch: Schematic) -> dict:
    stats = {}
    keep_syms, removed = [], []
    for s in sch.schematicSymbols:
        if inside(s.position.X, s.position.Y):
            removed.append(ref_of(s))
        else:
            keep_syms.append(s)
    sch.schematicSymbols = keep_syms
    stats["symbols"] = removed

    keep, n = [], 0
    for g in sch.graphicalItems:
        if isinstance(g, Connection):
            if any(inside(p.X, p.Y) for p in g.points):
                n += 1
                continue
        else:
            pts = []
            for attr in ("start", "end"):
                if hasattr(g, attr) and getattr(g, attr) is not None:
                    pts.append(getattr(g, attr))
            if hasattr(g, "points") and g.points:
                pts.extend(g.points)
            if pts and all(inside(p.X, p.Y) for p in pts):
                n += 1
                continue
        keep.append(g)
    sch.graphicalItems = keep
    stats["wires_or_graphics"] = n

    for coll in ("junctions", "noConnects", "globalLabels", "labels", "texts"):
        items = getattr(sch, coll)
        before = len(items)
        setattr(sch, coll, [it for it in items if not inside(it.position.X, it.position.Y)])
        stats[coll] = before - len(getattr(sch, coll))
    sch.texts = [t for t in sch.texts if t.text.strip() != "GPS"]
    return stats


def phase_rename_labels(sch: Schematic) -> dict:
    out = {}
    for gl in sch.globalLabels:
        m = re.match(r"^(CAN[0-3])_(TX|RX|EN|H|L)$", gl.text)
        if m:
            new = f"{LABEL_RENAME[m.group(1)]}_{SUFFIX_RENAME.get(m.group(2), m.group(2))}"
            out[gl.text] = new
            gl.text = new
    for t in sch.texts:
        if t.text == "Microcontroller":
            t.position = Position(652.78, 152.4, 0)
    return out


def phase_mcu(b: Builder) -> dict:
    sch = b.sch
    MX, MY = 701.04, 266.70
    u7 = b.symbol("MCU_ST_STM32H7", "STM32H725ZGTx", "U", "STM32H725ZGT6", "Package_QFP:LQFP-144_20x20mm_P0.5mm",
                  MX, MY, ref="U7", datasheet="https://www.st.com/resource/en/datasheet/stm32h725zg.pdf")
    # field placement: above the body
    for p in u7.properties:
        if p.key == "Reference":
            p.position = Position(MX - 40.64, MY - 101.6, 0)
        elif p.key == "Value":
            p.position = Position(MX - 20.32, MY - 101.6, 0)
    used = {}
    gnd_pts: list[tuple[float, float]] = []
    pins = lib_pins(sch, u7.libId, 1)
    top_rail_a, top_rail_b, bottom = [], [], []
    for p in pins:
        ax, ay = transform(p.position.X, p.position.Y, MX, MY, 0, None)
        port = re.match(r"^(P[A-K]\d+|[A-Z0-9_+]+)", p.name).group(1)
        ang = p.position.angle  # 0 = left side, 180 = right, 270 = top, 90 = bottom
        if ang in (0, 180):
            dx = -5.08 if ang == 0 else 5.08
            if port in MCU_LABELS:
                net, shape = MCU_LABELS[port]
                b.wire(ax, ay, ax + dx, ay)
                b.label(net, ax + dx, ay, 180 if ang == 0 else 0, shape)
                used[f"{port}#{p.number}"] = net
            elif port in MCU_TO_3V3:
                b.wire(ax, ay, ax + dx, ay)
                b.pwr("+3.3V", ax + dx, ay, 0)
                used[f"{port}#{p.number}"] = "+3.3V"
            elif port in MCU_TO_GND:
                b.wire(ax, ay, ax + dx, ay)
                gnd_pts.append((ax + dx, ay))
                used[f"{port}#{p.number}"] = "GND"
            else:
                b.nc(ax, ay)
        elif ang == 270:  # top power pins
            if p.name == "VDDA":
                b.wire(ax, ay, ax, ay - 10.16)
                b.label("VDDA", ax, ay - 10.16, 90, "passive")
            elif p.name in ("VDDLDO", "VDDSMPS"):
                top_rail_b.append(ax)
            else:
                top_rail_a.append(ax)
            used[f"{p.name}#{p.number}"] = "VDDA" if p.name == "VDDA" else "+3.3V"
        elif ang == 90:  # bottom VSS pins
            bottom.append(ax)
            used[f"{p.name}#{p.number}"] = "GND"
    ytop = MY - 93.98
    # HW_ID straps: join the four stub ends vertically and put one GND above the highest (below is PF11/VoltageSens)
    gnd_pts.sort(key=lambda t: t[1])
    gx = gnd_pts[0][0]
    assert all(x == gx for x, _ in gnd_pts), gnd_pts
    b.wire(gx, gnd_pts[0][1] - 2.54, gx, gnd_pts[-1][1])
    for _, y in gnd_pts[:-1]:
        b.junction(gx, y)
    b.pwr("GND", gx, gnd_pts[0][1] - 2.54, 180)
    rail_y = ytop - 5.08
    for xs, flag_end in ((top_rail_a, "left"), (top_rail_b, "right")):
        xs = sorted(set(xs))
        for x in xs:
            b.wire(x, ytop, x, rail_y)
        b.wire(xs[0], rail_y, xs[-1], rail_y)
        for x in xs[1:-1]:
            b.junction(x, rail_y)
        px = xs[0] if flag_end == "left" else xs[-1]
        b.pwr("+3.3V", px, rail_y, 0)
    ybot = MY + 93.98
    xs = sorted(set(bottom))
    for x in xs:
        b.wire(x, ybot, x, ybot + 5.08)
    b.wire(xs[0], ybot + 5.08, xs[-1], ybot + 5.08)
    mid = xs[len(xs) // 2]
    b.wire(mid, ybot + 5.08, mid, ybot + 7.62)
    b.junction(mid, ybot + 5.08)
    b.pwr("GND", mid, ybot + 7.62, 0)
    return used


def phase_support(b: Builder, bom: dict):
    """Support blocks in column x~787-815, and reused freed regions."""
    L = 787.40  # left label x for horizontal blocks

    # --- HSE 25 MHz (Y1 Crystal_GND24_Small, C23/C24 recalculated: see bom['hse'])
    b.text("HSE 25 MHz", 790.0, 179.0)
    y1 = b.symbol("Device", "Crystal_GND24_Small", "Y", bom["hse"]["crystal_value"], bom["hse"]["crystal_fp"], 800.10, 190.50, ref="Y1",
                  datasheet=bom["hse"].get("crystal_ds", "~"))
    pp = b.pins_abs(y1)
    b.wire(*pp["4"], 800.10, 185.42); b.pwr("GND", 800.10, 185.42, 180)
    b.wire(*pp["1"], 792.48, 190.50); b.wire(792.48, 190.50, L, 190.50); b.label("HSE_IN", L, 190.50, 180, "passive")
    b.wire(*pp["3"], 807.72, 190.50); b.wire(807.72, 190.50, 812.80, 190.50); b.label("HSE_OUT", 812.80, 190.50, 0, "passive")
    c23 = b.cap(bom["hse"]["cl_value"], 792.48, 195.58, ref="C23"); c24 = b.cap(bom["hse"]["cl_value"], 807.72, 195.58, ref="C24")
    for c, x in ((c23, 792.48), (c24, 807.72)):
        cp = b.pins_abs(c)
        b.wire(x, 190.50, *cp["1"]); b.junction(x, 190.50)
        b.wire(*cp["2"], x, 200.66); b.pwr("GND", x, 200.66)
    b.wire(*pp["2"], 800.10, 195.58); b.pwr("GND", 800.10, 195.58)

    # --- BOOT0: SW1 to +3V3, R14 10k pull-down
    b.text("BOOT0", 790.0, 211.0)
    sw = b.symbol("Switch", "SW_Push", "SW", "SW_Push", bom["sw_fp"], 800.10, 218.44, ref="SW1")
    sp = b.pins_abs(sw)
    b.wire(*sp["2"], 807.72, 218.44); b.pwr("+3.3V", 807.72, 218.44)
    b.wire(*sp["1"], 792.48, 218.44); b.wire(792.48, 218.44, L, 218.44); b.label("BOOT0", L, 218.44, 180, "passive")
    r14 = b.res("10k", 792.48, 223.52, ref="R14"); rp = b.pins_abs(r14)
    b.wire(792.48, 218.44, *rp["1"]); b.junction(792.48, 218.44)
    b.wire(*rp["2"], 792.48, 228.60); b.pwr("GND", 792.48, 228.60)

    # --- NRST 100nF
    b.text("NRST", 790.0, 236.0)
    cn = b.cap("100nF", 792.48, 243.84); cp = b.pins_abs(cn)
    b.wire(L, 241.30, *cp["1"]); b.label("NRST", L, 241.30, 180, "passive")
    b.wire(*cp["2"], 792.48, 248.92); b.pwr("GND", 792.48, 248.92)

    # --- SWD header (ARM 10-pin 1.27 mm)
    b.text("SWD (ARM 10-pin)", 790.0, 258.0)
    j1 = b.symbol("Connector_Generic", "Conn_02x05_Odd_Even", "J", "SWD", bom["swd_fp"], 800.10, 269.24)
    jp = b.pins_abs(j1)
    b.wire(*jp["1"], 789.94, 264.16); b.pwr("+3.3V", 789.94, 264.16)
    for n in ("3", "5", "9"):
        b.wire(*jp[n], 789.94, jp[n][1])
    b.wire(789.94, 266.70, 789.94, 276.86); b.junction(789.94, 269.24); b.junction(789.94, 274.32); b.pwr("GND", 789.94, 276.86)
    b.nc(*jp["7"]); b.nc(*jp["6"]); b.nc(*jp["8"])
    b.wire(*jp["2"], 812.80, 264.16); b.label("SWDIO", 812.80, 264.16, 0, "bidirectional")
    b.wire(*jp["4"], 812.80, 266.70); b.label("SWCLK", 812.80, 266.70, 0, "input")
    b.wire(*jp["10"], 812.80, 274.32); b.label("NRST", 812.80, 274.32, 0, "passive")

    # --- VCAP 2x2.2uF
    b.text("VCAP", 790.0, 286.0)
    b.wire(L, 292.10, 800.10, 292.10); b.label("VCAP", L, 292.10, 180, "passive")
    for x in (792.48, 800.10):
        c = b.cap("2.2uF", x, 297.18, fp="Capacitor_SMD:C_0603_1608Metric"); cp = b.pins_abs(c)
        b.wire(x, 292.10, *cp["1"]); b.wire(*cp["2"], x, 302.26); b.pwr("GND", x, 302.26)
    b.junction(792.48, 292.10)

    # --- SMPS: VLXSMPS -> L 2.2uH -> VFBSMPS, 220pF at VLX, 10uF at VFB, PWR_FLAG on VLXSMPS
    b.text("SMPS step-down", 790.0, 309.0)
    b.wire(L, 314.96, 795.02, 314.96); b.label("VLXSMPS", L, 314.96, 180, "passive")
    b.wire(795.02, 314.96, 800.10, 314.96); b.junction(795.02, 314.96); b.flag(795.02, 314.96)
    ind = b.symbol("Device", "L", "L", bom["smps"]["l_value"], bom["smps"]["l_fp"], 803.91, 314.96, 90, datasheet=bom["smps"].get("l_ds", "~"))
    lp = b.pins_abs(ind)
    assert lp["1"] == (800.10, 314.96) and lp["2"] == (807.72, 314.96), lp
    b.wire(807.72, 314.96, 812.80, 314.96); b.label("VFBSMPS", 812.80, 314.96, 0, "passive")
    c = b.cap("220pF", 792.48, 320.04); cp = b.pins_abs(c)
    b.wire(792.48, 314.96, *cp["1"]); b.junction(792.48, 314.96); b.wire(*cp["2"], 792.48, 325.12); b.pwr("GND", 792.48, 325.12)
    c = b.cap("10uF", 807.72, 320.04, fp="Capacitor_SMD:C_0805_2012Metric"); cp = b.pins_abs(c)
    b.wire(807.72, 314.96, *cp["1"]); b.junction(807.72, 314.96); b.wire(*cp["2"], 807.72, 325.12); b.pwr("GND", 807.72, 325.12)

    # --- VDDA filter: FB + 1uF + 100nF
    b.text("VDDA filter", 790.0, 332.0)
    b.wire(L, 337.82, 795.02, 337.82); b.wire(795.02, 337.82, 800.10, 337.82); b.label("VDDA", L, 337.82, 180, "passive")
    b.junction(795.02, 337.82); b.flag(795.02, 337.82)  # VDDA is fed through a ferrite: flag it as driven
    fb = b.symbol("Device", "FerriteBead_Small", "FB", "600R@100MHz", "Inductor_SMD:L_0603_1608Metric", 802.64, 337.82, 90)
    fp_ = b.pins_abs(fb); assert fp_["1"] == (800.10, 337.82), fp_
    b.wire(805.18, 337.82, 807.72, 337.82); b.pwr("+3.3V", 807.72, 337.82)
    for x, v in ((792.48, "1uF"), (797.56, "100nF")):
        c = b.cap(v, x, 342.90); cp = b.pins_abs(c)
        b.wire(x, 337.82, *cp["1"]); b.junction(x, 337.82); b.wire(*cp["2"], x, 347.98); b.pwr("GND", x, 347.98)

    # --- LED series resistors (reuse R17/R18/R19 values from baseline: 180R blue, 110R green, 100R red)
    b.text("LED drivers (PE4/PE3/PE2, active low)", 790.0, 351.0)
    for y, ref, val, net_in, net_out in ((355.60, "R19", "100R", "LED_RED", "RED-"),
                                          (360.68, "R18", "110R", "LED_GREEN", "GREEN-"),
                                          (365.76, "R17", "180R", "LED_BLUE", "BLUE-")):
        r = b.res(val, 792.48, y, 90, ref=ref); rp = b.pins_abs(r)
        b.wire(L, y, *rp["1"]); b.label(net_in, L, y, 180, "input")
        b.wire(*rp["2"], 797.56, y); b.label(net_out, 797.56, y, 0, "input")

    # --- SBU ADC conditioning: 10k series + BAT54S clamp (D-16)
    b.text("SBU ADC conditioning (10k + BAT54S)", 790.0, 373.0)
    for y, sbu, adc in ((378.46, "SBU1", "SBU1_ADC"), (398.78, "SBU2", "SBU2_ADC")):
        r = b.res("10k", 792.48, y, 90); rp = b.pins_abs(r)
        b.wire(L, y, *rp["1"]); b.label(sbu, L, y, 180, "bidirectional")
        b.wire(*rp["2"], 812.80, y); b.label(adc, 812.80, y, 0, "input")
        d = b.symbol("Diode", "BAT54S", "D", "BAT54S", "Package_TO_SOT_SMD:SOT-23", 800.10, y + 5.08, 180)
        dp = b.pins_abs(d)
        assert dp["3"] == (800.10, y), dp
        b.junction(800.10, y)
        b.wire(*dp["2"], dp["2"][0], y + 7.62); b.pwr("+3.3V", dp["2"][0], y + 7.62, 180)  # K -> 3V3
        b.wire(*dp["1"], dp["1"][0], y + 7.62); b.pwr("GND", dp["1"][0], y + 7.62, 0)      # A -> GND

    # --- 5VOUT_S divider (R15/R16 10k, +5V -> PB1)
    b.text("5V sense (PB1)", 790.0, 414.0)
    b.pwr("+5V", 792.48, 419.10)
    r15 = b.res("10k", 792.48, 424.18, ref="R15"); rp = b.pins_abs(r15)
    b.wire(792.48, 419.10, *rp["1"]); b.wire(*rp["2"], L, 426.72); b.label("5VOUT_S", L, 426.72, 180, "input")
    r16 = b.res("10k", 792.48, 431.80, ref="R16"); rp2 = b.pins_abs(r16)
    b.wire(792.48, 426.72, *rp2["1"]); b.junction(792.48, 426.72); b.wire(*rp2["2"], 792.48, 436.88); b.pwr("GND", 792.48, 436.88)

    # --- STB pull-ups (D-09) in freed region R1
    b.text("CAN STB pull-ups (default standby)", 262.0, 243.0)
    for i, net in enumerate(("BUS0_STB", "BUS1N_STB", "BUS1O_STB", "BUS2_STB")):
        x = 271.78 + i * 10.16
        r = b.res("10k", x, 254.00, 0); rp = b.pins_abs(r)
        b.pwr("+3.3V", x, 248.92); b.wire(x, 248.92, *rp["1"])
        b.wire(*rp["2"], x, 259.08); b.label(net, x, 259.08, 270, "bidirectional")

    # --- decoupling bank for the H725 (in freed region R1): 15x100nF + 3x4.7uF + 1uF (plus baseline C1/C2/C5/C11/C14)
    b.text("STM32H725 decoupling (VDD/VBAT/VDDLDO/VDDSMPS/VDD33USB)", 320.0, 275.5)
    vals = ["100nF"] * 15 + ["4.7uF"] * 3 + ["1uF"]
    xs = [266.70 + i * 5.08 for i in range(len(vals))]
    for x, v in zip(xs, vals):
        fp = "Capacitor_SMD:C_0603_1608Metric" if v == "4.7uF" else "Capacitor_SMD:C_0402_1005Metric"
        c = b.cap(v, x, 284.48, fp=fp); cp = b.pins_abs(c)
        b.wire(x, 279.40, *cp["1"]); b.wire(*cp["2"], x, 289.56)
    b.wire(xs[0], 279.40, xs[-1], 279.40); b.wire(xs[0], 289.56, xs[-1], 289.56)
    for x in xs[1:-1]:
        b.junction(x, 279.40); b.junction(x, 289.56)
    b.pwr("+3.3V", xs[0], 279.40); b.pwr("GND", xs[-1], 289.56)

    # --- PWR_FLAG cluster (fixes inherited ERC power_pin_not_driven) in freed region R3
    b.text("Power flags", 110.0, 295.0)
    for i, net in enumerate(("GND", "+3.3V", "+5V", "+12V")):
        x = 120.65 + i * 12.70
        b.flag(x, 300.99); b.wire(x, 300.99, x, 306.07)
        b.pwr(net, x, 306.07, 0 if net == "GND" else 180)
    x = 120.65 + 4 * 12.70
    b.flag(x, 300.99); b.wire(x, 300.99, x, 306.07); b.label("12V_Protected", x, 306.07, 270, "passive")


def phase_instances(sch: Schematic):
    n = 0
    for s in sch.schematicSymbols:
        for inst in s.instances or []:
            if inst.name == "BlackPanda":
                inst.name = PROJECT_NAME
                n += 1
    return n


def auto_junctions(b: Builder) -> int:
    """add junction dots where >=3 wire ends meet or a wire end sits on another wire's middle (connectivity safety)."""
    ends: dict[tuple, int] = {}
    wires = [g for g in b.sch.graphicalItems if isinstance(g, Connection)]
    for w in wires:
        for p in (w.points[0], w.points[-1]):
            ends[(r2(p.X), r2(p.Y))] = ends.get((r2(p.X), r2(p.Y)), 0) + 1
    have = {(r2(j.position.X), r2(j.position.Y)) for j in b.sch.junctions}
    added = 0
    for pt, n in ends.items():
        if pt in have:
            continue
        on_mid = False
        for w in wires:
            (x1, y1), (x2, y2) = (w.points[0].X, w.points[0].Y), (w.points[-1].X, w.points[-1].Y)
            if (x1, y1) == pt or (x2, y2) == pt:
                continue
            if min(x1, x2) - 1e-3 <= pt[0] <= max(x1, x2) + 1e-3 and min(y1, y2) - 1e-3 <= pt[1] <= max(y1, y2) + 1e-3 \
                    and abs((x2 - x1) * (pt[1] - y1) - (y2 - y1) * (pt[0] - x1)) < 1e-3:
                on_mid = True
                break
        if n >= 3 or on_mid:
            b.junction(*pt); have.add(pt); added += 1
    return added


def dangling_report(sch: Schematic) -> list:
    """wire ends not touching any pin/label/junction/other wire end -> reported (must be empty)."""
    anchors = all_anchor_points(sch)
    pin_pts = set()
    for sym in sch.schematicSymbols:
        for p in lib_pins(sch, sym.libId, sym.unit):
            pin_pts.add(transform(p.position.X, p.position.Y, sym.position.X, sym.position.Y, sym.position.angle, sym.mirror))
    wires = [g for g in sch.graphicalItems if isinstance(g, Connection)]
    ends: dict[tuple, int] = {}
    for w in wires:
        for p in (w.points[0], w.points[-1]):
            ends[(r2(p.X), r2(p.Y))] = ends.get((r2(p.X), r2(p.Y)), 0) + 1
    labels = {(r2(g.position.X), r2(g.position.Y)) for g in sch.globalLabels + sch.labels}
    juncs = {(r2(j.position.X), r2(j.position.Y)) for j in sch.junctions}
    bad = []
    for pt, n in ends.items():
        if n >= 2 or pt in pin_pts or pt in labels or pt in juncs:
            continue
        bad.append(pt)
    return sorted(bad)


def phase_project():
    """project file: name + ERC pin-conflict map (power_out<->power_out = warning, needed because the KiCad H7 symbol
    declares the three VCAP pins as power_out while ST requires them tied together; D-19)."""
    pro = PROJ / "HybridPanda.kicad_pro"
    d = json.loads(pro.read_text(encoding="utf-8"))
    d["meta"]["filename"] = "HybridPanda.kicad_pro"
    pm = d["erc"]["pin_map"]
    pm[8][8] = 1  # index 8 = power_out
    backup_before_write(pro, tag="step4_build")
    pro.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # project-local symbol libs were renamed to HybridPanda.symbols by the copy step; retarget the table
    slt = PROJ / "sym-lib-table"
    txt = slt.read_text(encoding="utf-8")
    if "BlackPanda.symbols" in txt:
        backup_before_write(slt, tag="step4_build")
        slt.write_text(txt.replace("BlackPanda.symbols", "HybridPanda.symbols"), encoding="utf-8")


def collision_report(sch: Schematic) -> list:
    """points where two different net names (global labels / power symbols) coincide -> accidental shorts."""
    names: dict[tuple, set] = {}
    for g in sch.globalLabels:
        names.setdefault((r2(g.position.X), r2(g.position.Y)), set()).add(g.text)
    for s in sch.schematicSymbols:
        if s.libraryNickname == "power" and s.entryName != "PWR_FLAG":
            val = next(p.value for p in s.properties if p.key == "Value")
            for pt in (transform(p.position.X, p.position.Y, s.position.X, s.position.Y, s.position.angle, s.mirror)
                       for p in lib_pins(sch, s.libId, s.unit)):
                names.setdefault(pt, set()).add(val)
    return sorted((pt, sorted(v)) for pt, v in names.items() if len(v) > 1)


def main():
    bom_path = OUTPUT_ROOT / "05_SCRIPTS" / "step4_bom_values.json"
    bom = json.loads(bom_path.read_text(encoding="utf-8"))
    assert_inside_output(SCH)
    # idempotency: always build from the pristine baseline copy
    pristine = SCH.with_suffix(".kicad_sch.baseline")
    if not pristine.exists():
        first_backup = sorted((OUTPUT_ROOT / "99_BACKUPS").glob("*_step4_build/04_PROJECT/HybridPanda/HybridPanda.kicad_sch"))
        src = first_backup[0] if first_backup else SCH
        pristine.write_bytes(src.read_bytes())
        log.info("pristine baseline stored", src=str(src))
    sch = Schematic.from_file(str(pristine))
    base_counts = {"symbols": len(sch.schematicSymbols), "labels": len(sch.globalLabels), "wires": len(sch.graphicalItems)}

    del_stats = phase_delete(sch)
    log.info("deleted", **{k: (v if not isinstance(v, list) else len(v)) for k, v in del_stats.items()})
    renames = phase_rename_labels(sch)
    log.info("labels renamed", n=len(renames))

    sch.paper = PageSettings(paperSize="A1")
    b = Builder(sch)
    mcu_used = phase_mcu(b)
    phase_support(b, bom)
    n_inst = phase_instances(sch)
    n_j = auto_junctions(b)
    dang = dangling_report(sch)
    if dang:
        log.error("dangling wire ends", points=dang)
        raise SystemExit("dangling wire ends: " + str(dang))
    coll = collision_report(sch)
    if coll:
        log.error("net name collisions", points=coll)
        raise SystemExit("net name collisions: " + str(coll))

    backup_before_write(SCH, tag="step4_build")
    sch.to_file(str(SCH))
    phase_project()
    report = {
        "schematic": str(SCH), "baseline_counts": base_counts, "deleted": del_stats, "label_renames": renames,
        "mcu_pins_used": mcu_used, "added_symbols": b.added, "instances_renamed": n_inst, "auto_junctions": n_j,
        "final_counts": {"symbols": len(sch.schematicSymbols), "labels": len(sch.globalLabels),
                         "wires": len([g for g in sch.graphicalItems if isinstance(g, Connection)]),
                         "noconnects": len(sch.noConnects), "junctions": len(sch.junctions)},
    }
    out = OUTPUT_ROOT / "06_REPORTS" / "step4_build_schematic.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("written", report=str(out))
    print(json.dumps({k: v for k, v in report.items() if k in ("baseline_counts", "final_counts", "instances_renamed", "auto_junctions")}, indent=1))
    print("deleted symbols:", del_stats["symbols"])


if __name__ == "__main__":
    main()
