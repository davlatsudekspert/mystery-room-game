#!/usr/bin/env python3
"""Store assets for Google Play and the App Store from real in-game renders and the owner's logo.

The renders come from the QA scenes, run through tools/qa_run.sh (one window size per store shape), e.g.
    tools/qa_run.sh -- --resolution 2560x1440 res://qa/playthrough.tscn -- --out=<R>/ch1_169_en --seed=4242 --lang=en
    tools/qa_run.sh -- --resolution 2868x1320 res://qa/playthrough_ch2.tscn -- --out=<R>/ch2_iph_en --seed=777
Folder names: <R>/<chapter>_<shape>_<lang>, chapter ch1|ch2, shape 169 (16:9, 2560x1440) | iph (2868x1320) |
ipad (2752x2064), lang en|ru. A missing language falls back to en.

    python3 tools/store/make_store_graphics.py --renders=<R>     # writes docs/store/**
    python3 tools/store/make_store_graphics.py --check-text      # character / byte counts of the listing texts

Writes (see docs/store/README.md):
    google_play/icon_512.png                         512x512 32-bit PNG
    google_play/feature_graphic_<locale>.jpg         1024x500, no alpha
    google_play/screenshots/<locale>/NN_<name>.jpg   2560x1440 (16:9; phones and 7"/10" tablets)
    app_store/screenshots/<size>/<locale>/NN_<name>.jpg
        iphone_6.9 2868x1320 | iphone_6.5 2688x1242 | iphone_6.3 2622x1206 | ipad_13 2752x2064
    store_assets_sheet.jpg                           contact sheet of everything above
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "store")
FONT = os.path.join(ROOT, "game", "assets", "fonts", "NotoSans-Variable.ttf")

LOCALES = {"en": {"play": "en-US", "apple": "en-US"}, "ru": {"play": "ru-RU", "apple": "ru"}}

# Store order: Chapter 1 first (free and playable in every build), then Chapter 2 (locked in store builds while
# payments are off; see README). (output name, chapter, QA shot name)
SHOTS: list[tuple[str, str, str]] = [
    ("01_laboratory", "ch1", "lab_powered"),
    ("02_projector_beam", "ch1", "beam_first_mirror"),
    ("03_radio", "ch1", "radio_tuned_41m"),
    ("04_darkroom", "ch1", "darkroom"),
    ("05_shadow_lock", "ch1", "shadow_emblem_recorded"),
    ("06_archive_hall", "ch2", "hall_start"),
    ("07_film_projection", "ch2", "film_frame"),
    ("08_archive_vault", "ch2", "vault_closed"),
]

# App Store sizes (landscape) and the render shape each one is made from. 6.5" and 6.3" are downscaled from the
# 6.9" render (same ~2.17:1 shape, so the HUD layout is identical), cropping at most a few pixels.
APPLE_SIZES = [("iphone_6.9", (2868, 1320), "iph"), ("iphone_6.5", (2688, 1242), "iph"),
    ("iphone_6.3", (2622, 1206), "iph"), ("ipad_13", (2752, 2064), "ipad")]
PLAY_SIZE = (2560, 1440)
JPEG = {"quality": 90, "optimize": True, "subsampling": "4:2:0"}


# ====================================================================== helpers
def find_render(renders: str, chapter: str, shape: str, lang: str, shot: str) -> str:
    for lg in (lang, "en"):
        hits = sorted(glob.glob(os.path.join(renders, "%s_%s_%s" % (chapter, shape, lg), "*_%s.png" % shot)))
        if hits:
            return hits[-1]
    raise FileNotFoundError("no render for %s %s %s %s in %s" % (chapter, shape, lang, shot, renders))


def cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale to cover `size`, then centre-crop (no letterbox, no distortion)."""
    w, h = size
    k = max(w / im.width, h / im.height)
    if abs(k - 1.0) > 1e-6:
        im = im.resize((max(w, round(im.width * k)), max(h, round(im.height * k))), Image.LANCZOS)
    x0 = (im.width - w) // 2
    y0 = (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def save_jpg(im: Image.Image, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.convert("RGB").save(path, "JPEG", **JPEG)


# ====================================================================== screenshots
def screenshots(renders: str, langs: list[str]) -> None:
    for lang in langs:
        loc = LOCALES[lang]
        for name, chapter, shot in SHOTS:
            src = Image.open(find_render(renders, chapter, "169", lang, shot)).convert("RGB")
            save_jpg(cover(src, PLAY_SIZE), os.path.join(OUT, "google_play", "screenshots", loc["play"], name + ".jpg"))
            for size_id, size, shape in APPLE_SIZES:
                src = Image.open(find_render(renders, chapter, shape, lang, shot)).convert("RGB")
                save_jpg(cover(src, size), os.path.join(OUT, "app_store", "screenshots", size_id, loc["apple"], name + ".jpg"))
        print("screenshots:", lang)


# ====================================================================== Play icon + feature graphic
def icon() -> None:
    # Play asks for a 32-bit PNG (with alpha); the icon itself is opaque
    im = Image.open(os.path.join(ROOT, "game", "assets", "ui", "icon.png")).convert("RGBA")
    path = os.path.join(OUT, "google_play", "icon_512.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((512, 512), Image.LANCZOS).save(path, optimize=True)


def feature(renders: str, lang: str, bg_shot: tuple[str, str], crop: tuple[float, float, float]) -> None:
    """1024x500: a real game frame (the HUD-free band of a 2868x1320 render), the logo in the safe centre.

    crop = (centre x, centre y, width) of the background window as fractions of the render."""
    src = Image.open(find_render(renders, bg_shot[0], "iph", lang, bg_shot[1])).convert("RGB")
    cw = crop[2] * src.width
    ch = cw * 500 / 1024
    cx, cy = crop[0] * src.width, crop[1] * src.height
    box = (round(cx - cw / 2), round(cy - ch / 2), round(cx + cw / 2), round(cy + ch / 2))
    bg = src.crop(box).resize((1024, 500), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.92)
    # a soft dark vignette behind the logo only, so the gold lettering reads on any frame
    shade = Image.new("L", (1024, 500), 0)
    ImageDraw.Draw(shade).ellipse((262, 20, 762, 480), fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(70))
    bg = Image.composite(Image.new("RGB", bg.size, (14, 18, 22)), bg, shade)
    logo_file = {"en": "logo_en.png", "ru": "logo_ru.png"}[lang]
    logo = Image.open(os.path.join(ROOT, "game", "assets", "ui", "logo", logo_file)).convert("RGBA")
    k = 430 / logo.height
    logo = logo.resize((round(logo.width * k), 430), Image.LANCZOS)
    out = bg.convert("RGBA")
    out.alpha_composite(logo, ((1024 - logo.width) // 2, (500 - logo.height) // 2))
    path = os.path.join(OUT, "google_play", "feature_graphic_%s.jpg" % LOCALES[lang]["play"])
    out.convert("RGB").save(path, "JPEG", quality=93, optimize=True, subsampling="4:4:4")


# ====================================================================== contact sheet
def contact_sheet() -> None:
    font = ImageFont.truetype(FONT, 22)
    font_b = ImageFont.truetype(FONT, 30)
    font_b.set_variation_by_axes([700, 100]) if hasattr(font_b, "set_variation_by_axes") else None
    rows: list[tuple[str, list[str]]] = []
    gp = os.path.join(OUT, "google_play")
    rows.append(("Google Play: icon 512, feature graphic 1024x500 (EN, RU)",
        [os.path.join(gp, "icon_512.png")] + sorted(glob.glob(os.path.join(gp, "feature_graphic_*.jpg")))))
    for loc in sorted(os.listdir(os.path.join(gp, "screenshots"))):
        rows.append(("Google Play phone + 7\"/10\" tablet, %s, 2560x1440" % loc,
            sorted(glob.glob(os.path.join(gp, "screenshots", loc, "*.jpg")))))
    for size_id, size, _shape in APPLE_SIZES:
        base = os.path.join(OUT, "app_store", "screenshots", size_id)
        if not os.path.isdir(base):
            continue
        for loc in sorted(os.listdir(base)):
            rows.append(("App Store %s, %s, %dx%d" % (size_id.replace("_", " "), loc, size[0], size[1]),
                sorted(glob.glob(os.path.join(base, loc, "*.jpg")))))
    th = 150 # thumbnail height
    pad = 10
    label_h = 40
    width = 2 * pad + 8 * (round(th * 2868 / 1320) + pad)
    height = pad + sum(label_h + th + pad for _ in rows) + 60
    sheet = Image.new("RGB", (width, height), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    d.text((pad, pad), "MYSTERY ROOM: store assets (docs/store/)", font=font_b, fill=(232, 205, 140))
    y = pad + 50
    for title, files in rows:
        d.text((pad, y), title, font=font, fill=(220, 220, 220))
        y += label_h
        x = pad
        for f in files:
            im = Image.open(f).convert("RGB")
            t = im.resize((round(im.width * th / im.height), th), Image.LANCZOS)
            if x + t.width > width - pad:
                break
            sheet.paste(t, (x, y))
            x += t.width + pad
        y += th + pad
    sheet = sheet.crop((0, 0, width, y + pad))
    sheet.save(os.path.join(OUT, "store_assets_sheet.jpg"), "JPEG", quality=85, optimize=True)


# ====================================================================== listing text check
LIMIT = re.compile(r"\((?:(\d[\d,]*) / )?(?:≤ )?(\d[\d, ]*)( bytes)?\)\s*$")


def check_text() -> bool:
    """Every ```text block under a heading like '### Short description (65 / 80)' or '(≤ 4,000)' or
    '(96 / 100 bytes)' is measured; the stated count must match and stay within the limit."""
    ok = True
    for md in sorted(glob.glob(os.path.join(OUT, "**", "*.md"), recursive=True)):
        lines = open(md, encoding="utf-8").read().split("\n")
        head = ""
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("### "):
                head = ln[4:]
            elif ln.strip() == "```text" and head:
                j = i + 1
                while lines[j].strip() != "```":
                    j += 1
                body = "\n".join(lines[i + 1:j])
                m = LIMIT.search(head)
                if m:
                    stated = int(m.group(1).replace(",", "")) if m.group(1) else None
                    limit = int(m.group(2).replace(",", "").replace(" ", ""))
                    use_bytes = bool(m.group(3))
                    n = len(body.encode("utf-8")) if use_bytes else len(body)
                    bad = n > limit or (stated is not None and stated != n)
                    if use_bytes and any(len(k) <= 2 for k in body.split(",")):
                        bad = True
                    ok = ok and not bad
                    print("%s %-55s %5d %s (limit %d)%s" % ("✗" if bad else "✓", os.path.relpath(md, OUT) + ": " + head[:40],
                        n, "bytes" if use_bytes else "chars", limit, "" if stated is None or stated == n else "  stated %d" % stated))
                head = ""
                i = j
            i += 1
    return ok


# ====================================================================== main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", help="folder with <chapter>_<shape>_<lang>/ render runs")
    ap.add_argument("--langs", default="en,ru")
    ap.add_argument("--check-text", action="store_true")
    a = ap.parse_args()
    if a.check_text:
        return 0 if check_text() else 1
    if not a.renders:
        ap.error("--renders is required")
    langs = a.langs.split(",")
    icon()
    for lang in langs:
        feature(a.renders, lang, ("ch1", "beam_first_mirror"), (0.5, 0.42, 0.78))
    screenshots(a.renders, langs)
    contact_sheet()
    print("written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
