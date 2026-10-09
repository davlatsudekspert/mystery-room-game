"""index_card.glb — Leyla's edge-notched catalogue card (P1 reward, P3 pattern). PUZZLE-CRITICAL.

A cream 125 x 75 mm index card (0.3 mm card stock) with 8 edge positions along its top edge, left to
right = positions 1..8, position k centred at u = (k - 0.5) / 8 of the card width. V-notches (8.4 mm
wide at the edge, 10 mm deep, matching the decal builder's NOTCH_W_PX / NOTCH_D_PX) are cut through the
edge at positions 1, 3, 4 and 7 only (pattern 1 0 1 1 0 0 1 0); 2, 5, 6 and 8 are plain.
The printed face (typed text, position numbers) is the separate mesh `card_face` with UV 0..1 over the
whole card rectangle, slot M_Decal_IndexCard; it carries the same notches. A Ø 6 mm catalogue rod hole
is punched at the bottom centre, 5.2 mm above the bottom edge (also transparent in the decal). Lies flat, face up
(Blender +Z, Godot +Y), top edge toward Blender +Y (Godot -Z). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/index_card.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "index_card"
C.LIGHTS = C.SOFT
W, H, T = C.CARD_W, C.CARD_H, 0.0003
NOTCHED = tuple(k + 1 for k, bit in enumerate(C.PUNCH_CODE) if bit)     # (1, 3, 4, 7)
NOTCH_FLAT = 0.0006
CORNER = 0.0015
ROD_R, ROD_FROM_BOTTOM = 0.0030, 0.0052   # catalogue rod hole (bottom centre), as drawn in index_card.png


def outline(notched=NOTCHED):
    """CCW card outline with V-notches cut into the top edge (y = +H/2)."""
    n = 3
    pts = L.rounded_rect(W, H, CORNER, n)
    # rounded_rect order: bottom-right, top-right, top-left, bottom-left corner (n points each).
    # Insert the notches (right to left) between the top-right and the top-left corner.
    top_r = 2 * n - 1
    notch_pts = []
    for k in sorted(notched, reverse=True):
        x = C.card_pos_x(k, W)
        notch_pts += [(x + C.NOTCH_W / 2, H / 2), (x + NOTCH_FLAT / 2, H / 2 - C.NOTCH_D),
                      (x - NOTCH_FLAT / 2, H / 2 - C.NOTCH_D), (x - C.NOTCH_W / 2, H / 2)]
    return pts[:top_r + 1] + notch_pts + pts[top_r + 1:]


def build():
    loop = outline()
    rod = L.circle(ROD_R, 20, cx=0.0, cy=-H / 2 + ROD_FROM_BOTTOM)
    card = L.curve_solid(NAME, [loop, rod], T, bevel=0.0, mat="M_Paper")
    C.drop_cap(card, T)                       # the printed face replaces the top cap
    face = L.flat_shape("card_face", [loop, rod], mat="M_Decal_IndexCard", loc=(0, 0, T))
    C.parent_all([face], card)
    return [card]


def post():
    face = M.bpy.data.objects["card_face"]
    C.uv_rect_all(face, -W / 2, W / 2, -H / 2, H / 2)


def main():
    C.item_main(NAME, build, post=post, required=("card_face",), shots=[
        ("", (0.05, -0.12, 0.13), (0.0, 0.004, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
