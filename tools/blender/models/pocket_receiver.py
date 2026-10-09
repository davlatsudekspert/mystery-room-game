"""pocket_receiver.glb — Leyla's pocket receiver (locker 9; the P6 hot/cold hunt tool).

A dark Bakelite pocket receiver, 75 x 120 x 30 mm (body), with rounded edges. Front, top to bottom: a
chrome-bezelled meter window (54 x 32 mm) with a cream face carrying a scale arc and **5 bar marks**
of rising length (bars 1-3 black, 4-5 red; a stop dot at the rest position), a black `needle` under a
glass; a small chrome name plate with the Institute's mark; a chrome-framed speaker grille with six
chrome bars over grille cloth. Right side: the knurled cream `tuning_knob` thumbwheel (Ø 21 mm)
protruding 7 mm. Left side: an earphone socket. Top: a telescopic chrome antenna (three sections, ball
tip, leaning 10 deg outward) at the right and a leather wrist-strap loop in a chrome keeper at the centre.

Parts (own objects, identity at rest, origin at the pivot):
- `needle`: pivot at the meter pivot; identity points at 12 o'clock (Godot +Y); the code rotates it by
  (40 deg - 16 deg x bars) about local +Z (bars 0..5): +40 deg = rest stop at the left, bar k at
  40 - 16 k deg (24, 8, -8, -24, -40).
- `tuning_knob`: pivot on the wheel axis; turns about local +Z (Godot), i.e. the axis faces the viewer.
Stands upright, face toward Blender -Y (Godot +Z). Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/pocket_receiver.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "pocket_receiver"
BW, BH, BD = 0.075, 0.120, 0.030
YF = -BD / 2                       # front plane
MW, MH, MZ = 0.054, 0.032, 0.030   # meter window size / centre height
PZ = MZ - MH / 2 + 0.0040          # needle pivot height
R_SCALE = 0.0172                   # bar marks start radius
GZ, GW, GH = -0.0275, 0.058, 0.050  # grille centre / size
KX, KZ, KR = BW / 2 - 0.0035, 0.024, 0.0105   # thumbwheel axis x, z and radius
ANT_X = 0.024
STRAP_X = -0.004


def polar(theta_deg, r, cz=PZ):
    """Point on the meter face at needle angle theta (deg from 12 o'clock, + = CCW seen from the front)."""
    t = math.radians(theta_deg)
    return (-r * math.sin(t), cz + r * math.cos(t))


def bar(theta_deg, r0, length, w):
    """Radial bar on the meter face (2D x, z)."""
    t = math.radians(theta_deg)
    ux, uz = -math.sin(t), math.cos(t)          # radial
    vx, vz = uz, -ux                            # tangential
    pts = []
    for (a, b) in ((r0, -w / 2), (r0, w / 2), (r0 + length, w / 2), (r0 + length, -w / 2)):
        pts.append((ux * a + vx * b, PZ + uz * a + vz * b))
    return pts


def body():
    b = L.curve_solid(NAME, [L.rounded_rect(BW, BH, 0.0090, 5)], BD, bevel=0.0035, bevel_res=2, mat="M_Bakelite")
    L.to_front(b, y_back=BD / 2)
    return b


def meter():
    parts = []
    win = L.rrect4(MW, MH, (0.003, 0.008, 0.008, 0.003), 4)
    bez = L.curve_solid("bezel", [L.rrect4(MW + 0.0060, MH + 0.0060, (0.005, 0.011, 0.011, 0.005), 4), win],
                        0.0016, bevel=0.0004, bevel_res=0, mat="M_Chrome")
    L.to_front(bez, y_back=YF + 0.0003, z=MZ)
    parts.append(bez)
    parts.append(L.flat_front("meter_face", [win], 0.0, YF - 0.0001, MZ, mat="M_Enamel_Cream"))
    # scale arc under the bars, from the rest stop (+42) to the full deflection (-42)
    arc_o = [polar(42 - 84 * i / 20, R_SCALE - 0.0010) for i in range(21)]
    arc_i = [polar(-42 + 84 * i / 20, R_SCALE - 0.0016) for i in range(21)]
    parts.append(L.flat_front("scale_arc", [arc_o + arc_i], 0.0, YF - 0.00016, 0.0, mat="M_Bakelite"))
    for k in range(1, 6):
        th = 40 - 16 * k
        mat = "M_Bakelite" if k <= 3 else "M_Enamel_Crimson"
        parts.append(L.flat_front(f"bar_{k}", [bar(th, R_SCALE, 0.0016 + 0.0009 * k, 0.0017)], 0.0, YF - 0.00016, 0.0,
                                  mat=mat))
    sx, sz = polar(40, R_SCALE + 0.0007)
    parts.append(L.flat_front("rest_dot", [L.circle(0.0007, 8, cx=sx, cy=sz)], 0.0, YF - 0.00016, 0.0, mat="M_Bakelite"))
    # glass in front of the needle, inside the bezel
    parts.append(L.flat_front("meter_glass", [win], 0.0, YF - 0.0012, MZ, mat="M_Glass"))
    return parts


def needle():
    pts = [(-0.00062, -0.0042), (0.00062, -0.0042), (0.00030, 0.0150), (0.00012, 0.0222), (-0.00012, 0.0222),
           (-0.00030, 0.0150)]
    n = L.flat_shape("needle", [pts], mat="M_Lacquer_Black")
    cap = L.lathe2("needle_cap", [(0.0019, 0.0), (0.0019, 0.0003), (0.0012, 0.0006), (0.0, 0.0007)], segments=12,
                   mat="M_Chrome", cap_bottom=False)
    cap.location = (0, 0, 0.00005)
    M.apply_transform(cap)
    obj = M.join([n, cap], "needle")
    L.to_front(obj, y_back=YF - 0.0005, x=0.0, z=PZ)
    M.set_origin(obj, (0.0, YF - 0.0005, PZ))
    return obj


def name_plate():
    z = 0.0070
    plate = L.curve_solid("name_plate", [L.rounded_rect(0.030, 0.0062, 0.0015, 3)], 0.0007, bevel=0.0002,
                          bevel_res=0, mat="M_Chrome")
    L.to_front(plate, y_back=YF + 0.0001, z=z)
    ring = L.flat_front("np_mark_ring", L.circle_line(0.0019, 0.00045, n=20), 0.0, YF - 0.00064, z, mat="M_Bakelite")
    bar_ = L.flat_front("np_mark_bar", [L.rounded_rect(0.00045, 0.0050, 0.0001, 1)], 0.0, YF - 0.00066, z,
                        mat="M_Bakelite")
    ticks = []
    for sx in (-1, 1):
        ticks.append(L.flat_front("np_line", [L.rounded_rect(0.0085, 0.00035, 0.0001, 1)], sx * 0.0084, YF - 0.00064, z,
                                  mat="M_Bakelite"))
    return [plate, ring, bar_] + ticks


def grille():
    parts = [L.flat_front("grille_cloth", [L.rounded_rect(GW, GH, 0.004, 3)], 0.0, YF - 0.0001, GZ,
                          mat="M_Grille_Fabric")]
    fr = L.curve_solid("grille_frame", [L.rounded_rect(GW + 0.0040, GH + 0.0040, 0.0060, 3),
                                        L.rounded_rect(GW, GH, 0.0040, 3)], 0.0012, bevel=0.0, mat="M_Chrome")
    L.to_front(fr, y_back=YF + 0.0002, z=GZ)
    parts.append(fr)
    for i in range(6):
        z = GZ - GH / 2 + GH * (i + 0.5) / 6
        parts.append(M.box("grille_bar", (GW - 0.0010, 0.0010, 0.0024), loc=(0, YF - 0.0006, z), mat="M_Chrome",
                           bevel=0.0003, segments=1))
    return parts


def tuning_knob():
    prof = [(0.0, -0.0030), (KR - 0.0008, -0.0030), (KR, -0.0022, "k"), (KR, 0.0022, "k"), (KR - 0.0008, 0.0030),
            (0.0, 0.0030)]
    k = D.revolve("tuning_knob", prof, direction=(0, -1, 0), loc=(KX, -0.0015, KZ), segments=32, knurl=0.00045,
                  mat="M_Enamel_Cream")
    dot = L.flat_front("knob_dot", [L.circle(0.0010, 8)], KX + 0.0072, -0.0015 - 0.00305, KZ, mat="M_Enamel_Crimson")
    obj = M.join([k, dot], "tuning_knob")
    M.set_origin(obj, (KX, -0.0015, KZ))
    return obj


def side_details():
    # earphone socket on the left side (facing -X)
    jack = D.revolve("jack", [(0.0, -0.0004), (0.0011, -0.0004), (0.0011, 0.0), (0.0024, 0.0), (0.0024, 0.0005),
                              (0.0018, 0.0009), (0.0011, 0.0009), (0.0011, 0.0002)],
                     direction=(-1, 0, 0), loc=(-BW / 2, 0.0, 0.034), segments=12, mat="M_Chrome",
                     cap_bottom=False, cap_top=False)
    # battery door on the back: a thin parting line and a coin-slot screw (facing +Y)
    door = L.flat_shape("battery_door", L.outline_ring(0.056, 0.072, 0.0040, 0.0006), mat="M_Lacquer_Black")
    L.to_front(door, y_back=BD / 2 + 0.00005, z=-0.012)
    door.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
    screw = L.screw("door_screw", 0.0028, (0.0, BD / 2, -0.012 - 0.036 + 0.0050), normal=(0, 1, 0),
                    mat="M_Chrome", slot_angle=0.4, segs=12, slot_mat="M_Lacquer_Black")
    return [jack, door, screw]


def antenna():
    prof = [(0.0034, -0.0020), (0.0034, 0.0030), (0.0028, 0.0040), (0.0028, 0.0240), (0.0023, 0.0245),
            (0.0021, 0.0250), (0.0021, 0.0400), (0.0017, 0.0405), (0.0015, 0.0410), (0.0015, 0.0510),
            (0.0021, 0.0514), (0.0026, 0.0530), (0.0022, 0.0548), (0.0, 0.0556)]
    ant = L.lathe2("antenna", prof, segments=10, mat="M_Chrome")
    ant.data.transform(Matrix.Translation((ANT_X, 0.0, BH / 2 - 0.0010)) @ Matrix.Rotation(math.radians(10), 4, "Y"))     # leans out to +X
    base = M.box("antenna_base", (0.0090, 0.0090, 0.0030), loc=(ANT_X, 0.0, BH / 2 + 0.0005), mat="M_Chrome",
                 bevel=0.0008, segments=1)
    return [ant, base]


def strap():
    x0, z0 = STRAP_X, BH / 2 + 0.0042
    ctrl = [(x0 + 0.0016, z0), (x0 + 0.0052, z0 + 0.0090), (x0 + 0.0072, z0 + 0.0200), (x0 + 0.0050, z0 + 0.0290),
            (x0, z0 + 0.0322), (x0 - 0.0050, z0 + 0.0290), (x0 - 0.0072, z0 + 0.0200), (x0 - 0.0052, z0 + 0.0090),
            (x0 - 0.0016, z0)]
    path = [(p.x, 0.0, p.y) for p in A.catmull([(px, pz, 0.0) for (px, pz) in ctrl], 3)]
    prof = [(-0.0006, -0.0031), (0.0006, -0.0031), (0.0006, 0.0031), (-0.0006, 0.0031)]
    band = A.sweep("strap", prof, path, up=(0, 1, 0), mat="M_Leather")
    keeper = M.box("strap_keeper", (0.0068, 0.0076, 0.0044), loc=(x0, 0.0, BH / 2 + 0.0030), mat="M_Chrome",
                   bevel=0.0010, segments=1)
    return [band, keeper]


def build():
    b = body()
    parts = meter() + name_plate() + grille() + side_details() + antenna() + strap()
    hard = M.join(parts, "receiver_details")
    M.set_parent(hard, b)
    nd = needle()
    M.set_parent(nd, b)
    kn = tuning_knob()
    M.set_parent(kn, b)
    return [b]


def post():
    D.resmooth(bpy.data.objects["tuning_knob"], 20.0)


def pose_bars(bars):
    def fn():
        nd = bpy.data.objects["needle"]
        nd.rotation_mode = "XYZ"
        # Godot local +Z = Blender -Y: a positive Godot angle is a negative rotation about Blender +Y
        nd.rotation_euler = (0.0, -math.radians(40 - 16 * bars), 0.0)
    return fn


def main():
    C.item_main(NAME, build, post=post, required=("needle", "tuning_knob"), shots=[
        ("", (0.15, -0.30, 0.13), (0.0, 0.0, 0.028), 60),
        ("_2", (0.0, -0.13, 0.03), (0.0, 0.0, 0.025), 60, pose_bars(0)),
        ("_3", (0.0, -0.13, 0.03), (0.0, 0.0, 0.025), 60, pose_bars(4)),
        ("_4", (0.20, 0.26, 0.17), (0.0, 0.0, 0.028), 60, pose_bars(0)),
    ])


if __name__ == "__main__":
    main()
