"""slide_projector.glb — a 1950s lantern-slide projector on a tall iron stand (projection booth).

A black japanned lamp house with brass bands, louvred sides and a lantern chimney with a brass cap;
a brass condenser flange; an open slide stage (two brass guide plates on a bottom rail) through which
a walnut push-through carrier slides across the body; a brass lens board and a long brass objective
with a rack-and-pinion focus knob. The body sits on a tilt head over a telescoping iron column with a
height collar, on a cast tripod with curved legs and felt pads. A cloth cable drops to the floor.

MODEL SPACE (Godot terms; Blender = (x, -z, y)): origin = stand centre on the floor, front +Z.
Placement (-2.35, 0, 2.45), yaw 180: footprint x in [-0.183, 0.183] local -> world [-2.533, -2.167].

PARTS (origin at the pivot, identity rotation at rest)
  IA_slide_gate      the walnut slide carrier across the stage (static tap target).
  slide_gate_mount   empty at the gate centre (0, 1.85, 0.049): a glass_slide.glb with identity stands
                     in the carrier facing +Z; the code rotates it about local +Z by -90 deg x steps.
  IA_slide_rot       knurled brass knob on the carrier's -X end, axis local +X (cosmetic -90 deg x steps).
  IA_slide_lamp      bat-handle toggle on a switch box on the -X side, pivot axis local +X: OFF at rest
                     (leans 15 deg back), ON = +30 deg (15 deg forward).
  lamp_glow          amber peep window + louvre slot backs (M_Glass_Amber), emissive by code.
  lens_origin        empty at the front lens centre (0, 1.85, 0.205); the beam runs along local +Z.

    blender -b --factory-startup -P tools/blender/models/slide_projector.py [-- --no-render] [-- --shot=1,2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_devices2 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "slide_projector"
G = C.G
AXN = (-1.0, 0.0, 0.0)
AXP = (1.0, 0.0, 0.0)
AYP = (0.0, 0.0, 1.0)
AZP = (0.0, -1.0, 0.0)

LY = 1.85                                  # optical axis height
LH = ((-0.105, 1.752, -0.170), (0.105, 1.948, 0.020))   # lamp house box
STAGE_Z0, STAGE_Z1 = 0.026, 0.072          # back face of the rear stage plate / front of the front plate
GATE_Z = 0.049                             # carrier / slide centre plane
CAR_W, CAR_H, CAR_T = 0.300, 0.104, 0.012  # carrier
LENS_FRONT = 0.205
KNOB_X0 = -CAR_W / 2                       # carrier -X end
TOG_P = (-0.1265, 1.790, -0.105)           # toggle pivot (bat axis, 4 mm proud of the switch plate)
TOG_REST = -15.0
WIN_C = (LH[0][0], 1.872, -0.112)          # peep window on the -X face
LEG_AZ = (270.0, 30.0, 150.0)              # legs: back, front-right, front-left (deg from +X toward +Z)
FOOT_R = 0.185


def gbox(name, mn, mx, mat, bevel=0.003, seg=1):
    a, b = G(*mn), G(*mx)
    return A.box_minmax(name, (min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)),
                        (max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)), mat=mat, bevel=bevel, segments=seg)


def rev(name, prof, direction, loc_g, segments=24, mat="M_Brass_Aged", **kw):
    return D.revolve(name, prof, direction=direction, loc=tuple(G(*loc_g)), segments=segments, mat=mat, **kw)


def side(obj, x_face, gy=0.0, gz=0.0, toward=-1.0):
    """Shape drawn in (Godot z, Godot y) offsets, extruded from x_face toward -X (toward=-1) or +X."""
    if toward < 0:
        C.side_plate(obj, x_face, -gz, gy, -1.0)
    else:
        obj.data.transform(Matrix.Scale(-1.0, 4, (1, 0, 0)))     # drawn x -> -x so that it maps to +Godot z
        obj.data.flip_normals()
        C.side_plate(obj, x_face, -gz, gy, 1.0)
    return obj


def front(obj, z_back, gx=0.0, gy=0.0):
    """Shape drawn in (Godot x, Godot y), extruded toward +Z from z_back (front plate)."""
    L.to_front(obj, y_back=-z_back, x=gx, z=gy)
    return obj


# ================================================================ stand (static)
def stand():
    parts = []
    hub_y = 0.17
    parts.append(A.hint(rev("hub", [(0.034, hub_y - 0.035), (0.040, hub_y - 0.020), (0.040, hub_y + 0.012),
                                    (0.030, hub_y + 0.030), (0.024, hub_y + 0.040)], AYP, (0, 0, 0), segments=12,
                            mat="M_Steel_Dark", cap_bottom=True, cap_top=False), 50.0))
    for k, az in enumerate(LEG_AZ):
        a = math.radians(az)
        d = Vector((math.cos(a), 0.0, math.sin(a)))      # Godot horizontal direction (x, -, z)

        def pt(r, y):
            return G(d.x * r, y, d.z * r)
        ctrl = [pt(0.028, hub_y + 0.004), pt(0.075, hub_y - 0.006), pt(0.130, 0.110), pt(0.168, 0.048),
                pt(FOOT_R, 0.022)]
        pts = A.catmull(ctrl, 2)
        rad = A.resample_radii(ctrl, [0.017, 0.015, 0.012, 0.010, 0.0095], 2)
        parts.append(A.tube(f"leg{k}", pts, 0.012, sides=8, radii=rad, mat="M_Steel_Dark"))
        foot = rev(f"pad{k}", [(0.024, 0.0), (0.024, 0.006), (0.019, 0.012), (0.010, 0.020), (0.0, 0.021)], AYP,
                   (d.x * FOOT_R, 0.0, d.z * FOOT_R), segments=10, mat="M_Steel_Dark",
                   band_mats=["M_Felt", "M_Steel_Dark", "M_Steel_Dark", "M_Steel_Dark"], cap_bottom=False)
        parts.append(A.hint(foot, 50.0))
    # outer iron column, height collar with a thumbscrew, inner chrome column, tilt head
    parts.append(A.hint(rev("column", [(0.022, hub_y + 0.030), (0.022, 1.080), (0.030, 1.088), (0.030, 1.128),
                                       (0.020, 1.136), (0.0165, 1.140)], AYP, (0, 0, 0), segments=14,
                            mat="M_Steel_Dark", band_mats=["M_Steel_Dark", "M_Brass_Aged", "M_Brass_Aged",
                                                           "M_Brass_Aged", "M_Brass_Aged"],
                            cap_bottom=False, cap_top=False), 50.0))
    parts.append(A.hint(rev("inner_col", [(0.0165, 1.130), (0.0165, 1.600), (0.024, 1.606), (0.0, 1.610)], AYP,
                            (0, 0, 0), segments=14, mat="M_Chrome", cap_bottom=False), 50.0))
    parts.append(A.hint(rev("thumb_rod", [(0.004, 0.0), (0.004, 0.022)], AXN, (-0.028, 1.108, 0.0), segments=8,
                            cap_bottom=False, cap_top=False), 60.0))
    tk = L.knurled_knob("thumb", 0.011, 0.012, ridges=8, mat="M_Brass_Aged", simple=True, index_mark=False)
    D.aim(tk, AXN)
    tk.location = tuple(G(-0.048, 1.108, 0.0))
    parts.append(A.hint(tk, 30.0))
    # tilt head: yoke cheeks + pivot bolt + wing nut, base plate under the lamp house
    parts.append(gbox("yoke_block", (-0.026, 1.600, -0.026), (0.026, 1.640, 0.026), "M_Steel_Dark", 0.004, 1))
    for s in (-1, 1):
        parts.append(gbox(f"yoke_cheek{s}", (s * 0.030 - 0.004, 1.615, -0.024), (s * 0.030 + 0.004, 1.708, 0.024),
                          "M_Steel_Dark", 0.003, 1))
    parts.append(A.hint(rev("tilt_bolt", [(0.008, -0.040), (0.008, 0.040)], AXP, (0.0, 1.690, 0.0), segments=10,
                            mat="M_Chrome", cap_bottom=True, cap_top=True), 50.0))
    wing = L.curve_solid("wing", [[(-0.022, 0.003), (-0.006, 0.006), (0.006, 0.006), (0.022, 0.003),
                                   (0.022, -0.003), (0.006, -0.006), (-0.006, -0.006), (-0.022, -0.003)]], 0.006,
                         bevel=0.001, mat="M_Brass_Aged")
    side(wing, -0.040, 1.690, 0.0)
    parts.append(wing)
    parts.append(gbox("base_plate", (-0.085, 1.738, -0.160), (0.085, 1.752, 0.125), "M_Lacquer_Black", 0.003, 1))
    parts.append(gbox("plate_block", (-0.025, 1.676, -0.040), (0.025, 1.740, 0.040), "M_Steel_Dark", 0.003, 1))
    # power cable: from the lamp house rear down the column to the floor
    cable = L.tube("cable", [tuple(G(0.060, 1.770, -0.172)), tuple(G(0.050, 1.700, -0.200)), tuple(G(0.030, 1.40, -0.040)),
                             tuple(G(0.030, 0.70, -0.034)), tuple(G(0.040, 0.24, -0.050)), tuple(G(0.060, 0.012, -0.200)),
                             tuple(G(0.070, 0.006, -0.330))], 0.0040, mat="M_Fabric", bevel_res=1, res_u=2)
    for v in cable.data.vertices:
        v.co.z = max(v.co.z, 0.0005)
    parts.append(A.hint(cable, 60.0))
    A.presmooth(parts)
    return M.join(parts, "lantern_stand")


# ================================================================ lamp house + optics (static)
def body():
    (x0, y0, z0), (x1, y1, z1) = LH
    parts = [gbox("lamp_house", (x0, y0, z0), (x1, y1, z1), "M_Lacquer_Black", 0.010, 2)]
    # brass bands round the house
    for z in (z0 + 0.012, z1 - 0.012):
        parts.append(gbox("band", (x0 - 0.0015, y0 - 0.0015, z - 0.006), (x1 + 0.0015, y1 + 0.0015, z + 0.006),
                          "M_Brass_Aged", 0.002, 1))
    # louvre plates on both sides (slots + brass lips); the -X side also carries the peep window
    slots_y = [1.905, 1.922]
    for sgn in (-1, 1):
        xf = x0 if sgn < 0 else x1
        loops = [L.rounded_rect(0.130, 0.044, 0.004, 2)]
        for y in slots_y:
            loops.append(L.rounded_rect(0.112, 0.0075, 0.0030, 2, cy=y - 1.9135))
        lp = L.curve_solid("louvre_plate", loops, 0.003, bevel=0.0, mat="M_Brass_Aged")
        side(lp, xf, 1.9135, -0.075, toward=sgn)
        parts.append(lp)
        for y in slots_y:
            lip = M.box("louvre_lip", (0.0025, 0.116, 0.004), mat="M_Brass_Polished", bevel=0.0, segments=1)
            lip.data.transform(Matrix.Rotation(math.radians(30.0 * -sgn), 4, "Y"))
            lip.location = tuple(G(xf + sgn * 0.0045, y + 0.0045, -0.075))
            parts.append(lip)
    # lantern chimney with a brass cap and pierced vents
    parts.append(A.hint(rev("chimney", [(0.040, 0.0), (0.040, 0.010), (0.030, 0.016), (0.030, 0.090),
                                        (0.048, 0.096), (0.048, 0.104), (0.026, 0.122), (0.010, 0.140),
                                        (0.0, 0.144)], AYP, (0.0, y1 - 0.004, -0.085), segments=14,
                            mat="M_Lacquer_Black", band_mats=["M_Brass_Aged", "M_Brass_Aged", "M_Lacquer_Black",
                                                              "M_Brass_Aged", "M_Brass_Polished", "M_Brass_Aged",
                                                              "M_Brass_Polished", "M_Brass_Polished"],
                            cap_bottom=False), 40.0))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        sl = L.flat_shape("chim_vent", [L.rounded_rect(0.0060, 0.036, 0.0025, 2)], mat="M_Bakelite")
        sl.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
        sl.data.transform(Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        sl.location = (0.0302 * math.cos(a), 0.085 + 0.0302 * math.sin(a), y1 - 0.004 + 0.054)
        parts.append(sl)
    # rear door with a brass knob
    parts.append(gbox("rear_door", (x0 + 0.018, y0 + 0.020, z0 - 0.004), (x1 - 0.018, y1 - 0.020, z0),
                      "M_Lacquer_Black", 0.003, 1))
    parts.append(A.hint(rev("door_knob", [(0.0, 0.0), (0.008, 0.001), (0.010, 0.008), (0.007, 0.014), (0.0, 0.016)],
                            (0, 1, 0), (0.0, 1.850, z0 - 0.004), segments=12, mat="M_Brass_Polished"), 60.0))
    # peep-window bezel on the -X face
    wx, wy, wz = WIN_C
    parts.append(A.hint(rev("win_bezel", [(0.0175, 0.0), (0.0175, 0.0026), (0.0140, 0.0040), (0.0122, 0.0008)],
                            AXN, (wx, wy, wz), segments=14, mat="M_Brass_Polished",
                            cap_bottom=False, cap_top=False), 50.0))
    # switch box for the lamp toggle (-X side, rear)
    px, py, pz = TOG_P
    parts.append(gbox("switch_box", (x0 - 0.016, py - 0.024, pz - 0.022), (x0, py + 0.016, pz + 0.022),
                      "M_Bakelite", 0.003, 2))
    plate = L.curve_solid("switch_plate", [L.rounded_rect(0.034, 0.030, 0.004, 2)], 0.0015, bevel=0.0004,
                          mat="M_Brass_Aged")
    side(plate, x0 - 0.016, py - 0.002, pz)
    parts.append(plate)
    for ang, mat in ((130.0, "M_Enamel_Crimson"), (50.0, "M_Enamel_Green")):
        a = math.radians(ang)
        dot = L.flat_shape("tog_dot", [L.circle(0.0026, 10)], mat=mat)
        side(dot, x0 - 0.0176, py + 0.0115 * math.sin(a), pz + 0.0115 * math.cos(a))
        parts.append(dot)
    # condenser flange on the house front
    parts.append(A.hint(rev("condenser", [(0.068, z1 - 0.004), (0.068, z1 + 0.004), (0.062, z1 + 0.008),
                                          (0.056, STAGE_Z0)], AZP, (0, LY, 0), segments=24, mat="M_Brass_Aged",
                            cap_bottom=False, cap_top=False), 40.0))
    # open slide stage: rear + front guide plates (windows), bottom rail, side posts
    for zb, nm in ((STAGE_Z0, "stage_rear"), (STAGE_Z1 - 0.003, "stage_front")):
        sp = L.curve_solid(nm, [L.rounded_rect(0.124, 0.124, 0.006, 2), L.rounded_rect(0.084, 0.084, 0.004, 1)],
                           0.003, bevel=0.0, mat="M_Brass_Aged")
        front(sp, zb, 0.0, LY)
        parts.append(sp)
    parts.append(gbox("stage_rail", (-0.062, LY - 0.064, STAGE_Z0 + 0.003), (0.062, LY - 0.056, STAGE_Z1 - 0.003),
                      "M_Brass_Aged", 0.0015, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(A.hint(rev("stage_post", [(0.0035, 0.0), (0.0035, STAGE_Z1 - STAGE_Z0)], AZP,
                                    (sx * 0.056, LY + sy * 0.056, STAGE_Z0), segments=8, cap_bottom=False,
                                    cap_top=False), 60.0))
    # lens board + objective tube + focus rack with a knurled pinion knob + front hood
    lb = L.curve_solid("lens_board", [L.rounded_rect(0.110, 0.110, 0.008, 2)], 0.007, bevel=0.0012,
                       mat="M_Lacquer_Black")
    front(lb, STAGE_Z1, 0.0, LY)
    parts.append(lb)
    parts.append(A.hint(rev("lens_flange", [(0.046, STAGE_Z1 + 0.007), (0.046, STAGE_Z1 + 0.012), (0.041, STAGE_Z1 + 0.015),
                                            (0.034, STAGE_Z1 + 0.016)], AZP, (0, LY, 0), segments=24,
                            mat="M_Brass_Aged", cap_bottom=False, cap_top=False), 40.0))
    parts.append(A.hint(rev("objective", [(0.0315, STAGE_Z1 + 0.012), (0.0315, 0.150), (0.0345, 0.153),
                                          (0.0345, 0.192), (0.0368, 0.196), (0.0368, LENS_FRONT - 0.002),
                                          (0.0290, LENS_FRONT), (0.0262, LENS_FRONT - 0.005)],
                            AZP, (0, LY, 0), segments=24, mat="M_Brass_Aged",
                            band_mats=["M_Brass_Aged", "M_Brass_Polished", "M_Brass_Aged", "M_Brass_Polished",
                                       "M_Brass_Polished", "M_Brass_Polished", "M_Lacquer_Black"],
                            cap_bottom=False, cap_top=False), 40.0))
    back = L.flat_shape("lens_back", [L.circle(0.0264, 20)], mat="M_Lacquer_Black")
    front(back, LENS_FRONT - 0.0090)
    back.data.transform(Matrix.Translation((0, 0, LY)))
    parts.append(back)
    parts.append(A.hint(rev("lens_glass", [(0.0263, LENS_FRONT - 0.0060), (0.0180, LENS_FRONT - 0.0030),
                                           (0.0, LENS_FRONT - 0.0018)], AZP, (0, LY, 0), segments=20, mat="M_Glass",
                            cap_bottom=False), 60.0))
    parts.append(gbox("rack", (-0.006, LY - 0.040, STAGE_Z1 + 0.020), (0.006, LY - 0.031, 0.148), "M_Brass_Polished",
                      0.001, 1))
    parts.append(gbox("rack_box", (-0.012, LY - 0.050, 0.098), (0.012, LY - 0.036, 0.122), "M_Brass_Aged", 0.002, 1))
    parts.append(A.hint(rev("pinion_rod", [(0.0032, 0.0), (0.0032, 0.020)], AXN, (-0.012, LY - 0.043, 0.110),
                            segments=8, cap_bottom=False, cap_top=False), 60.0))
    pk = L.knurled_knob("pinion_knob", 0.0105, 0.010, ridges=8, mat="M_Brass_Aged", simple=True, index_mark=False)
    D.aim(pk, AXN)
    pk.location = tuple(G(-0.030, LY - 0.043, 0.110))
    parts.append(A.hint(pk, 30.0))
    # maker's plate on the -X face
    mp = L.curve_solid("maker_plate", [L.rounded_rect(0.070, 0.018, 0.003, 2)], 0.0012, bevel=0.0003,
                       mat="M_Brass_Polished")
    side(mp, x0, 1.800, -0.045)
    parts.append(mp)
    t = L.text_flat("maker_txt", "MERIDIAN", 0.0092, font=L.FONT_COND_B, res=1, mat="M_Lacquer_Black", spacing=1.1)
    L.recentre_xy(t)
    side(t, x0 - 0.00125, 1.800, -0.045)
    parts.append(t)
    A.presmooth(parts)
    house = M.join(parts, "lantern_body")
    # glow: peep window + a strip behind every louvre slot (both sides)
    glow = []
    g0 = L.flat_shape("glow_win", [L.circle(0.0124, 16)], mat="M_Glass_Amber")
    side(g0, wx - 0.0004, wy, wz)
    glow.append(g0)
    for sgn in (-1, 1):
        xf = x0 if sgn < 0 else x1
        for y in slots_y:
            s = L.flat_shape("glow_slot", [L.rounded_rect(0.114, 0.009, 0.002, 1)], mat="M_Glass_Amber")
            side(s, xf + sgn * 0.0004, y, -0.075, toward=sgn)
            glow.append(s)
    g = M.join(glow, "lamp_glow")
    M.set_origin(g, tuple(G(wx, wy, wz)))
    return house, g


# ================================================================ interactive parts
def carrier():
    """Walnut push-through carrier with a rebated square window, brass end caps and a finger grip."""
    outer = L.rounded_rect(CAR_W, CAR_H, 0.008, 2)
    back = L.curve_solid("carrier_back", [outer, L.rounded_rect(0.072, 0.072, 0.003, 1)], 0.004, bevel=0.0,
                         mat="M_Wood_Walnut")
    front(back, GATE_Z - CAR_T / 2, 0.0, LY)                     # z 0.043..0.047: the lip the slide rests on
    fr = L.curve_solid("carrier_front", [outer, L.rounded_rect(0.084, 0.084, 0.003, 1)], CAR_T - 0.004,
                       bevel=0.0010, mat="M_Wood_Walnut", drop_bottom=True)
    front(fr, GATE_Z - CAR_T / 2 + 0.004, 0.0, LY)               # z 0.047..0.055: the 0.084 rebate
    parts = [back, fr]
    # brass rebate liner (where the 0.082 slide sits) on the front face
    reb = L.curve_solid("carrier_rebate", [L.rounded_rect(0.090, 0.090, 0.004, 1), L.rounded_rect(0.084, 0.084, 0.003, 1)],
                        0.0015, bevel=0.0, mat="M_Brass_Aged", drop_bottom=True)
    front(reb, GATE_Z + CAR_T / 2, 0.0, LY)
    parts.append(reb)
    for sx in (-1, 1):       # brass end caps
        xa, xb = sorted((sx * (CAR_W / 2 + 0.0005), sx * (CAR_W / 2 - 0.010)))
        parts.append(gbox("carrier_cap", (xa, LY - CAR_H / 2 - 0.001, GATE_Z - CAR_T / 2 - 0.001),
                          (xb, LY + CAR_H / 2 + 0.001, GATE_Z + CAR_T / 2 + 0.001), "M_Brass_Aged", 0.0015, 1))
    # finger grip groove marks on the +X end (front face)
    for k in range(3):
        parts.append(gbox("grip", (0.112 + 0.008 * k, LY - 0.030, GATE_Z + CAR_T / 2), (0.1145 + 0.008 * k, LY + 0.030,
                                                                                       GATE_Z + CAR_T / 2 + 0.0008),
                          "M_Lacquer_Black", 0.0, 1))
    A.presmooth(parts)
    o = M.join(parts, "IA_slide_gate")
    M.set_origin(o, tuple(G(0.0, LY, GATE_Z)))
    return o


def rot_knob():
    shaft = rev("rot_shaft", [(0.0040, 0.0), (0.0040, 0.008)], AXN, (KNOB_X0 - 0.0005, LY, GATE_Z), segments=8,
                cap_bottom=False, cap_top=False)
    k = L.knurled_knob("rot_grip", 0.0125, 0.013, ridges=12, mat="M_Brass_Aged", cap_mat="M_Brass_Polished",
                       index_mark=False, simple=True)
    D.aim(k, AXN)
    k.location = tuple(G(KNOB_X0 - 0.007, LY, GATE_Z))
    # white index line on the knob face (shows the rotation)
    mark = L.flat_shape("rot_mark", [L.rounded_rect(0.0012, 0.0085, 0.0003, 1, cy=0.0045)], mat="M_Enamel_White")
    side(mark, KNOB_X0 - 0.007 - 0.0133, LY, GATE_Z)
    parts = [A.hint(shaft, 60.0), A.hint(k, 30.0), mark]
    A.presmooth(parts)
    o = M.join(parts, "IA_slide_rot")
    M.set_origin(o, tuple(G(KNOB_X0 - 0.007, LY, GATE_Z)))
    return o


def toggle():
    px, py, pz = TOG_P
    boss = rev("tog_boss", [(0.0062, 0.0), (0.0062, 0.0050), (0.0050, 0.0068), (0.0, 0.0072)], AXN,
               (px + 0.0040, py, pz), segments=12, mat="M_Chrome", cap_bottom=False)
    bat = rev("tog_bat", [(0.0, -0.002), (0.0024, 0.0), (0.0021, 0.022), (0.0034, 0.030), (0.0036, 0.034),
                          (0.0, 0.0365)], AYP, (px, py, pz), segments=10, mat="M_Chrome")
    parts = [A.hint(boss, 50.0), A.hint(bat, 60.0)]
    A.presmooth(parts)
    o = M.join(parts, "IA_slide_lamp")
    P = G(px, py, pz)
    o.data.transform(Matrix.Translation(P) @ Matrix.Rotation(math.radians(TOG_REST), 4, "X") @ Matrix.Translation(-P))
    M.set_origin(o, tuple(P))
    return o


# ================================================================ build / verify
def build():
    M.reset_scene()
    A.prepare_materials()
    C.ensure_materials()
    out = dict(stand=stand())
    out["body"], out["glow"] = body()
    out["gate"] = carrier()
    out["rot"] = rot_knob()
    out["toggle"] = toggle()
    out["mount"] = M.empty("slide_gate_mount", loc=tuple(G(0.0, LY, GATE_Z)))
    out["lens"] = M.empty("lens_origin", loc=tuple(G(0.0, LY, LENS_FRONT)))
    A.finalize_uv()
    A.grain_uv(out["gate"])
    for k in ("stand", "body", "gate", "rot", "toggle", "glow"):
        print(f"[{NAME}]   {k:7s} {A.tris(out[k])}")
    print(f"[{NAME}] tris TOTAL={M.tri_count()}")
    return out


def verify() -> bool:
    exp = {
        "lantern_stand": dict(parent=None, pos=(0, 0, 0)),
        "lantern_body": dict(parent=None, pos=(0, 0, 0)),
        "IA_slide_gate": dict(parent=None, pos=(0.0, LY, GATE_Z)),
        "slide_gate_mount": dict(parent=None, pos=(0.0, LY, GATE_Z)),
        "IA_slide_rot": dict(parent=None, pos=(KNOB_X0 - 0.007, LY, GATE_Z)),
        "IA_slide_lamp": dict(parent=None, pos=TOG_P),
        "lamp_glow": dict(parent=None, pos=WIN_C),
        "lens_origin": dict(parent=None, pos=(0.0, LY, LENS_FRONT)),
    }
    return C.verify_glb(NAME, exp, 5000)


# ================================================================ QA
POS, YAW = (-2.35, 0.0, 2.45), 180.0


def world_of(local):
    x, y, z = local
    return (POS[0] - x, y, POS[2] - z)


def lamp(parts, on):
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA_slbeam")]:
        bpy.data.objects.remove(o, do_unlink=True)
    if not on:
        parts["glow"].material_slots[0].material = bpy.data.materials["M_Glass_Amber"]
        return
    C.qa_emit(parts["glow"], "FFF1D6", 9.0, base="FFD49A")
    M.refresh()
    lens = parts["lens"].matrix_world.translation
    spot = A.qa_light("slbeam_spot", "SPOT", tuple(lens), 110.0, "FFF6E6", size=0.01, target=tuple(G(-2.5, 1.9, -3.43)),
                      spot=math.radians(18.0))
    spot.data.spot_blend = 0.25
    spot.visible_glossy = False          # no highlight of the QA lamp on the window glass


def main():
    args = M.main_guard()
    parts = build()
    A.export_lean(NAME)
    ok = verify()
    print(f"[{NAME}] verify {'OK' if ok else 'FAILED'}")
    lens_w = world_of((0.0, LY, LENS_FRONT))
    for inset in (0.0, 0.04):
        C.beam_clearance(lens_w, aperture_r=0.027, inset=inset, label=f"slide beam (frame inset {inset})")
    lo, hi = D.bounds([parts["stand"], parts["body"], parts["gate"], parts["rot"], parts["toggle"]])
    print(f"[{NAME}] footprint local x [{lo.x:.3f}, {hi.x:.3f}] -> world x [{POS[0] - hi.x:.3f}, {POS[0] - lo.x:.3f}]; "
          f"local z [{-hi.y:.3f}, {-lo.y:.3f}] -> world z [{POS[2] + lo.y:.3f}, {POS[2] + hi.y:.3f}]")
    if "--no-render" in args:
        return
    want = set()
    for a in args:
        if a.startswith("--shot="):
            want |= set(a.split("=", 1)[1].split(","))

    def on(k):
        return not want or k in want
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    C.place(roots, POS, YAW)
    C.qa_room()
    C.qa_lights(booth_bulb=60.0, hall=60.0, fill=25.0)
    C.import_model("film_projector", (-2.9, 0.0, 2.65), 180.0)
    C.import_model("booth_door", (-1.55, 0.0, 2.0), 180.0)
    C.import_model("projection_screen", (-2.5, 0.0, -3.5), 0.0)
    objs, real = C.qa_item("glass_slide", parts["mount"], C.proxy_glass_slide)
    if real:
        # glass_slide.glb (group D2) lies flat, front +Y; the gate needs it standing, front +Z (contract):
        # +90 deg about X (what the item / the spawn code must provide, see docs/models/ch2_devices2.md)
        objs[0].matrix_world = parts["mount"].matrix_world @ Matrix.Rotation(math.pi / 2, 4, "X")
    C.qa_glass_tweak()
    parts["toggle"].rotation_euler = C.blender_rot_about_godot("X", 30.0)
    lamp(parts, True)
    if on("1"):    # in-game slide_projector view: slide in, lamp on
        C.render(NAME, (-1.75, 1.95, 2.95), (-2.35, 1.8, 2.45), 44.0, res=(960, 540))
    if on("2"):    # hero: three-quarter from the operator side, whole stand
        C.render(NAME + "_2", (-1.55, 1.55, 3.30), (-2.36, 1.05, 2.45), 50.0, res=(720, 900))
    if on("3"):    # stage close-up: carrier, slide, rotation knob, toggle
        C.render(NAME + "_3", (-1.98, 1.98, 2.72), (-2.30, 1.84, 2.42), 36.0, res=(960, 640))
    if on("4"):    # rest: lamp off, no slide
        parts["toggle"].rotation_euler = (0.0, 0.0, 0.0)
        lamp(parts, False)
        for o in bpy.context.scene.objects:
            if o.name.startswith("QA_item_") or o.name.startswith("QA_proxy_") or o.name.startswith("QA_slide"):
                o.hide_render = True
        C.render(NAME + "_4", (-1.75, 1.95, 2.95), (-2.35, 1.8, 2.45), 44.0, res=(960, 540))


main()
