"""battery_cell.glb — large 1970s "D" cell (R20, 34 x 61.5 mm) from Strand's gear box (inventory item).

Steel can with a crimped top, black seal washer and a chrome positive nub; a glossy printed paper label
wrap (black / crimson / cream bands) with MERIDIAN, 1.5 V, a lightning mark and the type line printed
around the can. Stands upright, + terminal up (Blender +Z) -- this also matches gear_box's
`battery_anchor` (parent it there with identity to lie in the cradle). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/battery_cell.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

NAME = "battery_cell"
R_CAN, R_LAB, HT = 0.0171, 0.01725, 0.0615


def build():
    can = L.lathe2("can", [(0.0, 0.0006), (0.0118, 0.0006), (0.0128, 0.0), (0.0160, 0.0), (0.0171, 0.0012),
                           (R_CAN, 0.0032), (R_CAN, 0.0578), (0.0171, 0.0600), (0.0163, 0.0611), (0.0148, 0.0611),
                           (0.0140, 0.0606), (0.0092, 0.0606), (0.0088, 0.0613), (0.0047, 0.0614), (0.0047, 0.0627),
                           (0.0040, 0.0633), (0.0, 0.0634)], segments=36, mat="M_Steel_Dark",
                    band_mats=[None, None, None, None, None, None, None, None, "M_Bakelite", "M_Bakelite",
                               "M_Bakelite", "M_Chrome", "M_Chrome", "M_Chrome", "M_Chrome", "M_Chrome"])
    bands = [(0.0030, "M_Bakelite"), (0.0062, "M_Enamel_Crimson"), (0.0150, "M_Paper"), (0.0478, "M_Enamel_Crimson"),
             (0.0528, "M_Bakelite"), (0.0582, None)]
    prof = [(R_CAN, 0.0030), (R_LAB, 0.0034)]
    mats = ["M_Bakelite"]
    for (z, m), (z2, _) in zip(bands[:-1], bands[1:]):
        prof.append((R_LAB, z2 - 0.0004 if z2 == 0.0582 else z2))
        mats.append(m)
    prof.append((R_CAN, 0.0582))
    mats.append("M_Bakelite")
    label = L.lathe2("label", prof, segments=36, band_mats=mats, mat="M_Paper", cap_bottom=False, cap_top=False)
    parts = [can, label]
    y = -R_LAB - 0.00004
    prints = [
        D.text("p_brand", "MERIDIAN", 0.0058, font=D.FONT_DISPLAY, mat="M_Bakelite", res=1, spacing=1.08,
               loc=(0.0, y, 0.0402), rot=L.front_rot()),
        D.text("p_volt", "1.5 V", 0.0088, font=D.FONT_COND_B, mat="M_Enamel_Crimson", res=1,
               loc=(0.0040, y, 0.0275), rot=L.front_rot()),
        D.text("p_type", "TYPE D · R20", 0.0030, font=D.FONT_COND_B, mat="M_Bakelite", res=1,
               loc=(0.0, y, 0.0185), rot=L.front_rot()),
        D.text("p_plus", "+", 0.0060, font=D.FONT_SANS_B, mat="M_Enamel_White", res=1,
               loc=(0.0, y, 0.0505), rot=L.front_rot()),
        D.text("p_minus", "–", 0.0060, font=D.FONT_SANS_B, mat="M_Enamel_White", res=1,
               loc=(0.0, y, 0.0047), rot=L.front_rot()),
    ]
    bolt = L.flat_shape("p_bolt", [[(0.0012, 0.0050), (-0.0016, -0.0002), (0.0001, -0.0002), (-0.0012, -0.0050),
                                    (0.0017, 0.0007), (0.0000, 0.0007)]], mat="M_Enamel_Crimson")
    L.to_front(bolt, y_back=y, x=-0.0108, z=0.0278)
    prints.append(bolt)
    for p in prints:
        D.wrap_to_cylinder(p, R_LAB + 0.00004)
    parts += prints
    return [M.join(parts, NAME)]


def main():
    D.item_main(NAME, build, shots=[("", (0.06, -0.12, 0.06), (0.0, 0.0, 0.002), 60)])


if __name__ == "__main__":
    main()
