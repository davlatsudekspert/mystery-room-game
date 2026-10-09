"""shell_choir.glb — the Choir Hall shell (Strand's wing), in WORLD coordinates (place at the origin, yaw 0).
Contract: docs/models/ch3.md §3 shell_choir (+ §1.1, §1.4 portal_w_c, §1.5 lights, §2 views); results:
docs/models/ch3_a.md.

Interior x ∈ [-13.0, -4.5], z ∈ [-4.0, 4.0], y ∈ [0, 6.0]; walls 0.3 thick outside the box (only the interior faces
and the opening reveals are modelled).

  choir_walls      board-formed concrete (one 0.15 m board per sawtooth step, pour-lift grooves) over a green-painted
                   dado 0 .. 1.5 m; pilasters 0.40 x 0.15 (north x -11.6 / -6.2, south x -9.95, east z -2.0 / +1.6);
                   openings: the west-door tunnel mouth (east wall, |z| <= 0.8, y <= 2.4) and the lobby passage (south
                   wall, x -6.3 .. -4.8, y <= 2.6)
  choir_floor      concrete with green walkway strips 0.08 wide (desk area, rack front, switch-room front)
  choir_ceiling    concrete at y 6.0 with two deep beams along x at z -2.0 and z 3.2
  catwalk          steel deck y 4.0 over x -13.0 .. -12.0 with a toe board, wall brackets (between the transformers),
                   handrail on x -12.0 (posts every 1.0 m, one at z 1.9 with the port_b mounting plate), the ladder
  gantry           crane I-beam at z 1.9 (flanges y 5.45 .. 5.75) on wall corbels, the trolley at x -8.6 with its drop
                   plate and the angled port_c mounting plate
  choir_trim       cable trays, conduits, steel pilaster capitals, the six caged lamp bodies
  lamp_glass_0..5  lamp glasses (code emission) + empties light_choir_0..5 at the bulbs
                   order: north x -12.3, -7.4; south x -11.6, -7.4; east z -2.8, 2.2 (all at y 3.4)
  portal_w_c       (-3.75, 1.2, 0), +Z toward +X (the Gallery)

    blender -b --factory-startup -P tools/blender/models/shell_choir.py [-- --no-render] [--shots=1,2,...]
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
import lib_ch3_a as K  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_choir"
TRI_BUDGET, SURF_BUDGET = 18000, 14
CONC, GREEN, STEEL, FROST = K.CONC, K.GREEN, K.STEEL, K.FROST
X0, X1, Z0, Z1, H = -13.0, -4.5, -4.0, 4.0, 6.0
DADO = 1.5
DOOR_Z, DOOR_H = 0.8, 2.4
PASS = (-6.3, -4.8)
PASS_H = 2.6
PIL_W, PIL_D = 0.40, 0.15
CAT_Y, CAT_X = 4.0, -12.0
GANTRY_Z, GANTRY_Y0, GANTRY_Y1 = 1.9, 5.45, 5.75
TROLLEY_X = -8.6
LAMP_Y = 3.4
LAMPS = [("n", -12.3), ("n", -7.4), ("s", -11.6), ("s", -7.4), ("e", -2.8), ("e", 2.2)]
PORT_B = ((-12.0, 4.55, 1.9), 110.0, 0.0)
PORT_C = ((-8.6, 5.15, 1.9), 180.0, 60.0)
CAT_POSTS = [-3.95, -3.1, -2.1, -1.1, -0.1, 0.9, 1.9, 2.9, 3.95]
CAT_BRACKETS = [-3.85, -2.15, -0.45, 1.25, 2.75]


def wall_profile():
    """Dado (painted, smooth) then 0.15 m sawtooth boards; extra rows at the opening heights 2.4 and 2.6."""
    prof = [(-0.012, 0.0), (-0.012, 0.13), (0.0, 0.142), (0.0, 1.475), (-0.005, 1.485), (-0.005, 1.515), (0.0, 1.525)]
    y = 1.525
    k = 0
    while y + 0.15 < H - 0.08:
        prof += [(0.0045, y + 0.146), (0.0, y + 0.15)]
        if k % 10 == 9:                                # pour-lift joint: a deeper groove every 1.5 m
            prof += [(0.012, y + 0.155), (0.012, y + 0.170), (0.0, y + 0.175)]
            y += 0.025
        y += 0.15
        k += 1
    prof += [(0.0, H)]
    out = []
    for i, (s, yy) in enumerate(prof):
        for lv in (DOOR_H, PASS_H):                   # insert exact rows at the opening tops
            if i > 0 and prof[i - 1][1] < lv < yy:
                s0, y0 = prof[i - 1]
                t = (lv - y0) / (yy - y0)
                out.append((s0 + (s - s0) * t, lv))
        out.append((s, yy))
    return out


def wall_path():
    hw, d = PIL_W / 2, PIL_D
    pts = [(X0, Z0)]
    for x in (-11.6, -6.2):                                   # north wall, going +x
        pts += [(x - hw, Z0), (x - hw, Z0 + d), (x + hw, Z0 + d), (x + hw, Z0)]
    pts += [(X1, Z0)]
    for z in (-2.0,):                                          # east wall, going +z
        pts += [(X1, z - hw), (X1 - d, z - hw), (X1 - d, z + hw), (X1, z + hw)]
    pts += [(X1, -DOOR_Z), (X1, DOOR_Z)]
    for z in (1.6,):
        pts += [(X1, z - hw), (X1 - d, z - hw), (X1 - d, z + hw), (X1, z + hw)]
    pts += [(X1, Z1), (PASS[1], Z1), (PASS[0], Z1)]          # south wall, going -x
    x = -9.95
    pts += [(x + hw, Z1), (x + hw, Z1 - d), (x - hw, Z1 - d), (x - hw, Z1)]
    pts += [(X0, Z1)]
    return pts


def walls():
    w = K.wall_sweep("walls", wall_path(), wall_profile(), CONC)

    def opening(c, n):
        if c.x > X1 - 0.1 and abs(c.z) < DOOR_Z and c.y < DOOR_H:
            return True
        return c.z > Z1 - 0.1 and PASS[0] < c.x < PASS[1] and c.y < PASS_H
    K.delete_faces_where(w, opening)
    A.mat_by_face(w, lambda c, n, cur: GREEN if c.y < DADO else None)
    return K.part("choir_walls", [w])


def floor():
    parts = [K.flat_poly("floor", [(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)], [], 0.0, CONC, up=True)]
    w = 0.08
    lines = []

    def rect(x0, x1, z0, z1):
        lines.extend([((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))])
    rect(-9.85, -6.15, -0.55, 1.55)                           # around the control desk
    lines.append(((-11.3, -2.75), (-6.4, -2.75)))             # rack + bench front
    lines += [((-9.85, 3.0), (-6.75, 3.0)), ((-9.85, 3.0), (-9.85, 3.95)), ((-6.75, 3.0), (-6.75, 3.95))]  # switch room
    lines.append(((-11.6, -3.9), (-11.6, 1.15)))              # transformer bay limit
    for (a, b) in lines:
        pa, pb = Vector((a[0], 0, a[1])), Vector((b[0], 0, b[1]))
        d = (pb - pa)
        n = Vector((-d.z, 0, d.x)).normalized() * (w / 2)
        e = d.normalized() * (w / 2)
        pa, pb = pa - e, pb + e
        poly = [(p.x, p.z) for p in (pa - n, pb - n, pb + n, pa + n)]
        parts.append(K.flat_poly("strip", poly, [], 0.003, GREEN, up=True))
    return K.part("choir_floor", parts)


def ceiling():
    parts = [K.flat_poly("ceil", [(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)], [], H, CONC, up=False)]
    for z in (-2.0, 3.2):
        parts.append(K.gbox("beam", (X0, 5.42, z - 0.2), (X1, H, z + 0.2), CONC, 0.015))
        parts.append(K.gbox("haunch", (X0, 5.25, z - 0.24), (X0 + 0.35, 5.42, z + 0.24), CONC, 0.01))
        parts.append(K.gbox("haunch", (X1 - 0.35, 5.25, z - 0.24), (X1, 5.42, z + 0.24), CONC, 0.01))
    return K.part("choir_ceiling", parts)


# ====================================================================== catwalk & gantry
def frame_from(origin, yaw_deg, pitch_deg=0.0):
    """Godot Basis(UP, yaw) * Basis(RIGHT, pitch) at origin, as a 4x4 (local -> world, G-frame)."""
    return (Matrix.Translation(origin) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Y") @
            Matrix.Rotation(math.radians(pitch_deg), 4, "X"))


def catwalk():
    p = []
    # deck plate with the ladder opening, raised tread bars, toe board on the open edge
    hole = (-12.95, -12.45, Z0, -3.40)
    p.append(K.gbox("deck", (X0, CAT_Y - 0.05, hole[3]), (CAT_X, CAT_Y, Z1), STEEL, 0.004))
    p.append(K.gbox("deck", (hole[1], CAT_Y - 0.05, Z0), (CAT_X, CAT_Y, hole[3]), STEEL, 0.004))
    for k in range(26):
        z = -3.30 + 0.28 * k
        p.append(K.gbox("ctread", (X0 + 0.05, CAT_Y, z - 0.01), (CAT_X - 0.05, CAT_Y + 0.006, z + 0.01), STEEL, 0.0))
    p.append(K.gbox("toe", (CAT_X - 0.008, CAT_Y, Z0), (CAT_X, CAT_Y + 0.12, Z1), STEEL, 0.002))
    p.append(K.gbox("edge", (CAT_X - 0.07, CAT_Y - 0.14, Z0), (CAT_X, CAT_Y - 0.05, Z1), STEEL, 0.004))
    # wall brackets (triangles of channel) between the transformers
    for z in CAT_BRACKETS:
        p.append(K.gbox("bwall", (X0, 3.25, z - 0.04), (X0 + 0.05, CAT_Y - 0.05, z + 0.04), STEEL, 0.004))
        p.append(K.gbox("btop", (X0, CAT_Y - 0.14, z - 0.035), (CAT_X - 0.07, CAT_Y - 0.05, z + 0.035), STEEL, 0.004))
        a, b = Vector((X0 + 0.04, 3.32, z)), Vector((CAT_X - 0.12, CAT_Y - 0.12, z))
        d = b - a
        st = K.gbox("strut", (-d.length / 2, -0.03, -0.03), (d.length / 2, 0.03, 0.03), STEEL, 0.004)
        st.data.transform(Matrix.Translation((a + b) / 2) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
        p.append(st)
    # handrail on x = -12.0
    for z in CAT_POSTS:
        p.append(K.gcyl("cpost", 0.022, CAT_Y, CAT_Y + 1.0, base=(CAT_X - 0.03, 0.0, z), axis=(0, 1, 0), segments=8,
                        mat=STEEL, caps=False))
    for y, r in ((CAT_Y + 1.0, 0.024), (CAT_Y + 0.52, 0.016)):
        p.append(K.V.tube("crail", [(CAT_X - 0.03, y, Z0), (CAT_X - 0.03, y, Z1)], r, sides=8, mat=STEEL))
    # port_b mounting plate on the post at z = 1.9 (front plane through the port origin, facing yaw 110)
    o, yaw, _ = PORT_B
    m = frame_from(o, yaw)
    pl = K.plate("pbplate", [L.rounded_rect(0.44, 0.44, 0.03, 3)], 0.012, z0=-0.012, mat=STEEL, bevel=0.002)
    pl.data.transform(m)
    p.append(pl)
    for dy in (-0.15, 0.15):                                  # clamps from the plate back to the post
        a = m @ Vector((0.0, dy, -0.012))
        b = Vector((CAT_X - 0.03, o[1] + dy, o[2]))
        d = b - a
        if d.length > 0.01:
            cl = K.gcyl("pbclamp", 0.018, 0.0, d.length, base=tuple(a), axis=tuple(d), segments=6, mat=STEEL)
            p.append(cl)
    # ladder against the north wall, floor to deck (+1.0 grab extension)
    for x in (-12.88, -12.52):
        p.append(K.gbox("lstile", (x - 0.03, 0.0, -3.86), (x + 0.03, CAT_Y + 1.0, -3.80), STEEL, 0.004))
        for y in (0.6, 2.0, 3.4):
            p.append(K.gbox("lbrk", (x - 0.02, y - 0.03, Z0), (x + 0.02, y + 0.03, -3.86), STEEL, 0.0))
    for k in range(13):
        y = 0.30 + 0.30 * k
        p.append(K.gcyl("rung", 0.012, 0.0, 0.30, base=(-12.85, y, -3.83), axis=(1, 0, 0), segments=6, mat=STEEL, caps=False))
    return K.part("catwalk", p)


def gantry():
    p = []
    z, y0, y1 = GANTRY_Z, GANTRY_Y0, GANTRY_Y1
    fw, ft, wt = 0.09, 0.022, 0.012
    p.append(K.gbox("bflange", (X0, y0, z - fw), (X1, y0 + ft, z + fw), STEEL, 0.004))
    p.append(K.gbox("tflange", (X0, y1 - ft, z - fw), (X1, y1, z + fw), STEEL, 0.004))
    p.append(K.gbox("web", (X0, y0 + ft, z - wt / 2), (X1, y1 - ft, z + wt / 2), STEEL, 0.0))
    for x in [X0 + 0.9 + 1.0 * k for k in range(8)]:            # web stiffeners
        p.append(K.gbox("stiff", (x - 0.006, y0 + ft, z - fw + 0.01), (x + 0.006, y1 - ft, z + fw - 0.01), STEEL, 0.0))
    for xw, sx in ((X0, 1), (X1, -1)):                          # wall corbels (riveted brackets) under both ends
        a, b = sorted((xw, xw + sx * 0.45))
        p.append(K.gbox("corbel", (a, y0 - 0.06, z - 0.16), (b, y0, z + 0.16), STEEL, 0.006))
        a2, b2 = sorted((xw, xw + sx * 0.08))
        p.append(K.gbox("corbelw", (a2, y0 - 0.55, z - 0.16), (b2, y0, z + 0.16), STEEL, 0.006))
        pa, pb = Vector((xw + sx * 0.04, y0 - 0.5, z)), Vector((xw + sx * 0.40, y0 - 0.06, z))
        d = pb - pa
        st = K.gbox("cstrut", (-d.length / 2, -0.035, -0.06), (d.length / 2, 0.035, 0.06), STEEL, 0.004)
        st.data.transform(Matrix.Translation((pa + pb) / 2) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
        p.append(st)
        for k in range(3):
            p.append(K.rivet("crv", 0.012, (xw + sx * (0.12 + 0.12 * k), y0 - 0.06, z + 0.13), normal=(0, -1, 0), segs=5))
    # trolley riding on the bottom flange, its hoist block and the drop plate to y 5.30
    tx = TROLLEY_X
    p.append(K.gbox("tframe", (tx - 0.25, y0 - 0.14, z - 0.16), (tx + 0.25, y0 - 0.02, z + 0.16), STEEL, 0.01))
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(K.gcyl("twheel", 0.045, -0.02, 0.02, base=(tx + sx * 0.16, y0 + 0.05, z + sz * 0.115), axis=(0, 0, 1),
                            segments=10, mat=STEEL))
        p.append(K.gbox("tside", (tx + sx * 0.2 - 0.02, y0 - 0.02, z - 0.16), (tx + sx * 0.2 + 0.02, y0 + 0.11, z + 0.16), STEEL, 0.004))
    p.append(K.gbox("drop", (tx - 0.13, 5.30, z - 0.008), (tx + 0.13, y0 - 0.14, z + 0.008), STEEL, 0.003))
    # angled port_c mounting plate (the port's back plane through its origin, pitch +60, yaw 180)
    o, yaw, pitch = PORT_C
    m = frame_from(o, yaw, pitch)
    pl = K.plate("pcplate", [L.rounded_rect(0.42, 0.42, 0.03, 3)], 0.012, z0=-0.012, mat=STEEL, bevel=0.002)
    pl.data.transform(m)
    p.append(pl)
    top = m @ Vector((0.0, 0.19, -0.012))
    for dx in (-0.10, 0.10):
        a = Vector((tx + dx, 5.31, z))
        b = Vector((top.x + dx, top.y, top.z))
        d = b - a
        if d.length > 0.005:
            p.append(K.gcyl("pcweb", 0.012, 0.0, d.length, base=tuple(a), axis=tuple(d), segments=6, mat=STEEL))
    return K.part("gantry", p)


# ====================================================================== trim + lamps
def wall_frame(side, s):
    """Local frame on a wall: x along the wall (seen from the room), y up, z into the room; returns a 4x4."""
    if side == "n":
        o, ex, ez = Vector((s, 0, Z0)), Vector((1, 0, 0)), Vector((0, 0, 1))
    elif side == "s":
        o, ex, ez = Vector((s, 0, Z1)), Vector((-1, 0, 0)), Vector((0, 0, -1))
    else:
        o, ex, ez = Vector((X1, 0, s)), Vector((0, 0, 1)), Vector((-1, 0, 0))
    ey = Vector((0, 1, 0))
    return Matrix(((ex.x, ey.x, ez.x, o.x), (ex.y, ey.y, ez.y, o.y), (ex.z, ey.z, ez.z, o.z), (0, 0, 0, 1)))


def lamp(k, side, s):
    """Caged bulkhead lamp: cast body + guard (trim), frosted glass (lamp_glass_k), bulb centre."""
    m = wall_frame(side, s)
    y = LAMP_Y
    body = []
    body.append(K.plate("lbase", [L.rounded_rect(0.20, 0.28, 0.06, 4)], 0.03, mat=STEEL, bevel=0.006, loc=(0, y, 0)))
    body.append(K.glathe("lhouse", [(0.0, 0.03), (0.085, 0.03), (0.095, 0.05), (0.09, 0.075), (0.075, 0.08), (0.0, 0.08)],
                         (0, y, 0), (0, 0, 1), 12, STEEL, smooth=45.0))
    for a in (0, 60, 120):
        r = math.radians(a)
        ca, sa = math.cos(r), math.sin(r)
        pts = [(-0.085 * ca, y - 0.085 * sa, 0.08), (-0.07 * ca, y - 0.07 * sa, 0.15), (0.0, y, 0.175),
               (0.07 * ca, y + 0.07 * sa, 0.15), (0.085 * ca, y + 0.085 * sa, 0.08)]
        body.append(K.V.tube("lguard", pts, 0.006, sides=4, mat=STEEL))
    ring = M.torus("lring", 0.087, 0.007, major_seg=12, minor_seg=4, mat=STEEL)
    ring.data.transform(Matrix.Translation((0, y, 0.10)))
    body.append(ring)
    body.append(K.gbox("jbox", (-0.06, y + 0.17, 0.0), (0.06, y + 0.29, 0.07), STEEL, 0.008))
    for o in body:
        o.data.transform(m)
    gl = K.glathe("lglass", [(0.075, 0.075), (0.074, 0.11), (0.06, 0.145), (0.03, 0.165), (0.0, 0.17)], (0, y, 0), (0, 0, 1),
                  12, FROST, smooth=60.0)
    gl.data.transform(m)
    bulb = m @ Vector((0, y, 0.12))
    return body, K.part(f"lamp_glass_{k}", [gl], pivot=tuple(bulb)), bulb


def trim(lamp_bodies):
    p = list(lamp_bodies)
    # cable trays at y 4.6: north wall (x -11.9 .. -4.6) and east wall (z -3.9 .. 3.9), with wall brackets
    ty = 4.6
    for (a, b, side) in ((-11.9, -4.65, "n"), (-3.9, 3.9, "e")):
        if side == "n":
            p.append(K.gbox("tray", (a, ty, Z0 + 0.05), (b, ty + 0.012, Z0 + 0.35), STEEL, 0.002))
            for zz in (Z0 + 0.05, Z0 + 0.35):
                p.append(K.gbox("trayside", (a, ty, zz - 0.006), (b, ty + 0.08, zz + 0.006), STEEL, 0.002))
            for x in [a + 0.3 + 1.5 * k for k in range(5)]:
                p.append(K.gbox("traybrk", (x - 0.025, ty - 0.10, Z0), (x + 0.025, ty, Z0 + 0.38), STEEL, 0.004))
            p.append(K.V.tube("cable", [(a, ty + 0.035, Z0 + 0.15), (b, ty + 0.035, Z0 + 0.15)], 0.025, sides=6, mat=STEEL))
            p.append(K.V.tube("cable", [(a, ty + 0.03, Z0 + 0.24), (b, ty + 0.03, Z0 + 0.24)], 0.02, sides=6, mat=STEEL))
        else:
            p.append(K.gbox("tray", (X1 - 0.35, ty, a), (X1 - 0.05, ty + 0.012, b), STEEL, 0.002))
            for xx in (X1 - 0.35, X1 - 0.05):
                p.append(K.gbox("trayside", (xx - 0.006, ty, a), (xx + 0.006, ty + 0.08, b), STEEL, 0.002))
            for z in [a + 0.4 + 1.5 * k for k in range(6)]:
                p.append(K.gbox("traybrk", (X1 - 0.38, ty - 0.10, z - 0.025), (X1, ty, z + 0.025), STEEL, 0.004))
            p.append(K.V.tube("cable", [(X1 - 0.15, ty + 0.035, a), (X1 - 0.15, ty + 0.035, b)], 0.025, sides=6, mat=STEEL))
    # conduits from the trays down to the lamps' junction boxes
    for side, s in LAMPS:
        if side == "n":
            top, bot = (s, ty, Z0 + 0.04), (s, LAMP_Y + 0.29, Z0 + 0.04)
        elif side == "e":
            top, bot = (X1 - 0.04, ty, s), (X1 - 0.04, LAMP_Y + 0.29, s)
        else:
            top, bot = (s, H - 0.05, Z1 - 0.04), (s, LAMP_Y + 0.29, Z1 - 0.04)
        p.append(K.V.tube("conduit", [top, bot], 0.016, sides=6, mat=STEEL))
    # steel capitals on the pilasters (bearing plates under the beam haunch level)
    caps = [("n", -11.6), ("n", -6.2), ("s", -9.95), ("e", -2.0), ("e", 1.6)]
    for side, s in caps:
        m = wall_frame(side, s)
        c = K.gbox("cap", (-0.24, 5.05, 0.0), (0.24, 5.25, PIL_D + 0.05), STEEL, 0.008)
        c.data.transform(m)
        p.append(c)
        for dx in (-0.16, 0.16):
            r = K.rivet("caprv", 0.012, (dx, 5.15, PIL_D + 0.05), normal=(0, 0, 1), segs=5)
            r.data.transform(m)
            p.append(r)
    return K.part("choir_trim", p)


def build():
    M.reset_scene()
    K.ensure_materials()
    out = dict(walls=walls(), floor=floor(), ceiling=ceiling(), catwalk=catwalk(), gantry=gantry())
    bodies, lamps, bulbs = [], [], []
    for k, (side, s) in enumerate(LAMPS):
        b, g, bulb = lamp(k, side, s)
        bodies += b
        lamps.append(g)
        bulbs.append(bulb)
    out["trim"] = trim(bodies)
    out["lamps"] = lamps
    for k, b in enumerate(bulbs):
        K.empty(f"light_choir_{k}", tuple(b))
    K.empty("portal_w_c", (-3.75, 1.2, 0.0), (0, 90, 0))
    K.to_blender()
    A.finalize_uv()
    return out


def verify(path):
    meshes = ["choir_floor", "choir_walls", "choir_ceiling", "catwalk", "gantry", "choir_trim"] + \
             [f"lamp_glass_{k}" for k in range(6)]
    req = meshes + [f"light_choir_{k}" for k in range(6)] + ["portal_w_c"]
    errs = K.V.verify_glb(path, required=req, identity=meshes + [f"light_choir_{k}" for k in range(6)],
                          expect={"portal_w_c": (-3.75, 1.2, 0.0)}, rot_expect={"portal_w_c": (0, 90, 0)}, show=req)
    errs += K.facts(path, TRI_BUDGET, SURF_BUDGET)
    for o, yaw, pitch in (PORT_B, PORT_C):
        m = frame_from(o, yaw, pitch)
        f = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
        print(f"{K.TAG} port mount at {o}: plate front plane through the origin, facing {tuple(round(c, 3) for c in f)}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    K.qa_begin(bounces=6)
    K.qa_import("blast_door", (-3.70, 0, 0), 90.0, prefix="qa_dw_")
    K.qa_import("shell_lift", (0, 0, 0), 0.0, prefix="qa_sl_")
    K.qa_import("freight_lift", (0, 0, 6.0), 0.0, prefix="qa_fl_")
    for o in list(bpy.data.objects):
        if o.name.startswith("qa_sl_intro"):
            o.hide_render = True
    lamp_glow = K.glow("qa_work", "FFD49A", 9.0)
    for g in parts["lamps"]:
        K.override(g, lamp_glow)

    def lights(cam=None):
        K.clear_lights()
        K.light("key_choir", "SPOT", (-8.0, 5.6, 2.6), 2200.0, "FFD2A0", radius=0.25, target=(-8.6, 0.0, -1.2), spot_deg=55)
        for k in range(6):
            p = bpy.data.objects[f"light_choir_{k}"].matrix_world.translation
            K.light(f"work_{k}", "POINT", (p.x, p.z, -p.y), 140.0 if k < 4 else 60.0, "FFC890", radius=0.06)
        K.light("bounce", "AREA", (-8.7, 5.8, 0.0), 220.0, "FFE6C8", radius=7.0, target=(-8.7, 0.0, 0.0))
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 12.0, "FFE2C2", radius=0.2)

    shots = [("1", NAME, (-5.4, 1.65, 3.3), (-9.6, 1.5, -2.0), 62),          # choir (R)
             ("2", NAME + "_2", (-5.6, 1.65, -2.9), (-10.6, 1.3, 2.6), 62),  # choir_s (R)
             ("3", NAME + "_3", (-5.8, 2.2, 2.9), (-10.0, 2.4, -2.0), 64),   # hall_start (cinematic)
             ("4", NAME + "_4", (-11.75, 4.65, 1.75), (-8.2, 1.15, 0.45), 34),  # port_b (from the catwalk)
             ("5", NAME + "_5", (-8.6, 4.95, 1.8), (-8.3, 1.2, 0.4), 40),   # port_c (under the gantry)
             ("6", NAME + "_6", (-6.5, 1.6, 0.0), (-4.5, 1.25, 0.0), 56),   # blast_west_hall
             ("7", NAME + "_7", (-7.0, 2.6, -1.0), (-12.4, 4.2, 1.2), 62)]  # catwalk, gantry, port_b plate
    for tag, name, cam, tgt, fov in shots:
        if K.want(args, tag):
            lights(cam if tag in ("4", "5", "6") else None)
            K.shoot(name, cam, tgt, vfov=fov)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
