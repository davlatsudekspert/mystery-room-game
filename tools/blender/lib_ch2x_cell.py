"""MYSTERY ROOM — extra helpers for the Night Cell group (R3) and the hall additions of the Chapter 2 expansion.

On top of lib_ch2x (never edits it):
  * slots of this group registered for the preview (M_Decal_TableMask, ...)
  * gsphere(...)     squashed / stretched ellipsoid in Godot axes (pillows, cushions, lamp globes)
  * drape(...)       a thick cloth (blanket, throw) swept along X over a (z, y) cross-section with soft folds
  * mug(...) / jar(...) / book(...)   small dressing used by the cell, the kettle shelf and the desk
  * wall_quad(...)   a decal quad on a wall at a Godot position facing a Godot axis
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
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402,F401

M.PREVIEW.setdefault("M_Decal_TableMask", ("DCCFB2", 0.8, 0.0, None, 1.0))
M.PREVIEW.setdefault("M_Decal_Sheet", ("DCCFB2", 0.8, 0.0, None, 1.0))
M.PREVIEW.setdefault("M_Decal_CellDrawing", ("DCCFB2", 0.8, 0.0, None, 1.0))
M.PREVIEW.setdefault("M_Decal_FloorPlan", ("DCCFB2", 0.8, 0.0, None, 1.0))


def gsphere(name, r, centre, scale=(1.0, 1.0, 1.0), mat="M_Linen", segs=14, rings=8, smooth=80.0):
    """Ellipsoid with the semi-axes r*scale (Godot axes) at the Godot point `centre`."""
    s = scale
    o = M.sphere(name, r, loc=(0, 0, 0), segments=segs, rings=rings, mat=mat, scale=(s[0], s[2], s[1]))
    A.place(o, Matrix.Identity(4))
    o.data.transform(Matrix.Translation(GV(centre)))
    return A.hint(o, smooth)


def drape(name, xs, section, thick=0.012, mat="M_Wool_Knit", folds=0.0, seed=0.0):
    """Cloth swept along Godot X. `section(x)` returns the top-surface cross-section as [(z, y), ...] in Godot axes
    (ordered along the cloth, e.g. from the far edge over the top to the hanging edge). The cloth is `thick` thick
    (offset along the local normal); `folds` adds a slow ripple (metres) along x. Closed solid, UVs by finalize_uv."""
    bm = bmesh.new()
    rows_top, rows_bot = [], []
    for xi in xs:
        pts = section(xi)
        n = len(pts)
        tops, bots = [], []
        for j, (z, y) in enumerate(pts):
            dy = folds * math.sin(xi * 17.0 + seed + j * 0.9) * (0.4 + 0.6 * math.sin(j * 1.3 + seed))
            z0 = pts[max(j - 1, 0)]
            z1 = pts[min(j + 1, n - 1)]
            tz, ty = z1[0] - z0[0], z1[1] - z0[1]
            ln = math.hypot(tz, ty) or 1.0
            nz, ny = -ty / ln, tz / ln              # normal in the (z, y) plane, up-facing for increasing z
            if ny < 0:
                nz, ny = -nz, -ny
            tops.append(bm.verts.new(G(xi, y + dy, z)))
            bots.append(bm.verts.new(G(xi, y + dy - ny * thick, z - nz * thick)))
        rows_top.append(tops)
        rows_bot.append(bots)
    nx, nz_ = len(xs), len(rows_top[0])
    for i in range(nx - 1):
        for j in range(nz_ - 1):
            bm.faces.new((rows_top[i][j], rows_top[i + 1][j], rows_top[i + 1][j + 1], rows_top[i][j + 1]))
            bm.faces.new((rows_bot[i][j + 1], rows_bot[i + 1][j + 1], rows_bot[i + 1][j], rows_bot[i][j]))
        bm.faces.new((rows_top[i][0], rows_bot[i][0], rows_bot[i + 1][0], rows_top[i + 1][0]))
        bm.faces.new((rows_top[i + 1][-1], rows_bot[i + 1][-1], rows_bot[i][-1], rows_top[i][-1]))
    for j in range(nz_ - 1):
        bm.faces.new((rows_top[0][j], rows_top[0][j + 1], rows_bot[0][j + 1], rows_bot[0][j]))
        bm.faces.new((rows_top[-1][j + 1], rows_top[-1][j], rows_bot[-1][j], rows_bot[-1][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return A.obj_from_bm(name, bm, mat)


def mug(name, cx, y, cz, r=0.040, h=0.085, mat="M_Enamel_Cream", rim="M_Enamel_Crimson", handle_dir=1.0):
    """Enamel mug standing at (cx, y, cz) with a coloured rim band and a handle toward +X (handle_dir)."""
    o = [glathe(name + "_b", [(0.0, 0.0), (r * 0.86, 0.0), (r, 0.006), (r, h - 0.004), (r - 0.003, h), (r - 0.007, h - 0.004), (r - 0.007, 0.012),
                              (0.0, 0.010)], (cx, y, cz), axis="y", segments=16, mat=mat),
         glathe(name + "_r", [(r + 0.0008, h - 0.014), (r + 0.0008, h - 0.001), (r - 0.003, h + 0.0005), (r - 0.003, h - 0.014)], (cx, y, cz),
                axis="y", segments=16, mat=rim)]
    hx = cx + handle_dir * (r + 0.012)
    o.append(gbox(name + "_h", (hx - 0.012, y + h * 0.28, cz - 0.006), (hx + 0.012, y + h * 0.78, cz + 0.006), mat, bevel=0.003))
    return o


def jar(name, cx, y, cz, r=0.034, h=0.10, glass="M_Glass_Amber", lid="M_Brass_Aged", fill=None):
    o = [glathe(name + "_g", [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.006), (r, h - 0.012), (r * 0.7, h - 0.004), (r * 0.62, h), (0.0, h)], (cx, y, cz),
                axis="y", segments=14, mat=glass),
         glathe(name + "_l", [(0.0, h), (r * 0.66, h), (r * 0.66, h + 0.014), (0.0, h + 0.014)], (cx, y, cz), axis="y", segments=14, mat=lid)]
    if fill:
        o.append(glathe(name + "_f", [(0.0, 0.004), (r * 0.8, 0.004), (r * 0.8, h * 0.6), (0.0, h * 0.6)], (cx, y, cz), axis="y", segments=12,
                        mat=fill))
    return o


def book(name, x0, x1, y0, z0, z1, h, mat="M_Book_Brown", spine_z=None):
    """Book lying with its spine along Z at x0 side (a box with cream page block and a darker cover)."""
    cover = gbox(name + "_c", (x0, y0, z0), (x1, y0 + h, z1), mat, bevel=0.002)
    pages = gbox(name + "_p", (x0 + 0.006, y0 + 0.003, z0 + 0.003), (x1 + 0.002, y0 + h - 0.003, z1 - 0.003), "M_Paper", bevel=0.0)
    return [cover, pages]


def book_row(prefix, x, y0, z0, widths, h, mats, depth=0.20, lean=0.0):
    """Row of upright books along +X at shelf height y0, spine toward +Z. Returns objects."""
    out = []
    cur = x
    for i, w in enumerate(widths):
        hh = h * (0.85 + 0.15 * ((i * 7) % 5) / 4)
        out.append(gbox(f"{prefix}{i}", (cur, y0, z0), (cur + w, y0 + hh, z0 + depth), mats[i % len(mats)], bevel=0.002))
        out.append(gbox(f"{prefix}p{i}", (cur + 0.002, y0 + 0.004, z0 + 0.006), (cur + w - 0.002, y0 + hh - 0.004, z0 + depth - 0.012), "M_Paper",
                        bevel=0.0))
        cur += w + 0.001
    return out


def wall_quad(name, centre, normal_axis, w, h, mat, up_axis="y"):
    """Decal quad centred at `centre` facing the Godot axis `normal_axis` ('x','-x','z','-z'), UV 0..1, upright."""
    n = X.C.AXES[normal_axis]
    u = {"z": (1, 0, 0), "-z": (-1, 0, 0), "x": (0, 0, -1), "-x": (0, 0, 1)}[normal_axis]
    return gquad(name, centre, u, (0, 1, 0), w, h, mat)


def alpha_decal(slot: str, fname: str):
    """Decal material whose image alpha drives the preview transparency (the Godot .tres has `transparency = 1`)."""
    m = X.decal(slot, fname)
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    for nd in nt.nodes:
        if nd.type == "TEX_IMAGE" and bsdf is not None:
            nt.links.new(nd.outputs["Alpha"], bsdf.inputs["Alpha"])
            break
    try:
        m.blend_method = "BLEND"
    except Exception:
        pass
    return m
