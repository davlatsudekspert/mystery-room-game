"""film_splicer.glb — projection-booth film editing bench (Chapter 2, Records Archive B; group B2).

A fire-safe steel booth workbench 1.20 x 0.60, top y = 0.90, standing against the booth's south wall.
Model space = Godot axes: origin on the floor at the centre of the back face (the wall plane), front +Z
(toward the player / north once placed with yaw 180 at world (-3.9, 0, 3.5)).

On the bench (left half -> right half as the player sees it):
  * a walnut light box with an opal glass top (`light_box_glass`, glows via code) carrying the four loose
    35 mm film strips `IA_frame_0..3` (scattered, k = 0..3 left -> right);
  * a black cast-iron butt-splicing block: a chrome film channel with four brass gate plates `IA_slot_0..3`
    (left -> right, pitch 0.15 so four placed strips form one continuous film), hinged pressure clamps
    standing open behind them, guide rollers at both ends; `slot_mount_<s>` where a strip lies when placed;
  * a rewind with a horizontal spindle toward the player: `splicer_reel_mount` (film_reel on edge, face +Z);
  * an open, empty reel can with a curl of torn leader inside, its lid `reel_can_lid` propped against the
    wall facing the player: the lid's top face is a disc with planar UV 0..1 (M_Decal_ReelCanLid, sunrise ->
    high sun) — puzzle-critical, legible from the splicer view;
  * a film-cement bottle, scissors and a china-marker (dressing); drawers and a lower shelf with film cans.

IA_frame_<k>: built straight along local X (0.15 x 0.05, UV 0..1 top quad, M_Decal_FilmStrip_<k>, film-base
underside). The scatter is the node's REST rotation (a small yaw about +Y) — the only rest rotation that is not
identity — so a strip moved onto `slot_mount_<s>` (identity rotation) lies straight in the channel.

    blender -b --factory-startup -P tools/blender/models/film_splicer.py [-- --no-render] [--shots a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_ch2_furniture2 as F  # noqa: E402
from lib_ch2_furniture2 import G  # noqa: E402

NAME = "film_splicer"
ARGS = M.main_guard()
BUDGET = 8000

TOP = 0.90                    # bench top
W2 = 0.60                     # half width
D = 0.60                      # depth (z from the wall 0 to the front 0.60)
GLASS_Y = 0.950               # light-box glass top
GLASS = (-0.560, -0.060, 0.165, 0.505)        # x0, x1, z0, z1
LB = (-0.585, -0.035, 0.140, 0.530)           # light-box body footprint
STRIPS = [(-0.465, 0.405, -6.0), (-0.355, 0.262, 5.0), (-0.255, 0.425, -3.0), (-0.150, 0.275, 7.0)]
STRIP_L, STRIP_W = 0.15, 0.05
SLOT_X = [0.065 + 0.15 * s for s in range(4)]
CH_Z = 0.45                   # film channel centre line
PLATE_TOP = 0.931
REEL = (0.45, 1.05, 0.266)    # splicer_reel_mount (reel centre; reel face plane z 0.256..0.276)
CAN = (0.20, TOP, 0.20)
LID_TILT = 14.0               # lid leans back from vertical against the wall
LID_R = 0.100

parts = {}


def S(lst, *objs):
    lst.extend(o for o in objs if o is not None)


# ------------------------------------------------------------------ bench
def build_bench():
    b = []
    # cream-enamelled steel top with a dark rolled nosing along the front
    S(b, F.gbox("top", (-W2, 0.874, 0.0), (W2, TOP, D - 0.004), mat="M_Steel_Cream", bevel=0.004, seg=1))
    S(b, F.gbox("nosing", (-W2 - 0.002, 0.871, D - 0.006), (W2 + 0.002, TOP + 0.0015, D + 0.004), mat="M_Steel_Dark",
                bevel=0.0025, seg=1))
    for sx in (-1, 1):
        S(b, F.gbox(f"nosing_end{sx}", (sx * W2 - 0.002 if sx < 0 else W2 - 0.004, 0.871, 0.0),
                    (sx * W2 + 0.004 if sx < 0 else W2 + 0.002, TOP + 0.0015, D - 0.004), mat="M_Steel_Dark",
                    bevel=0.002))
    # square-tube legs on rubber feet
    for (x, z) in ((-0.565, 0.035), (0.565, 0.035), (-0.565, 0.565), (0.565, 0.565)):
        S(b, F.gbox(f"leg_{x:+.2f}_{z:.2f}", (x - 0.0175, 0.012, z - 0.0175), (x + 0.0175, 0.874, z + 0.0175),
                    mat="M_Steel_Painted", bevel=0.004, seg=1))
        S(b, F.gcyl(f"foot_{x:+.2f}_{z:.2f}", 0.016, 0.012, (x, 0.0, z), verts=8, mat="M_Rubber", bevel=0.0))
    # aprons (back and sides) and a centre stile between the two drawers
    S(b, F.gbox("apron_back", (-0.548, 0.80, 0.022), (0.548, 0.874, 0.040), mat="M_Steel_Painted", bevel=0.003))
    for sx in (-1, 1):
        S(b, F.gbox(f"apron_side{sx}", (sx * 0.558 - 0.009, 0.80, 0.053), (sx * 0.558 + 0.009, 0.874, 0.547),
                    mat="M_Steel_Painted", bevel=0.003))
    S(b, F.gbox("stile", (-0.032, 0.79, 0.548), (0.032, 0.874, 0.584), mat="M_Steel_Painted", bevel=0.003))
    S(b, F.gbox("drawer_rail", (-0.548, 0.786, 0.548), (0.548, 0.800, 0.580), mat="M_Steel_Painted", bevel=0.003))
    for i, sx in enumerate((-1, 1)):
        x0, x1 = (sx * 0.040, sx * 0.540) if sx > 0 else (sx * 0.540, sx * 0.040)
        cx = (x0 + x1) / 2
        S(b, F.gbox(f"drawer_{i}", (x0, 0.802, 0.560), (x1, 0.868, 0.584), mat="M_Steel_Painted", bevel=0.004, seg=1))
        S(b, *F.bar_pull(f"drawer_pull_{i}", (cx + 0.05, 0.835, 0.584), length=0.10, r=0.0040, stand=0.018))
        S(b, *F.card_holder(f"drawer_label_{i}", (cx - 0.13, 0.835, 0.584), w=0.056, h=0.026))
    # lower shelf with a rolled front lip, and its film-can dressing
    S(b, F.gbox("shelf", (-0.548, 0.150, 0.053), (0.548, 0.166, 0.547), mat="M_Steel_Painted", bevel=0.003))
    S(b, F.gbox("shelf_lip", (-0.548, 0.150, 0.540), (0.548, 0.186, 0.552), mat="M_Steel_Painted", bevel=0.004))
    S(b, F.gbox("shelf_lip_back", (-0.548, 0.150, 0.048), (0.548, 0.186, 0.060), mat="M_Steel_Painted", bevel=0.004))
    y = 0.166
    for i, (dx, dz, h, mat) in enumerate(((0.0, 0.0, 0.034, "M_Steel_Painted"), (0.006, -0.004, 0.034, "M_Steel_Dark"))):
        S(b, can_shape(f"shelf_can_{i}", (-0.30 + dx, y, 0.30 + dz), 0.098, h, mat, segs=18))
        y += h
    S(b, F.gbox("shelf_box", (0.16, 0.166, 0.15), (0.50, 0.29, 0.47), mat="M_Cardboard", bevel=0.004, seg=1))
    S(b, F.gbox("shelf_box_lid", (0.155, 0.27, 0.145), (0.505, 0.296, 0.475), mat="M_Cardboard", bevel=0.003))
    S(b, F.gbox("shelf_box_label", (0.27, 0.205, 0.475), (0.39, 0.25, 0.4765), mat="M_Paper", bevel=0.0))
    parts["bench"] = F.part("bench", b)


def can_shape(name, base, r, h, mat, segs=28):
    """Closed film can (lid on): pressed rim bead and a slightly domed lid ring."""
    prof = [(0.0, 0.0), (r - 0.002, 0.0), (r, 0.003), (r + 0.0012, h * 0.5), (r, h - 0.003), (r - 0.003, h),
            (0.0, h)]
    return F.glathe(name, prof, base, segments=segs, mat=mat, smooth=50.0)


# ------------------------------------------------------------------ light box
def build_light_box():
    x0, x1, z0, z1 = LB
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    lb = []
    S(lb, F.gbox("lb_body", (x0, TOP, z0), (x1, 0.946, z1), mat="M_Wood_Walnut", bevel=0.005, seg=1))
    gx0, gx1, gz0, gz1 = GLASS
    gw, gd = gx1 - gx0, gz1 - gz0
    S(lb, F.gslab("lb_bezel", (cx, 0.9455, cz), x1 - x0 - 0.008, z1 - z0 - 0.008, 0.0065, r=0.010, mat="M_Steel_Dark",
                  hole=(gw, gd, 0.004, (gx0 + gx1) / 2 - cx, -((gz0 + gz1) / 2 - cz)), bevel=0.0012))
    # bezel screws
    for (x, z) in ((x0 + 0.012, z0 + 0.012), (x1 - 0.012, z0 + 0.012), (x0 + 0.012, z1 - 0.012), (x1 - 0.012, z1 - 0.012)):
        S(lb, F.screw(f"lb_screw_{x:.2f}_{z:.2f}", 0.0028, (x, 0.952, z), "y", mat="M_Chrome"))
    # toggle switch on the front face and an enamel maker's plate
    S(lb, F.gslab("lb_switch_plate", (x0 + 0.05, 0.923, z1), 0.032, 0.026, 0.0018, r=0.004, mat="M_Chrome", plane="xy",
                  bevel=0.0, n=3))
    sw = F.gcyl("lb_switch_bat", 0.0026, 0.016, (x0 + 0.05, 0.923, z1 + 0.0018), axis=(0, 0.45, 1.0), verts=10,
                mat="M_Chrome", bevel=0.0, r_top=0.0018)
    S(lb, sw, F.gcyl("lb_switch_nut", 0.0052, 0.003, (x0 + 0.05, 0.923, z1 + 0.0018), axis="z", verts=6, mat="M_Chrome",
                     bevel=0.0005))
    # cloth flex from the back, dropping behind the bench
    S(lb, F.gtube("lb_flex", [(x0 + 0.04, 0.912, z0), (x0 + 0.04, 0.905, z0 - 0.04), (x0 + 0.02, 0.903, z0 - 0.09),
                              (x0 - 0.006, 0.905, 0.012), (x0 - 0.010, 0.88, 0.008), (x0 - 0.010, 0.70, 0.008)],
                  0.0032, sides=5, mat="M_Fabric"))
    parts["light_box"] = F.part("light_box", lb)
    glass = F.gbox("light_box_glass", (gx0 + 0.0005, 0.9435, gz0 + 0.0005), (gx1 - 0.0005, GLASS_Y, gz1 - 0.0005),
                   mat="M_Glass_Frosted", bevel=0.0008)
    parts["glass"] = F.part("light_box_glass", [glass], pivot=((gx0 + gx1) / 2, GLASS_Y, (gz0 + gz1) / 2))


# ------------------------------------------------------------------ film strips
def build_strips():
    parts["strips"] = []
    for k, (x, z, yaw) in enumerate(STRIPS):
        mat = F.decal_material(f"M_Decal_FilmStrip_{k}", f"film_strip_{k}.png", color="4A3424", rough=0.22)
        top = F.gquad(f"strip_face_{k}", (0, 0.0001, 0), (1, 0, 0), (0, 0, -1), STRIP_L, STRIP_W, mat.name)
        bot = F.gquad(f"strip_base_{k}", (0, -0.0001, 0), (1, 0, 0), (0, 0, 1), STRIP_L, STRIP_W, "M_Film", uv=False)
        o = F.part(f"IA_frame_{k}", [top, bot], pivot=(0, 0, 0), presmooth=False)
        o.location = G(x, GLASS_Y + 0.0003, z)
        o.rotation_euler = (0.0, 0.0, math.radians(yaw))
        parts["strips"].append(o)


# ------------------------------------------------------------------ splicing block
def build_block():
    bl = []
    xa, xb = -0.022, 0.598
    S(bl, F.gbox("blk_base", (xa, TOP, 0.372), (xb, 0.918, 0.528), mat="M_Lacquer_Black", bevel=0.006, seg=1))
    S(bl, F.gbox("blk_deck", (xa + 0.006, 0.917, 0.380), (xb - 0.006, 0.924, 0.520), mat="M_Lacquer_Black", bevel=0.003,
                 seg=1))
    S(bl, F.gbox("blk_bed", (xa + 0.008, 0.9235, CH_Z - 0.027), (xb - 0.008, 0.929, CH_Z + 0.027), mat="M_Chrome",
                 bevel=0.0008))
    for i, (z0, z1) in enumerate(((CH_Z - 0.045, CH_Z - 0.027), (CH_Z + 0.027, CH_Z + 0.045))):
        S(bl, F.gbox(f"blk_rail{i}", (xa + 0.008, 0.9235, z0), (xb - 0.008, 0.9365, z1), mat="M_Chrome", bevel=0.0012))
    # cut marks between the gates (engraved lines on the rails) and guide rollers at both ends
    for s in range(5):
        x = SLOT_X[0] - 0.075 + 0.15 * s
        for z in (CH_Z - 0.036, CH_Z + 0.036):
            S(bl, F.gbox(f"blk_mark_{s}_{z:.3f}", (x - 0.0006, 0.9366, z - 0.008), (x + 0.0006, 0.9369, z + 0.008),
                         mat="M_Lacquer_Black", bevel=0.0))
    for x in (xa + 0.010, xb - 0.010):
        for z in (CH_Z - 0.058, CH_Z + 0.058):
            S(bl, F.glathe(f"blk_roller_{x:.2f}_{z:.2f}", [(0.0, 0.0), (0.0065, 0.0), (0.0055, 0.004), (0.0055, 0.014),
                                                         (0.0068, 0.016), (0.0, 0.018)],
                           (x, 0.924, z), segments=10, mat="M_Chrome"))
    # hinged pressure clamps standing open behind each gate (hinge knuckles on the back rail)
    for s, x in enumerate(SLOT_X):
        hz, hy = CH_Z - 0.047, 0.9375
        S(bl, F.gcyl(f"blk_knuckle_{s}", 0.0032, 0.12, (x - 0.06, hy, hz), axis="x", verts=8, mat="M_Chrome",
                     bevel=0.0))
        clamp = F.gbox(f"blk_clamp_{s}", (x - 0.064, 0.0, -0.0022), (x + 0.064, 0.034, 0.0022), mat="M_Chrome",
                       bevel=0.0012, seg=1)
        knob = F.gcyl(f"blk_clamp_knob_{s}", 0.0045, 0.008, (x, 0.031, 0.0022), axis="z", verts=8, mat="M_Bakelite",
                      bevel=0.0)
        pad = F.gbox(f"blk_clamp_pad_{s}", (x - 0.058, 0.004, 0.0022), (x + 0.058, 0.030, 0.0034), mat="M_Felt",
                     bevel=0.0006)
        for o in (clamp, knob, pad):
            F.bake_xform(o, pitch=-32.0, about=(x, 0.0, 0.0))    # opened past vertical, leaning back toward the wall
            o.location = G(0.0, hy, hz - 0.002)
            M.apply_transform(o)
        S(bl, clamp, knob, pad)
    # brass maker's plate on the front face
    S(bl, F.gslab("blk_plate", (0.288, 0.909, 0.528), 0.11, 0.0125, 0.0012, r=0.002, mat="M_Brass_Aged", plane="xy",
                  bevel=0.0, n=2))
    S(bl, F.gtext("blk_plate_txt", "35 mm", 0.0085, (0.288, 0.9062, 0.5293), facing="z", mat="M_Lacquer_Black"))
    for x in (0.288 - 0.049, 0.288 + 0.049):
        S(bl, F.screw(f"blk_plate_screw_{x:.3f}", 0.0018, (x, 0.909, 0.5292), "z", mat="M_Brass_Aged"))
    parts["block"] = F.part("splice_block", bl)
    # gate plates: the tap targets
    parts["slots"] = []
    for s, x in enumerate(SLOT_X):
        pl = [F.gbox(f"slot_plate_{s}", (x - 0.0725, 0.929, CH_Z - 0.026), (x + 0.0725, PLATE_TOP, CH_Z + 0.026),
                     mat="M_Brass_Polished", bevel=0.0006)]
        for dx in (-0.062, 0.062):
            for dz in (-0.018, 0.018):
                pl.append(F.gdisc(f"slot_pin_{s}_{dx}_{dz}", (x + dx, PLATE_TOP + 0.00015, CH_Z + dz), 0.0016, normal="y",
                                  up="-z", mat="M_Steel_Dark", n=8))
        o = F.part(f"IA_slot_{s}", pl, pivot=(x, PLATE_TOP, CH_Z))
        parts["slots"].append(o)
    parts["slot_mounts"] = [F.mount(f"slot_mount_{s}", (x, PLATE_TOP + 0.0008, CH_Z)) for s, x in enumerate(SLOT_X)]


# ------------------------------------------------------------------ rewind
def build_rewind():
    rw = []
    x, yc, zr = REEL
    S(rw, F.gbox("rw_base", (x - 0.055, TOP, 0.070), (x + 0.055, 0.914, 0.205), mat="M_Lacquer_Black", bevel=0.005, seg=1))
    for (dx, dz) in ((-0.042, 0.082), (0.042, 0.082), (-0.042, 0.193), (0.042, 0.193)):
        S(rw, F.screw(f"rw_bolt_{dx}_{dz}", 0.0038, (x + dx, 0.914, dz), "y", mat="M_Steel_Dark", slot=0.0))
    # tapered cast column
    col = F.gpoly("rw_column", [[(-0.024, 0.0), (0.024, 0.0), (0.016, 0.124), (-0.016, 0.124)]], 0.05,
                  (x, 0.914, 0.105), (1, 0, 0), (0, 1, 0), mat="M_Lacquer_Black", bevel=0.003)
    S(rw, col)
    # gear housing along Z with a chrome front boss, the spindle, a flange and a knurled retaining nut
    S(rw, F.glathe("rw_housing", [(0.0, 0.0), (0.028, 0.0), (0.033, 0.006), (0.034, 0.066), (0.030, 0.074), (0.018, 0.077),
                                  (0.0, 0.077)], (x, yc, 0.098), axis="z", segments=24, mat="M_Lacquer_Black"))
    S(rw, F.glathe("rw_boss", [(0.0, 0.0), (0.017, 0.0), (0.017, 0.008), (0.012, 0.012), (0.0, 0.012)], (x, yc, 0.175),
                   axis="z", segments=20, mat="M_Chrome"))
    S(rw, F.gcyl("rw_shaft", 0.0055, 0.115, (x, yc, 0.185), axis="z", verts=10, mat="M_Chrome", bevel=0.0))
    S(rw, F.glathe("rw_flange", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.003), (0.012, 0.006), (0.0, 0.006)],
                   (x, yc, zr - 0.010 - 0.006), axis="z", segments=24, mat="M_Chrome"))
    S(rw, F.glathe2("rw_nut", [(0.0, 0.0), (0.0085, 0.0), (0.0092, 0.002, "k"), (0.0092, 0.011, "k"), (0.008, 0.013),
                               (0.0, 0.013)], (x, yc, zr + 0.012), axis="z", segments=20, mat="M_Chrome", knurl=0.0007))
    # crank at the back: arm + turned wooden handle pointing at the wall
    S(rw, F.gcyl("rw_crank_hub", 0.009, 0.012, (x, yc, 0.086), axis="z", verts=12, mat="M_Chrome", bevel=0.0))
    arm = F.gpoly("rw_crank_arm", [[(0.0, -0.007), (0.062, -0.005), (0.062, 0.005), (0.0, 0.007)]], 0.005,
                  (x, yc, 0.083), (math.cos(math.radians(40)), math.sin(math.radians(40)), 0), (-math.sin(math.radians(40)),
                                                                                                 math.cos(math.radians(40)), 0),
                  mat="M_Chrome", bevel=0.0012)
    S(rw, arm)
    hx, hy = x + 0.062 * math.cos(math.radians(40)), yc + 0.062 * math.sin(math.radians(40))
    S(rw, F.glathe("rw_crank_grip", [(0.0, 0.0), (0.004, 0.0), (0.0065, 0.006), (0.0075, 0.022), (0.0068, 0.034),
                                     (0.0045, 0.040), (0.0, 0.041)], (hx, hy, 0.083), axis="-z", segments=12,
                   mat="M_Wood_Walnut"))
    parts["rewind"] = F.part("rewind", rw)
    parts["reel_mount"] = F.mount("splicer_reel_mount", REEL)


# ------------------------------------------------------------------ reel can, film curl, propped lid
def build_can():
    cx, cy, cz = CAN
    r = 0.098
    prof = [(0.0, 0.0), (r - 0.003, 0.0), (r, 0.003), (r, 0.026), (r + 0.0016, 0.0285), (r - 0.0004, 0.0300),
            (r - 0.0016, 0.0275), (r - 0.0016, 0.0035), (r - 0.012, 0.0022), (r - 0.014, 0.0034),
            (r - 0.017, 0.0022), (0.0, 0.0022)]
    can = [F.glathe("can_body", prof, CAN, segments=24, mat="M_Steel_Painted", smooth=50.0)]
    # a curl of torn film leader lying in the empty can (16/35 mm on edge, slack spiral)
    path = F.spiral(cx + 0.006, cz - 0.004, cy + 0.0023, 0.030, 0.082, 1.15, 26, phase=0.6)
    can.append(F.ribbon("can_film_curl", path, 0.016, mat="M_Film"))
    tail = [(path[-1][0], path[-1][1], path[-1][2]), (cx + 0.07, cy + 0.0023, cz + 0.07), (cx + 0.035, cy + 0.0023,
                                                                                           cz + 0.085)]
    can.append(F.ribbon("can_film_tail", tail, 0.016, mat="M_Film"))
    parts["can"] = F.part("reel_can", can)
    # lid (built face-up at the origin, image top toward -Z, then stood up against the wall)
    t = math.radians(LID_TILT)
    lip = 0.010
    lid_prof = [(0.0, -0.0008), (LID_R - 0.0025, -0.0008), (LID_R - 0.0028, -lip + 0.0012), (LID_R - 0.0012, -lip),
                (LID_R + 0.0008, -lip + 0.0012), (LID_R + 0.0008, -0.0016), (LID_R - 0.0004, 0.0), (0.0, 0.0)]
    shell = F.glathe("lid_shell", lid_prof, (0, 0, 0), segments=36, mat="M_Steel_Painted", smooth=50.0)
    face = F.gdisc("lid_face", (0, 0.00025, 0), LID_R - 0.0006, normal="y", up="-z",
                   mat=F.decal_material("M_Decal_ReelCanLid", "reel_can_lid.png", color="5E6A60", rough=0.5).name, n=36)
    lid = F.part("reel_can_lid", [shell, face], pivot=(0, 0, 0))
    lid.data.transform(F.gmat(pitch=90.0 - LID_TILT))
    n = Vector((0.0, math.sin(t), math.cos(t)))
    u = Vector((0.0, math.cos(t), -math.sin(t)))
    cy_ = TOP + lip * n.y + LID_R * u.y + 0.0004
    cz_ = lip * n.z + LID_R * math.sin(t) + 0.0015
    lid.location = G(cx, cy_, cz_)
    parts["lid"] = lid
    parts["lid_centre"] = (cx, cy_, cz_)


# ------------------------------------------------------------------ dressing: cement, scissors, marker
def build_dressing():
    dr = []
    bx, bz = 0.035, 0.305
    S(dr, F.glathe("cement_bottle", [(0.0, 0.0), (0.0165, 0.0), (0.0178, 0.003), (0.0178, 0.038), (0.0150, 0.046),
                                     (0.0090, 0.052), (0.0085, 0.058), (0.0, 0.058)], (bx, TOP, bz), segments=16,
                   mat="M_Glass_Amber", smooth=50.0))
    S(dr, F.glathe("cement_label", [(0.0181, 0.010), (0.0181, 0.031)], (bx, TOP, bz), segments=16, mat="M_Paper",
                   smooth=50.0))
    S(dr, F.glathe2("cement_cap", [(0.0, 0.0), (0.0098, 0.0), (0.0102, 0.002, "k"), (0.0102, 0.013, "k"), (0.0085, 0.016),
                                   (0.0035, 0.017), (0.0035, 0.024), (0.0, 0.025)], (bx, TOP + 0.056, bz), segments=12,
                    mat="M_Bakelite", knurl=0.0006))
    # scissors lying on the bench front strip (left half)
    sx, sz, ang = -0.30, 0.565, -12.0
    sc = []
    for i, side in enumerate((-1, 1)):
        blade = F.gpoly(f"sc_blade{i}", [[(0.0, -0.0035 * side), (0.020, -0.0050 * side), (0.088, -0.0008 * side),
                                          (0.090, 0.0003 * side), (0.020, 0.0012 * side), (0.0, 0.0010 * side)]],
                        0.0016, (0.0, TOP + 0.0006 + i * 0.0016, 0.0), (1, 0, 0), (0, 0, -1), mat="M_Chrome",
                        bevel=0.0004)
        sc.append(blade)
        loop = K.ring_band(f"sc_loop{i}", 0.0085, 0.0125, 0.0045, segments=10, mat="M_Bakelite", chamfer=0.0012)
        loop.data.transform(Matrix.Translation((-0.040, -side * 0.016, 0.0)))
        loop.location = G(0.0, TOP + 0.0023 + i * 0.0010, 0.0)
        M.apply_transform(loop)
        shank = F.gbox(f"sc_shank{i}", (-0.030, TOP + 0.0006 + i * 0.0016, -0.002 + side * 0.006),
                       (0.002, TOP + 0.0034 + i * 0.0016, 0.002 + side * 0.006), mat="M_Bakelite", bevel=0.0008)
        sc += [loop, shank]
    sc.append(F.gcyl("sc_pivot", 0.0028, 0.0042, (0.0, TOP + 0.0006, 0.0), verts=8, mat="M_Chrome", bevel=0.0))
    for o in sc:
        F.bake_xform(o, yaw=ang)
        o.location = G(sx, 0.0, sz)
        M.apply_transform(o)
    dr += sc
    # china marker (red wax pencil wrapped in paper) by the splicing block
    mk = [F.gcyl("marker_body", 0.0052, 0.10, (0.20, TOP + 0.0052, 0.565), axis="x", verts=10, mat="M_Paper", bevel=0.0),
          F.gcyl("marker_tip", 0.0052, 0.016, (0.30, TOP + 0.0052, 0.565), axis="x", verts=10, mat="M_Enamel_Crimson",
                 bevel=0.0, r_top=0.0018),
          F.gcyl("marker_string", 0.0054, 0.004, (0.24, TOP + 0.0052, 0.565), axis="x", verts=10, mat="M_Enamel_Crimson",
                 bevel=0.0)]
    for o in mk:
        F.bake_xform(o, yaw=8.0, about=(0.25, 0.0, 0.565))
    dr += mk
    parts["dressing"] = F.part("bench_dressing", dr)


def build():
    M.reset_scene()
    F.ensure_materials()
    build_bench()
    build_light_box()
    build_strips()
    build_block()
    build_rewind()
    build_can()
    build_dressing()
    F.finalize_all()
    return F.report(NAME)


REQUIRED = ["bench", "light_box", "light_box_glass", "splice_block", "rewind", "reel_can", "reel_can_lid",
            "splicer_reel_mount"] + [f"IA_frame_{k}" for k in range(4)] + [f"IA_slot_{s}" for s in range(4)] + \
           [f"slot_mount_{s}" for s in range(4)]


def main():
    total = build()
    path = F.export(NAME)
    errs = F.verify_glb(path, required=REQUIRED,
                        identity=[f"IA_slot_{s}" for s in range(4)] + [f"slot_mount_{s}" for s in range(4)] +
                        ["splicer_reel_mount", "light_box_glass", "reel_can_lid"],
                        budget=BUDGET, show=REQUIRED)
    print(f"[film_splicer] tris={total} errors={len(errs)} lid centre={parts['lid_centre']}")
    if "--no-render" in ARGS:
        return
    qa()


# ------------------------------------------------------------------ QA
def qa():
    F.qa_begin()
    F.qa_decal_alpha()
    F.qa_decal_emit("M_Decal_FilmStrip_", 0.18)
    F.qa_emit("M_Glass_Frosted", "FFF4DC", 0.9)
    F.qa_room("booth")
    place = F.qa_place((-3.9, 0.0, 3.5), 180.0)
    F.qa_neighbours([("slide_cabinet", (-5.0, 0.0, 2.8), 90.0), ("lens_case", (-3.75, 1.45, 3.37), 180.0),
                     ("film_projector", (-2.9, 0.0, 2.65), 180.0)])
    # a few film cans on the booth shelf (room A dressing) so the wall does not read empty in QA
    F.qa_light("booth_bulb", "POINT", (-3.0, 2.65, 2.85), 70.0, "FFCF94", radius=0.04)
    F.qa_light("focus_fill", "POINT", (-3.9, 1.75, 2.45), 6.0, "FFE6C8", radius=0.25)
    F.qa_light("lightbox", "AREA", (-3.59, 0.99, 3.165), 6.0, "FFF4DC", radius=0.35, target=(-3.59, 2.0, 3.165))
    M.refresh()
    if F.want("hero", ARGS):
        F.shoot(NAME, (-3.05, 1.42, 2.25), (-3.95, 0.93, 3.2), vfov=46, world=0.12)
    if F.want("view", ARGS):
        F.shoot(NAME + "_2", (-3.9, 1.55, 2.55), (-3.9, 0.95, 3.3), vfov=48, world=0.08)
    if F.want("lid", ARGS):
        lc = parts["lid_centre"]
        wl = (-3.9 - lc[0], lc[1], 3.5 - lc[2])
        F.shoot(NAME + "_4", (wl[0] + 0.12, wl[1] + 0.22, wl[2] - 0.42), wl, vfov=32, world=0.08)
    # placed state: strips in the solution order (slot 0..3 = f2, f0, f3, f1), reel on the spindle
    F.item_or_proxy("film_reel", parts["reel_mount"])
    for slot, k in enumerate((2, 0, 3, 1)):
        F.set_world_xform(parts["strips"][k], parts["slot_mounts"][slot])
    if F.want("placed", ARGS):
        F.shoot(NAME + "_3", (-3.9, 1.55, 2.55), (-3.9, 0.95, 3.3), vfov=48, world=0.08)
    if F.want("slots", ARGS):
        F.shoot(NAME + "_5", (-4.18, 1.22, 2.78), (-4.18, 0.93, 3.05), vfov=36, world=0.08)
    if F.want("booth", ARGS):
        F.shoot(NAME + "_6", (-1.55, 1.6, 2.6), (-4.6, 1.1, 2.9), vfov=62, world=0.10)


main()
