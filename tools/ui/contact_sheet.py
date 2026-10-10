#!/usr/bin/env python3
"""A labelled contact sheet from screenshots (QA previews).
    python3 tools/ui/contact_sheet.py out.jpg --cols 4 --width 640 a.png:"0.00 s" b.png:"0.34 s" ...
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--cols", type=int, default=4)
ap.add_argument("--width", type=int, default=640, help="width of one cell")
ap.add_argument("--quality", type=int, default=88)
ap.add_argument("items", nargs="+", help="image[:label]")
a = ap.parse_args()

cells = []
for it in a.items:
    path, _, label = it.partition(":")
    im = Image.open(path).convert("RGB")
    h = round(im.height * a.width / im.width)
    cells.append((im.resize((a.width, h), Image.LANCZOS), label))
h = max(c[0].height for c in cells)
rows = (len(cells) + a.cols - 1) // a.cols
gap = 6
sheet = Image.new("RGB", (a.cols * a.width + (a.cols + 1) * gap, rows * h + (rows + 1) * gap), (14, 14, 16))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except OSError:
    font = ImageFont.load_default()
d = ImageDraw.Draw(sheet)
for i, (im, label) in enumerate(cells):
    x = gap + (i % a.cols) * (a.width + gap)
    y = gap + (i // a.cols) * (h + gap)
    sheet.paste(im, (x, y))
    if label:
        tw = d.textlength(label, font=font)
        d.rectangle([x + 8, y + 8, x + 16 + tw, y + 36], fill=(0, 0, 0))
        d.text((x + 12, y + 10), label, fill=(240, 214, 150), font=font)
sheet.save(a.out, quality=a.quality)
print("wrote", a.out, sheet.size)
