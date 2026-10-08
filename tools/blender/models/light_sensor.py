"""light_sensor.glb — the door's "light lock": brass photocell eye with an iris, on a wall plate (Lab 7, east wall).

Model space: front = Blender -Y (Godot +Z). BACK PLANE at Blender Y = 0; origin at the centre of the back
plane, on the eye axis (the lead places it at Godot (3.0, 1.15, 0.12), yaw -90°, so the eye sits at the
beam height 1.15).
Parts:
  sensor_eye   ground-glass screen (M_Glass_Frosted), 0.163 m disc facing Blender -Y, centred on the axis
               (origin at the glass centre, Blender (0, -0.050, 0)). Glow it when the beam arrives.
  sensor_body  static: wall plate, brass housing with the engraved Institute emblem (ring + meridian) on the
               rim, 8 overlapping brass iris blades, selenium cell behind the glass, cable gland.
    blender -b --factory-startup -P tools/blender/models/light_sensor.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

PLATE = 0.30
PLATE_T = 0.012
R_HOUSE = 0.128      # brass housing radius (0.256 m)
Z_FRONT = 0.064      # rim face (distance in front of the wall)
R_RIM_IN = 0.110     # rim inner edge; the iris blades fill R_EYE..R_RIM_IN
R_EYE = 0.0815
Z_EYE = 0.050
Z_IRIS = 0.0545
N_BLADES = 8


def front(obj):
    """Lathe/2D built along +Z (distance from the wall) -> protrude toward -Y."""
    L.along(obj)


def build_body():
    """Everything is built with +Z = distance in front of the wall (2D y = up), then turned once to face -Y."""
    parts = []
    pl = L.curve_solid("plate", [L.rounded_rect(PLATE, PLATE, 0.03, 5)], PLATE_T, bevel=0.0032, bevel_res=1,
                       mat="M_Steel_Dark", drop_bottom=True)
    parts.append(pl)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(L.screw("pscrew", 0.0055, (sx * 0.124, sz * 0.124, PLATE_T), normal=(0, 0, 1),
                                 slot_angle=0.6 + sx * 0.5 + sz * 0.2, segs=8))
    R = R_HOUSE
    prof = [(R + 0.0035, PLATE_T - 0.0005), (R + 0.0035, PLATE_T + 0.0035), (R - 0.0005, PLATE_T + 0.0068),
            (R - 0.007, PLATE_T + 0.008), (R - 0.007, 0.043), (R - 0.0045, 0.0445), (R - 0.0045, 0.0475),
            (R - 0.007, 0.049), (R - 0.0025, 0.0505), (R, 0.0525), (R, 0.0605), (R - 0.0025, Z_FRONT),
            (R_RIM_IN + 0.0015, Z_FRONT),
            (R_RIM_IN, Z_FRONT - 0.0015), (R_RIM_IN, Z_EYE + 0.0015), (R_EYE + 0.004, Z_EYE + 0.0015),
            (R_EYE + 0.004, Z_EYE - 0.0005)]
    bands = [None] * 4 + ["M_Brass_Polished"] * 3 + [None] * 4 + ["M_Brass_Polished"] * 1 + [None] * 4
    parts.append(L.lathe2("housing", prof, segments=56, mat="M_Brass_Aged", band_mats=bands, cap_bottom=False,
                          cap_top=False))
    # --- engraved Institute emblem on the rim face: ring + meridian (top and bottom), plus 15° ticks
    zr = Z_FRONT + 0.00008
    parts.append(L.flat_shape("em_ring", L.circle_line(0.1172, 0.0019, 56), mat="M_Enamel_Cream", loc=(0, 0, zr)))
    for sz in (-1, 1):
        parts.append(L.flat_shape("em_bar", [[(-0.0013, sz * (R_RIM_IN + 0.0019)), (0.0013, sz * (R_RIM_IN + 0.0019)),
                                              (0.0013, sz * (R_HOUSE - 0.0034)), (-0.0013, sz * (R_HOUSE - 0.0034))]],
                                  mat="M_Enamel_Cream", loc=(0, 0, zr + 0.00002)))
    for k in range(24):
        if k % 6 == 0:
            continue
        a = k * math.pi / 12
        ln = 0.0032 if k % 2 == 0 else 0.002
        r0 = 0.1205
        tk = L.flat_shape("tick", [[(-0.00045, r0), (0.00045, r0), (0.00045, r0 + ln), (-0.00045, r0 + ln)]],
                          mat="M_Bakelite", loc=(0, 0, zr))
        tk.data.transform(Matrix.Rotation(a, 4, "Z"))
        parts.append(tk)
    # --- iris: 8 brass blades, each tilted about its radial axis so they overlap cyclically
    r_o = R_RIM_IN - 0.0005
    half = math.acos(R_EYE / r_o) + math.radians(9)
    for k in range(N_BLADES):
        phi = k * 2 * math.pi / N_BLADES + math.radians(11.0)
        pts = [(r_o * math.cos(phi + half - 2 * half * i / 8), r_o * math.sin(phi + half - 2 * half * i / 8))
               for i in range(9)]
        n = Vector((math.cos(phi), math.sin(phi)))
        p_a, p_b = Vector(pts[-1]), Vector(pts[0])
        inner = []
        for i in range(1, 6):          # concave inner edge, tangent to the aperture circle at phi
            u = i / 6.0
            p = p_a.lerp(p_b, u)
            bump = 1.0 - (2 * u - 1) ** 2
            p = p - n * (p.dot(n) - R_EYE) * bump + n * 0.0026 * bump
            inner.append((p.x, p.y))
        bl = L.curve_solid(f"blade{k}", [pts + inner], 0.0007, bevel=0.0002, bevel_res=0,
                           mat="M_Brass_Polished" if k % 2 else "M_Brass_Aged")
        bl.data.transform(Matrix.Rotation(math.radians(2.4), 4, Vector((math.cos(phi), math.sin(phi), 0.0))))
        bl.data.transform(Matrix.Translation((0, 0, Z_IRIS - 0.0004)))
        parts.append(bl)
    # --- selenium cell behind the glass: dark disc with silver collector rings and bus bar
    parts.append(L.flat_shape("cell", [L.circle(R_EYE + 0.004, 32)], mat="M_Steel_Dark", loc=(0, 0, 0.032)))
    for rr in (0.022, 0.042, 0.062):
        parts.append(L.flat_shape("cell_ring", L.circle_line(rr, 0.0022, 32), mat="M_Chrome", loc=(0, 0, 0.0321)))
    parts.append(L.flat_shape("cell_bar", [[(-0.0016, -0.065), (0.0016, -0.065), (0.0016, 0.065), (-0.0016, 0.065)]],
                              mat="M_Chrome", loc=(0, 0, 0.0322)))
    parts.append(L.lathe2("sleeve", [(R_EYE + 0.004, 0.032), (R_EYE + 0.004, Z_EYE - 0.0005)], segments=32,
                          mat="M_Steel_Dark", cap_bottom=False, cap_top=False))
    # --- cable gland under the housing and a braided cable into the wall (Z-space: y = up, z = out)
    gl = L.lathe2("gland", [(0.0105, 0.0), (0.0105, 0.006), (0.0085, 0.0085), (0.0085, 0.016), (0.0068, 0.0175),
                            (0.0068, 0.024)], segments=10, mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
    gl.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))       # +Z -> -Y (down in Z-space)
    gl.location = (0.0, -(R_HOUSE - 0.0075), 0.033)
    cable = L.tube("cable", [(0.0, -0.138, 0.033), (0.0, -0.156, 0.033), (0.0, -0.166, 0.027),
                             (0.0, -0.172, 0.014), (0.0, -0.174, -0.002)], 0.0058, mat="M_Fabric", bevel_res=1, res_u=3)
    parts += [gl, cable]
    body = M.join(parts, "sensor_body")
    front(body)
    return body


def build_eye():
    eye = L.flat_shape("sensor_eye", [L.circle(R_EYE + 0.0035, 40)], mat="M_Glass_Frosted")
    front(eye)
    eye.location = (0.0, -Z_EYE, 0.0)
    return eye


def build():
    build_body()
    build_eye()


def shot(name, cam, target, lens, samples=32):
    L.qa_wall(0.0, 0.0, w=1.6, h=1.2)
    L.qa_render(name, cam, target, lens=lens, floor_z=None, samples=samples)


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("light_sensor")
    if L.want_render():
        shot("light_sensor", (0.34, -0.55, 0.20), (0.0, -0.03, 0.0), 45)
        shot("light_sensor_2", (0.0, -0.62, 0.0), (0.0, 0.0, 0.0), 50)


main()
