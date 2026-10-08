"""chalkboard.glb — Strand's slate chalkboard in a moulded walnut frame, with chalk tray, chalk and a felt eraser.

Model space (Blender, Z up): back plane at Y = 0, front toward -Y (Godot +Z).
Origin = back plane, horizontal centre, at the BOTTOM edge of the slate: the slate spans
x in [-0.80, 0.80], z in [0.00, 1.00]; frame 1.73 x 1.13; tray below the slate (z ~ -0.03).
Place at Godot (-3.0, 1.0, 1.05), rotation_degrees.y = 90 (front faces +X): slate y in [1.0, 2.0].
`chalk_slate` front face: M_Decal_Chalkboard, planar 0..1 UV (u -> +X seen from the front, v -> up),
aspect 1.6 : 1.0 = 1024 : 640, not mirrored. Static; no IA parts.

Run: blender -b --factory-startup -P tools/blender/models/chalkboard.py [-- --no-render]
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

NAME = "chalkboard"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
M.material("M_Chalk", color="ECE6D6", rough=1.0)
rnd = random.Random(41)

SW, SH = 1.60, 1.00            # visible slate (decal) size
FW = 0.065                     # frame moulding width
SLATE_FRONT = 0.022            # slate front face depth (toward -Y)

# ---------------------------------------------------------------- slate (decal on the front face only)
slate = M.box("chalk_slate", (SW, 0.014, SH), loc=(0, -SLATE_FRONT + 0.007, SH / 2), mat="M_Chalkboard", bevel=0.0)
idx = M.add_slot(slate, "M_Decal_Chalkboard")
for p in slate.data.polygons:
    if p.normal.y < -0.9:
        p.material_index = idx
M.planar_uv(slate, axis="Y", material_prefix="M_Decal_")
backing = M.box("backing", (SW + 0.04, 0.008, SH + 0.04), loc=(0, -0.004, SH / 2), mat="M_Wood_Panel", bevel=0.001, segments=1)

# ---------------------------------------------------------------- moulded walnut frame
prof = [(0.0, 0.0), (0.0, 0.026), (0.0035, 0.0312), (0.011, 0.0335)]
prof += P.ogee(0.014, 0.0335, 0.04, 0.0272, n=5)[1:]
prof += [(0.047, 0.027), (0.0505, 0.0302), (0.054, 0.0305), (0.0575, 0.0275), (0.0615, 0.0262), (FW, 0.0245), (FW, 0.0)]
frame = P.frame_sweep("frame", SW + 2 * FW, SH + 2 * FW, prof, loc=(0, 0, SH / 2))
# subtle corner blocks (rosette-free, just a bead) and two brass mirror plates fixing it to the wall
plates = []
for sx in (-1, 1):
    x = sx * (SW / 2 + FW - 0.12)
    pl = M.box(f"mirror_plate{sx}", (0.03, 0.0018, 0.05), loc=(x, -0.001, SH + FW + 0.012), mat="M_Brass_Aged", bevel=0.0007,
               segments=1)
    plates.append(pl)
    plates.append(M.cylinder(f"mirror_screw{sx}", 0.0045, 0.002, loc=(x, -0.0025, SH + FW + 0.022), rot=(math.pi / 2, 0, 0), verts=8,
                             mat="M_Brass_Aged", bevel=0.0))

# ---------------------------------------------------------------- chalk tray (ledge on the bottom rail) + brass brackets
TL = 1.46                      # tray length
TZ = -0.028                    # tray top surface
TY0, TY1 = -0.026, -0.098      # tray from the rail front to its lip
tray = []
tray.append(M.box("tray_board", (TL, TY0 - TY1, 0.014), loc=(0, (TY0 + TY1) / 2, TZ - 0.007), bevel=0.0025, segments=2))
tray.append(M.box("tray_lip", (TL, 0.009, 0.024), loc=(0, TY1 + 0.0045, TZ - 0.002), bevel=0.003, segments=2))
for sx in (-1, 1):
    tray.append(M.box(f"tray_end{sx}", (0.012, TY0 - TY1, 0.02), loc=(sx * (TL / 2 - 0.006), (TY0 + TY1) / 2, TZ + 0.003), bevel=0.003,
                      segments=2))
    br = M.extrude_profile(f"tray_bracket{sx}", [(0.0, 0.0), (0.0, -0.06), (0.012, -0.06)] +
                           [(0.012 + 0.058 * (1 - math.cos(a)), -0.06 + 0.058 * math.sin(a)) for a in (0.3, 0.7, 1.1, 1.5707)] +
                           [(0.07, 0.0)], 0.005, mat="M_Brass_Aged", bevel=0.0008)
    br.rotation_euler = (math.pi / 2, 0, -math.pi / 2)        # outline x -> -Y (depth), y -> Z, extrusion along X
    br.location = (sx * (TL / 2 - 0.15) - 0.0025, TY0 + 0.0, TZ - 0.014)
    tray.append(br)
tray_obj = M.join(tray, "chalk_tray")

# ---------------------------------------------------------------- chalk, crumbs, dust, felt eraser
items = []
CH_R = 0.0052
for i, (x, ln, rz) in enumerate(((-0.52, 0.082, 0.05), (-0.47, 0.046, -0.25), (0.08, 0.031, 1.2))):
    c = M.cylinder(f"chalk{i}", CH_R, ln, loc=(x, (TY0 + TY1) / 2 + 0.004 * i, TZ + CH_R), rot=(0, math.pi / 2, rz), verts=10,
                   mat="M_Chalk", bevel=0.0012, segments=1)
    items.append(c)
for i in range(7):
    items.append(M.sphere(f"crumb{i}", rnd.uniform(0.0015, 0.003), loc=(rnd.uniform(-0.6, 0.3), rnd.uniform(TY1 + 0.012, TY0 - 0.01),
                                                                     TZ + 0.001), segments=6, rings=3, mat="M_Chalk",
                          scale=(1.0, 0.8, 0.5)))
# dust smudges on the tray (flat irregular patches)
for i, (cx, w) in enumerate(((-0.35, 0.34), (0.32, 0.22))):
    n = 9
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((cx + math.cos(a) * w / 2 * rnd.uniform(0.75, 1.0), (TY0 + TY1) / 2 + math.sin(a) * 0.026 * rnd.uniform(0.7, 1.0),
                    TZ + 0.0004))
    d = P.mesh_obj(f"dust{i}", pts, [list(range(n))], ["M_Chalk"])
    P.fix_normals(d)
    if d.data.polygons[0].normal.z < 0:
        d.data.flip_normals()
    items.append(d)
# felt eraser: walnut back block + grey felt pad, lying felt-down, chalk-dusted
ER = Vector((0.36, (TY0 + TY1) / 2 - 0.002, TZ))
er = [M.box("eraser_block", (0.12, 0.048, 0.022), loc=ER + Vector((0, 0, 0.006 + 0.011)), mat="M_Wood_Panel", bevel=0.004, segments=2),
      M.box("eraser_felt", (0.118, 0.046, 0.007), loc=ER + Vector((0, 0, 0.0035)), mat="M_Felt", bevel=0.0015, segments=1),
      M.box("eraser_grip", (0.09, 0.03, 0.01), loc=ER + Vector((0, 0, 0.032)), mat="M_Wood_Panel", bevel=0.004, segments=2)]
eraser = M.join(er, "eraser")
M.set_origin(eraser, ER)
eraser.rotation_euler = (0, 0, 0.08)
items.append(eraser)
M.join(items + plates, "chalk_items")
M.join([frame, backing, tray_obj], "chalk_frame")

M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)

if "--no-render" not in ARGS:
    P.render_threads(2)
    P.qa_box("qa_wall", (2.6, 0.04, 2.2), (0, 0.02, 0.4), colour="B8B2A0")
    P.shots(NAME, [
        ("", (0.75, -2.6, 0.75), (0.0, 0.0, 0.48), 35),
        ("_2", (0.28, -0.62, 0.16), (0.12, -0.05, -0.02), 40),
    ], ARGS, samples=32)
