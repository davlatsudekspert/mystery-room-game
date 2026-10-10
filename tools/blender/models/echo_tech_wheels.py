"""Light echoes: the two 1979 technicians at the bridge's handwheels (Chapter 4 `tech_wheels`).

Two root-level figures, each ONE closed mesh (M_Echo), origin on the floor between the feet, the figure faces Godot +Z, -X = its
right. The room puts them on `echo_mount_wheels_1` (-2.9, 2.5, 13.3) and `echo_mount_wheels_2` (2.9, 2.5, 13.3), both yaw 180
(they face north to the rail); each stands between two wheels, which are 0.70 to either side and 0.65 ahead (the wheel axis is
figure (+-0.70, 1.30, 0.65), the rim's centre-line radius 0.245, so the nearest rim point is 0.455 to the side). Neither can
turn a wheel from where he stands, so both are frozen REACHING: leaning in, one arm straight out, the fingertips on the rim.
Output: game/assets/models/echo_tech_wheels.glb
  tech_a   at mount 1 (between wheels I and II): a woman in a knee-length lab coat (the scientists' bob), torso turned 38 deg to
           her right, RIGHT hand open on wheel II's upper rim (rim point figure (-0.54, 1.49, 0.65)), a clipboard held to her
           chest in the left hand, eyes on the dial.
  tech_b   at mount 2 (between wheels III and IV): a man in a lab coat (a short crop), torso turned 32 deg to his left, LEFT hand
           open on wheel III's upper rim (rim point figure (0.54, 1.49, 0.65)), the right hand on his hip, eyes on the dial.
  rim_touch_tech_a / rim_touch_tech_b  empty, child of its figure, identity rotation, at the rim point the fingertips rest on.
Budget: <= 6,000 triangles per figure, <= 12,000 per file.
Run: blender -b --factory-startup -P tools/blender/models/echo_tech_wheels.py [-- --no-render] [-- --only tech_a]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch4_echo as C  # noqa: E402
import lib_ch4_echo_staff as S  # noqa: E402
from lib_ch4_echo import E, H, L, mrlib, vec  # noqa: E402

NAME = "echo_tech_wheels"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
BUDGET, FILE_BUDGET = 6000, 12000
VOXEL = 0.0036
WHEEL = Vector((0.70, 1.30, 0.65))               # |x|, y, z of a wheel's axis in the figure frame; rim radius 0.245
RIM_R = 0.245
HAND = 0.150                                      # wrist -> fingertip reach used to place a touching hand
MOUNTS = {"tech_a": ((-2.9, 2.5, 13.3), 180.0), "tech_b": ((2.9, 2.5, 13.3), 180.0)}
RIM_A = (-(WHEEL.x - RIM_R * math.cos(math.radians(50))), WHEEL.y + RIM_R * math.sin(math.radians(50)), WHEEL.z)
RIM_B = (WHEEL.x - RIM_R * math.cos(math.radians(50)), WHEEL.y + RIM_R * math.sin(math.radians(50)), WHEEL.z)


def touching_hand(key, side, sh, target_b, scale, curls, wrist_max=0.55):
    """An open hand whose fingertips land on `target_b`: wrist = target - F * HAND, F pointing from the shoulder."""
    F = (target_b - sh).normalized()
    wr = target_b - F * HAND * scale
    if (wr - sh).length > wrist_max:
        wr = sh + (wr - sh).normalized() * wrist_max
    N = L.ortho(Vector((0.35 * side, 0.0, -1.0)), F)
    parts, _info = H.hand(f"{key}_hand{'R' if side == 1 else 'L'}", wr, F, N, side == 1, curls, spread=[4, 0, -3, -7],
                          scale=scale, width=0.078, finger_r=0.0084)
    return parts, wr


def tech_a():
    key = "tech_a"
    sp = L.Spine(hip_xy=(0.0, -0.030), neck_xy=(-0.030, 0.210), z_hip=0.860, z_neck=1.390, yaw_hip=-12.0, yaw_chest=-38.0,
                 z_twist0=0.90, z_twist1=1.24)
    parts = S.woman_coat(key, sp)
    knees = {1: Vector((0.090, 0.020, 0.470)), -1: Vector((-0.082, 0.040, 0.462))}
    parts += S.woman_legs(key, {1: ((0.100, 0.030), -6.0), -1: ((-0.100, -0.030), 14.0)}, knees)
    sh_r = sp.point(sp.z_neck - 0.080, (0.155, 0.010, 0.0))
    sh_l = sp.point(sp.z_neck - 0.080, (-0.155, 0.010, 0.0))
    tgt = H.g2b(RIM_A)
    hand_r = touching_hand(key, 1, sh_r, tgt, 0.95, [(14, 22, 10), (16, 24, 12), (20, 28, 14), (24, 30, 16)], wrist_max=0.585)
    # clipboard on the chest, held by the left hand underneath (as the Chapter 3 technician)
    cb = vec((0.020, 0.250, 1.100))
    n = Vector((0.08, -0.56, 0.82)).normalized()
    u = L.ortho((1.0, 0.0, 0.0), n)
    v = n.cross(u)
    R = L.frame_matrix(u, v, n)
    parts.append(L.rounded_box(f"{key}_board", (0.230, 0.320, 0.007), cb, R, bevel=0.002, segments=1))
    parts.append(L.rounded_box(f"{key}_sheet", (0.205, 0.270, 0.004), cb + n * 0.0045 - v * 0.012, R, bevel=0.0015, segments=1))
    parts.append(L.rounded_box(f"{key}_clip", (0.080, 0.030, 0.012), cb + n * 0.008 + v * 0.140, R, bevel=0.003, segments=1))
    palm = cb - u * 0.050 - v * 0.060 - n * 0.006
    hand_l = S.flat(key, -1, palm, v * 0.85 + u * 0.4, n, 0.95, curl=1.2)
    head = S.head_woman(sp, -42.0, -4.0, 2.0, tilt=14.0)
    obj, sh, el, wr = S.figure(key, sp, parts, "f", {1: hand_r, -1: hand_l},
                               {1: (sh_r + Vector((0.50, -0.20, -0.10)), None), -1: (sh_l + Vector((-0.40, -0.25, -0.35)), None)},
                               head, dict(body=3250, hand=420, head=1450), voxel=VOXEL)
    return obj, RIM_A


def tech_b():
    key = "tech_b"
    sp = L.Spine(hip_xy=(0.0, -0.040), neck_xy=(0.030, 0.200), z_hip=0.930, z_neck=1.480, yaw_hip=10.0, yaw_chest=32.0,
                 z_twist0=0.97, z_twist1=1.32)
    parts = S.man_coat(key, sp, pockets=True) + S.man_legs(key, sp, {1: (0.110, 0.020, -8.0), -1: (-0.110, -0.040, 12.0)})
    sh_r = sp.point(sp.z_neck - 0.088, (0.178, 0.010, 0.0))
    sh_l = sp.point(sp.z_neck - 0.088, (-0.178, 0.010, 0.0))
    tgt = H.g2b(RIM_B)
    hand_l = touching_hand(key, -1, sh_l, tgt, 1.04, [(16, 24, 12), (18, 26, 14), (22, 30, 16), (26, 32, 18)], wrist_max=0.62)
    hip = sp.point(sp.z_hip + 0.03, (0.215, 0.060, 0.0))
    hand_r = S.flat(key, 1, hip, Vector((-0.30, 0.55, -0.75)), Vector((-0.90, 0.0, 0.0)), 1.04, curl=1.4)
    head = S.head_man(sp, 44.0, 0.0, -2.0, tilt=12.0, kind="crop")
    obj, sh, el, wr = S.figure(key, sp, parts, "m", {1: hand_r, -1: hand_l},
                               {1: (sh_r + Vector((0.60, -0.30, -0.10)), None), -1: (sh_l + Vector((-0.50, -0.20, -0.10)), None)},
                               head, dict(body=3250, hand=420, head=1450), voxel=VOXEL)
    return obj, RIM_B


FIGS = {"tech_a": tech_a, "tech_b": tech_b}


# ------------------------------------------------------------------ QA
def bridge_context():
    L.import_ctx("bridge", (0.0, 0.0, 0.0), 0.0)
    for x in (-3.6, -2.2, 2.2, 3.6):
        L.import_ctx("handwheel", (x, 2.5, 12.45), 0.0)
    if not L.import_ctx("bridge", (0.0, 0.0, 0.0), 0.0):
        L.proxy("deck", (11.8, 0.2, 3.0), (0.0, 2.4, 13.4), color="3B3E42")


def renders(by):
    names = list(by)
    H.solo(list(by.values()), list(by.values()))
    # both figures side by side, ghost look, 3/4 from the front (the wheel side)
    objs = [by[n] for n in names]
    for o, x in zip(objs, (-0.8, 0.8)):
        o.location.x = x
    H.L.ghost("echo_tech_wheels", objs, (0.0, -4.6, 1.5), (0.0, 0.0, 0.85), lens=42, res=(960, 800), samples=24)
    for o in objs:
        o.location.x = 0.0
    if len(by) == 2:
        # the room: the contract `handwheels` camera (0, 4.9, 15.2) -> (0, 3.3, 9.0), FOV 84; both at their mounts
        pa, ya = H.world_mount(MOUNTS["tech_a"][0], 0.0, (0.0, 0.0, 0.0), MOUNTS["tech_a"][1])
        pb, yb = H.world_mount(MOUNTS["tech_b"][0], 0.0, (0.0, 0.0, 0.0), MOUNTS["tech_b"][1])
        L.place(by["tech_b"], pb, yb)
        H.context("echo_tech_wheels_2", objs, by["tech_a"], pa, ya, bridge_context, (0.0, 4.9, 15.2), (0.0, 3.3, 9.0), fov=84,
                  res=(1100, 640), samples=24)
        L.unplace(by["tech_b"])


def main():
    mrlib.reset_scene()
    by = {}
    rims = {}
    for nm, fn in FIGS.items():
        if ONLY and nm not in ONLY:
            continue
        o, rim = fn()
        H.turn(o)
        o.data.name = o.name
        by[nm] = o
        rims[nm] = rim
        H.add_empty(f"rim_touch_{nm}", o, rim)
        H.contact_report(f"{nm} fingertips on the wheel rim", o, rim, radius=0.05)
    path = mrlib.export_glb(NAME)
    H.verify(path, {k: BUDGET for k in by}, empties=[f"rim_touch_{k}" for k in by], file_budget=FILE_BUDGET)
    if RENDER:
        renders(by)


if __name__ == "__main__":
    main()
