"""room_gallery.glb — R5 the Reading Gallery (Level +1), built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 3b/7. "A closed library on a Sunday": sepia daylight through tall arched windows,
wood and dust, long reading tables with green-shaded lamps, a records counter, and one long side open to a double-height void: the
balcony over the Archive Hall (the hall floor, its far wall and two enamel pendants are baked into the shell as `hall_below`).
Interior x [-4.5, 4.5], z [-3.0, 3.0], ceiling y 4.2, wall thickness 0.30. The gallery floor (y 0) ends at z = 1.6 (the balcony
edge, the `balcony_rail` model stands there); beyond it the void drops to the hall floor at y = -4.2 and rises to the far wall z = 3.0.
Openings and parts (all coordinates in room space):
  north wall z = -3.0   door to the Plate Room x [-4.1, -3.2] y [0, 2.3] (leaf `IA_door_plate`, hinge at x = -4.1, opens with +95 deg about +Y, into the
                        Plate Room); two arched windows at x = 1.5 and 3.1 (w 1.0, sill 0.8, spring 3.1); the roll-call board hangs at x = -1.0
  east wall x = 4.5     door to the Director's Office z [-2.4, -1.5] y [0, 2.3] (leaf `IA_door_office`, hinge z = -2.4, opens +95 deg, into the
                        office), a tag-shaped keyhole plate on it (`pass_lock`); the spiral stair hole at (3.15, 0.45) r 0.95
  west wall x = -4.5    records counter (z -1.4 .. 1.0) with three drawers `IA_counter_drawer_0..2`, pigeonholes, an arched window at z = -2.1
  south: the void and the far wall of the hall with three tall arched windows
Suggested placements of separate models (Godot position, yaw):
  balcony_rail (0, 0, 1.60) 0      roll_call_board (-1.0, 0, -3.0) 0 (the board's back sits on the wall; mount empty `board_mount`)
  pa_horn (-4.5, 3.35, 0.15) +90 (mount `horn_mount`)      stair_wedge (3.15, 0, 1.00) 0 (mount `wedge_mount`; the ladder leans over the stairwell)
Own objects: floor, wall_n/_e/_s/_w, ceiling, beams, windows, sky_cards, bookcases, tables, chairs, lamps, counter, stair_in, hall_below,
  dressing, IA_door_plate, IA_door_office, IA_counter_drawer_0..2, IA_tube_hatch, empties board_mount, horn_mount, wedge_mount, rail_mount,
  tube_mount, light_window_n (3.1, 3.6, -2.2), light_window_s (0, 3.4, 2.9), light_table_a (-1.3, 1.05, -1.0), light_table_b (-1.3, 1.05, 0.6).
    blender -b --factory-startup -P tools/blender/models/room_gallery.py [-- --no-render] [--shots=a,b]
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
from mathutils import Matrix  # noqa: E402

NAME = "room_gallery"
BUDGET = 60000
ARGS = M.main_guard()
X0, X1, Z0, Z1, H, T = -4.5, 4.5, -3.0, 3.0, 4.2, 0.30
ZB = 1.6                                  # balcony edge
HALL = -4.2
WOOD, PANEL, PLAS, FLOOR = "M_Wood_Walnut", "M_Wood_Panel", "M_Plaster_Wall", "M_Wood_Floor"
BRASS = "M_Brass_Aged"
SX, SZ, SR = 3.15, 0.45, 0.95             # spiral stair hole
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def shell():
    ops = {"n": [(-4.1, -3.2, 0.0, 2.3)], "e": [(-2.4, -1.5, 0.0, 2.3)]}
    mats = {"n": (PANEL, 1.30, PLAS), "s": PLAS, "e": (PANEL, 1.30, PLAS), "w": (PANEL, 1.30, PLAS)}
    w = X.wallset("gal", X0, X1, Z0, Z1, H, T, mats, ops, floor_mat=FLOOR, ceil_mat="M_Ceiling")
    # arched windows: north x 1.5 and 3.1, west z -2.1, south three (far wall of the hall, large)
    U.arch_cut(w["n"], "z", 1.5, 1.0, 0.8, 3.1, Z0 - T - 0.1, Z0 + 0.1)
    U.arch_cut(w["n"], "z", 3.1, 1.0, 0.8, 3.1, Z0 - T - 0.1, Z0 + 0.1)
    U.arch_cut(w["w"], "x", -2.1, 1.0, 0.8, 3.1, X0 - T - 0.1, X0 + 0.1)
    for cx in (-2.9, 0.0, 2.9):
        U.arch_cut(w["s"], "z", cx, 1.5, 0.6, 3.0, Z1 - 0.1, Z1 + T + 0.1)
    for k in ("n", "s", "e", "w"):
        add("wall_" + k, *w[k])
    add("ceiling", *w["ceiling"])
    # floor: from the north wall to the balcony edge, with the stair hole and a nosing at the edge
    for o in w["floor"]:
        bpy.data.objects.remove(o, do_unlink=True)
    fl = gbox("gal_floor", (X0 - T, -0.30, Z0 - T), (X1 + T, 0.0, ZB), FLOOR, bevel=0.0)
    hole = gcyl("hole", SR, 0.6, (SX, -0.4, SZ), axis="y", verts=28, mat="M_Concrete", bevel=0.0)
    M.boolean(fl, hole)
    add("floor", fl)
    add("floor", gbox("nosing", (X0, -0.6, ZB), (X1, 0.0, ZB + 0.16), WOOD, bevel=0.01, seg=2),
        gbox("nosing_fascia", (X0, -1.10, ZB + 0.10), (X1, -0.6, ZB + 0.16), WOOD, bevel=0.01),
        gbox("nosing_cove", (X0, -1.30, ZB + 0.06), (X1, -1.10, ZB + 0.16), PLAS, bevel=0.0))
    # floor boards: seams as thin dark strips across z every 0.9 (reads as long planks), split around the stair hole
    for i in range(1, 10):
        x = X0 + i * 0.9
        dx = abs(x - SX)
        if dx < SR + 0.02:
            hw = math.sqrt(max(SR * SR - dx * dx, 0.0)) + 0.02
            spans = [(Z0, SZ - hw), (SZ + hw, ZB)]
        else:
            spans = [(Z0, ZB)]
        for k, (za, zb) in enumerate(spans):
            add("dressing", gbox(f"seam{i}_{k}", (x - 0.004, 0.0, za), (x + 0.004, 0.004, zb), "M_Lacquer_Black", bevel=0.0))
    # extend the walls below the floor for the void: tile lower hall walls (west/east of the void, south wall)
    add("hall_below",
        gbox("hall_floor", (X0, HALL - 0.2, ZB), (X1, HALL, Z1), "M_Linoleum", bevel=0.0),
        gbox("hall_w", (X0 - T, HALL, ZB), (X0, 0.0, Z1 + T), "M_Tile_Glazed", bevel=0.0),
        gbox("hall_e", (X1, HALL, ZB), (X1 + T, 0.0, Z1 + T), "M_Tile_Glazed", bevel=0.0),
        gbox("hall_s", (X0 - T, HALL, Z1), (X1 + T, 0.0, Z1 + T), "M_Tile_Glazed", bevel=0.0),
        gbox("hall_dado", (X0, HALL, Z1 - 0.04), (X1, HALL + 0.14, Z1), "M_Steel_Dark", bevel=0.0),
        gbox("hall_rule", (X0, HALL + 1.55, Z1 - 0.03), (X1, HALL + 1.60, Z1), "M_Brass_Aged", bevel=0.0))
    # hall far wall: three dark arched doors / bays (recessed panels) and a brass cornice at gallery floor level
    for cx in (-2.9, 0.0, 2.9):
        add("hall_below", gbox(f"bay{cx}", (cx - 0.7, HALL, Z1 - 0.06), (cx + 0.7, HALL + 2.6, Z1 - 0.02), "M_Wood_Mahogany", bevel=0.0),
            gbox(f"bay_t{cx}", (cx - 0.78, HALL + 2.6, Z1 - 0.08), (cx + 0.78, HALL + 2.68, Z1 - 0.02), "M_Brass_Aged", bevel=0.0))
        add("hall_below", gbox(f"bay_p{cx}", (cx - 0.55, HALL + 0.3, Z1 - 0.075), (cx + 0.55, HALL + 2.3, Z1 - 0.06), "M_Wood_Panel", bevel=0.0))
    add("hall_below", gbox("hall_bench0", (-2.4, HALL, 2.2), (-0.9, HALL + 0.45, 2.55), WOOD, bevel=0.01),
        gbox("hall_bench1", (0.9, HALL, 2.2), (2.4, HALL + 0.45, 2.55), WOOD, bevel=0.01))
    # two hall pendants hanging in the void from the gallery ceiling (green enamel shade, brass cap, glowing bulb)
    for px in (-1.6, 1.6):
        add("hall_below", gcyl(f"pend_rod{px}", 0.008, 1.3, (px, H - 1.3, 2.3), axis="y", verts=6, mat=BRASS, bevel=0.0),
            glathe(f"pend_shade{px}", [(0.0, 0.0), (0.06, 0.0), (0.22, -0.18), (0.24, -0.22), (0.0, -0.22)], (px, H - 1.3, 2.3), axis="y", segments=18, mat="M_Enamel_Green"))
        add("hall_below", M.sphere(f"pend_bulb{px}", 0.06, loc=G(px, H - 1.55, 2.3), segments=10, rings=6, mat="M_Emissive_Warm"))
    # wainscot rail + skirting on the three gallery walls
    for side, mn, mx in (("n", (X0, 1.30, Z0), (X1, 1.37, Z0 + 0.03)), ("e", (X1 - 0.03, 1.30, Z0), (X1, 1.37, ZB)), ("w", (X0, 1.30, Z0), (X0 + 0.03, 1.37, ZB))):
        add("dressing", gbox("rail" + side, mn, mx, WOOD, bevel=0.004))
    add("dressing", gbox("skirt_n", (X0, 0.0, Z0), (X1, 0.14, Z0 + 0.03), WOOD, bevel=0.004), gbox("skirt_e", (X1 - 0.03, 0.0, Z0), (X1, 0.14, ZB), WOOD, bevel=0.004),
        gbox("skirt_w", (X0, 0.0, Z0), (X0 + 0.03, 0.14, ZB), WOOD, bevel=0.004))


def windows():
    wins = [("wn1", "z", Z0, +1, 1.5), ("wn2", "z", Z0, +1, 3.1), ("ww1", "x", X0, +1, -2.1)]
    for nm, ax, face, sgn, cu in wins:
        add("windows", *U.arch_frame(nm, ax, face, sgn, cu, 1.0, 0.8, 3.1, mat=WOOD))
        add("sky_cards", U.sky_card(nm, ax, face, sgn, cu, 1.0, 0.8, 3.1))
    for i, cx in enumerate((-2.9, 0.0, 2.9)):
        add("windows", *U.arch_frame(f"ws{i}", "z", Z1, -1, cx, 1.5, 0.6, 3.0, mat=WOOD, bar=0.09, depth=0.08))
        add("sky_cards", U.sky_card(f"ws{i}", "z", Z1, -1, cx, 1.5, 0.6, 3.0, dist=0.3))


def beams():
    for i, x in enumerate((-3.6, -1.8, 0.0, 1.8, 3.6)):
        add("beams", gbox(f"beam{i}", (x - 0.11, H - 0.30, Z0), (x + 0.11, H, Z1), WOOD, bevel=0.012, seg=2),
            gbox(f"beam_c{i}", (x - 0.15, H - 0.34, Z0), (x + 0.15, H - 0.30, Z1), WOOD, bevel=0.006))
    for z in (Z0, Z1):
        add("beams", gbox(f"cornice{z}", (X0, H - 0.22, z - (0.0 if z < 0 else 0.20)), (X1, H, z + (0.20 if z < 0 else 0.0)), WOOD, bevel=0.01))
    add("beams", gbox("cornice_e", (X1 - 0.20, H - 0.22, Z0), (X1, H, Z1), WOOD, bevel=0.01), gbox("cornice_w", (X0, H - 0.22, Z0), (X0 + 0.20, H, Z1), WOOD, bevel=0.01))


def stair():
    """Spiral stair hole: round shaft wall, newel, 9 wedge steps going down, a partial iron rail round the hole."""
    s = []
    # shaft wall: a ring from y = -0.0 down to the hall floor
    ring = [(SR, 0.0), (SR + 0.06, 0.0), (SR + 0.06, HALL), (SR, HALL)]
    s.append(glathe("shaft", ring, (SX, 0.0, SZ), axis="y", segments=28, mat=PLAS))
    s.append(glathe("shaft_lip", [(SR - 0.02, -0.0), (SR + 0.10, 0.0), (SR + 0.10, -0.05), (SR - 0.02, -0.05)], (SX, 0.0, SZ), axis="y", segments=28, mat=WOOD))
    s.append(gcyl("newel", 0.09, 4.4, (SX, HALL, SZ), axis="y", verts=12, mat="M_Steel_Painted", bevel=0.0))
    n = 9
    for i in range(n):
        y = -0.30 * (i + 1)
        a0 = math.radians(-100 + 35 * i)
        # step: wedge polygon in the XZ plane at height y (extruded 0.05 along +Y)
        poly = [(0.1 * math.cos(a0), 0.1 * math.sin(a0))] + [((SR - 0.08) * math.cos(a0 + math.radians(38) * k / 5), (SR - 0.08) * math.sin(a0 + math.radians(38) * k / 5)) for k in range(6)] + \
               [(0.1 * math.cos(a0 + math.radians(38)), 0.1 * math.sin(a0 + math.radians(38)))]
        mtx = X.C.gframe((SX, y - 0.05, SZ), (1, 0, 0), (0, 0, -1))
        s.append(X.gpoly(f"step{i}", [(px, py) for px, py in poly], 0.05, mtx, mat=WOOD, bevel=0.0))
    # iron rail around the hole (open on the side facing the room corner at +x/-z so the stair mouth stays free)
    for k in range(14):
        a = math.radians(135 + k * 14.0 * 1.0)
        if 20 < (math.degrees(a) % 360) < 110:
            continue
        s.append(gcyl(f"post{k}", 0.012, 0.95, (SX + math.cos(a) * (SR + 0.14), 0.0, SZ + math.sin(a) * (SR + 0.14)), axis="y", verts=6, mat="M_Steel_Dark", bevel=0.0))
    add("stair_in", *s)


def counter():
    """Records counter on the west wall: x [-4.5, -3.75], z [-1.4, 1.0], top at 1.06; pigeonholes above; three drawers on the room side."""
    cx0, cx1, cz0, cz1, top = -4.5, -3.78, -1.4, 1.0, 1.06
    c = [gbox("c_body", (cx0 + 0.02, 0.10, cz0), (cx1 - 0.02, top - 0.05, cz1), WOOD, bevel=0.004),
         gbox("c_plinth", (cx0 + 0.02, 0.0, cz0 + 0.02), (cx1 - 0.01, 0.10, cz1 - 0.02), "M_Wood_Mahogany", bevel=0.004),
         gbox("c_top", (cx0, top - 0.05, cz0 - 0.05), (cx1 + 0.06, top, cz1 + 0.05), "M_Wood_Mahogany", bevel=0.008, seg=2),
         gbox("c_leather", (cx0 + 0.05, top, cz0 + 0.05), (cx1 + 0.0, top + 0.004, cz1 - 0.05), "M_Leather", bevel=0.0)]
    for z in (cz0 + 0.04, cz1 - 0.04):
        c.append(gbox(f"c_post{z}", (cx0 + 0.02, top, z - 0.04), (cx0 + 0.20, 2.35, z + 0.04), "M_Wood_Mahogany", bevel=0.006))
    c.append(gbox("c_lintel", (cx0 + 0.02, 2.25, cz0 + 0.0), (cx0 + 0.20, 2.45, cz1), "M_Wood_Mahogany", bevel=0.006))
    # brass grille above the counter: vertical bars in the wicket opening
    for i in range(18):
        z = cz0 + 0.20 + i * 0.116
        c.append(gcyl(f"bar{i}", 0.007, 1.10, (cx0 + 0.10, top + 0.15, z), axis="y", verts=6, mat=BRASS, bevel=0.0))
    c.append(gbox("g_rail_b", (cx0 + 0.08, top + 0.12, cz0 + 0.06), (cx0 + 0.13, top + 0.17, cz1 - 0.06), BRASS, bevel=0.003))
    c.append(gbox("g_rail_t", (cx0 + 0.08, top + 1.22, cz0 + 0.06), (cx0 + 0.13, top + 1.27, cz1 - 0.06), BRASS, bevel=0.003))
    # pigeonholes (small dark boxes in a grid on the wall above the lintel)
    for r in range(3):
        for k in range(10):
            z = cz0 + 0.08 + k * 0.232
            c.append(gbox(f"ph{r}_{k}", (cx0 + 0.02, 2.55 + r * 0.38, z), (cx0 + 0.36, 2.55 + r * 0.38 + 0.34, z + 0.21), WOOD, bevel=0.003))
            c.append(gbox(f"ph_in{r}_{k}", (cx0 + 0.20, 2.58 + r * 0.38, z + 0.02), (cx0 + 0.36, 2.58 + r * 0.38 + 0.28, z + 0.19), "M_Lacquer_Black", bevel=0.0))
    add("counter", *c)
    dr = []
    for i in range(3):
        zc = cz0 + 0.4 + i * 0.8
        d = [gbox(f"df{i}", (cx1 - 0.02, 0.2, zc - 0.36), (cx1 + 0.012, 0.88, zc + 0.36), "M_Wood_Mahogany", bevel=0.006, seg=2),
             gbox(f"dp{i}", (cx1 + 0.012, 0.28, zc - 0.28), (cx1 + 0.022, 0.80, zc + 0.28), "M_Wood_Mahogany", bevel=0.004),
             gbox(f"dpull{i}", (cx1 + 0.022, 0.52, zc - 0.10), (cx1 + 0.05, 0.57, zc + 0.10), BRASS, bevel=0.004),
             gbox(f"dcard{i}", (cx1 + 0.022, 0.67, zc - 0.07), (cx1 + 0.028, 0.74, zc + 0.07), "M_Paper", bevel=0.0),
             gbox(f"dcard_f{i}", (cx1 + 0.020, 0.66, zc - 0.08), (cx1 + 0.024, 0.75, zc + 0.08), BRASS, bevel=0.0)]
        dr.append(part(f"IA_counter_drawer_{i}", d, (cx1, 0.54, zc)))
    return dr


def furniture():
    # reading tables: two long tables along x, with a green leather inlay and a lower stretcher; chairs both sides; banker lamps
    for ti, (tx0, tx1, tz) in enumerate(((-3.0, -0.2, -1.0), (-3.0, -0.2, 0.6))):
        top = 0.78
        t = [gbox(f"tbl{ti}_top", (tx0, top - 0.05, tz - 0.42), (tx1, top, tz + 0.42), "M_Wood_Mahogany", bevel=0.01, seg=2),
             gbox(f"tbl{ti}_inlay", (tx0 + 0.07, top, tz - 0.34), (tx1 - 0.07, top + 0.004, tz + 0.34), "M_Paint_Green", bevel=0.0),
             gbox(f"tbl{ti}_apron_f", (tx0 + 0.12, top - 0.14, tz + 0.35), (tx1 - 0.12, top - 0.05, tz + 0.38), WOOD, bevel=0.004),
             gbox(f"tbl{ti}_apron_b", (tx0 + 0.12, top - 0.14, tz - 0.38), (tx1 - 0.12, top - 0.05, tz - 0.35), WOOD, bevel=0.004)]
        for x in (tx0 + 0.16, tx1 - 0.16):
            for z in (tz - 0.34, tz + 0.34):
                t.append(gbox(f"tbl{ti}_leg", (x - 0.05, 0.0, z - 0.05), (x + 0.05, top - 0.05, z + 0.05), "M_Wood_Mahogany", bevel=0.006))
            t.append(gbox(f"tbl{ti}_end", (x - 0.03, 0.15, tz - 0.34), (x + 0.03, 0.22, tz + 0.34), WOOD, bevel=0.004))
        t.append(gbox(f"tbl{ti}_stretch", (tx0 + 0.16, 0.16, tz - 0.02), (tx1 - 0.16, 0.20, tz + 0.02), WOOD, bevel=0.003))
        add("tables", *t)
        # shared reading-desk furniture: a book stand + open book + blotter between lamps
        add("dressing", gbox(f"stand{ti}", (-1.85, top + 0.0, tz - 0.12), (-1.45, top + 0.012, tz + 0.12), WOOD, bevel=0.002),
            gbox(f"book{ti}_a", (-1.83, top + 0.012, tz - 0.10), (-1.64, top + 0.030, tz + 0.10), "M_Paper", bevel=0.002),
            gbox(f"book{ti}_b", (-1.64, top + 0.012, tz - 0.10), (-1.47, top + 0.030, tz + 0.10), "M_Paper", bevel=0.002),
            gbox(f"book{ti}_cover", (-1.86, top + 0.004, tz - 0.115), (-1.44, top + 0.012, tz + 0.115), "M_Book_Brown", bevel=0.002))
        for lx in (-2.5, -0.85):
            add("lamps", *U.banker_lamp(f"bl{ti}_{lx}_", lx, top + 0.0, tz - 0.02, yaw=0.0))
        # chairs
        for k, cx in enumerate((-2.55, -1.4, -0.3)):
            if ti == 0:
                add("chairs", *U.chair_wood(f"ch{ti}a{k}", cx, tz - 0.62, yaw=0.0))
            else:
                add("chairs", *U.chair_wood(f"ch{ti}b{k}", cx, tz + 0.62, yaw=180.0))
    # bookcase wall (west, north end) with a rolling ladder rail, and a short case on the east wall
    for zc0, zc1, nm in ((-2.95, -1.55, "bcw"),):
        add("bookcases", *bookcase(nm, -4.5, zc0, zc1, 0.42, 3.3, axis="x", sgn=1, seed=11))
    add("bookcases", *bookcase("bce", 4.5, -1.35, -0.55, 0.40, 2.7, axis="x", sgn=-1, seed=7))
    # ladder rail along the west bookcase (brass rail on brackets) + a library ladder resting on it
    add("dressing", gbox("lad_rail", (-4.08, 2.45, -2.95), (-4.04, 2.50, -1.55), BRASS, bevel=0.002))
    # a rug runner between the tables and the stair, a stack of crates under the window, a coat of dust: two chairs against the east wall
    add("dressing", gbox("runner", (-3.3, 0.004, -0.50), (1.9, 0.012, 0.10), "M_Dress_Wool", bevel=0.0),
        gbox("runner_edge_a", (-3.3, 0.012, -0.50), (1.9, 0.016, -0.47), BRASS, bevel=0.0), gbox("runner_edge_b", (-3.3, 0.012, 0.07), (1.9, 0.016, 0.10), BRASS, bevel=0.0))
    # a globe on a stand by the window
    add("dressing", glathe("globe_stand", [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.03, 0.75), (0.0, 0.75)], (3.9, 0.0, -2.35), axis="y", segments=14, mat="M_Wood_Mahogany"),
        M.sphere("globe", 0.17, loc=G(3.9, 0.98, -2.35), segments=16, rings=10, mat="M_Dress_Stone_Dark"))
    add("dressing", glathe("globe_ring", [(0.175, -0.01), (0.19, -0.01), (0.19, 0.01), (0.175, 0.01)], (3.9, 0.98, -2.35), axis="y", segments=22, mat=BRASS))


def bookcase(prefix, face, a0, a1, depth, height, axis="x", sgn=1, seed=1):
    """Wall bookcase with shelves of books, against a wall at x = face (axis x), spanning z a0..a1; sgn = +1 faces +x (room side)."""
    o = []
    th = 0.03
    x0 = face if sgn > 0 else face - depth
    x1 = face + depth if sgn > 0 else face
    o.append(gbox(prefix + "back", (x0 if sgn > 0 else x1 - 0.02, 0.05, a0), (x0 + 0.02 if sgn > 0 else x1, height, a1), "M_Wood_Panel", bevel=0.0))
    for z in (a0, a1 - th):
        o.append(gbox(prefix + "side", (x0, 0.0, z), (x1, height, z + th), "M_Wood_Mahogany", bevel=0.004))
    o.append(gbox(prefix + "top", (min(x0, x1) - 0.02, height, a0 - 0.02), (max(x0, x1) + 0.02, height + 0.05, a1 + 0.02), "M_Wood_Mahogany", bevel=0.006))
    o.append(gbox(prefix + "base", (x0, 0.0, a0), (x1, 0.16, a1), "M_Wood_Mahogany", bevel=0.004))
    nshelf = int((height - 0.2) / 0.36)
    for i in range(nshelf):
        y = 0.16 + i * (height - 0.2) / nshelf
        o.append(gbox(prefix + f"shelf{i}", (x0, y, a0), (x1, y + 0.025, a1), "M_Wood_Mahogany", bevel=0.002))
        if i > 0 or True:
            row = book_row_z(prefix + f"b{i}", a0 + th, a1 - th, y + 0.025, (x0 + x1) / 2 + 0.02 * sgn, depth * 0.62, seed + i * 7)
            o.append(row)
    return o


def book_row_z(name, z0, z1, y, x, depth, seed):
    """Upright books along z (spines toward the room, +x or -x: boxes are symmetric, so only the depth matters)."""
    import random
    rnd = random.Random(seed)
    mats = ["M_Book_Brown", "M_Book_Green", "M_Book_Red", "M_Book_Black", "M_Book_Blue", "M_Book_Gold", "M_Leather"]
    objs = []
    z = z0 + 0.01
    k = 0
    while z < z1 - 0.04:
        w = rnd.uniform(0.025, 0.055)
        h = rnd.uniform(0.20, 0.31)
        w = min(w, z1 - z - 0.005)
        objs.append(gbox(f"{name}_{k}", (x - depth / 2, y, z), (x + depth / 2, y + h, z + w * 0.96), rnd.choice(mats), bevel=0.0015))
        z += w
        k += 1
        if rnd.random() < 0.05:
            z += rnd.uniform(0.04, 0.10)
    return M.join(objs, name)


def doors_and_misc():
    # leaf to the plate room (north wall, hinge x = -4.1; leaf slightly inside the wall slab)
    ia1 = []
    ia1.append(gbox("leaf", (-4.1, 0.03, Z0 + 0.02), (-3.2, 2.27, Z0 + 0.07), "M_Wood_Panel", bevel=0.004))
    for y in (0.5, 1.15, 1.8):
        ia1.append(gbox(f"rail{y}", (-4.1, y - 0.04, Z0 + 0.07), (-3.2, y + 0.04, Z0 + 0.082), WOOD, bevel=0.003))
    ia1.append(gbox("handle", (-3.32, 1.0, Z0 + 0.082), (-3.26, 1.14, Z0 + 0.11), BRASS, bevel=0.004))
    ia1.append(gbox("kick", (-4.1, 0.03, Z0 + 0.07), (-3.2, 0.22, Z0 + 0.078), BRASS, bevel=0.0))
    d1 = part("IA_door_plate", ia1, (-4.1, 0.0, Z0 + 0.045))
    # frame of both doors
    add("dressing", gbox("fr1_h", (-4.2, 2.30, Z0 - 0.0), (-3.1, 2.40, Z0 + 0.10), WOOD, bevel=0.005),
        gbox("fr1_a", (-4.2, 0.0, Z0), (-4.1, 2.30, Z0 + 0.10), WOOD, bevel=0.005), gbox("fr1_b", (-3.2, 0.0, Z0), (-3.1, 2.30, Z0 + 0.10), WOOD, bevel=0.005))
    add("dressing", gbox("fr2_h", (X1 - 0.10, 2.30, -2.5), (X1, 2.40, -1.4), WOOD, bevel=0.005),
        gbox("fr2_a", (X1 - 0.10, 0.0, -2.5), (X1, 2.30, -2.4), WOOD, bevel=0.005), gbox("fr2_b", (X1 - 0.10, 0.0, -1.5), (X1, 2.30, -1.4), WOOD, bevel=0.005))
    # leaf to the office, with the tag-shaped keyhole plate (the key's bow is the same shape)
    o2 = [gbox("leaf", (X1 - 0.07, 0.03, -2.4), (X1 - 0.02, 2.27, -1.5), "M_Wood_Mahogany", bevel=0.004)]
    for y in (0.5, 1.15, 1.8):
        o2.append(gbox(f"rail{y}", (X1 - 0.082, y - 0.05, -2.4), (X1 - 0.07, y + 0.05, -1.5), WOOD, bevel=0.003))
    o2.append(gbox("lock_plate", (X1 - 0.092, 1.0, -1.72), (X1 - 0.082, 1.24, -1.52), BRASS, bevel=0.004))
    o2.append(X.gpoly("keyhole", A.rounded_rect(0.075, 0.056, 0.012, 3), 0.004, X.C.gframe((X1 - 0.092, 1.12, -1.62), (0, 0, 1), (0, 1, 0)), mat="M_Lacquer_Black", bevel=0.0))
    o2.append(gbox("handle", (X1 - 0.098, 0.95, -1.64), (X1 - 0.082, 1.0, -1.52), "M_Brass_Polished", bevel=0.003))
    d2 = part("IA_door_office", o2, (X1 - 0.045, 0.0, -2.4))
    # tube terminal on the west wall (brass hatch box) with a pipe up to the ceiling
    tx, ty, tz = X0, 1.35, 1.30
    tb = [gbox("tube_box", (tx, ty - 0.14, tz - 0.12), (tx + 0.16, ty + 0.14, tz + 0.12), BRASS, bevel=0.01, seg=2),
          gcyl("tube_ring", 0.1, 0.008, (tx + 0.16, ty, tz), axis="x", verts=16, mat="M_Brass_Polished", bevel=0.0)]
    add("dressing", X.pipe("tube_pipe", [(tx + 0.06, ty + 0.14, tz), (tx + 0.06, H - 0.1, tz)], 0.035, mat=BRASS, flange_r=0.055, bolts=6, flange_mat="M_Brass_Polished"), tb[0], tb[1])
    hatch = [gcyl("hatch", 0.085, 0.012, (tx + 0.172, ty, tz), axis="x", verts=16, mat="M_Brass_Polished", bevel=0.002),
             gcyl("hatch_knob", 0.018, 0.02, (tx + 0.184, ty, tz), axis="x", verts=10, mat="M_Lacquer_Black", bevel=0.002)]
    th = part("IA_tube_hatch", hatch, (tx + 0.172, ty, tz))
    mount("tube_mount", (tx, ty, tz))
    return d1, d2, th


def main():
    X.begin()
    shell()
    windows()
    beams()
    stair()
    drawers = counter()
    furniture()
    d1, d2, th = doors_and_misc()
    mount("board_mount", (-1.0, 0.0, Z0))
    mount("horn_mount", (X0, 3.35, 0.15))
    mount("wedge_mount", (SX, 0.0, 1.00))
    mount("rail_mount", (0.0, 0.0, ZB))
    mount("light_window_n", (3.1, 3.6, -2.2))
    mount("light_window_s", (0.0, 3.4, 2.9))
    mount("light_table_a", (-1.3, 1.05, -1.0))
    mount("light_table_b", (-1.3, 1.05, 0.6))
    for g, lst in grp.items():
        X.top(lst, 3)
    objs = {}
    for g, lst in grp.items():
        objs[g] = X.join_all(g, lst)
        objs[g].name = g
        objs[g].data.name = g
        M.set_origin(objs[g], G(0, 0, 0))
    req = list(grp.keys()) + ["IA_door_plate", "IA_door_office", "IA_tube_hatch", "IA_counter_drawer_0", "IA_counter_drawer_1", "IA_counter_drawer_2",
                              "board_mount", "horn_mount", "wedge_mount", "rail_mount", "tube_mount", "light_window_n", "light_window_s", "light_table_a",
                              "light_table_b"]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["IA_door_plate", "IA_door_office", "IA_tube_hatch", "IA_counter_drawer_0"], budget=BUDGET,
                          expect={"IA_door_plate": (-4.1, 0.0, Z0 + 0.045), "IA_door_office": (X1 - 0.045, 0.0, -2.4)}, show=["IA_door_plate", "IA_door_office"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")


main()
