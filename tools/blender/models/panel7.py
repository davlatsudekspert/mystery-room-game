"""panel7.glb — Panel 7: green-grey enamel electrical cabinet with the circuit-diagram plate (Lab 7, east wall).

Model space: front = Blender -Y (Godot +Z). BACK PLANE at Blender Y = 0; origin at the centre of the
back plane (cabinet vertical centre), so the lead places it at Godot (3.0, 1.45, -1.3), yaw -90°.
Cabinet 0.70 w x 0.90 h x 0.22 d; the door hangs open ~100° on its LEFT hinge (static).

Plate-local coordinates (metres, x right, y up, origin at plate centre) = Blender (x, z): the plate
centre sits on the model's X = 0, Z = 0 axis.
Parts (origins at pivots, identity rotation at rest):
  panel_plate        0.60 x 0.80, M_Decal_PanelDiagram on the front face, exact 0..1 planar UV (900:1200)
  lamp_0..3          jewel lenses only (M_Lamp_L/G/A/V) at plate (±0.065, ±0.195; +0.30)
  IA_switch_0..4     toggle levers at plate (−0.22..+0.22; −0.06); pivot on a horizontal X axle;
                     rest = DOWN = OFF (35° below horizontal); ON = rotate −70° about Godot X
  IA_main_lever      breaker fork at plate (0, −0.27); rest = DOWN = OFF (40° below); ON = −80° about X
    main_handle      child of IA_main_lever: bakelite grip (hide until installed)
  gauge_needle       voltmeter needle at plate (−0.25, +0.15); rest = 0 V; 220 V = −79° about Godot Z
  Static meshes are split (case l/r/t/b/back, plate, fittings, door) so no collider AABB hides the
  switches.
    blender -b --factory-startup -P tools/blender/models/panel7.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

W, H, D = 0.70, 0.90, 0.22
WALL = 0.022
R_OUT = 0.024
BACK_T = 0.012
PW, PH, PT = 0.60, 0.80, 0.004
PY = -0.034                    # plate front face
LAMPS = [(-0.195, 0.30, "M_Lamp_L"), (-0.065, 0.30, "M_Lamp_G"), (0.065, 0.30, "M_Lamp_A"), (0.195, 0.30, "M_Lamp_V")]
SWITCH_X = (-0.22, -0.11, 0.0, 0.11, 0.22)
SWITCH_Z = -0.06
SW_BASE_T = 0.005
SW_PIVOT_Y = PY - SW_BASE_T - 0.0075
SW_REST = 35.0                 # degrees below horizontal (OFF)
LEVER_Z = -0.27
LEVER_PIVOT_Y = PY - 0.019
LEVER_REST = 40.0
LEVER_LEN = 0.074
ARM_X = 0.0385
GX, GZ = -0.25, 0.15           # gauge (moved 3 cm left of the nominal −0.22 to keep clear of the traces)
G_R = 0.031
G_PIVOT_DZ = -0.007
DOOR_T = 0.026
DOOR_Y0 = -D - 0.002           # door inner face when closed
HINGE = (-W / 2 - 0.007, -D - 0.014)
HINGE_Z = (0.30, -0.30)
DOOR_OPEN = -100.0


# ---------------------------------------------------------------- enclosure
def build_case():
    ring = L.mitred_ring("panel_case", W, H, WALL, -D, 0.0, r_out=R_OUT, n_arc=3, bevel=0.004, bev_seg=2)
    left, right, top, bot = ring["l"], ring["r"], ring["t"], ring["b"]
    iw, ih = W / 2 - WALL, H / 2 - WALL
    back = [L.box_mm("back", (-iw, -BACK_T, -ih), (iw, 0.0, ih), mat="M_Steel_Painted", bevel=0.0015)]
    # plate mounting rails behind the plate
    for zz in (-0.30, 0.30):
        back.append(L.box_mm("rail", (-0.31, PY + PT, zz - 0.018), (0.31, -BACK_T, zz + 0.018), mat="M_Steel_Dark",
                             bevel=0.0015))
    back = M.join(back, "panel_case_back")
    # --- top: wall lugs, cable gland with conduit stub, lamp bezels, plate screws
    tp = [top]
    bp = [bot]
    for sx in (-1, 1):
        for sz, lst in ((1, tp), (-1, bp)):
            lug = L.curve_solid("lug", [L.rounded_rect(0.07, 0.056, 0.012, 2)], 0.006, bevel=0.0012,
                                mat="M_Steel_Painted")
            lug.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))     # plate in XZ, thickness along -Y..0
            lug.location = (sx * 0.22, 0.0, sz * (H / 2 + 0.006))
            bolt = L.lathe2("lugbolt", [(0.0085, 0.0), (0.0085, 0.0045), (0.0065, 0.0058), (0.0, 0.0062)], segments=6,
                            mat="M_Steel_Dark", cap_bottom=False)
            L.along(bolt)
            bolt.location = (sx * 0.22, -0.006, sz * (H / 2 + 0.014))
            lst += [lug, bolt]
    gl = L.lathe2("gland", [(0.019, 0.0), (0.019, 0.0055), (0.0165, 0.012), (0.0135, 0.0135), (0.0135, 0.020),
                            (0.0118, 0.021), (0.0118, 0.052), (0.0, 0.052)],
                  segments=10, mat="M_Brass_Aged", band_mats=[None] * 5 + ["M_Steel_Dark"] * 2, cap_bottom=False)
    gl.location = (0.20, -0.105, H / 2)
    tp.append(gl)
    for (lx, lz, _m) in LAMPS:
        bez = L.lathe2("bezel", [(0.0268, -0.0005), (0.0268, 0.0028), (0.0226, 0.0086), (0.0186, 0.0094),
                                 (0.0175, 0.0072)], segments=14, mat="M_Chrome",
                       cap_bottom=False)
        L.along(bez)
        bez.location = (lx, PY, lz)
        tp.append(bez)
    for sx in (-1, 1):
        for sz, lst in ((1, tp), (-1, bp)):
            lst.append(L.screw("pscrew", 0.0045, (sx * 0.282, PY, sz * 0.382), slot_angle=0.5 + sx * 0.7 + sz * 0.2,
                               segs=6))
    top = M.join(tp, "panel_case_t")
    bot = M.join(bp, "panel_case_b")
    # --- left side: cabinet half of the two hinges (knuckles + leaf on the side wall)
    lp = [left]
    hx, hy = HINGE
    for zc in HINGE_Z:
        for upper in (False, True):
            h = 0.028
            if upper:
                prof = [(0.0, 0.0), (0.0078, 0.0), (0.0078, h), (0.0048, h + 0.003), (0.003, h + 0.008), (0.0, h + 0.009)]
                z0 = zc + 0.0205
            else:
                prof = [(0.0, -0.009), (0.003, -0.008), (0.0048, -0.003), (0.0078, 0.0), (0.0078, h), (0.0, h)]
                z0 = zc - 0.0205 - h
            kn = L.lathe2("knuckle", prof, segments=10, mat="M_Brass_Aged")
            kn.location = (hx, hy, z0)
            lp.append(kn)
            lp.append(L.rivet("lrv", 0.0028, (-W / 2 - 0.003, -D + 0.024, z0 + h / 2), normal=(-1, 0, 0),
                              mat="M_Brass_Aged", segs=6))
        lp.append(L.box_mm("leaf", (-W / 2 - 0.003, hy + 0.004, zc - 0.048), (-W / 2 + 0.0002, -D + 0.035, zc + 0.048),
                           mat="M_Brass_Aged", bevel=0.0007))
    left = M.join(lp, "panel_case_l")
    return [left, right, top, bot, back]


def build_plate():
    plate = M.box("panel_plate", (PW, PT, PH), loc=(0, 0, 0), mat="M_Enamel_Cream", bevel=0.0008, segments=1)
    idx = M.add_slot(plate, "M_Decal_PanelDiagram")
    for p in plate.data.polygons:
        if p.normal.y < -0.99:
            p.material_index = idx
    plate.data.transform(Matrix.Translation((0, PT / 2, 0)))       # local y = 0 on the front face
    plate.location = (0, PY, 0)
    return plate


def build_lamps():
    out = []
    for j, (lx, lz, mat) in enumerate(LAMPS):
        jw = L.lathe2(f"lamp_{j}", [(0.0176, 0.0038), (0.0176, 0.0082), (0.0152, 0.0124), (0.0104, 0.0155),
                                    (0.0, 0.0168)], segments=12, mat=mat, cap_bottom=False)
        L.along(jw)
        jw.location = (lx, PY, lz)
        out.append(jw)
    return out


# ---------------------------------------------------------------- switches
def build_switch_bases():
    parts = []
    for x in SWITCH_X:
        base = L.curve_solid("swbase", [L.rounded_rect(0.032, 0.054, 0.0045, 2)], SW_BASE_T, bevel=0.0013,
                             bevel_res=1, mat="M_Bakelite", drop_bottom=True)
        L.to_front(base, y_back=PY, x=x, z=SWITCH_Z)
        nut = L.lathe2("nut", [(0.0082, 0.0), (0.0082, 0.0032), (0.0072, 0.0042), (0.0055, 0.0042), (0.0055, 0.0076),
                               (0.0, 0.0076)], segments=6, mat="M_Chrome", cap_bottom=False, phase=math.pi / 6)
        L.along(nut)
        nut.location = (x, PY - SW_BASE_T, SWITCH_Z)
        parts += [base, nut]
        for dz in (-0.0195, 0.0195):
            parts.append(L.flat_front("swrivet", [L.circle(0.0026, 8)], x, PY - SW_BASE_T - 0.0001, SWITCH_Z + dz,
                                      mat="M_Chrome"))
        # ON / OFF ticks engraved on the base (top = ON)
        parts.append(L.flat_front("on_tick", [L.circle(0.0012, 6)], x, PY - SW_BASE_T - 0.0001, SWITCH_Z + 0.0125,
                                  mat="M_Enamel_Cream"))
    return M.join(parts, "panel_switch_bases")


def build_switch(i):
    x = SWITCH_X[i]
    lev = L.lathe2(f"IA_switch_{i}", [(0.0, -0.0035), (0.0046, -0.0012), (0.0029, 0.0045), (0.0027, 0.021),
                                      (0.0054, 0.0245), (0.0064, 0.0295), (0.0058, 0.0355), (0.0, 0.0388)],
                   segments=8, mat="M_Chrome", band_mats=[None, None, None, "M_Bakelite", "M_Bakelite", "M_Bakelite",
                                                          "M_Bakelite"])
    L.along(lev)                                              # +Z -> -Y (toward the viewer)
    lev.data.transform(Matrix.Rotation(math.radians(SW_REST), 4, "X"))   # rest: down = OFF
    lev.location = (x, SW_PIVOT_Y, SWITCH_Z)
    return lev


# ---------------------------------------------------------------- main breaker
def build_breaker():
    parts = []
    hb = L.curve_solid("housing", [L.rounded_rect(0.064, 0.112, 0.008, 3)], 0.026, bevel=0.003, bevel_res=1,
                       mat="M_Bakelite", drop_bottom=True)
    L.to_front(hb, y_back=PY, x=0.0, z=LEVER_Z)
    parts.append(hb)
    # chrome face plate with a vertical slot and two screws
    fp = L.curve_solid("faceplate", [L.rounded_rect(0.046, 0.094, 0.005, 3), L.rounded_rect(0.012, 0.064, 0.0058, 3)],
                       0.0014, bevel=0.0004, mat="M_Chrome", drop_bottom=True)
    L.to_front(fp, y_back=PY - 0.026, x=0.0, z=LEVER_Z)
    parts.append(fp)
    slot = L.flat_front("slot", [L.rounded_rect(0.012, 0.064, 0.0058, 3)], 0.0, PY - 0.0262, LEVER_Z, mat="M_Rubber")
    parts.append(slot)
    for dz in (-0.039, 0.039):
        parts.append(L.screw("bscrew", 0.003, (0.0, PY - 0.0274, LEVER_Z + dz), mat="M_Chrome", slot_angle=dz * 30,
                             segs=6))
    # side bosses carrying the shaft
    for sx in (-1, 1):
        boss = L.lathe2("boss", [(0.0105, 0.0), (0.0105, 0.0035), (0.0, 0.0035)], segments=12,
                        mat="M_Bakelite", cap_bottom=False)
        boss.data.transform(Matrix.Rotation(sx * math.pi / 2, 4, "Y"))
        boss.location = (sx * 0.032, LEVER_PIVOT_Y, LEVER_Z)
        parts.append(boss)
    return M.join(parts, "panel_breaker")


def lever_xf(obj):
    """Lever pieces are drawn pointing straight at the viewer (-Y) around the pivot; tilt to rest (down)."""
    obj.data.transform(Matrix.Rotation(math.radians(LEVER_REST), 4, "X"))


def build_main_lever():
    parts = []
    shaft = L.lathe2("shaft", [(0.0, -0.0445), (0.0062, -0.0425), (0.0066, -0.040), (0.0042, -0.040), (0.0042, 0.040),
                               (0.0066, 0.040), (0.0062, 0.0425), (0.0, 0.0445)], segments=8, mat="M_Chrome")
    shaft.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    parts.append(shaft)
    for sx in (-1, 1):
        x = sx * ARM_X
        arm = L.curve_solid("arm", [[(-0.0075, 0.0), (0.0075, 0.0), (0.006, LEVER_LEN), (-0.006, LEVER_LEN)]],
                            0.0042, bevel=0.0008, mat="M_Steel_Dark")
        # 2D (u along lever) drawn in XY, thickness along Z -> rotate: u-> -Y, thickness -> X
        arm.data.transform(Matrix.Translation((0, 0, -0.0021)))
        arm.data.transform(Matrix(((0, 0, 1, 0), (0, -1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1))))
        arm.data.transform(Matrix.Translation((x, 0, 0)))
        hub = L.lathe2("arm_hub", [(0.0, -0.0028), (0.0098, -0.0028), (0.0098, 0.0028), (0.0, 0.0028)], segments=10,
                       mat="M_Steel_Dark")
        hub.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        hub.data.transform(Matrix.Translation((x, 0, 0)))
        eye = L.lathe2("eye", [(0.0046, -0.0028), (0.0092, -0.0028), (0.0092, 0.0028), (0.0046, 0.0028),
                               (0.0046, -0.0028)], segments=10, mat="M_Steel_Dark", cap_bottom=False, cap_top=False)
        eye.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        eye.data.transform(Matrix.Translation((x, -LEVER_LEN, 0)))
        parts += [arm, hub, eye]
    for p in parts:
        lever_xf(p)
    lev = M.join(parts, "IA_main_lever")
    lev.location = (0.0, LEVER_PIVOT_Y, LEVER_Z)
    # bakelite grip between the eyes, brass caps outside (hidden until the player installs it)
    grip = L.lathe2("main_handle", [(0.0, -0.0465), (0.0068, -0.0448), (0.0068, -0.041), (0.0040, -0.0405),
                                    (0.0040, -0.0352), (0.0095, -0.0322), (0.0118, -0.016), (0.0118, 0.016),
                                    (0.0095, 0.0322), (0.0040, 0.0352), (0.0040, 0.0405), (0.0068, 0.041),
                                    (0.0068, 0.0448), (0.0, 0.0465)], segments=10, mat="M_Bakelite",
                    band_mats=["M_Brass_Polished"] * 4 + [None] * 5 + ["M_Brass_Polished"] * 4)
    grip.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    grip.data.transform(Matrix.Translation((0, -LEVER_LEN, 0)))
    lever_xf(grip)
    grip.location = (0.0, LEVER_PIVOT_Y, LEVER_Z)
    # origin at the grip centre
    M.refresh()
    c = grip.matrix_world @ (Matrix.Rotation(math.radians(LEVER_REST), 4, "X") @ Vector((0, -LEVER_LEN, 0)))
    M.set_origin(grip, c)
    M.set_parent(grip, lev)
    return lev, grip


# ---------------------------------------------------------------- gauge
def build_gauge():
    parts = []
    body = L.lathe2("gbody", [(G_R, 0.0), (G_R, 0.0125), (G_R - 0.0015, 0.0158), (G_R - 0.005, 0.0168),
                              (G_R - 0.0062, 0.0148), (G_R - 0.0062, 0.0102), (0.0, 0.0102)], segments=24,
                    mat="M_Brass_Aged", band_mats=[None] * 5 + ["M_Enamel_Cream"], cap_bottom=False)
    L.along(body)
    body.location = (GX, PY, GZ)
    parts.append(body)
    fy = PY - 0.0102 - 0.0001          # dial face
    pz = GZ + G_PIVOT_DZ
    for k in range(11):
        a = math.radians(135.0 - 9.0 * k)
        major = k % 5 == 0
        r0, r1 = (0.0148, 0.0208) if major else (0.0168, 0.0208)
        w = 0.0006 if major else 0.00038
        ca, sa = math.cos(a), math.sin(a)
        quad = [(r0 * ca - w * sa, r0 * sa + w * ca), (r0 * ca + w * sa, r0 * sa - w * ca),
                (r1 * ca + w * sa, r1 * sa - w * ca), (r1 * ca - w * sa, r1 * sa + w * ca)]
        parts.append(L.flat_front("gtick", [quad], GX, fy, pz, mat="M_Bakelite"))
    # red band above 220 V
    a0, a1 = math.radians(135.0 - 90.0 * 220 / 250), math.radians(45.0)
    band = L.arc_pts(0.0213, a1, a0, 4) + L.arc_pts(0.0235, a0, a1, 4)
    parts.append(L.flat_front("gred", [band], GX, fy, pz, mat="M_Enamel_Crimson"))
    parts.append(L.label_front("gV", "V", 0.0075, GX, fy, GZ - 0.0105, font=L.FONT_SERIF_B, mat="M_Bakelite"))
    glass = L.flat_front("gglass", [L.circle(G_R - 0.0058, 20)], GX, PY - 0.0147, GZ, mat="M_Glass")
    parts.append(glass)
    gauge = M.join(parts, "panel_gauge")
    # needle (rest: 0 V, up-left at 135°)
    nd = L.flat_shape("gauge_needle", [L.pointer_outline(0.0195, 0.0035, shaft_w=0.0009, head_w=0.0016,
                                                         head_len=0.003, ball_r=0.0016)], mat="M_Steel_Dark")
    nd.data.transform(Matrix.Rotation(math.radians(45.0), 4, "Z"))
    hub = L.lathe2("ghub", [(0.0, 0.0), (0.0019, 0.0), (0.0019, 0.0008), (0.0, 0.0013)], segments=8,
                   mat="M_Brass_Polished", cap_bottom=False)
    hub.data.transform(Matrix.Translation((0, 0, 0.0002)))
    needle = M.join([nd, hub], "gauge_needle")
    L.to_front(needle, y_back=fy - 0.0012, x=GX, z=pz)
    M.set_origin(needle, (GX, fy - 0.0012, pz))
    return gauge, needle


# ---------------------------------------------------------------- door (static, open ~100°)
def build_door():
    parts = []
    y_in, y_out = DOOR_Y0, DOOR_Y0 - DOOR_T
    slab = L.curve_solid("dslab", [L.rounded_rect(W, H, R_OUT, 3)], DOOR_T, bevel=0.0045, bevel_res=1,
                         mat="M_Steel_Painted")
    L.to_front(slab, y_back=y_in)
    parts.append(slab)
    # inside: rubber gasket, schedule pocket with a folded sheet, enamel label
    gk = L.curve_solid("gasket", L.outline_ring(W - 0.07, H - 0.07, 0.012, 0.012, 2), 0.004, bevel=0.0012,
                       mat="M_Rubber")
    L.to_front(gk, y_back=y_in + 0.004)
    parts.append(gk)
    pk = L.curve_solid("pocket", [L.rounded_rect(0.21, 0.15, 0.006, 2)], 0.012, bevel=0.0015, mat="M_Steel_Painted")
    L.to_front(pk, y_back=y_in + 0.012, x=0.03, z=-0.17)
    paper = L.plane("sheet", 0.17, 0.09, mat="M_Paper")
    paper.data.transform(Matrix.Rotation(math.radians(4), 4, "Y"))
    paper.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
    paper.location = (0.025, y_in + 0.006, -0.105)
    M.apply_transform(paper)
    parts += [pk, paper]
    lab = L.curve_solid("dlabel", [L.rounded_rect(0.17, 0.05, 0.006, 3)], 0.0015, bevel=0.0005, mat="M_Enamel_Cream")
    L.to_front(lab, y_back=y_in + 0.0015, x=0.0, z=0.30)
    parts.append(lab)
    for txt, sz, zz, fnt in (("PANEL  7", 0.019, 0.30, L.FONT_SERIF_B),):
        t = L.label_front("dtxt", txt, sz, 0.0, 0.0, 0.0, font=fnt, mat="M_Bakelite")
        t.data.transform(t.matrix_basis)
        t.matrix_basis = Matrix.Identity(4)
        t.data.transform(Matrix.Rotation(math.pi, 4, "Z"))            # face +Y (the door's inside)
        t.data.transform(Matrix.Translation((0.0, y_in + 0.0016, zz)))
        parts.append(t)
    for sx in (-1, 1):
        rv = L.flat_shape("dlrv", [L.circle(0.0022, 8)], mat="M_Brass_Aged")
        L.along(rv, (0, 0, 1), (0, 1, 0))
        rv.location = (sx * 0.074, y_in + 0.0016, 0.30)
        parts.append(rv)
    # outside: quarter-turn latch, danger plaque
    boss = L.lathe2("latch", [(0.017, 0.0), (0.017, 0.004), (0.0105, 0.0075), (0.0075, 0.0085),
                              (0.0075, 0.018), (0.0, 0.0185)], segments=12, mat="M_Chrome", cap_bottom=False)
    L.along(boss)
    boss.location = (0.30, y_out, 0.0)
    tbar = M.box("tbar", (0.012, 0.010, 0.056), loc=(0.30, y_out - 0.021, 0.0), mat="M_Chrome", bevel=0.004, segments=2)
    M.apply_transform(tbar)
    parts += [boss, tbar]
    tri = [(0.0, 0.052), (-0.06, -0.052), (0.06, -0.052)]
    pl = L.curve_solid("danger", [tri], 0.0015, bevel=0.0005, mat="M_Enamel_Cream")
    L.to_front(pl, y_back=y_out, x=0.0, z=0.22)
    bolt = [(0.006, 0.03), (-0.012, -0.002), (-0.001, -0.002), (-0.008, -0.034), (0.013, 0.006), (0.002, 0.006)]
    parts += [pl, L.flat_front("bolt", [bolt], 0.0, y_out - 0.0016, 0.21, mat="M_Enamel_Crimson"),
              L.flat_front("dborder", [tri, [(0.0, 0.040), (-0.049, -0.045), (0.049, -0.045)]], 0.0, y_out - 0.0016,
                           0.22, mat="M_Bakelite")]
    # door half of the hinges: knuckle + leaf on the outside face
    hx, hy = HINGE
    for zc in HINGE_Z:
        kn = L.lathe2("dknuckle", [(0.0078, 0.0), (0.0078, 0.039)], segments=10, mat="M_Brass_Aged", cap_bottom=False,
                      cap_top=False)
        kn.location = (hx, hy, zc - 0.0195)
        leaf = L.box_mm("dleaf", (hx + 0.004, y_out - 0.003, zc - 0.018), (-W / 2 + 0.06, y_out + 0.0002, zc + 0.018),
                        mat="M_Brass_Aged", bevel=0.0008)
        parts += [kn, leaf]
        for dx in (0.03, 0.05):
            parts.append(L.rivet("dhrv", 0.0026, (-W / 2 + dx, y_out - 0.003, zc), mat="M_Brass_Aged", segs=6))
    door = M.join(parts, "panel_door")
    M.set_origin(door, (hx, hy, 0.0))
    door.rotation_euler = (0, 0, math.radians(DOOR_OPEN))
    return door


def build():
    build_case()
    build_plate()
    build_lamps()
    build_switch_bases()
    for i in range(5):
        build_switch(i)
    build_breaker()
    build_main_lever()
    build_gauge()
    build_door()


def decals():
    plate = M.bpy.data.objects["panel_plate"]
    L.planar_uv_rect(plate, -PW / 2, PW / 2, -PH / 2, PH / 2, axis="Y", material_prefix="M_Decal_")
    for j in range(4):
        L.faceted(M.bpy.data.objects[f"lamp_{j}"], 5.0)


def shot(name, cam, target, lens, samples=32, pose=None):
    objs = M.bpy.data.objects
    if pose:
        for i in range(5):
            objs[f"IA_switch_{i}"].rotation_euler = (math.radians(-70.0 * pose[0][i]), 0, 0)
        objs["IA_main_lever"].rotation_euler = (math.radians(-80.0 * pose[1]), 0, 0)
        objs["gauge_needle"].rotation_euler = (0, math.radians(79.0 * pose[1]), 0)   # Blender −Y = Godot +Z
    L.qa_wall(0.0, 0.0, w=2.4, h=2.0)
    L.qa_render(name, cam, target, lens=lens, floor_z=None, samples=samples)
    for i in range(5):
        objs[f"IA_switch_{i}"].rotation_euler = (0, 0, 0)
    objs["IA_main_lever"].rotation_euler = (0, 0, 0)
    objs["gauge_needle"].rotation_euler = (0, 0, 0)


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("panel7", decals=[decals])
    if L.want_render():
        shot("panel7", (0.95, -1.35, 0.35), (0.0, -0.08, 0.0), 40)
        shot("panel7_2", (0.0, -1.35, 0.0), (0.0, 0.0, 0.0), 50)
        shot("panel7_3", (0.30, -0.55, -0.05), (0.0, -0.04, -0.17), 45, pose=((1, 1, 1, 0, 0), 1))


main()
