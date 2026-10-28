#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ds_render.py - render selected PDF pages (or a clipped region) to PNG so drawings can be inspected.
Usage: python ds_render.py <name> <page[,page...]> [zoom] [x0,y0,x1,y1 as fractions]
"""
import sys, os
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1]
pages = [int(p) for p in sys.argv[2].split(",")]
zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
clip = [float(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
doc = pymupdf.open(os.path.join(HERE, "datasheets", name + ".pdf"))
outdir = os.path.join(HERE, "datasheets", "png")
os.makedirs(outdir, exist_ok=True)
for p in pages:
    page = doc[p - 1]
    r = page.rect
    c = None
    if clip:
        c = pymupdf.Rect(r.x0 + clip[0] * r.width, r.y0 + clip[1] * r.height, r.x0 + clip[2] * r.width, r.y0 + clip[3] * r.height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=c)
    out = os.path.join(outdir, f"{name}_p{p}{'_clip' if clip else ''}.png")
    pix.save(out)
    print(out, pix.width, pix.height)
