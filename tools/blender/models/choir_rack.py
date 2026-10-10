"""choir_rack.glb — the Choir's tube rack with the chalk staircase (W3).
Contract: docs/models/ch3.md §4 choir_rack (+ §1.3 slot hang points, §2 rack / rack_close views, §11 stair_quad);
tubes: choir_tube.py; results: docs/models/ch3_b.md.

Wall-mounted on the north wall at (-9.6, 0, -4.0), yaw 0 (front +Z faces into the hall). Origin = the wall plane at
floor level, centre. Posts at x ±1.35, top bar at y 2.35 (front face z 0.20), bottom rail at y 0.95, frame depth 0.35.

  choir_rack (static)   riveted dark steel: channel posts on foot plates with wall brackets, the top channel, the kick
                        rail on stays, the back board with its flat-bar frame, the striker's bearing blocks and the
                        hammer bracket (M_Steel_Dark); brass hanger brackets: a strap on the top bar, a block under it
                        and the peg that passes through the tube's eye, the lock-bar guides, the hammer's quadrant
                        (M_Brass_Aged).
  IA_slot_<k>           k = 0..6 (left -> right from the front, x_k = (k - 3) * 0.34): felt backing strips 0.24 x 1.15
                        (y 1.15..2.30, front at z 0.08), the slot's tap target (M_Felt).
  slot_mount_<k>        the hang point (x_k, 2.30, 0.20), identity: IA_tube_<r>'s eye top sits there, the tube hangs
                        along -Y; the peg's top is 5.6 mm below the hang point (the eye's inner top, choir_tube.py).
  striker               the felt-wrapped roller across all slots at y 2.12, z 0.30, on two arms from the axle at
                        (0, 2.40, 0.30); strike = +15° about local +X (the roller swings back into the tubes). One
                        material (M_Felt) so the rack stays at 13 surfaces.
  IA_hammer             the master-hammer lever on the right post, pivot (1.42, 1.10, 0.22) at its base;
                        pull = +45° about local +X (M_Brass_Aged).
  rack_lock             the brass locking bar in front of the peg tips, at rest above the eyes (y 2.305..2.345,
                        z 0.25..0.265); slides -0.05 on local Y once choir_tuned, closing the hooks.
  stair_quad            the chalk staircase on the wall above the rack: x ±1.30, y 2.55..3.45, z 0.004, UV 0..1
                        (u -> +X, v -> +Y), M_Shader_Quad (QA preview: qa/blender/ch3/preview/stair_quad.png).

    blender -b --factory-startup -P tools/blender/models/choir_rack.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "choir_rack"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 13, 4
STEEL, BRASS, FELT, SHQ = B.STEEL, B.BRASS, B.FELT, B.SHQ

POST_X, POST_W, POST_Z = 1.35, 0.08, (0.14, 0.22)
POST_TOP = 2.46
BAR = (2.30, 2.40, 0.0, 0.20)                   # top bar y0, y1, z0, z1 (front face 0.20)
RAIL = (0.93, 0.97, 0.29, 0.35)                 # bottom rail y0, y1, z0, z1
BOARD = (1.05, 2.30, 0.04, 0.07)                # back board y0, y1, z0, z1
HANG_Y, HANG_Z = 2.30, 0.20
EYE_TOP_TO_HOLE = 0.0056                        # choir_tube.py: the eye's inner top below the hang point
PEG_R = 0.0045
PEG_Y = HANG_Y - EYE_TOP_TO_HOLE - PEG_R
PEG_Z = (0.10, 0.235)
STRIKER_PIVOT = (0.0, 2.40, 0.30)
ROLLER_Y, ROLLER_R = 2.12, 0.022
HAMMER = (1.42, 1.10, 0.22)
LOCK = (2.305, 2.345, 0.25, 0.265)              # lock bar y0, y1, z0, z1 at rest (in front of the peg tips, z <= 0.243)
LOCK_SLIDE = -0.05
QUAD = (-1.30, 1.30, 2.55, 3.45, 0.004)
PLACE = ((-9.6, 0.0, -4.0), 0.0)
TUBES_START = [4, 0, 7, 2, 0, 5, 0, 6, 1, 3]    # UndergroundLogic.TUBES_START (0 = empty)
CHOIR_TARGET = [4, 6, 2, 7, 1, 5, 3]


def slot_x(k):
    return (k - 3) * 0.34


# ====================================================================== static steel
def frame():
    p = []
    z0, z1 = POST_Z
    for sx in (-1, 1):
        x = sx * POST_X
        # channel post (web toward the wall), foot plate with bolts, three wall brackets
        p.append(B.gbox("post", (x - POST_W / 2, 0.015, z0), (x + POST_W / 2, POST_TOP, z1), STEEL, 0.004))
        p.append(B.gbox("flange", (x - POST_W / 2 - 0.012, 0.015, z1 - 0.006), (x + POST_W / 2 + 0.012, POST_TOP, z1), STEEL, 0.002))
        p.append(B.gbox("foot", (x - 0.09, 0.0, 0.0), (x + 0.09, 0.015, 0.35), STEEL, 0.003))
        for (fx, fz) in ((x - 0.065, 0.05), (x + 0.065, 0.05), (x - 0.065, 0.30), (x + 0.065, 0.30)):
            p.append(B.hexbolt("fbolt", 0.008, (fx, 0.015, fz), normal=(0, 1, 0), h=0.008, mat=STEEL, washer=True))
        for y in (0.55, 1.55, 2.15):
            p.append(B.gbox("wbr", (x - 0.03, y - 0.025, 0.0), (x + 0.03, y + 0.025, z0), STEEL, 0.002))
            p.append(B.gbox("wpl", (x - 0.05, y - 0.045, 0.0), (x + 0.05, y + 0.045, 0.008), STEEL, 0.002))
        # kick-rail stays from the post front out to the rail
        p.append(B.gbox("stay", (x - 0.02, RAIL[0], z1), (x + 0.02, RAIL[1], RAIL[3]), STEEL, 0.002))
        # the striker's bearing blocks, out from the top bar's front
        bx = sx * 1.30
        p.append(B.gbox("bearing", (bx - 0.03, 2.37, BAR[3]), (bx + 0.03, 2.43, 0.33), STEEL, 0.003))
        p.append(B.gbox("bearing_t", (bx - 0.03, 2.37, 0.33 - 0.012), (bx + 0.03, 2.47, 0.33), STEEL, 0.003))
    # top channel (open toward the wall), its front lip, rivets along the lip
    p.append(B.gbox("bar", (-POST_X - 0.04, BAR[0], BAR[2]), (POST_X + 0.04, BAR[1], BAR[3]), STEEL, 0.004))
    p.append(B.gbox("barlip", (-POST_X - 0.04, BAR[1] - 0.004, BAR[3]), (POST_X + 0.04, BAR[1] + 0.03, BAR[3] + 0.008), STEEL, 0.002))
    for x in [-1.30 + 0.20 * k for k in range(14)]:
        p.append(B.rivet("brv", 0.006, (x, BAR[1] + 0.013, BAR[3] + 0.008), normal=(0, 0, 1), mat=STEEL, segs=6))
    # bottom (kick) rail: an angle between the posts
    p.append(B.gbox("rail", (-POST_X + 0.02, RAIL[0], RAIL[2]), (POST_X - 0.02, RAIL[1], RAIL[3]), STEEL, 0.003))
    p.append(B.gbox("rail2", (-POST_X + 0.02, RAIL[0] - 0.04, RAIL[3] - 0.006), (POST_X - 0.02, RAIL[0], RAIL[3]), STEEL, 0.002))
    # back board with its flat-bar frame and rivets (the felt strips sit on it)
    y0, y1, bz0, bz1 = BOARD
    p.append(B.gbox("board", (-1.30, y0, bz0), (1.30, y1, bz1), STEEL, 0.002))
    for (x0, x1) in ((-1.34, -1.30), (1.30, 1.34)):
        p.append(B.gbox("bfr", (x0, y0 - 0.04, bz0), (x1, y1, bz1 + 0.004), STEEL, 0.001))
    p.append(B.gbox("bfr_b", (-1.34, y0 - 0.04, bz0), (1.34, y0, bz1 + 0.004), STEEL, 0.001))
    for k in range(6):
        x = slot_x(k) + 0.17
        p.append(B.gbox("bmul", (x - 0.012, y0, bz0), (x + 0.012, y1, bz1 + 0.004), STEEL, 0.001))
        for y in (y0 + 0.08, 1.70, y1 - 0.06):
            p.append(B.rivet("brv2", 0.005, (x, y, bz1 + 0.004), normal=(0, 0, 1), mat=STEEL, segs=6))
    # hammer bracket on the right post's outer face: a plate, an outer cheek and the web between them (the boss turns
    # between the cheeks)
    hx, hy, hz = HAMMER
    xf = POST_X + POST_W / 2
    p.append(B.gbox("hplate", (xf - 0.012, hy - 0.075, hz - 0.06), (xf + 0.005, hy + 0.075, hz + 0.06), STEEL, 0.002))
    p.append(B.gbox("hcheek", (hx + 0.027, hy - 0.04, hz - 0.045), (hx + 0.034, hy + 0.04, hz + 0.045), STEEL, 0.002))
    p.append(B.gbox("hweb", (xf, hy - 0.05, hz - 0.045), (hx + 0.034, hy - 0.04, hz + 0.045), STEEL, 0.002))
    return p


def brass_static():
    p = []
    for k in range(7):
        x = slot_x(k)
        # hanger bracket: strap on the bar's face with two rivets, the block under the bar, the peg with its tip
        p.append(B.gbox("strap", (x - 0.022, BAR[0], BAR[3]), (x + 0.022, BAR[1] + 0.02, BAR[3] + 0.003), BRASS, 0.001))
        for y in (BAR[0] + 0.02, BAR[1] + 0.005):
            p.append(B.rivet("srv", 0.004, (x, y, BAR[3] + 0.003), normal=(0, 0, 1), mat=BRASS, segs=6))
        p.append(B.gbox("hblock", (x - 0.018, BAR[0] - 0.035, PEG_Z[0]), (x + 0.018, BAR[0], 0.19), BRASS, 0.002))
        p.append(B.gcyl("peg", PEG_R, PEG_Z[0] + 0.01, PEG_Z[1], base=(x, PEG_Y, 0.0), axis=(0, 0, 1), segments=8, mat=BRASS))
        p.append(B.glathe("pegtip", [(0.0, 0.0), (0.0075, 0.0), (0.0075, 0.004), (0.0, 0.008)], (x, PEG_Y + 0.002, PEG_Z[1]),
                          (0, 0, 1), 8, BRASS, smooth=50.0))
    # lock-bar guides on the posts: U brackets the bar slides in
    ly0, ly1, lz0, lz1 = LOCK
    for sx in (-1, 1):
        gx0, gx1 = (POST_X - 0.04, POST_X + 0.02) if sx > 0 else (-POST_X - 0.02, -POST_X + 0.04)
        p.append(B.gbox("guide_b", (gx0, ly0 + LOCK_SLIDE - 0.012, lz0 - 0.004), (gx1, ly0 + LOCK_SLIDE, lz1 + 0.004), BRASS, 0.001))
        p.append(B.gbox("guide_f", (gx0, ly0 + LOCK_SLIDE - 0.012, lz1), (gx1, ly1 + 0.012, lz1 + 0.004), BRASS, 0.001))
        p.append(B.gbox("guide_k", (gx0, ly0 + LOCK_SLIDE - 0.012, lz0 - 0.004), (gx1, ly1 + 0.012, lz0), BRASS, 0.001))
    # hammer quadrant: a toothed brass arc the lever's catch rides on (static)
    hx, hy, hz = HAMMER
    # drawn in XY (x = cos a, y = sin a), then stood in the YZ plane as (y = cos a, z = sin a): a = 0 is the upright
    # rest, a = 45 the pulled lever; the plate sits at the lever's right, x = hx + 0.035 .. 0.041
    arc = [(math.cos(math.radians(a)) * 0.12, math.sin(math.radians(a)) * 0.12) for a in range(-10, 61, 10)]
    arc_in = [(math.cos(math.radians(a)) * 0.095, math.sin(math.radians(a)) * 0.095) for a in range(60, -11, -10)]
    q = B.plate("quadrant", [arc + arc_in], 0.006, mat=BRASS, bevel=0.0, loc=(0.0, 0.0, 0.0))
    q.data.transform(Matrix.Translation((hx + 0.035, hy, hz)) @ Matrix.Rotation(math.radians(90), 4, "Y") @
                     Matrix.Rotation(math.radians(90), 4, "Z"))
    p.append(q)
    return p


def static():
    return B.part(NAME, frame() + brass_static())


# ====================================================================== parts
def slot(k):
    x = slot_x(k)
    o = B.gbox("felt", (x - 0.12, 1.15, BOARD[3]), (x + 0.12, HANG_Y, 0.08), FELT, 0.002)
    return B.part(f"IA_slot_{k}", [o], pivot=(x, (1.15 + HANG_Y) / 2, 0.075))


def striker():
    px, py, pz = STRIKER_PIVOT
    p = [B.gcyl("axle", 0.009, -1.33, 1.33, base=(0.0, py, pz), axis=(1, 0, 0), segments=8, mat=FELT)]
    for sx in (-1, 1):
        x = sx * 1.25
        p.append(B.gbox("arm", (x - 0.012, ROLLER_Y, pz - 0.015), (x + 0.012, py, pz + 0.015), FELT, 0.002))
    p.append(B.gcyl("roller", ROLLER_R, -1.30, 1.30, base=(0.0, ROLLER_Y, pz), axis=(1, 0, 0), segments=12, mat=FELT,
                    chamfer=0.006))
    return B.part("striker", p, pivot=STRIKER_PIVOT)


def hammer():
    hx, hy, hz = HAMMER
    p = [B.gcyl("boss", 0.018, -0.025, 0.025, base=(hx, hy, hz), axis=(1, 0, 0), segments=10, mat=BRASS, chamfer=0.003)]
    stem = [(0.0, 0.0), (0.011, 0.0), (0.011, 0.03), (0.0085, 0.04), (0.0075, 0.36), (0.010, 0.368), (0.010, 0.38), (0.0, 0.385)]
    p.append(B.glathe("stem", stem, (hx, hy, hz), (0, 1, 0), 10, BRASS, smooth=50.0))
    ball = M.sphere("grip", 0.026, loc=(hx, hy + 0.40, hz), segments=12, rings=7, mat=BRASS)
    M.apply_transform(ball)
    A.hint(ball, 80.0)
    p.append(ball)
    # the catch that rides on the quadrant
    p.append(B.gbox("catch", (hx + 0.011, hy + 0.09, hz - 0.006), (hx + 0.028, hy + 0.11, hz + 0.006), BRASS, 0.001))
    return B.part("IA_hammer", p, pivot=HAMMER)


def rack_lock():
    y0, y1, z0, z1 = LOCK
    bar = B.gbox("lockbar", (-POST_X - 0.01, y0, z0), (POST_X + 0.01, y1, z1), BRASS, 0.002)
    # a handle loop at the centre and end pins in the guides
    loop = B.tube("lloop", [(-0.03, y1, (z0 + z1) / 2), (-0.03, y1 + 0.02, z1 + 0.01), (0.03, y1 + 0.02, z1 + 0.01),
                            (0.03, y1, (z0 + z1) / 2)], 0.003, sides=6, mat=BRASS)
    return B.part("rack_lock", [bar, loop], pivot=(0.0, (y0 + y1) / 2, (z0 + z1) / 2))


def stair_quad():
    x0, x1, y0, y1, z = QUAD
    q = B.K.quad("stair_quad", ((x0 + x1) / 2, (y0 + y1) / 2, z), (1, 0, 0), (0, 1, 0), x1 - x0, y1 - y0, SHQ)
    return B.part("stair_quad", [q], pivot=((x0 + x1) / 2, (y0 + y1) / 2, z))


def mounts():
    return [B.empty(f"slot_mount_{k}", (slot_x(k), HANG_Y, HANG_Z)) for k in range(7)]


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    slots = [slot(k) for k in range(7)]
    strk = striker()
    hm = hammer()
    lk = rack_lock()
    sq = stair_quad()
    mts = mounts()
    B.K.to_blender()
    A.finalize_uv()
    uvl = sq.data.uv_layers.active      # finalize_uv skips only M_Decal_*: restore the shader quad's 0..1 UVs
    for li, (uu, vv) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uvl.data[li].uv = (uu, vv)
    return dict(static=st, slots=slots, striker=strk, hammer=hm, lock=lk, quad=sq, mounts=mts)


REQ = ([NAME] + [f"IA_slot_{k}" for k in range(7)] + [f"slot_mount_{k}" for k in range(7)] +
       ["striker", "IA_hammer", "rack_lock", "stair_quad"])


def check_quad_uv(obj):
    me = obj.data
    uv = me.uv_layers.active.data
    pts = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = B.V.C_INV @ (obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            pts.append((round(co.x, 3), round(co.y, 3), tuple(round(c, 3) for c in uv[li].uv)))
    ok = all(((u > 0.5) == (x > 0)) and ((v > 0.5) == (y > 3.0)) and (u in (0.0, 1.0)) and (v in (0.0, 1.0))
             for (x, y, (u, v)) in pts)
    print(f"{B.TAG} stair_quad UV corners (godot x, y, uv): {pts} -> {'OK' if ok else 'WRONG'}")
    return [] if ok else ["stair_quad UV not 0..1 with u -> +X, v -> +Y"]


def verify(path, parts):
    ident = list(REQ)
    expect = {f"IA_slot_{k}": (slot_x(k), (1.15 + HANG_Y) / 2, 0.075) for k in range(7)}
    expect.update({f"slot_mount_{k}": (slot_x(k), HANG_Y, HANG_Z) for k in range(7)})
    expect.update({"striker": STRIKER_PIVOT, "IA_hammer": HAMMER,
                   "rack_lock": (0.0, (LOCK[0] + LOCK[1]) / 2, (LOCK[2] + LOCK[3]) / 2),
                   "stair_quad": ((QUAD[0] + QUAD[1]) / 2, (QUAD[2] + QUAD[3]) / 2, QUAD[4])})
    errs = B.verify(path, REQ, identity=ident, expect=expect, parents={n: None for n in REQ}, tris=TRI_BUDGET,
                    surf=SURF_BUDGET, mats=MAT_BUDGET)
    errs += check_quad_uv(parts["quad"])
    lo, hi = B.V.mesh_bounds_godot([parts["static"]])
    print(f"{B.TAG} static bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    # §1.3: slot k hang point in the world
    (px, py, pz), _ = PLACE
    pts = [(round(px + slot_x(k), 3), round(py + HANG_Y, 3), round(pz + HANG_Z, 3)) for k in range(7)]
    print(f"{B.TAG} §1.3 hang points (world): {pts}")
    return errs


# ====================================================================== QA
def hang_tubes(holder, layout):
    """Parent the imported IA_tube_<r> objects to slot_mount_<k> per layout (slot k -> reading r, 0 = empty); hide the rest."""
    for o in holder.children_recursive:
        o.hide_render = True
    for k in range(7):
        r = layout[k]
        if r == 0:
            continue
        t = B.imported("qa_tubes_", f"IA_tube_{r}")
        if t is None:
            continue
        t.parent = bpy.data.objects[f"slot_mount_{k}"]
        t.matrix_parent_inverse = Matrix.Identity(4)
        t.matrix_basis = Matrix.Identity(4)
        t.hide_render = False
        for c in t.children_recursive:
            c.hide_render = False
    M.refresh()


def qa(parts, args):
    B.qa_begin()
    B.hall()
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    B.place(mine, *PLACE, name="qa_rack")
    for nm, pos, yaw in (("tube_bench", (-7.35, 0.0, -4.0), 0.0), ("control_desk", (-8.0, 0.0, 0.5), 180.0)):
        B.bring(nm, pos, yaw, prefix=f"qa_{nm}_")
    tubes = B.bring("choir_tube", prefix="qa_tubes_")
    prev = os.path.join(B.PREVIEW_DIR, "stair_quad.png")
    if os.path.exists(prev):
        B.K.override(parts["quad"], B.K.image_emitter("qa_stair", prev, strength=1.1))
    movers = [parts["striker"], parts["hammer"], parts["lock"]]
    rest = B.rest_store(movers)

    def state(layout, tuned=False):
        B.rest_apply(movers, rest)
        if tubes is not None:
            hang_tubes(tubes, layout)
        if tuned:
            B.K.pose_rot(parts["striker"], "x", 15.0)
            B.K.pose_rot(parts["hammer"], "x", 45.0)
            B.K.pose_slide(parts["lock"], (0.0, LOCK_SLIDE, 0.0))

    shots = [
        # 1 rack view at the start: three slots empty, the chalk staircase above
        ("1", NAME, (-9.6, 1.8, -1.25), (-9.6, 2.1, -3.65), 58, dict(layout=TUBES_START)),
        # 2 rack_close view at the start
        ("2", NAME + "_2", (-9.6, 1.75, -2.4), (-9.6, 1.75, -3.8), 54, dict(layout=TUBES_START)),
        # 3 rack view, tuned: the staircase hung, hammer pulled, striker swung into the tubes, lock bar dropped
        ("3", NAME + "_3", (-9.6, 1.8, -1.25), (-9.6, 2.1, -3.65), 58, dict(layout=CHOIR_TARGET, tuned=True)),
        # 4 hangers close-up: pegs through the eyes, the lock bar, the striker roller, the hammer
        ("4", NAME + "_4", (-8.35, 2.45, -3.05), (-9.1, 2.28, -3.78), 38, dict(layout=CHOIR_TARGET, tuned=True)),
        # 5 choir view (root view; the rack is its target)
        ("5", NAME + "_5", (-5.4, 1.65, 3.3), (-9.6, 1.5, -2.0), 62, dict(layout=TUBES_START)),
    ]
    for tag, name, cam, tgt, fov, st in shots:
        if not B.want(args, tag):
            continue
        state(**st)
        B.choir_lights(cam, fill=9.0 if tag != "5" else 0.0)
        B.shoot(name, cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path, parts)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
