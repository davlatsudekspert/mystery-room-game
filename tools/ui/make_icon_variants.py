#!/usr/bin/env python3
"""App-icon candidates with a larger central symbol (the eye, door, lens and light), for the owner to choose.

The shipped icon (game/assets/ui/icon*.png, made by tools/ui/make_logo_variants.py from docs/brand/logo_source.png)
is variant A and stays untouched. B and C use the very same artwork, palette, background and glow; only the emblem
is scaled up around the icon centre, so the lens, the door of light and the lids read better at 60 px and 120 px.
The outer ornaments (corner orbs, side-spike tips, the ends of the outer arc) are allowed to crop, and they fade
softly into the dark teal instead of being cut hard. There is no text in any icon.

Nothing here is written into game/assets. Output goes to docs/brand/icon_variants/:
    {A,B,C}_ios_1024.png            1024x1024, RGB (no alpha), full bleed (iOS applies its own mask)
    {A,B,C}_adaptive_fg_432.png     Android adaptive foreground, 432x432 RGBA (safe zone = central 66 %)
    {A,B,C}_adaptive_bg_432.png     Android adaptive background, 432x432
    {A,B,C}_monochrome_432.png      Android 13+ themed icon silhouette (the lens and door grow, the eye width stays)
    small_sizes.png                 A, B, C at 60 px and 120 px, actual pixels and a 4x nearest-neighbour zoom
    home_screen_preview.png/.jpg    iPhone home screen mock: 180 px icons (60 pt @3x) and a 120 px row (40 pt @3x)
    android_launcher_preview.png    circle and squircle launcher masks, plus the themed (monochrome) icon

    python3 tools/ui/make_icon_variants.py

The preview art is drawn here (abstract placeholder tiles, no real app logos). Fonts: the game's own Noto Sans.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_logo_variants as base  # noqa: E402  (same emblem cut, background and glow as the shipped icon)

ROOT = base.ROOT
UI = os.path.join(ROOT, "game/assets/ui")
OUT = os.path.join(ROOT, "docs/brand/icon_variants")
FONT = os.path.join(ROOT, "game/assets/fonts/NotoSans-Variable.ttf")

# scale = how much larger the emblem is than in the shipped icon (A). ios_fade = soft edge (px of 1024) where the
# outer ornaments run past the canvas; adaptive_fade = the same for the 432 px Android layer (radial, see below).
VARIANTS: dict[str, dict] = {
    "A": {"scale": 1.00, "ios_fade": 0, "adaptive_fade": False, "tag": "A  current"},
    "B": {"scale": 1.15, "ios_fade": 40, "adaptive_fade": True, "tag": "B  +15 %"},
    "C": {"scale": 1.20, "ios_fade": 84, "adaptive_fade": True, "tag": "C  +20 %"},
}
EMBLEM_W_A = 962  # px: width of the emblem in the shipped 1024 icon (int(1024 * 0.94))
LENS_RING_A = 457  # px of the 1024 icon: outer diameter of the gold ring round the lens, measured on the shipped icon
SAFE_R = 132  # Android adaptive safe zone: a 66 dp circle of the 108 dp layer = radius 132 px at 432 px
VISIBLE_R = 144  # the 72 dp window every launcher mask is cut from = radius 144 px at 432 px
FADE_R0, FADE_R1 = 126, 150  # adaptive foreground: full opacity inside R0, fully faded by R1 (radius from the centre)


# ----------------------------------------------------------------------------------------------- icon rendering
def smoothstep(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def place(layer: Image.Image, img: Image.Image, left: int, top: int) -> None:
    """alpha_composite that tolerates an image hanging over the layer's edge (the overhang is cropped)."""
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(layer.width, left + img.width), min(layer.height, top + img.height)
    if x0 < x1 and y0 < y1:
        layer.alpha_composite(img.crop((x0 - left, y0 - top, x1 - left, y1 - top)), (x0, y0))


def scale_alpha(im: Image.Image, weight: np.ndarray) -> None:
    a = np.asarray(im.getchannel("A")).astype(np.float32) * weight
    im.putalpha(Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "L"))


def ios_icon(emblem: Image.Image, k: float, fade: int) -> tuple[Image.Image, Image.Image]:
    """-> (1024 RGB icon, emblem layer). k = 1 with no fade is exactly make_logo_variants.make_icons()."""
    s = 1024
    e = base.fit(emblem, int(s * 0.94 * k))
    pos = ((s - e.width) // 2, (s - e.height) // 2)
    bg = base.icon_background(s)
    gl = Image.new("RGBA", e.size, (90, 230, 255, 0))
    gl.putalpha(e.getchannel("A").filter(ImageFilter.GaussianBlur(26 * k)).point(lambda v: int(v * 0.35)))
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    glow.paste(gl, pos, gl)
    layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    place(layer, e, *pos)
    if fade:  # the ornaments that run past the left/right edge dissolve over the last `fade` px instead of being cut
        x = np.arange(s, dtype=np.float32) + 0.5
        w = smoothstep(np.minimum(x, s - x) / fade)[None, :]
        scale_alpha(glow, w)
        scale_alpha(layer, w)
    icon = Image.alpha_composite(bg, glow)
    icon.alpha_composite(layer)
    return icon.convert("RGB"), layer


def adaptive_fg(emblem: Image.Image, k: float, radial: bool) -> Image.Image:
    s = 432
    e = base.fit(emblem, int(s * 0.64 * k))
    fg = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    place(fg, e, (s - e.width) // 2, (s - e.height) // 2)
    if radial:  # whatever lies beyond the safe zone (corner orbs, spike tips) fades out before the 72 dp window ends
        yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
        r = np.hypot(xx + 0.5 - s / 2, yy + 0.5 - s / 2)
        scale_alpha(fg, 1.0 - smoothstep((r - FADE_R0) / (FADE_R1 - FADE_R0)))
    return fg


def monochrome_eye(size: int, k: float) -> Image.Image:
    """make_logo_variants.monochrome_eye with the lens, the lids' height and the door scaled by k.
    The almond's width stays (it already fills the safe zone), so the lens grows relative to the eye."""
    s = size * 4
    img = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(img)
    cx, cy = s / 2, s / 2
    half_w, amp = s * 0.31, s * 0.15 * k

    def almond(f: float) -> list[tuple[float, float]]:
        pts = []
        for i in range(61):
            t = i / 60
            pts.append((cx - half_w * f + 2 * half_w * f * t, cy - amp * f * np.sin(np.pi * t)))
        for i in range(61):
            t = 1 - i / 60
            pts.append((cx - half_w * f + 2 * half_w * f * t, cy + amp * f * np.sin(np.pi * t)))
        return pts

    d.polygon(almond(1.0), fill=255)
    d.polygon(almond(0.86), fill=0)
    r = amp * 0.92
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    r2 = r * 0.8
    d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=0)
    dw, dh = r * 0.42, r * 0.95
    d.rounded_rectangle((cx - dw / 2, cy - dh / 2, cx + dw / 2, cy + dh / 2), radius=dw * 0.45, fill=255)
    img = img.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.putalpha(img)
    return out


def door_light_width(icon: Image.Image) -> int:
    """Width in px of the near-white core of the door of light (median of three rows), in the 1024 icon."""
    a = np.asarray(icon.convert("RGB")).astype(int)
    widths = []
    for y in (540, 570, 600):
        xs = np.nonzero(a[y, 440:600].min(axis=1) > 200)[0]
        widths.append(int(xs[-1] - xs[0] + 1) if len(xs) else 0)
    return sorted(widths)[1]


def make_variants() -> dict[str, dict]:
    src = Image.open(base.SRC).convert("RGBA")
    emblem = base.emblem_of(src)
    os.makedirs(OUT, exist_ok=True)
    info: dict[str, dict] = {}
    for name, v in VARIANTS.items():
        k = v["scale"]
        icon, layer = ios_icon(emblem, k, v["ios_fade"])
        fg = adaptive_fg(emblem, k, v["adaptive_fade"])
        bg = base.icon_background(432).convert("RGB")
        mono = monochrome_eye(432, k)
        icon.save(os.path.join(OUT, f"{name}_ios_1024.png"))
        fg.save(os.path.join(OUT, f"{name}_adaptive_fg_432.png"))
        bg.save(os.path.join(OUT, f"{name}_adaptive_bg_432.png"))
        mono.save(os.path.join(OUT, f"{name}_monochrome_432.png"))

        # --- checks: nothing is cut, the symbol stays inside the safe zones
        assert icon.mode == "RGB" and icon.size == (1024, 1024), "iOS icon must be 1024 RGB (no alpha)"
        edge = np.asarray(layer.getchannel("A"))
        frame = np.concatenate([edge[0], edge[-1], edge[:, 0], edge[:, -1]])
        assert frame.max() <= 8, f"{name}: the emblem is hard-cropped at the icon edge (alpha {frame.max()})"
        a = np.asarray(fg.getchannel("A"))
        yy, xx = np.nonzero(a >= 128)
        rmax = float(np.hypot(xx + 0.5 - 216, yy + 0.5 - 216).max())
        assert rmax <= VISIBLE_R, f"{name}: adaptive foreground has opaque pixels beyond the 72 dp window ({rmax:.0f})"
        info[name] = {
            "scale": k,
            "lens_1024": LENS_RING_A * k,
            "door_1024": door_light_width(icon),
            "adaptive_rmax": rmax,
            "lens_r_fg": LENS_RING_A / EMBLEM_W_A * int(432 * 0.64 * k) / 2,
        }
        assert info[name]["lens_r_fg"] <= SAFE_R, f"{name}: the lens leaves the adaptive safe zone"

    # A must be the shipped icon, unchanged: regenerate it and compare, then copy the shipped files as they are
    for n in ("icon.png", "icon_adaptive_fg.png", "icon_adaptive_bg.png", "icon_monochrome.png"):
        a = np.asarray(Image.open(os.path.join(UI, n)).convert("RGBA")).astype(int)
        b = np.asarray(Image.open(os.path.join(OUT, {"icon.png": "A_ios_1024.png", "icon_adaptive_fg.png": "A_adaptive_fg_432.png",
                                                      "icon_adaptive_bg.png": "A_adaptive_bg_432.png",
                                                      "icon_monochrome.png": "A_monochrome_432.png"}[n])).convert("RGBA")).astype(int)
        assert np.array_equal(a, b), f"variant A differs from the shipped {n}; make_logo_variants.py or the source changed"
    return info


# ------------------------------------------------------------------------------------------------- preview parts
def font(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:  # noqa: BLE001 - FreeType builds without variable-font axes
        pass
    return f


def mask_ios(size: int) -> Image.Image:
    """iOS app-icon rounded square: corner radius 22.37 % of the side (Apple's published approximation)."""
    s = size * 4
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), radius=round(s * 0.2237), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def mask_superellipse(size: int, n: float) -> Image.Image:
    """n = 2 is a circle; n = 4 is the squircle most Android launchers offer."""
    s = size * 4
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    x, y = (xx + 0.5) / s * 2 - 1, (yy + 0.5) / s * 2 - 1
    m = Image.fromarray(((np.abs(x) ** n + np.abs(y) ** n <= 1.0) * 255).astype(np.uint8), "L")
    return m.resize((size, size), Image.LANCZOS)


def masked(img: Image.Image, mask: Image.Image) -> Image.Image:
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def android_composite(name: str, size: int, mask: Image.Image) -> Image.Image:
    """The launcher shows the central 72 dp (2/3) of the 108 dp adaptive layers, cut by the mask."""
    bg = Image.open(os.path.join(OUT, f"{name}_adaptive_bg_432.png")).convert("RGBA")
    fg = Image.open(os.path.join(OUT, f"{name}_adaptive_fg_432.png")).convert("RGBA")
    full = Image.alpha_composite(bg, fg).crop((72, 72, 360, 360)).resize((size, size), Image.LANCZOS)
    return masked(full, mask)


def wallpaper(w: int, h: int) -> Image.Image:
    """A dark indigo/plum/teal wallpaper: dark enough to be the hardest case for a dark teal icon."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    a, b, c = np.array([14, 16, 30.0]), np.array([58, 36, 74.0]), np.array([18, 52, 66.0])
    t1 = np.clip(1 - np.hypot(u - 0.18, (v - 0.22) * 0.55) * 1.35, 0, 1)[..., None]
    t2 = np.clip(1 - np.hypot(u - 0.88, (v - 0.78) * 0.55) * 1.25, 0, 1)[..., None]
    rgb = a * (1 - t1) * (1 - t2) + b * t1 + c * t2
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# neutral placeholder tiles: flat colours and abstract geometry only
TILE_COLOURS = ["#3b6ea5", "#c9553d", "#4f8f6a", "#d4a537", "#7a5ca8", "#e8e4dc", "#2f3a4a", "#b8527a",
                "#5aa3a8", "#8d6e4f", "#d9743f", "#46506b"]
TILE_SHAPES = ["dots", "bars", "ring", "tri", "wave", "grid", "slash", "drop"]
TILE_NAMES = ["Tasks", "Budget", "Garden", "Recipes", "Fitness", "Travel", "Reader", "Radio", "Sketch", "Planner",
              "Journal", "Timer", "Puzzles", "Languages", "Habits", "Tickets", "Pantry"]


def tile(size: int, i: int, mask: Image.Image) -> Image.Image:
    colour = TILE_COLOURS[i % len(TILE_COLOURS)]
    light = sum(int(colour[j:j + 2], 16) for j in (1, 3, 5)) > 560
    ink = "#2b2f38" if light else "#ffffff"
    img = Image.new("RGBA", (size, size), colour)
    d = ImageDraw.Draw(img)
    c, r = size / 2, size * 0.30
    w = max(3, round(size * 0.07))
    kind = TILE_SHAPES[(i * 3 + 1) % len(TILE_SHAPES)]
    if kind == "dots":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                d.ellipse((c + dx * r * 0.7 - r * 0.16, c + dy * r * 0.7 - r * 0.16, c + dx * r * 0.7 + r * 0.16, c + dy * r * 0.7 + r * 0.16), fill=ink)
    elif kind == "bars":
        for j, hgt in enumerate((0.5, 0.9, 0.7)):
            x = c - r * 0.8 + j * r * 0.8
            d.rounded_rectangle((x - r * 0.18, c + r * 0.7 - r * 1.4 * hgt, x + r * 0.18, c + r * 0.7), radius=r * 0.1, fill=ink)
    elif kind == "ring":
        d.ellipse((c - r, c - r, c + r, c + r), outline=ink, width=w * 2)
    elif kind == "tri":
        d.polygon([(c, c - r), (c + r * 0.95, c + r * 0.7), (c - r * 0.95, c + r * 0.7)], outline=ink, width=w * 2)
    elif kind == "wave":  # a half ring with a dot
        d.arc((c - r, c - r * 0.6, c + r, c + r * 1.4), 180, 360, fill=ink, width=w * 2)
        d.ellipse((c - r * 0.2, c + r * 0.35, c + r * 0.2, c + r * 0.75), fill=ink)
    elif kind == "grid":
        for dx in (-0.5, 0.5):
            for dy in (-0.5, 0.5):
                d.rounded_rectangle((c + dx * r * 1.3 - r * 0.5, c + dy * r * 1.3 - r * 0.5, c + dx * r * 1.3 + r * 0.5, c + dy * r * 1.3 + r * 0.5), radius=r * 0.12, fill=ink)
    elif kind == "slash":
        d.line((c - r * 0.8, c + r * 0.8, c + r * 0.8, c - r * 0.8), fill=ink, width=w * 3)
    else:  # drop
        d.ellipse((c - r * 0.7, c - r * 0.25, c + r * 0.7, c + r * 1.15), fill=ink)
        d.polygon([(c, c - r * 1.1), (c + r * 0.62, c + r * 0.15), (c - r * 0.62, c + r * 0.15)], fill=ink)
    return masked(img, mask)


def text(d: ImageDraw.ImageDraw, xy: tuple[float, float], s: str, size: int, fill, weight: int = 500, anchor: str = "mm") -> None:
    d.text(xy, s, font=font(size, weight), fill=fill, anchor=anchor)


def panel(img: Image.Image, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int]) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill)
    img.alpha_composite(layer)


def home_screen_ios() -> Image.Image:
    """iPhone 15 Pro class screen at @3x: 1179x2556 px = 393x852 pt. Icons are 60 pt = 180 px."""
    w, h, icon = 1179, 2556, 180
    img = wallpaper(w, h)
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 235)
    # status bar and Dynamic Island
    text(d, (190, 96), "9:41", 50, white, 600)
    d.rounded_rectangle((w / 2 - 189, 33 * 3 - 4, w / 2 + 189, 33 * 3 + 107), radius=56, fill=(0, 0, 0, 255))
    for i in range(4):
        d.rounded_rectangle((900 + i * 22, 112 - i * 9 - 8, 912 + i * 22, 112), radius=3, fill=white)
    d.rounded_rectangle((1000, 78, 1086, 114), radius=11, outline=(255, 255, 255, 150), width=3)
    d.rounded_rectangle((1006, 84, 1068, 108), radius=6, fill=white)

    mk = mask_ios(icon)
    cols = [82, 357, 632, 907]
    rows = [270, 561, 852, 1143, 1434]
    names = list(TILE_NAMES)
    ti = 0
    for ri, y in enumerate(rows):
        for ci, x in enumerate(cols):
            if ri == 2 and ci >= 1:
                name = "ABC"[ci - 1]
                ic = masked(Image.open(os.path.join(OUT, f"{name}_ios_1024.png")).resize((icon, icon), Image.LANCZOS), mk)
                img.alpha_composite(ic, (x, y))
                text(d, (x + icon / 2, y + icon + 36), "Mystery Room", 31, white, 500)
                text(d, (x + icon / 2, y + icon + 84), VARIANTS[name]["tag"], 27, (226, 190, 110, 255), 600)
            else:
                img.alpha_composite(tile(icon, ti, mk), (x, y))
                text(d, (x + icon / 2, y + icon + 36), names[ti % len(names)], 31, white, 500)
                ti += 1

    # the small size: Spotlight / Settings, 40 pt @3x = 120 px
    py0, py1 = 1736, 2100
    panel(img, (50, py0, w - 50, py1), 56, (255, 255, 255, 34))
    text(d, (w / 2, py0 + 50), "Spotlight and Settings size:  40 pt @3x = 120 px", 30, (255, 255, 255, 190), 500)
    small = 120
    mk2 = mask_ios(small)
    sx = [190, 530, 870]
    for name, x in zip("ABC", sx):
        ic = masked(Image.open(os.path.join(OUT, f"{name}_ios_1024.png")).resize((small, small), Image.LANCZOS), mk2)
        img.alpha_composite(ic, (x, py0 + 100))
        text(d, (x + small / 2, py0 + 100 + small + 30), "Mystery Room", 27, white, 500)
        text(d, (x + small / 2, py0 + 100 + small + 70), VARIANTS[name]["tag"], 24, (226, 190, 110, 255), 600)

    # page dots, dock
    for i in range(3):
        d.ellipse((w / 2 - 50 + i * 40 - 8, 2188 - 8, w / 2 - 50 + i * 40 + 8, 2188 + 8), fill=(255, 255, 255, 230 if i == 0 else 110))
    panel(img, (40, 2240, w - 40, 2502), 80, (255, 255, 255, 52))
    for ci, x in enumerate(cols):
        img.alpha_composite(tile(icon, 7 + ci * 2, mk), (x, 2280))
    d.rounded_rectangle((w / 2 - 210, 2536 - 8, w / 2 + 210, 2536), radius=5, fill=(255, 255, 255, 235))
    return img.convert("RGB")


def android_panel(shape: str) -> Image.Image:
    """One phone screen (1080 px wide) with a circle or squircle launcher; icons are 56 dp @3x = 168 px."""
    w, h, icon = 1080, 1260, 168
    img = wallpaper(w, h)
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 235)
    text(d, (96, 60), "9:41", 40, white, 500)
    n = 2.0 if shape == "circle" else 4.0
    mk = mask_superellipse(icon, n)
    xs = [round(135 + 270 * i - icon / 2) for i in range(4)]
    rows = [140, 420, 700, 960]
    ti = 3
    for ri, y in enumerate(rows):
        for ci, x in enumerate(xs):
            if ri == 1 and ci < 3:
                name = "ABC"[ci]
                img.alpha_composite(android_composite(name, icon, mk), (x, y))
                text(d, (x + icon / 2, y + icon + 32), "Mystery Room", 28, white, 400)
                text(d, (x + icon / 2, y + icon + 74), VARIANTS[name]["tag"], 25, (226, 190, 110, 255), 600)
            elif ri == 3:
                img.alpha_composite(tile(icon, 5 + ci * 2, mk), (x, y))
            else:
                img.alpha_composite(tile(icon, ti, mk), (x, y))
                text(d, (x + icon / 2, y + icon + 32), TILE_NAMES[ti % len(TILE_NAMES)], 28, white, 400)
                ti += 1
    panel(img, (60, h - 110, w - 60, h - 30), 40, (255, 255, 255, 44))
    return img.convert("RGB")


def android_preview() -> Image.Image:
    pw, ph = 1080, 1260
    gap, top, strip = 40, 100, 360
    canvas = Image.new("RGB", (2 * pw + 3 * gap, top + ph + strip + 2 * gap), (22, 24, 30))
    d = ImageDraw.Draw(canvas)
    for i, (shape, label) in enumerate((("circle", "Circle mask"), ("squircle", "Squircle mask"))):
        x = gap + i * (pw + gap)
        text(d, (x + pw / 2, 52), label, 40, (240, 240, 240), 600)
        canvas.paste(android_panel(shape), (x, top))
    # themed (monochrome) icons, Android 13+: the launcher tints the silhouette on a pale disc
    y0 = top + ph + gap
    text(d, (canvas.width / 2, y0 + 30), "Themed icon (Android 13+): the monochrome silhouette, 56 dp @3x = 168 px", 32, (230, 230, 230), 500)
    disc = 168
    mk = mask_superellipse(disc, 2.0)
    for i, name in enumerate("ABC"):
        cx = canvas.width / 2 + (i - 1) * 420
        mono = Image.open(os.path.join(OUT, f"{name}_monochrome_432.png")).convert("RGBA").crop((72, 72, 360, 360)).resize((disc, disc), Image.LANCZOS)
        tint = Image.new("RGBA", mono.size, (40, 52, 70, 255))
        tint.putalpha(mono.getchannel("A"))
        tile_img = masked(Image.new("RGB", (disc, disc), (215, 227, 244)), mk)
        tile_img.alpha_composite(tint)
        tile_img.putalpha(mk)
        canvas.paste(tile_img.convert("RGB"), (int(cx - disc / 2), y0 + 70), mk)
        text(d, (cx, y0 + 70 + disc + 36), "Mystery Room", 28, (230, 230, 230), 400)
        text(d, (cx, y0 + 70 + disc + 76), VARIANTS[name]["tag"], 25, (226, 190, 110), 600)
    return canvas


def write_small_sizes() -> None:
    """The small-size sheet: row 1 = 120 px, row 2 = 60 px (both on dark), row 3 = 60 and 120 px on a light ground,
    and a 4x nearest-neighbour zoom of the 60 px renders on the right."""
    pad, zoom = 28, 240
    col_w = 120 + pad
    left_w = pad + 3 * col_w
    canvas = Image.new("RGB", (left_w + 30 + 3 * (zoom + pad), 4 * 150 + 80), (28, 28, 34))
    d = ImageDraw.Draw(canvas)
    light = Image.new("RGB", (left_w - pad // 2, 2 * 150 - 10), (236, 238, 242))
    canvas.paste(light, (pad // 2, 2 * 150 + 40))
    text(d, (pad, 22), "60 px and 120 px, actual pixels (iOS mask)", 22, (210, 210, 215), 500, "lm")
    text(d, (left_w + 30, 22), "60 px, zoomed 4x (nearest neighbour)", 22, (210, 210, 215), 500, "lm")
    for i, name in enumerate("ABC"):
        icon = Image.open(os.path.join(OUT, f"{name}_ios_1024.png"))
        x = pad + i * col_w
        for j, (bgy, size) in enumerate(((50, 120), (50 + 150, 60), (2 * 150 + 50, 120), (3 * 150 + 50, 60))):
            ic = masked(icon.resize((size, size), Image.LANCZOS), mask_ios(size))
            canvas.paste(ic.convert("RGB"), (x + (120 - size) // 2, bgy + (120 - size) // 2), ic.getchannel("A"))
        text(d, (x + 60, 4 * 150 + 52), VARIANTS[name]["tag"], 22, (226, 190, 110), 600)
        z = icon.resize((60, 60), Image.LANCZOS).resize((zoom, zoom), Image.NEAREST)
        canvas.paste(z, (left_w + 30 + i * (zoom + pad), 50))
    canvas.save(os.path.join(OUT, "small_sizes.png"))


def save_jpeg_under(img: Image.Image, path: str, limit: int = 380_000) -> int:
    for q in range(92, 40, -2):
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True, subsampling=2)
        if os.path.getsize(path) <= limit:
            return q
    raise RuntimeError("could not get the preview under the size limit")


def main() -> None:
    info = make_variants()
    write_small_sizes()
    home = home_screen_ios()
    home.save(os.path.join(OUT, "home_screen_preview.png"), optimize=True)
    q = save_jpeg_under(home, os.path.join(OUT, "home_screen_preview.jpg"))
    android_preview().save(os.path.join(OUT, "android_launcher_preview.png"), optimize=True)
    print(f"icon variants -> {OUT}  (jpg quality {q}, {os.path.getsize(os.path.join(OUT, 'home_screen_preview.jpg')) // 1000} KB)")
    for name, i in info.items():
        print(f"  {name}: scale x{i['scale']:.2f}  lens ring {i['lens_1024']:.0f}px of 1024 ({i['lens_1024'] / 10.24:.1f} %) "
              f"-> {i['lens_1024'] * 60 / 1024:.1f}px at 60, {i['lens_1024'] * 120 / 1024:.1f}px at 120; "
              f"door-light core {i['door_1024']}px of 1024 -> {i['door_1024'] * 60 / 1024:.1f}px at 60; "
              f"adaptive: lens radius {i['lens_r_fg']:.0f}px (safe {SAFE_R}), outermost opaque pixel {i['adaptive_rmax']:.0f}px (window {VISIBLE_R})")


if __name__ == "__main__":
    main()
