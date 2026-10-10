"""cradle.glb — the lens cradle on the Core's pedestal (Chapter 4, group D).
Contract: docs/models/ch4.md section 6 cradle; results: docs/models/ch4_d.md.

ISLAND FRAME: placed at (0, 2.5, 0); origin = the island centre on the platform top. A bracket on the pedestal's south face holds the
lens socket at (0, 1.32, 0.62); the socket looks at the Core centre (0, 1.6, 0): its axis n = (0, 0.41, -0.91) (24 deg above the horizon).
  cradle_arm     M_Steel_Dark + M_Brass_Aged  base plate on the pedestal top, a gusset, a brass neck and a fork whose trunnions hold the socket
  IA_cradle      M_Brass_Aged  the lens socket: a ring Ø 0.23 with an inner recess Ø 0.15 on the player side and a ledge (hole Ø 0.06) on the Core
                 side; ORIGIN = the socket centre (0, 1.32, 0.62), identity rotation (the tilt is baked into the mesh)
  cradle_ring    M_Glass_Dark  a lamp ring around the socket (r 0.117 .. 0.142), the code turns its emission on when the lens is seated;
                 origin = the socket centre
  lens_mount     empty at the lens centre (0, 1.3135, 0.6266) = the socket centre moved 7 mm toward the player; frame: +Z = toward the Core
                 (the lens `crystal_lens` faces +Z in its own file, so it looks at the crystal), +Y = up
  mark_mount     empty on the drawer face below, (0, 0.68, 0.705), identity (+Z = out of the face)

    blender -b --factory-startup -P tools/blender/models/cradle.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, D, BRASS, STEEL, GDARK  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "cradle"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3000, 4, 3
SOCKET = Vector((0.0, 1.32, 0.62))
CORE = Vector((0.0, 1.6, 0.0))
N = (CORE - SOCKET).normalized()                    # the socket axis, toward the Core
UP = Vector((0.0, 0.91, 0.41)).normalized()         # in-plane "up" of the socket ring (perpendicular to N)
LENS_C = SOCKET - N * 0.007
MARK = (0.0, 0.68, 0.705)


def lens_basis():
    ez = N.copy()
    ex = Vector((0, 1, 0)).cross(ez).normalized()
    ey = ez.cross(ex).normalized()
    return Matrix((ex, ey, ez)).transposed()


def rod(a, b, r, mat=BRASS, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    return K.gcyl("rod", r, 0.0, d.length, base=tuple(a), axis=tuple(d.normalized()), segments=segs, mat=mat, smooth=60.0)


def arm_parts():
    out = []
    # steel base plate on the pedestal top plate (y 1.07), a gusset to the collar, four bolts
    out.append(K.gbox("plate", (-0.16, 1.07, 0.38), (0.16, 1.115, 0.70), STEEL, 0.004))
    out.append(K.gbox("gusset", (-0.02, 0.93, 0.50), (0.02, 1.07, 0.70), STEEL, 0.003))
    for sx in (-1, 1):
        for z in (0.43, 0.65):
            out.append(K.hexbolt("bolt", 0.014, (sx * 0.125, 1.115, z), normal=(0, 1, 0), mat=STEEL, washer=False))
    # brass neck (turned): a flared foot, a slim neck, a collar, tilted nowhere (it is vertical, at z 0.60)
    prof = [(0.0, 1.115), (0.065, 1.115), (0.065, 1.135), (0.040, 1.155), (0.028, 1.17), (0.028, 1.20), (0.040, 1.212), (0.0, 1.22)]
    out.append(K.glathe("neck", prof, base=(0.0, 0.0, 0.60), axis=(0, 1, 0), segments=14, mat=BRASS, smooth=60.0))
    # the fork: a cross bar under the ring and two arms to the trunnions at the ring's sides
    out.append(K.gbox("bar", (-0.16, 1.20, 0.56), (0.16, 1.235, 0.64), BRASS, 0.004))
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.140, sx * 0.168))
        out.append(K.gbox("arm", (xa, 1.20, 0.575), (xb, 1.36, 0.645), BRASS, 0.004))
        out.append(rod((sx * 0.168, SOCKET.y, SOCKET.z), (sx * 0.118, SOCKET.y, SOCKET.z), 0.016, BRASS, 8))
        out.append(K.gcyl("cap", 0.024, 0.0, 0.014, base=(sx * 0.168, SOCKET.y, SOCKET.z), axis=(sx, 0, 0), segments=10, mat=BRASS))
    return out


def socket_parts():
    prof = [(0.075, -0.015), (0.115, -0.015), (0.115, 0.015), (0.030, 0.015), (0.030, 0.0), (0.075, 0.0)]
    ring = K.glathe("socket", prof + [(0.075, -0.015)], base=tuple(SOCKET), axis=tuple(N), segments=32, mat=BRASS, smooth=40.0,
                    cap_bottom=False, cap_top=False)
    out = [ring]
    # three small studs on the outer rim (screw heads)
    for i in range(6):
        a = math.radians(60.0 * i + 30.0)
        d = Vector((math.cos(a), 0, 0)) * 0.0
        r_ = 0.100
        ctr = SOCKET + Vector((r_ * math.cos(a), 0, 0)) + UP * (r_ * math.sin(a))
        # the ring plane is spanned by X and UP
        out.append(K.rivet("st", 0.011, tuple(ctr - N * 0.015), normal=tuple(-N), mat=BRASS, segs=5))
    return out


def glow_ring():
    prof = [(0.117, -0.012), (0.142, -0.012), (0.142, 0.010), (0.117, 0.010), (0.117, -0.012)]
    return K.glathe("lamp", prof, base=tuple(SOCKET), axis=tuple(N), segments=32, mat=GDARK, smooth=40.0, cap_bottom=False,
                    cap_top=False)


def build():
    M.reset_scene()
    C.ensure_materials()
    arm = C.merge("cradle_arm", arm_parts())
    sock = K.part("IA_cradle", socket_parts(), pivot=tuple(SOCKET))
    ring = K.part("cradle_ring", [glow_ring()], pivot=tuple(SOCKET))
    e1 = K.empty("lens_mount", tuple(LENS_C))
    e1.rotation_euler = lens_basis().to_euler("XYZ")
    K.empty("mark_mount", MARK)
    K.to_blender()
    C.finalize()
    return dict(arm=arm, sock=sock, ring=ring)


def verify(path):
    req = ["cradle_arm", "IA_cradle", "cradle_ring", "lens_mount", "mark_mount"]
    ident = ["cradle_arm", "IA_cradle", "cradle_ring", "mark_mount"]
    expect = {"cradle_arm": (0.0, 0.0, 0.0), "IA_cradle": tuple(SOCKET), "cradle_ring": tuple(SOCKET), "lens_mount": tuple(LENS_C),
              "mark_mount": MARK}
    e = lens_basis().to_euler("XYZ")
    rot = {"lens_mount": tuple(math.degrees(a) for a in e)}
    errs = C.verify(path, required=req, identity=ident, expect=expect, rot_expect=rot, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    print(f"{C.TAG} lens_mount euler XYZ deg {tuple(round(math.degrees(a), 2) for a in e)}; socket axis n = "
          f"{tuple(round(c, 4) for c in N)} ({round(math.degrees(math.asin(N.y)), 1)} deg above the horizon)")
    for n in ("cradle_arm", "IA_cradle", "cradle_ring"):
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_reliquary(skip=(NAME,), sprites=True)
    X.qa_place_island([parts["arm"], parts["sock"], parts["ring"], bpy.data.objects["lens_mount"], bpy.data.objects["mark_mount"]])
    # QA: the real crystal_lens at lens_mount (its own file faces +Z)
    holder = C.qa_import("crystal_lens", (0.0, 0.0, 0.0), 0.0, prefix="qa_lens_")
    lm = bpy.data.objects["lens_mount"]
    if holder is not None:
        holder.parent = lm
        holder.matrix_parent_inverse = Matrix.Identity(4)
        holder.location = (0, 0, 0)
        holder.rotation_euler = (0, 0, 0)
        M.refresh()
    for o in bpy.data.objects:                                   # the lamp ring lit (QA)
        if o.name == "cradle_ring":
            K.override(o, K.glow("qa_cradle_ring", "CFF6FF", 9.0))
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
    X.vis("qa_cage_", False)
    X.vis("qa_glass_tower_", False)
    if C.want(args, "1"):          # the cradle from above and the south: arm, socket with the lens, lamp ring, the drawer face below
        cam, tgt, fov = (0.0, 4.6, 2.4), (0.0, 3.6, 0.5), 50
        lit(cam, 40.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a closeup of the socket and the fork from the south-east
        cam, tgt, fov = (0.85, 4.05, 1.35), (0.0, 3.8, 0.62), 40
        lit(cam, 40.0, 0.2)
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
