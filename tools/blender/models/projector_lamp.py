"""projector_lamp.glb — the spare projector lamp from Strand's cabinet (R7 -> the dead lamp of the booth projector, gate G2).

A new, intact 750 W cinema projector lamp: a pear-shaped clear glass envelope with a tipped-off pip, a compact coiled filament on two
support wires, a ceramic neck and a brass prefocus base collar with a flange and two contact studs, a paper sticker on the neck
(numerals only). 0.115 m long including the base, 0.052 m wide.

Model space (Godot): stands upright (base down, bulb up, axis +Y), origin at the centre of mass (0, 0, 0): base bottom at y = -0.058,
the tip of the glass at y = +0.057. Item (hand-held): small. Parts: projector_lamp_body (single mesh: glass, metal, filament).
    blender -b --factory-startup -P tools/blender/models/projector_lamp.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, part  # noqa: E402

NAME = "projector_lamp"
BUDGET = 1800
ARGS = M.main_guard()


def build():
    X.begin()
    y0 = -0.058
    b = []
    # base: collar, flange, studs
    b.append(glathe("collar", [(0.0, 0.0), (0.0175, 0.0), (0.0185, 0.003), (0.0185, 0.020), (0.0165, 0.024), (0.0, 0.024)], (0, y0, 0), axis="y", segments=20, mat="M_Brass_Aged"))
    b.append(glathe("flange", [(0.0165, 0.017), (0.027, 0.017), (0.027, 0.0215), (0.0165, 0.0215)], (0, y0, 0), axis="y", segments=22, mat="M_Brass_Polished"))
    for sx in (-1, 1):
        b.append(gcyl(f"stud{sx}", 0.0042, 0.012, (sx * 0.009, y0 - 0.006, 0), axis="y", verts=8, mat="M_Brass_Polished", bevel=0.0))
    b.append(gcyl("ceramic", 0.014, 0.014, (0, y0 + 0.024, 0), axis="y", verts=16, mat="M_Porcelain", bevel=0.0, r_top=0.0125))
    # glass envelope: lathe of the pear outline (outer then inner shell, thin)
    prof = [(0.0125, 0.0), (0.016, 0.008), (0.023, 0.020), (0.026, 0.034), (0.024, 0.048), (0.017, 0.058), (0.008, 0.0635), (0.0025, 0.0655), (0.0, 0.066)]
    b.append(glathe("bulb", prof, (0, y0 + 0.036, 0), axis="y", segments=22, mat="M_Glass"))
    # filament: coiled ring of tiny cylinders between two support wires
    for sx in (-1, 1):
        b.append(gcyl(f"support{sx}", 0.0009, 0.040, (sx * 0.011, y0 + 0.040, 0), axis="y", verts=4, mat="M_Steel_Dark", bevel=0.0))
    for i in range(7):
        x = -0.0105 + i * 0.0035
        b.append(gcyl(f"coil{i}", 0.0030, 0.0012, (x, y0 + 0.078, 0), axis="x", verts=6, mat="M_Chrome", bevel=0.0) if False else
                 gbox(f"coil{i}", (x - 0.0013, y0 + 0.0755, -0.0035), (x + 0.0013, y0 + 0.0815, 0.0035), "M_Chrome", bevel=0.0))
    b.append(gbox("filament_bridge", (-0.0115, y0 + 0.0725, -0.0012), (0.0115, y0 + 0.0755, 0.0012), "M_Steel_Dark", bevel=0.0))
    # paper sticker around the ceramic neck, numerals only: a cream ring with two black bars
    b.append(glathe("sticker", [(0.0141, 0.0), (0.0146, 0.0), (0.0146, 0.009), (0.0141, 0.009)], (0, y0 + 0.027, 0), axis="y", segments=16, mat="M_Enamel_Cream"))
    b.append(gbox("sticker_bar", (-0.006, y0 + 0.0295, 0.0146), (0.006, y0 + 0.0315, 0.0151), "M_Lacquer_Black", bevel=0.0))
    return part("projector_lamp_body", b, (0, 0, 0))


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["projector_lamp_body"], [], BUDGET, {}, show=["projector_lamp_body"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.12, 0.05, 0.22), (0.0, 0.0, 0.0), 30)], floor=False, world=0.25, samples=16)
