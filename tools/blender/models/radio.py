"""radio.glb — 1950s walnut valve radio on the Lab 7 bench (tunes Strand's beacon on the 41 m band).

Walnut cabinet 0.42 x 0.28 x 0.22 m with a rounded top front edge, a recessed fascia framed by a brass
inlay line, tan grille cloth behind brass bars with a MERIDIAN badge, a curved glass dial window (with
real glass thickness) over the printed dial, a gold right-hand panel carrying the magic eye and the big
knurled tuning knob, a volume knob on the right side, brass-capped feet and a mains cord at the back.
A hatch in the top-back opens onto the valve chassis: two valves in place and one empty octal socket.

Model space: front = Blender -Y (Godot +Z), base on Z = 0, origin at the base centre.
Parts (separate objects, origin at the pivot, identity rotation at rest):
  radio_dial      flat quad, M_Decal_RadioDial, planar UV 0..1 (u left->right, v bottom->top), 1024:256
  dial_needle     red needle; slides along model X; at rest at u = 0.06 of the dial
  IA_tuning_knob  big knurled knob; origin on its axis at the fascia; rotates about Godot +Z
  IA_radio_hatch  top-back hatch; origin on the hinge axis (back edge); opens -70 deg about Godot +X
  IA_valve_socket empty octal socket on the chassis (origin at its top centre = valve seat)
  valve_installed glass valve standing in the socket (hide until installed)
  magic_eye       green indicator glass (M_Emissive_MagicEye)
    blender -b --factory-startup -P tools/blender/models/radio.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

W, H, DP = 0.42, 0.28, 0.22
Z0 = 0.010                    # cabinet underside (feet below)
YF, YB = -DP / 2, DP / 2      # front / back planes
RECESS = (-0.190, 0.190, 0.026, 0.234)     # fascia recess x0, x1, z0, z1
Y_REC = YF + 0.008            # fascia (recess back) plane
DIAL_W, DIAL_H = 0.288, 0.072 # decal 1024:256
DIAL_Z = 0.191                # dial centre height
Y_DIAL = YF + 0.0195          # decal plane (in the dial pocket)
NEEDLE_U = 0.06
GRILLE = (-0.182, 0.074, 0.034, 0.140)
COL_X = 0.139                 # right column centre
EYE_Z, KNOB_Z = 0.127, 0.070
HATCH = (-0.100, 0.100, -0.024, 0.0905)     # x0, x1, y0, y1 of the top opening
HINGE = (0.0, 0.0905, H)
SPLASH_Y = 0.255              # lab-bench splashback face, radio-local (radio at bench-local y = +0.05)
CHASSIS_Z = 0.140
SOCKET = (0.020, 0.034)
SOCK_TOP = CHASSIS_Z + 0.0075


def build_cabinet():
    prof = L.rrect4(DP, H - Z0, radii=(0.006, 0.014, 0.042, 0.009), n=6, cy=Z0 + (H - Z0) / 2)
    cab = L.curve_solid("cabinet", [prof], W, bevel=0.003, bevel_res=1, mat="M_Wood_Walnut")
    L.profile_yz(cab, -W / 2)
    x0, x1, z0, z1 = RECESS
    cuts = [
        M.box("c_recess", (x1 - x0, 0.03, z1 - z0), loc=((x0 + x1) / 2, Y_REC - 0.015, (z0 + z1) / 2), bevel=0.004,
              segments=2),
        M.box("c_dial", (0.300, 0.03, 0.078), loc=(0.0, Y_DIAL - 0.0135, DIAL_Z), bevel=0.003, segments=1),
        M.box("c_cavity", (0.25, 0.145, H - 0.013 - CHASSIS_Z), loc=(0.0, 0.0265, (H - 0.013 + CHASSIS_Z) / 2),
              bevel=0.0),
        M.box("c_hatch", (HATCH[1] - HATCH[0], HATCH[3] - HATCH[2], 0.03),
              loc=(0.0, (HATCH[2] + HATCH[3]) / 2, H), bevel=0.0015, segments=1),
        M.box("c_back", (0.36, 0.03, 0.215), loc=(0.0, YB + 0.0090, 0.13), bevel=0.003, segments=1),
    ]
    for c in cuts:
        M.boolean(cab, c)
    return cab


def build_body():
    parts = [build_cabinet()]
    x0, x1, z0, z1 = RECESS
    # brass inlay line around the fascia
    ring = L.outline_ring(x1 - x0 + 0.020, z1 - z0 + 0.020, 0.010, 0.0016, 4)
    inl = L.flat_shape("inlay", ring, mat="M_Brass_Polished")
    L.to_front(inl, y_back=YF - 0.00006, z=(z0 + z1) / 2)
    parts.append(inl)
    # ---- grille: cloth, brass frame, four brass bars, badge
    gx0, gx1, gz0, gz1 = GRILLE
    gw, gh, gcx, gcz = gx1 - gx0, gz1 - gz0, (gx0 + gx1) / 2, (gz0 + gz1) / 2
    cloth = L.plane("grille_cloth", gw, gh, loc=(gcx, Y_REC - 0.0004, gcz), mat="M_Grille_Fabric")
    frame = L.curve_solid("gframe", [L.rounded_rect(gw + 0.008, gh + 0.008, 0.008, 3),
                                     L.rounded_rect(gw - 0.004, gh - 0.004, 0.005, 3)], 0.004, bevel=0.0012,
                          mat="M_Brass_Aged")
    L.to_front(frame, y_back=Y_REC, x=gcx, z=gcz)
    parts += [cloth, frame]
    for k in range(4):
        bz = gz0 + gh * (k + 1) / 5.0
        bar = L.lathe2("gbar", [(0.0, 0.0), (0.0018, 0.0), (0.0024, 0.006), (0.0024, gw - 0.006), (0.0018, gw),
                                (0.0, gw)], segments=6, mat="M_Brass_Polished")
        bar.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        bar.location = (gx0, Y_REC - 0.0028, bz)
        parts.append(bar)
    badge = L.curve_solid("badge", [L.rounded_rect(0.084, 0.020, 0.0045, 3)], 0.0028, bevel=0.0009,
                          mat="M_Brass_Polished")
    L.to_front(badge, y_back=Y_REC - 0.0052, x=gcx, z=gcz)
    btxt = D.text("badge_txt", "MERIDIAN", 0.0115, font=D.FONT_DISPLAY, mat="M_Bakelite", res=0, spacing=1.1,
                  loc=(gcx, Y_REC - 0.0081, gcz - 0.0003), rot=L.front_rot())
    parts += [badge, btxt]
    # ---- dial: bezel, curved glass with thickness, guide rod (decal + needle are separate)
    bez = L.curve_solid("dial_bezel", [L.rounded_rect(0.318, 0.090, 0.014, 4),
                                       L.rounded_rect(0.296, 0.072, 0.007, 3)], 0.0045, bevel=0.0014,
                        bevel_res=0, mat="M_Brass_Polished")
    L.to_front(bez, y_back=Y_REC, z=DIAL_Z)
    parts.append(bez)
    rod = L.lathe2("guide", [(0.0012, 0.0), (0.0012, 0.296)], segments=6, mat="M_Chrome", cap_bottom=False,
                   cap_top=False)
    rod.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    rod.location = (-0.148, Y_DIAL - 0.0030, DIAL_Z - DIAL_H / 2 + 0.0035)
    parts.append(rod)
    # ---- right column: gold panel, magic-eye bezel + cap, knob escutcheon with ticks
    panel = L.curve_solid("panel", [L.rounded_rect(0.090, 0.106, 0.008, 4)], 0.0018, bevel=0.0006,
                          mat="M_Brass_Aged")
    L.to_front(panel, y_back=Y_REC, x=COL_X, z=(EYE_Z + KNOB_Z) / 2 - 0.004)
    parts.append(panel)
    yp = Y_REC - 0.0018
    eb = D.revolve("eye_bezel", [(0.0172, 0.0), (0.0172, 0.0018), (0.0158, 0.0035), (0.0118, 0.0035),
                                 (0.0118, -0.002)], direction=(0, -1, 0), loc=(COL_X, yp, EYE_Z), segments=16,
                   mat="M_Brass_Polished", cap_bottom=False, cap_top=False)
    cap = D.revolve("eye_cap", [(0.0042, 0.0), (0.0042, 0.0042), (0.0030, 0.0055), (0.0, 0.0058)],
                    direction=(0, -1, 0), loc=(COL_X, yp, EYE_Z), segments=10, mat="M_Bakelite", cap_bottom=False)
    parts += [eb, cap]
    esc = D.revolve("escutcheon", [(0.031, 0.0), (0.040, 0.0), (0.040, 0.0012), (0.0385, 0.0022), (0.031, 0.0022)],
                    direction=(0, -1, 0), loc=(COL_X, yp, KNOB_Z), segments=24, mat="M_Brass_Polished",
                    cap_bottom=False, cap_top=False)
    parts.append(esc)
    for k in range(11):              # tuning scale ticks from 7:30 to 4:30 o'clock
        a = math.radians(225.0 - k * 27.0)
        ln = 0.0042 if k % 5 == 0 else 0.0026
        tk = L.flat_shape("ktick", [L.rounded_rect(0.0009, ln, 0.0002, 1)], mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        rr = 0.0372 - ln / 2
        L.to_front(tk, y_back=yp - 0.00225, x=COL_X + rr * math.cos(a), z=KNOB_Z + rr * math.sin(a))
        parts.append(tk)
    # ---- side volume knob (right side, front)
    vk = L.lathe2("vknob", [(0.0, 0.0), (0.016, 0.0), (0.0165, 0.002, "k"), (0.0165, 0.013, "k"),
                            (0.0135, 0.0165), (0.0, 0.0172)], segments=18, knurl=0.0013, mat="M_Bakelite",
                  band_mats=[None, None, None, "M_Brass_Polished", "M_Brass_Polished"], cap_bottom=False)
    D.aim(vk, (1, 0, 0))
    vk.location = (W / 2, -0.045, 0.082)
    parts.append(vk)
    # ---- top: hinge knuckles on the cabinet behind the hatch
    for hx in (-0.062, 0.062):
        kn = D.revolve("knuckle", [(0.0, -0.011), (0.0032, -0.0105), (0.0032, 0.0105), (0.0, 0.011)],
                       direction=(1, 0, 0), loc=(hx, HINGE[1] + 0.0012, H + 0.0006), segments=8,
                       mat="M_Brass_Aged")
        parts.append(kn)
    # ---- chassis under the hatch: plate, static valves, transformer can, capacitor
    plate = M.box("chassis", (0.248, 0.143, 0.003), loc=(0.0, 0.0265, CHASSIS_Z + 0.0015), mat="M_Steel_Painted",
                  bevel=0.0)
    parts.append(plate)
    for (vx, vy, s) in ((-0.056, 0.010, 1.0), (-0.056, 0.058, 0.82)):
        sk = D.revolve("vsock", [(0.0, 0.0), (0.0175 * s, 0.0), (0.0175 * s, 0.006), (0.0, 0.006)],
                       direction=(0, 0, 1), loc=(vx, vy, CHASSIS_Z + 0.003), segments=12, mat="M_Bakelite")
        v = D.valve("static_valve", (0, 0, 0), quality="far")
        v.data.transform(Matrix.Diagonal((s, s, s, 1.0)))
        v.location = (vx, vy, CHASSIS_Z + 0.009)
        parts += [sk, v]
    can = L.lathe2("xcan", [(0.0, 0.0), (0.020, 0.0), (0.020, 0.052), (0.0185, 0.0555), (0.0, 0.056)],
                   segments=14, mat="M_Chrome", cap_bottom=False)
    can.location = (0.080, 0.060, CHASSIS_Z + 0.003)
    cap2 = L.lathe2("ecap", [(0.0, 0.0), (0.011, 0.0), (0.011, 0.034), (0.0095, 0.036), (0.0, 0.0365)],
                    segments=10, mat="M_Copper", cap_bottom=False)
    cap2.location = (0.082, 0.004, CHASSIS_Z + 0.003)
    parts += [can, cap2]
    # ---- back board with vent slots, mains cord through a grommet
    board = M.box("backboard", (0.356, 0.004, 0.211), loc=(0.0, YB - 0.004, 0.13), mat="M_Wood_Panel", bevel=0.001,
                  segments=1)
    parts.append(board)
    for k in range(6):
        sl = L.flat_shape("slot", [L.rounded_rect(0.20, 0.006, 0.0029, 3)], mat="M_Bakelite")
        sl.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))   # face +Y
        sl.location = (0.0, YB - 0.00195, 0.150 + k * 0.014)
        parts.append(sl)
    for (sx, sz) in ((-1, 0.04), (1, 0.04), (-1, 0.225), (1, 0.225)):
        parts.append(L.rivet("bscrew", 0.0035, (sx * 0.168, YB - 0.002, sz), normal=(0, 1, 0), segs=6))
    grom = D.revolve("grommet", [(0.0, 0.0), (0.0065, 0.0), (0.0065, 0.004), (0.0045, 0.0055), (0.0, 0.0055)],
                     direction=(0, 1, 0), loc=(-0.12, YB - 0.006, 0.055), segments=10, mat="M_Rubber")
    # mains cord to a round bakelite socket screwed to the bench splashback (radio-local y = 0.255)
    sx_, sz_ = -0.150, 0.070
    sock = D.revolve("wsocket", [(0.026, 0.0), (0.026, 0.006), (0.023, 0.013), (0.019, 0.016), (0.0, 0.0165)],
                     direction=(0, -1, 0), loc=(sx_, SPLASH_Y, sz_), segments=14, mat="M_Bakelite", cap_bottom=False)
    plug = D.revolve("plug", [(0.0, 0.0), (0.0155, 0.0), (0.0165, 0.004), (0.0150, 0.022), (0.0100, 0.030),
                              (0.0050, 0.034), (0.0, 0.034)], direction=(0, -1, 0), loc=(sx_, SPLASH_Y - 0.0165, sz_),
                     segments=12, mat="M_Bakelite")
    p_out = (sx_, SPLASH_Y - 0.052, sz_)
    cord = L.tube("cord", [(-0.12, YB - 0.001, 0.055), (-0.124, YB + 0.035, 0.040), (-0.132, YB + 0.075, 0.0075),
                           (-0.142, YB + 0.112, 0.0060), (sx_, YB + 0.128, 0.022), p_out], 0.0032, mat="M_Fabric",
                  bevel_res=1, res_u=3)
    parts += [sock, plug]
    parts += [grom, cord]
    # ---- feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(L.lathe2("foot", [(0.0, 0.0), (0.0115, 0.0), (0.0125, 0.003), (0.0095, 0.0085),
                                           (0.0075, Z0 + 0.001)], segments=8, cap_top=False,
                                  mat="M_Brass_Aged"))
            parts[-1].location = (sx * 0.172, sy * 0.082, 0.0)
    return M.join(parts, "radio_body")


def build_glass():
    """Curved dial glass (bulges 6 mm toward the viewer), 1.5 mm thick, edges hidden under the bezel."""
    gw, z0, z1 = 0.302, DIAL_Z - 0.039, DIAL_Z + 0.039
    n = 10
    verts, faces = [], []
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        t = (z - DIAL_Z) / ((z1 - z0) / 2)
        y = Y_REC + 0.0015 - 0.0065 * (1.0 - t * t)
        verts += [(-gw / 2, y, z), (gw / 2, y, z)]
    for i in range(n):
        a, b = 2 * i, 2 * i + 2
        faces.append((a, a + 1, b + 1, b))
    g = D.mesh("dial_glass", verts, faces, mat="M_Glass")
    if g.data.polygons[n // 2].normal.y > 0:
        g.data.flip_normals()
    D.solidify(g, 0.0015, offset=-1.0)
    return g


def build_dial():
    dial = L.plane("radio_dial", DIAL_W, DIAL_H, loc=(0.0, Y_DIAL, DIAL_Z), mat="M_Decal_RadioDial")
    M.apply_transform(dial)           # identity transform: mesh-local X == model X (the needle slides on it)
    x = -DIAL_W / 2 + NEEDLE_U * DIAL_W
    yb = Y_DIAL - 0.0030
    zb = DIAL_Z - DIAL_H / 2 + 0.0035
    blade = L.curve_solid("needle_blade", [[(-0.0008, 0.0), (0.0008, 0.0), (0.0005, 0.064), (-0.0005, 0.064)]],
                          0.0008, bevel=0.0, mat="M_Enamel_Crimson")
    L.to_front(blade, y_back=yb + 0.0004, x=x, z=zb)
    carriage = M.box("needle_car", (0.0065, 0.0045, 0.0055), loc=(x, yb, zb), mat="M_Bakelite", bevel=0.0008,
                     segments=1)
    needle = M.join([blade, carriage], "dial_needle")
    M.set_origin(needle, (x, yb, DIAL_Z))
    return dial, needle


def build_knob():
    prof = [(0.0, 0.0), (0.0315, 0.0), (0.0335, 0.0018), (0.0335, 0.0048), (0.0295, 0.0062),
            (0.0285, 0.0080, "k"), (0.0285, 0.0215, "k"), (0.0262, 0.0245), (0.0205, 0.0258), (0.0, 0.0260)]
    bands = ["M_Brass_Polished"] * 4 + ["M_Bakelite"] * 3 + ["M_Brass_Polished", "M_Brass_Polished"]
    knob = L.lathe2("tknob", prof, segments=36, knurl=0.0016, band_mats=bands, mat="M_Bakelite", cap_bottom=False)
    mark = L.flat_shape("tmark", [L.rounded_rect(0.0016, 0.013, 0.0007, 2, cy=0.0115)], mat="M_Enamel_Cream",
                        loc=(0, 0, 0.02605))
    skirt_mark = L.flat_shape("tmark2", [[(-0.0018, 0.0300), (0.0018, 0.0300), (0.0, 0.0333)]], mat="M_Bakelite",
                              loc=(0, 0, 0.0049))
    obj = M.join([knob, mark, skirt_mark], "IA_tuning_knob")
    D.aim(obj, (0, -1, 0))           # lathe +Z -> front; local +Y (mark) -> up
    obj.location = (COL_X, Y_REC - 0.0040, KNOB_Z)
    return obj


def build_eye():
    eye = D.revolve("magic_eye", [(0.0118, 0.0), (0.0108, 0.0012), (0.0060, 0.0024), (0.0, 0.0028)],
                    direction=(0, -1, 0), loc=(COL_X, Y_REC - 0.0018, EYE_Z), segments=20, mat="M_Emissive_MagicEye")
    M.set_origin(eye, (COL_X, Y_REC - 0.0018, EYE_Z))
    return eye


def build_hatch():
    x0, x1, y0, y1 = HATCH
    c = 0.0008
    hatch = M.box("hatch_panel", (x1 - x0 - 2 * c, y1 - y0 - 2 * c, 0.010), loc=(0.0, (y0 + y1) / 2, H - 0.005),
                  mat="M_Wood_Walnut", bevel=0.0018, segments=2)
    parts = [hatch]
    for k in range(5):
        sl = L.flat_shape("hvent", [L.rounded_rect(0.120, 0.0042, 0.0020, 3)], mat="M_Bakelite",
                          loc=(0.0, y0 + 0.034 + k * 0.0115, H + 0.00005))
        parts.append(sl)
    pull = D.revolve("pull", [(0.0, -0.016), (0.0045, -0.0145), (0.0045, 0.0145), (0.0, 0.016)],
                     direction=(1, 0, 0), loc=(0.0, y0 + 0.008, H + 0.0006), segments=8, mat="M_Brass_Polished")
    parts.append(pull)
    for hx in (-0.040, 0.040):
        kn = D.revolve("hknuckle", [(0.0, -0.011), (0.0032, -0.0105), (0.0032, 0.0105), (0.0, 0.011)],
                       direction=(1, 0, 0), loc=(hx, HINGE[1] + 0.0012, H + 0.0006), segments=8,
                       mat="M_Brass_Aged")
        leaf = M.box("hleaf", (0.020, 0.012, 0.0010), loc=(hx, HINGE[1] - 0.006, H + 0.0004), mat="M_Brass_Aged",
                     bevel=0.0)
        parts += [kn, leaf]
    obj = M.join(parts, "IA_radio_hatch")
    M.set_origin(obj, HINGE)
    return obj


def build_socket():
    sx, sy = SOCKET
    z = CHASSIS_Z + 0.003
    body = D.revolve("osock", [(0.0, 0.0), (0.0185, 0.0), (0.0185, 0.0035), (0.0170, 0.0045), (0.0, 0.0045)],
                     direction=(0, 0, 1), loc=(sx, sy, z), segments=16, mat="M_Bakelite")
    saddle = L.curve_solid("saddle", [L.rounded_rect(0.056, 0.024, 0.008, 2), L.circle(0.0186, 12)], 0.0012,
                           bevel=0.0003, mat="M_Brass_Aged")
    saddle.location = (sx, sy, z)
    parts = [body, saddle]
    for dx in (-0.0235, 0.0235):
        parts.append(L.rivet("srivet", 0.0022, (sx + dx, sy, z + 0.0012), normal=(0, 0, 1), segs=6))
    for k in range(8):               # pin holes + keyway
        a = math.tau * k / 8 + math.tau / 16
        parts.append(L.flat_shape("hole", [L.circle(0.0016, 6, cx=0.0087 * math.cos(a), cy=0.0087 * math.sin(a))],
                                  mat="M_Steel_Dark", loc=(sx, sy, SOCK_TOP + 0.00005)))
    parts.append(L.flat_shape("keyhole", [L.circle(0.0046, 10)], mat="M_Steel_Dark", loc=(sx, sy, SOCK_TOP + 0.00005)))
    obj = M.join(parts, "IA_valve_socket")
    M.set_origin(obj, (sx, sy, SOCK_TOP))
    return obj


def build():
    D.ensure_materials()
    build_body()
    build_glass()
    build_dial()
    build_knob()
    build_eye()
    build_hatch()
    build_socket()
    D.valve("valve_installed", (SOCKET[0], SOCKET[1], SOCK_TOP), quality="mid")


def decal_uvs():
    M.planar_uv(M.bpy.data.objects["radio_dial"], axis="Y", material_prefix="M_Decal_")


def main():
    M.reset_scene()
    build()
    L.finish("radio", decals=[decal_uvs])
    D.describe("radio")
    if D.want_render():
        D.qa_tweak()
        D.shot("radio", (0.52, -0.72, 0.46), (0.0, 0.0, 0.13), lens=45)
        D.shot("radio_2", (0.0, -0.62, 0.20), (0.0, 0.0, 0.14), lens=55)
        # hatch open, valve hidden (the puzzle state), seen from above-back
        hatch = M.bpy.data.objects["IA_radio_hatch"]
        hatch.rotation_euler = (math.radians(-70.0), 0.0, 0.0)
        M.bpy.data.objects["valve_installed"].hide_render = True
        D.shot("radio_3", (0.10, -0.30, 0.62), (0.010, 0.030, 0.17), lens=40)
        # tuned to the 41 m band with the valve installed
        M.bpy.data.objects["valve_installed"].hide_render = False
        needle = M.bpy.data.objects["dial_needle"]
        needle.location.x += (0.06 + 0.88 * 36 / 100.0 - NEEDLE_U) * DIAL_W
        D.shot("radio_4", (0.26, -0.42, 0.62), (0.0, 0.0, 0.17), lens=42)


if __name__ == "__main__":
    main()
