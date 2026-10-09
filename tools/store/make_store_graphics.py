#!/usr/bin/env python3
"""Store graphics for Google Play / App Store from the game's own icon and real in-game renders.

Writes docs/store/graphics/:
    icon_512.png            512×512 32-bit PNG (Play app icon)
    feature_1024x500.png    1024×500 24-bit PNG (Play feature graphic)
    screenshot_<n>.png      real gameplay screenshots (from docs/previews/playthrough)

    python3 tools/store/make_store_graphics.py
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "store", "graphics")
FONT_TITLE = os.path.join(ROOT, "game", "assets", "fonts", "CormorantGaramond-Bold.ttf")
FONT_SUB = os.path.join(ROOT, "game", "assets", "fonts", "CormorantGaramond-SemiBold.ttf")
SHOTS = ["17_lab_powered", "30_projector_beam_on", "21_bookcase_open", "26_shadow_emblem_recorded",
         "19_radio_tuned_41m", "32_finale_echo_1979", "14_safe_open", "23_darkroom"]


def icon() -> None:
    im = Image.open(os.path.join(ROOT, "game", "assets", "ui", "icon.png")).convert("RGBA")
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "icon_512.png"))


def feature() -> None:
    src = Image.open(os.path.join(ROOT, "docs", "previews", "player_view_north_powered.png")).convert("RGB")
    w, h = src.size
    # fill 1024×500 (cover), keep the lit centre of the room
    scale = max(1024 / w, 500 / h)
    bg = src.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    x0 = (bg.width - 1024) // 2
    y0 = (bg.height - 500) // 2
    bg = bg.crop((x0, y0, x0 + 1024, y0 + 500))
    bg = ImageEnhance.Brightness(bg).enhance(0.62)
    # left-to-right darkening so the title reads
    shade = Image.new("L", (1024, 500))
    sd = ImageDraw.Draw(shade)
    for x in range(1024):
        sd.line([(x, 0), (x, 500)], fill=int(200 * max(0.0, 1.0 - x / 760.0)))
    bg = Image.composite(Image.new("RGB", (1024, 500), (8, 10, 12)), bg, shade)
    d = ImageDraw.Draw(bg)
    brass = (227, 194, 122)
    cream = (232, 223, 200)
    ft = ImageFont.truetype(FONT_TITLE, 92)
    fs = ImageFont.truetype(FONT_SUB, 46)
    fl = ImageFont.truetype(FONT_SUB, 28)
    glow = Image.new("RGBA", (1024, 500), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((64, 150), "MYSTERY ROOM", font=ft, fill=(255, 200, 120, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    bg.paste(glow, (0, 0), glow)
    d.text((64, 150), "MYSTERY ROOM", font=ft, fill=brass)
    d.text((68, 262), "The Forgotten Institute", font=fs, fill=cream)
    d.line([(68, 330), (460, 330)], fill=(176, 141, 87), width=2)
    d.text((68, 344), "Light remembers.", font=fl, fill=(200, 190, 170))
    bg.save(os.path.join(OUT, "feature_1024x500.png"))


def screenshots() -> None:
    for i, name in enumerate(SHOTS, 1):
        Image.open(os.path.join(ROOT, "docs", "previews", "playthrough", name + ".jpg")).convert("RGB").save(
            os.path.join(OUT, "screenshot_%d.png" % i))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon()
    feature()
    screenshots()
    print("written to", OUT)
