"""flip_clock.glb — 1970s walnut & bakelite flip clock stopped at 03:17 (desk prop, Lab 7).

Front faces Blender -Y, base on Z=0, origin at the base centre.
Parts: clock_body (static), clock_face (M_Decal_ClockFace, planar UV along Y, 512:224).
No cover glass on purpose: the 03:17 clue must stay perfectly readable.
    blender -b --factory-startup -P tools/blender/models/flip_clock.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix  # noqa: E402

W, H, D = 0.19, 0.13, 0.10      # walnut wrap: width (X), height (Z), depth (Y)
Z0 = 0.012                      # wrap bottom (feet below)
ZC = Z0 + H / 2
WIN_W, WIN_H = 0.168, 0.082     # window opening
FACE_W, FACE_H = 0.160, 0.070   # decal 512:224
WIN_Z = Z0 + 0.069


def build():
    parts = []
    # --- walnut wrap: rounded profile in YZ, extruded across X
    prof = L.rrect4(D, H, radii=(0.012, 0.046, 0.013, 0.010), n=6, cy=ZC)
    wrap = L.curve_solid("wrap", [prof], W, bevel=0.0018, bevel_res=1, mat="M_Wood_Walnut")
    L.profile_yz(wrap, -W / 2)
    # window recess cut into the front
    cutter = M.box("cut", (WIN_W, 0.03, WIN_H), loc=(0, -D / 2 - 0.007, WIN_Z), bevel=0.003, segments=2)
    M.boolean(wrap, cutter)
    parts.append(wrap)
    # --- bakelite cheeks (slightly larger profile)
    for sx in (-1, 1):
        prof_c = L.rrect4(D + 0.006, H + 0.006, radii=(0.014, 0.049, 0.016, 0.013), n=5, cy=ZC)
        ch = L.curve_solid("cheek", [prof_c], 0.009, bevel=0.0022, bevel_res=1, mat="M_Bakelite")
        L.profile_yz(ch, W / 2 if sx > 0 else -W / 2 - 0.009)
        parts.append(ch)
        # chrome pinstripe between wrap and cheek
        strip_prof = L.rrect4(D + 0.002, H + 0.002, radii=(0.012, 0.047, 0.014, 0.011), n=5, cy=ZC)
        st = L.curve_solid("strip", [strip_prof], 0.0012, bevel=0.0, mat="M_Chrome")
        L.profile_yz(st, W / 2 - 0.0006 if sx > 0 else -W / 2 - 0.0006)
        parts.append(st)
        # sled foot under each cheek
        foot = M.box("foot", (0.013, 0.085, 0.010), loc=(sx * (W / 2 + 0.0045), 0.0, 0.005 + 0.002),
                     mat="M_Bakelite", bevel=0.003, segments=1)
        pad = M.box("pad", (0.011, 0.075, 0.002), loc=(sx * (W / 2 + 0.0045), 0.0, 0.001), mat="M_Rubber",
                    bevel=0.0006, segments=1)
        parts += [foot, pad]
    # --- recess lining (black mask) behind the face decal
    back = M.box("mask", (WIN_W - 0.002, 0.002, WIN_H - 0.002), loc=(0, -D / 2 + 0.0085, WIN_Z), mat="M_Bakelite",
                 bevel=0.0)
    parts.append(back)
    # flap hinge rods visible at the split line (between the flaps, in front of the decal)
    for xx in (-0.0395, 0.0395):
        rod = M.cylinder("rod", 0.0009, 0.075, loc=(xx, -D / 2 + 0.0058, WIN_Z - 0.0003), rot=(0, math.pi / 2, 0),
                         verts=6, mat="M_Steel_Dark", bevel=0)
        parts.append(rod)
    # --- chrome bezel around the window (protrudes 2.5 mm)
    outer = L.rounded_rect(WIN_W + 0.012, WIN_H + 0.012, 0.009, n=4)
    inner = L.rounded_rect(WIN_W - 0.001, WIN_H - 0.001, 0.0035, n=3)
    bez = L.curve_solid("bezel", [outer, inner], 0.0035, bevel=0.0012, bevel_res=1, mat="M_Chrome")
    L.to_front(bez, y_back=-D / 2 + 0.001, z=WIN_Z)
    parts.append(bez)
    # --- top: alarm/snooze bar on a bakelite base
    stad = L.rounded_rect(0.13, 0.014, 0.0069, n=6)
    base = L.curve_solid("bar_base", [L.rounded_rect(0.138, 0.020, 0.0099, n=6)], 0.002, bevel=0.0008, mat="M_Bakelite")
    base.location = (0, -0.017, Z0 + H - 0.0005)
    bar = L.curve_solid("bar", [stad], 0.0055, bevel=0.002, bevel_res=1, mat="M_Chrome")
    bar.location = (0, -0.017, Z0 + H + 0.0012)
    parts += [base, bar]
    # --- right cheek: knurled time-set knob; left cheek: alarm slide
    knob = L.knurled_knob("knob", 0.0115, 0.009, ridges=12, mat="M_Bakelite", index_mark=False, simple=True)
    knob.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    knob.location = (W / 2 + 0.009, 0.012, ZC + 0.008)
    collar = M.cylinder("collar", 0.007, 0.004, loc=(W / 2 + 0.010, 0.012, ZC + 0.008), rot=(0, math.pi / 2, 0),
                        verts=12, mat="M_Chrome", bevel=0.0008, segments=1)
    knob2 = L.knurled_knob("knob2", 0.008, 0.007, ridges=10, mat="M_Bakelite", index_mark=False, simple=True)
    knob2.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    knob2.location = (W / 2 + 0.009, 0.030, Z0 + 0.03)
    slide_slot = M.box("slot", (0.002, 0.03, 0.006), loc=(-W / 2 - 0.0095, 0.02, ZC + 0.01), mat="M_Steel_Dark",
                       bevel=0.0008, segments=1)
    slide = M.box("slide", (0.005, 0.008, 0.009), loc=(-W / 2 - 0.0115, 0.01, ZC + 0.01), mat="M_Chrome",
                  bevel=0.0018, segments=1)
    parts += [knob, collar, knob2, slide_slot, slide]
    # --- back: label plate with rivets, cord grommet + unplugged cord with plug
    lab = M.box("label", (0.06, 0.0012, 0.028), loc=(0.02, D / 2 + 0.0004, ZC - 0.022), mat="M_Brass_Aged",
                bevel=0.0005, segments=1)
    parts.append(lab)
    for dx in (-0.026, 0.026):
        parts.append(L.rivet("rv", 0.0016, (0.02 + dx, D / 2 + 0.001, ZC - 0.022), normal=(0, 1, 0), mat="M_Brass_Aged", segs=6))
    txt = L.text_flat("lbl_txt", "MERIDIAN", 0.0075, font=L.FONT_SANS_B, mat="M_Steel_Dark",
                      rot=(math.pi / 2, 0, math.pi), loc=(0.02, D / 2 + 0.0011, ZC - 0.022))
    parts.append(txt)
    grom = M.cylinder("grommet", 0.005, 0.006, loc=(-0.05, D / 2 + 0.002, Z0 + 0.025), rot=(math.pi / 2, 0, 0),
                      verts=10, mat="M_Rubber", bevel=0.0015, segments=1)
    pz = 0.0095   # plug axis height (plug radius) - the clock is unplugged: it stopped at 03:17
    cord = L.tube("cord", [(-0.05, D / 2 + 0.003, Z0 + 0.025), (-0.053, D / 2 + 0.028, 0.008),
                           (-0.035, D / 2 + 0.065, 0.0026), (0.01, D / 2 + 0.085, 0.0026),
                           (0.035, D / 2 + 0.07, 0.006), (0.05, D / 2 + 0.06, pz)], 0.0026, mat="M_Fabric",
                  bevel_res=1, res_u=4)
    plug = L.lathe2("plug", [(0.0, 0.0), (0.0032, 0.0), (0.0042, 0.004), (0.0085, 0.009), (0.0095, 0.024),
                             (0.0088, 0.028), (0.0, 0.0285)], segments=12, mat="M_Bakelite")
    plug.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))       # lathe +Z -> +X
    plug.location = (0.05, D / 2 + 0.06, pz)
    pins = []
    for dy in (-0.0048, 0.0048):
        pins.append(M.cylinder("pin", 0.002, 0.019, loc=(0.05 + 0.0285 + 0.008, D / 2 + 0.06 + dy, pz),
                               rot=(0, math.pi / 2, 0), verts=8, mat="M_Chrome", bevel=0.0006, segments=1))
    parts += [grom, cord, plug] + pins
    body = M.join(parts, "clock_body")

    # --- decal face + glass (separate objects)
    face = L.plane("clock_face", FACE_W, FACE_H, loc=(0, -D / 2 + 0.0073, WIN_Z), mat="M_Decal_ClockFace")
    return body, face


def decal_uvs():
    M.planar_uv(M.bpy.data.objects["clock_face"], axis="Y", material_prefix="M_Decal_")


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("flip_clock", decals=[decal_uvs])
    if L.want_render():
        L.qa_render("flip_clock", (0.30, -0.42, 0.24), (0.0, 0.0, 0.07), lens=60)
        L.qa_render("flip_clock_2", (0.0, -0.40, 0.08), (0.0, 0.0, 0.075), lens=70)
        L.qa_render("flip_clock_3", (-0.25, 0.35, 0.22), (0.0, 0.03, 0.05), lens=55)


main()
