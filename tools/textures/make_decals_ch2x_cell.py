#!/usr/bin/env python3
"""Chapter 2 expansion decals for the Night Cell and the hall plan (language neutral, PIL only; placeholders the code may replace).

  cell_drawing.png   a child's wax-crayon drawing pinned over the cot: a house, a sun, two stick figures holding hands
  floor_plan.png     the building plan on the hall wall: three stacked floor strips (-1 / 0 / +1), rooms as tiles
  sheet_print.png    generic acetate print: 11 x 11 cell grid, a few opaque cells, a reference arrow (RGBA, the variant mask is drawn by code)
  table_mask.png     the light-table window: 11 columns x 7 rows cell grid with the four corner marks (RGBA; lit cells are drawn by code)

Output: game/assets/textures/decals/ch2x/.   python3 tools/textures/make_decals_ch2x_cell.py
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "game", "assets", "textures", "decals", "ch2x")
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(1952)


def crayon(d, pts, col, w=5, jitter=1.6):
    for a, b in zip(pts, pts[1:]):
        for k in range(2):
            o = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in (a, b)]
            d.line(o, fill=col, width=w - k)


def drawing():
    W, H = 384, 512
    im = Image.new("RGB", (W, H), (233, 222, 196))
    px = im.load()
    for y in range(H):                                  # faint paper grain and a fold line
        for x in range(W):
            n = rnd.randint(-5, 5)
            r, g, b = px[x, y]
            px[x, y] = (r + n, g + n, b + n)
    d = ImageDraw.Draw(im)
    d.line([(0, H // 2), (W, H // 2)], fill=(214, 202, 176), width=2)
    # sun
    d.ellipse([268, 36, 340, 108], outline=(226, 152, 36), width=6)
    for k in range(10):
        import math
        a = k * math.pi / 5
        crayon(d, [(304 + math.cos(a) * 46, 72 + math.sin(a) * 46), (304 + math.cos(a) * 66, 72 + math.sin(a) * 66)], (226, 152, 36), 4)
    # house
    crayon(d, [(70, 300), (70, 210), (160, 210), (160, 300), (70, 300)], (150, 56, 44), 6)
    crayon(d, [(56, 214), (115, 150), (176, 214), (56, 214)], (150, 56, 44), 6)
    crayon(d, [(100, 300), (100, 252), (130, 252), (130, 300)], (96, 64, 40), 5)
    crayon(d, [(82, 226), (82, 246), (100, 246), (100, 226), (82, 226)], (60, 100, 150), 4)
    # ground
    crayon(d, [(10, 304), (120, 308), (250, 302), (374, 306)], (70, 130, 60), 6)
    # two figures holding hands: tall and small
    for fx, fh, col in ((228, 94, (60, 70, 120)), (290, 66, (170, 60, 90))):
        top = 306 - fh - 30
        d.ellipse([fx - 15, top - 15, fx + 15, top + 15], outline=col, width=5)
        crayon(d, [(fx, top + 15), (fx, 296 - 26)], col, 5)
        crayon(d, [(fx, 296 - 26), (fx - 17, 304)], col, 5)
        crayon(d, [(fx, 296 - 26), (fx + 17, 304)], col, 5)
    crayon(d, [(228, top_y := 244), (259, 251), (290, 262)], (60, 70, 120), 5)
    # tree and a bird
    crayon(d, [(336, 304), (336, 240)], (96, 64, 40), 7)
    d.ellipse([306, 180, 368, 246], outline=(70, 130, 60), width=6)
    crayon(d, [(40, 120), (56, 108), (70, 120), (84, 108), (98, 120)], (60, 60, 60), 3)
    # a lower half: tall lamp-post and many tiny stars (a night under the building)
    for _ in range(26):
        x, y = rnd.randint(20, W - 20), rnd.randint(350, H - 24)
        crayon(d, [(x - 6, y), (x + 6, y)], (226, 190, 60), 3, 0.8)
        crayon(d, [(x, y - 6), (x, y + 6)], (226, 190, 60), 3, 0.8)
    d.ellipse([160, 380, 224, 444], outline=(226, 190, 60), width=6)
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(OUT, "cell_drawing.png"))


def floor_plan():
    W, H = 640, 400
    im = Image.new("RGB", (W, H), (34, 40, 38))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, W - 7, H - 7], outline=(196, 170, 108), width=4)
    ink = (210, 196, 150)
    strips = [(24, 96), (146, 218), (268, 340)]
    # floor +1: gallery, plate, office; floor 0: hall (big) + booth; floor -1: pump, cell, cold
    rows = [[(40, 190), (200, 330), (340, 600)], [(40, 440), (450, 600)], [(40, 250), (260, 380), (390, 600)]]
    for (y0, y1), row in zip(strips, rows):
        for (x0, x1) in row:
            d.rectangle([x0, y0, x1, y1], outline=ink, width=3)
            d.line([(x0 + 6, y0 + 6), (x0 + 22, y0 + 6)], fill=ink, width=3)
    for (y0, y1) in strips:
        d.text((14, (y0 + y1) // 2 - 6), "", fill=ink)
    for (x, y) in ((190, 60), (220, 182), (445, 182), (255, 304), (385, 304)):   # doors
        d.rectangle([x - 5, y - 8, x + 5, y + 8], fill=(34, 40, 38), outline=ink, width=2)
    for x in (120, 520):                                                          # stair / lift marks
        d.line([(x, 96), (x, 146)], fill=ink, width=3)
        d.line([(x, 218), (x, 268)], fill=ink, width=3)
        d.polygon([(x - 8, 120), (x + 8, 120), (x, 108)], fill=ink)
        d.polygon([(x - 8, 244), (x + 8, 244), (x, 232)], fill=ink)
    d.ellipse([566, 22, 612, 68], outline=ink, width=3)      # compass
    d.polygon([(589, 28), (583, 50), (595, 50)], fill=ink)
    im.save(os.path.join(OUT, "floor_plan.png"))


def sheet_print():
    N = 11
    S = 440
    c = S // N
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(N):
        for j in range(N):
            if rnd.random() < 0.34 and (i, j) != (0, 0):      # the clipped corner cell is never opaque
                d.rectangle([i * c + 2, j * c + 2, (i + 1) * c - 3, (j + 1) * c - 3], fill=(26, 20, 16, 235))
    for k in range(N + 1):
        d.line([(k * c, 0), (k * c, S)], fill=(60, 50, 40, 70), width=1)
        d.line([(0, k * c), (S, k * c)], fill=(60, 50, 40, 70), width=1)
    d.polygon([(S // 2 - 14, 22), (S // 2 + 14, 22), (S // 2, 4)], fill=(190, 40, 30, 255))   # reference arrow (top edge)
    im.save(os.path.join(OUT, "sheet_print.png"))


def table_mask():
    W, H = 440, 280                                     # 11 columns x 7 rows of 40 px (two 5 x 7 digits side by side)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(12):
        d.line([(k * 40, 0), (k * 40, H)], fill=(40, 34, 28, 120), width=1)
    for k in range(8):
        d.line([(0, k * 40), (W, k * 40)], fill=(40, 34, 28, 120), width=1)
    for (x, y, sx, sy) in ((0, 0, 1, 1), (W - 1, 0, -1, 1), (0, H - 1, 1, -1), (W - 1, H - 1, -1, -1)):
        d.line([(x, y), (x + sx * 36, y)], fill=(20, 16, 12, 255), width=5)
        d.line([(x, y), (x, y + sy * 36)], fill=(20, 16, 12, 255), width=5)
    im.save(os.path.join(OUT, "table_mask.png"))


drawing()
floor_plan()
sheet_print()
table_mask()
print("cell decals written to", OUT)
