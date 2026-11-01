"""acetate_sheet_a/b/c.glb — the three acetate sheets of the light table (puzzle N3; items `acetate_a/b/c`).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N3). One script writes three GLBs. Each is a square clear acetate sheet (0.26 x 0.26 x 0.0015,
M_Acetate, translucent) with one clipped corner (the reference corner, top left when the sheet is upright), a 0.242 x 0.242 print quad
(M_Decal_Sheet, 11 x 11 cells of 0.022 m, UV 0..1; the code supplies the variant mask: opaque cells are the noise and the glyph), a thin edge
tape and a flip tab on the right edge. The tape and tab colour tells the sheets apart without text: a = crimson, b = cobalt, c = amber.

Model space (Godot): built UPRIGHT in the XY plane, front +Z, origin at the centre of the sheet (item convention). On the table the mounts
`sheet_mount_0..2` of `light_table` carry a -90 deg rotation about +X, so the sheet lies flat with its front up; rotate / flip it about its own axes:
  IA_sheet      root (the sheet), origin (0, 0, 0): tap = rotate 90 deg about its local +Z (the normal) each tap
  sheet_print   child, quad 0.242 x 0.242 at z +0.0010, material slot `M_Decal_Sheet` (alpha), UV 0..1 over the 11 x 11 cells
  IA_flip_tab   child, origin at the tab centre (0.1475, 0, 0): tap = flip the sheet, 180 deg about its local +Y (the tab swings to the left edge)

    blender -b --factory-startup -P tools/blender/models/acetate_sheet.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, gpoly, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "acetate_sheet"
BUDGET = 700
ARGS = M.main_guard()
S = 0.13                                   # half size
CH = 0.035                                 # clipped corner
T = 0.0015
TABC = {"a": "M_Enamel_Crimson", "b": "M_Enamel_Cobalt", "c": "M_Enamel_Amber"}


def flat(z0):
    return X.C.gframe((0.0, 0.0, z0), (1, 0, 0), (0, 1, 0))


def build(k):
    X.begin()
    Q.alpha_decal("M_Decal_Sheet", "sheet_print.png")
    pane_pts = [(-S + CH, S), (S, S), (S, -S), (-S, -S), (-S, S - CH)]            # clipped top-left corner
    pane = gpoly("pane", pane_pts, T, flat(-T / 2), mat="M_Acetate", bevel=0.0003)
    tape = []
    tc = TABC[k]
    w = 0.0085
    tape.append(gbox("tp_b", (-S, -S, -T / 2 - 0.0002), (S, -S + w, T / 2 + 0.0002), tc, bevel=0.0))
    tape.append(gbox("tp_r", (S - w, -S + w, -T / 2 - 0.0002), (S, S, T / 2 + 0.0002), tc, bevel=0.0))
    tape.append(gbox("tp_t", (-S + CH, S - w, -T / 2 - 0.0002), (S - w, S, T / 2 + 0.0002), tc, bevel=0.0))
    tape.append(gbox("tp_l", (-S, -S + w, -T / 2 - 0.0002), (-S + w, S - CH, T / 2 + 0.0002), tc, bevel=0.0))
    # reference arrow on the clipped corner side: a small crimson wedge printed in 3D at the top edge (shows from both sides)
    tape.append(gpoly("arrow", [(-0.012, S - w - 0.004), (0.012, S - w - 0.004), (0.0, S - w - 0.026)], T + 0.0006, flat(-(T + 0.0006) / 2),
                      mat="M_Lacquer_Black", bevel=0.0))
    root = part("IA_sheet", [pane] + tape, (0, 0, 0))
    q = gquad("sheet_print", (0.0, 0.0, 0.0010), (1, 0, 0), (0, 1, 0), 0.242, 0.242, "M_Decal_Sheet")
    pr = part("sheet_print", [q], (0.0, 0.0, 0.0010), presmooth=False)
    # flip tab: rounded plate + a curved-arrow ring glyph
    tab = [gpoly("tabplate", [(-0.0175, -0.019), (0.0175, -0.019), (0.0175, 0.019), (-0.0175, 0.019)], T + 0.0004, flat(-(T + 0.0004) / 2), mat=tc, bevel=0.0004)]
    tab[0].data.transform(Matrix.Translation(GV((0.1475, 0.0, 0.0))))
    ring = M.torus("tabring", 0.0085, 0.0014, major_seg=14, minor_seg=4, mat="M_Enamel_White")
    A.place(ring, Matrix.Identity(4))
    ring.data.transform(Matrix.Translation(GV((0.1475, 0.0, (T + 0.0004) / 2 + 0.0004))) @ Matrix.Rotation(math.radians(90), 4, "X"))
    tab.append(ring)
    head = gpoly("tabhead", [(-0.0045, 0.0), (0.0045, 0.0), (0.0, 0.0075)], 0.0012, flat(-0.0006), mat="M_Enamel_White", bevel=0.0)
    head.data.transform(Matrix.Translation(GV((0.1475 + 0.0085, 0.0, (T + 0.0004) / 2 + 0.0006))))
    tab.append(head)
    tb = part("IA_flip_tab", tab, (0.1475, 0.0, 0.0))
    X.C.parent(pr, root)
    X.C.parent(tb, root)
    return root


if __name__ == "__main__":
    for k in "abc":
        root = build(k)
        nm = f"acetate_sheet_{k}"
        req = ["IA_sheet", "sheet_print", "IA_flip_tab"]
        errs = X.finish(nm, req, ["IA_sheet", "sheet_print", "IA_flip_tab"], BUDGET, {"IA_flip_tab": (0.1475, 0.0, 0.0)}, show=req, wood=False)
    if X.want_render(ARGS):
        X.begin()
        Q.alpha_decal("M_Decal_Sheet", "sheet_print.png")
        build("a")
        X.qa_props("acetate_sheet", [("", (0.0, 0.12, 0.75), (0.0, 0.0, 0.0), 30)], floor=False, world=0.5)
