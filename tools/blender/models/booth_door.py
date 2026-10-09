"""booth_door.glb — the projection booth's walnut door with a telephone-dial combination lock.

A panelled walnut leaf (two fielded lower panels, a wide lock rail, an upper panel with a round
brass-ringed porthole) in a cream-painted casing that fills the 0.80 x 2.10 doorway of the booth's
0.1 m north wall: jamb linings with stops, a moulded architrave with plinth blocks and a capped head
on the hall side, flat boards on the booth side, a brass threshold and three butt-hinge knuckles.
The lock is a telephone finger wheel on a brass escutcheon over a fixed cream number plate whose
3D digits show through the finger holes; a chrome finger stop at -10 deg. A jewel lamp on the
latch-side architrave shows the lock state (the code makes it red / green).

MODEL SPACE (Godot terms; Blender = (x, -z, y)):
  origin  = centre of the doorway at floor level on the HALL-side wall plane (local z = 0);
            the wall occupies local z in [-0.10, 0]; local +Z (front) faces the hall.
  placement (-1.55, 0, 2.0), yaw 180 -> local +X = world -X; the hinge is on local -X (world east).

PARTS
  booth_door_casing  static: linings, stops, threshold, architrave, plinths, head cap, booth-side
                     boards, hinge knuckles, lamp housing + chrome bezel.
  IA_booth_door      the leaf. Origin = hinge-pin axis at floor level, Godot (-0.380, 0, +0.008).
                     OPEN = -100 deg about local +Y (the free edge swings out toward the hall).
  IA_rotary_dial     child of the leaf: the chrome finger wheel (Ø 0.121). Origin = dial centre,
                     Godot (0.27, 1.20, 0.01325) in model space. Hole n (1..9, 0 as n = 10) at
                     theta = 50 + (n - 1) * 30 deg CCW from +X seen from the front; finger stop at
                     -10 deg. Dialling n = rotate (theta_n + 10) deg CLOCKWISE (negative about +Z).
  IA_dial_hole_<d>   children of the wheel, d = 0..9: the polished wall of each finger hole (its
                     AABB is the tap disc). Origin = hole centre on the wheel mid-plane.
  booth_door_lamp    jewel lens (M_Glass_Frosted) on the latch-side architrave; the code sets its
                     emission (red locked / green open).

    blender -b --factory-startup -P tools/blender/models/booth_door.py [-- --no-render] [-- --shot=1,2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices2 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "booth_door"
# ---------------------------------------------------------------- dimensions (Blender: x across, y into the wall
# toward the booth, z up; the hall-side wall plane is y = 0)
OW2, OH, WT = 0.40, 2.10, 0.10          # half opening width, opening height, wall thickness
JT = 0.020                              # jamb lining thickness
JX = OW2 - JT                           # 0.380 lining face
LX = 0.377                              # leaf half width (3 mm gaps)
LZ0, LZ1 = 0.020, 2.074                 # leaf bottom / top
LYF, LYB = 0.0, 0.045                   # leaf hall face / booth face
LYM = (LYF + LYB) / 2
HEAD_Z = 2.078                          # underside of the head lining
PIN = (-JX, -0.008)                     # hinge-pin axis (x, y)
STILE, MUNTIN = 0.105, 0.07
BOT1 = 0.25
LOCK0, LOCK1 = 1.06, 1.34
TOP0 = 1.94
PORT_C, PORT_R = 1.64, 0.112            # porthole centre z / glazed radius
UP_HT = 0.011                           # upper panel half thickness
STOP_Y0, STOP_Y1 = 0.047, 0.062         # door stops (behind the leaf)
CAS_IN, CAS_W, CAS_T = 0.392, 0.088, 0.024   # architrave inner edge, width, thickness
HEAD_IN = HEAD_Z + 0.012
PL_H = 0.20
BB_W, BB_T = 0.045, 0.015               # booth-side boards
LAMP = (0.437, -0.030, 1.30)            # jewel base centre (Blender)
# ---------------------------------------------------------------- dial (Blender x, z of the centre; depths in y)
DX, DZ = 0.27, 1.20
PLATE_F = -0.004                        # escutcheon front face
NUM_F = -0.0095                         # number plate face
WB, WF = -0.0115, -0.0150               # finger wheel back / front
WM = (WB + WF) / 2
TW = WB - WF                            # wheel thickness (0.0035)
R_WHEEL, R_FACE, R_IN = 0.0604, 0.0585, 0.0275
R_HOLE_C, R_HOLE, R_HOLE_MOUTH = 0.043, 0.0090, 0.0098
DIGIT_SIZE = 0.0140

MAH = "M_Wood_Walnut"
PAINT = "M_Enamel_Cream"
MOULD = [(0.0, 0.0), (0.0, 0.007), (0.004, 0.012), (0.011, 0.013), (0.018, 0.006), (0.020, 0.0)]


def theta(n: int) -> float:
    """Hole angle (radians) of digit position n = 1..10 (10 = digit 0)."""
    return math.radians(50.0 + (n - 1) * 30.0)


def hole_xy(n: int):
    a = theta(n)
    return R_HOLE_C * math.cos(a), R_HOLE_C * math.sin(a)


def box(name, mn, mx, mat, bevel=0.003, seg=1):
    return A.box_minmax(name, mn, mx, mat=mat, bevel=bevel, segments=seg)


def face_matrix(front: bool) -> Matrix:
    """Local (a right as seen from that side, b up, c out of the leaf face)."""
    if front:
        return A.frame_matrix((0, LYF, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    return A.frame_matrix((0, LYB, 0), (-1, 0, 0), (0, 0, 1), (0, 1, 0))


def face_rect(front, x0, x1, z0, z1):
    fm = face_matrix(front)
    if front:
        return A.rect_path(fm, x0, x1, z0, z1)
    return A.rect_path(fm, -x1, -x0, z0, z1)


def flip(obj):
    obj.data.flip_normals()
    return obj


def keyhole(name, x, z, y):
    """Small bakelite keyhole (circle + tapering slot) lying on a plate face at depth y, facing -Y."""
    cv, rr, sw = 0.0026, 0.0024, 0.0010
    a0 = math.degrees(math.acos(sw / rr))
    pts = [(0.0016, -0.0068), (sw, cv - rr * math.sin(math.radians(a0)))]
    pts += A.arc(0.0, cv, rr, -a0, 180 + a0, 8)[1:-1]
    pts += [(-sw, cv - rr * math.sin(math.radians(a0))), (-0.0016, -0.0068)]
    return L.flat_front(name, [A.ccw(pts)], x, y, z, mat="M_Bakelite")


# ================================================================ leaf
def leaf():
    parts = []
    # frame: stiles, rails, muntin
    parts += [box("stile_hinge", (-LX, LYF, LZ0), (-LX + STILE, LYB, LZ1), MAH, 0.004),
              box("stile_latch", (LX - STILE, LYF, LZ0), (LX, LYB, LZ1), MAH, 0.004),
              box("rail_top", (-LX + STILE, LYF, TOP0), (LX - STILE, LYB, LZ1), MAH, 0.004),
              box("rail_lock", (-LX + STILE, LYF, LOCK0), (LX - STILE, LYB, LOCK1), MAH, 0.004),
              box("rail_bot", (-LX + STILE, LYF, LZ0), (LX - STILE, LYB, BOT1), MAH, 0.004),
              box("muntin", (-MUNTIN / 2, LYF, BOT1), (MUNTIN / 2, LYB, LOCK0), MAH, 0.004)]
    ix0, ix1 = -LX + STILE, LX - STILE
    # two fielded lower panels (double-sided)
    pm = A.frame_matrix((0, LYM, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    lower = [(ix0, -MUNTIN / 2, BOT1, LOCK0), (MUNTIN / 2, ix1, BOT1, LOCK0)]
    for i, (a0, a1, b0, b1) in enumerate(lower):
        parts.append(A.raised_field(f"panel{i}", a0, a1, b0, b1, 0.045, 0.007, pm, mat=MAH, both=True, half_t=0.009))
    # upper panel with the round porthole opening
    pc = (LOCK1 + TOP0) / 2
    up = L.curve_solid("panel_up", [L.rounded_rect(ix1 - ix0 + 0.016, TOP0 - LOCK1 + 0.016, 0.001, 1),
                                    L.circle(PORT_R, 40, cy=PORT_C - pc)], 2 * UP_HT, bevel=0.0012, mat=MAH)
    L.to_front(up, y_back=LYM + UP_HT, x=0.0, z=pc)
    parts.append(up)
    # ogee mouldings around the three openings, both faces
    openings = lower + [(ix0, ix1, LOCK1, TOP0)]
    for side in (True, False):
        upv = (0, -1, 0) if side else (0, 1, 0)
        for i, (a0, a1, b0, b1) in enumerate(openings):
            parts.append(A.sweep(f"mould_{int(side)}_{i}", MOULD, face_rect(side, a0, a1, b0, b1), up=upv, closed=True,
                                 mat=MAH))
    # porthole: brass rings both faces, glass, six screws on the hall ring
    yf, yb = LYM - UP_HT, LYM + UP_HT
    ring_f = L.lathe2("port_ring_f", [(0.1425, 0.0), (0.136, 0.0105), (0.122, 0.0135), (PORT_R, 0.008),
                                      (PORT_R, -0.003)], segments=32, mat="M_Brass_Aged",
                      band_mats=["M_Brass_Aged", "M_Brass_Aged", "M_Brass_Polished", "M_Brass_Aged"],
                      cap_bottom=False, cap_top=False)
    ring_f.data.transform(Matrix.Translation((0, yf, PORT_C)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    ring_b = L.lathe2("port_ring_b", [(0.138, 0.0), (0.130, 0.008), (PORT_R, 0.006), (PORT_R, -0.003)],
                      segments=32, mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
    ring_b.data.transform(Matrix.Translation((0, yb, PORT_C)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    parts += [A.hint(ring_f, 50.0), A.hint(ring_b, 50.0)]
    glass = M.cylinder("port_glass", PORT_R + 0.006, 0.005, loc=(0, LYM, PORT_C), rot=(math.pi / 2, 0, 0), verts=32,
                       mat="M_Glass", bevel=0.0)
    parts.append(glass)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        parts.append(L.screw("port_screw", 0.0032, (0.1305 * math.cos(a), yf - 0.0118, PORT_C + 0.1305 * math.sin(a)),
                             normal=(-0.0, -1, 0), slot_angle=0.4 + k, segs=6, slot_mat="M_Brass_Aged"))
    # brass kick plate (hall face), D-pull (hall face, latch stile), push plate (booth face)
    parts.append(box("kick", (-LX + 0.03, LYF - 0.002, 0.045), (LX - 0.03, LYF, 0.215), "M_Brass_Aged", 0.001))
    px = LX - STILE / 2
    pull = A.tube("pull", [(px, LYF - 0.004, 0.872), (px, LYF - 0.038, 0.886), (px, LYF - 0.038, 0.992),
                           (px, LYF - 0.004, 1.006)], 0.0068, sides=10, fillet=0.014, fillet_segs=3,
                  mat="M_Brass_Polished")
    parts.append(pull)
    for z in (0.876, 1.002):
        rose = L.lathe2("pull_rose", [(0.0145, 0.0), (0.0145, 0.002), (0.011, 0.0045), (0.0085, 0.0055),
                                      (0.0, 0.0055)], segments=12, mat="M_Brass_Aged", cap_bottom=False)
        rose.data.transform(Matrix.Translation((px, LYF, z)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        parts.append(A.hint(rose, 50.0))
    parts.append(box("push", (px - 0.0375, LYB, 1.10), (px + 0.0375, LYB + 0.002, 1.40), "M_Brass_Aged", 0.0008))
    for z in (1.115, 1.385):
        parts.append(L.screw("push_screw", 0.0026, (px, LYB + 0.002, z), normal=(0, 1, 0), slot_angle=0.7,
                             segs=6, slot_mat="M_Brass_Aged"))
    # thin brass hinge leaves showing on the hinge edge
    for z in (0.25, 1.05, 1.85):
        parts.append(box("hinge_leaf", (-LX - 0.0012, LYF + 0.004, z - 0.05), (-LX, LYF + 0.030, z + 0.05),
                         "M_Brass_Aged", 0.0))
    parts += dial_static()
    A.presmooth(parts)
    o = M.join(parts, "IA_booth_door")
    M.set_origin(o, (PIN[0], PIN[1], 0.0))
    return o


# ================================================================ dial (static parts on the leaf)
def dial_static():
    parts = []
    # brass escutcheon with four screws and a service keyhole
    esc = L.curve_solid("escutcheon", [L.rounded_rect(0.150, 0.270, 0.020, 3)], LYF - PLATE_F, bevel=0.0009,
                        mat="M_Brass_Aged")
    L.to_front(esc, y_back=LYF, x=DX, z=DZ - 0.005)
    parts.append(esc)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(L.screw("esc_screw", 0.0034, (DX + sx * 0.058, PLATE_F, DZ - 0.005 + sz * 0.115),
                                 normal=(0, -1, 0), slot_angle=0.3 + sx + 2 * sz, segs=8, slot_mat="M_Brass_Aged"))
    parts.append(keyhole("keyhole", DX, DZ - 0.100, PLATE_F - 0.00005))
    # black bezel cup around the number plate
    bez = L.lathe2("bezel", [(0.0712, 0.0), (0.0712, 0.0062), (0.0690, 0.0105), (0.0638, 0.0105), (0.0626, 0.0055)],
                   segments=40, mat="M_Bakelite", cap_bottom=False, cap_top=False)
    bez.data.transform(Matrix.Translation((DX, PLATE_F, DZ)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    parts.append(A.hint(bez, 40.0))
    # cream number plate with black digits under the holes + the Institute mark in the centre
    parts.append(L.flat_front("number_plate", [L.circle(0.0630, 40)], DX, NUM_F, DZ, mat="M_Enamel_Cream"))
    for n in range(1, 11):
        hx, hz = hole_xy(n)
        parts.append(L.label_front(f"digit{n % 10}", str(n % 10), DIGIT_SIZE, DX + hx, NUM_F - 0.0001, DZ + hz,
                                   mat="M_Bakelite", font=L.FONT_SANS_B, res=2))
        # thin printed ring around each digit (as on a real number plate)
        parts.append(L.flat_front(f"digit_ring{n % 10}", L.circle_line(0.0104, 0.0006, 20), DX + hx, NUM_F - 0.0001,
                                  DZ + hz, mat="M_Bakelite"))
    parts.append(L.flat_front("mark_ring", L.circle_line(0.0090, 0.0016, 28), DX, NUM_F - 0.0001, DZ, mat="M_Bakelite"))
    parts.append(L.flat_front("mark_line", [L.rounded_rect(0.0016, 0.0300, 0.0003, 1)], DX, NUM_F - 0.00015, DZ,
                              mat="M_Bakelite"))
    # chrome finger stop at -10 deg: foot on the bezel lip, bent over the wheel face to the hole ring
    a = math.radians(-10.0)
    u = Vector((math.cos(a), 0.0, math.sin(a)))
    c = Vector((DX, 0.0, DZ))

    def p(r, y):
        return tuple(c + u * r + Vector((0.0, y, 0.0)))
    stop = A.tube("finger_stop", [p(0.0668, PLATE_F - 0.0100), p(0.0668, -0.0200), p(0.0505, -0.0206)], 0.0017,
                  sides=8, fillet=0.0035, fillet_segs=3, mat="M_Chrome")
    foot = M.box("stop_foot", (0.0075, 0.0030, 0.0060), mat="M_Chrome", bevel=0.0008, segments=1)
    foot.data.transform(Matrix.Rotation(-a, 4, "Y"))
    foot.location = p(0.0668, PLATE_F - 0.0118)
    parts += [stop, A.hint(foot, 30.0)]
    return parts


# ================================================================ finger wheel + holes (interactive)
def wheel():
    loops = [L.circle(R_FACE, 48), L.circle(R_IN, 32)]
    for n in range(1, 11):
        hx, hz = hole_xy(n)
        loops.append(L.circle(R_HOLE_MOUTH, 14, cx=hx, cy=hz))
    face = L.flat_front("wheel_face", loops, DX, WF, DZ, mat="M_Chrome")
    parts = [face]
    # rounded outer rim (seen from the front and the side)
    rim = L.lathe2("wheel_rim", [(0.0594, 0.0), (0.0602, 0.0008), (R_WHEEL, 0.0020), (0.0598, 0.0031),
                                 (R_FACE, TW)], segments=48, mat="M_Chrome", cap_bottom=False, cap_top=False)
    rim.data.transform(Matrix.Translation((DX, WB, DZ)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    parts.append(A.hint(rim, 60.0))
    # inner lip (faces the axis)
    lip = L.lathe2("wheel_lip", [(R_IN, 0.0), (R_IN, TW)], segments=32, mat="M_Chrome", cap_bottom=False,
                   cap_top=False)
    lip.data.transform(Matrix.Translation((DX, WB, DZ)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    parts.append(A.hint(flip(lip), 60.0))
    # polished chamfer at every hole mouth (part of the wheel)
    for n in range(1, 11):
        hx, hz = hole_xy(n)
        ch = L.lathe2("hole_chamfer", [(R_HOLE_MOUTH, 0.0), (R_HOLE, 0.0008)], segments=14, mat="M_Chrome",
                      cap_bottom=False, cap_top=False)
        ch.data.transform(Matrix.Translation((DX + hx, WF, DZ + hz)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
        parts.append(A.hint(flip(ch), 60.0))
    A.presmooth(parts)
    w = M.join(parts, "IA_rotary_dial")
    M.set_origin(w, (DX, WM, DZ))
    holes = []
    for n in range(1, 11):
        hx, hz = hole_xy(n)
        hw = L.lathe2(f"IA_dial_hole_{n % 10}", [(R_HOLE, 0.0), (R_HOLE, TW - 0.0008)], segments=14,
                      mat="M_Chrome", cap_bottom=False, cap_top=False)
        hw.data.transform(Matrix.Translation((DX + hx, WB, DZ + hz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        flip(hw)
        A.presmooth([A.hint(hw, 60.0)])
        M.set_origin(hw, (DX + hx, WM, DZ + hz))
        holes.append(hw)
    return w, holes


# ================================================================ casing, threshold, hinges, lamp
def casing():
    parts = []
    z0 = 0.014
    parts += [box("jamb_l", (-OW2, 0.0, z0), (-JX, WT, OH), PAINT, 0.002),
              box("jamb_r", (JX, 0.0, z0), (OW2, WT, OH), PAINT, 0.002),
              box("jamb_head", (-OW2, 0.0, HEAD_Z), (OW2, WT, OH), PAINT, 0.002),
              box("stop_l", (-JX, STOP_Y0, z0), (-JX + 0.012, STOP_Y1, HEAD_Z), PAINT, 0.0015),
              box("stop_r", (JX - 0.012, STOP_Y0, z0), (JX, STOP_Y1, HEAD_Z), PAINT, 0.0015),
              box("stop_head", (-JX + 0.012, STOP_Y0, HEAD_Z - 0.012), (JX - 0.012, STOP_Y1, HEAD_Z), PAINT, 0.0015),
              box("threshold", (-OW2, -0.014, 0.0), (OW2, WT + 0.004, z0), "M_Brass_Aged", 0.003, 1)]
    # hall side: moulded architrave, plinth blocks, capped head
    cas = A.profile_casing(w=CAS_W, t=CAS_T)
    parts.append(A.sweep("architrave", cas, [(-CAS_IN, 0, PL_H), (-CAS_IN, 0, HEAD_IN), (CAS_IN, 0, HEAD_IN),
                                             (CAS_IN, 0, PL_H)], up=(0, -1, 0), mat=PAINT))
    for s in (-1, 1):
        x0, x1 = sorted((s * (CAS_IN - 0.006), s * (CAS_IN + CAS_W + 0.006)))
        parts.append(box(f"plinth{s}", (x0, -0.032, 0.0), (x1, 0.0, PL_H), PAINT, 0.004, 2))
    top = HEAD_IN + CAS_W
    parts.append(box("head_fillet", (-CAS_IN - CAS_W - 0.010, -0.034, top), (CAS_IN + CAS_W + 0.010, 0.0, top + 0.010),
                     PAINT, 0.002))
    parts.append(box("head_cap", (-CAS_IN - CAS_W - 0.022, -0.046, top + 0.010),
                     (CAS_IN + CAS_W + 0.022, 0.0, top + 0.032), PAINT, 0.005, 2))
    # booth side: plain boards (narrow: the booth's east wall is 5 cm from the hinge jamb)
    yb = WT
    parts += [box("bb_l", (-OW2 - BB_W, yb, 0.0), (-OW2, yb + BB_T, OH + BB_W), PAINT, 0.002),
              box("bb_r", (OW2, yb, 0.0), (OW2 + BB_W, yb + BB_T, OH + BB_W), PAINT, 0.002),
              box("bb_head", (-OW2, yb, OH), (OW2, yb + BB_T, OH + BB_W), PAINT, 0.002)]
    # butt-hinge knuckles on the pin axis (hall side)
    for z in (0.25, 1.05, 1.85):
        k = A.lathe_s("knuckle", [(0.0, -0.058), (0.004, -0.057), (0.0075, -0.052), (0.0075, 0.052), (0.004, 0.057),
                                  (0.0, 0.059)], segments=8, mat="M_Brass_Aged")
        k.location = (PIN[0], PIN[1], z)
        parts.append(k)
    # lamp: bakelite housing on the latch-side architrave + chrome bezel
    lx, ly, lz = LAMP
    parts.append(box("lamp_housing", (lx - 0.017, ly, lz - 0.026), (lx + 0.017, -0.010, lz + 0.026), "M_Bakelite",
                     0.003, 2))
    bz = L.lathe2("lamp_bezel", [(0.0094, 0.0), (0.0128, 0.0), (0.0130, 0.0026), (0.0112, 0.0042), (0.0094, 0.0032)],
                  segments=16, mat="M_Chrome", cap_bottom=False, cap_top=False)
    bz.data.transform(Matrix.Translation((lx, ly, lz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    parts.append(A.hint(bz, 50.0))
    for sz in (-1, 1):
        parts.append(L.screw("lamp_screw", 0.0018, (lx, ly, lz + sz * 0.019), normal=(0, -1, 0), slot_angle=0.5 * sz,
                             segs=6, slot_mat="M_Steel_Dark", mat="M_Chrome"))
    A.presmooth(parts)
    o = M.join(parts, "booth_door_casing")
    lamp = L.lathe2("booth_door_lamp", [(0.0094, 0.0), (0.0094, 0.0012), (0.0072, 0.0044), (0.0040, 0.0063),
                                        (0.0, 0.0068)], segments=12, mat="M_Glass_Frosted", cap_bottom=False)
    lamp.data.transform(Matrix.Translation((lx, ly, lz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    A.presmooth([A.hint(lamp, 20.0)])
    M.set_origin(lamp, (lx, ly, lz))
    return o, lamp


def build():
    M.reset_scene()
    A.prepare_materials()
    C.ensure_materials()
    cs, lamp = casing()
    lf = leaf()
    wh, holes = wheel()
    M.refresh()
    M.set_parent(wh, lf)
    for h in holes:
        M.set_parent(h, wh)
    A.finalize_uv()

    def vertical(c, n):     # lower panels: vertical grain
        if abs(c.x) > MUNTIN / 2 + 0.003 and abs(c.x) < LX - STILE - 0.003 and BOT1 + 0.003 < c.z < LOCK0 - 0.003:
            return True
        return None
    A.grain_uv(lf, force=vertical)
    A.grain_uv(cs)
    print(f"[{NAME}] tris: casing={A.tris(cs)} leaf={A.tris(lf)} wheel={A.tris(wh)} "
          f"holes={sum(A.tris(h) for h in holes)} lamp={A.tris(lamp)} TOTAL={M.tri_count()}")
    return dict(casing=cs, leaf=lf, wheel=wh, holes=holes, lamp=lamp)


def verify() -> bool:
    exp = {
        "booth_door_casing": dict(parent=None, pos=(0, 0, 0)),
        "IA_booth_door": dict(parent=None, pos=(PIN[0], 0.0, -PIN[1])),
        "IA_rotary_dial": dict(parent="IA_booth_door", pos=(DX - PIN[0], DZ, -WM + PIN[1])),
        "booth_door_lamp": dict(parent=None, pos=(LAMP[0], LAMP[2], -LAMP[1])),
    }
    for n in range(1, 11):
        hx, hz = hole_xy(n)
        exp[f"IA_dial_hole_{n % 10}"] = dict(parent="IA_rotary_dial", pos=(hx, hz, 0.0))
    return C.verify_glb(NAME, exp, 6000)


# ================================================================ QA
DOOR_POS, DOOR_YAW = (-1.55, 0.0, 2.0), 180.0


def qa_scene():
    C.qa_room()
    C.qa_lights(booth_bulb=25.0, hall=110.0, fill=35.0)
    for nm, pos, yaw in (("film_projector", (-2.9, 0.0, 2.65), 180.0), ("slide_projector", (-2.35, 0.0, 2.45), 180.0)):
        C.import_model(nm, pos, yaw)


def lamp_on(lamp, colour):
    C.qa_emit(lamp, colour, 8.0, base=colour)
    A.qa_light("door_lamp", "POINT", tuple(lamp.matrix_world @ Vector((0, -0.01, 0))), 0.15, colour, size=0.005)


def main():
    args = M.main_guard()
    parts = build()
    A.export_lean(NAME)
    ok = verify()
    print(f"[{NAME}] verify {'OK' if ok else 'FAILED'}")
    if "--no-render" in args:
        return
    want = set()
    for a in args:
        if a.startswith("--shot="):
            want |= set(a.split("=", 1)[1].split(","))

    def on(k):
        return not want or k in want
    C.place([parts["casing"], parts["leaf"], parts["lamp"]], DOOR_POS, DOOR_YAW)
    qa_scene()
    C.qa_glass_tweak()
    lamp_on(parts["lamp"], "FF3B2F")
    if on("1"):    # in-game booth_door view, closed (lamp red)
        C.render(NAME, (-1.55, 1.45, 0.75), (-1.55, 1.2, 2.0), 52.0, res=(960, 540))
    if on("2"):    # in-game dial view
        C.render(NAME + "_2", (-1.8, 1.25, 1.5), (-1.82, 1.2, 2.0), 36.0, res=(960, 540))
    if on("4"):    # hero: three-quarter view from the hall
        C.render(NAME + "_4", (-0.55, 1.35, 0.45), (-1.62, 1.15, 2.0), 40.0, res=(960, 640))
    if on("5"):    # dialling 5: the wheel turned clockwise by theta_5 + 10 = 180 deg, hole 5 at the stop
        parts["wheel"].rotation_euler = C.blender_rot_about_godot("Z", -(50.0 + 4 * 30.0 + 10.0))
        C.render(NAME + "_5", (-1.79, 1.24, 1.72), (-1.82, 1.2, 2.0), 30.0, res=(960, 640))
        parts["wheel"].rotation_euler = (0, 0, 0)
    if on("3"):    # OPEN: leaf -100 deg about local +Y, lamp green
        parts["leaf"].rotation_euler = C.blender_rot_about_godot("Y", -100.0)
        for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA_door_lamp")]:
            bpy.data.objects.remove(o, do_unlink=True)
        lamp_on(parts["lamp"], "4DFF7A")
        C.render(NAME + "_3", (-2.25, 1.6, 0.75), (-1.4, 1.15, 2.1), 50.0, res=(960, 640))
        C.render(NAME + "_6", (-1.55, 1.45, 0.75), (-1.55, 1.2, 2.0), 52.0, res=(960, 540))


main()
