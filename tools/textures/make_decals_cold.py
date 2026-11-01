#!/usr/bin/env python3
"""Cold Store (R4) decals, language neutral (PIL + numpy; original artwork). Output: game/assets/textures/decals/ch2x/.

  chest_ring.png        512^2 opaque ring face: six drum symbols (sun moon star triangle circle square) around a dark ring,
                        symbol k at angle 90 - 60 k degrees (k = 0 at the TOP, clockwise). Planar UV from the front:
                        u = x / (2 R) + 0.5, v = y / (2 R) + 0.5 (R = outer radius).
  meridian_stencil.png  512^2 RGBA stencil paint of the Institute mark with ticks (chest lid).
  carriage_tags.png     1280 x 192, five 256 x 192 cells left to right: end tags 1..5 (coloured band + pips, no words).
  can_label_1..4.png    256^2 lid labels of the four film cans (numerals and bands only).
  frost_sign_0..5.png   512^2 RGBA finger-written strokes of the six drum symbols (the signs under the frost).
  frost_tex.png         512^2 RGBA tileable frost crust (alpha = how frosted; for the reveal shader).
  frost_patch.png       512^2 RGBA soft-edged hoar-frost blotch for walls and floor (alpha fades to 0 at the border).
  plan_plate.png        512 x 352 generic plan plate: seven slots, five carriages, two gaps (the variant plan is drawn by code).
  chest_plate.png       512 x 192 blank brass plate on the chest lid (the inscription is drawn by code from tr()).
    python3 tools/textures/make_decals_cold.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
import make_decals_ch2 as D2  # noqa: E402
import make_decals_ch3 as D3  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from make_decals_ch2 import Pen, fbm, blur, smooth, to_img  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2x")
os.makedirs(OUT, exist_ok=True)
KINDS = ["sun", "moon", "star", "triangle", "circle", "square"]


def save(im, name):
    im.save(os.path.join(OUT, name), optimize=True)
    print("  wrote", name, im.size, im.mode)


def chest_ring():
    n = 512
    c = n / 2
    rgb = np.zeros((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rr = np.hypot(xx - c, yy - c) / c
    base = np.array([34, 42, 52], np.float32)
    rgb[:] = base
    grain = fbm(n, n, 10, 3, 3) - 0.5
    rgb += grain[..., None] * 14.0
    # brushed concentric lines + outer chamfer and inner lip
    lines = (np.sin(rr * 260.0) * 0.5 + 0.5) * 5.0
    rgb += lines[..., None]
    rim = smooth(0.94, 1.0, rr) * smooth(1.01, 0.97, rr)
    rgb = rgb * (1 - 0.0) + rim[..., None] * np.array([70, 80, 90], np.float32) * 0.6
    # ticks: 6 big (at the symbols) and 36 small
    pen = Pen(n, n, 4)
    for k in range(36):
        a = math.radians(90 - 10 * k)
        r0, r1 = (0.90, 0.97) if k % 6 == 0 else (0.93, 0.965)
        pen.line([(c + math.cos(a) * r0 * c, c - math.sin(a) * r0 * c), (c + math.cos(a) * r1 * c, c - math.sin(a) * r1 * c)],
                 5 if k % 6 == 0 else 2, 255, caps=False)
    ticks = pen.arr()
    # six symbols
    sym = np.zeros((n, n), np.float32)
    for k, kind in enumerate(KINDS):
        a = math.radians(90 - 60 * k)
        cx, cy = c + math.cos(a) * 0.64 * c, c - math.sin(a) * 0.64 * c
        sym = np.maximum(sym, D3.shape_mask(kind, n, n, cx, cy, 0.30 * c, rot_deg=-60 * k, ss=3))
    cream = np.array([232, 223, 200], np.float32)
    for m in (ticks * 0.75, sym):
        rgb = rgb * (1 - m[..., None]) + cream * m[..., None]
    save(to_img(rgb - 0.5), "chest_ring.png")


def meridian_stencil():
    n = 512
    pen = Pen(n, n, 4)
    mask = np.zeros((n, n), np.float32)
    for shp in S.shapes("mark_ticks", 0.88 * n, bold=1.25):
        p = Pen(n, n, 4)
        for li, lp in enumerate(shp):
            p.poly([(n / 2 + x, n / 2 - y) for x, y in lp], 255 if li == 0 else 0)
        mask = np.maximum(mask, p.arr())
    rng = np.random.default_rng(5)
    wear = fbm(n, n, 14, 9, 3)
    a = mask * (0.80 + 0.2 * (wear > 0.35))
    rgb = np.zeros((n, n, 3), np.float32) + np.array([206, 222, 230], np.float32)
    save(to_img(rgb - 0.5, a), "meridian_stencil.png")


def pips(pen, cx, cy, k, r, gap):
    lay = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
           5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]}[k]
    for dx, dy in lay:
        pen.circle(cx + dx * gap, cy + dy * gap, r, 255)


def carriage_tags():
    cw, ch = 256, 192
    cols = [(190, 58, 44), (52, 104, 176), (226, 178, 52), (70, 142, 96), (226, 226, 214)]
    im = Image.new("RGB", (cw * 5, ch), (200, 196, 180))
    d = ImageDraw.Draw(im)
    for i, col in enumerate(cols):
        x0 = i * cw
        d.rectangle([x0 + 6, 6, x0 + cw - 7, ch - 7], fill=(226, 220, 200), outline=(40, 44, 48), width=5)
        d.rectangle([x0 + 14, 14, x0 + cw - 15, 56], fill=col)
        pen = Pen(cw, ch, 4)
        pips(pen, cw / 2, 124, i + 1, 13, 30)
        m = np.array(Image.fromarray((pen.arr() * 255).astype(np.uint8)))
        layer = Image.fromarray(m).crop((0, 0, cw, ch))
        im.paste(Image.new("RGB", (cw, ch), (36, 38, 42)), (x0, 0), layer)
    save(im, "carriage_tags.png")


def can_labels():
    specs = [((196, 160, 60), "35", 1), ((90, 130, 170), "16", 2), ((168, 70, 52), "8", 3), ((120, 150, 110), "9", 4)]
    for col, num, i in specs:
        n = 256
        im = Image.new("RGB", (n, n), (150, 156, 150))
        d = ImageDraw.Draw(im)
        d.ellipse([6, 6, n - 7, n - 7], fill=(196, 198, 190))
        d.rectangle([40, 78, n - 41, 178], fill=(228, 220, 198), outline=(50, 44, 40), width=4)
        d.rectangle([40, 78, n - 41, 108], fill=col)
        f = D2.font(D2.F_SANS_B, 52)
        w = D2.text_width(num, D2.F_SANS_B, 52)
        d.text(((n - w) / 2, 112), num, font=f, fill=(40, 34, 30))
        for k in range(4):
            d.line([60, 168 + k * 0, n - 60, 168], fill=(80, 70, 60), width=2)
        save(im, f"can_label_{i}.png")


def frost_signs():
    n = 512
    for k, kind in enumerate(KINDS):
        pen = Pen(n, n, 4)
        D3.shape_outline(pen, kind, n / 2, n / 2, 0.56 * n, 26, 255, jitter=1.6, seed=k + 11)
        m = pen.arr()
        m = np.maximum(blur(m, 1.4) * 1.0, m * 0.9)
        # finger streak texture: break the stroke up a little
        br = fbm(n, n, 6, 20 + k, 3)
        a = np.clip(m * (0.78 + 0.5 * (br - 0.5)), 0, 1)
        rgb = np.zeros((n, n, 3), np.float32) + np.array([226, 240, 248], np.float32)
        save(to_img(rgb - 0.5, a), f"frost_sign_{k}.png")


def frost_tex():
    n = 512
    # tileable: crystalline blotches from periodic noise, plus fine needles
    a = D2.pnoise(n, n, 40, 1) * 0.55 + D2.pnoise(n, n, 14, 2) * 0.3 + D2.pnoise(n, n, 5, 3) * 0.15
    a = smooth(0.30, 0.62, a)
    fine = D2.pnoise(n, n, 2.5, 4, stretch=(1.0, 3.0))
    a = np.clip(a * (0.82 + 0.35 * fine), 0, 1)
    rgb = np.zeros((n, n, 3), np.float32) + np.array([232, 244, 250], np.float32)
    rgb -= (1 - a)[..., None] * 18.0
    save(to_img(rgb - 0.5, a), "frost_tex.png")


def frost_patch():
    n = 512
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - n / 2, yy - n / 2) / (n / 2)
    warp = fbm(n, n, 60, 31, 3) - 0.5
    core = D2.smooth(1.0, 0.25, r + warp * 0.55)
    crystals = D2.pnoise(n, n, 6, 32, stretch=(1.0, 2.4)) * 0.5 + D2.pnoise(n, n, 18, 33) * 0.5
    a = np.clip(core * (0.55 + 0.9 * crystals), 0, 1) ** 0.9
    a = np.clip(a * 1.15, 0, 0.92)
    rgb = np.zeros((n, n, 3), np.float32) + np.array([236, 246, 252], np.float32)
    rgb -= (1 - core)[..., None] * 14.0
    save(to_img(rgb - 0.5, a), "frost_patch.png")


def plan_plate():
    w, h = 512, 352
    im = Image.new("RGB", (w, h), (36, 42, 46))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 7, h - 7], outline=(190, 205, 212), width=4)
    x0, pitch = 40, 62
    for i in range(7):
        d.rectangle([x0 + i * pitch + 2, 150, x0 + (i + 1) * pitch - 2, 290], outline=(90, 104, 112), width=2)
    for i, slot in enumerate((0, 1, 3, 4, 6)):
        d.rectangle([x0 + slot * pitch + 8, 160, x0 + (slot + 1) * pitch - 8, 280], fill=(150, 168, 178), outline=(220, 232, 238), width=2)
        pen = Pen(w, h, 3)
        pips(pen, x0 + slot * pitch + pitch / 2, 220, i + 1, 4, 11)
        layer = Image.fromarray((pen.arr() * 255).astype(np.uint8))
        im.paste(Image.new("RGB", (w, h), (30, 34, 38)), (0, 0), layer)
    d.line([40, 316, 40 + 7 * pitch, 316], fill=(190, 205, 212), width=3)
    save(im, "plan_plate.png")


def chest_plate():
    w, h = 512, 192
    im = Image.new("RGB", (w, h), (150, 124, 78))
    d = ImageDraw.Draw(im)
    d.rectangle([5, 5, w - 6, h - 6], outline=(104, 84, 50), width=5)
    for x in (18, w - 18):
        for y in (18, h - 18):
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(96, 78, 46))
    save(im, "chest_plate.png")


if __name__ == "__main__":
    chest_ring()
    meridian_stencil()
    carriage_tags()
    can_labels()
    frost_signs()
    frost_tex()
    frost_patch()
    plan_plate()
    chest_plate()
    print("ok")
