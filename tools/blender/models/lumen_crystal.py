"""lumen_crystal.glb — a blank Lumen crystal (booth lens case; recorded at the screen socket, read by the
vault's light lock).

A clear crystal disc, 50 mm across and 6 mm thick, with a flat polished front and a shallow 12-facet
rose-cut back, held in a thin turned brass bezel (54.5 mm, 7.2 mm deep, two fine grooves round its band) with front
and back lips.
Eight engraved index dots ring the front lip (one every 45 deg, the 12 o'clock one a short bar), so a
rotation of the crystal in the vault's collars reads at a glance. A small brass grip tab with a hole
stands up from the bezel at 12 o'clock.
`crystal_face` is its own disc just in front of the crystal's front face, inside the lip: radius 23.2 mm,
UV 0..1 over its bounding square (u left -> right, v bottom -> top seen from the front), slot M_Crystal;
ItemDress puts the recorded image on it.
Stands on its rim with the disc facing Blender -Y (Godot +Z). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/lumen_crystal.py [-- --no-render]
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
from mathutils import Matrix  # noqa: E402

NAME = "lumen_crystal"
RC = 0.025            # crystal radius
TC = 0.003            # half thickness of the crystal (6 mm)
RO = 0.02725          # bezel outer radius
HB = 0.0036           # half depth of the bezel
RL = 0.0232           # lip inner radius = visible face radius
FACE_R = RL


def build():
    Y = (0, -1, 0)
    # crystal: flat front (profile z = +TC is the front, toward -Y), 12-facet rose-cut back
    gem = [(0.0, -TC), (0.0105, -TC + 0.0007), (0.0195, -TC + 0.0019), (RC, -0.0009), (RC, TC - 0.0006),
           (RC - 0.0006, TC), (0.0, TC)]
    crystal = D.revolve(NAME, gem, direction=Y, segments=24, mat="M_Crystal")
    # bezel: closed annular section revolved (front lip, groove for the crystal edge, back lip)
    c = 0.0005
    g = 0.00035          # two fine turned grooves on the outer band
    prof = [(RL, -HB), (RO - c, -HB), (RO, -HB + c), (RO, -0.0014 - g), (RO - g, -0.0014), (RO, -0.0014 + g),
            (RO, 0.0014 - g), (RO - g, 0.0014), (RO, 0.0014 + g), (RO, HB - c), (RO - c, HB), (RL + 0.0004, HB),
            (RL, HB - 0.0004), (RL, TC + 0.0001), (RC + 0.0002, TC + 0.0001), (RC + 0.0002, -TC - 0.0001),
            (RL, -TC - 0.0001), (RL, -HB)]
    bezel = D.revolve("bezel", prof, direction=Y, segments=48, mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
    parts = [bezel]
    # engraved index dots on the front lip: one every 45 deg, a short bar at 12 o'clock
    yf = -HB - 0.00004
    rm = (RL + 0.0004 + RO - c) / 2
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        if k == 0:
            mk = L.flat_shape("idx", [L.rounded_rect(0.0006, 0.0022, 0.0002, 2)], mat="M_Bakelite")
        else:
            mk = L.flat_shape("idx", [L.circle(0.00042, 8)], mat="M_Bakelite")
        mk.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        L.to_front(mk, y_back=yf, x=rm * math.cos(a), z=rm * math.sin(a))
        parts.append(mk)
    # grip tab at 12 o'clock: a rounded brass tongue with a hole, rooted inside the bezel
    tw, top = 0.0098, RO + 0.0062
    tab_pts = [(-tw / 2, RO - 0.0016), (tw / 2, RO - 0.0016), (tw / 2, top - tw / 2)]
    tab_pts += L.arc_pts(tw / 2, 0.0, math.pi, 9, cx=0.0, cy=top - tw / 2)[1:-1]
    tab_pts += [(-tw / 2, top - tw / 2)]
    tab = L.curve_solid("grip_tab", [tab_pts, L.circle(0.00140, 12, cy=RO + 0.0034)], 0.0022, bevel=0.00035,
                        bevel_res=1, mat="M_Brass_Aged")
    L.to_front(tab, y_back=0.0011)
    parts.append(tab)
    hard = M.join(parts, "crystal_bezel")
    M.set_parent(hard, crystal)
    # the recordable face (own object, UV 0..1 over its bounding square)
    face = L.flat_shape("crystal_face", [L.circle(FACE_R, 40)], mat="M_Crystal")
    L.to_front(face, y_back=-TC - 0.00006)
    M.set_parent(face, crystal)
    return [crystal]


def post():
    D.resmooth(bpy.data.objects[NAME], 10.0)
    D.resmooth(bpy.data.objects["crystal_bezel"], 40.0)          # crisp grooves, smooth round band
    C.uv_rect_all(bpy.data.objects["crystal_face"], -FACE_R, FACE_R, -FACE_R, FACE_R, axis="Y")


def recorded():
    """QA only: the face showing a recorded image (Leyla's sign), as ItemDress.glyph does in game."""
    img = os.path.join(C.DECALS_CH2, "glyph_sign.png")
    if not os.path.exists(img):
        return
    mat = bpy.data.materials.new("QA_glyph")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img, check_existing=True)
    bsdf.inputs["Base Color"].default_value = M.hex_rgba("CFF6FF")
    bsdf.inputs["Emission Color"].default_value = M.hex_rgba("CFF6FF")
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Emission Strength"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    face = bpy.data.objects["crystal_face"]
    face.data.materials.clear()
    face.data.materials.append(mat)
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"


def main():
    C.item_main(NAME, build, post=post, required=("crystal_face",), shots=[
        ("", (0.07, -0.15, 0.05), (0.0, 0.0, 0.0), 70),
        ("_2", (-0.06, 0.10, 0.04), (0.0, 0.0, 0.0), 70),
        ("_3", (0.0, -0.16, 0.012), (0.0, 0.0, 0.0), 70, recorded),
    ])


if __name__ == "__main__":
    main()
