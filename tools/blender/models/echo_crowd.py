"""Light echo: the Night-of-Silence crowd of the Array Hall (Chapter 4 group I; docs/models/ch4.md section 9).

ONE simplified 1970s lab-staff figure in THREE poses, each a root-level closed mesh (M_Echo), origin on the floor
between the feet, facing Godot +Z. The room draws the 33 crowd figures with one MultiMesh per shown pose (the
code swaps the mesh per minute of the replay; instance transform = position, yaw, a little scale jitter).

Output: game/assets/models/echo_crowd.glb
  pose_a   "at work": standing at ease, a clipboard hanging from the right hand, the left hand in a coat pocket,
           head up, looking ahead (the early minutes).
  pose_b   "reading": the clipboard held at the chest in both hands, head bowed over it (the middle minutes).
  pose_c   "03:17, the flash": torso turned away, one forearm raised across the eyes, the other arm bracing, the
           weight thrown back (the frozen minute; also the pose that "turns to the Sun").
The figure: a knee-length lab coat with a wide 1970s collar, trousers, shoes, a feathered shoulder-length cut with
sideburns (reads as either sex at 6 - 14 m). Height 1.70 m. Budget: <= 450 triangles per pose, <= 1,400 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_crowd.py [-- --no-render] [-- --only pose_b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch4_echo as C  # noqa: E402
from lib_ch4_echo import E, H, L, R, mrlib  # noqa: E402

NAME = "echo_crowd"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 450, 1400
VOXEL = 0.020

S = C.spec(z_hip=0.89, z_neck=1.42, w=0.94, d=0.96, grow=0.004, hair="shag", head=1.08, hand=1.0, coat_seg=18,
           leg=(0.074, 0.056, 0.058), shoe=1.05)               # bell-bottom trousers: the hem is the widest part


def board(c, size=(0.24, 0.030, 0.32), tilt=-18.0, roll=0.0):
    def make(ctx):
        rm = Matrix.Rotation(math.radians(tilt), 3, "X") @ Matrix.Rotation(math.radians(roll), 3, "Y")
        return [L.rounded_box("board", size, c, rm, bevel=0.006, segments=1)]
    return make


def pose_a():
    wr_l = R(-0.215, 0.100, 0.835)                      # left hand in the coat pocket
    return C.pose(hip_xy=(0.0, 0.0), neck_xy=(0.0, 0.010), yaw_hip=3.0, yaw_chest=-4.0,
                  feet={1: (0.10, 0.02, -8.0), -1: (-0.11, -0.04, 10.0)},
                  wrist={1: None, -1: wr_l}, hint={-1: (-0.35, -0.60, -0.15)},
                  head=(4.0, 3.0, 0.0), tilt=6.0,
                  props=[lambda ctx: [E.ellipsoid("clip_hang", ctx["wr"][1] + Vector((0.030, 0.045, -0.140)),
                                                  (0.020, 0.115, 0.150), seg=10, rings=6)]])


def pose_b():
    c = R(0.0, 0.290, 1.120)
    return C.pose(hip_xy=(0.0, -0.010), neck_xy=(0.0, 0.050), yaw_hip=-3.0, yaw_chest=4.0,
                  feet={1: (0.095, 0.0, -4.0), -1: (-0.105, 0.03, 8.0)},
                  wrist={1: R(0.130, 0.250, 1.190), -1: R(-0.120, 0.230, 1.020)},
                  hint={1: (0.35, -0.25, -0.40), -1: (-0.35, -0.25, -0.40)},
                  head=(-2.0, -34.0, 0.0), tilt=18.0, props=[board(c)])


def pose_c():
    return C.pose(hip_xy=(0.0, -0.040), neck_xy=(0.0, -0.040), yaw_hip=-10.0, yaw_chest=-34.0,
                  feet={1: (0.11, -0.150, -12.0), -1: (-0.10, 0.100, 18.0)},
                  wrist={1: R(0.070, 0.205, 1.560), -1: R(-0.400, 0.060, 1.000)},
                  hint={1: (0.60, 0.10, 0.25), -1: (-0.40, -0.40, -0.20)},
                  head=(-26.0, -8.0, 0.0), tilt=-4.0)


POSES = {"pose_a": pose_a, "pose_b": pose_b, "pose_c": pose_c}


# ------------------------------------------------------------------ QA
RINGS = ((12.6, 14), (9.5, 11), (7.5, 8), (5.5, 5), (3.8, 3))     # contract: the 41 on five rings


def crowd_positions():
    """33 positions: the 41 of the contract on rings r 12.6 / 9.5 / 7.5 / 5.5 / 3.8 minus the 8 nearest the catwalk (south)."""
    pts = []
    for ri, (r, n) in enumerate(RINGS):
        off = 0.5 * ri
        for i in range(n):
            a = math.radians(180.0 + 360.0 * (i + off) / n)       # azimuth from north, clockwise; start south
            pts.append((r * math.sin(a), -r * math.cos(a), r))
    pts.sort(key=lambda p: math.hypot(p[0], max(0.0, p[1] - 12.0, 1.4 - p[1])))       # distance to the catwalk
    return pts[8:]                                                 # the 8 nearest the catwalk are the named ones


def renders(objs):
    by = {o.name: o for o in objs}
    names = [n for n in POSES if n in by]
    # 1: the three poses in a row (ghost look, front 3/4)
    C.ghost_row(f"echo_crowd", [by[n] for n in names], [(-0.9, 0.0, 0.9)[i] for i in range(len(names))],
                (0.0, -4.2, 1.35), (0.0, 0.0, 0.95), lens=42, res=(1000, 560), everything=objs)
    # 2: the room: 33 instances with scale jitter on the rings, seen from the bridge camera (0, 4.4, 14.6)
    if len(names) == 3:
        import random
        rnd = random.Random(4)
        C.show_only(objs, [])                          # the three sources stay out of the room view
        inst = []
        for i, (x, z, r) in enumerate(crowd_positions()):
            src = by[names[1]]       # one pose at a time in the room: pose_b here
            o = bpy.data.objects.new(f"QA_crowd{i}", src.data)
            bpy.context.scene.collection.objects.link(o)
            yaw = math.degrees(math.atan2(-x, -z)) + rnd.uniform(-8, 8)
            sc = rnd.uniform(0.93, 1.07)
            L.place(o, (x, 0.0, z), yaw)
            o.scale = (sc * rnd.uniform(0.94, 1.06), sc * rnd.uniform(0.94, 1.06), sc)
            inst.append(o)
        # QA material on the instances, then the render
        src_data = by[names[1]].data
        keep = list(src_data.materials)
        saved = C.L._with_material(inst[:1], C.L.game_ghost_material())
        mrlib.QA_DIR = C.QA_DIR
        mrlib.render_preview("echo_crowd_2", L.g2b(0.0, 4.4, 14.6), L.g2b(0.0, 3.4, 0.0), lens=H.fov_lens(66, (1280, 720)),
                             res=(1280, 720),
                             samples=20, world_strength=0.02, lights=[((0, 0, 1), 1, "FFFFFF", 1.0)])
        src_data.materials.clear()
        for m in keep:
            src_data.materials.append(m)


def main():
    mrlib.reset_scene()
    objs = []
    for nm, fn in POSES.items():
        if ONLY and nm not in ONLY:
            continue
        o, _ctx = C.lp_figure(nm, S, fn(), voxel=VOXEL, tris=POSE_BUDGET)
        H.turn(o)
        o.data.name = o.name
        objs.append(o)
        print(f"[echo4] {nm}: {C.E.tris(o)} tris, {E.mesh_report(o)}")
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET for o in objs}, file_budget=FILE_BUDGET)
    if RENDER:
        renders(objs)


if __name__ == "__main__":
    main()
