"""MYSTERY ROOM — Chapter 2 build group C1 ("devices1": tube_station, canister, compressor_panel,
card_punch, tape_deck).

Shared helpers for the archive-hall devices. Builds on mrlib / lib_arch / lib_mech / lib_devices (never
edits them). Conventions as everywhere: Blender Z-up, model front = Blender -Y = Godot +Z,
Godot = Blender (x, z, -y). Every *_g argument below is in GODOT coordinates (the contract's numbers).

  G(x, y, z)                    Godot point -> Blender vector
  grot(axis, deg)               Blender 4x4 rotation for a rotation about a Godot axis
  gframe(o, ex, ey)             local plane frame (u right, v up, w = out of the face) -> Blender
  smooth_tag / part / mount     build helpers (pre-smoothing, joined parts with pivots, mount empties)
  finalize(decals)              box UVs on every non-decal face (keeps the per-part smoothing)
  verify_glb(...)               read the exported GLB back: names, parents, pivots, identity rest, tris
  qa_room() / qa_desk()         room_archive.glb / archivist_desk.glb when they exist, else proxies
  qa_item(...)                  item GLB at a mount empty (identity), else a proxy of the contract size
  render(...)                   Cycles QA render from a Godot camera (vertical FOV like Camera3D)
  studio(...)                   hero render with a three-point rig on a dark floor
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
TAG = "[c1]"
DECALS_CH2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
FONT_SANS_B = L.FONT_SANS_B
FONT_COND_B = L.FONT_COND_B
FONT_SERIF_B = L.FONT_SERIF_B
FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
TAU = 2.0 * math.pi

# new Chapter 2 slots (docs/models/ch2.md section 0) + library slots mrlib.PREVIEW does not know
CH2_SLOTS = {
    "M_Linoleum": ("3E5A48", 0.55, 0.0, 1.0),
    "M_Paint_Green": ("6F8C78", 0.6, 0.0, 1.0),
    "M_Concrete": ("8C8A84", 0.85, 0.0, 1.0),
    "M_Steel_Cream": ("D8CFB4", 0.4, 0.1, 1.0),
    "M_Tape": ("4A2C1A", 0.35, 0.0, 1.0),
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),
    "M_Felt": ("3A3A3A", 1.0, 0.0, 1.0),
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 0.85),
}
DECAL_IMAGES = {
    "M_Decal_DestSymbols": "dest_symbols.png",
    "M_Decal_RequestCard": "request_card.png",
}


def decal_image(slot: str) -> str | None:
    fn = DECAL_IMAGES.get(slot)
    if not fn:
        return None
    p = os.path.join(DECALS_CH2, fn)
    return p if os.path.exists(p) else None


def ensure_materials() -> None:
    D.ensure_materials()
    for name, (hx, rough, metal, alpha) in CH2_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)
    for slot in DECAL_IMAGES:
        if bpy.data.materials.get(slot) is None:
            img = decal_image(slot)
            M.material(slot, image=img)
            print(f"{TAG} decal {slot}: {'image ' + img if img else 'MISSING image (preview colour)'}")


# ---------------------------------------------------------------- coordinates
_C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))       # Godot vector -> Blender vector


def G(x, y, z) -> Vector:
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return Vector((x, -z, y))


def GV(v) -> Vector:
    return Vector((v[0], -v[2], v[1]))


def to_godot(v) -> tuple:
    return (v[0], v[2], -v[1])


_AX = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}


def grot(axis, deg: float) -> Matrix:
    """4x4 Blender rotation equal to a rotation of `deg` about the Godot axis ('x'/'y'/'z' or vector)."""
    a = _AX[axis] if isinstance(axis, str) else axis
    return Matrix.Rotation(math.radians(deg), 4, GV(a))


def gframe(origin_g, ex_g, ey_g) -> Matrix:
    """Matrix mapping a local plane (u = ex, v = ey, w = ex x ey, out of the face) at a Godot origin
    to Blender. Shapes drawn in local XY (facing +Z) land on that plane facing w."""
    ex = GV(ex_g).normalized()
    ey = GV(ey_g).normalized()
    ez = ex.cross(ey).normalized()
    o = GV(origin_g)
    return Matrix(((ex.x, ey.x, ez.x, o.x), (ex.y, ey.y, ez.y, o.y), (ex.z, ey.z, ez.z, o.z), (0, 0, 0, 1)))


def front_frame(x, y, z) -> Matrix:
    """Plane facing Godot +Z at Godot (x, y, z): u = +X, v = +Y."""
    return gframe((x, y, z), (1, 0, 0), (0, 1, 0))


def put(obj, matrix: Matrix):
    obj.data.transform(matrix)
    return obj


def aim_g(obj, dir_g, up_g=(0, 1, 0)) -> None:
    """Rotate mesh data built along local +Z (lathe) so +Z points along a Godot direction; the lathe's
    angle 0 (+X) ends near up_g x dir."""
    obj.data.transform(D.axis_matrix(GV(dir_g), GV(up_g)))


def revolve_g(name, profile, dir_g, at_g, segments=24, mat="M_Brass_Aged", up_g=(0, 1, 0), **kw):
    """lathe2 profile [(r, z)] revolved around a Godot axis direction, profile z = 0 at a Godot point."""
    obj = L.lathe2(name, profile, segments=segments, mat=mat, **kw)
    obj.data.transform(Matrix.Translation(GV(at_g)) @ D.axis_matrix(GV(dir_g), GV(up_g)))
    return obj


# ---------------------------------------------------------------- smoothing / parts / mounts
SMOOTH = "c1_smooth"


def sm(obj, angle: float = 35.0):
    """Tag + apply smoothing now (survives mrlib.join); use 60-80 for low-segment round parts."""
    if obj is not None and obj.type == "MESH":
        M.apply_modifiers(obj)
        M.smooth(obj, angle)
        obj[SMOOTH] = angle
    return obj


def part(name: str, objs, pivot_g=None):
    """Join objects (already smoothed with sm()) into one part; origin at a Godot pivot."""
    objs = [o for o in objs if o is not None]
    for o in objs:
        if SMOOTH not in o.keys():
            sm(o, 35.0)
    obj = M.join(objs, name) if len(objs) > 1 else D.rename(objs[0], name)
    if pivot_g is not None:
        M.set_origin(obj, GV(pivot_g))
    else:
        M.set_origin(obj, (0, 0, 0))
    return obj


def parent(child, par) -> None:
    """Parent keeping the world transform (child local = par^-1 * world, inverse matrix identity)."""
    M.refresh()
    mw = child.matrix_world.copy()
    child.parent = par
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.matrix_world = mw
    M.refresh()


def mount(name: str, pos_g, rot: Matrix | None = None, par=None, size: float = 0.03):
    """Empty at a Godot position with an optional Blender rotation (use grot()), parented keeping world."""
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = size
    mw = Matrix.Translation(GV(pos_g))
    if rot is not None:
        mw = mw @ rot
    e.matrix_world = mw
    if par is not None:
        parent(e, par)
    return e


def text_g(name, body, size, frame: Matrix, u=0.0, v=0.0, lift=0.0, font=FONT_SANS_B, mat="M_Bakelite",
           res=1, depth=0.0, rot_deg=0.0, spacing=1.0):
    """Text centred on its glyph bounds at (u, v) of a plane frame, `lift` out of the face."""
    t = L.text_flat(name, body, size, font=font, depth=depth, res=res, mat=mat, spacing=spacing)
    L.recentre_xy(t)
    if rot_deg:
        t.data.transform(Matrix.Rotation(math.radians(rot_deg), 4, "Z"))
    t.data.transform(Matrix.Translation((u, v, lift)))
    t.data.transform(frame)
    return t


def shape_g(name, loops, frame: Matrix, u=0.0, v=0.0, lift=0.0, mat="M_Bakelite"):
    """Flat filled shape (even-odd holes) drawn in local XY, placed on a plane frame."""
    o = L.flat_shape(name, loops, mat=mat)
    o.data.transform(Matrix.Translation((u, v, lift)))
    o.data.transform(frame)
    return o


def solid_g(name, loops, depth, frame: Matrix, u=0.0, v=0.0, lift=0.0, bevel=0.0006, mat="M_Brass_Aged",
            bevel_res=0, drop_bottom=False):
    """Extruded 2D shape (z 0..depth out of the face) on a plane frame."""
    o = L.curve_solid(name, loops, depth, bevel=bevel, bevel_res=bevel_res, mat=mat, drop_bottom=drop_bottom)
    o.data.transform(Matrix.Translation((u, v, lift)))
    o.data.transform(frame)
    return o


def gbox(name, mn_g, mx_g, mat="M_Steel_Cream", bevel=0.002, seg=1):
    """Bevelled box from Godot min/max corners."""
    a, b = GV(mn_g), GV(mx_g)
    mn = Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))
    mx = Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))
    return L.box_mm(name, mn, mx, mat=mat, bevel=bevel, segments=seg)


def gtube(name, pts_g, r, sides=8, mat="M_Copper", fillet=0.0, caps=True):
    """Polyline tube through Godot points (lib_arch.tube, optional filleted corners)."""
    pts = [tuple(GV(p)) for p in pts_g]
    o = A.tube(name, pts, r, sides=sides, fillet=fillet, mat=mat, caps=caps)
    sm(o, 70.0)
    return o


def screw_g(name, r, pos_g, normal_g=(0, 0, 1), mat="M_Brass_Aged", slot=0.4, segs=8):
    return L.screw(name, r, tuple(GV(pos_g)), normal=tuple(GV(normal_g)), mat=mat, slot_angle=slot, segs=segs)


def rivet_g(name, r, pos_g, normal_g=(0, 0, 1), mat="M_Brass_Aged", segs=8):
    return L.rivet(name, r, tuple(GV(pos_g)), normal=tuple(GV(normal_g)), mat=mat, segs=segs)


def arc_band(r0, r1, a0_deg, a1_deg, n=8):
    """Annular sector outline (CCW) between radii r0..r1 from angle a0 to a1 (degrees, CCW from +X)."""
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    outer = [(r1 * math.cos(a0 + (a1 - a0) * i / n), r1 * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    inner = [(r0 * math.cos(a1 + (a0 - a1) * i / n), r0 * math.sin(a1 + (a0 - a1) * i / n)) for i in range(n + 1)]
    return outer + inner


def radial_tick(r0, r1, ang_deg, w):
    """Thin quad from radius r0 to r1 along angle (degrees, CCW from +X), width w."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    hw = w / 2
    return [(r0 * ca + hw * sa, r0 * sa - hw * ca), (r1 * ca + hw * sa, r1 * sa - hw * ca),
            (r1 * ca - hw * sa, r1 * sa + hw * ca), (r0 * ca - hw * sa, r0 * sa + hw * ca)]


def strip(p0, p1, w):
    """Quad of width w along the 2D segment p0 -> p1 (CCW)."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1]))
    n = Vector((-d.y, d.x)).normalized() * (w / 2)
    return [(p0[0] - n.x, p0[1] - n.y), (p1[0] - n.x, p1[1] - n.y), (p1[0] + n.x, p1[1] + n.y),
            (p0[0] + n.x, p0[1] + n.y)]


def offset_polyline(pts, s: float):
    """Open 2D polyline offset by s to its left (mitred corners)."""
    P = [Vector(p) for p in pts]
    out = []
    n = len(P)
    for i in range(n):
        if i == 0:
            d = (P[1] - P[0]).normalized()
            nrm = Vector((-d.y, d.x))
            out.append(P[0] + nrm * s)
        elif i == n - 1:
            d = (P[-1] - P[-2]).normalized()
            nrm = Vector((-d.y, d.x))
            out.append(P[-1] + nrm * s)
        else:
            d1 = (P[i] - P[i - 1]).normalized()
            d2 = (P[i + 1] - P[i]).normalized()
            n1 = Vector((-d1.y, d1.x))
            n2 = Vector((-d2.y, d2.x))
            m = (n1 + n2).normalized()
            out.append(P[i] + m * (s / max(0.2, m.dot(n1))))
    return [(v.x, v.y) for v in out]


def polyline_band(pts, s0: float, s1: float):
    """Closed outline of the band between the left offsets s0 < s1 of an open polyline."""
    a = offset_polyline(pts, s1)
    b = offset_polyline(pts, s0)
    return a + b[::-1]


def finalize(decal_fns=()) -> None:
    """Box UVs (1 UV = 1 m) on every non-decal face, keeping the per-part smoothing; then decal UVs."""
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            continue
        M.apply_modifiers(o)
        if SMOOTH not in o.keys():
            M.smooth(o, 35.0)
        M.box_uv(o, 1.0)
    for fn in decal_fns:
        fn()


def uv_rect(obj, frame: Matrix, u0, u1, v0, v1, prefix="M_Decal_"):
    """Exact 0..1 UVs for decal faces over a rectangle of a plane frame (u right, v up)."""
    inv = frame.inverted()
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    names = [m.name if m else "" for m in me.materials]
    M.refresh()
    mw = obj.matrix_world
    n = 0
    for f in bm.faces:
        if f.material_index >= len(names) or not names[f.material_index].startswith(prefix):
            continue
        n += 1
        for lp in f.loops:
            p = inv @ (mw @ lp.vert.co)
            lp[uv].uv = ((p.x - u0) / (u1 - u0), (p.y - v0) / (v1 - v0))
    bm.to_mesh(me)
    bm.free()
    return n


def report(label: str, budget: int) -> int:
    rows = []
    total = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and not o.name.startswith("QA"):
            t = L.tris(o)
            total += t
            rows.append((t, o.name))
    rows.sort(reverse=True)
    print(f"{TAG} {label}: {total} tris (budget {budget}) {'OK' if total <= budget else 'OVER BUDGET'}")
    for t, n in rows:
        print(f"{TAG}     {t:6d}  {n}")
    return total


def export(name: str) -> str:
    return L.export_lean(name)


# ---------------------------------------------------------------- GLB read-back checks
def glb_json(path):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def verify_glb(name: str, expect: dict, budget: int) -> bool:
    """expect: {node: dict(parent=name|None|'?', pos=(x, y, z) Godot rel. to parent or None,
    identity=True, rot=(qx, qy, qz, qw) or None)}. Prints a table; True when everything matches (1 mm)."""
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    doc = glb_json(path)
    nodes = doc.get("nodes", [])
    par = {}
    for i, nd in enumerate(nodes):
        for c in nd.get("children", []):
            par[c] = i
    by_name = {nd.get("name"): i for i, nd in enumerate(nodes)}
    tris = 0
    for mesh in doc.get("meshes", []):
        for p in mesh["primitives"]:
            acc = doc["accessors"][p["indices"]] if "indices" in p else doc["accessors"][p["attributes"]["POSITION"]]
            tris += acc["count"] // 3
    ok = tris <= budget
    print(f"[verify] {name}.glb: {len(nodes)} nodes, {tris} tris (budget {budget}) {'OK' if ok else 'OVER BUDGET'}")
    bad_names = [nd.get("name", "") for nd in nodes]
    for nm, e in expect.items():
        if nm not in by_name:
            print(f"[verify]   MISSING {nm}")
            ok = False
            continue
        i = by_name[nm]
        nd = nodes[i]
        p = nodes[par[i]].get("name") if i in par else None
        t = nd.get("translation", [0, 0, 0])
        r = nd.get("rotation", [0, 0, 0, 1])
        s = nd.get("scale", [1, 1, 1])
        msgs = []
        if e.get("parent", "?") != "?" and e.get("parent") != p:
            msgs.append(f"parent {p} != {e.get('parent')}")
        want_r = e.get("rot")
        if want_r is None and e.get("identity", True):
            want_r = (0, 0, 0, 1)
        if want_r is not None:
            same = all(abs(a - b) < 2e-4 for a, b in zip(r, want_r)) or all(abs(a + b) < 2e-4 for a, b in zip(r, want_r))
            if not same:
                msgs.append(f"rotation {tuple(round(v, 4) for v in r)} != {want_r}")
        if any(abs(a - 1) > 1e-5 for a in s):
            msgs.append(f"scale {s}")
        if e.get("pos") is not None and any(abs(a - b) > 0.001 for a, b in zip(t, e["pos"])):
            msgs.append(f"pos {tuple(round(v, 4) for v in t)} != {e['pos']}")
        ok &= not msgs
        print(f"[verify]   {'ok ' if not msgs else 'BAD'} {nm:20s} parent={p or '-':18s} "
              f"t=({t[0]:+.4f}, {t[1]:+.4f}, {t[2]:+.4f}) {'; '.join(msgs)}")
    hints = ("_col", "_wheel", "-rigid", "_rigid", "_occ", "_navmesh", "_vehicle", "-noimp", "-col", "-convcol",
             "_convcol", "-occ", "-navmesh", "-vehicle", "-wheel", "-colonly", "_colonly")
    for nm in bad_names:
        base = nm.rstrip("0123456789").rstrip(".")
        if any(base.endswith(h) for h in hints):
            print(f"[verify]   BAD name with an import hint: {nm}")
            ok = False
    print(f"[verify] {name}: {'ALL OK' if ok else 'PROBLEMS'}")
    return ok


# ---------------------------------------------------------------- QA scene
def want_render() -> bool:
    return "--no-render" not in M.main_guard()


def qa_args() -> list[str]:
    return M.main_guard()


def model_roots():
    return [o for o in bpy.context.scene.objects if o.parent is None and not o.name.startswith("QA")]


def place(roots, pos_g, yaw_deg: float, name: str = "QA_place"):
    """Parent the model roots to an empty at a Godot world placement (QA only, after export)."""
    holder = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(holder)
    holder.location = GV(pos_g)
    holder.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    M.refresh()
    for r in roots:
        r.parent = holder
        r.matrix_parent_inverse = Matrix.Identity(4)
    M.refresh()
    return holder


def import_model(name: str, pos_g, yaw_deg: float = 0.0):
    """Another model's GLB at a Godot world placement (QA only). [] if missing."""
    path = os.path.join(M.MODELS_DIR, name + ".glb")
    out = A.import_glb(path, tuple(GV(pos_g)), yaw_deg, prefix="QA_imp_")
    print(f"{TAG} QA: {name}.glb {'imported' if out else 'missing'}")
    return out


def qa_item(item: str, mount_obj, proxy_fn):
    """Item GLB (or a QA proxy of the contract size) parented to a mount empty with identity."""
    M.refresh()
    path = os.path.join(M.MODELS_DIR, item + ".glb")
    if os.path.exists(path):
        new = A.import_glb(path, (0, 0, 0), 0.0, prefix="QA_item_")
        holder = new[0]
        holder.parent = mount_obj
        holder.matrix_parent_inverse = Matrix.Identity(4)
        holder.matrix_basis = Matrix.Identity(4)
        print(f"{TAG} QA: {item}.glb at {mount_obj.name}")
        return new, True
    objs = proxy_fn()
    holder = bpy.data.objects.new("QA_proxy_" + item, None)
    bpy.context.scene.collection.objects.link(holder)
    for o in objs:
        o.name = "QA_" + o.name
        o.parent = holder
    holder.parent = mount_obj
    holder.matrix_parent_inverse = Matrix.Identity(4)
    holder.matrix_basis = Matrix.Identity(4)
    print(f"{TAG} QA: {item}.glb missing -> proxy at {mount_obj.name}")
    return [holder] + objs, False


def proxy_tape_reel():
    """5-inch reel Ø 0.127 x 0.014 lying face up (Godot +Y), centred (QA only)."""
    parts = []
    for s in (-1, 1):
        fl = L.curve_solid("reel_flange", [L.circle(0.0635, 40)] +
                           [L.circle(0.017, 10, cx=0.038 * math.cos(a), cy=0.038 * math.sin(a))
                            for a in (math.radians(90 + 120 * k) for k in range(3))] + [L.circle(0.004, 8)],
                           0.0012, bevel=0.0003, mat="M_Glass_Dark")
        fl.location = (0, 0, s * 0.0064 - 0.0006)
        parts.append(fl)
    tape = L.lathe2("reel_tape", [(0.017, -0.0058), (0.052, -0.0058), (0.052, 0.0058), (0.017, 0.0058)],
                    segments=40, mat="M_Tape")
    hub = L.lathe2("reel_hub", [(0.004, -0.0068), (0.017, -0.0068), (0.017, 0.0068), (0.004, 0.0068)],
                   segments=16, mat="M_Enamel_Cream")
    return parts + [tape, hub]


def proxy_file_folder():
    """Manila folder 0.24 x 0.32 x 0.01 lying flat, top edge toward Godot -Z (QA only)."""
    b = L.box_mm("folder", (-0.12, -0.16, -0.005), (0.12, 0.16, 0.005), mat="M_Cardboard", bevel=0.001)
    return [b]


def proxy_locker_key():
    """Steel key 0.06 x 0.004 x 0.03 lying flat (QA only)."""
    k = L.box_mm("key", (-0.03, -0.006, -0.002), (0.03, 0.006, 0.002), mat="M_Chrome", bevel=0.0005)
    tag = L.lathe2("tag", [(0.0, -0.0015), (0.015, -0.0015), (0.015, 0.0015), (0.0, 0.0015)], segments=16,
                   mat="M_Brass_Aged")
    tag.location = (-0.03, 0, 0)
    return [k, tag]


def proxy_canister():
    c = L.lathe2("can", [(0.0, -0.11), (0.035, -0.11), (0.035, 0.11), (0.0, 0.11)], segments=20,
                 mat="M_Brass_Aged")
    return [c]


def _qa_box(name, mn_g, mx_g, mat, colour=None, rough=None):
    if bpy.data.materials.get(mat) is None:
        M.material(mat, color=colour, rough=rough)
    o = gbox("QA_room_" + name, mn_g, mx_g, mat=mat, bevel=0.0)
    M.box_uv(o)
    return o


def qa_room(east: bool = True, north: bool = True) -> bool:
    """room_archive.glb when group A has built it, else a proxy shell of the east half of the hall."""
    real = os.path.join(M.MODELS_DIR, "room_archive.glb")
    if os.path.exists(real):
        A.import_glb(real, (0, 0, 0), 0.0, prefix="QA_room_")
        print(f"{TAG} QA: room_archive.glb imported")
        return True
    print(f"{TAG} QA: room_archive.glb missing -> proxy shell")
    _qa_box("floor", (-1.0, -0.05, -3.7), (5.2, 0.0, 3.7), "M_Linoleum")
    _qa_box("ceiling", (-1.0, 3.6, -3.7), (5.2, 3.7, 3.7), "M_Ceiling")
    if east:
        _qa_box("east_lo", (5.0, 0.0, -3.5), (5.2, 1.2, 3.5), "M_Paint_Green")
        _qa_box("east_hi", (5.0, 1.2, -3.5), (5.2, 3.6, 3.5), "M_Plaster_Wall")
        _qa_box("east_dado", (4.975, 1.17, -3.5), (5.0, 1.23, 3.5), "M_Wood_Walnut")
        _qa_box("east_base", (4.985, 0.0, -3.5), (5.0, 0.12, 3.5), "M_Wood_Walnut")
    if north:
        _qa_box("north_lo", (-1.0, 0.0, -3.7), (5.2, 1.2, -3.5), "M_Paint_Green")
        _qa_box("north_hi", (-1.0, 1.2, -3.7), (5.2, 3.6, -3.5), "M_Plaster_Wall")
        _qa_box("north_dado", (-1.0, 1.17, -3.5), (5.0, 1.23, -3.475), "M_Wood_Walnut")
        _qa_box("north_base", (-1.0, 0.0, -3.5), (5.0, 0.12, -3.485), "M_Wood_Walnut")
    # tube runs (group A builds them): send riser p0 -> p1 and the return line from q0, as glass proxies
    for nm, (x, z) in (("tube_send", (4.80, -1.40)), ("tube_return", (4.80, -1.26))):
        t = L.lathe2("QA_room_" + nm, [(0.045, 0.0), (0.045, 0.85), (0.04, 0.85), (0.04, 0.0)], segments=20,
                     mat="M_Glass", cap_bottom=False, cap_top=False)
        t.location = GV((x, 2.35, z))
    return False


def qa_desk() -> bool:
    """archivist_desk.glb at its placement if it exists, else a walnut proxy (top y = 0.76)."""
    if import_model("archivist_desk", (3.7, 0.0, -3.1), 0.0):
        return True
    _qa_box("desk_top", (2.95, 0.73, -3.475), (4.45, 0.76, -2.725), "M_Wood_Walnut")
    _qa_box("desk_ped_l", (2.98, 0.0, -3.45), (3.42, 0.73, -2.76), "M_Wood_Walnut")
    _qa_box("desk_ped_r", (3.98, 0.0, -3.45), (4.42, 0.73, -2.76), "M_Wood_Walnut")
    _qa_box("desk_mod", (3.42, 0.60, -3.45), (3.98, 0.73, -2.78), "M_Wood_Panel")
    return False


def qa_light(name, kind, pos_g, energy, colour="FFE2C0", size=0.1, target_g=None, spot_deg=None):
    return A.qa_light(name, kind, tuple(GV(pos_g)), energy, color=colour, size=size,
                      target=tuple(GV(target_g)) if target_g is not None else None,
                      spot=math.radians(spot_deg) if spot_deg else None)


def qa_hall_lights(scale: float = 1.0) -> None:
    """East-hall lighting: the two nearest pendants, the desk lamp, a cool fill from the hall."""
    for k, p in enumerate(((3.0, 3.05, -2.0), (3.0, 3.05, 1.4), (0.0, 3.05, -2.4))):
        qa_light(f"pendant{k}", "POINT", p, 180.0 * scale, "FFC88E", size=0.15)
    qa_light("desklamp", "POINT", (3.12, 1.12, -3.18), 18.0 * scale, "FFB86B", size=0.04)
    qa_light("fill", "AREA", (1.5, 2.2, 0.0), 160.0 * scale, "AFC3DD", size=3.0, target_g=(4.6, 1.0, -1.0))


def setup_cycles(samples: int = 32, res=(960, 640), world: float = 0.03, exposure: float = 0.0):
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
    w = bpy.data.worlds.get("QA_World") or bpy.data.worlds.new("QA_World")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = M.hex_rgba("1A1C1F")
    bg.inputs["Strength"].default_value = world
    scene.world = w
    scene.cycles.max_bounces = 8
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 12
    scene.cycles.glossy_bounces = 4


def _out(name: str) -> str:
    d = os.path.join(M.QA_DIR, QA_SUB)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name + ".png")


def render(name: str, cam_g, target_g, fov_v: float = 50.0, res=(960, 480), samples: int = 32,
           world: float = 0.03, exposure: float = 0.0) -> str:
    """QA render from a Godot camera (vertical FOV like Camera3D keep_height). Lights: the QA_* lights
    the caller added."""
    setup_cycles(samples, res, world, exposure)
    cd = bpy.data.cameras.new("QA_Cam")
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24.0
    cd.lens = (cd.sensor_height / 2.0) / math.tan(math.radians(fov_v) / 2.0)
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("QA_Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = GV(cam_g)
    M._look_at(cam, GV(target_g))
    bpy.context.scene.camera = cam
    path = _out(name)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print(f"{TAG} rendered {path}")
    return path


STUDIO = [((1.0, -1.2, 1.4), 330, "FFE2C0", 1.5),
          ((-1.4, -0.6, 0.8), 110, "BFD4FF", 2.0),
          ((0.2, 1.4, 1.6), 260, "FFFFFF", 1.0)]


def studio(name: str, cam_b, target_b, lens: float = 50.0, floor_z: float | None = 0.0, samples: int = 32,
           res=(960, 640), lights=None, world: float = 0.12, exposure: float = 0.0) -> str:
    """Hero render (Blender coordinates) with a three-point rig scaled to the camera distance."""
    setup_cycles(samples, res, world, exposure)
    tmp = []
    if floor_z is not None:
        fl = L.studio_floor(floor_z)
        tmp.append(fl)
    cd = bpy.data.cameras.new("QA_Cam")
    cd.lens = lens
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("QA_Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = cam_b
    M._look_at(cam, target_b)
    bpy.context.scene.camera = cam
    tmp.append(cam)
    t = Vector(target_b)
    span = (Vector(cam_b) - t).length
    for i, (off, energy, colour, size) in enumerate(lights or STUDIO):
        ld = bpy.data.lights.new(f"QA_St{i}", "AREA")
        ld.energy = energy * (span ** 2) / 4.0
        ld.color = M.hex_rgba(colour)[:3]
        ld.size = size * span / 2.0
        lo = bpy.data.objects.new(f"QA_St{i}", ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = t + Vector(off) * span * 0.8
        M._look_at(lo, target_b)
        tmp.append(lo)
    path = _out(name)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    print(f"{TAG} rendered {path}")
    return path


def clear_qa(prefix: str = "QA") -> None:
    for o in [o for o in bpy.context.scene.objects if o.name.startswith(prefix)]:
        bpy.data.objects.remove(o, do_unlink=True)


def qa_tweak() -> None:
    """QA-only Cycles looks (real glass transmission, emissive strength). Never affects the GLB."""
    D.qa_tweak()
    for n in ("M_Glass_Dark",):
        mat = bpy.data.materials.get(n)
        if mat is not None and mat.use_nodes:
            b = mat.node_tree.nodes.get("Principled BSDF")
            b.inputs["Alpha"].default_value = 1.0
            b.inputs["Transmission Weight"].default_value = 0.85
            b.inputs["Roughness"].default_value = 0.05


def pose_rot(obj, axis: str, deg: float) -> None:
    """QA pose: rotate a part about its own local Godot axis (rest = identity, so basis = rotation)."""
    obj.matrix_basis = obj.matrix_basis @ grot(axis, deg)
    M.refresh()


def pose_slide(obj, vec_g) -> None:
    obj.matrix_basis = Matrix.Translation(obj.matrix_basis.to_3x3() @ GV(vec_g)) @ obj.matrix_basis
    M.refresh()


def qa_emit(obj, colour: str, strength: float = 6.0, base: str | None = None) -> None:
    """QA only: lamp on (private material copy with emission)."""
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
