"""MYSTERY ROOM — helpers for the Chapter 2 group B2 furniture (archivist desk, reading table and the
projection-booth furniture: film splicer, slide cabinet, lens case).

Builds on mrlib / lib_arch / lib_mech / lib_props (never edit those: they are shared).

Everything here takes **Godot coordinates** (x, y up, z toward the viewer) and converts them to
Blender (x, -z, y), so the model scripts can be written straight from docs/models/ch2.md.

  * G(x, y, z)                      Godot point -> Blender Vector
  * gbox(name, mn, mx, ...)         bevelled box from Godot min/max corners
  * gcyl / glathe(..., axis="y")    cylinders / lathes standing on a Godot point along a Godot axis
  * gquad(...)                      a decal quad with UV 0..1 (u = left->right, v = bottom->top)
  * part(name, objs, pivot)         join parts into one object with its origin at a Godot pivot
  * finish_static / finalize_all    smoothing (per-part hints), world-scale UVs, wood grain
  * verify_glb(...)                 reads the exported GLB: names, pivots, identity rotations, tris
  * qa_*                            QA scene: room (or proxy), neighbours, item proxies, cameras
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_props as P  # noqa: E402

ROOT = M.ROOT
DECALS2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
QA_SUB = "ch2"
QA_TEST = os.environ.get("MR_QA_TEST_DECALS", "")   # optional folder with QA-only stand-in decals

# New Chapter 2 slots (docs/models/ch2.md §0): name -> (hex, roughness, metallic, alpha)
CH2_SLOTS = {
    "M_Linoleum": ("3E5A48", 0.55, 0.0, 1.0),
    "M_Paint_Green": ("6F8C78", 0.6, 0.0, 1.0),
    "M_Concrete": ("8C8A84", 0.85, 0.0, 1.0),
    "M_Steel_Cream": ("D8CFB4", 0.4, 0.1, 1.0),
    "M_Screen": ("E9E6DF", 0.95, 0.0, 1.0),
    "M_Velvet": ("5A1420", 0.9, 0.0, 1.0),
    "M_Film": ("3A2414", 0.25, 0.0, 0.9),
    "M_Tape": ("4A2C1A", 0.35, 0.0, 1.0),
    "M_Cardboard": ("9A7B55", 0.85, 0.0, 1.0),
    "M_Linen": ("8C7B5E", 0.8, 0.0, 1.0),
}
# Existing game slots that mrlib.PREVIEW does not know (values copied from the .tres files).
OTHER_SLOTS = {
    "M_Glass_Green": ("16472A", 0.07, 0.0, 1.0),
    "M_Lacquer_Black": ("161210", 0.32, 0.0, 1.0),
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 1.0),
    "M_Glass_Amber": ("5A2A0C", 0.08, 0.0, 0.82),
}


def ensure_materials() -> None:
    """Create preview versions of every slot the B2 models use (call right after reset_scene)."""
    A.prepare_materials()
    P.init_materials()          # M_Book_*, M_Felt, M_Cork ... (tinted CC0 textures)
    K.ensure_materials()        # enamels
    for name, (hx, rough, metal, alpha) in {**CH2_SLOTS, **OTHER_SLOTS}.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)


def decal_path(fname: str) -> str | None:
    """Real decal from group F if it exists, else an optional QA-only stand-in, else None."""
    p = os.path.join(DECALS2, fname)
    if os.path.exists(p):
        return p
    if QA_TEST:
        q = os.path.join(QA_TEST, fname)
        if os.path.exists(q):
            return q
    return None


def decal_material(slot: str, fname: str, color: str = "FFFFFF", rough: float = 0.6):
    mat = bpy.data.materials.get(slot)
    if mat is not None:
        return mat
    return M.material(slot, color=color, rough=rough, image=decal_path(fname))


# ---------------------------------------------------------------- coordinates
def G(x, y, z) -> Vector:
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return Vector((x, -z, y))


def GV(v) -> Vector:
    return Vector((v[0], -v[2], v[1]))


def to_godot(v) -> tuple:
    return (v[0], v[2], -v[1])


def gbox(name, mn, mx, mat="M_Wood_Walnut", bevel=0.003, seg=1):
    """Bevelled box between Godot corners mn and mx."""
    bmn = (min(mn[0], mx[0]), -max(mn[2], mx[2]), min(mn[1], mx[1]))
    bmx = (max(mn[0], mx[0]), -min(mn[2], mx[2]), max(mn[1], mx[1]))
    return A.box_minmax(name, bmn, bmx, mat=mat, bevel=bevel, segments=seg)


def gbox_c(name, centre, size, mat="M_Wood_Walnut", bevel=0.003, seg=1, yaw=0.0, pitch=0.0, roll=0.0):
    """Box of Godot size (sx, sy, sz) centred on a Godot point, rotated (Godot yaw about Y, pitch about X,
    roll about Z, degrees; applied roll, pitch, yaw) and baked into the mesh at the origin."""
    o = M.box(name, (size[0], size[2], size[1]), loc=(0, 0, 0), mat=mat, bevel=bevel, segments=seg)
    rot_bake(o, yaw, pitch, roll)
    o.location = G(*centre)
    return o


def gmat(yaw=0.0, pitch=0.0, roll=0.0) -> Matrix:
    """Blender rotation matrix of a Godot rotation: roll about Godot Z, then pitch about X, then yaw about Y."""
    rz = Matrix.Rotation(math.radians(roll), 4, Vector((0, -1, 0)))
    rx = Matrix.Rotation(math.radians(pitch), 4, "X")
    ry = Matrix.Rotation(math.radians(yaw), 4, "Z")
    return ry @ rx @ rz


def rot_bake(o, yaw=0.0, pitch=0.0, roll=0.0) -> None:
    if yaw or pitch or roll:
        o.data.transform(gmat(yaw, pitch, roll))


GAXIS = {"x": (1, 0, 0), "-x": (-1, 0, 0), "y": (0, 0, 1), "-y": (0, 0, -1), "z": (0, -1, 0), "-z": (0, 1, 0)}


def axis_vec(axis) -> Vector:
    if isinstance(axis, str):
        return Vector(GAXIS[axis])
    return GV(axis).normalized()


def aim_z(o, axis) -> None:
    """Rotate mesh data so local Blender +Z points along the Godot axis/direction."""
    d = axis_vec(axis)
    z = Vector((0, 0, 1))
    if (d - z).length < 1e-9:
        return
    if (d + z).length < 1e-9:
        o.data.transform(Matrix.Rotation(math.pi, 4, "X"))
        return
    o.data.transform(z.rotation_difference(d).to_matrix().to_4x4())


def gcyl(name, r, h, base, axis="y", verts=24, mat="M_Brass_Aged", bevel=0.001, seg=1, r_top=None, smooth=60.0):
    """Cylinder (or frustum) of length h starting at Godot point `base` and running along `axis`."""
    o = M.cylinder(name, r, h, loc=(0, 0, 0), verts=verts, mat=mat, bevel=bevel, segments=seg, radius_top=r_top)
    o.data.transform(Matrix.Translation((0, 0, h / 2)))
    aim_z(o, axis)
    o.location = G(*base)
    return A.hint(o, smooth) if smooth else o


def glathe(name, profile, base, axis="y", segments=24, mat="M_Brass_Aged", smooth=60.0):
    """Lathe [(r, h)] around a Godot axis, profile h = 0 at `base`."""
    o = M.lathe(name, profile, segments=segments, mat=mat)
    aim_z(o, axis)
    o.location = G(*base)
    return A.hint(o, smooth) if smooth else o


def glathe2(name, profile, base, axis="y", segments=24, mat="M_Brass_Aged", smooth=60.0, **kw):
    """lib_mech.lathe2 (flags, band materials) around a Godot axis."""
    o = K.lathe2(name, profile, segments=segments, mat=mat, **kw)
    aim_z(o, axis)
    o.location = G(*base)
    return A.hint(o, smooth) if smooth else o


def gtube(name, pts, r, sides=8, mat="M_Steel_Dark", fillet=0.0, caps=True):
    return A.tube(name, [G(*p) for p in pts], r, sides=sides, fillet=fillet, mat=mat, caps=caps)


def gquad(name, centre, u_axis, v_axis, w, h, mat, uv=True):
    """Single quad centred on a Godot point. u_axis/v_axis are Godot directions of the image's
    left->right and bottom->top; the face normal is u x v. UV 0..1 fills the quad."""
    c, u, v = GV(centre), GV(u_axis).normalized(), GV(v_axis).normalized()
    co = [c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2, c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in co], [], [(0, 1, 2, 3)])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    if uv:
        uvl = me.uv_layers.new(name="UVMap")
        for li, (uu, vv) in zip(me.polygons[0].loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uvl.data[li].uv = (uu, vv)
    return o


def gpoly(name, pts2d, depth, origin, ex, ey, mat="M_Brass_Aged", bevel=0.0004, drop_bottom=True):
    """Extrude 2D loops (lib_mech.curve_solid) in a Godot plane: 2D x -> Godot `ex`, 2D y -> `ey`,
    extrusion along ex x ey, starting on the plane through `origin`."""
    loops = pts2d if isinstance(pts2d[0][0], (tuple, list)) else [pts2d]
    o = K.curve_solid(name, loops, depth, bevel=bevel, mat=mat, drop_bottom=drop_bottom)
    bx, by = GV(ex).normalized(), GV(ey).normalized()
    bz = bx.cross(by)
    o.data.transform(A.frame_matrix((0, 0, 0), bx, by, bz))
    o.location = G(*origin)
    return o


def screw(name, r, loc, normal, mat="M_Brass_Aged", slot=30.0):
    return A.screw(name, r, G(*loc), normal=axis_vec(normal), mat=mat, slot_angle=slot)


# ---------------------------------------------------------------- parts
def part(name, objs, pivot=None, presmooth=True):
    """Join objs into one object named `name` with its origin at Godot `pivot` (identity rotation)."""
    objs = [o for o in objs if o is not None]
    if presmooth:
        A.presmooth(objs)
    o = M.join(objs, name) if len(objs) > 1 or objs[0].name != name else objs[0]
    o.name = name
    if o.data is not None:
        o.data.name = name
    if pivot is not None:
        M.set_origin(o, G(*pivot))
    return o


def parent(child, par) -> None:
    M.set_parent(child, par)


def mount(name, loc, par=None, rot_deg=(0.0, 0.0, 0.0)):
    """Mount empty at Godot `loc`; rot_deg = Godot Euler (x, y, z) degrees (applied as Blender X, then Godot Y
    = Blender Z, then Godot Z = Blender -Y)."""
    e = M.empty(name, loc=G(*loc))
    rx, ry, rz = rot_deg
    e.rotation_mode = "QUATERNION"
    q = (gmat(ry, rx, rz)).to_quaternion()
    e.rotation_quaternion = q
    e.empty_display_size = 0.02
    if par is not None:
        M.set_parent(e, par)
    return e


def finalize_all(wood_grain=True) -> None:
    """World-scale UVs for every non-decal face (per-part smoothing must already be applied via part()),
    then run the wood grain along each member."""
    A.finalize_uv()
    if wood_grain:
        for o in bpy.context.scene.objects:
            if o.type == "MESH" and any(m and m.name in A.WOOD_SLOTS for m in o.data.materials):
                A.grain_uv(o)


def report(label: str) -> int:
    M.refresh()
    total = M.tri_count()
    print(f"[b2] {label}: TOTAL tris={total}")
    for o in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        if o.name.lower().startswith("qa"):
            continue
        t = A.tris(o) if o.type == "MESH" else 0
        g = to_godot(o.matrix_world.translation)
        print(f"[b2]   {o.name:26s} {o.type:5s} tris={t:5d} origin(godot)=({g[0]:+.4f}, {g[1]:+.4f}, {g[2]:+.4f}) "
              f"parent={o.parent.name if o.parent else '-'}")
    return total


def export(name: str) -> str:
    return A.export_lean(name)


# ---------------------------------------------------------------- GLB verification (glTF = Godot axes)
def glb_json(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def _node_matrix(n) -> Matrix:
    t = Vector(n.get("translation", (0, 0, 0)))
    q = n.get("rotation", (0, 0, 0, 1))
    s = n.get("scale", (1, 1, 1))
    return Matrix.Translation(t) @ Quaternion((q[3], q[0], q[1], q[2])).to_matrix().to_4x4() @ Matrix.Diagonal((*s, 1))


def verify_glb(path: str, required=(), identity=(), budget: int | None = None, show=()) -> list[str]:
    """Check an exported GLB: required node names exist; `identity` nodes have identity rotation and unit
    scale; print tris (from index accessors) and the Godot transforms of `show` nodes. Returns errors."""
    doc = glb_json(path)
    nodes = doc.get("nodes", [])
    parent_of = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent_of[c] = i
    by_name = {n.get("name", ""): i for i, n in enumerate(nodes)}

    def world(i):
        m = _node_matrix(nodes[i])
        while i in parent_of:
            i = parent_of[i]
            m = _node_matrix(nodes[i]) @ m
        return m

    acc = doc.get("accessors", [])
    tris = 0
    for n in nodes:
        if "mesh" in n:
            for prim in doc["meshes"][n["mesh"]]["primitives"]:
                tris += acc[prim["indices"]]["count"] // 3 if "indices" in prim else acc[prim["attributes"]["POSITION"]]["count"] // 3
    errors = []
    for r in required:
        if r not in by_name:
            errors.append(f"missing node {r}")
    for r in identity:
        if r not in by_name:
            continue
        n = nodes[by_name[r]]
        q = n.get("rotation", (0, 0, 0, 1))
        s = n.get("scale", (1, 1, 1))
        if max(abs(q[0]), abs(q[1]), abs(q[2])) > 1e-4 or max(abs(c - 1) for c in s) > 1e-4:
            errors.append(f"{r}: rest rotation/scale not identity (q={q}, s={s})")
    print(f"[b2-verify] {os.path.basename(path)}: nodes={len(nodes)} tris={tris}"
          + (f" budget={budget} {'OK' if tris <= budget else 'OVER'}" if budget else ""))
    if budget and tris > budget:
        errors.append(f"tris {tris} > budget {budget}")
    for r in show:
        if r not in by_name:
            continue
        i = by_name[r]
        n = nodes[i]
        w = world(i)
        e = Quaternion((n.get("rotation", (0, 0, 0, 1))[3], *n.get("rotation", (0, 0, 0, 1))[:3])).to_euler("YXZ")
        wt = w.translation
        par = nodes[parent_of[i]].get("name") if i in parent_of else "-"
        print(f"[b2-verify]   {r:24s} parent={par:20s} local_t={tuple(round(c, 4) for c in n.get('translation', (0, 0, 0)))} "
              f"local_rot_deg(x,y,z)=({math.degrees(e.x):+.1f}, {math.degrees(e.y):+.1f}, {math.degrees(e.z):+.1f}) "
              f"model_t=({wt.x:+.4f}, {wt.y:+.4f}, {wt.z:+.4f})")
    for e in errors:
        print(f"[b2-verify] ERROR {e}")
    if not errors:
        print("[b2-verify] all checks passed")
    return errors


# ---------------------------------------------------------------- QA scene
def qa_begin(bounces: int = 8) -> None:
    """Call AFTER export. Shared-farm render settings + Cycles-friendly glass."""
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    P.preview_tweak()
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        n = mat.name
        if n == "M_Glass_Green":
            b.inputs["Base Color"].default_value = M.hex_rgba("2E8A50")
            b.inputs["Transmission Weight"].default_value = 0.55
            b.inputs["Roughness"].default_value = 0.08
            b.inputs["Coat Weight"].default_value = 0.6
        if n == "M_Glass_Frosted":
            b.inputs["Base Color"].default_value = M.hex_rgba("E4E8E2")
            b.inputs["Transmission Weight"].default_value = 0.0
            b.inputs["Alpha"].default_value = 1.0
            b.inputs["Roughness"].default_value = 0.45
            b.inputs["Subsurface Weight"].default_value = 0.25
        if n == "M_Glass_Dark":
            b.inputs["Alpha"].default_value = 1.0
        if n == "M_Velvet":
            b.inputs["Sheen Weight"].default_value = 0.8
            b.inputs["Sheen Tint"].default_value = M.hex_rgba("E07080")
        if n == "M_Film":
            b.inputs["Alpha"].default_value = 1.0
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    P.render_threads(2)
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 12


def model_roots():
    return [o for o in bpy.context.scene.objects if o.parent is None and not o.name.lower().startswith("qa")]


def qa_place(pos, yaw_deg: float, name="qa_place"):
    """Move the built model (all non-QA roots) to its world placement (Godot pos + yaw)."""
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in model_roots():
        o.parent = root
    root.location = G(*pos)
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    M.refresh()
    return root


def qa_import(path: str, pos=(0, 0, 0), yaw_deg: float = 0.0, parent_obj=None, prefix: str = "qa_"):
    """Import a GLB under a holder empty (QA only). With parent_obj, the holder sits at identity under it."""
    if not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new(prefix + "holder_" + os.path.basename(path), None)
    bpy.context.scene.collection.objects.link(holder)
    for o in new:
        if o.parent is None:
            o.parent = holder
        o.name = prefix + o.name
    if parent_obj is not None:
        holder.parent = parent_obj
        holder.matrix_parent_inverse = Matrix.Identity(4)
        holder.matrix_basis = Matrix.Identity(4)
    else:
        holder.location = G(*pos)
        holder.rotation_euler = (0, 0, math.radians(yaw_deg))
    M.refresh()
    return holder


def model_glb(name: str) -> str:
    return os.path.join(M.MODELS_DIR, name + ".glb")


def qa_material(name, colour, rough=0.85, metal=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = M.material(name, color=colour, rough=rough, metal=metal)
    return mat


def qa_gbox(name, mn, mx, mat_name):
    o = gbox(name, mn, mx, mat=mat_name, bevel=0.0)
    return o


def qa_room(area: str) -> None:
    """room_archive.glb if it exists, otherwise a simple proxy shell for the given area
    ('desk', 'reading', 'booth')."""
    room = model_glb("room_archive")
    if os.path.exists(room):
        qa_import(room)
        return
    lino, paint, plaster, conc = "M_Linoleum", "M_Paint_Green", "M_Plaster_Wall", "M_Concrete"
    qa_gbox("qa_floor", (-5.2, -0.02, -3.7), (5.2, 0.0, 3.7), lino)
    qa_gbox("qa_ceiling", (-5.2, 3.6, -3.7), (5.2, 3.65, 3.7), "M_Ceiling")
    for nm, mn, mx in (("north", (-5.2, 0, -3.7), (5.2, 3.6, -3.5)), ("south", (-5.2, 0, 3.5), (5.2, 3.6, 3.7)),
                       ("west", (-5.2, 0, -3.5), (-5.0, 3.6, 3.5)), ("east", (5.0, 0, -3.5), (5.2, 3.6, 3.5))):
        lo = list(mn)
        hi = list(mx)
        hi[1] = 1.4
        qa_gbox(f"qa_wall_{nm}_lo", tuple(lo), tuple(hi), paint)
        lo[1] = 1.4
        hi[1] = 3.6
        qa_gbox(f"qa_wall_{nm}_hi", tuple(lo), tuple(hi), plaster)
    # booth enclosure (north wall with window + door gap, east wall, ceiling slab, shelf)
    qa_gbox("qa_booth_n_a", (-5.0, 0, 2.0), (-3.4, 2.8, 2.1), paint)
    qa_gbox("qa_booth_n_b", (-3.4, 0, 2.0), (-2.1, 1.65, 2.1), paint)
    qa_gbox("qa_booth_n_c", (-3.4, 2.25, 2.0), (-2.1, 2.8, 2.1), paint)
    qa_gbox("qa_booth_n_d", (-2.1, 0, 2.0), (-1.95, 2.8, 2.1), paint)
    qa_gbox("qa_booth_n_e", (-1.95, 2.1, 2.0), (-1.0, 2.8, 2.1), paint)
    qa_gbox("qa_booth_e", (-1.1, 0, 2.1), (-1.0, 2.8, 3.5), paint)
    qa_gbox("qa_booth_ceil", (-5.0, 2.8, 2.0), (-1.0, 2.9, 3.5), conc)
    qa_gbox("qa_shelf", (-4.6, 1.42, 3.24), (-3.3, 1.45, 3.5), "M_Wood_Panel")
    for x in (-4.5, -3.4):
        qa_gbox("qa_shelf_bracket", (x - 0.012, 1.28, 3.30), (x + 0.012, 1.42, 3.5), "M_Steel_Dark")


def qa_neighbours(items) -> None:
    """items: [(glb name, (x, y, z), yaw)] imported when the GLB exists."""
    for name, pos, yaw in items:
        qa_import(model_glb(name), pos, yaw)


def qa_light(name, kind, pos, energy, colour="FFE2C0", radius=0.05, target=None, spot_deg=None, blend=0.3):
    ld = bpy.data.lights.new("qa_" + name, kind)
    ld.energy = energy
    ld.color = M.hex_rgba(colour)[:3]
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = radius
    if kind == "AREA":
        ld.size = radius
    if kind == "SPOT" and spot_deg:
        ld.spot_size = math.radians(spot_deg)
        ld.spot_blend = blend
    lo = bpy.data.objects.new("qa_" + name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = G(*pos)
    if target is not None:
        M._look_at(lo, G(*target))
    return lo


def qa_clear_lights() -> None:
    for o in [o for o in bpy.context.scene.objects if o.type == "LIGHT" and o.name.startswith("qa_")]:
        bpy.data.objects.remove(o, do_unlink=True)


def lens_for_vfov(vfov_deg: float, res=(960, 640)) -> float:
    """Blender lens (36 mm sensor, horizontal fit for landscape) matching a Godot vertical FOV."""
    aspect = res[0] / res[1]
    return 18.0 / (math.tan(math.radians(vfov_deg) / 2) * aspect)


NO_LIGHTS = [((0, 0, 1), 0.0, "FFFFFF", 0.1)]


def shoot(name, cam, target, vfov=None, lens=None, res=(960, 640), samples=32, world=0.06, lights=None):
    """Render qa/blender/ch2/<name>.png from Godot camera/target points."""
    if lens is None:
        lens = lens_for_vfov(vfov or 50.0, res)
    return M.render_preview(f"{QA_SUB}/{name}", G(*cam), G(*target), lens=lens, res=res, samples=min(samples, 32),
                            world_strength=world, lights=lights if lights is not None else NO_LIGHTS)


def want(tag: str, args) -> bool:
    if "--shots" not in args:
        return True
    return tag in args[args.index("--shots") + 1].split(",")


# ---------------------------------------------------------------- item proxies (QA only)
def item_or_proxy(item: str, mount_obj):
    """Attach the item GLB at a mount with identity; if it does not exist yet, a proxy of its size."""
    h = qa_import(model_glb(item), parent_obj=mount_obj)
    if h is not None:
        return h
    if item == "film_reel":      # Ø0.18 x 0.02 disc standing on edge, face +Z
        o = M.cylinder("qa_proxy_film_reel", 0.09, 0.02, verts=48, mat="M_Steel_Dark", bevel=0.002)
        o.rotation_euler = (math.pi / 2, 0, 0)
        hub = M.cylinder("qa_proxy_reel_film", 0.07, 0.016, verts=48, mat="M_Film", bevel=0.0)
        hub.rotation_euler = (math.pi / 2, 0, 0)
        objs = [o, hub]
    elif item == "lumen_crystal":   # Ø0.05 x 0.006 crystal disc in a 0.056 ring, on edge, face +Z
        o = M.cylinder("qa_proxy_crystal", 0.025, 0.006, verts=40, mat="M_Crystal", bevel=0.001)
        ring = K.ring_band("qa_proxy_crystal_ring", 0.0245, 0.028, 0.0075, segments=40, mat="M_Brass_Aged")
        for x in (o, ring):
            x.rotation_euler = (math.pi / 2, 0, 0)
        tab = M.box("qa_proxy_crystal_tab", (0.010, 0.004, 0.006), loc=(0, 0, 0.030), mat="M_Brass_Aged", bevel=0.0008)
        objs = [o, ring, tab]
    elif item == "glass_slide":     # 0.082 x 0.082 x 0.004, flat, face up
        o = M.box("qa_proxy_slide", (0.082, 0.082, 0.004), mat="M_Lacquer_Black", bevel=0.0006)
        face = M.box("qa_proxy_slide_face", (0.070, 0.070, 0.0006), loc=(0, 0, 0.0021), mat="M_Paper", bevel=0.0)
        win = M.box("qa_proxy_slide_win", (0.050, 0.044, 0.0006), loc=(0, 0, 0.0024), mat="M_Glass_Dark", bevel=0.0)
        objs = [o, face, win]
    else:
        return None
    for x in objs:
        x.parent = mount_obj
        x.matrix_parent_inverse = Matrix.Identity(4)
    return objs[0]
