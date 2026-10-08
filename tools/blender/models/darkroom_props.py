"""darkroom_props.glb — dressing for Leyla's darkroom, built in ROOM coordinates (place at the origin).

Godot (x, y, z) = Blender (x, -z, y). Darkroom: x in [-4.8, -3.2], z in [-1.6, 0.4], ceiling 2.6.
Kept clear: the lamp table (-4.0, 0, 0.15) and its beam to the emblem, the north wall around x = -4.0
(y 0.4..2.0: emblem + cabinet), the west wall (evidence board z -1.3..0.1, y 1.0..2.0), the floor under the
wet bench where the UV shard lies (-4.55, 0.02, 0.15) and its camera ray, the camera spot of the
"shadow" view (-3.45, 1.6, 0.32), and the bookcase swing quadrant (within 1.16 m of (-3.1, -1.15)).

Clusters (separate objects -> compact tap blockers):
  wet_bench    SW corner x -4.78..-4.33, z -0.22..0.38: bench (open underneath), three enamel developing
               trays with developer, a print in the first tray, bamboo tongs, graduated cylinder, amber bottle
  wall_shelf   south wall above the bench (y 1.45): amber chemistry bottles, funnel, darkroom timer
  dry_bench    SE corner x -3.64..-3.22, z 0.05..0.38 + `enlarger` (column on the east wall)
  drying_line  cord from the west to the east wall at z = 0.05, y = 2.12, wooden pegs, a film strip
  print_0..3   hanging prints, M_Decal_Photos, own 0..1 UVs; image faces north (Godot -Z), not mirrored
  stool        (-4.45, 0, -0.45);  bucket  NW corner (-4.60, 0, -1.42)

Run: blender -b --factory-startup -P tools/blender/models/darkroom_props.py [-- --no-render]
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
import lib_props as P  # noqa: E402
import lib_mech as K  # noqa: E402

NAME = "darkroom_props"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
M.material("M_Glass_Amber", color="5A2A0C", rough=0.08, alpha=0.82)
M.material("M_Enamel_Cobalt", color="1F46A6", rough=0.28)
M.material("M_Enamel_White", color="EAE4D4", rough=0.3)
G = P.gd
rnd = random.Random(1979)


def gbox(name, size, centre, mat="M_Wood_Panel", bevel=0.003, segments=1, rot_y_deg=0.0):
    """Box with size and centre in GODOT axes (x, y, z); optional yaw about Godot +Y."""
    o = M.box(name, (size[0], size[2], size[1]), loc=G(*centre), mat=mat, bevel=bevel, segments=segments)
    o.rotation_euler = (0, 0, math.radians(rot_y_deg))
    return o


def glathe(name, profile, base, segments=16, mat="M_Glass_Amber"):
    """Lathe about the vertical axis standing on the Godot point `base`."""
    return M.lathe(name, profile, loc=G(*base), segments=segments, mat=mat)


def bottle(name, base, h=0.2, r=0.042, label=True, cap="M_Bakelite", face=(1.0, 0.0, 0.0)):
    """Amber chemistry bottle (solid: amber glass reads opaque in the dark), bakelite cap, paper label."""
    o = [(0.0, 0.0), (r * 0.93, 0.0), (r, 0.006), (r, h * 0.72), (r * 0.86, h * 0.8), (r * 0.42, h * 0.89), (r * 0.36, h * 0.93),
         (0.0, h * 0.93)]
    parts = [glathe(name, o, base, segments=12)]
    parts.append(glathe(name + "_cap", [(0.0, h * 0.925), (r * 0.42, h * 0.925), (r * 0.44, h * 0.94), (r * 0.44, h * 1.02),
                                        (r * 0.4, h * 1.03), (0.0, h * 1.03)], base, segments=10, mat=cap))
    if label:
        lab = glathe(name + "_label", [(r + 0.0006, h * 0.25), (r + 0.0006, h * 0.58)], base, segments=12, mat="M_Paper")
        bm = bmesh.new()
        bm.from_mesh(lab.data)
        fv = Vector(face)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.5 or f.calc_center_median().dot(fv) < r * 0.1],
                         context="FACES")
        bm.to_mesh(lab.data)
        bm.free()
        parts.append(lab)
    return parts


# ================================================================ 1. wet bench (SW corner), open underneath
WX0, WX1, WZ0, WZ1 = -4.78, -4.33, -0.22, 0.38
WTOP = 0.86
wcx, wcz = (WX0 + WX1) / 2, (WZ0 + WZ1) / 2
wb = []
wb.append(gbox("wb_top", (WX1 - WX0, 0.03, WZ1 - WZ0), (wcx, WTOP - 0.015, wcz), bevel=0.004, segments=1))
for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    wb.append(gbox(f"wb_leg{sx}{sz}", (0.045, WTOP - 0.03, 0.045), (wcx + sx * ((WX1 - WX0) / 2 - 0.03), (WTOP - 0.03) / 2,
                                                                  wcz + sz * ((WZ1 - WZ0) / 2 - 0.03)), bevel=0.003))
wb.append(gbox("wb_apron_back", (0.02, 0.1, WZ1 - WZ0 - 0.1), (WX0 + 0.018, WTOP - 0.08, wcz)))
wb.append(gbox("wb_apron_front", (0.02, 0.055, WZ1 - WZ0 - 0.1), (WX1 - 0.018, WTOP - 0.058, wcz)))
for sz in (-1, 1):
    wb.append(gbox(f"wb_apron_side{sz}", (WX1 - WX0 - 0.1, 0.1, 0.02), (wcx, WTOP - 0.08, wcz + sz * ((WZ1 - WZ0) / 2 - 0.018))))
    wb.append(gbox(f"wb_stretcher{sz}", (WX1 - WX0 - 0.1, 0.035, 0.022), (wcx, 0.15, wcz + sz * ((WZ1 - WZ0) / 2 - 0.03))))
wb.append(gbox("wb_stretcher_back", (0.022, 0.035, WZ1 - WZ0 - 0.1), (WX0 + 0.03, 0.15, wcz)))
# zinc-lined splash rim around the top
for sz in (-1, 1):
    wb.append(gbox(f"wb_rim_z{sz}", (WX1 - WX0, 0.022, 0.014), (wcx, WTOP + 0.011, wcz + sz * ((WZ1 - WZ0) / 2 - 0.007)),
                   mat="M_Steel_Dark", bevel=0.002))
wb.append(gbox("wb_rim_back", (0.014, 0.05, WZ1 - WZ0), (WX0 + 0.007, WTOP + 0.025, wcz), mat="M_Steel_Dark", bevel=0.002))
wb.append(gbox("wb_lining", (WX1 - WX0 - 0.02, 0.002, WZ1 - WZ0 - 0.02), (wcx, WTOP + 0.001, wcz), mat="M_Steel_Dark", bevel=0.0))

# three enamel developing trays: developer, stop, fix (white enamel, cobalt rim), with liquid
TW, TD, TH = 0.25, 0.185, 0.045
for i, tz in enumerate((-0.12, 0.08, 0.28)):
    base = G(wcx + 0.01, WTOP + 0.002, tz)
    rings = [(TW - 0.012, TD - 0.012, 0.012, 0.0), (TW - 0.004, TD - 0.004, 0.014, 0.004), (TW, TD, 0.015, TH - 0.004),
             (TW + 0.004, TD + 0.004, 0.016, TH - 0.001), (TW + 0.002, TD + 0.002, 0.016, TH + 0.002),
             (TW - 0.008, TD - 0.008, 0.012, TH), (TW - 0.026, TD - 0.026, 0.01, 0.006)]
    tray = P.rrect_loft(f"tray{i}", rings, mat="M_Enamel_White", n=2,
                        ring_mats=["M_Enamel_Cobalt", "M_Enamel_White", "M_Enamel_Cobalt", "M_Enamel_Cobalt", "M_Enamel_White",
                                   "M_Enamel_White"])
    # long side across the bench (Godot x), the three trays in a row along the bench (Godot z)
    tray.location = base
    wb.append(tray)
    liq = P.rrect_loft(f"tray_liquid{i}", [(TW - 0.02, TD - 0.02, 0.011, 0.024), (TW - 0.02, TD - 0.02, 0.011, 0.0245)],
                       mat="M_Glass", n=2, cap_bottom=False)
    liq.location = base
    wb.append(liq)
# a print developing in the first tray (under the liquid) and bamboo tongs on the rims
pr = gbox("tray_print", (0.165, 0.0008, 0.125), (wcx + 0.01, WTOP + 0.002 + 0.008, -0.12), mat="M_Paper", bevel=0.0, rot_y_deg=6)
wb.append(pr)
for i, (tz, ang) in enumerate(((-0.12, 18), (0.08, -12))):
    c = G(wcx + 0.02, WTOP + 0.002 + TH + 0.006, tz)
    d = Matrix.Rotation(math.radians(ang), 3, "Z") @ Vector((1.0, 0.0, 0.0))
    a, b = c - d * 0.1, c + d * 0.1
    for s in (-1, 1):
        off = Matrix.Rotation(math.radians(ang), 3, "Z") @ Vector((s * 0.006, 0, 0))
        wb.append(P.rod(f"tong{i}{s}", a + off, b + off * 0.4 + Vector((0, 0, -0.006)), 0.0035, sides=6, mat="M_Wood_Panel"))
    wb.append(M.cylinder(f"tong_tip{i}", 0.006, 0.02, loc=b + Vector((0, 0, -0.007)), rot=(math.pi / 2, 0, math.radians(ang)), verts=8,
                         mat="M_Rubber", bevel=0.001, segments=1))
# graduated cylinder + an amber stock bottle on the bench back corner
gcz = 0.355
wb.append(glathe("wb_graduate", P.shell_profile([(0.0, 0.012), (0.026, 0.012), (0.026, 0.25), (0.029, 0.253)], 0.0016),
                 (WX0 + 0.06, WTOP + 0.002, -0.19), segments=10, mat="M_Glass"))
wb.append(glathe("wb_graduate_foot", [(0.0, 0.0), (0.045, 0.0), (0.045, 0.006), (0.03, 0.012), (0.0, 0.012)],
                 (WX0 + 0.06, WTOP + 0.002, -0.19), segments=6, mat="M_Glass"))
wb += bottle("wb_bottle", (WX0 + 0.06, WTOP + 0.002, 0.02), h=0.24, r=0.05)
wet_bench = M.join(wb, "wet_bench")

# ================================================================ 2. wall shelf above the wet bench (south wall)
SH_Y = 1.45
SZ = 0.40 - 0.09
ws = [gbox("ws_board", (WX1 - WX0, 0.022, 0.18), (wcx, SH_Y - 0.011, SZ), bevel=0.003, segments=2),
      gbox("ws_lip", (WX1 - WX0, 0.03, 0.01), (wcx, SH_Y + 0.004, SZ - 0.085), bevel=0.002)]
for sx in (-1, 1):
    x = wcx + sx * 0.15
    br = M.extrude_profile(f"ws_bracket{sx}", [(0.0, 0.0), (0.012, 0.0), (0.012, 0.11), (0.04, 0.138), (0.15, 0.138), (0.15, 0.15),
                                              (0.0, 0.15)], 0.008, mat="M_Steel_Dark", bevel=0.001)
    br.rotation_euler = (math.pi / 2, 0, math.pi / 2)    # outline x -> +Y (toward the room, Godot -Z), y -> up, extrusion -X
    br.location = G(x - 0.004, SH_Y - 0.172, 0.40)
    ws.append(br)
for i, (bx, h, r) in enumerate(((-4.73, 0.22, 0.05), (-4.64, 0.17, 0.04), (-4.565, 0.24, 0.052), (-4.38, 0.15, 0.035))):
    ws += bottle(f"ws_bottle{i}", (bx, SH_Y, SZ + rnd.uniform(-0.03, 0.02)), h=h, r=r, face=(0.25, 1.0, 0.0))
# darkroom timer (bakelite case, cream dial, red sweep hand)
TIM = G(-4.46, SH_Y + 0.085, SZ + 0.03)       # dial centre; the dial faces the room (Blender +Y = Godot -Z)
ws.append(P.lathe_axis("ws_timer_case", [(0.0, 0.0), (0.07, 0.0), (0.075, 0.006), (0.075, 0.04), (0.068, 0.046), (0.062, 0.044),
                                         (0.0, 0.044)], axis="Y", segments=16, mat="M_Bakelite", loc=TIM + Vector((0, -0.044, 0))))
ws.append(P.lathe_axis("ws_timer_dial", [(0.0, 0.0), (0.06, 0.0), (0.0, 0.0005)], axis="Y", segments=24, mat="M_Enamel_Cream",
                       loc=TIM + Vector((0, -0.0022, 0))))
for k in range(4):
    a = 2 * math.pi * k / 4
    ws.append(M.box(f"ws_tick{k}", (0.0025, 0.0006, 0.01),
                    loc=TIM + Vector((0.05 * math.sin(a), -0.0012, 0.05 * math.cos(a))), rot=(0, a, 0), mat="M_Bakelite", bevel=0.0))
ws.append(M.box("ws_hand", (0.003, 0.0008, 0.048), loc=TIM + Vector((0.008, -0.0008, 0.018)), rot=(0, math.radians(25), 0),
                mat="M_Enamel_Crimson", bevel=0.0))
ws.append(M.box("ws_timer_foot", (0.11, 0.05, 0.012), loc=TIM + Vector((0, -0.022, -0.079)), mat="M_Bakelite", bevel=0.003))
wall_shelf = M.join(ws, "wall_shelf")

# ================================================================ 3. dry bench + enlarger (SE corner, column on the east wall)
DX0, DX1, DZ0, DZ1 = -3.64, -3.22, 0.05, 0.38
DTOP = 0.76
dcx, dcz = (DX0 + DX1) / 2, (DZ0 + DZ1) / 2
db = [gbox("db_top", (DX1 - DX0, 0.03, DZ1 - DZ0), (dcx, DTOP - 0.015, dcz), bevel=0.004, segments=2),
      gbox("db_body", (DX1 - DX0 - 0.02, DTOP - 0.1, DZ1 - DZ0 - 0.02), (dcx, (DTOP - 0.03 + 0.07) / 2, dcz + 0.005), bevel=0.003),
      gbox("db_plinth", (DX1 - DX0 - 0.04, 0.07, DZ1 - DZ0 - 0.05), (dcx, 0.035, dcz + 0.01), bevel=0.002)]
for i, (z0, z1) in enumerate(((DZ0 + 0.015, dcz - 0.002), (dcz + 0.002, DZ1 - 0.01))):
    door = P.raised_panel(f"db_door{i}", z1 - z0, DTOP - 0.16, 0.016, field_inset=0.03, raise_=0.004)
    door.data.transform(Matrix.Rotation(-math.pi / 2, 4, "Z"))     # front now faces -X (into the room)
    door.location = G(DX0 + 0.012, (DTOP - 0.03 + 0.09) / 2, (z0 + z1) / 2)
    db.append(door)
    kz = z1 - 0.03 if i == 0 else z0 + 0.03
    db.append(P.lathe_axis(f"db_knob{i}", [(0.0, 0.0), (0.006, 0.0), (0.0045, 0.008), (0.009, 0.016), (0.0, 0.019)], axis="X", sign=-1,
                           segments=10, mat="M_Brass_Aged", loc=G(DX0 - 0.004, DTOP - 0.17, kz)))
# box of photographic paper on the bench
db.append(gbox("db_paperbox", (0.2, 0.035, 0.15), (dcx - 0.06, DTOP + 0.0175, DZ0 + 0.09), mat="M_Bakelite", bevel=0.002,
               rot_y_deg=-6))
db.append(gbox("db_paperbox_lid", (0.205, 0.012, 0.155), (dcx - 0.06, DTOP + 0.035 + 0.004, DZ0 + 0.09), mat="M_Enamel_Crimson",
               bevel=0.002, rot_y_deg=-6))
dry_bench = M.join(db, "dry_bench")

en = []
EX = -3.255                                 # column axis (against the east wall)
EZ = 0.22
en.append(gbox("en_base", (0.3, 0.025, 0.3), (-3.43, DTOP + 0.0125, EZ), mat="M_Wood_Panel", bevel=0.004, segments=2))
en.append(gbox("en_easel", (0.22, 0.006, 0.18), (-3.45, DTOP + 0.028, EZ - 0.005), mat="M_Enamel_White", bevel=0.002))
for sx in (-1, 1):
    en.append(gbox(f"en_easel_blade{sx}", (0.012, 0.01, 0.2), (-3.45 + sx * 0.1, DTOP + 0.032, EZ - 0.005), mat="M_Steel_Dark",
                   bevel=0.002))
en.append(gbox("en_clamp", (0.06, 0.04, 0.08), (EX, DTOP + 0.045, EZ), mat="M_Steel_Dark", bevel=0.004))
en.append(M.cylinder("en_column", 0.018, 0.68, loc=G(EX, DTOP + 0.06 + 0.34, EZ), verts=14, mat="M_Chrome", bevel=0.002))
en.append(M.cylinder("en_column_cap", 0.022, 0.016, loc=G(EX, DTOP + 0.74, EZ), verts=14, mat="M_Steel_Dark", bevel=0.003))
HEAD_Y = DTOP + 0.5
en.append(gbox("en_carriage", (0.06, 0.08, 0.06), (EX, HEAD_Y, EZ), mat="M_Steel_Painted", bevel=0.006, segments=2))
en.append(P.lathe_axis("en_lock_knob", [(0.0, 0.0), (0.012, 0.0), (0.014, 0.004), (0.014, 0.012), (0.01, 0.016), (0.0, 0.017)],
                       axis="Y", sign=-1, segments=12, mat="M_Bakelite", loc=G(EX, HEAD_Y - 0.02, EZ + 0.03)))
en.append(gbox("en_arm", (0.17, 0.04, 0.05), (EX - 0.1, HEAD_Y + 0.02, EZ), mat="M_Steel_Painted", bevel=0.006, segments=2))
LH = Vector((-3.45, HEAD_Y + 0.06, EZ))      # lamphouse centre (Godot)
en.append(glathe("en_lamphouse", [(0.0, -0.06), (0.075, -0.06), (0.08, -0.05), (0.08, 0.02), (0.07, 0.045), (0.045, 0.07),
                                  (0.03, 0.075), (0.0, 0.076)], (LH.x, LH.y, LH.z), segments=16, mat="M_Steel_Painted"))
en.append(glathe("en_vent", [(0.0, 0.074), (0.03, 0.074), (0.03, 0.1), (0.04, 0.102), (0.04, 0.11), (0.0, 0.112)],
                 (LH.x, LH.y, LH.z), segments=12, mat="M_Steel_Dark"))
en.append(gbox("en_filter_drawer", (0.11, 0.025, 0.11), (LH.x, LH.y - 0.075, LH.z), mat="M_Steel_Dark", bevel=0.004))
# bellows: square folds shrinking toward the lens
for k in range(5):
    s = 0.1 - 0.01 * k
    en.append(gbox(f"en_bellows{k}", (s, 0.019, s), (LH.x, LH.y - 0.1 - 0.019 * k, LH.z), mat="M_Leather", bevel=0.004))
en.append(gbox("en_lensboard", (0.09, 0.008, 0.09), (LH.x, LH.y - 0.2, LH.z), mat="M_Steel_Dark", bevel=0.003))
en.append(glathe("en_lens", [(0.0, -0.05), (0.022, -0.05), (0.026, -0.045), (0.026, -0.02), (0.03, -0.015), (0.03, 0.0), (0.0, 0.0)],
                 (LH.x, LH.y - 0.203, LH.z), segments=12, mat="M_Steel_Dark"))
en.append(glathe("en_lens_glass", [(0.0, -0.0505), (0.019, -0.0505), (0.0, -0.0495)], (LH.x, LH.y - 0.203, LH.z), segments=12,
                 mat="M_Glass"))
en.append(P.lathe_axis("en_focus_knob", [(0.0, 0.0), (0.016, 0.0), (0.018, 0.004), (0.018, 0.014), (0.014, 0.018), (0.0, 0.019)],
                       axis="Y", sign=1, segments=14, mat="M_Bakelite", loc=G(EX - 0.02, HEAD_Y, EZ - 0.03)))
en.append(P.tube("en_cable", [G(EX + 0.01, HEAD_Y + 0.1, EZ + 0.06), G(EX + 0.015, HEAD_Y - 0.1, EZ + 0.1),
                              G(EX + 0.02, DTOP + 0.02, EZ + 0.13), G(EX + 0.02, DTOP + 0.005, DZ1 - 0.01)], 0.0035, sides=6,
                 mat="M_Fabric"))
enlarger = M.join(en, "enlarger")

# ================================================================ 4. drying line with pegs, four prints and a film strip
LY, LZ = 2.12, 0.05
LX0, LX1 = -4.79, -3.21
line = []
sag = []
for i in range(17):
    t = i / 16
    sag.append(G(LX0 + (LX1 - LX0) * t, LY - 0.05 * math.sin(math.pi * t), LZ))
line.append(P.tube("dl_cord", sag, 0.0018, sides=5, mat="M_Fabric", caps=False))
for x in (LX0, LX1):
    sx = 1 if x < -4.0 else -1
    line.append(P.lathe_axis(f"dl_eye{sx}", [(0.0, 0.0), (0.006, 0.0), (0.005, 0.004), (0.0, 0.005)], axis="X", sign=sx, segments=8,
                             mat="M_Brass_Aged", loc=G(x - sx * 0.01, LY, LZ)))
    line.append(M.torus(f"dl_ring{sx}", 0.008, 0.0016, loc=G(x + sx * 0.002, LY, LZ), rot=(0, math.pi / 2, 0), major_seg=10,
                        minor_seg=4, mat="M_Brass_Aged"))


def line_y(x):
    t = (x - LX0) / (LX1 - LX0)
    return LY - 0.05 * math.sin(math.pi * t)


def peg(name, x, yaw=0.0):
    """Wooden spring clothes-peg clamped on the cord at x (Godot), jaws down."""
    y = line_y(x)
    c = G(x, y - 0.012, LZ)
    parts = []
    for s in (-1, 1):
        parts.append(M.box(f"{name}_jaw{s}", (0.009, 0.0045, 0.072), loc=c + Vector((0, s * 0.0028, 0.0)), mat="M_Wood_Panel",
                           bevel=0.0, segments=1))
    parts.append(M.torus(f"{name}_spring", 0.0042, 0.0011, loc=c + Vector((0, 0, 0.012)), rot=(0, math.pi / 2, 0), major_seg=6,
                         minor_seg=3, mat="M_Steel_Dark"))
    g = M.join(parts, name)
    M.set_origin(g, c)
    g.rotation_euler = (0, 0, math.radians(yaw))
    return g


prints = []
PW, PH = 0.13, 0.165
for k, (x, yaw) in enumerate(((-4.62, 6), (-4.43, -4), (-4.22, 9), (-4.02, -7))):
    top = line_y(x) - 0.012 - 0.022
    verts = [(-PW / 2, 0, -PH), (PW / 2, 0, -PH), (PW / 2, 0, 0), (-PW / 2, 0, 0)]
    pobj = P.mesh_obj(f"print_{k}", verts, [(0, 1, 2, 3)], ["M_Decal_Photos"])
    P.fix_normals(pobj)
    if pobj.data.polygons[0].normal.y < 0:      # print image faces Blender +Y = Godot -Z (toward the room / north)
        pobj.data.flip_normals()
    # photo UVs: u -> -X seen from the front (north side), so the image is not mirrored when looked at from the room
    me = pobj.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (0.5 - v.x / PW, 1.0 + v.z / PH)
    # slight curl: bend the bottom toward the room
    pobj.location = G(x, top, LZ)
    pobj.rotation_euler = (0, 0, math.radians(yaw))
    prints.append(pobj)
    line.append(peg(f"peg{k}", x, yaw))
# film strip (dark negative) with a weight clip
fx = -3.72
ftop = line_y(fx) - 0.03
line.append(gbox("film", (0.035, 0.42, 0.0006), (fx, ftop - 0.21, LZ), mat="M_Bakelite", bevel=0.0, rot_y_deg=12))
line.append(gbox("film_clip", (0.045, 0.02, 0.008), (fx, ftop - 0.42, LZ), mat="M_Steel_Dark", bevel=0.002, rot_y_deg=12))
line.append(peg("peg_film", fx, 12))
drying_line = M.join(line, "drying_line")

# ================================================================ 5. lab stool and 6. galvanised bucket
SC = (-4.45, 0.0, -0.45)
stp = [glathe("st_seat", [(0.0, 0.6), (0.155, 0.6), (0.165, 0.607), (0.166, 0.622), (0.158, 0.632), (0.0, 0.635)], SC, segments=20,
              mat="M_Wood_Panel"),
       glathe("st_hub", [(0.0, 0.565), (0.07, 0.565), (0.075, 0.585), (0.07, 0.6), (0.0, 0.6)], SC, segments=12, mat="M_Steel_Painted")]
for i in range(4):
    a = math.radians(45 + 90 * i)
    d = Vector((math.cos(a), math.sin(a), 0))
    top = G(*SC) + d * 0.06 + Vector((0, 0, 0.575))
    foot = G(*SC) + d * 0.2 + Vector((0, 0, 0.012))
    stp.append(P.tube(f"st_leg{i}", [top, top.lerp(foot, 0.5) + d * 0.004, foot], 0.0115, sides=8, mat="M_Steel_Painted"))
    stp.append(glathe(f"st_foot{i}", [(0.0, 0.0), (0.015, 0.0), (0.013, 0.014), (0.0, 0.015)], (foot.x, 0.0, -foot.y), segments=6,
                      mat="M_Rubber"))
ring_r = 0.155
stp.append(M.torus("st_ring", ring_r, 0.0075, loc=G(SC[0], 0.22, SC[2]), major_seg=16, minor_seg=4, mat="M_Steel_Painted"))
stool = M.join(stp, "stool")

BC = (-4.60, 0.0, -1.42)
bk = [glathe("bk_body", P.shell_profile([(0.0, 0.0), (0.098, 0.0), (0.1, 0.006), (0.104, 0.03), (0.128, 0.275), (0.132, 0.28)], 0.0012,
                                        lip=0.003), BC, segments=18, mat="M_Steel_Dark"),
      glathe("bk_water", [(0.0, 0.17), (0.12, 0.17), (0.0, 0.1702)], BC, segments=16, mat="M_Glass")]
for s in (-1, 1):
    bk.append(gbox(f"bk_ear{s}", (0.012, 0.03, 0.018), (BC[0] + s * 0.131, 0.26, BC[2]), mat="M_Steel_Dark", bevel=0.0))
bail = [G(BC[0] + 0.136 * math.cos(a), 0.262 + 0.13 * math.sin(a) * 0.9, BC[2] - 0.03 * math.sin(a)) for a in
        [math.pi * i / 10 for i in range(11)]]
bk.append(P.tube("bk_bail", bail, 0.0025, sides=6, mat="M_Steel_Dark"))
bk.append(P.tube("bk_grip", [bail[4], bail[6]], 0.007, sides=8, mat="M_Wood_Panel"))
bk.append(P.rod("bk_paddle", G(BC[0] + 0.05, 0.05, BC[2] + 0.04), G(BC[0] + 0.12, 0.46, BC[2] + 0.11), 0.008, sides=8, mat="M_Wood_Panel"))
bucket = M.join(bk, "bucket")

M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)


# ================================================================ QA renders
def want(tag):
    return "--shots" not in ARGS or tag in ARGS[ARGS.index("--shots") + 1].split(",")


if "--no-render" not in ARGS:
    P.preview_tweak()
    P.render_threads(2)
    bpy.context.scene.cycles.max_bounces = 6
    for k in range(4):
        o = bpy.data.objects[f"print_{k}"]
        o.data.materials.clear()
        o.data.materials.append(P.photo_preview_material(4 + k))
    P.qa_box("qa_floor", (1.6, 2.0, 0.02), G(-4.0, -0.01, -0.6), colour="3A2A1E", rough=0.7)
    P.qa_box("qa_north", (1.6, 0.04, 2.6), (-4.0, 1.62, 1.3), colour="A8A190")
    P.qa_box("qa_west", (0.04, 2.0, 2.6), (-4.82, 0.6, 1.3), colour="A39C8B")
    P.qa_box("qa_south", (1.6, 0.04, 2.6), (-4.0, -0.42, 1.3), colour="A39C8B")
    P.qa_box("qa_ceiling", (1.6, 2.0, 0.04), (-4.0, 0.6, 2.62), colour="8E887A")
    P.qa_box("qa_east_s", (0.04, 0.45, 2.6), (-3.18, -0.175, 1.3), colour="A39C8B")
    P.qa_box("qa_east_n", (0.04, 0.45, 2.6), (-3.18, 1.375, 1.3), colour="A39C8B")
    P.qa_box("qa_east_top", (0.04, 1.1, 0.45), (-3.18, 0.6, 2.375), colour="A39C8B")
    # neighbours for context (their exported GLBs, untextured): shadow lock in room space, evidence board on the west wall
    for glb, loc, yaw in (("shadow_lock", (0, 0, 0), 0.0), ("evidence_board", G(-4.8, 1.5, -0.6), 90.0)):
        path = os.path.join(M.MODELS_DIR, glb + ".glb")
        if not os.path.exists(path):
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        root = bpy.data.objects.new("qa_root_" + glb, None)
        bpy.context.scene.collection.objects.link(root)
        for o in new:
            o.name = "qa_" + o.name
            if o.parent is None:
                o.parent = root
        root.location = loc
        root.rotation_euler = (0, 0, math.radians(yaw))
    P.qa_light("qa_bulb", "POINT", G(-4.0, 2.45, -0.6), 14.0, colour="FFD6A0", radius=0.03)
    P.qa_light("qa_red", "SPOT", G(-4.55, 1.95, 0.25), 18.0, colour="FF2A1A", radius=0.06, direction=(0, 0.88, -0.47),
               half_angle_deg=60.0, blend=0.8)
    soft = [((0.6, -0.8, 0.6), 60, "FFE2C0", 2.0)]
    if want("1"):   # the lead's "darkroom" view, looking west
        M.render_preview(NAME, G(-3.3, 1.5, -0.55), G(-4.8, 1.35, -0.75), lens=19.5, res=(960, 640), samples=32,
                         world_strength=0.25, lights=soft)
    if want("2"):   # wet side: bench, shelf, drying line
        M.render_preview(NAME + "_2", G(-3.85, 1.55, -0.65), G(-4.55, 1.2, 0.2), lens=24, res=(960, 640), samples=32,
                         world_strength=0.3, lights=soft)
    if want("3"):   # dry side: enlarger in the SE corner
        M.render_preview(NAME + "_3", G(-3.85, 1.45, -0.35), G(-3.42, 1.0, 0.25), lens=26, res=(960, 640), samples=32,
                         world_strength=0.3, lights=soft)
    if want("4"):   # floor view toward the shard spot (lead's "darkroom_floor" camera) — the floor under the bench stays visible
        P.qa_light("qa_shard", "POINT", G(-4.55, 0.05, 0.15), 0.6, colour="CFF6FF", radius=0.01)
        M.render_preview(NAME + "_4", G(-3.9, 0.9, -0.3), G(-4.5, 0.0, 0.2), lens=26, res=(960, 640), samples=32,
                         world_strength=0.6, lights=[((0.3, -1.0, 0.4), 160, "FFE2C0", 2.0)])
