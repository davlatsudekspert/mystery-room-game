"""MYSTERY ROOM — Chapter 4: the Institute's mark (a ring crossed by one meridian) as two separate solids.

`lib_ch3_symbols.loops("mark")` splits the glyph into touching pieces that Blender's curve filler mis-triangulates when they are extruded (half of the ring's hole came out filled), so every
Chapter 4 model that needs a RELIEF mark builds it with `mark_solids`: an annulus and a bar, each its own closed extrusion (they overlap where the bar crosses the ring). Zero-thickness
inlays can still use `lib_ch3_symbols.inlay`. Proportions are the glyph's (ring radius 0.384, band 0.032, meridian 0.030 wide, half length 0.484, in units of a 0.968 high glyph).
"""
from __future__ import annotations

import math
import os
import sys

from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_mech as L  # noqa: E402

RING_R, RING_W, BAR_W, BAR_HALF = 0.384, 0.032, 0.030, 0.484


def mark_solids(h: float, depth: float, mat: str, loc=(0.0, 0.0), z0: float = 0.0, n: int = 36, name: str = "mark", bold: float = 1.0):
    """The mark as [ring, bar] objects in local XY facing +Z, extruded z0 .. z0 + depth, centred on loc = (x, y); h = the glyph height (the meridian's length); bold > 1 thickens the ring and the bar (small reliefs read better)."""
    s = h / (2.0 * BAR_HALF)
    rw = RING_W * bold
    ro, ri = (RING_R + rw / 2.0) * s, (RING_R - rw / 2.0) * s
    ring = L.curve_solid(f"{name}_ring", [L.circle(ro, n), list(reversed(L.circle(ri, n)))], depth, bevel=0.0, bevel_res=0, mat=mat, drop_bottom=True)
    hw, half = BAR_W * bold / 2.0 * s, BAR_HALF * s
    bar = L.curve_solid(f"{name}_bar", [[(-hw, -half), (hw, -half), (hw, half), (-hw, half)]], depth, bevel=0.0, bevel_res=0, mat=mat, drop_bottom=True)
    out = []
    for o in (ring, bar):
        o.data.transform(Matrix.Translation((loc[0], loc[1], z0)))
        out.append(o)
    return out
