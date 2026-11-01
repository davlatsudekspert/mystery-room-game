"""manifold_plate.glb — the pressure manifold of the Pump Room (signature object of R2; puzzles N2 and N7).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3b/§7/§8. A riveted cast-iron wall plate 2.20 x 1.45 m carrying two
horizontal headers (supply below, return above), six vertical risers each with a globe valve and a spoked cast
handwheel, brass number plates 1-6 (numerals only, language neutral), two pressure gauges, a hazard lamp (the "H"
warning lamp of the pipe puzzle), a pressure lamp, an enamel diagram plaque (slot M_Decal_PipeDiagram, UV 0..1) and a big
red ram lever on the right (N7: the ram valve is on the same manifold).

Model space (Godot): front +Z, origin on the wall plane at floor level, x = 0 at the plate centre.
Placement suggestion: east wall of the Pump Room at (3.5, 0, 1.35), yaw -90.

Parts (own objects, origin at the pivot, identity rotation at rest):
  IA_valve_0..5       handwheels at x = -0.80 + 0.32 k, y = 1.12, z = 0.255. Turn about local +Z: open = -90 deg x steps
                      (clockwise seen from the front closes, as on real valves; the code decides the angle).
  IA_ram_lever        ram valve lever, pivot at (0.88, 0.98, 0.17); swings about local +Z (rest pointing down,
                      active = +70 deg, counter-clockwise seen from the front moves the tip toward +X)
  needle_a, needle_b  gauge needles at the gauge centres (-0.55, 1.62, 0.062) and (0.55, 1.62, 0.062); rest = 225 deg
                      from +X, value v of 12 = 225 - 22.5 v degrees, rotate about +Z
  hazard_lamp         red cage lamp lens (M_Emissive_Red), origin at its centre (-0.20, 1.62, 0.085)
  pressure_lamp       warm lamp lens (M_Emissive_Warm), origin at (0.20, 1.62, 0.085)
  diagram_plate       enamel plaque quad (M_Decal_PipeDiagram), centre (0.0, 1.62, 0.040)... see docs
  manifold_body       plate, headers, risers, valve bodies, brackets, number plates (static)

    blender -b --factory-startup -P tools/blender/models/manifold_plate.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, part  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "manifold_plate"
BUDGET = 13000
ARGS = M.main_guard()
PX, PY0, PY1 = 1.10, 0.45, 1.90
VX = [-0.80 + 0.32 * k for k in range(6)]
VY = 1.12
WZ = 0.255
HDR_LO, HDR_HI = 0.78, 1.46


def build():
    X.begin()
    body = []
    # backplate: two layers (plate + raised border) with rivets
    body.append(gbox("plate", (-PX, PY0, 0.0), (PX, PY1, 0.030), "M_Iron_Rust", bevel=0.006, seg=2))
    body.append(gbox("border", (-PX + 0.05, PY0 + 0.05, 0.030), (PX - 0.05, PY1 - 0.05, 0.036), "M_Iron_Rust", bevel=0.003))
    body.append(gbox("inset", (-PX + 0.07, PY0 + 0.07, 0.030), (PX - 0.07, PY1 - 0.07, 0.034), "M_Steel_Dark", bevel=0.002))
    rv = []
    for i in range(12):
        x = -PX + 0.035 + i * (2 * PX - 0.07) / 11
        rv += [(x, PY0 + 0.025, 0.030), (x, PY1 - 0.025, 0.030)]
    for j in range(1, 4):
        y = PY0 + 0.025 + j * (PY1 - PY0 - 0.05) / 4
        rv += [(-PX + 0.035, y, 0.030), (PX - 0.035, y, 0.030)]
    body.append(X.rivets("rv", rv, 0.0085, "z", segs=5))
    # wall lugs
    for sx in (-1, 1):
        body.append(gbox("lug", (sx * (PX + 0.04) - 0.04, PY0 + 0.1, 0.0), (sx * (PX + 0.04) + 0.04, PY1 - 0.1, 0.02),
                         "M_Steel_Dark", bevel=0.002))
    # headers (supply low, return high) on saddle brackets
    for nm, y, mat in (("hdr_lo", HDR_LO, "M_Copper"), ("hdr_hi", HDR_HI, "M_Steel_Painted")):
        body.append(X.pipe(nm, [(-1.02, y, 0.115), (1.02, y, 0.115)], 0.050, mat=mat, flange_r=0.075, flange_t=0.018,
                           bolts=8, flange_mat="M_Iron_Rust"))
        for x in (-0.92, -0.32, 0.32, 0.92):
            body.append(gbox("saddle", (x - 0.03, y - 0.06, 0.036), (x + 0.03, y + 0.06, 0.115), "M_Iron_Rust", bevel=0.003))
            body.append(gcyl("saddle_band", 0.058, 0.03, (x - 0.015, y, 0.115), axis="x", verts=12, mat="M_Steel_Dark",
                             bevel=0.0))
    # risers + valve bodies
    for k, x in enumerate(VX):
        body.append(X.pipe(f"riser{k}", [(x, HDR_LO, 0.115), (x, HDR_HI, 0.115)], 0.032, mat="M_Copper",
                           flange_ends=False))
        # valve: body sphere, bonnet cylinder toward +Z, packing nut, stem
        body.append(M.sphere(f"vb{k}", 0.058, loc=G(x, VY, 0.115), segments=12, rings=6, mat="M_Iron_Rust"))
        body.append(gcyl(f"bonnet{k}", 0.040, 0.085, (x, VY, 0.115), axis="z", verts=16, mat="M_Iron_Rust", bevel=0.003))
        body.append(gcyl(f"gland{k}", 0.026, 0.026, (x, VY, 0.195), axis="z", verts=12, mat="M_Brass_Aged", bevel=0.002))
        body.append(gcyl(f"stem{k}", 0.009, 0.060, (x, VY, 0.200), axis="z", verts=8, mat="M_Chrome", bevel=0.0))
        for s in (-1, 1):
            body.append(gcyl(f"vfl{k}{s}", 0.052, 0.014, (x, VY + s * 0.075, 0.115), axis="y" if s > 0 else "-y",
                             verts=14, mat="M_Iron_Rust", bevel=0.002))
        # number plate (brass) with the numeral below the valve
        body.append(gbox(f"np{k}", (x + 0.048, 0.915, 0.036), (x + 0.128, 0.995, 0.042), "M_Brass_Aged", bevel=0.001))
        body.append(C_text(f"n{k}", str(k + 1), 0.052, (x + 0.088, 0.955, 0.0425)))
    # ram valve body at the right end
    body.append(M.sphere("ram_body", 0.075, loc=G(0.88, 0.98, 0.14), segments=12, rings=6, mat="M_Iron_Rust"))
    body.append(gcyl("ram_neck", 0.045, 0.070, (0.88, 0.98, 0.14), axis="z", verts=14, mat="M_Iron_Rust", bevel=0.003))
    body.append(gcyl("ram_pivot", 0.022, 0.035, (0.88, 0.98, 0.17), axis="z", verts=12, mat="M_Brass_Aged", bevel=0.002))
    body.append(X.pipe("ram_in", [(0.88, 0.98, 0.14), (0.88, HDR_LO, 0.115)], 0.030, mat="M_Copper", flange_ends=False))
    # gauge boards (two): big brass gauges on short stand pipes
    needles = []
    for nm, x in (("a", -0.55), ("b", 0.55)):
        body.append(gcyl(f"gstem{nm}", 0.018, 0.150, (x, 1.46, 0.115), axis="y", verts=10, mat="M_Copper", bevel=0.0))
        gb, nd = X.gauge(f"gauge_{nm}", (x, 1.62, 0.062), r=0.085, axis="z")
        body.append(gb)
        needles.append(nd)
        nd.rotation_euler = (0, 0, 0)
    # lamps
    hz = M.sphere("hazard_lamp", 0.034, loc=G(-0.20, 1.62, 0.085), segments=14, rings=7, mat="M_Emissive_Red")
    pr = M.sphere("pressure_lamp", 0.034, loc=G(0.20, 1.62, 0.085), segments=14, rings=7, mat="M_Emissive_Warm")
    for nm, x in (("h", -0.20), ("p", 0.20)):
        body.append(gcyl(f"lampbase_{nm}", 0.046, 0.030, (x, 1.62, 0.036), axis="z", verts=16, mat="M_Brass_Aged", bevel=0.0))
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            body.append(gcyl(f"lcage_{nm}{i}", 0.0038, 0.062, (x + math.cos(a) * 0.043, 1.62 + math.sin(a) * 0.043, 0.064),
                             axis="z", verts=5, mat="M_Steel_Dark", bevel=0.0))
        body.append(M.torus(f"lring_{nm}", 0.043, 0.0042, loc=G(x, 1.62, 0.124), rot=(math.pi / 2, 0, 0), major_seg=14, minor_seg=4,
                            mat="M_Steel_Dark"))
    # enamel diagram plaque between the lamps and valves
    body.append(gbox("plaque_back", (-0.125, 1.235, 0.034), (0.125, 1.405, 0.040), "M_Brass_Polished", bevel=0.002))
    X.decal("M_Decal_PipeDiagram", "pipe_diagram.png")
    X_quad("diagram_plate", (0.0, 1.32, 0.0405), 0.23, 0.15, "M_Decal_PipeDiagram")
    # ram lever (own part): long iron arm with a brass-capped red ball grip, pivot at (0.88, 0.98, 0.17)
    lever = [gbox("arm", (0.88 - 0.016, 0.98 - 0.30, 0.17), (0.88 + 0.016, 0.98 + 0.02, 0.19), "M_Iron_Rust", bevel=0.003),
             M.sphere("grip", 0.034, loc=G(0.88, 0.98 - 0.32, 0.18), segments=10, rings=6, mat="M_Enamel_Crimson"),
             gcyl("lhub", 0.030, 0.016, (0.88, 0.98, 0.19), axis="z", verts=14, mat="M_Brass_Aged", bevel=0.002)]
    ia_ram = part("IA_ram_lever", lever, (0.88, 0.98, 0.17))
    # six handwheels (own parts, pivot at the wheel centre)
    wheels = []
    for k, x in enumerate(VX):
        w = X.wheel(f"wheelmesh{k}", 0.088, 0.0085, 5, (x, VY, WZ), axis="z", hub_r=0.024, boss_h=0.018,
                    mat="M_Enamel_Crimson", hub_mat="M_Brass_Aged", phase=0.2 * k)
        wheels.append(part(f"IA_valve_{k}", [w], (x, VY, WZ), presmooth=False))
    # bevel-free hazard bars: warning chevrons on the lower plate
    for i in range(10):
        x = -0.95 + i * 0.21
        body.append(gbox(f"chev{i}", (x, 0.52, 0.036), (x + 0.10, 0.60, 0.039), "M_Enamel_Amber" if i % 2 == 0 else "M_Lacquer_Black",
                         bevel=0.0))
    X.top(body)
    mb = part("manifold_body", body, (0, 0, 0))
    hz = part("hazard_lamp", [hz], (-0.20, 1.62, 0.085), presmooth=False)
    pr = part("pressure_lamp", [pr], (0.20, 1.62, 0.085), presmooth=False)
    needles[0].name, needles[1].name = "needle_a", "needle_b"
    return mb


def C_text(name, s, size, pos):
    m = A.text_lowpoly(name, s, size, depth=0.0012, mat="M_Lacquer_Black", font_path=X.FONT, resolution=1)
    m.data.transform(Matrix.Translation(GV(pos)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    return m


def X_quad(name, centre, w, h, mat):
    return X.gquad(name, centre, (1, 0, 0), (0, 1, 0), w, h, mat) if hasattr(X, "gquad") else None


def main():
    build()
    required = ["manifold_body", "diagram_plate", "hazard_lamp", "pressure_lamp", "needle_a", "needle_b", "IA_ram_lever"] + \
               [f"IA_valve_{k}" for k in range(6)]
    expect = {f"IA_valve_{k}": (VX[k], VY, WZ) for k in range(6)}
    expect["IA_ram_lever"] = (0.88, 0.98, 0.17)
    errs = X.finish(NAME, required, [r for r in required if r != "diagram_plate"], BUDGET, expect, show=required[:6])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.2, 1.3, 2.9), (0.0, 1.15, 0.0), 52), ("_2", (-0.5, 1.2, 1.1), (-0.45, 1.15, 0.0), 45)],
                   floor=False, world=0.18,
                   lights=X.STUDIO)
    return errs


main()
