"""Light echo: a 1979 maintenance welder kneeling at transformer_1's base seam (Chapter 3 kept echo `welder`).

A man in a hip-length leather welding jacket with a stand collar, work trousers and boots, gauntlet gloves,
his welding mask flipped down over his face. He kneels on his right knee (right foot on its toes), the left
foot planted forward, and leans in: the gas torch in his right fist, its nozzle on the seam; his left forearm
rests on his left thigh and the left hand feeds a filler rod toward the flame. Two hoses run from the torch's
back end to the floor behind him.

Output: game/assets/models/echo_welder.glb (Godot axes; the figure faces +Z, -X = his right)
  pose_weld   the figure, ONE closed mesh (M_Echo), origin on the floor between his knee and his front foot.
  torch_tip   empty, child of pose_weld, at (-0.10, 0.62, 0.48): the nozzle tip (the code's sparks).
Placement: transformer_1 `echo_mount` (-0.10, 0, 0.93) facing -Z -> world (-11.52, 0, -1.20), yaw -90; the tip
then meets the base seam at transformer-local (0, 0.62, 0.45).
Budget: <= 9,000 tris.

Run: blender -b --factory-startup -P tools/blender/models/echo_welder.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch3_echoes as H  # noqa: E402
from lib_ch3_echoes import E, L, mrlib, vec  # noqa: E402

NAME = "echo_welder"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
BUDGET = 9000
TRIS = dict(body=5000, hand=640, head=1700)
VOXEL = 0.0034
HAND_S = 1.06
UPPER, FORE = 0.315, 0.262
TIP_G = (-0.10, 0.62, 0.48)
TIP = H.g2b(TIP_G)                                # build (0.10, 0.48, 0.62)

# ------------------------------------------------------------------ skeleton (build space)
SP = L.Spine(hip_xy=(0.0, -0.030), neck_xy=(0.010, 0.185), z_hip=0.52, z_neck=1.045, yaw_hip=-4.0, yaw_chest=-10.0,
             z_twist0=0.56, z_twist1=0.90)
HIP = {1: vec((0.090, -0.040, 0.520)), -1: vec((-0.090, -0.020, 0.530))}
KNEE = {1: vec((0.115, 0.030, 0.068)), -1: vec((-0.140, 0.400, 0.505))}
ANKLE_FLOOR = {1: (0.115, -0.585), -1: (-0.150, 0.355)}          # shoe_on ankle_xy (before the toes-down turn)
FOOT = {1: (0.0, 64.0), -1: (8.0, 0.0)}                          # (yaw, toes_down)


def chest(x, y, z):
    return SP.point(z, (x, y, 0))


SH = {1: chest(0.180, 0.012, SP.z_neck - 0.088), -1: chest(-0.180, 0.012, SP.z_neck - 0.088)}

# torch: nozzle bent down from the mixer tube; handle in the right fist
NOZ_D = Vector((-0.05, 0.42, -0.906)).normalized()
TUBE_D = Vector((-0.10, 0.86, -0.50)).normalized()
HEAD = TIP - NOZ_D * 0.050
GRIP = HEAD - TUBE_D * 0.185
BACK = HEAD - TUBE_D * 0.265


def torch_parts():
    p = [E.limb("t_nozzle", HEAD, TIP, [0.0058, 0.0052, 0.0042], seg=10, side=(1, 0, 0), cap1=0.5),
         E.limb("t_tube", HEAD + TUBE_D * 0.010, GRIP + TUBE_D * 0.055, [0.0070, 0.0068, 0.0075], seg=10, side=(1, 0, 0)),
         E.limb("t_handle", GRIP + TUBE_D * 0.060, BACK, [0.0125, 0.0140, 0.0140, 0.0130], seg=14, side=(1, 0, 0))]
    side = L.ortho((1, 0, 0), TUBE_D)
    for i, sx in enumerate((1, -1)):
        k = BACK + TUBE_D * 0.012 + side * (sx * 0.016)
        p.append(E.limb(f"t_valve{i}", k - side * sx * 0.004, k + side * sx * 0.012, [0.0075, 0.0075], seg=10,
                        side=tuple(TUBE_D)))
    # hoses: from the back of the handle down to the floor behind him
    for i, sx in enumerate((1, -1)):
        a = BACK - TUBE_D * 0.008 + side * (sx * 0.006)
        pts = [a, a - TUBE_D * 0.06 + Vector((0, 0, -0.04)), vec((0.20 + 0.02 * sx, -0.05, 0.25)),
               vec((0.26 + 0.03 * sx, -0.35, 0.03)), vec((0.30 + 0.05 * sx, -0.70, 0.015))]
        p.append(E.loft(f"t_hose{i}", pts, [0.0068] * 5, side=(0, 0, 1), seg=10, sub=4, cap0=0.5, cap1=0.5))
    return p


def grip_frame():
    """Right fist round the torch handle: the handle axis runs from the little finger to the thumb (= S)."""
    S = TUBE_D
    N = L.ortho((-0.55, 0.0, -0.80), S)            # palm toward the handle from above his right
    F = N.cross(S).normalized()                    # right hand: S = F x N
    return F, N


ROD_A = TIP + Vector((-0.012, 0.018, -0.004))       # filler rod end at the flame
L_WR = vec((-0.105, 0.300, 0.640))


def left_hand():
    """Left hand: a pen grip on the filler rod, forearm resting on the left thigh."""
    rod_d = (ROD_A - (L_WR + Vector((0.03, 0.06, 0.005)))).normalized()
    S = -rod_d                                      # left hand: thumb side toward the back end of the rod
    N = L.ortho((0.3, 0.1, -1.0), rod_d)
    F = S.cross(N).normalized()                     # left hand: S = N x F  ->  F = S x N
    objs, info = H.hand("handL", L_WR, F, N, False, [(42, 62, 40), (50, 68, 44), (58, 72, 44), (64, 72, 40)],
                        spread=[2, 0, -3, -6], scale=HAND_S, width=0.086, finger_r=0.0092)
    return objs, info, rod_d


def gauntlet(prefix, el, wr):
    fd = (wr - el).normalized()
    return [E.limb(prefix, wr - fd * 0.115, wr - fd * 0.005, [(0.050, 0.044), (0.044, 0.040), (0.036, 0.031)],
                   seg=18, side=(0, 0, 1), cap0=0.15, cap1=0.3)]


# ------------------------------------------------------------------ head: mask down
P_HEAD = dict(E.MALE, nose=1.1, brow=1.6, jaw=1.12)


def hair(co, nrm):
    s = P_HEAD["scale"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    hl = np.interp(deg, [0, 40, 70, 85, 140, 180], [0.06, 0.06, 0.03, -0.02, -0.06, -0.075]) * s
    m = E.smoothstep(hl - 0.002, hl + 0.006, z)
    return nrm * (0.006 * m)[:, None]


def mask(_p):
    """Welding mask flipped down over the face, its headgear band round the skull and the two pivot bosses."""
    s = P_HEAD["scale"]
    rings = [(-0.140, 0.052, 0.062, 0.050, 0.030), (-0.095, 0.044, 0.092, 0.092, 0.050),
             (-0.030, 0.034, 0.102, 0.112, 0.062), (0.030, 0.026, 0.100, 0.110, 0.072),
             (0.075, 0.012, 0.092, 0.100, 0.082), (0.100, 0.000, 0.078, 0.082, 0.084)]
    shell = E.loft("h_mask", [(0, cy * s, z * s) for (z, cy, *_r) in rings],
                   [(rx * s, rf * s, rb * s) for (_z, _cy, rx, rf, rb) in rings], side=(1, 0, 0), seg=28, sub=3,
                   cap0=0.35, cap1=0.5)
    band = E.torus_obj("h_band", (0, -0.012 * s, 0.050 * s), 0.084 * s, 0.009 * s, rot=E.rot_x(-12), seg=28, mseg=8,
                       minor_y=0.014 * s)
    bosses = [E.ellipsoid(f"h_boss{sx}", (sx * 0.097 * s, -0.005 * s, 0.028 * s), (0.012, 0.020, 0.020), seg=12, rings=8)
              for sx in (1, -1)]
    return [shell, band] + bosses


MASK_KERNELS = [dict(c=(0, 0.150, 0.012), s=(0.040, 0.03, 0.014), a=-0.0045, face=(0, 1, 0)),   # filter window recess
                dict(c=(0, 0.150, 0.012), s=(0.055, 0.03, 0.026), a=0.0018, face=(0, 1, 0))]    # its raised frame


def head_kw():
    pivot = chest(0.0, 0.006, SP.z_neck - 0.008)
    nd = L.neck_dir(SP.yaw_chest, 34.0)
    return dict(P=P_HEAD, pivot=pivot, nd=nd, yaw=-6.0, pitch=-38.0, roll=-4.0, hair_fn=hair, extras_fn=mask,
                kernels=MASK_KERNELS, neck_r=((0.060, 0.062), (0.056, 0.058), (0.056, 0.056)), voxel=0.0018)


# ------------------------------------------------------------------ body
def jacket():
    rings = H.coat_rings(H.MAN_COAT, H.MAN_HIP, H.MAN_NECK, SP.z_hip, SP.z_neck, hem_dz=-0.115, grow=0.012)
    c = L.coat_loft("jacket", SP, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(c)
    zh = SP.z_hip
    parts = [c] + H.coat_details("w", SP, tree, female=False, collar_r=0.070, collar_z=SP.z_neck - 0.03, lapel=False,
                                 pockets=None, breast=(0.10, zh + 0.36, zh + 0.29), buttons=(), stand_collar=True)
    # front zip / placket and the waistband
    parts.append(E.surface_slab("w_placket", tree, [chest(0.010, 0.16, zh + 0.43), chest(0.010, 0.16, zh - 0.08)],
                                [0.022, 0.022], thick=0.004))
    parts.append(E.surface_slab("w_waist", tree, [chest(0.15, 0.10, zh - 0.07), chest(0.0, 0.17, zh - 0.08),
                                                  chest(-0.15, 0.10, zh - 0.07)], [0.04, 0.04, 0.04], thick=0.005))
    return parts


def legs():
    parts = []
    for s in (1, -1):
        sh_parts, ank = H.shoe_on(f"boot{s}", ANKLE_FLOOR[s], FOOT[s][0], heel=0.016, scale=1.10, toes_down=FOOT[s][1],
                                  boot=True)
        parts += sh_parts
        parts += H.bent_leg(f"leg{s}", HIP[s], KNEE[s], ank, r_thigh=0.080, r_knee=0.064, r_shin=0.060, r_hem=0.062,
                            hem_z=None)
    return parts


def build():
    parts = jacket() + legs() + torch_parts()
    F, N = grip_frame()
    wr_r = H.grip_wrist(GRIP, F, N, HAND_S, along=0.080, out=0.024)
    hr, _info = H.hand("handR", wr_r, F, N, True, [(66, 84, 56), (70, 86, 56), (74, 86, 54), (78, 84, 50)],
                       spread=[2, 0, -3, -6], scale=HAND_S, width=0.086, finger_r=0.0092)
    hl, info_l, rod_d = left_hand()
    el = {}
    for s, wr, pole in ((1, wr_r, SH[1] + Vector((0.55, -0.10, -0.25))), (-1, L_WR, SH[-1] + Vector((-0.50, -0.20, -0.40)))):
        ap, e = H.arm(f"arm{s}", SH[s], wr, UPPER, FORE, pole,
                      r=(0.060, 0.057, 0.054, 0.051, 0.052, (0.030, 0.023), (0.052, 0.057, 0.052)), sp=SP, side=s)
        parts += ap + gauntlet(f"gauntlet{s}", e, wr)
        el[s] = e
    # filler rod (thin: unioned after the decimation)
    grip_l = info_l["W"] + info_l["F"] * 0.075 * HAND_S + info_l["N"] * 0.018 * HAND_S
    rod = E.limb("rod", ROD_A, grip_l + (grip_l - ROD_A).normalized() * 0.11, [0.0026, 0.0026], seg=6, side=(0, 0, 1),
                 cap0=0.3, cap1=0.3)

    def folds():
        k = []
        for s in (1, -1):
            inner = (SH[s] - el[s]).normalized() + ((wr_r if s > 0 else L_WR) - el[s]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[s] + inner.normalized() * 0.040, s=0.016, a=-0.006)]
        k += L.groove([chest(0.13, 0.12, SP.z_hip + 0.25), chest(0.02, 0.17, SP.z_hip + 0.05)], 0.012, -0.004)
        k += L.groove([chest(-0.12, -0.13, SP.z_hip + 0.40), chest(-0.03, -0.13, SP.z_hip + 0.15)], 0.013, -0.003)
        k += L.groove([chest(0.12, -0.13, SP.z_hip + 0.40), chest(0.03, -0.13, SP.z_hip + 0.15)], 0.013, -0.003)
        # trouser creases behind the kneeling knee and at the front hip of the raised thigh
        k += L.groove([HIP[-1] + Vector((0, 0.10, -0.02)), KNEE[-1] + Vector((0, -0.05, -0.03))], 0.010, -0.003)
        return k
    obj = H.make_pose("pose_weld", parts, [(hr, wr_r), (hl, L_WR)], head_kw(), TRIS, voxel=VOXEL, folds=folds,
                      late=[rod])
    return obj


# ------------------------------------------------------------------ QA
T1 = (-12.45, 0.0, -1.3)


def transformer_context():
    if not L.import_ctx("transformer", T1, 90.0):
        L.proxy("tank", (0.90, 1.75, 1.20), (-12.45, 0.12 + 0.875, -1.3), color="4F5D55")
        L.proxy("plinth", (1.0, 0.12, 1.3), (-12.45, 0.06, -1.3), color="2A2B2D")
        L.proxy("seam", (0.02, 0.03, 1.22), (-12.0, 0.62, -1.3), color="2A2B2D")
    L.proxy("floor", (6.0, 0.02, 6.0), (-10.5, -0.01, -1.3), color="5A5852")
    L.proxy("wall_w", (0.1, 6.0, 8.0), (-13.05, 3.0, 0.0), color="6F8C78")


def renders(obj):
    H.clay(NAME, (1.5, 1.2, 1.9), (0.0, 0.62, 0.15), lens=42, res=(560, 640))
    H.clay(NAME + "_2", (-1.9, 1.0, 0.9), (0.0, 0.60, 0.15), lens=42, res=(560, 640))
    H.clay(NAME + "_3", (0.25, 0.95, 1.20), (-0.08, 0.66, 0.38), lens=55, res=(640, 640))       # torch and hands
    H.ghost(NAME + "_4", [obj], (1.5, 1.2, 1.9), (0.0, 0.62, 0.15), lens=42, res=(560, 640))
    H.ghost(NAME + "_5", [obj], (-1.4, 1.3, -1.6), (0.0, 0.62, 0.15), lens=42, res=(560, 640))
    pos, yaw = H.world_mount(T1, 90.0, (-0.10, 0.0, 0.93), 180.0)
    print(f"[echo3] welder world placement {tuple(round(v, 3) for v in pos)} yaw {yaw}")
    H.context(NAME + "_6", [obj], obj, pos, yaw, transformer_context, (-10.0, 1.6, -0.9), (-11.45, 0.9, -1.3), fov=48)


def main():
    mrlib.reset_scene()
    obj = build()
    H.turn(obj)
    H.add_empty("torch_tip", obj, TIP_G)
    H.contact_report("torch nozzle tip", obj, TIP_G, radius=0.02)
    path = mrlib.export_glb(NAME)
    H.verify(path, {"pose_weld": BUDGET}, empties=["torch_tip"], file_budget=BUDGET)
    if RENDER:
        renders(obj)


if __name__ == "__main__":
    main()
