"""reverse_pawl.glb — the reverse pawl Strand made for the chronometer and never dared to fit (Chapter 4, group H; puzzle P9 `pawl`).

A brass ratchet pawl 85 mm long lying flat: a tapered arm with a barbed hook at one end (the tooth is cut the wrong way round, so the escape wheel can run backwards), a turned pivot boss with a
through hole at the other end, an engraved arrow pointing along the arm toward the pivot (backwards), two rivets and a small steel return spring on a post at the tail. The pawl seat on the master
desk (`pawl_mount`) takes it with the boss over the spring post. 0.088 x 0.028 x 0.010 m. Lies flat (hero face up = Blender +Z = Godot +Y); the arm runs along X, the hook toward +X (Godot +X).
Origin at the centre of mass. Slots: M_Brass_Aged + M_Steel_Dark (spring, post).
    blender -b --factory-startup -P tools/blender/models/reverse_pawl.py [-- --no-render]
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
import lib_ch4_items as H  # noqa: E402  (sets the QA output folder to qa/blender/ch4)
from mathutils import Matrix, Vector  # noqa: E402

NAME = "reverse_pawl"
BRASS, STEEL = "M_Brass_Aged", "M_Steel_Dark"
PX = -0.034                                      # the pivot boss centre (x)


def arm_outline():
    """The pawl's arm, CCW: a broad pivot end, a tapered arm, a barbed hook (tip down, toward -Y) at +X."""
    return [(PX - 0.004, 0.0105), (0.000, 0.0085), (0.026, 0.0060), (0.038, 0.0052), (0.0455, 0.0030), (0.0475, -0.0020), (0.0445, -0.0125), (0.0400, -0.0090), (0.0385, -0.0035),
            (0.0300, -0.0030), (0.000, -0.0050), (PX + 0.002, -0.0110), (PX - 0.006, -0.0112), (PX - 0.0105, -0.0060), (PX - 0.0115, 0.0030)]


def build():
    parts = []
    arm = G.plate_xy("pawl", [arm_outline()], 0.0050, 0.0, BRASS, bevel=0.0007)
    parts.append(arm)
    # the pivot boss: a ring (hole through) standing higher
    boss = G.plate_xy("boss", [L.circle(0.0100, 28, cx=PX, cy=0.0), list(reversed(L.circle(0.0040, 16, cx=PX, cy=0.0)))], 0.0072, 0.0, BRASS, bevel=0.0007)
    parts.append(boss)
    rim = G.plate_xy("bossrim", [L.circle(0.0078, 28, cx=PX, cy=0.0), list(reversed(L.circle(0.0050, 16, cx=PX, cy=0.0)))], 0.0010, 0.0072, BRASS, bevel=0.0002)
    parts.append(rim)
    # the engraved arrow: pointing toward the pivot (-X), raised 0.8 mm on the arm
    # (a left-pointing arrow: shaft from +X to -X, head at -X)
    arrow = [(-0.0160, 0.0007), (-0.0070, 0.0042), (-0.0070, 0.0017), (0.0150, 0.0017), (0.0150, -0.0003), (-0.0070, -0.0003), (-0.0070, -0.0028)]
    parts.append(G.plate_xy("arrow", [arrow], 0.0008, 0.0050, BRASS, bevel=0.0001))
    # two rivets on the arm and a small tooth guard plate near the hook
    for x in (0.010, 0.026):
        parts.append(M.cylinder("rv", 0.0018, 0.0010, loc=(x, 0.0, 0.0050 + 0.0005), mat=BRASS, verts=8, bevel=0.0))
    # the steel return spring on a post at the tail: a post and four coils
    sx, sy = PX - 0.0055, 0.0150
    parts.append(M.cylinder("post", 0.0024, 0.0100, loc=(sx, sy, 0.0050), mat=STEEL, verts=8, bevel=0.0))
    for k in range(4):
        parts.append(M.torus(f"coil{k}", 0.0042, 0.0009, loc=(sx, sy, 0.0008 + 0.0019 * k), major_seg=12, minor_seg=4, mat=STEEL))
    # a leaf arm of the spring pressing on the pawl
    parts.append(G.plate_xy("leaf", [[(sx - 0.0010, sy - 0.0040), (sx + 0.0010, sy - 0.0040), (PX + 0.004, 0.0085), (PX + 0.0020, 0.0095)]], 0.0010, 0.0050, STEEL, bevel=0.0001))
    main_parts = [p for p in parts if p.name.startswith(("pawl", "boss", "bossrim", "arrow", "rv"))]
    spring_parts = [p for p in parts if p.name.startswith(("post", "coil", "leaf"))]
    root = M.join(main_parts, NAME)
    spring = M.join(spring_parts, "spring")
    M.set_parent(spring, root)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 34.0), required=("spring",), budget=1800, surf_budget=3, mat_budget=2, shots=[
        ("", (0.07, -0.16, 0.14), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, -0.001, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
