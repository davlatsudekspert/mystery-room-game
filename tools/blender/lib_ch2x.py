"""MYSTERY ROOM — helpers for the Chapter 2 expansion models ("The Whole Building", docs/CHAPTER2_EXPANSION.md).

Builds on lib_ch2_arch (Godot-coordinate wrappers, GLB verifier, QA scene helpers) and never edits the shared
libraries. All coordinates are **Godot, metres** (front +Z, Y up) unless a name says Blender.

  * begin()              reset the scene, register the preview colours of the new slots, create materials
  * wheel(...)           spoked hand wheel (cast rim, spokes, hub, boss) around a Godot axis
  * pipe(...) / flange   round pipe along Godot points with flange rings
  * gauge(...)           pressure gauge (brass bezel, cream face, needle part)
  * rivet_line(...)      rivet rows
  * qa_*                 prop studio renders (written to $MR_QA_DIR or the scratchpad, never into qa/blender)
  * room_shell(...)      box room (floor, ceiling, four walls with optional openings) with per-wall materials
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
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G, GV, gbox, gcyl, glathe, glathe_loop, gtube, gquad, gpoly, gtext, part, mount  # noqa: E402,F401

ROOT = M.ROOT
TAG = "[ch2x]"
C.TAG = TAG
C.QA_SUB = "ch2x"
QA_OUT = os.environ.get("MR_QA_DIR") or os.path.join(__import__("tempfile").gettempdir(), "mr_qa_ch2x")
M.QA_DIR = QA_OUT          # prop/room QA renders never go into the committed qa/blender tree
DECALS = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2x")

# Slots of the expansion (preview colour, roughness, metal, emission, alpha). The Godot .tres files come from
# tools/materials/make_ch2x_materials.py; the texture folder of the preview is name[2:].lower().
M.PREVIEW.update({
    "M_Iron_Rust": ("4A3A30", 0.7, 0.6, None, 1.0),
    "M_Wallpaper_Cell": ("C4A56C", 0.85, 0.0, None, 1.0),
    "M_Wool_Knit": ("8C4A3A", 0.96, 0.0, None, 1.0),
    "M_Steel_Galv": ("8E9CA4", 0.45, 0.85, None, 1.0),
    "M_Wallpaper_Office": ("2F4A3B", 0.7, 0.3, None, 1.0),
    "M_Paint_Black": ("151716", 0.85, 0.0, None, 1.0),
    "M_Frost": ("E4F0F6", 0.8, 0.0, None, 0.78),
    "M_Acetate": ("C9B890", 0.18, 0.0, None, 0.34),
    "M_Emissive_Table": ("EFE9D8", 0.4, 0.0, "FFF1D0", 1.0),
    "M_Emissive_Safelight": ("5A0A08", 0.3, 0.0, "FF1A0E", 1.0),
    "M_Tile_Glazed": ("B9C4C2", 0.3, 0.0, None, 1.0),
    "M_Chequer": ("7A7D7C", 0.5, 0.35, None, 1.0),
    "M_Porcelain": ("E8E2D4", 0.15, 0.0, None, 1.0),
    "M_Rock": ("4A4A46", 0.9, 0.0, None, 1.0),
})
for _n in ("M_Decal_CellDrawing", "M_Decal_PlanPlate", "M_Decal_ManifoldPlate", "M_Decal_ChestRings",
           "M_Decal_RollTags", "M_Decal_BoardPlate", "M_Decal_CabinetLabel", "M_Decal_Negatives", "M_Decal_Sheet",
           "M_Decal_CarriageTags", "M_Decal_FloorPlan", "M_Decal_WeightMarks", "M_Decal_LiftPlate",
           "M_Decal_SafeStencil", "M_Decal_Prints", "M_Decal_PipeDiagram", "M_Decal_Gauge"):
    M.PREVIEW.setdefault(_n, ("DCCFB2", 0.8, 0.0, None, 1.0))

FONT = C.FONT_SANS_B
FONT_SERIF = C.FONT_SERIF_B


# ---------------------------------------------------------------- scene
def begin() -> None:
    M.reset_scene()
    C.ensure_materials()
    A.prepare_materials()


def decal(slot: str, fname: str):
    """Decal material with the generated image (QA preview); images live in game/assets/textures/decals/ch2x/."""
    p = os.path.join(DECALS, fname)
    return M.material(slot, image=p if os.path.exists(p) else None)


def finish(name: str, required=(), identity=(), budget: int | None = None, expect=None, show=(), wood=True) -> list:
    """Finalize UVs, report, export lean GLB, verify. Returns the verify errors."""
    C.finalize_all(wood_grain=wood)
    total = C.report(name)
    path = C.export(name)
    errs = C.verify_glb(path, required=list(required), identity=list(identity), budget=budget, expect=expect, show=show)
    print(f"{TAG} {name}: tris={total} errors={len(errs)}")
    return errs


def sm(obj, angle=40.0):
    return A.hint(obj, angle)


# ---------------------------------------------------------------- mechanical shapes
def wheel(name: str, r: float, tube: float, spokes: int, centre, axis: str = "z", hub_r: float = 0.02,
          boss_h: float = 0.03, mat: str = "M_Iron_Rust", hub_mat: str = "M_Brass_Aged", ring_seg: int = 18, phase=0.0):
    """Cast hand wheel: torus rim, tapered spokes, hub and a brass boss, standing at `centre`, axis `z` = facing +Z.
    Returns one joined object whose origin is at `centre`."""
    objs = [M.torus(name + "_rim", r, tube, major_seg=ring_seg, minor_seg=5, mat=mat)]
    sp_len = r - hub_r * 0.5
    for k in range(spokes):
        a = phase + 2 * math.pi * k / spokes
        s = M.box(f"{name}_spoke{k}", (sp_len, tube * 1.5, tube * 1.3), mat=mat, bevel=0.0, segments=1)
        s.location = (math.cos(a) * (hub_r * 0.5 + sp_len / 2), math.sin(a) * (hub_r * 0.5 + sp_len / 2), 0)
        s.rotation_euler = (0, 0, a)
        objs.append(s)
    objs.append(M.cylinder(name + "_hub", hub_r, tube * 2.4, verts=12, mat=mat, bevel=0.0))
    boss = M.cylinder(name + "_boss", hub_r * 0.62, boss_h, loc=(0, 0, boss_h * 0.5 + tube), verts=14, mat=hub_mat,
                      bevel=0.0012, radius_top=hub_r * 0.5)
    objs.append(boss)
    for o in objs:
        A.place(o, Matrix.Identity(4))
    j = M.join(objs, name)
    C.aim(j, axis)
    j.data.transform(Matrix.Translation(GV(centre)))
    j.location = (0, 0, 0)
    return sm(j, 55.0)


def pipe(name: str, pts, r: float, mat="M_Copper", sides=12, fillet=0.0, flange_ends=True, flange_r=None,
         flange_t=0.012, flange_mat=None, bolts=6, caps=True):
    """Round pipe along Godot points; optional flange discs with bolt heads at both ends. One object."""
    objs = [gtube(name + "_p", pts, r, sides=sides, mat=mat, fillet=fillet, caps=caps)]
    if flange_ends:
        fr = flange_r or r * 1.7
        for i, (p, q) in enumerate(((pts[0], pts[1]), (pts[-1], pts[-2]))):
            d = (Vector(q) - Vector(p)).normalized()
            off = Vector(p) + d * (flange_t * 0.5)
            ax = max(range(3), key=lambda k: abs(d[k]))
            axn = "xyz"[ax]
            f = gcyl(f"{name}_fl{i}", fr, flange_t, tuple(Vector(p) + d * 0.0), axis=("-" + axn if d[ax] < 0 else axn),
                     verts=14, mat=flange_mat or mat, bevel=0.0)
            objs.append(f)
            for b in range(bolts):
                a = 2 * math.pi * b / bolts
                perp = [k for k in range(3) if k != ax]
                v = [0.0, 0.0, 0.0]
                v[perp[0]] = math.cos(a) * fr * 0.78
                v[perp[1]] = math.sin(a) * fr * 0.78
                bp = Vector(p) + d * flange_t + Vector(v)
                objs.append(gcyl(f"{name}_b{i}_{b}", fr * 0.11, flange_t * 0.7, tuple(bp),
                                 axis=("-" + axn if d[ax] < 0 else axn), verts=6, mat="M_Steel_Dark", bevel=0.0))
    return M.join(objs, name) if len(objs) > 1 else objs[0]


def rivets(prefix: str, pts, r: float, normal: str, mat="M_Iron_Rust", segs=6):
    """Dome rivets at Godot points facing the Godot axis `normal`, joined into one object (None if empty)."""
    objs = []
    for i, p in enumerate(pts):
        objs.append(gcyl(f"{prefix}{i}", r, r * 0.9, p, axis=normal, verts=segs, mat=mat, bevel=0.0, r_top=r * 0.7))
    return M.join(objs, prefix) if len(objs) > 1 else (objs[0] if objs else None)


def gauge(name: str, centre, r: float = 0.06, axis: str = "z", face_mat="M_Enamel_Cream", segs: int = 20,
          rest_deg: float = 225.0):
    """Pressure gauge facing the Godot axis `axis`: brass case, polished bezel, cream face with 11 ticks over a
    270-degree sweep (tick k at 225 - 27 k degrees from the dial's +X, counter-clockwise as seen), hub cap.
    Returns (body, needle): the needle is its own object whose origin is the dial centre (+4 mm) with the pointer
    baked at `rest_deg` (225 = value 0), so the code rotates it about the axis by -27 deg per tick."""
    n = Vector(C.AXES[axis])
    objs = [M.cylinder(name + "_case", r * 1.12, r * 0.5, loc=(0, 0, -r * 0.25), verts=segs, mat="M_Brass_Aged",
                       bevel=0.0, segments=1),
            M.torus(name + "_bezel", r * 1.02, r * 0.08, loc=(0, 0, 0.0), major_seg=segs, minor_seg=5, mat="M_Brass_Polished"),
            M.cylinder(name + "_face", r * 0.97, 0.004, loc=(0, 0, -0.0010), verts=segs, mat=face_mat, bevel=0.0)]
    for k in range(11):
        a = math.radians(225 - 27 * k)
        ln = r * (0.22 if k % 2 == 0 else 0.13)
        rad = r * 0.88 - ln / 2
        t = M.box(f"{name}_t{k}", (ln, r * 0.045, 0.0015), loc=(math.cos(a) * rad, math.sin(a) * rad, 0.0013),
                  rot=(0, 0, a), mat="M_Lacquer_Black", bevel=0.0, segments=1)
        objs.append(t)
    # red danger wedge on the last two ticks
    ra = math.radians(225 - 27 * 9.0)
    objs.append(M.box(name + "_red", (r * 0.14, r * 0.07, 0.0015), loc=(math.cos(ra) * r * 0.64, math.sin(ra) * r * 0.64, 0.0013),
                      rot=(0, 0, ra), mat="M_Enamel_Crimson", bevel=0.0, segments=1))
    for o in objs:
        A.place(o, Matrix.Identity(4))
    body = M.join(objs, name)
    C.aim(body, axis)
    body.data.transform(Matrix.Translation(GV(centre)))
    body.location = (0, 0, 0)
    ra = math.radians(rest_deg)
    nd = M.box(name + "_needle", (r * 0.78, r * 0.05, 0.0016), loc=(math.cos(ra) * r * 0.39, math.sin(ra) * r * 0.39, 0.0),
               rot=(0, 0, ra), mat="M_Lacquer_Black", bevel=0.0, segments=1)
    hub = M.cylinder(name + "_hub", r * 0.09, 0.004, loc=(0, 0, 0.0), verts=10, mat="M_Brass_Polished", bevel=0.0)
    for o in (nd, hub):
        A.place(o, Matrix.Identity(4))
    needle = M.join([nd, hub], name + "_needle")
    C.aim(needle, axis)
    c4 = Vector(centre) + n * 0.004
    needle.data.transform(Matrix.Translation(GV(tuple(c4))))
    needle.location = (0, 0, 0)
    needle = part(name + "_needle", [needle], tuple(c4), presmooth=False)
    return body, needle


def bracket(name: str, p0, p1, w=0.03, t=0.006, mat="M_Steel_Dark"):
    """Flat strap between two Godot points."""
    a, b = Vector(p0), Vector(p1)
    mid = (a + b) / 2
    d = b - a
    ln = d.length
    ax = max(range(3), key=lambda k: abs(d[k]))
    size = [w, w, w]
    size[ax] = ln
    other = [k for k in range(3) if k != ax]
    size[other[0]] = t
    return gbox(name, tuple(mid - Vector(size) / 2), tuple(mid + Vector(size) / 2), mat=mat, bevel=0.0008)


def join_all(name: str, objs):
    objs = [o for o in objs if o is not None]
    A.presmooth(objs)
    return M.join(objs, name) if len(objs) > 1 else objs[0]


# ---------------------------------------------------------------- room shell
def wall_box(name, mn, mx, mat):
    return gbox(name, mn, mx, mat=mat, bevel=0.0)


def cut(target, name, mn, mx):
    """Boolean-subtract a Godot box from `target`; the cutter is deleted."""
    cutter = gbox(name, mn, mx, mat="M_Concrete", bevel=0.0)
    M.boolean(target, cutter)
    return target


def wallset(prefix, x0, x1, z0, z1, h, t, mats, openings=None, floor_mat="M_Concrete", ceil_mat="M_Ceiling"):
    """Closed-solid walls around the interior box [x0,x1]x[z0,z1] (thickness t outside), floor and ceiling slabs.
    mats = dict(n, s, e, w) -> slot or (lower_slot, split_height, upper_slot).
    openings = {side: [(a0, a1, y0, y1)]} where a runs along x (n/s) or z (e/w). Returns dict name -> object."""
    openings = openings or {}
    out = {}

    def wall(side, mn, mx, along):
        m = mats[side]
        parts = []
        if isinstance(m, tuple):
            lo, hs, up = m
            parts.append((gbox(f"{prefix}_{side}_lo", mn, (mx[0], hs, mx[2]), mat=lo, bevel=0.0), "lo"))
            parts.append((gbox(f"{prefix}_{side}_hi", (mn[0], hs, mn[2]), mx, mat=up, bevel=0.0), "hi"))
        else:
            parts.append((gbox(f"{prefix}_{side}", mn, mx, mat=m, bevel=0.0), ""))
        for (a0, a1, y0, y1) in openings.get(side, []):
            for ob, _ in parts:
                if along == "x":
                    cut(ob, "cut", (a0, y0, mn[2] - 0.1), (a1, y1, mx[2] + 0.1))
                else:
                    cut(ob, "cut", (mn[0] - 0.1, y0, a0), (mx[0] + 0.1, y1, a1))
        out[side] = [p for p, _ in parts]
        return out[side]

    wall("n", (x0 - t, 0, z0 - t), (x1 + t, h, z0), "x")
    wall("s", (x0 - t, 0, z1), (x1 + t, h, z1 + t), "x")
    wall("e", (x1, 0, z0), (x1 + t, h, z1), "z")
    wall("w", (x0 - t, 0, z0), (x0, h, z1), "z")
    out["floor"] = [gbox(f"{prefix}_floor", (x0 - t, -0.2, z0 - t), (x1 + t, 0, z1 + t), mat=floor_mat, bevel=0.0)]
    out["ceiling"] = [gbox(f"{prefix}_ceiling", (x0 - t, h, z0 - t), (x1 + t, h + 0.2, z1 + t), mat=ceil_mat, bevel=0.0)]
    return out


# ---------------------------------------------------------------- QA (prop studio + room lights)
STUDIO = [((1.0, -1.2, 1.4), 900, "FFE2C0", 1.5), ((-1.4, -0.6, 0.8), 380, "BFD4FF", 2.0),
          ((0.2, 1.4, 1.6), 600, "FFFFFF", 1.0)]


def studio_floor(size=3.0, mat_colour="2A2622"):
    pl = M.box("qa_floor", (size, size, 0.02), loc=(0, 0, -0.01), mat="M_Concrete", bevel=0.0)
    return pl


def qa_props(name, shots, floor=True, samples=24, res=(800, 560), world=0.12, lights=None, hide=()):
    """shots: list of (tag, cam_godot, target_godot, vfov)."""
    C.qa_begin(samples=samples)
    if floor:
        fl = studio_floor()
        fl.name = "qa_floor"
    for tag, cam, tgt, vfov in shots:
        C.shoot(f"{name}{tag}", cam, tgt, vfov=vfov, res=res, samples=samples, world=world, lights=lights or STUDIO)
    # remove the floor so a later run in the same process stays clean
    if floor:
        bpy.data.objects.remove(bpy.data.objects["qa_floor"], do_unlink=True)


def want_render(args) -> bool:
    return "--no-render" not in args


def room_lights(spec):
    """spec: [(name, kind, godot_pos, energy, colour, radius)] QA point lights."""
    for nm, kind, pos, en, col, rad in spec:
        C.qa_light(nm, kind, pos, en, col, radius=rad)


def top(objs, n=12):
    """Debug: print the heaviest objects of a list (MR_DEBUG=1)."""
    if not os.environ.get("MR_DEBUG"):
        return
    rows = sorted(((A.tris(o), o.name) for o in objs if o is not None and o.type == "MESH"), reverse=True)
    print(TAG, "heaviest:", rows[:n], "sum", sum(r[0] for r in rows))
    if os.environ.get("MR_DEBUG") == "2":
        for o in objs:
            if o is None or o.type != "MESH":
                continue
            pts = [o.matrix_world @ v.co for v in o.data.vertices]
            if not pts:
                continue
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            g = lambda v: (round(v[0], 3), round(v[2], 3), round(-v[1], 3))
            print(TAG, "bbox", o.name, "godot lo", g(lo) if False else (round(lo[0],3), round(lo[2],3), round(-hi[1],3)), "hi", (round(hi[0],3), round(hi[2],3), round(-lo[1],3)))


def flat_poly(name: str, pts_xz, y: float, mat: str, up: bool = True):
    """Flat polygon in the Godot XZ plane at height y (normal up when `up`). One n-gon face."""
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for x, z in pts_xz]
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if (f.normal.z < 0) == up:
        f.normal_flip()
    bmesh.ops.triangulate(bm, faces=bm.faces)
    return A.obj_from_bm(name, bm, mat)
