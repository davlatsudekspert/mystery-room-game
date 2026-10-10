"""booth.glb — Strand's raised glass booth: legs, glass, the stair along the front with its stair gate, the stopped wall clock (Chapter 4, group F).
Contract: docs/models/ch4.md section 8 booth; results: docs/models/ch4_f.md.

LOCAL FRAME: placed at (0, 0, -13.0), yaw 0 (world = local + (0, 0, -13)); the front faces +Z (south, the hall). Floor y = 2.0, roof y = 4.7, x +-3.2,
z -0.9 (back, against the hall wall) .. +1.1 (the front glass). The desk stands at local (0, 2.0, -0.4).
Nodes:
  booth             M_Steel_Dark + M_Glass + M_Chequer + M_Brass_Aged  everything static: six legs with X braces and floor beams, the riveted fascia, the dado,
                    mullions and the glass (front, two sides, the door), the roof with its vent, the chequer floor, the stair (11 steps, treads in chequer plate,
                    brass nosings and handrails), the landing and the door at the east end of the front, the gate frame (south post), the back wall and the
                    stopped wall clock 03:17 (brass bezel, hour bars and hands on a dark dial)
  IA_booth_gate     M_Brass_Aged  the stair gate: a collapsible lattice leaf + the north post + a lock box with the Institute's mark and a key slot.
                    ORIGIN = the north post (0, 0, 1.5), the lattice runs from there along +Z to z = 2.3. Closed = identity; OPEN = scale local Z to 0.15
                    about the origin (the lattice folds against the post). The lock box sits ON the origin plane, so it squashes flat instead of drifting
    booth_key_mount child of IA_booth_gate, on the slot of the lock box; rotated so that the item's -Z (the bow) points +Y and its +Y (the face) points +Z
  empties: booth_lamp (0, 4.25, 0.10), desk_mount (0, 2.0, -0.4)

    blender -b --factory-startup -P tools/blender/models/booth.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
import lib_ch4_fgh as F  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL, CHEQ, GLASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "booth"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 10000, 9, 4
FY, ROOF = 2.0, 4.7
XW = 3.2
ZB, ZF = -0.9, 1.1
DADO = 2.55
GLASS_TOP = 4.55
N_STEPS = 11
RISE = FY / N_STEPS
RUN = 0.22
STAIR_X1 = N_STEPS * RUN              # 2.42
LANE_N, LANE_S = 1.5, 2.3             # the stair lane (z), the gate's north post is on LANE_N
GATE_ORIGIN = (0.0, 0.0, LANE_N)
CLOCK_C = (0.0, 3.95, ZB + 0.04)      # on the back wall panel's front face
SLOT_TOP = 1.38
MULL_X = [-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4]
DOOR_X0, DOOR_X1 = 2.4, 3.2


def tread_y(i: int) -> float:
    """Top of the tread of step i (0 = the first step at the foot)."""
    return (i + 1) * RISE


# ====================================================================== static meshes
def steel_parts():
    s = F.MB(STEEL)
    b = s.bm
    # --- legs with base and cap plates
    for x in (-3.0, 0.0, 3.0):
        for z in (-0.72, 0.92):
            s.box((x - 0.15, 0.0, z - 0.15), (x + 0.15, 0.03, z + 0.15))
            s.box((x - 0.08, 0.03, z - 0.08), (x + 0.08, 1.80, z + 0.08))
            s.box((x - 0.12, 1.80, z - 0.12), (x + 0.12, 1.84, z + 0.12))
            for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                b2 = (x + sx * 0.11, 0.03, z + sz * 0.11)
                s.dome(b2, 0.016, 0.014, segs=5, normal=(0, 1, 0))
    # --- X braces in the front plane (z 0.92) and the two side planes (x +-3.0)
    for (xa, xb) in ((-3.0, 0.0), (0.0, 3.0)):
        s.bar((xa + 0.12, 0.12, 0.92), (xb - 0.12, 1.74, 0.92), 0.045, ref=(0, 0, 1))
        s.bar((xa + 0.12, 1.74, 0.92), (xb - 0.12, 0.12, 0.92), 0.045, ref=(0, 0, 1))
    for x in (-3.0, 3.0):
        s.bar((x, 0.12, -0.60), (x, 1.74, 0.80), 0.045, ref=(1, 0, 0))
        s.bar((x, 1.74, -0.60), (x, 0.12, 0.80), 0.045, ref=(1, 0, 0))
    # --- floor beams: along X at the two leg rows, across at the three leg columns (webs and flanges)
    for z in (-0.72, 0.92):
        s.box((-3.2, 1.84, z - 0.07), (3.2, 1.86, z + 0.07))
        s.box((-3.2, 1.86, z - 0.012), (3.2, 1.92, z + 0.012))
        s.box((-3.2, 1.92, z - 0.07), (3.2, 1.94, z + 0.07))
    for x in (-3.0, 0.0, 3.0):
        s.box((x - 0.012, 1.86, ZB), (x + 0.012, 1.92, ZF))
        s.box((x - 0.06, 1.92, ZB), (x + 0.06, 1.94, ZF))
    # --- the riveted fascia round the floor (front and both sides), with a rivet row
    s.box((-XW, 1.70, ZF - 0.05), (XW, 1.94, ZF))
    s.box((-XW, 1.70, ZB), (-XW + 0.05, 1.94, ZF - 0.05))
    s.box((XW - 0.05, 1.70, ZB), (XW, 1.94, ZF - 0.05))
    for i in range(33):
        x = -3.1 + 0.19 * i
        s.dome((x, 1.82, ZF), 0.017, 0.015, segs=5, normal=(0, 0, 1))
    for z in (-0.6, -0.2, 0.2, 0.6):
        s.dome((-XW, 1.82, z), 0.017, 0.015, segs=5, normal=(-1, 0, 0))
        s.dome((XW, 1.82, z), 0.017, 0.015, segs=5, normal=(1, 0, 0))
    # --- the booth frame: corner posts, front and side mullions, the dado panels, the head beam
    for x in (-XW + 0.05, XW - 0.05):
        for z in (ZB + 0.05, ZF - 0.05):
            s.box((x - 0.05, FY, z - 0.05), (x + 0.05, GLASS_TOP, z + 0.05))
    for x in MULL_X:
        s.box((x - 0.03, FY, ZF - 0.05), (x + 0.03, GLASS_TOP, ZF + 0.01))
    for sx in (-1, 1):
        s.box((sx * XW - 0.03 - (0.0 if sx > 0 else -0.0), FY, 0.07), (sx * XW + 0.03, GLASS_TOP, 0.13))
    # dado: a continuous panel with a raised frame in every bay of the front
    s.box((-XW, FY, ZF - 0.05), (DOOR_X0, DADO, ZF - 0.02))
    s.box((-XW + 0.05, FY, ZB), (-XW + 0.08, DADO, ZF - 0.05))
    s.box((XW - 0.08, FY, ZB), (XW - 0.05, DADO, ZF - 0.05))
    edges = [-XW] + MULL_X
    for k in range(len(edges) - 1):
        xa, xb = edges[k] + 0.09, edges[k + 1] - 0.09
        for (x0, y0, x1, y1) in ((xa, 2.07, xb, 2.10), (xa, 2.45, xb, 2.48), (xa, 2.10, xa + 0.03, 2.45), (xb - 0.03, 2.10, xb, 2.45)):
            s.box((x0, y0, ZF - 0.02), (x1, y1, ZF + 0.004))
    for i in range(30):
        x = -3.05 + 0.19 * i
        if x < DOOR_X0 - 0.1:
            s.dome((x, 2.52, ZF - 0.02), 0.014, 0.012, segs=5, normal=(0, 0, 1))
    # back wall panel and the head beam under the roof
    s.box((-XW, FY, ZB - 0.01), (XW, GLASS_TOP, ZB + 0.04))
    s.box((-XW, GLASS_TOP - 0.06, ZF - 0.08), (XW, GLASS_TOP, ZF + 0.01))
    s.box((-XW, GLASS_TOP - 0.06, ZB), (-XW + 0.06, GLASS_TOP, ZF))
    s.box((XW - 0.06, GLASS_TOP - 0.06, ZB), (XW, GLASS_TOP, ZF))
    # --- roof: slab, upstand, vent box with a stack
    s.box((-XW - 0.12, GLASS_TOP, ZB - 0.05), (XW + 0.12, ROOF, ZF + 0.12))
    s.box((-0.45, ROOF, -0.35), (0.45, ROOF + 0.20, 0.15))
    s.box((-0.50, ROOF + 0.20, -0.40), (0.50, ROOF + 0.23, 0.20))
    s.cyl((1.55, ROOF, -0.2), (0, 1, 0), 0.09, 0.42, segs=10)
    s.cyl((1.55, ROOF + 0.42, -0.2), (0, 1, 0), 0.13, 0.04, segs=10)
    for x in (-2.6, -1.6, 1.6, 2.6):
        s.box((x - 0.03, ROOF, ZF - 0.05), (x + 0.03, ROOF + 0.05, ZF + 0.08))
    # inside: ceiling lamp (a shade on a stem)
    s.cyl((0.0, GLASS_TOP, 0.10), (0, -1, 0), 0.02, 0.18, segs=8)
    s.cyl((0.0, GLASS_TOP - 0.18, 0.10), (0, -1, 0), 0.07, 0.12, segs=14, r2=0.20)
    # --- door: frame, glass pane frame (steel), hinge side at the east post
    s.box((DOOR_X0 + 0.0, FY, ZF - 0.05), (DOOR_X0 + 0.05, 4.40, ZF + 0.02))
    s.box((DOOR_X0, 4.40, ZF - 0.05), (DOOR_X1, 4.50, ZF + 0.02))
    # door leaf: stiles, rails around a pane (the pane is glass)
    for (x0, y0, x1, y1) in ((DOOR_X0 + 0.05, 2.10, DOOR_X0 + 0.12, 4.38), (DOOR_X1 - 0.12, 2.10, DOOR_X1 - 0.05, 4.38),
                             (DOOR_X0 + 0.12, 2.10, DOOR_X1 - 0.12, 2.55), (DOOR_X0 + 0.12, 4.30, DOOR_X1 - 0.12, 4.38)):
        s.box((x0, y0, ZF - 0.04), (x1, y1, ZF + 0.03))
    # --- the stair: north / south stringers (side plates), risers
    for (z0, z1) in ((LANE_N - 0.04, LANE_N), (LANE_S, LANE_S + 0.04)):
        # a channel stringer: a strip 0.24 deep under the nosing line (the stair stays open underneath)
        pts = [(0.0, 0.0), (0.107, 0.0), (STAIR_X1, FY - 0.27), (STAIR_X1, FY - 0.03), (0.0, tread_y(0) - 0.03)]
        s.prism(pts, z0, z1)
        for x in (0.9, 1.9):                                       # trestle legs under the stringers
            yb = tread_y(0) - 0.27 + (FY - tread_y(0)) * x / STAIR_X1
            s.box((x - 0.04, 0.0, z0 - 0.0), (x + 0.04, yb + 0.01, z1 + (0.0 if z0 > LANE_N else 0.0)))
    for i in range(N_STEPS):
        s.box((i * RUN, i * RISE, LANE_N), ((i * RUN) + 0.014, tread_y(i) - 0.04, LANE_S))
    # landing structure: a beam under the landing slab and two legs
    s.box((STAIR_X1, FY - 0.14, ZF), (3.4, FY - 0.06, LANE_S + 0.04))
    for (x, z) in ((3.3, ZF + 0.05), (3.3, LANE_S - 0.02)):
        s.box((x - 0.05, 0.0, z - 0.05), (x + 0.05, FY - 0.14, z + 0.05))
        s.box((x - 0.09, 0.0, z - 0.09), (x + 0.09, 0.025, z + 0.09))
    # --- balustrade posts and a mid rail, along both stair sides and round the landing
    for i in (1, 5, 9):
        for z in (LANE_N - 0.02, LANE_S + 0.02):
            y0 = tread_y(i) - 0.04
            s.box((i * RUN + 0.10 - 0.025, y0, z - 0.025), (i * RUN + 0.10 + 0.025, y0 + 0.95, z + 0.025))
    for z in (LANE_S + 0.02,):
        for x in (STAIR_X1 + 0.1, 3.32):
            s.box((x - 0.025, FY - 0.06, z - 0.025), (x + 0.025, FY + 0.95, z + 0.025))
    s.box((3.32 - 0.025, FY - 0.06, ZF + 0.06 - 0.025), (3.32 + 0.025, FY + 0.95, ZF + 0.06 + 0.025))
    # sloped mid rails (steel) at 0.45 above the treads
    for z in (LANE_N - 0.02, LANE_S + 0.02):
        s.bar((0.10, tread_y(0) + 0.38, z), (STAIR_X1 - 0.12, FY + 0.43, z), 0.02, ref=(0, 0, 1))
    s.bar((STAIR_X1 + 0.1, FY + 0.45, LANE_S + 0.02), (3.32, FY + 0.45, LANE_S + 0.02), 0.02, ref=(0, 0, 1))
    s.bar((3.32, FY + 0.45, LANE_S + 0.02), (3.32, FY + 0.45, ZF + 0.06), 0.02, ref=(1, 0, 0))
    # the gate frame: the south post and a header bar over the gate lane at the stair foot
    s.box((-0.05, 0.0, LANE_S), (0.05, 1.45, LANE_S + 0.10))
    s.box((-0.05, 1.45, LANE_S - 0.01), (0.05, 1.50, LANE_S + 0.11))
    # the roof of the lock? no. a back plate on the booth's front fascia below the stair gap (the 0.4 gap between stair and fascia)
    s.box((0.0, 0.0, LANE_N - 0.40), (0.04, 1.30, LANE_N - 0.04))                   # the gap's end screen at the foot
    return s.obj("booth_steel")


def glass_parts():
    g = F.MB(GLASS)
    edges = [-XW] + MULL_X
    for k in range(len(edges) - 1):
        xa, xb = edges[k] + 0.03, edges[k + 1] - 0.03
        if k == 0:
            xa = -XW + 0.10
        g.box((xa, DADO + 0.04, ZF - 0.012), (xb, GLASS_TOP - 0.06, ZF - 0.004), bottom=True)
    # the door pane
    g.box((DOOR_X0 + 0.12, 2.60, ZF - 0.012), (DOOR_X1 - 0.12, 4.30, ZF - 0.004), bottom=True)
    # the east and west sides: two panes each
    for sx in (-1, 1):
        xc = sx * (XW - 0.03)
        for (za, zb) in ((ZB + 0.12, 0.07), (0.13, ZF - 0.12)):
            g.box((xc - 0.006, DADO + 0.04, za), (xc + 0.006, GLASS_TOP - 0.06, zb), bottom=True)
    return g.obj("booth_glass")


def cheq_parts():
    c = F.MB(CHEQ)
    c.box((-XW, 1.94, ZB), (XW, FY, ZF), bottom=True)
    for i in range(N_STEPS):
        c.box((i * RUN - 0.02, tread_y(i) - 0.04, LANE_N), ((i + 1) * RUN, tread_y(i), LANE_S), bottom=True)
    c.box((STAIR_X1, FY - 0.06, ZF), (3.4, FY, LANE_S + 0.04))                      # the landing
    return c.obj("booth_cheq")


def clock_loops():
    """Hands of the stopped wall clock at 03:17 (clockwise angles from 12 o'clock)."""
    th_h = (3 + 17 / 60.0) * 30.0
    th_m = 17 * 6.0

    def rot(pts, ang_cw):
        a = -math.radians(ang_cw)
        return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for (x, y) in pts]
    minute = [(-0.011, -0.07), (0.011, -0.07), (0.011, 0.03), (0.0055, 0.265), (-0.0055, 0.265), (-0.011, 0.03)]
    hour = [(-0.012, -0.05), (0.012, -0.05), (0.012, 0.03), (0.036, 0.10), (0.0, 0.185), (-0.036, 0.10), (-0.012, 0.03)]
    return rot(hour, th_h), rot(minute, th_m)


def brass_parts():
    br = F.MB(BRASS)
    # roof cornice (a band round the roof edge) and corner caps
    br.box((-XW - 0.14, GLASS_TOP - 0.02, ZF + 0.10), (XW + 0.14, GLASS_TOP + 0.05, ZF + 0.14))
    br.box((-XW - 0.14, GLASS_TOP - 0.02, ZB - 0.07), (-XW - 0.10, GLASS_TOP + 0.05, ZF + 0.14))
    br.box((XW + 0.10, GLASS_TOP - 0.02, ZB - 0.07), (XW + 0.14, GLASS_TOP + 0.05, ZF + 0.14))
    br.box((-XW - 0.14, ROOF - 0.03, ZF + 0.09), (XW + 0.14, ROOF + 0.01, ZF + 0.14))
    # the dado cap rail across the front and sides
    br.box((-XW, DADO, ZF - 0.06), (DOOR_X0, DADO + 0.04, ZF + 0.03))
    br.box((-XW + 0.04, DADO, ZB), (-XW + 0.10, DADO + 0.04, ZF - 0.06))
    br.box((XW - 0.10, DADO, ZB), (XW - 0.04, DADO + 0.04, ZF - 0.06))
    br.box((-XW, FY, ZF - 0.06), (XW, FY + 0.03, ZF + 0.04))                         # the floor edge nosing
    # corner post caps and mullion feet
    for x in (-XW + 0.05, XW - 0.05):
        for z in (ZB + 0.05, ZF - 0.05):
            br.box((x - 0.065, GLASS_TOP - 0.10, z - 0.065), (x + 0.065, GLASS_TOP - 0.06, z + 0.065))
    # tread nosings
    for i in range(N_STEPS):
        br.box((i * RUN - 0.03, tread_y(i) - 0.012, LANE_N + 0.03), (i * RUN - 0.012, tread_y(i) + 0.004, LANE_S - 0.03))
    # sloped handrails along both stair sides and round the landing
    for z in (LANE_N - 0.02, LANE_S + 0.02):
        br.bar((0.10, tread_y(0) + 0.88, z), (STAIR_X1 - 0.12, FY + 0.93, z), 0.045, ref=(0, 0, 1))
    br.bar((STAIR_X1 - 0.12, FY + 0.93, LANE_S + 0.02), (3.32, FY + 0.91, LANE_S + 0.02), 0.045, ref=(0, 0, 1))
    br.bar((3.32, FY + 0.91, LANE_S + 0.02), (3.32, FY + 0.91, ZF + 0.06), 0.045, ref=(1, 0, 0))
    for (x, y, z) in ((0.10, tread_y(0) + 0.88, LANE_N - 0.02), (0.10, tread_y(0) + 0.88, LANE_S + 0.02)):
        br.cyl((x - 0.02, y, z), (1, 0, 0), 0.032, 0.04, segs=8)
    # door hardware: a push plate with a pull bar on the leaf
    br.box((DOOR_X1 - 0.30, 3.00, ZF + 0.03), (DOOR_X1 - 0.20, 3.45, ZF + 0.045))
    br.bar((DOOR_X1 - 0.25, 3.04, ZF + 0.075), (DOOR_X1 - 0.25, 3.42, ZF + 0.075), 0.03, ref=(1, 0, 0))
    for y in (3.06, 3.40):
        br.cyl((DOOR_X1 - 0.25, y, ZF + 0.045), (0, 0, 1), 0.012, 0.03, segs=6)
    # the lamp's brass ring
    br.cyl((0.0, GLASS_TOP - 0.31, 0.10), (0, 1, 0), 0.215, 0.025, segs=18)
    # --- the stopped wall clock 03:17 on the back wall
    cx, cy, cz = CLOCK_C
    hour, minute = clock_loops()
    out = [br]
    objs = []
    objs.append(K.glathe("clock_bezel", [(0.292, 0.0), (0.345, 0.0), (0.350, 0.012), (0.345, 0.050), (0.330, 0.062), (0.300, 0.058), (0.292, 0.046), (0.292, 0.002)],
                         base=(cx, cy, cz), axis=(0, 0, 1), segments=40, mat=BRASS, smooth=50.0, cap_bottom=False, cap_top=False))
    for k in range(12):
        a = math.radians(30.0 * k)
        big = k % 3 == 0
        w, l = (0.026, 0.085) if big else (0.014, 0.050)
        bar = K.gbox("hb", (-w, 0.285 - l, 0.0), (w, 0.285, 0.016), BRASS, 0.0)
        bar.data.transform(Matrix.Translation((cx, cy, cz + 0.020)) @ Matrix.Rotation(-a, 4, "Z"))
        objs.append(bar)
    objs.append(K.plate("hand_h", [hour], 0.007, z0=cz + 0.040, mat=BRASS, bevel=0.0006, drop_bottom=True, loc=(cx, cy, 0.0)))
    objs.append(K.plate("hand_m", [minute], 0.007, z0=cz + 0.048, mat=BRASS, bevel=0.0006, drop_bottom=True, loc=(cx, cy, 0.0)))
    objs.append(K.gcyl("hub", 0.022, cz + 0.040, cz + 0.066, base=(cx, cy, 0.0), axis=(0, 0, 1), segments=12, mat=BRASS, chamfer=0.004))
    objs.append(br.obj("booth_brass"))
    return objs


def clock_dial():
    cx, cy, cz = CLOCK_C
    return K.gcyl("clock_dial", 0.296, cz + 0.014, cz + 0.020, base=(cx, cy, 0.0), axis=(0, 0, 1), segments=40, mat=STEEL)


def rivets_gate():
    return []


# ====================================================================== the gate
def gate_parts():
    """IA_booth_gate in booth-local coordinates (origin of the node = the north post)."""
    z0 = LANE_N
    br = F.MB(BRASS)
    # north post (on the origin plane), 0.10 square, 1.45 high, with a base plate and a cap
    br.box((-0.06, 0.0, z0 - 0.06), (0.06, 0.03, z0 + 0.06))
    br.box((-0.045, 0.03, z0 - 0.045), (0.045, 1.14, z0 + 0.045))
    br.box((-0.05, 1.14, z0 - 0.07), (0.05, 1.40, z0 + 0.07))                     # the lock box (centred on the origin plane z0)
    br.box((-0.06, 1.40, z0 - 0.08), (0.06, 1.43, z0 + 0.08))                     # the lid / key plate
    # the slot: two lips leaving a 5 mm slot along X on the top, a raised rim round it
    br.box((-0.045, 1.43, z0 - 0.03), (0.045, 1.452, z0 - 0.0035))
    br.box((-0.045, 1.43, z0 + 0.0035), (0.045, 1.452, z0 + 0.03))
    br.box((-0.045, 1.43, z0 - 0.0035), (0.045, 1.437, z0 + 0.0035))
    # lattice leaf: top and bottom rails, the end stile at the free end, X bars in 2 rows x 3 cells with hex rosettes
    y_lo, y_hi = 0.16, 0.96
    zs0, zs1 = z0 + 0.05, LANE_S
    br.bar((0.0, y_lo, zs0), (0.0, y_lo, zs1), 0.034, ref=(1, 0, 0))
    br.bar((0.0, y_hi, zs0), (0.0, y_hi, zs1), 0.034, ref=(1, 0, 0))
    br.bar((0.0, y_lo, zs1), (0.0, y_hi, zs1), 0.034, ref=(1, 0, 0))
    mid = (y_lo + y_hi) / 2.0
    br.bar((0.0, mid, zs0), (0.0, mid, zs1), 0.022, ref=(1, 0, 0))
    ncell = 3
    cw = (zs1 - zs0) / ncell
    for row, (ya, yb) in enumerate(((y_lo, mid), (mid, y_hi))):
        for c in range(ncell):
            za, zb = zs0 + cw * c, zs0 + cw * (c + 1)
            br.bar((0.0, ya, za), (0.0, yb, zb), 0.020, ref=(1, 0, 0))
            br.bar((0.0, yb, za), (0.0, ya, zb), 0.020, ref=(1, 0, 0))
            br.boss((0.0, (ya + yb) / 2.0, (za + zb) / 2.0), (1, 0, 0), 0.020, 0.010, sides=6)
            br.boss((0.0, (ya + yb) / 2.0, (za + zb) / 2.0), (-1, 0, 0), 0.020, 0.010, sides=6)
    obj1 = br.obj("gate_main")
    # Strand's mark on the lock box (the +Z face), the door's brass is the box
    mark = C.S.inlay("gate_mark", "mark", 0.15, depth=0.004, mat=BRASS, bevel=0.0004, loc=(0.0, 1.27, z0 + 0.07))
    return [obj1, mark]


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    steel = steel_parts()
    glass = glass_parts()
    cheq = cheq_parts()
    brass_objs = brass_parts()
    dial = clock_dial()
    body = C.merge("booth", [steel, glass, cheq, dial] + brass_objs)
    gate = K.part("IA_booth_gate", gate_parts(), pivot=GATE_ORIGIN)
    K.empty("booth_lamp", (0.0, 4.25, 0.10))
    K.empty("desk_mount", (0.0, FY, -0.4))
    # the key mount: bow (item -Z) up, face (item +Y) toward +Z = a +90 deg turn about X; the blade tip ~3 cm inside the slot
    K.empty("booth_key_mount", (0.0, SLOT_TOP + 0.085, LANE_N), rot_deg=(90.0, 0.0, 0.0))
    K.to_blender()
    K.parent(bpy.data.objects["booth_key_mount"], gate)
    C.finalize()
    return dict(body=body, gate=gate)


def verify(path):
    req = ["booth", "IA_booth_gate", "booth_key_mount", "booth_lamp", "desk_mount"]
    ident = ["booth", "IA_booth_gate"]
    expect = {"booth": (0.0, 0.0, 0.0), "IA_booth_gate": GATE_ORIGIN, "booth_lamp": (0.0, 4.25, 0.10), "desk_mount": (0.0, FY, -0.4),
              "booth_key_mount": (0.0, SLOT_TOP + 0.085, LANE_N)}
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents={"booth_key_mount": "IA_booth_gate"},
                    rot_expect={"booth_key_mount": (90.0, 0.0, 0.0)}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ["booth", "IA_booth_gate"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa_scene(parts, desk=True):
    X.qa_env(extra=[("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    K.qa_place([parts["body"], parts["gate"]], (0.0, 0.0, -13.0), 0.0, name="qa_booth_root")
    if desk:
        for (nm, pos) in (("booth_desk", (0.0, 2.0, -13.4)),):
            C.qa_import(nm, pos, 0.0, prefix=f"qa_{nm}_")
        C.qa_import("strand_box4", (0.0, 2.78, -13.4), 0.0, prefix="qa_box_")
        C.qa_import("key_strand", (0.0, 0.0, 0.0), 0.0, prefix="qa_key_")
    M.refresh()


def qa(args, parts):
    qa_scene(parts, desk=False)
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))
    # the stolen key hangs in the lock for the closeup (key_strand lies flat: bow -Z; the mount turns it +90 deg about X)
    key = C.qa_import("key_strand", (0.0, 0.0, 0.0), 0.0, prefix="qa_key_")
    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
        K.light("booth_lamp", "POINT", (0.0, 4.25, -12.9), 140.0, "FFD9A0", radius=0.1)
    if C.want(args, "1"):          # the contract view
        cam, tgt, fov = C.view("booth")
        lit(cam, 40.0, 1.0)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the stair foot, the gate and its lock with Strand's key in the slot
        mount = bpy.data.objects["booth_key_mount"]
        if key is not None:
            key.parent = mount
            key.matrix_parent_inverse = Matrix.Identity(4)
            key.location = (0.0, 0.0, 0.0)
            key.rotation_euler = (0.0, 0.0, 0.0)
        M.refresh()
        cam, tgt, fov = (-1.4, 1.75, -9.7), (0.0, 1.3, -11.5), 36
        lit(cam, 40.0, 1.0)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # inside the glass from the stair landing side: the clock and the booth
        cam, tgt, fov = (2.0, 3.55, -9.6), (-0.2, 3.5, -13.0), 52
        lit(cam, 40.0, 1.0)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "4"):          # the gate open
        g = parts["gate"]
        g.scale = (1.0, 0.15, 1.0)
        M.refresh()
        cam, tgt, fov = (-1.6, 1.5, -9.6), (0.7, 1.2, -11.3), 44
        lit(cam, 40.0, 1.0)
        C.shoot(NAME + "_4", cam, tgt, fov, samples=S, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    F.shell_report(label=NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    F.backface_check(label=NAME)
    qa(args, parts)


main()
