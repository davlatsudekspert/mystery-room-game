#!/usr/bin/env python3
"""Chapter 2 (Records Archive B) decals, glyphs, film frames and the linoleum texture set.

Original procedural artwork (PIL + numpy only, no third-party images). Outputs:
    game/assets/textures/decals/ch2/*.png|jpg     decals, glyphs, film frames (table: docs/models/ch2_decals.md)
    game/assets/textures/linoleum/{albedo.jpg, normal.png, orm.jpg}   M_Linoleum (seamless, 0.6 m repeat)
    qa/decals_ch2_contact_sheet.jpg               labelled QA sheet of everything above

Puzzle data MUST match game/src/rooms/archive/archive_logic.gd and docs/CHAPTER2_DESIGN.md.

    python3 tools/textures/make_decals_ch2.py                       # everything + contact sheet
    python3 tools/textures/make_decals_ch2.py --only badge,index_card
    python3 tools/textures/make_decals_ch2.py --sheet-only
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# make_decals only creates its (existing) output folders and seeds its own RNGs at import time.
from make_decals import aged_paper, noise  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
TEX = os.path.join(ROOT, "game", "assets", "textures")
QA = os.path.join(ROOT, "qa")

# ---- puzzle data (mirrors archive_logic.gd) -------------------------------------------------
BADGE_NO = "0417"
PUNCH_CODE = [1, 0, 1, 1, 0, 0, 1, 0]          # notched / punched positions 1..8
SPLICE_SHADOWS = [3, 1, 4, 2]                  # film strip k -> shadow length (units)
TAPE_SPEED = "4.75"                            # SPEEDS[SPEED_RIGHT]
TAPE_YEARS = (1996, 1997, 1998)
DEST_SYMBOLS = ["star", "book", "flask", "film", "envelope", "padlock"]  # dial d = 0..5 at 12,2,4,6,8,10 o'clock
SIGN_IN_VAULT_SCALE = 0.55                     # 1 - 0.15 * ZOOM_TARGET
SIGN_IN_VAULT_ROT_CW = 90.0                    # 45 deg * ROT_RIGHT_TARGET, clockwise as seen
STAFF_COUNT = 41

# card geometry shared by index_card / request_card (1250 x 750 px = 0.125 x 0.075 m, 10 px per mm);
# mirrored in tools/blender/lib_ch2_items.py (HOLE_FROM_TOP, HOLE_D, NOTCH_W, NOTCH_D)
CARD_W, CARD_H = 1250, 750
HOLE_V_PX = 92            # punch-circle centre, px from the top edge (9.2 mm)  -> v = 1 - 92/750
HOLE_R_PX = 27            # printed punch circle radius (Ø 5.4 mm); hole discs are Ø 5.0 mm
NOTCH_W_PX = 84           # V-notch width at the top edge (8.4 mm)
NOTCH_D_PX = 100          # V-notch depth (10 mm): the tip passes the printed circle centre
NOTCH_FLAT_PX = 6         # flat at the notch tip (0.6 mm, as the model)
CARD_CORNER_PX = 15       # 1.5 mm corner radius
REQ_CLIP_PX = 45          # request card: clipped top-left corner (4.5 mm)


def card_pos_x(k: int) -> float:
    """Centre of edge position k (1..8) in px: u = (k - 0.5) / 8."""
    return (k - 0.5) * CARD_W / 8


# ---- fonts ------------------------------------------------------------------------------------
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
SYS = "/usr/share/fonts"


def _first(*paths: str) -> str:
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(SYS, "truetype", "dejavu", "DejaVuSans.ttf")


URW = f"{SYS}/opentype/urw-base35"
F_TYPE = _first(f"{URW}/NimbusMonoPS-Regular.otf", f"{SYS}/truetype/freefont/FreeMono.ttf",
                f"{SYS}/truetype/dejavu/DejaVuSansMono.ttf")
F_TYPE_B = _first(f"{URW}/NimbusMonoPS-Bold.otf", f"{SYS}/truetype/freefont/FreeMonoBold.ttf",
                  f"{SYS}/truetype/dejavu/DejaVuSansMono-Bold.ttf")
F_HAND = _first(os.path.join(FONTS, "Caveat-Variable.ttf"))
F_SERIF_B = _first(os.path.join(FONTS, "CormorantGaramond-Bold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif-Bold.ttf")
F_SERIF = _first(os.path.join(FONTS, "CormorantGaramond-SemiBold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif.ttf")
F_ROMAN = _first(f"{URW}/NimbusRoman-Regular.otf", f"{SYS}/truetype/dejavu/DejaVuSerif.ttf")
F_ROMAN_B = _first(f"{URW}/NimbusRoman-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSerif-Bold.ttf")
F_SANS_N = _first(f"{URW}/NimbusSansNarrow-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")
F_SANS = _first(f"{URW}/NimbusSans-Regular.otf", f"{SYS}/truetype/dejavu/DejaVuSans.ttf")
F_SANS_B = _first(f"{URW}/NimbusSans-Bold.otf", f"{SYS}/truetype/dejavu/DejaVuSans-Bold.ttf")
F_GOTHIC = _first(f"{URW}/URWGothic-Demi.otf", F_SANS_B)

_font_cache: dict = {}


def font(path: str, size: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    key = (path, int(round(size)), weight)
    f = _font_cache.get(key)
    if f is None:
        f = ImageFont.truetype(path, max(1, int(round(size))))
        if weight is not None:
            try:
                f.set_variation_by_axes([weight])
            except Exception:  # static font
                pass
        _font_cache[key] = f
    return f


# ---- numeric helpers ---------------------------------------------------------------------------
def blur(a: np.ndarray, sigma: float, wrap: bool = False) -> np.ndarray:
    """Gaussian blur (FFT) for 2-D or HxWxC float arrays; reflect padding, or periodic with wrap."""
    if sigma <= 0.05:
        return a.astype(np.float32)
    pad = 0 if wrap else int(3 * sigma) + 2
    if pad:
        widths = ((pad, pad), (pad, pad)) + ((0, 0),) * (a.ndim - 2)
        p = np.pad(a.astype(np.float32), widths, mode="reflect")
    else:
        p = a.astype(np.float32)
    hh, ww = p.shape[:2]
    fy = np.fft.fftfreq(hh)[:, None]
    fx = np.fft.rfftfreq(ww)[None, :]
    g = np.exp(-2.0 * np.pi ** 2 * sigma ** 2 * (fx ** 2 + fy ** 2))
    if a.ndim == 3:
        g = g[..., None]
    out = np.fft.irfft2(np.fft.rfft2(p, axes=(0, 1)) * g, s=(hh, ww), axes=(0, 1))
    return out[pad:pad + a.shape[0], pad:pad + a.shape[1]].astype(np.float32)


def pnoise(h: int, w: int, scale: float, seed: int, stretch=(1.0, 1.0)) -> np.ndarray:
    """Periodic (tileable) smooth noise in 0..1; feature size ~scale px; stretch elongates (x, y)."""
    r = np.random.default_rng(seed)
    white = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * stretch[1]
    fx = np.fft.fftfreq(w)[None, :] * stretch[0]
    sig = scale * 0.5
    g = np.exp(-2.0 * np.pi ** 2 * sig ** 2 * (fx ** 2 + fy ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * g))
    lo, hi = np.percentile(n, 1), np.percentile(n, 99)
    return np.clip((n - lo) / (hi - lo + 1e-9), 0, 1).astype(np.float32)


def fbm(h: int, w: int, scale: float, seed: int, octaves: int = 4, stretch=(1.0, 1.0)) -> np.ndarray:
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * pnoise(h, w, scale / (2 ** o), seed + 17 * o, stretch)
        tot += amp
        amp *= 0.5
    return acc / tot


def smooth(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hexf(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def paint(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    """Lerp `color` (hex, rgb triple or HxWx3 array) onto a float sRGB image through mask (0..1)."""
    c = hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m) + c * m


def multiply(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    c = (hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)) / 255.0
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m + m * c)


def solid(h: int, w: int, color) -> np.ndarray:
    c = hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)
    return np.broadcast_to(c, (h, w, 3)).astype(np.float32).copy()


def to_img(rgb: np.ndarray, alpha: np.ndarray | None = None) -> Image.Image:
    rgb8 = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(rgb8, "RGB")
    a8 = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb8, a8]), "RGBA")


def grain(h: int, w: int, seed: int, sigma: float = 0.7) -> np.ndarray:
    r = np.random.default_rng(seed)
    g = blur(r.standard_normal((h, w)).astype(np.float32), sigma)
    return g / (g.std() + 1e-6)


def save(im: Image.Image, name: str, folder: str = OUT) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    if name.endswith(".jpg"):
        im.convert("RGB").save(path, quality=93, subsampling=0, optimize=True)
    else:
        im.save(path, optimize=True)
    print("  wrote", os.path.relpath(path, ROOT), im.size, im.mode)
    return path


def paper(w: int, h: int, base=(221, 208, 180), seed: int = 1, stains: int = 3, vignette: float = 0.25,
          fibres: float = 1.0) -> np.ndarray:
    """Aged paper (make_decals.aged_paper) plus fine fibres, as float sRGB."""
    rgb = np.asarray(aged_paper(w, h, base=base, seed=seed, stains=stains, vignette=vignette), np.float32)
    if fibres:
        f1 = noise(h, w, 1.6, 1, seed + 101)
        f2 = noise(h, w * 3, 2.0, 1, seed + 102)[:, ::3]
        rgb = rgb * (0.975 + 0.035 * fibres * (f1 - 0.5) + 0.03 * fibres * (f2 - 0.5))[..., None]
    return rgb


def edge_wear(w: int, h: int, seed: int, width: float = 30.0, amount: float = 0.18) -> np.ndarray:
    """0..1 mask that is 1 near the image border with a ragged inner edge (handling grime)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    n = noise(h, w, 30, 3, seed)
    return np.clip(1 - d / (width * (0.5 + n)), 0, 1) * amount


# ---- supersampled vector pen --------------------------------------------------------------------
class Pen:
    """Antialiased mask drawing: everything is drawn at `ss` x resolution in output-pixel
    coordinates and box-downsampled by .arr()."""

    def __init__(self, w: int, h: int, ss: int = 4):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        s = self.ss
        return [(x * s, y * s) for x, y in pts]

    def poly(self, pts, v: int = 255):
        self.d.polygon(self._p(pts), fill=v)

    def ellipse(self, cx, cy, rx, ry, v: int = 255):
        s = self.ss
        self.d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=v)

    def circle(self, cx, cy, r, v: int = 255):
        self.ellipse(cx, cy, r, r, v)

    def ring(self, cx, cy, r, width, v: int = 255):
        """Ring whose stroke is centred on radius r."""
        s = self.ss
        ro = r + width / 2
        self.d.ellipse([(cx - ro) * s, (cy - ro) * s, (cx + ro) * s, (cy + ro) * s], outline=v,
                       width=max(1, int(round(width * s))))

    def line(self, pts, width, v: int = 255, caps: bool = True):
        s = self.ss
        self.d.line(self._p(pts), fill=v, width=max(1, int(round(width * s))), joint="curve")
        if caps:
            for x, y in (pts[0], pts[-1]):
                self.circle(x, y, width / 2, v)

    def rect(self, x0, y0, x1, y1, v: int = 255, radius: float = 0, outline: float = 0):
        s = self.ss
        box = [x0 * s, y0 * s, x1 * s, y1 * s]
        if outline:
            self.d.rounded_rectangle(box, radius=radius * s, outline=v, width=max(1, int(round(outline * s))))
        else:
            self.d.rounded_rectangle(box, radius=radius * s, fill=v)

    def arc(self, cx, cy, r, a0, a1, width, v: int = 255):
        """Arc centred on radius r from angle a0 to a1 (degrees, PIL convention: 0 = +x, clockwise)."""
        s = self.ss
        ro = r + width / 2
        self.d.arc([(cx - ro) * s, (cy - ro) * s, (cx + ro) * s, (cy + ro) * s], a0, a1, fill=v,
                   width=max(1, int(round(width * s))))

    def text(self, x, y, txt, path, size, anchor="mm", v: int = 255, weight=None, spacing: float = 0):
        f = font(path, size * self.ss, weight)
        if not spacing:
            self.d.text((x * self.ss, y * self.ss), txt, font=f, fill=v, anchor=anchor)
            return
        total = sum(f.getlength(c) for c in txt) + spacing * self.ss * (len(txt) - 1)
        if anchor[0] == "m":
            cx = x * self.ss - total / 2
        elif anchor[0] == "r":
            cx = x * self.ss - total
        else:
            cx = x * self.ss
        for c in txt:
            self.d.text((cx, y * self.ss), c, font=f, fill=v, anchor="l" + anchor[1])
            cx += f.getlength(c) + spacing * self.ss

    def paste_rotated(self, mask_img: Image.Image, cx, cy, angle_deg):
        """Max-composite an 'L' image (drawn at ss scale) rotated CCW by angle about its centre at (cx, cy)."""
        r = mask_img.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
        x0 = int(cx * self.ss - r.width / 2)
        y0 = int(cy * self.ss - r.height / 2)
        base = self.im.crop((x0, y0, x0 + r.width, y0 + r.height))
        self.im.paste(ImageChops.lighter(base, r), (x0, y0))

    def arr(self) -> np.ndarray:
        im = self.im.resize((self.w, self.h), Image.BOX) if self.ss > 1 else self.im
        return np.asarray(im, np.float32) / 255.0


def text_mask(txt, path, size, ss=4, weight=None, pad=8, spacing: float = 0) -> Image.Image:
    """Tight 'L' image of a text run at ss scale (for rotated / jittered placement)."""
    f = font(path, size * ss, weight)
    l, t, r, b = f.getbbox(txt)
    extra = int(spacing * ss * max(0, len(txt) - 1))
    im = Image.new("L", (int(r - l) + extra + 2 * pad * ss, int(b - t) + 2 * pad * ss), 0)
    d = ImageDraw.Draw(im)
    if not spacing:
        d.text((pad * ss - l, pad * ss - t), txt, font=f, fill=255)
    else:
        x = pad * ss - l
        for c in txt:
            d.text((x, pad * ss - t), c, font=f, fill=255)
            x += f.getlength(c) + spacing * ss
    return im


def rot_text(pen: Pen, x, y, txt, path, size, angle=0.0, weight=None, spacing=0.0):
    pen.paste_rotated(text_mask(txt, path, size, pen.ss, weight, spacing=spacing), x, y, angle)


def arc_text(pen: Pen, cx, cy, r, txt, path, size, a_mid=-90.0, spacing=1.0, weight=None, inward=False):
    """Text set along a circle of radius r (baseline), centred at angle a_mid (deg, 0 = +x, +90 = down).
    Letters stand on the outside of the circle (top reading clockwise), or inside when inward."""
    f = font(path, size, weight)
    widths = [f.getlength(c) * spacing for c in txt]
    total = sum(widths)
    a = math.radians(a_mid) - (total / r) / 2 * (-1 if inward else 1)
    for c, wdt in zip(txt, widths):
        step = wdt / r
        am = a + (step / 2) * (-1 if inward else 1)
        x, y = cx + r * math.cos(am), cy + r * math.sin(am)
        if c != " ":
            rot = -math.degrees(am) - 90 if not inward else -math.degrees(am) + 90
            rot_text(pen, x, y, c, path, size, rot, weight)
        a += step * (-1 if inward else 1)


def typed(pen: Pen, x, y, txt, size, rng, path=None, jitter=0.7, fade=(0.72, 1.0), anchor="ls"):
    """Typewriter text: per-character jitter and uneven ink. (x, y) = baseline start."""
    path = path or F_TYPE
    f = font(path, size * pen.ss)
    s = pen.ss
    adv = f.getlength("M")
    if anchor[0] == "m":
        x -= adv * len(txt) / s / 2
    elif anchor[0] == "r":
        x -= adv * len(txt) / s
    cx = x * s
    for c in txt:
        if c != " ":
            v = int(255 * rng.uniform(*fade))
            dx, dy = rng.normal(0, jitter * 0.6) * s, rng.normal(0, jitter * 0.5) * s
            pen.d.text((cx + dx, y * s + dy), c, font=f, fill=v, anchor="ls")
            if rng.random() < 0.12:  # double strike / heavy key
                pen.d.text((cx + dx + 0.6 * s, y * s + dy), c, font=f, fill=int(v * 0.6), anchor="ls")
        cx += adv


def ink(mask: np.ndarray, seed: int, amount: float = 0.35, scale: float = 2.5) -> np.ndarray:
    """Uneven ink / worn print: modulate a mask with fine noise."""
    n = noise(mask.shape[0], mask.shape[1], scale, 2, seed)
    return mask * np.clip(1 - amount + amount * 1.5 * n, 0, 1)


def white_rgba(mask: np.ndarray) -> Image.Image:
    rgb = np.full(mask.shape + (3,), 255.0, np.float32)
    return to_img(rgb, mask)


def _bez(p0, p1, p2, n=24):
    t = np.linspace(0, 1, n)
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in t]


def stamp_mask(w, h, seed, amount=0.45):
    """Rubber-stamp texture: blotchy coverage with speckle gaps."""
    n1 = noise(h, w, 9, 3, seed)
    n2 = noise(h, w, 2.2, 1, seed + 1)
    return np.clip(1 - amount + amount * 1.6 * n1, 0, 1) * (n2 > 0.22)


# =================================================================================================
# Glyphs (unit coordinates: the 512 box is [-0.5, 0.5]^2, +y down)
# =================================================================================================
MARK_RING_R = 0.384      # ring centreline radius (outer diameter = 2 * (0.384 + 0.016) = 0.80)
MARK_RING_W = 0.032
MARK_MERIDIAN_W = 0.030
MARK_MERIDIAN_HALF = 0.484
MARK_TICK = (0.432, 0.478, 0.022)   # r0, r1, width (Chapter 1 emblem's 12 ticks; 12 and 6 o'clock are the meridian)

SIGN_R = 0.40            # crescent outer radius -> sign height 0.80
SIGN_T = 0.112           # crescent thickness at its back
SIGN_PHI = 50.0          # horn angle from the opening axis (deg)
SIGN_DOT_R = 0.043
SIGN_DOT_DY = 0.165
SIGN_DOT_DX = 0.045      # dot column x relative to the outer circle centre


def _sign_geometry():
    """Return (outer centre x, inner centre x, inner radius, dot x, horn x) in unit coords, centred."""
    R, t, phi = SIGN_R, SIGN_T, math.radians(SIGN_PHI)
    d = (t * t - 2 * R * t) / (2 * t - 2 * R * (1 + math.cos(phi)))
    r2 = R + d - t
    horn = R * math.cos(phi)
    right = max(horn, SIGN_DOT_DX + SIGN_DOT_R)
    a = -(-R + right) / 2.0      # centre the bounding box
    return a, a + d, r2, a + SIGN_DOT_DX, a + horn


def draw_mark(pen: Pen, cx, cy, size, v=255, ticks=True, ring_w=None, line_w=None):
    s = size
    rw = (ring_w or MARK_RING_W) * s
    pen.ring(cx, cy, MARK_RING_R * s, rw, v)
    lw = (line_w or MARK_MERIDIAN_W) * s
    pen.rect(cx - lw / 2, cy - MARK_MERIDIAN_HALF * s, cx + lw / 2, cy + MARK_MERIDIAN_HALF * s, v)
    if ticks:
        r0, r1, tw = MARK_TICK
        for k in range(12):
            if k in (3, 9):
                continue
            a = 2 * math.pi * k / 12
            ca, sa = math.cos(a), math.sin(a)
            pen.line([(cx + r0 * s * ca, cy + r0 * s * sa), (cx + r1 * s * ca, cy + r1 * s * sa)], tw * s, v, caps=False)


def sign_end_point(progress: float):
    """Unit-coordinate position of the pen tip when the sign is drawn to `progress` (see sign_mask)."""
    oa, _, _, dx, _ = _sign_geometry()
    if progress < 0.8:
        total = 360.0 - 2 * SIGN_PHI
        ang = math.radians(-SIGN_PHI - total * progress / 0.8)
        r = SIGN_R - SIGN_T * 0.5 * (0.3 + 0.7 * abs(math.sin((ang - math.pi) / 2 + math.pi / 2)))
        return oa + r * math.cos(ang), r * math.sin(ang)
    k = min(2, int((progress - 0.8) / 0.2 * 3))
    return dx, (k - 1) * SIGN_DOT_DY


def sign_mask(size: int, progress: float = 1.0, ss: int = 4) -> np.ndarray:
    """Leyla's sign as a float mask (size x size), centred. progress < 1 draws it partially
    (crescent swept from the top horn anticlockwise, then the dots) for the film frame."""
    pen = Pen(size, size, ss)
    c = size / 2
    oa, ia, r2, dx, _ = _sign_geometry()
    R = SIGN_R * size
    pen.circle(c + oa * size, c, R)
    pen.circle(c + ia * size, c, r2 * size, 0)
    m = pen.arr()
    if progress < 1.0:
        yy, xx = np.mgrid[0:size, 0:size]
        ang = np.degrees(np.arctan2(yy - c, xx - (c + oa * size)))  # 0 = +x, +90 = down
        sweep = np.mod(-SIGN_PHI - ang, 360.0)        # 0 at the top horn, growing anticlockwise on screen
        total = 360.0 - 2 * SIGN_PHI
        keep = sweep <= total * min(1.0, progress / 0.8)
        m = m * blur(keep.astype(np.float32), size * 0.004)
    dots = Pen(size, size, ss)
    nd = 3 if progress >= 1.0 else max(0, int((progress - 0.8) / 0.2 * 3 + 1e-6))
    for k in range(nd):
        dots.circle(c + dx * size, c + (k - 1) * SIGN_DOT_DY * size, SIGN_DOT_R * size)
    return np.maximum(m, dots.arr())


def mark_mask(size: int, ss: int = 4, **kw) -> np.ndarray:
    pen = Pen(size, size, ss)
    draw_mark(pen, size / 2, size / 2, size, **kw)
    return pen.arr()


def glyph_mark():
    save(white_rgba(mark_mask(512)), "glyph_mark.png")


def glyph_sign():
    save(white_rgba(sign_mask(512)), "glyph_sign.png")


def vault_engraving():
    """Composed programmatically from the two glyph images: the mark upright at scale 1 plus the sign
    rotated 90 deg clockwise and scaled 0.55, both centred. Etched-glass look: thin cut contours
    (alpha ~0.6) over a faint frosted fill."""
    mpath, spath = os.path.join(OUT, "glyph_mark.png"), os.path.join(OUT, "glyph_sign.png")
    if not (os.path.exists(mpath) and os.path.exists(spath)):
        glyph_mark()
        glyph_sign()
    S = 512
    up = 4  # compose at 4x for clean contours
    mark = Image.open(mpath).getchannel("A").resize((S * up, S * up), Image.LANCZOS)
    sign = Image.open(spath).getchannel("A")
    n = int(round(S * up * SIGN_IN_VAULT_SCALE))
    sign_s = sign.resize((n, n), Image.LANCZOS).rotate(-SIGN_IN_VAULT_ROT_CW, resample=Image.BICUBIC)  # PIL: negative = clockwise
    comb = Image.new("L", (S * up, S * up), 0)
    comb.paste(sign_s, ((S * up - n) // 2, (S * up - n) // 2))
    m = np.maximum(np.asarray(mark, np.float32), np.asarray(comb, np.float32)) / 255.0
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((S, S), Image.BOX), np.float32) / 255.0
    # contour = band around the 0.5 iso-line of the shape (about 2.6 px wide)
    sm = blur(m, 0.8)
    edge = np.clip(1.0 - np.abs(sm - 0.5) / 0.32, 0, 1)
    inner = np.clip(m - blur(m, 3.0), 0, 1)          # a second, finer cut just inside the edge
    fill = m * 0.16
    frost = (0.85 + 0.3 * noise(S, S, 1.4, 1, 77)) * fill
    a = np.clip(frost + 0.60 * edge + 0.15 * inner, 0, 0.66)
    save(white_rgba(a), "vault_engraving.png")


# =================================================================================================
# Pictograms (shared by the routing chart and the destination ring). Unit box [-0.5, 0.5]^2, +y down.
# =================================================================================================
def picto(pen: Pen, kind: str, cx: float, cy: float, s: float, v: int = 255):
    """Single-colour pictogram (filled shapes with cut-outs) centred at (cx, cy), box size s px."""
    def P(x, y):
        return (cx + x * s, cy + y * s)

    def poly(pts, val=v):
        pen.poly([P(x, y) for x, y in pts], val)

    def circ(x, y, r, val=v):
        pen.circle(cx + x * s, cy + y * s, r * s, val)

    def line(pts, w, val=v, caps=True):
        pen.line([P(x, y) for x, y in pts], w * s, val, caps)

    def rect(x0, y0, x1, y1, val=v, rad=0.0):
        pen.rect(cx + x0 * s, cy + y0 * s, cx + x1 * s, cy + y1 * s, val, radius=rad * s)

    if kind == "star":       # four-pointed star with concave sides (Strand's ✦)
        pts = []
        for t in np.linspace(0, 2 * np.pi, 200, endpoint=False):
            c, sn = math.cos(t), math.sin(t)
            pts.append((0.49 * math.copysign(abs(c) ** 3.3, c), 0.49 * math.copysign(abs(sn) ** 3.3, sn)))
        poly(pts)
    elif kind == "book":     # open book
        for sg in (-1, 1):
            top = _bez((sg * 0.035, -0.20), (sg * 0.22, -0.36), (sg * 0.47, -0.27))
            bot = _bez((sg * 0.47, 0.22), (sg * 0.22, 0.13), (sg * 0.035, 0.28))
            poly(top + bot)
            cov_top = _bez((sg * 0.0, 0.28), (sg * 0.22, 0.14), (sg * 0.47, 0.22))
            cov_bot = _bez((sg * 0.50, 0.32), (sg * 0.22, 0.24), (sg * 0.0, 0.40))
            poly(cov_top + [(sg * 0.50, 0.22)] + cov_bot)
            line(_bez((sg * 0.03, 0.285), (sg * 0.22, 0.155), (sg * 0.48, 0.225)), 0.035, 0, caps=False)
            for f in (0.24, 0.44, 0.64):
                pts = []
                for t in np.linspace(0.16, 0.86, 18):
                    # point between the top and bottom curves at parameter t
                    tx = (1 - t) ** 2 * sg * 0.035 + 2 * (1 - t) * t * sg * 0.22 + t * t * sg * 0.47
                    ty = (1 - t) ** 2 * -0.20 + 2 * (1 - t) * t * -0.36 + t * t * -0.27
                    by = (1 - t) ** 2 * 0.28 + 2 * (1 - t) * t * 0.13 + t * t * 0.22
                    pts.append((tx, ty + (by - ty) * f))
                line(pts, 0.032, 0, caps=False)
        rect(-0.018, -0.24, 0.018, 0.40, 0)
    elif kind == "flask":    # Erlenmeyer flask with liquid and bubbles
        w = 0.075
        outline = [(-0.10, -0.40), (-0.10, -0.11), (-0.38, 0.35), (-0.34, 0.43), (0.34, 0.43), (0.38, 0.35),
                   (0.10, -0.11), (0.10, -0.40)]
        line(outline, w)
        rect(-0.17, -0.48, 0.17, -0.39, rad=0.025)
        top_y = 0.10
        hw = 0.10 + (top_y + 0.11) * (0.28 / 0.46)
        wave = [(x, top_y + 0.018 * math.sin(x * 22)) for x in np.linspace(-hw, hw, 16)]
        poly(wave + [(0.38, 0.35), (0.34, 0.43), (-0.34, 0.43), (-0.38, 0.35)])
        for bx, by, br in ((-0.08, 0.30, 0.042), (0.09, 0.34, 0.032), (0.03, 0.22, 0.026)):
            circ(bx, by, br, 0)
    elif kind == "film":     # film reel with a film tail
        rx, ry = -0.07, -0.08
        rect(rx, 0.18, 0.48, 0.40, rad=0.02)
        circ(rx, ry, 0.40)
        for k in range(5):
            a = math.radians(-90 + 72 * k)
            circ(rx + 0.225 * math.cos(a), ry + 0.225 * math.sin(a), 0.10, 0)
        circ(rx, ry, 0.045, 0)
        for x in np.arange(0.06, 0.46, 0.085):
            rect(x, 0.205, x + 0.04, 0.245, 0, rad=0.008)
            rect(x, 0.335, x + 0.04, 0.375, 0, rad=0.008)
    elif kind == "envelope":
        rect(-0.47, -0.31, 0.47, 0.31, rad=0.04)
        line([(-0.43, -0.27), (0.0, 0.07), (0.43, -0.27)], 0.065, 0, caps=False)
        line([(-0.43, 0.27), (-0.13, 0.0)], 0.045, 0, caps=False)
        line([(0.43, 0.27), (0.13, 0.0)], 0.045, 0, caps=False)
    elif kind == "padlock":
        pen.arc(cx, cy - 0.13 * s, 0.20 * s, 180, 360, 0.095 * s, v)
        rect(-0.2475, -0.14, -0.1525, 0.02)
        rect(0.1525, -0.14, 0.2475, 0.02)
        rect(-0.34, -0.03, 0.34, 0.45, rad=0.07)
        circ(0, 0.15, 0.075, 0)
        poly([(-0.035, 0.17), (0.035, 0.17), (0.06, 0.33), (-0.06, 0.33)], 0)
    elif kind == "memo":     # folded note
        poly([(-0.34, -0.45), (0.15, -0.45), (0.34, -0.26), (0.34, 0.45), (-0.34, 0.45)])
        line([(0.15, -0.45), (0.15, -0.26), (0.34, -0.26)], 0.04, 0, caps=False)
        for i, y in enumerate((-0.22, -0.08, 0.06, 0.20, 0.33)):
            line([(-0.24, y), (0.24 if i else 0.04, y)], 0.045, 0, caps=False)
    else:
        raise ValueError(kind)


def picto_mask(kind: str, size: int, fill: float = 0.86, ss: int = 4) -> np.ndarray:
    pen = Pen(size, size, ss)
    picto(pen, kind, size / 2, size / 2, size * fill)
    return pen.arr()


# ---- coloured enamel item icons (routing chart, left column) -------------------------------------
INK = "#22262B"


def item_icon(kind: str, S: int, seed: int = 0):
    """Small multi-colour enamel illustration of a dispatch item. Returns (rgb, alpha) S x S."""
    s = S
    rgb = np.zeros((S, S, 3), np.float32)
    alpha = np.zeros((S, S), np.float32)
    layers = []  # (mask, colour)

    def pen():
        return Pen(S, S, 4)

    def P(x, y):
        return (S / 2 + x * s, S / 2 + y * s)

    if kind == "memo":
        a = pen()
        pts = [(-0.30, -0.42), (0.14, -0.42), (0.32, -0.24), (0.32, 0.42), (-0.30, 0.42)]
        a.poly([P(*p) for p in pts])
        o = pen()
        o.line([P(*p) for p in pts + [pts[0]]], 0.045 * s)
        fold = pen()
        fold.poly([P(0.14, -0.42), P(0.14, -0.24), P(0.32, -0.24)])
        fo = pen()
        fo.line([P(0.14, -0.42), P(0.14, -0.24), P(0.32, -0.24)], 0.035 * s)
        t = pen()
        for i, y in enumerate((-0.20, -0.07, 0.06, 0.19, 0.31)):
            t.line([P(-0.21, y), P(0.22 if i else 0.02, y)], 0.035 * s)
        layers = [(a.arr(), "#F1EBDD"), (fold.arr(), "#D6CDB8"), (t.arr(), "#6E7680"), (o.arr(), INK), (fo.arr(), INK)]
    elif kind == "request_card":
        a = pen()
        clip = 0.07
        pts = [(-0.46 + clip, -0.29), (0.46, -0.29), (0.46, 0.29), (-0.46, 0.29), (-0.46, -0.29 + clip)]
        a.poly([P(*p) for p in pts])
        o = pen()
        o.line([P(*p) for p in pts + [pts[0]]], 0.04 * s)
        holes = pen()
        for k in range(8):
            hx = -0.46 + (k + 0.5) * 0.92 / 8
            holes.ring(*P(hx, -0.185), 0.032 * s, 0.018 * s)
        red = pen()
        red.rect(*P(-0.36, -0.08), *P(0.36, -0.045))
        lines = pen()
        for y in (0.06, 0.15, 0.23):
            lines.line([P(-0.36, y), P(0.36, y)], 0.016 * s, caps=False)
        layers = [(a.arr(), "#D8C192"), (lines.arr(), "#8A7650"), (red.arr(), "#A8322A"), (holes.arr(), "#4A3A28"),
                  (o.arr(), INK)]
    elif kind == "vial":       # tilted test tube with amber liquid and a cork
        ax0, ay0, ax1, ay1 = -0.13, -0.30, 0.13, 0.34

        def at(t):
            return P(ax0 + (ax1 - ax0) * t, ay0 + (ay1 - ay0) * t)
        g = pen()
        g.line([at(0.0), at(1.0)], 0.26 * s)
        gm = g.arr()
        liq = pen()
        liq.line([at(0.50), at(1.0)], 0.19 * s)
        lq = liq.arr()
        cork = pen()
        cork.line([at(-0.16), at(0.04)], 0.24 * s, caps=False)
        co = cork.arr()
        hl = pen()
        hl.line([P(ax0 - 0.07, ay0 + 0.06), P(ax1 - 0.08, ay1 - 0.10)], 0.03 * s)
        edge = np.clip(gm - np.clip(blur(gm, 2.0) * 2 - 1, 0, 1), 0, 1)
        cedge = np.clip(co - np.clip(blur(co, 2.0) * 2 - 1, 0, 1), 0, 1)
        layers = [(gm, "#D5E6E2"), (lq, "#C98A1E"), (hl.arr() * gm, "#FFFFFF"), (edge, INK), (co, "#8A5A34"),
                  (cedge, INK)]
    elif kind == "film_can":
        body = pen()
        body.rect(*P(-0.40, -0.08), *P(0.40, 0.20))
        body.ellipse(*P(0, 0.20), 0.40 * s, 0.16 * s)
        top = pen()
        top.ellipse(*P(0, -0.08), 0.40 * s, 0.16 * s)
        lid_ring = pen()
        lid_ring.ellipse(*P(0, -0.08), 0.31 * s, 0.115 * s)
        lid_in = pen()
        lid_in.ellipse(*P(0, -0.08), 0.27 * s, 0.095 * s)
        label = pen()
        label.rect(*P(-0.18, 0.04), *P(0.18, 0.20))
        o = pen()
        o.ellipse(*P(0, -0.08), 0.40 * s, 0.16 * s)
        oi = pen()
        oi.ellipse(*P(0, -0.08), 0.37 * s, 0.135 * s)
        bm = body.arr()
        tm = top.arr()
        edge = np.clip(np.maximum(bm, tm) - np.clip(blur(np.maximum(bm, tm), 2.2) * 2 - 1, 0, 1), 0, 1)
        layers = [(bm, "#6F7A74"), (tm, "#9AA59F"), (np.clip(lid_ring.arr() - lid_in.arr(), 0, 1), "#5E6862"),
                  (label.arr(), "#E3D7B8"), (edge, INK)]
    elif kind == "envelope_sealed":
        a = pen()
        a.rect(*P(-0.45, -0.29), *P(0.45, 0.29), radius=0.03 * s)
        fl = pen()
        fl.line([P(-0.42, -0.26), P(0, 0.06), P(0.42, -0.26)], 0.035 * s, caps=False)
        fl.line([P(-0.42, 0.26), P(-0.12, 0.0)], 0.03 * s, caps=False)
        fl.line([P(0.42, 0.26), P(0.12, 0.0)], 0.03 * s, caps=False)
        seal = pen()
        for k in range(9):
            ang = 2 * math.pi * k / 9
            seal.circle(*P(0.0 + 0.085 * math.cos(ang), 0.07 + 0.085 * math.sin(ang)), 0.045 * s)
        seal.circle(*P(0, 0.07), 0.10 * s)
        st = pen()
        picto(st, "star", *P(0, 0.07), 0.13 * s)
        am = a.arr()
        edge = np.clip(am - np.clip(blur(am, 2.2) * 2 - 1, 0, 1), 0, 1)
        layers = [(am, "#F1EBDD"), (fl.arr(), INK), (edge, INK), (seal.arr(), "#9E2A22"), (st.arr(), "#C8574A")]
    elif kind == "no_entry":
        a = pen()
        a.circle(S / 2, S / 2, 0.42 * s)
        b = pen()
        b.rect(*P(-0.28, -0.075), *P(0.28, 0.075), radius=0.02 * s)
        layers = [(a.arr(), "#B23A2E"), (b.arr(), "#F1EBDD")]
    else:
        raise ValueError(kind)
    for m, col in layers:
        rgb = paint(rgb, m, col)
        alpha = np.maximum(alpha, m)
    return rgb, alpha


def brass_disc_rgb(S: int, seed: int, base="#5B4A2E", r_frac=0.5) -> np.ndarray:
    """Dark aged brass, circularly brushed, lit from the top-left (float sRGB)."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    ang = np.arctan2(yy - c, xx - c)
    rr = np.hypot(xx - c, yy - c) / (S * r_frac)
    # circular brushing: noise indexed by radius (streaks are rings)
    rings = noise(1, 2048, 3, 2, seed)[0]
    ri = np.clip((rr * 1400).astype(int), 0, 2047)
    brush = rings[ri]
    n = noise(S, S, 60, 3, seed + 1)
    b = hexf(base)
    shade = 0.85 + 0.25 * n + 0.10 * (brush - 0.5) + 0.12 * np.cos(ang + 2.35) * rr
    rgb = b[None, None, :] * shade[..., None]
    patina = smooth(0.62, 0.85, noise(S, S, 18, 3, seed + 2))
    rgb = paint(rgb, patina, "#3E4A3A", 0.35)
    return rgb


# =================================================================================================
# Routing chart (600 x 840, enamel sign)
# =================================================================================================
def routing_chart():
    W, H = 600, 840
    r = np.random.default_rng(510)
    n = noise(H, W, 90, 4, 511)
    rgb = solid(H, W, "#E6DCC2") * (0.95 + 0.07 * n)[..., None]
    # enamel ripple + gloss gradient
    rgb = rgb * (0.985 + 0.02 * noise(H, W, 6, 2, 512))[..., None]
    # border: a dark blue enamel frame line inside the edge
    fr = Pen(W, H, 4)
    fr.rect(14, 14, W - 14, H - 14, radius=22, outline=7)
    rgb = paint(rgb, fr.arr(), "#1F3550")
    # header band
    hb = Pen(W, H, 4)
    hb.rect(28, 28, W - 28, 150, radius=12)
    hm = hb.arr()
    rgb = paint(rgb, hm, "#1F3550")
    ht = Pen(W, H, 4)
    ht.text(W / 2 + 34, 76, "PNEUMATIC", F_GOTHIC, 54, spacing=3)
    ht.text(W / 2 + 34, 124, "POST", F_GOTHIC, 54, spacing=14)
    # canister icon in the header
    cx, cy = 92, 89
    ht.rect(cx - 17, cy - 44, cx + 17, cy + 44, radius=15)
    ht.rect(cx - 20, cy - 30, cx + 20, cy - 22, 0)
    ht.rect(cx - 20, cy + 22, cx + 20, cy + 30, 0)
    ht.rect(cx - 6, cy - 54, cx + 6, cy - 44, radius=3)
    rgb = paint(rgb, ht.arr(), "#EDE4CC")
    # rows
    rows = [("memo", "star"), ("request_card", "book"), ("vial", "flask"), ("film_can", "film"),
            ("envelope_sealed", "envelope")]
    y0, dy = 205, 112
    lines = Pen(W, H, 4)
    for i in range(len(rows) + 1):
        y = y0 - dy / 2 + i * dy
        lines.rect(46, y - 1, W - 46, y + 1)
    rgb = paint(rgb, lines.arr(), "#1F3550", 0.35)
    TILE = 92
    for i, (item, dest) in enumerate(rows):
        y = y0 + i * dy
        # item tile (white enamel square)
        tile = Pen(W, H, 4)
        tile.rect(70, y - TILE / 2, 70 + TILE, y + TILE / 2, radius=12)
        tm = tile.arr()
        rgb = paint(rgb, blur(tm, 3) * 0.6, "#7E7460", 0.35)
        rgb = paint(rgb, tm, "#F4EEE0")
        irgb, ia = item_icon(item, 84, i)
        x0i, y0i = int(70 + (TILE - 84) / 2), int(y - 42)
        sub = rgb[y0i:y0i + 84, x0i:x0i + 84]
        rgb[y0i:y0i + 84, x0i:x0i + 84] = sub * (1 - ia[..., None]) + irgb * ia[..., None]
        # arrow (tube): dashed shaft + head
        ar = Pen(W, H, 4)
        for xd in range(190, 382, 30):
            ar.rect(xd, y - 6, xd + 18, y + 6, radius=3)
        ar.poly([(384, y - 24), (426, y), (384, y + 24)])
        rgb = paint(rgb, ar.arr(), "#1F3550")
        # destination roundel: cream symbol on dark brass (same look as the dial ring)
        rgb = roundel(rgb, 482, y, 46, dest, 520 + i)
    # bottom row: no entry -> padlock (sealed)
    y = y0 + len(rows) * dy + 18
    band = Pen(W, H, 4)
    band.rect(46, y - 50, W - 46, y + 50, radius=10)
    bm = band.arr()
    rgb = paint(rgb, bm, "#E9DECA")
    stripes = Pen(W, H, 4)
    for xs in range(0, W + 200, 44):
        stripes.poly([(xs, y - 50), (xs + 22, y - 50), (xs - 78, y + 50), (xs - 100, y + 50)])
    rgb = paint(rgb, stripes.arr() * bm, "#B23A2E", 0.88)
    irgb, ia = item_icon("no_entry", 92)
    x0i, y0i = 70, int(y - 46)
    sub = rgb[y0i:y0i + 92, x0i:x0i + 92]
    rgb[y0i:y0i + 92, x0i:x0i + 92] = sub * (1 - ia[..., None]) + irgb * ia[..., None]
    rgb = roundel(rgb, 482, y, 46, "padlock", 530)
    # red "sealed" bar across the arrow position
    sb = Pen(W, H, 4)
    sb.rect(186, y - 13, 428, y + 13, radius=6)
    rgb = paint(rgb, sb.arr(), "#B23A2E")
    sbt = Pen(W, H, 4)
    for xd in range(198, 420, 36):
        sbt.rect(xd, y - 3, xd + 20, y + 3, radius=2)
    rgb = paint(rgb, sbt.arr(), "#F1EBDD", 0.9)
    # mounting rivets in the corners and a small plate number
    for rx, ry in ((36, 36), (W - 36, 36), (36, H - 36), (W - 36, H - 36)):
        rv = Pen(W, H, 4)
        rv.circle(rx, ry, 8)
        rgb = paint(rgb, rv.arr(), "#8F8A7E")
        hl = Pen(W, H, 4)
        hl.circle(rx - 2, ry - 2, 3)
        rgb = paint(rgb, hl.arr(), "#E8E2D4", 0.8)
    pn = Pen(W, H, 4)
    pn.text(W / 2, H - 36, "ARCHIVE  B", F_SANS_B, 18, spacing=3)
    rgb = paint(rgb, pn.arr(), "#1F3550", 0.75)
    # wear: enamel chips (dark iron showing) near the edges, grime, fine crazing
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dmin = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    chip = (smooth(0.80, 0.86, noise(H, W, 7, 3, 540)) * (dmin < 22)).astype(np.float32)
    rgb = paint(rgb, blur(chip, 0.6), "#2A2622", 0.9)
    rgb = paint(rgb, np.clip(blur(chip, 2.0) - chip, 0, 1), "#6B4A2E", 0.5)
    grime = smooth(0.4, 1.0, noise(H, W, 80, 4, 541)) * 0.10 + edge_wear(W, H, 542, 40, 0.18)
    rgb = multiply(rgb, grime, "#6E5A3A")
    craze = Pen(W, H, 2)
    for _ in range(26):
        x, y = r.uniform(0, W), r.uniform(0, H)
        pts = [(x, y)]
        ang = r.uniform(0, 6.28)
        for _ in range(int(r.integers(3, 8))):
            ang += r.normal(0, 0.6)
            x += 9 * math.cos(ang)
            y += 9 * math.sin(ang)
            pts.append((x, y))
        craze.line(pts, 0.6, caps=False)
    rgb = multiply(rgb, craze.arr(), "#7A6E58", 0.5)
    save(to_img(rgb), "routing_chart.png")


def roundel(rgb: np.ndarray, cx: float, cy: float, R: float, kind: str, seed: int) -> np.ndarray:
    """Composite a dark-brass roundel with a cream enamel pictogram onto rgb (in place style)."""
    H, W = rgb.shape[:2]
    S = int(2 * R + 8)
    x0, y0 = int(round(cx - S / 2)), int(round(cy - S / 2))
    disc = Pen(S, S, 4)
    disc.circle(S / 2, S / 2, R)
    dm = disc.arr()
    br = brass_disc_rgb(S, seed, r_frac=R / S)
    # bevel: bright upper-left rim, dark lower-right
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - S / 2, yy - S / 2) / R
    ang = np.arctan2(yy - S / 2, xx - S / 2)
    rim = smooth(0.84, 0.96, rr) * (1 - smooth(0.97, 1.0, rr))
    br = br * (1 + 0.45 * rim * np.cos(ang + 2.35))[..., None]
    inner_ring = smooth(0.80, 0.82, rr) * (1 - smooth(0.84, 0.86, rr))
    br = paint(br, inner_ring, "#2A2216", 0.7)
    pm = picto_mask(kind, S, fill=1.0 * (R * 1.12) / S)
    shadow = np.roll(np.roll(blur(pm, 1.2), 2, 0), 1, 1)
    br = paint(br, shadow * dm, "#15110A", 0.6)
    br = paint(br, pm * dm, "#E9DFC6")
    br = paint(br, np.clip(pm - np.roll(pm, 2, 0), 0, 1) * dm, "#FFF8E8", 0.35)
    # drop shadow of the roundel on the enamel
    sh = np.roll(np.roll(blur(dm, 3), 3, 0), 2, 1)
    sub = rgb[y0:y0 + S, x0:x0 + S]
    sub = multiply(sub, sh * 0.5, "#5A5040")
    sub = sub * (1 - dm[..., None]) + br * dm[..., None]
    rgb[y0:y0 + S, x0:x0 + S] = sub
    return rgb


# =================================================================================================
# Destination ring (512 x 512, RGBA: transparent centre and outside)
# =================================================================================================
DEST_R_IN, DEST_R_OUT, DEST_R_SYM = 0.29, 0.492, 0.393   # fractions of the image width


def dest_symbols():
    S = 512
    c = (S - 1) / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - c, yy - c) / S
    ang = np.arctan2(yy - c, xx - c)
    ring = Pen(S, S, 4)
    ring.circle(S / 2, S / 2, DEST_R_OUT * S)
    ring.circle(S / 2, S / 2, DEST_R_IN * S, 0)
    alpha = ring.arr()
    rgb = brass_disc_rgb(S, 600, base="#4E3F27")
    # bevels at both edges + an engraved groove on each side of the symbol track
    outer = smooth(DEST_R_OUT - 0.022, DEST_R_OUT - 0.004, rr)
    inner = 1 - smooth(DEST_R_IN + 0.004, DEST_R_IN + 0.020, rr)
    light = np.cos(ang + 2.35)
    rgb = rgb * (1 + 0.55 * outer * light - 0.45 * inner * light)[..., None]
    for rg in (DEST_R_OUT - 0.030, DEST_R_IN + 0.028):
        g = smooth(rg - 0.004, rg - 0.001, rr) * (1 - smooth(rg + 0.001, rg + 0.004, rr))
        rgb = paint(rgb, g, "#1E1810", 0.75)
        g2 = smooth(rg + 0.001, rg + 0.004, rr) * (1 - smooth(rg + 0.004, rg + 0.007, rr))
        rgb = paint(rgb, g2 * np.clip(light, 0, 1), "#C9A86A", 0.4)
    # six enamel symbols, d = 0..5 clockwise from 12 o'clock
    sym = Pen(S, S, 4)
    ticks = Pen(S, S, 4)
    for d, kind in enumerate(DEST_SYMBOLS):
        a = math.radians(-90 + 60 * d)
        px, py = S / 2 + DEST_R_SYM * S * math.cos(a), S / 2 + DEST_R_SYM * S * math.sin(a)
        picto(sym, kind, px, py, 0.135 * S)
        # index wedge on the inner groove, pointing at the knob
        ri = (DEST_R_IN + 0.012) * S
        tx, ty = S / 2 + ri * math.cos(a), S / 2 + ri * math.sin(a)
        nx, ny = math.cos(a), math.sin(a)
        ticks.poly([(tx - ny * 7 + nx * 10, ty + nx * 7 + ny * 10), (tx + ny * 7 + nx * 10, ty - nx * 7 + ny * 10),
                    (tx - nx * 2, ty - ny * 2)])
        # small engraved dots half-way between positions
        a2 = a + math.radians(30)
        ticks.circle(S / 2 + DEST_R_SYM * S * math.cos(a2), S / 2 + DEST_R_SYM * S * math.sin(a2), 3.0)
    sm = sym.arr()
    tm = ticks.arr()
    # cloisonne: dark cell outline, cream enamel, slight relief highlight
    cell = np.clip(blur(sm, 1.6) * 1.8, 0, 1)
    rgb = paint(rgb, cell, "#1A140C", 0.85)
    enamel = solid(S, S, "#E8DEC4") * (0.94 + 0.08 * noise(S, S, 20, 2, 601))[..., None]
    rgb = rgb * (1 - sm[..., None]) + enamel * sm[..., None]
    rgb = paint(rgb, np.clip(sm - np.roll(np.roll(sm, 2, 0), 2, 1), 0, 1), "#FFFBEF", 0.45)
    rgb = paint(rgb, np.clip(sm - np.roll(np.roll(sm, -2, 0), -2, 1), 0, 1), "#8C7A58", 0.4)
    rgb = paint(rgb, tm, "#E8DEC4", 0.95)
    # wear: enamel chips, grime in the grooves, polished rub on the top
    chips = smooth(0.84, 0.9, noise(S, S, 5, 2, 602)) * sm
    rgb = paint(rgb, chips, "#4A3B24", 0.8)
    rub = smooth(0.55, 0.9, noise(S, S, 50, 3, 603)) * (1 - sm)
    rgb = paint(rgb, rub, "#9C7F4C", 0.25)
    save(to_img(rgb, alpha), "dest_symbols.png")


# =================================================================================================
# Procedural portrait (badge photo) -- stylised 1970s ID photograph, original
# =================================================================================================
def portrait(w: int, h: int, seed: int = 41) -> np.ndarray:
    """Black-and-white studio ID portrait of a young woman with a dark bob (linear luminance 0..1)."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    # backdrop: soft light behind the head, darker corners
    lum = 0.50 + 0.22 * np.exp(-(((u - 0.42) / 0.45) ** 2 + ((v - 0.35) / 0.55) ** 2)) - 0.10 * v
    cx = 0.5 * w
    hy = 0.40 * h             # face centre
    fw, fh = 0.205 * w, 0.165 * h * (w / h) * (h / w) * 1.0
    fh = 0.175 * h
    ss = 4

    def P(px, py):
        return (cx + px * w, hy + py * h)

    def mask(draw):
        p = Pen(w, h, ss)
        draw(p)
        return p.arr()

    # shoulders: dark jacket with a white blouse collar
    def jacket(p):
        p.poly([P(-0.48, 0.62), P(-0.40, 0.40), P(-0.20, 0.31), P(-0.07, 0.27), P(0.07, 0.27), P(0.20, 0.31),
                P(0.40, 0.40), P(0.48, 0.62)])
    jm = mask(jacket)
    lum = lum * (1 - jm) + jm * (0.09 + 0.05 * (1 - v) + 0.04 * (u < 0.5))
    # lapels highlight (fabric fold)
    lap = mask(lambda p: (p.poly([P(-0.20, 0.31), P(-0.07, 0.27), P(-0.02, 0.45), P(-0.12, 0.62), P(-0.20, 0.62)]),
                          p.poly([P(0.20, 0.31), P(0.07, 0.27), P(0.02, 0.45), P(0.12, 0.62), P(0.20, 0.62)])))
    lum = lum * (1 - lap * 0.6) + lap * 0.6 * 0.16
    collar = mask(lambda p: (p.poly([P(-0.075, 0.262), P(0.0, 0.40), P(0.075, 0.262), P(0.11, 0.30), P(0.0, 0.47),
                                     P(-0.11, 0.30)])))
    lum = lum * (1 - collar) + collar * (0.80 - 0.15 * (u > 0.5))
    # neck (shadowed under the jaw)
    neck = mask(lambda p: p.poly([P(-0.07, 0.10), P(0.07, 0.10), P(0.075, 0.30), P(0.0, 0.40), P(-0.075, 0.30)]))
    neck_l = 0.52 - 0.18 * smooth(hy + 0.12 * h, hy + 0.20 * h, yy) * 0 - 0.12 * ((u - 0.5) * 4)
    jaw_shadow = 1 - 0.45 * np.exp(-((yy - (hy + 0.16 * h)) / (0.035 * h)) ** 2)
    lum = lum * (1 - neck) + neck * np.clip(neck_l * jaw_shadow, 0.15, 0.7)
    # face: egg-shaped, key light from camera left
    face = mask(lambda p: p.poly([(cx + fw * math.sin(t) * (0.92 if math.cos(t) < 0 else 1.0) *
                                   (1 - 0.18 * max(0, -math.cos(t)) ** 2),
                                   hy - fh * math.cos(t)) for t in np.linspace(0, 2 * math.pi, 120)]))
    nx = (xx - cx) / fw
    ny = (yy - hy) / fh
    key = 0.72 - 0.20 * nx - 0.06 * ny - 0.12 * np.clip(nx * nx + ny * ny - 0.5, 0, 1)
    fl = key.copy()
    # eye sockets, eyes, brows
    for sx in (-1, 1):
        ex, ey = cx + sx * 0.38 * fw, hy - 0.10 * fh
        sock = np.exp(-(((xx - ex) / (0.30 * fw)) ** 2 + ((yy - ey) / (0.16 * fh)) ** 2))
        fl = fl - 0.16 * sock
        eye = np.exp(-(((xx - ex) / (0.13 * fw)) ** 2 + ((yy - ey) / (0.045 * fh)) ** 2))
        fl = fl * (1 - 0.75 * eye)
        iris = np.exp(-(((xx - ex - 0.01 * fw) / (0.055 * fw)) ** 2 + ((yy - ey) / (0.05 * fh)) ** 2))
        fl = fl * (1 - 0.6 * iris)
        brow_y = ey - 0.17 * fh - 0.04 * fh * np.cos((xx - ex) / (0.3 * fw))
        brow = np.exp(-((yy - brow_y) / (0.025 * fh)) ** 2) * np.exp(-((xx - ex - sx * 0.03 * fw) / (0.24 * fw)) ** 4)
        fl = fl * (1 - 0.55 * brow)
    # nose: shadow on the far side, nostrils, highlight on the bridge
    nose_sh = np.exp(-(((xx - (cx + 0.10 * fw)) / (0.07 * fw)) ** 2) - (((yy - (hy + 0.12 * fh)) / (0.20 * fh)) ** 2))
    fl = fl - 0.12 * nose_sh
    nost = np.exp(-(((xx - cx) / (0.16 * fw)) ** 2 + ((yy - (hy + 0.30 * fh)) / (0.035 * fh)) ** 2))
    fl = fl - 0.14 * nost
    bridge = np.exp(-(((xx - (cx - 0.04 * fw)) / (0.05 * fw)) ** 2 + ((yy - (hy + 0.08 * fh)) / (0.18 * fh)) ** 2))
    fl = fl + 0.06 * bridge
    # mouth: dark line, lower lip highlight
    my = hy + 0.52 * fh
    mouth = np.exp(-(((xx - cx) / (0.26 * fw)) ** 4 + ((yy - my) / (0.022 * fh)) ** 2))
    fl = fl * (1 - 0.45 * mouth)
    lip = np.exp(-(((xx - cx) / (0.20 * fw)) ** 2 + ((yy - my - 0.06 * fh) / (0.035 * fh)) ** 2))
    fl = fl - 0.05 * lip
    chin = np.exp(-(((xx - cx) / (0.30 * fw)) ** 2 + ((yy - (hy + 0.80 * fh)) / (0.08 * fh)) ** 2))
    fl = fl + 0.03 * chin
    lum = lum * (1 - face) + face * np.clip(fl, 0.08, 0.95)
    # hair: dark bob with a side parting, framing the face to the jaw, a soft sheen
    def hair(p):
        pts = []
        for t in np.linspace(math.pi * 0.62, math.pi * 2.38, 80):
            rx = fw * 1.30
            ry = fh * 1.18
            px = cx + rx * math.cos(t) * 1.0
            py = hy - 0.10 * fh + ry * math.sin(t) * (1.0 if math.sin(t) < 0 else 0.0) - 0.02 * fh
            pts.append((px, py))
        # sides fall to the jaw line
        right = [(cx + fw * 1.30, hy + 0.05 * fh), (cx + fw * 1.22, hy + 0.62 * fh), (cx + fw * 0.98, hy + 0.80 * fh),
                 (cx + fw * 0.82, hy + 0.62 * fh), (cx + fw * 0.92, hy + 0.05 * fh)]
        left = [(cx - fw * 0.88, hy + 0.05 * fh), (cx - fw * 0.80, hy + 0.62 * fh), (cx - fw * 0.98, hy + 0.82 * fh),
                (cx - fw * 1.24, hy + 0.66 * fh), (cx - fw * 1.30, hy + 0.05 * fh)]
        p.poly(pts)
        p.poly(right)
        p.poly(left)
        # fringe sweeping from the parting (left) across the forehead
        p.poly([(cx - 0.55 * fw, hy - 1.15 * fh), (cx + 1.15 * fw, hy - 0.95 * fh), (cx + 0.95 * fw, hy - 0.30 * fh),
                (cx + 0.30 * fw, hy - 0.52 * fh), (cx - 0.40 * fw, hy - 0.60 * fh), (cx - 0.90 * fw, hy - 0.35 * fh)])
    hm = mask(hair)
    hm = np.clip(hm - 0.0, 0, 1)
    strands = noise(h, w * 4, 2.0, 1, seed + 3)[:, ::4]
    sheen = np.exp(-(((xx - (cx - 0.55 * fw)) / (0.35 * fw)) ** 2 + ((yy - (hy - 0.85 * fh)) / (0.22 * fh)) ** 2))
    hl = 0.07 + 0.05 * strands + 0.20 * sheen * (0.6 + 0.4 * strands)
    lum = lum * (1 - hm) + hm * hl
    lum = blur(lum, 0.8)
    lum = lum + r.normal(0, 0.02, lum.shape).astype(np.float32)
    return np.clip(lum, 0, 1)


# =================================================================================================
# Badge (860 x 540, RGBA: rounded corners)
# =================================================================================================
def badge():
    W, H = 860, 540
    r = np.random.default_rng(700)
    rgb = paper(W, H, base=(232, 224, 204), seed=701, stains=1, vignette=0.12, fibres=0.6)
    # guilloche security print (pale green rosette lines)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    gx, gy = 610, 330
    rr = np.hypot(xx - gx, yy - gy)
    th = np.arctan2(yy - gy, xx - gx)
    g1 = np.abs(np.sin(rr / 7.0 + 3.0 * np.sin(th * 9 + rr / 60.0)))
    g2 = np.abs(np.sin(rr / 9.0 - 2.4 * np.sin(th * 7 - rr / 45.0)))
    guil = (smooth(0.86, 0.97, g1) + smooth(0.88, 0.98, g2)) * (1 - smooth(260, 420, rr))
    rgb = paint(rgb, np.clip(guil, 0, 1), "#9FB8A4", 0.55)
    # top band
    band = Pen(W, H, 4)
    band.rect(0, 0, W, 112)
    bm = band.arr()
    rgb = paint(rgb, bm, "#23443A")
    stripe = Pen(W, H, 4)
    stripe.rect(0, 112, W, 120)
    rgb = paint(rgb, stripe.arr(), "#B08D57")
    hdr = Pen(W, H, 4)
    draw_mark(hdr, 70, 56, 92, ticks=True, ring_w=0.05, line_w=0.05)
    hdr.text(128, 50, "MERIDIAN  INSTITUTE", F_SERIF_B, 50, anchor="lm", spacing=2.5)
    hdr.text(130, 92, "STAFF PASS  ·  SECTION B", F_SANS_B, 21, anchor="lm", spacing=3)
    rgb = paint(rgb, hdr.arr(), "#EDE3C8")
    # photo
    px0, py0, pw, ph = 40, 146, 230, 292
    por = portrait(pw, ph, 41)
    sep = np.stack([por * 1.0, por * 0.96, por * 0.86], -1) * 255 * 0.98 + 6
    rgb[py0:py0 + ph, px0:px0 + pw] = sep
    pf = Pen(W, H, 4)
    pf.rect(px0 - 1, py0 - 1, px0 + pw + 1, py0 + ph + 1, outline=2)
    rgb = paint(rgb, pf.arr(), "#3A3328", 0.8)
    # text block
    t = Pen(W, H, 4)
    t.text(304, 178, "RAHIMOVA  L.", F_SANS_B, 52, anchor="ls")
    t.text(306, 220, "Dept. of Light Physics", F_SANS, 31, anchor="ls")
    t.text(306, 256, "Researcher  ·  Laboratory 7", F_SANS, 24, anchor="ls")
    rgb = paint(rgb, ink(t.arr(), 702, 0.12), "#1C1E22")
    lab = Pen(W, H, 4)
    lab.text(306, 302, "STAFF  No.", F_SANS_B, 20, anchor="ls", spacing=2)
    lab.text(306, 452, "ISSUED", F_SANS_B, 18, anchor="ls", spacing=2)
    lab.text(560, 452, "SIGNATURE", F_SANS_B, 18, anchor="ls", spacing=2)
    lab.rect(560, 470, 820, 472)
    rgb = paint(rgb, lab.arr(), "#4A5A50")
    num = Pen(W, H, 4)
    num.text(300, 410, "№", F_TYPE_B, 70, anchor="ls")
    num.text(372, 416, BADGE_NO, F_TYPE_B, 128, anchor="ls", spacing=2)
    rgb = paint(rgb, ink(num.arr(), 703, 0.10), "#14161A")
    yr = Pen(W, H, 4)
    yr.text(306, 492, "1976", F_TYPE_B, 34, anchor="ls")
    rgb = paint(rgb, yr.arr(), "#1C1E22")
    sig = Pen(W, H, 4)
    rot_text(sig, 690, 448, "L. Rahimova", F_HAND, 46, angle=4, weight=520)
    rgb = paint(rgb, ink(sig.arr(), 704, 0.25), "#22306A", 0.9)
    # access-level diagonal stripe (red) in the lower right corner
    ds = Pen(W, H, 4)
    ds.poly([(W - 120, H), (W, H - 120), (W, H - 86), (W - 86, H)])
    rgb = paint(rgb, ds.arr(), "#A8322A", 0.9)
    # round violet stamp over the photo corner
    st = Pen(W, H, 4)
    sx, sy, sr = 248, 404, 62
    st.ring(sx, sy, sr, 4)
    st.ring(sx, sy, sr - 18, 2.5)
    arc_text(st, sx, sy, sr - 15, "MERIDIAN · INSTITUTE ·", F_SANS_B, 13, a_mid=-90, spacing=1.05)
    arc_text(st, sx, sy, sr - 15, "· PERSONNEL ·", F_SANS_B, 13, a_mid=90, spacing=1.05, inward=True)
    draw_mark(st, sx, sy, 58, ticks=False, ring_w=0.06, line_w=0.06)
    sm = st.arr() * stamp_mask(W, H, 705, 0.5)
    rgb = paint(rgb, sm, "#4B3C8C", 0.7)
    # lamination: gloss streak + slight edge yellowing
    gl = np.clip(1 - np.abs((xx * 0.55 - yy + 120) / 90.0), 0, 1) ** 2
    rgb = rgb + (gl * 18)[..., None]
    rgb = multiply(rgb, edge_wear(W, H, 706, 18, 0.12), "#8A7A50")
    cm = Pen(W, H, 4)
    cm.rect(0, 0, W - 0.5, H - 0.5, radius=32)
    save(to_img(rgb, cm.arr()), "badge.png")


# =================================================================================================
# Index card / request card (1250 x 750)
# =================================================================================================
def card_outline_alpha(notched=(), clip_tl: float = 0.0) -> np.ndarray:
    """Card alpha: rounded corners, V-notches at the given positions (1..8), optional clipped corner."""
    pen = Pen(CARD_W, CARD_H, 4)
    pen.rect(0, 0, CARD_W, CARD_H, radius=CARD_CORNER_PX)
    for k in notched:
        x = card_pos_x(k)
        pen.poly([(x - NOTCH_W_PX / 2, -1), (x + NOTCH_W_PX / 2, -1), (x + NOTCH_FLAT_PX / 2, NOTCH_D_PX),
                  (x - NOTCH_FLAT_PX / 2, NOTCH_D_PX)], 0)
    if clip_tl:
        pen.poly([(-1, -1), (clip_tl + 1, -1), (-1, clip_tl + 1)], 0)
    return pen.arr()


def punch_positions(pen: Pen, numbers: bool = True, ring_w: float = 3.0):
    for k in range(1, 9):
        x = card_pos_x(k)
        pen.ring(x, HOLE_V_PX, HOLE_R_PX, ring_w)
        if numbers:
            pen.text(x, HOLE_V_PX + HOLE_R_PX + 26, str(k), F_SANS_B, 30)


def index_card():
    W, H = CARD_W, CARD_H
    rng = np.random.default_rng(800)
    rgb = paper(W, H, base=(236, 228, 206), seed=801, stains=2, vignette=0.14, fibres=0.8)
    # printed form: red header rule, blue ruling
    pr = Pen(W, H, 4)
    for y in range(318, H - 60, 62):
        pr.rect(36, y, W - 36, y + 1.6)
    rgb = paint(rgb, pr.arr(), "#7C9BC0", 0.75)
    red = Pen(W, H, 4)
    red.rect(36, 196, W - 36, 199.5)
    red.rect(36, 204, W - 36, 205.5)
    red.rect(250, 210, 252, H - 40)
    rgb = paint(rgb, red.arr(), "#C0574B", 0.8)
    # edge positions 1..8 (printed circles + numbers)
    pp = Pen(W, H, 4)
    punch_positions(pp)
    rgb = paint(rgb, ink(pp.arr(), 802, 0.15), "#3A3F4A", 0.9)
    hd = Pen(W, H, 4)
    hd.text(40, 244, "MERIDIAN INSTITUTE · ARCHIVE B · PERSONNEL INDEX", F_SANS_B, 22, anchor="ls", spacing=1.5)
    rgb = paint(rgb, hd.arr(), "#8A3A30", 0.85)
    # typed entries
    tp = Pen(W, H, 4)
    typed(tp, 860, 300, "№ " + BADGE_NO, 56, rng, path=F_TYPE_B)
    typed(tp, 40, 312, "0417", 34, rng)
    typed(tp, 272, 372, "RAHIMOVA, Leyla", 50, rng, path=F_TYPE_B)
    typed(tp, 272, 434, "researcher, Dept. of Light Physics", 38, rng)
    typed(tp, 272, 496, "Laboratory 7 · since 1974", 38, rng)
    typed(tp, 272, 558, "personnel file: Stacks B-3", 38, rng)
    typed(tp, 40, 434, "R-12", 34, rng)
    rgb = paint(rgb, ink(tp.arr(), 803, 0.3, 1.6), "#1E1F26", 0.92)
    # pencil note
    pc = Pen(W, H, 4)
    rot_text(pc, 980, 640, "req. via tube", F_HAND, 58, angle=6, weight=560)
    pc.line([(800, 650), (842, 642), (870, 650)], 3.0)
    pc.line([(842, 662), (870, 650), (848, 632)], 3.0)
    rgb = paint(rgb, ink(pc.arr(), 804, 0.5, 1.4), "#5A5A60", 0.85)
    # catalogue rod hole (bottom centre) -- dark so it reads as a hole even without alpha
    hole = Pen(W, H, 4)
    hole.circle(W / 2, H - 52, 30)
    hm = hole.arr()
    rgb = paint(rgb, np.clip(blur(hm, 3) - hm, 0, 1), "#8A7A5A", 0.6)
    # handling: thumb grime on the top edge, soft fold, foxing
    rgb = multiply(rgb, edge_wear(W, H, 805, 26, 0.16), "#8C7650")
    alpha = card_outline_alpha([k + 1 for k, b in enumerate(PUNCH_CODE) if b])
    cut = 1 - alpha
    rgb = paint(rgb, np.clip(blur(cut, 2.0) - cut, 0, 1), "#7A6848", 0.55)   # cut edges darken slightly
    alpha = np.clip(alpha - hm, 0, 1)
    rgb = paint(rgb, 1 - alpha, "#2A2620")
    save(to_img(rgb, alpha), "index_card.png")


def request_card():
    W, H = CARD_W, CARD_H
    rgb = paper(W, H, base=(220, 200, 156), seed=820, stains=1, vignette=0.12, fibres=0.9)
    pp = Pen(W, H, 4)
    punch_positions(pp, ring_w=3.5)
    rgb = paint(rgb, ink(pp.arr(), 821, 0.15), "#4A3A28", 0.9)
    hd = Pen(W, H, 4)
    hd.rect(36, 192, W - 36, 262, radius=4)
    hm = hd.arr()
    rgb = paint(rgb, hm, "#9A3B2E", 0.92)
    ht = Pen(W, H, 4)
    ht.text(W / 2, 228, "REQUEST  —  ARCHIVE  B", F_GOTHIC, 46, spacing=4)
    rgb = paint(rgb, ht.arr(), "#E9DAB8")
    f = Pen(W, H, 4)
    fields = [("STAFF  No.", 344), ("SURNAME", 418), ("ITEM / FILE", 492), ("DATE", 566)]
    for label, y in fields:
        f.text(52, y, label, F_SANS_B, 26, anchor="ls", spacing=1.5)
        for x in range(290, W - 300 if label == "DATE" else W - 50, 14):
            f.rect(x, y + 2, x + 7, y + 4)
    f.text(W - 280, 566, "SIGN.", F_SANS_B, 26, anchor="ls", spacing=1.5)
    for x in range(W - 190, W - 50, 14):
        f.rect(x, 568, x + 7, 570)
    f.text(52, 660, "Punch the code positions. Send by pneumatic post.", F_SANS, 22, anchor="ls")
    f.text(W - 52, 700, "Form A-12", F_SANS, 20, anchor="rs")
    rgb = paint(rgb, ink(f.arr(), 822, 0.15), "#4A3424", 0.85)
    # small canister pictogram in the corner
    cp = Pen(W, H, 4)
    cx, cy = W - 120, 640
    cp.rect(cx - 40, cy - 14, cx + 40, cy + 14, radius=12)
    cp.rect(cx - 30, cy - 17, cx - 24, cy + 17, 0)
    cp.rect(cx + 24, cy - 17, cx + 30, cy + 17, 0)
    rgb = paint(rgb, cp.arr(), "#9A3B2E", 0.8)
    rgb = multiply(rgb, edge_wear(W, H, 823, 22, 0.12), "#8C7650")
    alpha = card_outline_alpha(clip_tl=REQ_CLIP_PX)
    save(to_img(rgb, alpha), "request_card.png")


# =================================================================================================
# File cover (1200 x 1600 manila folder)
# =================================================================================================
def file_cover():
    W, H = 1200, 1600
    rng = np.random.default_rng(900)
    rgb = paper(W, H, base=(206, 176, 118), seed=901, stains=3, vignette=0.28, fibres=1.3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # creases (vertical score lines near the spine edge) and a soft diagonal bend
    for x0 in (36, 58):
        cr = np.exp(-((xx - x0) / 2.0) ** 2)
        rgb = rgb * (1 - 0.10 * cr)[..., None] + (np.exp(-((xx - x0 - 3) / 2.0) ** 2) * 10)[..., None]
    bend = np.exp(-((xx * 0.4 + yy - 1450) / 60.0) ** 2) * 0.05
    rgb = rgb * (1 - bend)[..., None]
    # printed header
    pr = Pen(W, H, 4)
    draw_mark(pr, 170, 170, 150, ticks=True)
    pr.text(270, 150, "MERIDIAN INSTITUTE", F_SERIF_B, 72, anchor="ls", spacing=2)
    pr.text(274, 205, "PERSONNEL RECORDS  ·  ARCHIVE B", F_SANS_B, 30, anchor="ls", spacing=4)
    pr.rect(90, 270, W - 90, 276)
    pr.rect(90, 284, W - 90, 286)
    rgb = paint(rgb, ink(pr.arr(), 902, 0.25), "#3A2E22", 0.88)
    # big title
    tt = Pen(W, H, 4)
    tt.text(W / 2, 400, "PERSONNEL", F_GOTHIC, 118, spacing=12)
    rgb = paint(rgb, ink(tt.arr(), 903, 0.3), "#2E241A", 0.9)
    # pasted label with typed entries
    lb = Pen(W, H, 4)
    lb.rect(150, 480, W - 150, 860, radius=10)
    lm = lb.arr()
    lab_rgb = paper(W, H, base=(238, 230, 210), seed=904, stains=0, vignette=0.0, fibres=0.6)
    rgb = paint(rgb, blur(lm, 6), "#5A4528", 0.25)
    rgb = rgb * (1 - lm[..., None]) + lab_rgb * lm[..., None]
    fr = Pen(W, H, 4)
    fr.rect(172, 502, W - 172, 838, radius=6, outline=3)
    for y in (612, 712):
        fr.rect(190, y, W - 190, y + 1.5)
    fr.text(194, 540, "SURNAME, INITIAL", F_SANS_B, 20, anchor="ls", spacing=2)
    fr.text(194, 642, "DEPARTMENT", F_SANS_B, 20, anchor="ls", spacing=2)
    fr.text(194, 742, "STAFF No.", F_SANS_B, 20, anchor="ls", spacing=2)
    fr.text(700, 742, "FILE", F_SANS_B, 20, anchor="ls", spacing=2)
    rgb = paint(rgb, fr.arr() * lm, "#5A4A3A", 0.8)
    tp = Pen(W, H, 4)
    typed(tp, 200, 600, "RAHIMOVA  L.", 76, rng, path=F_TYPE_B)
    typed(tp, 200, 696, "Light Physics", 56, rng)
    typed(tp, 200, 812, "№ " + BADGE_NO, 76, rng, path=F_TYPE_B)
    typed(tp, 700, 812, "B-3", 64, rng, path=F_TYPE_B)
    rgb = paint(rgb, ink(tp.arr(), 905, 0.3, 1.6), "#1C1C22", 0.92)
    # red stamp, rotated
    st = Pen(W, H, 4)
    sm_img = Image.new("L", (760 * 4, 230 * 4), 0)
    sd = ImageDraw.Draw(sm_img)
    sd.rounded_rectangle([8, 8, 760 * 4 - 8, 230 * 4 - 8], radius=40, outline=255, width=36)
    sd.rounded_rectangle([60, 60, 760 * 4 - 60, 230 * 4 - 60], radius=24, outline=255, width=12)
    sd.text((380 * 4, 92 * 4), "RESTRICTED", font=font(F_GOTHIC, 96 * 4), fill=255, anchor="mm")
    sd.text((380 * 4, 172 * 4), "ARCHIVE B · 1979", font=font(F_SANS_B, 46 * 4), fill=255, anchor="mm")
    st.paste_rotated(sm_img, 640, 1080, 9)
    sm = st.arr() * stamp_mask(W, H, 906, 0.55)
    rgb = paint(rgb, sm, "#B0302A", 0.78)
    # handwritten pencil note + filing number
    hw = Pen(W, H, 4)
    rot_text(hw, 300, 1290, "to vault? — E.S.", F_HAND, 64, angle=-3, weight=560)
    rot_text(hw, W - 200, 1520, "B-3 / 0417", F_HAND, 52, angle=2, weight=520)
    rgb = paint(rgb, ink(hw.arr(), 907, 0.45, 1.4), "#4A4A50", 0.8)
    # coffee ring
    cx, cy, cr = 880, 1340, 128
    d = np.hypot(xx - cx, (yy - cy) * 1.04)
    ringm = np.exp(-((d - cr) / 7.0) ** 2) * (0.5 + 0.5 * noise(H, W, 25, 2, 908))
    inside = (d < cr) * 0.10 * noise(H, W, 40, 2, 909)
    drip = np.exp(-(((xx - cx - 70) / 22.0) ** 2 + ((yy - cy - 150) / 16.0) ** 2))
    rgb = multiply(rgb, np.clip(ringm * 0.55 + inside + drip * 0.4, 0, 1), "#6A3E1A")
    # wear: edge darkening, corner rub
    rgb = multiply(rgb, edge_wear(W, H, 910, 70, 0.30), "#7A5A30")
    save(to_img(rgb), "file_cover.png")


# =================================================================================================
# Tape hub labels (512 x 512, RGBA: round label with spindle hole)
# =================================================================================================
TAPE_INK = {1996: "#24357A", 1997: "#1E1E24", 1998: "#3A2E7A"}


def tape_label(year: int):
    S = 512
    c = S / 2
    rng = np.random.default_rng(year)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - c + 0.5, yy - c + 0.5)
    rgb = paper(S, S, base=(234, 226, 204), seed=year + 7, stains=1 if year != 1996 else 2, vignette=0.0,
                fibres=0.8)
    # printed band (manufacturer's orange ring) with arc text
    band = smooth(206, 208, rr) * (1 - smooth(246, 248, rr))
    rgb = paint(rgb, band, "#C2562E", 0.92)
    bt = Pen(S, S, 4)
    arc_text(bt, c, c, 219, "MAGNETIC  TAPE", F_SANS_B, 22, a_mid=-90, spacing=1.15)
    arc_text(bt, c, c, 235, "ARCHIVE  B", F_SANS_B, 22, a_mid=90, spacing=1.2, inward=True)
    for a in (-160, -20, 20, 160):
        ra = math.radians(a)
        bt.circle(c + 227 * math.cos(ra), c + 227 * math.sin(ra), 4)
    rgb = paint(rgb, bt.arr() * band, "#F3E6CF", 0.95)
    # printed fields
    pf = Pen(S, S, 4)
    pf.ring(c, c, 62, 2.5)
    pf.rect(120, 156, 392, 158)
    pf.text(120, 106, "DATE / NAME", F_SANS_B, 15, anchor="ls", spacing=1.5)
    pf.rect(112, 410, 330, 412)
    pf.text(112, 330, "SPEED", F_SANS_B, 15, anchor="ls", spacing=1.5)
    pf.text(338, 408, "cm/s", F_SANS_B, 34, anchor="ls")
    rgb = paint(rgb, ink(pf.arr(), year + 1, 0.15), "#8A3A24", 0.85)
    # Leyla's handwriting
    hw = Pen(S, S, 4)
    tilt = {1996: -4, 1997: -2, 1998: -6}[year]
    rot_text(hw, 256, 132, f"L.R. {year}", F_HAND, 66, angle=tilt * 0.5, weight=640)
    rot_text(hw, 220, 372, TAPE_SPEED, F_HAND, 150, angle=tilt, weight=700)
    hw.line([(124, 426), (318, 418)], 4.0)   # underline the speed
    rgb = paint(rgb, ink(hw.arr(), year + 2, 0.25, 1.4), TAPE_INK[year], 0.95)
    # handling: grime, a little tape-oxide smudge
    smudge = smooth(0.70, 0.95, noise(S, S, 40, 3, year + 3)) * 0.25
    rgb = multiply(rgb, smudge, "#6A4A30")
    rgb = multiply(rgb, smooth(200, 256, rr) * 0.18, "#7A6040")
    # alpha: disc with spindle hole + 3 drive keyways
    al = Pen(S, S, 4)
    al.circle(c, c, 252)
    al.circle(c, c, 44, 0)
    for k in range(3):
        a = math.radians(-90 + 120 * k)
        kx, ky = c + 44 * math.cos(a), c + 44 * math.sin(a)
        al.circle(kx, ky, 11, 0)
    alpha = al.arr()
    edge = np.clip(blur(1 - alpha, 1.5) - (1 - alpha), 0, 1)
    rgb = paint(rgb, edge, "#7A6448", 0.6)
    save(to_img(rgb, alpha), f"tape_label_{year}.png")


# =================================================================================================
# Lantern slide (512 x 512, RGBA: clear glass)
# =================================================================================================
def slide_mark():
    S = 512
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # clear glass with faint green edge tint and specks
    rgb = solid(S, S, "#DDE6E2")
    alpha = np.full((S, S), 0.10, np.float32)
    # black paper mask with a round opening, under the tape
    mk = Pen(S, S, 4)
    mk.rect(0, 0, S, S)
    mk.circle(c, c, 212, 0)
    mm = mk.arr()
    rgb = paint(rgb, mm, "#17191A")
    alpha = np.maximum(alpha, mm * 0.97)
    # the mark: black emulsion, slightly soft, with tiny emulsion pinholes
    m = mark_mask(400)
    mark = np.zeros((S, S), np.float32)
    mark[56:456, 56:456] = m
    pin = (noise(S, S, 1.2, 1, 951) > 0.86).astype(np.float32) * 0.5
    mark = mark * (1 - pin * mark)
    rgb = paint(rgb, mark, "#0E0F10")
    alpha = np.maximum(alpha, mark * 0.94)
    # tape binding border (black gummed paper), slightly ragged inner edge
    d = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy))
    rag = 30 + 3 * noise(S, S, 10, 2, 952)
    tape = smooth(rag + 1.2, rag - 1.2, d)
    tape_rgb = solid(S, S, "#1E1C1A") * (0.9 + 0.25 * noise(S, S, 3, 2, 953))[..., None]
    scuff = smooth(0.72, 0.9, noise(S, S, 12, 3, 954)) * tape
    tape_rgb = paint(tape_rgb, scuff, "#6A645A", 0.6)
    rgb = rgb * (1 - tape[..., None]) + tape_rgb * tape[..., None]
    alpha = np.maximum(alpha, tape)
    # thumb-spot label (white paper dot) at the bottom-left, with Strand's star
    tl = Pen(S, S, 4)
    tl.circle(44, S - 44, 20)
    tm = tl.arr()
    rgb = paint(rgb, tm, "#ECE4D0")
    st = Pen(S, S, 4)
    picto(st, "star", 44, S - 44, 26)
    rgb = paint(rgb, st.arr(), "#8A2A22")
    alpha = np.maximum(alpha, tm)
    # glass sheen
    sh = np.clip(1 - np.abs((xx - yy * 0.6 - 120) / 60.0), 0, 1) * (1 - mm) * (1 - mark)
    rgb = paint(rgb, sh, "#FFFFFF", 0.4)
    alpha = np.maximum(alpha, sh * 0.25)
    save(to_img(rgb, alpha), "slide_mark.png")


# =================================================================================================
# Film look helpers
# =================================================================================================
def tone_curve(x: np.ndarray, contrast: float = 1.15, toe: float = 0.03) -> np.ndarray:
    """Filmic S-curve on 0..1 values."""
    x = np.clip(x, 0, None)
    y = 1.0 - np.exp(-x * 2.2)                                         # soft shoulder
    y = y / (1.0 - math.exp(-2.2 * 1.2))
    y = np.clip(y, 0, 1)
    y = 0.5 + (y - 0.5) * contrast
    return np.clip(y * (1 - toe) + toe, 0, 1)


def film_finish(lum: np.ndarray, seed: int, grain_amt=0.055, scratches=6, dust=60, vignette=0.55,
                weave=(2, 1), gate=True, tint=(1.0, 0.985, 0.95), hair=True, halation=0.0,
                contrast=1.15, flicker=0.0) -> np.ndarray:
    """Turn a linear luminance scene (0..~2) into a 1979 black-and-white projected print (sRGB 0..255)."""
    h, w = lum.shape
    r = np.random.default_rng(seed)
    x = lum.astype(np.float32)
    if halation:
        x = x + halation * blur(np.clip(x - 0.8, 0, None), 0.008 * w) + halation * 0.5 * blur(np.clip(x - 0.6, 0, None), 0.035 * w)
    yy, xx = np.mgrid[0:h, 0:w]
    dn = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    x = x * (1.0 - vignette * smooth(0.35, 1.45, dn))                    # projector hotspot / lens falloff
    if flicker:
        x = x * (1 + flicker * (noise(h, w, w * 0.6, 2, seed + 9) - 0.5))
    y = tone_curve(x, contrast)
    g = grain(h, w, seed + 1, 0.6) * 0.7 + grain(h, w, seed + 2, 1.6) * 0.5
    mid = 0.35 + 0.65 * (1 - np.abs(y - 0.5) * 2) ** 0.6
    y = y + grain_amt * g * mid
    for _ in range(scratches):
        sx = r.uniform(0.04, 0.96) * w
        y0, y1 = sorted(r.uniform(0, h, 2))
        if r.random() < 0.5:
            y0, y1 = 0, h
        col = (np.arange(h) >= y0) & (np.arange(h) <= y1)
        wob = sx + 1.5 * np.sin(np.arange(h) / r.uniform(40, 120) + r.uniform(0, 6))
        width = r.uniform(0.5, 1.4)
        strength = r.uniform(0.06, 0.22) * (1 if r.random() < 0.6 else -1)
        brk = noise(h, 1, r.uniform(8, 30), 1, int(r.integers(1e6)))[:, 0] > 0.35
        for yi in np.nonzero(col & brk)[0]:
            xc = wob[yi]
            x0i = int(max(0, xc - 2))
            for xi in range(x0i, min(w, x0i + 5)):
                f = max(0.0, 1 - abs(xi - xc) / width)
                y[yi, xi] += strength * f
    dl = np.zeros((h, w), np.float32)
    dd = np.zeros((h, w), np.float32)
    for _ in range(dust):
        cx, cy = r.uniform(0, w), r.uniform(0, h)
        rad = r.uniform(0.6, 2.6) if r.random() < 0.9 else r.uniform(3, 6)
        tgt = dd if r.random() < 0.7 else dl
        x0, x1 = int(max(0, cx - rad - 2)), int(min(w, cx + rad + 3))
        y0, y1 = int(max(0, cy - rad - 2)), int(min(h, cy + rad + 3))
        sub = np.sqrt((xx[y0:y1, x0:x1] - cx) ** 2 + ((yy[y0:y1, x0:x1] - cy) * r.uniform(0.6, 1.4)) ** 2)
        tgt[y0:y1, x0:x1] = np.maximum(tgt[y0:y1, x0:x1], np.clip(rad - sub + 0.5, 0, 1))
    if hair:
        hp = Pen(w, h, 2)
        hx, hy = r.uniform(0.05, 0.25) * w, r.uniform(0.6, 0.95) * h
        pts = []
        ang = r.uniform(0, 6.28)
        for _ in range(60):
            ang += r.normal(0, 0.12)
            hx += 2.2 * math.cos(ang)
            hy += 2.2 * math.sin(ang)
            pts.append((hx, hy))
        hp.line(pts, 1.2, caps=False)
        dd = np.maximum(dd, hp.arr() * 0.8)
    y = y - 0.55 * dd + 0.45 * dl
    if gate:
        ox, oy = weave
        y = np.roll(np.roll(y, oy, 0), ox, 1)
        gp = Pen(w, h, 2)
        m = 10
        gp.rect(m + ox, m + oy, w - m + ox, h - m + oy, radius=26)
        gm = blur(gp.arr(), 3.0)
        y = y * gm + 0.02 * (1 - gm)
    y = np.clip(y, 0, 1)
    rgb = np.stack([y * tint[0], y * tint[1], y * tint[2]], -1) * 255.0
    return rgb


# =================================================================================================
# Film strips (900 x 300, RGBA: sprocket holes are transparent)
# =================================================================================================
STRIP_W, STRIP_H = 900, 300
STRIP_MARGIN = 54          # sprocket band height (top and bottom)
STRIP_FRAME_W = 270
STRIP_PITCH = 292          # frame pitch; frames centred at 450 - 292, 450, 450 + 292
SUN_H_UNITS = 2.2          # obelisk height in shadow units: tan(elevation) = 2.2 / L


def obelisk_scene(fw: int, fh: int, L: int, seed: int, unit_frac: float = 0.12) -> np.ndarray:
    """Sundial obelisk film frame (linear luminance 0..~1.6). Shadow length L units, 1 unit = unit_frac * fw.
    The sun is on the left; its elevation follows tan(e) = H / L for an obelisk H = 2.2 units tall.
    Unit stones on the ground at 1..5 units from the obelisk make the length easy to read."""
    u = unit_frac * fw
    H = SUN_H_UNITS
    elev = math.degrees(math.atan2(H, L))
    k = float(np.clip((elev - 28.8) / (65.6 - 28.8), 0, 1))     # 0 = dawn (L = 4) .. 1 = high sun (L = 1)
    hor = 0.60 * fh
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    # sky: dawn darker and graded toward the sun, high sun bright and even
    top = 0.30 + 0.45 * k
    sky = top + (0.92 - top) * (yy / hor) ** 1.3
    sx = (0.11 + 0.03 * k) * fw
    sy = hor - (elev / 90.0) * hor * 1.05
    sy = max(sy, 0.10 * fh)
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    sky = sky + (0.85 - 0.25 * k) * np.exp(-d / (0.12 * fw)) + 0.5 * np.exp(-(d / (0.04 * fw)) ** 2)
    sky = np.where(d < 0.032 * fw, 1.7, sky)
    img = sky.copy()
    # far hills
    ridge = hor - (4 + 8 * noise(1, fw, 40, 3, seed)[0]) * fh / 180
    img = np.where(yy > ridge[None, :], 0.40 + 0.12 * k, img)
    # ground: light paving, brighter toward the camera
    g = 0.70 + 0.16 * ((yy - hor) / (fh - hor))
    img = np.where(yy >= hor, g, img)
    bx = 0.22 * fw
    by = hor + 0.20 * fh          # obelisk base line on the ground
    # unit stones at 1..5 units (dark studs on the ground line)
    marks = Pen(fw, fh, 4)
    for i in range(1, 6):
        mx = bx + i * u
        marks.rect(mx - 0.010 * fw, by - 0.020 * fh, mx + 0.010 * fw, by + 0.030 * fh, radius=1)
    mm = marks.arr()
    # shadow on the ground: from the base to L units, tapering to the tip
    ow = 0.085 * fw
    shp = Pen(fw, fh, 4)
    tip = bx + L * u
    shp.poly([(bx, by - 0.030 * fh), (tip, by - 0.008 * fh), (tip + 0.004 * fw, by), (tip, by + 0.010 * fh),
              (bx, by + 0.040 * fh)])
    sm = blur(shp.arr(), 0.4 + 0.5 * (1 - k))
    img = img * (1 - (0.88 - 0.1 * (1 - k)) * sm)
    img = img * (1 - mm) + mm * 0.22
    # obelisk: tapered shaft + pyramidion, lit face toward the sun (left), dark face right
    top_y = by - H * u
    w0, w1 = ow / 2, ow * 0.28
    cap = top_y + 0.30 * u
    lit = Pen(fw, fh, 4)
    lit.poly([(bx - w0, by), (bx - w1, cap), (bx, cap), (bx, by)])
    lit.poly([(bx - w1, cap), (bx, top_y - 0.05 * u), (bx, cap)])
    dark = Pen(fw, fh, 4)
    dark.poly([(bx, by), (bx, cap), (bx + w1, cap), (bx + w0, by)])
    dark.poly([(bx, cap), (bx, top_y - 0.05 * u), (bx + w1, cap)])
    base = Pen(fw, fh, 4)
    base.rect(bx - w0 * 1.5, by - 0.045 * fh, bx + w0 * 1.5, by + 0.015 * fh)
    lm, dm, bm = lit.arr(), dark.arr(), base.arr()
    img = img * (1 - lm) + lm * (0.62 + 0.25 * k)
    img = img * (1 - dm) + dm * 0.10
    img = img * (1 - bm) + bm * (0.30 + 0.1 * k)
    return img


def film_strip(k: int):
    L = SPLICE_SHADOWS[k]
    w, h = STRIP_W, STRIP_H
    r = np.random.default_rng(300 + k)
    fh = h - 2 * STRIP_MARGIN - 12
    y0 = STRIP_MARGIN + 6
    lum = np.zeros((h, w), np.float32) + 0.06
    for j, cx in enumerate((w / 2 - STRIP_PITCH, w / 2, w / 2 + STRIP_PITCH)):
        x0 = int(round(cx - STRIP_FRAME_W / 2))
        sc = obelisk_scene(STRIP_FRAME_W, fh, L, 310 + 10 * k + j)
        sc = sc * (0.97 + 0.06 * r.random())          # exposure flicker per frame
        fr = Pen(STRIP_FRAME_W, fh, 4)
        fr.rect(0, 0, STRIP_FRAME_W, fh, radius=6)
        fm = fr.arr()
        lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] = lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] * (1 - fm) + sc * fm
    holes = Pen(w, h, 4)
    pitch = STRIP_PITCH / 4.0
    hw, hh = 22, 30
    for i in range(-2, 16):
        hx = w / 2 - STRIP_PITCH * 1.5 + pitch * (i + 0.5)
        for hy in (STRIP_MARGIN / 2, h - STRIP_MARGIN / 2):
            if -hw < hx < w + hw:
                holes.rect(hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2, radius=5)
    hm = holes.arr()
    ep = Pen(w, h, 4)
    for ex in (w / 2 - STRIP_PITCH, w / 2 + STRIP_PITCH):
        ep.text(ex, h - 6, "SAFETY  FILM", F_SANS_B, 12, anchor="ms", spacing=1.2)
        ep.poly([(ex + 72, h - 16), (ex + 82, h - 11), (ex + 72, h - 6)])
    lum = lum + ep.arr() * 0.45
    rgb = film_finish(lum, 330 + k, grain_amt=0.04, scratches=3, dust=22, vignette=0.0, gate=False,
                      tint=(1.0, 0.94, 0.82), hair=False, contrast=1.25)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = smooth(0, 50, np.minimum(xx, w - 1 - xx)).astype(np.float32)
    rgb = rgb * (0.80 + 0.20 * edge)[..., None]
    # base colour in the margins (amber safety base)
    margin = ((yy < y0 - 2) | (yy > y0 + fh + 2)).astype(np.float32)
    rgb = paint(rgb, margin * 0.55, "#3A2414")
    rim = np.clip(blur(hm, 1.0) - hm, 0, 1) * 1.6
    rgb = paint(rgb, rim, "#C8B48A", 0.5)
    alpha = np.clip(1 - hm, 0, 1)
    save(to_img(rgb, alpha), f"film_strip_{k}.png")


# =================================================================================================
# Reel can lid (800 x 800, RGBA: transparent outside the disc)
# =================================================================================================
def reel_can_lid():
    S = 800
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    disc = Pen(S, S, 4)
    disc.circle(c, c, c - 2)
    alpha = disc.arr()
    n = noise(S, S, 120, 4, 401)
    fine = noise(S, S, 3, 2, 402)
    base = hexf("#5E6A60")
    rgb = base[None, None, :] * (0.86 + 0.18 * n + 0.06 * (fine - 0.5))[..., None]
    ang = np.arctan2(yy - c, xx - c)
    for r0, r1, s in ((0.965, 1.0, 0.55), (0.90, 0.93, 1.25), (0.86, 0.885, 0.78), (0.30, 0.32, 1.18)):
        m = smooth(r0 - 0.008, r0, rr) * (1 - smooth(r1, r1 + 0.008, rr))
        rgb = rgb * (1 + (s - 1) * m)[..., None]
    shade = 1 + 0.10 * np.cos(ang + 2.4) * smooth(0.84, 0.99, rr)
    rgb = rgb * shade[..., None]
    scuff = smooth(0.70, 0.86, noise(S, S, 25, 3, 404)) * smooth(0.6, 1.0, rr)
    rgb = paint(rgb, scuff, "#A9A9A0", 0.65)
    rust = smooth(0.80, 0.95, noise(S, S, 6, 2, 405)) * (0.4 + 0.6 * smooth(0.85, 1.0, rr))
    rgb = paint(rgb, rust, "#6B3A1E", 0.6)
    # painted pictogram band (cream enamel) across the middle
    bw, bh = 640, 270
    bx0, by0 = c - bw / 2, c - bh / 2 + 30
    band = Pen(S, S, 4)
    band.rect(bx0, by0, bx0 + bw, by0 + bh, radius=20)
    bm = band.arr()
    cream = hexf("#E3D7B8") * (0.92 + 0.1 * noise(S, S, 60, 3, 406))[..., None]
    rgb = rgb * (1 - bm[..., None]) + cream * bm[..., None]
    # three panels: sunrise (long shadow) -> morning -> high sun (short shadow); sun on the left
    ink_p = Pen(S, S, 4)
    sun_p = Pen(S, S, 4)
    pw = bw / 3
    ground = by0 + 172
    U = 30                                   # shadow unit (px)
    for i, (shadow, elev) in enumerate(((5.0, 3.0), (2.6, 40.0), (0.9, 68.0))):
        px0 = bx0 + i * pw
        if i:
            ink_p.rect(px0 - 1.5, by0 + 22, px0 + 1.5, by0 + 200)      # panel divider
        ox = px0 + 44                         # obelisk x
        ink_p.rect(px0 + 14, ground, px0 + pw - 14, ground + 4)        # ground line
        ink_p.poly([(ox - 9, ground), (ox - 5, ground - 76), (ox + 5, ground - 76), (ox + 9, ground)])
        ink_p.poly([(ox - 5, ground - 76), (ox, ground - 88), (ox + 5, ground - 76)])
        ink_p.poly([(ox + 8, ground + 4), (ox + 8 + shadow * U, ground + 6), (ox + 8 + shadow * U, ground + 11),
                    (ox + 8, ground + 15)])
        if elev < 10:          # sunrise: half sun on the horizon, behind (left of) the obelisk
            sx = ox - 26
            if sx - 22 < px0 + 6:
                sx = px0 + 30
            sun_p.circle(sx, ground, 19)
            sun_p.rect(sx - 30, ground, sx + 30, ground + 30, v=0)
            for a in range(195, 346, 30):
                ra = math.radians(a)
                sun_p.line([(sx + 26 * math.cos(ra), ground + 26 * math.sin(ra)),
                            (sx + 37 * math.cos(ra), ground + 37 * math.sin(ra))], 4.5)
        else:                  # sun up and to the left, height by elevation
            dist = 120
            sx = ox - dist * math.cos(math.radians(elev)) * 0.45 - 4
            sy = ground - 14 - dist * math.sin(math.radians(elev)) * 1.05
            sx = max(sx, px0 + 30)
            sun_p.circle(sx, sy, 16)
            for a in range(0, 360, 45):
                ra = math.radians(a)
                sun_p.line([(sx + 22 * math.cos(ra), sy + 22 * math.sin(ra)),
                            (sx + 31 * math.cos(ra), sy + 31 * math.sin(ra))], 4.5)
    ay = by0 + bh - 36
    ink_p.rect(bx0 + 70, ay - 4, bx0 + bw - 100, ay + 4)
    ink_p.poly([(bx0 + bw - 108, ay - 20), (bx0 + bw - 62, ay), (bx0 + bw - 108, ay + 20)])
    im_ink = ink(ink_p.arr(), 407, 0.22) * bm
    im_sun = ink(sun_p.arr(), 408, 0.18) * bm
    rgb = paint(rgb, im_sun, "#C77A22", 0.95)
    rgb = paint(rgb, im_ink, "#24282A", 0.95)
    chips = smooth(0.80, 0.9, noise(S, S, 9, 3, 409)) * (blur(bm, 6) < 0.92) * bm
    rgb = paint(rgb, chips.astype(np.float32), "#545C55", 0.85)
    # masking tape with Strand's initials (dressing, no clue)
    tape = Pen(S, S, 4)
    tape.poly([(268, 158), (532, 140), (536, 206), (272, 224)])
    tm = tape.arr()
    rgb = paint(rgb, tm, "#D9C79A", 0.92)
    rgb = multiply(rgb, np.clip(blur(tm, 2) - tm, 0, 1), "#3A3A30", 0.5)
    hw = Pen(S, S, 4)
    rot_text(hw, 402, 180, "E.S.  1979", F_HAND, 50, angle=4, weight=620)
    rgb = paint(rgb, ink(hw.arr(), 410, 0.2) * tm, "#1E2340", 0.92)
    rgb = rgb * (0.94 + 0.06 * fine)[..., None]
    save(to_img(rgb, alpha), "reel_can_lid.png")


GENERATORS: dict = {}


def register(name, fn):
    GENERATORS[name] = fn


register("glyph_mark", glyph_mark)
register("glyph_sign", glyph_sign)
register("vault_engraving", vault_engraving)
for _k in range(4):
    register(f"film_strip_{_k}", (lambda k: (lambda: film_strip(k)))(_k))
register("reel_can_lid", reel_can_lid)
register("index_card", index_card)
register("request_card", request_card)
register("badge", badge)
register("routing_chart", routing_chart)
register("dest_symbols", dest_symbols)
for _y in TAPE_YEARS:
    register(f"tape_label_{_y}", (lambda y: (lambda: tape_label(y)))(_y))
register("slide_mark", slide_mark)
register("file_cover", file_cover)


# ================================================================================================= main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated generator names")
    args = ap.parse_args()
    names = list(GENERATORS)
    if args.only:
        names = [n for n in args.only.split(",") if n]
        bad = [n for n in names if n not in GENERATORS]
        if bad:
            ap.error(f"unknown: {bad}; known: {list(GENERATORS)}")
    for n in names:
        print(f"[{n}]")
        GENERATORS[n]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
