"""Light echo: Dr. Leyla Rahimova, 1979, seated at her desk writing (Chapter 1 finale).

Output: game/assets/models/echo_leyla_sitting.glb
  echo_body  origin = floor below the seat centre (0, 0, 0). Seat top 0.46 m (no chair in the mesh).
  echo_head  head + neck + hair + bun, child of echo_body, origin = neck pivot (base of the neck,
             inside the coat collar). Rotate it about its local vertical axis (Godot +Y) to turn
             her head toward the player; negative yaw turns her to her right (Godot +X).
Facing: the desk is in front of her = Blender +Y = Godot -Z. Desk top 0.78 m; desk front edge
assumed 0.39 m in front of the seat centre (chair/desk placement in ROOM_LAYOUT.md).
Material: one slot, M_Echo (replaced in Godot by the additive light-echo shader).

Run: blender -b --factory-startup -P tools/blender/models/echo_leyla_sitting.py [-- --no-render]
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

NAME = "echo_leyla_sitting"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
DEV = "--dev" in ARGS  # extra close-up renders into the scratch dir given after --dev

SEAT, DESK, DESK_EDGE_Y = 0.46, 0.78, 0.39
BODY_TRIS, HEAD_TRIS = 6150, 2650
HEAD_VG, BODY_VG = 0.002, 0.002  # decimation detail bias (cost += edge_len * factor)

# ------------------------------------------------------------------ skeleton (Blender, metres)
# +X = her right, +Y = forward (toward the desk), +Z = up. Female, 1.65 m standing.
HIP = {1: vec((0.085, -0.032, 0.556)), -1: vec((-0.085, -0.032, 0.556))}
KNEE = {1: vec((0.082, 0.345, 0.488)), -1: vec((-0.077, 0.334, 0.488))}
ANKLE = {1: vec((0.095, 0.405, 0.086)), -1: vec((-0.087, 0.305, 0.086))}
SHOULDER = {1: vec((0.158, 0.104, 0.986)), -1: vec((-0.156, 0.094, 0.990))}
WRIST = {1: vec((0.118, 0.556, 0.826)), -1: vec((-0.170, 0.548, 0.814))}
ELBOW_POLE = {1: vec((0.60, 0.10, 0.55)), -1: vec((-0.60, 0.10, 0.55))}
UPPER_ARM, FOREARM = 0.300, 0.236
PIVOT = vec((0.0, 0.118, 1.060))          # neck pivot (echo_head origin)
NECK_TILT, HEAD_PITCH, HEAD_YAW = 20.0, -16.0, -8.0

ELBOW = {s: ik2(SHOULDER[s], WRIST[s], UPPER_ARM, FOREARM, ELBOW_POLE[s]) for s in (1, -1)}


def torso():
    rings = [  # (centre_y, z, rx, ry_front, ry_back) - outer surface of the lab coat
        (-0.050, 0.468, 0.156, 0.096, 0.094),
        (-0.048, 0.512, 0.184, 0.108, 0.118),
        (-0.040, 0.585, 0.178, 0.103, 0.108),
        (-0.022, 0.680, 0.146, 0.090, 0.090),
        (0.004, 0.770, 0.146, 0.096, 0.088),
        (0.038, 0.850, 0.157, 0.110, 0.088),
        (0.068, 0.918, 0.163, 0.110, 0.086),
        (0.094, 0.970, 0.166, 0.094, 0.082),
        (0.108, 1.008, 0.146, 0.076, 0.074),
        (0.116, 1.036, 0.104, 0.060, 0.062),
        (0.120, 1.060, 0.060, 0.048, 0.050),
    ]
    return E.loft("torso", [(0, y, z) for (y, z, *_r) in rings], [r for (_y, _z, *r) in rings],
                  side=(1, 0, 0), seg=32, sub=4, cap0=0.25, cap1=0.3)


def coat_details(tree):
    parts = [E.collar_band("collar", (0, 0.112, 1.040), 0.060, list(range(50, 315, 15)),
                           height=0.020, width=0.036, back_lift=0.010)]
    for sx in (1, -1):
        parts.append(E.surface_slab(
            f"lapel{sx}", tree,
            [(sx * 0.050, 0.165, 1.050), (sx * 0.066, 0.188, 0.995), (sx * 0.058, 0.198, 0.935),
             (sx * 0.036, 0.185, 0.875), (sx * 0.011, 0.160, 0.828)],
            [0.044, 0.060, 0.052, 0.030, 0.004], thick=0.0042, side_sign=sx))
        # hip patch pockets (seated: on the side of the hips)
        parts.append(E.surface_slab(f"hippocket{sx}", tree,
                                    [(sx * 0.18, 0.02, 0.655), (sx * 0.18, 0.02, 0.575)],
                                    [0.12, 0.13], thick=0.004))
    parts.append(E.surface_slab("breastpocket", tree, [(-0.088, 0.19, 0.935), (-0.088, 0.17, 0.875)],
                                [0.095, 0.10], thick=0.004))
    return parts


def arms():
    parts = []
    for s in (1, -1):
        sh, el, wr = SHOULDER[s], ELBOW[s], WRIST[s]
        fdir = (wr - el).normalized()
        cuff = wr - fdir * 0.030
        parts.append(E.ellipsoid(f"deltoid{s}", sh + Vector((s * 0.004, 0.0, 0.006)),
                                 (0.050, 0.056, 0.052), seg=20, rings=12))
        parts.append(E.limb(f"upperarm{s}", sh, el, [0.052, 0.051, 0.048, 0.046], seg=20,
                            side=(0, 0, 1)))
        parts.append(E.ellipsoid(f"elbow{s}", el, (0.045, 0.045, 0.045), seg=18, rings=10))
        parts.append(E.limb(f"forearm{s}", el, cuff, [0.045, 0.045, 0.043, 0.041, 0.044, 0.044],
                            ts=[0, 0.3, 0.65, 0.84, 0.88, 1.0], seg=20, side=(0, 0, 1), cap1=0.2))
        parts.append(E.limb(f"wrist{s}", cuff - fdir * 0.03, wr, [(0.025, 0.019), (0.024, 0.018)],
                            seg=14, side=(0, 0, 1)))
    return parts


def hands():
    parts = []
    # right hand: writing grip, resting on its little-finger side, palm facing left/down
    wr = WRIST[1]
    fdir = (wr - ELBOW[1]).normalized()
    F = (fdir + Vector((-0.30, 0.05, -0.10))).normalized()
    objs, info = E.hand("handR", wr, F, (-1.0, 0.1, -0.75), (-0.45, 0.0, 1.0),
                        curls=[(30, 36, 20), (46, 50, 30), (64, 68, 36), (74, 70, 38)],
                        spread=[2, 0, -3, -8], pinch=True)
    parts += objs
    it, tt = info["tips"][0], info["thumb_tip"]
    Ff, Ss = info["F"], info["S"]
    grip = (it + tt) * 0.5
    web = wr + Ff * 0.052 + Ss * 0.032
    pdir = (web - grip).normalized()
    t = (grip.z - (DESK + 0.001)) / max(1e-4, pdir.z)
    tip = grip - pdir * t
    pen = (tip, tip + pdir * 0.140)
    # left hand: resting flat on the desk, palm down, thumb toward her midline (+X)
    objs, _info = E.hand("handL", WRIST[-1], (0.26, 0.96, -0.12), (0, 0, -1), (1, -0.27, 0),
                         curls=[(10, 16, 10), (12, 18, 10), (14, 20, 12), (18, 22, 12)],
                         spread=[-6, -1, 3, 8])
    parts += objs
    return parts, pen


def legs():
    parts = []
    for s in (1, -1):
        hp, kn, an = HIP[s], KNEE[s], ANKLE[s]
        parts.append(E.limb(f"thigh{s}", hp, kn, [(0.086, 0.078), (0.078, 0.070), (0.064, 0.056),
                                                  (0.052, 0.048)], side=(1, 0, 0), seg=20))
        parts.append(E.ellipsoid(f"knee{s}", kn + Vector((0, 0.010, 0.004)), (0.048, 0.052, 0.048),
                                 seg=18, rings=10))
        # shin: for a downward limb the ring Y axis points back -> (rx, rx, calf, shin-front)
        parts.append(E.limb(f"shin{s}", kn, an,
                            [(0.046, 0.046, 0.048, 0.043), (0.047, 0.047, 0.058, 0.039),
                             (0.040, 0.040, 0.046, 0.033), (0.030, 0.030, 0.032, 0.027),
                             (0.028, 0.028, 0.030, 0.026)],
                            ts=[0, 0.25, 0.55, 0.85, 1.0], side=(1, 0, 0), seg=18))
        # flat shoe along the foot (ring X = up, so the sole sits flat on the floor)
        f = Vector((s * 0.12, 1.0, 0.0)).normalized()
        base = Vector((an.x, an.y, 0.0))
        sec = [(-0.058, 0.030, 0.024, 0.028), (-0.036, 0.038, 0.038, 0.033), (0.012, 0.040, 0.034, 0.036),
               (0.072, 0.029, 0.025, 0.041), (0.122, 0.021, 0.018, 0.038), (0.158, 0.016, 0.012, 0.029)]
        pts = [base + f * d + Vector((0, 0, cz)) for (d, cz, _t, _w) in sec]
        rads = [(top, cz, w, w, 2.6) for (_d, cz, top, w) in sec]
        parts.append(E.loft(f"shoe{s}", pts, rads, side=(0, 0, 1), seg=20, sub=3, cap0=0.6, cap1=0.7))
    # dress over the lap: forward loft, ring Y axis = down -> (lat, lat, down, up)
    parts.append(E.loft("lap", [(0, -0.04, 0.566), (0, 0.10, 0.548), (0, 0.24, 0.526), (0, 0.312, 0.515)],
                        [(0.172, 0.172, 0.050, 0.070, 2.4), (0.166, 0.166, 0.050, 0.068, 2.4),
                         (0.148, 0.148, 0.048, 0.062, 2.4), (0.136, 0.136, 0.046, 0.056, 2.4)],
                        side=(1, 0, 0), seg=28, sub=3, cap0=0.3, cap1=0.25))
    # lab-coat skirt panels over each thigh (open at the centre) and side drapes off the seat
    for s in (1, -1):
        cx = s * 0.098
        o_in = [0.084, 0.080, 0.072, 0.068]
        o_out = [0.108, 0.104, 0.094, 0.088]
        ups = [0.082, 0.078, 0.072, 0.064]
        rads = []
        for i in range(4):
            a, b = (o_out[i], o_in[i]) if s > 0 else (o_in[i], o_out[i])
            rads.append((a, b, 0.046, ups[i], 2.6))
        parts.append(E.loft(f"coatpanel{s}", [(cx, -0.07, 0.575), (cx, 0.09, 0.558), (cx, 0.23, 0.534),
                                              (cx, 0.348, 0.512)],
                            rads, side=(1, 0, 0), seg=24, sub=3, cap0=0.3, cap1=0.12))
        parts.append(E.loft(f"drape{s}", [(s * 0.195, -0.11, 0.515), (s * 0.202, 0.02, 0.500),
                                          (s * 0.198, 0.15, 0.500), (s * 0.186, 0.27, 0.508)],
                            [(0.011, 0.011, 0.058, 0.050), (0.012, 0.012, 0.072, 0.056),
                             (0.012, 0.012, 0.068, 0.056), (0.011, 0.011, 0.046, 0.042)],
                            side=(1, 0, 0), seg=16, sub=3, cap0=0.5, cap1=0.5))
    return parts


def build_body():
    t = torso()
    tree = E.bvh(t)
    parts = [t] + coat_details(tree) + arms() + legs()
    hp, pen = hands()
    parts += hp
    body = E.union_remesh(parts, "body_tmp", 0.0034)
    hand_c = [WRIST[1] + Vector((-0.02, 0.05, -0.01)), WRIST[-1] + Vector((0.01, 0.06, -0.01))]

    def hands_w(co):
        w = np.zeros(len(co))
        for c in hand_c:
            d2 = ((co - np.array(c)) ** 2).sum(1)
            w = np.maximum(w, np.exp(-d2 / (2 * 0.055 ** 2)))
        return w

    def not_hands(co):
        return 1.0 - hands_w(co)

    E.taubin(body, 4)
    E.fill_concave(body, 14, region=not_hands)
    E.fill_concave(body, 3, lam=0.4, region=hands_w)
    folds = []
    for s in (1, -1):
        el, sh = ELBOW[s], SHOULDER[s]
        inner = (sh - el).normalized() + ((WRIST[s] - el).normalized())
        folds += [dict(c=el + inner.normalized() * 0.035, s=0.016, a=-0.005),
                  dict(c=el + inner.normalized() * 0.03 + (WRIST[s] - el).normalized() * 0.03,
                       s=0.012, a=0.003),
                  dict(c=sh + (el - sh) * 0.55, s=(0.02, 0.02, 0.02), a=0.0015)]
    folds += [dict(c=(0, 0.16, 0.57), s=(0.010, 0.22, 0.03), a=-0.005, face=(0, 0, 1)),   # coat opening
              dict(c=(0, 0.33, 0.535), s=(0.028, 0.03, 0.03), a=-0.007),                  # between knees
              dict(c=(0, 0.12, 0.70), s=(0.10, 0.03, 0.018), a=-0.003, face=(0, 1, 0))]    # waist crease
    E.sculpt(body, folds)
    E.decimate(body, BODY_TRIS, vgroup_weights=hands_w, vg_factor=BODY_VG)
    pen_obj = E.limb("pen", pen[0], pen[1], [0.0026, 0.0040, 0.0044, 0.0040], ts=[0, 0.12, 0.6, 1],
                     seg=8, side=(0, 0, 1), cap0=0.3, cap1=0.5)
    body = mrlib.join([body, pen_obj], "echo_body")
    E.clean_mesh(body)
    return body


def hair_disp(co, nrm):
    """Swept-back 1970s hair: volume over the skull, soft hairline, strands converging on the bun."""
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


def head_matrix():
    Rh = rot_z(HEAD_YAW) @ rot_x(HEAD_PITCH)
    atlas_local = vec((0, -0.012, -0.048))
    nd = vec((0, math.sin(math.radians(NECK_TILT)), math.cos(math.radians(NECK_TILT))))
    atlas = PIVOT + nd * 0.092
    return Matrix.Translation(atlas - Rh @ atlas_local) @ Rh.to_4x4(), atlas_local, nd


def build_head(no_decimate=False):
    P = E.FEMALE
    Mh, atlas_local, nd = head_matrix()
    Mi = Mh.inverted()
    parts = E.face_parts("h", P)
    nb = Mi @ (PIVOT - nd * 0.045)
    nm = Mi @ (PIVOT + nd * 0.05)
    nt = atlas_local + Vector((0, 0.012, 0.03))
    parts.append(E.loft("h_neck", [nb, nm, nt], [(0.052, 0.054), (0.048, 0.050), (0.050, 0.050)],
                        side=(1, 0, 0), seg=24, sub=3, cap0=0.3, cap1=0.6))
    head = E.union_remesh(parts, "head_tmp", 0.0016)
    E.taubin(head, 4)
    E.fill_concave(head, 10)
    E.displace_fn(head, hair_disp)
    E.taubin(head, 2)
    extra = E.ear_parts("h", P)
    bun_c = vec((0, -0.121, 0.006))
    extra.append(E.ellipsoid("h_bun", bun_c, (0.038, 0.030, 0.033), seg=24, rings=14))
    extra.append(E.torus_obj("h_bun_coil", bun_c + Vector((0, -0.006, 0)), 0.025, 0.0135,
                             rot=rot_x(90), seg=28, mseg=12))
    head = E.union_remesh([head] + extra, "head_tmp2", 0.0016)
    E.taubin(head, 3)
    E.fill_concave(head, 6)
    E.sculpt(head, E.face_kernels(P))
    if no_decimate:
        return head, Mh
    # plain quadric collapse: the vgroup-weighted variant starves the cranium in Blender 5.2 and collapses
    # the skull and bun into a cone (see echo_strand_standing.py); curvature keeps the face features
    E.decimate(head, HEAD_TRIS)
    E.clean_mesh(head)
    head.data.transform(Mh)
    mrlib.set_origin(head, PIVOT)
    return head


def main():
    mrlib.reset_scene()
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
    print("[echo] elbows", {s: tuple(round(c, 3) for c in ELBOW[s]) for s in ELBOW})
    mrlib.export_glb(NAME)
    if not RENDER:
        return
    E.qa_proxy_box("seat", (0.42, 0.42, 0.03), (0, 0.0, SEAT - 0.015))
    E.qa_proxy_box("desk", (1.5, 0.72, 0.03), (0.0, DESK_EDGE_Y + 0.36, DESK - 0.015))
    E.qa_proxy_box("notebook", (0.30, 0.21, 0.006), (0.0, 0.62, DESK + 0.003), color="34363A")
    if DEV:
        mrlib.QA_DIR = ARGS[ARGS.index("--dev") + 1]
        E.echo_render("dev_head", (0.35, 0.75, 1.25), (0.0, 0.16, 1.17), lens=60, res=(700, 700), samples=24)
        E.echo_render("dev_head_side", (0.75, 0.15, 1.22), (0.0, 0.14, 1.17), lens=60, res=(700, 700), samples=24)
        E.echo_render("dev_hands", (0.25, 1.05, 1.15), (0.0, 0.55, 0.80), lens=50, res=(800, 600), samples=24)
        E.echo_render("dev_front", (0.0, 1.9, 0.95), (0.0, 0.2, 0.78), lens=45, res=(700, 800), samples=24)
        mrlib.QA_DIR = os.path.join(mrlib.ROOT, "qa", "blender")
    E.echo_render(NAME, (1.25, 1.65, 1.30), (0.0, 0.22, 0.80), lens=40)
    E.echo_render(NAME + "_2", (2.4, 0.22, 0.92), (0.0, 0.20, 0.74), lens=45)
    head.rotation_euler = (math.radians(10), 0, math.radians(-75))
    E.ghost_render(NAME + "_3", [body, head], (1.55, -1.45, 1.45), (0.0, 0.14, 0.92), lens=45)


if __name__ == "__main__":
    main()
