"""radio_valve.glb — miniature noval (B9A, EL84-style) radio valve from Strand's safe (inventory item).

Glass envelope with real wall thickness and a pinched exhaust tip, silver getter flash in the dome, nine
pins with the keying gap, two grey anode plates with wings, micas, support rods, cathode sleeve and a white
"MERIDIAN / EL 84" print on the glass. Stands upright (pins down, Blender -Z). Same geometry as the radio's
`valve_installed` (lib_devices.valve). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/radio_valve.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

NAME = "radio_valve"


def build():
    v = D.valve("valve_core", (0, 0, 0), quality="item")
    y = -D.VALVE_R - 0.00004
    t1 = D.text("print1", "MERIDIAN", 0.0030, font=D.FONT_DISPLAY, mat="M_Enamel_White", res=1, spacing=1.1,
                loc=(0.0, y, 0.0185), rot=L.front_rot())
    t2 = D.text("print2", "EL 84", 0.0036, font=D.FONT_COND_B, mat="M_Enamel_White", res=1,
                loc=(0.0, y, 0.0140), rot=L.front_rot())
    for t in (t1, t2):
        D.wrap_to_cylinder(t, D.VALVE_R + 0.00004)
    obj = M.join([v, t1, t2], NAME)
    return [obj]


def main():
    D.item_main(NAME, build, shots=[("", (0.07, -0.13, 0.045), (0.0, 0.0, 0.0), 60)])


if __name__ == "__main__":
    main()
