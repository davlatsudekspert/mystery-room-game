"""MYSTERY ROOM - Chapter 4 1979 staff figures, DETAILED pipeline (echo_tech_panel, echo_tech_wheels, echo_clerk_post).

Builders on top of lib_ch4_echo / lib_ch3_echoes: the Chapter 2 / 3 lab coats (the scientists' and technicians' coat ring
tables, collars, pockets, buttons), trousers or stockings and shoes, IK sleeves, fists and flat hands, the Chapter 2 heads
(the scientists' bob and side-parted hair, the welder's crop) and a clerk's eyeshade. Everything is built in the Blender build
frame (Z up, the figure faces +Y, +X = the figure's RIGHT) and turned to Godot +Z by the caller (`H.turn`).

  man_coat / woman_coat        coat loft + details       man_legs / woman_legs   trousers + shoes / stockings + heels
  fist(...)                    a hand closed round a bar or ball at a point
  figure(...)                  arms (IK) + hands + head -> one closed shell via lib_ch4_echo.make_pose
"""
from __future__ import annotations

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_ch4_echo as C  # noqa: E402
from lib_ch4_echo import E, H, L, mrlib, vec  # noqa: E402

SCI = H.load_model("echo_scientists")            # hair_bob (woman), hair_side_part + P_B (man)
WELD = H.load_model("echo_welder")               # hair (a short crop) + P_HEAD (a heavier jaw)
MAN_SLEEVE = (0.056, 0.053, 0.050, 0.047, 0.049, (0.027, 0.020), (0.048, 0.053, 0.048))
WOMAN_SLEEVE = (0.050, 0.047, 0.044, 0.041, 0.044, (0.0235, 0.0175), (0.044, 0.049, 0.045))
NECK_R = ((0.058, 0.060), (0.054, 0.056), (0.054, 0.054))


# ------------------------------------------------------------------ coats
def man_coat(key, sp, hem_dz=None, grow=0.004, pockets=True):
    rings = H.coat_rings(H.MAN_COAT, H.MAN_HIP, H.MAN_NECK, sp.z_hip, sp.z_neck, hem_dz=hem_dz, grow=grow)
    c = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(c)
    zh = sp.z_hip
    return [c] + H.coat_details(key, sp, tree, female=False, collar_r=0.068, collar_z=sp.z_neck - 0.028,
                                pockets=(0.120, zh - 0.01, zh - 0.12, 0.135) if pockets else None,
                                breast=(-0.100, zh + 0.38, zh + 0.31),
                                buttons=(zh + 0.24, zh + 0.14, zh + 0.04), button_x=0.004)


def woman_coat(key, sp):
    rings = H.coat_rings(H.WOMAN_COAT, H.WOMAN_HIP, H.WOMAN_NECK, sp.z_hip, sp.z_neck)
    c = L.coat_loft(f"{key}_coat", sp, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(c)
    zh = sp.z_hip
    return [c] + H.coat_details(key, sp, tree, female=True, collar_r=0.060, collar_z=sp.z_neck - 0.018,
                                pockets=(0.112, zh - 0.045, zh - 0.155, 0.125), breast=(-0.088, zh + 0.375, zh + 0.305),
                                buttons=(zh + 0.28, zh + 0.17, zh + 0.06, zh - 0.05), button_x=-0.004)


# ------------------------------------------------------------------ legs
def man_legs(key, sp, feet, scale=1.06, top_z=0.55, r_top=0.066):
    """Trousers + shoes. `top_z`: where the trouser leg starts (raise it under a coat that stops at the hip)."""
    parts = []
    for s in (1, -1):
        ax, ay, fy = feet[s]
        top = sp.point(top_z, (s * 0.098, 0.0, 0.0))
        shp, ank = H.shoe_on(f"{key}_shoe{s}", (ax, ay), fy, heel=0.014, scale=scale)
        parts += shp
        parts += L.trouser_leg(f"{key}_trouser{s}", top, ank, r_top=r_top, r_knee=0.060, r_hem=0.058)
    return parts


def woman_legs(key, feet, knees):
    parts = []
    for s in (1, -1):
        (ax, ay), fy = feet[s]
        shp, ank = H.shoe_on(f"{key}_shoe{s}", (ax, ay), fy, heel=0.026, scale=0.93, toe=0.95)
        parts += shp
        parts += L.lower_leg(f"{key}_leg{s}", knees[s], ank, calf=0.058, shin=0.043, knee_r=0.047, ankle_r=0.025)
    return parts


# ------------------------------------------------------------------ hands
def fist(key, side, centre_b, F, N, scale=1.0, curls=None, along=0.088, out=0.028, width=0.080, finger_r=0.0086):
    """A hand closed round a bar or ball whose centre is `centre_b` (build space). F = fingers' direction, N = out of the
    palm toward the held object; the held axis is F x N. Returns (parts, wrist)."""
    F = vec(F).normalized()
    N = L.ortho(N, F)
    wr = H.grip_wrist(centre_b, F, N, scale, along=along, out=out)
    curls = curls or [(42, 58, 40), (44, 60, 40), (46, 60, 38), (48, 58, 36)]
    parts, _info = H.hand(f"{key}_hand{'R' if side == 1 else 'L'}", wr, F, N, side == 1, curls, spread=[1, 0, -2, -5],
                          scale=scale, width=width, finger_r=finger_r)
    return parts, wr


def flat(key, side, palm_b, F, N, scale=1.0, curl=1.0):
    parts, wr, _ = H.flat_hand(f"{key}_hand{'R' if side == 1 else 'L'}", palm_b, F, N, side == 1, scale, curl=curl,
                               width=0.080, finger_r=0.0086)
    return parts, wr


def relaxed(key, side, scale=1.0):
    def make(el, wr):
        objs, _ = H.relaxed_hand(f"{key}_hand{'R' if side == 1 else 'L'}", el, wr, side == 1, scale)
        return objs
    return make


# ------------------------------------------------------------------ heads
def head_man(sp, yaw, pitch, roll=0.0, tilt=14.0, kind="side", extras=None, dz=0.008):
    pivot = sp.point(sp.z_neck - dz, (0.0, 0.006, 0.0))
    nd = L.neck_dir(sp.yaw_chest, tilt)
    P, hair = (SCI.P_B, SCI.hair_side_part) if kind == "side" else (WELD.P_HEAD, WELD.hair)
    kw = dict(P=P, pivot=pivot, nd=nd, yaw=yaw, pitch=pitch, roll=roll, hair_fn=hair, neck_r=NECK_R, voxel=0.0018)
    if extras is not None:
        kw["extras_fn"] = extras
    return kw


def head_woman(sp, yaw, pitch, roll=0.0, tilt=12.0):
    pivot = sp.point(sp.z_neck - 0.005, (0.0, 0.004, 0.0))
    nd = L.neck_dir(sp.yaw_chest + 2.0, tilt)
    return dict(P=E.FEMALE, pivot=pivot, nd=nd, yaw=yaw, pitch=pitch, roll=roll, hair_fn=SCI.hair_bob, voxel=0.0018)


def eyeshade(_p):
    """A clerk's eyeshade: a thin band round the brow and a stiff curved brim over the eyes."""
    s = SCI.P_B["scale"]
    band = E.torus_obj("h_band", (0, -0.010 * s, 0.052 * s), 0.085 * s, 0.0085 * s, rot=E.rot_x(-8), seg=28, mseg=8,
                       minor_y=0.011 * s)
    brim = E.ellipsoid("h_brim", (0, 0.092 * s, 0.046 * s), (0.086 * s, 0.060 * s, 0.0055 * s), rot=E.rot_x(-12), seg=24,
                       rings=8)
    return [band, brim]


# ------------------------------------------------------------------ the figure
def figure(key, sp, parts, sex, hands, poles, head, tris, voxel=0.0034, sleeve=None, scale_arm=None):
    """hands[side] = (hand parts, wrist) or a callable(el, wr) -> hand parts with the wrist in poles[side][2] (relaxed).
    poles[side] = (pole point, wrist or None). Returns the closed shell."""
    man = sex == "m"
    dz, hw = (0.088, 0.178) if man else (0.080, 0.155)
    l1, l2 = (0.315, 0.262) if man else (0.300, 0.236)
    rr = sleeve or (MAN_SLEEVE if man else WOMAN_SLEEVE)
    sh = {1: sp.point(sp.z_neck - dz, (hw, 0.010, 0.0)), -1: sp.point(sp.z_neck - dz, (-hw, 0.010, 0.0))}
    el, wr, hs = {}, {}, []
    for s in (1, -1):
        h = hands[s]
        if callable(h):
            w = poles[s][1] if poles[s][1] is not None else sh[s] + Vector((s * 0.055, 0.040, -(l1 + l2) * 0.95))
            ap, e = H.arm(f"{key}_arm{s}", sh[s], w, l1, l2, poles[s][0], r=rr, sp=sp, side=s)
            parts += ap
            hs.append((h(e, vec(w)), vec(w)))
            el[s], wr[s] = e, vec(w)
        else:
            hp, w = h
            ap, e = H.arm(f"{key}_arm{s}", sh[s], w, l1, l2, poles[s][0], r=rr, sp=sp, side=s)
            parts += ap
            hs.append((hp, vec(w)))
            el[s], wr[s] = e, vec(w)
    # hs is in the order (1, -1)

    def folds():
        k = []
        for s in (1, -1):
            inner = (sh[s] - el[s]).normalized() + (wr[s] - el[s]).normalized()
            if inner.length > 0.2:
                k += [dict(c=el[s] + inner.normalized() * 0.036, s=0.015, a=-0.005)]
        return k
    obj = C.make_pose(key, parts, hs, head, tris, voxel=voxel, folds=folds)
    return obj, sh, el, wr
