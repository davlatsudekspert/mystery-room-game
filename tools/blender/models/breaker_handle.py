"""breaker_handle.glb — the missing bakelite handle of Panel 7's main breaker (inventory item).

Turned bakelite grip with finger grooves and a ball end, a crimson enamel collar, and a knurled brass
ferrule whose open end shows the square drive socket that slips over the breaker lever. A cross pin
holds it. Lies along Blender X with the ferrule at -X. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/breaker_handle.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "breaker_handle"


def build():
    X = (1, 0, 0)
    ferrule = D.revolve("ferrule", [(0.0082, -0.0580), (0.0082, -0.0636), (0.0090, -0.0644), (0.0112, -0.0644),
                                    (0.0118, -0.0638), (0.0118, -0.0505), (0.0123, -0.0495, "k"),
                                    (0.0123, -0.0365, "k"), (0.0118, -0.0355), (0.0118, -0.0262), (0.0128, -0.0252),
                                    (0.0128, -0.0230), (0.0118, -0.0222)],
                        direction=X, segments=40, knurl=0.0010, mat="M_Brass_Aged",
                        band_mats=[None, None, "M_Brass_Polished", "M_Brass_Polished", None, None, None, None, None,
                                   "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished"],
                        cap_bottom=False, cap_top=False)
    bottom = D.revolve("bore", [(0.0, -0.0580), (0.0082, -0.0580)], direction=X, segments=16, mat="M_Steel_Dark",
                       cap_bottom=False, cap_top=False)
    sq = L.flat_shape("square", [L.rounded_rect(0.0085, 0.0085, 0.0006, 2)], mat="M_Bakelite")
    sq.data.transform(Matrix.Rotation(math.pi / 4, 4, "Z"))
    sq.data.transform(Matrix.Rotation(-math.pi / 2, 4, "Y"))         # face -X
    sq.location = (-0.0581, 0.0, 0.0)
    collar = D.revolve("collar", [(0.0118, -0.0222), (0.0122, -0.0218), (0.0122, -0.0196), (0.0116, -0.0192)],
                       direction=X, segments=28, mat="M_Enamel_Crimson", cap_bottom=False, cap_top=False)
    gp = [(0.0116, -0.0192), (0.0128, -0.0150), (0.0140, -0.0080)]
    for g in (0.0000, 0.0110, 0.0220):            # three crisp turned grooves
        r = 0.0142 + 0.00012 * (g / 0.011)
        gp += [(r, g - 0.0018), (r - 0.0011, g), (r, g + 0.0018)]
    gp += [(0.0147, 0.0320), (0.0134, 0.0395), (0.0160, 0.0465), (0.0173, 0.0535), (0.0169, 0.0598),
           (0.0141, 0.0657), (0.0090, 0.0697), (0.0040, 0.0713), (0.0, 0.0717)]
    grip = D.revolve("grip", gp, direction=X, segments=28, mat="M_Bakelite", cap_bottom=False)
    parts = [ferrule, bottom, sq, collar, grip]
    for s in (-1, 1):            # cross pin heads
        parts.append(L.rivet("pin", 0.0024, (-0.0300, s * 0.0118, 0.0), normal=(0, s, 0), segs=8))
    # brass end medallion with an engraved arrow (direction of the ON throw)
    med = D.revolve("medallion", [(0.0, 0.0), (0.0058, 0.0), (0.0058, 0.0006), (0.0050, 0.0010), (0.0, 0.0010)],
                    direction=X, loc=(0.0709, 0.0, 0.0), segments=16, mat="M_Brass_Polished")
    arrow = L.flat_shape("arrow", [[(0.0, 0.0034), (0.0024, 0.0006), (0.0009, 0.0006), (0.0009, -0.0030),
                                    (-0.0009, -0.0030), (-0.0009, 0.0006), (-0.0024, 0.0006)]], mat="M_Bakelite")
    arrow.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))        # face +X, arrow up (+Z)
    arrow.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
    arrow.location = (0.07195, 0.0, 0.0)
    parts += [med, arrow]
    return [M.join(parts, NAME)]


def main():
    D.item_main(NAME, build, shots=[
        ("", (0.05, -0.17, 0.07), (0.0, 0.0, 0.0), 50),
        ("_2", (-0.14, -0.06, 0.05), (-0.03, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
