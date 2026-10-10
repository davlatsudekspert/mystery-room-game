"""field_recorder.glb — Leyla's 1990s portable reel-to-reel on the camp table (E4): the recorder that plays the
four-note melody back. Contract: docs/models/ch3.md §7 field_recorder (+ §2 recorder view, §11 E4); results:
docs/models/ch3_e.md.

On the camp table at (4.95, 0.74, -1.45), yaw 180 (the front faces north into the camp). Origin = the bottom centre.
Body 0.28 w x 0.09 h x 0.22 d (z -0.11 .. 0.11); the two keys overhang the front by 0.022 (z up to 0.132).

  field_recorder   (static, M_Leather + M_Chrome) a leather-wrapped case (0 .. 0.062) with a key shelf and a notch for the
                   keys, the chrome deck block (to y 0.088) with the spindles, head block, capstan, tape guides, the
                   riser front with the VU window (leather face, chrome bezel and ticks), two chrome knobs and a folding
                   side handle
  reel_l, reel_r   (M_Tape) 5-inch pancake reels (R 0.0635; pack R 0.050; flanges with three kidney windows) on the
                   spindles at (-0.07 / +0.07, 0.095, -0.02); they spin about local +Y (code)
  IA_rec_rewind    (M_Bakelite) piano key, pivot (-0.03, 0.07, 0.10) at its back edge; press = -8 deg about local +X;
                   raised rewind pictogram
  IA_rec_play      (M_Bakelite) the same at (0.02, 0.07, 0.10) with the play pictogram
  rec_vu           (M_Chrome) the VU needle, pivot at its base (0.092, 0.066, 0.0775); rest = at the left stop (35 deg
                   counter-clockwise from vertical); the code swings it 0 .. -70 deg about local +Z while playing

    blender -b --factory-startup -P tools/blender/models/field_recorder.py [-- --no-render] [--shots=1,2,...]
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
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "field_recorder"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2500, 7, 4
LEATHER, CHROME, BAKE, TAPE = E.LEATHER, E.CHROME, E.BAKE, E.TAPE

HX, Z0, Z1 = 0.14, -0.11, 0.11
CASE_H = 0.062
DECK_Y = 0.088                                # top of the deck block (the contract's 0.09 height with the spindle heads)
RISER_Z = 0.075                               # the riser's front face
SPINDLES = {"l": (-0.07, 0.095, -0.02), "r": (0.07, 0.095, -0.02)}
KEY_PIVOT = {"rewind": (-0.03, 0.07, 0.10), "play": (0.02, 0.07, 0.10)}
KEY_W, KEY_LEN, KEY_T = 0.032, 0.032, 0.012
VU_PIVOT = (0.092, 0.066, 0.0775)
VU_LEN, VU_REST_DEG = 0.0185, 35.0
SHELF_NOTCH = (-0.056, 0.046)                 # x range of the lowered shelf under the keys


def circle(r, n=32, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ====================================================================== static body
def body():
    lea, chr_ = [], []
    # leather case: the main block behind the key shelf (z -0.11 .. 0.075) and the front shelf with the notch
    lea.append(K.gbox("case", (-HX, 0.0, Z0), (HX, CASE_H, RISER_Z), LEATHER, 0.004, 2))
    lea.append(K.gbox("shelf_l", (-HX, 0.0, RISER_Z - 0.002), (SHELF_NOTCH[0], CASE_H, Z1), LEATHER, 0.003, 1))
    lea.append(K.gbox("shelf_r", (SHELF_NOTCH[1], 0.0, RISER_Z - 0.002), (HX, CASE_H, Z1), LEATHER, 0.003, 1))
    lea.append(K.gbox("shelf_m", (SHELF_NOTCH[0] - 0.002, 0.0, RISER_Z - 0.002), (SHELF_NOTCH[1] + 0.002, 0.040, Z1), LEATHER, 0.002, 1))
    # chrome deck block with a bevelled top edge; riser front at z 0.075
    chr_.append(K.gbox("deck", (-HX + 0.003, CASE_H, Z0 + 0.003), (HX - 0.003, DECK_Y, RISER_Z), CHROME, 0.0025, 2))
    # spindles with platters and nuts
    for (sx, sy, sz) in SPINDLES.values():
        chr_.append(K.gcyl("platter", 0.021, DECK_Y, DECK_Y + 0.0045, base=(sx, 0.0, sz), axis=(0, 1, 0), segments=14, mat=CHROME))
        chr_.append(K.gcyl("spindle", 0.0034, DECK_Y + 0.004, 0.1045, base=(sx, 0.0, sz), axis=(0, 1, 0), segments=8, mat=CHROME))
        chr_.append(K.gcyl("nut", 0.0068, 0.1045, 0.1085, base=(sx, 0.0, sz), axis=(0, 1, 0), segments=6, mat=CHROME))
    # head block, capstan, pinch roller and tape guides on the tape path in front of the reels
    chr_.append(K.gbox("heads", (-0.03, DECK_Y, 0.034), (0.03, DECK_Y + 0.011, 0.052), CHROME, 0.002))
    chr_.append(K.gbox("head_slot", (-0.016, DECK_Y + 0.011, 0.038), (0.016, DECK_Y + 0.0125, 0.048), CHROME, 0.0))
    chr_.append(K.gcyl("capstan", 0.0026, DECK_Y, DECK_Y + 0.016, base=(0.045, 0.0, 0.040), axis=(0, 1, 0), segments=8, mat=CHROME))
    chr_.append(K.gcyl("pinch", 0.0085, DECK_Y, DECK_Y + 0.010, base=(0.066, 0.0, 0.043), axis=(0, 1, 0), segments=10, mat=CHROME))
    for gx, gz in ((-0.052, 0.036), (-0.040, 0.012), (0.052, 0.012)):
        chr_.append(K.gcyl("guide", 0.0030, DECK_Y, DECK_Y + 0.012, base=(gx, 0.0, gz), axis=(0, 1, 0), segments=6, mat=CHROME))
    # the VU window on the riser face: a chrome bezel round a leather face, ticks on a 35-degree arc each way
    vx, vy = VU_PIVOT[0], 0.0755
    chr_.append(K.plate("vu_bezel", [L.rounded_rect(0.056, 0.026, 0.004, 2), list(reversed(L.rounded_rect(0.046, 0.019, 0.003, 2)))], 0.0035,
                        z0=RISER_Z, mat=CHROME, bevel=0.0004, loc=(vx, vy, 0.0)))
    lea.append(K.gbox("vu_face", (vx - 0.023, vy - 0.0095, RISER_Z - 0.0005), (vx + 0.023, vy + 0.0095, RISER_Z + 0.0012), LEATHER, 0.0))
    for k in range(5):
        a = math.radians(-35 + k * 70 / 4)
        r0, r1 = VU_LEN + 0.0015, VU_LEN + 0.0045
        px, py = vx + (VU_PIVOT[1] - vy) * 0.0, VU_PIVOT[1]
        tx0, ty0 = vx + r0 * math.sin(a), py + r0 * math.cos(a)
        tx1, ty1 = vx + r1 * math.sin(a), py + r1 * math.cos(a)
        t = K.gbox("tick", (-0.0006, 0.0, 0.0), (0.0006, r1 - r0, 0.0006), CHROME, 0.0)
        t.data.transform(Matrix.Translation((tx0, ty0, RISER_Z + 0.0012)) @ Matrix.Rotation(-a, 4, "Z"))
        chr_.append(t)
    # two chrome knobs on the riser face
    for kx in (-0.118, -0.084):
        chr_.append(K.gcyl("knob", 0.0075, 0.0, 0.010, base=(kx, 0.0755, RISER_Z), axis=(0, 0, 1), segments=10, mat=CHROME, chamfer=0.0012))
        chr_.append(K.gbox("knob_ptr", (kx - 0.0006, 0.0755 + 0.0035, RISER_Z + 0.010), (kx + 0.0006, 0.0755 + 0.0072, RISER_Z + 0.0108), CHROME, 0.0))
    # a folding carrying handle on the right side
    chr_.append(K.V.tube("handle", [(HX - 0.002, 0.040, -0.045), (HX + 0.013, 0.040, -0.045), (HX + 0.013, 0.040, 0.030),
                                    (HX - 0.002, 0.040, 0.030)], 0.0045, sides=5, mat=CHROME, fillet=0.008))
    # two chrome latches on the front of the case
    for lx in (-0.105, 0.105):
        chr_.append(K.gbox("latch", (lx - 0.012, 0.012, Z1), (lx + 0.012, 0.034, Z1 + 0.0035), CHROME, 0.001))
        chr_.append(K.gcyl("latch_pin", 0.0035, 0.0, 0.0017, base=(lx, 0.023, Z1 + 0.0035), axis=(0, 0, 1), segments=8, mat=CHROME))
    if os.environ.get("MR_TRIS"):
        import collections
        cnt = collections.Counter()
        for o in lea + chr_:
            cnt[o.name.split(".")[0]] += sum(len(p.vertices) - 2 for p in o.data.polygons)
        print(f"{E.TAG} TRIS", cnt.most_common(14))
    return K.part(NAME, lea + chr_, pivot=(0.0, 0.0, 0.0))


# ====================================================================== reels
def reel(side):
    cx, cy, cz = SPINDLES[side]
    y_b0, y_b1, y_p1, y_t1 = -0.0020, -0.0008, 0.0062, 0.0074
    parts = []

    def flat(name, loops, y0, y1):
        o = K.plate(name, loops, y1 - y0, z0=0.0, mat=TAPE, bevel=0.0, drop_bottom=True)
        o.data.transform(Matrix.Translation((0.0, y0, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
        return o
    # bottom flange: a plain disc with the spindle hole; top flange: three kidney windows (faces up, bottom cap dropped)
    parts.append(flat("flange_b", [circle(0.0635, 24), list(reversed(circle(0.0042, 8)))], y_b0, y_b1))
    wins = []
    for k in range(3):
        ac = math.radians(30 + k * 120)
        wins.append(list(reversed(L.kidney(0.0300, 0.0555, ac - math.radians(36), ac + math.radians(36), n_arc=3))))
    parts.append(flat("flange_t", [circle(0.0635, 24), list(reversed(circle(0.0042, 8)))] + wins, y_p1, y_t1))
    # hub and the wound tape in one solid ring (the windows show the pack)
    pack = D.ring("pack", 0.0042, 0.0500, y_b1, y_p1, (0.0, 0.0, 0.0), (0, 1, 0), 18, TAPE, chamfer=0.0)
    parts.append(pack)
    o = K.part(f"reel_{side}", parts, pivot=(0.0, 0.0, 0.0))
    o.location = (cx, cy, cz)
    return o


# ====================================================================== keys and needle
def key(kind):
    glyph = "rewind" if kind == "rewind" else "play"
    return E.piano_key(f"IA_rec_{kind}", KEY_PIVOT[kind], KEY_W, KEY_LEN, KEY_T, BAKE, glyph=glyph, glyph_h=0.017, depth=0.0018, stretch=1.5)


def needle():
    # built at rest: from the base (origin) up and 35 degrees to the left (-X) in the XY plane, 0.0185 long, tapering
    a = math.radians(VU_REST_DEG)
    prof = [(-0.0007, 0.0), (0.0007, 0.0), (0.00035, VU_LEN), (-0.00035, VU_LEN)]
    n = K.plate("needle_bar", [prof], 0.0012, z0=0.0, mat=CHROME, bevel=0.0, drop_bottom=False)
    n.data.transform(Matrix.Rotation(a, 4, "Z"))
    hub = K.gcyl("needle_hub", 0.0028, 0.0, 0.0022, base=(0.0, 0.0, 0.0), axis=(0, 0, 1), segments=10, mat=CHROME, chamfer=0.0005)
    o = K.part("rec_vu", [n, hub], pivot=(0.0, 0.0, 0.0))
    o.location = VU_PIVOT
    return o


def build():
    M.reset_scene()
    E.ensure_materials()
    b = body()
    reels = {s: reel(s) for s in ("l", "r")}
    keys = {k: key(k) for k in ("rewind", "play")}
    vu = needle()
    K.to_blender()
    E.finalize()
    return dict(body=b, reels=reels, keys=keys, vu=vu)


def verify(path):
    req = [NAME, "reel_l", "reel_r", "IA_rec_rewind", "IA_rec_play", "rec_vu"]
    expect = {NAME: (0, 0, 0), "reel_l": SPINDLES["l"], "reel_r": SPINDLES["r"], "IA_rec_rewind": KEY_PIVOT["rewind"],
              "IA_rec_play": KEY_PIVOT["play"], "rec_vu": VU_PIVOT}
    errs = E.verify(path, required=req, identity=req, expect=expect, parents={n: None for n in req}, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = E.bounds([n])
        print(f"{E.TAG} {n:14s} bounds {tuple(round(c, 4) for c in lo)} .. {tuple(round(c, 4) for c in hi)}")
    return errs


# ====================================================================== QA
REST = {}


def qa(parts, args):
    E.qa_begin()
    for n, o in list(parts["keys"].items()) + [("vu", parts["vu"])]:
        REST[n] = o.matrix_basis.copy()
    roots = D.roots()
    D.place(roots, E.RECORDER_POS, E.RECORDER_YAW, name="qa_place_recorder")
    E.camp_room(extra=[("leyla_camp", (0, 0, 0), 0.0, "qa_lc_"), ("oscillograph", E.OSC_POS, E.OSC_YAW, "qa_os_"),
                       ("crystal_shutter", E.SHUTTER_POS, E.SHUTTER_YAW, "qa_cs_")])
    bulb = next((o for o in bpy.data.objects if o.name.startswith("qa_lc_camp_bulb")), None)
    if bulb is not None:
        K.override(bulb, K.glow("qa_bulb", "FFD9A8", 7.0))
    osc = next((o for o in bpy.data.objects if o.name.startswith("qa_os_osc_screen") and o.type == "MESH"), None)
    if osc is not None:
        E.preview(osc, "osc_screen.png", emissive=True, strength=1.5)
    W = lambda p: E.world_point(E.RECORDER_POS, E.RECORDER_YAW, p)   # noqa: E731
    # 1 the recorder view (§2)
    if E.want(args, "1"):
        R = E.view("recorder")
        E.camp_lights(R[0], fill=6.0)
        E.shoot(NAME, R[0], R[1], R[2])
    # 2 hero: from the front, high and close, the play key pressed and the needle at 40 %
    if E.want(args, "2"):
        K.pose_rot(parts["keys"]["play"], "x", -8.0)
        K.pose_rot(parts["vu"], "z", -40.0)
        cam = W((0.10, 0.30, 0.34))
        E.camp_lights(cam, fill=5.0)
        E.shoot(NAME + "_2", cam, W((0.0, 0.07, 0.01)), 36)
    # 3 the keys from above and in front, close (the pictograms)
    if E.want(args, "3"):
        cam = W((-0.005, 0.22, 0.20))
        E.camp_lights(cam, fill=3.0)
        K.shoot(NAME + "_3", cam, W((-0.005, 0.066, 0.118)), vfov=24)


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
