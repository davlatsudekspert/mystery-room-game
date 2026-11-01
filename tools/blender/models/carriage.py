"""carriage_1..5.glb — the five rolling compactus carriages of the Cold Store (N4 "Carriage aisle").

One script exports five carriages (same nodes, different contents and a different end tag 1..5 = pips 1..5 and colour band).
A carriage is a double-sided galvanised shelving unit on a steel plinth with four flanged wheels, running on two floor rails
that lie ACROSS its length: it slides along Godot X, one slot pitch (1.00 m) per crank. Cranks sit on the end panel (+Z).

Model space (Godot): origin on the floor at the footprint centre; front end panel +Z; size 0.92 (x) x 3.20 (z) x 2.45 (y).
Shelf faces are the +X and -X sides (5 levels at y 0.32 0.76 1.20 1.64 2.08, 4 bays of 0.8 m each side).
Rails (room): two rails along X at z = -1.20 and z = +1.20 relative to the carriage origin, rail top y = 0.025.
Parts (identity rotation at rest, origin = pivot):
  carriage_body   all static geometry (frame, shelves, boxes, cans, wheels, end panel, tag holder, crank gearbox)
  IA_crank        hand wheel with a spinner handle; pivot at the wheel centre (0, 1.15, 1.69); turn about +Z. One slide step
                  per quarter turn (the scene animates the slide and the spin together)
  end_tag         quad 0.20 x 0.12 with the slot `M_Decal_CarriageTags`, UV already on cell k of the 5-cell atlas
                  (decals/ch2x/carriage_tags.png), centre (0, 1.95, 1.606)
  light_carriage  empty (0.0, 2.2, 0.0): optional point of a cold shelf light (unused by default)
Contents are seeded by the carriage number, so the five look different; none of it is interactive.
    blender -b --factory-startup -P tools/blender/models/carriage.py [-- --no-render]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

ARGS = M.main_guard()
BUDGET = 4800
T2, L2, H = 0.46, 1.60, 2.40          # half thickness, half length, shelf height
LEVELS = (0.32, 0.76, 1.20, 1.64, 2.08)
GALV, DARK, PAINT = "M_Steel_Galv", "M_Steel_Dark", "M_Enamel_Ice"
CRANK_Y, CRANK_Z = 1.15, 1.69
TAG_Y = 1.95


def structure():
    o = []
    # plinth + wheels
    o.append(gbox("plinth", (-T2, 0.12, -L2), (T2, 0.26, L2), PAINT, bevel=0.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            o.append(gcyl("wheel", 0.060, 0.034, (sx * 0.30, 0.085, sz * 1.20 - 0.017), axis="z", verts=14, mat=DARK, bevel=0.0))
            o.append(gbox("axle_bk", (sx * 0.30 - 0.03, 0.06, sz * 1.20 - 0.030), (sx * 0.30 + 0.03, 0.12, sz * 1.20 + 0.030), DARK, bevel=0.0))
    # spine (double-sided back) with a top rail
    o.append(gbox("spine", (-0.012, 0.26, -L2 + 0.04), (0.012, H, L2 - 0.04), GALV, bevel=0.0))
    # end frames (front panel closes the end; back end open frame with a cross brace)
    o.append(gbox("end_panel", (-T2, 0.26, L2 - 0.020), (T2, H + 0.04, L2), GALV, bevel=0.0))
    o.append(gbox("end_flange_l", (-T2 - 0.004, 0.26, L2 - 0.034), (-T2 + 0.040, H + 0.04, L2 + 0.004), PAINT, bevel=0.0))
    o.append(gbox("end_flange_r", (T2 - 0.040, 0.26, L2 - 0.034), (T2 + 0.004, H + 0.04, L2 + 0.004), PAINT, bevel=0.0))
    o.append(gbox("end_cap", (-T2 - 0.006, H + 0.04, L2 - 0.040), (T2 + 0.006, H + 0.075, L2 + 0.006), PAINT, bevel=0.0))
    o.append(gbox("end_foot", (-T2 - 0.004, 0.14, L2 - 0.034), (T2 + 0.004, 0.30, L2 + 0.006), PAINT, bevel=0.0))
    o.append(gbox("back_l", (-T2, 0.26, -L2), (-T2 + 0.045, H + 0.04, -L2 + 0.04), PAINT, bevel=0.0))
    o.append(gbox("back_r", (T2 - 0.045, 0.26, -L2), (T2, H + 0.04, -L2 + 0.04), PAINT, bevel=0.0))
    o.append(gbox("back_cap", (-T2, H + 0.04, -L2), (T2, H + 0.070, -L2 + 0.045), PAINT, bevel=0.0))
    # top cover
    o.append(gbox("top", (-T2 - 0.004, H + 0.04, -L2), (T2 + 0.004, H + 0.075, L2 - 0.040), GALV, bevel=0.0))
    # uprights on both faces + shelf decks with front lips
    for sx in (-1, 1):
        xo = sx * T2
        for z in (-1.60, -0.80, 0.0, 0.80, 1.55):
            zz = min(max(z, -L2 + 0.025), L2 - 0.075)
            o.append(gbox("up", (min(xo, xo - sx * 0.040), 0.26, zz - 0.025), (max(xo, xo - sx * 0.040), H, zz + 0.025), PAINT, bevel=0.0))
        for ly in LEVELS:
            x0, x1 = sorted((sx * 0.012, sx * (T2 - 0.004)))
            o.append(gbox("deck", (x0, ly - 0.012, -L2 + 0.04), (x1, ly + 0.006, L2 - 0.075), GALV, bevel=0.0))
            lo, hi = sorted((sx * (T2 - 0.012), sx * (T2 + 0.004)))
            o.append(gbox("lip", (lo, ly - 0.034, -L2 + 0.04), (hi, ly + 0.050, L2 - 0.075), GALV, bevel=0.0))
    return o


def contents(seed):
    rnd = random.Random(seed * 77 + 5)
    o = []
    boxes, cans, labels = [], [], []
    bays = [(-1.58 + 0.80 * k + 0.05, -1.58 + 0.80 * (k + 1) - 0.05) for k in range(4)]
    # the 5th upright at z=+1.55 closes the last bay (shelf ends at z = L2 - 0.075 = 1.525)
    bays[3] = (bays[3][0], 1.50)
    for sx in (-1, 1):
        for li, ly in enumerate(LEVELS):
            top = ly + 0.006
            for bi, (z0, z1) in enumerate(bays):
                r = rnd.random()
                if r < 0.30:
                    continue                                  # empty bay
                xa, xb = sorted((sx * 0.05, sx * (T2 - 0.05)))
                if r < 0.68:                                  # archive boxes standing in a row
                    n = rnd.randint(2, 4)
                    zc = z0 + 0.03
                    for _ in range(n):
                        w = rnd.uniform(0.10, 0.17)
                        h = rnd.uniform(0.26, 0.34)
                        if zc + w > z1:
                            break
                        boxes.append(gbox("bx", (xa, top, zc), (xb, top + h, zc + w), "M_Cardboard", bevel=0.0))
                        if rnd.random() < 0.6:
                            labels.append(gbox("lb", (min(sx * (T2 - 0.050), sx * (T2 - 0.0555)), top + h * 0.35, zc + 0.012),
                                               (max(sx * (T2 - 0.050), sx * (T2 - 0.0555)), top + h * 0.35 + 0.05, zc + w - 0.012), "M_Paper", bevel=0.0))
                        zc += w + rnd.uniform(0.0, 0.05)
                else:                                         # stacks of film cans
                    k = 0
                    zc = z0 + 0.12
                    while zc + 0.11 < z1 and k < 2:
                        n = rnd.randint(2, 3)
                        rr = rnd.choice((0.09, 0.10, 0.12))
                        cx = (xa + xb) / 2
                        for j in range(n):
                            cans.append(gcyl("cn", rr, 0.046, (cx, top + j * 0.048, zc), axis="y", verts=6, mat=GALV, bevel=0.0))
                        zc += 2 * rr + 0.04
                        k += 1
    for lst, nm in ((boxes, "boxes"), (cans, "cans"), (labels, "labels")):
        if lst:
            o.append(M.join(lst, nm) if len(lst) > 1 else lst[0])
    return o


def end_fittings(i):
    o = []
    # tag holder: dark frame, card behind glass lip
    o.append(gbox("tag_frame", (-0.115, TAG_Y - 0.075, L2), (0.115, TAG_Y + 0.075, L2 + 0.010), DARK, bevel=0.0))
    o.append(gbox("tag_bed", (-0.100, TAG_Y - 0.060, L2 + 0.010), (0.100, TAG_Y + 0.060, L2 + 0.0124), "M_Paper", bevel=0.0))
    # crank gearbox: a cast housing on the end panel, shaft stub
    o.append(glathe("gbox", [(0.0, 0.0), (0.085, 0.0), (0.09, 0.012), (0.09, 0.050), (0.075, 0.062), (0.0, 0.062)], (0.0, CRANK_Y, L2), axis="z",
                    segments=20, mat=PAINT))
    o.append(gbox("gb_plate", (-0.13, CRANK_Y - 0.13, L2), (0.13, CRANK_Y + 0.13, L2 + 0.008), DARK, bevel=0.0))
    rv = [(sx * 0.105, CRANK_Y + sy * 0.105, L2 + 0.008) for sx in (-1, 1) for sy in (-1, 1)]
    o.append(X.rivets("gbr", rv, 0.0075, "z", mat=DARK, segs=6))
    o.append(gcyl("shaft", 0.014, 0.030, (0.0, CRANK_Y, L2 + 0.062), axis="z", verts=10, mat="M_Chrome", bevel=0.0))
    # lower end plate: yellow-black style hazard bars (painted stripes)
    for k in range(7):
        x = -0.40 + k * 0.133
        o.append(gbox(f"hz{k}", (x, 0.30, L2 + 0.002), (x + 0.060, 0.43, L2 + 0.004), "M_Brass_Aged", bevel=0.0))
    # number rivets + a small stencil strip: a short brass reading pointer for the slot position
    o.append(gbox("ptr_plate", (-0.05, 2.18, L2), (0.05, 2.26, L2 + 0.006), "M_Brass_Aged", bevel=0.0))
    return o


def crank(i):
    r = 0.150
    wh = X.wheel("crank", r, 0.013, 3, (0.0, CRANK_Y, CRANK_Z), axis="z", hub_r=0.030, boss_h=0.020, mat="M_Enamel_Crimson", hub_mat="M_Chrome", ring_seg=14, phase=math.pi / 2)
    # spinner handle: a bakelite knob on a short pin at the rim (12 o'clock)
    pin = gcyl("pin", 0.007, 0.050, (0.0, CRANK_Y + r - 0.0, CRANK_Z + 0.004), axis="z", verts=8, mat="M_Chrome", bevel=0.0)
    knob = glathe("knob", [(0.0, 0.0), (0.022, 0.0), (0.027, 0.020), (0.022, 0.050), (0.0, 0.056)], (0.0, CRANK_Y + r, CRANK_Z + 0.050), axis="z",
                  segments=14, mat="M_Bakelite")
    return part("IA_crank", [wh, pin, knob], (0.0, CRANK_Y, CRANK_Z))


def build(i):
    X.begin()
    X.decal("M_Decal_CarriageTags", "carriage_tags.png")
    st = structure() + contents(i) + end_fittings(i)
    # end tag quad with the UV cell of this carriage
    u0, u1 = (i - 1) / 5.0, i / 5.0
    tag = K.quad_decal("end_tag", (0.0, TAG_Y, L2 + 0.0127), (1, 0, 0), (0, 1, 0), 0.20, 0.12, "M_Decal_CarriageTags", uv=(u0, 0.0, u1, 1.0))
    tag = part("end_tag", [tag], (0.0, TAG_Y, L2 + 0.0127), presmooth=False)
    ia = crank(i)
    mount("light_carriage", (0.0, 2.2, 0.0))
    A.presmooth([o for o in st if o is not None])
    part("carriage_body", [o for o in st if o is not None], (0, 0, 0), presmooth=False)
    return ia


def one(i):
    ia = build(i)
    name = f"carriage_{i}"
    req = ["carriage_body", "IA_crank", "end_tag", "light_carriage"]
    X.C.finalize_all(wood_grain=False)
    total = X.C.report(name)
    path = X.C.export(name)
    errs = X.C.verify_glb(path, required=req, identity=["IA_crank", "end_tag"], budget=BUDGET, expect={"IA_crank": (0.0, CRANK_Y, CRANK_Z)},
                          show=["IA_crank", "end_tag"])
    print(f"{X.TAG} {name}: tris={total} errors={len(errs)}")
    return ia


def main():
    last = None
    for i in (1, 2, 3, 4, 5):
        last = one(i)
    if X.want_render(ARGS):
        X.begin()
        X.decal("M_Decal_CarriageTags", "carriage_tags.png")
        # two carriages side by side with a 1 m aisle: shows the shelf faces and the end tags
        X.C.qa_import(X.C.model_glb("carriage_1"), (-0.46 - 0.55, 0.0, 0.0), 0)
        X.C.qa_import(X.C.model_glb("carriage_4"), (0.46 + 0.55, 0.0, 0.0), 0)
        M.box("qa_floor", (9, 9, 0.02), loc=(0, 0, -0.01), mat="M_Concrete", bevel=0.0)
        K.retex()
        K.fix_pbr()
        COLD = [((0.0, 2.2, 4.2), 700, "D8EAFF", 0.5), ((0.0, 3.2, 0.0), 600, "BFD8FF", 0.6), ((-2.5, 1.6, 3.2), 250, "FFE9CC", 0.8)]
        X.qa_props("cold_carriage", [("_front", (0.0, 1.45, 4.6), (0.0, 1.15, 1.2), 44), ("_aisle", (0.0, 1.5, 2.4), (0.0, 1.2, -0.8), 58)],
                   floor=False, world=0.7, lights=K.glights(COLD), res=(900, 640))


main()
