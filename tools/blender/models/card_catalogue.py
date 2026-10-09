"""card_catalogue.glb — walnut library card-catalogue cabinet on a turned-leg stand (Chapter 2, group B1).

Wall-mounted furniture: origin = floor level, centre of the BACK face (z = 0); front faces +Z.
Placement: (-5.0, 0, -1.2), yaw 90 (front faces world +X).

  * stand 0.58 high: four turned legs with brass ferrules, apron, H-stretcher;
  * body 0.64 w x 0.86 h x 0.48 d (y 0.58 .. 1.44), panelled sides, face frame;
  * brass-edged top with a sloped reading ledge (brass paper lip);
  * 10 drawers, 2 columns x 5 rows, i = row * 2 + column (row 0 = top, column 0 = left seen from the front),
    fronts read 00 01 / 02 03 / 04 05 / 06 07 / 08 09. Each front: brass label holder with a cream card and the
    number in 3D text, brass cup pull, brass rod-lock nut (aligned with the tray rod).

Parts:
  * IA_cat_drawer_<i>: one object per drawer, pivot = front-face centre, identity at rest; the code slides it
    +0.30 along local +Z. Interior 0.144 w x 0.442 d. The back-top edge of the front is chamfered so the
    contents stay visible from the code's cat_drawer camera.
  * cat_tray_mount_<i>: child empty of each drawer at the interior floor (x centre), z = 0.280 model
    (0.039 forward of the geometric interior centre 0.241; see docs/models/ch2_furniture1.md).
  * static: carcass (sides, back, top, ledge), carcass_row_<r> (face-frame slice + dust board + runners of row r),
    stand.

    blender -b --factory-startup -P tools/blender/models/card_catalogue.py [-- --no-render] [-- --shots a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_ch2_furniture1 as F  # noqa: E402
from lib_ch2_furniture1 import G, gbox, gcyl, gquad, gtext, prism  # noqa: E402

NAME = "card_catalogue"
BUDGET = 9000
WOOD, WOOD_IN, BOX = "M_Wood_Walnut", "M_Wood_Walnut", "M_Wood_Panel"
BR, PAPER, INK = "M_Brass_Aged", "M_Paper", "M_Lacquer_Black"

# body
HW, D = 0.32, 0.48                  # half width, depth (back at z = 0)
Y0, Y1 = 0.58, 1.44                 # body bottom / top
FF = 0.462                          # face frame back (front at D)
# rows (row 0 = top)
OPEN_H, RAIL, PITCH = 0.157, 0.004, 0.161
TOP_OPEN = 1.419
# columns
COL_X = (-0.1425, 0.1425)
OPEN_HW, FRONT_HW = 0.1075, 0.105
# drawer
FRONT_Z0, FRONT_Z1 = 0.462, 0.484   # drawer front (pivot plane z = 0.484)
BOX_HW, BOX_T = 0.080, 0.008
BACK_Z0, BACK_Z1 = 0.012, 0.020     # drawer back board
FLOOR_UP = 0.006                    # interior floor above the opening bottom
MOUNT_Z = 0.280                     # tray origin (divider 9 sits 44.5 mm behind the front face)
ROD_Y = 0.010                       # tray rod height above the floor (catalogue_tray.py)
TRAVEL = 0.30                       # ArchiveVisuals.CAT_DRAWER_TRAVEL


def row_y(r):
    """(bottom, top) of opening row r."""
    top = TOP_OPEN - r * PITCH
    return top - OPEN_H, top


def drawer_geom(i):
    r, c = divmod(i, 2)
    yb, yt = row_y(r)
    xc = COL_X[c]
    yc = (yb + yt) / 2
    return r, c, xc, yb, yt, yc


# ---------------------------------------------------------------- drawer
def chamfer_rect(w, h, c):
    hw, hh = w / 2, h / 2
    return [(-hw + c, -hh), (hw - c, -hh), (hw, -hh + c), (hw, hh - c), (hw - c, hh), (-hw + c, hh), (-hw, hh - c),
            (-hw, -hh + c)]


def label_holder(i, xc, y, zf):
    """Brass frame with a cream card and the drawer number."""
    parts = []
    frame = F.gpoly(f"lh_frame{i}", [chamfer_rect(0.068, 0.034, 0.003), chamfer_rect(0.058, 0.025, 0.0012)],
                    0.0026, (xc, y, zf), (1, 0, 0), (0, 1, 0), mat=BR, bevel=0.0, drop_bottom=True)
    parts.append(frame)
    parts.append(gquad(f"lh_card{i}", (xc, y, zf + 0.0009), (1, 0, 0), (0, 1, 0), 0.0592, 0.0262, PAPER))
    parts.append(gtext(f"lh_txt{i}", f"{i:02d}", 0.0215, (xc, y - 0.0002, zf + 0.0013), font=F.FONT_SANS_B,
                       mat=INK, res=2))
    return parts


def cup_pull(i, xc, y, zf):
    """Brass cup (bin) pull: back plate + hood open at the bottom."""
    parts = []
    plate = F.gpoly(f"cp_plate{i}", [chamfer_rect(0.082, 0.032, 0.006)], 0.0018, (xc, y, zf), (1, 0, 0), (0, 1, 0),
                    mat=BR, bevel=0.0, drop_bottom=True)
    parts.append(plate)
    # hood profile in (z, y) relative to the plate centre, extruded across x
    outer, inner = [], []
    n = 5
    for k in range(n + 1):
        t = (math.pi / 2) * k / n
        outer.append((0.0018 + 0.0175 * math.sin(t), -0.004 + 0.0155 * math.cos(t)))
        inner.append((0.0018 + 0.0158 * math.sin(t), -0.004 + 0.0139 * math.cos(t)))
    loop = outer + [(0.0193, -0.0095), (0.0177, -0.0095)] + list(reversed(inner))
    loop = [(zf + zz, y + yy) for (zz, yy) in loop]
    hood = prism(f"cp_hood{i}", loop, xc - 0.034, xc + 0.034, axis="x", mat=BR)
    parts.append(A.hint(hood, 50.0))
    for s in (-1, 1):
        parts.append(F.gcyl(f"cp_screw{i}{s}", 0.0021, 0.0008, (xc + s * 0.0365, y + 0.001, zf + 0.0018), axis="z",
                            verts=6, mat=BR, bevel=0.0, smooth=0))
    return parts


def rod_nut(i, xc, y, zf):
    rose = F.glathe(f"rn_rose{i}", [(0.0082, 0.0), (0.0082, 0.0009), (0.0, 0.0016)], (xc, y, zf),
                    axis="z", segments=10, mat=BR)
    nut = F.glathe2(f"rn_nut{i}", [(0.0050, 0.0012, "k"), (0.0050, 0.0072, "k"), (0.0036, 0.0086), (0.0, 0.0090)],
                    (xc, y, zf), axis="z", segments=12, mat=BR, knurl=0.0005, cap_bottom=False)
    return [rose, nut]


def build_drawer(i):
    r, c, xc, yb, yt, yc = drawer_geom(i)
    yf = yb + FLOOR_UP
    parts = []
    fy0, fy1 = yb + 0.002, yt - 0.002
    # front: chamfered back-top edge (keeps the guide tabs visible from above), rounded front edges
    prof = [(FRONT_Z0, fy0), (FRONT_Z1, fy0), (FRONT_Z1, fy1), (FRONT_Z1 - 0.003, fy1), (FRONT_Z0, fy1 - 0.020)]
    front = prism(f"dr_front{i}", prof, xc - FRONT_HW, xc + FRONT_HW, axis="x", mat=WOOD, bevel=0.0024, seg=1,
                  angle=50.0)
    parts.append(front)
    # box
    parts.append(gbox(f"dr_bottom{i}", (xc - BOX_HW, yb + 0.002, BACK_Z0), (xc + BOX_HW, yf, FRONT_Z0), BOX, 0.0))
    for s in (-1, 1):
        x0, x1 = sorted((xc + s * (BOX_HW - BOX_T), xc + s * BOX_HW))
        parts.append(gbox(f"dr_side{i}{s}", (x0, yb + 0.002, BACK_Z0), (x1, yf + 0.064, FRONT_Z0), BOX, 0.0))
    parts.append(gbox(f"dr_back{i}", (xc - BOX_HW + BOX_T, yf, BACK_Z0), (xc + BOX_HW - BOX_T, yf + 0.052, BACK_Z1),
                      BOX, 0.0))
    # hardware
    parts += label_holder(i, xc, yc + 0.039, FRONT_Z1)
    parts += cup_pull(i, xc, yc - 0.006, FRONT_Z1)
    parts += rod_nut(i, xc, yf + ROD_Y, FRONT_Z1)
    drawer = F.part(f"IA_cat_drawer_{i}", parts, pivot=(xc, yc, FRONT_Z1))
    F.mount(f"cat_tray_mount_{i}", (xc, yf, MOUNT_Z), par=drawer)
    return drawer


# ---------------------------------------------------------------- carcass
def face_frame_slice(name, y0, y1, holes):
    """Face-frame slab (z FF..D) between y0 and y1 with rectangular holes [(x0, x1, ya, yb)]."""
    loops = [[(-HW + 0.02, y0), (HW - 0.02, y0), (HW - 0.02, y1), (-HW + 0.02, y1)]]
    for (x0, x1, ya, yb) in holes:
        loops.append([(x0, ya), (x1, ya), (x1, yb), (x0, yb)])
    return F.gpoly(name, loops, D - FF, (0.0, 0.0, FF), (1, 0, 0), (0, 1, 0), mat=WOOD, bevel=0.0015)


def build_row(r):
    yb, yt = row_y(r)
    parts = []
    y0 = yb - RAIL / 2 if r < 4 else Y0 + 0.02
    y1 = yt + RAIL / 2 if r > 0 else TOP_OPEN
    holes = [(xc - OPEN_HW, xc + OPEN_HW, yb, yt) for xc in COL_X]
    parts.append(face_frame_slice(f"ff_row{r}", y0, y1, holes))
    # dust board under the row (the rail's depth), runners, column partition slice
    if r < 4:
        parts.append(gbox(f"dust{r}", (-HW + 0.02, yb - RAIL, 0.006), (HW - 0.02, yb, FF), WOOD_IN, 0.0))
    for xc in COL_X:
        for s in (-1, 1):
            xa, xb = sorted((xc + s * (BOX_HW + 0.001), xc + s * OPEN_HW))
            parts.append(gbox(f"runner{r}{xc}{s}", (xa, yb, 0.006), (xb, yb + 0.03, FF), WOOD_IN, 0.0))
    parts.append(gbox(f"partition{r}", (-0.01, yb, 0.006), (0.01, yt, FF), WOOD_IN, 0.0))
    return F.part(f"carcass_row_{r}", parts)


def build_carcass():
    parts = []
    # sides with a raised field outside
    for s in (-1, 1):
        x0, x1 = sorted((s * (HW - 0.02), s * HW))
        parts.append(gbox(f"side{s}", (x0, Y0, 0.0), (x1, Y1, D), WOOD, 0.003))
        fm = F.frame((s * HW, 0.0, 0.0), (0, 0, -s), (0, 1, 0))     # local a = along -s*z, b = up, out = +s*x
        a0, a1 = sorted((-s * 0.04, -s * (D - 0.04)))
        parts.append(A.raised_field(f"side_field{s}", a0, a1, Y0 + 0.07, Y1 - 0.07, 0.016, 0.005, fm, mat=WOOD))
    parts.append(gbox("back", (-HW + 0.02, Y0, 0.0), (HW - 0.02, Y1, 0.006), WOOD_IN, 0.0))
    parts.append(gbox("bottom", (-HW + 0.02, Y0, 0.006), (HW - 0.02, Y0 + 0.02 + 0.02, FF), WOOD_IN, 0.0))
    parts.append(gbox("body_top", (-HW + 0.02, TOP_OPEN, 0.006), (HW - 0.02, Y1, FF), WOOD_IN, 0.0))
    # face-frame bottom and top rails + outer stiles are in the row slices; base moulding (skirt)
    parts.append(gbox("skirt", (-HW - 0.008, Y0 - 0.006, -0.0), (HW + 0.008, Y0 + 0.024, D + 0.008), WOOD, 0.004, 2))
    parts.append(gbox("ff_top", (-HW + 0.02, TOP_OPEN, FF), (HW - 0.02, Y1, D), WOOD, 0.0015))
    # top board with a rounded edge, brass edging on three sides
    parts.append(gbox("top", (-HW - 0.015, Y1, 0.0), (HW + 0.015, Y1 + 0.022, D + 0.02), WOOD, 0.006, 3))
    parts.append(gbox("edge_front", (-HW - 0.016, Y1 + 0.0015, D + 0.0195), (HW + 0.016, Y1 + 0.0205, D + 0.0222), BR, 0.0006))
    for s in (-1, 1):
        x0, x1 = sorted((s * (HW + 0.0145), s * (HW + 0.0172)))
        parts.append(gbox(f"edge_side{s}", (x0, Y1 + 0.0015, 0.004), (x1, Y1 + 0.0205, D + 0.022), BR, 0.0006))
    # sloped reading ledge (15 deg) on cheeks, with a brass paper lip
    yt = Y1 + 0.022
    ang = 15.0
    L = 0.215
    cz, cy = 0.383, yt + 0.0405
    parts.append(F.gbox_c("ledge", (0.0, cy, cz), (2 * HW - 0.01, 0.016, L), WOOD, 0.004, 2, pitch=ang))
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def on_board(v, w):          # board-local (up v, forward w) -> Godot (y, z)
        return cy + v * ca - w * sa, cz + v * sa + w * ca
    fy, fz = on_board(0.008, L / 2)
    by, bz = on_board(-0.008, -L / 2 + 0.01)
    for s in (-1, 1):
        x0, x1 = sorted((s * (HW - 0.012), s * (HW - 0.032)))
        tri = [(fz - 0.004, yt), (bz, yt), (bz, by - 0.002)]
        parts.append(prism(f"cheek{s}", tri, x0, x1, axis="x", mat=WOOD, bevel=0.0015))
    ly, lz = on_board(0.0145, L / 2 - 0.004)
    parts.append(F.gbox_c("ledge_lip", (0.0, ly, lz), (2 * HW - 0.06, 0.013, 0.0035), BR, 0.0008, 1, pitch=ang))
    for s in (-1, 1):
        parts.append(F.gbox_c(f"lip_post{s}", (s * (HW - 0.045), ly - 0.002, lz - 0.003), (0.008, 0.016, 0.008), BR,
                              0.001, 1, pitch=ang))
    return F.part("carcass", parts)


def build_stand():
    parts = []
    legs = [(sx * 0.275, sz) for sx in (-1, 1) for sz in (0.045, 0.435)]
    prof = [(0.0172, 0.0), (0.0172, 0.026), (0.0158, 0.030),                                   # brass ferrule
            (0.0185, 0.037), (0.0128, 0.065), (0.0168, 0.170), (0.0226, 0.290), (0.0200, 0.355), (0.0146, 0.408),
            (0.0204, 0.426), (0.0168, 0.444), (0.0246, 0.462)]
    bands = [BR] * 2 + [WOOD] * (len(prof) - 3)
    for k, (x, z) in enumerate(legs):
        leg = F.glathe2(f"leg{k}", prof, (x, 0.0, z), axis="y", segments=10, mat=WOOD, band_mats=bands, cap_top=False)
        parts.append(leg)
        parts.append(gbox(f"leg_block{k}", (x - 0.025, 0.46, z - 0.025), (x + 0.025, Y0 - 0.006, z + 0.025), WOOD, 0.002))
    # apron
    ya, yb = 0.50, Y0 - 0.006
    parts.append(gbox("apron_f", (-0.25, ya, 0.437), (0.25, yb, 0.455), WOOD, 0.0015))
    parts.append(gbox("apron_b", (-0.25, ya, 0.025), (0.25, yb, 0.043), WOOD, 0.0015))
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.266, s * 0.284))
        parts.append(gbox(f"apron_s{s}", (x0, ya, 0.07), (x1, yb, 0.41), WOOD, 0.0015))
    # apron bead (small moulding along the front apron bottom)
    parts.append(F.gcyl("apron_bead", 0.004, 0.50, (-0.25, ya + 0.002, 0.455), axis="x", verts=8, mat=WOOD, bevel=0.0))
    # H-stretcher
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.264, s * 0.286))
        parts.append(gbox(f"stretch_s{s}", (x0, 0.105, 0.06), (x1, 0.13, 0.42), WOOD, 0.002))
    parts.append(gbox("stretch_x", (-0.265, 0.108, 0.229), (0.265, 0.127, 0.251), WOOD, 0.002))
    return F.part("stand", parts)


def build():
    M.reset_scene()
    F.ensure_materials()
    build_stand()
    build_carcass()
    for r in range(5):
        build_row(r)
    for i in range(10):
        build_drawer(i)
    F.finalize_all(wood_grain=True)
    return F.report(NAME)


def verify(path):
    req = [f"IA_cat_drawer_{i}" for i in range(10)] + [f"cat_tray_mount_{i}" for i in range(10)]
    expect = {}
    for i in range(10):
        r, c, xc, yb, yt, yc = drawer_geom(i)
        expect[f"IA_cat_drawer_{i}"] = (round(xc, 5), round(yc, 5), FRONT_Z1)
        expect[f"cat_tray_mount_{i}"] = (round(xc, 5), round(yb + FLOOR_UP, 5), round(MOUNT_Z, 5))
    return F.verify_glb(path, required=req, identity=req, budget=BUDGET, expect=expect,
                        show=["IA_cat_drawer_0", "IA_cat_drawer_4", "cat_tray_mount_4", "IA_cat_drawer_9"])


# ---------------------------------------------------------------- QA
POS, YAW = (-5.0, 0.0, -1.2), 90.0


def to_world(p):
    """Model -> world (Godot) for the placement (yaw 90: model +X = world -Z, model +Z = world +X)."""
    a = math.radians(YAW)
    x, y, z = p
    return (POS[0] + x * math.cos(a) + z * math.sin(a), POS[1] + y, POS[2] - x * math.sin(a) + z * math.cos(a))


def cat_drawer_cam(i, travel=TRAVEL):
    """ArchiveVisuals.frame_cat_drawer(i)."""
    r, c, xc, yb, yt, yc = drawer_geom(i)
    front = to_world((xc, yc, FRONT_Z1 + travel))
    out = (1.0, 0.0, 0.0)
    cam = (front[0] + out[0] * 0.42, front[1] + 0.5, front[2])
    tgt = (front[0] - out[0] * 0.2, front[1] - 0.05, front[2])
    return cam, tgt


def qa_tray(objs, g=1, open_i=4, shown=False):
    """Pose the imported tray like ArchiveVisuals._apply_catalogue (divider g picked)."""
    tray = {o.name[3:]: o for o in bpy.context.scene.objects if o.name.startswith("qa_IA_")}
    div = tray.get(f"IA_divider_{g}")
    if div is None:
        return
    F.pose_rot(div, "x", 20.0)
    M.refresh()
    dz = div.matrix_basis.translation.y * -1.0          # Blender -y = Godot z (tray holder is at identity)
    tab_x = (-0.05, -0.025, 0.0, 0.025, 0.05)
    for n in range(10):
        c = tray[f"IA_card_{n}"]
        lift = 0.014 + (0.02 if n >= 5 else 0.0)
        if shown and n == 7:
            lift = 0.07
        F.pose_to(c, (0.0, lift, dz - 0.006 - n * 0.0026))
        txt = f"{g}{n}" if not (shown and n == 7) else f"{open_i:02d}{g}{n}"
        lbl = gtext(f"qa_lbl{n}", txt, 0.0106, (tab_x[n % 5], 0.081, 0.0008), font=F.FONT_SANS_B, mat="qa_label_ink")
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
    drawers = {i: bpy.data.objects[f"IA_cat_drawer_{i}"] for i in range(10)}
    mount4 = bpy.data.objects["cat_tray_mount_4"]
    F.qa_place(POS, YAW)
    F.qa_room()
    F.qa_neighbours([("library_ladder", (-4.62, 0, 0.35), 90.0), ("vent_grille", (-5.0, 2.55, 0.9), 90.0),
                     ("echo_archivist", (-4.05, 0, -1.05), -90.0)])
    F.qa_room_lights(150.0)
    F.qa_light("fill", "AREA", (-3.0, 1.9, -0.6), 60.0, "FFE6CC", radius=1.2, target=(-4.8, 1.0, -1.2))
    if F.want("hero", args):
        F.shoot(NAME, (-3.35, 1.55, -0.15), (-4.75, 1.0, -1.25), vfov=46)
    if F.want("view", args):
        F.shoot(NAME + "_2", (-3.55, 1.5, -1.2), (-4.7, 1.0, -1.2), vfov=50)
    # open drawer 4 with the tray, divider 1 picked, cards fanned (code poses), code camera
    F.pose_slide(drawers[4], (0.0, 0.0, TRAVEL))
    F.item_or_proxy("catalogue_tray", mount4)
    if F.want("drawer", args):
        qa_tray(None, g=1, open_i=4)
        cam, tgt = cat_drawer_cam(4)
        F.shoot(NAME + "_3", cam, tgt, vfov=44)
    if F.want("drawer36", args):
        F.pose_slide(drawers[4], (0.0, 0.0, 0.06))
        cam, tgt = cat_drawer_cam(4, 0.36)
        F.shoot(NAME + "_4", cam, tgt, vfov=44)


main()
