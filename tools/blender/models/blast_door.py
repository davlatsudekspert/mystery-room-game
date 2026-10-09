"""blast_door.glb — the Resonance Gallery's two blast doors (×2: door_west, door_east), each with its drum lock.
Contract: docs/models/ch3.md §3 blast_door (+ §1.1 tunnels, §1.3 drum locks, §2 views); results: docs/models/ch3_a.md.

Front +Z = the Gallery side. Origin = the bay face at floor level. West (-3.70, 0, 0) yaw 90; east (3.70, 0, 0) yaw -90.

  door_frame (static)  dark riveted steel plate x ±1.5, y 0..3.0, z 0..0.12 around the 1.6 x 2.4 opening, amber/black
                       chevrons on the lintel, the top rail and the pocket housing to x = +2.8 (hidden in the wall mass),
                       the drum-lock box x -1.40..-0.92, y 0.85..1.80, front z = 0.24 with four shrouded windows in
                       brass bezels, the four brass ring icons (x = -0.99) and the lamp bezel.
  IA_door_tunnel       the steel tunnel lining z 0 .. -0.80 (walls, ceiling, floor plates, hall-side flange), slotted
                       where the leaf runs.
  IA_blast_door        the leaf 1.8 x 2.55 x 0.25 at z -0.32 .. -0.07; Gallery face: rivets + a large relief of the
                       Institute mark; hall face: the big handwheel, dog bars and braces. Open = slide +1.9 local X.
  IA_drum_0..3         brass drums Ø0.10 x 0.08, axis local +X, centres (-1.16, 1.545 - 0.13 i, 0.19); six dark-steel
                       symbols in DRUM_SYMBOLS order at Basis(X, +60° s)·(0, 0, 1); one step = -60° about local +X.
  IA_drum_handle       brass T-handle, pivot (-1.16, 0.98, 0.21); pull = +45° about local +X.
  drum_lamp            amber jewel at (-1.16, 1.72, 0.25) (code tint).

    blender -b --factory-startup -P tools/blender/models/blast_door.py [-- --no-render] [--shots=1,2,...]
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
import lib_ch2_arch as C2  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "blast_door"
TRI_BUDGET, SURF_BUDGET = 9000, 15
STEEL, PAINT, BRASS, AMBER = K.STEEL, K.PAINT, K.BRASS, K.AMBER

OPEN_W, OPEN_H = 0.8, 2.4               # half width, height of the opening
FZ = 0.10                               # frame plate face (raised lip to 0.12)
LEAF = (-0.9, 0.9, 0.0, 2.55, -0.32, -0.07)
LEAF_OPEN = 1.9
SLOT_Z = (-0.46, -0.05)                 # lining slot on the pocket side (leaf + handwheel)
JAMB_Z = (-0.34, -0.05)                 # receiving slot on the closed side
BOX = (-1.40, -0.92, 0.85, 1.80)        # drum-lock box x0, x1, y0, y1
BOX_FRONT = 0.24
DRUM_X, DRUM_Z, DRUM_R, DRUM_L = -1.16, 0.19, 0.050, 0.080
BAND_R = 0.0485
WIN_W, WIN_H = 0.084, 0.046
ICON_X, ICON_D = -0.99, 0.075
HANDLE = (-1.16, 0.98, 0.21)
LAMP = (-1.16, 1.72, 0.25)


def drum_y(i):
    return 1.545 - 0.13 * i


# ====================================================================== static frame
def chevrons():
    """Amber / black chevron band on the lintel (pointing up at the centre), 5 mm plates on the frame face."""
    out = []
    y0, y1, xm = 2.56, 2.92, 1.40
    hgt, w = y1 - y0, 0.14
    for side in (-1, 1):
        a, idx = -xm - hgt, 0
        while a < 0.0:
            poly = [(a, y0), (a + w, y0), (a + w + hgt, y1), (a + hgt, y1)]       # left half: rising to the right
            if side > 0:
                poly = [(-x, y) for (x, y) in poly]                                # mirrored: rising to the left
            lo, hi = (-xm, 0.0) if side < 0 else (0.0, xm)
            cp = C2.clip_poly_x(poly, lo, hi)
            if len(cp) >= 3 and abs(A.signed_area(cp)) > 1e-5:
                out.append(K.plate("chev", [A.ccw(cp)], 0.005, z0=FZ, mat=AMBER if idx % 2 == 0 else STEEL, bevel=0.0))
            a += w
            idx += 1
    return out


def drum_box():
    x0, x1, y0, y1 = BOX
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = []
    t = 0.012
    # hollow body: four side walls from the frame face to just behind the front plate
    zf = BOX_FRONT - 0.008
    out += [K.gbox("bx_l", (x0, y0, FZ), (x0 + t, y1, zf), STEEL, 0.003),
            K.gbox("bx_r", (x1 - t, y0, FZ), (x1, y1, zf), STEEL, 0.003),
            K.gbox("bx_b", (x0 + t, y0, FZ), (x1 - t, y0 + t, zf), STEEL, 0.003),
            K.gbox("bx_t", (x0 + t, y1 - t, FZ), (x1 - t, y1, zf), STEEL, 0.003)]
    # front plate with the four windows and the handle recess
    holes = [L.rounded_rect(WIN_W, WIN_H, 0.006, 3, cx=DRUM_X - cx, cy=drum_y(i) - cy) for i in range(4)]
    holes.append(L.rounded_rect(0.090, 0.165, 0.02, 4, cx=HANDLE[0] - cx, cy=1.012 - cy))
    front = K.plate("bx_front", [L.rounded_rect(x1 - x0, y1 - y0, 0.018, 4)] + holes, 0.008, mat=STEEL,
                    bevel=0.002, loc=(cx, cy, zf))
    out.append(front)
    # corner screws
    for (bx, by) in ((x0 + 0.025, y0 + 0.025), (x1 - 0.025, y0 + 0.025), (x0 + 0.025, y1 - 0.025), (x1 - 0.025, y1 - 0.025)):
        out.append(K.rivet("bxb", 0.0075, (bx, by, BOX_FRONT), segs=6))
    return out


def brass_static():
    out = []
    zf = BOX_FRONT
    for i in range(4):
        y = drum_y(i)
        out.append(K.plate("bezel", [L.rounded_rect(WIN_W + 0.022, WIN_H + 0.020, 0.012, 4),
                                     L.rounded_rect(WIN_W, WIN_H, 0.006, 3)], 0.007, mat=BRASS, bevel=0.0,
                           loc=(DRUM_X, y, zf)))
        # reading index: two small brass pointers at the window's mid-height
        for sx in (-1, 1):
            tip = DRUM_X + sx * (WIN_W / 2 + 0.003)
            base = DRUM_X + sx * (WIN_W / 2 + 0.010)
            out.append(K.plate("idx", [A.ccw([(tip, y), (base, y - 0.004), (base, y + 0.004)])], 0.002, z0=zf + 0.007,
                               mat=BRASS, bevel=0.0))
        # ring icon: four concentric circles, circle i bold (flat brass inlay on a small brass disc)
        out.append(K.flat("icon", [lp for shp in S.ring_icon(i, ICON_D, n=20) for lp in shp], zf + 0.0006,
                          (ICON_X, y), BRASS))
    # lamp bezel
    out.append(K.glathe("lampbz", [(0.024, 0.0), (0.024, 0.004), (0.019, 0.008), (0.0145, 0.0075), (0.0145, 0.0)],
                        (LAMP[0], LAMP[1], zf), (0, 0, 1), 12, BRASS, smooth=50.0))
    return out


def static_frame():
    parts = []
    w, h, z0, z1 = 1.5, 3.0, 0.0, FZ
    parts += [K.gbox("fr_l", (-w, 0, z0), (-OPEN_W, h, z1), STEEL, 0.008, 1),
              K.gbox("fr_r", (OPEN_W, 0, z0), (w, h, z1), STEEL, 0.008, 1),
              K.gbox("fr_t", (-OPEN_W - 0.01, OPEN_H, z0), (OPEN_W + 0.01, h, z1), STEEL, 0.008, 1)]
    # raised lip around the opening (to z = 0.12)
    lip = 0.085
    parts += [K.gbox("lip_l", (-OPEN_W - lip, 0, z1 - 0.004), (-OPEN_W, OPEN_H + lip, 0.12), STEEL, 0.006, 1),
              K.gbox("lip_r", (OPEN_W, 0, z1 - 0.004), (OPEN_W + lip, OPEN_H + lip, 0.12), STEEL, 0.006, 1),
              K.gbox("lip_t", (-OPEN_W, OPEN_H, z1 - 0.004), (OPEN_W, OPEN_H + lip, 0.12), STEEL, 0.006, 1)]
    # rivets: around the lip and along the outer edge
    for y in [0.20 + 0.30 * k for k in range(8)]:
        parts.append(K.rivet("rv", 0.011, (OPEN_W + lip + 0.045, y, z1), segs=6))
        parts.append(K.rivet("rv", 0.011, (w - 0.05, y, z1), segs=6))
        parts.append(K.rivet("rv", 0.011, (-w + 0.05, y, z1), segs=6))
    for x in [-1.35 + 0.3 * k for k in range(10)]:
        parts.append(K.rivet("rv", 0.011, (x, h - 0.04, z1), segs=6))
    for (bx, by) in ((-1.38, 0.12), (1.38, 0.12), (-1.38, 2.86), (1.38, 2.86)):
        parts.append(K.hexbolt("anc", 0.018, (bx, by, z1), h=0.014, washer=False))
    parts += chevrons()
    parts += drum_box()
    parts += brass_static()
    # hidden in the wall mass: top rail, pocket housing (inward box) to x = +2.85
    parts.append(K.gbox("rail", (-1.05, 2.60, -0.24), (2.85, 2.66, -0.15), STEEL, 0.004))
    px0, px1, py0, py1, pz0, pz1 = 0.83, 2.85, -0.02, 2.70, -0.47, -0.03
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((px0, py0, pz0), (px1, py0, pz0), (px1, py1, pz0), (px0, py1, pz0),
                                     (px0, py0, pz1), (px1, py0, pz1), (px1, py1, pz1), (px0, py1, pz1))]
    for f in ((0, 1, 2, 3), (5, 4, 7, 6), (1, 5, 6, 2), (0, 4, 5, 1), (3, 2, 6, 7)):
        bm.faces.new([vs[i] for i in f])
    pocket = K.obj_from_bm("pocket", bm, STEEL)
    # normals inward: flip any face whose normal points away from the box centre
    me = pocket.data
    bm = bmesh.new()
    bm.from_mesh(me)
    c = Vector(((px0 + px1) / 2, (py0 + py1) / 2, (pz0 + pz1) / 2))
    for f in bm.faces:
        if f.normal.dot(f.calc_center_median() - c) > 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    parts.append(pocket)
    return K.part("door_frame", parts)


# ====================================================================== tunnel lining
def tunnel():
    t = 0.03
    zb = -0.80
    parts = []
    # side walls (pocket side +X slotted for the leaf + handwheel, closed side -X slotted for the leaf edge)
    for (zs0, zs1), sx in ((SLOT_Z, 1), (JAMB_Z, -1)):
        x0, x1 = (OPEN_W, OPEN_W + t) if sx > 0 else (-OPEN_W - t, -OPEN_W)
        parts.append(K.gbox("lw_front", (x0, 0.0, zs1), (x1, OPEN_H, 0.0), STEEL, 0.004))
        parts.append(K.gbox("lw_back", (x0, 0.0, zb), (x1, OPEN_H, zs0), STEEL, 0.004))
        # slot edge guides (U channel lips)
        for z in (zs0, zs1):
            parts.append(K.gbox("guide", (x0, 0.0, z - 0.012), (x1, OPEN_H, z + 0.012), STEEL, 0.0))
    # receiving channel behind the closed-side slot
    parts.append(K.gbox("jamb", (-OPEN_W - 0.12, 0.0, JAMB_Z[0] - 0.02), (-OPEN_W - t, OPEN_H + 0.12, JAMB_Z[0]), STEEL, 0.0))
    parts.append(K.gbox("jamb2", (-OPEN_W - 0.12, 0.0, JAMB_Z[1]), (-OPEN_W - t, OPEN_H + 0.12, JAMB_Z[1] + 0.02), STEEL, 0.0))
    parts.append(K.gbox("jamb3", (-OPEN_W - 0.14, 0.0, JAMB_Z[0] - 0.02), (-OPEN_W - 0.12, OPEN_H + 0.12, JAMB_Z[1] + 0.02), STEEL, 0.0))
    # ceiling (slotted where the leaf rises into the lintel)
    parts.append(K.gbox("ceil_f", (-OPEN_W - t, OPEN_H, SLOT_Z[1]), (OPEN_W + t, OPEN_H + t, 0.0), STEEL, 0.004))
    parts.append(K.gbox("ceil_b", (-OPEN_W - t, OPEN_H, zb), (OPEN_W + t, OPEN_H + t, SLOT_Z[0]), STEEL, 0.004))
    # floor plates either side of the leaf channel, with a raised tread pattern of welded bars
    parts.append(K.gbox("fl_f", (-OPEN_W, -0.03, JAMB_Z[1]), (OPEN_W, 0.012, 0.0), STEEL, 0.003))
    parts.append(K.gbox("fl_b", (-OPEN_W, -0.03, zb), (OPEN_W, 0.012, JAMB_Z[0]), STEEL, 0.003))
    parts.append(K.gbox("fl_ch", (-OPEN_W, -0.05, JAMB_Z[0]), (OPEN_W, -0.04, JAMB_Z[1]), STEEL, 0.0))
    for z in (-0.45, -0.65):
        parts.append(K.gbox("tread", (-0.62, 0.012, z - 0.012), (0.62, 0.020, z + 0.012), STEEL, 0.003))
    # rib frames inside the tunnel and the hall-side flange (a steel angle on the hall wall face)
    for z in (-0.60,):
        parts += [K.gbox("rib", (OPEN_W - 0.025, 0.0, z - 0.03), (OPEN_W, OPEN_H, z + 0.03), STEEL, 0.004),
                  K.gbox("rib", (-OPEN_W, 0.0, z - 0.03), (-OPEN_W + 0.025, OPEN_H, z + 0.03), STEEL, 0.004),
                  K.gbox("rib", (-OPEN_W, OPEN_H - 0.025, z - 0.03), (OPEN_W, OPEN_H, z + 0.03), STEEL, 0.004)]
    fw = 0.10
    parts += [K.gbox("fl_l", (-OPEN_W - t - fw, 0.0, zb - 0.02), (-OPEN_W - t, OPEN_H + t, zb), STEEL, 0.004),
              K.gbox("fl_r", (OPEN_W + t, 0.0, zb - 0.02), (OPEN_W + t + fw, OPEN_H + t, zb), STEEL, 0.004),
              K.gbox("fl_t", (-OPEN_W - t - fw, OPEN_H + t, zb - 0.02), (OPEN_W + t + fw, OPEN_H + t + fw, zb), STEEL, 0.004)]
    for y in (0.3, 1.2, 2.1):
        for sx in (-1, 1):
            parts.append(K.rivet("frv", 0.010, (sx * (OPEN_W + t + fw / 2), y, zb - 0.02), normal=(0, 0, -1), segs=6))
    return K.part("IA_door_tunnel", parts, pivot=(0.0, 0.0, -0.40))


# ====================================================================== leaf
def leaf():
    x0, x1, y0, y1, z0, z1 = LEAF
    parts = [K.gbox("leaf", (x0, y0, z0), (x1, y1, z1), PAINT, 0.012, 2)]
    # Gallery face (+Z): edge band with rivets, the Institute mark relief
    b, tb = 0.09, 0.010
    parts += [K.gbox("band", (x0 + 0.01, y0 + 0.01, z1), (x0 + b, y1 - 0.01, z1 + tb), PAINT, 0.004),
              K.gbox("band", (x1 - b, y0 + 0.01, z1), (x1 - 0.01, y1 - 0.01, z1 + tb), PAINT, 0.004),
              K.gbox("band", (x0 + b, y1 - b, z1), (x1 - b, y1 - 0.01, z1 + tb), PAINT, 0.004),
              K.gbox("band", (x0 + b, y0 + 0.01, z1), (x1 - b, y0 + b, z1 + tb), PAINT, 0.004),
              K.gbox("band", (x0 + b, 0.62, z1), (x1 - b, 0.70, z1 + tb), PAINT, 0.004)]
    for y in [0.20 + 0.33 * k for k in range(7)]:
        for sx in (-1, 1):
            parts.append(K.rivet("lrv", 0.011, (sx * (x1 - b / 2), y, z1 + tb), segs=6, mat=PAINT))
    for x in [-0.45 + 0.30 * k for k in range(4)]:
        parts.append(K.rivet("lrv", 0.011, (x, y1 - b / 2, z1 + tb), segs=6, mat=PAINT))
        parts.append(K.rivet("lrv", 0.011, (x, 0.66, z1 + tb), segs=6, mat=PAINT))
    mark = S.inlay("mark", "mark_ticks", 1.05, depth=0.016, mat=PAINT, bevel=0.0)
    mark.data.transform(Matrix.Translation((0.0, 1.55, z1)))
    parts.append(mark)
    # hall face (-Z): perimeter band, dog bars in guides, braces, the big handwheel
    zh = z0
    parts += [K.gbox("hband", (x0 + 0.01, y0 + 0.01, zh - tb), (x0 + b, y1 - 0.01, zh), PAINT, 0.004),
              K.gbox("hband", (x1 - b, y0 + 0.01, zh - tb), (x1 - 0.01, y1 - 0.01, zh), PAINT, 0.004)]
    hy = 1.25
    parts += [K.gbox("dog", (-0.03, 0.12, zh - 0.035), (0.03, hy - 0.10, zh - 0.012), PAINT, 0.005),
              K.gbox("dog", (-0.03, hy + 0.10, zh - 0.035), (0.03, y1 - 0.12, zh - 0.012), PAINT, 0.005)]
    for (ax, ay, bx, by) in ((x0 + b, y0 + b, -0.30, hy - 0.22), (x1 - b, y0 + b, 0.30, hy - 0.22),
                             (x0 + b, y1 - b, -0.30, hy + 0.22), (x1 - b, y1 - b, 0.30, hy + 0.22)):
        d = Vector((bx - ax, by - ay, 0))
        ln = d.length
        br = K.gbox("brace", (-ln / 2, -0.035, zh - 0.022), (ln / 2, 0.035, zh), PAINT, 0.004)
        br.data.transform(Matrix.Translation(((ax + bx) / 2, (ay + by) / 2, 0)) @
                          Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
        parts.append(br)
    hub = K.glathe("hub", [(0.0, 0.0), (0.09, 0.0), (0.09, 0.02), (0.06, 0.035), (0.05, 0.10), (0.035, 0.12),
                           (0.0, 0.12)], (0.0, hy, zh), (0, 0, -1), 20, PAINT, smooth=45.0)
    parts.append(hub)
    rim_r, rim_z = 0.31, zh - 0.09
    rim = M.torus("rim", rim_r, 0.022, major_seg=24, minor_seg=6, mat=PAINT)
    rim.data.transform(Matrix.Translation((0.0, hy, rim_z)))
    A.hint(rim, 70.0)
    parts.append(rim)
    for k in range(5):
        a = math.radians(90 + 72 * k)
        p0 = Vector((0.045 * math.cos(a), hy + 0.045 * math.sin(a), zh - 0.085))
        p1 = Vector(((rim_r - 0.01) * math.cos(a), hy + (rim_r - 0.01) * math.sin(a), rim_z))
        parts.append(K.gcyl("spoke", 0.016, 0.0, (p1 - p0).length, base=tuple(p0), axis=tuple(p1 - p0), segments=6,
                            mat=PAINT))
    # hanger trolleys on the top edge (run in the top rail)
    for x in (-0.55, 0.55):
        parts.append(K.gbox("trolley", (x - 0.10, y1, -0.235), (x + 0.10, 2.60, -0.155), PAINT, 0.006))
    return K.part("IA_blast_door", parts, pivot=(0.0, 0.0, (z0 + z1) / 2))


# ====================================================================== drums, handle, lamp
def drum(i):
    y = drum_y(i)
    prof = [(0.008, -DRUM_L / 2 - 0.004), (0.046, -DRUM_L / 2), (0.0500, -DRUM_L / 2 + 0.004, "k"),
            (0.0500, -0.029, "k"), (BAND_R, -0.027), (BAND_R, 0.027), (0.0500, 0.029, "k"),
            (0.0500, DRUM_L / 2 - 0.004, "k"), (0.046, DRUM_L / 2), (0.008, DRUM_L / 2 + 0.004)]
    body = K.glathe("drum", prof, (DRUM_X, y, DRUM_Z), (1, 0, 0), 18, BRASS, knurl=0.0012, smooth=40.0)
    parts = [body]
    for s, kind in enumerate(S.DRUM_ORDER):
        sym = S.inlay("sym", kind, 0.034, depth=0.0, mat=STEEL)
        sym.data.transform(Matrix.Translation((0, 0, 0.0004)))
        K.slice_y(sym, 0.0085, -0.02, 0.02)
        K.wrap_x(sym, BAND_R)
        sym.data.transform(Matrix.Translation((DRUM_X, y, DRUM_Z)) @ Matrix.Rotation(math.radians(60 * s), 4, "X"))
        A.hint(sym, 30.0)
        parts.append(sym)
    return K.part(f"IA_drum_{i}", parts, pivot=(DRUM_X, y, DRUM_Z))


def handle():
    x, y, z = HANDLE
    parts = [K.gcyl("boss", 0.016, -0.022, 0.022, base=(x, y, z), axis=(1, 0, 0), segments=10, mat=BRASS, chamfer=0.002)]
    parts.append(K.glathe("stem", [(0.0, 0.0), (0.009, 0.0), (0.008, 0.07), (0.0085, 0.078), (0.0, 0.08)],
                          (x, y, z), (0, 1, 0), 12, BRASS, smooth=50.0))
    parts.append(K.glathe("tbar", [(0.0, -0.038), (0.008, -0.038), (0.011, -0.032), (0.011, 0.032), (0.008, 0.038),
                                   (0.0, 0.038)], (x, y + 0.085, z), (1, 0, 0), 12, BRASS, smooth=50.0))
    return K.part("IA_drum_handle", parts, pivot=HANDLE)


def lamp():
    x, y, z = LAMP
    o = K.glathe("jewel", [(0.0145, -0.004), (0.0145, 0.0), (0.012, 0.005), (0.007, 0.0085), (0.0, 0.0095)],
                 (x, y, z), (0, 0, 1), 12, AMBER, smooth=80.0)
    return K.part("drum_lamp", [o], pivot=LAMP)


# ====================================================================== build / verify
def build():
    M.reset_scene()
    K.ensure_materials()
    frame = static_frame()
    tun = tunnel()
    lf = leaf()
    drums = [drum(i) for i in range(4)]
    hdl = handle()
    lmp = lamp()
    K.to_blender()
    A.finalize_uv()
    return dict(frame=frame, tunnel=tun, leaf=lf, drums=drums, handle=hdl, lamp=lmp)


def verify(path):
    req = ["door_frame", "IA_door_tunnel", "IA_blast_door", "IA_drum_handle", "drum_lamp"] + [f"IA_drum_{i}" for i in range(4)]
    expect = {f"IA_drum_{i}": (DRUM_X, drum_y(i), DRUM_Z) for i in range(4)}
    expect.update({"IA_drum_handle": HANDLE, "drum_lamp": LAMP})
    errs = K.V.verify_glb(path, required=req, identity=req, expect=expect, parents={n: None for n in req}, show=req)
    errs += K.facts(path, TRI_BUDGET, SURF_BUDGET)
    lo, hi = K.V.mesh_bounds_godot([bpy.data.objects["door_frame"]])
    print(f"{K.TAG} door_frame bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    lo, hi = K.V.mesh_bounds_godot([bpy.data.objects["IA_blast_door"]])
    print(f"{K.TAG} leaf bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    lo, hi = K.V.mesh_bounds_godot([bpy.data.objects["IA_door_tunnel"]])
    print(f"{K.TAG} tunnel bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, drums=(0, 0, 0, 0), pulled=False, open_=False):
    for o in [parts["leaf"], parts["handle"]] + parts["drums"]:
        o.matrix_basis = REST[o.name].copy()
    M.refresh()
    for d, s in zip(parts["drums"], drums):
        K.pose_rot(d, "x", -60.0 * s)
    if pulled:
        K.pose_rot(parts["handle"], "x", 45.0)
    if open_:
        K.pose_slide(parts["leaf"], (LEAF_OPEN, 0.0, 0.0))


def qa_context():
    """Proxy Gallery bay (concrete wall with the opening, stone floor) and the hall wall behind (local coords)."""
    q = K.V._qbox
    for nm, mn, mx in (("bay_l", (-2.6, 0.0, -0.30), (-OPEN_W - 0.03, 4.5, 0.0)),
                       ("bay_r", (OPEN_W + 0.03, 0.0, -0.30), (3.0, 4.5, 0.0)),
                       ("bay_t", (-OPEN_W - 0.03, OPEN_H + 0.03, -0.30), (OPEN_W + 0.03, 4.5, 0.0))):
        q("qa_" + nm, mn, mx, K.CONC)
    q("qa_gfloor", (-2.6, -0.05, 0.0), (3.0, 0.0, 3.5), K.STONE)
    q("qa_hfloor", (-2.6, -0.05, -4.0), (3.0, 0.0, -0.80), "M_Concrete")
    for nm, mn, mx, mat in (("hw_l", (-2.6, 0.0, -0.86), (-OPEN_W - 0.03, 1.5, -0.80), K.GREEN),
                            ("hw_r", (OPEN_W + 0.03, 0.0, -0.86), (3.0, 1.5, -0.80), K.GREEN),
                            ("hw_lh", (-2.6, 1.5, -0.86), (-OPEN_W - 0.03, 4.5, -0.80), K.CONC),
                            ("hw_rh", (OPEN_W + 0.03, 1.5, -0.86), (3.0, 4.5, -0.80), K.CONC),
                            ("hw_t", (-OPEN_W - 0.03, OPEN_H + 0.03, -0.86), (OPEN_W + 0.03, 4.5, -0.80), K.CONC)):
        q("qa_" + nm, mn, mx, mat)


def qa(parts, args):
    K.qa_begin(bounces=6)
    for o in [parts["leaf"], parts["handle"]] + parts["drums"]:
        REST[o.name] = o.matrix_basis.copy()
    qa_context()
    lamp_obj = parts["lamp"]
    amber = K.glow("qa_lamp_amber", "FFA030", 6.0)
    green = K.glow("qa_lamp_green", "40FF70", 6.0)

    def gallery_lights(cam=None):
        K.clear_lights()
        K.light("key", "SPOT", (1.2, 4.2, 3.4), 900.0, "D8E8F4", radius=0.3, target=(-0.3, 1.0, 0.0), spot_deg=60)
        K.light("sconce", "POINT", (-2.2, 2.7, 1.6), 60.0, "FFD7A0", radius=0.1)
        K.light("lumen", "AREA", (0.0, -0.5, 3.6), 120.0, "CFF6FF", radius=2.0, target=(0.0, 1.5, 0.0))
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 8.0, "FFE2C2", radius=0.2)

    def hall_lights(cam=None):
        K.clear_lights()
        K.light("work", "POINT", (-1.6, 3.2, -2.2), 160.0, "FFC890", radius=0.15)
        K.light("work2", "POINT", (1.8, 3.0, -3.0), 90.0, "FFC890", radius=0.15)
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 10.0, "FFE2C2", radius=0.2)

    # 1 hero: three-quarter from the Gallery, closed, sealed (lamp amber)
    if K.want(args, "1"):
        pose(parts)
        old = K.override(lamp_obj, amber)
        gallery_lights()
        K.shoot(NAME, (1.7, 1.75, 3.3), (-0.25, 1.25, 0.0), vfov=56)
        K.restore(lamp_obj, old)
    # 2 the drum_west view at the start (all ☼), sealed
    if K.want(args, "2"):
        pose(parts)
        old = K.override(lamp_obj, amber)
        cam = (-1.16, 1.45, 1.15)
        gallery_lights(cam)
        K.shoot(NAME + "_2", cam, (-1.16, 1.30, 0.15), vfov=46)
        K.restore(lamp_obj, old)
    # 3 drum_west view at the target (☾ ▲ ✦ ●), handle pulled, lamp green
    if K.want(args, "3"):
        pose(parts, drums=(1, 3, 2, 4), pulled=True)
        old = K.override(lamp_obj, green)
        cam = (-1.16, 1.45, 1.15)
        gallery_lights(cam)
        K.shoot(NAME + "_3", cam, (-1.16, 1.30, 0.15), vfov=46)
        K.restore(lamp_obj, old)
    # 4 blast_west view, closed
    if K.want(args, "4"):
        pose(parts)
        gallery_lights((-0.7, 1.6, 1.75))
        K.shoot(NAME + "_4", (-0.7, 1.6, 1.75), (0.0, 1.3, 0.0), vfov=56)
    # 5 blast_west view, OPEN (leaf slid +1.9 into the pocket): the tunnel and the hall beyond
    if K.want(args, "5"):
        pose(parts, drums=(1, 3, 2, 4), open_=True)
        old = K.override(lamp_obj, green)
        gallery_lights((-0.7, 1.6, 1.75))
        K.light("hall", "POINT", (0.0, 2.6, -2.6), 140.0, "FFC890", radius=0.15)
        K.shoot(NAME + "_5", (-0.7, 1.6, 1.75), (0.0, 1.3, 0.0), vfov=56)
        K.restore(lamp_obj, old)
    # 6 blast_west_hall view from the Choir Hall: the leaf's hall face with the handwheel
    if K.want(args, "6"):
        pose(parts)
        hall_lights((0.0, 1.6, -2.8))
        K.shoot(NAME + "_6", (0.0, 1.6, -2.8), (0.0, 1.25, -0.8), vfov=56)


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
