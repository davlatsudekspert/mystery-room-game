#!/usr/bin/env python3
"""Render the app icon set from tools/ui/icon.svg with Inkscape.

game/assets/ui/
  icon.png                  1024 px full icon (iOS, desktop, legacy Android launcher)
  icon_adaptive_fg.png      432 px Android adaptive foreground: emblem only, transparent, scaled into the
                            66 dp safe circle of the 108 dp layer (the full icon would be clipped by round masks)
  icon_adaptive_bg.png      432 px Android adaptive background: the dark radial gradient only
  icon_monochrome.png       432 px Android 13+ themed icon: emblem silhouette, white on transparent
    python3 tools/ui/make_icons.py
"""
import os
import re
import subprocess
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "tools", "ui", "icon.svg")
OUT = os.path.join(ROOT, "game", "assets", "ui")
EMBLEM_SCALE = 0.78  # emblem height 724/1024 -> 55 % of the layer, inside the 61 % mask circle


def split(svg: str) -> tuple[str, str, str]:
    """-> (head with <defs>, background rect, emblem elements)"""
    head, rest = svg.split("</defs>", 1)
    head += "</defs>"
    bg = re.search(r"<rect[^>]*/>", rest).group(0)
    emblem = rest.replace(bg, "").replace("</svg>", "")
    return head, bg, emblem


def render(svg: str, out: str, size: int) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg)
        tmp = f.name
    try:
        subprocess.run(["inkscape", tmp, "--export-type=png", f"--export-filename={out}",
                        f"--export-width={size}", f"--export-height={size}"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.unlink(tmp)
    print("wrote", os.path.relpath(out, ROOT))


def main() -> None:
    svg = open(SRC, encoding="utf-8").read()
    head, bg, emblem = split(svg)
    s = EMBLEM_SCALE
    scaled = f'<g transform="translate({512 * (1 - s):.1f} {512 * (1 - s):.1f}) scale({s})">{emblem}</g>'
    render(svg, os.path.join(OUT, "icon.png"), 1024)
    render(f"{head}{scaled}</svg>", os.path.join(OUT, "icon_adaptive_fg.png"), 432)
    render(f"{head}{bg}</svg>", os.path.join(OUT, "icon_adaptive_bg.png"), 432)
    mono = scaled.replace('fill="url(#lumen)"', 'fill="none"')  # the glow halo would become a solid disc
    mono = re.sub(r'(fill|stroke)="(url\(#\w+\)|#[0-9a-fA-F]{3,6})"', r'\1="#ffffff"', mono)
    render(f"{head}{mono}</svg>", os.path.join(OUT, "icon_monochrome.png"), 432)


if __name__ == "__main__":
    main()
