"""shell_hall.glb — the Array Hall's shell (Chapter 4, group A): a round vault, r 14, 1970s Soviet scientific
grandeur. Contract: docs/models/ch4.md section 3 shell_hall; results: docs/models/ch4_a.md.

Built in WORLD coordinates (origin = the hall's axis on the floor, y up, north = -Z). Mesh objects:
  hall_floor    concrete disc r 14 + the Sun apse niche floor
  hall_walls    concrete: the upper wall (with the south bay and west apse openings), skirting, 12 pilasters, the niche
                wall and ceiling
  hall_dado     green painted panels 0.25 - 3.2
  hall_vault    concrete: the shallow dome (r 14 -> 1.5, y 7 -> 12), 24 radial ribs, the oculus shaft to y 14.6
  hall_trim     steel: the oculus ring, 4 ring ribs, the ventilation grilles
  hall_brass    cornice, wall bands, pilaster caps, the floor inlay (8 radial lines, 2 rings) and the numerals 1-8
  oculus_shutter_a / _b   two half discs r 1.6 at y 11.78, origin on the axis; open = a -1.7 m, b +1.7 m along X
  empties       portal_bay, portal_apse

    blender -b --factory-startup -P tools/blender/models/shell_hall.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, CONC, GREEN, STEEL, BRASS, R_HALL, WALL_TOP  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_hall"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 16000, 9, 4

STEP = 3.75                                     # degrees per wall segment
BAY_A, BAY_B = C.BAY_PHI
APSE_A, APSE_B = C.APSE_PHI
LOW_RANGES = [(BAY_B, APSE_A), (APSE_B, BAY_A + 360.0)]          # where the wall reaches the floor
PILASTERS = [7.5 + 15.0 * k for k in range(24)]
PILASTERS = [p for p in PILASTERS if not (BAY_A - 1.5 < p < BAY_B + 1.5 or APSE_A - 1.5 < p < APSE_B + 1.5)]
GRILLE_AT = [15.0 * k for k in range(24)]
GRILLE_AT = [g for g in GRILLE_AT if not (BAY_A - 8 < g < BAY_B + 8 or APSE_A - 8 < g < APSE_B + 8)]


def nseg(a0, a1):
    return max(1, int(round(abs(a1 - a0) / STEP)))


def box_at(name, phi, r, w, d, y0, y1, mat, bevel=0.01):
    """A box w wide (tangential) x d deep (radial), centred at azimuth phi / radius r."""
    o = K.gbox(name, (-w / 2, y0, -d / 2), (w / 2, y1, d / 2), mat, bevel)
    C.at_azimuth(o, phi, r)
    return o


# ====================================================================== floor
def floor_parts():
    out = []
    disc = K.revolve("floor_disc", [(0.0, 0.0), (1.75, 0.0), (3.5, 0.0), (5.25, 0.0), (7.0, 0.0), (9.0, 0.0), (11.5, 0.0), (R_HALL, 0.0)], 0, 360, 48, CONC, closed=False)
    C.orient(disc, (0, 5, 0))
    out.append(disc)
    # the apse niche floor: the half disc west of the hall circle
    out.append(K.flat_poly("niche_floor", niche_outline(), [], 0.0, CONC, up=True))
    return out


def niche_outline(n=24):
    """(x, z) loop of the apse niche: the semicircle about (APSE_CX, 0), closed by the hall circle's arc."""
    pts = [(C.APSE_CX - C.APSE_R * math.cos(t), C.APSE_R * math.sin(t))
           for t in [(-math.pi / 2) + math.pi * i / n for i in range(n + 1)]]
    arc = []
    for i in range(1, 12):
        a = APSE_A + (APSE_B - APSE_A) * i / 12.0
        p = C.polar(R_HALL, a)
        arc.append((p.x, p.z))
    return pts + arc


# ====================================================================== walls
def wall_parts():
    out = []
    # the upper wall: y0 depends on the opening
    bands = [(BAY_A, BAY_B, C.BAY_CEIL), (BAY_B, APSE_A, 3.35), (APSE_A, APSE_B, C.APSE_H), (APSE_B, BAY_A + 360.0, 3.35)]
    for k, (a0, a1, y0) in enumerate(bands):
        out.append(K.ring_wall(f"upper_{k}", R_HALL, y0, WALL_TOP - 0.3, a0, a1, nseg(a0, a1), CONC, inward=True))
    # skirting (0 - 0.25) and the concrete band above the dado (3.2 - 3.35)
    for k, (a0, a1) in enumerate(LOW_RANGES):
        out.append(K.ring_wall(f"skirt_{k}", R_HALL - 0.06, 0.0, 0.25, a0, a1, nseg(a0, a1), CONC, inward=True))
        out.append(K.ring_wall(f"band_{k}", R_HALL - 0.02, 3.2, 3.36, a0, a1, nseg(a0, a1), CONC, inward=True))
    # 12 pilasters 0.5 x 0.38, from the skirt to just under the cornice
    for k, phi in enumerate(PILASTERS):
        out.append(box_at(f"pilaster_{k}", phi, R_HALL - 0.19 + 0.02, 0.5, 0.38, 0.0, WALL_TOP - 0.35, CONC, 0.015))
    # the apse niche: a half cylinder up to APSE_H, a flat ceiling
    n = 24
    pts = [(C.APSE_CX - C.APSE_R * math.cos(t), C.APSE_R * math.sin(t))
           for t in [(-math.pi / 2) + math.pi * i / n for i in range(n + 1)]]
    out.append(C.arc_strip("niche_wall", pts, 0.0, C.APSE_H, CONC, inside_pt=(C.APSE_CX - 1.0, 1.0, 0.0), toward=True))
    out.append(K.flat_poly("niche_ceiling", niche_outline(), [], C.APSE_H, CONC, up=False))
    return out


def dado_parts():
    out = []
    for k, (a0, a1) in enumerate(LOW_RANGES):
        out.append(K.ring_wall(f"dado_{k}", R_HALL - 0.04, 0.25, 3.2, a0, a1, nseg(a0, a1), GREEN, inward=True))
    # the niche dado, to match
    n = 24
    pts = [(C.APSE_CX - (C.APSE_R - 0.03) * math.cos(t), (C.APSE_R - 0.03) * math.sin(t))
           for t in [(-math.pi / 2) + math.pi * i / n for i in range(n + 1)]]
    out.append(C.arc_strip("niche_dado", pts, 0.25, 3.2, GREEN, inside_pt=(C.APSE_CX - 1.0, 1.0, 0.0), toward=True))
    return out


# ====================================================================== vault
def vault_parts():
    out = []
    # the dome: a profile of (r, y) from the wall top to the oculus
    radii = [R_HALL - (R_HALL - C.OCULUS_R) * i / 12.0 for i in range(13)]
    prof = [(r, C.dome_y(r)) for r in radii]
    dome = K.revolve("dome", prof, 0, 360, 96, CONC, closed=False)
    C.orient(dome, (0, 3.0, 0))
    out.append(dome)
    # the wall-top return under the cornice (r 13.7 -> 14, y 6.7 -> 7.0 is the cornice's job); the oculus shaft
    shaft = K.revolve("shaft", [(C.OCULUS_R, C.VAULT_APEX), (C.OCULUS_R, C.SHAFT_TOP)], 0, 360, 24, CONC, closed=False)
    C.orient(shaft, (0, 13.0, 0))
    out.append(shaft)
    cap = K.revolve("shaft_cap", [(C.OCULUS_R, C.SHAFT_TOP), (0.0, C.SHAFT_TOP)], 0, 360, 24, CONC, closed=False)
    C.orient(cap, (0, 8.0, 0))
    out.append(cap)
    # 24 radial ribs hanging under the dome, 0.34 wide x 0.42 deep
    for k in range(24):
        out.append(radial_rib(f"rib_{k}", 7.5 + k * 15.0, 0.34, 0.42))
    return out


def radial_rib(name, phi, w, d, mat=CONC, strip=False):
    """A rib hanging under the dome (w wide, d deep); strip=True gives only the thin brass cap on its underside."""
    bm = bmesh.new()
    t = Vector((math.cos(math.radians(phi)), 0.0, math.sin(math.radians(phi))))    # tangent (horizontal)
    yc = C.dome_centre_y()
    stations = []
    n = 9
    for i in range(n + 1):
        r = (R_HALL - 0.35) - (R_HALL - 0.35 - 2.0) * i / n
        p = C.polar(r, phi, C.dome_y(r))
        down = (Vector((0.0, yc, 0.0)) - p).normalized()          # toward the sphere centre = down and inward
        a = p + t * (w / 2)
        b = p - t * (w / 2)
        c = b + down * d
        e = a + down * d
        if strip:
            stations.append([bm.verts.new(v) for v in (c - t * 0.0, e)])
        else:
            stations.append([bm.verts.new(v) for v in (a, b, c, e)])
    for i in range(n):
        s0, s1 = stations[i], stations[i + 1]
        if strip:
            bm.faces.new((s0[0], s0[1], s1[1], s1[0]))
            continue
        for (u, v) in ((0, 1), (1, 2), (2, 3), (3, 0)):
            bm.faces.new((s0[u], s0[v], s1[v], s1[u]))
    if not strip:
        bm.faces.new(stations[0])
        bm.faces.new(reversed(stations[-1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = K.obj_from_bm(name, bm, mat)
    if strip:
        C.orient(o, (0, 3.0, 0))
    return o


# ====================================================================== steel trim
def trim_parts():
    out = []
    # the oculus ring r 1.5 - 2.05, y 11.85 - 12.18 (closed profile)
    ring = K.revolve("oculus_ring", [(1.5, 11.85), (2.05, 11.85), (2.05, 12.18), (1.5, 12.18)], 0, 360, 48, STEEL, closed=True)
    out.append(_recalc(ring))
    for k, r in enumerate((11.0, 8.0, 5.0, 3.2)):
        y_in, y_out = C.dome_y(r - 0.2), C.dome_y(r + 0.2)
        prof = [(r - 0.2, y_in), (r + 0.2, y_out), (r + 0.2, y_out - 0.38), (r - 0.2, y_in - 0.38)]
        o = K.revolve(f"ribring_{k}", prof, 0, 360, 48, STEEL, closed=True)
        out.append(_recalc(o))
    # ventilation grilles between the pilasters: a frame and vertical bars, 3.0 wide x 1.5 high at y 3.9 - 5.4
    for k, phi in enumerate(GRILLE_AT):
        g = []
        for (x0, y0, x1, y1) in ((-1.5, 3.9, 1.5, 4.0), (-1.5, 5.3, 1.5, 5.4), (-1.5, 4.0, -1.4, 5.3), (1.4, 4.0, 1.5, 5.3)):
            g.append(K.gbox("gf", (x0, y0, -0.04), (x1, y1, 0.04), STEEL, 0.006))
        for i in range(1, 7):
            x = -1.4 + 2.8 * i / 7.0
            g.append(K.gbox("gb", (x - 0.025, 4.0, -0.02), (x + 0.025, 5.3, 0.02), STEEL, 0.0))
        grille = M.join(g, f"grille_{k}")
        C.at_azimuth(grille, phi, R_HALL - 0.06)
        out.append(grille)
    return out


def _recalc(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o


# ====================================================================== brass
def brass_parts():
    out = []
    # cornice: a stepped closed profile all round at the wall top
    cor = K.revolve("cornice", [(R_HALL, 6.55), (R_HALL - 0.34, 6.62), (R_HALL - 0.34, 6.78), (R_HALL - 0.10, 6.84),
                                (R_HALL - 0.10, 7.0), (R_HALL, 7.0)], 0, 360, 96, BRASS, closed=True)
    out.append(_recalc(cor))
    # two thin brass bands at y 3.2 and 3.36 (only where the wall reaches the floor)
    for k, (a0, a1) in enumerate(LOW_RANGES):
        for j, (y0, y1) in enumerate(((3.18, 3.2), (3.36, 3.39))):
            out.append(K.ring_wall(f"bandb_{k}_{j}", R_HALL - 0.025, y0, y1, a0, a1, nseg(a0, a1), BRASS, inward=True))
    # pilaster caps and bases
    for k, phi in enumerate(PILASTERS):
        out.append(box_at(f"pcap_{k}", phi, R_HALL - 0.17, 0.58, 0.44, WALL_TOP - 0.55, WALL_TOP - 0.35, BRASS, 0.0))
        out.append(box_at(f"pbase_{k}", phi, R_HALL - 0.17, 0.56, 0.42, 0.0, 0.16, BRASS, 0.0))
    # a thin brass cap under every radial rib (a 0.14 strip on the rib's underside)
    for k in range(24):
        out.append(radial_rib(f"ribcap_{k}", 7.5 + k * 15.0, 0.34, 0.425, BRASS, strip=True))
    # floor inlay: 8 radial lines, two rings, the numerals 1-8 on the apron
    for k, phi in enumerate(C.MARK_PHI):
        out.append(radial_line(f"mark_{k + 1}", phi, 3.4, 11.4, 0.07))
        out.append(floor_numeral(f"num_{k + 1}", k + 1, phi, 12.4, 0.55))
    for nm, r in (("inner_ring", 3.3), ("outer_ring", 11.5)):
        o = K.revolve(nm, [(r - 0.035, 0.004), (r + 0.035, 0.004)], 0, 360, 96, BRASS, closed=False)
        C.orient(o, (0, 5, 0))
        out.append(o)
    return out


def radial_line(name, phi, r0, r1, w):
    a, b = C.polar(r0, phi, 0.004), C.polar(r1, phi, 0.004)
    t = Vector((math.cos(math.radians(phi)), 0.0, math.sin(math.radians(phi)))) * (w / 2)
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in (a - t, a + t, b + t, b - t)]
    bm.faces.new(vs)
    o = K.obj_from_bm(name, bm, BRASS)
    C.orient(o, (0, 5, 0))
    return o


def floor_numeral(name, d, phi, r, h):
    """A flat digit lying on the floor at azimuth phi / radius r, its top pointing outward."""
    o = C.N.digit_obj(name, d, h, 0.0, BRASS)
    o.data.transform(Matrix.Rotation(math.radians(-90.0), 4, "X"))        # lie on the floor, top toward north (-Z)
    o.data.transform(Matrix.Rotation(math.radians(-phi), 4, "Y"))         # top toward azimuth phi, outward
    o.data.transform(Matrix.Translation(C.polar(r, phi, 0.004)))
    C.orient(o, (0, 5, 0))
    return o


# ====================================================================== shutters
def shutter(name, west: bool):
    sgn = -1.0 if west else 1.0
    n = 16
    outer = [(sgn * 1.6 * math.sin(math.pi * i / n), 1.6 * math.cos(math.pi * i / n)) for i in range(n + 1)]
    # half disc in the XZ plane: x = sgn * 1.6 sin t, z = 1.6 cos t  (t 0..pi gives the half x of sign sgn)
    bm = bmesh.new()
    lo = [bm.verts.new((x, 11.78, z)) for (x, z) in outer]
    hi = [bm.verts.new((x, 11.84, z)) for (x, z) in outer]
    bm.faces.new(lo)
    bm.faces.new(reversed(hi))
    for i in range(len(outer)):
        j = (i + 1) % len(outer)
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts = [K.obj_from_bm(name + "_plate", bm, STEEL)]
    for k in range(4):                                                       # stiffening ribs on the underside
        x = sgn * (0.35 + 0.33 * k)
        parts.append(K.gbox("sr", (x - 0.025, 11.70, -1.5 * math.sqrt(max(0.0, 1 - (x / 1.6) ** 2))),
                            (x + 0.025, 11.78, 1.5 * math.sqrt(max(0.0, 1 - (x / 1.6) ** 2))), STEEL, 0.0))
    parts.append(K.gbox("sr_mid", (min(0.0, sgn * 1.55), 11.70, -0.025), (max(0.0, sgn * 1.55), 11.78, 0.025), STEEL, 0.0))
    return K.part(name, parts, pivot=(0.0, 11.78, 0.0))


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    floor = C.merge("hall_floor", floor_parts())
    walls = C.merge("hall_walls", wall_parts())
    dado = C.merge("hall_dado", dado_parts())
    vault = C.merge("hall_vault", vault_parts())
    trim = C.merge("hall_trim", trim_parts())
    brass = C.merge("hall_brass", brass_parts())
    sa, sb = shutter("oculus_shutter_a", True), shutter("oculus_shutter_b", False)
    pb = K.empty("portal_bay", (0.0, 3.0, 13.2))
    pa = K.empty("portal_apse", (-13.6, 2.0, 0.0), rot_deg=(0.0, -90.0, 0.0))
    K.to_blender()
    C.finalize()
    return dict(floor=floor, walls=walls, dado=dado, vault=vault, trim=trim, brass=brass, sa=sa, sb=sb)


def verify(path):
    req = ["hall_floor", "hall_walls", "hall_dado", "hall_vault", "hall_trim", "hall_brass", "oculus_shutter_a",
           "oculus_shutter_b", "portal_bay", "portal_apse"]
    expect = {"oculus_shutter_a": (0, 11.78, 0), "oculus_shutter_b": (0, 11.78, 0), "portal_bay": (0, 3.0, 13.2),
              "portal_apse": (-13.6, 2.0, 0.0)}
    errs = C.verify(path, required=req, identity=[n for n in req if n != "portal_apse"], expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    lo, hi = C.bounds(["hall_floor", "hall_walls", "hall_vault"])
    print(f"{C.TAG} hall bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    K.pose_slide(parts["sa"], (-1.7, 0.0, 0.0))        # the VENT line is live: the shutters are open
    K.pose_slide(parts["sb"], (1.7, 0.0, 0.0))
    # proxy for the Core so the hall has its real light colour
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False                # the Core's own light sits inside the proxy
    C.qa_floor_nonormal("hall_floor")
    if C.want(args, "1"):                      # the bridge view (from the bay mouth)
        cam, tgt, fov = C.view("bridge")
        C.lights(cam, fill=60.0, ambient=0.25)
        C.shoot(NAME, cam, tgt, fov, samples=int(os.environ.get("MR_S", "32")), res=(int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640"))))
    if C.want(args, "2"):                      # hero: low on the north apron, looking up at the vault and the oculus
        cam, tgt, fov = (0.0, 1.5, -10.0), (0.0, 7.5, 5.0), 70
        C.lights(cam, fill=30.0, ambient=0.12)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=int(os.environ.get("MR_S", "32")), res=(int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640"))))
    if C.want(args, "3"):                      # the Sun apse and the west wall
        cam, tgt, fov = C.view("apse")
        C.lights(cam, fill=40.0, ambient=0.25)
        C.shoot(NAME + "_3", cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
