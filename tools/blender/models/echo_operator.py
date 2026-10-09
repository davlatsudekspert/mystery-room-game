"""Light echo: the 1979 Choir Hall operator starting the hall at the control desk (Chapter 3 W4, port views only).

A man of about 40 in a grey knee-length work coat, a flat-topped work cap and a pair of headphones round his
neck (the cups resting on his collar). Five generic poses, each ONE closed mesh (root-level objects; the code
shows one at a time and crossfades through the 1 s flicker). No pose depends on which lever he pulls: the
code places him at `op_mount_<n>` (lever n) or `op_mount_knob` of control_desk.glb (floor empties rotated 180
deg about Y, so he faces the desk), and the contact points below meet lever n's grip or the knob.

Output: game/assets/models/echo_operator.glb (Godot axes; the figure faces +Z, -X = his right)
  pose_idle   standing a little back (feet centre 0.10 behind the origin), looking up and to his left at the
              step globes (head yaw 38 deg left, pitch 22 deg up), arms relaxed.
  pose_reach  right-hand grip on an upright lever's ball at (-0.15, 1.22, 0.50); left palm on the desk top
              (0.235, 0.872, 0.30), 0.08 behind the desk's front edge.
  pose_pull   right-hand grip at (-0.15, 1.12, 0.29): the same lever pulled 50 deg toward him; left palm on the
              desk top as in pose_reach.
  pose_knob   right hand on the master knob at (-0.15, 1.12, 0.40); hips back, leaning over the desk (feet
              centre 0.10 behind the origin, so his toes stay out of the desk front 0.07 ahead at op_mount_knob),
              left palm on the desk top at (0.25, 0.872, 0.20).
  pose_done   a step back (feet centre 0.25 behind the origin), head turned over his right shoulder toward the
              Choir rack (yaw 75 deg right).
Material: one slot, M_Echo. Budget: <= 6,000 tris per pose, <= 30,000 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_operator.py [-- --no-render] [-- --only <poses>]
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

NAME = "echo_operator"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 6000, 30000
TRIS = dict(body=3250, hand=430, head=1450)
VOXEL = 0.0037
HAND_S = 1.04
UPPER, FORE = 0.315, 0.262

# contacts (Godot figure frame)
GRIP_REST = (-0.15, 1.22, 0.50)
GRIP_PULLED = (-0.15, 1.12, 0.29)
KNOB = (-0.15, 1.12, 0.40)
LEVER_PIVOT = (-0.15, 0.95, 0.50)
# left palm resting on the desk top (top y = 0.86): 0.07 behind its front edge at the lever mounts (edge 0.22 ahead),
# 0.13 behind it at op_mount_knob (edge 0.07 ahead). Build space (x = his right, y forward, z up).
DESK_LEFT = Vector((-0.235, 0.300, 0.872))
DESK_LEFT_KNOB = Vector((-0.250, 0.200, 0.872))

P_HEAD = dict(E.MALE, nose=1.12, brow=1.6, jaw=1.12, chin=1.1)


# ------------------------------------------------------------------ head: cap and short hair
def short_hair(co, nrm):
    """Short back-and-sides crop (mostly under the cap)."""
    s = P_HEAD["scale"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    hl = np.interp(deg, [0, 30, 55, 72, 82, 95, 140, 180], [0.062, 0.064, 0.050, 0.026, -0.022, -0.016, -0.058,
                                                           -0.074]) * s
    m = E.smoothstep(hl - 0.002, hl + 0.006, z)
    sb = np.exp(-(((deg - 80) / 5.0) ** 2)) * E.smoothstep(-0.034 * s, -0.016 * s, z) * (1 - m)
    return nrm * ((0.0055 * m) + 0.003 * sb)[:, None]


def cap(_p):
    """A 1970s flat-topped work cap: a soft crown over the skull and a short peak, pushed back a little."""
    s = P_HEAD["scale"]
    crown = E.loft("h_cap", [(0, -0.016 * s, 0.040 * s), (0, -0.014 * s, 0.072 * s), (0, -0.012 * s, 0.104 * s),
                             (0, -0.010 * s, 0.124 * s)],
                   [(0.080 * s, 0.100 * s), (0.083 * s, 0.103 * s), (0.080 * s, 0.099 * s), (0.064 * s, 0.080 * s)],
                   side=(1, 0, 0), seg=28, sub=3, cap0=0.2, cap1=0.45)
    peak = E.ellipsoid("h_peak", (0, 0.092 * s, 0.047 * s), (0.074 * s, 0.050 * s, 0.0065 * s),
                       rot=E.rot_x(-14), seg=24, rings=8)
    button = E.ellipsoid("h_capbtn", (0, -0.010 * s, 0.135 * s), (0.008, 0.008, 0.005), seg=10, rings=6)
    return [crown, peak, button]


def head_kw(sp, yaw, pitch, roll=0.0, tilt=14.0):
    pivot = sp.point(sp.z_neck - 0.008, (0.0, 0.006, 0.0))
    nd = L.neck_dir(sp.yaw_chest, tilt)
    return dict(P=P_HEAD, pivot=pivot, nd=nd, yaw=yaw, pitch=pitch, roll=roll, hair_fn=short_hair, extras_fn=cap,
                neck_r=((0.058, 0.060), (0.054, 0.056), (0.054, 0.054)), voxel=0.0018)


# ------------------------------------------------------------------ body
def spine(hip_y, neck_dy, z_hip=0.93, z_neck=1.50, yaw_hip=0.0, yaw_chest=0.0, hip_x=0.0, neck_dx=0.0):
    return L.Spine(hip_xy=(hip_x, hip_y), neck_xy=(hip_x + neck_dx, hip_y + neck_dy), z_hip=z_hip, z_neck=z_neck,
                   yaw_hip=yaw_hip, yaw_chest=yaw_chest, z_twist0=z_hip + 0.04, z_twist1=z_neck - 0.17)


def coat(sp, key):
    rings = H.coat_rings(H.MAN_COAT, H.MAN_HIP, H.MAN_NECK, sp.z_hip, sp.z_neck, grow=0.004)
    c = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(c)
    zh = sp.z_hip
    parts = [c] + H.coat_details(key, sp, tree, female=False, collar_r=0.068, collar_z=sp.z_neck - 0.028,
                                 pockets=(0.120, zh - 0.01, zh - 0.14, 0.140), breast=(-0.100, zh + 0.39, zh + 0.315),
                                 buttons=(zh + 0.25, zh + 0.145, zh + 0.04), button_x=0.004)
    # pencil in the breast pocket
    base = E.hug(tree, [sp.point(zh + 0.35, (-0.115, 0.15, 0))], 0.006)[0]
    parts.append(E.limb(f"{key}_pencil", base, base + Vector((0.004, 0.004, 0.10)), [0.0052, 0.0052, 0.0046, 0.003],
                        ts=[0, 0.7, 0.88, 1.0], seg=10, side=(1, 0, 0), cap0=0.3, cap1=0.6))
    return parts, tree


def headphones(sp, key):
    """Headphones round the neck: the band behind the neck, the two cups resting on the collar in front."""
    zn = sp.z_neck
    parts = []
    cups = {}
    for sx in (1, -1):
        c = sp.point(zn - 0.052, (sx * 0.088, 0.048, 0.0))
        out = (sp.right(zn) * (sx * 0.55) + sp.front(zn) * 0.55 + Vector((0, 0, 0.62))).normalized()
        rot = L.frame_matrix(L.ortho(sp.right(zn) * sx, out).cross(out), L.ortho(sp.right(zn) * sx, out), out)
        parts.append(E.ellipsoid(f"{key}_cup{sx}", c + out * 0.004, (0.036, 0.036, 0.017), rot=rot, seg=18, rings=8))
        parts.append(E.torus_obj(f"{key}_cupring{sx}", c + out * 0.016, 0.026, 0.006, rot=rot, seg=18, mseg=6))
        cups[sx] = c
    path = [cups[-1] + Vector((0, 0, 0.022)), sp.point(zn - 0.02, (-0.080, -0.035, 0)),
            sp.point(zn - 0.012, (0.0, -0.078, 0)), sp.point(zn - 0.02, (0.080, -0.035, 0)),
            cups[1] + Vector((0, 0, 0.022))]
    parts.append(E.loft(f"{key}_band", path, [(0.007, 0.011)] * 5, side=(0, 0, 1), seg=10, sub=4, cap0=0.4, cap1=0.4))
    return parts


def legs(sp, key, feet, hip_dy=0.0):
    """feet: {s: (ankle_x, ankle_y, yaw)}; straight trouser legs from under the coat to the shoes."""
    parts = []
    for s in (1, -1):
        ax, ay, fy = feet[s]
        top = sp.point(0.66, (s * 0.098, hip_dy, 0.0))
        sh, ank = H.shoe_on(f"{key}_shoe{s}", (ax, ay), fy, heel=0.014, scale=1.07)
        parts += sh
        parts += L.trouser_leg(f"{key}_trouser{s}", top, ank, r_top=0.068, r_knee=0.062, r_hem=0.060)
    return parts


def shoulders(sp):
    z = sp.z_neck - 0.088
    return {1: sp.point(z, (0.178, 0.010, 0.0)), -1: sp.point(z, (-0.178, 0.010, 0.0))}


SLEEVE_R = (0.056, 0.053, 0.050, 0.047, 0.049, (0.027, 0.020), (0.048, 0.053, 0.048))


def folds_for(sp, sh, el, wr):
    def fn():
        k = []
        for s in (1, -1):
            inner = (sh[s] - el[s]).normalized() + (wr[s] - el[s]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[s] + inner.normalized() * 0.040, s=0.016, a=-0.0055),
                      dict(c=el[s] + inner.normalized() * 0.03 + (wr[s] - el[s]).normalized() * 0.035, s=0.012,
                           a=0.003)]
        zh = sp.z_hip
        k += L.groove([sp.point(zh + 0.26, (0.022, 0.16, 0)), sp.point(zh + 0.01, (0.022, 0.16, 0))], 0.005, -0.0028,
                      face=sp.front(zh + 0.1))
        k += L.groove([sp.point(zh - 0.01, (0.022, 0.20, 0)), sp.point(zh - 0.44, (0.012, 0.25, 0))], 0.009, -0.007,
                      face=sp.front(zh))
        k += L.groove([sp.point(zh - 0.07, (0.16, 0.07, 0)), sp.point(zh - 0.43, (0.175, 0.08, 0))], 0.012, -0.0035)
        k += L.groove([sp.point(zh - 0.07, (-0.16, 0.05, 0)), sp.point(zh - 0.43, (-0.18, 0.04, 0))], 0.011, -0.003)
        k += L.groove([sp.point(zh - 0.23, (0.0, -0.15, 0)), sp.point(zh - 0.45, (0.0, -0.15, 0))], 0.004, -0.004,
                      face=-sp.front(zh))
        k += L.groove([sp.point(zh + 0.43, (0.12, -0.12, 0)), sp.point(zh + 0.21, (0.03, -0.12, 0))], 0.013, -0.0025,
                      face=-sp.front(zh + 0.3))
        k += L.groove([sp.point(zh + 0.43, (-0.12, -0.12, 0)), sp.point(zh + 0.21, (-0.03, -0.12, 0))], 0.013,
                      -0.0025, face=-sp.front(zh + 0.3))
        return k
    return fn


def flutes_for(sp):
    def fn(body):
        hx, hy = sp.hip.x, sp.hip.y

        def amp(co, t):
            return 0.006 * E.smoothstep(sp.z_hip - 0.17, sp.z_hip - 0.44, co[:, 2]) * \
                (0.65 + 0.35 * np.sin(co[:, 0] * 19.0 + co[:, 1] * 15.0))
        L.flutes(body, (hx, hy + 0.01, 0.0), (0, 0, 1), 8, amp, phase=2.0,
                 region=lambda co: E.smoothstep(sp.z_hip - 0.17, sp.z_hip - 0.27, co[:, 2]) * (co[:, 2] > sp.z_hip - 0.47))
    return fn


def lever_grip_frame(pulled_deg):
    """Overhand grip on the lever ball (pull toward him): fingers over the top and down the far side, thumb inside.
    The frame turns with the lever (about build +X)."""
    R = Matrix.Rotation(math.radians(pulled_deg), 3, "X")
    F = R @ Vector((0.0, 0.70, 0.71)).normalized()
    N = R @ Vector((0.0, 0.71, -0.70)).normalized()
    return F, N


def grip_hand(key, centre, F, N, right=True, curls=None):
    wr = H.grip_wrist(centre, F, N, HAND_S)
    curls = curls or [(52, 66, 44), (56, 70, 46), (60, 72, 46), (64, 72, 44)]

    def thumb(info):
        # the thumb closes over the inner side of the ball toward the index's middle phalanx
        j = info["joints"][0]
        tip = j[1].lerp(j[2], 0.3) + info["N"] * 0.014 * HAND_S + info["S"] * 0.012 * HAND_S
        return L.thumb_to(info, tip, HAND_S, bulge=0.008)
    objs, info = H.hand(f"{key}_handR", wr, F, N, right, curls, spread=[3, 0, -3, -7], thumb=thumb, scale=HAND_S,
                        width=0.082, finger_r=0.0088)
    return objs, wr, info


# ------------------------------------------------------------------ poses
def build_standing(key, sp, feet, right_hand, left_hand, head, legs_dy=0.0):
    """Common standing figure: coat, details, headphones, legs, both arms and hands, head."""
    parts, _tree = coat(sp, key)
    parts += headphones(sp, key)
    parts += legs(sp, key, feet, hip_dy=legs_dy)
    sh = shoulders(sp)
    el, wr = {}, {}
    hands = []
    for s, spec in ((1, right_hand), (-1, left_hand)):
        w, pole, make = spec
        ap, e = H.arm(f"{key}_arm{s}", sh[s], vec(w), UPPER, FORE, pole, r=SLEEVE_R, sp=sp, side=s)
        parts += ap
        el[s], wr[s] = e, vec(w)
        hp = make(e, vec(w))
        hands.append((hp, vec(w)))
    obj = H.make_pose(key, parts, hands, head, TRIS, voxel=VOXEL, folds=folds_for(sp, sh, el, wr),
                      flutes=flutes_for(sp))
    return obj


def relaxed(key, right, pron=8.0, bend=(0.0, 0.10, -0.05), curl=1.0):
    def make(e, w):
        objs, _ = H.relaxed_hand(f"{key}_hand{'R' if right else 'L'}", e, w, right, HAND_S, pron, bend, curl)
        return objs
    return make


def fixed_hand(objs):
    return lambda e, w: objs


def pose_idle():
    key = "pose_idle"
    sp = spine(-0.105, 0.004, yaw_hip=6.0, yaw_chest=14.0)
    feet = {1: (0.112, -0.100, -6.0), -1: (-0.108, -0.118, 16.0)}
    sh = shoulders(sp)
    right = (sh[1] + Vector((0.065, 0.040, -0.535)), sh[1] + Vector((0.45, -0.35, -0.25)), relaxed(key, True))
    left = (sh[-1] + Vector((-0.060, 0.050, -0.530)), sh[-1] + Vector((-0.40, -0.40, -0.30)), relaxed(key, False))
    return build_standing(key, sp, feet, right, left, head_kw(sp, 38.0, 22.0, 3.0, tilt=6.0))


def pose_reach():
    key = "pose_reach"
    sp = spine(-0.030, 0.105, z_hip=0.925, z_neck=1.48, yaw_hip=-3.0, yaw_chest=-10.0)
    feet = {1: (0.110, 0.010, -8.0), -1: (-0.110, -0.030, 8.0)}
    F, N = lever_grip_frame(0.0)
    hp, wr, _ = grip_hand(key, H.g2b(GRIP_REST), F, N)
    sh = shoulders(sp)
    right = (wr, sh[1] + Vector((0.55, 0.05, -0.30)), fixed_hand(hp))
    lp, lw, _ = H.flat_hand(f"{key}_handL", DESK_LEFT, (0.15, 0.98, 0.0), (0, 0, -1), False, HAND_S)
    left = (lw, sh[-1] + Vector((-0.45, -0.10, -0.30)), fixed_hand(lp))
    return build_standing(key, sp, feet, right, left, head_kw(sp, -10.0, -16.0, 0.0, tilt=22.0))


def pose_pull():
    key = "pose_pull"
    sp = spine(-0.055, 0.040, z_hip=0.925, z_neck=1.495, yaw_hip=-4.0, yaw_chest=-12.0)
    feet = {1: (0.112, -0.010, -8.0), -1: (-0.112, -0.090, 10.0)}
    F, N = lever_grip_frame(50.0)
    hp, wr, _ = grip_hand(key, H.g2b(GRIP_PULLED), F, N)
    sh = shoulders(sp)
    right = (wr, sh[1] + Vector((0.50, -0.20, -0.35)), fixed_hand(hp))
    lp, lw, _ = H.flat_hand(f"{key}_handL", DESK_LEFT, (0.15, 0.98, 0.0), (0, 0, -1), False, HAND_S)
    left = (lw, sh[-1] + Vector((-0.45, -0.10, -0.30)), fixed_hand(lp))
    return build_standing(key, sp, feet, right, left, head_kw(sp, -8.0, -24.0, 0.0, tilt=16.0))


def pose_knob():
    key = "pose_knob"
    sp = spine(-0.115, 0.165, z_hip=0.915, z_neck=1.455, yaw_hip=-2.0, yaw_chest=-8.0)
    feet = {1: (0.112, -0.095, -7.0), -1: (-0.110, -0.110, 9.0)}
    c = H.g2b(KNOB)
    F = Vector((0.0, 0.22, 0.975)).normalized()
    N = Vector((0.0, 0.975, -0.22)).normalized()
    wr = H.grip_wrist(c, F, N, HAND_S, along=0.072, out=0.044)

    def thumb(info):
        tip = c + Vector((-0.040, -0.030, -0.030))
        return L.thumb_to(info, tip, HAND_S, bulge=0.010)
    hp, _info = H.hand(f"{key}_handR", wr, F, N, True, [(34, 48, 32), (36, 50, 32), (40, 50, 30), (44, 50, 28)],
                       spread=[8, 2, -5, -12], thumb=thumb, scale=HAND_S, width=0.082, finger_r=0.0088)
    sh = shoulders(sp)
    right = (wr, sh[1] + Vector((0.50, 0.05, -0.35)), fixed_hand(hp))
    lp, lw, _ = H.flat_hand(f"{key}_handL", DESK_LEFT_KNOB, (0.20, 0.97, 0.0), (0, 0, -1), False, HAND_S)
    left = (lw, sh[-1] + Vector((-0.45, -0.10, -0.30)), fixed_hand(lp))
    return build_standing(key, sp, feet, right, left, head_kw(sp, -6.0, -20.0, 0.0, tilt=26.0), legs_dy=-0.005)


def pose_done():
    key = "pose_done"
    sp = spine(-0.250, -0.010, z_hip=0.925, z_neck=1.495, yaw_hip=-8.0, yaw_chest=-22.0)
    feet = {1: (0.118, -0.330, -14.0), -1: (-0.100, -0.170, 4.0)}
    sh = shoulders(sp)
    right = (sh[1] + Vector((0.075, -0.060, -0.530)), sh[1] + Vector((0.45, -0.20, -0.25)), relaxed(key, True))
    left = (sh[-1] + Vector((-0.050, 0.080, -0.525)), sh[-1] + Vector((-0.40, -0.30, -0.30)), relaxed(key, False))
    return build_standing(key, sp, feet, right, left, head_kw(sp, -75.0, 5.0, -3.0, tilt=8.0))


POSES = {"pose_idle": pose_idle, "pose_reach": pose_reach, "pose_pull": pose_pull, "pose_knob": pose_knob,
         "pose_done": pose_done}


# ------------------------------------------------------------------ QA
DESK_POS = (-8.0, 0.0, 0.5)


def lever_world(n, pulled):
    x = -8.0 - (n - 3) * 0.36
    if pulled:
        return (x, 1.124, 0.5 - 0.327)
    return (x, 1.22, 0.38)


def desk_context(n_lit=3, pulled=None):
    def build():
        if not L.import_ctx("control_desk", DESK_POS, 180.0):
            L.proxy("desk", (2.6, 0.86, 0.8), (-8.0, 0.43, 0.5), color="4F5D55")
            L.proxy("quadrant", (2.0, 0.08, 0.18), (-8.0, 0.90, 0.38), color="3B4640")
            L.proxy("knobbox", (0.30, 0.44, 0.30), (-9.07, 1.08, 0.5), color="3B4640")
            L.proxy("knob", (0.09, 0.09, 0.03), (-9.07, 1.12, 0.415), color="1C1612")
            for n in range(1, 6):
                x = -8.0 - (n - 3) * 0.36
                if pulled == n:
                    gx, gy, gz = lever_world(n, True)
                    L.proxy(f"lever{n}", (0.016, 0.27, 0.016), ((x + gx) / 2, (0.95 + gy) / 2, (0.38 + gz) / 2),
                            color="B08D57")
                    L.proxy(f"ball{n}", (0.045, 0.045, 0.045), (gx, gy, gz), color="B08D57")
                else:
                    L.proxy(f"lever{n}", (0.016, 0.27, 0.016), (x, 1.085, 0.38), color="B08D57")
                    L.proxy(f"ball{n}", (0.045, 0.045, 0.045), (x, 1.22, 0.38), color="B08D57")
            L.proxy("mast", (0.03, 0.82, 0.03), (-6.80, 1.29, 0.2), color="3B4640")
            for k in range(1, 6):
                L.proxy(f"globe{k}", (0.13, 0.13, 0.13), (-6.80, 1.30 + 0.17 * (k - 1), 0.2), color="E8DFC8",
                        emit="FFE2B0" if k <= n_lit else None)
        L.proxy("floor", (8.0, 0.02, 8.0), (-8.0, -0.01, 0.0), color="5A5852")
        L.proxy("wall_n", (8.5, 6.0, 0.1), (-8.75, 3.0, -4.05), color="6F8C78")
    return build


def op_mount(n):
    """World (pos, yaw) of op_mount_<n> (n = 0 -> op_mount_knob)."""
    local = (0.92, 0.0, 0.47) if n == 0 else ((n - 3) * 0.36 - 0.15, 0.0, 0.62)
    return H.world_mount(DESK_POS, 180.0, local, 180.0)


def renders(objs):
    by = {o.name: o for o in objs}
    for nm, o in by.items():
        H.solo(objs, [o])
        H.clay(f"{NAME}_{nm}", (1.6, 1.4, 2.4), (0.0, 0.92, 0.05), lens=42, res=(480, 640))
    # ghost look, all five side by side would overlap: render each from the front-left
    for nm, o in by.items():
        H.solo(objs, [o])
        H.ghost(f"{NAME}_{nm}_ghost", [o], (-1.4, 1.3, 2.6), (0.0, 0.92, 0.05), lens=42, res=(480, 640))
    # contact close-ups with the lever / knob proxies at their contact points (figure frame)
    for nm, (pt, lever_deg) in {"pose_reach": (GRIP_REST, 0.0), "pose_pull": (GRIP_PULLED, 50.0),
                                "pose_knob": (KNOB, None)}.items():
        if nm not in by:
            continue
        H.solo(objs, [by[nm]])
        if lever_deg is None:
            L.proxy("knobp", (0.09, 0.09, 0.035), (pt[0], pt[1], pt[2] + 0.0), color="1C1612")
            L.proxy("knobbox", (0.30, 0.44, 0.04), (pt[0] - 0.15, pt[1] - 0.04, pt[2] + 0.035), color="3B4640")
        else:
            piv = LEVER_PIVOT
            L.proxy("ball", (0.045, 0.045, 0.045), pt, color="B08D57")
            mid = ((piv[0] + pt[0]) / 2, (piv[1] + pt[1]) / 2, (piv[2] + pt[2]) / 2)
            o = L.proxy("stem", (0.016, 0.27, 0.016), mid, color="B08D57")
            o.rotation_euler = (math.radians(-lever_deg), 0.0, 0.0)
        H.clay(f"{NAME}_{nm}_hand", (pt[0] - 0.45, pt[1] + 0.25, pt[2] - 0.30), pt, lens=55, res=(640, 640))
        H.clay(f"{NAME}_{nm}_hand2", (pt[0] + 0.05, pt[1] + 0.45, pt[2] + 0.35), pt, lens=55, res=(640, 640))
    # in context: the port views (each port's levers) and the desk view
    ctx = [("pose_reach", 2, False, "port_a", (-4.8, 0.95, 2.5), (-7.4, 1.35, 0.5), 36),
           ("pose_pull", 4, True, "port_b", (-11.75, 4.65, 1.75), (-8.2, 1.15, 0.45), 34),
           ("pose_knob", 0, False, "port_c", (-8.6, 4.95, 1.8), (-8.3, 1.2, 0.4), 40),
           ("pose_idle", 5, False, "port_c_lever5", (-8.6, 4.95, 1.8), (-8.3, 1.2, 0.4), 40),
           ("pose_done", 1, False, "desk_view", (-7.8, 1.85, -1.6), (-7.75, 1.2, 0.35), 60)]
    for nm, n, pulled, tag, cam, tgt, fov in ctx:
        if nm not in by:
            continue
        H.solo(objs, [by[nm]])
        pos, yaw = op_mount(n)
        H.context(f"{NAME}_{nm}_{tag}", [by[nm]], by[nm], pos, yaw, desk_context(3, n if pulled else None), cam, tgt,
                  fov=fov)
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
        print(f"[echo3] {nm}: {E.tris(o)} tris")
    for o in objs:
        pts = {"pose_reach": GRIP_REST, "pose_pull": GRIP_PULLED, "pose_knob": KNOB}
        if o.name in pts:
            H.contact_report(f"{o.name} right-hand grip", o, pts[o.name])
    for o in objs:
        # desk front: 0.22 ahead at op_mount_<n>, 0.07 ahead at op_mount_knob (Godot +Z = Blender -Y here)
        low = [o.matrix_world @ v.co for v in o.data.vertices if (o.matrix_world @ v.co).z < 0.86]
        front = max(-p.y for p in low)
        toes = max(-p.y for p in low if p.z < 0.12)
        print(f"[echo3] {o.name}: below the desk top (y < 0.86) the figure reaches z = {front:+.3f} "
              f"(toes {toes:+.3f}); desk front at +0.22 (levers) / +0.07 (knob)")
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET for o in objs}, file_budget=FILE_BUDGET)
    if RENDER:
        renders(objs)


if __name__ == "__main__":
    main()
