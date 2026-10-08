"""MYSTERY ROOM — helpers for hero devices (lumen_projector, radio) and inventory items.

Builds on mrlib + lib_mech (never edit those from here; mrlib is shared by every agent).
Conventions: metres, Blender Z-up, model front = Blender -Y (= Godot +Z after glTF export).
Godot = Blender (x, z, -y).

Main helpers
  ensure_materials()        preview colours for every slot used by the device/item scripts
  aim(obj, direction)       rotate mesh data so the lathe axis (+Z) points along `direction`
  revolve(...)              lathe2 + aim + move in one call (turned brass parts on any axis)
  knurl_ring(...)           straight-knurled grip band (focus collars, knobs)
  wedge(...)                tiny raised ridge/notch (tactile marks)
  text(...)                 engraved/printed text in the display, handwriting or sans fonts
  centre_of_mass(objs)      volume-weighted centroid (uniform density) of closed meshes
  recentre(objs)            move a whole item so its centre of mass sits at the origin
  qa_tweak()                QA-only Cycles look (real glass / crystal transmission, emissives)
  shot(...)                 QA render with a dark floor at a given height
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402

ROOT = M.ROOT
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
FONT_DISPLAY = os.path.join(FONTS, "CormorantGaramond-Bold.ttf")
FONT_HAND = os.path.join(FONTS, "Caveat-Variable.ttf")
FONT_SANS_B = L.FONT_SANS_B
FONT_COND_B = L.FONT_COND_B
TAU = 2.0 * math.pi

# Slots not known to mrlib.PREVIEW / lib_mech.EXTRA_MATERIALS.
# name: (hex, roughness, metallic, emission hex or None, alpha)
DEV_MATERIALS = {
    "M_Glass_UV": ("2C1748", 0.06, 0.0, None, 0.8),     # Wood's glass (UV filter), dark violet
    "M_String_Red": ("A0201C", 0.8, 0.0, None, 1.0),    # exists in game/assets/materials (ribbon, string)
}


def tinted(name, colour, rough, folder, uv_scale, metal=0.0):
    """QA preview like a Godot StandardMaterial3D: albedo texture x colour with uv1_scale (box UVs)."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = M.material(name, color=colour, rough=rough, metal=metal, image="")
    alb = os.path.join(ROOT, "game", "assets", "textures", folder, "albedo.jpg")
    if not os.path.exists(alb):
        return mat
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(alb, check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs["B"].default_value = M.hex_rgba(colour)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], mix.inputs["A"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return mat


def ensure_materials() -> None:
    tinted("M_Grille_Fabric", "B8A27A", 0.95, "fabric", 6.0)      # matches M_Grille_Fabric.tres
    L.ensure_materials()
    for name, (hx, rough, metal, emis, alpha) in DEV_MATERIALS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, emission=emis, alpha=alpha)


# ---------------------------------------------------------------- orientation
def aim(obj, direction) -> None:
    """Rotate the mesh data so its local +Z points along `direction` (mesh stays at the origin)."""
    d = Vector(direction).normalized()
    z = Vector((0, 0, 1))
    if (d - z).length < 1e-9:
        return
    if (d + z).length < 1e-9:
        obj.data.transform(Matrix.Rotation(math.pi, 4, "X"))
        return
    q = z.rotation_difference(d)
    obj.data.transform(q.to_matrix().to_4x4())


def bake(obj, loc=(0, 0, 0), rot=(0, 0, 0)) -> None:
    """Bake rotation (Euler XYZ, radians) then translation into the mesh data."""
    obj.data.transform(Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4())


def axis_matrix(direction, up_hint=(0, 0, 1)) -> Matrix:
    """Rotation whose +Z = direction and whose +Y is as close as possible to `up_hint`."""
    z = Vector(direction).normalized()
    up = Vector(up_hint)
    if abs(z.dot(up.normalized())) > 0.999:
        up = Vector((1, 0, 0))
    x = up.cross(z).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed()
    return m.to_4x4()


def revolve(name, profile, direction=(0, 0, 1), loc=(0, 0, 0), segments=24, mat="M_Brass_Aged",
            up_hint=(0, 0, 1), **kw):
    """lathe2 profile [(r, z[, flags])] whose axis points along `direction`, with the profile z=0
    at `loc`. The lathe's angle 0 (local +X) ends up on `up_hint` x direction (see axis_matrix)."""
    obj = L.lathe2(name, profile, segments=segments, mat=mat, **kw)
    obj.data.transform(Matrix.Translation(loc) @ axis_matrix(direction, up_hint))
    return obj


def knurl_profile(r, z0, z1, depth, chamfer=0.0008):
    """Profile chunk for a knurled band from z0 to z1 (use with lathe2(knurl=depth))."""
    return [(r - chamfer, z0), (r, z0 + chamfer, "k"), (r, z1 - chamfer, "k"), (r - chamfer, z1)]


def wedge(name, length, width, height, loc, direction_len=(0, 1, 0), normal=(0, 0, 1),
          mat="M_Brass_Polished", pyramid=False) -> bpy.types.Object:
    """Triangular ridge (no bottom face, 6 tris) of `length` along `direction_len`, base `width`,
    apex `height` above its base along `normal`. `loc` = base centre."""
    t = Vector(direction_len).normalized()
    n = Vector(normal).normalized()
    s = t.cross(n).normalized()
    c = Vector(loc)
    hl, hw = length / 2, width / 2
    bm = bmesh.new()
    a0 = bm.verts.new(c - t * hl - s * hw)
    a1 = bm.verts.new(c - t * hl + s * hw)
    b0 = bm.verts.new(c + t * hl - s * hw)
    b1 = bm.verts.new(c + t * hl + s * hw)
    if pyramid:      # 4-tri elongated pyramid (single apex)
        ap = bm.verts.new(c + n * height)
        bm.faces.new((a0, ap, a1))
        bm.faces.new((b0, b1, ap))
        bm.faces.new((a0, b0, ap))
        bm.faces.new((a1, ap, b1))
    else:            # 6-tri ridge
        a2 = bm.verts.new(c - t * hl * 0.6 + n * height)
        b2 = bm.verts.new(c + t * hl * 0.6 + n * height)
        bm.faces.new((a0, a2, a1))
        bm.faces.new((b0, b1, b2))
        bm.faces.new((a0, b0, b2, a2))
        bm.faces.new((a1, a2, b2, b1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, mat)
    # recalc_face_normals can flip an open shell inward: make the faces point away from the base centre
    me = obj.data
    score = sum((p.center - c).dot(p.normal) for p in me.polygons)
    if score < 0:
        me.flip_normals()
    return obj


def text(name, body, size, font=FONT_DISPLAY, depth=0.0, mat="M_Bakelite", loc=(0, 0, 0), rot=(0, 0, 0),
         res=2, align="CENTER", spacing=1.0):
    return L.text_flat(name, body, size, font=font, depth=depth, res=res, align=align, mat=mat, loc=loc, rot=rot,
                       spacing=spacing)


def obj_from_bm(name, bm, mat) -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, mat)
    return obj


def mesh(name, verts, faces, mat="M_Paper") -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, mat)
    return obj


def solidify(obj, thickness, offset=-1.0) -> None:
    mod = obj.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = offset
    mod.use_even_offset = True
    M.apply_modifiers(obj)


def rename(obj, name):
    obj.name = name
    if obj.data is not None:
        obj.data.name = name
    return obj


# ---------------------------------------------------------------- shared parts
def crystal_lens(name, centre=(0, 0, 0), segments=32, ticks=24, low=False):
    """Strand's crystal lens: a 12-facet rose-cut crystal (M_Crystal) held by a knurled, engraved brass
    ring. 70 mm across, 12 mm thick ring. Disc normal along -Y (front), origin at the lens centre.
    Used by crystal_lens.glb and by lumen_projector's `lens_installed` (low=True: no hidden back face,
    no screws). Call resmooth() after mrlib.finalize so the facets stay crisp."""
    cx, cy, cz = centre
    ro, ri, h = 0.0348, 0.0294, 0.006
    c = 0.0009
    if low:
        prof = [(ro, -h), (ro, -0.0022, "k"), (ro, 0.0022, "k"), (ro, h - c), (ro - c, h), (ri + 0.0006, h),
                (ri, h - 0.0012)]
        bands = [None, "M_Brass_Aged", None, None, None, None]
    else:
        prof = [(ri, -h), (ro - c, -h), (ro, -h + c), (ro, -0.0032), (ro, -0.0022, "k"), (ro, 0.0022, "k"),
                (ro, 0.0032), (ro, h - c), (ro - c, h), (ri + 0.0006, h), (ri, h - 0.0008), (ri, -h + 0.0008),
                (ri, -h)]
        bands = [None, None, None, None, "M_Brass_Aged", None, None, None, None, None, None, None]
    ring = revolve(name + "_ring", prof, direction=(0, -1, 0), segments=segments, knurl=0.0009,
                   mat="M_Brass_Polished", cap_bottom=False, cap_top=False, band_mats=bands)
    parts = [ring]
    # rose-cut crystal (both faces), 12 facets
    gem = [(0.0, -0.0080), (0.012, -0.0074), (0.0225, -0.0056), (0.0302, -0.0024), (0.0302, 0.0024),
           (0.0225, 0.0056), (0.012, 0.0074), (0.0, 0.0080)]
    cr = revolve(name + "_gem", gem, direction=(0, -1, 0), segments=12, mat="M_Crystal")
    parts.append(cr)
    # engraved ticks on the front face annulus + three tiny screws
    yf = -h - 0.00005
    rm = (ri + 0.0006 + ro - c) / 2
    for k in range(ticks):
        a = TAU * k / ticks + math.pi / 2
        ln = 0.0026 if k % (ticks // 4) == 0 else 0.0014
        tk = L.flat_shape("ltick", [L.rounded_rect(0.0005, ln, 0.0001, 1)], mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        L.to_front(tk, y_back=yf, x=(rm + 0.0004) * math.cos(a), z=(rm + 0.0004) * math.sin(a))
        parts.append(tk)
    for k in range(0 if low else 3):
        a = math.pi / 2 + math.pi / 3 + k * TAU / 3
        parts.append(L.screw("lscrew", 0.0011, (rm * math.cos(a), yf, rm * math.sin(a)), normal=(0, -1, 0),
                             slot_angle=0.5 + k, segs=6))
    obj = M.join(parts, name)
    obj.data.transform(Matrix.Translation((cx, cy, cz)))
    M.set_origin(obj, (cx, cy, cz))
    return obj


VALVE_H = 0.0612        # glass height of the noval valve (z = 0 at the glass bottom / socket seat)
VALVE_R = 0.0108


def valve(name, loc=(0, 0, 0), quality="item", heater=None):
    """1950s miniature noval (B9A, EL84-style) valve: glass envelope with real wall thickness (outer +
    inner surface) and pinched exhaust tip, silver getter flash in the dome, nine pins with the keying
    gap, two grey anode plates with side wings, top and bottom micas, support rods and a cathode sleeve.
    21.6 mm across, 61 mm of glass above z = 0 (the glass bottom, which seats on the socket); the pins
    reach 7.3 mm below. quality: "item" (inspect close-ups), "mid" (installed in the radio: single-surface
    glass, no pins), "far" (static valves seen through the hatch).
    heater: optional object name -> the cathode becomes a separate child mesh with M_Copper (the game
    lights it with ModelUtil.set_emission for the "warm orange glow")."""
    lx, ly, lz = loc
    item = quality == "item"
    segments = {"item": 20, "mid": 16, "far": 10}[quality]
    seg2 = max(8, segments // 2)
    parts = []
    if item:
        for k in range(9):              # 9 pins on a 11.9 mm circle; position 9 is the keying gap
            a = TAU * k / 10 + TAU / 20
            pin = L.lathe2(name + "_pin", [(0.0005, 0.0006), (0.0005, -0.0066), (0.0003, -0.0072),
                                           (0.0, -0.0073)], segments=4, mat="M_Chrome", cap_bottom=False)
            pin.location = (0.00595 * math.cos(a), 0.00595 * math.sin(a), 0.0)
            parts.append(pin)
        outer = [(0.0, 0.0), (0.0094, 0.0), (0.0106, 0.0011), (0.0108, 0.0030), (0.0108, 0.0480), (0.0101, 0.0524),
                 (0.0083, 0.0553), (0.0048, 0.0574), (0.0019, 0.0580), (0.0015, 0.0604), (0.0, 0.0612)]
        inner = [(0.0, 0.0569), (0.0042, 0.0564), (0.0074, 0.0545), (0.0093, 0.0516), (0.0099, 0.0478),
                 (0.0099, 0.0050), (0.0088, 0.0038), (0.0, 0.0036)]
        prof = outer + inner            # glass with thickness: outer surface up, inner surface back down
    else:
        prof = [(0.0, 0.0), (0.0100, 0.0), (0.0108, 0.0025), (0.0108, 0.0480), (0.0098, 0.0528),
                (0.0062, 0.0566), (0.0018, 0.0580), (0.0013, 0.0604), (0.0, 0.0612)]
    parts.append(L.lathe2(name + "_glass", prof, segments=segments, mat="M_Glass", cap_bottom=False,
                          cap_top=False))
    getter = [(0.0099, 0.0465), (0.0095, 0.0505), (0.0079, 0.0538), (0.0046, 0.0559), (0.0, 0.0565)]
    if quality == "far":
        getter = [(0.0099, 0.047), (0.0072, 0.0545), (0.0, 0.0563)]
    parts.append(L.lathe2(name + "_getter", getter, segments=segments, mat="M_Chrome", cap_bottom=False))
    for zm in ((0.0100, 0.0405) if quality != "far" else (0.0405,)):
        parts.append(L.lathe2(name + "_mica", [(0.0, zm), (0.0094, zm), (0.0094, zm + 0.0007), (0.0, zm + 0.0007)],
                              segments=seg2, mat="M_Glass_Frosted"))
    for sy in (-1, 1):                  # two anode plates (open sides show the cathode)
        parts.append(M.box(name + "_plate", (0.0118, 0.0007, 0.027), loc=(0.0, sy * 0.0024, 0.0252),
                           mat="M_Steel_Dark", bevel=0.0))
    if quality != "far":
        for sx in (-1, 1):
            parts.append(M.box(name + "_wing", (0.0030, 0.0006, 0.025), loc=(sx * 0.0072, 0.0, 0.0252),
                               mat="M_Steel_Dark", bevel=0.0))
        parts.append(M.box(name + "_shield", (0.0062, 0.0062, 0.0035), loc=(0.0, 0.0, 0.0438), mat="M_Steel_Dark",
                           bevel=0.0))
    if item:
        for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rod = L.lathe2(name + "_rod", [(0.0003, 0.0036), (0.0003, 0.0425)], segments=4, mat="M_Chrome",
                           cap_bottom=False, cap_top=False)
            rod.location = (sx * 0.0074, sy * 0.0015, 0.0)
            parts.append(rod)
    cath = L.lathe2(name + "_cathode", [(0.0, 0.0090), (0.0013, 0.0092), (0.0013, 0.0410), (0.0, 0.0412)],
                    segments=6, mat="M_Copper")
    if heater is None:
        parts.append(cath)
    obj = M.join(parts, name)
    obj.data.transform(Matrix.Translation((lx, ly, lz)))
    M.set_origin(obj, (lx, ly, lz))
    if heater is not None:
        cath.name = heater
        cath.data.name = heater
        cath.location = (lx, ly, lz)
        M.set_parent(cath, obj)
    return obj


def resmooth(obj, angle_deg=12.0) -> None:
    """Re-run smoothing with a tighter angle (crisp crystal facets, knurls) after mrlib.finalize."""
    M.smooth(obj, angle_deg)


# ---------------------------------------------------------------- items: centre of mass
def centre_of_mass(objs) -> Vector:
    """Uniform-density centroid via signed tetrahedra, integrating only the watertight islands of each
    mesh (open shells such as printed labels, paper or decals carry no volume). Falls back to the
    bounding-box centre when nothing closed is found."""
    M.refresh()
    vol = 0.0
    acc = Vector((0, 0, 0))
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        for v in bm.verts:
            lo = Vector(map(min, lo, v.co))
            hi = Vector(map(max, hi, v.co))
        seen = set()
        for f0 in bm.faces:
            if f0.index in seen:
                continue
            island, stack = [], [f0]
            seen.add(f0.index)
            while stack:
                f = stack.pop()
                island.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index)
                            stack.append(g)
            edges = {e for f in island for e in f.edges}
            closed = all(len(e.link_faces) == 2 for e in edges)
            ilo = Vector((1e9, 1e9, 1e9))
            ihi = Vector((-1e9, -1e9, -1e9))
            for f in island:
                for v in f.verts:
                    ilo = Vector(map(min, ilo, v.co))
                    ihi = Vector(map(max, ihi, v.co))
            ref = (ilo + ihi) / 2
            ivol = 0.0
            iacc = Vector((0, 0, 0))
            for f in island:
                vs = [v.co - ref for v in f.verts]
                for i in range(1, len(vs) - 1):
                    a, b, c = vs[0], vs[i], vs[i + 1]
                    v6 = a.dot(b.cross(c))
                    ivol += v6
                    iacc += v6 * ((a + b + c) / 4.0 + ref)
            box = (ihi - ilo)
            if not closed and abs(ivol / 6.0) < 0.2 * box.x * box.y * box.z:
                continue          # open sheet (print, paper, decal): no volume
            vol += ivol
            acc += iacc
        bm.free()
    if abs(vol) < 1e-12:
        return (lo + hi) / 2
    com = acc / vol
    for i in range(3):
        if not (lo[i] - 1e-6 <= com[i] <= hi[i] + 1e-6):
            return (lo + hi) / 2
    return com


def recentre(objs, com=None) -> Vector:
    """Translate the root objects of an item so its centre of mass lands on the world origin."""
    com = com if com is not None else centre_of_mass(objs)
    for o in objs:
        if o.parent is None:
            o.location = o.location - com
    M.refresh()
    return com


def bounds(objs=None):
    M.refresh()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in (objs or bpy.context.scene.objects):
        if o.type != "MESH" or o.name.startswith("QA"):
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def describe(label) -> None:
    lo, hi = bounds()
    size = hi - lo
    print(f"[devices] {label}: tris={M.tri_count()} size(x,y,z)={tuple(round(c, 4) for c in size)} "
          f"min={tuple(round(c, 4) for c in lo)} max={tuple(round(c, 4) for c in hi)}")
    for o in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        if o.name.startswith("QA"):
            continue
        t = L.tris(o) if o.type == "MESH" else 0
        print(f"[devices]   {o.name:22s} {o.type:5s} tris={t:5d} origin={tuple(round(c, 4) for c in o.matrix_world.translation)}"
              f" parent={o.parent.name if o.parent else '-'}")


# ---------------------------------------------------------------- QA
def qa_tweak() -> None:
    """QA-only material tweaks for Cycles (call AFTER export; never affects the GLB)."""
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        n = mat.name
        if n in ("M_Glass", "M_Crystal", "M_Glass_UV"):
            bsdf.inputs["Alpha"].default_value = 1.0
            bsdf.inputs["Transmission Weight"].default_value = 1.0
            bsdf.inputs["IOR"].default_value = {"M_Crystal": 1.55}.get(n, 1.47)
            bsdf.inputs["Roughness"].default_value = 0.02
            if n == "M_Glass":
                bsdf.inputs["Base Color"].default_value = M.hex_rgba("F0F8F4")
            if n == "M_Crystal":
                bsdf.inputs["Base Color"].default_value = M.hex_rgba("DDF7FF")
            if n == "M_Glass_UV":
                bsdf.inputs["Base Color"].default_value = M.hex_rgba("5A2E9A")
        if n == "M_Emissive_MagicEye":
            bsdf.inputs["Emission Strength"].default_value = 1.2
    scene = bpy.context.scene
    scene.cycles.max_bounces = 10
    scene.cycles.transmission_bounces = 10
    scene.cycles.transparent_max_bounces = 12
    scene.cycles.glossy_bounces = 4


def shot(name, cam, target, lens=50.0, floor_z=0.0, samples=32, res=(960, 640), lights=None, world=0.25):
    if floor_z is not None:
        L.studio_floor(floor_z)
    path = M.render_preview(name, cam, target, lens=lens, res=res, samples=samples, world_strength=world,
                            lights=lights)
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA_floor")]:
        bpy.data.objects.remove(o, do_unlink=True)
    return path


def want_render() -> bool:
    return "--no-render" not in M.main_guard()


def export(name) -> str:
    return L.export_lean(name)


# ---------------------------------------------------------------- text on curved surfaces
def wrap_to_cylinder(obj, radius, axis_point=(0, 0, 0)) -> None:
    """Bend a flat object lying in a plane y = const (facing -Y, built with front_rot) onto a vertical
    cylinder of `radius` around the Z axis through `axis_point`: x becomes arc length (angle x / r measured
    from -Y), the depth offset (y - plane) is kept radially. Bakes the object transform."""
    M.apply_transform(obj)
    ax, ay, _ = axis_point
    ys = [v.co.y for v in obj.data.vertices]
    y0 = max(ys)                       # the face that touches the surface
    for v in obj.data.vertices:
        a = (v.co.x - ax) / radius
        r = radius + (y0 - v.co.y)
        v.co.x = ax + r * math.sin(a)
        v.co.y = ay - r * math.cos(a)
    obj.data.update()


def text_on_circle(name, body, size, radius, centre=(0.0, 0.0), start_deg=90.0, step_deg=None, font=FONT_COND_B,
                   mat="M_Bakelite", res=1, clockwise=True):
    """Letters set around a circle in the XY plane (like the engraving on a camera-lens ring), letter
    bottoms toward the centre, centred on `start_deg`, reading clockwise. Returns one joined object
    (faces +Z, lying at z = 0); use lib_mech.to_front() to put it on a -Y facing surface."""
    step = step_deg if step_deg is not None else math.degrees(size * 0.62 / radius)
    n = len(body)
    total = step * (n - 1)
    parts = []
    for i, ch in enumerate(body):
        if ch == " ":
            continue
        a = math.radians(start_deg + (total / 2 - i * step) * (1 if clockwise else -1))
        t = L.text_flat(f"{name}_{i}", ch, size, font=font, res=res, mat=mat)
        t.data.transform(Matrix.Translation((0.0, -size * 0.05, 0.0)))     # centre the cap height
        t.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        t.data.transform(Matrix.Translation((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a), 0)))
        parts.append(t)
    return M.join(parts, name)


# ---------------------------------------------------------------- inventory-item pipeline
def item_main(name, build_fn, shots=(), post=None, lineup_rot=(0, 0, 0)):
    """Standard item build: reset, build, finalize (box UVs + smoothing), optional post-callback (decal UVs,
    resmoothing), move the centre of mass to the origin, export game/assets/models/<name>.glb, QA renders.
    shots: [(suffix, cam_loc, target, lens)] relative to the centred item (floor added under the item)."""
    M.reset_scene()
    ensure_materials()
    build_fn()
    M.finalize()
    if post:
        post()
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    com = recentre(roots, centre_of_mass(meshes))
    print(f"[devices] {name}: centre of mass moved to origin (was {tuple(round(c, 4) for c in com)})")
    export(name)
    describe(name)
    if want_render() and shots:
        qa_tweak()
        lo, _ = bounds()
        for (suffix, cam, target, lens) in shots:
            shot(f"item_{name}{suffix}", cam, target, lens=lens, floor_z=lo.z - 0.0005, samples=28, res=(800, 600))


def decimate(obj, ratio=0.5) -> None:
    """Collapse-decimate a dense flat mesh (handwriting text) to `ratio` of its faces."""
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    M.apply_modifiers(obj)


def hand(name, body, size, ratio=0.5, **kw):
    """Handwriting (Caveat) text geometry, decimated to keep the item budgets."""
    obj = text(name, body, size, font=FONT_HAND, res=1, **kw)
    decimate(obj, ratio)
    return obj
