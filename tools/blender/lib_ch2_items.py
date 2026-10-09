"""MYSTERY ROOM — Chapter 2 inventory-item helpers (build group D2, `items2`).

Builds on mrlib, lib_mech and lib_devices (never edits them). Same pipeline as the Chapter 1 items
(lib_devices.item_main): reset, build, finalize (box UVs + smoothing), optional post step (decal UVs,
resmoothing), move the centre of mass to the origin, export game/assets/models/<name>.glb, QA renders.
Differences: QA renders go to qa/blender/ch2/, Cycles uses 2 fixed threads (shared machine), the
Chapter 2 material slots are created with their contract preview colours, decal slots load their
images from game/assets/textures/decals/ch2/ when they exist, and every build checks its required
part names (own objects, identity rotation at rest), prints its size / bottom in Godot axes and runs
a back-face check.

Conventions: metres, Blender Z-up; Godot = Blender (x, z, -y). Flat items are built lying in the
Blender XY plane with the hero face up (+Z) and their top edge toward Blender +Y (= Godot -Z), so the
70 deg inspect tilt (ItemDB.view_tilt) shows them upright. Standing items face Blender -Y (= Godot +Z).

Main helpers
  ensure_materials()          every slot the items use (library + Chapter 2 + decals)
  text_loops(body, size)      2D outline loops of a text (for stamped / pierced digits in curve_solid)
  union_circle(poly, ...)     2D union of an outline and an overlapping circle (key eyes)
  key_shank(...)              turned key shank along Blender -Y with beads and a domed tip
  backface_check()            renders 14 views with back faces in red (Godot culls back faces)
  inspect_cam(dist)           QA camera matching ItemDB's 70 deg inspect tilt for flat items
  item_main(...)              the build / export / check / QA pipeline (C.LIGHTS = C.SOFT for paper)
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

ROOT = M.ROOT
DECALS_CH2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
QA_SUB = "ch2"
TAU = 2.0 * math.pi

# Chapter 2 slots (docs/models/ch2.md section 0) plus library slots mrlib.PREVIEW does not know.
# name: (hex, roughness, metallic, alpha)
CH2_SLOTS = {
    "M_Velvet": ("5A1420", 0.9, 0.0, 1.0),
    "M_Film": ("3A2414", 0.25, 0.0, 0.9),
    "M_Tape": ("4A2C1A", 0.35, 0.0, 1.0),
    "M_Cardboard": ("9A7B55", 0.85, 0.0, 1.0),
    "M_Linen": ("8C7B5E", 0.8, 0.0, 1.0),
    "M_Steel_Cream": ("D8CFB4", 0.4, 0.1, 1.0),
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),     # game/assets/materials/M_Lacquer_Black.tres
    "M_Felt": ("3A3A3A", 1.0, 0.0, 1.0),               # game/assets/materials/M_Felt.tres
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 0.85),       # game/assets/materials/M_Glass_Dark.tres
}

# decal slot -> image file in DECALS_CH2 (group F); (fallback preview colour, alpha-wired in QA like the
# .tres: IndexCard / TapeLabel use alpha scissor, SlideMark alpha blend, the others are opaque)
DECALS = {
    "M_Decal_Badge": ("badge.png", "E6DCC4", False),
    "M_Decal_IndexCard": ("index_card.png", "E9DFC6", True),
    "M_Decal_RequestCard": ("request_card.png", "D9C495", False),
    "M_Decal_FileCover": ("file_cover.png", "CDB27A", False),
    "M_Decal_TapeLabel_1996": ("tape_label_1996.png", "E8DFC8", True),
    "M_Decal_TapeLabel_1997": ("tape_label_1997.png", "E8DFC8", True),
    "M_Decal_TapeLabel_1998": ("tape_label_1998.png", "E8DFC8", True),
    "M_Decal_SlideMark": ("slide_mark.png", "D8E0DC", True),
}

# Card geometry shared with the decal builder (tools/textures/make_decals_ch2.py: 10 px per mm).
CARD_W, CARD_H = 0.125, 0.075
HOLE_FROM_TOP = 0.0092        # punch-circle / hole centre below the top edge
HOLE_D = 0.0050               # punched hole diameter
NOTCH_W = 0.0084              # V-notch width at the top edge
NOTCH_D = 0.0100              # V-notch depth (the tip passes the printed circle centre)
PUNCH_CODE = (1, 0, 1, 1, 0, 0, 1, 0)


def card_pos_x(k: int, w: float = CARD_W) -> float:
    """Centre of edge position k (1..8, left -> right): u = (k - 0.5) / 8 of the card width."""
    return -w / 2 + (k - 0.5) * w / 8


def ensure_materials() -> None:
    D.ensure_materials()
    for name, (hx, rough, metal, alpha) in CH2_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)
    for slot, (fname, hx, use_alpha) in DECALS.items():
        if bpy.data.materials.get(slot) is not None:
            continue
        path = os.path.join(DECALS_CH2, fname)
        if os.path.exists(path):
            mat = M.material(slot, color="FFFFFF", rough=0.6, metal=0.0, image=path)
            nt = mat.node_tree
            tex = [n for n in nt.nodes if n.type == "TEX_IMAGE"][0]
            bsdf = nt.nodes["Principled BSDF"]
            if use_alpha and tex.image is not None and tex.image.channels == 4:
                nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
                if hasattr(mat, "surface_render_method"):
                    mat.surface_render_method = "BLENDED"
        else:
            M.material(slot, color=hx, rough=0.6, metal=0.0, image="")


# ---------------------------------------------------------------- geometry helpers
def drop_cap(obj, z: float, up: bool = True, tol: float = 2e-6) -> None:
    """Delete the flat cap faces of obj lying in the plane z (normal +Z if up, else -Z)."""
    def pred(c, n):
        return abs(c.z - z) < tol and ((n.z > 0.99) if up else (n.z < -0.99))
    L.drop_faces(obj, pred)


def uv_rect_all(obj, x0: float, x1: float, y0: float, y1: float, axis: str = "Z") -> None:
    """0..1 planar UVs for every face of obj over the rectangle [x0, x1] x [y0, y1] (mesh-local).
    axis Z: u from X, v from Y (flat items, top toward +Y). axis Y (faces toward -Y): u from X, v from Z."""
    L.planar_uv_rect(obj, x0, x1, y0, y1, axis=axis, material_prefix="")


def parent_all(children, parent) -> None:
    for c in children:
        M.set_parent(c, parent)


def text_loops(body: str, size: float, font: str = L.FONT_SANS_B, res: int = 3, centre: bool = True):
    """Outline loops (outer contours and counters) of a text set in the XY plane, for curve_solid or
    flat_shape (even-odd fill). centre: centred on the real glyph bounds."""
    cu = bpy.data.curves.new("tl_txt", "FONT")
    cu.body = body
    cu.size = size
    cu.resolution_u = res
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    if os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    tmp = bpy.data.objects.new("tl_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    boundary = [e for e in bm.edges if len(e.link_faces) == 1]
    adj: dict = {}
    for e in boundary:
        for v in e.verts:
            adj.setdefault(v.index, []).append(e)
    used = set()
    loops = []
    for e in boundary:
        if e.index in used:
            continue
        used.add(e.index)
        v0, v1 = e.verts
        loop = [(v0.co.x, v0.co.y)]
        cur = v1
        while cur != v0:
            loop.append((cur.co.x, cur.co.y))
            nxt = [f for f in adj[cur.index] if f.index not in used]
            if not nxt:
                break
            used.add(nxt[0].index)
            cur = nxt[0].other_vert(cur)
        if len(loop) >= 3:
            loops.append(loop)
    bm.free()
    bpy.data.meshes.remove(me)
    if centre and loops:
        xs = [p[0] for lp in loops for p in lp]
        ys = [p[1] for lp in loops for p in lp]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        loops = [[(x - cx, y - cy) for (x, y) in lp] for lp in loops]
    return loops


def move_loops(loops, dx: float = 0.0, dy: float = 0.0, rot: float = 0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [[(x * c - y * s + dx, x * s + y * c + dy) for (x, y) in lp] for lp in loops]


def union_circle(poly, cx: float, cy: float, r: float, n: int = 24):
    """Outline of a CCW polygon united with a circle that overlaps one stretch of its boundary (e.g. a
    hanging eye on a key bow): the polygon's points inside the circle are replaced by the circle's arc
    outside the polygon. Avoids coplanar overlapping solids (z-fighting in Godot)."""
    inside = [math.hypot(x - cx, y - cy) < r for (x, y) in poly]
    if not any(inside) or all(inside):
        return list(poly)
    m = len(poly)
    start = next(i for i in range(m) if inside[i] and not inside[i - 1])     # first point inside
    out = [poly[(start + k) % m] for k in range(m) if not inside[(start + k) % m]]
    # out[-1] is the last outside point before the run (going CCW), out[0] the first one after it
    ax, ay = out[-1]
    bx, by = out[0]
    a0 = math.atan2(ay - cy, ax - cx)
    a1 = math.atan2(by - cy, bx - cx)
    while a1 <= a0:
        a1 += TAU
    arc = [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
           for i in range(1, n)]
    return out + arc


def key_shank(name: str, profile, y_top: float, mat: str, segments: int = 14) -> bpy.types.Object:
    """Turned key shank lying along Blender -Y (bow at +Y). profile [(r, d)] with d = distance down
    from y_top (d increasing toward the tip); the axis lies in z = 0."""
    prof = [(r, d) for (r, d) in profile]
    return D.revolve(name, prof, direction=(0, -1, 0), loc=(0, y_top, 0), segments=segments, mat=mat,
                     up_hint=(0, 0, 1), cap_bottom=prof[0][0] > 0, cap_top=prof[-1][0] > 0)


# ---------------------------------------------------------------- checks
def require(names) -> bool:
    """Every required part exists, is its own object, and is at an identity rotation / unit scale."""
    ok = True
    M.refresh()
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            print(f"[items2] MISSING part {nm}")
            ok = False
            continue
        q = o.matrix_local.to_quaternion()
        s = o.matrix_local.to_scale()
        ident = abs(abs(q.w) - 1.0) < 1e-6 and all(abs(c - 1.0) < 1e-6 for c in s)
        loc = o.matrix_world.translation
        g = (loc.x, loc.z, -loc.y)
        print(f"[items2] part {nm:14s} parent={o.parent.name if o.parent else '-':16s} "
              f"pivot(godot)=({g[0]:+.4f}, {g[1]:+.4f}, {g[2]:+.4f}) identity={'yes' if ident else 'NO'}")
        ok = ok and ident
    print(f"[items2] required parts: {'OK' if ok else 'FAILED'}")
    return ok


def backface_check(res: int = 200, samples: int = 4) -> float:
    """Godot culls back faces. Render the item from the 6 axis directions (plus 8 diagonals) with a
    view-layer material override that shows back faces in pure red, and report the red fraction of the
    item's pixels per view. Anything above ~0.5 % deserves a look (open shells built inside out)."""
    scene = bpy.context.scene
    mat = bpy.data.materials.new("QA_backface")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMixShader")
    front = nt.nodes.new("ShaderNodeEmission")
    front.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)
    back = nt.nodes.new("ShaderNodeEmission")
    back.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1.0)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
    nt.links.new(front.outputs["Emission"], mix.inputs[1])
    nt.links.new(back.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    vl = bpy.context.view_layer
    vl.material_override = mat
    old_world = scene.world
    world = bpy.data.worlds.new("QA_bf_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    setup_threads()
    lo, hi = D.bounds()
    centre = (lo + hi) / 2
    span = max((hi - lo).length, 0.02)
    cam_data = bpy.data.cameras.new("QA_bf_cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = span * 1.1
    cam = bpy.data.objects.new("QA_bf_cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    dirs += [(sx, sy, sz) for sx in (1, -1) for sy in (1, -1) for sz in (1, -1)]
    path = os.path.join(bpy.app.tempdir or "/tmp", "qa_backface.png")
    worst = 0.0
    for d in dirs:
        v = Vector(d).normalized()
        cam.location = centre + v * span * 2.0
        cam.rotation_euler = (-v).to_track_quat("-Z", "Y" if abs(v.z) < 0.99 else "X").to_euler()
        cam_data.clip_end = span * 5
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path, check_existing=False)
        px = list(img.pixels)
        bpy.data.images.remove(img)
        red = obj = 0
        for i in range(0, len(px), 4):
            r, g = px[i], px[i + 1]
            if r > 0.05 or g > 0.05:
                obj += 1
                if r > 0.6 and g < 0.25:
                    red += 1
        frac = red / max(obj, 1)
        worst = max(worst, frac)
        if frac > 0.005:
            print(f"[items2] backfaces visible from {d}: {100 * frac:.1f} % of the item's pixels")
    vl.material_override = None
    scene.world = old_world
    bpy.data.objects.remove(cam, do_unlink=True)
    print(f"[items2] backface check: worst view {100 * worst:.2f} % red ({'OK' if worst <= 0.005 else 'CHECK'})")
    return worst


def godot_bounds(objs=None):
    lo, hi = D.bounds(objs)
    # Blender (x, y, z) -> Godot (x, z, -y)
    glo = Vector((lo.x, lo.z, -hi.y))
    ghi = Vector((hi.x, hi.z, -lo.y))
    return glo, ghi


def summary(name: str, budget: int = 2500) -> None:
    glo, ghi = godot_bounds()
    size = ghi - glo
    tris = M.tri_count()
    print(f"[items2] {name}: tris={tris} (budget {budget}: {'OK' if tris <= budget else 'OVER'}) "
          f"size godot(x,y,z)=({size.x:.4f}, {size.y:.4f}, {size.z:.4f}) bottom y={glo.y:+.4f} "
          f"min={tuple(round(c, 4) for c in glo)} max={tuple(round(c, 4) for c in ghi)}")


# ---------------------------------------------------------------- QA
# A softer three-point rig for printed paper (the default mrlib rig over-exposes cream decals).
SOFT = [((1.0, -1.2, 1.4), 420, "FFE2C0", 1.8), ((-1.4, -0.6, 0.8), 150, "BFD4FF", 2.0),
        ((0.2, 1.4, 1.6), 300, "FFFFFF", 1.2)]
LIGHTS = None            # set to SOFT in an item script to use it for all of its shots


def setup_threads() -> None:
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2


def shot(name: str, cam, target, lens: float = 50.0, floor_z: float | None = 0.0, samples: int = 28,
         res=(800, 600), lights=None, world: float = 0.25) -> str:
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    setup_threads()
    return D.shot(f"{QA_SUB}/{name}", cam, target, lens=lens, floor_z=floor_z, samples=samples, res=res,
                  lights=lights, world=world)


def inspect_cam(dist: float, tilt_deg: float = 70.0):
    """Camera position (Blender) that sees a FLAT item as ItemDB's inspect view does: the item is tilted
    tilt_deg about Godot +X and seen from Godot +Z, i.e. the camera sits at Blender
    (0, -dist cos(tilt), dist sin(tilt)) relative to the item."""
    t = math.radians(tilt_deg)
    return (0.0, -dist * math.cos(t), dist * math.sin(t))


def item_main(name: str, build_fn, shots=(), post=None, required=(), budget: int = 2500) -> None:
    """shots: [(suffix, cam_loc, target, lens[, pose_fn])], Blender coordinates relative to the centred
    item; a floor is put under the item's lowest point. pose_fn() runs before its shot (QA only, after
    the export) and its pose stays for the following shots."""
    M.reset_scene()
    ensure_materials()
    build_fn()
    M.finalize()
    if post:
        post()
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    com = D.recentre(roots, D.centre_of_mass(meshes))
    print(f"[items2] {name}: centre of mass moved to origin (was {tuple(round(c, 4) for c in com)})")
    D.export(name)
    D.describe(name)
    summary(name, budget)
    require(required)
    backface_check()
    if D.want_render() and shots:
        D.qa_tweak()
        lo, _ = D.bounds()
        for s in shots:
            suffix, cam, target, lens = s[:4]
            if len(s) > 4 and s[4] is not None:
                s[4]()
            shot(f"item_{name}{suffix}", cam, target, lens=lens, floor_z=lo.z - 0.0002, lights=LIGHTS)
