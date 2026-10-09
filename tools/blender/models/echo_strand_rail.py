"""Light echo: Prof. Emil Strand, 1979, in the Resonance Gallery (Chapter 3: kept echo `strand_rail`, finale).

The face, beard and fringe of echo_strand_standing (its P_HEAD and hair_disp), the same long coat to below the
knee, a little stooped. Two root-level poses, each ONE closed mesh (M_Echo):

Output: game/assets/models/echo_strand_rail.glb (Godot axes; the figure faces +Z, -X = his right)
  pose_rail   leaning on the gallery rail: both forearms lie along the rail top (y = 1.0) at z = +0.30 .. +0.36,
              hands loosely together over the middle, hips back, looking down into the shaft (head pitch -42).
              At shell_gallery `echo_rail_mount` (-2.05, 0, -0.40), yaw 79.
  pose_offer  standing, his right arm out at chest height holding his tuning fork upright in his fist; the left
              arm relaxed. At `echo_strand_mount` (-2.30, 0, 1.00), yaw 40.
  fork_mount  empty, child of pose_offer, at (-0.20, 1.30, 0.45) inside the fist, identity: strand_fork.glb
              (origin = its centre of mass, on the stem) parented there stands upright with its stem in the fist.
Budget: <= 9,000 tris per pose, <= 18,000 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_strand_rail.py [-- --no-render] [-- --only pose_rail]
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

NAME = "echo_strand_rail"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 9000, 18000
TRIS = dict(body=4900, hand=620, head=2100)
VOXEL = 0.0034
HAND_S = 1.06
UPPER, FORE = 0.31, 0.265
SRC = H.load_model("echo_strand_standing")        # P_HEAD, hair_disp: Strand's face lineage
FORK_G = (-0.20, 1.30, 0.45)
RAIL_TOP, RAIL_Z0, RAIL_Z1 = 1.0, 0.30, 0.36
SLEEVE_R = (0.058, 0.055, 0.052, 0.049, 0.051, (0.028, 0.021), (0.052, 0.058, 0.052))
# his long coat: the man's coat table plus a hem ring below the knee (echo_strand_standing reaches mid-calf)
LONG_HEM = (0.380, 0.220, 0.218, 0.160, 0.155, 2.2, 0.010, 0.020)


def coat(sp, key):
    rings = H.coat_rings([LONG_HEM] + H.MAN_COAT, H.MAN_HIP, H.MAN_NECK, sp.z_hip, sp.z_neck, grow=0.003)
    c = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(c)
    zh = sp.z_hip
    parts = [c] + H.coat_details(key, sp, tree, female=False, collar_r=0.068, collar_z=sp.z_neck - 0.028,
                                 pockets=(0.120, zh - 0.01, zh - 0.12, 0.135), breast=(-0.100, zh + 0.39, zh + 0.32),
                                 buttons=(zh + 0.22, zh + 0.12, zh + 0.02), button_x=0.018)
    return parts


def legs(sp, key, feet):
    parts = []
    for s in (1, -1):
        ax, ay, fy = feet[s]
        top = sp.point(0.55, (s * 0.098, 0.0, 0.0))
        sh, ank = H.shoe_on(f"{key}_shoe{s}", (ax, ay), fy, heel=0.014, scale=1.08)
        parts += sh
        parts += L.trouser_leg(f"{key}_trouser{s}", top, ank, r_top=0.066, r_knee=0.060, r_hem=0.058)
    return parts


def shoulders(sp):
    z = sp.z_neck - 0.085
    return {1: sp.point(z, (0.172, 0.006, 0.0)), -1: sp.point(z, (-0.172, 0.006, 0.0))}


def head_kw(sp, yaw, pitch, roll=0.0, tilt=20.0):
    pivot = sp.point(sp.z_neck - 0.006, (0.0, 0.006, 0.0))
    nd = L.neck_dir(sp.yaw_chest, tilt)
    return dict(P=SRC.P_HEAD, pivot=pivot, nd=nd, yaw=yaw, pitch=pitch, roll=roll, hair_fn=SRC.hair_disp,
                neck_r=((0.058, 0.060), (0.054, 0.056), (0.054, 0.054)), voxel=0.0016,
                kernels=[dict(c=(sx * 0.03, 0.088, -0.037), s=(0.01, 0.01, 0.022), a=-0.0012, face=(0, 1, 0))
                         for sx in (1, -1)])


def folds_for(sp, sh, el, wr, extra=()):
    def fn():
        k = []
        for s in (1, -1):
            inner = (sh[s] - el[s]).normalized() + (wr[s] - el[s]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[s] + inner.normalized() * 0.040, s=0.016, a=-0.0055),
                      dict(c=el[s] + inner.normalized() * 0.03 + (wr[s] - el[s]).normalized() * 0.035, s=0.012,
                           a=0.003)]
        zh = sp.z_hip
        k += L.groove([sp.point(zh + 0.24, (0.020, 0.16, 0)), sp.point(zh - 0.02, (0.020, 0.16, 0))], 0.005, -0.0028,
                      face=sp.front(zh + 0.1))
        k += L.groove([sp.point(zh - 0.03, (0.020, 0.20, 0)), sp.point(zh - 0.52, (0.012, 0.25, 0))], 0.009, -0.007,
                      face=sp.front(zh))
        k += L.groove([sp.point(zh - 0.10, (0.16, 0.07, 0)), sp.point(zh - 0.50, (0.175, 0.08, 0))], 0.012, -0.0035)
        k += L.groove([sp.point(zh - 0.10, (-0.16, 0.05, 0)), sp.point(zh - 0.50, (-0.18, 0.04, 0))], 0.011, -0.003)
        k += L.groove([sp.point(zh - 0.25, (0.0, -0.15, 0)), sp.point(zh - 0.53, (0.0, -0.15, 0))], 0.004, -0.004,
                      face=-sp.front(zh))
        k.append(dict(c=sp.point(zh + 0.42, (0.0, -0.12, 0)), s=(0.10, 0.05, 0.06), a=0.004, face=-sp.front(zh + 0.4)))
        return k + list(extra)
    return fn


def flutes_for(sp):
    def fn(body):
        def amp(co, t):
            return 0.0065 * E.smoothstep(sp.z_hip - 0.20, sp.z_hip - 0.52, co[:, 2]) * \
                (0.65 + 0.35 * np.sin(co[:, 0] * 19.0 + co[:, 1] * 15.0))
        L.flutes(body, (sp.hip.x, sp.hip.y + 0.01, 0.0), (0, 0, 1), 8, amp, phase=1.2,
                 region=lambda co: E.smoothstep(sp.z_hip - 0.20, sp.z_hip - 0.30, co[:, 2]) * (co[:, 2] > 0.36))
    return fn


# ------------------------------------------------------------------ poses
def pose_rail():
    key = "pose_rail"
    sp = L.Spine(hip_xy=(0.0, -0.085), neck_xy=(0.0, 0.205), z_hip=0.915, z_neck=1.395, yaw_hip=0.0, yaw_chest=0.0,
                 z_twist0=0.95, z_twist1=1.25)
    feet = {1: (0.115, -0.060, -8.0), -1: (-0.112, -0.010, 9.0)}
    parts = coat(sp, key) + legs(sp, key, feet)
    sh = shoulders(sp)
    yr = 0.5 * (RAIL_Z0 + RAIL_Z1)
    zf = RAIL_TOP + 0.044                      # forearm centre line: the sleeve rests on the rail top
    el = {1: vec((0.215, yr + 0.010, zf + 0.004)), -1: vec((-0.215, yr + 0.010, zf + 0.004))}
    wr = {1: vec((0.035, yr - 0.010, zf + 0.010)), -1: vec((-0.040, yr + 0.004, zf + 0.004))}
    hands = []
    for s in (1, -1):
        sl, _cuff = L.sleeve(f"{key}_arm{s}", sh[s], el[s], wr[s], r_sh=SLEEVE_R[0], r_up=SLEEVE_R[1], r_el=SLEEVE_R[2],
                             r_fore=SLEEVE_R[3], r_cuff=SLEEVE_R[4], cuff_len=0.026, wrist_r=SLEEVE_R[5],
                             deltoid=SLEEVE_R[6], cuff_gap=0.026, start_back=0.006,
                             deltoid_off=sp.right(sh[s].z) * (0.006 * s) + Vector((0, 0, -0.010)))
        for p in sl:
            if p.name.endswith("_wrist"):
                bpy.data.objects.remove(p, do_unlink=True)
            else:
                parts.append(p)
        fdir = (wr[s] - el[s]).normalized()
        parts.append(E.limb(f"{key}_wstub{s}", wr[s] - fdir * 0.05, wr[s] + fdir * 0.004,
                            [SLEEVE_R[5], (SLEEVE_R[5][0] * 0.97, SLEEVE_R[5][1] * 0.97)], seg=14, side=(0, 0, 1)))
    # hands loosely together over the rail, the right lying over the left's fingers, both drooping a little
    Fr = Vector((-0.75, 0.55, -0.22)).normalized()
    hr, _ = H.hand(f"{key}_handR", wr[1], Fr, L.ortho((-0.2, 0.1, -1.0), Fr), True,
                   [(20, 30, 14), (24, 34, 16), (28, 36, 18), (32, 38, 18)], spread=[3, 0, -2, -5], scale=HAND_S)
    Fl = Vector((0.75, 0.58, -0.20)).normalized()
    hl, _ = H.hand(f"{key}_handL", wr[-1], Fl, L.ortho((0.2, 0.1, -1.0), Fl), False,
                   [(24, 34, 16), (28, 38, 18), (32, 40, 20), (36, 42, 20)], spread=[3, 0, -2, -5], scale=HAND_S)
    hands = [(hr, wr[1]), (hl, wr[-1])]
    extra = [dict(c=el[s] + Vector((0, 0, -0.035)), s=(0.05, 0.02, 0.012), a=-0.004) for s in (1, -1)]   # pressed sleeves
    obj = H.make_pose(key, parts, hands, head_kw(sp, 0.0, -42.0, 0.0, tilt=34.0), TRIS, voxel=VOXEL,
                      folds=folds_for(sp, sh, el, wr, extra), flutes=flutes_for(sp))
    return obj


def pose_offer():
    key = "pose_offer"
    sp = L.Spine(hip_xy=(0.0, -0.010), neck_xy=(0.0, 0.050), z_hip=0.920, z_neck=1.475, yaw_hip=4.0, yaw_chest=-6.0,
                 z_twist0=0.95, z_twist1=1.30)
    feet = {1: (0.112, 0.030, -10.0), -1: (-0.110, -0.040, 10.0)}
    parts = coat(sp, key) + legs(sp, key, feet)
    sh = shoulders(sp)
    # right fist round the fork's stem: the stem runs up through the fist (thumb on top), knuckles forward
    g = H.g2b(FORK_G)
    S = Vector((0.0, 0.0, 1.0))
    N = Vector((-1.0, 0.10, 0.0)).normalized()
    F = N.cross(S).normalized()                       # right hand: S = F x N
    wr_r = H.grip_wrist(g + Vector((0.0, 0.0, -0.010)), F, N, HAND_S, along=0.076, out=0.020)

    def thumb(info):
        j = info["joints"][0]
        tip = j[1].lerp(j[2], 0.5) + info["S"] * 0.004 + info["N"] * 0.012
        return L.thumb_to(info, tip, HAND_S, bulge=0.006)
    hr, _ = H.hand(f"{key}_handR", wr_r, F, N, True, [(78, 96, 66), (82, 98, 66), (86, 96, 62), (90, 94, 58)],
                   spread=[0, 0, -2, -4], thumb=thumb, scale=HAND_S, width=0.084, finger_r=0.0090)
    wr_l = sh[-1] + Vector((-0.060, 0.050, -0.530))
    parts_r, el_r = H.arm(f"{key}_arm1", sh[1], wr_r, UPPER, FORE, sh[1] + Vector((0.40, -0.20, -0.45)), r=SLEEVE_R,
                          sp=sp, side=1)
    parts_l, el_l = H.arm(f"{key}_arm-1", sh[-1], wr_l, UPPER, FORE, sh[-1] + Vector((-0.40, -0.40, -0.30)),
                          r=SLEEVE_R, sp=sp, side=-1)
    parts += parts_r + parts_l
    hl, _ = H.relaxed_hand(f"{key}_handL", el_l, wr_l, False, HAND_S)
    hands = [(hr, wr_r), (hl, wr_l)]
    obj = H.make_pose(key, parts, hands, head_kw(sp, 0.0, -2.0, 0.0, tilt=14.0), TRIS, voxel=VOXEL,
                      folds=folds_for(sp, sh, {1: el_r, -1: el_l}, {1: wr_r, -1: wr_l}), flutes=flutes_for(sp))
    return obj


POSES = {"pose_rail": pose_rail, "pose_offer": pose_offer}


# ------------------------------------------------------------------ QA
RAIL_MOUNT = ((-2.05, 0.0, -0.40), 79.0)
OFFER_MOUNT = ((-2.30, 0.0, 1.00), 40.0)


def gallery_context(fork=True):
    def build():
        if not L.import_ctx("shell_gallery", (0.0, 0.0, 0.0), 0.0):
            L.proxy("floor", (9.0, 0.02, 9.0), (0.0, -0.01, 0.0), color="8A8579")
        L.import_ctx("gallery_console", (0.0, 0.0, 2.6), 0.0)
        if fork:
            pos, yaw = OFFER_MOUNT
            a = math.radians(yaw)
            x, y, z = FORK_G
            fp = (pos[0] + x * math.cos(a) + z * math.sin(a), y, pos[2] - x * math.sin(a) + z * math.cos(a))
            L.import_ctx("strand_fork", fp, yaw)
    return build


def rail_proxy():
    """The rail top (y 1.0) as a box across the figure's front at z 0.30 .. 0.36 (figure frame)."""
    L.proxy("rail", (1.2, 0.04, 0.04), (0.0, RAIL_TOP - 0.02, 0.339), color="B08D57")


def renders(objs):
    by = {o.name: o for o in objs}
    for nm, o in by.items():
        H.solo(objs, [o])
        if nm == "pose_rail":
            rail_proxy()
        H.clay(f"{NAME}_{nm}", (1.6, 1.4, 2.3), (0.0, 0.95, 0.10), lens=42, res=(480, 640))
        if nm == "pose_rail":
            rail_proxy()
        H.clay(f"{NAME}_{nm}_2", (2.4, 1.3, -0.2), (0.0, 0.95, 0.10), lens=42, res=(480, 640))
        H.ghost(f"{NAME}_{nm}_3", [o], (-1.3, 1.5, 2.4), (0.0, 0.95, 0.10), lens=42, res=(480, 640))
    if "pose_offer" in by:
        H.solo(objs, [by["pose_offer"]])
        L.import_ctx("strand_fork", (FORK_G[0], FORK_G[1], FORK_G[2]), 0.0)
        H.clay(f"{NAME}_pose_offer_4", (0.35, 1.45, 1.25), FORK_G, lens=55, res=(640, 640))          # fist and fork
    # in context: the kept echo at the rail (port_c memory view) and the finale stance
    if "pose_rail" in by:
        H.solo(objs, [by["pose_rail"]])
        pos, yaw = RAIL_MOUNT
        H.context(f"{NAME}_pose_rail_5", [by["pose_rail"]], by["pose_rail"], pos, yaw, gallery_context(False),
                  (1.2, 1.65, 2.4), (-2.05, 1.35, -0.4), fov=50)
    if "pose_offer" in by:
        H.solo(objs, [by["pose_offer"]])
        pos, yaw = OFFER_MOUNT
        H.context(f"{NAME}_pose_offer_5", [by["pose_offer"]], by["pose_offer"], pos, yaw, gallery_context(True),
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
            H.add_empty("fork_mount", o, FORK_G)
            empties.append("fork_mount")
            H.contact_report("fork_mount (inside the fist)", o, FORK_G, radius=0.05)
        if o.name == "pose_rail":
            low = [o.matrix_world @ v.co for v in o.data.vertices
                   if RAIL_Z0 - 0.06 < -(o.matrix_world @ v.co).y < RAIL_Z1 + 0.06 and abs((o.matrix_world @ v.co).x) < 0.30]
            under = min(p.z for p in low) if low else float("nan")
            print(f"[echo3] pose_rail: lowest point over the rail band (z 0.24 .. 0.42, |x| < 0.30): y = {under:.3f} "
                  f"(rail top 1.0)")
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET for o in objs}, empties=empties, file_budget=FILE_BUDGET)
    if RENDER:
        renders(objs)


if __name__ == "__main__":
    main()
