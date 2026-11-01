#!/usr/bin/env python3
"""Chapter 2 expansion, upper floor (R5-R7) decals. Language neutral, PIL only, original art.
Placeholder images: the scene code swaps per-variant images (strip symbols, cabinet label, print) onto the same slots.
Output: game/assets/textures/decals/ch2x/
  roll_tags.png      3 x 2 atlas of six staff portrait tags (cream card, simple head-and-shoulders icons)   M_Decal_RollTags
  cabinet_label.png  brass-framed label card with one stencil symbol (placeholder: the variant symbol is swapped by code)  M_Decal_CabinetLabel
  negatives.png      one 35 mm style negative strip: sprockets, four inverted frames, an edge symbol at the right end  M_Decal_Negatives
  print_proj.png     placeholder of the enlarger's projected image (soft grey portrait with a pencilled number)   M_Decal_Prints
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2x")
os.makedirs(OUT, exist_ok=True)
INK = (43, 33, 24)
CREAM = (232, 223, 200)


def head(d, cx, cy, s, kind, fg, bg):
    """Head-and-shoulders icon in a box of size s centred at cx, cy. kind 0..5 picks the accessory."""
    d.pieslice([cx - s * 0.46, cy + s * 0.14, cx + s * 0.46, cy + s * 0.96], 180, 360, fill=fg)      # shoulders
    d.rectangle([cx - s * 0.08, cy + s * 0.02, cx + s * 0.08, cy + s * 0.2], fill=fg)                 # neck
    d.ellipse([cx - s * 0.2, cy - s * 0.34, cx + s * 0.2, cy + s * 0.1], fill=fg)                      # face
    if kind == 0:     # flat cap
        d.pieslice([cx - s * 0.24, cy - s * 0.40, cx + s * 0.24, cy - s * 0.04], 180, 360, fill=fg)
        d.rectangle([cx - s * 0.30, cy - s * 0.22, cx + s * 0.30, cy - s * 0.17], fill=fg)
        d.rectangle([cx - s * 0.20, cy - s * 0.215, cx + s * 0.20, cy - s * 0.19], fill=bg)
    elif kind == 1:   # round glasses
        for sx in (-1, 1):
            d.ellipse([cx + sx * s * 0.085 - s * 0.06, cy - s * 0.14, cx + sx * s * 0.085 + s * 0.06, cy - s * 0.02], outline=bg, width=max(2, int(s * 0.025)))
        d.line([cx - s * 0.025, cy - s * 0.08, cx + s * 0.025, cy - s * 0.08], fill=bg, width=max(2, int(s * 0.02)))
    elif kind == 2:   # hair bun
        d.ellipse([cx - s * 0.09, cy - s * 0.50, cx + s * 0.09, cy - s * 0.32], fill=fg)
        d.arc([cx - s * 0.2, cy - s * 0.34, cx + s * 0.2, cy + s * 0.04], 190, 350, fill=bg, width=max(2, int(s * 0.02)))
    elif kind == 3:   # moustache
        d.pieslice([cx - s * 0.12, cy - s * 0.07, cx + s * 0.0, cy + s * 0.02], 0, 180, fill=bg)
        d.pieslice([cx + s * 0.0, cy - s * 0.07, cx + s * 0.12, cy + s * 0.02], 0, 180, fill=bg)
    elif kind == 4:   # bow tie
        d.polygon([(cx, cy + s * 0.28), (cx - s * 0.13, cy + s * 0.2), (cx - s * 0.13, cy + s * 0.36)], fill=bg)
        d.polygon([(cx, cy + s * 0.28), (cx + s * 0.13, cy + s * 0.2), (cx + s * 0.13, cy + s * 0.36)], fill=bg)
    else:             # head scarf with a knot
        d.pieslice([cx - s * 0.24, cy - s * 0.40, cx + s * 0.24, cy - s * 0.02], 180, 360, fill=fg)
        d.polygon([(cx + s * 0.18, cy - s * 0.2), (cx + s * 0.34, cy - s * 0.3), (cx + s * 0.30, cy - s * 0.1)], fill=fg)
        d.arc([cx - s * 0.2, cy - s * 0.34, cx + s * 0.2, cy + s * 0.04], 200, 340, fill=bg, width=max(2, int(s * 0.02)))


def roll_tags():
    cw, ch = 256, 192
    im = Image.new("RGB", (cw * 3, ch * 2), CREAM)
    d = ImageDraw.Draw(im)
    for k in range(6):
        ox, oy = (k % 3) * cw, (k // 3) * ch
        d.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], fill=CREAM)
        d.rounded_rectangle([ox + 8, oy + 8, ox + cw - 9, oy + ch - 9], radius=22, outline=INK, width=4)
        d.rounded_rectangle([ox + 22, oy + 40, ox + cw - 23, oy + ch - 22], radius=14, fill=(206, 190, 150))
        head(d, ox + cw // 2, oy + 118, 120, k, INK, (206, 190, 150))
        d.ellipse([ox + cw // 2 - 12, oy + 14, ox + cw // 2 + 12, oy + 38], fill=(80, 70, 55))   # hang hole
    im.save(os.path.join(OUT, "roll_tags.png"))


def cabinet_label():
    im = Image.new("RGB", (256, 192), (176, 141, 87))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 249, 185], outline=(227, 194, 122), width=4)
    d.rectangle([22, 22, 233, 169], fill=CREAM)
    cx, cy, r = 128, 96, 46
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK)
    d.ellipse([cx - r + 22, cy - r - 6, cx + r + 22, cy + r - 6], fill=CREAM)
    for i in range(3):
        d.ellipse([cx + 40 + i * 0, cy - 30 + i * 28, cx + 52, cy - 18 + i * 28], fill=INK)
    im.save(os.path.join(OUT, "cabinet_label.png"))


def negatives():
    W, H = 1024, 160
    im = Image.new("RGB", (W, H), (42, 30, 24))
    d = ImageDraw.Draw(im)
    for k in range(34):                                 # sprocket holes along both edges
        x = 14 + k * 30
        for y in (8, H - 20):
            d.rounded_rectangle([x, y, x + 16, y + 12], radius=3, fill=(14, 10, 8))
    for f in range(4):                                  # four inverted (negative) frames
        x0 = 20 + f * 232
        face = Image.new("RGB", (200, H - 56), (70, 60, 52))                   # a negative: dark field, light figure
        fd = ImageDraw.Draw(face)
        head(fd, 100, 70, 90, f, (190, 182, 166), (70, 60, 52))
        im.paste(face, (x0, 28))
    d.rectangle([956, 28, 1010, H - 28], fill=(120, 112, 100))                             # edge symbol window (a negative too)
    d.ellipse([966, 56, 1000, 90], fill=(28, 22, 18))
    d.ellipse([978, 50, 1010, 84], fill=(120, 112, 100))
    im.save(os.path.join(OUT, "negatives.png"))


def print_proj():
    im = Image.new("RGB", (320, 240), (190, 184, 170))
    d = ImageDraw.Draw(im)
    head(d, 160, 110, 170, 1, (70, 62, 54), (190, 184, 170))
    d.text((24, 200), "0000", fill=(60, 60, 70))
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im.save(os.path.join(OUT, "print_proj.png"))


roll_tags()
cabinet_label()
negatives()
print_proj()
print("ch2x upper decals written to", OUT)
