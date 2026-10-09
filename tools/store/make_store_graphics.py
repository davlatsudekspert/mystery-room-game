#!/usr/bin/env python3
"""Store assets for Google Play and the App Store from real in-game renders and the owner's logo.

The renders come from the QA scenes, run through tools/qa_run.sh (one window size per store shape), e.g.
    tools/qa_run.sh -- --resolution 2560x1440 res://qa/playthrough.tscn -- --out=<R>/ch1_169_en --seed=4242 --lang=en
    tools/qa_run.sh -- --resolution 2868x1320 res://qa/playthrough_ch2.tscn -- --out=<R>/ch2_iph_en --seed=777
Folder names: <R>/<chapter>_<shape>_<lang>, chapter ch1|ch2, shape 169 (16:9, 2560x1440) | iph (2868x1320) |
ipad (2752x2064), lang en|ru. A store size is only written when all its renders exist in that language.

    python3 tools/store/make_store_graphics.py --renders=<R>     # writes docs/store/**
    python3 tools/store/make_store_graphics.py --check-text      # character / byte counts of the listing texts
    python3 tools/store/make_store_graphics.py --table           # file / pixel / size table for README.md

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

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "store")
FONT = os.path.join(ROOT, "game", "assets", "fonts", "NotoSans-Variable.ttf")

LOCALES = {"en": {"play": "en-US", "apple": "en-US"}, "ru": {"play": "ru-RU", "apple": "ru"}}

# Store order: Chapter 1 first (free and playable in every build), then Chapter 2 (locked in store builds while
# payments are off; see README). (output name, chapter, QA shot name)
SHOTS: list[tuple[str, str, str]] = [
    ("01_laboratory", "ch1", "lab_powered"),
    ("02_projector_beam", "ch1", "projector_beam_on"),
    ("03_radio", "ch1", "radio_tuned_41m"),
    ("04_uv_ink", "ch1", "uv_desk_mark"),
    ("05_shadow_sculpture", "ch1", "shadow_misaligned"), # unsolved: the aligned emblem is lore, the same in every game
    ("06_archive_hall", "ch2", "hall_start"),
    ("07_film_projection", "ch2", "film_frame"),
    ("08_echoes", "ch2", "echo_stacks"),
]

# App Store sizes (landscape) and the render shape each one is made from. 6.5" and 6.3" are downscaled from the
# 6.9" render (same ~2.17:1 shape, so the HUD layout is identical), cropping at most a few pixels.
APPLE_SIZES = [("iphone_6.9", (2868, 1320), "iph"), ("iphone_6.5", (2688, 1242), "iph"),
    ("iphone_6.3", (2622, 1206), "iph"), ("ipad_13", (2752, 2064), "ipad")]
PLAY_SIZE = (2560, 1440)
JPEG = {"quality": 85, "optimize": True, "subsampling": "4:2:0"}


# ====================================================================== helpers
def find_render(renders: str, chapter: str, shape: str, lang: str, shot: str, strict: bool = False) -> str:
    """The newest QA shot named `shot` in <renders>/<chapter>_<shape>_<lang>/ (EN as a fallback unless strict)."""
    for lg in (lang,) if strict else (lang, "en"):
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
    """Each store size is written only when every shot has a render of that shape in that language; a missing set
    is reported and skipped, never filled in from another shape or language."""
    targets = [("google_play", "screenshots", PLAY_SIZE, "169", "play")]
    targets += [("app_store", os.path.join("screenshots", sid), size, shape, "apple") for sid, size, shape in APPLE_SIZES]
    for lang in langs:
        for store, sub, size, shape, key in targets:
            try:
                srcs = [find_render(renders, chapter, shape, lang, shot, strict=True) for _n, chapter, shot in SHOTS]
            except FileNotFoundError as e:
                print("skip %s %s %s: %s" % (store, sub, lang, e))
                continue
            for (name, _c, _s), src in zip(SHOTS, srcs):
                im = Image.open(src).convert("RGB")
                save_jpg(cover(im, size), os.path.join(OUT, store, sub, LOCALES[lang][key], name + ".jpg"))
            print("screenshots: %s %s %s" % (store, sub, lang))


# ====================================================================== Play icon + feature graphic
def icon() -> None:
    # Play asks for a 32-bit PNG (with alpha); the icon itself is opaque
    im = Image.open(os.path.join(ROOT, "game", "assets", "ui", "icon.png")).convert("RGBA")
    path = os.path.join(OUT, "google_play", "icon_512.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((512, 512), Image.LANCZOS).save(path, optimize=True)


# Feature graphic background: a view_probe frame of the lit lab with the Lumen beam on (Chapter 1, so the graphic
# shows only content every store build offers), rendered at 2868x1320:
#   tools/qa_run.sh -- --resolution 2868x1320 res://qa/view_probe.tscn -- --out=<R>/fg_probe --from=p12 \
#       --seed=4242 "--cam=beamwide:0.6,1.7,-1.6:-0.6,1.15,1.6:55"
# The crop box (x0, y0, width) keeps clear of the HUD: the ceiling lamp ends at y≈110, the hint plate starts at y≈1058.
FEATURE_SRC = os.path.join("fg_probe", "cam_beamwide.png")
FEATURE_BOX = (600, 112, 1921)
FEATURE_LOGO_H = 360
FEATURE_LOGO_CX = 440


def feature(renders: str, lang: str) -> None:
    """1024x500, no alpha: a real game frame, the localized logo left of centre, the beam and projector beside it."""
    src = Image.open(os.path.join(renders, FEATURE_SRC)).convert("RGB")
    x0, y0, w = FEATURE_BOX
    h = w * 500 / 1024
    bg = src.crop((x0, y0, x0 + w, round(y0 + h))).resize((1024, 500), Image.LANCZOS)
    logo_file = {"en": "logo_en.png", "ru": "logo_ru.png"}[lang]
    logo = Image.open(os.path.join(ROOT, "game", "assets", "ui", "logo", logo_file)).convert("RGBA")
    k = FEATURE_LOGO_H / logo.height
    logo = logo.resize((round(logo.width * k), FEATURE_LOGO_H), Image.LANCZOS)
    x = round(FEATURE_LOGO_CX - logo.width / 2)
    y = (500 - logo.height) // 2
    # a soft dark halo behind the logo only, so the gold lettering reads on the lit wall
    shade = Image.new("L", (1024, 500), 0)
    ImageDraw.Draw(shade).ellipse((x - 20, y, x + logo.width + 20, y + logo.height), fill=140)
    shade = shade.filter(ImageFilter.GaussianBlur(50))
    bg = Image.composite(Image.new("RGB", bg.size, (14, 18, 22)), bg, shade)
    out = bg.convert("RGBA")
    out.alpha_composite(logo, (x, y))
    path = os.path.join(OUT, "google_play", "feature_graphic_%s.jpg" % LOCALES[lang]["play"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.convert("RGB").save(path, "JPEG", quality=93, optimize=True, subsampling="4:4:4")


# ====================================================================== contact sheet
def contact_sheet() -> None:
    font = ImageFont.truetype(FONT, 22)
    font_b = ImageFont.truetype(FONT, 30)
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
    d.text((pad + 640, pad + 8), "Orange frame = Chapter 2 (06-08): upload only once Chapter 2 can be unlocked in the store build",
        font=font, fill=(240, 150, 60))
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
            if os.path.basename(f)[:3] in ("06_", "07_", "08_"):
                d.rectangle((x - 3, y - 3, x + t.width + 2, y + th + 2), outline=(240, 150, 60), width=3)
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


# ====================================================================== file table for README.md
def table() -> None:
    """Markdown rows: file, pixels, mode, size, from the files on disk."""
    for f in sorted(glob.glob(os.path.join(OUT, "**", "*"), recursive=True)):
        if os.path.isdir(f):
            continue
        rel = os.path.relpath(f, OUT)
        kb = os.path.getsize(f) / 1024
        if f.endswith((".png", ".jpg")):
            im = Image.open(f)
            print("| `%s` | %dx%d %s | %.0f KB |" % (rel, im.width, im.height, im.mode, kb))
        else:
            print("| `%s` | text | %.1f KB |" % (rel, kb))


# ====================================================================== main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", help="folder with <chapter>_<shape>_<lang>/ render runs")
    ap.add_argument("--langs", default="en,ru")
    ap.add_argument("--check-text", action="store_true")
    ap.add_argument("--table", action="store_true", help="print the README file table")
    a = ap.parse_args()
    if a.check_text:
        return 0 if check_text() else 1
    if a.table:
        table()
        return 0
    if not a.renders:
        ap.error("--renders is required")
    langs = a.langs.split(",")
    icon()
    for lang in langs:
        feature(a.renders, lang)
    screenshots(a.renders, langs)
    contact_sheet()
    print("written to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
