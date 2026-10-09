"""Light echo: two 1979 Nursery technicians at the dead autoclaves (Chapter 3 kept echoes `tech_a`, `tech_b`).

Output: game/assets/models/echo_technicians.glb (Godot axes; each figure faces +Z, -X = its right)
  tech_a   a woman in a knee-length lab coat (the scientists' 1970s chin-length bob), standing 0.62 m from the
           vessel axis, reading its pressure gauge: a clipboard on her left palm, a pen in her right hand on the
           sheet, her eyes on the vessel at about 1.45 m. Origin between her feet.
  tech_b   a man in a lab coat crouching in a wide squat (left heel raised) at the vessel's drain valve: his right
           hand grips the top of a handwheel whose centre is at (-0.04, 0.40, 0.26), his left forearm rests on his
           left knee, he looks down at the valve. Origin between his feet.
Both are root-level objects, ONE closed mesh each (M_Echo); the code reparents them to autoclave_dead `echo_mount`
(0, 0, 0.62), facing -Z, on dead_0 (tech_a) and dead_1 (tech_b).
Budget: <= 8,000 tris each, <= 16,000 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_technicians.py [-- --no-render] [-- --only tech_a]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch3_echoes as H  # noqa: E402
from lib_ch3_echoes import E, L, mrlib, vec  # noqa: E402

NAME = "echo_technicians"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 8000, 16000
SCI = H.load_model("echo_scientists")           # hair_bob (woman), hair_side_part (man), P_B
VALVE_G = (-0.04, 0.40, 0.26)                     # handwheel centre (Godot figure frame), wheel Ø 0.08 facing him
GAUGE_G = (-0.05, 1.45, 0.20)                     # where tech_a looks (vessel front)


# ====================================================================== tech_a: the woman with the clipboard
def tech_a():
    key = "tech_a"
    tris = dict(body=4500, hand=600, head=1750)
    s = 0.95
    sp = L.Spine(hip_xy=(0.010, -0.010), neck_xy=(-0.006, 0.006), z_hip=0.86, z_neck=1.41, yaw_hip=-4.0, yaw_chest=6.0,
                 z_twist0=0.90, z_twist1=1.24)
    rings = H.coat_rings(H.WOMAN_COAT, H.WOMAN_HIP, H.WOMAN_NECK, sp.z_hip, sp.z_neck)
    coat = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(coat)
    parts = [coat] + H.coat_details(key, sp, tree, female=True, collar_r=0.060, collar_z=1.392,
                                    pockets=(0.112, 0.815, 0.705, 0.125), breast=(-0.088, 1.235, 1.165),
                                    buttons=(1.140, 1.030, 0.920, 0.810), button_x=-0.004)
    knee = {1: vec((0.088, 0.000, 0.470)), -1: vec((-0.082, 0.052, 0.462))}
    feet = {1: ((0.100, -0.012), -6.0), -1: ((-0.100, 0.040), 12.0)}
    for sx in (1, -1):
        sh_parts, ank = H.shoe_on(f"{key}_shoe{sx}", feet[sx][0], feet[sx][1], heel=0.026, scale=0.93, toe=0.95)
        parts += sh_parts
        parts += L.lower_leg(f"{key}_leg{sx}", knee[sx], ank, calf=0.058, shin=0.043, knee_r=0.047, ankle_r=0.025)
    # clipboard on the left palm, tilted up toward her face
    cb = vec((-0.030, 0.270, 1.085))
    n = Vector((0.08, -0.56, 0.82)).normalized()
    u = L.ortho((1.0, 0.0, 0.0), n)
    v = n.cross(u)                                     # along the board, away from her
    R = L.frame_matrix(u, v, n)
    parts.append(L.rounded_box(f"{key}_board", (0.230, 0.320, 0.007), cb, R, bevel=0.002, segments=1))
    parts.append(L.rounded_box(f"{key}_sheet", (0.205, 0.270, 0.004), cb + n * 0.0045 - v * 0.012, R, bevel=0.0015,
                               segments=1))
    parts.append(L.rounded_box(f"{key}_clip", (0.080, 0.030, 0.012), cb + n * 0.008 + v * 0.140, R, bevel=0.003,
                               segments=1))
    palm = cb - u * 0.060 - v * 0.070 - n * 0.006
    hl, wl, _ = H.flat_hand(f"{key}_handL", palm, v * 0.85 + u * 0.4, n, False, s, curl=1.2)
    # right hand writing: a loose fist over the sheet, the pen tip on the paper
    tip = cb + u * 0.040 + v * 0.010 + n * 0.006
    pen_d = (n * 0.62 - v * 0.45 + u * 0.50).normalized()
    Fr = (-u * 0.30 + v * 0.55 - n * 0.55).normalized()
    Nr = L.ortho(-n * 0.8 - u * 0.6, Fr)
    wr_r = tip + pen_d * 0.045 - Fr * 0.070 * s - Nr * 0.025 * s
    hr, _info = H.hand(f"{key}_handR", wr_r, Fr, Nr, True, [(38, 52, 34), (52, 66, 40), (60, 70, 40), (64, 70, 38)],
                       spread=[2, 0, -3, -7], scale=s, width=0.076, finger_r=0.0082)
    pen = E.limb(f"{key}_pen", tip, tip + pen_d * 0.140, [0.0030, 0.0042, 0.0045, 0.0045, 0.0040],
                 ts=[0, 0.08, 0.2, 0.9, 1.0], seg=8, side=tuple(u), cap0=0.3, cap1=0.5)
    sh = {1: sp.point(1.330, (0.154, 0.018, 0)), -1: sp.point(1.338, (-0.156, -0.004, 0))}
    el = {}
    for sx, wr, pole in ((1, wr_r, sh[1] + Vector((0.45, -0.30, -0.25))), (-1, wl, sh[-1] + Vector((-0.40, -0.25, -0.35)))):
        ap, e = H.arm(f"{key}_arm{sx}", sh[sx], wr, 0.300, 0.236, pole,
                      r=(0.050, 0.047, 0.044, 0.041, 0.044, (0.0235, 0.0175), (0.044, 0.049, 0.045)), sp=sp, side=sx)
        parts += ap
        el[sx] = e
    pivot = sp.point(1.405, (0.0, 0.004, 0.0))
    nd = L.neck_dir(sp.yaw_chest + 2.0, 12.0)
    head = dict(P=E.FEMALE, pivot=pivot, nd=nd, yaw=4.0, pitch=-6.0, roll=-3.0, hair_fn=SCI.hair_bob, voxel=0.0018)

    def folds():
        k = []
        for sx, wr in ((1, wr_r), (-1, wl)):
            inner = (sh[sx] - el[sx]).normalized() + (wr - el[sx]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[sx] + inner.normalized() * 0.034, s=0.014, a=-0.0045)]
        k += L.groove([sp.point(1.15, (-0.020, 0.15, 0)), sp.point(0.80, (-0.022, 0.15, 0))], 0.005, -0.0026,
                      face=sp.front(1.0))
        k += L.groove([vec((-0.022, 0.2, 0.78)), vec((-0.018, 0.22, 0.60)), vec((-0.010, 0.26, 0.43))], 0.009, -0.007,
                      face=(0, 1, 0))
        k += L.groove([vec((0.15, 0.08, 0.80)), vec((0.165, 0.10, 0.44))], 0.012, -0.0035)
        k += L.groove([vec((-0.09, 0.13, 0.66)), vec((-0.095, 0.17, 0.46))], 0.014, 0.003)
        k += L.groove([vec((0.0, -0.16, 0.62)), vec((0.0, -0.16, 0.43))], 0.004, -0.004, face=(0, -1, 0))
        return k

    def flutes(body):
        def amp(co, t):
            return 0.0065 * E.smoothstep(0.70, 0.44, co[:, 2]) * (0.65 + 0.35 * np.sin(co[:, 0] * 23.0 + co[:, 1] * 17.0))
        L.flutes(body, (0.008, 0.012, 0.0), (0, 0, 1), 9, amp, phase=0.4,
                 region=lambda co: E.smoothstep(0.69, 0.60, co[:, 2]) * (co[:, 2] > 0.40))

    return H.make_pose(key, parts, [(hr, wr_r), (hl, wl)], head, tris, voxel=0.0034, folds=folds, flutes=flutes,
                       late=[pen])


# ====================================================================== tech_b: the man crouching at the valve
def tech_b():
    key = "tech_b"
    tris = dict(body=4550, hand=580, head=1700)
    s = 1.04
    sp = L.Spine(hip_xy=(0.0, -0.150), neck_xy=(0.020, 0.105), z_hip=0.43, z_neck=0.95, yaw_hip=0.0, yaw_chest=-6.0,
                 z_twist0=0.47, z_twist1=0.80)
    rings = H.coat_rings(H.MAN_COAT, H.MAN_HIP, H.MAN_NECK, sp.z_hip, sp.z_neck, hem_dz=-0.03, grow=0.004)
    coat = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(coat)
    zh = sp.z_hip
    parts = [coat] + H.coat_details(key, sp, tree, female=False, collar_r=0.068, collar_z=sp.z_neck - 0.028,
                                    pockets=None, breast=(-0.100, zh + 0.38, zh + 0.31),
                                    buttons=(zh + 0.24, zh + 0.14, zh + 0.04), button_x=0.004)
    # coat skirt: hangs down behind the hips almost to the floor; its front panels lie on the thighs
    parts.append(E.loft(f"{key}_skirt", [vec((0.0, -0.150, 0.46)), vec((0.0, -0.200, 0.30)), vec((0.0, -0.235, 0.15)),
                                         vec((0.0, -0.250, 0.075))],
                        [(0.205, 0.205, 0.120, 0.125, 2.2), (0.220, 0.220, 0.105, 0.125, 2.2),
                         (0.232, 0.232, 0.090, 0.120, 2.2), (0.236, 0.236, 0.080, 0.112, 2.2)],
                        side=(1, 0, 0), seg=36, sub=3, cap0=0.15, cap1=0.12))
    hip = {1: vec((0.095, -0.140, 0.430)), -1: vec((-0.095, -0.140, 0.430))}
    knee = {1: vec((0.215, 0.200, 0.480)), -1: vec((-0.215, 0.185, 0.455))}
    feet = {1: ((0.185, 0.020), -18.0, 0.0), -1: ((-0.190, -0.130), 16.0, 22.0)}
    for sx in (1, -1):
        sh_parts, ank = H.shoe_on(f"{key}_shoe{sx}", feet[sx][0], feet[sx][1], heel=0.014, scale=1.07,
                                  toes_down=feet[sx][2])
        parts += sh_parts
        parts += H.bent_leg(f"{key}_leg{sx}", hip[sx], knee[sx], ank, r_thigh=0.074, r_knee=0.060, r_shin=0.058,
                            r_hem=0.060)
        # the coat's front panel lying over the thigh
        a, b = hip[sx] + Vector((0.0, 0.05, 0.06)), knee[sx] + Vector((-sx * 0.02, -0.07, 0.055))
        parts.append(E.limb(f"{key}_panel{sx}", a, b, [(0.090, 0.022), (0.085, 0.020), (0.075, 0.016)], seg=14,
                            side=(sx * 1.0, 0.0, 0.0), cap0=0.2, cap1=0.2))
    # handwheel grip (top of the rim), overhand: fingers forward over the rim, palm down, thumb to his left
    wheel = H.g2b(VALVE_G)
    grip = wheel + Vector((0.0, 0.0, 0.040))
    F = Vector((0.0, 0.92, -0.39)).normalized()
    N = L.ortho((0.0, 0.25, -1.0), F)
    wr_r = H.grip_wrist(grip, F, N, s, along=0.080, out=0.020)
    hr, _info = H.hand(f"{key}_handR", wr_r, F, N, True, [(55, 72, 48), (60, 74, 48), (64, 74, 46), (68, 72, 42)],
                       spread=[3, 0, -3, -7], scale=s, width=0.082, finger_r=0.0088)
    # left forearm on the left knee, the hand hanging past it
    wl = knee[-1] + Vector((0.045, 0.095, 0.020))
    sh = {1: sp.point(sp.z_neck - 0.088, (0.178, 0.010, 0)), -1: sp.point(sp.z_neck - 0.088, (-0.178, 0.010, 0))}
    el = {}
    for sx, wr, pole in ((1, wr_r, sh[1] + Vector((0.50, -0.10, -0.30))), (-1, wl, sh[-1] + Vector((-0.40, 0.10, -0.40)))):
        ap, e = H.arm(f"{key}_arm{sx}", sh[sx], wr, 0.315, 0.262, pole, r=(0.056, 0.053, 0.050, 0.047, 0.049,
                                                                         (0.027, 0.020), (0.048, 0.053, 0.048)),
                      sp=sp, side=sx)
        parts += ap
        el[sx] = e
    Fl = Vector((0.15, 0.55, -0.82)).normalized()
    hl, _ = H.hand(f"{key}_handL", wl, Fl, L.ortho((0.9, 0.2, 0.2), Fl), False,
                   [(16, 24, 12), (22, 30, 14), (26, 34, 16), (30, 38, 18)], spread=[3, 0, -2, -5], scale=s)
    pivot = sp.point(sp.z_neck - 0.008, (0.0, 0.006, 0.0))
    nd = L.neck_dir(sp.yaw_chest, 30.0)
    head = dict(P=SCI.P_B, pivot=pivot, nd=nd, yaw=4.0, pitch=-46.0, roll=2.0, hair_fn=SCI.hair_side_part,
                neck_r=((0.058, 0.060), (0.054, 0.056), (0.054, 0.054)), voxel=0.0018)

    def folds():
        k = []
        for sx, wr in ((1, wr_r), (-1, wl)):
            inner = (sh[sx] - el[sx]).normalized() + (wr - el[sx]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[sx] + inner.normalized() * 0.040, s=0.016, a=-0.0055)]
        k += L.groove([sp.point(zh + 0.40, (0.12, -0.12, 0)), sp.point(zh + 0.18, (0.03, -0.12, 0))], 0.013, -0.003,
                      face=-sp.front(zh + 0.3))
        k += L.groove([sp.point(zh + 0.40, (-0.12, -0.12, 0)), sp.point(zh + 0.18, (-0.03, -0.12, 0))], 0.013, -0.003,
                      face=-sp.front(zh + 0.3))
        for sx in (1, -1):
            k += L.groove([vec((sx * 0.10, -0.22, 0.40)), vec((sx * 0.16, -0.26, 0.12))], 0.012, -0.004)
        return k

    return H.make_pose(key, parts, [(hr, wr_r), (hl, wl)], head, tris, voxel=0.0034, folds=folds)


FIGS = {"tech_a": tech_a, "tech_b": tech_b}


# ====================================================================== QA
DEAD = {"tech_a": (9.65, 0.0, -3.5), "tech_b": (10.9, 0.0, -3.5)}


def nursery_context():
    for k, pos in DEAD.items():
        if not L.import_ctx("autoclave_dead", pos, 0.0):
            L.proxy(f"vessel_{k}", (0.85, 1.75, 0.85), (pos[0], 0.35 + 0.875, pos[2]), color="D8D8D8")
            L.proxy(f"frame_{k}", (0.9, 0.35, 0.9), (pos[0], 0.175, pos[2]), color="2A2B2D")
    gx, gy, gz = H.world_mount(DEAD["tech_a"], 0.0, (0.0, 0.0, 0.62), 180.0)[0]
    L.proxy("gauge", (0.12, 0.12, 0.04), (gx + 0.05, 1.45, gz - 0.20), color="E8DFC8")
    vx, vy, vz = H.world_mount(DEAD["tech_b"], 0.0, (0.0, 0.0, 0.62), 180.0)[0]
    L.proxy("valve", (0.08, 0.08, 0.02), (vx + 0.04, 0.26, vz - 0.40), color="B08D57")
    L.proxy("floor", (9.0, 0.02, 8.0), (8.75, -0.01, 0.0), color="3E5A48")
    L.proxy("wall_n", (9.0, 4.0, 0.1), (8.75, 2.0, -4.05), color="D9D6CB")


def renders(objs):
    by = {o.name: o for o in objs}
    for nm, o in by.items():
        H.solo(objs, [o])
        top = 0.88 if nm == "tech_a" else 0.55
        H.clay(f"{NAME}_{nm}", (1.5, 1.3, 2.2), (0.0, top, 0.05), lens=42, res=(480, 640))
        H.clay(f"{NAME}_{nm}_2", (-1.8, 1.1, 0.6), (0.0, top, 0.05), lens=42, res=(480, 640))
        H.ghost(f"{NAME}_{nm}_3", [o], (1.0, 1.4, -2.4), (0.0, top, 0.05), lens=42, res=(480, 640))
    if "tech_a" in by:
        H.solo(objs, [by["tech_a"]])
        H.clay(f"{NAME}_tech_a_4", (-0.25, 1.55, 0.75), (0.02, 1.10, 0.25), lens=50, res=(640, 640))   # clipboard
    if "tech_b" in by:
        H.solo(objs, [by["tech_b"]])
        L.proxy("wheel", (0.08, 0.08, 0.02), VALVE_G, color="B08D57")
        H.clay(f"{NAME}_tech_b_4", (-0.6, 0.85, 0.75), VALVE_G, lens=50, res=(640, 640))               # valve hand
    # in context: both at their mounts, seen from the port_a memory view
    H.solo(objs, objs)
    if len(by) == 2:
        pa, ya = H.world_mount(DEAD["tech_a"], 0.0, (0.0, 0.0, 0.62), 180.0)
        pb, yb = H.world_mount(DEAD["tech_b"], 0.0, (0.0, 0.0, 0.62), 180.0)
        L.place(by["tech_b"], pb, yb)
        H.context(f"{NAME}_5", objs, by["tech_a"], pa, ya, nursery_context, (9.1, 1.6, 0.4), (10.3, 1.0, -2.45), fov=50)
        L.unplace(by["tech_b"])


def main():
    mrlib.reset_scene()
    objs = []
    for nm, fn in FIGS.items():
        if ONLY and nm not in ONLY:
            continue
        o = fn()
        H.turn(o)
        objs.append(o)
    if any(o.name == "tech_b" for o in objs):
        H.contact_report("tech_b right hand on the handwheel rim top", [o for o in objs if o.name == "tech_b"][0],
                         (VALVE_G[0], VALVE_G[1] + 0.04, VALVE_G[2]))
    path = mrlib.export_glb(NAME)
    H.verify(path, {o.name: POSE_BUDGET for o in objs}, file_budget=FILE_BUDGET)
    if RENDER:
        renders(objs)


if __name__ == "__main__":
    main()
