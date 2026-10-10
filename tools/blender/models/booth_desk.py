"""booth_desk.glb — Strand's walnut desk with a green-shaded lamp, a table clock stopped at 03:17 and his leather coat on a stand (Chapter 4, group F).
Contract: docs/models/ch4.md section 8 booth_desk; results: docs/models/ch4_f.md.

LOCAL FRAME: origin = the floor at the centre of the desk footprint, front = +Z; placed at (0, 2.0, -13.4) (the booth floor), yaw 0. Desk 1.64 x 0.84 x 0.78
(x +-0.82, z +-0.42); the top is at y = 0.78 (a leather writing field 1.30 x 0.62 on it). The coat stand stands left of the desk at (-1.35, 0, -0.18).
Node:
  booth_desk      M_Wood_Walnut + M_Brass_Aged + M_Leather + M_Steel_Painted  one static mesh: two drawer pedestals (3 drawers each, raised fronts, brass pulls and
                  keyholes), the centre drawer, the leather field with a brass edge, a banker's lamp (brass base and arm, green painted shade), a round table clock
                  stopped at 03:17 (brass case, painted dial), an inkwell, a paperweight, a ledger, the coat stand with a long leather coat
  box_mount       empty on the desk top at (0, 0.78, 0.0): strand_box4's origin (the base centre of the box)
  lamp_light      empty under the lamp shade at (-0.62, 1.13, -0.24)

    blender -b --factory-startup -P tools/blender/models/booth_desk.py [-- --no-render] [--shots=1,2]
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
from lib_ch4 import K, D, BRASS, PAINT, WALNUT  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

LEATHER = "M_Leather"
NAME = "booth_desk"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 6, 4
TOP = 0.78
BOX_MOUNT = (0.0, TOP, 0.0)
LAMP_AT = (-0.62, TOP, -0.24)
CLOCK_AT = (0.60, TOP, -0.22)
STAND_AT = (-1.38, 0.0, -0.16)


def loft(bm, sections, sides=14, cap_top=True, cap_bot=True):
    """A closed loft through elliptical sections (y, cx, cz, hx, hz)."""
    rings = []
    for (y, cx, cz, hx, hz) in sections:
        rings.append([bm.verts.new((cx + hx * math.cos(math.tau * i / sides), y, cz + hz * math.sin(math.tau * i / sides))) for i in range(sides)])
    for k in range(len(rings) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    if cap_bot:
        bm.faces.new(rings[0])
    if cap_top:
        bm.faces.new(list(reversed(rings[-1])))


def walnut():
    w = F.MB(WALNUT)
    # top slab with a slight overhang, pedestals with a plinth, the centre drawer bay and a modesty panel
    w.box((-0.82, 0.74, -0.42), (0.82, TOP, 0.42), bottom=True)
    w.box((-0.84, 0.735, -0.44), (0.84, 0.745, 0.44), bottom=True)
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.30, sx * 0.78))
        w.box((xa, 0.08, -0.36), (xb, 0.74, 0.37), bottom=True)
        pa, pb = sorted((sx * 0.29, sx * 0.80))
        w.box((pa, 0.0, -0.38), (pb, 0.08, 0.39), bottom=True)
        w.box((pa, 0.075, -0.385), (pb, 0.085, 0.395), bottom=True)
        # drawer fronts: three raised panels with a recessed frame look
        for k in range(3):
            y0 = 0.10 + k * 0.215
            y1 = y0 + 0.195
            w.box((xa + 0.02, y0, 0.37), (xb - 0.02, y1, 0.384))
            w.box((xa + 0.045, y0 + 0.025, 0.384), (xb - 0.045, y1 - 0.025, 0.392))
    w.box((-0.30, 0.10, -0.36), (0.30, 0.70, -0.33))                       # modesty panel
    w.box((-0.30, 0.64, -0.36), (0.30, 0.74, 0.36))                        # the centre drawer carcass (under the top)
    w.box((-0.285, 0.655, 0.36), (0.285, 0.725, 0.376))
    w.box((-0.255, 0.665, 0.376), (0.255, 0.715, 0.383))
    # the coat stand's base disc is walnut
    return w.obj("desk_walnut")


def leather():
    lt = F.MB(LEATHER)
    lt.box((-0.65, TOP, -0.31), (0.65, TOP + 0.004, 0.31))                  # the writing field
    # ledger on the left front corner, a little turned
    led = F.MB(LEATHER)
    led.box((-0.10, 0.0, -0.075), (0.10, 0.034, 0.075), bottom=True)
    obj = led.obj("ledger")
    obj.data.transform(Matrix.Translation((-0.46, TOP + 0.004, 0.18)) @ Matrix.Rotation(math.radians(12.0), 4, "Y"))
    # the coat: a long leather coat on a hanger, front toward +Z, hanging from the stand's top hook
    cx, cz = STAND_AT[0], STAND_AT[2] + 0.17
    bm = lt.bm
    body = [(1.60, cx, cz, 0.17, 0.065), (1.50, cx, cz, 0.24, 0.09), (1.30, cx, cz, 0.24, 0.10), (1.00, cx, cz + 0.005, 0.255, 0.115),
            (0.72, cx, cz + 0.01, 0.30, 0.135), (0.58, cx, cz + 0.012, 0.325, 0.145)]
    loft(bm, body, sides=16)
    for sx in (-1, 1):                                                       # sleeves hanging slightly out
        sleeve = [(1.52, cx + sx * 0.235, cz, 0.065, 0.065), (1.22, cx + sx * 0.285, cz + 0.01, 0.060, 0.060), (0.90, cx + sx * 0.325, cz + 0.02, 0.052, 0.052),
                  (0.72, cx + sx * 0.345, cz + 0.025, 0.050, 0.050)]
        loft(bm, sleeve, sides=10)
    # a shawl collar and a belt
    loft(bm, [(1.60, cx, cz - 0.01, 0.20, 0.090), (1.50, cx, cz + 0.02, 0.225, 0.11), (1.40, cx, cz + 0.03, 0.19, 0.095)], sides=14)
    loft(bm, [(1.02, cx, cz + 0.004, 0.268, 0.130), (0.98, cx, cz + 0.004, 0.272, 0.134), (0.94, cx, cz + 0.004, 0.268, 0.130)], sides=16)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return [lt.obj("desk_leather", fix=False), obj]


def paint():
    pt = F.MB(PAINT)
    lx, ly, lz = LAMP_AT
    # the green lamp shade: a wide bell over the desk (open at the bottom), a short collar on top
    return pt


def lamp_and_clock():
    out = []
    lx, ly, lz = LAMP_AT
    # banker's lamp: round brass base, a stem, a swan neck to the shade
    out.append(K.glathe("lamp_base", [(0.0, 0.0), (0.095, 0.0), (0.100, 0.012), (0.080, 0.030), (0.040, 0.045), (0.022, 0.060), (0.020, 0.30), (0.0, 0.30)],
                        base=(lx, ly, lz), axis=(0, 1, 0), segments=18, mat=BRASS, smooth=55.0))
    br = F.MB(BRASS)
    br.bar((lx, ly + 0.30, lz), (lx + 0.04, ly + 0.38, lz + 0.03), 0.026, ref=(0, 0, 1))
    br.cyl((lx + 0.04, ly + 0.38, lz + 0.03), (0, 1, 0), 0.034, 0.04, segs=10)
    # pull chain
    br.bar((lx + 0.035, ly + 0.30, lz + 0.05), (lx + 0.035, ly + 0.20, lz + 0.05), 0.006)
    out.append(br.obj("lamp_arm"))
    out.append(K.glathe("lamp_shade", [(0.06, 0.0), (0.075, 0.0), (0.150, -0.11), (0.152, -0.115), (0.145, -0.115), (0.070, -0.012), (0.058, -0.004), (0.058, 0.0)],
                        base=(lx + 0.04, ly + 0.50, lz + 0.03), axis=(0, 1, 0), segments=24, mat=PAINT, smooth=45.0, cap_bottom=False, cap_top=False))
    out.append(K.glathe("lamp_cap", [(0.0, 0.0), (0.060, 0.0), (0.045, 0.030), (0.0, 0.040)], base=(lx + 0.04, ly + 0.49, lz + 0.03),
                        axis=(0, 1, 0), segments=14, mat=BRASS, smooth=55.0))
    # table clock: a round brass case on two feet facing +Z, a painted dial, hands at 03:17
    cx, cy, cz = CLOCK_AT
    yc = cy + 0.095
    out.append(K.glathe("clock_case", [(0.070, 0.0), (0.095, 0.0), (0.098, 0.012), (0.096, 0.050), (0.086, 0.062), (0.066, 0.060), (0.060, 0.050), (0.070, 0.002)],
                        base=(cx, yc, cz - 0.03), axis=(0, 0, 1), segments=28, mat=BRASS, smooth=45.0, cap_bottom=False, cap_top=False))
    out.append(K.gcyl("clock_back", 0.098, -0.002, 0.006, base=(cx, yc, cz - 0.03), axis=(0, 0, 1), segments=28, mat=BRASS))
    out.append(K.gcyl("clock_dial", 0.0715, 0.020, 0.026, base=(cx, yc, cz - 0.03), axis=(0, 0, 1), segments=28, mat=PAINT))
    for k in range(12):
        a = math.radians(30.0 * k)
        w, l = (0.0065, 0.016) if k % 3 == 0 else (0.0035, 0.009)
        t = K.gbox("ck", (-w, 0.068 - l, 0.0), (w, 0.068, 0.004), BRASS, 0.0)
        t.data.transform(Matrix.Translation((cx, yc, cz - 0.03 + 0.026)) @ Matrix.Rotation(-a, 4, "Z"))
        out.append(t)
    th_h, th_m = (3 + 17 / 60.0) * 30.0, 17 * 6.0

    def rot(pts, ang):
        a = -math.radians(ang)
        return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for (x, y) in pts]
    out.append(K.plate("ck_hour", [rot([(-0.0035, -0.012), (0.0035, -0.012), (0.0045, 0.020), (0.0, 0.040), (-0.0045, 0.020)], th_h)], 0.0015, z0=cz - 0.03 + 0.030,
                       mat=BRASS, bevel=0.0002, drop_bottom=True, loc=(cx, yc, 0.0)))
    out.append(K.plate("ck_min", [rot([(-0.0025, -0.014), (0.0025, -0.014), (0.0015, 0.058), (-0.0015, 0.058)], th_m)], 0.0015, z0=cz - 0.03 + 0.032,
                       mat=BRASS, bevel=0.0002, drop_bottom=True, loc=(cx, yc, 0.0)))
    out.append(K.gcyl("ck_hub", 0.007, cz - 0.03 + 0.026, cz - 0.03 + 0.036, base=(cx, yc, 0.0), axis=(0, 0, 1), segments=8, mat=BRASS))
    for sx in (-1, 1):
        out.append(K.gbox("clock_foot", (cx + sx * 0.060 - 0.012, cy, cz - 0.05), (cx + sx * 0.060 + 0.012, cy + 0.020, cz + 0.02), BRASS, 0.002))
    # inkwell with a pen, a paperweight
    out.append(K.glathe("inkwell", [(0.0, 0.0), (0.050, 0.0), (0.052, 0.012), (0.044, 0.040), (0.026, 0.046), (0.030, 0.052), (0.0, 0.052)],
                        base=(0.42, TOP + 0.004, 0.17), axis=(0, 1, 0), segments=16, mat=BRASS, smooth=50.0))
    out.append(D.rod("pen", (0.42, TOP + 0.090, 0.17), (0.50, TOP + 0.020, 0.115), 0.005, segs=6, mat=BRASS))
    out.append(K.glathe("weight", [(0.0, 0.0), (0.034, 0.0), (0.036, 0.008), (0.026, 0.026), (0.010, 0.034), (0.0, 0.035)],
                        base=(0.28, TOP + 0.004, 0.24), axis=(0, 1, 0), segments=14, mat=BRASS, smooth=50.0))
    return out


def brass_static():
    b = F.MB(BRASS)
    # drawer pulls (a bar on two posts) and keyholes, the leather field's edge strip, kick strips
    for sx in (-1, 1):
        xc = sx * 0.54
        for k in range(3):
            yc = 0.10 + k * 0.215 + 0.0975
            b.bar((xc - 0.06, yc, 0.440), (xc + 0.06, yc, 0.440), 0.016, ref=(0, 1, 0))
            for dx in (-0.045, 0.045):
                b.bar((xc + dx, yc, 0.392), (xc + dx, yc, 0.440), 0.011, ref=(1, 0, 0))
            b.boss((xc + sx * -0.25 * 0.0, yc + 0.045, 0.392), (0, 0, 1), 0.010, 0.004, sides=8)
        b.box((sx * 0.30 - (0.0 if sx > 0 else 0.02), 0.08, 0.385), (sx * 0.30 + (0.02 if sx > 0 else 0.0), 0.74, 0.398))
    b.bar((-0.05, 0.690, 0.395), (0.05, 0.690, 0.395), 0.014, ref=(0, 1, 0))
    b.boss((0.0, 0.690 + 0.0, 0.385), (0, 0, 1), 0.009, 0.004, sides=8)
    # brass edge round the leather field
    for (a, bb) in (((-0.66, TOP, -0.32), (0.66, TOP + 0.005, -0.31)), ((-0.66, TOP, 0.31), (0.66, TOP + 0.005, 0.32)),
                    ((-0.66, TOP, -0.31), (-0.65, TOP + 0.005, 0.31)), ((0.65, TOP, -0.31), (0.66, TOP + 0.005, 0.31))):
        b.box(a, bb)
    b.box((-0.84, 0.0, 0.0), (-0.83, 0.0, 0.0))  # no-op placeholder removed by remove_doubles
    # the coat stand: pole, three splayed feet, a crown with four hooks, a hanger
    sx, sy, sz = STAND_AT
    b.cyl((sx, 0.0, sz), (0, 1, 0), 0.055, 0.05, segs=14)
    b.cyl((sx, 0.05, sz), (0, 1, 0), 0.028, 1.60, segs=10)
    b.cyl((sx, 1.65, sz), (0, 1, 0), 0.05, 0.05, segs=10, r2=0.025)
    for k in range(3):
        a = math.radians(120.0 * k + 90.0)
        b.bar((sx, 0.04, sz), (sx + 0.22 * math.cos(a), 0.02, sz + 0.22 * math.sin(a)), 0.035, ref=(0, 1, 0))
    for k in range(4):
        a = math.radians(90.0 * k + 45.0)
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        b.bar((sx + 0.02 * d.x, 1.66, sz + 0.02 * d.z), (sx + 0.11 * d.x, 1.76, sz + 0.11 * d.z), 0.016, ref=(0, 1, 0))
        b.dome((sx + 0.11 * d.x, 1.77, sz + 0.11 * d.z), 0.014, 0.012, segs=6, normal=(0, 1, 0))
    # the hanger under the coat's shoulders
    b.bar((sx - 0.20, 1.62, sz + 0.17), (sx, 1.69, sz + 0.17), 0.012, ref=(0, 0, 1))
    b.bar((sx, 1.69, sz + 0.17), (sx + 0.20, 1.62, sz + 0.17), 0.012, ref=(0, 0, 1))
    b.bar((sx, 1.69, sz + 0.17), (sx, 1.76, sz + 0.11), 0.008, ref=(1, 0, 0))
    return b.obj("desk_brass")


def build():
    M.reset_scene()
    C.ensure_materials()
    M.material(LEATHER)
    objs = [walnut(), brass_static()] + leather() + lamp_and_clock()
    body = C.merge("booth_desk", objs)
    K.empty("box_mount", BOX_MOUNT)
    K.empty("lamp_light", (LAMP_AT[0] + 0.04, LAMP_AT[1] + 0.50, LAMP_AT[2] + 0.03))
    K.to_blender()
    C.finalize()
    return dict(body=body)


def verify(path):
    req = ["booth_desk", "box_mount", "lamp_light"]
    expect = {"booth_desk": (0.0, 0.0, 0.0), "box_mount": BOX_MOUNT}
    errs = C.verify(path, required=req, identity=["booth_desk"], expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = C.bounds(["booth_desk"])
    print(f"{C.TAG} booth_desk bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects['booth_desk'])}")
    return errs


def qa(args, parts):
    X.qa_env(extra=[])
    C.qa_import("booth", (0.0, 0.0, -13.0), 0.0, prefix="qa_booth_")
    K.qa_place([parts["body"]], (0.0, 2.0, -13.4), 0.0, name="qa_desk_root")
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))
    # the QA cameras look through the front glass: hide it in the closeups so reflections do not fog the picture
    X.vis("qa_booth_", True)

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
        K.light("booth_lamp", "POINT", (0.0, 4.25, -12.9), 160.0, "FFD9A0", radius=0.1)
        K.light("desk_lamp", "POINT", (-0.58, 3.28, -13.6), 40.0, "FFE2B0", radius=0.05)
    if C.want(args, "1"):          # from the hall through the glass
        cam, tgt, fov = (0.0, 3.4, -9.8), (-0.2, 2.9, -13.4), 46
        lit(cam, 40.0, 1.0)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # inside the booth (behind the glass): the desk, the lamp, the clock and the coat
        cam, tgt, fov = (1.5, 3.55, -12.4), (-0.5, 2.75, -13.7), 66
        lit(cam, 40.0, 1.0)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)


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
