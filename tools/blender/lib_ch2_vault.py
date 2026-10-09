"""MYSTERY ROOM — Chapter 2 vault helpers (build group D1: vault_door, vault_interior).

Builds on mrlib / lib_mech / lib_arch / lib_props (never edits them).

G-FRAME. Both vault scripts build their geometry directly in GODOT axes inside Blender (Blender x, y, z
are used as Godot x, y, z: y up, +z toward the room). That keeps every number identical to
docs/models/ch2.md, makes lathes around the door axis trivial (lib_mech.lathe2 revolves around local Z =
Godot Z) and lets lib_mech.curve_solid / text_flat / flat_shape produce plates that face the room (+Z).
`to_blender()` converts the finished, still unparented scene to Blender axes (Blender = (x, -z, y)) right
before parenting and export, so the GLB is a normal Godot-axis glTF.

Main helpers
  ensure_materials()          every slot the vault uses (library + Chapter 2 slots, decal previews)
  gbox / glathe / gcyl ...    G-frame primitives (Godot coordinates)
  to_blender(objs)            G-frame -> Blender axes for meshes and empties (call before parenting)
  verify_glb(...)             required names, identity rest rotations, model-space positions, tris
  qa_*                        QA scene: archive room (or a proxy shell with the vault opening), lights,
                              Godot-FOV cameras, disc-overlay emulation of vault_overlay.gdshader
"""
from __future__ import annotations

import json
import math
import os
import struct
import subprocess
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_props as P  # noqa: E402

ROOT = M.ROOT
TAG = "[d1-vault]"
QA_SUB = "ch2"
DECALS = os.path.join(ROOT, "game", "assets", "textures", "decals")
DECALS_CH2 = os.path.join(DECALS, "ch2")
TAU = 2.0 * math.pi

FONT_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_COND_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"

# Godot -> Blender axes: Blender = C @ Godot  (x, y, z) -> (x, -z, y)
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
C_INV = C.inverted()

# Library slots that mrlib.PREVIEW does not know (values from the .tres files)
OTHER_SLOTS = {
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 1.0),
    "M_Lacquer_Black": ("161210", 0.32, 0.0, 1.0),
    "M_Glass_Amber": ("5A2A0C", 0.08, 0.0, 0.82),
    "M_Felt": ("3A3A3A", 1.0, 0.0, 1.0),
    "M_Cork": ("9B7650", 0.9, 0.0, 1.0),
}


def ensure_materials() -> None:
    """Create preview materials for every slot the vault uses (call after reset_scene)."""
    L.ensure_materials()
    for name, (hx, rough, metal, alpha) in OTHER_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)
    # Chapter 2 slots come from mrlib.PREVIEW (contract §0 colours)
    for name in ("M_Concrete", "M_Velvet", "M_Screen", "M_Linen", "M_Cardboard", "M_Film", "M_Paint_Green",
                 "M_Linoleum", "M_Steel_Cream"):
        M.material(name)
    # M_Concrete.tres uses the stone texture set: mirror that in the QA preview
    con = bpy.data.materials.get("M_Concrete")
    if con is not None and not any(n.type == "TEX_IMAGE" for n in con.node_tree.nodes):
        M._attach_pbr(con.node_tree, con.node_tree.nodes.get("Principled BSDF"),
                      os.path.join(ROOT, "game", "assets", "textures", "stone"))
    decal_material("M_Decal_Photos", os.path.join(DECALS, "photo_0.jpg"))
    decal_material("M_Decal_BoxLabels", os.path.join(DECALS_CH2, "box_labels.jpg"))


def decal_material(slot: str, path: str):
    mat = bpy.data.materials.get(slot)
    if mat is not None:
        return mat
    return M.material(slot, image=path if os.path.exists(path) else None)


# ---------------------------------------------------------------- G-frame primitives (Godot coordinates)
def gbox(name, mn, mx, mat="M_Steel_Dark", bevel=0.003, seg=1):
    size = [mx[i] - mn[i] for i in range(3)]
    loc = [(mx[i] + mn[i]) / 2 for i in range(3)]
    o = M.box(name, size, loc=loc, mat=mat, bevel=bevel, segments=seg)
    M.apply_transform(o)
    return o


def axis_rot(axis) -> Matrix:
    """Rotation taking local +Z onto `axis` (4x4)."""
    a = Vector(axis).normalized()
    return Vector((0, 0, 1)).rotation_difference(a).to_matrix().to_4x4()


def glathe(name, profile, base=(0, 0, 0), axis=(0, 0, 1), segments=24, mat="M_Brass_Aged", phase=0.0,
           smooth=None, **kw):
    """lib_mech.lathe2 profile [(r, h[, 'k'])] revolved around `axis` through `base` (G-frame)."""
    o = L.lathe2(name, profile, segments=segments, mat=mat, phase=phase, **kw)
    o.data.transform(Matrix.Translation(base) @ axis_rot(axis))
    if smooth:
        A.hint(o, smooth)
    return o


def gcyl(name, r, h0, h1, base=(0, 0, 0), axis=(0, 0, 1), segments=16, mat="M_Steel_Dark", chamfer=0.0,
         caps=True, smooth=60.0):
    c = min(chamfer, r * 0.3, (h1 - h0) * 0.3)
    if c > 0:
        prof = [(0.0, h0), (r - c, h0), (r, h0 + c), (r, h1 - c), (r - c, h1), (0.0, h1)]
    else:
        prof = [(0.0, h0), (r, h0), (r, h1), (0.0, h1)]
    if not caps:
        prof = prof[1:-1]
    return glathe(name, prof, base, axis, segments, mat, smooth=smooth)


def plate(name, loops, depth, z0=0.0, mat="M_Brass_Aged", bevel=0.001, bevel_res=0, drop_bottom=True,
          loc=(0, 0, 0), rot_z=0.0):
    """curve_solid plate facing +Z (the room) from z0 to z0 + depth; loops drawn in XY around (0, 0),
    rotated by rot_z then moved to loc."""
    o = L.curve_solid(name, loops, depth, bevel=bevel, bevel_res=bevel_res, mat=mat, drop_bottom=drop_bottom)
    o.data.transform(Matrix.Translation((loc[0], loc[1], loc[2] + z0)) @ Matrix.Rotation(rot_z, 4, "Z"))
    return o


def flat(name, loops, z, loc=(0, 0), mat="M_Bakelite", rot_z=0.0):
    """Zero-thickness inlay facing +Z at height z."""
    o = L.flat_shape(name, loops, mat=mat)
    o.data.transform(Matrix.Translation((loc[0], loc[1], z)) @ Matrix.Rotation(rot_z, 4, "Z"))
    return o


def text(name, body, size, loc, z, font=FONT_SERIF_B, mat="M_Bakelite", depth=0.0, rot_z=0.0, spacing=1.0,
         res=2):
    """Low-poly text facing +Z, centred on its glyph bounds at loc (x, y), base plane z."""
    t = L.text_flat(name, body, size, font=font, depth=depth, res=res, mat=mat, spacing=spacing)
    L.recentre_xy(t)
    t.data.transform(Matrix.Translation((loc[0], loc[1], z)) @ Matrix.Rotation(rot_z, 4, "Z"))
    return t


def screw(name, r, loc, normal=(0, 0, 1), mat="M_Brass_Aged", slot=0.4, segs=8):
    return L.screw(name, r, loc, normal=normal, mat=mat, slot_angle=slot, segs=segs)


def rivet(name, r, loc, normal=(0, 0, 1), mat="M_Steel_Dark", segs=6):
    """Cheap domed rivet head (2 bands: 3·segs tris) on a surface with outward `normal`."""
    h = r * 0.55
    o = L.lathe2(name, [(r, 0.0), (r * 0.72, h * 0.72), (0.0, h)], segments=segs, mat=mat, cap_bottom=False)
    o.data.transform(Matrix.Translation(loc) @ axis_rot(normal))
    A.hint(o, 70.0)
    return o


def hexbolt(name, r, loc, normal=(0, 0, 1), h=None, mat="M_Steel_Dark", washer=True):
    """Hex bolt head (6-sided lathe) with an optional washer, sitting on a surface with `normal`."""
    h = h or r * 0.7
    prof = []
    if washer:
        prof += [(r * 1.35, 0.0), (r * 1.35, r * 0.18), (r * 1.02, r * 0.2)]
    else:
        prof += [(r, 0.0)]
    z0 = prof[-1][1]
    prof += [(r, z0 + h * 0.85), (r * 0.82, z0 + h), (0.0, z0 + h)]
    o = L.lathe2(name, prof, segments=6, mat=mat, cap_bottom=False, phase=math.pi / 6)
    o.data.transform(Matrix.Translation(loc) @ axis_rot(normal))
    return o


def tube(name, pts, r, sides=8, mat="M_Steel_Dark", fillet=0.0, caps=True):
    return A.tube(name, pts, r, sides=sides, fillet=fillet, mat=mat, caps=caps) if fillet > 0 else \
        A.tube(name, pts, r, sides=sides, mat=mat, caps=caps)


def part(name, objs, pivot=None, smooth_default=35.0):
    """Presmooth (per-part hints), join into one object `name`, origin at `pivot` (G-frame)."""
    objs = [o for o in objs if o is not None]
    A.presmooth(objs, smooth_default)
    o = M.join(objs, name) if len(objs) > 1 or objs[0].name != name else objs[0]
    if len(objs) == 1:
        o.name = name
        o.data.name = name
    if pivot is not None:
        M.set_origin(o, pivot)
    return o


def empty(name, loc, rot_deg=(0.0, 0.0, 0.0), size=0.03):
    """G-frame empty; rot_deg = Godot Euler XYZ in degrees (applied X, then Y, then Z)."""
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    return e


# ---------------------------------------------------------------- G-frame -> Blender
def to_blender(objs=None) -> None:
    """Convert unparented G-frame objects to Blender axes: data' = C·data, world' = C·W·C⁻¹."""
    M.refresh()
    for o in (objs or list(bpy.context.scene.objects)):
        if o.parent is not None:
            raise RuntimeError(f"{TAG} to_blender: {o.name} is parented; convert before parenting")
        w = o.matrix_world.copy()
        if o.type == "MESH":
            o.data.transform(C)
        o.matrix_world = C @ w @ C_INV
    M.refresh()


def parent(child, par) -> None:
    M.set_parent(child, par)


def gpos(o) -> Vector:
    """World position of an object in Godot axes (after to_blender)."""
    M.refresh()
    return C_INV @ o.matrix_world.translation


# ---------------------------------------------------------------- finishing / export
def finalize_all() -> None:
    """Box UVs (world scale) on every non-decal face; smoothing was done per part (presmooth)."""
    A.finalize_uv()


def uv_square(obj, centre, half, material_prefix=None) -> None:
    """Planar 0..1 UVs over the square [cx-half, cx+half] x [cy-half, cy+half] of the Godot XY plane
    (u left -> right, v bottom -> top as seen from +Z). Call AFTER to_blender (works on Blender X/Z)."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    M.refresh()
    mw = obj.matrix_world
    names = [m.name if m else "" for m in me.materials]
    for f in bm.faces:
        if material_prefix and not names[f.material_index].startswith(material_prefix):
            continue
        for lp in f.loops:
            p = mw @ lp.vert.co          # Blender world: x = Godot x, z = Godot y
            lp[uv].uv = ((p.x - (centre[0] - half[0])) / (2 * half[0]), (p.z - (centre[1] - half[1])) / (2 * half[1]))
    bm.to_mesh(me)
    bm.free()


def report(label: str) -> int:
    total = 0
    rows = []
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and not o.name.lower().startswith("qa"):
            t = L.tris(o)
            total += t
            rows.append((t, o.name))
    rows.sort(reverse=True)
    print(f"{TAG} {label}: {total} tris in {len(rows)} meshes")
    for t, n in rows[:60]:
        print(f"{TAG}     {t:6d}  {n}")
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


def verify_glb(path: str, required=(), identity=(), budget=None, expect=None, parents=None, show=(),
               rot_expect=None) -> list:
    """Check the exported GLB: required node names; identity rest rotation/scale; model-space positions
    (Godot, 1 mm); expected parents; expected local rotations {name: (x, y, z) deg}; tris vs budget."""
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
                tris += acc[prim["indices"]]["count"] // 3
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
    for r, p in (expect or {}).items():
        if r not in by_name:
            continue
        wt = world(by_name[r]).translation
        if (wt - Vector(p)).length > 1e-3:
            errors.append(f"{r}: model position {tuple(round(c, 4) for c in wt)} != expected {p}")
    for r, par in (parents or {}).items():
        if r not in by_name:
            continue
        got = nodes[parent_of[by_name[r]]].get("name") if by_name[r] in parent_of else None
        if got != par:
            errors.append(f"{r}: parent {got} != expected {par}")
    for r, eul in (rot_expect or {}).items():
        if r not in by_name:
            continue
        q = nodes[by_name[r]].get("rotation", (0, 0, 0, 1))
        want = Matrix.Rotation(math.radians(eul[2]), 3, "Z") @ Matrix.Rotation(math.radians(eul[1]), 3, "Y") @ \
            Matrix.Rotation(math.radians(eul[0]), 3, "X")
        got = Quaternion((q[3], q[0], q[1], q[2])).to_matrix()
        if max(abs(got[i][j] - want[i][j]) for i in range(3) for j in range(3)) > 1e-3:
            errors.append(f"{r}: local rotation {tuple(round(math.degrees(a), 2) for a in got.to_euler('XYZ'))} != {eul}")
    print(f"{TAG}-verify {os.path.basename(path)}: nodes={len(nodes)} tris={tris}"
          + (f" budget={budget} {'OK' if tris <= budget else 'OVER'}" if budget else ""))
    if budget and tris > budget:
        errors.append(f"tris {tris} > budget {budget}")
    for r in show:
        if r not in by_name:
            continue
        i = by_name[r]
        n = nodes[i]
        w = world(i)
        q = n.get("rotation", (0, 0, 0, 1))
        e = Quaternion((q[3], q[0], q[1], q[2])).to_euler("XYZ")
        wt = w.translation
        par = nodes[parent_of[i]].get("name") if i in parent_of else "-"
        print(f"{TAG}-verify   {r:22s} parent={par:16s} local_t={tuple(round(c, 4) for c in n.get('translation', (0, 0, 0)))} "
              f"rot_deg=({math.degrees(e.x):+.1f}, {math.degrees(e.y):+.1f}, {math.degrees(e.z):+.1f}) "
              f"model=({wt.x:+.4f}, {wt.y:+.4f}, {wt.z:+.4f})")
    for e in errors:
        print(f"{TAG}-verify ERROR {e}")
    if not errors:
        print(f"{TAG}-verify all checks passed")
    return errors


def check_names(path: str) -> int:
    script = os.path.join(ROOT, "tools", "blender", "check_glb_names.py")
    r = subprocess.run(["python3", script, path], capture_output=True, text=True)
    print(f"{TAG} check_glb_names: rc={r.returncode} {r.stdout.strip()} {r.stderr.strip()}")
    return r.returncode


def mesh_bounds_godot(objs):
    """Godot-axis AABB of the given (Blender-axis) mesh objects."""
    M.refresh()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.data.vertices:
            p = C_INV @ (o.matrix_world @ v.co)
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    return lo, hi


# ---------------------------------------------------------------- QA scene
def G(x, y, z) -> Vector:
    return Vector((x, -z, y))


def qa_begin(bounces: int = 8) -> None:
    """Call AFTER export. Shared-machine render settings + Cycles-friendly glass."""
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    P.preview_tweak()
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        if mat.name in ("M_Glass_Dark", "M_Film"):
            b.inputs["Alpha"].default_value = 1.0
        if mat.name == "M_Glass":
            b.inputs["Roughness"].default_value = 0.02
        if mat.name == "M_Velvet":
            b.inputs["Sheen Weight"].default_value = 0.6
            b.inputs["Sheen Tint"].default_value = (1.0, 0.55, 0.6, 1.0)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    P.render_threads(2)
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 12


def qa_import(path: str, pos=(0, 0, 0), yaw_deg: float = 0.0, parent_obj=None, prefix: str = "qa_"):
    """Import a GLB under a holder empty (QA only). With parent_obj the holder sits at identity under it."""
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


def _qbox(name, mn, mx, mat):
    """QA box from Godot min/max corners."""
    a, b = G(*mn), G(*mx)
    lo = Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))
    hi = Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))
    o = M.box(name, tuple(hi - lo), loc=tuple((hi + lo) / 2), mat=mat, bevel=0.0)
    return o


def qa_room(with_vault_interior_shell: bool = False) -> bool:
    """room_archive.glb if it exists (True), otherwise a proxy shell around the vault (north wall with the
    2.1 x 2.1 opening x 0.45..2.55, y 0.30..2.40, 0.2 thick)."""
    room = model_glb("room_archive")
    if os.path.exists(room):
        qa_import(room)
        return True
    paint, plaster = "M_Paint_Green", "M_Plaster_Wall"
    _qbox("qa_floor", (-5.2, -0.05, -3.7), (5.2, 0.0, 3.7), "M_Linoleum")
    _qbox("qa_ceiling", (-5.2, 3.6, -3.7), (5.2, 3.7, 3.7), "M_Ceiling")
    dado = 1.40
    # north wall pieces around the opening
    for nm, x0, x1, y0, y1 in (("w", -5.2, 0.45, 0.0, 3.6), ("e", 2.55, 5.2, 0.0, 3.6),
                               ("b", 0.45, 2.55, 0.0, 0.30), ("t", 0.45, 2.55, 2.40, 3.6)):
        lo_y1 = min(y1, dado)
        if y0 < dado:
            _qbox(f"qa_wall_n_{nm}_lo", (x0, y0, -3.7), (x1, lo_y1, -3.5), paint)
        if y1 > dado:
            _qbox(f"qa_wall_n_{nm}_hi", (x0, max(y0, dado), -3.7), (x1, y1, -3.5), plaster)
    for nm, mn, mx in (("e", (5.0, 0, -3.5), (5.2, 3.6, 3.5)), ("w", (-5.2, 0, -3.5), (-5.0, 3.6, 3.5)),
                       ("s", (-5.2, 0, 3.5), (5.2, 3.6, 3.7))):
        lo, hi = list(mn), list(mx)
        hi[1] = dado
        _qbox(f"qa_wall_{nm}_lo", tuple(lo), tuple(hi), paint)
        lo[1] = dado
        hi[1] = 3.6
        _qbox(f"qa_wall_{nm}_hi", tuple(lo), tuple(hi), plaster)
    # dado rail + baseboard on the north wall, pilaster at x = -0.55
    for x0, x1 in ((-5.0, 0.45), (2.55, 5.0)):
        _qbox("qa_dado", (x0, 1.38, -3.5), (x1, 1.43, -3.47), "M_Wood_Walnut")
        _qbox("qa_base", (x0, 0.0, -3.5), (x1, 0.15, -3.478), "M_Wood_Walnut")
    _qbox("qa_pilaster", (-0.75, 0.0, -3.5), (-0.35, 3.6, -3.38), "M_Concrete")
    if with_vault_interior_shell and not os.path.exists(model_glb("vault_interior")):
        _qbox("qa_vault_back", (0.45, 0.0, -5.35), (2.55, 2.65, -5.2), "M_Steel_Dark")
    return False


def qa_neighbours(items) -> None:
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


PENDANTS = [(-3.0, 3.6, -2.0), (0.0, 3.6, -2.4), (3.0, 3.6, -2.0), (-2.8, 3.6, 1.4), (0.0, 3.6, 1.6), (3.0, 3.6, 1.4)]


def qa_room_lights(energy=150.0) -> None:
    """Warm point lights where the archive pendants' OmniLights are (pendant y - 0.85), the desk lamp."""
    for i, p in enumerate(PENDANTS):
        qa_light(f"pendant{i}", "POINT", (p[0], p[1] - 0.85, p[2]), energy, "FFC58A", radius=0.15)
    qa_light("desk", "POINT", (3.1, 1.2, -3.2), 25.0, "FFB46B", radius=0.05)


def qa_fill(cam, energy=12.0) -> None:
    """The game's focus_fill light that follows the camera in close-ups (offset (0.12, 0.18, 0.05))."""
    qa_light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), energy, "FFE2C2", radius=0.2)


def qa_clear_lights() -> None:
    for o in [o for o in bpy.context.scene.objects if o.type == "LIGHT" and o.name.startswith("qa_")]:
        bpy.data.objects.remove(o, do_unlink=True)


def lens_for_vfov(vfov_deg: float, res=(960, 640)) -> float:
    """Blender lens (36 mm sensor, horizontal fit for landscape) matching a Godot vertical FOV."""
    aspect = res[0] / res[1]
    return 18.0 / (math.tan(math.radians(vfov_deg) / 2) * aspect)


NO_LIGHTS = [((0, 0, 1), 0.0, "FFFFFF", 0.1)]


def shoot(name, cam, target, vfov=50.0, res=(960, 640), samples=32, world=0.05, lights=None):
    """Render qa/blender/ch2/<name>.png from Godot camera/target points (Godot vertical FOV)."""
    return M.render_preview(f"{QA_SUB}/{name}", G(*cam), G(*target), lens=lens_for_vfov(vfov, res), res=res,
                            samples=min(samples, 32), world_strength=world,
                            lights=lights if lights is not None else NO_LIGHTS)


# ---------------------------------------------------------------- QA poses (never exported)
_AX = {"x": Vector((1, 0, 0)), "y": Vector((0, 0, 1)), "z": Vector((0, -1, 0))}


def pose_rot(obj, axis: str, deg: float) -> None:
    """Rotate an object about its own local Godot axis by `deg` (Godot sign convention)."""
    obj.matrix_basis = obj.matrix_basis @ Matrix.Rotation(math.radians(deg), 4, _AX[axis])
    M.refresh()


def pose_slide(obj, godot_vec) -> None:
    """Translate in the parent's space by a Godot vector (as ArchiveVisuals._bolt does)."""
    obj.matrix_basis = Matrix.Translation(C @ Vector(godot_vec)) @ obj.matrix_basis
    M.refresh()


def attach(path, mount_obj, prefix="qa_item_"):
    """Import an item GLB under a mount empty with an identity transform (QA only)."""
    return qa_import(path, parent_obj=mount_obj, prefix=prefix)


# ---------------------------------------------------------------- vault_overlay.gdshader emulation (QA only)
def _img_alpha(path):
    import numpy as np
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return px[::-1, :, 3]          # row 0 = top (Godot UV v down)


def disc_overlay_image(name, rot_left, rot_right, zoom, left_on=True, right_on=True, unlocked=False,
                       clockwise=True, n=512):
    """Bake what vault_overlay.gdshader draws on glass_disc for a logic state into a Blender image.

    clockwise=True rotates the crystal images CLOCKWISE as seen by 45° per collar step (what the
    engraving needs); clockwise=False reproduces the shader formula as written in the repo today."""
    import numpy as np
    eng = _img_alpha(os.path.join(DECALS_CH2, "vault_engraving.png"))
    mark = _img_alpha(os.path.join(DECALS_CH2, "glyph_mark.png"))
    sign = _img_alpha(os.path.join(DECALS_CH2, "glyph_sign.png"))
    V, U = np.mgrid[0:n, 0:n].astype(np.float32)
    U = (U + 0.5) / n
    V = (V + 0.5) / n

    def sample(a, u, v):
        h, w = a.shape
        x = np.clip((u * w).astype(int), 0, w - 1)
        y = np.clip((v * h).astype(int), 0, h - 1)
        out = a[y, x].copy()
        out[(u < 0) | (v < 0) | (u > 1) | (v > 1)] = 0.0
        return out

    def rot_sample(a, rot, scale):
        px, py = U - 0.5, V - 0.5
        c, s = math.cos(rot), math.sin(rot) * (-1.0 if clockwise else 1.0)
        return sample(a, (c * px - s * py) / scale + 0.5, (s * px + c * py) / scale + 0.5)

    r = np.sqrt((U - 0.5) ** 2 + (V - 0.5) ** 2)
    col = np.zeros((n, n, 3), np.float32) + np.array([0.16, 0.19, 0.19], np.float32)
    col += (0.06 * (1 - r * 2))[..., None]
    col += np.array([0.85, 0.82, 0.72], np.float32) * (sample(eng, U, V) * 0.32)[..., None]
    lv = rot_sample(mark, math.radians(45 * rot_left), 1.0) * (1.0 if left_on else 0.0)
    rv = rot_sample(sign, math.radians(45 * rot_right), 1.0 - 0.15 * zoom) * (1.0 if right_on else 0.0)
    glow = np.array([0.62, 0.95, 1.0], np.float32)
    col += glow * ((lv + rv) * (1.1 + (1.6 if unlocked else 0.0)) * 0.92)[..., None]
    col += glow * ((0.25 if unlocked else 0.0) * (1 - r * 2))[..., None]
    col = np.clip(col, 0, 1)
    alpha = np.where(r > 0.5, 0.0, 1.0).astype(np.float32)
    rgba = np.concatenate([col, alpha[..., None]], -1)[::-1]     # back to Blender bottom-up rows
    img = bpy.data.images.new(name, n, n, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels[:] = rgba.ravel()
    return img


def emissive_image_material(name, img, strength=1.0, alpha_from_image=True):
    """QA-only unshaded-looking material: emission = image colour (approximates Godot 'unshaded')."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    if alpha_from_image:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
        nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    else:
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def override_material(obj, mat) -> list:
    """Swap every slot of obj to mat (QA only); returns the old list for restore_material."""
    old = [s.material for s in obj.material_slots]
    for s in obj.material_slots:
        s.material = mat
    return old


def restore_material(obj, old) -> None:
    for s, m in zip(obj.material_slots, old):
        s.material = m


def glow_material(name, colour="CFF6FF", strength=6.0, base="CFF6FF", alpha=1.0):
    """QA-only emissive look for parts the code makes glow (light pipes, lamps)."""
    mat = M.material(name, color=base, rough=0.2, metal=0.0, emission=colour, emission_strength=strength,
                     alpha=alpha)
    return mat
