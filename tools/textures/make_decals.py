#!/usr/bin/env python3
"""Generate puzzle-critical and story decal textures (original artwork, procedural).

Outputs to game/assets/textures/decals/ and game/assets/ui/glyphs/.
All puzzle data here MUST match docs/PUZZLE_DESIGN.md and game/src/rooms/lab7/lab7_logic.gd.

    python3 tools/textures/make_decals.py          # everything
    python3 tools/textures/make_decals.py panel    # only Panel 7's plates, one per wiring in PANEL_POOL
"""
from __future__ import annotations

import ast
import itertools
import math
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals")
GLYPH_OUT = os.path.join(ROOT, "game", "assets", "ui", "glyphs")
os.makedirs(OUT, exist_ok=True)
os.makedirs(GLYPH_OUT, exist_ok=True)

FONT_DIR = "/usr/share/fonts/truetype"
F_SANS_B = os.path.join(FONT_DIR, "dejavu", "DejaVuSansCondensed-Bold.ttf")
F_SERIF_B = os.path.join(FONT_DIR, "dejavu", "DejaVuSerif-Bold.ttf")
F_SERIF = os.path.join(FONT_DIR, "dejavu", "DejaVuSerif.ttf")
F_MONO = os.path.join(FONT_DIR, "dejavu", "DejaVuSansMono.ttf")
F_SANS = os.path.join(FONT_DIR, "dejavu", "DejaVuSans.ttf")

# ---- puzzle data (single source of truth mirrored in lab7_logic.gd) -------------------
GLYPH_DOTS = {
    "sun": 7, "crescent": 3, "wave": 2, "spiral": 9, "delta": 4,
    "eye": 0, "cross": 5, "diamond": 1, "fork": 8, "hourglass": 6,
}
POSTER_ORDER = ["crescent", "eye", "spiral", "diamond", "hourglass",
                "wave", "fork", "sun", "delta", "cross"]
VIALS = {"crimson": "1.84", "cobalt": "1.26", "green": "0.79"}
# radio: dial value 0..100 -> needle u = 0.06 + 0.88 * value / 100 ; band label -> dial value
RADIO_BANDS = {"60": 5, "49": 20, "41": 36, "31": 55, "25": 72, "19": 86, "16": 96}
RADIO_MHZ = {5: 3, 6: 12, 7: 30, 9: 50, 11: 66, 13: 80, 15: 90, 17: 97}


def read_panel_pool() -> list:
    """Panel 7's wirings (switch -> lamps it toggles; lamps LOCK, LIGHT, ARRAY, VENT), read from the single source of
    truth, PANEL_POOL in lab7_logic.gd. Entry 0 is the canonical wiring."""
    src = open(os.path.join(ROOT, "game", "src", "rooms", "lab7", "lab7_logic.gd"), encoding="utf-8").read()
    m = re.search(r"const PANEL_POOL: Array = (\[.*?\n\])", src, re.S)
    assert m, "PANEL_POOL not found in lab7_logic.gd"
    return ast.literal_eval(m.group(1))


rng = np.random.default_rng(7)
random.seed(7)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(os.path.join(FONT_DIR, "dejavu", "DejaVuSans.ttf"), size)


def noise(h: int, w: int, scale: float, octaves: int = 4, seed: int = 0) -> np.ndarray:
    """Smooth value noise in 0..1 built from upsampled random grids."""
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int(h / scale * (2 ** o)))
        gw = max(2, int(w / scale * (2 ** o)))
        grid = r.random((gh, gw)).astype(np.float32)
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img, np.float32) / 255.0)
        total += amp
        amp *= 0.5
    return acc / total


def aged_paper(w: int, h: int, base=(217, 203, 176), seed: int = 1, stains: int = 6,
               vignette: float = 0.35) -> Image.Image:
    n = noise(h, w, 180, 5, seed)
    fine = noise(h, w, 6, 2, seed + 11)
    arr = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        arr[..., c] = base[c] * (0.86 + 0.18 * n + 0.06 * (fine - 0.5))
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    arr *= (1 - vignette * np.clip(d - 0.55, 0, 1))[..., None]
    r = np.random.default_rng(seed + 3)
    for _ in range(stains):  # coffee/foxing stains
        cx, cy = r.integers(0, w), r.integers(0, h)
        rad = r.integers(min(w, h) // 30, min(w, h) // 7)
        m = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad, 0, 1) ** 1.5
        ring = np.clip(1 - abs(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - rad * 0.85) / (rad * 0.08), 0, 1)
        arr *= (1 - 0.12 * m - 0.10 * ring)[..., None] * np.array([1.0, 0.97, 0.9])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def ink_rough(img: Image.Image, amount: float = 0.25, seed: int = 5) -> Image.Image:
    """Break up solid ink/chalk strokes with noise (expects RGBA layer)."""
    a = np.asarray(img).astype(np.float32)
    n = noise(img.height, img.width, 3, 2, seed)
    a[..., 3] *= np.clip(1 - amount + amount * 1.6 * n, 0, 1)
    return Image.fromarray(a.astype(np.uint8))


# ---- glyphs ------------------------------------------------------------------------------
def draw_glyph(d: ImageDraw.ImageDraw, gid: str, cx: float, cy: float, s: float, col, lw: int) -> None:
    """Draw glyph `gid` centred at (cx, cy) inside a box of half-size s."""
    def circ(r, width=lw, fill=None):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=width, fill=fill)

    if gid == "sun":
        circ(s * 0.8)
        circ(s * 0.14, width=0, fill=col)
    elif gid == "crescent":
        pts = []
        for i in range(0, 181):
            a = math.radians(-90 + i * 1.0 * 180 / 180)
            pts.append((cx + s * 0.8 * math.cos(a), cy + s * 0.8 * math.sin(a)))
        for i in range(180, -1, -1):
            a = math.radians(-90 + i)
            pts.append((cx + s * 0.25 + s * 0.45 * math.cos(a) - s * 0.25, cy + s * 0.8 * math.sin(a)))
        d.line(pts + [pts[0]], fill=col, width=lw, joint="curve")
    elif gid == "wave":
        for k in (-1, 0, 1):
            pts = [(cx - s * 0.8 + t * s * 1.6 / 60, cy + k * s * 0.42 + s * 0.16 * math.sin(t / 60 * 4 * math.pi))
                   for t in range(61)]
            d.line(pts, fill=col, width=lw, joint="curve")
    elif gid == "spiral":
        pts = []
        for t in range(0, 361 * 3, 4):
            a = math.radians(t)
            r = s * 0.8 * t / (360 * 3)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.line(pts, fill=col, width=lw, joint="curve")
    elif gid == "delta":
        p = [(cx, cy - s * 0.82), (cx + s * 0.82, cy + s * 0.62), (cx - s * 0.82, cy + s * 0.62)]
        d.line(p + [p[0]], fill=col, width=lw, joint="curve")
    elif gid == "eye":
        top = [(cx - s * 0.85 + t * s * 1.7 / 40, cy - s * 0.45 * math.sin(math.pi * t / 40)) for t in range(41)]
        bot = [(cx - s * 0.85 + t * s * 1.7 / 40, cy + s * 0.45 * math.sin(math.pi * t / 40)) for t in range(41)]
        d.line(top, fill=col, width=lw, joint="curve")
        d.line(bot, fill=col, width=lw, joint="curve")
        circ(s * 0.22, width=0, fill=col)
    elif gid == "cross":
        circ(s * 0.8)
        d.line([(cx - s * 0.8, cy), (cx + s * 0.8, cy)], fill=col, width=lw)
        d.line([(cx, cy - s * 0.8), (cx, cy + s * 0.8)], fill=col, width=lw)
    elif gid == "diamond":
        p = [(cx, cy - s * 0.85), (cx + s * 0.55, cy), (cx, cy + s * 0.85), (cx - s * 0.55, cy)]
        d.line(p + [p[0]], fill=col, width=lw, joint="curve")
    elif gid == "fork":
        d.line([(cx, cy - s * 0.1), (cx, cy + s * 0.85)], fill=col, width=lw)
        d.arc([cx - s * 0.6, cy - s * 0.9, cx + s * 0.6, cy + s * 0.2], 0, 180, fill=col, width=lw)
        d.line([(cx, cy - s * 0.85), (cx, cy - s * 0.1)], fill=col, width=lw)
        d.line([(cx - s * 0.6, cy - s * 0.85), (cx - s * 0.6, cy - s * 0.35)], fill=col, width=lw)
        d.line([(cx + s * 0.6, cy - s * 0.85), (cx + s * 0.6, cy - s * 0.35)], fill=col, width=lw)
    elif gid == "hourglass":
        p = [(cx - s * 0.6, cy - s * 0.8), (cx + s * 0.6, cy - s * 0.8), (cx - s * 0.6, cy + s * 0.8),
             (cx + s * 0.6, cy + s * 0.8)]
        d.line(p + [p[0]], fill=col, width=lw, joint="curve")
    else:
        raise ValueError(gid)


def make_glyph_icons() -> None:
    for gid in GLYPH_DOTS:
        size = 256
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_glyph(d, gid, size / 2, size / 2, size * 0.42, (255, 255, 255, 255), 14)
        im.save(os.path.join(GLYPH_OUT, f"{gid}.png"))


def draw_dots(d: ImageDraw.ImageDraw, n: int, x0: float, y0: float, size: float, col) -> None:
    """Dice-like pip layout of n (0..9) in a square starting at (x0, y0)."""
    layouts = {
        0: [], 1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)],
        4: [(0, 0), (2, 0), (0, 2), (2, 2)], 5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
        6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)],
        7: [(0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (2, 2)],
        8: [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)],
        9: [(i, j) for i in range(3) for j in range(3)],
    }
    r = size * 0.11
    for (i, j) in layouts[n]:
        cx = x0 + size * (0.17 + 0.33 * i)
        cy = y0 + size * (0.17 + 0.33 * j)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)


# ---- individual decals ---------------------------------------------------------------------
def brass_strip(w: int, h: int, seed: int = 2) -> np.ndarray:
    n = noise(h, w, 40, 4, seed)
    streak = noise(h, w * 4, 2, 1, seed + 1)[:, ::4]
    base = np.array([176, 141, 87], np.float32)
    shade = 0.75 + 0.25 * n + 0.08 * (streak - 0.5)
    yy = np.linspace(-1, 1, h)[:, None]
    shade *= (1 - 0.25 * yy ** 2)  # cylinder shading hint
    return base[None, None, :] * shade[..., None]


def drawer_digits() -> None:
    """1024x128 strip, digit k centred at u = (k + 0.5) / 10 (see docs/ROOM_LAYOUT.md)."""
    w, h = 1024, 128
    arr = brass_strip(w, h)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(F_SERIF_B, 88)
    for k in range(10):
        cx = (k + 0.5) * w / 10
        d.text((cx + 2, h / 2 + 2), str(k), font=f, anchor="mm", fill=(255, 230, 170, 120))  # bevel highlight
        d.text((cx, h / 2), str(k), font=f, anchor="mm", fill=(38, 26, 14, 235))
        d.line([(k * w / 10, 6), (k * w / 10, h - 6)], fill=(70, 50, 25, 160), width=3)  # knurl separators
    img = Image.alpha_composite(img, layer).convert("RGB")
    img.save(os.path.join(OUT, "drawer_digits.png"))


def clock_face() -> None:
    """512x224 flip-clock front: two flap windows showing 03 and 17 (the moment of Silence)."""
    w, h = 512, 224
    n = noise(h, w, 30, 3, 9)
    arr = np.stack([30 + 14 * n, 24 + 10 * n, 20 + 8 * n], -1)
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    f = font(F_SANS_B, 118)
    for i, txt in enumerate(["03", "17"]):
        x0 = 28 + i * 236
        for j, ch in enumerate(txt):
            cx0 = x0 + j * 110
            d.rounded_rectangle([cx0, 30, cx0 + 102, 194], radius=10, fill=(44, 44, 46, 255))
            d.text((cx0 + 51, 112), ch, font=f, anchor="mm", fill=(236, 229, 210, 255))
            d.line([(cx0, 112), (cx0 + 102, 112)], fill=(14, 14, 15, 255), width=4)
    # glass reflection hint
    refl = Image.new("L", (w, h), 0)
    ImageDraw.Draw(refl).polygon([(0, 0), (190, 0), (90, h), (0, h)], fill=26)
    img = Image.composite(Image.new("RGBA", (w, h), (255, 255, 255, 255)), img, refl)
    img.convert("RGB").save(os.path.join(OUT, "clock_face.png"))


def poster() -> None:
    """Strand's Table of Resonances, 1024x1448, 2 columns x 5 rows of glyph + pips."""
    w, h = 1024, 1448
    img = aged_paper(w, h, base=(214, 200, 170), seed=21, stains=4, vignette=0.22).convert("RGBA")
    ink = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ink)
    col = (43, 33, 24, 255)
    # header emblem: crystal lens with a meridian line
    d.ellipse([w / 2 - 70, 70, w / 2 + 70, 210], outline=col, width=6)
    d.ellipse([w / 2 - 45, 95, w / 2 + 45, 185], outline=col, width=3)
    d.line([(w / 2, 58), (w / 2, 222)], fill=col, width=4)
    d.text((w / 2, 268), "TABULA  RESONANTIARUM", font=font(F_SERIF_B, 52), anchor="mm", fill=col)
    d.text((w / 2, 322), "E. STRAND  ·  MCMLXXI", font=font(F_SERIF, 30), anchor="mm", fill=col)
    d.line([(120, 360), (w - 120, 360)], fill=col, width=3)
    d.line([(120, 368), (w - 120, 368)], fill=col, width=1)
    cell_w, cell_h = 380, 170
    for idx, gid in enumerate(POSTER_ORDER):
        c, r = idx % 2, idx // 2
        x0 = 112 + c * (cell_w + 40)
        y0 = 405 + r * (cell_h + 16)
        d.rounded_rectangle([x0, y0, x0 + cell_w, y0 + cell_h], radius=12, outline=col, width=3)
        d.line([(x0 + cell_w * 0.48, y0 + 18), (x0 + cell_w * 0.48, y0 + cell_h - 18)], fill=col, width=2)
        draw_glyph(d, gid, x0 + cell_w * 0.24, y0 + cell_h / 2, cell_h * 0.32, col, 9)
        draw_dots(d, GLYPH_DOTS[gid], x0 + cell_w * 0.58, y0 + 25, cell_h - 50, col)
    d.text((w / 2, h - 58), "LUX  MEMINIT", font=font(F_SERIF_B, 34), anchor="mm", fill=col)
    ink = ink_rough(ink, 0.22, 4)
    img = Image.alpha_composite(img, ink)
    img.convert("RGB").save(os.path.join(OUT, "poster_resonance.jpg"), quality=92)


def chalkboard() -> None:
    """1024x640 slate with Strand's chalk notes (language-neutral: maths, sketches, Latin)."""
    w, h = 1024, 640
    n = noise(h, w, 120, 5, 31)
    smear = noise(h, w, 40, 3, 32)
    arr = np.stack([28 + 16 * n + 14 * smear, 34 + 16 * n + 14 * smear, 31 + 15 * n + 13 * smear], -1)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    chalk = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(chalk)
    c = (226, 226, 214, 235)
    fbig, fmid = font(F_SERIF, 54), font(F_SERIF, 40)
    d.text((60, 50), "E = h·ν", font=fbig, fill=c)
    d.text((60, 130), "λ = c / ν", font=fbig, fill=c)
    # Strand's beacon band (radio puzzle): antenna doodle + circled wavelength
    ax, ay = 470, 470
    d.line([(ax, ay + 70), (ax, ay - 40)], fill=c, width=5)
    d.line([(ax - 30, ay + 70), (ax, ay - 10), (ax + 30, ay + 70)], fill=c, width=4)
    for k in range(1, 4):
        d.arc([ax - 22 * k, ay - 40 - 22 * k, ax + 22 * k, ay - 40 + 22 * k], 200, 340, fill=c, width=3)
    d.text((ax + 60, ay + 20), "λ = 41 m", font=fbig, anchor="lm", fill=c)
    d.ellipse([ax + 40, ay - 25, ax + 320, ay + 65], outline=c, width=3)
    d.text((60, 215), "Δt → 0 ?", font=fmid, fill=c)
    d.text((60, 280), "ψ(t₀) ≡ ψ(t)", font=fmid, fill=c)
    # crystal sketch with light rays
    cx, cy = 640, 250
    hexpts = [(cx + 80 * math.cos(math.radians(a)), cy + 38 * math.sin(math.radians(a))) for a in range(0, 361, 60)]
    d.line(hexpts, fill=c, width=4)
    d.line([(p[0], p[1] + 170) for p in hexpts[1:4]], fill=c, width=4)
    for p in hexpts[1:4]:
        d.line([p, (p[0], p[1] + 170)], fill=c, width=4)
    for k in range(5):
        d.line([(cx - 330, cy + 40 + k * 22), (cx - 80, cy + 85)], fill=c, width=2)
    d.line([(cx + 80, cy + 85), (cx + 330, cy + 70)], fill=c, width=5)
    d.text((cx + 250, cy + 100), "?", font=fbig, fill=c)
    # the moment, circled
    d.text((880, 590), "03:17", font=font(F_SERIF, 30), anchor="mm", fill=c)
    d.text((60, 560), "LUX MEMINIT", font=font(F_SERIF_B, 46), fill=c)
    chalk = ink_rough(chalk.filter(ImageFilter.GaussianBlur(0.6)), 0.45, 33)
    img = Image.alpha_composite(img, chalk)
    img.convert("RGB").save(os.path.join(OUT, "chalkboard.jpg"), quality=90)


PANEL_ICONS = ["lock", "light", "array", "vent"]  # the lamps' order on Panel 7 (LAMP_TARGET: on, on, on, off)


def draw_panel_icon(d: ImageDraw.ImageDraw, j: int, ix: float, iy: float, s: float, col) -> None:
    """Panel 7's lamp icon j (0 padlock = LOCK, 1 bulb = LIGHT, 2 crystal = ARRAY, 3 fan = VENT) centred at
    (ix, iy) in a box of half-size s. The same art is printed on the plate and shown in Leyla's notebook."""
    k = s / 24.0  # the icons were drawn at half-size 24
    lw = max(2, round(5 * k))
    if j == 0:  # padlock: body and shackle
        d.rounded_rectangle([ix - 18 * k, iy - 4 * k, ix + 18 * k, iy + 22 * k], radius=4 * k, fill=col)
        d.arc([ix - 13 * k, iy - 24 * k, ix + 13 * k, iy + 6 * k], 180, 360, fill=col, width=max(2, round(6 * k)))
    elif j == 1:  # bulb: glass and cap
        d.ellipse([ix - 16 * k, iy - 22 * k, ix + 16 * k, iy + 10 * k], outline=col, width=lw)
        d.rectangle([ix - 8 * k, iy + 10 * k, ix + 8 * k, iy + 22 * k], fill=col)
    elif j == 2:  # crystal: a facetted diamond
        pts = [(ix, iy - 24 * k), (ix + 16 * k, iy - 6 * k), (ix, iy + 24 * k), (ix - 16 * k, iy - 6 * k)]
        d.line(pts + [pts[0]], fill=col, width=lw, joint="curve")
        for q in pts:  # round the corners (the apex shows a notch otherwise)
            d.ellipse([q[0] - lw / 2, q[1] - lw / 2, q[0] + lw / 2, q[1] + lw / 2], fill=col)
        d.line([pts[1], pts[3]], fill=col, width=max(2, round(3 * k)))
    else:  # fan: a ring with three blades
        d.ellipse([ix - 22 * k, iy - 22 * k, ix + 22 * k, iy + 22 * k], outline=col, width=max(2, round(4 * k)))
        for a in (0, 120, 240):
            ra = math.radians(a)
            d.ellipse([ix + 11 * k * math.cos(ra) - 9 * k, iy + 11 * k * math.sin(ra) - 9 * k,
                       ix + 11 * k * math.cos(ra) + 9 * k, iy + 11 * k * math.sin(ra) + 9 * k], fill=col)


def make_panel_icons() -> None:
    """Panel 7's four lamp icons as white 256 px icons (tinted by the UI), for the notebook's page about the panel."""
    for j, name in enumerate(PANEL_ICONS):
        size = 256
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_panel_icon(d, j, size / 2, size / 2, size * 0.40, (255, 255, 255, 255))
        im.save(os.path.join(GLYPH_OUT, f"panel_{name}.png"))


# ---- Panel 7 back plate: the copper traces of every wiring in PANEL_POOL ---------------------------------------
# Plate pixels (900 x 1200 = 0.60 x 0.80 m, 1500 px per metre). The switch and lamp positions are fixed by the model
# (tools/blender/models/panel7.py); only the traces between them change per wiring.
PANEL_SW_X = [120.0, 285.0, 450.0, 615.0, 780.0]
PANEL_LAMP_X = [157.5, 352.5, 547.5, 742.5]
PANEL_ROW_Y = [595.0, 525.0, 455.0, 385.0, 315.0]  # the five rows, lowest first
PANEL_RISER_Y = 640.0                              # just above the switch plates
PANEL_LAMP_Y = 203.0                               # just below the lamp bezels
PANEL_GAUGE_BOTTOM = 422.0                         # the voltmeter (x 28..122, y 328..422) sits left of switch I's riser
PANEL_COPPER = (176, 98, 56, 255)
PANEL_WIRE, PANEL_DOT, PANEL_HOP = 9, 13, 18       # trace width, junction dot radius, hop radius (px)
HOP_CLEAR, DOT_CLEAR = 50.0, 40.0                  # least gap between two hops / a hop and a dot on one row


def panel_hops(m: list, level: list) -> list:
    """Where traces cross without connecting: (row of switch k, x, kind) for a wiring m and level[i] = the row
    (0 = lowest) switch i's trace runs along. A horizontal run hops over every vertical one it passes."""
    span = []
    for i in range(5):
        xs = [PANEL_SW_X[i]] + [PANEL_LAMP_X[j] for j in range(4) if m[i][j]]
        span.append((min(xs), max(xs)))
    out = []
    for k in range(5):
        a, b = span[k]
        for i in range(5):
            if i != k and level[i] > level[k] and a < PANEL_SW_X[i] < b:
                out.append((k, PANEL_SW_X[i]))
        for j in range(4):
            low = min(level[i] for i in range(5) if m[i][j])
            if level[k] >= low and not m[k][j] and a < PANEL_LAMP_X[j] < b:
                out.append((k, PANEL_LAMP_X[j]))
    return out


def panel_layout(m: list) -> list:
    """The row each switch's trace runs along: fewest crossings, no two events crowding on a row, switch I
    clear of the voltmeter; ties go to the order closest to I..V bottom to top."""
    best = None
    for level in itertools.permutations(range(5)):
        if PANEL_ROW_Y[level[0]] < PANEL_GAUGE_BOTTOM + 30:
            continue
        hops = panel_hops(m, list(level))
        crowd = 0
        for k in range(5):
            hx = sorted(x for kk, x in hops if kk == k)
            dots = [PANEL_LAMP_X[j] for j in range(4) if m[k][j]] + [PANEL_SW_X[k]]
            crowd += sum(1 for a, b in zip(hx, hx[1:]) if b - a < HOP_CLEAR)
            crowd += sum(1 for x in hx for dx in dots if abs(x - dx) < DOT_CLEAR)
        inversions = sum(1 for i in range(5) for k in range(i + 1, 5) if level[i] > level[k])
        score = (len(hops) + 10 * crowd, inversions)
        if best is None or score < best[0]:
            best = (score, list(level))
    assert best is not None and best[0][0] < 10, "no clean layout for %s" % m
    return best[1]


def panel_traces(m: list) -> Image.Image:
    """The copper traces of wiring m as an anti-aliased RGBA layer: one run up from each switch to its row, the row
    along to the lamps it feeds, a column up to each lamp. A dot marks every place two traces connect; where traces
    only cross, the horizontal one hops over the vertical one."""
    W, H, SS = 900, 1200, 3
    level = panel_layout(m)
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = PANEL_WIRE * SS

    def seg(x0, y0, x1, y1):
        d.line([(x0 * SS, y0 * SS), (x1 * SS, y1 * SS)], fill=PANEL_COPPER, width=w)
        for x, y in ((x0, y0), (x1, y1)):
            d.ellipse([x * SS - w / 2, y * SS - w / 2, x * SS + w / 2, y * SS + w / 2], fill=PANEL_COPPER)

    def dot(x, y):
        r = PANEL_DOT * SS
        d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=PANEL_COPPER)

    hops = panel_hops(m, level)
    for i in range(5):
        y = PANEL_ROW_Y[level[i]]
        conn = [j for j in range(4) if m[i][j]]
        xs = [PANEL_SW_X[i]] + [PANEL_LAMP_X[j] for j in conn]
        seg(PANEL_SW_X[i], PANEL_RISER_Y, PANEL_SW_X[i], y)
        # the row, cut open around every hop and bridged by a half circle
        cuts = sorted(x for k, x in hops if k == i)
        x = min(xs)
        for c in cuts:
            seg(x, y, c - PANEL_HOP, y)
            r = (PANEL_HOP + PANEL_WIRE / 2) * SS
            d.arc([c * SS - r, y * SS - r, c * SS + r, y * SS + r], 180, 360, fill=PANEL_COPPER, width=w)
            x = c + PANEL_HOP
        seg(x, y, max(xs), y)
        dot(PANEL_SW_X[i], y)
        for j in conn:
            dot(PANEL_LAMP_X[j], y)
    for j in range(4):
        low = max(PANEL_ROW_Y[level[i]] for i in range(5) if m[i][j])
        seg(PANEL_LAMP_X[j], PANEL_LAMP_Y, PANEL_LAMP_X[j], low)
    # lamp columns and risers were laid down after the rows: put the dots back on top
    for i in range(5):
        y = PANEL_ROW_Y[level[i]]
        dot(PANEL_SW_X[i], y)
        for j in range(4):
            if m[i][j]:
                dot(PANEL_LAMP_X[j], y)
    return layer.resize((W, H), Image.LANCZOS)


def panel_diagram(n: int = 0) -> Image.Image:
    """Panel 7 back plate (0.60 x 0.80 m -> 900x1200 px) drawn for wiring n of PANEL_POOL. Coordinates in plate
    metres, origin centre."""
    W, H = 900, 1200
    sx = W / 0.60
    sy = H / 0.80

    def P(x, y):
        return (W / 2 + x * sx, H / 2 - y * sy)

    n_ = noise(H, W, 80, 4, 41)
    arr = np.stack([224 * (0.9 + 0.1 * n_), 215 * (0.9 + 0.1 * n_), 192 * (0.9 + 0.1 * n_)], -1)
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    dark = (40, 34, 28, 255)
    lamp_x = [-0.195, -0.065, 0.065, 0.195]
    lamp_y = 0.30
    sw_x = [-0.22, -0.11, 0.0, 0.11, 0.22]
    sw_y = -0.06
    # the copper traces of this game's wiring
    img = Image.alpha_composite(img, panel_traces(read_panel_pool()[n]))
    d = ImageDraw.Draw(img)
    # lamp bezels + icons (padlock, bulb, crystal, fan) in the band between the bezels and the plate's top edge:
    # half-size 41 px = 2.7 cm, so they read from the close-up on a phone (they were 1.6 cm)
    for j, x in enumerate(lamp_x):
        q = P(x, lamp_y)
        d.ellipse([q[0] - 40, q[1] - 40, q[0] + 40, q[1] + 40], outline=dark, width=6)
        ix, iy = P(x, lamp_y + 0.068)
        draw_panel_icon(d, j, ix, iy, 41, dark)
    # switch plates + roman numerals
    f = font(F_SERIF_B, 40)
    for i, x in enumerate(sw_x):
        q = P(x, sw_y)
        d.rounded_rectangle([q[0] - 34, q[1] - 52, q[0] + 34, q[1] + 52], radius=8, outline=dark, width=5)
        d.text(P(x, sw_y - 0.085), ["I", "II", "III", "IV", "V"][i], font=f, anchor="mm", fill=dark)
    # main breaker plate with 0 / 1
    q = P(0.0, -0.27)
    d.rounded_rectangle([q[0] - 70, q[1] - 110, q[0] + 70, q[1] + 110], radius=10, outline=dark, width=6)
    d.text((q[0] + 100, q[1] - 85), "1", font=font(F_SANS_B, 48), anchor="mm", fill=dark)
    d.text((q[0] + 100, q[1] + 85), "0", font=font(F_SANS_B, 48), anchor="mm", fill=dark)
    # panel number badge + lightning symbol
    q = P(0.22, -0.30)
    d.ellipse([q[0] - 46, q[1] - 46, q[0] + 46, q[1] + 46], outline=dark, width=6)
    d.text(q, "7", font=font(F_SERIF_B, 64), anchor="mm", fill=dark)
    q = P(-0.22, -0.30)
    d.polygon([(q[0] + 6, q[1] - 50), (q[0] - 22, q[1] + 6), (q[0] - 2, q[1] + 6), (q[0] - 10, q[1] + 50),
               (q[0] + 22, q[1] - 8), (q[0] + 2, q[1] - 8)], fill=(181, 82, 59, 255))
    # wear
    grime = noise(H, W, 25, 3, 43)
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= (0.85 + 0.15 * grime)[..., None]
    return Image.fromarray(a.astype(np.uint8)).convert("RGB")


def panel_diagrams() -> None:
    """panel_diagram_<n>.jpg for every wiring in PANEL_POOL; panel_diagram.jpg (the model's baked default) is entry 0."""
    for n in range(len(read_panel_pool())):
        panel_diagram(n).save(os.path.join(OUT, "panel_diagram_%d.jpg" % n), quality=92)
    panel_diagram(0).save(os.path.join(OUT, "panel_diagram.jpg"), quality=92)


def vial_labels() -> None:
    for name, rho in VIALS.items():
        w, h = 256, 128
        img = aged_paper(w, h, base=(226, 214, 186), seed=50 + len(name), stains=1, vignette=0.2).convert("RGBA")
        d = ImageDraw.Draw(img)
        d.rectangle([6, 6, w - 7, h - 7], outline=(60, 44, 30, 255), width=3)
        d.text((w / 2, 54), f"ρ {rho}", font=font(F_MONO, 50), anchor="mm", fill=(36, 28, 22, 255))
        d.text((w / 2, 100), "g/cm³", font=font(F_MONO, 24), anchor="mm", fill=(60, 48, 36, 255))
        img.convert("RGB").save(os.path.join(OUT, f"vial_label_{name}.png"))


def childs_drawing() -> None:
    w, h = 512, 680
    img = aged_paper(w, h, base=(232, 224, 205), seed=61, stains=2).convert("RGBA")
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # sun
    d.ellipse([360, 50, 460, 150], outline=(222, 160, 40, 255), width=9)
    for k in range(10):
        a = 2 * math.pi * k / 10
        d.line([(410 + 62 * math.cos(a), 100 + 62 * math.sin(a)), (410 + 90 * math.cos(a), 100 + 90 * math.sin(a))],
               fill=(222, 160, 40, 255), width=7)
    # institute building with dome
    d.rectangle([60, 330, 330, 560], outline=(120, 70, 50, 255), width=8)
    d.arc([140, 240, 250, 420], 180, 360, fill=(120, 70, 50, 255), width=8)
    for i in range(3):
        d.rectangle([90 + i * 80, 380, 140 + i * 80, 430], outline=(50, 90, 160, 255), width=6)
    # two figures holding hands (mother in white coat, child)
    d.ellipse([380, 380, 430, 430], outline=(40, 40, 40, 255), width=6)
    d.polygon([(405, 432), (365, 560), (445, 560)], outline=(90, 90, 90, 255), width=6)
    d.ellipse([440, 450, 476, 486], outline=(40, 40, 40, 255), width=6)
    d.line([(458, 486), (458, 545)], fill=(200, 60, 60, 255), width=7)
    d.line([(430, 480), (450, 500)], fill=(40, 40, 40, 255), width=5)
    d.line([(20, 600), (500, 590)], fill=(70, 140, 60, 255), width=10)
    lay = ink_rough(lay, 0.5, 62)
    Image.alpha_composite(img, lay).convert("RGB").save(os.path.join(OUT, "childs_drawing.jpg"), quality=90)


def window_night() -> None:
    """Moonlit mountain valley seen through the barred window (emissive backdrop)."""
    w, h = 1024, 1024
    yy = np.linspace(0, 1, h)[:, None]
    top = np.array([8, 14, 28], np.float32)
    bot = np.array([34, 52, 72], np.float32)
    sky = top + (bot - top) * (yy ** 1.6)[..., None]
    arr = np.repeat(sky, w, axis=1)
    clouds = noise(h, w, 220, 5, 71)
    arr += (clouds[..., None] - 0.5) * np.array([18, 22, 26]) * (1 - yy)[..., None]
    r = np.random.default_rng(72)
    for _ in range(260):
        x, y = r.integers(0, w), r.integers(0, int(h * 0.55))
        b = r.uniform(80, 220)
        arr[y, x] = np.minimum(255, arr[y, x] + b)
    # moon + halo
    mx, my = int(w * 0.68), int(h * 0.22)
    xx, yy2 = np.mgrid[0:h, 0:w]
    dist = np.sqrt((yy2 - mx) ** 2 + (xx - my) ** 2)
    arr += (np.exp(-dist / 140.0) * 70)[..., None] * np.array([0.8, 0.9, 1.0])
    moon = (dist < 46).astype(np.float32)
    arr = arr * (1 - moon[..., None]) + moon[..., None] * np.array([228, 232, 222])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for layer, (base_y, amp, col) in enumerate([(0.62, 0.16, (18, 26, 38)), (0.72, 0.12, (11, 16, 24))]):
        pts = [(0, h)]
        rr = np.random.default_rng(80 + layer)
        y = base_y * h
        for x in range(0, w + 16, 16):
            y += rr.normal(0, amp * 60)
            y = min(max(y, (base_y - amp) * h), (base_y + amp) * h)
            pts.append((x, y))
        pts.append((w, h))
        d.polygon(pts, fill=col)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(os.path.join(OUT, "window_night.jpg"), quality=90)


def uv_desk_mark() -> None:
    """Fluorescent ink: circle + arrow pointing at the rosette (white on transparent, shader tints)."""
    w = h = 512
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for t in range(0, 380, 5):
        a = math.radians(t)
        rr = 120 + 8 * math.sin(a * 3)
        pts.append((330 + rr * math.cos(a), 256 + rr * math.sin(a)))
    d.line(pts, fill=(255, 255, 255, 255), width=12, joint="curve")
    d.line([(40, 420), (200, 330)], fill=(255, 255, 255, 255), width=12)
    d.polygon([(215, 322), (170, 320), (196, 362)], fill=(255, 255, 255, 255))
    ink_rough(im, 0.35, 90).save(os.path.join(OUT, "uv_desk_mark.png"))


def notebook_paper() -> None:
    w, h = 1024, 1400
    img = aged_paper(w, h, base=(226, 214, 188), seed=101, stains=3, vignette=0.25).convert("RGBA")
    d = ImageDraw.Draw(img)
    for y in range(170, h - 60, 56):
        d.line([(60, y), (w - 50, y)], fill=(120, 140, 160, 70), width=2)
    d.line([(120, 0), (120, h)], fill=(170, 80, 70, 70), width=2)
    img.convert("RGB").save(os.path.join(OUT, "notebook_page.jpg"), quality=90)


def radio_dial() -> None:
    """1024x256 glass dial: wavelength bands (m) on top, MHz below. Chalkboard says λ = 41 m."""
    w, h = 1024, 256
    n = noise(h, w, 60, 3, 120)
    arr = np.stack([214 * (0.92 + 0.08 * n), 198 * (0.92 + 0.08 * n), 160 * (0.92 + 0.08 * n)], -1)
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    dark = (44, 30, 20, 255)
    red = (150, 40, 30, 255)

    def ux(v):
        return (0.06 + 0.88 * v / 100.0) * w

    d.line([(ux(0), 128), (ux(100), 128)], fill=dark, width=3)
    for v in range(0, 101, 2):
        d.line([(ux(v), 118 if v % 10 else 108), (ux(v), 138 if v % 10 else 148)], fill=dark, width=2)
    fb = font(F_SERIF_B, 40)
    for label, v in RADIO_BANDS.items():
        d.rounded_rectangle([ux(v) - 36, 30, ux(v) + 36, 86], radius=8, outline=red, width=3)
        d.text((ux(v), 58), label, font=fb, anchor="mm", fill=red)
    d.text((ux(-3.5), 58), "m", font=font(F_SERIF, 34), anchor="mm", fill=red)
    fm = font(F_SANS, 30)
    for mhz, v in RADIO_MHZ.items():
        d.text((ux(v), 190), str(mhz), font=fm, anchor="mm", fill=dark)
    d.text((ux(-3.5), 190), "MHz", font=font(F_SANS, 20), anchor="mm", fill=dark)
    a = np.asarray(img).astype(np.float32)
    yy = np.linspace(-1, 1, h)[:, None]
    a[..., :3] *= (1 - 0.18 * yy ** 2)[..., None]
    Image.fromarray(a.astype(np.uint8)).convert("RGB").save(os.path.join(OUT, "radio_dial.jpg"), quality=92)


def wall_emblem() -> None:
    """Shadow-lock target painted on the secret-room wall: Institute emblem (ring + meridian)."""
    w = h = 512
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (232, 224, 200, 255)
    d.ellipse([96, 96, 416, 416], outline=col, width=10)
    d.line([(256, 40), (256, 472)], fill=col, width=10)
    for k in range(12):
        a = 2 * math.pi * k / 12
        d.line([(256 + 176 * math.cos(a), 256 + 176 * math.sin(a)), (256 + 196 * math.cos(a), 256 + 196 * math.sin(a))],
               fill=col, width=6)
    ink_rough(im, 0.3, 130).save(os.path.join(OUT, "wall_emblem.png"))


def staff_photos(count: int = 8) -> None:
    """Sepia studio-portrait silhouettes for Leyla's evidence wall (stylized, no real people)."""
    for k in range(count):
        r = np.random.default_rng(200 + k)
        w, h = 256, 320
        yy, xx = np.mgrid[0:h, 0:w]
        bg = 120 + 60 * np.exp(-(((xx - w / 2) / 110) ** 2 + ((yy - h * 0.45) / 140) ** 2))
        img = Image.fromarray(np.clip(np.stack([bg * 1.0, bg * 0.86, bg * 0.66], -1), 0, 255).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(img)
        tone = (int(r.integers(40, 70)), int(r.integers(30, 50)), int(r.integers(20, 35)), 255)
        cx = w / 2 + r.integers(-10, 10)
        d.ellipse([cx - 95, 215, cx + 95, 380], fill=tone)  # shoulders
        d.rectangle([cx - 22, 170, cx + 22, 230], fill=tone)  # neck
        hw, hh = r.integers(46, 56), r.integers(60, 70)
        d.ellipse([cx - hw, 150 - hh, cx + hw, 150 + hh], fill=(tone[0] + 60, tone[1] + 48, tone[2] + 34, 255))
        hair = (tone[0] - 15, tone[1] - 12, tone[2] - 8, 255)
        style = k % 4
        if style == 0:
            d.ellipse([cx - hw - 4, 150 - hh - 8, cx + hw + 4, 150 - hh / 3], fill=hair)
        elif style == 1:
            d.ellipse([cx - hw - 6, 150 - hh - 10, cx + hw + 6, 160], fill=hair)
            d.ellipse([cx - hw + 8, 150 - hh / 2, cx + hw - 8, 150 + hh], fill=(tone[0] + 60, tone[1] + 48, tone[2] + 34, 255))
        elif style == 2:
            d.ellipse([cx - 30, 150 - hh - 40, cx + 30, 150 - hh + 10], fill=hair)
            d.ellipse([cx - hw - 2, 150 - hh - 6, cx + hw + 2, 150 - hh / 2], fill=hair)
        if k % 3 == 1:  # glasses
            d.ellipse([cx - 34, 140, cx - 8, 160], outline=(30, 24, 18, 255), width=3)
            d.ellipse([cx + 8, 140, cx + 34, 160], outline=(30, 24, 18, 255), width=3)
        img = img.filter(ImageFilter.GaussianBlur(1.6))
        a = np.asarray(img).astype(np.float32)
        a[..., :3] += r.normal(0, 9, (h, w, 1))
        vign = 1 - 0.5 * np.clip(np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) - 0.6, 0, 1)
        a[..., :3] *= vign[..., None]
        out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGB")
        framed = Image.new("RGB", (w + 24, h + 24), (232, 224, 204))
        framed.paste(out, (12, 12))
        framed.save(os.path.join(OUT, f"photo_{k}.jpg"), quality=88)


if __name__ == "__main__":
    if sys.argv[1:] == ["panel"]:  # only Panel 7's plates (after editing PANEL_POOL)
        panel_diagrams()
        sys.exit(0)
    staff_photos()
    radio_dial()
    wall_emblem()
    make_glyph_icons()
    drawer_digits()
    clock_face()
    poster()
    chalkboard()
    panel_diagrams()
    make_panel_icons()
    vial_labels()
    childs_drawing()
    window_night()
    uv_desk_mark()
    notebook_paper()
    print("decals written to", OUT)
