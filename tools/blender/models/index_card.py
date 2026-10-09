"""index_card.glb — Leyla's edge-notched catalogue card (P1 reward, P3 pattern). PUZZLE-CRITICAL.

A cream 125 x 75 mm index card (0.28 mm card stock) with 8 edge positions along its top edge, left to
right = positions 1..8, position k centred at u = (k - 0.5) / 8 of the card width. V-notches are cut
through the edge at positions 1, 3, 4 and 7 only (pattern 1 0 1 1 0 0 1 0); 2, 5, 6 and 8 are plain.
The printed face (typed text, position numbers) is the separate quad `card_face` with UV 0..1 over the
whole card, slot M_Decal_IndexCard; it carries the same notches. Lies flat, face up (Blender +Z,
Godot +Y), top edge toward Blender +Y (Godot -Z). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/index_card.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "index_card"
W, H, T = 0.125, 0.075, 0.00028
NOTCHED = (1, 3, 4, 7)              # positions 1..8, left -> right (archive_logic punch pattern)
NOTCH_W, NOTCH_D, NOTCH_FLAT = 0.0068, 0.0058, 0.0007
CORNER = 0.0012


def pos_x(k: int) -> float:
    """Centre of edge position k (1..8): u = (k - 0.5) / 8 of the card width."""
    return -W / 2 + (k - 0.5) * W / 8


def outline(notched=NOTCHED):
    """CCW card outline with V-notches cut into the top edge (y = +H/2)."""
    pts = L.rounded_rect(W, H, CORNER, 3)
    # rounded_rect order: bottom-right, top-right corner, top-left, bottom-left. Insert the notches
    # (right to left) between the top-right and the top-left corner.
    top_r = 2 * 3 - 1           # last point of the top-right corner
    notch_pts = []
    for k in sorted(notched, reverse=True):
        x = pos_x(k)
        notch_pts += [(x + NOTCH_W / 2, H / 2), (x + NOTCH_FLAT / 2, H / 2 - NOTCH_D),
                      (x - NOTCH_FLAT / 2, H / 2 - NOTCH_D), (x - NOTCH_W / 2, H / 2)]
    return pts[:top_r + 1] + notch_pts + pts[top_r + 1:]


def build():
    loop = outline()
    card = L.curve_solid(NAME, [loop], T, bevel=0.0, mat="M_Paper")
    C.drop_cap(card, T)                       # the printed face replaces the top cap
    face = L.flat_shape("card_face", [loop], mat="M_Decal_IndexCard", loc=(0, 0, T))
    M.set_origin(face, (0, 0, T))
    C.parent_all([face], card)
    return [card]


def post():
    face = M.bpy.data.objects["card_face"]
    C.uv_rect_all(face, -W / 2, W / 2, -H / 2, H / 2)


def main():
    C.item_main(NAME, build, post=post, required=("card_face",), shots=[
        ("", (0.045, -0.13, 0.15), (0.0, 0.0, 0.0), 50),
        ("_2", (0.0, -0.02, 0.21), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
