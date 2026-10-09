"""Light echo: Dr. Leyla Rahimova in 1998, about 45 (Chapter 3: the seed library, the 42nd socket, the finale).

The face lineage of echo_leyla_standing (the same female head, swept-back hair and bun from that script), a little
older (nasolabial folds, softer cheeks, a forehead line). A 1990s field coat to mid-thigh with a stand collar, a
belt and four patch pockets, trousers and field boots. Six root-level poses, each ONE closed mesh (M_Echo):

Output: game/assets/models/echo_leyla_1998.glb (Godot axes; the figure faces +Z, -X = her right)
  pose_touch_0 / _1 / _2   her LEFT fingertips (middle finger) on a drawer front at (+0.40, y, +0.42),
                           y = 1.50 / 1.24 / 0.98 for library rows 0 / 1 / 2; at seed_library
                           `echo_touch_mount_<c>` (any column: the pose depends on the row only).
  pose_kneel               kneeling on her left knee, right foot forward, her RIGHT palm flat on the socket at
                           (-0.05, 1.15, 0.55); at memorial_wall `echo_kneel_mount`.
  pose_offer               standing, her right palm up and held out; at shell_gallery `echo_leyla_mount`.
  crystal_mount            empty, child of pose_offer, at (-0.20, 1.20, 0.45), identity. Her palm surface is
                           0.057 below it, so nursery_crystal.glb (origin = centre of mass, bottom 0.0569 below it)
                           parented there stands on her palm.
Budget: <= 8,000 tris per pose, <= 40,000 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_leyla_1998.py [-- --no-render] [-- --only pose_kneel]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch3_echoes as H  # noqa: E402
from lib_ch3_echoes import E, L, mrlib, vec  # noqa: E402

NAME = "echo_leyla_1998"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 8000, 40000
TRIS = dict(body=4300, hand=520, head=1850)
VOXEL = 0.0034
HAND_S = 0.95
UPPER, FORE = 0.300, 0.236
SRC = H.load_model("echo_leyla_standing")          # hair_disp, bun: her 1979 lineage
ROWS = (1.50, 1.24, 0.98)
SOCKET_G = (-0.05, 1.15, 0.55)
CRYSTAL_G = (-0.20, 1.20, 0.45)
CRYSTAL_BOTTOM = 0.0569                              # nursery_crystal.glb: bottom below its origin
SLEEVE_R = (0.053, 0.050, 0.047, 0.044, 0.046, (0.0235, 0.0175), (0.047, 0.052, 0.048))

AGE_KERNELS = ([dict(c=(sx * 0.030, 0.083, -0.036), s=(0.009, 0.010, 0.020), a=-0.0010, face=(0, 1, 0)) for sx in (1, -1)]
               + [dict(c=(sx * 0.035, 0.084, -0.011), s=(0.011, 0.010, 0.0035), a=-0.0008, face=(0, 1, 0))
                  for sx in (1, -1)]
               + [dict(c=(0, 0.074, 0.050), s=(0.035, 0.02, 0.0028), a=-0.0006, face=(0, 1, 0))])


# ------------------------------------------------------------------ body parts
def coat(sp, key):
    rings = H.coat_rings(H.WOMAN_COAT, H.WOMAN_HIP, H.WOMAN_NECK, sp.z_hip, sp.z_neck, hem_dz=-0.24, grow=0.014,
                         hem_flare=0.010)
    c = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.12, cap1=0.3)
    tree = E.bvh(c)
    zh = sp.z_hip
    parts = [c] + H.coat_details(key, sp, tree, female=True, collar_r=0.062, collar_z=sp.z_neck - 0.030, lapel=False,
                                 pockets=(0.105, zh - 0.07, zh - 0.18, 0.120), buttons=(zh + 0.40, zh + 0.29, zh + 0.18),
                                 button_x=0.0, stand_collar=True)
    for sx in (1, -1):                                      # bellows chest pockets with flaps
        parts.append(E.surface_slab(f"{key}_chestpocket{sx}", tree,
                                    [sp.point(zh + 0.40, (sx * 0.085, 0.15, 0)), sp.point(zh + 0.31, (sx * 0.085, 0.15, 0))],
                                    [0.085, 0.090], thick=0.0060))
        parts.append(E.surface_slab(f"{key}_flap{sx}", tree,
                                    [sp.point(zh + 0.415, (sx * 0.085, 0.15, 0)), sp.point(zh + 0.395, (sx * 0.085, 0.15, 0))],
                                    [0.094, 0.094], thick=0.0085))
    parts.append(E.surface_slab(f"{key}_belt", tree, [sp.point(zh + 0.13, (0.17, 0.0, 0)), sp.point(zh + 0.13, (0.10, 0.12, 0)),
                                                      sp.point(zh + 0.13, (0.0, 0.16, 0)), sp.point(zh + 0.13, (-0.10, 0.12, 0)),
                                                      sp.point(zh + 0.13, (-0.17, 0.0, 0))],
                                [0.035] * 5, thick=0.005))
    parts.append(E.surface_slab(f"{key}_placket", tree, [sp.point(zh + 0.47, (0.004, 0.15, 0)),
                                                         sp.point(zh - 0.22, (0.004, 0.18, 0))], [0.026, 0.026], thick=0.004))
    return parts


def standing_legs(sp, key, feet):
    parts = []
    for s in (1, -1):
        ax, ay, fy = feet[s]
        top = sp.point(0.62, (s * 0.090, 0.0, 0.0))
        sh, ank = H.shoe_on(f"{key}_boot{s}", (ax, ay), fy, heel=0.020, scale=0.95, boot=True)
        parts += sh
        parts += L.trouser_leg(f"{key}_trouser{s}", top, ank, r_top=0.066, r_knee=0.057, r_hem=0.056, hem_z=0.16)
    return parts


def shoulders(sp):
    z = sp.z_neck - 0.078
    return {1: sp.point(z, (0.155, 0.012, 0.0)), -1: sp.point(z, (-0.156, 0.000, 0.0))}


def head_kw(sp, yaw, pitch, roll=0.0, tilt=18.0):
    pivot = sp.point(sp.z_neck - 0.005, (0.0, 0.004, 0.0))
    nd = L.neck_dir(sp.yaw_chest, tilt)
    return dict(P=E.FEMALE, pivot=pivot, nd=nd, yaw=yaw, pitch=pitch, roll=roll, hair_fn=SRC.hair_disp,
                extras_fn=SRC.bun, kernels=AGE_KERNELS, voxel=0.0017)


def folds_for(sp, sh, el, wr):
    def fn():
        k = []
        for s in (1, -1):
            inner = (sh[s] - el[s]).normalized() + (wr[s] - el[s]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[s] + inner.normalized() * 0.034, s=0.014, a=-0.0045),
                      dict(c=el[s] + inner.normalized() * 0.026 + (wr[s] - el[s]).normalized() * 0.03, s=0.011,
                           a=0.0025)]
        zh = sp.z_hip
        for sx in (1, -1):                                  # gathers under the belt
            for dz in (-0.02, 0.03):
                k.append(dict(c=sp.point(zh + 0.13 + dz, (sx * 0.12, 0.10, 0)), s=(0.010, 0.03, 0.012), a=-0.0018))
        k += L.groove([sp.point(zh + 0.36, (0.10, -0.12, 0)), sp.point(zh + 0.16, (0.05, -0.12, 0))], 0.012, -0.0025,
                      face=-sp.front(zh + 0.3))
        k += L.groove([sp.point(zh + 0.36, (-0.10, -0.12, 0)), sp.point(zh + 0.16, (-0.05, -0.12, 0))], 0.012, -0.0025,
                      face=-sp.front(zh + 0.3))
        return k
    return fn


def assemble(key, sp, parts, sh, arms_spec, hands_spec, head):
    """arms_spec: {s: (wrist, pole)}; hands_spec: {s: parts or callable(el, wr) -> parts}."""
    el, wr = {}, {}
    for s in (1, -1):
        w, pole = arms_spec[s]
        ap, e = H.arm(f"{key}_arm{s}", sh[s], w, UPPER, FORE, pole, r=SLEEVE_R, sp=sp, side=s)
        parts += ap
        el[s], wr[s] = e, vec(w)
    hands = []
    for s in (1, -1):
        hp = hands_spec[s]
        if callable(hp):
            hp = hp(el[s], wr[s])
        hands.append((hp, wr[s]))
    return H.make_pose(key, parts, hands, head, TRIS, voxel=VOXEL, folds=folds_for(sp, sh, el, wr))


def relaxed(key, right):
    def make(e, w):
        objs, _ = H.relaxed_hand(f"{key}_hand{'R' if right else 'L'}", e, w, right, HAND_S)
        return objs
    return make


# ------------------------------------------------------------------ poses
def pose_touch(r):
    key = f"pose_touch_{r}"
    y = ROWS[r]
    lean = (0.020, 0.050, 0.095)[r]
    sp = L.Spine(hip_xy=(0.0, -0.010), neck_xy=(-0.030, -0.010 + lean), z_hip=0.865, z_neck=(1.415, 1.405, 1.380)[r],
                 yaw_hip=8.0, yaw_chest=(22.0, 20.0, 18.0)[r], z_twist0=0.90, z_twist1=1.24)
    feet = {1: (0.105, -0.050, -2.0), -1: (-0.135, 0.050, 22.0)}
    parts = coat(sp, key) + standing_legs(sp, key, feet)
    sh = shoulders(sp)
    target = H.g2b((0.40, y, 0.42))
    F = (target - sh[-1]).normalized()
    F = (F + Vector((0.0, 0.55, 0.0))).normalized()           # fingers forward onto the drawer front
    N = L.ortho((0.30, 0.20, -1.0), F)
    hl, wl, info = H.hand_to_tip(f"{key}_handL", target + Vector((0.0, -0.006, 0.0)), F, N, False,
                                 [(6, 12, 6), (4, 10, 6), (26, 36, 18), (36, 44, 22)], tip=1,
                                 spread=[4, 0, -4, -8], scale=HAND_S, width=0.075, finger_r=0.0082)
    pole_l = sh[-1] + Vector((-0.45, -0.15, (-0.35, -0.40, -0.30)[r]))
    wr_r = sh[1] + Vector((0.055, 0.040, -0.515))
    arms = {1: (wr_r, sh[1] + Vector((0.40, -0.40, -0.30))), -1: (wl, pole_l)}
    head = head_kw(sp, (30.0, 30.0, 28.0)[r], (14.0, -6.0, -26.0)[r], -3.0, tilt=(8.0, 14.0, 24.0)[r])
    print(f"[echo3] {key}: middle fingertip at {H.b2g(info['tips'][1])} (target {(0.40, y, 0.42)})")
    return assemble(key, sp, parts, sh, arms, {1: relaxed(key, True), -1: hl}, head)


def pose_kneel():
    key = "pose_kneel"
    sp = L.Spine(hip_xy=(0.0, -0.040), neck_xy=(-0.010, 0.080), z_hip=0.500, z_neck=1.035, yaw_hip=-4.0, yaw_chest=-8.0,
                 z_twist0=0.54, z_twist1=0.87)
    parts = coat(sp, key)
    hip = {1: vec((0.085, -0.030, 0.500)), -1: vec((-0.085, -0.050, 0.505))}
    knee = {1: vec((0.120, 0.380, 0.490)), -1: vec((-0.105, 0.010, 0.062))}
    sh_r, ank_r = H.shoe_on(f"{key}_boot1", (0.130, 0.270), 4.0, heel=0.020, scale=0.95, boot=True)
    sh_l, ank_l = H.shoe_on(f"{key}_boot-1", (-0.105, -0.570), 0.0, heel=0.020, scale=0.95, toes_down=62.0, boot=True)
    parts += sh_r + sh_l
    parts += H.bent_leg(f"{key}_leg1", hip[1], knee[1], ank_r, r_thigh=0.072, r_knee=0.055, r_shin=0.054, r_hem=0.056)
    parts += H.bent_leg(f"{key}_leg-1", hip[-1], knee[-1], ank_l, r_thigh=0.072, r_knee=0.055, r_shin=0.054, r_hem=0.056)
    sh = shoulders(sp)
    palm = H.g2b(SOCKET_G)
    hr, wr_r, _ = H.flat_hand(f"{key}_handR", palm, (-0.08, 0.10, 1.0), (0.0, 1.0, 0.0), True, HAND_S, curl=1.0,
                              width=0.075, finger_r=0.0082)
    # left hand resting on the outside of her left thigh
    pl = vec((-0.150, -0.020, 0.380))
    hl, wr_l, _ = H.flat_hand(f"{key}_handL", pl, (0.05, 0.25, -1.0), (1.0, 0.0, 0.0), False, HAND_S, curl=1.5,
                              width=0.075, finger_r=0.0082)
    arms = {1: (wr_r, sh[1] + Vector((0.45, -0.30, -0.35))), -1: (wr_l, sh[-1] + Vector((-0.40, -0.35, -0.10)))}
    head = head_kw(sp, -6.0, 12.0, 2.0, tilt=10.0)
    return assemble(key, sp, parts, sh, arms, {1: hr, -1: hl}, head)


def pose_offer():
    key = "pose_offer"
    sp = L.Spine(hip_xy=(0.010, -0.010), neck_xy=(-0.004, 0.030), z_hip=0.865, z_neck=1.415, yaw_hip=-4.0,
                 yaw_chest=-8.0, z_twist0=0.90, z_twist1=1.24)
    feet = {1: (0.110, 0.035, -8.0), -1: (-0.105, -0.040, 12.0)}
    parts = coat(sp, key) + standing_legs(sp, key, feet)
    sh = shoulders(sp)
    c = H.g2b(CRYSTAL_G)
    palm = c - Vector((0.0, 0.0, CRYSTAL_BOTTOM))
    hr, wr_r, _ = H.flat_hand(f"{key}_handR", palm, (0.10, 0.97, 0.10), (0.0, 0.0, 1.0), True, HAND_S, curl=2.2,
                              width=0.075, finger_r=0.0082)
    wr_l = sh[-1] + Vector((-0.050, 0.060, -0.505))
    arms = {1: (wr_r, sh[1] + Vector((0.35, -0.25, -0.50))), -1: (wr_l, sh[-1] + Vector((-0.40, -0.40, -0.30)))}
    head = head_kw(sp, -4.0, -6.0, 3.0, tilt=12.0)
    return assemble(key, sp, parts, sh, arms, {1: hr, -1: relaxed(key, False)}, head)


POSES = {"pose_touch_0": lambda: pose_touch(0), "pose_touch_1": lambda: pose_touch(1),
         "pose_touch_2": lambda: pose_touch(2), "pose_kneel": pose_kneel, "pose_offer": pose_offer}


# ------------------------------------------------------------------ QA
LIB_POS, LIB_YAW = (13.0, 0.0, -0.6), -90.0
KNEEL_MOUNT = ((1.49, 0.0, -3.02), 153.0)
OFFER_MOUNT = ((2.30, 0.0, 1.00), -40.0)
STRAND_MOUNT = ((-2.30, 0.0, 1.00), 40.0)


def library_context(r, c):
    def build():
        if not L.import_ctx("seed_library", LIB_POS, LIB_YAW):
            L.proxy("carcass", (0.45, 1.75, 1.50), (12.775, 0.875, -0.6), color="3B2416")
            for rr in range(3):
                for cc in range(4):
                    yr = 1.50 - 0.26 * rr
                    xc = (cc - 1.5) * 0.33
                    lit = rr == r and cc == c
                    L.proxy(f"drawer{rr}{cc}", (0.01, 0.22, 0.30), (12.545, yr, -0.6 + xc), color="5A3A22",
                            emit="CFF6FF" if lit else None)
        L.proxy("floor", (6.0, 0.02, 8.0), (10.0, -0.01, 0.0), color="3E5A48")
        L.proxy("wall_e", (0.1, 4.0, 8.0), (13.05, 2.0, 0.0), color="D9D6CB")
    return build


def memorial_context():
    if not L.import_ctx("memorial_wall", (0.0, 0.0, 0.0), 0.0):
        n = Vector((0.454, -0.890))
        sx, sz = 1.78 + n.x * 0.025, -3.49 + n.y * 0.025
        L.proxy("band", (1.4, 1.0, 0.05), (sx, 1.45, sz), color="5A5852", yaw=-27.0)
        L.proxy("socket", (0.05, 0.05, 0.04), (1.78 - n.x * 0.01, 1.15, -3.49 - n.y * 0.01), color="B08D57")
    if not L.import_ctx("shell_gallery", (0.0, 0.0, 0.0), 0.0):
        L.proxy("floor", (9.0, 0.02, 9.0), (0.0, -0.01, 0.0), color="8A8579")


def finale_context():
    if not L.import_ctx("shell_gallery", (0.0, 0.0, 0.0), 0.0):
        L.proxy("floor", (9.0, 0.02, 9.0), (0.0, -0.01, 0.0), color="8A8579")
    L.import_ctx("gallery_console", (0.0, 0.0, 2.6), 0.0)
    imp = L.import_ctx("echo_strand_rail", STRAND_MOUNT[0], STRAND_MOUNT[1])
    for o in imp:
        if o.name.startswith("QA_imp_pose_rail"):
            o.hide_render = True
    pos, yaw = H.world_mount(OFFER_MOUNT[0], OFFER_MOUNT[1], CRYSTAL_G, 0.0)
    L.import_ctx("nursery_crystal", pos, yaw)


def renders(objs):
    by = {o.name: o for o in objs}
    for nm, o in by.items():
        H.solo(objs, [o])
        top = 0.62 if nm == "pose_kneel" else 0.90
        H.clay(f"{NAME}_{nm}", (1.7, 1.35, 2.2), (0.0, top, 0.10), lens=42, res=(480, 640))
        H.ghost(f"{NAME}_{nm}_ghost", [o], (-1.6, 1.4, 2.2), (0.0, top, 0.10), lens=42, res=(480, 640))
    for r in range(3):
        nm = f"pose_touch_{r}"
        if nm in by:
            H.solo(objs, [by[nm]])
            L.proxy("drawer", (0.30, 0.22, 0.02), (0.40, ROWS[r], 0.43), color="5A3A22")
            H.clay(f"{NAME}_{nm}_hand", (1.15, ROWS[r] + 0.25, 0.05), (0.40, ROWS[r], 0.40), lens=50, res=(640, 640))
    if "pose_kneel" in by:
        H.solo(objs, [by["pose_kneel"]])
        L.proxy("socketwall", (0.6, 0.6, 0.02), (SOCKET_G[0], SOCKET_G[1], SOCKET_G[2] + 0.012), color="5A5852")
        H.clay(f"{NAME}_pose_kneel_hand", (-0.75, 1.30, 0.10), SOCKET_G, lens=50, res=(640, 640))
    if "pose_offer" in by:
        H.solo(objs, [by["pose_offer"]])
        L.import_ctx("nursery_crystal", CRYSTAL_G, 0.0)
        H.clay(f"{NAME}_pose_offer_hand", (-0.30, 1.55, 1.25), CRYSTAL_G, lens=55, res=(640, 640))
    # in context
    if "pose_touch_1" in by:
        H.solo(objs, [by["pose_touch_1"]])
        pos, yaw = H.world_mount(LIB_POS, LIB_YAW, ((2 - 1.5) * 0.33 + 0.40, 0.0, 0.87), 180.0)
        H.context(f"{NAME}_pose_touch_1_library", [by["pose_touch_1"]], by["pose_touch_1"], pos, yaw,
                  library_context(1, 2), (11.25, 1.45, -0.6), (12.55, 1.24, -0.6), fov=50)
    if "pose_kneel" in by:
        H.solo(objs, [by["pose_kneel"]])
        pos, yaw = KNEEL_MOUNT
        H.context(f"{NAME}_pose_kneel_secret", [by["pose_kneel"]], by["pose_kneel"], pos, yaw, memorial_context,
                  (0.6, 1.5, -1.8), (1.7, 0.9, -3.3), fov=52)
    if "pose_offer" in by:
        H.solo(objs, [by["pose_offer"]])
        pos, yaw = OFFER_MOUNT
        H.context(f"{NAME}_pose_offer_finale", [by["pose_offer"]], by["pose_offer"], pos, yaw, finale_context,
                  (0.0, 1.85, 3.75), (0.0, 1.15, 0.4), fov=66)
    H.solo(objs, objs)


def main():
    mrlib.reset_scene()
    objs = []
    for nm, fn in POSES.items():
        if ONLY and nm not in ONLY:
            continue
        o = fn()
        H.turn(o)
        objs.append(o)
    empties = []
    for o in objs:
        if o.name == "pose_offer":
            H.add_empty("crystal_mount", o, CRYSTAL_G)
            empties.append("crystal_mount")
            H.contact_report("palm under crystal_mount (0.057 below it)", o,
                             (CRYSTAL_G[0], CRYSTAL_G[1] - CRYSTAL_BOTTOM, CRYSTAL_G[2]), radius=0.04)
        if o.name == "pose_kneel":
            H.contact_report("right palm on socket 42", o, SOCKET_G, radius=0.04)
        if o.name.startswith("pose_touch_"):
            r = int(o.name[-1])
            H.contact_report(f"{o.name} left fingertips on the drawer", o, (0.40, ROWS[r], 0.42), radius=0.03)
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET for o in objs}, empties=empties, file_budget=FILE_BUDGET)
    if RENDER:
        renders(objs)


if __name__ == "__main__":
    main()
