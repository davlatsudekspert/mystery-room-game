"""vent_grille.glb — cast-iron ventilation grille over the west-wall duct (Leyla's 1996 reel hides behind it).

Frame: a cast-iron face flange 0.68 x 0.43 (it laps 0.03 over the 0.62 x 0.37 wall opening) with a moulded
edge, a sleeve into the opening and 4 brass screws; a louvred leaf `IA_grille` in a 0.56 x 0.31 clear
opening, hinged on its LEFT edge (seen from the room) with two hinge knuckles; a short duct liner behind.

Origin = the frame centre on the wall plane (local z = 0 is the wall face; the duct runs to -z).
Placement: (-5.0, 2.55, 0.9), yaw 90 (front +Z faces world +X).

Parts:
  IA_grille          the leaf; pivot on the hinge axis at local (-0.287, 0, 0.026), axis +Y.
                     Open = -100 deg about local +Y (it swings toward the room).
  grille_reel_mount  empty on the liner floor 0.12 behind the grille, identity: tape_reel.glb lies flat,
                     face up (its centre 0.0052 above the floor).
  grille_frame       static frame + hinge knuckles; grille_duct: static liner (M_Steel_Dark, 0.33 deep).

    blender -b --factory-startup -P tools/blender/models/vent_grille.py [-- --no-render]
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

NAME = "vent_grille"
IRON, BRASS = "M_Steel_Dark", "M_Brass_Aged"
FX, FY = 0.34, 0.215          # flange half sizes (0.68 x 0.43)
OX, OY = 0.28, 0.155          # clear opening half sizes (0.56 x 0.31)
SX, SY = 0.305, 0.18          # sleeve outer half sizes (0.61 x 0.36, inside the 0.62 x 0.37 wall opening)
LX, LY = 0.272, 0.148         # leaf half sizes
HINGE = (-0.287, 0.0, 0.026)
DEPTH = 0.33
FLOOR_Y = -0.168              # liner inner floor
REEL_MOUNT = (0.0, FLOOR_Y + 0.0052, -0.12)
OPEN_DEG = -100.0


def flange_profile():
    """s inward from the flange's outer edge, u out of the wall."""
    pts = [(0.0, 0.0), (0.0, 0.006), (0.004, 0.011), (0.010, 0.014), (0.018, 0.014)]
    pts += A.arc(0.024, 0.014, 0.006, 180, 0, 3)[1:]
    pts += [(0.034, 0.016), (FX - OX - 0.004, 0.016), (FX - OX, 0.012), (FX - OX, 0.0)]
    return pts


def build():
    M.reset_scene()
    C.ensure_materials()
    frame = []
    # face flange swept around the outer rectangle (CCW seen from the front -> profile runs inward)
    path = [G(-FX, -FY, 0), G(FX, -FY, 0), G(FX, FY, 0), G(-FX, FY, 0)]
    frame.append(A.sweep("flange", flange_profile(), path, up=GV((0, 0, 1)), closed=True, mat=IRON))
    # sleeve into the wall opening
    t = SX - OX
    frame += [gbox("sleeve_t", (-SX, OY, -0.05), (SX, SY, 0.0), IRON), gbox("sleeve_b", (-SX, -SY, -0.05), (SX, -OY, 0.0), IRON),
              gbox("sleeve_l", (-SX, -OY, -0.05), (-OX, OY, 0.0), IRON), gbox("sleeve_r", (OX, -OY, -0.05), (SX, OY, 0.0), IRON)]
    _ = t
    # 4 brass screws in the flange corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            frame.append(C.screw("flange_screw", 0.0075, (sx * (FX - 0.031), sy * (FY - 0.031), 0.014), (0, 0, 1), BRASS,
                                 30 + 40 * (sx + sy), segs=8))
    # static hinge knuckles on the frame (outer pair), with leaf straps' counterparts
    hx, _, hz = HINGE
    for y in (-0.105, 0.105):
        for dy in (-0.03, 0.03):
            frame.append(C.gcyl(f"knuckle_f{y}{dy}", 0.0075, 0.018, (hx, y + dy - 0.009, hz), axis="y", verts=10, mat=IRON,
                                bevel=0.0015))
        frame.append(gbox(f"hinge_leaf_f{y}", (hx - 0.03, y - 0.04, 0.012), (hx - 0.004, y + 0.04, 0.018), IRON, bevel=0.002))
    A.presmooth(frame)
    frame_o = M.join(frame, "grille_frame")

    # leaf: border + six 40-degree louvres + hinge knuckles + brass pull
    leaf = []
    bw, z0, z1 = 0.022, -0.004, 0.020
    leaf += [gbox("leaf_t", (-LX, LY - bw, z0), (LX, LY, z1), IRON, bevel=0.003),
             gbox("leaf_b", (-LX, -LY, z0), (LX, -LY + bw, z1), IRON, bevel=0.003),
             gbox("leaf_l", (-LX, -LY + bw, z0), (-LX + bw, LY - bw, z1), IRON, bevel=0.003),
             gbox("leaf_r", (LX - bw, -LY + bw, z0), (LX, LY - bw, z1), IRON, bevel=0.003)]
    n = 6
    span = 2 * (LY - bw)
    for k in range(n):
        y = -LY + bw + span * (k + 0.5) / n
        blade = M.box(f"louvre{k}", (2 * (LX - bw) + 0.004, 0.005, 0.046), mat=IRON, bevel=0.0015, segments=1)
        # tilt: the room-side edge lower than the back edge
        blade.data.transform(Matrix.Rotation(math.radians(-48), 4, "X"))
        blade.data.transform(Matrix.Translation(G(0, y, 0.008)))
        leaf.append(blade)
    # central vertical stiffener
    leaf.append(gbox("leaf_mullion", (-0.007, -LY + bw, z0 + 0.004), (0.007, LY - bw, z1 - 0.002), IRON, bevel=0.002))
    for y in (-0.105, 0.105):
        leaf.append(C.gcyl(f"knuckle_l{y}", 0.0075, 0.042, (hx, y - 0.021, hz), axis="y", verts=10, mat=IRON, bevel=0.0015))
        leaf.append(gbox(f"strap{y}", (hx + 0.004, y - 0.016, z1 - 0.004), (-LX + 0.07, y + 0.016, z1 + 0.003), IRON, bevel=0.002))
        leaf.append(C.screw(f"strap_rivet{y}", 0.0045, (-LX + 0.05, y, z1 + 0.003), (0, 0, 1), IRON, None, segs=6))
    leaf.append(C.glathe("pull_knob", [(0.0, 0.0), (0.009, 0.0), (0.0095, 0.004), (0.0045, 0.010), (0.0045, 0.016),
                                       (0.010, 0.020), (0.011, 0.026), (0.008, 0.031), (0.0, 0.032)],
                         (LX - 0.038, 0.0, z1), axis="z", segments=12, mat=BRASS))
    A.presmooth(leaf)
    leaf_o = M.join(leaf, "IA_grille")
    M.set_origin(leaf_o, G(*HINGE))

    # duct liner: 5 inward faces, 0.33 deep, slightly inside the sleeve
    ix, iy = SX - 0.006, SY - 0.012
    bm = bmesh.new()

    def q(*pts):
        bm.faces.new([bm.verts.new(G(*p)) for p in pts])
    zb, zf = -DEPTH, -0.05
    q((-ix, -iy, zb), (ix, -iy, zb), (ix, iy, zb), (-ix, iy, zb))
    q((-ix, -iy, zb), (-ix, -iy, zf), (ix, -iy, zf), (ix, -iy, zb))
    q((-ix, iy, zb), (ix, iy, zb), (ix, iy, zf), (-ix, iy, zf))
    q((-ix, -iy, zb), (-ix, iy, zb), (-ix, iy, zf), (-ix, -iy, zf))
    q((ix, -iy, zb), (ix, -iy, zf), (ix, iy, zf), (ix, iy, zb))
    duct = A.obj_from_bm("grille_duct", bm, IRON)
    inside = G(0, 0, -0.15)
    for p in duct.data.polygons:
        if (inside - p.center).dot(p.normal) < 0:
            p.flip()
    # a little dust/debris on the duct floor: two flat scraps of paper
    scrap = gbox("duct_scrap", (0.10, FLOOR_Y, -0.26), (0.19, FLOOR_Y + 0.001, -0.20), "M_Paper")
    scrap.data.transform(Matrix.Translation(-scrap.data.vertices[0].co * 0))
    duct = M.join([duct, scrap], "grille_duct")
    assert abs(FLOOR_Y - (-iy)) < 0.0005, (FLOOR_Y, -iy)
    mount = C.mount("grille_reel_mount", REEL_MOUNT)
    A.finalize_uv([frame_o, leaf_o, duct])
    C.report(NAME)
    return frame_o, leaf_o, duct, mount


def main():
    args = M.main_guard()
    frame_o, leaf_o, duct, mount = build()
    path = C.export(NAME)
    C.verify_glb(path, required=["IA_grille", "grille_reel_mount", "grille_frame", "grille_duct"],
                 identity=["IA_grille", "grille_reel_mount"], budget=3000,
                 expect={"IA_grille": HINGE, "grille_reel_mount": REEL_MOUNT}, show=["IA_grille", "grille_reel_mount"])
    if "--no-render" in args:
        return
    sel = C.args_shots(args)
    C.qa_begin()
    own = [frame_o, leaf_o, duct, mount]
    root = C.qa_place(own, (-5.0, 2.55, 0.9), 90.0)
    C.qa_import(C.model_glb("room_archive"))
    C.qa_import(C.model_glb("library_ladder"), (-4.62, 0.0, 0.35), 90.0)
    for p in C.PENDANTS:
        C.qa_import(C.model_glb("archive_pendant"), p, 0.0)
    reel = C.model_glb("tape_reel")
    # reel at the mount (world): mount local -> world through the placement
    M.refresh()
    mw = mount.matrix_world
    if os.path.exists(reel):
        h = C.qa_import(reel)
        h.matrix_world = mw.copy()
    else:
        M.cylinder("qa_reel", 0.0635, 0.0104, loc=mw.translation, verts=24, mat="M_Tape")
    if C.want("view", sel):
        C.qa_room_lights()
        C.shoot(NAME, (-3.7, 1.9, 0.9), (-5.0, 2.55, 0.9), vfov=46)
        C.qa_clear()
    if C.want("hero", sel):
        C.qa_room_lights()
        C.qa_light("key", "POINT", (-4.2, 2.3, 0.4), 6.0, "FFE2C0", radius=0.05)
        C.shoot(NAME + "_hero", (-4.35, 2.25, 0.45), (-5.0, 2.55, 0.92), vfov=40)
        C.qa_clear()
    C.pose_rot(leaf_o, "y", OPEN_DEG)
    if C.want("open", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_open", (-3.7, 1.9, 0.9), (-5.0, 2.55, 0.9), vfov=46)
        C.qa_clear()
    if C.want("inside", sel):
        C.qa_room_lights()
        C.qa_light("torch", "SPOT", (-4.55, 2.62, 0.9), 3.0, "FFE8C8", radius=0.02, target=(-5.2, 2.4, 0.9), spot_deg=50)
        C.shoot(NAME + "_inside", (-4.45, 2.75, 0.75), (-5.12, 2.40, 0.9), vfov=40)
        C.qa_clear()
    _ = root


main()
