"""Extra helpers for the prop scripts (bookshelf, lab bench, chalkboard, poster, desk lamp,
evidence board, shadow lock). Builds on mrlib (never edit mrlib — it is shared).

Usage inside tools/blender/models/<name>.py:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import mrlib as M
    import lib_props as P
"""
from __future__ import annotations

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import mrlib as M

DECALS = os.path.join(M.ROOT, "game", "assets", "textures", "decals")
FONT_SERIF_BOLD = next((p for p in (
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
) if os.path.exists(p)), None)

# Preview colours for the new material slots, matching game/assets/materials/*.tres
# (Godot replaces them by name). name: (base colour hex, roughness, metallic, texture folder or None)
EXTRA = {
    "M_Book_Red": ("7A2420", 0.65, 0.0, "leather"),
    "M_Book_Green": ("26402C", 0.65, 0.0, "leather"),
    "M_Book_Brown": ("5A3A24", 0.65, 0.0, "leather"),
    "M_Book_Blue": ("243A5A", 0.65, 0.0, "leather"),
    "M_Book_Black": ("2A2522", 0.65, 0.0, "leather"),
    "M_Book_Gold": ("E3C27A", 0.3, 1.0, None),
    "M_Cork": ("9C7650", 0.95, 0.0, None),
    "M_String_Red": ("A0201C", 0.8, 0.0, None),
    "M_Felt": ("3A3A3A", 1.0, 0.0, None),
}


def _tinted(name, colour, rough, metal, folder, uv_scale=3.0):
    """Material = texture albedo x colour (like StandardMaterial3D albedo_texture * albedo_color)."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = M.material(name, color=colour, rough=rough, metal=metal)
    tdir = os.path.join(M.ROOT, "game", "assets", "textures", folder) if folder else None
    alb = os.path.join(tdir, "albedo.jpg") if tdir else None
    if not alb or not os.path.exists(alb):
        return mat
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(alb, check_existing=True)
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = M.hex_rgba(colour)
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    nrm = os.path.join(tdir, "normal.png")
    if os.path.exists(nrm):
        nt_img = nt.nodes.new("ShaderNodeTexImage")
        nt_img.image = bpy.data.images.load(nrm, check_existing=True)
        nt_img.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], nt_img.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nt_img.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def init_materials() -> None:
    """Create preview versions of the extra M_* slots (call right after mrlib.reset_scene())."""
    for name, (c, r, m, folder) in EXTRA.items():
        _tinted(name, c, r, m, folder)
    for colour in ("Crimson", "Cobalt", "Green"):
        M.material(f"M_Decal_VialLabel_{colour}", color="E8DFC8", rough=0.85,
                   image=os.path.join(DECALS, f"vial_label_{colour.lower()}.png"))
    M.material("M_Decal_Chalkboard", color="1E2421", rough=0.92,
               image=os.path.join(DECALS, "chalkboard.jpg"))
    M.material("M_Decal_Poster", color="D9CBB0", rough=0.85,
               image=os.path.join(DECALS, "poster_resonance.jpg"))
    photo = os.path.join(DECALS, "photo_0.jpg")
    mat = M.material("M_Decal_Photos", color="D8D0C0", rough=0.6, image=photo if os.path.exists(photo) else None)
    if not os.path.exists(photo):
        _attach_photo_preview(mat)


def photo_preview_material(k: int):
    """Preview-only per-card photo material (photo_k.jpg) — used after export for QA renders."""
    path = os.path.join(DECALS, f"photo_{k}.jpg")
    return M.material(f"QA_Photo_{k}", color="D8D0C0", rough=0.6, image=path if os.path.exists(path) else None)


def _attach_photo_preview(mat) -> None:
    """In-memory sepia photo placeholder (only if no photo texture exists)."""
    w, h = 140, 172
    img = bpy.data.images.new("photo_preview", w, h)
    px = []
    for y in range(h):
        v = y / (h - 1)
        for x in range(w):
            u = x / (w - 1)
            if u < 0.05 or u > 0.95 or v < 0.04 or v > 0.96:
                px += [0.82, 0.79, 0.72, 1.0]
                continue
            g = max(0.03, (0.35 + 0.35 * v) * (1 - 0.5 * ((u - 0.5) ** 2 + (v - 0.5) ** 2)))
            px += [g, g * 0.82, g * 0.6, 1.0]
    img.pixels = px
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])


# ---------------------------------------------------------------- generic mesh helpers
def mesh_obj(name, verts, faces, mats, face_mats=None, col=None):
    """Object from raw verts/faces. `mats` = list of material names, `face_mats` = per-face index."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    for m in mats:
        me.materials.append(M.material(m))
    if face_mats:
        for p, i in zip(me.polygons, face_mats):
            p.material_index = i
    return obj


def bm_obj(name, bm, mats, col=None):
    """Object from a bmesh whose faces already carry material_index into `mats`."""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    for m in mats:
        me.materials.append(M.material(m))
    return obj


def fix_normals(obj) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def bezier(p0, p1, p2, p3, n: int):
    p0, p1, p2, p3 = (Vector(p) for p in (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t ** 2
        d = t ** 3
        out.append(p0 * a + p1 * b + p2 * c + p3 * d)
    return out


def tube(name, pts, radius, sides: int = 8, mat: str = "M_Rubber", caps: bool = True,
         radii=None, col=None, twist: float = 0.0):
    """Sweep a circle along a polyline (parallel-transport frames). Hoses, cables, rods, strings."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tans.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tans[0].cross(ref).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            nrm = (tans[i - 1].rotation_difference(tans[i]) @ nrm).normalized()
        b = tans[i].cross(nrm).normalized()
        r = radii[i] if radii else radius
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides + twist
            ring.append(bm.verts.new(pts[i] + (nrm * math.cos(a) + b * math.sin(a)) * r))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_obj(name, bm, [mat], col)


def rod(name, a, b, radius, sides: int = 12, mat: str = "M_Brass_Aged", bevel: float = 0.0008):
    """Straight cylinder between two points (bevelled caps)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    obj = M.cylinder(name, radius, d.length, loc=(a + b) / 2, verts=sides, mat=mat, bevel=bevel, segments=1)
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def shell_profile(outer, t: float, lip: float | None = None):
    """Closed lathe profile with wall thickness `t` from an outer profile [(r, z)...]
    that starts on the axis at the bottom (r = 0) and ends at the rim. Adds a rounded lip."""
    inner = []
    n = len(outer)
    for i, (r, z) in enumerate(outer):
        if i == 0:
            dr, dz = outer[1][0] - r, outer[1][1] - z
        elif i == n - 1:
            dr, dz = r - outer[i - 1][0], z - outer[i - 1][1]
        else:
            dr, dz = outer[i + 1][0] - outer[i - 1][0], outer[i + 1][1] - outer[i - 1][1]
        ln = math.hypot(dr, dz) or 1.0
        nx, nz = -dz / ln, dr / ln
        inner.append((max(0.0, r + nx * t), z + nz * t))
    inner[0] = (0.0, inner[0][1])
    rr, zz = outer[-1]
    ir, iz = inner[-1]
    lip = t * 0.55 if lip is None else lip
    lip_pts = [((rr * 0.75 + ir * 0.25), zz + lip * 0.8), ((rr * 0.25 + ir * 0.75), iz + lip * 0.8)]
    return list(outer) + lip_pts + list(reversed(inner))


def solid_profile(outer):
    """Closed lathe profile for a solid of revolution (liquids, stoppers)."""
    return list(outer)


def rim_edit(obj, angle: float, width: float, z_from: float, dz: float = 0.0, dr: float = 0.0,
             jag: float = 0.0, seed: int = 1) -> None:
    """Deform lathe vertices above `z_from` near `angle` (radians, local XY): push the rim
    down (chip) by `dz` or out (spout) by `dr`, with a cosine falloff over `width` radians."""
    rnd = random.Random(seed)
    me = obj.data
    for v in me.vertices:
        if v.co.z < z_from:
            continue
        a = math.atan2(v.co.y, v.co.x)
        d = abs((a - angle + math.pi) % (2 * math.pi) - math.pi)
        if d > width:
            continue
        f = 0.5 * (1 + math.cos(math.pi * d / width))
        r = math.hypot(v.co.x, v.co.y)
        if dr and r > 1e-6:
            k = (r + dr * f) / r
            v.co.x *= k
            v.co.y *= k
            v.co.z += abs(dr) * 0.35 * f
        if dz:
            v.co.z -= dz * f * (1 + jag * rnd.uniform(-1, 1))
    me.update()


# ---------------------------------------------------------------- frames, panels, mouldings
def frame_sweep(name, w, h, profile, mat="M_Wood_Walnut", loc=(0, 0, 0), fill_first=False,
                fill_last=False, mats=None, ring_mats=None, col=None):
    """Rectangular mitred frame/moulding in the XZ plane (front faces -Y).

    `profile` = [(inset, depth), ...]: inset from the outer edge (m), depth toward -Y from the
    back plane Y = 0. A closed profile loop gives a picture frame; with fill_last the innermost
    ring is capped (raised panels, drawer fronts). Rings are joined consecutively (and cyclically
    unless fill_first/fill_last)."""
    bm = bmesh.new()
    rings = []
    for (s, p) in profile:
        hx, hz = w / 2 - s, h / 2 - s
        rings.append([bm.verts.new((x, -p, z)) for (x, z) in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz))])
    n = len(rings)
    cyclic = not (fill_first or fill_last)
    face_idx = []
    for i in range(n if cyclic else n - 1):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(4):
            f = bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
            f.material_index = ring_mats[i] if ring_mats else 0
    if fill_first:
        bm.faces.new(list(reversed(rings[0])))
    if fill_last:
        f = bm.faces.new(rings[-1])
        f.material_index = ring_mats[-1] if ring_mats else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = bm_obj(name, bm, mats or [mat], col)
    obj.location = loc
    return obj


def ogee(x0, y0, x1, y1, n=6):
    """Points of an S-curve (cyma) from (x0, y0) to (x1, y1) for moulding profiles."""
    pts = []
    for i in range(n + 1):
        t = i / n
        s = 0.5 - 0.5 * math.cos(math.pi * t)
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * s))
    return pts


def arc(cx, cy, r, a0, a1, n=6):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def moulding(name, profile_yz, length, loc=(0, 0, 0), rot=(0, 0, 0), mat="M_Wood_Walnut",
             miter_left=False, miter_right=False, col=None):
    """Straight moulding run along X: `profile_yz` is a closed polygon [(y, z)] (y = projection
    toward -Y, use negative values for forward). Ends can be mitred 45 degrees (for returns)."""
    bm = bmesh.new()
    left, right = [], []
    for (y, z) in profile_yz:
        # mitre: the forward-projecting part (more negative y) is longer on mitred ends
        # `length` is measured along the back plane (y = 0); mitred ends grow by the projection
        xl = -length / 2 - ((-y) if miter_left else 0.0)
        xr = length / 2 + ((-y) if miter_right else 0.0)
        left.append(bm.verts.new((xl, y, z)))
        right.append(bm.verts.new((xr, y, z)))
    n = len(profile_yz)
    for i in range(n):
        bm.faces.new((left[i], left[(i + 1) % n], right[(i + 1) % n], right[i]))
    bm.faces.new(list(reversed(left)))
    bm.faces.new(right)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = bm_obj(name, bm, [mat], col)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def raised_panel(name, w, h, t, field_inset=0.03, raise_=0.006, mat="M_Wood_Walnut", loc=(0, 0, 0),
                 edge_round=0.003, col=None):
    """Door / drawer front: slab of thickness t (back at Y=0, front at -t) with a fielded
    (raised, chamfered) centre panel, all one mesh."""
    e = edge_round
    prof = [
        (0.0, 0.0), (0.0, t - e), (e * 0.3, t - e * 0.3), (e, t),           # rounded outer edge
        (field_inset, t),                                                      # flat margin
        (field_inset + 0.012, t + raise_ * 0.75), (field_inset + 0.016, t + raise_),  # chamfer up
    ]
    return frame_sweep(name, w, h, prof, mat=mat, loc=loc, fill_first=True, fill_last=True, col=col)


# ---------------------------------------------------------------- text
def text(name, body, size, loc=(0, 0, 0), rot=(0, 0, 0), mat="M_Book_Gold", depth=0.0,
         font=None, resolution: int = 3, align="CENTER", max_width: float | None = None, col=None):
    """Geometry text (flat when depth = 0) with controllable curve resolution; optional
    horizontal squeeze to `max_width`. Local text plane = XY, facing +Z (rotate to place)."""
    curve = bpy.data.curves.new(name + "_txt", "FONT")
    curve.body = body
    curve.size = size
    curve.extrude = depth
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.resolution_u = resolution
    if font and os.path.exists(font):
        curve.font = bpy.data.fonts.load(font, check_existing=True)
    tmp = bpy.data.objects.new(name + "_tmp", curve)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(curve)
    if max_width and me.vertices:
        xs = [v.co.x for v in me.vertices]
        wdt = max(xs) - min(xs)
        if wdt > max_width:
            k = max_width / wdt
            for v in me.vertices:
                v.co.x *= k
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    M.assign(obj, mat)
    return obj


# ---------------------------------------------------------------- books
def spine_y(x, t, rb):
    """Spine front curve (y toward the back, 0 at the apex) for a book of thickness t."""
    s = max(-1.0, min(1.0, x / (t / 2)))
    a = math.asin(s)
    return rb * (1 - math.cos(a))


def book(name, t, h, d, cover="M_Book_Red", deco=None, rb=None, cover_th=0.0025, squares=0.003,
         arc_pts=6, col=None):
    """Hardback book, local frame: x in [-t/2, t/2] (thickness), y in [0, d] (y = 0 = spine apex,
    +Y toward the fore-edge), z in [0, h]. Rounded spine, C-shaped case + inset page block.

    deco: list of ("band", z, height, mat) flat spine bands, ("raised", z, height, mat) raised bands,
          ("label", z0, z1, mat) spine label patches."""
    rb = min(0.0045, t * 0.11) if rb is None else rb
    c = min(cover_th, t * 0.12)
    s = 0.0018
    bm = bmesh.new()
    pts = []
    for i in range(arc_pts + 1):
        a = -math.pi / 2 + math.pi * i / arc_pts
        pts.append(((t / 2) * math.sin(a), rb * (1 - math.cos(a))))
    pts += [(t / 2, d), (t / 2 - c, d), (t / 2 - c, rb + s), (-t / 2 + c, rb + s), (-t / 2 + c, d), (-t / 2, d)]
    bot = [bm.verts.new((x, y, 0.0)) for (x, y) in pts]
    top = [bm.verts.new((x, y, h)) for (x, y) in pts]
    n = len(pts)
    for i in range(n):
        f = bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
        f.material_index = 0
    bm.faces.new(list(reversed(bot))).material_index = 0
    bm.faces.new(top).material_index = 0
    # page block
    x0, x1 = -t / 2 + c + 0.0002, t / 2 - c - 0.0002
    y0, y1 = rb + s, d - squares
    z0, z1 = squares, h - squares
    pv = [bm.verts.new(v) for v in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (1, 2, 6, 5), (3, 0, 4, 7), (2, 3, 7, 6)):
        bm.faces.new([pv[i] for i in f]).material_index = 1
    mats = [cover, "M_Paper"]
    for item in (deco or []):
        kind = item[0]
        mname = item[-1]
        if mname not in mats:
            mats.append(mname)
        mi = mats.index(mname)
        if kind in ("band", "label"):
            if kind == "band":
                za, zb = item[1] - item[2] / 2, item[1] + item[2] / 2
            else:
                za, zb = item[1], item[2]
            off = 0.00035
            row_a, row_b = [], []
            for i in range(arc_pts + 1):
                a = -math.pi / 2 + math.pi * i / arc_pts
                x = (t / 2 + off) * math.sin(a)
                y = rb * (1 - math.cos(a)) - off * math.cos(a)
                row_a.append(bm.verts.new((x, y, za)))
                row_b.append(bm.verts.new((x, y, zb)))
            for i in range(arc_pts):
                bm.faces.new((row_a[i], row_a[i + 1], row_b[i + 1], row_b[i])).material_index = mi
        elif kind == "raised":
            zc, bh = item[1], item[2]
            prof = [(0.0, zc - bh / 2), (0.0014, zc), (0.0, zc + bh / 2)]
            rows = []
            for (off, z) in prof:
                row = []
                for i in range(arc_pts + 1):
                    a = -math.pi / 2 + math.pi * i / arc_pts
                    x = (t / 2 + off * 0.6) * math.sin(a)
                    y = rb * (1 - math.cos(a)) - (off + 0.0002) * math.cos(a)
                    row.append(bm.verts.new((x, y, z)))
                rows.append(row)
            for j in range(len(rows) - 1):
                for i in range(arc_pts):
                    bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i])).material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_obj(name, bm, mats, col)


def conform_to_spine(obj, t, rb, lift=0.0005) -> None:
    """Bend a flat text object onto the rounded spine of a book built by `book()` at the origin
    (book-local frame: x across the spine, y = 0 at the apex). Bakes the object transform."""
    M.apply_transform(obj)
    for v in obj.data.vertices:
        v.co.y = spine_y(v.co.x, t, rb) - lift
    obj.data.update()


# ---------------------------------------------------------------- QA helpers
def preview_tweak() -> None:
    """Make QA renders closer to the Godot look (call AFTER export): real glass/liquids
    in Cycles, subtle wood grain. Never affects the exported .glb."""
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        n = mat.name
        if n in ("M_Glass", "M_Crystal", "M_Glass_Frosted") or n.startswith("M_Liquid_"):
            bsdf.inputs["Alpha"].default_value = 1.0
            bsdf.inputs["Transmission Weight"].default_value = 1.0
            bsdf.inputs["IOR"].default_value = 1.45 if not n.startswith("M_Liquid") else 1.34
            bsdf.inputs["Roughness"].default_value = 0.03 if n != "M_Glass_Frosted" else 0.35
            if n == "M_Glass":
                bsdf.inputs["Base Color"].default_value = M.hex_rgba("F2FAF6")
            if n.startswith("M_Liquid_"):
                c = M.PREVIEW[n][0]
                bsdf.inputs["Base Color"].default_value = M.hex_rgba(c)
        if n in ("M_Wood_Walnut", "M_Wood_Panel", "M_Wood_Mahogany"):
            nt = mat.node_tree
            if any(nd.type == "TEX_IMAGE" for nd in nt.nodes):
                continue
            base = bsdf.inputs["Base Color"].default_value[:]
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (1.0, 1.0, 9.0)
            wave = nt.nodes.new("ShaderNodeTexWave")
            wave.inputs["Scale"].default_value = 3.0
            wave.inputs["Distortion"].default_value = 6.0
            wave.inputs["Detail"].default_value = 3.0
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = tuple(c * 0.62 for c in base[:3]) + (1.0,)
            ramp.color_ramp.elements[1].color = tuple(min(1.0, c * 1.25) for c in base[:3]) + (1.0,)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
            nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def shots(name, views, args, samples: int = 48, res=(960, 640)) -> None:
    """Render QA views [(suffix, cam_loc, target, lens), ...] unless --no-render."""
    if "--no-render" in args:
        return
    preview_tweak()
    bpy.context.scene.cycles.max_bounces = 12
    bpy.context.scene.cycles.transmission_bounces = 12
    bpy.context.scene.cycles.transparent_max_bounces = 16
    for (suffix, cam, target, lens) in views:
        M.render_preview(name + suffix, cam, target, lens=lens, samples=samples, res=res)


def report(name) -> None:
    """Print tris, dims and object list for the docs."""
    objs = [o for o in bpy.context.scene.objects if o.type in ("MESH", "EMPTY")]
    M.refresh()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    print(f"[props] {name}: tris={M.tri_count()} bbox_blender min={tuple(round(c, 3) for c in lo)} "
          f"max={tuple(round(c, 3) for c in hi)} size={tuple(round(c, 3) for c in (hi - lo))}")
    for o in sorted(objs, key=lambda o: o.name):
        mw = o.matrix_world
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons) if o.type == "MESH" else 0
        print(f"[props]   {o.name:28s} {o.type:5s} tris={tris:5d} origin={tuple(round(c, 4) for c in mw.translation)} "
              f"parent={o.parent.name if o.parent else '-'} mats={[m.name for m in o.data.materials] if o.type == 'MESH' else ''}")


# ================================================================ room-coordinate, export and QA helpers
# (shadow lock, darkroom props, chalkboard, poster, desk lamp, evidence board, Strand echo)
def gd(x, y, z) -> Vector:
    """Godot room coordinates -> Blender (x, -z, y)."""
    return Vector((x, -z, y))


def export_lean(name: str) -> str:
    """mrlib.export_glb without embedded images: Godot swaps every material by slot name, and
    the QA preview textures would otherwise bloat the GLB by megabytes."""
    os.makedirs(M.MODELS_DIR, exist_ok=True)
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=False, export_apply=True, export_yup=True,
        export_materials="EXPORT", export_image_format="NONE", export_cameras=False, export_lights=False,
        export_extras=True)
    print(f"[props] exported {path} ({M.tri_count()} tris, {os.path.getsize(path) // 1024} KB)")
    return path


def alpha_decal_material(name: str, image: str, color: str = "FFFFFF", rough: float = 0.9):
    """Decal preview material whose texture alpha cuts the surface (painted emblem, stencils)."""
    mat = M.material(name, color=color, rough=rough, image=image)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for nd in nt.nodes:
        if nd.type == "TEX_IMAGE":
            nt.links.new(nd.outputs["Alpha"], bsdf.inputs["Alpha"])
            break
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    return mat


def lathe_axis(name, profile, axis: str = "Y", sign: float = 1.0, segments: int = 32,
               mat: str = "M_Brass_Aged", loc=(0, 0, 0), rot=(0, 0, 0)):
    """mrlib.lathe whose revolution axis (profile z) is baked onto local +/-X, +/-Y or Z."""
    o = M.lathe(name, profile, segments=segments, mat=mat)
    if axis == "Y":
        o.data.transform(Matrix.Rotation(-sign * math.pi / 2, 4, "X"))
    elif axis == "X":
        o.data.transform(Matrix.Rotation(sign * math.pi / 2, 4, "Y"))
    elif sign < 0:
        o.data.transform(Matrix.Rotation(math.pi, 4, "X"))
    o.location = loc
    o.rotation_euler = rot
    return o


def tapered_leg(name, top: float, bottom: float, h: float, loc=(0, 0, 0), mat: str = "M_Wood_Walnut",
                bevel: float = 0.003, foot_inset=(0.0, 0.0)):
    """Square leg tapering from `top` to `bottom` (side length) over height h; base at loc z.
    foot_inset shifts the foot (x, y) so the taper happens on the inner faces only."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.x = v.co.x * bottom + foot_inset[0]
            v.co.y = v.co.y * bottom + foot_inset[1]
        else:
            v.co.x *= top
            v.co.y *= top
        v.co.z = (v.co.z + 0.5) * h
    M._bevel_bm(bm, bevel, 1)
    obj = M._new_obj(name, bm)
    obj.location = loc
    M.assign(obj, mat)
    return obj


def qa_material(name: str, colour: str, rough: float = 0.85):
    """QA-only material (lower-case qa_ names survive mrlib.render_preview's QA cleanup)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = M.material(name, color=colour, rough=rough)
    return mat


def qa_box(name: str, size, loc, colour: str = "B8B2A0", rough: float = 0.9):
    """Plain proxy geometry for QA renders (walls, floor). Call after export."""
    o = M.box(name, size, loc=loc, mat="M_Plaster_Wall", bevel=0.0)
    o.data.materials.clear()
    o.data.materials.append(qa_material("qa_" + colour, colour, rough))
    return o


def qa_light(name: str, kind: str, loc, energy: float, colour: str = "FFFFFF", radius: float = 0.05,
             direction=None, half_angle_deg: float = 30.0, blend: float = 0.2):
    """QA-only Cycles light (lower-case name so it survives between renders)."""
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = M.hex_rgba(colour)[:3]
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = radius
    if kind == "SPOT":
        ld.spot_size = math.radians(2 * half_angle_deg)
        ld.spot_blend = blend
    if kind == "AREA":
        ld.size = radius
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    if direction is not None:
        lo.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    return lo


def render_threads(n: int = 2) -> None:
    """The QA farm is shared by several agents: cap Cycles threads."""
    r = bpy.context.scene.render
    r.threads_mode = "FIXED"
    r.threads = n


def rrect_ring(w: float, d: float, r: float, n: int = 4):
    """Counter-clockwise rounded rectangle (x = width, y = depth) with n points per corner."""
    r = max(1e-5, min(r, w / 2 - 1e-5, d / 2 - 1e-5))
    pts = []
    for (cx, cy, a0) in ((w / 2 - r, -d / 2 + r, -math.pi / 2), (w / 2 - r, d / 2 - r, 0.0),
                         (-w / 2 + r, d / 2 - r, math.pi / 2), (-w / 2 + r, -d / 2 + r, math.pi)):
        for i in range(n):
            a = a0 + (math.pi / 2) * i / max(1, n - 1)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rrect_loft(name: str, rings, mat: str = "M_Brass_Aged", n: int = 4, loc=(0, 0, 0), cap_bottom: bool = True,
               cap_top: bool = True, ring_mats=None):
    """Stepped/moulded solid from rounded-rect cross-sections [(w, d, corner_r, z), ...] bottom to top
    (lamp bases, plinths, trays). ring_mats[i] = material name for the band between ring i and i+1."""
    bm = bmesh.new()
    loops = [[bm.verts.new((x, y, z)) for (x, y) in rrect_ring(w, d, r, n)] for (w, d, r, z) in rings]
    mats = [mat] + [m for m in (ring_mats or []) if m and m != mat]
    mats = list(dict.fromkeys(mats))
    m = len(loops[0])
    for i in range(len(loops) - 1):
        a, b = loops[i], loops[i + 1]
        mi = mats.index(ring_mats[i]) if ring_mats and i < len(ring_mats) and ring_mats[i] else 0
        for k in range(m):
            f = bm.faces.new((a[k], a[(k + 1) % m], b[(k + 1) % m], b[k]))
            f.material_index = mi
    if cap_bottom:
        bm.faces.new(list(reversed(loops[0])))
    if cap_top:
        bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = bm_obj(name, bm, mats)
    obj.location = loc
    return obj


def flat_text_strips(name, x0, z0, width, rows, row_h=0.0016, gap=0.0042, y=0.0, mat="M_Fabric", seed=1,
                     headline=None):
    """Fake printed text: thin strips (one quad per line, ragged right) facing -Y, for newspapers/notes.
    headline = (height, n_lines) for bold lines on top. Returns the object."""
    rnd = random.Random(seed)
    verts, faces = [], []
    z = z0

    def strip(xa, xb, za, zb):
        i = len(verts)
        verts.extend([(xa, y, za), (xb, y, za), (xb, y, zb), (xa, y, zb)])
        faces.append((i, i + 1, i + 2, i + 3))

    if headline:
        hh, hn = headline
        for _ in range(hn):
            strip(x0, x0 + width * rnd.uniform(0.7, 1.0), z - hh, z)
            z -= hh + gap * 0.9
    for k in range(rows):
        frac = rnd.uniform(0.82, 1.0) if k % 5 != 4 else rnd.uniform(0.3, 0.6)
        strip(x0, x0 + width * frac, z - row_h, z)
        z -= row_h + gap
    obj = mesh_obj(name, verts, faces, [mat])
    fix_normals(obj)
    if obj.data.polygons and obj.data.polygons[0].normal.y > 0:
        obj.data.flip_normals()
    return obj
