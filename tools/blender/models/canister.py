"""canister.glb — pneumatic-post carrier for the Archive B tube station (docs/models/ch2.md section 5).

A brass carrier, 0.07 diameter x 0.22 long: leather sealing bands at both ends (the widest part, so the
carrier rides the 0.04-radius glass tube on them), a rolled-bead brass body with a crimson line band,
a domed brass foot and a domed end cap on a back hinge with a spring latch at the front.

Model space (Godot): origin = the centre, long axis = +Y, cap at +Y, hinge at -Z, latch at +Z.
Parts:
  canister        body (static)
  canister_cap    the end cap; pivot on the hinge axis (0, 0.0915, -0.0335); opens with a NEGATIVE
                  angle about local +X (about -110 deg fully open). Not animated by the game yet.
    blender -b --factory-startup -P tools/blender/models/canister.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices1 as C  # noqa: E402

NAME = "canister"
BUDGET = 1200
SEG = 16
R_BAND = 0.035                 # leather bands = the 0.07 diameter
R_BODY = 0.0305
HINGE_G = (0.0, 0.0915, -0.0335)


def build_body():
    c = 0.0012
    prof = [
        (0.0, -0.1100), (0.0200, -0.1092), (0.0285, -0.1065), (0.0318, -0.1020),                 # foot
        (R_BAND - c, -0.1000), (R_BAND, -0.0990), (R_BAND, -0.0745), (R_BAND - c, -0.0735),      # leather
        (R_BODY, -0.0722),
        (R_BODY, -0.0480), (R_BODY + 0.0016, -0.0465), (R_BODY, -0.0450),                       # bead
        (R_BODY - 0.0004, -0.0200), (R_BODY - 0.0004, 0.0200),                                    # line band
        (R_BODY, 0.0450), (R_BODY + 0.0016, 0.0465), (R_BODY, 0.0480),                          # bead
        (R_BODY, 0.0590),
        (R_BAND - c, 0.0602), (R_BAND, 0.0612), (R_BAND, 0.0848), (R_BAND - c, 0.0858),          # leather
        (0.0322, 0.0862), (0.0322, 0.0900), (0.0, 0.0905),
    ]
    bands = []
    for k in range(len(prof) - 1):
        r0, r1 = prof[k][0], prof[k + 1][0]
        if r0 >= R_BAND - c - 1e-9 and r1 >= R_BAND - c - 1e-9:
            bands.append("M_Leather")
        elif abs(r0 - (R_BODY - 0.0004)) < 1e-9 and abs(r1 - (R_BODY - 0.0004)) < 1e-9:
            bands.append("M_Enamel_Crimson")
        else:
            bands.append(None)
    body = L.lathe2("can_body", prof, segments=SEG, mat="M_Brass_Polished", band_mats=bands, cap_bottom=False,
                    cap_top=False)
    C.sm(body, 40.0)
    # stitch lines on the leather (thin dark rings would cost tris: two flat seams instead)
    parts = [body]
    for z in (-0.087, 0.073):
        seam = L.lathe2("seam", [(R_BAND + 0.0002, z - 0.0006), (R_BAND + 0.0002, z + 0.0006)], segments=SEG,
                        mat="M_Bakelite", cap_bottom=False, cap_top=False)
        C.sm(seam, 40.0)
        parts.append(seam)
    # hinge leaf + knuckle on the back (Godot -Z = Blender +Y), latch keeper at the front
    hb = C.GV(HINGE_G)
    leaf = L.box_mm("hleaf", (-0.008, hb.y - 0.0012, 0.078), (0.008, hb.y + 0.0004, 0.089), mat="M_Brass_Aged",
                    bevel=0.0)
    knuckle = L.lathe2("knuckle", [(0.0, -0.0045), (0.0019, -0.0045), (0.0019, 0.0045), (0.0, 0.0045)],
                       segments=8, mat="M_Brass_Aged")
    knuckle.data.transform(C.grot("z", 90.0))
    knuckle.location = hb
    keeper = L.box_mm("keeper", (-0.004, -0.0335, 0.080), (0.004, -0.0315, 0.0875), mat="M_Brass_Aged",
                      bevel=0.0)
    for o in (leaf, keeper):
        C.sm(o, 30.0)
    C.sm(knuckle, 60.0)
    parts += [leaf, knuckle, keeper]
    return C.part("canister", parts, (0.0, 0.0, 0.0))


def build_cap():
    prof = [(0.0, 0.0903), (0.0305, 0.0903), (0.0328, 0.0925), (0.0318, 0.0985), (0.0255, 0.1045),
            (0.0130, 0.1083), (0.0, 0.1092)]
    cap = L.lathe2("cap_shell", prof, segments=SEG, mat="M_Brass_Polished", cap_bottom=False, cap_top=False)
    C.sm(cap, 40.0)
    # knob on top + the two hinge cheeks + the spring latch tongue at the front
    knob = L.lathe2("cap_knob", [(0.0060, 0.1088), (0.0060, 0.1110), (0.0045, 0.1122), (0.0, 0.1124)],
                    segments=8, mat="M_Brass_Aged", cap_bottom=False)
    C.sm(knob, 50.0)
    hb = C.GV(HINGE_G)
    cheeks = []
    for sx in (-1, 1):
        ch = L.box_mm("cheek", (sx * 0.0072 - 0.0017, hb.y - 0.0025, hb.z - 0.0022),
                      (sx * 0.0072 + 0.0017, hb.y + 0.0015, 0.0960), mat="M_Brass_Aged", bevel=0.0)
        C.sm(ch, 30.0)
        cheeks.append(ch)
    tongue = L.box_mm("tongue", (-0.0032, -0.0345, 0.0835), (0.0032, -0.0325, 0.0975), mat="M_Chrome",
                      bevel=0.0)
    C.sm(tongue, 30.0)
    return C.part("canister_cap", [cap, knob, tongue] + cheeks, HINGE_G)


def build():
    C.ensure_materials()
    body = build_body()
    cap = build_cap()
    C.parent(cap, body)
    return body, cap


def main():
    M.reset_scene()
    body, cap = build()
    C.finalize()
    C.report(NAME, BUDGET)
    C.export(NAME)
    C.verify_glb(NAME, {
        "canister": dict(parent=None, pos=(0.0, 0.0, 0.0)),
        "canister_cap": dict(parent="canister", pos=HINGE_G),
    }, BUDGET)
    if not C.want_render():
        return
    C.qa_tweak()
    # hero: standing, cap closed (centre at the origin -> floor at z = -0.11)
    C.studio(NAME, (0.30, -0.50, 0.14), (0.0, 0.0, 0.005), lens=50, floor_z=-0.1101)
    # second: lying on its side with the cap open (QA pose only)
    import bpy
    from mathutils import Matrix
    C.pose_rot(cap, "x", -110.0)
    body.matrix_world = Matrix.Translation((0, 0, -0.1101 + 0.035)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    M.refresh()
    C.studio(NAME + "_2", (0.22, -0.36, 0.16), (0.02, 0.0, -0.07), lens=60, floor_z=-0.1101)


main()
