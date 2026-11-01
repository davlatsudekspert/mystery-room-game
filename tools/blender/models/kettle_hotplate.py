"""kettle_hotplate.glb — Leyla's two-ring electric hotplate with a blue enamel kettle (Night Cell, view `shelf`; "kettle tick" ambience).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3b/§7). A cream pressed-steel hotplate with a chrome rim, two cast rings (the left one has
a live coil that glows), two bakelite knobs with brass pointers, rubber feet and a cloth-covered cord that drops behind. A cobalt enamel kettle
with a cream rim, a bakelite handle and lid knob stands on the left ring, spout toward -X.

Model space (Godot): front +Z, origin on the support surface at the footprint centre (feet on y = 0). Footprint 0.42 (x) x 0.27 (z), plate top 0.075,
kettle top about 0.255.

Parts:
  hotplate_body     static hotplate (case, rings, feet, cord, knob faces)
  IA_kettle         the kettle with lid. Origin at the centre of its base on the ring: (-0.105, 0.0775, 0.0), rest = sitting on the ring.
                    Lift it by moving +Y (a tap target; it is also the item "kettle" if the scene wants one)
  IA_knob_left      bakelite knob, pivot (-0.105, 0.040, 0.1345) on the front face, turns about +Z; rest = off (pointer down). -90 deg = full on
  IA_knob_right     the same at (0.105, 0.040, 0.1345)
  coil_glow         the left coil ring (M_Emissive_Warm), origin (-0.105, 0.0905, 0.0); hide when off
  steam_mount       empty above the spout tip (-0.255, 0.205, 0.0), put the steam particles / the tick audio here

    blender -b --factory-startup -P tools/blender/models/kettle_hotplate.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "kettle_hotplate"
BUDGET = 4800
ARGS = M.main_guard()
CASE, CHROME, BAKE, BLUE, CREAM = "M_Steel_Cream", "M_Chrome", "M_Bakelite", "M_Enamel_Cobalt", "M_Enamel_Cream"
TOP = 0.075
LX, RX = -0.105, 0.105
KZ = 0.1345


def hotplate():
    o = []
    # case: base tray + body with rounded top corners, chrome rim ring on the top edge
    o.append(gbox("tray", (-0.205, 0.012, -0.130), (0.205, 0.030, 0.130), "M_Steel_Dark", bevel=0.004))
    o.append(gbox("case", (-0.210, 0.030, -0.132), (0.210, TOP - 0.006, 0.132), CASE, bevel=0.010, seg=2))
    o.append(gbox("rim", (-0.214, TOP - 0.008, -0.136), (0.214, TOP, 0.136), CHROME, bevel=0.003))
    o.append(gbox("topplate", (-0.202, TOP - 0.003, -0.124), (0.202, TOP + 0.0005, 0.124), "M_Steel_Painted", bevel=0.0))
    for x in (-0.18, 0.18):                       # rubber feet
        for z in (-0.10, 0.10):
            o.append(gcyl(f"foot{x}{z}", 0.014, 0.012, (x, 0.0, z), axis="y", verts=10, mat="M_Rubber", bevel=0.0, r_top=0.012))
    # cast rings (right = cold ring, with a grooved plate; left = live coil, glowing part separate)
    for x, nm in ((LX, "l"), (RX, "r")):
        o.append(glathe(f"ring_{nm}", [(0.0, 0.0), (0.086, 0.0), (0.090, 0.004), (0.090, 0.012), (0.083, 0.015), (0.0, 0.015)], (x, TOP, 0.0), axis="y",
                        segments=26, mat="M_Iron_Rust" if nm == "r" else "M_Steel_Dark"))
    for k in range(3):                            # grooves of the right ring
        o.append(glathe(f"groove{k}", [(0.018 + 0.022 * k, 0.015), (0.026 + 0.022 * k, 0.0165), (0.030 + 0.022 * k, 0.015)], (RX, TOP, 0.0), axis="y",
                        segments=24, mat="M_Steel_Dark"))
    # front panel: two knob bosses and a small enamel label plate
    for x in (LX, RX):
        o.append(gcyl(f"boss{x}", 0.030, 0.006, (x, 0.040, 0.132), axis="z", verts=18, mat=CHROME, bevel=0.0015))
        for k in range(7):                         # tick marks around (0..270 deg)
            a = math.radians(-90 + 30 * k)
            o.append(gbox(f"tk{x}{k}", (x + math.sin(a) * 0.036 - 0.0015, 0.040 - math.cos(a) * 0.036 - 0.0015, 0.1385),
                          (x + math.sin(a) * 0.036 + 0.0015, 0.040 - math.cos(a) * 0.036 + 0.0015, 0.1395), "M_Lacquer_Black", bevel=0.0))
    # cord: a cloth cable coming out of the back, dropping behind
    o.append(X.pipe("cord", [(0.16, 0.040, -0.128), (0.16, 0.040, -0.190), (0.16, 0.012, -0.230), (0.12, 0.004, -0.300)], 0.0045, mat="M_Fabric", sides=6,
                    fillet=0.05, flange_ends=False))
    o.append(gbox("cord_relief", (0.153, 0.032, -0.140), (0.167, 0.048, -0.128), BAKE, bevel=0.003))
    return o


def kettle():
    o = []
    prof = [(0.0, 0.0), (0.082, 0.0), (0.090, 0.006), (0.098, 0.040), (0.094, 0.085), (0.082, 0.115), (0.066, 0.132), (0.056, 0.142),
            (0.054, 0.148), (0.0, 0.148)]
    o.append(glathe("k_body", prof, (LX, TOP + 0.0025, 0.0), axis="y", segments=26, mat=BLUE))
    o.append(glathe("k_base_rim", [(0.083, 0.0), (0.091, 0.0), (0.092, 0.012), (0.085, 0.012)], (LX, TOP + 0.0025, 0.0), axis="y", segments=26, mat=CREAM))
    o.append(glathe("k_lid", [(0.0, 0.150), (0.040, 0.150), (0.054, 0.148), (0.056, 0.152), (0.046, 0.160), (0.024, 0.170), (0.0, 0.172)], (LX, TOP + 0.0025, 0.0),
                    axis="y", segments=22, mat=BLUE))
    o.append(glathe("k_lid_rim", [(0.054, 0.1475), (0.0575, 0.1475), (0.0575, 0.1525), (0.054, 0.1525)], (LX, TOP + 0.0025, 0.0), axis="y", segments=22,
                    mat=CREAM))
    o.append(gcyl("k_knob", 0.013, 0.022, (LX, TOP + 0.0025 + 0.170, 0.0), axis="y", verts=12, mat=BAKE, bevel=0.002, r_top=0.010))
    # spout: tapered tube leaving to -X, high on the shoulder
    sp = [(LX - 0.075, TOP + 0.0025 + 0.090, 0.0), (LX - 0.120, TOP + 0.0025 + 0.118, 0.0), (LX - 0.150, TOP + 0.0025 + 0.140, 0.0)]
    o.append(X.pipe("k_spout", sp, 0.020, mat=BLUE, sides=12, flange_ends=False, caps=False))
    # handle: bakelite arc on +X side with two brackets
    base = (LX + 0.088, TOP + 0.0025)
    h = [(base[0] + 0.0, base[1] + 0.130, 0.0), (base[0] + 0.040, base[1] + 0.128, 0.0), (base[0] + 0.062, base[1] + 0.095, 0.0),
         (base[0] + 0.060, base[1] + 0.055, 0.0), (base[0] + 0.030, base[1] + 0.030, 0.0), (base[0] + 0.004, base[1] + 0.034, 0.0)]
    o.append(X.pipe("k_handle", h, 0.0085, mat=BAKE, sides=8, fillet=0.03, flange_ends=False))
    o.append(gbox("k_bracket_a", (base[0] - 0.006, base[1] + 0.120, -0.010), (base[0] + 0.008, base[1] + 0.138, 0.010), "M_Steel_Dark", bevel=0.002))
    o.append(gbox("k_bracket_b", (base[0] - 0.006, base[1] + 0.026, -0.010), (base[0] + 0.008, base[1] + 0.044, 0.010), "M_Steel_Dark", bevel=0.002))
    # chipped enamel spots: three dark small discs on the belly (front)
    for (a, hy, r) in ((0.35, 0.07, 0.006), (-0.9, 0.05, 0.004), (0.9, 0.095, 0.005)):
        o.append(gcyl(f"chip{a}", r, 0.0015, (LX + math.sin(a) * 0.0965, TOP + 0.0025 + hy, math.cos(a) * 0.0965), axis=(math.sin(a), 0, math.cos(a)), verts=6,
                      mat="M_Steel_Dark", bevel=0.0))
    return o


def knob(x):
    o = [gcyl(f"kn{x}", 0.021, 0.026, (x, 0.040, KZ), axis="z", verts=18, mat=BAKE, bevel=0.003, r_top=0.018),
         gcyl(f"kn_cap{x}", 0.010, 0.004, (x, 0.040, KZ + 0.026), axis="z", verts=10, mat="M_Brass_Aged", bevel=0.0),
         gbox(f"kn_ptr{x}", (x - 0.0025, 0.040 - 0.0205, KZ + 0.020), (x + 0.0025, 0.040 - 0.008, KZ + 0.028), "M_Brass_Polished", bevel=0.0005)]
    return part("IA_knob_left" if x < 0 else "IA_knob_right", o, (x, 0.040, KZ))


def main():
    X.begin()
    kn = [knob(LX), knob(RX)]
    k = part("IA_kettle", kettle(), (LX, TOP + 0.0025, 0.0))
    coil = []
    for i, (r0, r1) in enumerate(((0.020, 0.028), (0.040, 0.048), (0.060, 0.068))):
        coil.append(glathe(f"coil{i}", [(r0, 0.0), (r1, 0.0), (r1, 0.0045), (r0, 0.0045)], (LX, TOP + 0.012, 0.0), axis="y", segments=26, mat="M_Emissive_Warm"))
    cg = part("coil_glow", coil, (LX, TOP + 0.0155, 0.0), presmooth=False)
    mount("steam_mount", (LX - 0.150, 0.205, 0.0))
    b = hotplate()
    X.top(b)
    part("hotplate_body", b, (0, 0, 0))
    return kn, k, cg


if __name__ == "__main__":
    main()
    req = ["hotplate_body", "IA_kettle", "IA_knob_left", "IA_knob_right", "coil_glow", "steam_mount"]
    errs = X.finish(NAME, req, ["IA_kettle", "IA_knob_left", "IA_knob_right", "coil_glow"], BUDGET,
                    {"IA_kettle": (LX, TOP + 0.0025, 0.0), "IA_knob_left": (LX, 0.040, KZ)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.55, 0.42, 0.62), (0.0, 0.10, 0.0), 38), ("_front", (0.0, 0.20, 0.70), (0.0, 0.10, 0.0), 36),
                          ("_back", (-0.5, 0.35, -0.55), (0.0, 0.10, 0.0), 40)], floor=True, world=0.15)
