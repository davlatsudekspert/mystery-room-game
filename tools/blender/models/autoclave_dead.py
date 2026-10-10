"""autoclave_dead.glb — the Nursery's three dead autoclaves (dead_0..2 at (9.65 / 10.9 / 12.15, 0, -3.5), yaw 0).
Contract: docs/models/ch3.md §6 autoclave_dead (+ §10 echo_technicians, §2 port_a_mem); results: docs/models/ch3_d.md.

The working autoclave's silhouette without the pedestal: everything static and merged per material into ONE mesh
object `autoclave_dead` (M_Chrome, M_Steel_Dark, M_Glass_Frosted = 3 surfaces): the vessel on its frame, the door
baked ajar by 10° with a frosted dead window, a pressure gauge with a frosted glass (tech_a reads it), a drain line
with a hand-wheel valve (tech_b turns it), rime on the top nozzle and icicles under the girth flange.

  echo_mount   floor empty facing -Z (rotated 180° about +Y): echo_technicians' tech_a / tech_b, parented with
               identity, stand facing the vessel. Its z (ECHO_Z) is set so both figures clear the vessel and the
               ajar door; the gauge and the valve hand-wheel sit at the figures' gaze / hand points (ch3_h.md).

    blender -b --factory-startup -P tools/blender/models/autoclave_dead.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "autoclave_dead"
TRI_BUDGET, SURF_BUDGET = 3500, 3
CHROME, STEEL, FROST = D.CHROME, D.STEEL, D.FROST

ECHO_Z = float(os.environ.get("MR_ECHO_Z", "0.95"))   # contract 0.62; moved out so tech_a / tech_b clear the
#                                                        vessel (measured in ch3_d.md; MR_ECHO_Z overrides for tests)
AJAR = -10.0                        # the door, baked ajar (negative = toward the viewer)
# echo_technicians contact data (figure frame, docs/models/ch3_h.md): tech_b's hand-wheel centre, tech_a's gaze
TECH_B_WHEEL = (-0.04, 0.40, 0.26)
TECH_A_GAZE = (-0.05, 1.45, 0.20)


def fig_to_model(p):
    """Figure-frame point -> model point for a figure parented to echo_mount (180° about +Y at (0, 0, ECHO_Z))."""
    return (-p[0], p[1], ECHO_Z - p[2])


WHEEL = fig_to_model(TECH_B_WHEEL)                     # (0.04, 0.40, ECHO_Z - 0.26)
GAUGE = (0.10, 1.53)                                    # on the vessel front, ahead of tech_a and slightly to her right


def gauge():
    gx, gy = GAUGE
    zv = math.sqrt(D.R_V ** 2 - gx ** 2)
    ch, st, fr = [], [], []
    ch.append(D.rod("gstub", (gx, gy, zv - 0.02), (gx, gy, zv + 0.045), 0.010, 6, CHROME))
    st.append(D.hexnut("gnut", 0.014, (gx, gy, zv + 0.012), (0, 0, 1), h=0.012))
    z0 = zv + 0.045
    st.append(K.glathe("gcase", [(0.058, 0.0), (0.064, 0.004), (0.064, 0.031), (0.0, 0.031)], (gx, gy, z0), (0, 0, 1),
                       12, STEEL, smooth=45.0, cap_bottom=False))
    ch.append(D.ring("gbezel", 0.054, 0.068, z0 + 0.029, z0 + 0.040, (gx, gy, 0.0), (0, 0, 1), 12, CHROME))
    ch.append(D.disc("gface", 0.0585, (gx, gy, z0 + 0.0315), (0, 0, 1), CHROME, 12))
    for k in range(6):
        a = math.radians(225 - 54 * k)
        t = D.quad01("gtick", (0.0, 0.046, 0.0), 0.0032, 0.012, STEEL)
        t.data.transform(Matrix.Translation((gx, gy, z0 + 0.0318)) @ Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        st.append(t)
    nd = K.plate("gneedle", [[(-0.0022, -0.008), (0.0022, -0.008), (0.0006, 0.046), (-0.0006, 0.046)]], 0.0006,
                 z0=0.0, mat=STEEL, bevel=0.0)
    nd.data.transform(Matrix.Translation((gx, gy, z0 + 0.0322)) @ Matrix.Rotation(math.radians(135), 4, "Z"))
    st.append(nd)                                       # dead: the needle sits on the stop pin, below zero
    fr.append(D.disc("gglass", 0.0555, (gx, gy, z0 + 0.0365), (0, 0, 1), FROST, 12))
    return ch, st, fr


def drain_valve():
    """Drain line from the vessel's lower front straight out to an angle valve; its hand-wheel (Ø 0.08) faces +Z at
    tech_b's grip point; the outlet drops to a floor gully."""
    wx, wy, wz = WHEEL
    st, ch, fr = [], [], []
    zv = math.sqrt(D.R_V ** 2 - wx ** 2)
    body_z = wz - 0.055
    st.append(D.tube("dline", [(wx, wy, zv - 0.02), (wx, wy, body_z)], 0.018, 8, STEEL))
    st.append(D.ring("dflange", 0.0, 0.034, zv - 0.004, zv + 0.010, (wx, wy, 0.0), (0, 0, 1), 8, STEEL))
    st.append(K.glathe("vbody", [(0.0, -0.034), (0.026, -0.030), (0.032, 0.0), (0.026, 0.030), (0.0, 0.034)],
                       (wx, wy, body_z), (0, 0, 1), 8, STEEL, smooth=50.0))
    st.append(K.gcyl("vbonnet", 0.016, 0.030, 0.050, base=(wx, wy, body_z), axis=(0, 0, 1), segments=6, mat=STEEL))
    st.append(K.gcyl("vstem", 0.005, 0.050, wz - body_z + 0.004, base=(wx, wy, body_z), axis=(0, 0, 1), segments=6,
                     mat=STEEL, caps=False))
    st.append(D.tube("vout", [(wx, wy - 0.02, body_z), (wx, 0.06, body_z)], 0.016, 8, STEEL))
    st.append(K.glathe("gully", [(0.05, 0.0), (0.05, 0.006), (0.035, 0.006), (0.0, 0.002)], (wx, 0.0, body_z),
                       (0, 1, 0), 8, STEEL, cap_bottom=False))
    # the hand-wheel: rim r 0.04 (tube r 0.005), four spokes, hub
    rim = M.torus("vwheel", 0.035, 0.005, major_seg=12, minor_seg=4, mat=CHROME)
    rim.data.transform(Matrix.Translation((wx, wy, wz)))
    ch.append(rim)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ch.append(D.rod("vspoke", (wx, wy, wz), (wx + 0.034 * math.cos(a), wy + 0.034 * math.sin(a), wz), 0.0035, 4,
                        CHROME, caps=False))
    ch.append(K.gcyl("vhub", 0.009, -0.006, 0.006, base=(wx, wy, wz), axis=(0, 0, 1), segments=6, mat=CHROME))
    fr.append(M.torus("vrime", 0.026, 0.006, major_seg=8, minor_seg=4, mat=FROST))
    fr[-1].data.transform(Matrix.Translation((wx, wy, body_z)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    return ch, st, fr


def frost():
    """Rime on the top nozzle (under the shell's frosted drop) and icicles under the girth flange."""
    out = [K.glathe("rime", [(0.064, 2.04), (0.080, 2.065), (0.094, 2.10), (0.092, 2.118), (0.060, 2.122)],
                    (0, 0, 0), (0, 1, 0), 10, FROST, cap_bottom=False, cap_top=False, smooth=60.0)]
    import random
    rng = random.Random(7)
    for deg in (-150, -112, -70, 62, 96, 128, 160, 200):
        a = math.radians(deg)
        ln = rng.uniform(0.03, 0.07)
        r = 0.448
        base = (r * math.sin(a), 1.853, r * math.cos(a))
        out.append(K.glathe("icicle", [(0.0065, 0.0), (0.0, -ln)], base, (0, 1, 0), 5, FROST, cap_bottom=False))
    return out


def body():
    shell = D.autoclave_shell(seg=24, lite=True)
    ch, st = shell[D.CHROME], shell[D.STEEL]
    dparts, glass = D.ac_door(AJAR, seg=16, frost=True, lite=True)
    ch += dparts
    fr = [glass]
    a, b, c = gauge()
    ch += a
    st += b
    fr += c
    a, b, c = drain_valve()
    ch += a
    st += b
    fr += c
    fr += frost()
    # a steel name plate with the Institute mark (no brass slot on the dead model)
    st.append(K.plate("nplate", [L.rounded_rect(0.15, 0.085, 0.008, 2)], 0.003, z0=0.428, mat=STEEL, bevel=0.0,
                      loc=(0.0, 0.66, 0.0)))
    mk = S.inlay("nmark", "mark", 0.055, depth=0.0, mat=CHROME)
    mk.data.transform(Matrix.Translation((0.0, 0.66, 0.4313)))
    ch.append(mk)
    D.tri_breakdown(ch + st + fr, NAME)
    return K.part(NAME, ch + st + fr)


def build():
    M.reset_scene()
    D.ensure_materials()
    out = dict(body=body())
    out["mount"] = K.empty("echo_mount", (0.0, 0.0, ECHO_Z), (0.0, 180.0, 0.0))
    K.to_blender()
    D.finalize()
    return out


def verify(path):
    req = [NAME, "echo_mount"]
    errs = D.verify(path, required=req, identity=[NAME], expect={NAME: (0, 0, 0), "echo_mount": (0.0, 0.0, ECHO_Z)},
                    parents={NAME: None, "echo_mount": None}, rot_expect={"echo_mount": (0, 180, 0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=3)
    lo, hi = D.bounds([NAME])
    print(f"{D.TAG} bounds {lo} .. {hi}")
    print(f"{D.TAG} valve wheel centre {tuple(round(c, 4) for c in WHEEL)}, gauge centre ({GAUGE[0]}, {GAUGE[1]}), "
          f"tech_a gaze target (model) {tuple(round(c, 4) for c in fig_to_model(TECH_A_GAZE))}")
    return errs


# ====================================================================== QA
def techs(mount_obj, which, prefix):
    """echo_technicians imported under echo_mount (identity); keep only `which` (tech_a / tech_b)."""
    h = D.attach("echo_technicians", mount_obj, prefix)
    if h is None:
        return None, []
    keep = []
    for o in h.children_recursive:
        if o.type != "MESH":
            continue
        if o.name == prefix + which:
            keep.append(o)
        else:
            o.hide_render = True
            o.hide_viewport = True
    return h, keep


def clearance(parts, figs):
    n, dmin = D.mesh_clearance(figs, [parts["body"]])
    return n, dmin


def qa(parts, args):
    D.qa_begin()
    mount = parts["mount"]
    roots = D.roots()
    D.place(roots, D.DEAD_POS[0], 0.0, name="qa_place_dead0")
    # tech_a at this instance (dead_0); a second instance at dead_1 with tech_b
    _ha, fig_a = techs(mount, "tech_a", "qa_ta_")
    measure = "--measure" in args
    D.room(shell=not measure,
           extra=[("autoclave", D.AC_POS, 0.0, "qa_ac_"), ("autoclave_dead", D.DEAD_POS[1], 0.0, "qa_d1_"),
                  ("autoclave_dead", D.DEAD_POS[2], 0.0, "qa_d2_"), ("growth_log", D.world_point(D.AC_POS, 0.0,
                                                                                                (0.30, 1.66, 0.40)),
                                                                     0.0, "qa_log_")])
    m1 = bpy.data.objects.get("qa_d1_echo_mount")
    _hb, fig_b = techs(m1, "tech_b", "qa_tb_") if m1 is not None else (None, [])
    gm = D.ghost_material()
    for f in fig_a + fig_b:
        K.override(f, gm)
    if fig_a:
        n, d = D.mesh_clearance(fig_a, [parts["body"]])
        print(f"{D.TAG} tech_a vs autoclave_dead: {n} intersecting triangle pairs, nearest vertex {d * 100:.1f} cm")
    d1 = [o for o in bpy.data.objects if o.name.startswith("qa_d1_autoclave_dead") and o.type == "MESH"]
    if fig_b and d1:
        n, d = D.mesh_clearance(fig_b, d1)
        print(f"{D.TAG} tech_b vs autoclave_dead: {n} intersecting triangle pairs, nearest vertex {d * 100:.1f} cm")
    if measure:
        for fig, nm in ((fig_a, "tech_a"), (fig_b, "tech_b")):
            if fig:
                lo, hi = K.V.mesh_bounds_godot(fig)
                print(f"{D.TAG} {nm} world bounds z {lo.z:+.3f} .. {hi.z:+.3f} (vessel front z = {-3.5 + D.R_V:+.3f})")
        return
    W0 = lambda p: D.world_point(D.DEAD_POS[0], 0.0, p)   # noqa: E731

    # 1 hero: the dead autoclave alone (figures hidden), three-quarter from the front left
    if K.want(args, "1"):
        for f in fig_a + fig_b:
            f.hide_render = True
        cam = W0((-1.0, 1.6, 1.85))
        D.lights(cam, fill=12.0)
        D.shoot(NAME, cam, W0((0.05, 1.1, 0.1)), 50)
        for f in fig_a + fig_b:
            f.hide_render = False
    # 2 port_a_mem (§2): the two kept technicians at dead_0 / dead_1
    if K.want(args, "2"):
        D.lights((9.1, 1.6, 0.4), fill=0.0)
        D.shoot(NAME + "_2", (9.1, 1.6, 0.4), (10.3, 1.0, -2.45), 50)
    # 3 tech_a at the gauge, side view (clearance of the clipboard and the ajar door)
    if K.want(args, "3"):
        cam = W0((1.45, 1.35, 0.75))
        D.lights(cam, fill=8.0)
        D.shoot(NAME + "_3", cam, W0((0.0, 1.15, 0.62)), 46)
    # 4 tech_b at the drain valve, close (his right hand on the hand-wheel)
    if K.want(args, "4"):
        W1 = lambda p: D.world_point(D.DEAD_POS[1], 0.0, p)   # noqa: E731
        cam = W1((0.75, 0.75, 1.30))
        D.lights(cam, fill=8.0)
        D.shoot(NAME + "_4", cam, W1((0.04, 0.42, WHEEL[2])), 40)
    # 5 the dead row from the nursery_w root view
    if K.want(args, "5"):
        D.lights()
        D.shoot(NAME + "_5", (12.2, 1.65, 2.9), (9.8, 1.2, -2.6), 62)
    # 6 close-up of the ajar door, frosted window, gauge (figures hidden)
    if K.want(args, "6"):
        for f in fig_a + fig_b:
            f.hide_render = True
        cam = W0((0.35, 1.45, 1.05))
        D.lights(cam, fill=10.0)
        D.shoot(NAME + "_6", cam, W0((0.0, 1.30, 0.42)), 44)
        for f in fig_a + fig_b:
            f.hide_render = False


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
