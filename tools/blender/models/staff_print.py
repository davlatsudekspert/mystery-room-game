"""staff_print.glb — the enlarged print of a staff photograph (the bag icon of `staff_print`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N9): a glossy photographic paper print, 0.13 x 0.10 x 0.0006, white border, a dark grey picture area with a
pale bust-and-head silhouette (the real print with the digits is drawn by the reader in the HUD; the model is the same in every game). Lies flat, face
up (Godot +Y). Origin at the centre. Original model, no third-party asset.

    blender -b --factory-startup -P tools/blender/models/staff_print.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gbox, gcyl, part  # noqa: E402

NAME = "staff_print"
BUDGET = 600
ARGS = M.main_guard()
W, D, T = 0.130, 0.100, 0.0006


def build():
    X.begin()
    o = []
    o.append(gbox("paper", (-W / 2, -T / 2, -D / 2), (W / 2, T / 2, D / 2), "M_Paper", bevel=0.0002))
    y = T / 2
    o.append(gbox("picture", (-W / 2 + 0.008, y, -D / 2 + 0.008), (W / 2 - 0.008, y + 0.0003, D / 2 - 0.008), "M_Lacquer_Black", bevel=0.0))
    # a pale head and shoulders
    o.append(gcyl("head", 0.016, 0.0003, (0.0, y + 0.0004, -0.008), axis="y", verts=14, mat="M_Steel_Cream", bevel=0.0))
    o.append(gbox("shoulders", (-0.030, y + 0.0003, 0.010), (0.030, y + 0.0006, D / 2 - 0.008), "M_Steel_Cream", bevel=0.0))
    X.top(o)
    return part("staff_print", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["staff_print"], ["staff_print"], BUDGET, {"staff_print": (0, 0, 0)}, show=["staff_print"], wood=False)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.22, 0.12), (0.0, 0.0, 0.0), 30)], floor=True, world=0.3)
