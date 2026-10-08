"""letter.glb — Strand's letter (inventory item; also used for Leyla's photograph envelope).

A cream C6 envelope lying back-up: closed flap with its folded seams, an intact crimson wax seal carrying
the Institute's mark in relief (a ring crossed by a single meridian), the sender's initials "E. S." in
ink. The envelope was slit open along the top edge and the tri-folded letter, addressed "Leyla" on its
outer panel, is pulled halfway out. 0.162 x 0.160 x ~0.005 m. Lies flat (Blender +Z up), the letter
sticks out toward +Y. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/letter.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "letter"
EW, EH, ET = 0.162, 0.114, 0.0016     # envelope
SEAL = (0.0, 0.0015)


def layer(name, pts, z0, t, mat="M_Paper", bevel=0.00012):
    obj = L.curve_solid(name, [pts], t, bevel=bevel, bevel_res=0, mat=mat)
    obj.location = (0, 0, z0)
    return obj


def wax_seal(cx, cy, z0):
    prof = [(0.0128, 0.0), (0.0126, 0.0006), (0.0118, 0.0018), (0.0102, 0.0028), (0.0087, 0.0025),
            (0.0079, 0.0018), (0.0, 0.0018)]
    seal = L.lathe2("seal", prof, segments=28, mat="M_Enamel_Crimson", cap_bottom=False)
    for v in seal.data.vertices:          # organic, poured outline
        r = math.hypot(v.co.x, v.co.y)
        if r > 0.0100:
            a = math.atan2(v.co.y, v.co.x)
            f = 1.0 + 0.07 * math.sin(3 * a + 1.0) + 0.045 * math.sin(7 * a + 2.0) + 0.02 * math.sin(11 * a)
            v.co.x *= f
            v.co.y *= f
    seal.location = (cx, cy, z0)
    ring = M.torus("emblem_ring", 0.0050, 0.00055, loc=(cx, cy, z0 + 0.0019), major_seg=20, minor_seg=4,
                   mat="M_Enamel_Crimson")
    bar = M.box("emblem_meridian", (0.0011, 0.0124, 0.0009), loc=(cx, cy, z0 + 0.0020), mat="M_Enamel_Crimson",
                bevel=0.0003, segments=1)
    dot = L.lathe2("emblem_dot", [(0.0, 0.0), (0.0016, 0.0), (0.0012, 0.0006), (0.0, 0.0008)], segments=8,
                   mat="M_Enamel_Crimson", cap_bottom=False)
    dot.location = (cx, cy, z0 + 0.0020)
    return [seal, ring, bar, dot]


def build():
    parts = []
    env = M.box("envelope", (EW, EH, ET), loc=(0, 0, ET / 2), mat="M_Paper", bevel=0.0003, segments=1)
    parts.append(env)
    # bottom flap (under) and the closed top flap with a rounded tip
    hx, hy = EW / 2, EH / 2
    parts.append(layer("flap_bottom", [(-hx, -hy), (hx, -hy), (hx, -hy + 0.006), (0.006, 0.011), (-0.006, 0.011),
                                       (-hx, -hy + 0.006)], ET, 0.00022))
    tip = [(0.012 * math.cos(a), SEAL[1] + 0.012 * math.sin(a)) for a in
           (math.radians(d) for d in (-20, -55, -90, -125, -160))]
    parts.append(layer("flap_top", [(-hx, hy), (-hx + 0.0005, hy - 0.004)] + tip[::-1] +
                       [(hx - 0.0005, hy - 0.004), (hx, hy)], ET + 0.00022, 0.00022))
    parts += wax_seal(SEAL[0], SEAL[1], ET + 0.00044)
    # sender's initials in ink, lower right of the back
    parts.append(D.hand("initials", "E. S.", 0.0095, ratio=0.6, mat="M_Bakelite", loc=(0.050, -0.040, ET + 0.00025),
                        rot=(0, 0, math.radians(-4.0))))
    # the tri-folded letter pulled halfway out of the slit top edge
    lw, out = 0.148, 0.046
    sheet = []
    a = [(-lw / 2, -0.030), (lw / 2, -0.030), (lw / 2, hy + out), (-lw / 2, hy + out)]
    b = [(-lw / 2 + 0.0006, -0.030), (lw / 2 - 0.0006, -0.030), (lw / 2 - 0.0006, hy + out - 0.0035),
         (-lw / 2 + 0.0006, hy + out - 0.0035)]
    sheet.append(layer("letter_a", a, 0.00045, 0.00030))
    sheet.append(layer("letter_b", b, 0.00075, 0.00030))
    sheet.append(D.hand("addressee", "Leyla", 0.0135, ratio=0.6, mat="M_Bakelite", loc=(-0.018, hy + 0.024, 0.00108)))
    sheet.append(L.flat_shape("underline", [[(-0.036, 0.0), (0.004, 0.0004), (0.004, 0.0011), (-0.036, 0.0007)]],
                              mat="M_Bakelite", loc=(0.0, hy + 0.0148, 0.00108)))
    let = M.join(sheet, "letter_sheet")
    let.data.transform(Matrix.Translation((-0.006, -hy, 0.0)))
    let.data.transform(Matrix.Rotation(math.radians(5.0), 4, "Z"))
    let.data.transform(Matrix.Translation((0.006, hy, 0.0)))
    parts.append(let)
    return [M.join(parts, NAME)]


def main():
    D.item_main(NAME, build, shots=[
        ("", (0.07, -0.20, 0.22), (0.0, 0.015, 0.0), 45),
        ("_2", (0.045, -0.095, 0.120), (0.0, 0.006, 0.0), 110),
    ])


if __name__ == "__main__":
    main()
