"""floor_plan.glb — the building plan as a document item (the bag icon and the inspect view of `floor_plan`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3, docs/models/ch2_exp.md): a sheet of cream plan paper, 0.20 x 0.126 x 0.002, folded once
along its long middle (a soft crease, the left half a hair lower) with the same plan picture the hall frame shows (M_Decal_FloorPlan: three
stacked floor strips, rooms as tiles, no text), a brass drawing pin hole in each top corner. Lies flat, printed face up (Godot +Y), top of the
plan toward -Z. Origin at the centre of mass. Original model, no third-party asset.

    blender -b --factory-startup -P tools/blender/models/floor_plan.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gbox, gcyl, gquad, part  # noqa: E402

NAME = "floor_plan"
BUDGET = 700
ARGS = M.main_guard()
W, D, T = 0.20, 0.126, 0.002


def build():
    X.begin()
    X.decal("M_Decal_FloorPlan", "floor_plan.png")
    o = []
    # two halves of the folded sheet, the crease a hair raised so it reads as a fold
    o.append(gbox("half_l", (-W / 2, -T / 2 - 0.0003, -D / 2), (-0.0015, T / 2 - 0.0003, D / 2), "M_Paper", bevel=0.0003))
    o.append(gbox("half_r", (0.0015, -T / 2, -D / 2), (W / 2, T / 2, D / 2), "M_Paper", bevel=0.0003))
    o.append(gbox("crease", (-0.0015, -T / 2 - 0.0002, -D / 2), (0.0015, T / 2 + 0.0004, D / 2), "M_Paper", bevel=0.0))
    # the printed plan (u = +X, v = -Z so that the top of the picture lies toward -Z)
    q = gquad("plan_print", (0.0, T / 2 + 0.0004, 0.0), (1, 0, 0), (0, 0, -1), W - 0.014, D - 0.014, "M_Decal_FloorPlan")
    o.append(q)
    for sx in (-1, 1):  # pin holes: a brass ring in each top corner
        o.append(gcyl(f"pin{sx}", 0.0035, 0.0006, (sx * (W / 2 - 0.0075), T / 2 + 0.0003, -D / 2 + 0.0075), axis="y", verts=10, mat="M_Brass_Aged", bevel=0.0))
    X.top(o)
    return part("floor_plan", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["floor_plan"], ["floor_plan"], BUDGET, {"floor_plan": (0, 0, 0)}, show=["floor_plan"], wood=False)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.22, 0.12), (0.0, 0.0, 0.0), 30)], floor=True, world=0.3)
