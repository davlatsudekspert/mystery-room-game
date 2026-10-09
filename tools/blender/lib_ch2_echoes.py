"""Chapter 2 light-echo figures (group E): standing-figure helpers on top of lib_echo.

lib_echo is reused as is (never edited). This module adds what standing, posed figures need:
  * `Spine`: a pelvis->neck curve with a gradual yaw (turned shoulders) and lean;
  * `coat_loft`: torso + coat skirt as ONE loft from the hem to the neck (no waist step);
  * `sleeve`: a continuous shoulder->elbow->cuff sleeve (no ball joints);
  * `hand2`: lib_echo.hand with a FIXED flexion axis per finger (lib_echo.hand re-derives the axis per
    joint, so curls beyond 90 deg reverse direction; fists and pointing hands need the fixed axis);
  * shoes, lower legs, trousers, cloth flutes (`flutes`), surface folds along paths (`groove`);
  * props (archive box, ledger, spectacles, pencil);
  * head assembly identical to the Chapter 1 echoes (`build_head`);
  * export turn: figures are BUILT in the lib_echo convention (Blender, Z up, the figure faces +Y,
    +X = the figure's right) and `turn_to_godot_front` rotates the finished meshes 180 deg about Z so
    the GLB faces Godot +Z (Chapter 2 contract, docs/models/ch2.md section 0);
  * QA: Cycles at 2 fixed threads into qa/blender/ch2, clay + ghost + in-context renders, GLB checks.
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_echo as E  # noqa: E402
import mrlib  # noqa: E402
from lib_echo import vec  # noqa: E402

QA_DIR = os.path.join(mrlib.ROOT, "qa", "blender", "ch2")
TURN = Matrix.Rotation(math.pi, 4, "Z")   # build space (faces +Y) -> export space (faces -Y = Godot +Z)


# ------------------------------------------------------------------ small maths
def rz(deg: float, v) -> Vector:
    return E.rot_z(deg) @ vec(v)


def smooth01(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ortho(v, ref) -> Vector:
    """Component of v perpendicular to ref, normalised."""
    v, r = vec(v), vec(ref).normalized()
    return (v - r * v.dot(r)).normalized()


def godot_to_build(p) -> Vector:
    """Model-local Godot point -> build-space Blender point (inverse of the export turn)."""
    x, y, z = p
    return TURN.inverted().to_3x3() @ Vector((x, -z, y))


def build_to_godot(p) -> tuple:
    b = TURN.to_3x3() @ vec(p)
    return (b.x, b.z, -b.y)


# ------------------------------------------------------------------ spine / torso frame
class Spine:
    """Torso axis: centre(z) and yaw(z) for every height.

    Below z_hip the centre stays at the pelvis centre; up to z_neck it bends toward `neck_xy`
    (quadratic, so the lower back stays upright and the upper back carries the lean).
    Yaw (degrees, + = turned to the figure's LEFT) blends from yaw_hip to yaw_chest between
    z_twist0 and z_twist1.
    """

    def __init__(self, hip_xy, neck_xy, z_hip, z_neck, yaw_hip=0.0, yaw_chest=0.0,
                 z_twist0=None, z_twist1=None):
        self.hip = Vector((hip_xy[0], hip_xy[1]))
        self.neck = Vector((neck_xy[0], neck_xy[1]))
        self.z_hip, self.z_neck = z_hip, z_neck
        self.yaw_hip, self.yaw_chest = yaw_hip, yaw_chest
        self.z0 = z_twist0 if z_twist0 is not None else z_hip + 0.05
        self.z1 = z_twist1 if z_twist1 is not None else z_neck - 0.12

    def centre(self, z: float) -> Vector:
        t = min(max((z - self.z_hip) / (self.z_neck - self.z_hip), 0.0), 1.2)
        c = self.hip.lerp(self.neck, t * t)
        return Vector((c.x, c.y, z))

    def yaw(self, z: float) -> float:
        return self.yaw_hip + (self.yaw_chest - self.yaw_hip) * smooth01((z - self.z0) / (self.z1 - self.z0))

    def point(self, z: float, local) -> Vector:
        """centre(z) + yaw-rotated local (x right, y front, z up) offset."""
        return self.centre(z) + rz(self.yaw(z), local)

    def front(self, z: float) -> Vector:
        return rz(self.yaw(z), (0, 1, 0))

    def right(self, z: float) -> Vector:
        return rz(self.yaw(z), (1, 0, 0))


def coat_loft(name: str, spine: Spine, rings, seg: int = 44, sub: int = 4, cap0: float = 0.12,
              cap1: float = 0.3) -> bpy.types.Object:
    """One closed loft from the hem (first ring) to the neck (last ring).

    rings: (z, rx_right, rx_left, ry_front, ry_back[, power[, dx, dy[, yaw_override]]]) with (dx, dy) a
    centre offset in the ring's yawed frame (use it below the hips to follow the legs).
    """
    pts, rads, sides = [], [], []
    for r in rings:
        z, a, b, c, d = r[:5]
        pw = r[5] if len(r) > 5 else 2.0
        dx, dy = (r[6], r[7]) if len(r) > 7 else (0.0, 0.0)
        yaw = r[8] if len(r) > 8 else spine.yaw(z)
        cen = spine.centre(z) + rz(yaw, (dx, dy, 0))
        pts.append(tuple(cen))
        rads.append((a, b, c, d, pw))
        sides.append(tuple(rz(yaw, (1, 0, 0))))
    return E.loft(name, pts, rads, side=sides, seg=seg, sub=sub, cap0=cap0, cap1=cap1)


# ------------------------------------------------------------------ limbs
def arm_chain(shoulder, wrist, l1: float, l2: float, pole):
    el = E.ik2(shoulder, wrist, l1, l2, pole)
    return vec(shoulder), el, vec(wrist)


def sleeve(prefix: str, sh, el, wr, r_sh=0.054, r_up=0.050, r_el=0.047, r_fore=0.044, r_cuff=0.046,
           cuff_len=0.030, wrist_r=(0.025, 0.019), up=(0, 0, 1), deltoid=(0.052, 0.058, 0.054),
           cuff_gap: float = 0.028, deltoid_off=(0.0, 0.0, 0.006), start_back: float = 0.02):
    """Continuous sleeve (shoulder -> elbow -> cuff) + deltoid cap + elbow point + wrist stub.

    Returns (parts, cuff_centre). The wrist stub emerges from the cuff so the hand joins cleanly.
    """
    sh, el, wr = vec(sh), vec(el), vec(wr)
    fdir = (wr - el).normalized()
    udir = (el - sh).normalized()
    cuff = wr - fdir * cuff_gap
    pts = [sh - udir * start_back, sh + (el - sh) * 0.35, el - udir * 0.05, el, el + fdir * 0.05,
           el + (cuff - el) * 0.55, cuff - fdir * cuff_len, cuff]
    rr = [r_sh * 0.9, r_up, r_el * 1.02, r_el, r_el * 0.99, r_fore, r_cuff * 0.98, r_cuff]
    parts = [E.loft(prefix + "_sleeve", pts, rr, side=up, seg=22, sub=3, cap0=0.6, cap1=0.15)]
    parts.append(E.ellipsoid(prefix + "_deltoid", sh + vec(deltoid_off), deltoid, seg=20, rings=12))
    # olecranon / sleeve point at the back of the elbow
    back = ortho(-(udir + fdir), udir) if (udir - fdir).length > 0.05 else ortho(Vector((0, -1, 0)), udir)
    parts.append(E.ellipsoid(prefix + "_elbowpt", el + back * (r_el * 0.45), (r_el * 0.75,) * 3, seg=14, rings=8))
    parts.append(E.limb(prefix + "_wrist", cuff - fdir * 0.03, wr, [wrist_r, (wrist_r[0] * 0.96, wrist_r[1] * 0.96)],
                        seg=14, side=up))
    return parts, cuff


def lower_leg(prefix: str, knee, ankle, calf=0.056, shin=0.040, knee_r=0.046, ankle_r=0.027):
    """Calf/shin from the knee to the ankle (stocking or bare leg). Ring Y points back on a downward limb."""
    kn, an = vec(knee), vec(ankle)
    return [E.limb(prefix, kn + Vector((0, 0, 0.03)), an,
                   [(knee_r, knee_r, knee_r * 1.04, knee_r * 0.95), (knee_r * 1.0, knee_r * 1.0, calf, shin),
                    (knee_r * 0.86, knee_r * 0.86, calf * 0.82, shin * 0.84),
                    (ankle_r * 1.12, ankle_r * 1.12, ankle_r * 1.2, ankle_r), (ankle_r, ankle_r, ankle_r * 1.1, ankle_r)],
                   ts=[0, 0.22, 0.52, 0.86, 1.0], side=(1, 0, 0), seg=20),
            E.ellipsoid(prefix + "_knee", kn + Vector((0, 0.012, 0.0)), (knee_r, knee_r * 1.05, knee_r * 1.05),
                        seg=16, rings=10)]


def trouser_leg(prefix: str, top, ankle, r_top=0.070, r_knee=0.060, r_hem=0.058, fwd=(0, 1, 0)):
    """Straight 1970s trouser leg from inside the coat to just above the shoe (slight flare)."""
    a, b = vec(top), vec(ankle) + Vector((0, 0, 0.035))
    return [E.limb(prefix, a, b, [(r_top, r_top * 0.95), (r_knee, r_knee * 0.92), (r_knee * 0.95, r_knee * 0.9),
                                  (r_hem, r_hem * 0.95)], ts=[0, 0.4, 0.75, 1.0], side=(1, 0, 0), seg=20, cap1=0.25)]


def shoe(prefix: str, ankle, yaw_deg: float, heel: float = 0.0, scale: float = 1.0, toe: float = 1.0):
    """Closed shoe along the foot; `heel` = heel height (block heel for the women's shoes)."""
    s = scale
    f = rz(yaw_deg, (0, 1, 0))
    base = Vector((ankle[0], ankle[1], 0.0))
    # (d along foot, centre z, top radius, half width)
    sec = [(-0.060, 0.030, 0.024, 0.028), (-0.038, 0.038, 0.036, 0.033), (0.012, 0.040, 0.032, 0.037),
           (0.072, 0.029, 0.024, 0.041), (0.122, 0.021, 0.017, 0.038 * toe), (0.160, 0.016, 0.012, 0.028 * toe)]
    pts, rads = [], []
    for d, cz, top, w in sec:
        lift = heel * (1.0 - smooth01((d * s + 0.02) / 0.11))
        cz2 = cz * s + lift
        bottom = cz * s if d < 0.03 else cz2
        pts.append(base + f * d * s + Vector((0, 0, cz2)))
        rads.append((top * s, min(bottom, cz2), w * s, w * s, 2.6))
    parts = [E.loft(prefix, pts, rads, side=(0, 0, 1), seg=20, sub=3, cap0=0.6, cap1=0.7)]
    if heel > 0.004:
        hb = base + f * (-0.042 * s)
        parts.append(E.loft(prefix + "_heel", [hb + Vector((0, 0, 0.002)), hb + Vector((0, 0, heel + 0.02))],
                            [(0.020 * s, 0.020 * s, 0.022 * s, 0.022 * s, 2.8),
                             (0.024 * s, 0.024 * s, 0.026 * s, 0.026 * s, 2.8)],
                            side=tuple(rz(yaw_deg, (1, 0, 0))), seg=16, sub=2, cap0=0.1, cap1=0.1))
    return parts


# ------------------------------------------------------------------ hands
FINGER_OFFS = (0.0265, 0.0085, -0.0095, -0.0265)
FINGER_LEN = (0.068, 0.076, 0.071, 0.056)


def hand2(prefix: str, wrist, fwd, palm_n, thumb_side, curls, spread=None, thumb=None, scale: float = 1.0,
          palm_len: float = 0.088, width: float = 0.072, finger_r: float = 0.0082, lengths=FINGER_LEN,
          knuckles: bool = True, web: bool = True):
    """Hand with fixed-axis finger flexion (see module doc). Returns (objects, info).

    curls[i] = (mcp, pip, dip) flexion in degrees toward the palm for index..little.
    spread[i] = abduction degrees about the palm normal (+ = toward the thumb).
    thumb: list of world points from the thumb base, or a callable(info) -> points, or None (relaxed).
    """
    F = vec(fwd).normalized()
    N = ortho(palm_n, F)
    Sd = vec(thumb_side)
    Sd = (Sd - F * Sd.dot(F) - N * Sd.dot(N)).normalized()
    W = vec(wrist)
    s = scale
    objs = []
    spread = spread or [4, 1, -2, -6]
    P_kn = W + F * palm_len * s
    objs.append(E.loft(prefix + "_palm",
                       [W - F * 0.012 * s, W + F * 0.03 * s, W + F * 0.062 * s, P_kn],
                       [(0.024 * s, 0.017 * s), (0.033 * s, 0.017 * s), (width / 2 * s, 0.015 * s),
                        (width / 2 * 0.98 * s, 0.012 * s)],
                       side=tuple(Sd), seg=18, sub=3, cap0=0.6, cap1=0.5,
                       offsets=[(0, 0.002 * s), (0, 0.001 * s), (0, 0), (0, -0.001 * s)]))
    objs.append(E.ellipsoid(prefix + "_thenar", W + F * 0.03 * s + Sd * 0.02 * s + N * 0.009 * s,
                            (0.016 * s, 0.024 * s, 0.011 * s), rot=E._frame(Sd, F, N), seg=14, rings=8))
    # hypothenar pad (little-finger side of the palm)
    objs.append(E.ellipsoid(prefix + "_hypo", W + F * 0.04 * s - Sd * 0.022 * s + N * 0.006 * s,
                            (0.012 * s, 0.026 * s, 0.009 * s), rot=E._frame(Sd, F, N), seg=12, rings=8))
    radii = [finger_r, finger_r * 1.03, finger_r * 0.97, finger_r * 0.86]
    tips, joints = [], []
    for i in range(4):
        base = P_kn + Sd * FINGER_OFFS[i] * s - F * 0.004 * s - N * 0.001 * s
        d0 = Matrix.Rotation(math.radians(spread[i]), 3, N) @ F
        axis = d0.cross(N).normalized()      # fixed flexion axis of this finger
        segs = [0.47, 0.30, 0.23]
        pts = [base]
        cur = base
        ang = 0.0
        for j in range(3):
            ang += curls[i][j]
            d = (Matrix.Rotation(math.radians(ang), 3, axis) @ d0).normalized()
            cur = cur + d * lengths[i] * segs[j] * s
            pts.append(cur)
        r = radii[i] * s
        objs.append(E.loft(f"{prefix}_f{i}", pts, [r * 1.05, r * 0.97, r * 0.9, r * 0.8],
                           side=tuple(Sd), seg=12, sub=3, cap0=0.8, cap1=0.95))
        if knuckles:
            objs.append(E.ellipsoid(f"{prefix}_k{i}", base - N * 0.004 * s, (r * 1.05, r * 1.1, r * 0.95),
                                    rot=E._frame(Sd, F, N), seg=10, rings=6))
        tips.append(cur)
        joints.append(pts)
        if sum(curls[i]) > 200:
            # fleshy pads of a tightly curled finger close the loop between the finger and the palm
            cen = sum(pts, Vector()) / len(pts)
            objs.append(E.ellipsoid(f"{prefix}_pad{i}", cen, (r * 0.95, r * 1.25, r * 1.25),
                                    rot=E._frame(Sd, F, N), seg=10, rings=6))
    info = {"tips": tips, "joints": joints, "knuckles": P_kn, "F": F, "N": N, "S": Sd, "W": W}
    if callable(thumb):
        thumb = thumb(info)
    if thumb is None:
        thumb = relaxed_thumb(info, s)
    objs.append(E.loft(prefix + "_thumb", [vec(p) for p in thumb],
                       [0.0135 * s, 0.0105 * s, 0.0092 * s, 0.0082 * s][:len(thumb)] if len(thumb) <= 4 else
                       [0.0135 * s] + [0.0105 * s] * (len(thumb) - 3) + [0.0092 * s, 0.0082 * s],
                       side=tuple(N), seg=12, sub=3, cap0=0.8, cap1=0.95))
    info["thumb_tip"] = vec(thumb[-1])
    info["thumb"] = [vec(p) for p in thumb]
    if web:
        # first web space: skin between the thumb's metacarpal and the index knuckle
        th = [vec(p) for p in thumb]
        a = th[0].lerp(th[1], 0.75)
        b = joints[0][0] - F * 0.010 * s
        m = (a + b) * 0.5 - N * 0.002 * s
        ax = (b - a)
        objs.append(E.ellipsoid(prefix + "_web", m, (ax.length * 0.55, 0.0105 * s, 0.0068 * s),
                                rot=frame_matrix(ax, ortho(N, ax).cross(ax.normalized()), ortho(N, ax)),
                                seg=14, rings=8))
    return objs, info


def arm_hand_frame(fwd, pronation_deg: float, right: bool = True):
    """Palm normal + thumb side for a hand pointing along `fwd`, rotated `pronation_deg` from the neutral
    (handshake) forearm position: 0 = palm faces the body midline, thumb up; 90 = palm down, thumb toward
    the midline. Works for any arm direction that is not vertical."""
    F = vec(fwd).normalized()
    up = Vector((0, 0, 1)) if abs(F.z) < 0.97 else Vector((0, 1, 0))
    U = ortho(up, F)
    lat = F.cross(U) * (1.0 if right else -1.0)     # lateral = away from the body
    c, s = math.cos(math.radians(pronation_deg)), math.sin(math.radians(pronation_deg))
    return (-lat * c - U * s), (U * c - lat * s)


def hand_shell(parts, name: str, tris: int, voxel: float = 0.0012, smooth_iters: int = 3) -> bpy.types.Object:
    """Hands are remeshed on their own, finer grid so the fingers stay separate (the body grid of ~3.4 mm
    fuses fingers into a mitten), then decimated and later boolean-unioned into the body."""
    obj = E.union_remesh(parts, name, voxel)
    E.taubin(obj, smooth_iters)
    E.fill_concave(obj, 4, lam=0.35)
    E.taubin(obj, 2)
    E.decimate(obj, tris)
    E.clean_mesh(obj)
    return obj


def bool_union(base, others, name: str | None = None) -> bpy.types.Object:
    """Exact boolean union of closed shells (one closed 2-manifold result, no hidden inner faces)."""
    for o in others:
        m = base.modifiers.new("u", "BOOLEAN")
        m.operation = "UNION"
        m.object = o
        m.solver = "EXACT"
        mrlib.apply_modifiers(base)
        bpy.data.objects.remove(o, do_unlink=True)
    E.clean_mesh(base)
    if name:
        base.name = base.data.name = name
    return base


def relaxed_thumb(info, s: float = 1.0, gap: float = 1.0):
    """Relaxed thumb: the metacarpal angles toward the front of the palm and the tip rests beside the
    index finger's middle phalanx, a little on the palm side (not splayed out sideways)."""
    F, N, S = info["F"], info["N"], info["S"]
    tb = thumb_base(info, s)
    j = info["joints"][0]
    tip = j[1].lerp(j[2], 0.2) + S * 0.0150 * s * gap + N * 0.0065 * s
    p1 = tb + (F * 0.64 + S * 0.52 + N * 0.50).normalized() * 0.038 * s
    p2 = p1.lerp(tip, 0.52) + S * 0.003 * s * gap + N * 0.001 * s
    return [tb, p1, p2, tip]


def thumb_base(info, s: float = 1.0) -> Vector:
    return info["W"] + info["F"] * 0.022 * s + info["S"] * 0.026 * s + info["N"] * 0.006 * s


def thumb_to(info, tip, s: float = 1.0, bulge: float = 0.010):
    """Thumb polyline from its base to `tip`, bowing away from the palm (natural thumb arc)."""
    tb = thumb_base(info, s)
    tip = vec(tip)
    p1 = tb + (info["F"] * 0.5 + info["S"] * 0.75 + info["N"] * 0.35).normalized() * 0.036 * s
    p2 = p1.lerp(tip, 0.55) + info["S"] * bulge * s
    return [tb, p1, p2, tip]


# ------------------------------------------------------------------ surface sculpt helpers
def groove(path, sigma, amount, face=None, step=None):
    """Sculpt kernels along a polyline: a crease (amount < 0) or a ridge (amount > 0)."""
    path = [vec(p) for p in path]
    ks = []
    for a, b in zip(path[:-1], path[1:]):
        L = (b - a).length
        st = step or max(sigma if isinstance(sigma, (int, float)) else min(sigma), 0.004) * 0.9
        n = max(1, int(L / st))
        for i in range(n):
            ks.append(dict(c=a.lerp(b, i / n), s=sigma, a=amount / 1.0, face=face))
    ks.append(dict(c=path[-1], s=sigma, a=amount, face=face))
    # overlapping Gaussians add up: normalise by the overlap so `amount` is the peak depth
    sig = sigma if isinstance(sigma, (int, float)) else float(np.mean(sigma))
    st = step or max(sig, 0.004) * 0.9
    k = st / (sig * math.sqrt(2 * math.pi))
    for kk in ks:
        kk["a"] = kk["a"] * k
    return ks


def flutes(obj, axis_pt, axis_dir, count: int, amp_fn, phase: float = 0.0, region=None, horizontal=True):
    """Radial cloth flutes around an axis: displacement = amp(t) * sin(count*phi + phase) along the
    horizontal radial direction. amp_fn(co, t) gives the amplitude per vertex (t = axial coordinate)."""
    a = np.array(vec(axis_pt))
    d = np.array(vec(axis_dir).normalized())

    def fn(co, nrm):
        rel = co - a
        t = rel @ d
        radial = rel - np.outer(t, d)
        rl = np.linalg.norm(radial, axis=1) + 1e-9
        ru = radial / rl[:, None]
        # reference frame for the angle
        ref = np.array((1.0, 0.0, 0.0)) if abs(d[0]) < 0.9 else np.array((0.0, 1.0, 0.0))
        e1 = ref - d * ref.dot(d)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        phi = np.arctan2(radial @ e2, radial @ e1)
        amp = amp_fn(co, t)
        if region is not None:
            amp = amp * np.clip(region(co), 0, 1)
        # only push along the radial direction where the surface faces outward
        facing = np.clip((nrm * ru).sum(1) * 1.5, 0, 1)
        return ru * (amp * np.sin(count * phi + phase) * facing)[:, None]
    E.displace_fn(obj, fn)


def gauss_w(centres, sigma):
    cs = [np.array(vec(c)) for c in centres]

    def w(co):
        out = np.zeros(len(co))
        for c in cs:
            d2 = ((co - c) ** 2).sum(1)
            out = np.maximum(out, np.exp(-d2 / (2 * sigma ** 2)))
        return out
    return w


# ------------------------------------------------------------------ props (closed shells)
def rounded_box(name: str, size, centre, rot: Matrix | None = None, bevel: float = 0.006, segments: int = 2):
    o = mrlib.box(name, size, loc=(0, 0, 0), mat=E.ECHO_MAT, bevel=bevel, segments=segments)
    mrlib.apply_transform(o)
    m = Matrix.Translation(vec(centre)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    o.data.transform(m)
    o.data.update()
    return o


def frame_matrix(x, y, z) -> Matrix:
    """3x3 matrix whose columns are the given (orthonormalised) axes."""
    X = vec(x).normalized()
    Z = ortho(z, X)
    Y = Z.cross(X)
    return Matrix((X, Y, Z)).transposed()


def archive_box(prefix: str, centre, rot: Matrix, size=(0.34, 0.12, 0.26)):
    """Archive box (local x = length, y = thickness, z = height) with a lid lip and a hand hole dent.
    Returns (parts, kernels-in-world for the hand hole)."""
    sx, sy, sz = size
    parts = [rounded_box(prefix + "_body", (sx, sy, sz * 0.86), vec(centre) + rot @ Vector((0, 0, -sz * 0.07)),
                         rot, bevel=0.006)]
    parts.append(rounded_box(prefix + "_lid", (sx + 0.008, sy + 0.008, sz * 0.2), vec(centre) + rot @ Vector((0, 0, sz * 0.4)),
                             rot, bevel=0.005))
    return parts


def ledger(prefix: str, spine_pt, rot: Matrix, w=0.21, h=0.30, thick=0.012, open_deg=150.0, pages=0.008):
    """Open ledger: local x across the spread (spine at x=0), y up out of the pages, z along the spine.
    Two covers + two page blocks with a soft V at the spine."""
    parts = []
    half = math.radians((180.0 - open_deg) / 2.0)
    for sgn in (1, -1):
        d = Vector((sgn * math.cos(half), math.sin(half), 0.0))
        up = Vector((-sgn * math.sin(half), math.cos(half), 0.0))
        c_cover = d * (w / 2) - up * (thick * 0.3)
        c_pages = d * (w / 2 - 0.006) + up * (pages * 0.6)
        R = rot @ frame_matrix(d, up, (0, 0, 1))
        parts.append(rounded_box(f"{prefix}_cover{sgn}", (w + 0.006, thick * 0.35, h + 0.01),
                                 vec(spine_pt) + rot @ c_cover, R, bevel=0.0015, segments=1))
        parts.append(rounded_box(f"{prefix}_pages{sgn}", (w - 0.012, pages, h - 0.012),
                                 vec(spine_pt) + rot @ c_pages, R, bevel=0.003, segments=2))
    parts.append(E.loft(prefix + "_spine", [vec(spine_pt) + rot @ Vector((0, -0.002, -h / 2 - 0.004)),
                                            vec(spine_pt) + rot @ Vector((0, -0.002, h / 2 + 0.004))],
                        [(0.010, 0.006), (0.010, 0.006)], side=tuple(rot @ Vector((1, 0, 0))), seg=12, sub=1,
                        cap0=0.2, cap1=0.2))
    return parts


def spectacles(prefix: str, s: float = 1.06, lens_r=(0.021, 0.0165), rim=0.0021, y_front=0.110,
               eye_z=0.003, ear_y=-0.006, ear_z=0.004):
    """Horn-rimmed 1970s spectacles in head-local space (origin eye level, +Y forward)."""
    parts = []
    for sx in (1, -1):
        c = Vector((sx * 0.0335 * s, y_front * s, eye_z * s))
        pts, n = [], 18
        for i in range(n):
            a = 2 * math.pi * i / n
            # slightly rectangular (superellipse) lens outline, wrapped a little around the face
            ca, sa = math.cos(a), math.sin(a)
            px = math.copysign(abs(ca) ** 0.75, ca) * lens_r[0] * s
            pz = math.copysign(abs(sa) ** 0.8, sa) * lens_r[1] * s
            py = -0.0035 * s * (sx * px / (lens_r[0] * s) + 1) ** 2 * 0.25
            pts.append(c + Vector((px, py, pz)))
        parts.append(_ring_tube(f"{prefix}_rim{sx}", pts, rim * s))
        # temple arm: from the outer rim edge back to above the ear
        t0 = c + Vector((sx * lens_r[0] * s * 0.98, -0.004 * s, lens_r[1] * s * 0.45))
        t1 = Vector((sx * 0.069 * s, 0.07 * s, ear_z * s + 0.004 * s))
        t2 = Vector((sx * 0.075 * s, ear_y * s, ear_z * s))
        parts.append(E.loft(f"{prefix}_temple{sx}", [t0, t1, t2], [(rim * 0.85 * s, rim * 1.1 * s)] * 3,
                            side=(0, 0, 1), seg=8, sub=3, cap0=0.5, cap1=0.5))
    # bridge over the nose (keyhole arch)
    b0 = Vector((0.0335 * s - lens_r[0] * s * 0.95, y_front * s, eye_z * s + 0.004 * s))
    parts.append(E.loft(prefix + "_bridge", [b0, Vector((0, (y_front + 0.002) * s, eye_z * s + 0.009 * s)),
                                             Vector((-b0.x, b0.y, b0.z))],
                        [(rim * s, rim * s)] * 3, side=(0, 1, 0), seg=8, sub=4, cap0=0.4, cap1=0.4))
    return parts


def _ring_tube(name: str, pts, r: float):
    """Closed torus-like tube through a closed loop of points."""
    n = len(pts)
    bm = bmesh.new()
    seg = 6
    rings = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        T = (p2 - p0).normalized()
        c = sum(pts, Vector()) / n
        X = ortho(p1 - c, T)
        Y = T.cross(X)
        rings.append([bm.verts.new(p1 + (X * math.cos(2 * math.pi * k / seg) + Y * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    return E._obj_from_bm(name, bm)


# ------------------------------------------------------------------ heads
def head_matrix(pivot, nd, yaw: float, pitch: float, roll: float = 0.0, s: float = 1.0,
                neck_len: float = 0.092):
    """Head-local -> build space. yaw (+ = to the figure's left), pitch (- = looking down), roll (+ = top of
    the head toward the figure's right)."""
    Rh = E.rot_z(yaw) @ E.rot_x(pitch) @ E.rot_y(roll)
    atlas_local = vec((0, -0.012 * s, -0.048 * s))
    atlas = vec(pivot) + vec(nd).normalized() * neck_len
    return Matrix.Translation(atlas - Rh @ atlas_local) @ Rh.to_4x4(), atlas_local


def neck_dir(chest_yaw: float, tilt: float, side_tilt: float = 0.0) -> Vector:
    return rz(chest_yaw, (math.sin(math.radians(side_tilt)), math.sin(math.radians(tilt)),
                          math.cos(math.radians(tilt)))).normalized()


def build_head(P, pivot, nd, yaw, pitch, roll, hair_fn, tris: int, extras_fn=None, kernels=None,
               neck_r=((0.052, 0.054), (0.048, 0.050), (0.050, 0.050)), post_fn=None, voxel: float = 0.0016,
               neck_len: float = 0.092, late_parts_fn=None):
    """Chapter 1 head pipeline (lib_echo face + neck + hair displacement + ears/extras), returned in build
    space with its origin at `pivot`. extras_fn(P) -> extra closed parts (bun, hair shells) unioned in the
    second remesh; late_parts_fn(Mh) -> low-poly shells joined AFTER decimation (spectacles)."""
    s = P["scale"]
    Mh, atlas_local = head_matrix(pivot, nd, yaw, pitch, roll, s, neck_len)
    Mi = Mh.inverted()
    parts = E.face_parts("h", P)
    nb = Mi @ (vec(pivot) - vec(nd) * 0.045)
    nm = Mi @ (vec(pivot) + vec(nd) * 0.05)
    nt = atlas_local + Vector((0, 0.012 * s, 0.03 * s))
    parts.append(E.loft("h_neck", [nb, nm, nt], list(neck_r), side=(1, 0, 0), seg=24, sub=3, cap0=0.3, cap1=0.6))
    head = E.union_remesh(parts, "head_tmp", voxel)
    E.taubin(head, 4)
    E.fill_concave(head, 10)
    E.displace_fn(head, hair_fn)
    E.taubin(head, 2)
    extra = E.ear_parts("h", P)
    if extras_fn is not None:
        extra += extras_fn(P)
    head = E.union_remesh([head] + extra, "head_tmp2", voxel)
    E.taubin(head, 3)
    E.fill_concave(head, 6)
    E.sculpt(head, E.face_kernels(P) + (kernels or []))
    if post_fn is not None:
        post_fn(head)
    E.decimate(head, tris)
    E.clean_mesh(head)
    if late_parts_fn is not None:
        late = late_parts_fn(Mh.inverted() @ Mh)   # head-local
        head = mrlib.join([head] + late, "head_tmp3")
    head.data.transform(Mh)
    mrlib.set_origin(head, vec(pivot))
    return head


# ------------------------------------------------------------------ body finishing
def finish_body(parts, voxel: float, tris: int, hand_centres, hand_sigma: float = 0.06,
                folds_fn=None, post_fn=None, vg_factor: float = 0.002, name: str = "body_tmp"):
    """union -> smooth -> fillets -> folds -> optional displacement -> decimate -> clean."""
    body = E.union_remesh(parts, name, voxel)
    hands_w = gauss_w(hand_centres, hand_sigma)

    def not_hands(co):
        return 1.0 - hands_w(co)

    E.taubin(body, 4)
    E.fill_concave(body, 14, region=not_hands)
    E.fill_concave(body, 3, lam=0.4, region=hands_w)
    if folds_fn is not None:
        E.sculpt(body, folds_fn())
    if post_fn is not None:
        post_fn(body)
    E.taubin(body, 2, region=not_hands)
    E.decimate(body, tris, vgroup_weights=hands_w, vg_factor=vg_factor)
    E.clean_mesh(body)
    return body


def turn_to_godot_front(items):
    """items: list of (obj, pivot_build or None). Bakes transforms, turns 180 deg about Z, resets origins."""
    for obj, pivot in items:
        mrlib.refresh()
        obj.data.transform(obj.matrix_world)
        obj.matrix_world = Matrix.Identity(4)
        obj.data.transform(TURN)
        obj.data.update()
        if pivot is not None:
            mrlib.set_origin(obj, TURN @ vec(pivot))


def finalize(body, heads):
    """heads: list of (obj, name, pivot_build). Names, M_Echo, turn, parent. Returns pivots in Godot coords."""
    turn_to_godot_front([(body, None)] + [(h, p) for (h, _n, p) in heads])
    body.name = body.data.name = "echo_body"
    E.finish_echo(body)
    out = {}
    for h, n, p in heads:
        h.name = n
        h.data.name = n
        E.finish_echo(h)
        mrlib.set_parent(h, body)
        out[n] = build_to_godot(p)
    return out


# ------------------------------------------------------------------ GLB verification
def glb_json(path: str) -> dict:
    with open(path, "rb") as fh:
        data = fh.read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def verify_glb(path: str, required, pivots: dict, budget: int) -> bool:
    """Required node names exist, heads are children of echo_body with identity rotation and translation =
    pivot (Godot coords), total tris within the budget."""
    doc = glb_json(path)
    nodes = doc.get("nodes", [])
    by_name = {n.get("name"): (i, n) for i, n in enumerate(nodes)}
    ok = True
    for r in required:
        if r not in by_name:
            print(f"[verify] MISSING node {r}")
            ok = False
    body_i = by_name.get("echo_body", (None, None))[0]
    for name, piv in pivots.items():
        if name not in by_name:
            continue
        i, n = by_name[name]
        parent = [j for j, m in enumerate(nodes) if i in m.get("children", [])]
        rot = n.get("rotation", [0, 0, 0, 1])
        tr = n.get("translation", [0, 0, 0])
        ident = max(abs(rot[0]), abs(rot[1]), abs(rot[2]), abs(abs(rot[3]) - 1)) < 1e-4
        dpos = max(abs(a - b) for a, b in zip(tr, piv))
        print(f"[verify] {name}: parent={'echo_body' if parent == [body_i] else parent} rot_identity={ident} "
              f"translation={tuple(round(x, 4) for x in tr)} expected={tuple(round(x, 4) for x in piv)}")
        if parent != [body_i] or not ident or dpos > 1e-3:
            ok = False
    total = 0
    for m in doc.get("meshes", []):
        for prim in m["primitives"]:
            idx = prim.get("indices")
            cnt = doc["accessors"][idx]["count"] if idx is not None else doc["accessors"][prim["attributes"]["POSITION"]]["count"]
            total += cnt // 3
            mats = doc.get("materials", [])
            mname = mats[prim["material"]]["name"] if "material" in prim else None
            if mname != E.ECHO_MAT:
                print(f"[verify] mesh {m.get('name')} uses material {mname}")
                ok = False
    print(f"[verify] total tris {total} / budget {budget}")
    if total > budget:
        ok = False
    print(f"[verify] {'PASS' if ok else 'FAIL'} {os.path.basename(path)}")
    return ok


# ------------------------------------------------------------------ QA rendering
def qa_setup() -> None:
    mrlib.QA_DIR = QA_DIR
    os.makedirs(QA_DIR, exist_ok=True)
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2


def clay(name: str, cam, target, lens=45.0, res=(480, 640), samples=24):
    """Lit clay render (same rim/fill set-up as the Chapter 1 echo renders)."""
    qa_setup()
    return E.echo_render(name, cam, target, lens=lens, res=res, samples=samples)


def game_ghost_material() -> bpy.types.Material:
    """QA-only Cycles approximation of game/src/fx/echo.gdshader: additive (emission over a transparent
    BSDF), ALBEDO = tint * (body + pow(1 - N.V, rim_power)) * scanlines, back faces culled (cull_back), so
    only the surfaces facing the camera glow, exactly as in Godot."""
    mat = bpy.data.materials.get("QA_GameGhost")
    if mat:
        return mat
    mat = bpy.data.materials.new("QA_GameGhost")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5            # Facing = 1 - |N.V|
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    body = nt.nodes.new("ShaderNodeMath")
    body.operation = "ADD"
    body.inputs[1].default_value = 0.10
    nt.links.new(pw.outputs[0], body.inputs[0])
    # scanlines: 0.8 + 0.2 sin(world_y * 140)  (Godot y = Blender z)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    m1.inputs[1].default_value = 140.0
    nt.links.new(sep.outputs["Z"], m1.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    nt.links.new(m1.outputs[0], sn.inputs[0])
    lines = nt.nodes.new("ShaderNodeMath")
    lines.operation = "MULTIPLY_ADD"
    lines.inputs[1].default_value = 0.2
    lines.inputs[2].default_value = 0.8
    nt.links.new(sn.outputs[0], lines.inputs[0])
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    nt.links.new(body.outputs[0], strength.inputs[0])
    nt.links.new(lines.outputs[0], strength.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 2.2                  # display gain (unshaded additive in Godot)
    nt.links.new(strength.outputs[0], gain.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.72 ** 2.2, 0.93 ** 2.2, 1.0, 1.0)
    nt.links.new(gain.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    cull = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], cull.inputs["Fac"])
    nt.links.new(add.outputs[0], cull.inputs[1])
    tr2 = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr2.outputs[0], cull.inputs[2])
    nt.links.new(cull.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    return mat


def _with_material(objs, mat):
    saved = {}
    for o in objs:
        saved[o.name] = list(o.data.materials)
        o.data.materials.clear()
        o.data.materials.append(mat)
    return saved


def _restore(objs, saved):
    for o in objs:
        o.data.materials.clear()
        for m in saved[o.name]:
            o.data.materials.append(m)


def ghost(name: str, objs, cam, target, lens=45.0, res=(480, 640), samples=24):
    """Render with the in-game echo look (game_ghost_material) on a near-black background."""
    qa_setup()
    saved = _with_material(objs, game_ghost_material())
    path = mrlib.render_preview(name, cam, target, lens=lens, res=res, samples=samples, world_strength=0.02,
                                lights=[((0, 0, 1), 1, "FFFFFF", 1.0)])
    _restore(objs, saved)
    return path


def place(body, pos_godot, yaw_deg: float) -> None:
    """Put the exported-orientation figure at its world placement (Godot pos + yaw) for a context render."""
    x, y, z = pos_godot
    body.matrix_world = Matrix.Translation((x, -z, y)) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")


def unplace(body) -> None:
    body.matrix_world = Matrix.Identity(4)


def g2b(x, y, z):
    return (x, -z, y)


def proxy(name: str, size_godot, centre_godot, color="2A2622", rough=0.8, emit=None, yaw=0.0):
    """Box proxy given in Godot axes (size x, y, z; centre). Named QA_* so render_preview removes it."""
    sx, sy, sz = size_godot
    mat = "QA_ctx_" + color + ("_e" if emit else "")
    o = mrlib.box("QA_" + name, (sx, sz, sy), loc=g2b(*centre_godot), rot=(0, 0, math.radians(yaw)), mat=mat,
                  bevel=0.004, segments=1)
    m = bpy.data.materials.get(mat)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = mrlib.hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = mrlib.hex_rgba(emit)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    return o


def import_ctx(name: str, pos_godot, yaw: float):
    """Import a neighbouring Chapter 2 GLB if it exists (QA_imp_ prefix -> removed after each render)."""
    import lib_arch
    path = os.path.join(mrlib.MODELS_DIR, name + ".glb")
    if not os.path.exists(path):
        return []
    return lib_arch.import_glb(path, loc=g2b(*pos_godot), rot_z_deg=yaw)


def context_render(name: str, figure_objs, body, pos, yaw, build_ctx, cam_godot, target_godot, lens_fov_deg=None,
                   lens=None, res=(960, 640), samples=28, lamp=None):
    """Figure (ghost look) at its world placement inside a dim proxy/imported context, seen from a game view.

    cam/target are Godot world points; `lens_fov_deg` = the game camera's vertical FOV.
    """
    qa_setup()
    place(body, pos, yaw)
    build_ctx()
    saved = _with_material(figure_objs, game_ghost_material())
    if lens is None:
        # vertical FOV -> focal length for the render aspect (sensor fit AUTO = the wider side)
        fov = math.radians(lens_fov_deg or 50.0)
        aspect = res[0] / res[1]
        sensor = 36.0
        lens = (sensor / aspect) / (2 * math.tan(fov / 2)) if aspect >= 1 else sensor / (2 * math.tan(fov / 2))
    lights = [((0.3, 0.2, 1.0), 260, "FFC58A", 2.0), ((-0.6, -0.8, 0.5), 60, "9FB4C8", 3.0)]
    if lamp is not None:
        lights = lamp
    path = mrlib.render_preview(name, g2b(*cam_godot), g2b(*target_godot), lens=lens, res=res, samples=samples,
                                world_strength=0.05, lights=lights)
    _restore(figure_objs, saved)
    unplace(body)
    return path
