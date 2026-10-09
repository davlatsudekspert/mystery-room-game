"""request_card.glb — buff "REQUEST — ARCHIVE B" card (P3 blank / punched request card).

Same size as the index card: 125 x 75 mm, 0.3 mm buff card stock, square-ish corners with a 1.5 mm
radius and one clipped top-left corner (the orientation corner of punched cards). The printed face
(header, 8 numbered punch circles along the top at u = (k - 0.5) / 8, v = 1 - 9.2/75) is the separate
mesh `card_face`, UV 0..1 over the card rectangle, slot M_Decal_RequestCard.
Holes: `hole_0` .. `hole_7` are separate dark discs (Ø 5.0 mm, M_Rubber, a thin closed puck from just
under the card to just over its face) at the 8 positions, left -> right; ItemDress shows the punched
ones (all visible in the GLB). Lies flat, face up (Godot +Y), top edge toward Godot -Z.
Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/request_card.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "request_card"
W, H, T = C.CARD_W, C.CARD_H, 0.0003
CORNER = 0.0015
CLIP = 0.0045            # clipped top-left corner (orientation corner)
HOLE_Y = H / 2 - C.HOLE_FROM_TOP


def outline():
    n = 3
    pts = L.rounded_rect(W, H, CORNER, n)
    # replace the top-left rounded corner (points 2n .. 3n-1) by a 45 deg clip
    return pts[:2 * n] + [(-W / 2 + CLIP, H / 2), (-W / 2, H / 2 - CLIP)] + pts[3 * n:]


def build():
    loop = outline()
    card = L.curve_solid(NAME, [loop], T, bevel=0.0, mat="M_Paper")
    C.drop_cap(card, T)
    face = L.flat_shape("card_face", [loop], mat="M_Decal_RequestCard", loc=(0, 0, T))
    C.parent_all([face], card)
    for i in range(8):
        x = C.card_pos_x(i + 1, W)
        h = L.lathe2(f"hole_{i}", [(C.HOLE_D / 2, -0.00004), (C.HOLE_D / 2, T + 0.00006)], segments=16,
                     mat="M_Rubber")
        h.location = (x, HOLE_Y, 0.0)
        M.set_parent(h, card)
    return [card]


def post():
    face = bpy.data.objects["card_face"]
    C.uv_rect_all(face, -W / 2, W / 2, -H / 2, H / 2)


def show_punch():
    """QA only: the punched pattern of the solved card (1 0 1 1 0 0 1 0)."""
    for i, bit in enumerate(C.PUNCH_CODE):
        bpy.data.objects[f"hole_{i}"].hide_render = not bit


def main():
    C.item_main(NAME, build, post=post, required=("card_face",) + tuple(f"hole_{i}" for i in range(8)), shots=[
        ("", (0.05, -0.12, 0.13), (0.0, 0.004, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, 0.0, 0.0), 50, show_punch),
    ])


if __name__ == "__main__":
    main()
