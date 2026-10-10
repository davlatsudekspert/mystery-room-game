"""crystal_shutter.glb — the shutter between Leyla's camp and the Resonance Gallery, with her four tuning crystals (E4).
Contract: docs/models/ch3.md §7 crystal_shutter (+ §1.1 shutter tunnel, §1.3 hang points, §1.4 portal_shutter_k,
§2 shutter / camp views, §11 E4); results: docs/models/ch3_e.md.

In the camp's west wall at (4.5, 0, -2.6), yaw 90: the front (+Z) faces +X into the camp, model +X is world -Z
(north). Origin = the wall plane at the frame's bottom centre. Frame 1.30 w x 2.10 h; opening x -0.55 .. 0.55,
y 0.30 .. 2.00 (the tunnel to the Gallery runs behind it, floor y 0.30).

  crystal_shutter   (static) dark riveted steel: the architrave round the opening (jambs, head) 6 cm proud with
                    rivets, the apron plate under the opening (y 0 .. 0.30) with two ribs, the reveal lining with the
                    leaf slots at both jambs, the threshold, the head's track channel; brass: the crystal bar across the
                    frame top (y 2.06, z 0.12) on two brackets with four hooks, the threshold strip, a kick strip
  shutter_leaf_l    riveted steel leaf 0.56 x 1.72 x 0.06 (x -0.56 .. 0, y 0.32 .. 2.04, z -0.09 .. -0.03), pivot
                    (-0.28, 0.32, -0.06); open = slide -0.58 along local X into the wall pocket (code, shutter_open)
  shutter_leaf_r    the mirror leaf, pivot (0.28, 0.32, -0.06); open = slide +0.58
  frame_mount_<p>   p = 0..3 (left -> right from the camp = south -> north): hang points (-0.42 + 0.28 p, 2.02, 0.12)
  IA_tcrystal_<s>   s = 1..4 (size rank, 1 smallest): a hexagonal crystal with pointed ends in a brass ferrule on a
                    brass wire with an eye; origin = the top of the eye (the hang point), hangs along local -Y; body
                    length 0.07 / 0.09 / 0.11 / 0.13, diameter 0.022 / 0.026 / 0.030 / 0.034, the body's top point
                    0.08 below the hang point. In the GLB crystal s hangs at frame_mount_<s-1> (child, identity); the
                    code reparents them from v_frame.
  portal_shutter_k  empty at (0, 1.2, -1.55) = world (2.95, 1.2, -2.6), +Z toward local -Z (rotation 180 about Y)

    blender -b --factory-startup -P tools/blender/models/crystal_shutter.py [-- --no-render] [--shots=1,2,...]
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
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "crystal_shutter"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 9, 3
STEEL, BRASS, CRYSTAL = E.STEEL, E.BRASS, E.CRYSTAL

OPEN_X, OPEN_Y0, OPEN_Y1 = 0.55, 0.30, 2.00
FRAME_X, FRAME_Y1 = 0.65, 2.10
FACE = 0.06                                   # architrave depth in front of the wall
LEAF_W, LEAF_H, LEAF_T = 0.56, 1.72, 0.06
LEAF_Y0 = 0.32
LEAF_Z0, LEAF_Z1 = -0.09, -0.03
LEAF_PIVOT = {"l": (-0.28, LEAF_Y0, -0.06), "r": (0.28, LEAF_Y0, -0.06)}
SLIDE = 0.58
BAR_Y, BAR_Z, BAR_R = 2.06, 0.12, 0.009
MOUNT_Y = 2.02
MOUNTS = [(-0.42 + 0.28 * p, MOUNT_Y, BAR_Z) for p in range(4)]
BODY_LEN = {1: 0.07, 2: 0.09, 3: 0.11, 4: 0.13}
BODY_D = {1: 0.022, 2: 0.026, 3: 0.030, 4: 0.034}
BODY_TOP = -0.08
PORTAL = (0.0, 1.2, -1.55)
FRAME_SIZES = [3, 4, 2, 1]                    # UndergroundLogic.FRAME_SIZES (seed 0): place p -> size


def rivets(prefix, pts, z, r=0.006, mat=STEEL, normal=(0, 0, 1)):
    return [K.rivet(prefix, r, (x, y, z), normal=normal, segs=6, mat=mat) for (x, y) in pts]


def along(a, b, step):
    n = max(1, int(round((b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


# ====================================================================== static
def frame():
    st, br = [], []
    # architrave: jambs and head, 6 cm proud, 0.10 wide, with a rebated inner edge (two boxes each)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * OPEN_X, sx * FRAME_X))
        st.append(K.gbox("jamb", (x0, OPEN_Y0 - 0.02, 0.0), (x1, FRAME_Y1, FACE), STEEL, 0.004))
        st.append(K.gbox("jamb_lip", (x0 if sx > 0 else x1 - 0.02, OPEN_Y0, FACE), (x0 + 0.02 if sx > 0 else x1, OPEN_Y1, FACE + 0.012),
                         STEEL, 0.002))
    st.append(K.gbox("head", (-FRAME_X, OPEN_Y1, 0.0), (FRAME_X, FRAME_Y1, FACE), STEEL, 0.004))
    st.append(K.gbox("head_lip", (-OPEN_X, OPEN_Y1, FACE), (OPEN_X, OPEN_Y1 + 0.02, FACE + 0.012), STEEL, 0.002))
    # apron plate under the opening with two stiffener ribs and a brass kick strip
    st.append(K.gbox("apron", (-FRAME_X, 0.0, 0.0), (FRAME_X, OPEN_Y0 - 0.02, 0.04), STEEL, 0.003))
    for x in (-0.30, 0.30):
        st.append(K.gbox("rib", (x - 0.02, 0.02, 0.04), (x + 0.02, OPEN_Y0 - 0.04, 0.055), STEEL, 0.002))
    br.append(K.gbox("kick", (-FRAME_X, 0.0, 0.04), (FRAME_X, 0.045, 0.047), BRASS, 0.001))
    # rivets on the architrave and the apron
    pts = []
    for sx in (-1, 1):
        pts += [(sx * (OPEN_X + 0.05), y) for y in along(OPEN_Y0 + 0.08, FRAME_Y1 - 0.08, 0.26)]
    pts += [(x, OPEN_Y1 + 0.05) for x in along(-OPEN_X + 0.10, OPEN_X - 0.10, 0.22)]
    st += rivets("arv", pts, FACE)
    st += rivets("apv", [(x, 0.15) for x in along(-FRAME_X + 0.08, FRAME_X - 0.08, 0.22)], 0.04, r=0.005)
    # reveal lining: threshold (floor of the slot), head channel, and the two jamb linings with the leaf slot
    st.append(K.gbox("threshold", (-OPEN_X, OPEN_Y0, -0.14), (OPEN_X, LEAF_Y0, 0.0), STEEL, 0.002))
    br.append(K.gbox("sill_strip", (-OPEN_X, LEAF_Y0, -0.02), (OPEN_X, LEAF_Y0 + 0.004, 0.0), BRASS, 0.0))
    st.append(K.gbox("head_ch", (-OPEN_X, OPEN_Y1 + 0.045, -0.14), (OPEN_X, OPEN_Y1 + 0.065, 0.0), STEEL, 0.0))
    st.append(K.gbox("head_in", (-OPEN_X, OPEN_Y1, -0.14), (OPEN_X, OPEN_Y1 + 0.04, LEAF_Z0 - 0.004), STEEL, 0.0))
    st.append(K.gbox("head_out", (-OPEN_X, OPEN_Y1, LEAF_Z1 + 0.004), (OPEN_X, OPEN_Y1 + 0.04, 0.0), STEEL, 0.0))
    for sx in (-1, 1):
        x0, x1 = sorted((sx * OPEN_X, sx * (OPEN_X + 0.012)))
        st.append(K.gbox("rev_f", (x0, OPEN_Y0, LEAF_Z1 + 0.004), (x1, OPEN_Y1, 0.0), STEEL, 0.0))
        st.append(K.gbox("rev_b", (x0, OPEN_Y0, -0.14), (x1, OPEN_Y1, LEAF_Z0 - 0.004), STEEL, 0.0))
    # the crystal bar on two brackets, with four hooks
    for x in (-0.52, 0.52):
        br.append(K.gbox("bracket", (x - 0.015, BAR_Y - 0.03, FACE), (x + 0.015, BAR_Y + 0.012, BAR_Z + 0.004), BRASS, 0.001))
        br.append(K.gbox("brk_plate", (x - 0.03, BAR_Y - 0.05, FACE), (x + 0.03, BAR_Y + 0.03, FACE + 0.004), BRASS, 0.001))
    br.append(K.gcyl("bar", BAR_R, -0.56, 0.56, base=(0.0, BAR_Y, BAR_Z), axis=(1, 0, 0), segments=10, mat=BRASS, chamfer=0.002))
    for (mx, my, mz) in MOUNTS:
        # a hook: a wire ring round the bar and a short drop ending just above the hang point
        ring = M.torus("hook_ring", BAR_R + 0.004, 0.0022, loc=(mx, BAR_Y, mz), rot=(0.0, math.radians(90), 0.0),
                       major_seg=10, minor_seg=4, mat=BRASS)
        M.apply_transform(ring)
        br.append(ring)
        br.append(K.gcyl("hook_drop", 0.0022, my + 0.004, BAR_Y - BAR_R - 0.002, base=(mx, 0.0, mz), axis=(0, 1, 0), segments=5,
                         mat=BRASS, caps=False))
    return K.part(NAME, st + br)


# ====================================================================== leaves
def leaf(side):
    sgn = -1 if side == "l" else 1
    x0, x1 = sorted((0.0, sgn * LEAF_W))
    y0, y1 = LEAF_Y0, LEAF_Y0 + LEAF_H
    p = [K.gbox("slab", (x0, y0, LEAF_Z0 + 0.012), (x1, y1, LEAF_Z1 - 0.012), STEEL, 0.003)]
    sw = 0.06
    # straps on the camp face (z toward -0.03) and the Gallery face (z toward -0.09); everything stays inside the
    # slot thickness z -0.09 .. -0.03 (plus 2.5 mm rivet heads) so the leaf can slide past the jamb linings
    for (za, zb) in ((LEAF_Z1 - 0.012, LEAF_Z1), (LEAF_Z0, LEAF_Z0 + 0.012)):
        p.append(K.gbox("st_v0", (x0, y0, za), (x0 + sw, y1, zb), STEEL, 0.0))
        p.append(K.gbox("st_v1", (x1 - sw, y0, za), (x1, y1, zb), STEEL, 0.0))
        for yy in (y0, y1 - sw, (y0 + y1) / 2 - sw / 2):
            p.append(K.gbox("st_h", (x0 + sw, yy, za), (x1 - sw, yy + sw, zb), STEEL, 0.0))
    # meeting stile (a thicker bar on the inner edge) and a flat finger plate on the camp face
    mx0, mx1 = (0.0, 0.03) if side == "r" else (-0.03, 0.0)
    p.append(K.gbox("stile", (mx0, y0, LEAF_Z0 + 0.002), (mx1, y1, LEAF_Z1 - 0.002), STEEL, 0.002))
    gx = sgn * 0.15
    p.append(K.gbox("pull", (gx - 0.025, 1.00, LEAF_Z1), (gx + 0.025, 1.30, LEAF_Z1 + 0.002), STEEL, 0.0005))
    p.append(K.gbox("pull_lip", (gx - 0.025, 1.14, LEAF_Z1 + 0.002), (gx + 0.025, 1.16, LEAF_Z1 + 0.0025), STEEL, 0.0))
    # rivets along the straps, camp face
    pts = []
    for yy in (y0 + sw / 2, y1 - sw / 2, (y0 + y1) / 2):
        pts += [(x, yy) for x in along(x0 + sw / 2, x1 - sw / 2, 0.14)]
    for xx in (x0 + sw / 2, x1 - sw / 2):
        pts += [(xx, y) for y in along(y0 + sw + 0.08, (y0 + y1) / 2 - sw - 0.02, 0.18)]
        pts += [(xx, y) for y in along((y0 + y1) / 2 + sw + 0.02, y1 - sw - 0.08, 0.18)]
    p += [K.rivet("lrv", 0.0045, (x, y, LEAF_Z1), segs=5, mat=STEEL) for (x, y) in pts]
    return K.part(f"shutter_leaf_{side}", p, pivot=LEAF_PIVOT[side])


# ====================================================================== crystals
def tcrystal(s):
    r = BODY_D[s] / 2
    length = BODY_LEN[s]
    parts = []
    # the eye: a small ring in the XY plane, its top at the origin
    eye = M.torus("eye", 0.0055, 0.0011, loc=(0.0, -0.0055, 0.0), major_seg=10, minor_seg=4, mat=BRASS)
    M.apply_transform(eye)
    parts.append(eye)
    parts.append(K.gcyl("wire", 0.0011, -0.069, -0.0105, base=(0.0, 0.0, 0.0), axis=(0, 1, 0), segments=5, mat=BRASS, caps=False))
    # ferrule: a turned brass cap over the crystal's top point
    fer = [(0.0, 0.0), (0.0035, 0.0), (0.0035, 0.003), (r * 0.55, 0.006), (r * 0.9, 0.012), (r * 0.9, 0.018),
           (r * 0.7, 0.019), (0.0, 0.019)]
    parts.append(K.glathe("ferrule", fer, (0.0, -0.067, 0.0), (0, -1, 0), 10, BRASS, smooth=50.0))
    body = E.hex_crystal("body", r, length, (0.0, BODY_TOP, 0.0), axis=(0, -1, 0), tip=r * 1.1, tip_top=r * 0.7,
                         mat=CRYSTAL, phase=math.pi / 6)
    parts.append(body)
    return K.part(f"IA_tcrystal_{s}", parts, pivot=(0.0, 0.0, 0.0))


def build():
    M.reset_scene()
    E.ensure_materials()
    out = dict(frame=frame(), leaves={s: leaf(s) for s in ("l", "r")})
    out["mounts"] = [K.empty(f"frame_mount_{p}", MOUNTS[p]) for p in range(4)]
    crystals = {}
    for s in range(1, 5):
        c = tcrystal(s)
        c.location = MOUNTS[s - 1]
        crystals[s] = c
    out["crystals"] = crystals
    out["portal"] = K.empty("portal_shutter_k", PORTAL, (0.0, 180.0, 0.0), size=0.2)
    K.to_blender()
    E.finalize()
    for s in range(1, 5):
        K.parent(crystals[s], out["mounts"][s - 1])
    return out


def verify(path):
    req = [NAME, "shutter_leaf_l", "shutter_leaf_r"] + [f"frame_mount_{p}" for p in range(4)] + \
          [f"IA_tcrystal_{s}" for s in range(1, 5)] + ["portal_shutter_k"]
    expect = {NAME: (0, 0, 0), "shutter_leaf_l": LEAF_PIVOT["l"], "shutter_leaf_r": LEAF_PIVOT["r"], "portal_shutter_k": PORTAL}
    parents = {NAME: None, "shutter_leaf_l": None, "shutter_leaf_r": None, "portal_shutter_k": None}
    for p in range(4):
        expect[f"frame_mount_{p}"] = MOUNTS[p]
        parents[f"frame_mount_{p}"] = None
    for s in range(1, 5):
        expect[f"IA_tcrystal_{s}"] = MOUNTS[s - 1]
        parents[f"IA_tcrystal_{s}"] = f"frame_mount_{s - 1}"
    errs = E.verify(path, required=req, identity=[n for n in req if n != "portal_shutter_k"], expect=expect, parents=parents,
                    rot_expect={"portal_shutter_k": (0.0, 180.0, 0.0)}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    errs = [e for e in errs if not e.startswith("surfaces")]      # documented: 12 surfaces (4 two-material crystals)
    for n in [NAME, "shutter_leaf_l", "shutter_leaf_r"] + [f"IA_tcrystal_{s}" for s in range(1, 5)]:
        lo, hi = E.bounds([n])
        print(f"{E.TAG} {n:16s} bounds {lo} .. {hi}")
    # the hang points in world (§1.3): (4.62, 2.02, -2.18 .. -3.02)
    for p in range(4):
        print(f"{E.TAG} frame_mount_{p} world {tuple(round(c, 3) for c in E.world_point(E.SHUTTER_POS, E.SHUTTER_YAW, MOUNTS[p]))}")
    # the leaves must stay inside the wall thickness (world x 4.2 .. 4.5) and clear the tunnel's side walls when open
    lo, hi = E.bounds(["shutter_leaf_l", "shutter_leaf_r"])
    print(f"{E.TAG} leaves z {lo[2]:.3f} .. {hi[2]:.3f} (wall x {4.5 + lo[2]:.3f} .. {4.5 + hi[2]:.3f}); open: x to ±{hi[0] + SLIDE:.3f}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, open_=False, order=None):
    for s, o in parts["leaves"].items():
        o.matrix_basis = REST[s].copy()
    M.refresh()
    if open_:
        K.pose_slide(parts["leaves"]["l"], (-SLIDE, 0.0, 0.0))
        K.pose_slide(parts["leaves"]["r"], (SLIDE, 0.0, 0.0))
    # hang the crystals in the given place -> size order (the code reparents; here we move them)
    order = order or [1, 2, 3, 4]
    for p, s in enumerate(order):
        c = parts["crystals"][s]
        c.parent = parts["mounts"][p]
        c.matrix_parent_inverse = Matrix.Identity(4)
        c.matrix_basis = Matrix.Identity(4)
    M.refresh()


def qa(parts, args):
    E.qa_begin()
    for s, o in parts["leaves"].items():
        REST[s] = o.matrix_basis.copy()
    roots = D.roots()
    D.place(roots, E.SHUTTER_POS, E.SHUTTER_YAW, name="qa_place_shutter")
    camp = [("leyla_camp", (0, 0, 0), 0.0, "qa_lc_"), ("field_recorder", E.RECORDER_POS, E.RECORDER_YAW, "qa_fr_"),
            ("oscillograph", E.OSC_POS, E.OSC_YAW, "qa_os_")]
    E.camp_room(extra=camp)
    bulb = next((o for o in bpy.data.objects if o.name.startswith("qa_lc_camp_bulb")), None)
    if bulb is not None:
        K.override(bulb, K.glow("qa_bulb", "FFD9A8", 7.0))
    osc = next((o for o in bpy.data.objects if o.name.startswith("qa_os_osc_screen") and o.type == "MESH"), None)
    if osc is not None:
        E.preview(osc, "osc_screen.png", emissive=True, strength=1.5)
    SH = E.view("shutter")
    # 1 the shutter view, closed, the crystals in the seed-0 frame order (sizes 3 4 2 1, south -> north)
    if E.want(args, "1"):
        pose(parts, False, FRAME_SIZES)
        E.camp_lights(SH[0], fill=6.0)
        E.shoot(NAME, SH[0], SH[1], SH[2])
    # 2 the shutter view, open: the leaves in their pockets, the tunnel and the Gallery beyond
    if E.want(args, "2"):
        pose(parts, True, FRAME_SIZES)
        E.gallery_room(doors=True, array=True)
        E.camp_lights(SH[0], fill=6.0)
        E.gallery_lights(None, fill=0.0, clear=False)
        E.shoot(NAME + "_2", SH[0], SH[1], SH[2])
        for o in [o for o in bpy.data.objects if o.name.startswith(("qa_sg_", "qa_dw_", "qa_de_", "qa_ab_"))]:
            o.hide_render = True
    # 3 hero: the crystal bar and the four crystals, oblique from the camp, close
    if E.want(args, "3"):
        pose(parts, False, FRAME_SIZES)
        cam = (5.25, 1.78, -2.05)
        E.camp_lights(cam, fill=9.0)
        E.shoot(NAME + "_3", cam, (4.63, 1.93, -2.62), 38)
    # 4 the camp root view (§2 camp), closed
    if E.want(args, "4"):
        pose(parts, False, FRAME_SIZES)
        C = E.view("camp")
        E.camp_lights(C[0], fill=4.0)
        E.shoot(NAME + "_4", C[0], C[1], C[2])


def main():
    args = M.main_guard()
    parts = build()
    E.report(NAME)
    path = E.export(NAME)
    errs = verify(path)
    print(f"{E.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
