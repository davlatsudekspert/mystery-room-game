"""Shared helpers of the Chapter 3 set-dressing models (ch3_dress_camp.py, ch3_dress_corridor.py,
ch3_dress_memorial.py). Not a model itself: it is not in a build list.

Every dressing model is built in WORLD coordinates in place (origin = the world origin, like leyla_camp), as ONE mesh
with one surface per material, and spawned by the room with no colliders (nothing here is interactive). Decals are
quads of the shared alpha-blended atlas material M_Dress_Grime (game/assets/textures/dress/ch3_grime.png, made by
ch3_dress_textures.py); their UVs address the atlas cells and are kept by `finalize` (no box UVs).

  decal(cell, centre, normal, w, h, tilt, off)   a flat atlas quad on a wall / floor / ceiling
  string_line(a, b)                               a thin red cord (M_String_Red) between two points
  pin(centre, normal)                             a tack
  sheet_pin(centre, normal, tilt, w, h)           where E.pinned_sheet puts its tack (to tie a string to it)
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

TAG = "[ch3-dress]"
ATLAS = os.path.join(M.ROOT, "game", "assets", "textures", "dress", "ch3_grime.png")
CELLS_JSON = os.path.join(M.ROOT, "game", "assets", "textures", "dress", "ch3_grime_cells.json")
AW, AH = 2048, 1024
GRIME = "M_Dress_Grime"
WOOL, PLASTER_DARK, STONE_DARK = "M_Dress_Wool", "M_Dress_Plaster_Dark", "M_Dress_Stone_Dark"
STEEL, BRASS, PAINT, WOOD = "M_Steel_Dark", "M_Brass_Aged", "M_Steel_Painted", "M_Wood_Panel"
PAPER, LEATHER, STRING = "M_Paper", "M_Leather", "M_String_Red"
GLASS, FLAME, CRIMSON = "M_Glass", "M_Emissive_Warm", "M_Enamel_Crimson"
CREAM, WALNUT, STONE = "M_Enamel_Cream", "M_Wood_Walnut", "M_Stone"
RUBBER, GREEN, LINEN, VELVET = "M_Rubber", "M_Paint_Green", "M_Linen", "M_Velvet"
with open(CELLS_JSON) as _f:
    CELLS = json.load(_f)
TILE = 0.15
# the camp's interior faces (docs/models/ch3.md §1.1; the tile faces of shell_nursery's camp_walls)
WALL_N, WALL_W, WALL_S, WALL_E = -3.965, 4.535, -1.203, 7.6
CAMP_LO = (WALL_W + 0.002, 0.0, WALL_N + 0.002)
CAMP_HI = (WALL_E - 0.002, 2.9, WALL_S - 0.002)
WALLS = {   # name: (normal into the room, point(a, y)); a = x on the north / south wall, z on the west / east wall
    "N": ((0, 0, 1), lambda a, y: (a, y, WALL_N)),
    "S": ((0, 0, -1), lambda a, y: (a, y, WALL_S)),
    "W": ((1, 0, 0), lambda a, y: (WALL_W, y, a)),
    "E": ((-1, 0, 0), lambda a, y: (WALL_E, y, a)),
}


def ensure_materials() -> None:
    """Preview materials (Godot swaps every M_* slot for res://assets/materials/<name>.tres)."""
    E.ensure_materials()
    mat = M.material(GRIME, color="3A2A1C", rough=0.9, alpha=0.99, image=ATLAS)     # QA preview: the atlas alpha drives the blend
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    if bsdf is not None and tex is not None and not bsdf.inputs["Alpha"].links:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    M.material(WOOL, color="8A4034", rough=0.95)
    M.material(PLASTER_DARK, color="2C3436", rough=0.95)
    M.material(STONE_DARK, color="4A4844", rough=0.8)
    for name in (WOOD, STEEL, BRASS, PAINT, PAPER, LEATHER, STRING, GLASS, FLAME, CRIMSON, CREAM, WALNUT, STONE, RUBBER, GREEN, LINEN, VELVET):
        M.material(name)


def uv_of(cell: str, inset: float = 3.0):
    """Atlas cell -> Blender UV rect (u0, v0, u1, v1): v0 = the bottom edge (glTF flips v on export)."""
    x, y, w, h = CELLS[cell]
    return ((x + inset) / AW, 1.0 - (y + h - inset) / AH, (x + w - inset) / AW, 1.0 - (y + inset) / AH)


def wall_axes(normal, tilt=0.0):
    n = Vector(normal).normalized()
    up = Vector((0, 1, 0))
    ux = up.cross(n)
    if ux.length < 1e-6:
        ux = Vector((1, 0, 0))     # floor / ceiling: u along +X, v along -Z (from above)
    ux.normalize()
    vy = n.cross(ux).normalized()
    if tilt:
        r = Matrix.Rotation(math.radians(tilt), 3, n)
        ux, vy = r @ ux, r @ vy
    return n, ux, vy


def decal(cell, centre, normal, w, h, tilt=0.0, off=0.004, name=None, flip=False):
    """A flat quad of atlas cell `cell` at `centre` (a point ON the surface), facing `normal`, w x h metres, turned `tilt`
    degrees in its plane, lifted `off` metres off the surface. flip mirrors it left-right."""
    n, ux, vy = wall_axes(normal, tilt)
    uv = uv_of(cell)
    if flip:
        uv = (uv[2], uv[1], uv[0], uv[3])
    return K.quad(name or ("dc_" + cell), tuple(Vector(centre) + n * off), tuple(ux), tuple(vy), w, h, GRIME, uv=uv)


def string_line(a, b, r=0.0016, sag=0.0, name="cord", mat=STRING):
    """A thin cord from a to b (3 sides), with an optional sag in the middle."""
    a, b = Vector(a), Vector(b)
    if sag > 0:
        mid = (a + b) / 2 - Vector((0, sag, 0))
        return K.V.tube(name, [tuple(a), tuple(mid), tuple(b)], r, sides=3, mat=mat, fillet=0.0)
    return D.rod(name, tuple(a), tuple(b), r, segs=3, mat=mat, caps=False, smooth=0)


def pin(centre, normal, r=0.0055, mat=STEEL):
    return K.rivet("tack", r, tuple(centre), normal=tuple(normal), mat=mat, segs=6)


def sheet_pin(centre, normal, tilt, w, h):
    """The tack position of E.pinned_sheet(centre, normal, w, h, tilt)."""
    n = Vector(normal).normalized()
    x = Vector((0, 1, 0)).cross(n)
    if x.length < 1e-6:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    t = h / 2 - 0.02
    top = Matrix.Rotation(math.radians(tilt), 3, "Z") @ Vector((0.0, t, 0.0))
    return Vector(centre) + x * top.x + y * top.y + n * 0.0019


def clip_quads(objs, lo, hi, eps=1e-4):
    """Clamp the corners of axis-aligned atlas quads (G-frame) into the box lo..hi and re-derive their UVs, so a decal
    near a corner never pokes through the neighbouring wall, the roof or the floor."""
    lo, hi = Vector(lo), Vector(hi)
    for o in objs:
        me = o.data
        if len(me.polygons) != 1 or len(me.vertices) != 4 or not me.uv_layers:
            continue
        v = [Vector(p.co) for p in me.vertices]
        e1, e2 = v[1] - v[0], v[3] - v[0]
        aligned = all(sum(1 for c in e if abs(c) > 1e-5) == 1 for e in (e1, e2))
        if not aligned:
            continue
        uvl = me.uv_layers[0].data
        uv = [Vector(uvl[i].uv) for i in range(4)]
        new = [Vector((min(max(p.x, lo.x), hi.x), min(max(p.y, lo.y), hi.y), min(max(p.z, lo.z), hi.z))) for p in v]
        if all((a - b).length < eps for a, b in zip(v, new)):
            continue
        for i, p in enumerate(new):
            s = (p - v[0]).dot(e1) / e1.dot(e1)
            t = (p - v[0]).dot(e2) / e2.dot(e2)
            uvl[i].uv = tuple(uv[0] + (uv[1] - uv[0]) * s + (uv[3] - uv[0]) * t)
            me.vertices[i].co = p
        me.update()


def report_outside(objs, lo, hi, tol=0.012):
    """Print every object that leaves the box lo..hi (G-frame), so props never poke through a wall."""
    n = 0
    for o in objs:
        if o is None or o.type != "MESH":
            continue
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        a = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        b = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        if any(a[i] < lo[i] - tol or b[i] > hi[i] + tol for i in range(3)):
            n += 1
            print(f"{TAG} OUTSIDE {o.name}: {tuple(round(c, 3) for c in a)} .. {tuple(round(c, 3) for c in b)}")
    return n


def at(x, y, z, rot_y=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot_y), 4, "Y")


def place(objs, matrix):
    for o in objs:
        o.data.transform(matrix)
    return objs


class Decals:
    """Collects atlas quads: on(cell, wall, a, y, w, h, tilt) for a wall, floor(cell, x, z, w, h, tilt) for the floor."""

    def __init__(self):
        self.items = []

    def on(self, cell, wall, a, y, w, h, tilt=0.0, off=0.004, flip=False):
        n, pt = WALLS[wall]
        self.items.append(decal(cell, pt(a, y), n, w, h, tilt, off, flip=flip))

    def floor(self, cell, x, z, w, h, tilt=0.0, off=0.0035):
        self.items.append(decal(cell, (x, 0.0, z), (0, 1, 0), w, h, tilt, off))


def polar(r, phi_deg, y=0.0):
    """World point at radius r, angle phi from NORTH (-Z) clockwise seen from above (toward +X)."""
    return K.polar(r, phi_deg, y)


def arc_solid(name, prof, a0, a1, n, mat, drop=()):
    """A prism swept round the Y axis: closed profile [(r, y)] between angles a0..a1 (degrees from north, clockwise), end
    caps included; the profile edges listed in `drop` (edge k joins point k and k + 1) are left open (they lie against
    another solid)."""
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        rings.append([bm.verts.new((r * math.sin(a), y, -r * math.cos(a))) for (r, y) in prof])
    m = len(prof)
    side = {}
    for i in range(n):
        for k in range(m):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % m], rings[i + 1][(k + 1) % m], rings[i + 1][k]))
            side.setdefault(k, []).append(f)
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[n])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for k in drop:
        bmesh.ops.delete(bm, geom=[f for f in side[k] if f.is_valid], context="FACES")
    return K.obj_from_bm(name, bm, mat)


def snap(v: float, step: float = TILE, phase: float = 0.0) -> float:
    return round((v - phase) / step) * step + phase


def jit(o, amp, seed):
    E.jitter(o, amp, seed)
    return o


def finalize() -> None:
    """World-scale box UVs on every face except the atlas quads (their 0..1 cell UVs stay)."""
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH":
            continue
        M.apply_modifiers(obj)
        M.box_uv(obj, 1.0, skip_materials=("M_Decal_", GRIME, E.SHQ))


def tri_report(name: str) -> int:
    return K.report(name)


def export_and_verify(name, required, expect, tri_budget, surf_budget, mat_budget, bounds_note=""):
    path = E.export(name)
    errs = E.verify(path, required=required, identity=required, expect=expect, parents={n: None for n in required},
                    tri_budget=tri_budget, surf_budget=surf_budget, mat_budget=mat_budget)
    print(f"{TAG} VERIFY {name} {'FAILED: ' + str(errs) if errs else 'OK'}")
    return path, errs
