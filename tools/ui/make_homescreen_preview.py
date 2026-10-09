#!/usr/bin/env python3
"""Phone home-screen previews of the app icon (how the icon reads among other apps at real size).

The surrounding apps are generic, unbranded placeholder tiles. Writes:
    docs/previews/logo/home_android.png  (adaptive icon in a circle mask, dark wallpaper)
    docs/previews/logo/home_ios.png      (squircle mask, light wallpaper: the hardest case for a dark icon)
    docs/previews/logo/icon_sizes.png    (the icon at launcher, settings and notification sizes)

    python3 tools/ui/make_homescreen_preview.py
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs/previews/logo")
UI = os.path.join(ROOT, "game/assets/ui")
FONT = os.path.join(ROOT, "game/assets/fonts/NotoSans-Variable.ttf")

W, H = 1080, 2340 # a common 19.5:9 phone, 1:1 pixels
# generic tiles: (label, colour, glyph)
APPS = [("Camera", "#3d4a55", "ring"), ("Clock", "#20262c", "clock"), ("Notes", "#e9c55a", "lines"),
        ("Music", "#c8465a", "note"), ("Maps", "#4f9a6b", "pin"), ("Mail", "#3c7fd1", "env"),
        ("Photos", "#f0f0f0", "petals"), ("Weather", "#4aa3e0", "sun"), ("Files", "#5c6bc0", "folder"),
        ("Calendar", "#ffffff", "cal"), ("Calculator", "#2b2b2b", "grid"), ("Settings", "#8a9099", "gear"),
        ("Phone", "#47b36b", "ring"), ("Messages", "#48c25e", "bubble"), ("Browser", "#e8eef4", "globe")]


def font(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception: # noqa: BLE001 - older FreeType builds without variable-font axes
        pass
    return f


def wallpaper(dark: bool) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    if dark:
        a, b, c = np.array([18, 22, 40.]), np.array([52, 38, 70.]), np.array([12, 48, 58.])
    else:
        a, b, c = np.array([214, 226, 240.]), np.array([246, 214, 200.]), np.array([196, 222, 214.])
    t1 = np.clip(1 - np.hypot(u - 0.2, v - 0.25) * 1.3, 0, 1)[..., None]
    t2 = np.clip(1 - np.hypot(u - 0.85, v - 0.75) * 1.2, 0, 1)[..., None]
    rgb = a * (1 - t1) * (1 - t2) + b * t1 + c * t2
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def squircle_mask(size: int, ios: bool) -> Image.Image:
    s = size * 4
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    x, y = (xx + 0.5) / s * 2 - 1, (yy + 0.5) / s * 2 - 1
    if ios:
        inside = np.abs(x) ** 5 + np.abs(y) ** 5 <= 1.0
    else:
        inside = x * x + y * y <= 1.0
    m = Image.fromarray((inside * 255).astype(np.uint8), "L")
    return m.resize((size, size), Image.LANCZOS)


def glyph(d: ImageDraw.ImageDraw, kind: str, box: tuple[float, float, float, float], col: str) -> None:
    x0, y0, x1, y1 = box
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2
    w = max(3, int(r * 0.16))
    if kind == "ring":
        d.ellipse((cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55), outline=col, width=w)
    elif kind == "clock":
        d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=col, width=w)
        d.line((cx, cy, cx, cy - r * 0.4), fill=col, width=w)
        d.line((cx, cy, cx + r * 0.3, cy), fill=col, width=w)
    elif kind == "lines":
        for i in range(3):
            yy = cy - r * 0.35 + i * r * 0.35
            d.line((cx - r * 0.45, yy, cx + r * 0.45, yy), fill=col, width=w)
    elif kind == "note":
        d.ellipse((cx - r * 0.45, cy + r * 0.1, cx - r * 0.05, cy + r * 0.45), fill=col)
        d.line((cx - r * 0.07, cy + r * 0.3, cx - r * 0.07, cy - r * 0.45), fill=col, width=w)
        d.line((cx - r * 0.07, cy - r * 0.45, cx + r * 0.4, cy - r * 0.3), fill=col, width=w)
    elif kind == "pin":
        d.ellipse((cx - r * 0.35, cy - r * 0.55, cx + r * 0.35, cy + r * 0.15), fill=col)
        d.polygon([(cx - r * 0.3, cy - r * 0.05), (cx + r * 0.3, cy - r * 0.05), (cx, cy + r * 0.55)], fill=col)
    elif kind == "env":
        d.rectangle((cx - r * 0.55, cy - r * 0.35, cx + r * 0.55, cy + r * 0.35), outline=col, width=w)
        d.line((cx - r * 0.55, cy - r * 0.35, cx, cy + r * 0.05, cx + r * 0.55, cy - r * 0.35), fill=col, width=w)
    elif kind == "petals":
        for i, c in enumerate(["#f2b33d", "#e0533d", "#3d8be0", "#4cb35f"]):
            a = i * np.pi / 2
            ox, oy = np.cos(a) * r * 0.25, np.sin(a) * r * 0.25
            d.ellipse((cx + ox - r * 0.28, cy + oy - r * 0.28, cx + ox + r * 0.28, cy + oy + r * 0.28), fill=c)
    elif kind == "sun":
        d.ellipse((cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32), fill="#ffd54a")
    elif kind == "folder":
        d.rounded_rectangle((cx - r * 0.55, cy - r * 0.3, cx + r * 0.55, cy + r * 0.4), radius=r * 0.08, fill=col)
        d.rectangle((cx - r * 0.55, cy - r * 0.42, cx - r * 0.1, cy - r * 0.3), fill=col)
    elif kind == "cal":
        d.rectangle((cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy - r * 0.25), fill="#e0533d")
        d.text((cx, cy + r * 0.12), "9", fill="#222", anchor="mm", font=font(int(r * 0.7), 700))
    elif kind == "grid":
        for i in range(3):
            for j in range(3):
                gx, gy = cx - r * 0.4 + i * r * 0.4, cy - r * 0.4 + j * r * 0.4
                d.ellipse((gx - r * 0.12, gy - r * 0.12, gx + r * 0.12, gy + r * 0.12), fill=col)
    elif kind == "gear":
        for i in range(8):
            a = i * np.pi / 4
            d.line((cx, cy, cx + np.cos(a) * r * 0.55, cy + np.sin(a) * r * 0.55), fill=col, width=int(w * 1.6))
        d.ellipse((cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4), fill=col)
        d.ellipse((cx - r * 0.15, cy - r * 0.15, cx + r * 0.15, cy + r * 0.15), fill="#8a9099")
    elif kind == "bubble":
        d.ellipse((cx - r * 0.55, cy - r * 0.42, cx + r * 0.55, cy + r * 0.32), fill=col)
        d.polygon([(cx - r * 0.35, cy + r * 0.2), (cx - r * 0.5, cy + r * 0.5), (cx - r * 0.1, cy + r * 0.28)], fill=col)
    elif kind == "globe":
        d.ellipse((cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55), outline="#3c7fd1", width=w)
        d.ellipse((cx - r * 0.22, cy - r * 0.55, cx + r * 0.22, cy + r * 0.55), outline="#3c7fd1", width=w)
        d.line((cx - r * 0.55, cy, cx + r * 0.55, cy), fill="#3c7fd1", width=w)


def generic_tile(size: int, colour: str, kind: str, ios: bool) -> Image.Image:
    tile = Image.new("RGBA", (size, size), colour)
    d = ImageDraw.Draw(tile)
    light = sum(int(colour[i:i + 2], 16) for i in (1, 3, 5)) > 560
    glyph(d, kind, (size * 0.1, size * 0.1, size * 0.9, size * 0.9), "#333333" if light else "#ffffff")
    tile.putalpha(squircle_mask(size, ios))
    return tile


def our_icon(size: int, ios: bool) -> Image.Image:
    if ios:
        ic = Image.open(os.path.join(UI, "icon.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    else:
        # adaptive: 108 dp layers, the launcher shows the central 72 dp (2/3)
        bg = Image.open(os.path.join(UI, "icon_adaptive_bg.png")).convert("RGBA")
        fg = Image.open(os.path.join(UI, "icon_adaptive_fg.png")).convert("RGBA")
        full = Image.alpha_composite(bg, fg)
        c = full.width / 6
        ic = full.crop((round(c), round(c), round(full.width - c), round(full.width - c))).resize((size, size), Image.LANCZOS)
    ic.putalpha(squircle_mask(size, ios))
    return ic


def shadowed(base: Image.Image, tile: Image.Image, pos: tuple[int, int]) -> None:
    sh = Image.new("RGBA", (tile.width + 40, tile.height + 40), (0, 0, 0, 0))
    a = tile.getchannel("A").point(lambda v: int(v * 0.35))
    sh.paste(Image.new("RGBA", tile.size, (0, 0, 0, 255)), (20, 26), a)
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    base.alpha_composite(sh, (pos[0] - 20, pos[1] - 20))
    base.alpha_composite(tile, pos)


def status_bar(d: ImageDraw.ImageDraw, col: str) -> None:
    d.text((70, 60), "9:41", fill=col, font=font(42, 600), anchor="lm")
    for i in range(4):
        d.rectangle((W - 250 + i * 16, 74 - i * 7, W - 240 + i * 16, 82), fill=col)
    d.rounded_rectangle((W - 160, 46, W - 80, 80), radius=9, outline=col, width=3)
    d.rectangle((W - 154, 52, W - 104, 74), fill=col)


def home(ios: bool) -> Image.Image:
    dark = not ios
    img = wallpaper(dark)
    d = ImageDraw.Draw(img)
    fg = "#ffffff" if dark else "#1b1b1f"
    status_bar(d, fg)
    if not ios:
        d.text((W / 2, 300), "Friday, 9 October", fill=fg, font=font(46, 500), anchor="mm")
    size = 196 if ios else 168
    cols = 4
    gap_x = (W - 2 * 70 - cols * size) / (cols - 1)
    top = 260 if ios else 470
    labels = font(34 if ios else 32, 500)
    slots = APPS[:]
    slots.insert(6, ("Mystery Room", "", "ours"))
    for i, (label, colour, kind) in enumerate(slots[:16]):
        r, c = divmod(i, cols)
        x = int(70 + c * (size + gap_x))
        y = int(top + r * (size + 120))
        tile = our_icon(size, ios) if kind == "ours" else generic_tile(size, colour, kind, ios)
        shadowed(img, tile, (x, y))
        name = label if len(label) <= 13 else label[:12] + "…"
        d.text((x + size / 2, y + size + 34), name, fill=fg, font=labels, anchor="mm")
    # dock
    dock_y = H - 360
    if ios:
        d.rounded_rectangle((40, dock_y - 30, W - 40, dock_y + size + 30), radius=70, fill=(255, 255, 255, 110))
    for i, (label, colour, kind) in enumerate([APPS[12], APPS[13], APPS[14], APPS[3]]):
        x = int(70 + i * (size + gap_x))
        shadowed(img, generic_tile(size, colour, kind, ios), (x, dock_y))
    d.rounded_rectangle((W / 2 - 150, H - 40, W / 2 + 150, H - 30), radius=5, fill=fg)
    return img


def phone_frame(screen: Image.Image) -> Image.Image:
    pad = 46
    out = Image.new("RGBA", (W + pad * 2 + 40, H + pad * 2 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((20, 20, W + pad * 2 + 20, H + pad * 2 + 20), radius=150, fill="#0d0d0f", outline="#3a3a40", width=6)
    m = Image.new("L", screen.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, W, H), radius=110, fill=255)
    out.paste(screen, (20 + pad, 20 + pad), m)
    d.ellipse((out.width / 2 - 22, 20 + pad + 30, out.width / 2 + 22, 20 + pad + 74), fill="#050506")
    return out


def sizes_sheet() -> Image.Image:
    img = Image.new("RGBA", (1600, 640), "#f3f4f6")
    d = ImageDraw.Draw(img)
    x = 60
    for s, label in [(192, "launcher 192"), (144, "144"), (96, "96"), (48, "48"), (29, "settings 29")]:
        for j, ios in enumerate([False, True]):
            ic = our_icon(s, ios)
            img.alpha_composite(ic, (x, 110 + j * 230 + (192 - s) // 2))
        d.text((x + s / 2, 590), label, fill="#333", font=font(26), anchor="mm")
        x += s + 90
    mono = Image.open(os.path.join(UI, "icon_monochrome.png")).convert("RGBA").resize((160, 160), Image.LANCZOS)
    tint = Image.new("RGBA", mono.size, (40, 52, 70, 255))
    tint.putalpha(mono.getchannel("A"))
    disc = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    ImageDraw.Draw(disc).ellipse((0, 0, 191, 191), fill="#d7e3f4")
    disc.alpha_composite(tint, (16, 16))
    img.alpha_composite(disc, (x, 120))
    d.text((x + 96, 590), "themed (A13+)", fill="#333", font=font(26), anchor="mm")
    d.text((60, 50), "Android (circle)  /  iOS (squircle)", fill="#111", font=font(34, 600))
    return img


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    phone_frame(home(False)).save(os.path.join(OUT, "home_android.png"))
    phone_frame(home(True)).save(os.path.join(OUT, "home_ios.png"))
    sizes_sheet().convert("RGB").save(os.path.join(OUT, "icon_sizes.png"))
    print("home-screen previews ->", OUT)


if __name__ == "__main__":
    main()
