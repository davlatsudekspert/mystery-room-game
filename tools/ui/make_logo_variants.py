#!/usr/bin/env python3
"""Localized logos and app icons from the owner's chosen logo (game/assets/ui/logo/logo_source.png).

The logo's subtitle "THE FORGOTTEN INSTITUTE" is baked into the artwork. Visible text must exist in EN, RU
and UZ, so the RU/UZ versions repaint the subtitle banner and engrave the translated subtitle in the same
gold style. The app icon is the logo's emblem (the eye with the crystal and the door of light), without text.

Writes:
    game/assets/ui/logo/logo_en.png, logo_ru.png, logo_uz.png
    game/assets/ui/icon.png (1024, full bleed), icon_adaptive_fg.png / icon_adaptive_bg.png / icon_monochrome.png (432)
    docs/store/graphics/icon_512.png

    python3 tools/ui/make_logo_variants.py
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "game/assets/ui/logo/logo_source.png")
OUT = os.path.join(ROOT, "game/assets/ui/logo")
FONT = os.path.join(ROOT, "game/assets/fonts/CormorantGaramond-Bold.ttf")

# subtitle band in source pixels (the gold ✦ marks at both ends stay)
BAND = (312, 836, 1132, 882)
SUBTITLES = {"ru": "ЗАБЫТЫЙ ИНСТИТУТ", "uz": "UNUTILGAN INSTITUT"}
# the emblem (eye medallion) used for the icon. The lettering overlaps the bottom of the medallion disc, so the
# icon keeps everything above the eye corners and, below them, only what lies inside the lower eyelid (whole
# sphere, whole lid, the bottom diamond); the disc around it dissolves softly into the icon background.
EMBLEM = (238, 8, 1212, 640)
EYE_CORNERS = ((300, 410), (1145, 410)) # the gold orbs at the eye's corners (source px)
LID_BOTTOM_Y = 618 # outer edge of the lower lid under the sphere
DIAMOND = ((700, 566), (746, 566), (723, 632)) # the gold diamond under the lid
EMBLEM_FADE = 16 # px of soft edge where the disc is cut


def erase_band(im: Image.Image) -> Image.Image:
    """Repaint the subtitle band from the banner rows just above and below it (keeps its texture)."""
    a = np.asarray(im).astype(np.float32)
    x0, y0, x1, y1 = BAND
    above = a[y0 - 9:y0 - 1, x0:x1].mean(axis=0)
    below = a[y1 + 1:y1 + 9, x0:x1].mean(axis=0)
    rng = np.random.default_rng(3)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        row = above * (1 - t) + below * t
        row[:, :3] += rng.normal(0.0, 3.0, (x1 - x0, 1))
        a[y, x0:x1] = row
    # soften the seams
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    band = out.crop((x0, y0 - 2, x1, y1 + 2)).filter(ImageFilter.GaussianBlur(1.2))
    out.paste(band, (x0, y0 - 2))
    return out


def engrave(im: Image.Image, text: str) -> Image.Image:
    """Gold, slightly embossed spaced capitals centred in the band, like the original subtitle."""
    x0, y0, x1, y1 = BAND
    w, h = x1 - x0, y1 - y0
    size = 44
    tracking = 0.30
    font = ImageFont.truetype(FONT, size)

    def width(s: int) -> float:
        f = ImageFont.truetype(FONT, s)
        return sum(f.getlength(c) for c in text) + s * tracking * (len(text) - 1)

    while width(size) > w * 0.96 and size > 20:
        size -= 1
    font = ImageFont.truetype(FONT, size)
    scale = 3
    W, H = w * scale, h * scale
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    big = ImageFont.truetype(FONT, size * scale)
    total = sum(big.getlength(c) for c in text) + size * scale * tracking * (len(text) - 1)
    x = (W - total) / 2
    asc, desc = big.getmetrics()
    y = (H - (asc - desc * 0.2)) / 2 - desc * 0.15
    for c in text:
        d.text((x, y), c, font=big, fill=255)
        x += big.getlength(c) + size * scale * tracking
    mask = mask.resize((w, h), Image.LANCZOS)
    # vertical gold gradient
    grad = np.linspace(0, 1, h)[:, None]
    top = np.array([246, 224, 168], np.float32)
    bot = np.array([176, 128, 58], np.float32)
    col = np.repeat((top * (1 - grad) + bot * grad)[:, None, :], w, axis=1)
    gold = Image.fromarray(col.astype(np.uint8), "RGB").convert("RGBA")
    gold.putalpha(mask)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh_mask = ImageChops.offset(mask, 0, 2).filter(ImageFilter.GaussianBlur(1.0))
    shadow.putalpha(sh_mask.point(lambda v: int(v * 0.85)))
    hi = Image.new("RGBA", (w, h), (255, 244, 214, 0))
    hi_mask = ImageChops.subtract(mask, ImageChops.offset(mask, 0, 1)).point(lambda v: int(v * 0.6))
    hi.putalpha(hi_mask)
    out = im.copy()
    region = out.crop(BAND)
    region = Image.alpha_composite(region, shadow)
    region = Image.alpha_composite(region, gold)
    region = Image.alpha_composite(region, hi)
    out.paste(region, (x0, y0))
    return out


def icon_background(size: int) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.46) ** 2)
    inner = np.array([22, 58, 62], np.float32)
    outer = np.array([5, 12, 14], np.float32)
    t = np.clip(r / 0.72, 0, 1)[..., None]
    rgb = inner * (1 - t) + outer * t
    return Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")


def fit(img: Image.Image, box: int) -> Image.Image:
    k = box / max(img.size)
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)


def emblem_mask(size: tuple[int, int]) -> np.ndarray:
    """Alpha multiplier in source pixels: 1 above the eye corners and inside the lower lid, soft edge below."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    (x0, y0), (x1, _) = EYE_CORNERS
    t = np.clip((xx - x0) / (x1 - x0), 0.0, 1.0)
    lid = y0 + (LID_BOTTOM_Y - y0) * np.sin(np.pi * t) # almond curve through both corners
    lid = np.maximum(lid, 540.0) # the disc and side spikes level with the corners stay
    keep = np.clip((lid - yy) / EMBLEM_FADE + 0.5, 0.0, 1.0)
    d = Image.new("L", (w, h), 0)
    ImageDraw.Draw(d).polygon(DIAMOND, fill=255)
    diamond = np.asarray(d.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255.0
    return np.maximum(keep, diamond)


def emblem_of(src: Image.Image) -> Image.Image:
    alpha = np.asarray(src.getchannel("A")).astype(np.float32) * emblem_mask(src.size)
    masked = src.copy()
    masked.putalpha(Image.fromarray(alpha.astype(np.uint8), "L"))
    emblem = masked.crop(EMBLEM)
    bbox = emblem.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return emblem.crop(bbox)


def monochrome_eye(size: int) -> Image.Image:
    """Themed-icon silhouette: the almond eye, the crystal iris and the door of light (white on clear)."""
    s = size * 4
    img = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(img)
    cx, cy = s / 2, s / 2
    half_w, amp = s * 0.31, s * 0.15

    def almond(k: float) -> list[tuple[float, float]]:
        pts = []
        for i in range(61):
            t = i / 60
            pts.append((cx - half_w * k + 2 * half_w * k * t, cy - amp * k * np.sin(np.pi * t)))
        for i in range(61):
            t = 1 - i / 60
            pts.append((cx - half_w * k + 2 * half_w * k * t, cy + amp * k * np.sin(np.pi * t)))
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


def make_icons(src: Image.Image) -> None:
    emblem = emblem_of(src)
    ui = os.path.join(ROOT, "game/assets/ui")
    bg = icon_background(1024)
    e = fit(emblem, int(1024 * 0.94))
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    gl = Image.new("RGBA", e.size, (90, 230, 255, 0))
    gl.putalpha(e.getchannel("A").filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.35)))
    pos = ((1024 - e.width) // 2, (1024 - e.height) // 2)
    glow.paste(gl, pos, gl)
    icon = Image.alpha_composite(bg, glow)
    icon.alpha_composite(e, pos)
    icon.convert("RGB").save(os.path.join(ui, "icon.png"))
    icon.convert("RGB").resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "docs/store/graphics/icon_512.png"))
    # Android adaptive: the foreground fits the central 66 % safe zone
    fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    ef = fit(emblem, int(432 * 0.64))
    fg.alpha_composite(ef, ((432 - ef.width) // 2, (432 - ef.height) // 2))
    fg.save(os.path.join(ui, "icon_adaptive_fg.png"))
    icon_background(432).convert("RGB").save(os.path.join(ui, "icon_adaptive_bg.png"))
    monochrome_eye(432).save(os.path.join(ui, "icon_monochrome.png"))


def main() -> None:
    src = Image.open(SRC).convert("RGBA")
    src.save(os.path.join(OUT, "logo_en.png"))
    blank = erase_band(src)
    for lang, text in SUBTITLES.items():
        engrave(blank, text).save(os.path.join(OUT, f"logo_{lang}.png"))
    make_icons(src)
    print("logos + icons written")


if __name__ == "__main__":
    main()
