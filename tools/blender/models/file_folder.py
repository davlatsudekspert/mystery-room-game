"""file_folder.glb — Leyla's personnel file (returned by the pneumatic tube; holds her 1998 letter).

A closed manila personnel folder, 240 x 320 mm: two 0.6 mm card covers joined by a rounded spine fold
on the left, three loose sheets inside (one sticks out 2 mm at the right edge, one 1.5 mm at the
bottom), an index tab on the back cover sticking out of the right edge near the top (linen-reinforced,
with a white label typed "0417"), and a string-and-button closure: a brown fibre washer riveted near
the right edge with a cotton string wound round it, its tail running over the right edge.
`folder_face` is its own mesh on the front cover: the full 240 x 320 mm, UV 0..1 (u left -> right,
v bottom -> top as seen from above with the folder's top toward Godot -Z), slot M_Decal_FileCover.
Lies flat, front cover up (Godot +Y), top edge toward Godot -Z, spine at -X. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/file_folder.py [-- --no-render]
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

NAME = "file_folder"
C.LIGHTS = C.SOFT
W, H = 0.240, 0.320
CT = 0.0006                       # cover thickness
SHEET = 0.0004
Z_FRONT = CT + 3 * SHEET          # bottom of the front cover
Z_TOP = Z_FRONT + CT              # printed face
CORNER = 0.0025
TAB_Y0, TAB_Y1, TAB_OUT = 0.070, 0.122, 0.0130
BTN = (0.103, -0.004)             # closure button centre
BTN_R = 0.0080
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def back_outline():
    """Back cover with the index tab on its right edge (CCW)."""
    r, t = CORNER, 0.0035
    pts = L.rrect4(W, H, (r, r, r, r), 3)
    # rrect4 order: bottom-right corner, top-right, top-left, bottom-left; insert the tab on the right edge
    tab = [(W / 2, TAB_Y0 - 0.004), (W / 2 + TAB_OUT - t, TAB_Y0), (W / 2 + TAB_OUT, TAB_Y0 + t),
           (W / 2 + TAB_OUT, TAB_Y1 - t), (W / 2 + TAB_OUT - t, TAB_Y1), (W / 2, TAB_Y1 + 0.004)]
    return pts[:3] + tab + pts[3:]


def sheet(name, w, h, dx, dy, z, rot_deg):
    s = M.box(name, (w, h, SHEET), loc=(0, 0, 0), mat="M_Paper", bevel=0.0)
    s.data.transform(Matrix.Translation((dx, dy, z + SHEET / 2)) @ Matrix.Rotation(math.radians(rot_deg), 4, "Z"))
    return s


def string_path():
    """Cotton string: one and a half turns round the button (under its rim), then the tail over the edge."""
    pts = []
    cx, cy = BTN
    rr = BTN_R + 0.0004
    z = Z_TOP + 0.0006
    for i in range(30):                                   # 1.5 turns, slowly spiralling out
        a = math.radians(-30) + math.tau * 1.5 * i / 29
        r = rr + 0.0007 * i / 29
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z + 0.0004 * math.sin(i * 0.9)))
    # tail: from the last point across to the right edge, over it and down the side
    lx, ly, _ = pts[-1]
    pts += [(lx + 0.0040, ly - 0.0050, z), (W / 2 - 0.0030, cy - 0.0150, z - 0.0001),
            (W / 2 + 0.0008, cy - 0.0180, Z_TOP - 0.0002), (W / 2 + 0.0016, cy - 0.0195, Z_TOP * 0.45),
            (W / 2 + 0.0012, cy - 0.0205, 0.0005)]
    return pts


def build():
    back = L.curve_solid(NAME, [back_outline()], CT, bevel=0.00015, bevel_res=0, mat="M_Cardboard")
    parts = []
    front = L.curve_solid("front_cover", [L.rrect4(W, H, (CORNER,) * 4, 3)], CT, bevel=0.00015, bevel_res=0,
                          mat="M_Cardboard")
    front.location = (0, 0, Z_FRONT)
    M.apply_transform(front)
    C.drop_cap(front, Z_TOP)                         # the printed face replaces the top cap
    parts.append(front)
    # loose sheets inside (slightly smaller, one sticking out right, one at the bottom)
    parts.append(sheet("sheet_a", 0.232, 0.312, -0.002, 0.001, CT, 0.3))
    parts.append(sheet("sheet_b", 0.228, 0.300, 0.0081, 0.002, CT + SHEET, -0.6))
    parts.append(sheet("sheet_c", 0.226, 0.306, -0.004, -0.0065, CT + 2 * SHEET, 0.5))
    # rounded spine fold along the left edge
    spine = M.cylinder("spine", Z_TOP / 2, H - 0.0004, loc=(-W / 2 + 0.0002, 0, Z_TOP / 2), rot=(math.pi / 2, 0, 0),
                       verts=12, mat="M_Cardboard", bevel=0.0)
    parts.append(spine)
    # linen reinforcement over the tab and the typed label
    tab_l = L.curve_solid("tab_linen", [L.rrect4(TAB_OUT + 0.0090, TAB_Y1 - TAB_Y0 + 0.0040, (0.0030, 0.0030, 0.0, 0.0), 3,
                                                 cx=W / 2 + (TAB_OUT - 0.0090) / 2, cy=(TAB_Y0 + TAB_Y1) / 2)],
                          0.0002, bevel=0.0, mat="M_Linen")
    tab_l.location = (0, 0, CT)
    M.apply_transform(tab_l)
    parts.append(tab_l)
    lx = W / 2 + TAB_OUT / 2 + 0.0004
    label = L.flat_shape("tab_label", [L.rounded_rect(0.0085, 0.0380, 0.0006, 2, cx=lx, cy=(TAB_Y0 + TAB_Y1) / 2)],
                         mat="M_Paper", loc=(0, 0, CT + 0.00022))
    M.apply_transform(label)
    parts.append(label)
    txt = L.text_flat("tab_text", "0417", 0.0052, font=MONO, res=1, mat="M_Bakelite")
    L.recentre_xy(txt)
    txt.data.transform(Matrix.Translation((lx, (TAB_Y0 + TAB_Y1) / 2, CT + 0.00025)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    parts.append(txt)
    # closure: brown fibre washer with a brass rivet, string wound round it
    btn = L.lathe2("button", [(BTN_R, 0.0), (BTN_R, 0.0005), (BTN_R - 0.0006, 0.0008), (0.0026, 0.0008),
                              (0.0024, 0.0013), (0.0012, 0.0017), (0.0, 0.0018)], segments=24, mat="M_Leather",
                   band_mats=[None, None, None, "M_Brass_Aged", "M_Brass_Aged", "M_Brass_Aged"], cap_bottom=False)
    btn.location = (BTN[0], BTN[1], Z_TOP + 0.0009)
    M.apply_transform(btn)
    shank = M.cylinder("button_shank", 0.0022, 0.0010, loc=(BTN[0], BTN[1], Z_TOP + 0.0005), verts=10,
                       mat="M_Brass_Aged", bevel=0.0)
    parts += [btn, shank]
    parts.append(L.tube("string", string_path(), 0.00055, mat="M_Linen", bevel_res=1, res_u=3))
    hard = M.join(parts, "folder_body")
    M.set_parent(hard, back)
    face = L.flat_shape("folder_face", [L.rrect4(W, H, (CORNER,) * 4, 3)], mat="M_Decal_FileCover", loc=(0, 0, Z_TOP))
    M.apply_transform(face)
    M.set_parent(face, back)
    return [back]


def post():
    C.uv_rect_all(bpy.data.objects["folder_face"], -W / 2, W / 2, -H / 2, H / 2)


def main():
    C.item_main(NAME, build, post=post, required=("folder_face",), shots=[
        ("", (0.20, -0.36, 0.34), (0.01, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.62), (0.0, 0.0, 0.0), 50),
        ("_3", (0.20, -0.10, 0.10), (0.11, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
