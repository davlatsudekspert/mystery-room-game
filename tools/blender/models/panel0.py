"""panel0.glb — Panel 0, the hall's distribution board (Chapter 4, group B), a free-standing steel switchboard on the pier wall
under the bridge: five toggle switches I-V in a column, four line lamps LOCK / LIGHT / ARRAY / VENT (pictograms, no words) over
a matrix of brass buses and switch wires with 20 toggled junction dots, Strand's plate (four filled discs), Leyla's chalk (her
sign, four tally strokes, 1998), and the big main lever. Contract: docs/models/ch4.md section 4 panel0; results: docs/models/ch4_b.md.

At (0, 0, 14.0), yaw 180 (faces north). Origin = floor level at the centre of the BACK face, on the wall plane; local +Z = the
front. Board x +-0.95, y 0.2 - 2.1, z 0 - 0.22 (face at z = 0.22), plinth to y 0.2. Local coordinates:
  panel_body    M_Steel_Painted  plinth, cabinet, raised bezel (face z 0.25 at the border), corner bolts
  panel_brass   M_Brass_Aged     4 line buses at x = -0.30 / 0 / 0.30 / 0.60 (y 0.40 - 1.60), 5 switch wires at y_s = 1.42 / 1.18 /
                                 0.94 / 0.70 / 0.46 (x -0.66 .. 0.72), Strand's plate (1.14 x 0.14 at (0.15, 2.00)) with 4 discs
                                 over the lamps, the lamp bezels, 4 pictograms at y 1.70, numerals I..V at x -0.90, switch collars,
                                 the main lever's quadrant guide
  leyla_chalk   M_Chalk          her sign, 1998 and four tally strokes on the lower left, 2 mm proud
  lamp_lock / lamp_light / lamp_array / lamp_vent   M_Glass_Dark domes r 0.035 at (-0.30 / 0 / 0.30 / 0.60, 1.86, 0.22)
  IA_switch_1..5   M_Brass_Aged  toggles, ORIGIN (-0.74, y_s, 0.22), neutral = straight out +Z (identity).
                   UP (on) = -40 deg about +X, DOWN (off) = +40 deg
  IA_main_lever    M_Brass_Aged  ORIGIN (0.84, 0.60, 0.24), rest = upright (+Y); PULLED = +60 deg about +X
  trace_<s>_<line> M_Brass_Aged  20 junction dots r 0.024 raised 4 mm at (x_line, y_s, 0.22); s = 1..5, line = lock | light |
                                 array | vent; the code shows the dot where v_panel[(s - 1) * 4 + line] = 1
  empties        echo_mount_tech_panel (0.8, 0, 1.0) yaw 180, panel_light (0, 2.4, 0.6)

    blender -b --factory-startup -P tools/blender/models/panel0.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, B, D, PAINT, BRASS, GDARK, CHALK  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "panel0"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 10000, 40, 4
FACE = 0.22
LINES = ("lock", "light", "array", "vent")
LINE_X = (-0.30, 0.0, 0.30, 0.60)
ROW_Y = (1.42, 1.18, 0.94, 0.70, 0.46)
LAMP_Y = 1.86
SW_X = -0.74
LEVER_P = (0.84, 0.60, 0.24)


def arc(r, a0, a1, n, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def relief(name, loops, x, y, depth=0.003, mat=BRASS):
    """A brass relief from 2D loops (even-odd) at (x, y) on the face."""
    o = K.plate(name, loops, depth, z0=FACE, mat=mat, bevel=0.0004, drop_bottom=True, loc=(x, y, 0.0))
    return o


def pictograms():
    out = []
    # LOCK: a padlock
    body = L.rounded_rect(0.072, 0.050, 0.007, 2, 0.0, -0.020)
    shackle = arc(0.024, 180, 0, 8) + arc(0.0155, 0, 180, 8)
    shackle = [(x, y + 0.005) for (x, y) in shackle]
    out.append(relief("pg_lock", [body], LINE_X[0], 1.70))
    out.append(relief("pg_lock2", [shackle], LINE_X[0], 1.70))
    # LIGHT: the sun symbol (disc with 8 rays)
    out.append(C.S.inlay("pg_light", "sun", 0.090, depth=0.003, mat=BRASS, loc=(LINE_X[1], 1.70, FACE)))
    # ARRAY: concentric rings and a dot
    rings = [L.circle(0.040, 24), list(reversed(L.circle(0.033, 24))), L.circle(0.024, 20), list(reversed(L.circle(0.017, 20))), L.circle(0.008, 12)]
    out.append(relief("pg_array", rings, LINE_X[2], 1.70))
    # VENT: three stacked upward chevrons
    for k, y in enumerate((-0.030, 0.0, 0.030)):
        chev = [(-0.034, y), (0.0, y + 0.025), (0.034, y), (0.034, y - 0.011), (0.0, y + 0.014), (-0.034, y - 0.011)]
        out.append(relief(f"pg_vent{k}", [chev], LINE_X[3], 1.70))
    return out


def body_parts():
    out = [K.gbox("plinth", (-0.98, 0.0, 0.0), (0.98, 0.2, 0.2), PAINT, 0.006),
           K.gbox("cab", (-0.95, 0.2, 0.0), (0.95, 2.1, FACE), PAINT, 0.008)]
    for (a, b) in (((-0.95, 0.2, FACE), (0.95, 0.25, 0.25)), ((-0.95, 2.05, FACE), (0.95, 2.1, 0.25)),
                   ((-0.95, 0.25, FACE), (-0.90, 2.05, 0.25)), ((0.90, 0.25, FACE), (0.95, 2.05, 0.25))):
        out.append(K.gbox("bz", a, b, PAINT, 0.003))
    for sx in (-1, 1):
        for y in (0.30, 2.00):
            out.append(K.hexbolt("bolt", 0.018, (sx * 0.915, y, 0.25), normal=(0, 0, 1), mat=PAINT))
    out.append(K.gbox("cap", (-0.97, 2.1, -0.02), (0.97, 2.14, 0.24), PAINT, 0.006))
    return out


def brass_parts():
    out = []
    for x in LINE_X:                                                      # the four buses
        out.append(K.gbox("bus", (x - 0.004, 0.40, FACE), (x + 0.004, 1.60, FACE + 0.0015), BRASS, 0.0))
    for y in ROW_Y:                                                       # the five switch wires
        out.append(K.gbox("wire", (-0.66, y - 0.004, FACE), (0.72, y + 0.004, FACE + 0.0015), BRASS, 0.0))
    # Strand's plate with four filled discs over the lamps
    out.append(K.gbox("plate", (-0.42, 1.93, FACE), (0.72, 2.07, FACE + 0.006), BRASS, 0.002))
    for x in LINE_X:
        out.append(K.gcyl("disc", 0.034, FACE + 0.006, FACE + 0.012, base=(x, 2.00, 0.0), axis=(0, 0, 1), segments=18, mat=BRASS, chamfer=0.0015))
    for x in (-0.38, 0.68):
        out.append(K.rivet("pr", 0.008, (x, 1.955, FACE + 0.006), normal=(0, 0, 1), mat=BRASS, segs=6))
    # lamp bezels
    for x in LINE_X:
        out.append(D.ring("lb", 0.036, 0.050, FACE, FACE + 0.012, (x, LAMP_Y, 0.0), (0, 0, 1), 20, BRASS, chamfer=0.002))
    out += pictograms()
    # numerals I..V and the switch collars
    for s in range(5):
        out.append(C.N.roman_obj(f"rn{s + 1}", s + 1, 0.06, 0.003, BRASS, loc=(0.0, 0.0, 0.0)))
        out[-1].data.transform(Matrix.Translation((-0.85, ROW_Y[s], FACE)))
        out.append(D.ring("sc", 0.012, 0.030, FACE, FACE + 0.010, (SW_X, ROW_Y[s], 0.0), (0, 0, 1), 16, BRASS, chamfer=0.002))
    # the main lever's guide: two arc rails at x = 0.80 / 0.88, radius 0.34 about the pivot, 0 .. 70 deg toward +Z, and a base boss
    py, pz = LEVER_P[1], LEVER_P[2]
    pts_o = [(pz + 0.34 * math.sin(math.radians(a)), py + 0.34 * math.cos(math.radians(a))) for a in range(0, 76, 5)]
    pts_i = [(pz + 0.30 * math.sin(math.radians(a)), py + 0.30 * math.cos(math.radians(a))) for a in range(75, -1, -5)]
    prof = pts_o + pts_i
    for (xa, xb) in ((0.79, 0.80), (0.88, 0.89)):
        out.append(B.prism_x("guide", prof, xa, xb, BRASS))
    out.append(K.gbox("lbase", (0.78, 0.50, FACE), (0.90, 0.70, 0.24), BRASS, 0.004))
    return out


def chalk_part():
    out = []
    sign = C.S.inlay("sign", "sign", 0.13, depth=0.002, mat=CHALK, loc=(-0.80, 0.29, FACE))
    out.append(sign)
    for k, ch in enumerate("1998"):
        d = C.N.digit_obj(f"d{k}", int(ch), 0.07, 0.002, CHALK, res=1)
        d.data.transform(Matrix.Translation((-0.705 + 0.052 * k, 0.29, FACE)))
        out.append(d)
    for k in range(4):                                                    # four tally strokes: "this time, all four"
        out.append(K.gbox("tally", (-0.46 + 0.022 * k, 0.255, FACE), (-0.456 + 0.022 * k, 0.335, FACE + 0.002), CHALK, 0.0))
    return M.join(out, "leyla_chalk")


def lamp(line, x):
    j = B.jewel(f"lamp_{line}", (x, LAMP_Y, FACE), 0.035, (0, 0, 1), GDARK, h=0.022, seg=14)
    return K.part(f"lamp_{line}", [j], pivot=(x, LAMP_Y, FACE))


def switch(s):
    y = ROW_Y[s - 1]
    p = (SW_X, y, FACE)
    parts = [K.gcyl("col", 0.017, 0.0, 0.020, base=p, axis=(0, 0, 1), segments=10, mat=BRASS, chamfer=0.003),
             D.rod("stem", (p[0], p[1], p[2] + 0.015), (p[0], p[1], p[2] + 0.075), 0.008, segs=8, mat=BRASS),
             M.sphere("tip", 0.014, loc=(p[0], p[1], p[2] + 0.08), segments=10, rings=6, mat=BRASS)]
    return K.part(f"IA_switch_{s}", parts, pivot=p)


def main_lever():
    px, py, pz = LEVER_P
    parts = [K.gcyl("hub", 0.026, -0.045, 0.045, base=(px, py, pz), axis=(1, 0, 0), segments=12, mat=BRASS, chamfer=0.004),
             K.gbox("blade", (px - 0.014, py, pz - 0.006), (px + 0.014, py + 0.36, pz + 0.006), BRASS, 0.003),
             M.sphere("ball", 0.032, loc=(px, py + 0.40, pz), segments=12, rings=8, mat=BRASS),
             K.gbox("tail", (px - 0.010, py - 0.09, pz - 0.005), (px + 0.010, py, pz + 0.005), BRASS, 0.002)]
    return K.part("IA_main_lever", parts, pivot=LEVER_P)


def trace(s, li):
    x, y = LINE_X[li], ROW_Y[s - 1]
    o = K.gcyl(f"trace_{s}_{LINES[li]}", 0.024, 0.0, 0.004, base=(x, y, FACE), axis=(0, 0, 1), segments=12, mat=BRASS, chamfer=0.001)
    return K.part(f"trace_{s}_{LINES[li]}", [o], pivot=(x, y, FACE))


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("panel_body", body_parts())
    brass = C.merge("panel_brass", brass_parts())
    chalk = chalk_part()
    lamps = [lamp(l, x) for l, x in zip(LINES, LINE_X)]
    switches = [switch(s) for s in range(1, 6)]
    lever = main_lever()
    traces = [trace(s, li) for s in range(1, 6) for li in range(4)]
    K.empty("echo_mount_tech_panel", (0.8, 0.0, 1.0), rot_deg=(0.0, 180.0, 0.0))
    K.empty("panel_light", (0.0, 2.4, 0.6))
    K.to_blender()
    C.finalize()
    return dict(body=body, brass=brass, chalk=chalk, lamps=lamps, switches=switches, lever=lever, traces=traces)


def verify(path):
    req = (["panel_body", "panel_brass", "leyla_chalk", "IA_main_lever", "panel_light", "echo_mount_tech_panel"] + [f"lamp_{l}" for l in LINES]
           + [f"IA_switch_{s}" for s in range(1, 6)] + [f"trace_{s}_{l}" for s in range(1, 6) for l in LINES])
    expect = {"IA_main_lever": LEVER_P, "IA_switch_1": (SW_X, ROW_Y[0], FACE), "IA_switch_5": (SW_X, ROW_Y[4], FACE),
              "lamp_vent": (LINE_X[3], LAMP_Y, FACE), "trace_3_array": (LINE_X[2], ROW_Y[2], FACE), "echo_mount_tech_panel": (0.8, 0.0, 1.0)}
    ident = [n for n in req if n != "echo_mount_tech_panel"]
    errs = C.verify(path, required=req, identity=ident, expect=expect, rot_expect={"echo_mount_tech_panel": (0, 180, 0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ("panel_body", "panel_brass", "leyla_chalk"):
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
PANEL = [1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0]       # array_hall_logic.gd canonical v_panel


def qa(args, parts):
    C.qa_begin()
    C.qa_floor_nonormal("bridge_deck")
    C.qa_hall(shell=True, extra=[("bridge", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0)])
    C.qa_floor_nonormal("qa_sh_hall_floor")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))
    roots = [parts["body"], parts["brass"], parts["chalk"], parts["lever"]] + parts["lamps"] + parts["switches"] + parts["traces"]
    for o in bpy.data.objects:
        if o.name.startswith(("echo_mount_tech_panel", "panel_light")):
            roots.append(o)
    K.qa_place(roots, (0.0, 0.0, 14.0), 180.0, name="qa_place_panel0")
    # the canonical state: traces where v_panel = 1; switches I and II up (on), the others down; all four lines live
    for s in range(1, 6):
        for li, l in enumerate(LINES):
            if PANEL[(s - 1) * 4 + li] == 0:
                bpy.data.objects[f"trace_{s}_{l}"].hide_render = True
    for s in range(1, 6):
        K.pose_rot(parts["switches"][s - 1], "x", -40.0 if s in (1, 2) else 40.0)
    for l in parts["lamps"]:
        K.override(l, K.glow("qa_lamp", "FFC27A", 7.0))
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, shaft=False, core=False, work=False)
        K.light("panel_lamp", "POINT", (0.0, 2.0, 12.6), 500.0, "FFC27A", radius=0.1)
        K.light("panel_lamp2", "POINT", (0.0, 1.0, 12.5), 300.0, "FFD9A0", radius=0.1)
    if C.want(args, "1"):          # the panel0 view
        cam, tgt, fov = C.view("panel0")
        lit(cam, 40.0, 0.12)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the matrix: switches, buses, junction dots and the chalk (power still off: lever up)
        cam, tgt, fov = (-0.1, 1.15, 12.95), (-0.1, 1.0, 13.78), 40
        lit(cam, 50.0, 0.12)
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
