"""lumen_projector.glb — Prof. Strand's "Lumen" projector, the small brass sibling of the Array.

Brass lamp-house with blackened cooling fins and a lantern chimney, on a trunnion yoke over a walnut
tripod. The light runs along the model front (Blender -Y = Godot +Z) at Z = 1.15 m.
A cloth cable drops from the rear cap to a brass floor outlet behind the tripod.

Model space: front = Blender -Y, floor on Z = 0, origin at the tripod centre on the floor.
Interactive parts (separate objects, origin at the pivot, identity rotation at rest):
  IA_ring_0..2        tuning rings around the barrel; ring 0 is nearest the lens (front, engraved "I" on
                      the index rail), ring 2 nearest the lamp house ("III"). Origin on the beam axis;
                      rotate about Godot +Z (the beam axis). Six enamel segments; seen from the front,
                      clockwise from 12 o'clock at rest: white, crimson, amber, green, cobalt, violet.
                      Colour k (0 crimson .. 5 white) carries k+1 raised brass notches. Colour k sits under
                      the index after rotating the ring by (k - 5) * 60 deg about Godot +Z (right-hand rule).
                      At rest WHITE is under the index.
  IA_lens_socket      bayonet socket at the barrel front (origin = lens centre)
  lens_installed      crystal lens seated in the socket (M_Crystal + brass ring; hide until inserted)
  IA_projector_lever  throw lever on the right (+X) side; rotates about Godot +X; ON = +35 deg
  beam_origin         empty at the lens front centre, beam along Godot +Z
Static meshes are split (tripod / mount / lamp house / cable) so their tap boxes stay tight.
    blender -b --factory-startup -P tools/blender/models/lumen_projector.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ZB = 1.15                    # beam height
R_H = 0.075                  # lamp-house radius
Y_HF, Y_HR = -0.020, 0.232   # lamp-house front / rear (before the rear cap)
FINS = (0.070, 0.094, 0.118, 0.142)
R_FIN, T_FIN = 0.095, 0.006
Y_CHIM = 0.194
R_BAR = 0.042                # barrel radius
Y_T = 0.020                  # trunnion axis (Y)
RING_Y = (-0.120, -0.089, -0.058)   # ring 0 = front (nearest the lens)
RING_W = 0.024
R_RI, R_RE, R_RB = 0.0425, 0.0575, 0.0590    # inner, enamel, brass-rim radii
RIM = 0.0022
ENAMEL = ("M_Enamel_Crimson", "M_Enamel_Amber", "M_Enamel_Green", "M_Enamel_Cobalt", "M_Enamel_Violet",
          "M_Enamel_White")
Y_SOCK = -0.255              # socket back face
LENS_Y = Y_SOCK - 0.016      # lens centre
LENS_FRONT = LENS_Y - 0.008  # crystal apex
LEVER_P = (0.088, 0.205, ZB)
LEVER_REST = math.radians(-25.0)   # arm leans back (toward +Y) at rest
HEAD_Z = 0.885
LEG_ANG = (90.0, 210.0, 330.0)     # one leg to the back, two to the front corners
LEG_TOP_R, LEG_TOP_Z, LEG_FOOT_R = 0.056, 0.862, 0.40
OUTLET = (0.15, 0.62)


def leg_point(ang_deg, t):
    """Point on a leg axis: t = 0 at the foot (floor), 1 at the hinge."""
    a = math.radians(ang_deg)
    r = LEG_FOOT_R + (LEG_TOP_R - LEG_FOOT_R) * t
    return Vector((r * math.cos(a), r * math.sin(a), LEG_TOP_Z * t))


# ---------------------------------------------------------------- tripod (static)
def build_tripod():
    parts = []
    for k, ang in enumerate(LEG_ANG):
        foot = leg_point(ang, 0.0)
        d = leg_point(ang, 1.0) - foot
        ln = d.length
        prof = [(0.0, 0.0), (0.011, 0.013), (0.0145, 0.020), (0.0145, 0.068), (0.0125, 0.073),
                (0.0190, ln - 0.05), (0.0178, ln - 0.044), (0.0178, ln)]
        bands = ["M_Steel_Dark", "M_Brass_Aged", "M_Brass_Aged", "M_Brass_Aged", "M_Wood_Walnut",
                 "M_Brass_Aged", "M_Brass_Aged"]
        parts.append(D.revolve(f"leg{k}", prof, direction=d, loc=foot, segments=6, band_mats=bands,
                               cap_bottom=False, cap_top=False))
        a = math.radians(ang)
        tang = Vector((-math.sin(a), math.cos(a), 0.0))
        hp = leg_point(ang, 1.0) - d.normalized() * 0.022
        parts.append(D.revolve(f"bolt{k}", [(0.0, -0.026), (0.0065, -0.0235), (0.007, -0.019), (0.007, 0.019),
                                            (0.0065, 0.0235), (0.0, 0.026)],
                               direction=tang, loc=hp, segments=6, mat="M_Brass_Aged"))
        for s in (-1, 1):
            ch = M.box("cheek", (0.004, 0.026, 0.034), mat="M_Brass_Aged", bevel=0.0, segments=1)
            ch.data.transform(Matrix.Rotation(a + math.pi / 2, 4, "Z"))
            ch.location = hp + tang * (0.0195 * s) + Vector((0, 0, 0.006))
            parts.append(ch)
        # spreader rod from the leg to the centre hub
        p_leg = leg_point(ang, 0.33)
        hub = Vector((0, 0, 0.245))
        rod_dir = p_leg - hub
        parts.append(D.revolve(f"spreader{k}", [(0.0035, 0.012), (0.0035, rod_dir.length - 0.013)],
                               direction=rod_dir, loc=hub, segments=6, mat="M_Brass_Aged", cap_bottom=False,
                               cap_top=False))
    hub = L.lathe2("hub", [(0.0, -0.008), (0.014, -0.007), (0.016, 0.0), (0.014, 0.007), (0.0, 0.008)],
                   segments=10, mat="M_Brass_Aged")
    hub.location = (0, 0, 0.245)
    parts.append(hub)
    head = L.lathe2("head", [(0.0, 0.846), (0.052, 0.847), (0.066, 0.858), (0.066, 0.877), (0.060, HEAD_Z),
                             (0.0, HEAD_Z)], segments=16, mat="M_Brass_Aged")
    parts.append(head)
    return M.join(parts, "projector_tripod")


# ---------------------------------------------------------------- column, pan head, yoke (static)
def build_mount():
    parts = []
    col = L.lathe2("column", [(0.017, HEAD_Z - 0.002), (0.017, 0.962), (0.046, 0.965), (0.049, 0.970),
                              (0.049, 0.982), (0.045, 0.986), (0.0, 0.986)], segments=14, mat="M_Brass_Aged",
                   cap_bottom=False)
    parts.append(col)
    # pan lock: bakelite T-handle screw on the column (+X)
    pk = L.lathe2("panknob", [(0.0, 0.0), (0.004, 0.0), (0.004, 0.010), (0.0085, 0.012), (0.0085, 0.020),
                              (0.006, 0.023), (0.0, 0.023)], segments=6, mat="M_Bakelite")
    D.aim(pk, (1, 0, 0))
    pk.location = (0.015, 0.0, 0.925)
    parts.append(pk)
    # trunnion yoke (U) drawn in XZ, extruded along Y
    xo, xi = 0.114, 0.102
    zo, zi = 0.986, 1.000
    rc = 0.03
    ri = rc - (xo - xi) + 0.002
    inner_r = L.arc_pts(ri, 0.0, -math.pi / 2, 3, cx=xi - ri, cy=zi + ri)
    top = L.arc_pts((xo - xi) / 2, 0.0, math.pi, 4, cx=(xo + xi) / 2, cy=ZB)
    outer = L.arc_pts(rc, -math.pi / 2, 0.0, 4, cx=xo - rc, cy=zo + rc)
    pts = outer + top + inner_r
    pts += [(-x, y) for (x, y) in inner_r[::-1]]
    pts += [(-x, y) for (x, y) in top[::-1]]
    pts += [(-x, y) for (x, y) in outer[::-1]]
    clean = []
    for p in pts:
        if not clean or (abs(clean[-1][0] - p[0]) > 1e-6 or abs(clean[-1][1] - p[1]) > 1e-6):
            clean.append(p)
    yoke = L.curve_solid("yoke", [clean], 0.024, bevel=0.0015, bevel_res=0, mat="M_Brass_Aged")
    L.to_front(yoke, y_back=Y_T + 0.012)
    parts.append(yoke)
    # trunnion bosses through the arms + knurled tension knobs
    for s in (-1, 1):
        boss = D.revolve("tboss", [(0.0145, 0.0), (0.0145, 0.044), (0.0125, 0.046), (0.0, 0.046)],
                         direction=(s, 0, 0), loc=(s * 0.074, Y_T, ZB), segments=10, mat="M_Brass_Aged",
                         cap_bottom=False)
        knob = L.lathe2("tknob", [(0.0, 0.0), (0.0165, 0.0), (0.0175, 0.0015, "k"), (0.0175, 0.0125, "k"),
                                  (0.0145, 0.0165), (0.0, 0.0175)], segments=14, knurl=0.0012,
                        mat="M_Brass_Aged", band_mats=[None, None, None, "M_Brass_Polished", "M_Brass_Polished"],
                        cap_bottom=False)
        D.aim(knob, (s, 0, 0))
        knob.location = (s * 0.118, Y_T, ZB)
        parts += [boss, knob]
    return M.join(parts, "projector_mount")


# ---------------------------------------------------------------- lamp house (static)
def build_house():
    parts = []
    # body: front bead, four blackened V-fins, plain rear band, bead, domed rear cap
    prof = [(R_H + 0.004, Y_HF), (R_H + 0.004, Y_HF + 0.007), (R_H, Y_HF + 0.010)]
    bands = ["M_Brass_Polished", "M_Brass_Aged"]
    for n, f in enumerate(FINS):      # brass V-fins over blackened gaps
        prof += [(R_H, f), (R_FIN, f + T_FIN / 2), (R_H, f + T_FIN)]
        bands += ["M_Brass_Aged" if n == 0 else "M_Bakelite", "M_Brass_Aged", "M_Brass_Aged"]
    prof += [(R_H, Y_HR - 0.003), (R_H + 0.005, Y_HR + 0.001), (R_H + 0.003, Y_HR + 0.007),
             (0.054, Y_HR + 0.026), (0.0, Y_HR + 0.036)]
    bands += ["M_Brass_Aged", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Aged", "M_Brass_Aged"]
    parts.append(D.revolve("house", prof, direction=(0, 1, 0), loc=(0, 0, ZB), segments=18, band_mats=bands,
                           cap_bottom=False))
    # lantern chimney with a mushroom cap and louvres
    zc = ZB + R_H - 0.012
    parts.append(D.revolve("chimney", [(0.022, 0.0), (0.022, 0.052), (0.039, 0.056), (0.040, 0.060),
                                       (0.018, 0.070), (0.0, 0.072)],
                           direction=(0, 0, 1), loc=(0, Y_CHIM, zc), segments=14, mat="M_Steel_Dark",
                           band_mats=[None, "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished",
                                      "M_Brass_Polished"], cap_bottom=False))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        v = L.flat_shape("louvre", [[(-0.0021, -0.012), (0.0021, -0.012), (0.0021, 0.012), (-0.0021, 0.012)]],
                         mat="M_Bakelite")
        v.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))      # face +X
        v.data.transform(Matrix.Rotation(a, 4, "Z"))
        v.location = (0.02215 * math.cos(a), Y_CHIM + 0.02215 * math.sin(a), zc + 0.030)
        parts.append(v)
    # front flange + barrel + rail collar (one turned piece along -Y, z = distance in front of Y_HF)
    fl = [(0.079, 0.0), (0.086, 0.002), (0.086, 0.009), (0.083, 0.012), (0.048, 0.012), (R_BAR, 0.018),
          (R_BAR, 0.134), (0.0505, 0.136), (0.0505, 0.150), (R_BAR + 0.001, 0.153),
          (R_BAR + 0.001, Y_HF - Y_SOCK + 0.001)]
    fbands = ["M_Brass_Aged", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Aged", "M_Brass_Polished",
              "M_Brass_Aged", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Polished", "M_Brass_Aged"]
    parts.append(D.revolve("flange", fl, direction=(0, -1, 0), loc=(0, Y_HF, ZB), segments=20, band_mats=fbands,
                           cap_bottom=False, cap_top=False))
    # knurled focus collar
    fz0, fz1 = 0.168, 0.200
    parts.append(D.revolve("focus", [(R_BAR + 0.001, fz0), (0.0488, fz0 + 0.0025, "k"), (0.0488, fz1 - 0.0025, "k"),
                                     (R_BAR + 0.001, fz1)],
                           direction=(0, -1, 0), loc=(0, Y_HF, ZB), segments=40, knurl=0.0021, mat="M_Brass_Aged",
                           cap_bottom=False, cap_top=False))
    # flange face: 4 domed screws + engraved name
    yf = Y_HF - 0.012
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        parts.append(L.rivet("fscrew", 0.0042, (0.071 * math.cos(a), yf, ZB + 0.071 * math.sin(a)),
                             normal=(0, -1, 0), segs=6))
    parts.append(D.text("lumen_txt", "LUMEN", 0.0105, font=D.FONT_DISPLAY, mat="M_Bakelite", res=1,
                        loc=(0.0, yf - 0.0002, ZB + 0.0775), rot=L.front_rot(), spacing=1.15))
    # index rail over the rings: bracket, rail, front post, 3 blued pointers, numerals I II III
    y_r0, y_r1 = Y_HF - 0.0115, Y_HF - 0.150
    zr = ZB + 0.0655
    parts.append(M.box("rail", (0.010, y_r0 - y_r1, 0.004), loc=(0, (y_r0 + y_r1) / 2, zr + 0.002),
                       mat="M_Brass_Aged", bevel=0.0012, segments=1))
    for (yy, z_base) in ((Y_HF - 0.0145, ZB + 0.0475), (Y_HF - 0.1435, ZB + 0.0495)):
        parts.append(M.box("post", (0.008, 0.006, zr - z_base + 0.001), loc=(0, yy, (zr + z_base) / 2),
                           mat="M_Brass_Aged", bevel=0.0))
    for i, yc in enumerate(RING_Y):
        ptr = L.curve_solid(f"ptr{i}", [[(-0.004, 0.0), (0.004, 0.0), (0.0, -0.0045)]], 0.0018, bevel=0.0003,
                            mat="M_Steel_Dark")
        L.to_front(ptr, y_back=yc + 0.0009, z=zr)
        parts.append(ptr)
        for j in range(i + 1):
            off = (j - i / 2.0) * 0.0022
            parts.append(L.flat_shape(f"num{i}", [L.rounded_rect(0.0062, 0.0009, 0.0002, 1)], mat="M_Bakelite",
                                      loc=(0.0, yc + off, zr + 0.00405)))
        for sx in (-1, 1):
            parts.append(L.flat_shape("ser", [L.rounded_rect(0.0008, 0.0022 * (i + 1) + 0.0012, 0.0002, 1)],
                                      mat="M_Bakelite", loc=(sx * 0.0031, yc, zr + 0.00406)))
    # lever boss + quadrant plate with OFF (cream) / ON (green) stops on the right side
    parts.append(D.revolve("lboss", [(0.016, 0.0), (0.016, 0.010), (0.0145, 0.0115), (0.0, 0.0115)],
                           direction=(1, 0, 0), loc=(LEVER_P[0] - 0.012, LEVER_P[1], ZB), segments=12,
                           mat="M_Brass_Aged", cap_bottom=False))
    quad = L.arc_pts(0.040, math.radians(50.0), math.radians(125.0), 5) + \
        L.arc_pts(0.018, math.radians(125.0), math.radians(50.0), 2)
    qp = L.curve_solid("quadrant", [quad], 0.0025, bevel=0.0006, mat="M_Brass_Aged")
    # drawn x -> world -Y (front), drawn y -> world +Z, extrusion -> world +X
    qp.data.transform(Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    qp.data.flip_normals()        # that axis map is a reflection (det -1): restore outward normals
    qp.location = (LEVER_P[0] - 0.0035, LEVER_P[1], ZB)
    parts.append(qp)
    for ang, mat in ((math.radians(115.0), "M_Enamel_Cream"), (math.radians(80.0), "M_Enamel_Green")):
        mk = L.flat_shape("qmark", [L.circle(0.0032, 8)], mat=mat)
        mk.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
        mk.location = (LEVER_P[0] - 0.0035 + 0.0026, LEVER_P[1] - 0.034 * math.cos(ang), ZB + 0.034 * math.sin(ang))
        parts.append(mk)
    # cable gland under the rear cap
    parts.append(D.revolve("gland", [(0.011, 0.0), (0.011, 0.012), (0.0085, 0.015), (0.0085, 0.021),
                                     (0.0, 0.022)],
                           direction=(0, 0.45, -1), loc=(0, Y_HR + 0.010, ZB - 0.052), segments=10,
                           mat="M_Brass_Aged", cap_bottom=False))
    return M.join(parts, "projector_house")


# ---------------------------------------------------------------- rings (interactive)
def build_ring(i):
    w = RING_W / 2
    c = 0.001
    yc = RING_Y[i]
    prof = [(R_RI, -w), (R_RB - c, -w), (R_RB, -w + c), (R_RB, -w + RIM), (R_RE, -w + RIM),
            (R_RE, w - RIM), (R_RB, w - RIM), (R_RB, w - c), (R_RB - c, w), (R_RI, w)]
    seg = 18

    def mat_fn(k, s):
        if k != 4:
            return "M_Brass_Polished"
        return ENAMEL[(6 - s // (seg // 6)) % 6]

    parts = [D.revolve(f"ring{i}", prof, direction=(0, -1, 0), loc=(0, yc, ZB), segments=seg, mat_fn=mat_fn,
                       cap_bottom=False, cap_top=False)]
    # tactile notches: colour k carries k+1 raised brass ridges, centred on its segment
    for k in range(6):
        a_k = math.radians(90.0 + (5 - k) * 60.0)
        n = k + 1
        for j in range(n):
            a = a_k + math.radians((j - (n - 1) / 2.0) * 6.0)
            nrm = Vector((math.cos(a), 0.0, math.sin(a)))
            base = Vector((0, yc, ZB)) + nrm * (R_RE - 0.0006)
            parts.append(D.wedge("notch", 0.0080, 0.0026, 0.0023, base, direction_len=(0, 1, 0), normal=nrm,
                                 mat="M_Brass_Polished", pyramid=True))
    obj = M.join(parts, f"IA_ring_{i}")
    M.set_origin(obj, (0, yc, ZB))
    return obj


# ---------------------------------------------------------------- socket + lens + lever (interactive)
def build_socket():
    prof = [(0.0525, 0.0), (0.0545, 0.0018), (0.0545, 0.0202), (0.0525, 0.022), (0.0358, 0.022),
            (0.0358, 0.0095), (0.0, 0.0095)]
    bands = ["M_Brass_Polished"] * 4 + ["M_Brass_Aged", "M_Bakelite"]
    parts = [D.revolve("socket", prof, direction=(0, -1, 0), loc=(0, Y_SOCK, ZB), segments=20, band_mats=bands,
                       cap_bottom=False, cap_top=False)]
    yf = Y_SOCK - 0.022
    for k in range(3):                       # bayonet lugs on the inner lip
        a = math.pi / 2 + k * 2 * math.pi / 3
        lug = M.box("lug", (0.0065, 0.003, 0.0024), mat="M_Brass_Polished", bevel=0.0, segments=1)
        lug.data.transform(Matrix.Rotation(math.pi / 2 - a, 4, "Y"))
        lug.location = (0.0352 * math.cos(a), yf + 0.0016, ZB + 0.0352 * math.sin(a))
        parts.append(lug)
    for k in range(12):                      # engraved index ticks on the front face
        a = k * math.pi / 6 + math.pi / 2
        ln = 0.0055 if k % 3 == 0 else 0.0032
        tk = L.flat_shape("stick", [L.rounded_rect(0.0008, ln, 0.0001, 1)], mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        L.to_front(tk, y_back=yf - 0.00005, x=(0.0505 - ln / 2) * math.cos(a), z=ZB + (0.0505 - ln / 2) * math.sin(a))
        parts.append(tk)
    obj = M.join(parts, "IA_lens_socket")
    M.set_origin(obj, (0, LENS_Y, ZB))
    return obj


def build_lever():
    px, py, pz = LEVER_P
    hub = D.revolve("lhub", [(0.0, 0.0), (0.012, 0.0), (0.0125, 0.0055), (0.0115, 0.0067), (0.005, 0.0085),
                             (0.0, 0.0088)], direction=(1, 0, 0), loc=(px, py, pz), segments=12,
                    mat="M_Brass_Polished")
    arm = L.curve_solid("arm", [[(-0.0055, 0.0), (0.0055, 0.0), (0.0036, 0.100), (-0.0036, 0.100)]], 0.0045,
                        bevel=0.0012, bevel_res=0, mat="M_Brass_Polished")
    # drawn x -> world Y (width), drawn y -> world Z (length), extrusion -> world +X (thickness)
    arm.data.transform(Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    arm.location = (px + 0.0010, py, pz)
    ball = L.lathe2("lknob", [(0.0, -0.002), (0.0055, 0.002), (0.0125, 0.011), (0.0135, 0.019), (0.0105, 0.027),
                              (0.0, 0.032)], segments=12, mat="M_Bakelite")
    ball.location = (px + 0.0032, py, pz + 0.098)
    obj = M.join([hub, arm, ball], "IA_projector_lever")
    obj.data.transform(Matrix.Translation((-px, -py, -pz)))
    obj.data.transform(Matrix.Rotation(LEVER_REST, 4, "X"))
    obj.location = (px, py, pz)
    return obj


# ---------------------------------------------------------------- power cable + floor outlet (static)
def build_cable():
    g0 = Vector((0, Y_HR + 0.010, ZB - 0.052)) + Vector((0, 0.45, -1)).normalized() * 0.021
    ox, oy = OUTLET
    path = [tuple(g0), (0.0, 0.268, 1.02), (0.022, 0.305, 0.80), (0.058, 0.362, 0.42), (0.098, 0.432, 0.07),
            (0.124, 0.505, 0.0068), (ox, oy - 0.032, 0.0075), (ox, oy, 0.016)]
    cable = L.tube("cable", path, 0.0042, mat="M_Fabric", bevel_res=1, res_u=2)
    for v in cable.data.vertices:           # Bezier overshoot: flatten the contact patch on the floor
        v.co.z = max(v.co.z, 0.0002)
    outlet = L.lathe2("outlet", [(0.032, 0.0), (0.032, 0.002), (0.028, 0.005), (0.012, 0.006), (0.0105, 0.018),
                                 (0.0, 0.019)], segments=12, mat="M_Brass_Aged", cap_bottom=False)
    outlet.location = (ox, oy, 0.0)
    return M.join([cable, outlet], "projector_cable")


def build():
    D.ensure_materials()
    build_tripod()
    build_mount()
    build_house()
    for i in range(3):
        build_ring(i)
    build_socket()
    D.crystal_lens("lens_installed", (0, LENS_Y, ZB), segments=20, ticks=12, low=True)
    build_lever()
    build_cable()
    M.empty("beam_origin", loc=(0.0, LENS_FRONT, ZB))


def pose(rings_k=(5, 5, 5), lever_on=False):
    """QA posing in Godot terms: ring i rotated by (k - 5) * 60 deg about Godot +Z (= Blender -Y)."""
    for i, k in enumerate(rings_k):
        a = math.radians((k - 5) * 60.0)
        M.bpy.data.objects[f"IA_ring_{i}"].rotation_euler = (0.0, -a, 0.0)   # about Blender +Y by -a
    M.bpy.data.objects["IA_projector_lever"].rotation_euler = (math.radians(35.0) if lever_on else 0.0, 0.0, 0.0)


def main():
    M.reset_scene()
    build()
    L.finish("lumen_projector", decals=[lambda: D.resmooth(M.bpy.data.objects["lens_installed"])])
    D.describe("lumen_projector")
    if D.want_render():
        D.qa_tweak()
        D.shot("lumen_projector", (1.25, -1.30, 1.50), (0.0, 0.04, 0.72), lens=38, res=(720, 960))
        D.shot("lumen_projector_2", (0.62, -0.62, 1.42), (0.0, -0.08, 1.15), lens=50)
        D.shot("lumen_projector_3", (0.16, -0.70, 1.30), (0.0, -0.13, 1.17), lens=60)
        pose((0, 3, 2), lever_on=True)
        D.shot("lumen_projector_4", (0.55, -0.45, 1.40), (0.0, -0.06, 1.16), lens=55)


if __name__ == "__main__":
    main()
