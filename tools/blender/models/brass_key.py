"""brass_key.glb — small ornate brass key from Strand's safe (opens the desk's secret keyhole).

Scalloped quatrefoil bow with a quatrefoil piercing and three round piercings, an engraved border line,
turned collar beads, round shank with a mid ring, a stepped bit with two wards and a slot, and a domed
tip. 66 mm long. Lies flat (broad faces +/-Z), shank along Blender X with the bit at +X hanging toward -Y.
Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/brass_key.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

NAME = "brass_key"
T = 0.0026           # plate thickness (bow, bit)
BX = -0.0215         # bow centre


def scallop(r0, r1, lobes, n, cx, cy, phase=0.0):
    return [(cx + (r0 + r1 * math.cos(lobes * t + phase)) * math.cos(t),
             cy + (r0 + r1 * math.cos(lobes * t + phase)) * math.sin(t)) for t in (math.tau * i / n for i in range(n))]


def build():
    outer = scallop(0.0108, 0.0021, 4, 56, BX, 0.0)
    hole = scallop(0.0040, 0.0011, 4, 24, BX, 0.0, phase=math.pi)
    loops = [outer, hole]
    for k in range(3):                              # piercings in the three free lobes
        a = math.pi / 2 + k * math.pi / 2
        loops.append(L.circle(0.0016, 8, cx=BX + 0.0091 * math.cos(a), cy=0.0091 * math.sin(a)))
    bow = L.curve_solid("bow", loops, T, bevel=0.0006, bevel_res=1, mat="M_Brass_Polished")
    bow.location = (0, 0, -T / 2)
    line = L.flat_shape("engrave", [scallop(0.0096, 0.0019, 4, 56, BX, 0.0), scallop(0.0090, 0.0018, 4, 56, BX, 0.0)],
                        mat="M_Bakelite", loc=(0, 0, T / 2 + 0.00004))
    X = (1, 0, 0)
    shank = D.revolve("shank", [(0.0024, -0.0110), (0.0033, -0.0100), (0.0037, -0.0088), (0.0030, -0.0076),
                                (0.0026, -0.0064), (0.0033, -0.0054), (0.0033, -0.0044), (0.0025, -0.0034),
                                (0.0021, -0.0020), (0.0021, 0.0090), (0.0026, 0.0098), (0.0026, 0.0114),
                                (0.0021, 0.0122), (0.0021, 0.0318), (0.0017, 0.0336), (0.0008, 0.0345),
                                (0.0, 0.0347)], direction=X, segments=14, mat="M_Brass_Polished", cap_bottom=False)
    bit_pts = [(0.0195, 0.0), (0.0195, -0.0104), (0.0222, -0.0104), (0.0222, -0.0076), (0.0244, -0.0076),
               (0.0244, -0.0104), (0.0274, -0.0104), (0.0274, -0.0088), (0.0302, -0.0088), (0.0302, 0.0)]
    slot = [(0.0255, -0.0018), (0.0263, -0.0018), (0.0263, -0.0058), (0.0255, -0.0058)]
    bit = L.curve_solid("bit", [bit_pts, slot], T, bevel=0.0004, bevel_res=0, mat="M_Brass_Polished")
    bit.location = (0, 0, -T / 2)
    return [M.join([bow, line, shank, bit], NAME)]


def main():
    D.item_main(NAME, build, shots=[("", (0.03, -0.11, 0.12), (0.0045, -0.002, 0.0), 85)])


if __name__ == "__main__":
    main()
