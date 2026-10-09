"""vault_interior.glb — Leyla's hidden room behind the round vault door (Chapter 2 finale).

Contract: docs/models/ch2.md §1, §2 (vault_inside view), §6 (vault_interior). Measured results and
deviations: docs/models/ch2_vault.md.

Built in ROOM coordinates (Godot axes, origin = room origin). Space x 0.6..2.4, z -5.2..-3.7, y 0..2.5:
the tunnel continues from the door frame (bore r 0.86, z -3.70..-3.86) into a steel-lined strongroom with
a concrete floor 0.49 m below the bore sill (two steel steps), riveted ceiling with I-beams.

STATIC  vault_shell        floor, steel-lined walls + ceiling, front wall with the tunnel, steps
        vault_boxes        two banks of safe-deposit boxes (one door open, its box pulled out)
        vault_table        steel table at (1.5, 0, -4.35), top y 0.78
        field_kit          Leyla's canvas satchel, torch, thermos, folded map with her route, notebook +
                           pencil, a photograph propped against the satchel
        vault_projector    portable 8 mm projector on a tilt stand, aimed at the screen
        screen_roller      roller case, brackets, bottom batten and pull ring of the pull-down screen
        key_cradle         brass-framed velvet cradle (1.5, 1.15, -5.15) with the hook, rests and the
                           engraved mark / sign under each key; clamp guides
        bulb_fixture       ceiling canopy, holder and wire cage of the caged bulb
PARTS   vault_reel_screen  0.90 x 0.60 screen centred (1.5, 1.85, -5.17) facing +Z, UV 0..1
        vault_lamp_glow    projector lens glass + lamp-house vents (M_Glass: the code makes it glow)
        vault_lens_origin  empty at the lens front, local +Z = beam toward the screen centre
        cradle_clamp_left/right  brass jaws above each key; lock = slide -0.03 on local Y
        key_strand_mount / key_leyla_mount  (1.32 / 1.68, 1.18, -5.12), rotated +90° about X so the
                           flat-lying item hangs bow-up with its hero face +Z
        vault_bulb         emissive bulb glass (M_Emissive_Warm, toggled by code); vault_light empty

    blender -b --factory-startup -P tools/blender/models/vault_interior.py [-- --no-render] [--shots 1,2]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_vault as V  # noqa: E402

NAME = "vault_interior"
BUDGET = 14000
X0, X1 = 0.6, 2.4               # side wall faces
ZB, ZF = -5.2, -3.86            # back wall face, front wall inner face (tunnel z -3.70..-3.86)
ZT = -3.70                      # tunnel start (back face of the door frame's sleeve)
YC = 2.5                        # ceiling
CX, CY, BORE = 1.5, 1.35, 0.86  # tunnel axis and radius
TABLE_Y = 0.78
TABLE = (1.0, 2.0, -4.575, -4.125)
SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_Z = (1.5, 1.85), 0.90, 0.60, -5.17
MOUNTS = {"strand": (1.32, 1.18, -5.12), "leyla": (1.68, 1.18, -5.12)}
# hanging geometry of the D2 keys (item space, flat pose; read from key_strand.py / key_leyla.py):
STRAND_EYE = (-0.0014, -0.0683)     # hanging-eye centre (x, z); eye hole r 0.0022
STRAND_TOP = -0.0731                # eye top (z)
LEYLA_BOW = (-0.0009, -0.0123, 0.0135, 0.016)   # bow centre x, bow bottom z, half width, half height
LEYLA_TOP = -0.0443
CLAMP_GAP = 0.035                   # jaw clearance above a key at rest (the code drops the clamp 0.03)
BULB = (1.5, 2.33, -4.45)
STEEL, PAINT, CHROME, BRASS, BRASS_P = "M_Steel_Dark", "M_Steel_Painted", "M_Chrome", "M_Brass_Aged", "M_Brass_Polished"
INK, CREAM = "M_Lacquer_Black", "M_Enamel_Cream"


def hang(mount, item_x, item_z):
    """World point of an item-space point (x, 0, z) when the item hangs on `mount` (+90° about X)."""
    return (mount[0] + item_x, mount[1] - item_z, mount[2])


def quad(name, pts, mat, uv=None):
    """One quad from 4 G-frame points (CCW seen from the front), optional UVs."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    if uv:
        lay = bm.loops.layers.uv.new("UVMap")
        for lp, t in zip(f.loops, uv):
            lp[lay].uv = t
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    return o


# ====================================================================== shell
def build_shell():
    p = []
    # floor slab + walls as thick boxes (closed shell, hidden outsides)
    p.append(V.gbox("floor", (0.45, -0.12, -5.35), (2.55, 0.0, ZT), "M_Concrete", 0.0))
    p.append(V.gbox("wall_l", (0.45, 0.0, -5.35), (X0, YC, ZT), PAINT, 0.0))
    p.append(V.gbox("wall_r", (X1, 0.0, -5.35), (2.55, YC, ZT), PAINT, 0.0))
    p.append(V.gbox("wall_b", (X0, 0.0, -5.35), (X1, YC, ZB), PAINT, 0.0))
    p.append(V.gbox("ceil", (0.45, YC, -5.35), (2.55, YC + 0.15, ZT), STEEL, 0.0))
    # front wall + tunnel: a 0.16 slab with the bore (its hole side is the tunnel lining)
    fw = V.plate("front", [L.rounded_rect(2.1, 2.5, 0.001, 1, cx=CX, cy=YC / 2), L.circle(BORE, 48, cy=CY, cx=CX)],
                 ZT - ZF, z0=ZF, mat=STEEL, bevel=0.012, bevel_res=1, drop_bottom=False)
    p.append(fw)
    # tunnel ring flange on the vault side
    p.append(V.glathe("tflange", [(BORE + 0.008, ZF + 0.0005), (BORE + 0.008, ZF - 0.02), (BORE + 0.064, ZF - 0.02),
                                  (BORE + 0.075, ZF - 0.012), (BORE + 0.075, ZF + 0.0005)], (CX, CY, 0), (0, 0, 1),
                      48, CHROME, smooth=40.0, cap_bottom=False, cap_top=False))
    # back wall: riveted panels (seam straps + rivets), a rub rail
    for x in (1.2, 1.8):
        p.append(V.gbox("seam", (x - 0.03, 0.0, ZB), (x + 0.03, YC, ZB + 0.006), STEEL, 0.002))
        for i in range(9):
            y = 0.12 + i * 0.28
            if 0.9 < y < 1.40 or 1.48 < y < 2.22:
                continue
            p.append(V.rivet("brv", 0.008, (x, y, ZB + 0.006), segs=6))
    p.append(V.gbox("rubrail", (X0, 0.06, ZB), (X1, 0.16, ZB + 0.012), STEEL, 0.003))
    # ceiling I-beams across the room and rivet rows
    for z in (-4.05, -4.85):
        p.append(V.gbox("beam_w", (X0, YC - 0.012, z - 0.05), (X1, YC, z + 0.05), STEEL, 0.0))
        p.append(V.gbox("beam_web", (X0, YC - 0.11, z - 0.006), (X1, YC - 0.012, z + 0.006), STEEL, 0.0))
        p.append(V.gbox("beam_f", (X0, YC - 0.122, z - 0.05), (X1, YC - 0.11, z + 0.05), STEEL, 0.0))
    # floor: worn rubber runner + brass drain
    p.append(V.gbox("runner", (1.18, 0.0, -5.0), (1.82, 0.006, -4.0), "M_Rubber", 0.003))
    p.append(V.glathe("drain", [(0.07, 0.0), (0.07, 0.004), (0.06, 0.006), (0.0, 0.004)], (0.9, 0.0, -5.0), (0, 1, 0),
                      16, BRASS, smooth=40.0))
    # steps from the bore sill (y 0.49) down to the floor
    for i, (y, z0, z1) in enumerate(((0.33, ZF - 0.13, ZF + 0.002), (0.165, ZF - 0.25, ZF - 0.13))):
        p.append(V.gbox("step", (1.12, 0.0, z0), (1.88, y, z1), STEEL, 0.004))
        p.append(V.gbox("nosing", (1.12, y - 0.012, z0 - 0.006), (1.88, y + 0.003, z0 + 0.03), BRASS, 0.002))
        for j in range(6):                         # tread plate ribs
            zz = z0 + 0.03 + j * (z1 - z0 - 0.04) / 6
            p.append(V.gbox("rib", (1.16, y, zz), (1.84, y + 0.003, zz + 0.008), STEEL, 0.0))
    return V.part("vault_shell", p)


# ====================================================================== deposit boxes
ROWS = [(0.30, 2), (0.30, 2), (0.22, 3), (0.22, 3), (0.18, 4), (0.18, 4), (0.18, 4), (0.18, 4), (0.18, 4)]
BANK_Z = (-5.17, -3.93)
BANK_D = 0.20
OPEN_DOOR = ("r", 4, 1)          # right bank, row 4, column 1: open, its box pulled out


def build_boxes():
    rnd = random.Random(1979)
    p = []
    for side in ("l", "r"):
        sx = 1 if side == "l" else -1
        xw = X0 if side == "l" else X1                  # wall face
        xf = xw + sx * BANK_D                           # bank front face
        z0, z1 = BANK_Z
        lo, hi = (min(xw, xf), max(xw, xf))
        p.append(V.gbox("carcass", (lo, 0.10, z0 - 0.02), (hi, 2.16, z1 + 0.02), PAINT, 0.004))
        xp = xf - sx * 0.02
        p.append(V.gbox("plinth", (min(xw, xp), 0.0, z0 - 0.02), (max(xw, xp), 0.10, z1 + 0.02), STEEL, 0.0))
        p.append(V.gbox("cornice", (min(xw, xf + sx * 0.02), 2.16, z0 - 0.03), (max(xw, xf + sx * 0.02), 2.21, z1 + 0.03),
                        STEEL, 0.006))
        y = 0.10
        for ri, (h, ncol) in enumerate(ROWS):
            w = (z1 - z0) / ncol
            for ci in range(ncol):
                zc = z0 + (ci + 0.5) * w
                yc = y + h / 2
                is_open = (side, ri, ci) == (OPEN_DOOR[0], OPEN_DOOR[1], OPEN_DOOR[2])
                p += deposit_door(sx, xf, zc, yc, w - 0.012, h - 0.012, rnd, is_open)
            y += h
    return V.part("vault_boxes", p)


def deposit_door(sx, xf, zc, yc, w, h, rnd, is_open):
    """One box door on a bank face at x = xf (sx = +1 faces +X). Built flat in the bank's (z, y) plane."""
    out = []
    t = 0.012
    dd = V.gbox("ddoor", (0.0, -h / 2, -w / 2), (t, h / 2, w / 2), STEEL, 0.003)
    L.drop_faces(dd, lambda c, n: c.x < 0.004 and n.x < -0.3)        # hidden back against the carcass
    door = [dd]
    # brass label holder + card (M_Decal_BoxLabels atlas cell)
    lw, lh = min(0.085, w * 0.5), 0.026
    ly = h / 2 - 0.03
    door.append(quad("lholder", [(t + 0.0012, ly - lh / 2 - 0.004, lw / 2 + 0.004),
                                 (t + 0.0012, ly - lh / 2 - 0.004, -lw / 2 - 0.004),
                                 (t + 0.0012, ly + lh / 2 + 0.004, -lw / 2 - 0.004),
                                 (t + 0.0012, ly + lh / 2 + 0.004, lw / 2 + 0.004)], BRASS))
    cu, cv = rnd.randrange(4), rnd.randrange(8)
    door.append(quad("label", [(t + 0.0024, ly - lh / 2, lw / 2), (t + 0.0024, ly - lh / 2, -lw / 2),
                               (t + 0.0024, ly + lh / 2, -lw / 2), (t + 0.0024, ly + lh / 2, lw / 2)],
                     "M_Decal_BoxLabels", uv=[(cu / 4, cv / 8), ((cu + 1) / 4, cv / 8), ((cu + 1) / 4, (cv + 1) / 8),
                                              (cu / 4, (cv + 1) / 8)]))
    # two key escutcheons (guard key + renter key)
    for dz in (-0.022, 0.022):
        esc = L.flat_shape("esc", [L.circle(0.0105, 6, phase=math.pi / 6)], mat=BRASS_P)
        esc.data.transform(Matrix.Translation((t + 0.0013, -0.012, dz)) @ V.axis_rot((1, 0, 0)))
        kh = quad("khole", [(t + 0.0026, -0.0175, dz - 0.0018), (t + 0.0026, -0.0175, dz + 0.0018),
                            (t + 0.0026, -0.0065, dz + 0.0018), (t + 0.0026, -0.0065, dz - 0.0018)], INK)
        door += [esc, kh]
    if is_open:
        # hinge on the edge toward the vault entrance (world +z), swung ~100° out into the room
        hz = w / 2 if sx > 0 else -w / 2
        ang = -100.0 if sx > 0 else 100.0
        for o in door:
            o.data.transform(Matrix.Translation((0, 0, hz)) @ Matrix.Rotation(math.radians(ang), 4, "Y")
                             @ Matrix.Translation((0, 0, -hz)))
        # the box pulled half out: a long steel tray with papers
        box = [V.gbox("dbox", (-0.17, -h / 2 + 0.01, -w / 2 + 0.01), (0.10, h / 2 - 0.04, w / 2 - 0.01), STEEL, 0.003),
               V.gbox("dpaper", (-0.15, h / 2 - 0.045, -w / 2 + 0.02), (0.08, h / 2 - 0.038, w / 2 - 0.02),
                      "M_Paper", 0.001),
               V.gbox("dpull", (0.10, -0.02, -0.03), (0.112, 0.0, 0.03), BRASS_P, 0.002)]
        door += box
    for o in door:            # right bank: turned 180° about Y (labels still read left -> right)
        mat = Matrix.Translation((xf, yc, zc))
        if sx < 0:
            mat = mat @ Matrix.Rotation(math.pi, 4, "Y")
        o.data.transform(mat)
    out += door
    return out


# ====================================================================== table + field kit
def build_table():
    x0, x1, z0, z1 = TABLE
    p = [V.gbox("top", (x0, TABLE_Y - 0.025, z0), (x1, TABLE_Y, z1), PAINT, 0.006, 2),
         V.gbox("apron", (x0 + 0.03, TABLE_Y - 0.09, z0 + 0.03), (x1 - 0.03, TABLE_Y - 0.025, z1 - 0.03), STEEL, 0.003),
         V.gbox("shelf", (x0 + 0.04, 0.16, z0 + 0.04), (x1 - 0.04, 0.18, z1 - 0.04), STEEL, 0.003)]
    for xx in (x0 + 0.035, x1 - 0.035):
        for zz in (z0 + 0.035, z1 - 0.035):
            p.append(V.gbox("leg", (xx - 0.016, 0.0, zz - 0.016), (xx + 0.016, TABLE_Y - 0.025, zz + 0.016), STEEL, 0.003))
            p.append(V.gbox("foot", (xx - 0.022, 0.0, zz - 0.022), (xx + 0.022, 0.012, zz + 0.022), "M_Rubber", 0.003))
    # a box from the open bank lying on the shelf below
    p.append(V.gbox("shelfbox", (1.2, 0.18, z0 + 0.06), (1.62, 0.29, z1 - 0.09), "M_Cardboard", 0.004))
    return V.part("vault_table", p)


def build_kit():
    p = []
    ty = TABLE_Y
    # --- canvas satchel standing upright, flap toward the room
    sx0, sx1, sz = 1.60, 1.88, -4.44
    body = V.gbox("satchel", (sx0, ty, sz - 0.05), (sx1, ty + 0.21, sz + 0.05), "M_Linen", 0.025, 3)
    gusset = V.gbox("gusset", (sx0 + 0.012, ty + 0.17, sz - 0.056), (sx1 - 0.012, ty + 0.215, sz + 0.048), "M_Linen", 0.02, 2)
    flap = V.gbox("flap", (sx0 + 0.004, ty + 0.085, sz + 0.05), (sx1 - 0.004, ty + 0.218, sz + 0.062), "M_Linen", 0.008, 2)
    p += [body, gusset, flap]
    for xx in (sx0 + 0.07, sx1 - 0.07):
        p.append(V.gbox("strap", (xx - 0.013, ty + 0.06, sz + 0.061), (xx + 0.013, ty + 0.22, sz + 0.066), "M_Leather",
                        0.002))
        p.append(V.gbox("buckle", (xx - 0.016, ty + 0.085, sz + 0.064), (xx + 0.016, ty + 0.108, sz + 0.069), BRASS_P,
                        0.002))
    # shoulder strap: loops from the satchel's side over the table edge
    p.append(V.tube("sstrap", [(sx1, ty + 0.17, sz), (sx1 + 0.05, ty + 0.12, sz + 0.03), (1.97, ty + 0.012, sz + 0.06),
                               (1.995, ty - 0.01, sz + 0.09), (2.012, ty - 0.12, sz + 0.11), (2.0, ty - 0.22, sz + 0.05)],
                    0.007, sides=6, mat="M_Leather", fillet=0.03))
    # --- photograph propped against the satchel
    ph_c = Vector((1.76, ty + 0.067, sz + 0.078))
    tilt = math.radians(-14)
    pw, phh = 0.09, 0.12
    frame = V.gbox("photo_card", (-pw / 2 - 0.006, -phh / 2 - 0.006, -0.0008), (pw / 2 + 0.006, phh / 2 + 0.012, 0.0),
                   "M_Paper", 0.0)
    img = quad("photo", [(-pw / 2, -phh / 2, 0.0003), (pw / 2, -phh / 2, 0.0003), (pw / 2, phh / 2, 0.0003),
                         (-pw / 2, phh / 2, 0.0003)], "M_Decal_Photos", uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    for o in (frame, img):
        o.data.transform(Matrix.Translation(ph_c) @ Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(math.radians(4), 4, "Z"))
    p += [frame, img]
    # --- thermos (enamel body, chrome cup) standing at the back right
    tx, tz = 1.935, -4.52
    p.append(V.glathe("thermos", [(0.0, 0.0), (0.04, 0.0), (0.043, 0.006), (0.043, 0.205), (0.037, 0.225),
                                  (0.036, 0.232)], (tx, ty, tz), (0, 1, 0), 16, "M_Enamel_Green", smooth=50.0,
                      cap_top=False))
    p.append(V.glathe("cup", [(0.038, 0.226), (0.045, 0.228), (0.045, 0.29), (0.04, 0.297), (0.0, 0.297)],
                      (tx, ty, tz), (0, 1, 0), 16, CHROME, smooth=50.0, cap_bottom=False))
    # --- torch lying on the table
    a = math.radians(-28)
    d = (math.cos(a), 0.0, -math.sin(a))
    tb = (1.40, ty + 0.0185, -4.205)
    p.append(V.glathe("torch", [(0.0, 0.0), (0.016, 0.0), (0.0175, 0.004), (0.0175, 0.13), (0.026, 0.155),
                                (0.026, 0.19), (0.022, 0.192)], tb, d, 12, STEEL, smooth=50.0, cap_top=False,
                      band_mats=[CHROME, CHROME, None, CHROME, CHROME, CHROME]))
    p.append(V.glathe("torch_lens", [(0.022, 0.189), (0.0, 0.189)], tb, d, 12, "M_Glass", smooth=50.0, cap_bottom=False))
    p.append(V.gbox("torch_sw", (-0.008, 0.0, 0.0), (0.008, 0.006, 0.012), "M_Rubber", 0.002))
    sw = p[-1]
    sw.data.transform(Matrix.Translation((tb[0] + 0.09 * d[0], tb[1] + 0.017, tb[2] + 0.09 * d[2]))
                      @ Matrix.Rotation(-a, 4, "Y"))
    # --- folded map (four panels, zig-zag) with her route in red
    mx0, mz0, pw_ = 1.33, -4.52, 0.075
    panels = []

    def map_y(x):                       # zig-zag fold height at x (panel i rises / falls 6 mm)
        i = min(3, max(0, int((x - mx0) / pw_)))
        t = (x - (mx0 + i * pw_)) / pw_
        return ty + 0.002 + 0.006 * ((1 - t) if i % 2 else t)
    for i in range(4):
        x_a, x_b = mx0 + i * pw_, mx0 + (i + 1) * pw_
        panels.append(quad("map", [(x_a, map_y(x_a + 1e-6), mz0 + 0.21), (x_b, map_y(x_b - 1e-6), mz0 + 0.21),
                                   (x_b, map_y(x_b - 1e-6), mz0), (x_a, map_y(x_a + 1e-6), mz0)], "M_Paper"))
    p += panels
    route = [(1.345, -4.33), (1.39, -4.37), (1.44, -4.36), (1.49, -4.42), (1.55, -4.40), (1.60, -4.47)]
    pts = [route[0]]
    for (xa, za), (xb, zb) in zip(route[:-1], route[1:]):
        for k in range(1, 4):           # split at the folds
            xf_ = mx0 + k * pw_
            if xa < xf_ < xb:
                pts.append((xf_, za + (zb - za) * (xf_ - xa) / (xb - xa)))
        pts.append((xb, zb))
    for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
        dx, dz = xb - xa, zb - za
        n = Vector((-dz, 0, dx)).normalized() * 0.0022
        ya, yb = map_y(xa + 1e-4) + 0.0004, map_y(xb - 1e-4) + 0.0004
        p.append(quad("route", [(xa - n.x, ya, za - n.z), (xb - n.x, yb, zb - n.z), (xb + n.x, yb, zb + n.z),
                                (xa + n.x, ya, za + n.z)], "M_Enamel_Crimson"))
    p.append(V.glathe("route_x", [(0.008, 0.0), (0.0, 0.0)], (1.60, map_y(1.60) + 0.0005, -4.47), (0, 1, 0), 8,
                      "M_Enamel_Crimson"))
    # --- notebook + pencil
    nb = (1.52, -4.30)
    p.append(V.gbox("nb_cover", (nb[0] - 0.068, ty, nb[1] - 0.095), (nb[0] + 0.068, ty + 0.003, nb[1] + 0.095),
                    "M_Leather", 0.0015))
    p.append(V.gbox("nb_pages", (nb[0] - 0.064, ty + 0.003, nb[1] - 0.092), (nb[0] + 0.066, ty + 0.017, nb[1] + 0.092),
                    "M_Paper", 0.001))
    p.append(V.gbox("nb_cover2", (nb[0] - 0.068, ty + 0.017, nb[1] - 0.095), (nb[0] + 0.068, ty + 0.020, nb[1] + 0.095),
                    "M_Leather", 0.0015))
    p.append(V.gbox("nb_band", (nb[0] + 0.045, ty - 0.001, nb[1] - 0.096), (nb[0] + 0.051, ty + 0.0212, nb[1] + 0.096),
                    "M_Rubber", 0.0005))
    pen = V.glathe("pencil", [(0.0, 0.0), (0.0035, 0.012), (0.0035, 0.15), (0.0, 0.152)], (0, 0, 0), (1, 0, 0), 6,
                   "M_Enamel_Amber", smooth=20.0, band_mats=["M_Wood_Walnut", None, "M_Rubber"])
    pen.data.transform(Matrix.Translation((nb[0] - 0.07, ty + 0.0235, nb[1] + 0.05)) @ Matrix.Rotation(math.radians(-18), 4, "Y"))
    p.append(pen)
    return V.part("field_kit", p)


# ====================================================================== projector
def projector_frame():
    """Lens position and aim (lens front L0, rotation R: local +Z = beam to the screen centre, +Y up)."""
    target = Vector((SCREEN_C[0], SCREEN_C[1], SCREEN_Z))
    L0 = Vector((1.20, 1.05, -4.37))
    for _ in range(4):
        R = D.axis_matrix(target - L0, up_hint=(0, 1, 0))
        rear_bottom = R @ Vector((0.0, -0.062, -0.335))
        L0.y = TABLE_Y + 0.004 - rear_bottom.y
    return L0, R


def build_projector():
    L0, R = projector_frame()
    body = []
    glow = []
    # lens barrel (bakelite with a chrome front ring), front glass = glow
    body.append(L.lathe2("lens", [(0.024, -0.095), (0.027, -0.09), (0.027, -0.02), (0.029, -0.016), (0.029, 0.0),
                                  (0.022, 0.0), (0.021, -0.004)], segments=16, mat="M_Bakelite", cap_bottom=False,
                         cap_top=False, band_mats=[None, None, CHROME, CHROME, CHROME, CHROME]))
    g = L.lathe2("lens_glass", [(0.021, -0.004), (0.0, -0.004)], segments=16, mat="M_Glass", cap_bottom=False,
                 cap_top=False)
    glow.append(g)
    # die-cast body + rounded lamp house on top
    body.append(V.gbox("pbody", (-0.066, -0.062, -0.335), (0.066, 0.085, -0.09), "M_Steel_Cream", 0.014, 2))
    body.append(V.gbox("plamp", (-0.05, 0.085, -0.27), (0.05, 0.125, -0.15), STEEL, 0.012, 2))
    for i in range(4):          # lamp-house vents (glow)
        z = -0.255 + i * 0.027
        glow.append(quad("vent", [(-0.035, 0.1252, z), (0.035, 0.1252, z), (0.035, 0.1252, z + 0.012),
                                  (-0.035, 0.1252, z + 0.012)], "M_Glass"))
    # reel arms + reels on the -X side (toward the room)
    for (zh, yh) in ((-0.05, 0.215), (-0.375, 0.215)):
        body.append(V.tube("arm", [(-0.068, 0.07, -0.14 if zh > -0.2 else -0.29), (-0.072, yh, zh)], 0.007, sides=6,
                           mat=CHROME))
        hub = Vector((-0.085, yh, zh))
        holes = [L.kidney(0.022, 0.064, math.radians(a0 + 12), math.radians(a0 + 108), 5) for a0 in (0, 120, 240)]
        outer = L.curve_solid("flange", [L.circle(0.078, 28)] + holes, 0.0012, bevel=0.0, mat=CHROME)
        outer.data.transform(Matrix.Translation((0, 0, -0.0107)))
        fl = [outer,
              L.lathe2("flange", [(0.0, 0.0095), (0.078, 0.0095), (0.078, 0.0105), (0.0, 0.0105)], segments=24, mat=STEEL),
              L.lathe2("hub", [(0.0, -0.012), (0.012, -0.012), (0.012, 0.012), (0.0, 0.012)], segments=10, mat=CHROME),
              L.lathe2("film", [(0.0, -0.0095), (0.06 if zh > -0.2 else 0.035, -0.0095),
                                (0.06 if zh > -0.2 else 0.035, 0.0095), (0.0, 0.0095)], segments=24, mat="M_Film")]
        for o in fl:
            o.data.transform(Matrix.Translation(hub) @ V.axis_rot((1, 0, 0)))
        body += fl
    # film running from the front reel into the gate
    body.append(quad("filmstrip", [(-0.076, 0.15, -0.055), (-0.076, 0.15, -0.045), (-0.068, 0.0, -0.10),
                                   (-0.068, 0.0, -0.11)], "M_Film"))
    # controls: knob + switch on the -X side
    body.append(V.glathe("pknob", [(0.0, 0.0), (0.014, 0.0), (0.014, 0.012), (0.0, 0.014)], (-0.066, 0.0, -0.25),
                         (-1, 0, 0), 12, "M_Bakelite", smooth=50.0))
    body.append(V.gbox("pswitch", (-0.074, -0.03, -0.19), (-0.066, -0.015, -0.17), CHROME, 0.002))
    # mains cable from the back, down to the table
    body.append(V.tube("cable", [(0.0, -0.02, -0.335), (0.0, -0.03, -0.38), (0.02, -0.12, -0.40)], 0.004, sides=6,
                       mat="M_Rubber", fillet=0.02))
    M_ = Matrix.Translation(L0) @ R
    for o in body + glow:
        o.data.transform(M_)
    # stand: a cast base on the table and a tilt post under the lens end (world, vertical)
    front_bottom = M_ @ Vector((0.0, -0.062, -0.12))
    rear_bottom = M_ @ Vector((0.0, -0.062, -0.32))
    stand = [V.gbox("pbase", (front_bottom.x - 0.06, TABLE_Y, front_bottom.z - 0.05),
                    (front_bottom.x + 0.06, TABLE_Y + 0.014, front_bottom.z + 0.05), STEEL, 0.004),
             V.gcyl("ppost", 0.009, TABLE_Y + 0.014, front_bottom.y + 0.01, base=(front_bottom.x, 0.0, front_bottom.z),
                    axis=(0, 1, 0), segments=8, mat=CHROME),
             V.gbox("pfoot", (rear_bottom.x - 0.06, TABLE_Y, rear_bottom.z - 0.012),
                    (rear_bottom.x + 0.06, rear_bottom.y + 0.006, rear_bottom.z + 0.012), "M_Rubber", 0.003)]
    proj = V.part("vault_projector", body + stand)
    glow_o = V.part("vault_lamp_glow", glow, pivot=tuple(L0))
    e = V.empty("vault_lens_origin", (0, 0, 0))
    e.matrix_world = Matrix.Translation(L0) @ R
    return proj, glow_o, e


# ====================================================================== screen, cradle, bulb
def build_screen():
    cx, cy = SCREEN_C
    w, h, z = SCREEN_W, SCREEN_H, SCREEN_Z
    scr = quad("vault_reel_screen", [(cx - w / 2, cy - h / 2, z), (cx + w / 2, cy - h / 2, z), (cx + w / 2, cy + h / 2, z),
                                     (cx - w / 2, cy + h / 2, z)], "M_Screen")
    scr = V.part("vault_reel_screen", [scr], pivot=(cx, cy, z))
    p = []
    top = cy + h / 2
    p.append(quad("scr_top", [(cx - w / 2, top, z), (cx + w / 2, top, z), (cx + w / 2, top + 0.02, z - 0.004),
                              (cx - w / 2, top + 0.02, z - 0.004)], "M_Screen"))
    p.append(quad("scr_bot", [(cx - w / 2, cy - h / 2 - 0.02, z), (cx + w / 2, cy - h / 2 - 0.02, z),
                              (cx + w / 2, cy - h / 2, z), (cx - w / 2, cy - h / 2, z)], "M_Screen"))
    p.append(V.gcyl("roller", 0.034, cx - 0.51, cx + 0.51, base=(0, top + 0.05, z - 0.006), axis=(1, 0, 0), segments=16,
                    mat=PAINT, chamfer=0.004))
    for sx in (-1, 1):
        p.append(V.glathe("rcap", [(0.036, 0.0), (0.038, 0.004), (0.038, 0.016), (0.0, 0.018)],
                          (cx + sx * 0.51, top + 0.05, z - 0.006), (sx, 0, 0), 16, BRASS, smooth=50.0, cap_bottom=False))
        p.append(V.gbox("rbracket", (cx + sx * 0.53 - 0.012, top + 0.0, ZB), (cx + sx * 0.53 + 0.012, top + 0.09, z - 0.004),
                        STEEL, 0.003))
    p.append(V.gcyl("batten", 0.011, cx - w / 2 - 0.02, cx + w / 2 + 0.02, base=(0, cy - h / 2 - 0.025, z + 0.002),
                    axis=(1, 0, 0), segments=10, mat="M_Wood_Walnut", chamfer=0.002))
    p.append(V.tube("cord", [(cx, cy - h / 2 - 0.035, z + 0.004), (cx, cy - h / 2 - 0.10, z + 0.006)], 0.0018, sides=5,
                    mat="M_Fabric"))
    ring = M.torus("pullring", 0.016, 0.003, major_seg=16, minor_seg=5, mat=BRASS_P)
    ring.data.transform(Matrix.Translation((cx, cy - h / 2 - 0.118, z + 0.006)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    V.A.hint(ring, 70.0)
    p.append(ring)
    return scr, V.part("screen_roller", p)


def build_cradle():
    cx, cy = 1.5, 1.16
    W, H = 0.54, 0.38
    iw, ih = 0.47, 0.28
    icy = 1.16
    p = []
    # brass frame ring (z -5.20 .. -5.10) with an inlaid line, velvet cushion inside
    p.append(V.plate("cframe", [L.rounded_rect(W, H, 0.02, 3, cx=cx, cy=cy), L.rounded_rect(iw, ih, 0.012, 3, cx=cx, cy=icy)],
                     0.10, z0=ZB, mat=BRASS, bevel=0.004, bevel_res=1))
    p.append(V.flat("cline", L.outline_ring(W - 0.022, H - 0.022, 0.014, 0.002, 3), -5.0998, (cx, cy), INK))
    p.append(V.plate("velvet", [L.rounded_rect(iw + 0.004, ih + 0.004, 0.012, 3, cx=cx, cy=icy)], 0.07 + 0.002, z0=ZB,
                     mat="M_Velvet", bevel=0.006, bevel_res=1))
    vz = ZB + 0.072                                     # velvet surface z = -5.128
    p.append(V.gbox("divider", (cx - 0.006, icy - ih / 2, vz - 0.002), (cx + 0.006, icy + ih / 2, -5.104), BRASS, 0.002))
    # Strand's key: a brass hook peg through its hanging eye
    ms = MOUNTS["strand"]
    ex, ey, _ = hang(ms, STRAND_EYE[0], STRAND_EYE[1])
    peg_y = ey + 0.0006
    p.append(V.glathe("peg", [(0.0016, 0.0), (0.0016, ms[2] + 0.0075 - vz), (0.0034, ms[2] + 0.0085 - vz),
                              (0.0034, ms[2] + 0.0105 - vz), (0.0, ms[2] + 0.011 - vz)], (ex, peg_y, vz), (0, 0, 1), 8,
                      BRASS_P, smooth=50.0))
    p.append(V.glathe("pegros", [(0.007, 0.0), (0.006, 0.002), (0.0, 0.0025)], (ex, peg_y, vz), (0, 0, 1), 10, BRASS,
                      smooth=50.0, cap_bottom=False))
    # Leyla's key: two rest pins under the shoulders of the oval bow
    ml = MOUNTS["leyla"]
    bx, bz, rx, ry = LEYLA_BOW
    for s in (-1, 1):
        dx = 0.0095
        lift = ry * (1 - math.sqrt(max(0.0, 1 - (dx / rx) ** 2)))
        top = ml[1] - bz + lift
        px = ml[0] + bx + s * dx
        p.append(V.glathe("rest", [(0.0018, 0.0), (0.0018, ml[2] + 0.006 - vz), (0.0028, ml[2] + 0.0075 - vz),
                                   (0.0, ml[2] + 0.008 - vz)], (px, top - 0.0018, vz), (0, 0, 1), 8, BRASS_P, smooth=50.0))
    # clamp guides (static): two slim rails per key under the top rail
    for k, (mx, my, _) in MOUNTS.items():
        top_k = hang(MOUNTS[k], 0, STRAND_TOP if k == "strand" else LEYLA_TOP)[1]
        y0 = top_k + CLAMP_GAP - 0.004
        for s in (-1, 1):
            p.append(V.gbox("cguide", (mx + s * 0.024 - 0.003, y0, vz - 0.001), (mx + s * 0.024 + 0.003, icy + ih / 2,
                                                                                vz + 0.016), BRASS_P, 0.001))
    # engraved mark / sign on the bottom rail under each key
    ry0 = cy - H / 2 + 0.025
    zt = -5.0999
    sx_, _, _ = MOUNTS["strand"]
    p.append(V.flat("emark", L.circle_line(0.0125, 0.003, 20), zt, (sx_, ry0), INK))
    p.append(V.flat("emark2", [L.rounded_rect(0.0028, 0.036, 0.0005, 1)], zt, (sx_, ry0), INK))
    lx_, _, _ = MOUNTS["leyla"]
    R_, r_, d_ = 0.0155, 0.013, 0.0068
    xi = (R_ * R_ - r_ * r_ + d_ * d_) / (2 * d_)
    a0 = math.atan2(math.sqrt(R_ * R_ - xi * xi), xi)
    b0 = math.atan2(math.sqrt(R_ * R_ - xi * xi), xi - d_)
    outer = [(R_ * math.cos(a0 + (2 * math.pi - 2 * a0) * i / 14), R_ * math.sin(a0 + (2 * math.pi - 2 * a0) * i / 14))
             for i in range(15)]
    inner = [(d_ + r_ * math.cos(-b0 - (2 * math.pi - 2 * b0) * i / 10), r_ * math.sin(-b0 - (2 * math.pi - 2 * b0) * i / 10))
             for i in range(1, 10)]
    p.append(V.flat("esign", [outer + inner], zt, (lx_ - 0.003, ry0), INK))
    for dy in (-0.0068, 0.0, 0.0068):
        p.append(V.flat("edot", [L.circle(0.0021, 8)], zt, (lx_ + 0.005, ry0 + dy), INK))
    # four corner screws
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(V.rivet("cscr", 0.005, (cx + sx * (W / 2 - 0.016), cy + sy * (H / 2 - 0.018), -5.10), mat=BRASS_P))
    cradle = V.part("key_cradle", p)
    # sliding clamps (own objects): a jaw block with a V notch + a plunger rod into the top rail
    clamps = []
    for k, side in (("strand", "left"), ("leyla", "right")):
        mx = MOUNTS[k][0]
        top_k = hang(MOUNTS[k], 0, STRAND_TOP if k == "strand" else LEYLA_TOP)[1]
        jb = top_k + CLAMP_GAP                         # jaw bottom at rest
        jc = (mx, jb + 0.007, vz + 0.0095)
        jaw = V.plate("jaw", [[(-0.019, -0.007), (-0.004, -0.007), (0.0, -0.002), (0.004, -0.007), (0.019, -0.007),
                               (0.019, 0.007), (-0.019, 0.007)]], 0.017, z0=vz + 0.001, mat=BRASS_P, bevel=0.0015,
                      loc=(mx, jc[1], 0), drop_bottom=False)
        rod = V.gcyl("rod", 0.003, jc[1] + 0.007, jc[1] + 0.06, base=(mx, 0.0, vz + 0.0095), axis=(0, 1, 0), segments=8,
                     mat=BRASS_P)
        knob = V.glathe("cknob", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.006), (0.0, 0.007)], (mx, jc[1], vz + 0.018),
                        (0, 0, 1), 10, BRASS, smooth=50.0)
        clamps.append(V.part(f"cradle_clamp_{side}", [jaw, rod, knob], pivot=jc))
    mounts = [V.empty(f"key_{k}_mount", MOUNTS[k], rot_deg=(90.0, 0.0, 0.0)) for k in ("strand", "leyla")]
    return cradle, clamps, mounts


def build_bulb():
    x, y, z = BULB
    p = [V.glathe("canopy", [(0.0, -0.04), (0.045, -0.035), (0.065, -0.01), (0.065, 0.0)], (x, YC, z), (0, 1, 0), 16,
                  STEEL, smooth=40.0, cap_top=False),
         V.gcyl("stem", 0.011, YC - 0.10, YC - 0.035, base=(x, 0.0, z), axis=(0, 1, 0), segments=8, mat=STEEL),
         V.glathe("holder", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.04), (0.02, 0.046), (0.0, 0.047)],
                  (x, YC - 0.147, z), (0, 1, 0), 12, "M_Bakelite", smooth=40.0)]
    # wire cage: 4 bent meridians + a ring
    for i in range(4):
        a = math.radians(45 + 90 * i)
        c, s = math.cos(a), math.sin(a)
        pts = []
        for j in range(7):
            t = math.radians(-80 + j * 160 / 6)
            r = 0.05 * math.cos(t) + 0.004
            pts.append((x + c * r, y + 0.006 + 0.058 * math.sin(t), z + s * r))
        p.append(V.tube("cage", pts, 0.0016, sides=4, mat=STEEL))
    ring = M.torus("cring", 0.054, 0.0022, major_seg=20, minor_seg=4, mat=STEEL)
    ring.data.transform(Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    V.A.hint(ring, 70.0)
    p.append(ring)
    fixture = V.part("bulb_fixture", p)
    bulb = V.glathe("vault_bulb", [(0.0, -0.045), (0.022, -0.04), (0.036, -0.018), (0.037, 0.004), (0.026, 0.03),
                                   (0.013, 0.045), (0.012, 0.052)], (x, y, z), (0, 1, 0), 14, "M_Emissive_Warm",
                    smooth=70.0, cap_top=False)
    bulb = V.part("vault_bulb", [bulb], pivot=BULB)
    light = V.empty("vault_light", BULB)
    return fixture, bulb, light


def build():
    M.reset_scene()
    V.ensure_materials()
    shell = build_shell()
    boxes = build_boxes()
    table = build_table()
    kit = build_kit()
    proj, glow, lens = build_projector()
    scr, roller = build_screen()
    cradle, clamps, mounts = build_cradle()
    fixture, bulb, light = build_bulb()
    V.to_blender()
    V.finalize_all()
    V.uv_square(scr, SCREEN_C, (SCREEN_W / 2, SCREEN_H / 2))
    return dict(shell=shell, boxes=boxes, table=table, kit=kit, proj=proj, glow=glow, lens=lens, screen=scr,
                roller=roller, cradle=cradle, clamps=clamps, mounts=mounts, fixture=fixture, bulb=bulb, light=light)


def verify(path):
    req = ["vault_projector", "vault_lens_origin", "vault_lamp_glow", "vault_reel_screen", "key_strand_mount",
           "key_leyla_mount", "cradle_clamp_left", "cradle_clamp_right", "vault_bulb", "vault_light"]
    L0, R = projector_frame()
    expect = {"key_strand_mount": MOUNTS["strand"], "key_leyla_mount": MOUNTS["leyla"],
              "vault_reel_screen": (SCREEN_C[0], SCREEN_C[1], SCREEN_Z), "vault_light": BULB,
              "vault_lens_origin": tuple(L0)}
    ident = ["vault_projector", "vault_lamp_glow", "vault_reel_screen", "cradle_clamp_left", "cradle_clamp_right",
             "vault_bulb"]
    errs = V.verify_glb(path, required=req, identity=ident, budget=BUDGET, expect=expect, show=req,
                        rot_expect={"key_strand_mount": (90, 0, 0), "key_leyla_mount": (90, 0, 0)})
    V.check_names(path)
    scr = bpy.data.objects["vault_reel_screen"]
    us = [d.uv[0] for d in scr.data.uv_layers.active.data]
    vs = [d.uv[1] for d in scr.data.uv_layers.active.data]
    print(f"{V.TAG} vault_reel_screen UV u {min(us):.3f}..{max(us):.3f} v {min(vs):.3f}..{max(vs):.3f}")
    fwd = R @ Vector((0, 0, 1))
    print(f"{V.TAG} projector lens {tuple(round(c, 3) for c in L0)} beam dir {tuple(round(c, 3) for c in fwd)} "
          f"pitch {math.degrees(math.asin(fwd.y)):.1f}°")
    lo, hi = V.mesh_bounds_godot([o for o in bpy.context.scene.objects if o.type == "MESH"])
    print(f"{V.TAG} model bounds (Godot) min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
def key_or_proxy(item, mount, length):
    path = V.model_glb(item)
    if os.path.exists(path):
        return V.attach(path, mount)
    o = M.box("qa_proxy_" + item, (0.03, length, 0.006), mat=BRASS)
    o.parent = mount
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = Matrix.Identity(4)
    return o


def reel_image():
    for f in ("vault_reel.jpg", "film_frame_2.jpg"):
        path = os.path.join(V.DECALS_CH2, f)
        if os.path.exists(path):
            return bpy.data.images.load(path, check_existing=True), f
    # placeholder: warm grey vignette (the decal builder has not delivered vault_reel.jpg yet)
    import numpy as np
    n = 256
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    v = 0.25 + 0.55 * np.exp(-(((xx - 0.5) / 0.35) ** 2 + ((yy - 0.55) / 0.3) ** 2))
    rgba = np.stack([v, v * 0.95, v * 0.86, np.ones_like(v)], -1)
    img = bpy.data.images.new("qa_reel_placeholder", n, n)
    img.pixels[:] = rgba.ravel()
    return img, None


def qa(parts, args):
    V.qa_begin(bounces=8)
    has_room = V.qa_room()
    V.qa_neighbours([("vault_door", (1.5, 0, -3.5), 0.0)])
    print(f"{V.TAG} QA room: {'room_archive.glb' if has_room else 'proxy shell'}")
    keys = [key_or_proxy("key_strand", parts["mounts"][0], 0.14), key_or_proxy("key_leyla", parts["mounts"][1], 0.11)]
    door = bpy.data.objects.get("qa_IA_vault_door")
    if door is not None:                      # open the imported door (-95° about its local Y)
        V.pose_rot(door, "y", -95.0)
        for k in range(8):
            b = bpy.data.objects.get(f"qa_bolt_{k}")
            if b:
                a = math.radians(45 * k)
                V.pose_slide(b, (-0.08 * math.cos(a), -0.08 * math.sin(a), 0.0))
    img, src = reel_image()
    print(f"{V.TAG} reel image: {src or 'placeholder'}")

    def want(tag):
        return "--shots" not in args or tag in args[args.index("--shots") + 1].split(",")

    def lights(reel=False):
        V.qa_clear_lights()
        V.qa_room_lights(150.0)
        V.qa_light("vault", "POINT", (1.5, 1.6, -4.4), 45.0, "CFF6FF", radius=0.25)
        V.qa_light("bulb", "POINT", BULB, 18.0, "FFE2B0", radius=0.04)
        if reel:
            V.qa_light("beam", "SPOT", tuple(projector_frame()[0]), 25.0, "FFF1D6", radius=0.01,
                       target=(SCREEN_C[0], SCREEN_C[1], SCREEN_Z), spot_deg=40)

    bulb_on = V.glow_material("QA_BulbOn", "FFE2B0", 12.0, base="FFE2B0")
    V.override_material(parts["bulb"], bulb_on)
    # 1 vault_inside view (finale), keys on the cradle, reel playing
    if want("1"):
        V.override_material(parts["screen"], V.emissive_image_material("qa_reel", img, 1.0, alpha_from_image=False))
        V.override_material(parts["glow"], V.glow_material("QA_LampOn", "FFF1D6", 8.0, base="FFF1D6"))
        lights(reel=True)
        V.shoot(NAME, (1.5, 1.55, -3.0), (1.5, 1.3, -5.2), vfov=56)
    # 2 vault_mouth view (through the open door)
    if want("2"):
        lights(reel=True)
        V.shoot(NAME + "_2", (1.5, 1.6, -1.6), (1.5, 1.4, -4.6), vfov=58)
    # 3 cradle close-up: Leyla's key taken, the left clamp dropped onto Strand's key
    if want("3"):
        lights(reel=True)
        V.pose_slide(parts["clamps"][0], (0.0, -0.03, 0.0))
        for o in [keys[1]] + list(keys[1].children_recursive if keys[1] else []):
            o.hide_render = True
        V.qa_fill((1.5, 1.35, -4.55), 6.0)
        V.shoot(NAME + "_3", (1.53, 1.30, -4.62), (1.5, 1.17, -5.15), vfov=40)
    # 4 the field kit on the table
    if want("4"):
        lights(reel=True)
        V.qa_fill((1.9, 1.35, -3.9), 6.0)
        V.shoot(NAME + "_4", (1.95, 1.32, -3.85), (1.55, 0.82, -4.40), vfov=44)


def main():
    args = M.main_guard()
    parts = build()
    V.report(NAME)
    path = V.export(NAME)
    errs = verify(path)
    if errs:
        print(f"{V.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
