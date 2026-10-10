"""growth_log.glb — Leyla's growth log: a clipboard hanging on the working autoclave's log_mount.
Contract: docs/models/ch3.md §6 growth_log (+ §11 E1 sketch, §12 growth_log.png); results: docs/models/ch3_d.md.

Origin = the hook point (the top of the hanging hole); the board hangs down local -Y, face +Z. The autoclave's
log_mount carries it with an identity transform.

  IA_growth_log   the board 0.23 x 0.32 x 0.006 (M_Wood_Panel) with the hanging hole; the tap target
  log_clip        the brass spring clip (child of the board)
  log_page        0.21 x 0.28 quad, UV 0..1, M_Decal_GrowthLog (localized; DecalLoc swaps _ru / _uz) (child)
  log_sketch      0.09 x 0.09 quad 0.5 mm above the page at page (u 0.50, v 0.36), UV 0..1, M_Shader_Quad: the
                  hex_glyph shader (style 1, pencil) draws v_sketch; alpha 0 outside the hexagon (child)

    blender -b --factory-startup -P tools/blender/models/growth_log.py [-- --no-render] [--shots=1,2,...]
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

NAME = "growth_log"
TRI_BUDGET, SURF_BUDGET = 800, 4
PANEL, BRASS, LOGDECAL, SHQ = D.PANEL, D.BRASS, D.LOGDECAL, D.SHQ

BOARD_W, BOARD_H, BOARD_T = 0.23, 0.32, 0.006
BOARD_TOP = 0.012                      # board top edge above the hook point
HOLE_Y, HOLE_R = -0.005, 0.005         # the hole's top edge is the hook point (y = 0)
PAGE_W, PAGE_H = 0.21, 0.28
PAGE_Y0 = -0.300                       # page bottom edge
PAGE_Z = BOARD_T / 2 + 0.0002
SKETCH = 0.09
SKETCH_C = (0.0, PAGE_Y0 + 0.36 * PAGE_H, PAGE_Z + 0.0005)
PAGE_C = (0.0, PAGE_Y0 + PAGE_H / 2, PAGE_Z)


def board():
    cy = BOARD_TOP - BOARD_H / 2
    loops = [L.rounded_rect(BOARD_W, BOARD_H, 0.012, 3), L.circle(HOLE_R, 12, cx=0.0, cy=HOLE_Y - cy)]
    o = K.plate("board", loops, BOARD_T, z0=-BOARD_T / 2, mat=PANEL, bevel=0.0012, loc=(0.0, cy, 0.0),
                drop_bottom=False)
    return K.part("IA_growth_log", [o], pivot=(0.0, 0.0, 0.0))


def clip():
    z = BOARD_T / 2
    parts = []
    # riveted base plate on the board, the rolled hinge, the spring jaw over the page top, the lever tab
    parts.append(K.plate("cbase", [L.rounded_rect(0.110, 0.020, 0.005, 4)], 0.0012, z0=z, mat=BRASS, bevel=0.0003,
                         loc=(0.0, -0.024, 0.0)))
    for x in (-0.042, 0.042):
        parts.append(K.rivet("crv", 0.0028, (x, -0.024, z + 0.0012), segs=6, mat=BRASS))
    parts.append(K.gcyl("chinge", 0.0035, -0.048, 0.048, base=(0.0, -0.036, z + 0.0035), axis=(1, 0, 0), segments=8,
                        mat=BRASS, chamfer=0.0008))
    jaw = K.plate("cjaw", [L.rounded_rect(0.076, 0.016, 0.005, 4)], 0.0010, z0=0.0, mat=BRASS, bevel=0.0003)
    jaw.data.transform(Matrix.Translation((0.0, -0.040, z + 0.0012)) @ Matrix.Rotation(math.radians(-6), 4, "X")
                       @ Matrix.Translation((0.0, -0.008, 0.0)))
    parts.append(jaw)
    lip = K.gcyl("clip_lip", 0.0016, -0.036, 0.036, base=(0.0, -0.0485, z + 0.0018), axis=(1, 0, 0), segments=6,
                 mat=BRASS)
    parts.append(lip)
    tab = K.plate("ctab", [L.rounded_rect(0.050, 0.020, 0.008, 4), L.circle(0.0045, 10, cy=0.002)], 0.0010, z0=0.0,
                  mat=BRASS, bevel=0.0003)
    tab.data.transform(Matrix.Translation((0.0, -0.036, z + 0.0055)) @ Matrix.Rotation(math.radians(38), 4, "X")
                       @ Matrix.Translation((0.0, 0.011, 0.0)))
    parts.append(tab)
    return K.part("log_clip", parts, pivot=(0.0, -0.036, z + 0.0035))


def build():
    M.reset_scene()
    D.ensure_materials()
    b = board()
    c = clip()
    page = D.quad01("log_page", PAGE_C, PAGE_W, PAGE_H, LOGDECAL)
    sk = D.quad01("log_sketch", SKETCH_C, SKETCH, SKETCH, SHQ)
    M.set_origin(page, PAGE_C)
    M.set_origin(sk, SKETCH_C)
    K.to_blender()
    D.finalize()
    for q in (page, sk):
        D.restore_uv01(q)
    for o in (c, page, sk):
        K.parent(o, b)
    return dict(board=b, clip=c, page=page, sketch=sk)


def verify(path):
    req = ["IA_growth_log", "log_page", "log_sketch", "log_clip"]
    expect = {"IA_growth_log": (0.0, 0.0, 0.0), "log_page": PAGE_C, "log_sketch": SKETCH_C}
    errs = D.verify(path, required=req, identity=req, expect=expect,
                    parents={"IA_growth_log": None, "log_page": "IA_growth_log", "log_sketch": "IA_growth_log",
                             "log_clip": "IA_growth_log"}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET)
    lo, hi = D.bounds(["IA_growth_log"])
    print(f"{D.TAG} board bounds {lo} .. {hi}")
    for n in ("log_page", "log_sketch"):
        o = bpy.data.objects[n]
        uv = [tuple(round(c, 3) for c in d.uv) for d in o.data.uv_layers.active.data]
        lo, hi = D.bounds([n])
        print(f"{D.TAG} {n}: UV {uv}, bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    D.qa_begin()
    sk_mat = D.preview_material("qa_log_sketch", "log_sketch.png", rough=0.8)
    if sk_mat is not None:
        K.override(parts["sketch"], sk_mat)
    # proxy: a chrome vessel side behind the board (model-local), the hook pin
    K.V._qbox("qa_back", (-0.6, -0.8, -0.12), (0.6, 0.5, -0.10), D.CHROME)
    pin = D.rod("qa_pin", (0.0, -0.0025, -0.10), (0.0, -0.0025, 0.012), 0.0025, 8, BRASS)
    K.to_blender([pin])

    def lt(cam):
        K.clear_lights()
        K.light("key", "SPOT", (0.6, 1.4, 1.2), 60.0, "DCEBFF", radius=0.2, target=(0.0, -0.15, 0.0), spot_deg=50)
        K.light("tube", "AREA", (-0.4, 1.2, 0.6), 25.0, "E8F2FF", radius=0.6, target=(0.0, -0.15, 0.0))
        K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 4.0, "FFE2C2", radius=0.2)
    # 1 hero: three-quarter
    if K.want(args, "1"):
        cam = (0.32, 0.02, 0.48)
        lt(cam)
        K.shoot(NAME, cam, (0.0, -0.15, 0.0), vfov=38)
    # 2 straight on (the growth_log view geometry: 0.55 m away, slightly above, FOV 38)
    if K.want(args, "2"):
        cam = (0.0, -0.10, 0.55)
        lt(cam)
        K.shoot(NAME + "_2", cam, (0.0, -0.152, 0.0), vfov=38)
    # 3 the clip and hole close-up
    if K.want(args, "3"):
        cam = (0.10, 0.05, 0.16)
        lt(cam)
        K.shoot(NAME + "_3", cam, (0.0, -0.03, 0.0), vfov=34)


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
