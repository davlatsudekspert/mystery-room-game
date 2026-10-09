"""catalogue_tray.glb — the contents of a card-catalogue drawer (Chapter 2, group B1).

The game spawns ONE tray and parents it with an identity transform to `cat_tray_mount_<i>` of the open
drawer of card_catalogue.glb. Origin = the drawer's interior floor centre. +Z points out of the drawer
toward the player, X runs across the drawer.

Parts (all direct children of the root, origin = pivot, identity rotation at rest):
  * IA_divider_<g>, g = 0..9: pressboard guide cards (M_Cardboard) 0.13 w x 0.10 h x 1.8 mm, standing across
    the drawer at z = -0.17 + g * 0.33 / 9 (back -> front). Each carries a 0.035 x 0.022 tab at
    x = -0.045 / 0 / +0.045 (g % 3) with a cream insert and the 3D text "g–". Pivot = bottom centre; the code
    tilts the picked guide +20 deg about local +X (top toward the player).
  * IA_card_<n>, n = 0..9: plain cream index cards 0.125 x 0.075 x 0.4 mm with a blank 0.021 x 0.0125 tab at
    x = -0.05 / -0.025 / 0 / +0.025 / +0.05 (n % 5), tab centre y = 0.081. At rest a compact block behind
    divider 0. Pivot = bottom centre. The code moves them behind the picked divider (z = divider.z - 0.006 -
    n * 0.0026), lifts them and adds Label3D numbers at (tab_x, 0.081, +0.0008).
  * cards_filler (static): the packs of cards between the guides (ragged tops, h ~0.048) and the main mass
    of cards behind everything (to the drawer's back board).
  * tray_rod (static): the brass rod through the bottom holes (y = 0.010), from the drawer front to the back.

    blender -b --factory-startup -P tools/blender/models/catalogue_tray.py [-- --no-render]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_furniture1 as F  # noqa: E402
from lib_ch2_furniture1 import G, gbox, gquad, gtext, prism  # noqa: E402

NAME = "catalogue_tray"
BUDGET = 5000

# guides
DIV_W, DIV_H, DIV_T = 0.13, 0.10, 0.0018
TAB_W, TAB_H = 0.035, 0.022
DIV_Z0, DIV_Z1 = -0.17, 0.16
DIV_TAB_X = (-0.045, 0.0, 0.045)
# cards
CARD_W, CARD_H, CARD_T = 0.125, 0.075, 0.0004
CTAB_W, CTAB_H = 0.021, 0.0125
CARD_TAB_X = (-0.05, -0.025, 0.0, 0.025, 0.05)
CARD_REST_Z0, CARD_PITCH = DIV_Z0 - 0.0045, 0.0026
# drawer interior (card_catalogue.py): the front's inner face and the back board, in tray coordinates
FRONT_IN, BACK_IN = 0.177, -0.265
ROD_Y, ROD_R = 0.010, 0.0025
PACK_H = (0.0455, 0.0490)


def div_z(g: int) -> float:
    return DIV_Z0 + g * (DIV_Z1 - DIV_Z0) / 9.0


def card_rest_z(n: int) -> float:
    return CARD_REST_Z0 - n * CARD_PITCH


def rounded_tab(x0, x1, y0, y1, r, n=3):
    """Outline points (left -> right over the top) of a tab with rounded top corners."""
    pts = [(x0, y0)]
    for k in range(n + 1):
        a = math.pi - (math.pi / 2) * k / n
        pts.append((x0 + r + r * math.cos(a), y1 - r + r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi / 2 - (math.pi / 2) * k / n
        pts.append((x1 - r + r * math.cos(a), y1 - r + r * math.sin(a)))
    pts.append((x1, y0))
    return pts


def card_outline(w, h, tab_x, tab_w, tab_h, r_tab, r_body=0.0015):
    """Closed outline (x, y): body w x h with slightly rounded top corners and a rounded tab on top."""
    hw = w / 2
    pts = [(-hw, 0.0), (hw, 0.0), (hw, h - r_body), (hw - r_body * 0.3, h - r_body * 0.3), (hw - r_body, h)]
    tab = rounded_tab(tab_x - tab_w / 2, tab_x + tab_w / 2, h, h + tab_h, r_tab)
    pts += list(reversed(tab))
    pts += [(-hw + r_body, h), (-hw + r_body * 0.3, h - r_body * 0.3), (-hw, h - r_body)]
    return pts


def build_divider(g: int):
    z = div_z(g)
    tx = DIV_TAB_X[g % 3]
    body = prism(f"div_body{g}", card_outline(DIV_W, DIV_H, tx, TAB_W, TAB_H, 0.004, 0.003),
                 z - DIV_T / 2, z + DIV_T / 2, axis="z", mat="M_Cardboard")
    zf = z + DIV_T / 2
    insert = gquad(f"div_insert{g}", (tx, DIV_H + 0.0105, zf + 0.00015), (1, 0, 0), (0, 1, 0), 0.029, 0.0145, "M_Paper")
    # celluloid window rim (thin brass-coloured frame reads as the metal tab clip)
    rim = F.gpoly(f"div_rim{g}", [A.rounded_rect(0.0326, 0.0175, 0.0015, 2), A.rounded_rect(0.029, 0.0145, 0.001, 2)],
                  0.0003, (tx, DIV_H + 0.0105, zf), (1, 0, 0), (0, 1, 0), mat="M_Brass_Aged", bevel=0.0)
    txt = gtext(f"div_txt{g}", f"{g}–", 0.0128, (tx + 0.0004, DIV_H + 0.0103, zf + 0.0003), font=F.FONT_SANS_B,
                mat="M_Lacquer_Black", res=2)
    return F.part(f"IA_divider_{g}", [body, insert, rim, txt], pivot=(0.0, 0.0, z))


def build_card(n: int):
    z = card_rest_z(n)
    tx = CARD_TAB_X[n % 5]
    body = prism(f"card_body{n}", card_outline(CARD_W, CARD_H, tx, CTAB_W, CTAB_H, 0.0025, 0.001),
                 z - CARD_T / 2, z + CARD_T / 2, axis="z", mat="M_Paper")
    return F.part(f"IA_card_{n}", [body], pivot=(0.0, 0.0, z))


def build_filler():
    parts = []
    w = CARD_W - 0.001
    # packs between the guides (cards whose tabs are hidden in the pack)
    for g in range(1, 10):
        za, zb = div_z(g - 1) + DIV_T / 2 + 0.0004, div_z(g) - DIV_T / 2 - 0.0004
        parts.append(F.stepped_pack(f"pack{g}", za, zb, 0.0026, PACK_H[0], PACK_H[1], w, seed=100 + g))
    # the main mass behind the IA cards, to the back board
    za, zb = BACK_IN + 0.0008, card_rest_z(9) - CARD_T / 2 - 0.0022
    parts.append(F.stepped_pack("pack_back", za, zb, 0.0024, 0.0728, 0.0752, w, seed=7))
    # a few tabs sticking up from the back mass (old, slightly dog-eared)
    rnd = random.Random(11)
    nz = int((zb - za) / 0.0024)
    picks = sorted(rnd.sample(range(1, nz - 1), 9))
    for k, i in enumerate(picks):
        z = za + (i + 0.5) * (zb - za) / nz
        tx = rnd.choice(CARD_TAB_X)
        h = 0.0735 + rnd.uniform(-0.0006, 0.0008)
        parts.append(prism(f"pack_tab{k}", rounded_tab(tx - 0.0105, tx + 0.0105, h - 0.002, h + 0.0118, 0.0022, 2) ,
                           z - 0.0002, z + 0.0002, axis="z", mat="M_Paper"))
    return F.part("cards_filler", parts, pivot=(0.0, 0.0, 0.0))


def build_rod():
    rod = F.gcyl("rod_shaft", ROD_R, FRONT_IN - BACK_IN - 0.002, (0.0, ROD_Y, BACK_IN + 0.001), axis="z", verts=10,
                 mat="M_Brass_Aged", bevel=0.0006)
    collar = F.gcyl("rod_collar", ROD_R * 1.9, 0.004, (0.0, ROD_Y, BACK_IN + 0.0015), axis="z", verts=10,
                    mat="M_Brass_Aged", bevel=0.0006)
    return F.part("tray_rod", [rod, collar], pivot=(0.0, 0.0, 0.0))


def build():
    M.reset_scene()
    F.ensure_materials()
    for g in range(10):
        build_divider(g)
    for n in range(10):
        build_card(n)
    build_filler()
    build_rod()
    F.finalize_all(wood_grain=False)
    return F.report(NAME)


def verify(path):
    required = [f"IA_divider_{g}" for g in range(10)] + [f"IA_card_{n}" for n in range(10)] + ["cards_filler", "tray_rod"]
    expect = {f"IA_divider_{g}": (0.0, 0.0, round(div_z(g), 6)) for g in range(10)}
    expect.update({f"IA_card_{n}": (0.0, 0.0, round(card_rest_z(n), 6)) for n in range(10)})
    return F.verify_glb(path, required=required, identity=required, budget=BUDGET, expect=expect,
                        top_level=required, show=["IA_divider_0", "IA_divider_9", "IA_card_0", "IA_card_9"])


# ---------------------------------------------------------------- QA
def proxy_drawer():
    """QA-only drawer box around the tray (the real one is in card_catalogue.glb)."""
    wd = "M_Wood_Panel"
    gbox("qa_dr_bottom", (-0.08, -0.004, BACK_IN - 0.008), (0.08, 0.0, FRONT_IN), wd, 0.0005)
    for s in (-1, 1):
        gbox(f"qa_dr_side{s}", (s * 0.072, -0.004, BACK_IN - 0.008), (s * 0.080, 0.065, FRONT_IN), wd, 0.001)
    gbox("qa_dr_back", (-0.072, 0.0, BACK_IN - 0.008), (0.072, 0.055, BACK_IN), wd, 0.001)
    gbox("qa_dr_front", (-0.105, -0.004, FRONT_IN), (0.105, 0.141, FRONT_IN + 0.022), "M_Wood_Walnut", 0.002)
    gbox("qa_table", (-0.6, -0.034, -0.6), (0.6, -0.004, 0.6), "M_Felt", 0.0)


def pose_code(objs, g, open_drawer=4, shown=False):
    """Replicates ArchiveVisuals._apply_catalogue for divider g (QA only)."""
    div = objs[f"IA_divider_{g}"]
    F.pose_rot(div, "x", 20.0)
    dz = div_z(g)
    for n in range(10):
        c = objs[f"IA_card_{n}"]
        lift = 0.014 + (0.02 if n >= 5 else 0.0)
        if shown and n == 7:
            lift = 0.07
        F.pose_to(c, (0.0, lift, dz - 0.006 - n * 0.0026))
        tx = CARD_TAB_X[n % 5]
        txt = f"{g}{n}" if not (shown and n == 7) else f"{open_drawer:02d}{g}{n}"
        lbl = gtext(f"qa_lbl{n}", txt, 0.0115 * 0.92, (tx, 0.081, 0.0008), font=F.FONT_SANS_B, mat="qa_label_ink")
        lbl.parent = c
        lbl.matrix_parent_inverse = F.Matrix.Identity(4)
        M.refresh()


def main():
    args = M.main_guard()
    build()
    path = F.export(NAME)
    F.check_names(path)
    errs = verify(path)
    if errs:
        print(f"{F.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    F.qa_begin()
    M.material("qa_label_ink", color="2B2118", rough=0.8)
    objs = {o.name: o for o in bpy_objects()}
    proxy_drawer()
    F.qa_light("key", "AREA", (0.35, 0.75, 0.55), 22.0, "FFE2C0", radius=0.6, target=(0.0, 0.05, -0.02))
    F.qa_light("fill", "AREA", (-0.6, 0.4, 0.3), 6.0, "C8D8FF", radius=0.8, target=(0.0, 0.05, 0.0))
    F.qa_light("rim", "AREA", (0.0, 0.6, -0.7), 8.0, "FFFFFF", radius=0.5, target=(0.0, 0.05, -0.1))
    if F.want("rest", args):
        F.shoot(NAME, (0.24, 0.36, 0.42), (0.0, 0.04, -0.04), vfov=40)
    if F.want("posed", args):
        pose_code(objs, 1)
        F.shoot(NAME + "_2", (0.10, 0.30, 0.30), (0.0, 0.05, -0.12), vfov=36)


def bpy_objects():
    import bpy
    return list(bpy.context.scene.objects)


main()
