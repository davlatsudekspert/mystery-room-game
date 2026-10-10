"""gallery_console.glb — Strand's resonance console in the Gallery (F, H2/H3): a walnut desk with a sloped top and a
vertical instrument board carrying the round CRT scope, the two frequency knobs (X = the Choir, Y = the Nursery) and
two lamps; on the slope the crystal cradle, Strand's brass plate (the target figure) and the finale socket.
Contract: docs/models/ch3.md §8 gallery_console (+ §1.3 console scope / cradle, §2 console / scope / strand_plate /
cradle / finale views, §11 H2 lissajous.gdshader); results: docs/models/ch3_f.md.

At (0, 0, 2.6), yaw 0; the front (+Z) faces south, the operator stands south and looks north over the shaft. Origin =
floor level at the footprint centre. Body 1.40 w x 0.60 d; the slope runs from the front edge (z 0.30, y 0.92) up to
(z -0.06, y 1.02) (15.5 deg); the board stands at z -0.12 .. -0.07, y 1.02 .. 1.48 (face z -0.07).

  gallery_console  (static, M_Wood_Walnut / M_Brass_Aged / M_Glass_Dark) the cabinet with plinth and raised panels,
                   brass nosing and grille, the board with the scope bezel and the dark glass margin, the knob bosses,
                   scale rings and brass numerals 1-5 (150, 120, 90, 60, 30 deg round each knob), a tube-rack
                   pictogram under X and a crystal pictogram under Y, the two lamp bezels, and the keystone pad of the
                   finale socket (level top y 0.98, a boss 0.0202 high for the crystal's foot)
  scope_screen     round CRT face Ø 0.24 at (0, 1.25, -0.065), UV 0..1 over its bounding square, M_Shader_Quad
  IA_knob_x / _y   knurled brass knobs Ø 0.07, axis +Z, origin (∓0.34, 1.20, -0.06), pointer at 12 o'clock at rest
                   (value 3); value v = (60 - 30 (v - 1)) deg about local +Z
  IA_cradle        brass pedestal with three claws, origin (0, 0.98, 0.14) = the seat top (level)
  cradle_ring      thin brass ring on the slope round the cradle (code glow)
  IA_strand_plate  brass plate 0.18 x 0.14 on the slope, origin (-0.42, 0.97, 0.16) = the face centre; the face is a
                   UV 0..1 M_Shader_Quad (u -> +X, v up the slope); frame, four screws, a tab with Strand's mark
  cradle_mount     empty (0, 1.0369, 0.14): the nursery_crystal's origin (its bottom is 0.0569 below it) on the seat
  choice_mount     empty (0.42, 1.0571, 0.16): the strand_fork's origin (its ball bottom is 0.0771 below it) on the pad
                   (0.98); a nursery_crystal's foot (0.0569 below) then rests on the boss
  lamp_choir / lamp_nursery   jewels (M_Glass_Dark) at (∓0.62, 1.42, -0.065)

    blender -b --factory-startup -P tools/blender/models/gallery_console.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "gallery_console"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 8000, 12, 4
WALNUT, BRASS, GLASS, SHQ = E.WALNUT, E.BRASS, E.GLASS_DARK, E.SHQ

HX = 0.70
Z_F, Y_F, Z_B, Y_B = 0.30, 0.92, -0.06, 1.02
K_SLOPE = (Y_B - Y_F) / (Z_F - Z_B)
ALPHA = math.atan(K_SLOPE)
NORMAL = Vector((0.0, math.cos(ALPHA), math.sin(ALPHA)))         # the slope's up-normal (leans toward the operator)
BOARD = (-0.66, 1.02, -0.12, 0.66, 1.48, -0.07)                    # x0, y0, z0, x1, y1, z1
BZ = -0.07                                                         # board face
SCOPE_C = (0.0, 1.25, -0.065)
SCOPE_R = 0.12
KNOB = {"x": (-0.34, 1.20, -0.06), "y": (0.34, 1.20, -0.06)}
KNOB_R, KNOB_H = 0.035, 0.030
NUMERAL_ANG = {1: 150, 2: 120, 3: 90, 4: 60, 5: 30}
NUMERAL_R = 0.066
LAMP = {"choir": (-0.62, 1.42, -0.065), "nursery": (0.62, 1.42, -0.065)}
CRADLE = (0.0, 0.98, 0.14)
SEAT_TOP = 0.98
CRYSTAL_BOTTOM = 0.0569                                            # nursery_crystal: origin -> bottom (ch3_g.md)
FORK_BOTTOM = 0.0771                                               # strand_fork ball underside
CRADLE_MOUNT = (0.0, SEAT_TOP + CRYSTAL_BOTTOM, 0.14)
CHOICE = (0.42, SEAT_TOP, 0.16)                                    # the pad's centre (top level)
CHOICE_MOUNT = (0.42, SEAT_TOP + FORK_BOTTOM, 0.16)
BOSS_H = FORK_BOTTOM - CRYSTAL_BOTTOM                              # 0.0202
PLATE_C = (-0.42, 0.97, 0.16)
PLATE_W, PLATE_H = 0.18, 0.14


def slope_y(z):
    return Y_F + (Z_F - z) * K_SLOPE


def circle(r, n=24, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def on_slope(o, centre):
    """Move a mesh built facing +Z (local XY = its face, +Y = up the slope) onto the slope at `centre`."""
    return D.place_xz(o, centre, tuple(NORMAL))


# ====================================================================== pictograms (relief, facing +Z)
def rack_pictogram(cx, cy, z, mat=BRASS, depth=0.0015):
    """Tube rack: a base bar, a top bar and three standing tubes (0.054 x 0.040)."""
    out = []
    for (x0, y0, x1, y1) in ((-0.027, -0.020, 0.027, -0.014), (-0.027, 0.010, 0.027, 0.016),
                             (-0.020, -0.014, -0.012, 0.010), (-0.004, -0.014, 0.004, 0.010), (0.012, -0.014, 0.020, 0.010)):
        out.append(K.gbox("rk", (cx + x0, cy + y0, z), (cx + x1, cy + y1, z + depth), mat, 0.0))
    # three test tubes standing in the rack, drawn as round-topped bars above the top bar
    for x in (-0.016, 0.0, 0.016):
        out.append(K.gbox("rk_tube", (cx + x - 0.003, cy + 0.016, z), (cx + x + 0.003, cy + 0.030, z + depth), mat, 0.0))
    return out


def crystal_pictogram(cx, cy, z, mat=BRASS, depth=0.0015):
    """A hexagonal crystal with pointed ends, outlined, with one facet line (0.022 x 0.046)."""
    outer = [(0.0, 0.026), (0.011, 0.014), (0.011, -0.014), (0.0, -0.026), (-0.011, -0.014), (-0.011, 0.014)]
    inner = [(0.0, 0.019), (0.0065, 0.0115), (0.0065, -0.0115), (0.0, -0.019), (-0.0065, -0.0115), (-0.0065, 0.0115)]
    o = K.plate("cr_out", [outer, list(reversed(inner))], depth, z0=z, mat=mat, bevel=0.0, drop_bottom=True, loc=(cx, cy, 0.0))
    f = K.gbox("cr_facet", (cx - 0.0007, cy - 0.016, z), (cx + 0.0007, cy + 0.016, z + depth), mat, 0.0)
    return [o, f]


# ====================================================================== static body
def body():
    wal, brs, gls = [], [], []
    # cabinet: side profile (z, y) extruded along x; the board stands on its back deck
    prof = [(-0.30, 0.08), (Z_F, 0.08), (Z_F, Y_F), (Z_B, Y_B), (-0.30, Y_B)]
    wal.append(B.prism_x("cabinet", prof, -HX, HX, WALNUT))
    wal.append(K.gbox("plinth", (-0.68, 0.0, -0.28), (0.68, 0.08, 0.28), WALNUT, 0.0))
    for (x0, x1) in ((-0.64, -0.28), (-0.22, 0.22), (0.28, 0.64)):                          # raised front panels
        wal.append(K.gbox("fpanel", (x0, 0.16, Z_F), (x1, 0.84, Z_F + 0.008), WALNUT, 0.003))
    for sx in (-1, 1):                                                                      # raised side panels
        a, b = sorted((sx * HX, sx * (HX + 0.008)))
        wal.append(K.gbox("spanel", (a, 0.16, -0.22), (b, 0.90, 0.22), WALNUT, 0.003))
    x0, y0, z0, x1, y1, z1 = BOARD
    wal.append(K.gbox("board", (x0, y0, z0), (x1, y1, z1), WALNUT, 0.004))
    # brass: nosing, plinth strip, grille, handles, board cap
    brs.append(K.gcyl("nosing", 0.009, -HX, HX, base=(0.0, Y_F + 0.004, Z_F), axis=(1, 0, 0), segments=8, mat=BRASS))
    brs.append(K.gbox("plinth_strip", (-0.69, 0.08, Z_F - 0.005), (0.69, 0.088, Z_F + 0.012), BRASS, 0.0))
    for k in range(6):
        y = 0.40 + 0.075 * k
        brs.append(K.gbox("grille", (-0.15, y, Z_F + 0.008), (0.15, y + 0.016, Z_F + 0.013), BRASS, 0.0))
    for sx in (-1, 1):
        kn = K.glathe("pull", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.010), (0.012, 0.016), (0.012, 0.020), (0.0, 0.021)],
                      (sx * 0.46, 0.50, Z_F + 0.008), (0, 0, 1), 8, BRASS, smooth=50.0)
        brs.append(kn)
    brs.append(K.gbox("board_cap", (x0 - 0.008, y1, z0 - 0.006), (x1 + 0.008, y1 + 0.014, z1 + 0.004), BRASS, 0.0015))
    for sx in (-1, 1):
        for sy in (1.06, 1.44):
            brs.append(K.rivet("board_screw", 0.0045, (sx * 0.625, sy, BZ), normal=(0, 0, 1), mat=BRASS, segs=6))
    # the scope: bezel, dark glass margin round the face, six screws
    brs.append(B.bezel("scope_bezel", (SCOPE_C[0], SCOPE_C[1], BZ), 0.119, 0.147, 0.022, normal=(0, 0, 1), mat=BRASS, seg=28))
    gls.append(D.ring("scope_glass", SCOPE_R, 0.134, -0.0670, -0.0635, (SCOPE_C[0], SCOPE_C[1], 0.0), (0, 0, 1), 28, GLASS))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        brs.append(K.rivet("bezel_screw", 0.0038, (0.131 * math.cos(a), SCOPE_C[1] + 0.131 * math.sin(a), BZ + 0.022), normal=(0, 0, 1),
                           mat=BRASS, segs=6))
    # the knobs' bosses, scale rings and numerals; the pictograms under them
    for key, (kx, ky, kz) in KNOB.items():
        brs.append(K.gcyl("boss", 0.030, BZ, kz, base=(kx, ky, 0.0), axis=(0, 0, 1), segments=12, mat=BRASS, chamfer=0.0015))
        ring = K.plate("scale_ring", [circle(0.0845, 28), list(reversed(circle(0.0795, 28)))], 0.0012, z0=BZ, mat=BRASS, bevel=0.0,
                       drop_bottom=True, loc=(kx, ky, 0.0))
        brs.append(ring)
        for v, ang in NUMERAL_ANG.items():
            a = math.radians(ang)
            t = K.V.text("num", str(v), 0.0165, (kx + NUMERAL_R * math.cos(a), ky + NUMERAL_R * math.sin(a)), BZ, mat=BRASS, depth=0.0016,
                         res=1)
            brs.append(t)
    brs += rack_pictogram(KNOB["x"][0], 1.085, BZ)
    brs += crystal_pictogram(KNOB["y"][0], 1.085, BZ)
    # the lamps' bezels
    for key, (lx, ly, lz) in LAMP.items():
        brs.append(B.bezel("lamp_bezel", (lx, ly, BZ), 0.0165, 0.026, 0.012, normal=(0, 0, 1), mat=BRASS, seg=14))
    # the finale socket: a keystone pad on the slope with a level top (y 0.98) and a boss for a crystal's foot
    cx, cy, cz = CHOICE
    ks = K.plate("keystone", [[(-0.055, -0.048), (0.055, -0.048), (0.036, 0.048), (-0.036, 0.048)]], cy - 0.925, z0=0.0, mat=BRASS,
                 bevel=0.0025, drop_bottom=True)
    ks.data.transform(Matrix.Translation((cx, 0.925, cz)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    brs.append(ks)
    brs.append(K.gcyl("boss", 0.0085, cy, cy + BOSS_H, base=(cx, 0.0, cz), axis=(0, 1, 0), segments=8, mat=BRASS, chamfer=0.0012))
    brs.append(D.ring("pad_ring", 0.026, 0.0295, cy, cy + 0.0025, (cx, 0.0, cz), (0, 1, 0), 14, BRASS))
    return K.part(NAME, wal + brs + gls, pivot=(0.0, 0.0, 0.0))


# ====================================================================== moving / interactive parts
def scope_screen():
    o = D.disc_uv("scope_screen", SCOPE_R, SCOPE_C, SHQ, segs=28)
    M.set_origin(o, SCOPE_C)
    return o


def knob(key):
    kx, ky, kz = KNOB[key]
    kn = L.knurled_knob("kn", KNOB_R, KNOB_H, ridges=10, mat=BRASS, index_mark=False, simple=True)
    ptr = K.gbox("ptr", (-0.0017, KNOB_R * 0.12, KNOB_H), (0.0017, KNOB_R * 0.90, KNOB_H + 0.0016), BRASS, 0.0)
    parts = [kn, ptr]
    for o in parts:
        o.data.transform(Matrix.Translation((kx, ky, kz)))
    return K.part(f"IA_knob_{key}", parts, pivot=(kx, ky, kz))


def cradle():
    cx, cy, cz = CRADLE
    parts = []
    prof = [(0.0, 0.930), (0.064, 0.930), (0.064, 0.948), (0.054, 0.958), (0.042, 0.968), (0.038, 0.976), (0.031, 0.977), (0.031, SEAT_TOP),
            (0.0, SEAT_TOP)]
    ped = K.glathe("pedestal", prof, (cx, 0.0, cz), (0, 1, 0), 14, BRASS, smooth=45.0)
    # the profile is (r, h along +Y from the base point)
    parts.append(ped)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        pts = [(0.0335, SEAT_TOP - 0.003), (0.0315, SEAT_TOP + 0.020), (0.0285, SEAT_TOP + 0.040), (0.0262, SEAT_TOP + 0.054)]
        path = [(cx + r * math.cos(a), y, cz + r * math.sin(a)) for (r, y) in pts]
        parts.append(D.tube("claw", path, 0.0036, sides=5, mat=BRASS, fillet=0.012))
    return K.part("IA_cradle", parts, pivot=CRADLE)


def cradle_ring():
    cx, cz = CRADLE[0], CRADLE[2]
    c = (cx, slope_y(cz) + 0.0015, cz)
    o = D.ring("cradle_ring", 0.072, 0.080, 0.0, 0.0035, c, tuple(NORMAL), 28, BRASS)
    return K.part("cradle_ring", [o], pivot=c)


def strand_plate():
    quad = D.quad01("plate_face", (0.0, 0.0, 0.0), PLATE_W, PLATE_H, SHQ)
    parts = [quad]
    parts.append(K.gbox("slab", (-0.102, -0.082, -0.0105), (0.102, 0.082, -0.0004), BRASS, 0.002))
    parts.append(K.plate("frame", [L.rounded_rect(0.204, 0.164, 0.006, 2), list(reversed(L.rounded_rect(PLATE_W, PLATE_H, 0.002, 1)))], 0.004,
                         z0=0.0, mat=BRASS, bevel=0.0008, drop_bottom=True))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(K.screw("pl_screw", 0.0036, (sx * 0.096, sy * 0.076, 0.004), normal=(0, 0, 1), mat=BRASS, segs=8))
    parts.append(K.gbox("tab", (-0.034, -0.116, -0.0105), (0.034, -0.078, 0.0), BRASS, 0.002))
    mark = S.inlay("mark", "mark", 0.024, depth=0.0016, mat=BRASS, loc=(0.0, -0.097, 0.0))
    parts.append(mark)
    for o in parts:
        on_slope(o, PLATE_C)
    return K.part("IA_strand_plate", parts, pivot=PLATE_C)


def lamps():
    out = {}
    for key, c in LAMP.items():
        j = B.jewel("jw", c, 0.0165, (0, 0, 1), GLASS, seg=12)
        out[key] = K.part(f"lamp_{key}", [j], pivot=c)
    return out


# ====================================================================== build
def build():
    M.reset_scene()
    E.ensure_materials()
    b = body()
    scr = scope_screen()
    kn = {k: knob(k) for k in ("x", "y")}
    cr = cradle()
    ring = cradle_ring()
    plate = strand_plate()
    lp = lamps()
    cm = K.empty("cradle_mount", CRADLE_MOUNT)
    ch = K.empty("choice_mount", CHOICE_MOUNT)
    K.to_blender()
    E.finalize()
    return dict(body=b, screen=scr, knobs=kn, cradle=cr, ring=ring, plate=plate, lamps=lp, cradle_mount=cm, choice_mount=ch)


def verify(path):
    req = [NAME, "scope_screen", "IA_knob_x", "IA_knob_y", "IA_cradle", "cradle_ring", "IA_strand_plate", "cradle_mount", "choice_mount",
           "lamp_choir", "lamp_nursery"]
    expect = {NAME: (0, 0, 0), "scope_screen": SCOPE_C, "IA_knob_x": KNOB["x"], "IA_knob_y": KNOB["y"], "IA_cradle": CRADLE,
              "IA_strand_plate": PLATE_C, "cradle_mount": CRADLE_MOUNT, "choice_mount": CHOICE_MOUNT,
              "lamp_choir": LAMP["choir"], "lamp_nursery": LAMP["nursery"]}
    errs = E.verify(path, required=req, identity=req, expect=expect, parents={n: None for n in req}, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req:
        if n in ("cradle_mount", "choice_mount"):
            continue
        lo, hi = E.bounds([n])
        print(f"{E.TAG} {n:16s} bounds {tuple(round(c, 4) for c in lo)} .. {tuple(round(c, 4) for c in hi)}")
    o = bpy.data.objects.get("scope_screen")
    for n in ("scope_screen", "IA_strand_plate"):
        ob = bpy.data.objects[n]
        uvl = ob.data.uv_layers.active
        shq = [i for i, m in enumerate(ob.data.materials) if m and m.name.startswith(SHQ)]
        uv = sorted({tuple(round(c, 2) for c in uvl.data[li].uv) for p in ob.data.polygons if p.material_index in shq for li in p.loop_indices})
        print(f"{E.TAG} {n} shader-quad UVs {uv[:6]}{' ...' if len(uv) > 6 else ''} (min {min(u for u, v in uv)}, max {max(u for u, v in uv)})")
    return errs


# ====================================================================== QA
def qa(parts, args):
    E.qa_begin()
    roots = D.roots()
    D.place(roots, E.CONSOLE_POS, 0.0, name="qa_place_console")
    E.gallery_room(doors=True, array=True)
    cm = next(o for o in bpy.data.objects if o.name == "cradle_mount")
    E.preview(parts["screen"], "scope_screen_live.png", emissive=True, strength=1.6)
    pl = parts["plate"]
    pm = D.preview_material("qa_plate", "strand_plate.png", rough=0.55)
    if pm is not None:
        for i, m in enumerate(pl.data.materials):
            if m and m.name.startswith(SHQ):
                pl.material_slots[i].material = pm
    for key in ("choir", "nursery"):
        K.override(parts["lamps"][key], K.glow(f"qa_lamp_{key}", "FFB45A" if key == "choir" else "9FE8FF", 5.0))
    K.override(parts["ring"], K.glow("qa_ring", "FFD9A8", 3.0))
    # a crystal in the cradle (the cradle_mount is the item's origin, identity)
    h = D.attach("nursery_crystal", cm, "qa_nc_")
    if h is not None:
        K.override(next((o for o in bpy.data.objects if o.name.startswith("qa_nc_crystal_body")), None), K.glow("qa_crystal", "CFF6FF", 2.0))
    W = lambda p: E.world_point(E.CONSOLE_POS, 0.0, p)   # noqa: E731
    # 1 the console view (§2)
    if E.want(args, "1"):
        V = E.view("console")
        E.gallery_lights(V[0], fill=10.0, array_awake=True)
        E.shoot(NAME, V[0], V[1], V[2])
    # 2 hero: from the operator's left, the slope with the plate, the cradle and the finale socket, low and close
    if E.want(args, "2"):
        cam = W((-0.55, 1.28, 0.62))
        E.gallery_lights(cam, fill=8.0, array_awake=True)
        E.shoot(NAME + "_2", cam, W((0.0, 0.98, 0.10)), 46)
    # 3 the scope view (§2)
    if E.want(args, "3"):
        V = E.view("scope")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_3", V[0], V[1], V[2])
    # 4 the strand_plate view (§2)
    if E.want(args, "4"):
        V = E.view("strand_plate")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_4", V[0], V[1], V[2])
    # 5 the cradle view (§2)
    if E.want(args, "5"):
        V = E.view("cradle")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_5", V[0], V[1], V[2])
    # 6 the finale view: the fork on the choice socket
    if E.want(args, "6"):
        chm = next(o for o in bpy.data.objects if o.name == "choice_mount")
        for o in [o for o in bpy.data.objects if o.name.startswith("qa_nc_")]:
            o.hide_render = True
        D.attach("strand_fork", chm, "qa_sf_")
        V = E.view("finale")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_6", V[0], V[1], V[2])


def main():
    args = M.main_guard()
    parts = build()
    E.report(NAME)
    path = E.export(NAME)
    errs = verify(path)
    print(f"{E.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
