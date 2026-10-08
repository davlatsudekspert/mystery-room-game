"""MYSTERY ROOM — shared Blender helper library for procedural modelling.

Run model scripts headless:
    blender -b --factory-startup -P tools/blender/models/<name>.py

Conventions (see docs/ART_DIRECTION.md):
  * 1 Blender unit = 1 m, Z-up in Blender (glTF export converts to Godot Y-up).
  * Material slots are named M_* and replaced in Godot by res://assets/materials/<name>.tres.
    Preview colours here are only for Blender QA renders.
  * UVs: world-scale box projection, 1 UV unit = 1 m, unless a decal material (M_Decal_*) is used,
    in which case the caller sets 0..1 UVs explicitly.
  * Interactive parts are separate objects named IA_<id> with their origin at the pivot.
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(ROOT, "game", "assets", "models")
QA_DIR = os.path.join(ROOT, "qa", "blender")

# name: (base colour sRGB hex, roughness, metallic, emission hex or None, alpha)
PREVIEW = {
    "M_Wood_Walnut": ("3B2416", 0.45, 0.0, None, 1.0),
    "M_Wood_Mahogany": ("5A2E1B", 0.4, 0.0, None, 1.0),
    "M_Wood_Floor": ("4A3020", 0.6, 0.0, None, 1.0),
    "M_Wood_Panel": ("442A1A", 0.5, 0.0, None, 1.0),
    "M_Plaster_Wall": ("B8B2A0", 0.9, 0.0, None, 1.0),
    "M_Ceiling": ("A9A493", 0.95, 0.0, None, 1.0),
    "M_Stone": ("8A8579", 0.8, 0.0, None, 1.0),
    "M_Brass_Aged": ("B08D57", 0.35, 1.0, None, 1.0),
    "M_Brass_Polished": ("E3C27A", 0.2, 1.0, None, 1.0),
    "M_Steel_Painted": ("4F5D55", 0.55, 0.2, None, 1.0),
    "M_Steel_Dark": ("2A2B2D", 0.5, 0.9, None, 1.0),
    "M_Chrome": ("D8D8D8", 0.12, 1.0, None, 1.0),
    "M_Copper": ("B4643C", 0.35, 1.0, None, 1.0),
    "M_Bakelite": ("1C1612", 0.25, 0.0, None, 1.0),
    "M_Rubber": ("151515", 0.9, 0.0, None, 1.0),
    "M_Glass": ("DDEBEA", 0.05, 0.0, None, 0.25),
    "M_Glass_Frosted": ("D8DEDC", 0.5, 0.0, None, 0.6),
    "M_Crystal": ("CFF6FF", 0.0, 0.0, None, 0.35),
    "M_Leather": ("3A2418", 0.6, 0.0, None, 1.0),
    "M_Fabric": ("2F2A26", 0.95, 0.0, None, 1.0),
    "M_Paper": ("D9CBB0", 0.85, 0.0, None, 1.0),
    "M_Enamel_Cream": ("E8DFC8", 0.35, 0.0, None, 1.0),
    "M_Chalkboard": ("1E2421", 0.9, 0.0, None, 1.0),
    "M_Liquid_Crimson": ("8E1B2A", 0.1, 0.0, None, 0.75),
    "M_Liquid_Cobalt": ("1F3E9E", 0.1, 0.0, None, 0.75),
    "M_Liquid_Green": ("3E8E3A", 0.1, 0.0, None, 0.75),
    "M_Emissive_Warm": ("FFB46B", 0.4, 0.0, "FFB46B", 1.0),
    "M_Emissive_Red": ("FF3B2F", 0.4, 0.0, "FF3B2F", 1.0),
    "M_Emissive_Lumen": ("CFF6FF", 0.2, 0.0, "CFF6FF", 1.0),
    "M_Lamp_L": ("3A2A12", 0.2, 0.0, None, 1.0),
    "M_Lamp_G": ("3A2A12", 0.2, 0.0, None, 1.0),
    "M_Lamp_A": ("3A2A12", 0.2, 0.0, None, 1.0),
    "M_Lamp_V": ("3A2A12", 0.2, 0.0, None, 1.0),
}


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h: str, alpha: float = 1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


# ---------------------------------------------------------------- scene
def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


# ---------------------------------------------------------------- materials
def material(name: str, color: str | None = None, rough: float | None = None,
             metal: float | None = None, emission: str | None = None,
             emission_strength: float = 3.0, alpha: float | None = None,
             image: str | None = None) -> bpy.types.Material:
    """Get or create a material. Unknown names fall back to PREVIEW defaults or grey.

    `image` (absolute path) lets decal materials show their texture in QA renders.
    """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    d = PREVIEW.get(name, ("808080", 0.5, 0.0, None, 1.0))
    color = color or d[0]
    rough = d[1] if rough is None else rough
    metal = d[2] if metal is None else metal
    emission = emission if emission is not None else d[3]
    alpha = d[4] if alpha is None else alpha
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    tex_dir = os.path.join(ROOT, "game", "assets", "textures", name[2:].lower())
    if image is None and os.path.isdir(tex_dir):
        _attach_pbr(nt, bsdf, tex_dir)
    if image and os.path.exists(image):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _attach_pbr(nt, bsdf, tex_dir: str) -> None:
    """Wire albedo/normal/ORM from game/assets/textures/<folder> so QA renders match Godot."""
    def img(fname, non_color=False):
        for ext in ("", ".jpg", ".png"):
            path = os.path.join(tex_dir, fname + ext) if ext else None
            if path and os.path.exists(path):
                node = nt.nodes.new("ShaderNodeTexImage")
                node.image = bpy.data.images.load(path, check_existing=True)
                if non_color:
                    node.image.colorspace_settings.name = "Non-Color"
                return node
        return None
    alb = img("albedo")
    if alb:
        nt.links.new(alb.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = img("normal", True)
    if nrm:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    orm = img("orm", True)
    if orm:
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])


def assign(obj: bpy.types.Object, mat_name: str) -> None:
    mat = material(mat_name)
    if mat.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(mat)
    idx = [m.name if m else "" for m in obj.data.materials].index(mat.name)
    for p in obj.data.polygons:
        p.material_index = idx


def add_slot(obj: bpy.types.Object, mat_name: str) -> int:
    mat = material(mat_name)
    names = [m.name if m else "" for m in obj.data.materials]
    if mat.name in names:
        return names.index(mat.name)
    obj.data.materials.append(mat)
    return len(obj.data.materials) - 1


# ---------------------------------------------------------------- objects
def _new_obj(name: str, bm: bmesh.types.BMesh, col: bpy.types.Collection | None = None) -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def _bevel_bm(bm: bmesh.types.BMesh, width: float, segments: int) -> None:
    if width <= 0:
        return
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, offset_type="OFFSET",
                    segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)


def box(name: str, size, loc=(0, 0, 0), rot=(0, 0, 0), mat: str = "M_Wood_Walnut",
        bevel: float = 0.004, segments: int = 2, col=None) -> bpy.types.Object:
    """Axis box of `size` (x, y, z) metres centred at `loc` with bevelled edges."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    _bevel_bm(bm, min(bevel, min(size) * 0.45), segments)
    obj = _new_obj(name, bm, col)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def cylinder(name: str, radius: float, depth: float, loc=(0, 0, 0), rot=(0, 0, 0),
             verts: int = 32, mat: str = "M_Brass_Aged", bevel: float = 0.002,
             segments: int = 2, radius_top: float | None = None, col=None) -> bpy.types.Object:
    """Cylinder (or cone frustum) along local Z, centred at `loc`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=radius if radius_top is None else radius_top,
                          depth=depth)
    if bevel > 0:
        # bevel only the cap rims (edges whose faces meet at a sharp angle)
        rims = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(50)]
        bmesh.ops.bevel(bm, geom=rims, offset=min(bevel, depth * 0.45), offset_type="OFFSET",
                        segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)
    obj = _new_obj(name, bm, col)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def sphere(name: str, radius: float, loc=(0, 0, 0), segments: int = 24, rings: int = 12,
           mat: str = "M_Brass_Aged", scale=(1, 1, 1), col=None) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    obj = _new_obj(name, bm, col)
    obj.location = loc
    assign(obj, mat)
    return obj


def torus(name: str, major: float, minor: float, loc=(0, 0, 0), rot=(0, 0, 0),
          major_seg: int = 32, minor_seg: int = 10, mat: str = "M_Brass_Aged", col=None) -> bpy.types.Object:
    bm = bmesh.new()
    verts_ring = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        ring = []
        for j in range(minor_seg):
            b = 2 * math.pi * j / minor_seg
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        verts_ring.append(ring)
    for i in range(major_seg):
        for j in range(minor_seg):
            a = verts_ring[i][j]
            b = verts_ring[(i + 1) % major_seg][j]
            c = verts_ring[(i + 1) % major_seg][(j + 1) % minor_seg]
            d = verts_ring[i][(j + 1) % minor_seg]
            bm.faces.new((a, b, c, d))
    obj = _new_obj(name, bm, col)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def lathe(name: str, profile, loc=(0, 0, 0), rot=(0, 0, 0), segments: int = 32,
          mat: str = "M_Brass_Aged", col=None) -> bpy.types.Object:
    """Revolve a 2D profile [(radius, z), ...] around local Z (bottom to top).

    Radius 0 at the ends closes the shape. Great for turned legs, knobs, vials, lamp shades.
    """
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(segments):
            a, b = rings[k][i], rings[k][(i + 1) % segments]
            c, d = rings[k + 1][(i + 1) % segments], rings[k + 1][i]
            bm.faces.new((a, b, c, d))
    if profile[0][0] > 1e-6:
        bm.faces.new(list(reversed(rings[0])))
    if profile[-1][0] > 1e-6:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _new_obj(name, bm, col)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def extrude_profile(name: str, points_2d, depth: float, loc=(0, 0, 0), rot=(0, 0, 0),
                    mat: str = "M_Wood_Walnut", bevel: float = 0.002, segments: int = 1,
                    col=None) -> bpy.types.Object:
    """Extrude a closed 2D polygon [(x, y), ...] (counter-clockwise) along +Z by `depth`."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0.0)) for (x, y) in points_2d]
    face = bm.faces.new(bottom)
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    top_verts = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=top_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(40)]
        bmesh.ops.bevel(bm, geom=sharp, offset=bevel, offset_type="OFFSET", segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    obj = _new_obj(name, bm, col)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def text_mesh(name: str, text: str, size: float, depth: float = 0.0005, loc=(0, 0, 0),
              rot=(0, 0, 0), mat: str = "M_Brass_Polished", align: str = "CENTER",
              font_path: str | None = None, col=None) -> bpy.types.Object:
    """Real geometry text (engraving/embossing). Converted to a mesh immediately."""
    curve = bpy.data.curves.new(name + "_txt", "FONT")
    curve.body = text
    curve.size = size
    curve.extrude = depth
    curve.align_x = align
    curve.align_y = "CENTER"
    if font_path and os.path.exists(font_path):
        curve.font = bpy.data.fonts.load(font_path, check_existing=True)
    tmp = bpy.data.objects.new(name + "_tmp", curve)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(curve)
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    assign(obj, mat)
    return obj


def empty(name: str, loc=(0, 0, 0), rot=(0, 0, 0), parent=None) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if parent is not None:
        set_parent(obj, parent)
    return obj


# ---------------------------------------------------------------- operations
def refresh() -> None:
    """Update matrix_world after location/rotation edits (needed before reading matrices)."""
    bpy.context.view_layer.update()


def apply_modifiers(obj: bpy.types.Object) -> None:
    if obj.type != "MESH" or not obj.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)


def boolean(target: bpy.types.Object, cutter: bpy.types.Object, op: str = "DIFFERENCE",
            delete_cutter: bool = True) -> None:
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.object = cutter
    mod.solver = "EXACT"
    apply_modifiers(target)
    # carry the cutter's materials over so cut faces keep them
    if delete_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)


def apply_transform(obj: bpy.types.Object) -> None:
    """Bake location/rotation/scale into mesh data (object ends at identity)."""
    if obj.type == "MESH":
        obj.data.transform(obj.matrix_basis)
    obj.matrix_basis = Matrix.Identity(4)


def join(objs, name: str | None = None) -> bpy.types.Object:
    """Join meshes into the first object (keeps material slots)."""
    objs = [o for o in objs if o is not None]
    refresh()
    base = objs[0]
    for o in objs:
        apply_modifiers(o)
    bm = bmesh.new()
    mats: list = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m is None:
                remap.append(0)
                continue
            if m.name not in [x.name for x in mats]:
                mats.append(m)
            remap.append([x.name for x in mats].index(m.name))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    new_me = bpy.data.meshes.new(name or base.name)
    bm.to_mesh(new_me)
    bm.free()
    for m in mats:
        new_me.materials.append(m)
    obj = bpy.data.objects.new(name or base.name, new_me)
    (base.users_collection[0] if base.users_collection else bpy.context.scene.collection).objects.link(obj)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    if name:
        obj.name = name
        obj.data.name = name
    return obj


def set_origin(obj: bpy.types.Object, world_point) -> None:
    """Move the object origin to `world_point` without moving geometry (pivot placement)."""
    refresh()
    wp = Vector(world_point)
    local = obj.matrix_world.inverted() @ wp
    obj.data.transform(Matrix.Translation(-local))
    obj.matrix_world = obj.matrix_world @ Matrix.Translation(local)


def set_parent(child: bpy.types.Object, parent: bpy.types.Object) -> None:
    refresh()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw


def mirror_copy(obj: bpy.types.Object, axis: int = 0, name: str | None = None) -> bpy.types.Object:
    new = obj.copy()
    new.data = obj.data.copy()
    obj.users_collection[0].objects.link(new)
    s = [1, 1, 1]
    s[axis] = -1
    new.data.transform(Matrix.Diagonal((*s, 1)))
    new.data.flip_normals()
    loc = list(obj.location)
    loc[axis] = -loc[axis]
    new.location = loc
    new.name = name or (obj.name + "_mirror")
    return new


def duplicate(obj: bpy.types.Object, name: str, loc=None, rot=None, linked: bool = False) -> bpy.types.Object:
    new = obj.copy()
    if not linked and obj.data is not None:
        new.data = obj.data.copy()
    obj.users_collection[0].objects.link(new)
    new.name = name
    if loc is not None:
        new.location = loc
    if rot is not None:
        new.rotation_euler = rot
    return new


def box_uv(obj: bpy.types.Object, scale: float = 1.0, skip_materials=("M_Decal_",)) -> None:
    """World-scale triplanar-style box projection: 1 UV unit = 1 m (times `scale`).

    Faces whose material name starts with any prefix in `skip_materials` keep their UVs.
    """
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    refresh()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    mat_names = [m.name if m else "" for m in me.materials]
    for f in bm.faces:
        mname = mat_names[f.material_index] if f.material_index < len(mat_names) else ""
        if any(mname.startswith(p) for p in skip_materials):
            continue
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            p = mw @ loop.vert.co
            if ax == 0:
                u, v = (p.y if n.x > 0 else -p.y), p.z
            elif ax == 1:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            else:
                u, v = p.x, (p.y if n.z > 0 else -p.y)
            loop[uv].uv = (u * scale, v * scale)
    bm.to_mesh(me)
    bm.free()


def cylinder_uv(obj: bpy.types.Object, axis: str = "Z", u_repeats: float = 1.0,
                material_prefix: str | None = None) -> None:
    """Cylindrical 0..1 UVs around the object's local axis — used for digit/colour wheels.

    U = angle / 2π (starting at local +X, counter-clockwise looking down +axis) * u_repeats,
    V = normalised height along the axis. Only faces of `material_prefix` if given.
    """
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    ai = "XYZ".index(axis)
    others = [i for i in range(3) if i != ai]
    hs = [v.co[ai] for v in bm.verts]
    h0, h1 = min(hs), max(hs)
    mat_names = [m.name if m else "" for m in me.materials]
    for f in bm.faces:
        if material_prefix is not None:
            mname = mat_names[f.material_index] if f.material_index < len(mat_names) else ""
            if not mname.startswith(material_prefix):
                continue
        center = f.calc_center_median()
        ca = math.atan2(center[others[1]], center[others[0]])
        for loop in f.loops:
            co = loop.vert.co
            a = math.atan2(co[others[1]], co[others[0]])
            # keep a face's U continuous across the -pi/pi seam
            if a - ca > math.pi:
                a -= 2 * math.pi
            elif ca - a > math.pi:
                a += 2 * math.pi
            u = (a / (2 * math.pi)) % 1.0 if abs(a - ca) < 1e-9 else (a / (2 * math.pi))
            v = (co[ai] - h0) / max(1e-9, (h1 - h0))
            loop[uv].uv = (u * u_repeats, v)
    bm.to_mesh(me)
    bm.free()


def planar_uv(obj: bpy.types.Object, axis: str = "Y", material_prefix: str | None = None,
              flip_u: bool = False) -> None:
    """Fit 0..1 UVs to the object's local bounding box, projected along `axis` — for decals/labels."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    ai = "XYZ".index(axis)
    ui, vi = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[ai]
    mat_names = [m.name if m else "" for m in me.materials]
    faces = [f for f in bm.faces if material_prefix is None or
             (f.material_index < len(mat_names) and mat_names[f.material_index].startswith(material_prefix))]
    verts = {v for f in faces for v in f.verts}
    if not verts:
        bm.free()
        return
    us = [v.co[ui] for v in verts]
    vs = [v.co[vi] for v in verts]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    for f in faces:
        for loop in f.loops:
            u = (loop.vert.co[ui] - u0) / max(1e-9, u1 - u0)
            v = (loop.vert.co[vi] - v0) / max(1e-9, v1 - v0)
            loop[uv].uv = ((1 - u) if flip_u else u, v)
    bm.to_mesh(me)
    bm.free()


def smooth(obj: bpy.types.Object, angle_deg: float = 35.0) -> None:
    """Smooth shading with sharp edges above `angle_deg` (exported as split normals)."""
    if obj.type != "MESH":
        return
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_face_angle(0) > thr:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


def finalize(objs=None, uv_scale: float = 1.0, smooth_angle: float = 35.0) -> None:
    """Apply modifiers, box-UV (non-decal faces) and smoothing on all mesh objects."""
    for obj in (objs or list(bpy.context.scene.objects)):
        if obj.type != "MESH":
            continue
        apply_modifiers(obj)
        box_uv(obj, uv_scale)
        smooth(obj, smooth_angle)


def tri_count(objs=None) -> int:
    total = 0
    for obj in (objs or bpy.context.scene.objects):
        if obj.type == "MESH":
            total += sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return total


# ---------------------------------------------------------------- export & QA
def export_glb(name: str, subdir: str = "") -> str:
    out_dir = os.path.join(MODELS_DIR, subdir)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        # Godot swaps every M_* slot for res://assets/materials/<name>.tres, so embedding the
        # QA-preview images would only duplicate the texture library inside each GLB.
        export_image_format="NONE",
    )
    print(f"[mrlib] exported {path} ({tri_count()} tris)")
    return path


def _look_at(obj, target) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_preview(name: str, cam_loc, target, lens: float = 50.0, res=(960, 640),
                   samples: int = 48, world_strength: float = 0.25, lights=None) -> str:
    """Cycles CPU QA render to qa/blender/<name>.png (three-point studio lighting)."""
    os.makedirs(QA_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        scene.view_settings.view_transform = "Filmic"
    world = bpy.data.worlds.new("QAWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = hex_rgba("1A1C1F")
    bg.inputs["Strength"].default_value = world_strength
    scene.world = world
    cam_data = bpy.data.cameras.new("QACam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("QACam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = cam_loc
    _look_at(cam, target)
    scene.camera = cam
    t = Vector(target)
    span = (Vector(cam_loc) - t).length
    for i, (off, energy, color, size) in enumerate(lights or [
        ((1.0, -1.2, 1.4), 900, "FFE2C0", 1.5),   # key, warm
        ((-1.4, -0.6, 0.8), 300, "BFD4FF", 2.0),  # fill, cool
        ((0.2, 1.4, 1.6), 600, "FFFFFF", 1.0),    # rim
    ]):
        ld = bpy.data.lights.new(f"QALight{i}", "AREA")
        ld.energy = energy * (span ** 2) / 4.0
        ld.color = hex_rgba(color)[:3]
        ld.size = size * span / 2.0
        lo = bpy.data.objects.new(f"QALight{i}", ld)
        scene.collection.objects.link(lo)
        lo.location = t + Vector(off) * span * 0.8
        _look_at(lo, target)
    path = os.path.join(QA_DIR, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # remove QA helpers so a later export stays clean
    for o in [o for o in scene.objects if o.name.startswith("QA")]:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"[mrlib] rendered {path}")
    return path


def main_guard() -> list[str]:
    """Return script args after '--' (blender -b -P x.py -- args)."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
