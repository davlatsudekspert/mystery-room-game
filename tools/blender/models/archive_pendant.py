"""archive_pendant.glb — industrial enamel pendant for Records Archive B (six of them hang in the hall).

A wide conical shade (dia 0.42), dark-green enamel outside / white enamel inside with a rolled, chipped
iron rim, on a 0.55 m brass rod with a ball swivel under a brass ceiling rose.

Origin = the ceiling mount point (top of the rose); everything hangs down along Godot -y; the shade rim is
at y = -0.75. Place at the ceiling points in docs/models/ch2.md §1 (y = 3.6), yaw 0.
Parts: `bulb` (own object, M_Emissive_Warm, origin at the bulb centre, toggled by code) and an empty
`light_origin` at the bulb centre (0, -0.724, 0). The rest is the static `pendant_body`.

    blender -b --factory-startup -P tools/blender/models/archive_pendant.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G  # noqa: E402

NAME = "archive_pendant"
NECK_Y = -0.652      # where the shade neck meets the gallery
RIM_Y = -0.75
RIM_R = 0.21
BULB_Y = -0.724


def shade():
    """Shade shell as one closed loop (outer top -> rim bead -> inner), revolved."""
    outer = []
    n = 6
    for i in range(n + 1):
        t = i / n
        r = 0.046 + (RIM_R - 0.004 - 0.046) * t
        # slightly convex cone: sag toward the rim
        y = NECK_Y - (RIM_Y + 0.004 - NECK_Y) * -1 * (t ** 1.18)
        outer.append((r, y))
    th = 0.0028
    inner = []
    for i, (r, y) in enumerate(outer):
        p0 = outer[max(0, i - 1)]
        p1 = outer[min(len(outer) - 1, i + 1)]
        dr, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dr, dy)
        nr, ny = -dy / ln, dr / ln        # outward (up/out) normal of a top->bottom profile
        inner.append((r - nr * th, y - ny * th))
    rr = 0.0045
    cx, cy = RIM_R - rr * 0.6, RIM_Y + rr
    bead = A.arc(cx, cy, rr, 30, -210, 4)
    loop = outer + bead[1:-1] + list(reversed(inner))
    o = A.lathe_loop("shade", loop, segments=28, mat="M_Enamel_Green")

    def pick(c, nrm, cur):
        radial = M.Vector((c.x, c.y, 0.0))
        rad = radial.length
        if rad < 1e-6:
            return None
        radial.normalize()
        if rad > RIM_R - 0.011 and c.z < RIM_Y + 0.012:          # rolled rim: chipped iron
            return "M_Steel_Dark"
        return "M_Enamel_White" if (nrm.dot(radial) * 0.6 + nrm.z * 0.8) < -0.05 else "M_Enamel_Green"
    A.mat_by_face(o, pick)
    return A.hint(o, 50)


def build():
    M.reset_scene()
    C.ensure_materials()
    parts = []
    B = "M_Brass_Aged"
    # ceiling rose (Blender z = Godot y; built along -Z)
    parts.append(A.lathe_s("rose", [(0.016, -0.040), (0.024, -0.035), (0.046, -0.024), (0.062, -0.010),
                                     (0.066, -0.003), (0.066, 0.0)], segments=20, mat=B))
    for i, a in enumerate((0.4, 0.4 + math.pi)):
        n = M.Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, -0.87)).normalized()
        parts.append(A.screw(f"rose_screw{i}", 0.004, (math.cos(a) * 0.046, math.sin(a) * 0.046, -0.025), n, B, 30, segs=6))
    # ball swivel + collar
    parts.append(A.sphere_s("swivel", 0.016, loc=(0, 0, -0.052), segments=10, rings=6, mat=B))
    parts.append(A.lathe_s("swivel_collar", [(0.0, -0.075), (0.012, -0.075), (0.0135, -0.071), (0.0135, -0.062),
                                              (0.011, -0.058)], segments=10, mat=B))
    # rod 0.55 m (from the swivel collar to the gallery)
    rod_top, rod_bot = -0.072, NECK_Y + 0.060
    parts.append(A.cyl_s("rod", 0.0085, rod_top - rod_bot, loc=(0, 0, (rod_top + rod_bot) / 2), verts=12, mat=B, bevel=0.0))
    # gallery / fitter: cast cup with a knurled ring that clamps the shade neck
    parts.append(A.lathe_s("gallery", [(0.0, NECK_Y + 0.064), (0.012, NECK_Y + 0.064), (0.014, NECK_Y + 0.058),
                                        (0.030, NECK_Y + 0.046), (0.036, NECK_Y + 0.034), (0.037, NECK_Y + 0.016),
                                        (0.040, NECK_Y + 0.012), (0.040, NECK_Y + 0.004), (0.049, NECK_Y + 0.002),
                                        (0.050, NECK_Y - 0.004), (0.044, NECK_Y - 0.006), (0.0, NECK_Y - 0.006)],
                           segments=14, mat=B))
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        d = M.Vector((math.cos(a), math.sin(a), 0))
        ts = M.lathe(f"thumb{i}", [(0.0, 0.0), (0.0025, 0.0), (0.0025, 0.008), (0.0055, 0.009), (0.0058, 0.015),
                                   (0.0048, 0.017), (0.0, 0.017)], segments=6, mat=B)
        q = M.Vector((0, 0, 1)).rotation_difference(d)
        ts.data.transform(q.to_matrix().to_4x4())
        ts.location = (d.x * 0.036, d.y * 0.036, NECK_Y + 0.026)
        parts.append(A.hint(ts))
    # bakelite socket + brass screw base inside the shade
    parts.append(A.lathe_s("socket", [(0.0, -0.688), (0.0175, -0.688), (0.020, -0.684), (0.020, -0.662),
                                       (0.024, -0.658)], segments=14, mat="M_Bakelite"))
    base = [(0.0, -0.7005)]
    for k in range(3):
        z = -0.700 + k * 0.004
        base += [(0.0126, z), (0.0138, z + 0.002)]
    base += [(0.0133, -0.688), (0.0, -0.688)]
    parts.append(A.lathe_s("bulb_base", base, segments=10, mat=B))
    parts.append(shade())
    A.presmooth(parts)
    body = M.join(parts, "pendant_body")
    # bulb glass (pear), origin at its centre
    bulb = A.lathe_s("bulb", [(0.0, -0.748), (0.0093, -0.7458), (0.0170, -0.7410), (0.0221, -0.7332), (0.0240, -0.724),
                              (0.0221, -0.7148), (0.0170, -0.7070), (0.0125, -0.7025), (0.0125, -0.7000)],
                     segments=14, mat="M_Emissive_Warm")
    A.presmooth([bulb])
    M.set_origin(bulb, G(0, BULB_Y, 0))
    M.empty("light_origin", G(0, BULB_Y, 0))
    A.finalize_uv()
    C.report(NAME)
    return body, bulb


def main():
    args = M.main_guard()
    body, bulb = build()
    path = C.export(NAME)
    C.verify_glb(path, required=["bulb", "light_origin", "pendant_body"], identity=["bulb", "light_origin"], budget=2500,
                 expect={"bulb": (0, BULB_Y, 0), "light_origin": (0, BULB_Y, 0)}, show=["bulb", "light_origin"])
    if "--no-render" in args:
        return
    C.qa_begin()
    ceil = M.box("qa_ceiling", (1.4, 1.4, 0.02), loc=(0, 0, 0.01), mat="M_Ceiling", bevel=0)
    _ = ceil
    # hero: 3/4 from below, studio light (bulb on)
    M.render_preview(f"{C.QA_SUB}/{NAME}", (0.62, -0.78, -1.05), (0, 0, -0.62), lens=50, res=(800, 800), samples=32,
                     world_strength=0.6, lights=[((1.0, -1.2, 1.4), 900, "FFE2C0", 1.5), ((-1.4, -0.6, 0.8), 300, "BFD4FF", 2.0),
                                                 ((0.2, 1.4, 1.6), 600, "FFFFFF", 1.0)])
    # from a standing player's eye, looking up into the shade
    M.render_preview(f"{C.QA_SUB}/{NAME}_2", (0.55, -0.70, -1.95), (0, 0, -0.70), lens=50, res=(800, 640), samples=32,
                     world_strength=0.25, lights=A.STUDIO)


main()
