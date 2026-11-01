"""service_door.glb — the service door in the Archive hall's east wall, hidden behind a painted cover hatch (puzzle N1 "Warm Wall").

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3, §8 N1). Behind the warm east wall hides the door to the Pump Room: a hatch-like cover panel painted like the hall wall
(green dado, walnut rail, plaster above) hides a heavy riveted steel door in a casing, with a telephone-dial combination lock (the same convention as `booth_door`,
code 0417) and a lock lamp; behind it a short stair goes down into the dark. Light by design (the hall is at its draw-call limit): two merged static objects,
at most 4 materials on the leaf, the hole liners are tap-disc volumes only (hide their meshes). While the cover is closed only `IA_cover_panel` (2 surfaces) needs
to be visible; show `service_door_frame`, `IA_service_door`, `service_lamp` when the cover opens.

Model space (Godot): origin at the centre of the 0.90 x 2.10 opening, at floor level, on the HALL-side wall plane (local z = 0); the wall occupies local z in
[-0.20, 0]; local +Z (front) faces the hall. Placement: east wall, (5.0, 0, 2.95), yaw -90 (then the hinge side, local -X, is the north side toward the compressor). The cover panel
stands 3 cm proud of the wall.

Parts:
  service_door_frame   static: casing, reveal liners, threshold, the stair shaft with four steps going down (M_Steel_Painted, M_Concrete, M_Steel_Dark)
  IA_service_door      the leaf (0.84 x 2.06 x 0.07). Origin = hinge axis at floor level (-0.43, 0.0, -0.04); OPEN = -100 deg about +Y (the free edge swings out into the hall)
  IA_rotary_dial       child of the leaf: the chrome finger wheel (diameter 0.121), origin = dial centre (0.20, 1.42, 0.0095) in model space. Hole n (1..9, 0 as n = 10) at
                       theta = 50 + (n - 1) * 30 deg counter-clockwise from +X seen from the front, at radius 0.0445; the finger stop is at -10 deg. Dialling n =
                       rotate (theta_n + 10) deg CLOCKWISE (negative about +Z), then release (spring back to 0)
  IA_dial_hole_<d>     d = 0..9, children of the wheel: a short liner tube in each finger hole; its AABB is the tap disc, origin = hole centre on the wheel mid-plane (hide the mesh)
  service_lamp         jewel (M_Emissive_Red) above the door head, origin (0.0, 2.175, 0.035); the code changes its emission (red locked, green open)
  IA_cover_panel       the painted cover hatch, 1.04 x 2.20, origin = hinge line at its top edge (0.0, 2.20, 0.0475); OPEN = -75 deg about +X (the bottom swings out of the wall, up)
  light_service        empty (0.0, 1.9, 0.5) in front of the opened door

    blender -b --factory-startup -P tools/blender/models/service_door.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gpoly, gtext, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "service_door"
BUDGET = 4200
ARGS = M.main_guard()
PAINT, DARK, CONC = "M_Steel_Painted", "M_Steel_Dark", "M_Concrete"
HX, HZ = -0.43, -0.04                       # hinge axis
DX, DY, DZ = 0.20, 1.42, 0.0095             # dial centre
RING_R = 0.0445


def frame():
    o = []
    # casing: head and jambs, proud 25 mm; reveal liners inside the wall thickness
    o.append(gbox("cs_l", (-0.55, 0.0, 0.0), (-0.45, 2.22, 0.025), PAINT, bevel=0.004))
    o.append(gbox("cs_r", (0.45, 0.0, 0.0), (0.55, 2.22, 0.025), PAINT, bevel=0.004))
    o.append(gbox("cs_h", (-0.45, 2.10, 0.0), (0.45, 2.22, 0.025), PAINT, bevel=0.004))
    o.append(gbox("lin_l", (-0.45, 0.0, -0.20), (-0.43, 2.10, 0.0), DARK, bevel=0.0))
    o.append(gbox("lin_r", (0.43, 0.0, -0.20), (0.45, 2.10, 0.0), DARK, bevel=0.0))
    o.append(gbox("lin_h", (-0.45, 2.08, -0.20), (0.45, 2.10, 0.0), DARK, bevel=0.0))
    o.append(gbox("thresh", (-0.55, 0.0, -0.20), (0.55, 0.02, 0.06), CONC, bevel=0.003))
    # stair shaft behind the door: floor steps going down, side walls and a back wall (dark), so the opened door shows a descent
    for i in range(4):
        o.append(gbox(f"step{i}", (-0.43, -0.20 * (i + 1), -0.20 - 0.30 * (i + 1)), (0.43, -0.20 * i, -0.20 - 0.30 * i), CONC, bevel=0.0))
    o.append(gbox("sh_l", (-0.50, -0.90, -1.60), (-0.43, 2.10, -0.20), CONC, bevel=0.0))
    o.append(gbox("sh_r", (0.43, -0.90, -1.60), (0.50, 2.10, -0.20), CONC, bevel=0.0))
    o.append(gbox("sh_back", (-0.50, -0.90, -1.66), (0.50, 2.10, -1.60), DARK, bevel=0.0))
    o.append(gbox("sh_top", (-0.45, 2.10, -1.66), (0.45, 2.16, -0.20), CONC, bevel=0.0))
    # hinge knuckles on the frame
    for y in (0.30, 1.76):
        o.append(gcyl(f"kn{y}", 0.020, 0.14, (HX - 0.005, y - 0.07, HZ), axis="y", verts=10, mat=DARK, bevel=0.0))
    return o


def leaf():
    o = []
    o.append(gbox("skin", (HX + 0.012, 0.02, HZ - 0.035), (0.418, 2.06, HZ + 0.035), PAINT, bevel=0.008, seg=2))
    # two fielded panels (recessed look: raised border ring is the skin; the field is a lower plate) + a lock rail zone
    for nm, y0, y1 in (("pn_lo", 0.12, 0.78), ("pn_hi", 1.00, 1.96)):
        o.append(gbox(nm, (-0.33, y0, HZ + 0.032), (0.33, y1, HZ + 0.043), PAINT, bevel=0.007, seg=2))
    o.append(gbox("kick", (HX + 0.02, 0.02, HZ + 0.034), (0.41, 0.17, HZ + 0.046), "M_Chrome", bevel=0.003))
    # rivet rows along both vertical edges (one merged cone object)
    pts = []
    for y in [0.30 + 0.20 * k for k in range(9)]:
        pts += [(-0.385, y, HZ + 0.035), (0.385, y, HZ + 0.035)]
    r = X.rivets("lrv", pts, 0.0085, "z", mat=PAINT, segs=5)
    if r:
        o.append(r)
    # hinge straps
    for y in (0.30, 1.76):
        o.append(gbox(f"strap{y}", (HX - 0.005, y - 0.05, HZ + 0.030), (-0.10, y + 0.05, HZ + 0.046), DARK, bevel=0.004))
        o.append(gcyl(f"eye{y}", 0.021, 0.10, (HX - 0.005, y - 0.05, HZ), axis="y", verts=10, mat=DARK, bevel=0.0))
    # lever handle (chrome) on the latch side
    o.append(gbox("hd_base", (0.34, 1.00, HZ + 0.043), (0.39, 1.06, HZ + 0.062), "M_Chrome", bevel=0.003))
    o.append(gbox("hd_bar", (0.22, 1.015, HZ + 0.052), (0.385, 1.045, HZ + 0.075), "M_Chrome", bevel=0.005, seg=2))
    # fixed number plate (cream enamel) with the numerals in the finger holes, finger stop at -10 deg
    z0 = HZ + 0.043 + 0.0
    o.append(glathe("plate", [(0.0, 0.0), (0.066, 0.0), (0.0675, 0.002), (0.0675, 0.004), (0.0, 0.004)], (DX, DY, z0), axis="z", segments=26, mat="M_Enamel_Cream"))
    for k in range(10):
        n = k if k else 10
        th = math.radians(50 + (n - 1) * 30)
        x, y = DX + math.cos(th) * RING_R, DY + math.sin(th) * RING_R
        o.append(gtext(f"num{k}", str(k if k < 10 else 0), 0.013, X.C.gframe((x, y, z0 + 0.0045), (1, 0, 0), (0, 1, 0)), depth=0.0008, font=X.FONT, mat=DARK, resolution=1))
    sa = math.radians(-10)
    o.append(gbox("stop", (DX + math.cos(sa) * 0.0625 - 0.004, DY + math.sin(sa) * 0.0625 - 0.008, z0 + 0.0045), (DX + math.cos(sa) * 0.0625 + 0.004, DY + math.sin(sa) * 0.0625 + 0.008,
                                                                                                                z0 + 0.020), "M_Chrome", bevel=0.001))
    return o, z0


def wheel(z0):
    # annular finger wheel with 10 finger holes (boolean cut), chrome, 12 mm thick, sitting 2 mm above the plate
    zc = z0 + 0.0065
    ring = X.glathe_loop("wheel", [(0.027, 0.0), (0.0605, 0.0), (0.0615, 0.0015), (0.0615, 0.0105), (0.0605, 0.012), (0.027, 0.012)], (DX, DY, zc), axis="z", segments=30, mat="M_Chrome")
    objs = [ring]
    for k in range(10):
        n = k if k else 10
        th = math.radians(50 + (n - 1) * 30)
        x, y = DX + math.cos(th) * RING_R, DY + math.sin(th) * RING_R
        cutter = gcyl("hcut", 0.0098, 0.03, (x, y, zc - 0.009), axis="z", verts=10, mat="M_Concrete", bevel=0.0)
        M.boolean(ring, cutter)
    liners = []
    for k in range(10):
        n = k if k else 10
        th = math.radians(50 + (n - 1) * 30)
        x, y = DX + math.cos(th) * RING_R, DY + math.sin(th) * RING_R
        lin = glathe(f"IA_dial_hole_{k}", [(0.0088, 0.0), (0.0098, 0.0), (0.0098, 0.012), (0.0088, 0.012)], (x, y, zc), axis="z", segments=8, mat="M_Chrome")
        liners.append(part(f"IA_dial_hole_{k}", [lin], (x, y, zc + 0.006), presmooth=False))
    wh = part("IA_rotary_dial", [ring], (DX, DY, zc))
    return wh, liners


def cover():
    o = []
    x0, x1, y0, y1, z0, z1 = -0.52, 0.52, 0.0, 2.20, 0.030, 0.065
    o.append(gbox("cv_lo", (x0, y0, z0), (x1, 1.37, z1), "M_Paint_Green", bevel=0.004))
    o.append(gbox("cv_hi", (x0, 1.44, z0), (x1, y1, z1), "M_Plaster_Wall", bevel=0.004))
    for x in (-0.46, 0.46):                              # four tiny dark screws read as an access hatch
        for y in (0.20, 2.0):
            o.append(gcyl(f"cs{x}{y}", 0.008, 0.004, (x, y, z1), axis="z", verts=6, mat="M_Paint_Green" if y < 1.4 else "M_Plaster_Wall", bevel=0.0))
    return part("IA_cover_panel", o, (0.0, 2.20, 0.0475))


def main():
    X.begin()
    fr = frame()
    lf, z0 = leaf()
    wh, liners = wheel(z0)
    X.top(fr + lf)
    leaf_part = part("IA_service_door", lf, (HX, 0.0, HZ))
    X.C.parent(wh, leaf_part)
    for li in liners:
        X.C.parent(li, wh)
    lamp = part("service_lamp", [glathe("lamp_j", [(0.0, 0.0), (0.0095, 0.0), (0.010, 0.003), (0.007, 0.008), (0.0, 0.009)], (0.0, 2.175, 0.025), axis="z", segments=10,
                                       mat="M_Emissive_Red")], (0.0, 2.175, 0.035), presmooth=False)
    cov = cover()
    mount("light_service", (0.0, 1.9, 0.5))
    part("service_door_frame", fr, (0, 0, 0))
    return leaf_part


if __name__ == "__main__":
    main()
    req = ["service_door_frame", "IA_service_door", "IA_rotary_dial", "service_lamp", "IA_cover_panel", "light_service"] + [f"IA_dial_hole_{k}" for k in range(10)]
    errs = X.finish(NAME, req, ["IA_service_door", "IA_rotary_dial", "service_lamp"], BUDGET,
                    {"IA_service_door": (HX, 0.0, HZ), "IA_rotary_dial": (DX, DY, DZ), "IA_cover_panel": (0.0, 2.20, 0.0475)}, show=req[:6])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.4, 1.5, 2.4), (0.0, 1.1, 0.0), 48), ("_dial", (0.20, 1.45, 0.55), (0.20, 1.40, 0.0), 24)], floor=True, world=0.25)
