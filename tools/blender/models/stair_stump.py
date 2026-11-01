"""stair_stump.glb — the stump of the spiral stair in the Archive hall: a collapsed route with a wedged ladder (thread "blocked spiral stair").

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3, §3b: "Hall - Gallery: spiral stair, blocked by a wedged ladder at the landing"). A cast-iron spiral
stair that is cut off after eight wedge treads: a central column, treads of chequer plate on cantilever brackets, an outer balustrade with a helical handrail,
a bent and broken landing at the top (1.62 m above the floor) and a long wooden ladder jammed diagonally across the gap between the landing and the
column, with two fallen balusters. Opens from above later (the wedge pin on the Gallery side): `IA_wedge_ladder` can slide away / fall.
Light by design (the hall is near its draw-call limit): three static materials merged into one object, the ladder is one object.

Model space (Godot): origin on the floor at the centre of the column; footprint radius 0.95; front +Z (the first tread starts at +Z and the stair turns
counter-clockwise seen from above, so the open side of the entrance faces the hall). Height 1.62 (treads) + 0.9 ladder. Suggested placement: against a free wall /
pilaster, see docs/models/ch2_exp.md.

Parts:
  stair_stump_body   column, 8 treads, brackets, balustrade, handrail, broken landing, fallen balusters (M_Steel_Dark, M_Chequer, M_Iron_Rust)
  IA_wedge_ladder    the wedged ladder (M_Wood_Walnut + a few M_Steel_Dark straps), origin = its lower end on the landing (0.62, 1.64, -0.22), identity;
                     slide it +0.9 along its own axis / or hide it when the route opens from above
  light_stair_top    empty (0.0, 2.3, 0.0), optional dust/light shaft above the stump

    blender -b --factory-startup -P tools/blender/models/stair_stump.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gpoly, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "stair_stump"
BUDGET = 3600
ARGS = M.main_guard()
DARK, CHEQ, RUST, WOOD = "M_Steel_Dark", "M_Chequer", "M_Iron_Rust", "M_Wood_Walnut"
R0, R1 = 0.07, 0.92          # column radius, tread outer radius
STEPS, RISE = 8, 0.18
STEP_ANG = math.radians(30.0)


def tread(i):
    a0 = i * STEP_ANG
    a1 = a0 + STEP_ANG + 0.02
    y = RISE * (i + 1)
    pts = []
    for k in range(3):
        a = a0 + (a1 - a0) * k / 2
        pts.append((math.sin(a) * R0 * 1.2, math.cos(a) * R0 * 1.2))
    for k in range(3):
        a = a1 - (a1 - a0) * k / 2
        pts.append((math.sin(a) * R1, math.cos(a) * R1))
    # polygon in the Godot XZ plane (x, z) -> local (x, -z) of the horizontal frame
    poly = [(x, -z) for x, z in pts]
    fr = X.C.gframe((0.0, y - 0.035, 0.0), (1, 0, 0), (0, 0, -1))
    plate = gpoly(f"tr{i}", poly, 0.035, fr, mat=CHEQ, bevel=0.002)
    return plate


def body():
    o = []
    o.append(gcyl("column", R0, RISE * STEPS + 0.12, (0.0, 0.0, 0.0), axis="y", verts=14, mat=DARK, bevel=0.003))
    o.append(gcyl("base", 0.16, 0.05, (0.0, 0.0, 0.0), axis="y", verts=14, mat=DARK, bevel=0.004, r_top=0.10))
    o.append(gcyl("cap", 0.10, 0.04, (0.0, RISE * STEPS + 0.12, 0.0), axis="y", verts=14, mat=RUST, bevel=0.004, r_top=0.07))
    hand = []
    for i in range(STEPS):
        o.append(tread(i))
        am = i * STEP_ANG + STEP_ANG / 2
        y = RISE * (i + 1)
        # balusters at the outer edge on every tread
        ax, az = math.sin(am) * (R1 - 0.03), math.cos(am) * (R1 - 0.03)
        o.append(gcyl(f"bal{i}", 0.009, 0.82, (ax, y, az), axis="y", verts=6, mat=DARK, bevel=0.0))
        hand.append((ax, y + 0.84, az))
    o.append(X.pipe("handrail", hand, 0.020, mat=RUST, sides=8, flange_ends=False, fillet=0.0))
    return o


def brackets():
    o = []
    for i in range(STEPS):
        am = i * STEP_ANG + STEP_ANG / 2
        y = RISE * (i + 1)
        b = gbox(f"brk{i}", (-0.012, y - 0.115, R0), (0.012, y - 0.035, R1 * 0.80), DARK, bevel=0.0)
        A.place(b, Matrix.Rotation(am, 4, "Z"))
        o.append(b)
    return o


def landing():
    o = []
    top = RISE * STEPS + 0.18
    # a broken landing plate: irregular polygon sticking out at the top, bent rim, with a torn edge
    am = STEPS * STEP_ANG
    pts = [(math.sin(am) * R0 * 1.2, math.cos(am) * R0 * 1.2), (math.sin(am + 0.5) * 0.55, math.cos(am + 0.5) * 0.55), (math.sin(am + 0.95) * 0.80, math.cos(am + 0.95) * 0.80),
           (math.sin(am + 0.35) * 0.95, math.cos(am + 0.35) * 0.95), (math.sin(am - 0.02) * 0.92, math.cos(am - 0.02) * 0.92)]
    fr = X.C.gframe((0.0, top - 0.035, 0.0), (1, 0, 0), (0, 0, -1))
    o.append(gpoly("landing", [(x, -z) for x, z in pts], 0.035, fr, mat=CHEQ, bevel=0.002))
    o.append(gbox("land_beam", (-0.02, top - 0.14, R0), (0.02, top - 0.035, 0.9), DARK, bevel=0.0))
    A.place(o[-1], Matrix.Rotation(am + 0.4, 4, "Z"))
    # a bent, broken balustrade stub and two fallen balusters on the landing
    for k, (da, dh, tilt) in enumerate(((0.45, 0.55, 0.5), (0.75, 0.30, -0.6))):
        a = am + da
        o.append(gcyl(f"stub{k}", 0.009, dh, (math.sin(a) * 0.70, top, math.cos(a) * 0.70), axis=(math.sin(a) * tilt, 1.0, math.cos(a) * tilt), verts=6, mat=DARK, bevel=0.0))
    o.append(gcyl("fallen_a", 0.009, 0.62, (-0.35, 0.015, 0.78), axis="x", verts=6, mat=DARK, bevel=0.0))
    o.append(gcyl("fallen_b", 0.009, 0.55, (-0.52, 0.015, 0.62), axis=(0.8, 0.0, -0.4), verts=6, mat=DARK, bevel=0.0))
    # rubble: two broken tread plates lying on the floor and a bent handrail piece
    pl = gpoly("rub", [(0.0, 0.0), (0.30, 0.04), (0.34, 0.20), (0.10, 0.26), (-0.04, 0.12)], 0.035, X.C.gframe((0.50, 0.0, 0.70), (1, 0, 0), (0, 0, -1)), mat=CHEQ,
               bevel=0.002)
    o.append(pl)
    o.append(X.pipe("rail_down", [(0.9, 0.04, 0.2), (0.7, 0.04, 0.55), (0.35, 0.05, 0.85)], 0.020, mat=RUST, sides=8, flange_ends=False, fillet=0.08))
    return o


def ladder():
    o = []
    base = Vector((0.62, 1.64, -0.22))
    d = Vector((-0.55, 0.62, 0.35)).normalized()         # leaning across the gap toward the column and up
    ln, w = 2.0, 0.22
    side = Vector((0.0, 0.0, 1.0)).cross(d).normalized() * (w / 2)
    side = Vector((d.z, 0.0, -d.x)).normalized() * (w / 2)
    for sgn in (-1, 1):
        a = base + side * sgn
        b = a + d * ln
        o.append(_rail(f"lr{sgn}", a, b, 0.032, 0.020))
    for k in range(7):
        c0 = base + d * (0.12 + 0.28 * k)
        a = c0 - side
        b = c0 + side
        o.append(_rail(f"rung{k}", a, b, 0.020, 0.020))
    for k, t in enumerate((0.55, 1.35)):                  # iron straps where it jams
        c = base + d * t
        o.append(gbox(f"strap{k}", tuple(c - Vector((0.13, 0.03, 0.03))), tuple(c + Vector((0.13, 0.03, 0.03))), DARK, bevel=0.002))
    return part("IA_wedge_ladder", o, (0.62, 1.64, -0.22))


def _rail(name, a, b, w, t):
    """Square beam between two Godot points (a, b: Vector)."""
    mid = (a + b) / 2
    dv = b - a
    o = M.box(name, (t, dv.length, w), loc=(0, 0, 0), mat=WOOD, bevel=0.003, segments=1)
    A.place(o, Matrix.Identity(4))
    bd = GV(dv).normalized()
    q = Vector((0, 1, 0)).rotation_difference(bd)
    o.data.transform(q.to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(GV(mid)))
    return o


def main():
    X.begin()
    lad = ladder()
    o = body() + brackets() + landing()
    X.top(o)
    mount("light_stair_top", (0.0, 2.3, 0.0))
    part("stair_stump_body", o, (0, 0, 0))


if __name__ == "__main__":
    main()
    req = ["stair_stump_body", "IA_wedge_ladder", "light_stair_top"]
    errs = X.finish(NAME, req, ["IA_wedge_ladder"], BUDGET, {"IA_wedge_ladder": (0.62, 1.64, -0.22)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.8, 1.7, 2.4), (0.0, 0.85, 0.0), 50), ("_top", (-1.6, 2.3, 1.6), (0.2, 1.4, 0.0), 46)], floor=True, world=0.15)
