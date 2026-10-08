"""Helpers for the Lumen "light echo" figures and the darkroom dressing.

Built on top of mrlib (never edit mrlib; add shared helpers here).

Figure pipeline (organic, closed, shader-friendly surfaces):
  1. Block the anatomy with closed primitives: `loft` (generalised elliptical tubes through a
     Catmull-Rom spine, rounded caps), `limb` (straight tapered tube) and `ellipsoid`.
  2. `union_remesh` joins every piece and voxel-remeshes it: one closed 2-manifold shell with no
     inner faces (important for an additive glow shader, which would show every hidden layer).
  3. `fill_concave` + `taubin` smooth the junctions into fillets (armpits, knuckles, collar).
  4. `sculpt` adds Gaussian bumps/dents along the normals (eye sockets, lips, cloth folds, grooves).
  5. `decimate` (quadric collapse) brings it to the triangle budget, keeping detail where the
     curvature is.
All numbers are metres, Blender Z-up. Figures face Blender +Y (= Godot -Z).
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib  # noqa: E402

ECHO_MAT = "M_Echo"


# ---------------------------------------------------------------- small maths
def vec(p) -> Vector:
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def lerp(a, b, t):
    return a + (b - a) * t


def rot_x(deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 3, "X")


def rot_y(deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 3, "Y")


def rot_z(deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 3, "Z")


def ik2(root, target, l1: float, l2: float, pole) -> Vector:
    """Two-bone IK: returns the middle joint (elbow/knee) for bone lengths l1, l2.

    `pole` is a world point the joint bends toward.
    """
    a, t, p = vec(root), vec(target), vec(pole)
    d = t - a
    dist = min(d.length, l1 + l2 - 1e-4)
    dn = d.normalized()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    pv = p - a
    perp = (pv - dn * pv.dot(dn)).normalized()
    return a + dn * x + perp * h


def reach(a, b, length: float) -> Vector:
    """Point at `length` from a toward b."""
    a, b = vec(a), vec(b)
    return a + (b - a).normalized() * length


# ---------------------------------------------------------------- spline resampling
def _cr(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def resample(vals, sub: int):
    """Catmull-Rom resampling of a list of numpy arrays, `sub` steps per segment."""
    n = len(vals)
    if n == 1:
        return list(vals)
    out = []
    for i in range(n - 1):
        p0 = vals[i - 1] if i > 0 else 2 * vals[0] - vals[1]
        p3 = vals[i + 2] if i + 2 < n else 2 * vals[-1] - vals[-2]
        for s in range(sub):
            out.append(_cr(p0, vals[i], vals[i + 1], p3, s / sub))
    out.append(vals[-1])
    return out


def _norm_r(r):
    """Radius spec -> (rx_pos, rx_neg, ry_pos, ry_neg, power)."""
    if isinstance(r, (int, float)):
        return (r, r, r, r, 2.0)
    r = tuple(float(x) for x in r)
    if len(r) == 2:
        return (r[0], r[0], r[1], r[1], 2.0)
    if len(r) == 3:  # rx, ry_front, ry_back
        return (r[0], r[0], r[1], r[2], 2.0)
    if len(r) == 4:
        return (r[0], r[1], r[2], r[3], 2.0)
    return r[:5]


# ---------------------------------------------------------------- primitives
def _obj_from_bm(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def loft(name: str, pts, rads, side=(1, 0, 0), seg: int = 20, sub: int = 4,
         cap0: float | None = 1.0, cap1: float | None = 1.0, cap_rings: int = 4,
         offsets=None) -> bpy.types.Object:
    """Closed generalised tube through `pts` (Catmull-Rom).

    rads[i]: r | (rx, ry) | (rx, ry_front, ry_back) | (rx+, rx-, ry+, ry-) | (+power).
    The ring's X axis follows `side` (single vector or one per point) projected off the tangent,
    Y = tangent x X. For an upward torso with side=+X, Y is the front (+Y).
    cap0/cap1: dome length as a fraction of the end radius (0 = nearly flat cap).
    offsets[i]: optional (dx, dy) ring-centre shift in the ring's X/Y frame.
    """
    P = [np.array(p, float) for p in pts]
    R = [np.array(_norm_r(r), float) for r in rads]
    if isinstance(side[0], (int, float)):
        S = [np.array(side, float)] * len(P)
    else:
        S = [np.array(s, float) for s in side]
    O = [np.array(o, float) for o in offsets] if offsets else [np.zeros(2)] * len(P)
    Ps, Rs, Ss, Os = (resample(x, sub) for x in (P, R, S, O))
    n = len(Ps)
    T = []
    for i in range(n):
        t = Ps[min(i + 1, n - 1)] - Ps[max(i - 1, 0)]
        T.append(t / np.linalg.norm(t))
    th = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    cs, sn = np.cos(th), np.sin(th)

    def ring(i, scale=1.0, shift=0.0):
        Tn, Sv, r, o = T[i], Ss[i], np.maximum(Rs[i], 1e-4), Os[i]
        X = Sv - Sv.dot(Tn) * Tn
        X /= np.linalg.norm(X)
        Y = np.cross(Tn, X)
        pw = max(r[4], 0.5)
        cc = np.sign(cs) * np.abs(cs) ** (2.0 / pw)
        ss = np.sign(sn) * np.abs(sn) ** (2.0 / pw)
        rx = np.where(cs >= 0, r[0], r[1])
        ry = np.where(sn >= 0, r[2], r[3])
        C = Ps[i] + X * o[0] + Y * o[1] + Tn * shift
        return C + scale * (np.outer(rx * cc, X) + np.outer(ry * ss, Y))

    bm = bmesh.new()
    rings = []

    def add_ring(arr):
        rings.append([bm.verts.new(tuple(p)) for p in arr])

    def cap(i, frac, sign):
        r = Rs[i]
        rad = min(r[0], r[1], r[2], r[3])
        length = max(frac if frac is not None else 0.0, 0.08) * rad
        out = []
        for k in range(1, cap_rings):
            phi = k / cap_rings * math.pi / 2
            out.append(ring(i, math.cos(phi), sign * length * math.sin(phi)))
        tip = Ps[i] + T[i] * sign * length
        o = Os[i]
        Tn, Sv = T[i], Ss[i]
        X = Sv - Sv.dot(Tn) * Tn
        X /= np.linalg.norm(X)
        Y = np.cross(Tn, X)
        tip = tip + X * o[0] + Y * o[1]
        return out, tip

    c0, tip0 = cap(0, cap0, -1)
    for arr in reversed(c0):
        add_ring(arr)
    first_main = len(rings)
    for i in range(n):
        add_ring(ring(i))
    c1, tip1 = cap(n - 1, cap1, 1)
    for arr in c1:
        add_ring(arr)
    del first_main
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(seg):
            bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
    v0 = bm.verts.new(tuple(tip0))
    v1 = bm.verts.new(tuple(tip1))
    for j in range(seg):
        bm.faces.new((v0, rings[0][(j + 1) % seg], rings[0][j]))
        bm.faces.new((v1, rings[-1][j], rings[-1][(j + 1) % seg]))
    return _obj_from_bm(name, bm)


def limb(name: str, a, b, rads, side=(1, 0, 0), seg: int = 18, cap0=1.0, cap1=1.0,
         ts=None, bow=None) -> bpy.types.Object:
    """Straight tapered tube from a to b; rads sampled at fractions `ts` (default evenly).

    `bow`=(vector, amount) bends the centre line sideways (sin profile) for muscle/cloth sag.
    """
    a, b = np.array(vec(a)), np.array(vec(b))
    k = len(rads)
    ts = ts or [i / (k - 1) for i in range(k)]
    pts = []
    for t in ts:
        p = a + (b - a) * t
        if bow is not None:
            p = p + np.array(bow[0], float) * bow[1] * math.sin(math.pi * t)
        pts.append(p)
    return loft(name, pts, rads, side=side, seg=seg, sub=3, cap0=cap0, cap1=cap1)


def ellipsoid(name: str, center, radii, rot: Matrix | None = None, seg: int = 20,
              rings: int = 12) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    m = Matrix.Diagonal((radii[0], radii[1], radii[2], 1.0))
    if rot is not None:
        m = rot.to_4x4() @ m
    m = Matrix.Translation(vec(center)) @ m
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return _obj_from_bm(name, bm)


def torus_obj(name: str, center, major: float, minor: float, rot: Matrix | None = None,
              seg: int = 24, mseg: int = 10, minor_y: float | None = None) -> bpy.types.Object:
    bm = bmesh.new()
    ring = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            r = major + minor * math.cos(b)
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), (minor_y or minor) * math.sin(b))))
        ring.append(row)
    for i in range(seg):
        for j in range(mseg):
            bm.faces.new((ring[i][j], ring[(i + 1) % seg][j], ring[(i + 1) % seg][(j + 1) % mseg],
                          ring[i][(j + 1) % mseg]))
    m = rot.to_4x4() if rot is not None else Matrix.Identity(4)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(vec(center)) @ m, verts=bm.verts)
    return _obj_from_bm(name, bm)


def transform_obj(obj: bpy.types.Object, mat4: Matrix) -> bpy.types.Object:
    obj.data.transform(mat4)
    obj.data.update()
    return obj


def boolean_intersect(target: bpy.types.Object, cutter: bpy.types.Object) -> None:
    mrlib.boolean(target, cutter, op="INTERSECT")


def half_space_box(name: str, point, normal, size: float = 1.0) -> bpy.types.Object:
    """Big cube whose face passes through `point` and that lies on the -normal side (keep side)."""
    n = vec(normal).normalized()
    q = n.to_track_quat("Z", "Y")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bmesh.ops.translate(bm, vec=(0, 0, -size / 2), verts=bm.verts)
    m = Matrix.Translation(vec(point)) @ q.to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return _obj_from_bm(name, bm)


# ---------------------------------------------------------------- numpy mesh access
def _co(me) -> np.ndarray:
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def _set_co(me, co: np.ndarray) -> None:
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def _edges(me) -> np.ndarray:
    e = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", e)
    return e.reshape(-1, 2)


def _normals(me) -> np.ndarray:
    a = np.empty(len(me.vertices) * 3)
    me.vertex_normals.foreach_get("vector", a)
    return a.reshape(-1, 3)


def _laplace(co: np.ndarray, ed: np.ndarray) -> np.ndarray:
    n = len(co)
    s = np.empty_like(co)
    for k in range(3):
        s[:, k] = (np.bincount(ed[:, 0], weights=co[ed[:, 1], k], minlength=n)
                   + np.bincount(ed[:, 1], weights=co[ed[:, 0], k], minlength=n))
    deg = np.bincount(ed[:, 0], minlength=n) + np.bincount(ed[:, 1], minlength=n)
    return s / np.maximum(deg, 1)[:, None] - co


def _weights(co: np.ndarray, region) -> np.ndarray:
    """region: None (all) or callable(co)->weights 0..1."""
    if region is None:
        return np.ones(len(co))
    return np.clip(region(co), 0.0, 1.0)


def taubin(obj, iters: int = 6, lam: float = 0.5, mu: float = -0.53, region=None) -> None:
    """Volume-preserving smoothing (removes voxel stair-steps)."""
    me = obj.data
    co = _co(me)
    ed = _edges(me)
    w = _weights(co, region)[:, None]
    for _ in range(iters):
        co = co + lam * w * _laplace(co, ed)
        co = co + mu * w * _laplace(co, ed)
    _set_co(me, co)


def laplace_smooth(obj, iters: int = 4, lam: float = 0.5, region=None) -> None:
    me = obj.data
    co = _co(me)
    ed = _edges(me)
    w = _weights(co, region)[:, None]
    for _ in range(iters):
        co = co + lam * w * _laplace(co, ed)
    _set_co(me, co)


def fill_concave(obj, iters: int = 20, lam: float = 0.6, region=None) -> None:
    """Move only concave vertices toward their neighbours: rounds creases into fillets
    (armpits, collar, knuckles) while leaving convex forms untouched."""
    me = obj.data
    ed = _edges(me)
    co = _co(me)
    w = _weights(co, region)
    for _ in range(iters):
        nrm = _normals(me)
        L = _laplace(co, ed)
        conc = (L * nrm).sum(1) > 0.0
        co = co + lam * (w * conc)[:, None] * L
        _set_co(me, co)


def sculpt(obj, kernels) -> None:
    """Gaussian displacement brushes.

    kernel dict: c (centre), s (sigma xyz or scalar), a (amount m, + = outward along normal),
    optional rot (Matrix3, brush axes), dir (displace along this vector instead of the normal),
    face (only vertices whose normal . face > 0), mask (callable(co)->0..1).
    """
    me = obj.data
    co = _co(me)
    nrm = _normals(me)
    disp = np.zeros_like(co)
    for k in kernels:
        c = np.array(vec(k["c"]))
        s = k.get("s", 0.01)
        s = np.array((s, s, s) if isinstance(s, (int, float)) else s, float)
        d = co - c
        if k.get("rot") is not None:
            d = d @ np.array(k["rot"])
        q = ((d / s) ** 2).sum(1)
        w = np.exp(-0.5 * q)
        if k.get("face") is not None:
            f = np.array(vec(k["face"]).normalized())
            w = w * np.clip((nrm @ f) * 2.0, 0.0, 1.0)
        if k.get("mask") is not None:
            w = w * np.clip(k["mask"](co), 0.0, 1.0)
        if k.get("dir") is not None:
            disp += w[:, None] * np.array(k["dir"], float) * k["a"]
        else:
            disp += w[:, None] * nrm * k["a"]
    _set_co(me, co + disp)


def displace_fn(obj, fn) -> None:
    """Generic displacement: fn(co, nrm) -> displacement array (N,3)."""
    me = obj.data
    co = _co(me)
    nrm = _normals(me)
    _set_co(me, co + fn(co, nrm))


# ---------------------------------------------------------------- remesh / decimate
def union_remesh(objs, name: str, voxel: float) -> bpy.types.Object:
    """Join closed parts and voxel-remesh into one closed shell (no inner faces)."""
    obj = mrlib.join(objs, name)
    m = obj.modifiers.new("vox", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.adaptivity = 0.0
    m.use_remove_disconnected = False
    mrlib.apply_modifiers(obj)
    return obj


def tris(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimate(obj, target_tris: int, vgroup_weights=None, vg_factor: float = 1.0) -> None:
    """Quadric collapse to ~target_tris. `vgroup_weights`: callable(co)->0..1 detail priority."""
    cur = tris(obj)
    if cur <= target_tris:
        return
    m = obj.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.use_collapse_triangulate = True
    m.ratio = target_tris / cur
    if vgroup_weights is not None:
        # Blender's collapse multiplies an edge cost by (1 + (2 - w1 - w2) * factor), i.e. LOW
        # weights are preserved. Store detail weights and invert the group so detail = kept.
        vg = obj.vertex_groups.new(name="detail")
        w = np.clip(vgroup_weights(_co(obj.data)), 0.0, 1.0)
        for i, wi in enumerate(w):
            if wi > 1e-3:
                vg.add([i], float(wi), "REPLACE")
        m.vertex_group = "detail"
        m.invert_vertex_group = True
        m.vertex_group_factor = vg_factor
    mrlib.apply_modifiers(obj)
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    # the collapse can leave a few slightly over-target; nudge once more
    if tris(obj) > target_tris * 1.02:
        m = obj.modifiers.new("dec2", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.use_collapse_triangulate = True
        m.ratio = target_tris / tris(obj)
        mrlib.apply_modifiers(obj)


def clean_mesh(obj) -> None:
    """Remove loose verts/degenerate faces, make normals consistent and outward."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.validate(verbose=False)
    obj.data.update()


def mesh_report(obj) -> dict:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bd = sum(1 for e in bm.edges if e.is_boundary)
    # connected components
    seen = set()
    comps = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        comps += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
    bm.free()
    co = _co(obj.data)
    mw = obj.matrix_world
    return {"tris": tris(obj), "non_manifold_edges": nm, "boundary_edges": bd, "shells": comps,
            "bbox_min": tuple(round(x, 3) for x in (mw @ Vector(co.min(0)))),
            "bbox_max": tuple(round(x, 3) for x in (mw @ Vector(co.max(0))))}


# ---------------------------------------------------------------- surface helpers
def bvh(obj) -> BVHTree:
    mrlib.refresh()
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(obj, dg)


def hug(tree: BVHTree, pts, offset: float):
    """Snap points to the nearest surface point + offset along the surface normal."""
    out = []
    for p in pts:
        loc, nrm, _i, _d = tree.find_nearest(vec(p))
        out.append(loc + nrm * offset)
    return out


# ---------------------------------------------------------------- materials & finishing
def echo_material() -> bpy.types.Material:
    return mrlib.material(ECHO_MAT, color="CFF6FF", rough=0.45, metal=0.0, emission="CFF6FF",
                          emission_strength=0.25)


def finish_echo(obj) -> None:
    """Single M_Echo slot, world box UVs, fully smooth normals (fresnel-friendly)."""
    obj.data.materials.clear()
    echo_material()
    mrlib.assign(obj, ECHO_MAT)
    mrlib.box_uv(obj)
    mrlib.smooth(obj, 180.0)


# ---------------------------------------------------------------- hands
def hand(prefix: str, wrist, fwd, palm_n, thumb_side, curls=None, spread=None,
         thumb_pts=None, scale: float = 1.0, palm_len: float = 0.088, width: float = 0.072,
         finger_r: float = 0.0082, lengths=(0.068, 0.076, 0.071, 0.056), pinch: bool = False):
    """Mitten-like hand: palm + 4 touching fingers (fused by the remesh into a mitten with
    soft grooves) + thumb. Returns (objects, info dict with fingertip/thumb-tip positions).

    fwd: wrist->knuckles direction; palm_n: out of the palm; thumb_side: toward the thumb.
    curls[i] = (mcp, pip, dip) degrees toward the palm for index..little.
    thumb_pts: explicit thumb polyline (world points) from its base; otherwise a relaxed thumb.
    """
    F = vec(fwd).normalized()
    N = vec(palm_n)
    N = (N - F * N.dot(F)).normalized()
    Sd = vec(thumb_side)
    Sd = (Sd - F * Sd.dot(F) - N * Sd.dot(N)).normalized()
    W = vec(wrist)
    s = scale
    objs = []
    curls = curls or [(15, 20, 10)] * 4
    spread = spread or [4, 1, -2, -6]
    # palm: from wrist to knuckles, flattened (width across Sd, thickness along N)
    P_kn = W + F * palm_len * s
    palm = loft(prefix + "_palm",
                [W - F * 0.012 * s, W + F * 0.03 * s, W + F * 0.062 * s, P_kn],
                [(0.024 * s, 0.017 * s), (0.033 * s, 0.017 * s), (width / 2 * s, 0.015 * s),
                 (width / 2 * 0.98 * s, 0.012 * s)],
                side=tuple(Sd), seg=18, sub=3, cap0=0.6, cap1=0.5,
                offsets=[(0, 0.002 * s), (0, 0.001 * s), (0, 0), (0, -0.001 * s)])
    objs.append(palm)
    # thenar (thumb ball) on the palm side
    objs.append(ellipsoid(prefix + "_thenar", W + F * 0.03 * s + Sd * 0.02 * s + N * 0.009 * s,
                          (0.016 * s, 0.024 * s, 0.011 * s),
                          rot=_frame(Sd, F, N), seg=14, rings=8))
    offs = [0.0265, 0.0085, -0.0095, -0.0265]
    radii = [finger_r, finger_r * 1.03, finger_r * 0.97, finger_r * 0.86]
    tips = []
    for i in range(4):
        base = P_kn + Sd * offs[i] * s - F * 0.004 * s - N * 0.001 * s
        d = F.copy()
        # spread: rotate about N
        d = Matrix.Rotation(math.radians(spread[i]), 3, N) @ d
        segs = [0.47, 0.30, 0.23]
        pts = [base]
        cur = base
        for j in range(3):
            d = _curl(d, Sd, N, curls[i][j])
            cur = cur + d * lengths[i] * segs[j] * s
            pts.append(cur)
        r = radii[i] * s
        objs.append(loft(f"{prefix}_f{i}", pts, [r * 1.05, r * 0.98, r * 0.9, r * 0.82],
                         side=tuple(Sd), seg=12, sub=3, cap0=0.8, cap1=0.9))
        tips.append(cur)
    # thumb
    if pinch:
        tb = W + F * 0.022 * s + Sd * 0.024 * s + N * 0.006 * s
        t1 = tb + (F * 0.55 + Sd * 0.55 + N * 0.35).normalized() * 0.040 * s
        t3 = tips[0] + Sd * 0.012 * s + F * 0.004 * s
        t2 = t1.lerp(t3, 0.55) + Sd * 0.008 * s
        thumb_pts = [tb, t1, t2, t3]
    if thumb_pts is None:
        tb = W + F * 0.022 * s + Sd * 0.026 * s + N * 0.006 * s
        d1 = (F * 0.55 + Sd * 0.65 + N * 0.45).normalized()
        p1 = tb + d1 * 0.042 * s
        d2 = (F * 0.85 + Sd * 0.25 + N * 0.35).normalized()
        p2 = p1 + d2 * 0.03 * s
        p3 = p2 + (F * 0.85 + N * 0.45).normalized() * 0.026 * s
        thumb_pts = [tb, p1, p2, p3]
    objs.append(loft(prefix + "_thumb", thumb_pts,
                     [0.0135 * s, 0.0105 * s, 0.0092 * s, 0.0082 * s],
                     side=tuple(N), seg=12, sub=3, cap0=0.8, cap1=0.9))
    info = {"tips": tips, "thumb_tip": vec(thumb_pts[-1]), "knuckles": P_kn,
            "F": F, "N": N, "S": Sd}
    return objs, info


def _frame(x, y, z) -> Matrix:
    m = Matrix((x, y, z)).transposed()
    return m


def _curl(d: Vector, Sd: Vector, N: Vector, deg: float) -> Vector:
    """Rotate direction d toward the palm normal N by deg (about the axis d x N)."""
    axis = d.cross(N)
    if axis.length < 1e-6:
        return d
    return (Matrix.Rotation(math.radians(deg), 3, axis.normalized()) @ d).normalized()


# ---------------------------------------------------------------- QA rendering
def qa_proxy_box(name: str, size, loc, color: str = "1E2024") -> bpy.types.Object:
    """Dim grey reference geometry for QA renders only (desk, seat, board). Not exported."""
    o = mrlib.box("QA_" + name, size, loc=loc, mat="QA_Proxy", bevel=0.005, segments=1)
    m = bpy.data.materials.get("QA_Proxy")
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = mrlib.hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = 0.8
    return o


def rim_lights(cam_loc, target, rim_energy: float = 3200, fill_energy: float = 14):
    """One strong cool rim light behind the subject (relative to the camera) + faint fill."""
    c = vec(cam_loc)
    t = vec(target)
    d = (c - t).normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up).normalized()
    rim = (-d * 1.0 + up * 0.55 + side * 0.55).normalized()
    fill = (d * 1.0 - side * 0.7 + up * 0.25).normalized()
    return [(tuple(rim), rim_energy, "DDF6FF", 0.5), (tuple(fill), fill_energy, "FFFFFF", 2.5)]


def echo_render(name: str, cam_loc, target, lens: float = 50.0, res=(800, 1000),
                samples: int = 40, rim_energy: float = 3200, fill_energy: float = 14) -> str:
    return mrlib.render_preview(name, cam_loc, target, lens=lens, res=res, samples=samples,
                                world_strength=0.04,
                                lights=rim_lights(cam_loc, target, rim_energy, fill_energy))


def ghost_look_material() -> bpy.types.Material:
    """QA-only approximation of the in-game additive light-echo shader (fresnel rim glow)."""
    mat = bpy.data.materials.get("QA_Ghost")
    if mat:
        return mat
    mat = bpy.data.materials.new("QA_Ghost")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeMath")
    ramp.operation = "POWER"
    ramp.inputs[1].default_value = 1.6
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    mix_amt = nt.nodes.new("ShaderNodeMath")
    mix_amt.operation = "MULTIPLY_ADD"
    mix_amt.inputs[1].default_value = 5.0
    mix_amt.inputs[2].default_value = 0.35
    nt.links.new(ramp.outputs[0], mix_amt.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = mrlib.hex_rgba("BFF2FF")
    nt.links.new(mix_amt.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    return mat


def ghost_render(name: str, objs, cam_loc, target, lens: float = 50.0, res=(800, 1000),
                 samples: int = 24) -> str:
    """Render with the QA fresnel-glow material (approximates the Godot echo shader)."""
    ghost = ghost_look_material()
    saved = {}
    for o in objs:
        saved[o.name] = list(o.data.materials)
        o.data.materials.clear()
        o.data.materials.append(ghost)
    path = mrlib.render_preview(name, cam_loc, target, lens=lens, res=res, samples=samples,
                                world_strength=0.02, lights=[((0, 0, 1), 1, "FFFFFF", 1.0)])
    for o in objs:
        o.data.materials.clear()
        for m in saved[o.name]:
            o.data.materials.append(m)
    return path


# ---------------------------------------------------------------- heads
FEMALE = dict(scale=1.0, jaw=1.0, brow=1.0, nose=1.0, chin=1.0, lips=1.0, cheek=1.0)
MALE = dict(scale=1.06, jaw=1.1, brow=1.8, nose=1.18, chin=1.12, lips=0.8, cheek=0.85)


def face_parts(prefix: str, p=FEMALE):
    """Closed primitives for skull + face in head-local space.

    Head-local: origin at eye level on the mid-plane, +Y = face forward, +Z = up.
    Female reference: vertex z=+0.112, chin z=-0.11 (0.22 m head height).
    """
    s, j, ns = p["scale"], p["jaw"], p["nose"]
    o = []
    o.append(ellipsoid(prefix + "_cranium", (0, -0.012 * s, 0.022 * s),
                       (0.071 * s, 0.093 * s, 0.090 * s), seg=32, rings=18))
    o.append(ellipsoid(prefix + "_forehead", (0, 0.030 * s, 0.026 * s),
                       (0.062 * s, 0.056 * s, 0.058 * s), seg=24, rings=14))
    # face mask, lofted from the chin up to the brow (front = +Y)
    rings = [  # (z, centre_y, rx, ry_front, ry_back)
        (-0.098, 0.050, 0.022 * j, 0.036, 0.030),
        (-0.086, 0.040, 0.036 * j, 0.050, 0.040),
        (-0.066, 0.026, 0.049 * j, 0.066, 0.052),
        (-0.040, 0.020, 0.058, 0.070, 0.062),
        (-0.012, 0.020, 0.064, 0.066, 0.062),
        (0.018, 0.020, 0.063, 0.066, 0.060),
    ]
    o.append(loft(prefix + "_face", [(0, cy * s, z * s) for (z, cy, _a, _b, _c) in rings],
                  [(a * s, b * s, c * s) for (_z, _cy, a, b, c) in rings],
                  side=(1, 0, 0), seg=28, sub=3, cap0=0.55, cap1=0.4))
    for sx in (1, -1):
        # jaw line from the angle of the jaw to the chin
        o.append(limb(f"{prefix}_jaw{sx}", (sx * 0.049 * j * s, -0.004 * s, -0.066 * s),
                      (sx * 0.017 * s, 0.072 * s, -0.103 * s),
                      [(0.010 * s, 0.012 * s), (0.010 * s, 0.011 * s), (0.009 * s, 0.009 * s)],
                      side=(sx, 0, 0), seg=12))
        o.append(ellipsoid(f"{prefix}_cheek{sx}", (sx * 0.050 * s, 0.050 * s, -0.008 * s),
                           (0.020 * s * p["cheek"], 0.018 * s, 0.013 * s), seg=14, rings=8))
        # nose wings
        o.append(ellipsoid(f"{prefix}_ala{sx}", (sx * 0.0125 * s * ns, 0.0935 * s, -0.0435 * s),
                           (0.0075 * s * ns, 0.0085 * s * ns, 0.0062 * s * ns), seg=12, rings=8))
    o.append(ellipsoid(prefix + "_chin", (0, 0.078 * s, -0.096 * s),
                       (0.019 * s * j, 0.0145 * s * p["chin"], 0.0145 * s), seg=16, rings=10))
    # nose ridge: nasion -> tip -> subnasale
    o.append(loft(prefix + "_nose",
                  [(0, 0.083 * s, 0.006 * s), (0, (0.083 + 0.0125 * ns) * s, -0.020 * s),
                   (0, (0.083 + 0.024 * ns) * s, -0.038 * s),
                   (0, (0.083 + 0.017 * ns) * s, -0.0465 * s), (0, 0.089 * s, -0.050 * s)],
                  [(0.0068 * s, 0.006 * s), (0.0074 * s * ns, 0.007 * s),
                   (0.0105 * s * ns, 0.0085 * s), (0.009 * s * ns, 0.006 * s),
                   (0.0068 * s, 0.004 * s)],
                  side=(1, 0, 0), seg=14, sub=3, cap0=0.7, cap1=0.7))
    lp = p["lips"]
    o.append(loft(prefix + "_lipU",
                  [(-0.025 * s, 0.078 * s, -0.064 * s), (-0.012 * s, 0.0925 * s, -0.0605 * s),
                   (0, 0.0965 * s, -0.0595 * s), (0.012 * s, 0.0925 * s, -0.0605 * s),
                   (0.025 * s, 0.078 * s, -0.064 * s)],
                  [(0.003 * s, 0.003 * s), (0.0055 * s * lp, 0.0048 * s * lp),
                   (0.0058 * s * lp, 0.005 * s * lp), (0.0055 * s * lp, 0.0048 * s * lp),
                   (0.003 * s, 0.003 * s)],
                  side=(0, 0, 1), seg=12, sub=3))
    o.append(loft(prefix + "_lipL",
                  [(-0.022 * s, 0.079 * s, -0.067 * s), (-0.010 * s, 0.090 * s, -0.0715 * s),
                   (0, 0.0925 * s, -0.0725 * s), (0.010 * s, 0.090 * s, -0.0715 * s),
                   (0.022 * s, 0.079 * s, -0.067 * s)],
                  [(0.003 * s, 0.003 * s), (0.0058 * s * lp, 0.0052 * s * lp),
                   (0.0062 * s * lp, 0.0055 * s * lp), (0.0058 * s * lp, 0.0052 * s * lp),
                   (0.003 * s, 0.003 * s)],
                  side=(0, 0, 1), seg=12, sub=3))
    return o


def ear_parts(prefix: str, p=FEMALE):
    s = p["scale"]
    o = []
    for sx in (1, -1):
        rot = rot_z(sx * 14) @ rot_x(-12)
        o.append(ellipsoid(f"{prefix}_ear{sx}", (sx * 0.0725 * s, -0.010 * s, -0.010 * s),
                           (0.0085 * s, 0.0185 * s, 0.029 * s), rot=rot, seg=16, rings=10))
    return o


def face_kernels(p=FEMALE):
    """Sculpt brushes for the face (head-local space)."""
    s, b = p["scale"], p["brow"]
    k = []
    for sx in (1, -1):
        k += [
            dict(c=(sx * 0.032 * s, 0.091 * s, 0.004 * s), s=(0.017 * s, 0.02 * s, 0.012 * s), a=-0.0075 * s,
                 face=(0, 1, 0)),
            dict(c=(sx * 0.0315 * s, 0.087 * s, -0.001 * s), s=(0.011 * s, 0.012 * s, 0.0072 * s), a=0.0036 * s,
                 face=(0, 1, 0)),
            dict(c=(sx * 0.030 * s, 0.092 * s, 0.021 * s), s=(0.021 * s, 0.012 * s, 0.0065 * s), a=0.0018 * s * b,
                 face=(0, 1, 0)),
            dict(c=(sx * 0.047 * s, 0.065 * s, -0.042 * s), s=(0.012 * s, 0.014 * s, 0.012 * s), a=-0.0016 * s,
                 face=(0, 1, 0)),
            dict(c=(sx * 0.066 * s, 0.040 * s, 0.030 * s), s=(0.010 * s, 0.014 * s, 0.014 * s), a=-0.0016 * s),
            # ear bowl (concha)
            dict(c=(sx * 0.081 * s, -0.004 * s, -0.012 * s), s=(0.008 * s, 0.009 * s, 0.012 * s), a=-0.0035 * s,
                 face=(sx, 0, 0)),
        ]
    k += [
        dict(c=(0, 0.090 * s, 0.012 * s), s=(0.008 * s, 0.01 * s, 0.007 * s), a=-0.0018 * s),
        dict(c=(0, 0.100 * s, -0.0662 * s), s=(0.021 * s, 0.012 * s, 0.0016 * s), a=-0.0022 * s, face=(0, 1, 0)),
        dict(c=(0, 0.095 * s, -0.081 * s), s=(0.015 * s, 0.012 * s, 0.0045 * s), a=-0.0018 * s, face=(0, 1, 0)),
        dict(c=(0, 0.098 * s, -0.055 * s), s=(0.0035 * s, 0.01 * s, 0.004 * s), a=-0.0008 * s, face=(0, 1, 0)),
    ]
    return k


def face_detail_weight(p=FEMALE):
    """Decimation priority: face front and ears keep more triangles."""
    s = p["scale"]

    def w(co):
        front = np.clip((co[:, 1] - 0.03 * s) / (0.05 * s), 0, 1) * np.clip((0.04 * s - co[:, 2]) / 0.02, 0, 1)
        front *= np.clip((co[:, 2] + 0.125 * s) / 0.02, 0, 1)
        ears = np.exp(-0.5 * (((np.abs(co[:, 0]) - 0.075 * s) / 0.015) ** 2 + ((co[:, 1] + 0.01 * s) / 0.025) ** 2
                              + ((co[:, 2] + 0.01 * s) / 0.035) ** 2))
        return np.maximum(front, ears)
    return w


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def collar_band(name: str, centre, radius: float, angles, height: float = 0.022,
                width: float = 0.036, thick: float = 0.0045, back_lift: float = 0.008,
                slope: float = 0.66) -> bpy.types.Object:
    """Fold-down shirt/coat collar lying around a neck centred at `centre` (vertical axis).

    angles: degrees from the front (+Y) around the neck, e.g. [55 .. 305] for a back collar.
    """
    c = vec(centre)
    pts, sides = [], []
    for a in angles:
        r = math.radians(a)
        rh = Vector((math.sin(r), math.cos(r), 0.0))
        back = 0.5 - 0.5 * math.cos(r)  # 0 front .. 1 back
        top = c + rh * radius + Vector((0, 0, height + back_lift * back))
        w = (rh * (1.0 - slope * 0.5) + Vector((0, 0, -slope))).normalized()
        pts.append(top + w * width * 0.5)
        sides.append(tuple(w))
    return loft(name, pts, [(width * 0.5, thick)] * len(pts), side=sides, seg=10, sub=3,
                cap0=0.3, cap1=0.3)


def surface_slab(name: str, tree: BVHTree, pts, widths, thick: float = 0.004,
                 side_sign: float = 0.0) -> bpy.types.Object:
    """Thin strip (lapel, pocket, placket) hugging a surface along `pts`.

    side_sign: 0 = strip centred on the path, +1/-1 = strip extends to one side of the path.
    """
    on = hug(tree, pts, thick)
    nrm = []
    for p in on:
        _loc, n, _i, _d = tree.find_nearest(p)
        nrm.append(tuple(n))
    return loft(name, on, [(thick, w / 2) for w in widths], side=nrm, seg=10, sub=4,
                cap0=0.3, cap1=0.3, offsets=[(0, side_sign * w / 2) for w in widths])
