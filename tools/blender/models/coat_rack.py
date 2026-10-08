"""coat_rack.glb — Thonet-style bentwood coat stand with Leyla's long wool coat on the front hook
and a felt fedora on the finial.

Origin = floor centre (pole axis). Front faces Blender -Y (Godot +Z). Stand 1.93 m to the finial
(hat on top ~2.0 m); feet span ~0.70 m. Static (no IA_ parts).

Hooks (angles measured from model +X toward +Y, i.e. counter-clockwise seen from above):
  upper scroll hooks at 165, 75, -15, -105 deg, lowest (hanging) point r = 0.212 m, z = 1.698
    -> the 165 deg hook's hanging point is model Blender (-0.205, 0.055, 1.698)
       = Godot model-local (-0.205, 1.698, -0.055); with the lead's placement (2.6, 0, -2.15),
       yaw -30 deg that is room Godot ~(2.45, 1.70, -2.30): FREE for the gas-mask prop.
  lower hooks at -90 (front: carries the coat) and +90 deg, hanging point r = 0.13 m, z = 1.558.
Coat pockets (flap centres, on the coat front): model Blender (+-0.12, -0.26, 1.09); pocket bag just
behind/below each flap at (+-0.12, -0.24, 1.06).

    blender -b --factory-startup -P tools/blender/models/coat_rack.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "coat_rack"
W, F, FE = "M_Wood_Walnut", "M_Fabric", "M_Felt"
UPPER = [165.0, 75.0, -15.0, -105.0]
LOWER = [-90.0, 90.0]
UP_HOOK = [(0.016, 1.815), (0.06, 1.81), (0.115, 1.786), (0.165, 1.743), (0.212, 1.698), (0.240, 1.712),
           (0.249, 1.745), (0.240, 1.772)]
LO_HOOK = [(0.016, 1.625), (0.05, 1.620), (0.09, 1.600), (0.13, 1.558), (0.150, 1.566), (0.157, 1.590),
           (0.150, 1.607)]
LEG = [(0.018, 0.66), (0.05, 0.52), (0.10, 0.36), (0.17, 0.19), (0.24, 0.055), (0.30, 0.012), (0.343, 0.026),
       (0.356, 0.066)]


def radial(path_rz, ang_deg):
    a = math.radians(ang_deg)
    return [(r * math.cos(a), r * math.sin(a), z) for (r, z) in path_rz]


def scroll(name, path_rz, ang, r0, r1, sides=6, knob=0.0105):
    pts = radial(path_rz, ang)
    rad = [r0 + (r1 - r0) * i / (len(pts) - 1) for i in range(len(pts))]
    parts = [A.tube(name, A.catmull(pts, 2), r0, sides=sides, radii=A.resample_radii(pts, rad, 2), mat=W)]
    parts.append(A.sphere_s(name + "_knob", knob, loc=pts[-1], segments=7, rings=4, mat=W))
    return parts


def stand():
    parts = []
    prof = [(0.0, 0.07), (0.015, 0.07), (0.019, 0.08), (0.018, 0.10), (0.022, 0.13), (0.024, 0.50), (0.027, 0.60),
            (0.031, 0.625), (0.031, 0.665), (0.026, 0.69), (0.0235, 0.72), (0.0215, 1.55), (0.027, 1.585),
            (0.027, 1.635), (0.0205, 1.66), (0.0205, 1.78), (0.028, 1.795), (0.028, 1.832), (0.020, 1.85),
            (0.023, 1.86), (0.031, 1.88), (0.033, 1.90), (0.027, 1.918), (0.013, 1.928), (0.0, 1.931)]
    parts.append(A.lathe_s("pole", prof, segments=12, mat=W))
    for k in range(4):
        ang = 45.0 + 90.0 * k
        pts = radial(LEG, ang)
        rad = [0.0155, 0.015, 0.0145, 0.014, 0.0135, 0.013, 0.012, 0.0115]
        parts.append(A.tube(f"leg{k}", A.catmull(pts, 2), 0.014, sides=7, radii=A.resample_radii(pts, rad, 2), mat=W))
        parts.append(A.sphere_s(f"leg_tip{k}", 0.0118, loc=pts[-1], segments=7, rings=4, mat=W))
    # umbrella ring, tangent to the outside of the legs, with brass screws at each leg
    z_ring = 0.26
    r_leg = 0.10 + (0.17 - 0.10) * (0.36 - z_ring) / (0.36 - 0.19)
    rr = r_leg + 0.0138 + 0.0085
    parts.append(A.torus_s("ring", rr, 0.0085, loc=(0, 0, z_ring), major_seg=24, minor_seg=5, mat=W))
    for k in range(4):
        a = math.radians(45.0 + 90.0 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(A.screw(f"ring_screw{k}", 0.0035, tuple(d * (rr + 0.0085) + Vector((0, 0, z_ring))), d,
                             "M_Brass_Aged", 20, segs=6))
    for i, ang in enumerate(UPPER):
        parts += scroll(f"hook_up{i}", UP_HOOK, ang, 0.0105, 0.0085)
    for i, ang in enumerate(LOWER):
        parts += scroll(f"hook_lo{i}", LO_HOOK, ang, 0.0095, 0.008, knob=0.0095)
    return parts


# ------------------------------------------------------------------ coat
# (z, half-width a, half-depth b, centre y, fold amplitude)
COAT_RINGS = [(1.600, 0.045, 0.036, -0.148, 0.0), (1.565, 0.072, 0.052, -0.160, 0.0),
              (1.520, 0.140, 0.064, -0.172, 0.002), (1.460, 0.196, 0.074, -0.180, 0.003),
              (1.390, 0.210, 0.080, -0.185, 0.005), (1.250, 0.198, 0.079, -0.187, 0.007),
              (1.100, 0.204, 0.082, -0.189, 0.010), (0.930, 0.222, 0.086, -0.191, 0.016),
              (0.760, 0.240, 0.091, -0.193, 0.022), (0.620, 0.252, 0.094, -0.195, 0.028)]
N_RING = 32
SUPER_N = 2.2


def coat_ring(z, a, b, yc, fold, k_ring):
    pts = []
    n = SUPER_N
    v_neck = max(0.0, (z - 1.30) / 0.30)                  # lapel V opens towards the neck
    last = k_ring == len(COAT_RINGS) - 1
    for i in range(N_RING):
        t = 2 * math.pi * i / N_RING - math.pi / 2           # start at the front (-y)
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2 / n), c)
        y = yc + b * math.copysign(abs(s) ** (2 / n), s)
        # vertical drape folds, slowly twisting with height, strongest on the front/back panels
        ph = 0.6 + 0.9 * (1.6 - z)
        f = fold * (math.sin(6 * t + ph) + 0.45 * math.sin(11 * t - 2 * ph)) * (0.55 + 0.45 * abs(s))
        x += f * c
        y += f * s
        # front edge: a crease at the centre front that widens into the lapel V near the neck
        da = abs(t + math.pi / 2)
        w = math.radians(7 + 22 * v_neck)
        if da < w:
            y += 0.010 * (1 - da / w) * (0.4 + v_neck)
        zz = z + (0.012 * math.sin(3 * t + 0.4) if last else 0.0)
        pts.append((x, y, zz))
    return pts


def surface_y(x, z):
    """Front surface y of the coat at (x, z) (interpolated rings, no folds)."""
    for (z0, a0, b0, y0, _), (z1, a1, b1, y1, _) in zip(COAT_RINGS[1:], COAT_RINGS[2:]):
        if z1 <= z <= z0:
            t = (z0 - z) / (z0 - z1)
            a, b, yc = a0 + (a1 - a0) * t, b0 + (b1 - b0) * t, y0 + (y1 - y0) * t
            n = SUPER_N
            u = min(1.0, abs(x) / a)
            return yc - b * (1 - u ** n) ** (1 / n)
    return -0.27


def coat():
    parts = []
    rings = [coat_ring(z, a, b, yc, f, k) for k, (z, a, b, yc, f) in enumerate(COAT_RINGS)]
    rings.reverse()                                        # loft bottom -> top
    body = A.loft("coat_body", rings, mat=F, cap_start=True, cap_end=True)
    parts.append(A.hint(body, 70))
    # rolled collar around the neck (higher at the back)
    col_pts = []
    for i in range(16):
        t = 2 * math.pi * i / 16
        col_pts.append((0.090 * math.cos(t), -0.162 + 0.064 * math.sin(t), 1.551 + 0.022 * math.sin(t)))
    collar = A.tube("collar", col_pts, 0.015, sides=6, closed=True, caps=False, mat=F)
    parts.append(collar)
    # sleeves hanging along the sides, slightly forward
    for s in (-1, 1):
        sl = [(s * 0.125, -0.180, 1.43), (s * 0.198, -0.186, 1.37), (s * 0.222, -0.197, 1.22), (s * 0.212, -0.206, 1.00)]
        pts = A.catmull(sl, 3)
        rad = A.resample_radii(sl, [0.036, 0.055, 0.053, 0.049], 3)
        parts.append(A.tube(f"sleeve{s}", pts, 0.055, sides=10, radii=rad, mat=F))
        cuff = A.torus_s(f"cuff{s}", 0.050, 0.0075, loc=(s * 0.2115, -0.2065, 1.006), major_seg=10, minor_seg=4, mat=F)
        d = (Vector(sl[-1]) - Vector(sl[-2])).normalized()
        cuff.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
        parts.append(cuff)
    # pocket flaps and buttons on the front
    for s in (-1, 1):
        x = s * 0.12
        y = surface_y(x, 1.10)
        flap = M.box(f"pocket_flap{s}", (0.150, 0.0055, 0.050), loc=(0, 0, 0), mat=F, bevel=0.0022, segments=1)
        yaw = math.atan2(surface_y(x + 0.02, 1.10) - surface_y(x - 0.02, 1.10), 0.04)
        flap.data.transform(Matrix.Rotation(math.radians(4), 4, "X"))
        flap.data.transform(Matrix.Rotation(yaw, 4, "Z"))
        flap.location = (x, y - 0.002, 1.088)
        parts.append(flap)
    for z in (1.34, 1.225, 1.11, 0.995):
        y = surface_y(0.03, z)
        parts.append(A.cyl_s(f"button{z}", 0.0105, 0.006, loc=(0.03, y - 0.002, z), rot=(math.pi / 2, 0, 0), verts=8,
                             mat="M_Bakelite", bevel=0.0015, segments=1))
    # hanging loop over the front lower hook
    loop = [(-0.012, -0.112, 1.585), (-0.01, -0.13, 1.575), (0.0, -0.140, 1.552), (0.01, -0.13, 1.575),
            (0.012, -0.112, 1.585)]
    parts.append(A.tube("coat_loop", loop, 0.004, sides=5, mat=F))
    return parts


# ------------------------------------------------------------------ hat
def hat():
    parts = []
    crown = A.lathe_s("hat_crown", [(0.0, 0.096), (0.022, 0.101), (0.044, 0.106), (0.062, 0.107), (0.074, 0.104),
                                    (0.082, 0.096), (0.086, 0.078), (0.088, 0.045), (0.089, 0.0)], segments=24, mat=FE)
    A.hint(crown, 80)
    for v in crown.data.vertices:
        if v.co.z > 0.05:
            a = math.atan2(v.co.y, v.co.x)
            # centre dent along the front-back axis + front pinch
            v.co.z -= 0.022 * max(0.0, 1 - abs(v.co.x) / 0.05) * (v.co.z - 0.05) / 0.057
            if v.co.y < 0:
                v.co.x *= 1 - 0.18 * (-math.sin(a)) * (v.co.z - 0.05) / 0.06
    crown.data.transform(Matrix.Diagonal((1.0, 1.12, 1.0, 1.0)))
    parts.append(crown)
    band = A.lathe_loop("hat_band", [(0.0885, 0.006), (0.0915, 0.006), (0.0915, 0.031), (0.0885, 0.031)], segments=20,
                        mat=F)
    band.data.transform(Matrix.Diagonal((1.0, 1.12, 1.0, 1.0)))
    parts.append(A.hint(band, 60))
    parts.append(M.box("hat_bow", (0.004, 0.022, 0.022), loc=(0.093, 0.035, 0.019), mat=F, bevel=0.002, segments=1))
    brim = A.lathe_loop("hat_brim", [(0.084, 0.0), (0.135, -0.001), (0.162, 0.007), (0.166, 0.013),
                                     (0.160, 0.013), (0.135, 0.005), (0.084, 0.005)], segments=28, mat=FE)
    for v in brim.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        a = math.atan2(v.co.y, v.co.x)
        k = max(0.0, (r - 0.084) / 0.082) ** 2
        v.co.z += 0.022 * math.cos(a) ** 2 * k - 0.010 * max(0.0, -math.sin(a)) * k   # sides up, front snapped down
    brim.data.transform(Matrix.Diagonal((1.0, 1.12, 1.0, 1.0)))
    parts.append(A.hint(brim, 60))
    return parts


def build():
    M.reset_scene()
    A.prepare_materials()
    M.material("M_Felt", color="3A3A3A", rough=1.0)      # QA preview = M_Felt.tres albedo
    parts = stand()
    hat_parts = hat()
    A.presmooth(hat_parts)
    h = M.join(hat_parts, "hat")
    h.data.transform(Matrix.Rotation(math.radians(9), 4, "X") @ Matrix.Rotation(math.radians(-6), 4, "Y"))
    h.location = (0.004, -0.004, 1.862)
    parts.append(h)
    coat_parts = coat()
    A.presmooth(parts + coat_parts)
    body = M.join(parts, "coat_rack_body")
    cobj = M.join(coat_parts, "coat")
    A.finalize_uv()
    A.grain_uv(body, ratio=1.0)
    print(f"[{NAME}] tris: stand+hat={A.tris(body)} coat={A.tris(cobj)} TOTAL={M.tri_count()}")
    return body, cobj


def main():
    args = M.main_guard()
    build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(32, bounces=4)
    for name, cam, tgt, lens in ((NAME, (1.25, -2.6, 1.45), (0.0, 0.0, 0.98), 35),
                                 (NAME + "_2", (-1.6, 1.3, 1.9), (0.0, 0.0, 1.05), 35),
                                 (NAME + "_3", (0.55, -1.05, 1.75), (0.0, -0.1, 1.5), 40)):
        M.box("QA_floor", (5, 5, 0.02), loc=(0, 0, -0.01), mat="M_Wood_Floor", bevel=0)
        M.render_preview(name, cam, tgt, lens=lens, res=(720, 960), samples=32, world_strength=0.35, lights=A.STUDIO)


main()
