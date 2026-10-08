"""chair.glb — bentwood cafe/office chair (Thonet No.18 pattern, the type still standard issue in
1960s-70s institutes): steam-bent walnut-stained beech, round leather-padded seat, continuous back
bow that runs down into the rear legs, inner back loop, leg hoop.

Origin = floor centre under the seat. Front faces Blender -Y (Godot +Z). Seat top 0.465 m,
overall 0.47 w x 0.92 h x 0.55 d. Static (no IA_ parts).

    blender -b --factory-startup -P tools/blender/models/chair.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Vector  # noqa: E402

NAME = "chair"
W = "M_Wood_Walnut"
SEAT_R = 0.20
RING_Z0, RING_Z1 = 0.405, 0.448


def mirror_path(half):
    """half = points from the left end to the centre (x <= 0); returns the full symmetric path."""
    full = list(half)
    for p in reversed(half[:-1]):
        full.append((-p[0], p[1], p[2]))
    return full


def bent(name, half_pts, half_radii, sides=8, sub=2):
    pts = mirror_path(half_pts)
    rad = list(half_radii) + list(reversed(half_radii[:-1]))
    return A.tube(name, A.catmull(pts, sub), 0.014, sides=sides, radii=A.resample_radii(pts, rad, sub), mat=W)


def leg(name, top, bottom, r_top=0.0165, r_bot=0.0125):
    top, bottom = Vector(top), Vector(bottom)
    d = top - bottom
    ln = d.length
    prof = [(0.0, 0.0), (r_bot - 0.002, 0.0), (r_bot, 0.003), (r_bot + (r_top - r_bot) * 0.5, ln * 0.5),
            (r_top, ln - 0.004), (r_top - 0.003, ln)]
    o = M.lathe(name, prof, segments=10, mat=W)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.transform(q.to_matrix().to_4x4())
    o.location = bottom
    return o


def build():
    M.reset_scene()
    A.prepare_materials()
    parts = []
    # seat ring (bent rim) and padded leather seat
    ring = A.lathe_loop("seat_ring", A.rounded_rect(0.026, RING_Z1 - RING_Z0, 0.009, seg=2,
                                                   cx=SEAT_R, cy=(RING_Z0 + RING_Z1) / 2), segments=28, mat=W)
    parts.append(ring)
    pad = M.lathe("seat_pad", [(0.0, 0.438), (0.190, 0.438), (0.194, 0.446), (0.191, 0.453), (0.180, 0.459),
                               (0.145, 0.4635), (0.075, 0.4655), (0.0, 0.466)], segments=28, mat="M_Leather")
    A.mat_by_face(pad, lambda c, n, cur: W if n.z < -0.5 else None)
    parts.append(pad)
    # piping welt around the leather
    parts.append(M.torus("seat_welt", 0.1925, 0.0032, loc=(0, 0, 0.4505), major_seg=28, minor_seg=5, mat="M_Leather"))
    # front legs (splayed)
    legs_at_hoop = []
    for s, th in (("l", -130.0), ("r", -50.0)):
        t = math.radians(th)
        top = (0.196 * math.cos(t), 0.196 * math.sin(t), RING_Z0 + 0.004)
        bot = (0.238 * math.cos(t), 0.238 * math.sin(t), 0.0)
        parts.append(leg(f"leg_front_{s}", top, bot))
        k = 0.20 / top[2]
        legs_at_hoop.append(Vector(bot).lerp(Vector(top), k))
    # back bow: floor -> rear leg -> past the seat ring -> back uprights -> crest -> mirror
    half = [(-0.128, 0.240, 0.0), (-0.121, 0.216, 0.20), (-0.1145, 0.198, 0.43), (-0.120, 0.213, 0.56),
            (-0.138, 0.246, 0.70), (-0.150, 0.270, 0.80), (-0.130, 0.292, 0.875), (-0.070, 0.303, 0.912),
            (0.0, 0.306, 0.922)]
    radii = [0.0128, 0.0148, 0.0168, 0.0162, 0.0150, 0.0142, 0.0138, 0.0136, 0.0136]
    parts.append(bent("back_bow", half, radii, sides=10, sub=4))
    legs_at_hoop += [Vector((-0.121, 0.216, 0.20)), Vector((0.121, 0.216, 0.20))]
    # inner back loop
    inner = [(-0.074, 0.188, 0.444), (-0.079, 0.214, 0.56), (-0.090, 0.243, 0.67), (-0.076, 0.262, 0.742),
             (-0.036, 0.273, 0.776), (0.0, 0.275, 0.781)]
    parts.append(bent("back_loop", inner, [0.0115, 0.0112, 0.0108, 0.0105, 0.0105, 0.0105], sides=8, sub=2))
    # leg hoop: circle through the inner faces of the four legs at z = 0.20
    cy = sum(p.y for p in legs_at_hoop) / 4
    rr = sum(math.hypot(p.x, p.y - cy) for p in legs_at_hoop) / 4
    parts.append(M.torus("leg_hoop", rr - 0.0215, 0.0095, loc=(0, cy, 0.20), major_seg=32, minor_seg=6, mat=W))
    # small brass screw heads where the hoop meets each leg, and under the seat at the rear legs
    for p in legs_at_hoop:
        dvec = Vector((p.x, p.y - cy, 0)).normalized()
        parts.append(A.screw("hoop_screw", 0.0035, (p.x + dvec.x * 0.0150, p.y + dvec.y * 0.0150, 0.20), dvec,
                             "M_Brass_Aged", 30, segs=6))
    body = M.join(parts, "chair_body")
    M.finalize(smooth_angle=50.0)
    A.grain_uv(body, ratio=1.0)
    print(f"[{NAME}] tris={M.tri_count()}")
    return body


def main():
    args = M.main_guard()
    build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(32, bounces=4)
    floor = M.box("QA_floor", (4, 4, 0.02), loc=(0, 0, -0.01), mat="M_Wood_Floor", bevel=0)
    _ = floor
    M.render_preview(NAME, (0.95, -1.35, 1.05), (0.0, 0.02, 0.46), lens=40, res=(800, 900), samples=32,
                     world_strength=0.35, lights=A.STUDIO)
    floor = M.box("QA_floor", (4, 4, 0.02), loc=(0, 0, -0.01), mat="M_Wood_Floor", bevel=0)
    M.render_preview(NAME + "_2", (-0.95, 1.25, 1.25), (0.0, 0.05, 0.5), lens=40, res=(800, 900), samples=32,
                     world_strength=0.35, lights=A.STUDIO)


main()
