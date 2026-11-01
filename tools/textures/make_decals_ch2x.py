#!/usr/bin/env python3
"""Chapter 2 expansion decals (language neutral, PIL only): pipe_diagram.png (generic S/C/H schematic, the variant graph is
drawn by code), lift_plate.png (blank LOAD plate with a scale). Output: game/assets/textures/decals/ch2x/."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "game", "assets", "textures", "decals", "ch2x")
os.makedirs(OUT, exist_ok=True)

im = Image.new("RGB", (460, 300), (30, 34, 33))
d = ImageDraw.Draw(im)
d.rectangle([6, 6, 453, 293], outline=(200, 180, 120), width=4)
nodes = {"s": (60, 150), "a": (170, 80), "b": (170, 220), "c": (290, 80), "d": (290, 220), "t": (400, 80), "h": (400, 220)}
for e in ("sa", "sb", "ab", "ac", "bd", "cd", "ct", "dh", "th"):
    d.line([nodes[e[0]], nodes[e[1]]], fill=(120, 110, 90), width=5)
for k, (x, y) in nodes.items():
    col = (200, 60, 40) if k == "h" else (230, 190, 100) if k in "st" else (150, 150, 140)
    d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col, outline=(20, 20, 20), width=3)
im.save(os.path.join(OUT, "pipe_diagram.png"))

im = Image.new("RGB", (400, 200), (232, 223, 200))
d = ImageDraw.Draw(im)
d.rectangle([5, 5, 394, 194], outline=(40, 30, 24), width=5)
for i in range(15):
    x = 30 + i * 24
    d.line([x, 150, x, 175 if i % 5 == 0 else 165], fill=(40, 30, 24), width=3)
im.save(os.path.join(OUT, "lift_plate.png"))
print("ok")
