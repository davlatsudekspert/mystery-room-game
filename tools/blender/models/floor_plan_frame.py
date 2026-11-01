"""floor_plan_frame.glb — the framed floor plan on the hall wall (view `plan`; the same plan is the document item `floor_plan`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3 "The same plan hangs in the hall as a view `plan`"). A walnut picture frame with a stepped
profile holds the building plan (M_Decal_FloorPlan: three stacked floor strips, rooms as tiles, no text). Light by design
(hall draw calls are at their limit): two objects, two materials in total, about 0.6k triangles.

Model space (Godot): wall-mounted, front +Z. Origin on the floor (y = 0) at the centre of the BACK face, so it is placed on the wall plane
(position = wall point at x/z of the centre, yaw so that +Z points into the hall: east wall yaw -90, north wall 0, west wall 90, south wall 180).
The frame is 0.68 (x) x 0.48 (y) x 0.035 deep, centred at y = 1.55.

Parts:
  floor_plan_frame   the frame and the mount board (M_Wood_Walnut, merged)
  IA_floor_plan      the plan quad 0.59 x 0.37, centre (0, 1.55, 0.0195), M_Decal_FloorPlan, UV 0..1 (the tap target for the overlay)

    blender -b --factory-startup -P tools/blender/models/floor_plan_frame.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, gquad, part, mount  # noqa: E402

NAME = "floor_plan_frame"
BUDGET = 900
ARGS = M.main_guard()
CY = 1.55
FW, FH, FD = 0.68, 0.48, 0.035


def build():
    X.begin()
    X.decal("M_Decal_FloorPlan", "floor_plan.png")
    o = []
    w = 0.045
    # moulded frame: four rails with a stepped profile (outer step, cove, inner lip)
    for nm, mn, mx in (("fr_t", (-FW / 2, CY + FH / 2 - w, 0.0), (FW / 2, CY + FH / 2, FD)), ("fr_b", (-FW / 2, CY - FH / 2, 0.0), (FW / 2, CY - FH / 2 + w, FD)),
                       ("fr_l", (-FW / 2, CY - FH / 2 + w, 0.0), (-FW / 2 + w, CY + FH / 2 - w, FD)), ("fr_r", (FW / 2 - w, CY - FH / 2 + w, 0.0), (FW / 2, CY + FH / 2 - w, FD))):
        o.append(gbox(nm, mn, mx, "M_Wood_Walnut", bevel=0.006, seg=2))
    # inner lip (a step toward the picture) and the cream mount board behind
    o.append(gbox("lip_t", (-FW / 2 + w, CY + FH / 2 - w - 0.008, 0.0), (FW / 2 - w, CY + FH / 2 - w, 0.026), "M_Wood_Walnut", bevel=0.002))
    o.append(gbox("lip_b", (-FW / 2 + w, CY - FH / 2 + w, 0.0), (FW / 2 - w, CY - FH / 2 + w + 0.008, 0.026), "M_Wood_Walnut", bevel=0.002))
    o.append(gbox("lip_l", (-FW / 2 + w, CY - FH / 2 + w + 0.008, 0.0), (-FW / 2 + w + 0.008, CY + FH / 2 - w - 0.008, 0.026), "M_Wood_Walnut", bevel=0.002))
    o.append(gbox("lip_r", (FW / 2 - w - 0.008, CY - FH / 2 + w + 0.008, 0.0), (FW / 2 - w, CY + FH / 2 - w - 0.008, 0.026), "M_Wood_Walnut", bevel=0.002))
    q = gquad("IA_floor_plan", (0.0, CY, 0.0195), (1, 0, 0), (0, 1, 0), 0.59, 0.37, "M_Decal_FloorPlan")
    part("IA_floor_plan", [q], (0.0, CY, 0.0195), presmooth=False)
    X.top(o)
    part("floor_plan_frame", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    req = ["floor_plan_frame", "IA_floor_plan"]
    errs = X.finish(NAME, req, ["IA_floor_plan"], BUDGET, {"IA_floor_plan": (0.0, CY, 0.0195)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.2, 1.6, 1.2), (0.0, CY, 0.0), 32)], floor=False, world=0.6)
