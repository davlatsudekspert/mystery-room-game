"""MYSTERY ROOM — Chapter 3 shared symbols and material slots (group A, docs/models/ch3.md §0, §12).

ONE definition of the seven Chapter 3 symbols, used by every 3D inlay (Blender) and by the decal generator
(tools/textures/make_decals_ch3.py, plain Python + PIL), so a symbol looks the same everywhere:

    sun ☼       a disc with 8 rays (one ray points straight up)
    moon ☾      the crescent of the Chapter 2 vault plate (vault_door.py sym_plate), OPENING TO THE RIGHT
    star ✦      the four-pointed star of the same plate (point up, inner radius 0.129 of the height)
    triangle ▲  equilateral, point up
    circle ●    a disc
    square ■    a square
    diamond ◆   a square turned 45° (equal diagonals)

Plus the two story marks (also shared, Chapter 2 proportions from make_decals_ch2.py):
    mark        Strand's mark / the Institute mark: a ring crossed by a vertical meridian (ticks=True adds the
                Chapter 1 emblem's ten ticks)
    sign        Leyla's sign: a crescent opening to the right with three dots in a vertical row in its opening

Geometry convention (pure math, no bpy at import):
    shapes(kind, h)  -> list of SHAPES; a shape is [outer_loop, *hole_loops]; loops are lists of (x, y) with
                        +y UP, counter-clockwise outer loops, centred on the symbol's bounding box (the box is
                        h tall). Shapes never overlap each other, so all loops together also fill correctly
                        with the even-odd rule (Blender 2D curves, lib_mech.curve_solid / flat_shape).
    loops(kind, h)   -> the flat list of every loop (for even-odd fills).
    bounds(kind, h)  -> (xmin, ymin, xmax, ymax).

Decals (§12): sym_<name>.png, 512² RGBA, white on transparent, symbol height 0.80 of the image.
Drum order (UndergroundLogic.DRUM_SYMBOLS): 0 sun, 1 moon, 2 star, 3 triangle, 4 circle, 5 square.

Blender helpers (import bpy lazily, only when called from a Blender script):
    inlay(name, kind, h, depth=0.0, mat=..., bevel=...)   flat (depth 0) or extruded symbol in local XY facing +Z
    ensure_materials()                                      every new Chapter 3 slot with its preview colour (+ the
                                                            procedural texture sets / decal images when they exist)
New Chapter 3 slots (§0): M_Tile_Glazed, M_Rock, M_Chequer, M_Porcelain, M_Shader_Quad and the §12 M_Decal_* slots.
Their preview values are injected into mrlib.PREVIEW on import (mrlib itself is not edited), so
M.material("M_Rock") already gets the right preview colour once this module is imported.
"""
from __future__ import annotations

import math
import os

TAU = 2.0 * math.pi
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "game", "assets", "textures")
DECALS3 = os.path.join(TEX, "decals", "ch3")

NAMES = ("sun", "moon", "star", "triangle", "circle", "square", "diamond")
DRUM_ORDER = ("sun", "moon", "star", "triangle", "circle", "square")       # DRUM_SYMBOLS 0..5
KEY_SHAPES = ("diamond", "triangle", "circle", "square")                     # the four isolator keys
GLYPH = {"sun": "☼", "moon": "☾", "star": "✦", "triangle": "▲", "circle": "●", "square": "■", "diamond": "◆"}
DECAL_FILE = {k: f"sym_{k}.png" for k in NAMES}
DECAL_SLOT = {k: f"M_Decal_Sym_{k.capitalize()}" for k in NAMES}

# ---- vault_door.py sym_plate() proportions (story anchors from Chapter 2) -----------------------------
_STAR_R_OUT, _STAR_R_IN = 0.029, 0.0075                    # four-pointed star, point up
_MOON_R, _MOON_r, _MOON_d = 0.028, 0.0235, 0.0125          # outer circle, inner circle, inner centre shift (+x)

# ---- sun proportions (fractions of the height) ------------------------------------------------------
SUN_DISC = 0.255          # disc radius
SUN_RAY_R0 = 0.325        # ray base radius (a clear gap to the disc)
SUN_RAY_R1 = 0.500        # ray tip radius
SUN_RAY_W0 = 0.085        # ray half-width at the base
SUN_RAY_W1 = 0.022        # ray half-width at the (blunt) tip

# ---- Chapter 2 mark / sign (unit glyph box, make_decals_ch2.py) ------------------------------------
MARK_RING_R, MARK_RING_W = 0.384, 0.032
MARK_MERIDIAN_W, MARK_MERIDIAN_HALF = 0.030, 0.484
MARK_TICK = (0.432, 0.478, 0.022)
SIGN_R, SIGN_T, SIGN_PHI = 0.40, 0.112, 50.0
SIGN_DOT_R, SIGN_DOT_DY, SIGN_DOT_DX = 0.043, 0.165, 0.045


# ====================================================================== 2D helpers
def _circle(r, n, cx=0.0, cy=0.0, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n)) for i in range(n)]


def _arc(r, a0, a1, n, cx=0.0, cy=0.0):
    """n + 1 points from angle a0 to a1 (radians, inclusive)."""
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _area(loop):
    a = 0.0
    for i in range(len(loop)):
        x0, y0 = loop[i]
        x1, y1 = loop[(i + 1) % len(loop)]
        a += x0 * y1 - x1 * y0
    return a / 2


def _ccw(loop):
    return list(loop) if _area(loop) > 0 else list(reversed(loop))


def _cw(loop):
    return list(reversed(_ccw(loop)))


def _map(shapes_, fn):
    return [[[fn(x, y) for (x, y) in loop] for loop in shape] for shape in shapes_]


def _bounds_of(shapes_):
    xs = [p[0] for s in shapes_ for lp in s for p in lp]
    ys = [p[1] for s in shapes_ for lp in s for p in lp]
    return min(xs), min(ys), max(xs), max(ys)


def _centre(shapes_):
    x0, y0, x1, y1 = _bounds_of(shapes_)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return _map(shapes_, lambda x, y: (x - cx, y - cy))


def _scale_to_height(shapes_, h):
    x0, y0, x1, y1 = _bounds_of(shapes_)
    s = h / (y1 - y0)
    return _map(shapes_, lambda x, y: (x * s, y * s))


# ====================================================================== the seven symbols (unit height)
def _star(n_pts=4):
    pts = []
    for i in range(2 * n_pts):
        a = math.pi / 2 + i * math.pi / n_pts
        r = 0.5 if i % 2 == 0 else 0.5 * _STAR_R_IN / _STAR_R_OUT
        pts.append((r * math.cos(a), r * math.sin(a)))
    return [[_ccw(pts)]]


def _moon(n_out=36, n_in=28):
    """sym_plate's crescent: disc R minus disc r centred d to the right -> horns point right."""
    k = 0.5 / _MOON_R
    R, r, d = _MOON_R * k, _MOON_r * k, _MOON_d * k
    xi = (R * R - r * r + d * d) / (2 * d)
    a0 = math.atan2(math.sqrt(R * R - xi * xi), xi)          # upper horn on the outer circle
    b0 = math.atan2(math.sqrt(R * R - xi * xi), xi - d)       # the same point seen from the inner centre
    outer = _arc(R, a0, TAU - a0, n_out)                      # top horn -> left -> bottom horn (CCW)
    inner = _arc(r, -b0, -(TAU - b0), n_in, cx=d)[1:-1]       # bottom horn -> left -> top horn (CW)
    return [[_ccw(outer + inner)]]


def _sun(n_disc=40):
    out = [[_ccw(_circle(SUN_DISC, n_disc))]]
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca                                       # tangent
        p = [(SUN_RAY_R0 * ca + SUN_RAY_W0 * tx, SUN_RAY_R0 * sa + SUN_RAY_W0 * ty),
             (SUN_RAY_R0 * ca - SUN_RAY_W0 * tx, SUN_RAY_R0 * sa - SUN_RAY_W0 * ty),
             (SUN_RAY_R1 * ca - SUN_RAY_W1 * tx, SUN_RAY_R1 * sa - SUN_RAY_W1 * ty),
             (SUN_RAY_R1 * ca + SUN_RAY_W1 * tx, SUN_RAY_R1 * sa + SUN_RAY_W1 * ty)]
        out.append([_ccw(p)])
    return out


def _triangle():
    s = 1.0 / math.sqrt(3.0)                                  # half side for height 1
    return [[_ccw([(0.0, 0.5), (-s, -0.5), (s, -0.5)])]]


def _circle_shape(n=48):
    return [[_ccw(_circle(0.5, n))]]


def _square():
    return [[_ccw([(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)])]]


def _diamond():
    return [[_ccw([(0.0, 0.5), (-0.5, 0.0), (0.0, -0.5), (0.5, 0.0)])]]


def _mark(ticks=False, n=48):
    """Ring + meridian (unit glyph box), split into non-overlapping pieces."""
    ro, ri = MARK_RING_R + MARK_RING_W / 2, MARK_RING_R - MARK_RING_W / 2
    hw, half = MARK_MERIDIAN_W / 2, MARK_MERIDIAN_HALF
    out = [[_ccw(_circle(ro, n, phase=math.pi / 2)), _cw(_circle(ri, n, phase=math.pi / 2))]]
    do, di = math.asin(hw / ro), math.asin(hw / ri)
    # top piece: from the outer circle up to the end of the meridian
    top = [(hw, half), (-hw, half)] + _arc(ro, math.pi / 2 + do, math.pi / 2 - do, 2)
    bot = [(-hw, -half), (hw, -half)] + _arc(ro, -math.pi / 2 + do, -math.pi / 2 - do, 2)
    mid = _arc(ri, math.pi / 2 - di, math.pi / 2 + di, 2) + _arc(ri, -math.pi / 2 - di, -math.pi / 2 + di, 2)
    out += [[_ccw(top)], [_ccw(bot)], [_ccw(mid)]]
    if ticks:
        r0, r1, tw = MARK_TICK
        for k in range(12):
            if k in (3, 9):                 # 12 and 6 o'clock are the meridian
                continue
            a = TAU * k / 12
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa * tw / 2, ca * tw / 2
            out.append([_ccw([(r0 * ca + tx, r0 * sa + ty), (r0 * ca - tx, r0 * sa - ty),
                              (r1 * ca - tx, r1 * sa - ty), (r1 * ca + tx, r1 * sa + ty)])])
    return out


def _sign(n_out=40, n_in=30, n_dot=16):
    R, t, phi = SIGN_R, SIGN_T, math.radians(SIGN_PHI)
    d = (t * t - 2 * R * t) / (2 * t - 2 * R * (1 + math.cos(phi)))
    r2 = R + d - t
    horn = R * math.cos(phi)
    right = max(horn, SIGN_DOT_DX + SIGN_DOT_R)
    a = -(-R + right) / 2.0
    outer = _arc(R, phi, TAU - phi, n_out, cx=a)
    hx, hy = R * math.cos(phi) - d, R * math.sin(phi)          # top horn seen from the inner centre
    b = math.atan2(hy, hx)
    inner = _arc(r2, -b, -(TAU - b), n_in, cx=a + d)[1:-1]
    out = [[_ccw(outer + inner)]]
    for k in (-1, 0, 1):
        out.append([_ccw(_circle(SIGN_DOT_R, n_dot, cx=a + SIGN_DOT_DX, cy=k * SIGN_DOT_DY))])
    return out


_BUILDERS = {"sun": _sun, "moon": _moon, "star": _star, "triangle": _triangle, "circle": _circle_shape,
             "square": _square, "diamond": _diamond, "mark": lambda: _mark(False), "mark_ticks": lambda: _mark(True),
             "sign": _sign}


def shapes(kind: str, h: float = 1.0):
    """Symbol `kind` as non-overlapping filled shapes [[outer, *holes], ...], bounding box centred on (0, 0),
    height h (+y up). kind: one of NAMES, or 'mark', 'mark_ticks', 'sign'."""
    if kind not in _BUILDERS:
        raise KeyError(f"unknown symbol {kind!r}; known: {sorted(_BUILDERS)}")
    return _scale_to_height(_centre(_BUILDERS[kind]()), h)


def loops(kind: str, h: float = 1.0):
    return [lp for s in shapes(kind, h) for lp in s]


def bounds(kind: str, h: float = 1.0):
    return _bounds_of(shapes(kind, h))


def ring_icon(i: int, d: float, line: float = 0.06, bold: float = 0.16, n: int = 40):
    """The drum lock's ring icon (§3 blast_door): four concentric circles (i = 0 outer ... 3 inner) of outer
    diameter d, circle i drawn bold. Returns shapes (each a ring [outer, hole])."""
    out = []
    radii = [0.5 - 0.125 * k for k in range(4)]               # 0.5, 0.375, 0.25, 0.125 of d
    for k, r in enumerate(radii):
        w = (bold if k == i else line) * 0.5                   # stroke as a fraction of d
        ro, ri = (r * d), max((r - w) * d, 0.0)
        if ri <= 1e-6:
            out.append([_ccw(_circle(ro, n))])
        else:
            out.append([_ccw(_circle(ro, n)), _cw(_circle(ri, n))])
    return out


# ====================================================================== material slots (§0, §12)
# name: (preview sRGB hex, roughness, metallic, alpha, texture folder or decal file or None, texture repeat m)
SLOTS = {
    "M_Tile_Glazed": ("D9D6CB", 0.25, 0.0, 1.0, "tile_glazed", 0.6),
    "M_Rock": ("2B2926", 0.85, 0.0, 1.0, "rock", 2.4),
    "M_Chequer": ("5E605B", 0.45, 0.85, 1.0, "chequer", 0.30),
    "M_Porcelain": ("5A3320", 0.15, 0.0, 1.0, None, 1.0),
    "M_Shader_Quad": ("1A1F1E", 0.3, 0.0, 1.0, None, 1.0),
    "M_Decal_InterlockPlate": ("E6DDC6", 0.3, 0.0, 1.0, "decals/ch3/interlock_plate.png", 1.0),
    "M_Decal_EcgPaper": ("E7B7A6", 0.85, 0.0, 1.0, "decals/ch3/ecg_paper.png", 1.0),
    "M_Decal_GrowthLog": ("DCD2BC", 0.85, 0.0, 1.0, "decals/ch3/growth_log.png", 1.0),
    "M_Decal_StrandNote": ("DCD0B4", 0.85, 0.0, 1.0, "decals/ch3/strand_note.png", 1.0),
    "M_Decal_StaffPhoto": ("8C8478", 0.3, 0.0, 1.0, "decals/ch2/film_frame_2.jpg", 1.0),
}
for _k in NAMES:
    SLOTS[DECAL_SLOT[_k]] = ("F2EEE4", 0.4, 0.0, 1.0, "decals/ch3/" + DECAL_FILE[_k], 1.0)
# Library slots mrlib.PREVIEW does not know (values from their .tres) that Chapter 3 models use.
LIBRARY_EXTRA = {
    "M_Glass_Dark": ("0C0F10", 0.06, 0.0, 1.0),
    "M_Enamel_Amber": ("C98A1E", 0.28, 0.0, 1.0),
    "M_Enamel_Green": ("2F7A3A", 0.28, 0.0, 1.0),
    "M_Enamel_White": ("E8E2D4", 0.28, 0.0, 1.0),
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),
    "M_Felt": ("3A3A3A", 1.0, 0.0, 1.0),
}


def _register_preview() -> None:
    try:
        import mrlib as M  # noqa: WPS433 (Blender only)
    except Exception:   # plain Python (decal generator): nothing to register
        return
    for name, (col, rough, metal, alpha, *_rest) in SLOTS.items():
        M.PREVIEW.setdefault(name, (col, rough, metal, None, alpha))
    for name, (col, rough, metal, alpha) in LIBRARY_EXTRA.items():
        M.PREVIEW.setdefault(name, (col, rough, metal, None, alpha))


try:
    import bpy  # noqa: F401
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    _register_preview()
except ImportError:
    pass


def _scaled_pbr(mat, folder: str, tile_m: float) -> None:
    """Hook a texture set (albedo/normal/orm) to a material with a 1 / tile_m mapping (world-scale UVs)."""
    import mrlib as M
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    M._attach_pbr(nt, bsdf, folder)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile_m, 1.0 / tile_m, 1.0)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    for nd in nt.nodes:
        if nd.type == "TEX_IMAGE":
            nt.links.new(mp.outputs["Vector"], nd.inputs["Vector"])


def ensure_materials() -> None:
    """Create every new Chapter 3 slot (call after mrlib.reset_scene). Tiling slots get their procedural texture
    set with the right repeat once make_decals_ch3.py has written it; decal slots show their image when it
    exists. QA preview only: Godot uses game/assets/materials/<slot>.tres."""
    import bpy
    import mrlib as M
    _register_preview()
    for name, (col, rough, metal, alpha, src, tile) in SLOTS.items():
        if bpy.data.materials.get(name) is not None:
            continue
        if src and not src.startswith("decals/"):
            folder = os.path.join(TEX, src)
            mat = M.material(name, color=col, rough=rough, metal=metal, alpha=alpha, image="")
            if os.path.isdir(folder) and os.path.exists(os.path.join(folder, "albedo.jpg")):
                _scaled_pbr(mat, folder, tile)
        elif src:
            path = os.path.join(TEX, src)
            M.material(name, color=col, rough=rough, metal=metal, alpha=alpha,
                       image=path if os.path.exists(path) else None)
        else:
            M.material(name, color=col, rough=rough, metal=metal, alpha=alpha)
    for name, (col, rough, metal, alpha) in LIBRARY_EXTRA.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=col, rough=rough, metal=metal, alpha=alpha)


# ====================================================================== Blender inlays
def inlay(name: str, kind: str, h: float, depth: float = 0.0, mat: str = "M_Brass_Aged", bevel: float = 0.0004,
          loc=(0.0, 0.0, 0.0), rot_z: float = 0.0):
    """Symbol `kind` (height h) in the local XY plane facing +Z: a zero-thickness inlay (depth 0) or a relief
    extruded from z = 0 to z = depth with a small bevel (bottom cap dropped). rot_z (radians) then loc."""
    import lib_mech as L
    from mathutils import Matrix
    lp = loops(kind, h)
    if depth <= 0.0:
        o = L.flat_shape(name, lp, mat=mat)
    else:
        o = L.curve_solid(name, lp, depth, bevel=min(bevel, depth * 0.4), bevel_res=0, mat=mat, drop_bottom=True)
    o.data.transform(Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z"))
    return o
