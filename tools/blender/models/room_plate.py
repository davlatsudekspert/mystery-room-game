"""room_plate.glb — R6 the Plate Room (Level +1), built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 3b/7. "A quiet confession box": deep red safelight, black walls over pale tile,
glass plates in tall wooden racks, a long steel sink with three trays, an enlarger bench, a drying table and a line of prints, a black
light-trap curtain and an extractor fan. NOT the Chapter 1 darkroom (no easel wall, no hanging shelf): this one is about glass plates.
Interior x [-3.0, 3.0], z [-2.6, 2.6], ceiling y 3.0, wall thickness 0.25.
Openings and parts (room space):
  south wall z = 2.6  door to the Gallery x [-2.6, -1.7] y [0, 2.2]: leaf `IA_door_gallery` (hinge at x = -1.7, opens +95 deg about +Y, OUT to +Z),
                      a black light-trap curtain `curtain` hangs 0.2 m inside it, the extractor fan grille above the door (`fan`)
  north wall          the enlarger bench `bench` (x -1.9 .. 1.7, top 0.90) with a bottle shelf, `paper_mount`
  west wall           the glass plate racks `plate_racks` (floor to 2.5 m, 40 slots per row)
  east wall           the sink bench `sink_bench` (z -1.9 .. 1.3, top 0.90, tile splashback, goosenecks), trays `trays`, the wall safelight
  centre              `drying_table` with a negative file box (strip mounts), the line of prints `print_line` along x at y 2.15
Suggested placements of separate models (Godot position, yaw): enlarger (0.20, 0.90, -2.20) 0 (mount `enlarger_mount`);
  negative_strip x4 on `strip_mount_0..3` (lying flat, x along the table).
Own objects: floor, wall_n/_e/_s/_w, ceiling, beams, bench, plate_racks, sink_bench, trays, drying_table, print_line, curtain, fan, safelights
  (static emissive housings), dressing, IA_door_gallery, empties enlarger_mount, paper_mount, strip_mount_0..3, light_safelight_a (-1.2, 2.7, -0.4),
  light_safelight_b (1.3, 2.7, 0.9), light_safelight_c (2.80, 2.1, -0.3), light_enlarger (0.25, 1.5, -2.1).
    blender -b --factory-startup -P tools/blender/models/room_plate.py [-- --no-render] [--shots=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402

NAME = "room_plate"
BUDGET = 40000
ARGS = M.main_guard()
X0, X1, Z0, Z1, H, T = -3.0, 3.0, -2.6, 2.6, 3.0, 0.25
TILE, BLACK, STEEL, DARK = "M_Tile_Glazed", "M_Paint_Black", "M_Steel_Galv", "M_Steel_Dark"
WOOD = "M_Wood_Panel"
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def shell():
    ops = {"s": [(-2.6, -1.7, 0.0, 2.2)]}
    mats = {"n": (TILE, 1.45, BLACK), "s": (TILE, 1.45, BLACK), "e": (TILE, 1.45, BLACK), "w": (TILE, 1.45, BLACK)}
    w = X.wallset("plate", X0, X1, Z0, Z1, H, T, mats, ops, floor_mat="M_Linoleum", ceil_mat=BLACK)
    for k in ("n", "s", "e", "w"):
        add("wall_" + k, *w[k])
    add("floor", *w["floor"])
    add("ceiling", *w["ceiling"])
    # tile cap rail at 1.45, skirting, floor drain channel and a wet patch
    for side, mn, mx in (("n", (X0, 1.45, Z0), (X1, 1.50, Z0 + 0.03)), ("s", (X0, 1.45, Z1 - 0.03), (X1, 1.50, Z1)),
                         ("e", (X1 - 0.03, 1.45, Z0), (X1, 1.50, Z1)), ("w", (X0, 1.45, Z0), (X0 + 0.03, 1.50, Z1))):
        add("dressing", gbox("cap" + side, mn, mx, "M_Steel_Dark", bevel=0.003))
    # tile grout: horizontal and vertical thin dark lines on the tile band
    g = []
    for y in (0.3, 0.6, 0.9, 1.2):
        g.append(gbox(f"gh_n{y}", (X0, y, Z0), (X1, y + 0.004, Z0 + 0.003), "M_Steel_Dark", bevel=0.0))
        g.append(gbox(f"gh_e{y}", (X1 - 0.003, y, Z0), (X1, y + 0.004, Z1), "M_Steel_Dark", bevel=0.0))
        g.append(gbox(f"gh_w{y}", (X0, y, Z0), (X0 + 0.003, y + 0.004, Z1), "M_Steel_Dark", bevel=0.0))
    add("dressing", *g)
    # floor drain gutter running to the east wall, and a red-lit wet patch
    add("dressing", gbox("gutter", (0.3, 0.0, -0.2), (3.0, 0.02, -0.08), "M_Steel_Dark", bevel=0.002))
    for i in range(10):
        add("dressing", gbox(f"gbar{i}", (0.34 + i * 0.26, 0.02, -0.19), (0.34 + i * 0.26 + 0.14, 0.03, -0.09), "M_Chrome", bevel=0.0))
    pts = [(1.2 + math.cos(a) * 0.55 * (0.85 + 0.15 * math.sin(a * 3)), 0.6 + math.sin(a) * 0.35) for a in [2 * math.pi * k / 14 for k in range(14)]]
    add("dressing", X.flat_poly("puddle", pts, 0.004, "M_Lacquer_Black"))


def ceiling():
    # low black beams across x, an extractor duct along the south wall, conduit
    for i, z in enumerate((-1.6, 0.0, 1.6)):
        add("beams", gbox(f"beam{i}", (X0, H - 0.22, z - 0.07), (X1, H, z + 0.07), "M_Steel_Dark", bevel=0.004))
    add("beams", X.pipe("duct", [(-2.2, H - 0.30, 2.2), (2.8, H - 0.30, 2.2), (2.8, H - 0.30, 0.0)], 0.17, mat=STEEL, flange_r=0.23, bolts=8, flange_mat="M_Iron_Rust", fillet=0.15))
    add("beams", X.pipe("conduit", [(-2.9, H - 0.08, -2.5), (-2.9, H - 0.08, 2.5)], 0.016, mat=DARK, flange_ends=False, sides=6))
    # safelight housings: three ceiling domes with a red lens (emissive) and a wall one over the sink
    for nm, x, y, z in (("sa", -1.2, H, -0.4), ("sb", 1.3, H, 0.9)):
        add("beams", glathe(nm + "_cup", [(0.0, 0.0), (0.12, 0.0), (0.14, -0.05), (0.10, -0.15), (0.0, -0.15)], (x, y, z), axis="y", segments=16, mat="M_Iron_Rust"),
            gcyl(nm + "_stem", 0.012, 0.06, (x, y - 0.03, z), axis="y", verts=6, mat=DARK, bevel=0.0))
        add("safelights", glathe(nm + "_lens", [(0.0, -0.14), (0.085, -0.14), (0.10, -0.16), (0.0, -0.20)], (x, y, z), axis="y", segments=14, mat="M_Emissive_Safelight"),
            M.sphere(nm + "_glow", 0.05, loc=G(x, y - 0.17, z), segments=10, rings=6, mat="M_Emissive_Safelight"))
    # wall safelight over the sink (east wall): a cast hood with a red glass disc facing -x
    add("beams", glathe("sc_hood", [(0.0, 0.0), (0.11, 0.0), (0.13, 0.04), (0.11, 0.16), (0.0, 0.16)], (X1 - 0.16, 2.1, -0.3), axis="x", segments=16, mat="M_Iron_Rust"),
        gbox("sc_arm", (X1 - 0.02, 2.03, -0.34), (X1, 2.17, -0.26), DARK, bevel=0.0))
    add("safelights", gcyl("sc_lens", 0.09, 0.012, (X1 - 0.174, 2.1, -0.3), axis="x", verts=16, mat="M_Emissive_Safelight", bevel=0.0))
    mount("light_safelight_a", (-1.2, 2.7, -0.4))
    mount("light_safelight_b", (1.3, 2.7, 0.9))
    mount("light_safelight_c", (X1 - 0.20, 2.1, -0.3))


def door_and_curtain():
    o = [gbox("leaf", (-2.6, 0.03, Z1 - 0.07), (-1.7, 2.17, Z1 - 0.02), "M_Paint_Black", bevel=0.004),
         gbox("leaf_rail", (-2.6, 1.0, Z1 - 0.082), (-1.7, 1.1, Z1 - 0.07), DARK, bevel=0.002),
         gbox("handle", (-2.55, 1.0, Z1 - 0.10), (-2.45, 1.07, Z1 - 0.07), "M_Chrome", bevel=0.003),
         gbox("seal_a", (-2.6, 0.03, Z1 - 0.082), (-2.585, 2.17, Z1 - 0.07), "M_Rubber", bevel=0.0),
         gbox("seal_b", (-1.715, 0.03, Z1 - 0.082), (-1.7, 2.17, Z1 - 0.07), "M_Rubber", bevel=0.0)]
    ia = part("IA_door_gallery", o, (-1.7, 0.0, Z1 - 0.045))
    add("dressing", gbox("fr_h", (-2.7, 2.20, Z1 - 0.10), (-1.6, 2.30, Z1), DARK, bevel=0.004), gbox("fr_a", (-2.7, 0.0, Z1 - 0.10), (-2.6, 2.20, Z1), DARK, bevel=0.004),
        gbox("fr_b", (-1.7, 0.0, Z1 - 0.10), (-1.6, 2.20, Z1), DARK, bevel=0.004))
    # light-trap curtain: pleated black drapes on a ceiling rail
    c = [gbox("c_rail", (-2.9, 2.60, 2.12), (-1.4, 2.64, 2.16), DARK, bevel=0.002)]
    n = 14
    for i in range(n):
        x = -2.85 + i * (1.35 / n)
        z = 2.15 + (0.05 if i % 2 else 0.0)
        c.append(gbox(f"fold{i}", (x, 0.04, z), (x + 1.35 / n * 1.05, 2.60, z + 0.03), "M_Velvet", bevel=0.004))
    for i in range(6):
        c.append(gcyl(f"ring{i}", 0.012, 0.03, (-2.8 + i * 0.25, 2.58, 2.135), axis="z", verts=6, mat="M_Brass_Aged", bevel=0.0))
    add("curtain", *c)
    # extractor fan above the door: round grille in a square frame, a fan rose behind it, louvres
    f = [gbox("fan_frame", (1.5, 1.95, Z1 - 0.06), (2.5, 2.75, Z1), DARK, bevel=0.01), gcyl("fan_ring", 0.34, 0.03, (2.0, 2.35, Z1 - 0.09), axis="z", verts=24, mat="M_Steel_Galv", bevel=0.0)]
    for k in range(5):
        a = math.tau * k / 5
        f.append(gbox(f"blade{k}", (-0.012, 0.0, -0.004), (0.012, 0.28, 0.004), "M_Steel_Dark", bevel=0.0))
        U.rot_godot([f[-1]], "z", math.degrees(a), (0, 0, 0))
        U.move([f[-1]], (2.0, 2.35, Z1 - 0.08))
    f.append(gcyl("fan_hub", 0.04, 0.03, (2.0, 2.35, Z1 - 0.11), axis="z", verts=10, mat=DARK, bevel=0.0))
    for k in range(9):
        f.append(gbox(f"louv{k}", (1.57, 2.0 + k * 0.08, Z1 - 0.11), (2.43, 2.0 + k * 0.08 + 0.012, Z1 - 0.07), "M_Steel_Galv", bevel=0.0))
    add("fan", *f)
    return ia


def bench_and_enlarger_zone():
    top = 0.90
    b = [gbox("bn_top", (-1.9, top - 0.06, Z0), (1.7, top, Z0 + 0.72), "M_Wood_Mahogany", bevel=0.006),
         gbox("bn_lino", (-1.9, top, Z0), (1.7, top + 0.004, Z0 + 0.72), "M_Rubber", bevel=0.0),
         gbox("bn_back", (-1.9, top, Z0), (1.7, top + 0.12, Z0 + 0.03), WOOD, bevel=0.003)]
    for x in (-1.85, 1.65):
        b.append(gbox("bn_leg", (x - 0.04, 0.0, Z0 + 0.04), (x + 0.04, top - 0.06, Z0 + 0.68), WOOD, bevel=0.003))
    b.append(gbox("bn_cupboard", (-1.8, 0.1, Z0 + 0.03), (-0.2, top - 0.06, Z0 + 0.68), "M_Wood_Mahogany", bevel=0.004))
    for k in range(2):
        b.append(gbox(f"bn_door{k}", (-1.78 + k * 0.80, 0.14, Z0 + 0.68), (-1.0 + k * 0.80, top - 0.10, Z0 + 0.705), "M_Wood_Mahogany", bevel=0.004))
        b.append(gbox(f"bn_knob{k}", (-1.04 + k * 0.80, 0.55, Z0 + 0.705), (-1.0 + k * 0.80, 0.60, Z0 + 0.73), "M_Brass_Aged", bevel=0.003))
    # the bottle shelf above: two shelves with amber and clear bottles, a funnel
    for y in (1.55, 1.95):
        b.append(gbox(f"shelf{y}", (-1.9, y, Z0), (1.7, y + 0.03, Z0 + 0.22), "M_Wood_Mahogany", bevel=0.003))
    rnd = random.Random(5)
    for i in range(15):
        x = -1.8 + i * 0.235
        for y in (1.58, 1.98):
            if rnd.random() < 0.8:
                r = rnd.uniform(0.032, 0.05)
                h = rnd.uniform(0.15, 0.27)
                mt = rnd.choice(["M_Glass_Amber", "M_Glass_Amber", "M_Glass", "M_Glass_Green"])
                b.append(glathe(f"btl{i}_{y}", [(0.0, 0.0), (r, 0.0), (r, h * 0.7), (r * 0.4, h * 0.85), (r * 0.35, h), (0.0, h)], (x, y, Z0 + 0.12), axis="y", segments=10, mat=mt))
                b.append(gcyl(f"cork{i}_{y}", r * 0.38, 0.03, (x, y + h, Z0 + 0.12), axis="y", verts=6, mat="M_Cork", bevel=0.0))
    # paper tray (flat tray of photographic paper, red lit) and a safelight timer on the bench front
    b.append(gbox("paper_box", (-1.55, top, Z0 + 0.20), (-1.05, top + 0.05, Z0 + 0.55), "M_Cardboard", bevel=0.004))
    b.append(gbox("paper_lid", (-1.57, top + 0.05, Z0 + 0.18), (-1.03, top + 0.062, Z0 + 0.57), "M_Cardboard", bevel=0.003))
    b.append(gbox("paper_label", (-1.48, top + 0.062, Z0 + 0.30), (-1.12, top + 0.064, Z0 + 0.45), "M_Enamel_Cream", bevel=0.0))
    add("bench", *b)
    mount("enlarger_mount", (0.20, top, -2.20))
    mount("paper_mount", (-1.30, top + 0.065, Z0 + 0.38))
    mount("light_enlarger", (0.25, 1.5, -2.1))


def plate_racks():
    """West wall: two tall wooden racks of glass plates (vertical slots, plate edges visible as pale green glass slabs)."""
    r = []
    rx0, rx1 = X0, X0 + 0.34
    for zc0, zc1, nm in ((-2.45, -0.15, "ra"), (0.15, 2.0, "rb")):
        r.append(gbox(nm + "_back", (rx0, 0.05, zc0), (rx0 + 0.02, 2.55, zc1), WOOD, bevel=0.0))
        for z in (zc0, zc1 - 0.04):
            r.append(gbox(nm + "_side", (rx0, 0.0, z), (rx1, 2.6, z + 0.04), "M_Wood_Mahogany", bevel=0.004))
        r.append(gbox(nm + "_top", (rx0, 2.55, zc0), (rx1 + 0.02, 2.62, zc1), "M_Wood_Mahogany", bevel=0.005))
        r.append(gbox(nm + "_foot", (rx0, 0.0, zc0), (rx1 + 0.03, 0.14, zc1), "M_Wood_Mahogany", bevel=0.004))
        rows = 4
        rnd = random.Random(31 if nm == "ra" else 47)
        for ri in range(rows):
            y0 = 0.22 + ri * 0.58
            r.append(gbox(nm + f"_shelf{ri}", (rx0, y0 - 0.025, zc0), (rx1, y0, zc1), "M_Wood_Mahogany", bevel=0.002))
            # comb of dividers + plates standing on edge, plates are 0.0035 thick, 0.40 tall
            nslots = int((zc1 - zc0 - 0.1) / 0.052)
            for k in range(nslots):
                z = zc0 + 0.06 + k * 0.052
                r.append(gbox(nm + f"_div{ri}_{k}", (rx0 + 0.02, y0, z), (rx1 - 0.02, y0 + 0.04, z + 0.004), "M_Wood_Mahogany", bevel=0.0))
                if rnd.random() < 0.72:
                    lean = rnd.uniform(-0.004, 0.004)
                    r.append(gbox(nm + f"_pl{ri}_{k}", (rx0 + 0.05, y0 + 0.01, z + 0.012 + lean), (rx1 - 0.015, y0 + 0.40, z + 0.0155 + lean), "M_Glass_Green", bevel=0.0))
        # brass index card holder per row on the front edge
        for ri in range(rows):
            y0 = 0.22 + ri * 0.58
            r.append(gbox(nm + f"_card{ri}", (rx1, y0 - 0.02, (zc0 + zc1) / 2 - 0.07), (rx1 + 0.01, y0 + 0.005, (zc0 + zc1) / 2 + 0.07), "M_Brass_Aged", bevel=0.0))
    add("plate_racks", *r)


def sink_and_trays():
    top = 0.90
    s = []
    z0, z1 = -1.9, 1.3
    sx0, sx1 = X1 - 0.78, X1
    # steel bench with a deep trough
    s.append(gbox("sk_body", (sx0, 0.10, z0), (sx1, top - 0.10, z1), STEEL, bevel=0.004))
    s.append(gbox("sk_plinth", (sx0 + 0.02, 0.0, z0 + 0.02), (sx1 - 0.0, 0.10, z1 - 0.02), DARK, bevel=0.003))
    s.append(gbox("sk_top_f", (sx0 - 0.03, top - 0.10, z0 - 0.03), (sx0 + 0.07, top, z1 + 0.03), STEEL, bevel=0.005))
    s.append(gbox("sk_top_b", (sx1 - 0.10, top - 0.10, z0 - 0.03), (sx1, top + 0.0, z1 + 0.03), STEEL, bevel=0.005))
    s.append(gbox("sk_top_n", (sx0 - 0.03, top - 0.10, z0 - 0.03), (sx1, top, z0 + 0.07), STEEL, bevel=0.005))
    s.append(gbox("sk_top_s", (sx0 - 0.03, top - 0.10, z1 - 0.07), (sx1, top, z1 + 0.03), STEEL, bevel=0.005))
    s.append(gbox("sk_floor", (sx0 + 0.07, top - 0.16, z0 + 0.07), (sx1 - 0.10, top - 0.15, z1 - 0.07), "M_Steel_Dark", bevel=0.0))
    # splashback tile + shelf of plates drying on a rack above
    s.append(gbox("sk_splash", (X1 - 0.035, top, z0 - 0.03), (X1, 1.60, z1 + 0.03), "M_Tile_Glazed", bevel=0.0))
    s.append(gbox("sk_ledge", (X1 - 0.07, 1.60, z0 - 0.03), (X1, 1.64, z1 + 0.03), STEEL, bevel=0.004))
    # goosenecks: brass pipes with a tap wheel, three of them
    for zz in (-1.35, -0.55, 0.25):
        s.append(X.pipe(f"tap{zz}", [(X1 - 0.12, top + 0.02, zz), (X1 - 0.12, top + 0.32, zz), (X1 - 0.28, top + 0.40, zz), (X1 - 0.34, top + 0.30, zz)], 0.012,
                        mat="M_Brass_Polished", fillet=0.05, flange_ends=False, sides=8))
        s.append(gcyl(f"tap_base{zz}", 0.026, 0.03, (X1 - 0.12, top, zz), axis="y", verts=10, mat="M_Brass_Aged", bevel=0.003))
        s.append(X.wheel(f"tapw{zz}", 0.035, 0.005, 4, (X1 - 0.12, top + 0.22, zz + 0.045), axis="z", hub_r=0.011, boss_h=0.008, mat="M_Enamel_Crimson"))
    # drying rack on the ledge: plates leaning in a wire comb
    dr = [gbox("dr_base", (X1 - 0.30, 1.64, z0 + 0.1), (X1 - 0.05, 1.67, z0 + 1.7), "M_Wood_Mahogany", bevel=0.003)]
    for k in range(18):
        z = z0 + 0.14 + k * 0.085
        dr.append(gbox(f"dr_w{k}", (X1 - 0.29, 1.67, z), (X1 - 0.06, 1.70, z + 0.004), "M_Wood_Mahogany", bevel=0.0))
        if k % 3 != 2:
            dr.append(gbox(f"dr_pl{k}", (X1 - 0.27, 1.675, z + 0.008), (X1 - 0.075, 2.08, z + 0.0115), "M_Glass", bevel=0.0))
    add("sink_bench", *s, *dr)
    # three enamel trays on the trough (developer, stop, fix) with a shallow bath, each with a pair of brass tongs on the rim
    t = []
    for i, (zz, col) in enumerate(((-1.35, "M_Liquid_Green"), (-0.55, "M_Liquid_Cobalt"), (0.25, "M_Liquid_Crimson"))):
        cx = X1 - 0.38
        t.append(gbox(f"tray{i}_floor", (cx - 0.22, top - 0.14, zz - 0.28), (cx + 0.22, top - 0.125, zz + 0.28), "M_Enamel_White", bevel=0.002))
        for (a0, a1, b0, b1) in ((-0.22, -0.20, -0.28, 0.28), (0.20, 0.22, -0.28, 0.28), (-0.22, 0.22, -0.28, -0.26), (-0.22, 0.22, 0.26, 0.28)):
            t.append(gbox(f"tray{i}_rim", (cx + a0, top - 0.14, zz + b0), (cx + a1, top - 0.07, zz + b1), "M_Enamel_White", bevel=0.002))
        t.append(gbox(f"tray{i}_liq", (cx - 0.2, top - 0.125, zz - 0.26), (cx + 0.2, top - 0.105, zz + 0.26), col, bevel=0.0))
        t.append(gbox(f"tongs{i}", (cx + 0.12, top - 0.07, zz + 0.285), (cx + 0.24, top - 0.062, zz + 0.295), "M_Steel_Dark", bevel=0.0))
    add("trays", *t)


def drying_table():
    """Centre-left table with a negative file box, a stack of plate boxes, a tray rack and the print line above."""
    tx0, tx1, tz0, tz1, top = -1.9, -0.1, -0.35, 0.50, 0.90
    d = [gbox("dt_top", (tx0, top - 0.05, tz0), (tx1, top, tz1), "M_Wood_Mahogany", bevel=0.006, seg=2),
         gbox("dt_under", (tx0 + 0.06, 0.28, tz0 + 0.04), (tx1 - 0.06, 0.32, tz1 - 0.04), "M_Wood_Panel", bevel=0.0)]
    for x in (tx0 + 0.07, tx1 - 0.07):
        for z in (tz0 + 0.07, tz1 - 0.07):
            d.append(gbox("dt_leg", (x - 0.035, 0.0, z - 0.035), (x + 0.035, top - 0.05, z + 0.035), "M_Wood_Mahogany", bevel=0.004))
    # negative file box: low wooden box with a sloped lid propped open and four slots; the four strips lie in front of it
    d.append(gbox("nb_box", (-1.80, top, -0.27), (-1.20, top + 0.07, 0.00), WOOD, bevel=0.004))
    d.append(gbox("nb_lid", (-1.82, top + 0.07, -0.30), (-1.18, top + 0.085, -0.255), WOOD, bevel=0.003))
    d.append(gbox("nb_label", (-1.60, top + 0.07, 0.0), (-1.40, top + 0.075, 0.003), "M_Brass_Aged", bevel=0.0))
    for k in range(4):
        d.append(gbox(f"nb_slot{k}", (-1.77 + k * 0.145, top + 0.07, -0.20), (-1.65 + k * 0.145, top + 0.072, -0.02), "M_Lacquer_Black", bevel=0.0))
        mount(f"strip_mount_{k}", (-1.62 + k * 0.0, top + 0.002, 0.1 + k * 0.09))
    # plate boxes (cardboard, brass corner label), a stack of three
    for i, (x, z, w, dd, y) in enumerate(((-0.70, -0.15, 0.30, 0.22, top), (-0.70, -0.15, 0.30, 0.22, top + 0.08), (-0.45, 0.20, 0.26, 0.20, top))):
        d.append(gbox(f"pbox{i}", (x - w / 2, y, z - dd / 2), (x + w / 2, y + 0.08, z + dd / 2), "M_Cardboard", bevel=0.004))
        d.append(gbox(f"pbox_l{i}", (x - 0.05, y + 0.03, z + dd / 2), (x + 0.05, y + 0.06, z + dd / 2 + 0.003), "M_Brass_Aged", bevel=0.0))
    # a folding stool and a lamp-less cord reel beside the table
    d.append(gbox("stool_top", (-1.55, 0.44, 0.90), (-1.15, 0.48, 1.30), "M_Wood_Mahogany", bevel=0.005))
    for x in (-1.5, -1.2):
        for z in (0.95, 1.25):
            d.append(gbox("stool_leg", (x - 0.016, 0.0, z - 0.016), (x + 0.016, 0.44, z + 0.016), "M_Wood_Mahogany", bevel=0.002))
    add("drying_table", *d)
    # print line: two cords across the room at y 2.15 with six pegged prints (one decal quad each, slot M_Decal_Prints)
    X.decal("M_Decal_Prints", "print_proj.png")
    pl = [gcyl("cord_a", 0.004, 4.9, (-2.35, 2.17, -1.2), axis="x", verts=4, mat="M_String_Red", bevel=0.0),
          gbox("hook_a", (-2.4, 2.12, -1.22), (-2.34, 2.22, -1.18), DARK, bevel=0.0), gbox("hook_b", (2.5, 2.12, -1.22), (2.56, 2.22, -1.18), DARK, bevel=0.0)]
    rnd = random.Random(9)
    for k in range(6):
        x = -2.0 + k * 0.62
        q = gquad(f"print{k}", (x, 1.98, -1.19), (1, 0, 0), (0, 1, 0), 0.20, 0.26, "M_Decal_Prints")
        pl.append(q)
        for dx in (-0.075, 0.075):
            pl.append(gbox(f"peg{k}_{dx}", (x + dx - 0.01, 2.10, -1.205), (x + dx + 0.01, 2.20, -1.175), "M_Wood_Floor", bevel=0.001))
    add("print_line", *pl)


def dressing():
    # a wall timer (big enamel dial) above the door side, a pegboard of tongs and thermometers, a fire bucket, a dustbin
    d = [gcyl("timer", 0.20, 0.05, (-2.0, 2.0, Z0 + 0.0), axis="z", verts=26, mat="M_Enamel_Cream", bevel=0.004),
         gcyl("timer_rim", 0.215, 0.025, (-2.0, 2.0, Z0 + 0.0), axis="z", verts=26, mat="M_Brass_Aged", bevel=0.0),
         gbox("timer_hand_a", (-2.008, 2.0, Z0 + 0.052), (-1.992, 2.17, Z0 + 0.056), "M_Lacquer_Black", bevel=0.0),
         gbox("timer_hand_b", (-2.0, 1.995, Z0 + 0.056), (-1.84, 2.005, Z0 + 0.06), "M_Enamel_Crimson", bevel=0.0)]
    for k in range(12):
        a = math.tau * k / 12
        d.append(gbox(f"tm{k}", (-0.006, 0.150, 0.0), (0.006, 0.185, 0.003), "M_Lacquer_Black", bevel=0.0))
        U.rot_godot([d[-1]], "z", math.degrees(a), (0, 0, 0))
        U.move([d[-1]], (-2.0, 2.0, Z0 + 0.052))
    d.append(gbox("peg_board", (1.9, 1.2, Z0), (2.9, 2.2, Z0 + 0.025), "M_Cork", bevel=0.0))
    for k, (x, ln) in enumerate(((2.05, 0.30), (2.25, 0.22), (2.45, 0.36), (2.65, 0.26))):
        d.append(gbox(f"tool{k}", (x - 0.012, 2.05 - ln, Z0 + 0.025), (x + 0.012, 2.05, Z0 + 0.034), "M_Steel_Dark" if k % 2 == 0 else "M_Chrome", bevel=0.0))
        d.append(gcyl(f"tool_pin{k}", 0.005, 0.03, (x, 2.07, Z0 + 0.025), axis="z", verts=6, mat="M_Brass_Aged", bevel=0.0))
    d.append(glathe("bucket", [(0.0, 0.0), (0.10, 0.0), (0.135, 0.28), (0.145, 0.30), (0.0, 0.30)], (2.2, 0.0, 1.9), axis="y", segments=14, mat="M_Enamel_Crimson"))
    d.append(glathe("bin", [(0.0, 0.0), (0.16, 0.0), (0.19, 0.50), (0.0, 0.50)], (2.6, 0.0, 2.1), axis="y", segments=14, mat="M_Steel_Galv"))
    add("dressing", *d)


def main():
    X.begin()
    shell()
    ceiling()
    ia = door_and_curtain()
    bench_and_enlarger_zone()
    plate_racks()
    sink_and_trays()
    drying_table()
    dressing()
    for g, lst in grp.items():
        X.top(lst, 3)
    objs = {}
    for g, lst in grp.items():
        objs[g] = X.join_all(g, lst)
        objs[g].name = g
        objs[g].data.name = g
        M.set_origin(objs[g], G(0, 0, 0))
    req = list(grp.keys()) + ["IA_door_gallery", "enlarger_mount", "paper_mount", "light_safelight_a", "light_safelight_b", "light_safelight_c", "light_enlarger"] + \
        [f"strip_mount_{k}" for k in range(4)]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["IA_door_gallery"], budget=BUDGET, expect={"IA_door_gallery": (-1.7, 0.0, Z1 - 0.045)}, show=["IA_door_gallery"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")


main()
