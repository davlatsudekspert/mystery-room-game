"""Light echo: Prof. Emil Strand at the master desk, 03:17, frozen reaching for the master lever (Chapter 4 group I).

The face, beard, fringe and long coat of echo_strand_rail (Chapter 3; its P_HEAD, hair and coat functions), at the
budget of this group (<= 5,000 triangles). ONE closed mesh (M_Echo), origin on the floor between his feet, the figure
faces Godot +Z, -X = his right. He is placed on master_desk's `echo_mount_strand` (desk-local (1.12, 0, 0.78), yaw 180),
so in the desk frame he faces the desk (-Z) with the lever on his right.

Output: game/assets/models/echo_strand_desk.glb
  echo_strand_desk   the figure. Body upright and a little back, torso turned 14 deg to the lever, the right arm
                     nearly straight with the fist closed round the lever's knurled grip (master_lever DOWN position:
                     the grip centre is at desk-local (1.28, 1.142, 0.337), i.e. figure (-0.160, 1.142, 0.443)); the
                     left hand rests flat on the console's sloping face at figure (0.37, 1.05, 0.44); the head is
                     turned to the lever and down.
  grip_right         empty, child of the figure, identity rotation, at the grip centre (-0.160, 1.142, 0.443).
Run: blender -b --factory-startup -P tools/blender/models/echo_strand_desk.py [-- --no-render]
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

NAME = "echo_strand_desk"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
POSE_BUDGET = 5000
TRIS = dict(body=2750, hand=320, head=1300)
VOXEL = 0.0038
SRC = H.load_model("echo_strand_rail")          # coat, legs, shoulders, head_kw, folds_for, flutes_for, sleeve radii
GRIP_G = (-0.160, 1.142, 0.443)                 # the lever grip centre (master_lever DOWN) in the figure frame
PALM_G = (0.370, 1.050, 0.440)                  # left palm on the console slope
MOUNT = ((0.0, 2.5, 13.15), 0.0)                # master_desk at the bridge's desk_mount
MOUNT_LOCAL = ((1.12, 0.0, 0.78), 180.0)        # echo_mount_strand in the desk frame


def build():
    key = NAME
    sp = L.Spine(hip_xy=(0.0, -0.100), neck_xy=(-0.020, 0.050), z_hip=0.920, z_neck=1.465, yaw_hip=-4.0,
                 yaw_chest=-14.0, z_twist0=0.95, z_twist1=1.30)
    feet = {1: (0.125, -0.020, -12.0), -1: (-0.100, 0.060, 10.0)}
    parts = SRC.coat(sp, key) + SRC.legs(sp, key, feet)
    sh = SRC.shoulders(sp)
    # right fist round the grip: the bar runs along the figure's forward axis (+Y build); fingers point down and forward,
    # the palm faces the body's centre line (-X), the thumb on top
    g = H.g2b(GRIP_G)
    F = Vector((0.0, 0.22, -0.975)).normalized()
    N = Vector((-1.0, 0.0, 0.0))
    wr_r = H.grip_wrist(g, F, N, SRC.HAND_S, along=0.088, out=0.030)
    hr, _info = H.hand(f"{key}_handR", wr_r, F, N, True, [(42, 58, 40), (44, 60, 40), (46, 60, 38), (48, 58, 36)],
                       spread=[0, 0, -2, -4], scale=SRC.HAND_S, width=0.084, finger_r=0.0090)
    # left palm flat on the slope (the slope's up-normal in the figure frame is (0, 0.7855, -0.6189))
    palm = H.g2b(PALM_G)
    Fl = Vector((0.0, 0.7855, 0.6189))               # up the slope, away from him (build: +Y forward, +Z up)
    Nl = Vector((0.0, 0.6189, -0.7855))              # into the surface
    hl, wr_l, _ = H.flat_hand(f"{key}_handL", palm, Fl, Nl, False, SRC.HAND_S, curl=1.0, width=0.084, finger_r=0.0090)
    parts_r, el_r = H.arm(f"{key}_arm1", sh[1], wr_r, SRC.UPPER, SRC.FORE, sh[1] + Vector((0.45, -0.25, -0.30)),
                          r=SRC.SLEEVE_R, sp=sp, side=1)
    parts_l, el_l = H.arm(f"{key}_arm-1", sh[-1], wr_l, SRC.UPPER, SRC.FORE, sh[-1] + Vector((-0.45, -0.35, -0.20)),
                          r=SRC.SLEEVE_R, sp=sp, side=-1)
    parts += parts_r + parts_l
    head = SRC.head_kw(sp, -18.0, -14.0, 0.0, tilt=16.0)
    return C.make_pose(key, parts, [(hr, wr_r), (hl, wr_l)], head, TRIS, voxel=VOXEL,
                       folds=SRC.folds_for(sp, sh, {1: el_r, -1: el_l}, {1: wr_r, -1: wr_l}), flutes=SRC.flutes_for(sp))


# ------------------------------------------------------------------ QA
def desk_context():
    if not L.import_ctx("master_desk", MOUNT[0], MOUNT[1]):
        L.proxy("desk", (3.1, 0.95, 0.9), (MOUNT[0][0], MOUNT[0][1] + 0.475, MOUNT[0][2]), color="3A3C3F")
    lever_pos = (MOUNT[0][0] + 1.28, MOUNT[0][1] + 0.95, MOUNT[0][2])
    L.import_ctx("master_lever", lever_pos, 0.0)
    L.proxy("deck", (14.0, 0.05, 8.0), (0.0, MOUNT[0][1] - 0.025, 14.0), color="3B3E42")


def renders(o):
    if "--dev" in ARGS:                                 # close-ups for the modeller (not committed)
        L.QA_DIR = ARGS[ARGS.index("--dev") + 1]
        L.proxy("bar", (0.034, 0.034, 0.17), GRIP_G, color="B08D57")
        H.clay(f"{NAME}_hand", (-0.55, 1.45, 0.85), GRIP_G, lens=60, res=(640, 640))
        H.clay(f"{NAME}_hand2", (0.65, 1.25, 0.95), GRIP_G, lens=60, res=(640, 640))
        H.clay(f"{NAME}_side", (3.0, 1.2, 0.3), (0.0, 1.0, 0.3), lens=42, res=(640, 800))
        return
    # 1: the figure alone, ghost look, front 3/4 from the desk side (north), dark
    H.solo([o], [o])
    H.ghost(f"echo_{NAME[5:]}", [o], (1.5, 1.45, 2.3), (0.0, 0.95, 0.15), lens=42, res=(640, 800), samples=24)
    # 2: at its mount in the room (desk, lever, deck) from behind and to the left, as the player on the bridge sees him
    pos, yaw = H.world_mount(MOUNT[0], 0.0, MOUNT_LOCAL[0], MOUNT_LOCAL[1])
    H.context(f"echo_{NAME[5:]}_2", [o], o, pos, yaw, desk_context, (-0.35, 4.55, 15.35), (1.0, 3.55, 13.4), fov=52,
              res=(960, 640), samples=24)


def main():
    mrlib.reset_scene()
    o = build()
    H.turn(o)
    o.data.name = o.name
    H.add_empty("grip_right", o, GRIP_G)
    H.contact_report("right fist round the lever grip", o, GRIP_G, radius=0.05)
    C.grip_report("lever grip (down: 6 deg below horizontal)", o, GRIP_G, (0.0, 0.105, 0.9945))
    H.contact_report("left palm on the console slope", o, PALM_G, radius=0.05)
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET}, empties=["grip_right"], file_budget=POSE_BUDGET)
    if RENDER:
        renders(o)


if __name__ == "__main__":
    main()
