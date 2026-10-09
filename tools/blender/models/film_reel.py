"""film_reel.glb — Strand's 16 mm film reel (torn reel from the booth, spliced at the film splicer,
threaded on the film projector).

A 7-inch (Ø 180 mm) pressed-steel 16 mm reel: two 0.8 mm flanges, each cut into three straight spokes
(12 mm wide) by three windows, a steel hub drum (Ø 50 mm) with the square 8 mm drive hole and its keyway
right through, wound with amber film (M_Film) to Ø 144 mm. The film pack shows its winding steps through
the windows; the film's end is held by a strip of white splicing tape.
Stands on its rim, the reel face toward Blender -Y (Godot +Z), the axis along Godot Z.
Origin at the centre of mass (= the reel axis centre).
    blender -b --factory-startup -P tools/blender/models/film_reel.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "film_reel"
R = 0.090             # flange radius
FT = 0.0008           # flange thickness
HW = 0.0088           # half width between the flange inner faces (16 mm film + play)
HUB_R = 0.025
PACK_R = 0.072
SPOKE_W = 0.012
R_IN, R_OUT = 0.031, 0.080       # window radii


def window(phi0, phi1, n_in=5, n_out=10):
    """Window between the spokes at phi0 and phi1 (CCW), bounded by lines offset SPOKE_W / 2 from them."""
    h = SPOKE_W / 2
    d_in = math.asin(h / R_IN)
    d_out = math.asin(h / R_OUT)
    pts = []
    for i in range(n_out):          # outer arc, CCW
        a = phi0 + d_out + (phi1 - phi0 - 2 * d_out) * i / (n_out - 1)
        pts.append((R_OUT * math.cos(a), R_OUT * math.sin(a)))
    for i in range(n_in):           # inner arc, back (CW)
        a = phi1 - d_in - (phi1 - phi0 - 2 * d_in) * i / (n_in - 1)
        pts.append((R_IN * math.cos(a), R_IN * math.sin(a)))
    return list(reversed(pts))


def drive_hole():
    """Square 8 mm drive hole with a keyway on one side (toward +Y in the flat build)."""
    s = 0.004
    return [(-s, -s), (s, -s), (s, s), (0.0011, s), (0.0011, s + 0.0018), (-0.0011, s + 0.0018), (-0.0011, s), (-s, s)]


def flange(name, z_mid):
    loops = [L.circle(R, 64), drive_hole()]
    for k in range(3):
        phi = math.pi / 2 + k * math.tau / 3
        loops.append(window(phi, phi + math.tau / 3))
    fl = L.curve_solid(name, loops, FT, bevel=0.0, mat="M_Chrome")
    fl.location = (0, 0, z_mid - FT / 2)
    M.apply_transform(fl)
    return fl


def build():
    zf = HW + FT / 2
    front = flange(NAME, zf)              # the face seen by the player (+Z here, -Y after the stand-up)
    back = flange("flange_back", -zf)
    # embossed stiffening ring and hub boss on each outer face
    parts = [back]
    for z, d in ((zf + FT / 2, 1), (-zf - FT / 2, -1)):
        boss = L.lathe2("boss", [(HUB_R + 0.0035, 0.0), (HUB_R + 0.0020, 0.0007 * d), (0.0072, 0.0007 * d)],
                        segments=32, mat="M_Chrome", cap_bottom=False, cap_top=False)
        rib = L.lathe2("rib", [(R - 0.0028, 0.0), (R - 0.0048, 0.0005 * d), (R - 0.0068, 0.0)], segments=64, mat="M_Chrome", cap_bottom=False, cap_top=False)
        for o in (boss, rib):
            o.location = (0, 0, z)
            M.apply_transform(o)
            if d < 0:
                o.data.flip_normals()
            parts.append(o)
    # hub drum with the square drive hole straight through
    hub = L.curve_solid("hub", [L.circle(HUB_R, 40), drive_hole()], 2 * HW + 0.0002, bevel=0.0, mat="M_Steel_Dark")
    hub.location = (0, 0, -HW - 0.0001)
    M.apply_transform(hub)
    L.drop_faces(hub, lambda c, n: abs(n.z) > 0.99)          # end caps are buried in the flanges
    parts.append(hub)
    # film pack: amber annulus with winding steps on both sides
    w = HW - 0.0004
    pack = L.lathe2("film_pack", [(HUB_R, -w), (0.038, -w + 0.00010), (0.052, -w - 0.00006), (0.063, -w + 0.00012),
                                  (PACK_R, -w + 0.0001), (PACK_R, w - 0.0001), (0.061, w + 0.00012), (0.048, w - 0.00006),
                                  (0.036, w + 0.00010), (HUB_R, w)],
                    segments=40, mat="M_Film", cap_bottom=False, cap_top=False)
    parts.append(pack)
    # splicing tape holding the film's end (a short band on the pack's rim)
    tape = L.lathe2("end_tape", [(PACK_R + 0.00008, -w + 0.0012), (PACK_R + 0.00008, w - 0.0012)], segments=90,
                    mat="M_Paper", cap_bottom=False, cap_top=False)
    L.drop_faces(tape, lambda c, n: abs(math.atan2(c.y, c.x) - math.radians(-35)) > 0.09)
    parts.append(tape)
    hard = M.join(parts, "reel_body")
    # stand up: flat build (+Z face) -> face toward -Y, the build's +Y becomes up (+Z)
    rot = Matrix.Rotation(math.pi / 2, 4, "X")
    for o in (front, hard):
        o.data.transform(rot)
    M.set_parent(hard, front)
    return [front]


def main():
    C.item_main(NAME, build, shots=[
        ("", (0.20, -0.36, 0.14), (0.0, 0.0, 0.0), 50),
        ("_2", (-0.10, -0.06, 0.40), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
