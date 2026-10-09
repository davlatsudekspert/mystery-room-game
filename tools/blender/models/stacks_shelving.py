"""stacks_shelving.glb — double-sided steel archive stack "B-3" with a pneumatic-post terminal (Chapter 2, group B1).

Free-standing furniture: origin = floor level at the footprint centre. Placement (0, 0, 0.25), yaw 0.
Footprint 1.80 (x) x 0.90 (z), height 2.05 (+ the terminal up to 2.25).

  * slotted green-grey uprights (M_Steel_Painted) at x = -0.875 / 0 / +0.875, dark steel shelves with folded lips
    (M_Steel_Dark), a central spine sheet, a dark kick plinth, top canopy; two bays per side, five shelves per bay
    (shelf tops y = 0.10, 0.525, 0.95, 1.375, 1.80);
  * end panels with brass range-label frames, 3D text "B-3";
  * both faces filled with archive boxes (M_Cardboard + M_Decal_BoxLabels strips, atlas 4 x 8), flat stacks of
    bound ledgers (M_Linen, M_Book_*), string-tied bundles;
  * pneumatic terminal on top: brass receiving bell, glass sight tube, top coupling at terminal_top (0, 2.25, 0) =
    world tube_p4, and the return tube inlet 0.14 m east (x = +0.14).

Parts:
  * IA_ledger: south face (+Z), right bay (+X), middle shelf: a thick ledger lying flat, fore-edge toward +Z,
    0.36 w x 0.07 h x 0.28 d; pivot = bottom-front-centre (0.40, 0.95, 0.39); slides +0.20 along local +Z.
  * ledger_cover: its top board, child of IA_ledger, pivot on the back (spine) edge (0, 0.064, -0.268) relative to
    the ledger; opens -110 deg about local +X. Under it the page block is hollowed (0.15 x 0.15 x 0.024 cavity).
  * ledger_reel_mount: child of IA_ledger in the cavity (tape reel lying flat, label up; centre of mass).
  * terminal_top: empty at (0, 2.25, 0).
  * static: stacks_frame, stacks_terminal, stacks_ledger_left / stacks_ledger_right (the ledger's neighbours),
    contents_<face>_<bay>_<level> (s = south/+Z, n = north/-Z; bay l = -X, r = +X; level 0..4 bottom -> top).

    blender -b --factory-startup -P tools/blender/models/stacks_shelving.py [-- --no-render] [-- --shots a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_furniture1 as F  # noqa: E402
from lib_ch2_furniture1 import G, gbox, gquad, gtext, prism  # noqa: E402

NAME = "stacks_shelving"
BUDGET = 12000
ST, DK, BR, CB, LN, PA = "M_Steel_Painted", "M_Steel_Dark", "M_Brass_Aged", "M_Cardboard", "M_Linen", "M_Paper"
LABEL = "M_Decal_BoxLabels"
HX, HZ, H = 0.90, 0.45, 2.05
POST = 0.035
POSTS_X = (-HX + POST / 2 + 0.005, 0.0, HX - POST / 2 - 0.005)      # post centres
BAYS = ((-HX + 0.045, -0.018), (0.018, HX - 0.045))                  # usable x per bay (l, r)
SHELF_Y = (0.10, 0.525, 0.95, 1.375, 1.80)
CANOPY_Y = 2.02
LIP = 0.028
# ledger (south face, right bay, middle shelf)
LX, LY, LZF = 0.40, 0.95, 0.39            # pivot: bottom-front-centre
LW, LH, LD = 0.36, 0.07, 0.28
BOARD = 0.006
PAGE_TOP = 0.064                          # page block top above the ledger bottom
CAV = (0.15, 0.024, 0.15)                 # cavity w x depth x d
SLIDE, COVER_DEG = 0.20, -110.0


B3_CELLS = (1, 8, 10, 11, 14, 15, 17, 19, 20, 24, 29, 30, 31)    # atlas strips that read "B-3 / year / no."


def pick_label(r):
    """Mostly B-3 strips (this is stack B-3), a few misfiled ones."""
    return r.choice(B3_CELLS) if r.random() < 0.85 else r.randrange(32)


def atlas_uv(k):
    """UV rect of box-label strip k in the 4 x 8 atlas (row 0 at the top of the image)."""
    c, r = k % 4, (k // 4) % 8
    return (c / 4.0, 1.0 - (r + 1) / 8.0, (c + 1) / 4.0, 1.0 - r / 8.0)


# ---------------------------------------------------------------- frame
def build_frame():
    parts = []
    # kick plinth (dark, recessed) and canopy
    parts.append(gbox("plinth", (-HX + 0.01, 0.0, -HZ + 0.03), (HX - 0.01, 0.075, HZ - 0.03), DK, 0.002))
    parts.append(gbox("canopy", (-HX - 0.006, CANOPY_Y, -HZ - 0.006), (HX + 0.006, H, HZ + 0.006), ST, 0.004, 2))
    # end panels (outside the end posts)
    for s in (-1, 1):
        x0, x1 = sorted((s * (HX - 0.006), s * HX))
        parts.append(gbox(f"end_panel{s}", (x0, 0.0, -HZ), (x1, CANOPY_Y, HZ), ST, 0.002))
        # pressed stiffening ribs
        for y in (0.55, 1.05, 1.55):
            xo, xr = s * HX, s * (HX + 0.0012)
            parts.append(gbox(f"end_rib{s}{y}", (min(xo, xr), y - 0.008, -HZ + 0.06), (max(xo, xr), y + 0.008, HZ - 0.06),
                              ST, 0.0006))
        # brass range-label frames with "B-3" (one per face side of each end panel)
        for fz in (-0.22, 0.22):
            parts += range_label(f"rl{s}{fz}", s, 1.62, fz)
    # posts (slotted)
    for px in POSTS_X:
        for sz in (-1, 1):
            z0, z1 = sorted((sz * (HZ - POST), sz * HZ))
            parts.append(gbox(f"post{px}{sz}", (px - POST / 2, 0.0, z0), (px + POST / 2, CANOPY_Y, z1), ST, 0.0015))
            parts += slots(f"slots{px}{sz}", px, sz * HZ, sz)
    # shelves: top plate over the whole depth + folded lips on both faces, per bay; spine sheet per bay
    for b, (xa, xb) in enumerate(BAYS):
        for k, y in enumerate(SHELF_Y):
            parts.append(gbox(f"shelf{b}{k}", (xa - 0.016, y - 0.0025, -HZ + 0.004), (xb + 0.016, y, HZ - 0.004), DK, 0.0006))
            for sz in (-1, 1):
                z0, z1 = sorted((sz * (HZ - 0.004), sz * (HZ - 0.0055)))
                parts.append(gbox(f"lip{b}{k}{sz}", (xa - 0.016, y - LIP, z0), (xb + 0.016, y, z1), DK, 0.0006))
        parts.append(gbox(f"spine{b}", (xa - 0.016, 0.075, -0.0025), (xb + 0.016, CANOPY_Y, 0.0025), ST, 0.0))
        # little card holders on the middle-shelf lips (both faces)
        for sz in (-1, 1):
            for cx in (xa + 0.12, xb - 0.12):
                parts += lip_card(f"lc{b}{sz}{cx:.2f}", cx, SHELF_Y[2] - LIP / 2, sz)
    return F.part("stacks_frame", parts)


def slots(tag, x, zf, sz):
    """Column of dark slots on the post face (the perforations)."""
    verts, faces = [], []
    z = zf + sz * 0.0004
    for k in range(38):
        y = 0.12 + k * 0.05
        for (u, v) in ((-0.003, -0.011), (0.003, -0.011), (0.003, 0.011), (-0.003, 0.011)):
            verts.append(G(x + u * sz, y + v, z))
        i = 4 * k
        faces.append((i, i + 1, i + 2, i + 3))
    me = bpy.data.meshes.new(tag)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(tag, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, DK)
    return [o]


def range_label(tag, s, y, z):
    """Brass frame with a cream card and the 3D text B-3 on the end panel outer face (x = s * HX)."""
    x = s * (HX + 0.0002)
    ex = (0, 0, -s)            # reads left -> right seen from outside the end panel
    parts = [F.gpoly(f"{tag}_frame", [A.rounded_rect(0.17, 0.095, 0.006, 2), A.rounded_rect(0.152, 0.077, 0.003, 2)],
                     0.003, (x, y, z), ex, (0, 1, 0), mat=BR, bevel=0.0006, drop_bottom=True),
             gquad(f"{tag}_card", (x + s * 0.0008, y, z), ex, (0, 1, 0), 0.153, 0.078, PA),
             gtext(f"{tag}_txt", "B-3", 0.052, (x + s * 0.0012, y, z), ex=ex, ey=(0, 1, 0), font=F.FONT_SANS_B,
                   mat="M_Lacquer_Black")]
    for k in (-1, 1):
        parts.append(F.screw(f"{tag}_scr{k}", 0.003, (x + s * 0.003, y, z + k * 0.078), (s, 0, 0), mat=BR, segs=6))
    return parts


def lip_card(tag, x, y, sz):
    z = sz * (HZ - 0.004)
    ex = (sz, 0, 0)
    return [F.gpoly(f"{tag}_f", [A.rounded_rect(0.07, 0.022, 0.003, 1), A.rounded_rect(0.062, 0.016, 0.002, 1)], 0.0015,
                    (x, y, z), ex, (0, 1, 0), mat=BR, bevel=0.0, drop_bottom=True),
            gquad(f"{tag}_c", (x, y, z + sz * 0.0006), ex, (0, 1, 0), 0.063, 0.017, PA)]


# ---------------------------------------------------------------- terminal
def build_terminal():
    parts = []
    y0 = H
    parts.append(gbox("term_plate", (-0.14, y0, -0.11), (0.21, y0 + 0.012, 0.11), DK, 0.003, 2))
    bell = [(0.088, 0.0), (0.088, 0.010), (0.080, 0.014), (0.074, 0.024), (0.064, 0.050), (0.056, 0.080),
            (0.054, 0.096), (0.060, 0.100), (0.060, 0.114), (0.050, 0.118)]
    parts.append(F.glathe("term_bell", bell, (0.0, y0 + 0.012, 0.0), axis="y", segments=24, mat=BR))
    # sight glass + top coupling (the room's glass tube, r 0.045, joins at y = 2.25)
    yg0 = y0 + 0.012 + 0.118
    parts.append(F.glathe("term_glass", [(0.0455, 0.0), (0.0455, 0.060), (0.0405, 0.060), (0.0405, 0.0)],
                          (0.0, yg0, 0.0), axis="y", segments=24, mat="M_Glass"))
    parts.append(F.glathe("term_collar", [(0.050, 0.0), (0.058, 0.004), (0.058, 0.022), (0.052, 0.026), (0.0455, 0.026),
                                          (0.0455, 0.0)], (0.0, 2.25 - 0.026, 0.0), axis="y", segments=24, mat=BR))
    for k in range(4):                       # tie rods between the bell shoulder and the top collar
        a = math.radians(45 + 90 * k)
        parts.append(F.gcyl(f"term_rod{k}", 0.003, 2.25 - 0.026 - (yg0 - 0.004), (0.054 * math.cos(a), yg0 - 0.004,
                            0.054 * math.sin(a)), axis="y", verts=6, mat=BR, bevel=0.0))
    # return-tube inlet 0.14 m east: coupling, short glass, elbow into the bell side
    xr = 0.14
    parts.append(F.glathe("ret_collar", [(0.050, 0.0), (0.056, 0.004), (0.056, 0.020), (0.0455, 0.022), (0.0455, 0.0)],
                          (xr, 2.25 - 0.022, 0.0), axis="y", segments=16, mat=BR))
    parts.append(F.glathe("ret_glass", [(0.0455, 0.0), (0.0455, 0.045), (0.0405, 0.045), (0.0405, 0.0)],
                          (xr, 2.25 - 0.022 - 0.045, 0.0), axis="y", segments=16, mat="M_Glass"))
    yb = 2.25 - 0.067
    elbow = A.tube("ret_elbow", [G(xr, yb + 0.004, 0.0), G(xr, y0 + 0.075, 0.0), G(0.050, y0 + 0.075, 0.0)], 0.036,
                   sides=14, fillet=0.045, fillet_segs=5, mat=BR)
    parts.append(elbow)
    parts.append(F.gcyl("ret_flange", 0.041, 0.008, (xr, yb - 0.004, 0.0), axis="y", verts=16, mat=BR, bevel=0.001))
    # arrival bell on a bracket (-X side) and a small enamel plate
    parts.append(F.gcyl("bell_post", 0.004, 0.07, (-0.105, y0 + 0.012, 0.05), axis="y", verts=6, mat=BR, bevel=0.0))
    parts.append(F.glathe("bell_dome", [(0.0, 0.0), (0.024, 0.0), (0.023, 0.006), (0.018, 0.016), (0.010, 0.022),
                                        (0.0, 0.024)], (-0.105, y0 + 0.08, 0.05), axis="y", segments=16, mat="M_Brass_Polished"))
    return F.part("stacks_terminal", parts)


# ---------------------------------------------------------------- contents
class Shelf:
    """Fills one shelf compartment (face sz, x range) with boxes, ledgers and bundles."""

    def __init__(self, tag, sz, xa, xb, y, clear, rnd):
        self.tag, self.sz, self.xa, self.xb, self.y, self.clear, self.r = tag, sz, xa, xb, y, clear, rnd
        self.parts = []
        self.k = 0

    def _n(self, kind):
        self.k += 1
        return f"{self.tag}_{kind}{self.k}"

    def zf(self, inset=0.0):
        return self.sz * (HZ - 0.03 - inset)

    def box(self, x0, w, h, d=0.36, label=True, lean=0.0):
        r = self.r
        zf = self.zf(r.uniform(0.0, 0.025))
        zb = zf - self.sz * d
        objs = [gbox(self._n("box"), (x0, self.y, min(zf, zb)), (x0 + w, self.y + h, max(zf, zb)), CB, 0.0025)]
        if label:
            lw, lh = min(0.8 * w, 0.075), min(0.8 * w, 0.075) / 2.0
            objs.append(gquad(self._n("lbl"), (x0 + w / 2, self.y + h - 0.07, zf + self.sz * 0.0006), (self.sz, 0, 0),
                              (0, 1, 0), lw, lh, LABEL, uv=atlas_uv(pick_label(r))))
            hole = [(0.012 * math.cos(a), 0.006 * math.sin(a)) for a in [2 * math.pi * i / 6 for i in range(6)]]
            objs.append(F.gpoly(self._n("hole"), [hole], 0.0004, (x0 + w / 2, self.y + 0.06, zf), (self.sz, 0, 0),
                                (0, 1, 0), mat="M_Bakelite", bevel=0.0, drop_bottom=True))
        if lean:
            piv = G(x0 + (w if lean < 0 else 0.0), self.y, 0.0)
            rot = F.Matrix.Translation(piv) @ F.Matrix.Rotation(math.radians(lean), 4, (0, 1, 0)) @ \
                F.Matrix.Translation(-piv)
            for o in objs:
                M.apply_transform(o)
                o.data.transform(rot)
        self.parts += objs

    def ledger_stack(self, x0, w, n, d=0.30, y=None):
        r = self.r
        yy = self.y if y is None else y
        for i in range(n):
            t = r.uniform(0.045, 0.07)
            ww = w - r.uniform(0.0, 0.02)
            dd = d - r.uniform(0.0, 0.03)
            xo = x0 + r.uniform(0.0, w - ww)
            zf = self.zf(r.uniform(0.0, 0.02))
            zb = zf - self.sz * dd
            cover = r.choice((LN, LN, "M_Book_Brown", "M_Book_Green", "M_Book_Black", "M_Book_Red"))
            z0, z1 = min(zf, zb), max(zf, zb)
            self.parts.append(gbox(self._n("lb"), (xo, yy, z0), (xo + ww, yy + t, z1), cover, 0.002))
            # page edge on the fore-edge (inset strip)
            za, zb2 = (z0 - 0.0004, z0 + 0.004) if self.sz < 0 else (z1 - 0.004, z1 + 0.0004)
            self.parts.append(gbox(self._n("lp"), (xo + 0.004, yy + 0.004, za), (xo + ww - 0.004, yy + t - 0.004, zb2),
                                   PA, 0.0))
            yy += t
        return yy

    def bundle(self, x0, w, h, d=0.32):
        r = self.r
        zf = self.zf(r.uniform(0.0, 0.02))
        zb = zf - self.sz * d
        z0, z1 = min(zf, zb), max(zf, zb)
        self.parts.append(gbox(self._n("bd"), (x0, self.y, z0), (x0 + w, self.y + h, z1), PA, 0.004))
        for fx in (0.3, 0.7):
            xs = x0 + w * fx
            self.parts.append(gbox(self._n("tw"), (xs - 0.003, self.y - 0.0005, z0 - 0.002),
                                   (xs + 0.003, self.y + h + 0.0015, z1 + 0.002), LN, 0.0))

    def fill(self, reserve=()):
        """Random run left -> right. reserve = [(x0, x1)] to keep empty."""
        r = self.r
        x = self.xa + r.uniform(0.0, 0.02)
        tall = self.clear > 0.3
        while x < self.xb - 0.06:
            blocked = next(((a, b) for (a, b) in reserve if a - 0.01 < x + 0.13 and x < b), None)
            if blocked:
                x = blocked[1] + 0.01
                continue
            room = self.xb - x
            pick = r.random()
            if tall and pick < 0.62 and room > 0.08:
                w = min(room, r.uniform(0.085, 0.125))
                h = r.uniform(0.25, min(0.31, self.clear - 0.04))
                lean = 0.0
                self.box(x, w, h, lean=lean)
                x += w + r.uniform(0.0, 0.006)
            elif pick < 0.80 and room > 0.27:
                w = r.uniform(0.25, min(0.33, room))
                n = r.randint(2, 3) if tall else r.randint(1, 2)
                self.ledger_stack(x, w, n)
                x += w + r.uniform(0.01, 0.03)
            elif pick < 0.90 and room > 0.22:
                w = r.uniform(0.20, min(0.26, room))
                self.bundle(x, w, r.uniform(0.06, 0.10 if tall else 0.08))
                x += w + r.uniform(0.01, 0.03)
            elif not tall and room > 0.25:
                w = r.uniform(0.24, min(0.30, room))         # box lying on its side (top shelf)
                self.box(x, w, r.uniform(0.09, 0.12), d=0.34, label=True)
                x += w + r.uniform(0.01, 0.03)
            else:
                x += r.uniform(0.04, 0.10)                   # gap
        return self.parts


def build_contents():
    objs = []
    for sz, face in ((1, "s"), (-1, "n")):
        for b, (xa, xb) in enumerate(BAYS):
            for k, y in enumerate(SHELF_Y):
                clear = (SHELF_Y[k + 1] - LIP if k < 4 else CANOPY_Y) - y
                rnd = random.Random(1000 * (sz + 2) + 100 * b + k)
                tag = f"c{face}{b}{k}"
                sh = Shelf(tag, sz, xa + 0.004, xb - 0.004, y, clear, rnd)
                if face == "s" and b == 1 and k == 2:
                    # the ledger's shelf: two standing boxes left, the IA ledger, a stack of flat ledgers right
                    left = Shelf(tag + "L", sz, xa, xb, y, clear, random.Random(77))
                    left.box(xa + 0.012, 0.092, 0.285)
                    left.box(xa + 0.108, 0.088, 0.27)
                    objs.append(F.part("stacks_ledger_left", left.parts))
                    right = Shelf(tag + "R", sz, xa, xb, y, clear, random.Random(78))
                    right.ledger_stack(LX + LW / 2 + 0.02, 0.25, 3, d=0.30)
                    objs.append(F.part("stacks_ledger_right", right.parts))
                    continue
                parts = sh.fill()
                if parts:
                    objs.append(F.part(f"contents_{face}_{'lr'[b]}_{k}", parts))
    return objs


# ---------------------------------------------------------------- the hollow ledger
def build_ledger():
    x0, x1 = LX - LW / 2, LX + LW / 2
    zb, zf = LZF - LD, LZF
    y0 = LY
    parts = []
    # spine (rounded, leather) and the bottom board (cloth over board, leather corners)
    sp = gbox("lg_spine", (x0, y0 - 0.0005, zb), (x1, y0 + LH + 0.0005, zb + 0.014), "M_Leather", 0.006, 3)
    parts.append(sp)
    parts.append(gbox("lg_board_b", (x0, y0, zb + 0.006), (x1, y0 + BOARD, zf), LN, 0.0012))
    for s in (-1, 1):
        xc = x1 if s > 0 else x0
        tri = [(xc, zf), (xc - s * 0.045, zf), (xc, zf - 0.045)]
        parts.append(prism(f"lg_corner_b{s}", [(p[0], p[1]) for p in tri], y0 - 0.0006, y0 + BOARD + 0.0006, axis="y",
                           mat="M_Leather"))
    # page block with a cavity: floor slab + four walls
    px0, px1, pz0, pz1 = x0 + 0.004, x1 - 0.004, zb + 0.014, zf - 0.003
    yp0, yp1 = y0 + BOARD, y0 + PAGE_TOP
    cw, cdep, cd = CAV
    cz = (pz0 + pz1) / 2
    cx0, cx1, cz0, cz1 = LX - cw / 2, LX + cw / 2, cz - cd / 2, cz + cd / 2
    ycf = yp1 - cdep
    parts.append(gbox("lg_pages_floor", (px0, yp0, pz0), (px1, ycf, pz1), PA, 0.0))
    for nm, mn, mx in (("l", (px0, ycf, pz0), (cx0, yp1, pz1)), ("r", (cx1, ycf, pz0), (px1, yp1, pz1)),
                       ("b", (cx0, ycf, pz0), (cx1, yp1, cz0)), ("f", (cx0, ycf, cz1), (cx1, yp1, pz1))):
        parts.append(gbox(f"lg_pages_{nm}", mn, mx, PA, 0.0))
    # cut-page texture in the cavity: a dark floor (the cut paper is darker) and a bookmark slip on the fore-edge
    parts.append(gbox("lg_cav_floor", (cx0 + 0.001, ycf, cz0 + 0.001), (cx1 - 0.001, ycf + 0.0006, cz1 - 0.001), "M_Felt",
                      0.0))
    parts.append(gbox("lg_slip", (LX + 0.08, yp0 + 0.03, zf - 0.02), (LX + 0.105, yp0 + 0.0306, zf + 0.025), PA, 0.0))
    ledger = F.part("IA_ledger", parts, pivot=(LX, LY, LZF))
    # cover (top board), hinged on the spine edge
    cparts = [gbox("lg_board_t", (x0, yp1, zb + 0.006), (x1, yp1 + BOARD, zf), LN, 0.0012)]
    for s in (-1, 1):
        xc = x1 if s > 0 else x0
        tri = [(xc, zf), (xc - s * 0.045, zf), (xc, zf - 0.045)]
        cparts.append(prism(f"lg_corner_t{s}", tri, yp1 - 0.0006, yp1 + BOARD + 0.0006, axis="y", mat="M_Leather"))
    cparts.append(gquad("lg_cover_label", (LX, yp1 + BOARD + 0.0004, (zb + zf) / 2 + 0.02), (1, 0, 0), (0, 0, -1), 0.11,
                        0.055, LABEL, uv=atlas_uv(11)))
    cover = F.part("ledger_cover", cparts, pivot=(LX, yp1, zb + 0.014))
    F.parent(cover, ledger)
    # tape_reel.glb lies flat, label up, its lowest point 0.0052 below its centre of mass
    mount = F.mount("ledger_reel_mount", (LX, ycf + 0.0006 + 0.0055, cz), par=ledger)
    return ledger, cover, mount


def build():
    M.reset_scene()
    F.ensure_materials()
    F.decal_material(LABEL, "box_labels.jpg", color="DCCFB2")
    build_frame()
    build_terminal()
    build_contents()
    ledger, cover, mount = build_ledger()
    F.finalize_all(wood_grain=False)
    F.mount("terminal_top", (0.0, 2.25, 0.0))
    return F.report(NAME), ledger, cover, mount


def verify(path):
    req = ["terminal_top", "IA_ledger", "ledger_cover", "ledger_reel_mount"]
    expect = {"terminal_top": (0.0, 2.25, 0.0), "IA_ledger": (LX, LY, LZF)}
    return F.verify_glb(path, required=req, identity=req, budget=BUDGET, expect=expect, show=req)


POS, YAW = (0.0, 0.0, 0.25), 0.0


def main():
    args = M.main_guard()
    _, ledger, cover, mount = build()
    path = F.export(NAME)
    F.check_names(path)
    errs = verify(path)
    if errs:
        print(f"{F.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    F.qa_begin()
    F.qa_place(POS, YAW)
    F.qa_room()
    F.qa_neighbours([("reading_table", (1.9, 0, 1.0), 0.0), ("floor_hatch", (0.9, 0.0, 2.5), 0.0),
                     ("lockers", (0.6, 0.0, 3.5), 180.0), ("archive_pendant", (0.0, 3.6, 1.6), 0.0)])
    F.qa_room_lights(150.0)
    F.qa_light("fill", "AREA", (0.3, 1.8, 2.3), 70.0, "FFE6CC", radius=1.6, target=(0.0, 1.0, 0.7))
    if F.want("hero", args):
        F.shoot(NAME, (2.3, 1.75, 2.4), (0.0, 1.15, 0.3), vfov=52)
    if F.want("view", args):
        F.shoot(NAME + "_2", (0.0, 1.5, 2.3), (0.0, 1.1, 0.7), vfov=56)
    if F.want("top", args):
        F.shoot(NAME + "_3", (0.9, 2.3, 1.4), (0.0, 2.12, 0.25), vfov=40)
    if F.want("ledger", args):
        F.shoot(NAME + "_4", (0.4, 1.3, 1.5), (0.35, 1.0, 0.65), vfov=40)
    # ledger open: slide + cover, a reel in the cavity
    F.pose_slide(ledger, (0.0, 0.0, SLIDE))
    F.pose_rot(cover, "x", COVER_DEG)
    F.item_or_proxy("tape_reel", mount)
    if F.want("ledger_open", args):
        F.shoot(NAME + "_5", (0.4, 1.3, 1.5), (0.35, 1.0, 0.65), vfov=40)


main()
