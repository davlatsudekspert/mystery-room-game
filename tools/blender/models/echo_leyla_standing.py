"""Light echo: Dr. Leyla Rahimova, 1979, standing in the projection booth and pointing at slide-cabinet
drawer 2 (Chapter 2, leave path). Same face and hair as echo_leyla_sitting (Chapter 1).

Output: game/assets/models/echo_leyla_standing.glb (Godot axes below; the model faces +Z)
  echo_body  origin = floor between her feet. Height to the crown ~1.65 m. Lab coat to just below the knee
             over a skirt, stockings, low block-heel shoes. Her RIGHT arm points forward-down at the target
             TARGET_G (model-local Godot), her left hand hangs relaxed. Body turned 10 deg (hips) .. 24 deg
             (chest) to her left toward the drawer, head 34 deg left and pitched down.
  echo_head  head + neck + hair + bun, child of echo_body, origin = neck pivot (base of the neck inside the
             collar), identity rotation. Rotate about its local +Y to turn the head.
Placement (docs/models/ch2.md section 1): world (-4.15, 0, 2.62), yaw -90. With that placement model +Z =
world -X and model +X = world +Z, so TARGET_G = (0.18, 0.68, 0.40) is the front centre of slide-cabinet drawer 2
(world (-4.55, 0.68, 2.80)). The pointing line (wrist -> index tip) passes within a few cm of it.
Material: one slot, M_Echo (replaced in Godot by the additive light-echo shader). One closed shell per object.

Run: blender -b --factory-startup -P tools/blender/models/echo_leyla_standing.py [-- --no-render] [-- --dev <dir>]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch2_echoes as L  # noqa: E402
import lib_echo as E  # noqa: E402
import mrlib  # noqa: E402
from lib_echo import vec  # noqa: E402

NAME = "echo_leyla_standing"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
DEV = ARGS[ARGS.index("--dev") + 1] if "--dev" in ARGS else None
BUDGET = 14000
BODY_TRIS, HAND_TRIS, HEAD_TRIS = 7900, 1150, 2900

PLACE, YAW = (-4.15, 0.0, 2.62), -90.0
TARGET_G = (0.18, 0.68, 0.40)                 # drawer 2 front centre, model-local Godot
TARGET = L.godot_to_build(TARGET_G)           # build space: (-0.18, 0.40, 0.68)

# ------------------------------------------------------------------ skeleton (build space: +Y forward, +X her right)
YAW_HIP, YAW_CHEST = 14.0, 30.0
SP = L.Spine(hip_xy=(-0.012, 0.0), neck_xy=(-0.052, 0.070), z_hip=0.86, z_neck=1.41,
             yaw_hip=YAW_HIP, yaw_chest=YAW_CHEST, z_twist0=0.9, z_twist1=1.24)


def hipf(p) -> Vector:
    """Hip-frame point (x right, y front, z up) -> build space."""
    return L.rz(YAW_HIP, p)


# weight on the left leg (contrapposto): left hip higher, right knee relaxed forward
HIP = {1: hipf((0.085, 0.0, 0.842)), -1: hipf((-0.088, 0.0, 0.860))}
KNEE = {1: hipf((0.098, 0.062, 0.458)), -1: hipf((-0.082, 0.012, 0.470))}
ANKLE = {1: hipf((0.116, 0.050, 0.082)), -1: hipf((-0.080, -0.012, 0.082))}
FOOT_YAW = {1: YAW_HIP - 13.0, -1: YAW_HIP + 7.0}
SHOULDER = {1: SP.point(1.330, (0.154, 0.018, 0)), -1: SP.point(1.338, (-0.156, -0.004, 0))}
UPPER_ARM, FOREARM = 0.300, 0.236
HAND_S = 0.95

# right arm: almost straight (about 17 deg elbow flexion), aimed at the drawer
_D = (TARGET - SHOULDER[1]).normalized()
WRIST = {1: SHOULDER[1] + _D * 0.527 + Vector((0.0, 0.0, 0.012)),
         -1: hipf((-0.246, 0.026, 0.818))}
ELBOW_POLE = {1: SHOULDER[1] + Vector((0.45, -0.35, -0.25)), -1: SHOULDER[-1] + Vector((-0.3, -0.45, -0.3))}
ELBOW = {s: E.ik2(SHOULDER[s], WRIST[s], UPPER_ARM, FOREARM, ELBOW_POLE[s]) for s in (1, -1)}

PIVOT = SP.point(1.405, (0.0, 0.004, 0))       # neck pivot (echo_head origin)
NECK_D = L.neck_dir(YAW_CHEST + 3.0, 21.0, side_tilt=-3.0)
HEAD_YAW, HEAD_PITCH, HEAD_ROLL = 37.0, -25.0, -4.0


# ------------------------------------------------------------------ body
def coat():
    # (z, rx_right, rx_left, ry_front, ry_back, power, dx, dy): outer surface of the lab coat, hem -> neck
    rings = [
        (0.425, 0.214, 0.212, 0.150, 0.158, 2.25, 0.012, 0.022),
        (0.500, 0.207, 0.206, 0.146, 0.153, 2.2, 0.010, 0.018),
        (0.620, 0.199, 0.200, 0.138, 0.146, 2.15, 0.006, 0.012),
        (0.740, 0.192, 0.195, 0.128, 0.140, 2.1, 0.002, 0.006),
        (0.840, 0.186, 0.191, 0.121, 0.134, 2.1, 0.0, 0.002),
        (0.920, 0.172, 0.177, 0.110, 0.118, 2.05, 0.0, 0.0),
        (0.990, 0.152, 0.155, 0.099, 0.098, 2.0, 0.0, 0.0),
        (1.060, 0.152, 0.154, 0.105, 0.092, 2.0, 0.0, 0.0),
        (1.130, 0.160, 0.162, 0.118, 0.090, 2.0, 0.0, 0.0),
        (1.200, 0.168, 0.168, 0.124, 0.092, 2.0, 0.0, 0.0),
        (1.255, 0.173, 0.172, 0.113, 0.096, 2.0, 0.0, 0.0),
        (1.300, 0.176, 0.175, 0.099, 0.094, 2.0, 0.0, 0.0),
        (1.340, 0.174, 0.173, 0.088, 0.088, 2.05, 0.0, 0.0),
        (1.370, 0.158, 0.157, 0.078, 0.080, 2.0, 0.0, 0.0),
        (1.396, 0.118, 0.118, 0.066, 0.070, 2.0, 0.0, 0.0),
        (1.418, 0.063, 0.063, 0.051, 0.054, 2.0, 0.0, 0.0),
    ]
    return L.coat_loft("coat", SP, rings, seg=44, sub=4, cap0=0.10, cap1=0.3)


def chest(x, y, z):
    return SP.point(z, (x, y, 0))


def coat_details(tree):
    c = SP.point(1.392, (0, 0.0, 0))
    col = E.collar_band("collar", (0, 0, 0), 0.060, list(range(50, 315, 15)), height=0.020, width=0.036,
                        back_lift=0.012)
    E.transform_obj(col, Matrix.Translation(c) @ E.rot_z(YAW_CHEST).to_4x4() @ E.rot_x(-12).to_4x4())
    parts = [col]
    for sx in (1, -1):
        parts.append(E.surface_slab(
            f"lapel{sx}", tree,
            [chest(sx * 0.050, 0.12, 1.398), chest(sx * 0.068, 0.14, 1.345), chest(sx * 0.064, 0.15, 1.285),
             chest(sx * 0.040, 0.15, 1.215), chest(sx * 0.008 - 0.012, 0.14, 1.150)],
            [0.044, 0.060, 0.054, 0.032, 0.004], thick=0.0042, side_sign=sx))
        # hip patch pockets
        parts.append(E.surface_slab(f"hippocket{sx}", tree,
                                    [hipf((sx * 0.112, 0.16, 0.815)), hipf((sx * 0.116, 0.17, 0.700))],
                                    [0.125, 0.135], thick=0.0042))
    parts.append(E.surface_slab("breastpocket", tree, [chest(-0.088, 0.15, 1.235), chest(-0.088, 0.15, 1.165)],
                                [0.092, 0.098], thick=0.004))
    # back half-belt with its two buttons
    parts.append(E.surface_slab("halfbelt", tree, [chest(0.105, -0.12, 0.99), chest(0.0, -0.12, 0.985),
                                                   chest(-0.105, -0.12, 0.99)], [0.034, 0.034, 0.034], thick=0.004))
    for i, sx in enumerate((1, -1)):
        p = E.hug(tree, [chest(sx * 0.088, -0.12, 0.988)], 0.007)[0]
        parts.append(E.ellipsoid(f"beltbtn{i}", p, (0.007, 0.007, 0.007), seg=10, rings=6))
    # front buttons (women's coat: right front over left), down to the hip
    for i, z in enumerate((1.140, 1.030, 0.920, 0.810)):
        p = E.hug(tree, [chest(-0.004, 0.15, z)], 0.0035)[0]
        parts.append(E.ellipsoid(f"button{i}", p, (0.0085, 0.0085, 0.0085), seg=10, rings=6))
    return parts


def arms():
    parts = []
    for s in (1, -1):
        sl, _cuff = L.sleeve(f"arm{s}", SHOULDER[s], ELBOW[s], WRIST[s], r_sh=0.050, r_up=0.047, r_el=0.044,
                             r_fore=0.041, r_cuff=0.044, cuff_len=0.026, wrist_r=(0.0235, 0.0175),
                             deltoid=(0.044, 0.049, 0.045), cuff_gap=0.026, start_back=0.006,
                             deltoid_off=SP.right(1.33) * (0.006 * s) + Vector((0, 0, -0.010)))
        parts += [p for p in sl if not p.name.endswith("_wrist")]
        for p in sl:
            if p.name.endswith("_wrist"):
                bpy.data.objects.remove(p, do_unlink=True)
    return parts


def wrist_stub(s):
    sh, el, wr = SHOULDER[s], ELBOW[s], WRIST[s]
    fdir = (wr - el).normalized()
    return E.limb(f"wrist{s}", wr - fdir * 0.06, wr + fdir * 0.004, [(0.0235, 0.0175), (0.0228, 0.017)],
                  seg=14, side=(0, 0, 1))


def legs():
    parts = []
    for s in (1, -1):
        parts += L.lower_leg(f"leg{s}", KNEE[s], ANKLE[s], calf=0.058, shin=0.043, knee_r=0.047, ankle_r=0.025)
        parts += L.shoe(f"shoe{s}", ANKLE[s], FOOT_YAW[s], heel=0.026, scale=0.93, toe=0.95)
    return parts


# ------------------------------------------------------------------ hands
def hand_right():
    """Pointing hand: index extended along the line to the drawer, the other fingers curled, thumb over the
    middle finger."""
    wr = WRIST[1]
    F = (TARGET - wr).normalized()
    F = (F + Vector((0, 0, 0.06))).normalized()            # slight wrist extension
    N, T = L.arm_hand_frame(F, 52.0, right=True)

    def thumb(info):
        # thumb lies across the outside of the curled middle finger's middle phalanx
        j = info["joints"][1]
        mid = j[1].lerp(j[2], 0.45)
        Fh, Nh, Sh = info["F"], info["N"], info["S"]
        tip = mid + Nh * 0.0135 * HAND_S + Sh * 0.003 * HAND_S
        tb = L.thumb_base(info, HAND_S)
        p1 = tb + (Fh * 0.62 + Sh * 0.42 + Nh * 0.66).normalized() * 0.034 * HAND_S
        p2 = p1.lerp(tip, 0.5) + Nh * 0.004 * HAND_S + Sh * 0.004 * HAND_S
        return [tb, p1, p2, tip]

    objs, info = L.hand2("handR", wr, F, N, T,
                         curls=[(2, 6, 4), (92, 108, 80), (94, 108, 78), (96, 104, 72)],
                         spread=[3, -1, -3, -6], thumb=thumb, scale=HAND_S, width=0.075, finger_r=0.0086)
    return [wrist_stub(1)] + objs, info


def hand_left():
    """Relaxed hand hanging beside the hip: palm toward the thigh, fingers loosely curled."""
    F = (WRIST[-1] - ELBOW[-1]).normalized()
    F = (F + Vector((0.0, 0.10, -0.05))).normalized()
    N, T = L.arm_hand_frame(F, 8.0, right=False)
    objs, info = L.hand2("handL", WRIST[-1], F, N, T,
                         curls=[(14, 22, 12), (20, 28, 14), (24, 32, 16), (28, 36, 18)],
                         spread=[3, 0, -2, -5], scale=HAND_S, width=0.076, finger_r=0.0082)
    return [wrist_stub(-1)] + objs, info


# ------------------------------------------------------------------ folds
def folds():
    k = []
    for s in (1, -1):
        el, sh, wr = ELBOW[s], SHOULDER[s], WRIST[s]
        inner = (sh - el).normalized() + (wr - el).normalized()
        if inner.length > 0.2:
            k += [dict(c=el + inner.normalized() * 0.034, s=0.014, a=-0.004),
                  dict(c=el + inner.normalized() * 0.026 + (wr - el).normalized() * 0.03, s=0.011, a=0.0025)]
        # sleeve gathers above the cuff
        fd = (wr - el).normalized()
        cuff = wr - fd * 0.026
        rot = L.frame_matrix(fd, L.ortho((0, 0, 1), fd), fd.cross(L.ortho((0, 0, 1), fd)))
        for i, d in enumerate((0.045, 0.075, 0.105)):
            k.append(dict(c=cuff - fd * d, s=(0.007, 0.07, 0.07), rot=rot, a=(0.0016, -0.0013, 0.001)[i]))
    # right (pointing) arm: twist folds from the armpit along the upper sleeve, drag fold across the chest
    sh, el = SHOULDER[1], ELBOW[1]
    for t, a in ((0.25, -0.0035), (0.42, 0.002), (0.58, -0.003)):
        k.append(dict(c=sh + (el - sh) * t + Vector((0, 0, -0.03)), s=(0.018, 0.018, 0.018), a=a))
    k += L.groove([chest(0.12, 0.13, 1.27), chest(0.04, 0.15, 1.16), chest(-0.03, 0.15, 1.07)], 0.012, -0.0028,
                  face=SP.front(1.15))
    # coat front edge: right front over left, opening widens below the last button
    k += L.groove([chest(-0.020, 0.15, 1.15), chest(-0.022, 0.15, 0.80)], 0.005, -0.0026, face=SP.front(1.0))
    k += L.groove([hipf((-0.022, 0.2, 0.78)), hipf((-0.020, 0.22, 0.60)), hipf((-0.014, 0.26, 0.43))],
                  0.009, -0.0075, face=hipf((0, 1, 0)))
    # waist: side compression creases and the back belt line
    for sx in (1, -1):
        for dz in (-0.03, 0.0, 0.035):
            k.append(dict(c=chest(sx * 0.15, 0.0, 1.0 + dz), s=(0.012, 0.05, 0.006), a=-0.0016,
                          face=(sx * SP.right(1.0))))
    # drape: folds falling from the high (left) hip toward the hem, and over the relaxed right knee
    k += L.groove([hipf((-0.15, 0.10, 0.84)), hipf((-0.165, 0.12, 0.62)), hipf((-0.17, 0.13, 0.44))], 0.012, -0.004)
    k += L.groove([hipf((-0.06, 0.13, 0.80)), hipf((-0.075, 0.15, 0.60)), hipf((-0.08, 0.16, 0.44))], 0.010, -0.003)
    k += L.groove([hipf((0.12, 0.12, 0.70)), hipf((0.105, 0.17, 0.48))], 0.014, 0.0035)          # knee push
    k += L.groove([hipf((0.17, 0.0, 0.80)), hipf((0.19, -0.02, 0.45))], 0.011, -0.003)
    # back: centre vent, shoulder-blade drag folds toward the belt
    k += L.groove([hipf((0.0, -0.16, 0.62)), hipf((0.0, -0.16, 0.43))], 0.004, -0.004, face=hipf((0, -1, 0)))
    k += L.groove([chest(0.10, -0.1, 1.27), chest(0.05, -0.1, 1.06)], 0.012, -0.0025, face=SP.front(1.1) * -1)
    k += L.groove([chest(-0.11, -0.1, 1.25), chest(-0.06, -0.1, 1.06)], 0.012, -0.0022, face=SP.front(1.1) * -1)
    return k


def _near(c, r):
    c = np.array(vec(c))

    def m(co):
        return np.exp(-((co - c) ** 2).sum(1) / (2 * r * r))
    return m


def hem_flutes(body):
    """Soft vertical flutes in the coat skirt, strongest at the hem (cloth, not a cone)."""
    def amp(co, t):
        z = co[:, 2]
        return 0.0075 * E.smoothstep(0.70, 0.44, z) * (0.65 + 0.35 * np.sin(co[:, 0] * 23.0 + co[:, 1] * 17.0))
    L.flutes(body, hipf((0.008, 0.012, 0.0)), (0, 0, 1), 9, amp, phase=0.7,
             region=lambda co: E.smoothstep(0.69, 0.60, co[:, 2]) * (co[:, 2] > 0.40))


def build_body():
    c = coat()
    tree = E.bvh(c)
    parts = [c] + coat_details(tree) + arms() + legs()
    body = L.finish_body(parts, voxel=0.0032, tris=BODY_TRIS, hand_centres=[WRIST[1], WRIST[-1]],
                         hand_sigma=0.04, folds_fn=folds, post_fn=hem_flutes)
    print("[leyla] body shell", E.mesh_report(body))
    hr, info_r = hand_right()
    hl, _info_l = hand_left()
    hands = [L.hand_shell(hr, "handR_shell", HAND_TRIS), L.hand_shell(hl, "handL_shell", HAND_TRIS)]
    for h in hands:
        print("[leyla] hand shell", h.name, E.mesh_report(h))
    body = L.bool_union(body, hands, "echo_body")
    return body, info_r


# ------------------------------------------------------------------ head (same face and hair as the sitting echo)
def hair_disp(co, nrm):
    """Swept-back 1970s hair: volume over the skull, soft hairline, strands converging on the bun
    (copied from echo_leyla_sitting.py so both echoes share the same hair)."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    h = np.interp(deg, [0, 30, 55, 72, 88, 105, 140, 180],
                  [0.064, 0.057, 0.038, 0.016, 0.016, -0.004, -0.050, -0.072])
    m = E.smoothstep(h - 0.002, h + 0.007, z)
    thick = np.interp(deg, [0, 40, 80, 120, 180], [0.0065, 0.010, 0.0155, 0.014, 0.012])
    thick = thick + 0.004 * E.smoothstep(0.05, 0.11, z) * np.interp(deg, [0, 60, 180], [0.6, 1.0, 0.5])
    psi = np.arctan2(z - 0.005, x)
    g = 1.0 - 0.22 * (0.5 - 0.5 * np.cos(22 * psi)) * E.smoothstep(-0.03, 0.02, y)
    return nrm * (thick * m * g)[:, None]


def bun(_p):
    bun_c = vec((0, -0.121, 0.006))
    return [E.ellipsoid("h_bun", bun_c, (0.038, 0.030, 0.033), seg=24, rings=14),
            E.torus_obj("h_bun_coil", bun_c + Vector((0, -0.006, 0)), 0.025, 0.0135, rot=E.rot_x(90), seg=28, mseg=12)]


def build_head():
    return L.build_head(E.FEMALE, PIVOT, NECK_D, HEAD_YAW, HEAD_PITCH, HEAD_ROLL, hair_disp, HEAD_TRIS,
                        extras_fn=bun)


# ------------------------------------------------------------------ QA
def pointing_report(info):
    tip = info["tips"][0]
    knuck = info["joints"][0][0]
    d = (tip - knuck).normalized()
    to_t = TARGET - tip
    miss = (to_t - d * to_t.dot(d)).length
    print(f"[leyla] index tip {tuple(round(v, 3) for v in L.build_to_godot(tip))} (Godot model-local), "
          f"distance to target {to_t.length:.3f} m, pointing line misses the target by {miss * 100:.1f} cm")


def booth_context():
    """Proxy booth: floor, west wall, slide cabinet with drawer 2 highlighted, projectors (Godot coords)."""
    L.proxy("floor", (4.0, 0.02, 1.5), (-3.05, -0.01, 2.8), color="2B2A27")
    L.proxy("wall_w", (0.1, 2.8, 1.5), (-5.05, 1.4, 2.8), color="3A4A40")
    L.proxy("wall_s", (4.0, 2.8, 0.1), (-3.05, 1.4, 3.55), color="3A4A40")
    L.proxy("wall_n", (4.0, 1.6, 0.1), (-3.05, 0.8, 2.05), color="3A4A40")
    L.proxy("cab_plinth", (0.45, 0.30, 0.60), (-4.775, 0.15, 2.8), color="2A1C12")
    L.proxy("cab_top", (0.45, 0.10, 0.60), (-4.775, 1.0, 2.8), color="3A2616")
    for i in range(5):
        y = 0.95 - 0.11 * (i + 0.5)
        L.proxy(f"cab_d{i}", (0.45, 0.104, 0.58), (-4.775, y, 2.8), color="6A4A2A" if i != 2 else "B08A50",
                emit="CFF6FF" if i == 2 else None)
    L.proxy("filmproj_base", (0.45, 0.06, 0.45), (-2.9, 0.03, 2.65), color="25282B")
    L.proxy("filmproj_column", (0.14, 1.5, 0.14), (-2.9, 0.78, 2.65), color="25282B")
    L.proxy("filmproj", (0.55, 0.42, 0.32), (-2.9, 1.82, 2.65), color="30343A")
    L.proxy("slideproj_column", (0.06, 1.7, 0.06), (-2.35, 0.85, 2.45), color="30343A")
    L.proxy("slideproj", (0.28, 0.16, 0.24), (-2.35, 1.82, 2.45), color="30343A")
    L.proxy("splicer", (1.2, 0.9, 0.5), (-3.9, 0.45, 3.25), color="3A2616")


def renders(body, head, info_r):
    objs = [body, head]
    fr = L.g2b                                       # model-local Godot -> Blender (export orientation)
    tip = Vector(L.build_to_godot(info_r["tips"][0]))
    wr_r = Vector(L.build_to_godot(WRIST[1]))
    wr_l = Vector(L.build_to_godot(WRIST[-1]))
    hc_r = (tip + wr_r) * 0.5
    hc_l = wr_l + Vector((0.0, -0.09, 0.0))
    # clay: three-quarter (her left front, the pointing side), front, side
    L.clay(NAME, fr(1.45, 1.35, 2.1), fr(0.02, 0.86, 0.1), lens=50, res=(520, 640))
    L.clay(NAME + "_2", fr(-0.2, 1.2, 3.0), fr(0.0, 0.86, 0.05), lens=50, res=(520, 640))
    L.clay(NAME + "_3", fr(2.9, 1.15, 0.45), fr(0.0, 0.85, 0.12), lens=50, res=(520, 640))
    # in-game look: front, three-quarter back (the booth side), side
    L.ghost(NAME + "_4", objs, fr(1.2, 1.3, 2.6), fr(0.02, 0.86, 0.1), lens=50, res=(520, 640))
    L.ghost(NAME + "_5", objs, fr(-1.7, 1.45, -2.2), fr(0.0, 0.88, 0.05), lens=50, res=(520, 640))
    L.ghost(NAME + "_6", objs, fr(2.9, 1.15, 0.45), fr(0.0, 0.85, 0.12), lens=50, res=(520, 640))
    # hands (finger count, separation) and the pointing line
    L.clay(NAME + "_7", tuple(Vector(fr(*hc_r)) + Vector(fr(0.42, 0.10, 0.10))), fr(*hc_r), lens=60, res=(640, 640))
    L.clay(NAME + "_8", tuple(Vector(fr(*hc_l)) + Vector(fr(0.40, 0.05, 0.22))), fr(*hc_l), lens=60, res=(640, 640))
    L.clay(NAME + "_11", tuple(Vector(fr(*hc_r)) + Vector(fr(-0.05, 0.12, 0.45))), fr(*hc_r), lens=60, res=(640, 640))
    # in context: the game's booth view, and a side view that shows the gesture (suggested walk camera)
    L.context_render(NAME + "_9", objs, body, PLACE, YAW, booth_context, (-1.55, 1.6, 2.6), (-4.6, 1.1, 2.9),
                     lens_fov_deg=62)
    L.context_render(NAME + "_10", objs, body, PLACE, YAW, booth_context, (-3.05, 1.55, 3.3), (-4.35, 0.95, 2.62),
                     lens_fov_deg=56)


def dev_hands():
    """--hands: build only the two hand shells (build space) and render close-ups (fast iteration)."""
    hr, info_r = hand_right()
    hl, info_l = hand_left()
    hands = [L.hand_shell(hr, "handR_shell", HAND_TRIS), L.hand_shell(hl, "handL_shell", HAND_TRIS)]
    for h in hands:
        E.finish_echo(h)
        print("[leyla] hand", h.name, E.mesh_report(h))
    c = (info_r["tips"][0] + WRIST[1]) * 0.5
    F, N, S = info_r["F"], info_r["N"], info_r["S"]
    L.clay("dev_handR_a", tuple(c + S * 0.35 + N * 0.12), tuple(c), lens=70, res=(560, 560))
    L.clay("dev_handR_b", tuple(c + N * 0.35 + S * 0.08), tuple(c), lens=70, res=(560, 560))
    L.clay("dev_handR_c", tuple(c - S * 0.35 + N * 0.05), tuple(c), lens=70, res=(560, 560))
    c2 = (info_l["tips"][1] + WRIST[-1]) * 0.5
    F, N, S = info_l["F"], info_l["N"], info_l["S"]
    L.clay("dev_handL_a", tuple(c2 - N * 0.35 + S * 0.05), tuple(c2), lens=70, res=(560, 560))
    L.clay("dev_handL_b", tuple(c2 + S * 0.35 + N * 0.05), tuple(c2), lens=70, res=(560, 560))
    L.clay("dev_handL_c", tuple(c2 + N * 0.35 + S * 0.05), tuple(c2), lens=70, res=(560, 560))


def main():
    mrlib.reset_scene()
    if "--hands" in ARGS:
        L.QA_DIR = DEV or L.QA_DIR
        dev_hands()
        return
    body, info_r = build_body()
    head = build_head()
    pivots = L.finalize(body, [(head, "echo_head", PIVOT)])
    for o in (body, head):
        print("[echo]", o.name, E.mesh_report(o))
    print("[echo] total tris", mrlib.tri_count(), "/", BUDGET)
    print("[echo] head pivot (Godot model-local)", tuple(round(v, 4) for v in pivots["echo_head"]))
    pointing_report(info_r)
    path = mrlib.export_glb(NAME)
    L.verify_glb(path, ["echo_body", "echo_head"], pivots, BUDGET)
    if not RENDER:
        return
    if DEV:
        L.QA_DIR = DEV
    renders(body, head, info_r)


if __name__ == "__main__":
    main()
