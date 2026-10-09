"""array_below.glb — the Array 30 m below the Resonance Gallery's glass floor (backdrop only), in WORLD coordinates.
Contract: docs/models/ch3.md §3 array_below (+ §1.1 shaft, §2 glass_floor view, §11 H1); results: docs/models/ch3_a.md.

  shaft_throat   rock bell mouth under the glass rim, r 1.62 at y -0.1 flaring to r 4.0 at y -1.2 (at least 50° from
                 vertical everywhere, so it never shows in the glass_floor view), with three brass hoops
  cavern         inward-facing low-poly rock dome r 14 from the throat (y -1.2) down to the floor at y -31; the brass
                 pylons, floor spokes and the central dais are part of it (one rock + one brass surface)
  ring_0..3      emissive rings (M_Emissive_Lumen) at y -30, radii 7.0 / 5.4 / 3.8 / 2.2 (outer -> inner), tube Ø0.45
  ring_sym_0..3  one flat quad per ring at y -29.70 facing +Y, UV u -> +X, v -> -Z (north up in the glass_floor view),
                 M_Shader_Quad; the code gives each the symbol of v_rings[r]
  array_center (0, -30, 0), rise_top (0, 2.6, 0)    empties for the rising-lights MultiMesh

    blender -b --factory-startup -P tools/blender/models/array_below.py [-- --no-render] [--shots=1,2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "array_below"
TRI_BUDGET, SURF_BUDGET = 6000, 10
ROCK, BRASS, LUMEN, SHQ = K.ROCK, K.BRASS, K.LUMEN, K.SHQ
RING_R = [7.0, 5.4, 3.8, 2.2]
RING_Y = -30.0
TUBE_R = 0.225
SYM_Y = -29.70
SYMS = [((-4.95, SYM_Y, 4.95), 1.5), ((3.82, SYM_Y, 3.82), 1.5), ((-2.69, SYM_Y, -2.69), 1.2), ((1.56, SYM_Y, -1.56), 1.2)]
THROAT = [(1.62, -0.10), (1.80, -0.17), (2.15, -0.30), (2.62, -0.48), (3.15, -0.72), (3.62, -0.98), (4.00, -1.20)]
CAVERN = [(4.00, -1.20), (6.2, -1.9), (8.8, -3.3), (11.2, -5.6), (13.0, -9.0), (14.0, -14.0), (14.0, -22.0),
          (13.6, -28.0), (12.6, -30.4), (11.5, -31.0)]


def throat():
    o = K.revolve("throat", THROAT, 0.0, 360.0, 40, ROCK)
    K._orient(o, inward=True)            # faces toward the axis / downward: seen from the shaft
    # flip so the visible side faces down/in (normal y < 0 on the flare)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    bm.to_mesh(o.data)
    bm.free()
    return K.part("shaft_throat", [o])


def hoops():
    """The throat's brass hoops and studs (merged into `cavern`'s brass surface to save a draw call)."""
    parts = []
    for (r, y) in ((2.15, -0.30), (2.90, -0.60), (3.62, -0.98)):
        band = K.revolve("hoop", [(r - 0.02, y - 0.035), (r + 0.03, y - 0.03), (r + 0.045, y + 0.01)], 0.0, 360.0, 40, BRASS)
        bm = bmesh.new()
        bm.from_mesh(band.data)
        for f in bm.faces:
            if f.normal.y > 0:
                f.normal_flip()
        bm.to_mesh(band.data)
        bm.free()
        A.hint(band, 50.0)
        parts.append(band)
    # hoop rivets (brass studs), 16 per hoop
    for (r, y) in ((2.15, -0.30), (2.90, -0.60), (3.62, -0.98)):
        for k in range(16):
            a = 360.0 * (k + 0.5) / 16
            p = K.polar(r + 0.01, a, y - 0.04)
            parts.append(K.rivet("stud", 0.03, tuple(p), normal=(0, -1, 0), mat=BRASS, segs=5))
    return parts


def cavern():
    rng = __import__("random").Random(3)
    o = K.revolve("cavern", CAVERN, 0.0, 360.0, 22, ROCK)
    # organic rock: jitter every vertex radially (keep the throat seam ring exact)
    for v in o.data.vertices:
        r = math.hypot(v.co.x, v.co.z)
        if r < 4.05 and v.co.y > -1.3:
            continue
        j = rng.uniform(-0.55, 0.55)
        v.co.x *= (r + j) / r
        v.co.z *= (r + j) / r
        v.co.y += rng.uniform(-0.35, 0.35) if v.co.y > -30.5 else 0.0
    K._orient(o, inward=True)
    floor = K.revolve("cfloor", [(11.5, -31.0), (0.0, -31.0)], 0.0, 360.0, 22, ROCK)
    bm = bmesh.new()
    bm.from_mesh(floor.data)
    for f in bm.faces:
        if f.normal.y < 0:
            f.normal_flip()
    bm.to_mesh(floor.data)
    bm.free()
    parts = [o, floor]
    # brass pylons under each ring (tapered, with a saddle), floor spokes and the central dais
    for ri, r in enumerate(RING_R):
        n = 8 if r > 5 else 6
        for k in range(n):
            a = 360.0 * (k + 0.5 * (ri % 2)) / n
            p = K.polar(r, a, -31.0)
            parts.append(K.glathe("pylon", [(0.0, 0.0), (0.22, 0.0), (0.16, 0.12), (0.10, 0.62), (0.16, 0.78), (0.0, 0.80)],
                                  (p.x, -31.0, p.z), (0, 1, 0), 6, BRASS, smooth=40.0))
    for k in range(8):
        a = 22.5 + 45.0 * k
        p0, p1 = K.polar(1.2, a, -31.0), K.polar(7.4, a, -31.0)
        d = p1 - p0
        bx = K.gbox("spoke", (-d.length / 2, 0.0, -0.09), (d.length / 2, 0.14, 0.09), BRASS, 0.0)
        bx.data.transform(Matrix.Translation((p0 + p1) / 2) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, "Y"))
        parts.append(bx)
    parts.append(K.glathe("dais", [(0.0, 0.0), (1.2, 0.0), (1.2, 0.25), (0.9, 0.35), (0.5, 0.4), (0.45, 1.1), (0.25, 1.3),
                                   (0.0, 1.35)], (0.0, -31.0, 0.0), (0, 1, 0), 16, BRASS, smooth=40.0))
    return K.part("cavern", parts + hoops())


def ring(i):
    r = RING_R[i]
    seg = {0: 48, 1: 40, 2: 32, 3: 24}[i]
    o = M.torus(f"ring_{i}", r, TUBE_R, major_seg=seg, minor_seg=6, mat=LUMEN)
    o.data.transform(Matrix.Rotation(math.radians(-90), 4, "X"))      # torus in XZ (G-frame), axis +Y
    o.data.transform(Matrix.Translation((0.0, RING_Y, 0.0)))
    A.hint(o, 70.0)
    return K.part(f"ring_{i}", [o], pivot=(0.0, RING_Y, 0.0))


def ring_sym(i):
    c, s = SYMS[i]
    # u -> +X, v -> -Z, facing +Y (u x v = +X x -Z = +Y)
    q = K.quad(f"ring_sym_{i}", c, (1, 0, 0), (0, 0, -1), s, s, SHQ)
    return K.part(f"ring_sym_{i}", [q], pivot=c)


def build():
    M.reset_scene()
    K.ensure_materials()
    th = throat()
    cv = cavern()
    rings = [ring(i) for i in range(4)]
    syms = [ring_sym(i) for i in range(4)]
    K.empty("array_center", (0.0, -30.0, 0.0))
    K.empty("rise_top", (0.0, 2.6, 0.0))
    K.to_blender()
    A.finalize_uv()
    for q in syms:      # finalize_uv skips only M_Decal_*: restore the quads' 0..1 UVs
        uvl = q.data.uv_layers.active
        for li, (uu, vv) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
            uvl.data[li].uv = (uu, vv)
    return dict(throat=th, cavern=cv, rings=rings, syms=syms)


def verify(path):
    req = ["shaft_throat", "cavern", "array_center", "rise_top"] + [f"ring_{i}" for i in range(4)] + \
          [f"ring_sym_{i}" for i in range(4)]
    expect = {"array_center": (0.0, -30.0, 0.0), "rise_top": (0.0, 2.6, 0.0)}
    expect.update({f"ring_sym_{i}": SYMS[i][0] for i in range(4)})
    expect.update({f"ring_{i}": (0.0, RING_Y, 0.0) for i in range(4)})
    errs = K.V.verify_glb(path, required=req, identity=req, expect=expect, show=req)
    errs += K.facts(path, TRI_BUDGET, 11)
    # throat flare: every throat face at least 50° from vertical
    th = bpy.data.objects["shaft_throat"]
    worst = 90.0
    for p in th.data.polygons:
        if th.data.materials[p.material_index].name != ROCK:
            continue
        n = p.normal            # Blender axes: z = Godot y
        ang = math.degrees(math.acos(min(1.0, abs(n.z))))      # angle between the normal and vertical
        worst = min(worst, 90.0 - ang)                         # surface angle from vertical
    print(f"{K.TAG} shaft_throat: steepest face is {worst:.1f}° from vertical (contract: >= 50°)")
    if worst < 50.0:
        errs.append("shaft_throat steeper than 50° from vertical")
    # ring symbol quads: UV corners and their facing
    for i in range(4):
        q = bpy.data.objects[f"ring_sym_{i}"]
        uv = [tuple(round(c, 3) for c in d.uv) for d in q.data.uv_layers.active.data]
        print(f"{K.TAG} ring_sym_{i}: UV {uv}, normal {tuple(round(c, 3) for c in q.data.polygons[0].normal)} (Blender +Z = up)")
    return errs


def qa(parts, args):
    K.qa_begin(bounces=4)
    target = [1, 3, 2, 4]                                     # DRUM_TARGET / v_rings seed 0: moon, triangle, star, circle
    for i, q in enumerate(parts["syms"]):
        img = os.path.join(S.DECALS3, S.DECAL_FILE[S.DRUM_ORDER[target[i]]])
        K.override(q, K.image_emitter(f"qa_sym_{i}", img, strength=3.0, tint=(0.8, 0.96, 1.0)))
    lum = K.glow("qa_lumen", "CFF6FF", 4.0)
    for r in parts["rings"]:
        K.override(r, lum)
    K.light("array_up", "SPOT", (0.0, -29.0, 0.0), 60000.0, "CFF6FF", radius=1.0, target=(0.0, 5.0, 0.0), spot_deg=40)
    K.light("floor_glow", "POINT", (0.0, -28.0, 0.0), 4000.0, "CFF6FF", radius=2.0)
    if K.want(args, "1"):          # hero: the Array from above at an angle (inside the cavern)
        K.shoot(NAME, (0.0, -16.0, 11.0), (0.0, -30.0, -0.5), vfov=60)
    if K.want(args, "2"):          # the glass_floor view without the glass (gallery QA shows it through the glass)
        K.shoot(NAME + "_2", (0.0, 1.55, 1.1), (0.0, -30.0, -0.6), vfov=32)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
