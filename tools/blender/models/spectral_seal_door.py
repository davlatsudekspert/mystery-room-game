"""spectral_seal_door.glb — the camp door (E3 spectral seal): a sliding riveted steel leaf with three light receptors,
on the south face of the camp wall at (6.1, 0, -1.05), yaw 0 (front +Z faces the prism bench).
Contract: docs/models/ch3.md §6 spectral_seal_door (+ §1.3 receptors 0..2, §2 seal / prisms, §11 E3
seal_receptor.gdshader); results: docs/models/ch3_d.md.

Origin = floor level at the centre of the opening, on the wall face (z = 0); the wall is behind (z < 0).
Opening x -0.50 .. 0.50, y 0 .. 2.10.

  door_frame      (static) painted angle architrave round the opening (12 mm proud) with rivets; the dark steel top
                  track x -1.60 .. 0.60 (y 2.22 .. 2.32, z 0.02 .. 0.12) on five wall brackets with end stops; a
                  floor guide bracket west of the opening
  IA_camp_door    the leaf 1.04 x 2.12 x 0.06 at z 0.02 .. 0.08 (x -0.52 .. 0.52, y 0.015 .. 2.135): painted steel
                  slab with riveted straps and a Z brace, two hanger plates with wheels in the track, a brass pull,
                  the brass receptor plate with three bezels; pivot (0, 0, 0.05) = floor level under the leaf centre;
                  open = slide -1.05 along local X (parks in front of the wall, west of the doorway)
    receptor_<i>  (children, i = 0..2 west -> east) discs r 0.08 at (-0.30 + 0.30 i, 1.15, 0.085) facing +Z,
                  UV 0..1 over the bounding square (u -> +X, v -> +Y), M_Shader_Quad (seal_receptor shader)

    blender -b --factory-startup -P tools/blender/models/spectral_seal_door.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "spectral_seal_door"
TRI_BUDGET, SURF_BUDGET = 5000, 7
PAINT, STEEL, BRASS, SHQ = D.PAINT, D.STEEL, D.BRASS, D.SHQ

OPEN_W, OPEN_H = 1.00, 2.10
LEAF_W, LEAF_H = 1.04, 2.12
LEAF_Y0 = 0.015
LEAF_Z0, LEAF_Z1 = 0.02, 0.08
SLAB_Z1 = 0.062                                # the slab face; straps and plates stand on it up to LEAF_Z1
LEAF_PIVOT = (0.0, 0.0, 0.05)
SLIDE = -1.05
REC_X = [-0.30, 0.0, 0.30]
REC_Y, REC_Z, REC_R = 1.15, 0.085, 0.08
RAIL_X0, RAIL_X1 = -1.60, 0.60
RAIL_Y0, RAIL_Y1 = 2.22, 2.32
RAIL_Z0, RAIL_Z1 = 0.02, 0.12
HANGER_X = (-0.34, 0.34)
WHEEL_Y = 2.256


def rivets(prefix, pts, z, r=0.0055, mat=PAINT):
    return [K.rivet(prefix, r, (x, y, z), segs=6, mat=mat) for (x, y) in pts]


def along(x0, x1, step):
    n = max(1, int(round((x1 - x0) / step)))
    return [x0 + (x1 - x0) * i / n for i in range(n + 1)]


# ====================================================================== static frame
def frame():
    st, pt = [], []
    # architrave: painted angle round the opening (jambs + head), 0.06 wide, 12 mm proud of the wall
    ax, hy = OPEN_W / 2, OPEN_H
    pt.append(D.box("jamb_w", (-ax - 0.06, 0.0, 0.0), (-ax, hy + 0.06, 0.012), PAINT, 0.002))
    pt.append(D.box("jamb_e", (ax, 0.0, 0.0), (ax + 0.06, hy + 0.06, 0.012), PAINT, 0.002))
    pt.append(D.box("head", (-ax - 0.06, hy, 0.0), (ax + 0.06, hy + 0.06, 0.012), PAINT, 0.002))
    pts = [(-ax - 0.03, y) for y in along(0.18, hy - 0.12, 0.30)] + [(ax + 0.03, y) for y in along(0.18, hy - 0.12, 0.30)]
    pts += [(x, hy + 0.03) for x in along(-ax + 0.10, ax - 0.10, 0.30)]
    pt += rivets("arv", pts, 0.012)
    # top track: an inverted channel open underneath (the hanger plates pass through z 0.044 .. 0.056)
    st.append(D.box("tr_top", (RAIL_X0, RAIL_Y1 - 0.02, RAIL_Z0), (RAIL_X1, RAIL_Y1, RAIL_Z1), STEEL, 0.0))
    st.append(D.box("tr_back", (RAIL_X0, RAIL_Y0, RAIL_Z0), (RAIL_X1, RAIL_Y1, RAIL_Z0 + 0.01), STEEL, 0.0))
    st.append(D.box("tr_front", (RAIL_X0, RAIL_Y0, RAIL_Z1 - 0.01), (RAIL_X1, RAIL_Y1, RAIL_Z1), STEEL, 0.0))
    st.append(D.box("tr_lip_b", (RAIL_X0, RAIL_Y0, RAIL_Z0 + 0.01), (RAIL_X1, RAIL_Y0 + 0.01, 0.044), STEEL, 0.0))
    st.append(D.box("tr_lip_f", (RAIL_X0, RAIL_Y0, 0.056), (RAIL_X1, RAIL_Y0 + 0.01, RAIL_Z1 - 0.01), STEEL, 0.0))
    for x in (RAIL_X0, RAIL_X1 - 0.02):                           # end stops
        st.append(D.box("stop", (x, RAIL_Y0, RAIL_Z0), (x + 0.02, RAIL_Y1, RAIL_Z1), STEEL, 0.0))
    # wall brackets over the track (plate on the wall, arm over the track top, two bolts)
    for x in (-1.52, -1.00, -0.48, 0.04, 0.52):
        st.append(D.box("brk", (x - 0.035, 2.16, 0.0), (x + 0.035, 2.40, 0.012), STEEL, 0.0))
        st.append(D.box("brk_arm", (x - 0.025, RAIL_Y1, 0.0), (x + 0.025, RAIL_Y1 + 0.02, RAIL_Z1), STEEL, 0.0))
        st.append(D.box("brk_gus", (x - 0.004, RAIL_Y1 + 0.02, 0.012), (x + 0.004, 2.39, 0.06), STEEL, 0.0))
        st += [D.hexnut("brb", 0.007, (x, 2.185, 0.012), (0, 0, 1)), D.hexnut("brb", 0.007, (x, 2.375, 0.012), (0, 0, 1))]
    # floor guide bracket west of the opening (bears on the leaf's back face in both states)
    st.append(D.box("guide", (-0.70, 0.0, 0.0), (-0.60, 0.05, 0.018), STEEL, 0.0))
    st.append(K.gcyl("groller", 0.012, 0.012, 0.038, base=(-0.65, 0.0, 0.0), axis=(0, 1, 0), segments=8, mat=STEEL))
    return K.part("door_frame", st + pt)


# ====================================================================== the leaf
def leaf():
    pt, br = [], []
    x0, x1 = -LEAF_W / 2, LEAF_W / 2
    y0, y1 = LEAF_Y0, LEAF_Y0 + LEAF_H
    pt.append(D.box("slab", (x0, y0, LEAF_Z0), (x1, y1, SLAB_Z1), PAINT, 0.004))
    sw = 0.07                                                     # strap width
    straps = [((x0, y0), (x0 + sw, y1)), ((x1 - sw, y0), (x1, y1)), ((x0, y0), (x1, y0 + sw)), ((x0, y1 - sw), (x1, y1)),
              ((x0, 0.72), (x1, 0.72 + sw)), ((x0, 1.52), (x1, 1.52 + sw))]
    for (a, b) in straps:
        pt.append(D.box("strap", (a[0], a[1], SLAB_Z1), (b[0], b[1], LEAF_Z1), PAINT, 0.002))
    # Z brace across the lower panel (bottom-west to top-east), 0.07 wide
    bx0, bx1, by0, by1 = x0 + sw, x1 - sw, y0 + sw, 0.72
    d = Vector((bx1 - bx0, by1 - by0)).normalized()
    nrm = Vector((-d.y, d.x)) * 0.035
    poly = [(bx0 + nrm.x, by0 + nrm.y), (bx0 - nrm.x, by0 - nrm.y), (bx1 - nrm.x, by1 - nrm.y), (bx1 + nrm.x, by1 + nrm.y)]
    pt.append(K.plate("brace", [poly], LEAF_Z1 - SLAB_Z1, z0=SLAB_Z1, mat=PAINT, bevel=0.0))
    # rivets along the straps
    pts = []
    for yy in (y0 + sw / 2, y1 - sw / 2, 0.72 + sw / 2, 1.52 + sw / 2):
        pts += [(x, yy) for x in along(x0 + sw / 2, x1 - sw / 2, 0.14)]
    for xx in (x0 + sw / 2, x1 - sw / 2):
        pts += [(xx, y) for y in along(y0 + sw + 0.07, 0.72 - 0.07, 0.14)]
        pts += [(xx, y) for y in along(0.79 + 0.07, 1.52 - 0.07, 0.14)]
        pts += [(xx, y) for y in along(1.59 + 0.07, y1 - sw - 0.07, 0.14)]
    for t in (0.2, 0.4, 0.6, 0.8):
        pts.append((bx0 + (bx1 - bx0) * t, by0 + (by1 - by0) * t))
    pt += rivets("rv", pts, LEAF_Z1)
    # hangers: plate up into the track, axle, two wheels (one each side of the plate)
    for hx in HANGER_X:
        pt.append(D.box("hanger", (hx - 0.012, y1 - 0.02, 0.046), (hx + 0.012, WHEEL_Y + 0.03, 0.054), PAINT, 0.0))
        pt.append(K.gcyl("axle", 0.006, 0.028, 0.072, base=(hx, WHEEL_Y, 0.0), axis=(0, 0, 1), segments=6, mat=PAINT))
        pt.append(K.gcyl("wheel", 0.025, 0.030, 0.044, base=(hx, WHEEL_Y, 0.0), axis=(0, 0, 1), segments=12, mat=PAINT))
        pt.append(K.gcyl("wheel", 0.025, 0.056, 0.070, base=(hx, WHEEL_Y, 0.0), axis=(0, 0, 1), segments=12, mat=PAINT))
    # brass pull near the east edge
    hx, hy0, hy1 = 0.43, 0.92, 1.24
    for hy in (hy0, hy1):
        br.append(K.gcyl("pstub", 0.009, LEAF_Z1, LEAF_Z1 + 0.035, base=(hx, hy, 0.0), axis=(0, 0, 1), segments=8,
                         mat=BRASS))
    br.append(K.gcyl("pbar", 0.010, hy0 - 0.012, hy1 + 0.012, base=(hx, 0.0, LEAF_Z1 + 0.038), axis=(0, 1, 0),
                     segments=10, mat=BRASS, chamfer=0.003))
    # the brass receptor plate and bezels
    br.append(K.plate("rplate", [L.rounded_rect(0.94, 0.26, 0.03, 3)], 0.006, z0=SLAB_Z1, mat=BRASS, bevel=0.001,
                      loc=(0.0, REC_Y, 0.0)))
    for (sx, sy) in ((-0.44, -0.10), (0.44, -0.10), (-0.44, 0.10), (0.44, 0.10)):
        br.append(K.rivet("rps", 0.0045, (sx, REC_Y + sy, SLAB_Z1 + 0.006), segs=6, mat=BRASS))
    for x in REC_X:
        br.append(D.ring("bezel", REC_R, REC_R + 0.018, SLAB_Z1 + 0.006, 0.090, (x, REC_Y, 0.0), (0, 0, 1), 24, BRASS,
                         chamfer=0.003))
        br.append(D.ring("bezel_in", REC_R - 0.004, REC_R + 0.0005, REC_Z - 0.0015, 0.090, (x, REC_Y, 0.0), (0, 0, 1),
                         24, BRASS))
    return K.part("IA_camp_door", pt + br, pivot=LEAF_PIVOT)


def receptors():
    out = []
    for i, x in enumerate(REC_X):
        o = D.disc_uv(f"receptor_{i}", REC_R, (x, REC_Y, REC_Z), SHQ, segs=32)
        M.set_origin(o, (x, REC_Y, REC_Z))
        out.append(o)
    return out


def build():
    M.reset_scene()
    D.ensure_materials()
    out = dict(frame=frame(), leaf=leaf(), receptors=receptors())
    K.to_blender()
    D.finalize()
    for r in out["receptors"]:
        K.parent(r, out["leaf"])
    return out


def verify(path):
    req = ["door_frame", "IA_camp_door", "receptor_0", "receptor_1", "receptor_2"]
    expect = {"door_frame": (0, 0, 0), "IA_camp_door": LEAF_PIVOT}
    parents = {"door_frame": None, "IA_camp_door": None}
    for i, x in enumerate(REC_X):
        expect[f"receptor_{i}"] = (x, REC_Y, REC_Z)
        parents[f"receptor_{i}"] = "IA_camp_door"
    errs = D.verify(path, required=req, identity=req, expect=expect, parents=parents, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET)
    for n in ("door_frame", "IA_camp_door"):
        lo, hi = D.bounds([n])
        print(f"{D.TAG} {n:14s} bounds {lo} .. {hi}")
    o = bpy.data.objects["receptor_0"]
    uvs = [d.uv for d in o.data.uv_layers.active.data]
    print(f"{D.TAG} receptor_0 UV range u {min(u.x for u in uvs):.3f}..{max(u.x for u in uvs):.3f} "
          f"v {min(u.y for u in uvs):.3f}..{max(u.y for u in uvs):.3f}")
    # world receptor points (§1.3): (5.8 / 6.1 / 6.4, 1.15, -0.97)
    for i, x in enumerate(REC_X):
        print(f"{D.TAG} receptor_{i} world {tuple(round(c, 3) for c in D.world_point(D.SEAL_POS, 0.0, (x, REC_Y, REC_Z)))}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, open_door=False):
    parts["leaf"].matrix_basis = REST["leaf"].copy()
    M.refresh()
    if open_door:
        K.pose_slide(parts["leaf"], (SLIDE, 0.0, 0.0))


def wall_clearance(parts, label):
    walls = [o for o in bpy.data.objects if o.name.startswith("qa_sn_camp_walls") and o.type == "MESH"]
    if not walls:
        print(f"{D.TAG} clearance {label}: camp_walls not imported")
        return
    n, d = D.mesh_clearance([parts["leaf"]], walls)
    print(f"{D.TAG} leaf vs camp_walls ({label}): {n} intersecting triangle pairs, nearest vertex {d * 100:.1f} cm")
    n, d = D.mesh_clearance([parts["frame"]], walls)
    print(f"{D.TAG} door_frame vs camp_walls: {n} intersecting triangle pairs, nearest vertex {d * 100:.1f} cm")


def qa(parts, args):
    D.qa_begin()
    REST["leaf"] = parts["leaf"].matrix_basis.copy()
    roots = D.roots()
    D.place(roots, D.SEAL_POS, 0.0, name="qa_place_seal")
    D.room(extra=[("prism_bench", D.BENCH_POS, 0.0, "qa_pb_")])
    start = [D.preview_material(f"qa_rec{i}", f"receptor_{i}.png", emissive=True, strength=1.6) for i in range(3)]
    solved = [D.preview_material(f"qa_rec{i}s", f"receptor_{i}_solved.png", emissive=True, strength=1.6) for i in range(3)]

    def recs(mats):
        olds = []
        for r, m in zip(parts["receptors"], mats):
            olds.append(K.override(r, m) if m is not None else None)
        return olds

    def restore(olds):
        for r, old in zip(parts["receptors"], olds):
            if old is not None:
                K.restore(r, old)

    pose(parts)
    wall_clearance(parts, "closed")
    pose(parts, True)
    wall_clearance(parts, "open")
    pose(parts)
    SEAL_CAM, SEAL_TGT = (6.1, 1.3, -0.3), (6.1, 1.15, -0.97)
    # 1 the seal view, closed, receptors at the start state (only receptor 2 lit)
    if K.want(args, "1"):
        pose(parts)
        olds = recs(start)
        D.lights(SEAL_CAM, fill=5.0, prism_lamp=True)
        D.shoot(NAME, SEAL_CAM, SEAL_TGT, 44)
        restore(olds)
    # 2 the seal view, solved: receptors accepted, the leaf slid -1.05 (the camp beyond)
    if K.want(args, "2"):
        pose(parts, True)
        olds = recs(solved)
        D.lights(SEAL_CAM, fill=5.0, camp=True, prism_lamp=True)
        D.shoot(NAME + "_2", SEAL_CAM, SEAL_TGT, 44)
        restore(olds)
    # 3 hero: three-quarter from the east, closed (track, brackets, straps, pull)
    if K.want(args, "3"):
        pose(parts)
        olds = recs(start)
        cam = (7.6, 1.7, 1.4)
        D.lights(cam, fill=10.0, prism_lamp=True)
        D.shoot(NAME + "_3", cam, (6.0, 1.15, -1.0), 50)
        restore(olds)
    # 4 the nursery_w root view, door open (the leaf parked west of the doorway, the camp lit)
    if K.want(args, "4"):
        pose(parts, True)
        olds = recs(solved)
        D.lights(camp=True)
        D.shoot(NAME + "_4", (12.2, 1.65, 2.9), (6.4, 1.2, -0.8), 62)
        restore(olds)
    # 5 close-up of receptor 2 and its bezel at the start state
    if K.want(args, "5"):
        pose(parts)
        olds = recs(start)
        cam = (6.62, 1.32, -0.62)
        D.lights(cam, fill=3.0, prism_lamp=True)
        D.shoot(NAME + "_5", cam, (6.38, 1.14, -0.965), 34)
        restore(olds)
    # 6 the prisms view (§2) with the bench if it exists: the seal 1.45 m behind the prisms
    if K.want(args, "6"):
        pose(parts)
        olds = recs(start)
        D.lights((6.1, 1.75, 1.65), fill=6.0, prism_lamp=True)
        D.shoot(NAME + "_6", (6.1, 1.75, 1.65), (6.1, 1.0, -0.55), 56)
        restore(olds)


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
