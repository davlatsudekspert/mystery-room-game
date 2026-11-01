"""tea_set.glb — the cold tea for two on Strand's side table (R7 Director's Office).

An oval brass tray with a porcelain teapot (lid, knob, spout, handle), a milk jug, a sugar bowl with a lid, two cups on saucers
with cold tea in them (one half drunk), two spoons, and a folded linen napkin. Two cups, two saucers: "the tea for two" that nobody
came back to. Original design (a plain white porcelain with a thin blue-grey band and a gold rim).

Model space (Godot): origin on the tray's bottom centre, front +Z. Tray 0.50 x 0.34, total height 0.17.
Parts: tea_body (tray, pot, jug, sugar, spoons, napkin; static), IA_cup_a (left cup + saucer, origin at the saucer bottom centre
(-0.12, 0.020, 0.07)), IA_cup_b (right cup, (0.12, 0.020, 0.07)); both lift +0.06 along +Y when tapped, they are optional hotspots.
    blender -b --factory-startup -P tools/blender/models/tea_set.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, glathe_loop, part, mount  # noqa: E402

NAME = "tea_set"
BUDGET = 6000
ARGS = M.main_guard()
POR = "M_Porcelain"
Y0 = 0.020          # tray surface


def cup(prefix, cx, cz, level):
    """Cup on a saucer; returns objs. The tea is a disc at `level` of the cup's depth."""
    o = [glathe(prefix + "saucer", [(0.0, 0.0), (0.050, 0.0), (0.070, 0.004), (0.072, 0.012), (0.066, 0.011), (0.040, 0.007), (0.0, 0.007)], (cx, Y0, cz), axis="y", segments=22, mat=POR)]
    loop = [(0.026, 0.007), (0.040, 0.020), (0.050, 0.060), (0.0505, 0.0615), (0.047, 0.0615), (0.0465, 0.060), (0.038, 0.022), (0.0, 0.011)]
    o.append(glathe_loop(prefix + "cup", loop, (cx, Y0 + 0.002, cz), axis="y", segments=22, mat=POR))
    o.append(glathe(prefix + "gold", [(0.0495, 0.0575), (0.0508, 0.0575), (0.0508, 0.0618), (0.0495, 0.0618)], (cx, Y0 + 0.002, cz), axis="y", segments=22, mat="M_Brass_Polished"))
    o.append(glathe(prefix + "band", [(0.0455, 0.036), (0.0476, 0.036), (0.0476, 0.042), (0.0458, 0.042)], (cx, Y0 + 0.002, cz), axis="y", segments=22, mat="M_Enamel_Cobalt"))
    o.append(glathe(prefix + "tea", [(0.0, 0.0), (0.0415, 0.0)], (cx, Y0 + 0.002 + 0.050 * level, cz), axis="y", segments=22, mat="M_Liquid_Crimson"))
    # handle: a half torus on the +X side
    h = X.C.hint_torus(prefix + "handle", X.GV((cx + 0.049, Y0 + 0.040, cz)), 0.020, 0.0045, axis="z", major_seg=12, minor_seg=5, mat=POR)
    o.append(h)
    return o


def build():
    X.begin()
    b = []
    # tray: oval = scaled disc lathe + rim
    tray = [glathe("tray", [(0.0, 0.0), (0.158, 0.0), (0.168, 0.006), (0.172, 0.020), (0.166, 0.020), (0.160, 0.011), (0.0, 0.011)], (0, 0, 0), axis="y", segments=28, mat="M_Brass_Aged"),
            glathe("tray_in", [(0.0, 0.011), (0.162, 0.011), (0.158, 0.014), (0.0, 0.014)], (0, 0, 0), axis="y", segments=28, mat="M_Brass_Polished")]
    for o in tray:
        o.data.transform(__import__("mathutils").Matrix.Diagonal((1.45, 1.0, 1.0, 1.0)))     # Blender X stretched: 0.25 half-width along Godot x
    b += tray
    for sx in (-1, 1):
        b.append(gbox(f"tray_handle{sx}", (sx * 0.262 - 0.016, Y0 - 0.002, -0.020), (sx * 0.262 + 0.016, Y0 + 0.004, 0.020), "M_Brass_Aged", bevel=0.003))
    # teapot (centre rear): body lathe, lid, knob, spout (tube), handle (half torus)
    px, pz = 0.0, -0.045
    b.append(glathe("pot", [(0.0, 0.0), (0.040, 0.0), (0.062, 0.020), (0.070, 0.055), (0.060, 0.090), (0.040, 0.105), (0.034, 0.112)], (px, Y0, pz), axis="y", segments=22, mat=POR))
    b.append(glathe("pot_lid", [(0.0, 0.112), (0.036, 0.112), (0.034, 0.118), (0.020, 0.128), (0.0, 0.130)], (px, Y0, pz), axis="y", segments=18, mat=POR))
    b.append(M.sphere("pot_knob", 0.011, loc=G(px, Y0 + 0.140, pz), segments=10, rings=6, mat=POR))
    b.append(glathe("pot_band", [(0.0605, 0.060), (0.0715, 0.060), (0.0715, 0.068), (0.0615, 0.068)], (px, Y0, pz), axis="y", segments=22, mat="M_Enamel_Cobalt"))
    b.append(X.pipe("spout", [(px - 0.060, Y0 + 0.035, pz), (px - 0.095, Y0 + 0.060, pz), (px - 0.125, Y0 + 0.098, pz)], 0.011, mat=POR, fillet=0.03, flange_ends=False, sides=8))
    hd = X.C.hint_torus("pot_handle", X.GV((px + 0.080, Y0 + 0.070, pz)), 0.038, 0.007, axis="z", major_seg=14, minor_seg=5, mat=POR)
    b.append(hd)
    # milk jug and sugar bowl (right and left rear)
    b.append(glathe("jug", [(0.0, 0.0), (0.026, 0.0), (0.034, 0.020), (0.032, 0.050), (0.028, 0.062), (0.034, 0.068)], (0.17, Y0, -0.075), axis="y", segments=16, mat=POR))
    b.append(gbox("jug_lip", (0.158, Y0 + 0.060, -0.075 - 0.012), (0.190, Y0 + 0.066, -0.075 + 0.012), POR, bevel=0.003))
    b.append(X.C.hint_torus("jug_handle", X.GV((0.205, Y0 + 0.040, -0.075)), 0.018, 0.004, axis="z", major_seg=10, minor_seg=5, mat=POR))
    b.append(glathe("sugar", [(0.0, 0.0), (0.030, 0.0), (0.040, 0.016), (0.040, 0.040), (0.036, 0.046)], (-0.20, Y0, -0.105), axis="y", segments=16, mat=POR))
    b.append(glathe("sugar_lid", [(0.0, 0.046), (0.038, 0.046), (0.030, 0.056), (0.0, 0.060)], (-0.20, Y0, -0.105), axis="y", segments=16, mat=POR))
    b.append(M.sphere("sugar_knob", 0.008, loc=G(-0.20, Y0 + 0.066, -0.105), segments=8, rings=5, mat=POR))
    # spoons on the tray front, napkin
    for sx in (-0.12, 0.12):
        b.append(gbox(f"spoon{sx}", (sx - 0.050, Y0 + 0.0, 0.130), (sx + 0.030, Y0 + 0.003, 0.136), "M_Chrome", bevel=0.0008))
        b.append(glathe(f"spoon_bowl{sx}", [(0.0, 0.0), (0.011, 0.0), (0.0, 0.004)], (sx + 0.040, Y0 + 0.001, 0.133), axis="y", segments=10, mat="M_Chrome"))
    b.append(gbox("napkin", (-0.030, Y0, 0.100), (0.030, Y0 + 0.012, 0.150), "M_Linen", bevel=0.004))
    b.append(gbox("napkin_fold", (-0.030, Y0 + 0.012, 0.100), (0.030, Y0 + 0.016, 0.125), "M_Linen", bevel=0.002))
    X.top(b, 4)
    body = part("tea_body", b, (0, 0, 0))
    ca = part("IA_cup_a", cup("ca_", -0.12, 0.07, 0.85), (-0.12, Y0, 0.07))
    cb = part("IA_cup_b", cup("cb_", 0.12, 0.07, 0.42), (0.12, Y0, 0.07))
    return body, ca, cb


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["tea_body", "IA_cup_a", "IA_cup_b"], ["IA_cup_a", "IA_cup_b"], BUDGET,
                    {"IA_cup_a": (-0.12, Y0, 0.07), "IA_cup_b": (0.12, Y0, 0.07)}, show=["tea_body", "IA_cup_a"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.5, 0.45, 0.65), (0.0, 0.05, 0.0), 40)], floor=True, world=0.25, samples=20)
