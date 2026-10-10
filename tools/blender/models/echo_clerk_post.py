"""Light echo: the 1979 watch-room clerk at the pneumatic post station (Chapter 4 `clerk_post`).

A man in a short office jacket (the lab-coat ring table cut at the hip), a clerk's green eyeshade and the scientists' side-parted
hair, sending the post: his RIGHT fist on the ball of the send lever, his LEFT hand over the destination knob, his eyes on the
pictogram ring. ONE closed mesh (M_Echo), origin on the floor between his feet, the figure faces Godot +Z, -X = his right.
Placed on watch_room's `echo_mount_clerk_post` (room-local (-2.95, 0.03, -0.35), yaw 180: he faces the station, 0.45 from
its dial plane).

Output: game/assets/models/echo_clerk_post.glb
  echo_clerk_post   the figure. Contact points in the figure frame (station-local + the mount: x_f = -sx, y_f = sy, z_f = 0.85 - sz):
                    send-lever ball (UPRIGHT rest) (-0.375, 1.05, 0.425); destination knob front face (0.19, 1.00, 0.42).
  lever_grip        empty, child of the figure, identity, at the lever ball centre (-0.375, 1.05, 0.425).
  dial_touch        empty, child of the figure, identity, at the knob's front face centre (0.19, 1.00, 0.42).
Run: blender -b --factory-startup -P tools/blender/models/echo_clerk_post.py [-- --no-render]
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

NAME = "echo_clerk_post"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
BUDGET = 6000
TRIS = dict(body=3300, hand=440, head=1500)
VOXEL = 0.0036
LEVER_G = (-0.375, 1.05, 0.425)
DIAL_G = (0.19, 1.00, 0.42)
ROOM = ((12.7, 0.0, 0.0), -90.0)                 # watch_room placement
POST = ((-2.95, 0.03, -1.2), 0.0)                # post_mount in the room frame
CLERK = ((-2.95, 0.03, -0.35), 180.0)            # echo_mount_clerk_post in the room frame


def build():
    key = NAME
    sp = L.Spine(hip_xy=(0.0, -0.040), neck_xy=(0.010, 0.140), z_hip=0.940, z_neck=1.485, yaw_hip=2.0, yaw_chest=4.0,
                 z_twist0=0.98, z_twist1=1.32)
    feet = {1: (0.105, -0.020, -8.0), -1: (-0.105, 0.040, 10.0)}
    parts = S.man_coat(key, sp, hem_dz=-0.20, grow=0.0, pockets=False) + S.man_legs(key, sp, feet, top_z=0.86, r_top=0.080)
    sh_r = sp.point(sp.z_neck - 0.088, (0.178, 0.010, 0.0))
    sh_l = sp.point(sp.z_neck - 0.088, (-0.178, 0.010, 0.0))
    # right fist over the lever ball from above (palm down, fingers forward and down round it)
    hand_r = S.fist(key, 1, H.g2b(LEVER_G), Vector((0.0, 1.0, -0.10)), Vector((0.0, 0.0, -1.0)), scale=1.0,
                    curls=[(34, 52, 36), (38, 54, 36), (42, 54, 34), (46, 52, 32)], along=0.088, out=0.030)
    # left hand flat over the knob's front, the fingers curled over its top edge
    palm = H.g2b((DIAL_G[0], DIAL_G[1] - 0.005, DIAL_G[2] - 0.012))
    hand_l = S.flat(key, -1, palm, Vector((0.12, 0.0, 1.0)), Vector((0.0, 1.0, 0.0)), 1.0, curl=1.6)
    head = S.head_man(sp, 8.0, -24.0, 0.0, tilt=18.0, kind="side", extras=S.eyeshade)
    obj, sh, el, wr = S.figure(key, sp, parts, "m", {1: hand_r, -1: hand_l},
                               {1: (sh_r + Vector((0.45, -0.30, -0.15)), None), -1: (sh_l + Vector((-0.45, -0.20, -0.20)), None)},
                               head, TRIS, voxel=VOXEL)
    return obj


# ------------------------------------------------------------------ QA
def room_context():
    pos, yaw = ROOM
    L.import_ctx("watch_room", pos, yaw)
    ppos, pyaw = H.world_mount(pos, yaw, POST[0], POST[1])
    if not L.import_ctx("post_station4", ppos, pyaw):
        L.proxy("post", (0.9, 2.0, 0.5), (ppos[0] - 0.25, 1.0, ppos[2]), color="2B2C2E")
    L.proxy("floor", (8.0, 0.05, 8.0), (10.0, -0.025, 0.0), color="3B3E42")


def renders(o):
    H.solo([o], [o])
    H.ghost("echo_clerk_post", [o], (1.5, 1.45, 2.2), (0.0, 1.0, 0.25), lens=42, res=(640, 800), samples=24)
    pos, yaw = H.world_mount(ROOM[0], ROOM[1], CLERK[0], CLERK[1])
    # the contract's `post_station` camera (9.8, 1.5, -1.5) looks through the glass front (opaque in this QA scene): a camera inside the cabin instead
    H.context("echo_clerk_post_2", [o], o, pos, yaw, room_context, (12.25, 1.6, -0.95), (13.6, 1.1, -2.95), fov=56,
              res=(960, 640), samples=24)


def main():
    mrlib.reset_scene()
    o = build()
    H.turn(o)
    o.data.name = o.name
    H.add_empty("lever_grip", o, LEVER_G)
    H.add_empty("dial_touch", o, DIAL_G)
    H.contact_report("right fist at the send-lever ball", o, LEVER_G, radius=0.05)
    H.contact_report("left palm at the destination knob", o, DIAL_G, radius=0.05)
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: BUDGET}, empties=["lever_grip", "dial_touch"], file_budget=BUDGET)
    if RENDER:
        renders(o)


if __name__ == "__main__":
    main()
