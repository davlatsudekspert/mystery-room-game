"""lab_bench.glb — 1950s laboratory bench with glassware, vial rack, retort stand, Bunsen burner
and a brass microscope.

Model space (Blender, Z up): origin = floor centre, front faces -Y (Godot +Z), x in [-1.1, 1.1],
y in [-0.325, 0.325], z in [0, 0.92] (+ splashback/reagent shelf up to 1.36). Place at Godot
(-0.3, 0, 2.15) with rotation_degrees.y = 180 (front faces -Z).
Clear zones kept for other models: radio at bench-local x = -0.85 (x in [-1.08, -0.62], y <= 0.16).
vial_rack at bench-local (0.6, -0.05, 0.92) = room (-0.9, 0.92, 2.1).

Run: blender -b --factory-startup -P tools/blender/models/lab_bench.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_props as P  # noqa: E402

ARGS = M.main_guard()
M.reset_scene()
P.init_materials()

TOP = 0.92
FY = -0.28            # carcass front plane (fronts overlay from -0.30 to -0.28)
bench = []

# ---------------------------------------------------------------- top + carcass
bench.append(M.box("top", (2.2, 0.65, 0.03), loc=(0, 0, TOP - 0.015), mat="M_Bakelite", bevel=0.004, segments=2))
bench.append(M.box("top_drip", (2.18, 0.012, 0.012), loc=(0, -0.312, TOP - 0.036), mat="M_Bakelite", bevel=0.003, segments=1))
for name, x0, x1 in (("carcass_l", -1.09, -0.03), ("carcass_r", 0.55, 1.09)):
    bench.append(M.box(name, (x1 - x0, 0.31 - FY, 0.80), loc=((x0 + x1) / 2, (FY + 0.31) / 2, 0.09 + 0.40), bevel=0.003, segments=2))
    bench.append(M.box(name + "_kick", (x1 - x0 - 0.02, 0.5, 0.09), loc=((x0 + x1) / 2, 0.05, 0.045), mat="M_Wood_Panel",
                       bevel=0.0, segments=1))
# knee space: apron with a shallow drawer above, modesty panel at the back
bench.append(M.box("knee_apron", (0.58, 0.31 - FY, 0.14), loc=(0.26, (FY + 0.31) / 2, 0.82), bevel=0.003, segments=1))
bench.append(M.box("knee_back", (0.58, 0.02, 0.66), loc=(0.26, 0.29, 0.42), mat="M_Wood_Panel", bevel=0.002, segments=1))

fronts = []
hardware = []


def drawer(name, x, z, w, h, pull=True, card=False):
    """Overlay drawer front (raised field) centred at (x, z) with a brass bar pull."""
    f = P.raised_panel(name, w, h, 0.02, field_inset=0.022, raise_=0.004, loc=(x, FY, z))
    fronts.append(f)
    if pull:
        py = FY - 0.02
        zz = z - (0.008 if card else 0.0)
        for dx in (-0.045, 0.045):
            hardware.append(M.cylinder(f"{name}_post{dx}", 0.0045, 0.022, loc=(x + dx, py - 0.011, zz), rot=(math.pi / 2, 0, 0),
                                       verts=6, mat="M_Brass_Aged", bevel=0.0))
        hardware.append(M.cylinder(f"{name}_bar", 0.0055, 0.115, loc=(x, py - 0.024, zz), rot=(0, math.pi / 2, 0), verts=8,
                                   mat="M_Brass_Aged", bevel=0.002, segments=1))
    if card:
        hardware.append(M.box(f"{name}_cardframe", (0.06, 0.003, 0.028), loc=(x, FY - 0.0215, z + 0.03), mat="M_Brass_Aged",
                              bevel=0.001, segments=1))
        hardware.append(M.box(f"{name}_card", (0.052, 0.001, 0.02), loc=(x, FY - 0.0232, z + 0.03), mat="M_Paper", bevel=0.0,
                              segments=1))


def door(name, x, z, w, h, knob_dx):
    f = P.raised_panel(name, w, h, 0.02, field_inset=0.05, raise_=0.006, loc=(x, FY, z))
    fronts.append(f)
    hardware.append(M.lathe(f"{name}_knob", [(0.0, 0.0), (0.008, 0.0), (0.006, 0.01), (0.012, 0.022),
                                             (0.009, 0.03), (0.0, 0.031)], loc=(x + knob_dx, FY - 0.02, z + h * 0.32),
                            rot=(math.pi / 2, 0, 0), segments=10, mat="M_Brass_Aged"))
    hardware.append(M.box(f"{name}_escutcheon", (0.016, 0.002, 0.032), loc=(x + knob_dx, FY - 0.021, z + h * 0.32 - 0.04),
                          mat="M_Brass_Aged", bevel=0.0008, segments=1))


G = 0.004   # reveal between fronts
# bay A: drawer + double doors
drawer("drawer_a", -0.82, 0.81, 0.54 - G, 0.14 - G)
door("door_a1", -0.955, 0.43 - 0.0, 0.27 - G, 0.62 - G, 0.09)
door("door_a2", -0.685, 0.43, 0.27 - G, 0.62 - G, -0.09)
# bay B: four graduated drawers with card frames
zb = 0.89
for i, hgt in enumerate((0.14, 0.17, 0.2, 0.29)):
    drawer(f"drawer_b{i}", -0.29, zb - hgt / 2, 0.52 - G, hgt - G, card=True)
    zb -= hgt
# bay C (knee space): shallow pencil drawer
drawer("drawer_c", 0.26, 0.82, 0.58 - G, 0.14 - G)
# bay D: drawer + single door
drawer("drawer_d", 0.82, 0.81, 0.54 - G, 0.14 - G)
door("door_d", 0.82, 0.43, 0.54 - G, 0.62 - G, -0.2)

# ---------------------------------------------------------------- splashback + reagent shelf
back = []
back.append(M.box("splashback", (2.14, 0.02, 0.4), loc=(0, 0.315, TOP + 0.2), bevel=0.003, segments=2))
back.append(M.box("splash_rail", (2.14, 0.03, 0.02), loc=(0, 0.3, TOP + 0.16), bevel=0.004, segments=1))
for name, x in (("upright_l", -1.085), ("upright_r", 1.085)):
    back.append(M.box(name, (0.03, 0.17, 0.44), loc=(x, 0.24, TOP + 0.22), bevel=0.004, segments=1))
SHELF_Z = 1.32
back.append(M.box("reagent_shelf", (2.14, 0.17, 0.022), loc=(0, 0.24, SHELF_Z - 0.011), bevel=0.004, segments=2))
# brass gallery rail on the shelf front
back.append(M.cylinder("gallery_rail", 0.0035, 2.1, loc=(0, 0.163, SHELF_Z + 0.04), rot=(0, math.pi / 2, 0), verts=8,
                       mat="M_Brass_Aged", bevel=0.001, segments=1))
for i in range(5):
    x = -1.02 + i * 2.04 / 4
    back.append(M.cylinder(f"gallery_post{i}", 0.003, 0.04, loc=(x, 0.163, SHELF_Z + 0.02), verts=6, mat="M_Brass_Aged", bevel=0.0))
# gas tap on the splashback (feeds the Bunsen hose)
TAP = Vector((-0.52, 0.305, 1.0))
back.append(M.box("tap_plate", (0.05, 0.004, 0.06), loc=(TAP.x, 0.303, TAP.z), mat="M_Brass_Aged", bevel=0.0012, segments=1))
back.append(M.cylinder("tap_body", 0.011, 0.04, loc=(TAP.x, 0.285, TAP.z), rot=(math.pi / 2, 0, 0), verts=12, mat="M_Brass_Aged",
                       bevel=0.002))
back.append(M.lathe("tap_nozzle", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.006), (0.0045, 0.008), (0.0052, 0.012), (0.0045, 0.016),
                                   (0.0052, 0.02), (0.0035, 0.026), (0.0, 0.026)], loc=(TAP.x, 0.275, TAP.z - 0.006),
                    rot=(math.pi, 0, 0), segments=10, mat="M_Brass_Aged"))
back.append(M.box("tap_lever", (0.05, 0.006, 0.008), loc=(TAP.x + 0.012, 0.268, TAP.z + 0.008), rot=(0, -0.35, 0),
                  mat="M_Brass_Polished", bevel=0.002, segments=1))
# bakelite power outlet
back.append(M.box("outlet", (0.07, 0.012, 0.07), loc=(0.62, 0.301, 1.0), mat="M_Bakelite", bevel=0.006, segments=2))
for dx in (-0.012, 0.012):
    back.append(M.cylinder(f"outlet_hole{dx}", 0.0025, 0.002, loc=(0.62 + dx, 0.2945, 1.0), rot=(math.pi / 2, 0, 0), verts=6,
                           mat="M_Steel_Dark", bevel=0.0))

bench_obj = M.join(bench + fronts + hardware + back, "lab_bench")

# ---------------------------------------------------------------- glassware helpers
glass, liquids, misc = [], [], []


def erlenmeyer(name, x, y, s=1.0):
    o = [(0.0, 0.0), (0.038 * s, 0.0), (0.042 * s, 0.006 * s), (0.0135 * s, 0.1 * s), (0.0125 * s, 0.107 * s),
         (0.0125 * s, 0.135 * s), (0.0148 * s, 0.138 * s)]
    g = M.lathe(name, P.shell_profile(o, 0.0016), loc=(x, y, TOP), segments=14 if s >= 1 else 12, mat="M_Glass")
    glass.append(g)
    return g


def beaker(name, x, y, r, h, chip=False, rot_z=0.0):
    o = [(0.0, 0.0), (r - 0.004, 0.0), (r, 0.004), (r, h), (r + 0.0018, h + 0.002)]
    g = M.lathe(name, P.shell_profile(o, 0.0016), loc=(x, y, TOP), rot=(0, 0, rot_z), segments=14, mat="M_Glass")
    P.rim_edit(g, 0.0, 0.5, h - 0.012, dr=0.005)                       # pouring spout
    if chip:
        P.rim_edit(g, 2.3, 0.22, h - 0.006, dz=0.0045, jag=0.6, seed=3)   # chipped rim
    glass.append(g)
    # printed graduation marks (white enamel) on the front
    for k in range(4):
        zz = h * (0.3 + 0.15 * k)
        misc.append(M.box(f"{name}_mark{k}", (0.008 if k % 2 else 0.013, 0.0004, 0.0012),
                          loc=(x + r * math.sin(-rot_z) * 0.0, y - r - 0.0003, TOP + zz), mat="M_Enamel_Cream", bevel=0.0))
    return g


def roundbottom(name, loc):
    o = [(0.0, 0.0), (0.02, 0.004), (0.036, 0.018), (0.042, 0.042), (0.036, 0.066), (0.02, 0.082),
         (0.012, 0.092), (0.012, 0.155), (0.0142, 0.158)]
    g = M.lathe(name, P.shell_profile(o, 0.0016), loc=loc, segments=14, mat="M_Glass")
    glass.append(g)
    return g


# ---------------------------------------------------------------- vial rack + IA vials
RACK = Vector((0.6, -0.05, TOP))
rack_parts = [
    M.box("rack_base", (0.2, 0.075, 0.018), loc=RACK + Vector((0, 0, 0.009)), bevel=0.003, segments=2),
    M.box("rack_post_l", (0.016, 0.06, 0.075), loc=RACK + Vector((-0.092, 0.004, 0.018 + 0.0375)), bevel=0.0025, segments=1),
    M.box("rack_post_r", (0.016, 0.06, 0.075), loc=RACK + Vector((0.092, 0.004, 0.018 + 0.0375)), bevel=0.0025, segments=1),
]
board = M.box("rack_board", (0.2, 0.062, 0.014), loc=RACK + Vector((0, 0.002, 0.093 + 0.007)), bevel=0.0025, segments=2)
VX = (-0.058, 0.0, 0.058)
for i, vx in enumerate(VX):
    cutter = M.cylinder(f"hole{i}", 0.0158, 0.05, loc=RACK + Vector((vx, 0.0, 0.1)), verts=12, bevel=0.0)
    M.boolean(board, cutter)
rack_parts.append(board)
rack_parts.append(M.box("rack_brass_edge", (0.2, 0.0025, 0.016), loc=RACK + Vector((0, -0.0303, 0.1)), mat="M_Brass_Aged",
                        bevel=0.0008, segments=1))
rack_parts.append(M.box("rack_plaque", (0.05, 0.0018, 0.012), loc=RACK + Vector((0, -0.0385, 0.009)), mat="M_Brass_Polished",
                        bevel=0.0006, segments=1))
vial_rack = M.join(rack_parts, "vial_rack")

VIALS = (("green", "Green", 0.066), ("crimson", "Crimson", 0.074), ("cobalt", "Cobalt", 0.061))
VR = 0.0145
LABEL_Z0, LABEL_H, LABEL_W = 0.03, 0.019, 0.038
ia_vials = []
for (key, cap, fill), vx in zip(VIALS, VX):
    base = RACK + Vector((vx, 0.0, 0.0195))
    o = [(0.0, 0.0), (0.008, 0.0007), (0.0128, 0.0038), (VR, 0.009), (VR, 0.098), (0.0139, 0.1), (0.0139, 0.104)]
    g = M.lathe(f"IA_vial_{key}", P.shell_profile(o, 0.0011, lip=0.0012), loc=base, segments=14, mat="M_Glass")
    cork = M.lathe(f"cork_{key}", [(0.0, 0.092), (0.0115, 0.092), (0.0124, 0.103), (0.0142, 0.1045), (0.0145, 0.116),
                                   (0.0132, 0.1185), (0.0, 0.1185)], loc=base, segments=10, mat="M_Cork")
    vial = M.join([g, cork], f"IA_vial_{key}")
    liq = M.lathe(f"vial_liquid_{key}", [(0.0, 0.0012), (0.0078, 0.0018), (0.0123, 0.0048), (VR - 0.0012, 0.0095),
                                         (VR - 0.0012, fill), (0.009, fill - 0.0007), (0.0, fill - 0.001)],
                  loc=base, segments=12, mat=f"M_Liquid_{cap}")
    # curved paper label: arc-length UVs, u increases to the viewer's right (+X) seen from the front (-Y)
    span = LABEL_W / (VR + 0.0003)
    a0 = -math.pi / 2 - span / 2
    n = 12
    verts, faces = [], []
    for k in range(n + 1):
        a = a0 + span * k / n
        for zz in (LABEL_Z0, LABEL_Z0 + LABEL_H):
            verts.append(((VR + 0.0003) * math.cos(a), (VR + 0.0003) * math.sin(a), zz))
    for k in range(n):
        b0, t0, b1, t1 = 2 * k, 2 * k + 1, 2 * k + 2, 2 * k + 3
        faces.append((b0, b1, t1, t0))
    lab = P.mesh_obj(f"vial_label_{key}", verts, faces, [f"M_Decal_VialLabel_{cap}"])
    P.fix_normals(lab)
    me = lab.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            k, top = divmod(vi, 2)
            uvl.data[li].uv = (k / n, float(top))
    lab.location = base
    M.refresh()
    centre = base + Vector((0, 0, 0.059))
    M.set_origin(vial, centre)
    M.set_parent(liq, vial)
    M.set_parent(lab, vial)
    ia_vials.append(vial)

# ---------------------------------------------------------------- free glassware on the bench
erlenmeyer("erlenmeyer_large", 0.9, -0.12)
erlenmeyer("erlenmeyer_small", 1.0, 0.02, s=0.75)
beaker("beaker_chipped", -0.12, -0.16, 0.038, 0.11, chip=True, rot_z=-0.4)
beaker("beaker_small", 0.83, 0.07, 0.033, 0.092, rot_z=0.9)
# glass stirring rod leaning in the chipped beaker
glass.append(P.rod("stirring_rod", (-0.115, -0.16, TOP + 0.006), (-0.15, -0.205, TOP + 0.19), 0.0028, sides=8, mat="M_Glass"))
# graduated cylinder with a hexagonal foot
grad = M.lathe("graduated_cylinder", P.shell_profile([(0.0, 0.012), (0.0145, 0.012), (0.0145, 0.24), (0.0165, 0.243)], 0.0014),
               loc=(1.02, -0.17, TOP), segments=12, mat="M_Glass")
P.rim_edit(grad, 0.0, 0.6, 0.235, dr=0.004)
glass.append(grad)
glass.append(M.lathe("graduated_foot", [(0.0, 0.0), (0.034, 0.0), (0.034, 0.006), (0.016, 0.012), (0.0, 0.012)],
                     loc=(1.02, -0.17, TOP), segments=6, mat="M_Glass"))
for k in range(5):
    misc.append(M.box(f"grad_mark{k}", (0.009 if k % 2 else 0.014, 0.0004, 0.0012), loc=(1.02 - 0.003, -0.17 - 0.0148, TOP + 0.06 + 0.03 * k),
                      mat="M_Enamel_Cream", bevel=0.0))

# reagent bottles on the shelf (clear glass, ground stoppers, paper labels)
for i, (x, kind, content) in enumerate(((-0.9, "wide", "M_Enamel_Cream"), (-0.36, "tall", "M_Copper"),
                                        (0.95, "tall", None))):
    y = 0.235
    if kind == "tall":
        o = [(0.0, 0.0), (0.028, 0.0), (0.031, 0.006), (0.031, 0.09), (0.018, 0.116), (0.011, 0.122), (0.011, 0.135)]
        stop = [(0.0, 0.125), (0.0095, 0.125), (0.013, 0.139), (0.013, 0.146), (0.018, 0.152), (0.018, 0.162), (0.0, 0.165)]
        lab_z = (0.035, 0.07)
    else:
        o = [(0.0, 0.0), (0.034, 0.0), (0.037, 0.006), (0.037, 0.075), (0.03, 0.088), (0.026, 0.09), (0.026, 0.1)]
        stop = [(0.0, 0.092), (0.0245, 0.092), (0.029, 0.104), (0.029, 0.112), (0.02, 0.118), (0.0, 0.119)]
        lab_z = (0.025, 0.055)
    glass.append(M.lathe(f"bottle_{i}", P.shell_profile(o, 0.0018), loc=(x, y, SHELF_Z), segments=12, mat="M_Glass"))
    glass.append(M.lathe(f"bottle_{i}_stopper", stop, loc=(x, y, SHELF_Z), segments=10, mat="M_Glass"))
    r = o[3][0] + 0.0004
    lab = M.lathe(f"bottle_{i}_label", [(r, lab_z[0]), (r, lab_z[1])], loc=(x, y, SHELF_Z), segments=12, mat="M_Paper")
    bm = bmesh.new()
    bm.from_mesh(lab.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y > -r * 0.3], context="FACES")
    bm.to_mesh(lab.data)
    bm.free()
    misc.append(lab)
    if content:
        misc.append(M.lathe(f"bottle_{i}_content", [(0.0, 0.002), (o[3][0] - 0.0025, 0.002), (o[3][0] - 0.0025, 0.03),
                                                     (o[3][0] * 0.6, 0.036), (0.0, 0.038)], loc=(x, y, SHELF_Z), segments=10,
                            mat=content))

# ---------------------------------------------------------------- retort stand + round-bottom flask + Bunsen burner
RS = Vector((-0.33, -0.03, TOP))
misc.append(M.box("retort_base", (0.13, 0.23, 0.012), loc=RS + Vector((0, 0, 0.006)), mat="M_Steel_Painted", bevel=0.004, segments=2))
for dx in (-0.055, 0.055):
    for dy in (-0.1, 0.1):
        misc.append(M.cylinder(f"retort_foot{dx}{dy}", 0.006, 0.003, loc=RS + Vector((dx, dy, -0.0005)), verts=6, mat="M_Rubber", bevel=0.0))
ROD = RS + Vector((0.0, 0.09, 0.012))
misc.append(M.cylinder("retort_rod", 0.0065, 0.52, loc=ROD + Vector((0, 0, 0.26)), verts=10, mat="M_Chrome", bevel=0.002))
misc.append(M.lathe("retort_rod_boss", [(0.0, 0.0), (0.015, 0.0), (0.012, 0.012), (0.009, 0.02), (0.0, 0.02)], loc=ROD,
                    segments=10, mat="M_Steel_Painted"))
CLAMP_Z = TOP + 0.3
misc.append(M.box("boss_head", (0.028, 0.03, 0.035), loc=(ROD.x, ROD.y, CLAMP_Z), mat="M_Steel_Dark", bevel=0.003, segments=1))
misc.append(M.lathe("boss_screw", [(0.0, 0.0), (0.003, 0.0), (0.003, 0.012), (0.009, 0.013), (0.009, 0.02), (0.0, 0.021)],
                    loc=(ROD.x + 0.014, ROD.y, CLAMP_Z), rot=(0, math.pi / 2, 0), segments=8, mat="M_Steel_Dark"))
FLASK = Vector((RS.x, RS.y - 0.06, TOP + 0.012 + 0.135 + 0.05))
arm_end = Vector((FLASK.x, FLASK.y + 0.022, CLAMP_Z))
misc.append(P.rod("clamp_arm", (ROD.x, ROD.y - 0.012, CLAMP_Z), arm_end, 0.0045, sides=8, mat="M_Chrome"))
for side in (-1, 1):   # two padded jaws around the flask neck
    misc.append(M.box(f"clamp_jaw{side}", (0.006, 0.03, 0.016), loc=(FLASK.x + side * 0.018, FLASK.y + 0.003, CLAMP_Z),
                      rot=(0, 0, side * 0.25), mat="M_Steel_Dark", bevel=0.0015, segments=1))
    misc.append(M.box(f"clamp_pad{side}", (0.004, 0.022, 0.014), loc=(FLASK.x + side * 0.0145, FLASK.y, CLAMP_Z),
                      mat="M_Cork", bevel=0.001, segments=1))
misc.append(M.box("clamp_yoke", (0.044, 0.008, 0.016), loc=(FLASK.x, FLASK.y + 0.02, CLAMP_Z), mat="M_Steel_Dark", bevel=0.0015,
                  segments=1))
misc.append(M.lathe("clamp_wingnut", [(0.0, 0.0), (0.003, 0.0), (0.003, 0.008), (0.008, 0.009), (0.008, 0.012), (0.0, 0.013)],
                    loc=(FLASK.x + 0.024, FLASK.y + 0.006, CLAMP_Z), rot=(0, math.pi / 2, 0), segments=8, mat="M_Steel_Dark"))
rb = roundbottom("roundbottom_flask", (FLASK.x, FLASK.y, CLAMP_Z - 0.115))
liquids.append(M.lathe("flask_residue", [(0.0, 0.0018), (0.012, 0.003), (0.022, 0.0075), (0.0, 0.0085)],
                       loc=(FLASK.x, FLASK.y, CLAMP_Z - 0.115), segments=12, mat="M_Bakelite"))

BURNER = Vector((RS.x, FLASK.y, TOP + 0.012))
misc.append(M.lathe("bunsen", [(0.0, 0.0), (0.036, 0.0), (0.037, 0.004), (0.033, 0.01), (0.018, 0.016), (0.009, 0.019),
                               (0.0065, 0.024), (0.0065, 0.12), (0.0078, 0.124), (0.0078, 0.13), (0.0058, 0.131),
                               (0.0058, 0.126), (0.0, 0.126)], loc=BURNER, segments=12, mat="M_Brass_Aged"))
misc.append(M.lathe("bunsen_collar", [(0.0082, 0.03), (0.0095, 0.031), (0.0095, 0.05), (0.0082, 0.051)], loc=BURNER, segments=12,
                    mat="M_Brass_Polished"))
misc.append(M.cylinder("bunsen_airhole", 0.003, 0.0004, loc=BURNER + Vector((0, -0.0096, 0.04)), rot=(math.pi / 2, 0, 0), verts=6,
                       mat="M_Steel_Dark", bevel=0.0))
inlet = BURNER + Vector((0.0, 0.014, 0.01))
misc.append(M.lathe("bunsen_inlet", [(0.0, 0.0), (0.004, 0.0), (0.004, 0.012), (0.0052, 0.015), (0.0042, 0.019), (0.0052, 0.023),
                                     (0.0042, 0.027), (0.0035, 0.032), (0.0, 0.032)], loc=inlet, rot=(-math.pi / 2, 0, 0), segments=8,
                    mat="M_Brass_Aged"))
# rubber hose: from the burner inlet, over the retort base, along the bench, up to the gas tap nozzle
h_start = inlet + Vector((0, 0.022, 0.0))
path = P.bezier(h_start, h_start + Vector((0, 0.06, 0.0)), Vector((RS.x + 0.02, 0.1, TOP + 0.03)), Vector((RS.x - 0.06, 0.16, TOP + 0.007)), 8)
path += P.bezier(Vector((RS.x - 0.06, 0.16, TOP + 0.007)), Vector((RS.x - 0.13, 0.2, TOP + 0.007)), Vector((TAP.x, 0.27, TOP + 0.02)),
                 Vector((TAP.x, 0.275, TAP.z - 0.03)), 8)[1:]
misc.append(P.tube("bunsen_hose", path, 0.0058, sides=7, mat="M_Rubber"))

# ---------------------------------------------------------------- brass microscope (lathe-turned parts)
MS = Vector((0.12, -0.02, TOP))
scope = []
foot = [(-0.05, -0.065), (-0.05, 0.005)] + P.arc(0.0, 0.005, 0.05, math.pi, 0.0, n=6)[1:-1] + [(0.05, 0.005), (0.05, -0.065),
                                                                                            (0.029, -0.065), (0.029, 0.0)]
foot += P.arc(0.0, 0.0, 0.029, 0.0, math.pi, n=5)[1:-1] + [(-0.029, 0.0), (-0.029, -0.065)]
f = M.extrude_profile("ms_foot", list(reversed(foot)), 0.014, loc=MS, mat="M_Steel_Dark", bevel=0.0018, segments=1)
scope.append(f)
scope.append(M.box("ms_pillar", (0.026, 0.02, 0.07), loc=MS + Vector((0, 0.035, 0.014 + 0.035)), mat="M_Brass_Aged", bevel=0.002, segments=1))
scope.append(M.cylinder("ms_trunnion", 0.012, 0.036, loc=MS + Vector((0, 0.036, 0.082)), rot=(0, math.pi / 2, 0), verts=12,
                        mat="M_Brass_Polished", bevel=0.002))
limb = [(0.025, 0.068), (0.047, 0.068), (0.047, 0.16), (0.044, 0.19), (0.032, 0.222), (0.014, 0.246), (-0.004, 0.256),
        (-0.004, 0.214), (0.008, 0.206), (0.019, 0.19), (0.025, 0.17)]
lb = M.extrude_profile("ms_limb", limb, 0.016, mat="M_Brass_Aged", bevel=0.002, segments=1)
lb.rotation_euler = (math.pi / 2, 0, math.pi / 2)
lb.location = MS + Vector((-0.008, 0, 0))
scope.append(lb)
scope.append(M.box("ms_stage", (0.086, 0.086, 0.006), loc=MS + Vector((0, -0.02, 0.1)), mat="M_Steel_Dark", bevel=0.0018, segments=1))
scope.append(M.box("ms_stage_bracket", (0.02, 0.03, 0.02), loc=MS + Vector((0, 0.025, 0.094)), mat="M_Brass_Aged", bevel=0.002, segments=1))
scope.append(M.cylinder("ms_aperture", 0.007, 0.0006, loc=MS + Vector((0, -0.02, 0.1032)), verts=12, mat="M_Bakelite", bevel=0.0))
for side in (-1, 1):
    scope.append(M.box(f"ms_clip{side}", (0.005, 0.032, 0.0012), loc=MS + Vector((side * 0.026, -0.01, 0.1038)), rot=(0, 0, side * 0.15),
                       mat="M_Brass_Polished", bevel=0.0004, segments=1))
    scope.append(M.cylinder(f"ms_clip_pin{side}", 0.0022, 0.004, loc=MS + Vector((side * 0.028, 0.004, 0.1045)), verts=8,
                            mat="M_Brass_Polished", bevel=0.0005))
# glass slide on the stage
scope.append(M.box("ms_slide", (0.025, 0.075, 0.0012), loc=MS + Vector((0.004, -0.02, 0.1036)), rot=(0, 0, 0.06), mat="M_Glass",
                   bevel=0.0003, segments=1))
scope.append(M.cylinder("ms_condenser", 0.011, 0.014, loc=MS + Vector((0, -0.02, 0.088)), verts=12, mat="M_Steel_Dark", bevel=0.0015))
# substage mirror on a swinging arm
scope.append(P.rod("ms_mirror_arm", MS + Vector((0, 0.03, 0.03)), MS + Vector((0, -0.002, 0.044)), 0.003, sides=8, mat="M_Brass_Aged"))
scope.append(M.cylinder("ms_mirror_rim", 0.017, 0.005, loc=MS + Vector((0, -0.02, 0.046)), rot=(0.55, 0, 0), verts=12,
                        mat="M_Brass_Aged", bevel=0.0012))
scope.append(M.cylinder("ms_mirror", 0.0145, 0.0008, loc=MS + Vector((0, -0.021, 0.0487)), rot=(0.55, 0, 0), verts=12,
                        mat="M_Chrome", bevel=0.0))
TUBE = MS + Vector((0, -0.02, 0.0))
scope.append(M.lathe("ms_tube", [(0.0, 0.15), (0.018, 0.15), (0.018, 0.158), (0.0155, 0.16), (0.0155, 0.268), (0.017, 0.27),
                                 (0.017, 0.278), (0.0135, 0.279), (0.0135, 0.296), (0.0148, 0.297), (0.0148, 0.31),
                                 (0.0112, 0.313), (0.0, 0.313)], loc=TUBE, segments=14, mat="M_Brass_Polished"))
scope.append(M.cylinder("ms_eyelens", 0.0105, 0.0006, loc=TUBE + Vector((0, 0, 0.3133)), verts=12, mat="M_Glass", bevel=0.0))
scope.append(M.lathe("ms_nosepiece", [(0.0, 0.127), (0.012, 0.128), (0.019, 0.134), (0.021, 0.141), (0.017, 0.15), (0.0, 0.15)],
                     loc=TUBE, segments=12, mat="M_Brass_Aged"))
obj_prof = [(0.0, 0.0), (0.0035, 0.0), (0.0055, 0.004), (0.0072, 0.016), (0.0078, 0.02), (0.0078, 0.026), (0.0, 0.026)]
scope.append(M.lathe("ms_objective_a", obj_prof, loc=TUBE + Vector((0, 0, 0.108)), segments=10, mat="M_Brass_Polished"))
ob = M.lathe("ms_objective_b", [(r * 0.85, z * 0.8) for (r, z) in obj_prof], loc=TUBE + Vector((0.012, 0, 0.118)),
             rot=(0, 0.6, 0), segments=8, mat="M_Brass_Polished")
scope.append(ob)
scope.append(M.box("ms_tube_clamp", (0.016, 0.022, 0.04), loc=MS + Vector((0, 0.001, 0.232)), mat="M_Brass_Aged", bevel=0.002, segments=1))
knob = [(0.0, 0.0), (0.0145, 0.0), (0.0155, 0.002), (0.0155, 0.008), (0.0145, 0.01), (0.005, 0.012), (0.0, 0.02)]
for side in (-1, 1):
    scope.append(M.lathe(f"ms_focus{side}", knob, loc=MS + Vector((side * 0.028, 0.028, 0.205)), rot=(0, -side * math.pi / 2, 0),
                         segments=12, mat="M_Brass_Polished"))
scope.append(M.lathe("ms_fine", [(0.0, 0.0), (0.008, 0.0), (0.008, 0.006), (0.004, 0.008), (0.0, 0.008)],
                     loc=MS + Vector((0, 0.04, 0.218)), rot=(-0.9, 0, 0), segments=10, mat="M_Brass_Polished"))
microscope = M.join(scope, "microscope")

# ---------------------------------------------------------------- join statics, finalize, export
M.join(glass, "glassware")
M.join(misc, "bench_props")
if liquids:
    M.join(liquids, "residue")
M.finalize(smooth_angle=40)
# decal labels keep their 0..1 UVs (box_uv skips M_Decal_ faces)
P.report("lab_bench")
M.export_glb("lab_bench")

P.shots("lab_bench", [
    ("", (1.45, -2.35, 1.75), (0.05, 0.0, 1.0), 32),
    ("_2", (0.66, -0.42, 1.06), (0.58, -0.05, 0.97), 50),
    ("_3", (-0.05, -0.75, 1.2), (-0.12, -0.04, 1.06), 45),
], ARGS)
