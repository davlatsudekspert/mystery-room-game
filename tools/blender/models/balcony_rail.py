"""balcony_rail.glb — the turned-baluster balcony rail of the Reading Gallery (R5), the edge over the Archive Hall.

Dark oak handrail on a heavy bottom rail, 44 turned balusters, three newel posts with brass ball finials and brass fixing
plates. 9.0 m long (x -4.5 .. 4.5), 1.05 m high, 0.16 m deep.

Model space (Godot): origin on the gallery floor at the CENTRE of the rail line, the rail runs along X, its face toward the hall
void is +Z. Gallery placement: (0, 0, 1.60), yaw 0. Parts: rail_main (everything, one mesh, 3 material slots).
    blender -b --factory-startup -P tools/blender/models/balcony_rail.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, part, mount  # noqa: E402

NAME = "balcony_rail"
BUDGET = 6000
ARGS = M.main_guard()
OAK, BRASS = "M_Wood_Mahogany", "M_Brass_Aged"
L, HR = 9.0, 1.05


def build():
    X.begin()
    b = []
    # bottom rail (plinth) with a chamfered top, handrail with a rounded profile
    b.append(gbox("plinth", (-L / 2, 0.0, -0.08), (L / 2, 0.10, 0.08), OAK, bevel=0.008))
    b.append(gbox("plinth_cap", (-L / 2, 0.10, -0.055), (L / 2, 0.135, 0.055), OAK, bevel=0.008))
    b.append(gbox("hand_base", (-L / 2, HR - 0.06, -0.06), (L / 2, HR - 0.03, 0.06), OAK, bevel=0.005))
    b.append(gbox("hand", (-L / 2, HR - 0.03, -0.07), (L / 2, HR + 0.01, 0.07), OAK, bevel=0.016, seg=2))
    b.append(gbox("hand_top", (-L / 2, HR + 0.01, -0.05), (L / 2, HR + 0.035, 0.05), OAK, bevel=0.012, seg=2))
    b.append(gbox("brass_inlay", (-L / 2, HR + 0.034, -0.012), (L / 2, HR + 0.038, 0.012), BRASS, bevel=0.0))
    # balusters: simple turned profile (vase), 6 sided
    prof = [(0.0, 0.0), (0.021, 0.0), (0.022, 0.03), (0.013, 0.08), (0.025, 0.27), (0.014, 0.62), (0.011, 0.70), (0.0, 0.70)]
    n = 44
    y0 = 0.135
    for i in range(n):
        x = -L / 2 + 0.17 + i * (L - 0.34) / (n - 1)
        if abs(x) < 0.09 or abs(abs(x) - L / 2 + 0.17) < 0.0:
            pass
        b.append(glathe(f"bal{i}", prof, (x, y0, 0.0), axis="y", segments=6, mat=OAK))
    # newel posts at the ends and the middle
    for x in (-L / 2 + 0.07, 0.0, L / 2 - 0.07):
        b.append(gbox(f"newel{x}", (x - 0.07, 0.0, -0.07), (x + 0.07, HR + 0.08, 0.07), OAK, bevel=0.012, seg=2))
        b.append(gbox(f"newel_cap{x}", (x - 0.085, HR + 0.08, -0.085), (x + 0.085, HR + 0.105, 0.085), OAK, bevel=0.01))
        b.append(M.sphere(f"ball{x}", 0.045, loc=G(x, HR + 0.15, 0.0), segments=12, rings=7, mat=BRASS))
        b.append(gbox(f"nplate{x}", (x - 0.05, 0.50, 0.0695), (x + 0.05, 0.62, 0.0745), BRASS, bevel=0.002))
        b.append(gcyl(f"nscrew{x}", 0.009, 0.006, (x, 0.56, 0.0745), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    # brass fixing plates on the handrail every 1.5 m
    for k in range(-2, 3):
        x = k * 1.5 + 0.75
        if abs(x) < 4.4:
            b.append(gbox(f"hplate{k}", (x - 0.06, HR - 0.035, 0.065), (x + 0.06, HR + 0.005, 0.071), BRASS, bevel=0.002))
    X.top(b, 4)
    return part("rail_main", b, (0, 0, 0))


if __name__ == "__main__":
    build()
    req = ["rail_main"]
    errs = X.finish(NAME, req, [], BUDGET, {}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (-2.0, 1.3, 2.4), (-0.8, 0.6, 0.0), 54)], floor=True, world=0.2)
