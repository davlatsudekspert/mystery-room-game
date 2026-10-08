"""poster_frame.glb — Strand's "Tabula Resonantiarum" poster behind glass in a thin black frame (M_Lacquer_Black).

Model space (Blender, Z up): back plane at Y = 0, front toward -Y (Godot +Z).
Origin = back plane, centre of the frame. Paper 0.50 x 0.7070 m (aspect 1024 : 1448), frame 0.544 x 0.751.
Place at Godot (-0.3, 1.9, 2.5), rotation_degrees.y = 180 (front faces -Z).
`poster_paper`: M_Decal_Poster, planar 0..1 UV (u -> +X seen from the front, v -> up), not mirrored.
`poster_glass`: M_Glass pane in front of the paper. Static; no IA parts.

Run: blender -b --factory-startup -P tools/blender/models/poster_frame.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_props as P  # noqa: E402

NAME = "poster_frame"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
M.material("M_Lacquer_Black", color="141211", rough=0.32)

PW = 0.50
PH = PW * 1448.0 / 1024.0      # 0.7070
FW = 0.022                     # frame moulding width

# black lacquered frame: rounded outer edge, flat face, small inner bevel stepping down to the glass
prof = [(0.0, 0.0), (0.0, 0.0175), (0.0012, 0.0212), (0.0042, 0.0236), (0.0085, 0.024), (0.0155, 0.024), (0.0185, 0.0222),
        (0.0205, 0.0185), (FW, 0.0165), (FW, 0.0)]
frame = P.frame_sweep("poster_frame_body", PW + 2 * FW, PH + 2 * FW, prof, mat="M_Lacquer_Black")
back = M.box("backboard", (PW + 0.02, 0.004, PH + 0.02), loc=(0, -0.002, 0), mat="M_Wood_Panel", bevel=0.0008, segments=1)
# turn buttons that hold the backboard (seen only from the side) + hanging wire hooks hidden behind
clips = []
for (x, z) in ((-PW / 2 + 0.05, PH / 2 + 0.01), (PW / 2 - 0.05, PH / 2 + 0.01), (-PW / 2 + 0.05, -PH / 2 - 0.01),
               (PW / 2 - 0.05, -PH / 2 - 0.01)):
    clips.append(M.box(f"clip{x}{z}", (0.018, 0.0015, 0.01), loc=(x, -0.0008, z), mat="M_Steel_Dark", bevel=0.0004, segments=1))
M.join([frame, back] + clips, "poster_frame_body")

# paper: slightly cockled sheet (a few rows of verts with a gentle wave), decal UVs 0..1
nx, nz = 6, 8
verts, faces = [], []
for j in range(nz + 1):
    for i in range(nx + 1):
        u, v = i / nx, j / nz
        wave = 0.0007 * math.sin(math.pi * u) * math.sin(math.pi * v) + 0.0003 * math.sin(3.1 * math.pi * v + 0.6)
        verts.append(((u - 0.5) * PW, -0.0062 - wave, (v - 0.5) * PH))
for j in range(nz):
    for i in range(nx):
        a = j * (nx + 1) + i
        faces.append((a, a + 1, a + nx + 2, a + nx + 1))
paper = P.mesh_obj("poster_paper", verts, faces, ["M_Decal_Poster"])
P.fix_normals(paper)
if paper.data.polygons[0].normal.y > 0:
    paper.data.flip_normals()
M.planar_uv(paper, axis="Y")
glass = M.box("poster_glass", (PW + 0.004, 0.002, PH + 0.004), loc=(0, -0.0105, 0), mat="M_Glass", bevel=0.0, segments=1)

M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)

if "--no-render" not in ARGS:
    P.render_threads(2)
    P.qa_box("qa_wall", (1.4, 0.04, 1.4), (0, 0.02, 0.0), colour="B8B2A0")
    P.shots(NAME, [
        ("", (0.45, -1.35, 0.15), (0.0, 0.0, 0.0), 45),
        ("_2", (0.42, -0.3, 0.42), (0.2, 0.0, 0.3), 40),
    ], ARGS, samples=32)
