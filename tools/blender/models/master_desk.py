"""master_desk.glb — the master desk on the operator's bridge (Chapter 4, group B): a green-grey painted console, 3.1 m wide,
with a sloped instrument panel carrying the chronometer (dial 03:10 - 03:17, jog wheel, the escapement bay with the EMPTY pawl
seat and its hinged cover) and the strip chart, two flat wings for the keeper unit (left) and the master lever (right).
Contract: docs/models/ch4.md section 4 master_desk; results: docs/models/ch4_b.md.

At (0, 2.5, 13.15), yaw 0. Origin = deck level, centre of the footprint; front (+Z) faces the operator (south). Body x +-1.55,
z -0.45 .. 0.46. Wings (x -1.55 .. -0.80 and 1.00 .. 1.55) are flat at y = 0.95. The console block (x -0.80 .. 1.00) has a slope from
the front edge (z 0.46, y 0.95) to (z -0.20, y 1.47) = 38.2 deg, up-normal n = (0, 0.7855, 0.6189), up-slope u = (0, 0.6189, -0.7855),
then a flat back shelf at y 1.47 (z -0.45 .. -0.20). Slope point P(s, x) = (x, 0.95 + 0.6189 s, 0.46 - 0.7855 s), s 0 .. 0.84.
  master_desk     M_Steel_Painted + M_Brass_Aged + M_Bakelite (3 surfaces): cabinet, the dial face / ticks / numerals / 03:1 legend,
                  the dial bezel, the bay frame, the chart frame with its minute numerals 0-7, the chart drum on the back shelf (static),
                  the jog wheel's brackets
  chrono_hand     M_Brass_Aged  ORIGIN = the dial centre P(0.5, 0) + 0.016 n = (0, 1.2675, 0.0543); built lying in the slope with its tip at
                  12 o'clock (up the slope). Turn it about n: position p (0..7) = (140 - 40 p) deg counter-clockwise seen from the front
                  of the dial (0 lower left ... 7 lower right)
  IA_scrub        M_Brass_Aged  knurled jog wheel r 0.12 x 0.10, ORIGIN (0, 1.07, 0.49), axis +X; position p = -45 p about +X
  IA_chronometer  M_Brass_Aged  the movement in the escapement bay (centre P(0.30, -0.62) = (-0.62, 1.1357, 0.2243)): escape wheel, train,
                  bridge, and the empty pawl seat. Origin = the bay centre. Use `reverse_pawl` on it
  chrono_plate    M_Brass_Aged  the bay's hinged cover, ORIGIN = its hinge on the bay's upper edge (-0.62, 1.1976, 0.1458), baked OPEN (-100 deg
                  from flat); the code closes it with +100 deg about +X after the pawl is fitted
  chart_paper     M_Shader_Quad 0.40 x 0.46 at P(0.475, 0.66) = (0.66, 1.244, 0.087) + 0.003 n; UV 0..1 (u across, minutes 0..7 left -> right;
                  v up the slope = time)
  empties         pawl_mount (the seat, rotated +38.2 deg about X), keeper_mount (-1.12, 0.95, 0), lever_mount (1.28, 0.95, 0),
                  echo_mount_strand (1.12, 0, 0.78) yaw 180, desk_light (0, 1.9, 0.5)

    blender -b --factory-startup -P tools/blender/models/master_desk.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, B, D, PAINT, BRASS, BAKE, SHQ  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "master_desk"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 12000, 8, 4
ZF, ZB = 0.46, -0.45
ZS1, YS1 = -0.20, 1.47
BETA = math.atan2(YS1 - 0.95, ZF - ZS1)
NV = Vector((0.0, math.cos(BETA), math.sin(BETA)))            # up-normal of the slope
UV_ = Vector((0.0, math.sin(BETA), -math.cos(BETA)))          # up-slope
DIAL_S = 0.5
BAY_X, BAY_S = -0.62, 0.30
CHART_X, CHART_S = 0.66, 0.45


def P(s, x=0.0, off=0.0):
    """A point on the slope (s along it from the front edge, x across), `off` along the normal."""
    return Vector((x, 0.95 + math.sin(BETA) * s, ZF - math.cos(BETA) * s)) + NV * off


def on_slope(o, s, x=0.0, off=0.0):
    """Move a mesh built facing +Z (local XY = the slope plane, +Y up the slope) onto the slope at P(s, x)."""
    return D.place_xz(o, tuple(P(s, x, off)), tuple(NV))


def flat_loops(o_loops):
    return o_loops


# ====================================================================== static body (3 materials)
def paint_parts():
    out = [K.gbox("kick", (-1.50, 0.0, -0.40), (1.50, 0.12, 0.41), PAINT, 0.006),
           K.gbox("block", (-1.55, 0.12, ZB), (1.55, 0.95, ZF), PAINT, 0.01)]
    out.append(B.prism_x("console", [(ZF, 0.95), (ZS1, YS1), (ZB, YS1), (ZB, 0.95)], -0.80, 1.00, PAINT))
    for (x0, x1) in ((-1.45, -0.90), (-0.72, 0.92), (1.08, 1.45)):          # raised panels on the front
        out.append(K.gbox("fp", (x0, 0.22, ZF), (x1, 0.86, ZF + 0.012), PAINT, 0.004))
    for sx in (-1, 1):                                                       # raised panels on the ends
        a, b = sorted((sx * 1.55, sx * 1.562))
        out.append(K.gbox("ep", (a, 0.22, -0.34), (b, 0.86, 0.34), PAINT, 0.004))
    for sx in (-1, 1):                                                       # cheeks of the back shelf
        a, b = sorted((sx * 0.80, sx * 0.80 + sx * 0.0))
    out.append(K.gbox("shelf_back", (-0.80, YS1, ZB), (1.00, YS1 + 0.07, ZB + 0.03), PAINT, 0.004))
    for i in range(8):                                                       # rivets along the front panel
        out.append(K.rivet("rv", 0.012, (-1.40 + i * 0.4, 0.90, ZF + 0.012), normal=(0, 0, 1), mat=PAINT, segs=6))
    return out


def brass_parts():
    out = []
    # brass nosing along the front top edge (wings + the slope's lower lip) and the wings' ends
    out.append(K.gcyl("nosing", 0.012, -1.55, 1.55, base=(0.0, 0.955, ZF - 0.002), axis=(1, 0, 0), segments=8, mat=BRASS))
    out.append(K.gbox("kickstrip", (-1.50, 0.12, ZF - 0.01), (1.50, 0.135, ZF + 0.008), BRASS, 0.002))
    # ---- the dial: bezel, ticks, numerals, the 03:1 legend, the pivot cap
    bez = D.ring("dbez", 0.288, 0.322, 0.0, 0.020, (0, 0, 0), (0, 0, 1), 48, BRASS, chamfer=0.003)
    out.append(on_slope(bez, DIAL_S))
    for p in range(8):
        a = math.radians(-140.0 + 40.0 * p)                                  # clockwise from 12 o'clock
        t = K.gbox("tk", (-0.0075, 0.225, 0.004), (0.0075, 0.275, 0.009), BRASS, 0.0)
        t.data.transform(Matrix.Rotation(-a, 4, "Z"))
        out.append(on_slope(t, DIAL_S))
        d = C.N.digit_obj(f"dn{p}", p, 0.055, 0.005, BRASS, res=1)
        d.data.transform(Matrix.Translation((0.185 * math.sin(a), 0.185 * math.cos(a), 0.004)))
        out.append(on_slope(d, DIAL_S))
        for q in (1, 2):                                                     # two minor ticks between stations
            if p == 7:
                continue
            b = math.radians(-140.0 + 40.0 * p + 13.33 * q)
            mt = K.gbox("mt", (-0.003, 0.255, 0.004), (0.003, 0.275, 0.0075), BRASS, 0.0)
            mt.data.transform(Matrix.Rotation(-b, 4, "Z"))
            out.append(on_slope(mt, DIAL_S))
    for k, (ch, x) in enumerate((("0", -0.085), ("3", -0.045), (":", -0.012), ("1", 0.022))):
        if ch == ":":
            for y in (-0.082, -0.108):
                out.append(on_slope(K.gbox("colon", (x - 0.004, y - 0.004, 0.004), (x + 0.004, y + 0.004, 0.009), BRASS, 0.0), DIAL_S))
        else:
            d = C.N.digit_obj(f"lg{k}", int(ch), 0.048, 0.005, BRASS, res=1)
            d.data.transform(Matrix.Translation((x, -0.095, 0.004)))
            out.append(on_slope(d, DIAL_S))
    out.append(on_slope(K.gcyl("cap", 0.026, 0.004, 0.028, base=(0, 0, 0), axis=(0, 0, 1), segments=14, mat=BRASS, chamfer=0.003), DIAL_S))
    # ---- the escapement bay's frame
    outer = L.rounded_rect(0.320, 0.240, 0.012, 3)
    inner = list(reversed(L.rounded_rect(0.272, 0.192, 0.006, 3)))
    fr = K.plate("bayframe", [outer, inner], 0.016, z0=0.0, mat=BRASS, bevel=0.002, drop_bottom=True)
    out.append(on_slope(fr, BAY_S, BAY_X))
    for sx in (-1, 1):
        for sy in (-1, 1):
            sc = K.rivet("bsc", 0.008, (sx * 0.145, sy * 0.105, 0.016), normal=(0, 0, 1), mat=BRASS, segs=8)
            out.append(on_slope(sc, BAY_S, BAY_X))
    # ---- the strip chart: frame and the minute numerals 0..7 in the lower border
    outer = L.rounded_rect(0.46, 0.56, 0.010, 3)
    inner = list(reversed(L.rounded_rect(0.40, 0.46, 0.004, 2, 0.0, 0.025)))
    outer = [(x, y + 0.0) for (x, y) in outer]
    cf = K.plate("chartframe", [outer, inner], 0.014, z0=0.0, mat=BRASS, bevel=0.002, drop_bottom=True)
    out.append(on_slope(cf, CHART_S, CHART_X))
    for i in range(8):                                                       # minute i's column centre (0.40 wide paper, 8 columns of 0.05)
        x = -0.20 + 0.05 * (i + 0.5)
        d = C.N.digit_obj(f"cn{i}", i, 0.028, 0.004, BRASS, res=1)
        d.data.transform(Matrix.Translation((x, -0.243, 0.0)))
        out.append(on_slope(d, CHART_S, CHART_X, off=0.010))
    # the paper's roll drum on the back shelf (static): drum, flanges, two brackets
    out.append(K.gcyl("drum", 0.075, -0.22, 0.22, base=(CHART_X, YS1 + 0.09, -0.33), axis=(1, 0, 0), segments=20, mat=BRASS, chamfer=0.004))
    for sx in (-1, 1):
        out.append(K.gcyl("flange", 0.092, 0.0, 0.012, base=(CHART_X + sx * 0.22, YS1 + 0.09, -0.33), axis=(sx, 0, 0), segments=20, mat=BRASS))
        out.append(K.gbox("brk", (CHART_X + sx * 0.235 - 0.012, YS1, -0.36), (CHART_X + sx * 0.235 + 0.012, YS1 + 0.12, -0.30), BRASS, 0.003))
    # the jog wheel's two bracket cheeks at the front lip
    for sx in (-1, 1):
        out.append(K.gbox("jb", (sx * 0.085 - 0.012, 0.95, 0.43), (sx * 0.085 + 0.012, 1.07, 0.55), BRASS, 0.004))
    return out


def bake_parts():
    out = []
    face = K.gcyl("face", 0.288, 0.0, 0.004, base=(0, 0, 0), axis=(0, 0, 1), segments=48, mat=BAKE, chamfer=0.0)
    out.append(on_slope(face, DIAL_S))
    rec = K.gbox("recess", (-0.136, -0.096, 0.0), (0.136, 0.096, 0.004), BAKE, 0.0)
    out.append(on_slope(rec, BAY_S, BAY_X))
    return out


# ====================================================================== moving parts
def chrono_hand():
    outline = L.pointer_outline(0.245, 0.06, shaft_w=0.014, head_w=0.045, head_len=0.06, ball_r=0.024)
    hand = L.curve_solid("hand", [outline], 0.006, bevel=0.0008, bevel_res=0, mat=BRASS, drop_bottom=True)
    hub = K.gcyl("hub", 0.022, 0.0, 0.012, base=(0, 0, 0), axis=(0, 0, 1), segments=14, mat=BRASS, chamfer=0.002)
    for o in (hand, hub):
        on_slope(o, DIAL_S, 0.0, 0.016)
    return K.part("chrono_hand", [hand, hub], pivot=tuple(P(DIAL_S, 0.0, 0.016)))


def scrub():
    cy, cz = 1.07, 0.49
    prof = [(0.0, 0.0), (0.105, 0.0), (0.12, 0.012, "k"), (0.12, 0.088, "k"), (0.105, 0.10), (0.0, 0.10)]
    w = K.glathe("wheel", prof, base=(-0.05, cy, cz), axis=(1, 0, 0), segments=36, mat=BRASS, smooth=60.0, knurl=0.003)
    caps = [K.gcyl("axle", 0.016, -0.085, 0.085, base=(0.0, cy, cz), axis=(1, 0, 0), segments=10, mat=BRASS, chamfer=0.002)]
    for sx in (-1, 1):
        caps.append(K.gcyl("capb", 0.032, 0.0, 0.012, base=(sx * 0.05, cy, cz), axis=(sx, 0, 0), segments=12, mat=BRASS, chamfer=0.002))
    return K.part("IA_scrub", [w] + caps, pivot=(0.0, cy, cz))


def chronometer():
    parts = []
    plate = K.plate("mplate", [L.rounded_rect(0.264, 0.184, 0.008, 3)], 0.004, z0=0.0, mat=BRASS, bevel=0.0008, drop_bottom=True)
    parts.append(on_slope(plate, BAY_S, BAY_X, 0.004))

    def gear(nm, n, r0, r1, thick, loc, off, phase=0.0, holes=5):
        g = L.make_gear(nm, n, r0, r1, thick, phase=phase, holes=holes, mat=BRASS, bevel=0.0005)
        g.data.transform(Matrix.Translation((loc[0], loc[1], 0.0)))
        return on_slope(g, BAY_S, BAY_X, off)

    parts.append(gear("g1", 22, 0.036, 0.044, 0.006, (-0.055, 0.005), 0.010))
    parts.append(gear("g2", 12, 0.020, 0.026, 0.006, (-0.010, 0.050), 0.014, 0.1, 0))
    parts.append(gear("g3", 16, 0.027, 0.033, 0.005, (-0.075, -0.050), 0.018, 0.3, 4))
    for (x, y, h) in ((-0.055, 0.005, 0.030), (-0.010, 0.050, 0.030), (-0.075, -0.050, 0.030)):
        post = K.gcyl("post", 0.005, 0.008, h, base=(x, y, 0.0), axis=(0, 0, 1), segments=8, mat=BRASS)
        parts.append(on_slope(post, BAY_S, BAY_X))
    bridge = K.gbox("bridge", (-0.095, -0.006, 0.026), (0.020, 0.006, 0.034), BRASS, 0.002)
    parts.append(on_slope(bridge, BAY_S, BAY_X))
    # the empty pawl seat: a ring boss with a spring post
    seat = D.ring("seat", 0.012, 0.022, 0.004, 0.016, (0.075, -0.012, 0.0), (0, 0, 1), 16, BRASS, chamfer=0.002)
    parts.append(on_slope(seat, BAY_S, BAY_X))
    sp = K.gcyl("spring", 0.006, 0.004, 0.020, base=(0.10, 0.035, 0.0), axis=(0, 0, 1), segments=8, mat=BRASS)
    parts.append(on_slope(sp, BAY_S, BAY_X))
    return K.part("IA_chronometer", parts, pivot=tuple(P(BAY_S, BAY_X)))


def chrono_plate():
    hinge = P(BAY_S + 0.10, BAY_X)                                          # the upper edge of the bay
    plate = K.plate("cover", [L.rounded_rect(0.28, 0.200, 0.010, 3, 0.0, -0.100)], 0.012, z0=0.0, mat=BRASS, bevel=0.002, drop_bottom=True)
    knob = K.gcyl("knob", 0.014, 0.012, 0.034, base=(0.0, -0.18, 0.0), axis=(0, 0, 1), segments=10, mat=BRASS, chamfer=0.003)
    barrel = K.gcyl("barrel", 0.008, -0.12, 0.12, base=(0.0, 0.0, 0.004), axis=(1, 0, 0), segments=8, mat=BRASS)
    objs = [plate, knob, barrel]
    for o in objs:
        D.place_xz(o, tuple(hinge + NV * 0.002), tuple(NV))
    # bake the OPEN pose: -100 degrees about X through the hinge
    m = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-100.0), 4, "X") @ Matrix.Translation(-hinge)
    for o in objs:
        o.data.transform(m)
    return K.part("chrono_plate", objs, pivot=tuple(hinge))


def chart_paper():
    q = D.quad01("chart_paper", tuple(P(CHART_S + 0.025, CHART_X, 0.003)), 0.40, 0.46, SHQ, (1, 0, 0), tuple(UV_))
    return q


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("master_desk", paint_parts() + brass_parts() + bake_parts())
    hand = chrono_hand()
    wheel = scrub()
    chrono = chronometer()
    plate = chrono_plate()
    paper = chart_paper()
    seat = P(BAY_S - 0.01 / math.cos(0.0), BAY_X + 0.075, 0.016)
    K.empty("pawl_mount", tuple(seat), rot_deg=(math.degrees(BETA), 0.0, 0.0))
    K.empty("keeper_mount", (-1.12, 0.95, 0.0))
    K.empty("lever_mount", (1.28, 0.95, 0.0))
    K.empty("echo_mount_strand", (1.12, 0.0, 0.78), rot_deg=(0.0, 180.0, 0.0))
    K.empty("desk_light", (0.0, 1.9, 0.5))
    K.to_blender()
    C.finalize()
    D.restore_uv01(paper)
    return dict(body=body, hand=hand, wheel=wheel, chrono=chrono, plate=plate, paper=paper)


def verify(path):
    req = ["master_desk", "chrono_hand", "IA_scrub", "IA_chronometer", "chrono_plate", "chart_paper", "pawl_mount", "keeper_mount",
           "lever_mount", "echo_mount_strand", "desk_light"]
    expect = {"chrono_hand": tuple(P(DIAL_S, 0.0, 0.016)), "IA_scrub": (0.0, 1.07, 0.49), "IA_chronometer": tuple(P(BAY_S, BAY_X)),
              "chrono_plate": tuple(P(BAY_S + 0.10, BAY_X)), "keeper_mount": (-1.12, 0.95, 0.0), "lever_mount": (1.28, 0.95, 0.0),
              "echo_mount_strand": (1.12, 0.0, 0.78)}
    ident = [n for n in req if n not in ("pawl_mount", "echo_mount_strand")]
    errs = C.verify(path, required=req, identity=ident, expect=expect,
                    rot_expect={"pawl_mount": (math.degrees(BETA), 0, 0), "echo_mount_strand": (0, 180, 0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ("master_desk", "chrono_hand", "IA_scrub", "IA_chronometer", "chrono_plate", "chart_paper"):
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi}")
    ob = bpy.data.objects["chart_paper"]
    uvl = ob.data.uv_layers.active
    uv = sorted({tuple(round(c, 2) for c in uvl.data[li].uv) for p in ob.data.polygons for li in p.loop_indices})
    print(f"{C.TAG} chart_paper UVs {uv}")
    print(f"{C.TAG} slope angle {math.degrees(BETA):.2f} deg, n = {tuple(round(c, 4) for c in NV)}, pawl_mount {tuple(round(c, 4) for c in P(BAY_S - 0.01, BAY_X + 0.075, 0.016))}")
    return errs


# ====================================================================== QA
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
    roots = [parts[k] for k in ("body", "hand", "wheel", "chrono", "plate", "paper")]
    roots += [o for o in bpy.data.objects if o.name in ("pawl_mount", "keeper_mount", "lever_mount", "echo_mount_strand", "desk_light")]
    K.qa_place(roots, (0.0, 2.5, 13.15), 0.0, name="qa_place_desk")
    for nm, pos in (("master_lever", (1.28, 3.45, 13.15)), ("keeper_knob", (-1.12, 3.45, 13.15))):
        C.qa_import(nm, pos, 0.0, prefix=f"qa_{nm}_")
    for i, x in enumerate((-3.6, -2.2, 2.2, 3.6)):
        C.qa_import("handwheel", (x, 2.5, 12.45), 0.0, prefix=f"qa_hw{i + 1}_")
    img = os.path.join(C.PREVIEW_DIR, "chart_paper.png")
    if os.path.exists(img):
        K.override(parts["paper"], K.image_emitter("qa_chart", img, strength=0.55))
    C.rot_about(parts["hand"], tuple(NV), 140.0 - 40.0 * 4)               # 03:14
    K.pose_rot(parts["wheel"], "x", -45.0 * 4)
    osc = os.path.join(C.PREVIEW_DIR, "osc_screen.png")
    for o in bpy.data.objects:
        if o.name == "qa_keeper_knob_osc_screen" and os.path.exists(osc):
            K.override(o, K.image_emitter("qa_osc", osc, strength=1.6))
        if o.name == "qa_keeper_knob_IA_keeper":
            K.pose_rot(o, "z", 135.0 - 22.5 * 7)
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
        K.light("desk_lamp", "POINT", (0.0, 4.9, 13.9), 700.0, "FFD9A0", radius=0.1)
    if C.want(args, "1"):          # the desk view
        cam, tgt, fov = C.view("desk")
        lit(cam, 70.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the chronometer view: dial at 03:14, jog wheel, the open bay with the empty seat, the chart
        cam, tgt, fov = C.view("chronometer")
        lit(cam, 80.0, 0.22)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # the same with the pawl fitted: the cover closed
        K.pose_rot(parts["plate"], "x", 100.0)
        cam, tgt, fov = C.view("chronometer")
        lit(cam, 80.0, 0.22)
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
