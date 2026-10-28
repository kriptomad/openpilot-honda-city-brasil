#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ds_fetch.py - helper: download a datasheet PDF into ./datasheets and print text pages
matching a regex (default: land pattern / footprint / recommended pad keywords).

Usage: python ds_fetch.py <name> <url> [regex] [--all]
"""
import sys, os, re, io
import urllib.request
import pypdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
DSD = os.path.join(HERE, "datasheets")
os.makedirs(DSD, exist_ok=True)

name, url = sys.argv[1], sys.argv[2]
rx = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else r"(?i)land pattern|footprint|recommended pad|solder pad|pcb pad|mounting pad|suggested pad|pad layout|recommended layout|package outline|stencil"
show_all = "--all" in sys.argv
path = os.path.join(DSD, name + ".pdf")
if not os.path.exists(path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) datasheet-audit"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    print("downloaded", len(data), "bytes")
rd = pypdf.PdfReader(path)
print("pages:", len(rd.pages))
for i, p in enumerate(rd.pages):
    try:
        t = p.extract_text() or ""
    except Exception as e:
        t = f"<extract error {e}>"
    if show_all or re.search(rx, t):
        print(f"\n===== page {i+1} =====")
        print(t[:6000])
