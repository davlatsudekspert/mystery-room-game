"""glass_tower.glb — the glass case round the Core, the brass collar ring and the four digit wheels (Chapter 4, group D).
Contract: docs/models/ch4.md section 6 glass_tower; results: docs/models/ch4_d.md.

ISLAND FRAME: placed at (0, 2.5, 0); origin = the island centre on the platform top. Nodes:
  tower_glass    M_Glass + M_Steel_Dark  an octagonal glass case, circumradius 1.10 (Ø 2.2), y 0 .. 3.5: eight glass panels (panel
                 centres at azimuth 180 + 45 k, the south one faces the player), eight steel mullions, a base rail, a transom, a top
                 frame and a shallow pyramid cap. ORIGIN (0, 0, 0); it SINKS by sliding -3.6 along Y (into the island)
  glass_static   M_Brass_Aged  the static base ring (r 1.12 .. 1.60, y 0 .. 0.26, the glass slides through its bore), four posts at azimuth
                 45 / 135 / 225 / 315, the collar r 1.13 .. 1.35 at y 0.85 .. 1.55 built as a bottom rail, a top rail and 42 thin
                 balusters (OPEN in the middle so the cradle and the Core show through it; open at the south, 34 deg) and the digit
                 housing that closes the gap: a lock box x +-0.46, y 0.85 .. 1.55, front plate at z 1.375 with four windows over the wheels
  IA_collar_digit_1..4  M_Brass_Polished  four polished-brass digit wheels (tappable: brighter than the aged static brass) Ø 0.20 x 0.12 at x = -0.30 / -0.10 / +0.10 / +0.30, y = 1.20, z = 1.22,
                 axis local X; the digits 0-9 are 3D relief round the rim (0.058 high). ORIGIN = the axis, identity = digit 0 reads
                 upright at the front. digit d = -36 deg x d about +X (the code turns the wheel; the digit d reaches the front)

    blender -b --factory-startup -P tools/blender/models/glass_tower.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
from lib_ch4 import K, D, BRASS, BRASS_P, STEEL, GLASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "glass_tower"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 9000, 7, 4
R_GLASS = 1.10
DIGIT_X = (-0.30, -0.10, 0.10, 0.30)
AXIS_YZ = (1.20, 1.22)
WHEEL_R, DRUM_R, DIGIT_H, DIGIT_D = 0.100, 0.088, 0.060, 0.026
GAP_DEG = 17.0                                    # the collar ring is open this many degrees either side of south
INRAD = R_GLASS * math.cos(math.radians(22.5))   # 1.016: the flat panels


# ---------------------------------------------------------------------- tower_glass
def glass_parts():
    steel = bmesh.new()
    glass = bmesh.new()
    side = 2.0 * R_GLASS * math.sin(math.radians(22.5))            # 0.842
    for k in range(8):
        a_centre = 180.0 + 45.0 * k
        a_vert = a_centre + 22.5
        # glass panel: a thin slab between the mullions
        X.bm_polar_box(glass, INRAD - 0.007, INRAD + 0.007, a_centre, side - 0.075, 0.15, 3.25, bottom=True)
        # mullion at the vertex (square, a little proud)
        X.bm_polar_box(steel, R_GLASS - 0.07, R_GLASS + 0.005, a_vert, 0.075, 0.0, 3.40, bottom=True)
        # horizontal rails: base rail, transom, top frame (flat boxes along the side, rotated to the side's tangent)
        for (y0, y1, rr) in ((0.0, 0.15, 0.13), (1.70, 1.76, 0.07), (3.25, 3.40, 0.12)):
            X.bm_polar_box(steel, INRAD - rr, INRAD + 0.03, a_centre, side + 0.03, y0, y1, bottom=True)
        # cap: a shallow pyramid (one triangle per side) from the top frame to the apex at y 3.5
        a0, a1 = math.radians(a_vert - 45.0), math.radians(a_vert)
        v0 = steel.verts.new((R_GLASS * math.sin(a0), 3.40, -R_GLASS * math.cos(a0)))
        v1 = steel.verts.new((R_GLASS * math.sin(a1), 3.40, -R_GLASS * math.cos(a1)))
        ap = steel.verts.new((0.0, 3.50, 0.0))
        steel.faces.new((v1, v0, ap))
    # a finial on the apex
    steel_obj = K.obj_from_bm("gt_steel", steel, STEEL)
    glass_obj = K.obj_from_bm("gt_glass", glass, GLASS)
    return [glass_obj, steel_obj]


# ---------------------------------------------------------------------- the static brass
def collar_ring():
    """The collar: a bottom and a top rail (y 0.85 .. 0.99 and 1.41 .. 1.55, r 1.13 .. 1.35) joined by 42 thin balusters, open at the
    south for the digit housing. The middle band is open so the cradle and the Core stay visible through it."""
    a0, a1 = 180.0 + GAP_DEG, 180.0 - GAP_DEG + 360.0
    n = 56
    out = []
    for prof in ([(1.13, 0.85), (1.35, 0.85), (1.35, 0.93), (1.32, 0.96), (1.32, 0.99), (1.13, 0.99)],
                 [(1.13, 1.41), (1.32, 1.41), (1.32, 1.44), (1.35, 1.47), (1.35, 1.55), (1.13, 1.55)]):
        bm = bmesh.new()
        rings = X.bm_revolve(bm, prof, n, a0=a0, a1=a1, closed=True)
        X.fix_dir(bm, up=True)
        for end, sgn in ((0, -1), (n, 1)):
            f = bm.faces.new([r[end] for r in rings])
            f.normal_update()
            a = math.radians(a0 if end == 0 else a1)
            tang = Vector((math.cos(a), 0.0, math.sin(a))) * sgn
            if f.normal.dot(tang) < 0:
                f.normal_flip()
        out.append(K.obj_from_bm("rail", bm, BRASS))
    bm = bmesh.new()
    k = 0
    while True:
        a = 7.5 * k
        k += 1
        if a >= 360.0:
            break
        if abs((a - 180.0 + 180.0) % 360.0 - 180.0) < GAP_DEG + 2.0:
            continue
        p = X.pol(1.24, a, 0.0)
        X.bm_bar(bm, (p[0], 0.99, p[2]), (p[0], 1.41, p[2]), 0.018, ref=(1.0, 0.0, 0.0))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    out.append(K.obj_from_bm("balusters", bm, BRASS))
    return out


def static_parts():
    out = []
    # base ring (the bore r 1.12 lets the glass slide through)
    prof = [(1.12, 0.0), (1.60, 0.0), (1.60, 0.10), (1.52, 0.16), (1.52, 0.22), (1.40, 0.26), (1.12, 0.26), (1.12, 0.0)]
    bm = bmesh.new()
    X.bm_revolve(bm, prof, 48, closed=True)
    X.fix_dir(bm, up=True)
    out.append(K.obj_from_bm("base", bm, BRASS))
    for i in range(16):
        a = math.radians(22.5 * i + 11.25)
        out.append(K.rivet("rv", 0.017, (1.56 * math.sin(a), 0.10, -1.56 * math.cos(a)),
                           normal=(math.sin(a), 0.0, -math.cos(a)), mat=BRASS, segs=5))
    # four posts at the diagonals
    pprof = [(0.0, 0.26), (0.085, 0.26), (0.085, 0.32), (0.058, 0.36), (0.058, 0.85), (0.058, 1.55), (0.075, 1.57), (0.075, 1.60),
             (0.04, 1.64), (0.0, 1.66)]
    for k in range(4):
        a = 45.0 + 90.0 * k
        p = X.pol(1.24, a, 0.0)
        out.append(K.glathe("post", pprof, base=p, axis=(0, 1, 0), segments=10, mat=BRASS, smooth=60.0))
    out += collar_ring()
    # the digit housing: a lock box closing the gap, hollow behind four windows
    hb = bmesh.new()
    y0, y1 = 0.85, 1.55
    X.bm_box(hb, (-0.46, y0, 1.00), (0.46, y0 + 0.05, 1.375), bottom=True)          # bottom plate
    X.bm_box(hb, (-0.46, y1 - 0.05, 1.00), (0.46, y1, 1.375), bottom=True)          # top plate
    X.bm_box(hb, (-0.46, y0 + 0.05, 1.00), (-0.43, y1 - 0.05, 1.355))                # side walls (stop behind the front plate)
    X.bm_box(hb, (0.43, y0 + 0.05, 1.00), (0.46, y1 - 0.05, 1.355))
    X.bm_box(hb, (-0.43, y0 + 0.05, 1.00), (0.43, y1 - 0.05, 1.10))                  # back wall
    zf = 1.355
    X.bm_box(hb, (-0.46, y0 + 0.05, zf), (-0.365, y1 - 0.05, 1.375))                 # front plate: end bars
    X.bm_box(hb, (0.365, y0 + 0.05, zf), (0.46, y1 - 0.05, 1.375))
    for xc in (-0.20, 0.0, 0.20):                                                    # separators (full depth)
        X.bm_box(hb, (xc - 0.035, 1.16, 1.10), (xc + 0.035, 1.245, 1.36))
    X.bm_box(hb, (-0.365, 1.245, zf), (0.365, y1 - 0.05, 1.375))                     # visor above the windows
    X.bm_box(hb, (-0.365, y0 + 0.05, zf), (0.365, 1.160, 1.375))                     # lip below the windows
    # the axle through the wheels
    out.append(K.obj_from_bm("housing", hb, BRASS))
    out.append(D.rod("axle", (-0.44, AXIS_YZ[0], AXIS_YZ[1]), (0.44, AXIS_YZ[0], AXIS_YZ[1]), 0.012, segs=8, mat=BRASS))
    # 40 small tick studs on the front plate lip: ten per window gap would be too many; four pointer notches instead
    for xc in DIGIT_X:
        out.append(K.gbox("ptr", (xc - 0.012, 1.246, zf + 0.020), (xc + 0.012, 1.262, zf + 0.026), BRASS, 0.001))
    return out


# ---------------------------------------------------------------------- the digit wheels
def wheel(k):
    xc = DIGIT_X[k]
    base = (xc, AXIS_YZ[0], AXIS_YZ[1])
    prof = [(0.0, -0.06), (0.092, -0.06), (WHEEL_R, -0.048), (WHEEL_R, -0.040), (DRUM_R, -0.040), (DRUM_R, 0.040), (WHEEL_R, 0.040),
            (WHEEL_R, 0.048), (0.092, 0.06), (0.0, 0.06)]
    parts = [K.glathe(f"drum{k}", prof, base=base, axis=(1, 0, 0), segments=20, mat=BRASS_P, smooth=60.0)]
    for d in range(10):
        o = C.N.digit_obj(f"dg{k}_{d}", d, DIGIT_H, DIGIT_D, BRASS_P, res=1)
        o.data.transform(Matrix.Translation(base) @ Matrix.Rotation(math.radians(36.0 * d), 4, "X")
                         @ Matrix.Translation((0.0, 0.0, DRUM_R - 0.002)))
        parts.append(o)
    return K.part(f"IA_collar_digit_{k + 1}", parts, pivot=base)


def build():
    M.reset_scene()
    C.ensure_materials()
    tg = C.merge("tower_glass", glass_parts())
    st = C.merge("glass_static", static_parts())
    wheels = [wheel(k) for k in range(4)]
    K.to_blender()
    C.finalize()
    return dict(glass=tg, static=st, wheels=wheels)


def verify(path):
    req = ["tower_glass", "glass_static"] + [f"IA_collar_digit_{k}" for k in (1, 2, 3, 4)]
    expect = {"tower_glass": (0.0, 0.0, 0.0), "glass_static": (0.0, 0.0, 0.0)}
    expect.update({f"IA_collar_digit_{k + 1}": (DIGIT_X[k], AXIS_YZ[0], AXIS_YZ[1]) for k in range(4)})
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_reliquary(skip=(NAME,), sprites=True)
    X.qa_place_island([parts["glass"], parts["static"]] + parts["wheels"])
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
    shown = (3, 1, 4, 7)                                     # QA: the wheels show these digits
    for w, d in zip(parts["wheels"], shown):
        K.pose_rot(w, "x", -36.0 * d)
    X.vis("qa_cage_", False)
    if C.want(args, "1"):          # the collar view: the four digit wheels at 3 1 4 7
        cam, tgt, fov = (0.0, 3.8, 2.6), (0.0, 3.7, 1.22), 40
        lit(cam, 25.0, 0.2)
        K.light("collar_lamp", "POINT", (0.0, 4.55, 1.9), 150.0, "FFC98A", radius=0.08)          # the lamp the code gives the collar
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the glass case, the collar and its posts from the north-west above
        cam, tgt, fov = (-2.8, 5.3, 3.6), (0.0, 3.5, 0.0), 54
        lit(cam, 40.0, 0.2)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # the glass sunk (-3.6 along Y): the collar and the Core stay
        K.pose_slide(parts["glass"], (0.0, -3.6, 0.0))
        cam, tgt, fov = (-2.8, 5.3, 3.6), (0.0, 3.5, 0.0), 54
        lit(cam, 40.0, 0.2)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)

def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
