"""choir_tube.glb — the Choir's seven brass resonance tubes (W3).
Contract: docs/models/ch3.md §4 choir_tube (+ choir_rack slot_mount_<k>, tube_bench bench_mount_<j>); results:
docs/models/ch3_b.md.

Seven root-level objects IA_tube_<r>, r = the meter reading 1..7; length L = (8 - r) x 0.15 (r = 1 -> 1.05 m ...
r = 7 -> 0.15 m), Ø0.05, brass end caps, a hanging eye at the top, one engraved ring near the top. No numbers.
Origin = the top of the eye (the hang point); the tube hangs along local -Y. Material M_Brass_Polished only.

All seven sit at the origin with an identity transform: the code spawns the GLB once and reparents each tube to
slot_mount_<k>, bench_mount_<j> or the in-hand anchor with an identity local transform.

    blender -b --factory-startup -P tools/blender/models/choir_tube.py [-- --no-render] [--shots=1,2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "choir_tube"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2800, 7, 1
BRASS_P = B.BRASS_P
R_TUBE, R_CAP = 0.025, 0.0265
EYE_R, EYE_W = 0.0085, 0.0028            # eye ring: centre-line radius, wire radius
Y_CAP = -(2 * EYE_R + 2 * EYE_W) + 0.003  # top of the upper cap (the eye's lower part is set into it)
RING_DEPTH = 0.045                        # engraved ring below the top of the cap
SEG = 12


def length(r):
    return (8 - r) * 0.15


def tube(r):
    L = length(r)
    yt, yb = Y_CAP, Y_CAP - L
    ring = yt - RING_DEPTH
    prof = [(0.0, yb), (0.021, yb + 0.003), (R_CAP, yb + 0.010), (R_TUBE, yb + 0.016),
            (R_TUBE, ring - 0.003), (R_TUBE - 0.0018, ring - 0.0012), (R_TUBE - 0.0018, ring + 0.0012),
            (R_TUBE, ring + 0.003),
            (R_TUBE, yt - 0.016), (R_CAP, yt - 0.010), (0.020, yt - 0.002), (0.0, yt)]
    body = B.glathe("body", prof, (0, 0, 0), (0, 1, 0), SEG, BRASS_P, smooth=50.0)
    # hanging eye: a ring in the XY plane (a peg passes through it along Z); 12 major segments put a vertex exactly at
    # the top, so the eye top is y = 0 (the hang point)
    eye = M.torus("eye", EYE_R, EYE_W, loc=(0.0, -(EYE_R + EYE_W), 0.0), major_seg=12, minor_seg=4, mat=BRASS_P)
    M.apply_transform(eye)
    A.hint(eye, 70.0)
    return B.part(f"IA_tube_{r}", [body, eye], pivot=(0.0, 0.0, 0.0))


def build():
    M.reset_scene()
    B.ensure_materials()
    tubes = [tube(r) for r in range(1, 8)]
    B.K.to_blender()
    A.finalize_uv()
    return tubes


def verify(path, tubes):
    req = [f"IA_tube_{r}" for r in range(1, 8)]
    errs = B.verify(path, req, identity=req, expect={n: (0.0, 0.0, 0.0) for n in req}, parents={n: None for n in req},
                    tris=TRI_BUDGET, surf=SURF_BUDGET, mats=MAT_BUDGET)
    for r, o in zip(range(1, 8), tubes):
        lo, hi = B.V.mesh_bounds_godot([o])
        body_len = -(Y_CAP - lo.y) if False else (Y_CAP - lo.y)
        print(f"{B.TAG} IA_tube_{r}: top {hi.y:+.4f}, bottom {lo.y:+.4f}, tube length {body_len:.4f} "
              f"(L = {length(r):.2f}), Ø {hi.x - lo.x:.4f}, tris {B.K.mesh_tris(o)}")
        if abs(body_len - length(r)) > 1e-3 or abs(hi.y) > 1e-4:
            errs.append(f"IA_tube_{r} length {body_len} / top {hi.y}")
    return errs


def qa(tubes, args):
    B.qa_begin()
    # a proxy hanging bar: the seven tubes in reading order, longest left (as the rack's staircase reads)
    bar = M.box("qa_bar", (1.2, 0.03, 0.03), loc=(0.0, 0.0, 0.03), mat=B.STEEL, bevel=0.003)
    floor = M.box("qa_floor", (4.0, 4.0, 0.02), loc=(0.0, 0.0, -1.55), mat="M_Concrete", bevel=0.0)
    wall = M.box("qa_wall", (4.0, 0.02, 3.0), loc=(0.0, 0.35, 0.0), mat="M_Paint_Green", bevel=0.0)
    for i, o in enumerate(tubes):
        o.location = B.G((i - 3) * 0.16, 0.0, 0.0)
    M.refresh()
    if B.want(args, "1"):
        B.K.clear_lights()
        B.K.light("key", "AREA", (1.2, 0.8, 2.4), 260.0, "FFE2C0", radius=1.5, target=(0.0, -0.5, 0.0))
        B.K.light("rim", "AREA", (-1.6, 0.6, -1.0), 120.0, "C8D8FF", radius=1.0, target=(0.0, -0.5, 0.0))
        B.shoot(NAME, (0.0, -0.35, 2.6), (0.0, -0.55, 0.0), 40, world=0.15)
    # 2 close-up of a tube top: the eye, the cap and the engraved ring
    if B.want(args, "2"):
        B.K.clear_lights()
        B.K.light("key", "AREA", (0.6, 0.3, 0.8), 40.0, "FFE2C0", radius=0.4, target=(-0.48, -0.05, 0.0))
        B.shoot(NAME + "_2", (-0.30, 0.02, 0.36), (-0.48, -0.05, 0.0), 30, world=0.15)
    for o in (bar, floor, wall):
        bpy.data.objects.remove(o, do_unlink=True)


def main():
    args = M.main_guard()
    tubes = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path, tubes)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(tubes, args)


main()
