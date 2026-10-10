"""handwheel.glb — one of the four brass handwheels on the bridge's north rail (Chapter 4, group B; instances at
wheel_mount_1..4). A steel pedestal (base plate, column, head block) carries a fixed dial plate (Ø 0.68, eight tick marks,
the numerals 1-8, a pointer tab at 12 o'clock) and the brass wheel in front of it.
Contract: docs/models/ch4.md section 4 handwheel; results: docs/models/ch4_b.md.

Origin = deck level at the footprint centre, front (+Z) toward the player. Local coordinates:
  handwheel_base  M_Steel_Painted  base plate (0.46 x 0.46) with four bolts, a tapered column (z -0.05, to y 1.08), the head
                  block, the dial plate (centre (0, 1.30), z 0.11 - 0.135, r 0.34) with 8 ticks at r 0.315 - 0.335, the
                  numerals 1-8 (0.045 high, upright, at r 0.295, clockwise from 12 o'clock) and the pointer tab; the shaft boss
  IA_handwheel    M_Brass_Aged     rim (major 0.245, tube r 0.02), six spokes, hub, a turned handle pin on the rim at
                  12 o'clock; ORIGIN = the axis (0, 1.30, 0.20), axis +Z, identity = handle at 12 o'clock.
                  k stops (45 deg each) = -45 deg x k about local +Z (a positive delta turns it clockwise seen from the player)

    blender -b --factory-startup -P tools/blender/models/handwheel.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, D, PAINT, BRASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "handwheel"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3500, 2, 2
AXIS = (0.0, 1.30, 0.20)
DIAL_Z = 0.135
DIAL_R = 0.34
WHEEL_R = 0.245


def base_parts():
    out = [K.gbox("plate", (-0.23, 0.0, -0.23), (0.23, 0.03, 0.23), PAINT, 0.005)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            out.append(K.hexbolt("bolt", 0.02, (sx * 0.185, 0.03, sz * 0.185), normal=(0, 1, 0), mat=PAINT))
    prof = [(0.0, 0.03), (0.13, 0.03), (0.13, 0.07), (0.10, 0.13), (0.075, 0.30), (0.062, 1.0), (0.085, 1.07), (0.0, 1.07)]
    out.append(K.glathe("column", prof, base=(0.0, 0.0, -0.05), axis=(0, 1, 0), segments=14, mat=PAINT, smooth=60.0))
    out.append(K.gbox("head", (-0.11, 1.07, -0.15), (0.11, 1.42, 0.11), PAINT, 0.008))
    out.append(K.gcyl("dial", DIAL_R, 0.11, DIAL_Z, base=(0.0, AXIS[1], 0.0), axis=(0, 0, 1), segments=48, mat=PAINT, chamfer=0.004))
    out.append(K.gcyl("boss", 0.045, DIAL_Z, 0.19, base=(0.0, AXIS[1], 0.0), axis=(0, 0, 1), segments=14, mat=PAINT, chamfer=0.004))
    for k in range(8):
        a = math.radians(45.0 * k)                                  # clockwise from 12 o'clock
        dx, dy = math.sin(a), math.cos(a)
        r0, r1 = 0.315, 0.335
        tick = K.gbox("tick", (-0.0065, r0, DIAL_Z), (0.0065, r1, DIAL_Z + 0.006), PAINT, 0.0)
        tick.data.transform(Matrix.Translation((0.0, AXIS[1], 0.0)) @ Matrix.Rotation(-a, 4, "Z"))
        out.append(tick)
        num = C.N.digit_obj(f"n{k + 1}", k + 1, 0.045, 0.006, PAINT, res=1)
        num.data.transform(Matrix.Translation((0.285 * dx, AXIS[1] + 0.285 * dy, DIAL_Z)))
        out.append(num)
    # the fixed pointer tab above the rim, pointing down at the 12 o'clock stop
    tab = [(-0.022, 0.352), (0.022, 0.352), (0.0, 0.322)]
    t = K.plate("pointer", [tab], 0.008, z0=DIAL_Z, mat=PAINT, bevel=0.0, drop_bottom=True, loc=(0.0, AXIS[1], 0.0))
    out.append(t)
    return out


def wheel_parts():
    """Built around the axis at the origin; moved to AXIS by K.part's pivot."""
    ax, ay, az = AXIS
    out = []
    rim = M.torus("rim", WHEEL_R, 0.02, loc=(ax, ay, az), major_seg=40, minor_seg=8, mat=BRASS)
    out.append(rim)
    for k in range(6):
        a = math.radians(90.0 + 60.0 * k)
        p0 = (ax + 0.05 * math.cos(a), ay + 0.05 * math.sin(a), az)
        p1 = (ax + (WHEEL_R - 0.012) * math.cos(a), ay + (WHEEL_R - 0.012) * math.sin(a), az)
        out.append(D.rod("spoke", p0, p1, 0.013, segs=6, mat=BRASS))
    hub = K.glathe("hub", [(0.0, -0.035), (0.055, -0.035), (0.062, -0.015), (0.062, 0.03), (0.04, 0.05), (0.0, 0.055)],
                   base=(ax, ay, az), axis=(0, 0, 1), segments=14, mat=BRASS, smooth=60.0)
    out.append(hub)
    # the handle pin on the rim at 12 o'clock: a stem forward (+Z) with a ball end
    hx, hy = ax, ay + WHEEL_R
    out.append(D.rod("pin", (hx, hy, az + 0.01), (hx, hy, az + 0.085), 0.013, segs=8, mat=BRASS))
    out.append(M.sphere("ball", 0.026, loc=(hx, hy, az + 0.105), segments=12, rings=8, mat=BRASS))
    return out


def build():
    M.reset_scene()
    C.ensure_materials()
    base = C.merge("handwheel_base", base_parts())
    wheel = K.part("IA_handwheel", wheel_parts(), pivot=AXIS)
    K.to_blender()
    C.finalize()
    return dict(base=base, wheel=wheel)


def verify(path):
    req = ["handwheel_base", "IA_handwheel"]
    expect = {"IA_handwheel": AXIS}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi}")
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
    # four instances at wheel_mount_1..4 (the built one is number 1)
    X = (-3.6, -2.2, 2.2, 3.6)
    K.qa_place([parts["base"], parts["wheel"]], (X[0], C.DECK_Y, 12.45), 0.0, name="qa_place_hw1")
    for i in (1, 2, 3):
        C.qa_import("handwheel", (X[i], C.DECK_Y, 12.45), 0.0, prefix=f"qa_hw{i + 1}_")
    turns = {1: 0, 2: 2, 3: 5, 4: 7}                    # each wheel's own count, to show the dial / handle moving
    for o in bpy.data.objects:
        for i in (2, 3, 4):
            if o.name == f"qa_hw{i}_IA_handwheel":
                K.pose_rot(o, "z", -45.0 * turns[i])
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # the handwheels view
        cam, tgt, fov = C.view("handwheels")
        lit(cam, 70.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a closeup of wheels I (rest) and II (two stops)
        cam, tgt, fov = (-2.9, 4.0, 14.2), (-2.9, 3.8, 12.45), 44
        lit(cam, 90.0, 0.25)
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
