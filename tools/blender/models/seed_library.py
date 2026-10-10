"""seed_library.glb — Leyla's seed library (E1): a walnut cabinet of 12 seed drawers on the Nursery's east wall at
(13.0, 0, -0.6), yaw -90 (front faces -X; front plane x = 12.55, z ∈ [-1.35, 0.15]).
Contract: docs/models/ch3.md §6 seed_library (+ §2 seed_library / seed_drawer, §10 echo_leyla_1998 pose_touch_<r>,
§11 E1 hex glyphs); results: docs/models/ch3_d.md.

  seed_library            (static) the carcass 1.50 w x 1.75 h x 0.45 d on a plinth: the face with 12 openings, the
                          bays behind them, brass frames round each opening, a velvet-topped ledge at waist height,
                          two panelled cupboard doors below, a cornice, and on the top a gallery board (velvet inset)
                          with turned walnut seed jars with brass lids
  IA_seed_drawer_<i>      i = 4 r + c: drawer 0.30 x 0.22 x 0.40 with a turned walnut knob and a turned cup inside
                          (one material); pivot = front-face centre (x_c, y_r, 0.45), x_c = (c - 1.5) 0.33,
                          y_r = 1.50 - 0.26 r; open = slide +0.24 along local +Z
    seed_mount_<i>        (child) (0, -0.05, -0.12) from the pivot: seed_crystal stands upright in the cup
  glyph_panel             ONE mesh of 12 quads 0.13 x 0.13 at (x_c, y_r + 0.02, 0.452); quad i covers the UV cell
                          u ∈ [c/4, (c+1)/4], v ∈ [(2-r)/3, (3-r)/3] (M_Shader_Quad, hex_glyph shader)
  glyph_open              one 0.13 x 0.13 quad, UV 0..1, M_Shader_Quad; child of IA_seed_drawer_0 at local
                          (0, 0.02, 0.0025): the code reparents it (local transform kept) to the open drawer
  echo_touch_mount_<c>    floor empties at (x_c + 0.40, 0, 0.87), 180° about +Y: Leyla's pose_touch_<r> puts her
                          left middle fingertip on drawer (r, c)'s front

    blender -b --factory-startup -P tools/blender/models/seed_library.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "seed_library"
TRI_BUDGET, SURF_BUDGET = 7000, 17
WALNUT, BRASS, VELVET, SHQ = D.WALNUT, D.BRASS, D.VELVET, D.SHQ

W, H, DEP = 1.50, 1.75, 0.45
FRONT = 0.45
PLINTH = 0.09
DRW_W, DRW_H, DRW_D = 0.30, 0.22, 0.40
OPEN_D = 0.24
GAP = 0.002                                   # clearance round each drawer front in its opening
GLYPH = 0.13
SEAT_DROP = 0.0088                            # seed_crystal collar bottom below its origin (ch3_g.md)
LEDGE = (0.815, 0.845, 0.505)                 # y0, y1, front z of the waist ledge


def xc(c):
    return (c - 1.5) * 0.33


def yr(r):
    return 1.50 - 0.26 * r


def drawer_index(r, c):
    return 4 * r + c


# ====================================================================== carcass
def carcass():
    wd, br, vl = [], [], []
    x0, x1 = -W / 2, W / 2
    # plinth (recessed), sides, back, top, bottom
    wd.append(D.box("plinth", (x0 + 0.02, 0.0, 0.02), (x1 - 0.02, PLINTH, FRONT - 0.03), WALNUT, 0.004))
    wd.append(D.box("side_l", (x0, PLINTH, 0.0), (x0 + 0.025, 1.70, FRONT), WALNUT, 0.003))
    wd.append(D.box("side_r", (x1 - 0.025, PLINTH, 0.0), (x1, 1.70, FRONT), WALNUT, 0.003))
    wd.append(D.box("back", (x0 + 0.02, PLINTH, 0.0), (x1 - 0.02, 1.70, 0.015), WALNUT, 0.0))
    # raised fields on the sides (seen in the room views)
    for sx in (-1, 1):
        for (ya, yb) in ((0.16, 0.78), (0.90, 1.62)):
            xs = sx * (W / 2 + 0.004)                       # 4 mm proud of the side
            wd.append(D.box("sfield", (min(xs, sx * W / 2), ya, 0.07), (max(xs, sx * W / 2), yb, FRONT - 0.07), WALNUT,
                            0.002))
    # cornice (stepped) and top
    wd.append(D.box("cor0", (x0 - 0.008, 1.70, -0.0), (x1 + 0.008, 1.72, FRONT + 0.012), WALNUT, 0.004))
    wd.append(D.box("cor1", (x0 - 0.016, 1.72, -0.0), (x1 + 0.016, 1.75, FRONT + 0.022), WALNUT, 0.005))
    # face plate with the 12 drawer openings (between the ledge and the cornice)
    fy0, fy1 = LEDGE[1], 1.70
    holes = []
    for r in range(3):
        for c in range(4):
            holes.append(L.rounded_rect(DRW_W + 2 * GAP, DRW_H + 2 * GAP, 0.004, 1, cx=xc(c), cy=yr(r) - (fy0 + fy1) / 2))
    face = K.plate("face", [L.rounded_rect(W - 0.05, fy1 - fy0, 0.001, 1)] + holes, 0.020, z0=FRONT - 0.020,
                   mat=WALNUT, bevel=0.0, loc=(0.0, (fy0 + fy1) / 2, 0.0), drop_bottom=True)
    wd.append(face)
    # bays behind the openings: shelves between rows and dividers between columns
    for r in range(4):
        y = (yr(0) + DRW_H / 2 + 0.03) if r == 0 else (yr(r - 1) - DRW_H / 2 - 0.02)
        y_a = y - 0.016
        wd.append(D.box("shelf", (-0.66, y_a, 0.015), (0.66, y_a + 0.016, FRONT - 0.02), WALNUT, 0.0))
    for c in range(5):
        x = -0.66 + 0.33 * c
        wd.append(D.box("div", (x - 0.012, yr(2) - DRW_H / 2 - 0.02, 0.015), (x + 0.012, yr(0) + DRW_H / 2 + 0.02,
                                                                              FRONT - 0.02), WALNUT, 0.0))
    # brass frames round each opening (proud of the face to z 0.454)
    for r in range(3):
        for c in range(4):
            fr = K.plate("bframe", [L.rounded_rect(DRW_W + 0.022, DRW_H + 0.022, 0.006, 2),
                                    L.rounded_rect(DRW_W + 2 * GAP, DRW_H + 2 * GAP, 0.003, 1)], 0.004, z0=FRONT,
                         mat=BRASS, bevel=0.0, loc=(xc(c), yr(r), 0.0), drop_bottom=True)
            br.append(fr)
    # waist ledge with a velvet inset (where the seeds were laid out)
    ly0, ly1, lz = LEDGE
    wd.append(D.box("ledge", (x0 + 0.01, ly0, 0.02), (x1 - 0.01, ly1, lz), WALNUT, 0.004))
    vl.append(D.box("ledge_velvet", (x0 + 0.06, ly1, FRONT - 0.13), (x1 - 0.06, ly1 + 0.003, lz - 0.02), VELVET, 0.001))
    br.append(D.box("ledge_edge", (x0 + 0.01, ly0 + 0.006, lz), (x1 - 0.01, ly0 + 0.012, lz + 0.003), BRASS, 0.0))
    # lower cupboard: two panelled doors (static) with brass pulls
    wd.append(D.box("lower", (x0 + 0.02, PLINTH, FRONT - 0.03), (x1 - 0.02, ly0, FRONT - 0.012), WALNUT, 0.0))
    for sx in (-1, 1):
        dx0, dx1 = (x0 + 0.03, -0.004) if sx < 0 else (0.004, x1 - 0.03)
        wd.append(D.box("ldoor", (dx0, PLINTH + 0.01, FRONT - 0.012), (dx1, ly0 - 0.012, FRONT), WALNUT, 0.003))
        wd.append(D.box("lfield", (dx0 + 0.06, PLINTH + 0.07, FRONT), (dx1 - 0.06, ly0 - 0.072, FRONT + 0.006), WALNUT,
                        0.003))
        hx = -0.045 if sx < 0 else 0.045
        br.append(K.glathe("lpull", [(0.0, 0.0), (0.012, 0.0), (0.008, 0.008), (0.006, 0.016), (0.013, 0.026),
                                     (0.010, 0.032), (0.0, 0.033)], (hx, 0.52, FRONT), (0, 0, 1), 8, BRASS,
                           smooth=50.0))
    # top gallery: back board with a velvet inset and turned walnut seed jars with brass lids
    wd.append(D.box("gal", (x0 + 0.03, 1.75, 0.0), (x1 - 0.03, 1.93, 0.03), WALNUT, 0.004))
    vl.append(D.box("gal_velvet", (x0 + 0.07, 1.775, 0.03), (x1 - 0.07, 1.905, 0.033), VELVET, 0.001))
    jars = [(-0.62, 0.050, 0.12), (-0.48, 0.042, 0.095), (-0.33, 0.055, 0.14), (-0.16, 0.040, 0.085),
            (0.02, 0.050, 0.125), (0.19, 0.044, 0.10), (0.36, 0.056, 0.135), (0.52, 0.040, 0.09), (0.63, 0.034, 0.075)]
    for k, (jx, jr, jh) in enumerate(jars):
        jz = 0.17 + 0.07 * ((k * 37) % 3) / 2
        base = (jx, 1.75, jz)
        wd.append(K.glathe("jar", [(jr * 0.82, 0.0), (jr, 0.012), (jr, jh * 0.80), (jr * 0.86, jh * 0.88)], base,
                           (0, 1, 0), 10, WALNUT, smooth=50.0, cap_top=False))
        br.append(K.glathe("lid", [(jr * 0.86, jh * 0.86), (jr * 1.04, jh * 0.88), (jr * 1.04, jh * 0.95),
                                   (jr * 0.40, jh * 0.97), (jr * 0.30, jh + 0.012), (0.0, jh + 0.016)], base, (0, 1, 0),
                           10, BRASS, smooth=50.0, cap_bottom=False))
    return K.part(NAME, wd + br + vl)


# ====================================================================== drawers
def drawer(r, c):
    x, y = xc(c), yr(r)
    i = drawer_index(r, c)
    zf = FRONT
    zb = FRONT - DRW_D
    hw, hh = DRW_W / 2, DRW_H / 2
    p = [D.box("front", (x - hw, y - hh, zf - 0.018), (x + hw, y + hh, zf), WALNUT, 0.003)]
    sy1 = y + 0.05                                       # sides lower than the front
    t = 0.010
    p.append(D.box("sl", (x - hw + 0.008, y - hh + 0.004, zb), (x - hw + 0.008 + t, sy1, zf - 0.018), WALNUT, 0.0))
    p.append(D.box("sr", (x + hw - 0.008 - t, y - hh + 0.004, zb), (x + hw - 0.008, sy1, zf - 0.018), WALNUT, 0.0))
    p.append(D.box("bk", (x - hw + 0.008, y - hh + 0.004, zb), (x + hw - 0.008, sy1, zb + t), WALNUT, 0.0))
    p.append(D.box("bt", (x - hw + 0.008, y - hh + 0.004, zb), (x + hw - 0.008, y - hh + 0.012, zf - 0.018), WALNUT, 0.0))
    # the turned cup (a goblet: foot, stem, cup with a shallow recess for the seed collar)
    seat = y - 0.05 - SEAT_DROP
    fl = y - hh + 0.012
    mz = zf - 0.12
    p.append(K.glathe("cup", [(0.020, fl), (0.020, fl + 0.006), (0.009, fl + 0.012), (0.008, seat - 0.016),
                              (0.015, seat - 0.006), (0.015, seat + 0.004), (0.0095, seat + 0.004), (0.0095, seat),
                              (0.0, seat)], (x, 0.0, mz), (0, 1, 0), 8, WALNUT, smooth=50.0, cap_bottom=False))
    # turned knob below the glyph
    p.append(K.glathe("knob", [(0.010, 0.0), (0.0065, 0.008), (0.0065, 0.013), (0.013, 0.022), (0.011, 0.030),
                               (0.0, 0.032)], (x, y - 0.075, zf), (0, 0, 1), 8, WALNUT, smooth=50.0, cap_bottom=False))
    d = K.part(f"IA_seed_drawer_{i}", p, pivot=(x, y, zf))
    m = K.empty(f"seed_mount_{i}", (x, y - 0.05, zf - 0.12))
    return d, m


def glyph_panel():
    """One mesh of 12 quads with the §11 UV cells (u -> +X, v -> +Y)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    h = GLYPH / 2
    for r in range(3):
        for c in range(4):
            cx, cy = xc(c), yr(r) + 0.02
            vs = [bm.verts.new((cx - h, cy - h, FRONT + 0.002)), bm.verts.new((cx + h, cy - h, FRONT + 0.002)),
                  bm.verts.new((cx + h, cy + h, FRONT + 0.002)), bm.verts.new((cx - h, cy + h, FRONT + 0.002))]
            f = bm.faces.new(vs)
            u0, u1 = c / 4, (c + 1) / 4
            v0, v1 = (2 - r) / 3, (3 - r) / 3
            for lp, (uu, vv) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                lp[uv].uv = (uu, vv)
    o = K.obj_from_bm("glyph_panel", bm, SHQ)
    return o


def build():
    M.reset_scene()
    D.ensure_materials()
    out = dict(body=carcass())
    out["drawers"], out["mounts"] = [], []
    for r in range(3):
        for c in range(4):
            d, m = drawer(r, c)
            out["drawers"].append(d)
            out["mounts"].append(m)
    out["panel"] = glyph_panel()
    out["open"] = D.quad01("glyph_open", (xc(0), yr(0) + 0.02, FRONT + 0.0025), GLYPH, GLYPH, SHQ)
    M.set_origin(out["open"], (xc(0), yr(0) + 0.02, FRONT + 0.0025))
    out["touch"] = [K.empty(f"echo_touch_mount_{c}", (xc(c) + 0.40, 0.0, 0.87), (0.0, 180.0, 0.0)) for c in range(4)]
    K.to_blender()
    # keep the glyph quads' 0..1 / cell UVs (finalize skips M_Shader_Quad faces)
    D.finalize()
    for d, m in zip(out["drawers"], out["mounts"]):
        K.parent(m, d)
    K.parent(out["open"], out["drawers"][0])
    return out


def verify(path):
    drawers = [f"IA_seed_drawer_{i}" for i in range(12)]
    mounts = [f"seed_mount_{i}" for i in range(12)]
    touch = [f"echo_touch_mount_{c}" for c in range(4)]
    req = [NAME, "glyph_panel", "glyph_open"] + drawers + mounts + touch
    expect = {NAME: (0, 0, 0)}
    parents = {NAME: None, "glyph_panel": None, "glyph_open": "IA_seed_drawer_0"}
    rot = {}
    for r in range(3):
        for c in range(4):
            i = drawer_index(r, c)
            expect[f"IA_seed_drawer_{i}"] = (xc(c), yr(r), FRONT)
            expect[f"seed_mount_{i}"] = (xc(c), yr(r) - 0.05, FRONT - 0.12)
            parents[f"IA_seed_drawer_{i}"] = None
            parents[f"seed_mount_{i}"] = f"IA_seed_drawer_{i}"
    expect["glyph_open"] = (xc(0), yr(0) + 0.02, FRONT + 0.0025)
    for c in range(4):
        expect[f"echo_touch_mount_{c}"] = (xc(c) + 0.40, 0.0, 0.87)
        parents[f"echo_touch_mount_{c}"] = None
        rot[f"echo_touch_mount_{c}"] = (0, 180, 0)
    errs = D.verify(path, required=req, identity=[NAME, "glyph_panel", "glyph_open"] + drawers + mounts,
                    expect=expect, parents=parents, rot_expect=rot, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET)
    lo, hi = D.bounds([NAME])
    print(f"{D.TAG} carcass bounds {lo} .. {hi}")
    lo, hi = D.bounds(["IA_seed_drawer_6"])
    print(f"{D.TAG} drawer 6 bounds {lo} .. {hi}")
    # the glyph panel's UV cells, read back from the mesh
    pan = bpy.data.objects["glyph_panel"]
    me = pan.data
    cells = []
    for poly in me.polygons:
        us = [me.uv_layers.active.data[li].uv for li in poly.loop_indices]
        c = Vector((0, 0, 0))
        for li in poly.loop_indices:
            c += pan.matrix_world @ me.vertices[me.loops[li].vertex_index].co
        c /= len(poly.loop_indices)
        g = K.V.C_INV @ c
        cells.append(((round(g.x, 3), round(g.y, 3)), (round(min(u.x for u in us), 3), round(min(u.y for u in us), 3))))
    print(f"{D.TAG} glyph_panel quads (centre x, y) -> UV cell min: {cells}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, open_i=-1):
    for o in parts["drawers"]:
        o.matrix_basis = REST[o.name].copy()
    M.refresh()
    if open_i >= 0:
        K.pose_slide(parts["drawers"][open_i], (0.0, 0.0, OPEN_D))


def panel_preview(hidden=-1):
    """glyph_panel.png with the open drawer's cell blanked (what the hex_glyph shader does with `hidden`)."""
    import numpy as np
    path = os.path.join(D.PREVIEW_DIR, "glyph_panel.png")
    if not os.path.exists(path):
        return None
    img = bpy.data.images.load(path, check_existing=False)
    if hidden >= 0:
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = hidden // 4, hidden % 4
        u0, u1 = int(w * c / 4), int(w * (c + 1) / 4)
        v0, v1 = int(h * (2 - r) / 3), int(h * (3 - r) / 3)          # rows bottom-up in Blender pixels
        px[v0:v1, u0:u1, 3] = 0.0
        img.pixels[:] = px.ravel()
    mat = bpy.data.materials.new(f"qa_glyph_panel_{hidden}")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.25
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    return mat


def leyla(mount_obj, pose_name, prefix):
    h = D.attach("echo_leyla_1998", mount_obj, prefix)
    if h is None:
        return None, []
    keep = []
    gm = D.ghost_material()
    for o in h.children_recursive:
        if o.type != "MESH":
            continue
        if o.name == prefix + pose_name:
            keep.append(o)
            K.override(o, gm)
        else:
            o.hide_render = True
            o.hide_viewport = True
    return h, keep


def fingertip_report(fig, r, c):
    """The pose's most forward left-hand vertex (the middle fingertip) in library coordinates vs drawer (r, c)."""
    M.refresh()
    mw = fig.matrix_world
    holder = bpy.data.objects["qa_place_lib"]
    inv = holder.matrix_world.inverted()
    best = None
    for v in fig.data.vertices:
        p = K.V.C_INV @ (inv @ (mw @ v.co))
        if abs(p.y - yr(r)) < 0.08 and abs(p.x - xc(c)) < 0.12:
            if best is None or p.z < best.z:
                best = p
    if best is None:
        print(f"{D.TAG} fingertip pose_touch_{r} at column {c}: no hand vertex found")
        return
    print(f"{D.TAG} fingertip pose_touch_{r} at column {c}: library-local ({best.x:+.4f}, {best.y:+.4f}, {best.z:+.4f}); "
          f"drawer centre ({xc(c):+.3f}, {yr(r):+.3f}, {FRONT:+.3f}) -> dx {100 * (best.x - xc(c)):+.1f} cm, "
          f"dy {100 * (best.y - yr(r)):+.1f} cm, z - front {1000 * (best.z - FRONT):+.1f} mm")


def qa(parts, args):
    D.qa_begin()
    for o in parts["drawers"]:
        REST[o.name] = o.matrix_basis.copy()
    roots = D.roots()
    D.place(roots, D.LIB_POS, D.LIB_YAW, name="qa_place_lib")
    D.room()
    pan_closed = panel_preview(-1)
    pan_open6 = panel_preview(6)
    open_mat = D.preview_material("qa_glyph_open", "glyph_open.png", rough=0.25)
    if open_mat is not None:
        K.override(parts["open"], open_mat)
    if pan_closed is not None:
        K.override(parts["panel"], pan_closed)
    seed = D.attach("seed_crystal", parts["mounts"][6], "qa_seed_")
    W = lambda p: D.world_point(D.LIB_POS, D.LIB_YAW, p)   # noqa: E731
    V_CAM, V_TGT = (11.25, 1.45, -0.6), (12.55, 1.24, -0.6)

    def show(objs, on):
        for o in objs:
            o.hide_render = not on

    seed_objs = [seed] + list(seed.children_recursive) if seed is not None else []
    show(seed_objs, False)
    parts["open"].hide_render = True

    # 1 the seed_library view (§2), all drawers closed
    if K.want(args, "1"):
        pose(parts)
        D.lights(V_CAM, fill=10.0)
        D.shoot(NAME, V_CAM, V_TGT, 50)
    # 2 drawer 6 open (row 1, column 2): the seed_drawer view, glyph_open on it, cell 6 blanked
    if K.want(args, "2"):
        pose(parts, 6)
        show(seed_objs, True)
        parts["open"].hide_render = False
        old = K.override(parts["panel"], pan_open6) if pan_open6 is not None else None
        # glyph_open reparented to drawer 6 with its local transform kept (as the code does)
        go = parts["open"]
        keep = go.matrix_basis.copy()
        go.parent = parts["drawers"][6]
        go.matrix_parent_inverse = parts["drawers"][0].matrix_basis.inverted() @ parts["drawers"][0].matrix_basis
        go.matrix_basis = keep
        M.refresh()
        F = W((xc(2), yr(1), FRONT + OPEN_D))
        cam = (F[0] - 0.30, F[1] + 0.36, F[2])
        tgt = (F[0] + 0.10, F[1] - 0.04, F[2])
        D.lights(cam, fill=6.0)
        D.shoot(NAME + "_2", cam, tgt, 42)
        go.parent = parts["drawers"][0]
        go.matrix_basis = keep
        M.refresh()
        if old is not None:
            K.restore(parts["panel"], old)
        show(seed_objs, False)
        parts["open"].hide_render = True
    # 3 hero: three-quarter from the south-west, drawer 6 open
    if K.want(args, "3"):
        pose(parts, 6)
        show(seed_objs, True)
        old = K.override(parts["panel"], pan_open6) if pan_open6 is not None else None
        cam = W((-1.35, 1.55, 2.25))
        D.lights(cam, fill=12.0)
        D.shoot(NAME + "_3", cam, W((0.0, 1.10, 0.30)), 50)
        if old is not None:
            K.restore(parts["panel"], old)
        show(seed_objs, False)
    # 4 Leyla's echo (leave path): pose_touch_1 at echo_touch_mount_2 = drawer 6, the seed_library view
    if K.want(args, "4"):
        pose(parts)
        h, figs = leyla(parts["touch"][2], "pose_touch_1", "qa_ly1_")
        if figs:
            fingertip_report(figs[0], 1, 2)
        D.lights(V_CAM, fill=10.0)
        D.shoot(NAME + "_4", V_CAM, V_TGT, 50)
        if h is not None:
            show([h] + list(h.children_recursive), False)
    # 5 close-ups of the three touch poses (row 0 at column 0, row 2 at column 3, row 1 at column 2)
    for tag, rr, cc in (("5", 0, 0), ("6", 2, 3), ("7", 1, 2)):
        if not K.want(args, tag):
            continue
        pose(parts)
        h, figs = leyla(parts["touch"][cc], f"pose_touch_{rr}", f"qa_ly{tag}_")
        if figs:
            fingertip_report(figs[0], rr, cc)
        cam = W((xc(cc) - 0.55, yr(rr) + 0.22, FRONT + 0.55))
        D.lights(cam, fill=6.0)
        D.shoot(NAME + "_" + tag, cam, W((xc(cc) + 0.05, yr(rr), FRONT + 0.05)), 40)
        if h is not None:
            show([h] + list(h.children_recursive), False)
    # 8 drawer 6 open, side view: drawer box, cup, seed, the bay above it (the Nursery root view with every group D
    #   model is prism_bench_6.png)
    if K.want(args, "8"):
        pose(parts, 6)
        show(seed_objs, True)
        cam = W((xc(2) + 0.55, yr(1) + 0.30, FRONT + 0.60))
        D.lights(cam, fill=6.0)
        D.shoot(NAME + "_8", cam, W((xc(2), yr(1) - 0.04, FRONT + 0.15)), 40)
        show(seed_objs, False)


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
