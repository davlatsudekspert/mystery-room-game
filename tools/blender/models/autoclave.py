"""autoclave.glb — the Nursery's working autoclave (E2 crystal growth). Free-standing at (8.4, 0, -3.5), yaw 0.
Contract: docs/models/ch3.md §6 autoclave (+ §2 views autoclave / cam_drum / growth_log / grow); results:
docs/models/ch3_d.md.

  autoclave_body    (static) chrome pressure vessel Ø 0.85 (y 0.36 .. 1.95, domed to 2.10) on a steel frame, lagging
                    bands, bolted girth flange, top nozzle under the shell's frosted drop, safety valve, pipes to the
                    wall, the manway neck / flange / hinge knuckles, the chamber (r 0.20, back wall z 0.10) with the
                    brass seat stand, a pressure gauge (needle fixed), the log hook bracket, the brass name plate, the
                    control pedestal x 0.10 .. 0.50, z 0.45 .. 0.80, top 0.95 with the brass cam drum Ø 0.16 x 0.30
                    (axis X through (0.30, 1.05, 0.62), 3 columns x 6 holes with 1..6 engraved pips), its bearings,
                    the lever bracket + quadrant, the remelt escutcheon (flame cut-out) and the lamp bezel
  IA_ac_door        round door Ø 0.42 centred (0, 1.20, 0.45); pivot (-0.21, 1.20, 0.46); open = -110° about +Y
    growth_window   (child) glass porthole Ø 0.24 (code: frost, inner glow)
  IA_peg_0..2       brass pegs at x 0.20 / 0.30 / 0.40, pivot on the drum axis (x_i, 1.05, 0.62); rest = hole 1
                    (30° above the front horizontal); hole p = -24° x (p - 1) about local +X
  IA_start_lever    brass lever, pivot (0.52, 0.95, 0.62); pull = +60° about local +X
  IA_remelt         brass push button with a flame relief at (0.20, 0.80, 0.81); press = -0.006 along local Z
  ac_lamp           glass jewel at (0.42, 0.97, 0.75) (code: amber / green / red)
  chamber_mount     (0, 1.08, 0.30), up +Y: the seed's collar sits on the seat (seat top y = 1.0712 = mount - 0.0088)
  log_mount         (0.30, 1.66, 0.40): the growth_log hangs here with identity (hook pin top)
  steam_origin      (0, 1.45, 0.47)

    blender -b --factory-startup -P tools/blender/models/autoclave.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "autoclave"
TRI_BUDGET, SURF_BUDGET = 9000, 12
CHROME, STEEL, BRASS, GLASS = D.CHROME, D.STEEL, D.BRASS, D.GLASS

PED = (0.10, 0.50, 0.45, 0.80, 0.95)          # x0, x1, z0, z1, top y
DRUM_C = (0.30, 1.05, 0.62)
DRUM_R, DRUM_X0, DRUM_X1 = 0.08, 0.15, 0.45
PEG_X = (0.20, 0.30, 0.40)
LEVER_P = (0.52, 0.95, 0.62)
REMELT = (0.20, 0.80, 0.81)
LAMP = (0.42, 0.97, 0.75)
CHAMBER = (0.0, 1.08, 0.30)
SEAT_Y = CHAMBER[1] - 0.0088                  # seed_crystal collar bottom (docs/models/ch3_g.md)
LOG_MOUNT = (0.30, 1.66, 0.40)
STEAM = (0.0, 1.45, 0.47)
GAUGE = (-0.245, 1.62)
WINDOW_C = (0.0, 1.20, 0.454)
CRYSTAL_UP = 0.0569 - 0.0088                  # nursery_crystal stands 0.0481 higher than the seed on the same seat


def hole_angle(p):
    """Hole p (1..6) in degrees above the front horizontal, over the top to the back."""
    return 30.0 + 24.0 * (p - 1)


def drum_point(x, deg, r):
    a = math.radians(deg)
    return Vector((x, DRUM_C[1] + r * math.sin(a), DRUM_C[2] + r * math.cos(a)))


# ====================================================================== static body
def pedestal():
    x0, x1, z0, z1, top = PED
    st, br = [], []
    st.append(D.box("ped", (x0, 0.06, z0), (x1, top - 0.02, z1), STEEL, 0.006))
    st.append(D.box("ped_toe", (x0 + 0.02, 0.0, z0 + 0.02), (x1 - 0.02, 0.07, z1 - 0.025), STEEL, 0.004))
    st.append(D.box("ped_top", (x0 - 0.006, top - 0.022, z0 - 0.006), (x1 + 0.006, top, z1 + 0.006), STEEL, 0.004))
    # front access panel with four brass screws
    st.append(D.box("ped_panel", (x0 + 0.03, 0.13, z1), (x1 - 0.03, 0.70, z1 + 0.005), STEEL, 0.003))
    for (sx, sy) in ((x0 + 0.045, 0.145), (x1 - 0.045, 0.145), (x0 + 0.045, 0.685), (x1 - 0.045, 0.685)):
        br.append(K.rivet("ps", 0.006, (sx, sy, z1 + 0.005), segs=6, mat=BRASS))
    # ventilation slots on the left side
    for k in range(5):
        y = 0.30 + 0.045 * k
        st.append(D.box("vent", (x0 - 0.004, y, z0 + 0.09), (x0, y + 0.018, z1 - 0.09), STEEL, 0.0))
    # drum bearings: cheeks with round housings, brass caps
    for (cx0, cx1, cap) in ((0.128, 0.146, -1), (0.454, 0.472, 1)):
        st.append(D.box("cheek", (cx0, top, DRUM_C[2] - 0.045), (cx1, DRUM_C[1], DRUM_C[2] + 0.045), STEEL, 0.0))
        st.append(K.gcyl("hous", 0.045, cx0, cx1, base=(0, DRUM_C[1], DRUM_C[2]), axis=(1, 0, 0), segments=16,
                         mat=STEEL))
        xc = cx0 if cap < 0 else cx1
        br.append(K.glathe("bcap", [(0.024, 0.0), (0.024, 0.006), (0.018, 0.011), (0.0, 0.012)],
                           (xc, DRUM_C[1], DRUM_C[2]), (cap, 0, 0), 12, BRASS, smooth=45.0, cap_bottom=False))
    # lever bracket on the right face + brass quadrant showing the 60° travel
    lx, ly, lz = LEVER_P
    st.append(D.box("lbrk", (x1, ly - 0.08, lz - 0.055), (x1 + 0.006, ly + 0.045, lz + 0.055), STEEL, 0.002))
    quad = []
    for i in range(11):
        a = math.radians(-8 + 76 * i / 10)
        quad.append((math.sin(a) * 0.118, math.cos(a) * 0.118))
    for i in range(10, -1, -1):
        a = math.radians(-8 + 76 * i / 10)
        quad.append((math.sin(a) * 0.092, math.cos(a) * 0.092))
    q = K.plate("quadrant", [A.ccw(quad)], 0.003, z0=0.0, mat=BRASS, bevel=0.0005)
    q.data.transform(Matrix.Translation((x1 + 0.006, ly, lz)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    br.append(q)
    for deg in (0.0, 60.0):                             # stops / end ticks on the quadrant
        a = math.radians(deg)
        c = (x1 + 0.0105, ly + 0.123 * math.cos(a), lz + 0.123 * math.sin(a))
        br.append(K.gcyl("qstop", 0.005, -0.004, 0.004, base=c, axis=(1, 0, 0), segments=6, mat=BRASS))
    # remelt escutcheon: brass plate with the button hole and a flame cut-out (its inner tongue stays brass)
    ex, ey = REMELT[0], REMELT[1] + 0.022
    loops = [L.rounded_rect(0.060, 0.098, 0.010, 3),
             L.circle(0.0185, 16, cy=REMELT[1] - ey),
             [(x, y + 0.026) for (x, y) in D.flame_loop(0.028, n=6)],
             [(x, y + 0.026) for (x, y) in D.flame_inner(0.028)]]
    br.append(K.plate("resc", loops, 0.0016, z0=z1, mat=BRASS, bevel=0.0, loc=(ex, ey, 0.0)))
    br.append(D.ring("rbez", 0.0172, 0.0205, z1, z1 + 0.004, (REMELT[0], REMELT[1], 0.0), (0, 0, 1), 16, BRASS))
    # lamp bezel on the top
    br.append(D.ring("lbez", 0.0105, 0.019, top, top + 0.010, (LAMP[0], 0.0, LAMP[2]), (0, 1, 0), 12, BRASS))
    return st, br


def cam_drum():
    br, st = [], []
    x0, x1 = DRUM_X0, DRUM_X1
    L_ = x1 - x0
    prof = [(0.0, 0.0), (0.068, 0.0), (DRUM_R, 0.007), (DRUM_R, L_ - 0.007), (0.068, L_), (0.0, L_)]
    br.append(K.glathe("drum", prof, (x0, DRUM_C[1], DRUM_C[2]), (1, 0, 0), 36, BRASS, smooth=40.0,
                       phase=math.pi / 36))
    for xg in (0.25, 0.35):                              # column dividers: thin dark rings between the columns
        st.append(K.gcyl("cdiv", DRUM_R + 0.0005, xg - 0.0012, xg + 0.0012, base=(0.0, DRUM_C[1], DRUM_C[2]),
                         axis=(1, 0, 0), segments=36, mat=STEEL, caps=False, smooth=40.0))
    # 18 holes (dark) and their 1..6 dice pips to the right of each hole
    pip = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
           5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}
    s = 0.0047
    for x in PEG_X:
        for p in range(1, 7):
            deg = hole_angle(p)
            n = drum_point(0.0, deg, 1.0) - Vector((0.0, DRUM_C[1], DRUM_C[2]))
            st.append(D.disc("hole", 0.0060, tuple(drum_point(x, deg, DRUM_R + 0.0003)), tuple(n), STEEL, 8))
            for (gx, gt) in pip[p]:
                d2 = deg + math.degrees(gt * s / DRUM_R)
                nn = drum_point(0.0, d2, 1.0) - Vector((0.0, DRUM_C[1], DRUM_C[2]))
                st.append(D.disc("pip", 0.0016, tuple(drum_point(x + 0.026 + gx * s, d2, DRUM_R + 0.0003)), tuple(nn),
                                 STEEL, 6))
    return br, st


def gauge():
    gx, gy = GAUGE
    zv = math.sqrt(D.R_V ** 2 - gx ** 2)
    ch, st, gl = [], [], []
    ch.append(D.rod("gstub", (gx, gy, zv - 0.02), (gx, gy, 0.400), 0.010, 8, CHROME))
    st.append(D.hexnut("gnut", 0.014, (gx, gy, 0.366), (0, 0, 1), h=0.012))
    st.append(K.glathe("gcase", [(0.058, 0.0), (0.064, 0.004), (0.064, 0.031), (0.0, 0.031)],
                       (gx, gy, 0.398), (0, 0, 1), 20, STEEL, smooth=45.0, cap_bottom=False))
    ch.append(D.ring("gbezel", 0.054, 0.068, 0.427, 0.438, (gx, gy, 0.0), (0, 0, 1), 20, CHROME))
    ch.append(D.disc("gface", 0.0585, (gx, gy, 0.4295), (0, 0, 1), CHROME, 20))
    for k in range(11):                                   # 270° scale, major ticks every 2
        a = math.radians(225 - 27 * k)
        r0 = 0.040 if k % 2 == 0 else 0.045
        w = 0.0018 if k % 2 == 0 else 0.0012
        t = D.quad01("gtick", (0.0, (r0 + 0.052) / 2, 0.0), 2 * w, 0.052 - r0, STEEL)
        t.data.transform(Matrix.Translation((gx, gy, 0.4298)) @ Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        st.append(t)
    nd = K.plate("gneedle", [[(-0.0022, -0.008), (0.0022, -0.008), (0.0006, 0.046), (-0.0006, 0.046)]], 0.0006,
                 z0=0.0, mat=STEEL, bevel=0.0)
    nd.data.transform(Matrix.Translation((gx, gy, 0.4302)) @ Matrix.Rotation(math.radians(-40), 4, "Z"))
    st.append(nd)
    st.append(D.disc("ghub", 0.0045, (gx, gy, 0.4310), (0, 0, 1), STEEL, 10))
    gl.append(D.disc("gglass", 0.0555, (gx, gy, 0.4345), (0, 0, 1), GLASS, 24))
    return ch, st, gl


def log_hook():
    x, y, z = LOG_MOUNT
    yc = y - 0.0025
    zv = math.sqrt(D.R_V ** 2 - x ** 2)
    out = [D.box("hookblk", (x - 0.016, yc - 0.016, zv - 0.012), (x + 0.016, yc + 0.016, zv + 0.022), BRASS, 0.003)]
    out.append(D.rod("hookpin", (x, yc, zv + 0.02), (x, yc, z + 0.012), 0.0025, 8, BRASS))
    out.append(D.rod("hooktip", (x, yc, z + 0.012), (x, yc + 0.016, z + 0.016), 0.0025, 8, BRASS))
    return out


def chamber_seat():
    prof = [(0.0, 0.997), (0.034, 0.997), (0.034, 1.004), (0.013, 1.010), (0.0085, 1.016), (0.0085, 1.052),
            (0.0135, 1.058), (0.0135, SEAT_Y), (0.0, SEAT_Y)]
    return K.glathe("seat", prof, (CHAMBER[0], 0.0, CHAMBER[2]), (0, 1, 0), 16, BRASS, smooth=45.0)


def name_plate():
    br = [K.plate("nplate", [L.rounded_rect(0.15, 0.085, 0.008, 3)], 0.003, z0=0.428, mat=BRASS, bevel=0.0,
                  loc=(0.0, 0.66, 0.0))]
    st = []
    for (px, py) in ((-0.062, 0.03), (0.062, 0.03), (-0.062, -0.03), (0.062, -0.03)):
        br.append(K.rivet("nrv", 0.004, (px, 0.66 + py, 0.431), segs=6, mat=BRASS))
    mk = S.inlay("nmark", "mark_ticks", 0.060, depth=0.0, mat=STEEL)
    mk.data.transform(Matrix.Translation((0.0, 0.66, 0.4313)))
    st.append(mk)
    return br, st


def body():
    shell = D.autoclave_shell(seg=40)
    ch, st, br = shell[D.CHROME], shell[D.STEEL], []
    a, b = pedestal()
    st += a
    br += b
    a, b = cam_drum()
    br += a
    st += b
    gch, gst, ggl = gauge()
    ch += gch
    st += gst
    br += log_hook()
    br.append(chamber_seat())
    a, b = name_plate()
    br += a
    st += b
    return K.part("autoclave_body", ch + st + br + ggl)


# ====================================================================== moving parts
def door():
    parts, glass = D.ac_door(0.0, seg=28)
    d = K.part("IA_ac_door", parts, pivot=D.DOOR_PIVOT)
    w = K.part("growth_window", [glass], pivot=WINDOW_C)
    return d, w


def peg(i):
    x = PEG_X[i]
    deg = hole_angle(1)
    n = drum_point(0.0, deg, 1.0) - Vector((0.0, DRUM_C[1], DRUM_C[2]))
    prof = [(0.0, 0.070), (0.0048, 0.070), (0.0048, 0.096), (0.0072, 0.097), (0.0072, 0.101), (0.0092, 0.102, "k"),
            (0.0092, 0.116, "k"), (0.0072, 0.119), (0.0, 0.1205)]
    o = K.glathe("peg", prof, (x, DRUM_C[1], DRUM_C[2]), tuple(n), 10, BRASS, knurl=0.0009, smooth=40.0)
    return K.part(f"IA_peg_{i}", [o], pivot=(x, DRUM_C[1], DRUM_C[2]))


def start_lever():
    lx, ly, lz = LEVER_P
    ax = lx + 0.006
    parts = [K.gcyl("lboss", 0.022, lx - 0.011, lx + 0.016, base=(0, ly, lz), axis=(1, 0, 0), segments=14, mat=BRASS,
                    chamfer=0.003),
             K.glathe("larm", [(0.0, 0.0), (0.0100, 0.0), (0.0090, 0.10), (0.0072, 0.23), (0.0, 0.245)], (ax, ly, lz),
                      (0, 1, 0), 10, BRASS, smooth=50.0),
             K.glathe("lknob", [(0.0, -0.020), (0.010, -0.0175), (0.0175, -0.009), (0.020, 0.0), (0.0175, 0.010),
                                (0.010, 0.0175), (0.0, 0.020)], (ax, ly + 0.262, lz), (0, 1, 0), 12, BRASS,
                      smooth=60.0),
             K.gcyl("lnut", 0.009, lx + 0.016, lx + 0.024, base=(0, ly, lz), axis=(1, 0, 0), segments=6, mat=BRASS)]
    return K.part("IA_start_lever", parts, pivot=LEVER_P)


def remelt():
    x, y, z = REMELT
    parts = [K.glathe("rbtn", [(0.0165, 0.0), (0.0165, 0.0125), (0.0150, 0.0145), (0.0, 0.0145)],
                      (x, y, z - 0.012), (0, 0, 1), 16, BRASS, smooth=40.0, cap_bottom=False)]
    fl = K.plate("rflame", [D.flame_loop(0.019, n=5)], 0.0012, z0=0.0, mat=BRASS, bevel=0.0)
    fl.data.transform(Matrix.Translation((x, y + 0.0005, z + 0.0025)))
    parts.append(fl)
    return K.part("IA_remelt", parts, pivot=REMELT)


def lamp():
    x, y, z = LAMP
    o = K.glathe("jewel", [(0.0, 0.954), (0.0125, 0.954), (0.0125, 0.964), (0.0105, 0.974), (0.006, 0.980),
                           (0.0, 0.982)], (x, 0.0, z), (0, 1, 0), 12, GLASS, smooth=70.0)
    return K.part("ac_lamp", [o], pivot=LAMP)


# ====================================================================== build / verify
MOVING = ["IA_ac_door", "IA_peg_0", "IA_peg_1", "IA_peg_2", "IA_start_lever", "IA_remelt"]


def build():
    M.reset_scene()
    D.ensure_materials()
    out = dict(body=body())
    out["door"], out["window"] = door()
    out["pegs"] = [peg(i) for i in range(3)]
    out["lever"] = start_lever()
    out["remelt"] = remelt()
    out["lamp"] = lamp()
    out["chamber"] = K.empty("chamber_mount", CHAMBER)
    out["log"] = K.empty("log_mount", LOG_MOUNT)
    out["steam"] = K.empty("steam_origin", STEAM)
    K.to_blender()
    D.finalize()
    K.parent(out["window"], out["door"])
    return out


def verify(path):
    req = ["autoclave_body", "growth_window", "ac_lamp", "chamber_mount", "log_mount", "steam_origin"] + MOVING
    expect = {"IA_ac_door": D.DOOR_PIVOT, "growth_window": WINDOW_C, "IA_start_lever": LEVER_P, "IA_remelt": REMELT,
              "ac_lamp": LAMP, "chamber_mount": CHAMBER, "log_mount": LOG_MOUNT, "steam_origin": STEAM}
    expect.update({f"IA_peg_{i}": (PEG_X[i], DRUM_C[1], DRUM_C[2]) for i in range(3)})
    parents = {n: None for n in req}
    parents["growth_window"] = "IA_ac_door"
    errs = D.verify(path, required=req, identity=req, expect=expect, parents=parents, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET)
    lo, hi = D.bounds(["autoclave_body"])
    print(f"{D.TAG} body bounds {lo} .. {hi}")
    for n in MOVING + ["growth_window", "ac_lamp"]:
        lo, hi = D.bounds([n])
        print(f"{D.TAG} {n:16s} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, door_deg=0.0, pegs=(1, 1, 1), lever=False, pressed=False):
    for o in [parts["door"], parts["lever"], parts["remelt"]] + parts["pegs"]:
        o.matrix_basis = REST[o.name].copy()
    M.refresh()
    if door_deg:
        K.pose_rot(parts["door"], "y", door_deg)
    for o, p in zip(parts["pegs"], pegs):
        K.pose_rot(o, "x", -24.0 * (p - 1))
    if lever:
        K.pose_rot(parts["lever"], "x", 60.0)
    if pressed:
        K.pose_slide(parts["remelt"], (0.0, 0.0, -0.006))


def qa(parts, args):
    D.qa_begin()
    for o in [parts["door"], parts["lever"], parts["remelt"]] + parts["pegs"]:
        REST[o.name] = o.matrix_basis.copy()
    roots = D.roots()
    holder = D.place(roots, D.AC_POS, 0.0)
    D.room(extra=[("autoclave_dead", p, 0.0, f"qa_dead{k}_") for k, p in enumerate(D.DEAD_POS)])
    D.attach("growth_log", parts["log"], "qa_log_")
    sk = bpy.data.objects.get("qa_log_log_sketch")
    sk_mat = D.preview_material("qa_log_sketch", "log_sketch.png", rough=0.8)
    if sk is not None and sk_mat is not None:
        K.override(sk, sk_mat)
    seed = D.attach("seed_crystal", parts["chamber"], "qa_seed_")
    crystal = D.attach("nursery_crystal", parts["chamber"], "qa_cry_")
    if crystal is not None:
        crystal.matrix_basis = Matrix.Translation(K.V.C @ Vector((0.0, CRYSTAL_UP, 0.0)))
    M.refresh()

    def show(holder_obj, on):
        if holder_obj is None:
            return
        for o in [holder_obj] + list(holder_obj.children_recursive):
            o.hide_render = not on

    lamp_obj = parts["lamp"]
    amber = K.glow("qa_lamp_amber", "FFA030", 6.0)
    green = K.glow("qa_lamp_green", "40FF70", 6.0)
    glow_win = K.glow("qa_window_glow", "BFF2FF", 1.2)
    W = lambda p: D.world_point(D.AC_POS, 0.0, p)   # noqa: E731

    # 1 hero: three-quarter from the front right, door closed, the log on its hook, lamp green
    if K.want(args, "1"):
        pose(parts)
        show(seed, False)
        show(crystal, False)
        old = K.override(lamp_obj, green)
        cam = W((1.25, 1.65, 1.75))
        D.lights(cam, fill=14.0)
        D.shoot(NAME, cam, W((0.05, 1.10, 0.10)), 50)
        K.restore(lamp_obj, old)
    # 2 the autoclave view (§2), door closed, start state (pegs 1-1-1)
    if K.want(args, "2"):
        pose(parts)
        show(seed, False)
        show(crystal, False)
        D.lights((8.4, 1.55, -1.55))
        D.shoot(NAME + "_2", (8.4, 1.55, -1.55), (8.4, 1.15, -2.95), 54)
    # 3 the autoclave view, door open (-110°), the seed on its seat
    if K.want(args, "3"):
        pose(parts, door_deg=-110.0)
        show(seed, True)
        show(crystal, False)
        D.lights((8.4, 1.55, -1.55))
        D.shoot(NAME + "_3", (8.4, 1.55, -1.55), (8.4, 1.15, -2.95), 54)
    # 4 the cam_drum view at the target (pegs 5-2-4), lever pulled, lamp amber (growing)
    if K.want(args, "4"):
        pose(parts, pegs=(5, 2, 4), lever=True)
        show(seed, False)
        show(crystal, False)
        old = K.override(lamp_obj, amber)
        D.lights((8.7, 1.35, -2.25))
        D.shoot(NAME + "_4", (8.7, 1.35, -2.25), (8.7, 1.05, -2.88), 40)
        K.restore(lamp_obj, old)
    # 5 the cam_drum view at the start (pegs 1-1-1)
    if K.want(args, "5"):
        pose(parts)
        show(seed, False)
        show(crystal, False)
        D.lights((8.7, 1.35, -2.25))
        D.shoot(NAME + "_5", (8.7, 1.35, -2.25), (8.7, 1.05, -2.88), 40)
    # 6 the growth_log view
    if K.want(args, "6"):
        pose(parts)
        show(seed, False)
        show(crystal, False)
        D.lights((8.7, 1.55, -2.55), fill=8.0)
        D.shoot(NAME + "_6", (8.7, 1.55, -2.55), (8.7, 1.5, -3.1), 38)
    # 7 the grow view: door closed, the clear crystal behind the glowing window, lamp green
    if K.want(args, "7"):
        pose(parts)
        show(seed, False)
        show(crystal, True)
        old = K.override(lamp_obj, green)
        oldw = K.override(parts["window"], glow_win)
        D.lights((8.4, 1.3, -2.3))
        K.light("chamber", "POINT", W((0.0, 1.22, 0.22)), 1.5, "CFF6FF", radius=0.03)
        D.shoot(NAME + "_7", (8.4, 1.3, -2.3), (8.4, 1.2, -3.1), 40)
        K.restore(parts["window"], oldw)
        K.restore(lamp_obj, old)
    # 8 close-up: the remelt button pressed, the lamp red-free (amber), the lever and its quadrant
    if K.want(args, "8"):
        pose(parts, pegs=(3, 3, 3), pressed=True)
        show(seed, False)
        show(crystal, False)
        old = K.override(lamp_obj, amber)
        cam = W((0.62, 1.05, 1.18))
        D.lights(cam, fill=10.0)
        D.shoot(NAME + "_8", cam, W((0.33, 0.90, 0.72)), 40)
        K.restore(lamp_obj, old)
    # 9 the open door from the side: hinge, chamber, the grown crystal on the seat
    if K.want(args, "9"):
        pose(parts, door_deg=-110.0)
        show(seed, False)
        show(crystal, True)
        cam = W((-0.35, 1.35, 0.95))
        D.lights(cam, fill=10.0)
        K.light("chamber", "POINT", W((0.0, 1.30, 0.40)), 0.6, "FFFFFF", radius=0.03)
        D.shoot(NAME + "_9", cam, W((0.02, 1.15, 0.30)), 40)
    # 10 the Nursery root view with all four autoclaves
    if K.want(args, "10"):
        pose(parts)
        show(seed, False)
        show(crystal, False)
        D.lights()
        D.shoot(NAME + "_10", (5.7, 1.65, 3.3), (10.6, 1.3, -2.6), 62)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
