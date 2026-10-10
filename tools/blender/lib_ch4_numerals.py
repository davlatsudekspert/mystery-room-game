"""MYSTERY ROOM — Chapter 4 shared numerals (docs/models/ch4.md, shared_numerals).

ONE definition of the Roman numerals I II III IV V (a blocky, bold, serifed Soviet face) and the digits 0-9, used by
every Chapter 4 model so a numeral looks the same everywhere.

Geometry (pure math, no bpy at import):
    roman_shapes(n, h) -> list of closed CCW outlines [(x, y), ...] (+y up) centred on the glyph's bounding box,
                          h tall; n in 1..5. Shapes never overlap, so they also fill with the even-odd rule.
    roman_width(n, h)  -> glyph width.
Blender helpers (bpy imported lazily):
    roman_obj(name, n, h, depth=0.0, mat=...)  flat (depth 0) or extruded numeral in local XY facing +Z
    digit_obj(name, d, h, depth=0.0, mat=...)  a digit (DejaVu Sans Bold, low-poly) in local XY facing +Z
"""
from __future__ import annotations

import math

STROKE = 0.17      # stem width / height
SERIF_W = 0.36     # I glyph width / height (serif tip to tip)
SERIF_T = 0.075    # serif thickness / height
GAP = 0.10         # gap between glyphs / height


def _i_shape(h: float, cx: float = 0.0):
    w, s, t = STROKE * h / 2.0, SERIF_W * h / 2.0, SERIF_T * h
    y0, y1 = -h / 2.0, h / 2.0
    pts = [(-s, y0), (s, y0), (s, y0 + t), (w, y0 + t), (w, y1 - t), (s, y1 - t), (s, y1), (-s, y1),
           (-s, y1 - t), (-w, y1 - t), (-w, y0 + t), (-s, y0 + t)]
    return [(x + cx, y) for (x, y) in pts]


def _v_shape(h: float, cx: float = 0.0):
    """A solid V with a flat tip, constant arm thickness, small top serifs."""
    big_x = 0.40 * h                      # outer half width at the top
    top, bot = h / 2.0, -h / 2.0
    b = 0.5 * STROKE * h * 0.5            # half width of the flat tip
    u = 1.25 * STROKE * h                 # horizontal width of an arm
    slope = (big_x - b) / h               # outer edge: x grows by `slope` per unit y
    inner_x_top = big_x - u
    m_y = top - inner_x_top / slope       # where the inner edges meet on the axis
    pts = [(-big_x, top), (-b, bot), (b, bot), (big_x, top), (big_x - u, top), (0.0, m_y), (-(big_x - u), top)]
    return [(x + cx, y) for (x, y) in pts]


def roman_width(n: int, h: float) -> float:
    iw = SERIF_W * h
    vw = 0.80 * h
    gap = GAP * h
    if n in (1, 2, 3):
        return n * iw + (n - 1) * gap
    if n == 4:
        return iw + gap + vw
    return vw


def roman_shapes(n: int, h: float):
    """Closed CCW outlines of the Roman numeral n (1..5), centred on the bounding box."""
    iw, vw, gap = SERIF_W * h, 0.80 * h, GAP * h
    total = roman_width(n, h)
    x0 = -total / 2.0
    out = []
    if n in (1, 2, 3):
        for k in range(n):
            out.append(_i_shape(h, x0 + iw / 2.0 + k * (iw + gap)))
    elif n == 4:
        out.append(_i_shape(h, x0 + iw / 2.0))
        out.append(_v_shape(h, x0 + iw + gap + vw / 2.0))
    elif n == 5:
        out.append(_v_shape(h, 0.0))
    else:
        raise ValueError(n)
    return out


def _ccw(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return pts if a > 0 else list(reversed(pts))


def roman_obj(name: str, n: int, h: float, depth: float = 0.0, mat: str = "M_Brass_Aged", loc=(0.0, 0.0, 0.0),
              bevel: float = 0.0006):
    """A Roman numeral as one object in local XY facing +Z (flat when depth == 0, else extruded z 0..depth)."""
    import lib_mech as L
    import mrlib as M
    shapes = [_ccw(s) for s in roman_shapes(n, h)]
    if depth <= 0.0:
        o = L.flat_shape(name, shapes, mat=mat)
        o.location = loc
        return o
    objs = []
    for k, s in enumerate(shapes):
        o = L.curve_solid(f"{name}_{k}", [s], depth, bevel=bevel, bevel_res=0, mat=mat, drop_bottom=True)
        objs.append(o)
    o = M.join(objs, name) if len(objs) > 1 else objs[0]
    o.name = name
    o.data.name = name
    o.location = loc
    return o


def digit_obj(name: str, d: int, h: float, depth: float = 0.0, mat: str = "M_Brass_Aged", loc=(0.0, 0.0, 0.0), res: int = 2):
    """A digit 0..9 (DejaVu Sans Bold, low-poly) centred on its glyph bounds, h tall, local XY facing +Z."""
    import lib_mech as L
    import lib_ch2_vault as V
    o = V.text(name, str(d), h / 0.72, (0.0, 0.0), 0.0, font=V.FONT_SANS_B, mat=mat, depth=depth, res=res)
    o.location = loc
    return o
