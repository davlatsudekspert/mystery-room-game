#!/usr/bin/env python3
"""Chapter 3 (The Underground Facility, Level -2) decals, symbol images, tiling texture sets and QA previews.

Original procedural artwork (PIL + numpy only, no third-party images); helpers and style from
make_decals_ch2.py. Contract: docs/models/ch3.md §0 (slots), §11 (variant evidence), §12 (decals).

Outputs
    game/assets/textures/decals/ch3/
        sym_sun|moon|star|triangle|circle|square|diamond.png   512² RGBA, white on transparent, height 0.80
        interlock_plate.png       1024 x 512   the W1 rule in pictograms (no words)
        ecg_paper.png             2048 x 320   ECG grid paper, three pen brackets with ☼ ☾ ✦ above (no trace)
        chalk_grid.png            1024 x 352   RGBA chalk grid of choir_rack stair_quad (no dots)
        growth_grid.png            768 x 1024  Leyla's graph paper (no curve)
        growth_log.png  (+_ru, _uz) 768 x 1024 a page of Leyla's log (doc3.growth_log) with the blank sketch square
        strand_note.png (+_ru, _uz) 512 x 384  doc3.note in Strand's hand
    game/assets/textures/{tile_glazed, rock, chequer}/{albedo.jpg, normal.png, orm.jpg}
        M_Tile_Glazed (0.15 m tiles, 0.6 m repeat), M_Rock (2.4 m repeat), M_Chequer (0.30 m repeat), 1024²
    qa/blender/ch3/preview/   seed-0 images of every §11 shader quad (QA only, never shipped)
    qa/blender/ch3/decals_ch3_sheet.jpg, decals_ch3_lang_sheet.jpg, preview/previews_sheet.jpg

The symbols come from tools/blender/lib_ch3_symbols.py (the same outlines as every 3D inlay). Puzzle data mirrors
game/src/rooms/underground/underground_logic.gd (seed 0 = the canonical constants).

    python3 tools/textures/make_decals_ch3.py                         # everything
    python3 tools/textures/make_decals_ch3.py --only interlock_plate,ecg_paper --no-sheet
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
import make_decals_ch2 as D2  # noqa: E402  (definitions only; its generators run from its own main())
from make_decals_ch2 import (F_HAND, F_SANS, F_SANS_B, LANGS, Pen, blur, fbm, font, hexf, lname, noise,  # noqa: E402
                             normal_from_height, paper, pnoise, rot_text, save, smooth, text_width, to_img,
                             white_rgba)
import lib_ch3_symbols as S  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch3")
TEX = os.path.join(ROOT, "game", "assets", "textures")
QA3 = os.path.join(ROOT, "qa", "blender", "ch3")
PREVIEW = os.path.join(QA3, "preview")

# ---- puzzle data (UndergroundLogic constants = seed 0) -------------------------------------------------
CHOIR_TARGET = [4, 6, 2, 7, 1, 5, 3]
CASE_CODE = [4, 2, 6]                       # v_heart: peaks in the sun, moon, star brackets
SEED_GLYPHS = ["110110", "001101", "100100", "111100", "010110", "110000",
               "110100", "100101", "010100", "101010", "110101", "111000"]
SEED_SKETCH = "001101"
PEGS_TARGET = [5, 2, 4]                     # v_curve
RED, GREEN, BLUE = 1, 2, 4
P_BANDS, Q_BANDS = [RED, GREEN, BLUE], [BLUE, GREEN, RED]
RIMS = [RED | GREEN, RED | GREEN, BLUE]
PRISM_START = 2
FREQ = (3, 2)
MELODY = [3, 1, 4, 2]

# ---- text (tools/localization/strings_ch3.py) -----------------------------------------------------------
TXT = {
    "doc3.note": ("My heart keeps the count.", "Моё сердце ведёт счёт.", "Yuragim sanoqni saqlaydi."),
    "doc3.growth_log": ("Last seed, cross-section. Sketched a third of a turn off.",
                        "Последняя затравка, срез. Зарисована с поворотом на треть оборота.",
                        "Oxirgi urugʻ, kesimi. Uchdan bir burilish bilan chizilgan."),
    "initial_s": ("— S.", "— С.", "— S."),
}


def t(key: str, lang: str) -> str:
    return TXT[key][LANGS.index(lang)]


INK_PEN = "#1F2A4E"        # blue-black fountain pen
INK_PRINT = "#1E232B"      # enamel print
GRAPHITE = "#4A4A4E"


# =================================================================================================
# shared drawing helpers
# =================================================================================================
def shape_mask(kind: str, w: int, h: int, cx: float, cy: float, height: float, rot_deg: float = 0.0,
               ss: int = 4, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """Filled lib_ch3_symbols shape as a float mask (image coords, y down). Shapes are max-combined, so holes
    stay holes. rot_deg rotates counter-clockwise as seen; jitter (px) wobbles the outline (hand-drawn)."""
    rng = np.random.default_rng(seed)
    ca, sa = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    acc = np.zeros((h, w), np.float32)
    for shp in S.shapes(kind, height):
        pen = Pen(w, h, ss)
        for li, lp in enumerate(shp):
            pts = []
            for (x, y) in lp:
                if jitter:
                    x += rng.normal(0, jitter)
                    y += rng.normal(0, jitter)
                xr, yr = x * ca - y * sa, x * sa + y * ca
                pts.append((cx + xr, cy - yr))
            pen.poly(pts, 255 if li == 0 else 0)
        acc = np.maximum(acc, pen.arr())
    return acc


def shape_outline(pen: Pen, kind: str, cx: float, cy: float, height: float, width: float, v: int = 255,
                  rot_deg: float = 0.0, jitter: float = 0.0, seed: int = 0) -> None:
    rng = np.random.default_rng(seed)
    ca, sa = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    for shp in S.shapes(kind, height):
        for lp in shp:
            pts = []
            for (x, y) in lp + [lp[0]]:
                xr, yr = x * ca - y * sa, x * sa + y * ca
                pts.append((cx + xr + (rng.normal(0, jitter) if jitter else 0), cy - yr + (rng.normal(0, jitter) if jitter else 0)))
            pen.line(pts, width, v, caps=True)


def wobble_line(pen: Pen, p0, p1, width: float, rng, amp: float = 1.2, n: int = 24, v: int = 255) -> None:
    """Hand-drawn straight line: low-frequency wobble perpendicular to the stroke."""
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ph1, ph2 = rng.uniform(0, math.tau), rng.uniform(0, math.tau)
    f1, f2 = rng.uniform(0.6, 1.4), rng.uniform(2.0, 3.5)
    pts = []
    for i in range(n + 1):
        s = i / n
        off = amp * (0.7 * math.sin(math.tau * f1 * s + ph1) + 0.3 * math.sin(math.tau * f2 * s + ph2))
        pts.append((x0 + (x1 - x0) * s + nx * off, y0 + (y1 - y0) * s + ny * off))
    pen.line(pts, width, v, caps=True)


def arrow(pen: Pen, p0, p1, width: float, head: float, v: int = 255) -> None:
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * head, y1 - uy * head
    pen.line([(x0, y0), (bx + ux * 1.0, by + uy * 1.0)], width, v, caps=False)
    pen.poly([(x1, y1), (bx - uy * head * 0.55, by + ux * head * 0.55), (bx + uy * head * 0.55, by - ux * head * 0.55)], v)


def arc_arrow(pen: Pen, cx, cy, r, a0, a1, width, head, v: int = 255, n: int = 48) -> None:
    """Arc from a0 to a1 (degrees, image coords: 0 = +x, +90 = down, so increasing = clockwise as seen) with an
    arrow head at a1."""
    sgn = 1.0 if a1 > a0 else -1.0
    trim = math.degrees(head * 0.8 / r) * sgn
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - trim - a0) * i / n)),
            cy + r * math.sin(math.radians(a0 + (a1 - trim - a0) * i / n))) for i in range(n + 1)]
    pen.line(pts, width, v, caps=True)
    ae = math.radians(a1)
    tip = (cx + r * math.cos(ae), cy + r * math.sin(ae))
    tx, ty = -math.sin(ae) * sgn, math.cos(ae) * sgn               # travel direction at the end
    nx, ny = math.cos(ae), math.sin(ae)
    b = (tip[0] - tx * head, tip[1] - ty * head)
    pen.poly([tip, (b[0] + nx * head * 0.55, b[1] + ny * head * 0.55), (b[0] - nx * head * 0.55, b[1] - ny * head * 0.55)], v)


def pencil_tex(mask: np.ndarray, seed: int, amount: float = 0.45) -> np.ndarray:
    """Graphite: grainy, paper-tooth broken coverage."""
    h, w = mask.shape
    tooth = noise(h, w, 1.3, 1, seed)
    streak = noise(h, w * 4, 3.0, 2, seed + 1)[:, ::4]
    return mask * np.clip(1 - amount + amount * 1.3 * (0.6 * tooth + 0.4 * streak), 0, 1)


def ink_tex(mask: np.ndarray, seed: int, amount: float = 0.22) -> np.ndarray:
    h, w = mask.shape
    n = noise(h, w, 2.4, 2, seed)
    pool = noise(h, w, 18, 2, seed + 7)
    return np.clip(mask * (1 - amount + amount * 1.4 * n) * (0.9 + 0.2 * pool), 0, 1)


def chalk_tex(mask: np.ndarray, seed: int, amount: float = 0.6) -> np.ndarray:
    h, w = mask.shape
    grit = noise(h, w, 1.1, 1, seed)
    drag = noise(h, w * 6, 2.0, 2, seed + 3)[:, ::6]
    return mask * np.clip((grit * 0.6 + drag * 0.4 - (amount - 0.5)) * 1.8, 0, 1)


def hand_lines(txt: str, path: str, size: float, max_w: float, weight=None):
    """Greedy word wrap (handwriting)."""
    words = txt.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, path, size, 0.0, weight) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def ensure_dirs() -> None:
    for d in (OUT, PREVIEW):
        os.makedirs(d, exist_ok=True)


# =================================================================================================
# 1. symbol images (§12)
# =================================================================================================
def symbols():
    for k in S.NAMES:
        m = shape_mask(k, 512, 512, 256, 256, 0.80 * 512)
        save(white_rgba(m), S.DECAL_FILE[k], OUT)


# =================================================================================================
# 2. tiling texture sets
# =================================================================================================
def _seam_dist(c, T):
    m = np.mod(c, T)
    return np.minimum(m, T - m)


def tile_glazed():
    """Cream-white glazed wall tiles 0.15 m with grey grout, 4 x 4 per 0.6 m repeat (1024 px: 1.71 px/mm)."""
    S_, N = 1024, 4
    T = S_ / N
    rng = np.random.default_rng(3100)
    yy, xx = np.mgrid[0:S_, 0:S_].astype(np.float32)
    sd = np.minimum(_seam_dist(xx + 0.5, T), _seam_dist(yy + 0.5, T))
    gh = 2.7                                                   # grout half width (≈ 3.2 mm joint)
    grout = smooth(gh + 0.7, gh - 0.7, sd)
    edge = smooth(gh, gh + 9.0, sd)                            # rounded tile edge (pillow)
    ti = np.floor(np.mod(xx + 0.5, S_) / T).astype(int)
    tj = np.floor(np.mod(yy + 0.5, S_) / T).astype(int)
    tint = np.zeros((N, N, 3), np.float32)
    craz = np.zeros((N, N), np.float32)
    for j in range(N):
        for i in range(N):
            k = rng.normal(0, 0.012)
            hue = rng.normal(0, 0.005)
            tint[j, i] = (1 + k + hue, 1 + k, 1 + k - hue * 1.5)
            craz[j, i] = rng.uniform(0.0, 1.0) ** 1.5
    base = hexf("#DCD8CC")
    alb = base[None, None] * tint[tj, ti]
    # glaze: soft clouding, crazing network, pinholes
    cloud = fbm(S_, S_, 90, 3110, 3)
    alb = alb * (0.985 + 0.03 * (cloud - 0.5))[..., None]
    c1, c2, _, _, _ = _voronoi(S_, 900, 3111)                 # crazing: a fine polygonal hairline network
    crack = smooth(1.3, 0.2, c2 - c1) * smooth(0.45, 0.8, craz[tj, ti]) * edge
    pin = (pnoise(S_, S_, 0.9, 3113) > 0.93).astype(np.float32) * 0.5
    # grime: grout dirt, soot at the tile edges, vertical streaks running down (v = world up)
    seam_dirt = np.exp(-(sd / 7.0) ** 2) * (0.5 + 0.5 * pnoise(S_, S_, 30, 3114))
    streak = smooth(0.62, 0.92, pnoise(S_, S_, 22, 3115, (0.35, 6.0))) * smooth(0.3, 0.8, fbm(S_, S_, 200, 3116, 3))
    blot = smooth(0.55, 0.85, fbm(S_, S_, 160, 3117, 4))
    # chipped glaze at a few tile corners
    chip_pen = Pen(S_, S_, 2)
    for _ in range(9):
        cx, cy = rng.integers(0, N + 1) * T + rng.normal(0, 4), rng.integers(0, N + 1) * T + rng.normal(0, 4)
        pts = [(cx + rng.uniform(4, 11) * math.cos(a), cy + rng.uniform(4, 11) * math.sin(a))
               for a in np.linspace(0, math.tau, 10, endpoint=False)]
        for ox in (-S_, 0, S_):
            for oy in (-S_, 0, S_):
                chip_pen.poly([(x + ox, y + oy) for x, y in pts])
    chips = blur(chip_pen.arr(), 0.6, wrap=True) * (1 - grout)
    g3 = grout[..., None]
    grout_col = hexf("#8D8A82") * (0.85 + 0.25 * pnoise(S_, S_, 3, 3118))[..., None]
    alb = alb * (1 - 0.10 * seam_dirt[..., None]) * (1 - 0.07 * blot[..., None]) * (1 - 0.10 * streak[..., None])
    alb = alb * (1 - 0.10 * crack[..., None]) * (1 - 0.12 * pin[..., None])
    alb = alb * (1 - chips[..., None]) + hexf("#8E8270") * chips[..., None]
    alb = alb * (1 - g3) + grout_col * (1 - 0.35 * seam_dirt[..., None]) * g3
    rough = 0.16 + 0.05 * (cloud - 0.5) + 0.08 * blot + 0.12 * streak + 0.25 * crack + 0.6 * chips
    rough = rough * (1 - grout) + (0.86 + 0.05 * (pnoise(S_, S_, 4, 3119) - 0.5)) * grout
    hgt = 1.0 * edge - 0.45 * chips - 0.03 * crack + 0.02 * (cloud - 0.5) - 0.25 * grout
    hgt = hgt + 0.015 * (pnoise(S_, S_, 3, 3120) - 0.5)
    normal = normal_from_height(hgt, 3.0)
    ao = np.clip(1 - 0.45 * grout - 0.12 * (1 - edge) - 0.25 * chips, 0, 1)
    orm = np.stack([ao, np.clip(rough, 0.08, 0.95), np.zeros_like(ao)], -1)
    folder = os.path.join(TEX, "tile_glazed")
    os.makedirs(folder, exist_ok=True)
    save(to_img(alb), "albedo.jpg", folder)
    save(to_img(normal * 255.0), "normal.png", folder)
    save(to_img(orm * 255.0), "orm.jpg", folder)


def _voronoi(S_, n, seed, warp=None):
    """Periodic Voronoi of n random points on an S_ x S_ torus: (d1, d2, nearest index, dx, dy to that point).
    warp = (wx, wy) pixel offsets (periodic fields) bend the cell edges."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, S_, (n, 2))
    yy, xx = np.mgrid[0:S_, 0:S_].astype(np.float64)
    if warp is not None:
        xx = xx + warp[0]
        yy = yy + warp[1]
    q = np.stack([(xx.ravel() + 0.5) % S_, (yy.ravel() + 0.5) % S_], -1)
    d, idx = cKDTree(pts, boxsize=S_).query(q, k=2)
    near = pts[idx[:, 0]]
    dx = (q[:, 0] - near[:, 0] + S_ / 2) % S_ - S_ / 2
    dy = (q[:, 1] - near[:, 1] + S_ / 2) % S_ - S_ / 2
    sh = (S_, S_)
    return (d[:, 0].reshape(sh).astype(np.float32), d[:, 1].reshape(sh).astype(np.float32), idx[:, 0].reshape(sh),
            dx.reshape(sh).astype(np.float32), dy.reshape(sh).astype(np.float32))


def rock():
    """Dark wet rock (lift shaft, shaft throat, Array cavern): angular fractured blocks (two Voronoi scales with a
    random facet slope per block), cracks, iron stains, calcite, and wet seeps. 2.4 m repeat, 1024 px."""
    S_ = 1024
    rng = np.random.default_rng(3200)
    w1 = (fbm(S_, S_, 120, 3211, 4) - 0.5) * 120, (fbm(S_, S_, 120, 3212, 4) - 0.5) * 120
    w2 = (fbm(S_, S_, 50, 3213, 3) - 0.5) * 50, (fbm(S_, S_, 50, 3214, 3) - 0.5) * 50
    d1, d2, idx, dx, dy = _voronoi(S_, 26, 3201, w1)          # blocks ~0.5 m, bent joints
    e1, e2, jdx, ex, ey = _voronoi(S_, 150, 3202, w2)         # fracture facets ~0.2 m
    gx, gy, off = rng.normal(0, 1, 26), rng.normal(0, 1, 26), rng.uniform(0, 1, 26)
    hx, hy = rng.normal(0, 1, 150), rng.normal(0, 1, 150)
    facet = off[idx] * 0.7 + (gx[idx] * dx + gy[idx] * dy) / 160.0
    facet2 = (hx[jdx] * ex + hy[jdx] * ey) / 130.0
    open_ = 0.4 + 0.9 * fbm(S_, S_, 90, 3215, 3)              # joints open and close along their length
    crack = smooth(5.0 * open_, 0.5, d2 - d1) * smooth(0.25, 0.5, open_)
    crack2 = smooth(1.8, 0.2, e2 - e1) * smooth(0.55, 0.75, fbm(S_, S_, 100, 3216, 3)) * 0.5
    bulge = np.sqrt(np.clip(d2 - d1, 0, 80) / 80.0)          # blocks are rounded away from their joints
    detail = fbm(S_, S_, 60, 3203, 5)
    fine = pnoise(S_, S_, 2.5, 3204)
    hgt = 0.50 * facet + 0.30 * facet2 + 0.35 * bulge - 0.7 * crack - 0.25 * crack2 + 0.75 * detail + 0.06 * fine
    cav = np.clip((blur(hgt, 5, wrap=True) - hgt) * 5, 0, 1)
    exp_ = np.clip((hgt - blur(hgt, 8, wrap=True)) * 4, 0, 1)
    tone = 0.80 + 0.35 * rng.uniform(0, 1, 30)[idx] * (0.7 + 0.6 * detail)
    col = hexf("#2D2B28")[None, None] * tone[..., None]
    col = col * (1 - 0.5 * cav[..., None]) + hexf("#57514A") * (0.40 * exp_)[..., None]
    rust = smooth(0.58, 0.85, fbm(S_, S_, 70, 3205, 3)) * np.clip(0.3 + 0.9 * blur(crack, 6, wrap=True), 0, 1)
    col = col * (1 - 0.45 * rust[..., None]) + hexf("#5E3B22") * (0.45 * rust)[..., None]
    calc = smooth(0.82, 0.96, pnoise(S_, S_, 10, 3206, (0.4, 4.0))) * smooth(0.55, 0.85, fbm(S_, S_, 160, 3207, 3))
    col = col * (1 - 0.30 * calc[..., None]) + hexf("#8A877C") * (0.30 * calc)[..., None]
    seep = smooth(0.62, 0.88, pnoise(S_, S_, 20, 3208, (0.3, 7.0))) * smooth(0.35, 0.75, fbm(S_, S_, 240, 3209, 3))
    wet = np.clip(np.maximum(seep, blur(crack, 3, wrap=True) * 0.9), 0, 1)
    col = col * (1 - 0.28 * wet[..., None])
    rough = np.clip(0.78 - 0.50 * wet - 0.10 * cav + 0.10 * exp_ + 0.06 * (fine - 0.5), 0.2, 0.95)
    normal = normal_from_height(hgt, 9.0)
    ao = np.clip(1 - 0.6 * cav - 0.35 * crack, 0, 1)
    orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
    folder = os.path.join(TEX, "rock")
    os.makedirs(folder, exist_ok=True)
    save(to_img(col), "albedo.jpg", folder)
    save(to_img(normal * 255.0), "normal.png", folder)
    save(to_img(orm * 255.0), "orm.jpg", folder)


def chequer():
    """Diamond (chequer) tread plate: 10 x 10 lugs per 0.30 m repeat, alternating ±45°, worn bright tops,
    dirt in the valleys, a little rust. Metallic in the ORM blue channel."""
    S_, N = 1024, 10
    yy, xx = np.mgrid[0:S_, 0:S_].astype(np.float32)
    u, v = (xx + 0.5) / S_ * N, (yy + 0.5) / S_ * N
    i, j = np.floor(u), np.floor(v)
    fx, fy = u - i - 0.5, v - j - 0.5
    sgn = np.where((i + j) % 2 == 0, 1.0, -1.0)
    c = math.cos(math.radians(45))
    ax = (fx + sgn * fy) * c                                   # along the lug
    ay = (-sgn * fx + fy) * c                                  # across
    hl, hw = 0.33, 0.085
    dx = np.maximum(np.abs(ax) - (hl - hw), 0)
    dist = np.sqrt(dx ** 2 + ay ** 2) - hw                     # rounded-end bar (capsule) distance
    lug = smooth(0.015, -0.03, dist)                           # 1 on the lug
    top = smooth(-0.025, -0.06, dist)                          # flat lug top
    hgt = lug * 0.8 + top * 0.2 + 0.03 * (pnoise(S_, S_, 4, 3300) - 0.5)
    wear = smooth(0.35, 0.8, fbm(S_, S_, 220, 3301, 3))        # walked paths
    dirt = (1 - lug) * smooth(0.3, 0.75, fbm(S_, S_, 60, 3302, 4))
    rust = smooth(0.70, 0.92, fbm(S_, S_, 40, 3303, 3)) * (1 - top)
    scr = np.zeros((S_, S_), np.float32)
    rng = np.random.default_rng(3304)
    strokes = []
    for _ in range(120):
        x0, y0 = rng.uniform(0, S_), rng.uniform(0, S_)
        a = rng.normal(0.2, 0.6)
        ln = rng.uniform(30, 160)
        strokes.append(([(x0, y0), (x0 + math.cos(a) * ln, y0 + math.sin(a) * ln)], rng.uniform(0.6, 1.2), rng.uniform(0.3, 0.8)))
    scr = D2._wrap_pen_lines(S_, strokes)
    steel = hexf("#5E605B")
    col = steel[None, None] * (0.92 + 0.12 * pnoise(S_, S_, 30, 3305))[..., None]
    col = col + (hexf("#8F918C") - steel) * (top * (0.35 + 0.55 * wear))[..., None]
    col = col + (hexf("#9EA09A") - col) * (0.35 * scr)[..., None]
    col = col * (1 - 0.6 * dirt[..., None]) + hexf("#4A4236") * (0.6 * dirt)[..., None]
    col = col * (1 - 0.7 * rust[..., None]) + hexf("#6A3E22") * (0.7 * rust)[..., None]
    metal = np.clip(0.88 - 0.75 * dirt - 0.8 * rust, 0.05, 1.0)
    rough = np.clip(0.48 - 0.16 * top * wear - 0.08 * scr + 0.35 * dirt + 0.35 * rust, 0.2, 0.95)
    normal = normal_from_height(hgt, 9.0)
    ao = np.clip(1 - 0.35 * (1 - lug) * smooth(0.05, -0.01, dist + 0.04) - 0.2 * dirt, 0, 1)
    orm = np.stack([ao, rough, metal], -1)
    folder = os.path.join(TEX, "chequer")
    os.makedirs(folder, exist_ok=True)
    save(to_img(col), "albedo.jpg", folder)
    save(to_img(normal * 255.0), "normal.png", folder)
    save(to_img(orm * 255.0), "orm.jpg", folder)


# =================================================================================================
# 3. interlock plate (W1 / W1b rule, no words)
# =================================================================================================
def _key_picto(pen: Pen, cx, top, kind, h=150.0, v=255, hollow=False, bow_h=None):
    """Castell-style key standing bow up: shaped bow (kind) with a ring hole, collar, shank, flag bit (right)."""
    bh = bow_h or h * 0.36
    bcy = top + bh / 2
    m = shape_mask(kind, pen.w, pen.h, cx, bcy, bh) if kind else None
    if kind:
        ss = pen.ss
        img = Image.fromarray((m * 255).astype(np.uint8)).resize((pen.w * ss, pen.h * ss), Image.BILINEAR)
        pen.im.paste(v, (0, 0), img) if v else None
        if hollow:
            inner = shape_mask(kind, pen.w, pen.h, cx, bcy, bh * 0.62)
            pen.im.paste(0, (0, 0), Image.fromarray((inner * 255).astype(np.uint8)).resize((pen.w * ss, pen.h * ss)))
    pen.circle(cx, bcy, bh * 0.10, 0)                               # ring hole
    sw = h * 0.075
    y0 = top + bh * (0.92 if kind != "triangle" else 1.0)
    pen.rect(cx - sw * 1.1, y0 - 2, cx + sw * 1.1, y0 + h * 0.05, v, radius=2)       # collar
    pen.rect(cx - sw / 2, y0, cx + sw / 2, top + h, v, radius=2)                      # shank
    by = top + h * 0.80
    pen.rect(cx, by, cx + h * 0.20, top + h * 0.97, v, radius=2)                       # flag bit
    pen.rect(cx + h * 0.09, by + h * 0.06, cx + h * 0.13, top + h * 0.97 + 1, 0)      # ward cut


def interlock_plate():
    W, H = 1024, 512
    rng = np.random.default_rng(3400)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = D2.solid(H, W, "#E6DCC3")
    base = base * (0.97 + 0.05 * fbm(H, W, 140, 3401, 4))[..., None]
    base = base * (1 - 0.06 * smooth(0.6, 1.0, np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))))[..., None]
    pr = Pen(W, H, 4)                    # dark print
    red = Pen(W, H, 4)                   # red arrows / accents
    # borders: outer rule + inner fine rule, and the division between the rows
    pr.rect(14, 14, W - 14, H - 14, 255, radius=18, outline=7)
    pr.rect(26, 26, W - 26, H - 26, 255, radius=12, outline=2)
    pr.rect(40, 262, W - 40, 265, 255)
    # ---- top row: ◆ -> ▲ -> ● -> ■ -> door
    xs = [118, 292, 466, 640]
    for x, k in zip(xs, S.KEY_SHAPES):
        _key_picto(pr, x, 52, k, h=178)
    for xa in xs:
        arrow(red, (xa + 52, 136), (xa + 122, 136), 9, 26)
    # door: frame, leaf, panel lines, handle, keyhole
    dx0, dy0, dx1, dy1 = 790, 50, 910, 236
    pr.rect(dx0 - 12, dy0 - 10, dx1 + 12, dy1, 255, radius=3, outline=8)
    pr.rect(dx0, dy0, dx1, dy1, 255, radius=2)
    pr.rect(dx0 + 14, dy0 + 14, dx1 - 14, dy0 + 82, 0, radius=3)     # glazed upper panel
    pr.rect(dx0 + 22, dy0 + 22, dx1 - 22, dy0 + 74, 255, radius=2)
    pr.rect(dx0 + 14, dy0 + 96, dx1 - 14, dy1 - 14, 0, radius=3, outline=4)
    pr.circle(dx1 - 22, dy0 + 112, 7, 0)
    pr.rect(dx1 - 25, dy0 + 120, dx1 - 19, dy0 + 134, 0)
    red_sq = shape_mask("square", W, H, dx1 - 22, dy0 + 152, 18)
    # ---- bottom row: three rule panels
    panels = [(58, 292, 338, 486), (372, 292, 652, 486), (686, 292, 966, 486)]
    for (x0, y0, x1, y1) in panels:
        pr.rect(x0, y0, x1, y1, 255, radius=14, outline=4)
    for (x0, y0, x1, y1), (nx0, _, _, _) in zip(panels[:-1], panels[1:]):
        arrow(red, (x1 + 4, 389), (nx0 - 4, 389), 8, 22)
    # panel 1: a key going down into a lock face (plate with a shaped keyhole surround)
    cx = 198
    pr.rect(cx - 70, 400, cx + 70, 470, 255, radius=8)                       # lock face
    pr.rect(cx - 58, 412, cx + 58, 458, 0, radius=6)
    pr.rect(cx - 44, 420, cx + 44, 450, 255, radius=4)                       # ledge
    pr.rect(cx - 5, 426, cx + 5, 444, 0, radius=2)                           # slot
    _key_picto(pr, cx - 6, 300, "circle", h=92, hollow=True)
    arrow(red, (cx + 52, 306), (cx + 52, 386), 7, 20)
    # panel 2: isolator dial: I at 12, O at 9, bar handle turned to O, curved arrow I -> O (anticlockwise)
    cx, cy, r = 512, 402, 52
    pr.ring(cx, cy, r, 5)
    pr.rect(cx - 4, cy - r - 28, cx + 4, cy - r - 8, 255)                       # I at 12 o'clock
    pr.ring(cx - r - 24, cy, 11, 5)                                             # O at 9 o'clock
    pr.line([(cx + 30, cy), (cx - 44, cy)], 20, 255, caps=True)                 # bar handle turned to O
    pr.circle(cx, cy, 18, 255)
    pr.circle(cx, cy, 5, 0)
    arc_arrow(red, cx, cy, r + 44, -78, -158, 7, 20)                            # I -> O, anticlockwise
    # panel 3: key window box with the flap swung open, the next key coming out
    cx = 826
    pr.rect(cx - 74, 318, cx + 4, 462, 255, radius=8)                          # box
    pr.rect(cx - 62, 346, cx - 8, 450, 0, radius=4)                            # opening
    pr.line([(cx - 74, 318), (cx - 112, 300)], 6, 255)                         # flap hinged on top, swung out
    pr.line([(cx - 4, 318), (cx - 40, 296)], 6, 255)
    pr.line([(cx - 112, 300), (cx - 40, 296)], 4, 255)
    _key_picto(pr, cx + 52, 330, "square", h=104)
    arrow(red, (cx - 36, 398), (cx + 26, 398), 7, 20)
    # compose
    ink_a = np.maximum(pr.arr(), 0)
    ink_a = ink_a * (0.92 + 0.08 * noise(H, W, 2.0, 2, 3402))
    red_a = red.arr()
    rgb = base * (1 - ink_a[..., None]) + hexf(INK_PRINT) * ink_a[..., None]
    rgb = rgb * (1 - red_a[..., None]) + hexf("#9C2B22") * red_a[..., None]
    rgb = rgb * (1 - red_sq[..., None]) + hexf("#E6DCC3") * red_sq[..., None]      # the ■ on the door lock
    # enamel chips (dark steel with a rust halo) along the edges and at the corners, grime
    chip = Pen(W, H, 2)
    for _ in range(9):
        side = rng.integers(0, 4)
        if side == 0:
            px, py = rng.uniform(0, W), rng.uniform(0, 12)
        elif side == 1:
            px, py = rng.uniform(0, W), H - rng.uniform(0, 12)
        elif side == 2:
            px, py = rng.uniform(0, 12), rng.uniform(0, H)
        else:
            px, py = W - rng.uniform(0, 12), rng.uniform(0, H)
        pts = [(px + rng.uniform(2, 8) * math.cos(a), py + rng.uniform(2, 8) * math.sin(a))
               for a in np.linspace(0, math.tau, 9, endpoint=False)]
        chip.poly(pts)
    for (px, py) in ((10, 10), (W - 10, 10), (10, H - 10), (W - 10, H - 10)):
        chip.circle(px + rng.normal(0, 2), py + rng.normal(0, 2), rng.uniform(6, 11))
    ch = blur(chip.arr(), 0.6)
    halo = np.clip(blur(ch, 4.0) * 1.6 - ch, 0, 1)
    rgb = rgb * (1 - 0.5 * halo[..., None]) + hexf("#7A4A26") * (0.5 * halo)[..., None]
    rgb = rgb * (1 - ch[..., None]) + hexf("#2A2B2D") * ch[..., None]
    grime = smooth(0.55, 0.95, fbm(H, W, 120, 3403, 4)) * 0.10 + 0.08 * smooth(0.6, 1.0, np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)))
    rgb = rgb * (1 - grime[..., None])
    save(to_img(rgb), "interlock_plate.png", OUT)


# =================================================================================================
# 4. ECG paper (W2), no trace
# =================================================================================================
ECG_W, ECG_H = 2048, 320
ECG_PX_MM = ECG_W / 320.0          # 0.32 m strip
BRACKETS = [(0.06, 0.32), (0.38, 0.62), (0.68, 0.94)]
BRACKET_SYMS = ["sun", "moon", "star"]
ECG_BASE_V = 0.30                  # suggested trace baseline (v, bottom -> top); the trace band is v 0.06 .. 0.58


def ecg_paper_rgb(seed=3500):
    W, H = ECG_W, ECG_H
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rgb = D2.solid(H, W, "#F3CDBB") * (0.97 + 0.05 * fbm(H, W, 90, seed + 1, 3))[..., None]
    p = ECG_PX_MM
    gx = np.abs(((xx + 0.5) / p + 0.5) % 1.0 - 0.5) * p
    gy = np.abs(((H - yy - 0.5) / p + 0.5) % 1.0 - 0.5) * p
    minor = np.maximum(smooth(0.9, 0.2, gx), smooth(0.9, 0.2, gy))
    Gx = np.abs(((xx + 0.5) / (5 * p) + 0.5) % 1.0 - 0.5) * 5 * p
    Gy = np.abs(((H - yy - 0.5) / (5 * p) + 0.5) % 1.0 - 0.5) * 5 * p
    major = np.maximum(smooth(1.5, 0.5, Gx), smooth(1.5, 0.5, Gy))
    rgb = rgb * (1 - 0.30 * minor[..., None]) + hexf("#E99A84") * (0.30 * minor)[..., None]
    rgb = rgb * (1 - 0.62 * major[..., None]) + hexf("#D9654E") * (0.62 * major)[..., None]
    # printed 1 s marks along the top edge (every 25 mm)
    pm = Pen(W, H, 2)
    for k in range(13):
        x = (k * 25 + 10) * p
        pm.rect(x - 1.2, 0, x + 1.2, 10, 255)
    pmk = pm.arr()
    rgb = rgb * (1 - 0.8 * pmk[..., None]) + hexf("#B4473A") * (0.8 * pmk)[..., None]
    # pen brackets and the three symbols above them (blue-black fountain pen, hand-drawn)
    ink = Pen(W, H, 3)
    yb = (1 - 0.70) * H
    for bi, ((u0, u1), sym) in enumerate(zip(BRACKETS, BRACKET_SYMS)):
        x0, x1 = u0 * W, u1 * W
        wobble_line(ink, (x0 + rng.normal(0, 1), yb + rng.normal(0, 1)), (x1 + rng.normal(0, 1), yb + rng.normal(0, 1)),
                    3.4, rng, amp=1.3, n=40)
        for xe in (x0, x1):
            wobble_line(ink, (xe, yb - 1), (xe + rng.normal(0, 1.5), yb + 0.085 * H), 3.2, rng, amp=0.6, n=8)
        m = shape_mask(sym, W, H, (x0 + x1) / 2 + rng.normal(0, 3), 0.19 * H, 0.15 * H, rot_deg=rng.normal(0, 4),
                       jitter=0.9, seed=3510 + bi)
        ink.im.paste(220, (0, 0), Image.fromarray((m * 255).astype(np.uint8)).resize((W * 3, H * 3), Image.BILINEAR))
    ia = ink_tex(ink.arr(), seed + 2)
    rgb = rgb * (1 - 0.92 * ia[..., None]) + hexf(INK_PEN) * (0.92 * ia)[..., None]
    rgb = rgb * (1 - 0.10 * D2.edge_wear(W, H, seed + 3, width=14, amount=1.0)[..., None])
    return rgb


def ecg_paper():
    save(to_img(ecg_paper_rgb()), "ecg_paper.png", OUT)


def ecg_trace_mask(peaks, W=ECG_W, H=ECG_H, base_v=ECG_BASE_V, amp_v=0.27):
    """Seed-0 emulation of ecg_trace.gdshader: peaks[b] QRS complexes evenly inside bracket b, one in each gap
    and one at each end, low P / T waves everywhere."""
    beats = []
    edges = [(0.0, BRACKETS[0][0])] + [(BRACKETS[i][1], BRACKETS[i + 1][0]) for i in range(2)] + [(BRACKETS[2][1], 1.0)]
    for a, b in edges:
        beats.append((a + b) / 2)
    for (u0, u1), n in zip(BRACKETS, peaks):
        for k in range(n):
            beats.append(u0 + (u1 - u0) * (k + 0.5) / n)
    beats.sort()
    us = np.linspace(0, 1, W * 3)
    y = np.zeros_like(us)
    for c in beats:
        d = (us - c) * 320.0                                   # mm
        y += 1.00 * np.exp(-(d / 0.9) ** 2) - 0.22 * np.exp(-((d - 1.4) / 0.8) ** 2) - 0.12 * np.exp(-((d + 1.2) / 0.6) ** 2)
        y += 0.12 * np.exp(-((d + 5.0) / 1.6) ** 2) + 0.18 * np.exp(-((d - 7.5) / 2.4) ** 2)
    y += 0.02 * np.sin(us * 160)
    pen = Pen(W, H, 2)
    pts = [(u * W, (1 - (base_v + amp_v * yy)) * H) for u, yy in zip(us, y)]
    for i in range(0, len(pts) - 1, 400):
        pen.line(pts[i:i + 401], 2.6, 255, caps=True)
    return pen.arr()


# =================================================================================================
# 5. chalk grid (W3)
# =================================================================================================
CHALK_W, CHALK_H = 1024, 352


def chalk_u(k):
    return ((k - 3) * 0.34 + 1.30) / 2.60


def chalk_v(h):
    return (0.10 + 0.12 * (h - 1)) / 0.90


def chalk_grid_alpha(seed=3600):
    W, H = CHALK_W, CHALK_H
    rng = np.random.default_rng(seed)
    pen = Pen(W, H, 3)
    for h in range(1, 8):
        y = (1 - chalk_v(h)) * H
        x0, x1 = 0.035 * W + rng.normal(0, 3), 0.965 * W + rng.normal(0, 3)
        wobble_line(pen, (x0, y + rng.normal(0, 0.8)), (x1, y + rng.normal(0, 0.8)), 3.2, rng, amp=1.4, n=60,
                    v=int(255 * rng.uniform(0.75, 0.95)))
    for k in range(7):
        x = chalk_u(k) * W
        wobble_line(pen, (x + rng.normal(0, 1), (1 - 0.068) * H), (x + rng.normal(0, 1), (1 - 0.020) * H), 3.6, rng,
                    amp=0.5, n=6)
    a = chalk_tex(pen.arr(), seed + 1, 0.55) * 0.62
    # dusty haze where the chalk was rubbed
    a = np.maximum(a, 0.05 * smooth(0.6, 0.9, fbm(H, W, 60, seed + 2, 3)))
    return a


def chalk_grid():
    a = chalk_grid_alpha()
    rgb = np.full((CHALK_H, CHALK_W, 3), 238.0, np.float32) * np.array([1.0, 0.985, 0.95], np.float32)
    save(to_img(rgb, a), "chalk_grid.png", OUT)


# =================================================================================================
# 6. growth grid (E2) and the log page (E1)
# =================================================================================================
GG_W, GG_H = 768, 1024


def gg_line_v(level):
    return 0.12 + 0.13 * (level - 1)


def gg_stage_u(s):
    return 0.12 + 0.27 * s, 0.39 + 0.27 * s


def _picto_flame(pen: Pen, cx, cy, s, v=255):
    """Teardrop flame with an inner tongue cut out."""
    def drop(sc, dy):
        tip = (cx, cy - 0.46 * s * sc + dy)
        bc = (cx, cy + 0.14 * s * sc + dy)
        r = 0.27 * s * sc
        right = D2._bez(tip, (cx + 0.30 * s * sc, cy - 0.12 * s * sc + dy), (bc[0] + r, bc[1]), 12)
        bottom = [(bc[0] + r * math.cos(a), bc[1] + r * math.sin(a)) for a in np.linspace(0, math.pi, 14)[1:-1]]
        left = D2._bez((bc[0] - r, bc[1]), (cx - 0.30 * s * sc, cy - 0.12 * s * sc + dy), tip, 12)
        return right + bottom + left
    pen.poly(drop(1.0, 0.0), v)
    pen.poly(drop(0.45, 0.16 * s), 0)


def _picto_crystal(pen: Pen, cx, cy, s, v=255):
    w, h = 0.22 * s, 0.75 * s
    pen.poly([(cx, cy - h / 2 - 0.12 * s), (cx + w, cy - h / 2 + 0.08 * s), (cx + w, cy + h / 2), (cx - w, cy + h / 2),
              (cx - w, cy - h / 2 + 0.08 * s)], v)
    pen.line([(cx, cy - h / 2 - 0.08 * s), (cx, cy + h / 2 - 0.04 * s)], max(1.5, 0.035 * s), 0)


def _picto_seed(pen: Pen, cx, cy, s, v=255):
    pts = [(cx + 0.20 * s * math.cos(math.radians(60 * k)), cy + 0.20 * s * math.sin(math.radians(60 * k))) for k in range(6)]
    pen.poly(pts, v)
    pen.ring(cx, cy, 0.32 * s, max(1.5, 0.05 * s), v)


def growth_grid_rgb(seed=3700):
    W, H = GG_W, GG_H
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rgb = paper(W, H, base=(228, 224, 206), seed=seed, stains=2, vignette=0.18)
    px_cm = W / 60.0
    gx = np.abs(((xx + 0.5) / px_cm + 0.5) % 1.0 - 0.5) * px_cm
    gy = np.abs(((H - yy - 0.5) / px_cm + 0.5) % 1.0 - 0.5) * px_cm
    g1 = np.maximum(smooth(0.9, 0.2, gx), smooth(0.9, 0.2, gy))
    Gx = np.abs(((xx + 0.5) / (5 * px_cm) + 0.5) % 1.0 - 0.5) * 5 * px_cm
    Gy = np.abs(((H - yy - 0.5) / (5 * px_cm) + 0.5) % 1.0 - 0.5) * 5 * px_cm
    g5 = np.maximum(smooth(1.4, 0.4, Gx), smooth(1.4, 0.4, Gy))
    rgb = rgb * (1 - 0.18 * g1[..., None]) + hexf("#7FA4A0") * (0.18 * g1)[..., None]
    rgb = rgb * (1 - 0.35 * g5[..., None]) + hexf("#5E8E88") * (0.35 * g5)[..., None]
    rng = np.random.default_rng(seed + 1)
    ink = Pen(W, H, 3)
    pencil = Pen(W, H, 3)
    ax_u, ax_v = 0.10, 0.085
    X = lambda u: u * W            # noqa: E731
    Y = lambda v: (1 - v) * H      # noqa: E731
    # axes with arrow heads
    wobble_line(ink, (X(ax_u), Y(ax_v)), (X(ax_u), Y(0.905)), 3.0, rng, amp=0.8)
    ink.poly([(X(ax_u), Y(0.935)), (X(ax_u) - 9, Y(0.900)), (X(ax_u) + 9, Y(0.900))])
    wobble_line(ink, (X(ax_u), Y(ax_v)), (X(0.955), Y(ax_v)), 3.0, rng, amp=0.8)
    ink.poly([(X(0.985), Y(ax_v)), (X(0.950), Y(ax_v) - 9), (X(0.950), Y(ax_v) + 9)])
    # six level lines (ruled in ink), ticks and hand-written level numbers
    for lv in range(1, 7):
        y = Y(gg_line_v(lv))
        wobble_line(ink, (X(ax_u) - 8, y), (X(0.93), y + rng.normal(0, 0.6)), 2.2, rng, amp=0.5)
        rot_text(ink, X(0.062), y, str(lv), F_HAND, 34, angle=rng.normal(0, 3), weight=560)
    # stage columns (dashed pencil) and their pictograms
    for s in range(3):
        u0, u1 = gg_stage_u(s)
        for ub in (u0, u1):
            if ub <= ax_u + 0.03:
                continue
            for k in range(26):
                v0 = ax_v + 0.03 * k
                if v0 > 0.86:
                    break
                wobble_line(pencil, (X(ub), Y(v0)), (X(ub), Y(min(v0 + 0.016, 0.86))), 1.8, rng, amp=0.2, n=3)
        cx = X((u0 + u1) / 2)
        [_picto_seed, _picto_flame, _picto_crystal][s](ink, cx, Y(0.040), 46)
    ia = ink_tex(ink.arr(), seed + 2)
    pa = pencil_tex(pencil.arr(), seed + 3) * 0.7
    rgb = rgb * (1 - 0.9 * ia[..., None]) + hexf(INK_PEN) * (0.9 * ia)[..., None]
    rgb = rgb * (1 - pa[..., None]) + hexf(GRAPHITE) * pa[..., None]
    return rgb


def growth_grid():
    save(to_img(growth_grid_rgb()), "growth_grid.png", OUT)


def growth_curve_mask(levels, W=GG_W, H=GG_H, seed=3750):
    """Seed-0 emulation of growth_curve.gdshader: rise from the axis to level 0, hold, step, hold, step, hold,
    fall. Pencil-ink line with a slight hand wobble."""
    rng = np.random.default_rng(seed)
    X = lambda u: u * W            # noqa: E731
    Y = lambda v: (1 - v) * H      # noqa: E731
    pts = [(0.10, 0.085)]
    for s, lv in enumerate(levels):
        u0, u1 = gg_stage_u(s)
        v = gg_line_v(lv)
        pts += [(u0 + 0.015, v), (u1 - 0.015, v)]
    pts += [(0.95, 0.085)]
    sm = []
    for (u, v) in pts:
        sm.append((X(u), Y(v)))
    pen = Pen(W, H, 3)
    for a, b in zip(sm[:-1], sm[1:]):
        wobble_line(pen, a, b, 5.0, rng, amp=1.2, n=30)
    return ink_tex(pen.arr(), seed + 1, 0.3)


LOG_W, LOG_H = 768, 1024
LOG_SQ = (0.22, 0.78, 0.15, 0.57)          # u0, u1, v0, v1 of the blank sketch square
LOG_C = (0.50, 0.36)
LOG_PX_M = LOG_W / 0.21                     # 3657 px per metre


def growth_log(lang="en"):
    W, H = LOG_W, LOG_H
    rng = np.random.default_rng(3800)
    rgb = paper(W, H, base=(226, 218, 196), seed=3801, stains=3, vignette=0.22)
    X = lambda u: u * W            # noqa: E731
    Y = lambda v: (1 - v) * H      # noqa: E731
    sx0, sx1, sy0, sy1 = X(LOG_SQ[0]), X(LOG_SQ[1]), Y(LOG_SQ[3]), Y(LOG_SQ[2])
    # printed notebook rules (light blue) every 8 mm, red margin; the sketch square stays blank
    rules = Pen(W, H, 2)
    step = 0.008 * LOG_PX_M
    y = 0.075 * H
    while y < H - 20:
        if not (sy0 - 12 < y < sy1 + 12):
            rules.rect(0, y - 0.8, W, y + 0.8, 255)
        else:
            rules.rect(0, y - 0.8, sx0 - 18, y + 0.8, 255)
            rules.rect(sx1 + 18, y - 0.8, W, y + 0.8, 255)
        y += step
    ra = rules.arr()
    rgb = rgb * (1 - 0.35 * ra[..., None]) + hexf("#7C9CC4") * (0.35 * ra)[..., None]
    mg = Pen(W, H, 2)
    mg.rect(0.115 * W - 1, 0, 0.115 * W + 1, H, 255)
    ma = mg.arr()
    rgb = rgb * (1 - 0.45 * ma[..., None]) + hexf("#C2645C") * (0.45 * ma)[..., None]
    # Leyla's hand: date (numerals only) and doc3.growth_log
    ink = Pen(W, H, 3)
    rot_text(ink, W - 150, 0.115 * H, "14.III.1998", F_HAND, 40, angle=-2, weight=520)
    lines = hand_lines(t("doc3.growth_log", lang), F_HAND, 52, W * 0.74, weight=520)
    y0 = 0.205 * H
    for i, ln in enumerate(lines[:4]):
        tw = text_width(ln, F_HAND, 52, 0.0, 520)
        rot_text(ink, 0.135 * W + tw / 2 + rng.normal(0, 4), y0 + i * 0.0545 * H, ln, F_HAND, 52,
                 angle=rng.normal(-1.0, 0.8), weight=520)
    ia = ink_tex(ink.arr(), 3802)
    rgb = rgb * (1 - 0.9 * ia[..., None]) + hexf(INK_PEN) * (0.9 * ia)[..., None]
    # pencil: the ruled sketch square and the clockwise one-third-turn arrow (r = 0.050 m) around its centre
    pc = Pen(W, H, 3)
    for (a, b) in (((sx0, sy0), (sx1, sy0)), ((sx1, sy0), (sx1, sy1)), ((sx1, sy1), (sx0, sy1)), ((sx0, sy1), (sx0, sy0))):
        wobble_line(pc, a, b, 2.4, rng, amp=0.6)
    cx, cy = X(LOG_C[0]), Y(LOG_C[1])
    r = 0.050 * LOG_PX_M
    arc_arrow(pc, cx, cy, r, -90.0, 30.0, 4.6, 26)
    for a in (-90.0, 30.0):                            # tick marks at the start and the end of the third
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        pc.line([(cx + (r - 14) * ca, cy + (r - 14) * sa), (cx + (r + 14) * ca, cy + (r + 14) * sa)], 2.6, 200)
    pa = pencil_tex(pc.arr(), 3803, 0.35)
    rgb = rgb * (1 - 0.85 * pa[..., None]) + hexf(GRAPHITE) * (0.85 * pa)[..., None]
    rgb = rgb * (1 - 0.12 * D2.edge_wear(W, H, 3804, width=26, amount=1.0)[..., None])
    save(to_img(rgb), lname("growth_log.png", lang), OUT)


def strand_note(lang="en"):
    W, H = 512, 384
    rng = np.random.default_rng(3900)
    rgb = paper(W, H, base=(224, 212, 184), seed=3901, stains=2, vignette=0.3)
    # a printed hairline under the top edge (his memo pad)
    pr = Pen(W, H, 2)
    pr.rect(26, 40, W - 26, 41.5, 255)
    pa = pr.arr()
    rgb = rgb * (1 - 0.4 * pa[..., None]) + hexf("#8A7A62") * (0.4 * pa)[..., None]
    ink = Pen(W, H, 3)
    size = 66
    lines = hand_lines(t("doc3.note", lang), F_HAND, size, W * 0.80, weight=650)
    while len(lines) > 3:
        size -= 4
        lines = hand_lines(t("doc3.note", lang), F_HAND, size, W * 0.80, weight=650)
    y0 = H * (0.42 if len(lines) <= 2 else 0.34)
    for i, ln in enumerate(lines):
        m0 = D2.text_mask(ln, F_HAND, size, ink.ss, 650)
        ex = int(0.3 * m0.size[1])
        m = Image.new("L", (m0.size[0] + 2 * ex, m0.size[1]), 0)
        m.paste(m0, (ex, 0))
        m = m.transform(m.size, Image.AFFINE, (1, 0.28, -0.14 * m.size[1], 0, 1, 0), resample=Image.BICUBIC)   # forward slant
        tw = text_width(ln, F_HAND, size, 0.0, 650)
        ink.paste_rotated(m, 40 + tw / 2 + rng.normal(0, 3) + i * 14, y0 + i * size * 1.05, rng.normal(3.0, 0.8))
    rot_text(ink, W - 110, H - 60, t("initial_s", lang), F_HAND, 54, angle=4, weight=700)
    ia = ink_tex(ink.arr(), 3902, 0.28)
    rgb = rgb * (1 - 0.92 * ia[..., None]) + hexf("#2A2220") * (0.92 * ia)[..., None]
    # an ink blot by the signature
    bl = Pen(W, H, 2)
    bl.circle(W - 58, H - 88, 5.5)
    rgb = rgb * (1 - 0.8 * blur(bl.arr(), 0.8)[..., None]) + hexf("#2A2220") * (0.8 * blur(bl.arr(), 0.8))[..., None]
    rgb = rgb * (1 - 0.14 * D2.edge_wear(W, H, 3903, width=18, amount=1.0)[..., None])
    save(to_img(rgb), lname("strand_note.png", lang), OUT)


# =================================================================================================
# 7. QA previews of the shader quads (seed 0), qa/blender/ch3/preview/
# =================================================================================================
def hex_glyph_loop(bits: str, cx, cy, R, notch_w=0.30, notch_d=0.22):
    """Flat-topped hexagon (circumradius R) with V-notches: edge e runs clockwise from the top, outward normal at
    90° - 60° e (counter-clockwise from +u). Image coordinates (y down)."""
    ap = R * math.sqrt(3) / 2
    pts = []
    for e in range(6):
        na = math.radians(90 - 60 * e)
        a0, a1 = na + math.radians(30), na - math.radians(30)      # clockwise traversal (math coords)
        p0 = (R * math.cos(a0), R * math.sin(a0))
        p1 = (R * math.cos(a1), R * math.sin(a1))
        pts.append(p0)
        if bits[e] == "1":
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            tx, ty = (p1[0] - p0[0]) / R, (p1[1] - p0[1]) / R
            nx, ny = math.cos(na), math.sin(na)
            hw, d = notch_w * R / 2, notch_d * ap
            pts += [(mx - tx * hw, my - ty * hw), (mx - nx * d, my - ny * d), (mx + tx * hw, my + ty * hw)]
    return [(cx + x, cy - y) for (x, y) in pts]


def hex_glyph(bits: str, size: int, style: int, seed: int = 0) -> Image.Image:
    """style 0 = engraved enamel plate (cream hex with a dark engraved inner contour), 1 = pencil sketch. RGBA,
    alpha 0 outside the hexagon (style 1: only the pencil lines)."""
    R = 0.42 * size
    loop = hex_glyph_loop(bits, size / 2, size / 2, R)
    if style == 0:
        pen = Pen(size, size, 4)
        pen.poly(loop)
        m = pen.arr()
        inner = hex_glyph_loop(bits, size / 2, size / 2, R * 0.86)
        ln = Pen(size, size, 4)
        ln.line(inner + [inner[0]], max(2.0, size * 0.018), 255)
        edge = np.clip(m - blur(m, size * 0.012), 0, 1)
        rgb = D2.solid(size, size, "#E4DBC2") * (0.96 + 0.06 * noise(size, size, 18, 2, seed))[..., None]
        rgb = rgb * (1 - 0.35 * edge[..., None])
        la = ln.arr()
        rgb = rgb * (1 - 0.9 * la[..., None]) + hexf("#20242A") * (0.9 * la)[..., None]
        return to_img(rgb, m)
    pen = Pen(size, size, 4)
    rng = np.random.default_rng(seed)
    pts = loop + [loop[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        wobble_line(pen, a, b, max(2.0, size * 0.014), rng, amp=size * 0.002, n=6)
    # faint lattice hatching inside (Leyla's habit)
    for k in range(-3, 4):
        x = size / 2 + k * R * 0.22
        pen.line([(x - R * 0.2, size / 2 - R * 0.6), (x + R * 0.2, size / 2 + R * 0.6)], 1.2, 70)
    a = pencil_tex(pen.arr(), seed + 1, 0.3)
    clip = Pen(size, size, 2)
    clip.poly(loop)
    c = blur(clip.arr(), 1.0)
    a = np.maximum(a * np.clip(c * 3, 0, 1), 0)
    rgb = D2.solid(size, size, GRAPHITE)
    return to_img(rgb, np.clip(a * 0.9, 0, 1))


def preview_glyph_panel():
    cell = 256
    im = Image.new("RGBA", (4 * cell, 3 * cell), (0, 0, 0, 0))
    for i, bits in enumerate(SEED_GLYPHS):
        r, c = divmod(i, 4)
        g = hex_glyph(bits, cell, 0, seed=4000 + i)
        im.alpha_composite(g, (c * cell, r * cell))
    save(im, "glyph_panel.png", PREVIEW)
    save(hex_glyph(SEED_GLYPHS[6], 256, 0, seed=4006), "glyph_open.png", PREVIEW)


def preview_log_sketch():
    save(hex_glyph(SEED_SKETCH, 256, 1, seed=4100), "log_sketch.png", PREVIEW)
    # the page with the sketch composed at its place (what the growth_log view shows)
    page = Image.open(os.path.join(OUT, "growth_log.png")).convert("RGBA")
    q = 0.09 * LOG_PX_M
    sk = hex_glyph(SEED_SKETCH, int(round(q)), 1, seed=4100)
    page.alpha_composite(sk, (int(LOG_C[0] * LOG_W - q / 2), int((1 - LOG_C[1]) * LOG_H - q / 2)))
    save(page.convert("RGB"), "growth_log_composed.jpg", PREVIEW)


def preview_stair_quad():
    a = chalk_grid_alpha()
    W, H = CHALK_W, CHALK_H
    pen = Pen(W, H, 3)
    rng = np.random.default_rng(4200)
    for k, hgt in enumerate(CHOIR_TARGET):
        x, y = chalk_u(k) * W, (1 - chalk_v(hgt)) * H
        pts = [(x + 15 * math.cos(q) + rng.normal(0, 1.2), y + 15 * math.sin(q) + rng.normal(0, 1.2))
               for q in np.linspace(0, math.tau, 14, endpoint=False)]
        pen.poly(pts)
    d = chalk_tex(pen.arr(), 4201, 0.45) * 0.95
    a = np.maximum(a, d)
    rgb = np.full((H, W, 3), 238.0, np.float32)
    save(to_img(rgb, a), "stair_quad.png", PREVIEW)


def preview_strip_face():
    rgb = ecg_paper_rgb()
    tr = ecg_trace_mask(CASE_CODE)
    tr = ink_tex(tr, 4300, 0.15)
    rgb = rgb * (1 - 0.95 * tr[..., None]) + hexf("#1D1B22") * (0.95 * tr)[..., None]
    save(to_img(rgb), "strip_face.png", PREVIEW)


def preview_chart_image():
    rgb = growth_grid_rgb()
    m = growth_curve_mask(PEGS_TARGET)
    rgb = rgb * (1 - 0.92 * m[..., None]) + hexf("#24264A") * (0.92 * m)[..., None]
    save(to_img(rgb), "chart_image.png", PREVIEW)


def _add_colour(mask):
    return np.array([255.0 if mask & RED else 0.0, 255.0 if mask & GREEN else 0.0, 255.0 if mask & BLUE else 0.0],
                    np.float32)


def receptor_image(rim: int, light: int, size: int = 256) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.hypot(xx + 0.5 - size / 2, yy + 0.5 - size / 2) / size
    disc = smooth(0.502, 0.495, r)
    ring = smooth(0.375, 0.385, r) * disc
    centre = smooth(0.385, 0.375, r)
    rgb = D2.solid(size, size, "#1A1C1E")
    rimc = _add_colour(rim) * 0.78
    rgb = rgb * (1 - ring[..., None]) + rimc * ring[..., None]
    if light:
        lc = _add_colour(light)
        glow = centre * (0.75 + 0.25 * smooth(0.38, 0.0, r))
        rgb = rgb * (1 - glow[..., None]) + lc * glow[..., None]
    bits = [(RED, "triangle"), (GREEN, "circle"), (BLUE, "square")]
    rim_syms = [k for b, k in bits if rim & b]
    for i, k in enumerate(rim_syms):
        ang = math.radians(90 - (i - (len(rim_syms) - 1) / 2) * 34)
        m = shape_mask(k, size, size, size / 2 + 0.44 * size * math.cos(ang), size / 2 - 0.44 * size * math.sin(ang),
                       0.075 * size)
        rgb = rgb * (1 - m[..., None]) + hexf("#EDE4CC") * m[..., None]
    in_syms = [k for b, k in bits if light & b]
    for i, k in enumerate(in_syms):
        m = shape_mask(k, size, size, size / 2 + (i - (len(in_syms) - 1) / 2) * 0.17 * size, size / 2, 0.12 * size)
        rgb = rgb * (1 - m[..., None]) + hexf("#F4EEDC") * m[..., None]
    return to_img(rgb, disc)


def receptor_light(p, q):
    r = [0, 0, 0]
    for k in range(3):
        if 0 <= p + k < 3:
            r[p + k] |= P_BANDS[k]
        if 0 <= q + k < 3:
            r[q + k] |= Q_BANDS[k]
    return r


def preview_receptors():
    light = receptor_light(PRISM_START, PRISM_START)
    for i in range(3):
        save(receptor_image(RIMS[i], light[i]), f"receptor_{i}.png", PREVIEW)
    sol = receptor_light(0, -1)
    for i in range(3):
        save(receptor_image(RIMS[i], sol[i]), f"receptor_{i}_solved.png", PREVIEW)


def lissajous_pts(a, b, cx, cy, rx, ry, n=2400):
    return [(cx + rx * math.sin(a * tt + math.pi / 2), cy - ry * math.sin(b * tt))
            for tt in np.linspace(0, math.tau, n)]


def preview_strand_plate():
    W, H = 576, 448                                   # 0.18 x 0.14 m
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    brush = noise(H, W * 8, 2.0, 2, 4400)[:, ::8]
    rgb = D2.solid(H, W, "#B08D57") * (0.88 + 0.16 * brush + 0.08 * fbm(H, W, 120, 4401, 3))[..., None]
    pts = lissajous_pts(FREQ[0], FREQ[1], W / 2, H / 2, W * 0.36, H * 0.36)
    g = Pen(W, H, 3)
    for i in range(0, len(pts) - 1, 300):
        g.line(pts[i:i + 301], 7.0, 255, caps=True)
    groove = g.arr()
    hl = np.roll(np.roll(groove, -2, 0), -2, 1)
    rgb = rgb * (1 - 0.75 * groove[..., None]) + hexf("#2B2116") * (0.75 * groove)[..., None]
    rgb = rgb + (hexf("#F3D9A0") - rgb) * (0.45 * np.clip(hl - groove, 0, 1))[..., None]
    save(to_img(rgb), "strand_plate.png", PREVIEW)


def _crt(W, H, round_=False):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rgb = D2.solid(H, W, "#0B1410")
    vig = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    rgb = rgb * (1.15 - 0.45 * np.clip(vig, 0, 1))[..., None]
    gr = Pen(W, H, 2)
    for k in range(1, 10):
        gr.rect(k * W / 10 - 0.6, 0, k * W / 10 + 0.6, H, 255)
    for k in range(1, 8):
        gr.rect(0, k * H / 8 - 0.6, W, k * H / 8 + 0.6, 255)
    ga = gr.arr()
    rgb = rgb * (1 - 0.25 * ga[..., None]) + hexf("#4E6A5A") * (0.25 * ga)[..., None]
    alpha = None
    if round_:
        alpha = smooth(0.502, 0.49, np.hypot((xx + 0.5 - W / 2) / W, (yy + 0.5 - H / 2) / H))
    return rgb, alpha


def _phosphor(rgb, mask, colour="#7CFFB0"):
    glow = blur(mask, 4.0) * 0.8
    rgb = rgb + hexf("#3AE07A") * glow[..., None] * 0.6
    return rgb * (1 - mask[..., None]) + hexf(colour) * mask[..., None]


def preview_scope_screen():
    W = H = 384
    rgb, al = _crt(W, H, round_=True)
    dot = Pen(W, H, 3)
    dot.circle(W / 2, H / 2, 5)
    save(to_img(np.clip(_phosphor(rgb, dot.arr()), 0, 255), al), "scope_screen.png", PREVIEW)
    rgb, al = _crt(W, H, round_=True)
    p = Pen(W, H, 3)
    pts = lissajous_pts(FREQ[0], FREQ[1], W / 2, H / 2, W * 0.34, H * 0.34)
    for i in range(0, len(pts) - 1, 300):
        p.line(pts[i:i + 301], 3.0, 255, caps=True)
    save(to_img(np.clip(_phosphor(rgb, p.arr()), 0, 255), al), "scope_screen_live.png", PREVIEW)


def preview_osc_screen():
    W, H = 400, 320
    for size in (1, 2, 3, 4):
        cycles = 2 + 2 * (5 - size)
        rgb, _ = _crt(W, H)
        p = Pen(W, H, 3)
        pts = [(x, H / 2 - H * 0.30 * math.sin(math.tau * cycles * x / W) * math.exp(-1.2 * x / W))
               for x in np.linspace(0, W, 1200)]
        for i in range(0, len(pts) - 1, 300):
            p.line(pts[i:i + 301], 2.6, 255, caps=True)
        save(to_img(np.clip(_phosphor(rgb, p.arr()), 0, 255)), f"osc_screen_s{size}.png", PREVIEW)
    first = os.path.join(PREVIEW, f"osc_screen_s{MELODY[0]}.png")
    Image.open(first).save(os.path.join(PREVIEW, "osc_screen.png"))
    print("  wrote", os.path.relpath(os.path.join(PREVIEW, "osc_screen.png"), ROOT), "(= melody note 1, size", MELODY[0], ")")


def preview_ring_symbols():
    """array_below ring_sym_0..3 for v_rings = DRUM_TARGET (☾ ▲ ✦ ●), as composed by the code."""
    target = [1, 3, 2, 4]
    im = Image.new("RGBA", (4 * 256, 256), (0, 0, 0, 255))
    for r, s in enumerate(target):
        k = S.DRUM_ORDER[s]
        m = shape_mask(k, 256, 256, 128, 128, 0.8 * 256)
        g = blur(m, 6.0)
        rgb = np.zeros((256, 256, 3), np.float32) + hexf("#CFF6FF") * np.clip(m + 0.6 * g, 0, 1)[..., None]
        im.paste(to_img(rgb).convert("RGBA"), (r * 256, 0))
    save(im, "ring_symbols.png", PREVIEW)


def previews():
    for fn in (preview_glyph_panel, preview_log_sketch, preview_stair_quad, preview_strip_face, preview_chart_image,
               preview_receptors, preview_strand_plate, preview_scope_screen, preview_osc_screen, preview_ring_symbols):
        fn()


# =================================================================================================
# 8. QA sheets
# =================================================================================================
def _sheet(items, title, path, SW=2400, TH=300):
    PAD, LAB = 18, 50
    tiles = []
    for p in items:
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        th = TH if im.width / im.height < 2.5 else TH * 0.6
        tw = int(im.width * th / im.height)
        if tw > SW - 2 * PAD:
            tw = SW - 2 * PAD
            th = im.height * tw / im.width
        im = im.resize((tw, int(th)), Image.LANCZOS)
        bg = Image.new("RGBA", im.size, (46, 52, 54, 255))
        chk = Pen(im.width, im.height, 1)
        for yy in range(0, im.height, 16):
            for xx in range(0, im.width, 16):
                if (xx // 16 + yy // 16) % 2:
                    chk.d.rectangle([xx, yy, xx + 15, yy + 15], fill=255)
        bg = Image.composite(Image.new("RGBA", im.size, (64, 70, 72, 255)), bg, chk.im)
        bg.alpha_composite(im)
        src = Image.open(p)
        lab = os.path.relpath(p, ROOT).replace("game/assets/textures/", "")
        tiles.append((bg.convert("RGB"), f"{lab}\n{src.width}x{src.height} {src.mode}"))
    rows, cur, wsum = [], [], PAD
    for tl in tiles:
        if wsum + tl[0].width + PAD > SW and cur:
            rows.append(cur)
            cur, wsum = [], PAD
        cur.append(tl)
        wsum += tl[0].width + PAD
    rows.append(cur)
    height = 60 + sum(max(tl[0].height for tl in r) + LAB + PAD for r in rows) + PAD
    sheet = Image.new("RGB", (SW, height), (28, 30, 32))
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 14), title, font=font(F_SANS_B, 24), fill=(230, 222, 200))
    y = 60
    f = font(F_SANS, 17)
    for r in rows:
        x = PAD
        rh = max(tl[0].height for tl in r)
        for im, lab in r:
            sheet.paste(im, (x, y))
            d.multiline_text((x, y + im.height + 4), lab, font=f, fill=(200, 196, 186), spacing=5)
            x += im.width + PAD
        y += rh + LAB + PAD
    sheet.save(path, quality=88)
    print("  wrote", os.path.relpath(path, ROOT), sheet.size)


def sheets():
    os.makedirs(QA3, exist_ok=True)
    dec = [os.path.join(OUT, S.DECAL_FILE[k]) for k in S.NAMES]
    dec += [os.path.join(OUT, n) for n in ("interlock_plate.png", "ecg_paper.png", "chalk_grid.png", "growth_grid.png",
                                           "growth_log.png", "strand_note.png")]
    for f in ("tile_glazed", "rock", "chequer"):
        dec += [os.path.join(TEX, f, n) for n in ("albedo.jpg", "normal.png", "orm.jpg")]
    _sheet(dec, "MYSTERY ROOM - Chapter 3 decals and texture sets (tools/textures/make_decals_ch3.py)",
           os.path.join(QA3, "decals_ch3_sheet.jpg"))
    lang = [os.path.join(OUT, lname(n, lg)) for n in ("growth_log.png", "strand_note.png") for lg in LANGS]
    _sheet(lang, "Chapter 3 localized decals: EN | RU | UZ", os.path.join(QA3, "decals_ch3_lang_sheet.jpg"), TH=420)
    pv = sorted(os.path.join(PREVIEW, n) for n in os.listdir(PREVIEW) if n.endswith((".png", ".jpg"))
                and not n.startswith("previews_sheet"))
    _sheet(pv, "Chapter 3 shader-quad QA previews, seed 0 (qa/blender/ch3/preview, not shipped)",
           os.path.join(PREVIEW, "previews_sheet.jpg"))


# =================================================================================================
GENERATORS: dict = {}


def register(name, fn, localized=False):
    GENERATORS[name] = (fn, localized)


register("symbols", symbols)
register("tile_glazed", tile_glazed)
register("rock", rock)
register("chequer", chequer)
register("interlock_plate", interlock_plate)
register("ecg_paper", ecg_paper)
register("chalk_grid", chalk_grid)
register("growth_grid", growth_grid)
register("growth_log", lambda langs: [growth_log(lg) for lg in langs], True)
register("strand_note", lambda langs: [strand_note(lg) for lg in langs], True)
register("previews", previews)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated generator names")
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--no-sheet", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    langs = [x for x in args.langs.split(",") if x]
    names = list(GENERATORS)
    if args.only:
        names = [n for n in args.only.split(",") if n]
        bad = [n for n in names if n not in GENERATORS]
        if bad:
            ap.error(f"unknown: {bad}; known: {list(GENERATORS)}")
    for n in names:
        fn, localized = GENERATORS[n]
        print(f"[{n}]")
        fn(langs) if localized else fn()
    if D2.GLYPH_FALLBACKS:
        print("glyph fallbacks:", ", ".join(f"{a} {c} -> {b}" for a, c, b in sorted(D2.GLYPH_FALLBACKS)))
    if not args.no_sheet:
        print("[sheets]")
        sheets()
    return 0


if __name__ == "__main__":
    sys.exit(main())
