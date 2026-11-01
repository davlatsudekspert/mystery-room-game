#!/usr/bin/env python3
"""Pack the QA PNGs of the upper-floor rooms and props into docs/previews/ch2_expansion/ with the prefixes gallery_, plate_, office_.

    python3 tools/blender/ch2x_upper_pack.py <png dir>      (the dir that holds ch2x/prev_*.png and ch2x/<prop>*.png)
Room shots prev_<room>_<shot>.png -> <room>_<shot>.jpg (the main shot is also copied to prev_<room>_<room>.jpg for the identity sheet);
prop renders <prop>[_tag].png -> <room prefix>_<prop>[_tag].jpg.
"""
import os
import shutil
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "previews", "ch2_expansion")
PROPS = {"gallery": ["roll_call_board", "pa_horn", "balcony_rail", "stair_wedge"], "plate": ["enlarger", "negative_strip"],
         "office": ["strand_cabinet", "tea_set", "pass_key", "projector_lamp"]}
os.makedirs(OUT, exist_ok=True)
src = os.path.join(sys.argv[1], "ch2x")


def save(png, name):
    im = Image.open(os.path.join(src, png)).convert("RGB")
    if im.width > 900:
        im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name + ".jpg"), quality=84, optimize=True)
    print("wrote", name + ".jpg")


for f in sorted(os.listdir(src)):
    if not f.endswith(".png"):
        continue
    stem = f[:-4]
    if stem.startswith("prev_"):
        room, shot = stem[5:].split("_", 1)
        if room in PROPS:
            clash = any(shot == pr or shot.startswith(pr + "_") for pr in PROPS[room])
            save(f, f"{room}_{shot}_view" if clash else f"{room}_{shot}")
            if room == shot:
                save(f, f"prev_{room}_{room}")
        continue
    for room, props in PROPS.items():
        if any(stem == p or stem.startswith(p + "_") for p in props):
            save(f, f"{room}_{stem}")
