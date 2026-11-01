"""boiler.glb — the riveted fire-tube boiler of the Pump Room (R2: "a ship's engine room at night").

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3b/§7. A horizontal boiler drum (axis along Z, front +Z) on two cast saddles
with a smoke-box front: riveted shell courses with butt-strap seams, a round hinged fire door with a glowing ember slit,
a brass-framed sight glass with a water column, a large pressure gauge with a moving needle, a brass safety valve with
a weighted lever, a steam dome, feed and blow-down pipes, a flue rising to the ceiling and a maker's plate (numerals only).

Model space (Godot): front +Z, origin on the floor at the footprint centre; size ~1.30 w x 2.30 d x 3.40 h (the flue
touches y = 3.40, the Pump Room ceiling). Placement suggestion: (0, 0, -1.75), yaw 0 (against the north wall).

Parts:
  boiler_body         everything static
  IA_fire_door        round door, hinged on its left edge seen from the front: pivot (-0.285, 0.70, 1.150); opens with a
                      NEGATIVE angle about +Y (toward the viewer), -100 deg
  fire_glow           ember slit + glow plate behind the door (M_Emissive_Warm); origin at its centre (0, 0.70, 1.118)
  needle_boiler       gauge needle, pivot at the gauge centre (0.38, 1.42, 1.150); rest 225 deg (value 0), 270 deg sweep
  water_level         sight-glass water column (M_Liquid_Cobalt tinted), origin at its bottom (-0.40, 1.16, 1.140); scale Y 0..1
  light_origin_fire   empty at the glow centre where an orange OmniLight belongs
    blender -b --factory-startup -P tools/blender/models/boiler.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "boiler"
BUDGET = 16000
ARGS = M.main_guard()
R = 0.62             # drum radius
CY = 1.12            # drum axis height
Z0, Z1 = -1.15, 1.15


def build():
    X.begin()
    b = []
    # drum: shell courses (rings with slightly bigger butt straps) along Z
    prof = [(R - 0.02, Z0)]
    courses = [Z0, -0.55, 0.05, 0.62, Z1]
    for i in range(4):
        z0, z1 = courses[i] + 0.012, courses[i + 1] - 0.012
        b.append(X.glathe_loop(f"shell{i}", [(R - 0.03, z0), (R, z0 + 0.004), (R + 0.004, z0 + 0.012), (R + 0.004, z1 - 0.012),
                                             (R, z1 - 0.004), (R - 0.03, z1)], (0, CY, 0), axis="z", segments=28, mat="M_Iron_Rust"))
        zs = z1 - 0.14 if i == 3 else z1
        b.append(X.glathe_loop(f"strap{i}", [(R + 0.002, zs - 0.07), (R + 0.012, zs - 0.062), (R + 0.012, zs + 0.062),
                                             (R + 0.002, zs + 0.07)], (0, CY, 0), axis="z", segments=28, mat="M_Iron_Rust"))
    # front head: flanged plate with smoke-box ring
    b.append(glathe("front_head", [(0.0, 1.150), (R - 0.04, 1.150), (R + 0.03, 1.138), (R + 0.03, 1.108), (R - 0.02, 1.100),
                                   (0.0, 1.100)], (0, CY, 0), axis="z", segments=28, mat="M_Steel_Dark"))
    # rivet rings: radial rivets on the three butt straps, axial rivets on the front flange
    ro = []
    for zc, rr, n in ((0.62, R + 0.014, 30), (0.0, R + 0.014, 30), (-0.55, R + 0.014, 30)):
        for k in range(n):
            ang = 2 * math.pi * k / n + 0.05
            ro.append(gcyl("rv", 0.0085, 0.008, (math.cos(ang) * rr, CY + math.sin(ang) * rr, zc),
                           axis=(math.cos(ang), math.sin(ang), 0), verts=5, mat="M_Iron_Rust", bevel=0.0, r_top=0.006))
    for k in range(28):
        ang = 2 * math.pi * k / 28
        ro.append(gcyl("rvf", 0.0085, 0.008, (math.cos(ang) * (R + 0.002), CY + math.sin(ang) * (R + 0.002), 1.138), axis="z",
                       verts=5, mat="M_Iron_Rust", bevel=0.0, r_top=0.006))
    b.append(M.join(ro, "rivets"))
    # saddles
    for z in (-0.65, 0.60):
        b.append(gbox(f"saddle{z}", (-0.45, 0.0, z - 0.11), (0.45, 0.46, z + 0.11), "M_Iron_Rust", bevel=0.01))
        b.append(glathe(f"saddlering{z}", [(R + 0.002, z - 0.07), (R + 0.03, z - 0.07), (R + 0.03, z + 0.07), (R + 0.002, z + 0.07)],
                        (0, CY, 0), axis="z", segments=28, mat="M_Steel_Dark"))
    b.append(gbox("plinth", (-0.62, 0, -1.10), (0.62, 0.07, 1.10), "M_Concrete", bevel=0.004))
    # fire-box opening ring and ash pit below
    b.append(glathe("door_ring", [(0.265, 1.150), (0.31, 1.150), (0.31, 1.170), (0.265, 1.170)], (0, 0.70, 0), axis="z",
                    segments=24, mat="M_Brass_Aged"))
    b.append(gbox("ashpit", (-0.20, 0.30, 1.0), (0.20, 0.40, 1.155), "M_Steel_Dark", bevel=0.004))
    for i in range(7):
        b.append(gbox(f"grate{i}", (-0.17 + i * 0.056, 0.31, 1.15), (-0.17 + i * 0.056 + 0.03, 0.39, 1.165), "M_Lacquer_Black", bevel=0.0))
    # steam dome + safety valve with weighted lever
    b.append(glathe("dome", [(0.20, 0.0), (0.22, 0.02), (0.22, 0.20), (0.16, 0.30), (0.08, 0.34), (0.0, 0.35)],
                    (0.0, CY + R - 0.02, -0.05), axis="y", segments=22, mat="M_Brass_Aged"))
    b.append(glathe("dome_band", [(0.221, 0.06), (0.228, 0.065), (0.228, 0.085), (0.221, 0.09)], (0.0, CY + R - 0.02, -0.05),
                    axis="y", segments=22, mat="M_Brass_Polished"))
    b.append(gcyl("sv_body", 0.045, 0.16, (0.0, CY + R + 0.31, -0.05), axis="y", verts=14, mat="M_Brass_Polished", bevel=0.003))
    b.append(gcyl("sv_cap", 0.03, 0.09, (0.0, CY + R + 0.47, -0.05), axis="y", verts=12, mat="M_Brass_Aged", bevel=0.002))
    b.append(gbox("sv_lever", (-0.02, CY + R + 0.50, -0.05 - 0.02), (0.02, CY + R + 0.515, -0.05 + 0.36), "M_Steel_Dark", bevel=0.002))
    b.append(gcyl("sv_weight", 0.032, 0.07, (0.0, CY + R + 0.455, 0.27), axis="y", verts=12, mat="M_Iron_Rust", bevel=0.003))
    # flue: from the rear top up to the ceiling with a flange and a damper
    b.append(X.pipe("flue", [(0.0, CY + 0.2, -0.95), (0.0, 3.40, -0.95)], 0.15, mat="M_Steel_Dark", sides=18, flange_r=0.2,
                    flange_t=0.02, bolts=10, flange_mat="M_Iron_Rust"))
    b.append(glathe("flue_collar", [(0.12, 0.0), (0.16, 0.0), (0.16, 0.10), (0.12, 0.10)], (0.0, CY + R - 0.05, -0.95), axis="y",
                    segments=18, mat="M_Iron_Rust"))
    b.append(gcyl("damper_wheel_shaft", 0.012, 0.28, (-0.1, 2.30, -0.95), axis="x", verts=8, mat="M_Steel_Dark", bevel=0.0))
    b.append(X.wheel("damper", 0.07, 0.008, 4, (-0.20, 2.30, -0.95), axis="x", hub_r=0.02, boss_h=0.015, mat="M_Iron_Rust"))
    # feed pipe and blow-down along the right side, sight glass on the front left
    b.append(X.pipe("feed", [(0.66, 0.20, 0.70), (0.66, 1.0, 0.70), (0.66, 1.55, 0.2)], 0.028, mat="M_Copper", fillet=0.07,
                    flange_r=0.045))
    b.append(X.pipe("blowdown", [(-0.66, 0.20, 0.6), (-0.66, 0.50, 0.6), (-0.9, 0.50, 0.6)], 0.03, mat="M_Iron_Rust", fillet=0.04,
                    flange_r=0.05))
    b.append(X.wheel("bd_wheel", 0.06, 0.007, 4, (-0.93, 0.50, 0.6), axis="x", hub_r=0.018, boss_h=0.014, mat="M_Enamel_Crimson"))
    # sight glass column on the left of the front head
    b.append(gbox("sg_back", (-0.47, 1.05, 1.150), (-0.33, 1.60, 1.172), "M_Brass_Aged", bevel=0.004))
    b.append(gcyl("sg_glass", 0.017, 0.46, (-0.40, 1.10, 1.185), axis="y", verts=12, mat="M_Glass", bevel=0.0))
    for y in (1.08, 1.58):
        b.append(gcyl(f"sg_cap{y}", 0.030, 0.03, (-0.40, y - 0.015, 1.185), axis="y", verts=12, mat="M_Brass_Polished", bevel=0.002))
    b.append(gcyl("sg_cock_a", 0.012, 0.07, (-0.40, 1.04, 1.185), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    b.append(gcyl("sg_cock_b", 0.012, 0.07, (-0.40, 1.60, 1.185), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    # maker's plate (numerals only)
    b.append(gbox("maker", (-0.20, 1.72, 1.150), (0.20, 1.80, 1.158), "M_Brass_Aged", bevel=0.002))
    b.append(X.C.gtext("maker_txt", "1952  No 4", 0.040, X.C.gframe((0.0, 1.76, 1.159), (1, 0, 0), (0, 1, 0)), depth=0.0012,
                       mat="M_Lacquer_Black", resolution=1))
    # gauge (right of the head) + its needle
    gb, nd = X.gauge("gauge_boiler", (0.38, 1.42, 1.150), r=0.105, axis="z")
    b.append(gb)
    nd.name = "needle_boiler"
    b.append(gcyl("gauge_stem", 0.018, 0.20, (0.38, 1.15, 1.10), axis="y", verts=8, mat="M_Copper", bevel=0.0))
    # fire door: round plate with hinge knuckles, handle and a peep slit
    door = [glathe("door_plate", [(0.0, 0.0), (0.255, 0.0), (0.27, 0.012), (0.27, 0.035), (0.24, 0.05), (0.0, 0.05)],
                   (0.0, 0.70, 1.150), axis="z", segments=26, mat="M_Iron_Rust")]
    door.append(glathe("door_boss", [(0.0, 0.05), (0.07, 0.05), (0.075, 0.065), (0.0, 0.07)], (0.0, 0.70, 1.150), axis="z",
                       segments=16, mat="M_Brass_Aged"))
    door.append(gbox("door_handle", (-0.012, 0.70 - 0.10, 1.200), (0.012, 0.70 + 0.10, 1.230), "M_Chrome", bevel=0.004))
    door.append(gbox("door_peep", (-0.10, 0.70 - 0.012, 1.198), (0.10, 0.70 + 0.012, 1.202), "M_Lacquer_Black", bevel=0.0))
    for k in range(10):
        a = 2 * math.pi * k / 10
        door.append(gcyl(f"drv{k}", 0.009, 0.008, (math.cos(a) * 0.215, 0.70 + math.sin(a) * 0.215, 1.198), axis="z",
                         verts=5, mat="M_Steel_Dark", bevel=0.0))
    # hinge knuckles on the body side, door part pivot at the hinge line
    for y in (0.52, 0.88):
        b.append(gcyl(f"hinge{y}", 0.020, 0.10, (-0.29, y - 0.05, 1.17), axis="y", verts=8, mat="M_Steel_Dark", bevel=0.0))
    ia = part("IA_fire_door", door, (-0.285, 0.70, 1.150))   # pivot on the hinge line (left edge seen from the front)
    return b, ia


def main():
    b, ia = build()
    # re-centre: door built around x=0.24; shift mesh so the door centre sits at the fire-box ring (x = 0) and the pivot at x=-0.24
    X.top(b)
    glow = [gcyl("glow_slit", 0.20, 0.01, (0.0, 0.70, 1.108), axis="z", verts=20, mat="M_Emissive_Warm", bevel=0.0)]
    gl = part("fire_glow", glow, (0.0, 0.70, 1.118), presmooth=False)
    water = gcyl("water_level", 0.0125, 0.24, (-0.40, 1.16, 1.185), axis="y", verts=10, mat="M_Liquid_Cobalt", bevel=0.0)
    water = part("water_level", [water], (-0.40, 1.16, 1.185), presmooth=False)
    mount("light_origin_fire", (0.0, 0.70, 1.20))
    part("boiler_body", b, (0, 0, 0))
    return gl, water


gl, water = None, None
if __name__ == "__main__":
    gl, water = main()
    req = ["boiler_body", "IA_fire_door", "fire_glow", "needle_boiler", "water_level", "light_origin_fire"]
    errs = X.finish(NAME, req, ["IA_fire_door", "fire_glow", "needle_boiler", "water_level"], BUDGET,
                    {"IA_fire_door": (-0.285, 0.70, 1.150), "needle_boiler": (0.38, 1.42, 1.154)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.9, 1.5, 3.6), (0.0, 1.2, 0.0), 50), ("_front", (0.3, 1.2, 2.3), (0.0, 1.0, 1.1), 48)],
                   floor=True, world=0.15)
