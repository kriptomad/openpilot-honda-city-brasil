"""_probe_render.py - scratch rasterizer (PIL) of copper items per layer in a region."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hp_common as hp
import pcbnew
from pcbnew import ToMM
from PIL import Image, ImageDraw, ImageFont

PCB = str(hp.OUTPUT_ROOT / "hardware/hybrid-panda/HybridPanda.kicad_pcb")
OUTD = str(hp.OUTPUT_ROOT / "hardware/reports/verification-pcb")
x0, y0, x1, y1 = [float(v) for v in sys.argv[1:5]] if len(sys.argv) > 5 else (108, 33, 136, 50)
tag = sys.argv[5] if len(sys.argv) > 5 else "probe"
S = 40  # px per mm
board = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
W, H = int((x1 - x0) * S), int((y1 - y0) * S)
def px(v): return ((ToMM(v.x) - x0) * S, (ToMM(v.y) - y0) * S)
def poly_pts(outline):
    return [((ToMM(outline.CPoint(i).x) - x0) * S, (ToMM(outline.CPoint(i).y) - y0) * S) for i in range(outline.PointCount())]
NETCOL = {"GND": (60, 60, 60), "+3V3": (120, 40, 40), "+5V": (40, 90, 40), "12V_Protected": (90, 60, 20), "+12V": (90, 60, 20),
          "USB_D+": (255, 60, 60), "USB_D-": (60, 120, 255), "USB_R_D+": (255, 120, 0), "USB_R_D-": (0, 200, 255)}
def col(net, default=(160, 160, 160)): return NETCOL.get(net, default)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
    im = Image.new("RGB", (W, H), (0, 0, 0)); dr = ImageDraw.Draw(im)
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(layer): continue
        polys = z.GetFilledPolysList(layer)
        for i in range(polys.OutlineCount()):
            pts = poly_pts(polys.Outline(i))
            if len(pts) > 2: dr.polygon(pts, fill=col(z.GetNetname(), (50, 50, 50)))
            for h in range(polys.HoleCount(i)):
                hp_ = poly_pts(polys.Hole(i, h))
                if len(hp_) > 2: dr.polygon(hp_, fill=(0, 0, 0))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(layer): continue
            shp = p.GetEffectiveShape(layer); bb = shp.BBox()
            a = ((ToMM(bb.GetLeft()) - x0) * S, (ToMM(bb.GetTop()) - y0) * S); b = ((ToMM(bb.GetRight()) - x0) * S, (ToMM(bb.GetBottom()) - y0) * S)
            c = col(p.GetNetname(), (200, 200, 200))
            dr.rectangle([a, b], fill=c, outline=(255, 255, 255))
            if p.GetDrillSize().x:
                r = ToMM(p.GetDrillSize().x) / 2 * S; cx, cy = px(p.GetPosition()); dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
        if fp.IsFlipped() == (layer == pcbnew.B_Cu):
            cx, cy = px(fp.GetPosition()); dr.text((cx + 2, cy + 2), fp.GetReference(), fill=(255, 255, 0))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            cx, cy = px(t.GetPosition()); r = ToMM(t.GetWidth(layer)) / 2 * S
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col(t.GetNetname(), (230, 230, 230)), outline=(255, 255, 255))
            rr = ToMM(t.GetDrill()) / 2 * S; dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(0, 0, 0))
        elif t.GetLayer() == layer:
            dr.line([px(t.GetStart()), px(t.GetEnd())], fill=col(t.GetNetname(), (200, 200, 200)), width=max(1, int(ToMM(t.GetWidth()) * S)))
    for gx in range(int(x0), int(x1) + 1):
        dr.line([((gx - x0) * S, 0), ((gx - x0) * S, H)], fill=(30, 30, 90), width=1); dr.text(((gx - x0) * S + 1, 1), str(gx), fill=(120, 120, 255))
    for gy in range(int(y0), int(y1) + 1):
        dr.line([(0, (gy - y0) * S), (W, (gy - y0) * S)], fill=(30, 30, 90), width=1); dr.text((1, (gy - y0) * S + 1), str(gy), fill=(120, 120, 255))
    im.save(os.path.join(OUTD, "_%s_%s.png" % (tag, board.GetLayerName(layer).replace(".", ""))))
print("ok")
