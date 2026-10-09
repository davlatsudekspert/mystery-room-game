"""Light echo: the old archivist of Records Archive B, 1979, stooped over an open card-catalogue drawer, his
fingers walking the index cards (Chapter 2, optional "kept echoes").

Output: game/assets/models/echo_archivist.glb (Godot axes below; the model faces +Z)
  echo_body  origin = floor between his feet. ~1.74 m upright, stooped to ~1.66. Grey knee-length work (dust)
             coat with notch lapels, breast pocket with two pencils, patch pockets; sleeve protectors (gathered
             oversleeves) from below the elbow to the wrist; trousers and leather shoes. Both hands are in the
             drawer: the right hand's index and middle fingers walk the guide/card tops, the left hand holds the
             front of the pack.
  echo_head  head + neck + receding grey hair + small moustache + horn-rimmed spectacles, child of echo_body,
             origin = neck pivot (base of the neck inside the collar), identity rotation. Rotate about local +Y.
Placement (docs/models/ch2.md section 1): world (-4.05, 0, -1.05), yaw -90: model +Z = world -X, model +X =
world +Z. card_catalogue (-5.0, 0, -1.2) yaw 90 has its column-0 drawers at world z = -1.0575 (model x = -0.0075),
so he stands straight in front of drawer 04 (row 2, opening y 0.94 .. 1.097, the 1.0 m drawer). His fingertips
are at y ~1.05 between 0.28 and 0.37 m ahead: inside the drawer when it is open (front 0.166 m ahead, cards
0.21 .. 0.53 m ahead); with the drawer closed (front 0.47 m ahead) the hands hover in front of it. Forearms clear
the open drawer front (top edge y 1.097 at 0.166 .. 0.188 m ahead).
Material: one slot, M_Echo. One closed shell per object (the spectacles are separate thin shells in echo_head).

Run: blender -b --factory-startup -P tools/blender/models/echo_archivist.py [-- --no-render] [-- --dev <dir>]
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

NAME = "echo_archivist"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
DEV = ARGS[ARGS.index("--dev") + 1] if "--dev" in ARGS else None
BUDGET = 14000
BODY_TRIS, HAND_TRIS, HEAD_TRIS = 7700, 1050, 2850

PLACE, YAW = (-4.05, 0.0, -1.05), -90.0
CAT_POS, CAT_YAW = (-5.0, 0.0, -1.2), 90.0

# ------------------------------------------------------------------ skeleton (build space: +Y forward, +X his right)
YAW_HIP, YAW_CHEST = -4.0, 0.0
SP = L.Spine(hip_xy=(0.0, -0.018), neck_xy=(0.004, 0.105), z_hip=0.93, z_neck=1.475,
             yaw_hip=YAW_HIP, yaw_chest=YAW_CHEST, z_twist0=0.95, z_twist1=1.3)


def hipf(p) -> Vector:
    return L.rz(YAW_HIP, p)


def chest(x, y, z):
    return SP.point(z, (x, y, 0))


HIP = {1: hipf((0.090, -0.01, 0.905)), -1: hipf((-0.090, -0.01, 0.905))}
KNEE = {1: hipf((0.104, 0.030, 0.495)), -1: hipf((-0.104, 0.022, 0.495))}
ANKLE = {1: hipf((0.118, -0.010, 0.086)), -1: hipf((-0.118, -0.018, 0.086))}
FOOT_YAW = {1: YAW_HIP - 9.0, -1: YAW_HIP + 8.0}
SHOULDER = {1: chest(0.163, 0.010, 1.396), -1: chest(-0.163, 0.010, 1.396)}
UPPER_ARM, FOREARM = 0.315, 0.262
HAND_S = 1.04
WRIST = {1: vec((0.052, 0.250, 1.160)), -1: vec((-0.074, 0.134, 1.163))}
ELBOW_POLE = {1: vec((0.75, -0.30, 1.05)), -1: vec((-0.75, -0.30, 1.05))}
ELBOW = {s: E.ik2(SHOULDER[s], WRIST[s], UPPER_ARM, FOREARM, ELBOW_POLE[s]) for s in (1, -1)}

PIVOT = chest(0.0, 0.006, 1.468)
NECK_D = L.neck_dir(YAW_CHEST, 34.0)
HEAD_YAW, HEAD_PITCH, HEAD_ROLL = 4.0, -30.0, 2.0
P_HEAD = dict(E.MALE, nose=1.16, brow=1.7, jaw=1.08, cheek=0.9)


# ------------------------------------------------------------------ body
def coat():
    rings = [  # (z, rx_right, rx_left, ry_front, ry_back, power, dx, dy) - grey work coat, hem -> neck
        (0.470, 0.214, 0.214, 0.158, 0.152, 2.2, 0.0, 0.012),
        (0.560, 0.208, 0.208, 0.152, 0.147, 2.2, 0.0, 0.010),
        (0.680, 0.200, 0.200, 0.144, 0.141, 2.1, 0.0, 0.005),
        (0.800, 0.193, 0.193, 0.137, 0.135, 2.1, 0.0, 0.0),
        (0.900, 0.187, 0.187, 0.134, 0.131, 2.05, 0.0, 0.0),
        (1.000, 0.181, 0.181, 0.140, 0.121, 2.0, 0.0, 0.0),
        (1.080, 0.181, 0.181, 0.142, 0.117, 2.0, 0.0, 0.0),
        (1.160, 0.183, 0.183, 0.134, 0.115, 2.0, 0.0, 0.0),
        (1.240, 0.187, 0.187, 0.124, 0.119, 2.0, 0.0, 0.0),
        (1.315, 0.190, 0.190, 0.112, 0.126, 2.0, 0.0, 0.0),
        (1.365, 0.184, 0.184, 0.100, 0.124, 2.0, 0.0, 0.0),
        (1.405, 0.166, 0.166, 0.088, 0.112, 2.05, 0.0, 0.0),
        (1.442, 0.126, 0.126, 0.074, 0.090, 2.0, 0.0, 0.0),
        (1.474, 0.071, 0.071, 0.058, 0.062, 2.0, 0.0, 0.0),
    ]
    return L.coat_loft("coat", SP, rings, seg=44, sub=4, cap0=0.10, cap1=0.3)


def coat_details(tree):
    c = chest(0.0, 0.0, 1.452)
    col = E.collar_band("collar", (0, 0, 0), 0.068, list(range(45, 320, 15)), height=0.022, width=0.040,
                        back_lift=0.014)
    E.transform_obj(col, Matrix.Translation(c) @ E.rot_z(YAW_CHEST).to_4x4() @ E.rot_x(-16).to_4x4())
    parts = [col]
    for sx in (1, -1):
        parts.append(E.surface_slab(
            f"lapel{sx}", tree,
            [chest(sx * 0.056, 0.12, 1.455), chest(sx * 0.074, 0.14, 1.400), chest(sx * 0.068, 0.15, 1.335),
             chest(sx * 0.040, 0.15, 1.265), chest(sx * 0.008 + 0.010, 0.15, 1.205)],
            [0.046, 0.062, 0.054, 0.032, 0.005], thick=0.0045, side_sign=sx))
        parts.append(E.surface_slab(f"pocket{sx}", tree, [hipf((sx * 0.118, 0.16, 0.905)), hipf((sx * 0.122, 0.17, 0.775))],
                                    [0.140, 0.150], thick=0.0045))
    parts.append(E.surface_slab("breastpocket", tree, [chest(-0.098, 0.15, 1.300), chest(-0.098, 0.15, 1.225)],
                                [0.100, 0.104], thick=0.0042))
    # two pencils in the breast pocket
    for i, (dx, lean) in enumerate(((-0.020, -0.010), (0.016, 0.012))):
        base = E.hug(tree, [chest(-0.098 + dx, 0.15, 1.262)], 0.006)[0]
        top = base + Vector((lean, 0.006, 0.098)) + SP.front(1.3) * 0.004
        parts.append(E.limb(f"pencil{i}", base, top, [0.0052, 0.0052, 0.0048, 0.003], ts=[0, 0.7, 0.88, 1.0],
                            seg=10, side=(1, 0, 0), cap0=0.3, cap1=0.6))
    # front buttons (men's coat: left front over right), down to just above the pockets
    for i, z in enumerate((1.200, 1.105, 1.010, 0.915)):
        p = E.hug(tree, [chest(0.004, 0.16, z)], 0.0038)[0]
        parts.append(E.ellipsoid(f"button{i}", p, (0.0095, 0.0095, 0.0095), seg=10, rings=6))
    return parts


def arms():
    """Coat sleeves to the elbow, then cloth sleeve protectors (gathered at both ends) down to the wrist."""
    parts = []
    for s in (1, -1):
        sh, el, wr = SHOULDER[s], ELBOW[s], WRIST[s]
        sl, _cuff = L.sleeve(f"arm{s}", sh, el, wr, r_sh=0.056, r_up=0.053, r_el=0.050, r_fore=0.047,
                             r_cuff=0.044, cuff_len=0.02, wrist_r=(0.027, 0.020), deltoid=(0.046, 0.051, 0.046),
                             cuff_gap=0.05, start_back=0.008,
                             deltoid_off=SP.right(1.4) * (0.006 * s) + Vector((0, 0, -0.010)))
        for p in sl:
            if p.name.endswith("_wrist"):
                bpy.data.objects.remove(p, do_unlink=True)
            else:
                parts.append(p)
        fd = (wr - el).normalized()
        up = L.ortho((0, 0, 1), fd)
        a = el + fd * 0.045
        b = wr - fd * 0.020
        n = 9
        pts = [a.lerp(b, i / (n - 1)) for i in range(n)]
        # puffed between the elastics, sagging a little under gravity
        prof = [0.049, 0.056, 0.061, 0.063, 0.062, 0.060, 0.056, 0.047, 0.037]
        sag = [0.0, 0.002, 0.005, 0.007, 0.008, 0.007, 0.005, 0.002, 0.0]
        pts = [p - up * sg for p, sg in zip(pts, sag)]
        parts.append(E.loft(f"protector{s}", pts, prof, side=tuple(up), seg=24, sub=3, cap0=0.4, cap1=0.3))
        # elastic hems
        for t, r in ((0.0, 0.050), (1.0, 0.038)):
            c = a.lerp(b, t)
            rot = L.frame_matrix(up, up.cross(fd), fd)
            parts.append(E.torus_obj(f"elastic{s}_{int(t)}", c, r - 0.003, 0.0045, rot=rot, seg=24, mseg=8))
    return parts


def wrist_stub(s):
    el, wr = ELBOW[s], WRIST[s]
    fdir = (wr - el).normalized()
    return E.limb(f"wrist{s}", wr - fdir * 0.05, wr + fdir * 0.004, [(0.027, 0.020), (0.026, 0.0195)],
                  seg=14, side=(0, 0, 1))


def legs():
    parts = []
    for s in (1, -1):
        top = hipf((s * 0.098, 0.0, 0.62))
        parts += L.trouser_leg(f"trouser{s}", top, ANKLE[s], r_top=0.068, r_knee=0.062, r_hem=0.060)
        parts += L.shoe(f"shoe{s}", ANKLE[s], FOOT_YAW[s], heel=0.012, scale=1.08, toe=1.0)
    return parts


# ------------------------------------------------------------------ hands
def hand_right():
    """Walking the cards: palm down, index and middle fingertips on the card tops, ring/little resting."""
    F = vec((-0.12, 0.64, -0.76)).normalized()
    N, T = L.arm_hand_frame(F, 80.0, right=True)
    objs, info = L.hand2("handR", WRIST[1], F, N, T,
                         curls=[(22, 34, 16), (16, 28, 14), (40, 52, 28), (48, 58, 30)],
                         spread=[5, 0, -4, -9], scale=HAND_S, width=0.082, finger_r=0.0088)
    return [wrist_stub(1)] + objs, info


DRAWER_FRONT = (0.166, 0.188, 1.097)          # open drawer 04 front: near face, far face (build y), top edge z


def hand_left():
    """Steadying the open drawer: palm on the top edge of the drawer front, fingers hooked over it into the
    drawer, thumb on the outer face."""
    F = vec((0.06, 0.95, -0.31)).normalized()
    N, T = L.arm_hand_frame(F, 86.0, right=False)

    def thumb(info):
        tip = Vector((WRIST[-1].x + 0.022, DRAWER_FRONT[0] - 0.012, DRAWER_FRONT[2] - 0.040))
        return L.thumb_to(info, tip, HAND_S, bulge=0.004)

    objs, info = L.hand2("handL", WRIST[-1], F, N, T,
                         curls=[(42, 66, 34), (44, 68, 36), (46, 68, 36), (48, 66, 34)],
                         spread=[3, 0, -3, -6], thumb=thumb, scale=HAND_S, width=0.082, finger_r=0.0088)
    return [wrist_stub(-1)] + objs, info


# ------------------------------------------------------------------ folds
def folds():
    k = []
    for s in (1, -1):
        el, sh, wr = ELBOW[s], SHOULDER[s], WRIST[s]
        inner = (sh - el).normalized() + (wr - el).normalized()
        k += [dict(c=el + inner.normalized() * 0.040, s=0.016, a=-0.006),
              dict(c=el + inner.normalized() * 0.03 + (sh - el).normalized() * 0.04, s=0.012, a=0.003)]
        # elastic gathers: radial pleats around both ends of the protector
        fd = (wr - el).normalized()
        up = L.ortho((0, 0, 1), fd)
        side = fd.cross(up)
        for t0, rr in ((0.045 + 0.015, 0.052), (None, 0.042)):
            c = (el + fd * t0) if t0 is not None else (wr - fd * 0.040)
            for j in range(10):
                ang = 2 * math.pi * j / 10
                d = up * math.cos(ang) + side * math.sin(ang)
                k.append(dict(c=c + d * rr, s=(0.006, 0.006, 0.006), a=-0.0022))
        # shoulder drag folds toward the bent elbow
        k += L.groove([sh + (el - sh) * 0.2 + Vector((0, 0.02, -0.02)), sh + (el - sh) * 0.75], 0.010, -0.003)
    # coat front edge (left over right), opening below the last button
    k += L.groove([chest(0.022, 0.16, 1.21), chest(0.022, 0.16, 0.88)], 0.005, -0.0028, face=SP.front(1.0))
    k += L.groove([hipf((0.022, 0.2, 0.86)), hipf((0.018, 0.22, 0.65)), hipf((0.012, 0.25, 0.47))], 0.009, -0.007,
                  face=hipf((0, 1, 0)))
    # belly pull: horizontal drag folds from the buttons toward the sides
    for z in (1.06, 0.97):
        for sx in (1, -1):
            k += L.groove([chest(sx * 0.03, 0.16, z), chest(sx * 0.13, 0.12, z - 0.03)], 0.008, -0.0022,
                          face=SP.front(z))
    # stooped back: tension folds from the shoulder blades, vent at the back hem
    k += L.groove([chest(0.12, -0.12, 1.34), chest(0.02, -0.13, 1.12)], 0.013, -0.0028, face=-SP.front(1.2))
    k += L.groove([chest(-0.12, -0.12, 1.34), chest(-0.02, -0.13, 1.12)], 0.013, -0.0028, face=-SP.front(1.2))
    k += L.groove([hipf((0.0, -0.16, 0.70)), hipf((0.0, -0.16, 0.47))], 0.004, -0.004, face=hipf((0, -1, 0)))
    # skirt drape between the legs and at the sides
    for sx in (1, -1):
        k += L.groove([hipf((sx * 0.16, 0.06, 0.86)), hipf((sx * 0.175, 0.07, 0.48))], 0.012, -0.0035)
        k += L.groove([hipf((sx * 0.07, 0.13, 0.80)), hipf((sx * 0.085, 0.15, 0.48))], 0.011, -0.0025)
    return k


def hem_flutes(body):
    def amp(co, t):
        return 0.0065 * E.smoothstep(0.74, 0.48, co[:, 2]) * (0.65 + 0.35 * np.sin(co[:, 0] * 21.0 + co[:, 1] * 13.0))
    L.flutes(body, hipf((0.0, 0.01, 0.0)), (0, 0, 1), 8, amp, phase=1.3,
             region=lambda co: E.smoothstep(0.74, 0.64, co[:, 2]) * (co[:, 2] > 0.45))


def build_body():
    c = coat()
    tree = E.bvh(c)
    parts = [c] + coat_details(tree) + arms() + legs()
    body = L.finish_body(parts, voxel=0.0032, tris=BODY_TRIS, hand_centres=[WRIST[1], WRIST[-1]],
                         hand_sigma=0.04, folds_fn=folds, post_fn=hem_flutes)
    print("[archivist] body shell", E.mesh_report(body))
    hr, info_r = hand_right()
    hl, info_l = hand_left()
    hands = [L.hand_shell(hr, "handR_shell", HAND_TRIS), L.hand_shell(hl, "handL_shell", HAND_TRIS)]
    body = L.bool_union(body, hands, "echo_body")
    return body, info_r, info_l


# ------------------------------------------------------------------ head
def hair_disp(co, nrm):
    """Receding grey hair combed back: high M-shaped hairline, thin over the crown, fuller at the sides and
    nape, comb lines; small clipped moustache."""
    s = P_HEAD["scale"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    hl = np.interp(deg, [0, 22, 40, 55, 72, 84, 100, 140, 180],
                   [0.082, 0.084, 0.094, 0.086, 0.040, 0.012, -0.004, -0.050, -0.066]) * s
    m = E.smoothstep(hl - 0.002, hl + 0.008, z)
    thick = np.interp(deg, [0, 40, 80, 120, 180], [0.0030, 0.0032, 0.0075, 0.0085, 0.0085])
    crown = 1.0 - 0.45 * np.exp(-(((z - 0.10 * s) / 0.02) ** 2 + ((y + 0.01) / 0.035) ** 2))
    psi = np.arctan2(z - 0.01, x)
    comb = 1.0 - 0.25 * (0.5 - 0.5 * np.cos(28 * psi)) * E.smoothstep(-0.05, 0.03, y)
    d = thick * m * crown * comb
    mous = (E.smoothstep(-0.071 * s, -0.065 * s, z) * (1 - E.smoothstep(-0.057 * s, -0.052 * s, z))
            * E.smoothstep(0.070 * s, 0.084 * s, y) * (1 - E.smoothstep(0.020 * s, 0.030 * s, ax)))
    return nrm * (d + 0.0024 * mous)[:, None]


def head_kernels():
    s = P_HEAD["scale"]
    k = [dict(c=(sx * 0.03 * s, 0.083 * s, -0.036 * s), s=(0.010 * s, 0.010 * s, 0.024 * s), a=-0.0016 * s,
              face=(0, 1, 0)) for sx in (1, -1)]                                       # nasolabial folds
    k += [dict(c=(sx * 0.036 * s, 0.085 * s, -0.013 * s), s=(0.012 * s, 0.010 * s, 0.004 * s), a=-0.0012 * s,
               face=(0, 1, 0)) for sx in (1, -1)]                                      # under-eye bags
    k += [dict(c=(sx * 0.045 * s, 0.040 * s, -0.095 * s), s=(0.016 * s, 0.02 * s, 0.012 * s), a=0.0022 * s)
          for sx in (1, -1)]                                                           # jowls
    k += [dict(c=(0, 0.076 * s, 0.050 * s), s=(0.040 * s, 0.02 * s, 0.003 * s), a=-0.0008 * s, face=(0, 1, 0)),
          dict(c=(0, 0.078 * s, 0.062 * s), s=(0.034 * s, 0.02 * s, 0.003 * s), a=-0.0007 * s, face=(0, 1, 0))]
    k += [dict(c=(sx * 0.0782 * s, -0.010 * s, -0.010 * s), s=(0.006, 0.014, 0.022), a=0.0015 * s) for sx in (1, -1)]
    return k


def glasses(_m):
    return L.spectacles("glasses", s=P_HEAD["scale"], lens_r=(0.0215, 0.0170), rim=0.0028, y_front=0.099,
                        eye_z=0.002, ear_y=-0.008, ear_z=0.002)


def build_head():
    return L.build_head(P_HEAD, PIVOT, NECK_D, HEAD_YAW, HEAD_PITCH, HEAD_ROLL, hair_disp, HEAD_TRIS,
                        kernels=head_kernels(), neck_r=((0.060, 0.062), (0.056, 0.058), (0.056, 0.056)),
                        late_parts_fn=glasses)


# ------------------------------------------------------------------ QA
def hands_report(info_r, info_l):
    for nm, info in (("R", info_r), ("L", info_l)):
        tips = [tuple(round(v, 3) for v in L.build_to_godot(t)) for t in info["tips"]]
        print(f"[archivist] {nm} fingertips (Godot model-local): {tips}")


def catalogue_context():
    L.proxy("floor", (6.0, 0.02, 7.0), (-2.0, -0.01, -0.5), color="2E4236")
    L.proxy("wall_w", (0.1, 3.0, 7.0), (-5.05, 1.5, -0.5), color="5E7766")
    L.proxy("wall_n", (6.0, 3.0, 0.1), (-2.0, 1.5, -3.55), color="5E7766")
    if not L.import_ctx("card_catalogue", CAT_POS, CAT_YAW):
        L.proxy("catalogue", (0.48, 0.86, 0.64), (-4.76, 1.01, -1.2), color="5A3A22")
    else:
        # drawer 04 pulled out by the game's 0.30 m travel, with the tray in it
        dr = bpy.data.objects.get("QA_imp_IA_cat_drawer_4")
        if dr is not None:
            dr.location.y -= 0.30          # glTF +Z (out of the cabinet) = Blender -Y
            mrlib.refresh()
            mount = bpy.data.objects.get("QA_imp_cat_tray_mount_4")
            if mount is not None:
                objs = L.import_ctx("catalogue_tray", (0, 0, 0), 0)
                if objs:
                    holder = objs[0]
                    holder.matrix_world = mount.matrix_world.copy()


def renders(body, head, info_r, info_l):
    objs = [body, head]
    fr = L.g2b
    L.ONLY = set(ARGS[ARGS.index("--only") + 1].split(",")) if "--only" in ARGS else None
    hc = (Vector(L.build_to_godot(info_r["tips"][1])) + Vector(L.build_to_godot(info_l["tips"][1]))) * 0.5
    L.clay(NAME, fr(1.4, 1.45, 2.0), fr(0.0, 0.92, 0.12), lens=50, res=(520, 640))
    L.clay(NAME + "_2", fr(0.1, 1.3, 3.0), fr(0.0, 0.9, 0.08), lens=50, res=(520, 640))
    L.clay(NAME + "_3", fr(-2.9, 1.2, 0.5), fr(0.0, 0.88, 0.12), lens=50, res=(520, 640))
    L.ghost(NAME + "_4", objs, fr(1.4, 1.45, 2.0), fr(0.0, 0.92, 0.12), lens=50, res=(520, 640))
    L.ghost(NAME + "_5", objs, fr(-1.6, 1.5, -2.2), fr(0.0, 0.9, 0.05), lens=50, res=(520, 640))
    L.ghost(NAME + "_6", objs, fr(-2.9, 1.2, 0.5), fr(0.0, 0.88, 0.12), lens=50, res=(520, 640))
    L.clay(NAME + "_7", tuple(Vector(fr(*hc)) + Vector(fr(0.30, 0.42, 0.42))), fr(*hc), lens=55, res=(640, 640))
    hp = Vector(L.build_to_godot(PIVOT)) + Vector((0.0, 0.13, 0.10))
    L.clay(NAME + "_8", tuple(Vector(fr(*hp)) + Vector(fr(0.18, -0.30, 0.42))), fr(*hp), lens=60, res=(640, 640))
    # in context: the game's west view (root) and catalogue view, catalogue + drawer 04 open with its tray
    L.context_render(NAME + "_9", objs, body, PLACE, YAW, catalogue_context, (-1.8, 1.65, 1.0), (-3.0, 1.5, -3.0),
                     lens_fov_deg=62)
    L.context_render(NAME + "_10", objs, body, PLACE, YAW, catalogue_context, (-3.2, 1.55, -0.2), (-4.4, 1.0, -1.1),
                     lens_fov_deg=50)
    L.context_render(NAME + "_11", objs, body, PLACE, YAW, catalogue_context, (-4.1, 1.5, -0.15), (-4.35, 1.0, -1.1),
                     lens_fov_deg=40)


def main():
    mrlib.reset_scene()
    body, info_r, info_l = build_body()
    head = build_head()
    pivots = L.finalize(body, [(head, "echo_head", PIVOT)])
    for o in (body, head):
        print("[echo]", o.name, E.mesh_report(o))
    print("[echo] total tris", mrlib.tri_count(), "/", BUDGET)
    print("[echo] head pivot (Godot model-local)", tuple(round(v, 4) for v in pivots["echo_head"]))
    hands_report(info_r, info_l)
    path = mrlib.export_glb(NAME)
    L.verify_glb(path, ["echo_body", "echo_head"], pivots, BUDGET)
    if not RENDER:
        return
    if DEV:
        L.QA_DIR = DEV
    renders(body, head, info_r, info_l)


if __name__ == "__main__":
    main()
