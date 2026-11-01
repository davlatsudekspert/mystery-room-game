"""film_can_1..4.glb — the four tin film cans of the Cold Store (lore cans on the carriage shelves and the cans of the
N4 aisle puzzle; docs/CHAPTER2_EXPANSION.md N4). Held items: origin at the centre of mass, the lid axis along Godot +Y.

  film_can_1  35 mm can, 0.30 dia x 0.066, rusty lid, canvas strap, label slot M_Decal_CanLabel_1 (numeral 35)
  film_can_2  16 mm can, 0.20 dia x 0.046, galvanised, tape wrap, label M_Decal_CanLabel_2 (16)
  film_can_3  8 mm can, 0.13 dia x 0.040, dented lid and a dent in the wall, label M_Decal_CanLabel_3 (8)
  film_can_4  tall 0.20 dia x 0.094 can with a wire handle and a paper tag, label M_Decal_CanLabel_4 (9)
Single object per can (lid label = its own material slot; the decal PNGs are numerals and bands only, language neutral).
    blender -b --factory-startup -P tools/blender/models/film_can.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part  # noqa: E402
from mathutils import Matrix  # noqa: E402

ARGS = M.main_guard()
BUDGET = 1800
# (radius, height, body material, lid material, label slot)
SPEC = {1: (0.150, 0.066, "M_Steel_Galv", "M_Iron_Rust", "M_Decal_CanLabel_1"),
        2: (0.100, 0.046, "M_Steel_Galv", "M_Steel_Galv", "M_Decal_CanLabel_2"),
        3: (0.065, 0.040, "M_Steel_Galv", "M_Steel_Galv", "M_Decal_CanLabel_3"),
        4: (0.100, 0.094, "M_Steel_Galv", "M_Iron_Rust", "M_Decal_CanLabel_4")}


def build(i):
    r, h, bm_, lm, lab = SPEC[i]
    y0 = -h / 2
    o = []
    # body: pressed tin with a rolled bottom bead and a seam ridge
    o.append(glathe("body", [(0.0, 0.0), (r - 0.006, 0.0), (r - 0.001, 0.003), (r, 0.007), (r, h * 0.52), (r - 0.002, h * 0.55),
                             (r, h * 0.58), (r, h - 0.012), (r - 0.002, h - 0.010), (0.0, h - 0.010)], (0, y0, 0), axis="y", segments=28,
                  mat=bm_, smooth=32))
    # lid: slightly bigger overlapping cap, raised label field
    o.append(glathe("lid", [(0.0, h - 0.012), (r + 0.003, h - 0.012), (r + 0.0045, h - 0.009), (r + 0.0045, h - 0.003), (r + 0.002, h),
                            (r - 0.012, h), (r - 0.016, h - 0.002), (0.0, h - 0.002)], (0, y0, 0), axis="y", segments=28, mat=lm, smooth=32))
    o.append(glathe("lid_bead", [(r - 0.020, h - 0.002), (r - 0.016, h + 0.0015), (r - 0.012, h + 0.0015), (r - 0.010, h - 0.002)],
                    (0, y0, 0), axis="y", segments=28, mat=lm, smooth=32))
    o.append(K.disc_decal("label", r - 0.024, (0, y0 + h + 0.0004, 0), "y", lab, segs=28))
    if i == 1:
        # canvas strap round the middle with a buckle
        o.append(glathe("strap", [(r + 0.0005, h * 0.30), (r + 0.004, h * 0.31), (r + 0.004, h * 0.62), (r + 0.0005, h * 0.63)], (0, y0, 0),
                        axis="y", segments=28, mat="M_Linen"))
        o.append(gbox("buckle", (r + 0.002, y0 + h * 0.34, -0.012), (r + 0.009, y0 + h * 0.60, 0.012), "M_Brass_Aged", bevel=0.0015))
    if i == 2:
        # adhesive tape band over the lid seam, torn tail
        o.append(glathe("tape", [(r + 0.0006, h - 0.030), (r + 0.003, h - 0.029), (r + 0.003, h - 0.004), (r + 0.0006, h - 0.0035)], (0, y0, 0),
                        axis="y", segments=28, mat="M_Tape"))
        o.append(gbox("tape_tail", (r - 0.002, y0 + h - 0.032, 0.0), (r + 0.016, y0 + h - 0.0308, 0.016), "M_Tape", bevel=0.0))
    if i == 3:
        pass
    if i == 4:
        # wire carry handle over the lid and a paper tag on a string
        pts = [(math.cos(a) * (r * 0.96), y0 + h * 0.70 + math.sin(a) * 0.0, math.sin(a) * (r * 0.96)) for a in [0.0]]
        o.append(X.pipe("handle", [(-r - 0.004, y0 + h * 0.62, 0.0), (-r - 0.016, y0 + h * 0.62 + 0.03, 0.0), (r + 0.016, y0 + h * 0.62 + 0.03, 0.0),
                                   (r + 0.004, y0 + h * 0.62, 0.0)], 0.0028, mat="M_Steel_Dark", sides=6, fillet=0.012, flange_ends=False))
        o.append(gbox("tag", (r + 0.004, y0 + h * 0.30, 0.020), (r + 0.007, y0 + h * 0.30 + 0.040, 0.062), "M_Paper", bevel=0.0006))
        o.append(gcyl("tag_string", 0.0012, 0.024, (r + 0.0035, y0 + h * 0.62, 0.012), axis="y", verts=4, mat="M_Linen", bevel=0.0))
    return o


def one(i):
    X.begin()
    objs = build(i)
    A.presmooth(objs)
    if i == 3:
        pass
    j = M.join(objs, f"film_can_{i}")
    if i == 3:
        # a dent: pull a few lid-side vertices down and the wall in on one side
        for v in j.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            d = math.hypot(x - 0.03, y + 0.02)
            if v.co.z > 0.0 and d < 0.035 and v.co.z > 0.012:
                v.co.z -= 0.0035 * (1 - d / 0.035)
            if x < -0.045 and abs(v.co.z) < 0.014:
                v.co.x += 0.004 * (1 - abs(v.co.z) / 0.014)
    # Blender mesh is built in Godot axes via G(); centre of mass = origin already (symmetric cylinder)
    X.C.finalize_all(wood_grain=False)
    total = X.C.report(f"film_can_{i}")
    path = X.C.export(f"film_can_{i}")
    errs = X.C.verify_glb(path, required=[f"film_can_{i}"], identity=[f"film_can_{i}"], budget=BUDGET, show=[f"film_can_{i}"])
    print(f"{X.TAG} film_can_{i}: tris={total} errors={len(errs)}")
    return errs


def main():
    for i in (1, 2, 3, 4):
        one(i)
    if X.want_render(ARGS):
        X.begin()
        for k in range(1, 5):
            X.decal(f"M_Decal_CanLabel_{k}", f"can_label_{k}.png")
        for n, i in enumerate((1, 2, 3, 4)):
            X.C.qa_import(X.C.model_glb(f"film_can_{i}"), (-0.36 + 0.24 * n + (0.04 if n else 0), 0.05, 0.0), 0)
        K.retex()
        K.fix_pbr()
        X.C.qa_begin(samples=24)
        fl = X.studio_floor()
        for tag, cam, tgt, vf in (("", (0.0, 0.55, 0.85), (0.0, 0.03, 0.0), 32),):
            X.C.shoot(f"cold_film_cans{tag}", cam, tgt, vfov=vf, res=(900, 520), samples=24, world=0.5, lights=X.STUDIO)


def _decal_img(name):
    if name.startswith("M_Decal_CanLabel_"):
        p = os.path.join(X.DECALS, f"can_label_{name[-1]}.png")
        return p if os.path.exists(p) else None
    return None


main()
