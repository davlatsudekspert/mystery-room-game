"""MYSTERY ROOM — Chapter 3 groups B and C helpers (Choir Hall props, desk, ports, cabinets).
Contract: docs/models/ch3.md §4, §5; measured results: docs/models/ch3_b.md, docs/models/ch3_c.md.

Builds on mrlib / lib_mech / lib_arch / lib_props / lib_ch2_vault / lib_ch3_a / lib_ch3_symbols (never edits them).

G-FRAME (as lib_ch2_vault / lib_ch3_a): every script builds its geometry directly in GODOT axes inside Blender
(Blender x, y, z used as Godot x, y, z: y up, +z = the model front), so every number reads straight from ch3.md;
`K.to_blender()` converts the finished, unparented scene to Blender axes right before parenting and export.

  ensure_materials()          every slot groups B and C use (QA previews)
  jewel / bezel / bolt_ring   small repeated parts
  vcolor(obj, rgba)           a COLOR attribute (exported as COLOR_0 with export(..., vertex_colors=True))
  export(name)                lean GLB export (no images), optional vertex colours, check_glb_names
  verify(path, ...)           required names, identity rests, model positions, mount rotations, parents, tris,
                              surfaces and material slots (§13), check_glb_names: one list of errors
  hall() / choir_lights()     QA: the real shell_choir.glb and the Choir Hall's light rig (§1.5)
  place() / bring()           QA: put this script's model, or a neighbouring GLB, at a world placement (yaw, pitch)
  ghost(objs)                 QA: the in-game echo look (lib_ch2_echoes.game_ghost_material)
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
import lib_arch as A  # noqa: E402
import lib_ch2_vault as V  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402

TAG = "[ch3-bc]"
ROOT = M.ROOT
QA_SUB = "ch3"
PREVIEW_DIR = os.path.join(M.QA_DIR, "ch3", "preview")
TAU = 2.0 * math.pi

# G-frame primitives (re-exported)
gbox, glathe, gcyl, plate, flat, rivet, hexbolt = V.gbox, V.glathe, V.gcyl, V.plate, V.flat, V.rivet, V.hexbolt
part, empty, parent, axis_rot, tube = V.part, V.empty, V.parent, V.axis_rot, V.tube
G = V.G

STEEL, PAINT, BRASS, BRASS_P = "M_Steel_Dark", "M_Steel_Painted", "M_Brass_Aged", "M_Brass_Polished"
PORC, COPPER, FELT, FLOORWOOD = "M_Porcelain", "M_Copper", "M_Felt", "M_Wood_Floor"
WALNUT, PANEL, PAPER, LEATHER, VELVET = "M_Wood_Walnut", "M_Wood_Panel", "M_Paper", "M_Leather", "M_Velvet"
CREAM, BAKELITE, GLASS, CRYSTAL, SHQ = "M_Enamel_Cream", "M_Bakelite", "M_Glass", "M_Crystal", "M_Shader_Quad"

FONT_SERIF_B = V.FONT_SERIF_B
FONT_SANS_B = V.FONT_SANS_B
FONT_COND_B = V.FONT_COND_B

# §1.5 Choir work lamps (light_choir_<k> in shell_choir.glb, docs/models/ch3_a.md)
CHOIR_LAMPS = [(-12.3, 3.4, -3.88), (-7.4, 3.4, -3.88), (-11.6, 3.4, 3.88), (-7.4, 3.4, 3.88), (-4.62, 3.4, -2.8),
               (-4.62, 3.4, 2.2)]


# ====================================================================== materials
def ensure_materials() -> None:
    """Preview materials for every slot groups B and C use (call after mrlib.reset_scene)."""
    K.ensure_materials()
    for name in (STEEL, PAINT, BRASS, BRASS_P, PORC, COPPER, FELT, FLOORWOOD, WALNUT, PANEL, PAPER, LEATHER, VELVET,
                 CREAM, BAKELITE, GLASS, CRYSTAL, SHQ):
        if bpy.data.materials.get(name) is None:
            M.material(name)


# ====================================================================== small parts (G-frame)
def jewel(name, centre, r, normal=(0, 0, 1), mat=CREAM, h=None, seg=14):
    """Indicator jewel: a low dome of radius r on a short skirt, its base plane through `centre`, bulging along
    `normal` (the object origin is set to `centre` by the caller's part())."""
    h = h if h is not None else r * 0.75
    prof = [(r, -r * 0.25), (r, 0.0), (r * 0.93, h * 0.35), (r * 0.72, h * 0.72), (r * 0.40, h * 0.95), (0.0, h)]
    return glathe(name, prof, centre, normal, seg, mat, smooth=80.0)


def bezel(name, centre, r_in, r_out, h, normal=(0, 0, 1), mat=BRASS, seg=16):
    """Turned ring bezel standing on a surface (its back plane through `centre`)."""
    prof = [(r_in, 0.0), (r_out, 0.0), (r_out, h * 0.45), (r_out * 0.94, h), (r_in * 1.04, h), (r_in, h * 0.6),
            (r_in, 0.0)]
    return glathe(name, prof, centre, normal, seg, mat, smooth=45.0, cap_bottom=False, cap_top=False)


def frame_mat(origin, x_axis, y_axis):
    """4x4 G-frame matrix with the given origin and (orthonormalised) local X and Y axes; Z = X x Y."""
    ex = Vector(x_axis).normalized()
    ey = Vector(y_axis)
    ey = (ey - ex * ey.dot(ex)).normalized()
    ez = ex.cross(ey)
    o = Vector(origin)
    return Matrix(((ex.x, ey.x, ez.x, o.x), (ex.y, ey.y, ez.y, o.y), (ex.z, ey.z, ez.z, o.z), (0, 0, 0, 1)))


def text3d(name, body, size, loc, z, mat, depth=0.0, font=None, rot_z=0.0, spacing=1.0, res=2):
    """Low-poly 3D text in local XY facing +Z (centred on its glyph bounds at loc), base plane z."""
    return V.text(name, body, size, loc, z, font=font or FONT_SANS_B, mat=mat, depth=depth, rot_z=rot_z,
                  spacing=spacing, res=res)


def prism_x(name, pts_zy, x0, x1, mat):
    """Closed prism: polygon [(z, y), ...] (G-frame side profile) extruded along X from x0 to x1."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for (z, y) in pts_zy]
    b = [bm.verts.new((x1, y, z)) for (z, y) in pts_zy]
    n = len(pts_zy)
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method="BEAUTY",
                          ngon_method="EAR_CLIP")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.obj_from_bm(name, bm, mat)


def place_mesh(obj, m):
    """Bake a 4x4 G-frame transform into a mesh (objects are built at the origin, then moved)."""
    obj.data.transform(m)
    return obj


def vcolor(obj, rgba, name="Col") -> None:
    """Set (or create) a per-corner COLOR attribute with one value on every corner of `obj`. FLOAT_COLOR is linear,
    so the glTF COLOR_0 carries the exact numbers (a BYTE_COLOR would be sRGB-converted on export)."""
    me = obj.data
    attr = me.color_attributes.get(name)
    if attr is None:
        attr = me.color_attributes.new(name=name, type="FLOAT_COLOR", domain="CORNER")
    for d in attr.data:
        d.color = rgba
    me.color_attributes.active_color = attr
    me.color_attributes.render_color_index = list(me.color_attributes).index(attr)


def uv_rect_faces(obj, pred, u_axis, v_axis, origin, w, h):
    """0..1 UVs on the faces whose (local) centre/normal satisfy pred(c, n): u along u_axis over width w, v along
    v_axis over height h, measured from `origin` (the rectangle's lower-left corner), local coordinates."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    U, Vv, O = Vector(u_axis).normalized(), Vector(v_axis).normalized(), Vector(origin)
    for f in bm.faces:
        if not pred(f.calc_center_median(), f.normal):
            continue
        for lp in f.loops:
            d = lp.vert.co - O
            lp[uv].uv = (d.dot(U) / w, d.dot(Vv) / h)
    bm.to_mesh(me)
    bm.free()


# ====================================================================== export / verify
def export(name: str, vertex_colors: bool = False) -> str:
    """Lean GLB (no images; Godot swaps M_* slots for its .tres), with COLOR_0 where a mesh has an active colour
    attribute when vertex_colors is set. Runs check_glb_names."""
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    os.makedirs(M.MODELS_DIR, exist_ok=True)
    kw = dict(filepath=path, export_format="GLB", use_selection=False, export_apply=True, export_yup=True,
              export_materials="EXPORT", export_image_format="NONE", export_cameras=False, export_lights=False,
              export_extras=True)
    kw["export_vertex_color"] = "ACTIVE" if vertex_colors else "NONE"
    bpy.ops.export_scene.gltf(**kw)
    print(f"{TAG} exported {path} ({M.tri_count()} tris, {os.path.getsize(path) // 1024} KB)")
    return path


def verify(path, required, identity=(), expect=None, parents=None, rot_expect=None, tris=0, surf=0, mats=4,
           show=None, surf_drawn=None):
    """All GLB checks in one list of errors (empty = pass). surf_drawn: the surfaces actually drawn per instance
    when the code hides some alternatives (reported next to the file count; the cap is checked against it)."""
    errs = V.verify_glb(path, required=required, identity=identity, expect=expect or {}, parents=parents or {},
                        rot_expect=rot_expect or {}, show=show if show is not None else required)
    n_tris = K.glb_tris(path)
    n_surf, n_mat, per = K.surfaces(path)
    print(f"{TAG} {os.path.basename(path)}: tris {n_tris} / {tris}, surfaces {n_surf}"
          + (f" (drawn {surf_drawn})" if surf_drawn is not None else "") + f" / {surf}, materials {n_mat} / {mats}")
    for k, v in sorted(per.items()):
        print(f"{TAG}     {k:28s} {v}")
    if tris and n_tris > tris:
        errs.append(f"tris {n_tris} > {tris}")
    if surf and (surf_drawn if surf_drawn is not None else n_surf) > surf:
        errs.append(f"surfaces {surf_drawn if surf_drawn is not None else n_surf} > {surf}")
    if n_mat > mats:
        errs.append(f"materials {n_mat} > {mats}")
    if V.check_names(path) != 0:
        errs.append("check_glb_names failed")
    return errs


def glb_color_meshes(path):
    """Names of the GLB meshes that carry COLOR_0."""
    doc = V.glb_json(path)
    return [m.get("name", "") for m in doc.get("meshes", []) if any("COLOR_0" in p["attributes"] for p in m["primitives"])]


def finish(errs, label) -> None:
    print(f"{TAG} {label} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")


# ====================================================================== QA
def qa_begin(bounces: int = 6) -> None:
    K.qa_begin(bounces=bounces)
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2


def model_glb(name):
    return V.model_glb(name)


def _set_world(obj, pos, yaw=0.0, pitch=0.0):
    obj.matrix_world = (Matrix.Translation(G(*pos)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @
                        Matrix.Rotation(math.radians(pitch), 4, "X"))


def place(objs, pos, yaw=0.0, pitch=0.0, name="qa_place"):
    """Parent this script's root objects under one empty at a Godot placement Basis(UP, yaw) * Basis(RIGHT, pitch)."""
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
            o.matrix_parent_inverse = Matrix.Identity(4)
    _set_world(root, pos, yaw, pitch)
    M.refresh()
    return root


def bring(name, pos=(0, 0, 0), yaw=0.0, pitch=0.0, prefix=None, under=None):
    """Import a neighbouring GLB (QA only) at a Godot placement, or under a mount empty with identity, with this
    scene's textured preview materials."""
    prefix = prefix or f"qa_{name}_"
    if under is not None:
        holder = V.qa_import(model_glb(name), parent_obj=under, prefix=prefix)
    else:
        holder = K.qa_import(name, (0, 0, 0), 0.0, prefix=prefix)
        if holder is not None:
            _set_world(holder, pos, yaw, pitch)
    if holder is None:
        print(f"{TAG} QA: {name}.glb not found, skipped")
        return None
    _swap_preview_materials(prefix)
    M.refresh()
    return holder


def _swap_preview_materials(prefix):
    for o in bpy.data.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            base = m.name.split(".")[0]
            if bpy.data.materials.get(base) is None:
                M.material(base)
            if base != m.name:
                slot.material = bpy.data.materials[base]


def imported(prefix, name):
    """An object by prefix + node name, ignoring the '.001' suffix Blender adds when the name already exists."""
    o = bpy.data.objects.get(prefix + name)
    if o is not None:
        return o
    for o in bpy.data.objects:
        if o.name.startswith(prefix) and o.name[len(prefix):].split(".")[0] == name:
            return o
    return None


def hall(prefix="qa_hall_", lamps=True):
    """The real Choir Hall shell (and its lamp glasses glowing like the game's work lamps)."""
    h = bring("shell_choir", prefix=prefix)
    if h is not None and lamps:
        g = K.glow("qa_worklamp", "FFD49A", 9.0)
        for k in range(6):
            o = bpy.data.objects.get(f"{prefix}lamp_glass_{k}")
            if o is not None:
                K.override(o, g)
    return h


def choir_lights(cam=None, fill=12.0, key=2200.0, work=140.0, bounce=220.0, extra=()):
    """The Choir zone lights of §1.5 (shadowed key spot, six work omnis, a soft ceiling bounce) + the camera's
    focus_fill. extra: [(name, kind, pos, energy, colour, radius)]."""
    K.clear_lights()
    K.light("key_choir", "SPOT", (-8.0, 5.6, 2.6), key, "FFD2A0", radius=0.25, target=(-8.6, 0.0, -1.2), spot_deg=55)
    for k, p in enumerate(CHOIR_LAMPS):
        K.light(f"work_{k}", "POINT", p, work if k < 4 else work * 0.45, "FFC890", radius=0.06)
    if bounce:
        K.light("bounce", "AREA", (-8.7, 5.8, 0.0), bounce, "FFE6C8", radius=7.0, target=(-8.7, 0.0, 0.0))
    for (n, kind, p, e, c, r) in extra:
        K.light(n, kind, p, e, c, radius=r)
    if cam is not None and fill:
        K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), fill, "FFE2C2", radius=0.2)


def shoot(name, cam, target, fov, res=(960, 640), samples=32, world=0.03):
    return K.shoot(name, cam, target, vfov=fov, res=res, samples=samples, world=world)


def ghost(objs):
    """Swap objs to the in-game echo look (QA only)."""
    import lib_ch2_echoes as E2
    mat = E2.game_ghost_material()
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


def show_only(objs, keep):
    for o in objs:
        o.hide_render = o not in keep
        for c in o.children_recursive:
            c.hide_render = o not in keep


def rest_store(objs):
    return {o.name: o.matrix_basis.copy() for o in objs}


def rest_apply(objs, rest):
    for o in objs:
        if o.name in rest:
            o.matrix_basis = rest[o.name].copy()
    M.refresh()


def want(args, tag):
    return K.want(args, tag)
