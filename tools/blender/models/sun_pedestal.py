"""sun_pedestal.glb — the Sun's control pedestal: feed wheel, ammeter with a green band, the Sun lever (Chapter 4, group E; puzzle P3).
Contract: docs/models/ch4.md section 7 sun_pedestal; results: docs/models/ch4_e.md.

LOCAL FRAME: origin = the floor at the footprint centre, front = +Z. Placed at (-12.0, 0, 2.4) with yaw 90 so the front faces +X, into the hall.
Nodes:
  sun_pedestal   M_Steel_Painted + M_Brass_Aged + M_Enamel_Cream  the static cabinet (plinth, door panel, a slanted top shelf, an instrument head),
                 the cream feed scale disc Ø 0.54 with its ticks and the numerals 9 .. 0 (the GAP g the handle points at, clockwise from 12 o'clock
                 every 27 deg), the ammeter bezel, the cream dial with ticks 0 .. 10 and the numerals 0 2 4 6 8 10, the lever's quadrant
  IA_feed        M_Brass_Aged  the feed hand wheel Ø 0.34 (rim, five spokes, hub, a handle pin at 12 o'clock). ORIGIN = its axis (0, 0.50, 0.30), axis +Z, identity at
                 the start (gap 9). Feed count w = 9 - g = -27 deg x w about +Z (clockwise = feeding in); the handle then points at the numeral g
  ammeter_needle M_Bakelite  the needle; ORIGIN = the dial centre (0, 1.20, -0.028); identity = pointing 55 deg LEFT of up (the cold stop); value n = -11 deg x n
                 about +Z (so 10 points 55 deg right of up)
  ammeter_band   M_Paint_Green  a green arc segment (r 0.082 .. 0.097, +-4.5 deg) on the dial; ORIGIN = the dial centre; built at the needle's identity
                 angle, so the code rotates it by -11 deg x (10 - g_target) about +Z, the same law as the needle
  IA_sun_lever   M_Bakelite  the Sun lever: an arm with a swelling grip on a brass pivot block; ORIGIN = the pivot (0.21, 0.99, 0.12); rest OFF = upright
                 (+Y); ON = +50 deg about +X (toward the player)

    blender -b --factory-startup -P tools/blender/models/sun_pedestal.py [-- --no-render] [--shots=1,2,...]
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
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, PAINT, CREAM, BAKE, GREEN  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "sun_pedestal"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 7, 5
WHEEL_C = (0.0, 0.50, 0.30)
DIAL_C = (0.0, 1.20, -0.028)
LEVER_P = (0.21, 0.99, 0.12)
FRONT = 0.24
HEAD_Z = -0.04


def rod(a, b, r, mat=BRASS, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    return K.gcyl("rod", r, 0.0, d.length, base=tuple(a), axis=tuple(d.normalized()), segments=segs, mat=mat, smooth=60.0)


def digit(name, d, h, depth, centre, mat=BRASS, rot=0.0):
    o = C.N.digit_obj(name, d, h, depth, mat, res=1)
    o.data.transform(Matrix.Translation(centre) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def body_parts():
    out = []
    # ---- painted steel: plinth, cabinet, slanted shelf, instrument head
    out.append(K.gbox("plinth", (-0.34, 0.0, -0.28), (0.34, 0.10, 0.28), PAINT, 0.008))
    out.append(K.gbox("cabinet", (-0.30, 0.10, -0.24), (0.30, 0.86, FRONT), PAINT, 0.010))
    for (x0, x1, y0, y1) in ((-0.26, 0.26, 0.15, 0.17), (-0.26, 0.26, 0.80, 0.82), (-0.26, -0.24, 0.17, 0.80), (0.24, 0.26, 0.17, 0.80)):
        out.append(K.gbox("panel", (x0, y0, FRONT), (x1, y1, FRONT + 0.012), PAINT, 0.002))      # a raised panel frame on the door
    wedge = bmesh.new()
    vs = [wedge.verts.new(p) for p in ((-0.30, 0.86, FRONT), (0.30, 0.86, FRONT), (0.30, 0.86, HEAD_Z), (-0.30, 0.86, HEAD_Z),
                                      (-0.30, 1.00, HEAD_Z), (0.30, 1.00, HEAD_Z))]
    X.bm_face(wedge, (vs[0], vs[1], vs[5], vs[4]), (0.0, 0.28, 0.14))              # the slope
    X.bm_face(wedge, (vs[0], vs[4], vs[3]), (-1.0, 0.0, 0.0))
    X.bm_face(wedge, (vs[1], vs[2], vs[5]), (1.0, 0.0, 0.0))
    out.append(K.obj_from_bm("shelf", wedge, PAINT))
    out.append(K.gbox("head", (-0.27, 1.00, -0.24), (0.27, 1.40, HEAD_Z), PAINT, 0.010))
    for sx in (-1, 1):
        for sz in (-1, 1):
            out.append(K.hexbolt("bolt", 0.018, (sx * 0.29, 0.10, sz * 0.23), normal=(0, 1, 0), mat=PAINT, washer=False))
    # ---- brass trim: kick strip, shelf edge, head cap, door hinges and a handle
    out.append(K.gbox("kick", (-0.305, 0.10, FRONT - 0.002), (0.305, 0.135, FRONT + 0.010), BRASS, 0.003))
    out.append(K.gbox("edge", (-0.305, 0.855, FRONT - 0.004), (0.305, 0.88, FRONT + 0.012), BRASS, 0.003))
    out.append(K.gbox("cap", (-0.285, 1.395, -0.255), (0.285, 1.425, HEAD_Z + 0.012), BRASS, 0.004))
    for y in (0.25, 0.72):
        out.append(rod((-0.255, y - 0.05, FRONT + 0.014), (-0.255, y + 0.05, FRONT + 0.014), 0.012, BRASS, 8))
    # ---- the feed scale disc (cream, Ø 0.54) with 10 ticks and the numerals 9..0 (the gap), clockwise from 12 o'clock every 27 deg
    out.append(K.gcyl("scale", 0.27, FRONT + 0.012, FRONT + 0.024, base=(0.0, WHEEL_C[1], 0.0), axis=(0, 0, 1), segments=56, mat=CREAM, chamfer=0.003))
    out.append(D.ring("scalerim", 0.272, 0.288, FRONT + 0.012, FRONT + 0.032, centre=(0.0, WHEEL_C[1], 0.0), axis=(0, 0, 1), segs=56, mat=BRASS,
                      chamfer=0.003))
    out.append(K.gcyl("boss", 0.045, FRONT + 0.012, 0.276, base=(0.0, WHEEL_C[1], 0.0), axis=(0, 0, 1), segments=14, mat=BRASS, chamfer=0.004))
    for w in range(10):
        a = math.radians(27.0 * w)
        dx, dy = math.sin(a), math.cos(a)
        t = K.gbox("tick", (-0.004, 0.180, FRONT + 0.024), (0.004, 0.205, FRONT + 0.028), BRASS, 0.0)
        t.data.transform(Matrix.Translation((0.0, WHEEL_C[1], 0.0)) @ Matrix.Rotation(-a, 4, "Z"))
        out.append(t)
        out.append(digit(f"g{w}", 9 - w, 0.040, 0.004, (0.237 * dx, WHEEL_C[1] + 0.237 * dy, FRONT + 0.024)))
    # the fixed pointer notch at the top of the disc
    out.append(K.plate("ptr", [[(-0.022, 0.292), (0.022, 0.292), (0.0, 0.262)]], 0.006, z0=FRONT + 0.032, mat=BRASS, bevel=0.0, drop_bottom=True,
                       loc=(0.0, WHEEL_C[1], 0.0)))
    # ---- the ammeter: bezel, cream dial, ticks, numerals
    out.append(K.glathe("bezel", [(0.118, HEAD_Z), (0.152, HEAD_Z), (0.152, HEAD_Z + 0.030), (0.140, HEAD_Z + 0.044), (0.118, HEAD_Z + 0.034),
                                  (0.118, HEAD_Z)], base=(0.0, DIAL_C[1], 0.0), axis=(0, 0, 1), segments=40, mat=BRASS, smooth=50.0,
                        cap_bottom=False, cap_top=False))
    out.append(K.gcyl("dial", 0.121, HEAD_Z + 0.004, HEAD_Z + 0.012, base=(0.0, DIAL_C[1], 0.0), axis=(0, 0, 1), segments=40, mat=CREAM))
    zd = HEAD_Z + 0.012
    for n in range(11):
        ang = math.radians(-55.0 + 11.0 * n)                          # from up, clockwise positive
        major = n % 5 == 0
        r0, r1 = (0.082, 0.112) if major else (0.094, 0.112)
        wdt = 0.0042 if major else 0.003
        t = K.gbox("tk", (-wdt, r0, zd), (wdt, r1, zd + 0.003), BRASS, 0.0)
        t.data.transform(Matrix.Translation((0.0, DIAL_C[1], 0.0)) @ Matrix.Rotation(-ang, 4, "Z"))
        out.append(t)
        if n % 2 == 0:
            cx, cy = 0.062 * math.sin(ang), DIAL_C[1] + 0.062 * math.cos(ang)
            if n == 10:
                out.append(digit("n1", 1, 0.020, 0.003, (cx - 0.008, cy, zd)))
                out.append(digit("n0", 0, 0.020, 0.003, (cx + 0.008, cy, zd)))
            else:
                out.append(digit(f"n{n}", n, 0.020, 0.003, (cx, cy, zd)))
    # a little pivot block, two cheek plates (the quadrant) with stops for the Sun lever
    out.append(K.gbox("pblock", (LEVER_P[0] - 0.06, 0.88, LEVER_P[2] - 0.05), (LEVER_P[0] + 0.06, LEVER_P[1] - 0.012, LEVER_P[2] + 0.05), BRASS, 0.004))
    for sx in (-1, 1):
        xa, xb = sorted((LEVER_P[0] + sx * 0.040, LEVER_P[0] + sx * 0.050))
        # a sector in the (z, y) plane about the pivot: angle a from up (+Y) toward +Z, from -10 to +60 deg
        pts = [(LEVER_P[2], LEVER_P[1])] + [(LEVER_P[2] + 0.20 * math.sin(math.radians(a)), LEVER_P[1] + 0.20 * math.cos(math.radians(a)))
                                           for a in range(-10, 61, 10)]
        cz = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        sb = bmesh.new()
        lo = [sb.verts.new((xa, y, z)) for (z, y) in pts]
        hi = [sb.verts.new((xb, y, z)) for (z, y) in pts]
        n = len(pts)
        X.bm_face(sb, list(reversed(lo)), (-1, 0, 0))
        X.bm_face(sb, hi, (1, 0, 0))
        for i in range(n):
            j = (i + 1) % n
            mz, my = 0.5 * (pts[i][0] + pts[j][0]) - cz, 0.5 * (pts[i][1] + pts[j][1]) - cy
            X.bm_face(sb, (lo[i], lo[j], hi[j], hi[i]), (0.0, my, mz))
        out.append(K.obj_from_bm("cheek", sb, BRASS))
    for a in (0.0, 50.0):                                                # the two stops
        s = math.radians(a)
        out.append(K.gbox("stop", (LEVER_P[0] - 0.040, LEVER_P[1] + 0.195 * math.cos(s) - 0.012, LEVER_P[2] + 0.195 * math.sin(s) - 0.012),
                          (LEVER_P[0] + 0.040, LEVER_P[1] + 0.195 * math.cos(s) + 0.012, LEVER_P[2] + 0.195 * math.sin(s) + 0.012), BRASS, 0.002))
    return out


def wheel_parts():
    ax, ay, az = WHEEL_C
    out = []
    out.append(M.torus("rim", 0.15, 0.020, loc=(ax, ay, az), major_seg=40, minor_seg=8, mat=BRASS))
    for k in range(5):
        a = math.radians(90.0 + 72.0 * k)
        out.append(D.rod("spoke", (ax + 0.04 * math.cos(a), ay + 0.04 * math.sin(a), az), (ax + 0.14 * math.cos(a), ay + 0.14 * math.sin(a), az), 0.012,
                         segs=6, mat=BRASS))
    out.append(K.glathe("hub", [(0.0, -0.030), (0.050, -0.030), (0.056, -0.012), (0.056, 0.030), (0.036, 0.048), (0.0, 0.052)], base=(ax, ay, az), axis=(0, 0, 1),
                        segments=14, mat=BRASS, smooth=60.0))
    # the handle pin on the rim at 12 o'clock (a stem forward with a ball) so the turning and the pointed numeral show
    out.append(D.rod("pin", (ax, ay + 0.15, az + 0.01), (ax, ay + 0.15, az + 0.085), 0.013, segs=8, mat=BRASS))
    out.append(M.sphere("ball", 0.026, loc=(ax, ay + 0.15, az + 0.105), segments=12, rings=8, mat=BRASS))
    return out


def needle_parts():
    zc = DIAL_C[2]
    z0 = zc + 0.0
    L_ = 0.098
    body = [(-0.0045, 0.0), (0.0045, 0.0), (0.0016, L_), (-0.0016, L_)]
    tail = [(-0.004, 0.0), (0.004, 0.0), (0.004, -0.026), (-0.004, -0.026)]
    ang = 55.0                                                            # identity: 55 deg LEFT of up = rotate +55 deg (CCW) about +Z
    o1 = K.plate("ndl", [body, tail], 0.004, z0=0.0, mat=BAKE, bevel=0.0, drop_bottom=False)
    o1.data.transform(Matrix.Translation((DIAL_C[0], DIAL_C[1], zc)) @ Matrix.Rotation(math.radians(ang), 4, "Z"))
    hub = K.glathe("nhub", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.006), (0.009, 0.011), (0.0, 0.012)], base=(DIAL_C[0], DIAL_C[1], zc + 0.004), axis=(0, 0, 1),
                   segments=12, mat=BAKE, smooth=60.0)
    return [o1, hub]


def band_parts():
    zc = DIAL_C[2]
    r0, r1 = 0.082, 0.097
    ang0 = 55.0                                                           # the centre, 55 deg left of up
    pts_o = [(r1 * math.sin(math.radians(-ang0 - 4.5 + 9.0 * i / 8.0)), r1 * math.cos(math.radians(-ang0 - 4.5 + 9.0 * i / 8.0))) for i in range(9)]
    pts_i = [(r0 * math.sin(math.radians(-ang0 - 4.5 + 9.0 * i / 8.0)), r0 * math.cos(math.radians(-ang0 - 4.5 + 9.0 * i / 8.0))) for i in range(9)][::-1]
    o = K.plate("band", [pts_o + pts_i], 0.003, z0=0.0, mat=GREEN, bevel=0.0, drop_bottom=True)
    o.data.transform(Matrix.Translation((DIAL_C[0], DIAL_C[1], zc + 0.0005)))
    return [o]


def lever_parts():
    px, py, pz = LEVER_P
    out = [K.gcyl("pivot", 0.026, -0.05, 0.05, base=(px, py, pz), axis=(1, 0, 0), segments=14, mat=BAKE, chamfer=0.004)]
    prof = [(0.0, 0.0), (0.020, 0.0), (0.020, 0.14), (0.026, 0.16), (0.040, 0.20), (0.044, 0.25), (0.038, 0.29), (0.022, 0.31), (0.0, 0.315)]
    out.append(K.glathe("arm", prof, base=(px, py, pz), axis=(0, 1, 0), segments=16, mat=BAKE, smooth=60.0))
    return out


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("sun_pedestal", body_parts())
    feed = K.part("IA_feed", wheel_parts(), pivot=WHEEL_C)
    needle = K.part("ammeter_needle", needle_parts(), pivot=DIAL_C)
    band = K.part("ammeter_band", band_parts(), pivot=DIAL_C)
    lever = K.part("IA_sun_lever", lever_parts(), pivot=LEVER_P)
    K.to_blender()
    C.finalize()
    return dict(body=body, feed=feed, needle=needle, band=band, lever=lever)


def verify(path):
    req = ["sun_pedestal", "IA_feed", "ammeter_needle", "ammeter_band", "IA_sun_lever"]
    expect = {"sun_pedestal": (0.0, 0.0, 0.0), "IA_feed": WHEEL_C, "ammeter_needle": DIAL_C, "ammeter_band": DIAL_C, "IA_sun_lever": LEVER_P}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    C.qa_import("sun_lamp", (-13.0, 1.8, 0.0), 0.0, prefix="qa_sun_")
    C.qa_import("sun_iris", (-11.8, 1.8, 0.0), 90.0, prefix="qa_iris_")
    K.qa_place([parts["body"], parts["feed"], parts["needle"], parts["band"], parts["lever"]], (-12.0, 0.0, 2.4), 90.0, name="qa_ped_root")
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))
    # QA pose: gap g = 4 (the canonical) -> w = 5 turns of the wheel, needle in the green (value 6), lever ON
    K.pose_rot(parts["feed"], "z", -27.0 * 5)
    K.pose_rot(parts["needle"], "z", -11.0 * 6)
    K.pose_rot(parts["band"], "z", -11.0 * 6)

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False, core=False)
        K.light("sun_arc", "POINT", (-12.4, 1.8, 0.0), 40000.0, "FFF6E8", radius=0.2)
    if C.want(args, "1"):          # the pedestal view (lever OFF)
        cam, tgt, fov = C.view("apse")
        cam, tgt, fov = (-10.2, 1.5, 2.8), (-12.0, 1.1, 2.4), 46
        lit(cam, 50.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a closeup of the dial and the wheel, lever ON
        K.pose_rot(parts["lever"], "x", 50.0)
        cam, tgt, fov = (-10.6, 1.45, 2.4), (-12.0, 1.0, 2.4), 40
        lit(cam, 50.0, 0.25)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
