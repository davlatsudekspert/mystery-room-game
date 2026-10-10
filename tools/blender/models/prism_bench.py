"""prism_bench.glb — the Nursery's optical bench (E3): a cast-iron bench with a bakelite lamp house and two brass
prism turntables whose fans fall on the spectral seal 1.45 m north. Free-standing at (6.1, 0, 0.4), yaw 0: the front
(+Z) faces the player (south), the fans leave the back (-Z).
Contract: docs/models/ch3.md §6 prism_bench (+ §1.5 prism_lamp, §2 prisms, §11 E3); results: docs/models/ch3_d.md.

  prism_bench      (static) cast-iron top 1.30 x 0.60 (top y 0.86) with a front apron and an optical rail, two cast
                   trestle ends with arches on feet, a stretcher; brass: five tick marks behind each turntable (the
                   centre one longer), bezels round the four buttons, ◀ ▶ inlays beside them on the apron; bakelite:
                   the lamp house (cylinder Ø 0.17 with a domed cap, top 0.975) at the front centre (0, ·, 0.18) with
                   two slit tubes aimed at the prisms, a cord gland
  prism_lamp       (M_Crystal, code emission) the lamp's lens strip: a window band round the front of the lamp house
                   and the two slit lenses at the tube mouths (one mesh)
  IA_prism_p / _q  brass turntable Ø 0.18 (y 0.86 .. 0.90, knurled rim, a pointer at the back) with a brass pedestal
                   (y 0.90 .. 0.94) and a glass equilateral prism (side 0.06, y 0.94 .. 1.06) whose exit face looks
                   -Z; pivot (∓0.28, 0.88, -0.08); position v = -12° x v about local +Y (identity = v 0)
  IA_p_left / IA_p_right / IA_q_left / IA_q_right   bakelite nudge buttons (one material, the arrow embossed) at
                   (∓0.28 ∓ 0.06, 0.80, 0.30) on the apron; press = -0.004 along local Z; left = -1, right = +1
  fan_origin_p / _q   empties at (∓0.28, 1.00, -0.12), just outside each prism's exit face: the code's fan bands

    blender -b --factory-startup -P tools/blender/models/prism_bench.py [-- --no-render] [--shots=1,2,...]
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
from mathutils import Matrix, Vector  # noqa: E402

NAME = "prism_bench"
TRI_BUDGET, SURF_BUDGET = 5000, 12
STEEL, BRASS, CRYSTAL, BAKE = D.STEEL, D.BRASS, D.CRYSTAL, D.BAKE

TOP = 0.86
HALF_W, HALF_D = 0.65, 0.30
SLAB_T = 0.025
APRON_Y0 = 0.76
PIVOT = {"p": (-0.28, 0.88, -0.08), "q": (0.28, 0.88, -0.08)}
TT_R = 0.09                                    # turntable radius
PRISM_SIDE, PRISM_H = 0.06, 0.12
PED_Y0, PED_Y1 = 0.90, 0.94
FAN = {"p": (-0.28, 1.00, -0.12), "q": (0.28, 1.00, -0.12)}
BUTTONS = {"IA_p_left": (-0.34, 0.80, HALF_D), "IA_p_right": (-0.22, 0.80, HALF_D),
           "IA_q_left": (0.22, 0.80, HALF_D), "IA_q_right": (0.34, 0.80, HALF_D)}
LAMP_C = (0.0, TOP, 0.18)
LAMP_R, LAMP_TOP = 0.085, 0.975
SLIT_Y = 0.925
STEP_DEG = -12.0
PRESS = -0.004
# the logic's bands (underground_logic.gd) and the visuals' colours, for the QA fans only
P_BANDS, Q_BANDS = ("FF402E", "40FF59", "4D73FF"), ("4D73FF", "40FF59", "FF402E")
RECEPTORS = [(5.8, 1.15, -0.97), (6.1, 1.15, -0.97), (6.4, 1.15, -0.97)]


def tick_dir(v):
    """Direction from a pivot to tick v (the exit side, -Z at v = 0; +X for positive v, like the fan)."""
    a = math.radians(-STEP_DEG * v)
    return Vector((math.sin(a), 0.0, -math.cos(a)))


# ====================================================================== static bench
def bench():
    st, br, bk = [], [], []
    st.append(D.box("slab", (-HALF_W, TOP - SLAB_T, -HALF_D), (HALF_W, TOP, HALF_D), STEEL, 0.004))
    st.append(D.box("apron", (-HALF_W, APRON_Y0, HALF_D - 0.045), (HALF_W, TOP - SLAB_T, HALF_D), STEEL, 0.003))
    for (x0, x1) in ((-0.60, -0.40), (-0.16, 0.16), (0.40, 0.60)):          # the optical rail, round the turntables
        st.append(D.box("rail", (x0, TOP, -0.10), (x1, TOP + 0.012, -0.06), STEEL, 0.002))
    # trestle ends: a cast slab with an arch, a foot, a cap under the top; bolts; a stretcher between them
    for sx in (-1, 1):
        x = sx * 0.52
        end = K.plate("end", [L.rounded_rect(0.44, 0.73, 0.02, 2), L.rounded_rect(0.26, 0.40, 0.06, 3, cy=-0.09)], 0.04,
                      z0=0.0, mat=STEEL, bevel=0.002, drop_bottom=False)
        end.data.transform(Matrix.Translation((x - 0.02, 0.395, 0.0)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        st.append(end)
        st.append(D.box("foot", (x - 0.05, 0.0, -0.26), (x + 0.05, 0.03, 0.26), STEEL, 0.003))
        st.append(D.box("cap", (x - 0.045, 0.76, -0.24), (x + 0.045, TOP - SLAB_T, 0.24), STEEL, 0.002))
        for (y, z) in ((0.12, -0.16), (0.12, 0.16), (0.66, -0.16), (0.66, 0.16)):
            st.append(D.hexnut("eb", 0.008, (x + sx * 0.02, y, z), (sx, 0, 0)))
    st.append(D.box("stretch", (-0.50, 0.22, -0.03), (0.50, 0.27, 0.03), STEEL, 0.002))
    # brass ticks behind each turntable (v = -2 .. 2, the centre one longer) and the pointer's zero line
    for which, (px, py, pz) in PIVOT.items():
        for v in range(-2, 3):
            d = tick_dir(v)
            s = Vector((d.z, 0.0, -d.x)) * (0.0022 if v else 0.003)
            r0, r1 = TT_R + 0.010, TT_R + (0.045 if v == 0 else 0.028)
            c = Vector((px, 0.0, pz))
            a, b = c + d * r0, c + d * r1
            br.append(D.flat_poly_y("tick", [(a.x + s.x, a.z + s.z), (b.x + s.x, b.z + s.z), (b.x - s.x, b.z - s.z),
                                             (a.x - s.x, a.z - s.z)], TOP + 0.0007, BRASS))
    # button bezels (brass) and the ◀ ▶ inlays outside each pair, on the apron face
    for name, (bx, by, bz) in BUTTONS.items():
        br.append(D.ring("bbez", 0.0195, 0.0255, bz, bz + 0.003, (bx, by, 0.0), (0, 0, 1), 16, BRASS))
        sgn = -1 if name.endswith("_left") else 1
        ax = bx + sgn * 0.040
        tri = [(ax + sgn * 0.009, by), (ax - sgn * 0.006, by + 0.009), (ax - sgn * 0.006, by - 0.009)]
        arrow = L.flat_shape("arrow", [tri], mat=BRASS)
        arrow.data.transform(Matrix.Translation((0.0, 0.0, bz + 0.0007)))
        br.append(arrow)
    # lamp house: bakelite cylinder on a base flange with a domed cap, two slit tubes toward the prisms, a cord gland
    prof = [(0.0, 0.0), (0.097, 0.0), (0.097, 0.010), (LAMP_R, 0.016), (LAMP_R, 0.088), (0.080, 0.095), (0.060, 0.104),
            (0.032, 0.112), (0.0, LAMP_TOP - TOP)]
    bk.append(K.glathe("lamp_house", prof, LAMP_C, (0, 1, 0), 24, BAKE, smooth=45.0, phase=math.pi / 24))
    for which, (px, py, pz) in PIVOT.items():
        d = (Vector((px, 0.0, pz)) - Vector((LAMP_C[0], 0.0, LAMP_C[2]))).normalized()
        a = Vector((LAMP_C[0], SLIT_Y, LAMP_C[2])) + d * 0.070
        b = Vector((LAMP_C[0], SLIT_Y, LAMP_C[2])) + d * 0.135
        bk.append(D.rod("slit_tube", tuple(a), tuple(b), 0.017, 10, BAKE))
        bk.append(D.ring("slit_rim", 0.014, 0.019, 0.0, 0.004, tuple(b - d * 0.004), tuple(d), 10, BAKE))
    gl = Vector((LAMP_C[0], 0.90, LAMP_C[2] - LAMP_R + 0.005))
    bk.append(K.gcyl("gland", 0.012, 0.0, 0.035, base=tuple(gl), axis=(0, 0, -1), segments=8, mat=BAKE, chamfer=0.002))
    st.append(D.tube("cord", [(gl.x, gl.y, gl.z - 0.035), (gl.x, gl.y, gl.z - 0.07), (gl.x, TOP - 0.01, gl.z - 0.07)],
                     0.004, 6, STEEL, fillet=0.02))
    return K.part(NAME, st + br + bk)


def lamp_lenses():
    """prism_lamp: the window band round the front of the lamp house + the two slit lenses (one mesh, M_Crystal)."""
    parts = []
    band = K.ring_wall("lamp_band", LAMP_R + 0.0012, SLIT_Y - 0.011, SLIT_Y + 0.011, 95.0, 265.0, 18, CRYSTAL, inward=False)
    band.data.transform(Matrix.Translation((LAMP_C[0], 0.0, LAMP_C[2])))
    parts.append(band)
    for which, (px, py, pz) in PIVOT.items():
        d = (Vector((px, 0.0, pz)) - Vector((LAMP_C[0], 0.0, LAMP_C[2]))).normalized()
        c = Vector((LAMP_C[0], SLIT_Y, LAMP_C[2])) + d * 0.1335
        side = Vector((d.z, 0.0, -d.x))
        q = D.quad01("slit_lens", (0, 0, 0), 0.008, 0.026, CRYSTAL)
        q.data.transform(Matrix.Translation(c) @ Matrix((side, Vector((0, 1, 0)), d)).transposed().to_4x4())
        parts.append(q)
    return K.part("prism_lamp", parts, pivot=(LAMP_C[0], SLIT_Y, LAMP_C[2]))


# ====================================================================== turntables, buttons
def prism(which):
    px, py, pz = PIVOT[which]
    prof = [(0.0, 0.0), (0.086, 0.0), (TT_R, 0.004), (TT_R, 0.031, "k"), (TT_R, 0.036, "k"), (0.086, 0.040), (0.0, 0.040)]
    tt = K.glathe("turntable", prof, (px, TOP, pz), (0, 1, 0), 32, BRASS, knurl=0.0008, smooth=40.0)
    # pointer: a flat brass arrow on the top, at the back rim (the exit side), reads against the ticks
    pointer = D.flat_poly_y("pointer", [(px - 0.009, pz - 0.050), (px + 0.009, pz - 0.050), (px, pz - 0.086)],
                            TOP + 0.0407, BRASS)
    ped = K.gcyl("pedestal", 0.022, PED_Y0, PED_Y1, base=(px, 0.0, pz), axis=(0, 1, 0), segments=16, mat=BRASS,
                 chamfer=0.003)
    # the prism: equilateral, one face (the exit face) toward -Z, the vertex opposite it toward +Z
    R = PRISM_SIDE / math.sqrt(3.0)
    c30 = math.cos(math.radians(30))
    tri = [(0.0, -R), (-R * c30, R / 2), (R * c30, R / 2)]                      # (x, -z)
    pr = K.plate("prism", [tri], PRISM_H, z0=0.0, mat=CRYSTAL, bevel=0.0008, drop_bottom=False)
    pr.data.transform(Matrix.Translation((px, PED_Y1, pz)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    return K.part(f"IA_prism_{which}", [tt, pointer, ped, pr], pivot=PIVOT[which])


def button(name, pos):
    bx, by, bz = pos
    body = K.glathe("btn", [(0.0, -0.010), (0.018, -0.010), (0.018, 0.008), (0.0155, 0.0115), (0.0, 0.012)],
                    (bx, by, bz), (0, 0, 1), 16, BAKE, smooth=50.0)
    sgn = -1 if name.endswith("_left") else 1
    tri = [(sgn * 0.0075, 0.0), (-sgn * 0.0055, 0.008), (-sgn * 0.0055, -0.008)]
    arrow = K.plate("barrow", [tri], 0.0012, z0=bz + 0.012, mat=BAKE, bevel=0.0, loc=(bx, by, 0.0), drop_bottom=True)
    return K.part(name, [body, arrow], pivot=pos)


def build():
    M.reset_scene()
    D.ensure_materials()
    out = dict(body=bench(), lamp=lamp_lenses())
    out["prisms"] = {w: prism(w) for w in ("p", "q")}
    out["buttons"] = {n: button(n, p) for n, p in BUTTONS.items()}
    out["fans"] = {w: K.empty(f"fan_origin_{w}", FAN[w]) for w in ("p", "q")}
    K.to_blender()
    D.finalize()
    return out


def verify(path):
    req = [NAME, "prism_lamp", "IA_prism_p", "IA_prism_q", "fan_origin_p", "fan_origin_q"] + list(BUTTONS)
    expect = {NAME: (0, 0, 0), "IA_prism_p": PIVOT["p"], "IA_prism_q": PIVOT["q"], "fan_origin_p": FAN["p"],
              "fan_origin_q": FAN["q"]}
    expect.update(BUTTONS)
    errs = D.verify(path, required=req, identity=req, expect=expect, parents={n: None for n in req},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET)
    for n in [NAME, "prism_lamp", "IA_prism_p", "IA_prism_q"] + list(BUTTONS):
        lo, hi = D.bounds([n])
        print(f"{D.TAG} {n:12s} bounds {lo} .. {hi}")
    lo, hi = D.bounds([NAME])
    if hi[1] > 0.98:
        errs.append(f"bench top {hi[1]} > 0.98 (the lamp house must stay under the prisms view)")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, p=0, q=0, pressed=None):
    for w in ("p", "q"):
        parts["prisms"][w].matrix_basis = REST[w].copy()
    for n, o in parts["buttons"].items():
        o.matrix_basis = REST[n].copy()
    M.refresh()
    K.pose_rot(parts["prisms"]["p"], "y", STEP_DEG * p)
    K.pose_rot(parts["prisms"]["q"], "y", STEP_DEG * q)
    if pressed:
        K.pose_slide(parts["buttons"][pressed], (0.0, 0.0, PRESS))


def rec_point(idx):
    """The visuals' _receptor_point: receptor idx, or the door / wall beside it when out of range."""
    if 0 <= idx <= 2:
        x, y, z = RECEPTORS[idx]
        return (x, y, z + 0.004)
    return (6.1 + 0.3 * (idx - 1), 1.15, -0.97 - 0.06)


def fans(p, q, on=True):
    for o in [o for o in bpy.data.objects if o.name.startswith("qa_fan_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    if not on:
        return
    for w, v, bands in (("p", p, P_BANDS), ("q", q, Q_BANDS)):
        o = D.world_point(D.BENCH_POS, 0.0, FAN[w])
        for b in range(3):
            tx, ty, tz = rec_point(v + b)
            D.qa_beam(f"qa_fan_{w}{b}", o, (tx - 0.05, ty, tz), (tx + 0.05, ty, tz), bands[b], alpha=0.30, strength=4.0)


def qa(parts, args):
    D.qa_begin()
    for w in ("p", "q"):
        REST[w] = parts["prisms"][w].matrix_basis.copy()
    for n, o in parts["buttons"].items():
        REST[n] = o.matrix_basis.copy()
    roots = D.roots()
    D.place(roots, D.BENCH_POS, 0.0, name="qa_place_bench")
    D.room(extra=[("spectral_seal_door", D.SEAL_POS, 0.0, "qa_sd_")])
    K.override(parts["lamp"], K.glow("qa_prism_lamp", "FFF4DC", 5.0))
    recs = [next((o for o in bpy.data.objects if o.name.startswith(f"qa_sd_receptor_{i}") and o.type == "MESH"), None)
            for i in range(3)]
    start = [D.preview_material(f"qa_rec{i}", f"receptor_{i}.png", emissive=True, strength=1.6) for i in range(3)]
    solved = [D.preview_material(f"qa_rec{i}s", f"receptor_{i}_solved.png", emissive=True, strength=1.6) for i in range(3)]

    def rec_mats(mats):
        for r, m in zip(recs, mats):
            if r is not None and m is not None:
                K.override(r, m)

    W = lambda pt: D.world_point(D.BENCH_POS, 0.0, pt)   # noqa: E731
    PR_CAM, PR_TGT = (6.1, 1.75, 1.65), (6.1, 1.0, -0.55)
    # 1 the prisms view at the start (P = Q = +2): both fans on receptor 2 and the wall east of the door
    if K.want(args, "1"):
        pose(parts, 2, 2)
        fans(2, 2)
        rec_mats(start)
        D.lights(PR_CAM, fill=6.0, prism_lamp=True)
        D.shoot(NAME, PR_CAM, PR_TGT, 56)
    # 2 the prisms view solved (P 0, Q -1): yellow, yellow, blue on the receptors
    if K.want(args, "2"):
        pose(parts, 0, -1)
        fans(0, -1)
        rec_mats(solved)
        D.lights(PR_CAM, fill=6.0, prism_lamp=True)
        D.shoot(NAME + "_2", PR_CAM, PR_TGT, 56)
    # 3 hero: turntable P from the front-left above, at position +2 (pointer on tick +2), fans off
    if K.want(args, "3"):
        pose(parts, 2, 2)
        fans(2, 2, on=False)
        rec_mats(start)
        cam = W((-0.80, 1.30, 0.50))
        D.lights(cam, fill=8.0, prism_lamp=True)
        D.shoot(NAME + "_3", cam, W((-0.26, 0.96, -0.06)), 40)
    # 4 the P buttons on the apron, IA_p_left pressed
    if K.want(args, "4"):
        pose(parts, 2, 2, pressed="IA_p_left")
        cam = W((-0.28, 1.00, 0.92))
        D.lights(cam, fill=6.0, prism_lamp=True)
        D.shoot(NAME + "_4", cam, W((-0.28, 0.81, HALF_D)), 34)
    # 5 the lamp house from the front-right, low, the strip lit and the fans leaving the slits
    if K.want(args, "5"):
        pose(parts, 2, 2)
        fans(2, 2)
        cam = W((0.55, 1.08, 0.80))
        D.lights(cam, fill=6.0, prism_lamp=True)
        D.shoot(NAME + "_5", cam, W((0.0, 0.93, 0.12)), 40)
    # 6 the nursery root view
    if K.want(args, "6"):
        pose(parts, 2, 2)
        fans(2, 2)
        D.lights(prism_lamp=True)
        D.shoot(NAME + "_6", (5.7, 1.65, 3.3), (10.6, 1.3, -2.6), 62)


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
