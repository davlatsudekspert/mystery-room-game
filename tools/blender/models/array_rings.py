"""array_rings.glb — the four rotating geared rims of the Array (Chapter 4, group C; the heroes of the hall floor).
Contract: docs/models/ch4.md section 5 array_rings; results: docs/models/ch4_c.md.

Origin (0, 0, 0) = the hall axis at floor level. Four rotating nodes, one mesh object each (single material M_Steel_Dark):
  ring_1..4   radii 10.5 / 8.5 / 6.5 / 4.5, ORIGIN AT THE HALL AXIS, identity at position 0. Beam 0.8 wide (r -0.40 .. +0.385
              with teeth), y 0.12 .. 0.50: a rack of 96 / 80 / 56 / 40 trapezoid teeth (pitch 0.69 / 0.67 / 0.73 / 0.71 m) on
              the outer edge, a stepped rim, two machined grooves on the inner wall, eight DEEP INDEX NOTCHES (0.20 wide,
              0.27 deep, full height) cut into the gaps at azimuths 0, 45, ... 315 (the position azimuths) with an arrow pad
              on top pointing at each, and rows of rivets. Position p = -45 deg x p about +Y.
  tower_mount_1..4   child empty of ring_n at (0, 0.5, r_n), identity: the code parents the mirror_tower instance here.

    blender -b --factory-startup -P tools/blender/models/array_rings.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, STEEL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "array_rings"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 14000, 4, 1
RADII = C.RING_R
TEETH = (96, 80, 56, 40)


def build():
    M.reset_scene()
    C.ensure_materials()
    rings = []
    for n, (r_, t) in enumerate(zip(RADII, TEETH), start=1):
        o = X.toothed_ring(f"ring_{n}_mesh", r_, t, STEEL)
        rings.append(K.part(f"ring_{n}", [o], pivot=(0.0, 0.0, 0.0)))
        K.empty(f"tower_mount_{n}", (0.0, 0.5, r_))
    K.to_blender()
    for n, ring in enumerate(rings, start=1):
        K.parent(bpy.data.objects[f"tower_mount_{n}"], ring)
    C.finalize()
    return dict(rings=rings)


def verify(path):
    req = [f"ring_{n}" for n in range(1, 5)] + [f"tower_mount_{n}" for n in range(1, 5)]
    expect = {f"ring_{n}": (0.0, 0.0, 0.0) for n in range(1, 5)}
    expect.update({f"tower_mount_{n}": (0.0, 0.5, RADII[n - 1]) for n in range(1, 5)})
    parents = {f"tower_mount_{n}": f"ring_{n}" for n in range(1, 5)}
    errs = C.verify(path, required=req, identity=req, expect=expect, parents=parents, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in range(1, 5):
        lo, hi = C.bounds([f"ring_{n}"])
        print(f"{C.TAG} ring_{n} bounds {lo} .. {hi}")
        print(f"{C.TAG} ring_{n} tris {K.mesh_tris(bpy.data.objects[f'ring_{n}'])}")
    return errs


# ====================================================================== QA
def qa_tower_proxy(n, r_):
    """A stand-in tower (QA only) at mark 1: plinth, post, head."""
    qb = K.V._qbox
    qb("qa_plinth", (-0.35, 0.5, r_ - 0.35), (0.35, 0.68, r_ + 0.35), "M_Brass_Aged")
    qb("qa_post", (-0.06, 0.68, r_ - 0.06), (0.06, 1.7, r_ + 0.06), "M_Brass_Aged")
    qb("qa_head", (-0.13, 1.6, r_ - 0.13), (0.13, 1.95, r_ + 0.13), "M_Chrome")


def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0)])
    X.qa_core()
    for n, r_ in enumerate(RADII, start=1):
        qa_tower_proxy(n, r_)
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # the bridge view: the whole Array
        cam, tgt, fov = C.view("bridge")
        lit(cam, 80.0, 0.3)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a low three-quarter closeup of the teeth, notches and arrow pads (ring I, II)
        cam, tgt, fov = (-2.2, 1.35, 11.9), (0.4, 0.3, 8.9), 54
        lit(cam, 100.0, 0.35)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # from above at an index notch (ring I, mark 3 west) with a ring turned two stops
        for n in (2, 3):
            ring = parts["rings"][n - 1]
            K.pose_rot(ring, "y", -90.0)
        cam, tgt, fov = (-8.0, 3.4, 4.0), (-9.4, 0.2, 0.0), 56
        lit(cam, 120.0, 0.4)
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
