"""cot.glb — Leyla's camp cot in the Night Cell (R3, "a grandmother's attic, kept warm"), with a child's drawing on the pillow.

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3b, §7: view `cot`; the drawing of Mira is the quiet echo of Lab 7).
A folding wooden cot: two walnut side rails with a stretched canvas bed, splayed legs with scissor cross-bars and iron
brackets, a thin ticking mattress, a linen sheet, a pillow and a folded brick-red wool blanket (M_Wool_Knit, cream stripe)
draped over the foot end and hanging over the front edge. A rolled spare blanket sits at the foot.

Model space (Godot): front +Z (the long side faces the room), origin on the floor at the footprint centre, footprint 1.90 (x) x 0.80 (z),
sleeping surface about 0.46 m, head (pillow) at -X. Suggested placement in `room_cell`: (-0.75, 0, -1.58), yaw 0 (head toward the west wall).

Parts:
  cot_body          everything static (frame, canvas, mattress, sheet, pillow, blankets)
  IA_cot_drawing    the pencil/crayon drawing lying on the pillow, tilted 12 deg toward the viewer: a 0.20 x 0.27 quad (M_Decal_CellDrawing,
                    UV 0..1) on a card. Origin at its centre (-0.74, 0.622, 0.072), identity rotation (the tilt is baked into the mesh)
  light_cot         empty above the pillow (-0.55, 1.10, 0.10) for a soft fill, optional

    blender -b --factory-startup -P tools/blender/models/cot.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "cot"
BUDGET = 3600
ARGS = M.main_guard()
WOOD, IRON, CANVAS = "M_Wood_Walnut", "M_Steel_Dark", "M_Linen"
DRAW_BOTTOM = (-0.74, 0.49, 0.10)
DRAW_C = (-0.74, 0.49 + 0.135 * math.cos(math.radians(12.0)), 0.10 - 0.135 * math.sin(math.radians(12.0)))
HB = 0.34                                   # canvas height (top of the rails)


def frame():
    o = []
    L = 0.93
    for z in (-0.37, 0.37):                  # side rails
        o.append(gbox(f"rail{z}", (-L, HB - 0.06, z - 0.025), (L, HB, z + 0.025), WOOD, bevel=0.006))
        for x in (-L, L):                    # iron end caps
            o.append(gbox(f"cap{z}{x}", (x - 0.012 if x > 0 else x - 0.004, HB - 0.058, z - 0.027), (x + 0.004 if x > 0 else x + 0.012, HB - 0.002, z + 0.027),
                          IRON, bevel=0.002))
    for x in (-L + 0.03, L - 0.03):          # end bars with a slight lip
        o.append(gbox(f"endbar{x}", (x - 0.025, HB - 0.05, -0.37), (x + 0.025, HB - 0.01, 0.37), WOOD, bevel=0.005))
    # scissor legs (X cross at the two thirds) on both sides, spread outward at the floor
    for z in (-0.38, 0.38):
        for x0, x1 in ((-0.75, -0.45), (0.45, 0.75)):
            for a, b in ((x0, x1), (x1, x0)):
                p0 = Vector((a, HB - 0.05, z))
                p1 = Vector((b, 0.02, z + (0.03 if z > 0 else -0.03)))
                o.append(_strut(f"leg{z}{a}{b}", p0, p1, 0.026))
            o.append(gcyl(f"pin{z}{x0}", 0.011, 0.075, ((x0 + x1) / 2, 0.17, z - 0.0375), axis="z", verts=8, mat="M_Brass_Aged", bevel=0.0))
        # floor stretcher runners
        o.append(gbox(f"runner{z}", (-0.78, 0.0, z - 0.02 + (0.03 if z > 0 else -0.03)), (0.78, 0.03, z + 0.02 + (0.03 if z > 0 else -0.03)), WOOD, bevel=0.004))
    for x in (-0.60, 0.60):                  # cross brace under the canvas
        o.append(gbox(f"xbrace{x}", (x - 0.02, HB - 0.12, -0.36), (x + 0.02, HB - 0.07, 0.36), WOOD, bevel=0.003))
    return o


def _strut(name, p0, p1, w):
    """Square-section strut between two Godot points."""
    d = p1 - p0
    ln = d.length
    mid = (p0 + p1) / 2
    o = M.box(name, (w, ln, w * 0.8), loc=(0, 0, 0), mat=WOOD, bevel=0.004, segments=1)
    A.place(o, Matrix.Identity(4))
    bd = GV(d).normalized()
    q = Vector((0, 1, 0)).rotation_difference(bd)
    o.data.transform(q.to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(GV(mid)))
    return o


def bed():
    o = []
    # canvas: slightly sagging sheet between the rails, thick 6 mm
    def sec(x):
        sag = -0.022 * (1.0 - (x / 0.93) ** 2)
        return [(-0.37 + 0.74 * j / 6, HB - 0.004 + sag * math.sin(math.pi * j / 6)) for j in range(7)]
    xs = [-0.93 + 1.86 * i / 14 for i in range(15)]
    o.append(Q.drape("canvas", xs, sec, thick=0.006, mat="M_Fabric"))
    # mattress: thick ticking pad with rounded edges
    mat_ = A.bevel_box("mattress", (1.74, 0.66, 0.085), loc=(0, 0, 0), mat="M_Linen", bevel=0.032, segments=3)
    A.place(mat_, Matrix.Identity(4))
    mat_.data.transform(Matrix.Translation(G(0.0, HB + 0.043 - 0.02, 0.0)))
    o.append(mat_)
    for k in range(5):                       # tufting buttons on the pad
        o.append(gcyl(f"tuft{k}", 0.006, 0.006, (-0.55 + 0.275 * k, HB + 0.063 + 0.003 + 0.002, 0.0), axis="y", verts=6, mat="M_Leather", bevel=0.0))
    return o


def bedding():
    o = []
    ytop = HB + 0.108
    # pillow at the head
    o.append(Q.gsphere("pillow", 0.30, (-0.70, ytop + 0.045, 0.0), (0.88, 0.17, 0.60), mat="M_Linen", segs=18, rings=9))
    # linen sheet folded back over the blanket line
    def sec_sheet(x):
        pts = [(0.325, ytop - 0.18 - 0.0), (0.335, ytop - 0.02), (0.30, ytop + 0.014), (0.0, ytop + 0.014 + 0.004 * math.sin(x * 9)),
               (-0.30, ytop + 0.014), (-0.335, ytop - 0.02), (-0.34, ytop - 0.15)]
        return [(z, y) for z, y in pts][::-1] if False else [(z, y) for z, y in sorted(pts, key=lambda p: p[0])]
    xs = [-0.30 + 1.15 * i / 10 for i in range(11)]
    o.append(Q.drape("sheet", xs, sec_sheet, thick=0.008, mat="M_Linen", folds=0.0))
    # wool blanket: over the foot part of the bed and hanging over the front (+Z) edge, soft ripples
    def sec_blank(x):
        z_end = 0.31
        pts = [(-0.345, ytop + 0.020), (-0.25, ytop + 0.032 + 0.006 * math.sin(x * 11)), (-0.1, ytop + 0.036), (0.1, ytop + 0.034 + 0.005 * math.sin(x * 7 + 1)),
               (0.25, ytop + 0.030), (0.335, ytop + 0.014), (0.37, ytop - 0.03), (0.385, ytop - 0.12), (0.392, ytop - 0.21 + 0.03 * math.sin(x * 12))]
        return pts
    xs = [-0.10 + 1.02 * i / 16 for i in range(17)]
    o.append(Q.drape("blanket", xs, sec_blank, thick=0.016, mat="M_Wool_Knit", folds=0.004, seed=0.6))
    # rolled spare blanket at the foot (cylinder) with a strap
    o.append(gcyl("roll", 0.075, 0.46, (0.82, ytop + 0.075 + 0.02, -0.23), axis="z", verts=14, mat="M_Wool_Knit", bevel=0.004))
    for z in (-0.12, 0.12):
        o.append(gcyl(f"strap{z}", 0.078, 0.022, (0.82, ytop + 0.075 + 0.02, z - 0.011), axis="z", verts=14, mat="M_Leather", bevel=0.0))
    return o


def drawing():
    """A sheet of paper with Mira's crayon drawing, leaning back against the pillow (tilt baked into the mesh)."""
    card = gbox("card", (-0.100, 0.0, -0.002), (0.100, 0.27, 0.0), "M_Paper", bevel=0.001)
    q = gquad("draw", (0.0, 0.135, 0.0008), (1, 0, 0), (0, 1, 0), 0.196, 0.266, "M_Decal_CellDrawing")
    tilt = Matrix.Rotation(math.radians(-12.0), 4, "X")          # about Godot +X: the top goes toward -Z
    for ob in (card, q):
        A.place(ob, Matrix.Identity(4))
        ob.data.transform(Matrix.Translation(GV(DRAW_BOTTOM)) @ tilt)
    return X.part("IA_cot_drawing", [card, q], DRAW_C)


def main():
    X.begin()
    X.decal("M_Decal_CellDrawing", "cell_drawing.png")
    q = drawing()
    body = frame() + bed() + bedding()
    X.top(body)
    mount("light_cot", (-0.55, 1.10, 0.10))
    part("cot_body", body, (0, 0, 0))
    return q


if __name__ == "__main__":
    main()
    req = ["cot_body", "IA_cot_drawing", "light_cot"]
    errs = X.finish(NAME, req, ["IA_cot_drawing"], BUDGET, {"IA_cot_drawing": DRAW_C}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.6, 1.3, 1.9), (0.0, 0.35, 0.0), 42), ("_head", (-0.4, 1.1, 1.3), (-0.7, 0.5, 0.0), 40),
                          ("_front", (0.1, 0.8, 2.2), (0.0, 0.35, 0.0), 40)], floor=True, world=0.15)
