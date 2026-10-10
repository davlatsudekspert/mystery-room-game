"""Light echo: Dr. Leyla Rahimova in 1998 carrying the crystal lens from the Core to the cradle (Chapter 4 `leyla_echo_lens`).

The same figure as echo_leyla_1998_lift (the face lineage, field coat, belt, patch pockets and boots of echo_leyla_1998), at the
budget of this file (<= 16,000 triangles: three key poses of about 5,300). Each pose is ONE closed mesh (M_Echo), origin on the
floor between her feet, the figure faces Godot +Z, -X = her right. The lens lies on her RIGHT palm, standing on its rim and
leaning back against her fingers, its face toward her (the same attitude it has in the cradle's `lens_mount`).

Output: game/assets/models/echo_leyla_1998_lens.glb
  pose_walk    a stride, LEFT foot forward, right foot back with the heel raised; the lens on the right palm in front of the
               chest (lens centre figure (-0.12, 1.15, 0.36)); the left arm swings back.
  pose_walk_b  the opposite stride (RIGHT foot forward); the left arm swings forward. Alternate pose_walk / pose_walk_b
               (a step every ~0.35 s) while the code moves her from the Core to the cradle.
  pose_seat    stopped at the cradle, the right arm extended: the lens centre at figure (-0.10, 1.3135, 0.45) (its top rim
               at y 1.345 is the contract's right-hand point (-0.10, 1.35, 0.45)), the palm under its rim, the left palm
               cupped beside it.
  lens_mount_walk, lens_mount_walk_b, lens_mount_seat   empty, child of its pose, at the lens centre, rotated so the lens's own +Z
               (the Institute's mark side) points toward her, tilted 24.3 deg up: the same orientation as `cradle`'s `lens_mount`
               (`crystal_lens.glb` parented to it stands on her palm). pose_seat: (-0.10, 1.3135, 0.45).
Run: blender -b --factory-startup -P tools/blender/models/echo_leyla_1998_lens.py [-- --no-render] [-- --only pose_seat]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

import lib_ch4_echo as C  # noqa: E402
from lib_ch4_echo import E, H, L, mrlib, vec  # noqa: E402

NAME = "echo_leyla_1998_lens"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 8000, 16000            # contract: <= 8,000 per pose, <= 16,000 per file
LEY = H.load_model("echo_leyla_1998")
LEY.TRIS = dict(body=2750, hand=320, head=1700)
LEY.VOXEL = 0.0038
H.make_pose = C.make_pose
LENS_R = 0.0348                                     # crystal_lens.glb: Ø 0.0696
YP = Vector((0.0, 0.9114, 0.4116))                  # the lens plane's "up" in the figure frame (face tilted 24.3 deg up)
NP = Vector((0.0, 0.4116, -0.9114))                 # the lens face normal, toward her (figure frame)
SEAT_LENS = (-0.10, 1.3135, 0.45)                   # the lens centre: with her origin at world (-0.10, 2.5, 1.0766), yaw 180
WALK_LENS = (-0.12, 1.15, 0.36)                     # it is exactly the cradle's lens_mount (0, 3.8135, 0.6266)
SEAT_PALM = tuple(Vector(SEAT_LENS) - YP * LENS_R)  # its lowest rim point rests on the palm
WALK_PALM = tuple(Vector(WALK_LENS) - YP * LENS_R)


def stride_legs(sp, key, front, stride=0.235):
    parts = []
    zh = sp.z_hip - 0.04
    for s in (1, -1):
        hip = sp.point(zh, (s * 0.090, 0.0, 0.0))
        if s == front:
            shp, ank = H.shoe_on(f"{key}_boot{s}", (s * 0.098, stride), -3.0 * s, heel=0.020, scale=0.95, boot=True)
        else:
            shp, ank = H.shoe_on(f"{key}_boot{s}", (s * 0.098, -stride * 0.85), 3.0 * s, heel=0.020, scale=0.95,
                                 toes_down=30.0, boot=True)
        knee = E.ik2(hip, ank, 0.430, 0.405, hip + Vector((0.0, 1.0, 0.10)))
        parts += shp
        parts += H.bent_leg(f"{key}_leg{s}", hip, knee, ank, r_thigh=0.070, r_knee=0.055, r_shin=0.054, r_hem=0.056)
    return parts


def palm_hand(key, side, palm_g, lens=True):
    """A flat, slightly cupped hand, palm up, centre at a Godot figure-frame point (the lens stands on it)."""
    palm = H.g2b(palm_g)
    right = side == 1
    hp, wr, _ = H.flat_hand(f"{key}_hand{'R' if right else 'L'}", palm, (0.10 * (-1 if right else 1), 0.97, 0.06),
                            (0.0, 0.0, 1.0), right, LEY.HAND_S, curl=2.2, width=0.075, finger_r=0.0082)
    return hp, wr


def stand_pose(key, front, palm_g, left_back, yaw_chest, tilt, head):
    sp = L.Spine(hip_xy=(0.0, -0.015), neck_xy=(-0.004, 0.065), z_hip=0.830, z_neck=1.385, yaw_hip=8.0 * front,
                 yaw_chest=yaw_chest, z_twist0=0.86, z_twist1=1.22)
    parts = LEY.coat(sp, key) + stride_legs(sp, key, front)
    sh = LEY.shoulders(sp)
    hr, wr_r = palm_hand(key, 1, palm_g)
    sw = 0.30 * (1 if left_back else -1)
    wr_l = sh[-1] + Vector((-0.040, -sw, -0.455))
    arms = {1: (wr_r, sh[1] + Vector((0.40, -0.30, -0.40))), -1: (wr_l, sh[-1] + Vector((-0.40, -0.40 if left_back else 0.20, -0.30)))}
    obj = LEY.assemble(key, sp, parts, sh, arms, {1: hr, -1: LEY.relaxed(key, False)}, LEY.head_kw(sp, 0.0, head, 0.0, tilt=tilt))
    return obj


def pose_walk():
    return stand_pose("pose_walk", -1, WALK_PALM, True, 9.0, 14.0, -12.0)


def pose_walk_b():
    return stand_pose("pose_walk_b", 1, WALK_PALM, False, -9.0, 14.0, -12.0)


def pose_seat():
    key = "pose_seat"
    sp = L.Spine(hip_xy=(0.0, -0.030), neck_xy=(-0.004, 0.075), z_hip=0.865, z_neck=1.410, yaw_hip=-6.0, yaw_chest=-4.0,
                 z_twist0=0.90, z_twist1=1.24)
    feet = {1: (0.105, -0.010, -6.0), -1: (-0.100, 0.060, 10.0)}
    parts = LEY.coat(sp, key) + LEY.standing_legs(sp, key, feet)
    sh = LEY.shoulders(sp)
    hr, wr_r = palm_hand(key, 1, SEAT_PALM)
    hl, wr_l, _ = H.flat_hand(f"{key}_handL", H.g2b((0.00, 1.24, 0.40)), (0.10, 0.97, 0.06), (0.0, 0.0, 1.0), False,
                              LEY.HAND_S, curl=2.2, width=0.075, finger_r=0.0082)
    arms = {1: (wr_r, sh[1] + Vector((0.40, -0.35, -0.20))), -1: (wr_l, sh[-1] + Vector((-0.40, -0.30, -0.25)))}
    return LEY.assemble(key, sp, parts, sh, arms, {1: hr, -1: hl}, LEY.head_kw(sp, -4.0, 8.0, 0.0, tilt=10.0))


POSES = {"pose_walk": pose_walk, "pose_walk_b": pose_walk_b, "pose_seat": pose_seat}
PALMS = {"pose_walk": WALK_PALM, "pose_walk_b": WALK_PALM, "pose_seat": SEAT_PALM}


def lens_mount(obj, palm_g, name):
    """Empty at the lens centre, rotated so the lens's +Z = NP and its +Y = YP (Godot figure frame)."""
    c = Vector(palm_g) + YP * LENS_R
    X = YP.cross(NP)
    Rg = Matrix((X, YP, NP)).transposed()               # columns = the lens axes in the figure frame
    Cm = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))      # Blender (export orientation) -> glTF / Godot
    Rb = Cm.inverted() @ Rg @ Cm
    e = mrlib.empty(name, loc=(c.x, -c.z, c.y))
    e.rotation_euler = Rb.to_euler()
    mrlib.set_parent(e, obj)
    return Rg.to_quaternion()


# ------------------------------------------------------------------ QA
def island_context():
    if not L.import_ctx("cradle", (0.0, 2.5, 0.0), 0.0):
        L.proxy("cradle", (0.4, 0.3, 0.2), (0.0, 3.8, 0.62), color="B08D57")
    L.import_ctx("core_crystal", (0.0, 2.5, 0.0), 0.0)
    L.import_ctx("core_pedestal", (0.0, 2.5, 0.0), 0.0)
    L.import_ctx("crystal_lens", (0.0, 2.5 + 1.3135, 0.6266), 0.0)
    L.proxy("deck", (6.0, 0.05, 6.0), (0.0, 2.475, 1.0), color="3B3E42")


def renders(by):                                    # (QA)
    names = [n for n in POSES if n in by]
    objs = [by[n] for n in names]
    for o, x in zip(objs, [(-1.0, 0.0, 1.0)[i] for i in range(len(objs))]):
        o.location.x = x
    path = H.L.ghost("echo_leyla_1998_lens", objs, (0.0, -4.4, 1.25), (0.0, 0.0, 0.85), lens=40, res=(1100, 640), samples=24)
    for o in objs:
        o.location.x = 0.0
    if "pose_seat" in by:
        # at the cradle, from the contract's `cradle` camera (0, 4.6, 2.4) -> (0, 3.6, 0.5): she stands on the player's side
        # (south of the cradle) facing north: origin (-0.10, 2.5, 1.0766), yaw 180
        C.show_only(objs, [by["pose_seat"]])
        H.context("echo_leyla_1998_lens_2", [by["pose_seat"]], by["pose_seat"], (-0.10, 2.5, 1.0766), 180.0, island_context,
                  (1.3, 4.2, 2.4), (0.0, 3.7, 0.7), fov=52, res=(960, 640), samples=24)
        C.show_only(objs, objs)


def main():
    mrlib.reset_scene()
    by = {}
    for nm, fn in POSES.items():
        if ONLY and nm not in ONLY:
            continue
        o = fn()
        H.turn(o)
        o.data.name = o.name
        by[nm] = o
    empties = []
    for nm, o in by.items():
        empties.append("lens_mount_" + nm[len("pose_"):])
        lens_mount(o, PALMS[nm], empties[-1])
    path = mrlib.export_glb(NAME)
    H.verify(path, {k: POSE_BUDGET for k in by}, empties=empties, file_budget=FILE_BUDGET)
    if "pose_seat" in by:
        H.contact_report("palm under the lens (pose_seat)", by["pose_seat"], SEAT_PALM, radius=0.05)
    if RENDER:
        renders(by)


if __name__ == "__main__":
    main()
