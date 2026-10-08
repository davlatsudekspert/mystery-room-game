"""MYSTERY ROOM — extra helpers for hero mechanisms and inventory items.

Builds on mrlib (never edit mrlib from here). Everything is metres, Blender Z-up,
model front = Blender -Y (Godot +Z).

Main helpers
  ensure_materials()      preview colours for the enamel / decal / grille slots
  lathe2()                lathe with knurled rings, per-face materials and partial caps
  curve_solid()           extruded 2D outline with holes and a real bevel (gears, keys, plates)
  text_flat()             low-poly engraved/printed text geometry
  tube()                  smooth swept tube (cables, wires, bars)
  screw() / rivet()       slotted screw heads and domed rivets
  bevel_sharp()           bevel only the sharp edges of an object
  gear_outline(), circle(), rounded_rect(), arc_pts()   2D outlines
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

ROOT = M.ROOT
DECALS = os.path.join(ROOT, "game", "assets", "textures", "decals")
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
FONT_SERIF = os.path.join(FONT_DIR, "DejaVuSerif.ttf")
FONT_COND_B = os.path.join(FONT_DIR, "DejaVuSansCondensed-Bold.ttf")

TAU = 2.0 * math.pi

# name: (hex, roughness, metallic, emission hex or None, alpha, image file in decals/ or None)
EXTRA_MATERIALS = {
    "M_Enamel_Crimson": ("9A1C2B", 0.28, 0.0, None, 1.0, None),
    "M_Enamel_Amber": ("D68D1F", 0.28, 0.0, None, 1.0, None),
    "M_Enamel_Green": ("2F7D46", 0.28, 0.0, None, 1.0, None),
    "M_Enamel_Cobalt": ("1F46A6", 0.28, 0.0, None, 1.0, None),
    "M_Enamel_Violet": ("6A40B8", 0.28, 0.0, None, 1.0, None),
    "M_Enamel_White": ("EAE4D4", 0.3, 0.0, None, 1.0, None),
    "M_Emissive_MagicEye": ("38E07A", 0.2, 0.0, "38E07A", 1.0, None),
    "M_Grille_Fabric": ("8A7350", 0.95, 0.0, None, 1.0, None),
    "M_Decal_ClockFace": ("FFFFFF", 0.3, 0.0, None, 1.0, "clock_face.png"),
    "M_Decal_PanelDiagram": ("FFFFFF", 0.6, 0.0, None, 1.0, "panel_diagram.jpg"),
    "M_Decal_RadioDial": ("FFFFFF", 0.35, 0.0, None, 1.0, "radio_dial.jpg"),
}


def ensure_materials() -> None:
    """Create preview materials for slot names mrlib.PREVIEW does not know (call after reset_scene)."""
    for name, (hx, rough, metal, emis, alpha, img) in EXTRA_MATERIALS.items():
        if bpy.data.materials.get(name):
            continue
        M.material(name, color=hx, rough=rough, metal=metal, emission=emis, emission_strength=2.0,
                   alpha=alpha, image=os.path.join(DECALS, img) if img else None)


# ---------------------------------------------------------------- 2D outlines
def circle(r: float, n: int = 24, phase: float = 0.0, cx: float = 0.0, cy: float = 0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n)) for i in range(n)]


def arc_pts(r: float, a0: float, a1: float, n: int, cx: float = 0.0, cy: float = 0.0):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1)))
            for i in range(n)]


def rounded_rect(w: float, h: float, r: float, n: int = 3, cx: float = 0.0, cy: float = 0.0):
    """Counter-clockwise rounded rectangle centred at (cx, cy); n points per corner."""
    r = min(r, w / 2 - 1e-5, h / 2 - 1e-5)
    pts = []
    corners = [(w / 2 - r, -h / 2 + r, -math.pi / 2), (w / 2 - r, h / 2 - r, 0.0),
               (-w / 2 + r, h / 2 - r, math.pi / 2), (-w / 2 + r, -h / 2 + r, math.pi)]
    for (x, y, a) in corners:
        for i in range(n):
            t = a + (math.pi / 2) * i / max(1, n - 1)
            pts.append((cx + x + r * math.cos(t), cy + y + r * math.sin(t)))
    return pts


def rrect4(w: float, h: float, radii=(0.01, 0.01, 0.01, 0.01), n: int = 4, cx: float = 0.0, cy: float = 0.0):
    """Rounded rectangle with per-corner radii (bottom-right, top-right, top-left, bottom-left), CCW."""
    pts = []
    corners = [(w / 2, -h / 2, -math.pi / 2, -1, 1), (w / 2, h / 2, 0.0, -1, -1),
               (-w / 2, h / 2, math.pi / 2, 1, -1), (-w / 2, -h / 2, math.pi, 1, 1)]
    for (x, y, a, sx, sy), r in zip(corners, radii):
        if r <= 1e-6:
            pts.append((cx + x, cy + y))
            continue
        ccx, ccy = x + sx * r, y + sy * r
        for i in range(n):
            t = a + (math.pi / 2) * i / max(1, n - 1)
            pts.append((cx + ccx + r * math.cos(t), cy + ccy + r * math.sin(t)))
    return pts


def gear_outline(n: int, r_root: float, r_tip: float, phase: float = 0.0,
                 base_frac: float = 0.27, tip_frac: float = 0.15, flank: bool = True):
    """Counter-clockwise spur-gear outline. Tooth k is centred at angle phase + k*2π/n."""
    pts = []
    p = TAU / n
    rm = (r_root + r_tip) / 2
    for k in range(n):
        a = phase + k * p
        hb, ht = p * base_frac, p * tip_frac
        hm = (hb + ht) / 2 + p * 0.02
        seq = [(a - hb, r_root)]
        if flank:
            seq.append((a - hm, rm))
        seq += [(a - ht, r_tip), (a + ht, r_tip)]
        if flank:
            seq.append((a + hm, rm))
        seq += [(a + hb, r_root), (a + p / 2, r_root * 0.985)]
        for ang, r in seq:
            pts.append((r * math.cos(ang), r * math.sin(ang)))
    return pts


def kidney(r_in: float, r_out: float, a0: float, a1: float, n_arc: int = 4):
    """Curved slot (clock-wheel 'crossing') between radii r_in..r_out and angles a0..a1, CCW."""
    rc = (r_out - r_in) / 2
    rm = (r_out + r_in) / 2
    pts = arc_pts(r_out, a0, a1, n_arc)
    c1 = (rm * math.cos(a1), rm * math.sin(a1))
    for i in range(1, 3):
        t = a1 + math.pi * i / 3
        pts.append((c1[0] + rc * math.cos(t), c1[1] + rc * math.sin(t)))
    pts += arc_pts(r_in, a1, a0, n_arc)
    c0 = (rm * math.cos(a0), rm * math.sin(a0))
    for i in range(1, 3):
        t = a0 + math.pi + math.pi * i / 3
        pts.append((c0[0] + rc * math.cos(t), c0[1] + rc * math.sin(t)))
    return pts


# ---------------------------------------------------------------- solids
def _link(name: str, me: bpy.types.Mesh, loc=(0, 0, 0), rot=(0, 0, 0)) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def _set_mats(obj, mat_names, face_index_names) -> None:
    """face_index_names: list (per polygon) of material names."""
    slots = {}
    for nm in mat_names:
        if nm not in slots:
            slots[nm] = M.add_slot(obj, nm)
    for p, nm in zip(obj.data.polygons, face_index_names):
        p.material_index = slots[nm]


def lathe2(name: str, profile, segments: int = 32, mat: str = "M_Brass_Aged", knurl: float = 0.0,
           band_mats=None, mat_fn=None, loc=(0, 0, 0), rot=(0, 0, 0), phase: float = 0.0,
           cap_bottom: bool = True, cap_top: bool = True) -> bpy.types.Object:
    """Revolve [(r, z[, flags]), ...] around local Z, bottom to top.

    flags: 'k' = knurled ring (every other vertex pushed in by `knurl`).
    band_mats[k] = material of the band between profile points k and k+1 (None -> mat).
    mat_fn(k, i) -> material name for band k, angular sector i (overrides band_mats).
    r == 0 at either end closes it with a fan. Faces point outward.
    """
    bm = bmesh.new()
    rings = []
    for p in profile:
        r, z = p[0], p[1]
        flags = p[2] if len(p) > 2 else ""
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        ring = []
        for i in range(segments):
            a = phase + TAU * i / segments
            rr = r - knurl if ("k" in flags and i % 2 == 1) else r
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    face_mats = []

    def mat_for(k, i):
        if mat_fn is not None:
            return mat_fn(k, i) or mat
        if band_mats is not None and k < len(band_mats) and band_mats[k]:
            return band_mats[k]
        return mat

    for k in range(len(rings) - 1):
        a_ring, b_ring = rings[k], rings[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            if len(a_ring) == 1 and len(b_ring) == 1:
                continue
            if len(a_ring) == 1:
                f = bm.faces.new((a_ring[0], b_ring[j], b_ring[i]))
            elif len(b_ring) == 1:
                f = bm.faces.new((a_ring[i], a_ring[j], b_ring[0]))
            else:
                f = bm.faces.new((a_ring[i], a_ring[j], b_ring[j], b_ring[i]))
            face_mats.append(mat_for(k, i))
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
        face_mats.append(mat_for(0, 0))
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
        face_mats.append(mat_for(len(rings) - 2, 0))
    # orient: lathe faces built (i, j, up) are CCW seen from outside -> outward normals
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = _link(name, me, loc, rot)
    _set_mats(obj, list(dict.fromkeys(face_mats)), face_mats)
    return obj


def curve_solid(name: str, loops, depth: float, bevel: float = 0.0006, bevel_res: int = 0,
                mat: str = "M_Brass_Aged", loc=(0, 0, 0), rot=(0, 0, 0), drop_bottom: bool = False,
                keep_size: bool = True) -> bpy.types.Object:
    """Extrude closed 2D loops (outer + holes, even-odd) from z=0 to z=depth with a bevelled rim.

    `keep_size` shrinks the outline by the bevel so the outer size stays as drawn.
    `drop_bottom` removes the faces of the hidden bottom (z == 0) cap to save triangles.
    """
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    for loop in loops:
        sp = cu.splines.new("POLY")
        sp.points.add(len(loop) - 1)
        for i, (x, y) in enumerate(loop):
            sp.points[i].co = (x, y, 0.0, 1.0)
        sp.use_cyclic_u = True
    b = min(bevel, depth * 0.45)
    cu.extrude = max(depth / 2 - b, 0.0)
    cu.bevel_depth = b
    cu.bevel_resolution = bevel_res
    cu.offset = -b if keep_size else 0.0
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.transform(Matrix.Translation((0, 0, depth / 2)))
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    if drop_bottom:   # hidden bottom cap and its chamfer
        bottom = [f for f in bm.faces if all(v.co.z < b + 1e-6 for v in f.verts)]
        bmesh.ops.delete(bm, geom=bottom, context="FACES")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.name = name
    obj = _link(name, me, loc, rot)
    M.assign(obj, mat)
    return obj


def text_flat(name: str, text: str, size: float, font: str = FONT_SANS_B, depth: float = 0.0,
              res: int = 2, align: str = "CENTER", mat: str = "M_Bakelite", loc=(0, 0, 0), rot=(0, 0, 0),
              spacing: float = 1.0) -> bpy.types.Object:
    """Low-poly text geometry lying in local XY (reads along +X, faces +Z).

    depth > 0 extrudes it (z from 0..depth); depth == 0 gives a single printed/inlaid face.
    Use rot=(pi/2, 0, 0) to put it on a front (-Y facing) surface.
    """
    cu = bpy.data.curves.new(name + "_txt", "FONT")
    cu.body = text
    cu.size = size
    cu.resolution_u = res
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    if depth > 0:
        cu.extrude = depth / 2
    if os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    if depth > 0:
        me.transform(Matrix.Translation((0, 0, depth / 2)))
    else:
        # keep only the front face set
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        bm.to_mesh(me)
        bm.free()
    obj = _link(name, me, loc, rot)
    M.assign(obj, mat)
    return obj


def tube(name: str, pts, radius: float, mat: str = "M_Rubber", bevel_res: int = 1, res_u: int = 4,
         smooth_path: bool = True, caps: bool = True) -> bpy.types.Object:
    """Round tube swept along points (Bezier with auto handles unless smooth_path=False)."""
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_mode = "ROUND"
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = caps
    cu.resolution_u = res_u
    cu.twist_mode = "MINIMUM"
    if smooth_path:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
    else:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    obj = _link(name, me)
    M.assign(obj, mat)
    return obj


def screw(name: str, r: float, loc, normal=(0, -1, 0), mat: str = "M_Brass_Aged", slot_angle: float = 0.3,
          segs: int = 8, slot_mat: str = "M_Steel_Dark") -> bpy.types.Object:
    """Slotted dome-head screw sitting on a surface with outward `normal` (head height 0.45 r)."""
    h = r * 0.45
    head = lathe2(name, [(r, 0.0), (r, h * 0.35), (r * 0.72, h * 0.9), (0.0, h)], segments=segs, mat=mat,
                  cap_bottom=False)
    slot = M.box(name + "_slot", (r * 1.7, r * 0.22, h * 0.5), loc=(0, 0, h * 0.85), mat=slot_mat, bevel=0)
    slot.rotation_euler = (0, 0, 0)
    obj = M.join([head, slot], name)
    obj.data.transform(Matrix.Rotation(slot_angle, 4, "Z"))
    _orient_to(obj, normal)
    obj.location = loc
    return obj


def rivet(name: str, r: float, loc, normal=(0, -1, 0), mat: str = "M_Brass_Aged", segs: int = 8) -> bpy.types.Object:
    h = r * 0.55
    obj = lathe2(name, [(r, 0.0), (r * 0.92, h * 0.45), (r * 0.6, h * 0.88), (0.0, h)], segments=segs,
                 mat=mat, cap_bottom=False)
    _orient_to(obj, normal)
    obj.location = loc
    return obj


def _orient_to(obj, normal) -> None:
    """Rotate mesh data so its local +Z points along `normal`."""
    n = Vector(normal).normalized()
    q = Vector((0, 0, 1)).rotation_difference(n)
    obj.data.transform(q.to_matrix().to_4x4())


def orient_mesh(obj, rot=(0, 0, 0), loc=(0, 0, 0)) -> None:
    """Bake a rotation (Euler XYZ) + translation into the mesh data."""
    from mathutils import Euler
    mat = Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    obj.data.transform(mat)


def bevel_sharp(obj, width: float, segments: int = 1, angle_deg: float = 40.0) -> None:
    """Bevel edges whose faces meet sharper than angle_deg (for bmesh-built solids)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle_deg)]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type="OFFSET", segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()


def drop_faces(obj, predicate) -> None:
    """Delete faces whose (world-independent) centre/normal satisfy predicate(center, normal)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if predicate(f.calc_center_median(), f.normal)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def ring_band(name: str, r_in: float, r_out: float, width: float, segments: int = 32,
              mat: str = "M_Brass_Aged", chamfer: float = 0.0008, loc=(0, 0, 0), rot=(0, 0, 0),
              mat_fn=None) -> bpy.types.Object:
    """Hollow ring (tube section) along local Z from -width/2..width/2 with chamfered edges."""
    c = min(chamfer, width * 0.3, (r_out - r_in) * 0.3)
    w = width / 2
    prof = [(r_in, -w + c), (r_in + c, -w), (r_out - c, -w), (r_out, -w + c),
            (r_out, w - c), (r_out - c, w), (r_in + c, w), (r_in, w - c), (r_in, -w + c)]
    return lathe2(name, prof, segments=segments, mat=mat, loc=loc, rot=rot, cap_bottom=False,
                  cap_top=False, mat_fn=mat_fn)


def knurled_knob(name: str, r: float, h: float, ridges: int = 24, mat: str = "M_Brass_Aged",
                 skirt: float = 0.0, cap_mat: str | None = None, dome: float = 0.0,
                 shaft_r: float = 0.0, shaft_len: float = 0.0, index_mark: bool = True,
                 simple: bool = False) -> bpy.types.Object:
    """Instrument knob along +Z from z=0 (base) to z≈h: optional skirt, knurled grip, chamfered cap.

    Index line (pointer) at local +Y if index_mark. Origin at base centre.
    """
    k = r * 0.06
    prof = []
    z = 0.0
    if shaft_r > 0 and shaft_len > 0:
        prof += [(0.0, -shaft_len), (shaft_r, -shaft_len), (shaft_r, 0.0)]
    if skirt > 0:
        rs = r + skirt
        prof += [(rs * 0.97, 0.0), (rs, h * 0.04), (rs, h * 0.16), (rs * 0.96, h * 0.2), (r * 0.98, h * 0.22)]
        z = h * 0.22
    else:
        prof += [(r * 0.94, 0.0), (r, h * 0.05)]
        z = h * 0.05
    zt = h * 0.86
    if simple:
        prof += [(r, z + 0.001, "k"), (r, zt, "k"), (r * 0.88, h)]
        if dome > 0:
            prof += [(r * 0.55, h + dome * 0.7), (0.0, h + dome)]
        else:
            prof += [(0.0, h)]
        bands = None
        if cap_mat:
            bands = [None] * (len(prof) - 1)
            bands[-1] = cap_mat
            if dome > 0:
                bands[-2] = cap_mat
        return lathe2(name, prof, segments=ridges * 2, mat=mat, knurl=k, phase=math.pi / 2, band_mats=bands)
    prof += [(r, z + 0.002, "k"), (r, zt, "k"), (r * 0.97, zt + h * 0.04), (r * 0.9, h * 0.97)]
    if dome > 0:
        prof += [(r * 0.75, h + dome * 0.4), (r * 0.4, h + dome * 0.85), (0.0, h + dome)]
    else:
        prof += [(r * 0.86, h), (r * 0.25, h), (0.0, h * 0.995)]
    seg = ridges * 2
    bands = None
    if cap_mat:
        n = len(prof)
        bands = [None] * (n - 1)
        for i in range(n - 1):
            if prof[i][1] >= h * 0.97 - 1e-6 and prof[i][0] < r * 0.9:
                bands[i] = cap_mat
    obj = lathe2(name, prof, segments=seg, mat=mat, knurl=k, band_mats=bands, phase=math.pi / 2)
    parts = [obj]
    if index_mark:
        mark = M.box(name + "_idx", (r * 0.08, r * 0.55, 0.0006), loc=(0, r * 0.5, (h + dome) - 0.0001 if dome <= 0 else h + dome * 0.5),
                     mat="M_Enamel_Cream", bevel=0)
        parts.append(mark)
    return M.join(parts, name) if len(parts) > 1 else obj


def tris(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons) if obj.type == "MESH" else 0


def report(label: str) -> int:
    total = 0
    rows = []
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            t = tris(o)
            total += t
            rows.append((t, o.name))
    rows.sort(reverse=True)
    print(f"[lib_mech] {label}: {total} tris")
    for t, n in rows[:40]:
        print(f"    {t:6d}  {n}")
    return total


def set_origin_keep(obj, world_point) -> None:
    M.set_origin(obj, world_point)


def parent_keep(child, parent) -> None:
    M.set_parent(child, parent)


def finish(name: str, decals=None, smooth_angle: float = 35.0) -> str:
    """finalize (box UVs on non-decal faces + smoothing), run decal UV callbacks, export GLB."""
    M.finalize(smooth_angle=smooth_angle)
    for fn in decals or []:
        fn()
    report(name)
    return export_lean(name)


def export_lean(name: str) -> str:
    """Like mrlib.export_glb but never embeds images: Godot swaps materials by slot name, and the
    QA preview textures (PBR folders, decals) would otherwise bloat the GLB to megabytes."""
    out_dir = M.MODELS_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=False, export_apply=True, export_yup=True,
        export_materials="EXPORT", export_image_format="NONE", export_cameras=False, export_lights=False,
        export_extras=True)
    print(f"[lib_mech] exported {path} ({M.tri_count()} tris, {os.path.getsize(path) // 1024} KB)")
    return path


def want_render() -> bool:
    return "--no-render" not in M.main_guard()


def studio_floor(z: float = 0.0, size: float = 6.0, color: str = "2A2622") -> bpy.types.Object:
    """A QA-only backdrop (call after export!)."""
    mat = bpy.data.materials.get("QA_Floor") or M.material("QA_Floor", color=color, rough=0.8)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = bpy.data.meshes.new("QA_floor")
    bm.to_mesh(me)
    bm.free()
    obj = _link("QA_floor", me, loc=(0, 0, z))
    obj.data.materials.append(mat)
    return obj


# ---------------------------------------------------------------- orientation of 2D-built solids
_PERM_YZ = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # (x_c,y_c,z_c) -> (z_c, x_c, y_c)
_FRONT = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))    # (x_c,y_c,z_c) -> (x_c, -z_c, y_c)
_SIDE_X = Matrix(((0, 0, 1, 0), (0, -1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1)))


def profile_yz(obj, x0: float = 0.0) -> None:
    """A curve/extrude built in XY (x = world Y, y = world Z) and extruded along +Z becomes a solid
    extruded along world +X starting at x0."""
    obj.data.transform(Matrix.Translation((x0, 0, 0)) @ _PERM_YZ)


def to_front(obj, y_back: float = 0.0, x: float = 0.0, z: float = 0.0) -> None:
    """A shape drawn in XY (x right, y up) and extruded along +Z becomes a front plate whose back is at
    world Y = y_back and which protrudes toward -Y (the viewer). Its 2D origin lands at (x, z)."""
    obj.data.transform(Matrix.Translation((x, y_back, z)) @ _FRONT)


def front_rot():
    """Euler for text_flat()/planes drawn in XY so they face the viewer (-Y)."""
    return (math.pi / 2, 0.0, 0.0)


def plane(name: str, w: float, h: float, loc=(0, 0, 0), mat: str = "M_Glass", facing: str = "-Y") -> bpy.types.Object:
    """Single quad of w (X) by h, facing -Y (default), +Z or +X."""
    bm = bmesh.new()
    if facing == "-Y":
        co = [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]
    elif facing == "+Z":
        co = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    else:  # +X
        co = [(0, -w / 2, -h / 2), (0, w / 2, -h / 2), (0, w / 2, h / 2), (0, -w / 2, h / 2)][::-1]
        co = [(0, w / 2, -h / 2), (0, -w / 2, -h / 2), (0, -w / 2, h / 2), (0, w / 2, h / 2)][::-1]
    vs = [bm.verts.new(c) for c in co]
    bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = _link(name, me, loc)
    if facing == "-Y" and obj.data.polygons[0].normal.y > 0:
        obj.data.flip_normals()
    M.assign(obj, mat)
    return obj


def qa_render(name: str, cam_loc, target, lens: float = 50.0, floor_z: float | None = 0.0,
              samples: int = 40, res=(960, 640), lights=None, world: float = 0.25) -> str:
    """Render a QA preview with an optional dark floor (re-created per shot)."""
    if floor_z is not None:
        studio_floor(floor_z)
    return M.render_preview(name, cam_loc, target, lens=lens, res=res, samples=samples,
                            world_strength=world, lights=lights)


# ---------------------------------------------------------------- clockwork parts
def make_gear(name: str, n: int, r_root: float, r_tip: float, thick: float, phase: float = 0.0,
              holes: int = 5, hole_r=None, mat: str = "M_Brass_Aged", bevel: float = 0.0005,
              bore: float = 0.0, drop_bottom: bool = True, spoke_w: float = 0.0045) -> bpy.types.Object:
    """Spur gear lying on z = 0..thick, tooth 0 at angle `phase`, with `holes` curved crossings."""
    loops = [gear_outline(n, r_root, r_tip, phase, flank=False)]
    if holes:
        r_in, r_out = hole_r or (r_root * 0.36, r_root * 0.78)
        span = TAU / holes
        rc, rm = (r_out - r_in) / 2, (r_out + r_in) / 2
        cap = math.asin(min(0.99, rc / rm))          # angular reach of the rounded slot ends
        spoke = spoke_w / rm
        for k in range(holes):
            a0 = phase + span * k + spoke / 2 + cap
            a1 = phase + span * (k + 1) - spoke / 2 - cap
            if a1 - a0 > math.radians(4):
                loops.append(kidney(r_in, r_out, a0, a1, n_arc=4))
    if bore > 0:
        loops.append(circle(bore, 10))
    return curve_solid(name, loops, thick, bevel=bevel, bevel_res=0, mat=mat, drop_bottom=drop_bottom)


def pointer_outline(length: float, tail: float, shaft_w: float = 0.0024, head_w: float = 0.008,
                    head_len: float = 0.009, ball_r: float = 0.0042):
    """Clock-hand outline pointing to +Y (tip at y=length), round counterweight centred at y=-tail."""
    hw = shaft_w / 2
    th = math.asin(min(0.99, hw / ball_r))
    pts = [(0.0, length), (-head_w / 2, length - head_len), (-hw, length - head_len + 0.001)]
    pts.append((-hw, -tail + ball_r * math.cos(th)))
    a0 = math.pi / 2 + th
    a1 = math.pi / 2 - th + TAU
    for i in range(1, 7):
        t = a0 + (a1 - a0) * i / 7
        pts.append((ball_r * math.cos(t), -tail + ball_r * math.sin(t)))
    pts.append((hw, -tail + ball_r * math.cos(th)))
    pts += [(hw, length - head_len + 0.001), (head_w / 2, length - head_len)]
    return pts


def flat_shape(name: str, loops, mat: str = "M_Bakelite", loc=(0, 0, 0), rot=(0, 0, 0)) -> bpy.types.Object:
    """Zero-thickness filled 2D shape (even-odd holes) in local XY facing +Z — inlays, engravings."""
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "FRONT"
    for loop in loops:
        sp = cu.splines.new("POLY")
        sp.points.add(len(loop) - 1)
        for i, (x, y) in enumerate(loop):
            sp.points[i].co = (x, y, 0.0, 1.0)
        sp.use_cyclic_u = True
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    me.name = name
    obj = _link(name, me, loc, rot)
    M.assign(obj, mat)
    return obj


def outline_ring(w: float, h: float, r: float, line: float, n: int = 4):
    """Two loops forming a thin engraved rounded-rectangle line of width `line`."""
    return [rounded_rect(w, h, r, n), rounded_rect(w - 2 * line, h - 2 * line, max(r - line, 0.0005), n)]


def circle_line(r: float, line: float, n: int = 32, cx: float = 0.0, cy: float = 0.0):
    return [circle(r + line / 2, n, cx=cx, cy=cy), circle(r - line / 2, n, cx=cx, cy=cy)]


if os.environ.get("MR_PARTS"):
    _orig_join = M.join

    def _join_dbg(objs, name=None):
        for o in objs:
            if o is not None and o.type == "MESH":
                print(f"PART {name} {o.name} {tris(o)}")
        return _orig_join(objs, name)

    M.join = _join_dbg
