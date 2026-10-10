"""sun_lamp.glb — THE SUN: a car-sized brass carbon-arc lamp (Chapter 4, group E; the apse's hero).
Contract: docs/models/ch4.md section 7 sun_lamp; results: docs/models/ch4_e.md.

LOCAL FRAME: origin = the sphere centre; placed at (-13.0, 1.8, 0), yaw 0; the glass port faces +X (into the hall); the floor is at local
y = -1.8. Nodes:
  sun_lamp   M_Brass_Aged + M_Steel_Dark + M_Glass  the static lamp: a riveted brass sphere Ø 2.4 (meridian and latitude straps, rivets) open
             at the port, a dark steel lining, the brass port bezel with 16 bolts and the 1.5 Ø glass port (x = 0.93 .. 0.95), a steel cradle
             (two trunnions, four splayed legs, braces, foot plates), a steel carriage rail for rod_b, cooling fins round the back pole
             and a chimney
  rod_a      M_Steel_Dark + M_Brass_Aged  the fixed carbon rod (Ø 0.10, tapered tip) on the -X side with its brass cap and holder; ORIGIN = its tip
             at the touching position (-0.25, 0, 0)
  rod_b      M_Steel_Dark + M_Brass_Aged  the moving carbon rod on the +X side (carbon, brass cap, a carriage strut and foot that ride on the
             rail); ORIGIN = its tip at the touching position (-0.25, 0, 0). GAP g (0 .. 9) = rod_b slid 0.07 x g along +X (g = 0 shorted, 9 the start)
  arc_glow   M_Emissive_Lumen  a disc Ø 0.44 at the touching plane x = -0.25 facing +X; origin at its centre; the code drives the intensity
             (it may slide it +0.035 x g along +X to stay mid-gap)
  sun_light  empty at (-0.20, 0, 0)

    blender -b --factory-startup -P tools/blender/models/sun_lamp.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, D, BRASS, STEEL, GLASS, LUMEN  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "sun_lamp"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 12000, 8, 4
R = 1.2
R_PORT = 0.75
TH_PORT = math.degrees(math.asin(R_PORT / R))      # 38.7 deg from +X
X_PORT = R * math.cos(math.radians(TH_PORT))       # 0.937
XT = -0.25                                         # the touching plane (tips meet here)
FLOOR = -1.8


def sph(theta, phi, rho):
    """Point on the sphere: theta from +X (deg), phi round the X axis from +Y (deg, toward +Z)."""
    t, p = math.radians(theta), math.radians(phi)
    return Vector((rho * math.cos(t), rho * math.sin(t) * math.cos(p), rho * math.sin(t) * math.sin(p)))


def shell_parts():
    brass, steel, glass = [], [], []
    # --- the shell: profile from the back pole to the port edge (bottom -> top along +X)
    prof = [(R * math.sin(math.radians(th)), R * math.cos(math.radians(th))) for th in [180.0 - i * (180.0 - TH_PORT) / 28.0 for i in range(29)]]
    prof[0] = (0.0, -R)
    brass.append(K.glathe("shell", prof, base=(0, 0, 0), axis=(1, 0, 0), segments=40, mat=BRASS, smooth=60.0, cap_top=False))
    # --- the lining: radius 1.17, faces inward (profile reversed: port edge -> back pole)
    r2 = 1.17
    th_p2 = math.degrees(math.asin(R_PORT / r2))
    prof2 = [(r2 * math.sin(math.radians(th)), r2 * math.cos(math.radians(th))) for th in [th_p2 + i * (180.0 - th_p2) / 12.0 for i in range(13)]]
    prof2[-1] = (0.0, -r2)
    steel.append(K.glathe("lining", prof2, base=(0, 0, 0), axis=(1, 0, 0), segments=32, mat=STEEL, smooth=60.0, cap_bottom=False))
    # --- straps and rivets (one bmesh)
    bm = bmesh.new()
    th0, th1 = TH_PORT + 9.0, 168.0
    nth = 18
    half = 0.032
    for m in range(8):
        phi = 45.0 * m + 22.5
        tang = Vector((0.0, -math.sin(math.radians(phi)), math.cos(math.radians(phi))))
        rows = []
        for i in range(nth + 1):
            th = th0 + (th1 - th0) * i / nth
            pos, low = sph(th, phi, R + 0.011), sph(th, phi, R - 0.004)
            rows.append((bm.verts.new(pos - tang * half), bm.verts.new(pos + tang * half),
                         bm.verts.new(low - tang * half), bm.verts.new(low + tang * half), pos.normalized()))
        for i in range(nth):
            a, b = rows[i], rows[i + 1]
            X.bm_face(bm, (a[0], a[1], b[1], b[0]), a[4])                  # top
            X.bm_face(bm, (a[2], a[0], b[0], b[2]), -tang)                 # side
            X.bm_face(bm, (a[1], a[3], b[3], b[1]), tang)                  # side
        for i in range(2, nth - 1, 2):                                     # rivets on the strap
            th = th0 + (th1 - th0) * i / nth
            c = sph(th, phi, R + 0.011)
            X.bm_dome(bm, tuple(c), 0.017, 0.016, segs=5, normal=tuple(c.normalized()))
    for th_l in (62.0, 118.0):                                             # two latitude straps
        nph = 40
        ring = []
        for j in range(nph):
            phi = 360.0 * j / nph
            top, low = sph(th_l, phi, R + 0.011), sph(th_l, phi, R - 0.004)
            ring.append((bm.verts.new(top + Vector((-half, 0, 0))), bm.verts.new(top + Vector((half, 0, 0))),
                         bm.verts.new(low + Vector((-half, 0, 0))), bm.verts.new(low + Vector((half, 0, 0))), top.normalized()))
        for j in range(nph):
            a, b = ring[j], ring[(j + 1) % nph]
            X.bm_face(bm, (a[0], a[1], b[1], b[0]), a[4])
            X.bm_face(bm, (a[2], a[0], b[0], b[2]), (-1, 0, 0))
            X.bm_face(bm, (a[1], a[3], b[3], b[1]), (1, 0, 0))
        for j in range(0, nph, 2):
            c = sph(th_l, 360.0 * j / nph + 4.5, R + 0.011)
            X.bm_dome(bm, tuple(c), 0.017, 0.016, segs=5, normal=tuple(c.normalized()))
    brass.append(K.obj_from_bm("straps", bm, BRASS))
    # --- the port bezel (a turned ring), its bolts, the glass port
    bez = [(0.75, 0.90), (0.98, 0.90), (0.98, 1.00), (0.93, 1.04), (0.70, 1.04), (0.70, 0.97), (0.75, 0.97), (0.75, 0.90)]
    brass.append(K.glathe("bezel", bez, base=(0, 0, 0), axis=(1, 0, 0), segments=48, mat=BRASS, smooth=50.0, cap_bottom=False, cap_top=False))
    for i in range(16):
        a = math.radians(22.5 * i)
        brass.append(K.rivet("bolt", 0.022, (1.04, 0.84 * math.cos(a), 0.84 * math.sin(a)), normal=(1, 0, 0), mat=BRASS, segs=5))
    glass.append(K.gcyl("glass", 0.752, 0.925, 0.945, base=(0, 0, 0), axis=(1, 0, 0), segments=32, mat=GLASS))
    # --- cooling fins round the back pole and a chimney on top
    for i in range(6):
        h = -0.78 - 0.064 * i
        r_in = math.sqrt(R * R - h * h) - 0.01
        loop = [(r_in, h - 0.012), (r_in + 0.20, h - 0.012), (r_in + 0.20, h + 0.012), (r_in, h + 0.012), (r_in, h - 0.012)]
        steel.append(K.glathe("fin", loop, base=(0, 0, 0), axis=(1, 0, 0), segments=28, mat=STEEL, smooth=40.0, cap_bottom=False, cap_top=False))
    chim = [(0.0, 1.10), (0.17, 1.10), (0.17, 1.22), (0.13, 1.24), (0.13, 1.44), (0.19, 1.46), (0.19, 1.50), (0.15, 1.52), (0.0, 1.52)]
    steel.append(K.glathe("chimney", chim, base=(0, 0, 0), axis=(0, 1, 0), segments=18, mat=STEEL, smooth=50.0))
    # --- the steel cradle: trunnions, four splayed legs, braces, feet, base rails, the carriage rail
    for s in (-1, 1):
        steel.append(K.gcyl("trun", 0.20, 1.18, 1.36, base=(0, 0, 0), axis=(0, 0, s), segments=18, mat=STEEL, chamfer=0.02))
        steel.append(K.gcyl("trunc", 0.12, 1.36, 1.44, base=(0, 0, 0), axis=(0, 0, s), segments=14, mat=STEEL, chamfer=0.01))
        for sx in (-1, 1):
            a = Vector((0.0, 0.0, s * 1.30))
            b = Vector((sx * 0.85, FLOOR + 0.06, s * 1.55))
            steel.append(D.rod("leg", tuple(a), tuple(b), 0.085, segs=6, mat=STEEL))
            steel.append(K.gbox("foot", (b.x - 0.20, FLOOR, b.z - 0.20), (b.x + 0.20, FLOOR + 0.06, b.z + 0.20), STEEL, 0.006))
        steel.append(D.rod("brace", (-0.62, -1.0, s * 1.46), (0.62, -1.0, s * 1.46), 0.045, segs=6, mat=STEEL))
    for sx in (-1, 1):
        steel.append(D.rod("base", (sx * 0.85, FLOOR + 0.08, -1.55), (sx * 0.85, FLOOR + 0.08, 1.55), 0.05, segs=6, mat=STEEL))
    steel.append(K.gbox("rail", (-0.30, -0.47, -0.035), (0.92, -0.43, 0.035), STEEL, 0.003))
    return brass, steel, glass


def rod_parts(side):
    """side = -1 (rod_a, the fixed rod toward -X) or +1 (rod_b, the moving rod toward +X). Origin = the tip at the touching plane."""
    s = side
    ax = (s, 0.0, 0.0)
    base = (XT, 0.0, 0.0)
    carbon_len = 0.55 if s < 0 else 0.42
    carbon = [(0.0, 0.0), (0.028, 0.0), (0.050, 0.07), (0.050, carbon_len), (0.0, carbon_len)]
    cap = [(0.0, carbon_len), (0.066, carbon_len), (0.076, carbon_len + 0.012), (0.076, carbon_len + 0.082), (0.060, carbon_len + 0.095), (0.0, carbon_len + 0.095)]
    steel = K.glathe("carbon", carbon, base=base, axis=ax, segments=14, mat=STEEL, smooth=60.0)
    brass = [K.glathe("cap", cap, base=base, axis=ax, segments=14, mat=BRASS, smooth=60.0)]
    if s < 0:
        x_end = XT - (carbon_len + 0.095)
        brass.append(K.gbox("holder", (x_end - 0.20, -0.07, -0.07), (x_end, 0.07, 0.07), BRASS, 0.005))
    else:
        x_c = XT + carbon_len + 0.05
        brass.append(K.gbox("strut", (x_c - 0.035, -0.43, -0.03), (x_c + 0.035, -0.05, 0.03), BRASS, 0.004))
        brass.append(K.gbox("shoe", (x_c - 0.09, -0.47, -0.06), (x_c + 0.09, -0.40, 0.06), BRASS, 0.004))
    return [steel] + brass


def build():
    M.reset_scene()
    C.ensure_materials()
    brass, steel, glass = shell_parts()
    lamp = C.merge("sun_lamp", brass + steel + glass)
    rod_a = K.part("rod_a", rod_parts(-1), pivot=(XT, 0.0, 0.0))
    rod_b = K.part("rod_b", rod_parts(+1), pivot=(XT, 0.0, 0.0))
    glow = K.glathe("glow_m", [(0.0, 0.0), (0.22, 0.0), (0.22, 0.012), (0.0, 0.012)], base=(XT, 0.0, 0.0), axis=(1, 0, 0), segments=24,
                    mat=LUMEN, smooth=40.0)
    glow = K.part("arc_glow", [glow], pivot=(XT, 0.0, 0.0))
    K.empty("sun_light", (XT + 0.05, 0.0, 0.0))
    K.to_blender()
    C.finalize()
    return dict(lamp=lamp, rod_a=rod_a, rod_b=rod_b, glow=glow)


def verify(path):
    req = ["sun_lamp", "rod_a", "rod_b", "arc_glow", "sun_light"]
    ident = ["sun_lamp", "rod_a", "rod_b", "arc_glow"]
    expect = {"sun_lamp": (0.0, 0.0, 0.0), "rod_a": (XT, 0.0, 0.0), "rod_b": (XT, 0.0, 0.0), "arc_glow": (XT, 0.0, 0.0),
              "sun_light": (XT + 0.05, 0.0, 0.0)}
    errs = C.verify(path, required=req, identity=ident, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ("sun_lamp", "rod_a", "rod_b", "arc_glow"):
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    objs = [parts["lamp"], parts["rod_a"], parts["rod_b"], parts["glow"], bpy.data.objects["sun_light"]]
    K.qa_place(objs, (-13.0, 1.8, 0.0), 0.0, name="qa_sun_root")
    for o in (parts["glow"],):
        K.override(o, K.glow("qa_arc", "FFFFFF", 30.0))
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False, core=False)
        K.light("sun_arc", "POINT", (-12.4, 1.8, 0.0), 60000.0, "FFF6E8", radius=0.2)
    if C.want(args, "1"):          # the apse view
        K.pose_slide(parts["rod_b"], (0.07 * 4, 0.0, 0.0))
        cam, tgt, fov = C.view("apse")
        lit(cam, 60.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a three-quarter closeup: sphere, straps, cradle, the rods through the port (g = 9: the start)
        K.pose_slide(parts["rod_b"], (0.07 * 5, 0.0, 0.0))   # (QA pose: g = 5 -> rod_b slid 0.35)
        cam, tgt, fov = (-9.8, 1.6, -2.6), (-13.0, 1.6, 0.0), 46
        lit(cam, 70.0, 0.25)
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
