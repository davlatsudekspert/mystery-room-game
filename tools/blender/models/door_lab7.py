"""door_lab7.glb — heavy panelled mahogany institute door for the Lab 7 east opening, with walnut
casing, stone threshold, frosted upper light with a sign-written gold "7", and a maglock unit.

MODEL SPACE (Blender; front = -Y = Godot +Z, like every other model):
  origin    = centre of the 1.0 m opening, at floor level, on the ROOM-side wall plane.
  local x   = across the opening, [-0.5, +0.5]; +x becomes Godot +Z (SOUTH) after the lead's -90 deg yaw.
  local y   = into the wall: [0, 0.2] is the wall thickness, +y is the corridor (Godot +X after the yaw).
  Lead placement (lab7_room.gd): position Godot (3.0, 0, 0.9), rotation_degrees.y = -90.

PARTS
  door_frame (static)  jamb linings + stops (mahogany), walnut architrave with plinth blocks and a
                       capped head, stone threshold, 3 hinge knuckles, maglock housing + cable.
  IA_door_leaf         0.924 x 2.146 x 0.05 leaf. ORIGIN = HINGE PIN AXIS at floor level:
                       Blender (+0.466, +0.203, 0) = the leaf's local +X edge (the SOUTH edge in the
                       room), on the corridor face. Hinge side = model +X = viewer's RIGHT when facing
                       the door from the room.
                       OPEN = rotate about the leaf's local up axis (Godot local Y / Blender Z) by
                       -95 deg (negative = clockwise seen from above) -> the free edge swings to
                       Godot +X, out of the room into the corridor. (+95 would swing it INTO the room
                       through the stop.)  Rest = 0.
  IA_door_handle       child of IA_door_leaf; both brass levers + roses on one spindle. ORIGIN on the
                       spindle axis at the leaf mid-plane, Blender (-0.397, 0.170, 1.08). Levers point
                       toward the hinge (+X). PRESS = rotate about the spindle = Godot local Z by -40
                       deg (lever tips go down; Blender: +40 about local Y). Rest = 0.
  maglock_lamp         M_Emissive_Red jewel lens on the maglock box above the casing, origin at the
                       lens base centre Blender (0.0, -0.075, 2.378)  (Godot room ~ (2.925, 2.378, 0.9)).

    blender -b --factory-startup -P tools/blender/models/door_lab7.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "door_lab7"
OW, OH, WT = 1.0, 2.2, 0.2              # opening width / height, wall thickness
JT = 0.035                              # jamb lining thickness
JX = OW / 2 - JT                        # 0.465 inner jamb face
LY0, LY1 = 0.145, 0.195                 # leaf room / corridor faces
LYM = (LY0 + LY1) / 2
LX0, LX1 = -0.462, 0.462
LZ0, LZ1 = 0.016, 2.162
PIN = (0.466, 0.203)
STILE, TOP_R = 0.13, 0.13
LOCK_Z0, LOCK_Z1 = 0.92, 1.14
BOT_Z1 = 0.27
MUNTIN = 0.09
GL_Z0, GL_Z1 = LOCK_Z1, LZ1 - TOP_R
HANDLE_X, HANDLE_Z, KEY_Z = -0.397, 1.08, 0.975
CAS_IN, CAS_W, PL_H = 0.49, 0.11, 0.23
HEAD_IN = 2.175
LAMP = (0.0, -0.075, 2.378)
MOULD = [(0.0, 0.0), (0.0, 0.007), (0.004, 0.012), (0.011, 0.013), (0.018, 0.006), (0.020, 0.0)]
MW = 0.020

MAH, WAL, BR = "M_Wood_Mahogany", "M_Wood_Walnut", "M_Brass_Aged"


def box(name, mn, mx, mat, bevel=0.003, seg=1):
    return A.box_minmax(name, mn, mx, mat=mat, bevel=bevel, segments=seg)


def face_matrix(room_side: bool) -> Matrix:
    """Local (a right as seen from that side, b up, c out of the leaf face)."""
    if room_side:
        return A.frame_matrix((0, LY0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    return A.frame_matrix((0, LY1, 0), (-1, 0, 0), (0, 0, 1), (0, 1, 0))


def face_rect(room_side, x0, x1, z0, z1):
    fm = face_matrix(room_side)
    if room_side:
        return A.rect_path(fm, x0, x1, z0, z1)
    return A.rect_path(fm, -x1, -x0, z0, z1)


def keyhole(name, x, z, y, out):
    """Small bakelite keyhole (circle + tapering slot) lying on a plate face at depth y; out = +-1 (Y)."""
    cv, rr, sw = 0.003, 0.0028, 0.0011
    a0 = math.degrees(math.acos(sw / rr))
    pts = [(0.0018, -0.0078), (sw, cv - rr * math.sin(math.radians(a0)))]
    pts += A.arc(0.0, cv, rr, -a0, 180 + a0, 10)[1:-1]
    pts += [(-sw, cv - rr * math.sin(math.radians(a0))), (-0.0018, -0.0078)]
    o = M.extrude_profile(name, A.ccw(pts), 0.0012, mat="M_Bakelite", bevel=0.0)
    # local XY -> wall plane (x, z), extrusion +Z -> out of the face
    n = Vector((0, out, 0))
    right = Vector((0, 0, 1)).cross(n)
    o.data.transform(A.frame_matrix((x, y, z), right, (0, 0, 1), n))
    return o


# ------------------------------------------------------------------ leaf
def leaf():
    parts = []
    seg = 2
    parts += [box("stile_lock", (LX0, LY0, LZ0), (LX0 + STILE, LY1, LZ1), MAH, 0.004, seg),
              box("stile_hinge", (LX1 - STILE, LY0, LZ0), (LX1, LY1, LZ1), MAH, 0.004, seg),
              box("rail_top", (LX0 + STILE, LY0, LZ1 - TOP_R), (LX1 - STILE, LY1, LZ1), MAH, 0.004, seg),
              box("rail_lock", (LX0 + STILE, LY0, LOCK_Z0), (LX1 - STILE, LY1, LOCK_Z1), MAH, 0.004, seg),
              box("rail_bot", (LX0 + STILE, LY0, LZ0), (LX1 - STILE, LY1, BOT_Z1), MAH, 0.004, seg),
              box("muntin", (-MUNTIN / 2, LY0, BOT_Z1), (MUNTIN / 2, LY1, LOCK_Z0), MAH, 0.004, seg)]
    # two fielded lower panels (double-sided, sitting in the frame grooves)
    pm = A.frame_matrix((0, LYM, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    ix0, ix1 = LX0 + STILE, LX1 - STILE
    openings = [(ix0, -MUNTIN / 2, BOT_Z1, LOCK_Z0), (MUNTIN / 2, ix1, BOT_Z1, LOCK_Z0)]
    for i, (a0, a1, b0, b1) in enumerate(openings):
        parts.append(A.raised_field(f"panel{i}", a0, a1, b0, b1, 0.045, 0.007, pm, mat=MAH, both=True, half_t=0.009))
    openings.append((ix0, ix1, GL_Z0, GL_Z1))
    # ogee mouldings / glazing beads on both faces
    for side in (True, False):
        up = (0, -1, 0) if side else (0, 1, 0)
        for i, (a0, a1, b0, b1) in enumerate(openings):
            parts.append(A.sweep(f"mould_{int(side)}_{i}", MOULD, face_rect(side, a0, a1, b0, b1), up=up, closed=True,
                                 mat=MAH))
    # frosted glass (in the stile grooves)
    parts.append(box("glass", (ix0 - 0.01, LYM - 0.003, GL_Z0 - 0.01), (ix1 + 0.01, LYM + 0.003, GL_Z1 + 0.01),
                     "M_Glass_Frosted", 0.0))
    # sign-written gold "7" with a black shadow line, and LABORATORY above it (room side of the glass)
    font = A.font_path()
    gy = LYM - 0.003
    rot = (math.pi / 2, 0, 0)
    parts.append(A.text_lowpoly("num7", "7", 0.36, depth=0.0003, loc=(0.0, gy - 0.0009, 1.555), rot=rot,
                             mat="M_Brass_Polished", font_path=font))
    parts.append(A.text_lowpoly("num7_shadow", "7", 0.36, depth=0.0003, loc=(0.006, gy - 0.0004, 1.549), rot=rot,
                             mat="M_Bakelite", font_path=font))
    parts.append(A.text_lowpoly("lab_word", "LABORATORY", 0.052, depth=0.0, resolution=1, loc=(0.0, gy - 0.0009, 1.865), rot=rot,
                             mat="M_Brass_Polished", font_path=font))
    for z in (1.825, 1.905):
        parts.append(box("gold_rule", (-0.17, gy - 0.0012, z - 0.0013), (0.17, gy - 0.0006, z + 0.0013), "M_Brass_Polished", 0.0))
    # brass furniture: kick plate, finger plate, long lock plates + keyholes on both faces
    parts.append(box("kick", (-0.43, LY0 - 0.0025, 0.045), (0.43, LY0, 0.245), BR, 0.0012, 2))
    parts.append(box("finger", (-0.444, LY0 - 0.002, 1.20), (-0.352, LY0, 1.50), BR, 0.0012, 2))
    for side, (y0, y1, out) in enumerate(((LY0 - 0.003, LY0, -1), (LY1, LY1 + 0.003, 1))):
        parts.append(box(f"lockplate{side}", (HANDLE_X - 0.026, y0, 0.925), (HANDLE_X + 0.026, y1, 1.165), BR, 0.0015, 2))
        yk = y0 if out < 0 else y1
        parts.append(keyhole(f"keyhole{side}", HANDLE_X, KEY_Z, yk, out))
        for z in (0.94, 1.15):
            parts.append(A.screw(f"lp_screw{side}", 0.0032, (HANDLE_X, yk, z), (0, out, 0), BR, 25 + 40 * side, segs=6))
    A.presmooth(parts)
    o = M.join(parts, "IA_door_leaf")
    M.set_origin(o, (PIN[0], PIN[1], 0.0))
    return o


def handle():
    parts = []
    for side, (yb, out) in enumerate(((LY0 - 0.003, -1), (LY1 + 0.003, 1))):
        # rose + boss
        rose = A.lathe_s(f"h_rose{side}", [(0.0, 0.0), (0.021, 0.0), (0.021, 0.003), (0.016, 0.008), (0.012, 0.010),
                                         (0.011, 0.024), (0.0125, 0.027), (0.0, 0.028)], segments=12, mat=BR)
        q = Vector((0, 0, 1)).rotation_difference(Vector((0, out, 0)))
        rose.data.transform(q.to_matrix().to_4x4())
        rose.location = (HANDLE_X, yb, HANDLE_Z)
        parts.append(rose)
        # lever: swept out from the boss toward the hinge, slight drop, thickened grip
        ya = yb + out * 0.022
        yl = yb + out * 0.040
        ctrl = [(HANDLE_X, ya, HANDLE_Z), (HANDLE_X + 0.012, yl, HANDLE_Z), (HANDLE_X + 0.05, yl, HANDLE_Z - 0.002),
                (HANDLE_X + 0.10, yl, HANDLE_Z - 0.006), (HANDLE_X + 0.128, yl + out * 0.004, HANDLE_Z - 0.010)]
        pts = A.catmull(ctrl, 3)
        rad = A.resample_radii(ctrl, [0.0085, 0.0075, 0.0068, 0.0082, 0.0088], 3)
        parts.append(A.tube(f"h_lever{side}", pts, 0.008, sides=8, radii=rad, mat=BR))
        tip = Vector(ctrl[-1])
        parts.append(A.sphere_s(f"h_tip{side}", 0.0088, loc=tuple(tip), segments=8, rings=5, mat=BR))
    A.presmooth(parts)
    o = M.join(parts, "IA_door_handle")
    M.set_origin(o, (HANDLE_X, LYM, HANDLE_Z))
    return o


# ------------------------------------------------------------------ frame, casing, maglock
def frame():
    parts = []
    parts += [box("jamb_l", (-OW / 2, 0.0, 0.014), (-JX, WT, OH), MAH, 0.003),
              box("jamb_r", (JX, 0.0, 0.014), (OW / 2, WT, OH), MAH, 0.003),
              box("jamb_head", (-OW / 2, 0.0, OH - JT), (OW / 2, WT, OH), MAH, 0.003),
              box("stop_l", (-JX, 0.103, 0.014), (-JX + 0.014, LY0 - 0.002, OH - JT), MAH, 0.002),
              box("stop_r", (JX - 0.014, 0.103, 0.014), (JX, LY0 - 0.002, OH - JT), MAH, 0.002),
              box("stop_head", (-JX, 0.103, OH - JT - 0.014), (JX, LY0 - 0.002, OH - JT), MAH, 0.002),
              box("threshold", (-OW / 2, -0.018, 0.0), (OW / 2, WT, 0.014), "M_Stone", 0.004, 2)]
    # walnut architrave, plinth blocks and capped head (room side)
    cas = A.profile_casing(w=CAS_W, t=0.034)
    parts.append(A.sweep("casing", cas, [(-CAS_IN, 0, PL_H), (-CAS_IN, 0, HEAD_IN), (CAS_IN, 0, HEAD_IN), (CAS_IN, 0, PL_H)],
                         up=(0, -1, 0), mat=WAL))
    for s in (-1, 1):
        x0, x1 = sorted((s * (CAS_IN - 0.008), s * (CAS_IN + CAS_W + 0.005)))
        parts.append(box(f"plinth{s}", (x0, -0.044, 0.0), (x1, 0.0, PL_H), WAL, 0.005, 2))
    top = HEAD_IN + CAS_W
    parts.append(box("head_fillet", (-CAS_IN - CAS_W - 0.012, -0.040, top), (CAS_IN + CAS_W + 0.012, 0.0, top + 0.012), WAL, 0.002))
    parts.append(box("head_cap", (-CAS_IN - CAS_W - 0.026, -0.054, top + 0.012), (CAS_IN + CAS_W + 0.026, 0.0, top + 0.036),
                     WAL, 0.006, 2))
    cove = [(0.0, 0.0), (0.0, -0.016), (0.004, -0.012), (0.009, -0.006), (0.014, 0.0)]
    parts.append(A.sweep("head_cove", cove, [(CAS_IN + CAS_W + 0.012, -0.040, top + 0.012), (-CAS_IN - CAS_W - 0.012, -0.040, top + 0.012)],
                         up=(0, 0, 1), mat=WAL))
    # hinge knuckles (corridor side, on the pin axis)
    for z in (0.28, 1.10, 1.92):
        k = A.lathe_s("knuckle", [(0.0, -0.062), (0.004, -0.061), (0.0078, -0.055), (0.0078, 0.055), (0.004, 0.061),
                                (0.0, 0.064)], segments=10, mat=BR)
        k.location = (PIN[0], PIN[1], z)
        parts.append(k)
    # maglock unit on the wall above the head cap
    mz0, mz1 = top + 0.050, top + 0.140
    mx0, mx1 = -0.30, 0.055
    parts.append(box("mag_box", (mx0, -0.075, mz0), (mx1, 0.0, mz1), "M_Steel_Painted", 0.007, 2))
    parts.append(box("mag_base", (mx0 - 0.012, -0.008, mz0 - 0.012), (mx1 + 0.012, 0.0, mz1 + 0.012), "M_Steel_Dark", 0.002))
    for (sx, sz) in ((mx0 + 0.012, mz0 + 0.012), (mx1 - 0.012, mz0 + 0.012), (mx0 + 0.012, mz1 - 0.012), (mx1 - 0.012, mz1 - 0.012)):
        parts.append(A.screw("mag_screw", 0.004, (sx, -0.075, sz), (0, -1, 0), BR, 15, segs=6))
    parts.append(box("mag_label", (-0.27, -0.0765, LAMP[2] - 0.016), (-0.06, -0.075, LAMP[2] + 0.016), "M_Enamel_Cream", 0.001))
    parts.append(A.text_lowpoly("mag_text", "MAGNETIC LOCK", 0.016, depth=0.0, resolution=1, loc=(-0.165, -0.0768, LAMP[2] - 0.001),
                             rot=(math.pi / 2, 0, 0), mat="M_Bakelite", font_path=A.font_path()))
    bez = A.lathe_s("mag_bezel", [(0.0145, 0.0), (0.022, 0.0), (0.023, 0.003), (0.020, 0.007), (0.0155, 0.0075),
                                (0.0145, 0.005)], segments=14, mat="M_Chrome")
    bez.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    bez.location = (LAMP[0], LAMP[1], LAMP[2])
    parts.append(bez)
    # armoured cable from the box into the wall
    cab = [(mx0 - 0.004, -0.036, LAMP[2]), (mx0 - 0.045, -0.036, LAMP[2]), (mx0 - 0.06, -0.03, LAMP[2] + 0.07),
           (mx0 - 0.06, -0.03, top + 0.40), (mx0 - 0.06, 0.004, top + 0.40)]
    parts.append(A.tube("mag_cable", cab, 0.0065, sides=8, fillet=0.016, mat="M_Steel_Dark"))
    parts.append(A.cyl_s("mag_gland", 0.011, 0.016, loc=(mx0 - 0.004, -0.036, LAMP[2]), rot=(0, math.pi / 2, 0), verts=10,
                            mat=BR, bevel=0.0012, segments=1))
    parts.append(A.cyl_s("mag_wallrose", 0.02, 0.008, loc=(mx0 - 0.06, -0.004, top + 0.40), rot=(math.pi / 2, 0, 0), verts=12,
                            mat="M_Steel_Dark", bevel=0.002, segments=1))
    A.presmooth(parts)
    o = M.join(parts, "door_frame")
    lamp = A.lathe_s("maglock_lamp", [(0.0, 0.0), (0.0145, 0.0), (0.0145, 0.004), (0.0125, 0.0095), (0.0085, 0.0128),
                                    (0.0, 0.014)], segments=18, mat="M_Emissive_Red")
    lamp.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    lamp.location = LAMP
    return o, lamp


def build():
    M.reset_scene()
    A.prepare_materials()
    fr, lamp = frame()
    lf = leaf()
    hd = handle()
    M.refresh()
    M.set_parent(hd, lf)
    A.presmooth([lamp])
    A.finalize_uv()
    # vertical grain on stiles / muntin / jambs / casing legs, and on the whole lower panels
    def panels(c, n):
        if abs(c.x) > MUNTIN / 2 + 0.003 and abs(c.x) < LX1 - STILE - 0.003 and BOT_Z1 + 0.003 < c.z < LOCK_Z0 - 0.003 \
                and LY0 + 0.005 < c.y < LY1 - 0.005:
            return True
        return None
    A.grain_uv(lf, force=panels)
    A.grain_uv(fr)
    print(f"[{NAME}] tris: frame={A.tris(fr)} leaf={A.tris(lf)} handle={A.tris(hd)} lamp={A.tris(lamp)} "
          f"TOTAL={M.tri_count()}")
    return dict(frame=fr, leaf=lf, handle=hd, lamp=lamp)


# ------------------------------------------------------------------ QA
def qa_context():
    """Room shell around the door: room -> door local = Rz(+90) . T(-3, +0.9, 0)."""
    A.import_glb(os.path.join(M.MODELS_DIR, "room_lab7.glb"), (-0.9, -3.0, 0.0), 90.0)
    A.qa_light("room", "POINT", (-0.4, -1.8, 2.3), 90.0, "FFC58A", size=0.15)
    A.qa_light("fill", "AREA", (0.6, -2.4, 1.6), 70.0, "C8D6EA", size=1.5, target=(0.0, 0.0, 1.2))
    A.qa_light("mag", "POINT", (0.0, -0.15, 2.35), 2.5, "FF3B2F", size=0.03)
    A.qa_light("corr", "AREA", (0.0, 1.6, 2.0), 40.0, "9FB6D8", size=1.0, target=(0.0, 0.0, 1.0))


def shot(name, cam, target, lens, res=(960, 640)):
    qa_context()
    M.render_preview(name, cam, target, lens=lens, res=res, samples=32, world_strength=0.05, lights=A.NO_LIGHTS)
    A.qa_reset_render_objects()


def main():
    args = M.main_guard()
    parts = build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(32, bounces=4)
    want = {a.split("=", 1)[1] for a in args if a.startswith("--shot=")}

    def on(k):
        return not want or k in want
    if on("1"):   # closed, from the room
        shot(NAME, (-1.05, -2.6, 1.45), (0.0, 0.0, 1.2), 30, res=(720, 900))
    if on("2"):   # glass numeral + lever close-up
        shot(NAME + "_2", (-0.30, -0.95, 1.40), (-0.12, 0.15, 1.42), 40, res=(900, 700))
    if on("4"):   # maglock unit
        shot(NAME + "_4", (0.10, -0.75, 2.30), (-0.10, 0.0, 2.33), 35, res=(900, 500))
    if on("3"):   # OPEN state: leaf -95 deg about the hinge pin, handle pressed (+40 about local Y)
        parts["leaf"].rotation_euler.z = math.radians(-95.0)
        parts["handle"].rotation_euler.y = math.radians(40.0)
        shot(NAME + "_3", (-1.2, -2.2, 1.9), (0.1, 0.5, 1.0), 26, res=(900, 700))


main()
