"""pa_horn.glb — the old public-address horn of the Reading Gallery (R5), the voice of the roll call (moment m4, N8).

A grey-painted iron re-entrant horn: exponential bell with a rolled brass rim and a cloth-covered inner baffle, a cast driver
unit with cooling fins and a small amber pilot lamp, a yoke bracket on a round wall plate, two brace rods and a cloth-covered cable.

Model space (Godot): origin = centre of the wall plate on the wall, the horn fires along +Z (out of the wall), axis at y = 0 (so
mount it at the wall height you want). Size ~0.60 w x 0.60 h x 1.12 d. West-wall placement in the gallery: (-4.5, 3.35, 0.3), yaw +90.
Parts: horn_body (static), horn_lamp (M_Emissive_Warm pilot lamp, origin at its centre (0, 0.135, 0.20)), empty light_origin_horn
(0, 0, 1.05) in front of the mouth (a faint warm OmniLight when the PA crackles).
    blender -b --factory-startup -P tools/blender/models/pa_horn.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, glathe_loop, part, mount  # noqa: E402

NAME = "pa_horn"
BUDGET = 4000
ARGS = M.main_guard()
GREY = "M_Steel_Painted"


def build():
    X.begin()
    b = []
    # wall plate and yoke
    b.append(glathe("plate", [(0.0, 0.0), (0.165, 0.0), (0.175, 0.008), (0.175, 0.022), (0.16, 0.03), (0.0, 0.03)], (0, 0, 0), axis="z", segments=24, mat="M_Iron_Rust"))
    for k in range(8):
        a = math.tau * k / 8 + 0.2
        b.append(gcyl(f"pl_bolt{k}", 0.010, 0.012, (math.cos(a) * 0.14, math.sin(a) * 0.14, 0.03), axis="z", verts=6, mat="M_Steel_Dark", bevel=0.0))
    b.append(gbox("yoke_stem", (-0.04, -0.045, 0.03), (0.04, 0.045, 0.19), "M_Iron_Rust", bevel=0.006))
    # horn flare: exponential, from the throat at z = 0.34 to the mouth at z = 1.10
    n, z0, z1, r0, r1, th = 10, 0.34, 1.10, 0.040, 0.300, 0.007
    flare = lambda t: r0 * (r1 / r0) ** (t ** 1.45)
    outer = [(flare(i / n) + th, z0 + (z1 - z0) * i / n) for i in range(n + 1)]
    inner = [(flare(i / n), z0 + (z1 - z0) * i / n) for i in range(n + 1)]
    loop = outer + [(outer[-1][0] + 0.012, z1 + 0.004), (inner[-1][0] - 0.004, z1 + 0.012)] + list(reversed(inner))
    b.append(glathe_loop("flare", loop, (0, 0, 0), axis="z", segments=22, mat=GREY))
    b.append(glathe("rim", [(r1 + th - 0.004, z1 - 0.012), (r1 + th + 0.012, z1 - 0.006), (r1 + th + 0.014, z1 + 0.012), (r1 + th - 0.004, z1 + 0.016)],
                    (0, 0, 0), axis="z", segments=28, mat="M_Brass_Aged"))
    for z, rr in ((0.52, 0.0), (0.78, 0.0)):                       # reinforcing bands
        t = (z - z0) / (z1 - z0)
        rad = flare(t) + th
        b.append(glathe(f"band{z}", [(rad - 0.002, z - 0.012), (rad + 0.008, z - 0.008), (rad + 0.008, z + 0.008), (rad - 0.002, z + 0.012)],
                        (0, 0, 0), axis="z", segments=24, mat="M_Brass_Aged"))
    # cloth baffle disc recessed in the mouth (radius follows the flare there) with a brass boss and three spider arms
    zb = 0.97
    rb = flare((zb - z0) / (z1 - z0)) - 0.004
    b.append(glathe("baffle", [(0.0, 0.0), (rb, 0.0), (rb, 0.006), (0.0, 0.030)], (0, 0, zb), axis="z", segments=22, mat="M_Grille_Fabric"))
    b.append(glathe("boss", [(0.0, 0.0), (0.03, 0.0), (0.028, 0.02), (0.0, 0.026)], (0, 0, zb + 0.026), axis="z", segments=14, mat="M_Brass_Polished"))
    for k in range(3):
        a = math.tau * k / 3 + 0.5
        sp = gbox(f"spider{k}", (0.0, -0.008, zb - 0.012), (rb, 0.008, zb), "M_Steel_Dark", bevel=0.0)
        U.rot_godot([sp], "z", math.degrees(a), (0, 0, zb))
        b.append(sp)
    # driver unit: cast drum with fins and a rear cap
    b.append(glathe("driver", [(0.0, 0.0), (0.075, 0.0), (0.085, 0.01), (0.085, 0.18), (0.07, 0.205), (0.0, 0.205)], (0, 0, 0.19), axis="z", segments=20, mat="M_Iron_Rust"))
    for i in range(5):
        b.append(glathe(f"fin{i}", [(0.083, 0.0), (0.105, 0.004), (0.105, 0.014), (0.083, 0.018)], (0, 0, 0.215 + i * 0.030), axis="z", segments=20, mat=GREY))
    b.append(glathe("throat", [(0.0, 0.0), (0.060, 0.0), (0.050, 0.06), (0.040, 0.15)], (0, 0, 0.30), axis="z", segments=14, mat=GREY))
    b.append(glathe("cap", [(0.0, 0.0), (0.055, 0.0), (0.05, 0.03), (0.0, 0.045)], (0, 0, 0.395 - 0.0), axis="z", segments=14, mat="M_Steel_Dark"))
    b.append(gbox("term", (-0.05, 0.075, 0.24), (0.05, 0.115, 0.34), "M_Bakelite", bevel=0.005))
    b.append(gcyl("lamp_seat", 0.015, 0.020, (0.0, 0.115, 0.20 - 0.0), axis="y", verts=10, mat="M_Brass_Aged", bevel=0.0))
    # braces from the plate to the bell, a cable
    for sx in (-1, 1):
        b.append(U.gbox("brace", (sx * 0.20 - 0.008, -0.008, 0.02), (sx * 0.20 + 0.008, 0.008, 0.66), "M_Iron_Rust", bevel=0.002))
    U.rot_godot([b[-1]], "y", 0.0, (0, 0, 0))
    b.append(X.pipe("cable", [(0.0, -0.08, 0.28), (0.0, -0.16, 0.20), (0.0, -0.17, 0.03), (0.0, -0.40, 0.01)], 0.009, mat="M_Fabric", fillet=0.04,
                    flange_ends=False, sides=6))
    ia = part("horn_body", b, (0, 0, 0))
    lamp = part("horn_lamp", [M.sphere("lamp", 0.014, loc=G(0.0, 0.135, 0.20), segments=10, rings=6, mat="M_Emissive_Warm")], (0.0, 0.135, 0.20), presmooth=False)
    mount("light_origin_horn", (0.0, 0.0, 1.05))
    return ia, lamp


if __name__ == "__main__":
    build()
    req = ["horn_body", "horn_lamp", "light_origin_horn"]
    errs = X.finish(NAME, req, ["horn_lamp"], BUDGET, {"horn_lamp": (0.0, 0.135, 0.20)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.5, 0.6, 1.9), (0.0, 0.0, 0.55), 46), ("_side", (2.5, 0.25, 0.55), (0.0, 0.0, 0.55), 36)], floor=False, world=0.25)
