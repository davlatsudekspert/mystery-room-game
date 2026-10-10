"""orrery.glb — the tiny brass Array inside Strand's box: a base with the marks 1-8, four fixed rings and four towers set from state (Chapter 4, group F; puzzle P5).
Contract: docs/models/ch4.md section 8 orrery; results: docs/models/ch4_f.md.

LOCAL FRAME: origin = the centre of the underside of the base on the stand (placed at strand_box4's `orrery_mount`), +Y up, mark 1 toward +Z (the front of the box).
The base is O 0.262 (the hall's wall r 14 at 1 : 107): ring I (outer) r 0.098 ... ring IV (inner) r 0.042 are the hall's 10.5 / 8.5 / 6.5 / 4.5 m at the same scale
(0.00933 per metre), the island r 0.028 carries the Core.
Nodes:
  orrery            M_Brass_Aged  the static model: the chamfered base (y 0 .. 0.008), four fixed ring tracks (y 0.008 .. 0.0105), eight radial index lines to the marks, the island
                    with a pedestal and a Core bead, and the mark numerals 1-8 on the rim (relief 1.6 mm, lying flat, top outward as on the hall's apron). Mark p + 1 sits at
                    azimuth 180 + 45 p (mark 1 front, 3 left (the Sun), 5 back, 7 right): a tower turned by -45 deg x p about +Y stands on mark p + 1
  orrery_tower_1..4 M_Steel_Dark  one node per ring, ORIGIN = the model centre (0, 0, 0), identity = the tower on its ring's mark 1 (at (0, ., r_n), r_I = 0.098 ...
                    r_IV = 0.042). A turned pylon with a foot and a stem; the tower's number is the stack of n small discs on its top (I = 1 disc ... IV = 4).
                    The code rotates tower n by -45 deg x p about +Y from v_align (p = 0..7)
(The contract said "a pylon at radius 0.04 n"; the hall's ring I is the OUTER ring, so tower n stands at 0.098 / 0.079 / 0.061 / 0.042: the model matches the hall.)

    blender -b --factory-startup -P tools/blender/models/orrery.py [-- --no-render] [--shots=1,2]
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
import lib_ch4_fgh as F  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "orrery"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3500, 5, 3
S = 0.098 / 10.5                                   # metres per hall metre
RADII = tuple(r * S for r in C.RING_R)             # 0.098, 0.0793, 0.0607, 0.042
R_BASE = 14.0 * S                                  # 0.1307
Y_BASE, Y_RING = 0.008, 0.0105
NUM_R = 0.1160                                     # 12.4 m at the hall's scale


def static_parts():
    out = []
    out.append(K.glathe("base", [(0.0, 0.0), (R_BASE, 0.0), (R_BASE, 0.0055), (R_BASE - 0.0025, Y_BASE), (0.0, Y_BASE)], base=(0, 0, 0), axis=(0, 1, 0),
                        segments=48, mat=BRASS, smooth=50.0))
    for R in RADII:
        out.append(K.glathe("ring", [(R + 0.0036, Y_BASE), (R + 0.0030, Y_RING), (R - 0.0030, Y_RING), (R - 0.0036, Y_BASE)], base=(0, 0, 0), axis=(0, 1, 0),
                            segments=28, mat=BRASS, smooth=50.0, cap_bottom=False, cap_top=False))
    # the eight radial lines to the marks
    b = F.MB(BRASS)
    for p in range(8):
        a = math.radians(180.0 + 45.0 * p)
        d = Vector((math.sin(a), 0.0, -math.cos(a)))
        b.bar(d * 0.031 + Vector((0, Y_BASE + 0.0006, 0)), d * (RADII[0] + 0.007) + Vector((0, Y_BASE + 0.0006, 0)), 0.0016, ref=(0, 1, 0))
    # the island, its pedestal and the Core bead
    out.append(K.glathe("island", [(0.0, Y_BASE), (0.0285, Y_BASE), (0.0275, 0.0115), (0.0, 0.0115)], base=(0, 0, 0), axis=(0, 1, 0), segments=24, mat=BRASS, smooth=50.0))
    out.append(K.glathe("core", [(0.0, 0.0115), (0.0075, 0.0115), (0.0045, 0.0165), (0.0045, 0.0185), (0.0095, 0.0215), (0.0095, 0.0265), (0.0, 0.0300)],
                        base=(0, 0, 0), axis=(0, 1, 0), segments=10, mat=BRASS, smooth=60.0))
    out.append(b.obj("lines"))
    # the numerals 1-8 on the rim, lying flat, the top outward (mark p + 1 at azimuth 180 + 45 p)
    for p in range(8):
        th = math.radians(-45.0 * p)                              # rotation about +Y of the +Z direction of mark 1
        ydir = Vector((math.sin(th), 0.0, math.cos(th)))          # radially outward: the top of the numeral
        zdir = Vector((0.0, 1.0, 0.0))
        xdir = ydir.cross(zdir)
        m = Matrix(((xdir.x, ydir.x, zdir.x, ydir.x * NUM_R), (xdir.y, ydir.y, zdir.y, Y_BASE), (xdir.z, ydir.z, zdir.z, ydir.z * NUM_R), (0, 0, 0, 1)))
        o = C.N.digit_obj(f"num{p + 1}", p + 1, 0.0145, 0.0018, BRASS, res=1)
        o.data.transform(m)
        out.append(o)
    return out


def tower_parts(n):
    r = RADII[n - 1]
    prof = [(0.0, Y_RING), (0.0058, Y_RING), (0.0058, Y_RING + 0.0018), (0.0036, Y_RING + 0.0030), (0.0026, Y_RING + 0.0042), (0.0026, Y_RING + 0.0180),
            (0.0036, Y_RING + 0.0190), (0.0036, Y_RING + 0.0200)]
    y = Y_RING + 0.0200
    for i in range(n):                                            # n discs: the tower's number
        prof += [(0.0066, y), (0.0066, y + 0.0018), (0.0026, y + 0.0018)]
        y += 0.0026
        prof += [(0.0026, y)] if i < n - 1 else []
    prof += [(0.0, y - 0.0008)]
    o = K.glathe(f"pylon{n}", prof, base=(0.0, 0.0, 0.0), axis=(0, 1, 0), segments=10, mat=STEEL, smooth=50.0)
    o.data.transform(Matrix.Translation((0.0, 0.0, r)))
    return [o]


def build():
    M.reset_scene()
    C.ensure_materials()
    body = K.part("orrery", static_parts(), pivot=(0.0, 0.0, 0.0))
    towers = [K.part(f"orrery_tower_{n}", tower_parts(n), pivot=(0.0, 0.0, 0.0)) for n in range(1, 5)]
    K.to_blender()
    C.finalize()
    return dict(body=body, towers=towers)


def verify(path):
    req = ["orrery"] + [f"orrery_tower_{n}" for n in range(1, 5)]
    expect = {n: (0.0, 0.0, 0.0) for n in req}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    M.material("M_Wood_Walnut")
    M.box("qa_table", (0.8, 0.8, 0.04), loc=K.G(0.0, -0.02, 0.0), mat="M_Wood_Walnut")
    root = K.qa_place([parts["body"]] + parts["towers"], (0.0, 0.0, 0.0), 0.0, name="qa_orr_root")
    SM = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit():
        K.clear_lights()
        K.light("key", "POINT", (0.25, 0.55, 0.35), 90.0, "FFE2C0", radius=0.06)
        K.light("fill", "POINT", (-0.4, 0.3, 0.4), 30.0, "BFD4FF", radius=0.1)
        K.light("rim", "POINT", (0.1, 0.4, -0.4), 40.0, "FFFFFF", radius=0.08)
    # the canonical alignment: towers I..IV at marks 3, 6, 8, 5 = positions 2, 5, 7, 4
    for n, p in enumerate((2, 5, 7, 4)):
        K.pose_rot(parts["towers"][n], "y", -45.0 * p)
    if C.want(args, "1"):
        cam, tgt, fov = (0.0, 0.34, 0.30), (0.0, 0.012, 0.0), 40
        lit()
        C.shoot(NAME, cam, tgt, fov, samples=SM, res=RES)
    if C.want(args, "2"):          # a low front view with all towers at mark 1 (rest)
        for n in range(4):
            K.pose_rot(parts["towers"][n], "y", 0.0)
        cam, tgt, fov = (0.05, 0.14, 0.34), (0.0, 0.02, 0.0), 38
        lit()
        C.shoot(NAME + "_2", cam, tgt, fov, samples=SM, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    F.shell_report(label=NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    F.backface_check(label=NAME, res=300)
    qa(args, parts)


main()
