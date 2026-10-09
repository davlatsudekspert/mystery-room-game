"""strand_fork.glb — Strand's steel tuning fork (Chapter 3 finale prop: held by Strand's echo, placed in the
Gallery console's choice_mount). Not an inventory item, but built with the item pipeline.

A polished steel (M_Chrome) tuning fork, 240 mm overall: two parallel tines of rectangular section
(6 x 5.5 mm, gap 7.5 mm) on a U yoke, a round turned stem (Ø 7.6 mm), and a heavy brass ball foot
(M_Brass_Aged, Ø 28 mm) with a flat medallion on its front that carries **Strand's mark** (a ring crossed by
a vertical meridian bar, as on key_strand) in polished steel.
Stands upright, stem down, tines up; the U of the fork and the mark face +Z (Godot).
Origin at the centre of mass, which lies on the stem: a fist closed round the stem at the origin holds it
(echo_strand_rail fork_mount, identity).
    blender -b --factory-startup -P tools/blender/models/strand_fork.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch3_items as G  # noqa: E402

NAME = "strand_fork"
STEEL, BRASS = "M_Chrome", "M_Brass_Aged"
RB = 0.0140                 # ball radius
ZB = RB - 0.0006            # ball centre (a small flat underneath to stand on)
TINE_W, TINE_T, GAP = 0.0060, 0.0055, 0.0075
Z_TOP = 0.2400              # tine tops (overall length 240 mm)
Z_YOKE = 0.1300             # centre of the yoke's bend
STEM_R = 0.0038


def ball():
    import math
    prof = [(0.0, 0.0)]
    flat = 0.0042
    prof.append((flat, 0.0))
    a0 = math.asin(flat / RB) if flat < RB else 0.0
    n = 10
    for i in range(1, n + 1):
        t = -math.pi / 2 + a0 + (math.pi - a0 - 0.30) * i / n          # up the sphere to the neck
        prof.append((RB * math.cos(t), ZB + RB * math.sin(t)))
    zt = prof[-1][1]
    prof += [(0.0052, zt + 0.0012), (0.0046, zt + 0.0030), (0.0, zt + 0.0032)]
    b = L.lathe2("ball", prof, segments=20, mat=BRASS)
    # medallion: a flat brass disc proud of the ball's front, with the mark inlaid in steel
    med = D.revolve("medallion", [(0.0, -0.0040), (0.0074, -0.0040), (0.0074, 0.0004), (0.0068, 0.0010),
                                  (0.0, 0.0010)], direction=(0, -1, 0), loc=(0, -RB + 0.0002, ZB),
                    segments=20, mat=BRASS)
    yf = -RB - 0.00125
    ring = L.flat_shape("mark_ring", L.circle_line(0.0043, 0.0012, n=20), mat=STEEL)
    bar = L.flat_shape("mark_bar", [L.rounded_rect(0.0011, 0.0120, 0.0002, 1)], mat=STEEL)
    L.to_front(ring, y_back=yf, z=ZB)
    L.to_front(bar, y_back=yf - 0.00008, z=ZB)          # the meridian lies over the ring (no z-fight)
    return M.join([b, med, ring, bar], "ball_foot")


def stem(z0):
    prof = [(0.0, z0 - 0.002), (0.0050, z0 - 0.002), (0.0050, z0 + 0.0015), (0.0042, z0 + 0.0030),
            (STEM_R, z0 + 0.0045), (STEM_R, Z_YOKE - 0.0150), (0.0044, Z_YOKE - 0.0108), (0.0, Z_YOKE - 0.0080)]
    return L.lathe2("stem", prof, segments=12, mat=STEEL)


def fork():
    import math
    ro = GAP / 2 + TINE_W
    ri = GAP / 2
    cap = 0.0018
    pts = []
    # outer contour, counter-clockwise: left tine outer edge down, round the yoke, right tine up
    pts.append((-ro + cap, Z_TOP))
    pts.append((-ro, Z_TOP - cap))
    n = 10
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        pts.append((ro * math.cos(a), Z_YOKE + ro * math.sin(a)))
    pts.append((ro, Z_TOP - cap))
    pts.append((ro - cap, Z_TOP))
    pts.append((ri + cap * 0.6, Z_TOP))
    pts.append((ri, Z_TOP - cap * 0.6))
    for i in range(7):
        a = -math.pi * i / 6
        pts.append((ri * math.cos(a), Z_YOKE + 0.0016 + ri * math.sin(a)))
    pts.append((-ri, Z_TOP - cap * 0.6))
    pts.append((-ri - cap * 0.6, Z_TOP))
    f = L.curve_solid("fork", [pts], TINE_T, bevel=0.0007, bevel_res=0, mat=STEEL)
    L.to_front(f, y_back=TINE_T / 2)
    return f


def build():
    b = ball()
    zt = max(v.co.z for v in b.data.vertices)
    s = stem(zt - 0.0012)
    f = fork()
    rest = M.join([s, f], "fork_steel")
    allp = M.join([b, rest], NAME)
    return [allp]


def post():
    D.resmooth(bpy.data.objects[NAME], 32.0)


def report():
    lo, hi = D.bounds()
    G.report_point("bottom (ball underside)", point=(0.0, 0.0, lo.z))
    G.report_point("tine tops", point=(0.0, 0.0, hi.z))
    stem_z0 = lo.z + 2 * RB - 0.0006
    stem_z1 = lo.z + Z_YOKE - 0.0150
    print(f"[items3] round stem (Ø {2 * STEM_R:.4f}) spans godot y {stem_z0:+.4f} .. {stem_z1:+.4f}; "
          f"the origin (centre of mass) is {'ON' if stem_z0 < 0 < stem_z1 else 'NOT on'} the stem")


def main():
    G.item_main(NAME, build, post=post, budget=1200, extra_report=report, shots=[
        ("", (0.30, -0.66, 0.22), (0.0, 0.0, 0.040), 60),
        ("_2", (0.03, -0.14, -0.035), (0.0, 0.0, -0.075), 70),
    ])


if __name__ == "__main__":
    main()
