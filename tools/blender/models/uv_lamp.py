"""uv_lamp.glb — Leyla's 1960s UV flashlight (inventory item; also used as `uv_lamp_empty`).

Green-grey enamelled steel body (wide enough for the D cell), ribbed rubber grip, knurled chrome tail cap
with a lanyard ring, chrome reflector head with a knurled bezel, a thumb slide switch and a violet enamel
"UV" badge. The violet Wood's-glass lens is a separate child object `uv_lens` (M_Glass_UV) so the game
can light it. Lies along Blender X with the head at +X. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/uv_lamp.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "uv_lamp"
R_B = 0.0198


def build():
    X = (1, 0, 0)
    prof = [(0.0, -0.0900), (0.0100, -0.0900), (0.0165, -0.0886), (0.0195, -0.0858),
            (0.0207, -0.0838, "k"), (0.0207, -0.0718, "k"), (0.0201, -0.0702), (0.0194, -0.0696),
            (R_B, -0.0690), (R_B, -0.0610),
            (0.0210, -0.0600, "k"), (0.0210, -0.0140, "k"), (R_B, -0.0130),
            (R_B, 0.0120), (0.0206, 0.0170), (0.0256, 0.0340), (0.0289, 0.0480), (0.0299, 0.0522),
            (0.0316, 0.0538, "k"), (0.0316, 0.0662, "k"), (0.0306, 0.0688), (0.0272, 0.0696), (0.0268, 0.0680),
            (0.0262, 0.0656)]
    mats = ["M_Chrome"] * 8 + ["M_Steel_Painted"] + ["M_Rubber"] * 3 + ["M_Steel_Painted"] + \
        ["M_Chrome"] * 10            # tail cap | body ring | ribbed grip | body | head
    shell = D.revolve("shell", prof, direction=X, segments=28, knurl=0.0014, band_mats=mats, mat="M_Chrome",
                      cap_bottom=False, cap_top=False)
    refl = D.revolve("reflector", [(0.0262, 0.0656), (0.0170, 0.0560), (0.0080, 0.0480), (0.0, 0.0470)],
                     direction=X, segments=20, mat="M_Chrome", cap_bottom=False)
    bulb = L.lathe2("bulb", [(0.0, 0.0), (0.0030, 0.0005), (0.0046, 0.0040), (0.0040, 0.0075), (0.0, 0.0095)],
                    segments=10, mat="M_Glass")
    D.aim(bulb, X)
    bulb.location = (0.0470, 0.0, 0.0)
    parts = [shell, refl, bulb]
    # thumb slide switch on top
    base = L.curve_solid("sw_base", [L.rounded_rect(0.032, 0.0105, 0.004, 3)], 0.0022, bevel=0.0007,
                         mat="M_Chrome")
    base.location = (-0.002, 0.0, R_B - 0.0006)
    slot = L.flat_shape("sw_slot", [L.rounded_rect(0.024, 0.0032, 0.0015, 3)], mat="M_Bakelite",
                        loc=(-0.002, 0.0, R_B + 0.00165))
    knob = L.curve_solid("sw_knob", [L.rounded_rect(0.0095, 0.0080, 0.0025, 3)], 0.0034, bevel=0.0010,
                         bevel_res=1, mat="M_Bakelite")
    knob.location = (-0.0085, 0.0, R_B + 0.0016)
    parts += [base, slot, knob]
    for k in range(3):
        parts.append(M.box("rib", (0.0010, 0.0066, 0.0007), loc=(-0.0110 + k * 0.0025, 0.0, R_B + 0.0052),
                           mat="M_Bakelite", bevel=0.0))
    # violet enamel "UV" badge facing the viewer (-Y), wrapped onto the body
    badge = L.flat_shape("badge", [L.circle(0.0062, 16)], mat="M_Enamel_Violet")
    badge.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    badge.location = (0.0030, -R_B - 0.00005, 0.0)
    ring = L.flat_shape("badge_ring", L.circle_line(0.0066, 0.0010, 16), mat="M_Chrome")
    ring.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    ring.location = (0.0030, -R_B - 0.00006, 0.0)
    uv = D.text("badge_txt", "UV", 0.0062, font=D.FONT_SANS_B, mat="M_Enamel_White", res=1,
                loc=(0.0030, -R_B - 0.00008, -0.0002), rot=L.front_rot())
    # wrap the badge around the body: the body axis is X, so bend in the YZ plane
    for o in (badge, ring, uv):
        M.apply_transform(o)
        for v in o.data.vertices:
            a = v.co.z / R_B
            r = R_B + (-R_B - v.co.y) + 0.00005
            v.co.y = -r * math.cos(a)
            v.co.z = r * math.sin(a)
        parts.append(o)
    # lanyard eyelet + ring at the tail
    eye = M.box("eyelet", (0.006, 0.0024, 0.006), loc=(-0.0920, 0.0, 0.0), mat="M_Chrome", bevel=0.0008,
                segments=1)
    lan = M.torus("lanyard", 0.0068, 0.0011, loc=(-0.0995, 0.0, -0.0010), rot=(math.pi / 2, 0.25, 0.0),
                  major_seg=14, minor_seg=5, mat="M_Chrome")
    parts += [eye, lan]
    lamp = M.join(parts, NAME)
    lens = D.revolve("uv_lens", [(0.0, 0.0662), (0.0270, 0.0662), (0.0270, 0.0688), (0.0180, 0.0697),
                                 (0.0, 0.0702)], direction=X, segments=24, mat="M_Glass_UV")
    M.set_origin(lens, (0.0685, 0.0, 0.0))
    M.set_parent(lens, lamp)
    return [lamp]


def post():
    D.resmooth(M.bpy.data.objects[NAME], 25.0)


def main():
    D.item_main(NAME, build, post=post, shots=[
        ("", (0.07, -0.20, 0.08), (0.0, 0.0, 0.0), 50),
        ("_2", (0.20, -0.07, 0.04), (0.02, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
