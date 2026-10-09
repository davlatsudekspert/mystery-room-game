"""slide_cabinet.glb — walnut lantern-slide cabinet in the projection booth (Chapter 2; group B2).

0.46 w x 1.05 h x 0.45 d (contract 0.60 w, see DEVIATION), wall-mounted: origin on the floor on the wall plane,
front +Z (placed at world (-5.0, 0, 2.8) with yaw 90, so the front faces east into the booth).

Five shallow drawers between y 0.40 and 0.95 (drawer 0 at the top, pitch 0.11), each with a pressed brass
frame holding a cream enamel plaque with a raised black symbol (0 ring, 1 triangle, 2 four-pointed star,
3 square, 4 Greek cross) and two brass cup pulls. Inside each drawer: a felt-lined tray with walnut
dividers, 3 rows x 4 compartments of lantern slides in card mounts lying flat (static, part of the drawer).
Below the drawers a two-door cupboard, a moulded plinth and a cove cornice.

DEVIATION (layout): 0.46 wide instead of 0.60, and the body is centred at local x = +0.135 (world z 2.665)
instead of on the origin. With the contract placement (-5.0, 0, 2.8) yaw 90, a centred 0.60 cabinet spans
world z 2.50..3.10 and its open drawers (out to world x -4.27) would run into the film-splicer bench
(x >= -4.50, z >= 2.896: top, apron, front leg); moving it north alone hits room A's fire bucket on the booth
north wall (x -4.74..-4.46, y 0.80..1.24, z 2.12..2.39). Now the carcass spans world z 2.409..2.921 (top
overhang included; the bench is lower and further east, so only the drawers matter) and the open drawers
z 2.456..2.874: 2.2 cm clear of the bench, 1.6 cm clear of the bucket. The origin stays at the contract
placement point on the wall plane (y = 0). Four slide columns per drawer instead of five.

Parts:
  IA_slide_drawer_<i>  i = 0..4, pivot at the drawer-front face centre (z = 0.45), identity at rest; the
                       code slides it along local +Z by 0.28. The whole drawer is one mesh (front, plaque,
                       pulls, tray, slides) so the echo highlight can light it.
  slide_mark_mount     child of IA_slide_drawer_2: front row, compartment left of centre, identity rotation;
                       glass_slide.glb lies flat there face up (image top toward -Z = the drawer back).
  carcass              static (sides, top, plinth, rails, dust boards, cupboard doors).

    blender -b --factory-startup -P tools/blender/models/slide_cabinet.py [-- --no-render] [--shots a,b]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_ch2_furniture2 as F  # noqa: E402
from lib_ch2_furniture2 import G  # noqa: E402

NAME = "slide_cabinet"
ARGS = M.main_guard()
BUDGET = 5000

W2 = 0.23                     # half width (0.46 wide; contract 0.60, see DEVIATION)
DEPTH = 0.45
FRONT = DEPTH                 # drawer-front / carcass front plane
SIDE_IN = 0.212               # inner face of the sides
DF = SIDE_IN - 0.003          # drawer-front half width
TS = SIDE_IN - 0.010          # tray side centre |x|
TI = TS - 0.005               # tray inner face |x|
PITCH = 0.11
TOP_RAIL = 0.95               # rail above drawer 0
FELT = 0.062                  # felt top above the drawer bottom edge (raised tray: the front row stays visible)
ROW_Z = [0.376, 0.281, 0.186]
COL_X = [-0.1425, -0.0475, 0.0475, 0.1425]
MARK_COL = 1                  # drawer 2, front row: the compartment left of centre holds the mark slide
TRAVEL = 0.28
SLIDE_BOTTOM = 0.0014         # glass_slide.glb: lowest point below its origin (measured in the QA import)
OFFSET_X = 0.135              # cabinet centre on local +X (world north): clears the bench and the fire bucket

parts = {}


def drawer_y(i):
    yb = TOP_RAIL - PITCH * (i + 1) + 0.005
    return yb, yb + 0.10


# ------------------------------------------------------------------ symbols (2D loops, plaque-local, metres)
def sym_loops(i):
    if i == 0:      # ring
        return [K.circle(0.0165, 22), K.circle(0.0118, 22)]
    if i == 1:      # triangle outline
        def tri(r, dy=-0.003):
            return [(r * math.cos(math.radians(a)), dy + r * math.sin(math.radians(a))) for a in (90, 210, 330)]
        return [tri(0.0215), tri(0.0215 - 0.0094)]
    if i == 2:      # four-pointed star (concave sides)
        pts = []
        tips = [(0.0, 0.020), (0.020, 0.0), (0.0, -0.020), (-0.020, 0.0)]
        for k in range(4):
            a, b = Vector(tips[k]), Vector(tips[(k + 1) % 4])
            c = (a + b) * 0.16
            for j in range(6):
                t = j / 6
                p = a * (1 - t) ** 2 + c * 2 * t * (1 - t) + b * t * t
                pts.append((p.x, p.y))
        return [list(reversed(pts))]
    if i == 3:      # square outline
        def sq(h):
            return [(-h, -h), (h, -h), (h, h), (-h, h)]
        return [sq(0.0150), sq(0.0103)]
    # Greek cross
    a, b = 0.0050, 0.0180
    return [[(-a, -b), (a, -b), (a, -a), (b, -a), (b, a), (a, a), (a, b), (-a, b), (-a, a), (-b, a), (-b, -a), (-a, -a)]]


def plaque(i, cy):
    p = []
    p.append(F.gslab(f"plq_frame_{i}", (0.0, cy, FRONT), 0.076, 0.058, 0.0026, r=0.007, mat="M_Brass_Aged", plane="xy",
                     hole=(0.064, 0.046, 0.005), bevel=0.0, n=3))
    p.append(F.gslab(f"plq_enamel_{i}", (0.0, cy, FRONT), 0.066, 0.048, 0.0018, r=0.006, mat="M_Enamel_Cream",
                     plane="xy", bevel=0.0, n=3))
    p.append(F.gpoly(f"plq_symbol_{i}", sym_loops(i), 0.0008, (0.0, cy, FRONT + 0.0018), (1, 0, 0), (0, 1, 0),
                     mat="M_Lacquer_Black", bevel=0.0))
    for sx in (-1, 1):
        p.append(F.screw(f"plq_pin_{i}_{sx}", 0.0017, (sx * 0.0345, cy, FRONT + 0.0026), "z", mat="M_Brass_Aged",
                         segs=5))
    return p


def cup_pull(name, cx, cy):
    out = [F.gslab(name + "_plate", (cx, cy, FRONT), 0.066, 0.030, 0.0015, r=0.006, mat="M_Brass_Aged", plane="xy",
                   bevel=0.0, n=3)]
    outer, inner = [], []
    for j in range(8):
        th = math.radians(90 - 125 * j / 7)
        outer.append((0.0135 * math.cos(th), 0.0135 * math.sin(th)))
        inner.append((0.0118 * math.cos(th), 0.0118 * math.sin(th)))
    loop = [(0.0, 0.0135)] + outer[1:] + list(reversed(inner[1:])) + [(0.0, 0.0118)]
    out.append(F.gpoly(name + "_hood", [loop], 0.056, (cx + 0.028, cy + 0.002, FRONT + 0.0015), (0, 0, 1), (0, 1, 0),
                       mat="M_Brass_Aged", bevel=0.0))
    return out


# ------------------------------------------------------------------ drawers
def build_drawer(i):
    yb, yt = drawer_y(i)
    yc = (yb + yt) / 2
    d = []
    d.append(F.gbox(f"dr_front_{i}", (-DF, yb, FRONT - 0.018), (DF, yt, FRONT), mat="M_Wood_Walnut", bevel=0.004))
    # tray: sides, back, bottom, felt, dividers
    fy = yb + FELT
    for sx in (-1, 1):
        d.append(F.gbox(f"dr_side_{i}_{sx}", (sx * TS - 0.005, yb + 0.006, 0.035), (sx * TS + 0.005, yb + 0.090,
                                                                                       FRONT - 0.018),
                        mat="M_Wood_Panel", bevel=0.0))
    d.append(F.gbox(f"dr_back_{i}", (-TI, yb + 0.006, 0.035), (TI, yb + 0.085, 0.045), mat="M_Wood_Panel",
                    bevel=0.0))
    d.append(F.gbox(f"dr_bottom_{i}", (-TI, yb + 0.006, 0.045), (TI, fy - 0.002, FRONT - 0.018),
                    mat="M_Wood_Panel", bevel=0.0))
    d.append(F.gbox(f"dr_felt_{i}", (-TI, fy - 0.002, 0.045), (TI, fy, FRONT - 0.018), mat="M_Felt", bevel=0.0))
    for x in (-0.095, 0.0, 0.095):
        d.append(F.gbox(f"dr_div_{i}_{x:+.2f}", (x - 0.002, fy, 0.138), (x + 0.002, fy + 0.017, FRONT - 0.018),
                        mat="M_Wood_Walnut", bevel=0.0))
    for z in (0.3285, 0.2335, 0.1385):
        d.append(F.gbox(f"dr_cross_{i}_{z:.3f}", (-TI, fy, z - 0.002), (TI, fy + 0.0155, z + 0.002),
                        mat="M_Wood_Walnut", bevel=0.0))
    # slides (card mount + dark glass window, lying flat); a few gaps, a little jitter
    rnd = __import__("random").Random(31 + i)
    for r, z in enumerate(ROW_Z):
        for c, x in enumerate(COL_X):
            if i == 2 and r == 0 and c == MARK_COL:
                continue                       # the mark slide is spawned here by the code
            if rnd.random() < 0.10:
                continue
            ang = rnd.uniform(-4.0, 4.0)
            jx, jz = rnd.uniform(-0.004, 0.004), rnd.uniform(-0.003, 0.003)
            card = F.gquad(f"sl_card_{i}_{r}_{c}", (0, fy + 0.0040, 0), (1, 0, 0), (0, 0, -1), 0.082, 0.082,
                           "M_Paper" if rnd.random() < 0.7 else "M_Cardboard", uv=False)
            win = F.gquad(f"sl_win_{i}_{r}_{c}", (0, fy + 0.0042, 0), (1, 0, 0), (0, 0, -1), 0.056,
                          0.050, "M_Glass_Dark" if rnd.random() < 0.8 else "M_Glass_Amber", uv=False)
            for o in (card, win):
                F.bake_xform(o, yaw=ang)
                o.location = G(x + jx, 0.0, z + jz)
                M.apply_transform(o)
            d += [card, win]
    d += plaque(i, yc)
    for sx in (-1, 1):
        d += cup_pull(f"pull_{i}_{sx}", sx * 0.140, yc)
    o = F.part(f"IA_slide_drawer_{i}", d, pivot=(0.0, yc, FRONT))
    if i == 2:
        parts["mark_mount"] = F.mount("slide_mark_mount", (COL_X[MARK_COL], fy + SLIDE_BOTTOM, ROW_Z[0]), par=o)
    return o


# ------------------------------------------------------------------ carcass
def build_carcass():
    c = []
    # plinth (recessed kick) and a base moulding
    c.append(F.gbox("plinth", (-W2 + 0.012, 0.0, 0.012), (W2 - 0.012, 0.072, DEPTH - 0.012), mat="M_Wood_Walnut",
                    bevel=0.003))
    base_prof = [(0.0, 0.070), (0.0, 0.104), (-0.006, 0.104), (-0.010, 0.098), (-0.010, 0.086), (-0.014, 0.078),
                 (-0.014, 0.070)]
    path = [G(-W2, 0, 0.0), G(-W2, 0, DEPTH), G(W2, 0, DEPTH), G(W2, 0, 0.0)]
    c.append(A.sweep("base_mould", base_prof, path, up=(0, 0, 1), mat="M_Wood_Walnut"))
    # sides, back, bottom deck
    for sx in (-1, 1):
        x0, x1 = (-W2, -SIDE_IN) if sx < 0 else (SIDE_IN, W2)
        c.append(F.gbox(f"side_{sx}", (x0, 0.10, 0.0), (x1, 0.995, DEPTH), mat="M_Wood_Walnut", bevel=0.003))
    c.append(F.gbox("back", (-SIDE_IN, 0.10, 0.0), (SIDE_IN, 0.995, 0.012), mat="M_Wood_Panel", bevel=0.0))
    c.append(F.gbox("deck", (-SIDE_IN, 0.10, 0.012), (SIDE_IN, 0.105, DEPTH), mat="M_Wood_Panel", bevel=0.0))
    # top with a cove cornice
    c.append(F.gbox("top", (-W2 - 0.026, 1.022, -0.002), (W2 + 0.026, 1.05, DEPTH + 0.026), mat="M_Wood_Walnut",
                    bevel=0.004))
    cove = [(0.002, 0.995), (0.002, 1.023), (-0.024, 1.023)]
    cove += [(0.024 * math.cos(math.radians(a)), 1.023 + 0.024 * math.sin(math.radians(a))) for a in (195, 215, 235, 255)]
    cove += [(0.0, 0.999)]
    c.append(A.sweep("cornice", cove, path, up=(0, 0, 1), mat="M_Wood_Walnut"))
    # frieze rail with a blank brass card holder
    c.append(F.gbox("frieze", (-SIDE_IN, TOP_RAIL + 0.005, FRONT - 0.020), (SIDE_IN, 0.995, FRONT), mat="M_Wood_Walnut",
                    bevel=0.002))
    c += F.card_holder("frieze_label", (0.0, 0.973, FRONT), w=0.090, h=0.026)
    # front rails between drawers + dust boards behind them
    for k in range(6):
        y = TOP_RAIL - PITCH * k
        c.append(F.gbox(f"rail_{k}", (-SIDE_IN, y - 0.005, FRONT - 0.020), (SIDE_IN, y + 0.005, FRONT), mat="M_Wood_Walnut",
                        bevel=0.0012))
        c.append(F.gbox(f"dust_{k}", (-SIDE_IN, y - 0.004, 0.012), (SIDE_IN, y + 0.002, FRONT - 0.020), mat="M_Wood_Panel",
                        bevel=0.0))
    # cupboard: two flush doors with raised fields, turned knobs, an escutcheon
    for j, sx in enumerate((-1, 1)):
        x0, x1 = (0.0015, DF) if sx > 0 else (-DF, -0.0015)
        c.append(F.gbox(f"door_{j}", (x0, 0.108, FRONT - 0.018), (x1, 0.39, FRONT), mat="M_Wood_Walnut", bevel=0.003))
        c.append(F.gbox(f"door_field_{j}", (x0 + 0.032, 0.140, FRONT - 0.002), (x1 - 0.032, 0.358, FRONT + 0.004),
                        mat="M_Wood_Walnut", bevel=0.006))
        kx = sx * 0.022
        c.append(F.glathe(f"door_knob_{j}", [(0.0, 0.0), (0.009, 0.0), (0.0045, 0.006), (0.0050, 0.011), (0.0105, 0.017),
                                             (0.0095, 0.023), (0.0, 0.0245)], (kx, 0.29, FRONT), axis="z", segments=8,
                          mat="M_Brass_Aged"))
    c.append(F.gslab("escutcheon", (0.022, 0.255, FRONT), 0.014, 0.026, 0.0012, r=0.006, mat="M_Brass_Aged", plane="xy",
                     bevel=0.0, n=3))
    c.append(F.gslab("keyhole", (0.022, 0.2565, FRONT + 0.0012), 0.0042, 0.011, 0.0004, r=0.0019, mat="M_Bakelite",
                     plane="xy", bevel=0.0, n=2))
    parts["carcass"] = F.part("carcass", c)


def build():
    M.reset_scene()
    F.ensure_materials()
    build_carcass()
    parts["drawers"] = [build_drawer(i) for i in range(5)]
    # shift the whole cabinet north (local +X): the static carcass in its mesh, the drawers by their pivots
    parts["carcass"].data.transform(__import__("mathutils").Matrix.Translation(G(OFFSET_X, 0, 0)))
    for d in parts["drawers"]:
        d.location = d.location + G(OFFSET_X, 0, 0)
    M.refresh()
    F.finalize_all()
    return F.report(NAME)


REQUIRED = ["carcass", "slide_mark_mount"] + [f"IA_slide_drawer_{i}" for i in range(5)]


def main():
    total = build()
    path = F.export(NAME)
    errs = F.verify_glb(path, required=REQUIRED, identity=REQUIRED[1:] + ["carcass"], budget=BUDGET, show=REQUIRED)
    print(f"[slide_cabinet] tris={total} errors={len(errs)}")
    if "--no-render" in ARGS:
        return
    qa()


def qa():
    F.qa_begin()
    F.qa_decal_alpha()
    F.qa_room("booth")
    F.qa_place((-5.0, 0.0, 2.8), 90.0)
    F.qa_neighbours([("film_splicer", (-3.9, 0.0, 3.5), 180.0), ("lens_case", (-3.75, 1.45, 3.37), 180.0)])
    F.qa_light("booth_bulb", "POINT", (-3.0, 2.65, 2.85), 70.0, "FFCF94", radius=0.04)
    F.qa_light("focus_fill", "POINT", (-3.7, 1.45, 2.8), 7.0, "FFE6C8", radius=0.25)
    M.refresh()
    if F.want("view", ARGS):
        F.shoot(NAME + "_2", (-3.85, 1.3, 2.8), (-4.8, 0.7, 2.8), vfov=48, world=0.10)
    if F.want("hero", ARGS):
        F.shoot(NAME, (-3.65, 1.42, 2.25), (-4.85, 0.62, 2.70), vfov=50, world=0.12)
    # drawer 2 open with the emblem slide
    dr = parts["drawers"][2]
    dr.location = dr.location + (dr.matrix_basis.to_3x3() @ G(0, 0, TRAVEL))
    M.refresh()
    h = F.item_or_proxy("glass_slide", parts["mark_mount"])
    F.qa_item_decals()
    M.refresh()
    if h is not None:
        lo = min((o.matrix_world @ Vector(c)).z for o in bpy.context.scene.objects if o.type == "MESH"
                 and o.name.startswith("qa_") and "slide" in o.name for c in o.bound_box)
        print(f"[slide_cabinet] glass_slide lowest z (world) = {lo:.4f}, felt top = {drawer_y(2)[0] + FELT:.4f}")
    if F.want("open", ARGS):
        F.shoot(NAME + "_3", (-3.85, 1.3, 2.8), (-4.8, 0.7, 2.8), vfov=48, world=0.10)
    if F.want("suggest", ARGS):     # suggested slides camera, centred on the (offset) cabinet
        F.shoot(NAME + "_4", (-3.80, 1.32, 2.70), (-4.62, 0.64, 2.68), vfov=48, world=0.10)
    if F.want("close", ARGS):
        F.shoot(NAME + "_5", (-4.00, 1.10, 2.80), (-4.33, 0.66, 2.70), vfov=40, world=0.10)


main()
