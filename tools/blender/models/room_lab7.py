"""room_lab7.glb — Laboratory 7 shell + Leyla's secret darkroom, built directly in ROOM coordinates.

Blender (x, y, z) = Godot (x, -z, y).  Place in Godot at the origin with no rotation.

  Lab 7      interior x [-3, 3], Godot z [-2.5, 2.5] (Blender y [-2.5, 2.5]), floor 0, ceiling 3.4,
             walls 0.2 m thick outside the interior box (closed solids, so the moon shadow works).
  North (Godot z = -2.5, Blender y = +2.5): window x [0.95, 2.05], y [1.45, 2.85]; plaster reveal,
             walnut architrave, stone sill (top 1.47, projects 0.14 into the room), walnut casement
             (two side-hung sashes 2 x 3 panes + 3-pane fanlight), 4 iron bars + 2 flat ties on the
             outside face, `window_glass` (M_Glass) as its own object.
  East  (x = +3): door opening Godot z [0.4, 1.4], h 2.2 (frame/casing/leaf live in door_lab7.glb;
             trims stop 0.10 m either side for its casing).
  South (Godot z = +2.5): safe recess x [1.95, 2.45], y [1.0, 1.5], 0.30 deep, M_Steel_Dark liner
             (+ steel flange on the wall face; chair rail cut for it).
  West  (x = -3): bookcase opening Godot z [-1.15, -0.05], h 2.15, straight through to the darkroom;
             vent grille centred (-2.98, 2.9, 1.5) 0.5 x 0.3 with a dark recess; copper pipe runs into it.
  Darkroom   x [-4.8, -3.2], Godot z [-1.6, 0.4], ceiling 2.6, stained plaster (M_Plaster_Stained),
             parquet continues, plain baseboard, safelight fixture hanging from (-4.0, 2.6, -0.6):
             `darkroom_bulb` (M_Emissive_Red, origin at bulb centre Godot (-4.0, 2.29, -0.6)),
             empty `darkroom_light_origin` at the same point.
  Finish     walnut wainscot (M_Wood_Panel backing + raised fields, M_Wood_Walnut ogee mouldings,
             chair rail, baseboard) 0-1.05 m; aged plaster above; plaster crown (M_Ceiling);
             plaster ceiling with 2 chamfered walnut beams E-W + corbels; 2 ceiling roses.
  Dressing   cast-iron column radiator under the window (centre x 1.5) with valves and copper
             flow/return; steel conduit + copper pipe from the top of Panel 7 up the east wall,
             offset under the crown and across the ceiling (conduit ends in a junction box at
             x -0.6, copper continues to the west wall and runs below the beam corbels into the vent).

  NOTE beams: placed at Godot z = +-1.05 (not +-0.9): pendant_lamp_2 hangs at Godot z = 0.8, which
  would sit inside a 0.17 m beam centred on 0.9. Roses (r 0.14) clear both beams.

Clear wall zones kept for wall-mounted props: Panel 7 (east, Godot z [-1.65, -0.95], y [1.0, 1.9]),
chalkboard (west, Godot z [0.25, 1.85], y [1.0, 2.0]), poster (south, x -0.3, y ~1.9),
light sensor (east, (3, 1.15, 0.12)).  No IA_* parts.

    blender -b --factory-startup -P tools/blender/models/room_lab7.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "room_lab7"

X0, X1, Y0, Y1, H, T = -3.0, 3.0, -2.5, 2.5, 3.4, 0.2
DX0, DX1, DY0, DY1, DH = -4.8, -3.2, -0.4, 1.6, 2.6
WIN_X0, WIN_X1, WIN_Z0, WIN_Z1 = 0.95, 2.05, 1.45, 2.85
SILL_TOP = 1.47
DOOR_Y0, DOOR_Y1, DOOR_H = -1.4, -0.4, 2.2
CASING_W = 0.10
SAFE_X0, SAFE_X1, SAFE_Z0, SAFE_Z1, SAFE_D = 1.95, 2.45, 1.0, 1.5, 0.30
BK_Y0, BK_Y1, BK_H = 0.05, 1.15, 2.15
VENT_Y, VENT_Z, VENT_W, VENT_H = -1.5, 2.9, 0.5, 0.3
BEAM_Y, BEAM_W, BEAM_Z0 = 1.05, 0.17, 3.18
ROSES = [(-0.6, 0.6), (1.2, -0.8)]
ROSE_R = 0.14
WAIN_TOP, RAIL_Z, BASE_H, BACK_T = 1.0, 0.985, 0.17, 0.012
PANEL_Z0, PANEL_Z1 = 0.26, 0.88
CHALK_Y0, CHALK_Y1 = -1.85, -0.25
P7_Y0, P7_Y1 = 0.95, 1.65
RAD_X, RAD_Y = 1.5, 2.37
STEEL_Y, COPPER_Y = 1.22, 1.40
BULB = (-4.0, 0.6, 2.29)

groups: dict = {}


def add(group, *objs):
    groups.setdefault(group, []).extend(o for o in objs if o is not None)
    return objs[0] if objs else None


def box(name, mn, mx, mat, bevel=0.0, seg=1):
    return A.box_minmax(name, mn, mx, mat=mat, bevel=bevel, segments=seg)


# ------------------------------------------------------------------ shell
def shell():
    P = "M_Plaster_Wall"
    north = box("wall_n", (X0 - T, Y1, 0), (X1 + T, Y1 + T, H), P)
    south = box("wall_s", (X0 - T, Y0 - T, 0), (X1 + T, Y0, H), P)
    east = box("wall_e", (X1, Y0, 0), (X1 + T, Y1, H), P)
    west = box("wall_w", (X0 - T, Y0, 0), (X0, Y1, H), P)
    M.boolean(north, box("cut_win", (WIN_X0, Y1 - 0.1, WIN_Z0), (WIN_X1, Y1 + T + 0.1, WIN_Z1), P))
    M.boolean(east, box("cut_door", (X1 - 0.1, DOOR_Y0, -0.1), (X1 + T + 0.1, DOOR_Y1, DOOR_H), P))
    M.boolean(south, box("cut_safe", (SAFE_X0 - 0.006, Y0 - T - 0.1, SAFE_Z0 - 0.006),
                         (SAFE_X1 + 0.006, Y0 + 0.1, SAFE_Z1 + 0.006), P))
    M.boolean(west, box("cut_book", (X0 - T - 0.1, BK_Y0, -0.1), (X0 + 0.1, BK_Y1, BK_H), P))
    M.boolean(west, box("cut_vent", (X0 - 0.07, VENT_Y - 0.215, VENT_Z - 0.115),
                        (X0 + 0.1, VENT_Y + 0.215, VENT_Z + 0.115), P))
    # soft plaster arris on the bookcase opening (light leaks along it when the safelight is on)
    def arris(v0, v1):
        same_face = any(abs(v0.x - fx) < 1e-4 and abs(v1.x - fx) < 1e-4 for fx in (X0, X0 - T))
        if not same_face:
            return False
        on_side = all(abs(v.y - BK_Y0) < 1e-4 or abs(v.y - BK_Y1) < 1e-4 for v in (v0, v1))
        on_head = all(abs(v.z - BK_H) < 1e-4 and BK_Y0 - 1e-4 <= v.y <= BK_Y1 + 1e-4 for v in (v0, v1))
        return (on_side and max(v0.z, v1.z) <= BK_H + 1e-4) or on_head
    A.bevel_edges(west, arris, 0.008, 2)

    # darkroom walls (stained)
    S = "M_Plaster_Stained"
    dw = [box("dwall_w", (DX0 - T, DY0 - T, 0), (DX0, DY1 + T, DH), S),
          box("dwall_n", (DX0, DY1, 0), (DX1, DY1 + T, DH), S),
          box("dwall_s", (DX0, DY0 - T, 0), (DX1, DY0, DH), S)]

    def wall_mat(c, n, cur):
        # darkroom side of the shared west wall -> stained; vent recess -> dark steel
        if n.x < -0.9 and abs(c.x - (X0 - T)) < 1e-3:
            return S
        if X0 - 0.075 < c.x < X0 - 1e-4 and abs(c.y - VENT_Y) < 0.22 and abs(c.z - VENT_Z) < 0.12:
            return "M_Steel_Dark"
        return None
    A.mat_by_face(west, wall_mat)
    add("walls", north, south, east, west, *dw)

    # floor slabs (one big parquet plane per room, world UVs continue through the opening)
    F = "M_Wood_Floor"
    add("floor", box("floor_lab", (X0 - T, Y0 - T, -0.12), (X1 + T, Y1 + T, 0.0), F),
        box("floor_dark", (DX0 - T, DY0 - T, -0.12), (X0 - T, DY1 + T, 0.0), F))
    C = "M_Ceiling"
    add("ceiling", box("ceil_lab", (X0 - T, Y0 - T, H), (X1 + T, Y1 + T, H + 0.15), C),
        box("ceil_dark", (DX0 - T, DY0 - T, DH), (X0 - T, DY1 + T, DH + 0.15), C))


# ------------------------------------------------------------------ wainscot
WALLS = {
    # origin, inward normal, runs (local x from, to, n panels, end stile)
    "south": ((X1, Y0, 0), (0, 1, 0), [(0.0, 6.0, 10, 0.05)]),
    "east": ((X1, Y1, 0), (-1, 0, 0), [(0.0, 2.8, 5, 0.07), (4.0, 5.0, 2, 0.07)]),
    "north": ((X0, Y1, 0), (0, -1, 0), [(0.0, 6.0, 10, 0.05)]),
    "west": ((X0, Y0, 0), (1, 0, 0), [(0.0, 2.55, 4, 0.07), (3.65, 5.0, 2, 0.07)]),
}
MOULD = [(0.0, 0.0), (0.0, 0.006), (0.005, 0.011), (0.012, 0.0125), (0.021, 0.005), (0.024, 0.0)]
MOULD_W = 0.024


def wainscot():
    for key, (origin, normal, runs) in WALLS.items():
        wf = A.WallFrame(origin, normal)
        fm = A.frame_matrix(wf.world(0, -BACK_T, 0), wf.ux, (0, 0, 1), wf.n)
        for r, (xa, xb, n, e) in enumerate(runs):
            b = M.box(f"wain_back_{key}_{r}", (xb - xa, BACK_T, WAIN_TOP),
                      loc=((xa + xb) / 2, -BACK_T / 2, WAIN_TOP / 2), mat="M_Wood_Panel", bevel=0.002, segments=1)
            add("panel", A.place(b, wf.m))
            s = 0.10
            pw = (xb - xa - 2 * e - (n - 1) * s) / n
            for i in range(n):
                a0 = xa + e + i * (pw + s)
                a1 = a0 + pw
                path = A.rect_path(fm, a0, a1, PANEL_Z0, PANEL_Z1)
                add("walnut", A.sweep(f"wain_mould_{key}_{r}_{i}", MOULD, path, up=wf.n, closed=True,
                                      mat="M_Wood_Walnut"))
                add("panel", A.raised_field(f"wain_field_{key}_{r}_{i}", a0 + MOULD_W, a1 - MOULD_W,
                                            PANEL_Z0 + MOULD_W, PANEL_Z1 - MOULD_W, 0.032, 0.010, fm))


def profile_rail(h=0.07):
    """Chair rail: s out of the wall, u up. Cove under, torus bead, small cap (16 pts)."""
    pts = [(0.0, 0.0), (0.010, 0.0)]
    pts += A.arc(0.010, 0.010, 0.010, -90, 0, 2)[1:]
    pts += [(0.022, 0.014)]
    pts += A.arc(0.022, 0.030, 0.016, -90, 90, 5)[1:]
    pts += [(0.018, 0.050), (0.018, 0.056)]
    pts += A.arc(0.018, 0.063, 0.007, -90, 90, 2)[1:]
    pts += [(0.008, h), (0.0, h)]
    return pts


def trims():
    W = "M_Wood_Walnut"
    base = A.profile_baseboard(h=BASE_H, t=0.032)
    for i, path in enumerate([
        [(X0, BK_Y0, 0), (X0, Y0, 0), (X1, Y0, 0), (X1, DOOR_Y0 - CASING_W, 0)],
        [(X1, DOOR_Y1 + CASING_W, 0), (X1, Y1, 0), (X0, Y1, 0), (X0, BK_Y1, 0)],
    ]):
        add("walnut", A.sweep(f"baseboard_{i}", base, path, mat=W))
    rail = profile_rail()
    z = RAIL_Z
    for i, path in enumerate([
        [(X0, BK_Y0, z), (X0, CHALK_Y1, z)],
        [(X0, CHALK_Y0, z), (X0, Y0, z), (SAFE_X0 - 0.03, Y0, z)],
        [(SAFE_X1 + 0.03, Y0, z), (X1, Y0, z), (X1, DOOR_Y0 - CASING_W, z)],
        [(X1, DOOR_Y1 + CASING_W, z), (X1, P7_Y0, z)],
        [(X1, P7_Y1, z), (X1, Y1, z), (X0, Y1, z), (X0, BK_Y1, z)],
    ]):
        add("walnut", A.sweep(f"chair_rail_{i}", rail, path, mat=W))
    # plaster crown (cornice) all round the lab
    crown = A.profile_crown(h=0.15, p=0.14)
    add("ceiling", A.sweep("crown", crown, [(X0, Y0, H), (X1, Y0, H), (X1, Y1, H), (X0, Y1, H)],
                           closed=True, mat="M_Ceiling"))
    # darkroom: plain painted-over skirting
    plain = [(0.0, 0.0), (0.020, 0.0), (0.020, 0.105), (0.014, 0.118), (0.0, 0.122)]
    add("panel", A.sweep("dark_skirting", plain,
                         [(DX1, BK_Y1, 0), (DX1, DY1, 0), (DX0, DY1, 0), (DX0, DY0, 0), (DX1, DY0, 0), (DX1, BK_Y0, 0)],
                         mat="M_Wood_Panel"))


# ------------------------------------------------------------------ ceiling: beams, corbels, roses
def corbel(name, wall_x, inward, yc):
    """Walnut bracket under a beam end. inward = +1 (west wall, room is +x) or -1 (east wall)."""
    pts = [(0.0, 2.90), (0.050, 2.90), (0.064, 2.908), (0.072, 2.922), (0.070, 2.940)]
    pts += A.arc(0.25, 2.95, 0.18, 178, 92, 6)
    pts += [(0.25, BEAM_Z0 - 0.02), (0.25, BEAM_Z0 + 0.01), (0.0, BEAM_Z0 + 0.01)]
    pts = A.dedupe(pts)
    o = M.extrude_profile(name, pts, 0.12, mat="M_Wood_Walnut", bevel=0.004)
    n = Vector((inward, 0, 0))
    ez = n.cross(Vector((0, 0, 1)))
    org = Vector((wall_x, yc, 0)) - ez * 0.06
    o.data.transform(A.frame_matrix(org, n, (0, 0, 1), ez))
    return o


def ceiling_parts():
    for sy in (1, -1):
        yc = sy * BEAM_Y
        add("walnut", box(f"beam_{sy}", (X0 - 0.05, yc - BEAM_W / 2, BEAM_Z0), (X1 + 0.05, yc + BEAM_W / 2, H + 0.01),
                          "M_Wood_Walnut", bevel=0.014, seg=1))
        add("walnut", corbel(f"corbel_w_{sy}", X0, 1, yc), corbel(f"corbel_e_{sy}", X1, -1, yc))
    for i, (x, y) in enumerate(ROSES):
        r = ROSE_R
        prof = [(0.0, -0.016), (0.072, -0.016), (0.078, -0.022), (0.086, -0.030), (0.096, -0.027),
                (0.106, -0.031), (0.118, -0.025), (0.130, -0.013), (r, -0.004), (r, 0.0)]
        o = M.lathe(f"rose_{i}", prof, segments=32, mat="M_Ceiling")
        petals = 8
        for v in o.data.vertices:
            rr = math.hypot(v.co.x, v.co.y)
            if 0.088 < rr < 0.135:
                a = math.atan2(v.co.y, v.co.x)
                c = math.cos(petals * a)
                f = 1.0 + 0.05 * c
                v.co.x *= f
                v.co.y *= f
                v.co.z *= 1.0 + 0.30 * c
        o.location = (x, y, H)
        add("ceiling", o)


# ------------------------------------------------------------------ window
def window():
    W = "M_Wood_Walnut"
    # stone sill with rounded nosing; horns run 0.12 m past the opening into the wall
    add("stone", box("sill", (WIN_X0 - 0.12, Y1 - 0.14, SILL_TOP - 0.07), (WIN_X1 + 0.12, Y1 + T, SILL_TOP),
                     "M_Stone", bevel=0.012, seg=2))
    # bed moulding under the sill nosing
    bed = [(0.0, 0.0), (0.0, -0.035), (0.010, -0.032), (0.022, -0.020), (0.028, -0.006), (0.030, 0.0)]
    add("stone", A.sweep("sill_bed", bed, [(WIN_X1 + 0.10, Y1, SILL_TOP - 0.07), (WIN_X0 - 0.10, Y1, SILL_TOP - 0.07)],
                         mat="M_Stone"))
    # architrave (room side) standing on the sill
    cas = A.profile_casing(w=0.095, t=0.030)
    add("walnut", A.sweep("win_casing", cas, [(WIN_X0, Y1, SILL_TOP), (WIN_X0, Y1, WIN_Z1),
                                              (WIN_X1, Y1, WIN_Z1), (WIN_X1, Y1, SILL_TOP)],
                          up=(0, -1, 0), mat=W))
    # fixed frame
    fy0, fy1 = Y1 + 0.08, Y1 + 0.16
    fw = 0.06
    tz0, tz1 = 2.33, 2.40
    mx0, mx1 = 1.47, 1.53
    parts = [
        box("wf_l", (WIN_X0, fy0, SILL_TOP), (WIN_X0 + fw, fy1, WIN_Z1), W, 0.004),
        box("wf_r", (WIN_X1 - fw, fy0, SILL_TOP), (WIN_X1, fy1, WIN_Z1), W, 0.004),
        box("wf_head", (WIN_X0 + fw, fy0, WIN_Z1 - fw), (WIN_X1 - fw, fy1, WIN_Z1), W, 0.004),
        box("wf_sill", (WIN_X0 + fw, fy0 - 0.012, SILL_TOP), (WIN_X1 - fw, fy1, SILL_TOP + fw), W, 0.006),
        box("wf_transom", (WIN_X0 + fw, fy0 - 0.008, tz0), (WIN_X1 - fw, fy1, tz1), W, 0.005),
        box("wf_mullion", (mx0, fy0 - 0.004, SILL_TOP + fw), (mx1, fy1, tz0), W, 0.004),
    ]
    add("walnut", *parts)
    glass = []
    sy0, sy1 = Y1 + 0.092, Y1 + 0.142        # sash depth
    for side, (sx0, sx1) in enumerate(((WIN_X0 + fw, mx0), (mx1, WIN_X1 - fw))):
        sz0, sz1 = SILL_TOP + fw, tz0
        st, tr, br, gb = 0.045, 0.045, 0.06, 0.02
        sash = [box(f"sash{side}_l", (sx0, sy0, sz0), (sx0 + st, sy1, sz1), W, 0.004),
                box(f"sash{side}_r", (sx1 - st, sy0, sz0), (sx1, sy1, sz1), W, 0.004),
                box(f"sash{side}_t", (sx0 + st, sy0, sz1 - tr), (sx1 - st, sy1, sz1), W, 0.004),
                box(f"sash{side}_b", (sx0 + st, sy0, sz0), (sx1 - st, sy1, sz0 + br), W, 0.004)]
        ix0, ix1, iz0, iz1 = sx0 + st, sx1 - st, sz0 + br, sz1 - tr
        xm = (ix0 + ix1) / 2
        sash.append(box(f"sash{side}_bv", (xm - gb / 2, sy0 + 0.006, iz0), (xm + gb / 2, sy1 - 0.006, iz1), W, 0.003))
        for k in (1, 2):
            zk = iz0 + (iz1 - iz0) * k / 3
            sash.append(box(f"sash{side}_bh{k}", (ix0, sy0 + 0.006, zk - gb / 2), (ix1, sy1 - 0.006, zk + gb / 2), W, 0.003))
        add("walnut", *sash)
        glass.append(box(f"glass_s{side}", (ix0 - 0.008, Y1 + 0.115, iz0 - 0.008), (ix1 + 0.008, Y1 + 0.119, iz1 + 0.008),
                         "M_Glass"))
    # fanlight: fixed, 3 panes
    for k in (1, 2):
        xk = WIN_X0 + fw + (WIN_X1 - WIN_X0 - 2 * fw) * k / 3
        add("walnut", box(f"fan_bar{k}", (xk - 0.011, fy0 + 0.01, tz1), (xk + 0.011, fy1 - 0.01, WIN_Z1 - fw), W, 0.003))
    glass.append(box("glass_fan", (WIN_X0 + fw - 0.008, Y1 + 0.118, tz1 - 0.008),
                     (WIN_X1 - fw + 0.008, Y1 + 0.122, WIN_Z1 - fw + 0.008), "M_Glass"))
    # brass espagnolette handle on the meeting stile + two casement stays
    B = "M_Brass_Aged"
    hx = mx1 + 0.0225
    add("brass", box("esp_plate", (hx - 0.013, sy0 - 0.004, 1.86), (hx + 0.013, sy0, 2.00), B, 0.0015))
    lever = M.box("esp_lever", (0.012, 0.014, 0.10), loc=(hx, sy0 - 0.012, 1.93 - 0.035), rot=(0, 0, 0), mat=B,
                  bevel=0.003, segments=1)
    add("brass", lever, M.cylinder("esp_boss", 0.009, 0.014, loc=(hx, sy0 - 0.009, 1.93), rot=(math.pi / 2, 0, 0),
                                   verts=10, mat=B, bevel=0.0015, segments=1))
    for side, x in enumerate((1.24, 1.76)):
        add("brass", box(f"stay{side}", (x - 0.11, sy0 - 0.010, SILL_TOP + fw + 0.01), (x + 0.11, sy0 - 0.004, SILL_TOP + fw + 0.022),
                         B, 0.002))
    # iron bars on the outside face
    I = "M_Steel_Dark"
    by = Y1 + T - 0.016
    for k in range(4):
        x = WIN_X0 + 0.22 * (k + 1)
        add("iron", M.cylinder(f"bar{k}", 0.012, WIN_Z1 - WIN_Z0 + 0.12, loc=(x, by, (WIN_Z0 + WIN_Z1) / 2),
                               verts=10, mat=I, bevel=0.0))
    for z in (1.82, 2.50):
        add("iron", box(f"bar_tie_{z}", (WIN_X0 - 0.04, by - 0.006, z - 0.02), (WIN_X1 + 0.04, by + 0.006, z + 0.02), I, 0.002))
    return glass


# ------------------------------------------------------------------ radiator
def radiator():
    P = "M_Steel_Painted"
    n, pitch = 12, 0.07
    x0 = RAD_X - pitch * (n - 1) / 2
    prof = [(0.0, 0.11), (0.019, 0.116), (0.026, 0.138), (0.019, 0.178), (0.022, 0.21), (0.022, 0.69),
            (0.019, 0.722), (0.026, 0.762), (0.019, 0.784), (0.0, 0.79)]
    for i in range(n):
        o = M.lathe(f"rad_sec{i}", prof, segments=8, mat=P)
        o.data.transform(Matrix.Diagonal((1.0, 2.9, 1.0, 1.0)))
        o.location = (x0 + i * pitch, RAD_Y, 0)
        add("iron", o)
    for z in (0.138, 0.762):
        add("iron", M.cylinder(f"rad_hub{z}", 0.017, pitch * (n - 1), loc=(RAD_X, RAD_Y, z), rot=(0, math.pi / 2, 0),
                               verts=8, mat=P, bevel=0.0))
    for x in (x0, x0 + pitch * (n - 1)):
        add("iron", M.lathe("rad_foot", [(0.0, 0.0), (0.024, 0.0), (0.026, 0.008), (0.017, 0.03), (0.016, 0.115), (0.0, 0.12)],
                            loc=(x, RAD_Y, 0), segments=8, mat=P))
    # copper flow with an angle valve (left) and return with a lockshield (right)
    Cu, B = "M_Copper", "M_Brass_Aged"
    xl, xr = x0 - 0.075, x0 + pitch * (n - 1) + 0.075
    add("copper", A.tube("rad_flow", [(xl, RAD_Y + 0.03, -0.01), (xl, RAD_Y + 0.03, 0.138), (x0, RAD_Y + 0.03, 0.138)],
                         0.0095, sides=8, fillet=0.03, mat=Cu))
    add("copper", A.tube("rad_return", [(xr, RAD_Y + 0.03, -0.01), (xr, RAD_Y + 0.03, 0.138), (xr - 0.075, RAD_Y + 0.03, 0.138)],
                         0.0095, sides=8, fillet=0.03, mat=Cu))
    add("brass", M.lathe("valve_body", [(0.0, 0.10), (0.017, 0.10), (0.018, 0.115), (0.018, 0.16), (0.012, 0.168),
                                        (0.006, 0.20), (0.0, 0.205)], loc=(xl, RAD_Y + 0.03, 0), segments=10, mat=B))
    add("brass", M.lathe("valve_wheel", [(0.0, 0.198), (0.028, 0.198), (0.030, 0.204), (0.030, 0.212), (0.024, 0.218),
                                         (0.0, 0.22)], loc=(xl, RAD_Y + 0.03, 0), segments=12, mat="M_Bakelite"))
    add("brass", M.lathe("lockshield", [(0.0, 0.11), (0.016, 0.11), (0.017, 0.16), (0.010, 0.175), (0.0, 0.178)],
                         loc=(xr, RAD_Y + 0.03, 0), segments=10, mat=B))
    add("brass", M.cylinder("bleed", 0.006, 0.024, loc=(xr - 0.04, RAD_Y + 0.0, 0.762), rot=(0, math.pi / 2, 0),
                            verts=8, mat=B, bevel=0.001, segments=1))
    for x in (xl, xr):    # floor escutcheons
        add("brass", M.cylinder("pipe_rose", 0.024, 0.004, loc=(x, RAD_Y + 0.03, 0.002), verts=12, mat=B,
                                bevel=0.0012, segments=1))


# ------------------------------------------------------------------ conduit / pipes / vent
def collar(name, p, axis, r, length=0.035, mat="M_Steel_Dark"):
    rot = {"x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0), "z": (0, 0, 0)}[axis]
    return M.cylinder(name, r, length, loc=p, rot=rot, verts=8, mat=mat, bevel=0.0012, segments=1)


def services():
    St, Cu, B = "M_Steel_Dark", "M_Copper", "M_Brass_Aged"
    wx = X1 - 0.03
    steel = [(wx, STEEL_Y, 1.88), (wx, STEEL_Y, 3.13), (X1 - 0.20, STEEL_Y, H - 0.016), (-0.57, STEEL_Y, H - 0.016)]
    add("iron", A.tube("conduit", steel, 0.013, sides=8, fillet=0.07, fillet_segs=4, mat=St))
    cx = X1 - 0.025
    cu = [(cx, COPPER_Y, 1.88), (cx, COPPER_Y, 3.13), (X1 - 0.20, COPPER_Y, H - 0.013),
          (X0 + 0.20, COPPER_Y, H - 0.013), (X0 + 0.025, COPPER_Y, 3.13), (X0 + 0.025, COPPER_Y, 2.86),
          (X0 + 0.025, VENT_Y + VENT_W / 2 - 0.012, 2.86)]
    add("copper", A.tube("copper_pipe", cu, 0.009, sides=8, fillet=0.06, fillet_segs=4, mat=Cu))
    # couplings + saddles (fixing blocks to the wall / ceiling)
    fix = []
    for z in (2.05, 2.75):
        fix.append(collar("cpl", (wx, STEEL_Y, z), "z", 0.017))
        fix.append(box("sad", (X1 - 0.017, STEEL_Y - 0.012, z - 0.012), (X1, STEEL_Y + 0.012, z + 0.012), St, 0.002))
        fix.append(collar("cpc", (cx, COPPER_Y, z), "z", 0.0125, 0.03, B))
        fix.append(box("sadc", (X1 - 0.016, COPPER_Y - 0.009, z - 0.009), (X1, COPPER_Y + 0.009, z + 0.009), B, 0.002))
    for x in (2.0, 0.9, -0.1):
        fix.append(collar("cpl", (x, STEEL_Y, H - 0.016), "x", 0.017))
        fix.append(box("sad", (x - 0.012, STEEL_Y - 0.012, H - 0.004), (x + 0.012, STEEL_Y + 0.012, H), St, 0.0015))
    for x in (1.8, 0.4, -1.0, -2.2):
        fix.append(collar("cpc", (x, COPPER_Y, H - 0.013), "x", 0.0125, 0.03, B))
    for y in (0.6, -0.6):
        fix.append(collar("cpc", (X0 + 0.025, y, 2.86), "y", 0.0125, 0.03, B))
        fix.append(box("sadc", (X0, y - 0.009, 2.851), (X0 + 0.016, y + 0.009, 2.869), B, 0.002))
    # cast junction box at the end of the conduit
    fix.append(M.lathe("jbox", [(0.0, -0.052), (0.040, -0.052), (0.046, -0.048), (0.048, -0.040), (0.048, -0.010),
                                (0.052, -0.006), (0.052, 0.0)], loc=(-0.6, STEEL_Y, H), segments=16, mat=St))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        fix.append(A.screw("jbox_screw", 0.004, (-0.6 + 0.03 * math.cos(a), STEEL_Y + 0.03 * math.sin(a), H - 0.052),
                           (0, 0, -1), B, 30 * k))
    # gland where the copper pipe enters the vent frame
    fix.append(collar("vent_gland", (X0 + 0.025, VENT_Y + VENT_W / 2 - 0.004, 2.86), "y", 0.015, 0.02, B))
    for o in fix:
        add("brass" if o.data.materials[0].name == B else "iron", o)

    # vent grille: brass frame, louvres, dark recess behind (cut in shell())
    vw, vh = VENT_W, VENT_H
    frame = [(0.0, 0.0), (0.0, 0.010), (0.006, 0.019), (0.028, 0.019), (0.034, 0.012), (0.034, 0.0)]
    path = [(X0, VENT_Y - vw / 2, VENT_Z - vh / 2), (X0, VENT_Y + vw / 2, VENT_Z - vh / 2),
            (X0, VENT_Y + vw / 2, VENT_Z + vh / 2), (X0, VENT_Y - vw / 2, VENT_Z + vh / 2)]
    add("brass", A.sweep("vent_frame", frame, path, up=(1, 0, 0), closed=True, mat=B))
    for k in range(5):
        z = VENT_Z - 0.10 + k * 0.05
        add("brass", M.box(f"louvre{k}", (0.004, vw - 0.06, 0.05), loc=(X0 - 0.012, VENT_Y, z), rot=(0, math.radians(-50), 0),
                           mat=B, bevel=0.0012, segments=1))
    for (dy, dz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        add("brass", A.screw("vent_screw", 0.005, (X0 + 0.019, VENT_Y + dy * (vw / 2 - 0.017), VENT_Z + dz * (vh / 2 - 0.017)),
                             (1, 0, 0), B, 20))


# ------------------------------------------------------------------ safe recess
def safe_recess():
    St = "M_Steel_Dark"
    yf, yb, t = Y0, Y0 - SAFE_D, 0.006
    parts = [
        box("safe_bot", (SAFE_X0 - t, yb - t, SAFE_Z0 - t), (SAFE_X1 + t, yf, SAFE_Z0), St),
        box("safe_top", (SAFE_X0 - t, yb - t, SAFE_Z1), (SAFE_X1 + t, yf, SAFE_Z1 + t), St),
        box("safe_l", (SAFE_X0 - t, yb - t, SAFE_Z0), (SAFE_X0, yf, SAFE_Z1), St),
        box("safe_r", (SAFE_X1, yb - t, SAFE_Z0), (SAFE_X1 + t, yf, SAFE_Z1), St),
        box("safe_back", (SAFE_X0, yb - t, SAFE_Z0), (SAFE_X1, yb, SAFE_Z1), St),
        box("safe_housing", (SAFE_X0 - 0.02, yb - 0.03, SAFE_Z0 - 0.02), (SAFE_X1 + 0.02, Y0 - T, SAFE_Z1 + 0.02), St),
    ]
    fw, ft = 0.03, 0.016
    parts += [
        box("safe_fl_b", (SAFE_X0 - fw, yf, SAFE_Z0 - fw), (SAFE_X1 + fw, yf + ft, SAFE_Z0), St, 0.003),
        box("safe_fl_t", (SAFE_X0 - fw, yf, SAFE_Z1), (SAFE_X1 + fw, yf + ft, SAFE_Z1 + fw), St, 0.003),
        box("safe_fl_l", (SAFE_X0 - fw, yf, SAFE_Z0), (SAFE_X0, yf + ft, SAFE_Z1), St, 0.003),
        box("safe_fl_r", (SAFE_X1, yf, SAFE_Z0), (SAFE_X1 + fw, yf + ft, SAFE_Z1), St, 0.003),
    ]
    add("iron", *parts)


# ------------------------------------------------------------------ darkroom fixture
def darkroom_fixture():
    bx, by, bz = BULB
    K = "M_Bakelite"
    parts = [M.lathe("dr_rose", [(0.0, -0.024), (0.030, -0.024), (0.040, -0.018), (0.046, -0.007), (0.046, 0.0)],
                     loc=(bx, by, DH), segments=16, mat=K),
             A.tube("dr_cord", [(bx, by, DH - 0.02), (bx, by, 2.44)], 0.0035, sides=6, mat="M_Fabric"),
             M.lathe("dr_socket", [(0.0, 2.372), (0.017, 2.372), (0.020, 2.379), (0.020, 2.414), (0.013, 2.430),
                                   (0.006, 2.442), (0.0, 2.446)], loc=(bx, by, 0), segments=14, mat=K)]
    base = [(0.0, 2.346)]
    for k in range(4):
        z = 2.348 + k * 0.006
        base += [(0.0125, z), (0.0137, z + 0.003)]
    base += [(0.013, 2.372), (0.0, 2.372)]
    parts.append(M.lathe("dr_base", base, loc=(bx, by, 0), segments=12, mat="M_Brass_Aged"))
    fixture = M.join(parts, "darkroom_fixture")
    bulb = M.lathe("darkroom_bulb", [(0.0, 2.236), (0.012, 2.239), (0.024, 2.252), (0.030, 2.270), (0.031, 2.290),
                                     (0.028, 2.310), (0.021, 2.327), (0.015, 2.340), (0.0125, 2.347)],
                   loc=(bx, by, 0), segments=16, mat="M_Emissive_Red")
    M.set_origin(bulb, (bx, by, bz))
    M.empty("darkroom_light_origin", (bx, by, bz))
    return fixture, bulb


# ------------------------------------------------------------------ build
GROUP_NAMES = {"walls": "room_walls", "floor": "room_floor", "ceiling": "room_ceiling", "panel": "room_wainscot",
               "walnut": "room_woodwork", "stone": "room_stone", "iron": "room_metal", "copper": "room_copper",
               "brass": "room_brass"}


def build():
    M.reset_scene()
    A.prepare_materials()
    A.prepare_tinted("M_Plaster_Stained", "plaster_wall", "C9AE86")
    groups.clear()
    shell()
    wainscot()
    trims()
    ceiling_parts()
    glass = window()
    radiator()
    services()
    safe_recess()
    fixture, bulb = darkroom_fixture()
    objs = {}
    for g, lst in groups.items():
        objs[g] = M.join(lst, GROUP_NAMES[g])
    wg = M.join(glass, "window_glass")
    M.finalize()
    for g in ("walnut", "panel"):
        A.grain_uv(objs[g])
    report = " ".join(f"{GROUP_NAMES[g]}={A.tris(o)}" for g, o in objs.items())
    print(f"[{NAME}] tris: {report} window_glass={A.tris(wg)} fixture={A.tris(fixture)} bulb={A.tris(bulb)} "
          f"TOTAL={M.tri_count()}")
    return objs


# ------------------------------------------------------------------ QA
MODELS = M.MODELS_DIR


def qa_lights(dark=False):
    A.qa_light("moon", "SUN", (1.5, 5.5, 4.5), 2.2, "8FB2E0", size=0.03, target=(0.3, -0.6, 0.0))
    for i, (x, y) in enumerate(ROSES):
        A.qa_light(f"pend{i}", "POINT", (x, y, 2.40), 70.0, "FFC58A", size=0.08)
    A.qa_light("desk", "POINT", (-1.05, 2.15, 1.18), 18.0, "FFB46B", size=0.05)
    A.qa_light("fill", "AREA", (0.0, 0.0, 3.2), 110.0, "BFD0E8", size=3.0, target=(0.0, 0.0, 0.0))
    A.qa_light("safelight", "POINT", (-3.6, 0.6, 2.25), 5.0, "FF2A1A", size=0.05)
    if dark:   # neutral QA fill so the darkroom geometry is readable
        A.qa_light("darkfill", "AREA", (-4.0, 0.6, 2.5), 30.0, "FFE6CC", size=1.2, target=(-4.0, 0.6, 0.0))
    A.qa_light("maglock", "POINT", (2.85, -0.9, 2.35), 3.0, "FF3B2F", size=0.03)


def qa_imports(west=False):
    A.import_glb(os.path.join(MODELS, "pendant_lamp.glb"), (-0.6, 0.6, 3.4))
    A.import_glb(os.path.join(MODELS, "pendant_lamp.glb"), (1.2, -0.8, 3.4))
    A.import_glb(os.path.join(MODELS, "desk.glb"), (-0.5, 2.1, 0.0))
    if os.path.exists(os.path.join(MODELS, "door_lab7.glb")):
        A.import_glb(os.path.join(MODELS, "door_lab7.glb"), (3.0, -0.9, 0.0), -90.0)
    if west:
        A.import_glb(os.path.join(MODELS, "bookshelf.glb"), (-3.1, 1.15, 0.0), 90.0)


def shot(name, cam, target, lens=22, res=(960, 540), samples=32, dark=False, west=False):
    qa_lights(dark)
    qa_imports(west)
    M.render_preview(name, cam, target, lens=lens, res=res, samples=samples, world_strength=0.04,
                     lights=A.NO_LIGHTS)
    A.qa_reset_render_objects()


def main():
    args = M.main_guard()
    build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(32, bounces=4)
    only = [a for a in args if a.startswith("--shot=")]
    want = {s.split("=", 1)[1] for s in only}

    def on(k):
        return not want or k in want
    if on("1"):   # player point, looking at the window wall
        shot(NAME, (0.2, -0.25, 1.55), (0.0, 2.5, 1.4))
    if on("2"):   # towards the door / east wall / safe
        shot(NAME + "_2", (-1.6, 1.4, 1.6), (3.0, -1.0, 1.5))
    if on("3"):   # west wall: bookcase opening, chalkboard zone, vent, pipe
        shot(NAME + "_3", (1.8, 0.2, 1.6), (-3.0, -0.4, 1.7), west=True)
    if on("4"):   # darkroom from the opening
        shot(NAME + "_4", (-3.3, 0.45, 1.5), (-4.8, 0.75, 1.75), lens=14, dark=True)
    if on("5"):   # ceiling: beams, roses, conduit
        shot(NAME + "_5", (-1.8, -1.6, 1.5), (1.2, 1.0, 3.3), lens=20)
    if on("6"):   # window, sill, bars and radiator close-up
        shot(NAME + "_6", (0.85, 1.05, 1.55), (1.55, 2.6, 1.45), lens=24)


main()
