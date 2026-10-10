"""oscillograph.glb — Leyla's portable oscilloscope on the camp table (E4): it shows the waveform of the tuning
crystal that was tapped. Contract: docs/models/ch3.md §7 oscillograph (+ §2 recorder / shutter views, §11 E4
osc_wave.gdshader); results: docs/models/ch3_e.md.

On the camp table at (4.97, 0.74, -1.72), yaw 135 (the screen faces north-east, toward both the `shutter` and the
`recorder` cameras). Origin = the bottom centre; front +Z.

Size 0.20 w x 0.15 h x 0.20 d (z -0.05 .. 0.15), STEPPED: a front block 0.15 high (z 0.085 .. 0.15, the bezel and the screen)
and a low body 0.085 high behind it with rounded rear corners. The contract's 0.22 x 0.16 x 0.30 box, 0.27 m from the
recorder, would put its back corner on the recorder's overhanging keys and hide them from the `recorder` view, whose
camera (5.3, 1.32, -2.55) looks over the scope at the keys (ch3_e.md, deviations).

  oscillograph   (static) cream steel stepped case with vent louvres on the low body, a bakelite front bezel with the
                 screen window, four bakelite knobs and a folded bakelite side handle, rubber feet; the dark CRT
                 glass behind the window (M_Glass_Dark) and a pilot jewel
  osc_screen     the CRT face 0.10 x 0.08 at (0, 0.09, 0.151), UV 0..1 (u -> +X, v -> +Y), M_Shader_Quad

    blender -b --factory-startup -P tools/blender/models/oscillograph.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "oscillograph"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2000, 4, 4
CREAM, BAKE, GLASS_DARK, SHQ = E.CREAM_STEEL, E.BAKE, E.GLASS_DARK, E.SHQ

HALF_W = 0.10
Z0, Z1 = -0.05, 0.15                      # case back / front (the bezel face)
ZF0 = 0.085                               # the front block runs z 0.085 .. 0.15; the low body behind it
ZB1 = 0.09
H_FRONT, H_BODY = 0.15, 0.085
FEET = 0.012
BEZEL_T = 0.006
SCREEN = (0.0, 0.09, 0.151)
SCREEN_W, SCREEN_H = 0.10, 0.08
WIN_W, WIN_H = 0.12, 0.10
KNOBS = [(0.08, 0.035), (0.08, 0.065), (0.08, 0.095), (0.08, 0.125), (-0.08, 0.05)]
JEWEL = (-0.08, 0.125)


def case():
    cr, bk, gl = [], [], []
    # the low body (rounded rear corners) and the front block carrying the bezel
    cr.append(E.rrect_box("body", 2 * HALF_W, H_BODY - FEET, ZB1 - Z0, 0.04, (0.0, (FEET + H_BODY) / 2, (Z0 + ZB1) / 2), CREAM, n=4, bevel=0.002))
    cr.append(K.gbox("front", (-HALF_W, FEET, ZF0), (HALF_W, H_FRONT, Z1 - BEZEL_T), CREAM, 0.003))
    for k in range(5):
        z = -0.02 + 0.022 * k
        cr.append(K.gbox("louvre", (-0.06, H_BODY - 0.0005, z - 0.004), (0.06, H_BODY + 0.0015, z + 0.004), CREAM, 0.0))
    # feet
    for sx in (-1, 1):
        for z in (Z0 + 0.03, Z1 - 0.03):
            bk.append(K.gcyl("foot", 0.009, 0.0, FEET + 0.001, base=(sx * (HALF_W - 0.02), 0.0, z), axis=(0, 1, 0), segments=8,
                             mat=BAKE))
    # bezel plate with the window
    bk.append(K.plate("bezel", [L.rounded_rect(2 * HALF_W, H_FRONT - FEET, 0.008, 2), list(reversed(L.rounded_rect(WIN_W, WIN_H, 0.006, 2, cy=SCREEN[1] - (FEET + H_FRONT) / 2)))],
                      BEZEL_T, z0=Z1 - BEZEL_T, mat=BAKE, bevel=0.0008, loc=(0.0, (FEET + H_FRONT) / 2, 0.0)))
    # the CRT glass behind the window and the screen's dark surround
    gl.append(K.gbox("crt_glass", (-WIN_W / 2, SCREEN[1] - WIN_H / 2, Z1 - 0.004), (WIN_W / 2, SCREEN[1] + WIN_H / 2, Z1 + 0.0004), GLASS_DARK, 0.0))
    # knobs (bakelite, simple knurl), pointer lines on the bezel, a pilot jewel
    for (kx, ky) in KNOBS:
        kn = L.knurled_knob("knob", 0.009, 0.012, ridges=8, mat=BAKE, index_mark=False, simple=True)
        kn.data.transform(Matrix.Translation((kx, ky, Z1)))
        bk.append(kn)
        bk.append(K.gbox("ptr", (kx - 0.0008, ky + 0.004, Z1 + 0.012), (kx + 0.0008, ky + 0.008, Z1 + 0.0128), CREAM, 0.0))
    gl.append(B.jewel("pilot", (JEWEL[0], JEWEL[1], Z1), 0.0045, (0, 0, 1), GLASS_DARK, seg=10))
    bk.append(D.ring("pilot_ring", 0.0045, 0.0065, Z1, Z1 + 0.002, (JEWEL[0], JEWEL[1], 0.0), (0, 0, 1), 10, BAKE))
    # a folded carrying handle on the left side (x = -HALF_W)
    hy = 0.052
    bk.append(K.V.tube("handle", [(-HALF_W - 0.002, hy, 0.05), (-HALF_W - 0.016, hy, 0.05), (-HALF_W - 0.016, hy, -0.03),
                                  (-HALF_W - 0.002, hy, -0.03)], 0.005, sides=6, mat=BAKE, fillet=0.01))
    # a BNC-style input socket (cream) low on the bezel's left
    cr.append(K.gcyl("socket", 0.006, Z1, Z1 + 0.008, base=(-0.08, 0.022, 0.0), axis=(0, 0, 1), segments=10, mat=CREAM, caps=False))
    cr.append(K.gcyl("socket_pin", 0.0015, Z1, Z1 + 0.007, base=(-0.08, 0.022, 0.0), axis=(0, 0, 1), segments=5, mat=CREAM))
    return K.part(NAME, cr + bk + gl)


def build():
    M.reset_scene()
    E.ensure_materials()
    body = case()
    screen = D.quad01("osc_screen", SCREEN, SCREEN_W, SCREEN_H, SHQ)
    M.set_origin(screen, SCREEN)
    K.to_blender()
    E.finalize()
    D.restore_uv01(screen)
    return dict(body=body, screen=screen)


def case_height(xl, zl):
    """Top of the case (above the table) at scope-local (x, z), None outside its footprint."""
    if abs(xl) > HALF_W or zl < Z0 or zl > Z1:
        return None
    r = 0.04
    if zl < Z0 + r and abs(xl) > HALF_W - r:          # the rounded rear corners
        if math.hypot(abs(xl) - (HALF_W - r), zl - (Z0 + r)) > r:
            return None
    return H_FRONT if zl >= ZF0 else H_BODY + 0.0015


def verify(path):
    req = [NAME, "osc_screen"]
    errs = E.verify(path, required=req, identity=req, expect={NAME: (0, 0, 0), "osc_screen": SCREEN},
                    parents={n: None for n in req}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = E.bounds([NAME])
    print(f"{E.TAG} {NAME} bounds {lo} .. {hi}")
    o = bpy.data.objects["osc_screen"]
    uv = [tuple(round(c, 3) for c in d.uv) for d in o.data.uv_layers.active.data]
    print(f"{E.TAG} osc_screen UV {uv}")
    # the recorder view's sight lines to the recorder's keys must clear the case (ch3_e.md): world -> scope-local
    cam = Vector((5.3, 1.32, -2.55))
    th = math.radians(E.OSC_YAW)
    ax, az = Vector((math.cos(th), -math.sin(th))), Vector((math.sin(th), math.cos(th)))     # local +X / +Z in world (x, z)
    worst = 9.0
    for kx in (4.93, 4.98):
        keys = Vector((kx, 0.812, -1.575))
        for i in range(1, 200):
            p = cam.lerp(keys, i / 200)
            d = Vector((p.x - E.OSC_POS[0], p.z - E.OSC_POS[2]))
            xl, zl = d.dot(ax), d.dot(az)
            h = case_height(xl, zl)
            if h is not None:
                worst = min(worst, p.y - (E.OSC_POS[1] + h))
    print(f"{E.TAG} sight line to the recorder keys clears the case by {worst * 1000:.0f} mm (worst point; >= 10 needed)")
    if worst < 0.010:
        errs.append("the scope hides the recorder keys")
    return errs


# ====================================================================== QA
def qa(parts, args):
    E.qa_begin()
    roots = D.roots()
    D.place(roots, E.OSC_POS, E.OSC_YAW, name="qa_place_osc")
    E.camp_room(extra=[("leyla_camp", (0, 0, 0), 0.0, "qa_lc_"), ("field_recorder", E.RECORDER_POS, E.RECORDER_YAW, "qa_fr_"),
                       ("crystal_shutter", E.SHUTTER_POS, E.SHUTTER_YAW, "qa_cs_")])
    bulb = next((o for o in bpy.data.objects if o.name.startswith("qa_lc_camp_bulb")), None)
    if bulb is not None:
        K.override(bulb, K.glow("qa_bulb", "FFD9A8", 7.0))
    E.preview(parts["screen"], "osc_screen_s3.png", emissive=True, strength=1.6)
    W = lambda p: E.world_point(E.OSC_POS, E.OSC_YAW, p)   # noqa: E731
    # 1 the recorder view (§2): the scope in the foreground, the recorder behind
    if E.want(args, "1"):
        R = E.view("recorder")
        E.camp_lights(R[0], fill=6.0)
        E.shoot(NAME, R[0], R[1], R[2])
    # 2 hero: the screen straight on, close (the seed-0 size-3 waveform)
    if E.want(args, "2"):
        cam = W((0.12, 0.26, 0.55))
        E.camp_lights(cam, fill=6.0)
        E.shoot(NAME + "_2", cam, W((0.0, 0.085, 0.15)), 30)
    # 3 the shutter view (§2): the scope at the frame's left edge reads from there too
    if E.want(args, "3"):
        S = E.view("shutter")
        E.camp_lights(S[0], fill=5.0)
        E.shoot(NAME + "_3", S[0], S[1], S[2])


def main():
    args = M.main_guard()
    parts = build()
    E.report(NAME)
    path = E.export(NAME)
    errs = verify(path)
    print(f"{E.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
