"""leyla_camp.glb — Leyla's 1998 field camp inside the Nursery's camp room (E): an army cot with a sleeping bag, a
rucksack and a field coat, a battery rig with cables running to the folding table, crates, a thermos and mug, a torch,
a stack of tape boxes, blank papers pinned to the walls, and the bare bulb. Contract: docs/models/ch3.md §7 leyla_camp
(+ §1.1 camp, §2 camp / shutter / recorder views, §1.5 camp_lamp); results: docs/models/ch3_e.md.

ROOM-COORDINATE model (§0): origin = the world origin, built in place in the camp x 4.5 .. 7.6, z -4.0 .. -1.2, y 0 .. 2.9
(the walls are shell_nursery's `camp_walls`; tile faces: north z -3.965, west x 4.535).

  leyla_camp   (static, M_Fabric / M_Wood_Panel / M_Steel_Dark / M_Paper) everything below as ONE mesh:
      cot            x 5.2 .. 7.2, z -3.95 .. -3.30: wooden rails and crossed legs, canvas sag, sleeping bag, pillow,
                     folded blanket; a coat hung on a peg board over it (north wall, x 5.55)
      rucksack       on a crate in the north-west corner (x 4.65 .. 5.10, z -3.92 .. -3.57) with a bedroll
      battery rig    a crate x 7.0 .. 7.55, z -3.20 .. -2.50 (top y 0.30) with three car batteries, terminals and
                     jumpers; two cables run over the floor to the table's east edge and end beside the recorder
                     and the oscillograph
      folding table  x 4.60 .. 5.40, z -1.90 .. -1.25, top y 0.74: wooden top, steel rim, crossed steel legs and rails
      crate stack    x 7.15 .. 7.55, z -2.35 .. -1.95 with a thermos, a mug and four tape boxes on top; a torch on the
                     table's east end; a woven floor mat; twelve blank sheets pinned to the north, west and south
                     walls; the ceiling rose, flex and bulb holder
  camp_bulb    (M_Paper) the bare bulb, origin at its centre (6.2, 2.55, -2.6); the code turns emission on
  camp_light   empty at (6.2, 2.45, -2.6): the camp_lamp omni

    blender -b --factory-startup -P tools/blender/models/leyla_camp.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "leyla_camp"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 9000, 6, 4
FAB, WOOD, STEEL, PAPER = E.FABRIC, E.PANEL, E.STEEL, E.PAPER

WALL_N, WALL_W, WALL_S = -3.965, 4.535, -1.203      # tile faces / the south partition's inner face (+ a hair)
BULB_C = (6.2, 2.55, -2.6)
CAMP_LIGHT = E.CAMP_LIGHT
TABLE = (4.60, 5.40, -1.90, -1.25)                   # x0, x1, z0, z1
TABLE_TOP = 0.74
RIG = (7.00, 7.55, -3.20, -2.50)                     # the battery crate
RIG_H = 0.30
CRATE_B = (7.15, 7.55, -2.35, -1.95)
CRATE_D = (4.65, 5.10, -3.92, -3.57)


def jit(o, amp, seed):
    E.jitter(o, amp, seed)
    return o


# ====================================================================== cot, bag, coat, rucksack
def cot():
    fab, wood = [], []
    x0, x1, z0, z1, y = 5.2, 7.2, -3.95, -3.30, 0.40
    # long rails and end bars (wood), crossed legs (wood) at both ends
    for z in (z0 + 0.02, z1 - 0.02):
        wood.append(K.gbox("rail", (x0, y - 0.05, z - 0.015), (x1, y, z + 0.015), WOOD, 0.002))
    for x in (x0 + 0.02, x1 - 0.02):
        wood.append(K.gbox("end", (x - 0.015, y - 0.045, z0 + 0.02), (x + 0.015, y - 0.015, z1 - 0.02), WOOD, 0.002))
    for x in (x0 + 0.12, x1 - 0.12):
        a, b = (x, 0.0, z0 + 0.02), (x, y - 0.03, z1 - 0.02)
        c, d = (x, 0.0, z1 - 0.02), (x, y - 0.03, z0 + 0.02)
        wood.append(D.rod("leg", a, b, 0.016, segs=4, mat=WOOD, caps=True))
        wood.append(D.rod("leg", c, d, 0.016, segs=4, mat=WOOD, caps=True))
        wood.append(K.gbox("brace", (x - 0.012, 0.19, z0 + 0.02), (x + 0.012, 0.215, z1 - 0.02), WOOD, 0.0))
    # canvas
    can = E.cloth_patch("canvas", (x0 + 0.015, y - 0.004, z0 + 0.035), (x1 - x0 - 0.03, 0, 0), (0, 0, z1 - z0 - 0.07),
                        14, 4, 0.03, FAB, seed=3, amp=0.0015)
    fab.append(can)
    # sleeping bag (rumpled), pillow, folded blanket at the foot
    bag = E.sausage("bag", (5.72, 0.495, -3.64), (6.92, 0.495, -3.62), 0.165, rings=5, sides=12, mat=FAB, squash=0.55)
    fab.append(jit(bag, 0.004, 5))
    pil = E.sausage("pillow", (5.44, 0.475, -3.78), (5.44, 0.475, -3.46), 0.085, rings=4, sides=10, mat=FAB, squash=0.6)
    fab.append(jit(pil, 0.003, 6))
    blk = K.gbox("blanket", (6.98, 0.405, -3.88), (7.17, 0.455, -3.36), FAB, 0.012, 2)
    fab.append(jit(blk, 0.002, 7))
    blk2 = K.gbox("blanket2", (6.99, 0.455, -3.84), (7.15, 0.485, -3.40), FAB, 0.01, 2)
    fab.append(jit(blk2, 0.002, 8))
    return fab, wood


def coat():
    """A 1990s field coat on a peg board on the north wall, over the cot's west end (x 5.55)."""
    fab, wood, steel = [], [], []
    cx, wz = 5.55, WALL_N
    wood.append(K.gbox("pegboard", (cx - 0.28, 1.90, wz), (cx + 0.28, 1.97, wz + 0.022), WOOD, 0.002))
    for dx in (-0.2, 0.0, 0.2):
        steel.append(K.gcyl("peg", 0.011, 0.0, 0.07, base=(cx + dx, 1.935, wz + 0.02), axis=(0, 0, 1), segments=6, mat=STEEL,
                            chamfer=0.003))
    zc = wz + 0.08
    fab.append(E.rrect_box("coat_body", 0.47, 0.82, 0.10, 0.045, (cx, 1.40, zc), FAB, n=3, bevel=0.008))
    fab.append(E.rrect_box("coat_skirt", 0.50, 0.14, 0.115, 0.05, (cx, 1.05, zc + 0.003), FAB, n=3, bevel=0.008))
    fab.append(E.sausage("collar", (cx - 0.17, 1.83, zc + 0.01), (cx + 0.17, 1.83, zc + 0.01), 0.05, rings=4, sides=8, mat=FAB))
    for sx in (-1, 1):
        s = E.sausage("sleeve", (cx + sx * 0.265, 1.78, zc + 0.005), (cx + sx * 0.30, 1.12, zc + 0.03), 0.046, rings=4, sides=8,
                      mat=FAB)
        fab.append(jit(s, 0.003, 10 + sx))
        fab.append(K.gbox("pocket", (cx + sx * 0.13 - 0.075, 1.12, zc + 0.05), (cx + sx * 0.13 + 0.075, 1.27, zc + 0.062), FAB, 0.004))
        fab.append(K.gbox("flap", (cx + sx * 0.13 - 0.08, 1.255, zc + 0.05), (cx + sx * 0.13 + 0.08, 1.30, zc + 0.066), FAB, 0.003))
    fab.append(K.gbox("placket", (cx - 0.02, 0.98, zc + 0.05), (cx + 0.02, 1.80, zc + 0.062), FAB, 0.002))
    for y in (1.72, 1.55, 1.38, 1.21):
        steel.append(K.gcyl("button", 0.012, 0.0, 0.007, base=(cx + 0.045, y, zc + 0.062), axis=(0, 0, 1), segments=8, mat=STEEL))
    return fab, wood, steel


def rucksack(top_y):
    """A canvas rucksack standing on the NW crate with a bedroll on top."""
    fab, steel = [], []
    cx, cz = 4.93, -3.745
    h = 0.44
    y = top_y + h / 2
    fab.append(E.rrect_box("pack", 0.31, h, 0.19, 0.05, (cx, y, cz), FAB, n=3, bevel=0.01))
    fab.append(E.rrect_box("pack_flap", 0.32, 0.13, 0.205, 0.05, (cx, top_y + h - 0.055, cz + 0.004), FAB, n=3, bevel=0.008))
    for sx in (-1, 1):
        fab.append(E.rrect_box("pack_side", 0.07, 0.24, 0.15, 0.025, (cx + sx * 0.19, top_y + 0.17, cz), FAB, n=2, bevel=0.006))
        fab.append(K.gbox("strap", (cx + sx * 0.075 - 0.014, top_y + 0.04, cz + 0.098), (cx + sx * 0.075 + 0.014, top_y + h - 0.03, cz + 0.107),
                          FAB, 0.002))
        steel.append(K.gbox("buckle", (cx + sx * 0.075 - 0.014, top_y + 0.20, cz + 0.107), (cx + sx * 0.075 + 0.014, top_y + 0.235, cz + 0.112),
                            STEEL, 0.001))
    roll = K.glathe("bedroll", [(0.0, -0.17), (0.062, -0.17), (0.066, -0.15), (0.066, 0.15), (0.062, 0.17), (0.0, 0.17)],
                    (cx, top_y + h + 0.062, cz), (1, 0, 0), 12, FAB, smooth=60.0)
    fab.append(roll)
    for dx in (-0.1, 0.1):
        steel.append(D.ring("roll_band", 0.064, 0.070, dx - 0.007, dx + 0.007, (cx, top_y + h + 0.062, cz), (1, 0, 0), 12, STEEL))
    return fab, steel


# ====================================================================== battery rig, cables
def battery(cx, cz, y0, L_=0.27, W=0.17, H=0.19):
    steel = [K.gbox("bat", (cx - L_ / 2, y0, cz - W / 2), (cx + L_ / 2, y0 + H, cz + W / 2), STEEL, 0.005)]
    steel.append(K.gbox("bat_lid", (cx - L_ / 2 + 0.012, y0 + H, cz - W / 2 + 0.012), (cx + L_ / 2 - 0.012, y0 + H + 0.008, cz + W / 2 - 0.012),
                        STEEL, 0.002))
    for dx in (-0.045, 0.0, 0.045):
        steel.append(K.gcyl("bat_cap", 0.0125, 0.0, 0.006, base=(cx + dx, y0 + H + 0.008, cz), axis=(0, 1, 0), segments=8, mat=STEEL))
    for sx in (-1, 1):
        steel.append(K.gcyl("bat_post", 0.0115, 0.0, 0.03, base=(cx + sx * 0.098, y0 + H, cz), axis=(0, 1, 0), segments=8, mat=STEEL,
                            chamfer=0.003))
    steel.append(K.gbox("bat_strap", (cx - 0.014, y0 + 0.14, cz - W / 2 - 0.004), (cx + 0.014, y0 + H - 0.012, cz + W / 2 + 0.004), STEEL, 0.0))
    return steel


def rig():
    wood, steel = [], []
    x0, x1, z0, z1 = RIG
    wood += E.plank_crate("rig_", x0, x1, z0, z1, RIG_H, mat=WOOD, lid="solid", n_slats=3, seed=21)
    cx = (x0 + x1) / 2
    zs = (-3.04, -2.85, -2.66)
    top = RIG_H
    for z in zs:
        steel += battery(cx, z, top)
    ty = top + 0.19 + 0.032                                    # terminal tops
    # jumpers between neighbouring batteries (the east posts, then the west posts)
    for sx in (1, -1):
        px = cx + sx * 0.098
        for a, b in ((zs[0], zs[1]), (zs[1], zs[2])):
            if sx == 1 and a == zs[1]:
                continue
            steel.append(D.tube("jumper", [(px, ty, a), (px, ty + 0.03, (a + b) / 2), (px, ty, b)], 0.0055, sides=5, mat=STEEL,
                                fillet=0.02))
    # the two supply cables: from the end batteries' free posts over the crate edge, along the floor, to the table
    def cable(start, via, end, r=0.0085):
        pts = [start] + via + [end]
        return D.tube("cable", pts, r, sides=5, mat=STEEL, fillet=0.06)
    px_w = cx - 0.098
    steel.append(cable((px_w, ty, zs[0]), [(px_w - 0.12, ty + 0.06, zs[0] - 0.02), (x0 - 0.06, 0.30, zs[0] + 0.12), (x0 - 0.08, 0.008, zs[0] + 0.5),
                                           (6.6, 0.008, -2.30), (6.0, 0.008, -2.22), (5.62, 0.008, -2.05), (5.52, 0.008, -1.86),
                                           (5.44, 0.20, -1.78), (5.40, 0.60, -1.76), (5.34, TABLE_TOP + 0.008, -1.74)],
                       (5.20, TABLE_TOP + 0.008, -1.74)))
    steel.append(cable((px_w, ty, zs[2]), [(px_w - 0.10, ty + 0.05, zs[2] + 0.03), (x0 - 0.07, 0.30, zs[2] - 0.04), (x0 - 0.10, 0.008, zs[2] + 0.30),
                                           (6.5, 0.008, -2.10), (5.95, 0.008, -2.02), (5.60, 0.008, -1.80), (5.50, 0.008, -1.62),
                                           (5.43, 0.20, -1.55), (5.40, 0.60, -1.53), (5.33, TABLE_TOP + 0.008, -1.52)],
                       (5.16, TABLE_TOP + 0.008, -1.50)))
    return wood, steel


# ====================================================================== folding table
def table():
    wood, steel = [], []
    x0, x1, z0, z1 = TABLE
    top = TABLE_TOP
    wood.append(K.gbox("table_top", (x0, top - 0.026, z0), (x1, top, z1), WOOD, 0.003))
    # steel rim round the underside + crossed legs
    for (a, b) in (((x0 + 0.01, z0 + 0.01), (x1 - 0.01, z0 + 0.03)), ((x0 + 0.01, z1 - 0.03), (x1 - 0.01, z1 - 0.01))):
        steel.append(K.gbox("rim", (a[0], top - 0.05, a[1]), (b[0], top - 0.026, b[1]), STEEL, 0.001))
    for (a, b) in (((x0 + 0.01, z0 + 0.03), (x0 + 0.03, z1 - 0.03)), ((x1 - 0.03, z0 + 0.03), (x1 - 0.01, z1 - 0.03))):
        steel.append(K.gbox("rim", (a[0], top - 0.05, a[1]), (b[0], top - 0.026, b[1]), STEEL, 0.001))
    zl0, zl1 = z0 + 0.04, z1 - 0.04
    for xe in (x0 + 0.06, x1 - 0.06):
        steel.append(D.rod("leg", (xe, 0.0, zl0), (xe, top - 0.05, zl1), 0.0125, segs=6, mat=STEEL))
        steel.append(D.rod("leg", (xe, 0.0, zl1), (xe, top - 0.05, zl0), 0.0125, segs=6, mat=STEEL))
        for z in (zl0, zl1):
            steel.append(K.gbox("foot", (xe - 0.025, 0.0, z - 0.02), (xe + 0.025, 0.012, z + 0.02), STEEL, 0.002))
    zm = (z0 + z1) / 2
    steel.append(D.rod("rail", (x0 + 0.06, 0.33, zm), (x1 - 0.06, 0.33, zm), 0.009, segs=6, mat=STEEL))
    return wood, steel


# ====================================================================== dressing
def small_things():
    steel, paper = [], []
    # crate stack (B): crate with a smaller crate on it carrying thermos, mug and tape boxes
    wood = E.plank_crate("cb_", *CRATE_B, 0.30, mat=WOOD, lid="slats", n_slats=3, seed=31)
    cx, cz = (CRATE_B[0] + CRATE_B[1]) / 2, (CRATE_B[2] + CRATE_B[3]) / 2
    ty = 0.30
    # thermos (lathe) with its cup, at the crate's north-east
    th = K.glathe("thermos", [(0.0, 0.0), (0.034, 0.0), (0.038, 0.012), (0.038, 0.235), (0.034, 0.255), (0.040, 0.262), (0.040, 0.305),
                              (0.032, 0.312), (0.0, 0.312)], (cx + 0.10, ty, cz - 0.08), (0, 1, 0), 14, STEEL, smooth=50.0)
    steel.append(th)
    steel.append(K.gbox("thermos_strap", (cx + 0.10 - 0.002, ty + 0.05, cz - 0.08 + 0.037), (cx + 0.10 + 0.002, ty + 0.25, cz - 0.08 + 0.041),
                        STEEL, 0.0))
    # mug: an open cup with a handle
    mug = K.glathe("mug", [(0.0, 0.0), (0.036, 0.0), (0.038, 0.004), (0.040, 0.085), (0.0372, 0.085), (0.0355, 0.008), (0.0, 0.008)],
                   (cx - 0.07, ty, cz + 0.10), (0, 1, 0), 14, STEEL, smooth=50.0)
    steel.append(mug)
    steel.append(D.tube("mug_handle", [(cx - 0.07 + 0.039, ty + 0.072, cz + 0.10), (cx - 0.07 + 0.066, ty + 0.072, cz + 0.10),
                                       (cx - 0.07 + 0.066, ty + 0.025, cz + 0.10), (cx - 0.07 + 0.038, ty + 0.025, cz + 0.10)], 0.0055,
                        sides=5, mat=STEEL, fillet=0.012))
    # four tape boxes in a leaning stack, plus a reel on top
    base = ty
    for k, (rot, dx, dz) in enumerate(((6, 0.0, 0.0), (-9, 0.006, -0.004), (14, -0.004, 0.006), (-4, 0.003, 0.0))):
        o = K.gbox("tapebox", (-0.054, 0.0, -0.054), (0.054, 0.028, 0.054), PAPER, 0.002)
        o.data.transform(Matrix.Translation((cx - 0.07 + dx, base + k * 0.028, cz - 0.09 + dz)) @ Matrix.Rotation(math.radians(rot), 4, "Y"))
        paper.append(o)
    reel = K.glathe("reel", [(0.0, 0.0), (0.045, 0.0), (0.045, 0.003), (0.012, 0.003), (0.012, 0.012), (0.045, 0.012), (0.045, 0.015),
                             (0.0, 0.015)], (cx - 0.07, base + 4 * 0.028, cz - 0.09), (0, 1, 0), 14, STEEL, smooth=40.0)
    steel.append(reel)
    # torch (flashlight) lying on the table's east end, along z
    tx, tz = 5.30, -1.47
    ty0 = TABLE_TOP + 0.024
    tor = K.glathe("torch", [(0.0, 0.0), (0.019, 0.0), (0.022, 0.012), (0.022, 0.12), (0.026, 0.135), (0.036, 0.185), (0.037, 0.205),
                             (0.030, 0.205), (0.0, 0.205)], (tx, ty0, tz), (0, 0, 1), 14, STEEL, smooth=50.0)
    steel.append(tor)
    steel.append(K.gbox("torch_sw", (tx - 0.008, ty0 + 0.02, tz + 0.05), (tx + 0.008, ty0 + 0.028, tz + 0.10), STEEL, 0.002))
    return wood, steel, paper


def mat_rug():
    return [K.gbox("rug", (5.55, 0.0006, -3.26), (7.00, 0.009, -2.62), FAB, 0.002)]


def sheets():
    paper, steel = [], []
    spec = [  # (centre, normal, tilt, w, h)
        ((6.20, 1.50, WALL_N + 0.002), (0, 0, 1), 4, 0.21, 0.30), ((6.50, 1.62, WALL_N + 0.002), (0, 0, 1), -7, 0.21, 0.30),
        ((6.80, 1.46, WALL_N + 0.002), (0, 0, 1), 3, 0.21, 0.30), ((6.40, 1.28, WALL_N + 0.002), (0, 0, 1), -3, 0.30, 0.21),
        ((7.15, 1.60, WALL_N + 0.002), (0, 0, 1), 9, 0.21, 0.30),
        ((WALL_W + 0.002, 1.55, -1.45), (1, 0, 0), 5, 0.21, 0.30), ((WALL_W + 0.002, 1.35, -1.72), (1, 0, 0), -8, 0.21, 0.30),
        ((WALL_W + 0.002, 1.65, -1.80), (1, 0, 0), 2, 0.30, 0.21),
        ((4.80, 1.52, WALL_S - 0.002), (0, 0, -1), -5, 0.21, 0.30), ((5.28, 1.40, WALL_S - 0.002), (0, 0, -1), 6, 0.21, 0.30),
        ((5.25, 1.70, WALL_S - 0.002), (0, 0, -1), -2, 0.30, 0.21), ((4.78, 1.22, WALL_S - 0.002), (0, 0, -1), 8, 0.30, 0.21),
    ]
    for k, (c, n, tilt, w, h) in enumerate(spec):
        o, p = E.pinned_sheet(f"sheet{k}", c, n, w, h, tilt)
        paper.append(o)
        steel.append(p)
    return paper, steel


def lamp_fittings():
    steel = []
    bx, by, bz = BULB_C
    steel.append(K.gcyl("rose", 0.032, 2.875, 2.90, base=(bx, 0.0, bz), axis=(0, 1, 0), segments=10, mat=STEEL, chamfer=0.003))
    steel.append(D.rod("flex", (bx, 2.88, bz), (bx, 2.64, bz), 0.0035, segs=5, mat=STEEL))
    steel.append(K.glathe("holder", [(0.0, 0.0), (0.013, 0.0), (0.017, 0.025), (0.017, 0.055), (0.012, 0.07), (0.0, 0.07)],
                          (bx, 2.58, bz), (0, 1, 0), 10, STEEL, smooth=50.0))
    return steel


def bulb():
    bx, by, bz = BULB_C
    # profile bottom -> top in local y around the origin at the bulb centre: a globe r 0.030 with a neck up to the holder
    prof = [(0.0, -0.034), (0.012, -0.031), (0.022, -0.022), (0.029, -0.008), (0.030, 0.004), (0.026, 0.017), (0.016, 0.028),
            (0.011, 0.036), (0.0105, 0.045), (0.0, 0.045)]
    o = K.glathe("camp_bulb", prof, (bx, by, bz), (0, 1, 0), 12, PAPER, smooth=80.0)
    return o


# ====================================================================== build
def build():
    M.reset_scene()
    E.ensure_materials()
    fab, wood, steel, paper = [], [], [], []
    f, w = cot()
    fab += f
    wood += w
    f, w, s = coat()
    fab += f
    wood += w
    steel += s
    wood += E.plank_crate("cd_", *CRATE_D, 0.28, mat=WOOD, lid="slats", n_slats=3, seed=41)
    f, s = rucksack(0.28)
    fab += f
    steel += s
    w, s = rig()
    wood += w
    steel += s
    w, s = table()
    wood += w
    steel += s
    w, s, p = small_things()
    wood += w
    steel += s
    paper += p
    fab += mat_rug()
    p, s = sheets()
    paper += p
    steel += s
    steel += lamp_fittings()
    body = K.part(NAME, fab + wood + steel + paper, pivot=(0.0, 0.0, 0.0))
    bulb_o = bulb()
    K.part("camp_bulb", [bulb_o], pivot=BULB_C)
    light = K.empty("camp_light", CAMP_LIGHT)
    K.to_blender()
    E.finalize()
    return dict(body=body, bulb=bpy.data.objects["camp_bulb"], light=light)


def verify(path):
    req = [NAME, "camp_bulb", "camp_light"]
    errs = E.verify(path, required=req, identity=req, expect={NAME: (0, 0, 0), "camp_bulb": BULB_C, "camp_light": CAMP_LIGHT},
                    parents={n: None for n in req}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = E.bounds([NAME])
    print(f"{E.TAG} {NAME} bounds {tuple(round(c, 3) for c in lo)} .. {tuple(round(c, 3) for c in hi)} (camp x 4.5..7.6, z -4.0..-1.2, y < 2.9)")
    if lo[0] < 4.5 or hi[0] > 7.6 or lo[2] < -4.0 or hi[2] > -1.2 or hi[1] > 2.9:
        errs.append("outside the camp")
    return errs


# ====================================================================== QA
def qa(parts, args):
    E.qa_begin()
    E.camp_room(extra=[("field_recorder", E.RECORDER_POS, E.RECORDER_YAW, "qa_fr_"), ("oscillograph", E.OSC_POS, E.OSC_YAW, "qa_os_"),
                       ("crystal_shutter", E.SHUTTER_POS, E.SHUTTER_YAW, "qa_cs_")])
    K.override(parts["bulb"], K.glow("qa_bulb", "FFD9A8", 7.0))
    osc = next((o for o in bpy.data.objects if o.name.startswith("qa_os_osc_screen") and o.type == "MESH"), None)
    if osc is not None:
        E.preview(osc, "osc_screen.png", emissive=True, strength=1.5)
    # 1 the camp root view (§2)
    if E.want(args, "1"):
        C = E.view("camp")
        E.camp_lights(C[0], fill=5.0)
        E.shoot(NAME, C[0], C[1], C[2])
    # 2 hero: the table and the battery cables from the doorway side, low
    if E.want(args, "2"):
        cam = (6.45, 1.35, -1.55)
        E.camp_lights(cam, fill=8.0)
        E.shoot(NAME + "_2", cam, (5.4, 0.55, -2.3), 55)
    # 3 hero: the cot, the coat and the rucksack corner from the table side
    if E.want(args, "3"):
        cam = (5.05, 1.45, -2.25)
        E.camp_lights(cam, fill=8.0)
        E.shoot(NAME + "_3", cam, (6.0, 0.85, -3.6), 58)
    # 4 the shutter view (§2): nothing may stand in the sight line to the shutter
    if E.want(args, "4"):
        S = E.view("shutter")
        E.camp_lights(S[0], fill=5.0)
        E.shoot(NAME + "_4", S[0], S[1], S[2])
    # 5 the recorder view (§2)
    if E.want(args, "5"):
        R = E.view("recorder")
        E.camp_lights(R[0], fill=6.0)
        E.shoot(NAME + "_5", R[0], R[1], R[2])


def main():
    args = M.main_guard()
    parts = build()
    E.report(NAME)
    path = E.export(NAME)
    errs = verify(path)
    print(f"{E.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
