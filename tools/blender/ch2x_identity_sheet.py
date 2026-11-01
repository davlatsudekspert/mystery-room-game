#!/usr/bin/env python3
"""Side-by-side identity sheet of the Chapter 2 expansion rooms (docs/CHAPTER2_EXPANSION.md 3b: "every room looks and feels different").

Takes the main review render of each available room from docs/previews/ch2_expansion/ and lays them out in a 3 x 2 grid with a small
label and a palette strip (the five most common colours of that render) so the dominant colours can be compared at a glance.

    python3 tools/blender/ch2x_identity_sheet.py
Output: docs/previews/ch2_expansion/room_identity_sheet.jpg
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR = os.path.join(ROOT, "docs", "previews", "ch2_expansion")
ROOMS = [("R2 Pump Room", ["prev_pump_pump", "prev_pump"]), ("R3 Night Cell", ["cell_room_overview", "prev_cell_cell"]),
         ("R4 Cold Store", ["cold_room_overview", "cold_room", "prev_cold_cold"]), ("R5 Reading Gallery", ["prev_gallery_gallery", "gallery_room"]),
         ("R6 Plate Room", ["prev_plate_plate", "plate_room"]), ("R7 Director's Office", ["prev_office_office", "office_room"])]
CW, CH = 600, 400


def find(cands):
    for c in cands:
        p = os.path.join(DIR, c + ".jpg")
        if os.path.exists(p):
            return p
    for c in cands:
        g = sorted(glob.glob(os.path.join(DIR, c + "*.jpg")))
        if g:
            return g[0]
    return None


def palette(im, n=5):
    small = im.resize((80, 54)).quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = small.getpalette()
    counts = sorted(small.getcolors(), reverse=True)
    return [tuple(pal[i * 3:i * 3 + 3]) for _, i in counts[:n]]


def main():
    items = [(lab, find(c)) for lab, c in ROOMS]
    items = [(lab, p) for lab, p in items if p]
    cols = 3
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * CW + (cols + 1) * 8, rows * (CH + 40) + (rows + 1) * 8), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    except OSError:
        font = ImageFont.load_default()
    for i, (lab, p) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = 8 + c * (CW + 8), 8 + r * (CH + 48)
        im = Image.open(p).convert("RGB")
        im = im.resize((CW, round(im.height * CW / im.width)))
        if im.height > CH:
            top = (im.height - CH) // 2
            im = im.crop((0, top, CW, top + CH))
        sheet.paste(im, (x, y))
        d.rectangle([x, y + CH, x + CW, y + CH + 38], fill=(30, 30, 33))
        d.text((x + 8, y + CH + 8), lab, fill=(232, 223, 200), font=font)
        for k, col in enumerate(palette(im)):
            d.rectangle([x + CW - 40 * (5 - k) - 8, y + CH + 8, x + CW - 40 * (4 - k) - 12, y + CH + 30], fill=col, outline=(80, 80, 80))
    out = os.path.join(DIR, "room_identity_sheet.jpg")
    sheet.save(out, quality=86, optimize=True)
    print("wrote", os.path.relpath(out, ROOT), len(items), "rooms:", [lab for lab, _ in items])


main()
