"""MYSTERY ROOM — Chapter 3 group D helpers (the Nursery: autoclave, autoclave_dead, growth_log, seed_library,
growth_chart, prism_bench, spectral_seal_door). Contract: docs/models/ch3.md §6; measured results: docs/models/ch3_d.md.

Builds on lib_ch3_a (group A: G-frame primitives, GLB facts, QA camera / light helpers), which itself builds on
mrlib / lib_mech / lib_arch / lib_props / lib_ch2_vault / lib_ch3_symbols. None of those are edited.

G-FRAME: every group-D script builds its geometry directly in GODOT axes (Blender x, y, z used as Godot x, y, z: y up,
+z = the model front), converts with K.to_blender() right before parenting, exports, re-reads the GLB.

  ensure_materials()            every slot group D uses (+ QA previews of the shader quads)
  finalize()                    world-scale box UVs on everything except decal and shader-quad faces (UV 0..1 kept)
  disc / ring / quad01 / fix_normals / inward   small G-frame mesh helpers
  autoclave_shell(...)          the shared autoclave silhouette (vessel, frame, bands, flange, nozzle, door neck and
                                chamber, pipes to the wall) used by autoclave.py and autoclave_dead.py
  ac_door_parts(...)            the round door (ring, hinge arm, latch), its window glass, the static hinge knuckles
  verify(...)                   GLB check (names, parents, identity rests, positions, rotations, tris, surfaces, slots)
  QA: room(), lights(), place(), attach(), ghost(), preview_material(), shoot()
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402

TAG = "[ch3-d]"
ROOT = M.ROOT
PREVIEW_DIR = os.path.join(ROOT, "qa", "blender", "ch3", "preview")
DECALS3 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch3")

CHROME, STEEL, BRASS, GLASS, FROST = "M_Chrome", "M_Steel_Dark", "M_Brass_Aged", "M_Glass", "M_Glass_Frosted"
PAINT, CREAM, CRYSTAL, BAKE = "M_Steel_Painted", "M_Steel_Cream", "M_Crystal", "M_Bakelite"
WALNUT, PANEL, VELVET, SHQ, LOGDECAL = "M_Wood_Walnut", "M_Wood_Panel", "M_Velvet", "M_Shader_Quad", "M_Decal_GrowthLog"

# world placements (§1.2)
AC_POS = (8.4, 0.0, -3.5)
DEAD_POS = [(9.65, 0.0, -3.5), (10.9, 0.0, -3.5), (12.15, 0.0, -3.5)]
LIB_POS, LIB_YAW = (13.0, 0.0, -0.6), -90.0
CHART_POS, CHART_YAW = (7.75, 0.0, -2.45), 90.0
BENCH_POS = (6.1, 0.0, 0.4)
SEAL_POS = (6.1, 0.0, -1.05)


# ====================================================================== materials / finishing
def ensure_materials() -> None:
    K.ensure_materials()
    for name in (CHROME, STEEL, BRASS, GLASS, FROST, PAINT, CREAM, CRYSTAL, BAKE, WALNUT, PANEL, VELVET):
        M.material(name)


def finalize(objs=None) -> None:
    """World-scale box UVs (1 UV unit = 1 m) on every face except M_Decal_* and M_Shader_Quad (their 0..1 UVs stay)."""
    for obj in (objs or list(bpy.context.scene.objects)):
        if obj.type != "MESH":
            continue
        M.apply_modifiers(obj)
        M.box_uv(obj, 1.0, skip_materials=("M_Decal_", SHQ))


# ====================================================================== G-frame mesh helpers
def _frame(normal):
    n = Vector(normal).normalized()
    return K.axis_rot(n)


def disc(name, r, centre, normal=(0, 0, 1), mat=STEEL, segs=8, phase=0.0):
    """Flat n-gon disc (one face) facing `normal`."""
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(phase + 2 * math.pi * i / segs), r * math.sin(phase + 2 * math.pi * i / segs), 0.0))
          for i in range(segs)]
    bm.faces.new(vs)
    o = K.obj_from_bm(name, bm, mat)
    o.data.transform(Matrix.Translation(centre) @ _frame(normal))
    return o


def disc_uv(name, r, centre, mat=SHQ, segs=32):
    """Disc in the local XY plane facing +Z with UV 0..1 over its bounding square (u -> +X, v -> +Y)."""
    me = bpy.data.meshes.new(name)
    vs = [(0.0, 0.0, 0.0)] + [(r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), 0.0)
                              for i in range(segs)]
    faces = [(0, 1 + i, 1 + (i + 1) % segs) for i in range(segs)]
    me.from_pydata(vs, [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            x, y, _z = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (0.5 + x / (2 * r), 0.5 + y / (2 * r))
    me.transform(Matrix.Translation(centre))
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    return o


def quad01(name, centre, w, h, mat=SHQ, u_axis=(1, 0, 0), v_axis=(0, 1, 0)):
    """G-frame quad with UV 0..1 (u along u_axis, v along v_axis); faces u x v."""
    return K.quad(name, centre, u_axis, v_axis, w, h, mat)


def restore_uv01(obj) -> None:
    """Re-apply 0..1 UVs on a single-quad object after a box UV pass (corner order of K.quad)."""
    uvl = obj.data.uv_layers.active
    for li, (uu, vv) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uvl.data[li].uv = (uu, vv)


def fix_normals(obj, inward=False):
    """Recalculate consistent outward normals on a closed mesh (inward=True flips them all)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inward:
        for f in bm.faces:
            f.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def flip(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def ring(name, r_in, r_out, z0, z1, centre=(0, 0, 0), axis=(0, 0, 1), segs=24, mat=BRASS, chamfer=0.0, smooth=50.0):
    """Closed annulus (washer / bezel) around `axis` through `centre`, from z0 to z1 along the axis."""
    c = min(chamfer, (z1 - z0) * 0.4, (r_out - r_in) * 0.4)
    prof = [(r_in, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c), (r_out - c, z1), (r_in, z1), (r_in, z0)]
    o = K.glathe(name, prof, centre, axis, segs, mat, cap_bottom=False, cap_top=False, smooth=smooth)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(o.data)
    bm.free()
    return fix_normals(o)


def rod(name, a, b, r, segs=8, mat=BRASS, caps=True, smooth=60.0):
    a, b = Vector(a), Vector(b)
    return K.gcyl(name, r, 0.0, (b - a).length, base=tuple(a), axis=tuple(b - a), segments=segs, mat=mat, caps=caps,
                  smooth=smooth)


def tube(name, pts, r, sides=10, mat=STEEL, fillet=0.0):
    return K.V.tube(name, pts, r, sides=sides, mat=mat, fillet=fillet)


def hexnut(name, r, loc, normal, mat=STEEL, h=None):
    """Cheap hex nut / bolt head: a six-sided prism with a top cap only (16 tris), sitting on a surface."""
    h = h or r * 0.8
    o = K.glathe(name, [(r, 0.0), (r, h), (0.0, h)], (0, 0, 0), (0, 0, 1), 6, mat, phase=math.pi / 6,
                 cap_bottom=False)
    o.data.transform(Matrix.Translation(loc) @ _frame(normal))
    return o


def box(name, mn, mx, mat, bevel=0.002, seg=1):
    return K.gbox(name, mn, mx, mat, bevel, seg)


def obox(name, centre, size, rot_y_deg, mat, bevel=0.002):
    """Box of `size` centred at `centre`, turned rot_y_deg about +Y (G-frame)."""
    o = K.gbox(name, tuple(-s / 2 for s in size), tuple(s / 2 for s in size), mat, bevel)
    o.data.transform(Matrix.Translation(centre) @ Matrix.Rotation(math.radians(rot_y_deg), 4, "Y"))
    return o


def place_xz(obj, centre, normal, up=(0, 1, 0)):
    """Move a mesh built facing +Z (local XY = its face, +Y = its up) onto `centre`, facing `normal`."""
    n = Vector(normal).normalized()
    u = Vector(up)
    x = u.cross(n)
    if x.length < 1e-6:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    m = Matrix((x, y, n)).transposed().to_4x4()
    obj.data.transform(Matrix.Translation(centre) @ m)
    return obj


def flame_loop(h, n=8):
    """A flame pictogram outline (height h, centred on its box, +y up): a round bulb drawn up into a tip that leans
    slightly right. Counter-clockwise."""
    w = h * 0.34
    cy = -h * 0.5 + w
    tip = (h * 0.05, h * 0.5)

    def circ(deg):
        a = math.radians(deg)
        return (w * math.cos(a), cy + w * math.sin(a))

    pts = [circ(-90 + 120 * i / n) for i in range(n + 1)]              # -90 .. 30
    a0, a1 = circ(30), tip
    for i in range(1, n):                                              # right flank, slightly concave
        t = i / n
        x = a0[0] + (a1[0] - a0[0]) * t - math.sin(math.pi * t) * w * 0.10
        y = a0[1] + (a1[1] - a0[1]) * t
        pts.append((x, y))
    pts.append(tip)
    b0 = circ(150)
    for i in range(1, n):                                              # left flank, bulging out
        t = i / n
        x = tip[0] + (b0[0] - tip[0]) * t - math.sin(math.pi * t) * w * 0.22
        y = tip[1] + (b0[1] - tip[1]) * t
        pts.append((x, y))
    pts += [circ(150 + 120 * i / n) for i in range(n + 1)]             # 150 .. 270
    return A.ccw(A.dedupe(pts[:-1]))


def flame_inner(h):
    """Inner tongue of the flame (a hole inside flame_loop(h)): the same flame at 0.42 scale, low in the bulb."""
    s = 0.42
    dy = -h * 0.5 + h * s * 0.5 + h * 0.07
    return [(x * s, y * s + dy) for (x, y) in flame_loop(h, n=6)]


# ====================================================================== the autoclave silhouette (shared)
R_V = 0.425                    # vessel radius (Ø 0.85)
Y_CYL0, Y_CYL1, Y_TOP = 0.36, 1.95, 2.10
DOOR_C = (0.0, 1.20)           # door centre (x, y)
DOOR_R = 0.21
NECK_R_IN, NECK_R_OUT = 0.200, 0.238
FLANGE_R, FLANGE_Z = 0.262, 0.43
CHAMBER_BACK = 0.10
DOOR_PIVOT = (-0.21, 1.20, 0.46)
WIN_R = 0.122


def vessel_profile():
    return [(0.0, 0.285), (0.20, 0.296), (0.36, 0.326), (R_V, Y_CYL0), (R_V, Y_CYL1), (0.420, 1.978),
            (0.402, 2.008), (0.368, 2.037), (0.31, 2.063), (0.22, 2.084), (0.11, 2.097), (0.0, Y_TOP)]


def autoclave_shell(seg=40, lite=False):
    """Static parts of the autoclave silhouette, in model coords (G-frame). Returns {material: [objects]}.

    Vessel Ø 0.85 (y 0.36 .. 1.95 cylinder, dished bottom to 0.285, domed top to 2.10) with the door hole cut, the
    manway neck and flange, the chamber (inward-facing cylinder r 0.20 from the flange back to z 0.10 + back wall),
    the top nozzle under the shell's frosted drop (local (0, 2.13, 0)), the bolted girth flange, three lagging bands,
    the steel frame (four legs, ring girder, low rails, foot plates), pipes back to the wall (local z = -0.5), a
    safety valve on the dome, and the static hinge knuckles of the door. lite=True (the dead autoclaves) uses fewer
    segments and bolts."""
    out = {CHROME: [], STEEL: []}
    ch, st = out[CHROME], out[STEEL]
    seg_s = 20 if lite else 24
    seg_b = 24 if lite else 32
    # ---- vessel + door hole
    ves = K.glathe("vessel", vessel_profile(), (0, 0, 0), (0, 1, 0), seg, CHROME, smooth=40.0, phase=math.pi / seg)
    cutter = K.gcyl("cut_door", NECK_R_IN, 0.0, 0.6, base=(DOOR_C[0], DOOR_C[1], 0.0), axis=(0, 0, 1), segments=seg_s,
                    mat=CHROME)
    M.boolean(ves, cutter)
    A.hint(ves, 40.0)
    ch.append(ves)
    # ---- manway neck (outer), flange ring, chamber (inward), back wall
    ch.append(K.gcyl("neck", NECK_R_OUT, 0.27, 0.41, base=(DOOR_C[0], DOOR_C[1], 0.0), axis=(0, 0, 1), segments=seg_s,
                     mat=CHROME, caps=False, smooth=50.0))
    ch.append(ring("flange", NECK_R_IN, FLANGE_R, 0.405, FLANGE_Z, (DOOR_C[0], DOOR_C[1], 0.0), (0, 0, 1), seg_s, CHROME))
    cham = K.gcyl("chamber", NECK_R_IN, CHAMBER_BACK, 0.405, base=(DOOR_C[0], DOOR_C[1], 0.0), axis=(0, 0, 1),
                  segments=seg_s, mat=STEEL, caps=False, smooth=50.0)
    flip(cham)
    st.append(cham)
    st.append(disc("chamber_back", NECK_R_IN + 0.002, (DOOR_C[0], DOOR_C[1], CHAMBER_BACK), (0, 0, 1), STEEL, seg_s))
    # flange bolts (visible ring r 0.21 .. 0.262)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        p = (DOOR_C[0] + 0.238 * math.cos(a), DOOR_C[1] + 0.238 * math.sin(a), FLANGE_Z)
        if p[0] < -0.17 and abs(p[1] - DOOR_C[1]) < 0.11:
            continue                                         # hinge block
        st.append(hexnut("fb", 0.0085, p, (0, 0, 1)))
    # ---- static hinge block + knuckles (pivot axis vertical through DOOR_PIVOT)
    px, py, pz = DOOR_PIVOT
    st.append(box("hblock", (-0.300, py - 0.075, 0.395), (-0.255, py + 0.075, 0.445), STEEL, 0.003))
    for (y0, y1) in ((py - 0.072, py - 0.038), (py + 0.038, py + 0.072)):
        st.append(box("harm", (-0.262, y0, pz - 0.012), (px, y1, pz + 0.012), STEEL, 0.0))
        ch.append(K.gcyl("hknuck", 0.0145, y0, y1, base=(px, 0, pz), axis=(0, 1, 0), segments=10, mat=CHROME))
    # ---- girth flange near the top (bolted lid), bands
    gf = [(R_V - 0.002, 1.852), (0.458, 1.858), (0.458, 1.902), (R_V - 0.002, 1.908)]
    ch.append(K.glathe("gflange", gf, (0, 0, 0), (0, 1, 0), seg, CHROME, cap_bottom=False, cap_top=False, smooth=40.0))
    nb = 8 if lite else 12
    for k in range(nb):
        a = 2 * math.pi * (k + 0.5) / nb
        st.append(hexnut("gfb", 0.0095, (0.442 * math.sin(a), 1.902, 0.442 * math.cos(a)), (0, 1, 0)))
    for y in ((0.50, 1.62) if lite else (0.50, 0.80, 1.62)):
        band = [(R_V - 0.001, y - 0.017), (R_V + 0.005, y - 0.013), (R_V + 0.005, y + 0.013), (R_V - 0.001, y + 0.017)]
        st.append(K.glathe("band", band, (0, 0, 0), (0, 1, 0), seg_b, STEEL, cap_bottom=False, cap_top=False,
                           smooth=40.0, phase=math.pi / seg_b))
        # band buckle at the back-left (clear of the door, gauge, log and the dead model's valve / gauge)
        a = math.radians(-125)
        c = Vector((R_V * math.sin(a), y, R_V * math.cos(a)))
        st.append(obox("buckle", tuple(c + Vector((math.sin(a), 0, math.cos(a))) * 0.012), (0.05, 0.038, 0.022),
                       math.degrees(a), STEEL, 0.0))
    # ---- top nozzle (meets the shell's frosted drop at (0, 2.13, 0)), dome safety valve
    ch.append(K.glathe("nozzle", [(0.062, 2.06), (0.062, 2.112), (0.088, 2.112), (0.088, 2.140), (0.050, 2.140)],
                       (0, 0, 0), (0, 1, 0), 16, CHROME, cap_bottom=False, cap_top=False, smooth=45.0))
    for k in range(4 if lite else 6):
        a = 2 * math.pi * k / (4 if lite else 6)
        st.append(hexnut("nb", 0.007, (0.075 * math.cos(a), 2.140, 0.075 * math.sin(a)), (0, 1, 0)))
    sv = (0.22, 2.068, -0.14)
    ch.append(K.glathe("svalve", [(0.034, 0.0), (0.034, 0.014), (0.024, 0.016), (0.024, 0.07), (0.030, 0.074),
                                  (0.030, 0.088), (0.0, 0.098)], sv, (0, 1, 0), 10, CHROME, smooth=45.0, cap_bottom=False))
    st.append(rod("svlever", (sv[0], sv[1] + 0.09, sv[2]), (sv[0] - 0.12, sv[1] + 0.075, sv[2] + 0.02), 0.005, 6, STEEL))
    st.append(K.gcyl("svweight", 0.016, -0.018, 0.018, base=(sv[0] - 0.115, sv[1] + 0.076, sv[2] + 0.019),
                     axis=(1, 0, 0), segments=8, mat=STEEL))
    # ---- frame: four square legs at the diagonals, lugs, ring girder, low rails, feet
    leg = 0.332
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * leg, sz * leg
            st.append(box("leg", (cx - 0.024, 0.012, cz - 0.024), (cx + 0.024, 0.86, cz + 0.024), STEEL, 0.003))
            st.append(box("foot", (cx - 0.055, 0.0, cz - 0.055), (cx + 0.055, 0.014, cz + 0.055), STEEL, 0.0))
            if not lite:
                for bx, bz in ((cx - 0.038, cz - 0.038), (cx + 0.038, cz + 0.038)):
                    st.append(hexnut("fbolt", 0.007, (bx, 0.014, bz), (0, 1, 0)))
            # lug plate welded to the vessel (radial, toward the leg)
            a = math.atan2(cx, cz)
            st.append(obox("lug", (0.405 * math.sin(a), 0.74, 0.405 * math.cos(a)), (0.012, 0.20, 0.09),
                           math.degrees(a), STEEL, 0.0))
    girder = [(0.39, 0.300), (0.468, 0.300), (0.468, 0.355), (0.39, 0.355)]
    st.append(K.glathe("girder", girder, (0, 0, 0), (0, 1, 0), seg_b, STEEL, cap_bottom=False, cap_top=False,
                       smooth=40.0, phase=math.pi / seg_b))
    for (a, b) in (((-leg, -leg), (leg, -leg)), ((-leg, -leg), (-leg, leg)), ((leg, -leg), (leg, leg)),
                   ((-leg, leg), (leg, leg))):
        y0, y1 = 0.10, 0.135
        if a[0] == b[0]:
            st.append(box("rail", (a[0] - 0.018, y0, a[1]), (a[0] + 0.018, y1, b[1]), STEEL, 0.0))
        else:
            st.append(box("rail", (a[0], y0, a[1] - 0.018), (b[0], y1, a[1] + 0.018), STEEL, 0.0))
    # ---- pipes back to the wall (local z = -0.5)
    st.append(tube("steam", [(-0.30, 1.72, -0.28), (-0.30, 1.72, -0.49)], 0.028, 8, STEEL))
    st.append(ring("steam_fl", 0.0, 0.058, -0.50, -0.488, (-0.30, 1.72, 0.0), (0, 0, 1), 10, STEEL))
    st.append(ring("steam_fl2", 0.026, 0.050, -0.33, -0.315, (-0.30, 1.72, 0.0), (0, 0, 1), 10, STEEL))
    st.append(tube("vent", [(0.29, 1.32, -0.29), (0.29, 1.32, -0.49)], 0.020, 8, STEEL))
    st.append(ring("vent_fl", 0.0, 0.045, -0.50, -0.488, (0.29, 1.32, 0.0), (0, 0, 1), 8, STEEL))
    st.append(tube("drain", [(0.0, 0.29, 0.0), (0.0, 0.16, 0.0), (0.0, 0.16, -0.49)], 0.024, 8, STEEL, fillet=0.06))
    st.append(ring("drain_fl", 0.0, 0.05, -0.50, -0.488, (0.0, 0.16, 0.0), (0, 0, 1), 8, STEEL))
    return out


def ac_door(ajar_deg=0.0, seg=28, frost=False, lite=False):
    """The round door (chrome ring with window hole, hinge arm and knuckle, latch lever, bolts) and its window
    glass. Built closed in model coords, then turned ajar_deg about +Y at DOOR_PIVOT (negative opens toward the
    viewer). Returns (door_parts, glass_obj)."""
    cx, cy = DOOR_C
    prof = [(WIN_R + 0.002, 0.433), (0.205, 0.433), (DOOR_R, 0.440), (DOOR_R, 0.457), (0.200, 0.466),
            (0.140, 0.472), (0.128, 0.474), (WIN_R, 0.469), (WIN_R + 0.002, 0.433)]
    ring_o = K.glathe("door_ring", prof, (cx, cy, 0.0), (0, 0, 1), seg, CHROME, cap_bottom=False, cap_top=False,
                      smooth=40.0)
    bm = bmesh.new()
    bm.from_mesh(ring_o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.to_mesh(ring_o.data)
    bm.free()
    fix_normals(ring_o)
    parts = [ring_o]
    for k in range(4 if lite else 6):
        a = math.radians(30 + (90 if lite else 60) * k)
        parts.append(hexnut("dbolt", 0.0075, (cx + 0.180 * math.cos(a), cy + 0.180 * math.sin(a), 0.468), (0, 0, 1),
                            CHROME, h=0.005))
    px, py, pz = DOOR_PIVOT
    parts.append(box("darm", (px, py - 0.034, pz - 0.010), (-0.165, py + 0.034, pz + 0.012), CHROME, 0.0))
    parts.append(K.gcyl("dknuck", 0.0145, py - 0.036, py + 0.036, base=(px, 0, pz), axis=(0, 1, 0), segments=10,
                        mat=CHROME))
    # latch: a boss on the free (right) edge and a lever handle hanging down-forward
    lb = (0.172, cy + 0.02, 0.468)
    parts.append(K.gcyl("lboss", 0.020, 0.0, 0.016, base=lb, axis=(0, 0, 1), segments=10, mat=CHROME, chamfer=0.003))
    parts.append(rod("lever", (lb[0], lb[1], lb[2] + 0.012), (lb[0] + 0.004, lb[1] - 0.115, lb[2] + 0.030), 0.0075, 8,
                     CHROME))
    parts.append(K.glathe("lgrip", [(0.0, -0.012), (0.012, -0.006), (0.013, 0.004), (0.0, 0.014)],
                          (lb[0] + 0.004, lb[1] - 0.125, lb[2] + 0.031), (0, -1, 0.25), 8, CHROME, smooth=60.0))
    glass = K.gcyl("window", WIN_R + 0.001, 0.443, 0.465, base=(cx, cy, 0.0), axis=(0, 0, 1), segments=seg,
                   mat=FROST if frost else GLASS, smooth=40.0)
    if abs(ajar_deg) > 1e-6:
        m = Matrix.Translation(DOOR_PIVOT) @ Matrix.Rotation(math.radians(ajar_deg), 4, "Y") @ \
            Matrix.Translation(Vector(DOOR_PIVOT) * -1)
        for o in parts + [glass]:
            o.data.transform(m)
    return parts, glass


# ====================================================================== GLB verification
def verify(path, required=(), identity=(), expect=None, parents=None, rot_expect=None, tri_budget=0, surf_budget=0,
           mat_budget=4):
    errs = K.V.verify_glb(path, required=required, identity=identity, expect=expect or {}, parents=parents or {},
                          show=required, rot_expect=rot_expect or {})
    errs += K.facts(path, tri_budget, surf_budget, mat_budget)
    rc = K.V.check_names(path)
    if rc != 0:
        errs.append("check_glb_names failed")
    return errs


def bounds(names):
    lo, hi = K.V.mesh_bounds_godot([bpy.data.objects[n] for n in names])
    return tuple(round(c, 4) for c in lo), tuple(round(c, 4) for c in hi)


# ====================================================================== QA
def qa_begin():
    K.qa_begin(bounces=6)
    for name, val in (("M_Velvet", 0.6),):
        mat = bpy.data.materials.get(name)
        if mat is not None and mat.use_nodes:
            b = mat.node_tree.nodes.get("Principled BSDF")
            if b is not None and "Sheen Weight" in b.inputs:
                b.inputs["Sheen Weight"].default_value = val


def room(shell=True, extra=()):
    """Import the Nursery shell (and neighbouring GLBs: [(name, pos, yaw, prefix)]) for world-placed QA shots."""
    if shell:
        K.qa_import("shell_nursery", (0, 0, 0), 0.0, prefix="qa_sn_")
    for name, pos, yaw, prefix in extra:
        if os.path.exists(K.V.model_glb(name)):
            K.qa_import(name, pos, yaw, prefix=prefix)
    for o in bpy.data.objects:
        if o.name.startswith("qa_sn_lamp_glass"):
            K.override(o, K.glow("qa_fluor", "E8F2FF", 7.0))


LAMPS = [(9.3, -2.2), (12.0, -2.2), (6.0, 1.6), (9.3, 1.6), (12.0, 1.6)]


def lights(cam=None, fill=10.0, camp=False, key=1500.0, prism_lamp=False):
    """The Nursery's §1.5 lights (key spot, two fills, the five fluorescent tubes) + the camera-following fill."""
    K.clear_lights()
    K.light("key_nursery", "SPOT", (9.8, 3.9, 0.2), key, "DCEBFF", radius=0.3, target=(9.8, 0.0, -3.4), spot_deg=60)
    K.light("fill_0b", "POINT", (6.8, 3.6, 1.2), 160.0, "DCEBFF", radius=0.2)
    K.light("fill_1b", "POINT", (11.5, 3.6, 0.8), 160.0, "DCEBFF", radius=0.2)
    for k, (x, z) in enumerate(LAMPS):
        K.light(f"tube_{k}", "AREA", (x, 3.85, z), 60.0, "E8F2FF", radius=1.2, target=(x, 0.0, z))
    if camp:
        K.light("camp_lamp", "POINT", (6.2, 2.45, -2.6), 70.0, "FFC27A", radius=0.05)
    if prism_lamp:
        K.light("prism_lamp", "SPOT", (6.1, 1.0, 0.55), 30.0, "FFF4E0", radius=0.02, target=(6.1, 1.15, -1.0),
                spot_deg=25)
    if cam is not None and fill > 0:
        K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), fill, "FFE2C2", radius=0.2)


def place(objs, pos, yaw, name="qa_place"):
    """Parent the (Blender-axis) root objects of a model under a holder at a world position / yaw (QA only)."""
    return K.qa_place(objs, pos, yaw, name=name)


def roots():
    return [o for o in bpy.context.scene.objects if o.parent is None and not o.name.startswith(("qa_", "QA"))]


def swap_materials(prefix):
    """Give imported (lean) GLB meshes this scene's preview materials of the same slot name (QA only)."""
    for o in bpy.data.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            base = m.name.split(".")[0]
            if base != m.name and bpy.data.materials.get(base) is not None:
                slot.material = bpy.data.materials[base]


def attach(name, mount_obj, prefix):
    """Import a GLB under a mount empty with an identity transform (QA only)."""
    h = K.V.qa_import(K.V.model_glb(name), parent_obj=mount_obj, prefix=prefix)
    swap_materials(prefix)
    return h


def attach_offset(name, mount_obj, prefix, godot_offset):
    h = attach(name, mount_obj, prefix)
    if h is not None:
        h.matrix_basis = Matrix.Translation(K.V.C @ Vector(godot_offset))
        M.refresh()
    return h


def ghost_material():
    import lib_echo as E
    return E.ghost_look_material()


def preview_material(name, filename, emissive=False, strength=1.0, rough=0.6):
    """QA-only material for a shader quad: the seed-0 preview image (alpha honoured). emissive=True for screens and
    receptors (light-like), else a matte printed look."""
    path = os.path.join(PREVIEW_DIR, filename)
    if not os.path.exists(path):
        return None
    if emissive:
        return K.image_emitter(name, path, strength=strength)
    img = bpy.data.images.load(path, check_existing=True)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = rough
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    return mat


def shoot(name, cam, target, vfov):
    return K.shoot(name, cam, target, vfov=vfov)


def world_point(pos, yaw_deg, local):
    """Model-local Godot point -> world Godot point for a model at pos with yaw (rotation about +Y)."""
    a = math.radians(yaw_deg)
    x, y, z = local
    return (pos[0] + x * math.cos(a) + z * math.sin(a), pos[1] + y, pos[2] - x * math.sin(a) + z * math.cos(a))


def obj_world_godot(o):
    M.refresh()
    p = K.V.C_INV @ o.matrix_world.translation
    return (p.x, p.y, p.z)


def mesh_clearance(fig_objs, solid_objs, sample=3):
    """(intersecting triangle pairs, min vertex distance) between figure meshes and solid meshes (Blender world)."""
    from mathutils.bvhtree import BVHTree
    M.refresh()
    dg = bpy.context.evaluated_depsgraph_get()

    def tree(objs):
        verts, polys = [], []
        for o in objs:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            base = len(verts)
            verts += [o.matrix_world @ v.co for v in me.vertices]
            polys += [[base + i for i in p.vertices] for p in me.polygons]
            ev.to_mesh_clear()
        return BVHTree.FromPolygons(verts, polys), verts

    ft, fverts = tree(fig_objs)
    st, _ = tree(solid_objs)
    pairs = ft.overlap(st)
    dmin = 1e9
    for v in fverts[::sample]:
        hit = st.find_nearest(v)
        if hit[0] is not None:
            dmin = min(dmin, hit[3])
    return len(pairs), dmin
