"""gear_box.glb — Prof. Strand's puzzle box (Lab 7, bookshelf shelf 3).

Walnut box with a brass top plate on a hinged lid. Three brass clockwork wheels with blued-steel
pointers sit on the lid plate; three knurled brass push-knobs on the front drive them. Inside: a
felt-lined tray with a cradle for the battery cell (empty `battery_anchor`).

Model space: front = Blender -Y (Godot +Z), base on Z = 0, origin at the base centre.
Interactive parts (origins at pivots, identity rotation at rest):
  IA_box_lid   origin on the back hinge axis; children: IA_gear_0..2 (+ static plate parts)
  IA_gear_0..2 origin at the wheel centre; rotate about local Godot Y; pointer at rest -> Godot -Z
  IA_knob_0..2 origin at the knob axis on the escutcheon face; axis = Godot Z

The middle wheel runs one deck higher than the outer wheels: the teeth interleave when seen from
above (they mesh visually) but never intersect, whatever the puzzle turns.
    blender -b --factory-startup -P tools/blender/models/gear_box.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix  # noqa: E402

BW, BD, BH, LH = 0.26, 0.18, 0.092, 0.030   # body width/depth/height, lid height
WALL = 0.011
FLOOR = 0.012
PT = BH + LH + 0.0025                         # top of the brass plate
GX = (-0.072, 0.0, 0.072)
GY = -0.004
N_TEETH, R_ROOT, R_TIP, G_T = 12, 0.0305, 0.0395, 0.004
WASHER = 0.0015
G_Z0 = (PT + WASHER, PT + WASHER + G_T + 0.0016, PT + WASHER)   # gear bottoms (middle wheel raised)
# tooth phases so neighbours interleave in plan view (all 60° steps keep it that way)
G_PHASE = (math.radians(0.0), math.radians(15.0), math.radians(0.0))
KZ = 0.052                                    # knob axis height
HINGE = (0.0, BD / 2 + 0.003, BH)             # lid hinge axis (X direction)
TRAY_TOP = 0.050


def corner_L(x, y, sx, sy, z0, h, arm=0.02, t=0.0013):
    """Brass L-shaped corner guard around the vertical box corner at (x, y)."""
    pts = [(x + sx * arm, y), (x + sx * arm, y - sy * t), (x - sx * t, y - sy * t), (x - sx * t, y + sy * arm),
           (x, y + sy * arm), (x, y)]
    obj = L.curve_solid("corner", [pts], h, bevel=0.0005, mat="M_Brass_Aged")
    obj.location = (0, 0, z0)
    return obj


def build_body():
    parts = []
    body = M.box("body_shell", (BW, BD, BH), loc=(0, 0, BH / 2), mat="M_Wood_Walnut", bevel=0.003, segments=2)
    cav = M.box("cav", (BW - 2 * WALL, BD - 2 * WALL, BH), loc=(0, 0, FLOOR + BH / 2 + 0.001), bevel=0.002,
                segments=1)
    M.boolean(body, cav)
    parts.append(body)
    plinth = M.box("plinth", (BW + 0.008, BD + 0.008, 0.012), loc=(0, 0, 0.006), mat="M_Wood_Walnut",
                   bevel=0.0035, segments=2)
    parts.append(plinth)
    # brass corner guards on the 4 vertical edges, above the plinth
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = corner_L(sx * BW / 2, sy * BD / 2, -sx, -sy, 0.012, 0.026)
            parts.append(c)
    # felt-covered tray insert with a cradle for the battery cell and a finger notch
    tw, td = BW - 2 * WALL - 0.002, BD - 2 * WALL - 0.002
    tray = M.box("tray", (tw, td, TRAY_TOP - FLOOR), loc=(0, 0, (TRAY_TOP + FLOOR) / 2), mat="M_Fabric",
                 bevel=0.002, segments=1)
    cradle = M.cylinder("cradle", 0.0178, 0.066, loc=(0, 0, TRAY_TOP), rot=(0, math.pi / 2, 0), verts=20,
                        mat="M_Fabric", bevel=0.002, segments=1)
    M.boolean(tray, cradle)
    notch = M.cylinder("notch", 0.011, 0.05, loc=(0.045, 0, TRAY_TOP + 0.002), rot=(math.pi / 2, 0, 0), verts=14,
                       mat="M_Fabric", bevel=0.0)
    M.boolean(tray, notch)
    parts.append(tray)
    # knob escutcheons (rosettes) on the front
    for x in GX:
        ros = L.lathe2("rosette", [(0.0175, 0.0), (0.0175, 0.0009), (0.0158, 0.0022), (0.0, 0.0022)], segments=16,
                       mat="M_Brass_Aged", cap_bottom=False)
        ros.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))  # +Z -> -Y
        ros.location = (x, -BD / 2, KZ)
        parts.append(ros)
        # 6 engraved position ticks around each knob (one per wheel step)
        for k in range(6):
            a = math.pi / 2 - k * math.pi / 3
            tk = L.flat_shape("tick", [[(-0.0006, -0.0017), (0.0006, -0.0017), (0.0006, 0.0017), (-0.0006, 0.0017)]],
                              mat="M_Bakelite")
            tk.data.transform(Matrix.Rotation(-(math.pi / 2 - a), 4, "Z"))
            L.to_front(tk, y_back=-BD / 2 - 0.00225, x=x + 0.0132 * math.cos(a), z=KZ + 0.0132 * math.sin(a))
            parts.append(tk)
    # name plate "Nº 7" with two rivets
    np_ = L.curve_solid("nameplate", [L.rounded_rect(0.05, 0.0135, 0.003, 3)], 0.0012, bevel=0.0004,
                        mat="M_Brass_Polished")
    L.to_front(np_, y_back=-BD / 2, z=0.0215)
    txt = L.text_flat("np_txt", "Nº 7", 0.0085, font=L.FONT_SERIF_B, mat="M_Bakelite",
                      rot=L.front_rot(), loc=(0.0, -BD / 2 - 0.00125, 0.0213))
    parts += [np_, txt]
    for dx in (-0.021, 0.021):
        parts.append(L.rivet("np_rv", 0.0014, (dx, -BD / 2 - 0.0012, 0.0215), mat="M_Brass_Aged", segs=6))
    # latch catch on the body front (top centre)
    catch = L.curve_solid("catch", [L.rounded_rect(0.022, 0.011, 0.002, 2)], 0.0016, bevel=0.0005,
                          mat="M_Brass_Aged")
    L.to_front(catch, y_back=-BD / 2, z=BH - 0.0075)
    staple = L.tube("staple", [(-0.004, -BD / 2 - 0.0016, BH - 0.0045), (-0.004, -BD / 2 - 0.0042, BH - 0.0045),
                               (0.004, -BD / 2 - 0.0042, BH - 0.0045), (0.004, -BD / 2 - 0.0016, BH - 0.0045)],
                    0.0009, mat="M_Brass_Polished", bevel_res=0, smooth_path=False)
    parts += [catch, staple]
    # hinges: barrels + body leaves
    for hx in (-0.075, 0.075):
        barrel = M.cylinder("barrel", 0.0029, 0.042, loc=(hx, HINGE[1], HINGE[2]), rot=(0, math.pi / 2, 0),
                            verts=8, mat="M_Brass_Aged", bevel=0.0008, segments=1)
        leaf = M.box("leaf", (0.042, 0.0012, 0.013), loc=(hx, BD / 2 + 0.0006, BH - 0.0075), mat="M_Brass_Aged",
                     bevel=0.0004, segments=1)
        parts += [barrel, leaf]
    return M.join(parts, "box_body")


def build_lid():
    parts = []
    lid = M.box("lid_shell", (BW, BD, LH), loc=(0, 0, BH + LH / 2), mat="M_Wood_Walnut", bevel=0.0045, segments=2)
    parts.append(lid)
    # underside: felt panel + brass plaque "E.S. 1971"
    felt = M.box("lid_felt", (BW - 2 * WALL - 0.004, BD - 2 * WALL - 0.004, 0.0015), loc=(0, 0, BH - 0.0006),
                 mat="M_Fabric", bevel=0.0005, segments=1)
    plq = M.box("plaque", (0.06, 0.022, 0.001), loc=(0, 0.02, BH - 0.0018), mat="M_Brass_Polished", bevel=0.0004,
                segments=1)
    ptxt = L.text_flat("plq_txt", "E. S.", 0.0085, font=L.FONT_SERIF_B, mat="M_Bakelite",
                       rot=(math.pi, 0, 0), loc=(0, 0.02, BH - 0.00235))
    parts += [felt, plq, ptxt]
    # hasp on the lid front
    hasp = L.curve_solid("hasp", [[(-0.009, 0.0), (0.009, 0.0), (0.009, 0.014), (0.003, 0.02), (-0.003, 0.02),
                                   (-0.009, 0.014)]], 0.0015, bevel=0.0005, mat="M_Brass_Aged")
    hasp.data.transform(Matrix.Rotation(math.pi, 4, "Z"))   # point downward
    L.to_front(hasp, y_back=-BD / 2, z=BH + 0.021)
    parts.append(hasp)
    # hinge leaves on the lid
    for hx in (-0.075, 0.075):
        leaf = M.box("lleaf", (0.042, 0.0012, 0.013), loc=(hx, BD / 2 + 0.0006, BH + 0.0075), mat="M_Brass_Aged",
                     bevel=0.0004, segments=1)
        parts.append(leaf)
    # brass top plate with engraved border, corner screws, numerals and target marks
    plate = L.curve_solid("plate", [L.rounded_rect(0.228, 0.148, 0.008, 4)], 0.0025, bevel=0.0007, bevel_res=0,
                          mat="M_Brass_Aged")
    plate.location = (0, 0, BH + LH)
    border = L.flat_shape("border", L.outline_ring(0.214, 0.134, 0.006, 0.0007, 4), mat="M_Bakelite",
                          loc=(0, 0, PT + 0.00005))
    field = L.flat_shape("field", [L.rounded_rect(0.212, 0.090, 0.006, 4, cy=GY - 0.002)], mat="M_Bakelite",
                         loc=(0, 0, PT + 0.00004))
    parts += [plate, border, field]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(L.screw("pscrew", 0.0032, (sx * 0.104, sy * 0.064, PT), normal=(0, 0, 1),
                                 slot_angle=0.4 + sx * 0.5 + sy * 0.2, segs=7))
    for i, x in enumerate(GX):
        num = L.text_flat(f"num{i}", ["I", "II", "III"][i], 0.0095, font=L.FONT_SERIF_B, mat="M_Bakelite",
                          loc=(x, GY - 0.053, PT + 0.00005))
        tri = L.flat_shape(f"target{i}", [[(x, GY + 0.0445), (x + 0.0042, GY + 0.0525), (x - 0.0042, GY + 0.0525)]],
                           mat="M_Enamel_Crimson", loc=(0, 0, PT + 0.00006))
        # arbor boss (the middle one is taller: its wheel runs one deck higher)
        top = G_Z0[i]
        boss = L.lathe2(f"boss{i}", [(0.0095, PT), (0.0095, top - 0.0004), (0.0088, top), (0.0, top)], segments=16,
                        mat="M_Brass_Polished", cap_bottom=False)
        parts += [num, tri, boss]
    obj = M.join(parts, "IA_box_lid")
    M.set_origin(obj, HINGE)
    return obj


def build_gear(i):
    x = GX[i]
    z0 = G_Z0[i]
    gear = L.make_gear(f"g{i}", N_TEETH, R_ROOT, R_TIP, G_T, phase=G_PHASE[i],
                       holes=4, mat="M_Brass_Polished", bevel=0.0006)
    gear.location = (x, GY, z0)
    # raised rim + hub turned on the wheel face
    ptr = L.curve_solid(f"ptr{i}", [L.pointer_outline(0.0265, 0.010)], 0.0008, bevel=0.0002, mat="M_Steel_Dark")
    ptr.location = (x, GY, z0 + G_T + 0.0001)
    hub = L.lathe2(f"hub{i}", [(0.0068, 0.0), (0.0068, 0.0016), (0.0056, 0.0026), (0.0040, 0.0027),
                               (0.0026, 0.0042), (0.0, 0.0046)], segments=12, mat="M_Brass_Polished", cap_bottom=False)
    hub.location = (x, GY, z0 + G_T + 0.0009)
    slot = M.box(f"hslot{i}", (0.0052, 0.0007, 0.0008), loc=(x, GY, z0 + G_T + 0.0009 + 0.0043), mat="M_Steel_Dark",
                 bevel=0.0)
    obj = M.join([gear, ptr, hub, slot], f"IA_gear_{i}")
    M.set_origin(obj, (x, GY, z0 + G_T / 2))
    return obj


def build_knob(i):
    x = GX[i]
    k = L.knurled_knob(f"k{i}", 0.0118, 0.016, ridges=12, mat="M_Brass_Aged", cap_mat="M_Brass_Polished",
                       shaft_r=0.0042, shaft_len=0.003, index_mark=False, simple=True, dome=0.0035)
    k.data.transform(Matrix.Translation((0, 0, 0.003)))
    k.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))   # +Z -> -Y
    k.location = (x, -BD / 2 - 0.0031, KZ)
    k.name = f"IA_knob_{i}"
    k.data.name = k.name
    return k


def build():
    build_body()
    lid = build_lid()
    for i in range(3):
        g = build_gear(i)
        M.set_parent(g, lid)
    for i in range(3):
        build_knob(i)
    anchor = M.empty("battery_anchor", loc=(0.0, 0.0, TRAY_TOP), rot=(0.0, math.pi / 2, 0.0))
    return anchor


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("gear_box")
    if L.want_render():
        L.qa_render("gear_box", (0.36, -0.42, 0.42), (0.0, 0.0, 0.08), lens=50)
        L.qa_render("gear_box_2", (0.0, -0.06, 0.62), (0.0, -0.004, 0.12), lens=60)
        L.qa_render("gear_box_3", (0.05, -0.36, 0.06), (0.0, -0.09, 0.05), lens=60)
        # posed: lid open 80°, wheels at positions A=1, B=3, C=2 (as the puzzle starts)
        lid = M.bpy.data.objects["IA_box_lid"]
        lid.rotation_euler = (math.radians(-80), 0, 0)
        steps = (1, 3, 2)
        signs = (-1, 1, -1)
        for i in range(3):
            M.bpy.data.objects[f"IA_gear_{i}"].rotation_euler = (0, 0, math.radians(60 * steps[i] * signs[i]))
        L.qa_render("gear_box_4", (0.30, -0.40, 0.36), (0.0, 0.02, 0.10), lens=45)


main()
