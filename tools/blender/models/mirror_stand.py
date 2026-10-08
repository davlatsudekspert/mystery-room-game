"""mirror_stand.glb — brass optical mirror stand (Lab 7; two instances: A with its mirror, B empty until mounted).

Model space: front = Blender -Y (Godot +Z), base on Z = 0, origin at the base centre (column axis).
Parts (origins at pivots, identity rotation at rest):
  IA_mirror_mount  turntable + U-fork gimbal; origin at the mount centre (0, 0, 1.15) on the column axis;
                   rotates about the vertical axis (Godot +Y). 8 engraved ticks = the 45° puzzle steps,
                   read against the fixed red index on the bearing (front).
    mirror         child of the mount: round 0.22 m mirror, M_Chrome face toward Blender −Y (Godot +Z) at
                   rest, brass back with the Institute emblem, trunnion pins in the fork. Origin = mirror
                   centre = mount centre. Hide it for the empty stand B.
  stand_base       static tripod, column, clamp and bearing.
    blender -b --factory-startup -P tools/blender/models/mirror_stand.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

MZ = 1.15                 # mirror / mount centre height
MR = 0.11                 # mirror radius (0.22 m)
FR = 0.118                # frame outer radius
ARM_X = 0.138             # fork arm centre line
BEAR_TOP = 0.986
TT_TOP = 1.004            # turntable top / fork base bottom
FOOT_R = 0.27
LEG_ANG = (90.0, 210.0, 330.0)


def orient_z_to(obj, d, origin):
    """Mesh built along +Z from 0: rotate +Z onto direction d and move its base to origin."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    obj.data.transform(Matrix.Translation(origin) @ q.to_matrix().to_4x4())


def build_base():
    parts = []
    col = L.lathe2("column", [
        (0.0, 0.268), (0.014, 0.268), (0.030, 0.282), (0.037, 0.298), (0.037, 0.334), (0.029, 0.344),
        (0.0235, 0.358), (0.026, 0.368), (0.0215, 0.380),                               # cast spider hub
        (0.0158, 0.388), (0.0158, 0.690),                                               # lower tube
        (0.0215, 0.694), (0.0245, 0.700), (0.0245, 0.736), (0.0215, 0.742),             # clamp collar
        (0.0128, 0.746), (0.0128, 0.948),                                               # upper tube
        (0.0175, 0.952), (0.031, 0.966), (0.0345, 0.976), (0.0345, 0.982), (0.031, BEAR_TOP),
        (0.0, BEAR_TOP)], segments=16, mat="M_Brass_Aged",
        band_mats=[None] * 15 + ["M_Brass_Polished"] + [None] * 6)
    parts.append(col)
    # clamp knob (knurled, on the right side of the collar)
    kn = L.knurled_knob("clamp", 0.0115, 0.013, ridges=10, mat="M_Brass_Aged", cap_mat="M_Brass_Polished",
                        index_mark=False, simple=True, shaft_r=0.0045, shaft_len=0.006)
    kn.data.transform(Matrix.Translation((0, 0, 0.006)))
    kn.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))      # +Z -> +X
    kn.location = (0.0245, 0.0, 0.718)
    M.apply_transform(kn)
    parts.append(kn)
    # spreader collar
    sc = L.lathe2("spread_collar", [(0.0158, 0.452), (0.0205, 0.455), (0.0205, 0.472), (0.0158, 0.475)], segments=12,
                  mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
    parts.append(sc)
    for a_deg in LEG_ANG:
        a = math.radians(a_deg)
        ca, sa = math.cos(a), math.sin(a)
        p0 = Vector((0.030 * ca, 0.030 * sa, 0.318))
        p1 = Vector((FOOT_R * ca, FOOT_R * sa, 0.024))
        d = p1 - p0
        ln = d.length
        leg = L.lathe2("leg", [(0.0125, -0.004), (0.0125, 0.026), (0.0102, 0.032), (0.0086, ln - 0.034),
                               (0.0108, ln - 0.03), (0.0108, ln), (0.0, ln + 0.003)], segments=10, mat="M_Brass_Aged",
                       band_mats=[None, None, None, "M_Brass_Polished", None, None], cap_bottom=False)
        orient_z_to(leg, d, p0)
        # rubber-shod brass foot
        foot = L.lathe2("foot", [(0.0, 0.0), (0.0175, 0.0), (0.0178, 0.0055), (0.0158, 0.0085), (0.0118, 0.016),
                                 (0.0108, 0.030)], segments=12, mat="M_Brass_Aged",
                        band_mats=["M_Rubber", "M_Rubber", None, None, None], cap_top=False)
        foot.location = (p1.x, p1.y, 0.0)
        M.apply_transform(foot)
        # spreader rod from the collar to 42 % down the leg
        pm = p0 + d * 0.42
        q0 = Vector((0.0205 * ca, 0.0205 * sa, 0.4635))
        rod = L.lathe2("spreader", [(0.0042, 0.0), (0.0042, (pm - q0).length)], segments=6, mat="M_Brass_Aged",
                       cap_bottom=False, cap_top=False)
        orient_z_to(rod, pm - q0, q0)
        clip = L.lathe2("clip", [(0.0, -0.007), (0.0125, -0.007), (0.0125, 0.007), (0.0, 0.007)], segments=8,
                        mat="M_Brass_Polished")
        orient_z_to(clip, d, pm)
        parts += [leg, foot, rod, clip]
    # fixed index mark on the bearing flange (front, Godot +Z)
    parts.append(L.flat_front("index", [[(-0.0026, -0.0022), (0.0026, -0.0022), (0.0, 0.0024)]], 0.0, -0.03465,
                              0.979, mat="M_Enamel_Crimson"))
    return M.join(parts, "stand_base")


def build_mount():
    parts = []
    tt = L.lathe2("turntable", [(0.031, BEAR_TOP + 0.0015), (0.0345, BEAR_TOP + 0.0035), (0.0345, TT_TOP - 0.004),
                                (0.031, TT_TOP), (0.0, TT_TOP)], segments=24, mat="M_Brass_Polished", cap_bottom=False)
    parts.append(tt)
    # 8 engraved ticks on the turntable rim chamfer (45° steps)
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        tk = L.flat_shape("tick", [[(-0.0006, 0.0), (0.0006, 0.0), (0.0006, 0.007), (-0.0006, 0.007)]],
                          mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))          # vertical, facing -Y
        tk.data.transform(Matrix.Translation((0, -0.03455, BEAR_TOP + 0.0045)))
        tk.data.transform(Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        parts.append(tk)
    # U-fork (yoke): drawn in the front plane, 14 mm thick
    t = 0.014
    w_arm = 0.016
    xo, xi = ARM_X + w_arm / 2, ARM_X - w_arm / 2
    zb, zi = TT_TOP, TT_TOP + 0.019
    ro, ri = 0.030, 0.012
    outline = [(-xo, MZ)]
    outline += L.arc_pts(ro, math.pi, 1.5 * math.pi, 5, cx=-xo + ro, cy=zb + ro)
    outline += L.arc_pts(ro, 1.5 * math.pi, 2 * math.pi, 5, cx=xo - ro, cy=zb + ro)[1:]
    outline += [(xo, MZ)]
    outline += L.arc_pts(w_arm / 2, 0.0, math.pi, 6, cx=ARM_X, cy=MZ)[1:-1]
    outline += [(xi, MZ)]
    outline += L.arc_pts(ri, 0.0, -0.5 * math.pi, 4, cx=xi - ri, cy=zi + ri)
    outline += L.arc_pts(ri, -0.5 * math.pi, -math.pi, 4, cx=-xi + ri, cy=zi + ri)[1:]
    outline += [(-xi, MZ)]
    outline += L.arc_pts(w_arm / 2, 0.0, math.pi, 6, cx=-ARM_X, cy=MZ)[1:-1]
    fork = L.curve_solid("fork", [outline], t, bevel=0.0022, bevel_res=1, mat="M_Brass_Aged")
    L.to_front(fork, y_back=t / 2)
    parts.append(fork)
    # trunnion bosses + knurled tilt-lock knobs
    for sx in (-1, 1):
        boss = L.lathe2("boss", [(0.0, -0.011), (0.0125, -0.011), (0.0135, -0.0095), (0.0135, 0.0095), (0.0125, 0.011),
                                 (0.0, 0.011)], segments=14, mat="M_Brass_Polished")
        boss.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        boss.location = (sx * ARM_X, 0.0, MZ)
        M.apply_transform(boss)
        kn = L.knurled_knob("tiltknob", 0.0118, 0.012, ridges=9, mat="M_Brass_Aged", cap_mat="M_Brass_Polished",
                            index_mark=False, simple=True, dome=0.003)
        kn.data.transform(Matrix.Rotation(sx * math.pi / 2, 4, "Y"))    # +Z -> ±X
        kn.location = (sx * (ARM_X + 0.011), 0.0, MZ)
        M.apply_transform(kn)
        parts += [boss, kn]
    mount = M.join(parts, "IA_mirror_mount")
    M.set_origin(mount, (0.0, 0.0, MZ))
    return mount


def build_mirror(mount):
    parts = []
    # brass dish + polished frame lip, built along +Z (front), then turned to face -Y
    prof = [(0.0, -0.0165), (0.056, -0.0165), (0.094, -0.0125), (0.112, -0.0085), (FR, -0.0045), (FR, 0.0035),
            (FR - 0.0035, 0.0068), (MR - 0.0005, 0.0068), (MR - 0.0035, 0.0034), (MR - 0.0052, 0.0026)]
    dish = L.lathe2("dish", prof, segments=40, mat="M_Brass_Aged",
                    band_mats=[None, None, None, None, "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished",
                               "M_Brass_Polished", "M_Brass_Polished"], cap_top=False)
    face = L.flat_shape("face", [L.circle(MR - 0.0045, 40)], mat="M_Chrome", loc=(0, 0, 0.0027))
    M.apply_transform(face)
    # Institute emblem on the back: ring + meridian (engraved inlay), facing -Z (the back)
    em_ring = L.flat_shape("emblem_ring", L.circle_line(0.036, 0.0042, 32), mat="M_Bakelite")
    em_line = L.flat_shape("emblem_line", [[(-0.0021, -0.05), (0.0021, -0.05), (0.0021, 0.05), (-0.0021, 0.05)]],
                           mat="M_Bakelite", loc=(0, 0, -0.00002))
    M.apply_transform(em_line)
    em = M.join([em_ring, em_line], "emblem")
    em.data.transform(Matrix.Rotation(math.pi, 4, "Y"))
    em.location = (0, 0, -0.01665)
    M.apply_transform(em)
    parts += [dish, face, em]
    # back boss + 3 frame screws
    hub = L.lathe2("hub", [(0.0, -0.0225), (0.006, -0.0222), (0.0105, -0.0195), (0.0125, -0.0165)], segments=12,
                   mat="M_Brass_Polished", cap_top=False)
    parts.append(hub)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        parts.append(L.rivet("fscrew", 0.0026, (0.1145 * math.cos(a), 0.1145 * math.sin(a), 0.0068), normal=(0, 0, 1),
                             mat="M_Brass_Aged", segs=6))
    m = M.join(parts, "mirror")
    L.along(m)                                                   # +Z -> -Y
    # trunnion pins into the fork bosses
    pins = []
    for sx in (-1, 1):
        pin = L.lathe2("pin", [(0.0, 0.0), (0.0058, 0.0), (0.0058, 0.016), (0.0, 0.016)], segments=10,
                       mat="M_Brass_Polished")
        pin.data.transform(Matrix.Rotation(sx * math.pi / 2, 4, "Y"))
        pin.location = (sx * (FR - 0.004), 0.0, 0.0)
        M.apply_transform(pin)
        pins.append(pin)
    m = M.join([m] + pins, "mirror")
    m.location = (0.0, 0.0, MZ)
    M.set_parent(m, mount)
    return m


def build():
    build_base()
    mount = build_mount()
    build_mirror(mount)


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("mirror_stand")
    if L.want_render():
        L.qa_render("mirror_stand", (1.35, -1.9, 1.35), (0.0, 0.0, 0.66), lens=40, samples=32)
        L.qa_render("mirror_stand_2", (0.0, -0.75, 1.15), (0.0, 0.0, 1.10), lens=50, samples=32)
        mount = M.bpy.data.objects["IA_mirror_mount"]
        mount.rotation_euler = (0, 0, math.radians(-135.0))
        L.qa_render("mirror_stand_3", (0.55, -0.70, 1.32), (0.0, 0.0, 1.08), lens=45, samples=32)
        mount.rotation_euler = (0, 0, 0)


main()
