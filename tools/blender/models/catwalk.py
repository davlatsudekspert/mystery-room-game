"""catwalk.glb — the steel catwalk from the bridge gate to the island (Chapter 4, group A): a 1.2 m wide chequer deck at
y = 2.5 from z 11.95 to 3.0, four 0.9 x 0.9 holes over the ring tracks (z = 10.5, 8.5, 6.5, 4.5) closed by hinged lids,
two girders, trestles standing in the gaps BETWEEN the ring tracks (z = 11.4, 9.5, 7.5, 5.5), brass handrails.
Contract: docs/models/ch4.md section 3 catwalk; results: docs/models/ch4_a.md.

Built in WORLD coordinates. Mesh objects:
  catwalk_deck   M_Chequer    the deck slab with the four hole openings (and the two side strips beside them)
  catwalk_frame  M_Steel_Dark girders, cross ties, 4 trestles, hole coamings, hinge barrels, posts, toe boards, rivets
  catwalk_rail   M_Brass_Aged top + mid rails on both sides
  IA_hatch_1..4  M_Chequer    lid 0.98 x 0.98 x 0.03, origin at the NORTH hinge edge (0, 2.5, z_n - 0.49); closed =
                 identity (flat over the opening, top at y 2.53); open = -105 deg about +X (back-hinged, stands up
                 toward the north). z_n = 10.5 / 8.5 / 6.5 / 4.5 for the rings I / II / III / IV.

    blender -b --factory-startup -P tools/blender/models/catwalk.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, STEEL, BRASS, CHEQ  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "catwalk"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 8000, 7, 3
DECK = C.DECK_Y
HX = 0.6                                    # half width
Z_N, Z_S = 3.0, 11.95                       # south end (island) .. north? z grows toward the bridge: 3.0 island, 11.95 bridge
HATCH_Z = (10.5, 8.5, 6.5, 4.5)             # hatch n = 1..4
HOLE = 0.45                                 # half size of the openings
TRESTLE_Z = (11.4, 9.5, 7.5, 5.5)
POST_Z = [11.6 - 1.075 * k for k in range(9)]


def rod(a, b, r, mat, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    return K.gcyl("rod", r, 0.0, d.length, base=tuple(a), axis=tuple(d.normalized()), segments=segs, mat=mat, smooth=60.0)


def hole_bands():
    """z intervals of the full-width slab between the holes (low z = toward the island)."""
    edges = [Z_N]
    for z in sorted(HATCH_Z):
        edges += [z - HOLE, z + HOLE]
    edges.append(Z_S)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


def deck_parts():
    out = []
    for (a, b) in hole_bands():
        out.append(K.gbox("slab", (-HX, DECK - 0.06, a), (HX, DECK, b), CHEQ, 0.003))
    for z in HATCH_Z:                               # the two strips beside each opening
        for sx in (-1, 1):
            xa, xb = sorted((sx * HOLE, sx * HX))
            out.append(K.gbox("strip", (xa, DECK - 0.06, z - HOLE), (xb, DECK, z + HOLE), CHEQ, 0.003))
    return out


def frame_parts():
    out = []
    # two girders under the deck edges (clear of the holes), web + flanges
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.50, sx * 0.58))
        out.append(K.gbox("girder", (xa, 1.92, Z_N), (xb, DECK - 0.06, Z_S), STEEL, 0.003))
        fa, fb = sorted((sx * 0.46, sx * 0.62))
        out.append(K.gbox("gfl_t", (fa, DECK - 0.11, Z_N), (fb, DECK - 0.06, Z_S), STEEL, 0.003))
        out.append(K.gbox("gfl_b", (fa, 1.88, Z_N), (fb, 1.92, Z_S), STEEL, 0.003))
    # cross ties in the gaps between the holes
    for z in (11.4, 9.5, 7.5, 5.5, 3.4):
        out.append(K.gbox("tie", (-0.58, 2.22, z - 0.05), (0.58, DECK - 0.11, z + 0.05), STEEL, 0.003))
    # trestles: two posts, a foot plate each and an X brace, standing between the ring tracks
    for z in TRESTLE_Z:
        for sx in (-1, 1):
            out.append(K.gbox("tpost", (sx * 0.5 - 0.07, 0.0, z - 0.07), (sx * 0.5 + 0.07, 1.88, z + 0.07), STEEL, 0.006))
            out.append(K.gbox("tfoot", (sx * 0.5 - 0.17, 0.0, z - 0.17), (sx * 0.5 + 0.17, 0.05, z + 0.17), STEEL, 0.004))
        out.append(rod((-0.5, 0.25, z), (0.5, 1.7, z), 0.022, STEEL, 6))
        out.append(rod((0.5, 0.25, z), (-0.5, 1.7, z), 0.022, STEEL, 6))
    # hole coamings (a thin lip round each opening, flush with the deck top) and the hinge barrels on the island-side...
    for z in HATCH_Z:
        for (a, b) in (((-HOLE - 0.02, z - HOLE - 0.02), (HOLE + 0.02, z - HOLE)), ((-HOLE - 0.02, z + HOLE), (HOLE + 0.02, z + HOLE + 0.02))):
            out.append(K.gbox("coam", (a[0], DECK - 0.04, a[1]), (b[0], DECK + 0.004, b[1]), STEEL, 0.0))
        out.append(K.gcyl("hinge", 0.02, -0.46, 0.46, base=(0.0, DECK + 0.03, z + HOLE + 0.03), axis=(1, 0, 0), segments=8, mat=STEEL))
    # posts + toe boards on both sides
    for sx in (-1, 1):
        for z in POST_Z:
            out.append(K.gbox("post", (sx * HX - 0.03, DECK, z - 0.03), (sx * HX + 0.03, 3.5, z + 0.03), STEEL, 0.003))
        xa, xb = sorted((sx * HX - 0.015, sx * HX + 0.015))
        out.append(K.gbox("toe", (xa, DECK, Z_N), (xb, DECK + 0.1, Z_S), STEEL, 0.002))
    # rivets on the girders
    for sx in (-1, 1):
        for i in range(0, 22):
            z = Z_N + 0.2 + i * (Z_S - Z_N - 0.4) / 21.0
            out.append(K.rivet("rv", 0.016, (sx * 0.58 if sx > 0 else -0.58, 2.2, z), normal=(sx, 0, 0), mat=STEEL, segs=5))
    # island-end plate
    out.append(K.gbox("endplate", (-HX, 1.88, Z_N - 0.06), (HX, DECK, Z_N), STEEL, 0.004))
    return out


def rail_parts():
    out = []
    for sx in (-1, 1):
        x = sx * HX
        out.append(rod((x, 3.5, Z_S), (x, 3.5, Z_N), 0.028, BRASS, 10))
        out.append(rod((x, 3.0, Z_S), (x, 3.0, Z_N), 0.02, BRASS, 8))
    return out


def lid(n):
    z = HATCH_Z[n - 1]
    hz = z - 0.49                                    # the north hinge edge
    parts = [K.gbox("lid", (-0.49, 0.0, hz), (0.49, 0.03, hz + 0.98), CHEQ, 0.004)]
    parts.append(K.gbox("pull", (-0.10, 0.03, hz + 0.76), (0.10, 0.052, hz + 0.80), CHEQ, 0.006))
    for part in parts:
        part.data.transform(Matrix.Translation((0.0, DECK, 0.0)))
    return K.part(f"IA_hatch_{n}", parts, pivot=(0.0, DECK, hz))


def build():
    M.reset_scene()
    C.ensure_materials()
    deck = C.merge("catwalk_deck", deck_parts())
    frame = C.merge("catwalk_frame", frame_parts())
    rail = C.merge("catwalk_rail", rail_parts())
    lids = [lid(n) for n in (1, 2, 3, 4)]
    K.to_blender()
    C.finalize()
    return dict(deck=deck, frame=frame, rail=rail, lids=lids)


def verify(path):
    req = ["catwalk_deck", "catwalk_frame", "catwalk_rail"] + [f"IA_hatch_{n}" for n in (1, 2, 3, 4)]
    expect = {f"IA_hatch_{n}": (0.0, DECK, HATCH_Z[n - 1] - 0.49) for n in (1, 2, 3, 4)}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    lo, hi = C.bounds(["catwalk_deck", "catwalk_frame", "catwalk_rail"])
    print(f"{C.TAG} catwalk bounds {lo} .. {hi}")
    for n in (1, 2, 3, 4):
        lo, hi = C.bounds([f"IA_hatch_{n}"])
        print(f"{C.TAG} IA_hatch_{n} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa_tower_proxy(z):
    """A stand-in tower on ring z (QA only, Blender axes via the Godot min/max helper): ring, plinth, post, head, key."""
    qb = K.V._qbox
    return [qb("qa_ring", (-0.4, 0.0, z - 1.0), (0.4, 0.5, z + 1.0), "M_Steel_Dark"),
            qb("qa_plinth", (-0.35, 0.5, z - 0.35), (0.35, 0.68, z + 0.35), "M_Brass_Aged"),
            qb("qa_post", (-0.06, 0.68, z - 0.06), (0.06, 1.8, z + 0.06), "M_Brass_Aged"),
            qb("qa_head", (-0.18, 1.62, z - 0.18), (0.18, 2.0, z + 0.18), "M_Chrome"),
            qb("qa_key", (-0.04, 0.68, z + 0.15), (0.04, 0.72, z + 0.36), "M_Brass_Polished")]


def qa(args, parts):
    C.qa_begin()
    C.qa_floor_nonormal("catwalk_deck")
    C.qa_hall(shell=True, extra=[("bridge", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0)])
    C.qa_floor_nonormal("qa_sh_hall_floor")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))
    for z in HATCH_Z:
        qa_tower_proxy(z)
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):          # the catwalk view (R): from the bridge gate along the catwalk, one lid open
        K.pose_rot(parts["lids"][1], "x", -105.0)
        cam, tgt, fov = C.view("catwalk")
        lit(cam, 60.0, 0.18)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
        K.pose_rot(parts["lids"][1], "x", 105.0)
    if C.want(args, "2"):          # hatch_1: down through the open lid at the tower base
        K.pose_rot(parts["lids"][0], "x", -105.0)
        cam, tgt, fov = C.hatch_view(1)
        lit(cam, 80.0, 0.25)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
        K.pose_rot(parts["lids"][0], "x", 105.0)
    if C.want(args, "3"):          # from the island end, back toward the bridge (closed lids)
        cam, tgt, fov = (0.0, 3.6, 3.4), (0.0, 3.2, 12.0), 62
        lit(cam, 60.0, 0.18)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
