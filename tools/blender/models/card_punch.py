"""card_punch.glb — 1950s keyboard card punch on the archivist's desk (Archive B), puzzle P3.

Grey-green enamel body on a dark steel plinth, chrome trim. Eight square bakelite keys with cream
digits 1..8 stand on vertical chrome stems in a row across the front slope (caps tilted 31 deg toward the
player so the digits read from the punch view). A chrome card throat across the top-back holds a request
card standing half inserted; a chrome lever on the right side.

Model space (Godot): front +Z, origin = base centre on the desk surface (y = 0).
Placement: (3.25, 0.76, -3.05), yaw 0. Overall 0.37 (with the lever) x 0.19 (with the card) x 0.29.
Parts (origin at the pivot, identity rotation at rest):
  IA_punch_key_<i>  i = 0..7 left -> right, digits 1..8; pivot at the cap centre; pressed / latched =
                    translate -0.006 along local Y (straight down, the stems are vertical)
  IA_punch_slot     the card throat (chrome housing with the slot)
  card_in_punch     request card standing in the throat (print side +Z, M_Decal_RequestCard, UV 0..1);
                    hidden by code when the punch is empty
  IA_punch_lever    chrome lever on the right side, pivot (0.181, 0.075, -0.030); pull = +60 deg about +X
    blender -b --factory-startup -P tools/blender/models/card_punch.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices1 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "card_punch"
BUDGET = 6000
BW = 0.34                        # body width
BASE_H = 0.012
SLOPE = ((0.128, 0.040), (0.036, 0.096))      # (z, y) start (front) and end (back) of the key slope
SLOPE_DEG = math.degrees(math.atan2(SLOPE[1][1] - SLOPE[0][1], SLOPE[0][0] - SLOPE[1][0]))
TOP_Y = 0.105
KEY_PITCH = 0.036
CAP = 0.027
CAP_H = 0.011
KEY_LIFT = 0.016                 # cap centre above the slope surface, along the slope normal
THROAT = (-0.074, 0.148, 0.040, 0.142)       # slot z, housing width, housing depth, housing top y
CARD = (0.125, 0.075, 0.0006)
CARD_BOTTOM = 0.112
LEVER_PIVOT = (0.181, 0.075, -0.030)


def slope_point(s: float):
    (z0, y0), (z1, y1) = SLOPE
    return (z0 + (z1 - z0) * s, y0 + (y1 - y0) * s)


def rounded_poly(pts, radii, n=4):
    """Polygon with per-corner fillet radii (2D, any orientation)."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % m])
        r = radii[i]
        if r <= 0:
            out.append((p1.x, p1.y))
            continue
        d1 = (p0 - p1).normalized()
        d2 = (p2 - p1).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        t = r / math.tan(ang / 2)
        a = p1 + d1 * t
        b = p1 + d2 * t
        bis = (d1 + d2).normalized()
        c = p1 + bis * (r / math.sin(ang / 2))
        a0 = math.atan2(a.y - c.y, a.x - c.x)
        a1 = math.atan2(b.y - c.y, b.x - c.x)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            aa = a0 + da * k / n
            out.append((c.x + r * math.cos(aa), c.y + r * math.sin(aa)))
    return out


# ---------------------------------------------------------------- body
def build_body():
    parts = []
    plan = C.gframe((0.0, 0.0, 0.0), (1, 0, 0), (0, 0, -1))
    base = C.solid_g("plinth", [L.rounded_rect(BW + 0.012, 0.290, 0.016, 4)], BASE_H, plan, bevel=0.003,
                     bevel_res=1, mat="M_Steel_Dark")
    parts.append(C.sm(base, 40.0))
    # side profile (z, y), extruded along X, rounded edges
    (sz0, sy0), (sz1, sy1) = SLOPE
    prof = [(0.138, BASE_H), (0.138, 0.032), (sz0, sy0), (sz1, sy1), (0.020, TOP_Y), (-0.136, TOP_Y),
            (-0.140, BASE_H)]
    radii = [0.0, 0.008, 0.006, 0.010, 0.006, 0.012, 0.0]
    rp = rounded_poly(prof, radii, 3)
    side = C.gframe((-BW / 2, 0.0, 0.0), (0, 0, -1), (0, 1, 0))       # u = -z, v = y, out = +x
    body = C.solid_g("body", [[(-z, y) for (z, y) in rp]], BW, side, bevel=0.007, bevel_res=2,
                     mat="M_Steel_Painted")
    parts.append(C.sm(body, 40.0))
    # chrome trim strip along the top edge of the slope and along the front lip
    ang = math.radians(SLOPE_DEG)
    for (z, y, w) in ((0.022, TOP_Y - 0.0005, 0.010), (0.139, 0.024, 0.008)):
        tr = C.gbox("trim", (-BW / 2 + 0.010, y - 0.0025, z - w / 2), (BW / 2 - 0.010, y + 0.0025, z + w / 2),
                    mat="M_Chrome", bevel=0.0015)
        parts.append(C.sm(tr, 30.0))
    # key slots on the slope (dark), one per key
    n = (0.0, math.cos(ang), math.sin(ang))
    sz, sy = slope_point(0.5)
    sf = C.gframe((0.0, sy + 0.0004 * n[1], sz + 0.0004 * n[2]), (1, 0, 0), (0, math.sin(ang), -math.cos(ang)))
    for i in range(8):
        x = -3.5 * KEY_PITCH + i * KEY_PITCH
        parts.append(C.shape_g("kslot", [L.rounded_rect(0.012, 0.020, 0.005, 3)], sf, u=x, v=0.0,
                               mat="M_Lacquer_Black"))
    # brass maker's badge on the front lip
    bf = C.front_frame(-0.105, 0.0215, 0.1381)
    parts.append(C.solid_g("badge", [L.rounded_rect(0.064, 0.016, 0.004, 2)], 0.0015, bf, bevel=0.0004,
                           mat="M_Brass_Polished"))
    parts.append(C.text_g("badge_txt", "PERFO  K-8", 0.0085, bf, lift=0.0016, font=C.FONT_COND_B,
                          mat="M_Lacquer_Black", res=1))
    # side vents and screws (left side; the right side carries the lever boss)
    for k in range(4):
        vf = C.gframe((-BW / 2 - 0.0002, 0.0, 0.0), (0, 0, 1), (0, 1, 0))
        parts.append(C.shape_g("vent", [L.rounded_rect(0.060, 0.006, 0.003, 3)], vf, u=-0.060, v=0.040 + 0.012 * k,
                               mat="M_Lacquer_Black"))
    for sx in (-1, 1):
        for (z, y) in ((0.110, 0.030), (-0.115, 0.030), (-0.115, 0.088)):
            parts.append(C.screw_g("sscrew", 0.0035, (sx * (BW / 2 + 0.0001), y, z), normal_g=(sx, 0, 0),
                                   mat="M_Chrome", segs=6, slot=0.4 + z))
    # lever boss on the right side (static bearing the lever turns in)
    lx, ly, lz = LEVER_PIVOT
    boss = C.revolve_g("lboss", [(0.021, 0.0), (0.021, 0.003), (0.018, 0.005), (0.0, 0.005)], (1, 0, 0),
                       (BW / 2, ly, lz), segments=16, mat="M_Chrome", cap_bottom=False)
    parts.append(C.sm(boss, 40.0))
    # rest stop + pulled stop pins
    for a in (90.0 + 8.0, 30.0 - 4.0):
        ar = math.radians(a)
        pin = C.revolve_g("lstop", [(0.003, 0.0), (0.003, 0.008), (0.0, 0.009)], (1, 0, 0),
                          (BW / 2, ly + 0.032 * math.sin(ar), lz + 0.032 * math.cos(ar)), segments=6,
                          mat="M_Rubber", cap_bottom=False)
        parts.append(C.sm(pin, 40.0))
    return C.part("punch_body", parts, (0.0, 0.0, 0.0))


# ---------------------------------------------------------------- keys
def build_keys():
    ang = math.radians(SLOPE_DEG)
    nrm = (0.0, math.cos(ang), math.sin(ang))
    sz, sy = slope_point(0.5)
    cz, cy = sz + KEY_LIFT * nrm[2], sy + KEY_LIFT * nrm[1]
    keys = []
    for i in range(8):
        x = -3.5 * KEY_PITCH + i * KEY_PITCH
        cap = M.box("cap", (CAP, CAP, CAP_H), mat="M_Bakelite", bevel=0.0032, segments=2)
        # cap lies in its own XY (top = +Z local) -> tilt so its top faces the slope normal
        dig = L.text_flat("digit", str(i + 1), 0.0165, font=C.FONT_SANS_B, res=1, mat="M_Enamel_Cream")
        L.recentre_xy(dig)
        dig.data.transform(Matrix.Translation((0, 0, CAP_H / 2 + 0.00025)))
        ring = L.box_mm("collar", (-CAP / 2 - 0.0012, -CAP / 2 - 0.0012, -CAP_H / 2 - 0.0005),
                        (CAP / 2 + 0.0012, CAP / 2 + 0.0012, -CAP_H / 2 + 0.0022), mat="M_Chrome", bevel=0.0008)
        loc = []
        for o in (cap, dig, ring):
            M.apply_transform(o)
            loc.append(o)
        # local key frame: x = model x, y = up the slope, z = slope normal
        kf = C.gframe((x, cy, cz), (1, 0, 0), (0, math.sin(ang), -math.cos(ang)))
        for o in loc:
            o.data.transform(kf)
        # vertical chrome stem down into the slot
        stem = C.revolve_g("stem", [(0.0035, 0.0), (0.0035, 0.024)], (0, 1, 0), (x, cy - 0.024, cz - 0.004),
                           segments=8, mat="M_Chrome", cap_bottom=False, cap_top=False)
        for o in (cap, ring):
            C.sm(o, 35.0)
        C.sm(stem, 60.0)
        key = C.part(f"IA_punch_key_{i}", [cap, dig, ring, stem], (x, cy, cz))
        keys.append(key)
    return keys


# ---------------------------------------------------------------- throat + card
def build_throat():
    tz, tw, td, ty = THROAT
    parts = []
    hb = C.gbox("throat", (-tw / 2, TOP_Y - 0.004, tz - td / 2), (tw / 2, ty, tz + td / 2), mat="M_Chrome",
                bevel=0.006, seg=2)
    parts.append(C.sm(hb, 35.0))
    # dark slot on top + card guides
    sf = C.gframe((0.0, ty + 0.0003, tz), (1, 0, 0), (0, 0, -1))
    parts.append(C.shape_g("slot", [L.rounded_rect(CARD[0] + 0.008, 0.0042, 0.0018, 3)], sf, mat="M_Lacquer_Black"))
    for sx in (-1, 1):
        g = C.gbox("guide", (sx * (CARD[0] / 2 + 0.006) - 0.003, ty, tz - 0.006),
                   (sx * (CARD[0] / 2 + 0.006) + 0.003, ty + 0.010, tz + 0.006), mat="M_Chrome", bevel=0.0012)
        parts.append(C.sm(g, 30.0))
    # front face of the throat: a row of 8 punch-die windows (small dark squares) matching the card positions
    ff = C.front_frame(0.0, (TOP_Y + ty) / 2 + 0.002, tz + td / 2 + 0.0002)
    pitch = CARD[0] / 8
    for k in range(8):
        parts.append(C.shape_g("die", [L.rounded_rect(0.0055, 0.0055, 0.0012, 2)], ff, u=(k - 3.5) * pitch,
                               mat="M_Lacquer_Black"))
    return C.part("IA_punch_slot", parts, (0.0, ty, tz))


def build_card():
    cw, ch, ct = CARD
    tz = THROAT[0]
    card = M.box("card", (cw, ct, ch), mat="M_Paper", bevel=0.0)
    # front (+Z Godot = -Y Blender) face gets the decal
    me = card.data
    slot = M.add_slot(card, "M_Decal_RequestCard")
    for p in me.polygons:
        if p.normal.y < -0.9:
            p.material_index = slot
    card.data.transform(C.grot("x", -4.0))                              # leans back 4 deg in the slot
    card.data.transform(Matrix.Translation(C.G(0.0, CARD_BOTTOM + ch / 2, tz)))
    obj = C.part("card_in_punch", [C.sm(card, 30.0)], (0.0, CARD_BOTTOM + ch / 2, tz))
    return obj


def card_uv():
    o = M.bpy.data.objects["card_in_punch"]
    cw, ch, ct = CARD
    fr = C.front_frame(0.0, CARD_BOTTOM + ch / 2, THROAT[0]) @ Matrix.Rotation(math.radians(-4.0), 4, "X")
    n = C.uv_rect(o, fr, -cw / 2, cw / 2, -ch / 2, ch / 2)
    print(f"{C.TAG} card_in_punch decal faces: {n}")


# ---------------------------------------------------------------- lever
def build_lever():
    lx, ly, lz = LEVER_PIVOT
    hub = C.revolve_g("lhub", [(0.0150, 0.0), (0.0150, 0.008), (0.0120, 0.011), (0.0, 0.011)], (1, 0, 0),
                      (BW / 2 + 0.005, ly, lz), segments=14, mat="M_Chrome", cap_bottom=True)
    arm = C.gbox("larm", (lx + 0.004, ly, lz - 0.0045), (lx + 0.012, ly + 0.108, lz + 0.0045), mat="M_Chrome",
                 bevel=0.0025)
    ball = C.revolve_g("lball", [(0.0, -0.011), (0.007, -0.0095), (0.0105, -0.005), (0.011, 0.0), (0.0105, 0.005),
                                 (0.007, 0.0095), (0.0, 0.011)], (0, 1, 0), (lx + 0.008, ly + 0.117, lz),
                       segments=14, mat="M_Bakelite")
    ia = C.part("IA_punch_lever", [C.sm(hub, 40.0), C.sm(arm, 30.0), C.sm(ball, 60.0)], LEVER_PIVOT)
    return ia


def build():
    C.ensure_materials()
    build_body()
    build_keys()
    build_throat()
    build_card()
    build_lever()


def main():
    M.reset_scene()
    build()
    C.finalize([card_uv])
    C.report(NAME, BUDGET)
    C.export(NAME)
    exp = {f"IA_punch_key_{i}": dict(parent=None) for i in range(8)}
    exp.update({"IA_punch_slot": dict(parent=None), "card_in_punch": dict(parent=None),
                "IA_punch_lever": dict(parent=None, pos=LEVER_PIVOT)})
    C.verify_glb(NAME, exp, BUDGET)
    lo, hi = C.D.bounds()
    print(f"{C.TAG} bounds Godot x [{lo.x:.3f}, {hi.x:.3f}] y [{lo.z:.3f}, {hi.z:.3f}] z [{-hi.y:.3f}, {-lo.y:.3f}]")
    for i in (0, 7):
        o = M.bpy.data.objects[f"IA_punch_key_{i}"]
        print(f"{C.TAG} key {i} pivot {tuple(round(v, 4) for v in C.to_godot(o.location))}")
    for nm in ("IA_punch_lever", "IA_punch_slot", "IA_punch_key_0"):
        o = M.bpy.data.objects[nm]
        lo2 = [min(v.co[k] for v in o.data.vertices) for k in range(3)]
        hi2 = [max(v.co[k] for v in o.data.vertices) for k in range(3)]
        print(f"{C.TAG} {nm} mesh AABB {tuple(round(h - l, 4) for l, h in zip(lo2, hi2))}")
    if C.want_render():
        qa()


def qa():
    C.qa_tweak()
    args = C.qa_args()
    roots = C.model_roots()
    ob = M.bpy.data.objects
    if "--only-views" not in args:
        C.studio(NAME, tuple(C.G(0.42, 0.42, 0.62)), tuple(C.G(0.0, 0.07, 0.0)), lens=45, floor_z=0.0)
    for i in (0, 2, 3, 6):               # keys 1, 3, 4, 7 down (the index-card pattern 1 0 1 1 0 0 1 0)
        C.pose_slide(ob[f"IA_punch_key_{i}"], (0.0, -0.006, 0.0))
    if "--only-views" not in args:
        C.studio(NAME + "_2", tuple(C.G(0.05, 0.36, 0.42)), tuple(C.G(0.0, 0.085, 0.02)), lens=50, floor_z=0.0)
    C.pose_rot(ob["IA_punch_lever"], "x", 60.0)
    if "--only-views" not in args:
        C.studio(NAME + "_3", tuple(C.G(0.55, 0.30, 0.30)), tuple(C.G(0.05, 0.09, -0.02)), lens=45, floor_z=0.0)
    C.pose_rot(ob["IA_punch_lever"], "x", -60.0)
    C.place(roots, (3.25, 0.76, -3.05), 0.0)
    C.qa_room()
    C.qa_desk()
    C.import_model("desk_lamp", (3.05, 0.76, -3.32), 0.0)
    C.import_model("tape_deck", (4.15, 0.76, -3.05), 0.0)
    C.qa_hall_lights()
    C.render(NAME + "_4", (3.25, 1.2, -2.35), (3.25, 0.82, -3.05), 40.0)


main()
