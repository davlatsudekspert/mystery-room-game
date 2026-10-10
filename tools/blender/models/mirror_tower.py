"""mirror_tower.glb — one of the four brass mirror towers that stand on the Array rings (Chapter 4, group C; the code instances
it four times at tower_mount_1..4).
Contract: docs/models/ch4.md section 5 mirror_tower; results: docs/models/ch4_c.md.

Origin = the plinth base centre on the ring top; front (+Z) = radially outward at rest. Local coordinates (metres):
  tower_body       M_Brass_Aged  stepped plinth 0.70 x 0.70 x 0.18 with corner bolts, a key shelf with two clips on the +Z (south)
                   side of its top, the turned post (Ø 0.12) from y 0.18 to 1.16 with collars, a numeral plate 0.30 x 0.26
                   on the +Z face of the post (centre (0, 0.58, 0.06)) and the yoke hub on the post top
  tower_head       M_Brass_Aged + M_Chrome  the yoke (two arms, cross bar, trunnions) and the 45 deg mirror (a chrome disc Ø 0.185 in
                   a brass bezel, its face looking up and +Z). ORIGIN = the post top / mirror centre (0, 1.30, 0), identity at
                   rest; the code yaws it about +Y so the beam turns toward the next tower
  tower_numeral_1..4   M_Chrome  the numeral I..IV in 0.014 relief on the plate; origin = the plate centre (0, 0.58, 0.075);
                   the code shows ONE of the four
  IA_key           M_Brass_Aged  the brass key lying in the bracket, bow toward -Z, ORIGIN (0, 0.19, 0.24), 0.20 long
  beam_point       empty (0, 1.30, 0)

    blender -b --factory-startup -P tools/blender/models/mirror_tower.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, D, BRASS, CHROME  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "mirror_tower"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 4000, 3, 2
HEAD = (0.0, 1.30, 0.0)
KEY = (0.0, 0.19, 0.24)
PLATE_C = (0.0, 0.58, 0.075)
NUM_H = 0.17
S45 = math.sqrt(0.5)
MIRROR_N = (0.0, S45, S45)              # the mirror face looks up and toward +Z (outward)


def rod(a, b, r, mat=BRASS, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    return K.gcyl("rod", r, 0.0, d.length, base=tuple(a), axis=tuple(d.normalized()), segments=segs, mat=mat, smooth=60.0)


def body_parts():
    out = []
    # --- plinth: foot, body, cap (chamfered boxes) with corner bolts
    out.append(K.gbox("foot", (-0.35, 0.0, -0.35), (0.35, 0.05, 0.35), BRASS, 0.006))
    out.append(K.gbox("plinth", (-0.31, 0.05, -0.31), (0.31, 0.15, 0.31), BRASS, 0.006))
    out.append(K.gbox("cap", (-0.335, 0.15, -0.335), (0.335, 0.18, 0.335), BRASS, 0.004))
    for sx in (-1, 1):
        for sz in (-1, 1):
            out.append(K.hexbolt("bolt", 0.022, (sx * 0.29, 0.05, sz * 0.29), normal=(0, 1, 0), mat=BRASS, washer=False))
    # --- key shelf: a tray with a low lip on the south edge and two clips
    out.append(K.gbox("tray", (-0.11, 0.18, 0.11), (0.11, 0.186, 0.335), BRASS, 0.002))
    out.append(K.gbox("lip", (-0.11, 0.186, 0.325), (0.11, 0.215, 0.338), BRASS, 0.003))
    for zc in (0.20, 0.285):
        out.append(K.gbox("clipL", (-0.052, 0.186, zc - 0.014), (-0.036, 0.236, zc + 0.014), BRASS, 0.002))
        out.append(K.gbox("clipR", (0.036, 0.186, zc - 0.014), (0.052, 0.236, zc + 0.014), BRASS, 0.002))
        out.append(K.gbox("clipT", (-0.052, 0.226, zc - 0.014), (0.052, 0.242, zc + 0.014), BRASS, 0.002))
    # --- post (turned): flared foot, two collars, taper to the hub
    prof = [(0.0, 0.18), (0.115, 0.18), (0.115, 0.205), (0.085, 0.235), (0.06, 0.29), (0.06, 0.50), (0.075, 0.51), (0.075, 0.53),
            (0.06, 0.54), (0.06, 0.95), (0.072, 0.96), (0.072, 0.985), (0.06, 0.995), (0.06, 1.12), (0.075, 1.14), (0.075, 1.17)]
    out.append(K.glathe("post", prof, base=(0.0, 0.0, 0.0), axis=(0, 1, 0), segments=16, mat=BRASS, smooth=60.0))
    # --- numeral plate on the +Z face of the post, with two bolts
    out.append(K.gbox("plate", (-0.15, PLATE_C[1] - 0.13, 0.045), (0.15, PLATE_C[1] + 0.13, 0.075), BRASS, 0.004))
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(K.hexbolt("pbolt", 0.011, (sx * 0.128, PLATE_C[1] + sy * 0.108, 0.075), normal=(0, 0, 1), mat=BRASS,
                                 washer=False))
    return out


def head_parts():
    ax, ay, az = HEAD
    out = []
    n = Vector(MIRROR_N)
    # the mirror: a chrome disc in a brass bezel with a brass back plate (lathes about the mirror normal)
    out.append(K.glathe("mirror", [(0.0, 0.0), (0.093, 0.0), (0.093, 0.004), (0.0, 0.004)], base=HEAD, axis=tuple(n), segments=22,
                        mat=CHROME, smooth=60.0))
    out.append(K.glathe("bezel", [(0.090, -0.004), (0.112, -0.004), (0.112, 0.010), (0.100, 0.016), (0.090, 0.010), (0.090, -0.004)],
                        base=HEAD, axis=tuple(n), segments=22, mat=BRASS, smooth=60.0, cap_bottom=False, cap_top=False))
    out.append(K.glathe("back", [(0.0, -0.024), (0.100, -0.024), (0.112, -0.012), (0.112, -0.004), (0.0, -0.004)], base=HEAD,
                        axis=tuple(n), segments=22, mat=BRASS, smooth=60.0))
    # yoke: hub boss on the post top, a cross bar, two arms, trunnion pins
    out.append(K.glathe("hub", [(0.0, 1.17), (0.082, 1.17), (0.082, 1.20), (0.066, 1.215), (0.0, 1.215)], base=(0, 0, 0),
                        axis=(0, 1, 0), segments=16, mat=BRASS, smooth=60.0))
    out.append(K.gbox("bar", (-0.150, 1.205, -0.040), (0.150, 1.235, 0.040), BRASS, 0.004))
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.132, sx * 0.158))
        out.append(K.gbox("arm", (xa, 1.205, -0.034), (xb, 1.40, 0.034), BRASS, 0.004))
        out.append(rod((sx * 0.158, ay, 0.0), (sx * 0.118, ay, 0.0), 0.013, BRASS, 8))
        out.append(K.gcyl("cap", 0.02, 0.0, 0.012, base=(sx * 0.158, ay, 0.0), axis=(sx, 0, 0), segments=10, mat=BRASS))
    return out


def key_parts():
    ky = KEY[1]
    out = [D.ring("bow", 0.021, 0.040, -0.008, 0.008, centre=(0.0, ky, 0.175), axis=(0, 1, 0), segs=14, mat=BRASS, chamfer=0.003)]
    out.append(K.gbox("shaft", (-0.008, ky - 0.008, 0.210), (0.008, ky + 0.008, 0.340), BRASS, 0.002))
    out.append(K.gbox("collar", (-0.017, ky - 0.010, 0.222), (0.017, ky + 0.010, 0.234), BRASS, 0.002))
    for z0, z1 in ((0.298, 0.309), (0.322, 0.340)):
        out.append(K.gbox("bit", (0.008, ky - 0.008, z0), (0.036, ky + 0.008, z1), BRASS, 0.001))
    return out


def numeral(n):
    o = C.N.roman_obj(f"tn_{n}", n, NUM_H, depth=0.014, mat=CHROME)
    o.data.transform(Matrix.Translation(PLATE_C))
    return K.part(f"tower_numeral_{n}", [o], pivot=PLATE_C)


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("tower_body", body_parts())
    head = K.part("tower_head", head_parts(), pivot=HEAD)
    key = K.part("IA_key", key_parts(), pivot=KEY)
    nums = [numeral(n) for n in (1, 2, 3, 4)]
    K.empty("beam_point", HEAD)
    K.to_blender()
    C.finalize()
    return dict(body=body, head=head, key=key, nums=nums)


def verify(path):
    req = ["tower_body", "tower_head", "IA_key", "beam_point"] + [f"tower_numeral_{n}" for n in (1, 2, 3, 4)]
    ident = [r for r in req if r != "beam_point"]
    expect = {"tower_head": HEAD, "IA_key": KEY, "beam_point": HEAD}
    expect.update({f"tower_numeral_{n}": PLATE_C for n in (1, 2, 3, 4)})
    errs = C.verify(path, required=req, identity=ident, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET + 5,
                    mat_budget=MAT_BUDGET)
    for n in ["tower_body", "tower_head", "IA_key", "tower_numeral_4"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def place_tower(n, r_, yaw_head, prefix):
    """Import the GLB at tower n's mount, show only numeral n, yaw its head (QA only)."""
    root = C.qa_import(NAME, (0.0, 0.5, r_), 0.0, prefix=prefix)
    for o in bpy.data.objects:
        if o.name.startswith(prefix + "tower_numeral_") and not o.name.startswith(f"{prefix}tower_numeral_{n}"):
            o.hide_render = True
            o.hide_viewport = True
        if o.name == prefix + "tower_head":
            K.pose_rot(o, "y", yaw_head)
    return root


def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_core()
    # the built tower is number 1 on ring I; towers 2..4 are the GLB again on the other rings (head yaws vary)
    for n, (r_, yaw) in enumerate(zip(C.RING_R, (0.0, 50.0, 100.0, -40.0)), start=1):
        place_tower(n, r_, yaw, f"qa_mt{n}_")
    for o in list(bpy.data.objects):                      # the freshly built objects are the unplaced originals: hide them
        if o.name in ("tower_body", "tower_head", "IA_key", "beam_point") or o.name.startswith("tower_numeral_"):
            o.hide_render = True
            o.hide_viewport = True
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # hatch_1: down through the open lid at the tower base
        for o in bpy.data.objects:
            if o.name.startswith("qa_catwalk_IA_hatch_1"):
                K.pose_rot(o, "x", -105.0)
        cam, tgt, fov = C.hatch_view(1)
        lit(cam, 90.0, 0.3)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a closeup of tower I from the south-east: plate, numeral, key, mirror head
        cam, tgt, fov = (1.5, 1.35, 12.55), (0.0, 1.0, 10.5), 44
        lit(cam, 110.0, 0.35)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # the bridge view: four towers, four head yaws
        cam, tgt, fov = C.view("bridge")
        lit(cam, 80.0, 0.3)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)


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
