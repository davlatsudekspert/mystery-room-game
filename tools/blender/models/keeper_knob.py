"""keeper_knob.glb — the keeper unit on the desk's left wing (Chapter 4, group B): a bench-instrument box with a large brass
knob on a numbered collar (0 off, 1-12) and, above it on a panel leaning back 25 deg, the oscillograph screen that draws the
beat. Contract: docs/models/ch4.md section 4 keeper_knob; results: docs/models/ch4_b.md.

At the desk's keeper_mount (-1.12, 2.5 + 0.95, 13.15), yaw 0. Origin = the box's base centre on the wing pad. Front (+Z) toward
the operator. Local coordinates:
  keeper_body   M_Steel_Painted + M_Brass_Aged (2 surfaces): the box 0.62 x 0.50 x 0.25, the raised collar plate (r 0.115 at
                (0, 0.125, 0.25)) with 13 brass ticks and the numerals 0, 3, 6, 9, 12, the leaning panel (centre (0, 0.404, -0.06),
                0.58 x 0.34, normal (0, 0.4226, 0.9063)), two side cheeks, the brass screen bezel
  osc_screen    M_Shader_Quad  round CRT face r 0.12 on the leaning panel, UV 0..1 over its bounding square (u -> +X, v up the
                panel); the shader draws the beat envelope
  IA_keeper     M_Brass_Aged   knurled knob r 0.07 x 0.058 with a pointer ridge. ORIGIN (0, 0.125, 0.256), axis +Z, identity =
                pointer at 12 o'clock. Position p (0..12) = (135 - 22.5 p) deg about local +Z (0 lower left, 12 lower right)

    blender -b --factory-startup -P tools/blender/models/keeper_knob.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, B, D, PAINT, BRASS, SHQ  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "keeper_knob"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 4500, 4, 3
KNOB_C = (0.0, 0.125, 0.256)
PLATE_C = (0.0, 0.125, 0.25)
TILT = 25.0
PANEL_C = Vector((0.0, 0.404, -0.06))
NORMAL = Vector((0.0, math.sin(math.radians(TILT)), math.cos(math.radians(TILT))))
UPV = Vector((0.0, math.cos(math.radians(TILT)), -math.sin(math.radians(TILT))))
LEAN = Matrix.Rotation(math.radians(-TILT), 4, "X")


def on_panel(o, off=0.0, local=(0.0, 0.0)):
    """Move a mesh built facing +Z (local XY = the panel plane) onto the leaning panel, `off` along its normal."""
    c = PANEL_C + NORMAL * off + Vector((local[0], 0.0, 0.0)) + UPV * local[1]
    o.data.transform(Matrix.Translation(c) @ LEAN)
    return o


def stat_parts():
    st, br = [], []
    st.append(K.gbox("box", (-0.31, 0.0, -0.25), (0.31, 0.25, 0.25), PAINT, 0.008))
    st.append(K.gbox("foot", (-0.33, 0.0, -0.27), (0.33, 0.02, 0.27), PAINT, 0.004))
    # the leaning panel and its cheeks
    slab = K.gbox("slab", (-0.29, -0.17, -0.015), (0.29, 0.17, 0.015), PAINT, 0.004)
    st.append(on_panel(slab))
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.29, sx * 0.31))
        st.append(B.prism_x("cheek", [(0.03, 0.25), (-0.14, 0.57), (-0.16, 0.25)], xa, xb, PAINT))
    # the raised collar plate on the front face
    st.append(K.gcyl("plate", 0.115, 0.25, 0.256, base=(0.0, 0.125, 0.0), axis=(0, 0, 1), segments=32, mat=PAINT, chamfer=0.002))
    for sx in (-1, 1):
        for sy in (0.04, 0.21):
            st.append(K.rivet("rv", 0.012, (sx * 0.27, sy, 0.25), normal=(0, 0, 1), mat=PAINT, segs=6))
    # brass: 13 ticks and the numerals 0 3 6 9 12 on the plate
    for p in range(13):
        a = math.radians(-135.0 + 22.5 * p)                      # clockwise from 12 o'clock
        long_ = (p % 3 == 0)
        r0, r1 = (0.094, 0.108) if long_ else (0.099, 0.108)
        t = K.gbox("tick", (-0.0035 if long_ else -0.0025, r0, 0.256), (0.0035 if long_ else 0.0025, r1, 0.2605), BRASS, 0.0)
        t.data.transform(Matrix.Translation((0.0, 0.125, 0.0)) @ Matrix.Rotation(-a, 4, "Z"))
        br.append(t)
        if long_:
            txt = str(p)
            for k, chh in enumerate(txt):
                d = C.N.digit_obj(f"n{p}_{k}", int(chh), 0.020, 0.0035, BRASS, res=1)
                off = (k - (len(txt) - 1) / 2.0) * 0.014
                cx = 0.082 * math.sin(a) + off
                cy = 0.125 + 0.082 * math.cos(a)
                d.data.transform(Matrix.Translation((cx, cy, 0.2565)))
                br.append(d)
    # screen bezel
    bez = D.ring("bezel", 0.122, 0.150, 0.0, 0.014, (0, 0, 0), (0, 0, 1), 32, BRASS, chamfer=0.003)
    br.append(on_panel(bez, 0.015))
    for k in range(4):
        a = math.radians(45.0 + 90.0 * k)
        s = K.rivet("bs", 0.007, (0.0, 0.0, 0.0), normal=(0, 0, 1), mat=BRASS, segs=8)
        s.data.transform(Matrix.Translation((0.139 * math.cos(a), 0.139 * math.sin(a), 0.0)))
        br.append(on_panel(s, 0.029))
    return st, br


def screen():
    o = D.disc_uv("osc_screen", 0.12, (0.0, 0.0, 0.0), SHQ, 32)
    return on_panel(o, 0.0165)


def knob():
    prof = [(0.0, 0.0), (0.070, 0.0), (0.070, 0.012, "k"), (0.064, 0.030, "k"), (0.058, 0.048), (0.040, 0.058), (0.0, 0.058)]
    k = K.glathe("knob", prof, base=KNOB_C, axis=(0, 0, 1), segments=32, mat=BRASS, smooth=60.0, knurl=0.0025)
    ridge = K.gbox("ridge", (-0.006, 0.012, 0.0), (0.006, 0.066, 0.064), BRASS, 0.002)
    ridge.data.transform(Matrix.Translation(KNOB_C))
    dot = K.gcyl("dot", 0.006, 0.0, 0.004, base=(KNOB_C[0], KNOB_C[1] + 0.05, KNOB_C[2] + 0.057), axis=(0, 0, 1), segments=8, mat=BRASS)
    return K.part("IA_keeper", [k, ridge, dot], pivot=KNOB_C)


def build():
    M.reset_scene()
    C.ensure_materials()
    st, br = stat_parts()
    body = C.merge("keeper_body", st + br)
    scr = screen()
    kn = knob()
    K.to_blender()
    C.finalize()
    return dict(body=body, screen=scr, knob=kn)


def verify(path):
    req = ["keeper_body", "osc_screen", "IA_keeper"]
    expect = {"IA_keeper": KNOB_C}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi}")
    ob = bpy.data.objects["osc_screen"]
    uvl = ob.data.uv_layers.active
    uv = sorted({tuple(round(c, 2) for c in uvl.data[li].uv) for p in ob.data.polygons for li in p.loop_indices})
    print(f"{C.TAG} osc_screen UV range u {min(u for u, v in uv)}..{max(u for u, v in uv)}, v {min(v for u, v in uv)}..{max(v for u, v in uv)}")
    return errs


# ====================================================================== QA
def qa_desk_wing():
    qb = K.V._qbox
    qb("qa_wing", (-1.55, 2.5 + 0.12, 12.69), (-0.80, 2.5 + 0.95, 13.61), "M_Steel_Painted")
    qb("qa_desk", (-0.80, 2.5 + 0.12, 12.69), (1.55, 2.5 + 0.95, 13.61), "M_Steel_Painted")


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
    qa_desk_wing()
    K.qa_place([parts["body"], parts["screen"], parts["knob"]], (-1.12, 2.5 + 0.95, 13.15), 0.0, name="qa_place_keeper")
    img = os.path.join(C.PREVIEW_DIR, "osc_screen.png")
    if os.path.exists(img):
        K.override(parts["screen"], K.image_emitter("qa_osc", img, strength=1.6))
    K.pose_rot(parts["knob"], "z", 135.0 - 22.5 * 7)           # the keeper at 7
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # from the operator: the knob and the screen
        cam, tgt, fov = (-1.12, 4.35, 14.7), (-1.12, 3.9, 13.1), 40
        lit(cam, 70.0, 0.22)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the knob close up from the front-left, off
        K.pose_rot(parts["knob"], "z", -(135.0 - 22.5 * 7) + 135.0)       # back to 0
        cam, tgt, fov = (-1.55, 3.95, 14.3), (-1.12, 3.58, 13.4), 34
        lit(cam, 70.0, 0.22)
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
