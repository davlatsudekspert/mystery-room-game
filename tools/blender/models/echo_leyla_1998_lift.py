"""Light echo: Dr. Leyla Rahimova in 1998, about 45, at the lift landing, looking at her chalk (Chapter 4 `leyla_lift`).

The face lineage, field coat, belt, patch pockets and boots of echo_leyla_1998 (Chapter 3; its functions are imported), at
this group's budget (<= 8,000 triangles). ONE closed mesh (M_Echo), origin on the floor between her feet, the figure faces
Godot +Z, -X = her right.

Output: game/assets/models/echo_leyla_1998_lift.glb
  pose_lift   standing, torso turned 16 deg and head turned 19 deg to her left toward the chalk sign and "1998" on the
              back wall (at `echo_mount_leyla_lift` (-3.4, 0, 17.0), yaw 0 the chalk centre is at figure (0.40, 1.50, 1.18));
              her LEFT arm is raised and her index finger points at it (the fingertip is at figure (0.285, 1.424, 0.582)); her
              right arm hangs relaxed.
  chalk_target  empty, child of pose_lift, at the chalk centre (0.40, 1.50, 1.18) (identity): look-at point for her head.
Run: blender -b --factory-startup -P tools/blender/models/echo_leyla_1998_lift.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch4_echo as C  # noqa: E402
from lib_ch4_echo import E, H, L, mrlib, vec  # noqa: E402

NAME = "echo_leyla_1998_lift"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
POSE_BUDGET = 8000
LEY = H.load_model("echo_leyla_1998")
LEY.TRIS = dict(body=4300, hand=520, head=1850)
H.make_pose = C.make_pose                            # the retrying union
CHALK_G = (0.40, 1.50, 1.18)
MOUNT = ((-3.4, 0.0, 17.0), 0.0)


def pointing(prefix, el, wr, tgt):
    """Left hand, index finger straight at `tgt`, the other fingers curled, thumb tucked."""
    F = (vec(tgt) - vec(wr)).normalized()
    N, T = L.arm_hand_frame(F, -35.0, right=False)
    curls = [(4, 6, 3), (72, 88, 60), (76, 90, 60), (80, 88, 56)]
    thumb = None

    def th(info):
        j = info["joints"][1]                                  # tuck the thumb over the middle finger's second joint
        base = info["W"] + info["F"] * 0.030 + info["S"] * 0.020
        return [base, base.lerp(j[1], 0.45) + info["N"] * 0.010, j[1] + info["N"] * 0.006]
    return L.hand2(prefix, vec(wr), F, N, T, curls=curls, spread=[2, -2, -3, -6], thumb=th, scale=LEY.HAND_S,
                   width=0.078, finger_r=0.0084)


def pose_lift():
    key = "pose_lift"
    sp = L.Spine(hip_xy=(0.010, -0.005), neck_xy=(-0.004, 0.030), z_hip=0.865, z_neck=1.415, yaw_hip=8.0, yaw_chest=16.0,
                 z_twist0=0.90, z_twist1=1.24)
    feet = {1: (0.108, -0.020, -4.0), -1: (-0.102, 0.040, 16.0)}
    parts = LEY.coat(sp, key) + LEY.standing_legs(sp, key, feet)
    sh = LEY.shoulders(sp)
    tgt = H.g2b(CHALK_G)
    d = (tgt - sh[-1]).normalized()
    wr_l = sh[-1] + d * 0.480 + Vector((0.0, 0.0, -0.030))
    wr_r = sh[1] + Vector((0.055, 0.040, -0.515))
    arms = {1: (wr_r, sh[1] + Vector((0.40, -0.40, -0.30))), -1: (wr_l, sh[-1] + Vector((-0.45, -0.20, -0.70)))}

    def left(el, wr):
        objs, _info = pointing(f"{key}_handL", el, wr, tgt)
        return objs
    head = LEY.head_kw(sp, 19.0, 3.0, 0.0, tilt=12.0)
    return LEY.assemble(key, sp, parts, sh, arms, {1: LEY.relaxed(key, True), -1: left}, head)


# ------------------------------------------------------------------ QA
def lift_context():
    L.import_ctx("shell_lift4", (0.0, 0.0, 0.0), 0.0)
    if not L.import_ctx("freight_lift", (0.0, 0.0, 16.4), 0.0):
        L.proxy("cage", (2.6, 2.6, 2.6), (0.0, 1.3, 16.4), color="2B2C2E")


def renders(o):
    H.solo([o], [o])
    H.ghost("echo_leyla_1998_lift", [o], (-1.6, 1.4, 2.3), (0.05, 0.95, 0.25), lens=42, res=(640, 800), samples=24)
    # the contract's `lift_chalk` camera (-2.9, 1.55, 15.4) -> (-3.0, 1.5, 18.18), FOV 46: she stands between it and the chalk
    pos, yaw = MOUNT
    H.context("echo_leyla_1998_lift_2", [o], o, pos, yaw, lift_context, (-2.9, 1.55, 15.4), (-3.0, 1.5, 18.18), fov=46,
              res=(960, 640), samples=24)


def main():
    mrlib.reset_scene()
    o = pose_lift()
    H.turn(o)
    o.data.name = o.name
    H.add_empty("chalk_target", o, CHALK_G)
    mrlib.refresh()
    tgt = Vector(CHALK_G)
    pts = [Vector((v.co.x, v.co.z, -v.co.y)) for v in o.data.vertices]          # export orientation -> Godot figure frame
    tip = max(pts, key=lambda p: (p - Vector((0.17, 1.33, 0.0))).dot((tgt - Vector((0.17, 1.33, 0.0))).normalized()))
    print(f"[echo4] pointing fingertip at figure {tuple(round(c, 3) for c in tip)}, {((tgt - tip).length):.2f} m from the chalk centre")
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET}, empties=["chalk_target"], file_budget=POSE_BUDGET)
    if RENDER:
        renders(o)


if __name__ == "__main__":
    main()
