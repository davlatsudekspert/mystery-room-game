"""Light echo: Prof. Emil Strand, 1979 — an older man, slightly stooped, in a long coat, standing at a
chalkboard and raising a stick of chalk to it (Chapter 1+ story beat; same pipeline as echo_leyla_sitting).

Output: game/assets/models/echo_strand_standing.glb
  echo_body  origin = floor between the feet (0, 0, 0). Height to the crown ~1.67 m (stooped).
  echo_head  head + neck + fringe of hair + short beard, child of echo_body, origin = neck pivot
             (base of the neck inside the collar). Rotate about its local vertical axis (Godot +Y) to turn
             his head; positive yaw turns him to his left (Godot -X side of the model).
Facing: the board is in front of him = Blender +Y = Godot -Z. The chalk tip touches a board plane
0.52 m in front of the origin at height 1.60 m (model local (0.13, 0.52, 1.60) Blender = Godot (0.13, 1.60, -0.52)).
To stand him at the Lab 7 chalkboard (slate face at Godot x = -2.978, slate z 0.25..1.85): place the GLB at
Godot (-2.458, 0, 0.95), rotation_degrees.y = +90 -> the chalk touches the slate at (-2.978, 1.60, 0.82) and his
left side stays clear of the lumen projector at (-2.3, 0, 1.6).
Material: one slot, M_Echo (replaced in Godot by the additive light-echo shader). Closed 2-manifold meshes.

Run: blender -b --factory-startup -P tools/blender/models/echo_strand_standing.py [-- --no-render] [-- --dev <dir>]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_echo as E  # noqa: E402
import mrlib  # noqa: E402
from lib_echo import ik2, rot_x, rot_z, vec  # noqa: E402

NAME = "echo_strand_standing"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
DEV = "--dev" in ARGS
HEAD_ONLY = "--head-only" in ARGS

BODY_TRIS, HEAD_TRIS = 5950, 2700
BOARD_Y, CHALK_TIP = 0.52, vec((0.13, 0.52, 1.60))

# ------------------------------------------------------------------ skeleton (Blender, metres)
# +X = his right, +Y = forward (toward the board), +Z = up. Male, ~1.76 m upright, stooped to ~1.67.
HIP = {1: vec((0.088, -0.03, 0.915)), -1: vec((-0.09, -0.028, 0.905))}
KNEE = {1: vec((0.098, -0.01, 0.50)), -1: vec((-0.112, 0.055, 0.495))}
ANKLE = {1: vec((0.108, -0.02, 0.085)), -1: vec((-0.125, 0.04, 0.085))}
SHOULDER = {1: vec((0.168, 0.062, 1.388)), -1: vec((-0.168, 0.05, 1.378))}
ELBOW_POLE = {1: vec((0.62, -0.05, 1.05)), -1: vec((-0.5, -0.35, 1.0))}
UPPER_ARM, FOREARM = 0.31, 0.265
PIVOT = vec((0.0, 0.088, 1.47))           # neck pivot (echo_head origin)
NECK_TILT, HEAD_PITCH, HEAD_YAW = 30.0, 9.0, -7.0
WRIST = {1: vec((0.15, 0.37, 1.50)), -1: vec((-0.215, 0.115, 0.835))}


def elbow(s):
    return ik2(SHOULDER[s], WRIST[s], UPPER_ARM, FOREARM, ELBOW_POLE[s])


def torso():
    rings = [  # (centre_y, z, rx, ry_front, ry_back) - outer surface of the long coat, stooped upper back
        (-0.012, 0.86, 0.178, 0.122, 0.122),
        (-0.004, 0.95, 0.172, 0.128, 0.118),
        (0.008, 1.05, 0.166, 0.134, 0.112),
        (0.018, 1.15, 0.168, 0.128, 0.114),
        (0.028, 1.25, 0.178, 0.12, 0.122),
        (0.040, 1.32, 0.186, 0.11, 0.128),
        (0.054, 1.375, 0.18, 0.098, 0.118),
        (0.066, 1.415, 0.15, 0.08, 0.094),
        (0.076, 1.445, 0.096, 0.062, 0.068),
        (0.084, 1.47, 0.064, 0.054, 0.055),
    ]
    return E.loft("torso", [(0, y, z) for (y, z, *_r) in rings], [r for (_y, _z, *r) in rings],
                  side=(1, 0, 0), seg=32, sub=4, cap0=0.2, cap1=0.3)


def coat_skirt():
    """Long coat below the waist: a bell to mid-calf (z 0.34), following the forward left knee."""
    rings = [  # (centre_x, centre_y, z, rx, ry_front, ry_back)
        (0.0, -0.006, 0.99, 0.17, 0.128, 0.116),
        (0.0, 0.0, 0.86, 0.182, 0.132, 0.126),
        (-0.004, 0.008, 0.72, 0.192, 0.142, 0.134),
        (-0.008, 0.018, 0.56, 0.204, 0.152, 0.142),
        (-0.01, 0.024, 0.42, 0.214, 0.158, 0.148),
        (-0.01, 0.026, 0.345, 0.218, 0.16, 0.15),
    ]
    return E.loft("skirt", [(x, y, z) for (x, y, z, *_r) in rings], [r for (_x, _y, _z, *r) in rings],
                  side=(1, 0, 0), seg=36, sub=3, cap0=0.06, cap1=0.25)


def coat_details(tree):
    parts = [E.collar_band("collar", (0, 0.084, 1.452), 0.066, list(range(45, 320, 15)), height=0.024, width=0.042,
                           back_lift=0.014)]
    for sx in (1, -1):
        parts.append(E.surface_slab(
            f"lapel{sx}", tree,
            [(sx * 0.055, 0.15, 1.45), (sx * 0.075, 0.172, 1.39), (sx * 0.07, 0.178, 1.32), (sx * 0.045, 0.165, 1.24),
             (sx * 0.012, 0.15, 1.17)],
            [0.05, 0.068, 0.06, 0.036, 0.006], thick=0.0045, side_sign=sx))
        parts.append(E.surface_slab(f"pocket{sx}", tree, [(sx * 0.12, 0.11, 0.96), (sx * 0.12, 0.12, 0.86)], [0.13, 0.14],
                                    thick=0.0045))
    parts.append(E.surface_slab("breastpocket", tree, [(-0.095, 0.155, 1.31), (-0.095, 0.15, 1.25)], [0.1, 0.1], thick=0.004))
    for i, z in enumerate((1.14, 1.04, 0.94)):   # coat buttons on the right front edge
        p = E.hug(tree, [(0.018, 0.2, z)], 0.003)[0]
        parts.append(E.ellipsoid(f"button{i}", p, (0.009, 0.006, 0.009), seg=10, rings=6))
    return parts


def arms():
    parts = []
    for s in (1, -1):
        sh, el, wr = SHOULDER[s], elbow(s), WRIST[s]
        fdir = (wr - el).normalized()
        cuff = wr - fdir * 0.035
        parts.append(E.ellipsoid(f"deltoid{s}", sh + Vector((s * 0.006, 0.0, 0.004)), (0.058, 0.062, 0.058), seg=20, rings=12))
        parts.append(E.limb(f"upperarm{s}", sh, el, [0.058, 0.056, 0.053, 0.05], seg=20, side=(0, 0, 1)))
        parts.append(E.ellipsoid(f"elbow{s}", el, (0.05, 0.05, 0.05), seg=18, rings=10))
        parts.append(E.limb(f"forearm{s}", el, cuff, [0.05, 0.05, 0.048, 0.047, 0.052, 0.052],
                            ts=[0, 0.3, 0.65, 0.84, 0.88, 1.0], seg=20, side=(0, 0, 1), cap1=0.2))
        parts.append(E.limb(f"wrist{s}", cuff - fdir * 0.03, wr, [(0.028, 0.021), (0.027, 0.02)], seg=14, side=(0, 0, 1)))
    return parts


def hands():
    parts = []
    # right hand: chalk held between thumb and index/middle, palm facing left-down, pointing at the board
    wr = WRIST[1]
    fdir = (CHALK_TIP - wr).normalized()
    F = (fdir + Vector((0.0, 0.0, -0.15))).normalized()
    objs, info = E.hand("handR", wr, F, (-0.75, 0.0, -0.6), (0.1, 0.05, 1.0),
                        curls=[(24, 30, 16), (40, 46, 26), (62, 66, 34), (72, 70, 38)],
                        spread=[2, 0, -3, -7], pinch=True, scale=1.08)
    it, tt = info["tips"][0], info["thumb_tip"]
    grip = (it + tt) * 0.5
    cdir = (CHALK_TIP - grip).normalized()
    chalk = (grip - cdir * 0.014, CHALK_TIP)
    parts += objs
    # left hand: hanging relaxed beside the coat, fingers loosely curled
    objs, _info = E.hand("handL", WRIST[-1], (-0.05, 0.22, -1.0), (0.95, 0.15, 0.1), (0.05, 1.0, 0.1),
                         curls=[(22, 28, 14), (26, 32, 16), (30, 36, 18), (34, 40, 20)], spread=[3, 0, -3, -7], scale=1.08)
    parts += objs
    return parts, chalk, grip


def legs():
    parts = []
    for s in (1, -1):
        kn, an = KNEE[s], ANKLE[s]
        # trouser legs (visible below the coat hem), slightly loose
        parts.append(E.limb(f"shin{s}", kn + Vector((0, 0, 0.06)), an + Vector((0, 0, 0.02)),
                            [(0.06, 0.06, 0.062, 0.058), (0.058, 0.058, 0.064, 0.055), (0.054, 0.054, 0.056, 0.052),
                             (0.052, 0.052, 0.053, 0.052)], ts=[0, 0.3, 0.7, 1.0], side=(1, 0, 0), seg=18))
        f = Vector((s * 0.16, 1.0, 0.0)).normalized()
        base = Vector((an.x, an.y, 0.0))
        sec = [(-0.065, 0.032, 0.026, 0.032), (-0.04, 0.042, 0.042, 0.038), (0.012, 0.044, 0.038, 0.042),
               (0.08, 0.032, 0.028, 0.046), (0.14, 0.024, 0.02, 0.044), (0.19, 0.018, 0.014, 0.034)]
        pts = [base + f * d + Vector((0, 0, cz)) for (d, cz, _t, _w) in sec]
        rads = [(top, cz, w, w, 2.6) for (_d, cz, top, w) in sec]
        parts.append(E.loft(f"shoe{s}", pts, rads, side=(0, 0, 1), seg=20, sub=3, cap0=0.6, cap1=0.7))
    return parts


def build_body():
    t = torso()
    tree = E.bvh(t)
    parts = [t, coat_skirt()] + coat_details(tree) + arms() + legs()
    hp, chalk, grip = hands()
    parts += hp
    body = E.union_remesh(parts, "body_tmp", 0.0036)
    hand_c = [WRIST[1] + (grip - WRIST[1]) * 0.6, WRIST[-1] + Vector((0.0, 0.02, -0.06))]

    def hands_w(co):
        w = np.zeros(len(co))
        for c in hand_c:
            d2 = ((co - np.array(c)) ** 2).sum(1)
            w = np.maximum(w, np.exp(-d2 / (2 * 0.06 ** 2)))
        return w

    def not_hands(co):
        return 1.0 - hands_w(co)

    E.taubin(body, 4)
    E.fill_concave(body, 14, region=not_hands)
    E.fill_concave(body, 3, lam=0.4, region=hands_w)
    folds = []
    for s in (1, -1):
        el, sh, wr = elbow(s), SHOULDER[s], WRIST[s]
        inner = (sh - el).normalized() + (wr - el).normalized()
        folds += [dict(c=el + inner.normalized() * 0.04, s=0.018, a=-0.006),
                  dict(c=el + inner.normalized() * 0.03 + (wr - el).normalized() * 0.035, s=0.013, a=0.003),
                  dict(c=sh + (el - sh) * 0.55, s=(0.022, 0.022, 0.022), a=0.0015)]
    folds += [
        dict(c=(0.0, 0.17, 0.62), s=(0.012, 0.03, 0.3), a=-0.008, face=(0, 1, 0)),     # coat opening (front split)
        dict(c=(0.0, 0.18, 0.4), s=(0.022, 0.03, 0.06), a=-0.01, face=(0, 1, 0)),      # split widens at the hem
        dict(c=(0.0, -0.15, 0.5), s=(0.008, 0.03, 0.15), a=-0.005, face=(0, -1, 0)),   # back vent
        dict(c=(0.0, 0.1, 1.08), s=(0.14, 0.03, 0.02), a=-0.004, face=(0, 1, 0)),      # belt-line crease
        dict(c=(0.0, -0.1, 1.33), s=(0.1, 0.05, 0.06), a=0.004, face=(0, -1, 0)),      # rounded old back
        dict(c=(-0.13, 0.02, 0.62), s=(0.03, 0.12, 0.2), a=-0.004),                    # drape fold over the left leg
        dict(c=(0.15, -0.04, 0.6), s=(0.03, 0.1, 0.18), a=-0.003),
    ]
    E.sculpt(body, folds)
    E.decimate(body, BODY_TRIS, vgroup_weights=hands_w, vg_factor=0.002)
    chalk_obj = E.limb("chalk", chalk[0], chalk[1], [0.0052, 0.0055, 0.0055, 0.005], ts=[0, 0.1, 0.85, 1], seg=8,
                       side=(0, 0, 1), cap0=0.4, cap1=0.25)
    body = mrlib.join([body, chalk_obj], "echo_body")
    E.clean_mesh(body)
    return body


# ------------------------------------------------------------------ head
P_HEAD = dict(E.MALE, nose=1.1, brow=2.0)


def hair_disp(co, nrm):
    """Receding grey fringe (horseshoe round the back of the head) + short trimmed beard and moustache."""
    s = P_HEAD["scale"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    lower = np.interp(deg, [0, 70, 85, 100, 140, 180], [0.3, 0.3, 0.004, -0.02, -0.06, -0.072]) * s
    upper = np.interp(deg, [0, 70, 85, 110, 150, 180], [-0.3, -0.3, 0.05, 0.072, 0.086, 0.09]) * s
    m = E.smoothstep(lower - 0.002, lower + 0.008, z) * (1.0 - E.smoothstep(upper - 0.014, upper + 0.004, z))
    fringe = np.interp(deg, [80, 120, 180], [0.006, 0.0085, 0.0095]) * m
    # short full beard: chin below the lower lip + jaw sides up to the sideburns, feathered edges
    chin = E.smoothstep(-0.03 * s, 0.035 * s, y) * E.smoothstep(-0.07 * s, -0.084 * s, z)
    sides = (E.smoothstep(0.042 * s, 0.062 * s, ax) * E.smoothstep(0.012 * s, -0.03 * s, z)
             * E.smoothstep(-0.028 * s, 0.0, y))
    beard = np.clip(chin + 0.75 * sides, 0, 1) * E.smoothstep(-0.16 * s, -0.12 * s, z)
    beard_d = (0.0055 + 0.0035 * E.smoothstep(-0.09 * s, -0.11 * s, z)) * beard
    # moustache over the upper lip, out to the mouth corners
    mous = (E.smoothstep(-0.07 * s, -0.064 * s, z) * (1 - E.smoothstep(-0.056 * s, -0.051 * s, z))
            * E.smoothstep(0.066 * s, 0.08 * s, y) * (1 - E.smoothstep(0.026 * s, 0.036 * s, ax)))
    d = np.maximum(fringe, beard_d) + 0.0045 * mous
    return nrm * d[:, None]


def head_matrix():
    Rh = rot_z(HEAD_YAW) @ rot_x(HEAD_PITCH)
    s = P_HEAD["scale"]
    atlas_local = vec((0, -0.012 * s, -0.05 * s))
    nd = vec((0, math.sin(math.radians(NECK_TILT)), math.cos(math.radians(NECK_TILT))))
    atlas = PIVOT + nd * 0.098
    return Matrix.Translation(atlas - Rh @ atlas_local) @ Rh.to_4x4(), atlas_local, nd


def build_head(no_decimate=False):
    Pp = P_HEAD
    Mh, atlas_local, nd = head_matrix()
    Mi = Mh.inverted()
    parts = E.face_parts("h", Pp)
    nb = Mi @ (PIVOT - nd * 0.045)
    nm = Mi @ (PIVOT + nd * 0.05)
    nt = atlas_local + Vector((0, 0.014, 0.03))
    parts.append(E.loft("h_neck", [nb, nm, nt], [(0.058, 0.06), (0.054, 0.056), (0.054, 0.054)],
                        side=(1, 0, 0), seg=24, sub=3, cap0=0.3, cap1=0.6))
    head = E.union_remesh(parts, "head_tmp", 0.0016)
    E.taubin(head, 4)
    E.fill_concave(head, 10)
    E.displace_fn(head, hair_disp)
    E.taubin(head, 2)
    extra = E.ear_parts("h", Pp)
    head = E.union_remesh([head] + extra, "head_tmp2", 0.0016)
    E.taubin(head, 3)
    E.fill_concave(head, 6)
    s = Pp["scale"]
    kern = E.face_kernels(Pp) + [
        dict(c=(sx * 0.03 * s, 0.083 * s, -0.035 * s), s=(0.01 * s, 0.01 * s, 0.022 * s), a=-0.0012 * s, face=(0, 1, 0))
        for sx in (1, -1)] + [                                                   # nasolabial folds
        dict(c=(sx * 0.036 * s, 0.084 * s, -0.012 * s), s=(0.012 * s, 0.01 * s, 0.004 * s), a=-0.001 * s, face=(0, 1, 0))
        for sx in (1, -1)] + [                                                   # under-eye bags
        dict(c=(0, 0.075 * s, 0.05 * s), s=(0.04 * s, 0.02 * s, 0.003 * s), a=-0.0007 * s, face=(0, 1, 0)),  # forehead line
    ]
    E.sculpt(head, kern)
    if no_decimate:
        return head, Mh
    # plain quadric collapse: the weighted variant (lib_echo vgroup protection) starves the cranium at this ratio
    # and collapses it into a cone; curvature alone keeps the face features
    E.decimate(head, HEAD_TRIS)
    E.clean_mesh(head)
    head.data.transform(Mh)
    mrlib.set_origin(head, PIVOT)
    return head


def main():
    mrlib.reset_scene()
    if HEAD_ONLY:
        head = build_head()
        head.name = "echo_head"
        E.finish_echo(head)
        print("[echo] head", E.mesh_report(head))
        d = ARGS[ARGS.index("--dev") + 1] if DEV else os.path.join(mrlib.ROOT, "qa", "blender")
        mrlib.QA_DIR = d
        c = PIVOT + Vector((0, 0.06, 0.13))
        E.echo_render("dev_strand_head", c + Vector((0.12, 0.55, 0.05)), c, lens=60, res=(700, 700), samples=24)
        E.echo_render("dev_strand_head_side", c + Vector((0.55, 0.08, 0.04)), c, lens=60, res=(700, 700), samples=24)
        E.echo_render("dev_strand_head_back", c + Vector((-0.35, -0.45, 0.12)), c, lens=60, res=(700, 700), samples=24)
        return
    body = build_body()
    head = build_head()
    for o, n in ((body, "echo_body"), (head, "echo_head")):
        o.name = n
        o.data.name = n
        E.finish_echo(o)
    mrlib.set_parent(head, body)
    for o in (body, head):
        print("[echo]", o.name, E.mesh_report(o))
    print("[echo] total tris", mrlib.tri_count())
    print("[echo] elbows", {s: tuple(round(c, 3) for c in elbow(s)) for s in (1, -1)})
    mrlib.export_glb(NAME)
    if not RENDER:
        return
    E.qa_proxy_box("board", (1.6, 0.03, 1.0), (0.1, BOARD_Y + 0.015, 1.5))
    E.qa_proxy_box("floor", (1.6, 1.6, 0.01), (0.0, 0.1, -0.005), color="15171A")
    if DEV:
        mrlib.QA_DIR = ARGS[ARGS.index("--dev") + 1]
        E.echo_render("dev_front", (0.1, 2.4, 1.1), (0.0, 0.1, 0.95), lens=40, res=(700, 900), samples=24)
        E.echo_render("dev_hand", (0.55, 0.15, 1.75), (0.13, 0.42, 1.55), lens=50, res=(800, 600), samples=24)
        mrlib.QA_DIR = os.path.join(mrlib.ROOT, "qa", "blender")
    # 3/4 from behind his right shoulder (the player's view of a figure writing at the board)
    E.echo_render(NAME, (1.35, -1.25, 1.5), (0.0, 0.15, 0.95), lens=40)
    E.echo_render(NAME + "_2", (2.4, 0.3, 1.0), (0.0, 0.18, 0.88), lens=42)
    head.rotation_euler = (math.radians(4), 0, math.radians(55))
    E.ghost_render(NAME + "_3", [body, head], (-1.3, -1.6, 1.45), (0.0, 0.15, 0.95), lens=42)


if __name__ == "__main__":
    main()
