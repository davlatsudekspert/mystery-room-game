"""Light echo: two scientists of the Institute, 1979, pausing between the stacks and the screen wall
(Chapter 2, optional "kept echoes"). A woman holds an archive box against her right hip; a man reads an open
ledger and tilts it toward her. They stand 0.7 m apart and half-turn to each other.

Output: game/assets/models/echo_scientists.glb (Godot axes below; both figures face roughly +Z)
  echo_body    both bodies (two closed shells: woman at model x = -0.35, man at x = +0.35), the archive box
               and the ledger. Origin = the floor midpoint between them.
  echo_head_a  the woman's head (1970s chin-length bob with a fringe), child of echo_body, origin = her neck
               pivot, identity rotation.
  echo_head_b  the man's head (side-parted 1970s hair, sideburns), child of echo_body, origin = his neck
               pivot, identity rotation.
Seen from the front, the woman is on the left and the man on the right. She is turned ~24 deg toward him
(hips 14, chest 24), he ~22 deg toward her (hips -12, chest -22); their heads turn further (to the ledger).
Placement (docs/models/ch2.md section 1): world (-0.8, 0, -1.7), yaw 50 (front toward the hall camera).
Material: one slot, M_Echo.

Run: blender -b --factory-startup -P tools/blender/models/echo_scientists.py [-- --no-render] [-- --dev <dir>]
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

NAME = "echo_scientists"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
DEV = ARGS[ARGS.index("--dev") + 1] if "--dev" in ARGS else None
BUDGET = 14000
TRIS = {"a": dict(body=4000, hand=520, head=1700), "b": dict(body=4000, hand=520, head=1650)}
VOXEL = 0.0035
PLACE, YAW = (-0.8, 0.0, -1.7), 50.0
HALF = 0.35                                   # each figure 0.35 m from the midpoint (0.7 m apart)


class Fig:
    """One standing figure built in its own local frame (origin between the feet, facing +Y, +X = its right),
    then moved into the group frame by `M` (translation along X + a base yaw)."""

    def __init__(self, key, x_build, base_yaw, spine, female):
        self.key = key
        self.M = Matrix.Translation((x_build, 0.0, 0.0)) @ Matrix.Rotation(math.radians(base_yaw), 4, "Z")
        self.sp = spine
        self.female = female

    def chest(self, x, y, z):
        return self.sp.point(z, (x, y, 0))

    def g(self, p):
        """Figure-local -> group build space."""
        return self.M @ vec(p)


def coat_common(fig, tree, collar_r, collar_c, lapel_pts, lapel_w, pockets, breast, buttons, button_x):
    col = E.collar_band(f"{fig.key}_collar", (0, 0, 0), collar_r, list(range(50, 315, 15)), height=0.020,
                        width=0.036 if fig.female else 0.040, back_lift=0.012)
    E.transform_obj(col, Matrix.Translation(collar_c) @ E.rot_z(fig.sp.yaw_chest).to_4x4() @ E.rot_x(-10).to_4x4())
    parts = [col]
    for sx in (1, -1):
        parts.append(E.surface_slab(f"{fig.key}_lapel{sx}", tree,
                                    [fig.chest(sx * x, 0.14, z) for (x, z) in lapel_pts],
                                    lapel_w, thick=0.0042, side_sign=sx))
        (px, pz0, pz1, pw) = pockets
        parts.append(E.surface_slab(f"{fig.key}_pocket{sx}", tree,
                                    [fig.chest(sx * px, 0.16, pz0), fig.chest(sx * px, 0.17, pz1)],
                                    [pw, pw + 0.01], thick=0.0042))
    (bx, bz0, bz1) = breast
    parts.append(E.surface_slab(f"{fig.key}_breast", tree, [fig.chest(bx, 0.15, bz0), fig.chest(bx, 0.15, bz1)],
                                [0.094, 0.098], thick=0.004))
    for i, z in enumerate(buttons):
        p = E.hug(tree, [fig.chest(button_x, 0.16, z)], 0.0036)[0]
        parts.append(E.ellipsoid(f"{fig.key}_button{i}", p, (0.009, 0.009, 0.009), seg=10, rings=6))
    return parts


def sleeves(fig, sh, el, wr, r):
    parts = []
    for s in (1, -1):
        sl, _cuff = L.sleeve(f"{fig.key}_arm{s}", sh[s], el[s], wr[s], r_sh=r[0], r_up=r[1], r_el=r[2],
                             r_fore=r[3], r_cuff=r[4], cuff_len=0.026, wrist_r=r[5], deltoid=r[6],
                             cuff_gap=0.026, start_back=0.006,
                             deltoid_off=fig.sp.right(1.33) * (0.006 * s) + Vector((0, 0, -0.010)))
        for p in sl:
            if p.name.endswith("_wrist"):
                bpy.data.objects.remove(p, do_unlink=True)
            else:
                parts.append(p)
    return parts


def wrist_stub(name, el, wr, r):
    fdir = (wr - el).normalized()
    return E.limb(name, wr - fdir * 0.05, wr + fdir * 0.004, [r, (r[0] * 0.97, r[1] * 0.97)], seg=14, side=(0, 0, 1))


def finish_figure(fig, parts, hands, folds, hand_tris, body_tris, flutes_fn=None):
    """Union + fold sculpt + decimate in the figure's local frame, then hands, then move to the group frame."""
    body = L.finish_body(parts, voxel=VOXEL, tris=body_tris, hand_centres=[h[1] for h in hands],
                         hand_sigma=0.04, folds_fn=folds, post_fn=flutes_fn, name=f"{fig.key}_body")
    print(f"[sci] {fig.key} body shell", E.mesh_report(body))
    shells = [L.hand_shell(hp, f"{fig.key}_hand{i}", hand_tris) for i, (hp, _c) in enumerate(hands)]
    body = L.bool_union(body, shells, f"{fig.key}_body")
    body.data.transform(fig.M)
    body.data.update()
    return body


# ====================================================================== the woman (a): archive box on her right hip
SP_A = L.Spine(hip_xy=(0.022, 0.0), neck_xy=(-0.012, 0.018), z_hip=0.86, z_neck=1.41, yaw_hip=0.0, yaw_chest=10.0,
               z_twist0=0.9, z_twist1=1.24)
A = Fig("a", HALF, 14.0, SP_A, True)
A_HIP = {1: vec((0.105, 0.0, 0.868)), -1: vec((-0.068, 0.0, 0.846))}
A_KNEE = {1: vec((0.092, 0.010, 0.476)), -1: vec((-0.080, 0.070, 0.462))}
A_ANKLE = {1: vec((0.080, -0.010, 0.082)), -1: vec((-0.105, 0.060, 0.082))}
A_FOOT_YAW = {1: -6.0, -1: 12.0}
A_SH = {1: A.chest(0.157, 0.0, 1.333), -1: A.chest(-0.156, 0.004, 1.340)}
# right arm over the box: elbow at its top-outer corner, forearm down its outer face, hand under the bottom edge
A_WR = {1: vec((0.355, 0.085, 0.852)), -1: A.chest(-0.150, 0.235, 0.985)}
A_POLE = {1: vec((0.6, -0.2, 1.2)), -1: vec((-0.6, -0.4, 0.8))}
A_EL = {s: E.ik2(A_SH[s], A_WR[s], 0.300, 0.236, A_POLE[s]) for s in (1, -1)}
A_BOX_C = vec((0.262, 0.035, 0.935))
A_PIVOT = A.chest(0.0, 0.004, 1.405)
A_ND = L.neck_dir(SP_A.yaw_chest + 4, 14.0, side_tilt=-5.0)
A_HEAD = (32.0, -12.0, -6.0)                    # yaw (to her left, toward him), pitch, roll


def woman_body():
    f = A
    rings = [
        (0.430, 0.212, 0.210, 0.150, 0.156, 2.25, 0.008, 0.020),
        (0.520, 0.206, 0.203, 0.146, 0.152, 2.2, 0.010, 0.016),
        (0.640, 0.200, 0.196, 0.138, 0.145, 2.15, 0.010, 0.010),
        (0.760, 0.196, 0.190, 0.128, 0.139, 2.1, 0.008, 0.004),
        (0.850, 0.192, 0.184, 0.121, 0.133, 2.1, 0.004, 0.0),
        (0.930, 0.176, 0.172, 0.110, 0.118, 2.05, 0.0, 0.0),
        (0.995, 0.153, 0.154, 0.099, 0.098, 2.0, 0.0, 0.0),
        (1.065, 0.153, 0.154, 0.106, 0.092, 2.0, 0.0, 0.0),
        (1.135, 0.161, 0.162, 0.119, 0.090, 2.0, 0.0, 0.0),
        (1.205, 0.168, 0.168, 0.124, 0.092, 2.0, 0.0, 0.0),
        (1.258, 0.173, 0.172, 0.113, 0.096, 2.0, 0.0, 0.0),
        (1.300, 0.176, 0.175, 0.099, 0.094, 2.0, 0.0, 0.0),
        (1.340, 0.173, 0.173, 0.088, 0.088, 2.05, 0.0, 0.0),
        (1.370, 0.157, 0.157, 0.078, 0.080, 2.0, 0.0, 0.0),
        (1.396, 0.118, 0.118, 0.066, 0.070, 2.0, 0.0, 0.0),
        (1.418, 0.063, 0.063, 0.051, 0.054, 2.0, 0.0, 0.0),
    ]
    coat = L.coat_loft("a_coat", SP_A, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(coat)
    parts = [coat] + coat_common(
        f, tree, 0.060, f.chest(0, 0, 1.392),
        [(0.050, 1.398), (0.068, 1.345), (0.064, 1.285), (0.040, 1.215), (0.004, 1.150)],
        [0.044, 0.060, 0.054, 0.032, 0.004], (0.112, 0.815, 0.705, 0.125), (-0.088, 1.235, 1.165),
        (1.140, 1.030, 0.920, 0.810), -0.004)
    # pussy-bow of the blouse in the V of the coat
    bow = E.hug(tree, [f.chest(0.0, 0.14, 1.205)], 0.008)[0]
    for sx in (1, -1):
        parts.append(E.ellipsoid(f"a_bow{sx}", bow + SP_A.right(1.2) * (sx * 0.013), (0.013, 0.008, 0.009),
                                 rot=E.rot_z(SP_A.yaw_chest) @ E.rot_y(sx * 18), seg=12, rings=8))
        tail0 = bow + SP_A.right(1.2) * (sx * 0.004) + SP_A.front(1.2) * 0.002
        tail1 = bow + SP_A.right(1.2) * (sx * 0.011) + Vector((0, 0, -0.045))
        parts.append(E.limb(f"a_bowtail{sx}", tail0, E.hug(tree, [tail1], 0.004)[0],
                            [(0.0065, 0.003), (0.0085, 0.0028)], side=tuple(SP_A.right(1.2)), seg=10))
    parts.append(E.ellipsoid("a_bowknot", bow, (0.0075, 0.0065, 0.0075), seg=10, rings=6))
    parts += sleeves(f, A_SH, A_EL, A_WR, (0.050, 0.047, 0.044, 0.041, 0.044, (0.0235, 0.0175), (0.044, 0.049, 0.045)))
    for s in (1, -1):
        parts += L.lower_leg(f"a_leg{s}", A_KNEE[s], A_ANKLE[s], calf=0.058, shin=0.043, knee_r=0.047, ankle_r=0.025)
        parts += L.shoe(f"a_shoe{s}", A_ANKLE[s], A_FOOT_YAW[s], heel=0.026, scale=0.93, toe=0.95)
    # the archive box against her right hip (lid up, long side along her front-back)
    rot = E.rot_z(4.0)
    box = L.rounded_box("a_box", (0.12, 0.34, 0.225), A_BOX_C + rot @ Vector((0, 0, -0.018)), rot, bevel=0.006)
    lid = L.rounded_box("a_lid", (0.128, 0.348, 0.050), A_BOX_C + rot @ Vector((0, 0, 0.098)), rot, bevel=0.005)
    label = L.rounded_box("a_label", (0.075, 0.005, 0.040), A_BOX_C + rot @ Vector((0, 0.172, -0.035)), rot,
                          bevel=0.0015, segments=1)
    parts += [box, lid, label]
    hands = [(woman_hand_right(), A_WR[1]), (woman_hand_left(), A_WR[-1])]
    return finish_figure(f, parts, hands, woman_folds, TRIS["a"]["hand"], TRIS["a"]["body"], woman_flutes)


def woman_hand_right():
    """Hand cupped under the box's front-outer bottom edge, palm up/inward, fingers curled under."""
    F = vec((-0.30, 0.25, -0.92)).normalized()
    N = L.ortho((-1.0, 0.1, 0.25), F)
    T = L.ortho(F.cross(N), F)                         # right hand: thumb side = F x N
    objs, _info = L.hand2("a_handR", A_WR[1], F, N, T,
                          curls=[(48, 58, 30), (52, 60, 32), (56, 62, 32), (60, 62, 30)],
                          spread=[3, 0, -3, -6], scale=0.95, width=0.076, finger_r=0.0082)
    return [wrist_stub("a_wristR", A_EL[1], A_WR[1], (0.0235, 0.0175))] + objs


def woman_hand_left():
    """Conversational open hand, palm up, toward him."""
    F = (A_WR[-1] - A_EL[-1]).normalized()
    F = (F + Vector((0.20, 0.10, 0.10))).normalized()
    N, T = L.arm_hand_frame(F, -70.0, right=False)        # supinated: palm up
    objs, _info = L.hand2("a_handL", A_WR[-1], F, N, T,
                          curls=[(10, 16, 8), (14, 20, 10), (20, 26, 12), (26, 32, 14)],
                          spread=[6, 1, -4, -10], scale=0.95, width=0.076, finger_r=0.0082)
    return [wrist_stub("a_wristL", A_EL[-1], A_WR[-1], (0.0235, 0.0175))] + objs


def woman_folds():
    f, sp = A, SP_A
    k = []
    for s in (1, -1):
        el, sh, wr = A_EL[s], A_SH[s], A_WR[s]
        inner = (sh - el).normalized() + (wr - el).normalized()
        if inner.length > 0.2:
            k += [dict(c=el + inner.normalized() * 0.034, s=0.014, a=-0.0045),
                  dict(c=el + inner.normalized() * 0.026 + (wr - el).normalized() * 0.03, s=0.011, a=0.0025)]
    k += L.groove([f.chest(-0.020, 0.15, 1.15), f.chest(-0.022, 0.15, 0.80)], 0.005, -0.0026, face=sp.front(1.0))
    k += L.groove([vec((-0.022, 0.2, 0.78)), vec((-0.018, 0.22, 0.60)), vec((-0.010, 0.26, 0.43))], 0.009, -0.007,
                  face=(0, 1, 0))
    # box pressing the coat at the hip; drag folds from the box toward the opposite waist
    k += L.groove([vec((0.17, 0.06, 0.98)), vec((0.06, 0.12, 1.02))], 0.010, -0.003)
    k += L.groove([vec((0.17, 0.0, 0.84)), vec((0.08, 0.12, 0.90))], 0.010, -0.0025)
    # weight-leg drape and relaxed-knee push (left knee forward)
    k += L.groove([vec((0.15, 0.08, 0.80)), vec((0.165, 0.10, 0.44))], 0.012, -0.0035)
    k += L.groove([vec((-0.09, 0.13, 0.66)), vec((-0.095, 0.17, 0.46))], 0.014, 0.003)
    k += L.groove([vec((-0.16, 0.06, 0.80)), vec((-0.18, 0.05, 0.45))], 0.011, -0.003)
    k += L.groove([vec((0.0, -0.16, 0.62)), vec((0.0, -0.16, 0.43))], 0.004, -0.004, face=(0, -1, 0))
    for sx in (1, -1):
        k.append(dict(c=f.chest(sx * 0.15, 0.0, 1.0), s=(0.012, 0.05, 0.008), a=-0.0016, face=sp.right(1.0) * sx))
    # archive box: hand hole in its front end above the label
    rot = E.rot_z(4.0)
    k.append(dict(c=A_BOX_C + rot @ Vector((0, 0.17, 0.035)), s=(0.028, 0.012, 0.008), rot=rot, a=-0.005,
                  face=rot @ Vector((0, 1, 0))))
    return k


def woman_flutes(body):
    def amp(co, t):
        return 0.0065 * E.smoothstep(0.70, 0.44, co[:, 2]) * (0.65 + 0.35 * np.sin(co[:, 0] * 23.0 + co[:, 1] * 17.0))
    L.flutes(body, (0.008, 0.012, 0.0), (0, 0, 1), 9, amp, phase=0.4,
             region=lambda co: E.smoothstep(0.69, 0.60, co[:, 2]) * (co[:, 2] > 0.40) * (co[:, 0] < 0.17))


def hair_bob(co, nrm):
    """1970s chin-length bob: side-parted fringe, full sides covering the ears, ends turned under at the jaw."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    hl = np.interp(deg, [0, 25, 50, 70, 90, 180], [0.030, 0.034, 0.030, -0.060, -0.112, -0.112])
    m = E.smoothstep(hl - 0.004, hl + 0.006, z)
    side = E.smoothstep(55, 85, deg)
    thick = 0.016 + 0.016 * E.smoothstep(0.06, -0.07, z) * side + 0.008 * E.smoothstep(0.02, 0.10, z)
    # ends: turned under (thicker just above the cut line), cut at the jaw
    cut = 1.0 - E.smoothstep(-0.112, -0.122, z)
    thick = thick * cut + 0.005 * np.exp(-((z + 0.100) / 0.012) ** 2) * side
    psi = np.arctan2(z - 0.02, x)
    g = 1.0 - 0.18 * (0.5 - 0.5 * np.cos(26 * psi)) * E.smoothstep(-0.02, 0.04, y)
    return nrm * (thick * m * g)[:, None]


def woman_head():
    return L.build_head(E.FEMALE, A_PIVOT, A_ND, *A_HEAD, hair_bob, TRIS["a"]["head"], voxel=0.0018)


# ====================================================================== the man (b): reading an open ledger
SP_B = L.Spine(hip_xy=(-0.010, 0.0), neck_xy=(-0.004, 0.050), z_hip=0.93, z_neck=1.50, yaw_hip=0.0, yaw_chest=-10.0,
               z_twist0=0.97, z_twist1=1.33)
B = Fig("b", -HALF, -12.0, SP_B, False)
B_HIP = {1: vec((0.092, 0.0, 0.915)), -1: vec((-0.090, 0.0, 0.930))}
B_KNEE = {1: vec((0.115, 0.065, 0.505)), -1: vec((-0.096, 0.010, 0.512))}
B_ANKLE = {1: vec((0.135, 0.050, 0.088)), -1: vec((-0.100, -0.012, 0.088))}
B_FOOT_YAW = {1: -12.0, -1: 7.0}
B_SH = {1: B.chest(0.178, 0.010, 1.418), -1: B.chest(-0.178, 0.010, 1.420)}
LEDGER_SPINE = B.chest(0.0, 0.300, 1.150)
LEDGER_TILT = 52.0                               # page normal elevation toward his face
B_PIVOT = B.chest(0.0, 0.006, 1.492)
B_ND = L.neck_dir(SP_B.yaw_chest, 18.0)
B_HEAD = (-16.0, -28.0, 3.0)


def ledger_frame():
    yaw = math.radians(SP_B.yaw_chest)
    t = math.radians(LEDGER_TILT)
    up_spine = Vector((-math.sin(yaw) * math.sin(t), math.cos(yaw) * math.sin(t), math.cos(t)))  # along the spine, away-up
    across = L.rz(SP_B.yaw_chest, (-1.0, 0.0, 0.0))
    return L.frame_matrix(across, (0, 0, 1), up_spine)


LEDGER_W, LEDGER_H, LEDGER_OPEN = 0.20, 0.29, 150.0


def ledger_grip(side):
    """C-grip at the outer edge of one cover (side +1 = his right): four fingers flat under the cover, palm
    toward its underside, thumb over the edge onto the pages. Returns (wrist, F, N, thumb_tip, edge)."""
    R = ledger_frame()
    h = math.radians((180.0 - LEDGER_OPEN) / 2.0)
    sgn = -side                                   # ledger local +x = his left
    d = Vector((sgn * math.cos(h), math.sin(h), 0.0))
    up = Vector((-sgn * math.sin(h), math.cos(h), 0.0))
    along = Vector((0.0, 0.0, 1.0))
    edge = LEDGER_SPINE + R @ (d * 0.203 - up * 0.006 - along * 0.055)
    wrist = edge + R @ (d * 0.050 - up * 0.019 - along * 0.012)
    F = (R @ (-d * 0.95 + along * 0.30)).normalized()
    N = (R @ up).normalized()
    tip = edge + R @ (-d * 0.036 + up * 0.020 + along * 0.004)
    return wrist, F, N, tip, edge


B_GRIP = {s: ledger_grip(s) for s in (1, -1)}
B_LEDGER_R = ledger_frame()
B_WR = {s: B_GRIP[s][0] for s in (1, -1)}
B_POLE = {1: vec((0.7, -0.3, 0.9)), -1: vec((-0.7, -0.3, 0.9))}
B_EL = {s: E.ik2(B_SH[s], B_WR[s], 0.315, 0.262, B_POLE[s]) for s in (1, -1)}


def man_body():
    f = B
    rings = [
        (0.480, 0.214, 0.212, 0.156, 0.150, 2.2, 0.010, 0.016),
        (0.580, 0.208, 0.207, 0.150, 0.146, 2.2, 0.008, 0.012),
        (0.700, 0.200, 0.200, 0.142, 0.140, 2.1, 0.004, 0.006),
        (0.820, 0.193, 0.193, 0.135, 0.134, 2.1, 0.0, 0.0),
        (0.920, 0.186, 0.186, 0.130, 0.130, 2.05, 0.0, 0.0),
        (1.010, 0.176, 0.176, 0.124, 0.118, 2.0, 0.0, 0.0),
        (1.090, 0.176, 0.176, 0.126, 0.114, 2.0, 0.0, 0.0),
        (1.170, 0.182, 0.182, 0.126, 0.114, 2.0, 0.0, 0.0),
        (1.250, 0.190, 0.190, 0.124, 0.118, 2.0, 0.0, 0.0),
        (1.330, 0.196, 0.196, 0.116, 0.120, 2.0, 0.0, 0.0),
        (1.390, 0.194, 0.194, 0.104, 0.112, 2.0, 0.0, 0.0),
        (1.432, 0.180, 0.180, 0.092, 0.098, 2.05, 0.0, 0.0),
        (1.466, 0.136, 0.136, 0.076, 0.082, 2.0, 0.0, 0.0),
        (1.498, 0.072, 0.072, 0.058, 0.060, 2.0, 0.0, 0.0),
    ]
    coat = L.coat_loft("b_coat", SP_B, rings, seg=40, sub=3, cap0=0.10, cap1=0.3)
    tree = E.bvh(coat)
    parts = [coat] + coat_common(
        f, tree, 0.068, f.chest(0, 0, 1.472),
        [(0.058, 1.478), (0.080, 1.415), (0.074, 1.345), (0.046, 1.262), (0.012, 1.190)],
        [0.048, 0.066, 0.058, 0.034, 0.005], (0.120, 0.920, 0.790, 0.140), (-0.100, 1.320, 1.245),
        (1.180, 1.075, 0.970), 0.004)
    # shirt collar points and tie in the V of the coat
    knot = E.hug(tree, [f.chest(0.0, 0.10, 1.452)], 0.010)[0]
    tip = E.hug(tree, [f.chest(0.004, 0.16, 1.215)], 0.006)[0]
    parts.append(E.ellipsoid("b_knot", knot, (0.013, 0.010, 0.014), rot=E.rot_z(SP_B.yaw_chest), seg=12, rings=8))
    parts.append(E.surface_slab("b_tie", tree, [knot + Vector((0, 0, -0.012)), (knot * 0.5 + tip * 0.5), tip],
                                [0.034, 0.052, 0.072], thick=0.005))
    for sx in (1, -1):
        parts.append(E.surface_slab(f"b_shirtcollar{sx}", tree,
                                    [knot + SP_B.right(1.45) * (sx * 0.012) + Vector((0, 0, 0.012)),
                                     knot + SP_B.right(1.45) * (sx * 0.040) + Vector((0, 0.0, -0.030))],
                                    [0.028, 0.012], thick=0.003))
    parts += sleeves(f, B_SH, B_EL, B_WR, (0.056, 0.053, 0.050, 0.047, 0.049, (0.027, 0.020), (0.048, 0.053, 0.048)))
    for s in (1, -1):
        parts += L.trouser_leg(f"b_trouser{s}", vec((s * 0.10, 0.0, 0.62)) if s > 0 else vec((s * 0.098, 0.0, 0.63)),
                               B_ANKLE[s], r_top=0.068, r_knee=0.062, r_hem=0.061)
        parts += L.shoe(f"b_shoe{s}", B_ANKLE[s], B_FOOT_YAW[s], heel=0.012, scale=1.07)
    parts += L.ledger("b_ledger", LEDGER_SPINE, B_LEDGER_R, w=LEDGER_W, h=LEDGER_H, thick=0.012, open_deg=LEDGER_OPEN,
                      pages=0.010)
    hands = [(man_hand(1), B_WR[1]), (man_hand(-1), B_WR[-1])]
    return finish_figure(f, parts, hands, man_folds, TRIS["b"]["hand"], TRIS["b"]["body"], man_flutes)


def man_hand(s):
    """Holding the open ledger at its outer edge (C-grip): fingers under the cover, thumb on the pages."""
    wrist, F, N, tip, _edge = B_GRIP[s]
    T = L.ortho(F.cross(N) * (1.0 if s > 0 else -1.0), F)   # chirality: right F x N, left N x F

    def thumb(info):
        return L.thumb_to(info, tip, 1.04, bulge=0.004)

    objs, _info = L.hand2(f"b_hand{s}", wrist, F, N, T,
                          curls=[(8, 8, 4), (6, 8, 4), (8, 10, 6), (10, 12, 6)],
                          spread=[4, 0, -4, -9], thumb=thumb, scale=1.04, width=0.082, finger_r=0.0088)
    return [wrist_stub(f"b_wrist{s}", B_EL[s], B_WR[s], (0.027, 0.020))] + objs


def man_folds():
    f, sp = B, SP_B
    k = []
    for s in (1, -1):
        el, sh, wr = B_EL[s], B_SH[s], B_WR[s]
        inner = (sh - el).normalized() + (wr - el).normalized()
        k += [dict(c=el + inner.normalized() * 0.040, s=0.016, a=-0.0055),
              dict(c=el + inner.normalized() * 0.03 + (wr - el).normalized() * 0.035, s=0.012, a=0.003),
              dict(c=el + inner.normalized() * 0.03 + (sh - el).normalized() * 0.04, s=0.012, a=0.0025)]
    k += L.groove([f.chest(0.022, 0.16, 1.19), f.chest(0.022, 0.16, 0.94)], 0.005, -0.0028, face=sp.front(1.0))
    k += L.groove([vec((0.022, 0.2, 0.92)), vec((0.018, 0.22, 0.70)), vec((0.012, 0.25, 0.48))], 0.009, -0.007,
                  face=(0, 1, 0))
    k += L.groove([vec((0.16, 0.07, 0.86)), vec((0.175, 0.08, 0.50))], 0.012, -0.0035)
    k += L.groove([vec((0.10, 0.14, 0.72)), vec((0.11, 0.17, 0.50))], 0.014, 0.003)
    k += L.groove([vec((-0.16, 0.05, 0.86)), vec((-0.18, 0.04, 0.50))], 0.011, -0.003)
    k += L.groove([vec((0.0, -0.15, 0.70)), vec((0.0, -0.15, 0.48))], 0.004, -0.004, face=(0, -1, 0))
    k += L.groove([f.chest(0.12, -0.12, 1.36), f.chest(0.03, -0.12, 1.14)], 0.013, -0.0025, face=-sp.front(1.2))
    k += L.groove([f.chest(-0.12, -0.12, 1.36), f.chest(-0.03, -0.12, 1.14)], 0.013, -0.0025, face=-sp.front(1.2))
    return k


def man_flutes(body):
    def amp(co, t):
        return 0.006 * E.smoothstep(0.76, 0.49, co[:, 2]) * (0.65 + 0.35 * np.sin(co[:, 0] * 19.0 + co[:, 1] * 15.0))
    L.flutes(body, (0.0, 0.01, 0.0), (0, 0, 1), 8, amp, phase=2.0,
             region=lambda co: E.smoothstep(0.76, 0.66, co[:, 2]) * (co[:, 2] > 0.46))


P_B = dict(E.MALE, nose=1.08, brow=1.5)


def hair_side_part(co, nrm):
    """1970s side-parted hair: full over the crown, combed over from a part on his left, covering the top of
    the ears, long sideburns."""
    s = P_B["scale"]
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    deg = np.degrees(np.abs(np.arctan2(x, y + 0.01)))
    hl = np.interp(deg, [0, 30, 50, 68, 80, 95, 140, 180], [0.066, 0.068, 0.058, 0.030, -0.030, -0.020, -0.062, -0.078]) * s
    m = E.smoothstep(hl - 0.002, hl + 0.007, z)
    # sideburns: a strip in front of the ear down to the earlobe
    sb = np.exp(-(((deg - 79) / 5.0) ** 2)) * E.smoothstep(-0.040 * s, -0.020 * s, z) * (1 - m)
    thick = np.interp(deg, [0, 40, 90, 140, 180], [0.010, 0.012, 0.012, 0.011, 0.010])
    thick = thick + 0.004 * E.smoothstep(0.04, 0.10, z)
    # part line on his left (x < 0) and the comb-over sweep
    part = 1.0 - 0.75 * np.exp(-(((x + 0.030 * s) / 0.004) ** 2)) * E.smoothstep(0.03, 0.08, z) * (y > -0.04)
    psi = np.arctan2(y + 0.02, x + 0.03)
    g = 1.0 - 0.20 * (0.5 - 0.5 * np.cos(20 * psi)) * E.smoothstep(0.02, 0.09, z)
    return nrm * ((thick * m * part * g) + 0.0045 * sb)[:, None]


def man_head():
    return L.build_head(P_B, B_PIVOT, B_ND, *B_HEAD, hair_side_part, TRIS["b"]["head"], voxel=0.0018,
                        neck_r=((0.058, 0.060), (0.054, 0.056), (0.054, 0.054)))


def move_head(fig, head, pivot):
    head.data.transform(head.matrix_world)
    head.matrix_world = Matrix.Identity(4)
    head.data.transform(fig.M)
    head.data.update()
    mrlib.set_origin(head, fig.g(pivot))
    return fig.g(pivot)


# ====================================================================== QA
def stacks_context():
    L.proxy("floor", (7.0, 0.02, 6.0), (0.0, -0.01, -0.8), color="2E4236")
    L.proxy("wall_n", (7.0, 3.0, 0.1), (0.0, 1.5, -3.55), color="5E7766")
    L.proxy("wall_w", (0.1, 3.0, 6.0), (-5.05, 1.5, -0.8), color="5E7766")
    if not L.import_ctx("stacks_shelving", (0.0, 0.0, 0.25), 0.0):
        L.proxy("stacks", (1.8, 2.3, 0.9), (0.0, 1.15, 0.25), color="3B4A44")
    L.proxy("screen", (2.6, 1.6, 0.04), (-2.5, 1.9, -3.46), color="D8D4CA")
    L.proxy("vault_frame", (2.4, 2.4, 0.1), (1.5, 1.35, -3.42), color="6A6A66")


def renders(body, heads):
    objs = [body] + heads
    fr = L.g2b
    L.ONLY = set(ARGS[ARGS.index("--only") + 1].split(",")) if "--only" in ARGS else None
    L.clay(NAME, fr(1.3, 1.45, 3.1), fr(0.0, 0.9, 0.0), lens=42, res=(800, 600))
    L.clay(NAME + "_2", fr(0.0, 1.3, 3.6), fr(0.0, 0.9, 0.0), lens=42, res=(800, 600))
    L.clay(NAME + "_3", fr(-3.3, 1.25, 0.8), fr(0.0, 0.88, 0.0), lens=42, res=(800, 600))
    L.ghost(NAME + "_4", objs, fr(0.0, 1.3, 3.6), fr(0.0, 0.9, 0.0), lens=42, res=(800, 600))
    L.ghost(NAME + "_5", objs, fr(-1.4, 1.5, -3.0), fr(0.0, 0.9, 0.0), lens=42, res=(800, 600))
    L.ghost(NAME + "_6", objs, fr(3.3, 1.25, 0.8), fr(0.0, 0.88, 0.0), lens=42, res=(800, 600))
    # close-ups: box hand + bob (woman), ledger hands + head (man)
    a = Vector(fr(-HALF, 1.05, 0.05))
    b = Vector(fr(HALF, 1.25, 0.12))
    L.clay(NAME + "_7", tuple(a + Vector(fr(-0.55, 0.25, 0.75))), tuple(a), lens=50, res=(640, 640))
    L.clay(NAME + "_8", tuple(b + Vector(fr(0.25, 0.35, 0.80))), tuple(b), lens=50, res=(640, 640))
    # hands: the box hand from her right (outer) side, the ledger grip over his shoulder
    g = lambda p: Vector(L.build_to_godot(p))
    box_c = g(A.g(A_BOX_C))
    her_right = g(A.M.to_3x3() @ Vector((1.0, 0.0, 0.0)))
    L.clay(NAME + "_11", tuple(Vector(fr(*(box_c + her_right * 0.62 + Vector((0, 0.18, 0.30)))))), fr(*box_c),
           lens=55, res=(640, 640))
    led = g(B.g(LEDGER_SPINE))
    eye = g(B.g(B_PIVOT + Vector((0, 0.02, 0.17))))
    his_back = g(B.M.to_3x3() @ Vector((0.0, -1.0, 0.0)))
    his_left = g(B.M.to_3x3() @ Vector((-1.0, 0.0, 0.0)))
    L.clay(NAME + "_12", tuple(Vector(fr(*(eye + his_back * 0.08 + his_left * 0.42 + Vector((0, 0.22, 0)))))),
           fr(*led), lens=45, res=(640, 640))
    # in context: the game's hall view (root free look) and the screen view
    L.context_render(NAME + "_9", objs, body, PLACE, YAW, stacks_context, (3.8, 1.65, 1.8), (0.0, 1.3, -2.2),
                     lens_fov_deg=62)
    L.context_render(NAME + "_10", objs, body, PLACE, YAW, stacks_context, (0.75, 1.55, -0.45), (-0.8, 1.0, -1.7),
                     lens_fov_deg=50)


def main():
    mrlib.reset_scene()
    body_a = woman_body()
    body_b = man_body()
    head_a = woman_head()
    piv_a = move_head(A, head_a, A_PIVOT)
    head_b = man_head()
    piv_b = move_head(B, head_b, B_PIVOT)
    body = mrlib.join([body_a, body_b], "echo_body")
    pivots = L.finalize(body, [(head_a, "echo_head_a", piv_a), (head_b, "echo_head_b", piv_b)])
    for o in (body, head_a, head_b):
        print("[echo]", o.name, E.mesh_report(o))
    print("[echo] total tris", mrlib.tri_count(), "/", BUDGET)
    for k, v in pivots.items():
        print("[echo] pivot", k, tuple(round(c, 4) for c in v))
    path = mrlib.export_glb(NAME)
    L.verify_glb(path, ["echo_body", "echo_head_a", "echo_head_b"], pivots, BUDGET)
    if not RENDER:
        return
    if DEV:
        L.QA_DIR = DEV
    renders(body, [head_a, head_b])


if __name__ == "__main__":
    main()
