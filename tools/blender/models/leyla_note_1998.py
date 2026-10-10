"""leyla_note_1998.glb — Leyla's note from 1998: a folded sheet of lined notepaper with her sign and the year in ink (Chapter 4, group H; secret S1, locker 17).

A cream sheet folded in half and again (0.090 x 0.120 m, 3 layers at the folded end): the top third folded down over the sheet (its crease on the top edge, its lower edge ragged), a torn left
edge, one dog-eared corner (a small triangle folded up at the lower right), a diagonal crease; on the outer face Leyla's sign (a crescent opening to the right and three dots) in hand-inked
lines and the year 1998 in her handwriting, under it three lines of unreadable scribble and a rule. No words. Lies flat (Blender +Z = Godot +Y), the crease edge toward Blender +Y (Godot -Z).
Origin at the centre of mass. Slots: M_Paper + M_Bakelite (ink).
    blender -b --factory-startup -P tools/blender/models/leyla_note_1998.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402
import lib_ch4_items as H  # noqa: E402  (sets the QA output folder to qa/blender/ch4)
from mathutils import Matrix, Vector  # noqa: E402

NAME = "leyla_note_1998"
PAPER, INK = "M_Paper", "M_Bakelite"
W, HT = 0.090, 0.120
T = 0.0007


def sheet_outline():
    """The sheet: a torn left edge, a slightly wavy right edge, square top and bottom."""
    hw, hh = W / 2.0, HT / 2.0
    left = [(-hw, hh), (-hw - 0.0016, hh - 0.012), (-hw + 0.0010, hh - 0.022), (-hw - 0.0020, hh - 0.036), (-hw + 0.0008, hh - 0.050), (-hw - 0.0014, hh - 0.064),
            (-hw + 0.0012, hh - 0.080), (-hw - 0.0018, hh - 0.094), (-hw + 0.0006, hh - 0.106), (-hw, -hh)]
    return [(hw, -hh), (hw + 0.0008, -hh + 0.030), (hw - 0.0006, -hh + 0.070), (hw, hh), (-hw, hh)] + left[1:-1] + [(-hw, -hh)]


def build():
    parts = []
    hw, hh = W / 2.0, HT / 2.0
    base = G.plate_xy("sheet", [sheet_outline()], T, 0.0, PAPER, bevel=0.0001)
    parts.append(base)
    # the folded-down top third: crease on the top edge, a ragged lower edge, a little thicker
    flap = [(-hw + 0.0008, hh), (hw, hh), (hw - 0.0004, hh - 0.040), (0.050 * 0.6, hh - 0.0425), (0.020, hh - 0.0385), (-0.010, hh - 0.0440), (-0.030, hh - 0.0405), (-hw - 0.0008, hh - 0.0420)]
    parts.append(G.plate_xy("flap", [flap], 0.0008, T, PAPER, bevel=0.0001))
    # a second fold: the right third turned over the flap (a narrow strip) and a dog-eared corner at the lower right
    ear = [(hw, -hh), (hw - 0.017, -hh), (hw, -hh + 0.017)]
    parts.append(G.plate_xy("ear", [ear], 0.0007, T, PAPER, bevel=0.0001))
    # crease lines: thin raised strips (a diagonal and the vertical middle fold)
    parts.append(G.plate_xy("crease", [[(-0.0008, hh - 0.0425), (0.0008, hh - 0.0425), (0.0008, -hh + 0.002), (-0.0008, -hh + 0.002)]], 0.00025, T, PAPER, bevel=0.0))
    # the ink: Leyla's sign (a crescent opening right + three dots), the year 1998, scribble lines and a rule
    sign = G.symbols().loops("sign", 0.026)
    ink = []
    ink.append(L.flat_shape("sign", sign, mat=INK, loc=(-0.018, 0.0045, T + 0.0003)))
    yr = D.hand("year", "1998", 0.0190, ratio=0.7, mat=INK, loc=(0.020, 0.0045, T + 0.0003), rot=(0.0, 0.0, math.radians(3.0)))
    ink.append(yr)
    for k, (y, length, ang) in enumerate(((-0.020, 0.062, 1.0), (-0.032, 0.054, -1.5), (-0.044, 0.060, 0.8), (-0.056, 0.036, -0.6))):
        pts = [(x * length - length / 2.0, 0.00055 * math.sin(x * 7.0 + k) ) for x in [i / 14.0 for i in range(15)]]
        strip = [(px, py + 0.0006) for (px, py) in pts] + [(px, py - 0.0006) for (px, py) in reversed(pts)]
        o = L.flat_shape(f"line{k}", [strip], mat=INK, loc=(0.0, y, T + 0.0003), rot=(0.0, 0.0, math.radians(ang)))
        ink.append(o)
    rule = [(-0.032, -0.0805), (0.032, -0.0795), (0.032, -0.0809), (-0.032, -0.0819)]
    ink.append(L.flat_shape("rule", [rule], mat=INK, loc=(0.0, 0.0, T + 0.0003)))
    root = M.join(parts, NAME)
    inkobj = M.join(ink, "ink")
    M.set_parent(inkobj, root)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 30.0), required=("ink",), budget=1800, surf_budget=3, mat_budget=2, shots=[
        ("", (0.06, -0.12, 0.13), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, -0.001, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
