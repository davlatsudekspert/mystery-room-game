"""growth_chart.glb — Leyla's growth chart (E2): an enamel frame with a glass cover on the camp's east wall (outer
face) at (7.75, 0, -2.45), yaw 90 (front faces +X).
Contract: docs/models/ch3.md §6 growth_chart (+ §2 chart, §11 E2 growth_curve.gdshader, §12 growth_grid.png);
results: docs/models/ch3_d.md.

Origin = floor level at the centre of the back face, on the wall plane (wall-mounted, §0); the model front is +Z.

  chart_frame    (static, M_Steel_Cream) cream enamel steel frame 0.66 x 0.86 (y 1.17 .. 2.03): a back pan, the
                 side wall, a mitred lip with a 0.58 x 0.78 opening, four dome screws
  chart_glass    (M_Glass) the glass cover 0.60 x 0.80 x 0.004 at z 0.028 .. 0.032, behind the lip
  chart_image    0.60 x 0.80 quad centred (0, 1.60, 0.02), UV 0..1 (u -> +X, v -> +Y), M_Shader_Quad: the code's
                 growth_curve shader (growth_grid.png + v_curve); QA shows the seed-0 preview chart_image.png

    blender -b --factory-startup -P tools/blender/models/growth_chart.py [-- --no-render] [--shots=1,2,...]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402

NAME = "growth_chart"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 800, 3, 3
CREAM, GLASS, SHQ = D.CREAM, D.GLASS, D.SHQ

FRAME_W, FRAME_H = 0.66, 0.86
IMG_W, IMG_H = 0.60, 0.80
CY = 1.60                                  # frame / image centre height
IMAGE_C = (0.0, CY, 0.02)
GLASS_Z0, GLASS_Z1 = 0.028, 0.032
GLASS_C = (0.0, CY, (GLASS_Z0 + GLASS_Z1) / 2)
PAN_T = 0.018
LIP_Z0, LIP_Z1 = 0.036, 0.044
OPEN_W, OPEN_H = 0.58, 0.78


def frame():
    parts = [D.box("pan", (-FRAME_W / 2, CY - FRAME_H / 2, 0.0), (FRAME_W / 2, CY + FRAME_H / 2, PAN_T), CREAM, 0.002)]
    # side wall (the frame's return between the pan and the lip), open inside 0.62 x 0.82
    parts.append(K.plate("wall", [L.rounded_rect(FRAME_W, FRAME_H, 0.012, 3), L.rounded_rect(0.62, 0.82, 0.004, 1)],
                         LIP_Z0 - PAN_T, z0=PAN_T, mat=CREAM, bevel=0.0, loc=(0.0, CY, 0.0), drop_bottom=True))
    # the lip over the glass edge
    parts.append(K.plate("lip", [L.rounded_rect(FRAME_W, FRAME_H, 0.012, 3), L.rounded_rect(OPEN_W, OPEN_H, 0.006, 2)],
                         LIP_Z1 - LIP_Z0, z0=LIP_Z0, mat=CREAM, bevel=0.0015, loc=(0.0, CY, 0.0), drop_bottom=False))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(K.rivet("scr", 0.0055, (sx * (FRAME_W / 2 - 0.022), CY + sy * (FRAME_H / 2 - 0.022), LIP_Z1),
                                 segs=8, mat=CREAM))
    return K.part("chart_frame", parts)


def build():
    M.reset_scene()
    D.ensure_materials()
    fr = frame()
    gl = D.box("chart_glass", (-IMG_W / 2, CY - IMG_H / 2, GLASS_Z0), (IMG_W / 2, CY + IMG_H / 2, GLASS_Z1), GLASS, 0.0)
    M.set_origin(gl, GLASS_C)
    img = D.quad01("chart_image", IMAGE_C, IMG_W, IMG_H, SHQ)
    M.set_origin(img, IMAGE_C)
    K.to_blender()
    D.finalize()
    D.restore_uv01(img)
    return dict(frame=fr, glass=gl, image=img)


def verify(path):
    req = ["chart_frame", "chart_glass", "chart_image"]
    errs = D.verify(path, required=req, identity=req, expect={"chart_frame": (0, 0, 0), "chart_glass": GLASS_C,
                                                              "chart_image": IMAGE_C},
                    parents={n: None for n in req}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in req:
        lo, hi = D.bounds([n])
        print(f"{D.TAG} {n:12s} bounds {lo} .. {hi}")
    o = bpy.data.objects["chart_image"]
    uv = [tuple(round(c, 3) for c in d.uv) for d in o.data.uv_layers.active.data]
    print(f"{D.TAG} chart_image UV {uv}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    D.qa_begin()
    roots = D.roots()
    D.place(roots, D.CHART_POS, D.CHART_YAW, name="qa_place_chart")
    D.room()
    mat = D.preview_material("qa_chart", "chart_image.png", rough=0.75)
    if mat is not None:
        K.override(parts["image"], mat)
    W = lambda p: D.world_point(D.CHART_POS, D.CHART_YAW, p)   # noqa: E731
    # 1 the chart view (§2)
    if K.want(args, "1"):
        cam = (9.1, 1.6, -2.3)
        D.lights(cam, fill=6.0)
        D.shoot(NAME, cam, (7.8, 1.6, -2.45), 44)
    # 2 hero: three-quarter from the north-east, low (glass, lip, screws)
    if K.want(args, "2"):
        cam = W((0.55, 1.25, 0.95))
        D.lights(cam, fill=8.0)
        D.shoot(NAME + "_2", cam, W((0.0, 1.55, 0.03)), 40)
    # 3 the nursery_w root view (the camp's east wall in context)
    if K.want(args, "3"):
        D.lights()
        D.shoot(NAME + "_3", (12.2, 1.65, 2.9), (6.4, 1.2, -0.8), 62)


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
