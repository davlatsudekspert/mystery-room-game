"""seed_crystal.glb — one of Leyla's seed crystals (seed library drawers, Chapter 3 E1 / E2).

A tiny clear hexagonal seed crystal, Ø 12 mm across its corners and 20 mm long with a pointed tip, set in a
turned brass collar (Ø 15 mm, 6.5 mm high: the same collar becomes the foot of the grown nursery crystal).
A flat prism face looks at the viewer. Two slots: M_Crystal (the crystal), M_Brass_Aged (the collar).
Stands upright, face +Z (Godot). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/seed_crystal.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch3_items as G  # noqa: E402

NAME = "seed_crystal"
R = 0.0060                         # circumradius (Ø 12 mm across the corners)
Z0 = G.COLLAR_SEAT - 0.0004         # crystal base, just under the collar's seat
Z_PRISM = Z0 + 0.0135              # top of the prism
Z_TIP = Z0 + 0.0200                # apex (20 mm crystal)


def build():
    cry = G.hex_crystal(NAME, [(Z0, R * 0.97), (Z0 + 0.0030, R), (Z_PRISM, R * 0.98), (Z_TIP, 0.0)],
                        jitter=[1.0, 0.96, 1.03, 0.98, 1.02, 0.95], tip_offset=(0.0004, -0.0003))
    collar = G.seed_collar("seed_collar")
    M.set_parent(collar, cry)
    return [cry]


def post():
    D.resmooth(bpy.data.objects[NAME], 10.0)
    D.resmooth(bpy.data.objects["seed_collar"], 40.0)


def report():
    lo, hi = D.bounds([bpy.data.objects["seed_collar"]])
    G.report_point("collar bottom centre", point=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    G.report_point("collar top centre", point=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))


def main():
    G.item_main(NAME, build, post=post, budget=800, extra_report=report, shots=[
        ("", (0.07, -0.15, 0.08), (0.0, 0.0, 0.0015), 135),
        ("_2", (0.0, -0.17, 0.02), (0.0, 0.0, 0.0), 135),
    ])


if __name__ == "__main__":
    main()
