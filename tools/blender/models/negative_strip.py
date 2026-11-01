"""negative_strip.glb — a strip of four photographic negatives from the Plate Room (R6, puzzle N9). Four instances are used (strip 0..3).

A 35 mm style film strip (0.200 x 0.045 m, much larger than real for readability): a tapered leader tab at -X, sprocket holes along
both edges (decal), four inverted frames and an edge symbol window at the +X end (the symbol the cabinet label is matched with).
The decal quad `strip_frames` uses slot M_Decal_Negatives (UV 0..1 over the whole strip, placeholder image: sprockets, four inverted
frames, edge symbol); the scene swaps the image per strip (the symbol window is the right-most 6 percent of the width).

Model space (Godot): lies flat, broad faces +-Y, strip along X, the leader tab at -X, origin at the centre of mass, thickness 1.2 mm.
Parts: strip_body (film base, M_Film), strip_frames (decal quad on the top face, y +0.0007).
    blender -b --factory-startup -P tools/blender/models/negative_strip.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import gquad, gpoly, part  # noqa: E402

NAME = "negative_strip"
BUDGET = 400
ARGS = M.main_guard()
L, W, T = 0.200, 0.045, 0.0012


def build():
    X.begin()
    # outline in the Godot XZ plane, extruded along +Y: gframe(origin, ex, ey) with ex = +X, ey = -Z -> local z = ex x ey = -Y ... use ey = +Z? choose
    # ex=(1,0,0), ey=(0,0,-1) so local z = ex x ey = (0,1,0) = +Y.
    mtx = X.C.gframe((0.0, -T / 2, 0.0), (1, 0, 0), (0, 0, -1))
    pts = [(-L / 2 - 0.022, -W * 0.18), (-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2), (-L / 2 - 0.022, W * 0.18)]
    body = gpoly("strip_body", pts, T, mtx, mat="M_Film", bevel=0.0)
    X.decal("M_Decal_Negatives", "negatives.png")
    q = gquad("strip_frames", (0.0, T / 2 + 0.0004, 0.0), (1, 0, 0), (0, 0, -1), L, W, "M_Decal_Negatives")
    part("strip_body", [body], (0, 0, 0), presmooth=False)
    part("strip_frames", [q], (0.0, T / 2, 0.0), presmooth=False)


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["strip_body", "strip_frames"], [], BUDGET, {}, show=["strip_body", "strip_frames"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 0.32, 0.22), (0.0, 0.0, 0.0), 40)], floor=True, world=0.3, samples=16)
