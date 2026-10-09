#!/usr/bin/env python3
"""Chapter 2 (Records Archive B) decals, glyphs, film frames and the linoleum texture set.

Original procedural artwork (PIL + numpy only). Outputs:
    game/assets/textures/decals/ch2/*.png|jpg     decals, glyphs, film frames (see docs/models/ch2_decals.md)
    game/assets/textures/linoleum/{albedo.jpg, normal.png, orm.jpg}
    game/assets/textures/paint_green/...          eggshell paint over plaster (M_Paint_Green)
    game/assets/textures/concrete/...             cast concrete (M_Concrete)
    qa/decals_ch2_contact_sheet.jpg               labelled QA sheet

Puzzle data MUST match game/src/rooms/archive/archive_logic.gd and docs/CHAPTER2_DESIGN.md.

    python3 tools/textures/make_decals_ch2.py                 # everything + contact sheet
    python3 tools/textures/make_decals_ch2.py --only badge,index_card
    python3 tools/textures/make_decals_ch2.py --sheet-only
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# make_decals only creates its (existing) output folders and seeds its own RNGs at import time.
import make_decals as MD  # noqa: E402
from make_decals import aged_paper, noise  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
TEX = os.path.join(ROOT, "game", "assets", "textures")
QA = os.path.join(ROOT, "qa")

# ---- puzzle data (mirrors archive_logic.gd) -------------------------------------------------
BADGE_NO = "0417"
PUNCH_CODE = [1, 0, 1, 1, 0, 0, 1, 0]          # notched / punched positions 1..8
SPLICE_SHADOWS = [3, 1, 4, 2]                  # film strip k -> shadow length (units)
TAPE_SPEED = "4.75"
TAPE_YEARS = (1996, 1997, 1998)
DEST_SYMBOLS = ["star", "book", "flask", "film", "envelope", "padlock"]  # dial d = 0..5 at 12,2,4,6,8,10 o'clock
SIGN_IN_VAULT_SCALE = 0.55                     # vault engraving: sign rotated 90 deg clockwise, scaled 0.55

# card geometry shared by index_card / request_card (1250 x 750 px = 0.125 x 0.075 m, 10 px per mm)
CARD_W, CARD_H = 1250, 750
HOLE_V_PX = 92            # punch-circle centre, px from the top edge (9.2 mm)  -> v = 1 - 92/750
HOLE_R_PX = 27            # printed punch circle radius (Ø 5.4 mm); hole discs should be Ø 5.0 mm
NOTCH_W_PX = 84           # V-notch width at the top edge (8.4 mm)
NOTCH_D_PX = 100          # V-notch depth (10 mm): the tip passes through the printed circle centre

# ---- fonts ------------------------------------------------------------------------------------
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
SYS = "/usr/share/fonts"


def _first(*paths: str) -> str:
    for p in paths:
        if os.path.exists(p):
            return p
    return os.path.join(SYS, "truetype", "dejavu", "DejaVuSans.ttf")


F_TYPE = _first(f"{SYS}/opentype/urw-base35/NimbusMonoPS-Regular.otf", f"{SYS}/truetype/freefont/FreeMono.ttf",
                f"{SYS}/truetype/liberation/LiberationMono-Regular.ttf", f"{SYS}/truetype/dejavu/DejaVuSansMono.ttf")
F_TYPE_B = _first(f"{SYS}/opentype/urw-base35/NimbusMonoPS-Bold.otf", f"{SYS}/truetype/freefont/FreeMonoBold.ttf",
                  f"{SYS}/truetype/liberation/LiberationMono-Bold.ttf", f"{SYS}/truetype/dejavu/DejaVuSansMono-Bold.ttf")
F_HAND = _first(os.path.join(FONTS, "Caveat-Variable.ttf"))
F_SERIF_B = _first(os.path.join(FONTS, "CormorantGaramond-Bold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif-Bold.ttf")
F_SERIF = _first(os.path.join(FONTS, "CormorantGaramond-SemiBold.ttf"), f"{SYS}/truetype/dejavu/DejaVuSerif.ttf")
F_SANS_B = _first(f"{SYS}/opentype/urw-base35/NimbusSansNarrow-Bold.otf", f"{SYS}/truetype/liberation/LiberationSans-Bold.ttf",
                  f"{SYS}/truetype/dejavu/DejaVuSans-Bold.ttf")
F_SANS = _first(f"{SYS}/opentype/urw-base35/NimbusSans-Regular.otf", f"{SYS}/truetype/liberation/LiberationSans-Regular.ttf",
                f"{SYS}/truetype/dejavu/DejaVuSans.ttf")
F_SANS_W = _first(f"{SYS}/opentype/urw-base35/NimbusSans-Bold.otf", f"{SYS}/truetype/liberation/LiberationSans-Bold.ttf",
                  f"{SYS}/truetype/dejavu/DejaVuSans-Bold.ttf")
F_DEJAVU = f"{SYS}/truetype/dejavu/DejaVuSans.ttf"

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
def blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur (FFT, reflect padding) for 2-D or HxWxC float arrays."""
    if sigma <= 0.05:
        return a.astype(np.float32)
    pad = int(3 * sigma) + 2
    widths = ((pad, pad), (pad, pad)) + ((0, 0),) * (a.ndim - 2)
    p = np.pad(a.astype(np.float32), widths, mode="reflect")
    hh, ww = p.shape[:2]
    fy = np.fft.fftfreq(hh)[:, None]
    fx = np.fft.rfftfreq(ww)[None, :]
    g = np.exp(-2.0 * np.pi ** 2 * sigma ** 2 * (fx ** 2 + fy ** 2))
    if a.ndim == 3:
        g = g[..., None]
    out = np.fft.irfft2(np.fft.rfft2(p, axes=(0, 1)) * g, s=(hh, ww), axes=(0, 1))
    return out[pad:pad + a.shape[0], pad:pad + a.shape[1]].astype(np.float32)


def smooth(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hexf(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def paint(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    """Lerp `color` (hex or rgb) onto float sRGB image through mask (0..1)."""
    c = hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m) + c * m


def multiply(rgb: np.ndarray, mask: np.ndarray, color, opacity: float = 1.0) -> np.ndarray:
    c = (hexf(color) if isinstance(color, str) else np.asarray(color, np.float32)) / 255.0
    m = np.clip(mask * opacity, 0, 1)[..., None]
    return rgb * (1 - m + m * c)


def to_img(rgb: np.ndarray, alpha: np.ndarray | None = None) -> Image.Image:
    rgb8 = np.clip(rgb, 0, 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(rgb8, "RGB")
    a8 = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb8, a8]), "RGBA")


def from_img(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("RGB"), np.float32)


def grain(h: int, w: int, seed: int, sigma: float = 0.7) -> np.ndarray:
    r = np.random.default_rng(seed)
    g = blur(r.standard_normal((h, w)).astype(np.float32), sigma)
    return g / (g.std() + 1e-6)


def save(im: Image.Image, name: str) -> str:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    if name.endswith(".jpg"):
        im.convert("RGB").save(path, quality=92, subsampling=0, optimize=True)
    else:
        im.save(path, optimize=True)
    print("  wrote", os.path.relpath(path, ROOT), im.size)
    return path


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
        ro, ri = r + width / 2, r - width / 2
        self.d.ellipse([(cx - ro) * s, (cy - ro) * s, (cx + ro) * s, (cy + ro) * s], outline=v,
                       width=max(1, int(round(width * s))))
        del ri

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
        # letter-spaced text (anchor applies to the whole run horizontally)
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
        from PIL import ImageChops
        self.im.paste(ImageChops.lighter(base, r), (x0, y0))

    def arr(self) -> np.ndarray:
        im = self.im.resize((self.w, self.h), Image.BOX) if self.ss > 1 else self.im
        return np.asarray(im, np.float32) / 255.0


def text_mask(txt, path, size, ss=4, weight=None, pad=8) -> Image.Image:
    """Tight 'L' image of a text run at ss scale (for rotated / jittered placement)."""
    f = font(path, size * ss, weight)
    l, t, r, b = f.getbbox(txt)
    im = Image.new("L", (int(r - l) + 2 * pad * ss, int(b - t) + 2 * pad * ss), 0)
    ImageDraw.Draw(im).text((pad * ss - l, pad * ss - t), txt, font=f, fill=255)
    return im


def rot_text(pen: Pen, x, y, txt, path, size, angle=0.0, weight=None):
    pen.paste_rotated(text_mask(txt, path, size, pen.ss, weight), x, y, angle)


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
        # stroke starts at the top horn (-50 deg) and sweeps through the back (180) to the lower horn (+50)
        sweep = np.mod(-50.0 - ang, 360.0)           # 0 at top horn, increases going anticlockwise on screen
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


def white_rgba(mask: np.ndarray) -> Image.Image:
    rgb = np.full(mask.shape + (3,), 255.0, np.float32)
    return to_img(rgb, mask)


def glyph_mark():
    save(white_rgba(mark_mask(512)), "glyph_mark.png")


def glyph_sign():
    save(white_rgba(sign_mask(512)), "glyph_sign.png")


def vault_engraving():
    """Built from the two glyph images: mark upright at scale 1 + sign rotated 90 deg clockwise at 0.55."""
    mpath, spath = os.path.join(OUT, "glyph_mark.png"), os.path.join(OUT, "glyph_sign.png")
    if not (os.path.exists(mpath) and os.path.exists(spath)):
        glyph_mark()
        glyph_sign()
    mark = Image.open(mpath).getchannel("A")
    sign = Image.open(spath).getchannel("A")
    n = int(round(512 * SIGN_IN_VAULT_SCALE))
    sign_s = sign.resize((n, n), Image.LANCZOS).rotate(-90, resample=Image.BICUBIC)  # PIL: negative = clockwise
    comb = Image.new("L", (512, 512), 0)
    comb.paste(sign_s, ((512 - n) // 2, (512 - n) // 2))
    m = np.maximum(np.asarray(mark, np.float32), np.asarray(comb, np.float32)) / 255.0
    # etched glass: frosted fill + brighter cut edges + sparkle
    edge = np.clip(m - blur(m, 2.2), 0, 1) * 2.4 + np.clip(blur(m, 2.2) - m, 0, 1) * 1.2
    fill = m * 0.30
    sparkle = (noise(512, 512, 1.5, 1, 77) > 0.62).astype(np.float32) * m * 0.12
    a = np.clip(fill + 0.62 * np.clip(edge, 0, 1) + sparkle, 0, 0.66)
    a = blur(a, 0.5)
    save(white_rgba(a), "vault_engraving.png")


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
                weave=(2, 1), gate=True, tint=(1.0, 0.985, 0.95), hair=True, halation=0.0) -> np.ndarray:
    """Turn a linear luminance scene (0..~2) into a 1979 black-and-white projected print (sRGB 0..255)."""
    h, w = lum.shape
    r = np.random.default_rng(seed)
    x = lum.astype(np.float32)
    if halation:
        x = x + halation * blur(np.clip(x - 0.8, 0, None), 9) + halation * 0.5 * blur(np.clip(x - 0.6, 0, None), 40)
    yy, xx = np.mgrid[0:h, 0:w]
    dn = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    x = x * (1.0 - vignette * smooth(0.35, 1.45, dn))                    # projector hotspot / lens falloff
    y = tone_curve(x)
    # grain: two scales, stronger in the mid-tones
    g = grain(h, w, seed + 1, 0.6) * 0.7 + grain(h, w, seed + 2, 1.6) * 0.5
    mid = 0.35 + 0.65 * (1 - np.abs(y - 0.5) * 2) ** 0.6
    y = y + grain_amt * g * mid
    # vertical scratches (light = emulsion side, dark = base side) with breaks and wobble
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
    # dust: dark specks (dirt on the print) and a few bright (holes in the emulsion)
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
        for i in range(60):
            ang += r.normal(0, 0.12)
            hx += 2.2 * math.cos(ang)
            hy += 2.2 * math.sin(ang)
            pts.append((hx, hy))
        hp.line(pts, 1.2, caps=False)
        dd = np.maximum(dd, hp.arr() * 0.8)
    y = y - 0.55 * dd + 0.45 * dl
    # gate weave: offset the picture and show the soft rounded aperture edge
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


def obelisk_scene(fw: int, fh: int, L: int, seed: int, unit_frac: float = 0.12) -> np.ndarray:
    """Sundial obelisk film frame (linear luminance 0..~1.4). Shadow length L units, 1 unit = unit_frac * fw.
    Sun on the left; its elevation follows tan(e) = H / L for an obelisk H = 2.2 units tall."""
    u = unit_frac * fw
    H = 2.2
    elev = math.degrees(math.atan2(H, L))
    hor = 0.66 * fh
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    # sky: dawn (low sun) is darker and graded, noon is bright and flat
    k = (elev - 28) / 40.0                     # 0 = dawn .. 1 = high
    top = 0.38 + 0.42 * k
    low = 0.95
    sky = top + (low - top) * (yy / hor) ** 1.4
    # sun
    sx = (0.10 + 0.08 * k) * fw
    sy = hor - (elev / 90.0) * hor * 1.02
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    sky = sky + 0.9 * np.exp(-d / (0.10 * fw)) + 0.5 * np.exp(-(d / (0.035 * fw)) ** 2)
    sky = np.where(d < 0.035 * fw, 1.6, sky)
    img = sky.copy()
    # distant ridge (the valley)
    r = np.random.default_rng(seed)
    ridge = hor - (6 + 10 * noise(1, fw, 40, 3, seed)[0]) * fh / 184
    img = np.where(yy > ridge[None, :], 0.42 + 0.1 * k, img)
    # ground: paved plaza, lighter toward the camera, with joints
    g = 0.62 + 0.18 * ((yy - hor) / (fh - hor))
    joints = (np.abs(np.mod((xx - 0.3 * fw) / (0.5 * u), 1.0) - 0.5) > 0.47).astype(np.float32) * 0.0
    img = np.where(yy >= hor, g - joints, img)
    pen = Pen(fw, fh, 4)
    bx = 0.26 * fw
    by = hor + 0.11 * fh
    # paving band the obelisk stands on
    band = Pen(fw, fh, 4)
    band.poly([(0, by - 0.04 * fh), (fw, by - 0.04 * fh), (fw, by + 0.05 * fh), (0, by + 0.05 * fh)])
    bm = band.arr()
    img = img * (1 - bm) + bm * (0.78 + 0.06 * k)
    # unit stones (sundial marks) at 1..5 units from the base centre
    marks = Pen(fw, fh, 4)
    for i in range(1, 6):
        mx = bx + i * u
        marks.rect(mx - 0.012 * fw, by - 0.03 * fh, mx + 0.012 * fw, by + 0.03 * fh, radius=1)
    mm = marks.arr()
    img = img * (1 - mm) + mm * 0.30
    # shadow on the ground: from the base to L units, tapering
    ow = 0.075 * fw
    shp = Pen(fw, fh, 4)
    tip = bx + L * u
    shp.poly([(bx - ow * 0.45, by - 0.018 * fh), (tip, by - 0.006 * fh), (tip, by + 0.006 * fh), (bx - ow * 0.45, by + 0.022 * fh)])
    sm = blur(shp.arr(), 0.5)
    img = img * (1 - 0.82 * sm)
    # obelisk: tapered shaft + pyramidion, lit side toward the sun (left)
    top_y = by - H * u
    w0, w1 = ow / 2, ow * 0.30
    shaft_l = [(bx - w0, by), (bx - w1, top_y + 0.12 * u * 2), (bx, top_y + 0.12 * u * 2), (bx, by)]
    shaft_r = [(bx, by), (bx, top_y + 0.24 * u), (bx + w1, top_y + 0.24 * u), (bx + w0, by)]
    pyr_l = [(bx - w1, top_y + 0.24 * u), (bx, top_y - 0.10 * u), (bx, top_y + 0.24 * u)]
    pyr_r = [(bx, top_y + 0.24 * u), (bx, top_y - 0.10 * u), (bx + w1, top_y + 0.24 * u)]
    lit = Pen(fw, fh, 4)
    lit.poly(shaft_l)
    lit.poly(pyr_l)
    dark = Pen(fw, fh, 4)
    dark.poly(shaft_r)
    dark.poly(pyr_r)
    base = Pen(fw, fh, 4)
    base.rect(bx - w0 * 1.5, by - 0.035 * fh, bx + w0 * 1.5, by + 0.01 * fh)
    lm, dm, bm2 = lit.arr(), dark.arr(), base.arr()
    img = img * (1 - lm) + lm * (0.30 + 0.35 * (1 - k))
    img = img * (1 - dm) + dm * 0.08
    img = img * (1 - bm2) + bm2 * 0.22
    del pen, r
    return img


# =================================================================================================
# Film strips (900 x 300, RGBA: sprocket holes are transparent)
# =================================================================================================
STRIP_W, STRIP_H = 900, 300
STRIP_MARGIN = 54          # sprocket band height (top and bottom)
STRIP_FRAME_W = 270
STRIP_PITCH = 292          # frame pitch; frames centred at 450 - 292, 450, 450 + 292


def film_strip(k: int):
    L = SPLICE_SHADOWS[k]
    w, h = STRIP_W, STRIP_H
    r = np.random.default_rng(300 + k)
    # base: warm grey-amber film base, darker exposed edges
    base = np.zeros((h, w), np.float32) + 0.10
    alpha = np.ones((h, w), np.float32)
    fh = h - 2 * STRIP_MARGIN - 12
    y0 = STRIP_MARGIN + 6
    lum = base.copy()
    for j, cx in enumerate((w / 2 - STRIP_PITCH, w / 2, w / 2 + STRIP_PITCH)):
        x0 = int(round(cx - STRIP_FRAME_W / 2))
        sc = obelisk_scene(STRIP_FRAME_W, fh, L, 310 + 10 * k + j)
        sc = sc * (0.96 + 0.08 * r.random())          # exposure flicker per frame
        fr = Pen(STRIP_FRAME_W, fh, 4)
        fr.rect(0, 0, STRIP_FRAME_W, fh, radius=7)
        fm = fr.arr()
        lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] = lum[y0:y0 + fh, x0:x0 + STRIP_FRAME_W] * (1 - fm) + sc * fm
    # sprocket holes (Bell & Howell shape: rounded rectangles), 4 per frame pitch
    holes = Pen(w, h, 4)
    pitch = STRIP_PITCH / 4.0
    hw, hh = 22, 30
    for i in range(-2, 16):
        hx = w / 2 - STRIP_PITCH * 1.5 + pitch * (i + 0.5)
        for hy in (STRIP_MARGIN / 2, h - STRIP_MARGIN / 2):
            if -hw < hx < w + hw:
                holes.rect(hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2, radius=5)
    hm = holes.arr()
    # edge print (latent edge text) in the margins, no digits (they would look like an order clue)
    ep = Pen(w, h, 4)
    for i, ex in enumerate((w / 2 - STRIP_PITCH, w / 2 + STRIP_PITCH)):
        ep.text(ex, h - 8, "SAFETY  FILM", F_SANS_B, 13, anchor="ms", spacing=1.2)
        ep.poly([(ex + 72, h - 18), (ex + 82, h - 13), (ex + 72, h - 8)])
    em = ep.arr()
    lum = lum + em * 0.55
    rgb = film_finish(lum * 1.05, 330 + k, grain_amt=0.05, scratches=3, dust=25, vignette=0.12, gate=False,
                      tint=(1.0, 0.93, 0.80), hair=False)
    # amber cast in the clear base (M_Film look), cut ends slightly darker from handling
    yy, xx = np.mgrid[0:h, 0:w]
    edge = smooth(0, 60, np.minimum(xx, w - 1 - xx)).astype(np.float32)
    rgb = rgb * (0.82 + 0.18 * edge)[..., None]
    # hole edges: a thin bright rim (light catching the cut edge)
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
    # tinplate painted grey-green, pressed concentric rings, rim
    n = noise(S, S, 120, 4, 401)
    fine = noise(S, S, 3, 2, 402)
    base = hexf("#5E6A60")
    rgb = base[None, None, :] * (0.86 + 0.18 * n + 0.06 * (fine - 0.5))[..., None]
    ang = np.arctan2(yy - c, xx - c)
    brushed = noise(S, S, 2, 1, 403)
    for r0, r1, s in ((0.965, 1.0, 0.55), (0.90, 0.93, 1.25), (0.86, 0.885, 0.78), (0.30, 0.32, 1.18)):
        m = smooth(r0 - 0.008, r0, rr) * (1 - smooth(r1, r1 + 0.008, rr))
        rgb = rgb * (1 + (s - 1) * m)[..., None]
    # light from the top-left on the pressed rings
    shade = 1 + 0.10 * np.cos(ang + 2.4) * smooth(0.84, 0.99, rr)
    rgb = rgb * shade[..., None]
    # wear: scuffs to bare tin and rust freckles
    scuff = smooth(0.70, 0.86, noise(S, S, 25, 3, 404)) * smooth(0.6, 1.0, rr)
    rgb = paint(rgb, scuff, "#A9A9A0", 0.65)
    rust = smooth(0.80, 0.95, noise(S, S, 6, 2, 405)) * (0.4 + 0.6 * smooth(0.85, 1.0, rr))
    rgb = paint(rgb, rust, "#6B3A1E", 0.6)
    # painted pictogram band (cream enamel strip across the middle)
    bw, bh = 640, 250
    bx0, by0 = c - bw / 2, c - bh / 2 + 40
    band = Pen(S, S, 4)
    band.rect(bx0, by0, bx0 + bw, by0 + bh, radius=18)
    bm = band.arr()
    cream = hexf("#E3D7B8") * (0.92 + 0.1 * noise(S, S, 60, 3, 406))[..., None]
    rgb = rgb * (1 - bm[..., None]) + cream * bm[..., None]
    # three panels: sunrise (long shadow) -> morning -> high sun (short shadow)
    ink_p = Pen(S, S, 4)
    sun_p = Pen(S, S, 4)
    panels = [(bx0 + 110, 5.0, 4.0), (bx0 + 320, 2.6, 22.0), (bx0 + 530, 0.9, 62.0)]
    ground = by0 + 160
    for px, shadow, elev in panels:
        u = 24
        ox = px - 70
        ink_p.rect(ox - 30, ground, ox + 190, ground + 5)                       # ground line
        ink_p.poly([(ox - 8, ground), (ox - 4, ground - 70), (ox + 4, ground - 70), (ox + 8, ground)])  # obelisk
        ink_p.poly([(ox - 4, ground - 70), (ox, ground - 80), (ox + 4, ground - 70)])
        ink_p.poly([(ox + 6, ground + 1), (ox + 6 + shadow * u, ground + 3), (ox + 6 + shadow * u, ground + 9), (ox + 6, ground + 11)])
        # sun: on the horizon at sunrise (half disc), higher and to the left otherwise
        sx = ox - 22 + (0 if elev < 10 else -6)
        sy = ground - 2 - elev * 1.45
        if elev < 10:
            sun_p.circle(sx, ground - 1, 20)
            sun_p.rect(sx - 30, ground, sx + 30, ground + 30, v=0)
            for a in range(200, 341, 28):
                ra = math.radians(a)
                sun_p.line([(sx + 27 * math.cos(ra), ground + 27 * math.sin(ra)),
                            (sx + 40 * math.cos(ra), ground + 40 * math.sin(ra))], 5)
        else:
            sun_p.circle(sx, sy, 17)
            for a in range(0, 360, 45):
                ra = math.radians(a)
                sun_p.line([(sx + 24 * math.cos(ra), sy + 24 * math.sin(ra)),
                            (sx + 35 * math.cos(ra), sy + 35 * math.sin(ra))], 5)
    # arrow under the panels, left -> right
    ay = by0 + bh - 38
    ink_p.rect(bx0 + 60, ay - 4, bx0 + bw - 90, ay + 4)
    ink_p.poly([(bx0 + bw - 100, ay - 20), (bx0 + bw - 56, ay), (bx0 + bw - 100, ay + 20)])
    im_ink = ink(ink_p.arr(), 407, 0.25) * bm
    im_sun = ink(sun_p.arr(), 408, 0.2) * bm
    rgb = paint(rgb, im_sun, "#C77A22", 0.95)
    rgb = paint(rgb, im_ink, "#24282A", 0.95)
    # chipped enamel on the band edge
    chips = smooth(0.78, 0.9, noise(S, S, 9, 3, 409)) * (blur(bm, 6) < 0.92) * bm
    rgb = paint(rgb, chips.astype(np.float32), "#545C55", 0.85)
    # masking tape with Strand's note
    tape = Pen(S, S, 4)
    tape.poly([(250, 150), (520, 128), (526, 196), (256, 218)])
    tm = tape.arr()
    rgb = paint(rgb, tm, "#D9C79A", 0.92)
    hw = Pen(S, S, 4)
    rot_text(hw, 388, 170, "E.S. · 1979 · reel 1", F_HAND, 44, angle=4.5, weight=600)
    rgb = paint(rgb, ink(hw.arr(), 410, 0.2) * tm, "#1E2340", 0.92)
    # centre boss with a pressed star (the lid's maker mark), dulled
    boss = Pen(S, S, 4)
    boss.circle(c, c - 230 + 0, 0)
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
