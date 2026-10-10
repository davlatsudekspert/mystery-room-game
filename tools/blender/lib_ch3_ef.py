"""MYSTERY ROOM — Chapter 3 groups E and F helpers (Leyla's camp, the field recorder, the oscillograph, the crystal
shutter; the Gallery console and the memorial wall). Contract: docs/models/ch3.md §7, §8; measured results:
docs/models/ch3_e.md, docs/models/ch3_f.md.

Builds on lib_ch3_d (group D: G-frame helpers, verify, Nursery QA lights) and lib_ch3_a / lib_ch3_bc (G-frame
primitives, GLB facts, QA cameras); none of the older libraries are edited.

G-FRAME: every script builds its geometry directly in GODOT axes (Blender x, y, z used as Godot x, y, z: y up,
+z = the model front), converts with K.to_blender() right before parenting, exports, re-reads the GLB.

  ensure_materials()          every slot groups E and F use
  hex_crystal(...)            a hexagonal crystal with pointed ends along an axis (tuning crystals, memorial crystals)
  piano_key(...)              a recorder piano key hinged at its back edge, with a 3D pictogram on top
  rrect_box(...)              a rounded-corner slab (cases, decks)
  QA: camp_room(), camp_lights(), gallery_room(), gallery_lights(), echo_pose(), ghost()
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
import lib_ch3_a as K  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402

TAG = "[ch3-ef]"
ROOT = M.ROOT
PREVIEW_DIR = D.PREVIEW_DIR

STEEL, BRASS, CRYSTAL, SHQ = "M_Steel_Dark", "M_Brass_Aged", "M_Crystal", "M_Shader_Quad"
FABRIC, PANEL, PAPER = "M_Fabric", "M_Wood_Panel", "M_Paper"
LEATHER, CHROME, BAKE, TAPE = "M_Leather", "M_Chrome", "M_Bakelite", "M_Tape"
CREAM_STEEL, GLASS_DARK, WALNUT, STONE = "M_Steel_Cream", "M_Glass_Dark", "M_Wood_Walnut", "M_Stone"

# world placements (§1.2)
CAMP = (4.5, 7.6, -4.0, -1.2)                     # x0, x1, z0, z1 (interior)
CAMP_H = 2.9
RECORDER_POS, RECORDER_YAW = (4.95, 0.74, -1.45), 180.0
OSC_POS, OSC_YAW = (4.97, 0.74, -1.72), 135.0
SHUTTER_POS, SHUTTER_YAW = (4.5, 0.0, -2.6), 90.0
CONSOLE_POS = (0.0, 0.0, 2.6)
CAMP_LIGHT = (6.2, 2.45, -2.6)
# §2 views used by groups E and F
VIEWS = {
    "camp": ((7.25, 1.6, -1.5), (4.9, 1.2, -2.8), 62),
    "shutter": ((6.55, 1.55, -2.6), (4.66, 1.6, -2.6), 50),
    "recorder": ((5.3, 1.32, -2.55), (5.0, 0.84, -1.55), 46),
    "nursery_w": ((12.2, 1.65, 2.9), (6.4, 1.2, -0.8), 62),
    "gallery": ((-2.7, 1.65, 2.2), (1.8, 1.0, -2.2), 62),
    "gallery_w": ((2.7, 1.65, 2.2), (-1.8, 1.0, -2.2), 62),
    "console": ((0.0, 1.55, 3.45), (0.0, 1.0, 2.55), 52),
    "scope": ((0.0, 1.42, 3.0), (0.0, 1.25, 2.53), 34),
    "strand_plate": ((-0.42, 1.3, 3.1), (-0.42, 0.97, 2.76), 34),
    "cradle": ((0.0, 1.35, 3.15), (0.0, 1.0, 2.74), 38),
    "memorial": ((0.0, 1.6, -1.2), (0.0, 1.45, -3.92), 60),
    "socket_42": ((1.35, 1.4, -2.6), (1.78, 1.15, -3.49), 40),
    "finale": ((0.0, 1.85, 3.75), (0.0, 1.15, 0.4), 66),
    "secret": ((0.6, 1.5, -1.8), (1.7, 0.9, -3.3), 52),
}


# ====================================================================== materials / finishing
def ensure_materials() -> None:
    D.ensure_materials()
    B.ensure_materials()
    for name in (STEEL, BRASS, CRYSTAL, SHQ, FABRIC, PANEL, PAPER, LEATHER, CHROME, BAKE, TAPE, CREAM_STEEL,
                 GLASS_DARK, WALNUT, STONE):
        M.material(name)


def finalize(objs=None) -> None:
    D.finalize(objs)


# ====================================================================== geometry helpers (G-frame)
def hex_crystal(name, r, length, centre, axis=(0, 1, 0), tip=None, tip_top=None, mat=CRYSTAL, phase=0.0,
                flat_top=False):
    """Hexagonal crystal of circumradius r whose body (prism + the two points) spans `length` along `axis`, from
    `centre` (the base end) toward the axis. tip = length of the far point (default 0.9 r), tip_top = the near
    point (default the same; flat_top=True makes the near end a flat hexagon instead)."""
    tip = r * 0.9 if tip is None else tip
    tip_top = tip if tip_top is None else tip_top
    body = length - tip - (0.0 if flat_top else tip_top)
    prof = [(0.0, 0.0), (r, 0.0 if flat_top else tip_top)]
    z0 = prof[-1][1]
    prof += [(r, z0 + body), (0.0, length)]
    o = K.glathe(name, prof, centre, axis, 6, mat, phase=phase, smooth=20.0)
    return o


def rrect_box(name, w, h, d, r, centre, mat, n=3, bevel=0.0, drop_bottom=False):
    """Rounded-corner slab w (x) x d (z) x h (y) centred at `centre`, corners rounded in plan by r."""
    o = K.plate(name, [L.rounded_rect(w, d, r, n)], h, z0=0.0, mat=mat, bevel=bevel, drop_bottom=drop_bottom)
    o.data.transform(Matrix.Translation((centre[0], centre[1] - h / 2, centre[2])) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    return o


def arrow_loops(kind, h):
    """Flat pictogram loops (+y up, centred): 'play' ▶, 'rewind' ◀◀, 'ffwd' ▶▶, 'stop' ■."""
    s = h / 2
    if kind == "play":
        return [[(-s * 0.8, -s), (s * 0.9, 0.0), (-s * 0.8, s)]]
    if kind == "stop":
        return [[(-s * 0.8, -s * 0.8), (s * 0.8, -s * 0.8), (s * 0.8, s * 0.8), (-s * 0.8, s * 0.8)]]
    tri = [(-s * 0.7, -s), (s * 0.45, 0.0), (-s * 0.7, s)]
    if kind == "ffwd":
        return [[(x - s * 0.55, y) for (x, y) in tri], [(x + s * 0.65, y) for (x, y) in tri]]
    if kind == "rewind":
        return [[(-x - s * 0.55, y) for (x, y) in reversed(tri)], [(-x + s * 0.65, y) for (x, y) in reversed(tri)]]
    raise ValueError(kind)


def piano_key(name, pivot, w, length, thick, mat, glyph=None, glyph_h=0.008, depth=0.0012):
    """A piano key hinged at its BACK edge (the pivot, at the key's top-back centre): the body runs from the pivot
    toward +Z (the player) by `length`, `thick` below the pivot plane, with a raised pictogram on top. The
    object's origin is `pivot`; press = a negative angle about local +X dips the front end."""
    px, py, pz = pivot
    body = K.gbox("kbody", (px - w / 2, py - thick, pz), (px + w / 2, py, pz + length), mat, 0.0012, 1)
    parts = [body]
    if glyph:
        g = L.curve_solid("kglyph", arrow_loops(glyph, glyph_h), depth, bevel=0.0002, mat=mat, drop_bottom=True)
        g.data.transform(Matrix.Translation((px, py, pz + length * 0.55)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
        parts.append(g)
    return K.part(name, parts, pivot=pivot)


def person_loops(h):
    """A standing-figure pictogram (head disc + body) centred on its box, h tall, +y up: two loops."""
    r = h * 0.14
    head = [(r * math.cos(2 * math.pi * i / 10), h / 2 - r + r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    top = h / 2 - 2 * r - h * 0.03
    body = [(-h * 0.17, top), (h * 0.17, top), (h * 0.21, top - h * 0.28), (h * 0.11, top - h * 0.28),
            (h * 0.11, -h / 2), (h * 0.02, -h / 2), (h * 0.02, top - h * 0.36), (-h * 0.02, top - h * 0.36),
            (-h * 0.02, -h / 2), (-h * 0.11, -h / 2), (-h * 0.11, top - h * 0.28), (-h * 0.21, top - h * 0.28)]
    return [A.ccw(head), A.ccw(body)]


def slice_x(obj, step, x0, x1) -> None:
    """Cut a (G-frame) mesh with planes x = k * step so it can be bent round a vertical axis."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    k0, k1 = int(math.floor(x0 / step)), int(math.ceil(x1 / step))
    for k in range(k0, k1 + 1):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=(k * step, 0, 0), plane_no=(1, 0, 0))
    bm.to_mesh(obj.data)
    bm.free()


def wrap_y(obj, r) -> None:
    """Bend a G-frame mesh built in the XY plane facing +Z (x = arc length from north, +x = east) round the vertical
    axis: (x, y, z) -> on the cylinder of radius r - z at angle x / r from north (clockwise from above), facing the
    axis. Used for the memorial band (face at r, geometry at z > 0 goes INTO the wall)."""
    for v in obj.data.vertices:
        x, y, z = v.co
        a = x / r
        rr = r + z
        v.co = (rr * math.sin(a), y, -rr * math.cos(a))
    obj.data.update()


def polar_frame(r, phi_deg, y, radial_out=False):
    """4x4 G-frame matrix at radius r / angle phi (from north, clockwise from above) / height y whose local +Z
    points toward the axis (the Gallery centre) and local +X runs along the arc toward +phi (the viewer's right
    seen from the centre... i.e. east on the north arc). radial_out=True points +Z away from the axis."""
    a = math.radians(phi_deg)
    pos = Vector((r * math.sin(a), y, -r * math.cos(a)))
    ez = Vector((-math.sin(a), 0.0, math.cos(a)))
    if radial_out:
        ez = -ez
    ey = Vector((0.0, 1.0, 0.0))
    ex = ey.cross(ez)
    return Matrix(((ex.x, ey.x, ez.x, pos.x), (ex.y, ey.y, ez.y, pos.y), (ex.z, ey.z, ez.z, pos.z), (0, 0, 0, 1)))


def cloth_patch(name, origin, u, v, nu, nv, sag, mat, seed=1, amp=0.0):
    """A sagging rectangular cloth: origin + a u + b v with a cosine sag along -Y of `sag` at the centre plus a
    little random noise; double-sided look comes from the material (faces look +Y x ...)."""
    import random
    rng = random.Random(seed)
    U, Vv = Vector(u), Vector(v)
    bm = bmesh.new()
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            fu, fv = i / nu, j / nv
            s = math.sin(math.pi * fu) * math.sin(math.pi * fv) * sag
            n = rng.uniform(-amp, amp) if 0 < i < nu and 0 < j < nv else 0.0
            row.append(bm.verts.new(Vector(origin) + U * fu + Vv * fv + Vector((0.0, -s + n, 0.0))))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = K.obj_from_bm(name, bm, mat)
    # make the faces look up (+Y)
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        if f.normal.y < 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    A.hint(o, 80.0)
    return o


def sausage(name, a, b, r, rings=8, sides=10, mat=FABRIC, squash=1.0):
    """A soft rounded cylinder (sleeping bag, bolster) from a to b with hemispherical ends; squash < 1 flattens it
    vertically."""
    a, b = Vector(a), Vector(b)
    d = (b - a).length
    prof = [(0.0, -r)]
    for i in range(1, rings):
        t = math.pi / 2 * i / rings
        prof.append((r * math.sin(t), -r * math.cos(t)))
    prof += [(r, 0.0), (r, d)]
    for i in range(1, rings):
        t = math.pi / 2 * i / rings
        prof.append((r * math.cos(t), d + r * math.sin(t)))
    prof.append((0.0, d + r))
    o = K.glathe(name, prof, tuple(a), tuple(b - a), sides, mat, smooth=80.0)
    if squash != 1.0:
        c = (a + b) / 2
        for v in o.data.vertices:
            v.co.y = c.y + (v.co.y - c.y) * squash
        o.data.update()
    return o


# ====================================================================== GLB verification
def verify(path, required=(), identity=(), expect=None, parents=None, rot_expect=None, tri_budget=0, surf_budget=0,
           mat_budget=4):
    return D.verify(path, required=required, identity=identity, expect=expect, parents=parents, rot_expect=rot_expect,
                    tri_budget=tri_budget, surf_budget=surf_budget, mat_budget=mat_budget)


def bounds(names):
    return D.bounds(names)


def report(label):
    return K.report(label)


def export(name):
    return K.export(name)


# ====================================================================== QA
def qa_begin():
    D.qa_begin()


def camp_room(extra=()):
    """The Nursery shell (its camp walls included) and the camp's neighbours for world-placed QA shots:
    extra = [(name, pos, yaw, prefix)]."""
    D.room(extra=[("spectral_seal_door", D.SEAL_POS, 0.0, "qa_sd_"), ("prism_bench", D.BENCH_POS, 0.0, "qa_pb_"),
                  ("growth_chart", D.CHART_POS, D.CHART_YAW, "qa_gc_")] + list(extra))
    recs = [D.preview_material(f"qa_rec{i}s", f"receptor_{i}_solved.png", emissive=True, strength=1.4) for i in range(3)]
    for i, m in enumerate(recs):
        o = next((o for o in bpy.data.objects if o.name.startswith(f"qa_sd_receptor_{i}") and o.type == "MESH"), None)
        if o is not None and m is not None:
            K.override(o, m)
    leaf = next((o for o in bpy.data.objects if o.name.startswith("qa_sd_IA_camp_door")), None)
    if leaf is not None:
        K.pose_slide(leaf, (-1.05, 0.0, 0.0))          # the camp is open in every camp shot
    gc = next((o for o in bpy.data.objects if o.name.startswith("qa_gc_chart_image") and o.type == "MESH"), None)
    m = D.preview_material("qa_prev_chart", "chart_image.png", rough=0.6)
    if gc is not None and m is not None:
        K.override(gc, m)


def camp_lights(cam=None, fill=8.0, bulb=90.0):
    """The camp's §1.5 light (one warm omni under the bulb) + the Nursery lights beyond the doorway + the camera's
    focus_fill."""
    D.lights(cam, fill=fill, camp=False, prism_lamp=True)
    K.light("camp_lamp", "POINT", CAMP_LIGHT, bulb, "FFC27A", radius=0.03)


def gallery_room(doors=True, array=True, console=False, memorial=False):
    """The Gallery shell (+ blast doors, the Array below) for world-placed QA shots."""
    K.qa_import("shell_gallery", (0, 0, 0), 0.0, prefix="qa_sg_")
    if doors:
        K.qa_import("blast_door", (-3.70, 0.0, 0.0), 90.0, prefix="qa_dw_")
        K.qa_import("blast_door", (3.70, 0.0, 0.0), -90.0, prefix="qa_de_")
    if array:
        K.qa_import("array_below", (0, 0, 0), 0.0, prefix="qa_ab_")
    if console:
        K.qa_import("gallery_console", CONSOLE_POS, 0.0, prefix="qa_gcn_")
    if memorial:
        K.qa_import("memorial_wall", (0, 0, 0), 0.0, prefix="qa_mw_")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sg_lamp_glass"):
            K.override(o, K.glow("qa_sconce_glass", "FFD9A8", 6.0))
        if o.name.startswith("qa_ab_ring_") and o.type == "MESH" and "sym" not in o.name:
            K.override(o, K.glow("qa_array_ring", "CFF6FF", 4.0))
    M.refresh()


def gallery_lights(cam=None, fill=10.0, array_awake=False, clear=True):
    """The Gallery's §1.5 lights (key spot, the Array's up-light from the shaft, two sconces) + focus_fill."""
    if clear:
        K.clear_lights()
    K.light("key_gallery", "SPOT", (0.0, 4.4, 2.2), 900.0, "D6E6F2", radius=0.05, target=(0.0, 0.0, -1.4), spot_deg=60)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        K.light(f"array_up_{k}", "SPOT", (3.0 * math.sin(a), -1.0, -3.0 * math.cos(a)), 2200.0 if array_awake else 1500.0,
                "CFF6FF", radius=0.05, target=(0.0, 4.5, 0.0), spot_deg=50)
    sg = K.light("shaft_glow", "AREA", (0.0, -0.4, 0.0), 160.0, "CFF6FF", radius=2.6, target=(0.0, 5.0, 0.0))
    sg.visible_camera = sg.visible_glossy = sg.visible_transmission = False
    sconces = {0: (3.072, 2.76, 2.151), 1: (1.283, 2.76, 3.524), 2: (-1.283, 2.76, 3.524), 3: (-3.072, 2.76, 2.151),
               4: (-2.652, 2.76, -2.652)}
    for k, p in sconces.items():
        K.light(f"sconce_{k}", "POINT", p, 70.0 if k in (0, 3) else 25.0, "FFCF94", radius=0.06)
    if cam is not None and fill > 0:
        K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), fill, "FFE2C2", radius=0.2)


def echo_pose(model, pose, mount_obj, prefix):
    """Import an echo GLB under a mount empty (identity), keep only `pose` visible, give it the in-game ghost look."""
    h = D.attach(model, mount_obj, prefix)
    if h is None:
        print(f"{TAG} QA: {model}.glb not found, skipped")
        return None
    gm = D.ghost_material()
    for o in bpy.data.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        root = o
        while root.parent is not None and root.parent != h:
            root = root.parent
        base = root.name[len(prefix):].split(".")[0]
        if base != pose:
            o.hide_render = True
        else:
            o.data.materials.clear()
            o.data.materials.append(gm)
            o.visible_shadow = False
    return h


def preview(obj, filename, emissive=False, strength=1.0, rough=0.6):
    m = D.preview_material("qa_prev_" + obj.name, filename, emissive=emissive, strength=strength, rough=rough)
    if m is not None:
        K.override(obj, m)
    return m


def shoot(name, cam, target, vfov):
    return K.shoot(name, cam, target, vfov=vfov)


def view(name):
    return VIEWS[name]


def world_point(pos, yaw, local):
    return D.world_point(pos, yaw, local)


def want(args, tag):
    return K.want(args, tag)
