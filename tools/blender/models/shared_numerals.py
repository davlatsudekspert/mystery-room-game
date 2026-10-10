"""shared_numerals.glb — the Chapter 4 numeral kit (group A): the Roman numerals I II III IV V and the digits 0-9 exactly as
every Chapter 4 model draws them (lib_ch4_numerals.py). A reference / QA sheet, NOT drawn in the game: one material
(M_Brass_Aged), 15 objects, each 0.25 high and 0.01 deep, built centred on its own origin and facing +Z, laid out in two
rows (the node positions only arrange the sheet).

  num_I .. num_V     x = 0.50 + 0.55 k (k = 0..4), y = 0.40
  dig_0 .. dig_9     x = 0.20 + 0.40 k (k = 0..9), y = 0.00

    blender -b --factory-startup -P tools/blender/models/shared_numerals.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, BRASS  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "shared_numerals"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3000, 15, 1
ROMAN = ["I", "II", "III", "IV", "V"]


def build():
    M.reset_scene()
    C.ensure_materials()
    objs = []
    for k, r in enumerate(ROMAN):
        o = C.N.roman_obj(f"num_{r}", k + 1, 0.25, 0.01, BRASS)
        o.location = (0.50 + 0.55 * k, 0.40, 0.0)
        objs.append(o)
    for d in range(10):
        o = C.N.digit_obj(f"dig_{d}", d, 0.25, 0.01, BRASS)
        o.location = (0.20 + 0.40 * d, 0.0, 0.0)
        objs.append(o)
    C.smooth(objs, 40.0)
    K.to_blender()
    C.finalize()
    return objs


def verify(path):
    req = [f"num_{r}" for r in ROMAN] + [f"dig_{d}" for d in range(10)]
    expect = {"num_I": (0.5, 0.40, 0.0), "dig_9": (3.8, 0.0, 0.0)}
    return C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)


def qa(args):
    C.qa_begin()
    K.V._qbox("qa_back", (-0.3, -0.3, -0.05), (4.3, 0.75, -0.0005), "M_Steel_Dark")
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))
    K.clear_lights()
    K.light("key", "AREA", (1.0, 1.4, 3.0), 600.0, "FFE2C0", radius=1.0, target=(2.0, 0.2, 0.0))
    K.light("fill", "AREA", (3.6, 0.2, 3.0), 300.0, "CFE0FF", radius=1.0, target=(2.0, 0.2, 0.0))
    C.shoot(NAME, (2.0, 0.22, 3.3), (2.0, 0.22, 0.0), 48, samples=S, res=RES)


def main():
    args = M.main_guard()
    build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args)


main()
