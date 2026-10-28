"""proposed_fixes.py - aplica (ou simula) as correcoes de footprint da auditoria.

PADRAO = --dry-run: so imprime o que faria. Com --apply: copia a placa para
<placa>.bak_fpaudit_<timestamp> ANTES de salvar.  Nunca foi executado com --apply
contra a placa real pelo auditor.

Uso:
  "C:\\...\\KiCad\\10.0\\bin\\python.exe" proposed_fixes.py <board.kicad_pcb> [--apply] [--refs Q3,U5,...] [--fix attr,3d,...]

Fixes disponiveis (chave -> referencias padrao):
  q3_sot323   Q3      pads -> geometria KiCad SOT-323 (0.925x0.45 em +-0.8875/+-0.65)
  sot23_comma Q1,Q2   pads -> geometria KiCad SOT-23 (0.6x1.475 em +-0.95/+-1.0) + courtyard
  led_u5      U5      pads y +-0.50 -> +-0.60 (datasheet FM-B1921: gap 0.50)
  usbc_p1     P1      B1-B12 pad 0.60 -> 0.70; remove circulos F.Paste graficos sobre PTH
  tps_u6      U6      pads 1-8 ganham F.Mask; EP ganha F.Mask; remove poligonos graficos de mascara/pasta;
                      adiciona pasta no EP via janela 2.6x3.1 (pad SMD so em F.Paste)
  xl1509_u12  U12     remove F.Paste e F.Mask dos 4 pads de EP (SOP-8 sem EP) e troca modelo 3D
  attr_smd    D1,D5-D9,Q1,Q2,U5,L3  atributo THT -> SMD (DRC footprint_type_mismatch)
  model_3d    D8,D9,Q4,U12          atribui/corrige modelo 3D
  courtyard_l3 L3     adiciona courtyard F.CrtYd 8.9 x 7.6
  r6_note     R6      so avisa (troca de footprint deve ser feita no esquema: R_0603)
"""
import argparse
import datetime
import os
import shutil
import sys

import pcbnew

sys.stdout.reconfigure(encoding="utf-8")
MM = pcbnew.FromMM

DEFAULT_REFS = {
    "q3_sot323": ["Q3"],
    "sot23_comma": ["Q1", "Q2"],
    "led_u5": ["U5"],
    "usbc_p1": ["P1"],
    "tps_u6": ["U6"],
    "xl1509_u12": ["U12"],
    "attr_smd": ["D1", "D5", "D6", "D7", "D8", "D9", "Q1", "Q2", "U5", "L3"],
    "model_3d": ["D8", "D9", "Q4", "U12"],
    "courtyard_l3": ["L3"],
    "r6_note": ["R6"],
}
MODELS = {
    "D8": "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "D9": "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "Q4": "${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/PowerPAK_SO-8_Single.step",
    "U12": "${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step",
}

LOG = []


def log(msg):
    LOG.append(msg)
    print(msg)


def set_pad_local(fp, pad, lx, ly, sx, sy):
    """Define posicao local (antes da rotacao do footprint) e tamanho de um pad."""
    import math
    rot = fp.GetOrientation()
    if fp.IsFlipped():
        lx = -lx
    a = fp.GetOrientationDegrees() * math.pi / 180.0
    ax = fp.GetPosition().x + int(round(MM(lx) * math.cos(a) + MM(ly) * math.sin(a)))
    ay = fp.GetPosition().y + int(round(-MM(lx) * math.sin(a) + MM(ly) * math.cos(a)))
    pad.SetPosition(pcbnew.VECTOR2I(ax, ay))
    try:
        pad.SetSize(pcbnew.PADSTACK.ALL_LAYERS, pcbnew.VECTOR2I(MM(sx), MM(sy)))
    except Exception:
        pad.SetSize(pcbnew.VECTOR2I(MM(sx), MM(sy)))
    pad.SetOrientation(rot)


def pad_local(fp, pad):
    import math
    d = pad.GetPosition() - fp.GetPosition()
    a = -fp.GetOrientationDegrees() * math.pi / 180.0
    lx = d.x * math.cos(a) + d.y * math.sin(a)
    ly = -d.x * math.sin(a) + d.y * math.cos(a)
    if fp.IsFlipped():
        lx = -lx
    return pcbnew.ToMM(int(lx)), pcbnew.ToMM(int(ly))


def pad_size(pad):
    try:
        s = pad.GetSize(pcbnew.PADSTACK.ALL_LAYERS)
    except Exception:
        s = pad.GetSize()
    return pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)


def fix_pads(fp, geometry, dry):
    """geometry: {num: (lx, ly, sx, sy)} em mm, coordenadas locais."""
    for pad in fp.Pads():
        g = geometry.get(pad.GetNumber())
        if not g:
            continue
        lx, ly = pad_local(fp, pad)
        sx, sy = pad_size(pad)
        log("  %s pad %s: (%.4f, %.4f) %.3fx%.3f -> (%.4f, %.4f) %.3fx%.3f" % (
            fp.GetReference(), pad.GetNumber(), lx, ly, sx, sy, g[0], g[1], g[2], g[3]))
        if not dry:
            set_pad_local(fp, pad, *g)


def add_courtyard(fp, w, h, dry):
    log("  %s: adicionar courtyard F.CrtYd %.2f x %.2f" % (fp.GetReference(), w, h))
    if dry:
        return
    shape = pcbnew.PCB_SHAPE(fp)
    shape.SetShape(pcbnew.SHAPE_T_RECT)
    shape.SetLayer(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd)
    shape.SetWidth(MM(0.05))
    c = fp.GetPosition()
    shape.SetStart(pcbnew.VECTOR2I(c.x - MM(w / 2), c.y - MM(h / 2)))
    shape.SetEnd(pcbnew.VECTOR2I(c.x + MM(w / 2), c.y + MM(h / 2)))
    fp.Add(shape)
    shape.thisown = 0  # C++ passa a ser dono; evita double free pelo GC do Python


def remove_graphics(fp, layer_names, dry, only_shape=None):
    board = fp.GetBoard()
    n = 0
    for g in list(fp.GraphicalItems()):
        L = board.GetLayerName(g.GetLayer())
        if L not in layer_names:
            continue
        if only_shape and getattr(g, "GetShape", lambda: None)() != only_shape:
            continue
        n += 1
        if not dry:
            g.thisown = 0
            g.DeleteStructure()
    log("  %s: remover %d graficos em %s" % (fp.GetReference(), n, ",".join(layer_names)))


def layers_with(pad, add=(), remove=()):
    ls = pad.GetLayerSet()
    for name in add:
        ls.addLayer(getattr(pcbnew, name))
    for name in remove:
        ls.removeLayer(getattr(pcbnew, name))
    pad.SetLayerSet(ls)


def apply_fix(key, fp, dry):
    ref = fp.GetReference()
    if key == "q3_sot323":
        fix_pads(fp, {"1": (-0.8875, -0.65, 0.925, 0.45), "2": (-0.8875, 0.65, 0.925, 0.45),
                      "3": (0.8875, 0.0, 0.925, 0.45)}, dry)
    elif key == "sot23_comma":
        # orientacao da comma: pino 1 em (+0.889,-1.016), pino 2 em (-0.889,-1.016), pino 3 em (0,+1.0)
        fix_pads(fp, {"1": (0.95, -1.0, 0.6, 1.475), "2": (-0.95, -1.0, 0.6, 1.475),
                      "3": (0.0, 1.0, 0.6, 1.475)}, dry)
        add_courtyard(fp, 3.3, 3.3, dry)
    elif key == "led_u5":
        geo = {}
        for pad in fp.Pads():
            lx, ly = pad_local(fp, pad)
            geo[pad.GetNumber()] = (lx, 0.60 if ly > 0 else -0.60, 0.66, 0.70)
        fix_pads(fp, geo, dry)
    elif key == "usbc_p1":
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNumber().startswith("B"):
                sx, sy = pad_size(pad)
                log("  P1 pad %s: %.2fx%.2f -> 0.70x0.70 (furo 0.40, anel 0.15)" % (pad.GetNumber(), sx, sy))
                if not dry:
                    try:
                        pad.SetSize(pcbnew.PADSTACK.ALL_LAYERS, pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
                    except Exception:
                        pad.SetSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
        remove_graphics(fp, ["F.Paste"], dry, only_shape=pcbnew.SHAPE_T_CIRCLE)
    elif key == "tps_u6":
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n in [str(i) for i in range(1, 9)]:
                log("  U6 pad %s: + F.Mask" % n)
                if not dry:
                    layers_with(pad, add=("F_Mask",))
            elif n == "9" and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                sx, sy = pad_size(pad)
                if sx > 2.0:
                    log("  U6 EP pad 9 (%.2fx%.2f): + F.Mask" % (sx, sy))
                    if not dry:
                        layers_with(pad, add=("F_Mask",))
        log("  U6: adicionar pad '9' extra 2.6x3.1 apenas F.Paste (janela de pasta TI)")
        if not dry:
            p = pcbnew.PAD(fp)
            p.SetNumber("9")
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetShape(pcbnew.PAD_SHAPE_RECT)
            try:
                p.SetSize(pcbnew.PADSTACK.ALL_LAYERS, pcbnew.VECTOR2I(MM(2.6), MM(3.1)))
            except Exception:
                p.SetSize(pcbnew.VECTOR2I(MM(2.6), MM(3.1)))
            p.SetPosition(fp.GetPosition())
            p.SetOrientation(fp.GetOrientation())
            ls = pcbnew.LSET()
            ls.addLayer(pcbnew.F_Paste)
            p.SetLayerSet(ls)
            fp.Add(p)
            p.thisown = 0
        remove_graphics(fp, ["F.Mask", "F.Paste"], dry)
    elif key == "xl1509_u12":
        for pad in fp.Pads():
            if pad.GetNumber() in ("9", "EP", ""):
                sx, sy = pad_size(pad)
                log("  U12 pad '%s' %.2fx%.2f: remover F.Paste e F.Mask (SOP-8 sem EP)" % (pad.GetNumber(), sx, sy))
                if not dry:
                    layers_with(pad, remove=("F_Paste", "F_Mask"))
    elif key == "attr_smd":
        log("  %s: atributo %s -> SMD" % (ref, fp.GetAttributes()))
        if not dry:
            fp.SetAttributes((fp.GetAttributes() & ~pcbnew.FP_THROUGH_HOLE) | pcbnew.FP_SMD)
    elif key == "model_3d":
        cur = [m.m_Filename for m in fp.Models()]
        log("  %s: modelos %s -> %s" % (ref, cur, MODELS[ref]))
        if not dry:
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = MODELS[ref]
            fp.Models().push_back(m)
    elif key == "courtyard_l3":
        add_courtyard(fp, 8.9, 7.6, dry)
    elif key == "r6_note":
        log("  R6: footprint %s - trocar no ESQUEMA para Resistor_SMD:R_0603_1608Metric e atualizar a placa" % fp.GetFPID().GetLibItemName())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--apply", action="store_true", help="grava (faz backup antes). Sem isto = dry-run")
    ap.add_argument("--dry-run", action="store_true", help="padrao")
    ap.add_argument("--refs", default="", help="lista de referencias (filtra)")
    ap.add_argument("--fix", default="", help="lista de chaves de fix (filtra)")
    a = ap.parse_args()
    dry = not a.apply
    refs = set(r.strip() for r in a.refs.split(",") if r.strip())
    keys = [k.strip() for k in a.fix.split(",") if k.strip()] or list(DEFAULT_REFS)

    board = pcbnew.LoadBoard(a.board)

    def find(ref):
        # proxies SWIG ficam invalidos apos fp.Remove(); buscar de novo a cada uso
        for fp in board.GetFootprints():
            if fp.GetReference() == ref:
                return fp
        return None

    log("%s %s" % ("DRY-RUN" if dry else "APPLY", a.board))
    for key in keys:
        for ref in DEFAULT_REFS[key]:
            if refs and ref not in refs:
                continue
            fp = find(ref)
            if fp is None:
                log("  %s: nao encontrado" % ref)
                continue
            log("[%s] %s" % (key, ref))
            apply_fix(key, fp, dry)
    if dry:
        log("dry-run: nada gravado.")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = a.board + ".bak_fpaudit_" + stamp
    shutil.copy2(a.board, bak)
    log("backup: " + bak)
    pcbnew.SaveBoard(a.board, board)
    log("gravado.")


if __name__ == "__main__":
    main()


