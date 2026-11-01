"""frost_sketch.glb — Leyla's sketch of the three signs from under the frost (the bag icon of `frost_sketch`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N5): a torn half-sheet of squared paper, 0.11 x 0.08 x 0.0015, with three pencilled signs in a row
(a small triangle, a ring and a dash: only a hint, the real signs of this game are drawn by the reader in the HUD, the model is the same in every
game). Lies flat, face up (Godot +Y). Origin at the centre of mass. Original model, no third-party asset.

    blender -b --factory-startup -P tools/blender/models/frost_sketch.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gbox, gcyl, part  # noqa: E402

NAME = "frost_sketch"
BUDGET = 500
ARGS = M.main_guard()
W, D, T = 0.11, 0.08, 0.0015


def build():
    X.begin()
    o = []
    o.append(gbox("sheet", (-W / 2, -T / 2, -D / 2), (W / 2, T / 2, D / 2), "M_Paper", bevel=0.0003))
    ink = "M_Lacquer_Black"
    y = T / 2 + 0.0001
    # sign 1: a triangle (three strokes)
    for (x0, z0, x1, z1) in ((-0.040, 0.010, -0.022, 0.010), (-0.040, 0.010, -0.031, -0.008), (-0.022, 0.010, -0.031, -0.008)):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        o.append(gbox(f"t{len(o)}", (min(x0, x1) - 0.0008, y, min(z0, z1) - 0.0008), (max(x0, x1) + 0.0008, y + 0.0004, max(z0, z1) + 0.0008), ink, bevel=0.0))
    # sign 2: a ring
    o.append(gcyl("ring", 0.010, 0.0004, (0.0, y + 0.0002, 0.0), axis="y", verts=14, mat=ink, bevel=0.0))
    o.append(gcyl("ring_hole", 0.0075, 0.0006, (0.0, y + 0.0003, 0.0), axis="y", verts=14, mat="M_Paper", bevel=0.0))
    # sign 3: a dash
    o.append(gbox("dash", (0.024, y, -0.0007), (0.044, y + 0.0004, 0.0007), ink, bevel=0.0))
    X.top(o)
    return part("frost_sketch", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["frost_sketch"], ["frost_sketch"], BUDGET, {"frost_sketch": (0, 0, 0)}, show=["frost_sketch"], wood=False)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.16, 0.08), (0.0, 0.0, 0.0), 30)], floor=True, world=0.3)
