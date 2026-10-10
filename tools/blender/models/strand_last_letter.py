"""strand_last_letter.glb — Strand's last letter: a folded letter bound with a crimson ribbon and sealed in wax with the Institute's mark (Chapter 4, group H; the heart drawer's `heart_letter`).

(The contract suggested re-using `letter.glb`, Strand's Chapter 2 envelope; this is a different object — the letter itself, never posted, found in the Reliquary: "Let them go.")
A cream letter folded in thirds (0.120 x 0.085 m; three loose leaves, each a little turned and offset, so the folds show as a stepped edge), a crimson ribbon 8 mm wide wrapped lengthwise round
it and a poured crimson wax seal O 0.026 over the ribbon with the Institute's mark (a ring crossed by one meridian) in relief. No words. Lies flat (hero face up = Blender +Z = Godot +Y), the long side
along X. 0.122 x 0.087 x 0.008. Origin at the centre of mass. Slots: M_Paper + M_Enamel_Crimson.
    blender -b --factory-startup -P tools/blender/models/strand_last_letter.py [-- --no-render]
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
from mathutils import Matrix, Vector  # noqa: E402

NAME = "strand_last_letter"
PAPER, WAX = "M_Paper", "M_Enamel_Crimson"
W, HT = 0.120, 0.085
LEAF = 0.0011


def leaf(name, dx, dy, rot_deg, shrink, z0):
    pts = L.rounded_rect(W - shrink, HT - shrink, 0.0012, 2)
    o = G.plate_xy(name, [pts], LEAF, z0, PAPER, bevel=0.00018)
    o.data.transform(Matrix.Translation((dx, dy, 0.0)) @ Matrix.Rotation(math.radians(rot_deg), 4, "Z"))
    return o


def build():
    paper = [leaf("leaf0", 0.0000, 0.0000, 0.0, 0.000, 0.0), leaf("leaf1", 0.0012, -0.0008, 0.5, 0.003, LEAF), leaf("leaf2", -0.0006, 0.0010, -0.4, 0.001, 2 * LEAF)]
    top = 3 * LEAF
    # the two fold creases (thirds) as thin raised strips, a slight tear at one corner
    for x in (-0.020, 0.020):
        paper.append(G.plate_xy("crease", [[(x - 0.0006, -HT / 2 + 0.0015), (x + 0.0006, -HT / 2 + 0.0015), (x + 0.0006, HT / 2 - 0.0015), (x - 0.0006, HT / 2 - 0.0015)]],
                                0.0003, top, PAPER, bevel=0.0))
    root = M.join(paper, NAME)
    # the ribbon: lengthwise over the top and down both short ends, 8 mm wide, under the seal
    rb = []
    rb.append(G.plate_xy("rib_top", [[(-W / 2 - 0.0004, -0.0040), (W / 2 + 0.0004, -0.0040), (W / 2 + 0.0004, 0.0040), (-W / 2 - 0.0004, 0.0040)]], 0.0007, top + 0.0003, WAX, bevel=0.0002))
    for sx in (-1, 1):
        rb.append(M.box("rib_end", (0.0008, 0.0080, top + 0.0012), loc=(sx * (W / 2 + 0.0008), 0.0, (top + 0.0012) / 2.0), mat=WAX, bevel=0.0002, segments=1))
    # the seal: a poured disc with an organic outline, a raised rim and the mark
    zs = top + 0.0010
    prof = [(0.0138, 0.0), (0.0136, 0.0008), (0.0128, 0.0021), (0.0112, 0.0032), (0.0094, 0.0029), (0.0086, 0.0020), (0.0, 0.0020)]
    seal = L.lathe2("seal", prof, segments=28, mat=WAX, cap_bottom=False)
    for v in seal.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r > 0.0105:
            a = math.atan2(v.co.y, v.co.x)
            f = 1.0 + 0.07 * math.sin(3 * a + 1.0) + 0.045 * math.sin(7 * a + 2.0) + 0.02 * math.sin(11 * a)
            v.co.x *= f
            v.co.y *= f
    seal.location = (0.0, 0.0, zs)
    M.apply_transform(seal)
    mark = L.curve_solid("sealmark", G.symbols().loops("mark", 0.0145), 0.0012, bevel=0.0, mat=WAX, drop_bottom=True)
    mark.location = (0.0, 0.0, zs + 0.0020)
    M.apply_transform(mark)
    rb += [seal, mark]
    ribbon = M.join(rb, "ribbon")
    M.set_parent(ribbon, root)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 32.0), required=("ribbon",), budget=1800, surf_budget=3, mat_budget=2, shots=[
        ("", (0.07, -0.12, 0.14), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, -0.001, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
