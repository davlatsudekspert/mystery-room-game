"""bookshelf.glb — walnut bookcase that is a hidden hinged door (Laboratory 7, west wall).

Model space (Blender, Z up; front faces -Y = Godot +Z):
  origin = HINGE = back-north-bottom corner. With the front facing room +X, north (room -Z)
  is the model's +X side, so the case occupies x in [-1.10, 0], y in [-0.36, 0] (+0.05 cornice),
  z in [0, 2.10]. Place at Godot (-3.1, 0, -1.15), rotation_degrees.y = +90; open = -85 deg more.
Book levels (top surface z): 0.15 (base), 0.50, 0.85 (encyclopedia), 1.20 (gear-box spot), 1.55.
IA_book_1..9: origin = bottom edge of the spine (bottom-front), tilt out = +rotation about local X.

Run: blender -b --factory-startup -P tools/blender/models/bookshelf.py [-- --no-render]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_props as P  # noqa: E402

ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
rnd = random.Random(1979)

W, D, H = 1.10, 0.36, 2.10
XL, XR = -W, 0.0                 # outer sides
SIDE = 0.025
IN_L, IN_R = XL + SIDE, XR - SIDE  # inner faces of the sides
FRONT = -0.345                   # carcass front plane (pilasters/cornice project beyond)
LEVELS = [0.15, 0.50, 0.85, 1.20, 1.55]
SHELF_T = 0.025
TOP_Z = 1.925                    # underside of the top board
CX = (XL + XR) / 2               # -0.55, centre line
SPINE_Y = -0.333                 # typical spine line (12 mm behind the shelf front)

case_parts = []

# ---------------------------------------------------------------- carcass
for name, x in (("side_l", XL + SIDE / 2), ("side_r", XR - SIDE / 2)):
    case_parts.append(M.box(name, (SIDE, -FRONT, TOP_Z + 0.025), loc=(x, FRONT / 2, (TOP_Z + 0.025) / 2),
                            bevel=0.003, segments=2))
case_parts.append(M.box("top", (W - 2 * SIDE, -FRONT, 0.025), loc=(CX, FRONT / 2, TOP_Z + 0.0125), bevel=0.002, segments=1))
for i, z in enumerate(LEVELS):
    # shelves with a generous rounded front edge (bullnose read)
    case_parts.append(M.box(f"shelf_{i}", (IN_R - IN_L, -FRONT - 0.012, SHELF_T),
                            loc=(CX, (FRONT - 0.012) / 2, z - SHELF_T / 2), bevel=0.0075, segments=2))

# back boards (V-jointed) — visible behind the books and from the secret room
n_boards = 7
bw = (IN_R - IN_L) / n_boards
for i in range(n_boards):
    case_parts.append(M.box(f"back_{i}", (bw - 0.002, 0.012, 1.825),
                            loc=(IN_L + bw * (i + 0.5), -0.006, 0.1125 + 1.825 / 2),
                            mat="M_Wood_Panel", bevel=0.0025, segments=1))

# ---------------------------------------------------------------- reeded pilasters on the side fronts
pil_w, pil_d = 0.05, 0.015
prof = [(0.0, 0.0), (-0.011, 0.0), (-0.015, -0.004)]
for gx in (0.016, 0.025, 0.034):                       # three reeds (V-grooves)
    prof += [(-0.015, -(gx - 0.003)), (-0.0125, -gx), (-0.015, -(gx + 0.003))]
prof += [(-0.015, -0.046), (-0.011, -0.05), (0.0, -0.05)]
for name, x0 in (("pilaster_l", XL), ("pilaster_r", XR - pil_w)):
    z0, z1 = 0.135, 1.92
    p = P.moulding(name, [(y + FRONT, z) for (y, z) in prof], z1 - z0, mat="M_Wood_Walnut")
    # moulding runs along X with profile (y, z); turn the run vertical: X -> Z, profile z -> -x
    p.rotation_euler = (0, -math.pi / 2, 0)
    p.location = (x0, 0, (z0 + z1) / 2)
    case_parts.append(p)
    case_parts.append(M.box(name + "_cap", (pil_w + 0.006, pil_d + 0.006, 0.03), loc=(x0 + pil_w / 2, FRONT - pil_d / 2 - 0.002, 1.935),
                            bevel=0.003, segments=1))

# ---------------------------------------------------------------- frieze + crown cornice (front only: built-in look,
# nothing projects past the side planes so the door clears its opening)
case_parts.append(M.box("frieze", (W, 0.018, 0.075), loc=(CX, FRONT - 0.009, 1.95 + 0.0375), bevel=0.003, segments=2))
crown = [(FRONT, 2.025), (FRONT - 0.019, 2.025), (FRONT - 0.021, 2.029)]
crown += P.ogee(FRONT - 0.021, 2.031, FRONT - 0.044, 2.062, n=6)
crown += [(FRONT - 0.047, 2.064), (FRONT - 0.047, 2.075)]
crown += [(FRONT - 0.047 - 0.008 * math.sin(a), 2.075 + 0.008 * (1 - math.cos(a))) for a in (0.6, 1.2)]
crown += [(FRONT - 0.057, 2.085), (FRONT - 0.057, 2.1), (FRONT, 2.1)]
case_parts.append(P.moulding("crown", crown, W, loc=(CX, 0, 0)))
case_parts.append(M.box("crown_back", (W, -FRONT - 0.018, 0.15), loc=(CX, FRONT / 2, 2.025), bevel=0.002, segments=1))
case_parts.append(M.cylinder("crown_bead", 0.005, W, loc=(CX, FRONT - 0.018, 2.02), rot=(0, math.pi / 2, 0), verts=8,
                             mat="M_Wood_Walnut", bevel=0.0, segments=1))

# ---------------------------------------------------------------- plinth with base moulding
case_parts.append(M.box("plinth", (W, 0.025, 0.115), loc=(CX, FRONT - 0.0155, 0.0575), bevel=0.003, segments=2))
case_parts.append(M.box("plinth_back", (W - 2 * SIDE, -FRONT - 0.03, 0.125), loc=(CX, FRONT / 2, 0.0625), mat="M_Wood_Panel",
                        bevel=0.002, segments=1))
base = [(FRONT - 0.028, 0.112), (FRONT - 0.031, 0.114)]
base += P.ogee(FRONT - 0.031, 0.116, FRONT - 0.016, 0.135, n=5)
base += [(FRONT - 0.016, 0.14), (FRONT, 0.14), (FRONT, 0.112)]
case_parts.append(P.moulding("base_moulding", base, W, loc=(CX, 0, 0)))

# ---------------------------------------------------------------- hidden-door hardware on the BACK (secret-room side)
hw = []
for z in (0.22, 1.05, 1.88):
    hw.append(M.cylinder(f"hinge_knuckle_{z}", 0.011, 0.12, loc=(0.0, 0.0, z), verts=10, mat="M_Steel_Dark", bevel=0.002, segments=1))
    hw.append(M.box(f"hinge_strap_{z}", (0.32, 0.004, 0.045), loc=(-0.16, 0.003, z), mat="M_Steel_Dark", bevel=0.0015, segments=1))
    for k in range(3):
        hw.append(M.cylinder(f"hinge_bolt_{z}_{k}", 0.006, 0.004, loc=(-0.06 - 0.1 * k, 0.006, z), rot=(math.pi / 2, 0, 0),
                             verts=6, mat="M_Steel_Dark", bevel=0.0))
hw.append(M.box("pull_plate", (0.07, 0.004, 0.09), loc=(XL + 0.12, 0.003, 1.05), mat="M_Steel_Dark", bevel=0.0015, segments=1))
hw.append(M.torus("pull_ring", 0.032, 0.0045, loc=(XL + 0.12, 0.012, 1.02), rot=(math.pi / 2, 0, 0), major_seg=12, minor_seg=5,
                  mat="M_Steel_Dark"))
hw.append(M.cylinder("pull_boss", 0.008, 0.012, loc=(XL + 0.12, 0.009, 1.056), rot=(math.pi / 2, 0, 0), verts=8, mat="M_Steel_Dark",
                     bevel=0.0))

case = M.join(case_parts + hw, "bookshelf_case")

# ---------------------------------------------------------------- book helpers
COLS = ["M_Book_Red", "M_Book_Brown", "M_Book_Black", "M_Book_Blue", "M_Book_Green"]
WEIGHTS = [0.24, 0.3, 0.16, 0.22, 0.08]
static_books = []
props = []


def pick_col():
    return rnd.choices(COLS, WEIGHTS)[0]


def deco_for(h, cover):
    style = rnd.random()
    if style < 0.42:      # gold bands at head and tail
        return [("band", h - 0.018, 0.0025, "M_Book_Gold"), ("band", 0.02, 0.0025, "M_Book_Gold")]
    if style < 0.66:      # leather title label framed by gold rules
        lab = "M_Book_Black" if cover != "M_Book_Black" else "M_Book_Red"
        z0 = h * rnd.uniform(0.62, 0.72)
        return [("label", z0, z0 + 0.035, lab), ("band", z0 + 0.039, 0.0015, "M_Book_Gold")]
    if style < 0.78:      # institute library shelf-mark (paper label near the tail)
        return [("label", 0.018, 0.04, "M_Paper"), ("band", h - 0.02, 0.003, "M_Book_Gold")]
    return []


def put_upright(x, z, t, h, d, cover, deco=None, yjit=0.008):
    b = P.book("book", t, h, d, cover=cover, deco=deco if deco is not None else deco_for(h, cover), arc_pts=4)
    b.location = (x + t / 2, SPINE_Y + rnd.uniform(-0.002, yjit), z)
    b.rotation_euler = (0, rnd.uniform(-0.012, 0.012), rnd.uniform(-0.02, 0.02))
    static_books.append(b)
    return b


def run_fill(x0, x1, z, hmax, series_p, gap):
    x = x0
    last_h = 0.0
    while True:
        if rnd.random() < series_p:     # a matching set of 3-5 volumes
            k = rnd.randint(3, 5)
            t, h, d = rnd.uniform(0.026, 0.042), rnd.uniform(0.2, min(hmax, 0.27)), rnd.uniform(0.15, 0.21)
            cover = pick_col()
            deco = [("band", h - 0.016, 0.003, "M_Book_Gold"),
                    ("label", h * 0.6, h * 0.6 + 0.03, "M_Book_Black" if cover != "M_Book_Black" else "M_Book_Brown"),
                    ("band", 0.018, 0.003, "M_Book_Gold")]
            k = min(k, int((x1 - x) / (t + 0.0012)))
            if k <= 0:
                break
            for _ in range(k):
                put_upright(x, z, t, h, d, cover, deco=deco, yjit=0.003)
                x += t + rnd.uniform(0.0003, 0.0012)
            last_h = h
        else:
            t = rnd.choice([rnd.uniform(0.018, 0.03), rnd.uniform(0.03, 0.05), rnd.uniform(0.045, 0.065)])
            h = rnd.uniform(0.18, hmax)
            d = min(0.29, h * rnd.uniform(0.65, 0.78))
            if x + t > x1:
                break
            put_upright(x, z, t, h, d, pick_col())
            x += t + rnd.uniform(*gap)
            last_h = h
    return x, last_h


def run(x0, x1, z, hmax, series_p=0.35, gap=(0.0005, 0.003), align_right=False):
    """Fill [x0, x1] left to right with upright books; returns (end_x, height of last book).
    align_right pushes the whole run against x1 (books held by a bookend)."""
    first = len(static_books)
    x, lh = run_fill(x0, x1, z, hmax, series_p, gap)
    if align_right:
        dx = x1 - x
        for b in static_books[first:]:
            b.location.x += dx
        return x1, lh
    return x, lh


def lean(xr, z, h_neighbour, t, h, d, theta_deg, cover=None):
    """Book leaning left against a book whose right face is at xr. Returns the free x."""
    th = math.radians(theta_deg)
    contact = h_neighbour * math.tan(th) if h * math.cos(th) > h_neighbour else h * math.sin(th)
    cover = cover or pick_col()
    b = P.book("book_lean", t, h, d, cover=cover, deco=deco_for(h, cover), arc_pts=4)
    xa = xr + contact                       # bottom-left corner on the shelf
    b.location = (xa + (t / 2) * math.cos(th), SPINE_Y + 0.004, z + (t / 2) * math.sin(th))
    b.rotation_euler = (0, -th, rnd.uniform(-0.02, 0.02))
    static_books.append(b)
    return xa + t * math.cos(th)


def stack(x0, z, sizes, spin=0.05):
    """Books lying flat, spines to the front. sizes = [(t, h, d), ...] bottom first (h runs along X)."""
    zc = z
    for (t, h, d) in sizes:
        cover = pick_col()
        b = P.book("book_flat", t, h, d, cover=cover, deco=deco_for(h, cover), arc_pts=4)
        b.rotation_euler = (0, math.pi / 2, rnd.uniform(-spin, spin))
        b.location = (x0 + rnd.uniform(-0.006, 0.006), SPINE_Y + rnd.uniform(0.0, 0.01), zc + t / 2)
        static_books.append(b)
        zc += t + 0.0004
    return zc


def bookend(x, z, facing, name):
    """Brass L-bookend; `facing` = +1 when the books are on its +X side."""
    outline = [(0.0, 0.0), (0.105, 0.0), (0.105, 0.085)] + P.arc(0.06, 0.085, 0.045, 0.0, math.pi * 0.5, n=4)[1:] \
        + [(0.0, 0.13)]
    up = M.extrude_profile(name + "_up", outline, 0.005, mat="M_Brass_Aged", bevel=0.0012, segments=1)
    up.rotation_euler = (math.pi / 2, 0, math.pi / 2)      # outline x -> +Y (depth), y -> Z, extrusion -> X
    up.location = (x - (0.005 if facing > 0 else 0.0), SPINE_Y + 0.002, z)
    foot = M.box(name + "_foot", (0.07, 0.1, 0.0025), loc=(x + facing * 0.037, SPINE_Y + 0.054, z + 0.00125), mat="M_Brass_Aged",
                 bevel=0.001, segments=1)
    props.extend([up, foot])


def jar(x, y, z, name, h=0.15, r=0.05):
    outer = [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.006), (r, h * 0.72), (r * 0.92, h * 0.8), (r * 0.62, h * 0.86), (r * 0.6, h * 0.95)]
    g = M.lathe(name, P.shell_profile(outer, 0.0025), loc=(x, y, z), segments=14, mat="M_Glass")
    lid = M.lathe(name + "_lid", [(0.0, h * 0.93), (r * 0.56, h * 0.93), (r * 0.66, h * 0.965), (r * 0.6, h * 0.99),
                                  (0.012, h * 1.0), (0.011, h * 1.05), (0.016, h * 1.08), (0.0, h * 1.1)],
                  loc=(x, y, z), segments=14, mat="M_Glass")
    stones = []
    for k in range(4):
        a = k * 2.4
        s = M.sphere(name + f"_stone{k}", rnd.uniform(0.013, 0.019), loc=(x + 0.02 * math.cos(a), y + 0.02 * math.sin(a),
                                                                      z + 0.016 + 0.008 * (k > 2)), segments=6, rings=4, mat="M_Stone",
                     scale=(1.0, rnd.uniform(0.7, 1.0), rnd.uniform(0.55, 0.8)))
        stones.append(s)
    label = M.lathe(name + "_label", [(r + 0.0004, h * 0.3), (r + 0.0004, h * 0.55)], loc=(x, y, z), segments=14, mat="M_Paper")
    bm = bmesh.new()
    bm.from_mesh(label.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y > -r * 0.2], context="FACES")
    bm.to_mesh(label.data)
    bm.free()
    props.extend([g, lid, label] + stones)


def roll(name, p0, p1, r=0.022, ties=True):
    """Rolled drawing (paper tube with recessed hollow ends) between p0 and p1, tied with red string."""
    a, b = Vector(p0), Vector(p1)
    ln = (b - a).length
    o = M.lathe(name, [(r - 0.004, 0.015), (r - 0.004, 0.0), (r, 0.0), (r, ln), (r - 0.004, ln), (r - 0.004, ln - 0.015)],
                segments=10, mat="M_Paper")
    o.location = a
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    props.append(o)
    if ties:
        for f in (0.28, 0.72):
            z0 = ln * f
            t = M.lathe(name + f"_tie{f}", [(r + 0.0006, z0 - 0.002), (r + 0.0014, z0), (r + 0.0006, z0 + 0.002)], segments=8,
                        mat="M_String_Red")
            t.location = a
            t.rotation_euler = o.rotation_euler
            props.append(t)


def specimen_box(x, y, z, name):
    """Walnut mineral box with a glazed lid frame, cotton bed and three specimens."""
    w, d, h = 0.22, 0.15, 0.05
    props.append(M.box(name, (w, d, h), loc=(x, y, z + h / 2), bevel=0.003, segments=1))
    props.append(M.box(name + "_bed", (w - 0.02, d - 0.02, 0.004), loc=(x, y, z + h + 0.0015), mat="M_Paper", bevel=0.0015, segments=1))
    for k, (mx, mt) in enumerate(((-0.065, "M_Copper"), (0.0, "M_Stone"), (0.065, "M_Brass_Polished"))):
        props.append(M.sphere(name + f"_min{k}", 0.017, loc=(x + mx, y - 0.01, z + h + 0.012), segments=6, rings=4, mat=mt,
                              scale=(1.2, 0.9, 0.6)))
    for side, yy in (("f", y - d / 2 + 0.005), ("b", y + d / 2 - 0.005)):
        props.append(M.box(name + f"_rim_{side}", (w, 0.01, 0.032), loc=(x, yy, z + h + 0.016), bevel=0.002, segments=1))
    for side, xx in (("l", x - w / 2 + 0.005), ("r", x + w / 2 - 0.005)):
        props.append(M.box(name + f"_rim_{side}", (0.01, d - 0.02, 0.032), loc=(xx, y, z + h + 0.016), bevel=0.002, segments=1))
    props.append(M.box(name + "_glass", (w - 0.016, d - 0.016, 0.0025), loc=(x, y, z + h + 0.03), mat="M_Glass", bevel=0.0, segments=1))
    props.append(M.box(name + "_plate", (0.05, 0.002, 0.016), loc=(x, y - d / 2 - 0.001, z + h * 0.5), mat="M_Brass_Polished",
                       bevel=0.0006, segments=1))


# ---------------------------------------------------------------- level 0 (z = 0.15): folios, atlases, rolls
z = LEVELS[0]
x, lh = run(IN_L + 0.002, IN_L + 0.34, z, 0.315, series_p=0.0, gap=(0.001, 0.003))
x = lean(x, z, lh, 0.04, 0.31, 0.24, 14)
top = stack(x + 0.03, z, [(0.045, 0.40, 0.29), (0.035, 0.37, 0.27), (0.03, 0.34, 0.25)])
roll("roll_a", (x + 0.05, SPINE_Y + 0.06, top + 0.022), (x + 0.47, SPINE_Y + 0.07, top + 0.022))
roll("roll_b", (x + 0.06, SPINE_Y + 0.11, top + 0.02), (x + 0.44, SPINE_Y + 0.1, top + 0.02), r=0.02)
run(x + 0.48, IN_R - 0.002, z, 0.30, series_p=0.5)

# ---------------------------------------------------------------- level 1 (z = 0.50): mixed run + jar
z = LEVELS[1]
x, lh = run(IN_L + 0.002, IN_L + 0.40, z, 0.29, series_p=0.5)
x = lean(x, z, lh, 0.03, 0.25, 0.18, 18)
jar(x + 0.07, SPINE_Y + 0.09, z, "jar_minerals")
stack(x + 0.14, z, [(0.04, 0.27, 0.2), (0.028, 0.24, 0.18)])
run(x + 0.14 + 0.29, IN_R - 0.002, z, 0.30, series_p=0.4)

# ---------------------------------------------------------------- level 2 (z = 0.85): the encyclopedia
z = LEVELS[2]
ENC_T, ENC_H, ENC_D, ENC_RB = 0.046, 0.26, 0.185, 0.0032
enc_gap = 0.0015
enc_w = 9 * ENC_T + 8 * enc_gap
enc_x0 = CX - enc_w / 2
x, lh = run(IN_L + 0.002, enc_x0 - 0.075, z, 0.29, series_p=0.0)
lean(x, z, lh, 0.028, 0.22, 0.17, 12)
bookend(enc_x0 - 0.002, z, +1, "bookend_a")
bookend(enc_x0 + enc_w + 0.002, z, -1, "bookend_b")
stack(enc_x0 + enc_w + 0.03, z, [(0.05, 0.29, 0.22), (0.032, 0.26, 0.2), (0.03, 0.22, 0.17), (0.024, 0.2, 0.15)])
run(enc_x0 + enc_w + 0.34, IN_R - 0.002, z, 0.29, series_p=0.0)

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
enc_objs = []
for k in range(9):
    deco = [
        ("band", ENC_H - 0.009, 0.0016, "M_Book_Gold"),
        ("raised", ENC_H - 0.032, 0.0055, "M_Book_Gold"),
        ("label", ENC_H - 0.074, ENC_H - 0.04, "M_Book_Black"),
        ("raised", ENC_H - 0.083, 0.0055, "M_Book_Gold"),
        ("raised", ENC_H - 0.137, 0.0055, "M_Book_Gold"),
        ("raised", 0.07, 0.0055, "M_Book_Gold"),
        ("band", 0.009, 0.0016, "M_Book_Gold"),
    ]
    body = P.book(f"IA_book_{k + 1}", ENC_T, ENC_H, ENC_D, cover="M_Book_Green", deco=deco, rb=ENC_RB, arc_pts=6)
    # gold Roman numeral between the 2nd and 3rd raised bands, conformed to the rounded spine
    num = P.text(f"num_{k}", ROMAN[k], 0.031, loc=(0, 0, ENC_H - 0.110), rot=(math.pi / 2, 0, 0), mat="M_Book_Gold",
                 font=P.FONT_SERIF_BOLD, resolution=2, max_width=ENC_T * 0.74)
    P.conform_to_spine(num, ENC_T, ENC_RB, lift=0.0004)
    # gold rule frame on the black title label + lozenge ornament in the lower panel
    orn = P.mesh_obj(f"orn_{k}", [(0, 0, 0.111), (0.0045, 0, 0.104), (0, 0, 0.097), (-0.0045, 0, 0.104)], [(0, 3, 2, 1)],
                     ["M_Book_Gold"])
    P.conform_to_spine(orn, ENC_T, ENC_RB, lift=0.0004)
    vol = M.join([body, num, orn], f"IA_book_{k + 1}")
    # mesh is in book-local space: origin = bottom edge of the spine (pivot for tilting out)
    vol.location = (enc_x0 + ENC_T / 2 + k * (ENC_T + enc_gap), SPINE_Y + 0.001, z)
    enc_objs.append(vol)

# ---------------------------------------------------------------- level 3 (z = 1.20): gear-box spot kept clear
z = LEVELS[3]
SPOT0, SPOT1 = CX - 0.16, CX + 0.16
run(IN_L + 0.002, SPOT0 - 0.007, z, 0.29, series_p=0.6, align_right=True)
bookend(SPOT0 - 0.002, z, -1, "bookend_c")
bookend(SPOT1 + 0.002, z, +1, "bookend_d")
x, lh = run(SPOT1 + 0.003, IN_R - 0.09, z, 0.28, series_p=0.0)
lean(x, z, lh, 0.03, 0.27, 0.2, 16)

# ---------------------------------------------------------------- level 4 (z = 1.55): smaller books, specimen box, rolls
z = LEVELS[4]
x, lh = run(IN_L + 0.002, IN_L + 0.30, z, 0.27, series_p=0.5)
x = lean(x, z, lh, 0.022, 0.22, 0.16, 20)
top = stack(x + 0.02, z, [(0.035, 0.30, 0.23), (0.03, 0.26, 0.2)])
specimen_box(x + 0.02 + 0.15, SPINE_Y + 0.1, top, "specimen_box")
run(x + 0.34, IN_R - 0.14, z, 0.29, series_p=0.0)
roll("roll_c", (IN_R - 0.06, SPINE_Y + 0.12, z + 0.0), (IN_R - 0.035, SPINE_Y + 0.15, z + 0.33), r=0.024)
roll("roll_d", (IN_R - 0.11, SPINE_Y + 0.15, z + 0.0), (IN_R - 0.04, SPINE_Y + 0.2, z + 0.34), r=0.02)

# ---------------------------------------------------------------- join + finalize
M.join(static_books, "bookshelf_books")
M.join(props, "bookshelf_props")
M.finalize(smooth_angle=40)
P.report("bookshelf")
M.export_glb("bookshelf")

P.shots("bookshelf", [
    ("", (CX + 1.25, -3.05, 1.55), (CX, -0.15, 1.02), 32),
    ("_2", (CX + 0.16, -1.02, 1.06), (CX, -0.3, 0.97), 50),
    ("_3", (CX - 1.6, 2.4, 1.3), (CX, 0.0, 1.0), 32),
], ARGS)
