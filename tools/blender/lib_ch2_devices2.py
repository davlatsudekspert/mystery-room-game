"""MYSTERY ROOM — Chapter 2 build group C2 ("devices2": booth_door, film_projector, slide_projector).

Shared helpers for the projection-booth devices. Builds on mrlib / lib_arch / lib_mech / lib_devices
(never edit those). Conventions as everywhere: Blender Z-up, model front = Blender -Y = Godot +Z,
Godot = Blender (x, z, -y).

  G(x, y, z)                Godot model/room coordinates -> Blender vector
  ensure_materials()        preview colours for every slot used here (incl. the new Chapter 2 slots)
  place(objs, pos, yaw)     parent model roots to a placement empty (Godot world pos + yaw), QA only
  qa_room(...)              room_archive.glb if it exists, else a proxy shell of the booth + hall
  qa_lights(...)            booth bulb, hall pendants, cool fill (QA lights are hidden from camera rays)
  qa_item(...)              item GLB (film_reel / glass_slide) at a mount empty, else a proxy
  qa_glass_tweak()          Cycles glass, also for the material copies imported GLBs bring (M_Glass.001)
  qa_emit(obj, colour)      QA-only emissive copy of an object's materials (lamp on)
  render(...)               Cycles QA render from a Godot camera (vertical FOV like Camera3D)
  verify_glb(...)           read the exported GLB JSON back: names, parents, pivots, identity rest, tris
  beam_clearance(...)       how far a projector beam (lens -> whole screen) stays inside the booth window
  side_plate / front_plate  orient 2D-drawn plates onto side (+-X) or front (-Y) faces
  blender_rot_about_godot   Euler for a QA pose about a Godot axis
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

ROOT = M.ROOT
QA_SUB = "ch2"
DECALS_CH2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")

# new Chapter 2 slots (docs/models/ch2.md §0) + slots that exist as .tres but are unknown to mrlib.PREVIEW
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
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),
}


def G(x, y, z) -> Vector:
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return Vector((x, -z, y))


def ensure_materials() -> None:
    D.ensure_materials()
    for name, (hx, rough, metal, alpha) in CH2_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)


# ---------------------------------------------------------------- small geometry helpers
def disc_loop(r: float, n: int, cx: float = 0.0, cy: float = 0.0, phase: float = 0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def front_plate(obj, y_back: float, x: float, z: float) -> None:
    """Shape drawn in XY, extruded +Z -> plate whose back is at y_back, protruding toward -Y."""
    L.to_front(obj, y_back=y_back, x=x, z=z)


def side_plate(obj, x_back: float, y: float, z: float, toward: float = -1.0) -> None:
    """Shape drawn in XY (x = Godot -z i.e. toward the front when looking from -X ... see below),
    extruded +Z -> plate on a side face whose back is at x_back, protruding along X*toward.
    Drawing axes: drawn x -> Blender -Y (Godot +Z, the model front) when toward = -1 (seen from -X the
    front is on the viewer's right), drawn y -> Blender +Z."""
    if toward < 0:
        # (xc, yc, zc) -> (-zc, -xc, yc): extrusion toward -X, drawn x toward -Y (front), drawn y up
        m = Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    else:
        # (xc, yc, zc) -> (zc, xc, yc): extrusion toward +X, drawn x toward +Y (back), drawn y up
        m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    obj.data.transform(Matrix.Translation((x_back, y, z)) @ m)


def text_side(name, body, size, x_face, y, z, mat="M_Bakelite", font=L.FONT_SANS_B, toward=-1.0, res=1,
              depth=0.0):
    """Text on a side face (normal along X*toward) that reads upright from that side."""
    t = L.text_flat(name, body, size, font=font, depth=depth, res=res, mat=mat)
    side_plate(t, x_face, y, z, toward)
    return t


def recentre_xy(obj, cx: float = 0.0, cy: float = 0.0) -> None:
    """Shift a flat XY-drawn object so its bounding-box centre is at (cx, cy) (before orienting)."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    dx = cx - (min(xs) + max(xs)) / 2
    dy = cy - (min(ys) + max(ys)) / 2
    obj.data.transform(Matrix.Translation((dx, dy, 0.0)))


def tris_of(objs) -> int:
    return sum(L.tris(o) for o in objs if o is not None and o.type == "MESH")


# ---------------------------------------------------------------- QA placement
def place(roots, pos_godot, yaw_deg: float, name: str = "PLACE"):
    """Parent the model roots to an empty at the Godot world placement (QA only, after export)."""
    holder = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(holder)
    holder.location = G(*pos_godot)
    holder.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    M.refresh()
    for r in roots:
        r.parent = holder
        r.matrix_parent_inverse = Matrix.Identity(4)
    M.refresh()
    return holder


def model_roots():
    return [o for o in bpy.context.scene.objects if o.parent is None and not o.name.startswith("QA")
            and o.name != "PLACE"]


def import_model(name: str, pos_godot, yaw_deg: float):
    """Import another model GLB at a Godot world placement (QA only). Returns [] if missing."""
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    return A.import_glb(path, tuple(G(*pos_godot)), yaw_deg, prefix="QA_imp_")


def qa_item(item: str, mount, proxy_fn):
    """Put the item GLB (or a QA proxy) at a mount empty with an identity transform."""
    M.refresh()
    path = os.path.join(M.MODELS_DIR, item + ".glb")
    if os.path.exists(path):
        new = A.import_glb(path, (0, 0, 0), 0.0, prefix="QA_item_")
        holder = new[0]
        holder.matrix_world = mount.matrix_world.copy()
        print(f"[ch2_devices2] QA: {item}.glb imported at {mount.name}")
        return new, True
    objs = proxy_fn()
    holder = bpy.data.objects.new("QA_proxy_" + item, None)
    bpy.context.scene.collection.objects.link(holder)
    for o in objs:
        o.parent = holder
    holder.matrix_world = mount.matrix_world.copy()
    print(f"[ch2_devices2] QA: {item}.glb missing -> proxy at {mount.name}")
    return [holder] + objs, False


def proxy_film_reel():
    """16 mm reel, Ø 0.18 x 0.02, standing on edge with its face (and axle) along Godot +Z, like
    film_reel.glb (the code spins it about its local +Z). Centred on the origin (QA only)."""
    parts = []
    for s in (-1, 1):
        fl = L.curve_solid("QA_reel_flange", [disc_loop(0.09, 40)] +
                           [disc_loop(0.022, 10, 0.052 * math.cos(a), 0.052 * math.sin(a))
                            for a in (math.radians(90 + 120 * k) for k in range(3))] + [disc_loop(0.0045, 8)],
                           0.0012, bevel=0.0003, mat="M_Chrome")
        front_plate(fl, s * 0.0094 + 0.0006, 0.0, 0.0)       # flanges at Godot z = -/+ 0.0094
        parts.append(fl)
    film = L.lathe2("QA_reel_film", [(0.016, -0.0085), (0.074, -0.0085), (0.074, 0.0085), (0.016, 0.0085)],
                    segments=40, mat="M_Film")
    film.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    hub = L.lathe2("QA_reel_hub", [(0.0045, -0.0095), (0.016, -0.0095), (0.016, 0.0095), (0.0045, 0.0095)],
                   segments=16, mat="M_Steel_Dark")
    hub.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    return parts + [film, hub]


def proxy_glass_slide():
    """Lantern slide 0.082 x 0.082 x 0.004 facing Godot +Z (Blender -Y), centred (QA only)."""
    card = L.curve_solid("QA_slide_card", [L.rounded_rect(0.082, 0.082, 0.002, 1),
                                           L.rounded_rect(0.060, 0.060, 0.004, 2)], 0.004, bevel=0.0003,
                         mat="M_Lacquer_Black")
    front_plate(card, 0.002, 0.0, 0.0)
    glass = M.box("QA_slide_glass", (0.062, 0.0036, 0.062), mat="M_Glass", bevel=0.0)
    mark = L.flat_shape("QA_slide_mark", [disc_loop(0.020, 24), disc_loop(0.0165, 24),
                                          L.rounded_rect(0.003, 0.050, 0.0005, 1)], mat="M_Bakelite")
    front_plate(mark, -0.0019, 0.0, 0.0)
    return [card, glass, mark]


# ---------------------------------------------------------------- QA room
def _qa_mat(name, colour, rough=0.85, metal=0.0, emission=None, strength=3.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = M.material(name, color=colour, rough=rough, metal=metal, emission=emission,
                         emission_strength=strength)
    return mat


def _qa_box(name, mn_g, mx_g, mat):
    """Box from Godot min/max corners (QA proxy)."""
    a, b = G(*mn_g), G(*mx_g)
    mn = Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))
    mx = Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))
    o = A.box_minmax("QA_room_" + name, mn, mx, mat=mat, bevel=0.0)
    o.data.materials.clear()
    o.data.materials.append(bpy.data.materials.get(mat) or M.material(mat))
    M.box_uv(o)
    return o


def _wall_with_holes(name, x0, x1, z0, z1, y0, y1, holes, mat_lo, mat_hi, split=1.2, mat_back=None):
    """North-type wall slab x in [x0, x1], Godot z in [z0, z1] (thickness), y in [y0, y1], with
    rectangular holes [(hx0, hx1, hy0, hy1)] (Godot x / y). Lower part mat_lo up to `split`."""
    out = []
    xs = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    ys = sorted({y0, y1, split} | {h[2] for h in holes} | {h[3] for h in holes})
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in holes):
                continue
            mat = mat_lo if cy < split else mat_hi
            out.append(_qa_box(f"{name}_{i}_{j}", (xs[i], ys[j], z0), (xs[i + 1], ys[j + 1], z1), mat))
    return out


def qa_room(screen: bool = True, booth: bool = True):
    """Archive room for composite QA renders: the real room_archive.glb when group A has built it,
    otherwise a proxy of the parts that matter here (booth enclosure with window + doorway, hall north
    wall with the screen, floor, ceiling). Returns True if the real room was used."""
    real = os.path.join(M.MODELS_DIR, "room_archive.glb")
    if os.path.exists(real):
        A.import_glb(real, (0, 0, 0), 0.0, prefix="QA_room_")
        print("[ch2_devices2] QA: room_archive.glb imported")
        used = True
    else:
        used = False
        for nm, col, rough in (("M_Linoleum", "3E5A48", 0.55), ("M_Paint_Green", "6F8C78", 0.6),
                               ("M_Wood_Panel", None, None), ("M_Plaster_Wall", None, None),
                               ("M_Ceiling", None, None)):
            if bpy.data.materials.get(nm) is None:
                M.material(nm, color=col, rough=rough)
        _qa_box("floor", (-5.2, -0.05, -3.7), (5.2, 0.0, 3.7), "M_Linoleum")
        _qa_box("ceiling", (-5.2, 3.6, -3.7), (5.2, 3.7, 3.7), "M_Ceiling")
        _wall_with_holes("wall_n", -5.0, 5.0, -3.7, -3.5, 0.0, 3.6, [], "M_Paint_Green", "M_Plaster_Wall", 1.4)
        _qa_box("wall_w", (-5.2, 0.0, -3.5), (-5.0, 3.6, 3.5), "M_Plaster_Wall")
        _qa_box("wall_e", (5.0, 0.0, -3.5), (5.2, 3.6, 3.5), "M_Plaster_Wall")
        _qa_box("wall_s", (-5.0, 0.0, 3.5), (5.0, 3.6, 3.7), "M_Plaster_Wall")
        _qa_box("dado_n", (-5.0, 1.38, -3.5), (5.0, 1.44, -3.47), "M_Wood_Walnut")
        if booth:
            holes = [(-3.4, -2.1, 1.65, 2.25), (-1.95, -1.15, 0.0, 2.1)]
            _wall_with_holes("booth_n", -5.0, -1.0, 2.0, 2.1, 0.0, 2.8, holes, "M_Wood_Panel", "M_Paint_Green")
            _qa_box("booth_e_lo", (-1.1, 0.0, 2.1), (-1.0, 1.2, 3.5), "M_Wood_Panel")
            _qa_box("booth_e_hi", (-1.1, 1.2, 2.1), (-1.0, 2.8, 3.5), "M_Paint_Green")
            _qa_box("booth_ceiling", (-5.0, 2.8, 2.0), (-1.0, 2.9, 3.5), "M_Plaster_Wall")
            _qa_box("booth_parapet", (-5.0, 2.9, 2.0), (-1.0, 3.05, 2.06), "M_Wood_Walnut")
            # window: brass frame + glass in the opening
            fr = []
            for (a, b) in (((-3.4, 1.65), (-2.1, 1.69)), ((-3.4, 2.21), (-2.1, 2.25)),
                           ((-3.4, 1.65), (-3.36, 2.25)), ((-2.14, 1.65), (-2.1, 2.25))):
                fr.append(_qa_box("win_frame", (a[0], a[1], 1.995), (b[0], b[1], 2.105), "M_Brass_Aged"))
            _qa_box("win_glass", (-3.36, 1.69, 2.048), (-2.14, 2.21, 2.052), "M_Glass")
            # shelf on the south wall, bench, bulb
            _qa_box("shelf", (-4.6, 1.42, 3.24), (-3.3, 1.45, 3.5), "M_Wood_Walnut")
            M.sphere("QA_room_booth_bulb", 0.03, loc=tuple(G(-3.0, 2.65, 2.85)), segments=12, rings=6,
                            mat="M_Emissive_Warm")
            M.cylinder("QA_room_bulb_cord", 0.004, 0.12, loc=tuple(G(-3.0, 2.74, 2.85)), verts=6,
                              mat="M_Rubber", bevel=0.0)
        if screen:
            frame = _qa_box("screen_frame", (-3.82, 0.98, -3.5), (-1.18, 2.82, -3.45), "M_Wood_Walnut")
            border = _qa_box("screen_border", (-3.76, 1.04, -3.45), (-1.24, 2.76, -3.44), "M_Lacquer_Black")
            _qa_mat("M_Screen", "E9E6DF", 0.95)
            _qa_box("screen", (-3.7, 1.1, -3.44), (-1.3, 2.7, -3.43), "M_Screen")
    return used


def qa_lights(booth_bulb: float = 60.0, hall: float = 120.0, fill: float = 40.0):
    """Archive lighting: the booth's bare bulb, the hall pendants and a cool fill."""
    A.qa_light("booth_bulb", "POINT", tuple(G(-3.0, 2.62, 2.85)), booth_bulb, "FFB46B", size=0.04)
    for k, p in enumerate(((-2.8, 2.85, 1.4), (0.0, 2.85, 1.6), (-3.0, 2.85, -2.0), (0.0, 2.85, -2.4))):
        A.qa_light(f"pendant{k}", "POINT", tuple(G(*p)), hall, "FFC58A", size=0.12)
    A.qa_light("fill", "AREA", tuple(G(1.0, 2.6, 0.0)), fill * 4, "9FB6D8", size=3.0,
               target=tuple(G(-2.5, 1.2, 2.0)))
    hide_qa_lights()


def hide_qa_lights() -> None:
    """QA lights stand in for fixtures that are not in the scene: keep them out of camera rays (no floating
    light spheres seen through the booth window); they still light and reflect."""
    for o in bpy.context.scene.objects:
        if o.type == "LIGHT" and o.name.startswith("QA"):
            o.visible_camera = False


# ---------------------------------------------------------------- QA render (Godot camera)
def render(name: str, cam_g, target_g, fov_v: float = 50.0, res=(960, 540), samples: int = 32,
           world: float = 0.03, exposure: float = 0.0) -> str:
    """Cycles QA render to qa/blender/ch2/<name>.png from a Godot camera (vertical FOV, as Camera3D
    keep_height). Lights: whatever QA_* lights the caller added (no studio rig)."""
    out_dir = os.path.join(M.QA_DIR, QA_SUB)
    os.makedirs(out_dir, exist_ok=True)
    hide_qa_lights()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        scene.view_settings.view_transform = "Filmic"
    scene.view_settings.exposure = exposure
    w = bpy.data.worlds.new("QA_World")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = M.hex_rgba("1A1C1F")
    bg.inputs["Strength"].default_value = world
    scene.world = w
    cd = bpy.data.cameras.new("QA_Cam")
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24.0
    cd.lens = (cd.sensor_height / 2.0) / math.tan(math.radians(fov_v) / 2.0)
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("QA_Cam", cd)
    scene.collection.objects.link(cam)
    cam.location = G(*cam_g)
    M._look_at(cam, G(*target_g))
    scene.camera = cam
    path = os.path.join(out_dir, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print(f"[ch2_devices2] rendered {path}")
    return path


def clear_qa():
    """Remove every QA_* object (room, lights, items, proxies)."""
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA")]:
        bpy.data.objects.remove(o, do_unlink=True)


def qa_glass_tweak() -> None:
    """Cycles glass for the QA renders, also for the copies an imported GLB brings ("M_Glass.001")."""
    D.qa_tweak()
    for mat in bpy.data.materials:
        base = mat.name.split(".")[0]
        if not mat.use_nodes or mat.name == base and base != "M_Glass_Amber":
            continue
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        if base in ("M_Glass", "M_Crystal"):
            b.inputs["Alpha"].default_value = 1.0
            b.inputs["Transmission Weight"].default_value = 1.0
            b.inputs["IOR"].default_value = 1.47
            b.inputs["Roughness"].default_value = 0.02
            b.inputs["Base Color"].default_value = M.hex_rgba("F0F8F4")
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "DITHERED"
        elif base == "M_Glass_Amber":
            b.inputs["Transmission Weight"].default_value = 0.8


# ---------------------------------------------------------------- GLB read-back checks
def _glb_json(path):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def verify_glb(name: str, expect: dict, budget: int) -> bool:
    """expect: {node_name: dict(parent=str|None, pos=(x, y, z) Godot rel. to parent or None,
    identity=True)}. Prints a table, returns True when everything matches (pos tolerance 1 mm)."""
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    doc = _glb_json(path)
    nodes = doc.get("nodes", [])
    parent = {}
    for i, nd in enumerate(nodes):
        for c in nd.get("children", []):
            parent[c] = i
    by_name = {nd.get("name"): i for i, nd in enumerate(nodes)}
    tris = 0
    for mesh in doc.get("meshes", []):
        for p in mesh["primitives"]:
            acc = doc["accessors"][p["indices"]] if "indices" in p else doc["accessors"][p["attributes"]["POSITION"]]
            tris += acc["count"] // 3
    ok = True
    print(f"[verify] {name}.glb: {len(nodes)} nodes, {tris} tris (budget {budget}) "
          f"{'OK' if tris <= budget else 'OVER BUDGET'}")
    ok &= tris <= budget
    for nm, e in expect.items():
        if nm not in by_name:
            print(f"[verify]   MISSING {nm}")
            ok = False
            continue
        i = by_name[nm]
        nd = nodes[i]
        par = nodes[parent[i]].get("name") if i in parent else None
        t = nd.get("translation", [0, 0, 0])
        r = nd.get("rotation", [0, 0, 0, 1])
        s = nd.get("scale", [1, 1, 1])
        ident = all(abs(a - b) < 1e-5 for a, b in zip(r, (0, 0, 0, 1))) and all(abs(a - 1) < 1e-5 for a in s)
        msgs = []
        if e.get("parent", "?") != "?" and e.get("parent") != par:
            msgs.append(f"parent {par} != {e.get('parent')}")
        if e.get("identity", True) and not ident:
            msgs.append(f"rotation {r} scale {s} not identity")
        if e.get("pos") is not None and any(abs(a - b) > 0.001 for a, b in zip(t, e["pos"])):
            msgs.append(f"pos {tuple(round(v, 4) for v in t)} != {e['pos']}")
        state = "ok " if not msgs else "BAD"
        ok &= not msgs
        print(f"[verify]   {state} {nm:22s} parent={par or '-':18s} t=({t[0]:+.4f}, {t[1]:+.4f}, {t[2]:+.4f})"
              f" {'; '.join(msgs)}")
    return ok


# ---------------------------------------------------------------- beam clearance through the window
WINDOW = (-3.4, -2.1, 1.65, 2.25)     # booth projection window x0, x1, y0, y1 (world, Godot)
WALL_Z = (2.0, 2.1)                   # booth north wall faces (hall side, booth side)
SCREEN = (-3.7, -1.3, 1.1, 2.7, -3.43)


def beam_clearance(lens_world, aperture_r: float = 0.0, window=WINDOW, inset: float = 0.0,
                   screen=SCREEN, label: str = "beam") -> float:
    """Pyramid from the lens (a disc of radius aperture_r facing -Z world) to the screen rectangle.
    Returns the smallest distance between the beam and the window opening edges (shrunk by `inset`
    for a frame) over both wall faces; prints the details. Negative = clipping."""
    lx, ly, lz = lens_world
    sx0, sx1, sy0, sy1, sz = screen
    x0, x1, y0, y1 = window[0] + inset, window[1] - inset, window[2] + inset, window[3] - inset
    worst = 1e9
    rows = []
    for wz in WALL_Z:
        t = (lz - wz) / (lz - sz)
        bx0 = lx + (sx0 - lx) * t - aperture_r * (1 - t)
        bx1 = lx + (sx1 - lx) * t + aperture_r * (1 - t)
        by0 = ly + (sy0 - ly) * t - aperture_r * (1 - t)
        by1 = ly + (sy1 - ly) * t + aperture_r * (1 - t)
        c = (bx0 - x0, x1 - bx1, by0 - y0, y1 - by1)
        worst = min(worst, *c)
        rows.append((wz, bx0, bx1, by0, by1, c))
    print(f"[beam] {label}: lens {tuple(round(v, 3) for v in lens_world)}, aperture r {aperture_r}, "
          f"window inset {inset}")
    for (wz, bx0, bx1, by0, by1, c) in rows:
        print(f"[beam]   z={wz:.2f}: beam x [{bx0:.3f}, {bx1:.3f}] y [{by0:.3f}, {by1:.3f}] -> clearance "
              f"west {c[0]:.3f} east {c[1]:.3f} bottom {c[2]:.3f} top {c[3]:.3f}")
    print(f"[beam]   min clearance {worst:.3f} m {'OK' if worst > 0 else 'CLIPS'}")
    return worst


# ---------------------------------------------------------------- extra solids
def ring_solid(name, loop, centre, direction, segments=24, mat="M_Chrome"):
    """Revolve a CLOSED (r, z) loop into a solid ring (correct outward normals) whose axis points along
    `direction` (Blender) with the loop's z = 0 at `centre`."""
    o = A.lathe_loop(name, loop, segments=segments, mat=mat)
    o.data.transform(Matrix.Translation(Vector(centre)) @ D.axis_matrix(direction))
    return o


def qa_emit(obj, colour: str, strength: float = 6.0, base: str | None = None):
    """QA only: give an object a private copy of its material(s) with emission (lamp on)."""
    for i, slot in enumerate(obj.material_slots):
        m = slot.material
        if m is None:
            continue
        q = m.copy()
        q.name = "QA_" + m.name + "_on"
        b = q.node_tree.nodes.get("Principled BSDF")
        b.inputs["Emission Color"].default_value = M.hex_rgba(colour)
        b.inputs["Emission Strength"].default_value = strength
        if base:
            b.inputs["Base Color"].default_value = M.hex_rgba(base)
        obj.material_slots[i].material = q


def blender_rot_about_godot(axis: str, deg: float):
    """Euler (Blender) for a rotation about a Godot local axis (rest = identity)."""
    a = math.radians(deg)
    if axis == "X":
        return (a, 0.0, 0.0)
    if axis == "Y":        # Godot +Y = Blender +Z
        return (0.0, 0.0, a)
    if axis == "Z":        # Godot +Z = Blender -Y
        return (0.0, -a, 0.0)
    raise ValueError(axis)
