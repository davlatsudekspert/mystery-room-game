"""light_table.glb — the light table of the Night Cell desk (puzzle N3 "Light table", the new mechanic M14).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N3). A wooden drafting lightbox: a walnut case with brass corner guards, an opal-glass
top lit from inside (`table_glow`), a brass bezel with four corner marks that fix the reference corner, a raised back panel with a
bakelite rocker switch and a pilot lamp, rubber feet and a cloth cord. The 11 x 7 cell window (two 5 x 7 digits side by side) is a
quad `table_mask` on the glass, 0.242 (x) x 0.154 (z), cell pitch 0.022 m, columns along X, rows along Z (row 0 at the back). Three square
acetate sheets (`acetate_sheet_a/b/c`, 0.26 x 0.26) stack on the glass: `sheet_mount_0..2` are the slots.

Model space (Godot): front +Z, origin on the desk surface at the footprint centre. Footprint 0.42 (x) x 0.42 (z), a 5.6 cm front ledge with a brass ruler edge; case top 0.055, glass top 0.0585.
Suggested placement in `room_cell`: on the desk at (1.30, 0.78, -1.62), yaw 0.

Parts:
  light_table_body   everything static (case, bezel with corner marks, back panel, lamp housing, feet, cord)
  table_glow         the opal glass, M_Emissive_Table (hide / dim = lamp off), origin = centre of the glass (0, 0.0585, 0.02)
  table_mask         0.242 x 0.154 quad on the glass (y 0.0592), M_Decal_TableMask, UV 0..1; the code draws the lit cells, origin (0, 0.0592, 0.02)
  IA_switch          bakelite rocker on the back panel, pivot (0.145, 0.083, -0.1165); off = rest, ON = -25 deg about +X (the rocker top tips toward the back)
  pilot_lamp         red/amber jewel (M_Emissive_Warm), origin (0.095, 0.083, -0.1185); show when the table is on
  sheet_mount_0..2   empties on the glass, y 0.0615 + 0.0030 k, centre z 0.02; each is rotated -90 deg about +X so a sheet model (built upright, front +Z)
                     lies flat with its front up and its local +Z = world up. Rotating a sheet = rotating about the sheet's local +Z
  light_table_light  empty (0, 0.20, 0.02): a warm OmniLight so the desk is lit from the table

    blender -b --factory-startup -P tools/blender/models/light_table.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "light_table"
BUDGET = 4200
ARGS = M.main_guard()
WOOD, BRASS, BAKE = "M_Wood_Walnut", "M_Brass_Aged", "M_Bakelite"
CASE_TOP, GLASS_Y = 0.055, 0.0585
GZ = 0.02                                     # glass centre z
GH = 0.14                                     # glass half size
WIN_W, WIN_H = 0.242, 0.154
SW = (0.145, 0.083, -0.1165)                   # switch pivot


def body():
    o = []
    # case: walnut box, a lower plinth step, and the raised back housing with the lamp
    o.append(gbox("plinth", (-0.205, 0.010, -0.180), (0.205, 0.024, 0.218), "M_Wood_Panel", bevel=0.003))
    o.append(gbox("case", (-0.210, 0.024, -0.190), (0.210, CASE_TOP, 0.226), WOOD, bevel=0.006, seg=2))
    o.append(gbox("back_house", (-0.210, CASE_TOP, -0.190), (0.210, 0.098, -0.118), WOOD, bevel=0.006, seg=2))
    o.append(gbox("back_plate", (-0.205, 0.062, -0.1185), (0.205, 0.094, -0.1175), BRASS, bevel=0.0))
    # bezel: brass frame round the glass (4 strips), 3.5 mm proud
    bz0, bz1 = GZ - GH - 0.010, GZ + GH + 0.010
    o.append(gbox("bz_n", (-GH - 0.010, CASE_TOP - 0.002, bz0), (GH + 0.010, CASE_TOP + 0.0075, bz0 + 0.010), BRASS, bevel=0.0015))
    o.append(gbox("bz_s", (-GH - 0.010, CASE_TOP - 0.002, bz1 - 0.010), (GH + 0.010, CASE_TOP + 0.0075, bz1), BRASS, bevel=0.0015))
    o.append(gbox("bz_w", (-GH - 0.010, CASE_TOP - 0.002, bz0 + 0.010), (-GH, CASE_TOP + 0.0075, bz1 - 0.010), BRASS, bevel=0.0015))
    o.append(gbox("bz_e", (GH, CASE_TOP - 0.002, bz0 + 0.010), (GH + 0.010, CASE_TOP + 0.0075, bz1 - 0.010), BRASS, bevel=0.0015))
    # corner marks: small brass triangles pointing at the glass corners; the reference corner (back left) has a crimson dot
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (GH + 0.0095), GZ + sz * (GH + 0.0095)
            o.append(gbox(f"mk{sx}{sz}", (cx - 0.0065, CASE_TOP + 0.0075, cz - 0.0065), (cx + 0.0065, CASE_TOP + 0.0095, cz + 0.0065), "M_Brass_Polished", bevel=0.0))
    o.append(gcyl("ref_dot", 0.0048, 0.0015, (-GH - 0.0095, CASE_TOP + 0.0095, GZ - GH - 0.0095), axis="y", verts=10, mat="M_Enamel_Crimson", bevel=0.0))
    # front ledge: a brass ruler strip with tick marks (1 cm), so the table reads as a drafting tool
    o.append(gbox("ruler", (-0.185, CASE_TOP - 0.001, 0.188), (0.185, CASE_TOP + 0.0025, 0.216), "M_Brass_Polished", bevel=0.0012))
    for i in range(38):
        ln = 0.014 if i % 5 == 0 else 0.008
        x = -0.185 + 0.01 * i + 0.0025
        o.append(gbox(f"rt{i}", (x - 0.0006, CASE_TOP + 0.0025, 0.216 - ln), (x + 0.0006, CASE_TOP + 0.0030, 0.216), "M_Lacquer_Black", bevel=0.0))
    # brass corner guards on the case and four rubber feet
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * 0.2075, (0.2265 if sz > 0 else -0.1895)
            o.append(gbox(f"cg{sx}{sz}", (cx - 0.012, 0.024, cz - 0.012), (cx + 0.012, CASE_TOP + 0.001, cz + 0.012), BRASS, bevel=0.002))
    for x in (-0.17, 0.17):
        for z in (-0.15, 0.19):
            o.append(gcyl(f"foot{x}{z}", 0.016, 0.010, (x, 0.0, z), axis="y", verts=10, mat="M_Rubber", bevel=0.0, r_top=0.014))
    # back panel hardware: switch base plate, lamp housing, small ventilation slots, a maker's label
    o.append(gbox("sw_base", (SW[0] - 0.020, 0.066, -0.1195), (SW[0] + 0.020, 0.096, -0.1115), BAKE, bevel=0.003))
    o.append(gcyl("lamp_ring", 0.012, 0.007, (0.095, 0.083, -0.1195), axis="z", verts=14, mat="M_Brass_Polished", bevel=0.0015))
    for i in range(6):
        o.append(gbox(f"vent{i}", (-0.17 + i * 0.020, 0.071, -0.1195), (-0.17 + i * 0.020 + 0.010, 0.088, -0.1186), "M_Lacquer_Black", bevel=0.0))
    o.append(gbox("label", (-0.020, 0.072, -0.1195), (0.050, 0.086, -0.1188), "M_Enamel_Cream", bevel=0.0))
    # cord from the back left, with a strain relief
    o.append(gbox("relief", (-0.178, 0.040, -0.197), (-0.158, 0.056, -0.186), BAKE, bevel=0.003))
    o.append(X.pipe("cord", [(-0.168, 0.048, -0.197), (-0.168, 0.030, -0.260), (-0.20, 0.004, -0.320), (-0.30, 0.004, -0.400)], 0.0045, mat="M_Fabric", sides=6,
                    fillet=0.06, flange_ends=False))
    return o


def glow_parts():
    glass = gbox("glass", (-GH, GLASS_Y - 0.004, GZ - GH), (GH, GLASS_Y, GZ + GH), "M_Emissive_Table", bevel=0.0)
    glow = part("table_glow", [glass], (0.0, GLASS_Y, GZ), presmooth=False)
    mask = gquad("table_mask", (0.0, GLASS_Y + 0.0007, GZ), (1, 0, 0), (0, 0, -1), WIN_W, WIN_H, "M_Decal_TableMask")
    mk = part("table_mask", [mask], (0.0, GLASS_Y + 0.0007, GZ), presmooth=False)
    return glow, mk


def switch():
    o = [gbox("rocker", (SW[0] - 0.012, SW[1] - 0.004, SW[2] - 0.0095), (SW[0] + 0.012, SW[1] + 0.004, SW[2] + 0.0095), BAKE, bevel=0.0025),
         gbox("rocker_lip", (SW[0] - 0.012, SW[1] - 0.004, SW[2] + 0.005), (SW[0] + 0.012, SW[1] + 0.006, SW[2] + 0.0095), "M_Brass_Polished", bevel=0.0015)]
    return part("IA_switch", o, SW)


def lamp():
    j = glathe("jewel", [(0.0, 0.0), (0.008, 0.0), (0.0085, 0.002), (0.0065, 0.0065), (0.0, 0.0075)], (0.095, 0.083, -0.1185), axis="z", segments=12,
               mat="M_Emissive_Warm")
    return part("pilot_lamp", [j], (0.095, 0.083, -0.1185), presmooth=False)


def main():
    X.begin()
    Q.alpha_decal("M_Decal_TableMask", "table_mask.png")
    glow, mk = glow_parts()
    sw = switch()
    pl = lamp()
    b = body()
    X.top(b)
    part("light_table_body", b, (0, 0, 0))
    rot = Matrix.Rotation(math.radians(-90.0), 4, "X")
    for k in range(3):
        mount(f"sheet_mount_{k}", (0.0, 0.0615 + 0.003 * k, GZ), rot_blender=rot)
    mount("light_table_light", (0.0, 0.20, GZ))
    return glow, mk, sw, pl


if __name__ == "__main__":
    main()
    req = ["light_table_body", "table_glow", "table_mask", "IA_switch", "pilot_lamp", "sheet_mount_0", "sheet_mount_1", "sheet_mount_2", "light_table_light"]
    errs = X.finish(NAME, req, ["table_glow", "table_mask", "IA_switch"], BUDGET,
                    {"IA_switch": SW, "table_glow": (0.0, GLASS_Y, GZ), "table_mask": (0.0, GLASS_Y + 0.0007, GZ)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.45, 0.50, 0.62), (0.0, 0.04, 0.0), 40), ("_top", (0.0, 0.85, 0.45), (0.0, 0.05, 0.0), 36),
                          ("_back", (0.35, 0.28, -0.60), (0.0, 0.05, -0.05), 40)], floor=True, world=0.15)
