"""MYSTERY ROOM — Chapter 4 helpers for groups F, G and H (Strand's booth, the watch room, the items).
Additive to lib_ch4.py / lib_ch4_cde.py (never edits them). Contract: docs/models/ch4.md section 8 / 9;
measured results: docs/models/ch4_f.md, ch4_g.md, ch4_h.md.

G-FRAME as lib_ch4: every F / G script builds in Godot axes (x, y, z = Blender x, y, z) and calls `K.to_blender()` before
parenting and export. The items (group H) use the Chapter 2 / 3 item pipeline (Blender Z up) instead.

  MB                one bmesh per material: boxes, bars, bosses, domes, cylinders, prisms, faces (outward normals)
  prism_xy / cyl    closed solids that the MB class does not cover
  picto_loops       2D loops (even-odd, +y up, height 1) of the six Chapter 2 pictograms + the box's wheel-and-arrow
  top_plate         a flat plate lying in the XZ plane (2D +y = Godot -Z, i.e. "up" of a top view = the back)
  relief            a brass relief plate from 2D loops on a vertical face
  gear              a toothed wheel with spokes lying in the XZ plane, axis +Y
  qa_*              QA stand-ins for the booth and the watch room
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
import lib_mech as L  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
from lib_ch4 import K, D  # noqa: E402

TAU = 2.0 * math.pi


# ---------------------------------------------------------------------- mesh builder
class MB:
    """One bmesh for one material; every primitive writes into it. `obj(name)` makes the object."""

    def __init__(self, mat: str):
        self.bm = bmesh.new()
        self.mat = mat

    # -- boxes and bars
    def box(self, mn, mx, bottom=True):
        X.bm_box(self.bm, mn, mx, bottom=bottom)

    def bar(self, a, b, w, ref=(0.0, 1.0, 0.0), caps=True):
        X.bm_bar(self.bm, a, b, w, ref=ref, caps=caps)

    def boss(self, c, normal, r, h, sides=6, phase=0.0):
        X.bm_boss(self.bm, c, normal, r, h, sides=sides, phase=phase)

    def dome(self, c, r, h, segs=5, normal=(0.0, 1.0, 0.0)):
        return X.bm_dome(self.bm, c, r, h, segs=segs, normal=normal)

    def face(self, verts, ref):
        return X.bm_face(self.bm, [self.bm.verts.new(v) for v in verts], ref)

    def quad(self, a, b, c, d, ref):
        return self.face([a, b, c, d], ref)

    def cyl(self, c, axis, r, h, segs=12, r2=None, caps=True, phase=0.0):
        cyl_bm(self.bm, c, axis, r, h, segs=segs, r2=r2, caps=caps, phase=phase)

    def prism(self, pts_xy, z0, z1):
        prism_xy(self.bm, pts_xy, z0, z1)

    def prism_xz(self, pts_xz, y0, y1):
        """A closed prism: a simple polygon in the XZ plane extruded along Y."""
        prism_xz(self.bm, pts_xz, y0, y1)

    def fix(self):
        """Outward normals for a bmesh made only of closed solids."""
        bmesh.ops.recalc_face_normals(self.bm, faces=list(self.bm.faces))

    def obj(self, name, fix=True):
        """The object. The bmesh is NOT welded (`X.bm_obj` merges doubles): welding the coincident corners of overlapping boxes made non-manifold edges and
        smooth-shaded dark top faces (a black rim round the strand box's opening)."""
        if fix:
            self.fix()
        return K.obj_from_bm(name, self.bm, self.mat)


def cyl_bm(bm, c, axis, r, h, segs=12, r2=None, caps=True, phase=0.0):
    """A closed cylinder / cone frustum from point c along `axis` for length h (radius r at c, r2 at the far end)."""
    n = Vector(axis).normalized()
    ref = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    u = n.cross(ref).normalized()
    w = n.cross(u).normalized()
    r2 = r if r2 is None else r2
    c0 = Vector(c)
    lo, hi = [], []
    for i in range(segs):
        a = phase + TAU * i / segs
        d = u * math.cos(a) + w * math.sin(a)
        lo.append(bm.verts.new(c0 + d * r))
        hi.append(bm.verts.new(c0 + n * h + d * r2))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if caps:
        if r2 > 1e-9:
            bm.faces.new(list(reversed(hi)))
        if r > 1e-9:
            bm.faces.new(lo)


def prism_xy(bm, pts, z0, z1):
    """A closed prism: the simple polygon `pts` (x, y), extruded along Z from z0 to z1."""
    lo = [bm.verts.new((x, y, z0)) for (x, y) in pts]
    hi = [bm.verts.new((x, y, z1)) for (x, y) in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))


def prism_xz(bm, pts, y0, y1):
    """A closed prism: the simple polygon `pts` (x, z), extruded along Y from y0 to y1."""
    lo = [bm.verts.new((x, y0, z)) for (x, z) in pts]
    hi = [bm.verts.new((x, y1, z)) for (x, z) in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))


def prism_yz(bm, pts, x0, x1):
    """A closed prism: the simple polygon `pts` (z, y) in the YZ plane, extruded along X from x0 to x1."""
    lo = [bm.verts.new((x0, y, z)) for (z, y) in pts]
    hi = [bm.verts.new((x1, y, z)) for (z, y) in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))


# ---------------------------------------------------------------------- 2D loops
def _scale(loops, h):
    ys = [p[1] for lp in loops for p in lp]
    xs = [p[0] for lp in loops for p in lp]
    cur = max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0
    s = h / cur
    return [[((x - cx) * s, (y - cy) * s) for (x, y) in lp] for lp in loops]


def _ccw(lp):
    a = 0.0
    for i in range(len(lp)):
        x0, y0 = lp[i]
        x1, y1 = lp[(i + 1) % len(lp)]
        a += x0 * y1 - x1 * y0
    return lp if a > 0 else list(reversed(lp))


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def picto_loops(kind: str, h: float = 1.0):
    """The Chapter 2 destination pictograms as flat shapes (outer loops + holes, even-odd), centred, `h` tall.
    kind: star (the director's four-pointed star), book, flask, film, envelope, padlock; and wheels (the box's
    pictogram: a wheel with an arrow to its neighbour)."""
    loops = []
    if kind == "star":
        pts = []
        for i in range(64):
            t = TAU * i / 64
            c, s = math.cos(t), math.sin(t)
            pts.append((0.49 * math.copysign(abs(c) ** 3.3, c), 0.49 * math.copysign(abs(s) ** 3.3, s)))
        loops = [pts]
    elif kind == "book":
        # two pages that rise to the spine, each with three text slits, on a thin cover line
        for sg in (-1, 1):
            pg = [(sg * 0.03, -0.30), (sg * 0.49, -0.20), (sg * 0.49, 0.34), (sg * 0.03, 0.22)]
            loops.append(_ccw(pg))
            for k in range(3):
                y = -0.10 + 0.13 * k
                x0, x1 = sg * 0.10, sg * 0.40
                a, b = min(x0, x1), max(x0, x1)
                yy = y + (0.0 if sg < 0 else 0.0)
                loops.append(_ccw([(a, yy - 0.025 + 0.02 * (abs(a) - 0.03)), (b, yy - 0.025 + 0.02 * (abs(b) - 0.03)),
                                   (b, yy + 0.025 + 0.02 * (abs(b) - 0.03)), (a, yy + 0.025 + 0.02 * (abs(a) - 0.03))]))
        loops.append(_ccw([(-0.49, -0.40), (0.49, -0.40), (0.49, -0.34), (-0.49, -0.34)]))
    elif kind == "flask":
        loops.append(_ccw([(-0.16, 0.48), (0.16, 0.48), (0.16, 0.40), (0.10, 0.40), (0.10, 0.04), (0.42, -0.36), (0.38, -0.46),
                           (-0.38, -0.46), (-0.42, -0.36), (-0.10, 0.04), (-0.10, 0.40), (-0.16, 0.40)]))
        loops.append(list(reversed(_arc(-0.07, -0.22, 0.055, 0, 360, 12)[:-1])))
        loops.append(list(reversed(_arc(0.10, -0.30, 0.04, 0, 360, 10)[:-1])))
        loops.append(list(reversed(_arc(0.03, -0.08, 0.03, 0, 360, 8)[:-1])))
    elif kind == "film":
        rx, ry, rad = -0.08, 0.04, 0.38
        tail = _rect(0.22, -0.40, 0.50, -0.22)
        loops.append(_ccw(_arc(rx, ry, rad, 0, 360, 36)[:-1]))
        for k in range(5):
            a = math.radians(90 + 72 * k)
            loops.append(list(reversed(_arc(rx + 0.21 * math.cos(a), ry + 0.21 * math.sin(a), 0.085, 0, 360, 10)[:-1])))
        loops.append(list(reversed(_arc(rx, ry, 0.04, 0, 360, 8)[:-1])))
        loops.append(_ccw(tail))
        for x in (0.29, 0.36, 0.43):
            loops.append(list(reversed(_rect(x - 0.021, -0.345, x + 0.021, -0.275))))
    elif kind == "envelope":
        loops.append(_ccw(L.rounded_rect(0.96, 0.64, 0.05, 2)))
        loops.append(list(reversed(_ccw([(-0.42, 0.24), (0.0, -0.05), (0.42, 0.24), (0.42, 0.185), (0.0, -0.13), (-0.42, 0.185)]))))
    elif kind == "padlock":
        loops.append(_ccw(L.rounded_rect(0.70, 0.46, 0.06, 2, 0.0, -0.20)))
        loops.append(list(reversed(_arc(0.0, -0.17, 0.07, 0, 360, 10)[:-1])))
        loops.append(list(reversed(_ccw([(-0.035, -0.17), (0.035, -0.17), (0.05, -0.34), (-0.05, -0.34)]))))
        outer = _arc(0.0, 0.08, 0.24, 180, 0, 14)
        inner = _arc(0.0, 0.08, 0.13, 0, 180, 12)
        loops.append(_ccw(outer + inner))
    elif kind == "wheels":
        for (cx, r_out, r_in, n_t) in ((-0.30, 0.30, 0.20, 8), (0.34, 0.24, 0.15, 7)):
            outline = L.gear_outline(n_t, r_out * 0.86, r_out, 0.0, flank=False)
            loops.append(_ccw([(cx + x, y) for (x, y) in outline]))
            loops.append(list(reversed(_arc(cx, 0.0, r_in, 0, 360, 14)[:-1])))
            loops.append(_ccw(_arc(cx, 0.0, 0.045, 0, 360, 8)[:-1]))
        loops.append(_ccw([(-0.02, -0.025), (0.02, -0.025), (0.02, -0.062), (0.075, 0.0), (0.02, 0.062), (0.02, 0.025),
                           (-0.02, 0.025)]))
    else:
        raise KeyError(kind)
    return _scale(loops, h) if kind != "wheels" else [[(x * h, y * h) for (x, y) in lp] for lp in loops]


def relief(name, loops, depth, mat, x=0.0, y=0.0, z=0.0, bevel=0.0004):
    """A relief plate from 2D loops lying on a vertical face that looks along +Z: base plane z, `depth` proud."""
    return K.plate(name, loops, depth, z0=z, mat=mat, bevel=bevel, drop_bottom=True, loc=(x, y, 0.0))


def top_plate(name, loops, y0, depth, mat, x=0.0, z=0.0, bevel=0.0004, rot_deg=0.0):
    """A plate lying in the XZ plane from y0 to y0 + depth (a top view: the loops' +y is Godot -Z), centred (x, z)."""
    o = L.curve_solid(name, loops, depth, bevel=bevel, bevel_res=0, mat=mat, drop_bottom=True)
    o.data.transform(Matrix.Translation((x, y0, z)) @ Matrix.Rotation(math.radians(-90.0), 4, "X")
                     @ Matrix.Rotation(math.radians(rot_deg), 4, "Z"))
    return o


def gear(name, n, r_root, r_tip, y0, y1, centre, mat, hole=0.0, spokes=4, hub=0.0, phase=0.0, rim=0.0075, bevel=0.0, flank=False):
    """A spoked gear in the XZ plane (axis +Y) from y0 to y1 about `centre` = (x, z): an outer toothed outline, `spokes`
    windows (even-odd holes) between a rim of width `rim` and a hub of radius `hub`."""
    outline = L.gear_outline(n, r_root, r_tip, phase, flank=flank)
    loops = [outline]
    if spokes > 0 and hub > 0:
        r_in = r_root - rim
        step = TAU / spokes
        sw = 0.16 * step * 0.5 + 0.0
        for k in range(spokes):
            a0 = k * step + 0.5 * step * 0.28
            a1 = (k + 1) * step - 0.5 * step * 0.28
            w = L.arc_pts(r_in, a0, a1, 5) + L.arc_pts(hub * 1.25, a1, a0, 3)
            loops.append(list(reversed(w)))
    if hole > 0:
        loops.append(list(reversed(L.circle(hole, 8))))
    o = L.curve_solid(name, loops, y1 - y0, bevel=bevel, bevel_res=0, mat=mat, drop_bottom=False)
    o.data.transform(Matrix.Translation((centre[0], y0, centre[1])) @ Matrix.Rotation(math.radians(-90.0), 4, "X"))
    return o


def fluted(name, r, h0, h1, n, depth, base=(0.0, 0.0, 0.0), axis=(0, 0, 1), mat="M_Brass_Aged", cham=0.002):
    """A knurled / fluted cylinder: `n` flutes, groove depth `depth`, chamfered both ends, between h0 and h1 along `axis`."""
    bm = bmesh.new()
    rings = []
    prof = [(r - cham - depth, h0), (r, h0 + cham), (r, h1 - cham), (r - cham - depth, h1)]
    # each ring: alternating tooth (full radius of this profile point) and groove (radius - depth) vertices
    for k, (rr, hh) in enumerate(prof):
        ring = []
        for i in range(2 * n):
            rad = rr if i % 2 == 0 else max(rr - depth, rr * 0.82)
            if k in (0, len(prof) - 1):
                rad = rr
            a = TAU * i / (2 * n)
            ring.append(bm.verts.new((rad * math.cos(a), rad * math.sin(a), hh)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(2 * n):
            j = (i + 1) % (2 * n)
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    o = K.obj_from_bm(name, bm, mat)
    o.data.transform(Matrix.Translation(base) @ K.axis_rot(axis))
    return o


# ---------------------------------------------------------------------- numerals
def digits(n: int, h: float, depth: float, mat: str, centre, normal_z=True, res=1):
    """The decimal digits of n side by side, centred on `centre` = (x, y, z), facing +Z. Returns a list of objects."""
    s = str(n)
    adv = h * 0.68
    x0 = -adv * (len(s) - 1) / 2.0
    out = []
    for i, ch in enumerate(s):
        o = C.N.digit_obj(f"dg{n}_{i}", int(ch), h, depth, mat, res=res)
        o.data.transform(Matrix.Translation((centre[0] + x0 + adv * i, centre[1], centre[2])))
        out.append(o)
    return out


# ---------------------------------------------------------------------- QA environments
def qa_env_hall(extra=()):
    """The hall shell with the shutters open and the floor material without the stone normal (as X.qa_env, no bridge)."""
    X.qa_env(extra=list(extra))


def qa_lamp(name, pos, energy=300.0, colour="FFD9A0", radius=0.08):
    return K.light(name, "POINT", pos, energy, colour, radius=radius)


# ---------------------------------------------------------------------- normals checks (Godot culls back faces)
def shell_report(objs=None, label="", verbose=False):
    """Per mesh object: connected face shells; every CLOSED shell must have a positive signed volume (outward normals).
    Returns the number of inverted closed shells (and prints the open-shell count)."""
    bad = 0
    tot_closed = tot_open = 0
    for o in (objs or [o for o in bpy.context.scene.objects if o.type == "MESH"]):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.faces.ensure_lookup_table()
        seen = set()
        for f0 in bm.faces:
            if f0.index in seen:
                continue
            comp, stack = [], [f0]
            seen.add(f0.index)
            while stack:
                f = stack.pop()
                comp.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index)
                            stack.append(g)
            boundary = sum(1 for f in comp for e in f.edges if len(e.link_faces) == 1)
            if boundary or any(len(e.link_faces) != 2 for f in comp for e in f.edges):
                tot_open += 1
                if verbose:
                    c = comp[0].calc_center_median()
                    print(f"{C.TAG} open shell in {o.name} near {tuple(round(v, 4) for v in c)} ({len(comp)} tris, {boundary} boundary edges)")
                continue
            tot_closed += 1
            vol = sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in comp) / 6.0
            if vol < 0:
                bad += 1
                c = comp[0].calc_center_median()
                print(f"{C.TAG} INVERTED closed shell in {o.name} near {tuple(round(v, 3) for v in c)} vol {vol:.5f} ({len(comp)} tris)")
        bm.free()
    print(f"{C.TAG} shell check {label}: {tot_closed} closed shells ({bad} inverted), {tot_open} open shells (checked by the backface render)")
    return bad


def backface_check(res=300, samples=2, scale_pad=1.12, label="", extra_dirs=(), save=None):
    """Render the (isolated) scene from 14 directions with a view-layer material override that paints back faces red; print the
    red fraction of the object's pixels per view (> 0.5 % deserves a look). Call BEFORE the QA scene is built."""
    scene = bpy.context.scene
    mat = bpy.data.materials.new("QA_backface")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMixShader")
    front = nt.nodes.new("ShaderNodeEmission")
    front.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    back = nt.nodes.new("ShaderNodeEmission")
    back.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1.0)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
    nt.links.new(front.outputs["Emission"], mix.inputs[1])
    nt.links.new(back.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    vl = bpy.context.view_layer
    vl.material_override = mat
    old_world = scene.world
    world = bpy.data.worlds.new("QA_bf_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scene.world = world
    old = (scene.render.engine, scene.cycles.samples, scene.cycles.use_denoising, scene.render.resolution_x, scene.render.resolution_y)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    pts = []
    M.refresh()
    for o in scene.objects:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    span = max((hi - lo).length, 0.02)
    cam_data = bpy.data.cameras.new("QA_bf_cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = span * scale_pad
    cam_data.clip_end = span * 6
    cam = bpy.data.objects.new("QA_bf_cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    dirs += [(sx, sy, sz) for sx in (1, -1) for sy in (1, -1) for sz in (1, -1)] + list(extra_dirs)
    path = os.path.join(bpy.app.tempdir or "/tmp", "qa_backface.png")
    worst = 0.0
    for d in dirs:
        v = Vector(d).normalized()
        cam.location = centre + v * span * 2.5
        cam.rotation_euler = (-v).to_track_quat("-Z", "Y" if abs(v.z) < 0.99 else "X").to_euler()
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        if save:
            import shutil
            os.makedirs(save, exist_ok=True)
            shutil.copy(path, os.path.join(save, f"bf_{d[0]}_{d[1]}_{d[2]}.png".replace("-", "m")))
        img = bpy.data.images.load(path, check_existing=False)
        px = list(img.pixels)
        bpy.data.images.remove(img)
        red = obj = 0
        for i in range(0, len(px), 4):
            r, g = px[i], px[i + 1]
            if r > 0.05 or g > 0.05:
                obj += 1
                if r > 0.6 and g < 0.25:
                    red += 1
        frac = red / max(obj, 1)
        worst = max(worst, frac)
        if frac > 0.005:
            print(f"{C.TAG} backfaces visible from {d}: {100 * frac:.1f} % of the object's pixels")
    vl.material_override = None
    scene.world = old_world
    scene.render.engine, scene.cycles.samples, scene.cycles.use_denoising, scene.render.resolution_x, scene.render.resolution_y = old
    bpy.data.objects.remove(cam, do_unlink=True)
    print(f"{C.TAG} backface check {label}: worst view {100 * worst:.2f} % red ({'OK' if worst <= 0.005 else 'CHECK'})")
    return worst
