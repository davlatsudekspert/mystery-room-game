"""roll_slips.glb — the clue slips from the Records counter (the bag icon of `roll_slips`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N8): a small bundle of three narrow paper slips (0.04 x 0.11 m) fanned a few degrees apart and held by a
brass paper clip, a pencil tick on each (a short dark stroke: only a hint, the real slips are pictograms drawn by the reader in the HUD). Lies flat,
face up (Godot +Y). Origin at the centre. Original model, no third-party asset.

    blender -b --factory-startup -P tools/blender/models/roll_slips.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gbox, part  # noqa: E402

NAME = "roll_slips"
BUDGET = 500
ARGS = M.main_guard()
W, D, T = 0.040, 0.110, 0.0008


def build():
    X.begin()
    o = []
    for k, ang in enumerate((-9.0, 0.0, 9.0)):
        s = gbox(f"slip{k}", (-W / 2, k * 0.0009, -D / 2), (W / 2, k * 0.0009 + T, D / 2), "M_Paper", bevel=0.0001)
        s.rotation_euler = (0, math.radians(ang), 0)
        o.append(s)
        tick = gbox(f"tick{k}", (-0.012, k * 0.0009 + T, -0.030), (0.012, k * 0.0009 + T + 0.0003, -0.028), "M_Lacquer_Black", bevel=0.0)
        tick.rotation_euler = (0, math.radians(ang), 0)
        o.append(tick)
    # the brass clip across the bottom end of the bundle
    o.append(gbox("clip_top", (-0.016, 0.0028, 0.032), (0.016, 0.0034, 0.037), "M_Brass_Aged", bevel=0.0001))
    o.append(gbox("clip_side", (0.016, 0.0000, 0.032), (0.0175, 0.0034, 0.037), "M_Brass_Aged", bevel=0.0))
    X.top(o)
    return part("roll_slips", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["roll_slips"], ["roll_slips"], BUDGET, {"roll_slips": (0, 0, 0)}, show=["roll_slips"], wood=False)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.22, 0.12), (0.0, 0.0, 0.0), 30)], floor=True, world=0.3)
