"""photo_print.glb — Leyla's photograph from the desk's hidden compartment (inventory item).

A 1970s gloss print with a white border (wider at the bottom), a faint lengthwise curl and one softened
corner. Leyla's note is on the back (the text itself is localized in the inspect view, doc.photo), so the
back only carries a language-neutral "7 — 1977" in ink. 0.084 x 0.106 m, ~0.4 mm thick.
Lies flat (Blender +Z up, image readable from above with +Y = top of the picture). Origin at the
centre of mass. The image is `M_Decal_Photo_Leyla` (photo_3.jpg, 280:344) with its own 0..1 UV.
    blender -b --factory-startup -P tools/blender/models/photo_print.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_props as P  # noqa: E402

NAME = "photo_print"
CW, CH, CT = 0.084, 0.106, 0.0004     # card
IW, IH = 0.072, 0.0884                # image, aspect 280:344
IMG_Y = 0.0045                        # image sits above centre: the bottom border is wider
CURL = 0.9                            # lift (1/m) of the long edges: z = CURL * x^2


def lift(x: float) -> float:
    return CURL * x * x


def grid(name, w, h, cy, z0, mat, nx=6, ny=6, corner_cut=0.0):
    """Curled rectangle in XY (normal +Z). `corner_cut` trims the top-right corner (a worn corner)."""
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * w
            y = cy + (j / ny - 0.5) * h
            if corner_cut and i == nx and j == ny:
                x -= corner_cut * 0.6
                y -= corner_cut * 0.6
            verts.append((x, y, z0 + lift(x)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = P.mesh_obj(name, verts, faces, [mat])
    P.fix_normals(o)
    if o.data.polygons[0].normal.z < 0:
        o.data.flip_normals()
    return o


def build():
    card = grid("card", CW, CH, 0.0, 0.0, "M_Paper", corner_cut=0.003)
    sol = card.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = CT
    sol.offset = -1.0
    M.apply_modifiers(card)
    img_path = os.path.join(P.DECALS, "photo_3.jpg")
    M.material("M_Decal_Photo_Leyla", color="FFFFFF", rough=0.3, image=img_path if os.path.exists(img_path) else None)
    img = grid("image", IW, IH, IMG_Y, 0.00008, "M_Decal_Photo_Leyla", nx=6, ny=6)
    M.planar_uv(img, axis="Z")
    # back: readable when the print is flipped over about its long (Y) axis
    note = D.hand("back_note", "7 — 1977", 0.0085, ratio=0.6, mat="M_Bakelite", loc=(0.0, 0.012, 0.0),
                  rot=(0.0, math.pi, 0.0))
    M.apply_transform(note)
    for v in note.data.vertices:          # sit on the curled back face
        v.co.z = -CT - 0.00008 + lift(v.co.x)
    return [M.join([card, img, note], NAME)]


def post():
    """finalize() box-maps everything; give the image faces back their exact 0..1 fit."""
    import bpy
    M.planar_uv(bpy.data.objects[NAME], axis="Z", material_prefix="M_Decal_")


def main():
    D.item_main(NAME, build, post=post, shots=[
        ("", (0.05, -0.15, 0.17), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
