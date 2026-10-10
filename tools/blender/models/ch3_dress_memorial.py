"""ch3_dress_memorial.glb — set-dressing of the Resonance Gallery's memorial wall (group G): the flat concrete-grey drum
wall becomes a framed niche so the 41 crystals glow against a darker field.

ROOM-COORDINATE model: origin = the world origin, built in place on the drum's north arc (phi from north, clockwise seen
from above; the drum's inner face is r 4.0; the memorial_wall.glb band stands at r 3.92 for phi -30 .. 30, y 0.95 .. 2.15).
The niche stops at phi +-35.2, short of the shutter tunnel mouth (phi 38 and more). Nothing here is interactive (no
colliders) and nothing stands in front of the band, the sockets or the kneeling place of Leyla's echo (r 3.37, phi 26).

  ch3_dress_memorial  (static) ONE mesh, a surface per material:
      niche            a darker plaster field (phi +-33.5, y 0 .. 3.3) between two stone pilasters, a stone cornice and a dark
                       stone plinth; the rest of the drum keeps its marbled stone
      inscription band a carved band above the figures (y 2.40 .. 2.58): abstract strokes and diamonds, no letters
      offering ledge   a stone shelf on a corbel (phi -24 .. 15, y 0.50 .. 0.56) with five candles and a posy of dried flowers in a
                       tin that Leyla left; soot above the candles
      bench            a worn walnut bench with iron end frames, facing the wall at r 2.75 (phi -10)
      grime            streaks and damp on the plaster
  memorial_candles  empty over the candles: the room puts a small warm omni there

    blender -b --factory-startup -P tools/blender/models/ch3_dress_memorial.py [-- --no-render]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ch3_dress_lib as X  # noqa: E402
from ch3_dress_lib import K, D, E, M, bpy, Matrix, Vector  # noqa: E402

NAME = "ch3_dress_memorial"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 12, 12
R_WALL = 4.0
R_PAN = 3.985
PHI_N = 33.5            # niche half-angle
PHI_P = 35.2            # outer edge of the pilasters
BENCH_R, BENCH_PHI = 2.75, -10.0
CANDLE_PHI = (-16.0, -11.0, -6.5, 0.0, 5.0)
LEDGE_Y = 0.56
CANDLES_LIGHT = K.polar(3.86, -8.0, 0.72)


def polar(r, phi, y=0.0):
    p = K.polar(r, phi, y)
    return (p.x, p.y, p.z)


def tangent_matrix(r, phi, y, lift=0.0):
    """Moves a mesh built at the origin (local x along the wall, y up, z out toward the room) onto the arc at (r, phi, y)."""
    return Matrix.Translation(polar(r, phi, y)) @ Matrix.Rotation(math.radians(-phi), 4, "Y")


# ====================================================================== the niche
def niche():
    stone, dark, plaster = [], [], []
    plaster.append(X.arc_solid("niche_field", [(R_PAN, 0.0), (R_WALL, 0.0), (R_WALL, 3.30), (R_PAN, 3.30)], -PHI_N, PHI_N, 28, X.PLASTER_DARK, drop=(0, 1)))
    for s in (-1, 1):
        a0, a1 = (PHI_N, PHI_P) if s > 0 else (-PHI_P, -PHI_N)
        stone.append(X.arc_solid("pilaster", [(3.93, 0.30), (R_WALL, 0.30), (R_WALL, 3.28), (3.93, 3.28)], a0, a1, 2, X.STONE, drop=(1,)))
        stone.append(X.arc_solid("pilaster_cap", [(3.91, 3.28), (R_WALL, 3.28), (R_WALL, 3.36), (3.91, 3.36)], a0 - 0.3 * s, a1 + 0.3 * s, 2, X.STONE, drop=(1,)))
    # cornice over the niche and a thin rail under it, plinth of dark stone below
    stone.append(X.arc_solid("cornice", [(3.90, 3.28), (R_WALL, 3.28), (R_WALL, 3.46), (3.90, 3.46), (3.935, 3.34)], -PHI_P - 0.3, PHI_P + 0.3, 30, X.STONE, drop=(1,)))
    dark.append(X.arc_solid("plinth", [(3.925, 0.0), (R_WALL, 0.0), (R_WALL, 0.30), (3.925, 0.30)], -PHI_P, PHI_P, 30, X.STONE_DARK, drop=(1,)))
    dark.append(X.arc_solid("plinth_cap", [(3.90, 0.30), (R_WALL, 0.30), (R_WALL, 0.335), (3.90, 0.335)], -PHI_P - 0.2, PHI_P + 0.2, 30, X.STONE, drop=(1,)))
    return stone, dark, plaster


# ====================================================================== inscription band: strokes and diamonds, no letters
def inscription():
    dark, stone = [], []
    y0, y1 = 2.40, 2.58
    dark.append(X.arc_solid("insc_base", [(3.962, y0), (R_PAN, y0), (R_PAN, y1), (3.962, y1)], -PHI_N + 1.5, PHI_N - 1.5, 26, X.STONE_DARK, drop=(1,)))
    rng = random.Random(7)
    phi = -PHI_N + 2.4
    yc = (y0 + y1) / 2
    heights = (0.060, 0.095, 0.125, 0.080, 0.110)
    k = 0
    while phi < PHI_N - 2.6:
        for _ in range(rng.randint(2, 5)):
            h = rng.choice(heights)
            b = K.gbox("stroke", (-0.009, -h / 2, 0.0), (0.009, h / 2, 0.011), X.STONE, 0.0)
            b.data.transform(tangent_matrix(3.962, phi, yc))
            stone.append(b)
            phi += 0.52
        phi += 0.55
        if k % 2 == 1 and phi < PHI_N - 3.0:
            d = K.gbox("diamond", (-0.016, -0.016, 0.0), (0.016, 0.016, 0.010), X.STONE, 0.0)
            d.data.transform(tangent_matrix(3.962, phi, yc) @ Matrix.Rotation(math.radians(45), 4, "Z"))
            stone.append(d)
            phi += 1.2
        k += 1
    return dark, stone


# ====================================================================== ledge, candles, flowers
def ledge():
    stone, dark, wax, flame, steel, green, velvet, brass = [], [], [], [], [], [], [], []
    stone.append(X.arc_solid("ledge", [(3.74, LEDGE_Y - 0.06), (R_PAN, LEDGE_Y - 0.06), (R_PAN, LEDGE_Y), (3.74, LEDGE_Y)], -24.0, 15.0, 18, X.STONE, drop=(1,)))
    dark.append(X.arc_solid("corbel", [(3.86, 0.34), (R_PAN, 0.34), (R_PAN, LEDGE_Y - 0.06), (3.86, LEDGE_Y - 0.06)], -22.0, 13.0, 14, X.STONE_DARK, drop=(1,)))
    rng = random.Random(11)
    for k, phi in enumerate(CANDLE_PHI):
        h = rng.choice((0.17, 0.12, 0.09, 0.14, 0.10)) if k else 0.15
        r_c = rng.uniform(0.017, 0.022)
        cx, cy, cz = polar(3.86 + rng.uniform(-0.03, 0.03), phi, LEDGE_Y)
        brass.append(K.glathe("candle_dish", [(0.0, 0.0), (0.034, 0.0), (0.040, 0.008), (0.030, 0.010), (0.0, 0.010)], (cx, cy, cz), (0, 1, 0), 10, X.BRASS, smooth=60.0))
        wax.append(K.glathe("candle", [(0.0, 0.010), (r_c, 0.010), (r_c * 1.05, h * 0.6), (r_c * 0.9, h), (r_c * 0.55, h + 0.004), (0.0, h - 0.008)],
                            (cx, cy, cz), (0, 1, 0), 8, X.CREAM, smooth=70.0))
        flame.append(K.glathe("candle_flame", [(0.0, h + 0.004), (0.005, h + 0.010), (0.0075, h + 0.022), (0.004, h + 0.036), (0.0, h + 0.050)],
                              (cx, cy, cz), (0, 1, 0), 6, X.FLAME, smooth=80.0))
    # Leyla's posy: dried flowers in a tin can at the west end of the ledge
    px, py, pz = polar(3.88, -21.0, LEDGE_Y)
    steel.append(K.glathe("tin", [(0.0, 0.0), (0.040, 0.0), (0.042, 0.004), (0.042, 0.092), (0.0385, 0.092), (0.0385, 0.008), (0.0, 0.008)],
                          (px, py, pz), (0, 1, 0), 10, X.STEEL, smooth=60.0))
    rng = random.Random(23)
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.4
        tilt = rng.uniform(0.16, 0.45)
        ln = rng.uniform(0.20, 0.27)
        top = (px + math.sin(tilt) * math.cos(a) * ln, py + 0.07 + math.cos(tilt) * ln, pz + math.sin(tilt) * math.sin(a) * ln)
        green.append(D.rod("stem", (px + 0.004 * math.cos(a), py + 0.04, pz + 0.004 * math.sin(a)), top, 0.0022, segs=3, mat=X.GREEN, caps=False, smooth=0))
        head = K.glathe("bloom", [(0.0, -0.004), (0.017, 0.0), (0.021, 0.008), (0.012, 0.016), (0.0, 0.014)], top, (0.2 * math.cos(a), 1.0, 0.2 * math.sin(a)), 7, X.VELVET, smooth=70.0)
        velvet.append(head)
    return stone, dark, wax, flame, steel, green, velvet, brass


# ====================================================================== bench
def bench():
    wood, iron = [], []
    L_, D_, H_ = 1.50, 0.40, 0.45
    for k in range(3):
        z0 = -D_ / 2 + k * (D_ / 3) + 0.006
        wood.append(K.gbox("plank", (-L_ / 2, H_ - 0.04, z0), (L_ / 2, H_, z0 + D_ / 3 - 0.012), X.WALNUT, 0.003))
    for sx in (-1, 1):
        x = sx * (L_ / 2 - 0.10)
        for sz in (-1, 1):
            iron.append(K.gbox("leg", (x - 0.022, 0.0, sz * (D_ / 2 - 0.05) - 0.022), (x + 0.022, H_ - 0.04, sz * (D_ / 2 - 0.05) + 0.022), X.STEEL, 0.003))
        iron.append(K.gbox("stretch", (x - 0.02, 0.17, -D_ / 2 + 0.05), (x + 0.02, 0.20, D_ / 2 - 0.05), X.STEEL, 0.002))
        iron.append(K.gbox("end_rail", (x - 0.03, H_ - 0.065, -D_ / 2 + 0.03), (x + 0.03, H_ - 0.04, D_ / 2 - 0.03), X.STEEL, 0.002))
    # the bench faces the wall: seat run along the tangent at phi, the wall is behind it
    m = Matrix.Translation(polar(BENCH_R, BENCH_PHI, 0.0)) @ Matrix.Rotation(math.radians(-BENCH_PHI), 4, "Y")
    X.place(wood + iron, m)
    return wood, iron


# ====================================================================== grime
def grime():
    d = X.Decals()
    def on_arc(cell, phi, y, w, h, tilt=0.0, off=0.020):
        n = (-math.sin(math.radians(phi)), 0.0, math.cos(math.radians(phi)))
        d.items.append(X.decal(cell, polar(R_PAN, phi, y), n, w, h, tilt, off))
    on_arc("streaks_a", -29.0, 2.95, 0.55, 0.55)
    on_arc("streaks_b", 29.0, 2.95, 0.55, 0.55)
    on_arc("damp_a", -26.0, 3.05, 0.55, 0.55, 10.0)
    on_arc("damp_b", 27.0, 2.9, 0.50, 0.50, -15.0)
    on_arc("soot", -8.0, 0.80, 0.62, 0.62, 0.0, 0.02)
    for phi in (-27.0, -20.0, -13.0, 13.0, 20.0, 27.0):     # narrow pieces: a wide flat quad would sink into the curved wall
        on_arc("baseboard", phi, 0.42, 0.60, 0.60, 0.0, 0.02)
    on_arc("streaks_a", -3.0, 3.1, 0.6, 0.5)
    return d.items


# ====================================================================== build
def build():
    M.reset_scene()
    X.ensure_materials()
    stone, dark, plaster = niche()
    d2, s2 = inscription()
    dark += d2
    stone += s2
    ls, ld, wax, flame, steel, green, velvet, brass = ledge()
    stone += ls
    dark += ld
    wood, iron = bench()
    dec = grime()
    objs = stone + dark + plaster + wax + flame + steel + green + velvet + brass + wood + iron + dec
    body = K.part(NAME, objs, pivot=(0.0, 0.0, 0.0))
    light = K.empty("memorial_candles", (CANDLES_LIGHT.x, CANDLES_LIGHT.y, CANDLES_LIGHT.z))
    K.to_blender()
    X.finalize()
    return dict(body=body, light=light)


# ====================================================================== QA (Cycles, qa/blender/ch3/dress_memorial*.png)
def qa(args):
    E.qa_begin()
    E.gallery_room(doors=True, array=True, console=False, memorial=True)
    cx, cy, cz = CANDLES_LIGHT
    if E.want(args, "1"):                                   # the memorial view
        V_ = E.view("memorial")
        E.gallery_lights(V_[0], fill=6.0)
        K.light("memorial_lamp", "POINT", (0.0, 2.7, -1.6), 160.0, "FFE0B8", radius=0.1)
        K.light("candles", "POINT", (cx, cy, cz), 8.0, "FFA860", radius=0.03)
        E.shoot("dress_memorial", V_[0], V_[1], V_[2])
    if E.want(args, "2"):                                   # the gallery view: niche, ledge, bench
        V_ = E.view("gallery")
        E.gallery_lights(V_[0], fill=6.0)
        K.light("memorial_lamp", "POINT", (0.0, 2.7, -1.6), 160.0, "FFE0B8", radius=0.1)
        K.light("candles", "POINT", (cx, cy, cz), 8.0, "FFA860", radius=0.03)
        E.shoot("dress_memorial_2", V_[0], V_[1], V_[2])


def main():
    args = M.main_guard()
    build()
    X.tri_report(NAME)
    path = E.export(NAME)
    req = [NAME, "memorial_candles"]
    errs = E.verify(path, required=req, identity=req, expect={NAME: (0, 0, 0), "memorial_candles": tuple(CANDLES_LIGHT)}, parents={n: None for n in req},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = E.bounds([NAME])
    print(f"{X.TAG} {NAME} bounds {lo} .. {hi}")
    print(f"{X.TAG} VERIFY {NAME} {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args)


main()
