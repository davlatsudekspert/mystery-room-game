"""library_ladder.glb — walnut library ladder (2.3 m) leaning on the archive's west wall (dressing, no parts).

Two tapered walnut rails (0.42 apart at the foot, 0.36 at the top) with eight level treads housed into them,
two brass tie rods, brass ferrules, rubber shoes at the foot and felt pads where the rail tops rest on the wall.

Origin = the floor point midway between the feet. Front (climbing face) = +Z. The ladder leans back: the rail
tops touch a wall plane at local z = -0.38 (top centre at about y 2.27).
Placement: (-4.62, 0, 0.35), yaw 90 -> the wall plane is the west wall x = -5.0.

    blender -b --factory-startup -P tools/blender/models/library_ladder.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G, GV  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "library_ladder"
L = 2.30                 # rail length
WALL = 0.38              # wall plane distance behind the feet
RD, RW = 0.068, 0.036    # rail depth (in the lean plane) and width
DZ = WALL - RD / 2 - 0.006   # rail centreline set-back at the top (felt pad thickness)
HT = math.sqrt(L * L - DZ * DZ)
W0, W1 = 0.21, 0.18      # rail centre half-spacing at the foot / top
WAL, BRASS = "M_Wood_Walnut", "M_Brass_Aged"


def rail_point(side, t):
    """Godot point on a rail centreline, t = 0 (foot) .. 1 (top)."""
    return Vector((side * (W0 + (W1 - W0) * t), HT * t, -DZ * t))


def beam(name, p0, p1, w, d, mat, bevel=0.006, seg=2):
    """Box from Godot p0 to p1 (centreline), width w across (Godot x-ish), depth d in the lean plane."""
    axis = (p1 - p0)
    ln = axis.length
    ey = axis.normalized()
    ex = Vector((1, 0, 0))
    ex = (ex - ey * ex.dot(ey)).normalized()
    ez = ex.cross(ey)
    o = M.box(name, (w, ln, d), loc=(0, ln / 2, 0), mat=mat, bevel=bevel, segments=seg)
    m = A.frame_matrix(GV(p0), GV(ex), GV(ey), GV(ez))
    A.place(o, m)
    return o


def build():
    M.reset_scene()
    C.ensure_materials()
    parts = []
    for s in (-1, 1):
        p0, p1 = rail_point(s, 0.0), rail_point(s, 1.0)
        parts.append(beam(f"rail{s}", p0, p1, RW, RD, WAL))
        # rubber shoe + brass ferrule at the foot, brass cap + felt pad at the top
        parts.append(beam(f"shoe{s}", p0 - Vector((0, 0.0, 0)), rail_point(s, 0.018), RW + 0.006, RD + 0.006, "M_Rubber", 0.004, 1))
        parts.append(beam(f"ferrule{s}", rail_point(s, 0.018), rail_point(s, 0.034), RW + 0.004, RD + 0.004, BRASS, 0.002, 1))
        parts.append(beam(f"cap{s}", rail_point(s, 0.985), rail_point(s, 1.0) + Vector((0, 0.004, 0)), RW + 0.004, RD + 0.004,
                          BRASS, 0.003, 1))
        pad_c = rail_point(s, 0.955) + Vector((0, 0, -RD / 2 - 0.003))
        parts.append(C.gcyl(f"pad{s}", 0.014, 0.006, tuple(pad_c), axis="-z", verts=10, mat="M_Felt", bevel=0.0015))
    # eight level treads housed between the rails
    n = 8
    for k in range(n):
        y = 0.26 + k * 0.268
        t = y / HT
        zc = -DZ * t
        half = W0 + (W1 - W0) * t - RW / 2 + 0.004
        o = M.box(f"tread{k}", (2 * half, 0.024, 0.112), loc=(0, 0, 0), mat=WAL, bevel=0.005, segments=2)
        o.data.transform(Matrix.Translation(G(0.0, y, zc + 0.022)))
        parts.append(o)
        # brass nosing strip on the front edge (worn bright)
        parts.append(M.box(f"nosing{k}", (2 * half - 0.03, 0.006, 0.012), loc=G(0.0, y + 0.012, zc + 0.022 + 0.05), mat="M_Brass_Polished",
                           bevel=0.0015, segments=1))
    # two brass tie rods under treads 1 and 6 with round washers on the rail outer faces
    for k in (1, 6):
        y = 0.26 + k * 0.268 - 0.035
        t = y / HT
        zc = -DZ * t
        half = W0 + (W1 - W0) * t + RW / 2 + 0.004
        parts.append(C.gcyl(f"tierod{k}", 0.0045, 2 * half, (-half, y, zc), axis="x", verts=8, mat=BRASS, bevel=0.0))
        for s in (-1, 1):
            parts.append(C.gcyl(f"washer{k}{s}", 0.011, 0.004, (s * half, y, zc), axis="x" if s > 0 else "-x", verts=10, mat=BRASS,
                                bevel=0.001))
    A.presmooth(parts)
    lad = M.join(parts, "library_ladder")
    C.finalize_all(wood_grain=False)
    # wood grain along the rails: force vertical grain on the rail faces, horizontal on the treads
    A.grain_uv(lad, force=lambda c, nrm: True if abs(c.x) > 0.15 else False)
    C.report(NAME)
    return lad


def main():
    args = M.main_guard()
    lad = build()
    path = C.export(NAME)
    C.verify_glb(path, required=["library_ladder"], budget=2500)
    top = rail_point(1, 1.0)
    print(f"{C.TAG} ladder: rail top centre y={top.y:.3f} z={top.z:.3f}; height={HT:.3f}; lean={math.degrees(math.asin(DZ / L)):.1f} deg")
    if "--no-render" in args:
        return
    sel = C.args_shots(args)
    C.qa_begin()
    C.qa_place([lad], (-4.62, 0.0, 0.35), 90.0)
    C.qa_import(C.model_glb("room_archive"))
    C.qa_import(C.model_glb("vent_grille"), (-5.0, 2.55, 0.9), 90.0)
    C.qa_import(C.model_glb("card_catalogue"), (-5.0, 0, -1.2), 90.0)
    for p in C.PENDANTS:
        C.qa_import(C.model_glb("archive_pendant"), p, 0.0)
    if C.want("hero", sel):
        C.qa_room_lights()
        C.shoot(NAME, (-2.7, 1.5, 1.6), (-4.75, 1.2, 0.35), vfov=56)
        C.qa_clear()
    if C.want("detail", sel):
        C.qa_room_lights()
        C.qa_light("key", "POINT", (-4.0, 1.0, 0.9), 6.0, "FFE2C0", radius=0.06)
        C.shoot(NAME + "_detail", (-3.95, 0.75, 0.95), (-4.65, 0.35, 0.35), vfov=44)
        C.qa_clear()


main()
