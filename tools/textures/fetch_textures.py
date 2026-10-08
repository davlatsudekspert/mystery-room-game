#!/usr/bin/env python3
"""Rebuild the PBR texture library, the Godot materials and the QA contact sheet.

MYSTERY ROOM: The Forgotten Institute.

Every scanned source is CC0 (ambientCG or Poly Haven); a few maps are
procedural (numpy). The script downloads the source maps, grades the albedo to
the palette in docs/ART_DIRECTION.md, remaps roughness, packs ORM and writes:

    game/assets/textures/<folder>/albedo.jpg   sRGB colour, JPG q90
    game/assets/textures/<folder>/normal.png   OpenGL (Y+) tangent-space normal
    game/assets/textures/<folder>/orm.jpg      R = AO, G = roughness, B = metallic
    game/assets/materials/<Material>.tres      ORMMaterial3D / StandardMaterial3D
    qa/textures_contact_sheet.jpg              labelled grid of all albedo maps

Usage (from the repository root):
    python3 tools/textures/fetch_textures.py                 # everything
    python3 tools/textures/fetch_textures.py --only wood_walnut,stone
    python3 tools/textures/fetch_textures.py --materials-only
    python3 tools/textures/fetch_textures.py --cache /tmp/tex_cache --keep-cache

Downloads are treated as untrusted data: each source goes into its own fresh
directory inside the cache, only the expected image files are read out of the
ambientCG zips (nothing is executed or extracted wholesale), and the cache is
deleted at the end unless --keep-cache is given.

Requires: Python 3.10+, numpy, Pillow. Network: ambientcg.com,
api.polyhaven.com, dl.polyhaven.org.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TEX_DIR = ROOT / "game" / "assets" / "textures"
MAT_DIR = ROOT / "game" / "assets" / "materials"
QA_DIR = ROOT / "qa"

UA = {"User-Agent": "mystery-room-texture-fetch/1.0"}

# ---------------------------------------------------------------------------
# Material table
# ---------------------------------------------------------------------------
# source: ("ambientcg", AssetId, "1K"|"2K") | ("polyhaven", id, "1k"|"2k") | ("procedural", name, None)
# tile_m: physical size of one texture repeat in metres (Blender UVs are
#         world-scale, 1 UV unit = 1 m, so uv1_scale = 1 / tile_m).
# albedo: target sRGB mean colour + optional contrast / saturation / overlays.
# rough:  target mean roughness, contrast around the mean, clamp range.
# metal:  "map" (use source metalness), or a constant 0..1.
TEXTURED = [
    dict(folder="wood_walnut", material="M_Wood_Walnut",
         source=("polyhaven", "natural_walnut_veneer", "1k"), tile_m=1.0, size=1024,
         albedo=dict(target="#3B2416", contrast=1.1, sat=1.0),
         rough=dict(mean=0.45, contrast=0.6, lo=0.25, hi=0.7), metal=0.0),
    dict(folder="wood_mahogany", material="M_Wood_Mahogany",
         source=("polyhaven", "dark_wood", "1k"), tile_m=2.0, size=1024,
         albedo=dict(target="#5A2E1B", contrast=0.9, sat=0.85),
         rough=dict(mean=0.42, contrast=0.6, lo=0.25, hi=0.7), metal=0.0),
    dict(folder="wood_floor", material="M_Wood_Floor",
         source=("ambientcg", "WoodFloor014", "2K"), tile_m=1.25, size=2048, anisotropic=True,
         albedo=dict(target="#3F2C1E", contrast=1.05, sat=0.85,
                     dust=dict(color="#7A6E5E", amount=0.22, scale=0.18, seed=11)),
         rough=dict(mean=0.62, contrast=0.6, lo=0.4, hi=0.85, dust_add=0.12),
         ao_from_disp=0.6, metal=0.0),
    dict(folder="wood_panel", material="M_Wood_Panel",
         source=("polyhaven", "walnut_veneer_02", "1k"), tile_m=1.0, size=1024,
         albedo=dict(target="#4A3222", contrast=1.2, sat=0.9),
         rough=dict(mean=0.5, contrast=0.6, lo=0.3, hi=0.75), metal=0.0),
    dict(folder="plaster_wall", material="M_Plaster_Wall",
         source=("polyhaven", "plaster_grey_04", "2k"), tile_m=2.0, size=2048, normal_strength=0.45,
         albedo=dict(target="#AEAC97", contrast=0.7, sat=0.9),
         rough=dict(mean=0.88, contrast=0.5, lo=0.7, hi=1.0), metal=0.0),
    dict(folder="plaster_ceiling", material="M_Ceiling",
         source=("ambientcg", "Plaster001", "1K"), tile_m=1.5, size=1024, normal_strength=0.35,
         albedo=dict(target="#B4B1A4", contrast=1.0, sat=0.8,
                     stains=dict(color="#8C8270", amount=0.18, scale=0.3, seed=5)),
         rough=dict(mean=0.92, contrast=0.4, lo=0.8, hi=1.0), metal=0.0),
    dict(folder="stone", material="M_Stone",
         source=("ambientcg", "Concrete036", "1K"), tile_m=1.0, size=1024,
         albedo=dict(target="#86837B", contrast=0.75, sat=0.6),
         rough=dict(mean=0.72, contrast=0.6, lo=0.5, hi=0.9), metal=0.0),
    dict(folder="brass_aged", material="M_Brass_Aged",
         source=("ambientcg", "Metal008", "1K"), tile_m=0.5, size=1024,
         albedo=dict(target="#B08D57", contrast=0.85, sat=1.0),
         rough=dict(mean=0.36, contrast=0.9, lo=0.2, hi=0.7), metal="map"),
    dict(folder="brass_polished", material="M_Brass_Polished",
         source=("ambientcg", "Metal048B", "1K"), tile_m=0.5, size=1024,
         albedo=dict(target="#D2B06C", contrast=1.0, sat=1.0),
         rough=dict(mean=0.18, contrast=0.8, lo=0.08, hi=0.4), metal="map"),
    dict(folder="steel_painted", material="M_Steel_Painted",
         source=("polyhaven", "green_metal_rust", "1k"), tile_m=1.0, size=1024,
         albedo=dict(target="#5A6557", contrast=1.0, sat=0.6),
         rough=dict(mean=0.55, contrast=0.8, lo=0.3, hi=0.85), metal=0.0),
    dict(folder="steel_dark", material="M_Steel_Dark",
         source=("ambientcg", "Metal046B", "1K"), tile_m=0.5, size=1024,
         albedo=dict(target="#3E3D3B", contrast=1.0, sat=0.5),
         rough=dict(mean=0.55, contrast=0.9, lo=0.3, hi=0.85), metal="map"),
    dict(folder="copper", material="M_Copper",
         source=("ambientcg", "Metal057C", "1K"), tile_m=0.5, size=1024,
         albedo=dict(target="#A56A4F", contrast=1.2, sat=0.9),
         rough=dict(mean=0.35, contrast=0.9, lo=0.15, hi=0.7), metal="map"),
    dict(folder="leather", material="M_Leather",
         source=("ambientcg", "Leather030", "1K"), tile_m=0.45, size=1024,
         albedo=dict(target="#3A2519", contrast=1.0, sat=1.0),
         rough=dict(mean=0.55, contrast=0.8, lo=0.35, hi=0.8), metal=0.0),
    dict(folder="fabric", material="M_Fabric",
         source=("polyhaven", "poly_wool_herringbone", "1k"), tile_m=0.27, size=1024,
         albedo=dict(target="#34302C", contrast=1.0, sat=1.0),
         rough=dict(mean=0.92, contrast=0.4, lo=0.8, hi=1.0), metal=0.0),
    dict(folder="paper", material="M_Paper",
         source=("ambientcg", "Paper001", "1K"), tile_m=0.5, size=1024, normal_strength=0.4,
         albedo=dict(target="#D2C4A8", contrast=1.0, sat=1.0,
                     stains=dict(color="#A88B5E", amount=0.25, scale=0.25, seed=21)),
         rough=dict(mean=0.85, contrast=0.4, lo=0.7, hi=0.98), metal=0.0),
    dict(folder="chalkboard", material="M_Chalkboard",
         source=("procedural", "chalkboard", None), tile_m=1.0, size=1024,
         albedo=None, rough=None, metal=0.0),
    dict(folder="bakelite", material="M_Bakelite",
         source=("ambientcg", "Plastic012B", "1K"), tile_m=0.5, size=1024, normal_strength=0.5,
         albedo=dict(target="#23170F", contrast=1.0, sat=1.0,
                     stains=dict(color="#3C1E12", amount=0.35, scale=0.12, seed=33, mode="lerp")),
         rough=dict(mean=0.28, contrast=0.8, lo=0.12, hi=0.6), metal=0.0),
    dict(folder="enamel_cream", material="M_Enamel_Cream",
         source=("ambientcg", "Plastic013B", "1K"), tile_m=0.5, size=1024, normal_strength=0.5,
         albedo=dict(target="#E2D8BF", contrast=0.6, sat=1.0),
         rough=dict(mean=0.3, contrast=0.7, lo=0.12, hi=0.6), metal=0.0),
]

# Untextured materials (StandardMaterial3D). Colours are sRGB hex.
PLAIN = [
    dict(material="M_Glass", albedo="#D8E4E0", alpha=0.25, roughness=0.05, metallic=0.0,
         transparent=True, specular=0.6),
    dict(material="M_Glass_Frosted", albedo="#D4DDDA", alpha=0.6, roughness=0.5, metallic=0.0,
         transparent=True),
    dict(material="M_Crystal", albedo="#CFF6FF", alpha=0.35, roughness=0.0, metallic=0.0,
         transparent=True, specular=0.8, rim=0.4, emission="#CFF6FF", emission_energy=0.15),
    dict(material="M_Liquid_Crimson", albedo="#8E1B2A", alpha=0.75, roughness=0.1, metallic=0.0,
         transparent=True),
    dict(material="M_Liquid_Cobalt", albedo="#1F3E9E", alpha=0.75, roughness=0.1, metallic=0.0,
         transparent=True),
    dict(material="M_Liquid_Green", albedo="#3E8E3A", alpha=0.75, roughness=0.1, metallic=0.0,
         transparent=True),
    dict(material="M_Chrome", albedo="#E6E8EA", roughness=0.15, metallic=1.0),
    dict(material="M_Rubber", albedo="#151515", roughness=0.9, metallic=0.0),
    dict(material="M_Emissive_Warm", albedo="#FFB46B", roughness=0.4, metallic=0.0,
         emission="#FFB46B", emission_energy=3.0),
    dict(material="M_Emissive_Red", albedo="#FF3B2F", roughness=0.4, metallic=0.0,
         emission="#FF3B2F", emission_energy=2.5),
    dict(material="M_Emissive_Lumen", albedo="#CFF6FF", roughness=0.3, metallic=0.0,
         emission="#CFF6FF", emission_energy=4.0),
] + [
    # Indicator lamp glass: dark amber, non-emissive by default. Game code sets
    # emission_enabled / emission_energy_multiplier when a lamp lights up.
    dict(material=f"M_Lamp_{k}", albedo="#3A2A12", roughness=0.2, metallic=0.0,
         specular=0.6, emission_off="#FFB46B")
    for k in ("L", "G", "A", "V")
]

# ---------------------------------------------------------------------------
# Networking (untrusted downloads)
# ---------------------------------------------------------------------------

def http_get(url: str, tries: int = 6) -> bytes:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - retry on any transport error
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"download failed: {url}: {last}")


AC_MAPS = {
    "color": "Color", "normal": "NormalGL", "rough": "Roughness",
    "ao": "AmbientOcclusion", "metal": "Metalness", "disp": "Displacement",
}


def fetch_ambientcg(asset: str, res: str, cache: Path) -> dict[str, Path]:
    d = cache / f"acg_{asset}_{res}"
    if not (d / "color.jpg").exists():
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        name = f"{asset}_{res}-JPG.zip"
        data = http_get(f"https://ambientcg.com/get?file={name}")
        zf = zipfile.ZipFile(io.BytesIO(data))
        members = set(zf.namelist())
        for key, suffix in AC_MAPS.items():
            member = f"{asset}_{res}-JPG_{suffix}.jpg"
            if member in members:  # read by exact name only; never extractall()
                (d / f"{key}.jpg").write_bytes(zf.read(member))
        if not (d / "color.jpg").exists():
            raise RuntimeError(f"{asset}: no colour map in {name}: {sorted(members)}")
    return {p.stem: p for p in d.glob("*.jpg")}


PH_MAPS = {"color": ("Diffuse", "jpg"), "normal": ("nor_gl", "png"), "arm": ("arm", "jpg"),
           "disp": ("Displacement", "jpg")}


def fetch_polyhaven(asset: str, res: str, cache: Path) -> dict[str, Path]:
    d = cache / f"ph_{asset}_{res}"
    if not (d / "color.jpg").exists():
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        files = json.loads(http_get(f"https://api.polyhaven.com/files/{asset}"))
        for key, (mapname, ext) in PH_MAPS.items():
            entry = files.get(mapname, {}).get(res, {}).get(ext)
            if not entry:
                continue
            url = entry["url"]
            if not url.startswith("https://dl.polyhaven.org/"):
                raise RuntimeError(f"unexpected host in {url}")
            (d / f"{key}.{ext}").write_bytes(http_get(url))
    return {p.stem: p for p in d.iterdir() if p.suffix in (".jpg", ".png")}


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def load(path: Path, mode: str = "RGB") -> np.ndarray:
    with Image.open(path) as im:
        im = im.convert(mode)
        return np.asarray(im, dtype=np.float32) / 255.0


def s2l(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def l2s(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def resize_wrap(a: np.ndarray, size: int) -> np.ndarray:
    """Resize a tileable map without breaking the wrap-around seam."""
    h = a.shape[0]
    if h == size:
        return a
    pad = max(8, h // 32)
    single = a.ndim == 2
    src = a[..., None] if single else a
    padded = np.pad(src, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")
    scale = size / h
    new = int(round(padded.shape[0] * scale))
    chans = []
    for c in range(padded.shape[2]):
        im = Image.fromarray(padded[..., c].astype(np.float32), mode="F")
        chans.append(np.asarray(im.resize((new, new), Image.LANCZOS)))
    out = np.stack(chans, axis=-1)
    p = int(round(pad * scale))
    out = out[p:p + size, p:p + size]
    return out[..., 0] if single else out


def tile_noise(size: int, scale: float, seed: int, stretch: tuple[float, float] = (1.0, 1.0)) -> np.ndarray:
    """Periodic (tileable) smooth noise in 0..1.

    scale   feature size as a fraction of the tile width
    stretch (x, y) multipliers on the feature size, e.g. (8, 1) for horizontal streaks
    """
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((size, size))
    sigma = scale * size * 0.5
    fy = np.fft.fftfreq(size)[:, None] * stretch[1]
    fx = np.fft.fftfreq(size)[None, :] * stretch[0]
    g = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * g))
    lo, hi = np.percentile(n, 1), np.percentile(n, 99)
    return np.clip((n - lo) / (hi - lo + 1e-9), 0, 1).astype(np.float32)


def fbm(size: int, scale: float, seed: int, octaves: int = 4, stretch=(1.0, 1.0)) -> np.ndarray:
    acc = np.zeros((size, size), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * tile_noise(size, scale / (2 ** o), seed + 101 * o, stretch)
        tot += amp
        amp *= 0.5
    return acc / tot


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def box_blur_wrap(a: np.ndarray, r: int) -> np.ndarray:
    """Periodic gaussian-ish blur via FFT (radius r pixels)."""
    n = a.shape[0]
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (r ** 2) * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def grade(rgb: np.ndarray, target: str, contrast: float = 1.0, sat: float = 1.0) -> np.ndarray:
    """Grade an sRGB albedo so its mean hits `target`, keeping the texture's detail."""
    lin = s2l(rgb).astype(np.float32)
    w = np.array([0.2126, 0.7152, 0.0722], np.float32)
    lum = (lin @ w)[..., None]
    lin = lum + (lin - lum) * sat
    lin = np.clip(lin, 1e-5, None)
    lum = np.clip(lin @ w, 1e-5, None)[..., None]
    mean_l = float(lum.mean())
    lin = lin * np.power(lum / mean_l, contrast - 1.0)
    tgt = s2l(hex_rgb(target))
    gain = tgt / lin.reshape(-1, 3).mean(0)
    for _ in range(8):  # match the mean in sRGB space, not linear
        cur = l2s(lin * gain).reshape(-1, 3).mean(0)
        gain *= s2l(hex_rgb(target)) / np.maximum(s2l(cur), 1e-6)
    return l2s(lin * gain).astype(np.float32)


def overlay(rgb: np.ndarray, spec: dict, size: int) -> tuple[np.ndarray, np.ndarray]:
    """Blend a low-frequency tileable stain/dust layer. Returns (rgb, mask)."""
    n = fbm(size, spec["scale"], spec["seed"], octaves=4)
    mask = smoothstep(0.45, 0.9, n) * spec["amount"]
    col = hex_rgb(spec["color"])
    if spec.get("mode", "lerp") == "multiply":
        out = rgb * (1 - mask[..., None] + mask[..., None] * col)
    else:
        out = rgb * (1 - mask[..., None]) + col * mask[..., None]
    return out.astype(np.float32), mask


def remap_rough(r: np.ndarray, mean: float, contrast: float, lo: float, hi: float) -> np.ndarray:
    m = float(r.mean())
    std = float(r.std()) + 1e-6
    # normalise spread so very flat / very noisy sources behave alike
    spread = min(std, 0.12) * contrast
    out = mean + (r - m) / std * spread
    return np.clip(out, lo, hi).astype(np.float32)


def normal_fix(n: np.ndarray, strength: float = 1.0) -> np.ndarray:
    v = n * 2.0 - 1.0
    v[..., 0] *= strength
    v[..., 1] *= strength
    v[..., 2] = np.clip(v[..., 2], 0.05, None)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return (v * 0.5 + 0.5).astype(np.float32)


def normal_from_height(h: np.ndarray, strength: float) -> np.ndarray:
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    # OpenGL convention: +Y up in tangent space; image rows grow downward.
    v = np.stack([-dx, dy, np.ones_like(h)], axis=-1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return (v * 0.5 + 0.5).astype(np.float32)


def to_u8(a: np.ndarray) -> np.ndarray:
    return (np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def save_jpg(a: np.ndarray, path: Path) -> None:
    Image.fromarray(to_u8(a), "RGB").save(path, "JPEG", quality=90, subsampling=0, optimize=True)


def save_png(a: np.ndarray, path: Path) -> None:
    Image.fromarray(to_u8(a), "RGB").save(path, "PNG", optimize=True)


# ---------------------------------------------------------------------------
# Procedural sources
# ---------------------------------------------------------------------------

def procedural_chalkboard(size: int) -> dict[str, np.ndarray]:
    """Dark slate board with eraser-swipe chalk haze (tileable, 1 m per repeat)."""
    grain = fbm(size, 0.003, 7, octaves=3)                       # slate grain
    cloud = fbm(size, 0.3, 8, octaves=3)                         # faint residue clouds
    bands = tile_noise(size, 0.07, 9, stretch=(4.0, 1.0))        # broad horizontal eraser swipes
    streak = tile_noise(size, 0.0025, 10, stretch=(60.0, 1.0))   # felt streaks inside a swipe
    specks = tile_noise(size, 0.0012, 13)                        # chalk dust grains
    swipe = smoothstep(0.55, 0.92, bands)
    haze = 0.02 + 0.05 * cloud
    haze += swipe * (0.025 + 0.05 * streak)
    haze += smoothstep(0.9, 1.0, specks) * 0.05
    haze = np.clip(haze, 0, 0.3)
    base = s2l(hex_rgb("#252C29"))
    chalk = s2l(hex_rgb("#B4B8B0"))
    lin = base[None, None, :] * (0.9 + 0.2 * grain[..., None])
    lin = lin * (1 - haze[..., None]) + chalk * haze[..., None]
    albedo = l2s(lin)
    rough = np.clip(0.78 + 0.5 * haze + 0.04 * (grain - 0.5), 0.7, 0.98)
    normal = normal_from_height(grain * 0.5 + streak * 0.05, strength=1.5)
    ao = np.ones((size, size), np.float32)
    return dict(albedo=albedo.astype(np.float32), rough=rough.astype(np.float32),
                normal=normal, ao=ao, metal=np.zeros((size, size), np.float32))


PROCEDURAL = {"chalkboard": procedural_chalkboard}


# ---------------------------------------------------------------------------
# Build one material
# ---------------------------------------------------------------------------

def build(spec: dict, cache: Path) -> dict:
    kind, asset, res = spec["source"]
    size = spec["size"]
    out_dir = TEX_DIR / spec["folder"]
    out_dir.mkdir(parents=True, exist_ok=True)

    if kind == "procedural":
        maps = PROCEDURAL[asset](size)
        albedo, rough, normal, ao, metal = (maps[k] for k in ("albedo", "rough", "normal", "ao", "metal"))
    else:
        paths = fetch_ambientcg(asset, res, cache) if kind == "ambientcg" else fetch_polyhaven(asset, res, cache)
        color = resize_wrap(load(paths["color"]), size)
        normal = normal_fix(resize_wrap(load(paths["normal"]), size), spec.get("normal_strength", 1.0))
        if "arm" in paths:  # Poly Haven packs AO / Rough / Metal already
            arm = resize_wrap(load(paths["arm"]), size)
            ao_src, rough_src, metal_src = arm[..., 0], arm[..., 1], arm[..., 2]
        else:
            ao_src = resize_wrap(load(paths["ao"], "L"), size) if "ao" in paths else None
            rough_src = resize_wrap(load(paths["rough"], "L"), size)
            metal_src = resize_wrap(load(paths["metal"], "L"), size) if "metal" in paths else None

        a = spec["albedo"]
        albedo = grade(color, a["target"], a.get("contrast", 1.0), a.get("sat", 1.0))
        dust_mask = np.zeros((size, size), np.float32)
        if "stains" in a:
            albedo, _ = overlay(albedo, a["stains"], size)
        if "dust" in a:
            albedo, dust_mask = overlay(albedo, a["dust"], size)

        r = spec["rough"]
        rough = remap_rough(rough_src, r["mean"], r["contrast"], r["lo"], r["hi"])
        if r.get("dust_add"):
            rough = np.clip(rough + dust_mask / max(a["dust"]["amount"], 1e-6) * r["dust_add"], 0, 1)

        if ao_src is not None:
            # Scanned AO is often globally dark; keep only the local occlusion.
            ao = np.clip(ao_src / max(float(np.percentile(ao_src, 98)), 1e-3), 0, 1)
            ao = 1.0 - (1.0 - ao) * spec.get("ao_strength", 1.0)
        else:
            ao = np.ones((size, size), np.float32)
        if spec.get("ao_from_disp") and "disp" in paths:
            d = resize_wrap(load(paths["disp"], "L"), size)
            cavity = np.clip((box_blur_wrap(d, max(2, size // 256)) - d) * 6.0, 0, 1)
            ao = ao * (1 - spec["ao_from_disp"] * cavity)

        if spec["metal"] == "map":
            metal = metal_src if metal_src is not None else np.ones((size, size), np.float32)
        else:
            metal = np.full((size, size), float(spec["metal"]), np.float32)

    orm = np.stack([ao, rough, metal], axis=-1)
    save_jpg(albedo, out_dir / "albedo.jpg")
    save_png(normal, out_dir / "normal.png")
    save_jpg(orm, out_dir / "orm.jpg")
    stats = dict(folder=spec["folder"],
                 albedo_mean="#%02X%02X%02X" % tuple(to_u8(albedo.reshape(-1, 3).mean(0))),
                 rough_mean=round(float(rough.mean()), 3), metal_mean=round(float(metal.mean()), 3),
                 ao_mean=round(float(ao.mean()), 3))
    print("  built", stats)
    return stats


# ---------------------------------------------------------------------------
# Godot materials
# ---------------------------------------------------------------------------

def fmt(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def color_str(h: str, alpha: float = 1.0) -> str:
    r, g, b = hex_rgb(h)
    return f"Color({fmt(r)}, {fmt(g)}, {fmt(b)}, {fmt(alpha)})"


def write_textured_tres(spec: dict) -> None:
    folder, name = spec["folder"], spec["material"]
    uv = 1.0 / spec["tile_m"]
    is_metal = spec["metal"] == "map" or float(spec["metal"]) > 0
    lines = [
        '[gd_resource type="ORMMaterial3D" load_steps=4 format=3]',
        "",
        f'[ext_resource type="Texture2D" path="res://assets/textures/{folder}/albedo.jpg" id="1"]',
        f'[ext_resource type="Texture2D" path="res://assets/textures/{folder}/normal.png" id="2"]',
        f'[ext_resource type="Texture2D" path="res://assets/textures/{folder}/orm.jpg" id="3"]',
        "",
        "[resource]",
        f'resource_name = "{name}"',
        'albedo_texture = ExtResource("1")',
        'orm_texture = ExtResource("3")',
        # metallic/roughness stay at 1.0 so the ORM channels pass through unchanged
        f"metallic = {fmt(1.0 if is_metal else 0.0)}",
        "roughness = 1.0",
        "normal_enabled = true",
        'normal_texture = ExtResource("2")',
        "ao_enabled = true",
        f"uv1_scale = Vector3({fmt(uv)}, {fmt(uv)}, {fmt(uv)})",
    ]
    if spec.get("anisotropic"):
        lines.append("texture_filter = 5")  # LINEAR_WITH_MIPMAPS_ANISOTROPIC: floor is seen at grazing angles
    lines.append("")
    (MAT_DIR / f"{name}.tres").write_text("\n".join(lines))


def write_plain_tres(p: dict) -> None:
    lines = ['[gd_resource type="StandardMaterial3D" format=3]', "", "[resource]",
             f'resource_name = "{p["material"]}"']
    if p.get("transparent"):
        lines.append("transparency = 1")  # BaseMaterial3D.TRANSPARENCY_ALPHA
    lines.append(f'albedo_color = {color_str(p["albedo"], p.get("alpha", 1.0))}')
    lines.append(f'metallic = {fmt(p["metallic"])}')
    if "specular" in p:
        lines.append(f'metallic_specular = {fmt(p["specular"])}')
    lines.append(f'roughness = {fmt(p["roughness"])}')
    if "emission" in p:
        lines += ["emission_enabled = true",
                  f'emission = {color_str(p["emission"])}',
                  f'emission_energy_multiplier = {fmt(p["emission_energy"])}']
    elif "emission_off" in p:
        # colour pre-set, switched on at runtime by the game
        lines += ["emission_enabled = false",
                  f'emission = {color_str(p["emission_off"])}',
                  "emission_energy_multiplier = 2.0"]
    if "rim" in p:
        lines += ["rim_enabled = true", f'rim = {fmt(p["rim"])}', "rim_tint = 0.8"]
    lines.append("")
    (MAT_DIR / f'{p["material"]}.tres').write_text("\n".join(lines))


def write_materials(specs: list[dict]) -> None:
    MAT_DIR.mkdir(parents=True, exist_ok=True)
    for s in specs:
        write_textured_tres(s)
    for p in PLAIN:
        write_plain_tres(p)
    print(f"  wrote {len(specs) + len(PLAIN)} materials to {MAT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# QA contact sheet
# ---------------------------------------------------------------------------

def find_font(size: int):
    for f in (ROOT / "game/assets/fonts/NotoSans-Variable.ttf",
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        try:
            return ImageFont.truetype(str(f), size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def contact_sheet(specs: list[dict], cell: int = 256) -> Path:
    cols = 6
    rows = (len(specs) + cols - 1) // cols
    label_h = 40
    sheet = Image.new("RGB", (cols * cell, rows * (cell + label_h)), (14, 15, 18))
    d = ImageDraw.Draw(sheet)
    f1, f2 = find_font(15), find_font(12)
    for i, s in enumerate(specs):
        x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
        with Image.open(TEX_DIR / s["folder"] / "albedo.jpg") as im:
            sheet.paste(im.convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y + label_h))
        d.text((x + 6, y + 3), s["material"], fill=(232, 223, 200), font=f1)
        src = s["source"]
        d.text((x + 6, y + 22), f"{src[1]}  |  {s['tile_m']} m/tile", fill=(176, 141, 87), font=f2)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    out = QA_DIR / "textures_contact_sheet.jpg"
    sheet.save(out, "JPEG", quality=88)
    print("  contact sheet:", out.relative_to(ROOT))
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated texture folders to rebuild")
    ap.add_argument("--cache", help="download cache directory (default: a fresh temp dir)")
    ap.add_argument("--keep-cache", action="store_true", help="do not delete the download cache")
    ap.add_argument("--materials-only", action="store_true", help="only (re)write the .tres files")
    ap.add_argument("--no-sheet", action="store_true", help="skip the QA contact sheet")
    args = ap.parse_args()

    specs = TEXTURED
    if args.only:
        wanted = set(args.only.split(","))
        unknown = wanted - {s["folder"] for s in TEXTURED}
        if unknown:
            ap.error(f"unknown folders: {sorted(unknown)}")
        specs = [s for s in TEXTURED if s["folder"] in wanted]

    if not args.materials_only:
        cache = Path(args.cache) if args.cache else Path(tempfile.mkdtemp(prefix="mr_tex_"))
        cache.mkdir(parents=True, exist_ok=True)
        try:
            for s in specs:
                print(f"[{s['folder']}] {s['source'][0]}:{s['source'][1]}")
                build(s, cache)
        finally:
            if not args.keep_cache:
                shutil.rmtree(cache, ignore_errors=True)
    write_materials(TEXTURED)
    if not args.no_sheet and not args.materials_only:
        contact_sheet(TEXTURED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
