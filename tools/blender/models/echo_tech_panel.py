"""Light echo: a 1979 technician at Panel 0, throwing the main lever (Chapter 4 `tech_panel`).

A man in a knee-length lab coat (the Chapter 2 / 3 technicians' coat, the scientists' side-parted hair), bent forward over the
panel's low main lever. ONE closed mesh (M_Echo), origin on the floor between his feet, the figure faces Godot +Z, -X = his
right. Placed on panel0's `echo_mount_tech_panel` (panel-local (0.8, 0, 1.0), yaw 180).

Output: game/assets/models/echo_tech_panel.glb
  echo_tech_panel   RIGHT fist (overhand, fingers toward his left) round the stem of `IA_main_lever` in its PULLED position
                    (+60 deg about +X: the stem points at him, 30 deg above horizontal): grip centre figure (-0.04, 0.75, 0.50),
                    i.e. panel-local (0.84, 0.75, 0.50); the ball is 0.07 further up the stem. The left hand braces on his left
                    thigh at figure (0.215, 0.70, 0.08); he looks up and to his right at the lamp row (panel-local y 1.86).
  grip_right        empty, child of the figure, identity rotation, at the grip centre.
Run: blender -b --factory-startup -P tools/blender/models/echo_tech_panel.py [-- --no-render]
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

NAME = "echo_tech_panel"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
BUDGET = 6000
TRIS = dict(body=3350, hand=420, head=1450)
VOXEL = 0.0036
GRIP_G = (-0.04, 0.75, 0.50)                    # the main lever's stem, pulled (panel-local (0.84, 0.75, 0.50))
STEM_D = Vector((0.0, -0.866, 0.5))             # pivot -> tip in the build frame (toward him, 30 deg above horizontal)
PANEL = ((0.0, 0.0, 14.0), 180.0)               # panel0 at its group-P placement
MOUNT_LOCAL = ((0.8, 0.0, 1.0), 180.0)          # echo_mount_tech_panel


def build():
    key = NAME
    sp = L.Spine(hip_xy=(0.0, -0.140), neck_xy=(-0.020, 0.250), z_hip=0.930, z_neck=1.395, yaw_hip=-4.0, yaw_chest=-10.0,
                 z_twist0=0.97, z_twist1=1.28)
    feet = {1: (0.125, -0.030, -10.0), -1: (-0.115, -0.100, 14.0)}
    parts = S.man_coat(key, sp) + S.man_legs(key, sp, feet)
    sh_r = sp.point(sp.z_neck - 0.088, (0.178, 0.010, 0.0))
    sh_l = sp.point(sp.z_neck - 0.088, (-0.178, 0.010, 0.0))
    g = H.g2b(GRIP_G)
    F = Vector((-1.0, 0.05, -0.05))
    N = Vector((0.0, -0.5, -0.866))
    hand_r = S.fist(key, 1, g, F, N, scale=1.04, along=0.088, out=0.030)
    head = S.head_man(sp, -10.0, 14.0, 0.0, tilt=10.0, kind="side")
    obj, sh, el, wr = S.figure(key, sp, parts, "m", {1: hand_r, -1: S.relaxed(key, -1, 1.04)},
                               {1: (sh_r + Vector((0.50, -0.20, -0.25)), None), -1: (sh_l + Vector((-0.55, -0.15, 0.05)), Vector((-0.215, 0.080, 0.700)))},
                               head, TRIS, voxel=VOXEL)
    return obj


# ------------------------------------------------------------------ QA
def panel_context():
    if not L.import_ctx("panel0", PANEL[0], PANEL[1]):
        L.proxy("panel", (1.96, 2.14, 0.3), (0.0, 1.07, 13.9), color="3A3C3F")
    L.proxy("floor", (14.0, 0.05, 8.0), (0.0, -0.025, 12.0), color="3B3E42")


def renders(o):
    H.solo([o], [o])
    H.ghost("echo_tech_panel", [o], (-1.7, 1.3, 2.0), (0.0, 0.95, 0.30), lens=42, res=(640, 800), samples=24)
    pos, yaw = H.world_mount(PANEL[0], PANEL[1], MOUNT_LOCAL[0], MOUNT_LOCAL[1])
    # the contract `panel0` camera (0, 1.2, 12.3) -> (0, 1.15, 14.0) puts him 0.7 m in front of the lens (his back); the second
    # view stands off to the side, as a player who has stepped east of the panel would see him
    H.context("echo_tech_panel_2", [o], o, pos, yaw, panel_context, (2.2, 1.55, 11.9), (-0.45, 1.0, 13.6), fov=56,
              res=(960, 640), samples=24)


def main():
    mrlib.reset_scene()
    o = build()
    H.turn(o)
    o.data.name = o.name
    H.add_empty("grip_right", o, GRIP_G)
    H.contact_report("right fist on the lever stem", o, GRIP_G, radius=0.05)
    C.grip_report("main lever stem (pulled)", o, GRIP_G, (0.0, 0.5, -0.866), half=0.05, r=0.012)
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: BUDGET}, empties=["grip_right"], file_budget=BUDGET)
    if RENDER:
        renders(o)


if __name__ == "__main__":
    main()
