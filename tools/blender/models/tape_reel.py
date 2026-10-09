"""tape_reel.glb — Leyla's 5-inch tape reel (three of them: 1996, 1997, 1998; same model, label swapped).

A glossy black plastic (M_Lacquer_Black) 5-inch reel (Ø 127 mm): two 1.2 mm flanges with a stiffening
rim and three kidney windows each, a 54 mm hub with a keyed spindle hole (three keyways), wound with
brown 1/4-inch tape (M_Tape) to Ø 104 mm, the tape end held by a strip of splicing tape; the pack shows
its slightly uneven winding through the windows.
`label` is its own object: a round paper hub label (outer Ø 51 mm, spindle hole Ø 9 mm) on the top
flange, UV 0..1 over its bounding square (u left -> right, v bottom -> top seen from above with the
reel's 'top' toward Godot -Z), default slot M_Decal_TapeLabel_1996; ItemDress sets the year.
Lies flat, label side up (Godot +Y). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/tape_reel.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "tape_reel"
C.LIGHTS = C.SOFT
R = 0.0635            # flange radius (5 inch reel)
FT = 0.0012           # flange thickness
GAP = 0.0070          # between the flanges (6.35 mm tape + play)
Z1 = FT               # bottom flange top
Z2 = FT + GAP         # top flange bottom
ZT = Z2 + FT          # top face
HUB_R = 0.027
PACK_R = 0.052
HOLE_R = 0.0040
LABEL_R, LABEL_HOLE = 0.0255, 0.0045


def spindle_hole():
    """Centre hole with three keyways (at 90, 210 and 330 deg)."""
    kw = 0.0008 / HOLE_R          # half-width of a keyway as an angle
    rk = HOLE_R + 0.0013          # keyway depth
    steps = 7
    loop = []
    for k in range(3):
        a0 = math.pi / 2 + k * math.tau / 3
        loop += [(rk * math.cos(a0 - kw), rk * math.sin(a0 - kw)), (rk * math.cos(a0 + kw), rk * math.sin(a0 + kw))]
        a_start, a_end = a0 + kw, a0 + math.tau / 3 - kw
        for j in range(steps + 1):
            a = a_start + (a_end - a_start) * j / steps
            loop.append((HOLE_R * math.cos(a), HOLE_R * math.sin(a)))
    return loop


def windows():
    out = []
    for k in range(3):
        ac = math.radians(30 + k * 120)
        out.append(L.kidney(0.0330, 0.0552, ac - math.radians(38), ac + math.radians(38), n_arc=9))
    return out


def flange(name, z0):
    loops = [L.circle(R, 60), spindle_hole()] + windows()
    fl = L.curve_solid(name, loops, FT, bevel=0.0, mat="M_Lacquer_Black")
    fl.location = (0, 0, z0)
    M.apply_transform(fl)
    return fl


def build():
    parts = []
    bottom = flange(NAME, 0.0)
    top = flange("flange_top", Z2)
    parts.append(top)
    # stiffening rims (outer lip on the outside faces) and the hub boss rings
    for z, d in ((0.0, -1), (ZT, 1)):
        rim = L.lathe2("rim", [(R - 0.0001, 0.0), (R - 0.0016, 0.0005 * d), (R - 0.0026, 0.0)],
                       segments=60, mat="M_Lacquer_Black", cap_bottom=False, cap_top=False)
        rim.location = (0, 0, z)
        M.apply_transform(rim)
        if d < 0:
            rim.data.flip_normals()
        parts.append(rim)
    # hub drum between the flanges, with three spokes toward the spindle
    hub = L.lathe2("hub", [(HUB_R, Z1 - 0.0001), (HUB_R, Z2 + 0.0001)], segments=40, mat="M_Lacquer_Black",
                   cap_bottom=False, cap_top=False)
    parts.append(hub)
    # wound tape: annular pack with a slightly uneven top (two layer steps)
    pz0, pz1 = Z1 + 0.0004, Z2 - 0.0003
    pack = L.lathe2("tape_pack", [(HUB_R, pz0), (0.040, pz0 - 0.00008), (PACK_R, pz0 + 0.00006),
                                  (PACK_R, pz1 - 0.00006), (0.0415, pz1 + 0.00008), (HUB_R, pz1)],
                    segments=48, mat="M_Tape", cap_bottom=False, cap_top=False)
    parts.append(pack)
    # tape tail: the free end lies against the pack, held by a small strip of splicing tape
    tab = L.lathe2("splice_tab", [(PACK_R + 0.00005, pz0 + 0.0008), (PACK_R + 0.00005, pz1 - 0.0008)], segments=60,
                   mat="M_Paper", cap_bottom=False, cap_top=False)
    L.drop_faces(tab, lambda c, n: abs(math.atan2(c.y, c.x) - math.radians(-20)) >= 0.07)
    parts.append(tab)
    hard = M.join(parts, "reel_body")
    M.set_parent(hard, bottom)
    # the hub label (own object)
    lab = L.flat_shape("label", [L.circle(LABEL_R, 48), L.circle(LABEL_HOLE, 20)], mat="M_Decal_TapeLabel_1996",
                       loc=(0, 0, ZT + 0.00005))
    M.apply_transform(lab)
    M.set_parent(lab, bottom)
    return [bottom]


def post():
    C.uv_rect_all(bpy.data.objects["label"], -LABEL_R, LABEL_R, -LABEL_R, LABEL_R, axis="Z")


def main():
    C.item_main(NAME, build, post=post, required=("label",), shots=[
        ("", (0.10, -0.17, 0.16), (0.0, 0.004, 0.0), 50),
        ("_2", C.inspect_cam(0.30), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
