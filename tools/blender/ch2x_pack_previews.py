#!/usr/bin/env python3
"""Convert the QA PNG renders of the Chapter 2 expansion into small JPG previews under docs/previews/ch2_expansion/.

    python3 tools/blender/ch2x_pack_previews.py <png dir> [prefix filter]
"""
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "previews", "ch2_expansion")
os.makedirs(OUT, exist_ok=True)
src = sys.argv[1]
flt = sys.argv[2] if len(sys.argv) > 2 else ""
for f in sorted(os.listdir(src)):
    if f.endswith(".png") and f.startswith(flt):
        im = Image.open(os.path.join(src, f)).convert("RGB")
        if im.width > 900:
            im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
        out = os.path.join(OUT, f[:-4] + ".jpg")
        im.save(out, quality=82, optimize=True)
        print("wrote", os.path.relpath(out, ROOT), os.path.getsize(out) // 1024, "KB")
