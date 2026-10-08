"""wall_safe.glb — heavy green-grey enamel wall safe with a brass keypad (Lab 7, south-wall recess).

Model space: front = Blender -Y (Godot +Z). Origin = centre of the FRONT FACE of the frame, which is
flush with the wall face (the lead places it at Godot (2.2, 1.25, 2.5), yaw 180°). The body fills the
0.50 x 0.50 x 0.30 recess (Blender Y 0..0.30).

Parts (origins at pivots, identity rotation at rest):
  IA_safe_door     origin on the LEFT hinge axis (seen from the front), at mid height.
                   Opens by rotating about Godot +Y, negative angle (−110° = open).
    IA_key_1..9, IA_key_0, IA_key_clear (C), IA_key_enter (↵)   children of the door; origin at the
                   key base centre; press = translate along Godot −Z (3 mm).
    safe_display   child of the door; flat dark glass face, origin at its centre (Label3D overlay).
    IA_safe_handle child of the door; spoked wheel, origin on its axis at the door face; turns about Godot Z.
    safe_bolts     child of the door; 3 locking bolts on the free edge (optional slide −X 24 mm).
  Static body split into slabs (safe_frame_l/r/t/b, safe_back, safe_shelf, safe_drawer) so no
  collider AABB covers the cavity: items placed inside stay tappable.
    blender -b --factory-startup -P tools/blender/models/wall_safe.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix  # noqa: E402

HALF = 0.25           # outer half size (fills the 0.5 x 0.5 recess)
OP = 0.217            # door opening half size (33 mm frame face)
DEPTH = 0.30
BACK_T = 0.028
JAMB_Y = 0.074        # painted jamb depth; dark steel interior beyond
DF = -0.014           # door front face (proud of the wall by 14 mm)
DS = 0.003            # front slab / rear body split
DB = 0.068            # door back face
DH = 0.215            # door front slab half size (2 mm gap)
RH = 0.203            # door rear body half size
HX, HY = -0.2235, -0.0105   # hinge axis (vertical)
HINGE_Z = (0.135, -0.135)
SHELF_Z = 0.035       # shelf top (items: radio valve)
FLOOR_Z = -0.115      # felt top of the internal drawer unit (items: key, lens, letter)
IN_Y = 0.086          # front of the interior fittings
KP_X, KP_Z = -0.093, 0.004   # keypad plate centre
KP_W, KP_H, KP_T = 0.162, 0.256, 0.004
PF = DF - KP_T        # keypad plate front face
KEY_W, KEY_H, KEY_T = 0.036, 0.030, 0.0075
PITCH_X, PITCH_Z = 0.046, 0.0395
DISP_Z = KP_Z + 0.0995
DISP_W, DISP_H = 0.116, 0.034
HW_X, HW_Z = 0.112, -0.028   # handle wheel centre
KEYS = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["clear", "0", "enter"]]
KEY_LABEL = {"clear": "C", "enter": "↵"}


# ---------------------------------------------------------------- static body
def frame_piece(name, pts):
    """One mitred side of the frame + its wall, full depth. Only the front face edges are bevelled
    (outer + inner), so the four pieces meet seamlessly at the mitres."""
    obj = L.prism_xz(name, pts, 0.0, DEPTH, mat="M_Steel_Painted")

    def front_edge(a, b, e):
        if abs(a.y) > 1e-6 or abs(b.y) > 1e-6:
            return False
        return abs(a.x - b.x) < 1e-6 or abs(a.z - b.z) < 1e-6     # not the diagonal mitre edge
    L.bevel_where(obj, front_edge, 0.0032, 2)
    L.bisect(obj, (0, JAMB_Y, 0), (0, 1, 0))
    L.mat_faces(obj, lambda c, n: "M_Steel_Dark" if c.y > JAMB_Y else None)
    return obj


def build_body():
    H, O = HALF, OP
    left = frame_piece("safe_frame_l", [(-H, -H), (-O, -O), (-O, O), (-H, H)])
    right = frame_piece("safe_frame_r", [(H, H), (O, O), (O, -O), (H, -H)])
    top = frame_piece("safe_frame_t", [(-H, H), (-O, O), (O, O), (H, H)])
    bot = frame_piece("safe_frame_b", [(H, -H), (O, -O), (-O, -O), (-H, -H)])
    # --- static hinge knuckles + leaves on the left frame face (door knuckle lives on the door)
    parts = [left]
    for zc in HINGE_Z:
        for (z0, z1) in ((zc - 0.047, zc - 0.016), (zc + 0.016, zc + 0.047)):
            h = z1 - z0
            if z1 > zc:      # turned finial on top of the upper knuckle, under the lower one
                prof = [(0.0, 0.0), (0.0095, 0.0), (0.0095, h), (0.0055, h + 0.003), (0.0035, h + 0.0085),
                        (0.0, h + 0.0095)]
            else:
                prof = [(0.0, -0.0095), (0.0035, -0.0085), (0.0055, -0.003), (0.0095, 0.0), (0.0095, h), (0.0, h)]
            kn = L.lathe2("knuckle", prof, segments=10, mat="M_Brass_Aged")
            kn.location = (HX, HY, z0)
            parts.append(kn)
        leaf = L.box_mm("hleaf", (-0.2475, -0.0035, zc - 0.045), (HX - 0.004, 0.0, zc - 0.018), mat="M_Brass_Aged",
                        bevel=0.0008)
        leaf2 = L.box_mm("hleaf", (-0.2475, -0.0035, zc + 0.018), (HX - 0.004, 0.0, zc + 0.045),
                         mat="M_Brass_Aged", bevel=0.0008)
        parts += [leaf, leaf2]
        for dz in (-0.0315, 0.0315):
            parts.append(L.rivet("hrivet", 0.0032, (-0.2405, -0.0035, zc + dz), mat="M_Brass_Aged", segs=6))
    left = M.join(parts, "safe_frame_l")
    # strike holes for the bolts on the right jamb (face -X)
    rparts = [right]
    for bz in (-0.12, 0.0, 0.12):
        hole = L.flat_shape("strike", [L.circle(0.0118, 14)], mat="M_Rubber")
        L.along(hole, (0, 0, 1), (-1, 0, 0))
        hole.location = (OP - 0.0002, 0.036, bz)
        ring = L.flat_shape("strike_r", L.circle_line(0.0128, 0.0016, 14), mat="M_Chrome")
        L.along(ring, (0, 0, 1), (-1, 0, 0))
        ring.location = (OP - 0.0003, 0.036, bz)
        rparts += [hole, ring]
    right = M.join(rparts, "safe_frame_r")

    back = L.box_mm("safe_back", (-OP, DEPTH - BACK_T, -OP), (OP, DEPTH, OP), mat="M_Steel_Dark", bevel=0.002)
    # --- shelf: folded steel with a front lip, felt mat and two angle brackets
    sh = [L.box_mm("shelf", (-OP + 0.001, IN_Y + 0.004, SHELF_Z - 0.004), (OP - 0.001, DEPTH - BACK_T, SHELF_Z - 0.0015),
                   mat="M_Steel_Painted", bevel=0.001),
          L.box_mm("shelf_lip", (-OP + 0.001, IN_Y, SHELF_Z - 0.02), (OP - 0.001, IN_Y + 0.0045, SHELF_Z - 0.0015),
                   mat="M_Steel_Painted", bevel=0.0012),
          L.box_mm("shelf_felt", (-OP + 0.012, IN_Y + 0.012, SHELF_Z - 0.0016), (OP - 0.012, DEPTH - BACK_T - 0.01, SHELF_Z),
                   mat="M_Felt", bevel=0.0)]
    for sx in (-1, 1):
        sh.append(L.box_mm("bracket", (sx * OP - (0.012 if sx > 0 else 0), IN_Y + 0.03, SHELF_Z - 0.03),
                           (sx * OP + (0.012 if sx < 0 else 0), DEPTH - BACK_T - 0.02, SHELF_Z - 0.004),
                           mat="M_Steel_Dark", bevel=0.0))
    shelf = M.join(sh, "safe_shelf")
    # --- internal deposit drawer unit (its felt top is the floor for the items)
    dr = [L.box_mm("carcass", (-OP + 0.0005, IN_Y + 0.006, -OP + 0.0005), (OP - 0.0005, DEPTH - BACK_T, FLOOR_Z - 0.002),
                   mat="M_Steel_Painted", bevel=0.002, segments=1),
          L.box_mm("dr_felt", (-OP + 0.008, IN_Y + 0.016, FLOOR_Z - 0.0025), (OP - 0.008, DEPTH - BACK_T - 0.006, FLOOR_Z),
                   mat="M_Felt", bevel=0.0),
          L.box_mm("dr_front", (-0.135, IN_Y, -OP + 0.012), (0.135, IN_Y + 0.0065, FLOOR_Z - 0.013),
                   mat="M_Steel_Painted", bevel=0.0018, segments=2)]
    pz = (-OP + FLOOR_Z) / 2 - 0.004
    # brass bar pull on two posts
    dr.append(L.tube("pull", [(-0.035, IN_Y, pz), (-0.035, IN_Y - 0.012, pz), (0.035, IN_Y - 0.012, pz),
                              (0.035, IN_Y, pz)], 0.0035, mat="M_Brass_Aged", bevel_res=1, smooth_path=False))
    for sx in (-1, 1):
        ros = L.lathe2("pull_ros", [(0.0065, 0.0), (0.0065, 0.001), (0.0045, 0.0028), (0.0, 0.0028)], segments=8,
                       mat="M_Brass_Aged", cap_bottom=False)
        L.along(ros)
        ros.location = (sx * 0.035, IN_Y, pz)
        dr.append(ros)
    # card holder with a blank index card
    ch = L.flat_front("cardholder", L.outline_ring(0.056, 0.022, 0.002, 0.003, 2), 0.0, IN_Y - 0.0006, pz + 0.026,
                      mat="M_Brass_Aged")
    card = L.plane("card", 0.052, 0.018, loc=(0.0, IN_Y - 0.0004, pz + 0.026), mat="M_Paper")
    dr += [ch, card]
    drawer = M.join(dr, "safe_drawer")
    return [left, right, top, bot, back, shelf, drawer]


# ---------------------------------------------------------------- door
def build_door():
    parts = []
    slab = L.box_mm("door_slab", (-DH, DF, -DH), (DH, DS, DH), mat="M_Steel_Painted", bevel=0.0042, segments=2)
    parts.append(slab)
    rear = L.box_mm("door_rear", (-RH, DS - 0.001, -RH), (RH, DB, RH), mat="M_Steel_Painted", bevel=0.003)
    parts.append(rear)
    # boltwork cover on the inside of the door with 4 screws
    cover = L.box_mm("cover", (-0.15, DB - 0.0005, -0.15), (0.15, DB + 0.004, 0.15), mat="M_Steel_Painted", bevel=0.0015)
    parts.append(cover)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(L.screw("cscrew", 0.0042, (sx * 0.135, DB + 0.004, sz * 0.135), normal=(0, 1, 0),
                                 slot_angle=0.4 + 0.6 * sx * sz, segs=6))
    # brass pinstripe inlay around the door face
    parts.append(L.flat_front("pinstripe", L.outline_ring(0.386, 0.386, 0.014, 0.0013, 4), 0.0, DF - 0.00008, 0.0,
                              mat="M_Brass_Aged"))
    # steel rivets on the border
    rp = [(sx * 0.2025, sz * 0.2025) for sx in (-1, 1) for sz in (-1, 1)]
    rp += [(0.0, 0.2025), (0.0, -0.2025), (0.2025, 0.0), (-0.2025, 0.0)]
    parts += L.rivet_row("drivet", rp, 0.0052, DF, mat="M_Steel_Dark", segs=6)
    # door knuckles + leaves (rotate with the door)
    for zc in HINGE_Z:
        kn = L.lathe2("dknuckle", [(0.0095, 0.0005), (0.0095, 0.0315)], segments=10, mat="M_Brass_Aged",
                      cap_bottom=False, cap_top=False)
        kn.location = (HX, HY, zc - 0.016)
        leaf = L.box_mm("dleaf", (HX + 0.004, DF - 0.003, zc - 0.0145), (-0.178, DF + 0.0003, zc + 0.0145),
                        mat="M_Brass_Aged", bevel=0.0008)
        parts += [kn, leaf]
        parts.append(L.screw("dscrew", 0.0033, (-0.188, DF - 0.003, zc), slot_angle=1.2, segs=6))
    # --- keypad escutcheon (brass) with engraved border and key wells
    kp = L.curve_solid("keypad", [L.rounded_rect(KP_W, KP_H, 0.012, 4)], KP_T, bevel=0.0013, bevel_res=1,
                       mat="M_Brass_Aged", drop_bottom=True)
    L.to_front(kp, y_back=DF, x=KP_X, z=KP_Z)
    parts.append(kp)
    parts.append(L.flat_front("kp_line", L.outline_ring(KP_W - 0.012, KP_H - 0.012, 0.007, 0.0008, 3), KP_X,
                              PF - 0.00008, KP_Z, mat="M_Bakelite"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(L.screw("kpscrew", 0.0031, (KP_X + sx * (KP_W / 2 - 0.0115), PF, KP_Z + sz * (KP_H / 2 - 0.0115)),
                                 slot_angle=0.3 + sx * 0.8 + sz * 0.3, segs=6))
    for r, row in enumerate(KEYS):
        for c, _k in enumerate(row):
            kx, kz = key_pos(r, c)
            parts.append(L.flat_front("well", [L.rounded_rect(KEY_W + 0.005, KEY_H + 0.005, 0.0075, 3)], kx,
                                      PF - 0.0001, kz, mat="M_Rubber"))
    # display bezel (chrome)
    bez = L.curve_solid("disp_bezel", [L.rounded_rect(DISP_W + 0.014, DISP_H + 0.014, 0.0065, 3),
                                       L.rounded_rect(DISP_W - 0.003, DISP_H - 0.003, 0.0028, 2)], 0.003,
                        bevel=0.0009, bevel_res=0, mat="M_Chrome", drop_bottom=True)
    L.to_front(bez, y_back=PF, x=KP_X, z=DISP_Z)
    parts.append(bez)
    # --- handle rosette with engraved index ticks
    ros = L.lathe2("rosette", [(0.0, 0.0), (0.043, 0.0), (0.043, 0.0016), (0.0395, 0.0042), (0.024, 0.005),
                               (0.0, 0.005)], segments=20, mat="M_Brass_Aged", cap_bottom=False)
    L.along(ros)
    ros.location = (HW_X, DF, HW_Z)
    parts.append(ros)
    for k in range(12):
        a = math.pi / 2 - k * math.pi / 6
        ln = 0.006 if k % 3 == 0 else 0.0035
        tk = L.flat_shape("tick", [[(-0.0006, -ln / 2), (0.0006, -ln / 2), (0.0006, ln / 2), (-0.0006, ln / 2)]],
                          mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(-(math.pi / 2 - a), 4, "Z"))
        L.to_front(tk, y_back=DF - 0.00505, x=HW_X + 0.033 * math.cos(a), z=HW_Z + 0.033 * math.sin(a))
        parts.append(tk)
    # maker's plaque above the handle
    pl = L.curve_solid("plaque", [L.rounded_rect(0.118, 0.036, 0.005, 3)], 0.0016, bevel=0.0005,
                       mat="M_Brass_Polished", drop_bottom=True)
    L.to_front(pl, y_back=DF, x=HW_X, z=0.142)
    parts.append(pl)
    parts.append(L.label_front("pl_txt", "MERIDIAN", 0.0125, HW_X, DF - 0.0017, 0.142, font=L.FONT_SERIF_B,
                               mat="M_Bakelite", spacing=1.05))
    for sx in (-1, 1):
        parts.append(L.rivet("pl_rv", 0.0021, (HW_X + sx * 0.0515, DF - 0.0016, 0.142), mat="M_Brass_Aged", segs=6))
    # emergency key escutcheon below the handle
    esc = L.lathe2("escutcheon", [(0.0, 0.0), (0.012, 0.0), (0.012, 0.0012), (0.0098, 0.0032), (0.0, 0.0032)],
                   segments=12, mat="M_Brass_Aged", cap_bottom=False)
    L.along(esc)
    esc.location = (HW_X, DF, -0.158)
    kh = L.flat_front("keyhole", [L.circle(0.0026, 10, cy=0.0016)], HW_X, DF - 0.00325, -0.158, mat="M_Rubber")
    kh2 = L.flat_front("keyhole2", [[(-0.0013, -0.0048), (0.0013, -0.0048), (0.0019, 0.001), (-0.0019, 0.001)]],
                       HW_X, DF - 0.00326, -0.158, mat="M_Rubber")
    parts += [esc, kh, kh2]
    door = M.join(parts, "IA_safe_door")
    M.set_origin(door, (HX, HY, 0.0))
    return door


def key_pos(r, c):
    kx = KP_X + (c - 1) * PITCH_X
    kz = DISP_Z - DISP_H / 2 - 0.007 - 0.016 - KEY_H / 2 - r * PITCH_Z
    return kx, kz


def build_keys(door):
    for r, row in enumerate(KEYS):
        for c, k in enumerate(row):
            kx, kz = key_pos(r, c)
            name = f"IA_key_{k}"
            cap = L.curve_solid(name + "_cap", [L.rounded_rect(KEY_W, KEY_H, 0.0058, 3)], KEY_T, bevel=0.0019,
                                bevel_res=1, mat="M_Brass_Polished", drop_bottom=True)
            L.to_front(cap, y_back=PF, x=kx, z=kz)
            label = KEY_LABEL.get(k, k)
            mat = {"clear": "M_Enamel_Crimson", "enter": "M_Enamel_Green"}.get(k, "M_Bakelite")
            size = 0.0165 if k not in KEY_LABEL else (0.0155 if k == "clear" else 0.018)
            font = L.FONT_SANS_B
            face = L.flat_front(name + "_face", [L.rounded_rect(KEY_W - 0.0085, KEY_H - 0.0085, 0.0034, 3)], kx,
                                PF - KEY_T - 0.0001, kz, mat="M_Enamel_Cream")
            txt = L.label_front(name + "_lbl", label, size, kx, PF - KEY_T - 0.0002, kz, font=font, mat=mat)
            key = M.join([cap, face, txt], name)
            M.set_origin(key, (kx, PF, kz))
            M.set_parent(key, door)


def build_display(door):
    disp = L.plane("safe_display", DISP_W, DISP_H, loc=(KP_X, PF - 0.0003, DISP_Z), mat="M_Glass_Dark")
    M.set_parent(disp, door)
    return disp


def build_handle(door):
    z0 = 0.005     # sits on the rosette
    hub = L.lathe2("hub", [(0.0165, z0), (0.0165, z0 + 0.006), (0.0128, z0 + 0.0095),
                           (0.0128, z0 + 0.0175), (0.0175, z0 + 0.0195), (0.0175, z0 + 0.026),
                           (0.0128, z0 + 0.0295), (0.0, z0 + 0.0325)], segments=12,
                   mat="M_Brass_Polished", cap_bottom=False)
    parts = [hub]
    zs = z0 + 0.0225      # wheel plane
    R = 0.056
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        sp = L.lathe2("spoke", [(0.0052, 0.0), (0.0046, R - 0.013), (0.0046, R)], segments=8, mat="M_Brass_Aged",
                      cap_bottom=False, cap_top=False)
        sp.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))           # +Z -> +X (radial)
        sp.data.transform(Matrix.Rotation(a, 4, "Z"))
        sp.data.transform(Matrix.Translation((0, 0, zs)))
        # bakelite grip on a brass ferrule outside the rim
        grip = L.lathe2("grip", [(0.0052, 0.0), (0.0058, 0.0055), (0.0078, 0.0085),
                                 (0.0098, 0.0165), (0.0088, 0.0232), (0.0048, 0.0266), (0.0, 0.0272)], segments=8,
                        mat="M_Bakelite", cap_bottom=False,
                        band_mats=["M_Brass_Polished", None, None, None, None, None])
        grip.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        grip.data.transform(Matrix.Translation((R + 0.003, 0, 0)))
        grip.data.transform(Matrix.Rotation(a, 4, "Z"))
        grip.data.transform(Matrix.Translation((0, 0, zs)))
        parts += [sp, grip]
    rim = M.torus("rim", R, 0.0062, major_seg=24, minor_seg=5, mat="M_Brass_Aged")
    rim.location = (0, 0, zs)
    M.apply_transform(rim)
    parts.append(rim)
    h = M.join(parts, "IA_safe_handle")
    L.along(h)                         # wheel axis +Z -> -Y (toward the viewer)
    h.location = (HW_X, DF, HW_Z)
    M.set_parent(h, door)
    return h


def build_bolts(door):
    parts = []
    for bz in (-0.12, 0.0, 0.12):
        b = L.lathe2("bolt", [(0.0, 0.0), (0.0098, 0.0), (0.0098, 0.0225), (0.0085, 0.0262), (0.0, 0.0268)],
                     segments=10, mat="M_Chrome", cap_bottom=False)
        b.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        b.location = (RH - 0.002, 0.036, bz)
        parts.append(b)
    bolts = M.join(parts, "safe_bolts")
    M.set_origin(bolts, (RH, 0.036, 0.0))
    M.set_parent(bolts, door)
    return bolts


def build():
    build_body()
    door = build_door()
    build_keys(door)
    build_display(door)
    build_handle(door)
    build_bolts(door)
    return door


def shot(name, cam, target, lens, door_deg=0.0, samples=32):
    door = M.bpy.data.objects["IA_safe_door"]
    door.rotation_euler = (0, 0, math.radians(door_deg))
    L.qa_wall(2 * HALF, 2 * HALF, w=1.6, h=1.4)
    L.qa_render(name, cam, target, lens=lens, floor_z=None, samples=samples)
    door.rotation_euler = (0, 0, 0)


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("wall_safe")
    if L.want_render():
        shot("wall_safe", (0.55, -0.95, 0.30), (0.0, 0.0, 0.0), 45)
        shot("wall_safe_2", (-0.04, -0.62, 0.02), (-0.045, 0.0, 0.0), 55)
        shot("wall_safe_3", (0.42, -1.0, 0.26), (-0.17, -0.06, 0.0), 36, door_deg=-110.0)


main()
