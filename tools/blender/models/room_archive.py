"""room_archive.glb — Records Archive B shell, built directly in ROOM coordinates (Godot = Blender (x, z, -y)).
Place it at the origin with no rotation. Contract: docs/models/ch2.md §1 + §3 (results: docs/models/ch2_arch.md).

  Hall      interior x [-5, 5], z [-3.5, 3.5], floor 0, ceiling 3.6; walls 0.2 m thick outside the box
            (closed solids). Lower walls M_Paint_Green to 1.40, walnut dado rail at 1.37-1.44, cream plaster
            above, walnut baseboard 0.15, plaster crown; concrete pilasters N x=-0.55, S x=2.35, E z=2.2,
            W z=-2.7. Ceiling: plaster coffer grid (N-S beams x=+-1.5, E-W beam z=-0.2).
  Openings  vault x [0.45, 2.55] y [0.30, 2.40] (north); fire shutter x [2.9, 4.1] y [0, 2.3] (south) with the
            corridor stub behind; vent 0.62 x 0.37 at (-5, 2.55, 0.9) with a 0.35 deep duct (west);
            floor hatch hole 0.70 x 0.70 at (0.9, 0, 2.5) with a 0.36 deep void.
  Booth     walls N z [2.0, 2.1] x [-5, -1.0], E x [-1.1, -1.0] z [2.0, 3.5], slab y [2.8, 2.9] + parapet;
            window x [-3.4, -2.1] y [1.65, 2.25] (`booth_glass`, brass frame); doorway x [-1.95, -1.15]
            y [0, 2.1]; walnut panelling to 1.2, green paint above, enamel film-reel sign over the door;
            inside plain plaster, shelf (top 1.45) with film cans, fire bucket, conduit, `booth_bulb`.
  Tube run  `tube_glass` (outer r 0.045, inner 0.04) along tube_p0..p4 with 0.25 bends, the return line
            (tube_q0 ... 0.14 m to the side) and the Director's line through the north wall; brass sleeves,
            trapeze hangers, wall brackets, diverter box, wall junction box (`tube_run`).
  Lamps     10 caged bulkhead lamps at y 2.95: `elamp_<k>` body, `elamp_glass_<k>` amber glass,
            `elamp_light_<k>` empty at the bulb centre (k order: N x -4.3, -0.55, 3.2; E z -2.6, 0, 2.6;
            S x 0.6, 2.35; W z -2.7, 0.25).
  Shutter   `fire_shutter` (origin (3.5, 0, 3.45), rest = down), `shutter_frame` (rails, coil box, head
            bulkhead, threshold), `shutter_lamp` (M_Emissive_Red).
  Dressing  framed rules notice (M_Decal_ArchiveRules) on the east wall, wall clock stopped at 4:17 above the
            vault frame, conduits to the lamps.

    blender -b --factory-startup -P tools/blender/models/room_archive.py [-- --no-render] [--shots=hall,west,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G, GV, WF, gbox, lbox  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "room_archive"
X0, X1, Z0, Z1, H, T = -5.0, 5.0, -3.5, 3.5, 3.6, 0.2
DADO = 1.40
BASE_H = 0.15
CROWN_H = 0.15
GREEN, PLASTER, CONC, WAL = "M_Paint_Green", "M_Plaster_Wall", "M_Concrete", "M_Wood_Walnut"
BRASS, STEEL, PAINTED = "M_Brass_Aged", "M_Steel_Dark", "M_Steel_Painted"

# booth (outer faces N z = 2.0, E x = -1.0)
BX0, BX1, BZ0, BZ1, BT = -5.0, -1.0, 2.0, 3.5, 0.1
BOOTH_H, BOOTH_TOP = 2.8, 2.9
WIN = (-3.4, -2.1, 1.65, 2.25)
DOOR = (-1.95, -1.15, 2.1)
PANEL_TOP = 1.2

# wall frames: a along the wall, b up, c into the room
WN = WF((0, 0, Z0), (1, 0, 0), (0, 0, 1))
WS = WF((0, 0, Z1), (-1, 0, 0), (0, 0, -1))
WE = WF((X1, 0, 0), (0, 0, 1), (-1, 0, 0))
WW = WF((X0, 0, 0), (0, 0, -1), (1, 0, 0))
WBN = WF((0, 0, BZ0), (-1, 0, 0), (0, 0, -1))   # booth north face (hall side)
WBE = WF((BX1, 0, 0), (0, 0, -1), (1, 0, 0))    # booth east face (hall side)

PILASTERS = [(WN, -0.55), (WS, -2.35), (WE, 2.2), (WW, 2.7)]
# emergency lamps: (frame, a, c offset) in k order
ELAMPS = [(WN, -4.3, 0.0), (WN, -0.55, 0.12), (WN, 3.2, 0.0), (WE, -2.6, 0.0), (WE, 0.0, 0.0), (WE, 2.6, 0.0),
          (WS, -0.6, 0.0), (WS, -2.35, 0.12), (WW, 2.7, 0.12), (WW, -0.25, 0.0)]
ELAMP_Y = 2.95

TUBE_P = [(4.80, 2.35, -1.40), (4.80, 3.25, -1.40), (0.00, 3.25, -1.40), (0.00, 3.25, 0.25), (0.00, 2.25, 0.25)]
TUBE_Q = [(4.80, 2.35, -1.26), (4.80, 3.25, -1.26), (0.14, 3.25, -1.26), (0.14, 3.25, 0.25), (0.14, 2.25, 0.25)]
DIVERTER = (4.0, 3.25, -1.40)
TUBE_D = [(4.0, 3.25, -1.47), (4.0, 3.25, -3.38)]
R_OUT, R_IN, BEND = 0.045, 0.040, 0.25

HALL = [(-5.0, -3.5), (-5.0, 2.0), (-1.0, 2.0), (-1.0, 3.5), (5.0, 3.5), (5.0, -3.5)]
RECT = [(-5.0, -3.5), (-5.0, 3.5), (5.0, 3.5), (5.0, -3.5)]

groups: dict = {}


def add(group, *objs):
    groups.setdefault(group, []).extend(o for o in objs if o is not None)
    return objs[0] if objs else None


# ====================================================================== shell
def shell():
    # --- north wall (vault opening)
    nlo = gbox("wn_lo", (X0 - T, 0, Z0 - T), (X1 + T, DADO, Z0), GREEN)
    nhi = gbox("wn_hi", (X0 - T, DADO, Z0 - T), (X1 + T, H, Z0), PLASTER)
    for w in (nlo, nhi):
        M.boolean(w, gbox("cut_vault", (0.45, 0.30, Z0 - T - 0.1), (2.55, 2.40, Z0 + 0.1), CONC))

    def vault_reveal(c, n, cur):
        if 0.44 < c.x < 2.56 and 0.29 < c.z < 2.41 and abs(n.y) < 0.5:
            return CONC
        return None
    for w in (nlo, nhi):
        A.mat_by_face(w, vault_reveal)
    add("wall_n", nlo, nhi)

    # --- south wall (shutter opening); inside the booth the lower wall is plaster
    s_parts = [gbox("ws_lo_booth", (X0 - T, 0, Z1), (BX1 - 0.05, DADO, Z1 + T), PLASTER),
               gbox("ws_lo", (BX1 - 0.05, 0, Z1), (X1 + T, DADO, Z1 + T), GREEN),
               gbox("ws_hi", (X0 - T, DADO, Z1), (X1 + T, H, Z1 + T), PLASTER)]
    for w in s_parts[1:]:
        M.boolean(w, gbox("cut_shutter", (2.9, -0.1, Z1 - 0.1), (4.1, 2.3, Z1 + T + 0.1), PLASTER))
    add("wall_s", *s_parts)

    # --- east wall
    add("wall_e", gbox("we_lo", (X1, 0, Z0), (X1 + T, DADO, Z1), GREEN),
        gbox("we_hi", (X1, DADO, Z0), (X1 + T, H, Z1), PLASTER))

    # --- west wall (vent opening + duct); inside the booth the lower wall is plaster
    w_parts = [gbox("ww_lo", (X0 - T, 0, Z0), (X0, DADO, BZ0 + 0.05), GREEN),
               gbox("ww_lo_booth", (X0 - T, 0, BZ0 + 0.05), (X0, DADO, Z1), PLASTER),
               gbox("ww_hi", (X0 - T, DADO, Z0), (X0, H, Z1), PLASTER)]
    vz0, vz1, vy0, vy1 = 0.59, 1.21, 2.365, 2.735
    M.boolean(w_parts[2], gbox("cut_vent", (X0 - T - 0.1, vy0, vz0), (X0 + 0.1, vy1, vz1), STEEL))

    def vent_reveal(c, n, cur):
        if c.x < X0 + 1e-4 and vz0 - 0.01 < -c.y < vz1 + 0.01 and vy0 - 0.01 < c.z < vy1 + 0.01 and abs(n.x) < 0.5:
            return STEEL
        return None
    A.mat_by_face(w_parts[2], vent_reveal)
    # duct box behind the opening (inward faces), 0.35 deep from the wall face, 1 mm inside the reveal
    e = 0.001
    xa, xb = X0 - 0.35, X0
    za, zb, ya, yb = vz0 + e, vz1 - e, vy0 + e, vy1 - e
    bm = bmesh.new()

    def q(p0, p1, p2, p3):
        bm.faces.new([bm.verts.new(G(*p)) for p in (p0, p1, p2, p3)])
    q((xa, ya, za), (xa, ya, zb), (xa, yb, zb), (xa, yb, za))       # back
    q((xa, ya, za), (xb, ya, za), (xb, ya, zb), (xa, ya, zb))       # floor
    q((xa, yb, za), (xa, yb, zb), (xb, yb, zb), (xb, yb, za))       # top
    q((xa, ya, za), (xa, yb, za), (xb, yb, za), (xb, ya, za))       # side
    q((xa, ya, zb), (xb, ya, zb), (xb, yb, zb), (xa, yb, zb))       # side
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    duct = A.obj_from_bm("vent_duct", bm, STEEL)
    _face_inward(duct, G(X0 - 0.17, (vy0 + vy1) / 2, (vz0 + vz1) / 2))
    add("wall_w", *w_parts, duct)

    # --- floor with the hatch hole + void
    fl = gbox("floor_slab", (X0 - T, -0.12, Z0 - T), (X1 + T, 0.0, Z1 + T), "M_Linoleum")
    hx0, hx1, hz0, hz1 = 0.55, 1.25, 2.15, 2.85
    M.boolean(fl, gbox("cut_hatch", (hx0, -0.3, hz0), (hx1, 0.1, hz1), CONC))

    def hatch_reveal(c, n, cur):
        if hx0 - 0.01 < c.x < hx1 + 0.01 and hz0 - 0.01 < -c.y < hz1 + 0.01 and abs(n.z) < 0.5:
            return CONC
        return None
    A.mat_by_face(fl, hatch_reveal)
    bm = bmesh.new()
    yb0, yb1 = -0.36, -0.12
    q((hx0, yb0, hz0), (hx1, yb0, hz0), (hx1, yb0, hz1), (hx0, yb0, hz1))
    q((hx0, yb0, hz0), (hx0, yb1, hz0), (hx1, yb1, hz0), (hx1, yb0, hz0))
    q((hx0, yb0, hz1), (hx1, yb0, hz1), (hx1, yb1, hz1), (hx0, yb1, hz1))
    q((hx0, yb0, hz0), (hx0, yb0, hz1), (hx0, yb1, hz1), (hx0, yb1, hz0))
    q((hx1, yb0, hz0), (hx1, yb1, hz0), (hx1, yb1, hz1), (hx1, yb0, hz1))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    void = A.obj_from_bm("hatch_void", bm, CONC)
    _face_inward(void, G(0.9, -0.24, 2.5))
    add("floor", fl, void)

    # --- ceiling slab + coffer beams
    add("ceiling", gbox("ceiling_slab", (X0 - T, H, Z0 - T), (X1 + T, H + 0.15, Z1 + T), "M_Ceiling"))
    by = H - 0.16
    for x in (-1.5, 1.5):
        add("ceiling", gbox(f"beam_ns_{x}", (x - 0.12, by, Z0), (x + 0.12, H + 0.01, Z1), "M_Ceiling", bevel=0.014))
    for (xa_, xb_) in ((X0, -1.62), (-1.38, 1.38), (1.62, X1)):
        add("ceiling", gbox(f"beam_ew_{xa_}", (xa_, by, -0.32), (xb_, H + 0.01, -0.08), "M_Ceiling", bevel=0.014))


def _face_inward(obj, inside_blender):
    """Flip faces of a liner so they face `inside_blender` (a Blender point)."""
    me = obj.data
    for p in me.polygons:
        if (inside_blender - p.center).dot(p.normal) < 0:
            p.flip()
    me.update()


# ====================================================================== pilasters
def pilasters():
    for i, (wf, a) in enumerate(PILASTERS):
        grp = {id(WN): "wall_n", id(WS): "wall_s", id(WE): "wall_e", id(WW): "wall_w"}[id(wf)]
        add(grp,
            lbox(f"pil{i}_base", wf, a - 0.22, a + 0.22, 0.0, 0.18, 0.0, 0.15, CONC, bevel=0.008),
            lbox(f"pil{i}_plinth_cap", wf, a - 0.21, a + 0.21, 0.18, 0.205, 0.0, 0.135, CONC, bevel=0.006),
            lbox(f"pil{i}_shaft", wf, a - 0.20, a + 0.20, 0.205, 3.28, 0.0, 0.12, CONC, bevel=0.012),
            lbox(f"pil{i}_neck", wf, a - 0.212, a + 0.212, 3.28, 3.31, 0.0, 0.132, CONC, bevel=0.006),
            lbox(f"pil{i}_cap", wf, a - 0.24, a + 0.24, 3.31, H, 0.0, 0.165, CONC, bevel=0.010))


# ====================================================================== trims
def hall_trims():
    base_breaks = [
        ((-0.77, Z0), (-0.33, Z0)), ((2.13, Z1), (2.57, Z1)), ((X1, 1.98), (X1, 2.42)), ((X0, -2.92), (X0, -2.48)),
        ((2.78, Z1), (4.22, Z1)),            # shutter rails
        ((-0.62, Z1), (1.82, Z1)),           # lockers
        ((X1, -1.87), (X1, -0.93)),          # tube station
        ((X1, 0.20), (X1, 1.40)),            # compressor
        ((-2.08, BZ0), (-1.03, BZ0)),        # booth door casing
    ]
    for i, path in enumerate(C.perim_paths(HALL, True, base_breaks, 0.0)):
        add("trim", A.sweep(f"baseboard_{i}", A.profile_baseboard(h=BASE_H, t=0.022), path, mat=WAL))
    dado_breaks = [
        ((-0.755, Z0), (-0.345, Z0)), ((2.145, Z1), (2.555, Z1)), ((X1, 1.995), (X1, 2.405)), ((X0, -2.905), (X0, -2.495)),
        ((-4.20, Z0), (-0.80, Z0)),          # projection screen (frame, pilasters, drapes)
        ((0.28, Z0), (2.72, Z0)),            # vault frame
        ((X1, -1.87), (X1, -0.93)),          # tube station
        ((X1, -0.66), (X1, -0.04)),          # routing chart
        ((X1, 0.20), (X1, 1.40)),            # compressor
        ((-0.62, Z1), (1.82, Z1)),           # lockers
        ((2.78, Z1), (4.22, Z1)),            # shutter
        ((X0, -1.56), (X0, -0.84)),          # card catalogue
        ((X0, BZ0), (BX1, Z1)),              # booth faces (own panelling cap at 1.2)
    ]
    for i, path in enumerate(C.perim_paths(HALL, True, dado_breaks, DADO - 0.03)):
        add("trim", A.sweep(f"dado_{i}", C.profile_rail(0.07), path, mat=WAL))
    crown_breaks = [
        ((-0.79, Z0), (-0.31, Z0)), ((2.11, Z1), (2.59, Z1)), ((X1, 1.96), (X1, 2.44)), ((X0, -2.94), (X0, -2.46)),
        ((-1.625, Z0), (-1.375, Z0)), ((1.375, Z0), (1.625, Z0)), ((-1.625, Z1), (-1.375, Z1)), ((1.375, Z1), (1.625, Z1)),
        ((X1, -0.325), (X1, -0.075)), ((X0, -0.325), (X0, -0.075)),
        ((2.75, Z1), (4.25, Z1)),            # shutter head bulkhead
    ]
    for i, path in enumerate(C.perim_paths(RECT, True, crown_breaks, H)):
        add("ceiling", A.sweep(f"crown_{i}", A.profile_crown(h=CROWN_H, p=0.14), path, mat="M_Ceiling"))


# ====================================================================== booth
MOULD = [(0.0, 0.0), (0.0, 0.006), (0.005, 0.011), (0.012, 0.0125), (0.021, 0.005), (0.024, 0.0)]
MOULD_W = 0.024


def profile_cap():
    pts = [(0.0, 0.0), (0.014, 0.0), (0.014, 0.006)]
    pts += A.arc(0.024, 0.006, 0.010, 180, 90, 3)[1:]
    pts += [(0.032, 0.016), (0.035, 0.020), (0.035, 0.033), (0.031, 0.038), (0.0, 0.038)]
    return pts


def profile_fascia():
    """Booth cornice: s out of the wall, u <= 0 measured down from the slab top."""
    pts = [(0.0, 0.0), (0.0, -0.17), (0.010, -0.17), (0.014, -0.162)]
    pts += A.arc(0.014 + 0.03, -0.162, 0.03, 180, 90, 3)[1:]
    pts += [(0.046, -0.128), (0.046, -0.040), (0.052, -0.034), (0.058, -0.022), (0.058, -0.006), (0.054, 0.0)]
    return pts


def booth():
    # walls with the window and doorway
    bn = gbox("booth_n", (BX0, 0, BZ0), (BX1, BOOTH_H, BZ0 + BT), GREEN)
    be = gbox("booth_e", (BX1 - BT, 0, BZ0 + BT), (BX1, BOOTH_H, BZ1), GREEN)
    M.boolean(bn, gbox("cut_win", (WIN[0], WIN[2], BZ0 - 0.1), (WIN[1], WIN[3], BZ0 + BT + 0.1), GREEN))
    M.boolean(bn, gbox("cut_door", (DOOR[0], -0.1, BZ0 - 0.1), (DOOR[1], DOOR[2], BZ0 + BT + 0.1), GREEN))

    def inner(c, n, cur):
        gz, gx = -c.y, c.x
        if n.y < -0.9 and gz > BZ0 + BT - 1e-3:      # north wall, booth side (normal +Godot z)
            return PLASTER
        if n.x < -0.9 and gx < BX1 - BT + 1e-3:      # east wall, booth side (normal -x)
            return PLASTER
        return None
    A.mat_by_face(bn, inner)
    A.mat_by_face(be, inner)
    add("booth_walls", bn, be)
    # slab + parapet
    add("booth_ceiling", gbox("booth_slab", (BX0, BOOTH_H, BZ0), (BX1, BOOTH_TOP, BZ1), "M_Ceiling"))
    add("booth_ceiling",
        lbox("parapet_n", WBN, -BX1, -BX0, BOOTH_TOP, 3.08, -0.08, 0.0, GREEN, bevel=0.004),
        lbox("parapet_e", WBE, -BZ1, -(BZ0 + 0.08), BOOTH_TOP, 3.08, -0.08, 0.0, GREEN, bevel=0.004),
        lbox("parapet_cap_n", WBN, -BX1 - 0.012, -BX0, 3.08, 3.105, -0.09, 0.012, WAL, bevel=0.005),
        lbox("parapet_cap_e", WBE, -BZ1, -(BZ0 + 0.09), 3.08, 3.105, -0.09, 0.012, WAL, bevel=0.005))
    # cornice at the top of the hall faces
    ext = [(BX0, BZ0), (BX1, BZ0), (BX1, BZ1)]
    for i, path in enumerate(C.perim_paths(ext, False, [], BOOTH_TOP)):
        add("booth_walls", A.sweep(f"booth_cornice_{i}", profile_fascia(), path, mat=WAL))
    # panelling (walnut raised fields on a backing board), cap rail at 1.2
    BACK_T = 0.012
    for wf, a0, a1, n in ((WBN, 2.08, 5.0, 4), (WBE, -3.5, -2.0, 2)):
        add("booth_walls", lbox(f"booth_back_{n}", wf, a0, a1, BASE_H, PANEL_TOP - 0.035, 0.0, BACK_T, "M_Wood_Panel", 0.002))
        fm = wf.m(BACK_T)
        e, s = 0.07, 0.09
        pw = (a1 - a0 - 2 * e - (n - 1) * s) / n
        b0, b1 = 0.27, 1.06
        for i in range(n):
            pa = a0 + e + i * (pw + s)
            pb = pa + pw
            path = A.rect_path(fm, pa, pb, b0, b1)
            add("booth_walls", A.sweep(f"booth_mould_{n}_{i}", MOULD, path, up=GV(wf.n), closed=True, mat=WAL))
            add("booth_walls", A.raised_field(f"booth_field_{n}_{i}", pa + MOULD_W, pb - MOULD_W, b0 + MOULD_W, b1 - MOULD_W,
                                              0.034, 0.010, fm))
    for i, path in enumerate(C.perim_paths(ext, False, [((-2.08, BZ0), (-1.03, BZ0))], PANEL_TOP - 0.038)):
        add("booth_walls", A.sweep(f"booth_cap_{i}", profile_cap(), path, mat=WAL))
    # interior skirting (plain)
    inner_poly = [(BX1 - BT, BZ0 + BT), (BX0, BZ0 + BT), (BX0, BZ1), (BX1 - BT, BZ1)]
    plain = [(0.0, 0.0), (0.018, 0.0), (0.018, 0.100), (0.012, 0.112), (0.0, 0.116)]
    sk_breaks = [((-1.97, BZ0 + BT), (-1.13, BZ0 + BT)), ((BX0, 2.48), (BX0, 3.12)), ((-4.52, BZ1), (-3.28, BZ1))]
    for i, path in enumerate(C.perim_paths(inner_poly, True, sk_breaks, 0.0)):
        add("booth_walls", A.sweep(f"booth_skirt_{i}", plain, path, mat="M_Wood_Panel"))
    booth_window()
    booth_sign()
    return booth_interior()


def booth_window():
    x0, x1, y0, y1 = WIN
    zf, zb = BZ0, BZ0 + BT
    t = 0.006
    parts = [
        gbox("win_rev_t", (x0, y1 - t, zf), (x1, y1, zb), BRASS),
        gbox("win_rev_b", (x0, y0, zf), (x1, y0 + t, zb), BRASS),
        gbox("win_rev_l", (x0, y0, zf), (x0 + t, y1, zb), BRASS),
        gbox("win_rev_r", (x1 - t, y0, zf), (x1, y1, zb), BRASS),
    ]
    fw = 0.036
    for side, z in (("h", zf), ("b", zb)):
        dz = -0.007 if side == "h" else 0.007
        za, zb2 = (z + dz, z) if dz < 0 else (z, z + dz)
        parts += [gbox(f"win_fl_{side}_t", (x0 - fw, y1, za), (x1 + fw, y1 + fw, zb2), BRASS, bevel=0.0018),
                  gbox(f"win_fl_{side}_b", (x0 - fw, y0 - fw, za), (x1 + fw, y0, zb2), BRASS, bevel=0.0018),
                  gbox(f"win_fl_{side}_l", (x0 - fw, y0, za), (x0, y1, zb2), BRASS, bevel=0.0018),
                  gbox(f"win_fl_{side}_r", (x1, y0, za), (x1 + fw, y1, zb2), BRASS, bevel=0.0018)]
    # glazing beads either side of the pane
    zc = (zf + zb) / 2
    bd = 0.012
    for s, zz in (("h", zc - 0.003 - bd), ("b", zc + 0.003)):
        parts += [gbox(f"bead_{s}_t", (x0 + t, y1 - t - bd, zz), (x1 - t, y1 - t, zz + bd), BRASS, bevel=0.002),
                  gbox(f"bead_{s}_b", (x0 + t, y0 + t, zz), (x1 - t, y0 + t + bd, zz + bd), BRASS, bevel=0.002),
                  gbox(f"bead_{s}_l", (x0 + t, y0 + t + bd, zz), (x0 + t + bd, y1 - t - bd, zz + bd), BRASS, bevel=0.002),
                  gbox(f"bead_{s}_r", (x1 - t - bd, y0 + t + bd, zz), (x1 - t, y1 - t - bd, zz + bd), BRASS, bevel=0.002)]
    # four domed screws per face flange corner
    for side, z, nrm in (("h", zf - 0.007, (0, 0, -1)), ("b", zb + 0.007, (0, 0, 1))):
        for (xx, yy) in ((x0 - fw / 2, y0 - fw / 2), (x1 + fw / 2, y0 - fw / 2), (x1 + fw / 2, y1 + fw / 2), (x0 - fw / 2, y1 + fw / 2)):
            parts.append(C.screw(f"win_screw_{side}", 0.0055, (xx, yy, z), nrm, BRASS, 35))
    add("booth_walls", *parts)
    glass = gbox("booth_glass", (x0 + t, y0 + t, zc - 0.003), (x1 - t, y1 - t, zc + 0.003), "M_Glass")
    return add("booth_glass", glass)


def booth_sign():
    """Cream enamel plate with a film-reel pictogram over the doorway (hall side, faces -z)."""
    cx, cy, z = (DOOR[0] + DOOR[1]) / 2, 2.43, BZ0
    fm = C.gframe((cx, cy, z), (-1, 0, 0), (0, 1, 0))          # local x = -Godot x (reads left->right from the hall)
    w, h = 0.34, 0.19
    parts = [C.gpoly("sign_plate", A.rounded_rect(w, h, 0.022, 3), 0.007, fm, "M_Enamel_Cream", 0.0015)]
    # border line
    outer = A.rounded_rect(w - 0.024, h - 0.024, 0.014, 3)
    inner = A.rounded_rect(w - 0.036, h - 0.036, 0.008, 3)
    ring = _ring_mesh("sign_border", outer, inner, 0.0072, fm, "M_Lacquer_Black")
    parts.append(ring)
    # reel: black disc with cream holes, at the left; film tail to the right
    rx = -0.065
    disc = M.cylinder("sign_reel", 0.058, 0.002, loc=(rx, 0.0, 0.0078), verts=28, mat="M_Lacquer_Black", bevel=0.0)
    disc.data.transform(Matrix.Translation(disc.location))
    disc.location = (0, 0, 0)
    disc.data.transform(fm)
    parts.append(disc)
    for k in range(5):
        a = math.radians(90 + 72 * k)
        hole = M.cylinder(f"sign_hole{k}", 0.0155, 0.002, loc=(rx + 0.032 * math.cos(a), 0.032 * math.sin(a), 0.0090),
                          verts=12, mat="M_Enamel_Cream", bevel=0.0)
        hole.data.transform(Matrix.Translation(hole.location))
        hole.location = (0, 0, 0)
        hole.data.transform(fm)
        parts.append(hole)
    hub = M.cylinder("sign_hub", 0.007, 0.002, loc=(rx, 0, 0.0090), verts=10, mat="M_Enamel_Cream", bevel=0.0)
    hub.data.transform(Matrix.Translation(hub.location))
    hub.location = (0, 0, 0)
    hub.data.transform(fm)
    parts.append(hub)
    # film strip leaving the reel bottom toward the right, with sprocket holes
    strip = [(rx, -0.058), (0.13, -0.058), (0.13, -0.030), (rx + 0.03, -0.030)]
    parts.append(C.gpoly("sign_film", strip, 0.0012, fm @ Matrix.Translation((0, 0, 0.0068)), "M_Lacquer_Black", 0.0))
    for k in range(7):
        xx = -0.01 + k * 0.021
        for yy in (-0.053, -0.035):
            sq = [(xx - 0.0035, yy - 0.0022), (xx + 0.0035, yy - 0.0022), (xx + 0.0035, yy + 0.0022), (xx - 0.0035, yy + 0.0022)]
            parts.append(C.gpoly(f"sign_sprocket{k}", sq, 0.0006, fm @ Matrix.Translation((0, 0, 0.0080)), "M_Enamel_Cream", 0.0))
    # two brass screws
    for xx in (-w / 2 + 0.013, w / 2 - 0.013):
        p = fm @ Vector((xx, 0.0, 0.007))
        parts.append(A.screw("sign_screw", 0.0045, p, GV((0, 0, -1)), BRASS, 20))
    add("booth_walls", *parts)


def _ring_mesh(name, outer, inner, depth, fm, mat):
    """Flat ring between two CCW outlines of equal point count, at local z = depth."""
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, depth)) for x, y in outer]
    vi = [bm.verts.new((x, y, depth)) for x, y in inner]
    n = len(vo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    o = A.obj_from_bm(name, bm, mat)
    o.data.transform(fm)
    return o


def booth_interior():
    # shelf on the south wall, top 1.45, z 3.24 -> 3.5
    add("booth_walls", lbox("shelf", WS, 3.3, 4.6, 1.42, 1.45, 0.0, 0.26, WAL, bevel=0.003))
    for a in (3.44, 4.46):
        add("booth_walls", lbox(f"shelf_br_v{a}", WS, a - 0.012, a + 0.012, 1.22, 1.42, 0.0, 0.006, STEEL, 0.001),
            lbox(f"shelf_br_h{a}", WS, a - 0.012, a + 0.012, 1.414, 1.42, 0.0, 0.22, STEEL, 0.001))
        gus = M.extrude_profile(f"shelf_gusset{a}", [(0.0, 1.24), (0.17, 1.414), (0.0, 1.414)], 0.004, mat=STEEL, bevel=0.0)
        # extrude_profile builds in local (x, y) + z depth: map local x -> c, y -> b, z -> -a (right-handed)
        m = A.frame_matrix(GV(WS.p(a + 0.002, 0, 0)), GV(WS.n), GV(WS.up), -GV(WS.u))
        gus.data.transform(m)
        add("booth_walls", gus)
    film_cans()
    fire_bucket()
    # conduit: bulb rose -> east wall -> switch box by the door
    bx, bz = -3.0, 2.85
    add("booth_walls", C.gtube("booth_conduit", [(bx + 0.05, BOOTH_H - 0.012, bz), (BX1 - BT - 0.014, BOOTH_H - 0.012, bz),
                                                 (BX1 - BT - 0.014, 1.43, bz)], 0.010, sides=8, mat=STEEL, fillet=0.06))
    add("booth_walls", gbox("booth_switch", (BX1 - BT - 0.04, 1.27, bz - 0.05), (BX1 - BT, 1.43, bz + 0.05), "M_Bakelite", 0.006),
        C.gcyl("booth_switch_toggle", 0.006, 0.022, (BX1 - BT - 0.04, 1.36, bz), axis="-x", verts=8, mat=BRASS))
    for y in (2.1, 1.75):
        add("booth_walls", gbox(f"booth_saddle{y}", (BX1 - BT - 0.026, y - 0.012, bz - 0.014), (BX1 - BT, y + 0.012, bz + 0.014), STEEL, 0.002))
    # bulb fixture
    rose = C.glathe("booth_rose", [(0.0, -0.022), (0.030, -0.022), (0.040, -0.016), (0.044, -0.006), (0.044, 0.0)],
                    (bx, BOOTH_H, bz), axis="y", segments=12, mat="M_Bakelite")
    cord = C.gtube("booth_cord", [(bx, BOOTH_H - 0.02, bz), (bx, 2.738, bz)], 0.0035, sides=6, mat="M_Fabric")
    sock = C.glathe("booth_socket", [(0.0, 2.698), (0.0165, 2.698), (0.0195, 2.704), (0.0195, 2.728), (0.013, 2.736),
                                     (0.006, 2.742), (0.0, 2.744)], (bx, 0, bz), segments=12, mat="M_Bakelite")
    base = [(0.0, 2.684)]
    for k in range(3):
        yy = 2.686 + k * 0.004
        base += [(0.0122, yy), (0.0134, yy + 0.002)]
    base += [(0.013, 2.698), (0.0, 2.698)]
    base_o = C.glathe("booth_bulb_base", base, (bx, 0, bz), segments=10, mat=BRASS)
    add("booth_fixture", rose, cord, sock, base_o)
    bulb = C.glathe("booth_bulb", [(0.0, 2.616), (0.012, 2.619), (0.022, 2.627), (0.029, 2.638), (0.031, 2.650),
                                   (0.029, 2.662), (0.023, 2.672), (0.016, 2.680), (0.0125, 2.686), (0.0, 2.687)],
                    (bx, 0, bz), segments=14, mat="M_Emissive_Warm")
    return bulb


def film_cans():
    """35 mm feature cans (dia 0.36) on the booth shelf: a flat stack at the left, a few 16 mm cans, and four
    standing on edge at the right. Keeps x [-3.95, -3.55] free for the lens case."""
    prof_big = [(0.0, 0.0), (0.176, 0.0), (0.180, 0.004), (0.180, 0.031), (0.183, 0.033), (0.183, 0.042),
                (0.0, 0.045)]
    prof_small = [(0.0, 0.0), (0.098, 0.0), (0.101, 0.003), (0.101, 0.022), (0.103, 0.024), (0.103, 0.031),
                  (0.099, 0.033), (0.0, 0.033)]
    cans = []
    top = 1.45
    # flat stack of three, pushed to the wall (they overhang the 0.26 shelf by 0.10 like real stacks)
    for k, (dx, dz, rot) in enumerate(((0.0, 0.0, 0), (0.008, -0.006, 20), (-0.006, 0.004, 47))):
        o = M.lathe(f"can_big_flat{k}", prof_big, segments=16, mat=STEEL)
        o.data.transform(Matrix.Rotation(math.radians(rot), 4, "Z"))
        o.data.transform(Matrix.Translation(G(-4.40 + dx, top + 0.0455 * k, 3.315 + dz)))
        cans.append(A.hint(o, 50))
    for k, (x, rot) in enumerate(((-4.092, 10),)):
        o = M.lathe(f"can_small{k}", prof_small, segments=14, mat=STEEL)
        o.data.transform(Matrix.Rotation(math.radians(rot), 4, "Z"))
        o.data.transform(Matrix.Translation(G(x, top + 0.0335 * k, 3.37)))
        cans.append(A.hint(o, 50))
    # four standing on edge (axis along x), slightly leaning on each other
    for k in range(3):
        x = -3.335 - k * 0.048
        lean = math.radians(-4.0 + k * 2.0)
        o = M.lathe(f"can_big_edge{k}", prof_big, segments=16, mat=STEEL)
        o.data.transform(Matrix.Translation((0, 0, -0.0225)))
        o.data.transform(Matrix.Rotation(math.radians(90), 4, "Y"))     # axis -> Blender X (Godot x)
        o.data.transform(Matrix.Rotation(lean, 4, "Y"))
        o.data.transform(Matrix.Translation(G(x, top + 0.183, 3.315)))
        cans.append(A.hint(o, 50))
    add("film_cans", *cans)


def fire_bucket():
    """Conical red fire bucket hanging on a hook, booth north wall (inside), west end."""
    cx, cz = -4.60, BZ0 + BT + 0.155
    y0 = 0.80
    outer = [(0.012, 0.0), (0.03, 0.012), (0.125, 0.275), (0.136, 0.288), (0.140, 0.296)]
    t = 0.004
    loop = [(0.0, 0.0)] + outer + [(0.136, 0.300), (0.130, 0.296)] + [(r - t, z + t * 0.4) for (r, z) in reversed(outer[2:])] + \
        [(0.03 - t, 0.012 + t)]
    b = C.glathe_loop("fire_bucket", loop, (cx, y0, cz), axis="y", segments=18, mat="M_Enamel_Crimson")
    hook = C.gtube("bucket_hook", [(cx, 1.20, BZ0 + BT), (cx, 1.20, BZ0 + BT + 0.05), (cx, 1.235, BZ0 + BT + 0.06)],
                   0.004, sides=6, mat=STEEL, fillet=0.015)
    # bail from both rim sides up to the hook
    pts = []
    for k in range(9):
        a = math.radians(180 * k / 8)
        pts.append((cx + 0.14 * math.cos(a), y0 + 0.30 + 0.105 * math.sin(a), cz - 0.005))
    bail = C.gtube("bucket_bail", pts, 0.0028, sides=5, mat=STEEL)
    add("booth_walls", b, hook, bail)


# ====================================================================== fire shutter + corridor
def shutter():
    xa, xb = 2.86, 4.14
    zc = 3.45
    p = 0.076
    y_lo, y_hi = 0.065, 2.42
    n = int(round((y_hi - y_lo) / p))
    p = (y_hi - y_lo) / n
    prof = []
    for k in range(n):
        y = y_lo + k * p
        for t, d in ((0.0, -0.004), (0.12, 0.006), (0.5, 0.012), (0.88, 0.006)):
            prof.append((y + t * p, d))
    prof.append((y_hi, -0.004))
    bm = bmesh.new()
    front, back = [], []
    for (y, d) in prof:
        front.append((bm.verts.new(G(xa, y, zc - d - 0.006)), bm.verts.new(G(xb, y, zc - d - 0.006))))
        back.append((bm.verts.new(G(xa, y, zc - d + 0.006)), bm.verts.new(G(xb, y, zc - d + 0.006))))
    for i in range(len(prof) - 1):      # front faces the room (-Godot z = Blender +y), back the corridor
        bm.faces.new((front[i][1], front[i][0], front[i + 1][0], front[i + 1][1]))
        bm.faces.new((back[i][0], back[i][1], back[i + 1][1], back[i + 1][0]))
    curtain = A.obj_from_bm("shutter_curtain", bm, PAINTED)
    # bottom bar: black body + amber hazard stripes on the room face, rubber seal
    bar = gbox("shutter_bar", (xa + 0.01, 0.008, zc - 0.03), (xb - 0.01, y_lo + 0.004, zc + 0.03), "M_Lacquer_Black", bevel=0.004)
    seal = gbox("shutter_seal", (xa + 0.012, 0.0, zc - 0.016), (xb - 0.012, 0.010, zc + 0.016), "M_Rubber", bevel=0.003)
    stripes = []
    sw, y0s, y1s = 0.075, 0.014, 0.063
    hgt = y1s - y0s
    x = xa - 0.2
    k = 0
    bm2 = bmesh.new()
    zf = zc - 0.0315
    while x < xb + 0.1:
        poly = [(x, y0s), (x + sw, y0s), (x + sw + hgt, y1s), (x + hgt, y1s)]
        cp = C.clip_poly_x(poly, xa + 0.016, xb - 0.016)
        if len(cp) >= 3:
            vs = [bm2.verts.new(G(px, py, zf)) for (px, py) in cp]
            f = bm2.faces.new(vs)
            f.normal_update()
            if f.normal.y < 0:      # face the room (Blender +y)
                f.normal_flip()
        x += 2 * sw
        k += 1
    stripes = A.obj_from_bm("shutter_stripes", bm2, "M_Enamel_Amber")
    # two lift handles on the bar
    handles = [C.gtube(f"shutter_handle{i}", [(hx - 0.05, 0.035, zc - 0.03), (hx - 0.05, 0.035, zc - 0.055),
                                               (hx + 0.05, 0.035, zc - 0.055), (hx + 0.05, 0.035, zc - 0.03)],
                       0.0055, sides=6, mat=STEEL, fillet=0.012) for i, hx in enumerate((3.15, 3.85))]
    sh = C.part("fire_shutter", [curtain, bar, seal, stripes] + handles, pivot=(3.5, 0.0, 3.45))

    # static frame: guide channels, coil box, head bulkhead, threshold
    fr = []
    for side, (x0, x1, web) in enumerate(((2.80, 2.92, 2.80), (4.08, 4.20, 4.194))):
        fr += [gbox(f"rail_back{side}", (x0, 0.0, 3.492), (x1, 2.30, 3.5), STEEL, 0.0015),
               gbox(f"rail_web{side}", (web, 0.0, 3.40), (web + 0.006, 2.30, 3.5), STEEL, 0.0015),
               gbox(f"rail_lip{side}", (x0 if side == 0 else 4.125, 0.0, 3.40), (2.875 if side == 0 else x1, 2.30, 3.407), STEEL, 0.0015)]
        for y in (0.35, 1.15, 1.95):
            xx = (x0 + x1) / 2 + (-0.03 if side == 0 else 0.03)
            fr.append(C.screw(f"rail_bolt{side}", 0.006, (xx, y, 3.40), (0, 0, -1), STEEL, 0))
    fr.append(gbox("coil_box", (2.75, 2.30, 3.16), (4.25, 2.76, 3.5), PAINTED, bevel=0.012, seg=2))
    for x, d in ((2.75, -1), (4.25, 1)):
        fr.append(C.gcyl(f"coil_boss{x}", 0.085, 0.02, (x, 2.53, 3.33), axis="x" if d > 0 else "-x", verts=16, mat=PAINTED, bevel=0.003))
        fr.append(C.gcyl(f"coil_hub{x}", 0.03, 0.035, (x, 2.53, 3.33), axis="x" if d > 0 else "-x", verts=10, mat=STEEL, bevel=0.0))
    for x in (2.82, 3.3, 3.7, 4.18):
        for y in (2.34, 2.72):
            fr.append(C.screw("coil_rivet", 0.006, (x, y, 3.16), (0, 0, -1), PAINTED, None))
    fr.append(gbox("shutter_head", (2.75, 2.76, 3.34), (4.25, H, 3.5), PLASTER, bevel=0.006))
    fr.append(gbox("threshold", (2.88, -0.004, 3.36), (4.12, 0.003, 3.66), BRASS, bevel=0.002))
    # relay lamp housing (the red dome is `shutter_lamp`) and a warning triangle plate
    lx, ly = 3.98, 2.53
    fr.append(C.glathe("relay_base", [(0.0, 0.0), (0.036, 0.0), (0.038, 0.006), (0.030, 0.014), (0.026, 0.018), (0.0, 0.018)],
                       (lx, ly, 3.16), axis="-z", segments=16, mat=STEEL))
    cage = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        pts = []
        for j in range(6):
            t = j / 5
            r = 0.026 * math.cos(t * math.pi / 2) + 0.004
            dz = 0.018 + 0.03 * math.sin(t * math.pi / 2)
            pts.append((lx + r * math.cos(a), ly + r * math.sin(a), 3.16 - dz))
        cage.append(C.gtube(f"relay_wire{k}", pts, 0.0018, sides=4, mat=STEEL))
    fr += cage
    tri = [(0.0, 0.05), (-0.0433, -0.025), (0.0433, -0.025)]
    tm = C.gframe((3.02, 2.535, 3.16), (-1, 0, 0), (0, 1, 0))
    fr.append(C.gpoly("warn_plate", tri, 0.003, tm, "M_Enamel_Amber", 0.0008))
    inner_tri = [(0.0, 0.032), (-0.0277, -0.016), (0.0277, -0.016)]
    outer_tri = [(0.0, 0.041), (-0.0355, -0.0205), (0.0355, -0.0205)]
    fr.append(_ring_mesh("warn_border", outer_tri, inner_tri, 0.0034, tm, "M_Lacquer_Black"))
    bolt = [(-0.004, -0.010), (0.006, 0.004), (0.0, 0.004), (0.004, 0.018), (-0.006, 0.002), (0.0, 0.002)]
    fr.append(C.gpoly("warn_bolt", bolt, 0.0006, tm @ Matrix.Translation((0, 0, 0.0034)), "M_Lacquer_Black", 0.0))
    add("shutter_frame", *fr)
    lamp = C.glathe("shutter_lamp", [(0.0, 0.048), (0.008, 0.047), (0.016, 0.043), (0.021, 0.036), (0.023, 0.026),
                                     (0.023, 0.016), (0.0, 0.016)], (lx, ly, 3.16), axis="-z", segments=16, mat="M_Emissive_Red")
    M.set_origin(lamp, G(lx, ly, 3.16 - 0.032))
    return sh, lamp


def corridor():
    cx0, cx1, cz0, cz1, ch = 2.9, 4.1, 3.7, 7.0, 2.6
    parts = [gbox("cor_floor", (cx0 - T, -0.12, cz0), (cx1 + T, 0.0, cz1 + T), "M_Linoleum"),
             gbox("cor_ceiling", (cx0 - T, ch, cz0), (cx1 + T, ch + 0.12, cz1 + T), "M_Ceiling")]
    for side, (xa, xb) in enumerate(((cx0 - T, cx0), (cx1, cx1 + T))):
        parts += [gbox(f"cor_wall_lo{side}", (xa, 0, cz0), (xb, DADO, cz1), GREEN),
                  gbox(f"cor_wall_hi{side}", (xa, DADO, cz0), (xb, ch, cz1), PLASTER)]
        xi = xb if side == 0 else xa
        d = 0.02 if side == 0 else -0.02
        parts.append(gbox(f"cor_skirt{side}", (min(xi, xi + d), 0.0, cz0), (max(xi, xi + d), 0.12, cz1), WAL, 0.003))
        parts.append(gbox(f"cor_rail{side}", (min(xi, xi + d * 1.2), DADO - 0.02, cz0), (max(xi, xi + d * 1.2), DADO + 0.03, cz1), WAL, 0.004))
    far = gbox("cor_far", (cx0, 0, cz1), (cx1, ch, cz1 + T), PLASTER)
    M.boolean(far, gbox("cut_far_door", (3.1, -0.1, cz1 - 0.1), (3.9, 2.05, cz1 + T + 0.1), PLASTER))
    parts.append(far)
    parts.append(gbox("cor_door_leaf", (3.1, 0.0, cz1 + 0.06), (3.9, 2.05, cz1 + 0.10), "M_Wood_Panel", 0.004))
    parts.append(gbox("cor_door_win", (3.32, 1.35, cz1 + 0.055), (3.68, 1.80, cz1 + 0.06), "M_Glass_Dark", 0.0))
    cas = A.profile_casing(w=0.08, t=0.022)
    parts.append(A.sweep("cor_casing", cas, [G(3.9, 0, cz1), G(3.9, 2.05, cz1), G(3.1, 2.05, cz1), G(3.1, 0, cz1)],
                         up=GV((0, 0, -1)), mat=WAL))
    parts.append(C.gcyl("cor_knob", 0.022, 0.05, (3.82, 1.0, cz1 + 0.06), axis="-z", verts=12, mat=BRASS))
    # a dead ceiling lamp
    parts.append(C.glathe("cor_lamp", [(0.0, -0.10), (0.09, -0.10), (0.11, -0.06), (0.11, -0.02), (0.06, 0.0), (0.0, 0.0)],
                          (3.5, ch, 5.6), axis="y", segments=16, mat="M_Glass_Frosted"))
    add("corridor", *parts)


# ====================================================================== emergency lamps
def emergency_lamps():
    bodies, glasses, lights = [], [], []
    for k, (wf, a, c0) in enumerate(ELAMPS):
        base = wf.m() @ Matrix.Translation((a, ELAMP_Y, c0))     # local x along wall, y up, z out
        parts = []
        plate = M.extrude_profile(f"el{k}_plate", A.rounded_rect(0.115, 0.155, 0.024, 2), 0.012, mat=PAINTED, bevel=0.0)
        plate.data.transform(base)
        parts.append(plate)
        body = M.lathe(f"el{k}_body", [(0.058, 0.012), (0.058, 0.040), (0.052, 0.050), (0.046, 0.052), (0.0, 0.052)],
                       segments=12, mat=PAINTED)
        body.data.transform(base)
        parts.append(A.hint(body, 50))
        ring = M.torus(f"el{k}_ring", 0.0495, 0.0028, loc=(0, 0, 0.088), major_seg=12, minor_seg=3, mat=STEEL)
        ring.data.transform(Matrix.Translation(ring.location))
        ring.location = (0, 0, 0)
        ring.data.transform(base)
        parts.append(A.hint(ring, 70))
        for j in range(4):
            ang = math.radians(45 + 90 * j)
            pts = []
            for i in range(6):
                t = i / 5
                r = 0.052 * math.cos(t * math.pi / 2) + 0.003 * (1 - t)
                z = 0.050 + 0.080 * math.sin(t * math.pi / 2)
                pts.append(base @ Vector((r * math.cos(ang), r * math.sin(ang), z)))
            parts.append(A.tube(f"el{k}_wire{j}", pts, 0.0022, sides=3, mat=STEEL, caps=False))
        boss = M.cylinder(f"el{k}_boss", 0.009, 0.008, loc=(0, 0, 0.131), verts=6, mat=STEEL, bevel=0.0)
        boss.data.transform(Matrix.Translation(boss.location))
        boss.location = (0, 0, 0)
        boss.data.transform(base)
        parts.append(boss)
        # conduit gland on top and the conduit up to the crown (or the pilaster capital)
        top = 3.30 if c0 > 0 else H - CROWN_H + 0.01
        gl = M.box(f"el{k}_gland", (0.034, 0.03, 0.03), loc=(0, 0.0905, 0.018), mat=PAINTED, bevel=0.0)
        A.place(gl, base)
        parts.append(gl)
        cp = [base @ Vector((0, 0.105, 0.018)), base @ Vector((0, top - ELAMP_Y, 0.018))]
        parts.append(A.tube(f"el{k}_conduit", cp, 0.0105, sides=6, mat=STEEL, caps=False))
        sad = M.box(f"el{k}_saddle", (0.03, 0.016, 0.012), loc=(0, (top - ELAMP_Y) * 0.6 + 0.04, 0.006), mat=STEEL, bevel=0.0)
        A.place(sad, base)
        parts.append(sad)
        b = C.part(f"elamp_{k}", parts)
        bodies.append(b)
        gl_o = M.lathe(f"elamp_glass_{k}", [(0.0, 0.124), (0.022, 0.119), (0.037, 0.106), (0.045, 0.088),
                                            (0.046, 0.066), (0.046, 0.050), (0.0, 0.050)], segments=12, mat="M_Glass_Amber")
        gl_o.data.transform(base)
        A.hint(gl_o, 60)
        bulb_c = base @ Vector((0, 0, 0.082))
        M.set_origin(gl_o, bulb_c)
        glasses.append(gl_o)
        lights.append(M.empty(f"elamp_light_{k}", bulb_c))
    return bodies, glasses, lights


# ====================================================================== pneumatic tube run
def sleeve(name, p, axis_vec):
    """Brass coupling sleeve around the glass at Blender point p, along the Blender axis vector."""
    loop = [(0.0462, -0.025), (0.0530, -0.020), (0.0530, 0.020), (0.0462, 0.025)]
    o = A.lathe_loop(name, loop, segments=12, mat=BRASS)
    q = Vector((0, 0, 1)).rotation_difference(Vector(axis_vec).normalized())
    o.data.transform(Matrix.Translation(p) @ q.to_matrix().to_4x4())
    return A.hint(o, 60)


def clamp_ring(name, p, axis_vec, r=0.049):
    o = M.torus(name, r, 0.0035, major_seg=10, minor_seg=3, mat=STEEL)
    q = Vector((0, 0, 1)).rotation_difference(Vector(axis_vec).normalized())
    o.data.transform(Matrix.Translation(p) @ q.to_matrix().to_4x4())
    return A.hint(o, 70)


def run_sleeves(path_godot, step=1.1, tag="m"):
    """Sleeves at both tangent points of every bend, at the ends, and every <= step on straight runs."""
    pts = [GV(p) for p in path_godot]
    out = []
    n = len(pts)
    for i in range(n - 1):
        a, b = pts[i], pts[i + 1]
        d = (b - a)
        ln = d.length
        d.normalize()
        s0 = 0.0 if i == 0 else BEND
        s1 = ln if i == n - 2 else ln - BEND
        s0 += 0.026 if i == 0 else 0.0
        s1 -= 0.026 if i == n - 2 else 0.0
        cnt = max(1, int(math.ceil((s1 - s0) / step)))
        for j in range(cnt + 1):
            s = s0 + (s1 - s0) * j / cnt
            out.append(sleeve(f"sleeve_{tag}{i}_{j}", a + d * s, d))
    return out


def tube_run():
    glass = []
    for nm, path in (("tg_main", TUBE_P), ("tg_ret", TUBE_Q)):
        fp = A.fillet_path([GV(p) for p in path], BEND, 6)
        glass.append(C.hollow_tube(nm, fp, R_OUT, R_IN, sides=12))
    glass.append(C.hollow_tube("tg_dir", [GV(p) for p in TUBE_D], R_OUT, R_IN, sides=12))
    brass = run_sleeves(TUBE_P, tag="m") + run_sleeves(TUBE_Q, tag="r")
    d0, d1 = GV(TUBE_D[0]), GV(TUBE_D[1])
    dd = (d1 - d0).normalized()
    for j, s in enumerate((0.03, 0.9, 1.6)):
        brass.append(sleeve(f"sleeve_d{j}", d0 + dd * s, dd))
    iron = []
    # trapeze hangers for the twin runs (x-run at z -1.40 / -1.26, z-run at x 0 / 0.14)
    ytop_strut = 3.25 - R_OUT - 0.004
    for x in (3.3, 1.5, 0.62):
        top = H - 0.16 if abs(x - 1.5) < 0.2 else H
        iron += _trapeze(f"hx{x}", (x, ytop_strut, -1.33), "z", top, (-1.40, -1.26))
    for z in (-0.2,):
        top = H - 0.16 if abs(z + 0.2) < 0.2 else H
        iron += _trapeze(f"hz{z}", (0.07, ytop_strut, z), "x", top, (0.0, 0.14))
    # single hangers on the Director's line
    for z in (-2.3, -3.05):
        iron.append(C.gtube(f"hd_rod{z}", [(4.0, H, z), (4.0, 3.25 + R_OUT + 0.003, z)], 0.005, sides=6, mat=STEEL))
        iron.append(clamp_ring(f"hd_ring{z}", GV((4.0, 3.25, z)), GV((0, 0, 1))))
        iron.append(C.gcyl(f"hd_plate{z}", 0.022, 0.006, (4.0, H - 0.006, z), axis="y", verts=8, mat=STEEL, bevel=0.0))
    # wall bracket for the two risers on the east wall
    for y in (2.62, 3.02):
        iron += [gbox(f"wb_plate{y}", (X1 - 0.008, y - 0.05, -1.37), (X1, y + 0.05, -1.29), STEEL, 0.002),
                 gbox(f"wb_arm{y}", (4.80 + 0.02, y - 0.008, -1.345), (X1 - 0.008, y + 0.008, -1.315), STEEL, 0.002),
                 gbox(f"wb_bar{y}", (4.80 + 0.045, y - 0.012, -1.45), (4.80 + 0.06, y + 0.012, -1.21), STEEL, 0.002)]
        for z in (-1.40, -1.26):
            iron.append(clamp_ring(f"wb_ring{y}{z}", GV((4.80, y, z)), GV((0, 1, 0))))
    # diverter box on the main run where the Director's line branches off
    dx, dy, dz = DIVERTER
    brass.append(gbox("diverter", (dx - 0.11, dy - 0.07, dz - 0.065), (dx + 0.11, dy + 0.07, dz + 0.065), BRASS, bevel=0.012, seg=2))
    brass.append(gbox("diverter_lid", (dx - 0.085, dy - 0.077, dz - 0.05), (dx + 0.085, dy - 0.07, dz + 0.05), BRASS, bevel=0.004))
    for sx in (-1, 1):
        for sz in (-1, 1):
            brass.append(C.screw("div_screw", 0.005, (dx + sx * 0.07, dy - 0.077, dz + sz * 0.036), (0, -1, 0), BRASS, 30))
    brass.append(C.gcyl("div_rod", 0.006, H - dy - 0.07, (dx, dy + 0.07, dz), axis="y", verts=8, mat=STEEL))
    brass.append(C.gcyl("div_plate", 0.03, 0.006, (dx, H - 0.006, dz), axis="y", verts=12, mat=STEEL))
    # north-wall junction box where the Director's line leaves (with the destination star plate)
    jx, jy = 4.0, 3.25
    brass.append(gbox("junction_box", (jx - 0.12, jy - 0.12, Z0), (jx + 0.12, jy + 0.12, Z0 + 0.11), BRASS, bevel=0.012, seg=2))
    brass.append(gbox("junction_lid", (jx - 0.10, jy - 0.10, Z0 + 0.11), (jx + 0.10, jy + 0.10, Z0 + 0.116), BRASS, bevel=0.003))
    brass.append(C.glathe("junction_gland", [(0.0, 0.0), (0.056, 0.0), (0.056, 0.012), (0.050, 0.02), (0.0, 0.02)],
                          (jx, jy, Z0 + 0.116), axis="z", segments=12, mat=BRASS))
    for sx in (-1, 1):
        for sy in (-1, 1):
            brass.append(C.screw("jb_screw", 0.006, (jx + sx * 0.082, jy + sy * 0.082, Z0 + 0.116), (0, 0, 1), BRASS, 45))
    # small cream enamel plate under the box with the Director's star (destination 0 on the dial)
    pm = C.gframe((jx, jy - 0.175, Z0), (1, 0, 0), (0, 1, 0))
    brass.append(C.gpoly("dir_plate", A.rounded_rect(0.09, 0.06, 0.008, 2), 0.004, pm, "M_Enamel_Cream", 0.001))
    star = []
    for i in range(8):
        r = 0.022 if i % 2 == 0 else 0.0075
        a = math.radians(90 + 45 * i)
        star.append((r * math.cos(a), r * math.sin(a)))
    brass.append(C.gpoly("dir_star", star, 0.0012, pm @ Matrix.Translation((0, 0, 0.004)), "M_Lacquer_Black", 0.0))
    add("tube_glass", *glass)
    add("tube_run", *brass, *iron)
    empties = [M.empty(f"tube_p{i}", GV(p)) for i, p in enumerate(TUBE_P)]
    empties.append(M.empty("tube_q0", GV(TUBE_Q[0])))
    return empties


def _trapeze(tag, centre, across, top, offsets):
    """Two drop rods + a strut channel under a pair of tubes; clamp rings on each tube.
    centre: Godot strut-top centre; across: Godot axis the strut spans ('x' or 'z'); offsets: the tube
    coordinates along `across`."""
    cx, cy, cz = centre
    out = []
    lo, hi = min(offsets) - 0.075, max(offsets) + 0.075
    if across == "z":
        out.append(gbox(f"{tag}_strut", (cx - 0.02, cy - 0.032, lo), (cx + 0.02, cy, hi), STEEL, 0.003))
        rods = [(cx, lo + 0.022), (cx, hi - 0.022)]
        for (x, z) in rods:
            out.append(C.gtube(f"{tag}_rod", [(x, top, z), (x, cy - 0.04, z)], 0.005, sides=6, mat=STEEL))
            out.append(C.gcyl(f"{tag}_nut", 0.009, 0.012, (x, cy - 0.045, z), axis="y", verts=6, mat=STEEL, bevel=0.0))
            out.append(C.gcyl(f"{tag}_plate", 0.02, 0.006, (x, top - 0.006, z), axis="y", verts=8, mat=STEEL, bevel=0.0))
        for z in offsets:
            out.append(clamp_ring(f"{tag}_ring{z}", GV((cx, 3.25, z)), GV((1, 0, 0))))
    else:
        out.append(gbox(f"{tag}_strut", (lo, cy - 0.032, cz - 0.02), (hi, cy, cz + 0.02), STEEL, 0.003))
        rods = [(lo + 0.022, cz), (hi - 0.022, cz)]
        for (x, z) in rods:
            out.append(C.gtube(f"{tag}_rod", [(x, top, z), (x, cy - 0.04, z)], 0.005, sides=6, mat=STEEL))
            out.append(C.gcyl(f"{tag}_nut", 0.009, 0.012, (x, cy - 0.045, z), axis="y", verts=6, mat=STEEL, bevel=0.0))
            out.append(C.gcyl(f"{tag}_plate", 0.02, 0.006, (x, top - 0.006, z), axis="y", verts=8, mat=STEEL, bevel=0.0))
        for x in offsets:
            out.append(clamp_ring(f"{tag}_ring{x}", GV((x, 3.25, cz)), GV((0, 0, 1))))
    return out


# ====================================================================== wall dressing
def dressing():
    parts = []
    # --- framed archive rules notice, east wall by the entrance, facing -x
    cz, cy = 2.9, 1.665
    w, h = 0.34, 0.44
    fm = WE.m() @ Matrix.Translation((cz, cy, 0.0))
    prof = [(0.0, 0.0), (0.0, 0.014), (0.005, 0.021), (0.019, 0.022), (0.026, 0.013), (0.03, 0.006), (0.03, 0.0)]
    path = A.rect_path(fm, -w / 2, w / 2, -h / 2, h / 2)
    parts.append(A.sweep("notice_frame", prof, path, up=GV(WE.n), closed=True, mat=WAL))
    back = M.box("notice_back", (w - 0.04, h - 0.04, 0.004), loc=(0, 0, 0.002), mat="M_Paper", bevel=0.0)
    A.place(back, fm)
    parts.append(back)
    C.decal("M_Decal_ArchiveRules", "archive_rules.jpg")
    notice = C.gquad("rules_notice", (X1 - 0.0045, cy, cz), (0, 0, 1), (0, 1, 0), w - 0.06, h - 0.06, "M_Decal_ArchiveRules")
    # --- wall clock above the vault frame, stopped at 4:17
    ccx, ccy, cz0 = 1.5, 2.95, Z0
    cm = C.gframe((ccx, ccy, cz0), (1, 0, 0), (0, 1, 0))       # local z = +Godot z (out of the wall)
    case = M.lathe("clock_case", [(0.150, 0.0), (0.158, 0.004), (0.160, 0.026), (0.156, 0.030), (0.0, 0.030)],
                   segments=28, mat="M_Bakelite")
    case.data.transform(cm)
    parts.append(A.hint(case, 40))
    bezel = A.lathe_loop("clock_bezel", [(0.143, 0.030), (0.170, 0.030), (0.176, 0.036), (0.176, 0.048), (0.170, 0.056),
                                         (0.160, 0.058), (0.150, 0.054), (0.145, 0.044)], segments=28, mat="M_Chrome")
    bezel.data.transform(cm)
    parts.append(A.hint(bezel, 50))
    face = M.cylinder("clock_face", 0.146, 0.004, loc=(0, 0, 0.036), verts=28, mat="M_Enamel_White", bevel=0.0)
    face.data.transform(Matrix.Translation(face.location))
    face.location = (0, 0, 0)
    face.data.transform(cm)
    parts.append(face)
    # batons + minute ticks (flat, on the face at z 0.0385)
    bm = bmesh.new()
    zf = 0.0384
    for i in range(60):
        a = math.radians(90 - 6 * i)
        if i % 5 == 0:
            r0, r1, hw = 0.100, 0.135, (0.0065 if i % 15 == 0 else 0.0042)
        else:
            r0, r1, hw = 0.126, 0.135, 0.0011
        d = Vector((math.cos(a), math.sin(a), 0))
        nrm = Vector((-d.y, d.x, 0))
        vs = [bm.verts.new(cm @ (d * r0 - nrm * hw + Vector((0, 0, zf)))),
              bm.verts.new(cm @ (d * r1 - nrm * hw + Vector((0, 0, zf)))),
              bm.verts.new(cm @ (d * r1 + nrm * hw + Vector((0, 0, zf)))),
              bm.verts.new(cm @ (d * r0 + nrm * hw + Vector((0, 0, zf))))]
        f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ticks = A.obj_from_bm("clock_ticks", bm, "M_Lacquer_Black")
    for p in ticks.data.polygons:
        if p.normal.dot(GV((0, 0, 1))) < 0:
            p.flip()
    parts.append(ticks)

    def hand(name, length, tail, w0, w1, z, ang_cw, mat="M_Lacquer_Black"):
        pts = [(-w0, -tail), (w0, -tail), (w1, length), (0.0, length + w1 * 1.5), (-w1, length)]
        o = M.extrude_profile(name, A.ccw(pts), 0.0012, mat=mat, bevel=0.0)
        o.data.transform(Matrix.Rotation(-math.radians(ang_cw), 4, "Z"))
        o.data.transform(Matrix.Translation((0, 0, z)))
        o.data.transform(cm)
        return o
    parts.append(hand("clock_hour", 0.078, 0.018, 0.0062, 0.0045, 0.0395, (4 + 17 / 60) * 30))
    parts.append(hand("clock_minute", 0.118, 0.022, 0.0045, 0.0028, 0.0410, 17 * 6))
    parts.append(hand("clock_second", 0.122, 0.034, 0.0012, 0.0009, 0.0425, 41 * 6, mat="M_Enamel_Crimson"))
    cap = M.cylinder("clock_cap", 0.0075, 0.005, loc=(0, 0, 0.044), verts=12, mat="M_Lacquer_Black", bevel=0.001, segments=1)
    cap.data.transform(Matrix.Translation(cap.location))
    cap.location = (0, 0, 0)
    cap.data.transform(cm)
    parts.append(cap)
    glass = M.lathe("clock_glass", [(0.0, 0.054), (0.08, 0.052), (0.146, 0.047), (0.146, 0.045), (0.0, 0.045)],
                    segments=28, mat="M_Glass")
    glass.data.transform(cm)
    A.hint(glass, 60)
    add("wall_dressing", *parts)
    add("rules_notice", notice)
    add("clock_glass", glass)


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    groups.clear()
    shell()
    pilasters()
    hall_trims()
    bulb = booth()
    sh, lamp = shutter()
    corridor()
    bodies, glasses, lights = emergency_lamps()
    empties = tube_run()
    dressing()
    objs = {}
    for g, lst in groups.items():
        objs[g] = C.part(g, lst)
    A.presmooth(glasses + [bulb, lamp])
    C.finalize_all(wood_grain=True)
    # booth bulb origin at the bulb centre (contract: (-3.0, 2.65, 2.85))
    M.set_origin(bulb, G(-3.0, 2.65, 2.85))
    M.empty("booth_light", G(-3.0, 2.65, 2.85))
    return objs


def verify(path):
    req = (["floor", "ceiling", "wall_n", "wall_e", "wall_s", "wall_w", "booth_walls", "booth_ceiling", "booth_glass",
            "tube_run", "tube_glass", "corridor", "trim", "fire_shutter", "shutter_lamp", "booth_bulb", "film_cans"]
           + [f"tube_p{i}" for i in range(5)] + ["tube_q0"]
           + [f"elamp_{k}" for k in range(10)] + [f"elamp_glass_{k}" for k in range(10)] + [f"elamp_light_{k}" for k in range(10)])
    expect = {f"tube_p{i}": p for i, p in enumerate(TUBE_P)}
    expect["tube_q0"] = TUBE_Q[0]
    expect["fire_shutter"] = (3.5, 0.0, 3.45)
    expect["booth_bulb"] = (-3.0, 2.65, 2.85)
    ident = ["fire_shutter", "shutter_lamp", "booth_bulb"] + [f"elamp_glass_{k}" for k in range(10)] + list(expect)
    errs = C.verify_glb(path, required=req, identity=ident, budget=30000, expect=expect,
                        show=["fire_shutter", "shutter_lamp", "booth_bulb", "elamp_light_0", "elamp_light_9", "tube_q0"])
    return errs


# ====================================================================== QA
def qa_scene(neighbours=True):
    """Small group-A models at their placements + whatever other groups have exported."""
    for p in C.PENDANTS:
        C.qa_import(C.model_glb("archive_pendant"), p, 0.0)
    for nm, pos, yaw in (("vent_grille", (-5.0, 2.55, 0.9), 90.0), ("floor_hatch", (0.9, 0.0, 2.5), 0.0),
                         ("projection_screen", (-2.5, 0.0, -3.5), 0.0), ("library_ladder", (-4.62, 0.0, 0.35), 90.0)):
        C.qa_import(C.model_glb(nm), pos, yaw)
    if not neighbours:
        return
    for nm, pos, yaw in (("card_catalogue", (-5.0, 0, -1.2), 90.0), ("stacks_shelving", (0.0, 0, 0.25), 0.0),
                         ("archivist_desk", (3.7, 0, -3.1), 0.0), ("reading_table", (1.9, 0, 1.0), 0.0),
                         ("lockers", (0.6, 0, 3.5), 180.0), ("routing_chart", (5.0, 0, -0.35), -90.0),
                         ("film_splicer", (-3.9, 0, 3.5), 180.0), ("slide_cabinet", (-5.0, 0, 2.8), 90.0),
                         ("lens_case", (-3.75, 1.45, 3.37), 180.0), ("tube_station", (5.0, 0, -1.4), -90.0),
                         ("compressor_panel", (5.0, 0, 0.8), -90.0), ("card_punch", (3.25, 0.76, -3.05), 0.0),
                         ("tape_deck", (4.15, 0.76, -3.05), 0.0), ("booth_door", (-1.55, 0, 2.0), 180.0),
                         ("film_projector", (-2.9, 0, 2.65), 180.0), ("slide_projector", (-2.35, 0, 2.45), 180.0),
                         ("vault_door", (1.5, 0, -3.5), 0.0), ("vault_interior", (0, 0, 0), 0.0),
                         ("chair", (3.55, 0.0, -2.35), 172.0), ("chair", (1.55, 0.0, 1.62), 186.0),
                         ("chair", (2.35, 0.0, 0.42), -8.0), ("desk_lamp", (3.05, 0.76, -3.32), 20.0)):
        C.qa_import(C.model_glb(nm), pos, yaw)


def main():
    args = M.main_guard()
    build()
    C.report(NAME)
    path = C.export(NAME)
    verify(path)
    if "--no-render" in args:
        return
    sel = C.args_shots(args)
    C.qa_begin(bounces=6)
    qa_scene(neighbours="--bare" not in args)
    lit = bpy.data.materials.get("M_Emissive_Red")
    if C.want("hall", sel):
        C.qa_room_lights()
        C.shoot(NAME, (3.8, 1.65, 1.8), (0.0, 1.3, -2.2), vfov=62)
        C.qa_clear()
    if C.want("west", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_west", (-1.8, 1.65, 1.0), (-3.0, 1.5, -3.0), vfov=62)
        C.qa_clear()
    if C.want("booth", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_booth", (-1.55, 1.6, 2.6), (-4.6, 1.1, 2.9), vfov=62)
        C.qa_clear()
    if C.want("tubes", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_tubes", (2.6, 1.7, 1.2), (1.6, 3.1, -1.3), vfov=62)
        C.qa_clear()
    if C.want("shutter", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_shutter", (2.6, 1.6, 0.6), (3.5, 1.5, 3.4), vfov=56)
        C.qa_clear()
    if C.want("elamp", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_elamp", (4.25, 2.6, -0.45), (5.0, 2.95, 0.0), vfov=40)
        C.qa_clear()
    if C.want("booth_ext", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_booth_ext", (0.6, 1.6, -0.4), (-2.6, 1.6, 2.0), vfov=62)
        C.qa_clear()
    if C.want("intro", sel):        # shutter raised (+2.25 y) as in the intro "before" shot
        sh = bpy.data.objects.get("fire_shutter")
        if sh:
            sh.location.z += 2.25
        C.qa_room_lights()
        C.shoot(NAME + "_intro", (3.3, 1.6, 0.3), (3.5, 1.3, 4.5), vfov=62)
        C.qa_clear()
        if sh:
            sh.location.z -= 2.25
    _ = lit


main()
