"""strand_office.glb — Strand's glazed office in the Choir Hall's south-west corner (W1b / W2).
Contract: docs/models/ch3.md §4 strand_office (+ §1.3 office lock, §2 office_door / office / switch_room views);
key: docs/models/ch3_g.md (key_square); results: docs/models/ch3_b.md.

Built in WORLD coordinates (origin = the world origin). Partitions: east at x = -10.2 (z 1.2 .. 4.0) and north at
z = 1.2 (x -13.0 .. -10.2): walnut panelling to 0.9, clear glass in brass mullions to 2.8, a wooden roof slab
y 2.8 .. 2.9. Doorway in the east partition z 2.2 .. 3.1, y 0 .. 2.15.

  strand_office (static)  panelling, stiles, cap rails, door frame, corner post, roof slab, the filing cabinet in the
                          north-west corner, the coat stand, the photo frame's backing (M_Wood_Panel); mullions,
                          transoms, head rails, hinge knuckles, cabinet pulls and label frames, coat hooks, the photo
                          frame (M_Brass_Aged); the glass panes (M_Glass).
  IA_office_door          leaf 0.88 x 2.12 x 0.04 (walnut panel below, glass above), hinged on its north edge: pivot
                          (-10.2, 0, 2.22); open = +100° about +Y (it swings out into the hall). Two materials.
    IA_office_lock        child of the door: the brass lock box on the hall face at the free edge, centre
                          (-10.14, 1.05, 3.0), a key slot on its top, a raised ■ on its face, and the lever handles.
      office_key_mount    child of the lock, on the slot: key_square stands blade down, bow up, bow face toward +X
                          (Godot Euler XYZ (90, 90, 0)); the key's collar face rests on the box top (y 1.12).
  staff_photo             0.60 x 0.40 quad centred (-12.98, 1.65, 2.95) facing +X, UV 0..1 (u -> -Z = the viewer's
                          right, v -> +Y), M_Decal_StaffPhoto.
  Strand's lab coat hangs on the coat stand but lives in office_desk.glb (M_Paper): this GLB has no cream slot.

    blender -b --factory-startup -P tools/blender/models/strand_office.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "strand_office"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 9000, 7, 4
WOOD, BRASS, GLASS, DECAL = B.PANEL, B.BRASS, B.GLASS, "M_Decal_StaffPhoto"

EX, NZ = -10.2, 1.2                       # partition planes
WX = -13.0                                # the hall's west wall
DADO, GLASS_TOP, ROOF = 0.90, 2.80, (2.80, 2.90)
DOOR_Z = (2.2, 3.1)
DOOR_H = 2.15
LEAF = (2.22, 3.10, 0.0, 2.12)            # z0, z1, y0, y1
LEAF_X = (-10.22, -10.18)
PIVOT = (EX, 0.0, 2.22)
LOCK = (-10.14, 1.05, 3.0)
LOCK_BOX = (-10.18, -10.10, 0.98, 1.12, 2.95, 3.05)
KEY_COLLAR_SQUARE = 0.0032                # ch3_g.md: ■'s collar face is 0.0032 above its origin when standing
HANDLE_Z = 2.86
PHOTO = (-12.98, 1.65, 2.95, 0.60, 0.40)
CABINET = (-12.95, -12.45, 1.3, 1.8, 1.30)
COAT_STAND = B.COAT_STAND
CHAIR = ((-11.8, 0.0, 3.55), 60.0)


# ====================================================================== partitions
def bay(parts, m, u0, u1, door=False):
    """One bay of partition between the mullion lines u0 and u1 in the frame m (local X along the wall, Y up, Z =
    thickness). door=True builds the door frame and the transom light instead of the panel and the lower pane."""
    def box(name, a, b, mat, bevel=0.003, seg=1):
        o = B.gbox(name, a, b, mat, bevel, seg)
        B.place_mesh(o, m)
        parts.append(o)

    if not door:
        box("plinth", (u0, 0.0, -0.045), (u1, 0.12, 0.045), WOOD)
        box("panel", (u0, 0.12, -0.03), (u1, DADO - 0.04, 0.03), WOOD)
        for sz in (-1, 1):
            box("field", (u0 + 0.07, 0.19, min(0.03 * sz, 0.042 * sz)), (u1 - 0.07, DADO - 0.11, max(0.03 * sz, 0.042 * sz)), WOOD,
                0.004)
        box("cap", (u0, DADO - 0.04, -0.045), (u1, DADO, 0.045), WOOD)
        box("pane_lo", (u0 + 0.02, DADO, -0.003), (u1 - 0.02, 1.92, 0.003), GLASS, 0.0)
        box("transom", (u0, 1.92, -0.025), (u1, 1.96, 0.025), BRASS, 0.002)
        box("pane_hi", (u0 + 0.02, 1.96, -0.003), (u1 - 0.02, GLASS_TOP - 0.04, 0.003), GLASS, 0.0)
    else:
        for (a, b) in ((u0, u0 + 0.04), (u1 - 0.04, u1)):
            box("jamb", (a, 0.0, -0.045), (b, DOOR_H + 0.06, 0.045), WOOD)
        box("head", (u0, DOOR_H, -0.045), (u1, DOOR_H + 0.06, 0.045), WOOD)
        box("pane_door", (u0 + 0.06, DOOR_H + 0.06, -0.003), (u1 - 0.06, GLASS_TOP - 0.04, 0.003), GLASS, 0.0)
        for (a, b) in ((u0 + 0.04, u0 + 0.06), (u1 - 0.06, u1 - 0.04)):
            box("tmul", (a, DOOR_H + 0.06, -0.03), (b, GLASS_TOP - 0.04, 0.03), BRASS, 0.002)
    box("head_rail", (u0, GLASS_TOP - 0.04, -0.03), (u1, GLASS_TOP, 0.03), BRASS, 0.002)
    for u in (u0, u1):
        box("mullion", (u - 0.02, DADO - 0.002, -0.03), (u + 0.02, GLASS_TOP - 0.04, 0.03), BRASS, 0.002)


def partitions():
    p = []
    # east partition: local X = world +Z (from z 1.2), thickness along world X
    m_e = B.frame_mat((EX, 0.0, NZ), (0, 0, 1), (0, 1, 0))
    bay(p, m_e, 0.04, DOOR_Z[0] - NZ)
    bay(p, m_e, DOOR_Z[0] - NZ, DOOR_Z[1] - NZ, door=True)
    bay(p, m_e, DOOR_Z[1] - NZ, 4.0 - NZ)
    # north partition: local X = world +X (from x -13.0), thickness along world Z
    m_n = B.frame_mat((WX, 0.0, NZ), (1, 0, 0), (0, 1, 0))
    for (a, b) in ((0.0, 0.70), (0.70, 1.40), (1.40, 2.10), (2.10, EX - WX - 0.04)):
        bay(p, m_n, a, b)
    # corner post, roof slab with a brass edge bead
    p.append(B.gbox("cpost", (EX - 0.045, 0.0, NZ - 0.045), (EX + 0.045, GLASS_TOP, NZ + 0.045), WOOD, 0.004))
    p.append(B.gbox("roof", (WX, ROOF[0], NZ - 0.045), (EX + 0.045, ROOF[1], 4.0), WOOD, 0.004))
    p.append(B.gbox("roofbead", (EX + 0.045, ROOF[0] - 0.01, NZ - 0.045), (EX + 0.06, ROOF[1] + 0.005, 4.0), BRASS, 0.002))
    p.append(B.gbox("roofbead_n", (WX, ROOF[0] - 0.01, NZ - 0.06), (EX + 0.06, ROOF[1] + 0.005, NZ - 0.045), BRASS, 0.002))
    # hinge knuckles on the door's north jamb (static halves)
    for y in (0.25, 1.00, 1.80):
        p.append(B.gcyl("knuckle", 0.011, y, y + 0.10, base=(EX, 0.0, LEAF[0] - 0.012), axis=(0, 1, 0), segments=8, mat=BRASS,
                        chamfer=0.002))
    return p


# ====================================================================== dressing
def filing_cabinet():
    x0, x1, z0, z1, h = CABINET
    p = [B.gbox("fc_plinth", (x0 + 0.02, 0.0, z0 + 0.02), (x1 - 0.02, 0.08, z1 - 0.02), WOOD, 0.003),
         B.gbox("fc_body", (x0, 0.08, z0), (x1, h, z1), WOOD, 0.005, 1)]
    # four drawer fronts on the east face (+X), each with a brass cup pull and a label frame
    for k in range(4):
        y0 = 0.12 + k * 0.29
        p.append(B.gbox("fc_front", (x1, y0, z0 + 0.02), (x1 + 0.012, y0 + 0.26, z1 - 0.02), WOOD, 0.004, 1))
        zc = (z0 + z1) / 2
        cup = B.glathe("fc_pull", [(0.0, 0.0), (0.018, 0.0), (0.022, 0.006), (0.022, 0.018), (0.014, 0.024), (0.0, 0.024)],
                       (x1 + 0.012, y0 + 0.09, zc), (1, 0, 0), 10, BRASS, smooth=45.0)
        p.append(cup)
        fr = B.plate("fc_label", [L.rounded_rect(0.07, 0.03, 0.004, 2), L.rounded_rect(0.058, 0.02, 0.003, 2)], 0.002, mat=BRASS,
                     bevel=0.0, loc=(0.0, 0.0, 0.0))
        fr.data.transform(Matrix.Translation((x1 + 0.012, y0 + 0.19, zc)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        p.append(fr)
    return p


def coat_stand():
    (sx, _, sz), hook_y, hook_r = COAT_STAND["pos"], COAT_STAND["hook_y"], COAT_STAND["hook_r"]
    p = [B.glathe("cs_base", [(0.0, 0.0), (0.20, 0.0), (0.20, 0.02), (0.12, 0.035), (0.04, 0.05), (0.03, 0.06)], (sx, 0.0, sz),
                  (0, 1, 0), 16, WOOD, smooth=45.0),
         B.glathe("cs_pole", [(0.03, 0.06), (0.03, 1.55), (0.026, 1.60), (0.026, 1.84), (0.036, 1.86), (0.036, 1.90), (0.0, 1.93)],
                  (sx, 0.0, sz), (0, 1, 0), 12, WOOD, smooth=50.0)]
    p.append(B.glathe("cs_ring", [(0.034, hook_y - 0.03), (0.042, hook_y - 0.03), (0.042, hook_y + 0.03), (0.034, hook_y + 0.03)],
                      (sx, 0.0, sz), (0, 1, 0), 12, BRASS, smooth=45.0, cap_bottom=False, cap_top=False))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        pts = [Vector((sx, hook_y, sz)) + d * 0.04, Vector((sx, hook_y + 0.02, sz)) + d * (hook_r - 0.03),
               Vector((sx, hook_y + 0.06, sz)) + d * hook_r]
        p.append(B.tube("cs_hook", [tuple(q) for q in pts], 0.006, sides=6, mat=BRASS))
    return p


def photo_frame():
    px, py, pz, w, h = PHOTO
    p = []
    b, t = 0.025, 0.022
    for (z0, z1, y0, y1) in ((pz - w / 2 - b, pz + w / 2 + b, py - h / 2 - b, py - h / 2),
                             (pz - w / 2 - b, pz + w / 2 + b, py + h / 2, py + h / 2 + b),
                             (pz - w / 2 - b, pz - w / 2, py - h / 2, py + h / 2),
                             (pz + w / 2, pz + w / 2 + b, py - h / 2, py + h / 2)):
        p.append(B.gbox("pf", (WX, y0, z0), (WX + t, y1, z1), BRASS, 0.003, 1))
    p.append(B.gbox("pf_back", (WX, py - h / 2, pz - w / 2), (px - 0.002, py + h / 2, pz + w / 2), WOOD, 0.0))
    return p


def static():
    return B.part(NAME, partitions() + filing_cabinet() + coat_stand() + photo_frame())


# ====================================================================== door, lock, photo
def door():
    z0, z1, y0, y1 = LEAF
    x0, x1 = LEAF_X
    st = 0.10
    p = [B.gbox("stile", (x0, y0, z0), (x1, y1, z0 + st), WOOD, 0.004),
         B.gbox("stile", (x0, y0, z1 - st), (x1, y1, z1), WOOD, 0.004),
         B.gbox("rail_b", (x0, y0, z0 + st), (x1, 0.20, z1 - st), WOOD, 0.004),
         B.gbox("rail_m", (x0, 0.86, z0 + st), (x1, 0.96, z1 - st), WOOD, 0.004),
         B.gbox("rail_t", (x0, y1 - 0.08, z0 + st), (x1, y1, z1 - st), WOOD, 0.004),
         B.gbox("lpanel", (x0 + 0.006, 0.20, z0 + st), (x1 - 0.006, 0.86, z1 - st), WOOD, 0.0)]
    for sx in (-1, 1):
        xa = (x0 + x1) / 2 + sx * 0.014
        xb = (x0 + x1) / 2 + sx * 0.024
        p.append(B.gbox("lfield", (min(xa, xb), 0.27, z0 + st + 0.07), (max(xa, xb), 0.79, z1 - st - 0.07), WOOD, 0.004))
    p.append(B.gbox("dglass", ((x0 + x1) / 2 - 0.003, 0.96, z0 + st), ((x0 + x1) / 2 + 0.003, y1 - 0.08, z1 - st), GLASS, 0.0))
    return B.part("IA_office_door", p, pivot=PIVOT)


def lock():
    x0, x1, y0, y1, z0, z1 = LOCK_BOX
    p = [B.gbox("lbox", (x0, y0, z0), (x1, y1, z1), BRASS, 0.003, 1)]
    sq = S.inlay("lsq", "square", 0.045, depth=0.002, mat=BRASS, bevel=0.0004)
    sq.data.transform(Matrix.Translation((x1, LOCK[1], LOCK[2])) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    p.append(sq)
    # a sunk border round the square so it reads in one material
    p.append(B.plate("lsq_fr", [L.rounded_rect(0.062, 0.062, 0.004, 2), list(reversed(L.rounded_rect(0.054, 0.054, 0.003, 2)))],
                     0.0015, mat=BRASS, bevel=0.0, loc=(0.0, 0.0, 0.0)))
    p[-1].data.transform(Matrix.Translation((x1, LOCK[1], LOCK[2])) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    # key slot escutcheon on the top
    p.append(B.glathe("lesc", [(0.0, 0.0), (0.014, 0.0), (0.014, 0.003), (0.010, 0.005), (0.004, 0.005), (0.004, -0.004), (0.0, -0.004)],
                      (LOCK[0], y1, LOCK[2]), (0, 1, 0), 12, BRASS, smooth=45.0))
    # lever handles on both faces, pointing toward the hinge (-Z)
    for (xf, sx) in ((LEAF_X[1], 1), (LEAF_X[0], -1)):
        p.append(B.glathe("rose", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.006), (0.018, 0.012), (0.010, 0.012), (0.010, 0.030),
                                   (0.0, 0.030)], (xf, LOCK[1], HANDLE_Z), (sx, 0, 0), 12, BRASS, smooth=45.0))
        p.append(B.tube("lever", [(xf + sx * 0.03, LOCK[1], HANDLE_Z), (xf + sx * 0.036, LOCK[1], HANDLE_Z - 0.03),
                                  (xf + sx * 0.036, LOCK[1] - 0.004, HANDLE_Z - 0.12)], 0.008, sides=8, mat=BRASS))
    return B.part("IA_office_lock", p, pivot=LOCK)


def photo():
    px, py, pz, w, h = PHOTO
    q = B.K.quad("staff_photo", (px, py, pz), (0, 0, -1), (0, 1, 0), w, h, DECAL)
    return B.part("staff_photo", [q], pivot=(px, py, pz))


def key_mount():
    return B.empty("office_key_mount", (LOCK[0], LOCK_BOX[3] - KEY_COLLAR_SQUARE, LOCK[2]), (90.0, 90.0, 0.0))


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    dr = door()
    lk = lock()
    ph = photo()
    km = key_mount()
    B.K.to_blender()
    A.finalize_uv()          # M_Decal_* faces keep their UVs: the photo quad stays 0..1
    B.parent(lk, dr)
    B.parent(km, lk)
    return dict(static=st, door=dr, lock=lk, photo=ph, key_mount=km)


REQ = [NAME, "IA_office_door", "IA_office_lock", "office_key_mount", "staff_photo"]


def check_photo_uv(obj):
    me = obj.data
    uv = me.uv_layers.active.data
    pts = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = B.V.C_INV @ (obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            pts.append((round(co.z, 3), round(co.y, 3), tuple(round(c, 3) for c in uv[li].uv)))
    # u grows toward -Z (the viewer's right when facing -X), v toward +Y
    ok = all(((u > 0.5) == (z < PHOTO[2])) and ((v > 0.5) == (y > PHOTO[1])) for (z, y, (u, v)) in pts)
    print(f"{B.TAG} staff_photo UV corners (godot z, y, uv): {pts} -> {'OK' if ok else 'MIRRORED'}")
    return [] if ok else ["staff_photo UV mirrored"]


def verify(path, parts):
    expect = {"IA_office_door": PIVOT, "IA_office_lock": LOCK, "staff_photo": PHOTO[:3],
              "office_key_mount": (LOCK[0], LOCK_BOX[3] - KEY_COLLAR_SQUARE, LOCK[2])}
    parents = {NAME: None, "IA_office_door": None, "IA_office_lock": "IA_office_door", "office_key_mount": "IA_office_lock",
               "staff_photo": None}
    errs = B.verify(path, REQ, identity=[NAME, "IA_office_door", "IA_office_lock", "staff_photo"], expect=expect,
                    parents=parents, rot_expect={"office_key_mount": (90.0, 90.0, 0.0)}, tris=TRI_BUDGET, surf=SURF_BUDGET,
                    mats=MAT_BUDGET)
    errs += check_photo_uv(parts["photo"])
    lo, hi = B.V.mesh_bounds_godot([parts["door"]])
    print(f"{B.TAG} door leaf bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    # the open door (+100° about +Y) must stay out of the switch_room / cabinet / office frusta: report where it lies
    a = math.radians(100.0)
    tip = (PIVOT[0] + 0.88 * math.sin(a), PIVOT[2] + 0.88 * math.cos(a))
    print(f"{B.TAG} open door: free edge at x {tip[0]:.3f}, z {tip[1]:.3f} (contract: along z ~ 2.1 for x -10.2 .. -9.33)")
    return errs


# ====================================================================== QA
def qa(parts, args):
    B.qa_begin()
    B.hall()
    # the room-coordinate model stays at the origin; neighbours: desk, case, chair, cabinets, plate
    B.bring("office_desk", (-12.6, 0.0, 2.95), 90.0, prefix="qa_desk_")
    B.bring("meter_case", (-12.62, 0.76, 3.30), 90.0, prefix="qa_case_")
    B.bring("chair", *CHAIR, prefix="qa_chair_")
    for x in (-7.4, -8.3, -9.2):
        B.bring("switch_cabinet", (x, 0.0, 4.0), 180.0, prefix=f"qa_cab{int(-x * 10)}_")
    B.bring("interlock_plate", (-8.3, 0.0, 4.0), 180.0, prefix="qa_plate_")
    key = B.bring("key_square", under=parts["key_mount"], prefix="qa_key_")
    lamp = B.imported("qa_desk_", "office_bulb")
    if lamp is not None:
        B.K.override(lamp, B.K.glow("qa_office_bulb", "FFD9A8", 6.0))
    rest = B.rest_store([parts["door"]])
    office_lamp = [("office_lamp", "POINT", (-12.65, 1.12, 2.45), 25.0, "FFCC8A", 0.05)]

    def door_open(on):
        B.rest_apply([parts["door"]], rest)
        if on:
            B.K.pose_rot(parts["door"], "y", 100.0)
        if key is not None:
            for o in key.children_recursive:
                o.hide_render = on

    shots = [
        # 1 office_door view: closed, the ■ key standing in the lock
        ("1", NAME, (-9.0, 1.5, 2.65), (-10.2, 1.1, 2.75), 50, False),
        # 2 office view (door open): the desk, the lamp, the photo, the case, the chair, the coat stand
        ("2", NAME + "_2", (-10.5, 1.6, 2.35), (-12.55, 0.85, 2.95), 56, True),
        # 3 switch_room view with the door open: the leaf must stay out of the frame
        ("3", NAME + "_3", (-8.3, 1.65, 1.75), (-8.3, 1.4, 4.0), 58, True),
        # 4 choir_s root view (the office is its target), door closed
        ("4", NAME + "_4", (-5.6, 1.65, -2.9), (-10.6, 1.3, 2.6), 62, False),
        # 5 hero from the hall: the glazed corner with the door open
        ("5", NAME + "_5", (-8.6, 1.7, 1.0), (-11.4, 1.3, 2.9), 54, True),
    ]
    for tag, name, cam, tgt, fov, open_ in shots:
        if not B.want(args, tag):
            continue
        door_open(open_)
        B.choir_lights(cam, fill=8.0 if tag not in ("3", "4") else 0.0, extra=office_lamp)
        B.shoot(name, cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path, parts)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
