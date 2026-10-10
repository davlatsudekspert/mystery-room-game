"""pocket_watch.glb — Strand's pocket watch: a brass hunter-case watch, stopped (Chapter 4, group H; the heart drawer's `heart_watch`, puzzle P10 `lens`/story).

A closed (hunter) brass case O 50 mm x 15 mm: a reeded edge, a stepped bezel, a flat lid with two engraved rings and the Institute's mark (a ring crossed by one meridian) in polished relief,
two hinge knuckles on the left, a pendant with a fluted crown, a bow (a ring in the face plane) and the first two links of a short chain. Standing, the face toward Godot +Z (Blender -Y), the
pendant up. About 50 x 15 x 62 mm. Origin at the centre of mass. Slots: M_Brass_Aged + M_Brass_Polished.
    blender -b --factory-startup -P tools/blender/models/pocket_watch.py [-- --no-render]
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
import lib_ch4_items as H  # noqa: E402
import lib_ch4_mark as MK  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "pocket_watch"
BRASS, POL = "M_Brass_Aged", "M_Brass_Polished"
R = 0.025
ZB, ZF = -0.0072, 0.0072          # the back and the front of the case (lying frame: face +Z, the pendant +Y)


def build():
    parts = []
    # the case, lying: face +Z, a reeded edge (the 'k' flagged points), a stepped bezel and a flat lid
    prof = [(0.0, ZB), (0.0205, ZB), (0.0235, ZB + 0.0012), (R, ZB + 0.0035, "k"), (R, ZF - 0.0030, "k"), (0.0243, ZF - 0.0012), (0.0225, ZF - 0.0004), (0.0218, ZF - 0.0014),
            (0.0214, ZF), (0.0, ZF)]
    case = L.lathe2("case", prof, segments=40, mat=BRASS, knurl=0.0008)
    parts.append(case)
    # engraved rings and the mark on the lid, polished (the Institute's mark: a ring crossed by one meridian)
    for (ro, ri) in ((0.0198, 0.0190), (0.0150, 0.0145)):
        rg = L.curve_solid("ring", [L.circle(ro, 30), list(reversed(L.circle(ri, 30)))], 0.0005, bevel=0.0, mat=POL, drop_bottom=True)
        rg.location = (0, 0, ZF)
        M.apply_transform(rg)
        parts.append(rg)
    parts += MK.mark_solids(0.0235, 0.0009, POL, loc=(0.0, 0.0), z0=ZF, name="mark")
    # hinge knuckles (left) and the thumb-catch at the pendant
    for z in (-0.0035, 0.0035):
        k = L.lathe2("knuckle", [(0.0, -0.0060), (0.0033, -0.0060), (0.0033, 0.0060), (0.0, 0.0060)], segments=10, mat=BRASS)
        k.data.transform(Matrix.Translation((-R - 0.0003, 0.0, z)) @ Matrix.Rotation(math.radians(-90.0), 4, "X"))
        parts.append(k)
    # pendant (a short stem), the crown (fluted) and the bow
    stem = L.lathe2("stem", [(0.0, 0.0), (0.0042, 0.0), (0.0042, 0.0075), (0.0, 0.0075)], segments=12, mat=BRASS)
    stem.data.transform(Matrix.Translation((0.0, R - 0.0010, 0.0)) @ Matrix.Rotation(math.radians(-90.0), 4, "X"))
    parts.append(stem)
    crown = L.lathe2("crown", [(0.0, 0.0), (0.0058, 0.0), (0.0062, 0.0012, "k"), (0.0062, 0.0062, "k"), (0.0058, 0.0074), (0.0042, 0.0080), (0.0, 0.0080)], segments=20, mat=BRASS, knurl=0.0005)
    crown.data.transform(Matrix.Translation((0.0, R + 0.0063, 0.0)) @ Matrix.Rotation(math.radians(-90.0), 4, "X"))
    parts.append(crown)
    bow = M.torus("bow", 0.0090, 0.0017, loc=(0.0, R + 0.0143 + 0.0070, 0.0), major_seg=18, minor_seg=5, mat=BRASS)
    parts.append(bow)
    # the first two chain links: an oval ring in the face plane, then one turned 90 deg (an edge view), hanging from the bow
    y1 = R + 0.0143 + 0.0070 + 0.0090 + 0.0050
    for k, (rot, dy) in enumerate(((0.0, 0.0), (90.0, 0.0098))):
        lk = M.torus(f"link{k}", 0.0040, 0.0010, loc=(0.0, y1 + dy, 0.0), major_seg=10, minor_seg=4, mat=BRASS)
        lk.scale = (1.0, 1.55, 1.0)
        lk.rotation_euler = (0.0, math.radians(rot), 0.0)
        M.apply_transform(lk)
        parts.append(lk)
    root = M.join(parts, NAME)
    # stand it up: face (+Z) -> Blender -Y (Godot +Z), the pendant (+Y) -> +Z
    root.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    M.apply_transform(root)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 36.0), required=(), budget=2600, surf_budget=3, mat_budget=2, shots=[
        ("", (0.07, -0.20, 0.11), (0.0, 0.0, 0.0), 50),
        ("_2", (0.0, -0.22, 0.01), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
