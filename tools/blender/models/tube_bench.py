"""tube_bench.glb — the work bench east of the Choir rack where the spare tubes lie (W3).
Contract: docs/models/ch3.md §4 tube_bench (+ §2 bench view); tubes: choir_tube.py; results: docs/models/ch3_b.md.

Back to the north wall at (-7.35, 0, -4.0), yaw 0 (front +Z). Origin = the wall plane at floor level, centre.
1.40 w x 0.60 d (x ±0.70, z 0 .. 0.60), top y 0.86.

  tube_bench (static)   painted steel angle-iron legs, stretchers and shelf frame, the tool rack's hooks and tools
                        (M_Steel_Painted); the plank top, the lower shelf boards, the tool board and the mallet
                        (M_Wood_Floor).
  IA_bench_<j>          j = 0..2 (front -> back): felt cradle strips 1.15 long along X at z_j = 0.45, 0.32, 0.19,
                        y 0.86 .. 0.89, with a shallow V groove (M_Felt). Tap target: tap_tube(7 + j).
  bench_mount_<j>       (-0.55, 0.915, z_j), basis +90° about local +Z: a tube parented with identity lies along +X in
                        the cradle (its eye at the left end, standing up).

    blender -b --factory-startup -P tools/blender/models/tube_bench.py [-- --no-render] [--shots=1,2,...]
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

NAME = "tube_bench"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2500, 5, 3
PAINT, WOOD, FELT = B.PAINT, B.FLOORWOOD, B.FELT

W2, DEPTH, TOP = 0.70, 0.60, 0.86
TOP_T = 0.04
CRADLE_Z = (0.45, 0.32, 0.19)
CRADLE_L, CRADLE_W = 1.15, 0.08
MOUNT = (-0.55, 0.915)
LEG = 0.04
PLACE = ((-7.35, 0.0, -4.0), 0.0)
BENCH_START = (6, 1, 3)                 # UndergroundLogic.TUBES_START[7:]


def angle_leg(x, z, y0, y1, out_x, out_z):
    """Angle-iron post: two 4 mm plates meeting at the corner (x, z), opening toward (out_x, out_z)."""
    t = 0.004
    a = B.gbox("legp", (min(x, x + out_x * LEG), y0, min(z, z + out_z * t)), (max(x, x + out_x * LEG), y1, max(z, z + out_z * t)),
               PAINT, 0.0)
    b = B.gbox("legp", (min(x, x + out_x * t), y0, min(z, z + out_z * LEG)), (max(x, x + out_x * t), y1, max(z, z + out_z * LEG)),
               PAINT, 0.0)
    return [a, b]


def steel():
    p = []
    y1 = TOP - TOP_T
    for sx in (-1, 1):
        for (z, oz) in ((0.03, 1), (DEPTH - 0.03, -1)):
            x = sx * (W2 - 0.03)
            p += angle_leg(x, z, 0.0, y1, -sx, oz)
            p.append(B.gbox("pad", (x - 0.03, 0.0, z - 0.03), (x + 0.03, 0.012, z + 0.03), PAINT, 0.002))
    # stretchers under the top (front, back, ends) and the shelf frame at y 0.22
    for (y0, yy1) in ((y1 - 0.045, y1), (0.20, 0.235)):
        p.append(B.gbox("str_f", (-W2 + 0.03, y0, 0.03), (W2 - 0.03, yy1, 0.034), PAINT, 0.0))
        p.append(B.gbox("str_b", (-W2 + 0.03, y0, DEPTH - 0.034), (W2 - 0.03, yy1, DEPTH - 0.03), PAINT, 0.0))
        for sx in (-1, 1):
            x = sx * (W2 - 0.03)
            p.append(B.gbox("str_e", (min(x, x - sx * 0.004), y0, 0.03), (max(x, x - sx * 0.004), yy1, DEPTH - 0.03), PAINT, 0.0))
    # a diagonal brace at each end, bolts at the leg tops
    for sx in (-1, 1):
        x = sx * (W2 - 0.032)
        br = B.gbox("brace", (x - 0.002, -0.015, -0.3), (x + 0.002, 0.015, 0.3), PAINT, 0.0)
        br.data.transform(Matrix.Translation((x, 0.50, DEPTH / 2)) @ Matrix.Rotation(math.radians(-42 * sx), 4, "X"))
        p.append(br)
        for z in (0.03, DEPTH - 0.03):
            p.append(B.hexbolt("lbolt", 0.006, (x + sx * 0.004, y1 - 0.022, z + (0.025 if z < 0.3 else -0.025)),
                               normal=(sx, 0, 0), h=0.006, mat=PAINT, washer=False))
    # tool rack hooks on the wall board, and the tools hanging on them
    for k, x in enumerate((-0.42, -0.14, 0.14, 0.42)):
        p.append(B.gcyl("hook", 0.004, 0.0, 0.05, base=(x, 1.30, 0.02), axis=(0, 0, 1), segments=6, mat=PAINT))
        p.append(B.gcyl("hooktip", 0.004, 0.0, 0.02, base=(x, 1.30, 0.07), axis=(0, 1, 0), segments=6, mat=PAINT))
    # a tuning spanner (a flat bar with a ring end) on hook 0
    p.append(B.gbox("spanner", (-0.42 - 0.009, 1.00, 0.026), (-0.42 + 0.009, 1.30, 0.032), PAINT, 0.0))
    p.append(B.plate("sp_ring", [L.circle(0.028, 12), list(reversed(L.circle(0.012, 10)))], 0.006, mat=PAINT, bevel=0.0,
                     loc=(-0.42, 0.985, 0.026)))
    # a tube hook (a bent rod) on hook 1
    p.append(B.tube("thook", [(-0.14, 1.30, 0.03), (-0.14, 1.05, 0.03), (-0.11, 1.02, 0.03), (-0.08, 1.05, 0.03)], 0.004, sides=6,
                    mat=PAINT))
    # mallet head band (the mallet itself is wood)
    p.append(B.gcyl("mband", 0.027, -0.006, 0.006, base=(0.42, 1.09, 0.06), axis=(1, 0, 0), segments=12, mat=PAINT, caps=False))
    return p


def wood():
    p = []
    # the plank top: three planks with 2 mm gaps, a chamfered front edge
    for k in range(3):
        z0 = 0.004 + k * 0.198
        p.append(B.gbox("plank", (-W2, TOP - TOP_T, z0), (W2, TOP, min(z0 + 0.194, DEPTH)), WOOD, 0.004, 1))
    # lower shelf boards
    for k in range(2):
        z0 = 0.09 + k * 0.23
        p.append(B.gbox("shelf", (-W2 + 0.05, 0.235, z0), (W2 - 0.05, 0.255, z0 + 0.20), WOOD, 0.002))
    # a crate on the shelf (closed box, open top)
    p.append(B.gbox("crate", (0.18, 0.255, 0.12), (0.58, 0.47, 0.50), WOOD, 0.003))
    p.append(B.gbox("cratehole", (0.20, 0.44, 0.14), (0.56, 0.475, 0.48), PAINT, 0.0))
    # tool board on the wall
    p.append(B.gbox("board", (-0.55, 0.95, 0.0), (0.55, 1.40, 0.02), WOOD, 0.003))
    # the mallet hanging from hook 3: a round head with a turned handle
    p.append(B.gcyl("mhead", 0.026, -0.05, 0.05, base=(0.42, 1.09, 0.06), axis=(1, 0, 0), segments=12, mat=WOOD, chamfer=0.004))
    p.append(B.glathe("mhandle", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.16), (0.012, 0.19), (0.012, 0.215), (0.0, 0.22)],
                      (0.42, 1.09, 0.06), (0, 1, 0), 10, WOOD, smooth=50.0))
    return p


def static():
    return B.part(NAME, steel() + wood())


# ====================================================================== cradles and mounts
def cradle(j):
    z = CRADLE_Z[j]
    hw, v_hw, v_d = CRADLE_W / 2, 0.008, 0.004
    prof = [(z - hw, TOP), (z + hw, TOP), (z + hw, 0.89), (z + v_hw, 0.89), (z, 0.89 - v_d), (z - v_hw, 0.89), (z - hw, 0.89)]
    o = B.prism_x("felt", prof, -CRADLE_L / 2, CRADLE_L / 2, FELT)
    return B.part(f"IA_bench_{j}", [o], pivot=(0.0, 0.875, z))


def mounts():
    return [B.empty(f"bench_mount_{j}", (MOUNT[0], MOUNT[1], CRADLE_Z[j]), (0.0, 0.0, 90.0)) for j in range(3)]


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    cr = [cradle(j) for j in range(3)]
    mts = mounts()
    B.K.to_blender()
    A.finalize_uv()
    return dict(static=st, cradles=cr, mounts=mts)


REQ = [NAME] + [f"IA_bench_{j}" for j in range(3)] + [f"bench_mount_{j}" for j in range(3)]


def verify(path, parts):
    expect = {f"IA_bench_{j}": (0.0, 0.875, CRADLE_Z[j]) for j in range(3)}
    expect.update({f"bench_mount_{j}": (MOUNT[0], MOUNT[1], CRADLE_Z[j]) for j in range(3)})
    rot = {f"bench_mount_{j}": (0.0, 0.0, 90.0) for j in range(3)}
    errs = B.verify(path, REQ, identity=[NAME] + [f"IA_bench_{j}" for j in range(3)], expect=expect,
                    parents={n: None for n in REQ}, rot_expect=rot, tris=TRI_BUDGET, surf=SURF_BUDGET, mats=MAT_BUDGET)
    lo, hi = B.V.mesh_bounds_godot([parts["static"]])
    print(f"{B.TAG} static bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    # a tube of radius 0.025 resting on the V's top edges (half-width 0.008) has its axis at:
    axis_y = 0.89 + math.sqrt(0.025 ** 2 - 0.008 ** 2)
    print(f"{B.TAG} tube axis on the cradle: y {axis_y:.4f} (mount at {MOUNT[1]})")
    return errs


# ====================================================================== QA
def lay_tubes(layout):
    for j, r in enumerate(layout):
        t = B.imported("qa_tubes_", f"IA_tube_{r}") if r else None
        if t is None:
            continue
        t.parent = bpy.data.objects[f"bench_mount_{j}"]
        t.matrix_parent_inverse = Matrix.Identity(4)
        t.matrix_basis = Matrix.Identity(4)
        t.hide_render = False
    M.refresh()


def qa(parts, args):
    B.qa_begin()
    B.hall()
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    B.place(mine, *PLACE, name="qa_bench")
    B.bring("choir_rack", (-9.6, 0.0, -4.0), 0.0, prefix="qa_rack_")
    tubes = B.bring("choir_tube", prefix="qa_tubes_")
    if tubes is not None:
        for o in tubes.children_recursive:
            o.hide_render = True
        lay_tubes(BENCH_START)
    shots = [
        # 1 bench view: the three spare tubes in their cradles (6, 1, 3 front -> back)
        ("1", NAME, (-7.35, 1.6, -2.35), (-7.35, 0.9, -3.7), 50),
        # 2 oblique close-up of the cradles, the eyes at the left ends, the tool board
        ("2", NAME + "_2", (-6.45, 1.35, -3.0), (-7.5, 0.92, -3.72), 42),
    ]
    for tag, name, cam, tgt, fov in shots:
        if not B.want(args, tag):
            continue
        B.choir_lights(cam, fill=9.0)
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
