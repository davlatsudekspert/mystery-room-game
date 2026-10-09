"""nursery_crystal.glb — the crystal grown in the working autoclave (Chapter 3 E2; also `cloudy_crystal`).

A clear hexagonal crystal, Ø 45 mm across its corners and 110 mm long, grown from Leyla's seed: its lower
end tapers into the brass seed collar (the same collar as seed_crystal.glb, Ø 15 mm), the prism carries a
slightly uneven rhombohedral point, and two small satellite crystals have grown on the taper.
Parts:
- `nursery_crystal` (root): the brass foot (seed collar), M_Brass_Aged.
- `crystal_body`: everything clear (M_Crystal), its own object. Pivot = the centre of its base on the collar's
  seat, identity rotation: the code grows it by scaling crystal_body 0.15 -> 1 about this pivot (8 s), and
  ItemDress swaps its material to a milky one for `cloudy_crystal`.
Stands upright, tip up, face +Z (Godot). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/nursery_crystal.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402
import mrlib as M  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch3_items as G  # noqa: E402

NAME = "nursery_crystal"
R = 0.0225                          # circumradius (Ø 45 mm)
Z0 = G.COLLAR_SEAT - 0.0004          # crystal base inside the collar's recess
Z_FULL = Z0 + 0.028                  # end of the lower taper
Z_PRISM = Z0 + 0.084                 # top of the prism
Z_TIP = Z0 + 0.110                   # apex: 110 mm crystal


def satellite(name, length, r, base, tilt_deg, yaw_deg):
    s = G.hex_crystal(name, [(0.0, r * 0.9), (length * 0.62, r), (length, 0.0)],
                      jitter=[1.0, 0.94, 1.05, 0.97, 1.02, 0.95])
    s.data.transform(Matrix.Translation(base) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")
                     @ Matrix.Rotation(math.radians(tilt_deg), 4, "Y"))
    return s


def build():
    foot = G.seed_collar(NAME)
    main = G.hex_crystal("crystal_main",
                         [(Z0, 0.0057), (Z0 + 0.008, 0.0105), (Z0 + 0.018, 0.0185), (Z_FULL, R),
                          (Z0 + 0.056, R * 1.01), (Z_PRISM, R * 0.99), (Z_TIP, 0.0)],
                         jitter=[1.0, 0.95, 1.04, 0.97, 1.03, 0.96], tip_offset=(0.0016, -0.0010))
    # two small crystals grown on the lower taper (left back and right front)
    s1 = satellite("sat_1", 0.022, 0.0042, (-0.0105, 0.0035, Z0 + 0.013), -38.0, 160.0)
    s2 = satellite("sat_2", 0.016, 0.0032, (0.0100, -0.0045, Z0 + 0.016), 34.0, -20.0)
    body = M.join([main, s1, s2], "crystal_body")
    M.set_origin(body, (0.0, 0.0, Z0))
    M.set_parent(body, foot)
    return [foot]


def post():
    D.resmooth(bpy.data.objects["crystal_body"], 8.0)
    D.resmooth(bpy.data.objects[NAME], 40.0)


def report():
    cb = bpy.data.objects["crystal_body"]
    G.report_point("crystal_body pivot (base centre on the collar seat)", obj_name="crystal_body")
    lo, hi = D.bounds([cb])
    print(f"[items3] crystal_body height {hi.z - lo.z:.4f}, width x {hi.x - lo.x:.4f}, depth {hi.y - lo.y:.4f}")
    lo, hi = D.bounds()
    G.report_point("item bottom (collar bottom centre)", point=(0.0, 0.0, lo.z))
    G.report_point("item top (apex)", point=(0.0, 0.0, hi.z))


def grown(scale):
    def fn():
        cb = bpy.data.objects["crystal_body"]
        cb.scale = (scale, scale, scale)
    return fn


def main():
    G.item_main(NAME, build, post=post, required=("crystal_body",), budget=1500, extra_report=report, shots=[
        ("", (0.13, -0.27, 0.13), (0.0, 0.0, 0.002), 70),
        ("_2", (0.0, -0.33, 0.035), (0.0, 0.0, 0.0), 70),
        ("_3", (0.12, -0.30, 0.12), (0.0, 0.0, -0.04), 85, grown(0.15)),
    ])


if __name__ == "__main__":
    main()
