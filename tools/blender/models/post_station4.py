"""post_station4.glb — the watch room's pneumatic post station: destination dial with the six Chapter 2 pictograms, number wheel 1-9, canister, send lever, the tube into the ceiling
(Chapter 4, group G; secret S1). Contract: docs/models/ch4.md section 8 post_station4; results: docs/models/ch4_g.md.

LOCAL FRAME: origin = the floor on the wall plane (back z = 0) at the cabinet's centre, front = +Z; placed at the watch room's `post_mount`. Cabinet 0.90 w (x +-0.45) x 1.45 h x 0.40 d
on a 0.10 plinth, panel face at z = 0.40; the riser tube (O 0.10) stands on it at (0, ., 0.20) up to the ceiling flange at y = 3.30.
Nodes:
  post_station4      M_Steel_Dark + M_Brass_Aged + M_Enamel_Cream  the cabinet with a brass bezel, a header with the Institute's mark, the destination ring plate with the six pictograms as
                     cream enamel relief (d = 0 .. 5 clockwise at the clock positions 12, 2, 4, 6, 8, 10 round (-0.19, 1.00): the director's four-pointed star, a book, the flask, a film
                     reel, a letter, a padlock), the number wheel's recess with a fixed pointer, the lever's quadrant with two stops, the canister's tube mouth (a hollow brass tube back to z 0.12),
                     a pressure gauge, the riser tube with clamps and brackets and the ceiling flange
  IA_post_dial       M_Bakelite  the destination knob O 0.10 with a pointer ridge. ORIGIN = (-0.19, 1.00, 0.40), axis +Z; identity = d 0 (the star); position d (0..5) = -60 deg x d about +Z
  IA_post_number     M_Brass_Aged  the number wheel, a brass disc O 0.21 with the digits 1..9 in relief near the rim, digit n at +40 deg x (n - 1) counter-clockwise from 12 o'clock.
                     ORIGIN = (0.19, 1.00, 0.40), axis +Z; identity = 1 at the fixed pointer; number n (1..9) = -40 deg x (n - 1) about +Z
  IA_post_canister   M_Brass_Aged  the brass carrier O 0.09 x 0.26 lying along Z in the tube mouth, its front end 0.07 outside the collar. ORIGIN = its centre (0, 0.50, 0.34), identity.
                     The code slides it +0.35 along +Z when it is sent and "knocks back"
    canister_mount   child of IA_post_canister at its centre, identity
  IA_post_send       M_Brass_Aged  the send lever, an arm 0.30 with a ball grip. ORIGIN = the pivot (0.375, 0.74, 0.425); rest = upright (+Y); PULLED = +50 deg about +X (toward the player)

    blender -b --factory-startup -P tools/blender/models/post_station4.py [-- --no-render] [--shots=1,2]
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
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL, BAKE, CREAM  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "post_station4"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 8000, 12, 4
ZF = 0.40
D_C = (-0.19, 1.00, ZF)
W_C = (0.19, 1.00, ZF)
L_P = (0.375, 0.74, 0.425)
M_C = (0.0, 0.50, ZF)
CAN_C = (0.0, 0.50, 0.34)
TUBE = (0.0, 0.20)
TUBE_TOP = 3.30
DEST_KINDS = ("star", "book", "flask", "film", "envelope", "padlock")


def cabinet():
    s = F.MB(STEEL)
    s.box((-0.43, 0.0, 0.03), (0.43, 0.10, 0.37))                                  # the plinth
    s.box((-0.45, 0.10, 0.0), (0.45, 1.45, ZF))                                    # the carcass
    s.box((-0.46, 1.45, -0.01), (0.46, 1.49, ZF + 0.01))                           # the top cap
    for sx in (-1, 1):                                                              # side vents: five slots each
        for k in range(5):
            s.box((sx * 0.45 - (0.0 if sx > 0 else 0.004), 0.26 + 0.05 * k, 0.08), (sx * 0.45 + (0.004 if sx > 0 else 0.0), 0.28 + 0.05 * k, 0.32))
    # the recessed number wheel: a dark steel ring wall and floor is simply the panel; a raised steel collar round it
    cx, cy, cz = W_C
    s.cyl((cx, cy, ZF), (0, 0, 1), 0.125, 0.004, segs=32)
    # the destination ring plate (dark steel disc with the pictograms on it)
    cx, cy, cz = D_C
    s.cyl((cx, cy, ZF), (0, 0, 1), 0.185, 0.004, segs=40)
    # the lever's quadrant plate: a sector in the (z, y) plane about the pivot, two stops
    px, py, pz = L_P
    return [s.obj("post_steel")]


def brass_static():
    b = F.MB(BRASS)
    # panel bezel: four strips, header band, corner screws
    b.box((-0.45, 1.40, ZF), (0.45, 1.45, ZF + 0.010))
    b.box((-0.45, 0.10, ZF), (0.45, 0.15, ZF + 0.010))
    b.box((-0.45, 0.15, ZF), (-0.40, 1.40, ZF + 0.010))
    b.box((0.40, 0.15, ZF), (0.45, 1.40, ZF + 0.010))
    b.box((-0.40, 1.205, ZF), (0.40, 1.225, ZF + 0.006))                            # the rail under the header
    for sx in (-1, 1):
        for y in (0.20, 1.35):
            b.boss((sx * 0.425, y, ZF + 0.010), (0, 0, 1), 0.012, 0.004, sides=6)
    # rings round the ring plate and round the wheel recess (a low brass wall)
    for (c, r0, r1, h) in ((D_C, 0.185, 0.200, 0.014), (W_C, 0.118, 0.134, 0.014)):
        b.box((c[0] - 0.001, c[1] - 0.001, c[2]), (c[0] + 0.001, c[1] + 0.001, c[2] + 0.001))
    # the fixed pointer over the number wheel (a brass wedge pointing down at the top digit) and over the dial (a notch)
    b.prism([(W_C[0] - 0.014, W_C[1] + 0.150), (W_C[0] + 0.014, W_C[1] + 0.150), (W_C[0], W_C[1] + 0.124)], ZF, ZF + 0.008)
    # the lever's quadrant: two cheek plates with stops (a sector in the YZ plane about the pivot)
    px, py, pz = L_P
    for sx in (-1, 1):
        xa, xb = sorted((px + sx * 0.022, px + sx * 0.032))
        pts = [(pz, py)] + [(pz + 0.14 * math.sin(math.radians(a)), py + 0.14 * math.cos(math.radians(a))) for a in range(-10, 71, 10)]
        F.prism_yz(b.bm, pts, xa, xb)
    for a in (0.0, 50.0):
        s_ = math.radians(a)
        b.box((px - 0.034, py + 0.135 * math.cos(s_) - 0.010, pz + 0.135 * math.sin(s_) - 0.010), (px + 0.034, py + 0.135 * math.cos(s_) + 0.010, pz + 0.135 * math.sin(s_) + 0.010))
    b.box((px - 0.040, py - 0.045, ZF), (px + 0.040, py + 0.045, pz + 0.020))      # the pivot block
    # the canister's tube mouth: a hollow tube (outer 0.088, inner 0.056) from z 0.12 to the collar, a flared collar, a bottom disc
    mc = M_C
    prof = [(0.058, 0.12), (0.058, 0.50), (0.060, 0.47), (0.067, 0.462), (0.080, 0.452), (0.100, 0.440), (0.100, 0.425), (0.092, ZF - 0.005)]
    # lathe along Z about the mouth axis: profile (r, z) -> (r, h) with h = z
    o1 = K.glathe("mouth_in", [(0.0, 0.12), (0.056, 0.12), (0.056, 0.455)], base=(mc[0], mc[1], 0.0), axis=(0, 0, 1), segments=24, mat=BRASS, smooth=60.0, cap_bottom=False, cap_top=False)
    o2 = K.glathe("mouth_collar", [(0.056, 0.455), (0.062, 0.460), (0.074, 0.456), (0.092, 0.448), (0.106, 0.436), (0.106, 0.418), (0.100, 0.410), (0.100, ZF)], base=(mc[0], mc[1], 0.0),
                  axis=(0, 0, 1), segments=28, mat=BRASS, smooth=50.0, cap_bottom=False, cap_top=False)
    # the gauge: a bezel and a boss; its dial is cream (separate)
    gx, gy = -0.30, 0.30
    # the riser tube, its clamps, brackets and flange
    tx, tz = TUBE
    b.cyl((tx, 1.49, tz), (0, 1, 0), 0.062, 0.05, segs=18)
    b.cyl((tx, 1.49, tz), (0, 1, 0), 0.050, TUBE_TOP - 1.49, segs=18)
    for y in (1.85, 2.45, 3.00):
        b.cyl((tx, y, tz), (0, 1, 0), 0.064, 0.045, segs=18)
        b.bar((tx, y + 0.022, tz), (tx, y + 0.022, 0.0), 0.040, ref=(1, 0, 0))
        b.box((tx - 0.07, y - 0.01, 0.0), (tx + 0.07, y + 0.055, 0.012))
        for sx in (-1, 1):
            b.boss((tx + sx * 0.055, y + 0.022, 0.012), (0, 0, 1), 0.010, 0.006, sides=6)
    b.cyl((tx, TUBE_TOP - 0.05, tz), (0, 1, 0), 0.13, 0.05, segs=20)               # the ceiling flange
    b.cyl((tx, TUBE_TOP - 0.06, tz), (0, 1, 0), 0.075, 0.012, segs=18)
    # the rail of rivets round the header
    for i in range(16):
        b.dome((-0.38 + 0.0507 * i, 1.215, ZF + 0.006), 0.006, 0.0045, segs=5, normal=(0, 0, 1))
    return [b.obj("post_brass"), o1, o2]


def pictograms():
    out = []
    cx, cy, cz = D_C
    for d, kind in enumerate(DEST_KINDS):
        a = math.radians(60.0 * d)
        x, y = cx + 0.128 * math.sin(a), cy + 0.128 * math.cos(a)
        loops = F.picto_loops(kind, 0.060)
        out.append(K.plate(f"pg_{kind}", loops, 0.0030, z0=ZF + 0.004, mat=CREAM, bevel=0.0003, drop_bottom=True, loc=(x, y, 0.0)))
        # an index wedge on the inner side of every position (pointing at the knob)
        r0, r1 = 0.082, 0.096
        wedge = [(-0.006, 0.0), (0.006, 0.0), (0.0, -0.012)]
        w = K.plate(f"wedge{d}", [wedge], 0.0022, z0=ZF + 0.004, mat=CREAM, bevel=0.0002, drop_bottom=True,
                    loc=(cx + 0.087 * math.sin(a), cy + 0.087 * math.cos(a), 0.0), rot_z=-a + math.pi)
        out.append(w)
    # the gauge dial (cream) with ticks, bottom left
    gx, gy = -0.30, 0.30
    out.append(K.gcyl("gauge_dial", 0.052, ZF + 0.002, ZF + 0.008, base=(gx, gy, 0.0), axis=(0, 0, 1), segments=24, mat=CREAM))
    for k in range(9):
        a = math.radians(-120.0 + 30.0 * k)
        t = K.gbox("gt", (-0.0016, 0.036, ZF + 0.008), (0.0016, 0.048, ZF + 0.0105), CREAM, 0.0)
        t.data.transform(Matrix.Translation((gx, gy, 0.0)) @ Matrix.Rotation(-a, 4, "Z"))
        out.append(t)
    return out


def brass_gauge():
    gx, gy = -0.30, 0.30
    out = [K.glathe("gauge_bezel", [(0.052, ZF), (0.066, ZF), (0.066, ZF + 0.014), (0.060, ZF + 0.020), (0.052, ZF + 0.014)], base=(gx, gy, 0.0), axis=(0, 0, 1), segments=24, mat=BRASS,
                    smooth=50.0, cap_bottom=False, cap_top=False)]
    # lathe base is along Z from base z = 0: heights are absolute z
    out.append(K.gbox("gauge_needle", (gx - 0.0016, gy, ZF + 0.0085), (gx + 0.0016, gy + 0.042, ZF + 0.0105), BRASS, 0.0))
    out[-1].data.transform(Matrix.Translation((gx, gy, 0.0)) @ Matrix.Rotation(math.radians(-35.0), 4, "Z") @ Matrix.Translation((-gx, -gy, 0.0)))
    # Strand's mark on the header
    out.append(K.plate("mark", C.S.loops("mark", 0.125), 0.004, z0=ZF + 0.006, mat=BRASS, bevel=0.0004, drop_bottom=True, loc=(0.0, 1.31, 0.0)))
    return out


def dial_parts():
    cx, cy, cz = D_C
    out = [K.glathe("knob", [(0.0, 0.0), (0.056, 0.0), (0.056, 0.004), (0.048, 0.010), (0.046, 0.036), (0.040, 0.043), (0.0, 0.046)], base=(cx, cy, cz), axis=(0, 0, 1), segments=28, mat=BAKE,
                    smooth=50.0)]
    # a pointer ridge to 12 o'clock on the face and out over the skirt
    out.append(K.gbox("ridge", (cx - 0.0045, cy + 0.008, cz + 0.040), (cx + 0.0045, cy + 0.056, cz + 0.050), BAKE, 0.0006))
    # eight grip flutes on the side
    for k in range(8):
        a = math.radians(45.0 * k + 22.5)
        t = K.gbox("fl", (-0.0045, 0.0455, 0.012), (0.0045, 0.0495, 0.034), BAKE, 0.0)
        t.data.transform(Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(-a, 4, "Z"))
        out.append(t)
    return out


def number_parts():
    cx, cy, cz = W_C
    out = [K.glathe("disc", [(0.0, 0.0), (0.105, 0.0), (0.105, 0.006), (0.100, 0.012), (0.0, 0.012)], base=(cx, cy, cz), axis=(0, 0, 1), segments=36, mat=BRASS, smooth=50.0)]
    out.append(K.glathe("cap", [(0.0, 0.012), (0.030, 0.012), (0.030, 0.016), (0.022, 0.024), (0.0, 0.026)], base=(cx, cy, cz), axis=(0, 0, 1), segments=16, mat=BRASS, smooth=60.0))
    for n in range(1, 10):
        a = math.radians(40.0 * (n - 1))
        # digit n at +40 deg x (n - 1) counter-clockwise from 12 o'clock, top outward
        px, py = cx - 0.071 * math.sin(a), cy + 0.071 * math.cos(a)
        o = C.N.digit_obj(f"d{n}", n, 0.039, 0.0032, BRASS, res=1)
        o.data.transform(Matrix.Translation((px, py, cz + 0.012)) @ Matrix.Rotation(a, 4, "Z"))
        out.append(o)
    # two grip bosses
    for sg in (-1, 1):
        out.append(K.gcyl("grip", 0.008, cz + 0.012, cz + 0.022, base=(cx + sg * 0.040, cy - 0.002, 0.0), axis=(0, 0, 1), segments=8, mat=BRASS, chamfer=0.002))
    return out


def canister_parts():
    cx, cy, cz = CAN_C
    # along Z about the centre, 0.26 long, O 0.09: rolled beads at both ends and a mid band, domed ends
    h = 0.13
    prof = [(0.0, -h), (0.032, -h), (0.040, -h + 0.008), (0.045, -h + 0.020), (0.0455, -h + 0.034), (0.040, -h + 0.042), (0.040, -0.06), (0.044, -0.054), (0.044, -0.034), (0.040, -0.028),
            (0.040, 0.028), (0.044, 0.034), (0.044, 0.054), (0.040, 0.060), (0.040, h - 0.042), (0.0455, h - 0.034), (0.045, h - 0.020), (0.040, h - 0.008), (0.030, h - 0.002), (0.0, h)]
    o = K.glathe("can", prof, base=(cx, cy, cz), axis=(0, 0, 1), segments=22, mat=BRASS, smooth=50.0)
    return [o]


def lever_parts():
    px, py, pz = L_P
    out = [K.gcyl("pin", 0.018, -0.040, 0.040, base=(px, py, pz), axis=(1, 0, 0), segments=14, mat=BRASS, chamfer=0.004)]
    prof = [(0.0, 0.0), (0.014, 0.0), (0.012, 0.18), (0.016, 0.205), (0.030, 0.235), (0.034, 0.262), (0.028, 0.288), (0.012, 0.300), (0.0, 0.302)]
    out.append(K.glathe("arm", prof, base=(px, py, pz), axis=(0, 1, 0), segments=16, mat=BRASS, smooth=55.0))
    return out


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("post_station4", cabinet() + brass_static() + pictograms() + brass_gauge())
    dial = K.part("IA_post_dial", dial_parts(), pivot=D_C)
    number = K.part("IA_post_number", number_parts(), pivot=W_C)
    can = K.part("IA_post_canister", canister_parts(), pivot=CAN_C)
    send = K.part("IA_post_send", lever_parts(), pivot=L_P)
    K.empty("canister_mount", CAN_C)
    K.to_blender()
    K.parent(bpy.data.objects["canister_mount"], can)
    C.finalize()
    return dict(body=body, dial=dial, number=number, can=can, send=send)


def verify(path):
    req = ["post_station4", "IA_post_dial", "IA_post_number", "IA_post_canister", "IA_post_send", "canister_mount"]
    ident = req[:5]
    expect = {"post_station4": (0.0, 0.0, 0.0), "IA_post_dial": D_C, "IA_post_number": W_C, "IA_post_canister": CAN_C, "IA_post_send": L_P, "canister_mount": CAN_C}
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents={"canister_mount": "IA_post_canister"}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req[:5]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    M.material("M_Concrete")
    M.material("M_Paint_Green")
    M.box("qa_wall", (3.0, 0.1, 3.6), loc=K.G(0.0, 1.8, -0.05), mat="M_Paint_Green")
    M.box("qa_floor", (3.0, 3.0, 0.05), loc=K.G(0.0, -0.025, 1.4), mat="M_Concrete")
    SM = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, strength=1.0):
        K.clear_lights()
        K.light("key", "POINT", (-0.5, 2.0, 1.6), 260.0 * strength, "FFE2C0", radius=0.2)
        K.light("fill", "POINT", (1.5, 1.2, 2.0), 90.0 * strength, "BFD4FF", radius=0.3)
        K.light("rim", "POINT", (0.0, 1.8, 1.0), 60.0 * strength, "FFD9A0", radius=0.2)
    if C.want(args, "1"):          # the whole station from the room, canister in place
        cam, tgt, fov = (-0.2, 1.55, 3.0), (0.0, 1.6, 0.0), 54
        lit(cam)
        C.shoot(NAME, cam, tgt, fov, samples=SM, res=RES)
    if C.want(args, "2"):          # the panel: dial on the flask (d 2), number 7, lever pulled, the canister knocked back
        K.pose_rot(parts["dial"], "z", -60.0 * 2)
        K.pose_rot(parts["number"], "z", -40.0 * 6)
        K.pose_rot(parts["send"], "x", 50.0)
        K.pose_slide(parts["can"], (0.0, 0.0, 0.35))
        cam, tgt, fov = (-0.15, 1.15, 1.35), (0.0, 0.85, 0.40), 46
        lit(cam)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=SM, res=RES)


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
