"""floor_hatch.glb — steel service hatch in the archive floor near the reading table (Leyla's 1998 reel).

A steel angle frame 0.70 x 0.70 set flush into the floor (top at y = 0), a sheet-steel cavity liner 0.30 deep,
and a 0.60 x 0.60 chequer-plate lid (`IA_hatch`, painted plate with bare-steel lugs worn through) hinged at
its back (-Z) edge on two surface hinges, with a recessed ring pull near the front edge. A copper service
pipe crosses the cavity.

Origin = the lid centre at floor level. Placement: (0.9, 0.0, 2.5), yaw 0 (docs/models/ch2.md §1).
The room cuts a 0.70 x 0.70 hole with a 0.36 deep void under it (room_archive).

Parts:
  IA_hatch          the lid; pivot on the hinge axis at local (0, 0, -0.305), axis +X.
                    Open = -105 deg about local +X (the front edge swings up and back).
  ring_pull         child of IA_hatch: the flat ring in its recess, origin at its staple (0, -0.0055, 0.212).
  hatch_reel_mount  empty on the cavity floor, identity: tape_reel.glb lies flat, face up.
  hatch_frame       static frame + hinge leaves; hatch_liner: static liner + pipe.

    blender -b --factory-startup -P tools/blender/models/floor_hatch.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G, GV, gbox  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "floor_hatch"
STEEL, PAINT, BRASS = "M_Steel_Dark", "M_Steel_Painted", "M_Brass_Aged"
FO, FI = 0.35, 0.31          # frame outer / inner half sizes
LH, LT = 0.30, 0.012         # lid half size, thickness (top flush at y = 0)
HINGE = (0.0, 0.0, -0.305)
DEPTH = 0.30
RING_C = (0.0, -0.0055, 0.235)
RING_PIVOT = (0.0, -0.0055, 0.212)
REEL_MOUNT = (0.04, -DEPTH + 0.0052, 0.03)
OPEN_DEG = -105.0


def build():
    M.reset_scene()
    C.ensure_materials()
    fr = []
    # angle frame: top flange (flush) + vertical leg + lid seat ledge
    for nm, mn, mx in (("fl_n", (-FO, -0.006, -FO), (FO, 0.0, -FI)), ("fl_s", (-FO, -0.006, FI), (FO, 0.0, FO)),
                       ("fl_w", (-FO, -0.006, -FI), (-FI, 0.0, FI)), ("fl_e", (FI, -0.006, -FI), (FO, 0.0, FI))):
        fr.append(gbox(nm, mn, mx, STEEL, bevel=0.0015))
    for nm, mn, mx in (("leg_n", (-FI, -0.07, -FI), (FI, -0.006, -FI + 0.006)), ("leg_s", (-FI, -0.07, FI - 0.006), (FI, -0.006, FI)),
                       ("leg_w", (-FI, -0.07, -FI + 0.006), (-FI + 0.006, -0.006, FI - 0.006)),
                       ("leg_e", (FI - 0.006, -0.07, -FI + 0.006), (FI, -0.006, FI - 0.006))):
        fr.append(gbox(nm, mn, mx, STEEL))
    s0, s1 = -LT - 0.006, -LT
    for nm, mn, mx in (("seat_n", (-FI, s0, -FI), (FI, s1, -FI + 0.02)), ("seat_s", (-FI, s0, FI - 0.02), (FI, s1, FI)),
                       ("seat_w", (-FI, s0, -FI + 0.02), (-FI + 0.02, s1, FI - 0.02)),
                       ("seat_e", (FI - 0.02, s0, -FI + 0.02), (FI, s1, FI - 0.02))):
        fr.append(gbox(nm, mn, mx, STEEL))
    # countersunk screw heads in the flange
    for (x, z) in ((-0.33, -0.2), (-0.33, 0.2), (0.33, -0.2), (0.33, 0.2), (-0.15, 0.33), (0.15, 0.33)):
        fr.append(C.gcyl("fl_screw", 0.006, 0.0008, (x, 0.0, z), axis="y", verts=8, mat=STEEL, bevel=0.0))
    # static hinge leaves on the back flange + knuckle halves
    hx0, hy, hz = HINGE
    for x in (-0.19, 0.19):
        fr.append(gbox(f"hleaf_f{x}", (x - 0.04, 0.0, -FO + 0.004), (x + 0.04, 0.003, -0.316), STEEL, bevel=0.001))
        for dx in (-0.03, 0.03):
            fr.append(C.gcyl(f"knuckle_f{x}{dx}", 0.0075, 0.018, (x + dx - 0.009, hy, hz), axis="x", verts=10, mat=STEEL, bevel=0.001))
    A.presmooth(fr)
    frame_o = M.join(fr, "hatch_frame")

    # liner: floor + 4 walls (inward faces), from the seat ledge down to -DEPTH
    li = FI - 0.006
    bm = bmesh.new()

    def q(*pts):
        bm.faces.new([bm.verts.new(G(*p)) for p in pts])
    yb, yt = -DEPTH, -0.07
    q((-li, yb, -li), (li, yb, -li), (li, yb, li), (-li, yb, li))
    q((-li, yb, -li), (-li, yt, -li), (li, yt, -li), (li, yb, -li))
    q((-li, yb, li), (li, yb, li), (li, yt, li), (-li, yt, li))
    q((-li, yb, -li), (-li, yb, li), (-li, yt, li), (-li, yt, -li))
    q((li, yb, -li), (li, yt, -li), (li, yt, li), (li, yb, li))
    liner = A.obj_from_bm("hatch_liner_box", bm, STEEL)
    inside = G(0, -0.15, 0)
    for p in liner.data.polygons:
        if (inside - p.center).dot(p.normal) < 0:
            p.flip()
    pipe = C.gtube("service_pipe", [(-li, -0.21, -0.19), (li, -0.21, -0.19)], 0.016, sides=10, mat="M_Copper")
    clips = [gbox(f"pipe_clip{x}", (x - 0.012, -0.235, -li), (x + 0.012, -0.185, -0.19), STEEL, bevel=0.002) for x in (-0.18, 0.18)]
    grit = gbox("liner_dust", (-0.2, yb, -0.1), (0.1, yb + 0.0006, 0.2), "M_Concrete")
    A.presmooth([liner, pipe] + clips + [grit])
    liner_o = M.join([liner, pipe] + clips + [grit], "hatch_liner")

    # ---- lid: painted plate with a ring-pull pocket, bare-steel chequer lugs, hinge leaves, underside ribs
    plate = gbox("lid_plate", (-LH, -LT, -LH), (LH, 0.0, LH), PAINT, bevel=0.0025, seg=1)
    cut = M.cylinder("pocket_cut", 0.040, 0.03, loc=G(RING_C[0], 0.0, RING_C[2]), verts=20, mat=STEEL, bevel=0.0)
    cut.data.transform(Matrix.Translation(cut.location))
    cut.location = (0, 0, 0)
    cut.data.transform(Matrix.Translation((0, 0, -0.008 + 0.015 - 0.0)))     # pocket floor at y = -0.008
    M.boolean(plate, cut)

    def pocket(c, n, cur):
        if math.hypot(c.x - RING_C[0], -c.y - RING_C[2]) < 0.0405 and c.z < -0.0005:
            return STEEL
        return None
    A.mat_by_face(plate, pocket)
    lid = [plate]
    # chequer lugs: elongated pyramids, alternating 45/-45 deg, 12 x 12 at 0.045 pitch, inside a 0.03 margin
    bm = bmesh.new()
    pitch, n = 0.045, 12
    for i in range(n):
        for j in range(n):
            x = -LH + 0.0525 + i * pitch
            z = -LH + 0.0525 + j * pitch
            if math.hypot(x - RING_C[0], z - RING_C[2]) < 0.062:
                continue
            a = math.radians(45 if (i + j) % 2 == 0 else -45)
            u = Vector((math.cos(a), math.sin(a)))
            v = Vector((-u.y, u.x))
            L, W, Hh = 0.0135, 0.0042, 0.0018
            c = Vector((x, z))
            base = [c + u * L, c + v * W, c - u * L, c - v * W]
            ridge = [c + u * (L * 0.55), c - u * (L * 0.55)]
            vb = [bm.verts.new(G(p.x, 0.0, p.y)) for p in base]
            vr = [bm.verts.new(G(p.x, Hh, p.y)) for p in ridge]
            for f in ((vb[0], vb[1], vr[1], vr[0]), (vb[1], vb[2], vr[1]), (vb[2], vb[3], vr[0], vr[1]), (vb[3], vb[0], vr[0])):
                bm.faces.new(f)
    lugs = A.obj_from_bm("lid_lugs", bm, STEEL)
    for p in lugs.data.polygons:
        if p.normal.z < 0:
            p.flip()
    lid.append(lugs)
    for x in (-0.19, 0.19):
        lid.append(gbox(f"hleaf_l{x}", (x - 0.04, 0.0, -LH + 0.004), (x + 0.04, 0.003, -LH + 0.07), STEEL, bevel=0.001))
        lid.append(C.gcyl(f"knuckle_l{x}", 0.0075, 0.042, (x - 0.021, hy, hz), axis="x", verts=10, mat=STEEL, bevel=0.001))
        for dz in (0.02, 0.05):
            lid.append(C.gcyl("hl_rivet", 0.004, 0.0015, (x, 0.003, -LH + dz), axis="y", verts=6, mat=STEEL, bevel=0.0))
    for z in (-0.12, 0.12):
        lid.append(gbox(f"rib{z}", (-LH + 0.03, -LT - 0.028, z - 0.004), (LH - 0.03, -LT, z + 0.004), STEEL, bevel=0.001))
    # staple for the ring
    rx, ry, rz = RING_PIVOT
    lid.append(C.gtube("ring_staple", [(rx - 0.012, -0.008, rz + 0.002), (rx - 0.012, -0.004, rz - 0.003), (rx + 0.012, -0.004, rz - 0.003),
                                       (rx + 0.012, -0.008, rz + 0.002)], 0.0022, sides=5, mat=STEEL))
    A.presmooth(lid)
    lid_o = M.join(lid, "IA_hatch")
    M.set_origin(lid_o, G(*HINGE))
    # ring pull (child of the lid)
    ring = C.hint_torus("ring_pull", G(*RING_C), 0.025, 0.0038, axis="y", major_seg=18, minor_seg=6, mat=BRASS)
    M.set_origin(ring, G(*RING_PIVOT))
    M.set_parent(ring, lid_o)
    mount = C.mount("hatch_reel_mount", REEL_MOUNT)
    A.finalize_uv([frame_o, liner_o, lid_o, ring])
    C.report(NAME)
    return frame_o, liner_o, lid_o, ring, mount


def main():
    args = M.main_guard()
    frame_o, liner_o, lid_o, ring, mount = build()
    path = C.export(NAME)
    C.verify_glb(path, required=["IA_hatch", "ring_pull", "hatch_reel_mount", "hatch_frame", "hatch_liner"],
                 identity=["IA_hatch", "ring_pull", "hatch_reel_mount"], budget=3000,
                 expect={"IA_hatch": HINGE, "ring_pull": RING_PIVOT, "hatch_reel_mount": REEL_MOUNT},
                 show=["IA_hatch", "ring_pull", "hatch_reel_mount"])
    if "--no-render" in args:
        return
    sel = C.args_shots(args)
    C.qa_begin()
    own = [frame_o, liner_o, lid_o, mount]
    C.qa_place(own, (0.9, 0.0, 2.5), 0.0)
    C.qa_import(C.model_glb("room_archive"))
    for p in C.PENDANTS:
        C.qa_import(C.model_glb("archive_pendant"), p, 0.0)
    for nm, pos, yaw in (("reading_table", (1.9, 0, 1.0), 0.0), ("lockers", (0.6, 0, 3.5), 180.0), ("stacks_shelving", (0.0, 0, 0.25), 0.0)):
        C.qa_import(C.model_glb(nm), pos, yaw)
    M.refresh()
    reel = C.model_glb("tape_reel")
    if os.path.exists(reel):
        h = C.qa_import(reel)
        h.matrix_world = mount.matrix_world.copy()
    if C.want("view", sel):
        C.qa_room_lights()
        C.shoot(NAME, (1.5, 1.45, 3.0), (0.9, 0.0, 2.5), vfov=50)
        C.qa_clear()
    if C.want("hero", sel):
        C.qa_room_lights()
        C.qa_light("key", "POINT", (1.3, 0.8, 2.2), 6.0, "FFE2C0", radius=0.08)
        C.shoot(NAME + "_hero", (1.32, 0.62, 3.02), (0.85, 0.0, 2.45), vfov=42)
        C.qa_clear()
    C.pose_rot(lid_o, "x", OPEN_DEG)
    if C.want("open", sel):
        C.qa_room_lights()
        C.qa_light("fill", "POINT", (1.2, 0.9, 2.9), 5.0, "FFE2C0", radius=0.08)
        C.shoot(NAME + "_open", (1.5, 1.45, 3.0), (0.9, 0.0, 2.5), vfov=50)
        C.qa_clear()


main()
