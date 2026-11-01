"""MYSTERY ROOM — shared builders for the upper floor of the Chapter 2 expansion (R5 Reading Gallery, R6 Plate Room, R7 Director's Office).

Sits on top of lib_ch2x (never edits it). All coordinates are Godot metres (front +Z, Y up).

  rot_godot(objs, axis, deg, pivot)   rotate objects about a Godot axis through a Godot point (bakes into the mesh)
  banker_lamp(...)                    green glass-shaded brass desk lamp (list of objects; `shade_mat` selectable)
  chair_wood(...)                     simple turned-leg reading chair (list of objects)
  frame_art(...)                      picture frame + original bust silhouette art, as geometry (no image needed)
  book_row(...)                       a run of upright books (boxes of varied height/colour), one object
  arch_window_cut(...)                cut a round-headed window opening into wall boxes
  louvres / curtain helpers           small repeated elements
"""
from __future__ import annotations

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402,F401

AX = {"x": (1, 0, 0), "y": (0, 0, 1), "z": (0, -1, 0)}   # Godot axis -> Blender axis vector


def rot_godot(objs, axis: str, deg: float, pivot=(0, 0, 0)):
    """Bake a rotation about the Godot axis through `pivot` into each object's mesh. Returns objs."""
    p = GV(pivot)
    m = Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, Vector(AX[axis])) @ Matrix.Translation(-p)
    for o in objs:
        if o is not None:
            A.place(o, m)                  # bakes the object's own location/rotation first, then the matrix
    return objs


def move(objs, d):
    m = Matrix.Translation(GV(d))
    for o in objs:
        if o is not None:
            A.place(o, m)
    return objs


def banker_lamp(prefix: str, x: float, y: float, z: float, yaw: float = 0.0, shade_mat: str = "M_Glass_Green", base_mat="M_Brass_Aged",
                with_bulb: bool = False):
    """A banker's lamp standing on y: brass round base and stem, a long half-cylinder shade (open below) in green glass.
    The shade runs along x and faces +Z. Returns objs."""
    o = [glathe(prefix + "base", [(0.0, 0.0), (0.070, 0.0), (0.072, 0.008), (0.060, 0.022), (0.026, 0.040), (0.016, 0.07), (0.0, 0.07)],
                (x, y, z), axis="y", segments=16, mat=base_mat),
         gcyl(prefix + "stem", 0.0085, 0.20, (x, y + 0.06, z), axis="y", verts=8, mat="M_Brass_Polished", bevel=0.0)]
    r0, r1, ln, n = 0.062, 0.057, 0.30, 10
    sy = y + 0.25
    outer = [(math.cos(math.pi * i / n) * r0, math.sin(math.pi * i / n) * r0 * 0.95) for i in range(n + 1)]
    inner = [(math.cos(math.pi * i / n) * r1, math.sin(math.pi * i / n) * r1 * 0.95) for i in range(n + 1)]
    loop = outer + list(reversed(inner))                   # (z, y) pairs of the arch section, CCW as seen from +x?
    mat4 = X.C.gframe((x + ln / 2, sy, z), (0, 0, 1), (0, 1, 0))
    o.append(X.gpoly(prefix + "shade", loop, ln, mat4, mat=shade_mat))
    o.append(gcyl(prefix + "hang", 0.009, 0.06, (x, sy - 0.02, z), axis="y", verts=8, mat=base_mat, bevel=0.0))
    for sx in (-1, 1):
        o.append(gcyl(prefix + f"endcap{sx}", 0.010, 0.012, (x + sx * (ln / 2 + 0.002), sy + 0.03, z), axis="x", verts=8, mat=base_mat, bevel=0.0))
    if with_bulb:
        o.append(M.sphere(prefix + "bulb", 0.020, loc=G(x, sy + 0.012, z), segments=10, rings=6, mat="M_Emissive_Warm"))
    if abs(yaw) > 1e-6:
        rot_godot(o, "y", yaw, (x, y, z))
    return o


def chair_wood(prefix: str, x: float, z: float, yaw: float = 0.0, mat="M_Wood_Walnut", seat=0.46, back_h=0.95, leather: bool = False):
    """Simple reading chair centred at (x, z), facing +Z (rotate by yaw about Y)."""
    s = 0.21
    o = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            o.append(gbox(prefix + "leg", (x + sx * s - 0.02, 0, z + sz * s - 0.02), (x + sx * s + 0.02, seat, z + sz * s + 0.02), mat, bevel=0.003))
    o.append(gbox(prefix + "seat", (x - s - 0.03, seat, z - s - 0.03), (x + s + 0.03, seat + 0.04, z + s + 0.03),
                  "M_Leather" if leather else mat, bevel=0.006))
    for sx in (-1, 1):
        o.append(gbox(prefix + "post", (x + sx * s - 0.018, seat, z - s - 0.02), (x + sx * s + 0.018, back_h, z - s + 0.016), mat, bevel=0.003))
    o.append(gbox(prefix + "rail_t", (x - s, back_h - 0.10, z - s - 0.014), (x + s, back_h, z - s + 0.012), mat, bevel=0.004))
    o.append(gbox(prefix + "rail_m", (x - s, back_h - 0.34, z - s - 0.01), (x + s, back_h - 0.28, z - s + 0.008), mat, bevel=0.003))
    for i in range(4):
        xx = x - s + 0.07 + i * 0.1
        o.append(gbox(prefix + "splat", (xx - 0.012, seat + 0.05, z - s - 0.008), (xx + 0.012, back_h - 0.10, z - s + 0.008), mat, bevel=0.001))
    o.append(gbox(prefix + "str", (x - s, 0.14, z - s), (x + s, 0.17, z - s + 0.025), mat, bevel=0.0))
    if abs(yaw) > 1e-6:
        rot_godot(o, "y", yaw, (x, 0, z))
    return o


def book_row(name: str, x0: float, x1: float, y: float, z: float, depth: float, seed: int, hmin=0.19, hmax=0.30, mats=None, axis="x"):
    """Upright books standing on y from x0 to x1 (axis x) with their spines toward +Z. One joined object."""
    import random
    rnd = random.Random(seed)
    mats = mats or ["M_Book_Brown", "M_Book_Green", "M_Book_Red", "M_Book_Black", "M_Book_Blue", "M_Book_Gold", "M_Leather"]
    objs = []
    x = x0
    k = 0
    while x < x1 - 0.02:
        w = rnd.uniform(0.022, 0.050)
        h = rnd.uniform(hmin, hmax)
        w = min(w, x1 - x)
        lean = 0.0
        if rnd.random() < 0.06:
            lean = 1
        objs.append(gbox(f"{name}{k}", (x, y, z - depth / 2), (x + w * 0.97, y + h, z + depth / 2), rnd.choice(mats), bevel=0.0015))
        x += w
        k += 1
        if rnd.random() < 0.05:
            x += rnd.uniform(0.03, 0.08)
    return M.join(objs, name) if len(objs) > 1 else objs[0]


def bust_art(prefix: str, cx: float, cy: float, z: float, s: float, kind: int, facing="z", fg="M_Lacquer_Black", depth=0.004):
    """Original head-and-shoulders silhouette (extruded polygons) centred at (cx, cy) on a wall at depth z facing +Z
    (facing 'z') or +X ('x' puts it at x = z). `s` is the figure height. kind picks the accessory 0..4. Returns objs."""
    ex, ey = ((1, 0, 0), (0, 1, 0)) if facing == "z" else ((0, 0, -1), (0, 1, 0))
    origin = (cx, cy, z) if facing == "z" else (z, cy, cx)
    mat4 = X.C.gframe(origin, ex, ey)
    o = []
    pts = []
    for i in range(0, 13):                          # shoulders: half ellipse
        a = math.pi * i / 12
        pts.append((math.cos(a) * s * 0.46, -s * 0.5 + math.sin(a) * s * 0.30))
    o.append(X.gpoly(prefix + "sh", list(reversed(pts)), depth, mat4, mat=fg))
    head = [(math.cos(2 * math.pi * i / 16) * s * 0.17, -s * 0.02 + math.sin(2 * math.pi * i / 16) * s * 0.21) for i in range(16)]
    o.append(X.gpoly(prefix + "hd", head, depth, mat4, mat=fg))
    o.append(X.gpoly(prefix + "nk", [(-s * 0.05, -s * 0.2), (s * 0.05, -s * 0.2), (s * 0.05, -s * 0.12), (-s * 0.05, -s * 0.12)], depth, mat4, mat=fg))
    if kind % 5 == 0:     # bowler hat
        o.append(X.gpoly(prefix + "hat", [(-s * 0.2, s * 0.13), (s * 0.2, s * 0.13), (s * 0.15, s * 0.28), (-s * 0.15, s * 0.28)], depth, mat4, mat=fg))
    elif kind % 5 == 1:   # high collar
        o.append(X.gpoly(prefix + "col", [(-s * 0.09, -s * 0.2), (s * 0.09, -s * 0.2), (s * 0.12, -s * 0.07), (-s * 0.12, -s * 0.07)], depth, mat4, mat=fg))
    elif kind % 5 == 2:   # beard
        o.append(X.gpoly(prefix + "bd", [(-s * 0.12, -s * 0.10), (s * 0.12, -s * 0.10), (s * 0.06, -s * 0.28), (-s * 0.06, -s * 0.28)], depth, mat4, mat=fg))
    elif kind % 5 == 3:   # hair bun
        o.append(X.gpoly(prefix + "bun", [(-s * 0.07, s * 0.17), (s * 0.07, s * 0.17), (s * 0.07, s * 0.29), (-s * 0.07, s * 0.29)], depth, mat4, mat=fg))
    else:                 # spectacles bridge band
        o.append(X.gpoly(prefix + "gl", [(-s * 0.15, s * 0.0), (s * 0.15, s * 0.0), (s * 0.15, s * 0.04), (-s * 0.15, s * 0.04)], depth * 0.5, mat4, mat="M_Brass_Aged"))
    return o


def frame_art(prefix: str, cx: float, cy: float, z: float, w: float, h: float, kind: int, facing="z", frame_mat="M_Brass_Aged",
              card_mat="M_Paper", oval=False):
    """Framed original portrait: moulded frame, paper mat and a bust silhouette. Returns objs (picture on a wall facing +Z or +X)."""
    o = []
    t = 0.035
    if facing == "z":
        def bx(a0, b0, a1, b1, c0, c1, m):
            return gbox(prefix + "f", (cx + a0, cy + b0, z + c0), (cx + a1, cy + b1, z + c1), m, bevel=0.0025)
    else:
        def bx(a0, b0, a1, b1, c0, c1, m):
            return gbox(prefix + "f", (z + c0, cy + b0, cx - a1), (z + c1, cy + b1, cx - a0), m, bevel=0.0025)
    o.append(bx(-w / 2, -h / 2, w / 2, -h / 2 + t, 0, 0.035, frame_mat))
    o.append(bx(-w / 2, h / 2 - t, w / 2, h / 2, 0, 0.035, frame_mat))
    o.append(bx(-w / 2, -h / 2, -w / 2 + t, h / 2, 0, 0.035, frame_mat))
    o.append(bx(w / 2 - t, -h / 2, w / 2, h / 2, 0, 0.035, frame_mat))
    o.append(bx(-w / 2 + t, -h / 2 + t, w / 2 - t, h / 2 - t, 0, 0.012, card_mat))
    o += bust_art(prefix + "b", cx, cy - h * 0.06, z + 0.012, h * 0.62, kind, facing=facing)
    return o


# ---------------------------------------------------------------- walls: wall-local boxes, arched windows, door frames
def _P(axis: str, face: float, sgn: int, u: float, y: float, n: float):
    """Wall-local point -> Godot: u along the wall, y up, n out of the wall face INTO the room (n > 0 = further into the room)."""
    return (u, y, face + sgn * n) if axis == "z" else (face + sgn * n, y, u)


def wbox(name, axis, face, sgn, u0, u1, y0, y1, n0, n1, mat, bevel=0.0, seg=1):
    a, b = _P(axis, face, sgn, u0, y0, n0), _P(axis, face, sgn, u1, y1, n1)
    mn = tuple(min(a[i], b[i]) for i in range(3))
    mx = tuple(max(a[i], b[i]) for i in range(3))
    return gbox(name, mn, mx, mat, bevel=bevel, seg=seg)


def arch_cut(targets, axis, cu, w, y0, ysp, zmin, zmax):
    """Boolean-cut a round-headed opening (width w centred at u = cu, from y0 to the spring line ysp, plus a half circle on top)
    through the wall slab [zmin, zmax] (the extent along the wall normal) from each target object."""
    for t in targets:
        if axis == "z":
            c1 = gbox("cut_a", (cu - w / 2, y0, zmin), (cu + w / 2, ysp, zmax), "M_Concrete", bevel=0.0)
            c2 = gcyl("cut_b", w / 2, zmax - zmin, (cu, ysp, zmin), axis="z", verts=20, mat="M_Concrete", bevel=0.0)
        else:
            c1 = gbox("cut_a", (zmin, y0, cu - w / 2), (zmax, ysp, cu + w / 2), "M_Concrete", bevel=0.0)
            c2 = gcyl("cut_b", w / 2, zmax - zmin, (zmin, ysp, cu), axis="x", verts=20, mat="M_Concrete", bevel=0.0)
        M.boolean(t, c1)
        M.boolean(t, c2)


def arch_frame(prefix, axis, face, sgn, cu, w, y0, ysp, mat="M_Wood_Panel", bar=0.07, depth=0.07, muntins=True, mun_mat=None, glass=True, n0=-0.02):
    """Frame of a round-headed window whose opening is the arch_cut above: sill, jambs, arched head band, muntins, glass quad.
    Returns objs. Sits just inside the wall face (n0 .. n0 + depth into the room)."""
    o = []
    r = w / 2
    o.append(wbox(prefix + "sill", axis, face, sgn, cu - r - 0.07, cu + r + 0.07, y0 - 0.05, y0 + 0.015, n0, n0 + depth + 0.07, mat, bevel=0.004))
    o.append(wbox(prefix + "jamb_a", axis, face, sgn, cu - r, cu - r + bar, y0 + 0.015, ysp, n0, n0 + depth, mat, bevel=0.003))
    o.append(wbox(prefix + "jamb_b", axis, face, sgn, cu + r - bar, cu + r, y0 + 0.015, ysp, n0, n0 + depth, mat, bevel=0.003))
    # arched head band (annulus half) as an extruded polygon in the wall plane
    n = 12
    ro, ri = r + 0.0, r - bar
    outer = [(math.cos(math.pi * i / n) * ro, math.sin(math.pi * i / n) * ro) for i in range(n + 1)]
    inner = [(math.cos(math.pi * i / n) * ri, math.sin(math.pi * i / n) * ri) for i in range(n + 1)]
    ex = (sgn, 0, 0) if axis == "z" else (0, 0, -sgn)
    mtx = X.C.gframe(_P(axis, face, sgn, cu, ysp, n0), ex, (0, 1, 0))
    o.append(X.gpoly(prefix + "head", outer + list(reversed(inner)), depth, mtx, mat=mat, bevel=0.0))
    if muntins:
        mm = mun_mat or mat
        o.append(wbox(prefix + "transom", axis, face, sgn, cu - ri, cu + ri, ysp - 0.025, ysp + 0.025, n0 + 0.01, n0 + 0.05, mm))
        o.append(wbox(prefix + "mull", axis, face, sgn, cu - 0.015, cu + 0.015, y0 + 0.015, ysp + ri, n0 + 0.01, n0 + 0.05, mm))
        mid = (y0 + ysp) / 2
        o.append(wbox(prefix + "bar", axis, face, sgn, cu - ri, cu + ri, mid - 0.015, mid + 0.015, n0 + 0.01, n0 + 0.05, mm))
    if glass:
        a = _P(axis, face, sgn, cu, (y0 + ysp) / 2 + 0.05, n0 + 0.03)
        gu, gv = ((sgn, 0, 0) if axis == "z" else (0, 0, -sgn)), (0, 1, 0)
        g = X.C.gquad(prefix + "glass", a, gu, gv, w - 0.02, (ysp - y0) + r * 0.9, "M_Glass")
        o.append(g)
    return o


def sky_card(prefix, axis, face, sgn, cu, w, y0, ysp, dist=0.35, mat="M_Emissive_Table"):
    """A bright card outside a window (the daylight seen through it), facing into the room."""
    a = _P(axis, face, sgn, cu, (y0 + ysp) / 2 + w * 0.2, -dist)
    gu, gv = ((sgn, 0, 0) if axis == "z" else (0, 0, -sgn)), (0, 1, 0)
    return X.C.gquad(prefix + "sky", a, gu, gv, w + 0.9, (ysp - y0) + w * 0.9 + 0.5, mat)


def wall_bookcase(prefix, axis, face, sgn, u0, u1, depth, height, seed=1, shelf_step=0.36, glass_front=False, mat="M_Wood_Mahogany"):
    """Bookcase against a wall (any of the four): u0..u1 along the wall, `depth` into the room, `height` tall; rows of books on every shelf.
    glass_front adds a brass-framed glass door pane per bay (static)."""
    import random
    rnd = random.Random(seed)
    th = 0.03
    o = []
    o.append(wbox(prefix + "back", axis, face, sgn, u0, u1, 0.05, height, 0.0, 0.02, "M_Wood_Panel"))
    for u in (u0, u1 - th):
        o.append(wbox(prefix + "side", axis, face, sgn, u, u + th, 0.0, height, 0.0, depth, mat, bevel=0.004))
    o.append(wbox(prefix + "top", axis, face, sgn, u0 - 0.03, u1 + 0.03, height, height + 0.06, 0.0, depth + 0.04, mat, bevel=0.006, seg=2))
    o.append(wbox(prefix + "base", axis, face, sgn, u0, u1, 0.0, 0.16, 0.0, depth + 0.02, mat, bevel=0.004))
    n = max(2, int((height - 0.2) / shelf_step))
    mats = ["M_Book_Brown", "M_Book_Green", "M_Book_Red", "M_Book_Black", "M_Book_Blue", "M_Book_Gold", "M_Leather"]
    for i in range(n):
        y = 0.16 + i * (height - 0.2) / n
        o.append(wbox(prefix + f"shelf{i}", axis, face, sgn, u0, u1, y, y + 0.025, 0.0, depth, mat, bevel=0.002))
        u = u0 + th + 0.01
        books = []
        k = 0
        while u < u1 - th - 0.04:
            w = min(rnd.uniform(0.025, 0.055), u1 - th - u - 0.005)
            h = rnd.uniform(0.19, shelf_step - 0.04)
            books.append(wbox(f"{prefix}b{i}_{k}", axis, face, sgn, u, u + w * 0.96, y + 0.025, y + 0.025 + h, 0.05, depth * 0.78, rnd.choice(mats), bevel=0.0015))
            u += w
            k += 1
            if rnd.random() < 0.05:
                u += rnd.uniform(0.04, 0.10)
        if books:
            o.append(M.join(books, f"{prefix}row{i}"))
    if glass_front:
        bays = max(1, int(round((u1 - u0) / 0.8)))
        w = (u1 - u0) / bays
        for b in range(bays):
            a, c = u0 + b * w, u0 + (b + 1) * w
            o.append(wbox(prefix + "mull", axis, face, sgn, c - 0.015, c + 0.015, 0.16, height, depth - 0.01, depth + 0.02, mat, bevel=0.002))
            o.append(wbox(prefix + "gl", axis, face, sgn, a + 0.03, c - 0.03, 0.2, height - 0.04, depth + 0.002, depth + 0.006, "M_Glass"))
            o.append(wbox(prefix + "knob", axis, face, sgn, c - 0.05, c - 0.035, height * 0.5 - 0.04, height * 0.5 + 0.04, depth + 0.01, depth + 0.03, "M_Brass_Aged", bevel=0.004))
    return o
