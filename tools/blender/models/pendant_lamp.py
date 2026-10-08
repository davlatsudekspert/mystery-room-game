"""pendant_lamp.glb — 1950s institutional pendant: green enamel dome shade (white enamel inside),
brass gallery + bakelite socket, cloth cord, brass ceiling canopy.

Origin = ceiling attachment point (top of the canopy); everything hangs down along -Z (Godot -Y).
Place at the ceiling position, e.g. Godot (-0.6, 3.4, -0.6).
Parts: `bulb` (M_Emissive_Warm), empty `light_origin` at the bulb centre; rest static.

    blender -b --factory-startup -P tools/blender/models/pendant_lamp.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402

NAME = "pendant_lamp"

SHADE_TOP = -0.955     # neck of the shade (meets the brass gallery)
RIM_Z = -1.13          # bottom rim of the shade
BULB_C = -1.086        # bulb glass centre


def shade():
    # outer surface of the dome, top (neck) -> rim
    outer = [(0.046, SHADE_TOP), (0.075, -0.961), (0.110, -0.977), (0.142, -1.000),
             (0.168, -1.028), (0.188, -1.060), (0.201, -1.093), (0.209, -1.120),
             (0.211, RIM_Z + 0.004)]
    t = 0.0035
    # inner surface: outer offset by the wall thickness against the outward (up/out) normal
    inner = []
    for i, (r, z) in enumerate(outer):
        p0 = outer[max(0, i - 1)]
        p1 = outer[min(len(outer) - 1, i + 1)]
        dr, dz = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dr, dz)
        nr, nz = -dz / ln, dr / ln          # outward normal for a top->bottom profile
        inner.append((r - nr * t, z - nz * t))
    # rolled rim bead joining outer -> inner around the bottom
    rr = 0.0042
    cx, cz = 0.2115 - rr * 0.5, RIM_Z + rr
    bead = A.arc(cx, cz, rr, 20, -200, 4)
    loop = outer + bead[1:-1] + list(reversed(inner))
    o = A.lathe_loop("shade", loop, segments=32, mat="M_Steel_Painted")
    # inner faces (normals towards the axis / downwards) get the white enamel
    def pick(c, n, cur):
        radial = M.Vector((c.x, c.y, 0.0))
        if radial.length < 1e-6:
            return None
        radial.normalize()
        return "M_Enamel_Cream" if (n.dot(radial) * 0.8 + n.z * 0.6) < -0.05 else "M_Steel_Painted"
    A.mat_by_face(o, pick)
    return o


def build():
    M.reset_scene()
    A.prepare_materials()
    parts = []

    # ---- ceiling canopy (brass) with a small cord-grip nut
    canopy = M.lathe("canopy", [(0.010, -0.050), (0.022, -0.049), (0.040, -0.042), (0.056, -0.030),
                                (0.065, -0.016), (0.069, -0.007), (0.070, -0.002), (0.066, 0.0)],
                     segments=28, mat="M_Brass_Aged")
    parts.append(canopy)
    grip = M.lathe("canopy_grip", [(0.0, -0.078), (0.006, -0.078), (0.0085, -0.074), (0.0085, -0.062),
                                   (0.0095, -0.060), (0.0095, -0.054), (0.008, -0.050)],
                   segments=12, mat="M_Brass_Aged")
    parts.append(grip)
    # two screws on the canopy
    for i, a in enumerate((0.0, math.pi)):
        n = M.Vector((math.cos(a) * 0.55, math.sin(a) * 0.55, -0.83)).normalized()
        parts.append(A.screw(f"canopy_screw{i}", 0.0045,
                             (math.cos(a) * 0.050, math.sin(a) * 0.050, -0.036), n, "M_Brass_Aged", 30 + 50 * i))

    # ---- cloth cord
    cord = A.tube("cord", [(0, 0, -0.075), (0, 0, -0.832)], 0.0036, sides=8, mat="M_Fabric")
    parts.append(cord)

    # ---- brass gallery / fitter with cord grip and ribs
    fitter = M.lathe("fitter", [
        (0.0, -0.962), (0.050, -0.962), (0.053, -0.957), (0.051, -0.950), (0.036, -0.946),
        (0.027, -0.940), (0.0285, -0.925), (0.0285, -0.918), (0.026, -0.915), (0.026, -0.880),
        (0.0285, -0.875), (0.026, -0.867), (0.020, -0.857), (0.0105, -0.850), (0.0105, -0.837),
        (0.0, -0.832)], segments=20, mat="M_Brass_Aged")
    parts.append(fitter)
    # three knurled thumb screws that clamp the shade neck
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.3
        d = M.Vector((math.cos(a), math.sin(a), 0))
        ts = M.lathe(f"thumb{i}", [(0.0, 0.0), (0.0028, 0.0), (0.0028, 0.010), (0.0062, 0.011),
                                   (0.0066, 0.017), (0.0055, 0.0195), (0.0, 0.0195)],
                     segments=10, mat="M_Brass_Aged")
        q = M.Vector((0, 0, 1)).rotation_difference(d)
        ts.data.transform(q.to_matrix().to_4x4())
        ts.location = (d.x * 0.050, d.y * 0.050, -0.954)
        parts.append(ts)

    # ---- bakelite socket + brass screw base
    sock = M.lathe("socket", [(0.0, -1.006), (0.0175, -1.006), (0.0205, -1.002), (0.0205, -0.966),
                              (0.023, -0.962), (0.0, -0.962)], segments=20, mat="M_Bakelite")
    parts.append(sock)
    base_prof = [(0.0, -1.028)]
    for k in range(5):
        z = -1.027 + k * 0.0042
        base_prof += [(0.0128, z), (0.0140, z + 0.0021)]
    base_prof += [(0.0135, -1.006), (0.0, -1.006)]
    parts.append(M.lathe("bulb_base", base_prof, segments=16, mat="M_Brass_Aged"))

    shade_o = shade()

    # ---- bulb (emissive glass) + light origin
    bulb = M.lathe("bulb", [(0.0129, -1.028), (0.0145, -1.036), (0.019, -1.048), (0.025, -1.060),
                            (0.0295, -1.074), (0.031, -1.088), (0.0298, -1.102), (0.0262, -1.114),
                            (0.0195, -1.123), (0.010, -1.1285), (0.0, -1.1295)],
                   segments=20, mat="M_Emissive_Warm")
    bulb.name = "bulb"

    static = M.join(parts + [shade_o], "pendant_lamp_body")
    M.empty("light_origin", (0, 0, BULB_C))

    M.finalize()
    print(f"[{NAME}] tris body={A.tris(static)} bulb={A.tris(bulb)} total={M.tri_count()}")
    return static, bulb


def main():
    args = M.main_guard()
    build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(64)
    # 3/4 view of the shade, slightly from above, studio lights
    M.render_preview(NAME, (0.62, -0.78, -0.80), (0, 0, -1.0), lens=50, res=(800, 640), samples=64,
                     world_strength=0.3, lights=A.STUDIO)
    # full length with a ceiling plane, seen from a standing player below
    ceil = M.box("QA_ceiling", (1.6, 1.6, 0.02), loc=(0, 0, 0.01), mat="M_Ceiling", bevel=0)
    M.render_preview(NAME + "_3", (1.15, -1.5, -1.55), (0, 0, -0.55), lens=40, res=(640, 960), samples=48,
                     world_strength=0.3, lights=A.STUDIO)
    _ = ceil
    # from below, looking into the shade
    M.render_preview(NAME + "_2", (0.32, -0.42, -1.75), (0, 0, -1.07), lens=50, res=(800, 640),
                     samples=64, world_strength=0.3, lights=A.STUDIO)


main()
