"""tape_deck.glb — open-reel tape recorder lying on the archivist's desk (Archive B), puzzle P7.

A walnut case with a dark brushed-steel top deck: two spindles on chrome-ringed platters (an empty
glossy take-up reel on the right one), the tape path between them (tension arms, guide posts, a chrome
head cover, capstan and pinch roller), and a black control strip sloping toward the player with the VU
meter, the chicken-head speed selector (3D labels 2.4 / 4.75 / 9.5 / 19 cm/s) and the PLAY / EJECT
piano keys.

Model space (Godot): front +Z, origin = base centre on the desk surface (y = 0).
Placement: (4.15, 0.76, -3.05), yaw 0. Overall 0.46 x 0.165 x 0.36.
Parts (origin at the pivot, identity rotation at rest relative to the parent):
  strip_frame       EMPTY on the control strip (centre of the strip face), rotated -48.4 deg about +X so its
                    local +Z is the strip normal and local +Y points up the slope. Parent of:
    IA_speed        speed knob; rotation (45 - 30 i) deg about local +Z, i = 0..3 (2.4, 4.75, 9.5, 19);
                    identity pointer at 12 o'clock (up the strip, between 4.75 and 9.5)
    IA_play         piano key; hinge on its lower (front) edge; pressed = -8 deg about local +X (its upper
                    end dips into the strip)
    IA_eject        smaller key, same motion
    vu_face         cream meter face (own mesh, can be lit); the 3D ticks are the static `vu_scale`
    vu_needle       pivot at its base; identity = the meter's left stop (40 deg left of vertical);
                    code: clockwise = negative about local +Z, up to -80 deg (right stop)
  spindle_l / _r    platter + spindle, origin on the axis at the deck surface; spin about local +Y
    deck_reel_mount child of spindle_l at the reel centre: tape_reel.glb lies face up there (identity)
    takeup_reel     child of spindle_r: empty glossy reel, 0.127 diameter
  tape_path         static guides, tension arms, head block, capstan, pinch roller
    blender -b --factory-startup -P tools/blender/models/tape_deck.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_devices1 as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "tape_deck"
BUDGET = 8000
W, Z0, Z1 = 0.46, -0.18, 0.18
CHEEK = 0.016                      # walnut side cheeks
DECK_Y = 0.128                     # top plate surface
STRIP = ((0.088, 0.128), (0.177, 0.049))       # (z, y) top and bottom of the sloped strip face
SPX, SPZ = 0.120, -0.058           # spindles at x = +-SPX, z = SPZ
PLATTER_R, PLATTER_H = 0.040, 0.006
REEL_R, REEL_T = 0.0635, 0.014
VU_U, VU_V = -0.128, 0.004         # VU window centre on the strip
VU_PIVOT_V = -0.026
VU_LEN = 0.046
SPEED_U, SPEED_V = -0.016, -0.010
LABELS = ["2.4", "4.75", "9.5", "19"]
LABEL_R = 0.042
PLAY_U, EJECT_U = 0.090, 0.163
KEY_V0 = -0.044                    # key hinge line (lower edge) on the strip
KEY_LEN = 0.046
KEY_GAP = 0.0075                   # key underside above the strip face


def strip_geom():
    (za, ya), (zb, yb) = STRIP
    ang = math.atan2(ya - yb, zb - za)                 # slope angle from horizontal
    centre = ((za + zb) / 2, (ya + yb) / 2)
    length = math.hypot(zb - za, ya - yb)
    return ang, centre, length


ANG, SC, SLEN = strip_geom()
TILT = -(90.0 - math.degrees(ANG))                    # strip_frame rotation about +X


def strip_matrix(lift=0.0) -> Matrix:
    """Strip-local (u right, v up the slope, w out) -> Blender."""
    n = (0.0, math.cos(ANG), math.sin(ANG))
    up = (0.0, math.sin(ANG), -math.cos(ANG))
    o = (0.0, SC[1] + n[1] * lift, SC[0] + n[2] * lift)
    return C.gframe(o, (1, 0, 0), up)


# ---------------------------------------------------------------- case + top deck + strip panel (static)
def build_case():
    parts = []
    (za, ya), (zb, yb) = STRIP
    prof = [(Z1 - 0.002, 0.010), (Z1 - 0.002, yb - 0.004), (zb, yb), (za, ya), (Z0 + 0.012, DECK_Y), (Z0, DECK_Y - 0.012),
            (Z0, 0.010)]
    side = C.gframe((-W / 2 + CHEEK, 0.0, 0.0), (0, 0, -1), (0, 1, 0))
    body = C.solid_g("case", [[(-z, y - 0.003) for (z, y) in prof]], W - 2 * CHEEK, side, bevel=0.003,
                     mat="M_Wood_Walnut")
    parts.append(C.sm(body, 40.0))
    # walnut cheeks: a little proud of the plates, rounded
    cprof = [(Z1, 0.008), (Z1, yb + 0.002), (zb + 0.004, yb + 0.008), (za + 0.004, ya + 0.006), (Z0 + 0.016, DECK_Y + 0.006),
             (Z0, DECK_Y - 0.010), (Z0, 0.008)]
    for sx in (-1, 1):
        x0 = -W / 2 if sx < 0 else W / 2 - CHEEK
        ch = C.solid_g("cheek", [[(-z, y) for (z, y) in cprof]], CHEEK, C.gframe((x0, 0.0, 0.0), (0, 0, -1), (0, 1, 0)),
                       bevel=0.005, bevel_res=1, mat="M_Wood_Walnut")
        parts.append(C.sm(ch, 40.0))
    # feet
    for sx in (-1, 1):
        for sz in (-1, 1):
            ft = C.revolve_g("foot", [(0.012, 0.0), (0.014, 0.002), (0.014, 0.007), (0.010, 0.010)], (0, 1, 0),
                             (sx * 0.19, 0.0, sz * 0.145), segments=10, mat="M_Rubber", cap_bottom=True, cap_top=True)
            parts.append(C.sm(ft, 45.0))
    # top deck plate (brushed dark steel) with a chrome edge strip
    pw = W - 2 * CHEEK - 0.002
    plate = C.gbox("deckplate", (-pw / 2, DECK_Y - 0.004, Z0 + 0.010), (pw / 2, DECK_Y, za + 0.002),
                   mat="M_Steel_Dark", bevel=0.0015)
    parts.append(C.sm(plate, 30.0))
    edge = C.gbox("deckedge", (-pw / 2, DECK_Y - 0.0035, za - 0.004), (pw / 2, DECK_Y + 0.0012, za + 0.003),
                  mat="M_Chrome", bevel=0.0012)
    parts.append(C.sm(edge, 30.0))
    # black control strip face
    sm_ = strip_matrix()
    strip = C.solid_g("strip", [L.rounded_rect(pw, SLEN - 0.004, 0.003, 2)], 0.003, sm_, lift=-0.003, bevel=0.0008,
                      mat="M_Lacquer_Black")
    parts.append(C.sm(strip, 30.0))
    # platter rings (chrome) recessed around each spindle
    for sx in (-1, 1):
        ring = C.revolve_g("pring", [(PLATTER_R + 0.009, 0.0), (PLATTER_R + 0.009, 0.0012), (PLATTER_R + 0.004, 0.0016),
                                     (PLATTER_R + 0.002, 0.0)], (0, 1, 0), (sx * SPX, DECK_Y, SPZ), segments=28,
                           mat="M_Chrome", cap_bottom=False, cap_top=False)
        parts.append(C.sm(ring, 35.0))
    # corner screws on the deck, a chrome brand badge
    for (x, z) in ((-0.198, -0.162), (0.198, -0.162), (-0.198, 0.070), (0.198, 0.070)):
        parts.append(C.screw_g("dscrew", 0.0032, (x, DECK_Y, z), normal_g=(0, 1, 0), mat="M_Chrome", segs=6,
                               slot=x * 3))
    bf = C.gframe((-0.135, DECK_Y + 0.0002, 0.064), (1, 0, 0), (0, 0, -1))
    parts.append(C.solid_g("badge", [L.rounded_rect(0.072, 0.016, 0.004, 2)], 0.0012, bf, bevel=0.0003,
                           mat="M_Chrome"))
    parts.append(C.text_g("badge_txt", "ORBITA  5", 0.0090, bf, lift=0.0013, font=C.FONT_COND_B,
                          mat="M_Lacquer_Black", res=1))
    # strip decorations: VU bezel + glass, knob ticks and speed labels, key slots + hinge blocks, 'cm/s'
    sf = strip_matrix(0.0)
    bez = C.solid_g("vubezel", [L.rounded_rect(0.094, 0.068, 0.008, 3), L.rounded_rect(0.082, 0.056, 0.005, 3)],
                    0.004, sf, u=VU_U, v=VU_V, bevel=0.0010, mat="M_Chrome")
    parts.append(C.sm(bez, 30.0))
    glass = C.shape_g("vuglass", [L.rounded_rect(0.084, 0.058, 0.005, 3)], sf, u=VU_U, v=VU_V, lift=0.0032,
                      mat="M_Glass")
    parts.append(glass)
    ticks = []
    for k, lab in enumerate(LABELS):
        phi = 45.0 - 30.0 * k
        a = math.radians(90.0 + phi)
        ticks.append(C.radial_tick(0.0205, 0.0280, 90.0 + phi, 0.0017))
        parts.append(C.text_g("slabel", lab, 0.0090, sf, u=SPEED_U + LABEL_R * math.cos(a),
                              v=SPEED_V + LABEL_R * math.sin(a), lift=0.0002, font=C.FONT_SANS_B,
                              mat="M_Enamel_Cream", res=1))
    parts.append(C.shape_g("sticks", ticks, sf, u=SPEED_U, v=SPEED_V, lift=0.0002, mat="M_Enamel_Cream"))
    parts.append(C.text_g("cms", "cm/s", 0.0058, sf, u=SPEED_U, v=SPEED_V - 0.034, lift=0.0002, font=C.FONT_SANS_B,
                          mat="M_Enamel_Cream", res=1))
    for (u, w) in ((PLAY_U, 0.052), (EJECT_U, 0.034)):
        parts.append(C.shape_g("kslot", [L.rounded_rect(w + 0.004, KEY_LEN + 0.004, 0.003, 2)], sf, u=u,
                               v=KEY_V0 + KEY_LEN / 2, lift=0.0001, mat="M_Steel_Dark"))
        hb = C.solid_g("khinge", [L.rounded_rect(w * 0.6, 0.008, 0.002, 2)], KEY_GAP + 0.002, sf, u=u, v=KEY_V0 + 0.002,
                       bevel=0.0006, mat="M_Chrome")
        parts.append(C.sm(hb, 30.0))
    return C.part("deck_body", parts, (0.0, 0.0, 0.0))


# ---------------------------------------------------------------- strip controls (children of strip_frame)
def build_strip_controls(frame_empty):
    sf = strip_matrix(0.0)
    out = []
    # VU face (own object) + static scale + needle
    face = C.shape_g("vu_face", [L.rounded_rect(0.080, 0.054, 0.004, 3)], sf, u=VU_U, v=VU_V, lift=0.0004,
                     mat="M_Enamel_Cream")
    vface = C.part("vu_face", [face], None)
    M.set_origin(vface, sf @ Vector((VU_U, VU_V, 0.0004)))
    scale = []
    for k in range(9):
        a = 90.0 + 40.0 - 10.0 * k
        r0 = 0.036 if k % 2 == 0 else 0.0385
        scale.append(C.radial_tick(r0, 0.0425, a, 0.0007 if k % 2 else 0.0010))
    scale.append(C.arc_band(0.0425, 0.0437, 90.0 - 40.5, 90.0 + 40.5, 16))
    red = C.arc_band(0.0437, 0.0465, 90.0 - 40.5, 90.0 - 12.0, 8)
    sc = C.shape_g("vu_ticks", scale, sf, u=VU_U, v=VU_PIVOT_V, lift=0.0007, mat="M_Lacquer_Black")
    rd = C.shape_g("vu_red", [red], sf, u=VU_U, v=VU_PIVOT_V, lift=0.0007, mat="M_Enamel_Crimson")
    vt = C.text_g("vu_txt", "VU", 0.0085, sf, u=VU_U, v=VU_PIVOT_V + 0.020, lift=0.0007, font=C.FONT_SERIF_B,
                  mat="M_Lacquer_Black", res=1)
    shroud = C.solid_g("vu_shroud", [L.arc_pts(0.011, 0.0, math.pi, 8) + [(-0.011, -0.004), (0.011, -0.004)]],
                       0.0028, sf, u=VU_U, v=VU_PIVOT_V + 0.002, bevel=0.0006, mat="M_Lacquer_Black")
    vscale = C.part("vu_scale", [sc, rd, vt, C.sm(shroud, 30.0)], None)
    M.set_origin(vscale, sf @ Vector((VU_U, VU_V, 0.0)))
    nd = L.curve_solid("vu_nd", [[(-0.0006, 0.004), (0.0006, 0.004), (0.0003, VU_LEN), (-0.0003, VU_LEN)]], 0.0006,
                       bevel=0.0, mat="M_Lacquer_Black")
    nd.data.transform(Matrix.Rotation(math.radians(40.0), 4, "Z"))      # rest = left stop
    nd.data.transform(Matrix.Translation((VU_U, VU_PIVOT_V, 0.0018)))
    nd.data.transform(sf)
    needle = C.part("vu_needle", [C.sm(nd, 30.0)], None)
    M.set_origin(needle, sf @ Vector((VU_U, VU_PIVOT_V, 0.0018)))
    # speed knob: round skirt + chicken-head bar (bakelite) + cream index line
    skirt = L.lathe2("sk_skirt", [(0.0125, 0.0), (0.0130, 0.0015), (0.0130, 0.0040), (0.0110, 0.0060), (0.0, 0.0060)],
                     segments=20, mat="M_Bakelite", cap_bottom=False)
    bar = L.curve_solid("sk_bar", [[(-0.0065, -0.016), (0.0065, -0.016), (0.0050, 0.016), (0.0, 0.0225),
                                    (-0.0050, 0.016)]], 0.012, bevel=0.0022, bevel_res=1, mat="M_Bakelite")
    bar.data.transform(Matrix.Translation((0, 0, 0.0050)))
    line = L.flat_shape("sk_line", [[(-0.0010, 0.004), (0.0010, 0.004), (0.0007, 0.0190), (-0.0007, 0.0190)]],
                        mat="M_Enamel_Cream")
    line.data.transform(Matrix.Translation((0, 0, 0.0171)))
    for o in (skirt, bar, line):
        o.data.transform(Matrix.Translation((SPEED_U, SPEED_V, 0.0)))
        o.data.transform(sf)
    knob = C.part("IA_speed", [C.sm(skirt, 40.0), C.sm(bar, 35.0), line], None)
    M.set_origin(knob, sf @ Vector((SPEED_U, SPEED_V, 0.0)))
    # piano keys: hinge on the lower edge, raised KEY_GAP over the strip
    keys = []
    for (nm, u, w, mat, glyph_mat) in (("IA_play", PLAY_U, 0.052, "M_Enamel_Cream", "M_Lacquer_Black"),
                                       ("IA_eject", EJECT_U, 0.034, "M_Bakelite", "M_Enamel_Cream")):
        key = L.curve_solid("key", [L.rrect4(w, KEY_LEN, radii=(0.002, 0.005, 0.005, 0.002), n=3)], 0.010,
                            bevel=0.0018, bevel_res=1, mat=mat)
        key.data.transform(Matrix.Translation((u, KEY_V0 + KEY_LEN / 2, KEY_GAP)))
        if nm == "IA_play":
            g = [[(-0.0055, -0.0070), (0.0075, 0.0), (-0.0055, 0.0070)]]
        else:
            g = [[(-0.0070, -0.0010), (0.0070, -0.0010), (0.0, 0.0065)], L.rounded_rect(0.014, 0.0028, 0.0005, 1,
                                                                                         cy=-0.0055)]
        gl = L.flat_shape("glyph", g, mat=glyph_mat)
        gl.data.transform(Matrix.Translation((u, KEY_V0 + KEY_LEN / 2 + 0.004, KEY_GAP + 0.0101)))
        for o in (key, gl):
            o.data.transform(sf)
        k = C.part(nm, [C.sm(key, 35.0), gl], None)
        M.set_origin(k, sf @ Vector((u, KEY_V0, KEY_GAP)))
        keys.append(k)
    M.refresh()
    frot = frame_empty.matrix_world.to_3x3().to_4x4()
    for o in [vface, vscale, needle, knob] + keys:
        C.rebase(o, Matrix.Translation(o.matrix_world.translation) @ frot)
        C.parent(o, frame_empty)
    return vface, vscale, needle, knob, keys


# ---------------------------------------------------------------- spindles + reels + tape path
def reel_parts(prefix, mat_flange="M_Glass_Dark"):
    """Empty 5-inch reel lying flat (local Blender XY, z = thickness), centred at the origin."""
    parts = []
    holes = []
    for k in range(3):
        a0 = math.radians(90 + 120 * k - 42)
        a1 = math.radians(90 + 120 * k + 42)
        outer = L.arc_pts(0.054, a0, a1, 7)
        inner = L.arc_pts(0.024, a1, a0, 4)
        holes.append(outer + inner)
    for s in (-1, 1):
        fl = L.curve_solid(prefix + "_flange", [L.circle(REEL_R, 40)] + holes + [L.circle(0.0045, 8)], 0.0012,
                           bevel=0.0003, mat=mat_flange)
        fl.data.transform(Matrix.Translation((0, 0, s * (REEL_T / 2 - 0.0006) - 0.0006)))
        parts.append(C.sm(fl, 35.0))
    hub = L.lathe2(prefix + "_hub", [(0.0045, -REEL_T / 2 + 0.0012), (0.0230, -REEL_T / 2 + 0.0012),
                                     (0.0230, REEL_T / 2 - 0.0012), (0.0045, REEL_T / 2 - 0.0012)], segments=20,
                   mat=mat_flange, cap_bottom=False, cap_top=False)
    parts.append(C.sm(hub, 40.0))
    lab = L.flat_shape(prefix + "_label", [L.circle(0.0215, 20), L.circle(0.0062, 10)], mat="M_Enamel_Cream")
    lab.data.transform(Matrix.Translation((0, 0, REEL_T / 2 + 0.00005)))
    parts.append(lab)
    # a few turns of leader tape on the hub
    tape = L.lathe2(prefix + "_leader", [(0.0232, -0.0032), (0.0255, -0.0032), (0.0255, 0.0032), (0.0232, 0.0032)],
                    segments=20, mat="M_Tape", cap_bottom=False, cap_top=False)
    parts.append(C.sm(tape, 40.0))
    return parts


def build_spindles():
    out = {}
    for side, sx in (("l", -1), ("r", 1)):
        x = sx * SPX
        pl = C.revolve_g("platter", [(0.0, 0.0005), (PLATTER_R, 0.0005), (PLATTER_R, PLATTER_H - 0.0015),
                                     (PLATTER_R - 0.0015, PLATTER_H), (0.0, PLATTER_H)], (0, 1, 0), (x, DECK_Y, SPZ),
                         segments=28, mat="M_Chrome", cap_bottom=False,
                         band_mats=[None, None, None, "M_Rubber"])
        sh = C.revolve_g("shaft", [(0.0042, PLATTER_H), (0.0042, PLATTER_H + 0.020), (0.0030, PLATTER_H + 0.023),
                                   (0.0, PLATTER_H + 0.0235)], (0, 1, 0), (x, DECK_Y, SPZ), segments=10,
                         mat="M_Chrome", cap_bottom=False)
        parts = [C.sm(pl, 40.0), C.sm(sh, 45.0)]
        for k in range(3):            # locking lugs
            a = math.radians(90 + 120 * k)
            lug = C.gbox("lug", (-0.0011, DECK_Y + PLATTER_H + 0.016, 0.0038), (0.0011, DECK_Y + PLATTER_H + 0.020, 0.0072),
                         mat="M_Chrome", bevel=0.0004)
            lug.data.transform(Matrix.Translation(-C.G(0, 0, 0)))
            lug.data.transform(Matrix.Rotation(a, 4, "Z"))
            lug.data.transform(Matrix.Translation(C.G(x, 0, SPZ)))
            parts.append(C.sm(lug, 30.0))
        sp = C.part(f"spindle_{side}", parts, (x, DECK_Y, SPZ))
        out[side] = sp
    # deck_reel_mount on the left spindle (reel resting on the platter, face up)
    mnt = C.mount("deck_reel_mount", (-SPX, DECK_Y + PLATTER_H + REEL_T / 2, SPZ), par=out["l"])
    # take-up reel on the right spindle
    rp = reel_parts("tu")
    for o in rp:
        o.data.transform(Matrix.Translation(C.G(SPX, DECK_Y + PLATTER_H + REEL_T / 2, SPZ)))
    tu = C.part("takeup_reel", rp, (SPX, DECK_Y + PLATTER_H + REEL_T / 2, SPZ))
    C.parent(tu, out["r"])
    return out, mnt, tu


def build_tape_path():
    parts = []
    y0 = DECK_Y
    # head block: chrome cover with a dark window, mounted on a plinth, two heads visible at its front
    hz = 0.040
    plinth = C.gbox("hplinth", (-0.050, y0, hz - 0.020), (0.050, y0 + 0.006, hz + 0.022), mat="M_Steel_Dark",
                    bevel=0.002)
    cover = C.gbox("hcover", (-0.046, y0 + 0.006, hz - 0.016), (0.046, y0 + 0.032, hz + 0.016), mat="M_Chrome",
                   bevel=0.006, seg=2)
    parts += [C.sm(plinth, 30.0), C.sm(cover, 35.0)]
    cf = C.gframe((0.0, y0 + 0.0322, hz), (1, 0, 0), (0, 0, -1))
    parts.append(C.shape_g("hgrill", [L.rounded_rect(0.060, 0.012, 0.004, 3)], cf, mat="M_Lacquer_Black"))
    for x in (-0.018, 0.018):
        hd = C.gbox("head", (x - 0.007, y0 + 0.008, hz - 0.019), (x + 0.007, y0 + 0.026, hz - 0.015), mat="M_Steel_Dark",
                    bevel=0.002)
        parts.append(C.sm(hd, 30.0))
    # guide posts, capstan, pinch roller
    for (x, z, r, h, mat) in ((-0.070, 0.028, 0.0045, 0.024, "M_Chrome"), (0.070, 0.028, 0.0045, 0.024, "M_Chrome"),
                              (0.056, 0.016, 0.0022, 0.026, "M_Chrome")):
        post = C.revolve_g("post", [(r + 0.002, 0.0), (r + 0.002, 0.003), (r, 0.004), (r, h), (0.0, h)], (0, 1, 0),
                           (x, y0, z), segments=10, mat=mat, cap_bottom=False)
        parts.append(C.sm(post, 45.0))
    roller = C.revolve_g("pinch", [(0.0035, 0.004), (0.0105, 0.004), (0.0110, 0.006), (0.0110, 0.020), (0.0105, 0.022),
                                   (0.0, 0.022)], (0, 1, 0), (0.060, y0, 0.034), segments=14, mat="M_Rubber",
                         cap_bottom=False)
    parts.append(C.sm(roller, 45.0))
    arm = C.gbox("pinch_arm", (0.060, y0 + 0.001, 0.030), (0.088, y0 + 0.004, 0.038), mat="M_Chrome", bevel=0.001)
    parts.append(C.sm(arm, 30.0))
    # tension arms with rollers near each reel
    for sx in (-1, 1):
        x = sx * 0.088
        arm = C.gbox("tarm", (x - 0.003, y0 + 0.001, 0.000), (x + 0.003, y0 + 0.004, 0.034), mat="M_Chrome",
                     bevel=0.001)
        arm.data.transform(Matrix.Translation(-C.G(x, 0, 0.034)))
        arm.data.transform(C.grot("y", sx * 28.0))
        arm.data.transform(Matrix.Translation(C.G(x, 0, 0.034)))
        rol = C.revolve_g("troller", [(0.0050, 0.003), (0.0050, 0.016), (0.0, 0.016)], (0, 1, 0),
                          (x + sx * 0.016 * math.sin(math.radians(28)), y0, 0.034 - 0.030), segments=10,
                          mat="M_Chrome", cap_bottom=False)
        piv = C.revolve_g("tpivot", [(0.0045, 0.0), (0.0045, 0.006), (0.0, 0.007)], (0, 1, 0), (x, y0, 0.034),
                          segments=8, mat="M_Chrome", cap_bottom=False)
        parts += [C.sm(arm, 30.0), C.sm(rol, 45.0), C.sm(piv, 45.0)]
    return C.part("tape_path", parts, (0.0, 0.0, 0.0))


def build():
    C.ensure_materials()
    build_case()
    fe = C.mount("strip_frame", (0.0, SC[1], SC[0]), rot=C.grot("x", TILT), size=0.05)
    build_strip_controls(fe)
    build_spindles()
    build_tape_path()


def main():
    M.reset_scene()
    build()
    C.finalize()
    C.report(NAME, BUDGET)
    C.export(NAME)
    q = (math.sin(math.radians(TILT) / 2), 0.0, 0.0, math.cos(math.radians(TILT) / 2))
    C.verify_glb(NAME, {
        "strip_frame": dict(parent=None, pos=(0.0, SC[1], SC[0]), rot=q),
        "IA_speed": dict(parent="strip_frame", pos=(SPEED_U, SPEED_V, 0.0)),
        "IA_play": dict(parent="strip_frame", pos=(PLAY_U, KEY_V0, KEY_GAP)),
        "IA_eject": dict(parent="strip_frame", pos=(EJECT_U, KEY_V0, KEY_GAP)),
        "vu_face": dict(parent="strip_frame"),
        "vu_needle": dict(parent="strip_frame", pos=(VU_U, VU_PIVOT_V, 0.0018)),
        "spindle_l": dict(parent=None, pos=(-SPX, DECK_Y, SPZ)),
        "spindle_r": dict(parent=None, pos=(SPX, DECK_Y, SPZ)),
        "deck_reel_mount": dict(parent="spindle_l", pos=(0.0, PLATTER_H + REEL_T / 2, 0.0)),
        "takeup_reel": dict(parent="spindle_r", pos=(0.0, PLATTER_H + REEL_T / 2, 0.0)),
        "tape_path": dict(parent=None),
    }, BUDGET)
    print(f"{C.TAG} strip slope {math.degrees(ANG):.2f} deg, strip_frame tilt {TILT:.2f} deg about +X, centre (z, y) "
          f"({SC[0]:.4f}, {SC[1]:.4f})")
    lo, hi = C.D.bounds()
    print(f"{C.TAG} bounds Godot x [{lo.x:.3f}, {hi.x:.3f}] y [{lo.z:.3f}, {hi.z:.3f}] z [{-hi.y:.3f}, {-lo.y:.3f}]")
    for nm in ("IA_speed", "IA_play", "IA_eject"):
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
        C.studio(NAME, tuple(C.G(0.55, 0.50, 0.72)), tuple(C.G(0.0, 0.08, 0.0)), lens=45, floor_z=0.0)
    # reel on, speed 4.75 (i = 1), VU up, play pressed
    C.qa_item("tape_reel", ob["deck_reel_mount"], C.proxy_tape_reel)
    C.pose_rot(ob["IA_speed"], "z", 45.0 - 30.0 * 1)
    C.pose_rot(ob["vu_needle"], "z", -52.0)
    C.pose_rot(ob["IA_play"], "x", -8.0)
    C.qa_emit(ob["vu_face"], "FFC070", 0.8)
    if "--only-views" not in args:
        C.studio(NAME + "_2", tuple(C.G(0.0, 0.34, 0.50)), tuple(C.G(-0.04, 0.09, 0.08)), lens=50, floor_z=0.0)
    C.place(roots, (4.15, 0.76, -3.05), 0.0)
    C.qa_room()
    C.qa_desk()
    C.import_model("card_punch", (3.25, 0.76, -3.05), 0.0)
    C.import_model("desk_lamp", (3.05, 0.76, -3.32), 0.0)
    C.qa_hall_lights()
    C.render(NAME + "_3", (4.15, 1.2, -2.35), (4.15, 0.82, -3.05), 40.0)
    C.render(NAME + "_4", (3.7, 1.6, -1.85), (3.7, 0.8, -3.1), 52.0)


main()
