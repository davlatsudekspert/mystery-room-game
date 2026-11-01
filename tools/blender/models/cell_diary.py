"""cell_diary.glb — Leyla's night diary (Night Cell desk; the item `cell_diary`, a document read in an overlay).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §7 new items). A small worn leather diary lying closed: stitched cover with rounded corners and brass
corner caps, a cream page block with a slightly fanned edge, a rounded spine with raised bands, an elastic band closed over the cover with a brass
tab, a crimson ribbon bookmark hanging out at the foot and a stub of yellow pencil tucked along the spine. A small embossed crescent-and-star on the cover.

Model space (Godot): the item lies FLAT on the desk, the cover faces +Y, the spine is on the -X side, the foot (ribbon end) toward +Z. Origin at the
centre of mass (0, 0, 0). Size 0.150 (x) x 0.036 (y) x 0.210 (z).

Parts:
  IA_cell_diary   the whole diary (the single tap target); origin = centre (identity)

    blender -b --factory-startup -P tools/blender/models/cell_diary.py [-- --no-render]
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

NAME = "cell_diary"
BUDGET = 1800
ARGS = M.main_guard()
W, H, D = 0.150, 0.036, 0.210
LEA, BR = "M_Leather", "M_Brass_Aged"


def build():
    X.begin()
    x0, x1, z0, z1 = -W / 2, W / 2, -D / 2, D / 2
    y0 = -H / 2
    o = []
    # pages: block inset 3 mm from the cover edge
    o.append(gbox("pages", (x0 + 0.008, y0 + 0.0045, z0 + 0.004), (x1 - 0.003, y0 + H - 0.0045, z1 - 0.004), "M_Paper", bevel=0.0012))
    for k in range(6):                                                 # fanned page edges (foot, front, head)
        yy = y0 + 0.007 + 0.0035 * k
        o.append(gbox(f"pg{k}", (x0 + 0.008 + 0.002 * (k % 2), yy, z1 - 0.004), (x1 - 0.003, yy + 0.0011, z1 - 0.0015), "M_Paper", bevel=0.0))
    # covers: bottom and top boards with rounded edges, spine as a half-round
    o.append(gbox("cover_b", (x0, y0, z0), (x1, y0 + 0.0045, z1), LEA, bevel=0.0018, seg=2))
    o.append(gbox("cover_t", (x0, y0 + H - 0.0045, z0), (x1, y0 + H, z1), LEA, bevel=0.0018, seg=2))
    o.append(glathe("spine", [(0.0, -D / 2 + 0.001), (H / 2, -D / 2 + 0.001), (H / 2, D / 2 - 0.001), (0.0, D / 2 - 0.001)], (x0 + 0.0, 0.0, 0.0), axis="z",
                    segments=14, mat=LEA) if False else gcyl("spine", H / 2, D - 0.002, (x0 + 0.0, 0.0, z0 + 0.001), axis="z", verts=14, mat=LEA, bevel=0.0))
    for k in range(4):                                                 # raised spine bands
        zc = -0.075 + 0.05 * k
        o.append(gcyl(f"band{k}", H / 2 + 0.0012, 0.006, (x0, 0.0, zc - 0.003), axis="z", verts=14, mat="M_Wood_Mahogany", bevel=0.0))
    # brass corner caps on the three open corners (cover side) and stitching dashes along the top cover edge
    for sx, sz in ((1, 1), (1, -1)):
        cx, cz = x1 - 0.011, sz * (z1 - 0.011)
        o.append(gbox(f"cc{sx}{sz}", (cx - 0.011, y0 + H - 0.0050, cz - 0.011), (cx + 0.011, y0 + H + 0.0006, cz + 0.011), BR, bevel=0.0012))
    ypos = y0 + H + 0.0003
    for i in range(18):
        zz = z0 + 0.014 + i * ((D - 0.028) / 17)
        o.append(gbox(f"st{i}", (x1 - 0.0085, ypos, zz - 0.003), (x1 - 0.0075, ypos + 0.0006, zz + 0.003), "M_Wood_Mahogany", bevel=0.0))
        o.append(gbox(f"stl{i}", (x0 + 0.014, ypos, zz - 0.003), (x0 + 0.015, ypos + 0.0006, zz + 0.003), "M_Wood_Mahogany", bevel=0.0)) if i % 2 == 0 else None
    # elastic band over the cover with a brass slider
    o.append(gbox("elastic", (x1 - 0.036, y0 + H - 0.0006, z0 - 0.0006), (x1 - 0.022, y0 + H + 0.0014, z1 + 0.0006), "M_Fabric", bevel=0.0004))
    o.append(gbox("elastic_f", (x1 - 0.036, y0 - 0.0010, z0 - 0.0006), (x1 - 0.022, y0 + H, z0 + 0.0004), "M_Fabric", bevel=0.0004))
    o.append(gbox("slider", (x1 - 0.040, y0 + H + 0.0004, -0.004), (x1 - 0.018, y0 + H + 0.0026, 0.016), BR, bevel=0.0008))
    # embossed crescent and star on the cover (flat shapes, 0.6 mm), upper left of the elastic
    ccx, ccz = x0 + 0.050, 0.0
    cres = M.torus("cres", 0.020, 0.0016, major_seg=20, minor_seg=4, mat="M_Brass_Aged")
    A.place(cres, Matrix.Identity(4))
    cres.data.transform(Matrix.Translation(GV((ccx, y0 + H + 0.0006, ccz))) @ Matrix.Rotation(math.radians(90), 4, "X") * 1.0 if False else Matrix.Identity(4))
    cres.data.transform(Matrix.Translation(GV((ccx, ypos + 0.0004, ccz))) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    o.append(cres)
    st = gpoly("star", [(math.sin(a) * (0.0085 if k % 2 == 0 else 0.0035), math.cos(a) * (0.0085 if k % 2 == 0 else 0.0035))
                       for k in range(10) for a in [math.radians(36 * k)]], 0.0008, X.C.gframe((ccx + 0.010, ypos, ccz - 0.001), (1, 0, 0), (0, 0, -1)),
               mat=BR, bevel=0.0)
    o.append(st)
    # ribbon bookmark out of the foot, a pencil stub along the spine side
    o.append(gbox("ribbon", (x0 + 0.040, y0 + 0.012, z1 - 0.003), (x0 + 0.050, y0 + 0.0135, z1 + 0.042), "M_Enamel_Crimson", bevel=0.0))
    o.append(gcyl("pencil", 0.0035, 0.100, (x0 + 0.014, y0 + H + 0.0028, z0 + 0.050), axis="z", verts=6, mat="M_Enamel_Amber", bevel=0.0))
    o.append(gcyl("pencil_tip", 0.0035, 0.012, (x0 + 0.014, y0 + H + 0.0028, z0 + 0.038), axis="z", verts=6, mat="M_Wood_Panel", bevel=0.0, r_top=0.0008))
    o.append(gcyl("pencil_loop", 0.0045, 0.008, (x0 + 0.014, y0 + H + 0.0028, z0 + 0.150), axis="z", verts=8, mat="M_Fabric", bevel=0.0))
    X.top(o)
    return part("IA_cell_diary", o, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["IA_cell_diary"], ["IA_cell_diary"], BUDGET, {"IA_cell_diary": (0, 0, 0)}, show=["IA_cell_diary"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.18, 0.28, 0.32), (0.0, 0.0, 0.01), 32)], floor=True, world=0.2)
