"""weight_1/2/4/8.glb — the four cast counterweights of the book lift (puzzle N7: hang 1-2-4-8 on the counterweight hook).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N7, items `weights (4)`). One script writes four GLBs:
`weight_1.glb`, `weight_2.glb`, `weight_4.glb`, `weight_8.glb`. Each is a cast-iron slotted disc weight with a forged top ring and a
raised number (1, 2, 4, 8) on both faces plus that many notches round the rim, so the value reads without text. Sizes grow
with the mass (the 8 is 0.19 m across). The item origin is the centre of mass; the hanging ring is at +Y (Blender +Z)
and the number faces +Z toward the viewer (Godot +Z, Blender -Y). Hang the model by its ring: in the `hook_mount`
of `book_lift_cage` place the item so that its ring top sits at the mount (offset +ring_top_y, listed in docs/models/ch2_exp.md).

    blender -b --factory-startup -P tools/blender/models/weights.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "weights"
SIZES = {1: (0.060, 0.022), 2: (0.078, 0.028), 4: (0.100, 0.034), 8: (0.125, 0.042)}   # radius, thickness


def build(v):
    r, t = SIZES[v]
    ob = []
    # disc standing in the XZ plane (axis along Y in Blender? use axis Y = thickness) hanging ring above (+Z)
    disc = D.revolve("disc", [(0.0, -t / 2), (r - 0.004, -t / 2), (r, -t / 2 + 0.004), (r, t / 2 - 0.004), (r - 0.004, t / 2),
                              (0.0, t / 2)], direction=(0, 1, 0), segments=36, mat="M_Iron_Rust")
    ob.append(disc)
    ob.append(D.revolve("boss", [(0.0, -t / 2 - 0.004), (r * 0.30, -t / 2 - 0.004), (r * 0.32, 0.0), (r * 0.30, t / 2 + 0.004),
                                 (0.0, t / 2 + 0.004)], direction=(0, 1, 0), segments=20, mat="M_Iron_Rust"))
    # forged ring on top
    ring = M.torus("ring", r * 0.20, 0.0075, loc=(0, 0, r + r * 0.14), rot=(math.pi / 2, 0, 0), major_seg=18, minor_seg=6,
                   mat="M_Steel_Dark")
    ob.append(ring)
    ob.append(M.box("neck", (0.018, 0.012, r * 0.18), loc=(0, 0, r + r * 0.03), mat="M_Steel_Dark", bevel=0.002))
    # notches: v notches in the rim (small dark boxes) and raised numeral on both faces
    for k in range(v):
        a = math.pi + (k - (v - 1) / 2) * 0.28
        ob.append(M.box(f"notch{k}", (0.012, t * 1.02, 0.014), loc=(math.sin(a) * (r - 0.004), 0, -math.cos(a) * (r - 0.004) * -1 - 0.0),
                        rot=(0, a, 0), mat="M_Steel_Dark", bevel=0.0))
    for sgn in (1, -1):
        txt = A.text_lowpoly(f"num{sgn}", str(v), r * 1.0, depth=0.004, mat="M_Brass_Aged", font_path=X.FONT, resolution=1)
        txt.data.transform(Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Translation((0, 0, 0)))
        txt.data.transform(Matrix.Translation((0, -sgn * (t / 2 + 0.0005) + (0.0 if sgn == 1 else 0.0), -r * 0.02)))
        if sgn == -1:
            txt.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
        ob.append(txt)
    return ob


def one(v):
    X.begin()
    objs = build(v)
    for o in objs:
        pass
    j = M.join(objs, f"weight_{v}")
    M.finalize([j])
    mesh = [j]
    com = D.recentre([j], D.centre_of_mass(mesh))
    path = D.export(f"weight_{v}")
    D.describe(f"weight_{v}")
    return j


def main():
    args = M.main_guard()
    for v in (1, 2, 4, 8):
        one(v)
    if "--no-render" not in args:
        # lineup render of the four (QA only): rebuild side by side
        X.begin()
        objs = []
        for i, v in enumerate((1, 2, 4, 8)):
            o = M.join(build(v), f"w{v}")
            o.location = (-0.30 + 0.20 * i, 0, 0.14)
            objs.append(o)
        M.finalize(objs)
        D.qa_tweak()
        D.shot("weights_lineup", (0.0, -0.80, 0.30), (0.0, 0.0, 0.16), lens=70, floor_z=0.0, samples=24, res=(800, 400))


main()
