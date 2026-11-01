"""enlarger.glb — the plate-room enlarger (R6, puzzle N9: strip + zoom + focus -> a print with Strand's digits).

A cast-iron column enlarger on a mahogany baseboard: lamp house with cooling fins, a negative carrier with a slot for the strip, a
square leather-look bellows, a lens barrel with a knurled focus ring, a crank for the height ("zoom") on the column clamp, a paper
easel with four black masking blades, a darkroom timer box with two bakelite knobs and a red safelight filter swing-arm.

Model space (Godot): origin on the baseboard BOTTOM at its centre (sits on the bench top), front +Z. Baseboard 0.64 x 0.54, column
at the back left. Size ~0.64 w x 0.54 d x 1.22 h.
Parts (origin at the pivot, identity rotation at rest):
  enlarger_body     baseboard, column, easel, timer, safelight arm (static)
  IA_head           lamp house + carrier + bellows + lens board + lens barrel + the crank clamp, origin at the optical axis on the carrier
                    plane: (0.05, 0.70, 0.10). ZOOM: slides along +Y by 0.04 m per zoom step, 5 steps (0 .. 0.16 m, rest = step 0)
  IA_zoom_knob      crank on the clamp (child of IA_head in the scene), origin on its axle (-0.33, 0.74, -0.19), turns about +X
  IA_focus_ring     brass ring on the lens barrel (child of IA_head), origin on the optical axis (0.05, 0.375, 0.10), turns about +Y; 9 index
                    ticks every 40 degrees with a fixed index mark on the barrel (focus 0..8)
  (the square bellows accordion is part of IA_head's mesh and rises with it)
  strip_slot        empty, the negative carrier slot centre (0.05, 0.665, 0.10): the strip lies here (strip 0.20 x 0.045, long axis along X)
  projected_image   quad on the baseboard under the lens (0.05, 0.0305, 0.10), 0.20 x 0.15, slot M_Decal_Prints (placeholder; swap the
                    image per variant, scale about its centre with the zoom, blur with the focus)
  light_origin_enlarger  empty at the lens (0.05, 0.40, 0.10)
    blender -b --factory-startup -P tools/blender/models/enlarger.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402

NAME = "enlarger"
BUDGET = 6000
ARGS = M.main_guard()
AX, AZ = 0.05, 0.10               # optical axis
CX, CZ = -0.22, -0.19             # column
IRON, DARK, CAST = "M_Iron_Rust", "M_Steel_Dark", "M_Steel_Painted"


def build():
    X.begin()
    b = []
    # baseboard (mahogany, chamfered) + rubber feet; column on a cast foot
    b.append(gbox("board", (-0.32, 0.0, -0.27), (0.32, 0.03, 0.27), "M_Wood_Mahogany", bevel=0.006, seg=2))
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.append(gcyl("foot", 0.018, 0.004, (sx * 0.29, -0.0, sz * 0.24), axis="y", verts=8, mat="M_Rubber", bevel=0.0))
    b.append(gbox("col_foot", (CX - 0.06, 0.03, CZ - 0.06), (CX + 0.06, 0.07, CZ + 0.06), IRON, bevel=0.006))
    b.append(gbox("column", (CX - 0.022, 0.07, CZ - 0.022), (CX + 0.022, 1.20, CZ + 0.022), "M_Steel_Galv", bevel=0.003))
    b.append(gbox("col_rack", (CX - 0.008, 0.07, CZ + 0.022), (CX + 0.008, 1.18, CZ + 0.030), DARK, bevel=0.0))
    for i in range(18):                                                            # rack teeth
        y = 0.12 + i * 0.06
        b.append(gbox(f"tooth{i}", (CX - 0.008, y, CZ + 0.030), (CX + 0.008, y + 0.018, CZ + 0.036), DARK, bevel=0.0))
    b.append(gcyl("col_cap", 0.03, 0.03, (CX, 1.20, CZ), axis="y", verts=10, mat=IRON, bevel=0.003))
    for y in (0.65, 0.82, 1.0):                                                    # height scale ticks on the column face
        b.append(gbox(f"scale{y}", (CX - 0.022, y, CZ + 0.0225), (CX - 0.004, y + 0.003, CZ + 0.0245), "M_Enamel_Cream", bevel=0.0))
    # easel: white blade, four black masking blades, a brass hinge strip
    b.append(gbox("easel_base", (AX - 0.145, 0.03, AZ - 0.115), (AX + 0.145, 0.034, AZ + 0.115), "M_Enamel_White", bevel=0.001))
    for nm, mn, mx in (("m_l", (AX - 0.145, 0.034, AZ - 0.115), (AX - 0.108, 0.037, AZ + 0.115)),
                       ("m_r", (AX + 0.108, 0.034, AZ - 0.115), (AX + 0.145, 0.037, AZ + 0.115)),
                       ("m_t", (AX - 0.145, 0.034, AZ - 0.115), (AX + 0.145, 0.037, AZ - 0.088)),
                       ("m_b", (AX - 0.145, 0.034, AZ + 0.088), (AX + 0.145, 0.037, AZ + 0.115))):
        b.append(gbox(nm, mn, mx, "M_Lacquer_Black", bevel=0.0007))
    b.append(gbox("easel_hinge", (AX - 0.15, 0.03, AZ + 0.115), (AX + 0.15, 0.04, AZ + 0.128), "M_Brass_Aged", bevel=0.002))
    # timer box, front left of the board
    b.append(gbox("timer", (-0.29, 0.03, 0.12), (-0.14, 0.095, 0.25), "M_Bakelite", bevel=0.007, seg=2))
    b.append(gcyl("timer_face", 0.034, 0.003, (-0.215, 0.07, 0.250), axis="z", verts=20, mat="M_Enamel_Cream", bevel=0.0))
    for k in range(9):
        a = math.radians(225 - 33.75 * k)
        b.append(gbox(f"ttick{k}", (-0.0012, 0.0, 0.0), (0.0012, 0.012, 0.0014), "M_Lacquer_Black", bevel=0.0))
        U.rot_godot([b[-1]], "z", math.degrees(a) - 90, (0, 0, 0))
        U.move([b[-1]], (-0.215 + math.cos(a) * 0.022, 0.07 + math.sin(a) * 0.022, 0.2535))
    b.append(gcyl("timer_knob", 0.014, 0.020, (-0.215, 0.07, 0.253), axis="z", verts=14, mat="M_Bakelite", bevel=0.002))
    b.append(gbox("timer_ptr", (-0.2165, 0.07, 0.272), (-0.2135, 0.095, 0.274), "M_Lacquer_Black", bevel=0.0))
    b.append(gcyl("timer_btn", 0.010, 0.014, (-0.165, 0.045, 0.250), axis="z", verts=10, mat="M_Enamel_Crimson", bevel=0.001))
    # red filter swing arm on the column (a safelight filter that swings under the lens)
    b.append(gcyl("arm_pin", 0.006, 0.12, (CX + 0.034, 0.30, CZ), axis="y", verts=6, mat=DARK, bevel=0.0))
    b.append(gbox("arm_bar", (CX + 0.028, 0.37, CZ - 0.006), (CX + 0.17, 0.381, CZ + 0.006), DARK, bevel=0.0008))
    b.append(gcyl("arm_filter", 0.034, 0.003, (CX + 0.18, 0.385, CZ + 0.0), axis="y", verts=16, mat="M_Emissive_Safelight", bevel=0.0))
    X.top(b, 4)
    body = part("enlarger_body", b, (0, 0, 0))

    # ---- head (moves up the column): clamp + arm + lamp house + carrier + bellows + lens board + lens barrel
    h = []
    y0 = 0.70
    h.append(gbox("clamp", (CX - 0.04, y0 - 0.06, CZ - 0.04), (CX + 0.04, y0 + 0.14, CZ + 0.04), IRON, bevel=0.005))
    h.append(gbox("arm", (CX + 0.02, y0 + 0.02, CZ - 0.03), (AX - 0.06, y0 + 0.08, AZ + 0.0), IRON, bevel=0.006))
    h.append(gbox("arm2", (AX - 0.14, y0 + 0.02, CZ - 0.03), (AX - 0.06, y0 + 0.08, AZ + 0.12), IRON, bevel=0.006))
    # lamp house: painted body, vented cap, fins, handle, a pilot hole
    h.append(gbox("lamp_body", (AX - 0.13, y0 + 0.02, AZ - 0.13), (AX + 0.13, y0 + 0.27, AZ + 0.13), CAST, bevel=0.01, seg=2))
    h.append(gbox("lamp_cap", (AX - 0.095, y0 + 0.27, AZ - 0.095), (AX + 0.095, y0 + 0.30, AZ + 0.095), DARK, bevel=0.006))
    h.append(glathe("lamp_chimney", [(0.0, 0.0), (0.055, 0.0), (0.05, 0.05), (0.03, 0.075), (0.0, 0.08)], (AX, y0 + 0.30, AZ), axis="y", segments=14, mat=DARK))
    for i in range(5):
        h.append(gbox(f"vent{i}", (AX - 0.134, y0 + 0.08 + i * 0.035, AZ - 0.08), (AX - 0.128, y0 + 0.095 + i * 0.035, AZ + 0.08), "M_Lacquer_Black", bevel=0.0))
        h.append(gbox(f"ventr{i}", (AX + 0.128, y0 + 0.08 + i * 0.035, AZ - 0.08), (AX + 0.134, y0 + 0.095 + i * 0.035, AZ + 0.08), "M_Lacquer_Black", bevel=0.0))
    h.append(gbox("lamp_label", (AX - 0.05, y0 + 0.14, AZ + 0.13), (AX + 0.05, y0 + 0.19, AZ + 0.134), "M_Brass_Aged", bevel=0.001))
    h.append(gbox("handle", (AX - 0.10, y0 + 0.29, AZ + 0.135), (AX + 0.10, y0 + 0.31, AZ + 0.15), "M_Bakelite", bevel=0.006))
    # negative carrier: two plates with a slot for the strip (x runs along the slot), a brass pull
    h.append(gbox("car_top", (AX - 0.13, y0 - 0.002, AZ - 0.10), (AX + 0.13, y0 + 0.02, AZ + 0.10), DARK, bevel=0.002))
    h.append(gbox("car_bot", (AX - 0.13, y0 - 0.034, AZ - 0.10), (AX + 0.13, y0 - 0.012, AZ + 0.10), DARK, bevel=0.002))
    h.append(gbox("car_front", (AX - 0.13, y0 - 0.034, AZ + 0.10), (AX + 0.13, y0 + 0.02, AZ + 0.108), "M_Brass_Aged", bevel=0.002))
    h.append(gbox("car_pull", (AX + 0.13, y0 - 0.026, AZ - 0.012), (AX + 0.17, y0 + 0.0, AZ + 0.012), "M_Brass_Polished", bevel=0.002))
    # bellows: square accordion between the carrier (0.665) and the lens board (0.46)
    yb0, yb1 = 0.46, 0.665
    nf = 8
    for i in range(nf):
        ya = yb0 + (yb1 - yb0) * i / nf
        yb = yb0 + (yb1 - yb0) * (i + 1) / nf
        ym = (ya + yb) / 2
        wt = 0.085
        wi = 0.058
        h.append(gbox(f"fold{i}", (AX - wt, ya + 0.003, AZ - wt), (AX + wt, ym, AZ + wt), "M_Leather", bevel=0.004))
        h.append(gbox(f"foldb{i}", (AX - wi, ym - 0.004, AZ - wi), (AX + wi, yb - 0.003, AZ + wi), "M_Leather", bevel=0.002))
    # lens board and barrel
    h.append(gbox("lens_board", (AX - 0.10, 0.435, AZ - 0.10), (AX + 0.10, 0.462, AZ + 0.10), DARK, bevel=0.004))
    h.append(glathe("barrel", [(0.0, 0.0), (0.042, 0.0), (0.046, 0.01), (0.046, 0.045), (0.036, 0.06), (0.0, 0.06)], (AX, 0.375, AZ), axis="y", segments=22, mat="M_Lacquer_Black"))
    h.append(glathe("lens_glass", [(0.0, 0.0), (0.032, 0.0), (0.026, 0.0)], (AX, 0.373, AZ), axis="y", segments=16, mat="M_Glass"))
    h.append(glathe("lens_bulge", [(0.0, 0.0), (0.028, 0.0), (0.020, 0.008), (0.0, 0.011)], (AX, 0.367, AZ), axis="y", segments=14, mat="M_Glass_Dark"))
    h.append(gcyl("index_mark", 0.004, 0.012, (AX, 0.37, AZ + 0.047), axis="y", verts=4, mat="M_Enamel_Crimson", bevel=0.0))
    # zoom crank axle on the clamp
    h.append(gcyl("crank_axle", 0.010, 0.07, (CX - 0.11, y0 + 0.04, CZ), axis="x", verts=8, mat=DARK, bevel=0.0))
    head = part("IA_head", h, (AX, y0, AZ))

    # focus ring around the barrel: brass ring with nine ticks every 40 degrees on its top face
    fr = [glathe("ring", [(0.0455, 0.0), (0.054, 0.0), (0.055, 0.004), (0.055, 0.026), (0.054, 0.030), (0.0455, 0.030)], (AX, 0.375, AZ), axis="y", segments=36, mat="M_Brass_Aged"),
          glathe("ring_top", [(0.0455, 0.030), (0.0555, 0.030), (0.0555, 0.0325), (0.0455, 0.0325)], (AX, 0.375, AZ), axis="y", segments=36, mat="M_Brass_Polished")]
    for k in range(9):
        t = gbox(f"ftick{k}", (0.0475, 0.0, -0.0022), (0.0545, 0.0016, 0.0022), "M_Lacquer_Black", bevel=0.0)
        U.rot_godot([t], "y", 40.0 * k, (0, 0, 0))
        U.move([t], (AX, 0.375 + 0.0325, AZ))
        fr.append(t)
    ring_part = part("IA_focus_ring", fr, (AX, 0.375, AZ))

    # crank knob
    kn_o = [gcyl("kn_stem", 0.008, 0.045, (CX - 0.15, y0 + 0.04, CZ), axis="x", verts=8, mat=DARK, bevel=0.0)]
    kn_o.append(glathe("kn_disc", [(0.0, 0.0), (0.050, 0.0), (0.052, 0.006), (0.052, 0.014), (0.0, 0.016)], (CX - 0.185, y0 + 0.04, CZ), axis="x", segments=18, mat="M_Bakelite"))
    kn_o.append(gcyl("kn_handle", 0.011, 0.045, (CX - 0.205, y0 + 0.04 + 0.032, CZ), axis="x", verts=8, mat="M_Bakelite", bevel=0.002))
    knob = part("IA_zoom_knob", kn_o, (CX - 0.11, y0 + 0.04, CZ))

    # projected image quad
    X.decal("M_Decal_Prints", "print_proj.png")
    img = gquad("projected_image", (AX, 0.0345, AZ), (1, 0, 0), (0, 0, -1), 0.20, 0.15, "M_Decal_Prints")
    img = part("projected_image", [img], (AX, 0.0345, AZ), presmooth=False)
    mount("strip_slot", (AX, y0 - 0.0215 + 0.012, AZ))
    mount("light_origin_enlarger", (AX, 0.40, AZ))
    return body, head, ring_part, knob, img


if __name__ == "__main__":
    build()
    req = ["enlarger_body", "IA_head", "IA_zoom_knob", "IA_focus_ring", "strip_slot", "projected_image", "light_origin_enlarger"]
    errs = X.finish(NAME, req, ["IA_head", "IA_zoom_knob", "IA_focus_ring", "projected_image"], BUDGET,
                    {"IA_head": (AX, 0.70, AZ), "IA_focus_ring": (AX, 0.375, AZ), "IA_zoom_knob": (CX - 0.11, 0.74, CZ)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.15, 0.95, 1.55), (0.0, 0.58, 0.0), 44), ("_lens", (0.35, 0.55, 0.65), (0.05, 0.45, 0.10), 42)], floor=True, world=0.2)
