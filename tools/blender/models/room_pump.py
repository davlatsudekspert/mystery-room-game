"""room_pump.glb — R2 the Pump Room (Level -1), built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3b/§7. "A ship's engine room at night": orange-black, iron, rivets, wet floor.
Interior x [-3.5, 3.5], z [-3.0, 3.0], floor y 0, ceiling y 3.4 (walls 0.25 thick outside). Lower walls riveted iron plate
(M_Iron_Rust) to 1.20, cast concrete above, concrete floor with chequer-plate walkways, a floor drain and wet patches, steel
I-beam ceiling with a pipe rack. Openings:
  south  x [-2.2, -1.2], y [0, 2.3]   the stair from the hall (stair block with steps and a rail outside; `stair_in`)
  east   z [-1.55, -0.65], y [0, 2.1] door to the Night Cell, leaf `IA_door_cell` (pivot at the hinge, the left edge seen from
         inside the room: (3.5, 0, -1.55); opens INTO the cell with a POSITIVE angle about +Y, +95 deg)
  west   z [-2.3, -0.7], y [0, 2.7]   book-lift niche 1.70 deep (x -5.2 .. -3.5), closed above 3.4; `lift_frame` iron surround
Suggested placements of the separate models (Godot position, yaw):
  boiler (0, 0, -1.75) 0   manifold_plate (3.5, 0, 1.35) -90   pipe_run (-3.5, 0, 1.05) +90
  book_lift_cage (-4.40, 0, -1.50) +90   mallet on `mallet_mount`
Own objects: floor, wall_n/_e/_s/_w, ceiling, beams, pipe_rack, walkway, pump_unit, bench, stair_in, lift_frame, dressing,
  puddles, IA_door_cell, work_lamp (+ work_lamp_bulb, work_lamp_light, pivot at the ceiling hook (0.5, 3.4, 0.2): swings about
  +X / +Z), mallet_mount (identity empty on the bench top at (1.55, 0.86, 2.55): the mallet lies there), light_boiler_glow
  (empty (0, 0.7, -0.55) in front of the boiler door), light_fill (empty (-1.5, 2.6, 1.0)).
    blender -b --factory-startup -P tools/blender/models/room_pump.py [-- --no-render] [--shots=a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "room_pump"
BUDGET = 22000
ARGS = M.main_guard()
X0, X1, Z0, Z1, H, T = -3.5, 3.5, -3.0, 3.0, 3.4, 0.25
IRON, CONC, STEEL, DARK, COP = "M_Iron_Rust", "M_Concrete", "M_Steel_Painted", "M_Steel_Dark", "M_Copper"
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def shell():
    ops = {"s": [(-2.2, -1.2, 0.0, 2.3)], "e": [(-1.55, -0.65, 0.0, 2.1)], "w": [(-2.3, -0.7, 0.0, 2.7)]}
    mats = {k: (IRON, 1.20, CONC) for k in "nsew"}
    w = X.wallset("pump", X0, X1, Z0, Z1, H, T, mats, ops, floor_mat=CONC, ceil_mat=CONC)
    for k in ("n", "s", "e", "w"):
        add("wall_" + k, *w[k])
    add("floor", *w["floor"])
    add("ceiling", *w["ceiling"])
    # plate seams (vertical straps) + rivet rows on the lower walls
    rv = []
    for side, along, fixed, sgn, lo, hi in (("n", "x", Z0, 1, X0, X1), ("s", "x", Z1, -1, X0, X1), ("e", "z", X1, -1, Z0, Z1),
                                            ("w", "z", X0, 1, Z0, Z1)):
        a = lo
        seams = []
        k = 0
        while a <= hi + 1e-6:
            seams.append(a)
            a += 0.70
        for s in seams:
            if side == "s" and -2.3 < s < -1.1:
                continue
            if side == "e" and -1.65 < s < -0.55:
                continue
            if side == "w" and -2.4 < s < -0.6:
                continue
            if along == "x":
                add("wall_" + side, gbox(f"seam{side}{k}", (s - 0.03, 0.05, fixed + sgn * 0.0 - (0.012 if sgn < 0 else 0)),
                                         (s + 0.03, 1.20, fixed + (0.012 if sgn > 0 else 0)), IRON, bevel=0.0))
                for y in (0.15, 0.40, 0.65, 0.90, 1.12):
                    rv.append((s - 0.02, y, fixed + sgn * 0.012))
                    rv.append((s + 0.02, y, fixed + sgn * 0.012))
            else:
                add("wall_" + side, gbox(f"seam{side}{k}", (fixed + (0.0 if sgn > 0 else -0.012), 0.05, s - 0.03),
                                         (fixed + (0.012 if sgn > 0 else 0.0), 1.20, s + 0.03), IRON, bevel=0.0))
                for y in (0.15, 0.40, 0.65, 0.90, 1.12):
                    rv.append((fixed + sgn * 0.012, y, s - 0.02))
                    rv.append((fixed + sgn * 0.012, y, s + 0.02))
            k += 1
    # horizontal plate edge at 0.6 and the dado band at 1.20
    for side, mn, mx in (("n", (X0, 1.20, Z0), (X1, 1.26, Z0 + 0.04)), ("s", (X0, 1.20, Z1 - 0.04), (X1, 1.26, Z1)),
                         ("e", (X1 - 0.04, 1.20, Z0), (X1, 1.26, Z1)), ("w", (X0, 1.20, Z0), (X0 + 0.04, 1.26, Z1))):
        add("wall_" + side, gbox("dado" + side, mn, mx, DARK, bevel=0.0))
    # rivets as one object (stub axis chosen per wall: use z-axis stubs on n/s, x-axis on e/w)
    rv_n = [p for p in rv if abs(p[2] - Z0) < 0.05 or abs(p[2] - Z1) < 0.05]
    rv_e = [p for p in rv if p not in rv_n]
    for pts, ax in ((rv_n, "z"), (rv_e, "x")):
        o = X.rivets("rivets" + ax, pts, 0.0095, ax, segs=5)
        add("dressing", o)
    # --- stair block outside the south wall (inside view: the opening is the doorway)
    stairs = []
    x0, x1 = -2.2, -1.2
    steps = 9
    for i in range(steps):
        z0 = Z1 + 0.25 + i * 0.30
        stairs.append(gbox(f"step{i}", (x0, 0.0, z0 - 0.0), (x1, 0.20 * (i + 1) + 0.0, z0 + 0.30), CONC, bevel=0.0))
        stairs.append(gbox(f"tread{i}", (x0, 0.20 * (i + 1), z0), (x1, 0.20 * (i + 1) + 0.025, z0 + 0.32), "M_Chequer", bevel=0.0))
    stairs.append(gbox("stair_wall_l", (x0 - 0.2, 0, Z1), (x0, 3.0, Z1 + 3.2), CONC, bevel=0.0))
    stairs.append(gbox("stair_wall_r", (x1, 0, Z1), (x1 + 0.2, 3.0, Z1 + 3.2), CONC, bevel=0.0))
    stairs.append(gbox("stair_top", (x0 - 0.2, 3.0, Z1), (x1 + 0.2, 3.2, Z1 + 3.2), CONC, bevel=0.0))
    # handrail pipe along the right side
    stairs.append(X.pipe("handrail", [(x1 - 0.06, 1.0, Z1 + 0.25), (x1 - 0.06, 1.0, Z1 + 0.25 + 0.30 * 3), (x1 - 0.06, 1.6, Z1 + 0.25 + 0.30 * 7)],
                         0.022, mat=STEEL, fillet=0.0, flange_ends=False))
    add("stair_in", *stairs)
    # --- door frame (east) and leaf
    add("wall_e", gbox("door_head", (X1 - 0.12, 2.10, -1.65), (X1 + 0.02, 2.22, -0.55), DARK, bevel=0.004),
        gbox("door_jamb_n", (X1 - 0.12, 0.0, -1.65), (X1 + 0.02, 2.10, -1.55), DARK, bevel=0.004),
        gbox("door_jamb_s", (X1 - 0.12, 0.0, -0.65), (X1 + 0.02, 2.10, -0.55), DARK, bevel=0.004))
    leaf = [gbox("leaf", (X1 - 0.07, 0.03, -1.55), (X1 - 0.02, 2.07, -0.65), "M_Wood_Panel", bevel=0.004)]
    for y in (0.35, 1.05, 1.75):
        leaf.append(gbox(f"strap{y}", (X1 - 0.085, y - 0.05, -1.55), (X1 - 0.065, y + 0.05, -0.80), IRON, bevel=0.003))
    leaf.append(gbox("handle", (X1 - 0.11, 1.0, -0.78), (X1 - 0.07, 1.04, -0.72), "M_Brass_Aged", bevel=0.003))
    for y in (0.35, 1.75):
        leaf.append(gcyl(f"hinge{y}", 0.020, 0.14, (X1 - 0.05, y - 0.07, -1.56), axis="y", verts=8, mat=DARK, bevel=0.0))
    ia = part("IA_door_cell", leaf, (X1 - 0.045, 0.0, -1.55))
    # --- lift niche (west): box 1.7 deep behind the opening, iron surround, floor grate plate
    nx0 = X0 - 1.7
    add("lift_frame", gbox("niche_back", (nx0 - 0.2, 0, -2.5), (nx0, H + 2.5, -0.5), CONC, bevel=0.0),
        gbox("niche_s", (nx0, 0, -0.7), (X0, H + 2.5, -0.5), CONC, bevel=0.0),
        gbox("niche_n", (nx0, 0, -2.5), (X0, H + 2.5, -2.3), CONC, bevel=0.0),
        gbox("niche_top", (nx0, H + 2.3, -2.5), (X0, H + 2.5, -0.5), CONC, bevel=0.0),
        gbox("niche_floor", (nx0, -0.2, -2.5), (X0, 0.0, -0.5), CONC, bevel=0.0))
    add("lift_frame", gbox("lf_l", (X0 + 0.02, 0.0, -2.38), (X0 + 0.14, 2.78, -2.30), IRON, bevel=0.005),
        gbox("lf_r", (X0 + 0.02, 0.0, -0.70), (X0 + 0.14, 2.78, -0.62), IRON, bevel=0.005),
        gbox("lf_t", (X0 + 0.02, 2.70, -2.38), (X0 + 0.14, 2.78, -0.62), IRON, bevel=0.005),
        gbox("lf_sill", (X0 - 0.30, 0.0, -2.30), (X0 + 0.14, 0.06, -0.70), "M_Chequer", bevel=0.003))
    for z in (-2.34, -0.66):
        for y in (0.3, 0.9, 1.5, 2.1, 2.62):
            add("dressing", gcyl(f"lfrv{z}{y}", 0.012, 0.012, (X0 + 0.14, y, z), axis="x", verts=6, mat=DARK, bevel=0.0))
    # guide rails in the niche for the cage
    for z in (-2.12, -0.88):
        add("lift_frame", gbox(f"guide{z}", (nx0 + 0.05, 0, z - 0.03), (nx0 + 0.12, H + 2.3, z + 0.03), DARK, bevel=0.002))
    return ia


def floor_dressing():
    # chequer walkways: from the stair to the boiler front, and in front of the manifold; drain grate; steps
    add("walkway", gbox("walk_a", (-2.45, 0.0, 0.8), (-0.95, 0.035, 3.0), "M_Chequer", bevel=0.002),
        gbox("walk_b", (-1.2, 0.0, -0.3), (-0.4, 0.040, 1.2), "M_Chequer", bevel=0.002),
        gbox("walk_c", (2.35, 0.0, 0.1), (3.5, 0.035, 2.6), "M_Chequer", bevel=0.002),
        gbox("walk_boiler", (-0.9, 0.0, -0.65), (0.9, 0.045, 0.1), "M_Chequer", bevel=0.002))
    # floor drain with grate bars
    gr = [gbox("drain_frame", (0.35, 0.0, 1.45), (1.05, 0.02, 1.95), DARK, bevel=0.002)]
    for i in range(8):
        gr.append(gbox(f"drain_bar{i}", (0.38 + i * 0.082, 0.02, 1.47), (0.38 + i * 0.082 + 0.04, 0.035, 1.93), "M_Steel_Dark", bevel=0.0))
    add("walkway", *gr)
    # wet patches: thin glossy quads
    pud = []
    for i, (cx, cz, rx, rz) in enumerate(((0.8, 0.9, 0.55, 0.38), (-1.8, -1.6, 0.45, 0.30), (1.9, -0.4, 0.35, 0.25), (-0.2, 2.3, 0.5, 0.3),
                                          (2.3, -2.4, 0.3, 0.22))):
        pts = [(cx + math.cos(a) * rx * (0.85 + 0.15 * math.sin(a * 3 + i)), cz + math.sin(a) * rz * (0.85 + 0.15 * math.cos(a * 2 + i)))
               for a in [2 * math.pi * k / 14 for k in range(14)]]
        add("puddles", X.flat_poly(f"puddle{i}", pts, 0.0045, "M_Lacquer_Black"))


def ceiling():
    # I-beams across x, pipe rack along z
    for i, z in enumerate((-2.3, -0.7, 0.9, 2.5)):
        add("beams", gbox(f"beam_web{i}", (X0, H - 0.34, z - 0.012), (X1, H - 0.04, z + 0.012), DARK, bevel=0.0),
            gbox(f"beam_fl{i}", (X0, H - 0.04, z - 0.09), (X1, H, z + 0.09), DARK, bevel=0.0),
            gbox(f"beam_fb{i}", (X0, H - 0.37, z - 0.09), (X1, H - 0.34, z + 0.09), DARK, bevel=0.0))
        for x in (-3.0, -1.5, 0.0, 1.5, 3.0):
            add("beams", gbox(f"gus{i}{x}", (x - 0.12, H - 0.34, z - 0.02), (x + 0.12, H - 0.04, z + 0.02), DARK, bevel=0.0))
    # three pipe runs along z under the beams: big painted steel, copper, insulated
    runs = [(("rackA", 0.20, STEEL, -2.9, 2.9, -2.6, 0.0)), (("rackB", 0.12, COP, -2.9, 2.9, -2.2, 1.3)), (("rackC", 0.16, "M_Steel_Cream", -2.9, 2.9, -1.2, 0.45))]
    # A: x = -2.6; B: x = -2.2? keep clear of the lift niche (z -2.3..-0.7 at x<-3.5 only) and the door
    for nm, r, mat, za, zb, x, _ in runs:
        y = H - 0.55 - (0.0 if nm != "rackC" else 0.05)
        add("pipe_rack", X.pipe(nm, [(x, y, za), (x, y, zb)], r, mat=mat, flange_r=r * 1.5, bolts=8, flange_mat=IRON))
        for z in (-2.0, -0.2, 1.6, 2.8):
            add("pipe_rack", gbox(f"hang{nm}{z}", (x - 0.012, y + r, z - 0.04), (x + 0.012, H - 0.37, z + 0.04), DARK, bevel=0.0),
                gcyl(f"strap{nm}{z}", r + 0.012, 0.05, (x, y, z - 0.025), axis="z", verts=14, mat=DARK, bevel=0.0))
        # flanges mid pipe
        for z in (-0.9, 1.2):
            add("pipe_rack", gcyl(f"mfl{nm}{z}", r * 1.45, 0.025, (x, y, z), axis="z", verts=16, mat=IRON, bevel=0.0))
    # wall header across north wall at 2.6 with a drop to the east wall
    add("pipe_rack", X.pipe("hdr_n", [(-3.3, 2.65, Z0 + 0.18), (2.2, 2.65, Z0 + 0.18), (3.3, 2.65, Z0 + 0.18)], 0.09, mat=COP, flange_r=0.13,
                            bolts=8, flange_mat=IRON, fillet=0.0))
    for x in (-2.6, -0.6, 1.4, 3.0):
        add("pipe_rack", gbox(f"hdr_br{x}", (x - 0.03, 2.55, Z0), (x + 0.03, 2.75, Z0 + 0.14), DARK, bevel=0.0))
    # vertical drop along the east wall corner to the manifold side
    add("pipe_rack", X.pipe("drop_e", [(3.3, 2.65, Z0 + 0.18), (3.3, 2.65, 0.4), (3.3, 2.1, 0.4)], 0.07, mat=COP, fillet=0.12, flange_r=0.10,
                            bolts=6, flange_mat=IRON))
    # flue hole sleeve through the ceiling above the boiler
    add("pipe_rack", glathe("flue_sleeve", [(0.19, 0.0), (0.24, 0.0), (0.24, 0.10), (0.19, 0.10)], (0.0, H - 0.10, -2.70), axis="y",
                            segments=16, mat=IRON))


def pump_unit():
    # water circulating pump with motor, against the north-east corner (east of the boiler)
    cx, cz = 2.55, -2.25
    u = [gbox("pu_base", (cx - 0.55, 0.0, cz - 0.30), (cx + 0.55, 0.12, cz + 0.30), IRON, bevel=0.008),
         glathe("pu_volute", [(0.0, 0.0), (0.20, 0.0), (0.24, 0.05), (0.24, 0.16), (0.20, 0.22), (0.0, 0.22)], (cx - 0.25, 0.37, cz), axis="x",
                segments=22, mat=IRON),
         gcyl("pu_neck", 0.07, 0.30, (cx - 0.25, 0.12, cz), axis="y", verts=12, mat=IRON, bevel=0.0),
         glathe("pu_motor", [(0.0, 0.0), (0.17, 0.0), (0.185, 0.03), (0.185, 0.46), (0.17, 0.50), (0.0, 0.50)], (cx + 0.00, 0.34, cz), axis="x",
                segments=24, mat="M_Steel_Painted"),
         glathe("pu_cap", [(0.0, 0.0), (0.12, 0.0), (0.14, 0.04), (0.0, 0.12)], (cx + 0.50, 0.34, cz), axis="x", segments=20, mat=DARK),
         gbox("pu_termbox", (cx + 0.15, 0.68, cz - 0.07), (cx + 0.35, 0.80, cz + 0.07), DARK, bevel=0.004)]
    for i in range(7):                         # cooling fins
        u.append(glathe(f"pu_fin{i}", [(0.184, 0.0), (0.205, 0.004), (0.205, 0.018), (0.184, 0.022)], (cx + 0.04 + i * 0.065, 0.34, cz), axis="x",
                        segments=24, mat="M_Steel_Painted"))
    u.append(X.wheel("pu_flywheel", 0.17, 0.016, 6, (cx - 0.52, 0.34, cz), axis="x", hub_r=0.035, boss_h=0.03, mat=IRON))
    u.append(X.pipe("pu_in", [(cx - 0.25, 0.30, cz - 0.24), (cx - 0.25, 0.30, Z0 + 0.15), (cx - 0.25, 1.2, Z0 + 0.15)], 0.055, mat=STEEL,
                    flange_r=0.085, bolts=6, flange_mat=IRON))
    u.append(X.pipe("pu_out", [(cx - 0.25, 0.60, cz), (cx - 0.25, 1.0, cz + 0.0), (cx - 0.25, 2.65, cz + 0.0)], 0.05, mat=COP, flange_r=0.08,
                    bolts=6, flange_mat=IRON))
    add("pump_unit", *u)


def bench():
    # workbench against the south wall east of the stair: x [0.9, 2.5], z [2.4, 2.95]
    bx0, bx1, bz0, bz1, top = 0.9, 2.5, 2.35, 2.95, 0.86
    b = [gbox("bn_top", (bx0, top - 0.06, bz0), (bx1, top, bz1), "M_Wood_Walnut", bevel=0.005),
         gbox("bn_shelf", (bx0 + 0.04, 0.22, bz0 + 0.04), (bx1 - 0.04, 0.26, bz1 - 0.02), "M_Wood_Panel", bevel=0.003)]
    for x in (bx0 + 0.05, bx1 - 0.05):
        for z in (bz0 + 0.04, bz1 - 0.04):
            b.append(gbox("bn_leg", (x - 0.04, 0.0, z - 0.04), (x + 0.04, top - 0.06, z + 0.04), "M_Wood_Walnut", bevel=0.003))
    # vise at the left end, oil can, rag, a tin
    b.append(gbox("vise_body", (bx0 + 0.08, top, bz0 + 0.05), (bx0 + 0.26, top + 0.10, bz0 + 0.23), DARK, bevel=0.004))
    b.append(gbox("vise_jaw", (bx0 + 0.06, top + 0.02, bz0 + 0.02), (bx0 + 0.28, top + 0.09, bz0 + 0.06), IRON, bevel=0.003))
    b.append(gcyl("vise_screw", 0.011, 0.20, (bx0 + 0.17, top + 0.06, bz0 - 0.15), axis="z", verts=8, mat="M_Chrome", bevel=0.0))
    b.append(gcyl("vise_knob", 0.016, 0.03, (bx0 + 0.17, top + 0.06, bz0 - 0.17), axis="z", verts=8, mat=DARK, bevel=0.0))
    b.append(glathe("oilcan", [(0.0, 0.0), (0.045, 0.0), (0.047, 0.005), (0.047, 0.10), (0.03, 0.12), (0.0, 0.12)], (bx0 + 0.95, top, bz0 + 0.30), axis="y",
                    segments=14, mat="M_Steel_Dark"))
    b.append(gcyl("oilspout", 0.006, 0.11, (bx0 + 0.95, top + 0.10, bz0 + 0.30), axis="y", verts=6, mat="M_Brass_Aged", bevel=0.0))
    # tool board above the bench with painted silhouettes and hooks
    b.append(gbox("toolboard", (bx0 + 0.1, 1.25, Z1 - 0.04), (bx1 - 0.1, 2.05, Z1 - 0.018), "M_Wood_Panel", bevel=0.004))
    for i, (tx, tl) in enumerate(((1.15, 0.30), (1.45, 0.38), (1.78, 0.26), (2.05, 0.34), (2.30, 0.22))):
        b.append(gbox(f"tool_ghost{i}", (tx - 0.02, 1.35, Z1 - 0.019 - 0.002), (tx + 0.02, 1.35 + tl, Z1 - 0.019), "M_Lacquer_Black", bevel=0.0))
        b.append(gcyl(f"hook{i}", 0.006, 0.05, (tx, 1.35 + tl + 0.03, Z1 - 0.06), axis="z", verts=5, mat=DARK, bevel=0.0))
    add("bench", *b)
    mount("mallet_mount", (1.60, top + 0.0, 2.58))
    # fire bucket and ladder-rung near the stair
    add("dressing", glathe("bucket", [(0.0, 0.0), (0.10, 0.0), (0.135, 0.28), (0.145, 0.30), (0.0, 0.30)], (-0.65, 0.0, 2.75), axis="y", segments=16,
                           mat="M_Enamel_Crimson"),
        glathe("bucket_rim", [(0.140, 0.285), (0.152, 0.29), (0.152, 0.31), (0.140, 0.31)], (-0.65, 0.0, 2.75), axis="y", segments=16, mat=DARK),
        gbox("bucket_rack", (-0.85, 0.55, Z1 - 0.04), (-0.45, 0.60, Z1), DARK, bevel=0.0))


def lamp_and_lights():
    hx, hy, hz = 0.5, H, 0.2
    L = [gbox("hook", (hx - 0.02, hy - 0.06, hz - 0.02), (hx + 0.02, hy, hz + 0.02), DARK, bevel=0.0)]
    cord = gcyl("cord", 0.008, 0.85, (hx, hy - 0.91, hz), axis="y", verts=6, mat="M_Rubber", bevel=0.0)
    L.append(cord)
    by = hy - 1.05
    L.append(glathe("lamp_socket", [(0.0, 0.0), (0.028, 0.0), (0.030, 0.02), (0.028, 0.07), (0.0, 0.07)], (hx, by + 0.0, hz), axis="y", segments=12, mat="M_Bakelite"))
    L.append(glathe("lamp_shade", [(0.0, 0.0), (0.045, 0.0), (0.12, -0.10), (0.125, -0.115), (0.115, -0.115), (0.04, -0.01), (0.0, -0.005)],
                    (hx, by + 0.14, hz), axis="y", segments=18, mat="M_Enamel_Green"))
    for i in range(6):
        a = i * math.pi / 3
        L.append(gcyl(f"cage{i}", 0.0035, 0.20, (hx + math.cos(a) * 0.085, by - 0.15, hz + math.sin(a) * 0.085), axis="y", verts=4, mat=DARK, bevel=0.0))
    L.append(gcyl("cage_ring", 0.095, 0.008, (hx, by - 0.16, hz), axis="y", verts=14, mat=DARK, bevel=0.0))
    lamp = part("work_lamp", L, (hx, hy, hz))
    bulb = part("work_lamp_bulb", [M.sphere("bulb", 0.040, loc=G(hx, by - 0.06, hz), segments=12, rings=6, mat="M_Emissive_Warm")],
                (hx, by - 0.06, hz), presmooth=False)
    bulb.parent = lamp
    bulb.matrix_parent_inverse = lamp.matrix_world.inverted()
    e = mount("work_lamp_light", (hx, by - 0.06, hz))
    e.parent = lamp
    e.matrix_parent_inverse = lamp.matrix_world.inverted()
    mount("light_boiler_glow", (0.0, 0.70, -0.55))
    mount("light_fill", (-1.5, 2.6, 1.0))
    return lamp


def main():
    X.begin()
    ia = shell()
    floor_dressing()
    ceiling()
    pump_unit()
    bench()
    lamp = lamp_and_lights()
    for k, v in grp.items():
        X.top(v, 4)
    objs = {}
    for g, lst in grp.items():
        objs[g] = X.join_all(g, lst)
        objs[g].name = g
        objs[g].data.name = g
        M.set_origin(objs[g], G(0, 0, 0))
    req = list(grp.keys()) + ["IA_door_cell", "work_lamp", "work_lamp_bulb", "work_lamp_light", "mallet_mount", "light_boiler_glow",
                              "light_fill"]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["IA_door_cell", "work_lamp", "work_lamp_bulb"], budget=BUDGET,
                          expect={"IA_door_cell": (X1 - 0.045, 0.0, -1.55), "work_lamp": (0.5, H, 0.2)}, show=["IA_door_cell", "work_lamp"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")


main()
