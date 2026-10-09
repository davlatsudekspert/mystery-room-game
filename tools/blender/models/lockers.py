"""lockers.glb — bank of 12 steel staff lockers, 2 rows x 6 (Chapter 2, group B1).

Wall-mounted furniture: origin = floor level, centre of the BACK face (z = 0); front faces +Z.
Placement: (0.6, 0, 3.5), yaw 180 (front faces world -Z; model +X = world -X, so world x = 0.6 - model x).

  * 2.40 w (six columns x 0.40) x 1.85 h x 0.45 d, green-grey enamelled steel (M_Steel_Painted);
  * recessed dark plinth 0.10, top cornice; doors 0.396 x 0.856 on a 0.40 x 0.86 grid (4 mm gaps);
  * every door: pressed louvres top and bottom, cream enamel number plate (3D text 1..12), brass keyhole
    escutcheon, chrome lift handle, two hinge knuckles on the left edge.

Numbering: top row 1..6 left -> right seen from the front (model -X -> +X), bottom row 7..12.
Locker 9 = bottom row, third from the left: model x centre -0.2 (world x 0.8).

Parts:
  * IA_locker_<n>, n = 1..12: the door; pivot on its LEFT edge (seen from the front, the hinge axis in the
    4 mm gap, on the front-face plane z = 0.45) at the door's mid height; identity at rest; open = -105 deg
    about local +Y.
  * receiver_mount: in locker 9, on the J-hook under the hat shelf; pocket_receiver.glb (identity) hangs there by
    its strap loop, face +Z (the empty is at the receiver's centre of mass, 0.0952 below the hook's catch point).
  * static: lockers_body (carcass, frame, plinth, cornice), locker9_interior (liner, hat shelf, hook, mirror).

    blender -b --factory-startup -P tools/blender/models/lockers.py [-- --no-render] [-- --shots a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_furniture1 as F  # noqa: E402
from lib_ch2_furniture1 import G, gbox, gtext, prism  # noqa: E402

NAME = "lockers"
BUDGET = 9000
ST, DK, CR, BR, EN, INK = "M_Steel_Painted", "M_Steel_Dark", "M_Chrome", "M_Brass_Aged", "M_Enamel_Cream", "M_Lacquer_Black"

HW, D, H = 1.20, 0.45, 1.85
PLINTH = 0.10
COLS, PITCH_X = 6, 0.40
ROW_Y = ((0.964, 1.820), (0.104, 0.960))      # row 0 = top doors, row 1 = bottom doors (door leaf y range)
GAP = 0.002                                    # half of the 4 mm gap between doors
DOOR_Z0, DOOR_Z1 = 0.432, 0.450                # door pan (front face z = 0.45)
FRAME_Z0, FRAME_Z1 = 0.415, 0.432              # face frame behind the doors
OPEN_DEG = -105.0                              # ArchiveVisuals.LOCKER_OPEN_DEG
LEYLA = 9
# receiver hook (locker 9)
SHELF_Y = 0.775
HOOK_Z = 0.287
ROD_R = 0.0028


def locker_cell(n):
    """(column, row, x0, x1, y0, y1) of locker n's door leaf."""
    row = 0 if n <= 6 else 1
    col = (n - 1) % 6
    xa = -HW + col * PITCH_X
    y0, y1 = ROW_Y[row]
    return col, row, xa + GAP, xa + PITCH_X - GAP, y0, y1


# ---------------------------------------------------------------- doors
def louvre_bank(tag, xc, ytop, count, width=0.17, pitch=0.0165):
    """Pressed louvres (hoods open at the bottom) on the door front, top louvre at ytop."""
    parts = []
    z = DOOR_Z1
    for k in range(count):
        yl = ytop - k * pitch - 0.011
        hood = prism(f"lv{tag}_{k}", [(z - 0.0004, yl + 0.011), (z + 0.0042, yl), (z - 0.0004, yl)],
                     xc - width / 2, xc + width / 2, axis="x", mat=ST)
        K_mat_down(hood)
        parts.append(hood)
    return parts


def K_mat_down(obj):
    """Downward-facing louvre opening -> dark steel (reads as the slot)."""
    idx = M.add_slot(obj, DK)
    for p in obj.data.polygons:
        if p.normal.z < -0.7:          # Blender -Z = Godot -Y (down)
            p.material_index = idx


def number_plate(n, xc, y):
    parts = []
    plate = F.gpoly(f"np_plate{n}", [A.rounded_rect(0.086, 0.050, 0.008, 1)], 0.0022, (xc, y, DOOR_Z1), (1, 0, 0),
                    (0, 1, 0), mat=EN, bevel=0.0, drop_bottom=True)
    parts.append(plate)
    parts.append(F.gpoly(f"np_rim{n}", [A.rounded_rect(0.090, 0.054, 0.009, 1), A.rounded_rect(0.086, 0.050, 0.008, 1)],
                         0.0026, (xc, y, DOOR_Z1), (1, 0, 0), (0, 1, 0), mat=CR, bevel=0.0, drop_bottom=True))
    parts.append(gtext(f"np_txt{n}", str(n), 0.044, (xc, y, DOOR_Z1 + 0.0024), font=F.FONT_SANS_B, mat=INK, res=2))
    for s in (-1, 1):
        parts.append(F.gcyl(f"np_rivet{n}{s}", 0.0024, 0.0008, (xc + s * 0.036, y, DOOR_Z1 + 0.0022), axis="z", verts=6,
                            mat=CR, bevel=0.0, smooth=0))
    return parts


def keyhole(n, x, y):
    esc = F.glathe(f"kh_esc{n}", [(0.0115, 0.0), (0.0100, 0.0020), (0.0, 0.0028)], (x, y, DOOR_Z1),
                   axis="z", segments=10, mat=BR)
    slot = [(-0.0016, -0.0062), (0.0016, -0.0062), (0.0013, -0.0005)] + \
           [(0.0029 * math.cos(a), 0.0016 + 0.0029 * math.sin(a)) for a in
            [math.radians(-60 + 300 * k / 7) for k in range(8)]] + [(-0.0013, -0.0005)]
    hole = F.gpoly(f"kh_hole{n}", [slot], 0.0004, (x, y, DOOR_Z1 + 0.0027), (1, 0, 0), (0, 1, 0), mat="M_Bakelite",
                   bevel=0.0, drop_bottom=True)
    return [esc, hole]


def lift_handle(n, x, y):
    """Chrome lift handle: escutcheon plate + a vertical pull bar on two posts."""
    parts = []
    parts.append(F.gpoly(f"lh_plate{n}", [A.rounded_rect(0.030, 0.110, 0.012, 2)], 0.003, (x, y, DOOR_Z1), (1, 0, 0),
                         (0, 1, 0), mat=CR, bevel=0.0, drop_bottom=True))
    bar = A.tube(f"lh_bar{n}", [G(x, y - 0.040, DOOR_Z1 + 0.002), G(x, y - 0.040, DOOR_Z1 + 0.020),
                                G(x, y + 0.040, DOOR_Z1 + 0.020), G(x, y + 0.040, DOOR_Z1 + 0.002)],
                 0.0055, sides=6, fillet=0.010, fillet_segs=2, mat=CR)
    parts.append(bar)
    return parts


def build_door(n):
    col, row, x0, x1, y0, y1 = locker_cell(n)
    xc = (x0 + x1) / 2
    ym = (y0 + y1) / 2
    parts = []
    pan = gbox(f"door_pan{n}", (x0, y0, DOOR_Z0), (x1, y1, DOOR_Z1), ST, 0.003, 1)
    parts.append(pan)
    parts += louvre_bank(f"t{n}", xc, y1 - 0.045, 6)
    parts += louvre_bank(f"b{n}", xc, y0 + 0.145, 6)
    parts += number_plate(n, xc, y1 - 0.205)
    hx = x1 - 0.045
    parts += keyhole(n, hx, ym + 0.085)
    parts += lift_handle(n, hx, ym - 0.005)
    # hinge knuckles on the left edge (the hinge axis = pivot line)
    for k, dy in enumerate((0.31, -0.31)):
        parts.append(F.gcyl(f"knuckle{n}{k}", 0.0045, 0.05, (x0 - GAP, ym + dy - 0.025, DOOR_Z1), axis="y", verts=6,
                            mat=ST, bevel=0.0))
    door = F.part(f"IA_locker_{n}", parts, pivot=(x0 - GAP, ym, DOOR_Z1))
    return door


# ---------------------------------------------------------------- carcass
def build_body():
    parts = []
    # plinth (recessed, dark) and the bottom pan
    parts.append(gbox("plinth", (-HW + 0.01, 0.0, 0.02), (HW - 0.01, PLINTH, D - 0.035), DK, 0.002))
    parts.append(gbox("bottom_pan", (-HW, PLINTH - 0.004, 0.0), (HW, 0.104, D - 0.005), ST, 0.002))
    # sides, back, top
    for s in (-1, 1):
        x0, x1 = sorted((s * (HW - 0.012), s * HW))
        parts.append(gbox(f"side{s}", (x0, PLINTH - 0.004, 0.0), (x1, 1.824, D - 0.002), ST, 0.002))
    parts.append(gbox("back", (-HW, PLINTH, 0.0), (HW, 1.824, 0.008), ST, 0.0))
    # cornice: a pressed top with a front flange
    parts.append(gbox("top", (-HW - 0.004, 1.824, -0.0), (HW + 0.004, 1.842, D + 0.006), ST, 0.003, 2))
    parts.append(gbox("cornice", (-HW - 0.008, 1.836, D - 0.03), (HW + 0.008, H, D + 0.010), ST, 0.004, 2))
    # face frame behind the doors: stiles at every column boundary, rails at the bottom, middle and top
    for c in range(COLS + 1):
        x = -HW + c * PITCH_X
        xa, xb = x - 0.014, x + 0.014
        xa, xb = max(xa, -HW), min(xb, HW)
        parts.append(gbox(f"stile{c}", (xa, PLINTH, FRAME_Z0), (xb, 1.824, FRAME_Z1), ST, 0.001))
    for (ya, yb) in ((PLINTH, 0.116), (0.948, 0.976), (1.808, 1.824)):
        parts.append(gbox(f"rail{ya:.3f}", (-HW, ya, FRAME_Z0), (HW, yb, FRAME_Z1), ST, 0.001))
    # the frame fill behind the closed doors (all except locker 9): a dark panel just behind the opening so a gap
    # never shows daylight
    for n in range(1, 13):
        if n == LEYLA:
            continue
        col, row, x0, x1, y0, y1 = locker_cell(n)
        parts.append(gbox(f"blind{n}", (x0 + 0.010, y0 + 0.010, FRAME_Z0 - 0.004), (x1 - 0.010, y1 - 0.010, FRAME_Z0),
                          DK, 0.0))
    # vertical number strip on the side? (none) - a small maker's plate on the plinth
    parts.append(F.gpoly("maker_plate", [A.rounded_rect(0.12, 0.03, 0.004, 2)], 0.0015, (0.0, 0.055, D - 0.035),
                         (1, 0, 0), (0, 1, 0), mat=BR, bevel=0.0004, drop_bottom=True))
    return F.part("lockers_body", parts)


def build_interior():
    """Locker 9: liner, hat shelf with a lip, a J-hook under the shelf, a small mirror on the back wall."""
    col, row, x0, x1, y0, y1 = locker_cell(LEYLA)
    xa, xb = x0 - GAP + 0.003, x1 + GAP - 0.003           # between the column partitions
    ya, yb = 0.116, 0.948
    parts = []
    parts.append(gbox("l9_back", (xa, ya, 0.008), (xb, yb, 0.012), ST, 0.0))
    for s, (p, q) in ((-1, (xa, xa + 0.003)), (1, (xb - 0.003, xb))):
        parts.append(gbox(f"l9_side{s}", (p, ya, 0.008), (q, yb, FRAME_Z0), ST, 0.0))
    parts.append(gbox("l9_floor", (xa, ya - 0.003, 0.008), (xb, ya, FRAME_Z0), ST, 0.0))
    parts.append(gbox("l9_ceiling", (xa, yb, 0.008), (xb, yb + 0.003, FRAME_Z0), ST, 0.0))
    # hat shelf: 3 mm steel with a 22 mm front lip
    parts.append(gbox("l9_shelf", (xa + 0.003, SHELF_Y, 0.012), (xb - 0.003, SHELF_Y + 0.003, 0.395), ST, 0.0005))
    parts.append(gbox("l9_shelf_lip", (xa + 0.003, SHELF_Y - 0.019, 0.392), (xb - 0.003, SHELF_Y + 0.003, 0.395), ST,
                      0.0008))
    # J-hook from the shelf underside: stem down, J opening toward +Z
    xc = (x0 + x1) / 2
    r = 0.016
    yb_j = SHELF_Y - 0.058                     # centre height of the J bend
    pts = [G(xc, SHELF_Y, HOOK_Z), G(xc, yb_j, HOOK_Z)]
    for k in range(1, 9):
        a = math.pi + math.pi * k / 8          # 180 -> 360 deg in the (z, y) plane, centre (HOOK_Z + r, yb_j)
        pts.append(G(xc, yb_j + r * math.sin(a), HOOK_Z + r + r * math.cos(a)))
    pts.append(G(xc, yb_j + 0.012, HOOK_Z + 2 * r))
    parts.append(A.tube("l9_hook", pts, ROD_R, sides=8, mat=BR))
    parts.append(F.gcyl("l9_hook_tip", ROD_R * 1.5, 0.004, (xc, yb_j + 0.012, HOOK_Z + 2 * r), axis="y", verts=8,
                        mat=BR, bevel=0.001))
    parts.append(F.gcyl("l9_hook_rose", 0.009, 0.003, (xc, SHELF_Y - 0.003, HOOK_Z), axis="y", verts=10, mat=BR,
                        bevel=0.0008))
    # small mirror on the back wall above the shelf, and a folded scarf on the shelf
    parts.append(gbox("l9_mirror_frame", (xc - 0.06, 0.82, 0.012), (xc + 0.06, 0.925, 0.016), CR, 0.001))
    parts.append(gbox("l9_mirror", (xc - 0.055, 0.825, 0.016), (xc + 0.055, 0.92, 0.0168), "M_Glass_Dark", 0.0))
    scarf = M.box("l9_scarf", (0.20, 0.13, 0.035), loc=G(xc - 0.03, SHELF_Y + 0.003 + 0.0175, 0.19), mat="M_Fabric",
                  bevel=0.012, segments=2)
    scarf.data.transform(F.Matrix.Rotation(math.radians(8), 4, "Z"))
    parts.append(scarf)
    catch = (xc, yb_j - r + ROD_R, HOOK_Z + r)     # top of the rod at the bottom of the J
    return F.part("locker9_interior", parts), catch


def build():
    M.reset_scene()
    F.ensure_materials()
    M.material("M_Fabric", color="5B3A3A", rough=0.95)    # preview only: a maroon wool scarf
    build_body()
    interior, catch = build_interior()
    doors = {n: build_door(n) for n in range(1, 13)}
    F.finalize_all(wood_grain=False)
    # receiver hangs by its strap: in pocket_receiver.glb the strap loop's inner top is at (-0.0044, +0.0952, -0.0001)
    # from the centre of mass, so the empty (= the receiver's origin) sits that far below/beside the hook's catch point
    mount = F.mount("receiver_mount", (catch[0] + 0.0044, catch[1] - 0.0952, catch[2] + 0.0001))
    print(f"{F.TAG} hook catch (godot) = {tuple(round(c, 4) for c in catch)}")
    return F.report(NAME), doors, mount


def verify(path):
    req = [f"IA_locker_{n}" for n in range(1, 13)] + ["receiver_mount"]
    expect = {}
    for n in range(1, 13):
        col, row, x0, x1, y0, y1 = locker_cell(n)
        expect[f"IA_locker_{n}"] = (round(x0 - GAP, 5), round((y0 + y1) / 2, 5), DOOR_Z1)
    return F.verify_glb(path, required=req, identity=req, budget=BUDGET, expect=expect,
                        show=["IA_locker_1", "IA_locker_9", "IA_locker_12", "receiver_mount"])


POS, YAW = (0.6, 0.0, 3.5), 180.0


def main():
    args = M.main_guard()
    _, doors, mount = build()
    path = F.export(NAME)
    F.check_names(path)
    errs = verify(path)
    if errs:
        print(f"{F.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    F.qa_begin()
    F.qa_place(POS, YAW)
    F.qa_room()
    F.qa_neighbours([("floor_hatch", (0.9, 0.0, 2.5), 0.0), ("reading_table", (1.9, 0, 1.0), 0.0)])
    F.qa_room_lights(150.0)
    F.qa_light("fill", "AREA", (0.6, 1.9, 1.4), 70.0, "FFE6CC", radius=1.6, target=(0.6, 0.9, 3.4))
    if F.want("hero", args):
        F.shoot(NAME, (-0.35, 1.5, 1.45), (0.75, 0.95, 3.35), vfov=52)
    if F.want("view", args):
        F.shoot(NAME + "_2", (0.6, 1.35, 1.5), (0.6, 0.95, 3.5), vfov=56)
    # locker 9 open with the receiver on the hook
    F.pose_rot(doors[LEYLA], "y", OPEN_DEG)
    F.item_or_proxy("pocket_receiver", mount)
    F.qa_light("l9fill", "AREA", (0.8, 1.0, 2.6), 6.0, "FFE6CC", radius=0.5, target=(0.8, 0.6, 3.3))
    if F.want("l9code", args):          # the view as coded (contract table): centred on locker 10
        F.shoot(NAME + "_3", (0.4, 0.95, 2.45), (0.4, 0.55, 3.35), vfov=46)
    if F.want("l9", args):              # the view centred on locker 9 (world x 0.8) - recommended
        F.shoot(NAME + "_4", (0.8, 0.95, 2.45), (0.8, 0.55, 3.35), vfov=46)
    if F.want("l9close", args):
        F.shoot(NAME + "_5", (0.95, 0.85, 2.85), (0.8, 0.62, 3.3), vfov=40)


main()
