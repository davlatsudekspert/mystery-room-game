"""pass_key.glb — the pass key of the Reading Gallery (N8 reward; opens the door to the Director's Office).

The bow is the shape of a roll-call tag (a rounded card with a hang hole) with a raised head-and-shoulders portrait, so the keyhole
of the office door (the same shape) reads as "the tag's key". Brass, a round shank with two collar beads and a stepped bit with
three wards. 74 mm long.

Model space (Godot): lies flat, broad faces +-Y, the bow at -X, the shank along X, the bit at +X hanging toward +Z; origin at the
centre of mass. Part: pass_key_body (one mesh, M_Brass_Aged + M_Brass_Polished).
    blender -b --factory-startup -P tools/blender/models/pass_key.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gbox, gcyl, gpoly, part  # noqa: E402

NAME = "pass_key"
BUDGET = 1500
ARGS = M.main_guard()
T = 0.0028


def build():
    X.begin()
    b = []
    bx = -0.0245
    flat = lambda x, z, y: X.C.gframe((x, y, z), (1, 0, 0), (0, 0, -1))     # local xy = Godot (x, -z), local z = +Y
    bow = gpoly("bow", A.rounded_rect(0.030, 0.0225, 0.005, 3), T, flat(0.0, 0.0, -T / 2), mat="M_Brass_Aged", bevel=0.0004)
    bow.data.transform(__import__("mathutils").Matrix.Translation(X.GV((bx, 0.0, 0.0))))
    hole = gcyl("hole", 0.0034, T * 3, (bx - 0.0105, -T * 1.5, 0.0), axis="y", verts=14, mat="M_Brass_Aged", bevel=0.0)
    M.boolean(bow, hole)
    b.append(bow)
    # raised portrait: head and shoulders, 0.8 mm
    m = flat(bx + 0.004, 0.0, T / 2)
    sh = [(math.cos(math.pi * i / 10) * 0.0070, math.sin(math.pi * i / 10) * 0.0050 - 0.0085) for i in range(11)]
    b.append(gpoly("shoulders", list(reversed(sh)), 0.0008, m, mat="M_Brass_Polished", bevel=0.0))
    head = [(math.cos(math.tau * i / 12) * 0.0035, math.sin(math.tau * i / 12) * 0.0042 + 0.0018) for i in range(12)]
    b.append(gpoly("head", head, 0.0008, m, mat="M_Brass_Polished", bevel=0.0))
    # shank, collar beads
    b.append(gcyl("shank", 0.0030, 0.0450, (-0.0095, 0.0, 0.0), axis="x", verts=10, mat="M_Brass_Aged", bevel=0.0))
    for x in (-0.0085, -0.0050):
        b.append(gcyl(f"bead{x}", 0.0046, 0.0024, (x, 0.0, 0.0), axis="x", verts=12, mat="M_Brass_Polished", bevel=0.0004))
    b.append(gcyl("mid_ring", 0.0040, 0.0020, (0.0105, 0.0, 0.0), axis="x", verts=12, mat="M_Brass_Polished", bevel=0.0004))
    b.append(M.sphere("tip", 0.0030, loc=X.GV((0.0345, 0.0, 0.0)), segments=8, rings=5, mat="M_Brass_Aged"))
    # bit: a stepped plate hanging toward +Z (Godot) from the shank end, three wards
    bit = [(0.0185, 0.0), (0.0345, 0.0), (0.0345, -0.0105), (0.0305, -0.0105), (0.0305, -0.0062), (0.0272, -0.0062), (0.0272, -0.0125),
           (0.0240, -0.0125), (0.0240, -0.0062), (0.0215, -0.0062), (0.0215, -0.0100), (0.0185, -0.0100)]
    b.append(gpoly("bit", bit, T * 0.9, flat(0.0, 0.0, -T * 0.45), mat="M_Brass_Aged", bevel=0.0003))
    return part("pass_key_body", b, (0.0, 0.0, 0.0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["pass_key_body"], [], BUDGET, {}, show=["pass_key_body"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.16, 0.10), (0.0, 0.0, 0.0), 28)], floor=True, world=0.3, samples=16)
