"""reading_table.glb — long walnut library reading table with a green banker's lamp (Chapter 2; group B2).

1.40 x 0.80, top y = 0.76. Free-standing: origin on the floor at the footprint centre, front +Z (placed at
world (1.9, 0, 1.0), yaw 0; the reading view looks at it from the south).
Thick walnut top with a moulded thumbnail edge, aprons with a shallow centre drawer, four turned legs on an
H stretcher. Dressing: a brass banker's lamp with a green cased-glass shade at the back centre, two open
ledgers, a closed pair of ledgers and a brass reading magnifier on a stand. The spots the code uses for the
CC0 magnifying glass (model (+0.35, 0.12)) and spectacles (model (-0.45, -0.14)) are kept free.

Parts (no IA parts):
  lamp_shade     M_Glass_Green outside / M_Enamel_White inside, own object.
  bulb           M_Emissive_Warm, own object, origin at the bulb centre (the code sets its emission).
  light_origin   empty at the bulb centre (where an OmniLight belongs).
  table, banker_lamp, table_dressing   static.

    blender -b --factory-startup -P tools/blender/models/reading_table.py [-- --no-render] [--shots a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as K  # noqa: E402
import lib_props as P  # noqa: E402
import lib_ch2_furniture2 as F  # noqa: E402
from lib_ch2_furniture2 import G  # noqa: E402

NAME = "reading_table"
ARGS = M.main_guard()
BUDGET = 5000

TOP = 0.76
W2, D2 = 0.70, 0.40
LEG_X, LEG_Z = 0.615, 0.315
APRON_Y = (0.625, 0.728)
LAMP = (0.0, TOP, -0.235)     # lamp base centre on the table

parts = {}


# ------------------------------------------------------------------ table
def build_table():
    t = []
    # top: core slab + a moulded edge band all round (thumbnail top edge, small cove underneath)
    t.append(F.gbox("top_core", (-W2 + 0.006, 0.728, -D2 + 0.006), (W2 - 0.006, TOP, D2 - 0.006), mat="M_Wood_Walnut",
                    bevel=0.0))
    edge = [(0.0, 0.728), (-0.003, 0.7295), (-0.005, 0.733), (-0.006, 0.737), (-0.006, 0.746), (-0.0055, 0.7515),
            (-0.004, 0.7555), (-0.0015, 0.7585), (0.0, TOP)]
    path = [G(-W2 + 0.006, 0, D2 - 0.006), G(W2 - 0.006, 0, D2 - 0.006), G(W2 - 0.006, 0, -D2 + 0.006),
            G(-W2 + 0.006, 0, -D2 + 0.006)]
    t.append(A.sweep("top_edge", edge, path, up=(0, 0, 1), closed=True, mat="M_Wood_Walnut"))
    # aprons with a shallow centre drawer on the front
    y0, y1 = APRON_Y
    t.append(F.gbox("apron_back", (-LEG_X, y0, -LEG_Z - 0.010), (LEG_X, y1, -LEG_Z + 0.010), mat="M_Wood_Walnut",
                    bevel=0.002))
    for sx in (-1, 1):
        t.append(F.gbox(f"apron_side{sx}", (sx * LEG_X - 0.010, y0, -LEG_Z), (sx * LEG_X + 0.010, y1, LEG_Z),
                        mat="M_Wood_Walnut", bevel=0.002))
        t.append(F.gbox(f"apron_front{sx}", (sx * 0.24 if sx > 0 else -LEG_X, y0, LEG_Z - 0.010),
                        (LEG_X if sx > 0 else -0.24, y1, LEG_Z + 0.010), mat="M_Wood_Walnut", bevel=0.002))
    t.append(F.gbox("apron_front_top", (-0.24, y1 - 0.012, LEG_Z - 0.010), (0.24, y1, LEG_Z + 0.010), mat="M_Wood_Walnut",
                    bevel=0.0015))
    t.append(F.gbox("drawer_front", (-0.236, y0 + 0.004, LEG_Z - 0.006), (0.236, y1 - 0.014, LEG_Z + 0.012),
                    mat="M_Wood_Walnut", bevel=0.004))
    t.append(F.gbox("apron_bead", (-LEG_X, y0 - 0.006, LEG_Z + 0.004), (LEG_X, y0, LEG_Z + 0.013), mat="M_Wood_Walnut",
                    bevel=0.002))
    for sx in (-1, 1):
        t.append(F.glathe(f"drawer_knob{sx}", [(0.0, 0.0), (0.010, 0.0), (0.0055, 0.006), (0.006, 0.012), (0.012, 0.019),
                                               (0.011, 0.026), (0.0, 0.0275)],
                          (sx * 0.12, (y0 + y1) / 2 - 0.004, LEG_Z + 0.012), axis="z", segments=8, mat="M_Brass_Aged"))
    t.append(F.gslab("drawer_esc", (0.0, (y0 + y1) / 2 - 0.002, LEG_Z + 0.012), 0.016, 0.028, 0.0012, r=0.007,
                     mat="M_Brass_Aged", plane="xy", bevel=0.0, n=3))
    t.append(F.gslab("drawer_keyhole", (0.0, (y0 + y1) / 2 - 0.0005, LEG_Z + 0.0132), 0.0045, 0.012, 0.0004, r=0.002,
                     mat="M_Bakelite", plane="xy", bevel=0.0, n=2))
    # legs: square blocks under the top, turned below
    prof = [(0.030, 0.0), (0.030, 0.014), (0.021, 0.030), (0.017, 0.10), (0.0265, 0.13), (0.0285, 0.30), (0.0255, 0.47),
            (0.030, 0.525), (0.022, 0.548), (0.033, 0.58), (0.0, 0.58)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * LEG_X, sz * LEG_Z
            t.append(F.gbox(f"leg_block_{sx}_{sz}", (x - 0.031, 0.575, z - 0.031), (x + 0.031, 0.728, z + 0.031),
                            mat="M_Wood_Walnut", bevel=0.003))
            t.append(F.glathe(f"leg_{sx}_{sz}", [(0.0, 0.0)] + prof, (x, 0.0, z), segments=8, mat="M_Wood_Walnut",
                              smooth=50.0))
    # H stretcher
    for sx in (-1, 1):
        t.append(F.gbox(f"stretcher_side{sx}", (sx * LEG_X - 0.014, 0.105, -LEG_Z), (sx * LEG_X + 0.014, 0.135, LEG_Z),
                        mat="M_Wood_Walnut", bevel=0.004))
    t.append(F.gbox("stretcher_mid", (-LEG_X, 0.108, -0.016), (LEG_X, 0.134, 0.016), mat="M_Wood_Walnut", bevel=0.004))
    parts["table"] = F.part("table", t)


# ------------------------------------------------------------------ banker's lamp
def build_lamp():
    bx, by, bz = LAMP
    base_c = G(bx, by, bz)
    lp = []
    base = P.rrect_loft("lamp_base", [
        (0.200, 0.140, 0.034, 0.000), (0.200, 0.140, 0.034, 0.006), (0.196, 0.136, 0.032, 0.009),
        (0.186, 0.126, 0.028, 0.011), (0.180, 0.120, 0.025, 0.016), (0.168, 0.108, 0.020, 0.019),
        (0.150, 0.090, 0.015, 0.0215), (0.146, 0.086, 0.014, 0.0215)], mat="M_Brass_Aged", n=3)
    base.location = base_c
    lp.append(base)
    stem0 = base_c + Vector((0.0, 0.028, 0.0))       # stem rises at the back of the base (Blender +Y = Godot -Z)
    lp.append(M.lathe("lamp_boss", [(0.0, 0.0215), (0.026, 0.0215), (0.024, 0.028), (0.016, 0.036), (0.0115, 0.046),
                                    (0.0, 0.046)], loc=stem0, segments=12, mat="M_Brass_Aged"))
    lp.append(K.lathe2("lamp_collar", [(0.0, 0.044), (0.0115, 0.044), (0.0125, 0.047, "k"), (0.0125, 0.056, "k"),
                                       (0.011, 0.059), (0.0, 0.059)], segments=14, mat="M_Brass_Polished", knurl=0.0007,
                       loc=stem0))
    crook = [stem0 + Vector((0, 0, 0.056)), stem0 + Vector((0, 0, 0.30))]
    crook += P.bezier(stem0 + Vector((0, 0, 0.30)), stem0 + Vector((0, 0, 0.352)), stem0 + Vector((0, -0.016, 0.386)),
                      stem0 + Vector((0, -0.052, 0.386)), 5)[1:]
    crook += P.bezier(stem0 + Vector((0, -0.052, 0.386)), stem0 + Vector((0, -0.066, 0.386)),
                      stem0 + Vector((0, -0.074, 0.382)), stem0 + Vector((0, -0.076, 0.374)), 2)[1:]
    lp.append(P.tube("lamp_stem", crook, 0.0072, sides=10, mat="M_Brass_Aged"))
    for zc in (0.16, 0.29):
        lp.append(M.lathe(f"lamp_ring{zc}", [(0.0071, zc - 0.005), (0.0095, zc - 0.0025), (0.0095, zc + 0.0025),
                                             (0.0071, zc + 0.005)], loc=stem0, segments=10, mat="M_Brass_Polished"))
    hold = stem0 + Vector((0, -0.076, 0.368))
    lp.append(M.lathe("shade_boss", [(0.0, -0.004), (0.016, -0.004), (0.018, 0.0), (0.011, 0.006), (0.008, 0.008),
                                     (0.0, 0.009)], loc=hold, segments=10, mat="M_Brass_Polished"))
    # green cased-glass shade: stretched dome, opening tilted toward the reader (+Z Godot = -Y Blender)
    sh_l = 0.13
    outer = [(0.0, 0.0), (0.030, 0.003), (0.052, 0.015), (0.066, 0.034), (0.0725, 0.054), (0.0745, 0.069)]
    loop = P.shell_profile(outer, 0.0032, lip=0.0012)
    bands = ["M_Glass_Green"] * (len(outer) - 1) + ["M_Enamel_White"] * (len(loop) - len(outer))
    shade = K.lathe2("lamp_shade", loop, segments=22, mat="M_Glass_Green", band_mats=bands, phase=math.pi / 22)
    bm = bmesh.new()
    bm.from_mesh(shade.data)
    for v in bm.verts:
        if abs(v.co.x) > 1e-7:
            v.co.x += math.copysign(sh_l / 2, v.co.x)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(shade.data)
    bm.free()
    tilt = math.radians(-13)
    shade.data.transform(Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(math.pi, 4, "X"))
    sh_top = hold + Vector((0, 0, -0.004))
    shade.location = sh_top
    M.apply_transform(shade)
    A.hint(shade, 50.0)
    down = Matrix.Rotation(tilt, 3, "X") @ Vector((0, 0, -1))
    sock_p = sh_top + down * 0.004
    sock = M.lathe("lamp_socket", [(0.0, 0.0), (0.011, 0.0), (0.012, -0.004), (0.012, -0.018), (0.0105, -0.021),
                                   (0.0, -0.021)], segments=8, mat="M_Brass_Aged")
    sock.data.transform(Matrix.Rotation(tilt, 4, "X"))
    sock.location = sock_p
    lp.append(sock)
    bulb_c = sock_p + down * 0.040
    bulb = M.lathe("bulb", [(r * 0.85, z * 0.85) for (r, z) in ((0.0, -0.002), (0.0085, -0.003), (0.0115, -0.009),
                                                               (0.0165, -0.02), (0.0182, -0.03), (0.017, -0.039),
                                                               (0.0125, -0.047), (0.006, -0.0505), (0.0, -0.051))],
                   segments=12, mat="M_Emissive_Warm")
    bulb.data.transform(Matrix.Translation((0, 0, -0.018)))
    bulb.data.transform(Matrix.Rotation(tilt, 4, "X"))
    bulb.location = sock_p
    M.apply_transform(bulb)
    A.hint(bulb, 60.0)
    # bead pull chain
    ch0 = sock_p + down * 0.012 + Vector((0.017, 0.0, 0.0))
    ch1 = Vector((ch0.x + 0.002, ch0.y - 0.003, base_c.z + 0.215))
    for i in range(10):
        lp.append(M.sphere(f"lamp_bead{i}", 0.0017, loc=ch0.lerp(ch1, i / 9), segments=5, rings=3, mat="M_Brass_Polished"))
    lp.append(P.tube("lamp_chain", [ch0, ch1], 0.0005, sides=4, mat="M_Brass_Aged"))
    lp.append(M.lathe("lamp_pull", [(0.0, 0.0), (0.0025, 0.0005), (0.0048, -0.006), (0.0052, -0.014), (0.0035, -0.021),
                                    (0.0, -0.023)], loc=ch1, segments=7, mat="M_Brass_Polished"))
    # cloth flex: from the back of the base over the table's back edge, down the back
    fl = [G(bx + 0.03, TOP + 0.006, bz - 0.06), G(bx + 0.05, TOP + 0.005, bz - 0.10), G(bx + 0.09, TOP + 0.005, -D2 + 0.03),
          G(bx + 0.12, TOP + 0.002, -D2 - 0.004), G(bx + 0.13, TOP - 0.03, -D2 - 0.010), G(bx + 0.13, 0.62, -D2 - 0.012)]
    lp.append(P.tube("lamp_flex", fl, 0.0033, sides=6, mat="M_Fabric"))
    parts["lamp"] = F.part("banker_lamp", lp)
    parts["shade"] = F.part("lamp_shade", [shade], pivot=F.to_godot(sh_top))
    parts["bulb"] = F.part("bulb", [bulb], pivot=F.to_godot(bulb_c))
    parts["light_origin"] = F.mount("light_origin", F.to_godot(bulb_c))
    parts["bulb_c"] = F.to_godot(bulb_c)


# ------------------------------------------------------------------ ledgers, magnifier
def page_loop(w, h, side, gutter_dip=0.006, flat_from=0.035):
    """2D cross-section (x across, y up) of one page block of an open book; side -1 = left, +1 = right."""
    pts = [(side * 0.002, 0.0), (side * (w - 0.004), 0.0), (side * (w - 0.002), h * 0.25), (side * (w - 0.004), h)]
    for j in range(7):
        x = (w - 0.004) * (1 - j / 6)
        if x > flat_from:
            y = h
        else:
            u = x / flat_from
            y = h - gutter_dip * (1 - math.sin(u * math.pi / 2))
        pts.append((side * x, y))
    pts.append((side * 0.0, h - gutter_dip - 0.001))
    loop = pts if side < 0 else list(reversed(pts))
    return A.dedupe(loop) if hasattr(A, "dedupe") else loop


def open_ledger(prefix, centre, yaw, w=0.21, d=0.30, h=0.016, cover="M_Linen", seed=1):
    cx, cy, cz = centre
    objs = []
    # boards (cover) under each half and a rounded spine strip
    for side in (-1, 1):
        objs.append(F.gbox(f"{prefix}_board{side}", (min(0, side * (w + 0.008)), 0.0, -d / 2 - 0.006),
                           (max(0, side * (w + 0.008)), 0.0035, d / 2 + 0.006), mat=cover, bevel=0.0012))
        objs.append(F.gpoly(f"{prefix}_pages{side}", [page_loop(w, h, side)], d, (0.0, 0.0035, -d / 2), (1, 0, 0),
                            (0, 1, 0), mat="M_Paper", bevel=0.0))
    objs.append(F.gbox(f"{prefix}_spine", (-0.012, -0.0005, -d / 2 - 0.006), (0.012, 0.002, d / 2 + 0.006),
                       mat="M_Leather", bevel=0.001))
    # ruled entries: thin ink lines on the flat part of both pages
    rnd = random.Random(seed)
    verts, faces = [], []
    yl = 0.0035 + h + 0.0003
    for side in (-1, 1):
        x_in, x_out = 0.040, w - 0.022
        z = -d / 2 + 0.035
        while z < d / 2 - 0.030:
            frac = rnd.uniform(0.45, 1.0) if rnd.random() > 0.12 else rnd.uniform(0.15, 0.3)
            xa, xb = side * x_in, side * (x_in + (x_out - x_in) * frac)
            xa, xb = min(xa, xb), max(xa, xb)
            i = len(verts)
            verts += [(xa, yl, z), (xb, yl, z), (xb, yl, z + 0.0014), (xa, yl, z + 0.0014)]
            faces.append((i, i + 3, i + 2, i + 1))
            z += 0.0118
        # a ruled red margin line
        xm = side * (x_in - 0.008)
        i = len(verts)
        verts += [(xm - 0.0006, yl, -d / 2 + 0.02), (xm + 0.0006, yl, -d / 2 + 0.02), (xm + 0.0006, yl, d / 2 - 0.02),
                  (xm - 0.0006, yl, d / 2 - 0.02)]
        faces.append((i, i + 3, i + 2, i + 1))
    me = bpy.data.meshes.new(prefix + "_ink")
    me.from_pydata([tuple(G(*v)) for v in verts], [], faces)
    me.update()
    ink = bpy.data.objects.new(prefix + "_ink", me)
    bpy.context.scene.collection.objects.link(ink)
    M.assign(ink, "M_Bakelite")
    for p in me.polygons:
        if p.normal.z < 0:
            p.flip()
    objs.append(ink)
    for o in objs:
        F.bake_xform(o, yaw=yaw)
        o.location = G(cx, cy, cz)
        M.apply_transform(o)
    return objs


def closed_ledger(prefix, centre, yaw, w=0.24, d=0.32, h=0.045, cover="M_Book_Green"):
    cx, cy, cz = centre
    o = [F.gbox(f"{prefix}_cover", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), mat=cover, bevel=0.004),
         F.gbox(f"{prefix}_block", (-w / 2 + 0.004, 0.003, -d / 2 + 0.006), (w / 2 + 0.0005, h - 0.003, d / 2 - 0.006),
                mat="M_Paper", bevel=0.0008),
         F.gbox(f"{prefix}_corner_a", (-w / 2 - 0.0008, -0.0008, d / 2 - 0.035), (-w / 2 + 0.035, h + 0.0008, d / 2 + 0.0008),
                mat="M_Leather", bevel=0.0),
         F.gbox(f"{prefix}_corner_b", (-w / 2 - 0.0008, -0.0008, -d / 2 - 0.0008), (-w / 2 + 0.035, h + 0.0008,
                                                                                    -d / 2 + 0.035),
                mat="M_Leather", bevel=0.0),
         F.gbox(f"{prefix}_label", (-0.04, h, -0.025), (0.04, h + 0.0006, 0.025), mat="M_Paper", bevel=0.0)]
    for x in o:
        F.bake_xform(x, yaw=yaw)
        x.location = G(cx, cy, cz)
        M.apply_transform(x)
    return o


def magnifier_stand(prefix, base):
    bx, by, bz = base
    o = []
    o.append(F.glathe(f"{prefix}_foot", [(0.0, 0.0), (0.044, 0.0), (0.044, 0.006), (0.036, 0.012), (0.014, 0.016),
                                         (0.0, 0.017)], (bx, by, bz), segments=16, mat="M_Brass_Aged"))
    o.append(F.gcyl(f"{prefix}_post", 0.0045, 0.17, (bx, by + 0.016, bz), verts=10, mat="M_Brass_Aged", bevel=0.0))
    o.append(F.glathe2(f"{prefix}_knuckle", [(0.0, 0.0), (0.0075, 0.0), (0.0078, 0.003, "k"), (0.0078, 0.013, "k"),
                                             (0.0065, 0.016), (0.0, 0.016)], (bx, by + 0.180, bz - 0.009), axis="z",
                       segments=12, mat="M_Brass_Polished", knurl=0.0006))
    # lens ring on a short arm, tipped toward the front and down
    lc = (bx + 0.0, by + 0.155, bz + 0.065)
    o.append(F.gtube(f"{prefix}_arm", [(bx, by + 0.188, bz), (bx, by + 0.186, bz + 0.012)], 0.0035, sides=8,
                     mat="M_Brass_Aged"))
    ring = K.lathe2(f"{prefix}_ring", [(0.043, -0.004), (0.0475, -0.004), (0.0475, 0.004), (0.043, 0.004), (0.043, -0.004)],
                    segments=22, mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
    lens = M.cylinder(f"{prefix}_lens", 0.0435, 0.004, verts=22, mat="M_Glass", bevel=0.0)
    for x in (ring, lens):
        x.data.transform(Matrix.Rotation(math.radians(90 - 40), 4, "X"))
        x.location = G(*lc)
        M.apply_transform(x)
    o += [ring, lens]
    top = Vector(G(*lc)) + Matrix.Rotation(math.radians(90 - 40), 3, "X") @ Vector((0, 0.0475, 0))
    o.append(P.tube(f"{prefix}_fork", [G(bx, by + 0.186, bz + 0.012), top], 0.003, sides=6, mat="M_Brass_Aged"))
    return o


def build_dressing():
    d = []
    d += open_ledger("ledger_a", (-0.29, TOP, 0.09), -7.0, w=0.21, d=0.30, cover="M_Linen", seed=3)
    d += open_ledger("ledger_b", (0.28, TOP, -0.255), 6.0, w=0.15, d=0.22, h=0.012, cover="M_Book_Brown", seed=8)
    d += closed_ledger("ledger_c", (0.585, TOP, -0.215), 4.0, w=0.20, d=0.27, cover="M_Book_Green")
    d += closed_ledger("ledger_d", (0.588, TOP + 0.045, -0.222), -3.0, w=0.19, d=0.25, h=0.035, cover="M_Linen")
    d += magnifier_stand("magnifier", (-0.60, TOP, -0.26))
    parts["dressing"] = F.part("table_dressing", d)


def build():
    M.reset_scene()
    F.ensure_materials()
    build_table()
    build_lamp()
    build_dressing()
    F.finalize_all()
    return F.report(NAME)


REQUIRED = ["table", "banker_lamp", "lamp_shade", "bulb", "light_origin", "table_dressing"]


def main():
    total = build()
    path = F.export(NAME)
    errs = F.verify_glb(path, required=REQUIRED, identity=REQUIRED, budget=BUDGET, show=REQUIRED)
    bc = parts["bulb_c"]
    print(f"[reading_table] tris={total} errors={len(errs)} light_origin model=({bc[0]:.4f}, {bc[1]:.4f}, {bc[2]:.4f}) "
          f"world=({1.9 + bc[0]:.4f}, {bc[1]:.4f}, {1.0 + bc[2]:.4f})")
    if "--no-render" in ARGS:
        return
    qa()


def qa():
    F.qa_begin()
    F.qa_emit("M_Emissive_Warm", "FFD29A", 6.0)
    F.qa_room("reading")
    F.qa_place((1.9, 0.0, 1.0), 0.0)
    F.qa_neighbours([("chair", (1.55, 0.0, 1.62), 186.0), ("chair", (2.35, 0.0, 0.42), -8.0),
                     ("cc0/magnifying_glass_01/magnifying_glass_01", (2.25, 0.76, 1.12), 40.0),
                     ("cc0/round_spectacles/round_spectacles", (1.45, 0.76, 0.86), -25.0),
                     ("stacks_shelving", (0.0, 0.0, 0.25), 0.0), ("floor_hatch", (0.9, 0.0, 2.5), 0.0)])
    bc = parts["bulb_c"]
    F.qa_light("banker", "POINT", (1.9 + bc[0], bc[1], 1.0 + bc[2]), 25.0, "FFD29A", radius=0.02)
    F.qa_light("pendant_4", "POINT", (0.0, 2.75, 1.6), 120.0, "FFC58A", radius=0.1)
    F.qa_light("pendant_5", "POINT", (3.0, 2.75, 1.4), 120.0, "FFC58A", radius=0.1)
    M.refresh()
    if F.want("view", ARGS):
        F.shoot(NAME + "_2", (1.9, 1.6, 2.35), (1.9, 0.8, 1.0), vfov=52, world=0.10)
    if F.want("hero", ARGS):
        F.shoot(NAME, (3.15, 1.45, 2.05), (1.85, 0.62, 0.92), vfov=48, world=0.12)
    if F.want("lamp", ARGS):
        F.shoot(NAME + "_3", (2.15, 1.12, 1.35), (1.9, 0.96, 0.78), vfov=40, world=0.10)


main()
