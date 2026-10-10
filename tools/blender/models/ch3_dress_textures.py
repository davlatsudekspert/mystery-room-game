"""Chapter 3 set-dressing textures (original, procedural; no third-party image is used).

  python3 tools/blender/models/ch3_dress_textures.py

Writes game/assets/textures/dress/ch3_grime.png, one 2048 x 1024 RGBA atlas that every Chapter 3 dressing model
shares through ONE alpha-blended material (M_Dress_Grime), and the .tres materials of the dressing
(M_Dress_Grime, M_Dress_Plaster_Dark, M_Dress_Stone_Dark, M_Dress_Wool).

Atlas cells (x, y, w, h in pixels; the tools/blender/models/ch3_dress_*.py scripts read CELLS below):
  grime / damp / rust / soot / crack / tile damage      alpha masks of one flat colour each (no colour halos)
  warning stencils                                       language-neutral pictograms (hazard bolt, flame, arrow,
                                                         no entry, stripe band); no letters anywhere
  maps / charts / notebook page                          sepia paper with contour lines, routes and scribbles
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "dress")
MAT = os.path.join(ROOT, "game", "assets", "materials")
W, H = 2048, 1024
PAD = 6

# name: (x, y, w, h)
CELLS = {
    "grime_top": (0, 0, 512, 256),
    "damp_a": (512, 0, 256, 256),
    "damp_b": (768, 0, 256, 256),
    "streaks_a": (1024, 0, 256, 256),
    "tiles_a": (1280, 0, 256, 256),
    "tiles_b": (1536, 0, 256, 256),
    "crack_a": (1792, 0, 256, 256),
    "baseboard": (0, 256, 512, 256),
    "rust_a": (512, 256, 256, 256),
    "rust_b": (768, 256, 256, 256),
    "corner": (1024, 256, 256, 256),
    "soot": (1280, 256, 256, 256),
    "crack_b": (1536, 256, 256, 256),
    "streaks_b": (1792, 256, 256, 256),
    "st_bolt": (0, 512, 256, 256),
    "st_flame": (256, 512, 256, 256),
    "st_arrow": (512, 512, 256, 256),
    "st_noentry": (768, 512, 256, 256),
    "st_stripes": (1024, 512, 512, 128),
    "st_keepclear": (1536, 512, 256, 256),
    "st_pipe": (1792, 512, 256, 128),
    "st_valve": (1792, 640, 256, 128),
    "map_a": (0, 768, 512, 256),
    "map_b": (512, 768, 256, 256),
    "map_c": (768, 768, 256, 256),
    "page": (1024, 768, 256, 256),
    "chart": (1280, 768, 256, 256),
    "tags": (1536, 768, 256, 256),
}

GRIME = np.array([34, 25, 16], np.float32)
DAMP = np.array([32, 31, 24], np.float32)
RUST = np.array([128, 62, 26], np.float32)
SOOT = np.array([14, 11, 9], np.float32)


# ====================================================================== noise helpers
def noise(h, w, cells_y, cells_x, seed):
    r = np.random.RandomState(seed)
    a = r.rand(max(2, cells_y), max(2, cells_x)).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def fbm(h, w, base, octs, seed):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octs):
        out += amp * noise(h, w, int(base * 2 ** o * h / max(h, w)) + 2, int(base * 2 ** o * w / max(h, w)) + 2, seed + 31 * o)
        tot += amp
        amp *= 0.5
    return out / tot


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0


def edge_fade(h, w, fx=0.12, fy=0.0):
    x = np.linspace(0, 1, w, dtype=np.float32)
    fx_ = smoothstep(0, fx, x) * smoothstep(0, fx, 1 - x)
    out = np.tile(fx_, (h, 1))
    if fy > 0:
        y = np.linspace(0, 1, h, dtype=np.float32)
        out = out * np.tile((smoothstep(0, fy, y) * smoothstep(0, fy, 1 - y))[:, None], (1, w))
    return out


def drips(h, w, n, seed, wmin=2, wmax=7, lmin=0.2, lmax=0.9, y0=0.0, soft=1.4):
    r = np.random.RandomState(seed)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x = r.randint(int(w * 0.06), int(w * 0.94))
        ww = r.randint(wmin, wmax)
        ln = int(h * r.uniform(lmin, lmax))
        a = int(r.uniform(90, 230))
        yy = int(h * y0)
        d.rounded_rectangle((x, yy, x + ww, yy + ln), radius=ww // 2, fill=a)
        d.ellipse((x - 1, yy + ln - ww, x + ww + 1, yy + ln + ww // 2), fill=a)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(soft)), np.float32) / 255.0


# ====================================================================== grime masks (alpha only; colour is flat)
def m_grime_top(w, h, seed):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    n = fbm(h, w, 6, 4, seed)
    base = np.clip(1.15 - y * 1.55 + (n - 0.5) * 0.9, 0, 1)
    a = np.maximum(base * 0.85, drips(h, w, 26, seed + 5, lmin=0.3, lmax=0.95) * 0.7)
    return np.clip(a * edge_fade(h, w, 0.10), 0, 0.92)


def m_baseboard(w, h, seed):
    y = np.linspace(1, 0, h, dtype=np.float32)[:, None]
    n = fbm(h, w, 7, 4, seed)
    a = np.clip(1.05 - y * 1.7 + (n - 0.5) * 1.0, 0, 1) ** 1.2
    splash = noise(h, w, 4, 40, seed + 9)
    a = np.clip(a * (0.65 + 0.7 * splash), 0, 1)
    return np.clip(a * edge_fade(h, w, 0.08), 0, 0.9)


def m_damp(w, h, seed):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.42
    d = np.sqrt(((xx - cx) / (w * 0.5)) ** 2 + ((yy - cy) / (h * 0.5)) ** 2)
    n = fbm(h, w, 5, 5, seed)
    d = d + (n - 0.5) * 0.9
    body = 1.0 - smoothstep(0.42, 0.78, d)
    rim = smoothstep(0.50, 0.68, d) * (1.0 - smoothstep(0.68, 0.80, d))
    a = body * 0.46 + rim * 0.34
    streak = drips(h, w, 10, seed + 3, wmin=3, wmax=9, lmin=0.15, lmax=0.45, y0=0.42) * 0.6
    a = np.maximum(a, streak * smoothstep(0.0, 0.5, body + 0.3))
    return np.clip(a * edge_fade(h, w, 0.04, 0.04), 0, 0.85)


def m_streaks(w, h, seed):
    n = noise(h, w, 3, w // 6, seed)
    n2 = noise(h, w, 6, w // 3, seed + 7)
    a = smoothstep(0.55, 0.95, n * 0.7 + n2 * 0.5)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    a = a * smoothstep(0.0, 0.25, y) * (1.0 - smoothstep(0.55, 1.0, y) * (0.5 + 0.5 * n))
    return np.clip(a * 0.7 * edge_fade(h, w, 0.12), 0, 0.8)


def m_rust(w, h, seed):
    n = fbm(h, w, 5, 3, seed)
    a = drips(h, w, 7, seed + 2, wmin=4, wmax=14, lmin=0.25, lmax=0.95, y0=0.06, soft=3.0)
    head = np.zeros((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    head = np.clip(1.0 - np.sqrt(((xx - w / 2) / (w * 0.3)) ** 2 + ((yy - h * 0.08) / (h * 0.14)) ** 2), 0, 1)
    a = np.clip(a * (0.6 + 0.8 * n) + head * 0.7, 0, 1)
    return np.clip(a * 0.85 * edge_fade(h, w, 0.08), 0, 0.85)


def m_soot(w, h, seed):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w * 0.42)) ** 2 + ((yy - h * 0.72) / (h * 0.5)) ** 2)
    n = fbm(h, w, 5, 4, seed)
    a = (1.0 - smoothstep(0.0, 1.0, d + (n - 0.5) * 0.6)) ** 1.6
    return np.clip(a * 0.85, 0, 0.85)


def m_corner(w, h, seed):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx / w) ** 2 + (yy / h) ** 2)
    n = fbm(h, w, 5, 4, seed)
    a = (1.0 - smoothstep(0.1, 1.05, d + (n - 0.5) * 0.45)) ** 1.5
    return np.clip(a * 0.8, 0, 0.85)


def crack_mask(w, h, seed, branches=5):
    r = np.random.RandomState(seed)
    im = Image.new("L", (w * 2, h * 2), 0)
    d = ImageDraw.Draw(im)

    def walk(x, y, ang, steps, width):
        pts = [(x, y)]
        for _ in range(steps):
            ang += r.uniform(-0.55, 0.55)
            step = r.uniform(8, 22) * 2
            x += np.cos(ang) * step
            y += np.sin(ang) * step
            pts.append((x, y))
            if r.rand() < 0.16 and width > 1:
                walk(x, y, ang + r.choice([-1, 1]) * r.uniform(0.5, 1.1), steps // 2, max(1, width - 1))
        d.line(pts, fill=255, width=width * 2, joint="curve")

    walk(w * r.uniform(0.2, 0.5) * 2, 0, np.pi / 2 + r.uniform(-0.3, 0.3), 14, 2)
    for _ in range(branches - 1):
        walk(w * r.uniform(0.2, 0.8) * 2, h * r.uniform(0.2, 0.7) * 2, r.uniform(0, 6.28), 6, 2)
    im = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(im, np.float32) / 255.0
    return np.clip(a * 0.55, 0, 1)


def paint_cell(atlas, name, rgb_fill, alpha):
    x, y, w, h = CELLS[name]
    atlas[y:y + h, x:x + w, :3] = rgb_fill
    atlas[y:y + h, x:x + w, 3] = alpha * 255.0


# ====================================================================== tile damage (opaque patch with soft edge)
def tile_patch(w, h, seed):
    """Missing tiles: an irregular hole in a 4 x 4 tile grid (tile = 64 px = 0.15 m). Exposed grey-brown plaster and mortar bed
    with a dark inner shadow on the upper and left edges, chipped pale glaze on the rim, a broken, jagged outline.
    Returns rgb, alpha."""
    r = np.random.RandomState(seed)
    n = fbm(h, w, 8, 4, seed + 1)
    ss = 3
    mask_im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(mask_im)
    cells = [(1, 1), (2, 1), (1, 2)] if seed % 2 == 0 else [(1, 0), (1, 1), (2, 1), (2, 2)]
    for (cx, cy) in cells:
        x0, y0 = cx * 64 * ss, cy * 64 * ss
        pts = []
        steps = 5
        for side in range(4):
            for k in range(steps):
                t = k / steps
                if side == 0:
                    ux, uy = t, 0.0
                elif side == 1:
                    ux, uy = 1.0, t
                elif side == 2:
                    ux, uy = 1.0 - t, 1.0
                else:
                    ux, uy = 0.0, 1.0 - t
                pts.append((x0 + (ux * 68 - 2) * ss + r.uniform(-7, 7) * ss * 0.45, y0 + (uy * 68 - 2) * ss + r.uniform(-7, 7) * ss * 0.45))
        d.polygon(pts, fill=255)
    m = mask_im.resize((w, h), Image.LANCZOS)
    mask = np.asarray(m, np.float32) / 255.0
    mask = np.clip(mask * (0.9 + 0.2 * smoothstep(0.35, 0.65, n)), 0, 1)
    # shadow: the hole's top and left inside edge sit in the shadow of the surrounding tiles
    sh = np.maximum((mask - np.roll(mask, 7, axis=0)).clip(0, 1), (mask - np.roll(mask, 7, axis=1)).clip(0, 1))
    sh = blur(sh, 2.2)
    base = np.array([66, 57, 47], np.float32) * (0.55 + 0.6 * fbm(h, w, 18, 4, seed + 3))[..., None]
    bed = base * (1.0 - 0.9 * sh[..., None])
    # darker pockets (deep plaster), a few lighter flecks (lime)
    deep = smoothstep(0.55, 0.8, fbm(h, w, 10, 3, seed + 11))
    bed = bed * (1.0 - 0.45 * deep[..., None])
    edge = np.clip(blur(mask, 1.4) * (1 - blur(mask, 1.4)) * 4.0, 0, 1)
    chip = np.array([188, 180, 158], np.float32)
    rgb = bed * (1 - edge[..., None] * 0.55) + chip * edge[..., None] * 0.55
    alpha = np.clip(blur(mask, 0.7), 0, 1)
    rgb = np.where(alpha[..., None] > 0.02, rgb, np.array([84, 74, 62], np.float32))
    return rgb, alpha


# ====================================================================== stencils
YEL = (214, 172, 40)
BLK = (22, 20, 18)
RED = (170, 40, 32)
WHT = (200, 194, 176)


def weather(alpha, seed, amount=0.5):
    n = fbm(alpha.shape[0], alpha.shape[1], 14, 5, seed)
    scratch = noise(alpha.shape[0], alpha.shape[1], 3, alpha.shape[1] // 3, seed + 4)
    k = smoothstep(0.30, 0.60, n * 0.75 + scratch * 0.35)
    return alpha * (1.0 - amount * (1.0 - k)) * (1.0 - 0.25 * (n < 0.28))


def stencil_canvas(w, h, ss=3):
    return Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0)), ss


def finish_stencil(im, w, h, seed, amount=0.55):
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    al = weather(a[..., 3] / 255.0, seed, amount)
    rgb = a[..., :3]
    rgb = np.where(a[..., 3:4] > 4, rgb, np.array(YEL, np.float32))
    return rgb, al


def st_bolt(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    cx, top, bot = w * s / 2, h * s * 0.10, h * s * 0.90
    tri = [(cx, top), (w * s * 0.93, bot), (w * s * 0.07, bot)]
    d.polygon(tri, fill=BLK + (255,))
    inner = [(cx, top + 0.11 * h * s), (w * s * 0.80, bot - 0.045 * h * s), (w * s * 0.20, bot - 0.045 * h * s)]
    d.polygon(inner, fill=YEL + (255,))
    bolt = [(0.56, 0.30), (0.40, 0.58), (0.50, 0.58), (0.44, 0.82), (0.64, 0.50), (0.53, 0.50), (0.62, 0.30)]
    d.polygon([(x * w * s, y * h * s) for x, y in bolt], fill=BLK + (255,))
    return finish_stencil(im, w, h, seed)


def st_flame(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((w * s * 0.08, h * s * 0.08, w * s * 0.92, h * s * 0.92), radius=int(w * s * 0.08), fill=RED + (255,))
    d.rounded_rectangle((w * s * 0.13, h * s * 0.13, w * s * 0.87, h * s * 0.87), radius=int(w * s * 0.05), outline=WHT + (255,), width=int(w * s * 0.018))
    fl = [(0.50, 0.20), (0.62, 0.38), (0.70, 0.52), (0.68, 0.68), (0.58, 0.78), (0.42, 0.78), (0.32, 0.68), (0.30, 0.52),
          (0.38, 0.42), (0.42, 0.50), (0.46, 0.34)]
    d.polygon([(x * w * s, y * h * s) for x, y in fl], fill=WHT + (255,))
    d.polygon([(x * w * s, y * h * s) for x, y in [(0.50, 0.52), (0.58, 0.64), (0.55, 0.74), (0.45, 0.74), (0.42, 0.64)]], fill=RED + (255,))
    return finish_stencil(im, w, h, seed, 0.6)


def st_arrow(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((w * s * 0.04, h * s * 0.22, w * s * 0.96, h * s * 0.78), radius=int(h * s * 0.06), fill=YEL + (255,))
    ar = [(0.12, 0.44), (0.52, 0.44), (0.52, 0.32), (0.88, 0.50), (0.52, 0.68), (0.52, 0.56), (0.12, 0.56)]
    d.polygon([(x * w * s, y * h * s) for x, y in ar], fill=BLK + (255,))
    return finish_stencil(im, w, h, seed, 0.6)


def st_noentry(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    c = (w * s / 2, h * s / 2)
    r = w * s * 0.42
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=WHT + (255,))
    d.ellipse((c[0] - r * 0.80, c[1] - r * 0.80, c[0] + r * 0.80, c[1] + r * 0.80), fill=(0, 0, 0, 0))
    ring = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=RED + (255,))
    rd.ellipse((c[0] - r * 0.80, c[1] - r * 0.80, c[0] + r * 0.80, c[1] + r * 0.80), fill=(0, 0, 0, 0))
    rd.line((c[0] - r * 0.57, c[1] - r * 0.57, c[0] + r * 0.57, c[1] + r * 0.57), fill=RED + (255,), width=int(r * 0.22))
    return finish_stencil(ring, w, h, seed, 0.6)


def st_stripes(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    step = h * s * 0.9
    x = -h * s
    while x < w * s + h * s:
        d.polygon([(x, h * s), (x + step * 0.5, h * s), (x + step * 0.5 + h * s * 0.8, 0), (x + h * s * 0.8, 0)], fill=BLK + (255,))
        x += step
    d.rectangle((0, 0, w * s, h * s * 0.06), fill=YEL + (255,))
    # yellow ground behind the black stripes
    ground = Image.new("RGBA", im.size, YEL + (255,))
    ground.alpha_composite(im)
    return finish_stencil(ground, w, h, seed, 0.82)


def st_keepclear(w, h, seed):
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle((w * s * 0.1, h * s * 0.1, w * s * 0.9, h * s * 0.9), outline=YEL + (255,), width=int(w * s * 0.045))
    d.line((w * s * 0.1, h * s * 0.1, w * s * 0.9, h * s * 0.9), fill=YEL + (255,), width=int(w * s * 0.04))
    d.line((w * s * 0.9, h * s * 0.1, w * s * 0.1, h * s * 0.9), fill=YEL + (255,), width=int(w * s * 0.04))
    return finish_stencil(im, w, h, seed, 0.6)


def st_pipe(w, h, seed):
    """Flow chevrons on a small band (pipe marking): three arrow heads on a pale band."""
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle((0, h * s * 0.2, w * s, h * s * 0.8), fill=(150, 160, 140, 255))
    for k in range(3):
        x0 = (0.12 + 0.26 * k) * w * s
        d.polygon([(x0, h * s * 0.28), (x0 + w * s * 0.14, h * s * 0.5), (x0, h * s * 0.72), (x0 + w * s * 0.05, h * s * 0.5)], fill=BLK + (255,))
    rgb, al = finish_stencil(im, w, h, seed, 0.5)
    return rgb, al


def st_valve(w, h, seed):
    """A valve wheel pictogram next to a pipe tag: wheel with four spokes and a red ring."""
    im, s = stencil_canvas(w, h)
    d = ImageDraw.Draw(im)
    c = (w * s * 0.5, h * s * 0.5)
    r = h * s * 0.40
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=RED + (255,), width=int(r * 0.22))
    d.line((c[0] - r, c[1], c[0] + r, c[1]), fill=RED + (255,), width=int(r * 0.18))
    d.line((c[0], c[1] - r, c[0], c[1] + r), fill=RED + (255,), width=int(r * 0.18))
    return finish_stencil(im, w, h, seed, 0.55)


# ====================================================================== maps and paper
PAPER = np.array([214, 196, 160], np.float32)
INK = (98, 74, 48)
ROUTE = (150, 50, 36)


def paper_base(w, h, seed, stain=True):
    n = fbm(h, w, 6, 4, seed)
    p = PAPER[None, None, :] * (0.86 + 0.22 * n[..., None])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (min(w, h) * 0.5)
    p = p * (0.72 + 0.28 * smoothstep(0.0, 0.35, ed))[..., None]
    if stain:
        m = fbm(h, w, 3, 3, seed + 9)
        p = p * (1.0 - 0.28 * smoothstep(0.55, 0.85, m))[..., None] * np.array([1.0, 0.97, 0.9])
    return p


def contour_lines(w, h, seed, n_lines=14):
    n = fbm(h, w, 3, 4, seed + 2)
    lv = n * n_lines
    d = np.abs(lv - np.round(lv))
    return smoothstep(0.10, 0.0, d)


def finish_paper(p, im_marks, seed, fold=True):
    h, w = p.shape[:2]
    a = np.asarray(im_marks, np.float32) / 255.0
    col = np.array(INK, np.float32)
    p = p * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]
    if fold:
        x = w // 2
        line = np.zeros((h, w), np.float32)
        line[:, x - 1:x + 1] = 1.0
        line[h // 2 - 1:h // 2 + 1, :] = 1.0
        line = blur(line, 1.2)
        p = p * (1 - 0.18 * line[..., None]) + 14 * line[..., None]
    return np.clip(p, 0, 255)


def paper_map_a(w, h, seed):
    p = paper_base(w, h, seed)
    cl = contour_lines(w, h, seed)
    p = p * (1 - 0.5 * cl[..., None] * 0.5) + np.array(INK, np.float32) * 0 + (np.array([120, 96, 64], np.float32) - p) * 0.0
    p = p - cl[..., None] * np.array([70, 70, 60], np.float32) * 0.45
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # grid ticks
    for x in range(0, w, 64):
        d.line((x * ss, 0, x * ss, 10 * ss), fill=INK + (200,), width=2)
        d.line((x * ss, (h - 10) * ss, x * ss, h * ss), fill=INK + (200,), width=2)
    # a river and a route with an X
    r = np.random.RandomState(seed)
    pts = [(10, h * 0.25)]
    for k in range(1, 9):
        pts.append((w * k / 8, h * (0.25 + 0.5 * (k / 8)) + r.uniform(-18, 18)))
    d.line([(x * ss, y * ss) for x, y in pts], fill=(70, 96, 120, 200), width=5 * ss // 2, joint="curve")
    rp = [(w * 0.12, h * 0.82), (w * 0.3, h * 0.62), (w * 0.46, h * 0.66), (w * 0.62, h * 0.42), (w * 0.8, h * 0.36)]
    for i in range(len(rp) - 1):
        (x0, y0), (x1, y1) = rp[i], rp[i + 1]
        L = max(1, int(np.hypot(x1 - x0, y1 - y0) / 9))
        for t in range(0, L, 2):
            a0, a1 = t / L, min(1, (t + 1) / L)
            d.line((x0 + (x1 - x0) * a0, y0 + (y1 - y0) * a0, x0 + (x1 - x0) * a1, y0 + (y1 - y0) * a1), fill=ROUTE + (235,), width=3 * ss // 2)
    xx, yy = rp[-1]
    d.line(((xx - 12) * ss, (yy - 12) * ss, (xx + 12) * ss, (yy + 12) * ss), fill=ROUTE + (255,), width=5 * ss // 2)
    d.line(((xx - 12) * ss, (yy + 12) * ss, (xx + 12) * ss, (yy - 12) * ss), fill=ROUTE + (255,), width=5 * ss // 2)
    d.ellipse(((xx - 22) * ss, (yy - 22) * ss, (xx + 22) * ss, (yy + 22) * ss), outline=ROUTE + (230,), width=3 * ss // 2)
    im = im.resize((w, h), Image.LANCZOS)
    p = finish_paper(p, im, seed)
    return p


def paper_map_b(w, h, seed):
    """A survey sheet: concentric rings and a cross-hair grid (a plan of the Gallery's drum), pencilled marks."""
    p = paper_base(w, h, seed + 4)
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (w * ss / 2, h * ss / 2)
    for k, rr in enumerate([0.42, 0.34, 0.22, 0.10]):
        r = rr * w * ss
        d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=INK + (210,), width=2 * ss // 2 + 1)
    d.line((c[0], 0.08 * h * ss, c[0], 0.92 * h * ss), fill=INK + (190,), width=2)
    d.line((0.08 * w * ss, c[1], 0.92 * w * ss, c[1]), fill=INK + (190,), width=2)
    r = np.random.RandomState(seed)
    for k in range(41):
        a = 2 * np.pi * k / 41
        rr = 0.42 * w * ss
        x, y = c[0] + np.cos(a) * rr, c[1] + np.sin(a) * rr
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=INK + (230,))
    d.line((c[0] + 0.1 * w * ss, c[1] - 0.3 * w * ss, c[0] + 0.28 * w * ss, c[1] - 0.2 * w * ss), fill=ROUTE + (230,), width=4)
    im = im.resize((w, h), Image.LANCZOS)
    return finish_paper(p, im, seed + 1)


def paper_map_c(w, h, seed):
    """A floor plan: rooms as rectangles with door gaps, a dashed path, a star."""
    p = paper_base(w, h, seed + 8)
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x0, y0, x1, y1) in [(0.10, 0.12, 0.45, 0.50), (0.45, 0.12, 0.90, 0.40), (0.45, 0.40, 0.90, 0.88), (0.10, 0.50, 0.45, 0.88)]:
        d.rectangle((x0 * w * ss, y0 * h * ss, x1 * w * ss, y1 * h * ss), outline=INK + (220,), width=3)
    d.line((0.45 * w * ss, 0.26 * h * ss, 0.45 * w * ss, 0.34 * h * ss), fill=(0, 0, 0, 0), width=7)
    for k in range(10):
        a = 0.14 + 0.07 * k
        d.line((a * w * ss, 0.30 * h * ss, (a + 0.035) * w * ss, 0.30 * h * ss), fill=ROUTE + (230,), width=4)
    cx, cy, r = 0.72 * w * ss, 0.62 * h * ss, 0.07 * w * ss
    pts = [(cx + np.cos(np.pi * (0.5 + 0.4 * k)) * (r if k % 2 == 0 else r * 0.4), cy - np.sin(np.pi * (0.5 + 0.4 * k)) * (r if k % 2 == 0 else r * 0.4)) for k in range(10)]
    pts = [(cx + np.cos(2 * np.pi * k / 10 - np.pi / 2) * (r if k % 2 == 0 else r * 0.42), cy + np.sin(2 * np.pi * k / 10 - np.pi / 2) * (r if k % 2 == 0 else r * 0.42)) for k in range(10)]
    d.polygon(pts, fill=ROUTE + (230,))
    im = im.resize((w, h), Image.LANCZOS)
    return finish_paper(p, im, seed + 2)


def paper_page(w, h, seed):
    """A notebook page: ruled lines, a margin, scribbled sketch marks (no words)."""
    p = paper_base(w, h, seed + 12, stain=False)
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(1, 13):
        y = k * h * ss / 13
        d.line((0.06 * w * ss, y, 0.94 * w * ss, y), fill=(110, 140, 160, 150), width=2)
    d.line((0.16 * w * ss, 0, 0.16 * w * ss, h * ss), fill=(170, 80, 70, 150), width=2)
    r = np.random.RandomState(seed)
    for k in range(5):
        y = (1.3 + k * 1.8) * h * ss / 13
        x = 0.2 * w * ss
        pts = []
        while x < r.uniform(0.55, 0.9) * w * ss:
            pts.append((x, y + r.uniform(-4, 4) * ss * 0.5))
            x += r.uniform(5, 14) * ss * 0.5
        if len(pts) > 2:
            d.line(pts, fill=INK + (200,), width=2, joint="curve")
    d.ellipse((0.58 * w * ss, 0.60 * h * ss, 0.86 * w * ss, 0.88 * h * ss), outline=INK + (200,), width=3)
    d.line((0.64 * w * ss, 0.78 * h * ss, 0.80 * w * ss, 0.70 * h * ss), fill=INK + (200,), width=3)
    im = im.resize((w, h), Image.LANCZOS)
    return finish_paper(p, im, seed + 3, fold=False)


def paper_chart(w, h, seed):
    """A tuning chart: horizontal bars of descending length (four sizes) beside a time axis, no figures."""
    p = paper_base(w, h, seed + 20)
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(4):
        y0 = (0.16 + 0.19 * k) * h * ss
        ln = (0.78 - 0.14 * k) * w * ss
        d.rectangle((0.12 * w * ss, y0, 0.12 * w * ss + ln, y0 + 0.10 * h * ss), outline=INK + (220,), width=3)
        d.rectangle((0.12 * w * ss, y0, 0.12 * w * ss + ln * 0.5, y0 + 0.10 * h * ss), fill=INK + (90,))
    d.line((0.10 * w * ss, 0.08 * h * ss, 0.10 * w * ss, 0.94 * h * ss), fill=INK + (230,), width=3)
    im = im.resize((w, h), Image.LANCZOS)
    return finish_paper(p, im, seed + 5, fold=False)


def paper_tags(w, h, seed):
    """Cut-out photo / tag strips: a small instant photo frame with an abstract scene."""
    p = np.zeros((h, w, 3), np.float32) + np.array([226, 220, 204], np.float32)
    n = fbm(h, w, 6, 3, seed)
    p = p * (0.85 + 0.2 * n[..., None])
    ss = 2
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0.10 * w * ss, 0.10 * h * ss, 0.90 * w * ss, 0.70 * h * ss), fill=(52, 60, 58, 255))
    d.polygon([(0.10 * w * ss, 0.70 * h * ss), (0.40 * w * ss, 0.40 * h * ss), (0.58 * w * ss, 0.56 * h * ss), (0.70 * w * ss, 0.44 * h * ss), (0.90 * w * ss, 0.70 * h * ss)], fill=(88, 98, 90, 255))
    d.ellipse((0.66 * w * ss, 0.16 * h * ss, 0.80 * w * ss, 0.30 * h * ss), fill=(214, 204, 170, 255))
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    p = p * (1 - a[..., 3:4]) + a[..., :3] * 255 * a[..., 3:4]
    return np.clip(p, 0, 255)


# ====================================================================== build
def build_atlas():
    atlas = np.zeros((H, W, 4), np.float32)
    atlas[..., :3] = GRIME
    paint_cell(atlas, "grime_top", GRIME, m_grime_top(512, 256, 11))
    paint_cell(atlas, "damp_a", DAMP, m_damp(256, 256, 21))
    paint_cell(atlas, "damp_b", DAMP, m_damp(256, 256, 22))
    paint_cell(atlas, "streaks_a", GRIME, m_streaks(256, 256, 31))
    paint_cell(atlas, "streaks_b", GRIME, m_streaks(256, 256, 32))
    paint_cell(atlas, "baseboard", GRIME, m_baseboard(512, 256, 41))
    paint_cell(atlas, "rust_a", RUST, m_rust(256, 256, 51))
    paint_cell(atlas, "rust_b", RUST, m_rust(256, 256, 52))
    paint_cell(atlas, "corner", GRIME, m_corner(256, 256, 61))
    paint_cell(atlas, "soot", SOOT, m_soot(256, 256, 71))
    paint_cell(atlas, "crack_a", np.array([22, 18, 14], np.float32), crack_mask(256, 256, 81))
    paint_cell(atlas, "crack_b", np.array([22, 18, 14], np.float32), crack_mask(256, 256, 82, 4))
    for nm, seed in (("tiles_a", 2), ("tiles_b", 3)):
        x, y, w, h = CELLS[nm]
        rgb, al = tile_patch(w, h, seed)
        atlas[y:y + h, x:x + w, :3] = rgb
        atlas[y:y + h, x:x + w, 3] = al * 255.0
    for nm, fn, seed in (("st_bolt", st_bolt, 91), ("st_flame", st_flame, 92), ("st_arrow", st_arrow, 93),
                         ("st_noentry", st_noentry, 94), ("st_stripes", st_stripes, 95), ("st_keepclear", st_keepclear, 96),
                         ("st_pipe", st_pipe, 97), ("st_valve", st_valve, 98)):
        x, y, w, h = CELLS[nm]
        rgb, al = fn(w, h, seed)
        atlas[y:y + h, x:x + w, :3] = rgb
        atlas[y:y + h, x:x + w, 3] = al * 255.0
    for nm, fn, seed in (("map_a", paper_map_a, 101), ("map_b", paper_map_b, 102), ("map_c", paper_map_c, 103),
                         ("page", paper_page, 104), ("chart", paper_chart, 105), ("tags", paper_tags, 106)):
        x, y, w, h = CELLS[nm]
        atlas[y:y + h, x:x + w, :3] = fn(w, h, seed)
        atlas[y:y + h, x:x + w, 3] = 255.0
    return np.clip(atlas, 0, 255).astype(np.uint8)


TRES = {
    "M_Dress_Grime": """[gd_resource type="StandardMaterial3D" load_steps=2 format=3]

[ext_resource type="Texture2D" path="res://assets/textures/dress/ch3_grime.png" id="1"]

[resource]
resource_name = "M_Dress_Grime"
transparency = 1
cull_mode = 2
albedo_texture = ExtResource("1")
roughness = 0.92
""",
    # darker plaster for the memorial niche (same plaster scan as M_Plaster_Stained, tinted blue-grey and darkened)
    "M_Dress_Plaster_Dark": """[gd_resource type="ORMMaterial3D" load_steps=4 format=3]

[ext_resource type="Texture2D" path="res://assets/textures/plaster_wall/albedo.jpg" id="1"]
[ext_resource type="Texture2D" path="res://assets/textures/plaster_wall/normal.png" id="2"]
[ext_resource type="Texture2D" path="res://assets/textures/plaster_wall/orm.jpg" id="3"]

[resource]
resource_name = "M_Dress_Plaster_Dark"
albedo_texture = ExtResource("1")
orm_texture = ExtResource("3")
metallic = 0
roughness = 1.0
normal_enabled = true
normal_scale = 0.6
albedo_color = Color(0.2, 0.235, 0.24, 1)
normal_texture = ExtResource("2")
ao_enabled = true
uv1_scale = Vector3(0.45, 0.45, 0.45)
""",
    # a dark, polished basalt look from the stone scan (plinth, dentil band)
    "M_Dress_Stone_Dark": """[gd_resource type="ORMMaterial3D" load_steps=4 format=3]

[ext_resource type="Texture2D" path="res://assets/textures/stone/albedo.jpg" id="1"]
[ext_resource type="Texture2D" path="res://assets/textures/stone/normal.png" id="2"]
[ext_resource type="Texture2D" path="res://assets/textures/stone/orm.jpg" id="3"]

[resource]
resource_name = "M_Dress_Stone_Dark"
albedo_texture = ExtResource("1")
orm_texture = ExtResource("3")
metallic = 0
roughness = 0.85
normal_enabled = true
albedo_color = Color(0.3, 0.29, 0.28, 1)
normal_texture = ExtResource("2")
ao_enabled = true
uv1_scale = Vector3(1.4, 1.4, 1.4)
""",
    # a worn wool blanket: faded brick-brown (darker and less saturated than the first pass) (the fabric scan's albedo is too dark to tint), the weave kept in normal and ORM
    "M_Dress_Wool": """[gd_resource type="ORMMaterial3D" load_steps=3 format=3]

[ext_resource type="Texture2D" path="res://assets/textures/fabric/normal.png" id="2"]
[ext_resource type="Texture2D" path="res://assets/textures/fabric/orm.jpg" id="3"]

[resource]
resource_name = "M_Dress_Wool"
orm_texture = ExtResource("3")
metallic = 0
roughness = 1.0
normal_enabled = true
albedo_color = Color(0.30, 0.205, 0.165, 1)
normal_texture = ExtResource("2")
ao_enabled = true
uv1_scale = Vector3(3.7037, 3.7037, 3.7037)
""",
    # candle / lantern / heater-window flames: emission kept below the environment's glow threshold (1.1), so a phone shows a
    # warm point of light and no bloom halo (M_Emissive_Warm is 3.0 and blooms)
    "M_Dress_Flame": """[gd_resource type="StandardMaterial3D" load_steps=1 format=3]

[resource]
resource_name = "M_Dress_Flame"
albedo_color = Color(1, 0.74, 0.44, 1)
roughness = 0.6
emission_enabled = true
emission = Color(1, 0.72, 0.4, 1)
emission_energy_multiplier = 0.95
""",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    atlas = build_atlas()
    Image.fromarray(atlas, "RGBA").save(os.path.join(OUT, "ch3_grime.png"), optimize=True)
    with open(os.path.join(OUT, "ch3_grime_cells.json"), "w") as f:
        json.dump(CELLS, f, indent=1)
    for name, body in TRES.items():
        path = os.path.join(MAT, name + ".tres")
        with open(path, "w") as f:
            f.write(body)
    print("[ch3-dress-tex] wrote", os.path.join(OUT, "ch3_grime.png"), "and", ", ".join(TRES))
    if "--sheet" in sys.argv:
        bg = Image.new("RGBA", (W, H), (150, 150, 140, 255))
        bg.alpha_composite(Image.fromarray(atlas, "RGBA"))
        bg.convert("RGB").save(sys.argv[sys.argv.index("--sheet") + 1])


if __name__ == "__main__":
    main()
