"""archivist_desk.glb — institutional oak pedestal desk of the Archive B archivist (Chapter 2; group B2).

1.50 x 0.75, top y = 0.76. Free-standing: origin on the floor at the footprint centre, front +Z (placed at
world (3.7, 0, -3.1), yaw 0, its back 2.5 cm off the north wall).
Left pedestal with three drawers, right pedestal with a drawer over a panelled cupboard, a centre drawer over
the kneehole, a modesty panel, and a green writing inlay (M_Book_Green: dark green leather-cloth; the
M_Linoleum slot is the floor's 0.6 m checker texture, wrong on a desk). A low pigeonhole gallery stands at
the back centre (top y = 0.995).

Dressing (static), placed around the spots the code fills (model coords):
  card_punch footprint x -0.64..-0.26, z -0.10..0.20     tape_deck footprint x 0.21..0.69, z -0.14..0.24
  desk_lamp at (-0.65, -0.22)                             CC0 book set from (0.30, -0.26) to the right
  -> two-tier wire in/out trays (back left), a bakelite rotary telephone and a rubber-stamp carousel (back
     centre, in front of the gallery), a blotter pad (front centre), a card-file box (front left corner).
Parts: none (no IA parts). Static meshes: desk, gallery, desk_dressing.

    blender -b --factory-startup -P tools/blender/models/archivist_desk.py [-- --no-render] [--shots a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_props as P  # noqa: E402
import lib_ch2_furniture2 as F  # noqa: E402
from lib_ch2_furniture2 import G  # noqa: E402

NAME = "archivist_desk"
ARGS = M.main_guard()
BUDGET = 6000

TOP = 0.76
W2, D2 = 0.75, 0.375
TOP0 = 0.728
PED = ((-0.73, -0.33), (0.33, 0.73))      # pedestal x ranges (left, right)
PZ = (-0.355, 0.345)                      # carcass z range (front faces at 0.345, fronts proud to 0.363)
PLINTH = 0.075
WOOD = "M_Wood_Panel"

parts = {}


def cup_pull(name, cx, cy, cz, w=0.072):
    out = [F.gslab(name + "_plate", (cx, cy, cz), w + 0.010, 0.030, 0.0015, r=0.006, mat="M_Brass_Aged", plane="xy",
                   bevel=0.0, n=3)]
    outer, inner = [], []
    for j in range(7):
        th = math.radians(90 - 125 * j / 6)
        outer.append((0.0135 * math.cos(th), 0.0135 * math.sin(th)))
        inner.append((0.0118 * math.cos(th), 0.0118 * math.sin(th)))
    loop = [(0.0, 0.0135)] + outer[1:] + list(reversed(inner[1:])) + [(0.0, 0.0118)]
    out.append(F.gpoly(name + "_hood", [loop], w - 0.008, (cx + (w - 0.008) / 2, cy + 0.002, cz + 0.0015), (0, 0, 1),
                       (0, 1, 0), mat="M_Brass_Aged", bevel=0.0))
    return out


# ------------------------------------------------------------------ desk body
def build_desk():
    d = []
    # top with a rounded front edge, the green inlay and a thin brass-free border groove
    d.append(F.gbox("top", (-W2, TOP0, -D2), (W2, TOP, D2), mat=WOOD, bevel=0.006, seg=2))
    d.append(F.gbox("inlay", (-0.665, TOP - 0.001, -0.262), (0.665, TOP + 0.0004, 0.300), mat="M_Book_Green", bevel=0.0))
    for nm, mn, mx in (("groove_f", (-0.671, TOP - 0.0006, 0.300), (0.671, TOP + 0.0002, 0.306)),
                       ("groove_b", (-0.671, TOP - 0.0006, -0.268), (0.671, TOP + 0.0002, -0.262)),
                       ("groove_l", (-0.671, TOP - 0.0006, -0.262), (-0.665, TOP + 0.0002, 0.300)),
                       ("groove_r", (0.665, TOP - 0.0006, -0.262), (0.671, TOP + 0.0002, 0.300))):
        d.append(F.gbox(nm, mn, mx, mat="M_Bakelite", bevel=0.0))
    for k, (x0, x1) in enumerate(PED):
        # plinth (recessed), carcass, side panels with a raised field
        d.append(F.gbox(f"plinth_{k}", (x0 + 0.012, 0.0, PZ[0] + 0.01), (x1 - 0.012, PLINTH, PZ[1] - 0.012), mat=WOOD,
                        bevel=0.003))
        d.append(F.gbox(f"carcass_{k}", (x0, PLINTH, PZ[0]), (x1, TOP0, PZ[1]), mat=WOOD, bevel=0.004))
        d.append(F.gbox(f"base_band_{k}", (x0 - 0.006, PLINTH, PZ[0] - 0.004), (x1 + 0.006, PLINTH + 0.022, PZ[1] + 0.022),
                        mat=WOOD, bevel=0.004))
        fx0, fx1 = (x0 - 0.004, x0 + 0.001) if k == 0 else (x1 - 0.001, x1 + 0.004)
        d.append(F.gbox(f"side_field_{k}", (fx0, 0.16, PZ[0] + 0.07), (fx1, 0.66, PZ[1] - 0.07), mat=WOOD, bevel=0.006))
    # left pedestal: three drawers (shallow, middle, deep) with brass cup pulls and card holders
    x0, x1 = PED[0]
    cx = (x0 + x1) / 2
    for i, (ya, yb) in enumerate(((0.560, 0.715), (0.360, 0.548), (0.105, 0.348))):
        d.append(F.gbox(f"ldrawer_{i}", (x0 + 0.012, ya, PZ[1]), (x1 - 0.012, yb, PZ[1] + 0.018), mat=WOOD, bevel=0.004,
                        seg=1))
        yc = (ya + yb) / 2
        d += cup_pull(f"lpull_{i}", cx, yc - 0.008, PZ[1] + 0.018)
        d += F.card_holder(f"llabel_{i}", (cx, yc + 0.030, PZ[1] + 0.018), w=0.060, h=0.024)
    # right pedestal: top drawer + panelled cupboard door with a knob and an escutcheon
    x0, x1 = PED[1]
    cx = (x0 + x1) / 2
    d.append(F.gbox("rdrawer", (x0 + 0.012, 0.560, PZ[1]), (x1 - 0.012, 0.715, PZ[1] + 0.018), mat=WOOD, bevel=0.004,
                    seg=1))
    d += cup_pull("rpull", cx, 0.630, PZ[1] + 0.018)
    d += F.card_holder("rlabel", (cx, 0.668, PZ[1] + 0.018), w=0.060, h=0.024)
    d.append(F.gbox("rdoor", (x0 + 0.012, 0.105, PZ[1]), (x1 - 0.012, 0.548, PZ[1] + 0.018), mat=WOOD, bevel=0.004, seg=1))
    d.append(F.gbox("rdoor_field", (x0 + 0.050, 0.145, PZ[1] + 0.016), (x1 - 0.050, 0.508, PZ[1] + 0.024), mat=WOOD,
                    bevel=0.008))
    d.append(F.glathe("rdoor_knob", [(0.0, 0.0), (0.011, 0.0), (0.006, 0.007), (0.0065, 0.013), (0.013, 0.021),
                                     (0.012, 0.029), (0.0, 0.031)], (x0 + 0.045, 0.40, PZ[1] + 0.018), axis="z",
                      segments=8, mat="M_Brass_Aged"))
    d.append(F.gslab("rdoor_esc", (x0 + 0.045, 0.445, PZ[1] + 0.018), 0.016, 0.030, 0.0012, r=0.007, mat="M_Brass_Aged",
                     plane="xy", bevel=0.0, n=3))
    d.append(F.gslab("rdoor_keyhole", (x0 + 0.045, 0.4465, PZ[1] + 0.0192), 0.0045, 0.012, 0.0004, r=0.002,
                     mat="M_Bakelite", plane="xy", bevel=0.0, n=2))
    # kneehole: centre drawer, rails, modesty panel
    d.append(F.gbox("knee_rail", (-0.33, 0.632, PZ[1] - 0.02), (0.33, TOP0, PZ[1]), mat=WOOD, bevel=0.002))
    d.append(F.gbox("cdrawer", (-0.318, 0.640, PZ[1]), (0.318, 0.718, PZ[1] + 0.018), mat=WOOD, bevel=0.004, seg=1))
    d += cup_pull("cpull", 0.0, 0.676, PZ[1] + 0.018, w=0.09)
    d.append(F.gbox("modesty", (-0.33, 0.20, -0.335), (0.33, 0.632, -0.315), mat=WOOD, bevel=0.003))
    d.append(F.gbox("modesty_field", (-0.29, 0.24, -0.317), (0.29, 0.60, -0.309), mat=WOOD, bevel=0.008))
    parts["desk"] = F.part("desk", d)


# ------------------------------------------------------------------ gallery (pigeonholes)
def build_gallery():
    g = []
    gx0, gx1, gz0, gz1 = -0.25, 0.25, -0.372, -0.270
    ytop = 0.995
    for x in (gx0, gx1):
        g.append(F.gbox(f"gal_side_{x}", (x - 0.008, TOP, gz0), (x + 0.008, ytop - 0.012, gz1), mat=WOOD, bevel=0.002))
    g.append(F.gbox("gal_top", (gx0 - 0.016, ytop - 0.014, gz0 - 0.002), (gx1 + 0.016, ytop, gz1 + 0.010), mat=WOOD,
                    bevel=0.003))
    g.append(F.gbox("gal_back", (gx0, TOP, gz0), (gx1, ytop - 0.012, gz0 + 0.008), mat=WOOD, bevel=0.0))
    g.append(F.gbox("gal_shelf", (gx0, 0.872, gz0 + 0.008), (gx1, 0.882, gz1), mat=WOOD, bevel=0.0015))
    g.append(F.gbox("gal_base", (gx0, TOP, gz0 + 0.008), (gx1, TOP + 0.010, gz1), mat=WOOD, bevel=0.0015))
    for x in (-0.125, 0.0, 0.125):
        g.append(F.gbox(f"gal_div_{x}", (x - 0.005, TOP + 0.010, gz0 + 0.008), (x + 0.005, ytop - 0.014, gz1 - 0.004),
                        mat=WOOD, bevel=0.0012))
    # contents: papers, card bundles, envelopes, a rolled drawing
    rnd = random.Random(5)
    cells = [(cx, y0) for cx in (-0.1875, -0.0625, 0.0625, 0.1875) for y0 in (TOP + 0.010, 0.882)]
    for j, (cx, y0) in enumerate(cells):
        kind = j % 4
        if kind == 0:     # stack of papers
            for k in range(3):
                g.append(F.gbox(f"gal_paper_{j}_{k}", (cx - 0.052 + rnd.uniform(-0.003, 0.003), y0 + 0.004 * k, gz0 + 0.012),
                                (cx + 0.052 + rnd.uniform(-0.003, 0.003), y0 + 0.004 * k + 0.004, gz1 + 0.012), mat="M_Paper",
                                bevel=0.0))
        elif kind == 1:   # envelopes standing, leaning
            for k in range(3):
                e = F.gbox(f"gal_env_{j}_{k}", (cx - 0.004, y0, gz0 + 0.014), (cx - 0.001, y0 + 0.085, gz1 - 0.004),
                           mat="M_Paper" if k != 1 else "M_Cardboard", bevel=0.0)
                F.bake_xform(e, roll=-14 + 9 * k, about=(cx, y0, 0))
                e.location = G(-0.03 + 0.03 * k, 0, 0)
                M.apply_transform(e)
                g.append(e)
        elif kind == 2:   # bundle of index cards tied with string
            g.append(F.gbox(f"gal_cards_{j}", (cx - 0.040, y0, gz0 + 0.018), (cx + 0.040, y0 + 0.050, gz1 - 0.006),
                            mat="M_Paper", bevel=0.002))
            g.append(F.gbox(f"gal_string_{j}", (cx - 0.041, y0 + 0.022, gz0 + 0.017), (cx + 0.041, y0 + 0.0245, gz1 - 0.005),
                            mat="M_Cardboard", bevel=0.0))
        else:             # rolled drawing
            g.append(F.gcyl(f"gal_roll_{j}", 0.016, 0.12, (cx - 0.055, y0 + 0.017, gz1 - 0.035), axis="x", verts=10,
                            mat="M_Paper", bevel=0.0))
    parts["gallery"] = F.part("gallery", g)


# ------------------------------------------------------------------ dressing
def wire_tray(prefix, cx, cz, y0, w=0.20, d=0.27, h=0.055):
    o = []
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
    o.append(F.gbox(prefix + "_floor", (x0, y0, z0), (x1, y0 + 0.002, z1), mat="M_Steel_Dark", bevel=0.0))
    o.append(F.gtube(prefix + "_rim", [(x0, y0 + h, z0), (x1, y0 + h, z0), (x1, y0 + h, z1), (x0, y0 + h, z1),
                                       (x0, y0 + h, z0 + 0.002)], 0.0022, sides=5, mat="M_Chrome"))
    for x in (x0, x1):
        for z in (z0, z1):
            o.append(F.gcyl(f"{prefix}_post_{x:.2f}_{z:.2f}", 0.002, h, (x, y0, z), verts=5, mat="M_Chrome", bevel=0.0))
    for k in range(1, 4):
        x = x0 + w * k / 4
        o.append(F.gtube(f"{prefix}_wire_{k}", [(x, y0 + 0.002, z0), (x, y0 + h, z0)], 0.0013, sides=4, mat="M_Chrome",
                         caps=False))
        o.append(F.gtube(f"{prefix}_wirez_{k}", [(x0, y0 + 0.002, z0 + d * k / 4), (x0, y0 + h, z0 + d * k / 4)], 0.0013,
                         sides=4, mat="M_Chrome", caps=False))
        o.append(F.gtube(f"{prefix}_wirex_{k}", [(x1, y0 + 0.002, z0 + d * k / 4), (x1, y0 + h, z0 + d * k / 4)], 0.0013,
                         sides=4, mat="M_Chrome", caps=False))
    return o


def build_dressing():
    dr = []
    rnd = random.Random(11)
    # two-tier wire trays (back left, between the lamp and the gallery)
    tx, tz = -0.395, -0.235
    dr += wire_tray("tray_lo", tx, tz, TOP)
    dr += wire_tray("tray_hi", tx, tz, TOP + 0.075)
    for k in range(4):
        dr.append(F.gcyl(f"tray_riser_{k}", 0.0025, 0.075, (tx + (-0.096 if k % 2 else 0.096), TOP + 0.002,
                                                            tz + (-0.13 if k < 2 else 0.13)), verts=5, mat="M_Chrome",
                         bevel=0.0))
    for lvl, y0, n in ((0, TOP + 0.002, 6), (1, TOP + 0.077, 3)):
        for k in range(n):
            p = F.gbox(f"tray_sheet_{lvl}_{k}", (tx - 0.090, y0 + k * 0.0022, tz - 0.125), (tx + 0.090, y0 + (k + 1) * 0.0022,
                                                                                        tz + 0.125),
                       mat="M_Paper" if k % 3 else "M_Cardboard", bevel=0.0)
            F.bake_xform(p, yaw=rnd.uniform(-3, 3), about=(tx, 0, tz))
            dr.append(p)
    # rotary telephone (bakelite) at the back centre
    px, pz = -0.055, -0.140
    body = P.rrect_loft("phone_body", [(0.200, 0.230, 0.020, 0.0), (0.200, 0.230, 0.022, 0.005), (0.190, 0.220, 0.024, 0.020),
                                       (0.150, 0.100, 0.020, 0.085), (0.130, 0.085, 0.016, 0.092)], mat="M_Bakelite", n=3)
    body.location = G(px, TOP, pz)
    dr.append(body)
    # sloped dial face at the front of the body
    tilt = math.radians(43)
    dial_c = (px, TOP + 0.0525, pz + 0.080)
    dial = K.lathe2("phone_dial", [(0.0, 0.0), (0.036, 0.0), (0.037, 0.004), (0.033, 0.007), (0.0, 0.007)], segments=20,
                    mat="M_Chrome")
    dial.data.transform(Matrix.Rotation(tilt, 4, "X"))
    dial.location = G(*dial_c)
    dr.append(dial)
    card = K.lathe2("phone_dial_card", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.0075), (0.0, 0.0075)], segments=16,
                    mat="M_Enamel_Cream")
    card.data.transform(Matrix.Rotation(tilt, 4, "X"))
    card.location = G(*dial_c)
    dr.append(card)
    n_dir = Matrix.Rotation(tilt, 3, "X") @ Vector((0, 0, 1))
    u_dir = Matrix.Rotation(tilt, 3, "X") @ Vector((1, 0, 0))
    v_dir = Matrix.Rotation(tilt, 3, "X") @ Vector((0, 1, 0))
    for k in range(10):
        a = math.radians(60 + 27 * k)
        hc = Vector(G(*dial_c)) + n_dir * 0.0072 + (u_dir * math.cos(a) + v_dir * math.sin(a)) * 0.0255
        hole = F.gdisc(f"phone_hole_{k}", (0, 0, 0), 0.0050, normal="y", up="-z", mat="M_Bakelite", n=7)
        hole.data.transform(Matrix.Rotation(tilt, 4, "X"))
        hole.location = hc
        dr.append(hole)
    # cradle prongs + handset across them
    for sx in (-1, 1):
        dr.append(F.gbox(f"phone_prong_{sx}", (px + sx * 0.050 - 0.010, TOP + 0.088, pz - 0.040),
                         (px + sx * 0.050 + 0.010, TOP + 0.106, pz + 0.010), mat="M_Bakelite", bevel=0.004))
    hs = [G(px - 0.098, TOP + 0.122, pz - 0.016), G(px - 0.060, TOP + 0.130, pz - 0.018), G(px, TOP + 0.133, pz - 0.018),
          G(px + 0.060, TOP + 0.130, pz - 0.018), G(px + 0.098, TOP + 0.122, pz - 0.016)]
    dr.append(P.tube("phone_handle", hs, 0.0125, sides=10, mat="M_Bakelite"))
    for sx in (-1, 1):
        cup = F.glathe(f"phone_cup_{sx}", [(0.0, 0.0), (0.022, 0.0), (0.026, 0.006), (0.027, 0.016), (0.018, 0.026),
                                           (0.012, 0.030)], (px + sx * 0.100, TOP + 0.094, pz - 0.016), segments=10,
                       mat="M_Bakelite")
        dr.append(cup)
    # coiled cord from the handset end to the body side
    coil = []
    for i in range(29):
        t = i / 28
        a = t * 11 * 2 * math.pi
        base = Vector((px - 0.11 - 0.03 * t, pz - 0.01 + 0.07 * t))
        coil.append((base.x + 0.006 * math.cos(a), TOP + 0.008 + 0.006 * math.sin(a), base.y))
    dr.append(F.gtube("phone_cord", coil, 0.0016, sides=4, mat="M_Bakelite"))
    # rubber-stamp carousel
    sx_, sz_ = 0.130, -0.190
    dr.append(F.glathe("stamp_base", [(0.0, 0.0), (0.056, 0.0), (0.056, 0.008), (0.050, 0.013), (0.012, 0.016),
                                      (0.0, 0.016)], (sx_, TOP, sz_), segments=14, mat="M_Wood_Walnut"))
    dr.append(F.gcyl("stamp_post", 0.006, 0.120, (sx_, TOP + 0.016, sz_), verts=10, mat="M_Chrome", bevel=0.0))
    dr.append(F.glathe("stamp_rack", [(0.0, 0.0), (0.048, 0.0), (0.048, 0.006), (0.0, 0.006)], (sx_, TOP + 0.100, sz_),
                       segments=16, mat="M_Wood_Walnut"))
    dr.append(F.glathe("stamp_finial", [(0.0, 0.0), (0.008, 0.002), (0.010, 0.010), (0.006, 0.017), (0.0, 0.019)],
                       (sx_, TOP + 0.130, sz_), segments=10, mat="M_Wood_Walnut"))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        hx, hz = sx_ + 0.038 * math.cos(a), sz_ + 0.038 * math.sin(a)
        dr.append(F.glathe(f"stamp_{k}", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.006), (0.0045, 0.009), (0.005, 0.036),
                                          (0.0075, 0.046), (0.0055, 0.054), (0.0, 0.055)], (hx, TOP + 0.042, hz),
                           segments=5, mat="M_Wood_Walnut"))
        dr.append(F.gcyl(f"stamp_rubber_{k}", 0.0095, 0.004, (hx, TOP + 0.038, hz), verts=8, mat="M_Rubber", bevel=0.0))
    # blotter pad with leather corners (front centre)
    bx0, bx1, bz0, bz1 = -0.215, 0.170, 0.035, 0.330
    dr.append(F.gbox("blotter_board", (bx0, TOP, bz0), (bx1, TOP + 0.004, bz1), mat="M_Cardboard", bevel=0.001))
    dr.append(F.gbox("blotter_sheet", (bx0 + 0.004, TOP + 0.004, bz0 + 0.004), (bx1 - 0.004, TOP + 0.0048, bz1 - 0.004),
                     mat="M_Paper", bevel=0.0))
    for (cxx, czz, sx2, sz2) in ((bx0, bz0, 1, 1), (bx1, bz0, -1, 1), (bx0, bz1, 1, -1), (bx1, bz1, -1, -1)):
        tri = [(0.0, 0.0), (0.055 * sx2, 0.0), (0.0, -0.055 * sz2)]
        if sx2 * sz2 < 0:
            tri = list(reversed(tri))
        dr.append(F.gpoly(f"blotter_corner_{cxx:.2f}_{czz:.2f}", [tri], 0.0016, (cxx, TOP + 0.004, czz), (1, 0, 0),
                          (0, 0, -1), mat="M_Leather", bevel=0.0004))
    # a few scattered cards and a pencil on the blotter
    for k in range(3):
        c = F.gbox(f"loose_card_{k}", (-0.0625, TOP + 0.0049 + 0.0004 * k, -0.0375), (0.0625, TOP + 0.0053 + 0.0004 * k,
                                                                                        0.0375), mat="M_Paper", bevel=0.0)
        F.bake_xform(c, yaw=rnd.uniform(-25, 25))
        c.location = G(-0.08 + 0.05 * k, 0, 0.16 + 0.03 * k)
        M.apply_transform(c)
        dr.append(c)
    pen = F.gcyl("pencil", 0.0035, 0.16, (0.0, TOP + 0.0085, 0.27), axis="x", verts=6, mat="M_Enamel_Amber", bevel=0.0)
    tip = F.gcyl("pencil_tip", 0.0035, 0.014, (0.16, TOP + 0.0085, 0.27), axis="x", verts=6, mat="M_Wood_Panel", bevel=0.0,
                 r_top=0.0008)
    for o in (pen, tip):
        F.bake_xform(o, yaw=-18.0, about=(0.08, 0, 0.27))
        o.location = G(-0.06, 0, 0)
        M.apply_transform(o)
    dr += [pen, tip]
    # card-file box (front left corner): oak box, open lid propped back, cards, brass label holder
    fx, fz = -0.645, 0.290
    dr.append(F.gbox("cardfile_box", (fx - 0.065, TOP, fz - 0.075), (fx + 0.065, TOP + 0.085, fz + 0.075), mat="M_Wood_Walnut",
                     bevel=0.004))
    dr.append(F.gbox("cardfile_cards", (fx - 0.058, TOP + 0.020, fz - 0.068), (fx + 0.058, TOP + 0.093, fz + 0.050),
                     mat="M_Paper", bevel=0.002))
    for k in range(3):
        dr.append(F.gbox(f"cardfile_tab_{k}", (fx - 0.050 + 0.035 * k, TOP + 0.093, fz - 0.040 + 0.035 * k),
                         (fx - 0.030 + 0.035 * k, TOP + 0.101, fz - 0.038 + 0.035 * k), mat="M_Cardboard", bevel=0.0))
    lid = F.gbox("cardfile_lid", (fx - 0.067, 0.0, -0.008), (fx + 0.067, 0.152, 0.0), mat="M_Wood_Walnut", bevel=0.003)
    F.bake_xform(lid, pitch=-18.0, about=(fx, 0.0, 0.0))
    lid.location = G(0.0, TOP + 0.085, fz - 0.075)
    M.apply_transform(lid)
    dr.append(lid)
    dr += F.card_holder("cardfile_label", (fx, TOP + 0.045, fz + 0.075), w=0.050, h=0.020)
    parts["dressing"] = F.part("desk_dressing", dr)


def build():
    M.reset_scene()
    F.ensure_materials()
    build_desk()
    build_gallery()
    build_dressing()
    F.finalize_all()
    return F.report(NAME)


REQUIRED = ["desk", "gallery", "desk_dressing"]


def main():
    total = build()
    path = F.export(NAME)
    errs = F.verify_glb(path, required=REQUIRED, identity=REQUIRED, budget=BUDGET, show=REQUIRED)
    print(f"[archivist_desk] tris={total} errors={len(errs)}")
    if "--no-render" in ARGS:
        return
    qa()


def proxy_box(name, centre, size, mat):
    cx, cy, cz = centre
    return F.gbox(name, (cx - size[0] / 2, cy, cz - size[2] / 2), (cx + size[0] / 2, cy + size[1], cz + size[2] / 2),
                  mat=mat, bevel=0.004)


def qa():
    F.qa_begin()
    F.qa_room("desk")
    F.qa_place((3.7, 0.0, -3.1), 0.0)
    F.qa_neighbours([("desk_lamp", (3.05, 0.76, -3.32), 20.0), ("chair", (3.55, 0.0, -2.35), 172.0),
                     ("cc0/book_encyclopedia_set_01/book_encyclopedia_set_01", (4.0, 0.76, -3.36), 0.0),
                     ("vault_door", (1.5, 0.0, -3.5), 0.0)])
    for nm, pos, size, mat in (("card_punch", (3.25, 0.76, -3.05), (0.36, 0.14, 0.28), "M_Steel_Cream"),
                               ("tape_deck", (4.15, 0.76, -3.05), (0.46, 0.16, 0.36), "M_Steel_Painted")):
        if F.qa_import(F.model_glb(nm), (pos[0], pos[1], pos[2]), 0.0) is None:
            proxy_box("qa_proxy_" + nm, pos, size, mat)
    F.qa_light("desk_lamp", "POINT", (3.1, 1.2, -3.2), 20.0, "FFB46B", radius=0.03)
    F.qa_light("pendant_2", "POINT", (3.0, 2.75, -2.0), 120.0, "FFC58A", radius=0.1)
    M.refresh()
    if F.want("view", ARGS):
        F.shoot(NAME + "_2", (3.7, 1.6, -1.85), (3.7, 0.8, -3.1), vfov=52, world=0.10)
    if F.want("hero", ARGS):
        F.shoot(NAME, (2.55, 1.45, -1.75), (3.75, 0.62, -3.05), vfov=50, world=0.12)
    if F.want("close", ARGS):
        F.shoot(NAME + "_3", (3.55, 1.25, -2.55), (3.62, 0.84, -3.3), vfov=44, world=0.10)


main()
