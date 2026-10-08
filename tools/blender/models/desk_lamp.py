"""desk_lamp.glb — 1950s brass banker's lamp with a green cased-glass shade (Leyla's desk).

Model space (Blender, Z up): origin = centre of the base underside on the desk (Z = 0), front (the
shade opening and the pull chain) toward -Y (Godot +Z). Footprint 0.24 x 0.16, height ~0.43.
Place on the desk at Godot (-1.18, 0.78, -2.32) (lab7_room.gd uses yaw 25 deg).
Parts: `bulb` (M_Emissive_Warm) and empty `light_origin` at the bulb centre (local (0, -0.035, 0.335));
`lamp_shade` (M_Glass_Green outside / M_Enamel_White inside). Rest static; no IA parts.

Run: blender -b --factory-startup -P tools/blender/models/desk_lamp.py [-- --no-render]
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

NAME = "desk_lamp"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
M.material("M_Glass_Green", color="1F5C35", rough=0.08, metal=0.0)

# ---------------------------------------------------------------- stepped cast-brass base
base = P.rrect_loft("lamp_base", [
    (0.240, 0.160, 0.030, 0.000), (0.240, 0.160, 0.030, 0.007), (0.236, 0.156, 0.028, 0.010),
    (0.226, 0.146, 0.024, 0.012), (0.222, 0.142, 0.022, 0.016), (0.214, 0.134, 0.019, 0.019),
    (0.200, 0.120, 0.016, 0.022), (0.188, 0.108, 0.013, 0.0235), (0.184, 0.104, 0.012, 0.0235)],
    mat="M_Brass_Aged", n=4)
parts = [base]
# raised boss where the stem enters (rear), with a polished collar
STEM = Vector((0.0, 0.032, 0.0))
parts.append(M.lathe("stem_boss", [(0.0, 0.0235), (0.03, 0.0235), (0.028, 0.03), (0.02, 0.038), (0.013, 0.046), (0.0115, 0.056),
                                   (0.0, 0.056)], loc=STEM, segments=20, mat="M_Brass_Aged"))
parts.append(K.lathe2("stem_collar", [(0.0, 0.054), (0.0125, 0.054), (0.0135, 0.057, "k"), (0.0135, 0.066, "k"), (0.012, 0.069),
                                      (0.0, 0.069)], segments=24, mat="M_Brass_Polished", knurl=0.0008, loc=STEM))
# stem: straight up, then a smooth crook forward over the shade
crook = [STEM + Vector((0, 0, 0.066)), STEM + Vector((0, 0, 0.30))]
crook += P.bezier(STEM + Vector((0, 0, 0.30)), STEM + Vector((0, 0, 0.355)), Vector((0, 0.012, 0.39)), Vector((0, -0.026, 0.39)), 6)[1:]
crook += P.bezier(Vector((0, -0.026, 0.39)), Vector((0, -0.04, 0.39)), Vector((0, -0.048, 0.386)), Vector((0, -0.05, 0.378)), 3)[1:]
parts.append(P.tube("stem", crook, 0.0075, sides=12, mat="M_Brass_Aged"))
for zc in (0.17, 0.30):  # decorative rings on the stem
    parts.append(M.lathe(f"stem_ring{zc}", [(0.0074, zc - 0.006), (0.0098, zc - 0.003), (0.0098, zc + 0.003), (0.0074, zc + 0.006)],
                         loc=STEM, segments=16, mat="M_Brass_Polished"))
# shade holder: boss on the shade top + finial
HOLD = Vector((0.0, -0.05, 0.372))
parts.append(M.lathe("shade_boss", [(0.0, -0.004), (0.017, -0.004), (0.019, 0.0), (0.012, 0.006), (0.0085, 0.008), (0.0, 0.009)],
                     loc=HOLD, segments=16, mat="M_Brass_Polished"))

# ---------------------------------------------------------------- green cased-glass shade (stretched dome, tilted forward)
SH_L = 0.105                   # straight length added between the dome halves (total width ~0.26)
SH_H = 0.0705
# built as a bowl (outer surface from the bottom centre up to the rim), then turned upside down
outer = [(0.0, 0.0), (0.024, 0.002), (0.044, 0.009), (0.059, 0.021), (0.0685, 0.0365), (0.0735, 0.0535), (0.0752, 0.0655),
         (0.0756, SH_H)]
loop = P.shell_profile(outer, 0.0032, lip=0.0012)            # outer -> rolled lip (white edge of cased glass) -> inner
n_out = len(outer)
bands = ["M_Glass_Green"] * (n_out - 1) + ["M_Enamel_White"] * (len(loop) - n_out)
shade = K.lathe2("lamp_shade", loop, segments=28, mat="M_Glass_Green", band_mats=bands, phase=math.pi / 28)
bm = bmesh.new()
bm.from_mesh(shade.data)
for v in bm.verts:
    v.co.x += math.copysign(SH_L / 2, v.co.x) if abs(v.co.x) > 1e-7 else 0.0
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(shade.data)
bm.free()
shade.data.transform(Matrix.Rotation(math.pi, 4, "X"))      # apex on top at the local origin, opening down
SHADE_TILT = math.radians(-14)                              # opening tilts toward the reader (-Y)
SH_TOP = HOLD + Vector((0, 0, -0.004))
shade.location = SH_TOP
shade.rotation_euler = (SHADE_TILT, 0, 0)

# ---------------------------------------------------------------- socket, bulb, pull chain (inside the shade)
M.refresh()
R = shade.matrix_world.to_3x3()
down = R @ Vector((0, 0, -1))
SOCK = SH_TOP + down * 0.004
sock = M.lathe("socket", [(0.0, 0.0), (0.011, 0.0), (0.012, -0.004), (0.012, -0.018), (0.0105, -0.021), (0.0, -0.021)],
               segments=14, mat="M_Brass_Aged")
sock.data.transform(Matrix.Rotation(SHADE_TILT, 4, "X"))
sock.location = SOCK
parts.append(sock)
BULB_C = SOCK + down * 0.0415
bulb = M.lathe("bulb", [(r * 0.85, z * 0.85) for (r, z) in ((0.0, -0.002), (0.0085, -0.003), (0.0115, -0.009), (0.0165, -0.02),
                                                         (0.0182, -0.03), (0.017, -0.039), (0.0125, -0.047), (0.006, -0.0505),
                                                         (0.0, -0.051))], segments=16, mat="M_Emissive_Warm")
bulb.data.transform(Matrix.Translation((0, 0, -0.018)))
bulb.data.transform(Matrix.Rotation(SHADE_TILT, 4, "X"))
bulb.location = SOCK
M.refresh()
M.set_origin(bulb, BULB_C)
# bead pull chain from the socket down past the rim, brass pull
ch0 = SOCK + down * 0.012 + Vector((0.016, 0.0, 0.0))
ch1 = Vector((ch0.x + 0.002, ch0.y - 0.004, 0.214))
beads = []
n_b = 14
for i in range(n_b + 1):
    p = ch0.lerp(ch1, i / n_b)
    beads.append(M.sphere(f"bead{i}", 0.0016, loc=p, segments=6, rings=3, mat="M_Brass_Polished"))
beads.append(P.tube("chain_wire", [ch0, ch1], 0.0005, sides=4, mat="M_Brass_Aged"))
beads.append(M.lathe("pull", [(0.0, 0.0), (0.0025, 0.0005), (0.0048, -0.006), (0.0052, -0.014), (0.0035, -0.021), (0.0, -0.023)],
                     loc=ch1, segments=10, mat="M_Brass_Polished"))
parts += beads

# ---------------------------------------------------------------- cloth flex into a brass desk grommet behind the base
G0 = Vector((0.045, 0.155, 0.0))
parts.append(M.lathe("grommet", [(0.0115, 0.0), (0.0175, 0.0), (0.0185, 0.0015), (0.0165, 0.003), (0.0115, 0.0015)],
                     loc=G0, segments=16, mat="M_Brass_Aged"))
parts.append(M.cylinder("grommet_hole", 0.0114, 0.0004, loc=G0 + Vector((0, 0, 0.0004)), verts=16, mat="M_Bakelite", bevel=0.0))
cab = P.bezier(Vector((0.02, 0.078, 0.006)), Vector((0.03, 0.11, 0.004)), Vector((0.06, 0.13, 0.005)), G0 + Vector((0.0, -0.004, 0.006)), 7)
cab += [G0 + Vector((0.0, 0.0, -0.002))]
parts.append(P.tube("flex", cab, 0.0035, sides=7, mat="M_Fabric"))
parts.append(M.box("flex_entry", (0.012, 0.012, 0.008), loc=(0.02, 0.078, 0.006), mat="M_Brass_Aged", bevel=0.002, segments=1))
# little cream maker's label on the base front step
parts.append(M.box("label", (0.042, 0.0008, 0.0055), loc=(0.0, -0.0726, 0.0175), rot=(-0.45, 0, 0), mat="M_Enamel_Cream",
                   bevel=0.0, segments=1))
body = M.join(parts, "desk_lamp_body")
M.empty("light_origin", BULB_C)
M.set_parent(bpy.data.objects["light_origin"], body)
M.set_parent(bulb, body)

M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)
print("[desk_lamp] light_origin local", tuple(round(c, 4) for c in BULB_C))

if "--no-render" not in ARGS:
    P.render_threads(2)
    P.qa_box("qa_desk", (1.0, 0.8, 0.03), (0.0, 0.1, -0.015), colour="4A2C1C", rough=0.5)
    P.qa_box("qa_wall", (1.4, 0.04, 1.2), (0.0, 0.42, 0.5), colour="B8B2A0")
    P.shots(NAME, [
        ("", (0.55, -0.75, 0.48), (0.0, 0.0, 0.2), 45),
        ("_2", (-0.42, -0.42, 0.12), (0.0, -0.03, 0.3), 40),
    ], ARGS, samples=32)
