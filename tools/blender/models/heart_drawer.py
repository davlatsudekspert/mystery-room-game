"""heart_drawer.glb — the brass drawer unit under the cradle, on the south face of the Core's pedestal (Chapter 4, group D).
Contract: docs/models/ch4.md section 6 heart_drawer; results: docs/models/ch4_d.md.

ISLAND FRAME: placed at (0, 2.5, 0); origin = the island centre on the platform top. The drawer face is at (0, 0.68, 0.70).
  heart_housing   M_Steel_Dark + M_Brass_Aged  the unit: a brass front frame (x +-0.35, y 0.43 .. 0.93, z 0.70 .. 0.745) round the opening, steel
                  side / top / bottom walls and runners going back into the pedestal (z 0.20 .. 0.70)
  IA_heart_drawer M_Brass_Aged  the drawer: a front panel (x +-0.30, y 0.51 .. 0.85) with a window frame and a pull bar, and a tray running
                  back to z = 0 (0.70 deep; its rear end stays inside the housing when open). ORIGIN = the drawer face centre
                  (0, 0.68, 0.70), identity at rest. OPEN = slides +0.55 along +Z (the code moves the node; its children come along)
    drawer_face     M_Glass_Frosted  CHILD of IA_heart_drawer: the frosted pane 0.40 x 0.20 in the window (z 0.700 .. 0.708), origin (0, 0.68, 0.704);
                    the projected mark falls here (cradle.glb `mark_mount` is on it at (0, 0.68, 0.705))
    IA_heart_watch / IA_heart_letter / IA_heart_pawl   M_Velvet  CHILDREN of IA_heart_drawer: three velvet pads in the tray (watch Ø 0.13 at
                    x = -0.185, letter 0.19 x 0.19 at x = 0, pawl 0.13 x 0.13 at x = +0.185; all at z = 0.36 closed (0.91 open), y top 0.545); origin =
                    the pad's top centre
    watch_mount / letter_mount / pawl_item_mount   empties, identity, CHILDREN of their pad, at the pad top centre (items lie flat, hero face +Y)

    blender -b --factory-startup -P tools/blender/models/heart_drawer.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL, FROST, VELVET  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "heart_drawer"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 4000, 7, 4
FACE = (0.0, 0.68, 0.70)
FACE_PANE = (0.0, 0.68, 0.704)
TRAY_TOP = 0.545                                  # the pad tops
PADS = {"IA_heart_watch": ("watch_mount", -0.185, 0.13, 0.13, True),
        "IA_heart_letter": ("letter_mount", 0.0, 0.19, 0.19, False),
        "IA_heart_pawl": ("pawl_item_mount", 0.185, 0.13, 0.13, False)}
PAD_Z = 0.36                                      # closed; open = 0.91: behind the front panel by 0.25 .. 0.43, so a high camera sees the pads


def housing_parts():
    out = []
    bm = bmesh.new()
    # front frame (brass): four bars round the opening x +-0.30, y 0.49 .. 0.87
    X.bm_box(bm, (-0.35, 0.43, 0.70), (0.35, 0.49, 0.745), bottom=True)                # bottom bar
    X.bm_box(bm, (-0.35, 0.87, 0.70), (0.35, 0.93, 0.745), bottom=True)                # top bar
    X.bm_box(bm, (-0.35, 0.49, 0.70), (-0.30, 0.87, 0.745), bottom=True)               # left bar
    X.bm_box(bm, (0.30, 0.49, 0.70), (0.35, 0.87, 0.745), bottom=True)                 # right bar
    # a raised bead round the frame
    X.bm_box(bm, (-0.335, 0.445, 0.745), (0.335, 0.455, 0.755), bottom=True)
    X.bm_box(bm, (-0.335, 0.905, 0.745), (0.335, 0.915, 0.755), bottom=True)
    X.bm_box(bm, (-0.335, 0.455, 0.745), (-0.325, 0.905, 0.755), bottom=True)
    X.bm_box(bm, (0.325, 0.455, 0.745), (0.335, 0.905, 0.755), bottom=True)
    for sx in (-1, 1):
        for y in (0.46, 0.90):
            X.bm_boss(bm, (sx * 0.325, y, 0.755), (0, 0, 1), 0.016, 0.008, sides=6)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    out.append(K.obj_from_bm("frame", bm, BRASS))
    # steel walls and runners behind the frame
    sb = bmesh.new()
    X.bm_box(sb, (-0.345, 0.49, 0.20), (-0.31, 0.87, 0.70), bottom=True)
    X.bm_box(sb, (0.31, 0.49, 0.20), (0.345, 0.87, 0.70), bottom=True)
    X.bm_box(sb, (-0.345, 0.43, 0.20), (0.345, 0.49, 0.70), bottom=True)
    X.bm_box(sb, (-0.345, 0.87, 0.20), (0.345, 0.93, 0.70), bottom=True)
    for sx in (-1, 1):                                                  # runners on the inside faces
        xa, xb = sorted((sx * 0.31, sx * 0.295))
        X.bm_box(sb, (xa, 0.545, 0.22), (xb, 0.575, 0.70), bottom=True)
    bmesh.ops.recalc_face_normals(sb, faces=list(sb.faces))
    out.append(K.obj_from_bm("walls", sb, STEEL))
    return out


def drawer_parts():
    bm = bmesh.new()
    zf, zb = 0.70, 0.665
    # front panel
    X.bm_box(bm, (-0.30, 0.51, zb), (0.30, 0.85, zf), bottom=True)
    # window frame (a raised rim round the pane, 0.40 x 0.20 at y 0.68)
    X.bm_box(bm, (-0.225, 0.58, zf), (0.225, 0.595, zf + 0.012), bottom=True)
    X.bm_box(bm, (-0.225, 0.765, zf), (0.225, 0.78, zf + 0.012), bottom=True)
    X.bm_box(bm, (-0.225, 0.595, zf), (-0.21, 0.765, zf + 0.012), bottom=True)
    X.bm_box(bm, (0.21, 0.595, zf), (0.225, 0.765, zf + 0.012), bottom=True)
    # pull bar on two posts, rivets in the corners
    X.bm_bar(bm, (-0.09, 0.545, zf + 0.040), (0.09, 0.545, zf + 0.040), 0.022, ref=(0, 1, 0))
    for sx in (-1, 1):
        X.bm_bar(bm, (sx * 0.075, 0.545, zf), (sx * 0.075, 0.545, zf + 0.040), 0.016, ref=(1, 0, 0))
    for sx in (-1, 1):
        for y in (0.535, 0.825):
            X.bm_boss(bm, (sx * 0.262, y, zf), (0, 0, 1), 0.015, 0.008, sides=6)
    # tray: floor, two side walls, a back wall (the tray runs to z = 0)
    X.bm_box(bm, (-0.265, 0.495, 0.0), (0.265, 0.520, zb), bottom=True)
    X.bm_box(bm, (-0.265, 0.520, 0.0), (-0.245, 0.62, zb), bottom=True)
    X.bm_box(bm, (0.245, 0.520, 0.0), (0.265, 0.62, zb), bottom=True)
    X.bm_box(bm, (-0.245, 0.520, 0.0), (0.245, 0.62, 0.02), bottom=True)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return [K.obj_from_bm("drawer", bm, BRASS)]


def build():
    M.reset_scene()
    C.ensure_materials()
    housing = C.merge("heart_housing", housing_parts())
    drawer = K.part("IA_heart_drawer", drawer_parts(), pivot=FACE)
    face = K.gbox("face_m", (-0.20, 0.58, 0.700), (0.20, 0.78, 0.708), FROST, 0.002)
    face = K.part("drawer_face", [face], pivot=FACE_PANE)
    pads = {}
    for name, (mount, x, w, d, rnd) in PADS.items():
        if rnd:
            m = K.gcyl("padm", w / 2.0, 0.520, TRAY_TOP, base=(x, 0.0, PAD_Z), axis=(0, 1, 0), segments=20, mat=VELVET, chamfer=0.006)
            # K.gcyl's base is the point on the axis: h is measured along +Y from base.y = 0 (so 0.520 .. 0.545 = absolute y)
        else:
            m = K.gbox("padm", (x - w / 2.0, 0.520, PAD_Z - d / 2.0), (x + w / 2.0, TRAY_TOP, PAD_Z + d / 2.0), VELVET, 0.006)
        pads[name] = K.part(name, [m], pivot=(x, TRAY_TOP, PAD_Z))
        K.empty(mount, (x, TRAY_TOP, PAD_Z))
    K.to_blender()
    K.parent(face, drawer)
    for name, (mount, x, w, d, rnd) in PADS.items():
        K.parent(pads[name], drawer)
        K.parent(bpy.data.objects[mount], pads[name])
    C.finalize()
    return dict(housing=housing, drawer=drawer, face=face, pads=pads)


def verify(path):
    req = ["heart_housing", "IA_heart_drawer", "drawer_face"] + list(PADS) + [v[0] for v in PADS.values()]
    ident = ["heart_housing", "IA_heart_drawer", "drawer_face"] + list(PADS)
    expect = {"heart_housing": (0.0, 0.0, 0.0), "IA_heart_drawer": FACE, "drawer_face": FACE_PANE}
    parents = {"drawer_face": "IA_heart_drawer"}
    for name, (mount, x, w, d, rnd) in PADS.items():
        expect[name] = (x, TRAY_TOP, PAD_Z)
        expect[mount] = (x, TRAY_TOP, PAD_Z)
        parents[name] = "IA_heart_drawer"
        parents[mount] = name
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents=parents, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ["heart_housing", "IA_heart_drawer", "drawer_face", "IA_heart_watch"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_reliquary(skip=(NAME,), sprites=True)
    X.qa_place_island([parts["housing"], parts["drawer"]])
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
    X.vis("qa_cage_", False)
    X.vis("qa_glass_tower_", False)
    if C.want(args, "1"):          # closed: the drawer face under the cradle
        cam, tgt, fov = (0.5, 3.75, 2.4), (0.0, 3.15, 0.7), 44
        lit(cam, 40.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # open (+0.55) with the letter on its pad
        K.pose_slide(parts["drawer"], (0.0, 0.0, 0.55))
        qb = K.V._qbox                                           # QA stand-in for the letter on its pad (the real size, 0.162 wide)
        qb("qa_letter", (-0.081, TRAY_TOP + 2.5, PAD_Z + 0.55 - 0.081), (0.081, TRAY_TOP + 2.504, PAD_Z + 0.55 + 0.081), "M_Paper")
        cam, tgt, fov = (0.5, 5.0, 2.7), (0.0, 3.1, 0.95), 46
        lit(cam, 40.0, 0.2)
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
