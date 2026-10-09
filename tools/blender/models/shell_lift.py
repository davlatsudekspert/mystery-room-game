"""shell_lift.glb — the lift lobby, the shaft above the cage, the two passage linings and the intro shaft, in WORLD
coordinates (place at the origin, yaw 0). Contract: docs/models/ch3.md §3 shell_lift (+ §1.1 lobby and passages,
§2 lift_w / lift_e); results: docs/models/ch3_a.md.

  lobby_floor      chequer plate x ±6.6, z 4.7 .. 7.4 at y 0, plus the two bridge ramps (1.0 long) from the cage
                   floor (y 0.25 at x ±1.15) down to the lobby, with curbs (moved here from freight_lift: they hide with
                   the lobby during the intro)
  lobby_walls      concrete walls (plinth, board-form lift lines, a cornice step), openings for the two passages
  lobby_ceiling    concrete at y 3.0 with the shaft opening x ±1.25, z 4.85 .. 7.15 and two beams flanking it
  lift_shaft       rock walls of the shaft above the cage, y 3.0 .. 12, with a rock cap (the hoist rails are in
                   freight_lift's static cage)
  IA_passage_w/_e  steel linings of the Choir / Nursery passages x ∈ [-6.3, -4.8] / [4.8, 6.3], z 4.0 .. 4.7, y 0 .. 2.6
  intro_shaft      open rock box just outside the cage (x ±1.45, z 4.75 .. 7.25, y -6 .. 3) with guide rails and
                   2 x 5 steel lamp cages; the code slides it +Y by up to 9.0 during the intro descent
  intro_bulbs      the ten bulbs (M_Steel_Dark, code emission), CHILD of intro_shaft so they slide with it

    blender -b --factory-startup -P tools/blender/models/shell_lift.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_lift"
TRI_BUDGET, SURF_BUDGET = 7000, 8
CONC, ROCK, CHEQ, STEEL = K.CONC, K.ROCK, K.CHEQ, K.STEEL
X0, X1, Z0, Z1, H = -6.6, 6.6, 4.7, 7.4, 3.0
SHAFT = (-1.25, 1.25, 4.85, 7.15)
PASS = {"w": (-6.3, -4.8), "e": (4.8, 6.3)}
PASS_Z0, PASS_H = 4.0, 2.6
CAGE_Z = 6.0
INTRO = (-1.45, 1.45, 4.75, 7.25, -6.0, 3.0)
INTRO_LAMP_Y = [-5.1, -3.3, -1.5, 0.3, 2.1]
WALL_PROFILE = [(-0.02, 0.0), (-0.02, 0.15), (0.0, 0.17), (0.0, 1.20), (0.01, 1.21), (0.01, 1.23), (0.0, 1.24),
                (0.0, 2.40), (0.01, 2.41), (0.01, 2.43), (0.0, 2.44), (0.0, PASS_H), (0.0, 2.88), (-0.06, 2.94), (-0.06, H)]


# ====================================================================== lobby
def lobby_floor():
    parts = [K.flat_poly("floor", [(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)], [], 0.0, CHEQ, up=True)]
    for sx in (-1, 1):
        xa, xb = sx * 1.15, sx * 2.15
        za, zb = CAGE_Z - 0.80, CAGE_Z + 0.80
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in ((xa, 0.25, za), (xb, 0.002, za), (xb, 0.002, zb), (xa, 0.25, zb))]
        bm.faces.new(v if sx > 0 else list(reversed(v)))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ramp = K.obj_from_bm("ramp", bm, CHEQ)
        if ramp.data.polygons[0].normal.y < 0:
            ramp.data.polygons[0].flip()
        parts.append(ramp)
        # ramp edges and curbs (steel angle look in chequer plate)
        for z in (za, zb):
            c = K.gbox("curb", (-0.5, 0.0, -0.025), (0.5, 0.06, 0.025), CHEQ, 0.004)
            ang = math.atan2(0.25, 1.0)
            c.data.transform(Matrix.Translation(((xa + xb) / 2, 0.125, z)) @ Matrix.Rotation(-sx * ang, 4, "Z"))
            parts.append(c)
        parts.append(K.gbox("toe", (min(xb, xb + sx * 0.04), 0.0, za), (max(xb, xb + sx * 0.04), 0.008, zb), CHEQ, 0.002))
    return K.part("lobby_floor", parts)


def lobby_walls():
    path = [(X0, Z0), (PASS["w"][0], Z0), (PASS["w"][1], Z0), (PASS["e"][0], Z0), (PASS["e"][1], Z0), (X1, Z0), (X1, Z1),
            (X0, Z1)]
    w = K.wall_sweep("walls", path, WALL_PROFILE, CONC)

    def opening(c, n):
        return abs(c.z - Z0) < 0.1 and c.y < PASS_H and any(a < c.x < b for a, b in PASS.values())
    K.delete_faces_where(w, opening)
    parts = [w]
    # pilasters on the long walls (x = ±3.2) and a concrete lintel band over the passages
    for z0, sz in ((Z0, 1), (Z1, -1)):
        for x in (-3.2, 3.2):
            a, b = sorted((z0, z0 + sz * 0.14))
            parts.append(K.gbox("pil", (x - 0.22, 0.0, a), (x + 0.22, H, b), CONC, 0.01))
    for a, b in PASS.values():
        parts.append(K.gbox("lintel", (a - 0.15, PASS_H, Z0), (b + 0.15, PASS_H + 0.22, Z0 + 0.05), CONC, 0.008))
    return K.part("lobby_walls", parts)


def lobby_ceiling():
    xs0, xs1, zs0, zs1 = SHAFT
    parts = [K.flat_poly("ceil", [(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)], [[(xs0, zs0), (xs1, zs0), (xs1, zs1), (xs0, zs1)]],
                         H, CONC, up=False)]
    for sx in (-1, 1):
        a, b = sorted((sx * 1.25, sx * 1.55))
        parts.append(K.gbox("beam", (a, 2.62, Z0), (b, H, Z1), CONC, 0.012))
    for x in (-3.2, 3.2):
        parts.append(K.gbox("beam", (x - 0.15, 2.70, Z0), (x + 0.15, H, Z1), CONC, 0.012))
    # the shaft mouth reveal (concrete collar 0.3 deep)
    parts.append(K.quad("rev_n", (0.0, H + 0.15, zs0), (1, 0, 0), (0, 1, 0), xs1 - xs0, 0.3, CONC))
    parts.append(K.quad("rev_s", (0.0, H + 0.15, zs1), (-1, 0, 0), (0, 1, 0), xs1 - xs0, 0.3, CONC))
    parts.append(K.quad("rev_w", (xs0, H + 0.15, (zs0 + zs1) / 2), (0, 0, -1), (0, 1, 0), zs1 - zs0, 0.3, CONC))
    parts.append(K.quad("rev_e", (xs1, H + 0.15, (zs0 + zs1) / 2), (0, 0, 1), (0, 1, 0), zs1 - zs0, 0.3, CONC))
    return K.part("lobby_ceiling", parts)


def lift_shaft():
    xs0, xs1, zs0, zs1 = SHAFT
    y0, y1 = H + 0.3, 12.0
    parts = [K.rock_panel("sh_n", (xs0, y0, zs0), (1, 0, 0), (0, 1, 0), xs1 - xs0, y1 - y0, 5, 14, 0.06, 11),
             K.rock_panel("sh_s", (xs1, y0, zs1), (-1, 0, 0), (0, 1, 0), xs1 - xs0, y1 - y0, 5, 14, 0.06, 12),
             K.rock_panel("sh_w", (xs0, y0, zs1), (0, 0, -1), (0, 1, 0), zs1 - zs0, y1 - y0, 5, 14, 0.06, 13),
             K.rock_panel("sh_e", (xs1, y0, zs0), (0, 0, 1), (0, 1, 0), zs1 - zs0, y1 - y0, 5, 14, 0.06, 14)]
    parts.append(K.flat_poly("sh_cap", [(xs0, zs0), (xs1, zs0), (xs1, zs1), (xs0, zs1)], [], y1, ROCK, up=False))
    return K.part("lift_shaft", parts)


def passage(side):
    a, b = PASS[side]
    z0, z1 = PASS_Z0, Z0
    p = []
    t = 0.02
    p.append(K.gbox("pfloor", (a, -0.01, z0), (b, 0.008, z1), STEEL, 0.003))
    p.append(K.gbox("pwall", (a, 0.0, z0), (a + t, PASS_H, z1), STEEL, 0.003))
    p.append(K.gbox("pwall", (b - t, 0.0, z0), (b, PASS_H, z1), STEEL, 0.003))
    p.append(K.gbox("pceil", (a, PASS_H - t, z0), (b, PASS_H, z1), STEEL, 0.003))
    fw = 0.09
    for z, d in ((z0, -1), (z1, 1)):            # angle frames on the hall face (z 4.0) and the lobby face (z 4.7)
        za, zb = sorted((z, z + d * 0.012))
        p.append(K.gbox("pfr", (a - fw, 0.0, za), (a + t, PASS_H + fw, zb), STEEL, 0.004))
        p.append(K.gbox("pfr", (b - t, 0.0, za), (b + fw, PASS_H + fw, zb), STEEL, 0.004))
        p.append(K.gbox("pfr", (a - fw, PASS_H - t, za), (b + fw, PASS_H + fw, zb), STEEL, 0.004))
        for y in (0.35, 1.30, 2.25):
            for x in (a - fw / 2, b + fw / 2):
                p.append(K.rivet("prv", 0.009, (x, y, zb if d > 0 else za), normal=(0, 0, d), segs=5))
    # seam strips on the lining walls
    for x, n in ((a + t, 1), (b - t, -1)):
        xa, xb = sorted((x, x + n * 0.006))
        p.append(K.gbox("pseam", (xa, 0.0, (z0 + z1) / 2 - 0.03), (xb, PASS_H, (z0 + z1) / 2 + 0.03), STEEL, 0.002))
    return K.part(f"IA_passage_{side}", p, pivot=((a + b) / 2, 0.0, (z0 + z1) / 2))


# ====================================================================== intro shaft
def intro():
    xa, xb, za, zb, y0, y1 = INTRO
    h = y1 - y0
    rock = [K.rock_panel("in_w", (xa, y0, zb), (0, 0, -1), (0, 1, 0), zb - za, h, 5, 16, 0.07, 21),
            K.rock_panel("in_e", (xb, y0, za), (0, 0, 1), (0, 1, 0), zb - za, h, 5, 16, 0.07, 22),
            K.rock_panel("in_n", (xa, y0, za), (1, 0, 0), (0, 1, 0), xb - xa, h, 5, 16, 0.07, 23),
            K.rock_panel("in_s", (xb, y0, zb), (-1, 0, 0), (0, 1, 0), xb - xa, h, 5, 16, 0.07, 24)]
    steel = []
    for sz, z in ((1, za), (-1, zb)):           # guide rails on the north / south rock
        a0, a1 = sorted((z, z + sz * 0.10))
        steel.append(K.gbox("irail", (-0.05, y0, a0), (0.05, y1, a1), STEEL, 0.0))
        for y in range(-5, 3, 2):
            b0, b1 = sorted((z, z + sz * 0.03))
            steel.append(K.gbox("ibrk", (-0.12, y - 0.06, b0), (0.12, y + 0.06, b1), STEEL, 0.0))
    bulbs = []
    for sx, x in ((1, xa), (-1, xb)):           # a column of five caged bulkhead lamps on each gate-side wall
        for y in INTRO_LAMP_Y:
            c = (x + sx * 0.06, y, CAGE_Z)
            a0, a1 = sorted((x, x + sx * 0.03))
            steel.append(K.gbox("lback", (a0, y - 0.14, CAGE_Z - 0.10), (a1, y + 0.14, CAGE_Z + 0.10), STEEL, 0.006))
            for k in range(3):
                zz = CAGE_Z - 0.07 + 0.07 * k
                steel.append(K.V.tube("lbar", [(x + sx * 0.03, y + 0.11, zz), (x + sx * 0.13, y + 0.07, zz),
                                               (x + sx * 0.13, y - 0.07, zz), (x + sx * 0.03, y - 0.11, zz)], 0.006,
                                      sides=4, mat=STEEL))
            bulbs.append(K.glathe("ibulb", [(0.0, -0.05), (0.035, -0.035), (0.04, 0.0), (0.03, 0.035), (0.0, 0.05)],
                                  (x + sx * 0.085, y, CAGE_Z), (sx, 0, 0), 8, STEEL, smooth=70.0))
    sh = K.part("intro_shaft", rock + steel, pivot=(0.0, 0.0, CAGE_Z))
    bl = K.part("intro_bulbs", bulbs, pivot=(0.0, 0.0, CAGE_Z))
    return sh, bl


def build():
    M.reset_scene()
    K.ensure_materials()
    out = dict(floor=lobby_floor(), walls=lobby_walls(), ceiling=lobby_ceiling(), shaft=lift_shaft(),
               pw=passage("w"), pe=passage("e"))
    out["intro"], out["bulbs"] = intro()
    K.to_blender()
    K.parent(out["bulbs"], out["intro"])
    A.finalize_uv()
    return out


def verify(path):
    req = ["lobby_floor", "lobby_walls", "lobby_ceiling", "lift_shaft", "IA_passage_w", "IA_passage_e", "intro_shaft",
           "intro_bulbs"]
    errs = K.V.verify_glb(path, required=req, identity=req, parents={"intro_bulbs": "intro_shaft"},
                          expect={"intro_shaft": (0.0, 0.0, CAGE_Z), "intro_bulbs": (0.0, 0.0, CAGE_Z)}, show=req)
    errs += K.facts(path, TRI_BUDGET, 9)
    for n in ("intro_shaft", "IA_passage_w", "IA_passage_e", "lobby_floor"):
        lo, hi = K.V.mesh_bounds_godot([bpy.data.objects[n]])
        print(f"{K.TAG} {n} bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    K.qa_begin(bounces=6)
    K.qa_import("freight_lift", (0.0, 0.0, 6.0), 0.0, prefix="qa_fl_")
    K.qa_import("shell_choir", (0, 0, 0), 0.0, prefix="qa_sc_")
    K.qa_import("shell_nursery", (0, 0, 0), 0.0, prefix="qa_sn_")
    for o in list(bpy.data.objects):
        if o.name.startswith("qa_fl_cage_bulb"):
            K.override(o, K.glow("qa_bulb", "FFE0B0", 12.0))
    bulbs = parts["bulbs"]

    def lights(cam=None, intro=False):
        K.clear_lights()
        K.light("cage_lamp", "POINT", (0.0, 2.3, 6.0), 110.0, "FFD7A0", radius=0.05)
        if not intro:
            K.light("hall_w", "POINT", (-5.5, 2.2, 2.6), 160.0, "FFC890", radius=0.1)
            K.light("hall_e", "POINT", (5.5, 2.2, 2.6), 120.0, "DDE8F0", radius=0.1)
            K.light("lobby_fill", "AREA", (0.0, 2.9, 6.0), 60.0, "FFE0B8", radius=6.0, target=(0.0, 0.0, 6.0))
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 8.0, "FFE2C2", radius=0.2)

    def show_intro(on, slide=0.0):
        for o in (parts["floor"], parts["walls"], parts["ceiling"], parts["shaft"], parts["pw"], parts["pe"]):
            o.hide_render = on
        parts["intro"].hide_render = not on
        bulbs.hide_render = not on
        parts["intro"].location = K.G(0.0, slide, CAGE_Z)
        for o in bpy.data.objects:
            if o.name.startswith(("qa_sc_", "qa_sn_")):
                o.hide_render = on
        M.refresh()

    if K.want(args, "1"):        # lobby hero from the west passage
        show_intro(False)
        lights()
        K.shoot(NAME, (-5.2, 1.7, 5.15), (0.0, 1.2, 6.4), vfov=62)
    if K.want(args, "2"):        # lobby from the east, looking west (Choir passage at the far end)
        show_intro(False)
        lights()
        K.shoot(NAME + "_2", (5.6, 1.7, 7.0), (-2.5, 1.2, 5.2), vfov=62)
    if K.want(args, "3"):        # intro: lift_w during the descent (intro_shaft shown, slid +4.0, bulbs lit)
        show_intro(True, 4.0)
        old = K.override(bulbs, K.glow("qa_ibulb", "FFD49A", 25.0))
        lights((0.5, 1.6, 6.4), intro=True)
        for k, y in enumerate(INTRO_LAMP_Y):
            for x in (-1.3, 1.3):
                K.light(f"ib_{k}_{x}", "POINT", (x, y + 4.0, CAGE_Z), 25.0, "FFD49A", radius=0.05)
        K.shoot(NAME + "_3", (0.5, 1.6, 6.4), (-1.1, 1.35, 6.0), vfov=62)
        K.restore(bulbs, old)
        show_intro(False)
    if K.want(args, "4"):        # looking up the shaft from the lobby
        show_intro(False)
        lights()
        K.light("shaft_top", "POINT", (0.0, 9.0, 6.0), 400.0, "FFD7A0", radius=0.1)
        K.light("shaft_mid", "POINT", (0.6, 5.5, 6.6), 150.0, "FFD7A0", radius=0.1)
        K.shoot(NAME + "_4", (0.55, 1.45, 6.55), (0.0, 8.0, 6.0), vfov=62)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
