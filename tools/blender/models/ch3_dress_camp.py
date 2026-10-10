"""ch3_dress_camp.glb — set-dressing of Leyla's 1998 camp (group K): what a woman who lived 45 years ago under the
Institute left on her camp table and walls, so the room reads as inhabited and abandoned instead of a clean tiled box.
Nothing here is interactive (no colliders); the room draws it only in the camp views.

ROOM-COORDINATE model: origin = the world origin, built in place in the camp x 4.5 .. 7.6, z -4.0 .. -1.2, y 0 .. 2.9
(walls: north z -3.965, west x 4.535, south z -1.203, east x 7.6). Everything sits clear of the interactive parts
(recorder, oscillograph, shutter frame, crystals) and of the sight lines of the `camp`, `shutter` and `recorder` views.

  ch3_dress_camp   (static) ONE mesh, a surface per material (steel, painted steel, brass, wood, paper, leather, wool, red
                   cord, glass, flame, crimson enamel, and the shared grime atlas M_Dress_Grime):
      crate table       a plank crate beside the cot, with the storm lantern (the camp's key light), a stack of notebooks,
                        an open notebook and a pencil, a tin mug
      wool blanket      on the sleeping bag, one edge hanging over the cot rail
      kerosene heater   on the floor at the cot's head, mica window glowing
      spare battery     a steel pack with clamp leads, beside the table's cable run
      maps and cords    survey maps pinned over the tiles (north, west and south walls) with red cord tied between the
                        tacks, notebook pages and a photo
      wall services     a pipe and a conduit run along the walls, a junction box, a valve, a fire bucket on a hook with
                        its pictogram, a hazard-bolt sign, a no-entry sign
      grime atlas       baseboard dirt, ceiling-line soot, damp stains, rust drips, streaks, cracks, missing tiles, floor
                        grime, the hazard stripe in front of the shutter
  camp_lamp_flame  empty at the lantern's flame: the key light of the camp (the room puts an omni there)

    blender -b --factory-startup -P tools/blender/models/ch3_dress_camp.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ch3_dress_lib as X  # noqa: E402
from ch3_dress_lib import K, D, E, M, bpy, Matrix, Vector  # noqa: E402

NAME = "ch3_dress_camp"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 9000, 14, 14
WALL_N, WALL_W, WALL_S, WALL_E = -3.965, 4.535, -1.203, 7.6
CT = (6.34, 6.86, -3.24, -2.80)          # the crate table
CT_H = 0.42
LAMP = (6.49, CT_H, -3.03)
FLAME_Y = 0.115                          # flame centre above the lantern base
HEATER = (5.60, 0.0, -3.06)
PACK = (5.84, 0.0, -1.42)

WALLS = {   # name: (normal, point(a, y))
    "N": ((0, 0, 1), lambda a, y: (a, y, WALL_N)),
    "S": ((0, 0, -1), lambda a, y: (a, y, WALL_S)),
    "W": ((1, 0, 0), lambda a, y: (WALL_W, y, a)),
    "E": ((-1, 0, 0), lambda a, y: (WALL_E, y, a)),
}


def place(objs, matrix):
    for o in objs:
        o.data.transform(matrix)
    return objs


def at(x, y, z, rot_y=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot_y), 4, "Y")


# ====================================================================== crate table, lantern, notebooks
def crate_table():
    wood = E.plank_crate("ct_", *CT, CT_H, mat=X.WOOD, lid="solid", n_slats=3, seed=61)
    # a dark ring where a hot mug stood, a rope-handle notch: the crate is a table now
    wood.append(K.gbox("ct_brace", (CT[0] + 0.02, 0.06, CT[2] - 0.004), (CT[1] - 0.02, 0.085, CT[2] + 0.012), X.WOOD, 0.0))
    return wood


def lantern():
    """A tin storm lantern: brass tank, glass globe, flame, cap, bail. Origin = the base centre."""
    lx, ly, lz = LAMP
    brass, glass, flame = [], [], []
    tank = [(0.0, 0.0), (0.056, 0.0), (0.060, 0.008), (0.061, 0.040), (0.050, 0.056), (0.036, 0.062), (0.034, 0.078), (0.0, 0.078)]
    brass.append(K.glathe("lamp_tank", tank, (lx, ly, lz), (0, 1, 0), 14, X.BRASS, smooth=60.0))
    glass.append(K.glathe("lamp_globe", [(0.033, 0.078), (0.050, 0.104), (0.054, 0.136), (0.046, 0.180), (0.032, 0.214), (0.026, 0.232)],
                          (lx, ly, lz), (0, 1, 0), 14, X.GLASS, smooth=60.0, cap_bottom=False, cap_top=False))
    brass.append(K.glathe("lamp_cap", [(0.026, 0.230), (0.034, 0.236), (0.030, 0.252), (0.014, 0.264), (0.0, 0.266)],
                          (lx, ly, lz), (0, 1, 0), 12, X.BRASS, smooth=60.0))
    flame.append(K.glathe("lamp_flame", [(0.0, 0.084), (0.006, 0.090), (0.011, 0.104), (0.008, 0.124), (0.003, 0.140), (0.0, 0.150)],
                          (lx, ly, lz), (0, 1, 0), 8, X.FLAME, smooth=80.0))
    brass.append(K.gcyl("lamp_wick", 0.011, 0.078, 0.092, base=(lx, ly, lz), axis=(0, 1, 0), segments=8, mat=X.BRASS))
    brass.append(K.gcyl("lamp_knob", 0.011, 0.0, 0.012, base=(lx + 0.068, ly + 0.03, lz), axis=(1, 0, 0), segments=8, mat=X.BRASS))
    # bail handle, folded down to the side
    brass.append(D.tube("lamp_bail", [(lx - 0.052, ly + 0.050, lz), (lx - 0.060, ly + 0.230, lz), (lx + 0.060, ly + 0.230, lz),
                                     (lx + 0.052, ly + 0.050, lz)], 0.0028, sides=4, mat=X.BRASS, fillet=0.03))
    return brass, glass, flame


def notebook(cx, y0, cz, rot, w=0.19, d=0.135, t=0.024):
    """A cloth-bound notebook, spine to -x: two boards, a spine, the page block."""
    cov, pag = [], []
    cov.append(K.gbox("nb_bot", (-w / 2, 0.0, -d / 2), (w / 2, 0.004, d / 2), X.LEATHER, 0.0015))
    cov.append(K.gbox("nb_top", (-w / 2, t - 0.004, -d / 2), (w / 2, t, d / 2), X.LEATHER, 0.0015))
    cov.append(K.gbox("nb_spine", (-w / 2, 0.0, -d / 2), (-w / 2 + 0.008, t, d / 2), X.LEATHER, 0.002))
    pag.append(K.gbox("nb_pages", (-w / 2 + 0.008, 0.004, -d / 2 + 0.004), (w / 2 - 0.004, t - 0.004, d / 2 - 0.004), X.PAPER, 0.0))
    place(cov + pag, at(cx, y0, cz, rot))
    return cov, pag


def table_things():
    steel, leather, paper, wood = [], [], [], []
    for k, (dx, dz, rot) in enumerate(((0.0, 0.0, 6.0), (0.012, 0.004, -11.0), (-0.006, -0.006, 17.0))):
        c, p = notebook(6.735 + dx, CT_H + k * 0.024, -3.115 + dz, rot)
        leather += c
        paper += p
    # an open notebook, a pencil
    leather.append(K.gbox("onb_cover", (-0.15, 0.0, -0.10), (0.15, 0.006, 0.10), X.LEATHER, 0.002))
    paper.append(K.gbox("onb_l", (-0.14, 0.006, -0.09), (-0.004, 0.014, 0.09), X.PAPER, 0.0))
    paper.append(K.gbox("onb_r", (0.004, 0.006, -0.09), (0.14, 0.012, 0.09), X.PAPER, 0.0))
    place(leather[-1:] + paper[-2:], at(6.585, CT_H, -2.905, -14.0))
    pen = D.rod("pencil", (6.52, CT_H + 0.016, -2.835), (6.69, CT_H + 0.016, -2.80), 0.0036, segs=5, mat=X.WOOD)
    wood.append(pen)
    # a tin mug, handle to the east
    mx, mz = 6.785, -2.895
    steel.append(K.glathe("tmug", [(0.0, 0.0), (0.034, 0.0), (0.037, 0.004), (0.039, 0.080), (0.0362, 0.080), (0.0345, 0.008), (0.0, 0.008)],
                          (mx, CT_H, mz), (0, 1, 0), 14, X.STEEL, smooth=50.0))
    steel.append(D.tube("tmug_h", [(mx + 0.038, CT_H + 0.066, mz), (mx + 0.064, CT_H + 0.066, mz), (mx + 0.064, CT_H + 0.022, mz),
                                  (mx + 0.037, CT_H + 0.022, mz)], 0.0052, sides=5, mat=X.STEEL, fillet=0.012))
    return steel, leather, paper, wood


# ====================================================================== blanket, heater, battery pack
def blanket():
    wool = []
    b = E.rrect_box("wool_a", 0.96, 0.05, 0.46, 0.05, (6.42, 0.615, -3.625), X.WOOL, n=3, bevel=0.014)
    wool.append(X.jit(b, 0.004, 71))
    f = E.rrect_box("wool_b", 0.62, 0.035, 0.36, 0.04, (6.56, 0.66, -3.62), X.WOOL, n=3, bevel=0.012)
    f.data.transform(Matrix.Translation((6.56, 0, -3.62)) @ Matrix.Rotation(math.radians(8), 4, "Y") @ Matrix.Translation((-6.56, 0, 3.62)))
    wool.append(X.jit(f, 0.003, 72))
    hang = K.gbox("wool_hang", (6.02, 0.19, -3.336), (6.64, 0.47, -3.308), X.WOOL, 0.01, 2)
    wool.append(X.jit(hang, 0.003, 73))
    return wool


def heater():
    """A paraffin heater: tank, chimney with a mica window that glows, ribs, cap and handle."""
    hx, hy, hz = HEATER
    steel, paint, flame = [], [], []
    tank = [(0.0, 0.0), (0.118, 0.0), (0.134, 0.016), (0.134, 0.170), (0.108, 0.200), (0.100, 0.224), (0.0, 0.224)]
    steel.append(K.glathe("ht_tank", tank, (hx, hy, hz), (0, 1, 0), 16, X.STEEL, smooth=60.0))
    paint.append(K.glathe("ht_lo", [(0.100, 0.224), (0.100, 0.290)], (hx, hy, hz), (0, 1, 0), 16, X.PAINT, smooth=60.0, cap_bottom=False, cap_top=False))
    paint.append(K.glathe("ht_hi", [(0.100, 0.392), (0.100, 0.462)], (hx, hy, hz), (0, 1, 0), 16, X.PAINT, smooth=60.0, cap_bottom=False, cap_top=False))
    flame.append(K.glathe("ht_mica", [(0.099, 0.290), (0.099, 0.392)], (hx, hy, hz), (0, 1, 0), 16, X.FLAME, smooth=60.0, cap_bottom=False, cap_top=False))
    for k in range(8):
        a = 2 * math.pi * k / 8
        steel.append(K.gbox("ht_rib", (-0.006, 0.224, -0.006), (0.006, 0.462, 0.006), X.STEEL, 0.0))
        steel[-1].data.transform(Matrix.Translation((hx + 0.108 * math.cos(a), hy, hz + 0.108 * math.sin(a))))
    steel.append(K.glathe("ht_cap", [(0.104, 0.462), (0.118, 0.470), (0.118, 0.486), (0.07, 0.504), (0.0, 0.508)],
                          (hx, hy, hz), (0, 1, 0), 16, X.STEEL, smooth=60.0))
    steel.append(D.tube("ht_handle", [(hx - 0.075, 0.50, hz), (hx - 0.070, 0.585, hz), (hx + 0.070, 0.585, hz), (hx + 0.075, 0.50, hz)],
                        0.0055, sides=5, mat=X.STEEL, fillet=0.03))
    return steel, paint, flame


def battery_pack():
    px, py, pz = PACK
    steel, cord = [], []
    body = [K.gbox("bp_body", (-0.12, 0.0, -0.075), (0.12, 0.150, 0.075), X.STEEL, 0.006),
            K.gbox("bp_lid", (-0.115, 0.150, -0.07), (0.115, 0.158, 0.07), X.STEEL, 0.003),
            K.gbox("bp_band", (-0.012, 0.0, -0.079), (0.012, 0.150, 0.079), X.STEEL, 0.0)]
    steel += body
    for sx in (-1, 1):
        steel.append(K.gcyl("bp_post", 0.011, 0.0, 0.026, base=(sx * 0.082, 0.158, 0.0), axis=(0, 1, 0), segments=8, mat=X.BRASS, chamfer=0.003))
    steel.append(D.tube("bp_handle", [(-0.07, 0.158, 0.0), (-0.07, 0.205, 0.0), (0.07, 0.205, 0.0), (0.07, 0.158, 0.0)], 0.006, sides=5,
                        mat=X.STEEL, fillet=0.02))
    place(steel, at(px, py, pz, 24.0))
    # two leads (red cord, black rubber) from the posts down to the floor and over to the table's cable run
    def w(x, y, z):
        v = at(px, py, pz, 24.0) @ Vector((x, y, z))
        return (v.x, v.y, v.z)
    red = D.tube("bp_red", [w(0.082, 0.184, 0.0), w(0.12, 0.17, 0.06), w(0.15, 0.05, 0.12), (5.62, 0.01, -1.62), (5.50, 0.01, -1.72)],
                 0.0075, sides=5, mat=X.STRING, fillet=0.05)
    blk = D.tube("bp_black", [w(-0.082, 0.184, 0.0), w(-0.12, 0.17, -0.06), w(-0.15, 0.05, -0.1), (5.58, 0.01, -1.60), (5.47, 0.01, -1.50)],
                 0.0075, sides=5, mat=X.RUBBER, fillet=0.05)
    return steel, [red], [blk]


# ====================================================================== maps, cords and pins
SHEETS = [  # the blank sheets of leyla_camp (centre, normal, tilt, w, h): where their tacks are
    ((6.20, 1.50, WALL_N + 0.002), (0, 0, 1), 4, 0.21, 0.30), ((6.50, 1.62, WALL_N + 0.002), (0, 0, 1), -7, 0.21, 0.30),
    ((6.80, 1.46, WALL_N + 0.002), (0, 0, 1), 3, 0.21, 0.30), ((6.40, 1.28, WALL_N + 0.002), (0, 0, 1), -3, 0.30, 0.21),
    ((7.15, 1.60, WALL_N + 0.002), (0, 0, 1), 9, 0.21, 0.30),
    ((WALL_W + 0.002, 1.55, -1.45), (1, 0, 0), 5, 0.21, 0.30), ((WALL_W + 0.002, 1.35, -1.72), (1, 0, 0), -8, 0.21, 0.30),
    ((WALL_W + 0.002, 1.65, -1.74), (1, 0, 0), 2, 0.30, 0.21),
    ((4.80, 1.52, WALL_S - 0.002), (0, 0, -1), -5, 0.21, 0.30), ((5.28, 1.40, WALL_S - 0.002), (0, 0, -1), 6, 0.21, 0.30),
    ((5.25, 1.70, WALL_S - 0.002), (0, 0, -1), -2, 0.30, 0.21), ((4.78, 1.22, WALL_S - 0.002), (0, 0, -1), 8, 0.30, 0.21),
]


def board():
    """Maps and pages pinned over the tiles, with red cord between the tacks (a detective's wall, a field worker's way)."""
    decs, steel, cords = [], [], []
    pins = {}

    def sheet(k):
        c, n, tilt, w, h = SHEETS[k]
        return X.sheet_pin(c, n, tilt, w, h) + Vector(n) * 0.006

    def map_on(cell, wall, a, y, w, h, tilt, key):
        n, pt = WALLS[wall]
        c = Vector(pt(a, y))
        d = X.decal(cell, tuple(c), n, w, h, tilt, off=0.0075, name="map_" + key)
        decs.append(d)
        # tack at the sheet's top centre, the cord is tied there
        nn, ux, vy = X.wall_axes(n, tilt)
        p = c + vy * (h / 2 - 0.018) + nn * 0.0075
        pins[key] = p
        steel.append(X.pin(tuple(p), n))

    # north wall, above the cot: a big contour map, a survey ring sheet, a notebook page
    map_on("map_a", "N", 6.60, 0.99, 0.50, 0.25, -2.0, "n1")
    map_on("map_b", "N", 7.12, 1.00, 0.26, 0.26, 5.0, "n2")
    map_on("page", "N", 5.97, 1.10, 0.20, 0.20, -4.0, "n3")
    map_on("tags", "N", 6.20, 1.86, 0.15, 0.15, 6.0, "n4")
    # west wall, south of the shutter: a floor plan between the blank sheets, a chart
    map_on("map_c", "W", -1.70, 1.00, 0.30, 0.30, 4.0, "w1")
    map_on("chart", "W", -1.46, 1.88, 0.26, 0.26, -6.0, "w2")
    # south wall (plain steel), above the table: the plan, a second map
    map_on("map_a", "S", 5.02, 1.92, 0.34, 0.17, 3.0, "s1")
    map_on("page", "S", 5.40, 1.04, 0.17, 0.17, -7.0, "s2")
    links = [
        (pins["n3"], sheet(0)), (sheet(0), pins["n1"]), (pins["n1"], sheet(2)), (sheet(2), pins["n2"]), (pins["n2"], sheet(4)),
        (sheet(1), pins["n4"]), (pins["n4"], sheet(0)), (pins["n1"], sheet(3)),
        (pins["w1"], sheet(6)), (sheet(6), pins["w2"]), (pins["w2"], sheet(5)), (sheet(5), pins["w1"]),
        (pins["s1"], sheet(8)), (sheet(8), pins["s2"]), (pins["s2"], sheet(9)), (sheet(10), pins["s1"]),
    ]
    for k, (a, b) in enumerate(links):
        cords.append(X.string_line(a, b, 0.0016, sag=0.012 + 0.004 * (k % 3), name="cord"))
    return decs, steel, cords


# ====================================================================== wall services
def services():
    paint, steel, crimson, paper = [], [], [], []
    # high pipe along the west wall (north -> south), turning into the south partition and up through the roof
    y = 2.20
    zN, zS = WALL_N + 0.045, WALL_S - 0.045
    xw = WALL_W + 0.045
    paint.append(D.rod("pipe_w", (xw, y, zN), (xw, y, zS), 0.032, segs=10, mat=X.PAINT))
    paint.append(D.rod("pipe_w_up", (xw, y, zS), (xw, 2.9, zS), 0.032, segs=10, mat=X.PAINT))
    for z in (-3.62, -3.0, -2.2, -1.6):                       # wall clamps
        steel.append(K.gbox("clamp", (WALL_W, y - 0.046, z - 0.014), (WALL_W + 0.042, y + 0.046, z + 0.014), X.STEEL, 0.002))
    # a flanged joint and a valve with a red wheel in the pipe, north of the shutter frame
    zv = -3.44
    for dz in (-0.03, 0.03):
        paint.append(K.gcyl("flange", 0.046, 0.0, 0.014, base=(xw, y, zv + dz), axis=(0, 0, 1), segments=10, mat=X.PAINT, chamfer=0.002))
    paint.append(K.gcyl("valve_body", 0.038, -0.05, 0.05, base=(xw, y, zv), axis=(0, 0, 1), segments=10, mat=X.PAINT))
    steel.append(D.rod("valve_stem", (xw, y, zv), (xw + 0.09, y + 0.0, zv), 0.007, segs=5, mat=X.STEEL))
    crimson.append(D.ring("valve_wheel", 0.040, 0.050, xw + 0.082, xw + 0.092, (0.0, 0.0, 0.0), (1, 0, 0), 14, X.CRIMSON))
    crimson[-1].data.transform(Matrix.Translation((0.0, y, zv)))
    # conduit along the north wall under the roof, with clips and a junction box at the west end
    yc = 2.48
    steel.append(D.rod("conduit_n", (WALL_W + 0.10, yc, WALL_N + 0.026), (WALL_E - 0.02, yc, WALL_N + 0.026), 0.0165, segs=8, mat=X.STEEL))
    for x in (5.05, 5.65, 6.25, 6.85, 7.35):
        steel.append(K.gbox("clip", (x - 0.014, yc - 0.03, WALL_N), (x + 0.014, yc + 0.03, WALL_N + 0.034), X.STEEL, 0.002))
    steel.append(K.gbox("jbox", (WALL_W + 0.02, yc - 0.075, WALL_N), (WALL_W + 0.16, yc + 0.075, WALL_N + 0.07), X.STEEL, 0.004))
    for sx in (-0.045, 0.045):
        for sy in (-0.05, 0.05):
            steel.append(K.rivet("jbox_bolt", 0.006, (WALL_W + 0.09 + sx, yc + sy, WALL_N + 0.07), normal=(0, 0, 1), mat=X.STEEL, segs=6))
    # a drop from the junction box down the north-west corner to a small switch box above the rucksack
    steel.append(D.rod("conduit_drop", (WALL_W + 0.06, yc - 0.075, WALL_N + 0.03), (WALL_W + 0.06, 1.72, WALL_N + 0.03), 0.0165, segs=8, mat=X.STEEL))
    steel.append(K.gbox("sw_box", (WALL_W + 0.025, 1.52, WALL_N), (WALL_W + 0.105, 1.72, WALL_N + 0.045), X.STEEL, 0.003))
    # a fire bucket on a hook, north wall, left of the coat
    bx, bz = 4.96, WALL_N + 0.13
    steel.append(K.gbox("hook_plate", (bx - 0.045, 1.30, WALL_N), (bx + 0.045, 1.42, WALL_N + 0.012), X.STEEL, 0.002))
    steel.append(D.rod("hook", (bx, 1.38, WALL_N + 0.01), (bx, 1.38, WALL_N + 0.075), 0.007, segs=5, mat=X.STEEL))
    crimson.append(K.glathe("bucket", [(0.0, 0.0), (0.085, 0.0), (0.098, 0.010), (0.128, 0.255), (0.0, 0.255)],
                            (bx, 1.07, bz), (0, 1, 0), 16, X.CRIMSON, smooth=60.0))
    crimson.append(K.glathe("bucket_rim", [(0.124, 0.238), (0.134, 0.246), (0.134, 0.262), (0.122, 0.266), (0.118, 0.250)],
                            (bx, 1.07, bz), (0, 1, 0), 16, X.CRIMSON, smooth=60.0, cap_bottom=False, cap_top=False))
    paper.append(K.glathe("bucket_sand", [(0.0, 0.241), (0.118, 0.241)], (bx, 1.07, bz), (0, 1, 0), 16, X.PAPER, smooth=80.0,
                          cap_bottom=False, cap_top=False))
    steel.append(D.tube("bucket_bail", [(bx - 0.125, 1.07 + 0.258, bz), (bx - 0.05, 1.07 + 0.36, bz - 0.03), (bx + 0.05, 1.07 + 0.36, bz - 0.03),
                                       (bx + 0.125, 1.07 + 0.258, bz)], 0.0035, sides=4, mat=X.STEEL, fillet=0.03))
    return paint, steel, crimson, paper


# ====================================================================== the dusty hand cart
CART = (6.42, 0.0, -2.12)
CART_YAW = 12.0


def cart():
    """A flat-bed hand cart left in the camp: plank deck on a steel frame, four casters, a tubular handle, a canvas-covered
    load with a coil of cable hung on the handle. Local frame: x along the cart, z across, handle at -x."""
    wood, steel, rub, wool, fab = [], [], [], [], []
    L_, W_, deck = 0.78, 0.46, 0.31
    for k in range(5):
        z0 = -W_ / 2 + k * W_ / 5
        wood.append(K.gbox("deck", (-L_ / 2, deck, z0 + 0.004), (L_ / 2, deck + 0.032, z0 + W_ / 5 - 0.004), X.WOOD, 0.002))
    for sz in (-1, 1):
        steel.append(K.gbox("cart_rail", (-L_ / 2 + 0.02, deck - 0.05, sz * (W_ / 2 - 0.03) - 0.016), (L_ / 2 - 0.02, deck, sz * (W_ / 2 - 0.03) + 0.016), X.STEEL, 0.002))
    for sx in (-1, 1):
        steel.append(K.gbox("cart_cross", (sx * (L_ / 2 - 0.07) - 0.016, deck - 0.05, -W_ / 2 + 0.03), (sx * (L_ / 2 - 0.07) + 0.016, deck, W_ / 2 - 0.03), X.STEEL, 0.002))
        for sz in (-1, 1):
            cx, cz = sx * (L_ / 2 - 0.07), sz * (W_ / 2 - 0.05)
            steel.append(K.gbox("fork", (cx - 0.012, 0.075, cz - 0.02), (cx + 0.012, deck - 0.05, cz + 0.02), X.STEEL, 0.001))
            rub.append(K.gcyl("caster", 0.045, -0.014, 0.014, base=(cx, 0.047, cz), axis=(0, 0, 1), segments=10, mat=X.RUBBER, chamfer=0.003))
    for sz in (-1, 1):
        steel.append(D.tube("cart_handle_leg", [(-L_ / 2 + 0.03, deck, sz * (W_ / 2 - 0.05)), (-L_ / 2 - 0.10, deck + 0.40, sz * (W_ / 2 - 0.06)),
                                                 (-L_ / 2 - 0.16, deck + 0.64, sz * (W_ / 2 - 0.06))], 0.0105, sides=6, mat=X.STEEL, fillet=0.0))
    steel.append(D.rod("cart_handle", (-L_ / 2 - 0.16, deck + 0.64, -W_ / 2 + 0.04), (-L_ / 2 - 0.16, deck + 0.64, W_ / 2 - 0.04), 0.0115, segs=8, mat=X.STEEL))
    # the load: a crate under a canvas, a roll of cable on the handle
    load = E.rrect_box("cart_load", 0.46, 0.32, 0.34, 0.04, (0.12, deck + 0.032 + 0.16, 0.0), X.WOOL, n=3, bevel=0.02)
    fab.append(E.jitter(load, 0.006, 91) or load)
    steel_loop = D.tube("cable_coil", [(-L_ / 2 - 0.16, deck + 0.60, -0.10), (-L_ / 2 - 0.20, deck + 0.50, -0.06), (-L_ / 2 - 0.20, deck + 0.46, 0.04),
                                       (-L_ / 2 - 0.16, deck + 0.50, 0.10), (-L_ / 2 - 0.14, deck + 0.58, 0.04), (-L_ / 2 - 0.16, deck + 0.60, -0.04)],
                         0.0085, sides=5, mat=X.RUBBER, fillet=0.03)
    rub.append(steel_loop)
    for o in wood + steel + rub + fab:
        o.data.transform(at(CART[0], CART[1], CART[2], CART_YAW))
    return wood, steel, rub, fab


# ====================================================================== grime atlas
def grime():
    d = []
    A = X.decal

    def on(cell, wall, a, y, w, h, tilt=0.0, off=0.004, flip=False):
        n, pt = WALLS[wall]
        d.append(A(cell, pt(a, y), n, w, h, tilt, off, flip=flip))

    def floor(cell, x, z, w, h, tilt=0.0, off=0.0035):
        d.append(A(cell, (x, 0.0, z), (0, 1, 0), w, h, tilt, off))

    # ---- north wall (tiles)
    on("grime_top", "N", 5.30, 2.50, 1.7, 0.85)
    on("grime_top", "N", 6.90, 2.52, 1.7, 0.85, flip=True)
    on("baseboard", "N", 5.30, 0.40, 1.7, 0.85)
    on("baseboard", "N", 6.90, 0.40, 1.7, 0.85, flip=True)
    on("damp_a", "N", 6.85, 2.02, 0.80, 0.80, 20.0)
    on("streaks_a", "N", 5.95, 1.50, 0.80, 0.80, 0.0, 0.0045)
    on("rust_a", "N", WALL_W + 0.06, 1.56, 0.34, 0.34, 0.0, 0.005)      # under the switch box
    on("tiles_a", "N", snap_t(5.40), snap_t(0.90, 0.0), 0.60, 0.60)
    on("crack_a", "N", 7.10, 1.60, 0.70, 0.70, 15.0)
    # ---- west wall (tiles; the shutter frame stands in front of z -3.25 .. -1.95)
    on("grime_top", "W", -3.10, 2.50, 1.7, 0.85)
    on("grime_top", "W", -1.75, 2.50, 1.7, 0.85, flip=True)
    on("baseboard", "W", -3.10, 0.40, 1.7, 0.85, flip=True)
    on("baseboard", "W", -1.75, 0.40, 1.7, 0.85)
    on("damp_b", "W", -3.45, 1.78, 0.80, 0.80, -10.0)
    on("streaks_b", "W", -1.40, 1.30, 0.80, 0.80)
    on("tiles_b", "W", snap_t(-1.60), snap_t(0.45, 0.0), 0.60, 0.60)
    on("rust_b", "W", -3.44, 1.88, 0.40, 0.40, 0.0, 0.005)               # under the flanged joint
    on("crack_b", "W", -2.10, 2.50, 0.70, 0.70)
    on("corner", "W", -3.95, 2.78, 0.6, 0.6, 0.0)
    # ---- south partition (cream steel)
    on("grime_top", "S", 5.0, 2.52, 1.7, 0.85)
    on("baseboard", "S", 5.0, 0.40, 1.7, 0.85)
    on("damp_a", "S", 5.10, 2.20, 0.8, 0.8, 200.0)
    on("streaks_a", "S", 5.45, 1.30, 0.7, 0.7)
    on("rust_a", "S", 5.45, 2.55, 0.34, 0.34, 0.0, 0.005)
    on("baseboard", "S", 7.0, 0.40, 1.7, 0.85)
    on("grime_top", "S", 7.0, 2.52, 1.7, 0.85)
    # ---- east wall
    on("grime_top", "E", -3.0, 2.52, 1.7, 0.85)
    on("grime_top", "E", -1.8, 2.52, 1.7, 0.85)
    on("baseboard", "E", -3.0, 0.40, 1.7, 0.85)
    on("damp_b", "E", -2.7, 1.9, 0.9, 0.9)
    # ---- warning marks: a hazard bolt on the tile beside the shutter, a fire pictogram behind the bucket, no-entry above
    on("st_bolt", "W", -3.62, 1.12, 0.20, 0.20, 3.0, 0.0045)
    on("st_noentry", "W", -3.62, 1.58, 0.22, 0.22, 0.0, 0.0045)
    on("st_flame", "N", 4.96, 1.70, 0.20, 0.20, -2.0, 0.0045)
    on("st_pipe", "W", -1.45, 2.08, 0.50, 0.25, 0.0, 0.0045)             # flow chevrons under the pipe
    on("st_valve", "W", -3.44, 1.92, 0.20, 0.10, 0.0, 0.0045)
    # ---- floor: dirt along the walls, damp, the hazard stripe before the shutter, a keep-clear box
    floor("baseboard", 6.05, -3.78, 3.1, 0.62, 180.0)
    floor("baseboard", 4.75, -2.6, 2.9, 0.55, 90.0)
    floor("baseboard", 6.05, -1.42, 3.1, 0.55)
    floor("damp_a", 6.2, -2.35, 1.2, 1.2, 40.0)
    floor("damp_b", 5.35, -3.15, 0.8, 0.8, 100.0)
    floor("corner", 7.4, -1.4, 0.9, 0.9, 0.0)
    floor("st_stripes", 4.86, -2.6, 1.34, 0.30, 90.0, 0.0045)
    floor("st_keepclear", 5.64, -2.60, 0.85, 0.85, 90.0, 0.0045)
    floor("soot", 5.6, -3.06, 0.9, 0.9, 0.0, 0.0038)                     # under the heater
    return d


def snap_t(v, phase=0.0):
    """Snap a wall coordinate to the 0.15 m tile grid."""
    return X.snap(v, X.TILE, phase)


# ====================================================================== build
def build():
    M.reset_scene()
    X.ensure_materials()
    wood = crate_table()
    steel, leather, paper, w2 = table_things()
    wood += w2
    brass, glass, flame = lantern()
    wool = blanket()
    s, paint, f = heater()
    steel += s
    flame += f
    s, red, black = battery_pack()
    steel += s
    cord = red
    steel += black
    dec, s, cords = board()
    steel += s
    cord += cords
    p, s, crimson, pp = services()
    paint += p
    steel += s
    paper += pp
    cw, cs, cr, cf = cart()
    wood += cw
    steel += cs
    steel += cr
    wool += cf
    dec += grime()
    X.clip_quads(dec, (WALL_W + 0.002, 0.0, WALL_N + 0.002), (WALL_E - 0.002, 2.9, WALL_S - 0.002))
    objs = wood + steel + leather + paper + brass + glass + flame + wool + paint + cord + crimson + dec
    X.report_outside(objs, (WALL_W, 0.0, WALL_N), (WALL_E, 2.9, WALL_S))
    body = K.part(NAME, objs, pivot=(0.0, 0.0, 0.0))
    lx, ly, lz = LAMP
    light = K.empty("camp_lamp_flame", (lx, ly + FLAME_Y, lz))
    K.to_blender()
    X.finalize()
    return dict(body=body, light=light)


def main():
    args = M.main_guard()
    build()
    X.tri_report(NAME)
    path = E.export(NAME)
    lx, ly, lz = LAMP
    req = [NAME, "camp_lamp_flame"]
    errs = E.verify(path, required=req, identity=req, expect={NAME: (0, 0, 0), "camp_lamp_flame": (lx, ly + FLAME_Y, lz)},
                    parents={n: None for n in req}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = E.bounds([NAME])
    print(f"{X.TAG} {NAME} bounds {lo} .. {hi}")
    print(f"{X.TAG} VERIFY {NAME} {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return


main()
