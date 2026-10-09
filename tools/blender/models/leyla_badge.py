"""leyla_badge.glb — Leyla's laminated Institute staff badge (P1 clue: staff no. 0417).

The printed card is 86 x 54 mm (ID-1 / CR80 size), 0.76 mm thick; its front is the separate mesh
`badge_face` (UV 0..1 over the 86 x 54 card, slot M_Decal_Badge: emblem, photo, RAHIMOVA L., № 0417).
It is sealed in a clear laminate pouch whose border (M_Glass) shows 2 mm around the card and a 10 mm
margin above it, punched with a strap slot. A clear vinyl strap (M_Glass_Frosted) with a chrome snap runs
through the slot to a nickel-plated alligator clip (M_Chrome); a short frayed stub of the old red lanyard
cord (M_String_Red) is still knotted through the clip's eye. Lies flat, face up (Godot +Y), the card's top
edge toward Godot -Z (clip and cord beyond it). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/leyla_badge.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "leyla_badge"
CW, CH, CT = 0.086, 0.054, 0.00076        # printed card
CR = 0.0032
LAM_SIDE, LAM_TOP = 0.002, 0.010
LZ0, LT = 0.00020, 0.00036                # laminate seal: z range of the border sheet
SLOT_Y = CH / 2 + 0.0052
SLOT_W, SLOT_H = 0.0136, 0.0032
CLIP_Y0 = CH / 2 + 0.0185                 # clip's strap end
CLIP_L, CLIP_W = 0.026, 0.0150


def card_loop():
    return L.rounded_rect(CW, CH, CR, 4)


def laminate():
    lw, lh = CW + 2 * LAM_SIDE, CH + LAM_SIDE + LAM_TOP
    cy = (LAM_TOP - LAM_SIDE) / 2
    outer = L.rounded_rect(lw, lh, CR + 0.0012, 4, cy=cy)
    slot = L.rounded_rect(SLOT_W, SLOT_H, SLOT_H / 2 - 1e-5, 4, cy=SLOT_Y)
    lam = L.curve_solid("laminate", [outer, card_loop(), slot], LT, bevel=0.00012, mat="M_Glass")
    lam.location = (0, 0, LZ0)
    return lam


def strap():
    """Clear vinyl strap: through the slot, folded back on itself, riveted under the clip's base."""
    w, t = SLOT_W - 0.0012, 0.00045
    y_a = SLOT_Y - SLOT_H / 2 + 0.0004
    y_b = CLIP_Y0 + 0.0040
    parts = []
    top = L.curve_solid("strap_top", [L.rounded_rect(w, y_b - y_a, 0.0015, 3, cy=(y_a + y_b) / 2)], t,
                        bevel=0.0001, mat="M_Glass_Frosted")
    top.location = (0, 0, CT + 0.00002)
    parts.append(top)
    bot = L.curve_solid("strap_bot", [L.rounded_rect(w, y_b - y_a, 0.0015, 3, cy=(y_a + y_b) / 2)], t,
                        bevel=0.0001, mat="M_Glass_Frosted")
    bot.location = (0, 0, LZ0 + LT + 0.00002)
    parts.append(bot)
    # the fold through the slot (half tube)
    fold = M.cylinder("strap_fold", 0.0006, w, loc=(0, y_a, LZ0 + LT + 0.0003), rot=(0, math.pi / 2, 0),
                      mat="M_Glass_Frosted", verts=8, bevel=0.0)
    parts.append(fold)
    # chrome snap (dome + cap ring)
    snap = L.lathe2("snap", [(0.0032, 0.0), (0.0032, 0.0004), (0.0027, 0.0011), (0.0016, 0.0015), (0.0, 0.0016)],
                    segments=20, mat="M_Chrome", cap_bottom=False)
    snap.location = (0, SLOT_Y + 0.0068, CT + t + 0.00002)
    parts.append(snap)
    return parts


def clip():
    """Nickel alligator clip lying flat, jaws toward +Y."""
    y0, y1 = CLIP_Y0, CLIP_Y0 + CLIP_L
    parts = []
    base_pts = [(-CLIP_W / 2 + 0.002, y0), (CLIP_W / 2 - 0.002, y0), (CLIP_W / 2, y0 + 0.004),
                (CLIP_W / 2, y1 - 0.003), (CLIP_W / 2 - 0.003, y1), (-CLIP_W / 2 + 0.003, y1),
                (-CLIP_W / 2, y1 - 0.003), (-CLIP_W / 2, y0 + 0.004)]
    base = L.curve_solid("clip_base", [base_pts, L.circle(0.0016, 12, cy=y0 + 0.0040)], 0.0006,
                         bevel=0.00015, mat="M_Chrome")
    base.location = (0, 0, 0.0)
    parts.append(base)
    # side flanges of the base (turned-up edges)
    for sx in (-1, 1):
        fl = M.box("clip_flange", (0.0006, CLIP_L - 0.008, 0.0022), loc=(sx * (CLIP_W / 2 - 0.0003),
                   (y0 + y1) / 2 + 0.001, 0.0011), mat="M_Chrome", bevel=0.0002, segments=1)
        parts.append(fl)
    # hinge barrel across the clip
    hy = y0 + 0.0125
    parts.append(M.cylinder("clip_hinge", 0.0017, CLIP_W + 0.0008, loc=(0, hy, 0.0026), rot=(0, math.pi / 2, 0),
                            mat="M_Chrome", verts=12, bevel=0.0002, segments=1))
    # upper lever: press tab behind the hinge rising a little, jaw in front closing onto the base
    lever = []
    n = 10
    for i in range(n + 1):
        t = i / n
        y = y0 + 0.0050 + t * (y1 - y0 - 0.0050)
        z = 0.0042 - 0.0026 * max(0.0, (y - hy) / (y1 - hy)) ** 0.8 if y > hy else 0.0042 + 0.0012 * (hy - y) / 0.0075
        lever.append((y, z))
    w2 = CLIP_W / 2 - 0.0006
    verts, faces = [], []
    for (y, z) in lever:
        verts += [(-w2, y, z), (w2, y, z), (w2, y, z - 0.0006), (-w2, y, z - 0.0006)]
    for i in range(len(lever) - 1):
        a, b = 4 * i, 4 * (i + 1)
        faces += [(a, a + 1, b + 1, b), (a + 3, b + 3, b + 2, a + 2), (a, b, b + 3, a + 3), (a + 1, a + 2, b + 2, b + 1)]
    faces += [(0, 3, 2, 1), (4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3)]
    lv = C.D.mesh("clip_lever", verts, faces, mat="M_Chrome")
    me = lv.data
    me.update()
    score = sum((p.center - M.Vector((0, (y0 + y1) / 2, 0.003))).dot(p.normal) for p in me.polygons)
    if score < 0:
        me.flip_normals()
    parts.append(lv)
    # grip ridges on the press tab
    for k in range(3):
        y = y0 + 0.0060 + 0.0018 * k
        z = 0.0042 + 0.0012 * (hy - y) / 0.0075
        parts.append(M.box("clip_ridge", (CLIP_W - 0.004, 0.0005, 0.0004), loc=(0, y, z + 0.0001), mat="M_Chrome",
                           bevel=0.0001, segments=1))
    # teeth at the jaw tip (small wedge row)
    for k in range(5):
        x = -0.0048 + 0.0024 * k
        parts.append(C.D.wedge("clip_tooth", 0.0016, 0.0016, 0.0009, (x, y1 - 0.0014, 0.0006), direction_len=(0, 1, 0),
                               normal=(0, 0, 1), mat="M_Chrome", pyramid=True))
    # rivet holding the strap
    parts.append(L.rivet("clip_rivet", 0.0015, (0, y0 + 0.0040, 0.0006), normal=(0, 0, 1), mat="M_Chrome", segs=10))
    return parts


def cord():
    """Frayed stub of the old lanyard, knotted through the clip's hinge eye, curling to the right."""
    y = CLIP_Y0 + 0.0125
    pts = [(CLIP_W / 2 + 0.0012, y, 0.0026), (CLIP_W / 2 + 0.0055, y + 0.0035, 0.0016),
           (CLIP_W / 2 + 0.0120, y + 0.0020, 0.0011), (CLIP_W / 2 + 0.0185, y - 0.0050, 0.0011),
           (CLIP_W / 2 + 0.0215, y - 0.0150, 0.0011), (CLIP_W / 2 + 0.0190, y - 0.0235, 0.0011)]
    c = L.tube("cord", pts, 0.0011, mat="M_String_Red", bevel_res=1, res_u=5)
    knot = M.sphere("cord_knot", 0.0021, loc=(CLIP_W / 2 + 0.0030, y + 0.0012, 0.0020), segments=10, rings=6,
                    mat="M_String_Red", scale=(1.25, 0.95, 0.8))
    M.apply_transform(knot)
    # frayed end: three short splayed fibres
    end = pts[-1]
    fibres = []
    for k, a in enumerate((-0.5, 0.0, 0.55)):
        d = (math.sin(a) * 0.0045, -math.cos(a) * 0.0045)
        fibres.append(L.tube(f"fray{k}", [end, (end[0] + d[0] * 0.5, end[1] + d[1] * 0.5, 0.0007),
                                         (end[0] + d[0], end[1] + d[1], 0.0004)], 0.00035,
                             mat="M_String_Red", bevel_res=0, res_u=2))
    return [c, knot] + fibres


def build():
    loop = card_loop()
    card = L.curve_solid(NAME, [loop], CT, bevel=0.00015, mat="M_Paper")
    C.drop_cap(card, CT)
    face = L.flat_shape("badge_face", [loop], mat="M_Decal_Badge", loc=(0, 0, CT))
    hard = M.join([laminate()] + strap() + clip() + cord(), "badge_clip")
    M.set_parent(hard, card)
    M.set_parent(face, card)
    return [card]


def post():
    C.uv_rect_all(bpy.data.objects["badge_face"], -CW / 2, CW / 2, -CH / 2, CH / 2)


def main():
    C.item_main(NAME, build, post=post, required=("badge_face",), shots=[
        ("", (0.07, -0.13, 0.15), (0.0, 0.012, 0.0), 50),
        ("_2", C.inspect_cam(0.24), (0.0, 0.0, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
