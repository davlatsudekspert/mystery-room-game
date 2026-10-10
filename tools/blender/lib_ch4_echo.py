"""MYSTERY ROOM - Chapter 4 light-echo figures (build group I, docs/models/ch4.md section 9, docs/models/ch4_i.md).

Additive to lib_echo / lib_ch2_echoes / lib_ch3_echoes (never edits them). Two pipelines live side by side:

  * the DETAILED one (Strand, Leyla, the technicians, the clerk): the Chapter 3 figure pipeline of
    lib_ch3_echoes (organic lofts, boolean-united hands and a modelled head), here only with smaller
    budgets and the QA output redirected to qa/blender/ch4;
  * the LOW-POLY one below (`lp_figure`, used by echo_crowd and echo_named): a figure from a few lofts and
    ellipsoids (coat from the Chapter 3 ring tables, IK arms and legs, a stylised head with a hair /
    headgear kit), voxel-united into ONE closed shell and quadric-decimated to a few hundred triangles.
    These are only ever seen as glowing silhouettes at 4 - 14 m, so the silhouette (coat, hair, props) and the
    pose carry the character.

Build frame (as the other echo libraries): Blender, Z up, the figure faces +Y, +X = the figure's RIGHT.
`R(r, f, u)` writes a point as (right, forward, up); `gp(...)` converts a Godot figure-frame point
(x = left, y = up, z = forward; the exported frame) to build space. `H.turn` (the Chapter 3 helper) rotates the
finished mesh 180 deg about Z so the GLB faces Godot +Z.

  lp_figure(key, S, Pz, ...)   one low-poly figure / pose -> one closed shell (build space)
  ghost_set(...), grid(...)    QA: ghost-look renders of several figures side by side
"""
from __future__ import annotations

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_ch3_echoes as H  # noqa: E402
from lib_ch3_echoes import E, L, mrlib, vec  # noqa: E402

QA_DIR = os.path.join(mrlib.ROOT, "qa", "blender", "ch4")
L.QA_DIR = QA_DIR
H.QA_DIR = QA_DIR


def R(r: float, f: float, u: float) -> Vector:
    """(right, forward, up) -> build space."""
    return Vector((r, f, u))


def gp(p) -> Vector:
    """Godot figure-frame point (x, y, z) -> build space (the pre-turn frame)."""
    return Vector((-p[0], p[2], p[1]))


def rz(deg: float, v) -> Vector:
    return L.rz(deg, v)


def frame3(x, y, z) -> Matrix:
    """3x3 whose columns are the given axes (made orthonormal: y kept, x and z re-derived)."""
    Y = vec(y).normalized()
    Z = L.ortho(z, Y)
    X = Y.cross(Z)
    return Matrix((X, Y, Z)).transposed()


# ------------------------------------------------------------------ low-poly figure kit
MAN, WOMAN = H.MAN_COAT, H.WOMAN_COAT
STD = {"m": (H.MAN_HIP, H.MAN_NECK), "f": (H.WOMAN_HIP, H.WOMAN_NECK)}


def spec(**kw) -> dict:
    """Static description of a figure (defaults: an average man in a knee-length lab coat)."""
    s = dict(sex="m", z_hip=0.93, z_neck=1.50, w=1.0, d=1.0, grow=0.0, hem_dz=None, hem_flare=0.0, long_hem=None,
             leg=(0.074, 0.058, 0.047), shoe=1.0, boot=False, sleeve=(0.050, 0.045, 0.038), hand=1.0,
             hair="shag", head=1.0, gear=(), collar=True, coat_seg=22, long_leg=0.0)
    s.update(kw)
    return s


def pose(**kw) -> dict:
    """One pose: spine, feet, wrists (build space or None = hanging), head and props."""
    p = dict(hip_xy=(0.0, 0.0), neck_xy=(0.0, 0.02), yaw_hip=0.0, yaw_chest=0.0,
             feet={1: (0.10, 0.0, -6.0), -1: (-0.10, 0.03, 8.0)}, wrist={1: None, -1: None}, hint={}, hand_n={},
             head=(0.0, 0.0, 0.0), tilt=8.0, props=(), step=None)
    p.update(kw)
    return p


def _hair(kind: str, s: float):
    """Closed hair / headgear shells in head-local space (origin = skull base, +Y face, +Z up)."""
    k = []

    def e(c, r, rot=None):
        k.append(("e", tuple(x * s for x in c), tuple(x * s for x in r), rot))
    if kind == "shag":                         # 1970s feathered, collar-length, sideburns
        e((0, -0.008, 0.120), (0.092, 0.102, 0.104))
        e((0, -0.062, 0.078), (0.092, 0.070, 0.092))
        e((0, -0.080, 0.020), (0.086, 0.050, 0.078))
        for sx in (1, -1):
            e((sx * 0.084, 0.012, 0.078), (0.024, 0.050, 0.056))
    elif kind == "short":                      # short back and sides, side parting
        e((0, -0.006, 0.120), (0.083, 0.094, 0.090))
        e((0, -0.046, 0.090), (0.078, 0.052, 0.070))
        for sx in (1, -1):
            e((sx * 0.077, 0.010, 0.085), (0.014, 0.036, 0.040))
    elif kind == "bob":                        # the chin-length 1970s bob
        e((0, -0.014, 0.100), (0.096, 0.106, 0.118))
        e((0, -0.036, 0.046), (0.092, 0.088, 0.062))
        e((0, 0.060, 0.172), (0.070, 0.040, 0.026))          # fringe
    elif kind == "bun":                        # swept back with a bun
        e((0, -0.010, 0.118), (0.086, 0.098, 0.096))
        e((0, -0.096, 0.150), (0.042, 0.040, 0.040))
    elif kind == "receding":                   # old: grey fringe over the ears and the nape
        for sx in (1, -1):
            e((sx * 0.077, -0.020, 0.095), (0.020, 0.056, 0.052))
        e((0, -0.064, 0.100), (0.062, 0.034, 0.050))
    elif kind == "cropped":                    # stocky, cropped
        e((0, -0.004, 0.122), (0.081, 0.093, 0.086))
    elif kind == "long":                       # long, straight to the shoulders
        e((0, -0.010, 0.112), (0.090, 0.102, 0.108))
        e((0, -0.068, 0.040), (0.086, 0.052, 0.110))
    return k


def _gear(kind: str, s: float):
    k = []

    def e(c, r, rot=None):
        k.append(("e", tuple(x * s for x in c), tuple(x * s for x in r), rot))
    if kind == "cap":                          # flat-topped work cap with a peak
        e((0, 0.006, 0.182), (0.094, 0.108, 0.034))
        e((0, 0.000, 0.156), (0.090, 0.102, 0.034))
        e((0, 0.100, 0.168), (0.062, 0.046, 0.010), ("x", -12))
    elif kind == "visor":                      # clerk's eyeshade
        e((0, 0.084, 0.166), (0.088, 0.064, 0.009), ("x", -14))
        e((0, 0.000, 0.152), (0.090, 0.103, 0.014))
    elif kind == "mask":                       # welding mask flipped up on the head
        e((0, 0.014, 0.196), (0.112, 0.112, 0.074))
        e((0, 0.088, 0.160), (0.100, 0.026, 0.066), ("x", 18))
    elif kind == "headphones":                 # round the neck, the cups on the collar
        k.append(("t", (0, 0.0, -0.005), 0.088, 0.014))
        for sx in (1, -1):
            e((sx * 0.092, 0.040, -0.030), (0.030, 0.026, 0.040))
    elif kind == "glasses":
        for sx in (1, -1):
            e((sx * 0.040, 0.094, 0.112), (0.026, 0.010, 0.022))
    return k


def head_shells(S, pivot, yaw, pitch, roll, key):
    """Head, neck-top and hair as closed shells at their place in build space."""
    s = S["head"]
    parts = []
    M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ \
        Matrix.Rotation(math.radians(pitch), 4, "X") @ Matrix.Rotation(math.radians(roll), 4, "Y")

    def add(o):
        E.transform_obj(o, M)
        parts.append(o)
    add(E.ellipsoid(f"{key}_skull", (0, 0.010 * s, 0.104 * s), (0.077 * s, 0.092 * s, 0.103 * s), seg=18, rings=12))
    add(E.ellipsoid(f"{key}_jaw", (0, 0.030 * s, 0.050 * s), (0.056 * s, 0.070 * s, 0.062 * s), seg=16, rings=10))
    add(E.ellipsoid(f"{key}_nose", (0, 0.096 * s, 0.088 * s), (0.013 * s, 0.024 * s, 0.028 * s), seg=10, rings=8))
    add(E.limb(f"{key}_nape", (0, 0, -0.045 * s), (0, 0.004, 0.050 * s), [0.050 * s, 0.052 * s], seg=14))
    kits = _hair(S["hair"], s) + sum((_gear(g, s) for g in S["gear"]), [])
    for i, it in enumerate(kits):
        if it[0] == "e":
            _t, c, r, rot = it
            rm = None
            if rot is not None:
                rm = Matrix.Rotation(math.radians(rot[1]), 3, rot[0].upper())
            add(E.ellipsoid(f"{key}_hair{i}", c, r, rot=rm, seg=14, rings=9))
        else:
            _t, c, major, minor = it
            add(E.torus_obj(f"{key}_gear{i}", c, major * s, minor * s, seg=24, mseg=8))
    return parts


def mitten(name, wrist, F, N, hs, grip=False):
    F = vec(F).normalized()
    Nn = L.ortho(N, F)
    rm = frame3(F.cross(Nn), F, Nn)
    r = (0.036 * hs, 0.056 * hs, 0.020 * hs) if not grip else (0.040 * hs, 0.044 * hs, 0.034 * hs)
    return E.ellipsoid(name, vec(wrist) + F * (0.050 * hs if not grip else 0.040 * hs), r, rot=rm, seg=14, rings=9)


def lp_figure(key, S, Pz, voxel=0.012, tris=1200, hand_w=1.0):
    """One closed low-poly shell (build space) from a static spec and a pose. Returns (obj, ctx)."""
    zh, zn = S["z_hip"], S["z_neck"]
    sp = L.Spine(hip_xy=Pz["hip_xy"], neck_xy=Pz["neck_xy"], z_hip=zh, z_neck=zn, yaw_hip=Pz["yaw_hip"],
                 yaw_chest=Pz["yaw_chest"], z_twist0=zh + 0.04, z_twist1=zn - 0.14)
    std_hip, std_neck = STD[S["sex"]]
    table = S.get("table") or (MAN if S["sex"] == "m" else WOMAN)
    if S["long_hem"]:
        table = [S["long_hem"]] + list(table)
    rings = H.coat_rings(table, std_hip, std_neck, zh, zn, hem_dz=S["hem_dz"], grow=S["grow"],
                         hem_flare=S["hem_flare"])
    rings = [(r[0], r[1] * S["w"], r[2] * S["w"], r[3] * S["d"], r[4] * S["d"]) + tuple(r[5:]) for r in rings]
    coat = L.coat_loft(f"{key}_coat", sp, rings, seg=S["coat_seg"], sub=2, cap0=0.10, cap1=0.3)
    parts = [coat]
    w = S["w"]
    # ---- legs (knee forward by IK) and shoes
    ll = (zh - 0.04 - 0.075 + S["long_leg"])
    for sx in (1, -1):
        hip = sp.point(zh - 0.04, (sx * 0.088 * w, 0.0, 0.0))
        fx, fy, fyaw = Pz["feet"][sx]
        ank = Vector((fx, fy, 0.075))
        knee = E.ik2(hip, ank, 0.52 * ll, 0.50 * ll, hip + Vector((0, 1.0, 0.0)))
        r0, r1, r2 = S["leg"]
        parts.append(E.loft(f"{key}_leg{sx}", [hip + Vector((0, 0, 0.02)), knee, ank], [r0, r1, r2], side=(1, 0, 0),
                            seg=14, sub=3, cap0=0.3, cap1=0.3))
        fd = rz(fyaw, (0, 1, 0))
        sc = S["shoe"]
        rm = frame3(rz(fyaw, (1, 0, 0)), fd, (0, 0, 1))
        parts.append(E.ellipsoid(f"{key}_shoe{sx}", Vector((fx, fy, 0.036)) + fd * 0.042 * sc,
                                 (0.041 * sc, 0.116 * sc, 0.038 * sc), rot=rm, seg=14, rings=8))
        if S["boot"]:
            parts.append(E.limb(f"{key}_shaft{sx}", ank, ank + Vector((0, -0.004, 0.17)), [0.054, 0.058, 0.060],
                                seg=14, cap1=0.3))
    # ---- arms and hands
    sh, el, wr = {}, {}, {}
    zs = zn - 0.078
    ua, fa = 0.30 * (zn / 1.50), 0.25 * (zn / 1.50)
    rs = S["sleeve"]
    for sx in (1, -1):
        sh[sx] = sp.point(zs, (sx * (0.150 * w + 0.014), 0.006, 0.0))
        tgt = Pz["wrist"][sx]
        if tgt is None:
            tgt = sh[sx] + Vector((sx * 0.050, 0.035, -(ua + fa) * 0.965))
        wr[sx] = vec(tgt)
        hint = Pz["hint"].get(sx, (sx * 0.35, -0.45, -0.30))
        el[sx] = E.ik2(sh[sx], wr[sx], ua, fa, sh[sx] + Vector(hint))
        parts.append(E.loft(f"{key}_arm{sx}", [sh[sx] + Vector((0, 0, 0.012)), el[sx], wr[sx]], [rs[0], rs[1], rs[2]],
                            side=(0, 1, 0), seg=12, sub=3, cap0=0.8, cap1=0.3))
        parts.append(E.ellipsoid(f"{key}_delt{sx}", sh[sx] + Vector((sx * 0.004, 0, -0.012)),
                                 (rs[0] * 1.06, rs[0] * 1.02, rs[0] * 1.10), seg=12, rings=8))
        F = (wr[sx] - el[sx]).normalized()
        N = Pz["hand_n"].get(sx, Vector((-sx * 0.9, 0.2, 0.0)))
        grip = Pz.get("grip", {}).get(sx, False)
        parts.append(mitten(f"{key}_hand{sx}", wr[sx], F, N, S["hand"], grip=grip))
    # ---- head
    tilt = math.radians(Pz["tilt"])
    nd = rz(Pz["yaw_chest"], (0.0, math.sin(tilt), math.cos(tilt)))
    base = sp.point(zn - 0.030, (0.0, 0.004, 0.0))
    pivot = base + nd * 0.085
    parts.append(E.limb(f"{key}_neck", base - Vector((0, 0, 0.03)), pivot + nd * 0.02, [0.058, 0.050, 0.050], seg=14,
                        cap0=0.5, cap1=0.2))
    hy, hp, hr = Pz["head"]
    parts += head_shells(S, pivot, Pz["yaw_chest"] + hy, hp, hr, key)
    if S["collar"]:
        c = sp.point(zn - 0.012, (0, 0.0, 0))
        for sx in (1, -1):
            wing = E.ellipsoid(f"{key}_collar{sx}", c + sp.right(zn) * (sx * 0.050) + sp.front(zn) * 0.060,
                               (0.048, 0.042, 0.018), rot=Matrix.Rotation(math.radians(-sx * 28 + Pz["yaw_chest"]), 3, "Z"),
                               seg=10, rings=6)
            parts.append(wing)
    ctx = dict(sp=sp, sh=sh, el=el, wr=wr, pivot=pivot, head=(hy, hp, hr), zn=zn, zh=zh, S=S, Pz=Pz, key=key)
    for fn in Pz["props"]:
        parts += fn(ctx)
    # ---- unite, simplify
    obj = E.union_remesh(parts, key, voxel)
    L.drop_small_islands(obj, min_verts=30)
    E.taubin(obj, 2)
    centres = [pivot + Vector((0, 0, 0.10))] + [wr[1], wr[-1]]
    wfn = L.gauss_w(centres, 0.09)
    E.decimate(obj, tris, vgroup_weights=wfn, vg_factor=0.6 * hand_w)
    E.clean_mesh(obj)
    low = min(v.co.z for v in obj.data.vertices)           # the feet stand exactly on the floor (y = 0 in Godot)
    obj.data.transform(Matrix.Translation((0.0, 0.0, -low)))
    ctx["lift"] = -low
    return obj, ctx


# ------------------------------------------------------------------ QA helpers
def ghost_row(name, objs, xs, cam, target, lens=40.0, res=(1200, 560), samples=20, everything=None):
    """Ghost-look render of several figures standing at x offsets (build +X = right). Restores the positions;
    `everything` = every figure of the scene (those not in `objs` are hidden from the render)."""
    if everything is not None:
        show_only(everything, objs)
    for o, x in zip(objs, xs):
        o.location.x = x
    path = H.L.ghost(name, objs, cam, target, lens=lens, res=res, samples=samples)
    for o in objs:
        o.location.x = 0.0
    if everything is not None:
        show_only(everything, everything)
    return path


def show_only(objs, keep):
    for o in objs:
        o.hide_render = o not in keep
        o.hide_viewport = o not in keep
