"""strand_box4.glb — Strand's walnut gear box: four knobs, four meshing gears with pointers on the lid, the orrery and his log inside (Chapter 4, group F; puzzle P2).
Contract: docs/models/ch4.md section 8 strand_box4; results: docs/models/ch4_f.md.

LOCAL FRAME: origin = the base centre of the box on the desk top (0.0 = the desk's box_mount), front = +Z. Placed at (0, 2.78, -13.4) with yaw 0.
Box 0.48 w x 0.34 d x 0.19 high (body 0.15 + lid 0.04): x +-0.24, z +-0.17. (The contract said 0.42 x 0.30; the orrery inside is O 0.26.)
Nodes:
  strand_box4   M_Wood_Walnut + M_Brass_Aged  the hollow walnut body (floor, four walls, base and top mouldings), four brass escutcheon discs with six detent ticks
                each on the front, corner brackets, the lid's hinge knuckles, a brass stand for the orrery
  IA_box_lid    M_Brass_Aged  the brass lid with its stepped top plate: four fixed target indices (one behind each gear), four gear posts, Strand's mark
                (front strip) and the pictogram "a wheel with an arrow to its neighbour" (rear strip). ORIGIN = the hinge axis (0, 0.158, -0.181), along X.
                Closed = identity; OPEN = -110 deg about +X (the lid stands up and leans back; the gears travel with it)
    gear_pointer_1..4  M_Bakelite  CHILDREN of IA_box_lid: a spoked 12-tooth wheel (six spokes = the six positions) with a needle. ORIGIN = the gear centre at
                (x_k, 0.19, z_k), k = 1..4 at x = -0.12675, -0.0423, +0.0423, +0.12675 (a zig-zag: odd gears at z = 0.0443, even at z = -0.0043; neighbours mesh,
                the even gears run 5 mm higher). Identity = the needle points at its fixed index (toward -Z, the back); position k (0..5) = -60 deg x k about +Y
  IA_knob_1..4  M_Brass_Aged  fluted brass push-knobs O 0.050 on the escutcheons, same x as the gear above. ORIGIN = (x_k, 0.075, 0.174), axis +Z; identity = the
                pointer ridge at 12 o'clock; position k (0..5) = -60 deg x k about +Z
  IA_box_log    M_Paper  the blotting-paper pad for the log inside the body (x 0.07 .. 0.22, z +-0.13, top at y 0.044). ORIGIN = the top centre (0.145, 0.044, 0)
    log_mount   child of IA_box_log, identity: strand_log lies flat on the pad (hero face +Y, top edge -Z, 0.14 wide x 0.20)
  orrery_mount  at (-0.08, 0.05, 0.0), identity: orrery.glb stands on the brass stand (its base O 0.26)

    blender -b --factory-startup -P tools/blender/models/strand_box4.py [-- --no-render] [--shots=1,2]
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
import lib_ch4_mark as MK  # noqa: E402
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, WALNUT, BAKE, PAPER  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "strand_box4"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 7000, 12, 4
BW, BD = 0.24, 0.17                       # half width, half depth
BH, LH = 0.15, 0.04                       # body and lid heights
TOPY = BH + LH                            # 0.19
HINGE = (0.0, 0.158, -0.181)
GX = (-0.12675, -0.0423, 0.0423, 0.12675)
GZ = (0.04425, -0.00425, 0.04425, -0.00425)
G_Y0 = (0.1935, 0.1985, 0.1935, 0.1985)  # gear bottoms (even gears 5 mm higher)
G_T = 0.0035
G_PHASE = (0.0, math.radians(15.0), 0.0, math.radians(15.0))
KY, KZ = 0.075, 0.174
R_ROOT, R_TIP = 0.0425, 0.0545
POINTER = 0.0720
LOG_C = (0.145, 0.044, 0.0)
ORR_C = (-0.08, 0.05, 0.0)
FLUTES = 12


def body_walnut():
    """The hollow walnut body. No two boxes overlap (stacked and abutting only): overlapping boxes merged by the builder's vertex weld gave dark top faces."""
    w = F.MB(WALNUT)
    t = 0.014
    y_w0, y_w1 = 0.016, BH - 0.012                                           # the walls stand on the base slab and carry the top moulding
    w.box((-BW - 0.008, 0.0, -BD - 0.008), (BW + 0.008, y_w0, BD + 0.008))   # the floor, a base slab wider than the walls
    for (x0, z0, x1, z1) in ((-BW, BD - t, BW, BD), (-BW, -BD, BW, -BD + t), (-BW, -BD + t, -BW + t, BD - t), (BW - t, -BD + t, BW, BD - t)):
        w.box((x0, y_w0, z0), (x1, y_w1, z1))                                # front, back, left, right walls
    ex = 0.004
    for (x0, z0, x1, z1) in ((-BW - ex, BD, BW + ex, BD + ex), (-BW - ex, -BD - ex, BW + ex, -BD), (-BW - ex, -BD, -BW, BD), (BW, -BD, BW + ex, BD)):
        w.box((x0, y_w0, z0), (x1, y_w0 + 0.008, z1))                        # a lower trim ring round the walls
    ex = 0.005
    for (x0, z0, x1, z1) in ((-BW - ex, BD - t, BW + ex, BD + ex), (-BW - ex, -BD - ex, BW + ex, -BD + t), (-BW - ex, -BD + t, -BW + t, BD - t), (BW - t, -BD + t, BW + ex, BD - t)):
        w.box((x0, y_w1, z0), (x1, BH, z1))                                  # the top moulding: a frame, so the box stays hollow
    w.box((-BW + 0.03, 0.036, BD), (BW - 0.03, 0.040, BD + 0.004))
    w.box((-BW + 0.03, 0.112, BD), (BW - 0.03, 0.116, BD + 0.004))
    return w.obj("box_walnut")


def body_brass():
    b = F.MB(BRASS)
    for x in GX:
        # escutcheon: a brass disc r 0.034 proud 0.002 with a stepped edge, six detent ticks (the 12 o'clock one longer)
        b.cyl((x, KY, BD), (0, 0, 1), 0.034, 0.002, segs=24)
        b.cyl((x, KY, BD + 0.002), (0, 0, 1), 0.030, 0.002, segs=24)
        for k in range(6):
            a = math.radians(60.0 * k)
            r1 = 0.038 + (0.013 if k == 0 else 0.007)
            side = 0.0038 if k == 0 else 0.0028
            b.bar((x + 0.038 * math.sin(a), KY + 0.038 * math.cos(a), BD + side / 2.0 - 0.0005),
                  (x + r1 * math.sin(a), KY + r1 * math.cos(a), BD + side / 2.0 - 0.0005), side, ref=(0, 0, 1))
    # corner brackets (L-shaped brass protectors) on the four vertical edges
    for sx in (-1, 1):
        for sz in (-1, 1):
            xo, zo = sx * BW, sz * BD
            b.box((min(xo, xo - sx * 0.020), 0.028, min(zo, zo + sz * 0.003)), (max(xo, xo - sx * 0.020), 0.146, max(zo, zo + sz * 0.003)))
            b.box((min(xo, xo + sx * 0.003), 0.028, min(zo, zo - sz * 0.020)), (max(xo, xo + sx * 0.003), 0.146, max(zo, zo - sz * 0.020)))
    # the body's hinge knuckles (x -0.22 .. -0.17, -0.06 .. +0.06, +0.17 .. +0.22) at the back
    for (xa, xb) in ((-0.22, -0.165), (-0.05, 0.05), (0.165, 0.22)):
        b.cyl((xa, HINGE[1], HINGE[2]), (1, 0, 0), 0.0085, xb - xa, segs=10)
        b.box((xa, 0.130, HINGE[2] + 0.004), (xb, 0.158, -BD + 0.001))
    # the stand for the orrery: a flared brass base and a turned neck, top at y 0.05
    b.cyl((ORR_C[0], 0.014, 0.0), (0, 1, 0), 0.072, 0.008, segs=24)
    b.cyl((ORR_C[0], 0.022, 0.0), (0, 1, 0), 0.050, 0.020, segs=20, r2=0.040)
    b.cyl((ORR_C[0], 0.042, 0.0), (0, 1, 0), 0.046, 0.008, segs=20)
    # a brass strap rail on the pad's side wall, two pillars for the log
    b.box((0.066, 0.014, -0.135), (0.072, 0.050, 0.135))
    b.box((0.218, 0.014, -0.135), (0.224, 0.050, 0.135))
    b.box((0.066, 0.014, -0.141), (0.224, 0.050, -0.135))
    b.box((0.066, 0.014, 0.135), (0.224, 0.050, 0.141))
    return b.obj("box_brass")


def lid_parts():
    b = F.MB(BRASS)
    zl0, zl1 = -BD - 0.002, BD + 0.002
    b.box((-BW - 0.005, BH, zl0), (BW + 0.005, TOPY - 0.012, zl1))           # the lid shell
    b.box((-BW + 0.012, TOPY - 0.012, zl0 + 0.012), (BW - 0.012, TOPY, zl1 - 0.012))   # the stepped top plate
    # front hasp: a latch plate hanging over the body's front, with a boss
    b.box((-0.035, BH - 0.030, zl1), (0.035, BH + 0.002, zl1 + 0.005))
    b.boss((0.0, BH - 0.014, zl1 + 0.005), (0, 0, 1), 0.011, 0.005, sides=10)
    # hinge knuckles on the lid: x -0.165 .. -0.05 and +0.05 .. +0.165
    for (xa, xb) in ((-0.162, -0.053), (0.053, 0.162)):
        b.cyl((xa, HINGE[1], HINGE[2]), (1, 0, 0), 0.0085, xb - xa, segs=10)
        b.box((xa, HINGE[1] - 0.006, HINGE[2] + 0.004), (xb, BH + 0.020, zl0 + 0.004))
    # rivets round the plate edge
    for i in range(12):
        x = -0.2 + 0.0364 * i
        for z in (zl0 + 0.022, zl1 - 0.022):
            b.dome((x, TOPY, z), 0.0042, 0.0035, segs=4, normal=(0, 1, 0))
    # posts and fixed target indices (a small arrowhead pointing at the gear) for each dial
    for k in range(4):
        x, z = GX[k], GZ[k]
        b.cyl((x, TOPY, z), (0, 1, 0), 0.0050, 0.020 if k % 2 == 0 else 0.026, segs=8)
        b.cyl((x, TOPY, z), (0, 1, 0), 0.0105, 0.0020, segs=14)
        zi = z - 0.0885                                                  # base of the index; its tip points at the gear, 4 mm beyond the needle
        b.prism_xz([(x - 0.0075, zi), (x + 0.0075, zi), (x, zi + 0.0105)], TOPY, TOPY + 0.0022)
    obj = b.obj("lid_brass")
    out = [obj]
    # Strand's mark in the front strip, the "wheel and arrow" pictogram in the rear strip
    marks = MK.mark_solids(0.050, 0.0030, BRASS, name="lid_mark")
    for o in marks:
        o.data.transform(Matrix.Translation((0.0, TOPY, 0.140)) @ Matrix.Rotation(math.radians(-90.0), 4, "X"))
    out += marks
    pic = F.picto_loops("wheels", 0.105)
    out.append(F.top_plate("lid_picto", pic, TOPY, 0.0035, BRASS, x=0.0, z=-0.134, bevel=0.0))
    return out


def gear_parts(k):
    x, z = GX[k], GZ[k]
    y0 = G_Y0[k]
    objs = [F.gear(f"gear{k}", 12, R_ROOT, R_TIP, y0, y0 + G_T, (x, z), BAKE, hole=0.0, spokes=6, hub=0.0105, phase=G_PHASE[k], rim=0.0075)]
    # hub boss and needle (lying above the gear, one level higher on the raised gears)
    yp = y0 + G_T + 0.0005 + (0.0045 if k % 2 == 0 else 0.0)
    objs.append(K.gcyl(f"hub{k}", 0.0105, y0, yp + 0.0030, base=(x, 0.0, z), axis=(0, 1, 0), segments=14, mat=BAKE, chamfer=0.0012))
    needle = [(-0.0050, -0.016), (0.0050, -0.016), (0.0045, 0.040), (0.0090, 0.056), (0.0, POINTER), (-0.0090, 0.056), (-0.0045, 0.040)]
    objs.append(F.top_plate(f"needle{k}", [needle], yp, 0.0026, BAKE, x=x, z=z, bevel=0.0))
    return objs


def knob_parts(k):
    x = GX[k]
    objs = [F.fluted(f"fl{k}", 0.025, 0.0, 0.020, FLUTES, 0.0016, base=(x, KY, KZ), axis=(0, 0, 1), mat=BRASS, cham=0.003)]
    objs.append(K.glathe(f"dome{k}", [(0.0, 0.020), (0.022, 0.020), (0.020, 0.0235), (0.012, 0.0265), (0.0, 0.0275)], base=(x, KY, KZ), axis=(0, 0, 1),
                         segments=12, mat=BRASS, smooth=60.0))
    # the pointer ridge at 12 o'clock on the face and a skirt
    objs.append(K.gbox(f"rd{k}", (x - 0.0022, KY + 0.004, KZ + 0.0255), (x + 0.0022, KY + 0.022, KZ + 0.0295), BRASS, 0.0003))
    objs.append(K.gcyl(f"sk{k}", 0.0275, KZ, KZ + 0.004, base=(x, KY, 0.0), axis=(0, 0, 1), segments=14, mat=BRASS))
    return objs


def pad_parts():
    return [K.gbox("padm", (LOG_C[0] - 0.075, 0.014, -0.13), (LOG_C[0] + 0.075, LOG_C[1], 0.13), PAPER, 0.003)]


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("strand_box4", [body_walnut(), body_brass()])
    lid = K.part("IA_box_lid", lid_parts(), pivot=HINGE)
    gears, knobs = [], []
    for k in range(4):
        gears.append(K.part(f"gear_pointer_{k + 1}", gear_parts(k), pivot=(GX[k], TOPY, GZ[k])))
        knobs.append(K.part(f"IA_knob_{k + 1}", knob_parts(k), pivot=(GX[k], KY, KZ)))
    log = K.part("IA_box_log", pad_parts(), pivot=LOG_C)
    K.empty("log_mount", LOG_C)
    K.empty("orrery_mount", ORR_C)
    K.to_blender()
    for g in gears:
        K.parent(g, lid)
    K.parent(bpy.data.objects["log_mount"], log)
    C.finalize()
    return dict(body=body, lid=lid, gears=gears, knobs=knobs, log=log)


def verify(path):
    gp = [f"gear_pointer_{k + 1}" for k in range(4)]
    kn = [f"IA_knob_{k + 1}" for k in range(4)]
    req = ["strand_box4", "IA_box_lid", "IA_box_log", "log_mount", "orrery_mount"] + gp + kn
    ident = ["strand_box4", "IA_box_lid", "IA_box_log"] + gp + kn
    expect = {"strand_box4": (0.0, 0.0, 0.0), "IA_box_lid": HINGE, "IA_box_log": LOG_C, "log_mount": LOG_C, "orrery_mount": ORR_C}
    parents = {"log_mount": "IA_box_log"}
    for k in range(4):
        expect[gp[k]] = (GX[k], TOPY, GZ[k])
        expect[kn[k]] = (GX[k], KY, KZ)
        parents[gp[k]] = "IA_box_lid"
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents=parents, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in ["strand_box4", "IA_box_lid", "gear_pointer_1", "IA_knob_1", "IA_box_log"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa_table(parts):
    """A neutral QA stage: a dark walnut table top under the box, the orrery / log neighbours when they exist, soft lights."""
    C.qa_begin()
    M.material("M_Wood_Walnut")
    top = M.box("qa_table", (1.6, 1.0, 0.04), loc=K.G(0.0, -0.02, 0.0), mat="M_Wood_Walnut")
    return top


def qa(args, parts):
    qa_table(parts)
    root = K.qa_place([parts["body"], parts["lid"], parts["log"]] + parts["knobs"], (0.0, 0.0, 0.0), 0.0, name="qa_box_root")
    orr = C.qa_import("orrery", ORR_C, 0.0, prefix="qa_orr_")
    if orr is not None:
        orr.parent = root
    log = C.qa_import("strand_log", LOG_C, 0.0, prefix="qa_log_")
    if log is not None:
        log.parent = root
    M.refresh()
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, strength=1.0):
        K.clear_lights()
        K.light("key", "POINT", (0.5, 1.0, 0.7), 260.0 * strength, "FFE2C0", radius=0.15)
        K.light("fill", "POINT", (-0.7, 0.6, 0.9), 80.0 * strength, "BFD4FF", radius=0.2)
        K.light("rim", "POINT", (0.2, 0.8, -0.8), 90.0 * strength, "FFFFFF", radius=0.15)
    if C.want(args, "1"):          # closed, from the front above (the gear_box camera proposal)
        cam, tgt, fov = (0.0, 0.62, 0.62), (0.0, 0.10, 0.0), 42
        lit(cam)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a gear state: pointers 4-1-3-5, then the lid open with the orrery and the log
        for k, v in enumerate((4, 1, 3, 5)):
            K.pose_rot(parts["gears"][k], "y", -60.0 * v)
        cam, tgt, fov = (0.0, 0.46, 0.34), (0.0, 0.17, 0.0), 40
        lit(cam)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # open
        K.pose_rot(parts["lid"], "x", -110.0)
        cam, tgt, fov = (0.0, 0.50, 0.55), (0.0, 0.12, -0.02), 46
        lit(cam)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)


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
    F.backface_check(label=NAME, res=400)
    qa(args, parts)


main()
