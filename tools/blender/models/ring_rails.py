"""ring_rails.glb — the four circular steel tracks the Array rings turn on (Chapter 4, group C).
Contract: docs/models/ch4.md section 5 ring_rails; results: docs/models/ch4_c.md.

Built in WORLD coordinates, origin (0, 0, 0) = the hall axis at floor level. ONE mesh object `ring_rails` with two
surfaces:
  M_Steel_Dark   four tracks (band r +- 0.45, y 0 .. 0.12, chamfered edges) at r = 10.5 / 8.5 / 6.5 / 4.5, 32 cast
                 sleepers per track every 11.25 deg (they stand 0.11 out of the band on both sides) and a rail clip on
                 every sleeper's outer end
  M_Brass_Aged   a thin guide groove (inlay) at each radius and the Roman numerals I..IV (3D relief, 0.46 high, lying on
                 the floor, readable from the south) beside each track at mark 1 (west of the catwalk, x about -1.5)

    blender -b --factory-startup -P tools/blender/models/ring_rails.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, STEEL, BRASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "ring_rails"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 2, 2
RADII = C.RING_R
SEGS = (64, 48, 40, 32)                     # polygon segments per track
TRACK = [(-0.45, 0.0), (-0.45, 0.08), (-0.39, 0.12), (0.39, 0.12), (0.45, 0.08), (0.45, 0.0)]
SLEEPERS = 32
NUM_H = 0.46
NUM_X = -1.5


def steel_obj():
    bm = bmesh.new()
    for r_, n in zip(RADII, SEGS):
        prof = [(r_ + dr, y) for (dr, y) in TRACK]
        X.bm_revolve(bm, prof, n)
    X.fix_dir(bm, up=True)
    # sleepers (stubs stand out of the band) and rail clips
    for r_ in RADII:
        for k in range(SLEEPERS):
            a = 11.25 * k + 5.625
            X.bm_polar_box(bm, r_ - 0.56, r_ + 0.56, a, 0.24, 0.0, 0.07)
            X.bm_polar_box(bm, r_ + 0.40, r_ + 0.47, a, 0.07, 0.07, 0.14)
    return K.obj_from_bm("rails_steel", bm, STEEL)


def brass_obj():
    bm = bmesh.new()
    for r_, n in zip(RADII, SEGS):
        X.bm_revolve(bm, [(r_ - 0.03, 0.1215), (r_ + 0.03, 0.1215)], n)
    X.fix_dir(bm, up=True)
    return K.obj_from_bm("rails_groove", bm, BRASS)


def numerals():
    out = []
    for n, r_ in zip((1, 2, 3, 4), RADII):
        o = C.N.roman_obj(f"num_{n}", n, NUM_H, depth=0.022, mat=BRASS)
        # lie flat: local +Y -> -Z (north, "up" for a reader standing south), local +Z -> +Y
        o.data.transform(Matrix.Rotation(math.radians(-90.0), 4, "X"))
        rr = r_ + 0.86
        phi = 180.0 + math.degrees(math.asin(-NUM_X / rr))
        C.at_azimuth(o, phi, rr, 0.0)
        out.append(o)
    return out


def build():
    M.reset_scene()
    C.ensure_materials()
    st, br = steel_obj(), brass_obj()
    nums = numerals()
    rails = C.merge(NAME, [st, br] + nums)
    K.to_blender()
    C.finalize()
    return dict(rails=rails)


def verify(path):
    errs = C.verify(path, required=[NAME], identity=[NAME], expect={NAME: (0.0, 0.0, 0.0)}, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = C.bounds([NAME])
    print(f"{C.TAG} {NAME} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa_rings_proxy():
    """QA stand-ins for the rings if array_rings.glb is not built yet: dark flat rings."""
    if os.path.exists(K.V.model_glb("array_rings")):
        C.qa_import("array_rings", (0, 0, 0), 0.0, prefix="qa_ar_")
        return
    for r_ in RADII:
        bm = bmesh.new()
        X.bm_revolve(bm, [(r_ - 0.4, 0.12), (r_ - 0.4, 0.5), (r_ + 0.38, 0.5), (r_ + 0.38, 0.12)], 96)
        X.fix_dir(bm, up=True)
        o = K.obj_from_bm("qa_ring", bm, STEEL)
        o.data.transform(K.V.C)             # G-frame -> Blender axes (the scene is already converted)


def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0)])
    X.qa_core()
    qa_rings_proxy()
    S = int(os.environ.get("MR_S", "28"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # the bridge view: all four tracks from the south
        cam, tgt, fov = C.view("bridge")
        lit(cam, 70.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a low oblique on mark 1: sleepers, clips, the groove and the numerals I..IV
        cam, tgt, fov = (-3.4, 1.5, 11.2), (-1.3, 0.0, 7.4), 58
        lit(cam, 90.0, 0.3)
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
