"""ch3_dress_corridor.glb — set-dressing of the crystal shutter's wall (group K, drawn in the camp's own views): the
service side of Leyla's camp, where the shutter tunnel to the Gallery leaves the room. Pipes and conduit run along the
walls, a fire bucket hangs on a hook under its pictogram, a dusty hand cart is parked in the room, warning marks (original,
language-neutral pictograms: hazard bolt, flame, no entry, flow chevrons, valve, hazard stripes, ) are
stencilled on the tiles and the floor, and the tiles are cracked, stained and missing in places.
Nothing here is interactive (no colliders).

ROOM-COORDINATE model: origin = the world origin, built in place in the camp x 4.5 .. 7.6, z -4.0 .. -1.2, y 0 .. 2.9.
The shutter frame (x 4.5 .. 4.65, z -3.25 .. -1.95, y 0 .. 2.1), its crystals and the sheets near it stay clear.

  ch3_dress_corridor  (static) ONE mesh, a surface per material (painted steel, steel, rubber, wood, crimson enamel, paper,
                      canvas, the grime atlas):
      pipe run     a painted pipe along the west wall (clamps, a flanged valve with a red wheel), turning up through the
                   roof at the south wall; a conduit along the north wall with clips, a junction box, a drop to a switch box
      fire bucket  crimson enamel with sand, on a hook plate (north wall), the flame pictogram above it
      hand cart    plank deck on a steel frame, four casters, a tubular handle with a cable coil, a canvas-covered load
      grime atlas  the west wall's baseboard dirt, soot, damp, rust, streaks, cracks, missing tiles; the warning marks;
                   the hazard stripe in front of the shutter and the  on the floor

    blender -b --factory-startup -P tools/blender/models/ch3_dress_corridor.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ch3_dress_lib as X  # noqa: E402
from ch3_dress_lib import K, D, E, M, bpy, Matrix, Vector  # noqa: E402

NAME = "ch3_dress_corridor"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 10, 10
WALL_N, WALL_W, WALL_S, WALL_E = X.WALL_N, X.WALL_W, X.WALL_S, X.WALL_E
place, at = X.place, X.at
CART = (5.60, 0.0, -2.42)
CART_YAW = 100.0                         # long axis north-south, parked in the ; the handle points south
BUCKET_X = 4.96


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
    bx, bz = BUCKET_X, WALL_N + 0.13
    steel.append(K.gbox("hook_plate", (bx - 0.045, 1.30, WALL_N), (bx + 0.045, 1.42, WALL_N + 0.012), X.STEEL, 0.002))
    steel.append(D.rod("hook", (bx, 1.38, WALL_N + 0.01), (bx, 1.38, WALL_N + 0.075), 0.007, segs=5, mat=X.STEEL))
    crimson.append(K.glathe("bucket", [(0.0, 0.0), (0.078, 0.0), (0.090, 0.010), (0.118, 0.235), (0.0, 0.235)],
                            (bx, 1.08, bz), (0, 1, 0), 16, X.CRIMSON, smooth=60.0))
    crimson.append(K.glathe("bucket_rim", [(0.114, 0.218), (0.124, 0.226), (0.124, 0.242), (0.112, 0.246), (0.108, 0.230)],
                            (bx, 1.08, bz), (0, 1, 0), 16, X.CRIMSON, smooth=60.0, cap_bottom=False, cap_top=False))
    paper.append(K.glathe("bucket_sand", [(0.0, 0.221), (0.108, 0.221)], (bx, 1.08, bz), (0, 1, 0), 16, X.PAPER, smooth=80.0,
                          cap_bottom=False, cap_top=False))
    steel.append(D.tube("bucket_bail", [(bx - 0.115, 1.08 + 0.238, bz), (bx - 0.05, 1.08 + 0.33, bz - 0.03), (bx + 0.05, 1.08 + 0.33, bz - 0.03),
                                       (bx + 0.115, 1.08 + 0.238, bz)], 0.0035, sides=4, mat=X.STEEL, fillet=0.03))
    return paint, steel, crimson, paper


# ====================================================================== the dusty hand cart
def cart():
    """A flat-bed hand cart left in the camp: plank deck on a steel frame, four casters, a tubular handle, a canvas-covered
    load with a coil of cable hung on the handle. Local frame: x along the cart, z across, handle at -x (turned by CART_YAW)."""
    wood, steel, rub, fab = [], [], [], []
    L_, W_, deck = 0.78, 0.46, 0.31
    for k in range(5):
        z0 = -W_ / 2 + k * W_ / 5
        wood.append(K.gbox("deck", (-L_ / 2, deck, z0 + 0.004), (L_ / 2, deck + 0.032, z0 + W_ / 5 - 0.004), X.WOOD, 0.002))
    for sz in (-1, 1):
        steel.append(K.gbox("cart_rail", (-L_ / 2 + 0.02, deck - 0.05, sz * (W_ / 2 - 0.03) - 0.016),
                            (L_ / 2 - 0.02, deck, sz * (W_ / 2 - 0.03) + 0.016), X.STEEL, 0.002))
    for sx in (-1, 1):
        steel.append(K.gbox("cart_cross", (sx * (L_ / 2 - 0.07) - 0.016, deck - 0.05, -W_ / 2 + 0.03),
                            (sx * (L_ / 2 - 0.07) + 0.016, deck, W_ / 2 - 0.03), X.STEEL, 0.002))
        for sz in (-1, 1):
            cx, cz = sx * (L_ / 2 - 0.07), sz * (W_ / 2 - 0.05)
            steel.append(K.gbox("fork", (cx - 0.012, 0.075, cz - 0.02), (cx + 0.012, deck - 0.05, cz + 0.02), X.STEEL, 0.001))
            rub.append(K.gcyl("caster", 0.045, -0.014, 0.014, base=(cx, 0.047, cz), axis=(0, 0, 1), segments=10, mat=X.RUBBER, chamfer=0.003))
    for sz in (-1, 1):
        steel.append(D.tube("cart_handle_leg", [(-L_ / 2 + 0.03, deck, sz * (W_ / 2 - 0.05)), (-L_ / 2 - 0.10, deck + 0.40, sz * (W_ / 2 - 0.06)),
                                                 (-L_ / 2 - 0.16, deck + 0.64, sz * (W_ / 2 - 0.06))], 0.0105, sides=6, mat=X.STEEL, fillet=0.0))
    steel.append(D.rod("cart_handle", (-L_ / 2 - 0.16, deck + 0.64, -W_ / 2 + 0.04), (-L_ / 2 - 0.16, deck + 0.64, W_ / 2 - 0.04), 0.0115, segs=8, mat=X.STEEL))
    # the load: a crate under a dusty canvas; a coil of cable hung on the handle
    load = E.rrect_box("cart_load", 0.36, 0.22, 0.30, 0.04, (0.14, deck + 0.032 + 0.11, 0.0), X.LINEN, n=3, bevel=0.02)
    E.jitter(load, 0.006, 91)
    fab.append(load)
    rub.append(D.tube("cable_coil", [(-L_ / 2 - 0.16, deck + 0.60, -0.10), (-L_ / 2 - 0.20, deck + 0.50, -0.06), (-L_ / 2 - 0.20, deck + 0.46, 0.04),
                                     (-L_ / 2 - 0.16, deck + 0.50, 0.10), (-L_ / 2 - 0.14, deck + 0.58, 0.04), (-L_ / 2 - 0.16, deck + 0.60, -0.04)],
                       0.0085, sides=5, mat=X.RUBBER, fillet=0.03))
    place(wood + steel + rub + fab, at(CART[0], CART[1], CART[2], CART_YAW) @ Matrix.Scale(0.85, 4))
    return wood, steel, rub, fab


# ====================================================================== grime atlas and warning marks
def snap_t(v, phase=0.0):
    """Snap to the 0.15 m tile grid: u = x / -z (lines at multiples of 0.15), v = 1 - y (lines at y = 0.10 + 0.15 k)."""
    return X.snap(v, X.TILE, phase)


def grime():
    d = X.Decals()
    on, floor = d.on, d.floor
    # ---- west wall (the shutter frame stands in front of z -3.25 .. -1.95)
    on("grime_top", "W", -3.10, 2.47, 1.7, 0.85)
    on("grime_top", "W", -1.75, 2.47, 1.7, 0.85, flip=True)
    on("baseboard", "W", -3.10, 0.42, 1.7, 0.85, flip=True)
    on("baseboard", "W", -1.75, 0.42, 1.7, 0.85)
    on("damp_b", "W", -3.45, 1.78, 0.80, 0.80, -10.0)
    on("streaks_b", "W", -1.40, 1.30, 0.80, 0.80)
    on("tiles_b", "W", snap_t(-3.60), snap_t(1.35, 0.10), 0.60, 0.60)
    on("tiles_a", "W", snap_t(-1.60), snap_t(0.45, 0.10), 0.60, 0.60)
    on("rust_b", "W", -3.44, 1.88, 0.40, 0.40, 0.0, 0.005)               # under the flanged joint
    on("crack_b", "W", -1.45, 0.75, 0.55, 0.55)
    on("crack_a", "W", -2.95, 2.35, 0.5, 0.5)
    on("corner", "W", -3.95, 2.78, 0.6, 0.6, 0.0)
    # ---- warning marks: a hazard bolt on the tile beside the shutter, flow chevrons under the pipe, a valve glyph
    on("st_bolt", "W", -3.70, 0.98, 0.20, 0.20, 3.0, 0.0045)
    on("st_pipe", "W", -1.45, 2.08, 0.50, 0.25, 0.0, 0.0045)
    on("st_valve", "W", -3.44, 1.92, 0.20, 0.10, 0.0, 0.0045)
    on("st_flame", "N", BUCKET_X, 1.70, 0.20, 0.20, -2.0, 0.0045)       # behind the bucket's hook
    # ---- floor: the only hazard stripe frames the shutter's foot; it is old, so dirt is laid over it afterwards
    floor("st_stripes", 4.86, -2.6, 1.34, 0.30, 90.0, 0.0045)
    floor("baseboard", 4.75, -2.6, 2.9, 0.55, 90.0)
    floor("damp_a", 5.55, -2.20, 1.0, 1.0, 40.0)
    floor("damp_b", 4.95, -2.95, 0.8, 0.8, 100.0, 0.0038)
    floor("corner", 4.85, -2.25, 0.8, 0.8, 270.0, 0.0038)
    floor("soot", 4.90, -2.62, 0.7, 0.7, 30.0, 0.0040)
    return d.items


# ====================================================================== build
def build():
    M.reset_scene()
    X.ensure_materials()
    paint, steel, crimson, paper = services()
    cw, cs, cr, cf = cart()
    dec = grime()
    X.clip_quads(dec, X.CAMP_LO, X.CAMP_HI)
    objs = paint + steel + crimson + paper + cw + cs + cr + cf + dec
    X.report_outside(objs, (WALL_W, 0.0, WALL_N), (WALL_E, 2.9, WALL_S))
    body = K.part(NAME, objs, pivot=(0.0, 0.0, 0.0))
    K.to_blender()
    X.finalize()
    return dict(body=body)


# ====================================================================== QA (Cycles, qa/blender/ch3/dress_corridor*.png)
def qa(args):
    E.qa_begin()
    E.camp_room(extra=[("leyla_camp", (0, 0, 0), 0.0, "qa_lc_"), ("ch3_dress_camp", (0, 0, 0), 0.0, "qa_dk_"),
                       ("crystal_shutter", E.SHUTTER_POS, E.SHUTTER_YAW, "qa_cs_")])
    if E.want(args, "1"):                                   # the shutter view
        S = E.view("shutter")
        E.camp_lights(S[0], fill=5.0, bulb=40.0)
        K.light("camp_kero", "POINT", (5.78, 0.535, -3.13), 70.0, "FFB868", radius=0.03)
        E.shoot("dress_corridor", S[0], S[1], S[2])
    if E.want(args, "2"):                                   # the cart and the shutter foot from the doorway side
        cam = (6.9, 1.2, -1.6)
        E.camp_lights(cam, fill=4.0, bulb=40.0)
        K.light("camp_kero", "POINT", (5.78, 0.535, -3.13), 70.0, "FFB868", radius=0.03)
        E.shoot("dress_corridor_2", cam, (5.3, 0.5, -2.7), 58)


def main():
    args = M.main_guard()
    build()
    X.tri_report(NAME)
    path = E.export(NAME)
    req = [NAME]
    errs = E.verify(path, required=req, identity=req, expect={NAME: (0, 0, 0)}, parents={n: None for n in req},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = E.bounds([NAME])
    print(f"{X.TAG} {NAME} bounds {lo} .. {hi}")
    print(f"{X.TAG} VERIFY {NAME} {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args)


main()
