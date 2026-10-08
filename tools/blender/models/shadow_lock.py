"""shadow_lock.glb — Leyla's shadow lock in the darkroom (puzzle P10), built in ROOM coordinates.

Place the GLB at the room origin (Godot transform identity). Godot (x, y, z) = Blender (x, -z, y).

Optics (Godot): the lantern's `light_origin`, the gimbal centre S = (-4.0, 1.25, -0.60) and the emblem
centre C = (-4.0, 1.50, -1.60) on the north-wall surface are collinear, so the real-time shadow of
ring + rod is always centred on IA_emblem_socket. With the ring plane parallel to the wall (yaw 0)
its shadow is a perfect circle (parallel planes); the rod then draws the meridian.
  light_origin  = (-4.0, 1.080, 0.080), local -Z = beam axis, pitched up 14.04 deg toward C.
  magnification = |C - L| / |S - L| = 1.68 / 0.68 = 2.47 -> ring shadow r = 0.247 m, rod shadow 0.69 m.
  `emblem_paint` (M_Decal_Emblem, wall_emblem.png) is scaled so its circle and meridian match that shadow.

Interactive parts (origin = pivot):
  sculpture_ring  origin S; rotates about Godot +Y (local UP). REST = +60 deg yaw from aligned.
  sculpture_rod   CHILD of the ring (nested gimbal: its shoes ride on the ring band), origin on the
                  ring axis 11.5 mm in front of S; rotates about its local +Z (Godot BACK = the ring
                  normal = the lamp->wall axis whenever the ring is aligned). REST = +60 deg tilt.
  IA_ring_knob    horizontal knurled wheel on the stand head (axis Godot +Y).
  IA_rod_knob     knurled knob on the head front (axis Godot +Z).
  IA_emblem_socket  brass socket on the wall (origin (-4.0, 1.5, -1.585)); child `socket_lens` (M_Crystal).
  IA_cabinet_door origin on the hinge (front-left edge, mid-height); opens with NEGATIVE yaw (Godot +Y).
  spot_lamp (origin = tilt trunnion) with children `spot_bulb` (M_Emissive_Warm) and empty `light_origin`.
  safelight (M_Emissive_Red filter glass) with child empty `safelight_origin`.

Run: blender -b --factory-startup -P tools/blender/models/shadow_lock.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_props as P  # noqa: E402
import lib_mech as K  # noqa: E402

NAME = "shadow_lock"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
G = P.gd

# ---------------------------------------------------------------- optics (Godot coordinates)
S_G = Vector((-4.0, 1.25, -0.60))          # gimbal centre
C_G = Vector((-4.0, 1.50, -1.60))          # emblem centre on the wall surface
WALL_Z = -1.60
L_Z = 0.08                                 # light origin depth
k = (L_Z - S_G.z) / (S_G.z - C_G.z)
L_G = S_G + (S_G - C_G) * k                # (-4.0, 1.08, 0.08)
MAG = (L_G - C_G).length / (L_G - S_G).length
BEAM_G = (C_G - L_G).normalized()          # toward the wall
S, C, L = G(*S_G), G(*C_G), G(*L_G)
BEAM = Vector((BEAM_G.x, -BEAM_G.z, BEAM_G.y))
PITCH = math.atan2(BEAM.z, BEAM.y)         # 14.04 deg up
R_PITCH = Matrix.Rotation(PITCH, 4, "X")
RING_R = 0.10
ROD_LEN = 0.28
REST_YAW = math.radians(60.0)
REST_TILT = math.radians(60.0)
ROD_DZ = 0.0115                            # rod plane in front of the ring plane (toward the lamp)
print(f"[shadow_lock] light_origin Godot {tuple(round(c, 4) for c in L_G)} pitch {math.degrees(PITCH):.2f} "
      f"mag {MAG:.4f} ring-shadow r {RING_R * MAG:.4f}")



def dbg(parts, label):
    if "--debug" in ARGS:
        rows = sorted(((M.tri_count([o]), o.name) for o in parts), reverse=True)
        print(f"[dbg] {label}: " + ", ".join(f"{n}={t}" for t, n in rows[:14]))


# ================================================================ 1. small walnut table (Godot centre (-4.0, 0, 0.15))
TC = G(-4.0, 0.0, 0.15)
TW, TD, TH = 0.56, 0.46, 0.70
table = []
top = M.box("t_top", (TW, TD, 0.028), loc=(TC.x, TC.y, TH - 0.014), bevel=0.007, segments=2)
table.append(top)
AP_IN = 0.035                                  # apron inset from the top edge
ax0, ax1 = TC.x - TW / 2 + AP_IN, TC.x + TW / 2 - AP_IN
ay0, ay1 = TC.y - TD / 2 + AP_IN, TC.y + TD / 2 - AP_IN
LEG = 0.042
for i, (lx, ly) in enumerate(((ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1))):
    sx = 1 if lx > TC.x else -1
    sy = 1 if ly > TC.y else -1
    table.append(P.tapered_leg(f"t_leg{i}", LEG, 0.028, TH - 0.028,
                               loc=(lx - sx * LEG / 2, ly - sy * LEG / 2, 0.0),
                               foot_inset=(sx * 0.006, sy * 0.006), bevel=0.003))
    # brass ferrule cups on the feet
    table.append(M.cylinder(f"t_cup{i}", 0.0215, 0.022, loc=(lx - sx * (LEG / 2 - 0.006), ly - sy * (LEG / 2 - 0.006), 0.011),
                            verts=4, rot=(0, 0, math.pi / 4), mat="M_Brass_Aged", bevel=0.002, segments=1))
AP_H = 0.085
for name, size, loc in (
        ("t_apron_s", (ax1 - ax0 - 2 * LEG + 0.004, 0.018, AP_H), (TC.x, ay1 - 0.009, TH - 0.028 - AP_H / 2)),
        ("t_apron_n", (ax1 - ax0 - 2 * LEG + 0.004, 0.018, AP_H), (TC.x, ay0 + 0.009, TH - 0.028 - AP_H / 2)),
        ("t_apron_w", (0.018, ay1 - ay0 - 2 * LEG + 0.004, AP_H), (ax0 + 0.009, TC.y, TH - 0.028 - AP_H / 2)),
        ("t_apron_e", (0.018, ay1 - ay0 - 2 * LEG + 0.004, AP_H), (ax1 - 0.009, TC.y, TH - 0.028 - AP_H / 2))):
    table.append(M.box(name, size, loc=loc, bevel=0.002, segments=1))
# drawer front on the east apron (toward the doorway) with a turned brass knob
dr = P.raised_panel("t_drawer", 0.26, 0.058, 0.012, field_inset=0.012, raise_=0.003, loc=(0, 0, 0))
dr.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))        # front now faces +X
dr.location = (ax1 - 0.002, TC.y, TH - 0.028 - AP_H / 2)
table.append(dr)
table.append(P.lathe_axis("t_knob", [(0.0, 0.0), (0.006, 0.0), (0.0045, 0.008), (0.0095, 0.016), (0.0085, 0.022),
                                    (0.0, 0.023)], axis="X", segments=12, mat="M_Brass_Aged",
                          loc=(ax1 + 0.010, TC.y, TH - 0.028 - AP_H / 2)))
# lower shelf between the legs
table.append(M.box("t_shelf", (ax1 - ax0 - 0.01, ay1 - ay0 - 0.01, 0.016), loc=(TC.x, TC.y, 0.17), bevel=0.003, segments=1))
# a stack of spare gel frames and a coiled spare cable on the shelf
for i in range(2):
    gf = K.curve_solid(f"t_gel{i}", [K.rounded_rect(0.15, 0.15, 0.008, 2), K.circle(0.055, 16)], 0.0025, bevel=0.0,
                       mat="M_Steel_Dark")
    gf.location = (TC.x - 0.09 + 0.004 * i, TC.y + 0.04 - 0.003 * i, 0.178 + 0.0026 * i)
    gf.rotation_euler = (0, 0, 0.08 * i - 0.1)
    table.append(gf)
coil = M.torus("t_coil", 0.055, 0.009, loc=(TC.x + 0.13, TC.y - 0.03, 0.186), major_seg=16, minor_seg=5, mat="M_Fabric")
coil.scale = (1.0, 0.85, 0.7)
table.append(coil)
coil2 = M.torus("t_coil2", 0.048, 0.008, loc=(TC.x + 0.135, TC.y - 0.035, 0.2), rot=(0.06, 0.05, 0.4), major_seg=16,
                minor_seg=5, mat="M_Fabric")
coil2.scale = (1.0, 0.85, 0.7)
table.append(coil2)
# Leyla's folded note on the table top, front-left
note = M.box("t_note", (0.09, 0.13, 0.0006), loc=(TC.x - 0.16, TC.y - 0.12, TH + 0.0008), rot=(0, 0, -0.35), mat="M_Paper",
             bevel=0.0)
table.append(note)
shadow_table = (dbg(table, "shadow_table") or M.join(table, "shadow_table"))

# ================================================================ 2. theatre lantern (baby profile spot) on a yoke stand
# lantern-local frame: origin = tilt trunnion, +Y = beam, +Z = up; posed by R_PITCH about the trunnion.
D_TL = 0.200                                   # trunnion -> light_origin along the beam
T = L - BEAM * D_TL                            # trunnion (Blender)
body = []
house = [(0.0, -0.092), (0.028, -0.0905), (0.05, -0.087), (0.063, -0.082), (0.0695, -0.077), (0.0735, -0.072),
         (0.0735, -0.066), (0.0715, -0.0645), (0.0715, 0.034), (0.0745, 0.036), (0.0745, 0.045), (0.066, 0.047),
         (0.062, 0.050), (0.0525, 0.064), (0.0, 0.066)]
body.append(P.lathe_axis("l_house", house, axis="Y", segments=24, mat="M_Steel_Dark"))
# rear cap rib ring + centre lamp-adjust knob (bakelite) + cable gland
body.append(P.lathe_axis("l_rear_knob", [(0.0, -0.104), (0.009, -0.104), (0.0115, -0.101), (0.0115, -0.094), (0.006, -0.092),
                                         (0.0, -0.091)], axis="Y", segments=14, mat="M_Bakelite"))
gland = P.lathe_axis("l_gland", [(0.0, 0.0), (0.0065, 0.0), (0.0065, 0.012), (0.005, 0.016), (0.005, 0.02), (0.0, 0.02)],
                     axis="Y", sign=-1, segments=10, mat="M_Brass_Aged")
gland.data.transform(Matrix.Rotation(math.radians(-35), 4, "X"))
gland.location = (0.0, -0.083, -0.036)
body.append(gland)
# gate: rounded-square shutter housing, four framing-shutter handles, iris lever
body.append(M.box("l_gate", (0.112, 0.026, 0.112), loc=(0, 0.077, 0), mat="M_Steel_Dark", bevel=0.012, segments=2))
for i, (ang, ext) in enumerate(((90, 0.026), (270, 0.018), (0, 0.022), (180, 0.03))):
    a = math.radians(ang)
    d = Vector((math.cos(a), 0, math.sin(a)))
    base = d * 0.054 + Vector((0, 0.072 + 0.006 * (i % 2), 0))
    blade = M.box(f"l_shutter{i}", (0.013, 0.0016, ext), loc=(0, 0, 0), mat="M_Steel_Dark", bevel=0.0005, segments=1)
    blade.data.transform(Matrix.Translation((0, 0, ext / 2)))
    blade.data.transform(Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
    blade.location = base
    body.append(blade)
    kn = M.sphere(f"l_shutter_knob{i}", 0.0062, loc=base + d * (ext + 0.004), segments=8, rings=5, mat="M_Bakelite",
                  scale=(1, 1, 1))
    body.append(kn)
iris = M.box("l_iris", (0.006, 0.004, 0.03), loc=(0.04, 0.083, 0.052), rot=(0, math.radians(-38), 0), mat="M_Brass_Aged",
             bevel=0.0012, segments=1)
body.append(iris)
body.append(M.sphere("l_iris_knob", 0.0055, loc=(0.0495, 0.083, 0.064), segments=8, rings=5, mat="M_Bakelite"))
# lens tube with front lip, focus knob on top
tube = [(0.0, 0.088), (0.0505, 0.088), (0.0505, 0.165), (0.0545, 0.167), (0.0545, 0.176), (0.0505, 0.178), (0.0458, 0.1775),
        (0.0452, 0.158), (0.0, 0.152)]
body.append(P.lathe_axis("l_tube", tube, axis="Y", segments=24, mat="M_Steel_Dark"))
tb = K.lathe2("l_tube_band", [(0.0505, 0.09), (0.0525, 0.091), (0.0525, 0.099), (0.0505, 0.1)], segments=24, mat="M_Brass_Aged",
              cap_bottom=False, cap_top=False)
tb.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
body.append(tb)
body.append(M.box("l_focus_slot", (0.012, 0.05, 0.004), loc=(0, 0.13, 0.0505), mat="M_Bakelite", bevel=0.0015, segments=1))
fk = M.lathe("l_focus_knob", [(0.0, 0.0), (0.0035, 0.0), (0.0035, 0.008), (0.0085, 0.009), (0.009, 0.015), (0.007, 0.018),
                               (0.0, 0.0185)], segments=12, mat="M_Bakelite")
fk.location = (0, 0.142, 0.052)
body.append(fk)
# gel-frame runners + an empty gel frame
for sx in (-1, 1):
    body.append(M.box(f"l_runner{sx}", (0.006, 0.014, 0.13), loc=(sx * 0.066, 0.183, 0), mat="M_Steel_Dark", bevel=0.0012,
                      segments=1))
    body.append(M.box(f"l_runner_arm{sx}", (0.016, 0.012, 0.012), loc=(sx * 0.058, 0.172, sx * 0.0 + 0.0), mat="M_Steel_Dark",
                      bevel=0.0012, segments=1))
gel = K.curve_solid("l_gel_frame", [K.rounded_rect(0.128, 0.128, 0.006, 2), K.circle(0.047, 24)], 0.0025, bevel=0.0,
                    mat="M_Steel_Dark")
gel.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
gel.location = (0, 0.1855, 0)
body.append(gel)
body.append(M.box("l_gel_tab", (0.03, 0.0025, 0.016), loc=(0, 0.1868, 0.072), mat="M_Steel_Dark", bevel=0.0008, segments=1))
# lens glass (plano-convex, M_Glass) seated inside the lip
body.append(P.lathe_axis("l_lens", [(0.0, 0.1585), (0.0448, 0.1585), (0.0448, 0.161), (0.032, 0.1655), (0.016, 0.1678),
                                    (0.0, 0.1684)], axis="Y", segments=24, mat="M_Glass"))
# ventilation chimney on the lamp house: louvred box + raised cap
body.append(M.box("l_chimney", (0.07, 0.10, 0.028), loc=(0, -0.022, 0.08), mat="M_Steel_Dark", bevel=0.004, segments=1))
body.append(M.box("l_chimney_cap", (0.084, 0.112, 0.006), loc=(0, -0.022, 0.1035), mat="M_Steel_Dark", bevel=0.0025, segments=2))
for j in range(4):
    for sx in (-1, 1):
        body.append(M.box(f"l_louvre{j}{sx}", (0.002, 0.016, 0.004), loc=(sx * 0.0355, -0.058 + 0.024 * j, 0.0835),
                          rot=(math.radians(25), 0, 0), mat="M_Bakelite", bevel=0.0, segments=1))
for sx in (-1, 1):
    for sy in (-1, 1):
        body.append(M.cylinder(f"l_cap_post{sx}{sy}", 0.0035, 0.006, loc=(sx * 0.03, -0.022 + sy * 0.04, 0.0975), verts=8,
                               mat="M_Steel_Dark", bevel=0.0))
# carrying handle on top of the house (behind the chimney)
hp = P.bezier((0.0, -0.08, 0.07), (0.0, -0.088, 0.112), (0.0, -0.084, 0.128), (0.0, -0.07, 0.128), 5)
hp += P.bezier((0.0, -0.07, 0.128), (0.0, -0.02, 0.128), (0.0, 0.02, 0.128), (0.0, 0.032, 0.128), 3)[1:]
hp += P.bezier((0.0, 0.032, 0.128), (0.0, 0.044, 0.128), (0.0, 0.047, 0.11), (0.0, 0.043, 0.074), 4)[1:]
body.append(P.tube("l_handle", hp, 0.0042, sides=8, mat="M_Steel_Dark"))
body.append(P.tube("l_handle_grip", [(0.0, -0.06, 0.1285), (0.0, 0.0, 0.1285)], 0.007, sides=8, mat="M_Bakelite"))
# trunnion bosses + enamel maker's plate on the side
for sx in (-1, 1):
    body.append(P.lathe_axis(f"l_boss{sx}", [(0.0, 0.0), (0.014, 0.0), (0.012, 0.012), (0.0, 0.0125)], axis="X", sign=sx,
                             segments=12, mat="M_Steel_Dark", loc=(sx * 0.066, 0.0, 0.0)))
plate = M.box("l_plate", (0.0016, 0.05, 0.028), loc=(-0.0727, -0.05, -0.02), mat="M_Enamel_Cream", bevel=0.0006, segments=1)
body.append(plate)
for dy in (-0.021, 0.021):
    body.append(M.cylinder(f"l_plate_rivet{dy}", 0.0022, 0.002, loc=(-0.0742, -0.05 + dy, -0.02), rot=(0, math.pi / 2, 0),
                           verts=6, mat="M_Brass_Aged", bevel=0.0))
spot_lamp = (dbg(body, "spot_lamp") or M.join(body, "spot_lamp"))
spot_lamp.location = T
spot_lamp.rotation_euler = (PITCH, 0, 0)

bulb = P.lathe_axis("spot_bulb", [(0.0, 0.1545), (0.0445, 0.1545), (0.0445, 0.1568), (0.0, 0.1578)], axis="Y", segments=24,
                    mat="M_Emissive_Warm")
bulb.location = T
bulb.rotation_euler = (PITCH, 0, 0)
M.refresh()
M.set_parent(bulb, spot_lamp)
light_origin = M.empty("light_origin", L, (PITCH, 0, 0))
M.set_parent(light_origin, spot_lamp)

# yoke + telescopic spigot + cast base (world-vertical, not pitched)
stand = []
YX = 0.086
for sx in (-1, 1):
    stand.append(M.box(f"y_arm{sx}", (0.006, 0.026, 0.1), loc=(T.x + sx * YX, T.y, T.z - 0.05), mat="M_Steel_Dark",
                       bevel=0.0018, segments=1))
    stand.append(M.cylinder(f"y_eye{sx}", 0.015, 0.0062, loc=(T.x + sx * YX, T.y, T.z), rot=(0, math.pi / 2, 0),
                            verts=12, mat="M_Steel_Dark", bevel=0.0015, segments=1))
stand.append(M.box("y_bottom", (2 * YX + 0.006, 0.026, 0.007), loc=(T.x, T.y, T.z - 0.1), mat="M_Steel_Dark", bevel=0.0018,
                   segments=1))
# tilt-lock: big bakelite wing knob on the right (+X), hex bolt on the left
wing = K.lathe2("y_lock", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.008), (0.019, 0.010, "k"), (0.019, 0.022, "k"), (0.015, 0.026),
                           (0.0, 0.027)], segments=16, mat="M_Bakelite", knurl=0.0025)
wing.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
wing.location = (T.x + YX + 0.003, T.y, T.z)
stand.append(wing)
hexb = M.cylinder("y_hex", 0.009, 0.007, loc=(T.x - YX - 0.0065, T.y, T.z), rot=(0, math.pi / 2, 0), verts=6,
                  mat="M_Steel_Dark", bevel=0.001, segments=1)
stand.append(hexb)
SP_TOP = T.z - 0.1035
BASE_TOP = TH + 0.034
stand.append(M.lathe("y_base", [(0.0, TH), (0.078, TH), (0.079, TH + 0.004), (0.074, TH + 0.012), (0.052, TH + 0.022),
                                (0.024, TH + 0.03), (0.017, BASE_TOP), (0.0, BASE_TOP)], loc=(T.x, T.y, 0), segments=20,
                     mat="M_Steel_Dark"))
stand.append(M.cylinder("y_spigot_lo", 0.013, 0.10, loc=(T.x, T.y, BASE_TOP + 0.05), verts=12, mat="M_Steel_Dark", bevel=0.0015,
                        segments=1))
stand.append(M.lathe("y_collar", [(0.0, 0.0), (0.019, 0.0), (0.02, 0.004), (0.02, 0.018), (0.017, 0.022), (0.0, 0.022)],
                     loc=(T.x, T.y, BASE_TOP + 0.096), segments=12, mat="M_Steel_Dark"))
stand.append(P.rod("y_tscrew", (T.x, T.y - 0.019, BASE_TOP + 0.107), (T.x, T.y - 0.038, BASE_TOP + 0.107), 0.0035, sides=8,
                   mat="M_Steel_Dark"))
stand.append(M.cylinder("y_tbar", 0.004, 0.04, loc=(T.x, T.y - 0.04, BASE_TOP + 0.107), rot=(0, math.pi / 2, 0), verts=8,
                        mat="M_Bakelite", bevel=0.0015))
stand.append(M.cylinder("y_spigot_hi", 0.0095, SP_TOP - (BASE_TOP + 0.118), loc=(T.x, T.y, (SP_TOP + BASE_TOP + 0.118) / 2),
                        verts=12, mat="M_Chrome", bevel=0.0012, segments=1))
stand.append(M.cylinder("y_spigot_cap", 0.016, 0.012, loc=(T.x, T.y, SP_TOP + 0.002), verts=12, mat="M_Steel_Dark", bevel=0.002,
                        segments=1))
# cloth cable: gland -> table top beside the base -> over the south (back) edge -> floor -> wall socket
M.refresh()
g_end = spot_lamp.matrix_world @ Vector((0.0, -0.083 - 0.02 * math.cos(math.radians(35)), -0.036 - 0.02 * math.sin(math.radians(35))))
SOCKET = G(-3.90, 0.15, 0.40)                    # bakelite wall socket on the south wall, low
back_y = TC.y - TD / 2                           # table edge toward the south wall
on_top = Vector((T.x + 0.085, T.y - 0.07, TH + 0.0045))
over = Vector((T.x + 0.105, back_y - 0.004, TH - 0.004))
floor_pt = Vector((T.x + 0.11, back_y - 0.011, 0.0045))
plug_in = SOCKET + Vector((0.0, 0.043, -0.032))
cable = P.bezier(g_end, g_end + Vector((0.01, -0.012, -0.05)), on_top + Vector((-0.03, 0.03, 0.0)), on_top, 6)
cable += P.bezier(on_top, on_top + Vector((0.02, -0.03, 0.0)), over + Vector((0.0, 0.006, 0.006)), over, 4)[1:]
cable += P.bezier(over, over + Vector((0.002, -0.006, -0.02)), floor_pt + Vector((0.0, 0.0, 0.25)), floor_pt, 6)[1:]
cable += P.bezier(floor_pt, floor_pt + Vector((0.0, 0.0, -0.004)) + Vector((0.06, 0.0, 0.0)),
                  plug_in + Vector((-0.03, 0.0, -0.09)), plug_in, 5)[1:]
stand.append(P.tube("y_cable", cable, 0.0042, sides=7, mat="M_Fabric"))
stand.append(M.box("y_wall_socket", (0.075, 0.026, 0.075), loc=SOCKET + Vector((0, 0.013, 0)), mat="M_Bakelite",
                   bevel=0.006, segments=2))
for dx in (-0.012, 0.012):
    stand.append(M.cylinder(f"y_socket_pin{dx}", 0.0026, 0.004, loc=SOCKET + Vector((dx, 0.027, 0.018)), rot=(math.pi / 2, 0, 0),
                            verts=6, mat="M_Brass_Aged", bevel=0.0))
stand.append(M.box("y_plug", (0.032, 0.026, 0.04), loc=SOCKET + Vector((0, 0.039, -0.008)), mat="M_Bakelite", bevel=0.005,
                   segments=2))
spot_stand = (dbg(stand, "spot_stand") or M.join(stand, "spot_stand"))

# ================================================================ 3. brass gimbal sculpture on its instrument stand
B0 = G(-4.0, 0.0, -0.60)                       # floor point under the gimbal
HEAD_Z = 0.955
st = []
st.append(M.lathe("s_hub", [(0.0, 0.03), (0.038, 0.03), (0.04, 0.036), (0.034, 0.05), (0.026, 0.07), (0.022, 0.1),
                            (0.02, 0.112), (0.0, 0.112)], loc=B0, segments=16, mat="M_Steel_Dark"))
for i in range(3):
    a = math.radians(90 + 120 * i)
    d = Vector((math.cos(a), math.sin(a), 0))
    p0 = B0 + d * 0.025 + Vector((0, 0, 0.078))
    p3 = B0 + d * 0.205 + Vector((0, 0, 0.016))
    pts = P.bezier(p0, p0 + d * 0.06 + Vector((0, 0, 0.004)), p3 - d * 0.08 + Vector((0, 0, 0.03)), p3, 6)
    st.append(P.tube(f"s_leg{i}", pts, 0.012, sides=8, mat="M_Steel_Dark",
                     radii=[0.016 - 0.008 * (j / (len(pts) - 1)) for j in range(len(pts))]))
    st.append(M.lathe(f"s_foot{i}", [(0.0, 0.0), (0.017, 0.0), (0.018, 0.004), (0.012, 0.011), (0.007, 0.02), (0.0, 0.02)],
                      loc=(p3.x, p3.y, 0.0), segments=10, mat="M_Brass_Aged"))
st.append(M.lathe("s_column", [(0.0, 0.11), (0.0145, 0.11), (0.0145, 0.556), (0.0, 0.556)], loc=(B0.x, B0.y, 0), segments=16,
                  mat="M_Steel_Dark"))
st.append(K.lathe2("s_column_collar", [(0.0, 0.554), (0.0185, 0.554), (0.021, 0.557), (0.021, 0.559, "k"), (0.021, 0.581, "k"),
                                       (0.0185, 0.584), (0.0, 0.584)], segments=24, mat="M_Brass_Aged", knurl=0.0012,
                   loc=(B0.x, B0.y, 0)))
st.append(M.lathe("s_column_hi", [(0.0, 0.584), (0.0118, 0.584), (0.0118, 0.594), (0.0112, 0.6), (0.0112, HEAD_Z), (0.0, HEAD_Z)],
                  loc=(B0.x, B0.y, 0), segments=16, mat="M_Brass_Aged"))
head = [(0.0, HEAD_Z), (0.016, HEAD_Z), (0.031, HEAD_Z + 0.006), (0.036, HEAD_Z + 0.013), (0.036, HEAD_Z + 0.05),
        (0.0335, HEAD_Z + 0.056), (0.022, HEAD_Z + 0.06), (0.0, HEAD_Z + 0.06)]
st.append(M.lathe("s_head", head, loc=(B0.x, B0.y, 0), segments=24, mat="M_Brass_Aged"))
st.append(K.lathe2("s_head_band", [(0.036, 0.018), (0.0372, 0.019), (0.0372, 0.026), (0.036, 0.027)], segments=24,
                   mat="M_Brass_Polished", cap_bottom=False, cap_top=False, loc=(B0.x, B0.y, HEAD_Z)))
ROD_KNOB_Z = HEAD_Z + 0.032
st.append(P.lathe_axis("s_rod_boss", [(0.0, 0.0), (0.0125, 0.0), (0.0125, 0.012), (0.011, 0.014), (0.0, 0.014)], axis="Y",
                       sign=-1, segments=12, mat="M_Brass_Aged", loc=(B0.x, B0.y - 0.031, ROD_KNOB_Z)))
# engraved arrow plates (enamel) showing each knob's sense of rotation
st.append(M.box("s_plate", (0.034, 0.0012, 0.009), loc=(B0.x, B0.y - 0.0362, HEAD_Z + 0.008), mat="M_Enamel_Cream",
                bevel=0.0004, segments=1))
STEM_TOP = S.z - RING_R - 0.006 - 0.0115
st.append(M.lathe("s_stem", [(0.0, HEAD_Z + 0.08), (0.0045, HEAD_Z + 0.08), (0.0042, STEM_TOP - 0.012), (0.0075, STEM_TOP - 0.009),
                             (0.0082, STEM_TOP - 0.002), (0.0068, STEM_TOP), (0.0, STEM_TOP)], loc=(B0.x, B0.y, 0), segments=14,
                  mat="M_Brass_Polished"))
sculpture_stand = (dbg(st, "sculpture_stand") or M.join(st, "sculpture_stand"))

ring_knob = K.lathe2("IA_ring_knob", [(0.0, 0.0), (0.03, 0.002), (0.041, 0.005), (0.042, 0.007, "k"), (0.042, 0.019, "k"),
                                      (0.039, 0.022), (0.012, 0.024), (0.009, 0.034), (0.0, 0.036)], segments=32,
                     mat="M_Brass_Polished", knurl=0.0018)
ring_knob.location = (B0.x, B0.y, HEAD_Z + 0.06)
# index notch + enamel pip on the wheel rim (rotates with it)
pip = M.box("IA_ring_knob_pip", (0.006, 0.006, 0.0012), loc=(B0.x, B0.y - 0.034, HEAD_Z + 0.06 + 0.0225), mat="M_Enamel_Cream",
            bevel=0.0, segments=1)
ring_knob = M.join([ring_knob, pip], "IA_ring_knob")
M.set_origin(ring_knob, (B0.x, B0.y, HEAD_Z + 0.06 + 0.012))

rod_knob = K.knurled_knob("IA_rod_knob", 0.019, 0.022, ridges=14, mat="M_Brass_Polished", skirt=0.003, dome=0.003,
                          cap_mat="M_Bakelite")
rod_knob.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))      # knob axis +Z -> -Y (Godot +Z, toward the lamp)
rod_knob.location = (B0.x, B0.y - 0.045, ROD_KNOB_Z)
M.refresh()
M.set_origin(rod_knob, (B0.x, B0.y - 0.045 - 0.012, ROD_KNOB_Z))

# ---- the ring (aligned pose in mesh: plane = Godot XY, normal = Godot Z); object yaw = REST
ring_parts = [K.ring_band("ring_band", RING_R - 0.006, RING_R + 0.006, 0.0084, segments=56, mat="M_Brass_Polished",
                          chamfer=0.0009)]
for i in range(12):                              # degree pips on the front face (inside the band outline)
    a = math.radians(30 * i)
    ring_parts.append(M.box(f"ring_pip{i}", (0.005 if i % 3 else 0.008, 0.0016, 0.0008), loc=(RING_R * math.cos(a), RING_R * math.sin(a), 0.0046),
                            rot=(0, 0, a), mat="M_Enamel_Cream", bevel=0.0, segments=1))
ring = M.join(ring_parts, "sculpture_ring")
ring.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))       # axis Z -> -Y: front face toward the lamp
knuckle = M.lathe("ring_knuckle", [(0.0, -RING_R - 0.0175), (0.0058, -RING_R - 0.0175), (0.0062, -RING_R - 0.014),
                                   (0.0052, -RING_R - 0.006), (0.0052, -RING_R + 0.002), (0.0, -RING_R + 0.002)],
                  loc=(0, 0.0032, 0), segments=12, mat="M_Brass_Polished")
ring = M.join([ring, knuckle], "sculpture_ring")
ring.location = S
ring.rotation_euler = (0, 0, REST_YAW)

# ---- the rod: built vertical about its own centre; rides on the ring band on two shoes
rp = []
rp.append(M.cylinder("rod_shaft", 0.0032, ROD_LEN - 0.02, loc=(0, 0, 0), verts=12, mat="M_Brass_Polished", bevel=0.0))
fin = [(0.0, 0.0), (0.0034, 0.0), (0.0056, 0.003), (0.0062, 0.0058), (0.0052, 0.0082), (0.0028, 0.0096), (0.0, 0.01)]
for sz in (1, -1):
    f = M.lathe(f"rod_fin{sz}", fin, segments=10, mat="M_Brass_Polished")
    if sz < 0:
        f.data.transform(Matrix.Rotation(math.pi, 4, "X"))
    f.location = (0, 0, sz * (ROD_LEN / 2 - 0.01))
    rp.append(f)
    zc = sz * RING_R
    rp.append(M.cylinder(f"rod_sleeve{sz}", 0.0052, 0.016, loc=(0, 0, zc), verts=10, mat="M_Brass_Aged", bevel=0.0012, segments=1))
    rp.append(M.box(f"rod_shoe{sz}", (0.017, 0.0042, 0.015), loc=(0, ROD_DZ - 0.0042 - 0.0021 + 0.0002, zc), mat="M_Brass_Aged",
                    bevel=0.0012, segments=1))
    for side in (-1, 1):   # lips that wrap the band's inner and outer edges
        rp.append(M.box(f"rod_lip{sz}{side}", (0.017, 0.0094, 0.0018), loc=(0, ROD_DZ - 0.0042 + 0.0047 - 0.0002, zc + side * 0.0071),
                        mat="M_Brass_Aged", bevel=0.0005, segments=1))
rp.append(P.lathe_axis("rod_hub", [(0.0, -0.0035), (0.0075, -0.0035), (0.0088, -0.0015), (0.0088, 0.0015), (0.0075, 0.0035),
                                   (0.0, 0.0035)], axis="Y", segments=16, mat="M_Brass_Aged"))
rp.append(P.lathe_axis("rod_hub_pip", [(0.0, 0.0), (0.0035, 0.0), (0.0, 0.0022)], axis="Y", sign=-1, segments=10,
                       mat="M_Enamel_Cream", loc=(0, -0.0035, 0)))
rod = (dbg(rp, "sculpture_rod") or M.join(rp, "sculpture_rod"))
# place: ring-local offset (0, -ROD_DZ, 0) (toward the lamp), rest tilt +60 deg about Godot +Z (= Blender -Y)
M.refresh()
rod_local = Matrix.Translation((0, -ROD_DZ, 0)) @ Matrix.Rotation(-REST_TILT, 4, "Y")
rod.matrix_world = ring.matrix_world @ rod_local
M.refresh()
M.set_parent(rod, ring)

# ================================================================ 4. emblem socket on the north wall + crystal disc
SOCK = G(-4.0, 1.5, -1.585)
WALL_Y = -WALL_Z                                 # Blender y of the wall surface (1.6)
sock_prof = [(0.0, 0.0), (0.045, 0.0), (0.045, 0.0035), (0.043, 0.0055), (0.0385, 0.0065), (0.0375, 0.008),
             (0.0375, 0.022), (0.0405, 0.0245), (0.0405, 0.0285), (0.0388, 0.0302), (0.0372, 0.0302), (0.0362, 0.0285),
             (0.0362, 0.0125), (0.033, 0.0105), (0.0, 0.0105)]
bands = [None] * (len(sock_prof) - 1)
bands[-1] = "M_Steel_Dark"
bands[-2] = "M_Steel_Dark"
bands[-3] = "M_Steel_Dark"
socket = K.lathe2("IA_emblem_socket", sock_prof, segments=28, mat="M_Brass_Aged", band_mats=bands)
knurl_ring = K.lathe2("sock_knurl", [(0.0376, 0.011, "k"), (0.0376, 0.019, "k")], segments=56, mat="M_Brass_Polished",
                      knurl=0.0009, cap_bottom=False, cap_top=False)
socket = M.join([socket, knurl_ring] + [K.screw(f"sock_screw{i}", 0.0032, (0.0412 * math.cos(a), 0.0412 * math.sin(a), 0.0038),
                                                (0, 0, 1), "M_Brass_Aged", slot_angle=a + 0.4)
                                        for i, a in enumerate((math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4))],
                "IA_emblem_socket")
socket.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))     # axis Z -> -Y (protrudes into the room)
socket.location = (SOCK.x, WALL_Y, SOCK.z)
M.refresh()
M.set_origin(socket, SOCK)
lens = P.lathe_axis("socket_lens", [(0.0, 0.0108), (0.02, 0.0115), (0.0328, 0.0128), (0.0352, 0.0152), (0.0352, 0.0192),
                                    (0.0328, 0.0218), (0.02, 0.0236), (0.0, 0.0244)], axis="Y", sign=-1, segments=24,
                    mat="M_Crystal", loc=(SOCK.x, WALL_Y, SOCK.z))
M.refresh()
M.set_origin(lens, (SOCK.x, WALL_Y - 0.0176, SOCK.z))
M.set_parent(lens, socket)

# painted emblem, scaled to the aligned shadow (circle centre-line r = 155.5 px of 512 in wall_emblem.png)
EMB_PX_R = 155.5
emb_size = 512.0 * (RING_R * MAG) / EMB_PX_R
P.alpha_decal_material("M_Decal_Emblem", os.path.join(P.DECALS, "wall_emblem.png"), color="E8DFC8", rough=0.95)
emb = P.mesh_obj("emblem_paint", [(-emb_size / 2, 0, -emb_size / 2), (emb_size / 2, 0, -emb_size / 2),
                                  (emb_size / 2, 0, emb_size / 2), (-emb_size / 2, 0, emb_size / 2)],
                 [(0, 1, 2, 3)], ["M_Decal_Emblem"])
P.fix_normals(emb)
if emb.data.polygons[0].normal.y > 0:
    emb.data.flip_normals()
emb.location = (C.x, WALL_Y - 0.0012, C.z)
M.planar_uv(emb, axis="Y")

# ================================================================ 5. wall cabinet on the north wall (Godot (-4.0, 0.55, -1.58))
CW, CH, CD = 0.36, 0.40, 0.18
CZ = 0.55
CX = -4.0
FRONT_Y = WALL_Y - CD                            # carcass front plane (Blender y 1.42)
cab = []
cab.append(M.box("c_back", (CW, 0.012, CH), loc=(CX, WALL_Y - 0.006, CZ), bevel=0.002, segments=1))
for sx in (-1, 1):
    cab.append(M.box(f"c_side{sx}", (0.018, CD - 0.012, CH), loc=(CX + sx * (CW / 2 - 0.009), (WALL_Y - 0.012 + FRONT_Y) / 2, CZ),
                     bevel=0.002, segments=1))
for sz, nm in ((1, "c_top"), (-1, "c_bottom")):
    cab.append(M.box(nm, (CW - 0.036, CD - 0.012, 0.018), loc=(CX, (WALL_Y - 0.012 + FRONT_Y) / 2, CZ + sz * (CH / 2 - 0.009)),
                     bevel=0.002, segments=1))
cab.append(M.box("c_felt", (CW - 0.04, 0.002, CH - 0.04), loc=(CX, WALL_Y - 0.0125, CZ), mat="M_Felt", bevel=0.0))
cab.append(M.box("c_felt_floor", (CW - 0.04, CD - 0.03, 0.002), loc=(CX, (WALL_Y + FRONT_Y) / 2 - 0.004, CZ - CH / 2 + 0.019),
                 mat="M_Felt", bevel=0.0))
# cornice + base mouldings (front and sides, mitred look from P.moulding returns)
crown = [(0.0, 0.0), (-0.004, 0.0), (-0.006, 0.003)] + P.ogee(-0.006, 0.004, -0.016, 0.016, n=4) + [(-0.018, 0.017),
                                                                                                    (-0.018, 0.024), (0.0, 0.024)]
cab.append(P.moulding("c_crown_f", crown, CW, loc=(CX, FRONT_Y, CZ + CH / 2), miter_left=True, miter_right=True))
for sx in (-1, 1):
    side = P.moulding(f"c_crown_s{sx}", crown, CD, miter_left=(sx > 0), miter_right=(sx < 0))
    side.rotation_euler = (0, 0, sx * math.pi / 2)
    side.location = (CX + sx * CW / 2, (WALL_Y + FRONT_Y) / 2, CZ + CH / 2)
    cab.append(side)
base = [(0.0, 0.0), (-0.012, 0.0), (-0.012, 0.006)] + P.ogee(-0.012, 0.007, -0.002, 0.016, n=4) + [(0.0, 0.016)]
base = [(y, -z) for (y, z) in base]
cab.append(P.moulding("c_base_f", base, CW, loc=(CX, FRONT_Y, CZ - CH / 2), miter_left=True, miter_right=True))
for sx in (-1, 1):
    side = P.moulding(f"c_base_s{sx}", base, CD, miter_left=(sx > 0), miter_right=(sx < 0))
    side.rotation_euler = (0, 0, sx * math.pi / 2)
    side.location = (CX + sx * CW / 2, (WALL_Y + FRONT_Y) / 2, CZ - CH / 2)
    cab.append(side)
# barrel hinges on the left edge (hinge axis = door pivot)
HINGE = Vector((CX - CW / 2 + 0.002, FRONT_Y - 0.021, CZ))
for dz in (-0.12, 0.12):
    cab.append(M.cylinder(f"c_hinge{dz}", 0.0045, 0.05, loc=(HINGE.x, HINGE.y, CZ + dz), verts=10, mat="M_Brass_Aged", bevel=0.0012,
                          segments=1))
    cab.append(M.sphere(f"c_hinge_tip{dz}", 0.0042, loc=(HINGE.x, HINGE.y, CZ + dz + 0.027), segments=8, rings=4, mat="M_Brass_Aged"))
shadow_cabinet = (dbg(cab, "shadow_cabinet") or M.join(cab, "shadow_cabinet"))
M.set_origin(shadow_cabinet, G(-4.0, 0.55, -1.58))

door = [P.raised_panel("d_panel", CW - 0.004, CH - 0.004, 0.02, field_inset=0.04, raise_=0.005, loc=(CX, FRONT_Y, CZ))]
# Institute mark inlaid in brass on the field
mark = K.lathe2("d_mark_ring", [(0.034, -0.0015), (0.034, 0.0012), (0.0355, 0.0015), (0.0375, 0.0015), (0.039, 0.0012),
                                 (0.039, -0.0015)], segments=28, mat="M_Brass_Aged", cap_bottom=False, cap_top=False)
mark.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
mark.location = (CX, FRONT_Y - 0.0255, CZ + 0.02)
door.append(mark)
door.append(M.box("d_mark_bar", (0.005, 0.003, 0.108), loc=(CX, FRONT_Y - 0.0255, CZ + 0.02), mat="M_Brass_Aged", bevel=0.0007,
                  segments=1))
door.append(P.lathe_axis("d_knob", [(0.0, 0.0), (0.0105, 0.0), (0.009, 0.004), (0.0045, 0.009), (0.0045, 0.014), (0.011, 0.02),
                                    (0.012, 0.025), (0.0095, 0.031), (0.0, 0.0325)], axis="Y", sign=-1, segments=12,
                         mat="M_Brass_Aged", loc=(CX + CW / 2 - 0.04, FRONT_Y - 0.02, CZ)))
door.append(M.box("d_escutcheon", (0.016, 0.003, 0.03), loc=(CX + CW / 2 - 0.04, FRONT_Y - 0.0205, CZ - 0.045), mat="M_Brass_Aged",
                  bevel=0.0012, segments=1))
door.append(M.box("d_keyhole", (0.003, 0.0012, 0.009), loc=(CX + CW / 2 - 0.04, FRONT_Y - 0.0222, CZ - 0.043), mat="M_Bakelite",
                  bevel=0.0, segments=1))
door.append(M.cylinder("d_keyhole_o", 0.0028, 0.0012, loc=(CX + CW / 2 - 0.04, FRONT_Y - 0.0222, CZ - 0.0385),
                       rot=(math.pi / 2, 0, 0), verts=8, mat="M_Bakelite", bevel=0.0))
cab_door = (dbg(door, "IA_cabinet_door") or M.join(door, "IA_cabinet_door"))
M.set_origin(cab_door, HINGE)
item_spot = M.empty("cabinet_item_spot", G(-4.0, 0.55, -1.50))

# ================================================================ 6. darkroom safelight (south wall, west, above the trays)
SL = G(-4.55, 2.05, 0.40)                        # wall point (Blender y = -0.40 is the south wall surface)
SL_TILT = math.radians(28)                       # aims down toward the trays / room
R_SL = Matrix.Rotation(-SL_TILT, 4, "X")
SL_C = Vector((SL.x, SL.y + 0.15, SL.z - 0.02))  # housing centre
FORK = SL_C + (R_SL @ Vector((0.0, -0.012, 0.0675)))   # top of the fork: the wall arm ends here
sl = []
sl.append(M.box("sl_wallplate", (0.07, 0.008, 0.11), loc=(SL.x, SL.y + 0.004, FORK.z), mat="M_Steel_Painted", bevel=0.003,
                segments=2))
for dz in (-0.04, 0.04):
    sl.append(K.screw(f"sl_screw{dz}", 0.004, (SL.x, SL.y + 0.008, FORK.z + dz), (0, 1, 0), "M_Steel_Dark"))
sl.append(P.rod("sl_arm", (SL.x, SL.y + 0.008, FORK.z), (SL.x, FORK.y + 0.006, FORK.z), 0.0065, sides=10, mat="M_Steel_Dark"))
sl.append(M.cylinder("sl_arm_nut", 0.011, 0.012, loc=(SL.x, SL.y + 0.014, FORK.z), rot=(math.pi / 2, 0, 0), verts=6,
                     mat="M_Steel_Dark", bevel=0.0012, segments=1))
# lamp housing in its own frame: +Y = light direction, tilted down about X
hz = []
hz.append(M.box("sl_body", (0.2, 0.085, 0.15), loc=(0, 0.0, 0), mat="M_Steel_Painted", bevel=0.012, segments=2))
bez = K.curve_solid("sl_bezel", [K.rounded_rect(0.192, 0.142, 0.012, 3), K.rounded_rect(0.164, 0.114, 0.006, 2)], 0.012,
                    bevel=0.0012, mat="M_Steel_Dark")
bez.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
bez.location = (0, 0.039, 0)
hz.append(bez)
for j in range(5):
    hz.append(M.box(f"sl_vent{j}", (0.12, 0.006, 0.004), loc=(0, -0.0435, 0.035 - j * 0.014), mat="M_Bakelite", bevel=0.0,
                    segments=1))
hz.append(M.box("sl_hood", (0.21, 0.05, 0.006), loc=(0, 0.06, 0.077), rot=(math.radians(-8), 0, 0), mat="M_Steel_Painted",
                bevel=0.002, segments=1))
for sx in (-1, 1):
    hz.append(P.lathe_axis(f"sl_pivot{sx}", [(0.0, 0.0), (0.011, 0.0), (0.011, 0.006), (0.008, 0.009), (0.0, 0.0095)], axis="X",
                           sign=sx, segments=10, mat="M_Steel_Dark", loc=(sx * 0.1, 0.0, 0.0)))
    hz.append(M.box(f"sl_fork{sx}", (0.005, 0.02, 0.07), loc=(sx * 0.112, -0.012, 0.03), mat="M_Steel_Dark", bevel=0.0015, segments=1))
hz.append(M.box("sl_fork_top", (0.229, 0.02, 0.005), loc=(0, -0.012, 0.065), mat="M_Steel_Dark", bevel=0.0015, segments=1))
hz.append(M.box("sl_label", (0.07, 0.0012, 0.018), loc=(0, -0.0432, -0.05), mat="M_Enamel_Cream", bevel=0.0004, segments=1))
housing = (dbg(hz, "sl_housing") or M.join(hz, "sl_housing"))
housing.location = SL_C
housing.rotation_euler = (-SL_TILT, 0, 0)
sl.append(housing)
# cable from the housing top up the wall to a junction box under the ceiling
M.refresh()
c0 = housing.matrix_world @ Vector((0.075, -0.03, 0.075))
sl.append(P.tube("sl_cable", P.bezier(c0, c0 + Vector((0.0, -0.02, 0.06)), Vector((SL.x + 0.075, SL.y + 0.02, 2.42)),
                                      Vector((SL.x + 0.075, SL.y + 0.014, 2.52)), 7), 0.0035, sides=7, mat="M_Fabric"))
sl.append(M.box("sl_jbox", (0.07, 0.03, 0.07), loc=(SL.x + 0.075, SL.y + 0.015, 2.55), mat="M_Bakelite", bevel=0.006, segments=2))
safelight_housing = M.join(sl, "safelight_housing")
filt = M.box("safelight", (0.168, 0.004, 0.118), loc=(0, 0.044, 0), mat="M_Emissive_Red", bevel=0.0015, segments=1)
filt.location = SL_C
filt.rotation_euler = (-SL_TILT, 0, 0)
M.refresh()
M.set_origin(filt, filt.matrix_world @ Vector((0, 0.044, 0)))
SL_DIR = R_SL @ Vector((0, 1, 0))
sl_origin = M.empty("safelight_origin", filt.matrix_world.translation + SL_DIR * 0.05, (-SL_TILT, 0, 0))
M.set_parent(sl_origin, filt)

# ================================================================ finalize + export
M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)


# ================================================================ QA renders (after export: nothing below is exported)
def qa_darkroom():
    """Plaster shell of the darkroom (walls with the bookcase doorway, floor, ceiling) for context."""
    P.qa_box("qa_floor", (1.6, 2.0, 0.02), G(-4.0, -0.01, -0.6), colour="3A2A1E", rough=0.7)
    P.qa_box("qa_north", (1.6, 0.04, 2.6), (-4.0, WALL_Y + 0.02, 1.3), colour="A8A190")
    P.qa_box("qa_west", (0.04, 2.0, 2.6), (-4.82, 0.6, 1.3), colour="A39C8B")
    P.qa_box("qa_south", (1.6, 0.04, 2.6), (-4.0, -0.42, 1.3), colour="A39C8B")
    P.qa_box("qa_ceiling", (1.6, 2.0, 0.04), (-4.0, 0.6, 2.62), colour="8E887A")
    P.qa_box("qa_east_s", (0.04, 0.45, 2.6), (-3.18, -0.175, 1.3), colour="A39C8B")
    P.qa_box("qa_east_n", (0.04, 0.45, 2.6), (-3.18, 1.375, 1.3), colour="A39C8B")
    P.qa_box("qa_east_top", (0.04, 1.1, 0.45), (-3.18, 0.6, 2.375), colour="A39C8B")


def set_pose(yaw_deg, tilt_deg, door_deg=0.0):
    ring.rotation_euler = (0, 0, math.radians(yaw_deg))
    rod.matrix_basis = Matrix.Translation((0, -ROD_DZ, 0)) @ Matrix.Rotation(-math.radians(tilt_deg), 4, "Y")
    cab_door.rotation_euler = (0, 0, math.radians(door_deg))
    M.refresh()


def want(tag):
    if "--shots" not in ARGS:
        return True
    return tag in ARGS[ARGS.index("--shots") + 1].split(",")


if "--no-render" not in ARGS:
    P.preview_tweak()
    P.render_threads(2)
    bpy.context.scene.cycles.max_bounces = 6
    qa_darkroom()
    # pure point source at light_origin, cone like the in-game SpotLight3D (half-angle 14 deg)
    spot = P.qa_light("qa_shadow_spot", "SPOT", L, 60.0, colour="FFF1D6", radius=0.004, direction=BEAM,
                      half_angle_deg=14.0, blend=0.35)
    red = P.qa_light("qa_red", "SPOT", sl_origin.matrix_world.translation, 25.0, colour="FF2A1A", radius=0.06,
                     direction=SL_DIR, half_angle_deg=60.0, blend=0.8)
    bulb_l = P.qa_light("qa_bulb", "POINT", G(-4.0, 2.45, -0.6), 6.0, colour="FFD6A0", radius=0.03)
    no_studio = [((0.0, 0.0, 1.0), 0.5, "FFFFFF", 1.0)]
    GD_FOV56 = 22.5          # Blender lens matching Godot fov 56 (vertical) at 3:2
    if want("1"):            # the player's "shadow" view (lab7_room.gd), rest state
        M.render_preview(NAME, G(-3.45, 1.6, 0.32), G(-4.0, 1.38, -1.45), lens=GD_FOV56, res=(960, 640), samples=32,
                         world_strength=0.25, lights=no_studio)
    red.data.energy = 0.0
    bulb_l.data.energy = 0.0
    if want("2"):            # aligned from behind the lamp: full ring + meridian around the socket
        set_pose(0.0, 0.0)
        M.render_preview(NAME + "_2", G(-3.86, 1.42, 0.36), G(-4.0, 1.42, -1.6), lens=30, res=(960, 640), samples=32,
                         world_strength=0.05, lights=no_studio)
    if want("3"):            # rest state, same camera: ellipse + tilted bar
        set_pose(60.0, 60.0)
        M.render_preview(NAME + "_3", G(-3.86, 1.42, 0.36), G(-4.0, 1.42, -1.6), lens=30, res=(960, 640), samples=32,
                         world_strength=0.05, lights=no_studio)
    studio = [((1.0, 0.3, 0.8), 200, "FFE2C0", 1.0), ((-0.6, -0.4, 0.5), 60, "BFD4FF", 1.5)]
    if want("4"):            # sculpture + cabinet open
        set_pose(60.0, 60.0, -100.0)
        spot.data.energy = 25.0
        M.render_preview(NAME + "_4", G(-3.40, 1.30, -0.05), G(-4.0, 0.95, -0.95), lens=28, res=(960, 640), samples=32,
                         world_strength=0.3, lights=studio)
    set_pose(60.0, 60.0, 0.0)
    if want("5"):            # darkroom main view (lab7_room.gd "darkroom"), safelight on
        red.data.energy = 25.0
        bulb_l.data.energy = 4.0
        spot.data.energy = 60.0
        M.render_preview(NAME + "_5", G(-3.3, 1.5, -0.55), G(-4.8, 1.35, -0.75), lens=19.5, res=(960, 640), samples=32,
                         world_strength=0.2, lights=no_studio)
    if want("6"):            # lantern close-up
        spot.data.energy = 0.0
        red.data.energy = 0.0
        M.render_preview(NAME + "_6", G(-3.62, 1.22, -0.2), G(-4.0, 0.98, 0.24), lens=40, res=(960, 640), samples=32,
                         world_strength=0.3, lights=studio)
