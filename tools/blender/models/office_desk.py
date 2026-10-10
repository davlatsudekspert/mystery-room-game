"""office_desk.glb — Strand's desk: the lamp with the ECG strip, his letters, his note (W2).
Contract: docs/models/ch3.md §4 office_desk (+ §1.2 placement, §2 office / ecg_lamp views, §12 strand_note);
strip: docs/models/ch3_g.md (ecg_strip); results: docs/models/ch3_b.md.

Free-standing, front +Z = the sitter's side; at (-12.6, 0, 2.95), yaw 90 (the front faces east, the back is against the
west wall). 1.30 w x 0.65 d (x ±0.65, z ±0.325), top y 0.76. Origin = the footprint centre on the floor.

  office_desk (static)   walnut pedestal desk: moulded top, two drawer pedestals (three drawers each on the sitter's
                         side), modesty panel, plinth; a stack of books, the blotter's corners (M_Wood_Walnut); drawer
                         pulls, the lamp's base and stem, the ashtray, the fountain pen, the blotter corners' studs
                         (M_Brass_Aged); the blotter sheet, the books' page blocks, and Strand's lab coat hanging on
                         the office coat stand (built here in M_Paper because strand_office has no cream slot; the
                         stand is strand_office's; world (-10.55, 0, 3.7) = desk-local (-0.75, 0, 2.05)).
  IA_office_lamp         the lamp head: ball joint, arm, bell shade (rim y 1.06, front at z -0.03) and the strip clip
                         on the rim's front (M_Brass_Aged). Pick-up target for the strip.
  office_bulb            frosted bulb inside the shade (M_Paper, code emission); office_light: empty at the bulb.
  ecg_mount              (0.50, 1.06, -0.02), basis +90° about local +X: ecg_strip hangs by its top edge, face toward
                         +Z (east); its clip hole lands at (0.50, 1.0822, -0.0239), in the clip's jaws.
  letters_mount          (0.10, 0.765, 0.05), identity: strand_letters (letter.glb) lies flat.
  IA_note                Strand's note: a 0.15 x 0.11 quad at (0.33, 0.762, 0.18) facing +Y, UV 0..1 with u -> +X and
                         v -> -Z (upright for the sitter / the east), M_Decal_StrandNote.

    blender -b --factory-startup -P tools/blender/models/office_desk.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "office_desk"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 6, 4
WALNUT, BRASS, PAPER, DECAL = B.WALNUT, B.BRASS, B.PAPER, "M_Decal_StrandNote"

W2, D2, TOP, TOP_T = 0.65, 0.325, 0.76, 0.035
PED_X = 0.43                                  # pedestal inner edge (knee hole x ±0.22 .. ±0.65)
LAMP_BASE = (0.50, TOP, -0.15)
SHADE_C = (0.50, 1.11, -0.08)                 # bell shade axis; rim y 1.06, r 0.05 -> front at z -0.03
SHADE_R, RIM_Y = 0.05, 1.06
BULB = (0.50, 1.085, -0.08)
ECG = (0.50, 1.06, -0.02)
CLIP_HOLE = (0.50, 1.0822, -0.0239)           # ch3_g.md: hole = mount + (0, 0.0222, -0.0039)
LETTERS = (0.10, 0.765, 0.05)
NOTE = (0.33, 0.762, 0.18)
NOTE_W, NOTE_H = 0.15, 0.11
PLACE = ((-12.6, 0.0, 2.95), 90.0)
COAT_STAND = B.COAT_STAND


def w2l(x, y, z):
    """World -> desk-local for the desk's placement (yaw 90: local +Z -> world +X, local +X -> world -Z)."""
    (px, py, pz), _ = PLACE
    return (-(z - pz), y - py, x - px)


# ====================================================================== static
def desk():
    p = [B.gbox("top", (-W2, TOP - TOP_T, -D2), (W2, TOP, D2), WALNUT, 0.008, 2),
         B.gbox("edge", (-W2 - 0.01, TOP - TOP_T - 0.012, -D2 - 0.01), (W2 + 0.01, TOP - TOP_T + 0.004, D2 + 0.01), WALNUT, 0.004, 1)]
    for sx in (-1, 1):
        x0, x1 = (sx * W2, sx * (W2 - PED_X)) if sx < 0 else (sx * (W2 - PED_X), sx * W2)
        p.append(B.gbox("ped", (x0 + 0.01, 0.08, -D2 + 0.03), (x1 - 0.01, TOP - TOP_T, D2 - 0.02), WALNUT, 0.004))
        p.append(B.gbox("plinth", (x0 + 0.03, 0.0, -D2 + 0.05), (x1 - 0.03, 0.08, D2 - 0.04), WALNUT, 0.003))
        # three drawer fronts on the sitter's side with brass pulls
        for k in range(3):
            y0 = 0.11 + k * 0.205
            p.append(B.gbox("drawer", (x0 + 0.03, y0, D2 - 0.02), (x1 - 0.03, y0 + 0.17, D2 - 0.008), WALNUT, 0.004, 1))
            cx = (x0 + x1) / 2
            p.append(B.glathe("pull", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.014), (0.012, 0.018), (0.012, 0.024), (0.0, 0.024)],
                              (cx, y0 + 0.085, D2 - 0.008), (0, 0, 1), 10, BRASS, smooth=45.0))
            p.append(B.plate("pullpl", [L.rounded_rect(0.07, 0.03, 0.006, 2)], 0.002, mat=BRASS, bevel=0.0004,
                             loc=(cx, y0 + 0.085, D2 - 0.008)))
    # modesty panel between the pedestals, at the back
    p.append(B.gbox("modesty", (-(W2 - PED_X), 0.20, -D2 + 0.03), (W2 - PED_X, TOP - TOP_T, -D2 + 0.05), WALNUT, 0.003))
    return p


def dressing():
    p = []
    # blotter: a paper sheet with four walnut corners and brass studs
    bx, bz, bw, bd = -0.15, 0.08, 0.46, 0.30
    p.append(B.gbox("blotter", (bx - bw / 2, TOP, bz - bd / 2), (bx + bw / 2, TOP + 0.0015, bz + bd / 2), PAPER, 0.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = bx + sx * (bw / 2 - 0.03), bz + sz * (bd / 2 - 0.03)
            tri = [(cx + sx * 0.03, cz + sz * 0.03), (cx - sx * 0.05, cz + sz * 0.03), (cx + sx * 0.03, cz - sz * 0.05)]
            corner = B.K.flat_poly("bcorner", A.ccw([(x, z) for (x, z) in tri]), TOP + 0.0025, WALNUT, up=True)
            p.append(corner)
            p.append(B.rivet("bstud", 0.004, (cx, TOP + 0.0025, cz), normal=(0, 1, 0), mat=BRASS, segs=6))
    # ashtray
    p.append(B.glathe("ashtray", [(0.0, 0.0), (0.045, 0.0), (0.05, 0.006), (0.05, 0.02), (0.042, 0.024), (0.035, 0.012), (0.0, 0.008)],
                      (-0.52, TOP, 0.18), (0, 1, 0), 14, BRASS, smooth=45.0))
    # a stack of three books (walnut covers, paper page blocks) at the back left
    y = TOP
    for (w, d, h, rot) in ((0.22, 0.16, 0.035, 6.0), (0.20, 0.14, 0.03, -8.0), (0.18, 0.13, 0.028, 3.0)):
        cover = B.gbox("book", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), WALNUT, 0.002)
        pages = B.gbox("pages", (-w / 2 + 0.006, 0.003, -d / 2 - 0.002), (w / 2 - 0.012, h - 0.003, d / 2 - 0.004), PAPER, 0.0)
        for o in (cover, pages):
            o.data.transform(Matrix.Translation((-0.48, y, -0.17)) @ Matrix.Rotation(math.radians(rot), 4, "Y"))
            p.append(o)
        y += h
    # fountain pen on the blotter
    pen = B.glathe("pen", [(0.0, 0.0), (0.004, 0.004), (0.006, 0.02), (0.006, 0.10), (0.0065, 0.11), (0.006, 0.135), (0.0, 0.14)],
                   (0.0, 0.0, 0.0), (0, 0, 1), 8, BRASS, smooth=50.0)
    pen.data.transform(Matrix.Translation((-0.05, TOP + 0.0065, 0.16)) @ Matrix.Rotation(math.radians(25), 4, "Y") @
                       Matrix.Rotation(math.radians(-90), 4, "Y"))
    p.append(pen)
    # lamp base and stem (static; the head is IA_office_lamp)
    lx, ly, lz = LAMP_BASE
    p.append(B.glathe("lbase", [(0.0, 0.0), (0.075, 0.0), (0.075, 0.012), (0.055, 0.02), (0.03, 0.03), (0.016, 0.04), (0.0, 0.04)],
                      (lx, ly, lz), (0, 1, 0), 16, BRASS, smooth=45.0))
    p.append(B.gcyl("stem", 0.011, 0.04, 0.26, base=(lx, ly, lz), axis=(0, 1, 0), segments=10, mat=BRASS, caps=False))
    p.append(B.glathe("collar", [(0.011, 0.26), (0.016, 0.26), (0.016, 0.275), (0.011, 0.275)], (lx, ly, lz), (0, 1, 0), 10,
                      BRASS, smooth=45.0, cap_bottom=False, cap_top=False))
    return p


def coat():
    """Strand's lab coat on the office coat stand's north-west hook (world), built in desk-local coordinates."""
    (sx, _, sz), hook_y, hook_r = COAT_STAND["pos"], COAT_STAND["hook_y"], COAT_STAND["hook_r"]
    a = math.radians(225.0)
    hook = Vector((sx + hook_r * math.cos(a), hook_y + 0.06, sz + hook_r * math.sin(a)))
    radial = Vector((math.cos(a), 0.0, math.sin(a)))              # away from the pole
    tang = Vector((-math.sin(a), 0.0, math.cos(a)))               # across the coat
    out = []
    rings = []
    # (height below the hook, half width across, half depth, radial shift): collar loop -> shoulders -> hem
    for (dy, hw, hd, sh) in ((0.0, 0.02, 0.015, 0.0), (-0.05, 0.08, 0.04, 0.02), (-0.09, 0.21, 0.09, 0.04), (-0.25, 0.20, 0.10, 0.03),
                             (-0.50, 0.18, 0.09, 0.02), (-0.72, 0.20, 0.10, 0.02), (-0.98, 0.24, 0.12, 0.03)):
        c = hook + Vector((0.0, dy, 0.0)) + radial * sh
        ring = []
        n = 14
        for i in range(n):
            t = 2 * math.pi * i / n
            q = c + tang * (hw * math.cos(t)) + radial * (hd * math.sin(t))
            ring.append(w2l(*q))
        rings.append(ring)
    body = A.loft("coat", rings, mat=PAPER, cap_start=True, cap_end=True)
    A.hint(body, 70.0)
    out.append(body)
    # sleeves hanging from the shoulders, slightly forward
    for s in (-1, 1):
        top = hook + Vector((0.0, -0.11, 0.0)) + tang * (s * 0.19) + radial * 0.04
        pts = [top, top + Vector((0.0, -0.22, 0.0)) + radial * 0.03 + tang * (s * 0.01),
               top + Vector((0.0, -0.50, 0.0)) + radial * 0.05 + tang * (s * 0.0)]
        sl = A.tube("sleeve", [B.G(*w2l(*q)) if False else Vector(w2l(*q)) for q in pts], 0.055, sides=10, mat=PAPER, radii=[0.062, 0.052, 0.046])
        out.append(sl)
    return out


def static():
    return B.part(NAME, desk() + dressing() + coat())


# ====================================================================== parts
def lamp_head():
    lx, ly, lz = LAMP_BASE
    cx, cy, cz = SHADE_C
    p = [M.sphere("joint", 0.018, loc=(lx, ly + 0.28, lz), segments=10, rings=6, mat=BRASS)]
    M.apply_transform(p[0])
    A.hint(p[0], 80.0)
    # arm: from the joint up and forward to the shade's crown
    p.append(B.tube("arm", [(lx, ly + 0.29, lz), (lx, ly + 0.36, lz - 0.01), (cx, 1.19, cz - 0.02), (cx, 1.165, cz)], 0.007,
                    sides=8, mat=BRASS))
    # bell shade: open below (rim y 1.06, r 0.05), crown with a finial
    prof = [(SHADE_R, RIM_Y), (SHADE_R + 0.004, RIM_Y + 0.004), (0.046, RIM_Y + 0.02), (0.034, RIM_Y + 0.06), (0.020, RIM_Y + 0.095),
            (0.012, RIM_Y + 0.105), (0.0, RIM_Y + 0.108)]
    shade = B.glathe("shade", prof, (cx, 0.0, cz), (0, 1, 0), 18, BRASS, smooth=50.0, cap_bottom=False)
    # the inside of the shade: a second, inward-facing surface
    inner = B.glathe("shade_in", [(0.0, RIM_Y + 0.1), (0.011, RIM_Y + 0.1), (0.019, RIM_Y + 0.093), (0.032, RIM_Y + 0.06),
                                  (0.044, RIM_Y + 0.02), (SHADE_R - 0.001, RIM_Y + 0.002)], (cx, 0.0, cz), (0, 1, 0), 18, BRASS,
                     smooth=50.0, cap_bottom=False, cap_top=False)
    p += [shade, inner]
    # strip clip on the rim's front: two jaws round the strip's top edge, a pin through the clip hole
    hx, hy, hz = CLIP_HOLE
    p.append(B.gbox("jaw_b", (hx - 0.012, hy - 0.012, cz + SHADE_R - 0.004), (hx + 0.012, hy + 0.014, hz - 0.0045), BRASS, 0.001))
    p.append(B.gbox("jaw_f", (hx - 0.012, hy - 0.004, hz + 0.0085), (hx + 0.012, hy + 0.014, hz + 0.011), BRASS, 0.001))
    p.append(B.gbox("jaw_t", (hx - 0.012, hy + 0.011, hz - 0.0045), (hx + 0.012, hy + 0.014, hz + 0.0085), BRASS, 0.001))
    p.append(B.gcyl("pin", 0.0013, hz - 0.0045, hz + 0.0085, base=(hx, hy, 0.0), axis=(0, 0, 1), segments=6, mat=BRASS))
    return B.part("IA_office_lamp", p, pivot=(cx, RIM_Y + 0.05, cz))


def bulb():
    bx, by, bz = BULB
    o = M.sphere("bulbs", 0.019, loc=(bx, by, bz), segments=12, rings=7, mat=PAPER)
    M.apply_transform(o)
    A.hint(o, 80.0)
    neck = B.gcyl("neck", 0.008, 0.012, 0.03, base=(bx, by, bz), axis=(0, 1, 0), segments=8, mat=PAPER)
    return B.part("office_bulb", [o, neck], pivot=BULB)


def note():
    q = B.K.quad("IA_note", NOTE, (1, 0, 0), (0, 0, -1), NOTE_W, NOTE_H, DECAL)
    return B.part("IA_note", [q], pivot=NOTE)


def empties():
    return [B.empty("ecg_mount", ECG, (90.0, 0.0, 0.0)), B.empty("letters_mount", LETTERS), B.empty("office_light", BULB)]


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = static()
    head = lamp_head()
    bl = bulb()
    nt = note()
    emp = empties()
    B.K.to_blender()
    A.finalize_uv()          # the decal quad keeps its 0..1 UVs
    return dict(static=st, head=head, bulb=bl, note=nt, empties=emp)


REQ = [NAME, "IA_office_lamp", "office_bulb", "office_light", "ecg_mount", "letters_mount", "IA_note"]


def check_note_uv(obj):
    me = obj.data
    uv = me.uv_layers.active.data
    pts = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = B.V.C_INV @ (obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            pts.append((round(co.x, 3), round(co.z, 3), tuple(round(c, 3) for c in uv[li].uv)))
    ok = all(((u > 0.5) == (x > NOTE[0])) and ((v > 0.5) == (z < NOTE[2])) for (x, z, (u, v)) in pts)
    print(f"{B.TAG} IA_note UV corners (godot x, z, uv): {pts} -> {'OK' if ok else 'WRONG'}")
    return [] if ok else ["IA_note UV: u must grow toward +X, v toward -Z"]


def verify(path, parts):
    expect = {"IA_office_lamp": (SHADE_C[0], RIM_Y + 0.05, SHADE_C[2]), "office_bulb": BULB, "office_light": BULB, "ecg_mount": ECG,
              "letters_mount": LETTERS, "IA_note": NOTE}
    errs = B.verify(path, REQ, identity=[NAME, "IA_office_lamp", "office_bulb", "IA_note", "letters_mount", "office_light"],
                    expect=expect, parents={n: None for n in REQ}, rot_expect={"ecg_mount": (90.0, 0.0, 0.0)}, tris=TRI_BUDGET,
                    surf=SURF_BUDGET, mats=MAT_BUDGET)
    errs += check_note_uv(parts["note"])
    lo, hi = B.V.mesh_bounds_godot([parts["static"]])
    print(f"{B.TAG} static bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)} (the coat reaches out to the stand)")
    lo, hi = B.V.mesh_bounds_godot([parts["head"]])
    print(f"{B.TAG} lamp head bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    B.qa_begin()
    B.hall()
    mine = [o for o in bpy.data.objects if o.parent is None and not o.name.startswith("qa")]
    B.place(mine, *PLACE, name="qa_desk")
    B.bring("strand_office", prefix="qa_office_")
    B.bring("meter_case", (-12.62, 0.76, 3.30), 90.0, prefix="qa_case_")
    B.bring("chair", (-11.8, 0.0, 3.55), 60.0, prefix="qa_chair_")
    B.bring("letter", under=bpy.data.objects["letters_mount"], prefix="qa_letter_")
    strip = B.bring("ecg_strip", under=bpy.data.objects["ecg_mount"], prefix="qa_strip_")
    prev = os.path.join(B.PREVIEW_DIR, "strip_face.png")
    face = B.imported("qa_strip_", "strip_face")
    if face is not None and os.path.exists(prev):
        B.K.override(face, M.material("qa_strip_prev", color="E7B7A6", rough=0.85, image=prev))
    B.K.override(parts["bulb"], B.K.glow("qa_bulb", "FFD9A8", 7.0))
    office_lamp = [("office_lamp", "POINT", (-12.65, 1.09, 2.45), 22.0, "FFCC8A", 0.02)]
    shots = [
        # 1 office view: the desk under the lamp, the strip hanging on the shade, the letters and the note
        ("1", NAME, (-10.5, 1.6, 2.35), (-12.55, 0.85, 2.95), 56),
        # 2 ecg_lamp view: the strip clipped to the shade's rim, lit by the bulb
        ("2", NAME + "_2", (-12.0, 1.3, 2.3), (-12.62, 1.06, 2.45), 40),
        # 3 the note and the letters from the sitter's side
        ("3", NAME + "_3", (-12.0, 1.25, 2.72), (-12.47, 0.77, 2.72), 42),
        # 4 the coat stand with Strand's coat (the stand is strand_office's), from the office door
        ("4", NAME + "_4", (-10.3, 1.5, 2.75), (-10.6, 1.25, 3.65), 46),
    ]
    for tag, name, cam, tgt, fov in shots:
        if not B.want(args, tag):
            continue
        B.choir_lights(cam, fill=6.0, extra=office_lamp)
        B.shoot(name, cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path, parts)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
