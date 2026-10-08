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


def valve(name, loc=(0, 0, 0), quality="item"):
    """1950s octal power valve ("coke-bottle" ST envelope): bakelite base with 8 pins and a keyed spigot,
    glass envelope with real wall thickness (outer + inner surface), silver getter flash in the dome,
    mica spacers, grey anode with wings, support rods and the pinched glass stem. 115 mm tall above
    z = 0 (the underside of the base, which seats on the socket); pins reach 11.5 mm below; 38 mm across.
    quality: "item" (inventory close-ups), "mid" (installed in the radio: single-surface glass, no pins),
    "far" (static valves seen through the hatch)."""
    lx, ly, lz = loc
    item = quality == "item"
    segments = {"item": 20, "mid": 14, "far": 10}[quality]
    seg2 = max(8, segments // 2)
    parts = []
    base = [(0.0, 0.0), (0.0146, 0.0), (0.0160, 0.0016), (0.0163, 0.0185), (0.0155, 0.0215), (0.0128, 0.0225)]
    if not item:
        base = [(0.0155, 0.0), (0.0163, 0.0020), (0.0163, 0.0185), (0.0150, 0.0222)]
    parts.append(L.lathe2(name + "_base", base, segments=segments, mat="M_Bakelite", cap_top=False,
                          cap_bottom=False))
    if item:
        for k in range(8):
            a = TAU * k / 8 + TAU / 16
            pin = L.lathe2(name + "_pin", [(0.0, -0.0095), (0.0009, -0.0092), (0.0012, -0.0085), (0.0012, 0.0)],
                           segments=6, mat="M_Chrome", cap_top=False)
            pin.location = (0.0087 * math.cos(a), 0.0087 * math.sin(a), 0.0)
            parts.append(pin)
        parts.append(L.lathe2(name + "_spigot", [(0.0, -0.0115), (0.0036, -0.011), (0.0042, -0.0102),
                                                 (0.0042, 0.0)], segments=10, mat="M_Bakelite", cap_top=False))
        parts.append(M.box(name + "_key", (0.0016, 0.0016, 0.010), loc=(0.0043, 0.0, -0.0055), mat="M_Bakelite",
                           bevel=0.0))
        outer = [(0.0128, 0.0215), (0.0136, 0.0255), (0.0150, 0.036), (0.0180, 0.050), (0.0189, 0.061),
                 (0.0178, 0.073), (0.0153, 0.083), (0.0150, 0.097), (0.0132, 0.1045), (0.0085, 0.1095),
                 (0.0030, 0.1115), (0.0019, 0.1140), (0.0, 0.1148)]
        inner = [(0.0, 0.1100), (0.0072, 0.1082), (0.0122, 0.1034), (0.0141, 0.097), (0.0144, 0.083),
                 (0.0169, 0.073), (0.0180, 0.061), (0.0171, 0.050), (0.0141, 0.036), (0.0127, 0.0255),
                 (0.0119, 0.0215)]
        prof = outer + inner          # glass with thickness: outer surface up, inner surface back down
    else:
        prof = [(0.0130, 0.0215), (0.0150, 0.036), (0.0183, 0.051), (0.0187, 0.064), (0.0156, 0.082),
                (0.0150, 0.097), (0.0108, 0.1075), (0.0026, 0.1125), (0.0, 0.1145)]
    parts.append(L.lathe2(name + "_glass", prof, segments=segments, mat="M_Glass", cap_bottom=False,
                          cap_top=False))
    getter = [(0.0140, 0.095), (0.0134, 0.1015), (0.0112, 0.1055), (0.0068, 0.1080), (0.0, 0.1092)]
    if not item:
        getter = [(0.0140, 0.096), (0.0110, 0.1050), (0.0, 0.1092)]
    parts.append(L.lathe2(name + "_getter", getter, segments=segments, mat="M_Chrome", cap_bottom=False))
    if quality != "far":
        parts.append(L.lathe2(name + "_stem", [(0.0110, 0.0225), (0.0080, 0.027), (0.0040, 0.033), (0.0, 0.034)],
                              segments=seg2, mat="M_Glass", cap_bottom=False))
    for zm in ((0.040, 0.079) if item else (0.079,)):
        parts.append(L.lathe2(name + "_mica", [(0.0, zm), (0.0130, zm), (0.0130, zm + 0.0008), (0.0, zm + 0.0008)],
                              segments=seg2, mat="M_Glass_Frosted"))
    parts.append(M.box(name + "_anode", (0.016, 0.0075, 0.037), loc=(0.0, 0.0, 0.0602), mat="M_Steel_Dark",
                       bevel=0.0008 if item else 0.0, segments=1))
    if quality != "far":
        for sx in (-1, 1):
            parts.append(M.box(name + "_wing", (0.004, 0.0009, 0.033), loc=(sx * 0.0098, 0.0, 0.0602),
                               mat="M_Steel_Dark", bevel=0.0))
    if item:
        for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rod = L.lathe2(name + "_rod", [(0.00045, 0.030), (0.00045, 0.086)], segments=4, mat="M_Chrome",
                           cap_bottom=False, cap_top=False)
            rod.location = (sx * 0.0118, sy * 0.0028, 0.0)
            parts.append(rod)
    obj = M.join(parts, name)
    obj.data.transform(Matrix.Translation((lx, ly, lz)))
    M.set_origin(obj, (lx, ly, lz))
    return obj


def resmooth(obj, angle_deg=12.0) -> None:
    """Re-run smoothing with a tighter angle (crisp crystal facets, knurls) after mrlib.finalize."""
    M.smooth(obj, angle_deg)


# ---------------------------------------------------------------- items: centre of mass
def centre_of_mass(objs) -> Vector:
    """Uniform-density centroid of the (closed-ish) meshes via signed tetrahedra; falls back to the
    bounding-box centre if the volume is degenerate (open sheets such as paper)."""
    M.refresh()
    vol = 0.0
    acc = Vector((0, 0, 0))
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        me = o.data
        mw = o.matrix_world
        me.calc_loop_triangles()
        co = [mw @ v.co for v in me.vertices]
        for v in co:
            lo = Vector(map(min, lo, v))
            hi = Vector(map(max, hi, v))
        for t in me.loop_triangles:
            a, b, c = (co[i] for i in t.vertices)
            v6 = a.dot(b.cross(c))
            vol += v6
            acc += v6 * (a + b + c) / 4.0
    if abs(vol) < 1e-12:
        return (lo + hi) / 2
    com = acc / vol
    # sanity: keep inside the bounding box
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
