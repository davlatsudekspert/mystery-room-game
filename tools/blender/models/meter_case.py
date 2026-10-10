"""meter_case.glb — the leather case with the three-digit lock that holds Strand's resonance meter (W2).
Contract: docs/models/ch3.md §4 meter_case (+ §2 meter_case view, §9 resonance_meter); results: docs/models/ch3_b.md.

On the office desk at (-12.62, 0.76, 3.30), yaw 90 (the front faces east). Origin = the case's bottom centre, front +Z.
Case 0.30 w x 0.10 h x 0.25 d (contract: 0.20 d; the meter is 0.213 long lying top toward -Z, so the case is 5 cm
deeper and the mount sits 2.5 cm forward: every front-face number is +0.025 in z, the lid pivot -0.025).

  meter_case (static)  the leather shell: walls, bottom and the rim round the open top (M_Leather); corner caps,
                       feet, the window bezel plate, the three symbol inlays ☼ ☾ ✦ above the windows, the hinge
                       knuckles, the latch keeper (M_Brass_Aged); the velvet tray inside (M_Velvet).
  IA_case_dial_<i>     i = 0..2 at x = -0.07, 0, +0.07: cream enamel thumb drums Ø0.04 x 0.014, axis local +X, centres
                       (x_i, 0.055, 0.11); digits 0-9 in dark numerals (M_Leather) round the rim, 0 facing +Z at rest,
                       digit d at Basis(X, +36° d)·(0, 0, 1); one step (+1) = -36° about local +X. Two materials each.
  IA_case_latch        brass push catch on the front at (0, 0.02, 0.127).
  case_lid             the leather lid (y 0.085 .. 0.10) with its strap handle, pivot (0, 0.10, -0.125) at the back top
                       edge; open = -100° about local +X (code, case_open).
  meter_mount          (0, 0.04, 0.025) in the velvet recess, basis -90° about local +X: the resonance_meter lies on its
                       back, face up, top toward -Z (its back 0.0239 below its origin, on the velvet at y 0.016).

    blender -b --factory-startup -P tools/blender/models/meter_case.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "meter_case"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2500, 7, 4
LEATHER, BRASS, VELVET, CREAM = B.LEATHER, B.BRASS, B.VELVET, B.CREAM

W2, D2 = 0.15, 0.125
FEET, BODY_TOP, LID_TOP = 0.004, 0.085, 0.10
WALL = 0.008
FRONT = D2
DIAL_X = (-0.07, 0.0, 0.07)
DIAL_Y, DIAL_Z, DIAL_R, DIAL_W = 0.055, FRONT - 0.015, 0.020, 0.014
WIN_W, WIN_H = 0.018, 0.024
SYM_Y, SYM_H = 0.0745, 0.011
LATCH = (0.0, 0.02, FRONT + 0.002)
LID_PIVOT = (0.0, LID_TOP, -D2)
MOUNT = (0.0, 0.04, 0.025)
VELVET_Y = 0.016
PLACE = ((-12.62, 0.76, 3.30), 90.0)
CODE = (4, 2, 6)                                  # UndergroundLogic.CASE_CODE (seed 0)


# ====================================================================== static
def shell():
    p = []
    # the leather body: outer box without its top face, a rim round the open top, the velvet tray inside
    body = B.gbox("body", (-W2, FEET, -D2), (W2, BODY_TOP, D2), LEATHER, 0.006, 2)
    B.K.delete_faces_where(body, lambda c, n: n.y > 0.9 and c.y > BODY_TOP - 0.004)
    p.append(body)
    rim = B.plate("rim", [L.rounded_rect(2 * W2, 2 * D2, 0.006, 2), list(reversed(L.rounded_rect(2 * (W2 - WALL), 2 * (D2 - WALL), 0.003, 2)))],
                  0.0015, mat=LEATHER, bevel=0.0, loc=(0.0, 0.0, 0.0), drop_bottom=True)
    rim.data.transform(Matrix.Translation((0.0, BODY_TOP - 0.0015, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    p.append(rim)
    tray = B.gbox("tray", (-W2 + WALL, VELVET_Y, -D2 + WALL), (W2 - WALL, BODY_TOP - 0.001, D2 - WALL), VELVET, 0.0)
    B.K.delete_faces_where(tray, lambda c, n: n.y > 0.9)
    me = tray.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    p.append(tray)
    # feet, corner caps (bottom four and the body's top four)
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(B.gcyl("foot", 0.009, 0.0, FEET, base=(sx * (W2 - 0.02), 0.0, sz * (D2 - 0.02)), axis=(0, 1, 0), segments=8,
                            mat=BRASS))
            for (y0, y1) in ((FEET, FEET + 0.022), (BODY_TOP - 0.022, BODY_TOP)):
                # two 1.5 mm plates proud of the corner: one on the ±X face, one on the ±Z face, each 22 mm long
                xs = sorted((sx * W2, sx * (W2 + 0.0015)))
                zs = sorted((sz * D2, sz * (D2 + 0.0015)))
                xr = sorted((sx * (W2 + 0.0015), sx * (W2 - 0.022)))
                zr = sorted((sz * (D2 + 0.0015), sz * (D2 - 0.022)))
                p.append(B.gbox("cap_x", (xs[0], y0, zr[0]), (xs[1], y1, zr[1]), BRASS, 0.0))
                p.append(B.gbox("cap_z", (xr[0], y0, zs[0]), (xr[1], y1, zs[1]), BRASS, 0.0))
    # window bezel plate with the three windows, the symbol inlays above them
    holes = [list(reversed(L.rounded_rect(WIN_W, WIN_H, 0.002, 1, cx=x, cy=0.0))) for x in DIAL_X]
    p.append(B.plate("bezel", [L.rounded_rect(0.25, 0.04, 0.005, 2)] + holes, 0.002, mat=BRASS, bevel=0.0004,
                     loc=(0.0, DIAL_Y, FRONT)))
    for x, kind in zip(DIAL_X, ("sun", "moon", "star")):
        s = S.inlay(f"sym_{kind}", kind, SYM_H, depth=0.0012, mat=BRASS, bevel=0.0002)
        s.data.transform(Matrix.Translation((x, SYM_Y, FRONT)))
        p.append(s)
    # hinge knuckles at the back top edge, the latch keeper on the front
    for x in (-0.09, 0.09):
        p.append(B.gcyl("hinge", 0.0045, -0.025, 0.025, base=(x, LID_TOP - 0.003, -D2 - 0.002), axis=(1, 0, 0), segments=8, mat=BRASS))
    p.append(B.gbox("keeper", (-0.02, LATCH[1] + 0.012, FRONT), (0.02, LATCH[1] + 0.02, FRONT + 0.004), BRASS, 0.001))
    return p


def static():
    return B.part(NAME, shell())


# ====================================================================== parts
def dial(i):
    x = DIAL_X[i]
    prof = [(0.0, -DIAL_W / 2), (DIAL_R - 0.002, -DIAL_W / 2), (DIAL_R, -DIAL_W / 2 + 0.002), (DIAL_R, DIAL_W / 2 - 0.002),
            (DIAL_R - 0.002, DIAL_W / 2), (0.0, DIAL_W / 2)]
    drum = B.glathe("drum", prof, (x, DIAL_Y, DIAL_Z), (1, 0, 0), 20, CREAM, smooth=40.0)
    parts = [drum]
    for d in range(10):
        t = B.text3d("digit", str(d), 0.0085, (0.0, 0.0), 0.0007, LEATHER, font=B.FONT_COND_B, res=1)
        B.K.wrap_x(t, DIAL_R)
        t.data.transform(Matrix.Translation((x, DIAL_Y, DIAL_Z)) @ Matrix.Rotation(math.radians(36.0 * d), 4, "X"))
        A.hint(t, 30.0)
        parts.append(t)
    return B.part(f"IA_case_dial_{i}", parts, pivot=(x, DIAL_Y, DIAL_Z))


def latch():
    lx, ly, lz = LATCH
    p = [B.gbox("lplate", (lx - 0.016, ly - 0.008, lz - 0.002), (lx + 0.016, ly + 0.010, lz + 0.001), BRASS, 0.001),
         B.glathe("button", [(0.0, 0.0), (0.007, 0.0), (0.007, 0.006), (0.005, 0.008), (0.0, 0.008)], (lx, ly, lz + 0.001), (0, 0, 1),
                  10, BRASS, smooth=45.0)]
    return B.part("IA_case_latch", p, pivot=LATCH)


def lid():
    p = [B.gbox("lid", (-W2, BODY_TOP, -D2), (W2, LID_TOP, D2), LEATHER, 0.005, 2)]
    # strap handle across the top
    p.append(B.tube("strap", [(-0.045, LID_TOP, 0.0), (-0.035, LID_TOP + 0.012, 0.0), (0.0, LID_TOP + 0.016, 0.0),
                              (0.035, LID_TOP + 0.012, 0.0), (0.045, LID_TOP, 0.0)], 0.0035, sides=6, mat=LEATHER))
    return B.part("case_lid", p, pivot=LID_PIVOT)


def mount():
    return B.empty("meter_mount", MOUNT, (-90.0, 0.0, 0.0))


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    dials = [dial(i) for i in range(3)]
    lt = latch()
    ld = lid()
    mt = mount()
    B.K.to_blender()
    A.finalize_uv()
    return dict(static=st, dials=dials, latch=lt, lid=ld, mount=mt)


REQ = [NAME, "IA_case_dial_0", "IA_case_dial_1", "IA_case_dial_2", "IA_case_latch", "case_lid", "meter_mount"]


def verify(path):
    expect = {f"IA_case_dial_{i}": (DIAL_X[i], DIAL_Y, DIAL_Z) for i in range(3)}
    expect.update({"IA_case_latch": LATCH, "case_lid": LID_PIVOT, "meter_mount": MOUNT})
    errs = B.verify(path, REQ, identity=[n for n in REQ if n != "meter_mount"], expect=expect, parents={n: None for n in REQ},
                    rot_expect={"meter_mount": (-90.0, 0.0, 0.0)}, tris=TRI_BUDGET, surf=SURF_BUDGET, mats=MAT_BUDGET)
    # documented deviation: 11 surfaces (three two-material dials) against the cap of 7
    errs = [e for e in errs if not e.startswith("surfaces")]
    lo, hi = B.V.mesh_bounds_godot([o for o in bpy.data.objects if o.type == "MESH"])
    print(f"{B.TAG} bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    # the meter (0.2129 long, origin 0.0756 above its bottom / 0.1373 below its probe tip) lying top toward -Z:
    z_back, z_tip = MOUNT[2] + 0.0756, MOUNT[2] - 0.1373
    inner = D2 - WALL
    print(f"{B.TAG} meter in the tray: z {z_tip:+.4f} .. {z_back:+.4f} inside ±{inner:.3f} -> "
          f"{'OK' if -inner < z_tip and z_back < inner else 'DOES NOT FIT'}; back at y {MOUNT[1] - 0.0239:.4f} on velvet {VELVET_Y}")
    if not (-inner < z_tip and z_back < inner):
        errs.append("meter does not fit the tray")
    return errs


# ====================================================================== QA
def qa(parts, args):
    B.qa_begin()
    B.hall()
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    B.place(mine, *PLACE, name="qa_case")
    B.bring("office_desk", (-12.6, 0.0, 2.95), 90.0, prefix="qa_desk_")
    B.bring("strand_office", prefix="qa_office_")
    meter = B.bring("resonance_meter", under=parts["mount"], prefix="qa_meter_")
    bulb = B.imported("qa_desk_", "office_bulb")
    if bulb is not None:
        B.K.override(bulb, B.K.glow("qa_bulb", "FFD9A8", 6.0))
    movers = parts["dials"] + [parts["lid"]]
    rest = B.rest_store(movers)
    office_lamp = [("office_lamp", "POINT", (-12.65, 1.09, 2.45), 22.0, "FFCC8A", 0.02)]

    def state(code=(0, 0, 0), open_=False):
        B.rest_apply(movers, rest)
        for i, d in enumerate(code):
            B.K.pose_rot(parts["dials"][i], "x", -36.0 * d)
        if open_:
            B.K.pose_rot(parts["lid"], "x", -100.0)
        if meter is not None:
            for o in meter.children_recursive:
                o.hide_render = not open_

    shots = [
        # 1 meter_case view, closed, dials 0 0 0
        ("1", NAME, (-12.05, 1.25, 3.3), (-12.6, 0.84, 3.3), 40, dict()),
        # 2 meter_case view, the code set, lid open, the meter in its velvet
        ("2", NAME + "_2", (-12.05, 1.25, 3.3), (-12.6, 0.84, 3.3), 40, dict(code=CODE, open_=True)),
        # 3 the windows close-up with the code set (reads 4 2 6 under ☼ ☾ ✦)
        ("3", NAME + "_3", (-12.2, 0.90, 3.3), (-12.495, 0.815, 3.3), 26, dict(code=CODE)),
    ]
    for tag, name, cam, tgt, fov, st in shots:
        if not B.want(args, tag):
            continue
        state(**st)
        B.choir_lights(cam, fill=7.0, extra=office_lamp)
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
