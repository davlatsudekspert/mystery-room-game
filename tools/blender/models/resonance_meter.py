"""resonance_meter.glb — Strand's handheld resonance meter (Chapter 3 M8; meter case in his office, then a tool).

A black Bakelite handheld meter, 85 x 150 x 40 mm with rounded edges. The upper front carries a round dial:
a brass bezel round a cream enamel face with a scale arc, 7 major and 6 minor ticks and the readings 1-7 in
3D numerals, a brass rest-stop pin at the left and the black `needle` under a brass pivot cap. Below the dial a
brass push button and Strand's mark (ring and meridian) inlaid in brass; four brass screws. On top a brass
ferrule and probe rod ending in a small tuning fork (`probe_tip` between the tine tips). A black leather wrist
strap runs through a brass ring at the bottom left corner and lies folded up against the back.
Parts (own objects, identity at rest):
- `needle`: pivot at the dial's needle pivot, rotates about local +Z (Godot; the axis faces the viewer).
  Identity = the left stop, pointing at polar 142.5 deg (counter-clockwise from +X as the player sees the face).
  Reading r = -15 deg x r about local +Z (r = 1 -> 127.5 deg ... r = 7 -> 37.5 deg); numeral r sits on that
  angle.
- `probe_tip` (empty): the point between the probe fork's tine tips.
Materials: M_Bakelite, M_Enamel_Cream, M_Brass_Aged (3, see docs/models/ch3_g.md "Deviations").
Stands upright, face +Z (Godot). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/resonance_meter.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch3_items as G  # noqa: E402

NAME = "resonance_meter"
BK, CR, BR = "M_Bakelite", "M_Enamel_Cream", "M_Brass_Aged"
BW, BH, BD = 0.085, 0.150, 0.040
YF = -BD / 2                        # front plane (Blender y)
DZ, RW = 0.030, 0.031               # dial centre height and window radius
PZ = DZ - 0.019                     # needle pivot height
R_NUM, R_TICK0, R_TICK1, R_ARC = 0.0305, 0.0210, 0.0252, 0.0204
REST = 142.5
TOP = BH / 2


def polar(theta_deg, r):
    t = math.radians(theta_deg)
    return (r * math.cos(t), PZ + r * math.sin(t))


def radial_bar(theta_deg, r0, r1, w):
    t = math.radians(theta_deg)
    ux, uz = math.cos(t), math.sin(t)
    vx, vz = -uz, ux
    return [(ux * a + vx * b, PZ + uz * a + vz * b) for (a, b) in ((r0, -w / 2), (r0, w / 2), (r1, w / 2), (r1, -w / 2))]


def body():
    b = L.curve_solid(NAME, [L.rounded_rect(BW, BH, 0.0120, 5)], BD, bevel=0.0040, bevel_res=2, mat=BK)
    L.to_front(b, y_back=BD / 2)
    return b


def dial():
    parts = []
    ro, ri = RW + 0.0045, RW
    bez = D.revolve("bezel", [(ri, 0.0), (ro - 0.0004, 0.0), (ro, 0.0006), (ro - 0.0006, 0.0022),
                              (ri + 0.0012, 0.0026), (ri, 0.0018)],
                    direction=(0, -1, 0), loc=(0.0, YF + 0.0004, DZ), segments=40, mat=BR,
                    cap_bottom=False, cap_top=False)
    parts.append(bez)
    parts.append(L.flat_front("dial_face", [L.circle(RW, 40)], 0.0, YF - 0.0002, DZ, mat=CR))
    yi = YF - 0.00035
    arc_o = [polar(REST - 15 - 90 * i / 18, R_ARC + 0.00028) for i in range(19)]
    arc_i = [polar(REST - 105 + 90 * i / 18, R_ARC - 0.00028) for i in range(19)]
    parts.append(L.flat_front("scale_arc", [arc_o + arc_i], 0.0, yi, 0.0, mat=BK))
    for r in range(1, 8):
        th = REST - 15 * r
        parts.append(L.flat_front(f"tick_{r}", [radial_bar(th, R_TICK0, R_TICK1, 0.0008)], 0.0, yi, 0.0, mat=BK))
        nx, nz = polar(th, R_NUM)
        t = L.text_flat(f"num_{r}", str(r), 0.0068, font=L.FONT_SANS_B, res=2, mat=BK)
        t.data.transform(Matrix.Translation((0.0, -0.0068 * 0.05, 0.0)))
        L.to_front(t, y_back=yi, x=nx, z=nz)
        parts.append(t)
        if r < 7:
            parts.append(L.flat_front(f"minor_{r}", [radial_bar(th - 7.5, R_ARC, R_TICK1 - 0.0016, 0.0005)], 0.0, yi,
                                      0.0, mat=BK))
    # rest-stop pin just beyond the rest position, and the needle's pivot cap
    sx, sz = polar(REST + 6.0, 0.0175)
    pin = D.revolve("stop_pin", [(0.0, 0.0), (0.0008, 0.0), (0.0008, 0.0022), (0.0006, 0.0028), (0.0, 0.0028)],
                    direction=(0, -1, 0), loc=(sx, YF - 0.0002, sz), segments=8, mat=BR)
    cap = D.revolve("cap", [(0.0, 0.0), (0.0026, 0.0), (0.0026, 0.0008), (0.0018, 0.0016), (0.0, 0.0019)],
                    direction=(0, -1, 0), loc=(0.0, YF - 0.0007, PZ), segments=16, mat=BR)
    return parts + [pin, cap]


def lower_front():
    S = G.symbols()
    parts = []
    btn = D.revolve("button", [(0.0, 0.0), (0.0078, 0.0), (0.0078, 0.0012), (0.0066, 0.0016), (0.0060, 0.0016),
                               (0.0060, 0.0034), (0.0052, 0.0042), (0.0, 0.0044)],
                    direction=(0, -1, 0), loc=(0.0, YF + 0.0003, -0.024), segments=16, mat=BR)
    parts.append(btn)
    if S is not None:
        # one flat fill per piece (the ring and the three meridian pieces touch: a single even-odd fill of all
        # loops mis-fills where their outlines meet)
        mk = M.join([L.flat_shape(f"mark_{i}", sh, mat=BR) for i, sh in enumerate(S.shapes("mark", 0.0150))], "mark")
        L.to_front(mk, y_back=YF - 0.0002, z=-0.052)
        parts.append(mk)
    for sx in (-1, 1):
        for szv in (-1, 1):
            parts.append(L.screw("screw", 0.0022, (sx * 0.0315, YF, szv * 0.0625 if szv > 0 else -0.0635),
                                 normal=(0, -1, 0), mat=BR, slot_angle=0.5 + 0.3 * sx * szv, segs=10,
                                 slot_mat=BK))
    return parts


def probe():
    z0 = TOP - 0.0012
    prof = [(0.0, 0.0), (0.0068, 0.0), (0.0068, 0.0040), (0.0060, 0.0052), (0.0040, 0.0064), (0.0032, 0.0090),
            (0.0021, 0.0102), (0.0021, 0.0440), (0.0026, 0.0446), (0.0026, 0.0470), (0.0016, 0.0478), (0.0, 0.0480)]
    rod = D.revolve("probe_rod", prof, direction=(0, 0, 1), loc=(0.0, 0.0, z0), segments=12, mat=BR)
    # small fork at the end of the rod (in the face plane)
    zf = z0 + 0.0470
    ro, ri, top = 0.0034, 0.0014, zf + 0.0170
    pts = [(-ro + 0.0005, top), (-ro, top - 0.0005)]
    for i in range(9):
        a = math.pi + math.pi * i / 8
        pts.append((ro * math.cos(a), zf + 0.0034 + ro * math.sin(a)))
    pts += [(ro, top - 0.0005), (ro - 0.0005, top), (ri + 0.0002, top), (ri, top - 0.0002)]
    for i in range(5):
        a = -math.pi * i / 4
        pts.append((ri * math.cos(a), zf + 0.0050 + ri * math.sin(a)))
    pts += [(-ri, top - 0.0002), (-ri - 0.0002, top)]
    fork = L.curve_solid("probe_fork", [pts], 0.0018, bevel=0.0003, bevel_res=0, mat=BR)
    L.to_front(fork, y_back=0.0009)
    tip = M.empty("probe_tip", loc=(0.0, 0.0, top))
    return [rod, fork], tip


def strap():
    """Leather wrist loop through a brass ring at the bottom left corner, folded up flat against the back (so
    the meter still stands on its base)."""
    rx, rz, y = -0.0290, -BH / 2 + 0.0050, BD / 2 + 0.0010
    ring = M.torus("d_ring", 0.0042, 0.0009, loc=(rx, y, rz), rot=(math.pi / 2, 0, 0), major_seg=12, minor_seg=5,
                   mat=BR)
    ctrl = [(rx + 0.0034, rz + 0.0030), (rx + 0.0085, rz + 0.0140), (rx + 0.0080, rz + 0.0320),
            (rx + 0.0010, rz + 0.0460), (rx - 0.0060, rz + 0.0330), (rx - 0.0070, rz + 0.0150),
            (rx - 0.0034, rz + 0.0030)]
    path = [(p.x, y + 0.0007, p.y) for p in A.catmull([(px, pz, 0.0) for (px, pz) in ctrl], 3)]
    prof = [(-0.0040, -0.0007), (0.0040, -0.0007), (0.0040, 0.0007), (-0.0040, 0.0007)]
    band = A.sweep("strap", prof, path, up=(0, 1, 0), mat=BK)
    keeper = M.box("strap_keeper", (0.0140, 0.0030, 0.0050), loc=(rx + 0.0005, y + 0.0012, rz + 0.0120), mat=BK,
                   bevel=0.0008, segments=1)
    return [ring, band, keeper]


def needle():
    pts = [(-0.00065, -0.0045), (0.00065, -0.0045), (0.00040, 0.0140), (0.00014, 0.0272), (-0.00014, 0.0272),
           (-0.00040, 0.0140)]
    n = L.flat_shape("needle", [pts, L.circle(0.0007, 8, cx=0.0, cy=0.0)], mat=BK)
    tail = L.flat_shape("needle_tail", [L.circle(0.0021, 12, cx=0.0, cy=-0.0040)], mat=BK)
    obj = M.join([n, tail], "needle")
    obj.data.transform(Matrix.Rotation(math.radians(REST - 90.0), 4, "Z"))     # identity -> 142.5 deg
    L.to_front(obj, y_back=YF - 0.0005, x=0.0, z=PZ)
    M.set_origin(obj, (0.0, YF - 0.0005, PZ))
    return obj


def build():
    b = body()
    rods, tip = probe()
    hard = M.join(dial() + lower_front() + rods + strap(), "meter_fittings")
    root = M.join([b, hard], NAME)
    nd = needle()
    M.set_parent(nd, root)
    M.set_parent(tip, root)
    return [root]


def post():
    D.resmooth(bpy.data.objects[NAME], 34.0)


def report():
    G.report_point("needle pivot", obj_name="needle")
    G.report_point("probe_tip", obj_name="probe_tip")
    lo, hi = D.bounds()
    G.report_point("bottom of the item (body base)", point=(0.0, 0.0, lo.z))
    G.report_point("top of the item (probe fork)", point=(0.0, 0.0, hi.z))


def reading(r):
    def fn():
        nd = bpy.data.objects["needle"]
        nd.rotation_mode = "XYZ"
        nd.rotation_euler = (0.0, math.radians(15.0 * r), 0.0)   # Godot -15 r about +Z = Blender +15 r about +Y
    return fn


def main():
    G.item_main(NAME, build, post=post, required=("needle", "probe_tip"), budget=2500, surf_budget=4, mat_budget=3,
                extra_report=report, shots=[
                    ("", (0.21, -0.45, 0.20), (0.0, 0.0, 0.025), 60),
                    ("_2", (0.0, -0.20, 0.05), (0.0, 0.0, 0.040), 70, reading(4)),
                    ("_3", (0.0, -0.20, 0.05), (0.0, 0.0, 0.040), 70, reading(7)),
                    ("_4", (-0.20, 0.30, 0.12), (0.0, 0.0, 0.012), 60, reading(0)),
                ])


if __name__ == "__main__":
    main()
