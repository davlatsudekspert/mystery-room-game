"""vault_door.glb — the Chapter 2 climax: a 1.9 m round bank-vault door with a dual "light lock".

Contract: docs/models/ch2.md §1 (vault opening), §2 (vault, vault_ports views), §6 (vault_door).
Measured results and deviations: docs/models/ch2_vault.md.

MODEL SPACE (Godot axes, metres). Origin = world (1.5, 0, -3.5) on the north wall's room face;
local z = 0 is the wall face, +Z points into the room, door centre (0, 1.35).

STATIC  vault_frame      cast-concrete frame plate x ±1.2, y 0.15..2.55, z 0..0.10 with a steel angle
                         border, a raised stepped steel lining around the Ø1.90 aperture, a stepped tunnel
                         sleeve through the wall (z -0.20..0; bore r 0.95 / 0.915 / 0.86), eight bolt
                         keepers (the locked bolts reach into them), the static hinge knuckles + brackets,
                         rivets, anchor bolts, the brass maker's plate and the Institute medallion.
DOOR    IA_vault_door    Ø1.88, 0.40 thick (z -0.24..+0.16), stepped/tapered plug so it clears the bore
                         when it swings (checked numerically in check_swing()). ORIGIN = hinge axis
                         (-1.05, 1.35, +0.22). OPEN = -95° about local +Y (swings into the room).
  IA_vault_handle        6-spoke brass handwheel Ø0.52, origin (0, 0.98, 0.16); tap = -120° about +Z.
  bolt_0..7              chrome locking bolts lying on guide rails at angle k·45° (CCW from +X), centre
                         radius 0.86, axis z 0.215; origin at the bolt centre. Unlocked = 0.08 inward.
  glass_disc             Ø0.444 disc at (0, 1.62, 0.182) facing +Z, UV 0..1 over its bounding square.
  disc_bezel             polished brass bezel ring around it (own object).
  IA_port_left/right     brass lens barrels Ø0.155 at (∓0.55, 1.62), z 0.16..0.281 (protrude 0.12).
    port_left/right_mount  mouth centre (∓0.55, 1.62, 0.268), identity: a crystal stands in it facing +Z.
  light_pipe_left/right  glass rods (M_Crystal) in brass channels from each port to the bezel.
  IA_collar_left/right   knurled collars on the barrels, -45° × steps about +Z; 8 enamel ticks, tick n
                         at 90° + 45°·n (CCW) so step n brings tick n to the top index; 0/4 marked.
  IA_zoom_right          narrower ring in front of IA_collar_right, -40° × zoom; digits 0..4.
  (door mesh)            ✦ / ☾ brass plates under the ports, hinge arms + door knuckles, bolt guides,
                         the boltwork window and the time lock on the back face.

    blender -b --factory-startup -P tools/blender/models/vault_door.py [-- --no-render] [--shots 1,2,..]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_vault as V  # noqa: E402

NAME = "vault_door"
BUDGET = 14000
CY = 1.35                       # door centre height
SEG = 48                        # big lathes (sagitta 2 mm at r 0.95; smooth-shaded)
PIVOT = (-1.05, CY, 0.22)       # hinge axis (door origin)
HINGE_Y = (0.85, 1.85)          # hinge assemblies
FACE = 0.16                     # door front face
BOLT_R, BOLT_Z, BOLT_TRAVEL = 0.86, 0.215, 0.08
HANDLE = (0.0, 0.98)
DISC = (0.0, 1.62)
DISC_R = 0.222
DISC_Z = 0.182
PORT_X = 0.55
PORT_Y = 1.62
MOUNT_Z = 0.268
DOOR_PROFILE = [            # (r, z): back centre -> rim steps -> front face (see check_swing)
    (0.0, -0.24), (0.815, -0.24), (0.83, -0.225), (0.83, -0.12), (0.884, -0.12), (0.89, -0.114),
    (0.89, 0.0), (0.932, 0.0), (0.932, 0.10), (0.94, 0.10), (0.94, 0.149), (0.929, 0.16), (0.725, 0.16),
    (0.70, 0.16), (0.0, 0.16)]
BORE_PROFILE = [            # frame lining + tunnel sleeve (r, z), surfaces face the axis / the room
    (1.12, 0.098), (1.12, 0.115), (1.108, 0.127), (0.962, 0.127), (0.95, 0.115), (0.95, 0.0), (0.915, 0.0),
    (0.915, -0.12), (0.86, -0.12), (0.86, -0.20)]
STEEL, CHROME, BRASS, BRASS_P = "M_Steel_Dark", "M_Chrome", "M_Brass_Aged", "M_Brass_Polished"
PAINT, CREAM, INK = "M_Steel_Painted", "M_Enamel_Cream", "M_Lacquer_Black"


def polar(r, a_deg, cy=CY):
    a = math.radians(a_deg)
    return (r * math.cos(a), cy + r * math.sin(a))


def rot_about_door_axis(obj, a_deg):
    """Rotate mesh data about the door axis (0, CY) by a_deg (CCW seen from the room)."""
    obj.data.transform(Matrix.Translation((0, CY, 0)) @ Matrix.Rotation(math.radians(a_deg), 4, "Z")
                       @ Matrix.Translation((0, -CY, 0)))


def radial_prism(name, poly_vz, u0, u1, mat, bevel=0.0):
    """Prism of the polygon [(v, z)] (v tangential) extruded radially from u0 to u1 along +X."""
    bm = bmesh.new()
    a = [bm.verts.new((u0, v, z)) for (v, z) in poly_vz]
    b = [bm.verts.new((u1, v, z)) for (v, z) in poly_vz]
    n = len(poly_vz)
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    if bevel > 0:
        L.bevel_sharp(o, bevel, 1, 40.0)
    return o


# ====================================================================== swing check
def check_swing() -> bool:
    """2D check at mid height: every door profile corner must stay out of the bore material while the
    door turns 0..-95° about the hinge axis (plan view: dx = x + 1.05, dz = z - 0.22)."""
    bore = []          # material rectangles (x_min, z0, z1) on the right side of the bore
    for i in range(len(BORE_PROFILE) - 1):
        (r0, z0), (r1, z1) = BORE_PROFILE[i], BORE_PROFILE[i + 1]
        if abs(r0 - r1) < 1e-9:          # a bore cylinder: material at x >= r for z in [z1, z0]
            bore.append((r0, min(z0, z1), max(z0, z1)))
    # the keepers and the raised lining: material at x >= 0.955 for z in [0.10, 0.29]
    bore.append((0.955, 0.10, 0.29))
    pts = [(r, z) for (r, z) in DOOR_PROFILE if r > 0.5]
    pts += [(BOLT_R + 0.12 - BOLT_TRAVEL, BOLT_Z - 0.042), (BOLT_R + 0.12 - BOLT_TRAVEL, BOLT_Z + 0.042)]
    worst = 1e9
    for (r, z) in pts:
        dx, dz = r + 1.05, z - PIVOT[2]
        for step in range(0, 951):
            a = math.radians(-step / 10.0)
            # rotation about +Y by a: x' = x cos a + z sin a ; z' = -x sin a + z cos a
            nx = dx * math.cos(a) + dz * math.sin(a)
            nz = -dx * math.sin(a) + dz * math.cos(a)
            x, zz = nx - 1.05, nz + PIVOT[2]
            for (xr, z0, z1) in bore:
                if z0 + 1e-6 < zz < z1 - 1e-6:
                    worst = min(worst, xr - x)
    ok = worst > 0.0
    print(f"{V.TAG} swing check: minimum clearance to the bore / keepers during 0..-95° = {worst * 1000:.1f} mm "
          f"({'OK' if ok else 'COLLISION'})")
    return ok


# ====================================================================== frame (static)
def build_frame():
    parts = []
    # cast concrete plate with a steel angle border
    conc = V.plate("conc", [L.rounded_rect(2.36, 2.36, 0.02, 3, cy=CY), L.circle(1.0, 48, cy=CY)], 0.10,
                   mat="M_Concrete", bevel=0.008, bevel_res=1)
    parts.append(conc)
    border = [V.gbox("bord", (-1.2, 0.15, 0.0), (1.2, 0.18, 0.104), STEEL, 0.004),
              V.gbox("bord", (-1.2, 2.52, 0.0), (1.2, 2.55, 0.104), STEEL, 0.004),
              V.gbox("bord", (-1.2, 0.18, 0.0), (-1.17, 2.52, 0.104), STEEL, 0.004),
              V.gbox("bord", (1.17, 0.18, 0.0), (1.2, 2.52, 0.104), STEEL, 0.004)]
    parts += border
    for t in (0.2, 0.5, 0.8):                  # rivets on the angle border
        x = -1.08 + 2.16 * t
        for y in (0.165, 2.535):
            parts.append(V.rivet("brv", 0.008, (x, y, 0.104), segs=6))
        y = 0.40 + 1.90 * t
        for x2 in (-1.185, 1.185):
            parts.append(V.rivet("brv", 0.008, (x2, y, 0.104), segs=6))
    # stepped steel lining + tunnel sleeve (one lathe)
    bands = [STEEL, STEEL, STEEL, CHROME, STEEL, CHROME, STEEL, CHROME, STEEL]
    lin = V.glathe("lining", BORE_PROFILE, (0, CY, 0), (0, 0, 1), SEG, STEEL, band_mats=bands,
                   cap_bottom=False, cap_top=False, smooth=40.0)
    parts.append(lin)
    # rivets on the lining ring between the keepers
    for k in range(8):
        for j in (1, 3):
            a = k * 45 + 11.25 * j
            x, y = polar(1.045, a)
            parts.append(V.rivet("lrv", 0.011, (x, y, 0.127), segs=6))
    # bolt keepers
    for k in range(8):
        parts += keeper(k)
    # static hinge knuckles + brackets
    for yh in HINGE_Y:
        parts += hinge_static(yh)
    # anchor bolts in the lower corners
    for sx in (-1, 1):
        parts.append(V.hexbolt("anchor", 0.022, (sx * 1.07, 0.29, 0.10), h=0.018))
    parts += makers_plate()
    parts += medallion()
    return V.part("vault_frame", parts)


def keeper(k):
    """A cast steel keeper on the lining at angle k·45°: the locked bolt end sits in its socket."""
    u0, u1, hw = 0.956, 1.08, 0.072
    poly = [(-hw, 0.127), (hw, 0.127), (hw * 0.86, 0.29), (-hw * 0.86, 0.29)]
    body = radial_prism("keeper", poly, u0, u1, STEEL, bevel=0.006)
    hole = L.flat_shape("hole", [L.circle(0.0475, 12)], mat=INK)
    hole.data.transform(Matrix.Translation((u0 - 0.0008, 0, BOLT_Z)) @ V.axis_rot((-1, 0, 0)))
    bolts = [V.hexbolt("kbolt", 0.012, (u0 + 0.075, 0.0, 0.29), h=0.01, washer=False)]
    objs = [body, hole] + bolts
    for o in objs:
        o.data.transform(Matrix.Translation((0, CY, 0)) @ Matrix.Rotation(math.radians(k * 45), 4, "Z"))
        V.A.hint(o, 40.0)
    return objs


def hinge_static(yh):
    x, z = PIVOT[0], PIVOT[2]
    out = []
    lo = [(0.0, -0.212), (0.03, -0.205), (0.055, -0.188), (0.07, -0.168), (0.07, -0.08), (0.0, -0.076)]
    hi = [(0.0, 0.076), (0.07, 0.08), (0.07, 0.168), (0.055, 0.188), (0.03, 0.205), (0.0, 0.212)]
    for prof in (lo, hi):
        bm = [BRASS_P, BRASS_P, BRASS_P, None, None] if prof is lo else [None, None, BRASS_P, BRASS_P, BRASS_P]
        kn = V.glathe("knuckle", prof, (x, yh, z), (0, 1, 0), 16, STEEL, smooth=50.0, band_mats=bm)
        out.append(kn)
        y0, y1 = (yh + 0.084, yh + 0.166) if prof is hi else (yh - 0.166, yh - 0.084)
        out.append(V.gbox("hbracket", (x - 0.062, y0, 0.10), (x + 0.062, y1, z), STEEL, 0.008))
        base = V.gbox("hbase", (x - 0.095, y0 - 0.02, 0.10), (x + 0.085, y1 + 0.02, 0.114), STEEL, 0.004)
        out.append(base)
        for sx in (-1, 1):
            out.append(V.rivet("hbb", 0.009, (x + sx * 0.076 - 0.005, (y0 + y1) / 2, 0.114), segs=6))
    return out


def makers_plate():
    cx, cy, z = 0.92, 2.43, 0.10
    w, h = 0.30, 0.11
    out = [V.plate("mplate", [L.rounded_rect(w, h, 0.012, 3)], 0.006, mat=BRASS, bevel=0.0015, loc=(cx, cy, z))]
    zt = z + 0.006
    out.append(V.flat("mline", L.outline_ring(w - 0.014, h - 0.014, 0.008, 0.0016, 3), zt + 0.0001, (cx, cy), INK))
    ex = cx - 0.103                         # emblem: ring + meridian
    out.append(V.flat("memb", L.circle_line(0.026, 0.0045, 28), zt + 0.0001, (ex, cy), INK))
    out.append(V.flat("memb2", [L.rounded_rect(0.0042, 0.07, 0.001, 1)], zt + 0.0001, (ex, cy), INK))
    out.append(V.text("mtxt", "MERIDIAN", 0.030, (cx + 0.03, cy + 0.016), zt + 0.0001, font=V.FONT_SERIF_B, mat=INK,
                      spacing=1.05, res=1))
    out.append(V.text("mtxt2", "№ 2 · 1961", 0.020, (cx + 0.03, cy - 0.024), zt + 0.0001, font=V.FONT_SERIF_B,
                      mat=INK, spacing=1.05, res=1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(V.rivet("mscr", 0.0055, (cx + sx * (w / 2 - 0.011), cy + sy * (h / 2 - 0.011), zt),
                               mat=BRASS_P))
    return out


def medallion():
    cx, cy, z = -0.93, 2.43, 0.10
    out = [V.glathe("medal", [(0.068, 0.0), (0.068, 0.006), (0.062, 0.011), (0.0, 0.012)], (cx, cy, z), (0, 0, 1),
                    32, BRASS, smooth=50.0)]
    zt = z + 0.0122
    out.append(V.flat("mring", L.circle_line(0.036, 0.006, 32), zt, (cx, cy), INK))
    out.append(V.flat("mmer", [L.rounded_rect(0.0055, 0.098, 0.001, 1)], zt + 0.0001, (cx, cy), INK))
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        t = V.flat("mtick", [L.rounded_rect(0.004, 0.011, 0.0005, 1)], zt, (cx + 0.051 * math.cos(a),
                   cy + 0.051 * math.sin(a)), INK, rot_z=a - math.pi / 2)
        out.append(t)
    return out


# ====================================================================== door
def build_door():
    parts = []
    bands = [PAINT, STEEL, CHROME, CHROME, CHROME, CHROME, CHROME, CHROME, CHROME, CHROME, STEEL, STEEL,
             BRASS_P, PAINT]
    body = V.glathe("door_body", DOOR_PROFILE, (0, CY, 0), (0, 0, 1), SEG, STEEL, band_mats=bands, smooth=40.0)
    parts.append(body)
    # bolt grooves, guide rails, guide straps, rivets between the bolts
    for k in range(8):
        groove = V.flat("groove", [[(0.655, -0.06), (0.926, -0.06), (0.926, 0.06), (0.655, 0.06)]], FACE + 0.0003,
                        (0, 0), INK)
        rails = [V.gbox("rail", (0.66, s * 0.035 - 0.0045, FACE), (0.92, s * 0.035 + 0.0045, BOLT_Z - 0.042),
                        CHROME, 0.0) for s in (-1, 1)]
        strap = radial_prism("strap", [(-0.066, FACE), (-0.049, FACE), (-0.049, 0.259), (0.049, 0.259),
                                       (0.049, FACE), (0.066, FACE), (0.066, 0.264), (0.058, 0.272),
                                       (-0.058, 0.272), (-0.066, 0.264)], 0.80, 0.846, STEEL)
        grp = [groove] + rails + [strap]
        for o in grp:
            o.data.transform(Matrix.Translation((0, CY, 0)) @ Matrix.Rotation(math.radians(k * 45), 4, "Z"))
        parts += grp
        x, y = polar(0.875, k * 45 + 22.5)
        parts.append(V.rivet("drv", 0.017, (x, y, FACE), mat=CHROME, segs=8))
    # handwheel rosette (static on the door)
    parts.append(V.glathe("rosette", [(0.118, FACE), (0.118, FACE + 0.006), (0.106, FACE + 0.015),
                                      (0.0, FACE + 0.021)], (HANDLE[0], HANDLE[1], 0), (0, 0, 1), 32, BRASS,
                          smooth=40.0))
    # light-pipe channels
    for s in (-1, 1):
        x0, x1 = 0.258, 0.47
        xa, xb = (x0, x1) if s > 0 else (-x1, -x0)
        parts.append(V.gbox("chan", (xa, PORT_Y - 0.017, FACE), (xb, PORT_Y + 0.017, FACE + 0.008), BRASS, 0.002))
        for w in (-1, 1):
            parts.append(V.gbox("chanw", (xa, PORT_Y + w * 0.0145 - 0.0025, FACE + 0.008),
                                (xb, PORT_Y + w * 0.0145 + 0.0025, FACE + 0.021), BRASS, 0.0012))
        parts.append(V.gbox("clip", (s * 0.36 - 0.006, PORT_Y - 0.018, FACE + 0.021),
                            (s * 0.36 + 0.006, PORT_Y + 0.018, FACE + 0.025), BRASS_P, 0.0))
    # ✦ / ☾ plates under the ports
    parts += sym_plate(-PORT_X, "star")
    parts += sym_plate(PORT_X, "moon")
    # hinge arms (door half)
    for yh in HINGE_Y:
        parts += hinge_door(yh)
    # back face: boltwork window + time lock
    parts += door_back()
    return V.part("IA_vault_door", parts, pivot=PIVOT)


def sym_plate(x, kind):
    cy = 1.418
    out = [V.plate("splate", [L.rounded_rect(0.112, 0.086, 0.01, 3)], 0.006, mat=BRASS, bevel=0.0015,
                   loc=(x, cy, FACE))]
    zt = FACE + 0.006 + 0.0001
    out.append(V.flat("sline", L.outline_ring(0.098, 0.072, 0.007, 0.0014, 3), zt, (x, cy), INK))
    if kind == "star":
        pts = []
        for i in range(8):
            a = math.pi / 2 + i * math.pi / 4
            r = 0.029 if i % 2 == 0 else 0.0075
            pts.append((r * math.cos(a), r * math.sin(a)))
        out.append(V.flat("sym", [pts], zt + 0.0001, (x, cy), INK))
    else:
        R, r, d = 0.028, 0.0235, 0.0125
        xi = (R * R - r * r + d * d) / (2 * d)
        a0 = math.atan2(math.sqrt(R * R - xi * xi), xi)
        b0 = math.atan2(math.sqrt(R * R - xi * xi), xi - d)
        outer = [(R * math.cos(a0 + (2 * math.pi - 2 * a0) * i / 18), R * math.sin(a0 + (2 * math.pi - 2 * a0) * i / 18))
                 for i in range(19)]
        inner = [(d + r * math.cos(-b0 - (2 * math.pi - 2 * b0) * i / 14), r * math.sin(-b0 - (2 * math.pi - 2 * b0) * i / 14))
                 for i in range(1, 14)]
        out.append(V.flat("sym", [outer + inner], zt + 0.0001, (x - 0.004, cy), INK))
    for sx in (-1, 1):
        out.append(V.rivet("sscr", 0.005, (x + sx * 0.045, cy, FACE + 0.006), mat=BRASS_P))
    return out


def hinge_door(yh):
    x, z = PIVOT[0], PIVOT[2]
    out = [V.glathe("dknuckle", [(0.0, -0.072), (0.07, -0.07), (0.07, 0.07), (0.0, 0.072)], (x, yh, z), (0, 1, 0), 16,
                    STEEL, smooth=50.0)]
    arm = V.gbox("arm", (x + 0.03, yh - 0.042, FACE + 0.012), (-0.70, yh + 0.042, 0.262), STEEL, 0.012, 2)
    out.append(arm)
    out.append(V.gbox("strap", (-0.79, yh - 0.08, FACE), (-0.64, yh + 0.08, FACE + 0.012), STEEL, 0.004))
    for xx in (-0.772, -0.66):
        for sy in (-1, 1):
            out.append(V.hexbolt("sbolt", 0.0105, (xx, yh + sy * 0.061, FACE + 0.012), h=0.009, washer=False))
    # brass grease cap on top of the door knuckle
    out.append(V.glathe("gcap", [(0.018, 0.0), (0.018, 0.008), (0.012, 0.012), (0.0, 0.013)], (x, yh + 0.072, z),
                        (0, 1, 0), 10, BRASS_P, smooth=60.0))
    return out


def door_back():
    out = []
    zb = -0.24
    # boltwork window (faces -Z, toward the vault)
    out.append(V.glathe("bw_ring", [(0.47, 0.0), (0.47, 0.012), (0.458, 0.02), (0.41, 0.014), (0.41, 0.0)],
                        (0, CY, zb), (0, 0, -1), 40, BRASS, smooth=40.0, cap_bottom=False, cap_top=False))
    glass = V.flat("bw_glass", [L.circle(0.412, 40)], 0.0, (0, 0), "M_Glass")
    glass.data.transform(Matrix.Translation((0, CY, zb - 0.012)) @ Matrix.Rotation(math.pi, 4, "X"))
    out.append(glass)
    cam = V.glathe("bw_cam", [(0.15, 0.0), (0.15, 0.008), (0.06, 0.012), (0.0, 0.012)], (0, CY, zb), (0, 0, -1), 24,
                   CHROME, smooth=40.0)
    out.append(cam)
    for k in range(8):
        bar = V.gbox("bw_bar", (0.12, -0.016, zb - 0.007), (0.76, 0.016, zb), STEEL, 0.0)
        guide = V.gbox("bw_guide", (0.62, -0.03, zb - 0.014), (0.68, 0.03, zb), STEEL, 0.0)
        for o in (bar, guide):
            o.data.transform(Matrix.Translation((0, CY, 0)) @ Matrix.Rotation(math.radians(k * 45), 4, "Z"))
        out += [bar, guide]
    # time lock: brass case with three clock movements behind glass
    ty = CY + 0.585
    out.append(V.gbox("tl_case", (-0.18, ty - 0.08, zb - 0.075), (0.18, ty + 0.08, zb), BRASS, 0.008, 2))
    tglass = V.flat("tl_glass", [L.rounded_rect(0.33, 0.13, 0.006, 2)], 0.0, (0, 0), "M_Glass")
    tglass.data.transform(Matrix.Translation((0, ty, zb - 0.0765)) @ Matrix.Rotation(math.pi, 4, "X"))
    out.append(tglass)
    for i, xx in enumerate((-0.11, 0.0, 0.11)):
        dial = V.flat("tl_dial", [L.circle(0.042, 20)], 0.0, (0, 0), CREAM)
        dial.data.transform(Matrix.Translation((xx, ty, zb - 0.0755)) @ Matrix.Rotation(math.pi, 4, "X"))
        hand = V.flat("tl_hand", [L.rounded_rect(0.004, 0.034, 0.001, 1, cy=0.014)], 0.0, (0, 0), INK,
                      rot_z=math.radians(40 + 95 * i))
        hand.data.transform(Matrix.Translation((xx, ty, zb - 0.0757)) @ Matrix.Rotation(math.pi, 4, "X"))
        out += [dial, hand]
    return out


# ====================================================================== door children
def build_handle():
    x, y = HANDLE
    zs = FACE + 0.088                      # wheel plane
    parts = [V.glathe("hub", [(0.05, FACE + 0.021), (0.036, FACE + 0.04), (0.036, zs - 0.012), (0.056, zs - 0.004),
                              (0.056, zs + 0.016), (0.042, zs + 0.032), (0.0, zs + 0.037)], (x, y, 0), (0, 0, 1), 20,
                      BRASS_P, smooth=45.0, cap_bottom=False)]
    R = 0.20
    for i in range(6):
        a = math.radians(90 + i * 60)
        d = (math.cos(a), math.sin(a), 0)
        sp = V.glathe("spoke", [(0.0135, 0.04), (0.0115, 0.232)], (x, y, zs), d, 8, BRASS,
                      cap_bottom=False, cap_top=False, smooth=60.0)
        knob = V.glathe("knob", [(0.0115, 0.0), (0.019, 0.006), (0.024, 0.018), (0.019, 0.03), (0.0, 0.0355)],
                        (x + 0.2245 * d[0], y + 0.2245 * d[1], zs), d, 8, BRASS_P, smooth=70.0, cap_bottom=False)
        parts += [sp, knob]
    rim = M.torus("rim", R, 0.0165, major_seg=36, minor_seg=6, mat=BRASS)
    rim.location = (x, y, zs)
    M.apply_transform(rim)
    V.A.hint(rim, 70.0)
    parts.append(rim)
    return V.part("IA_vault_handle", parts, pivot=(x, y, FACE))


def build_bolts():
    out = []
    prof = [(0.0, -0.12), (0.051, -0.12), (0.054, -0.117), (0.054, -0.093), (0.042, -0.09), (0.042, 0.096),
            (0.03, 0.115), (0.0, 0.12)]
    for k in range(8):
        a = math.radians(k * 45)
        c = (BOLT_R * math.cos(a), CY + BOLT_R * math.sin(a), BOLT_Z)
        b = V.glathe(f"bolt_{k}", prof, c, (math.cos(a), math.sin(a), 0), 12, CHROME, smooth=50.0,
                     band_mats=[BRASS_P, BRASS_P, BRASS_P, BRASS_P, CHROME, CHROME, CHROME])
        out.append(V.part(f"bolt_{k}", [b], pivot=c))
    return out


def build_disc():
    bez = V.glathe("disc_bezel", [(0.266, FACE), (0.266, 0.191), (0.257, 0.2), (0.232, 0.199), (0.2205, 0.189),
                                  (0.2205, DISC_Z - 0.002)], (DISC[0], DISC[1], 0), (0, 0, 1), 40,
                   BRASS_P, cap_bottom=False, cap_top=False, smooth=40.0)
    scr = []
    for i in range(6):
        x, y = polar(0.2445, i * 60, cy=DISC[1])
        scr.append(V.rivet("bscr", 0.0065, (x, y, 0.1995), mat=BRASS, segs=6))
    bezel = V.part("disc_bezel", [bez] + scr, pivot=(DISC[0], DISC[1], FACE))
    # the glass disc: a 48-gon fan, UV 0..1 over its bounding square (set after to_blender)
    bm = bmesh.new()
    c = bm.verts.new((DISC[0], DISC[1], DISC_Z))
    ring = [bm.verts.new((DISC[0] + DISC_R * math.cos(TA), DISC[1] + DISC_R * math.sin(TA), DISC_Z))
            for TA in [2 * math.pi * i / 48 for i in range(48)]]
    for i in range(48):
        bm.faces.new((c, ring[i], ring[(i + 1) % 48]))
    me = bpy.data.meshes.new("glass_disc")
    bm.to_mesh(me)
    bm.free()
    disc = bpy.data.objects.new("glass_disc", me)
    bpy.context.scene.collection.objects.link(disc)
    M.assign(disc, "M_Glass_Frosted")
    M.set_origin(disc, (DISC[0], DISC[1], DISC_Z))
    return bezel, disc


def build_port(side):
    s = -1 if side == "left" else 1
    x, y = s * PORT_X, PORT_Y
    prof = [(0.088, FACE), (0.088, FACE + 0.007), (0.0775, 0.171), (0.0775, 0.272), (0.069, 0.281),
            (0.058, 0.281), (0.054, 0.277), (0.054, 0.256), (0.0, 0.256)]
    bands = [BRASS, BRASS, BRASS, BRASS_P, BRASS_P, BRASS_P, INK, "M_Glass_Dark"]
    barrel = V.glathe("barrel", prof, (x, y, 0), (0, 0, 1), 24, BRASS, band_mats=bands, cap_bottom=False,
                      smooth=45.0)
    # fixed index: an enamel stripe on the barrel top and a triangle on the lip
    stripe = V.gbox("idx", (x - 0.0035, y + 0.0772, 0.2535), (x + 0.0035, y + 0.0792, 0.2705), CREAM, 0.0)
    tri = V.flat("idx_tri", [[(-0.0055, 0.0595), (0.0055, 0.0595), (0.0, 0.0685)]], 0.2812, (x, y), CREAM)
    port = V.part(f"IA_port_{side}", [barrel, stripe, tri], pivot=(x, y, FACE))
    mount = V.empty(f"port_{side}_mount", (x, y, MOUNT_Z))
    # light pipe (glass rod only: the code makes the whole mesh glow)
    xa, xb = (0.262, 0.472) if s > 0 else (-0.472, -0.262)
    pipe = V.gcyl(f"light_pipe_{side}", 0.0085, xa, xb, base=(0, y, FACE + 0.0175), axis=(1, 0, 0), segments=10,
                  mat="M_Crystal", chamfer=0.002, smooth=60.0)
    pipe = V.part(f"light_pipe_{side}", [pipe], pivot=((xa + xb) / 2, y, FACE + 0.0175))
    return port, mount, pipe


def ticks8(x, y, z, r0, r1, long_r0, name):
    out = []
    for n in range(8):
        a = math.radians(90 + 45 * n)
        if n % 4 == 0:
            ra, rb, w = long_r0, r1, 0.0052
        else:
            ra, rb, w = r0, r1, 0.0034
        ln = rb - ra
        t = V.flat(name, [L.rounded_rect(w, ln, 0.0008, 1, cy=ra + ln / 2)], z, (x, y), CREAM, rot_z=a - math.pi / 2)
        out.append(t)
        if n % 4 == 0:               # the "upright" marker: a small bar across the inner end
            bar = V.flat(name, [L.rounded_rect(0.016, 0.0034, 0.0008, 1, cy=ra - 0.0045)], z, (x, y), CREAM,
                         rot_z=a - math.pi / 2)
            out.append(bar)
    return out


def build_collars():
    out = []
    # left: one wide collar
    x, y = -PORT_X, PORT_Y
    prof = [(0.078, 0.188), (0.127, 0.188), (0.132, 0.193, "k"), (0.132, 0.243, "k"), (0.127, 0.248),
            (0.078, 0.248)]
    c = V.glathe("collar", prof, (x, y, 0), (0, 0, 1), 40, BRASS, knurl=0.0028, cap_bottom=False, cap_top=False,
                 smooth=30.0)
    out.append(V.part("IA_collar_left", [c] + ticks8(x, y, 0.2483, 0.098, 0.123, 0.09, "ctick"),
                      pivot=(x, y, 0.218)))
    # right: rotation collar + the narrower zoom ring in front of it
    x = PORT_X
    prof = [(0.078, 0.188), (0.130, 0.188), (0.135, 0.193, "k"), (0.135, 0.217, "k"), (0.130, 0.222),
            (0.078, 0.222)]
    c = V.glathe("collar", prof, (x, y, 0), (0, 0, 1), 40, BRASS, knurl=0.0028, cap_bottom=False, cap_top=False,
                 smooth=30.0)
    out.append(V.part("IA_collar_right", [c] + ticks8(x, y, 0.2223, 0.109, 0.130, 0.104, "ctick"),
                      pivot=(x, y, 0.205)))
    prof = [(0.078, 0.226), (0.101, 0.226), (0.106, 0.231, "k"), (0.106, 0.247, "k"), (0.101, 0.252),
            (0.078, 0.252)]
    zr = V.glathe("zoom", prof, (x, y, 0), (0, 0, 1), 36, BRASS_P, knurl=0.0022, cap_bottom=False, cap_top=False,
                  smooth=30.0)
    digits = []
    for n in range(5):
        a = math.radians(90 + 40 * n)
        d = V.text("zdig", str(n), 0.0135, (0.0, 0.0), 0.0, font=V.FONT_COND_B, mat=INK)
        d.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        d.data.transform(Matrix.Translation((x + 0.0905 * math.cos(a), y + 0.0905 * math.sin(a), 0.2523)))
        digits.append(d)
    out.append(V.part("IA_zoom_right", [zr] + digits, pivot=(x, y, 0.239)))
    return out


def build():
    M.reset_scene()
    V.ensure_materials()
    frame = build_frame()
    door = build_door()
    handle = build_handle()
    bolts = build_bolts()
    bezel, disc = build_disc()
    ports = [build_port("left"), build_port("right")]
    collars = build_collars()
    V.to_blender()
    # glass disc UV: 0..1 over its bounding square (u left -> right, v bottom -> top as seen from the room)
    V.uv_square(disc, DISC, (DISC_R, DISC_R))
    for ch in [handle, bezel, disc] + bolts + collars:
        V.parent(ch, door)
    for port, mount, pipe in ports:
        V.parent(port, door)
        V.parent(mount, port)
        V.parent(pipe, door)
    V.finalize_all()
    V.uv_square(disc, DISC, (DISC_R, DISC_R))
    return dict(frame=frame, door=door, handle=handle, bolts=bolts, bezel=bezel, disc=disc, ports=ports,
                collars=collars)


# ====================================================================== verification
def verify(path):
    req = ["vault_frame", "IA_vault_door", "IA_vault_handle", "glass_disc", "disc_bezel", "IA_port_left",
           "IA_port_right", "port_left_mount", "port_right_mount", "light_pipe_left", "light_pipe_right",
           "IA_collar_left", "IA_collar_right", "IA_zoom_right"] + [f"bolt_{k}" for k in range(8)]
    expect = {"IA_vault_door": PIVOT, "IA_vault_handle": (HANDLE[0], HANDLE[1], FACE),
              "port_left_mount": (-PORT_X, PORT_Y, MOUNT_Z), "port_right_mount": (PORT_X, PORT_Y, MOUNT_Z),
              "glass_disc": (DISC[0], DISC[1], DISC_Z), "IA_port_left": (-PORT_X, PORT_Y, FACE),
              "IA_port_right": (PORT_X, PORT_Y, FACE)}
    for k in range(8):
        a = math.radians(k * 45)
        expect[f"bolt_{k}"] = (BOLT_R * math.cos(a), CY + BOLT_R * math.sin(a), BOLT_Z)
    parents = {n: "IA_vault_door" for n in req if n not in ("vault_frame", "IA_vault_door", "port_left_mount",
                                                             "port_right_mount")}
    parents.update({"port_left_mount": "IA_port_left", "port_right_mount": "IA_port_right", "vault_frame": None,
                    "IA_vault_door": None})
    errs = V.verify_glb(path, required=req, identity=req, budget=BUDGET, expect=expect, parents=parents,
                        show=req)
    V.check_names(path)
    # glass disc UV range
    disc = bpy.data.objects["glass_disc"]
    us = [d.uv[0] for d in disc.data.uv_layers.active.data]
    vs = [d.uv[1] for d in disc.data.uv_layers.active.data]
    print(f"{V.TAG} glass_disc UV u {min(us):.3f}..{max(us):.3f} v {min(vs):.3f}..{max(vs):.3f}")
    lo, hi = V.mesh_bounds_godot([o for o in bpy.context.scene.objects if o.type == "MESH"])
    print(f"{V.TAG} model bounds (Godot) min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    fr = bpy.data.objects["vault_frame"]
    lo, hi = V.mesh_bounds_godot([fr])
    print(f"{V.TAG} vault_frame bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
CRYSTAL = os.path.join(M.MODELS_DIR, "lumen_crystal.glb")


def crystal_proxy(mount, name):
    """Proxy lumen crystal (Ø0.05 crystal disc in a 0.056 brass ring, 6 mm thick, face +Z) at a mount."""
    if os.path.exists(CRYSTAL):
        return V.attach(CRYSTAL, mount)
    ring = L.lathe2(name + "_ring", [(0.025, -0.003), (0.028, -0.003), (0.028, 0.003), (0.025, 0.003)], segments=32,
                    mat=BRASS_P, cap_bottom=False, cap_top=False)
    disc = L.lathe2(name + "_disc", [(0.0, -0.0025), (0.025, -0.0025), (0.025, 0.0025), (0.0, 0.0025)], segments=32,
                    mat="M_Crystal")
    tab = M.box(name + "_tab", (0.008, 0.01, 0.004), loc=(0, 0.031, 0), mat=BRASS_P, bevel=0.0008)
    M.apply_transform(tab)
    o = M.join([ring, disc, tab], name)
    o.data.transform(V.C)                     # built in Godot axes -> Blender
    o.parent = mount
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = Matrix.Identity(4)
    return o


def crystal_image(mount, glyph, name):
    """QA: the recorded image glowing on the crystal face (what ItemDress.glyph shows)."""
    path = os.path.join(V.DECALS_CH2, f"glyph_{glyph}.png")
    img = bpy.data.images.load(path, check_existing=True)
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.75, 0.95, 1.0, 1.0)
    em.inputs["Strength"].default_value = 3.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    q = L.plane(name, 0.044, 0.044, mat="M_Glass", facing="+Z")
    q.data.materials[0] = mat
    q.data.uv_layers.new(name="UVMap")
    for poly in q.data.polygons:
        for li in poly.loop_indices:
            co = q.data.vertices[q.data.loops[li].vertex_index].co
            q.data.uv_layers.active.data[li].uv = (co.x / 0.044 + 0.5, co.y / 0.044 + 0.5)
    q.data.transform(Matrix.Translation((0, 0, 0.0035)))
    q.data.transform(V.C)
    q.parent = mount
    q.matrix_parent_inverse = Matrix.Identity(4)
    q.matrix_basis = Matrix.Identity(4)
    return q


def qa_place_model():
    root = bpy.data.objects.new("qa_place", None)
    bpy.context.scene.collection.objects.link(root)
    for o in [o for o in bpy.context.scene.objects if o.parent is None and not o.name.startswith("qa")]:
        o.parent = root
    root.location = V.G(1.5, 0.0, -3.5)
    M.refresh()
    return root


REST = {}


def pose(parts, rot_left=0, rot_right=0, zoom=0, wheel=0, bolts_in=False, open_deg=0.0):
    door = parts["door"]
    for o in [door, parts["handle"]] + parts["collars"] + parts["bolts"]:
        o.matrix_basis = REST[o.name].copy()
    M.refresh()
    V.pose_rot(parts["collars"][0], "z", -45.0 * rot_left)
    V.pose_rot(parts["collars"][1], "z", -45.0 * rot_right)
    V.pose_rot(parts["collars"][2], "z", -40.0 * zoom)
    V.pose_rot(parts["handle"], "z", -120.0 * wheel)
    if bolts_in:
        for k, b in enumerate(parts["bolts"]):
            a = math.radians(45 * k)
            V.pose_slide(b, (-BOLT_TRAVEL * math.cos(a), -BOLT_TRAVEL * math.sin(a), 0.0))
    if open_deg:
        V.pose_rot(door, "y", open_deg)


def qa(parts, args):
    V.qa_begin(bounces=8)
    for o in [parts["door"], parts["handle"]] + parts["collars"] + parts["bolts"]:
        REST[o.name] = o.matrix_basis.copy()
    has_room = V.qa_room(with_vault_interior_shell=True)
    qa_place_model()
    V.qa_neighbours([("vault_interior", (0, 0, 0), 0.0), ("archivist_desk", (3.7, 0, -3.1), 0.0),
                     ("archive_pendant", (0.0, 3.6, -2.4), 0.0), ("archive_pendant", (3.0, 3.6, -2.0), 0.0),
                     ("stacks_shelving", (0.0, 0.0, 0.25), 0.0)])
    print(f"{V.TAG} QA room: {'room_archive.glb' if has_room else 'proxy shell'}")
    disc = parts["disc"]
    pipes = [p[2] for p in parts["ports"]]
    mounts = [p[1] for p in parts["ports"]]
    glow = V.glow_material("QA_PipeGlow", "CFF6FF", 6.0, base="CFF6FF")

    def disc_state(name, rl, rr, z, on=True, unlocked=False):
        img = V.disc_overlay_image(name, rl, rr, z, on, on, unlocked, clockwise=True)
        V.override_material(disc, V.emissive_image_material(name + "_m", img, 1.0))

    def lights_room():
        V.qa_clear_lights()
        V.qa_room_lights(150.0)

    def want(tag):
        return "--shots" not in args or tag in args[args.index("--shots") + 1].split(",")

    # 1 hero, closed (three-quarter from the room)
    if want("1"):
        disc_state("qa_disc0", 2, 5, 0, on=False)
        pose(parts)
        lights_room()
        V.qa_light("hero_key", "AREA", (3.2, 2.6, -1.4), 60.0, "FFE2C0", radius=1.2, target=(1.5, 1.3, -3.5))
        V.shoot(NAME, (2.75, 1.75, -1.05), (1.38, 1.30, -3.5), vfov=48)
    # 2 the in-game 'vault' view (closed, locked)
    if want("2"):
        disc_state("qa_disc0", 2, 5, 0, on=False)
        pose(parts)
        lights_room()
        V.qa_fill((1.5, 1.55, -0.9), 6.0)
        V.shoot(NAME + "_2", (1.5, 1.55, -0.9), (1.5, 1.35, -3.5), vfov=56)
    # 3 the 'vault_ports' view: crystals in both ports, start pose (left 2, right 5, zoom 0)
    crystals = []
    if want("3") or want("4"):
        crystals = [crystal_proxy(mounts[0], "qa_cr_l"), crystal_proxy(mounts[1], "qa_cr_r"),
                    crystal_image(mounts[0], "mark", "qa_img_l"), crystal_image(mounts[1], "sign", "qa_img_r")]
    if want("3"):
        disc_state("qa_disc1", 2, 5, 0)
        old = [V.override_material(p, glow) for p in pipes]
        pose(parts, rot_left=2, rot_right=5, zoom=0)
        lights_room()
        V.qa_fill((1.5, 1.65, -2.3), 9.0)
        V.shoot(NAME + "_3", (1.5, 1.65, -2.3), (1.5, 1.55, -3.4), vfov=50)
        for p, o in zip(pipes, old):
            V.restore_material(p, o)
    # 4 solved: left 0, right 2, zoom 3 -> overlay matches the engraving, bolts retracted, wheel turned
    if want("4"):
        disc_state("qa_disc2", 0, 2, 3, unlocked=True)
        old = [V.override_material(p, glow) for p in pipes]
        pose(parts, rot_left=0, rot_right=2, zoom=3, wheel=1, bolts_in=True)
        lights_room()
        V.qa_fill((1.5, 1.65, -2.3), 9.0)
        V.shoot(NAME + "_4", (1.5, 1.65, -2.3), (1.5, 1.55, -3.4), vfov=50)
        for p, o in zip(pipes, old):
            V.restore_material(p, o)
    for c in crystals:
        if c:
            bpy.data.objects.remove(c, do_unlink=True)
    # 5 bolts retracted + handwheel, close three-quarter from the right
    if want("5"):
        disc_state("qa_disc2", 0, 2, 3, on=False, unlocked=True)
        pose(parts, wheel=2, bolts_in=True)
        lights_room()
        V.qa_fill((2.9, 1.5, -2.4), 8.0)
        V.shoot(NAME + "_5", (2.85, 1.45, -2.35), (1.85, 1.15, -3.4), vfov=44)
    # 6 OPEN (-95°) from the in-game 'vault' view, interior visible
    if want("6"):
        disc_state("qa_disc3", 0, 2, 3, on=False, unlocked=True)
        pose(parts, wheel=3, bolts_in=True, open_deg=-95.0)
        lights_room()
        V.qa_light("vault_in", "POINT", (1.5, 1.6, -4.4), 70.0, "CFF6FF", radius=0.2)
        V.qa_light("vault_bulb", "POINT", (1.5, 2.3, -4.45), 20.0, "FFE2B0", radius=0.05)
        V.shoot(NAME + "_6", (1.5, 1.55, -0.9), (1.5, 1.35, -3.5), vfov=56)
    # 7 OPEN, three-quarter: the stepped plug, the back face (boltwork window, time lock), the hinge
    if want("7"):
        pose(parts, wheel=3, bolts_in=True, open_deg=-95.0)
        lights_room()
        V.qa_light("vault_in", "POINT", (1.5, 1.6, -4.4), 70.0, "CFF6FF", radius=0.2)
        V.qa_fill((2.4, 1.6, -1.2), 10.0)
        V.shoot(NAME + "_7", (2.55, 1.65, -1.05), (0.75, 1.25, -2.9), vfov=50)
    # 8 hall view (context)
    if want("8"):
        pose(parts)
        disc_state("qa_disc0", 2, 5, 0, on=False)
        lights_room()
        V.shoot(NAME + "_8", (3.8, 1.65, 1.8), (0.0, 1.3, -2.2), vfov=62)


def main():
    args = M.main_guard()
    check_swing()
    parts = build()
    V.report(NAME)
    path = V.export(NAME)
    errs = verify(path)
    if errs:
        print(f"{V.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
