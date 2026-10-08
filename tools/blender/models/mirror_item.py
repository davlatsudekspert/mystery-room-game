"""mirror_item.glb — Strand's round signal mirror (inventory item; mounts on mirror stand B).

0.22 m brass frame with a beaded front lip and cove, M_Chrome mirror face, brass back plate with a
turned boss, engraved rings, four screws and "MERIDIAN INSTITUTE · LUMEN SIGNAL MIRROR Nº 2" around it,
and a turned brass mounting pin under the frame (drops into the stand's gimbal socket).
Stands upright: mirror face toward Blender -Y (Godot +Z), pin down. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/mirror_item.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "mirror_item"
R_OUT = 0.110
Y_BACK = 0.008          # back plate plane (frame spans y = +0.008 .. -0.0105)


def build():
    F = (0, -1, 0)
    prof = [(0.0, -0.0045), (0.0115, -0.0045), (0.0160, -0.0020), (0.0165, 0.0), (0.0960, 0.0), (0.1060, 0.0010),
            (R_OUT, 0.0040), (R_OUT, 0.0100), (0.1092, 0.0136), (0.1072, 0.0162), (0.1044, 0.0170),
            (0.1020, 0.0158), (0.1000, 0.0140), (0.0978, 0.0150), (0.0957, 0.0140), (0.0946, 0.0104),
            (0.0, 0.0100)]
    mats = ["M_Brass_Polished", "M_Brass_Polished", "M_Brass_Aged", "M_Brass_Aged", "M_Brass_Aged", "M_Brass_Aged",
            "M_Brass_Aged", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Aged",
            "M_Brass_Aged", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished", "M_Chrome"]
    frame = D.revolve("frame", prof, direction=F, loc=(0, Y_BACK, 0), segments=44, band_mats=mats)
    parts = [frame]
    # back: engraved rings, screws, lettering (all facing +Y)
    back = []
    back.append(L.flat_shape("ring1", L.circle_line(0.0880, 0.0008, 40), mat="M_Bakelite"))
    back.append(L.flat_shape("ring2", L.circle_line(0.0300, 0.0008, 24), mat="M_Bakelite"))
    txt = D.text_on_circle("back_txt", "MERIDIAN INSTITUTE · LUMEN SIGNAL MIRROR Nº 2", 0.0048, 0.0790,
                           start_deg=90.0, step_deg=5.3, mat="M_Bakelite")
    back.append(txt)
    for o in back:   # drawn in XY facing +Z -> back plane facing +Y (mirror x so text reads from behind)
        o.data.transform(Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
        o.location = (0.0, Y_BACK + 0.00006, 0.0)
        parts.append(o)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        parts.append(L.screw("bscrew", 0.0040, (0.0620 * math.cos(a), Y_BACK, 0.0620 * math.sin(a)),
                             normal=(0, 1, 0), slot_angle=a, segs=8))
    # mounting pin under the frame
    pin = D.revolve("pin", [(0.0, 0.0), (0.0080, 0.0), (0.0080, 0.0090), (0.0092, 0.0110), (0.0092, 0.0160),
                            (0.0062, 0.0182), (0.0050, 0.0200), (0.0050, 0.0400), (0.0034, 0.0440), (0.0, 0.0452)],
                    direction=(0, 0, -1), loc=(0.0, Y_BACK - 0.0060, -R_OUT + 0.0030), segments=16,
                    mat="M_Brass_Aged", band_mats=[None, None, "M_Brass_Polished", "M_Brass_Polished",
                                                   "M_Brass_Polished", None, None, None, None])
    groove = D.revolve("groove", [(0.0051, 0.0300), (0.0044, 0.0310), (0.0044, 0.0330), (0.0051, 0.0340)],
                       direction=(0, 0, -1), loc=(0.0, Y_BACK - 0.0060, -R_OUT + 0.0030), segments=16,
                       mat="M_Steel_Dark", cap_bottom=False, cap_top=False)
    parts += [pin, groove]
    return [M.join(parts, NAME)]


def main():
    D.item_main(NAME, build, shots=[
        ("", (0.20, -0.48, 0.12), (0.0, 0.0, -0.01), 50),
        ("_2", (-0.22, 0.42, 0.06), (0.0, 0.0, -0.01), 50),
    ])


if __name__ == "__main__":
    main()
