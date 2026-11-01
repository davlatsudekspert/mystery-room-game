"""mallet.glb — the plumber's mallet of the Pump Room (puzzle N2 "tap a pipe, listen"; hands layer: mallet strike).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §7/§8/§12). A turned walnut handle with a leather-wrapped grip, a brass
ferrule and a lanyard hole, through a barrel head of walnut with two riveted brass bands and a hard-rubber face
on each end. 0.285 m long, head 0.115 x 0.058. Lies flat: handle along Blender +Y (Godot -Z), head axis along X,
heads strike faces at +/-X. Origin at the centre of mass.

    blender -b --factory-startup -P tools/blender/models/mallet.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2x as X  # noqa: E402,F401  (redirects the QA output folder)

NAME = "mallet"
HL, HR = 0.115, 0.029        # head length (X) and radius
HY = 0.215                   # head centre along the handle axis (Y)


def build():
    Y = (0, 1, 0)
    # handle: turned profile (r, y) from the butt to the neck that enters the head
    handle = D.revolve("handle", [(0.0, 0.0), (0.011, 0.0), (0.0135, 0.006), (0.0125, 0.020), (0.0115, 0.060),
                                  (0.0120, 0.100), (0.0128, 0.150), (0.0132, 0.175), (0.0145, 0.186),
                                  (0.0128, 0.200), (0.0125, HY), (0.0, HY)], direction=Y, segments=18,
                       mat="M_Wood_Walnut")
    grip = D.revolve("grip", [(0.0120, 0.026), (0.0132, 0.030), (0.0136, 0.100), (0.0136, 0.160), (0.0132, 0.164),
                              (0.0120, 0.168)], direction=Y, segments=18, mat="M_Leather")
    ferrule = D.revolve("ferrule", [(0.0138, 0.168), (0.0150, 0.171), (0.0150, 0.180), (0.0140, 0.183)],
                        direction=Y, segments=18, mat="M_Brass_Aged")
    # barrel head along X
    head = D.revolve("head", [(0.0, -HL / 2 + 0.008), (HR - 0.004, -HL / 2 + 0.008), (HR, -HL / 2 + 0.014),
                              (HR + 0.0015, -0.030), (HR + 0.002, 0.0), (HR + 0.0015, 0.030), (HR, HL / 2 - 0.014),
                              (HR - 0.004, HL / 2 - 0.008), (0.0, HL / 2 - 0.008)],
                     direction=(1, 0, 0), loc=(0, HY, 0), segments=28, mat="M_Wood_Walnut")
    parts = [handle, grip, ferrule, head]
    for sx in (-1, 1):
        # rubber striking face (disc proud of the end) and a brass band behind it
        face = D.revolve(f"face{sx}", [(0.0, 0.0), (HR - 0.002, 0.0), (HR, 0.004), (HR - 0.004, 0.009), (0.0, 0.009)],
                         direction=(sx, 0, 0), loc=(sx * (HL / 2 - 0.009), HY, 0), segments=28, mat="M_Rubber")
        band = D.revolve(f"band{sx}", [(HR - 0.0005, -0.007), (HR + 0.0045, -0.006), (HR + 0.0045, 0.006),
                                       (HR - 0.0005, 0.007)], direction=(1, 0, 0),
                         loc=(sx * (HL / 2 - 0.028), HY, 0), segments=28, mat="M_Brass_Aged")
        parts += [face, band]
        for k in range(4):                      # rivet heads on the bands
            a = math.pi / 4 + k * math.pi / 2
            rv = L.rivet(f"rv{sx}{k}", 0.0021, (sx * (HL / 2 - 0.028), HY + (HR + 0.0045) * math.cos(a),
                                                (HR + 0.0045) * math.sin(a)), normal=(0, math.cos(a), math.sin(a)),
                         mat="M_Brass_Polished", segs=6)
            parts.append(rv)
    # lanyard hole ring at the butt
    ring = M.torus("lanyard", 0.0075, 0.0017, loc=(0, 0.004, 0), rot=(math.pi / 2, 0, 0), major_seg=14, minor_seg=5,
                   mat="M_Brass_Aged")
    parts.append(ring)
    return parts


def main():
    D.item_main(NAME, build, shots=[("", (0.20, -0.20, 0.17), (0.0, 0.01, 0.0), 70),
                                    ("_2", (0.02, 0.19, 0.20), (0.0, 0.07, 0.0), 70)])


if __name__ == "__main__":
    main()
