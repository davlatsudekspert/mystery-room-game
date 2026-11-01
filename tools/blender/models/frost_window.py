"""frost_window.glb — the frosted store-room window of the Cold Store (N5 "Frost window": wipe reveal, cloth beat).

A galvanised casement window with a deep reveal and an inside sill. The pane is covered in hoar frost; under each of three
horizontal bands Leyla finger-wrote one symbol (the three signs form the chest target). Layers seen from the room (+Z):
  frost_glass   z +0.018  quad 0.80 x 1.20, slot `M_Decal_FrostPane` (ShaderMaterial, uniform `wipe_mask`, see the .gdshader)
  frost_sign_k  z +0.004  quad 0.22 x 0.22 each, slot `M_Decal_FrostSign` (the scene sets the texture decals/ch2x/frost_sign_0..5.png)
  window_glass  z  0.000  clear pane (M_Glass) with the cold daylight behind
UV layout of `frost_glass` (the wipe mask is painted in this space): U 0..1 left to right as seen from the room, glTF V 0 = TOP
of the pane (image row 0 = top). The pane is 0.80 w x 1.20 h, the three bands are 0.40 high each and tile it:
  band_0  V 0.000..0.333  (top)      centre (0,  +0.40, 0.018)
  band_1  V 0.333..0.667  (middle)   centre (0,   0.00, 0.018)
  band_2  V 0.667..1.000  (bottom)   centre (0,  -0.40, 0.018)
Sign k sits at the centre of band k, shifted along X by (-0.22, 0, +0.22): reading left to right = band 0, 1, 2.
Two glazing bars (at the band borders) lie behind the frost and show through it.
Origin = the centre of the pane in the plane of the glass; the front is +Z (into the room). The inner wall plane is z = +0.045
(the casing sits on it): cut a 0.96 x 1.36 opening in the wall behind it, the reveal reaches back to z = -0.22.
Parts / nodes: window_frame (static), window_glass, frost_sign_0..2, frost_glass, empties band_0..2 and light_window (0, 0, -0.20).
    blender -b --factory-startup -P tools/blender/models/frost_window.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "frost_window"
BUDGET = 3200
ARGS = M.main_guard()
PW, PH = 0.80, 1.20
GALV, DARK, PAINT = "M_Steel_Galv", "M_Steel_Dark", "M_Enamel_Ice"
ZW = 0.045          # inner wall plane (casing front face)
ZB = -0.22          # back of the reveal
ZC = ZW + 0.004     # the casing stands 4 mm proud of the wall plane (no coplanar faces with the wall panel)


def frame():
    o = []
    fw = 0.045           # frame member width seen from the front
    hx, hy = PW / 2, PH / 2
    # sash frame round the pane (depth z -0.02..+0.030)
    for nm, mn, mx in (("fl", (-hx - fw, -hy - fw, -0.02), (-hx, hy + fw, 0.030)), ("fr", (hx, -hy - fw, -0.02), (hx + fw, hy + fw, 0.030)),
                       ("ft", (-hx, hy, -0.02), (hx, hy + fw, 0.030)), ("fb", (-hx, -hy - fw, -0.02), (hx, -hy, 0.030))):
        o.append(gbox(nm, mn, mx, GALV, bevel=0.004))
    # inner lip so the glass reads as set in a rebate
    for nm, mn, mx in (("lp_l", (-hx, -hy, 0.0), (-hx + 0.012, hy, 0.024)), ("lp_r", (hx - 0.012, -hy, 0.0), (hx, hy, 0.024)),
                       ("lp_t", (-hx, hy - 0.012, 0.0), (hx, hy, 0.024)), ("lp_b", (-hx, -hy, 0.0), (hx, -hy + 0.012, 0.024))):
        o.append(gbox(nm, mn, mx, DARK, bevel=0.0))
    # glazing bars at the band borders, behind the frost (z 0.002..0.014)
    for y in (PH / 6, -PH / 6):
        o.append(gbox(f"bar{y:+.2f}", (-hx, y - 0.013, 0.002), (hx, y + 0.013, 0.014), GALV, bevel=0.002))
    # casing: 0.10 steel surround on the wall plane, lap seams and rivets
    cx0, cy0 = hx + fw + 0.0, hy + fw
    cw = 0.10
    for nm, mn, mx in (("cs_l", (-cx0 - cw, -cy0 - cw, ZC - 0.022), (-cx0, cy0 + cw, ZC)), ("cs_r", (cx0, -cy0 - cw, ZC - 0.022), (cx0 + cw, cy0 + cw, ZC)),
                       ("cs_t", (-cx0, cy0, ZC - 0.022), (cx0, cy0 + cw, ZC)), ("cs_b", (-cx0, -cy0 - cw, ZC - 0.022), (cx0, -cy0, ZC))):
        o.append(gbox(nm, mn, mx, "M_Enamel_Ice", bevel=0.0))
    rv = []
    for x in (-cx0 - cw / 2, cx0 + cw / 2):
        for y in (-1.15 * 0.5, -0.30, 0.0, 0.30, 0.55):
            rv.append((x, y, ZC))
    for y in (cy0 + cw / 2, -cy0 - cw / 2):
        for x in (-0.55 * 0.5, 0.0, 0.27, -0.27):
            rv.append((x, y, ZC))
    o.append(X.rivets("rv", rv, 0.0075, "z", mat=DARK, segs=6))
    # reveal lining: four slabs back to z = -0.22 (inside faces visible through the opening)
    for nm, mn, mx in (("rv_l", (-cx0, -cy0, ZB), (-cx0 + 0.012, cy0, -0.02)), ("rv_r", (cx0 - 0.012, -cy0, ZB), (cx0, cy0, -0.02)),
                       ("rv_t", (-cx0, cy0 - 0.012, ZB), (cx0, cy0, -0.02)), ("rv_b", (-cx0, -cy0, ZB), (cx0, -cy0 + 0.012, -0.02))):
        o.append(gbox(nm, mn, mx, "M_Concrete", bevel=0.0))
    # inside sill: a steel ledge into the room with a drip lip, and a tin tray on it
    o.append(gbox("sill", (-cx0 - cw, -cy0 - cw - 0.030, ZW - 0.02), (cx0 + cw, -cy0 - cw, ZW + 0.17), GALV, bevel=0.005))
    o.append(gbox("sill_lip", (-cx0 - cw, -cy0 - cw - 0.030, ZW + 0.17), (cx0 + cw, -cy0 - cw + 0.012, ZW + 0.185), PAINT, bevel=0.002))
    # casement latch (cam handle) on the right of the sash and two hinges on the left
    o.append(gbox("latch_base", (hx + 0.004, -0.06, 0.030), (hx + 0.040, 0.06, 0.040), "M_Brass_Aged", bevel=0.002))
    o.append(gbox("latch_arm", (hx + 0.012, -0.012, 0.040), (hx + 0.034, 0.17, 0.056), "M_Brass_Polished", bevel=0.003))
    o.append(gcyl("latch_knob", 0.012, 0.030, (hx + 0.023, 0.17, 0.040), axis="z", verts=10, mat="M_Brass_Polished", bevel=0.001))
    for y in (0.40, -0.40):
        o.append(gcyl(f"hinge{y}", 0.012, 0.10, (-hx - fw / 2, y - 0.05, 0.030), axis="y", verts=8, mat=DARK, bevel=0.0))
        o.append(gbox(f"hinge_p{y}", (-hx - fw + 0.004, y - 0.05, 0.030), (-hx + 0.004, y + 0.05, 0.036), DARK, bevel=0.0015))
    # hoar frost in the lower corners and along the sill (flat white lumps), and short icicles under the top casing
    # hoar frost crust: thin white slabs on the sill and in the bottom of the sash (flat, no lumps)
    o.append(gbox("rime_sill", (-0.40, -cy0 - cw, ZW + 0.04), (0.38, -cy0 - cw + 0.007, ZW + 0.15), "M_Porcelain", bevel=0.0))
    o.append(gbox("rime_sash", (-hx + 0.012, -hy + 0.012, 0.024), (hx - 0.012, -hy + 0.045, 0.030), "M_Porcelain", bevel=0.0))
    for k, x in enumerate((-0.30, -0.12, 0.10, 0.32)):
        ln = (0.05, 0.08, 0.04, 0.065)[k]
        o.append(gcyl(f"ice{k}", 0.010, ln, (x, cy0 - ln + 0.0, ZW + 0.004), axis="y", verts=5, mat="M_Frost", bevel=0.0, r_top=0.002))
    return o


def main():
    X.begin()
    K.decal_alpha("M_Decal_FrostSign", "frost_sign_0.png")
    hx, hy = PW / 2, PH / 2
    body = part("window_frame", frame(), (0, 0, 0))
    glass = M.box("window_glass", (PW, PH, 0.006), loc=(0, 0, 0), mat="M_Glass", bevel=0.0, segments=1)
    glass = part("window_glass", [glass], (0, 0, 0), presmooth=False)
    glass.location = (0, 0, 0)
    signs = []
    for k in range(3):
        cx, cy = (-0.22, 0.0, 0.22)[k], (0.40, 0.0, -0.40)[k]
        q = K.quad_decal(f"frost_sign_{k}", (cx, cy, 0.004), (1, 0, 0), (0, 1, 0), 0.22, 0.22, "M_Decal_FrostSign")
        signs.append(part(f"frost_sign_{k}", [q], (cx, cy, 0.004), presmooth=False))
    fg = K.quad_decal("frost_glass", (0, 0, 0.018), (1, 0, 0), (0, 1, 0), PW, PH, "M_Decal_FrostPane")
    fg = part("frost_glass", [fg], (0, 0, 0.018), presmooth=False)
    for k in range(3):
        mount(f"band_{k}", (0.0, (0.40, 0.0, -0.40)[k], 0.018))
    mount("light_window", (0.0, 0.0, -0.20))
    return body, glass, signs, fg


if __name__ == "__main__":
    body, glass, signs, fg = main()
    req = ["window_frame", "window_glass", "frost_sign_0", "frost_sign_1", "frost_sign_2", "frost_glass", "band_0", "band_1", "band_2", "light_window"]
    errs = X.finish(NAME, req, ["frost_glass", "frost_sign_0"], BUDGET, {"frost_glass": (0, 0, 0.018), "frost_sign_1": (0.0, 0.0, 0.004)}, show=["frost_glass"], wood=False)
    if X.want_render(ARGS):
        import bpy
        K.fix_pbr()
        K.qa_frost_material(wipe_band=-1)
        # cold daylight card behind the glass
        card = K.quad_decal("qa_card", (0, 0, -0.60), (1, 0, 0), (0, 1, 0), 3.0, 3.0, "M_Emissive_Cold")
        bm = bpy.data.materials["M_Emissive_Cold"].node_tree.nodes["Principled BSDF"]
        bm.inputs["Emission Strength"].default_value = 1.2
        COLD = [((0.8, 0.9, 2.0), 160, "D8EAFF", 0.5), ((-1.2, 0.4, 1.4), 70, "FFE9CC", 0.6)]
        X.qa_props(NAME, [("_frosted", (0.0, 0.1, 2.15), (0.0, 0.0, 0.0), 46)], floor=False, world=0.5, lights=K.glights(COLD))
        K.qa_frost_material(wipe_band=1)
        X.qa_props(NAME, [("_wiped", (0.5, 0.1, 1.9), (0.0, 0.0, 0.0), 46)], floor=False, world=0.5, lights=K.glights(COLD))

