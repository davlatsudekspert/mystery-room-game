"""stair_wedge.glb — the wedged library ladder that blocks the top of the spiral stair on the Gallery side (R5).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 3 ("collapsed route, go around"; N-less beat: pull the pin from above).
A wooden rolling-ladder section leans over the stairwell mouth and is held by an oak chock with an iron pin. Pulling the
pin frees the chock, the ladder topples away and the stair is open (the scene hides/animates the parts).

Model space (Godot): origin on the floor at the FOOT of the ladder, the ladder leans toward -Z (over the stairwell) 24 deg
from vertical; the player stands on +Z. Footprint ~0.55 x 0.9 m, height 1.5 m.
Parts (origin at the pivot, identity rotation at rest):
  wedge_body        floor plate with the pin socket and the two stop brackets (static)
  IA_wedge_chock    oak chock in front of the ladder foot, origin at (0, 0, 0.17): slide +0.35 along +Z once the pin is out
  IA_wedge_pin      iron pin with a ring head, vertical, origin at the ring centre (0, 0.215, 0.17): pull +0.22 along +Y
  IA_wedge_ladder   the ladder, origin at the foot (0, 0.02, 0): topple about +X, 0 -> -78 deg (top falls toward -Z, away from the player)
    blender -b --factory-startup -P tools/blender/models/stair_wedge.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, part  # noqa: E402

NAME = "stair_wedge"
BUDGET = 3500
ARGS = M.main_guard()
LEAN = 24.0


def build():
    X.begin()
    body = [gbox("plate", (-0.30, 0.0, -0.28), (0.30, 0.02, 0.36), "M_Steel_Dark", bevel=0.003)]
    for sx in (-1, 1):                                       # stop brackets either side of the foot
        body.append(gbox("stop", (sx * 0.20 - 0.015, 0.02, -0.06), (sx * 0.20 + 0.015, 0.09, 0.06), "M_Steel_Dark", bevel=0.003))
        body.append(gcyl("bolt", 0.008, 0.004, (sx * 0.20, 0.09, 0.0), axis="y", verts=6, mat="M_Brass_Aged", bevel=0.0))
    for sx in (-0.26, 0.26):
        for sz in (-0.23, 0.31):
            body.append(gcyl("rv", 0.009, 0.008, (sx, 0.02, sz), axis="y", verts=6, mat="M_Iron_Rust", bevel=0.0, r_top=0.006))
    body.append(glathe("socket", [(0.016, 0.0), (0.030, 0.0), (0.030, 0.04), (0.016, 0.04)], (0.0, 0.02, 0.17), axis="y", segments=10, mat="M_Steel_Dark"))
    # chock: a wedge block, thick at the back, with a hole for the pin
    ch = [gbox("chock", (-0.13, 0.02, 0.07), (0.13, 0.17, 0.28), "M_Wood_Floor", bevel=0.006),
          gbox("chock_slope", (-0.13, 0.17, 0.12), (0.13, 0.19, 0.24), "M_Wood_Floor", bevel=0.004)]
    ch.append(glathe("chock_eye", [(0.026, 0.0), (0.034, 0.0), (0.034, 0.012), (0.026, 0.012)], (0.0, 0.19, 0.17), axis="y", segments=10, mat="M_Steel_Dark"))
    chock = part("IA_wedge_chock", ch, (0.0, 0.0, 0.17))
    # pin: shank down through the chock into the socket, ring head on top
    pn = [gcyl("pin", 0.011, 0.23, (0.0, 0.0, 0.17), axis="y", verts=8, mat="M_Steel_Dark", bevel=0.0, r_top=0.011),
          gcyl("pin_tip", 0.011, 0.02, (0.0, 0.0, 0.17), axis="y", verts=8, mat="M_Steel_Dark", bevel=0.0, r_top=0.006)]
    pn.append(M.torus("pin_ring", 0.032, 0.0065, loc=G(0.0, 0.255, 0.17), major_seg=16, minor_seg=5, mat="M_Iron_Rust"))
    pn.append(gcyl("pin_head", 0.016, 0.015, (0.0, 0.225, 0.17), axis="y", verts=10, mat="M_Iron_Rust", bevel=0.0))
    pin = part("IA_wedge_pin", pn, (0.0, 0.215, 0.17))
    # ladder: two rails, rungs, brass hooks at the top, built upright then leaned toward -Z
    lad = []
    L = 1.48
    for sx in (-1, 1):
        lad.append(gbox("rail", (sx * 0.18 - 0.022, 0.02, -0.015), (sx * 0.18 + 0.022, 0.02 + L, 0.015), "M_Wood_Walnut", bevel=0.004))
        lad.append(gbox("shoe", (sx * 0.18 - 0.026, 0.0, -0.02), (sx * 0.18 + 0.026, 0.06, 0.02), "M_Steel_Dark", bevel=0.003))
    for i in range(6):
        y = 0.18 + i * 0.235
        lad.append(gcyl(f"rung{i}", 0.014, 0.34, (-0.17, y, 0.0), axis="x", verts=8, mat="M_Wood_Floor", bevel=0.0))
    lad.append(gcyl("topbar", 0.011, 0.46, (-0.23, 0.02 + L - 0.02, 0.025), axis="x", verts=8, mat="M_Brass_Aged", bevel=0.0))
    for sx in (-1, 1):
        lad.append(gbox("hook", (sx * 0.18 - 0.015, 0.02 + L - 0.07, 0.0), (sx * 0.18 + 0.015, 0.02 + L + 0.02, 0.05), "M_Brass_Aged", bevel=0.003))
    U.rot_godot(lad, "x", LEAN, (0.0, 0.02, 0.0))             # Blender +X rotation by +24: top toward... verified in the render
    ladder = part("IA_wedge_ladder", lad, (0.0, 0.02, 0.0))
    part("wedge_body", body, (0, 0, 0))
    return chock, pin, ladder


if __name__ == "__main__":
    build()
    req = ["wedge_body", "IA_wedge_chock", "IA_wedge_pin", "IA_wedge_ladder"]
    errs = X.finish(NAME, req, ["IA_wedge_chock", "IA_wedge_pin", "IA_wedge_ladder"], BUDGET,
                    {"IA_wedge_chock": (0.0, 0.0, 0.17), "IA_wedge_pin": (0.0, 0.215, 0.17), "IA_wedge_ladder": (0.0, 0.02, 0.0)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.4, 1.1, 1.9), (0.0, 0.6, 0.0), 50), ("_side", (2.2, 0.9, 0.2), (0.0, 0.6, 0.0), 42)], floor=True, world=0.2)
