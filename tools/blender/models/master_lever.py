"""master_lever.glb — the master lever unit on the desk's right wing (Chapter 4, group B): a base plate with two cheek plates
carrying the quadrant, an upper stop bar, and a big brass knife-switch lever with a turned grip, a counterweight tail and
a pivot hub. "Down since 1979": at rest the lever points toward the operator. Contract: docs/models/ch4.md section 4
master_lever; results: docs/models/ch4_b.md.

At the desk's lever_mount (1.28, 2.5 + 0.95, 13.15), yaw 0. Origin = the unit's base centre on the wing pad (y 0 = the pad top).
Front (+Z) toward the operator. The lever pivots at P = (0, 0.24, -0.12).
  master_lever_body  M_Steel_Painted  base plate 0.40 x 0.55 x 0.03, two cheek plates (x +-0.07 .. 0.095) with the quadrant lobe
                     (radius 0.19 about P), an upper stop bar at 80 deg
  IA_master_lever    M_Brass_Aged     ORIGIN = P, length 0.55 (blade 0.40 + grip 0.16), counterweight tail 0.14, hub with bolt
                     heads. REST = DOWN: the lever points +Z, 6 deg below horizontal baked into the mesh (node rotation identity).
                     LIFTED = -80 deg about +X (the grip rises and moves away from the operator).

    blender -b --factory-startup -P tools/blender/models/master_lever.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, B, D, PAINT, BRASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "master_lever"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3000, 2, 2
PIV = (0.0, 0.24, -0.12)
REST_TILT = 6.0                                   # degrees below horizontal at rest


def cheek_profile():
    z0, y0 = PIV[2], PIV[1]
    pts = [(-0.25, 0.03), (0.22, 0.03), (0.22, 0.15)]
    for k in range(0, 10):                        # the lobe's arc, theta -10 .. 130 degrees (from +Z toward +Y)
        th = math.radians(-10.0 + 140.0 * k / 9.0)
        pts.append((z0 + 0.19 * math.cos(th), y0 + 0.19 * math.sin(th)))
    pts[-1] = (-0.25, pts[-1][1])
    return pts


def body_parts():
    out = [K.gbox("plate", (-0.20, 0.0, -0.275), (0.20, 0.03, 0.275), PAINT, 0.004)]
    prof = cheek_profile()
    for (xa, xb) in ((0.07, 0.095), (-0.095, -0.07)):
        out.append(B.prism_x("cheek", prof, xa, xb, PAINT))
    th = math.radians(80.0)
    sz, sy = PIV[2] + 0.20 * math.cos(th), PIV[1] + 0.20 * math.sin(th)
    out.append(K.gbox("stop", (-0.07, sy - 0.02, sz - 0.02), (0.07, sy + 0.02, sz + 0.02), PAINT, 0.004))
    for sx in (-1, 1):
        for sz_ in (-1, 1):
            out.append(K.hexbolt("bolt", 0.014, (sx * 0.16, 0.03, sz_ * 0.235), normal=(0, 1, 0), mat=PAINT))
    return out


def lever_parts():
    px, py, pz = PIV
    out = []
    out.append(K.gcyl("hub", 0.032, -0.085, 0.085, base=(px, py, pz), axis=(1, 0, 0), segments=14, mat=BRASS, chamfer=0.004))
    for sx in (-1, 1):
        out.append(K.gcyl("bolt", 0.024, 0.0, 0.016, base=(px + sx * 0.085, py, pz), axis=(sx, 0, 0), segments=10, mat=BRASS, chamfer=0.003))
    out.append(K.gbox("blade", (-0.02, py - 0.009, pz), (0.02, py + 0.009, pz + 0.40), BRASS, 0.004))
    out.append(K.gbox("tail", (-0.015, py - 0.008, pz - 0.14), (0.015, py + 0.008, pz), BRASS, 0.003))
    out.append(M.sphere("weight", 0.038, loc=(px, py, pz - 0.15), segments=12, rings=8, mat=BRASS))
    grip = K.glathe("grip", [(0.0, 0.0), (0.016, 0.0), (0.020, 0.012), (0.020, 0.025, "k"), (0.024, 0.032), (0.024, 0.045, "k"),
                             (0.020, 0.052), (0.020, 0.115, "k"), (0.027, 0.125), (0.031, 0.142), (0.022, 0.158), (0.0, 0.165)],
                    base=(px, py, pz + 0.38), axis=(0, 0, 1), segments=16, mat=BRASS, smooth=60.0, knurl=0.0015)
    out.append(grip)
    tilt = Matrix.Translation(PIV) @ Matrix.Rotation(math.radians(REST_TILT), 4, "X") @ Matrix.Translation(-Vector(PIV))
    for o in out:                                   # bake the 6 deg rest tilt about the pivot BEFORE the origin moves there
        o.data.transform(tilt)
    return K.part("IA_master_lever", out, pivot=PIV)


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("master_lever_body", body_parts())
    lever = lever_parts()
    K.to_blender()
    C.finalize()
    return dict(body=body, lever=lever)


def verify(path):
    req = ["master_lever_body", "IA_master_lever"]
    expect = {"IA_master_lever": PIV}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa_desk_wing():
    qb = K.V._qbox
    qb("qa_wing", (0.95, 2.5 + 0.12, 12.69), (1.55, 2.5 + 0.95, 13.61), "M_Steel_Painted")
    qb("qa_desk", (-1.55, 2.5 + 0.12, 12.69), (0.95, 2.5 + 0.95, 13.61), "M_Steel_Painted")
    qb("qa_slope", (-0.8, 2.5 + 0.95, 12.69), (0.95, 2.5 + 1.45, 13.3), "M_Steel_Painted")


def qa(args, parts):
    C.qa_begin()
    C.qa_floor_nonormal("bridge_deck")
    C.qa_hall(shell=True, extra=[("bridge", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0)])
    C.qa_floor_nonormal("qa_sh_hall_floor")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))
    qa_desk_wing()
    K.qa_place([parts["body"], parts["lever"]], (1.28, 2.5 + 0.95, 13.15), 0.0, name="qa_place_lever")
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    cam, tgt, fov = (1.75, 4.25, 14.55), (1.28, 3.8, 13.05), 36
    if C.want(args, "1"):          # at rest: down since 1979
        lit(cam, 90.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # lifted
        K.pose_rot(parts["lever"], "x", -80.0)
        lit(cam, 90.0, 0.25)
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
