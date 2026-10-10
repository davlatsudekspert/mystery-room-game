"""MYSTERY ROOM — Chapter 4 helpers for groups C, D and E (the Array, the Reliquary, the Sun apse).
Additive to lib_ch4.py (never edits it). Contract: docs/models/ch4.md; measured results: docs/models/ch4_c.md / ch4_d.md /
ch4_e.md.

G-FRAME as lib_ch4: every script builds in Godot axes (x, y, z = Blender x, y, z) and calls `K.to_blender()` before
parenting and export.

  bm_*            cheap geometry written straight into one bmesh (boxes, polar boxes, rivet domes, revolved profiles)
  toothed_ring    the geared rim beam of the Array rings (rack teeth, notches), one closed solid
  gem             a faceted crystal (hexagonal prism with pointed ends)
  qa_core / qa_*  QA-only stand-ins (the Core glow, the neighbours of a model)
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, D  # noqa: E402


def pol(r: float, a_deg: float, y: float = 0.0):
    """Point at radius r, azimuth a (degrees from north, clockwise seen from above), height y."""
    a = math.radians(a_deg)
    return (r * math.sin(a), y, -r * math.cos(a))


# ---------------------------------------------------------------------- bmesh primitives
def bm_new():
    return bmesh.new()


def bm_obj(name, bm, mat):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    o = K.obj_from_bm(name, bm, mat)
    return o


def bm_quad(bm, a, b, c, d):
    try:
        return bm.faces.new((bm.verts.new(a), bm.verts.new(b), bm.verts.new(c), bm.verts.new(d)))
    except ValueError:
        return None


def bm_box(bm, mn, mx, bottom=False):
    """Axis-aligned box (outward normals, no bottom unless asked): 10 or 12 tris."""
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                                   (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1))]
    faces = [(4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    if bottom:
        faces.append((0, 1, 2, 3))
    for f in faces:
        bm.faces.new([v[i] for i in f])


def bm_polar_box(bm, r0, r1, a_deg, t_w, y0, y1, bottom=False):
    """A box in polar placement: radial extent r0..r1, tangential width t_w centred on azimuth a (degrees), y0..y1."""
    a = math.radians(a_deg)
    rad = Vector((math.sin(a), 0.0, -math.cos(a)))
    tan = Vector((math.cos(a), 0.0, math.sin(a)))
    h = t_w / 2.0
    corners = []
    for (rr, tt) in ((r0, -h), (r1, -h), (r1, h), (r0, h)):
        corners.append(rad * rr + tan * tt)
    lo = [bm.verts.new((c.x, y0, c.z)) for c in corners]
    hi = [bm.verts.new((c.x, y1, c.z)) for c in corners]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(hi)
    if bottom:
        bm.faces.new(list(reversed(lo)))


def bm_dome(bm, c, r, h, segs=5, normal=(0.0, 1.0, 0.0)):
    """A low rivet head on a surface with outward `normal`: base ring r, shoulder 0.62 r at 0.85 h, flat cap. 3 * segs - 2 + segs tris."""
    n = Vector(normal).normalized()
    ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(ref).normalized()
    w = n.cross(u).normalized()
    base, top = [], []
    for i in range(segs):
        a = 2.0 * math.pi * i / segs
        d = u * math.cos(a) + w * math.sin(a)
        base.append(bm.verts.new(Vector(c) + d * r))
        top.append(bm.verts.new(Vector(c) + d * (0.62 * r) + n * (0.85 * h)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((base[i], base[j], top[j], top[i]))
    bm.faces.new(top)
    return top


def bm_revolve(bm, prof, nseg, centre=(0.0, 0.0), phase_deg=0.0, a0=0.0, a1=360.0, closed=False):
    """Revolve a profile [(r, y)] about the vertical axis through `centre` (x, z). Returns the rings (list of vertex lists).
    Face winding is NOT fixed here: call `fix_dir` afterwards (open surfaces) or recalc normals (closed solids)."""
    full = abs((a1 - a0) - 360.0) < 1e-6
    cnt = nseg if full else nseg + 1
    rings = []
    for (r, y) in prof:
        ring = []
        for i in range(cnt):
            a = math.radians(phase_deg + a0 + (a1 - a0) * i / nseg)
            ring.append(bm.verts.new((centre[0] + r * math.sin(a), y, centre[1] - r * math.cos(a))))
        rings.append(ring)
    for k in range(len(rings) - (0 if closed else 1)):
        ra, rb = rings[k], rings[(k + 1) % len(rings)]
        for i in range(nseg):
            j = (i + 1) % cnt
            try:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            except ValueError:
                pass
    return rings


def fix_dir(bm, up=True):
    """Flip every face of an open revolved strip so its highest flat face looks up (or down when up=False)."""
    best, by = None, -1e9
    for f in bm.faces:
        if abs(f.normal.y) > 0.9:
            y = f.calc_center_median().y
            if y > by:
                best, by = f, y
    if best is not None and (best.normal.y > 0) != up:
        for f in bm.faces:
            f.normal_flip()


# ---------------------------------------------------------------------- the toothed ring (array_rings)
def toothed_ring(name, R, N, mat, y0=0.12, y1=0.50, root=0.30, tip=0.385, w_root=0.56, w_tip=0.34, inner=0.40,
                 notch_w=0.20, notch_depth=0.27, notches=8, pads=True, rivets=True):
    """The geared rim beam of one Array ring, centred on the hall axis, as ONE closed solid (the bottom face is removed at
    the end): inner wall at R - inner, rack teeth from R + root to R + tip over y0..y_band, a stepped rim above, N teeth
    (a multiple of 8), `notches` deep index notches cut into the gaps at azimuths 0, 45, ... (the position azimuths).
    Returns the object."""
    bm = bmesh.new()
    dA = 360.0 / N
    pitch = 2.0 * math.pi * (R + root) / N
    wr = math.degrees((pitch * w_root / 2.0) / (R + root))
    wt = math.degrees((pitch * w_tip / 2.0) / (R + tip))
    yb = y0 + 0.28                      # top of the toothed band
    yr = y1 - 0.04                      # top of the rim wall (the chamfer follows)
    rim_r = R + root - 0.04
    cham_r = R + root - 0.07

    def tooth_loop(y):
        loop = []
        for k in range(N):
            c = (k + 0.5) * dA
            for da, rr in ((-wr, root), (-wt, tip), (wt, tip), (wr, root)):
                loop.append(bm.verts.new(pol(R + rr, c + da, y)))
        return loop

    def circle_loop(r, y):
        return [bm.verts.new(pol(r, (k + 0.5) * dA, y)) for k in range(N)]

    def wall(la, lb):
        n = len(la)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((la[i], la[j], lb[j], lb[i]))

    def ledge(S, T):
        for k in range(N):
            k1 = (k + 1) % N
            t0, t1, t2, t3 = T[4 * k], T[4 * k + 1], T[4 * k + 2], T[4 * k + 3]
            u0, u1 = T[4 * k1], T[4 * k1 + 1]
            bm.faces.new((S[k], S[k1], u1, u0, t3, t2))
            bm.faces.new((S[k], t2, t1))

    # outer: the bottom tooth loop, the band top tooth loop, the rim circle, chamfer circle
    T0, T1 = tooth_loop(y0), tooth_loop(yb)
    S1 = circle_loop(rim_r, yb)
    S2 = circle_loop(rim_r, yr)
    S3 = circle_loop(cham_r, y1)
    wall(T0, T1)
    ledge(S1, T1)
    wall(S1, S2)
    wall(S2, S3)
    # top annulus to the inner chamfer
    Ti = circle_loop(R - inner + 0.06, y1)
    wall(S3, Ti)
    # inner wall with two machined grooves
    prof = [(R - inner + 0.06, y1), (R - inner, y1 - 0.045), (R - inner, yb + 0.07), (R - inner + 0.014, yb + 0.06),
            (R - inner + 0.014, yb - 0.02), (R - inner, yb - 0.03), (R - inner, y0)]
    inner_loops = [Ti] + [circle_loop(r, y) for (r, y) in prof[1:]]
    for a, b in zip(inner_loops[:-1], inner_loops[1:]):
        wall(a, b)
    # bottom (closed solid for the notch cut): annulus inner circle .. tooth loop
    Bi = inner_loops[-1]
    ledge(Bi, T0)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    o = K.obj_from_bm(name, bm, mat)
    # deep index notches
    if notches:
        cb = bmesh.new()
        for m in range(notches):
            g = m * (N // notches) * dA
            bm_polar_box(cb, R + root - notch_depth, R + tip + 0.2, g, notch_w, y0 - 0.05, y1 + 0.2, bottom=True)
        bmesh.ops.recalc_face_normals(cb, faces=list(cb.faces))
        cut = K.obj_from_bm(name + "_cut", cb, mat)
        M.boolean(o, cut)
        # drop the bottom faces again (never seen) to save triangles
        bm2 = bmesh.new()
        bm2.from_mesh(o.data)
        kill = [f for f in bm2.faces if f.normal.y < -0.9 and all(abs(v.co.y - y0) < 1e-4 for v in f.verts)]
        bmesh.ops.delete(bm2, geom=kill, context="FACES")
        bm2.to_mesh(o.data)
        bm2.free()
    extra = bmesh.new()
    if pads:
        for m in range(notches):
            g = m * (N // notches) * dA
            a = math.radians(g)
            rad = Vector((math.sin(a), 0.0, -math.cos(a)))
            tan = Vector((math.cos(a), 0.0, math.sin(a)))
            base = rad * (R + root - 0.34)
            tipp = rad * (R + root - 0.06)
            pts = [base - tan * 0.15, base + tan * 0.15, tipp]
            lo = [extra.verts.new((p.x, y1 - 0.002, p.z)) for p in pts]
            hi = [extra.verts.new((p.x, y1 + 0.022, p.z)) for p in pts]
            for i in range(3):
                j = (i + 1) % 3
                extra.faces.new((lo[j], lo[i], hi[i], hi[j]))
            extra.faces.new(hi)
    if rivets:
        for k in range(0, N, 2):
            c = (k + 0.5) * dA
            for rr in (R + 0.10,):
                p = pol(rr, c, y1)
                bm_dome(extra, p, 0.016, 0.014, segs=5)
    if len(extra.verts):
        bmesh.ops.recalc_face_normals(extra, faces=list(extra.faces))
        ex = K.obj_from_bm(name + "_extra", extra, mat)
        o = K.merge(name, [o, ex])
    else:
        extra.free()
    return o


# ---------------------------------------------------------------------- crystal
def gem(name, centre, r, h_body, h_tip, mat, sides=6, phase_deg=0.0, twist=0.0, tip_top=None):
    """A double-terminated crystal: a prism of `sides` faces (circumradius r, height h_body) with pointed ends h_tip tall,
    centred on `centre`. Optional `twist` rotates the upper ring (a screw); flat shaded faces."""
    bm = bmesh.new()
    cx, cy, cz = centre
    lo, hi = [], []
    for i in range(sides):
        a = math.radians(phase_deg + 360.0 * i / sides)
        lo.append(bm.verts.new((cx + r * math.cos(a), cy - h_body / 2.0, cz + r * math.sin(a))))
        b = a + math.radians(twist)
        hi.append(bm.verts.new((cx + r * math.cos(b), cy + h_body / 2.0, cz + r * math.sin(b))))
    bot = bm.verts.new((cx, cy - h_body / 2.0 - h_tip, cz))
    top = bm.verts.new((cx, cy + h_body / 2.0 + (tip_top if tip_top else h_tip), cz))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new((lo[j], lo[i], bot))
        bm.faces.new((hi[i], hi[j], top))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    o = K.obj_from_bm(name, bm, mat)
    return o


# ---------------------------------------------------------------------- QA helpers
def qa_core(strength=10.0, r=0.55, name="qa_core"):
    core = M.sphere(name, r, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow(name, "CFF6FF", strength))
    core.visible_shadow = False
    return core


def qa_shutters_open() -> None:
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))


def qa_env(extra=()):
    """The hall shell plus neighbouring GLBs (extra = [(name, pos, yaw)]), shutters open, floor without the stone normal."""
    C.qa_begin()
    C.qa_floor_nonormal("catwalk_deck")
    C.qa_hall(shell=True, extra=list(extra))
    C.qa_floor_nonormal("qa_sh_hall_floor")
    qa_shutters_open()
