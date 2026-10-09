"""MYSTERY ROOM — helpers for the Chapter 2 group A (architecture) models:
room_archive, archive_pendant, vent_grille, floor_hatch, projection_screen, library_ladder.

Builds on mrlib / lib_arch (never edit those: they are shared).

Everything here takes **Godot coordinates** (x, y up, z toward the viewer / south) and converts them to
Blender (x, -z, y), so the model scripts read straight from docs/models/ch2.md.

  * G(x, y, z)                  Godot point -> Blender Vector
  * gbox(name, mn, mx, ...)     bevelled box from Godot min/max corners
  * gcyl / glathe(axis=...)     cylinders / lathes standing on a Godot point along a Godot axis
  * gtube(name, pts, r)         round tube along Godot points (lib_arch.tube)
  * gquad(...)                  decal quad with UV 0..1 (u left->right, v bottom->top as seen)
  * gframe(origin, ex, ey)      Blender matrix of a local frame given in Godot vectors
  * part(name, objs, pivot)     join parts into one object with its origin at a Godot pivot
  * mount(name, loc, par)       empty at a Godot point (identity rotation unless given)
  * verify_glb(...)             reads the exported GLB: names, pivots, identity rotations, tris
  * qa_* / shoot(...)           QA scene: imports, lights, posing, Godot-FOV cameras, 2 render threads
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
import lib_arch as A  # noqa: E402

ROOT = M.ROOT
DECALS2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
TEX = os.path.join(ROOT, "game", "assets", "textures")
QA_SUB = "ch2"
TAG = "[arch]"

FONT_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

# New Chapter 2 slots (docs/models/ch2.md §0) and game slots mrlib.PREVIEW does not know (.tres values).
EXTRA_SLOTS = {
    "M_Glass_Green": ("16472A", 0.07, 0.0, 1.0),
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 1.0),
    "M_Glass_Amber": ("5A2A0C", 0.08, 0.0, 0.82),
    "M_Enamel_Green": ("2F7A3A", 0.28, 0.0, 1.0),
    "M_Enamel_White": ("E8E2D4", 0.28, 0.0, 1.0),
    "M_Enamel_Amber": ("C98A1E", 0.28, 0.0, 1.0),
    "M_Enamel_Crimson": ("8E1B22", 0.28, 0.0, 1.0),
    "M_Enamel_Cobalt": ("1F3E7A", 0.28, 0.0, 1.0),
    "M_Felt": ("3A3A3A", 1.0, 0.0, 1.0),
}


# ---------------------------------------------------------------- coordinates
def G(x, y, z) -> Vector:
    """Godot (x, y, z) -> Blender Vector (x, -z, y)."""
    return Vector((x, -z, y))


def GV(v) -> Vector:
    return G(v[0], v[1], v[2])


def to_godot(v) -> tuple:
    return (v[0], v[2], -v[1])


def gbox(name, mn, mx, mat="M_Wood_Walnut", bevel=0.0, seg=1):
    a, b = G(*mn), G(*mx)
    lo = Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))
    hi = Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))
    return A.box_minmax(name, lo, hi, mat=mat, bevel=bevel, segments=seg)


AXES = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1), "-x": (-1, 0, 0), "-y": (0, -1, 0), "-z": (0, 0, -1)}


def gdir(axis) -> Vector:
    """Godot axis name or vector -> Blender unit vector."""
    v = AXES[axis] if isinstance(axis, str) else axis
    return GV(v).normalized()


def aim(obj, axis) -> None:
    """Bake a rotation that maps the mesh's local +Z onto the Godot direction `axis`."""
    q = Vector((0, 0, 1)).rotation_difference(gdir(axis))
    obj.data.transform(q.to_matrix().to_4x4())


def gcyl(name, r, h, base, axis="y", verts=24, mat="M_Brass_Aged", bevel=0.001, seg=1, r_top=None, smooth=60.0):
    """Cylinder of height h starting at Godot point `base`, running along the Godot axis."""
    o = M.cylinder(name, r, h, loc=(0, 0, h / 2), verts=verts, mat=mat, bevel=bevel, segments=seg, radius_top=r_top)
    A.place(o, Matrix.Identity(4))
    aim(o, axis)
    o.data.transform(Matrix.Translation(GV(base)))
    return A.hint(o, smooth)


def glathe(name, profile, base, axis="y", segments=24, mat="M_Brass_Aged", smooth=60.0):
    """Lathe [(r, h)] around the Godot axis through `base` (h measured along the axis)."""
    o = M.lathe(name, profile, segments=segments, mat=mat)
    aim(o, axis)
    o.data.transform(Matrix.Translation(GV(base)))
    return A.hint(o, smooth)


def glathe_loop(name, loop, base, axis="y", segments=24, mat="M_Brass_Aged", smooth=60.0):
    o = A.lathe_loop(name, loop, segments=segments, mat=mat)
    aim(o, axis)
    o.data.transform(Matrix.Translation(GV(base)))
    return A.hint(o, smooth)


def hint_torus(name, centre_blender, major, minor, axis="z", major_seg=24, minor_seg=6, mat="M_Brass_Polished"):
    """Torus around the Godot axis through a Blender point."""
    o = M.torus(name, major, minor, major_seg=major_seg, minor_seg=minor_seg, mat=mat)
    aim(o, axis)
    o.data.transform(Matrix.Translation(Vector(centre_blender)))
    return A.hint(o, 70)


def gtube(name, pts, r, sides=8, mat="M_Steel_Dark", fillet=0.0, fillet_segs=4, caps=True):
    return A.tube(name, [GV(p) for p in pts], r, sides=sides, fillet=fillet, fillet_segs=fillet_segs, mat=mat, caps=caps)


def gframe(origin, ex, ey) -> Matrix:
    """Blender matrix of a local frame: local x along Godot ex, local y along Godot ey, local z = ex x ey."""
    bx, by = GV(ex).normalized(), GV(ey).normalized()
    bz = bx.cross(by).normalized()
    return A.frame_matrix(GV(origin), bx, by, bz)


def gquad(name, centre, u_axis, v_axis, w, h, mat, uv=None):
    """Single quad facing u x v (Godot axes), UV 0..1 (or uv=(u0, v0, u1, v1))."""
    c = GV(centre)
    u = GV(u_axis).normalized() * (w / 2)
    v = GV(v_axis).normalized() * (h / 2)
    me = bpy.data.meshes.new(name)
    vs = [c - u - v, c + u - v, c + u + v, c - u + v]
    me.from_pydata([tuple(p) for p in vs], [], [(0, 1, 2, 3)])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    uvl = me.uv_layers.new(name="UVMap")
    u0, v0, u1, v1 = uv or (0.0, 0.0, 1.0, 1.0)
    for li, (uu, vv) in zip(range(4), ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        uvl.data[li].uv = (uu, vv)
    return o


def gpoly(name, pts2d, depth, matrix, mat="M_Brass_Aged", bevel=0.0005):
    """Extrude a CCW 2D outline (local x, y) by depth along local +z, then place by `matrix`."""
    o = M.extrude_profile(name, A.ccw(A.dedupe(pts2d)), depth, mat=mat, bevel=bevel)
    o.data.transform(matrix)
    return o


def gtext(name, body, size, matrix, depth=0.0008, font=FONT_SANS_B, mat="M_Lacquer_Black", resolution=2):
    """Low-poly 3D text in the local xy plane of `matrix` (reads along +x, up +y, faces +z)."""
    o = A.text_lowpoly(name, body, size, depth=depth, mat=mat, font_path=font, resolution=resolution)
    o.data.transform(matrix)
    return o


def screw(name, r, loc, normal, mat="M_Brass_Aged", slot=30.0, segs=6):
    return A.screw(name, r, GV(loc), gdir(normal), mat, slot, segs)


# ---------------------------------------------------------------- parts, mounts
def part(name, objs, pivot=None, presmooth=True):
    """Join `objs` into one object called `name`; origin at the Godot `pivot` (identity rotation)."""
    objs = [o for o in objs if o is not None]
    if presmooth:
        A.presmooth(objs)
    o = M.join(objs, name) if len(objs) > 1 else objs[0]
    o.name = name
    if o.data is not None:
        o.data.name = name
    if pivot is not None:
        M.set_origin(o, GV(pivot))
    return o


def parent(child, par) -> None:
    M.set_parent(child, par)


def mount(name, loc, par=None, rot_blender=None):
    """Empty at the Godot point `loc`. rot_blender: optional Blender-space rotation Matrix (3x3/4x4)."""
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.03
    mw = Matrix.Translation(GV(loc))
    if rot_blender is not None:
        mw = mw @ rot_blender.to_4x4()
    e.matrix_world = mw
    if par is not None:
        M.set_parent(e, par)
    return e


def godot_basis(ex, ey, ez) -> Matrix:
    """Blender rotation matrix whose model axes (Godot x, y, z) point along the given Godot directions.
    A Godot node's local x/y/z map to Blender x/-z... so build the Blender-space columns of the
    Godot-local axes: Blender local X = Godot x, local Y = -Godot z, local Z = Godot y."""
    bx = GV(ex).normalized()
    by = -GV(ez).normalized()
    bz = GV(ey).normalized()
    return Matrix((bx, by, bz)).transposed()


def finalize_all(wood_grain=True, objs=None) -> None:
    A.finalize_uv(objs)
    if wood_grain:
        for o in (objs or bpy.context.scene.objects):
            if o.type == "MESH":
                A.grain_uv(o)


def tris(obj) -> int:
    return A.tris(obj)


def report(label: str) -> int:
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    total = sum(A.tris(o) for o in objs)
    print(f"{TAG} {label}: total tris = {total}")
    for o in sorted(objs, key=lambda o: -A.tris(o))[:40]:
        print(f"{TAG}    {o.name:28s} {A.tris(o):6d}  mats={[m.name for m in o.data.materials if m]}")
    return total


# ---------------------------------------------------------------- materials
def ensure_materials() -> None:
    """Create the slots used here with their preview colours; QA-only texture hookups for the new
    Chapter 2 wall/floor slots (Godot uses the .tres files)."""
    A.prepare_materials()
    for name, (col, rough, metal, alpha) in EXTRA_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=col, rough=rough, metal=metal, alpha=alpha)
    # M_Paint_Green.tres = plaster_wall albedo x (0.65, 0.83, 0.80); M_Concrete.tres = stone textures
    A.prepare_tinted("M_Paint_Green", "plaster_wall", "A7D3CB", rough=0.6)
    A.prepare_tinted("M_Concrete", "stone", "D8D4CC", rough=0.85)
    _linoleum()


def _linoleum() -> None:
    """M_Linoleum: the real texture set (0.6 m repeat) if group F has written it, else a QA checker of
    0.30 m tiles so the tile alignment can be checked."""
    if bpy.data.materials.get("M_Linoleum") is not None:
        return
    folder = os.path.join(TEX, "linoleum")
    mat = M.material("M_Linoleum", image="")  # image="" -> no auto PBR hookup
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    if os.path.isdir(folder) and any(f.startswith("albedo") for f in os.listdir(folder)):
        M._attach_pbr(nt, bsdf, folder)
        mp.inputs["Scale"].default_value = (1 / 0.6, 1 / 0.6, 1.0)
        for nd in nt.nodes:
            if nd.type == "TEX_IMAGE":
                nt.links.new(mp.outputs["Vector"], nd.inputs["Vector"])
    else:
        ck = nt.nodes.new("ShaderNodeTexChecker")
        ck.inputs["Scale"].default_value = 1 / 0.3
        ck.inputs["Color1"].default_value = M.hex_rgba("2F4A3A")
        ck.inputs["Color2"].default_value = M.hex_rgba("B9B293")
        nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
        nt.links.new(ck.outputs["Color"], bsdf.inputs["Base Color"])


def decal(slot: str, fname: str):
    """Decal material with the group-F image if it exists (QA preview)."""
    p = os.path.join(DECALS2, fname)
    return M.material(slot, image=p if os.path.exists(p) else None)


# ---------------------------------------------------------------- export + verification
def export(name: str) -> str:
    path = A.export_lean(name)
    check_names(path)
    return path


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


def verify_glb(path: str, required=(), identity=(), budget: int | None = None, show=(), expect=None) -> list[str]:
    """Check an exported GLB: required node names exist; `identity` nodes have identity rotation and unit
    scale; `expect` = {name: (x, y, z)} model-space (Godot) positions to within 1 mm; prints tris and the
    transforms of `show` nodes. Returns the list of errors."""
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
    total = 0
    per = {}
    for n in nodes:
        if "mesh" in n:
            t = 0
            for prim in doc["meshes"][n["mesh"]]["primitives"]:
                t += acc[prim["indices"]]["count"] // 3 if "indices" in prim else acc[prim["attributes"]["POSITION"]]["count"] // 3
            per[n.get("name", "?")] = t
            total += t
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
    print(f"{TAG}-verify {os.path.basename(path)}: nodes={len(nodes)} tris={total}"
          + (f" budget={budget} {'OK' if total <= budget else 'OVER'}" if budget else ""))
    if budget and total > budget:
        errors.append(f"tris {total} > budget {budget}")
    for r in show:
        if r not in by_name:
            continue
        i = by_name[r]
        n = nodes[i]
        w = world(i)
        q = n.get("rotation", (0, 0, 0, 1))
        e = Quaternion((q[3], q[0], q[1], q[2])).to_euler("YXZ")
        wt = w.translation
        par = nodes[parent_of[i]].get("name") if i in parent_of else "-"
        print(f"{TAG}-verify   {r:22s} parent={par:18s} local_t={tuple(round(c, 4) for c in n.get('translation', (0, 0, 0)))} "
              f"rot_deg(x,y,z)=({math.degrees(e.x):+.1f}, {math.degrees(e.y):+.1f}, {math.degrees(e.z):+.1f}) "
              f"model_t=({wt.x:+.4f}, {wt.y:+.4f}, {wt.z:+.4f})")
    for e in errors:
        print(f"{TAG}-verify ERROR {e}")
    if not errors:
        print(f"{TAG}-verify all checks passed")
    return errors


def check_names(path: str) -> None:
    script = os.path.join(ROOT, "tools", "blender", "check_glb_names.py")
    r = subprocess.run(["python3", script, path], capture_output=True, text=True)
    print(f"{TAG} check_glb_names rc={r.returncode} {r.stdout.strip()} {r.stderr.strip()}")


# ---------------------------------------------------------------- QA scene
def qa_begin(bounces: int = 6, samples: int = 32) -> None:
    """Call AFTER export: shared-machine render settings (2 threads) + Cycles-friendly glass."""
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        n = mat.name
        if n in ("M_Glass", "M_Crystal", "M_Glass_Frosted", "M_Glass_Amber"):
            b.inputs["Alpha"].default_value = 1.0
            b.inputs["Transmission Weight"].default_value = 1.0
            b.inputs["IOR"].default_value = 1.45
            b.inputs["Roughness"].default_value = 0.02 if n != "M_Glass_Frosted" else 0.35
            if n == "M_Glass":
                b.inputs["Base Color"].default_value = M.hex_rgba("F2FAF6")
            if n == "M_Glass_Amber":
                b.inputs["Base Color"].default_value = M.hex_rgba("E8902E")
        if n == "M_Film":
            b.inputs["Alpha"].default_value = 1.0
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    sc.cycles.samples = min(samples, 32)
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 8
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.use_denoising = True


def model_glb(name: str) -> str:
    return os.path.join(M.MODELS_DIR, name + ".glb")


def qa_import(path: str, pos=(0, 0, 0), yaw_deg: float = 0.0, prefix: str = "qa_imp_"):
    """Import a GLB under a holder empty placed at the Godot position/yaw (QA only). The lowercase prefix
    matters: mrlib.render_preview deletes every object whose name starts with "QA" after a render."""
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
    holder.location = G(*pos)
    holder.rotation_euler = (0, 0, math.radians(yaw_deg))
    M.refresh()
    return holder


def qa_find(prefix_name: str):
    """Object imported by qa_import (qa_imp_<name>, possibly with a .001 suffix)."""
    for o in bpy.data.objects:
        if o.name == "qa_imp_" + prefix_name or o.name.startswith("qa_imp_" + prefix_name + "."):
            return o
    return None


def qa_place(objs, pos, yaw_deg: float, name="qa_place"):
    """Parent the built model roots to a holder at the Godot placement (QA only, after export)."""
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.location = G(*pos)
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    M.refresh()
    return root


def qa_light(name, kind, pos, energy, colour="FFE2C0", radius=0.05, target=None, spot_deg=None, blend=0.3):
    ld = bpy.data.lights.new("QA_" + name, kind)
    ld.energy = energy
    ld.color = M.hex_rgba(colour)[:3]
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = radius
    if kind == "AREA":
        ld.size = radius
    if kind == "SPOT" and spot_deg:
        ld.spot_size = math.radians(spot_deg)
        ld.spot_blend = blend
    lo = bpy.data.objects.new("QA_" + name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = G(*pos)
    if target is not None:
        M._look_at(lo, G(*target))
    return lo


PENDANTS = [(-3.0, 3.6, -2.0), (0.0, 3.6, -2.4), (3.0, 3.6, -2.0), (-2.8, 3.6, 1.4), (0.0, 3.6, 1.6), (3.0, 3.6, 1.4)]


def qa_room_lights(energy=110.0, booth=True, emergency=True) -> None:
    """Approximation of the game lighting (archive_room.gd _build_lights)."""
    for i, p in enumerate(PENDANTS):
        qa_light(f"pendant{i}", "POINT", (p[0], p[1] - 0.70, p[2]), energy, "FFC58A", radius=0.10)
    if emergency:
        for k, p in enumerate([(-4.7, 2.8, 0.25), (4.7, 2.8, 0.0)]):
            qa_light(f"emergency{k}", "POINT", p, 18.0, "FF9A3C", radius=0.05)
    if booth:
        qa_light("booth", "POINT", (-3.0, 2.55, 2.85), 45.0, "FFCF94", radius=0.04)
    qa_light("desk", "POINT", (3.1, 1.2, -3.2), 25.0, "FFB46B", radius=0.05)
    qa_light("banker", "POINT", (1.9, 1.15, 1.25), 22.0, "FFD29A", radius=0.05)
    qa_light("fill", "AREA", (0.0, 3.3, 0.0), 120.0, "C8D8E0", radius=6.0, target=(0.0, 0.0, 0.0))


def qa_clear() -> None:
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA") and o.type in ("LIGHT", "CAMERA")]:
        bpy.data.objects.remove(o, do_unlink=True)


def lens_for_vfov(vfov_deg: float, res=(960, 640)) -> float:
    """Blender lens (36 mm sensor, horizontal fit for landscape) matching a Godot vertical FOV."""
    aspect = res[0] / res[1]
    return 18.0 / (math.tan(math.radians(vfov_deg) / 2) * aspect)


NO_LIGHTS = [((0, 0, 1), 0.0, "FFFFFF", 0.1)]


def shoot(name, cam, target, vfov=None, lens=None, res=(960, 640), samples=32, world=0.05, lights=None):
    """Render qa/blender/ch2/<name>.png from Godot camera/target points (Godot vertical FOV)."""
    if lens is None:
        lens = lens_for_vfov(vfov or 50.0, res)
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    path = M.render_preview(f"{QA_SUB}/{name}", G(*cam), G(*target), lens=lens, res=res, samples=min(samples, 32),
                            world_strength=world, lights=lights if lights is not None else NO_LIGHTS)
    return path


def args_shots(args):
    """--shots=a,b,c restricts which QA renders run (all when absent)."""
    for a in args:
        if a.startswith("--shots="):
            return set(a.split("=", 1)[1].split(","))
    return None


def want(tag: str, sel) -> bool:
    return sel is None or tag in sel


def pose_rot(obj, axis_godot: str, deg: float) -> None:
    """QA pose: rotate obj about its LOCAL Godot axis (x/y/z) by deg (post-multiplied like the code)."""
    ax = {"x": Vector((1, 0, 0)), "y": Vector((0, 0, 1)), "z": Vector((0, -1, 0))}[axis_godot]
    obj.matrix_basis = obj.matrix_basis @ Matrix.Rotation(math.radians(deg), 4, ax)
    M.refresh()


def pose_slide(obj, godot_vec) -> None:
    obj.matrix_basis = obj.matrix_basis @ Matrix.Translation(GV(godot_vec))
    M.refresh()


# ---------------------------------------------------------------- geometry helpers (room shell)
class WF:
    """A wall-local frame in Godot terms: a = along the wall (u), b = up, c = out of the wall (n, into
    the room). u x up must equal n (right-handed)."""

    def __init__(self, origin, u, n):
        self.o = Vector(origin)
        self.u = Vector(u).normalized()
        self.n = Vector(n).normalized()
        self.up = Vector((0, 1, 0))
        assert (self.u.cross(self.up) - self.n).length < 1e-6, "WF: u x up != n"

    def p(self, a, b, c=0.0) -> Vector:
        """Godot point."""
        return self.o + self.u * a + self.up * b + self.n * c

    def m(self, c_off: float = 0.0) -> Matrix:
        """Blender matrix: local (a, b, c) -> Blender world."""
        return A.frame_matrix(GV(self.o + self.n * c_off), GV(self.u), GV(self.up), GV(self.n))


def lbox(name, wf: WF, a0, a1, b0, b1, c0, c1, mat, bevel=0.0, seg=1):
    """Box in a wall frame (local a/b/c ranges)."""
    o = M.box(name, (abs(a1 - a0), abs(b1 - b0), abs(c1 - c0)),
              loc=((a0 + a1) / 2, (b0 + b1) / 2, (c0 + c1) / 2), mat=mat, bevel=bevel, segments=seg)
    A.place(o, wf.m())
    return o


def hollow_tube(name, pts, r_out, r_in, sides=12, mat="M_Glass"):
    """Thick-walled round tube along Blender points (already filleted): outer + inner skins + end rings."""
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
    nrm = (ref - tans[0] * ref.dot(tans[0])).normalized()
    bm = bmesh.new()
    outer, inner = [], []
    for i in range(n):
        if i > 0:
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = q @ nrm
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        b = tans[i].cross(nrm)
        ro, ri = [], []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            d = nrm * math.cos(a) + b * math.sin(a)
            ro.append(bm.verts.new(pts[i] + d * r_out))
            ri.append(bm.verts.new(pts[i] + d * r_in))
        outer.append(ro)
        inner.append(ri)
    for i in range(n - 1):
        for j in range(sides):
            k = (j + 1) % sides
            bm.faces.new((outer[i][j], outer[i][k], outer[i + 1][k], outer[i + 1][j]))
            bm.faces.new((inner[i][j], inner[i + 1][j], inner[i + 1][k], inner[i][k]))
    for i, flip in ((0, True), (n - 1, False)):
        for j in range(sides):
            k = (j + 1) % sides
            f = (outer[i][j], inner[i][j], inner[i][k], outer[i][k])
            bm.faces.new(f if flip else tuple(reversed(f)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return A.hint(A.obj_from_bm(name, bm, mat), 60.0)


def clip_poly_x(poly, xa, xb):
    """Sutherland-Hodgman clip of a 2D polygon [(x, y)] to xa <= x <= xb."""
    def clip(pts, keep, inter):
        out = []
        for i in range(len(pts)):
            p, q = pts[i - 1], pts[i]
            if keep(q):
                if not keep(p):
                    out.append(inter(p, q))
                out.append(q)
            elif keep(p):
                out.append(inter(p, q))
        return out

    def ix(x0):
        def f(p, q):
            t = (x0 - p[0]) / (q[0] - p[0])
            return (x0, p[1] + (q[1] - p[1]) * t)
        return f
    pts = clip(list(poly), lambda p: p[0] >= xa - 1e-9, ix(xa))
    if pts:
        pts = clip(pts, lambda p: p[0] <= xb + 1e-9, ix(xb))
    return pts


def perim_paths(corners, closed, breaks, y):
    """Trim paths along a Godot (x, z) polygon at height y, with gaps.

    breaks: [((x0, z0), (x1, z1))] pairs of points on the polygon; the stretch between them is left out
    (each pair is taken along increasing perimeter distance). Returns lists of Blender points (corners kept).
    """
    pts = [Vector((x, z)) for x, z in corners]
    if closed:
        pts.append(pts[0])
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + (pts[i + 1] - pts[i]).length)
    L = cum[-1]

    def s_of(x, z):
        best = None
        P = Vector((x, z))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = b - a
            ln = d.length
            t = max(0.0, min(1.0, (P - a).dot(d) / (ln * ln)))
            dist = (a + d * t - P).length
            if best is None or dist < best[0] - 1e-9:
                best = (dist, cum[i] + t * ln)
        return best[1]

    def at(s):
        if closed:
            s = s % L
        for i in range(len(pts) - 1):
            if s <= cum[i + 1] + 1e-9:
                t = (s - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
                return pts[i].lerp(pts[i + 1], t)
        return pts[-1]

    iv = []
    for p0, p1 in breaks:
        a, b = s_of(*p0), s_of(*p1)
        iv.append((min(a, b), max(a, b)))
    iv.sort()
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    kept = []
    if not closed:
        cur = 0.0
        for a, b in merged:
            if a > cur:
                kept.append((cur, a))
            cur = max(cur, b)
        if cur < L:
            kept.append((cur, L))
    elif not merged:
        kept.append((0.0, L))
    else:
        for j in range(len(merged)):
            a = merged[j][1]
            b = merged[(j + 1) % len(merged)][0] + (L if j == len(merged) - 1 else 0.0)
            kept.append((a, b))
    corner_s = cum[:-1] if closed else cum[1:-1]
    paths = []
    for sa, sb in kept:
        if sb - sa < 0.03:
            continue
        ss = [sa, sb]
        for c in corner_s:
            for k in ((0, 1) if closed else (0,)):
                cs = c + k * L
                if sa + 1e-6 < cs < sb - 1e-6:
                    ss.append(cs)
        ss.sort()
        paths.append([G(at(s).x, y, at(s).y) for s in ss])
    return paths


def profile_rail(h=0.07):
    """Dado/chair rail: s out of the wall, u up. Cove under, torus bead, small cap (16 pts)."""
    pts = [(0.0, 0.0), (0.010, 0.0)]
    pts += A.arc(0.010, 0.010, 0.010, -90, 0, 2)[1:]
    pts += [(0.022, 0.014)]
    pts += A.arc(0.022, 0.030, 0.016, -90, 90, 5)[1:]
    pts += [(0.018, 0.050), (0.018, 0.056)]
    pts += A.arc(0.018, 0.063, 0.007, -90, 90, 2)[1:]
    pts += [(0.008, h), (0.0, h)]
    return pts
