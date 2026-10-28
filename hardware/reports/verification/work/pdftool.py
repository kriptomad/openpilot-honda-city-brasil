"""Read-only helper: extract text from a PDF (optionally around keywords) and
render selected pages to PNG in ds/png/. Usage:
  python pdftool.py text <pdf> [keyword ...]
  python pdftool.py render <pdf> <page1-based> [zoom]
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import fitz  # pymupdf

mode, pdf = sys.argv[1], sys.argv[2]
doc = fitz.open(pdf)
if mode == "text":
    kws = [k.lower() for k in sys.argv[3:]]
    for i, page in enumerate(doc):
        t = page.get_text()
        if not kws:
            print(f"===== page {i+1}\n{t}")
            continue
        tl = t.lower()
        if any(k in tl for k in kws):
            print(f"===== page {i+1}\n{t}")
elif mode == "render":
    pno = int(sys.argv[3]) - 1
    zoom = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
    os.makedirs("ds/png", exist_ok=True)
    pix = doc[pno].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    out = f"ds/png/{os.path.basename(pdf)[:-4]}_p{pno+1}.png"
    pix.save(out)
    print(out, pix.width, pix.height)
