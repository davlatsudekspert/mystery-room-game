"""tube_station.glb — the pneumatic-post station of Archive B (east wall), puzzles P3/P4.

A cream-enamel steel counter cabinet (0.90 x 0.88 x 0.46) with a walnut top, an upper control panel to
y = 2.0 and, in front of it, the brass-and-glass riser of the send line up to tube_p0 plus the return
riser beside it (ending at tube_q0). On the counter: the brass receiving box (glass-fronted door) with the
send-port chamber standing on it, and a walnut tray of blank request cards. On the panel: the 6-position
destination selector inside its symbol ring (decal M_Decal_DestSymbols), the pressure jewel lamp with a
gauge pictogram plate, and the big send lever on the right.

Model space (Godot): front +Z, origin on the wall plane at floor level, x = 0 = the send riser's axis.
Placement: (5.0, 0, -1.4), yaw -90 (local +X = world +Z). Overall 0.94 w x 2.35 h x 0.475 d.
Parts (origin at the pivot, identity rotation at rest):
  IA_send_port      send chamber on the riser (axis x 0, z 0.20), canister seat at y 1.135
    port_flap       curved door with a sight glass; hinge on its bottom edge (0, 1.112, 0.266);
                    open = +80 deg about local +X (top falls toward the player)
    canister_mount  (0, 1.245, 0.20): the canister stands there (long axis +Y), identity
  IA_receive_tray   brass receiving box x [-0.20, 0.20], y [0.885, 1.075], z [0.10, 0.43]
    tray_door       glass-fronted door, hinge on its bottom edge (0, 0.897, 0.440); open = +75 deg about +X
    return_mount    canister lying along local X (cap toward +X) on the file
    file_mount      file_folder lying flat, turned 93 deg (its top edge toward -X)
    key_mount       locker_key lying flat on the file
  IA_dest_dial      selector knob at (-0.22, 1.55, 0.0835); -60 deg x d about +Z; pointer at 12 o'clock
  dest_ring         0.24 x 0.24 decal quad centred on the knob axis (UV 0..1, u right, v up),
                    M_Decal_DestSymbols: symbols at 12, 2, 4, 6, 8, 10 o'clock for d = 0..5
  lamp_status       jewel lens only (M_Lamp_G) at (-0.22, 1.735, 0.09); the code sets its emission colour
  IA_send_lever     big brass lever, pivot (0.31, 1.25, 0.125); pull = +55 deg about +X
    send_lever_arm  child: the lower arm + pivot boss (so the IA mesh stays <= 0.15 m: box collider)
  IA_card_tray      walnut tray at (-0.315, 0.88, 0.33)
    tray_cards      static stack of blank request cards (top face M_Decal_RequestCard)
    tray_card_mount on top of the stack
    blender -b --factory-startup -P tools/blender/models/tube_station.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices1 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "tube_station"
BUDGET = 9000
CW, CH, CD = 0.90, 0.88, 0.46          # counter
TOP_T = 0.028
PANEL = (-0.40, 0.40, 0.88, 2.00)      # upper panel x0, x1, y0, y1
PZ = 0.080                             # panel front face
RZ = 0.20                              # riser axis z
RX_RET = 0.14                          # return riser x
R_OUT, R_IN = 0.045, 0.040
BOX = (-0.20, 0.20, 0.885, 1.075, 0.10, 0.43)     # receiving box x0, x1, y0, y1, z0, z1
FLOOR_Y = 0.905                        # felt floor inside the box
DOOR_HINGE = (0.0, 0.897, 0.440)
PORT_Y0, PORT_Y1 = 1.075, 1.430        # send chamber (on the box) bottom / top
SEAT_Y = 1.135
CH_RO, CH_RI = 0.062, 0.050            # chamber outer / inner radius
OPEN = (1.112, 1.388, 42.0)            # chamber front opening y0, y1, half-angle (deg)
FLAP_HINGE = (0.0, 1.112, RZ + 0.066)
DIAL = (-0.22, 1.55)
RING_HW = 0.12
LAMP = (-0.22, 1.735)
LEVER_PIVOT = (0.31, 1.25, 0.125)
TRAY = (-0.315, 0.33)                  # card tray centre x, z (on the counter top y = CH)


def godot_band(x0, x1, y0, y1, z0, z1, mat, bevel=0.003, seg=1):
    return C.sm(C.gbox("b", (x0, y0, z0), (x1, y1, z1), mat=mat, bevel=bevel, seg=seg), 30.0)


# ---------------------------------------------------------------- counter + panel (static body)
def build_body():
    parts = []
    # plinth (recessed kick) and carcass with rounded front corners
    parts.append(godot_band(-0.43, 0.43, 0.0, 0.085, 0.0, 0.415, "M_Steel_Dark", bevel=0.002))
    plan = C.gframe((0.0, 0.085, 0.0), (1, 0, 0), (0, 0, -1))      # u = x, v = -z, out = +y
    car = C.solid_g("carcass", [L.rrect4(CW, 0.44, radii=(0.03, 0.0, 0.0, 0.03), n=4, cy=-0.22)],
                    CH - TOP_T - 0.085, plan, bevel=0.004, bevel_res=1, mat="M_Steel_Cream")
    parts.append(C.sm(car, 40.0))
    top = C.solid_g("top", [L.rrect4(CW + 0.04, 0.475, radii=(0.035, 0.0, 0.0, 0.035), n=4, cy=-0.2375)],
                    TOP_T, C.gframe((0.0, CH - TOP_T, 0.0), (1, 0, 0), (0, 0, -1)), bevel=0.006, bevel_res=2,
                    mat="M_Wood_Walnut")
    parts.append(C.sm(top, 40.0))
    # front: two doors (gaps), chrome pulls, a brass station plate, louvres at the foot
    ff = C.front_frame(0.0, 0.0, 0.4401)
    for dx in (-0.215, 0.215):
        parts.append(C.shape_g("door_gap", L.outline_ring(0.405, 0.66, 0.012, 0.0035, 3), ff, u=dx, v=0.455,
                               mat="M_Steel_Dark"))
    for dx in (-0.035, 0.035):
        pull = C.gtube("pull", [(dx, 0.56, 0.441), (dx, 0.56, 0.462), (dx, 0.70, 0.462), (dx, 0.70, 0.441)], 0.0055,
                       sides=6, mat="M_Chrome", fillet=0.010, fillet_segs=2)
        parts.append(pull)
    kh = C.shape_g("keyhole", [L.circle(0.0045, 10, cy=0.004),
                               [(-0.002, -0.006), (0.002, -0.006), (0.0015, -0.0002), (-0.0015, -0.0002)]], ff,
                   u=0.06, v=0.63, lift=0.0004, mat="M_Steel_Dark")
    kp = C.solid_g("keyplate", [L.rounded_rect(0.020, 0.034, 0.004, 2)], 0.0015, ff, u=0.06, v=0.63,
                   bevel=0.0004, mat="M_Brass_Aged")
    kh.data.transform(Matrix.Translation(C.GV((0, 0, 0.0015))))
    parts += [kp, kh]
    sp = C.solid_g("stplate", [L.rounded_rect(0.20, 0.040, 0.006, 3)], 0.002, ff, u=0.0, v=0.815, bevel=0.0006,
                   mat="M_Brass_Polished")
    parts.append(sp)
    parts.append(C.text_g("stplate_txt", "STATION  3", 0.017, ff, u=0.0, v=0.815, lift=0.0021,
                          font=C.FONT_COND_B, mat="M_Lacquer_Black", res=1))
    for sx in (-1, 1):
        parts.append(C.rivet_g("strivet", 0.0028, (sx * 0.088, 0.815, 0.4421), segs=6))
    for k in range(5):
        parts.append(C.shape_g("louvre", [L.rounded_rect(0.16, 0.007, 0.0034, 3)], ff, u=-0.215, v=0.16 + 0.016 * k,
                               mat="M_Steel_Dark"))
        parts.append(C.shape_g("louvre", [L.rounded_rect(0.16, 0.007, 0.0034, 3)], ff, u=0.215, v=0.16 + 0.016 * k,
                               mat="M_Steel_Dark"))
    # upper panel: cream steel with rounded top corners, brass inlay border, screws
    x0, x1, y0, y1 = PANEL
    pf = C.front_frame(0.0, 0.0, 0.0)
    pan = C.solid_g("panel", [L.rrect4(x1 - x0, y1 - y0, radii=(0.0, 0.03, 0.03, 0.0), n=4, cx=(x0 + x1) / 2,
                                       cy=(y0 + y1) / 2)], PZ, pf, bevel=0.006, bevel_res=2, mat="M_Steel_Cream")
    parts.append(C.sm(pan, 40.0))
    pfront = C.front_frame((x0 + x1) / 2, (y0 + y1) / 2 + 0.01, PZ)
    parts.append(C.shape_g("ptrim", L.outline_ring(x1 - x0 - 0.04, y1 - y0 - 0.06, 0.016, 0.0026, 4), pfront,
                           lift=0.0002, mat="M_Brass_Aged"))
    for (sx, yy) in ((-1, 1.95), (1, 1.95), (-1, 0.95), (1, 0.95)):
        parts.append(C.screw_g("pscrew", 0.005, (sx * 0.365, yy, PZ), mat="M_Brass_Aged", slot=0.5 + sx * 0.3,
                               segs=8))
    # destination escutcheon (brass disc behind the decal ring)
    esc = C.revolve_g("escutcheon", [(RING_HW + 0.005, 0.0), (RING_HW + 0.005, 0.0022), (RING_HW + 0.002, 0.0034),
                                     (0.0, 0.0034)], (0, 0, 1), (DIAL[0], DIAL[1], PZ), segments=32,
                      mat="M_Brass_Aged", cap_bottom=False)
    parts.append(C.sm(esc, 35.0))
    # lamp bezel (chrome) + gauge pictogram plate
    bez = C.revolve_g("lampbezel", [(0.027, 0.0), (0.027, 0.006), (0.024, 0.010), (0.0185, 0.0105),
                                    (0.0175, 0.006)], (0, 0, 1), (LAMP[0], LAMP[1], PZ), segments=16,
                      mat="M_Chrome", cap_bottom=False, cap_top=False)
    parts.append(C.sm(bez, 40.0))
    lf = C.front_frame(LAMP[0] - 0.088, LAMP[1], PZ)
    parts.append(C.solid_g("pictoplate", [L.rounded_rect(0.050, 0.044, 0.006, 3)], 0.002, lf, bevel=0.0005,
                           mat="M_Brass_Polished"))
    pic = [C.arc_band(0.0135, 0.0160, -30.0, 210.0, 12)]
    for a in (210.0, 150.0, 90.0, 30.0, -30.0):
        pic.append(C.radial_tick(0.0095, 0.0130, a, 0.0018))
    pic.append(C.strip((0.0, 0.0), (0.0095 * math.cos(math.radians(60)), 0.0095 * math.sin(math.radians(60))),
                       0.0022))
    pic.append(L.circle(0.0028, 8))
    parts.append(C.shape_g("picto", pic, lf, v=-0.003, lift=0.0021, mat="M_Lacquer_Black"))
    # send-lever quadrant: a compact notched brass sector beside the lever (outboard, +X), on a standoff
    lx, ly, lz = LEVER_PIVOT
    qf = C.gframe((lx + 0.026, ly, lz), (0, 0, 1), (0, 1, 0))      # u = +z, v = +y, out of the face = -x
    rq = 0.105
    quad = [(-0.030, -0.028), (0.028, -0.028)] + \
        [(rq * math.cos(math.radians(a2)), rq * math.sin(math.radians(a2))) for a2 in range(20, 111, 10)] + \
        [(-0.030, 0.050)]
    qplate = C.solid_g("quadrant", [quad, L.circle(0.006, 8)], 0.006, qf, bevel=0.0012, mat="M_Brass_Polished")
    parts.append(C.sm(qplate, 35.0))
    for a2 in (90.0, 35.0):               # rest and pulled notches on the rim
        parts.append(C.shape_g("qnotch", [C.radial_tick(0.080, 0.101, a2, 0.0045)], qf, lift=0.0062,
                               mat="M_Lacquer_Black"))
    for (u, v) in ((-0.020, -0.018), (0.018, -0.018)):
        parts.append(C.rivet_g("qrivet", 0.0028, (lx + 0.020, ly + v, lz + u), normal_g=(-1, 0, 0), segs=6))
    parts.append(godot_band(lx + 0.024, lx + 0.040, ly - 0.040, ly + 0.040, PZ - 0.002, lz + 0.012, "M_Brass_Aged"))
    # riser collars, brackets and the little pressure gauge
    for (x, y0c, y1c, ro) in ((0.0, 1.425, 1.452, 0.054), (0.0, 1.84, 1.868, 0.051), (0.0, 2.288, 2.35, 0.056),
                              (RX_RET, 1.075, 1.105, 0.054), (RX_RET, 1.84, 1.868, 0.051),
                              (RX_RET, 2.288, 2.35, 0.056)):
        h = y1c - y0c
        col = C.revolve_g("collar", [(ro - 0.0025, 0.0), (ro, 0.0025), (ro, h - 0.0025), (ro - 0.0025, h),
                                     (R_OUT, h)], (0, 1, 0), (x, y0c, RZ), segments=16,
                          mat="M_Brass_Polished", cap_bottom=False, cap_top=False)
        parts.append(C.sm(col, 40.0))
    # twin clamp bracket at 1.854 (to the panel) and 2.20 (to the wall above the panel)
    for (y, zb) in ((1.854, PZ), (2.20, 0.0)):
        parts.append(godot_band(-0.02, RX_RET + 0.02, y - 0.009, y + 0.009, RZ - 0.058, RZ - 0.044, "M_Steel_Dark",
                                bevel=0.002))
        parts.append(godot_band(RX_RET / 2 - 0.012, RX_RET / 2 + 0.012, y - 0.008, y + 0.008, zb, RZ - 0.050,
                                "M_Steel_Dark", bevel=0.002))
        parts.append(godot_band(RX_RET / 2 - 0.035, RX_RET / 2 + 0.035, y - 0.035, y + 0.035, zb, zb + 0.006,
                                "M_Steel_Dark", bevel=0.002))
        for x in (0.0, RX_RET):
            ring = M.torus("clamp", R_OUT + 0.004, 0.0035, major_seg=12, minor_seg=3, mat="M_Steel_Dark")
            ring.data.transform(Matrix.Translation(C.G(x, y, RZ)))
            parts.append(C.sm(ring, 70.0))
    if True:
        gy = 1.625
        band = C.revolve_g("gband", [(R_OUT + 0.006, 0.0), (R_OUT + 0.006, 0.026), (R_OUT, 0.026), (R_OUT, 0.0)],
                           (0, 1, 0), (0.0, gy - 0.013, RZ), segments=20, mat="M_Brass_Polished",
                           cap_bottom=False, cap_top=False)
        stub = C.revolve_g("gstub", [(0.009, 0.0), (0.009, 0.024)], (0, 0, 1), (0.0, gy, RZ + R_OUT), segments=8,
                           mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
        gcase = C.revolve_g("gcase", [(0.030, 0.0), (0.031, 0.004), (0.031, 0.016), (0.028, 0.020), (0.026, 0.020),
                                      (0.026, 0.012)], (0, 0, 1), (0.0, gy, RZ + R_OUT + 0.024), segments=16,
                            mat="M_Brass_Polished", cap_bottom=True, cap_top=False)
        gf = C.front_frame(0.0, gy, RZ + R_OUT + 0.024 + 0.012)
        gface = C.shape_g("gface", [L.circle(0.0262, 20)], gf, mat="M_Enamel_Cream")
        gt = []
        for k in range(9):
            a = 225.0 - 33.75 * k
            gt.append(C.radial_tick(0.019, 0.0235, a, 0.0012 if k % 2 else 0.0018))
        gticks = C.shape_g("gticks", gt + [C.arc_band(0.0232, 0.0240, -45.5, 225.5, 14)], gf, lift=0.0002,
                           mat="M_Lacquer_Black")
        gnd = L.flat_shape("gneedle", [L.pointer_outline(0.020, 0.005, shaft_w=0.0012, head_w=0.0024, head_len=0.004,
                                                          ball_r=0.0022)], mat="M_Enamel_Crimson")
        gnd.data.transform(Matrix.Rotation(math.radians(135.0), 4, "Z"))
        gnd.data.transform(Matrix.Translation((0, 0, 0.0006)))
        gnd.data.transform(gf)
        gglass = C.shape_g("gglass", [L.circle(0.0265, 20)], C.front_frame(0.0, gy, RZ + R_OUT + 0.024 + 0.0175),
                           mat="M_Glass")
        parts += [C.sm(band, 40.0), C.sm(stub, 60.0), C.sm(gcase, 40.0), gface, gticks, gnd, gglass]
    # cream enamel operating plate on the panel's right: 1 canister into the port, 2 set the dial, 3 pull
    of = C.front_frame(0.25, 1.735, PZ)
    parts.append(C.solid_g("opplate", [L.rounded_rect(0.170, 0.150, 0.010, 3)], 0.002, of, bevel=0.0006,
                           mat="M_Enamel_Cream"))
    icons = []
    for k in range(3):
        v = 0.048 - 0.048 * k
        icons.append(C.text_g("opnum", str(k + 1), 0.022, of, u=-0.062, v=v, lift=0.0021, font=C.FONT_SANS_B,
                              mat="M_Lacquer_Black", res=1))
    ink = []
    # 1: canister dropping into a port (rounded cylinder + down arrow)
    ink.append(L.rounded_rect(0.012, 0.030, 0.005, 3, cx=-0.012, cy=0.048))
    ink.append([(0.008, 0.058), (0.014, 0.058), (0.014, 0.046), (0.020, 0.046), (0.011, 0.036), (0.002, 0.046),
                (0.008, 0.046)])
    ink += [L.rounded_rect(0.036, 0.004, 0.001, 1, cx=0.003, cy=0.030)]
    # 2: dial (ring + pointer)
    ink += [C.arc_band(0.0105, 0.0135, 0.0, 359.0, 16)]
    ink = [p for p in ink]
    dial_ring = [(x - 0.004, y) for (x, y) in C.arc_band(0.0105, 0.0135, 0.0, 359.0, 16)]
    ink[-1] = dial_ring
    ink.append([(-0.0055, -0.0015), (-0.0025, -0.0015), (0.0035, 0.0080), (0.0005, 0.0080)])
    ink.append([(0.016, 0.010), (0.024, 0.010), (0.020, 0.016)])
    # 3: lever pulled toward the viewer (rod + ball + curved arrow)
    ink.append(C.strip((-0.012, -0.060), (-0.002, -0.036), 0.004))
    ink.append(L.circle(0.0045, 10, cx=-0.001, cy=-0.034))
    ink.append(C.arc_band(0.019, 0.0225, 70.0, 140.0, 6))
    ink.append([(0.0050, -0.0400), (0.0145, -0.0405), (0.0085, -0.0480)])
    shifted = []
    for loop in ink:
        shifted.append([(x + 0.012, y) for (x, y) in loop])
    parts.append(C.shape_g("opicons", shifted[:3], of, lift=0.0021, mat="M_Lacquer_Black"))
    parts.append(C.shape_g("opicons2", shifted[3:6], of, lift=0.0021, mat="M_Lacquer_Black"))
    parts.append(C.shape_g("opicons3", shifted[6:], of, lift=0.0021, mat="M_Lacquer_Black"))
    parts += icons
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        parts.append(C.rivet_g("oprivet", 0.0025, (0.25 + sx * 0.075, 1.735 + sy * 0.065, PZ + 0.002), segs=6))
    return C.part("station_body", parts, (0.0, 0.0, 0.0))


def build_risers():
    out = []
    for (x, y0, y1) in ((0.0, 1.452, 2.288), (RX_RET, 1.105, 2.288)):
        t = C.revolve_g("riser", [(R_OUT, 0.0), (R_OUT, y1 - y0), (R_IN, y1 - y0), (R_IN, 0.0), (R_OUT, 0.0)],
                        (0, 1, 0), (x, y0, RZ), segments=18, mat="M_Glass", cap_bottom=False, cap_top=False)
        out.append(C.sm(t, 40.0))
    return C.part("riser_glass", out, (0.0, 0.0, 0.0))


# ---------------------------------------------------------------- send port
def build_port():
    y0, y1 = PORT_Y0, PORT_Y1
    h = y1 - y0
    # closed shell profile: base flange, chamber wall, shoulder up to the riser collar; dark inside
    prof = [(0.077, 0.0), (0.077, 0.011), (CH_RO, 0.017), (CH_RO, h - 0.040), (0.052, h - 0.016),
            (0.052, h), (R_IN, h), (R_IN, h - 0.040), (CH_RI, h - 0.045), (CH_RI, 0.035), (0.0, 0.035)]
    bands = [None] * 7 + ["M_Steel_Dark", "M_Steel_Dark", "M_Steel_Dark"]
    shell = C.revolve_g("chamber", prof, (0, 1, 0), (0.0, y0, RZ), segments=24, mat="M_Brass_Polished",
                        cap_bottom=True, cap_top=False, band_mats=bands)
    # front opening for the flap
    oy0, oy1, half = OPEN
    w = 2 * CH_RO * math.sin(math.radians(half))
    cut = C.gbox("cut", (-w / 2, oy0, RZ + CH_RO * math.cos(math.radians(half)) - 0.03),
                 (w / 2, oy1, RZ + CH_RO + 0.02), mat="M_Steel_Dark", bevel=0.0)
    M.boolean(shell, cut)
    C.sm(shell, 40.0)
    parts = [shell]
    # canister seat: rubber buffer on a brass disc
    seat = C.revolve_g("seat", [(0.046, 0.0), (0.046, 0.006), (0.040, 0.009), (0.040, 0.018), (0.0, 0.018)],
                       (0, 1, 0), (0.0, SEAT_Y - 0.018, RZ), segments=16, mat="M_Rubber", cap_bottom=False,
                       band_mats=[None, None, None, None])
    parts.append(C.sm(seat, 40.0))
    # opening lip (brass frame around the cut) and two hinge knuckles at the bottom edge
    for sx in (-1, 1):
        kn = C.revolve_g("knuckle", [(0.0045, 0.0), (0.0045, 0.014), (0.0, 0.014)], (1, 0, 0),
                         (sx * 0.020 - 0.007, FLAP_HINGE[1], FLAP_HINGE[2]), segments=8, mat="M_Brass_Aged",
                         cap_bottom=True)
        parts.append(C.sm(kn, 50.0))
    # engraved "send" arrow plate on the chamber shoulder (pointing up)
    af = C.front_frame(0.0, 1.405, RZ + 0.0605)
    parts.append(C.shape_g("uparrow", [[(-0.010, -0.006), (0.010, -0.006), (0.0, 0.008)]], af, lift=0.0002,
                           mat="M_Lacquer_Black"))
    port = C.part("IA_send_port", parts, (0.0, SEAT_Y, RZ))

    # port flap: curved shell segment with a sight-glass slot and a knurled latch knob at the top
    r0, r1 = CH_RO + 0.0008, CH_RO + 0.0040
    fy0, fy1 = oy0 + 0.001, oy1 - 0.001
    half_f = half + 2.0
    win_a, wy0, wy1 = 15.0, fy0 + 0.040, fy1 - 0.050
    plate = curved_window_panel("flap_plate", r0, r1, half_f, fy0, fy1, win_a, wy0, wy1, "M_Brass_Polished")
    glass = curved_window_panel("flap_glass", r0 + 0.0012, r0 + 0.0013, win_a + 1.0, wy0 - 0.003, wy1 + 0.003,
                                0.0, 0.0, 0.0, "M_Glass", n_side=0, n_win=4)
    flap_objs = [plate, glass]
    knob = C.revolve_g("flapknob", [(0.0075, 0.0), (0.0075, 0.010, "k"), (0.0060, 0.013), (0.0, 0.0135)], (0, 0, 1),
                       (0.0, fy1 - 0.018, RZ + r1), segments=12, mat="M_Brass_Polished", knurl=0.0006,
                       cap_bottom=False)
    leaf = C.gbox("flapleaf", (-0.028, fy0 - 0.004, FLAP_HINGE[2] - 0.003), (0.028, fy0 + 0.010, FLAP_HINGE[2] + 0.0015),
                  mat="M_Brass_Aged", bevel=0.0006)
    kn = C.revolve_g("flapknuckle", [(0.0042, 0.0), (0.0042, 0.024), (0.0, 0.024)], (1, 0, 0),
                     (-0.012, FLAP_HINGE[1], FLAP_HINGE[2]), segments=8, mat="M_Brass_Aged", cap_bottom=True)
    for o in flap_objs:
        C.sm(o, 40.0)
    flap = C.part("port_flap", flap_objs + [C.sm(knob, 40.0), C.sm(leaf, 30.0), C.sm(kn, 50.0)], FLAP_HINGE)
    C.parent(flap, port)
    cm = C.mount("canister_mount", (0.0, SEAT_Y + 0.110, RZ), par=port)
    return port, flap, cm


def curved_window_panel(name, r0, r1, a_half, y0, y1, win_a, wy0, wy1, mat, n_side=3, n_win=4):
    """Closed curved shell (cylinder segment around the chamber axis, centred on +Z) between radii r0..r1,
    angles -a_half..a_half (deg), heights y0..y1, with a rectangular window (|a| < win_a, wy0 < y < wy1).
    win_a = 0 -> no window (then only n_win columns)."""
    if win_a > 0:
        angs = [(-a_half + (a_half - win_a) * i / n_side) for i in range(n_side)] + \
               [(-win_a + 2 * win_a * i / n_win) for i in range(n_win)] + \
               [(win_a + (a_half - win_a) * i / n_side) for i in range(n_side + 1)]
        ys = [y0, wy0, wy1, y1]
    else:
        angs = [(-a_half + 2 * a_half * i / n_win) for i in range(n_win + 1)]
        ys = [y0, y1]
    na, ny = len(angs), len(ys)

    def hole(i, j):
        if win_a <= 0:
            return False
        ac = (angs[i] + angs[i + 1]) / 2
        yc = (ys[j] + ys[j + 1]) / 2
        return abs(ac) < win_a and wy0 < yc < wy1
    bm = bmesh.new()
    V = {}
    for side, r in (("o", r1), ("i", r0)):
        for i, a in enumerate(angs):
            for j, y in enumerate(ys):
                ar = math.radians(a)
                V[(side, i, j)] = bm.verts.new(C.G(r * math.sin(ar), y, RZ + r * math.cos(ar)))
    cells = [(i, j) for i in range(na - 1) for j in range(ny - 1) if not hole(i, j)]
    for (i, j) in cells:
        o = [V[("o", i, j)], V[("o", i + 1, j)], V[("o", i + 1, j + 1)], V[("o", i, j + 1)]]
        bm.faces.new(o)
        bm.faces.new([V[("i", i, j + 1)], V[("i", i + 1, j + 1)], V[("i", i + 1, j)], V[("i", i, j)]])
    # boundary edges of the cell set -> side walls
    edges = {}
    for (i, j) in cells:
        for e in (((i, j), (i + 1, j)), ((i + 1, j), (i + 1, j + 1)), ((i + 1, j + 1), (i, j + 1)), ((i, j + 1), (i, j))):
            key = frozenset(e)
            edges[key] = None if key in edges else e
    for key, e in edges.items():
        if e is None:
            continue
        (a0, b0) = e
        bm.faces.new([V[("o", b0[0], b0[1])], V[("o", a0[0], a0[1])], V[("i", a0[0], a0[1])], V[("i", b0[0], b0[1])]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = M.bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = M.bpy.data.objects.new(name, me)
    M.bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, mat)
    return obj


def _subdivide_x(obj, step):
    """Cut the (flat, XY-drawn) mesh along vertical lines every `step` so it can be bent."""
    xs = [v.co.x for v in obj.data.vertices]
    x0, x1 = min(xs), max(xs)
    k = int((x1 - x0) / step)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for i in range(1, k + 1):
        x = x0 + i * (x1 - x0) / (k + 1)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    bm.to_mesh(obj.data)
    bm.free()


def _bend(obj, r_base, fy0, fy1):
    """Unrolled flap (x = arc length at r_base.. , y up from the centre, z = outward thickness) -> wrapped
    around the chamber axis (Godot x 0, z RZ), front centred on +Z, y mapped to [fy0, fy1]."""
    cy = (fy0 + fy1) / 2
    for v in obj.data.vertices:
        s, yy, zz = v.co.x, v.co.y, v.co.z
        r = r_base + zz
        a = s / r_base
        gx, gz = r * math.sin(a), RZ + r * math.cos(a)
        v.co = C.G(gx, cy + yy, gz)
    obj.data.update()


# ---------------------------------------------------------------- receiving box
def build_tray():
    x0, x1, y0, y1, z0, z1 = BOX
    t = 0.020
    parts = [
        godot_band(x0, x1, y0, FLOOR_Y, z0, z1, "M_Brass_Aged", bevel=0.003),            # bottom
        godot_band(x0, x1, y1 - t, y1, z0, z1, "M_Brass_Aged", bevel=0.003),             # top
        godot_band(x0, x0 + 0.025, FLOOR_Y - 0.002, y1 - t + 0.002, z0, z1, "M_Brass_Aged", bevel=0.002),
        godot_band(x1 - 0.025, x1, FLOOR_Y - 0.002, y1 - t + 0.002, z0, z1, "M_Brass_Aged", bevel=0.002),
        godot_band(x0 + 0.02, x1 - 0.02, FLOOR_Y - 0.002, y1 - t + 0.002, z0, z0 + 0.012, "M_Brass_Aged", bevel=0.0),
    ]
    felt = C.shape_g("felt", [L.rounded_rect(x1 - x0 - 0.05, z1 - z0 - 0.012 - 0.004, 0.004, 2)],
                     C.gframe((0.0, FLOOR_Y + 0.0002, (z0 + 0.012 + z1) / 2), (1, 0, 0), (0, 0, -1)),
                     mat="M_Felt")
    parts.append(felt)
    # rolled top edge bead along the front and a small brass label with a down arrow
    bead = C.revolve_g("bead", [(0.006, 0.0), (0.006, x1 - x0 + 0.008)], (1, 0, 0), (x0 - 0.004, y1 - 0.006, z1 + 0.001),
                       segments=8, mat="M_Brass_Polished", cap_bottom=True, cap_top=True)
    parts.append(C.sm(bead, 50.0))
    lf = C.gframe((0.0, y1 + 0.0002, z1 - 0.035), (1, 0, 0), (0, 0, -1))
    parts.append(C.solid_g("tlabel", [L.rounded_rect(0.07, 0.035, 0.005, 2)], 0.0015, lf, bevel=0.0004,
                           mat="M_Enamel_Cream"))
    parts.append(C.shape_g("tarrow", [[(-0.012, 0.006), (0.012, 0.006), (0.0, -0.010)]], lf, lift=0.0016,
                           mat="M_Lacquer_Black"))
    # feet
    for sx in (-1, 1):
        for zz in (z0 + 0.03, z1 - 0.03):
            ft = C.revolve_g("foot", [(0.010, 0.0), (0.012, 0.003), (0.012, 0.005), (0.0, 0.005)], (0, 1, 0),
                             (sx * 0.175, CH, zz), segments=8, mat="M_Rubber", cap_bottom=True)
            parts.append(C.sm(ft, 40.0))
    # front bezel around the opening (the door closes against it) and corner rivets on the sides
    bz = C.solid_g("tbezel", [L.rounded_rect(x1 - x0 + 0.004, y1 - y0 + 0.002, 0.006, 3),
                              L.rounded_rect(x1 - x0 - 0.050, y1 - y0 - 0.044, 0.004, 3)], 0.004,
                   C.front_frame(0.0, (y0 + y1) / 2, z1 - 0.002), bevel=0.0012, mat="M_Brass_Polished")
    parts.append(C.sm(bz, 35.0))
    for sx in (-1, 1):
        for (yy, zz) in ((y0 + 0.022, z0 + 0.03), (y1 - 0.022, z0 + 0.03), (y0 + 0.022, z1 - 0.03),
                         (y1 - 0.022, z1 - 0.03)):
            parts.append(C.rivet_g("trivet", 0.0035, (sx * (x1 + 0.0001), yy, zz), normal_g=(sx, 0, 0), segs=6))
        sf = C.gframe((sx * (x1 + 0.0002), (y0 + y1) / 2, (z0 + z1) / 2), (0, 0, sx), (0, 1, 0))
        parts.append(C.shape_g("tpanel", L.outline_ring(z1 - z0 - 0.09, y1 - y0 - 0.07, 0.008, 0.0022, 3), sf,
                               mat="M_Brass_Polished"))
    tray = C.part("IA_receive_tray", parts, (0.0, y0, (z0 + z1) / 2))

    # door: brass frame + glass + knob + hinge knuckles; hinge on the bottom edge
    hx, hy, hz = DOOR_HINGE
    dw, dh = (x1 - x0) - 0.016, (y1 - y0) - 0.012
    df = C.front_frame(0.0, hy + dh / 2 - 0.002, hz - 0.004)
    frame = C.solid_g("dframe", [L.rounded_rect(dw, dh, 0.008, 3), L.rounded_rect(dw - 0.040, dh - 0.040, 0.006, 3)],
                      0.010, df, bevel=0.0015, mat="M_Brass_Polished")
    glass = C.shape_g("dglass", [L.rounded_rect(dw - 0.034, dh - 0.034, 0.007, 3)], df, lift=0.005, mat="M_Glass")
    knob = C.revolve_g("dknob", [(0.009, 0.0), (0.009, 0.006), (0.011, 0.012), (0.009, 0.017), (0.0, 0.018)],
                       (0, 0, 1), (0.0, hy + dh - 0.012, hz + 0.006), segments=12, mat="M_Brass_Polished",
                       cap_bottom=False)
    dparts = [C.sm(frame, 35.0), glass, C.sm(knob, 40.0)]
    for sx in (-1, 1):
        kn = C.revolve_g("dknuckle", [(0.0048, 0.0), (0.0048, 0.030), (0.0, 0.030)], (1, 0, 0),
                         (sx * 0.12 - 0.015, hy, hz + 0.001), segments=8, mat="M_Brass_Aged", cap_bottom=True)
        dparts.append(C.sm(kn, 50.0))
    door = C.part("tray_door", dparts, DOOR_HINGE)
    C.parent(door, tray)
    # mounts (identity -> item rests exactly right)
    fm = C.mount("file_mount", (-0.005, FLOOR_Y + 0.005, 0.282), rot=C.grot("y", 93.0), par=tray)
    km = C.mount("key_mount", (0.090, FLOOR_Y + 0.010 + 0.002, 0.355), rot=C.grot("y", -28.0), par=tray)
    rm = C.mount("return_mount", (-0.010, FLOOR_Y + 0.010 + 0.035, 0.190), rot=C.grot("z", -90.0), par=tray)
    return tray, door, (fm, km, rm)


# ---------------------------------------------------------------- dial, ring, lamp, lever, card tray
def build_dial():
    dx, dy = DIAL
    zb = PZ + 0.0034
    skirt = L.lathe2("dskirt", [(0.0480, 0.0), (0.0500, 0.0018), (0.0500, 0.0055), (0.0470, 0.0085),
                                (0.0360, 0.0100), (0.0, 0.0100)], segments=24, mat="M_Brass_Polished", cap_bottom=False)
    C.sm(skirt, 40.0)
    # chicken-head grip bar pointing to 12 o'clock (+Y), black bakelite with a cream index line
    bar = [(-0.0130, -0.0300), (0.0130, -0.0300), (0.0150, -0.0200), (0.0085, 0.0420), (0.0, 0.0610),
           (-0.0085, 0.0420), (-0.0150, -0.0200)]
    grip = L.curve_solid("dgrip", [bar], 0.022, bevel=0.0035, bevel_res=1, mat="M_Bakelite")
    grip.data.transform(Matrix.Translation((0, 0, 0.0095)))
    C.sm(grip, 35.0)
    line = L.flat_shape("dline", [[(-0.0016, 0.006), (0.0016, 0.006), (0.0010, 0.050), (-0.0010, 0.050)]],
                        mat="M_Enamel_Cream")
    line.data.transform(Matrix.Translation((0, 0, 0.0316)))
    cap = L.lathe2("dcap", [(0.0095, 0.0), (0.0095, 0.004), (0.0060, 0.0075), (0.0, 0.0085)], segments=12,
                   mat="M_Brass_Polished", cap_bottom=False)
    cap.data.transform(Matrix.Translation((0, 0, 0.0300)))
    C.sm(cap, 50.0)
    objs = [skirt, grip, line, cap]
    fr = C.front_frame(dx, dy, zb)
    for o in objs:
        o.data.transform(fr)
    knob = C.part("IA_dest_dial", objs, (dx, dy, zb))
    ring = L.plane("dest_ring", 2 * RING_HW, 2 * RING_HW, mat="M_Decal_DestSymbols", facing="+Z")
    ring.data.transform(C.front_frame(dx, dy, PZ + 0.0036))
    ring = C.part("dest_ring", [C.sm(ring, 30.0)], (dx, dy, PZ + 0.0036))
    return knob, ring


def build_lamp():
    lx, ly = LAMP
    jw = L.lathe2("lamp_status", [(0.0185, 0.0), (0.0185, 0.0045), (0.0160, 0.0090), (0.0105, 0.0125),
                                  (0.0, 0.0140)], segments=12, mat="M_Lamp_G", cap_bottom=False)
    jw.data.transform(C.front_frame(lx, ly, PZ + 0.006))
    lamp = C.part("lamp_status", [C.sm(jw, 5.0)], (lx, ly, PZ + 0.010))
    return lamp


def build_lever():
    lx, ly, lz = LEVER_PIVOT
    # upper part (the IA mesh, <= 0.15 m tall -> box collider): rod end + bakelite grip + brass ball
    rod_t = C.revolve_g("lv_rodtop", [(0.0085, 0.0), (0.0085, 0.070)], (0, 1, 0), (lx, ly + 0.135, lz), segments=12,
                        mat="M_Brass_Polished", cap_bottom=False, cap_top=False)
    grip = C.revolve_g("lv_grip", [(0.0120, 0.0), (0.0165, 0.006), (0.0175, 0.048), (0.0150, 0.058),
                                   (0.0095, 0.062)], (0, 1, 0), (lx, ly + 0.195, lz), segments=16,
                       mat="M_Bakelite", cap_bottom=True, cap_top=False)
    ball = C.revolve_g("lv_ball", [(0.0, -0.004), (0.0120, -0.001), (0.0185, 0.009), (0.0175, 0.019), (0.0110, 0.026),
                                   (0.0, 0.0285)], (0, 1, 0), (lx, ly + 0.255, lz), segments=16, mat="M_Brass_Polished")
    ia = C.part("IA_send_lever", [C.sm(rod_t, 60.0), C.sm(grip, 45.0), C.sm(ball, 45.0)], LEVER_PIVOT)
    # lower arm + pivot boss + spring latch (child, rotates with the lever)
    rod = C.revolve_g("lv_rod", [(0.0095, -0.012), (0.0085, 0.0), (0.0085, 0.140)], (0, 1, 0), (lx, ly, lz),
                      segments=12, mat="M_Brass_Polished", cap_bottom=True, cap_top=False)
    boss = C.revolve_g("lv_boss", [(0.022, 0.0), (0.022, 0.016), (0.019, 0.020), (0.0, 0.020)], (1, 0, 0),
                       (lx - 0.006, ly, lz), segments=16, mat="M_Brass_Aged", cap_bottom=True)
    nut = C.revolve_g("lv_nut", [(0.010, 0.0), (0.010, 0.006), (0.0, 0.007)], (-1, 0, 0), (lx - 0.006, ly, lz),
                      segments=6, mat="M_Chrome", cap_bottom=False)
    latch = C.gbox("lv_latch", (lx - 0.0025, ly + 0.030, lz - 0.0135), (lx + 0.0025, ly + 0.180, lz - 0.0095),
                   mat="M_Chrome", bevel=0.0010)
    trig = C.gbox("lv_trig", (lx - 0.004, ly + 0.170, lz - 0.020), (lx + 0.004, ly + 0.188, lz - 0.008),
                  mat="M_Chrome", bevel=0.0020)
    child = C.part("send_lever_arm", [C.sm(rod, 60.0), C.sm(boss, 40.0), C.sm(nut, 20.0), C.sm(latch, 30.0),
                                      C.sm(trig, 30.0)], LEVER_PIVOT)
    C.parent(child, ia)
    return ia, child


def build_card_tray():
    tx, tz = TRAY
    w, d, h, t = 0.146, 0.100, 0.034, 0.0075
    parts = []
    tf = C.gframe((tx, CH, tz), (1, 0, 0), (0, 0, -1))
    outer = L.rounded_rect(w, d, 0.010, 3)
    inner = L.rounded_rect(w - 2 * t, d - 2 * t, 0.005, 3)
    base = C.solid_g("tbase", [outer], 0.007, tf, bevel=0.0015, mat="M_Wood_Walnut")
    wall = C.solid_g("twall", [outer, inner], h, tf, bevel=0.002, bevel_res=0, mat="M_Wood_Walnut")
    # finger notch: cut the front wall
    notch = C.gbox("notch", (tx - 0.022, CH + h - 0.014, tz + d / 2 - 0.02), (tx + 0.022, CH + h + 0.01, tz + d / 2 + 0.01),
                   mat="M_Wood_Walnut", bevel=0.0)
    M.boolean(wall, notch)
    parts += [C.sm(base, 35.0), C.sm(wall, 35.0)]
    felt = C.shape_g("tfelt", [inner], C.gframe((tx, CH + 0.0072, tz), (1, 0, 0), (0, 0, -1)), mat="M_Felt")
    parts.append(felt)
    tray = C.part("IA_card_tray", parts, (tx, CH, tz))
    # card stack: 0.125 x 0.075, 18 mm, slightly fanned top cards; top face = request-card decal
    cw, cd = 0.125, 0.075
    sy0, sy1 = CH + 0.0072, CH + 0.0072 + 0.016
    stack = C.gbox("stack", (tx - cw / 2, sy0, tz - cd / 2), (tx + cw / 2, sy1, tz + cd / 2), mat="M_Paper", bevel=0.0006)
    top = L.plane("stack_top", cw, cd, mat="M_Decal_RequestCard", facing="+Z")
    top.data.transform(Matrix.Rotation(math.radians(1.5), 4, "Z"))
    top.data.transform(Matrix.Translation(C.G(tx, sy1 + 0.0004, tz)))
    cards = C.part("tray_cards", [C.sm(stack, 30.0), C.sm(top, 30.0)], (tx, CH, tz))
    C.parent(cards, tray)
    mnt = C.mount("tray_card_mount", (tx, sy1 + 0.0008, tz), par=tray)
    return tray, cards, mnt


def build():
    C.ensure_materials()
    M.material("M_Lamp_G")
    build_body()
    build_risers()
    build_port()
    build_tray()
    build_dial()
    build_lamp()
    build_lever()
    build_card_tray()


def decal_uvs():
    ring = M.bpy.data.objects["dest_ring"]
    dx, dy = DIAL
    n1 = C.uv_rect(ring, C.front_frame(dx, dy, PZ + 0.0036), -RING_HW, RING_HW, -RING_HW, RING_HW)
    tx, tz = TRAY
    cards = M.bpy.data.objects["tray_cards"]
    fr = C.gframe((tx, 0.0, tz), (1, 0, 0), (0, 0, -1)) @ Matrix.Rotation(math.radians(1.5), 4, "Z")
    n2 = C.uv_rect(cards, fr, -0.0625, 0.0625, -0.0375, 0.0375)
    print(f"{C.TAG} decal faces: dest_ring {n1}, tray_cards {n2}")


def main():
    M.reset_scene()
    build()
    C.finalize([decal_uvs])
    C.report(NAME, BUDGET)
    C.export(NAME)
    C.verify_glb(NAME, {
        "IA_send_port": dict(parent=None, pos=(0.0, SEAT_Y, RZ)),
        "port_flap": dict(parent="IA_send_port", pos=(0.0, FLAP_HINGE[1] - SEAT_Y, FLAP_HINGE[2] - RZ)),
        "canister_mount": dict(parent="IA_send_port", pos=(0.0, 0.110, 0.0)),
        "IA_receive_tray": dict(parent=None),
        "tray_door": dict(parent="IA_receive_tray"),
        "return_mount": dict(parent="IA_receive_tray", rot=None, identity=False),
        "file_mount": dict(parent="IA_receive_tray", rot=None, identity=False),
        "key_mount": dict(parent="IA_receive_tray", rot=None, identity=False),
        "IA_dest_dial": dict(parent=None, pos=(DIAL[0], DIAL[1], PZ + 0.0034)),
        "dest_ring": dict(parent=None),
        "lamp_status": dict(parent=None),
        "IA_send_lever": dict(parent=None, pos=LEVER_PIVOT),
        "send_lever_arm": dict(parent="IA_send_lever", pos=(0.0, 0.0, 0.0)),
        "IA_card_tray": dict(parent=None),
        "tray_cards": dict(parent="IA_card_tray"),
        "tray_card_mount": dict(parent="IA_card_tray"),
    }, BUDGET)
    # world positions of the riser tops (must be tube_p0 / tube_q0 in station space)
    print(f"{C.TAG} riser tops (local): send (0, 2.35, {RZ}), return ({RX_RET}, 2.35, {RZ})")
    for nm in ("IA_send_lever", "IA_dest_dial", "IA_card_tray", "IA_send_port", "IA_receive_tray"):
        o = M.bpy.data.objects[nm]
        lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
        print(f"{C.TAG} {nm} mesh AABB {tuple(round(h - l, 4) for l, h in zip(lo, hi))}")
    if C.want_render():
        qa()


def qa():
    import lib_ch2_devices1 as Q
    Q.qa_tweak()
    args = Q.qa_args()
    roots = Q.model_roots()
    ob = M.bpy.data.objects
    if "--only-views" not in args:
        Q.studio(NAME, tuple(Q.G(1.15, 1.75, 2.15)), tuple(Q.G(0.0, 1.25, 0.15)), lens=30, floor_z=0.0)
    # open state: flap open with the canister, tray open with the file + key, dial at 1, lamp green
    Q.pose_rot(ob["port_flap"], "x", 80.0)
    Q.pose_rot(ob["tray_door"], "x", 75.0)
    Q.pose_rot(ob["IA_dest_dial"], "z", -60.0)
    Q.qa_emit(ob["lamp_status"], "4DFF7A", 8.0)
    Q.qa_item("canister", ob["canister_mount"], Q.proxy_canister)
    Q.qa_item("file_folder", ob["file_mount"], Q.proxy_file_folder)
    Q.qa_item("locker_key", ob["key_mount"], Q.proxy_locker_key)
    if "--only-views" not in args:
        Q.studio(NAME + "_2", tuple(Q.G(0.55, 1.45, 1.05)), tuple(Q.G(0.0, 1.18, 0.25)), lens=32, floor_z=0.0)
    Q.place(roots, (5.0, 0.0, -1.4), -90.0)
    Q.qa_room()
    Q.import_model("routing_chart", (5.0, 0.0, -0.35), -90.0)
    Q.import_model("compressor_panel", (5.0, 0.0, 0.8), -90.0)
    Q.qa_hall_lights()
    Q.render(NAME + "_3", (3.55, 1.55, -1.4), (4.95, 1.2, -1.4), 52.0)
    Q.render(NAME + "_4", (3.3, 1.7, 0.3), (4.9, 1.6, -1.4), 55.0)


main()
