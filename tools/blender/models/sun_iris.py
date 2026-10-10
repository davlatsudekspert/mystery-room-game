"""sun_iris.glb — the iris of six overlapping brass leaves in front of the Sun (Chapter 4, group E; puzzle P4).
Contract: docs/models/ch4.md section 7 sun_iris; results: docs/models/ch4_e.md.

LOCAL FRAME (the iris frame): origin = the iris centre, leaves in the XY plane, the front is +Z. Placed at (-11.8, 1.8, 0) with yaw 90 so
local +Z faces +X, into the hall. Nodes:
  iris_frame   M_Steel_Dark  a back ring (r 0.74 .. 1.20, z -0.03 .. 0), a front bezel (r 1.00 .. 1.22, z 0.075 .. 0.13) the leaves slide under,
               six radial guide rails (r 1.2 .. 1.9 on each leaf's centreline) with end stops and latch brackets (r 1.85 .. 1.95), rivets
  IA_leaf_1..6 M_Brass_Aged  six wedge leaves, each 88 deg = 60 deg + 14 deg of overlap on each side, outer radius 0.86 (a rim, a centre rib, a pull
               knob at r 0.52, rivets). Leaf k is centred at CLOCKWISE 60 deg x (k - 1) from up (+Y) seen from the front.
               ORIGIN = (0, 0, z_k) in the iris frame, identity rotation, mesh built round that origin. STACK OFFSET z = 0.012 x (5 - rank), rank 0 =
               the top of the stack; the GLB ships the canonical stack [3, 6, 1, 5, 2, 4] (top -> bottom) baked: z = 0.036 / 0.012 / 0.060 / 0.000 /
               0.024 / 0.048 for leaves 1..6. The code overrides each leaf's position.z from v_iris. A leaf OPENS by sliding 0.95 radially
               outward: position.xy = 0.95 x (sin a, cos a), a = 60 deg x (k - 1), and latches against its end stop.

    blender -b --factory-startup -P tools/blender/models/sun_iris.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, D, BRASS, STEEL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "sun_iris"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 7, 2
STACK = [3, 6, 1, 5, 2, 4]                       # canonical order, top -> bottom
LEAF_R = 0.86
HALF_ANGLE = 44.0
THICK = 0.010


def z_of(k):
    rank = STACK.index(k)
    return 0.012 * (5 - rank)


def leaf_mesh(k):
    """Leaf k in the iris frame: centred on up (+Y) then turned clockwise 60 (k-1) deg, built at z = z_k."""
    z0 = z_of(k)
    bm = bmesh.new()
    n = 12
    arc = [(LEAF_R * math.sin(math.radians(-HALF_ANGLE + 2 * HALF_ANGLE * i / n)), LEAF_R * math.cos(math.radians(-HALF_ANGLE + 2 * HALF_ANGLE * i / n)))
           for i in range(n + 1)]
    apex_t, apex_b = bm.verts.new((0.0, 0.0, z0 + THICK)), bm.verts.new((0.0, 0.0, z0))
    top = [bm.verts.new((x, y, z0 + THICK)) for (x, y) in arc]
    bot = [bm.verts.new((x, y, z0)) for (x, y) in arc]
    for i in range(n):
        X.bm_face(bm, (apex_t, top[i + 1], top[i]), (0, 0, 1))
        X.bm_face(bm, (bot[i], bot[i + 1], top[i + 1], top[i]), (math.sin(math.radians(-HALF_ANGLE + HALF_ANGLE * 2 * (i + 0.5) / n)),
                                                                 math.cos(math.radians(-HALF_ANGLE + HALF_ANGLE * 2 * (i + 0.5) / n)), 0))
    X.bm_face(bm, (apex_b, bot[0], top[0], apex_t), (-math.cos(math.radians(HALF_ANGLE)), -math.sin(math.radians(HALF_ANGLE)), 0))
    X.bm_face(bm, (apex_b, apex_t, top[n], bot[n]), (math.cos(math.radians(HALF_ANGLE)), -math.sin(math.radians(HALF_ANGLE)), 0))
    # a raised rim along the outer arc and a centre rib
    zt = z0 + THICK
    ri, ro = LEAF_R - 0.034, LEAF_R - 0.004
    rim = []
    for i in range(n + 1):
        a = math.radians(-HALF_ANGLE + 2 * HALF_ANGLE * i / n)
        rim.append((bm.verts.new((ri * math.sin(a), ri * math.cos(a), zt)), bm.verts.new((ro * math.sin(a), ro * math.cos(a), zt)),
                    bm.verts.new((ri * math.sin(a), ri * math.cos(a), zt + 0.006)), bm.verts.new((ro * math.sin(a), ro * math.cos(a), zt + 0.006))))
    for i in range(n):
        a, b = rim[i], rim[i + 1]
        X.bm_face(bm, (a[2], a[3], b[3], b[2]), (0, 0, 1))                                    # top of the rim
        am = math.radians(-HALF_ANGLE + 2 * HALF_ANGLE * (i + 0.5) / n)
        X.bm_face(bm, (a[1], a[3], b[3], b[1]), (math.sin(am), math.cos(am), 0))             # outer wall
        X.bm_face(bm, (a[0], b[0], b[2], a[2]), (-math.sin(am), -math.cos(am), 0))           # inner wall
    rib = bmesh.new()
    X.bm_bar(rib, (0.0, 0.14, zt + 0.0025), (0.0, 0.78, zt + 0.0025), 0.022, ref=(0, 0, 1))
    bmesh.ops.recalc_face_normals(rib, faces=list(rib.faces))
    rib_me = bpy.data.meshes.new("rib_tmp")
    rib.to_mesh(rib_me)
    rib.free()
    bm.from_mesh(rib_me)
    bpy.data.meshes.remove(rib_me)
    for sg in (-1, 1):                                                                       # rivets near the arc corners
        a = math.radians(sg * 33.0)
        X.bm_dome(bm, (0.76 * math.sin(a), 0.76 * math.cos(a), zt), 0.014, 0.012, segs=5, normal=(0, 0, 1))
    for r_ in (0.26,):
        X.bm_dome(bm, (0.0, r_, zt), 0.014, 0.012, segs=5, normal=(0, 0, 1))
    leaf = K.obj_from_bm(f"leaf_m{k}", bm, BRASS)
    knob = K.glathe(f"knob{k}", [(0.0, zt), (0.040, zt), (0.040, zt + 0.012), (0.027, zt + 0.030), (0.0, zt + 0.037)],
                    base=(0.0, 0.52, 0.0), axis=(0, 0, 1), segments=10, mat=BRASS, smooth=60.0)
    # the knob profile is relative to base: shift so its z is absolute
    parts = [leaf, knob]
    ang = -60.0 * (k - 1)                                         # clockwise seen from the front (+Z)
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))
    return parts


def frame_parts():
    out = []
    back = K.glathe("back", [(0.74, -0.03), (1.20, -0.03), (1.20, 0.0), (0.74, 0.0), (0.74, -0.03)], base=(0, 0, 0), axis=(0, 0, 1),
                    segments=64, mat=STEEL, smooth=50.0, cap_bottom=False, cap_top=False)
    front = K.glathe("front", [(1.00, 0.075), (1.22, 0.075), (1.22, 0.115), (1.16, 0.135), (1.00, 0.135), (1.00, 0.075)], base=(0, 0, 0),
                     axis=(0, 0, 1), segments=64, mat=STEEL, smooth=50.0, cap_bottom=False, cap_top=False)
    out += [back, front]
    sb = bmesh.new()
    for k in range(6):
        a = math.radians(60.0 * k)
        rad = Vector((math.sin(a), math.cos(a), 0.0))
        tan = Vector((math.cos(a), -math.sin(a), 0.0))
        def pt(r, t, z):
            p = rad * r + tan * t
            return (p.x, p.y, z)
        # guide rail (under the leaf's path) and the end stop + latch bracket
        X.bm_bar(sb, pt(1.2, 0, -0.015), pt(1.92, 0, -0.015), 0.12, ref=(0, 0, 1))
        for t in (-0.07, 0.07):
            X.bm_bar(sb, pt(1.86, t, 0.02), pt(1.94, t, 0.02), 0.045, ref=(0, 0, 1))
        X.bm_bar(sb, pt(1.86, -0.07, 0.065), pt(1.86, 0.07, 0.065), 0.03, ref=(0, 0, 1))
        for r_ in (1.35, 1.62):                                  # hold-down clips either side of the path
            for t in (-0.15, 0.15):
                X.bm_bar(sb, pt(r_ - 0.03, t, 0.000), pt(r_ + 0.03, t, 0.000), 0.05, ref=(0, 0, 1))
                X.bm_bar(sb, pt(r_ - 0.03, t * 0.6, 0.020), pt(r_ + 0.03, t * 0.6, 0.020), 0.03, ref=(0, 0, 1))
    bmesh.ops.recalc_face_normals(sb, faces=list(sb.faces))
    for i in range(24):
        a = math.radians(15.0 * i + 7.5)
        X.bm_dome(sb, (1.11 * math.sin(a), 1.11 * math.cos(a), 0.135), 0.018, 0.016, segs=5, normal=(0, 0, 1))
    out.append(K.obj_from_bm("rails", sb, STEEL))
    return out


def build():
    M.reset_scene()
    C.ensure_materials()
    frame = K.part("iris_frame", frame_parts(), pivot=(0.0, 0.0, 0.0))
    leaves = [K.part(f"IA_leaf_{k}", leaf_mesh(k), pivot=(0.0, 0.0, z_of(k))) for k in range(1, 7)]
    K.to_blender()
    C.finalize()
    return dict(frame=frame, leaves=leaves)


def verify(path):
    req = ["iris_frame"] + [f"IA_leaf_{k}" for k in range(1, 7)]
    expect = {"iris_frame": (0.0, 0.0, 0.0)}
    expect.update({f"IA_leaf_{k}": (0.0, 0.0, z_of(k)) for k in range(1, 7)})
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    C.qa_import("sun_lamp", (-13.0, 1.8, 0.0), 0.0, prefix="qa_sun_")
    C.qa_import("sun_pedestal", (-12.0, 0.0, 2.4), 90.0, prefix="qa_ped_")
    K.qa_place([parts["frame"]] + parts["leaves"], (-11.8, 1.8, 0.0), 90.0, name="qa_iris_root")
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False, core=False)
        K.light("sun_arc", "POINT", (-12.4, 1.8, 0.0), 60000.0, "FFF6E8", radius=0.2)
    if C.want(args, "1"):          # the iris view, closed: the stack reads from the overlaps
        cam, tgt, fov = (-8.8, 1.8, 0.0), (-11.8, 1.8, 0.0), 40
        lit(cam, 60.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the top of the stack lifted: leaves 3 and 6 slid out 0.95
        for k in (3, 6):
            a = math.radians(60.0 * (k - 1))
            K.pose_slide(parts["leaves"][k - 1], (0.95 * math.sin(a), 0.95 * math.cos(a), 0.0))
        cam, tgt, fov = (-8.8, 2.4, -1.6), (-11.8, 1.8, 0.0), 46
        lit(cam, 60.0, 0.25)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)


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
