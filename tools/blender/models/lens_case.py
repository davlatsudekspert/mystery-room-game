"""lens_case.glb — velvet-lined walnut case for two blank Lumen crystals (Chapter 2 booth shelf; group B2).

0.24 w x 0.070 h x 0.13 d (contract 0.16 d, see DEVIATION). Free-standing small object: origin at the centre
of its underside, front +Z (placed at world (-3.75, 1.45, 3.37) with yaw 180 on the booth shelf).
Walnut box with rounded vertical corners, eight brass corner caps, brass butt hinges at the back and a
brass hook catch at the front. Inside: a crimson velvet insert with two round pockets (each with a
finger notch toward the hinge) holding the crystals face up; the lid is velvet padded.

Parts:
  IA_case_lid       pivot on the hinge axis (back top edge of the base: (0, 0.048, -0.065)), identity at rest;
                    open = -105 deg about local +X (the lid swings up and back toward the wall).
  crystal_mount_1/2 pocket centres at x = -0.055 / +0.055 (player's left / right), rotation -90 deg about X:
                    lumen_crystal.glb (natural pose on edge, face +Z) then lies FACE UP, its grip tab toward
                    -Z (the hinge, into the finger notch), resting on the pocket floor.
  case_base         static.

DEVIATION: depth 0.13 instead of 0.16. Opened to -105 deg, a 0.16-deep lid would reach 0.066 behind the
hinge, i.e. 1.6 cm into the booth wall (the case's back is only 0.05 from the wall at z 3.37 + 0.08); at
0.13 the open lid stops ~8 mm short of the wall.

    blender -b --factory-startup -P tools/blender/models/lens_case.py [-- --no-render] [--shots a,b]
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

NAME = "lens_case"
ARGS = M.main_guard()
BUDGET = 2500

W, D = 0.24, 0.13
HB = 0.048                    # base height (hinge line)
HT = 0.070                    # total height
R = 0.009                     # corner radius
WALL = 0.011
POCKET_FLOOR = 0.034
VELVET_TOP = 0.040
POCKET_R = 0.0295
POCKETS = [(-0.055, 0.006), (0.055, 0.006)]
CRYSTAL_BOTTOM = 0.0041       # lumen_crystal.glb lying face up: lowest point below its origin
HINGE = (0.0, HB, -D / 2)
LID_OPEN = -105.0

parts = {}


def pocket_loop(cx, cy, r=POCKET_R, notch_w=0.0072, notch_l=0.0385, n=26):
    """Round pocket with a finger notch toward 2D +y (= Godot -Z with ey = (0, 0, -1))."""
    a0 = math.degrees(math.asin(notch_w / r))
    pts = []
    for j in range(n + 1):
        a = math.radians(90 + a0 + (360 - 2 * a0) * j / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts += [(cx + notch_w, cy + notch_l - 0.003), (cx + notch_w - 0.002, cy + notch_l),
            (cx - notch_w + 0.002, cy + notch_l), (cx - notch_w, cy + notch_l - 0.003)]
    return pts


def corner_caps(prefix, y0, y1):
    """Brass caps wrapping the four rounded vertical corners (cylinders on the corner-arc centres)."""
    out = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (W / 2 - R), sz * (D / 2 - R)
            out.append(F.gcyl(f"{prefix}_{sx}_{sz}", R + 0.0008, y1 - y0, (cx, y0, cz), verts=16, mat="M_Brass_Aged",
                              bevel=0.0, smooth=50.0))
    return out


def build_base():
    b = []
    shell_loops = [K.rounded_rect(W, D, R, 4), K.rounded_rect(W - 2 * WALL, D - 2 * WALL, 0.003, 2)]
    b.append(F.gpoly("base_walls", shell_loops, HB - 0.001, (0, 0.001, 0), (1, 0, 0), (0, 0, -1), mat="M_Wood_Walnut",
                     bevel=0.0012))
    b.append(F.gslab("base_bottom", (0, 0.0, 0), W - 0.004, D - 0.004, 0.006, r=R - 0.002, mat="M_Wood_Walnut",
                     bevel=0.0008, n=3))
    # velvet insert: block up to the pocket floor, then a layer with the two pockets
    iw, idp = W - 2 * WALL, D - 2 * WALL
    b.append(F.gbox("velvet_block", (-iw / 2, 0.006, -idp / 2), (iw / 2, POCKET_FLOOR, idp / 2), mat="M_Velvet",
                    bevel=0.0))
    loops = [K.rounded_rect(iw, idp, 0.003, 2)] + [pocket_loop(x, -z) for (x, z) in POCKETS]
    b.append(F.gpoly("velvet_top", loops, VELVET_TOP - POCKET_FLOOR, (0, POCKET_FLOOR, 0), (1, 0, 0), (0, 0, -1),
                     mat="M_Velvet", bevel=0.0012))
    b += corner_caps("base_cap", 0.0, HB - 0.0005)
    # catch staple on the front, hinge leaves + outer knuckles at the back
    b.append(F.gslab("catch_plate", (0, HB - 0.019, D / 2), 0.020, 0.016, 0.0012, r=0.003, mat="M_Brass_Aged",
                     plane="xy", bevel=0.0, n=3))
    b.append(F.gtube("catch_staple", [(-0.0045, HB - 0.020, D / 2 + 0.001), (-0.0045, HB - 0.020, D / 2 + 0.0055),
                                      (0.0045, HB - 0.020, D / 2 + 0.0055), (0.0045, HB - 0.020, D / 2 + 0.001)],
                     0.0011, sides=6, mat="M_Brass_Aged"))
    for hx in (-0.065, 0.065):
        b.append(F.gbox(f"hinge_leaf_b_{hx}", (hx - 0.015, HB - 0.013, -D / 2 - 0.0012), (hx + 0.015, HB - 0.0012,
                                                                                         -D / 2), mat="M_Brass_Aged",
                        bevel=0.0003))
        for k in (-1, 1):
            b.append(F.gcyl(f"knuckle_b_{hx}_{k}", 0.0026, 0.0095, (hx + k * 0.0105 - 0.00475, HB, -D / 2 - 0.0002),
                            axis="x", verts=8, mat="M_Brass_Aged", bevel=0.0))
    parts["base"] = F.part("case_base", b)


def build_lid():
    lid = []
    lid.append(F.gslab("lid_body", (0, HB, 0), W, D, HT - HB, r=R, mat="M_Wood_Walnut", bevel=0.0035, n=4))
    lid += corner_caps("lid_cap", HB + 0.0005, HT + 0.0006)
    # velvet padding under the lid (fits inside the base walls) and a brass name plate on the top
    lid.append(F.gslab("lid_pad", (0, HB - 0.0055, 0), W - 2 * WALL - 0.003, D - 2 * WALL - 0.003, 0.0056, r=0.004,
                       mat="M_Velvet", bevel=0.0018, n=3))
    lid.append(F.gslab("lid_plate", (0, HT, 0.004), 0.064, 0.026, 0.0008, r=0.012, mat="M_Brass_Aged", bevel=0.0, n=5))
    for sx in (-1, 1):
        lid.append(F.screw(f"lid_plate_screw_{sx}", 0.0015, (sx * 0.026, HT + 0.0008, 0.004), "y", mat="M_Brass_Aged",
                           segs=5))
    # hook catch: plate on the lid front edge, a hook hanging over the base staple
    lid.append(F.gslab("hook_plate", (0, HB + 0.011, D / 2), 0.016, 0.014, 0.0012, r=0.003, mat="M_Brass_Aged",
                       plane="xy", bevel=0.0, n=3))
    lid.append(F.gtube("hook", [(0, HB + 0.011, D / 2 + 0.0024), (0, HB - 0.002, D / 2 + 0.0034),
                                (0, HB - 0.016, D / 2 + 0.0040), (0, HB - 0.019, D / 2 + 0.0020)], 0.0013, sides=6,
                       mat="M_Brass_Aged"))
    for hx in (-0.065, 0.065):
        lid.append(F.gbox(f"hinge_leaf_l_{hx}", (hx - 0.015, HB + 0.0012, -D / 2 - 0.0012),
                          (hx + 0.015, HB + 0.013, -D / 2), mat="M_Brass_Aged", bevel=0.0003))
        lid.append(F.gcyl(f"knuckle_l_{hx}", 0.0026, 0.0105, (hx - 0.00525, HB, -D / 2 - 0.0002), axis="x", verts=8,
                          mat="M_Brass_Aged", bevel=0.0))
    o = F.part("IA_case_lid", lid, pivot=HINGE)
    parts["lid"] = o


def build_mounts():
    parts["mounts"] = []
    for k, (x, z) in enumerate(POCKETS, start=1):
        parts["mounts"].append(F.mount(f"crystal_mount_{k}", (x, POCKET_FLOOR + CRYSTAL_BOTTOM, z), rot_deg=(-90.0, 0.0, 0.0)))


def build():
    M.reset_scene()
    F.ensure_materials()
    build_base()
    build_lid()
    build_mounts()
    F.finalize_all()
    return F.report(NAME)


REQUIRED = ["case_base", "IA_case_lid", "crystal_mount_1", "crystal_mount_2"]


def main():
    total = build()
    path = F.export(NAME)
    errs = F.verify_glb(path, required=REQUIRED, identity=["case_base", "IA_case_lid"], budget=BUDGET, show=REQUIRED)
    print(f"[lens_case] tris={total} errors={len(errs)}")
    if "--no-render" in ARGS:
        return
    qa()


def qa():
    F.qa_begin()
    F.qa_room("booth")
    root = F.qa_place((-3.75, 1.45, 3.37), 180.0)
    F.qa_neighbours([("film_splicer", (-3.9, 0.0, 3.5), 180.0), ("slide_cabinet", (-5.0, 0.0, 2.8), 90.0)])
    F.qa_light("booth_bulb", "POINT", (-3.0, 2.65, 2.85), 70.0, "FFCF94", radius=0.04)
    F.qa_light("focus_fill", "POINT", (-3.75, 2.0, 2.75), 5.0, "FFE6C8", radius=0.25)
    M.refresh()
    if F.want("view", ARGS):
        F.shoot(NAME + "_2", (-3.75, 1.85, 2.8), (-3.75, 1.47, 3.37), vfov=40, world=0.10)
    # open with the crystals
    lid = parts["lid"]
    lid.rotation_mode = "XYZ"
    lid.rotation_euler = (math.radians(LID_OPEN), 0.0, 0.0)
    for m in parts["mounts"]:
        F.item_or_proxy("lumen_crystal", m)
    M.refresh()
    zs = [(o.matrix_world @ Vector(c)) for o in bpy.context.scene.objects if o.type == "MESH" and o.name.startswith("qa_")
          and ("crystal" in o.name) for c in o.bound_box]
    if zs:
        print(f"[lens_case] crystal lowest z (world) = {min(v.z for v in zs):.4f}; pocket floor = {1.45 + POCKET_FLOOR:.4f}")
    back = max((-(o.matrix_world @ Vector(c)).y for o in [lid] for c in o.bound_box))
    print(f"[lens_case] open lid reaches world z = {back:.4f} (wall at 3.5)")
    if F.want("open", ARGS):
        F.shoot(NAME + "_3", (-3.75, 1.85, 2.8), (-3.75, 1.47, 3.37), vfov=40, world=0.10)
    if F.want("hero", ARGS):
        F.shoot(NAME, (-3.55, 1.72, 3.0), (-3.75, 1.49, 3.37), vfov=36, world=0.12)


main()
