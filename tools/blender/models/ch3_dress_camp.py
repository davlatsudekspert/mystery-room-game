"""ch3_dress_camp.glb — set-dressing of Leyla's 1998 camp (group K): what a woman who lived 45 years ago under the
Institute left on her camp table and walls, so the room reads as inhabited and abandoned instead of a clean tiled box.
Nothing here is interactive (no colliders); the room draws it only in the camp's own views (culling group J).

ROOM-COORDINATE model: origin = the world origin, built in place in the camp x 4.5 .. 7.6, z -4.0 .. -1.2, y 0 .. 2.9
(walls: north z -3.965, west x 4.535, south z -1.203, east x 7.6). Everything sits clear of the interactive parts
(recorder, oscillograph, shutter frame, crystals) and of the sight lines of the `camp`, `shutter` and `recorder` views.
The wall services, the fire bucket, the cart and the shutter wall's marks are the sibling model ch3_dress_corridor.

  ch3_dress_camp   (static) ONE mesh, a surface per material:
      crate table       a plank crate beside the cot's head, with the storm lantern (the camp's key light), a stack of
                        notebooks, an open notebook and a pencil, a tin mug
      wool blanket      on the sleeping bag, one edge hanging over the cot rail
      kerosene heater   on the floor at the cot's head, its mica window glowing
      spare battery     a steel pack with clamp leads, beside the table's cable run
      maps and cords    survey maps pinned over the tiles (north, west and south walls) with red cord tied between the
                        tacks, notebook pages and a photo
      grime atlas       baseboard dirt, ceiling-line soot, damp stains, rust drips, streaks, cracks, missing tiles on the
                        north, south and east walls; floor dirt
  camp_lamp_flame  empty at the lantern's flame: the key light of the camp (the room puts an omni there)

    blender -b --factory-startup -P tools/blender/models/ch3_dress_camp.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ch3_dress_lib as X  # noqa: E402
from ch3_dress_lib import K, D, E, M, bpy, Matrix, Vector  # noqa: E402

NAME = "ch3_dress_camp"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 7000, 12, 12
WALL_N, WALL_W, WALL_S, WALL_E, WALLS = X.WALL_N, X.WALL_W, X.WALL_S, X.WALL_E, X.WALLS
place, at = X.place, X.at
CT = (5.60, 6.16, -3.32, -2.84)          # the crate table
CT_H = 0.42
LAMP = (5.78, CT_H, -3.13)
FLAME_Y = 0.115                          # flame centre above the lantern base
HEATER = (5.38, 0.0, -3.10)
PACK = (5.84, 0.0, -1.42)


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
        c, p = notebook(6.00 + dx, CT_H + k * 0.024, -3.15 + dz, rot)
        leather += c
        paper += p
    # an open notebook, a pencil
    leather.append(K.gbox("onb_cover", (-0.15, 0.0, -0.10), (0.15, 0.006, 0.10), X.LEATHER, 0.002))
    paper.append(K.gbox("onb_l", (-0.14, 0.006, -0.09), (-0.004, 0.014, 0.09), X.PAPER, 0.0))
    paper.append(K.gbox("onb_r", (0.004, 0.006, -0.09), (0.14, 0.012, 0.09), X.PAPER, 0.0))
    place(leather[-1:] + paper[-2:], at(5.88, CT_H, -2.975, -14.0))
    pen = D.rod("pencil", (5.80, CT_H + 0.016, -2.885), (5.99, CT_H + 0.016, -2.865), 0.0036, segs=5, mat=X.WOOD)
    wood.append(pen)
    # a tin mug, handle to the east
    mx, mz = 5.70, -2.95
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


# ====================================================================== grime atlas
def grime():
    """Atlas decals of the camp room itself: the north, south and east walls and the floor (the shutter wall is the
    corridor model's)."""
    d = X.Decals()
    on, floor = d.on, d.floor
    # ---- north wall (tiles)
    on("grime_top", "N", 5.30, 2.47, 1.7, 0.85)
    on("grime_top", "N", 6.90, 2.47, 1.7, 0.85, flip=True)
    on("baseboard", "N", 5.30, 0.42, 1.7, 0.85)
    on("baseboard", "N", 6.90, 0.42, 1.7, 0.85, flip=True)
    on("damp_a", "N", 6.30, 2.12, 0.80, 0.80, 20.0)
    on("streaks_a", "N", 5.95, 1.50, 0.80, 0.80, 0.0, 0.0045)
    on("streaks_b", "N", 7.30, 1.55, 0.70, 0.70, 0.0, 0.0045)
    on("rust_a", "N", WALL_W + 0.06, 1.56, 0.34, 0.34, 0.0, 0.005)      # under the corridor's switch box
    on("tiles_a", "N", snap_t(7.05), snap_t(2.0, 0.10), 0.60, 0.60)
    on("crack_a", "N", 5.05, 1.55, 0.55, 0.55, 0.0)
    # ---- south partition (cream steel)
    on("grime_top", "S", 5.0, 2.47, 1.7, 0.85)
    on("baseboard", "S", 5.0, 0.42, 1.7, 0.85)
    on("damp_a", "S", 5.10, 2.15, 0.8, 0.8, 200.0)
    on("streaks_a", "S", 5.45, 1.30, 0.7, 0.7)
    on("rust_a", "S", 5.45, 2.55, 0.34, 0.34, 0.0, 0.005)
    on("baseboard", "S", 7.0, 0.42, 1.7, 0.85)
    on("grime_top", "S", 7.0, 2.47, 1.7, 0.85)
    on("st_noentry", "S", 4.74, 1.28, 0.20, 0.20, 0.0, 0.0045)
    # ---- east wall
    on("grime_top", "E", -3.0, 2.47, 1.7, 0.85)
    on("grime_top", "E", -1.8, 2.47, 1.7, 0.85)
    on("baseboard", "E", -3.0, 0.42, 1.7, 0.85)
    on("damp_b", "E", -2.7, 1.9, 0.9, 0.9)
    # ---- floor: dirt along the north and south walls, damp, soot under the heater
    floor("baseboard", 6.05, -3.78, 3.1, 0.62, 180.0)
    floor("baseboard", 6.05, -1.42, 3.1, 0.55)
    floor("damp_a", 6.4, -2.60, 1.1, 1.1, 40.0)
    floor("damp_b", 5.35, -3.15, 0.8, 0.8, 100.0)
    floor("corner", 7.4, -1.4, 0.9, 0.9, 0.0)
    floor("soot", 5.38, -3.10, 0.8, 0.8, 0.0, 0.0038)                     # under the heater
    return d.items


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
    dec += grime()
    X.clip_quads(dec, X.CAMP_LO, X.CAMP_HI)
    objs = wood + steel + leather + paper + brass + glass + flame + wool + paint + cord + dec
    X.report_outside(objs, (WALL_W, 0.0, WALL_N), (WALL_E, 2.9, WALL_S))
    body = K.part(NAME, objs, pivot=(0.0, 0.0, 0.0))
    lx, ly, lz = LAMP
    light = K.empty("camp_lamp_flame", (lx, ly + FLAME_Y, lz))
    K.to_blender()
    X.finalize()
    return dict(body=body, light=light)


# ====================================================================== QA (Cycles, qa/blender/ch3/dress_camp*.png)
def qa(args):
    E.qa_begin()
    E.camp_room(extra=[("leyla_camp", (0, 0, 0), 0.0, "qa_lc_"), ("ch3_dress_corridor", (0, 0, 0), 0.0, "qa_dc_"),
                       ("field_recorder", E.RECORDER_POS, E.RECORDER_YAW, "qa_fr_"), ("oscillograph", E.OSC_POS, E.OSC_YAW, "qa_os_"),
                       ("crystal_shutter", E.SHUTTER_POS, E.SHUTTER_YAW, "qa_cs_")])
    lx, ly, lz = LAMP
    if E.want(args, "1"):                                   # the camp view: the lantern is the key light
        C = E.view("camp")
        E.camp_lights(C[0], fill=5.0, bulb=40.0)
        K.light("camp_kero", "POINT", (lx, ly + FLAME_Y, lz), 70.0, "FFB868", radius=0.03)
        E.shoot("dress_camp", C[0], C[1], C[2])
    if E.want(args, "2"):                                   # the crate table and the heater from the cot's foot
        cam = (6.9, 1.05, -2.3)
        E.camp_lights(cam, fill=4.0, bulb=40.0)
        K.light("camp_kero", "POINT", (lx, ly + FLAME_Y, lz), 70.0, "FFB868", radius=0.03)
        E.shoot("dress_camp_2", cam, (5.6, 0.45, -3.1), 55)


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
    qa(args)


main()
