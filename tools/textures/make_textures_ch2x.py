#!/usr/bin/env python3
"""Chapter 2 expansion ("The Whole Building") — seamless PBR texture sets, original procedural art (numpy + PIL).

Outputs game/assets/textures/<set>/{albedo.jpg, normal.png, orm.jpg} (1024 px, tileable) for:
    iron_rust          M_Iron_Rust          Pump Room cast iron and riveted plate, rust bloom (1.0 m repeat)
    wallpaper_cell     M_Wallpaper_Cell     Night Cell: warm ochre lattice wallpaper with tiny sprigs (0.5 m)
    wool_knit          M_Wool_Knit          Night Cell: blanket / rug, faded brick-red wool with a cream stripe (0.5 m)
    steel_galv         M_Steel_Galv         Cold Store: spangled galvanised steel, blue-grey (0.5 m)
    wallpaper_office   M_Wallpaper_Office   Director's Office: bottle-green watered stripe with a gold pin line (0.4 m)

    python3 tools/textures/make_textures_ch2x.py [--only iron_rust,wool_knit]

Deterministic (fixed seeds). No third-party images; recorded in docs/ASSET_LICENSES.md.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures")
N = 1024


def hexf(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def vnoise(size: int, cells: int, seed: int) -> np.ndarray:
    """Tileable value noise in 0..1 (bilinear with smoothstep over a wrapped random grid)."""
    rng = np.random.default_rng(seed)
    g = rng.random((cells, cells))
    xs = np.linspace(0, cells, size, endpoint=False)
    i0 = np.floor(xs).astype(int)
    f = xs - i0
    f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % cells
    a = g[np.ix_(i0, i0)]
    b = g[np.ix_(i0, i1)]
    c = g[np.ix_(i1, i0)]
    d = g[np.ix_(i1, i1)]
    fx = f[None, :]
    fy = f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(size: int, base: int, seed: int, octaves: int = 5, gain: float = 0.5) -> np.ndarray:
    out = np.zeros((size, size))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += amp * vnoise(size, base * 2 ** o, seed + o * 17)
        tot += amp
        amp *= gain
    return out / tot


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def normal_from_height(h: np.ndarray, strength: float) -> np.ndarray:
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength * N / 64
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength * N / 64
    nz = np.ones_like(h)
    ln = np.sqrt(gx * gx + gy * gy + nz * nz)
    return np.stack([(-gx / ln) * 0.5 + 0.5, (gy / ln) * 0.5 + 0.5, nz / ln * 0.5 + 0.5], -1)


def voronoi(size: int, cells: int, seed: int):
    """Tileable voronoi: returns (distance to nearest, cell id value 0..1)."""
    rng = np.random.default_rng(seed)
    pts = (np.stack(np.meshgrid(np.arange(cells), np.arange(cells), indexing="ij"), -1) + rng.random((cells, cells, 2))) / cells
    pts = pts.reshape(-1, 2)
    ids = rng.random(len(pts))
    ys, xs = np.meshgrid(np.arange(size) / size, np.arange(size) / size, indexing="ij")
    best = np.full((size, size), 9.0)
    bid = np.zeros((size, size))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for p, i in zip(pts, ids):
                d = np.hypot(((xs - p[1] - dx) + 0), ((ys - p[0] - dy) + 0))
                m = d < best
                best = np.where(m, d, best)
                bid = np.where(m, i, bid)
    return best * cells, bid


def save(name: str, albedo: np.ndarray, height: np.ndarray, rough: np.ndarray, metal: np.ndarray, ao: np.ndarray,
         nstrength: float = 2.0) -> None:
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)

    def u8(a):
        return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(u8(albedo)).save(os.path.join(d, "albedo.jpg"), quality=88)
    Image.fromarray(u8(normal_from_height(height, nstrength))).save(os.path.join(d, "normal.png"), optimize=True)
    orm = np.stack([ao, rough, metal], -1)
    Image.fromarray(u8(orm)).save(os.path.join(d, "orm.jpg"), quality=90)
    print("wrote", d)


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def iron_rust():
    n1, n2, n3 = fbm(N, 3, 11), fbm(N, 8, 23), fbm(N, 24, 37, 3)
    rust = smooth(0.40, 0.58, n1 * 0.55 + n2 * 0.45)
    base = np.array([0.20, 0.17, 0.155])
    bloom = np.array([0.50, 0.24, 0.09])
    deep = np.array([0.32, 0.14, 0.06])
    mix = rust[..., None]
    col = base * (1 - mix) + (bloom * smooth(0.5, 0.8, n2)[..., None] + deep * (1 - smooth(0.5, 0.8, n2))[..., None]) * mix
    col *= (0.82 + 0.3 * n3)[..., None]
    # pitting + faint horizontal plate seams every 0.5 m
    seam = np.zeros((N, N))
    for k in (0, N // 2):
        seam[k:k + 3, :] = 1.0
        seam[:, k:k + 3] = 1.0
    h = n2 * 0.5 + n3 * 0.25 + rust * 0.35 - seam * 0.5
    col *= (1 - seam * 0.35)[..., None]
    rough = np.clip(0.55 + rust * 0.35 + (n3 - 0.5) * 0.2, 0, 1)
    metal = np.clip(0.75 - rust * 0.6, 0, 1)
    save("iron_rust", col, h, rough, metal, np.clip(1 - seam * 0.5 - rust * 0.15, 0, 1), 3.0)


def wallpaper_cell():
    ys, xs = np.meshgrid(np.arange(N) / N, np.arange(N) / N, indexing="ij")
    base = hexf("#c4a56c")
    line = hexf("#8a5f26")
    spr = hexf("#6f4a1c")
    # diamond lattice, 4 per repeat
    u = (xs * 4) % 1.0
    v = (ys * 4) % 1.0
    d = np.minimum(np.abs((u - 0.5)) + np.abs((v - 0.5)), 1.0)
    lat = 1 - smooth(0.02, 0.05, np.abs(d - 0.40))
    # small sprig dot at each diamond centre and a lighter band
    dot = 1 - smooth(0.030, 0.05, np.hypot(u - 0.5, v - 0.5) * 1.0 + 0.0)
    ring = 1 - smooth(0.0, 0.02, np.abs(np.hypot(u - 0.5, v - 0.5) - 0.085))
    col = np.ones((N, N, 3)) * base
    col = col * (1 - lat[..., None] * 0.9) + line * lat[..., None] * 0.9
    col = col * (1 - ring[..., None] * 0.8) + spr * ring[..., None] * 0.8
    col = col * (1 - dot[..., None] * 0.8) + spr * dot[..., None] * 0.8
    stain = fbm(N, 4, 5)
    fade = fbm(N, 10, 9, 3)
    col *= (0.88 + 0.20 * stain)[..., None]
    col *= (0.93 + 0.1 * fade)[..., None]
    h = lat * 0.2 + dot * 0.1 + fade * 0.1
    save("wallpaper_cell", col, h, np.full((N, N), 0.85), np.zeros((N, N)), np.ones((N, N)), 0.8)


def wool_knit():
    ys, xs = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    cols, rows = 32, 40
    cx = (xs / N * cols) % 1.0
    ry = (ys / N * rows) % 1.0
    colid = np.floor(xs / N * cols)
    # knit V stitch: two slanted lobes per column, alternating sides
    left = np.abs((cx - 0.5) - (ry - 0.5) * 0.65)
    right = np.abs((cx - 0.5) + (ry - 0.5) * 0.65)
    lobe = np.minimum(left, right)
    h = 1 - smooth(0.0, 0.24, lobe)
    h *= 0.8 + 0.2 * smooth(0, 0.5, ry) * smooth(1, 0.5, ry)
    fibre = vnoise(N, 256, 3)
    h = h * 0.85 + fibre * 0.15
    base = hexf("#8c4a3a")
    stripe = hexf("#d6c4a0")
    band = (np.floor(ys / N * 20) % 20)
    sm = ((band == 6) | (band == 7)).astype(float)
    sm2 = ((band == 14)).astype(float) * 0.7
    c = np.ones((N, N, 3)) * base
    mask = np.clip(sm + sm2, 0, 1)[..., None]
    c = c * (1 - mask) + stripe * mask
    c *= (0.55 + 0.55 * h)[..., None]
    c *= (0.9 + 0.2 * fbm(N, 5, 41, 3))[..., None]
    save("wool_knit", c, h, np.full((N, N), 0.96), np.zeros((N, N)), 0.7 + 0.3 * h, 2.5)


def steel_galv():
    dist, cid = voronoi(N, 16, 5)
    spangle = 0.72 + 0.28 * cid
    edge = smooth(0.0, 0.05, dist * 0.0 + 1.0)  # no edge darkening: soft crystals
    base = hexf("#b7c6cf")          # pale cold zinc; the Cold Store reads blue-white
    c = np.ones((N, N, 3)) * base * spangle[..., None]
    c *= (0.9 + 0.2 * fbm(N, 6, 13))[..., None]
    # fine directional scratches
    sc = vnoise(N, 512, 7)
    sc = np.roll(sc, 3, 1)
    c *= (0.96 + 0.08 * vnoise(N, 256, 8)[:, :])[..., None]
    wear = smooth(0.62, 0.8, fbm(N, 5, 99))
    c = c * (1 - wear[..., None] * 0.25) + hexf("#6e6a60") * wear[..., None] * 0.25
    h = cid * 0.25 + sc * 0.05
    rough = np.clip(0.42 + wear * 0.3 + (1 - spangle) * 0.2, 0, 1)
    save("steel_galv", c, h, rough, np.full((N, N), 0.55) - wear * 0.2, np.ones((N, N)), 0.6)   # half-metal: lit by the room, not black in a closed room
    _ = edge


def wallpaper_office():
    ys, xs = np.meshgrid(np.arange(N) / N, np.arange(N) / N, indexing="ij")
    base = hexf("#2f4a3b")
    dark = hexf("#233a2e")
    stripes = 8
    u = (xs * stripes) % 1.0
    band = smooth(0.0, 0.03, u) * smooth(0.5, 0.47, u)
    wide = np.where(u < 0.5, 1.0, 0.0)
    c = np.ones((N, N, 3)) * (base * wide[..., None] + dark * (1 - wide)[..., None])
    gold = 1 - smooth(0.0, 0.012, np.abs(u - 0.5) - 0.004)
    gold += 1 - smooth(0.0, 0.012, np.abs(u - 0.0) - 0.004) + 1 - smooth(0.0, 0.012, np.abs(u - 1.0) - 0.004)
    gold = np.clip(gold, 0, 1)
    c = c * (1 - gold[..., None] * 0.8) + hexf("#a68a4f") * gold[..., None] * 0.8
    # watered silk moire
    w = np.sin((xs * 40 + fbm(N, 3, 71) * 6) * 2 * np.pi) * 0.5 + 0.5
    c *= (0.92 + 0.12 * w * fbm(N, 6, 73))[..., None]
    c *= (0.85 + 0.25 * fbm(N, 4, 75))[..., None]
    save("wallpaper_office", c, w * 0.1 + gold * 0.05, np.full((N, N), 0.7) - gold * 0.3, gold * 0.6, np.ones((N, N)), 0.5)


SETS = {"iron_rust": iron_rust, "wallpaper_cell": wallpaper_cell, "wool_knit": wool_knit, "steel_galv": steel_galv,
        "wallpaper_office": wallpaper_office}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    for k, fn in SETS.items():
        if not a.only or k in a.only.split(","):
            fn()
