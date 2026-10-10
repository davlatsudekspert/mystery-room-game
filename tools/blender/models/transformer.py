"""transformer.glb — the Choir Hall's three oil transformers with their Jacob's ladders (×3: transformer_0..2).
Contract: docs/models/ch3.md §4 transformer (+ §1.2 placement, §10 welder contact point); results: docs/models/ch3_b.md.

Free-standing, front +Z (faces into the hall), origin = the footprint centre. Placed at (-12.45, 0, -3.0 / -1.3 / 0.4),
yaw 90 (the front faces world +X, the fins face the neighbours along the west wall). Nothing above y = 3.6: the
catwalk deck is at 4.0.

  transformer (static)   painted steel: a channel-iron skid, the base section with the bolted seam at y 0.62 (the
                         welder's torch tip meets it at (0, 0.62, 0.45)), the riveted tank with a lid flange, lifting
                         lugs and drain valve, radiator fins on both sides with header pipes, the conservator drum on
                         saddles with its filler cap and down pipe, the bushing flanges and the lamp housing
                         (M_Steel_Painted); three brown porcelain bushings (M_Porcelain); the copper rating plate with
                         its rivets, the bushing terminals, the feed bars, the two diverging rods of the Jacob's
                         ladder (gap 0.03 at y 2.35, 0.36 at y 3.50) with their ball ends (M_Copper).
  hum_lamp               a glazed jewel at (0.45, 1.50, 0.46) on the front face (M_Porcelain; the code tints it).
  arc_base / arc_top     empties (0, 2.38, 0) / (0, 3.48, 0): the code spawns the climbing arc between them.
  echo_mount             floor empty (-0.10, 0, 0.93) facing -Z (rotated 180° about Y): echo_welder on transformer_1.

    blender -b --factory-startup -P tools/blender/models/transformer.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "transformer"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 4, 4
PAINT, PORC, COPPER = B.PAINT, B.PORC, B.COPPER

X2, Z2 = 0.60, 0.45                      # tank half width / half depth
PLINTH_H, SEAM_Y, TANK_TOP = 0.12, 0.62, 1.87
BUSH_X = (-0.38, 0.0, 0.38)
BUSH_Z = 0.0
BUSH_TOP = (2.35, 2.17, 2.35)            # the middle bushing is lower: the feed bars pass over it
ROD_BASE, ROD_TOP = (0.027, 2.355), (0.18, 3.50)  # rod end x (±) and y: ball gap 0.03 / rod-axis gap 0.36
DRUM = (0.16, -0.27, 2.08)               # conservator radius, z, y
LAMP = (0.45, 1.50, 0.46)
PLATE = (-0.30, 1.40)
ARC_BASE, ARC_TOP = (0.0, 2.38, 0.0), (0.0, 3.48, 0.0)
ECHO = (-0.10, 0.0, 0.93)
PLACES = ((-12.45, 0.0, -3.0), (-12.45, 0.0, -1.3), (-12.45, 0.0, 0.4))
YAW = 90.0


# ====================================================================== painted steel
def skid_and_tank():
    p = []
    # channel-iron skid: two rails along X, two cross members, four levelling pads
    for sz in (-1, 1):
        p.append(B.gbox("rail", (-X2 - 0.02, 0.0, sz * 0.36 - 0.06), (X2 + 0.02, PLINTH_H, sz * 0.36 + 0.06), PAINT, 0.004))
    for sx in (-1, 1):
        p.append(B.gbox("cross", (sx * 0.45 - 0.05, 0.02, -0.36), (sx * 0.45 + 0.05, PLINTH_H, 0.36), PAINT, 0.003))
    p.append(B.gbox("deck", (-X2 - 0.005, PLINTH_H - 0.02, -Z2 - 0.005), (X2 + 0.005, PLINTH_H, Z2 + 0.005), PAINT, 0.003))
    # base section (a shade larger than the tank: the bolted seam steps in at y 0.62)
    p.append(B.gbox("base", (-X2 - 0.005, PLINTH_H, -Z2 - 0.005), (X2 + 0.005, SEAM_Y, Z2 + 0.005), PAINT, 0.006, 1))
    # seam bolts on the base's top edge, front and sides (x = 0 left free for the torch tip)
    for x in (-0.48, -0.30, -0.12, 0.12, 0.30, 0.48):
        p.append(B.hexbolt("sbolt", 0.011, (x, SEAM_Y - 0.035, Z2 + 0.005), normal=(0, 0, 1), h=0.012, mat=PAINT,
                           washer=False))
    for sx in (-1, 1):
        for z in (-0.33, -0.11, 0.11, 0.33):
            p.append(B.hexbolt("sbolt", 0.011, (sx * (X2 + 0.005), SEAM_Y - 0.035, z), normal=(sx, 0, 0), h=0.012,
                               mat=PAINT, washer=False))
    # the tank, its lid flange and the lid
    p.append(B.gbox("tank", (-X2, SEAM_Y, -Z2), (X2, TANK_TOP - 0.03, Z2), PAINT, 0.014, 2))
    p.append(B.gbox("lidfl", (-X2 - 0.025, TANK_TOP - 0.03, -Z2 - 0.025), (X2 + 0.025, TANK_TOP, Z2 + 0.025), PAINT, 0.004))
    p.append(B.gbox("lid", (-X2 + 0.02, TANK_TOP, -Z2 + 0.02), (X2 - 0.02, TANK_TOP + 0.02, Z2 - 0.02), PAINT, 0.005))
    for x in (-0.50, -0.25, 0.0, 0.25, 0.50):
        p.append(B.hexbolt("lbolt", 0.010, (x, TANK_TOP, Z2 + 0.012), normal=(0, 1, 0), h=0.010, mat=PAINT, washer=False))
    # rivet rows down the tank's four vertical corner seams (front and sides)
    for y in [SEAM_Y + 0.10 + 0.155 * k for k in range(7)]:
        for sx in (-1, 1):
            p.append(B.rivet("rv", 0.009, (sx * (X2 - 0.035), y, Z2), normal=(0, 0, 1), mat=PAINT, segs=6))
            p.append(B.rivet("rv", 0.009, (sx * X2, y, Z2 - 0.035), normal=(sx, 0, 0), mat=PAINT, segs=6))
            p.append(B.rivet("rv", 0.009, (sx * X2, y, -Z2 + 0.035), normal=(sx, 0, 0), mat=PAINT, segs=6))
    # lifting lugs on the lid flange corners
    for sx in (-1, 1):
        for sz in (-1, 1):
            lug = B.plate("lug", [L.rounded_rect(0.07, 0.06, 0.012, 2), list(reversed(L.circle(0.012, 10, cy=0.012)))],
                          0.012, mat=PAINT, bevel=0.0, loc=(sx * 0.46, TANK_TOP + 0.03, sz * (Z2 + 0.012)), drop_bottom=False)
            p.append(lug)
    # drain valve at the bottom front-left: a boss and a square-headed plug
    p.append(B.glathe("drain", [(0.0, 0.0), (0.028, 0.0), (0.028, 0.025), (0.020, 0.030), (0.020, 0.050), (0.0, 0.050)],
                      (-0.46, 0.22, Z2), (0, 0, 1), 10, PAINT, smooth=45.0))
    return p


def fins():
    """Radiator fins on both sides (local ±X) with top and bottom header pipes."""
    p = []
    for sx in (-1, 1):
        x0, x1 = (X2, X2 + 0.13) if sx > 0 else (-X2 - 0.13, -X2)
        for k in range(8):
            z = -0.35 + 0.10 * k
            p.append(B.gbox("fin", (x0, 0.78, z - 0.011), (x1, 1.74, z + 0.011), PAINT, 0.0))
        for y in (0.83, 1.69):
            p.append(B.gcyl("header", 0.030, -0.40, 0.40, base=(sx * (X2 + 0.10), y, 0.0), axis=(0, 0, 1), segments=10,
                            mat=PAINT, chamfer=0.004))
            # stubs from the headers into the tank
            for z in (-0.30, 0.30):
                p.append(B.gcyl("stub", 0.018, 0.0, 0.10, base=(sx * X2, y, z), axis=(sx, 0, 0), segments=8, mat=PAINT,
                                caps=False))
    return p


def conservator():
    r, z, y = DRUM
    p = []
    prof = [(0.0, -0.52), (r * 0.72, -0.52), (r, -0.47), (r, 0.47), (r * 0.72, 0.52), (0.0, 0.52)]
    p.append(B.glathe("drum", prof, (0.0, y, z), (1, 0, 0), 18, PAINT, smooth=45.0))
    # hoops, filler cap on top, oil level pipe, saddles down to the lid, the down pipe into the tank
    for x in (-0.30, 0.30):
        p.append(B.glathe("hoop", [(r + 0.006, -0.012), (r + 0.006, 0.012)], (x, y, z), (1, 0, 0), 18, PAINT, smooth=45.0,
                          cap_bottom=False, cap_top=False))
    p.append(B.glathe("cap", [(0.0, 0.0), (0.035, 0.0), (0.035, 0.03), (0.03, 0.04), (0.0, 0.04)], (0.0, y + r - 0.004, z),
                      (0, 1, 0), 10, PAINT, smooth=45.0))
    for x in (-0.38, 0.38):
        # saddle block from the lid up into the drum (the top is hidden inside it)
        p.append(B.gbox("saddle", (x - 0.03, TANK_TOP + 0.02, z - 0.14), (x + 0.03, y - r + 0.05, z + 0.14), PAINT, 0.003))
    p.append(B.gcyl("downpipe", 0.016, TANK_TOP + 0.015, y - r + 0.02, base=(0.46, 0.0, z + 0.02), axis=(0, 1, 0), segments=8,
                    mat=PAINT, caps=False))
    return p


def bushing_flanges_and_lamp_housing():
    p = []
    for x, top in zip(BUSH_X, BUSH_TOP):
        p.append(B.glathe("bflange", [(0.0, 0.0), (0.105, 0.0), (0.105, 0.012), (0.085, 0.020), (0.0, 0.020)],
                          (x, TANK_TOP + 0.02, BUSH_Z), (0, 1, 0), 16, PAINT, smooth=45.0))
        for k in range(4):
            a = math.radians(45 + 90 * k)
            p.append(B.hexbolt("fbolt", 0.007, (x + 0.092 * math.cos(a), TANK_TOP + 0.032, BUSH_Z + 0.092 * math.sin(a)),
                               normal=(0, 1, 0), h=0.008, mat=PAINT, washer=False))
    lx, ly, lz = LAMP
    p.append(B.glathe("lhouse", [(0.0, 0.0), (0.034, 0.0), (0.034, 0.008), (0.026, 0.012), (0.022, 0.012), (0.0, 0.012)],
                      (lx, ly, Z2), (0, 0, 1), 14, PAINT, smooth=45.0))
    return p


# ====================================================================== porcelain and copper
def bushing(x, top):
    """Brown glazed bushing: a stack of sheds from the flange to the top, then a neck for the terminal."""
    y0 = TANK_TOP + 0.04
    prof = [(0.0, y0), (0.070, y0), (0.070, y0 + 0.02)]
    y = y0 + 0.03
    n = 0
    while y + 0.075 < top - 0.04:
        prof += [(0.098, y + 0.012), (0.098, y + 0.022), (0.072, y + 0.034), (0.072, y + 0.055)]
        y += 0.075
        n += 1
    prof += [(0.058, top - 0.02), (0.040, top - 0.006), (0.0, top - 0.006)]
    return B.glathe("bush", prof, (x, 0.0, BUSH_Z), (0, 1, 0), 16, PORC, smooth=50.0)


def porcelain():
    return [bushing(x, top) for x, top in zip(BUSH_X, BUSH_TOP)]


def copper():
    p = []
    # terminal caps on the bushings
    for x, top in zip(BUSH_X, BUSH_TOP):
        p.append(B.glathe("term", [(0.0, -0.006), (0.030, -0.006), (0.030, 0.012), (0.024, 0.018), (0.018, 0.018),
                                   (0.018, 0.0), (0.0, 0.0)], (x, top, BUSH_Z), (0, 1, 0), 12, COPPER, smooth=50.0))
    # the ladder: ball terminals 0.03 apart at the base, rods diverging to 0.36 at the top, ball tips
    bx, by = ROD_BASE
    tx, ty = ROD_TOP
    for sx in (-1, 1):
        base = Vector((sx * bx, by, BUSH_Z))
        tip = Vector((sx * tx, ty, BUSH_Z))
        d = tip - base
        p.append(B.gcyl("rod", 0.0075, 0.0, d.length, base=tuple(base), axis=tuple(d), segments=8, mat=COPPER))
        for c, r in ((base, 0.013), (tip, 0.011)):
            s = M.sphere("ball", r, loc=tuple(c), segments=10, rings=6, mat=COPPER)
            M.apply_transform(s)
            A.hint(s, 80.0)
            p.append(s)
        # feed bar from the outer terminal to the ball terminal
        p.append(B.gcyl("feed", 0.007, 0.0, abs(BUSH_X[2]) - bx, base=(sx * bx, by, BUSH_Z), axis=(sx, 0, 0), segments=8,
                        mat=COPPER))
    # strap from the middle terminal down to a tank-top terminal block
    p.append(B.gbox("strap", (-0.012, TANK_TOP + 0.02, BUSH_Z + 0.16), (0.012, BUSH_TOP[1] + 0.006, BUSH_Z + 0.19), COPPER, 0.0))
    p.append(B.gbox("strap_t", (-0.012, BUSH_TOP[1] - 0.006, BUSH_Z + 0.016), (0.012, BUSH_TOP[1] + 0.006, BUSH_Z + 0.19),
                    COPPER, 0.0))
    # rating plate on the front (blank, riveted)
    px, py = PLATE
    p.append(B.plate("rplate", [L.rounded_rect(0.22, 0.14, 0.008, 2)], 0.004, mat=COPPER, bevel=0.0008, loc=(px, py, Z2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(B.rivet("prv", 0.005, (px + sx * 0.098, py + sy * 0.058, Z2 + 0.004), normal=(0, 0, 1), mat=COPPER, segs=6))
    return p


def static():
    return B.part(NAME, skid_and_tank() + fins() + conservator() + bushing_flanges_and_lamp_housing() + porcelain() + copper())


# ====================================================================== lamp and empties
def hum_lamp():
    lx, ly, lz = LAMP
    o = B.jewel("jewel", (lx, ly, lz - 0.002), 0.017, normal=(0, 0, 1), mat=PORC, h=0.018, seg=12)
    return B.part("hum_lamp", [o], pivot=LAMP)


def empties():
    return [B.empty("arc_base", ARC_BASE), B.empty("arc_top", ARC_TOP), B.empty("echo_mount", ECHO, (0.0, 180.0, 0.0))]


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    lamp = hum_lamp()
    emp = empties()
    B.K.to_blender()
    A.finalize_uv()
    return dict(static=st, lamp=lamp, empties=emp)


REQ = [NAME, "hum_lamp", "arc_base", "arc_top", "echo_mount"]


def verify(path):
    expect = {"hum_lamp": LAMP, "arc_base": ARC_BASE, "arc_top": ARC_TOP, "echo_mount": ECHO}
    errs = B.verify(path, REQ, identity=[NAME, "hum_lamp"], expect=expect, parents={n: None for n in REQ},
                    rot_expect={"echo_mount": (0.0, 180.0, 0.0)}, tris=TRI_BUDGET, surf=SURF_BUDGET, mats=MAT_BUDGET)
    lo, hi = B.V.mesh_bounds_godot([o for o in bpy.data.objects if o.type == "MESH"])
    print(f"{B.TAG} bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    if hi.y > 3.6:
        errs.append(f"top {hi.y:.3f} above 3.6 (catwalk at 4.0)")
    # the ladder gap at the arc base and top (measured on the rods' axes)
    g0, g1 = 2 * (ROD_BASE[0] - 0.013), 2 * ROD_TOP[0]
    print(f"{B.TAG} ladder gap: {g0:.3f} between the ball terminals at y {ROD_BASE[1]}, {g1:.2f} between the rod axes at y {ROD_TOP[1]}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    B.qa_begin()
    B.hall()
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    # this scene's objects are transformer_1 (the welder's); 0 and 2 are imported copies
    B.place(mine, PLACES[1], YAW, name="qa_tr_1")
    B.bring(NAME, PLACES[0], YAW, prefix="qa_t0_")
    B.bring(NAME, PLACES[2], YAW, prefix="qa_t2_")
    green = B.K.glow("qa_hum_green", "45FF70", 3.0)
    for o in (parts["lamp"], B.imported("qa_t0_", "hum_lamp"), B.imported("qa_t2_", "hum_lamp")):
        if o is not None:
            B.K.override(o, green)
    mount = bpy.data.objects["echo_mount"]
    welder = B.bring("echo_welder", under=mount, prefix="qa_welder_")
    if welder is not None:
        B.ghost([o for o in welder.children_recursive if o.type == "MESH"])
    # QA stand-ins for the code's effects: a spark glow at the torch tip, an arc between the rods
    spark = M.sphere("qa_spark", 0.012, segments=8, rings=4, mat="M_Emissive_Warm")
    tip = B.imported("qa_welder_", "torch_tip")
    if tip is not None:
        spark.parent = tip
        spark.matrix_parent_inverse = Matrix.Identity(4)
        spark.matrix_basis = Matrix.Identity(4)
    spark.hide_render = True
    arc = B.K.glow("qa_arc", "BFD8FF", 30.0)
    arc_pts = [(0.0, 2.40, 0.0), (0.03, 2.62, 0.01), (-0.02, 2.80, -0.01), (0.04, 2.98, 0.0), (0.0, 3.10, 0.0)]
    arc_obj = A.tube("qa_arc_tube", [B.G(*p) for p in arc_pts], 0.004, sides=5, mat="M_Emissive_Lumen")
    arc_obj.parent = bpy.data.objects["qa_tr_1"]
    arc_obj.matrix_parent_inverse = Matrix.Identity(4)
    B.K.override(arc_obj, arc)
    arc_obj.hide_render = True
    M.refresh()

    shots = [
        # 1 hero: the three transformers along the west wall under the catwalk, from the hall floor
        ("1", NAME, (-9.9, 1.7, 1.5), (-12.35, 1.55, -1.3), 52, dict()),
        # 2 port_b_mem view: the welder kneeling at transformer_1, torch on the base seam
        ("2", NAME + "_2", (-10.0, 1.6, -0.9), (-11.45, 0.9, -1.3), 48, dict(welder=True, spark=True)),
        # 3 the bushings and the Jacob's ladder (hall running: arc climbing, lamp green)
        ("3", NAME + "_3", (-11.2, 2.0, -0.55), (-12.45, 2.75, -1.3), 42, dict(arc=True)),
        # 4 choir view (root view of the hall)
        ("4", NAME + "_4", (-5.4, 1.65, 3.3), (-9.6, 1.5, -2.0), 62, dict()),
    ]
    for tag, name, cam, tgt, fov, st in shots:
        if not B.want(args, tag):
            continue
        if welder is not None:
            for o in welder.children_recursive:
                o.hide_render = not st.get("welder", False)
        spark.hide_render = not (st.get("spark", False) and tip is not None)
        arc_obj.hide_render = not st.get("arc", False)
        extra = [("arcs", "POINT", (-12.3, 3.0, -1.3), 60.0, "9FC4FF", 0.1)] if st.get("arc") else []
        if st.get("spark"):
            extra.append(("sparkl", "POINT", (-11.47, 0.66, -1.30), 6.0, "FFB060", 0.03))
        B.choir_lights(cam, fill=8.0 if tag != "4" else 0.0, extra=extra)
        B.shoot(name, cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
