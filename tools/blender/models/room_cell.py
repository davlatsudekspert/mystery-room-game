"""room_cell.glb — R3 the Night Cell (Level -1), Leyla's hidden home, built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3b/§7. "A grandmother's attic, kept warm": amber, wool, wood, one low lamp, kettle tick, soft pipe hum.
Deliberately the opposite of the Pump Room: no iron or rivets, patterned ochre wallpaper over walnut wainscoting, a planked floor with an oval wool rug,
a cream cast radiator under a curtained window, a cloth-shaded pendant lamp, shelves of jars and books, a coat on the hooks.
Interior x [-2.2, 2.2], z [-2.0, 2.0], ceiling 2.70 (walls 0.25 thick outside). Openings:
  west   z [-1.55, -0.65], y [0, 2.1]   the doorway from the Pump Room (the leaf `IA_door_cell` lives in `room_pump`; its free edge opens INTO the cell)
  east   z [-0.45, 0.45],  y [0, 2.1]   the insulated door to the Cold Store (model `cold_door`: placed at (2.2, 0, 0), yaw -90)
Placement in the building: the cell origin sits at world (6.2, 0, 0) relative to the Pump Room origin (the cell's west wall then touches the Pump
Room's east wall, forming a 0.5 m deep doorway), yaw 0. No lighting is baked: the lights are empties (below).

Suggested placements of the separate models (room coordinates, yaw): see the empties `cot_mount`, `light_table_mount`, `kettle_mount`, `diary_mount`,
`cold_door_mount`, `acetate_mount_a/b/c`. (The empties carry the position; the yaw is documented in docs/models/ch2_exp.md.)

Own objects (static unless noted): floor, wall_n, wall_e, wall_s, wall_w, ceiling, trim, rug, furniture (desk, chair, armchair, sideboard, bookcase,
shelves, cork board), radiator, window (frame, dark glass, curtains), dressing (jars, books, mugs, plant, basket, coat, slippers, boots, pinned papers),
lamp_ceiling (pendant, shade) + lamp_ceiling_glow (bulb, M_Emissive_Warm) + lamp_desk (table lamp) + lamp_desk_glow. Empties: light_lamp_ceiling
(0.0, 2.02, 0.20), light_lamp_desk (2.0, 1.10, -1.72), light_fill (-1.2, 1.9, 1.2), light_cot_fill (-0.8, 1.2, -1.2).

    blender -b --factory-startup -P tools/blender/models/room_cell.py [-- --no-render]
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

NAME = "room_cell"
BUDGET = 26000
ARGS = M.main_guard()
X0, X1, Z0, Z1, H, T = -2.2, 2.2, -2.0, 2.0, 2.70, 0.25
WOOD, PANEL, BRASS, WOOL, PLASTER = "M_Wood_Walnut", "M_Wood_Panel", "M_Brass_Aged", "M_Wool_Knit", "M_Plaster_Wall"
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def at(objs, pos, yaw=0.0):
    """Rotate a list of objects about the Godot Y axis by `yaw` degrees, then move them to the Godot point `pos`."""
    m = Matrix.Translation(GV(pos)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
    for o in objs:
        if o is not None:
            A.place(o, m)                    # bake the object's own location together with the move (gbox objects carry a location)
    return objs


# ---------------------------------------------------------------- shell
def shell():
    ops = {"w": [(-1.55, -0.65, 0.0, 2.1)], "e": [(-0.45, 0.45, 0.0, 2.1)]}
    mats = {k: (PANEL, 0.95, "M_Wallpaper_Cell") for k in "nsew"}
    w = X.wallset("cell", X0, X1, Z0, Z1, H, T, mats, ops, floor_mat="M_Wood_Floor", ceil_mat=PLASTER)
    for k in "nsew":
        add("wall_" + k, *w[k])
    add("floor", *w["floor"])
    add("ceiling", *w["ceiling"])
    t = []
    # baseboard + chair rail + crown (skipping the two openings and the west doorway casing)
    def run(nm, mn, mx, mat=WOOD):
        t.append(gbox(nm, mn, mx, mat, bevel=0.002))
    for y0, y1, d, tag in ((0.0, 0.13, 0.018, "bb"), (0.93, 0.97, 0.022, "cr")):
        run(f"{tag}_n", (X0, y0, Z0), (X1, y1, Z0 + d))
        run(f"{tag}_s", (X0, y0, Z1 - d), (X1, y1, Z1))
        run(f"{tag}_w1", (X0, y0, Z0), (X0 + d, y1, -1.68))
        run(f"{tag}_w2", (X0, y0, -0.52), (X0 + d, y1, Z1))
        run(f"{tag}_e1", (X1 - d, y0, Z0), (X1, y1, -0.60))
        run(f"{tag}_e2", (X1 - d, y0, 0.60), (X1, y1, Z1))
    for nm, mn, mx in (("cw_n", (X0, H - 0.07, Z0), (X1, H, Z0 + 0.06)), ("cw_s", (X0, H - 0.07, Z1 - 0.06), (X1, H, Z1)),
                       ("cw_w", (X0, H - 0.07, Z0), (X0 + 0.06, H, Z1)), ("cw_e", (X1 - 0.06, H - 0.07, Z0), (X1, H, Z1))):
        run(nm, mn, mx, PLASTER)
    # west doorway: reveal liners (wood), architrave on the cell side
    for nm, mn, mx in (("jb_n", (X0 - T, 0.0, -1.55), (X0, 2.1, -1.52)), ("jb_s", (X0 - T, 0.0, -0.68), (X0, 2.1, -0.65)),
                       ("jb_h", (X0 - T, 2.07, -1.55), (X0, 2.1, -0.65)),
                       ("ar_n", (X0, 0.0, -1.68), (X0 + 0.02, 2.24, -1.55)), ("ar_s", (X0, 0.0, -0.65), (X0 + 0.02, 2.24, -0.52)),
                       ("ar_h", (X0, 2.10, -1.68), (X0 + 0.02, 2.24, -0.52)), ("sill_w", (X0 - T, 0.0, -1.55), (X0 + 0.03, 0.02, -0.65))):
        t.append(gbox(nm, mn, mx, WOOD, bevel=0.003))
    add("trim", *t)


def beams_ceiling():
    add("ceiling", gbox("beam", (X0, H - 0.12, -0.25), (X1, H, -0.05), WOOD, bevel=0.008))      # one low beam across the room


# ---------------------------------------------------------------- furniture
def desk():
    o = []
    x0, x1, z0, z1, top = 0.50, 2.14, -1.99, -1.34, 0.76
    o.append(gbox("dk_top", (x0, top - 0.04, z0), (x1, top, z1), WOOD, bevel=0.005, seg=2))
    o.append(gbox("dk_lip", (x0 + 0.01, top - 0.075, z1 - 0.07), (x1 - 0.01, top - 0.04, z1 - 0.02), WOOD, bevel=0.003))
    for x in (x0 + 0.05, x1 - 0.05):
        for z in (z0 + 0.06, z1 - 0.05):
            o.append(glathe(f"dk_leg{x}{z}", [(0.0, 0.0), (0.020, 0.0), (0.026, 0.08), (0.030, 0.30), (0.032, 0.60), (0.036, 0.72), (0.0, 0.72)], (x, 0.0, z), axis="y",
                            segments=8, mat=WOOD))
    o.append(gbox("dk_back", (x0 + 0.04, 0.18, z0 + 0.02), (x1 - 0.04, top - 0.04, z0 + 0.045), PANEL, bevel=0.002))
    # drawer pedestal under the left half (front +Z)
    px0, px1 = x0 + 0.04, x0 + 0.58
    o.append(gbox("dk_ped", (px0, 0.12, z0 + 0.04), (px1, top - 0.04, z1 - 0.06), WOOD, bevel=0.004))
    for i, (y0, y1) in enumerate(((0.52, 0.72), (0.30, 0.50), (0.12, 0.28))):
        o.append(gbox(f"dk_dr{i}", (px0 + 0.02, y0, z1 - 0.063), (px1 - 0.02, y1, z1 - 0.045), PANEL, bevel=0.003))
        o.append(gcyl(f"dk_kn{i}", 0.011, 0.016, ((px0 + px1) / 2, (y0 + y1) / 2, z1 - 0.045), axis="z", verts=10, mat=BRASS, bevel=0.002))
    o.append(gbox("dk_base", (px0 - 0.005, 0.0, z0 + 0.035), (px1 + 0.005, 0.12, z1 - 0.055), WOOD, bevel=0.003))
    # a green blotter under the table, a pen tray, a stack of papers: dressing on the desk top
    add("furniture", *o)


def chair(name, pos, yaw, seat_h=0.46, wool=False):
    o = []
    for x in (-0.19, 0.19):
        for z in (-0.18, 0.18):
            o.append(gbox(f"{name}_l{x}{z}", (x - 0.022, 0.0, z - 0.022), (x + 0.022, seat_h, z + 0.022), WOOD, bevel=0.004))
    for z in (-0.18, 0.18):
        o.append(gbox(f"{name}_sr{z}", (-0.19, 0.17, z - 0.012), (0.19, 0.20, z + 0.012), WOOD, bevel=0.002))
    o.append(gbox(f"{name}_seat", (-0.225, seat_h, -0.215), (0.225, seat_h + 0.035, 0.215), WOOD, bevel=0.01, seg=2))
    # back: two posts + three slats + top rail (back toward -Z)
    for x in (-0.19, 0.19):
        o.append(gbox(f"{name}_bp{x}", (x - 0.02, seat_h + 0.03, -0.20), (x + 0.02, seat_h + 0.46, -0.16), WOOD, bevel=0.004))
    for i in range(3):
        yy = seat_h + 0.10 + 0.11 * i
        o.append(gbox(f"{name}_bs{i}", (-0.17, yy, -0.188), (0.17, yy + 0.06, -0.176), WOOD, bevel=0.003))
    o.append(gbox(f"{name}_br", (-0.215, seat_h + 0.44, -0.205), (0.215, seat_h + 0.50, -0.155), WOOD, bevel=0.01, seg=2))
    if wool:
        o.append(gbox(f"{name}_cu", (-0.19, seat_h + 0.035, -0.17), (0.19, seat_h + 0.07, 0.19), WOOL, bevel=0.012, seg=2))
    return at(o, pos, yaw)


def armchair():
    o = []
    s = 0.42
    for x in (-0.26, 0.26):
        for z in (-0.24, 0.24):
            o.append(gbox(f"ac_l{x}{z}", (x - 0.03, 0.0, z - 0.03), (x + 0.03, s, z + 0.03), WOOD, bevel=0.005))
    o.append(gbox("ac_seat", (-0.31, s, -0.29), (0.31, s + 0.07, 0.29), WOOD, bevel=0.012, seg=2))
    o.append(gbox("ac_cush", (-0.28, s + 0.07, -0.23), (0.28, s + 0.17, 0.27), WOOL, bevel=0.035, seg=3))
    for x in (-0.31, 0.31):                                   # arms
        o.append(gbox(f"ac_arm{x}", (x - 0.03, s + 0.07, -0.29), (x + 0.03, s + 0.30, 0.29), WOOD, bevel=0.008))
        o.append(gbox(f"ac_armtop{x}", (x - 0.05, s + 0.30, -0.28), (x + 0.05, s + 0.33, 0.20), WOOD, bevel=0.01, seg=2))
    o.append(gbox("ac_back", (-0.31, s + 0.07, -0.31), (0.31, s + 0.70, -0.25), WOOD, bevel=0.012, seg=2))
    o.append(gbox("ac_bcush", (-0.27, s + 0.17, -0.25), (0.27, s + 0.62, -0.19), WOOL, bevel=0.04, seg=3))
    # throw over the back (cream striped wool drape)
    def sec(x):
        return [(-0.34, s + 0.30), (-0.31, s + 0.58), (-0.27, s + 0.72 + 0.006 * math.sin(x * 12)), (-0.22, s + 0.66), (-0.20, s + 0.40), (-0.19, s + 0.26)]
    o.append(Q.drape("ac_throw", [-0.22 + 0.44 * i / 10 for i in range(11)], sec, thick=0.014, mat="M_Dress_Wool", folds=0.004, seed=1.2))
    return at(o, (-1.38, 0.0, 1.28), 128.0)


def sideboard():
    o = []
    x0, x1, z0, z1, top = -1.55, 0.05, 1.52, 1.99, 0.86
    o.append(gbox("sb_body", (x0, 0.10, z0), (x1, top - 0.04, z1), WOOD, bevel=0.004))
    o.append(gbox("sb_top", (x0 - 0.02, top - 0.04, z0 - 0.025), (x1 + 0.02, top, z1), WOOD, bevel=0.006, seg=2))
    o.append(gbox("sb_base", (x0 + 0.02, 0.0, z0 + 0.02), (x1 - 0.02, 0.10, z1 - 0.02), WOOD, bevel=0.003))
    for i in range(2):                                            # two panelled doors facing -Z
        dx0 = x0 + 0.03 + i * (x1 - x0 - 0.06) / 2 + 0.005
        dx1 = dx0 + (x1 - x0 - 0.06) / 2 - 0.01
        o.append(gbox(f"sb_door{i}", (dx0, 0.13, z0 - 0.012), (dx1, top - 0.07, z0 + 0.002), PANEL, bevel=0.004))
        o.append(gbox(f"sb_pan{i}", (dx0 + 0.05, 0.19, z0 - 0.020), (dx1 - 0.05, top - 0.13, z0 - 0.012), WOOD, bevel=0.004))
        o.append(gcyl(f"sb_kn{i}", 0.012, 0.018, (dx0 + 0.03 if i == 1 else dx1 - 0.03, 0.50, z0 - 0.012), axis="-z", verts=10, mat=BRASS, bevel=0.002))
    add("furniture", *o)


def bookcase():
    o = []
    x0, x1, z0, z1, ht = 0.62, 1.98, 1.72, 1.99, 1.95
    o.append(gbox("bc_l", (x0, 0.0, z0), (x0 + 0.03, ht, z1), PANEL, bevel=0.003))
    o.append(gbox("bc_r", (x1 - 0.03, 0.0, z0), (x1, ht, z1), PANEL, bevel=0.003))
    o.append(gbox("bc_back", (x0, 0.0, z1 - 0.012), (x1, ht, z1), PANEL, bevel=0.0))
    o.append(gbox("bc_top", (x0 - 0.02, ht, z0 - 0.02), (x1 + 0.02, ht + 0.035, z1), WOOD, bevel=0.005))
    o.append(gbox("bc_plinth", (x0, 0.0, z0), (x1, 0.08, z0 + 0.02), WOOD, bevel=0.002))
    ys = (0.08, 0.50, 0.88, 1.26, 1.62)
    for i, y in enumerate(ys):
        o.append(gbox(f"bc_sh{i}", (x0 + 0.03, y, z0), (x1 - 0.03, y + 0.022, z1 - 0.012), PANEL, bevel=0.002))
    mats = ["M_Book_Brown", "M_Book_Green", "M_Book_Red", "M_Book_Blue", "M_Book_Gold", "M_Book_Black"]
    # book rows on four shelves (spines toward -Z); gaps and leaning books give a lived-in look
    o += Q.book_row("bkA", x0 + 0.05, ys[0] + 0.022, z0 + 0.04, [0.04, 0.05, 0.035, 0.06, 0.045, 0.04, 0.05, 0.035, 0.055, 0.04, 0.05], 0.34, mats, depth=0.20)
    o += Q.book_row("bkB", x0 + 0.05, ys[1] + 0.022, z0 + 0.04, [0.05, 0.04, 0.06, 0.04, 0.05, 0.035, 0.045, 0.05], 0.32, mats[::-1], depth=0.20)
    o += Q.book_row("bkC", x0 + 0.60, ys[2] + 0.022, z0 + 0.04, [0.04, 0.05, 0.05, 0.04, 0.06, 0.035, 0.05], 0.30, mats[2:] + mats[:2], depth=0.20)
    o += Q.book_row("bkD", x0 + 0.05, ys[3] + 0.022, z0 + 0.04, [0.045, 0.05, 0.04, 0.055, 0.04, 0.05], 0.30, mats[1:] + mats[:1], depth=0.20)
    # stacked books lying flat on shelf 2 and the top
    for k, (w, d, hh, m) in enumerate(((0.26, 0.19, 0.04, "M_Book_Red"), (0.24, 0.17, 0.035, "M_Book_Green"), (0.22, 0.18, 0.03, "M_Book_Brown"))):
        o += Q.book(f"stk{k}", x0 + 0.08 + 0.01 * k, x0 + 0.08 + w, ys[2] + 0.022 + sum(h for h in (0.04, 0.035, 0.03)[:k]), z0 + 0.04, z0 + 0.04 + d, hh, m)
    add("furniture", *o)
    # things on the bookcase: a wool basket with yarn, a framed photo, two jars on the second shelf gap
    d = []
    d.append(glathe("basket", [(0.0, 0.0), (0.12, 0.0), (0.15, 0.17), (0.0, 0.17)], (1.55, ht + 0.035, 1.84), axis="y", segments=14, mat=PANEL))
    d.append(glathe("basket_rim", [(0.150, 0.165), (0.156, 0.17), (0.156, 0.185), (0.150, 0.185)], (1.55, ht + 0.035, 1.84), axis="y", segments=14, mat=WOOD))
    for k, (dx, dz, c) in enumerate(((-0.04, -0.02, WOOL), (0.05, 0.04, "M_Dress_Wool"), (0.0, -0.07, "M_Enamel_Cobalt"))):
        d.append(Q.gsphere(f"yarn{k}", 0.058, (1.55 + dx, ht + 0.035 + 0.19, 1.84 + dz), (1.0, 0.95, 1.0), mat=c, segs=10, rings=6))
    for s in (-1, 1):
        d.append(gcyl(f"needle{s}", 0.0035, 0.30, (1.55 + 0.02 * s, ht + 0.035 + 0.12, 1.84), axis=(0.30 * s, 1.0, 0.1), verts=5, mat="M_Wood_Panel", bevel=0.0))
    add("dressing", *d)


def shelves_north():
    """Two wall shelves and a cork board above the desk, with the clutter of a person who lives here."""
    o = []
    for i, y in enumerate((1.28, 1.62)):
        o.append(gbox(f"nsh{i}", (0.52, y, Z0), (2.10, y + 0.025, Z0 + 0.20), WOOD, bevel=0.003))
        for x in (0.62, 2.0):
            o.append(gbox(f"nbr{i}{x}", (x - 0.012, y - 0.10, Z0), (x + 0.012, y, Z0 + 0.15), WOOD, bevel=0.002))
    mats = ["M_Book_Brown", "M_Book_Green", "M_Book_Red", "M_Book_Blue", "M_Book_Gold", "M_Book_Black"]
    o += Q.book_row("nbA", 0.58, 1.305, Z0 + 0.03, [0.035, 0.05, 0.04, 0.05, 0.035, 0.045, 0.04, 0.05], 0.24, mats, depth=0.15)
    o += Q.book_row("nbB", 1.52, 1.305, Z0 + 0.03, [0.04, 0.035, 0.05], 0.22, mats[2:], depth=0.15)
    o += Q.jar("njA", 1.27, 1.305, Z0 + 0.10, 0.034, 0.12, "M_Glass_Amber", fill="M_Liquid_Crimson")
    o += Q.jar("njB", 1.38, 1.305, Z0 + 0.10, 0.030, 0.10, "M_Glass_Green", fill="M_Liquid_Green")
    o += Q.mug("nmg", 1.92, 1.305, Z0 + 0.10)
    o += Q.book_row("nbC", 0.58, 1.645, Z0 + 0.03, [0.05, 0.04, 0.05, 0.035, 0.05], 0.22, mats[1:], depth=0.15)
    o.append(gbox("ntin", (1.10, 1.645, Z0 + 0.04), (1.28, 1.745, Z0 + 0.16), "M_Enamel_Cream", bevel=0.006))
    o.append(gbox("ntin_lid", (1.098, 1.745, Z0 + 0.038), (1.282, 1.757, Z0 + 0.162), "M_Enamel_Crimson", bevel=0.004))
    o += Q.jar("njC", 1.60, 1.645, Z0 + 0.10, 0.028, 0.09, "M_Glass_Amber")
    # cork board with pinned papers
    o.append(gbox("cork", (0.62, 1.86, Z0), (1.96, 2.42, Z0 + 0.018), "M_Cork", bevel=0.003))
    o.append(gbox("cork_fr_b", (0.60, 1.84, Z0), (1.98, 1.86, Z0 + 0.026), WOOD, bevel=0.002))
    o.append(gbox("cork_fr_t", (0.60, 2.42, Z0), (1.98, 2.44, Z0 + 0.026), WOOD, bevel=0.002))
    o.append(gbox("cork_fr_l", (0.60, 1.86, Z0), (0.62, 2.42, Z0 + 0.026), WOOD, bevel=0.002))
    o.append(gbox("cork_fr_r", (1.96, 1.86, Z0), (1.98, 2.42, Z0 + 0.026), WOOD, bevel=0.002))
    for k, (cx, cy, w, h, rot) in enumerate(((0.80, 2.18, 0.20, 0.26, 0.05), (1.12, 2.05, 0.15, 0.20, -0.08), (1.45, 2.22, 0.22, 0.17, 0.04),
                                             (1.78, 2.08, 0.14, 0.22, -0.05), (1.30, 1.95, 0.10, 0.07, 0.1))):
        pa = gbox(f"pap{k}", (cx - w / 2, cy - h / 2, Z0 + 0.018), (cx + w / 2, cy + h / 2, Z0 + 0.0205), "M_Paper", bevel=0.0)
        A.place(pa, Matrix.Translation(GV((cx, cy, Z0))) @ Matrix.Rotation(-rot, 4, "Y") @ Matrix.Translation(GV((-cx, -cy, -Z0))))
        o.append(pa)
        o.append(gcyl(f"pin{k}", 0.006, 0.006, (cx, cy + h / 2 - 0.02, Z0 + 0.0205), axis="z", verts=6, mat="M_Enamel_Crimson", bevel=0.0))
    add("furniture", *o)


def desk_dressing():
    o = []
    top = 0.76
    # papers, a pencil jar, an inkwell, a small brass bell, the diary mount spot is kept clear
    o.append(gbox("pp1", (0.62, top, -1.72), (0.82, top + 0.004, -1.46), "M_Paper", bevel=0.0))
    o.append(gbox("pp2", (0.60, top + 0.004, -1.70), (0.80, top + 0.008, -1.44), "M_Paper", bevel=0.0))
    o += Q.jar("pj", 1.82, top, -1.86, 0.036, 0.10, "M_Glass", lid="M_Brass_Aged")
    for k in range(5):
        a = k * 1.26
        o.append(gcyl(f"pc{k}", 0.0035, 0.15, (1.82 + math.cos(a) * 0.012, top + 0.02, -1.86 + math.sin(a) * 0.012), axis=(math.cos(a) * 0.12, 1.0, math.sin(a) * 0.12),
                      verts=5, mat="M_Enamel_Amber" if k % 2 else "M_Enamel_Crimson", bevel=0.0))
    o += Q.mug("dmg", 0.70, top, -1.37, handle_dir=-1.0)
    add("dressing", *o)
    # the desk lamp: low table lamp with a cream cloth shade and a bulb glow
    lx, lz = 2.0, -1.72
    lamp = [glathe("tl_base", [(0.0, 0.0), (0.07, 0.0), (0.075, 0.012), (0.045, 0.05), (0.06, 0.12), (0.035, 0.20), (0.012, 0.24), (0.0, 0.24)], (lx, top, lz), axis="y",
                   segments=18, mat="M_Porcelain"),
            glathe("tl_band", [(0.0455, 0.050), (0.0475, 0.054), (0.0475, 0.066), (0.0455, 0.07)], (lx, top, lz), axis="y", segments=18, mat=BRASS),
            glathe("tl_shade", [(0.060, 0.0), (0.150, 0.0), (0.162, -0.012), (0.082, -0.20), (0.074, -0.205), (0.070, -0.195), (0.145, -0.012), (0.060, -0.003)],
                   (lx, top + 0.46, lz), axis="y", segments=24, mat="M_Linen"),
            glathe("tl_cap", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.016), (0.0, 0.02)], (lx, top + 0.255, lz), axis="y", segments=12, mat=BRASS)]
    part("lamp_desk", lamp, (lx, top, lz))
    bulb = [Q.gsphere("tl_bulb", 0.030, (lx, top + 0.34, lz), (1.0, 1.2, 1.0), mat="M_Emissive_Warm", segs=10, rings=6)]
    part("lamp_desk_glow", bulb, (lx, top + 0.34, lz), presmooth=False)


# ---------------------------------------------------------------- radiator, window, rug, lamp, dressing
def radiator():
    o = []
    cz = 0.90
    n = 9
    for i in range(n):
        z = cz - (n - 1) * 0.036 + i * 0.072
        o.append(gbox(f"rd_s{i}", (-2.17, 0.14, z - 0.028), (-2.04, 0.66, z + 0.028), "M_Steel_Cream", bevel=0.012, seg=2))
        o.append(gbox(f"rd_g{i}", (-2.165, 0.10, z - 0.014), (-2.09, 0.14, z + 0.014), "M_Steel_Cream", bevel=0.003))
    zc0, zc1 = cz - (n - 1) * 0.036 - 0.04, cz + (n - 1) * 0.036 + 0.04
    o.append(gbox("rd_top", (-2.18, 0.64, zc0), (-2.03, 0.69, zc1), "M_Steel_Cream", bevel=0.01, seg=2))
    o.append(gbox("rd_bot", (-2.18, 0.12, zc0), (-2.03, 0.16, zc1), "M_Steel_Cream", bevel=0.01, seg=2))
    o.append(X.pipe("rd_feed", [(-2.12, 0.14, zc1 - 0.02), (-2.12, 0.0, zc1 - 0.02)], 0.020, mat="M_Iron_Rust", sides=10, flange_ends=False))
    o.append(gcyl("rd_valve", 0.022, 0.07, (-2.12, 0.30, zc1 + 0.04), axis="y", verts=10, mat=BRASS, bevel=0.003))
    o.append(X.wheel("rd_wheel", 0.034, 0.005, 4, (-2.12, 0.40, zc1 + 0.075), axis="z", hub_r=0.01, boss_h=0.008, mat="M_Enamel_Crimson", hub_mat=BRASS))
    for z in (zc0 + 0.03, zc1 - 0.03):
        o.append(gbox(f"rd_br{z}", (-2.20, 0.40, z - 0.012), (-2.14, 0.55, z + 0.012), "M_Steel_Dark", bevel=0.002))
    add("radiator", *o)


def curtain(name, z_a, z_b, y0, y1, n_cols, amp):
    """Vertical wool curtain panel hung on the west wall (folds along z): swept along local X, then yawed -90 so local X runs along +Z and
    local -Z points into the room."""
    w = z_b - z_a
    xs = [w * i / n_cols for i in range(n_cols + 1)]

    def sec(u):
        d = amp * (0.5 + 0.5 * math.sin(u / w * n_cols * math.pi * 1.0))
        return [(-(0.050 + d), y1 - (y1 - y0) * k / 5.0) for k in range(6)]
    c = Q.drape(name, xs, sec, thick=0.012, mat=WOOL)
    at([c], (X0, 0.0, z_a), -90.0)
    return c


def window():
    o = []
    # a window onto a light well: dark glass, brass-grey frame, crossbars, sill with a plant
    zc, y0, y1, z0, z1 = 0.90, 1.18, 2.12, 0.30, 1.50
    o.append(gbox("wi_glass", (X0, y0, z0), (X0 + 0.004, y1, z1), "M_Glass_Dark", bevel=0.0))
    for nm, mn, mx in (("wi_t", (X0, y1 - 0.045, z0 - 0.04), (X0 + 0.04, y1 + 0.03, z1 + 0.04)), ("wi_b", (X0, y0 - 0.03, z0 - 0.04), (X0 + 0.04, y0 + 0.045, z1 + 0.04)),
                       ("wi_l", (X0, y0, z0 - 0.04), (X0 + 0.04, y1, z0 + 0.03)), ("wi_r", (X0, y0, z1 - 0.03), (X0 + 0.04, y1, z1 + 0.04)),
                       ("wi_mv", (X0, y0, zc - 0.015), (X0 + 0.03, y1, zc + 0.015)), ("wi_mh", (X0, 1.62, z0), (X0 + 0.03, 1.66, z1))):
        o.append(gbox(nm, mn, mx, WOOD, bevel=0.003))
    o.append(gbox("wi_sill", (X0, y0 - 0.06, z0 - 0.08), (X0 + 0.14, y0 - 0.03, z1 + 0.08), WOOD, bevel=0.005, seg=2))
    # plant on the sill
    o.append(glathe("pot", [(0.0, 0.0), (0.050, 0.0), (0.066, 0.10), (0.070, 0.12), (0.0, 0.12)], (X0 + 0.08, y0 - 0.03, 1.15), axis="y", segments=14, mat="M_Porcelain"))
    for k in range(9):
        a = k * 2.4
        o.append(Q.gsphere(f"leaf{k}", 0.07, (X0 + 0.08 + math.cos(a) * 0.05, y0 - 0.03 + 0.20 + 0.03 * (k % 3), 1.15 + math.sin(a) * 0.05), (0.35, 1.0, 0.55), mat="M_Enamel_Green", segs=7, rings=4))
    # curtain rod and two wool curtains with a tie-back
    o.append(gcyl("rod", 0.011, z1 - z0 + 0.50, (X0 + 0.07, 2.27, z0 - 0.25), axis="z", verts=8, mat=BRASS, bevel=0.0))
    for z in (z0 - 0.25, z1 + 0.25):
        o.append(Q.gsphere(f"fin{z}", 0.022, (X0 + 0.07, 2.27, z), mat=BRASS, segs=8, rings=5))
    for z in (z0 - 0.06, z1 + 0.06):
        o.append(gbox(f"rodb{z}", (X0, 2.255, z - 0.01), (X0 + 0.07, 2.285, z + 0.01), BRASS, bevel=0.002))
    cl = curtain("curt_a", z0 - 0.22, z0 + 0.14, 0.55, 2.25, 10, 0.045)
    cr = curtain("curt_b", z1 - 0.14, z1 + 0.22, 0.55, 2.25, 10, 0.045)
    add("window", *o, cl, cr)


def rug():
    r = glathe("rug_base", [(0.0, 0.0), (0.98, 0.0), (1.0, 0.004), (1.0, 0.011), (0.96, 0.014), (0.0, 0.014)], (0.0, 0.0, 0.0), axis="y", segments=40, mat=WOOL)
    r.data.transform(Matrix.Scale(1.22, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.80, 4, Vector((0, 1, 0))))   # oval: x 1.22, z 0.80 (Blender y = -z)
    r.data.transform(Matrix.Translation(GV((0.10, 0.0, 0.40))))
    bands = []
    for i, (r0, r1, mt) in enumerate(((0.80, 0.86, "M_Enamel_Cobalt"), (0.70, 0.74, "M_Enamel_Cream"))):
        b = X.glathe_loop(f"rug_band{i}", [(r0, 0.0145), (r1, 0.0145), (r1, 0.0150), (r0, 0.0150)], (0.0, 0.0, 0.0), axis="y", segments=40, mat=mt)
        b.data.transform(Matrix.Scale(1.22, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.80, 4, Vector((0, 1, 0))))
        b.data.transform(Matrix.Translation(GV((0.10, 0.0, 0.40))))
        bands.append(b)
    add("rug", r, *bands)


def pendant():
    px, pz = 0.0, 0.20
    L = [glathe("pd_rose", [(0.0, 0.0), (0.075, 0.0), (0.08, -0.012), (0.04, -0.03), (0.0, -0.034)], (px, H, pz), axis="y", segments=16, mat=BRASS),
         gcyl("pd_cord", 0.006, 0.46, (px, H - 0.50, pz), axis="y", verts=6, mat="M_Fabric", bevel=0.0),
         glathe("pd_sock", [(0.0, 0.0), (0.022, 0.0), (0.024, 0.02), (0.020, 0.06), (0.0, 0.06)], (px, H - 0.55, pz), axis="y", segments=12, mat="M_Bakelite"),
         glathe("pd_shade", [(0.045, 0.0), (0.075, 0.0), (0.215, -0.22), (0.222, -0.235), (0.210, -0.235), (0.07, -0.01), (0.05, -0.01)], (px, H - 0.46, pz), axis="y",
                segments=22, mat="M_Linen")]
    for k in range(10):                                                 # a fringe of little wool balls round the shade rim
        a = 2 * math.pi * k / 10
        L.append(Q.gsphere(f"pd_fr{k}", 0.012, (px + math.cos(a) * 0.218, H - 0.46 - 0.245, pz + math.sin(a) * 0.218), mat="M_Dress_Wool", segs=5, rings=3))
    part("lamp_ceiling", L, (px, H, pz))
    bulb = Q.gsphere("pd_bulb", 0.040, (px, H - 0.60, pz), mat="M_Emissive_Warm", segs=10, rings=6)
    part("lamp_ceiling_glow", [bulb], (px, H - 0.60, pz), presmooth=False)
    mount("light_lamp_ceiling", (px, H - 0.68, pz))


def dressing():
    o = []
    # coat on three brass hooks (west wall, south of the doorway), hat, scarf
    for z in (-0.42, -0.14, 0.14):
        o.append(gbox(f"hk{z}", (X0, 1.78, z - 0.012), (X0 + 0.06, 1.795, z + 0.012), BRASS, bevel=0.002))
        o.append(gcyl(f"hkb{z}", 0.010, 0.02, (X0 + 0.06, 1.77, z), axis="x", verts=8, mat=BRASS, bevel=0.002))
    o.append(gbox("hkboard", (X0, 1.74, -0.52), (X0 + 0.016, 1.84, 0.24), WOOD, bevel=0.003))
    o.append(gbox("coat_up", (X0 + 0.03, 1.16, -0.29), (X0 + 0.17, 1.70, 0.01), "M_Leather", bevel=0.05, seg=2))
    o.append(gbox("coat_lo", (X0 + 0.03, 0.66, -0.34), (X0 + 0.19, 1.22, 0.06), "M_Leather", bevel=0.05, seg=2))
    o.append(gbox("coat_sl", (X0 + 0.04, 0.90, -0.40), (X0 + 0.13, 1.62, -0.32), "M_Leather", bevel=0.03, seg=2))
    o.append(gbox("coat_sr", (X0 + 0.04, 0.90, 0.04), (X0 + 0.13, 1.62, 0.12), "M_Leather", bevel=0.03, seg=2))
    o.append(gbox("coat_c", (X0 + 0.03, 1.60, -0.31), (X0 + 0.20, 1.74, 0.03), "M_Fabric", bevel=0.03, seg=2))
    for y in (1.40, 1.24, 1.08):
        o.append(gcyl(f"coat_bt{y}", 0.012, 0.008, (X0 + 0.17, y, -0.14), axis="x", verts=8, mat="M_Brass_Aged", bevel=0.0))
    o.append(Q.gsphere("scarf", 0.14, (X0 + 0.07, 1.50, 0.17), (0.35, 1.0, 0.38), mat=WOOL, segs=9, rings=6))
    # boots + slippers on the rug by the cot
    for z, nm in ((-0.28, "bt_l"), (-0.50, "bt_r")):
        o.append(gbox(nm + "_s", (-1.95, 0.0, z - 0.06), (-1.72, 0.07, z + 0.06), "M_Rubber", bevel=0.012, seg=2))
        o.append(gbox(nm + "_u", (-1.88, 0.07, z - 0.05), (-1.72, 0.30, z + 0.05), "M_Leather", bevel=0.015, seg=2))
    for x, z, yw in ((-0.20, -0.92, 20), (0.06, -0.80, -30)):
        s = [Q.gsphere("sl", 0.10, (0, 0.04, 0), (1.1, 0.40, 0.58), mat=WOOL, segs=10, rings=6), Q.gsphere("slh", 0.06, (-0.07, 0.07, 0), (0.9, 0.7, 0.9), mat=WOOL, segs=8, rings=5)]
        at(s, (x, 0.012, z), yw)
        o += s
    # tea things on the sideboard: tray, two mugs, the sugar jar
    o.append(gbox("tray", (-1.48, 0.86, 1.62), (-1.14, 0.872, 1.88), "M_Wood_Panel", bevel=0.004))
    o += Q.mug("sg1", -1.38, 0.872, 1.74)
    o += Q.mug("sg2", -1.27, 0.872, 1.78, mat="M_Enamel_Cobalt", rim="M_Enamel_Cream", handle_dir=-1.0)
    o += Q.jar("sj", -0.30, 0.86, 1.80, 0.040, 0.13, "M_Porcelain", lid="M_Wood_Panel")
    # sideboard wall shelf with cups and a framed picture above it
    o.append(gbox("ssh", (-1.50, 1.32, 1.80), (-0.10, 1.345, Z1), WOOD, bevel=0.003))
    for x in (-1.45, -0.15):
        o.append(gbox(f"sbr{x}", (x - 0.012, 1.22, 1.88), (x + 0.012, 1.32, Z1), WOOD, bevel=0.002))
    for i in range(5):
        o += Q.mug(f"cu{i}", -1.36 + 0.26 * i, 1.345, 1.90, r=0.036, h=0.075, mat="M_Enamel_Cream" if i % 2 == 0 else "M_Porcelain", rim="M_Enamel_Cobalt")
    o.append(gbox("fr_o", (-1.10, 1.52, Z1 - 0.026), (-0.60, 1.92, Z1 - 0.004), WOOD, bevel=0.004))
    o.append(gbox("fr_i", (-1.065, 1.555, Z1 - 0.0272), (-0.635, 1.885, Z1 - 0.0262), "M_Paper", bevel=0.0))
    o.append(gbox("fr_p", (-0.99, 1.62, Z1 - 0.0282), (-0.71, 1.82, Z1 - 0.0272), "M_Enamel_Green", bevel=0.0))
    add("dressing", *o)


def mounts():
    mount("cot_mount", (-0.75, 0.0, -1.58))
    mount("light_table_mount", (1.30, 0.76, -1.62))
    mount("kettle_mount", (-0.70, 0.86, 1.76))
    mount("diary_mount", (0.82, 0.76, -1.62))
    mount("cold_door_mount", (2.20, 0.0, 0.0))
    mount("acetate_mount_a", (1.70, 0.76, -1.52))
    mount("acetate_mount_b", (-0.30, 0.872, 1.66))
    mount("acetate_mount_c", (1.20, 1.652, -1.82))
    mount("light_lamp_desk", (2.0, 1.10, -1.72))
    mount("light_fill", (-1.2, 1.9, 1.2))
    mount("light_cot_fill", (-0.8, 1.2, -1.2))


def main():
    X.begin()
    shell()
    beams_ceiling()
    desk()
    add("furniture", *chair("dchair", (1.38, 0.0, -0.98), 180.0, wool=True))
    add("furniture", *armchair())
    sideboard()
    bookcase()
    shelves_north()
    desk_dressing()
    radiator()
    window()
    rug()
    pendant()
    dressing()
    mounts()
    for k, v in grp.items():
        X.top(v, 4)
    for g, lst in grp.items():
        ob = X.join_all(g, lst)
        ob.name = g
        ob.data.name = g
        M.set_origin(ob, G(0, 0, 0))
    req = list(grp.keys()) + ["lamp_desk", "lamp_desk_glow", "lamp_ceiling", "lamp_ceiling_glow", "cot_mount", "light_table_mount", "kettle_mount", "diary_mount",
                              "cold_door_mount", "acetate_mount_a", "acetate_mount_b", "acetate_mount_c", "light_lamp_ceiling", "light_lamp_desk", "light_fill",
                              "light_cot_fill"]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["lamp_desk", "lamp_ceiling", "lamp_ceiling_glow", "lamp_desk_glow"], budget=BUDGET,
                          expect={"lamp_ceiling": (0.0, H, 0.20), "lamp_desk": (2.0, 0.76, -1.72)}, show=["lamp_ceiling", "lamp_desk"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")


main()
