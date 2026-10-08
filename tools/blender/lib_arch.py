"""MYSTERY ROOM — extra helpers for architecture / furniture models (room shell, door, desk...).

Complements tools/blender/mrlib.py (do not edit mrlib from here; it is shared):
  * sweep()        2D profile swept along a polyline with mitred corners (mouldings, casings, rails)
  * tube()         round tube along a 3D path with filleted bends (pipes, conduit, bentwood, cords)
  * loft()         skin a list of equal-length rings (cloth, organic shapes)
  * WallFrame      local frame for a wall: x = right along the wall (seen from the room),
                   y = into the wall, z = up  (same convention as wall-mounted models)
  * profiles       ogee / cove / bead helpers that return (s, u) point lists
  * export_lean()  glTF export without the CC0 PBR images (materials are replaced in Godot by
                   res://assets/materials/<slot>.tres); decal images are kept
  * QA helpers     interior lights, glb import for composite renders
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402

ROOT = M.ROOT
DECALS = os.path.join(ROOT, "game", "assets", "textures", "decals")

# Texture folders whose name does not follow mrlib's M_<Name> -> <name> rule (QA preview only).
_TEX_ALIASES = {"M_Ceiling": "plaster_ceiling"}


def prepare_materials() -> None:
    """Pre-create materials whose CC0 texture folder name differs from the slot name (QA only)."""
    for mname, folder in _TEX_ALIASES.items():
        if bpy.data.materials.get(mname) is not None:
            continue
        tex_dir = os.path.join(ROOT, "game", "assets", "textures", folder)
        mat = M.material(mname)
        if os.path.isdir(tex_dir):
            nt = mat.node_tree
            M._attach_pbr(nt, nt.nodes.get("Principled BSDF"), tex_dir)


def font_path(bold: bool = True) -> str | None:
    cands = [
        os.path.join(ROOT, "tools", "fonts", "CormorantGaramond-Bold.ttf"),
        os.path.join(ROOT, "tools", "fonts", "CormorantGaramond-SemiBold.ttf"),
        os.path.join(ROOT, "game", "assets", "fonts", "CormorantGaramond-Bold.ttf"),
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return None


# ---------------------------------------------------------------- basic mesh plumbing
def obj_from_bm(name: str, bm: bmesh.types.BMesh, mat: str, col=None) -> bpy.types.Object:
    obj = M._new_obj(name, bm, col)
    M.assign(obj, mat)
    return obj


def bake(obj: bpy.types.Object, matrix: Matrix) -> bpy.types.Object:
    """Transform mesh data by `matrix` (object stays at identity)."""
    obj.data.transform(matrix)
    obj.matrix_basis = Matrix.Identity(4)
    return obj


def place(obj: bpy.types.Object, matrix: Matrix) -> bpy.types.Object:
    """Pre-multiply the object's current local transform by `matrix` and bake it into the mesh."""
    M.refresh()
    full = matrix @ obj.matrix_basis
    obj.data.transform(full)
    obj.matrix_basis = Matrix.Identity(4)
    return obj


def mat_by_face(obj: bpy.types.Object, fn) -> None:
    """fn(center: Vector(world), normal: Vector(world), current_name) -> material name or None."""
    M.refresh()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    me = obj.data
    names = [m.name if m else "" for m in me.materials]
    for p in me.polygons:
        c = mw @ p.center
        n = (rot @ p.normal).normalized()
        cur = names[p.material_index] if p.material_index < len(names) else ""
        res = fn(c, n, cur)
        if res and res != cur:
            p.material_index = M.add_slot(obj, res)
            names = [m.name if m else "" for m in me.materials]


def bevel_edges(obj: bpy.types.Object, pred, width: float, segments: int = 1) -> None:
    """Bevel edges of obj whose (v0, v1) local coordinates satisfy pred(v0, v1)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edges = [e for e in bm.edges if pred(e.verts[0].co, e.verts[1].co)]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type="OFFSET", segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()


def tris(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------------------------------------------------------------- 2D helpers
def arc(cx: float, cy: float, r: float, a0: float, a1: float, n: int):
    """Points on an arc from angle a0 to a1 (degrees), inclusive, n segments."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rounded_rect(w: float, h: float, r: float, seg: int = 3, cx: float = 0.0, cy: float = 0.0):
    """CCW rounded rectangle centred on (cx, cy)."""
    r = min(r, w / 2 - 1e-5, h / 2 - 1e-5)
    pts = []
    for (ccx, ccy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0),
                           (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        pts += arc(cx + ccx, cy + ccy, r, a0, a0 + 90, seg)
    return pts


def signed_area(pts) -> float:
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2


def ccw(pts):
    return list(pts) if signed_area(pts) > 0 else list(reversed(pts))


def dedupe(pts, eps=1e-6):
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > eps or abs(out[-1][1] - p[1]) > eps):
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


# ---------------------------------------------------------------- sweep (mouldings)
def sweep(name: str, profile, path, up=(0, 0, 1), closed: bool = False, mat: str = "M_Wood_Walnut",
          caps: bool = True, col=None) -> bpy.types.Object:
    """Sweep a closed 2D profile [(s, u)] along a polyline with mitred joints.

    s = offset to the LEFT of the travel direction (left = up x tangent), u = offset along `up`.
    `up` must be perpendicular to every path segment (e.g. Z for horizontal room trims, the wall
    normal for a casing that runs in the wall plane).
    """
    up = Vector(up).normalized()
    prof = ccw(dedupe(profile))
    pts = [Vector(p) for p in path]
    n = len(pts)
    bm = bmesh.new()
    rings = []
    for i in range(n):
        dirs = []
        if closed or i > 0:
            dirs.append((pts[i] - pts[i - 1]).normalized())
        if closed or i < n - 1:
            dirs.append((pts[(i + 1) % n] - pts[i]).normalized())
        sides = [up.cross(d).normalized() for d in dirs]
        m = sides[0] if len(sides) == 1 else (sides[0] + sides[1])
        if m.length < 1e-6:
            m = sides[0]
        m.normalize()
        k = 1.0 / max(0.25, m.dot(sides[0]))
        rings.append([bm.verts.new(pts[i] + m * (s * k) + up * u) for (s, u) in prof])
    np_ = len(prof)
    last = n if closed else n - 1
    for i in range(last):
        a, b = rings[i], rings[(i + 1) % n]
        for j in range(np_):
            bm.faces.new((a[j], a[(j + 1) % np_], b[(j + 1) % np_], b[j]))
    if caps and not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return obj_from_bm(name, bm, mat, col)


# ---------------------------------------------------------------- tubes
def fillet_path(path, radius: float, segs: int = 4):
    pts = [Vector(p) for p in path]
    if len(pts) < 3 or radius <= 0:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        d0 = (p1 - p0)
        d1 = (p2 - p1)
        l0, l1 = d0.length, d1.length
        d0.normalize()
        d1.normalize()
        cosang = max(-1.0, min(1.0, d0.dot(d1)))
        theta = math.acos(cosang)
        if theta < 1e-3:
            out.append(p1)
            continue
        r = radius
        t = r * math.tan(theta / 2)
        lim = min(l0 if i == 1 else l0 / 2, l1 if i == len(pts) - 2 else l1 / 2) * 0.98
        if t > lim:
            t = lim
            r = t / math.tan(theta / 2)
        a = p1 - d0 * t
        nrm = (d1 - d0 * cosang).normalized()
        c = a + nrm * r
        axis = d0.cross(d1).normalized()
        va = a - c
        for k in range(segs + 1):
            q = Quaternion(axis, theta * k / segs)
            out.append(c + q @ va)
    out.append(pts[-1])
    # drop near-duplicates
    clean = [out[0]]
    for p in out[1:]:
        if (p - clean[-1]).length > 1e-5:
            clean.append(p)
    return clean


def tube(name: str, path, radius: float, sides: int = 10, fillet: float = 0.0, fillet_segs: int = 4,
         mat: str = "M_Steel_Dark", caps: bool = True, radii=None, closed: bool = False,
         col=None) -> bpy.types.Object:
    """Round tube along a 3D path (parallel-transport frames). `radii` optionally per path point
    (only used when fillet == 0)."""
    pts = fillet_path(path, fillet, fillet_segs) if fillet > 0 else [Vector(p) for p in path]
    n = len(pts)
    tans = []
    for i in range(n):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1])
        elif i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tans.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - tans[0] * ref.dot(tans[0])).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = (q @ nrm)
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        b = tans[i].cross(nrm)
        r = radii[i] if (radii is not None and fillet <= 0) else radius
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            ring.append(bm.verts.new(pts[i] + (nrm * math.cos(a) + b * math.sin(a)) * r))
        rings.append(ring)
    last = n if closed else n - 1
    for i in range(last):
        a, b2 = rings[i], rings[(i + 1) % n]
        for j in range(sides):
            bm.faces.new((a[j], a[(j + 1) % sides], b2[(j + 1) % sides], b2[j]))
    if caps and not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return obj_from_bm(name, bm, mat, col)


def loft(name: str, rings, mat: str = "M_Fabric", cap_start: bool = True, cap_end: bool = True,
         closed_rings: bool = True, col=None) -> bpy.types.Object:
    """Skin rings (lists of 3D points of equal length, ordered CCW looking along the loft
    direction) bottom->top."""
    bm = bmesh.new()
    vr = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    m = len(vr[0])
    for i in range(len(vr) - 1):
        a, b = vr[i], vr[i + 1]
        rng = m if closed_rings else m - 1
        for j in range(rng):
            bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
    if closed_rings:
        if cap_start:
            bm.faces.new(list(reversed(vr[0])))
        if cap_end:
            bm.faces.new(vr[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, mat, col)


def lathe_loop(name: str, loop, segments: int = 32, mat: str = "M_Brass_Aged", col=None) -> bpy.types.Object:
    """Revolve a CLOSED 2D loop [(r, z), ...] around Z (no caps) -> a solid shell such as a lamp
    shade with an outer and an inner surface. Points with r == 0 are allowed only as poles."""
    pts = ccw(dedupe(loop))   # CCW in (r, z) + this winding => outward normals (no recalc needed)
    bm = bmesh.new()
    rings = []
    for (r, z) in pts:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments),
                                    r * math.sin(2 * math.pi * i / segments), z)) for i in range(segments)])
    n = len(rings)
    for k in range(n):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(segments):
            bm.faces.new((a[i], a[(i + 1) % segments], b[(i + 1) % segments], b[i]))
    return obj_from_bm(name, bm, mat, col)


def subsurf(obj: bpy.types.Object, levels: int = 1) -> None:
    mod = obj.modifiers.new("subsurf", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    M.apply_modifiers(obj)


# ---------------------------------------------------------------- profiles (s = out from wall, u = up)
def profile_baseboard(h=0.16, t=0.022):
    """Skirting: flat face, ogee/bead cap; s = out of wall (0 = wall), u = up from floor."""
    pts = [(0.0, 0.0), (t, 0.0), (t, h - 0.035)]
    pts += arc(t - 0.008, h - 0.035, 0.008, 0, 90, 3)            # bead
    pts += [(t - 0.010, h - 0.027)]
    pts += arc(t - 0.010, h - 0.012, 0.015 * 0.6, -90, 0, 3)     # small cove up
    pts += [(t - 0.010 + 0.009 - 0.004, h), (0.0, h)]
    return pts


def profile_chair_rail(h=0.07, t=0.03):
    pts = [(0.0, 0.0), (0.012, 0.0)]
    pts += arc(0.012, 0.012, 0.012, -90, 0, 3)                     # cove under
    pts += [(0.024, 0.016)]
    pts += arc(0.024, 0.032, 0.016, -90, 90, 6)                    # torus bead
    pts += [(0.02, 0.048), (0.02, 0.054)]
    pts += arc(0.02, 0.062, 0.008, -90, 90, 3)
    pts += [(0.012, h - 0.004), (0.006, h), (0.0, h)]
    return pts


def profile_crown(h=0.15, p=0.14):
    """Crown/cornice: s out of wall, u measured DOWN from the ceiling is negative (u <= 0)."""
    pts = [(0.0, 0.0), (0.0, -h), (0.012, -h), (0.012, -h + 0.012)]
    pts += arc(0.022, -h + 0.022, 0.010, 180, 90, 2)
    pts += [(0.03, -h + 0.034)]
    pts += arc(0.03 + 0.07, -h + 0.034, 0.07, 180, 90, 6)         # big cove (concave)
    pts += [(0.105, -h + 0.110), (0.115, -h + 0.110)]
    pts += arc(0.115, -h + 0.122, 0.012, -90, 90, 3)              # top bead
    pts += [(0.118, -0.006), (p, -0.006), (p, 0.0)]
    return pts


def profile_casing(w=0.095, t=0.026):
    """Architrave: s = 0 at the opening edge -> w outwards; u = out of wall."""
    pts = [(0.0, 0.0), (0.0, t - 0.010)]
    pts += arc(0.008, t - 0.010, 0.008, 180, 90, 3)
    pts += [(0.014, t - 0.002), (0.03, t - 0.004), (0.05, t - 0.008), (0.062, t - 0.008)]
    pts += arc(0.072, t - 0.008, 0.010, 180, 0, 4)
    pts += [(0.084, t - 0.008)]
    pts += arc(0.088, t - 0.014, 0.007, 90, 0, 2)
    pts += [(w, t - 0.016), (w, 0.0)]
    return pts


def profile_panel_mould(w=0.026, t=0.014):
    """Small ogee panel moulding: s inward (towards panel centre), u = out of wall."""
    pts = [(0.0, 0.0), (0.0, t * 0.55)]
    pts += arc(0.006, t * 0.55, 0.006, 180, 90, 2)
    pts += [(0.010, t)]
    pts += arc(0.010 + 0.010, t, 0.010, 180, 270, 3)   # ogee
    pts += [(w, t - 0.010), (w, 0.0)]
    return pts


# ---------------------------------------------------------------- wall frames
class WallFrame:
    """A wall's interior plane. Local coords: x right along the wall (seen from the room),
    y into the wall (0 = wall face, negative = into the room), z up. Matches the convention of
    wall-mounted models (front faces local -Y)."""

    def __init__(self, origin, normal):
        self.n = Vector(normal).normalized()           # points into the room
        self.ux = Vector((0, 0, 1)).cross(self.n)       # right along the wall
        self.origin = Vector(origin)
        self.m = Matrix((
            (self.ux.x, -self.n.x, 0.0, self.origin.x),
            (self.ux.y, -self.n.y, 0.0, self.origin.y),
            (self.ux.z, -self.n.z, 1.0, self.origin.z),
            (0.0, 0.0, 0.0, 1.0)))

    def world(self, x, y, z):
        return self.m @ Vector((x, y, z))

    def local_x(self, world_point) -> float:
        return (Vector(world_point) - self.origin).dot(self.ux)


# ---------------------------------------------------------------- small hardware
def screw(name: str, r: float, loc, normal=(0, -1, 0), mat: str = "M_Brass_Aged", slot_angle: float = 0.0,
          segs: int = 8, col=None) -> bpy.types.Object:
    """Domed screw/rivet head (with a shallow slot) whose dome faces `normal`."""
    prof = [(r, 0.0), (r, r * 0.12), (r * 0.8, r * 0.38), (r * 0.42, r * 0.55), (0.0, r * 0.6)]
    o = M.lathe(name, prof, segments=segs, mat=mat, col=col)
    if slot_angle is not None:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        # pinch two opposite vertices on the top ring down a bit to fake a slot (keeps tris low)
        for v in bm.verts:
            if abs(v.co.z - r * 0.55) < 1e-6:
                a = math.atan2(v.co.y, v.co.x) - math.radians(slot_angle)
                if abs(math.sin(a)) < 0.2:
                    v.co.z -= r * 0.15
        bm.to_mesh(o.data)
        bm.free()
    z = Vector((0, 0, 1))
    q = z.rotation_difference(Vector(normal).normalized())
    o.data.transform(q.to_matrix().to_4x4())
    o.location = loc
    return o


def bevel_box(name, size, loc=(0, 0, 0), mat="M_Wood_Walnut", bevel=0.004, segments=2, rot=(0, 0, 0), col=None):
    return M.box(name, size, loc=loc, rot=rot, mat=mat, bevel=bevel, segments=segments, col=col)


def box_minmax(name, mn, mx, mat="M_Wood_Walnut", bevel=0.003, segments=1, col=None):
    """Bevelled box from min/max corners."""
    mn, mx = Vector(mn), Vector(mx)
    size = mx - mn
    c = (mn + mx) / 2
    return M.box(name, tuple(size), loc=tuple(c), mat=mat, bevel=bevel, segments=segments, col=col)


# ---------------------------------------------------------------- combination wheel
def combo_wheel(name: str, radius: float, width: float, chamfer: float = 0.0015, segments: int = 30,
                rim_mat: str = "M_Decal_DrawerDigits", side_mat: str = "M_Brass_Aged",
                digits: int = 10, col=None) -> bpy.types.Object:
    """Digit wheel with its axle along local X, origin at the axle centre.

    Rim UVs (decal strip, digit k centred at u = (k + 0.5) / digits) are laid out per digit sector
    so that every glyph is upright and not mirrored when it is at the FRONT (local -Y):
      * digit k occupies the sector centred at angle a_k = 180deg - k * 360/digits, where the
        angle is atan2(z, y) in the wheel's local frame (180deg = facing -Y = the viewer);
      * at rest digit 0 faces the viewer; rotating the wheel by +k*360/digits about local +X
        (Blender and Godot alike) brings digit k to the front.
    `segments` must be a multiple of `digits`.
    """
    assert segments % digits == 0
    step = 2 * math.pi / segments
    sector = 2 * math.pi / digits
    phi0 = sector / 2 - step * (int((sector / 2) / step))  # vertex on every sector boundary
    angles = [phi0 + j * step for j in range(segments)]
    hw = width / 2
    prof = [(-hw, radius - chamfer), (-hw + chamfer, radius), (hw - chamfer, radius), (hw, radius - chamfer)]
    bm = bmesh.new()
    rings = []
    for (x, r) in prof:
        rings.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for a in angles])
    faces_rim = []
    for k in range(len(rings) - 1):
        for j in range(segments):
            a, b = rings[k], rings[k + 1]
            f = bm.faces.new((a[j], b[j], b[(j + 1) % segments], a[(j + 1) % segments]))
            if k == 1:
                faces_rim.append(f)
    bm.faces.new(list(reversed(rings[0])))   # -X side
    bm.faces.new(rings[-1])                  # +X side
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rim_set = set(faces_rim)
    obj = M._new_obj(name, bm, col)
    obj.data.materials.append(M.material(side_mat))
    dec = M.material(rim_mat, image=os.path.join(DECALS, "drawer_digits.png"))
    obj.data.materials.append(dec)
    me = obj.data
    # rim faces are created in order: ring pair 1 holds the decal
    rim_idx = set(range(segments, 2 * segments))
    for p in me.polygons:
        p.material_index = 1 if p.index in rim_idx else 0
    _ = rim_set
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        if p.material_index != 1:
            continue
        cy = sum(me.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        cz = sum(me.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        ca = math.atan2(cz, cy)
        k = int(round((math.pi - ca) / sector)) % digits
        ak = math.pi - k * sector
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(co.z, co.y)
            while a - ak > math.pi:
                a -= 2 * math.pi
            while ak - a > math.pi:
                a += 2 * math.pi
            v = (ak + sector / 2 - a) / sector
            u = (k + (co.x + hw - chamfer) / (width - 2 * chamfer)) / digits
            uvl.data[li].uv = (u, v)
    return obj


# ---------------------------------------------------------------- export without PBR images
def export_lean(name: str, subdir: str = "") -> str:
    """Export a GLB whose materials carry only base factors (+ decal images). The CC0 PBR maps
    are applied in Godot through res://assets/materials/<slot>.tres, so embedding them would
    only bloat the GLB. Texture links are restored afterwards for the QA render."""
    saved = []
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.name.startswith("M_Decal_"):
            continue
        nt = mat.node_tree
        for lk in list(nt.links):
            if lk.from_node.type in ("TEX_IMAGE", "NORMAL_MAP", "SEPARATE_COLOR"):
                saved.append((mat, lk.from_node.name, lk.from_socket.identifier,
                              lk.to_node.name, lk.to_socket.identifier))
                nt.links.remove(lk)
    path = M.export_glb(name, subdir)
    for (mat, fn, fs, tn, ts) in saved:
        nt = mat.node_tree
        f, t = nt.nodes[fn], nt.nodes[tn]
        fsock = next(s for s in f.outputs if s.identifier == fs)
        tsock = next(s for s in t.inputs if s.identifier == ts)
        nt.links.new(fsock, tsock)
    return path


# ---------------------------------------------------------------- QA helpers
def qa_light(name, kind, loc, energy, color="FFFFFF", size=0.5, rot=None, target=None, spot=None):
    ld = bpy.data.lights.new("QA_" + name, kind)
    ld.energy = energy
    ld.color = M.hex_rgba(color)[:3]
    if kind == "AREA":
        ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "SUN":
        ld.angle = size
    if spot is not None and kind == "SPOT":
        ld.spot_size = spot
    lo = bpy.data.objects.new("QA_" + name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    if target is not None:
        M._look_at(lo, target)
    elif rot is not None:
        lo.rotation_euler = rot
    return lo


NO_LIGHTS = [((0, 0, 1), 0.0, "FFFFFF", 0.1)]
# Dimmer three-point rig than mrlib's default (which over-exposes dark walnut / enamel).
STUDIO = [((1.0, -1.2, 1.4), 330, "FFE2C0", 1.5),
          ((-1.4, -0.6, 0.8), 110, "BFD4FF", 2.0),
          ((0.2, 1.4, 1.6), 260, "FFFFFF", 1.0)]


def import_glb(path: str, loc=(0, 0, 0), rot_z_deg: float = 0.0, prefix: str = "QA_imp_"):
    """Import a GLB for a composite QA render; renames objects with a QA prefix so
    mrlib.render_preview removes them afterwards."""
    if not os.path.exists(path):
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None or o.parent not in new]
    holder = bpy.data.objects.new(prefix + os.path.basename(path), None)
    bpy.context.scene.collection.objects.link(holder)
    for r in roots:
        r.parent = holder
    holder.location = loc
    holder.rotation_euler = (0, 0, math.radians(rot_z_deg))
    for o in new:
        o.name = prefix + o.name
    return [holder] + new


def godot_to_blender(x, y, z):
    return (x, -z, y)


def render_setup(samples=64, bounces=6):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.samples = samples


# ================================================================ room-shell / joinery helpers
def prepare_tinted(name: str, folder: str, tint: str, rough: float | None = None) -> bpy.types.Material:
    """QA-preview material that reuses another CC0 texture folder multiplied by a tint
    (e.g. M_Plaster_Stained = plaster_wall x yellow-brown). Godot uses <name>.tres instead."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = M.material(name, color=tint, rough=rough)
    tex_dir = os.path.join(ROOT, "game", "assets", "textures", folder)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if os.path.isdir(tex_dir):
        M._attach_pbr(nt, bsdf, tex_dir)
        link = next((lk for lk in nt.links if lk.to_socket == bsdf.inputs["Base Color"]), None)
        if link is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            src = link.from_socket
            nt.links.remove(link)
            a_in = next(i for i in mix.inputs if i.name == "A" and i.type == "RGBA")
            b_in = next(i for i in mix.inputs if i.name == "B" and i.type == "RGBA")
            out = next(o for o in mix.outputs if o.type == "RGBA")
            nt.links.new(src, a_in)
            b_in.default_value = M.hex_rgba(tint)
            nt.links.new(out, bsdf.inputs["Base Color"])
    return mat


def frame_matrix(origin, ex, ey, ez) -> Matrix:
    """4x4 matrix whose columns are the given axes (local -> world)."""
    ex, ey, ez, o = Vector(ex), Vector(ey), Vector(ez), Vector(origin)
    return Matrix(((ex.x, ey.x, ez.x, o.x), (ex.y, ey.y, ez.y, o.y), (ex.z, ey.z, ez.z, o.z), (0, 0, 0, 1)))


def raised_field(name: str, a0: float, a1: float, b0: float, b1: float, inset: float, rise: float,
                 matrix: Matrix, mat: str = "M_Wood_Panel", both: bool = False, half_t: float = 0.0,
                 col=None) -> bpy.types.Object:
    """Raised (fielded) panel: flat field + four sloped bevels, built in a local plane (a = right,
    b = up, +z = out of the surface) and transformed by `matrix`. Open at the back (it sits on a
    backing board) unless `both`, in which case it is a closed double-sided panel of thickness
    2 * half_t + 2 * rise (for doors)."""
    bm = bmesh.new()

    def ring(z, ins):
        return [bm.verts.new((a0 + ins, b0 + ins, z)), bm.verts.new((a1 - ins, b0 + ins, z)),
                bm.verts.new((a1 - ins, b1 - ins, z)), bm.verts.new((a0 + ins, b1 - ins, z))]
    base = ring(half_t, 0.0)
    top = ring(half_t + rise, inset)
    for i in range(4):
        bm.faces.new((base[i], base[(i + 1) % 4], top[(i + 1) % 4], top[i]))
    bm.faces.new(top)
    if both:
        bbase = ring(-half_t, 0.0)
        btop = ring(-half_t - rise, inset)
        for i in range(4):
            bm.faces.new((bbase[(i + 1) % 4], bbase[i], btop[i], btop[(i + 1) % 4]))
        bm.faces.new(list(reversed(btop)))
        if half_t > 0:
            for i in range(4):
                bm.faces.new((bbase[i], bbase[(i + 1) % 4], base[(i + 1) % 4], base[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, mat, col)
    o.data.transform(matrix)
    return o


def rect_path(matrix: Matrix, a0: float, a1: float, b0: float, b1: float, z: float = 0.0):
    """CCW rectangle (seen from +z of the local frame) as world points, for closed sweeps."""
    return [tuple(matrix @ Vector(p)) for p in ((a0, b0, z), (a1, b0, z), (a1, b1, z), (a0, b1, z))]


def offset_pts(pts, d):
    return [tuple(Vector(p) + Vector(d)) for p in pts]


def catmull(points, sub: int = 4):
    """Catmull-Rom resample of a 3D polyline (keeps the end points)."""
    pts = [Vector(p) for p in points]
    if len(pts) < 3:
        return pts
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def resample_radii(points, radii, sub: int = 4):
    """Linear resample of per-point radii to match catmull(points, sub)."""
    out = []
    for i in range(len(radii) - 1):
        for k in range(sub):
            out.append(radii[i] + (radii[i + 1] - radii[i]) * k / sub)
    out.append(radii[-1])
    return out


def delete_faces(obj: bpy.types.Object, pred) -> None:
    """Delete faces whose world centre / normal satisfy pred(center, normal) (hidden faces)."""
    M.refresh()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    dead = [f for f in bm.faces if pred(mw @ f.calc_center_median(), (rot @ f.normal).normalized())]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def qa_reset_render_objects() -> None:
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA")]:
        bpy.data.objects.remove(o, do_unlink=True)


def text_lowpoly(name: str, text: str, size: float, depth: float = 0.0, loc=(0, 0, 0), rot=(0, 0, 0),
                 mat: str = "M_Brass_Polished", font_path: str | None = None, resolution: int = 2,
                 align: str = "CENTER", col=None) -> bpy.types.Object:
    """Like mrlib.text_mesh but with a low curve resolution and limited-dissolve cleanup, so sign
    lettering / labels stay cheap (a glyph ~ 20-60 tris instead of several hundred)."""
    curve = bpy.data.curves.new(name + "_txt", "FONT")
    curve.body = text
    curve.size = size
    curve.extrude = depth
    curve.resolution_u = resolution
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.fill_mode = "BOTH" if depth > 0 else "FRONT"
    if font_path and os.path.exists(font_path):
        curve.font = bpy.data.fonts.load(font_path, check_existing=True)
    tmp = bpy.data.objects.new(name + "_tmp", curve)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(curve)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=size * 1e-4)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.0), verts=bm.verts, edges=bm.edges)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    M.assign(obj, mat)
    return obj


WOOD_SLOTS = ("M_Wood_Walnut", "M_Wood_Mahogany", "M_Wood_Panel")


def grain_uv(obj: bpy.types.Object, slots=WOOD_SLOTS, ratio: float = 1.15, force=None) -> int:
    """Run the wood grain along each member: after box_uv the grain (texture U) is horizontal,
    so faces that are clearly longer along their V axis (stiles, legs, jambs, mullions) get their
    UVs rotated 90 deg. `force(center, normal)` -> True/False/None overrides per face (e.g. to give
    a whole raised panel vertical grain). Call after mrlib.finalize(). Returns rotated face count."""
    me = obj.data
    if not me.uv_layers:
        return 0
    uvl = me.uv_layers.active
    M.refresh()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    names = [m.name if m else "" for m in me.materials]
    count = 0
    for p in me.polygons:
        if names[p.material_index] not in slots:
            continue
        n = (rot @ p.normal).normalized()
        c = mw @ p.center
        f = force(c, n) if force else None
        if f is None:
            ax = max(range(3), key=lambda i: abs(n[i]))
            ua, va = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[ax]
            pts = [mw @ me.vertices[v].co for v in p.vertices]
            eu = max(q[ua] for q in pts) - min(q[ua] for q in pts)
            ev = max(q[va] for q in pts) - min(q[va] for q in pts)
            f = ev > ratio * eu
        if f:
            for li in p.loop_indices:
                u, v = uvl.data[li].uv
                uvl.data[li].uv = (v, -u)
            count += 1
    return count
