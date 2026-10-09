"""shell_nursery.glb — the Nursery shell (Leyla's crystal-growing wing) and the walls of her 1998 camp, in WORLD
coordinates (place at the origin, yaw 0). Contract: docs/models/ch3.md §3 shell_nursery (+ §1.1, §1.4 portal_e_n,
§1.5 lights, §2 views); results: docs/models/ch3_a.md.

Interior x ∈ [4.5, 13.0], z ∈ [-4.0, 4.0], y ∈ [0, 4.0]. The camp: x ∈ [4.5, 7.6], z ∈ [-4.0, -1.2], y ∈ [0, 2.9];
its south wall z ∈ [-1.2, -1.05], east wall x ∈ [7.6, 7.75], roof slab y 2.9 .. 3.0.

  nursery_walls    glazed tiles to the ceiling (coved skirting tile, a moulded tile course) on the Nursery side of the
                   north, east, south and west walls; openings: the east-door tunnel mouth (west wall |z| <= 0.8,
                   y <= 2.4) and the lobby passage (south wall x 4.8 .. 6.3, y <= 2.6)
  nursery_floor    linoleum, without the camp area
  nursery_ceiling  cream steel ceiling panels in a T-bar grid, the five fluorescent fitting bodies, pipe hangers
  nursery_pipes    frosted, lagged pipes along the north wall at y 2.6 .. 3.2 dropping to each of the four autoclaves
  camp_walls       (groups N and K) the camp's cream steel partitions (both faces, with the doorway x 5.6 .. 6.6,
                   y <= 2.12), the roof slab, the camp's worn linoleum floor patch, and the tiled camp-side faces of the
                   room's north and west walls with the shutter opening (z -3.15 .. -2.05, y 0.30 .. 2.10)
  lamp_glass_0..4  fluorescent diffusers at y 3.9: (9.3, -2.2), (12.0, -2.2), (6.0, 1.6), (9.3, 1.6), (12.0, 1.6);
                   empties light_nursery_0..4
  portal_e_n       (3.75, 1.2, 0), +Z toward -X (the Gallery)

    blender -b --factory-startup -P tools/blender/models/shell_nursery.py [-- --no-render] [--shots=1,2,...]
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
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_nursery"
TRI_BUDGET, SURF_BUDGET = 14000, 12
TILE, LINO, CREAM, FROST = K.TILE, K.LINO, K.CREAM_STEEL, K.FROST
X0, X1, Z0, Z1, H = 4.5, 13.0, -4.0, 4.0, 4.0
DOOR_Z, DOOR_H = 0.8, 2.4
PASS = (4.8, 6.3)
PASS_H = 2.6
CAMP = (4.5, 7.6, -4.0, -1.2)          # interior x0, x1, z0, z1
CAMP_SZ = (-1.2, -1.05)                # south wall z range
CAMP_EX = (7.6, 7.75)                  # east wall x range
CAMP_H, ROOF_T = 2.9, 0.1
CAMP_DOOR = (5.6, 6.6, 2.12)
SHUT = (-3.15, -2.05, 0.30, 2.10)
LAMPS = [(9.3, -2.2), (12.0, -2.2), (6.0, 1.6), (9.3, 1.6), (12.0, 1.6)]
LAMP_Y = 3.9
AUTOCLAVES = [8.4, 9.65, 10.9, 12.15]
TILE_PROFILE = [(-0.035, 0.0), (-0.03, 0.012), (-0.018, 0.03), (-0.006, 0.06), (0.0, 0.10), (0.0, 1.185),
                (-0.012, 1.195), (-0.014, 1.22), (-0.012, 1.245), (0.0, 1.255), (0.0, DOOR_H), (0.0, PASS_H), (0.0, H)]


# ====================================================================== walls / floor / ceiling
def nursery_walls():
    path = [(CAMP_EX[1], Z0), (X1, Z0), (X1, Z1), (PASS[1], Z1), (PASS[0], Z1), (X0, Z1), (X0, DOOR_Z), (X0, -DOOR_Z),
            (X0, CAMP_SZ[1])]
    w = K.wall_sweep("walls", path, TILE_PROFILE, TILE, closed=False)

    def opening(c, n):
        if c.x < X0 + 0.1 and abs(c.z) < DOOR_Z and c.y < DOOR_H:
            return True
        return c.z > Z1 - 0.1 and PASS[0] < c.x < PASS[1] and c.y < PASS_H
    K.delete_faces_where(w, opening)
    return K.part("nursery_walls", [w])


def nursery_floor():
    outline = [(X0, CAMP_SZ[1]), (CAMP_EX[1], CAMP_SZ[1]), (CAMP_EX[1], Z0), (X1, Z0), (X1, Z1), (X0, Z1)]
    return K.part("nursery_floor", [K.flat_poly("floor", outline, [], 0.0, LINO, up=True)])


def fitting_body(x, z):
    """Cream steel fluorescent fitting (housing + end caps + suspension) under the ceiling."""
    out = [K.gbox("fhouse", (x - 0.64, LAMP_Y + 0.035, z - 0.13), (x + 0.64, LAMP_Y + 0.085, z + 0.13), CREAM, 0.012)]
    for sx in (-1, 1):
        out.append(K.gbox("fcap", (x + sx * 0.62 - 0.02, LAMP_Y - 0.035, z - 0.11), (x + sx * 0.62 + 0.02, LAMP_Y + 0.04, z + 0.11),
                          CREAM, 0.006))
        out.append(K.gcyl("frod", 0.006, LAMP_Y + 0.085, H, base=(x + sx * 0.45, 0, z), axis=(0, 1, 0), segments=4, mat=CREAM,
                          caps=False))
    return out


def lamp_glass(k, x, z):
    """Opal diffuser: a rounded prismatic section along x (lamp_glass_k)."""
    prof = [(-0.10, 0.035), (-0.10, 0.0), (-0.075, -0.035), (0.075, -0.035), (0.10, 0.0), (0.10, 0.035)]
    bm = bmesh.new()
    rings = []
    for xx in (x - 0.60, x + 0.60):
        rings.append([bm.verts.new((xx, LAMP_Y + py, z + pz)) for (pz, py) in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rings[0][i], rings[1][i], rings[1][i + 1], rings[0][i + 1]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = K.obj_from_bm("diffuser", bm, FROST)
    return K.part(f"lamp_glass_{k}", [o], pivot=(x, LAMP_Y, z))


def nursery_ceiling():
    outline = [(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)]
    parts = [K.flat_poly("ceil", outline, [], H, CREAM, up=False)]
    # T-bar grid (1.2 x 0.6 panels) a little below the panels
    xs = [X0 + 0.25 + 1.2 * k for k in range(8) if X0 + 0.25 + 1.2 * k < X1]
    zs = [Z0 + 0.6 * k for k in range(1, 14)]
    for x in xs:
        parts.append(K.gbox("tbar", (x - 0.012, H - 0.018, Z0), (x + 0.012, H, Z1), CREAM, 0.0))
    for z in zs:
        parts.append(K.gbox("tbar", (X0, H - 0.018, z - 0.012), (X1, H, z + 0.012), CREAM, 0.0))
    for (x, z) in LAMPS:
        parts += fitting_body(x, z)
    # pipe hangers from the ceiling down to the mains (north wall)
    for x in [8.0 + 1.25 * k for k in range(5)]:
        parts.append(K.gcyl("hanger", 0.008, 2.55, H, base=(x, 0, -3.70), axis=(0, 1, 0), segments=4, mat=CREAM, caps=False))
        parts.append(K.gbox("hstrap", (x - 0.025, 2.53, -3.92), (x + 0.025, 2.56, -3.50), CREAM, 0.004))
    return K.part("nursery_ceiling", parts)


def nursery_pipes():
    parts = []
    mains = [(2.66, -3.82, 0.075), (2.92, -3.80, 0.065), (3.14, -3.84, 0.055)]
    for (y, z, r) in mains:
        parts.append(K.V.tube("main", [(CAMP_EX[1], y, z), (X1, y, z)], r, sides=10, mat=FROST))
        for x in [8.1 + 0.62 * k for k in range(8)]:      # lagging bands / frost rings
            ring = M.torus("band", r + 0.004, 0.009, major_seg=10, minor_seg=4, mat=FROST)
            ring.data.transform(Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
            parts.append(ring)
    # drops to the autoclaves' domes (vessel centre z -3.5, dome top y 2.10)
    for x in AUTOCLAVES:
        pts = [(x, 2.66, -3.82), (x, 2.66, -3.50), (x, 2.13, -3.50)]
        parts.append(K.V.tube("drop", pts, 0.05, sides=10, mat=FROST, fillet=0.12))
        parts.append(K.glathe("dflange", [(0.0, 0.0), (0.085, 0.0), (0.085, 0.03), (0.0, 0.03)], (x, 2.30, -3.50), (0, 1, 0),
                              10, FROST, smooth=40.0))
        # a frozen hand valve on the drop
        parts.append(K.glathe("vbody", [(0.0, -0.06), (0.065, -0.05), (0.07, 0.0), (0.065, 0.05), (0.0, 0.06)],
                              (x, 2.66, -3.66), (0, 0, 1), 10, FROST, smooth=50.0))
        wheel = M.torus("vwheel", 0.07, 0.01, major_seg=12, minor_seg=4, mat=FROST)
        wheel.data.transform(Matrix.Translation((x, 2.80, -3.66)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
        parts.append(wheel)
        parts.append(K.gcyl("vstem", 0.01, 2.70, 2.80, base=(x, 0, -3.66), axis=(0, 1, 0), segments=4, mat=FROST, caps=False))
    for p in parts:
        A.hint(p, 50.0)
    return K.part("nursery_pipes", parts)


# ====================================================================== camp walls (groups N + K)
def camp_walls():
    cx0, cx1, cz0, cz1 = CAMP
    p = []
    sz0, sz1 = CAMP_SZ
    ex0, ex1 = CAMP_EX
    d0, d1, dh = CAMP_DOOR
    # south partition: two panels either side of the doorway + the head above it
    for (a, b) in ((cx0, d0), (d1, ex1)):
        p.append(K.gbox("sp", (a, 0.0, sz0), (b, CAMP_H, sz1), CREAM, 0.006))
    p.append(K.gbox("sp_head", (d0, dh, sz0), (d1, CAMP_H, sz1), CREAM, 0.006))
    # east partition
    p.append(K.gbox("ep", (ex0, 0.0, cz0), (ex1, CAMP_H, sz0), CREAM, 0.006))
    # roof slab
    p.append(K.gbox("roof", (cx0, CAMP_H, cz0), (ex1, CAMP_H + ROOF_T, sz1), CREAM, 0.008))
    # stiffener ribs and seam cover strips on both faces of the partitions (riveted panel construction)
    for x in (5.0, 7.1):
        for z, n in ((sz1, 1), (sz0, -1)):
            a, b = sorted((z, z + n * 0.012))
            p.append(K.gbox("rib", (x - 0.03, 0.0, a), (x + 0.03, CAMP_H, b), CREAM, 0.003))
    for z in (-3.35, -1.60):                               # clear of the growth chart (z -2.78 .. -2.12)
        for x, n in ((ex1, 1), (ex0, -1)):
            a, b = sorted((x, x + n * 0.012))
            p.append(K.gbox("rib", (a, 0.0, z - 0.03), (b, CAMP_H, z + 0.03), CREAM, 0.003))
    for y in (0.08, 1.45):                                  # horizontal rails on the Nursery faces
        p.append(K.gbox("rail", (cx0, y - 0.02, sz1), (d0, y + 0.02, sz1 + 0.01), CREAM, 0.002))
        p.append(K.gbox("rail", (d1, y - 0.02, sz1), (ex1, y + 0.02, sz1 + 0.01), CREAM, 0.002))
        if y < 1.0:                                         # the chart hangs on the east face: kick rail only
            p.append(K.gbox("rail", (ex1, y - 0.02, cz0), (ex1 + 0.01, y + 0.02, sz0), CREAM, 0.002))
    for x in [4.65 + 0.3 * k for k in range(11)]:
        if d0 - 0.05 < x < d1 + 0.05:
            continue
        p.append(K.rivet("crv", 0.007, (x, 2.80, sz1 + 0.0), normal=(0, 0, 1), mat=CREAM, segs=5))
    # doorway reveal (cream steel lining in the opening)
    for x in (d0, d1):
        p.append(K.gbox("dj", (x - 0.008, 0.0, sz0), (x + 0.008, dh, sz1), CREAM, 0.0))
    # the camp's worn floor patch (linoleum)
    p.append(K.flat_poly("cfloor", [(cx0, cz0), (cx1, cz0), (cx1, cz1), (cx0, cz1)], [], 0.0005, LINO, up=True))
    # tiled camp-side faces of the room's north wall and west wall (with the shutter opening)
    nw = K.wall_sweep("cnorth", [(cx0, cz0), (ex0, cz0)], [(-0.035, 0.0), (0.0, 0.10), (0.0, CAMP_H)], TILE, closed=False)
    ww = K.wall_sweep("cwest", [(cx0, cz1), (cx0, SHUT[1]), (cx0, SHUT[0]), (cx0, cz0)],
                      [(-0.035, 0.0), (0.0, 0.10), (0.0, SHUT[2]), (0.0, SHUT[3]), (0.0, CAMP_H)], TILE, closed=False)
    K.delete_faces_where(ww, lambda c, n: SHUT[0] < c.z < SHUT[1] and SHUT[2] < c.y < SHUT[3])
    p += [nw, ww]
    # the shutter opening reveal is the gallery's IA_tunnel_shutter + the crystal_shutter frame (group E)
    return K.part("camp_walls", p)


def build():
    M.reset_scene()
    K.ensure_materials()
    out = dict(walls=nursery_walls(), floor=nursery_floor(), ceiling=nursery_ceiling(), pipes=nursery_pipes(),
               camp=camp_walls())
    out["lamps"] = [lamp_glass(k, x, z) for k, (x, z) in enumerate(LAMPS)]
    for k, (x, z) in enumerate(LAMPS):
        K.empty(f"light_nursery_{k}", (x, LAMP_Y, z))
    K.empty("portal_e_n", (3.75, 1.2, 0.0), (0, -90, 0))
    K.to_blender()
    A.finalize_uv()
    return out


def verify(path):
    meshes = ["nursery_floor", "nursery_walls", "nursery_ceiling", "nursery_pipes", "camp_walls"] + \
             [f"lamp_glass_{k}" for k in range(5)]
    req = meshes + [f"light_nursery_{k}" for k in range(5)] + ["portal_e_n"]
    expect = {f"light_nursery_{k}": (x, LAMP_Y, z) for k, (x, z) in enumerate(LAMPS)}
    expect["portal_e_n"] = (3.75, 1.2, 0.0)
    errs = K.V.verify_glb(path, required=req, identity=meshes + [f"light_nursery_{k}" for k in range(5)], expect=expect,
                          rot_expect={"portal_e_n": (0, -90, 0)}, show=req)
    errs += K.facts(path, TRI_BUDGET, SURF_BUDGET)
    lo, hi = K.V.mesh_bounds_godot([bpy.data.objects["camp_walls"]])
    print(f"{K.TAG} camp_walls bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    K.qa_begin(bounces=6)
    K.qa_import("blast_door", (3.70, 0, 0), -90.0, prefix="qa_de_")
    K.qa_import("shell_lift", (0, 0, 0), 0.0, prefix="qa_sl_")
    K.qa_import("shell_gallery", (0, 0, 0), 0.0, prefix="qa_sg_")
    K.qa_import("freight_lift", (0, 0, 6.0), 0.0, prefix="qa_fl_")
    for o in list(bpy.data.objects):
        if o.name.startswith("qa_sl_intro"):
            o.hide_render = True
    glow = K.glow("qa_fluor", "E8F2FF", 7.0)
    for g in parts["lamps"]:
        K.override(g, glow)

    def lights(cam=None, camp=False):
        K.clear_lights()
        K.light("key_nursery", "SPOT", (9.8, 3.9, 0.2), 1500.0, "DCEBFF", radius=0.3, target=(9.8, 0.0, -3.4), spot_deg=60)
        K.light("fill_0", "POINT", (6.8, 3.6, 1.2), 160.0, "DCEBFF", radius=0.2)
        K.light("fill_1", "POINT", (11.5, 3.6, 0.8), 160.0, "DCEBFF", radius=0.2)
        for k, (x, z) in enumerate(LAMPS):
            K.light(f"tube_{k}", "AREA", (x, LAMP_Y - 0.05, z), 60.0, "E8F2FF", radius=1.2, target=(x, 0.0, z))
        if camp:
            K.light("camp_lamp", "POINT", (6.2, 2.45, -2.6), 70.0, "FFC27A", radius=0.05)
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 10.0, "FFE2C2", radius=0.2)

    shots = [("1", NAME, (5.7, 1.65, 3.3), (10.6, 1.3, -2.6), 62, False),           # nursery (R)
             ("2", NAME + "_2", (12.2, 1.65, 2.9), (6.4, 1.2, -0.8), 62, False),     # nursery_w (R)
             ("3", NAME + "_3", (6.1, 1.3, -0.3), (6.1, 1.15, -0.97), 44, True),      # seal (camp doorway)
             ("4", NAME + "_4", (7.25, 1.6, -1.5), (4.9, 1.2, -2.8), 62, True),      # camp (inside, K)
             ("5", NAME + "_5", (6.55, 1.55, -2.6), (4.66, 1.6, -2.6), 50, True),    # shutter opening
             ("6", NAME + "_6", (9.1, 1.6, -2.3), (7.8, 1.6, -2.45), 44, False)]     # chart wall (camp east face)
    for tag, name, cam, tgt, fov, camp in shots:
        if K.want(args, tag):
            lights(cam if tag in ("3", "5", "6") else None, camp)
            K.shoot(name, cam, tgt, vfov=fov)


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
