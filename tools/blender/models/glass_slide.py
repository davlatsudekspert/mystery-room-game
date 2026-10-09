"""glass_slide.glb — Strand's emblem slide (slide cabinet drawer ✦, shown by the slide projector).

A 3 1/4-inch (82 x 82 mm) lantern slide: a 2.6 mm glass sandwich (M_Glass) bound on all four edges with
black passe-partout tape (M_Rubber, 2.8 mm over each face).
`slide_image` is its own square at the image plane inside the sandwich, the full 82 x 82 mm, UV 0..1
(u left -> right, v bottom -> top seen from the front), slot M_Decal_SlideMark: slide_mark.png carries
the black card mask with its round window, the mark (black on clear glass) and the ✦ corner spot.
Lies flat, front up (Godot +Y), top edge toward Godot -Z. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/glass_slide.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "glass_slide"
S = 0.082             # slide size
TG = 0.0026           # glass sandwich thickness
TAPE = 0.0028         # tape width over each face
ZI = TG / 2           # image plane


def build():
    glass = L.curve_solid(NAME, [L.rounded_rect(S - 0.0004, S - 0.0004, 0.0008, 2)], TG, bevel=0.0002,
                          mat="M_Glass")
    parts = []
    # binding tape: a frame wrapping the four edges (top band, outer edge, bottom band)
    tape = L.curve_solid("tape", [L.rounded_rect(S + 0.0002, S + 0.0002, 0.0010, 3),
                                  L.rounded_rect(S - 2 * TAPE, S - 2 * TAPE, 0.0004, 2)], TG + 0.0002,
                         bevel=0.00025, bevel_res=1, mat="M_Rubber")
    tape.location = (0, 0, -0.0001)
    M.apply_transform(tape)
    lim = S / 2 - TAPE + 0.0004                # the inner wall would show through the glass: drop it
    L.drop_faces(tape, lambda c, n: max(abs(c.x), abs(c.y)) < lim and abs(n.z) < 0.9)
    parts.append(tape)
    hard = M.join(parts, "slide_mount")
    M.set_parent(hard, glass)
    img = L.flat_shape("slide_image", [L.rounded_rect(S - 0.0006, S - 0.0006, 0.0006, 2)], mat="M_Decal_SlideMark",
                       loc=(0, 0, ZI))
    M.apply_transform(img)
    M.set_parent(img, glass)
    return [glass]


def post():
    C.uv_rect_all(bpy.data.objects["slide_image"], -S / 2, S / 2, -S / 2, S / 2)


def main():
    C.item_main(NAME, build, post=post, required=("slide_image",), shots=[
        ("", (0.05, -0.10, 0.10), (0.0, 0.003, 0.0), 50),
        ("_2", C.inspect_cam(0.17), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
