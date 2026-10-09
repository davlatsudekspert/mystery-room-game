"""compressor_panel.glb — the air-supply panel of the pneumatic post (Archive B, east wall), puzzle P2.

A cream-enamel steel wall panel, 1.10 w x 1.30 h (y 0.65 .. 1.95), with:
  * two brass-bezel pressure gauges, P (left) and F (right): cream faces, a 3D scale 0..12 (value v at
    225 - 22.5 v degrees, counter-clockwise from +X seen from the front), big numbers at the even values,
    a tick for every integer, a green enamel wedge at P = 5 / F = 4 (+-0.35 units), the big letter P / F;
  * the piping-diagram plate (dark enamel with raised brass inlay lines): A -> P single, A -> F double,
    B -> P double, C -> F single, the letters A B C (bottom, over the valves) and P F (top, under the
    gauges) in brass rings at the line ends. No line crosses another;
  * three red cast handwheels A, B, C on brass bonnets, each over a fixed brass dial ring engraved 0..4
    (position k at 90 - 72 k degrees) with a brass pointer, and a letter plate below;
  * under it, on the floor, an electric compressor: tank on saddles, finned pump, motor with an exposed
    fan, belt guard, copper pipes rising into the panel, a drain cock and a cable to a wall box.

Model space (Godot): front +Z, origin on the wall plane at floor level (x = 0 = panel centre).
Placement: (5.0, 0, 0.8), yaw -90 (front faces world -X).
Parts (origin at the pivot, identity rotation at rest):
  needle_p, needle_f        pivot at the gauge centre on the face; rest points at 0 (225 deg);
                            code: -22.5 deg x value about local +Z
  IA_valve_a / _b / _c      handwheels at x = -0.32 / 0 / +0.32, y = 0.88; -72 deg x position about +Z
    pointer_a / _b / _c     child of each handwheel: the brass pointer (separate mesh so the wheel's own
                            mesh stays <= 0.15 m and gets a box collider)
  compressor_tank           tank + pump + motor body + belt guard (code shudders it)
    motor_pulley            child: motor shaft, pulley and fan; spins about local +X
    blender -b --factory-startup -P tools/blender/models/compressor_panel.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices1 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "compressor_panel"
BUDGET = 9000
PW, PH, PCY = 1.10, 1.30, 1.30          # panel width, height, centre y
FACE_Z = 0.090                          # panel front face
GAUGES = {"p": -0.25, "f": 0.25}
GY = 1.68
WEDGE = {"p": 5.0, "f": 4.0}
G_FACE_H = 0.012                        # dial face height over the panel face
NEEDLE_H = 0.0140                       # needle back face height over the panel face
VALVES = {"a": -0.32, "b": 0.0, "c": 0.32}
VY = 0.88
WHEEL_H = 0.050                         # handwheel plane over the panel face
PLATE = (-0.44, 0.44, 1.02, 1.42)       # piping plate x0, x1, y0, y1
PLATE_T = 0.004
SRC_Y, SNK_Y = 1.10, 1.34               # terminal ring centres on the plate
RING_R = 0.031
INLAY_MAT = "M_Brass_Polished"          # piping-plate lines, rings and letters (contract: brass inlay)
LINE_W, LINE_GAP = 0.006, 0.008         # inlay strip width; clear gap between the two strips of a double
POS_PULLEY = (0.0, 0.40, 0.335)         # motor axis point (x varies)


def ang_v(v: float) -> float:
    return 225.0 - 22.5 * v


# ---------------------------------------------------------------- cabinet
def build_cabinet():
    parts = []
    fr = C.front_frame(0.0, PCY, 0.006)
    shell = C.solid_g("cab_shell", [L.rounded_rect(PW, PH, 0.028, 4)], FACE_Z - 0.006, fr, bevel=0.007,
                      bevel_res=2, mat="M_Steel_Cream")
    C.sm(shell, 40.0)
    back = C.solid_g("cab_back", [L.rounded_rect(PW + 0.016, PH + 0.016, 0.034, 3)], 0.006,
                     C.front_frame(0.0, PCY, 0.0), bevel=0.0, mat="M_Steel_Dark", drop_bottom=True)
    C.sm(back, 40.0)
    parts += [shell, back]
    ff = C.front_frame(0.0, PCY, FACE_Z)
    # brass inlay border line 24 mm inside the edge, and a thin rule between the plate and the valves
    trim = C.shape_g("trim", L.outline_ring(PW - 0.048, PH - 0.048, 0.018, 0.0028, 4), ff, lift=0.0002,
                     mat="M_Brass_Aged")
    parts.append(trim)
    # corner screws
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(C.screw_g("cscrew", 0.0055, (sx * (PW / 2 - 0.040), PCY + sy * (PH / 2 - 0.040), FACE_Z),
                                   mat="M_Brass_Aged", slot=0.3 + 0.4 * sx + 0.2 * sy, segs=8))
    # maker's plate at the top centre
    np_fr = C.front_frame(0.0, 1.885, FACE_Z)
    plate = C.solid_g("nameplate", [L.rounded_rect(0.20, 0.036, 0.006, 2)], 0.002, np_fr, bevel=0.0,
                      mat="M_Brass_Polished")
    txt = C.text_g("name_txt", "AIR SUPPLY  ·  LINE B", 0.0125, np_fr, lift=0.0021, font=C.FONT_COND_B,
                   mat="M_Lacquer_Black", res=1)
    parts += [plate, txt]
    for sx in (-1, 1):
        parts.append(C.rivet_g("nprivet", 0.0028, (sx * 0.088, 1.885, FACE_Z + 0.002), mat="M_Brass_Aged", segs=6))
    # wall lugs top and bottom
    for sx in (-1, 1):
        for y in (PCY + PH / 2 + 0.004, PCY - PH / 2 - 0.004):
            lug = C.gbox("lug", (sx * 0.40 - 0.025, y - 0.012, 0.0), (sx * 0.40 + 0.025, y + 0.012, 0.012),
                         mat="M_Steel_Dark", bevel=0.0)
            parts.append(C.sm(lug, 30.0))
    return C.part("panel_body", parts, (0.0, 0.0, 0.0))


# ---------------------------------------------------------------- gauges
def build_gauge(key: str):
    gx = GAUGES[key]
    statics = []
    bez = C.revolve_g(f"bezel_{key}", [(0.117, 0.0), (0.119, 0.004), (0.119, 0.019), (0.115, 0.027),
                                       (0.108, 0.029), (0.102, 0.025), (0.102, 0.010)],
                      (0, 0, 1), (gx, GY, FACE_Z), segments=30, mat="M_Brass_Polished", cap_bottom=False,
                      cap_top=False)
    statics.append(C.sm(bez, 35.0))
    ff = C.front_frame(gx, GY, FACE_Z + G_FACE_H)
    face = C.shape_g(f"gface_{key}", [L.circle(0.1025, 32)], ff, mat="M_Enamel_Cream")
    statics.append(face)
    # green wedge (under the ticks)
    w0, w1 = ang_v(WEDGE[key] + 0.35), ang_v(WEDGE[key] - 0.35)
    statics.append(C.shape_g(f"wedge_{key}", [C.arc_band(0.071, 0.0935, w0, w1, 6)], ff, lift=0.0002,
                             mat="M_Enamel_Green"))
    # scale arc + ticks + numbers
    statics.append(C.shape_g("scale_arc", [C.arc_band(0.0925, 0.0943, ang_v(12) - 0.4, ang_v(0) + 0.4, 36)], ff,
                             lift=0.0004, mat="M_Lacquer_Black"))
    for v in range(13):
        major = v % 2 == 0
        r0 = 0.0795 if major else 0.0845
        statics.append(C.shape_g("tick", [C.radial_tick(r0, 0.0935, ang_v(v), 0.0024 if major else 0.0014)], ff,
                                 lift=0.0004, mat="M_Lacquer_Black"))
        if major:
            a = math.radians(ang_v(v))
            rr = 0.0625 if v < 10 else 0.0590
            statics.append(C.text_g("num", str(v), 0.0190, ff, u=rr * math.cos(a), v=rr * math.sin(a), lift=0.0004,
                                    font=C.FONT_SANS_B, mat="M_Lacquer_Black", res=1))
    # half-unit ticks are omitted on purpose: integer ticks only (contract)
    statics.append(C.text_g("letter", key.upper(), 0.034, ff, u=0.0, v=-0.040, lift=0.0004, font=C.FONT_SERIF_B,
                            mat="M_Lacquer_Black", res=1))
    # needle: pointer + counterweight + brass hub; rest at 0 (225 deg)
    nd = L.curve_solid("needle", [L.pointer_outline(0.0880, 0.020, shaft_w=0.0032, head_w=0.0068,
                                                     head_len=0.016, ball_r=0.0060)], 0.0012, bevel=0.0,
                       mat="M_Enamel_Crimson")
    nd.data.transform(Matrix.Rotation(math.radians(ang_v(0) - 90.0), 4, "Z"))
    hub = L.lathe2("nhub", [(0.0080, 0.0), (0.0080, 0.0020), (0.0060, 0.0040), (0.0025, 0.0050), (0.0, 0.0051)],
                   segments=10, mat="M_Brass_Polished", cap_bottom=False)
    hub.data.transform(Matrix.Translation((0, 0, 0.0005)))
    C.sm(nd, 30.0)
    C.sm(hub, 50.0)
    nf = C.front_frame(gx, GY, FACE_Z + NEEDLE_H)
    for o in (nd, hub):
        o.data.transform(nf)
    needle = C.part(f"needle_{key}", [nd, hub], (gx, GY, FACE_Z + NEEDLE_H))
    # glass (static, separate mesh)
    glass = C.shape_g(f"gglass_{key}", [L.circle(0.1035, 32)], C.front_frame(gx, GY, FACE_Z + 0.0235),
                      mat="M_Glass")
    return statics, needle, glass


# ---------------------------------------------------------------- piping-diagram plate
def plate_lines():
    """Centre paths of the inlay lines (plate coords = panel x, y). Returns [(path, double)]."""
    a, b, c = VALVES["a"], VALVES["b"], VALVES["c"]
    p, f = GAUGES["p"], GAUGES["f"]
    rr = RING_R + 0.0015
    lines = [
        # A -> P single: up from A's ring, then right into P's ring (left side)
        ([(a, SRC_Y + rr), (a, SNK_Y), (p - rr, SNK_Y)], False),
        # B -> P double: up from B, left, up into P's ring (bottom)
        ([(b, SRC_Y + rr), (b, 1.215), (p, 1.215), (p, SNK_Y - rr)], True),
        # C -> F single: up from C, then left into F's ring (right side)
        ([(c, SRC_Y + rr), (c, SNK_Y), (f + rr, SNK_Y)], False),
        # A -> F double: down from A's ring, right along the bottom (under B), up into F's ring (bottom)
        ([(a, SRC_Y - rr), (a, 1.047), (f, 1.047), (f, SNK_Y - rr)], True),
    ]
    return lines


def build_plate():
    x0, x1, y0, y1 = PLATE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    parts = []
    base = C.solid_g("plate", [L.rounded_rect(x1 - x0, y1 - y0, 0.012, 3)], PLATE_T, C.front_frame(cx, cy, FACE_Z),
                     bevel=0.0012, mat="M_Lacquer_Black")
    parts.append(C.sm(base, 40.0))
    pf = C.front_frame(0.0, 0.0, FACE_Z + PLATE_T)
    frame = C.solid_g("plate_frame", L.outline_ring(x1 - x0 - 0.016, y1 - y0 - 0.016, 0.008, 0.0035, 3), 0.0008,
                      pf, u=cx, v=cy, bevel=0.0, mat=INLAY_MAT, drop_bottom=True)
    parts.append(frame)
    h = 0.0009
    for path, double in plate_lines():
        if double:
            off = (LINE_GAP + LINE_W) / 2
            bands = [C.polyline_band(path, off - LINE_W / 2, off + LINE_W / 2),
                     C.polyline_band(path, -off - LINE_W / 2, -off + LINE_W / 2)]
        else:
            bands = [C.polyline_band(path, -LINE_W / 2, LINE_W / 2)]
        for bd in bands:
            parts.append(C.solid_g("inlay", [bd], h, pf, bevel=0.0, mat=INLAY_MAT, drop_bottom=True))
    # terminal rings with letters (sources bottom: A B C over the valves; sinks top: P F under the gauges)
    terms = [("A", VALVES["a"], SRC_Y), ("B", VALVES["b"], SRC_Y), ("C", VALVES["c"], SRC_Y),
             ("P", GAUGES["p"], SNK_Y), ("F", GAUGES["f"], SNK_Y)]
    for letter, tx, ty in terms:
        parts.append(C.shape_g("tring", L.circle_line(RING_R, 0.0034, 24), pf, u=tx, v=ty, lift=h,
                               mat=INLAY_MAT))
        parts.append(C.text_g("tletter", letter, 0.036, pf, u=tx, v=ty, lift=0.0004, font=C.FONT_SANS_B,
                              mat=INLAY_MAT, res=1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(C.rivet_g("privet", 0.0035, (cx + sx * (x1 - x0 - 0.026) / 2, cy + sy * (y1 - y0 - 0.026) / 2,
                                                       FACE_Z + PLATE_T), mat="M_Brass_Aged", segs=6))
    return C.part("piping_plate", parts, (0.0, 0.0, 0.0))


# ---------------------------------------------------------------- valves
def build_valve(key: str):
    vx = VALVES[key]
    statics = []
    ring = C.revolve_g(f"vring_{key}", [(0.113, 0.0), (0.113, 0.0035), (0.1115, 0.0048), (0.1085, 0.0048),
                                        (0.0855, 0.0048), (0.083, 0.0030), (0.083, 0.0)], (0, 0, 1),
                       (vx, VY, FACE_Z), segments=24, mat="M_Brass_Aged", cap_bottom=False, cap_top=False,
                       band_mats=[None, None, None, "M_Enamel_Cream", None, None])
    statics.append(C.sm(ring, 35.0))
    rf = C.front_frame(vx, VY, FACE_Z + 0.0048)
    for k in range(5):
        a = math.radians(90.0 - 72.0 * k)
        statics.append(C.text_g("vnum", str(k), 0.0205, rf, u=0.0985 * math.cos(a), v=0.0985 * math.sin(a),
                                lift=0.0003, font=C.FONT_SANS_B, mat="M_Lacquer_Black", res=1))
        statics.append(C.shape_g("vtick", [C.radial_tick(0.0850, 0.0885, 90.0 - 72.0 * k, 0.0018)], rf, lift=0.0003,
                                 mat="M_Lacquer_Black"))
    # bonnet: hex gland nut + packing nut + stem
    nut = C.revolve_g("gland", [(0.024, 0.0), (0.024, 0.011), (0.021, 0.013), (0.0, 0.013)], (0, 0, 1),
                      (vx, VY, FACE_Z), segments=6, mat="M_Brass_Aged", cap_bottom=False)
    statics.append(C.sm(nut, 20.0))
    pk = C.revolve_g("packing", [(0.015, 0.013), (0.015, 0.022), (0.012, 0.025), (0.0, 0.025)], (0, 0, 1),
                     (vx, VY, FACE_Z), segments=10, mat="M_Brass_Polished", cap_bottom=False)
    statics.append(C.sm(pk, 40.0))
    stem = C.revolve_g("stem", [(0.0065, 0.025), (0.0065, WHEEL_H - 0.010)], (0, 0, 1), (vx, VY, FACE_Z),
                       segments=8, mat="M_Chrome", cap_bottom=False, cap_top=False)
    statics.append(C.sm(stem, 60.0))
    # letter plate under the valve
    lp_fr = C.front_frame(vx, 0.733, FACE_Z)
    lp = C.solid_g("lplate", [L.rounded_rect(0.066, 0.050, 0.007, 2)], 0.002, lp_fr, bevel=0.0,
                   mat="M_Brass_Polished")
    lt = C.text_g("lplate_txt", key.upper(), 0.038, lp_fr, lift=0.0021, font=C.FONT_SANS_B, mat="M_Lacquer_Black",
                  res=1)
    statics += [lp, lt]
    for sx in (-1, 1):
        statics.append(C.rivet_g("lrivet", 0.0024, (vx + sx * 0.026, 0.733 + 0.016, FACE_Z + 0.002), segs=6))

    # handwheel (IA): rim + 5 dished spokes + hub with a brass nut and a cream index line
    wf = C.front_frame(vx, VY, FACE_Z + WHEEL_H)
    rim = M.torus("rim", 0.0663, 0.0072, major_seg=20, minor_seg=5, mat="M_Enamel_Crimson")
    rim.data.transform(Matrix.Translation((0, 0, -0.004)))
    C.sm(rim, 70.0)
    wheel = [rim]
    for k in range(5):
        a = math.radians(90.0 + 36.0 + 72.0 * k)      # spokes between the 12 o'clock pointer positions
        ca, sa = math.cos(a), math.sin(a)
        pts = [(0.012 * ca, 0.012 * sa, 0.006), (0.036 * ca, 0.036 * sa, 0.002), (0.062 * ca, 0.062 * sa, -0.004)]
        sp = C.A.tube("spoke", pts, 0.0048, sides=6, mat="M_Enamel_Crimson", caps=False)
        C.sm(sp, 70.0)
        wheel.append(sp)
    hub = L.lathe2("hub", [(0.0140, -0.012), (0.0165, -0.006), (0.0165, 0.010), (0.0140, 0.014), (0.0, 0.014)],
                   segments=10, mat="M_Enamel_Crimson", cap_bottom=False)
    C.sm(hub, 45.0)
    hnut = L.lathe2("hnut", [(0.0085, 0.014), (0.0085, 0.020), (0.0065, 0.022), (0.0, 0.022)], segments=6,
                    mat="M_Brass_Polished", cap_bottom=False)
    C.sm(hnut, 20.0)
    idx = L.flat_shape("hidx", [L.rounded_rect(0.0030, 0.0055, 0.001, 2, cy=0.0108)], mat="M_Enamel_Cream")
    idx.data.transform(Matrix.Translation((0, 0, 0.0141)))
    wheel += [hub, hnut, idx]
    for o in wheel:
        o.data.transform(wf)
    ia = C.part(f"IA_valve_{key}", wheel, (vx, VY, FACE_Z + WHEEL_H))
    # pointer (child): post from the rim back to a pointed plate over the dial ring's inner edge
    tip = 0.0870
    plate = L.curve_solid("ptr", [[(-0.0055, 0.0600), (0.0055, 0.0600), (0.0016, tip - 0.003), (0.0, tip),
                                    (-0.0016, tip - 0.003)]], 0.0016, bevel=0.0003, mat="M_Brass_Polished")
    plate.data.transform(Matrix.Translation((0, 0, -WHEEL_H + 0.0090)))
    post = L.box_mm("ptr_post", (-0.0028, 0.0600, -WHEEL_H + 0.0095), (0.0028, 0.0660, -0.006),
                    mat="M_Brass_Polished", bevel=0.0006)
    C.sm(plate, 30.0)
    C.sm(post, 30.0)
    for o in (plate, post):
        o.data.transform(wf)
    ptr = C.part(f"pointer_{key}", [plate, post], (vx, VY, FACE_Z + WHEEL_H))
    C.parent(ptr, ia)
    return statics, ia


# ---------------------------------------------------------------- compressor on the floor
def obround(c0, r0, c1, r1, n=10):
    """Convex hull outline of two circles (2D, CCW)."""
    pts = L.circle(r0, 3 * n, cx=c0[0], cy=c0[1]) + L.circle(r1, 3 * n, cx=c1[0], cy=c1[1])
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def build_compressor():
    tank_parts = []
    TY, TZ, TR, TL = 0.205, 0.215, 0.125, 0.70
    # tank: cylinder along X with dished ends, a weld seam band and a data plate
    prof = [(0.0, -TL / 2 - 0.040), (0.060, -TL / 2 - 0.034), (0.100, -TL / 2 - 0.018), (TR - 0.006, -TL / 2 - 0.003),
            (TR, -TL / 2 + 0.006), (TR, -0.006), (TR + 0.0025, -0.003), (TR + 0.0025, 0.003), (TR, 0.006),
            (TR, TL / 2 - 0.006), (TR - 0.006, TL / 2 + 0.003), (0.100, TL / 2 + 0.018), (0.060, TL / 2 + 0.034),
            (0.0, TL / 2 + 0.040)]
    tank = C.revolve_g("tank", prof, (1, 0, 0), (0.0, TY, TZ), segments=16, mat="M_Steel_Painted")
    tank_parts.append(C.sm(tank, 40.0))
    # saddle feet with rubber pads
    for sx in (-1, 1):
        x = sx * 0.235
        sad = C.gbox("saddle", (x - 0.022, 0.012, TZ - 0.105), (x + 0.022, TY - 0.07, TZ + 0.105), mat="M_Steel_Dark",
                     bevel=0.0)
        pad = C.gbox("pad", (x - 0.030, 0.0, TZ - 0.115), (x + 0.030, 0.012, TZ + 0.115), mat="M_Rubber", bevel=0.0)
        tank_parts += [C.sm(sad, 30.0), C.sm(pad, 30.0)]
    # drain cock under the tank, safety valve with a ring on top-left
    tank_parts.append(C.sm(C.revolve_g("drain", [(0.010, 0.0), (0.010, 0.020), (0.006, 0.024), (0.006, 0.034),
                                                  (0.0, 0.036)], (0, -1, 0), (-0.10, TY - TR + 0.002, TZ + 0.04),
                                       segments=6, mat="M_Brass_Aged"), 30.0))
    sv = C.revolve_g("safety", [(0.011, 0.0), (0.011, 0.016), (0.008, 0.020), (0.008, 0.045), (0.004, 0.052),
                                (0.0, 0.053)], (0, 1, 0), (-0.29, TY + TR - 0.012, TZ), segments=6, mat="M_Brass_Aged")
    tank_parts.append(C.sm(sv, 40.0))
    # pump: crankcase, finned cylinder, head with bolts (behind the motor)
    PX, PZ = 0.03, 0.150
    cc = C.gbox("crankcase", (PX - 0.085, TY + TR - 0.018, PZ - 0.075), (PX + 0.085, 0.445, PZ + 0.075),
                mat="M_Steel_Dark", bevel=0.008)
    tank_parts.append(C.sm(cc, 35.0))
    fins = [(0.050, 0.445)]
    y = 0.452
    for k in range(3):
        fins += [(0.050, y), (0.070, y + 0.003), (0.070, y + 0.013), (0.050, y + 0.016)]
        y += 0.034
    fins += [(0.050, 0.560), (0.0, 0.560)]
    cyl = C.revolve_g("pump_cyl", [(r, h - 0.445) for (r, h) in fins], (0, 1, 0), (PX, 0.445, PZ), segments=10,
                      mat="M_Steel_Dark", cap_bottom=False)
    tank_parts.append(C.sm(cyl, 40.0))
    head = C.gbox("pump_head", (PX - 0.062, 0.560, PZ - 0.062), (PX + 0.062, 0.592, PZ + 0.062), mat="M_Steel_Dark",
                  bevel=0.006)
    tank_parts.append(C.sm(head, 35.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            tank_parts.append(C.sm(C.revolve_g("hbolt", [(0.006, 0.0), (0.006, 0.007), (0.0, 0.008)], (0, 1, 0),
                                               (PX + sx * 0.045, 0.592, PZ + sz * 0.045), segments=6,
                                               mat="M_Chrome", cap_bottom=False), 20.0))
    # electric motor (along X, in front of the pump) with end bells and a terminal box
    MY, MZ = POS_PULLEY[1], POS_PULLEY[2]
    mot = C.revolve_g("motor", [(0.040, -0.140), (0.058, -0.136), (0.064, -0.122), (0.064, 0.100),
                                (0.058, 0.112), (0.036, 0.118), (0.020, 0.122)], (1, 0, 0), (0.0, MY, MZ),
                      segments=16, mat="M_Steel_Painted", cap_bottom=False, cap_top=False)
    tank_parts.append(C.sm(mot, 40.0))
    tb = C.gbox("termbox", (-0.040, MY + 0.050, MZ - 0.035), (0.030, MY + 0.085, MZ + 0.025), mat="M_Steel_Painted",
                bevel=0.004)
    tank_parts.append(C.sm(tb, 30.0))
    mount_plate = C.gbox("mplate", (-0.150, TY + TR - 0.010, MZ - 0.055), (0.130, MY - 0.050, MZ + 0.055),
                         mat="M_Steel_Dark", bevel=0.003)
    tank_parts.append(C.sm(mount_plate, 30.0))
    # fan guard ring at the -X end (the fan itself is part of motor_pulley)
    fgr = M.torus("fanguard", 0.058, 0.0028, major_seg=16, minor_seg=3, mat="M_Chrome")
    fgr.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    fgr.data.transform(Matrix.Translation(C.G(-0.172, MY, MZ)))
    tank_parts.append(C.sm(fgr, 70.0))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        st = C.A.tube("fstrut", [tuple(C.G(-0.172, MY + 0.058 * math.sin(a), MZ + 0.058 * math.cos(a))),
                                 tuple(C.G(-0.128, MY + 0.060 * math.sin(a), MZ + 0.060 * math.cos(a)))], 0.0025,
                      sides=4, mat="M_Chrome", caps=False)
        tank_parts.append(C.sm(st, 70.0))
    # belt guard at the +X end: a sheet-metal box enclosing the motor pulley, the belt and the pump flywheel
    fly_c = (0.150, 0.500)            # (z, y) of the pump crankshaft
    gd = obround((MZ, MY), 0.058, fly_c, 0.118, 6)
    gfr = C.gframe((0.120, 0.0, 0.0), (0, 0, -1), (0, 1, 0))         # u = -z, v = y, out of the face = +x
    guard = C.solid_g("beltguard", [[(-z, y) for (z, y) in gd]], 0.092, gfr, bevel=0.006, bevel_res=0,
                      mat="M_Steel_Cream")
    tank_parts.append(C.sm(guard, 40.0))
    lfr = C.gframe((0.2122, 0.0, 0.0), (0, 0, -1), (0, 1, 0))
    for k in range(4):
        tank_parts.append(C.shape_g("louvre", [L.rounded_rect(0.085, 0.007, 0.0034, 3)], lfr, u=-0.185,
                                    v=0.455 + 0.024 * k, lift=0.0, mat="M_Steel_Dark"))
    for (z, y) in ((MZ, MY), fly_c):
        tank_parts.append(C.sm(C.revolve_g("gnut", [(0.010, 0.0), (0.010, 0.006), (0.0, 0.007)], (1, 0, 0),
                                            (0.212, y, z), segments=6, mat="M_Chrome", cap_bottom=False), 20.0))
    tank = C.part("compressor_tank", tank_parts, (0.0, TY, TZ))

    # motor_pulley: shaft + V pulley (+X end, under the guard) + 6-blade fan (-X end)
    mp = []
    shaft = C.revolve_g("shaft", [(0.007, -0.170), (0.007, 0.168)], (1, 0, 0), (0.0, MY, MZ), segments=8,
                        mat="M_Chrome", cap_bottom=True, cap_top=True)
    mp.append(C.sm(shaft, 60.0))
    pul = C.revolve_g("pulley", [(0.010, 0.124), (0.036, 0.124), (0.026, 0.138), (0.036, 0.152),
                                 (0.010, 0.152)], (1, 0, 0), (0.0, MY, MZ), segments=8,
                      mat="M_Steel_Dark", cap_bottom=False, cap_top=False)
    mp.append(C.sm(pul, 40.0))
    fhub = C.revolve_g("fanhub", [(0.0, -0.162), (0.014, -0.160), (0.016, -0.150), (0.016, -0.142)], (1, 0, 0),
                       (0.0, MY, MZ), segments=10, mat="M_Steel_Dark", cap_top=False)
    mp.append(C.sm(fhub, 45.0))
    for k in range(6):
        a = math.radians(60 * k)
        bl = L.curve_solid("blade", [[(0.012, -0.010), (0.052, -0.016), (0.054, 0.014), (0.012, 0.008)]], 0.0016,
                           bevel=0.0, mat="M_Steel_Painted")
        bl.data.transform(Matrix.Rotation(math.radians(20), 4, "X"))       # pitch
        bl.data.transform(Matrix.Rotation(a, 4, "Z"))
        bl.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))           # blade plane faces X
        bl.data.transform(Matrix.Translation(C.G(-0.152, MY, MZ)))
        mp.append(C.sm(bl, 30.0))
    pulley = C.part("motor_pulley", mp, (0.0, MY, MZ))
    C.parent(pulley, tank)
    return tank, pulley


def build_pipes():
    parts = []
    # copper delivery pipe: pump head -> up into the panel bottom (with a union nut)
    parts.append(C.gtube("pipe1", [(0.03 + 0.0, 0.592, 0.150), (0.03, 0.618, 0.150), (0.11, 0.618, 0.150),
                                   (0.11, 0.618, 0.055), (0.11, 0.652, 0.055)], 0.0075, sides=6, fillet=0.018))
    # copper line from a tee on the tank (with a pressure switch) up into the panel
    parts.append(C.gtube("pipe2", [(-0.20, 0.330, 0.215), (-0.20, 0.47, 0.215), (-0.20, 0.47, 0.055),
                                   (-0.20, 0.652, 0.055)], 0.0075, sides=6, fillet=0.030))
    sw = C.gbox("pswitch", (-0.245, 0.43, 0.20), (-0.155, 0.50, 0.255), mat="M_Steel_Cream", bevel=0.006)
    parts.append(C.sm(sw, 30.0))
    swl = C.text_g("pswitch_txt", "6 bar", 0.010, C.front_frame(-0.20, 0.465, 0.255), lift=0.0002,
                   font=C.FONT_COND_B, mat="M_Lacquer_Black", res=1)
    parts.append(swl)
    # brass glands where the pipes enter the panel bottom
    for x in (0.11, -0.20):
        parts.append(C.sm(C.revolve_g("gland", [(0.014, 0.0), (0.014, 0.014), (0.0, 0.014)], (0, 1, 0),
                                       (x, 0.636, 0.055), segments=6, mat="M_Brass_Aged", cap_bottom=False), 20.0))
    # tank tee
    parts.append(C.sm(C.revolve_g("tee", [(0.013, 0.0), (0.013, 0.022), (0.0, 0.022)], (0, 1, 0),
                                   (-0.20, 0.320, 0.215), segments=6, mat="M_Brass_Aged", cap_bottom=False), 20.0))
    # power cable from the motor terminal box to a wall junction box
    jb = C.gbox("jbox", (0.36, 0.38, 0.0), (0.46, 0.48, 0.045), mat="M_Steel_Dark", bevel=0.004)
    parts.append(C.sm(jb, 30.0))
    parts.append(C.screw_g("jscrew", 0.004, (0.41, 0.43, 0.045), mat="M_Chrome", segs=6))
    cable = L.tube("cable", [tuple(C.G(0.0, 0.485, 0.335)), tuple(C.G(0.10, 0.52, 0.30)), tuple(C.G(0.25, 0.45, 0.20)),
                             tuple(C.G(0.33, 0.43, 0.06)), tuple(C.G(0.36, 0.43, 0.025))], 0.006, mat="M_Rubber",
                   bevel_res=1, res_u=2)
    parts.append(C.sm(cable, 60.0))
    return C.part("compressor_pipes", parts, (0.0, 0.0, 0.0))


def build():
    C.ensure_materials()
    build_cabinet()
    glass = []
    for k in GAUGES:
        statics, needle, g = build_gauge(k)
        C.part(f"gauge_{k}", statics, (GAUGES[k], GY, FACE_Z))
        glass.append(g)
    C.part("gauge_glass", glass, (0.0, GY, FACE_Z))
    build_plate()
    for k in VALVES:
        statics, ia = build_valve(k)
        C.part(f"valve_{k}_body", statics, (VALVES[k], VY, FACE_Z))
    build_compressor()
    build_pipes()


def main():
    M.reset_scene()
    build()
    C.finalize()
    C.report(NAME, BUDGET)
    C.export(NAME)
    exp = {
        "needle_p": dict(parent=None, pos=(GAUGES["p"], GY, FACE_Z + NEEDLE_H)),
        "needle_f": dict(parent=None, pos=(GAUGES["f"], GY, FACE_Z + NEEDLE_H)),
        "compressor_tank": dict(parent=None),
        "motor_pulley": dict(parent="compressor_tank"),
    }
    for k, x in VALVES.items():
        exp[f"IA_valve_{k}"] = dict(parent=None, pos=(x, VY, FACE_Z + WHEEL_H))
        exp[f"pointer_{k}"] = dict(parent=f"IA_valve_{k}", pos=(0.0, 0.0, 0.0))
    C.verify_glb(NAME, exp, BUDGET)
    for k in VALVES:
        o = M.bpy.data.objects[f"IA_valve_{k}"]
        lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
        print(f"{C.TAG} IA_valve_{k} mesh AABB {tuple(round(h - l, 4) for l, h in zip(lo, hi))} (box collider if <= 0.15)")
    if not C.want_render():
        return
    qa()


def pose_solved(on: bool):
    vals = {"a": 1, "b": 2, "c": 2} if on else {"a": 0, "b": 0, "c": 0}
    for k, v in vals.items():
        o = M.bpy.data.objects[f"IA_valve_{k}"]
        o.matrix_basis = Matrix.Translation(o.matrix_basis.translation)
        C.pose_rot(o, "z", -72.0 * v)
    p = vals["a"] + 2 * vals["b"]
    f = 2 * vals["a"] + vals["c"]
    for k, v in (("p", p), ("f", f)):
        o = M.bpy.data.objects[f"needle_{k}"]
        o.matrix_basis = Matrix.Translation(o.matrix_basis.translation)
        C.pose_rot(o, "z", -22.5 * v)


def qa():
    C.qa_tweak()
    args = C.qa_args()
    shots = None
    for a in args:
        if a.startswith("--shots="):
            shots = set(a.split("=", 1)[1].split(","))

    def want(n):
        return shots is None or n in shots
    roots = C.model_roots()
    # hero in a studio (model space)
    if want("1"):
        C.studio(NAME, tuple(C.G(0.95, 1.55, 2.05)), tuple(C.G(0.0, 1.05, 0.10)), lens=32, floor_z=0.0)
    if want("2"):
        C.studio(NAME + "_2", tuple(C.G(0.0, 1.30, 0.95)), tuple(C.G(0.0, 1.28, 0.09)), lens=30, floor_z=0.0)
    # in the room: compressor view (rest), solved pose (valves 1-2-2, P = 5, F = 4), hall angle, valve close-up
    place(roots)
    C.qa_room()
    C.qa_hall_lights()
    if want("3"):
        C.render(NAME + "_3", (3.65, 1.45, 0.8), (5.0, 1.25, 0.8), 52.0)
    pose_solved(True)
    if want("4"):
        C.render(NAME + "_4", (3.65, 1.45, 0.8), (5.0, 1.25, 0.8), 52.0)
    if want("5"):
        C.render(NAME + "_5", (3.2, 1.15, 1.9), (5.0, 0.75, 0.6), 50.0)
    if want("6"):
        C.render(NAME + "_6", (4.35, 1.12, 0.8), (5.0, 0.86, 0.8), 40.0)
    if want("7"):
        C.render(NAME + "_7", (4.40, 1.62, 0.8), (5.0, 1.62, 0.8), 40.0)


def place(roots):
    return C.place(roots, (5.0, 0.0, 0.8), -90.0)


main()
