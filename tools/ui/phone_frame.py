#!/usr/bin/env python3
"""Put real in-game screenshots into a landscape phone frame (for previews: how a scene reads on a phone).

The frame is drawn here (no third-party art): a 19.5:9 body with a punch-hole camera and rounded screen corners.
The screenshot is letterboxed into the screen at its own aspect ratio, never stretched.

    python3 tools/ui/phone_frame.py <screenshot.png> [...] --out <dir>
"""
from __future__ import annotations

import argparse
import os

from PIL import Image, ImageDraw, ImageFilter

SCREEN_W, SCREEN_H = 2340, 1080 # a common 19.5:9 phone in landscape
BEZEL = 34
RADIUS = 120


def frame(shot: Image.Image) -> Image.Image:
    shot = shot.convert("RGB")
    k = min(SCREEN_W / shot.width, SCREEN_H / shot.height)
    img = shot.resize((round(shot.width * k), round(shot.height * k)), Image.LANCZOS)
    screen = Image.new("RGB", (SCREEN_W, SCREEN_H), "black")
    screen.paste(img, ((SCREEN_W - img.width) // 2, (SCREEN_H - img.height) // 2))
    W, H = SCREEN_W + 2 * BEZEL, SCREEN_H + 2 * BEZEL
    pad = 60
    out = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("L", out.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((pad + 10, pad + 24, pad + W + 10, pad + H + 24), radius=RADIUS + BEZEL, fill=150)
    out.putalpha(shadow.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((pad, pad, pad + W, pad + H), radius=RADIUS + BEZEL, fill="#101013", outline="#3b3b42", width=5)
    mask = Image.new("L", screen.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SCREEN_W - 1, SCREEN_H - 1), radius=RADIUS, fill=255)
    out.paste(screen, (pad + BEZEL, pad + BEZEL), mask)
    cx, cy = pad + BEZEL + 46, pad + H // 2 # punch-hole on the left edge in landscape
    d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill="#050506")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for p in a.shots:
        name = os.path.splitext(os.path.basename(p))[0] + "_phone.png"
        f = frame(Image.open(p))
        f.thumbnail((1600, 1600))
        f.save(os.path.join(a.out, name))
        print(os.path.join(a.out, name))


if __name__ == "__main__":
    main()
