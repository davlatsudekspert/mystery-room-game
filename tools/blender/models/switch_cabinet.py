"""switch_cabinet.glb — the switch room's three trapped-key isolator cabinets (×3: cabinet_0..2 = I, II, III).
Contract: docs/models/ch3.md §5 switch_cabinet (+ §1.3 lock / window points, §2 switch_room / cabinet_n views);
keys: docs/models/ch3_g.md; results: docs/models/ch3_c.md.

Wall-mounted on the south wall, yaw 180, at (-7.4 / -8.3 / -9.2, 0, 4.0). Origin = the wall plane at floor level,
front +Z. Body 0.70 w x 1.90 h x 0.45 d on a 0.10 plinth; front face z = 0.45. From the front: the lock ledge and
the key window on the left, the isolator on the right.

  switch_cabinet (static)   painted steel cabinet: recessed plinth, carcass, front door with a pressed border and
                            hinges, side louvres, top cap with cable glands; the lock ledge (x -0.26..0.02,
                            y 1.10..1.13, to z = 0.58) with its gussets and the brass lock housing under it; the key
                            box with its brass bezel, flap hinge and the hanging pin; the isolator's brass dial plate
                            (painted IEC marks I at 12, O at 9) and boss; the lamp bezel. (M_Steel_Painted,
                            M_Brass_Aged)
  IA_lock                   brass barrel plug with its rose, centre (-0.12, 1.13, 0.52), axis local +Y, a counterbored
                            keyway; OFF = -90° about local +Y (code, with the isolator).
    lock_key_mount          child of IA_lock at (0, 0.004, 0); key blade down, bow up, bow face +Z (+90° about X).
  lock_sym_diamond / _triangle / _circle / _square
                            brass 3D inlays (0.05) on the ledge top beside the keyhole; the code shows the cabinet's
                            own (I ▲, II ◆, III ●).
  IA_key_window             top-hinged glass flap 0.12 x 0.16, pivot (-0.12, 1.53, 0.51); open = -100° about local +X.
  held_key_mount            (-0.12, 1.46, 0.47): the held key hangs on the pin, blade down, face +Z (+90° about X).
  IA_isolator               bakelite rotary bar handle (0.18) at (0.15, 1.28, 0.47), axis local +Z;
                            ON (rest) = vertical, OFF = +90° about local +Z (points at O).
  iso_lamp                  opal glass jewel at (0.15, 1.62, 0.46) (code: green ON, red OFF).
  num_1 / num_2 / num_3     brass plates with pierced Roman numerals I, II, III at (0, 1.76, 0.455); the code shows
                            the cabinet's own.

    blender -b --factory-startup -P tools/blender/models/switch_cabinet.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "switch_cabinet"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3500, 8, 4
PAINT, BRASS, GLASS, BAKE = B.PAINT, B.BRASS, B.GLASS, B.BAKELITE

W2, Y0, Y1, ZF = 0.35, 0.10, 2.00, 0.45          # half width, body bottom / top, front face
LEDGE = (-0.26, 0.02, 1.10, 1.13, 0.58)          # x0, x1, y0, y1, z front
LOCK = (-0.12, 1.13, 0.52)
PLUG_R, ROSE_R, BORE_R = 0.020, 0.032, 0.0085
BORE_BOTTOM = 1.120
SYM_C = (-0.205, 0.52)                           # symbol centre on the ledge top (x, z)
WIN = (-0.12, 1.45, 0.50)
FLAP_PIVOT = (-0.12, 1.53, 0.51)
FLAP_W, FLAP_H = 0.12, 0.16
HELD = (-0.12, 1.46, 0.47)
PIN_Y = 1.4995                                   # held keys' hole centres sit 0.0387..0.0424 above the mount
ISO = (0.15, 1.28, 0.47)
DIAL_R, MARK_R = 0.140, 0.122
LAMP = (0.15, 1.62, 0.46)
NUM = (0.0, 1.76, 0.455)
KEYS = {"diamond": "key_diamond", "triangle": "key_triangle", "circle": "key_circle", "square": "key_square"}
CAB_X = (-7.4, -8.3, -9.2)
TAKES = ("triangle", "diamond", "circle")        # lock face: I ▲, II ◆, III ●
HOLDS = ("circle", "triangle", "square")         # behind the glass: I ●, II ▲, III ■


# ====================================================================== static cabinet
def carcass():
    p = []
    # recessed plinth, carcass, top cap
    p.append(B.gbox("plinth", (-W2 + 0.02, 0.0, 0.02), (W2 - 0.02, Y0, ZF - 0.03), PAINT, 0.004))
    p.append(B.gbox("carcass", (-W2, Y0, 0.0), (W2, Y1 - 0.03, ZF - 0.018), PAINT, 0.0))
    p.append(B.gbox("cap", (-W2 - 0.012, Y1 - 0.03, -0.0), (W2 + 0.012, Y1, ZF - 0.006), PAINT, 0.008, 1))
    # front door: pressed border (raised frame) and a flat field, three hinges on the right edge
    dz0 = ZF - 0.018
    p.append(B.gbox("door", (-W2 + 0.012, Y0 + 0.015, dz0), (W2 - 0.012, Y1 - 0.045, ZF - 0.004), PAINT, 0.004, 1))
    b = 0.045
    for (x0, y0_, x1, y1_) in ((-W2 + 0.012, Y0 + 0.015, W2 - 0.012, Y0 + 0.015 + b),
                               (-W2 + 0.012, Y1 - 0.045 - b, W2 - 0.012, Y1 - 0.045),
                               (-W2 + 0.012, Y0 + 0.015 + b, -W2 + 0.012 + b, Y1 - 0.045 - b),
                               (W2 - 0.012 - b, Y0 + 0.015 + b, W2 - 0.012, Y1 - 0.045 - b)):
        p.append(B.gbox("border", (x0, y0_, ZF - 0.006), (x1, y1_, ZF), PAINT, 0.0))
    for y in (0.40, 1.05, 1.70):
        p.append(B.gcyl("hinge", 0.011, y - 0.045, y + 0.045, base=(W2 - 0.004, 0.0, ZF - 0.012), axis=(0, 1, 0),
                        segments=8, mat=PAINT, chamfer=0.002))
        p.append(B.gcyl("hpin", 0.005, y + 0.045, y + 0.052, base=(W2 - 0.004, 0.0, ZF - 0.012), axis=(0, 1, 0),
                        segments=6, mat=BRASS))
    # door screws (four corners of the field)
    for sx in (-1, 1):
        for y in (Y0 + 0.07, Y1 - 0.10):
            p.append(B.rivet("dscr", 0.007, (sx * (W2 - 0.045), y, ZF), mat=BRASS, segs=6))
    # side louvres (pressed slats, both sides, low and high)
    for sx in (-1, 1):
        for yb in (0.34, 1.62):
            for k in range(4):
                y = yb + 0.05 * k
                sl = B.gbox("louvre", (-0.005, -0.012, 0.10), (0.005, 0.012, 0.34), PAINT, 0.0)
                sl.data.transform(Matrix.Translation((sx * (W2 + 0.004), y, 0.0)) @
                                  Matrix.Rotation(math.radians(35 * sx), 4, "Z"))
                p.append(sl)
    # cable glands on the top
    for x in (-0.18, 0.18):
        p.append(B.glathe("gland", [(0.032, 0.0), (0.032, 0.012), (0.026, 0.016), (0.026, 0.034), (0.022, 0.036),
                                    (0.0, 0.036)], (x, Y1, 0.16), (0, 1, 0), 10, BRASS, smooth=40.0))
        p.append(B.gcyl("conduit", 0.018, 0.034, 0.075, base=(x, Y1, 0.16), axis=(0, 1, 0), segments=10, mat=PAINT,
                        caps=False))
    return p


def ledge_and_lock_housing():
    p = []
    x0, x1, y0, y1, zf = LEDGE
    cx, cz = LOCK[0], LOCK[2]
    hw = PLUG_R + 0.002
    # the ledge with a square hole for the plug (the rose covers the corners)
    p += [B.gbox("ledge_l", (x0, y0, ZF), (cx - hw, y1, zf), PAINT, 0.003),
          B.gbox("ledge_r", (cx + hw, y0, ZF), (x1, y1, zf), PAINT, 0.003),
          B.gbox("ledge_b", (cx - hw, y0, ZF), (cx + hw, y1, cz - hw), PAINT, 0.0),
          B.gbox("ledge_f", (cx - hw, y0, cz + hw), (cx + hw, y1, zf), PAINT, 0.0)]
    # gussets under the ledge
    for gx in (x0 + 0.012, x1 - 0.012):
        g = L.prism_xz("gusset", [(0.0, 0.0), (zf - ZF - 0.01, 0.0), (0.0, -0.09)], -0.004, 0.004, mat=PAINT)
        # prism_xz: polygon in its XZ plane (x = depth out of the door, z = down), extruded along its Y (= our X)
        g.data.transform(Matrix.Translation((gx, y0, ZF)) @ Matrix((( 0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 0),
                                                                    (0, 0, 0, 1))))
        p.append(g)
    # brass lock housing under the ledge (encloses the key blade)
    p.append(B.glathe("housing", [(0.0, -0.065), (0.022, -0.065), (0.026, -0.060), (0.026, -0.006), (0.030, 0.0),
                                  (0.0, 0.0)], (cx, y0, cz), (0, 1, 0), 12, BRASS, smooth=45.0))
    return p


def key_box():
    p = []
    wx, wy = WIN[0], WIN[1]
    bx0, bx1 = wx - FLAP_W / 2 - 0.014, wx + FLAP_W / 2 + 0.014
    by0, by1 = wy - FLAP_H / 2 - 0.014, wy + FLAP_H / 2 + 0.014
    zb = 0.503
    t = 0.010
    p += [B.gbox("kb_l", (bx0, by0, ZF - 0.002), (bx0 + t, by1, zb), PAINT, 0.002),
          B.gbox("kb_r", (bx1 - t, by0, ZF - 0.002), (bx1, by1, zb), PAINT, 0.002),
          B.gbox("kb_b", (bx0 + t, by0, ZF - 0.002), (bx1 - t, by0 + t, zb), PAINT, 0.002),
          B.gbox("kb_t", (bx0 + t, by1 - t, ZF - 0.002), (bx1 - t, by1, zb), PAINT, 0.002)]
    # brass bezel round the window opening (the flap closes onto it)
    bez = B.plate("kbez", [L.rounded_rect(bx1 - bx0 + 0.004, by1 - by0 + 0.004, 0.008, 3),
                           L.rounded_rect(FLAP_W - 0.004, FLAP_H - 0.004, 0.005, 2)], 0.003, mat=BRASS, bevel=0.0,
                  loc=(wx, wy, zb - 0.001))
    p.append(bez)
    # flap hinge knuckles (static) along the top edge, the hanging pin inside
    for dx in (-0.045, 0.045):
        p.append(B.gcyl("fhinge", 0.0045, -0.012, 0.012, base=(wx + dx, FLAP_PIVOT[1] + 0.003, FLAP_PIVOT[2]),
                        axis=(1, 0, 0), segments=8, mat=BRASS))
    p.append(B.gcyl("pin", 0.0012, ZF - 0.001, 0.492, base=(HELD[0], PIN_Y + 0.0004, 0.0), axis=(0, 0, 1), segments=6,
                    mat=BRASS, caps=True))
    p.append(B.gcyl("pinhead", 0.0022, 0.492, 0.495, base=(HELD[0], PIN_Y + 0.0004, 0.0), axis=(0, 0, 1), segments=6,
                    mat=BRASS))
    return p


def isolator_static():
    p = []
    x, y, z = ISO
    p.append(B.glathe("dial", [(0.0, 0.0), (DIAL_R, 0.0), (DIAL_R, 0.003), (DIAL_R - 0.003, 0.005), (0.0, 0.005)],
                      (x, y, ZF), (0, 0, 1), 24, BRASS, smooth=40.0))
    # IEC marks, painted into the brass: I at 12 o'clock, O at 9 o'clock; short travel arc between them
    zt = ZF + 0.005
    p.append(B.plate("mark_I", [L.rounded_rect(0.006, 0.026, 0.001, 1)], 0.0012, mat=PAINT, bevel=0.0,
                     loc=(x, y + MARK_R, zt)))
    p.append(B.plate("mark_O", [L.circle(0.0125, 14), list(reversed(L.circle(0.0075, 14)))], 0.0012, mat=PAINT,
                     bevel=0.0, loc=(x - MARK_R, y, zt)))
    arc = [(math.cos(math.radians(a)) * 0.096, math.sin(math.radians(a)) * 0.096) for a in range(100, 171, 10)]
    arc_in = [(math.cos(math.radians(a)) * 0.092, math.sin(math.radians(a)) * 0.092) for a in range(170, 99, -10)]
    p.append(B.plate("travel", [arc + arc_in], 0.0008, mat=PAINT, bevel=0.0, loc=(x, y, zt)))
    # the boss
    p.append(B.glathe("boss", [(0.036, 0.0), (0.036, 0.008), (0.030, 0.016), (0.022, 0.020), (0.0, 0.020)],
                      (x, y, ZF + 0.002), (0, 0, 1), 14, BRASS, smooth=45.0))
    # lamp bezel
    p.append(B.bezel("lampbz", (LAMP[0], LAMP[1], ZF), 0.021, 0.032, 0.012, seg=12))
    return p


def static():
    parts = carcass() + ledge_and_lock_housing() + key_box() + isolator_static()
    return B.part(NAME, parts)


# ====================================================================== moving / coded parts
def lock():
    x, y, z = LOCK
    # plug body below the rose, the rose flange on the ledge top, a counterbored keyway for the key collar
    prof = [(0.0, BORE_BOTTOM - y), (BORE_R, BORE_BOTTOM - y), (BORE_R, 0.0045), (BORE_R + 0.0015, 0.006),
            (ROSE_R - 0.004, 0.006), (ROSE_R, 0.0035), (ROSE_R, 0.0), (PLUG_R, 0.0), (PLUG_R, -0.040),
            (PLUG_R - 0.003, -0.043), (0.0, -0.043)]
    prof = list(reversed(prof))
    body = B.glathe("plug", prof, (x, y, z), (0, 1, 0), 16, BRASS, smooth=40.0)
    # keyway slot for the blade + bit (a dark recess suggested by a box sunk below the bore bottom)
    slot = B.gbox("keyway", (x - 0.0065, BORE_BOTTOM - 0.0015, z - 0.0016), (x + 0.0095, BORE_BOTTOM + 0.0005,
                                                                               z + 0.0016), BRASS, 0.0)
    # index mark on the rose (shows the quarter turn) and two grip notches
    idx = B.gbox("idx", (x - 0.0015, y + 0.006, z + ROSE_R - 0.012), (x + 0.0015, y + 0.0072, z + ROSE_R - 0.003),
                 BRASS, 0.0)
    return B.part("IA_lock", [body, slot, idx], pivot=LOCK)


def lock_symbols():
    out = []
    x, z = SYM_C
    for kind in ("diamond", "triangle", "circle", "square"):
        s = S.inlay(f"lock_sym_{kind}", kind, 0.05, depth=0.0025, mat=BRASS, bevel=0.0005)
        # inlay faces +Z in its XY plane: lay it on the ledge top facing +Y, its "up" toward -Z (away from the viewer)
        s.data.transform(Matrix.Translation((x, LEDGE[3] - 0.0005, z)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
        out.append(B.part(f"lock_sym_{kind}", [s], pivot=(x, LEDGE[3], z)))
    return out


def key_window():
    x, y, z = FLAP_PIVOT
    g = B.gbox("flap", (x - FLAP_W / 2, y - FLAP_H, 0.505), (x + FLAP_W / 2, y, 0.511), GLASS, 0.0015)
    knuckle = B.gcyl("fknuckle", 0.004, -0.032, 0.032, base=(x, y + 0.003, z), axis=(1, 0, 0), segments=8, mat=GLASS)
    lip = B.gbox("fliplip", (x - 0.02, y - FLAP_H - 0.006, 0.505), (x + 0.02, y - FLAP_H + 0.002, 0.516), GLASS, 0.002)
    return B.part("IA_key_window", [g, knuckle, lip], pivot=FLAP_PIVOT)


def isolator():
    x, y, z = ISO
    # tapered grip bar 0.18 long: tail -0.075, pointer tip +0.105 (points at I when ON)
    outline = [(-0.014, -0.075), (0.014, -0.075), (0.017, -0.040), (0.017, 0.040), (0.011, 0.090), (0.0, 0.105),
               (-0.011, 0.090), (-0.017, 0.040), (-0.017, -0.040)]
    bar = B.plate("bar", [A.ccw(outline)], 0.020, mat=BAKE, bevel=0.004, bevel_res=1, loc=(x, y, z + 0.002))
    hub = B.glathe("hub", [(0.0, 0.0), (0.026, 0.0), (0.026, 0.016), (0.022, 0.024), (0.0, 0.026)], (x, y, z),
                   (0, 0, 1), 12, BAKE, smooth=50.0)
    ridge = B.gbox("ridge", (x - 0.004, y - 0.06, z + 0.020), (x + 0.004, y + 0.075, z + 0.026), BAKE, 0.002)
    return B.part("IA_isolator", [bar, hub, ridge], pivot=ISO)


def iso_lamp():
    o = B.jewel("jewel", (LAMP[0], LAMP[1], ZF + 0.004), 0.020, mat=GLASS, h=0.016, seg=12)
    return B.part("iso_lamp", [o], pivot=LAMP)


def numeral_plate(n):
    """Brass plate with the Roman numeral pierced through (the painted door shows in the cuts)."""
    w, h = 0.13, 0.072
    loops = [L.rounded_rect(w, h, 0.008, 3)]
    sw, sh, cap, ch = 0.008, 0.044, 0.018, 0.0055        # stem width, height, serif width, serif height
    pitch = 0.020
    for k in range(n):
        cx = (k - (n - 1) / 2) * pitch
        hole = [(cx - cap / 2, -sh / 2), (cx + cap / 2, -sh / 2), (cx + cap / 2, -sh / 2 + ch), (cx + sw / 2, -sh / 2 + ch),
                (cx + sw / 2, sh / 2 - ch), (cx + cap / 2, sh / 2 - ch), (cx + cap / 2, sh / 2), (cx - cap / 2, sh / 2),
                (cx - cap / 2, sh / 2 - ch), (cx - sw / 2, sh / 2 - ch), (cx - sw / 2, -sh / 2 + ch),
                (cx - cap / 2, -sh / 2 + ch)]
        loops.append(list(reversed(A.ccw(hole))))
    pl = B.plate("np", loops, 0.004, mat=BRASS, bevel=0.0, loc=(NUM[0], NUM[1], NUM[2] - 0.002))
    return B.part(f"num_{n}", [pl], pivot=NUM)


def mounts(lock_obj):
    lk = B.empty("lock_key_mount", (LOCK[0], LOCK[1] + 0.004, LOCK[2]), (90.0, 0.0, 0.0))
    hk = B.empty("held_key_mount", HELD, (90.0, 0.0, 0.0))
    return lk, hk


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    lk = lock()
    syms = lock_symbols()
    win = key_window()
    iso = isolator()
    lamp = iso_lamp()
    nums = [numeral_plate(n) for n in (1, 2, 3)]
    lkm, hkm = mounts(lk)
    B.K.to_blender()
    A.finalize_uv()
    B.parent(lkm, lk)
    return dict(static=st, lock=lk, syms=syms, window=win, isolator=iso, lamp=lamp, nums=nums, lock_mount=lkm,
                held_mount=hkm)


REQ = (["switch_cabinet", "IA_lock", "lock_key_mount", "IA_key_window", "held_key_mount", "IA_isolator", "iso_lamp",
        "num_1", "num_2", "num_3"] + [f"lock_sym_{k}" for k in ("diamond", "triangle", "circle", "square")])


def verify(path):
    ident = [n for n in REQ if not n.endswith("_mount")]
    expect = {"IA_lock": LOCK, "lock_key_mount": (LOCK[0], LOCK[1] + 0.004, LOCK[2]), "IA_key_window": FLAP_PIVOT,
              "held_key_mount": HELD, "IA_isolator": ISO, "iso_lamp": LAMP, "num_1": NUM, "num_2": NUM, "num_3": NUM}
    parents = {n: None for n in REQ}
    parents["lock_key_mount"] = "IA_lock"
    rot = {"lock_key_mount": (90.0, 0.0, 0.0), "held_key_mount": (90.0, 0.0, 0.0)}
    # drawn per instance: static 2 + lock + window + isolator + lamp + one numeral + one symbol = 8
    errs = B.verify(path, REQ, identity=ident, expect=expect, parents=parents, rot_expect=rot, tris=TRI_BUDGET,
                    surf=SURF_BUDGET, mats=MAT_BUDGET, surf_drawn=8)
    lo, hi = B.V.mesh_bounds_godot([bpy.data.objects[NAME]])
    print(f"{B.TAG} static bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
def own_only(prefix, n):
    """Hide the alternatives the code hides on cabinet n (keep its own numeral and lock symbol)."""
    for k in (1, 2, 3):
        o = B.imported(prefix, f"num_{k}")
        if o is not None:
            o.hide_render = (k != n + 1)
    for kind in ("diamond", "triangle", "circle", "square"):
        o = B.imported(prefix, f"lock_sym_{kind}")
        if o is not None:
            o.hide_render = (kind != TAKES[n])


def set_off(prefix, off):
    """Isolator OFF: lock -90° about Y, window open -100° about X, isolator +90° about Z (from rest)."""
    for nm, ax, deg in (("IA_lock", "y", -90.0), ("IA_key_window", "x", -100.0), ("IA_isolator", "z", 90.0)):
        o = B.imported(prefix, nm)
        if o is not None and off:
            B.K.pose_rot(o, ax, deg)


def qa(parts, args):
    B.qa_begin()
    B.hall()
    B.bring("interlock_plate", (-8.3, 0.0, 4.0), 180.0)
    # this scene's objects are cabinet II (centre); I and III are imported copies
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    B.place(mine, (CAB_X[1], 0.0, 4.0), 180.0, name="qa_cab_1")
    prefixes = {0: "qa_c0_", 1: "", 2: "qa_c2_"}
    B.bring(NAME, (CAB_X[0], 0.0, 4.0), 180.0, prefix="qa_c0_")
    B.bring(NAME, (CAB_X[2], 0.0, 4.0), 180.0, prefix="qa_c2_")
    for n in range(3):
        own_only(prefixes[n], n)
    lamp_green = B.K.glow("qa_iso_green", "3CFF6A", 4.0)
    lamp_red = B.K.glow("qa_iso_red", "FF3A2A", 4.0)
    lamps = {n: B.imported(prefixes[n], "iso_lamp") for n in range(3)}
    for n in range(3):
        B.K.override(lamps[n], lamp_green)
    # held keys in their windows at the start: I ●, II ▲, III ■
    for n in range(3):
        mt = B.imported(prefixes[n], "held_key_mount")
        B.bring(KEYS[HOLDS[n]], under=mt, prefix=f"qa_k{n}held_")
    movers = [B.imported(prefixes[n], nm) for n in range(3) for nm in ("IA_lock", "IA_key_window",
                                                                                 "IA_isolator")]
    movers = [o for o in movers if o is not None]
    rest = B.rest_store(movers)

    def cab_view(n):
        x = CAB_X[n]
        return (x, 1.45, 2.75), (x, 1.3, 3.55)

    # 1 switch_room view, start state (all ON, held keys in, locks empty)
    if B.want(args, "1"):
        B.rest_apply(movers, rest)
        cam = (-8.3, 1.65, 1.75)
        B.choir_lights(cam, fill=10.0)
        B.shoot(NAME, cam, (-8.3, 1.4, 4.0), 58)
    # 2 cabinet_1 view, start state
    if B.want(args, "2"):
        B.rest_apply(movers, rest)
        cam, tgt = cab_view(1)
        B.choir_lights(cam, fill=12.0)
        B.shoot(NAME + "_2", cam, tgt, 50)
    # ◆ into cabinet II, turned OFF: the lock (with its key) turned, the window open, ▲ free; lamp red
    key_in = B.bring("key_diamond", under=parts["lock_mount"], prefix="qa_kd_")
    if B.want(args, "3"):
        B.rest_apply(movers, rest)
        set_off(prefixes[1], True)
        B.K.override(lamps[1], lamp_red)
        cam, tgt = cab_view(1)
        B.choir_lights(cam, fill=12.0)
        B.shoot(NAME + "_3", cam, tgt, 50)
    # 4 close-up of cabinet II's lock and window (OFF state), oblique from the left
    if B.want(args, "4"):
        cam = (-8.05, 1.36, 3.12)
        B.choir_lights(cam, fill=10.0)
        B.shoot(NAME + "_4", cam, (-8.19, 1.24, 3.50), 40)
    # 5 the isolator close-up (OFF, pointing at O) and the numeral plate
    if B.want(args, "5"):
        cam = (-8.52, 1.52, 3.05)
        B.choir_lights(cam, fill=10.0)
        B.shoot(NAME + "_5", cam, (-8.44, 1.45, 3.55), 40)
    if key_in is None:
        print(f"{B.TAG} QA: key_diamond.glb missing")


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
