"""room_cold.glb — R4 the Cold Store (Level -1), built directly in ROOM coordinates (origin = room origin, Godot axes).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3b/§7. "A cathedral made of shelves": a film cellar clad in galvanised insulating
panels, a segmental barrel vault with steel ribs over a bank of seven carriage slots, blue-white tube light, frost and breath.
Identity next to the other lower rooms: Pump Room = orange iron + rivets, Night Cell = amber wool + wallpaper, Cold Store = pale
blue-grey zinc, white enamel, frost, one red accent (the carriage cranks) and a lived-in parka.
Interior x [-3.8, 3.8], z [-3.4, 3.4]; floor y 0; side walls (E/W) are 3.0 high at the corners and the vault rises to 3.8 at z = 0
(y(z) = 3.0 + 0.8 (1 - (z / 3.55)^2)); N/S walls are 3.0 high. Walls 0.25 (W, N, S) / 0.30 (E) thick outside.
Openings:
  west   z [1.75, 2.65], y [0, 2.15]   the insulated door from the Night Cell (frame + gasket + PVC strip curtain here; the leaf is `cold_door`)
  east   z [1.72, 2.68], y [0.95, 2.31] the frost window (place `frost_window` at `window_mount`, yaw -90); a light well behind it
The carriage bank: seven slots of 1.00 m pitch at x = -3 .. +3 (`carriage_slot_0..6`, z centre -1.00, carriage z extent -2.60 .. 0.60); five
carriage_N models (origin = floor footprint centre) stand in five of them and slide along X. Floor rails (parts of `rails`) run along X
at z = -2.20 and z = +0.20, rail top y 0.025 (carriage wheels at z = rail). The back strip z -3.40 .. -2.60 holds the chest: seven
`chest_mount_0..6` at (x slot, 0, -3.14), yaw 0 (the chest faces +Z), so the chest is seen down any opened aisle.
Own objects: floor, wall_n, wall_s, wall_e, wall_w, ceiling, ribs, rails, lamps (7 strip fixtures with M_Emissive_Cold tubes), evaporator
(ceiling coil unit with fans, drip tray, icicles, insulated feed pipes: the Pump Room's `t` coil ends here), door_frame, strip_curtain,
dressing (gauge, crates, pallet, parka, skirting details, cam-lock strips), frost_patches, well (the light well behind the window),
window_glow (emissive plane, M_Emissive_Cold), plan_frame + plan_plate (quad 0.50 x 0.344, slot `M_Decal_PlanPlate`, UV 0..1, east wall).
Empties: carriage_slot_0..6, chest_mount_0..6, window_mount (3.845, 1.63, 2.20), door_mount (-3.80, 0, 2.20), light_cold_0..2
(2.9 above the aisles), light_window_fill (3.0, 1.6, 2.2), breath_origin (0, 1.55, 2.6) (where the player's breath mist can start).
    blender -b --factory-startup -P tools/blender/models/room_cold.py [-- --no-render]
"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "room_cold"
BUDGET = 16000
ARGS = M.main_guard()
X0, X1, Z0, Z1 = -3.8, 3.8, -3.4, 3.4
HW = 3.0                      # wall height at the corners
RISE = 0.8
TW, TE = 0.25, 0.30
GALV, ICE, CONC, DARK = "M_Steel_Galv", "M_Enamel_Ice", "M_Concrete", "M_Steel_Dark"
CARR_Z = -1.00
RAILS_Z = (CARR_Z - 1.20, CARR_Z + 1.20)
SLOTS = [-3.0 + i for i in range(7)]
grp = {}


def add(g, *o):
    grp.setdefault(g, []).extend(x for x in o if x is not None)


def vault_y(z: float) -> float:
    return HW + RISE * (1.0 - (z / 3.55) ** 2)


def prism_zy(name, pts, x0, x1, mat):
    """Extrude the convex (z, y) polygon along X from x0 to x1."""
    bm = bmesh.new()
    a = [bm.verts.new(G(x0, y, z)) for z, y in pts]
    b = [bm.verts.new(G(x1, y, z)) for z, y in pts]
    n = len(pts)
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return A.obj_from_bm(name, bm, mat)


def arch_pts(zs, y0=0.0):
    top = [(z, vault_y(z)) for z in zs]
    return [(zs[0], y0), (zs[-1], y0)] + list(reversed(top))[:]


def shell():
    # side walls (E/W) with the arched top
    zs = [Z0 + i * (Z1 - Z0) / 12 for i in range(13)]
    pts = [(zs[0], 0.0), (zs[-1], 0.0)] + [(z, vault_y(z)) for z in reversed(zs)]
    # N/S wall footprint is at the arch's ends: outer wall slabs as prisms
    we = prism_zy("wall_e", [(zs[0] - TW, 0.0), (zs[-1] + TW, 0.0)] + [(z, vault_y(z)) for z in reversed([zs[0] - TW] + zs + [zs[-1] + TW])],
                  X1, X1 + TE, GALV)
    ww = prism_zy("wall_w", [(zs[0] - TW, 0.0), (zs[-1] + TW, 0.0)] + [(z, vault_y(z)) for z in reversed([zs[0] - TW] + zs + [zs[-1] + TW])],
                  X0 - TW, X0, GALV)
    # openings
    X.cut(ww, "cut_door", (X0 - 0.4, 0.0, 1.75), (X0 + 0.1, 2.15, 2.65))
    X.cut(we, "cut_win", (X1 - 0.1, 0.95, 1.72), (X1 + TE + 0.1, 2.31, 2.68))
    add("wall_w", ww)
    add("wall_e", we)
    add("wall_n", gbox("wall_n", (X0 - TW, 0.0, Z0 - TW), (X1 + TE, HW + 0.05, Z0), GALV, bevel=0.0))
    add("wall_s", gbox("wall_s", (X0 - TW, 0.0, Z1), (X1 + TE, HW + 0.05, Z1 + TW), GALV, bevel=0.0))
    add("floor", gbox("floor", (X0 - TW, -0.2, Z0 - TW), (X1 + TE, 0.0, Z1 + TW), CONC, bevel=0.0))
    # barrel-vault underside: a lofted strip along X (panel colour), thin slab above is not needed (never seen)
    bm = bmesh.new()
    zz = [Z0 - TW + i * ((Z1 + TW) - (Z0 - TW)) / 16 for i in range(17)]
    r0 = [bm.verts.new(G(X0 - TW, vault_y(z), z)) for z in zz]
    r1 = [bm.verts.new(G(X1 + TE, vault_y(z), z)) for z in zz]
    for i in range(16):
        bm.faces.new((r0[i], r1[i], r1[i + 1], r0[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    cv = A.obj_from_bm("ceiling", bm, GALV)
    # the underside must face down (Blender -Z up axis): flip when the mean normal points up
    if sum(p.normal.z for p in cv.data.polygons) > 0:
        for p in cv.data.polygons:
            p.flip()
        cv.data.update()
    add("ceiling", cv)
    # N/S wall caps above 3.0 up to the vault (the vault rises only towards z = 0, N/S walls are 3.0 at z = +-3.4; y(z=3.4)=3.0+0.8*(1-0.917)=3.066)
    # -> raise the N/S walls slightly: handled by HW + 0.05 above.


def panels():
    """Insulating-panel look: vertical lap strips, a cam-lock strip at 1.10, kick plate, ceiling ribs."""
    # E/W: strips along z (every 0.6), N/S: strips along x
    for k in range(-5, 6):
        z = k * 0.6
        if True:
            for xw, sgn in ((X0, 1), (X1, -1)):
                if xw == X0 and 1.60 < z < 2.80:
                    continue
                if xw == X1 and 1.50 < z < 2.90:
                    continue
                add("wall_e" if sgn < 0 else "wall_w", gbox("strip", (xw if sgn > 0 else xw - 0.016, 0.12, z - 0.025) if sgn > 0 else (xw - 0.016, 0.12, z - 0.025),
                                                            (xw + 0.016 if sgn > 0 else xw, 2.96, z + 0.025), ICE, bevel=0.0))
    for k in range(-6, 7):
        x = k * 0.6
        add("wall_n", gbox("stripn", (x - 0.025, 0.12, Z0), (x + 0.025, 2.98, Z0 + 0.016), ICE, bevel=0.0))
        add("wall_s", gbox("strips", (x - 0.025, 0.12, Z1 - 0.016), (x + 0.025, 2.98, Z1), ICE, bevel=0.0))
    # kick plates (white enamel) and cam-lock horizontal bars
    add("wall_n", gbox("kick_n", (X0, 0.0, Z0), (X1, 0.12, Z0 + 0.022), ICE, bevel=0.0), gbox("cam_n", (X0, 1.10, Z0), (X1, 1.135, Z0 + 0.012), DARK, bevel=0.0))
    add("wall_s", gbox("kick_s", (X0, 0.0, Z1 - 0.022), (X1, 0.12, Z1), ICE, bevel=0.0), gbox("cam_s", (X0, 1.10, Z1 - 0.012), (X1, 1.135, Z1), DARK, bevel=0.0))
    add("wall_w", gbox("kick_w", (X0, 0.0, Z0), (X0 + 0.022, 0.12, 1.75), ICE, bevel=0.0), gbox("kick_w2", (X0, 0.0, 2.65), (X0 + 0.022, 0.12, Z1), ICE, bevel=0.0),
        gbox("cam_w", (X0, 1.10, Z0), (X0 + 0.012, 1.135, 1.75), DARK, bevel=0.0), gbox("cam_w2", (X0, 1.10, 2.65), (X0 + 0.012, 1.135, Z1), DARK, bevel=0.0))
    add("wall_e", gbox("kick_e", (X1 - 0.022, 0.0, Z0), (X1, 0.12, Z1), ICE, bevel=0.0), gbox("cam_e", (X1 - 0.012, 1.10, Z0), (X1, 1.135, 1.72), DARK, bevel=0.0),
        gbox("cam_e2", (X1 - 0.012, 1.10, 2.68), (X1, 1.135, Z1), DARK, bevel=0.0))
    # vault ribs at every slot boundary (x = -3.5 .. 3.5) following the curve: short boxes along the arc
    zs = [Z0 + i * (Z1 - Z0) / 10 for i in range(11)]
    for x in [-3.5 + i for i in range(8)]:
        for a, b in zip(zs[:-1], zs[1:]):
            ya, yb = vault_y(a) - 0.02, vault_y(b) - 0.02
            ln = math.hypot(b - a, yb - ya)
            seg = M.box("rib", (0.05, ln + 0.01, 0.22), loc=(0, 0, 0), mat=ICE, bevel=0.0, segments=1)
            A.place(seg, Matrix.Identity(4))
            # box local: x thickness, y length, z depth (Blender); orient length along the (z,y) chord in Godot axes
            seg.data.transform(Matrix.Rotation(math.atan2(yb - ya, -(b - a)), 4, "X"))
            seg.data.transform(Matrix.Translation(G(x, (ya + yb) / 2 - 0.09, (a + b) / 2)))
            add("ribs", seg)
        add("ribs", gbox("rib_foot", (x - 0.07, 2.70, Z0), (x + 0.07, 3.10, Z0 + 0.03), ICE, bevel=0.0),
            gbox("rib_foot2", (x - 0.07, 2.70, Z1 - 0.03), (x + 0.07, 3.10, Z1), ICE, bevel=0.0))


def rails():
    for rz in RAILS_Z:
        add("rails", gbox("rail_bed", (X0, 0.0, rz - 0.07), (X1, 0.012, rz + 0.07), DARK, bevel=0.0),
            gbox("rail", (X0 + 0.15, 0.012, rz - 0.028), (X1 - 0.15, 0.025, rz + 0.028), "M_Chrome", bevel=0.0))
        for sx in (-1, 1):
            add("rails", gbox("stop", (sx * 3.62 - 0.06 if sx < 0 else sx * 3.62 - 0.06, 0.0, rz - 0.06), (sx * 3.62 + 0.06, 0.12, rz + 0.06), "M_Enamel_Crimson", bevel=0.0))
        # sleepers
        for k in range(-7, 8):
            add("rails", gbox("sleeper", (k * 0.5 - 0.03, 0.0, rz - 0.085), (k * 0.5 + 0.03, 0.006, rz + 0.085), DARK, bevel=0.0))


def lamps():
    for i, x in enumerate(SLOTS):
        y = 3.12
        add("lamps", gbox(f"fx{i}", (x - 0.10, y, CARR_Z - 0.85), (x + 0.10, y + 0.07, CARR_Z + 0.85), ICE, bevel=0.0),
            gbox(f"tube{i}", (x - 0.07, y - 0.012, CARR_Z - 0.80), (x + 0.07, y, CARR_Z + 0.80), "M_Emissive_Cold", bevel=0.0))
        for dz in (-0.55, 0.55):
            add("lamps", gbox(f"rod{i}{dz}", (x - 0.008, y + 0.07, CARR_Z + dz - 0.008), (x + 0.008, vault_y(CARR_Z + dz) - 0.02, CARR_Z + dz + 0.008), DARK, bevel=0.0))
    for k, x in enumerate((-2.0, 0.0, 2.0)):
        mount(f"light_cold_{k}", (x, 2.95, CARR_Z))


def evaporator():
    ex0, ex1, ey0, ey1, ez0, ez1 = -2.6, -0.7, 2.50, 3.10, -3.35, -2.70
    e = [gbox("ev_body", (ex0, ey0, ez0), (ex1, ey1, ez1), ICE, bevel=0.0),
         gbox("ev_tray", (ex0 - 0.03, ey0 - 0.05, ez0), (ex1 + 0.03, ey0, ez1 + 0.05), GALV, bevel=0.0),
         gbox("ev_lip", (ex0 - 0.03, ey0 - 0.05, ez1 + 0.03), (ex1 + 0.03, ey0 + 0.02, ez1 + 0.05), GALV, bevel=0.0)]
    for k, fx in enumerate((-2.15, -1.15)):
        e.append(glathe(f"fan_ring{k}", [(0.205, 0.0), (0.225, 0.0), (0.225, 0.04), (0.205, 0.04)], (fx, 2.80, ez1), axis="z", segments=20, mat=DARK))
        e.append(glathe(f"fan_hub{k}", [(0.0, 0.0), (0.045, 0.0), (0.045, 0.05), (0.0, 0.055)], (fx, 2.80, ez1), axis="z", segments=10, mat=DARK))
        for b in range(5):
            a = 2 * math.pi * b / 5 + 0.3
            e.append(gcyl(f"fs{k}{b}", 0.004, 0.20, (fx, 2.80, ez1 + 0.02), axis=(math.cos(a), math.sin(a), 0.0), verts=4, mat=DARK, bevel=0.0))
        e.append(glathe(f"fan_in{k}", [(0.19, 0.0), (0.2, 0.0), (0.2, 0.02), (0.19, 0.02)], (fx, 2.80, ez1 + 0.01), axis="z", segments=14, mat=DARK))
    # hanger rods to the ceiling
    for x in (ex0 + 0.12, ex1 - 0.12):
        e.append(gbox("ev_rod", (x - 0.012, ey1, ez0 + 0.05), (x + 0.012, vault_y(-3.2) - 0.02, ez0 + 0.08), DARK, bevel=0.0))
    # the insulated feed pipe: from the north wall corner (Pump-Room line `t`) into the unit
    e.append(X.pipe("feed_a", [(ex0 - 0.5, 2.62, ez0 + 0.12), (ex0, 2.62, ez0 + 0.12)], 0.045, mat="M_Porcelain", sides=10, flange_ends=True, flange_r=0.075, flange_mat=DARK))
    e.append(X.pipe("feed_b", [(X0, 2.62, ez0 + 0.12), (ex0 - 0.5, 2.62, ez0 + 0.12)], 0.045, mat="M_Porcelain", sides=10, flange_ends=False))
    e.append(gcyl("valve", 0.05, 0.12, (ex0 - 0.95, 2.62, ez0 + 0.12 - 0.06), axis="z", verts=10, mat="M_Brass_Aged", bevel=0.0))
    e.append(gbox("valve_box", (ex0 - 1.15, 2.57, ez0 + 0.06), (ex0 - 0.85, 2.76, ez0 + 0.12 + 0.07), DARK, bevel=0.0))
    for k, (ix, il) in enumerate(((-2.45, 0.22), (-2.1, 0.12), (-1.8, 0.28), (-1.4, 0.16), (-1.0, 0.24), (-0.8, 0.10))):
        e.append(gcyl(f"ice{k}", 0.014, il, (ix, ey0 - 0.05 - il, ez1 + 0.02), axis="y", verts=5, mat="M_Frost", bevel=0.0, r_top=0.003))
    # frost bloom on the front of the coil casing (flat lumps) and an ice mound on the floor below (drip)
    e.append(K.frost_crust("ev_frost", [((-1.65, 3.02, ez1 + 0.005), 0.55, 0.012, "z"), ((-2.45, 2.75, ez1 + 0.005), 0.12, 0.010, "z"), ((-0.85, 2.7, ez1 + 0.005), 0.10, 0.010, "z")],
                           seed=11, sides=6))
    add("evaporator", *e)
    # stalagmites of dripped ice under the unit (tapered 6-sided cones, frosted glass)
    ice = [gcyl(f"stal{k}", r, h, (x, 0.0, z), axis="y", verts=6, mat="M_Frost", bevel=0.0, r_top=0.012)
           for k, (x, z, r, h) in enumerate(((-1.65, -2.98, 0.075, 0.30), (-1.50, -2.90, 0.050, 0.17), (-1.82, -3.05, 0.045, 0.14), (-1.40, -3.08, 0.040, 0.11)))]
    add("frost_patches", *ice)
    mount("evaporator_mount", (-1.65, 2.8, -2.7))


def door_and_window():
    # insulated door frame (dark steel jambs and head, rubber gasket) on the west wall; the leaf belongs to the Night Cell
    f = [gbox("dj_n", (X0 - 0.02, 0.0, 1.64), (X0 + 0.10, 2.27, 1.75), DARK, bevel=0.0), gbox("dj_s", (X0 - 0.02, 0.0, 2.65), (X0 + 0.10, 2.27, 2.76), DARK, bevel=0.0),
         gbox("dh", (X0 - 0.02, 2.15, 1.64), (X0 + 0.10, 2.27, 2.76), DARK, bevel=0.0),
         gbox("gasket_n", (X0 + 0.0, 0.0, 1.75), (X0 + 0.045, 2.15, 1.78), "M_Rubber", bevel=0.0), gbox("gasket_s", (X0 + 0.0, 0.0, 2.62), (X0 + 0.045, 2.15, 2.65), "M_Rubber", bevel=0.0),
         gbox("gasket_h", (X0 + 0.0, 2.12, 1.75), (X0 + 0.045, 2.15, 2.65), "M_Rubber", bevel=0.0),
         gbox("threshold", (X0 - 0.10, 0.0, 1.75), (X0 + 0.14, 0.03, 2.65), "M_Chequer", bevel=0.0)]
    # emergency release knob (cold-room safety): red mushroom on the inside of the jamb
    f.append(gcyl("rel_stem", 0.012, 0.05, (X0 + 0.10, 1.05, 2.82), axis="x", verts=8, mat=DARK, bevel=0.0))
    f.append(glathe("rel_knob", [(0.0, 0.0), (0.035, 0.0), (0.04, 0.012), (0.03, 0.03), (0.0, 0.034)], (X0 + 0.15, 1.05, 2.82), axis="x", segments=14, mat="M_Enamel_Crimson"))
    f.append(gbox("rel_plate", (X0 + 0.0, 0.92, 2.78), (X0 + 0.02, 1.18, 2.86), DARK, bevel=0.0))
    add("door_frame", *f)
    # PVC strip curtain inside the door (just in front of the opening)
    s = [gbox("curtain_bar", (X0 + 0.28, 2.15, 1.72), (X0 + 0.32, 2.19, 2.68), DARK, bevel=0.0)]
    for k in range(9):
        z = 1.77 + k * 0.1
        s.append(gbox(f"strip{k}", (X0 + 0.295 + 0.004 * (k % 2), 0.05, z + 0.006), (X0 + 0.301 + 0.004 * (k % 2), 2.15, z + 0.096), "M_Frost", bevel=0.0))
    add("strip_curtain", *s)
    # light well behind the window: shaft box and the glow plane
    w = [gbox("well_top", (X1 + TE, 2.31, 1.72), (X1 + TE + 1.0, 2.40, 2.68), CONC, bevel=0.0), gbox("well_bot", (X1 + TE, 0.85, 1.72), (X1 + TE + 1.0, 0.95, 2.68), CONC, bevel=0.0),
         gbox("well_n", (X1 + TE, 0.85, 1.62), (X1 + TE + 1.0, 2.40, 1.72), CONC, bevel=0.0), gbox("well_s", (X1 + TE, 0.85, 2.68), (X1 + TE + 1.0, 2.40, 2.78), CONC, bevel=0.0)]
    add("well", *w)
    glow = K.quad_decal("window_glow", (X1 + TE + 0.98, 1.62, 2.20), (0, 0, 1), (0, 1, 0), 0.96, 1.4, "M_Emissive_Cold")
    glow = part("window_glow", [glow], (X1 + TE + 0.98, 1.62, 2.20), presmooth=False)
    mount("window_mount", (3.845, 1.63, 2.20))
    mount("door_mount", (X0, 0.0, 2.20))
    mount("light_window_fill", (3.0, 1.6, 2.2))
    return glow


def plan_plate():
    # framed plan plate on the east wall south of the carriages (rail-end view)
    px, pz, py = X1, 1.00, 1.55
    fr = [gbox("pf_t", (px - 0.03, py + 0.19, pz - 0.28), (px, py + 0.215, pz + 0.28), DARK, bevel=0.0), gbox("pf_b", (px - 0.03, py - 0.215, pz - 0.28), (px, py - 0.19, pz + 0.28), DARK, bevel=0.0),
          gbox("pf_n", (px - 0.03, py - 0.215, pz - 0.28), (px, py + 0.215, pz - 0.255), DARK, bevel=0.0), gbox("pf_s", (px - 0.03, py - 0.215, pz + 0.255), (px, py + 0.215, pz + 0.28), DARK, bevel=0.0),
          gbox("pf_back", (px - 0.012, py - 0.19, pz - 0.255), (px, py + 0.19, pz + 0.255), "M_Steel_Dark", bevel=0.0)]
    add("plan_frame", *fr)
    q = K.quad_decal("plan_plate", (px - 0.0125, py, pz), (0, 0, 1), (0, 1, 0), 0.50, 0.344, "M_Decal_PlanPlate")
    q = part("plan_plate", [q], (px - 0.0125, py, pz), presmooth=False)
    return q


def dressing():
    d = []
    # thermometer gauge on the north wall by the chest strip
    gb, nd = X.gauge("gauge_cold", (3.0, 1.7, Z0 + 0.012), r=0.09, axis="z")
    # gauge faces +Z; the needle is a separate object: fold it into the static dressing (rest at 225 deg)
    d.append(gb)
    d.append(nd)
    d.append(gbox("gauge_plate", (2.80, 1.50, Z0), (3.20, 1.90, Z0 + 0.012), DARK, bevel=0.0))
    # crate stack and a pallet near the south-east corner
    d.append(gbox("pal_a", (2.4, 0.0, 2.55), (3.4, 0.10, 3.3), "M_Wood_Panel", bevel=0.0))
    for j in range(3):
        d.append(gbox(f"pal_b{j}", (2.4, 0.10, 2.55 + j * 0.32), (3.4, 0.14, 2.55 + j * 0.32 + 0.18), "M_Wood_Panel", bevel=0.0))
    d.append(gbox("crate1", (2.5, 0.14, 2.65), (3.2, 0.62, 3.2), "M_Wood_Walnut", bevel=0.0))
    d.append(gbox("crate1_band", (2.5, 0.34, 2.65), (3.2, 0.38, 3.2), DARK, bevel=0.0))
    d.append(gbox("crate2", (2.62, 0.62, 2.75), (3.12, 1.0, 3.15), "M_Cardboard", bevel=0.0))
    d.append(gbox("crate2_band", (2.62, 0.78, 2.75), (3.12, 0.80, 3.15), "M_Paper", bevel=0.0))
    # a parka on a peg near the door (Leyla's: red wool, quilted, hood): flat torso and skirt against the wall, hanging sleeves, hood behind the neck
    pz = 3.0
    d.append(gbox("peg_board", (X0, 1.70, 2.84), (X0 + 0.03, 2.00, 3.16), "M_Wood_Panel", bevel=0.0))
    d.append(gcyl("peg", 0.012, 0.12, (X0 + 0.03, 1.88, pz), axis="x", verts=8, mat="M_Brass_Aged", bevel=0.0))
    d.append(gbox("parka_torso", (X0 + 0.05, 1.28, pz - 0.20), (X0 + 0.20, 1.86, pz + 0.20), "M_Wool_Knit", bevel=0.01))
    d.append(gbox("parka_skirt", (X0 + 0.05, 0.92, pz - 0.23), (X0 + 0.21, 1.30, pz + 0.23), "M_Wool_Knit", bevel=0.01))
    for sz in (-1, 1):
        d.append(gbox("parka_sleeve", (X0 + 0.07, 1.10, pz + sz * 0.20 - (0.0 if sz > 0 else 0.11)),
                      (X0 + 0.19, 1.84, pz + sz * 0.20 + (0.11 if sz > 0 else 0.0)), "M_Wool_Knit", bevel=0.012))
    d.append(M.sphere("hood", 0.11, loc=G(X0 + 0.10, 1.84, pz), segments=8, rings=5, mat="M_Wool_Knit", scale=(0.8, 1.0, 1.05)))
    d.append(gbox("parka_belt", (X0 + 0.045, 1.24, pz - 0.215), (X0 + 0.215, 1.29, pz + 0.215), "M_Leather", bevel=0.0))
    # tall steel waste/ice-scraper stand and a squeegee beside the window: a hint of the cloth beat (a bucket and a hook)
    d.append(glathe("pail", [(0.0, 0.0), (0.11, 0.0), (0.14, 0.26), (0.15, 0.28), (0.0, 0.28)], (3.3, 0.0, 1.2), axis="y", segments=14, mat=GALV))
    d.append(gbox("hook_rail", (X1 - 0.03, 1.60, 0.40), (X1, 1.64, 0.62), DARK, bevel=0.0))
    # ceiling: a hose coil hanging from the first rib? no. A fire extinguisher by the window
    d.append(glathe("extinguisher", [(0.0, 0.0), (0.06, 0.0), (0.075, 0.03), (0.075, 0.38), (0.04, 0.45), (0.0, 0.46)], (3.55, 0.45, 0.55), axis="y", segments=12, mat="M_Enamel_Crimson"))
    d.append(gbox("ext_bracket", (3.50, 0.80, 0.50), (3.80, 0.84, 0.60), DARK, bevel=0.0))
    # floor drain by the door
    d.append(gbox("drain", (-3.0, 0.0, 3.0), (-2.5, 0.012, 3.25), DARK, bevel=0.0))
    for k in range(6):
        d.append(gbox(f"drb{k}", (-2.97 + k * 0.083, 0.012, 3.02), (-2.97 + k * 0.083 + 0.035, 0.02, 3.23), "M_Steel_Dark", bevel=0.0))
    add("dressing", *d)
    # frost: hoar patches on the floor along the walls and window sill zone, chest strip rime
    patches()
    mount("breath_origin", (0.0, 1.55, 2.6))
    for i, x in enumerate(SLOTS):
        mount(f"carriage_slot_{i}", (x, 0.0, CARR_Z))
        mount(f"chest_mount_{i}", (x, 0.0, -3.14))


def patches():
    """Hoar-frost blotches (soft-edged alpha quads, slot M_Decal_FrostPatch) on walls and floor; they float 1.8 cm off the panel strips."""
    off = 0.018
    P = []
    # (face, a, b, size): face n/s/e/w -> (x or z along, y); f -> (x, z) on the floor
    for a, b, sz in ((-1.7, 2.3, 1.3), (-3.5, 0.7, 0.9), (3.4, 0.5, 0.8), (0.0, 0.5, 1.0), (1.6, 0.4, 0.8), (-0.6, 2.6, 0.7)):
        P.append(("n", a, b, sz))
    for a, b, sz in ((-2.9, 0.5, 0.9), (0.4, 0.35, 0.8), (2.2, 2.65, 0.8), (-3.1, 0.3, 0.7)):
        P.append(("w", a, b, sz))
    for a, b, sz in ((3.15, 2.75, 0.7), (0.3, 0.4, 0.8), (3.05, 0.4, 0.7), (-1.5, 2.5, 0.8), (-0.9, 0.35, 0.8)):
        P.append(("e", a, b, sz))
    for a, b, sz in ((-3.0, 0.45, 0.9), (1.8, 0.3, 1.0), (-0.4, 1.9, 0.8)):
        P.append(("s", a, b, sz))
    for a, b, sz in ((-1.7, -3.0, 1.5), (-3.3, -1.0, 1.1), (3.2, -1.0, 1.0), (0.0, 3.1, 1.3), (3.3, 0.9, 0.9), (-3.2, 3.1, 1.0), (1.2, -3.2, 1.1)):
        P.append(("f", a, b, sz))
    for k, (f, a, b, sz) in enumerate(P):
        if f == "n":
            q = K.quad_decal(f"fp{k}", (a, b, Z0 + off), (1, 0, 0), (0, 1, 0), sz, sz, "M_Decal_FrostPatch")
        elif f == "s":
            q = K.quad_decal(f"fp{k}", (a, b, Z1 - off), (-1, 0, 0), (0, 1, 0), sz, sz, "M_Decal_FrostPatch")
        elif f == "e":
            q = K.quad_decal(f"fp{k}", (X1 - off, b, a), (0, 0, 1), (0, 1, 0), sz, sz, "M_Decal_FrostPatch")
        elif f == "w":
            q = K.quad_decal(f"fp{k}", (X0 + off, b, a), (0, 0, -1), (0, 1, 0), sz, sz, "M_Decal_FrostPatch")
        else:
            q = K.quad_decal(f"fp{k}", (a, 0.006, b), (1, 0, 0), (0, 0, -1), sz, sz, "M_Decal_FrostPatch")
        add("frost_decals", q)


def main():
    X.begin()
    K.decal_alpha("M_Decal_FrostPatch", "frost_patch.png")
    K.decal_alpha("M_Decal_FrostSign", "frost_sign_0.png")
    X.decal("M_Decal_PlanPlate", "plan_plate.png")
    shell()
    panels()
    rails()
    lamps()
    evaporator()
    glow = door_and_window()
    plan = plan_plate()
    dressing()
    for k, v in grp.items():
        X.top(v, 4)
    objs = {}
    for g, lst in grp.items():
        objs[g] = X.join_all(g, lst)
        objs[g].name = g
        objs[g].data.name = g
        M.set_origin(objs[g], G(0, 0, 0))
    return glow, plan


if __name__ == "__main__":
    glow, plan = main()
    req = ["floor", "wall_n", "wall_s", "wall_e", "wall_w", "ceiling", "ribs", "rails", "lamps", "evaporator", "door_frame", "strip_curtain", "dressing",
           "frost_patches", "frost_decals", "well", "window_glow", "plan_frame", "plan_plate", "window_mount", "door_mount", "carriage_slot_0", "carriage_slot_6",
           "chest_mount_0", "chest_mount_6", "light_cold_0", "light_window_fill", "breath_origin", "evaporator_mount"]
    X.C.finalize_all(wood_grain=True)
    total = X.C.report(NAME)
    path = X.C.export(NAME)
    errs = X.C.verify_glb(path, required=req, identity=["plan_plate", "window_glow"], budget=BUDGET, show=["plan_plate", "window_mount"])
    print(f"{X.TAG} {NAME}: tris={total} errors={len(errs)}")
