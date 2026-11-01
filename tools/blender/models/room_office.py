"""room_office.glb — R7 the Director's Office (Level +1), built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 3b/7. "A headmaster's study kept as it was": order, brass and leather. Bottle-green
watered wallpaper over dark panelling, a heavy mahogany desk with a leather top and ONE green banker's lamp, a marble fireplace with a
big institute portrait, glass-fronted bookcases, a cold tea for two on a low table between two leather armchairs, a rug, institute
portraits (original simple silhouettes), a pale circle on the wall where a clock used to hang (there is no clock in this room).
Interior x [-2.9, 2.9], z [-2.4, 2.4], ceiling y 3.2, wall thickness 0.25.
Openings and parts (room space):
  west wall x = -2.9  door to the Gallery z [-1.6, -0.7] y [0, 2.2], leaf `IA_door_gallery` (hinge at z = -0.7, opens +95 deg about +Y, OUT to -X),
                      the tag-shaped keyhole plate on its inner face
  north wall          arched window x = 0.4 (w 1.3, sill 0.9, spring 2.6) behind the desk chair, velvet curtains on a brass rod (`curtains`)
  east wall           the cabinet wall: `strand_cabinet` stands against it (mount `cabinet_mount`), a ghost-clock circle, a radiator
  south wall          the marble fireplace x [-1.3, 0.3] with the institute portrait over it, glass-front bookcases either side
Suggested placements of separate models (Godot position, yaw): strand_cabinet (2.67, 0, 0.30) -90 (mount `cabinet_mount`),
  tea_set (-0.55, 0.60, 0.95) 0 (mount `tea_mount`, the table top is at y 0.60).
Own objects: floor, wall_n/_e/_s/_w, ceiling, desk, chairs, fireplace, bookcases, portraits, curtains, window, sky_card, tea_table, rug, dressing,
  IA_door_gallery, IA_desk_drawer (the centre drawer, pivot at its front-bottom centre (0.4, 0.59, -0.83), slide +0.30 along +Z), empties
  cabinet_mount, tea_mount, light_desk_lamp (0.05, 1.12, -1.25), light_window_n (0.4, 2.4, -2.1), light_fire (-0.5, 0.5, 2.1).
    blender -b --factory-startup -P tools/blender/models/room_office.py [-- --no-render] [--shots=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402

NAME = "room_office"
BUDGET = 50000
ARGS = M.main_guard()
X0, X1, Z0, Z1, H, T = -2.9, 2.9, -2.4, 2.4, 3.2, 0.25
PAPER, DADO, MAH, BRASS = "M_Wallpaper_Office", "M_Wood_Panel", "M_Wood_Mahogany", "M_Brass_Aged"
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def shell():
    ops = {"w": [(-1.6, -0.7, 0.0, 2.2)]}
    mats = {k: (DADO, 1.10, PAPER) for k in "nsew"}
    w = X.wallset("off", X0, X1, Z0, Z1, H, T, mats, ops, floor_mat="M_Wood_Floor", ceil_mat="M_Ceiling")
    U.arch_cut(w["n"], "z", 0.4, 1.3, 0.9, 2.6, Z0 - T - 0.1, Z0 + 0.1)
    for k in ("n", "s", "e", "w"):
        add("wall_" + k, *w[k])
    add("floor", *w["floor"])
    add("ceiling", *w["ceiling"])
    # dado rail, skirting, picture rail and crown moulding, wallpaper stripes are in the texture
    for side, mn, mx in (("n", (X0, 1.10, Z0), (X1, 1.16, Z0 + 0.04)), ("s", (X0, 1.10, Z1 - 0.04), (X1, 1.16, Z1)),
                         ("e", (X1 - 0.04, 1.10, Z0), (X1, 1.16, Z1)), ("w", (X0, 1.10, Z0), (X0 + 0.04, 1.16, Z1))):
        add("dressing", gbox("dado" + side, mn, mx, MAH, bevel=0.004))
    for side, mn, mx in (("n", (X0, 0.0, Z0), (X1, 0.16, Z0 + 0.03)), ("s", (X0, 0.0, Z1 - 0.03), (X1, 0.16, Z1)),
                         ("e", (X1 - 0.03, 0.0, Z0), (X1, 0.16, Z1)), ("w", (X0, 0.0, Z0), (X0 + 0.03, 0.16, Z1))):
        add("dressing", gbox("skirt" + side, mn, mx, MAH, bevel=0.004))
    for side, mn, mx in (("n", (X0, 2.62, Z0), (X1, 2.68, Z0 + 0.04)), ("s", (X0, 2.62, Z1 - 0.04), (X1, 2.68, Z1)),
                         ("e", (X1 - 0.04, 2.62, Z0), (X1, 2.68, Z1)), ("w", (X0, 2.62, Z0), (X0 + 0.04, 2.68, Z1))):
        add("dressing", gbox("prail" + side, mn, mx, BRASS, bevel=0.002))
    for z, sg in ((Z0, 1), (Z1, -1)):
        add("dressing", gbox(f"crown{z}", (X0, H - 0.20, z if sg > 0 else z - 0.14), (X1, H, z + 0.14 if sg > 0 else z), "M_Plaster_Wall", bevel=0.006),
            gbox(f"crown_b{z}", (X0, H - 0.26, z if sg > 0 else z - 0.07), (X1, H - 0.20, z + 0.07 if sg > 0 else z), MAH, bevel=0.004))
    add("dressing", gbox("crown_e", (X1 - 0.14, H - 0.20, Z0), (X1, H, Z1), "M_Plaster_Wall", bevel=0.006), gbox("crown_w", (X0, H - 0.20, Z0), (X0 + 0.14, H, Z1), "M_Plaster_Wall", bevel=0.006))
    # coffer beams on the ceiling (a 3 x 2 grid of shallow panels)
    for i in range(3):
        x = X0 + (i + 1) * 5.8 / 3
        add("dressing", gbox(f"cof_x{i}", (x - 0.05, H - 0.07, Z0), (x + 0.05, H, Z1), "M_Plaster_Wall", bevel=0.004))
    add("dressing", gbox("cof_z", (X0, H - 0.07, -0.05), (X1, H, 0.05), "M_Plaster_Wall", bevel=0.004))
    # window frame and curtains
    add("window", *U.arch_frame("win", "z", Z0, +1, 0.4, 1.3, 0.9, 2.6, mat=MAH, bar=0.08))
    add("sky_card", U.sky_card("win", "z", Z0, +1, 0.4, 1.3, 0.9, 2.6, mat="M_Emissive_Table"))
    cu = []
    for sx in (-1, 1):
        for i in range(6):
            x = 0.4 + sx * (0.78 + i * 0.075)
            cu.append(gbox(f"cfold{sx}{i}", (x - 0.04, 0.20, Z0 + 0.08 + (0.03 if i % 2 else 0.0)), (x + 0.04, 2.95, Z0 + 0.12 + (0.03 if i % 2 else 0.0)), "M_Velvet", bevel=0.006))
        cu.append(gbox(f"tieback{sx}", (0.4 + sx * 0.88 - 0.03, 1.2, Z0 + 0.06), (0.4 + sx * 0.88 + 0.03, 1.26, Z0 + 0.22), BRASS, bevel=0.003))
    cu.append(gcyl("rod", 0.014, 2.5, (-0.85, 3.0, Z0 + 0.10), axis="x", verts=8, mat=BRASS, bevel=0.0))
    for sx in (-1, 1):
        cu.append(M.sphere(f"rod_end{sx}", 0.03, loc=G(0.4 + sx * 1.25, 3.0, Z0 + 0.10), segments=10, rings=6, mat=BRASS))
    add("curtains", *cu)


def door():
    o = [gbox("leaf", (X0 + 0.02, 0.03, -1.6), (X0 + 0.07, 2.17, -0.7), "M_Wood_Mahogany", bevel=0.004)]
    for y in (0.45, 1.1, 1.75):
        o.append(gbox(f"pan{y}", (X0 + 0.07, y - 0.22, -1.52), (X0 + 0.082, y + 0.22, -0.78), MAH, bevel=0.004))
    o.append(gbox("lock_plate", (X0 + 0.07, 1.0, -0.96), (X0 + 0.08, 1.24, -0.76), BRASS, bevel=0.004))
    o.append(X.gpoly("keyhole", A.rounded_rect(0.075, 0.056, 0.012, 3), 0.004, X.C.gframe((X0 + 0.08, 1.12, -0.86), (0, 0, -1), (0, 1, 0)), mat="M_Lacquer_Black", bevel=0.0))
    o.append(gbox("handle", (X0 + 0.08, 0.95, -0.92), (X0 + 0.11, 1.0, -0.80), "M_Brass_Polished", bevel=0.003))
    ia = part("IA_door_gallery", o, (X0 + 0.045, 0.0, -0.7))
    add("dressing", gbox("fr_h", (X0, 2.20, -1.7), (X0 + 0.10, 2.32, -0.6), MAH, bevel=0.005), gbox("fr_a", (X0, 0.0, -1.7), (X0 + 0.10, 2.20, -1.6), MAH, bevel=0.005),
        gbox("fr_b", (X0, 0.0, -0.7), (X0 + 0.10, 2.20, -0.6), MAH, bevel=0.005))
    return ia


def desk_zone():
    """Mahogany desk (1.8 x 0.9) at (0.4, z -1.25), leather top, two drawer pedestals + centre drawer, banker lamp, blotter, inkwell, phone, chair."""
    cx, cz = 0.4, -1.25
    top = 0.76
    d = [gbox("top", (cx - 0.92, top - 0.05, cz - 0.46), (cx + 0.92, top, cz + 0.46), MAH, bevel=0.008, seg=2),
         gbox("leather", (cx - 0.82, top, cz - 0.37), (cx + 0.82, top + 0.004, cz + 0.37), "M_Leather", bevel=0.0),
         gbox("leather_edge", (cx - 0.84, top, cz - 0.39), (cx + 0.84, top + 0.002, cz + 0.39), BRASS, bevel=0.0)]
    for sx in (-1, 1):
        px0, px1 = (cx - 0.88, cx - 0.30) if sx < 0 else (cx + 0.30, cx + 0.88)
        d.append(gbox("ped", (px0, 0.04, cz - 0.42), (px1, top - 0.05, cz + 0.42), MAH, bevel=0.004))
        d.append(gbox("ped_plinth", (px0 - 0.015, 0.0, cz - 0.435), (px1 + 0.015, 0.06, cz + 0.435), MAH, bevel=0.004))
        for k in range(3):
            y0 = 0.10 + k * 0.19
            d.append(gbox(f"pdrw{sx}{k}", (px0 + 0.03, y0, cz + 0.42), (px1 - 0.03, y0 + 0.17, cz + 0.44), MAH, bevel=0.004))
            d.append(gbox(f"ppull{sx}{k}", ((px0 + px1) / 2 - 0.05, y0 + 0.075, cz + 0.44), ((px0 + px1) / 2 + 0.05, y0 + 0.095, cz + 0.462), BRASS, bevel=0.003))
            d.append(gbox(f"pkey{sx}{k}", ((px0 + px1) / 2 - 0.004, y0 + 0.12, cz + 0.44), ((px0 + px1) / 2 + 0.004, y0 + 0.145, cz + 0.442), "M_Lacquer_Black", bevel=0.0))
    d.append(gbox("modesty", (cx - 0.30, 0.2, cz - 0.42), (cx + 0.30, top - 0.05, cz - 0.40), MAH, bevel=0.0))
    cdr = [gbox("cdr", (cx - 0.26, top - 0.17, cz + 0.42), (cx + 0.26, top - 0.06, cz + 0.44), MAH, bevel=0.004),
           gbox("cdr_pull", (cx - 0.06, top - 0.125, cz + 0.44), (cx + 0.06, top - 0.105, cz + 0.462), BRASS, bevel=0.003)]
    d_ia = part("IA_desk_drawer", cdr, (cx, top - 0.17, cz + 0.42))
    # desk furniture
    d.append(gbox("blotter", (cx - 0.28, top + 0.004, cz + 0.06), (cx + 0.18, top + 0.014, cz + 0.32), "M_Paper", bevel=0.002))
    d.append(gbox("blotter_l", (cx - 0.30, top + 0.004, cz + 0.04), (cx - 0.28, top + 0.026, cz + 0.34), "M_Leather", bevel=0.002))
    d.append(gbox("blotter_r", (cx + 0.18, top + 0.004, cz + 0.04), (cx + 0.20, top + 0.026, cz + 0.34), "M_Leather", bevel=0.002))
    d.append(gbox("pen_tray", (cx + 0.30, top + 0.004, cz - 0.05), (cx + 0.58, top + 0.032, cz + 0.04), BRASS, bevel=0.004))
    d.append(gcyl("pen", 0.005, 0.20, (cx + 0.34, top + 0.032, cz - 0.01), axis="x", verts=6, mat="M_Lacquer_Black", bevel=0.0))
    d.append(glathe("ink_well", [(0.0, 0.0), (0.04, 0.0), (0.04, 0.045), (0.02, 0.055), (0.0, 0.055)], (cx + 0.64, top + 0.004, cz - 0.22), axis="y", segments=12, mat="M_Glass_Dark"))
    d.append(glathe("ink_cap", [(0.0, 0.055), (0.022, 0.055), (0.018, 0.075), (0.0, 0.078)], (cx + 0.64, top + 0.004, cz - 0.22), axis="y", segments=10, mat=BRASS))
    # bakelite telephone (cradle phone)
    d.append(gbox("ph_base", (cx - 0.67, top + 0.004, cz - 0.30), (cx - 0.43, top + 0.07, cz - 0.10), "M_Bakelite", bevel=0.012, seg=2))
    d.append(gcyl("ph_dial", 0.045, 0.006, (cx - 0.55, top + 0.072, cz - 0.20), axis="y", verts=14, mat=BRASS, bevel=0.0))
    d.append(gcyl("ph_stem", 0.012, 0.13, (cx - 0.55, top + 0.07, cz - 0.20), axis="y", verts=8, mat="M_Bakelite", bevel=0.0))
    d.append(gbox("ph_handset", (cx - 0.68, top + 0.18, cz - 0.24), (cx - 0.42, top + 0.205, cz - 0.16), "M_Bakelite", bevel=0.01))
    # papers stack and a closed ledger
    d.append(gbox("ledger", (cx - 0.15, top + 0.004, cz - 0.30), (cx + 0.13, top + 0.050, cz - 0.08), "M_Book_Green", bevel=0.003))
    # banker lamp: THE green lamp of the room (green glass shade)
    d += U.banker_lamp("dl_", cx - 0.45, top + 0.0, cz - 0.28, yaw=0.0, with_bulb=False)
    # desk chair (leather, swivel): seat, back, arms, cast base with wheels
    chx, chz = cx, cz - 0.92
    c = [gbox("seat", (chx - 0.26, 0.46, chz - 0.25), (chx + 0.26, 0.52, chz + 0.25), "M_Leather", bevel=0.02, seg=2),
         gbox("back", (chx - 0.25, 0.60, chz - 0.30), (chx + 0.25, 1.12, chz - 0.22), "M_Leather", bevel=0.025, seg=2),
         gbox("back_frame", (chx - 0.275, 0.58, chz - 0.315), (chx + 0.275, 1.14, chz - 0.30), MAH, bevel=0.01),
         gcyl("post", 0.03, 0.36, (chx, 0.12, chz), axis="y", verts=10, mat="M_Brass_Polished", bevel=0.0)]
    for sx in (-1, 1):
        c.append(gbox("arm", (chx + sx * 0.27 - 0.025, 0.62, chz - 0.20), (chx + sx * 0.27 + 0.025, 0.66, chz + 0.20), MAH, bevel=0.01))
        c.append(gbox("arm_post", (chx + sx * 0.27 - 0.02, 0.52, chz + 0.12), (chx + sx * 0.27 + 0.02, 0.62, chz + 0.16), MAH, bevel=0.003))
    for k in range(5):
        a = math.tau * k / 5
        c.append(gbox(f"leg{k}", (0.0, -0.015, -0.015), (0.30, 0.015, 0.015), "M_Iron_Rust", bevel=0.0))
        U.rot_godot([c[-1]], "y", math.degrees(a), (0, 0, 0))
        U.move([c[-1]], (chx, 0.10, chz))
        c.append(gcyl(f"cast{k}", 0.025, 0.04, (chx + math.cos(a) * 0.30, 0.0, chz - math.sin(a) * 0.30), axis="y", verts=8, mat="M_Rubber", bevel=0.0))
    for i in range(14):                                   # leather buttons on the back
        c.append(M.sphere(f"btn{i}", 0.008, loc=G(chx - 0.18 + (i % 4) * 0.12, 0.74 + (i // 4) * 0.12, chz - 0.215), segments=6, rings=4, mat="M_Brass_Polished"))
    add("desk", *d)
    add("chairs", *c)
    return d_ia


def seating_and_tea():
    # low round tea table with a cloth; two leather armchairs facing it
    tx, tz, top = -0.55, 0.95, 0.60
    t = [gcyl("tt_top", 0.42, 0.04, (tx, top - 0.04, tz), axis="y", verts=26, mat=MAH, bevel=0.006),
         gcyl("tt_cloth", 0.40, 0.006, (tx, top, tz), axis="y", verts=26, mat="M_Linen", bevel=0.0),
         glathe("tt_stem", [(0.0, 0.0), (0.12, 0.0), (0.07, 0.06), (0.04, 0.2), (0.07, 0.52), (0.0, 0.56)], (tx, 0.0, tz), axis="y", segments=14, mat=MAH),
         glathe("tt_rim", [(0.405, top - 0.01), (0.425, top - 0.01), (0.425, top + 0.003), (0.405, top + 0.003)], (tx, 0.0, tz), axis="y", segments=26, mat=BRASS)]
    add("tea_table", *t)
    mount("tea_mount", (tx, top + 0.006, tz))
    for k, (ax, az, yaw) in enumerate(((tx - 0.95, tz, 90.0), (tx + 0.95, tz, -90.0))):
        a = [gbox("a_seat", (ax - 0.30, 0.28, az - 0.30), (ax + 0.30, 0.46, az + 0.30), "M_Leather", bevel=0.035, seg=3),
             gbox("a_base", (ax - 0.32, 0.12, az - 0.32), (ax + 0.32, 0.30, az + 0.32), MAH, bevel=0.01),
             gbox("a_back", (ax - 0.32, 0.46, az - 0.36), (ax + 0.32, 1.02, az - 0.20), "M_Leather", bevel=0.05, seg=3),
             gbox("a_wing_l", (ax - 0.38, 0.46, az - 0.34), (ax - 0.30, 0.95, az + 0.0), "M_Leather", bevel=0.03, seg=2),
             gbox("a_wing_r", (ax + 0.30, 0.46, az - 0.34), (ax + 0.38, 0.95, az + 0.0), "M_Leather", bevel=0.03, seg=2)]
        for sx in (-1, 1):
            a.append(gbox("a_arm", (ax + sx * 0.38 - 0.06, 0.46, az - 0.22), (ax + sx * 0.38 + 0.06, 0.62, az + 0.30), "M_Leather", bevel=0.04, seg=2))
            for sz in (-1, 1):
                a.append(gcyl("a_foot", 0.025, 0.12, (ax + sx * 0.28, 0.0, az + sz * 0.28), axis="y", verts=8, mat=MAH, bevel=0.0, r_top=0.03))
        for i in range(12):
            a.append(M.sphere(f"abtn{i}", 0.008, loc=G(ax - 0.20 + (i % 4) * 0.13, 0.62 + (i // 4) * 0.13, az - 0.195), segments=6, rings=4, mat="M_Brass_Polished"))
        U.rot_godot(a, "y", yaw, (ax, 0, az))
        add("chairs", *a)
    # rug under the seating group and the desk
    add("rug", gbox("rug_a", (-1.95, 0.004, -0.15), (0.85, 0.012, 2.05), "M_Dress_Wool", bevel=0.0), gbox("rug_a_b", (-1.90, 0.012, -0.10), (0.80, 0.014, 2.00), "M_Wool_Knit", bevel=0.0),
        gbox("rug_a_c", (-1.75, 0.014, 0.05), (0.65, 0.016, 1.85), "M_Dress_Wool", bevel=0.0),
        gbox("rug_b", (-0.7, 0.004, -2.0), (1.5, 0.012, -0.2), "M_Dress_Wool", bevel=0.0), gbox("rug_b_b", (-0.65, 0.012, -1.95), (1.45, 0.014, -0.25), "M_Wool_Knit", bevel=0.0))


def fireplace():
    fx0, fx1, fh = -1.3, 0.3, 1.25
    f = [gbox("fp_jamb_l", (fx0, 0.0, Z1 - 0.34), (fx0 + 0.24, fh - 0.28, Z1), "M_Stone", bevel=0.01),
         gbox("fp_jamb_r", (fx1 - 0.24, 0.0, Z1 - 0.34), (fx1, fh - 0.28, Z1), "M_Stone", bevel=0.01),
         gbox("fp_lintel", (fx0 - 0.04, fh - 0.28, Z1 - 0.34), (fx1 + 0.04, fh, Z1), "M_Stone", bevel=0.01),
         gbox("fp_shelf", (fx0 - 0.14, fh, Z1 - 0.42), (fx1 + 0.14, fh + 0.07, Z1), "M_Stone", bevel=0.012, seg=2),
         gbox("fp_hearth", (fx0 - 0.10, 0.0, Z1 - 0.70), (fx1 + 0.10, 0.04, Z1 - 0.34), "M_Stone", bevel=0.01),
         gbox("fp_back", (fx0 + 0.24, 0.02, Z1 - 0.04), (fx1 - 0.24, fh - 0.28, Z1), "M_Lacquer_Black", bevel=0.0),
         gbox("fp_floor", (fx0 + 0.24, 0.0, Z1 - 0.34), (fx1 - 0.24, 0.05, Z1), "M_Stone", bevel=0.0)]
    for k in range(7):                                   # cold grate bars + two firedogs
        f.append(gcyl(f"bar{k}", 0.008, 0.30, (fx0 + 0.36 + k * 0.1, 0.12, Z1 - 0.22), axis="y", verts=6, mat="M_Iron_Rust", bevel=0.0))
    f.append(gbox("grate_b", (fx0 + 0.34, 0.12, Z1 - 0.23), (fx1 - 0.34, 0.14, Z1 - 0.21), "M_Iron_Rust", bevel=0.0))
    for sx in (fx0 + 0.32, fx1 - 0.32):
        f.append(glathe("dog", [(0.0, 0.0), (0.03, 0.0), (0.025, 0.28), (0.04, 0.34), (0.0, 0.36)], (sx, 0.04, Z1 - 0.22), axis="y", segments=8, mat="M_Iron_Rust"))
        f.append(M.sphere("dog_ball", 0.032, loc=G(sx, 0.43, Z1 - 0.22), segments=8, rings=5, mat=BRASS))
    # ash and a tin scuttle, mantel garniture: a brass candlestick pair, a closed box
    f.append(gbox("ash", (fx0 + 0.34, 0.04, Z1 - 0.18), (fx1 - 0.34, 0.07, Z1 - 0.04), "M_Concrete", bevel=0.01))
    for sx in (fx0 + 0.12, fx1 - 0.12):
        f.append(glathe("cdl", [(0.0, 0.0), (0.05, 0.0), (0.05, 0.02), (0.015, 0.06), (0.02, 0.2), (0.032, 0.22), (0.0, 0.22)], (sx, fh + 0.07, Z1 - 0.12), axis="y", segments=10, mat=BRASS))
        f.append(gcyl("candle", 0.012, 0.10, (sx, fh + 0.29, Z1 - 0.12), axis="y", verts=8, mat="M_Enamel_Cream", bevel=0.0))
    f.append(gbox("mantel_box", (-0.75, fh + 0.07, Z1 - 0.22), (-0.30, fh + 0.17, Z1 - 0.08), "M_Leather", bevel=0.004))
    add("fireplace", *f)
    mount("light_fire", (-0.5, 0.5, 2.1))


def bookcases_and_portraits():
    add("bookcases", *U.wall_bookcase("bcl", "z", Z1, -1, -2.8, -1.4, 0.38, 2.55, seed=21, glass_front=True))
    add("bookcases", *U.wall_bookcase("bcr", "z", Z1, -1, 0.4, 2.0, 0.38, 2.55, seed=27, glass_front=True))
    add("bookcases", *U.wall_bookcase("bcw", "x", X0, +1, 0.45, 2.0, 0.34, 2.2, seed=33, glass_front=True))
    # portraits: the big institute portrait over the fireplace, two directors flanking the window, three on the west wall, small ones in a row by the cabinet
    P = []
    # facing: on the south wall (z = Z1, room is -z) a z-facing frame needs the picture normal -z; U.frame_art builds toward +Z, so use west/north/east
    P += U.frame_art("pn1", -1.55, 1.75, Z0 + 0.0, 0.62, 0.82, 0, facing="z")
    P += U.frame_art("pn2", 2.20, 1.75, Z0 + 0.0, 0.62, 0.82, 1, facing="z")
    P += U.frame_art("pn3", -2.55, 1.9, Z0 + 0.0, 0.50, 0.66, 4, facing="z")
    P += U.frame_art("pw0", -2.05, 1.80, X0, 0.42, 0.56, 3, facing="x")
    add("portraits", *P)
    # a big portrait over the fireplace built by hand, facing -z
    fr = []
    cx, cy, w, h = -0.5, 2.05, 0.9, 1.15
    for (a0, b0, a1, b1) in ((-w / 2, -h / 2, w / 2, -h / 2 + 0.05), (-w / 2, h / 2 - 0.05, w / 2, h / 2), (-w / 2, -h / 2, -w / 2 + 0.05, h / 2), (w / 2 - 0.05, -h / 2, w / 2, h / 2)):
        fr.append(gbox("bf", (cx + a0, cy + b0, Z1 - 0.045), (cx + a1, cy + b1, Z1), BRASS, bevel=0.004))
    fr.append(gbox("bcard", (cx - w / 2 + 0.05, cy - h / 2 + 0.05, Z1 - 0.02), (cx + w / 2 - 0.05, cy + h / 2 - 0.05, Z1 - 0.012), "M_Paper", bevel=0.0))
    mtx = X.C.gframe((cx, cy - 0.08, Z1 - 0.022), (-1, 0, 0), (0, 1, 0))
    s = 0.74
    sh = [(math.cos(math.pi * i / 12) * s * 0.46, -s * 0.5 + math.sin(math.pi * i / 12) * s * 0.30) for i in range(13)]
    fr.append(X.gpoly("bsh", list(reversed(sh)), 0.006, mtx, mat="M_Lacquer_Black"))
    fr.append(X.gpoly("bhd", [(math.cos(math.tau * i / 16) * s * 0.17, -s * 0.02 + math.sin(math.tau * i / 16) * s * 0.21) for i in range(16)], 0.006, mtx, mat="M_Lacquer_Black"))
    fr.append(X.gpoly("bnk", [(-s * 0.05, -s * 0.2), (s * 0.05, -s * 0.2), (s * 0.05, -s * 0.12), (-s * 0.05, -s * 0.12)], 0.006, mtx, mat="M_Lacquer_Black"))
    fr.append(X.gpoly("bbd", [(-s * 0.12, -s * 0.10), (s * 0.12, -s * 0.10), (s * 0.06, -s * 0.28), (-s * 0.06, -s * 0.28)], 0.006, mtx, mat="M_Lacquer_Black"))
    fr.append(gbox("bplaque", (cx - 0.12, cy - h / 2 - 0.09, Z1 - 0.025), (cx + 0.12, cy - h / 2 - 0.04, Z1), BRASS, bevel=0.002))
    add("portraits", *fr)
    # east wall: the ghost clock (a pale disc where a clock hung), a nail, a radiator under it
    gx = X1 - 0.003
    add("dressing", X.gpoly("ghost", [(math.cos(math.tau * i / 28) * 0.22, math.sin(math.tau * i / 28) * 0.22) for i in range(28)], 0.003,
                           X.C.gframe((X1 - 0.003, 2.15, 1.6), (0, 0, -1), (0, 1, 0)), mat="M_Plaster_Wall"),
        gcyl("nail", 0.006, 0.03, (X1 - 0.03, 2.15, 1.6), axis="x", verts=6, mat="M_Steel_Dark", bevel=0.0))
    rd = [gbox("rad_base", (X1 - 0.12, 0.12, 1.1), (X1 - 0.02, 0.18, 2.1), "M_Iron_Rust", bevel=0.002)]
    for k in range(10):
        rd.append(gbox(f"rad{k}", (X1 - 0.12, 0.18, 1.12 + k * 0.095), (X1 - 0.03, 0.78, 1.12 + k * 0.095 + 0.06), "M_Steel_Painted", bevel=0.008))
    rd.append(gbox("rad_top", (X1 - 0.13, 0.78, 1.1), (X1 - 0.02, 0.82, 2.1), "M_Iron_Rust", bevel=0.004))
    rd.append(X.pipe("rad_pipe", [(X1 - 0.07, 0.12, 2.1), (X1 - 0.07, 0.04, 2.2), (X1 - 0.07, 0.04, 2.38)], 0.018, mat="M_Iron_Rust", flange_ends=False, sides=8, fillet=0.03))
    add("dressing", *rd)
    # library globe near the window, a coat stand and an umbrella stand by the door
    add("dressing", glathe("globe_stand", [(0.0, 0.0), (0.18, 0.0), (0.18, 0.03), (0.04, 0.07), (0.03, 0.62), (0.0, 0.62)], (-2.35, 0.0, -1.85), axis="y", segments=14, mat=MAH),
        M.sphere("globe", 0.20, loc=G(-2.35, 0.86, -1.85), segments=18, rings=10, mat="M_Dress_Stone_Dark"),
        glathe("globe_ring", [(0.208, -0.012), (0.224, -0.012), (0.224, 0.012), (0.208, 0.012)], (-2.35, 0.86, -1.85), axis="y", segments=24, mat=BRASS))
    add("dressing", glathe("umbrella_stand", [(0.0, 0.0), (0.12, 0.0), (0.14, 0.55), (0.0, 0.55)], (-2.55, 0.0, -0.3), axis="y", segments=14, mat="M_Enamel_Green"),
        gcyl("umb", 0.012, 0.8, (-2.56, 0.45, -0.3), axis="y", verts=6, mat="M_Lacquer_Black", bevel=0.0))


def main():
    X.begin()
    shell()
    ia = door()
    dd = desk_zone()
    seating_and_tea()
    fireplace()
    bookcases_and_portraits()
    mount("cabinet_mount", (2.67, 0.0, 0.30))
    mount("light_desk_lamp", (0.05, 1.12, -1.25))
    mount("light_window_n", (0.4, 2.4, -2.1))
    for g, lst in grp.items():
        X.top(lst, 3)
    objs = {}
    for g, lst in grp.items():
        objs[g] = X.join_all(g, lst)
        objs[g].name = g
        objs[g].data.name = g
        M.set_origin(objs[g], G(0, 0, 0))
    req = list(grp.keys()) + ["IA_door_gallery", "IA_desk_drawer", "cabinet_mount", "tea_mount", "light_desk_lamp", "light_window_n", "light_fire"]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["IA_door_gallery", "IA_desk_drawer"], budget=BUDGET,
                          expect={"IA_door_gallery": (X0 + 0.045, 0.0, -0.7), "IA_desk_drawer": (0.4, 0.59, -0.83)}, show=["IA_door_gallery", "IA_desk_drawer"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")


main()
