"""film_projector.glb — a 1950s 16 mm cinema projector on a heavy cast pedestal (projection booth).

A green-grey hammertone body casting with a black-and-chrome lens barrel at the front, the film path
(sprockets, gate, loop rollers, framing knob) and every control on the operator side (local -X):
the RUN lever on a quadrant with red / green stops, two frame-step buttons with 3D arrows and a
crimson MERIDIAN-16 badge. The feed arm rises over the front of the body; the take-up arm reaches
down behind it with an empty reel. A black crinkle lamp house with chrome louvres, a mushroom
chimney and an amber inspection window stands at the back left (+X). The column stands on a
domed cast base with a height clamp and a tilt head; a cloth cable runs to a floor box.

MODEL SPACE (Godot terms; Blender = (x, -z, y)): origin = pedestal centre on the floor, front +Z.
Placement (-2.9, 0, 2.65), yaw 180: the lens fires world -Z through the booth window; the operator
side (local -X) faces world +X, toward the projector camera.

PARTS (origin at the pivot, identity rotation at rest)
  IA_focus_ring    knurled ring on the lens barrel, axis local +Z through (0, 1.95); digits 0..8 at
                   polar angle 90 + 30k (CCW from +X seen from the lens front); a fixed index on top.
                   Rotation -30 deg x focus about +Z brings digit `focus` under the index.
  IA_run_lever     operator-side lever, pivot axis local +X; OFF at rest (arm leans 20 deg back over
                   the red stop), RUN = +40 deg (20 deg forward, over the green stop).
  IA_frame_prev    push buttons with raised arrows (prev = back / viewer's left from the operator side,
  IA_frame_next    next = front / right). Origin = button face centre; pressed = +0.004 along +X.
  takeup_reel      empty 16 mm reel on the lower arm, spins about local +X.
  feed_reel_mount  empty: a film_reel.glb (axle = its local +Z) parented with identity hangs on the
                   feed spindle with its face toward the operator (mount = -90 deg about +Y).
  lamp_glow        amber inspection window + louvre slot backs (M_Glass_Amber), emissive by code.
  lens_origin      empty at the front lens centre; the beam runs along local +Z.

    blender -b --factory-startup -P tools/blender/models/film_projector.py [-- --no-render] [-- --shot=1,2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_devices2 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "film_projector"
G = C.G
AXN = (-1.0, 0.0, 0.0)          # Godot -X (operator side) in Blender
AXP = (1.0, 0.0, 0.0)
AYP = (0.0, 0.0, 1.0)           # Godot +Y
AZP = (0.0, -1.0, 0.0)          # Godot +Z (front)

LY = 1.95                       # lens axis height
OPF = -0.055                    # operator face (x)
BX1 = 0.115                     # body +X face
BY0, BY1 = 1.70, 2.08           # body bottom / top
BZ0, BZ1 = -0.15, 0.17          # body back / front
LENS_FRONT = 0.3125
RING_Z0, RING_Z1 = 0.215, 0.258
RING_C = (RING_Z0 + RING_Z1) / 2
R_DIGIT_BAND = 0.0421
LEVER_P = (OPF, 1.885, -0.075)
LEVER_REST = -20.0
BTN_Y, BTN_Z = 1.765, (-0.112, -0.064)
BTN_FACE = OPF - 0.002 - 0.0066
REEL_X = -0.075
FEED_C = (REEL_X, 2.31, 0.07)
TAKE_C = (REEL_X, 1.655, -0.255)
LH = ((0.03, 1.76, -0.265), (0.16, 2.17, -0.13))      # lamp house box (back plate behind it)
LH_BACK = -0.275
WIN_C = (0.03, 1.99, -0.215)


def gbox(name, mn, mx, mat, bevel=0.003, seg=1):
    a, b = G(*mn), G(*mx)
    return A.box_minmax(name, (min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)),
                        (max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)), mat=mat, bevel=bevel, segments=seg)


def rev(name, prof, direction, loc_g, segments=24, mat="M_Chrome", **kw):
    return D.revolve(name, prof, direction=direction, loc=tuple(G(*loc_g)), segments=segments, mat=mat, **kw)


def op_plate(obj, x_face, gy=0.0, gz=0.0):
    """Shape drawn in (Godot z, Godot y) offsets, extruded toward -X from x_face (operator side)."""
    C.side_plate(obj, x_face, -gz, gy, -1.0)
    return obj


def op_flat(name, loops, x_face, gy, gz, mat):
    return op_plate(L.flat_shape(name, loops, mat=mat), x_face, gy, gz)


def op_text(name, body, size, x_face, gy, gz, mat="M_Chrome", font=L.FONT_COND_B, res=1, spacing=1.0):
    t = L.text_flat(name, body, size, font=font, res=res, mat=mat, spacing=spacing)
    L.recentre_xy(t)
    return op_plate(t, x_face, gy, gz)


def flip(obj):
    obj.data.flip_normals()
    return obj


# ================================================================ pedestal (static)
def pedestal():
    parts = []
    base = rev("base", [(0.235, 0.012), (0.235, 0.026), (0.226, 0.036), (0.150, 0.058), (0.092, 0.094),
                        (0.064, 0.128), (0.054, 0.146)], AYP, (0, 0, 0), segments=28, mat="M_Steel_Painted",
               band_mats=["M_Steel_Dark", "M_Steel_Painted"], cap_bottom=True, cap_top=False)
    parts.append(A.hint(base, 40.0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ft = rev("foot", [(0.024, 0.0), (0.024, 0.005), (0.014, 0.012), (0.0, 0.0125)], AYP,
                 (0.19 * math.cos(a), 0.0, 0.19 * math.sin(a)), segments=10, mat="M_Steel_Dark", cap_top=False)
        parts.append(A.hint(ft, 50.0))
    col = rev("column", [(0.050, 0.140), (0.050, 0.172), (0.040, 0.184), (0.036, 0.196), (0.036, 1.380),
                         (0.046, 1.390), (0.046, 1.440), (0.033, 1.452), (0.030, 1.460), (0.030, 1.575),
                         (0.042, 1.586), (0.0, 1.590)], AYP, (0, 0, 0), segments=18, mat="M_Steel_Painted",
              band_mats=["M_Steel_Painted"] * 4 + ["M_Chrome", "M_Chrome", "M_Chrome"] + ["M_Steel_Painted"] * 4,
              cap_bottom=False)
    parts.append(A.hint(col, 50.0))
    # height clamp T-handle (operator side)
    parts.append(A.hint(rev("clamp_rod", [(0.0045, 0.0), (0.0045, 0.040)], AXN, (-0.044, 1.415, 0.0), segments=8,
                            cap_bottom=False, cap_top=False), 60.0))
    parts.append(A.hint(rev("clamp_knob", [(0.0, 0.0), (0.008, 0.002), (0.0105, 0.010), (0.0095, 0.020),
                                           (0.0, 0.024)], AXN, (-0.082, 1.415, 0.0), segments=10,
                            mat="M_Bakelite"), 60.0))
    # tilt head: trunnion block, platform, tilt knob
    parts.append(gbox("head_block", (-0.032, 1.585, -0.05), (0.062, 1.660, 0.05), "M_Steel_Painted", 0.008, 2))
    parts.append(gbox("platform", (-0.050, 1.655, -0.138), (0.112, 1.702, 0.158), "M_Steel_Painted", 0.008, 2))
    tk = L.knurled_knob("tilt_knob", 0.014, 0.020, ridges=10, mat="M_Bakelite", simple=True, index_mark=False)
    D.aim(tk, AXN)
    tk.location = tuple(G(-0.032, 1.622, 0.0))
    parts.append(A.hint(tk, 30.0))
    A.presmooth(parts)
    return M.join(parts, "projector_pedestal")


# ================================================================ body casting + lens barrel + film path (static)
def body():
    parts = []
    # side silhouette (drawn x = Godot z, y = Godot y): sloped front-top, rounded corners
    sil = A.ccw(A.dedupe(
        L.arc_pts(0.020, math.radians(180), math.radians(270), 3, cx=BZ0 + 0.020, cy=BY0 + 0.020)
        + L.arc_pts(0.020, math.radians(270), math.radians(360), 3, cx=BZ1 - 0.020, cy=BY0 + 0.020)
        + L.arc_pts(0.030, math.radians(0), math.radians(60), 3, cx=BZ1 - 0.030, cy=2.005)
        + L.arc_pts(0.030, math.radians(60), math.radians(90), 2, cx=0.112, cy=BY1 - 0.030)
        + L.arc_pts(0.024, math.radians(90), math.radians(180), 3, cx=BZ0 + 0.024, cy=BY1 - 0.024)))
    cast = L.curve_solid("casting", [sil], BX1 - OPF, bevel=0.009, bevel_res=2, mat="M_Steel_Painted")
    op_plate(cast, BX1)
    parts.append(cast)
    # lens mount boss, fixed index collar, front barrel with chrome bezel + glass
    parts.append(A.hint(rev("lens_boss", [(0.060, 0.164), (0.060, 0.174), (0.054, 0.182), (0.046, 0.188),
                                          (0.0386, 0.188)], AZP, (0, LY, 0), segments=32, mat="M_Chrome",
                            cap_bottom=False, cap_top=False), 40.0))
    parts.append(A.hint(rev("collar", [(0.0386, 0.188), (0.0386, 0.2135), (0.0372, 0.2148)], AZP, (0, LY, 0),
                            segments=32, mat="M_Lacquer_Black", cap_bottom=False, cap_top=False), 40.0))
    parts.append(A.hint(rev("front_barrel", [(0.0356, 0.2585), (0.0356, 0.2960), (0.0386, 0.2990), (0.0392, 0.3090),
                                             (0.0362, LENS_FRONT), (0.0300, LENS_FRONT), (0.0290, 0.3075)],
                            AZP, (0, LY, 0), segments=32, mat="M_Lacquer_Black",
                            band_mats=["M_Lacquer_Black", "M_Chrome", "M_Chrome", "M_Chrome", "M_Chrome",
                                       "M_Chrome"], cap_bottom=False, cap_top=False), 40.0))
    parts.append(op_disc("lens_back", 0.0292, 0.3000, "M_Lacquer_Black"))
    glass = rev("lens_glass", [(0.0291, 0.3040), (0.0200, 0.3082), (0.0, 0.3096)], AZP, (0, LY, 0), segments=24,
                mat="M_Glass", cap_bottom=False)
    parts.append(A.hint(glass, 60.0))
    # index mark on top of the collar (white wedge pointing at the ring) + engraved line
    idx = L.flat_shape("index", [[(-0.0026, -0.2050), (0.0026, -0.2050), (0.0, -0.2142)]], mat="M_Enamel_White")
    idx.location = (0.0, 0.0, LY + 0.0387)
    parts.append(idx)
    parts.append(L.flat_shape("index_line", [L.rounded_rect(0.0007, 0.014, 0.0002, 1, cy=-0.1975)],
                              mat="M_Enamel_White", loc=(0.0, 0.0, LY + 0.0387)))
    # gate: chrome plate, aperture, latch knob, four rivets
    gate = L.curve_solid("gate", [L.rounded_rect(0.046, 0.084, 0.006, 2)], 0.006, bevel=0.0012, mat="M_Chrome")
    parts.append(op_plate(gate, OPF, LY, 0.128))
    parts.append(op_flat("aperture", [L.rounded_rect(0.012, 0.016, 0.0015, 1)], OPF - 0.0061, LY, 0.128,
                         "M_Lacquer_Black"))
    for dy in (-0.034, 0.034):
        for dz in (-0.016, 0.016):
            parts.append(L.rivet("gate_rivet", 0.0022, tuple(G(OPF - 0.006, LY + dy, 0.128 + dz)), normal=AXN,
                                 mat="M_Chrome", segs=6))
    gk = L.knurled_knob("gate_knob", 0.0075, 0.010, ridges=8, mat="M_Chrome", simple=True, index_mark=False)
    D.aim(gk, AXN)
    gk.location = tuple(G(OPF - 0.006, LY + 0.026, 0.128))
    parts.append(A.hint(gk, 30.0))
    # sprockets (toothed drums), loop rollers, framing knob
    for k, y in enumerate((2.035, 1.800)):
        sp = rev(f"sprocket{k}", [(0.019, 0.0), (0.0196, 0.0012, "k"), (0.0196, 0.0050, "k"), (0.0182, 0.0060),
                                  (0.0182, 0.0180), (0.0120, 0.0200), (0.0, 0.0204)], AXN, (OPF, y, 0.095),
                 segments=16, knurl=0.0016, mat="M_Chrome", cap_bottom=False)
        parts.append(A.hint(sp, 30.0))
        shoe = L.curve_solid(f"shoe{k}", [L.arc_pts(0.027, math.radians(-60), math.radians(60), 4)
                                          + L.arc_pts(0.0225, math.radians(60), math.radians(-60), 4)],
                             0.016, bevel=0.0006, mat="M_Steel_Dark")
        parts.append(op_plate(shoe, OPF - 0.002, y, 0.095))
    for y in (1.990, 1.845):
        parts.append(A.hint(rev("roller", [(0.0085, 0.0), (0.0085, 0.0170), (0.0050, 0.0185), (0.0, 0.0188)], AXN,
                                (OPF, y, 0.052), segments=12, mat="M_Chrome", cap_bottom=False), 50.0))
    fk = L.knurled_knob("framing_knob", 0.0125, 0.016, ridges=12, mat="M_Bakelite", simple=True,
                        cap_mat="M_Chrome", index_mark=False)
    D.aim(fk, AXN)
    fk.location = tuple(G(OPF, 1.918, 0.012))
    parts.append(A.hint(fk, 30.0))
    # run-lever quadrant with red (OFF) / green (RUN) stops
    px, py, pz = LEVER_P
    quad = L.curve_solid("quadrant", [L.arc_pts(0.064, math.radians(48), math.radians(132), 6)
                                      + L.arc_pts(0.020, math.radians(132), math.radians(48), 2)], 0.0025,
                         bevel=0.0006, mat="M_Lacquer_Black")
    parts.append(op_plate(quad, OPF, py, pz))
    for ang, mat in ((124.0, "M_Enamel_Crimson"), (56.0, "M_Enamel_Green")):
        a = math.radians(ang)
        parts.append(op_flat("stop_dot", [L.circle(0.0042, 12)], OPF - 0.0026, py + 0.050 * math.sin(a),
                             pz + 0.050 * math.cos(a), mat))
    # frame-button panel + bezels
    bp = L.curve_solid("btn_panel", [L.rounded_rect(0.090, 0.036, 0.008, 2)], 0.002, bevel=0.0005, mat="M_Chrome")
    parts.append(op_plate(bp, OPF, BTN_Y, sum(BTN_Z) / 2))
    for z in BTN_Z:
        parts.append(A.hint(rev("btn_bezel", [(0.0152, 0.0), (0.0152, 0.0016), (0.0130, 0.0030), (0.0114, 0.0024)],
                                AXN, (OPF - 0.002, BTN_Y, z), segments=16, mat="M_Chrome", cap_bottom=False,
                                cap_top=False), 50.0))
    # badge: crimson enamel plate with chrome lettering
    badge = L.curve_solid("badge", [L.rounded_rect(0.082, 0.020, 0.003, 2)], 0.0015, bevel=0.0004,
                          mat="M_Enamel_Crimson")
    parts.append(op_plate(badge, OPF, 2.040, -0.075))
    parts.append(op_text("badge_txt", "MERIDIAN-16", 0.0105, OPF - 0.0016, 2.0405, -0.075, mat="M_Chrome",
                         spacing=1.05))
    # motor housing on the +X side, bottom front
    parts.append(A.hint(rev("motor", [(0.042, 0.0), (0.042, 0.050), (0.038, 0.058), (0.022, 0.062), (0.0, 0.0625)],
                            AXP, (BX1 - 0.004, 1.775, 0.040), segments=20, mat="M_Steel_Painted",
                            band_mats=["M_Steel_Painted", "M_Chrome", "M_Chrome", "M_Chrome"],
                            cap_bottom=False), 40.0))
    # arms: feed (rising over the front) and take-up (reaching down behind)
    feed = A.ccw(A.dedupe([(-0.012, 2.072), (0.074, 2.072), (0.090, 2.150), (0.090, 2.300)]
                          + L.arc_pts(0.020, math.radians(0), math.radians(180), 5, cx=0.070, cy=2.310)
                          + [(0.050, 2.290), (0.034, 2.160)]))
    fa = L.curve_solid("feed_arm", [feed], 0.012, bevel=0.0018, mat="M_Steel_Painted")
    parts.append(op_plate(fa, -0.044))
    take = A.ccw(A.dedupe([(-0.140, 1.812), (-0.140, 1.725), (-0.238, 1.641)]
                          + L.arc_pts(0.020, math.radians(-40), math.radians(-300), 7, cx=-0.255, cy=1.655)
                          + [(-0.150, 1.818)]))
    ta = L.curve_solid("take_arm", [take], 0.012, bevel=0.0018, mat="M_Steel_Painted")
    parts.append(op_plate(ta, -0.044))
    for (cx, cy, cz) in (FEED_C, TAKE_C):
        parts.append(A.hint(rev("spindle", [(0.0110, 0.0), (0.0110, 0.0060), (0.0045, 0.0075), (0.0045, 0.0450),
                                            (0.0062, 0.0458), (0.0062, 0.0480), (0.0, 0.0490)], AXN,
                                (-0.056, cy, cz), segments=12, mat="M_Chrome", cap_bottom=False), 50.0))
    # cloth power cable from under the body down the column to a floor box
    cable = L.tube("cable", [tuple(G(0.075, 1.705, -0.110)), tuple(G(0.080, 1.60, -0.080)), tuple(G(0.052, 1.10, -0.048)),
                             tuple(G(0.060, 0.40, -0.052)), tuple(G(0.100, 0.07, -0.140)), tuple(G(0.115, 0.006, -0.300)),
                             tuple(G(0.120, 0.006, -0.405))], 0.0045, mat="M_Fabric", bevel_res=1, res_u=3)
    for v in cable.data.vertices:
        v.co.z = max(v.co.z, 0.0005)
    parts.append(A.hint(cable, 60.0))
    parts.append(gbox("floor_box", (0.085, 0.0, -0.455), (0.155, 0.032, -0.400), "M_Steel_Dark", 0.004, 1))
    A.presmooth(parts)
    return M.join(parts, "projector_body")


def op_disc(name, r, z, mat):
    """Flat disc facing +Z (front) on the lens axis at Godot depth z."""
    d = L.flat_shape(name, [L.circle(r, 24)], mat=mat)
    L.to_front(d, y_back=-z, x=0.0, z=LY)
    return d


# ================================================================ lamp house (static) + lamp_glow
def lamphouse():
    (x0, y0, z0), (x1, y1, z1) = LH
    parts = [gbox("lh_box", (x0, y0, z0), (x1, y1, z1), "M_Steel_Dark", 0.010, 2)]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    slots = [1.885 + 0.038 * k for k in range(6)]
    loops = [L.rounded_rect(x1 - x0, y1 - y0, 0.010, 2)]
    for y in slots:
        loops.append(L.rounded_rect(0.086, 0.010, 0.004, 2, cy=y - cy))
    bp = L.curve_solid("lh_back", loops, z0 - LH_BACK, bevel=0.0012, mat="M_Steel_Dark")
    # drawn (xc, yc, zc) -> Godot (cx - xc, cy + yc, z0 - zc) (back plate, extruded toward -Z)
    bp.data.transform(Matrix.Translation((cx, -z0, cy)) @ Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0),
                                                                   (0, 0, 0, 1))))
    parts.append(bp)
    for y in slots:     # chrome louvre lips over the slots
        lip = M.box("louvre", (0.092, 0.012, 0.0025), mat="M_Chrome", bevel=0.0006, segments=1)
        lip.data.transform(Matrix.Rotation(math.radians(-35), 4, "X"))
        lip.location = tuple(G(cx, y + 0.0085, LH_BACK - 0.004))
        parts.append(lip)
    # mushroom chimney with dark louvre slots
    parts.append(A.hint(rev("chimney", [(0.034, 0.0), (0.034, 0.046), (0.052, 0.051), (0.052, 0.057), (0.022, 0.069),
                                        (0.0, 0.071)], AYP, (cx, y1 - 0.004, -0.200), segments=18, mat="M_Steel_Dark",
                            band_mats=["M_Steel_Dark", "M_Chrome", "M_Chrome", "M_Chrome", "M_Chrome"],
                            cap_bottom=False), 40.0))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        sl = L.flat_shape("chim_slot", [L.rounded_rect(0.0055, 0.026, 0.0015, 1)], mat="M_Bakelite")
        sl.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))           # face -Y
        sl.data.transform(Matrix.Rotation(a + math.pi / 2, 4, "Z"))       # face outward at angle a
        sl.location = (cx + 0.0342 * math.cos(a), 0.200 + 0.0342 * math.sin(a), y1 - 0.004 + 0.024)
        parts.append(sl)
    # inspection window bezel on the -X face
    wx, wy, wz = WIN_C
    parts.append(A.hint(rev("win_bezel", [(0.0235, 0.0), (0.0235, 0.0030), (0.0200, 0.0048), (0.0168, 0.0040),
                                          (0.0168, 0.0010)], AXN, (wx, wy, wz), segments=20, mat="M_Chrome",
                            cap_bottom=False, cap_top=False), 50.0))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        parts.append(L.rivet("win_rivet", 0.0016, tuple(G(wx - 0.003, wy + 0.0215 * math.sin(a), wz + 0.0215 * math.cos(a))),
                             normal=AXN, mat="M_Chrome", segs=6))
    A.presmooth(parts)
    house = M.join(parts, "projector_lamphouse")
    # glow: window disc + one strip behind each slot (single material, toggled by code)
    glow = [op_flat("glow_win", [L.circle(0.0170, 16)], wx - 0.0004, wy, wz, "M_Glass_Amber")]
    for y in slots:
        s = L.flat_shape("glow_slot", [L.rounded_rect(0.088, 0.012, 0.002, 1)], mat="M_Glass_Amber")
        s.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))           # face +Y (Godot -Z)
        s.location = tuple(G(cx, y, z0 - 0.0006))
        glow.append(s)
    g = M.join(glow, "lamp_glow")
    M.set_origin(g, tuple(G(wx, wy, wz)))
    return house, g


# ================================================================ interactive parts
def focus_ring():
    k = "k"
    prof = [(0.0372, RING_Z0), (0.0416, RING_Z0), (R_DIGIT_BAND, RING_Z0 + 0.0010), (R_DIGIT_BAND, 0.2345),
            (0.0429, 0.2368, k), (0.0429, 0.2558, k), (0.0372, RING_Z1)]
    ring = rev("focus_body", prof, AZP, (0, LY, 0), segments=40, mat="M_Lacquer_Black", knurl=0.0013,
               band_mats=["M_Lacquer_Black", "M_Lacquer_Black", "M_Lacquer_Black", "M_Chrome", "M_Chrome", "M_Chrome"],
               cap_bottom=False, cap_top=False)
    parts = [A.hint(ring, 25.0)]
    rr = R_DIGIT_BAND + 0.00012
    for d in range(9):
        phi = math.radians(90.0 + 30.0 * d)
        right = Vector((-math.sin(phi), 0.0, math.cos(phi)))
        up = Vector((0.0, -1.0, 0.0))
        nrm = Vector((math.cos(phi), 0.0, math.sin(phi)))
        frame = Matrix((right, up, nrm)).transposed().to_4x4()
        t = L.text_flat(f"fdigit{d}", str(d), 0.0122, font=L.FONT_SANS_B, res=2, mat="M_Enamel_White")
        L.recentre_xy(t)
        t.data.transform(Matrix.Translation(G(rr * math.cos(phi), LY + rr * math.sin(phi), 0.2268)) @ frame)
        parts.append(t)
        tick = L.flat_shape(f"ftick{d}", [L.rounded_rect(0.0008, 0.0030, 0.0002, 1)], mat="M_Enamel_White")
        tick.data.transform(Matrix.Translation(G(rr * math.cos(phi), LY + rr * math.sin(phi), 0.2177)) @ frame)
        parts.append(tick)
    A.presmooth(parts)
    o = M.join(parts, "IA_focus_ring")
    M.set_origin(o, tuple(G(0.0, LY, RING_C)))
    return o


def run_lever():
    px, py, pz = LEVER_P
    hub = rev("lever_hub", [(0.0140, 0.0), (0.0140, 0.0130), (0.0125, 0.0165), (0.0065, 0.0185), (0.0, 0.0188)],
              AXN, (px, py, pz), segments=16, mat="M_Chrome", cap_bottom=False)
    arm = L.curve_solid("lever_arm", [[(-0.0055, 0.0), (0.0055, 0.0), (0.0034, 0.082), (-0.0034, 0.082)]], 0.005,
                        bevel=0.0012, mat="M_Chrome")
    op_plate(arm, -0.0685, py, pz)
    knob = rev("lever_knob", [(0.0, -0.002), (0.0052, 0.0015), (0.0118, 0.0095), (0.0124, 0.0170), (0.0096, 0.0250),
                              (0.0, 0.0290)], AYP, (-0.0712, py + 0.078, pz), segments=16, mat="M_Bakelite")
    parts = [A.hint(hub, 50.0), arm, A.hint(knob, 60.0)]
    A.presmooth(parts)
    o = M.join(parts, "IA_run_lever")
    P = G(px, py, pz)
    o.data.transform(Matrix.Translation(P) @ Matrix.Rotation(math.radians(LEVER_REST), 4, "X") @ Matrix.Translation(-P))
    M.set_origin(o, tuple(P))
    return o


def frame_button(name, z, direction):
    cap = rev(name + "_cap", [(0.0108, 0.0), (0.0108, 0.0052), (0.0100, 0.0064), (0.0, 0.0066)], AXN,
              (OPF - 0.002, BTN_Y, z), segments=20, mat="M_Bakelite", cap_bottom=False)
    s = direction
    tri = [(-s * 0.0036, 0.0046), (-s * 0.0036, -0.0046), (s * 0.0046, 0.0)]
    arrow = L.curve_solid(name + "_arrow", [A.ccw(tri)], 0.0008, bevel=0.0002, mat="M_Enamel_White")
    op_plate(arrow, BTN_FACE + 0.0002, BTN_Y, z)
    parts = [A.hint(cap, 50.0), arrow]
    A.presmooth(parts)
    o = M.join(parts, name)
    M.set_origin(o, tuple(G(BTN_FACE, BTN_Y, z)))
    return o


def reel(name, centre):
    """Empty 16 mm reel (Ø 0.18), plane = local YZ, axle along X, three kidney windows per flange."""
    cx, cy, cz = centre
    parts = []
    loops = [L.circle(0.090, 36)]
    for kk in range(3):
        a0 = math.radians(90 + 120 * kk + 18)
        a1 = math.radians(90 + 120 * (kk + 1) - 18)
        loops.append(L.kidney(0.030, 0.078, a0, a1, n_arc=4))
    loops.append(L.circle(0.0050, 8))
    for s in (-1, 1):
        fl = L.curve_solid(name + "_flange", loops, 0.0012, bevel=0.0, mat="M_Chrome")
        C.side_plate(fl, cx + s * 0.0094 + 0.0006, -cz, cy, -1.0)
        parts.append(fl)
        rim = rev(name + "_rim", [(0.0900, -0.0006), (0.0912, 0.0), (0.0900, 0.0006)], AXN,
                  (cx + s * 0.0094, cy, cz), segments=36, mat="M_Chrome", cap_bottom=False, cap_top=False)
        parts.append(A.hint(rim, 60.0))
    parts.append(A.hint(rev(name + "_hub", [(0.0160, -0.0090), (0.0160, 0.0090)], AXN, (cx, cy, cz), segments=16,
                            mat="M_Steel_Dark", cap_bottom=False, cap_top=False), 60.0))
    parts.append(A.hint(rev(name + "_leader", [(0.0230, -0.0079), (0.0230, 0.0079)], AXN, (cx, cy, cz), segments=24,
                            mat="M_Film", cap_bottom=False, cap_top=False), 60.0))
    A.presmooth(parts)
    o = M.join(parts, name)
    M.set_origin(o, tuple(G(cx, cy, cz)))
    return o


# ================================================================ build / verify
def build():
    M.reset_scene()
    A.prepare_materials()
    C.ensure_materials()
    out = dict(pedestal=pedestal(), body=body())
    out["house"], out["glow"] = lamphouse()
    out["focus"] = focus_ring()
    out["lever"] = run_lever()
    out["prev"] = frame_button("IA_frame_prev", BTN_Z[0], -1.0)
    out["next"] = frame_button("IA_frame_next", BTN_Z[1], 1.0)
    out["takeup"] = reel("takeup_reel", TAKE_C)
    out["feed_mount"] = M.empty("feed_reel_mount", loc=tuple(G(*FEED_C)), rot=(0.0, 0.0, math.radians(-90.0)))
    out["lens"] = M.empty("lens_origin", loc=tuple(G(0.0, LY, LENS_FRONT)))
    A.finalize_uv()
    for k in ("pedestal", "body", "house"):
        print(f"[{NAME}]   {k:9s} {A.tris(out[k])}")
    print(f"[{NAME}] tris TOTAL={M.tri_count()}")
    return out


def verify() -> bool:
    exp = {
        "projector_pedestal": dict(parent=None, pos=(0, 0, 0)),
        "projector_body": dict(parent=None, pos=(0, 0, 0)),
        "projector_lamphouse": dict(parent=None, pos=(0, 0, 0)),
        "IA_focus_ring": dict(parent=None, pos=(0.0, LY, RING_C)),
        "IA_run_lever": dict(parent=None, pos=LEVER_P),
        "IA_frame_prev": dict(parent=None, pos=(BTN_FACE, BTN_Y, BTN_Z[0])),
        "IA_frame_next": dict(parent=None, pos=(BTN_FACE, BTN_Y, BTN_Z[1])),
        "takeup_reel": dict(parent=None, pos=TAKE_C),
        "feed_reel_mount": dict(parent=None, pos=FEED_C, identity=False),
        "lamp_glow": dict(parent=None, pos=WIN_C),
        "lens_origin": dict(parent=None, pos=(0.0, LY, LENS_FRONT)),
    }
    ok = C.verify_glb(NAME, exp, 9000)
    # the feed mount must be -90 deg about +Y: quaternion (0, -sin45, 0, cos45)
    doc = C._glb_json(os.path.join(M.MODELS_DIR, NAME + ".glb"))
    nd = next(n for n in doc["nodes"] if n.get("name") == "feed_reel_mount")
    q = nd.get("rotation", [0, 0, 0, 1])
    good = abs(q[0]) < 1e-4 and abs(q[2]) < 1e-4 and abs(q[1] + math.sqrt(0.5)) < 1e-4 and abs(q[3] - math.sqrt(0.5)) < 1e-4
    print(f"[verify]   {'ok ' if good else 'BAD'} feed_reel_mount rotation {tuple(round(v, 4) for v in q)} "
          f"(want -90 deg about +Y)")
    return ok and good


# ================================================================ QA
POS, YAW = (-2.9, 0.0, 2.65), 180.0


def world_of(local):
    """Model-local Godot point -> world Godot point (placement above)."""
    x, y, z = local
    return (POS[0] - x, y, POS[2] - z)


def pose(parts, run=False, focus=1):
    parts["lever"].rotation_euler = C.blender_rot_about_godot("X", 40.0 if run else 0.0)
    parts["focus"].rotation_euler = C.blender_rot_about_godot("Z", -30.0 * focus)


def lamp(parts, on):
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA_beam")]:
        bpy.data.objects.remove(o, do_unlink=True)
    g = parts["glow"]
    if not on:
        g.material_slots[0].material = bpy.data.materials["M_Glass_Amber"]
        return
    C.qa_emit(g, "FFE2B0", 9.0, base="FFC27A")
    M.refresh()
    inside = parts["house"].matrix_world @ G(0.095, 1.97, -0.20)
    A.qa_light("beam_lamp", "POINT", tuple(inside), 1.5, "FFD9A0", size=0.02)
    lens = parts["lens"].matrix_world.translation
    spot = A.qa_light("beam_spot", "SPOT", tuple(lens), 140.0, "FFF4E0", size=0.01, target=tuple(G(-2.5, 1.9, -3.43)),
                      spot=math.radians(22.0))
    spot.data.spot_blend = 0.25


def main():
    args = M.main_guard()
    parts = build()
    A.export_lean(NAME)
    ok = verify()
    print(f"[{NAME}] verify {'OK' if ok else 'FAILED'}")
    lens_w = world_of((0.0, LY, LENS_FRONT))
    for inset in (0.0, 0.04):
        C.beam_clearance(lens_w, aperture_r=0.035, inset=inset, label=f"film beam (frame inset {inset})")
    if "--no-render" in args:
        return
    want = set()
    for a in args:
        if a.startswith("--shot="):
            want |= set(a.split("=", 1)[1].split(","))

    def on(k):
        return not want or k in want
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    C.place(roots, POS, YAW)
    C.qa_room()
    C.qa_lights(booth_bulb=60.0, hall=60.0, fill=25.0)
    C.import_model("slide_projector", (-2.35, 0.0, 2.45), 180.0)
    C.import_model("booth_door", (-1.55, 0.0, 2.0), 180.0)
    C.qa_item("film_reel", parts["feed_mount"], C.proxy_film_reel)
    C.qa_glass_tweak()
    pose(parts, run=True, focus=5)
    lamp(parts, True)
    if on("1"):    # in-game projector view (contract camera): reel on, RUN, focus 5
        C.render(NAME, (-2.2, 1.75, 3.15), (-2.9, 1.5, 2.6), 50.0, res=(960, 540))
    if on("2"):    # recommended projector view (higher, aimed at the controls and the lens)
        C.render(NAME + "_2", (-2.22, 2.12, 3.12), (-2.86, 1.84, 2.52), 50.0, res=(960, 540))
    if on("3"):    # focus ring close-up: digit 5 under the index
        C.render(NAME + "_3", (-2.80, 2.13, 2.60), (-2.90, 1.95, 2.42), 34.0, res=(960, 640))
    if on("4"):    # hero: operator side, three-quarter from behind
        C.render(NAME + "_4", (-1.95, 1.95, 3.38), (-2.88, 1.55, 2.62), 48.0, res=(720, 900))
    if on("5"):    # from the hall through the booth window (lamp on)
        C.render(NAME + "_5", (-2.25, 1.70, 0.90), (-2.85, 1.95, 2.40), 40.0, res=(960, 640))
    if on("6"):    # rest: OFF, no reel, focus 1 (the spawned reel hidden)
        pose(parts, run=False, focus=1)
        lamp(parts, False)
        for o in bpy.context.scene.objects:
            if o.name.startswith("QA_item_") or o.name.startswith("QA_proxy_") or o.name.startswith("QA_reel"):
                o.hide_render = True
        C.render(NAME + "_6", (-2.22, 2.12, 3.12), (-2.86, 1.84, 2.52), 50.0, res=(960, 540))


main()
