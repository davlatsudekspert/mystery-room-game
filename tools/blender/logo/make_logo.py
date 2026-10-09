"""MYSTERY ROOM: The Forgotten Institute — logo + app-icon renders (three variants).

    blender -b --factory-startup -P tools/blender/logo/make_logo.py -- --variant A [--jobs icon,fg,bg,mono,wordmark]
            [--draft] [--out qa/logo/A]

Variants (all 100% procedural geometry; fonts: Cormorant Garamond, OFL, from game/assets/fonts):
  A  "Lumen Emblem"     brass Institute mark (instrument ring + meridian needle) holding a glowing crystal.
  B  "Keyhole of Light" ornate brass escutcheon on a green-enamel door, Lumen light pouring out of the keyhole.
  C  "Lumen Key"        antique brass key whose bow is the Institute ring with a glowing crystal, on velvet.

Jobs: icon (1024 full-bleed), fg / bg (Android adaptive 432 layers), mono (432 white silhouette),
      wordmark (2400 px wide, transparent). Cycles CPU, 2 threads, <= 96 samples + OpenImageDenoise.
"""
from __future__ import annotations

import math
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logo_lib as G  # noqa: E402

ROOT = G.ROOT


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opt = {"variant": "A", "jobs": "icon,fg,bg,mono,wordmark", "draft": False, "out": None, "samples": None}
    i = 0
    while i < len(a):
        k = a[i]
        if k == "--draft":
            opt["draft"] = True
        elif k.startswith("--") and i + 1 < len(a):
            opt[k[2:]] = a[i + 1]
            i += 1
        i += 1
    opt["variant"] = opt["variant"].upper()
    if opt["out"] is None:
        opt["out"] = os.path.join(ROOT, "qa", "logo", opt["variant"] + ("_draft" if opt["draft"] else ""))
    opt["out"] = os.path.abspath(opt["out"])
    return opt


# ======================================================================= shared materials
def brass_set():
    class S:
        pass
    s = S()
    s.aged = G.mat_brass("LG_BrassAged", hi="E4C887", lo="8E723F", rough=0.24, rough_var=0.14, crevice=0.8)
    s.pol = G.mat_brass("LG_BrassPol", hi="F2DCA2", lo="BC9A58", rough=0.12, rough_var=0.07, crevice=0.6, bump=0.12)
    s.satin = G.mat_brass("LG_BrassSatin", hi="D2AA66", lo="8F6B36", rough=0.3, rough_var=0.08, crevice=0.5,
                          bump=0.05, aniso=0.8, radial=True)
    s.eng = G.mat_engrave()
    return s


def scaled(pts, s):
    return [(x * s, y * s) for (x, y) in pts]


# ======================================================================= crystal (rose cut)
def rose_gem(name, R, zg0, zg1, crown, pav, n=12, mat=None):
    """Rose-cut gem: pavilion point, short girdle band, two staggered rings of crown facets, apex."""
    import bmesh
    bm = bmesh.new()
    spec = [(0.0, zg0 - pav, 0.0), (R, zg0, 0.0), (R, zg1, 0.0), (R * 0.80, zg1 + crown * 0.42, 0.5),
            (R * 0.44, zg1 + crown * 0.82, 0.0), (0.0, zg1 + crown, 0.0)]
    rings = []
    for (r, z, ph) in spec:
        if r < 1e-9:
            rings.append([(0.0, bm.verts.new((0, 0, z)))])
        else:
            ring = []
            for i in range(n):
                a = (i + ph) * G.TAU / n
                ring.append((a, bm.verts.new((r * math.cos(a), r * math.sin(a), z))))
            rings.append(ring)
    for A, B in zip(rings[:-1], rings[1:]):
        if len(A) == 1 or len(B) == 1:
            c = A[0][1] if len(A) == 1 else B[0][1]
            R_ = B if len(A) == 1 else A
            for i in range(len(R_)):
                bm.faces.new((c, R_[i][1], R_[(i + 1) % len(R_)][1]))
            continue
        # zipper triangulation by angle
        ia = ib = 0
        na, nb = len(A), len(B)
        angA = [a for a, _ in A] + [A[0][0] + G.TAU]
        angB = [a for a, _ in B] + [B[0][0] + G.TAU]
        if angB[0] < angA[0]:
            angA = [x + G.TAU if x < angB[0] else x for x in angA]
        while ia < na or ib < nb:
            va, vb = A[ia % na][1], B[ib % nb][1]
            if ib >= nb or (ia < na and angA[ia + 1] <= angB[ib + 1]):
                bm.faces.new((va, A[(ia + 1) % na][1], vb))
                ia += 1
            else:
                bm.faces.new((va, B[(ib + 1) % nb][1], vb))
                ib += 1
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = G.link(bpy.data.objects.new(name, me))
    if mat is not None:
        G.set_mat(obj, mat)
    G.shade(obj, 0.0)
    return obj


def crystal_unit(prefix, s, z_seat, R, mats, glow=1.0, lights=True, front_energy=6.0, back_energy=30.0,
                 back_z=None):
    """Glowing Lumen crystal seated at z_seat (girdle bottom) with an emissive bed under it and two
    cyan point lights (front: lights the bezel; back: haloes the backdrop). Returns (objs, lights)."""
    gem = rose_gem(prefix + "_gem", R * s, z_seat * s, (z_seat + 0.015) * s, 0.072 * s, 0.032 * s,
                   n=12, mat=G.mat_crystal("LG_Crystal", tint="9EE9FF", glow="1EC0FF", glow_strength=9.0 * glow / max(s, 1e-3)))
    gem.visible_shadow = False
    bed = G.lathe(prefix + "_bed", [(0.0, (z_seat - 0.034) * s), (R * 1.02 * s, (z_seat - 0.034) * s)],
                  segments=64, mat=G.mat_glow_disc("LG_GlowBed", strength=3.2 * glow, radius=R * s))
    bed.visible_shadow = False
    objs = [gem, bed]
    lts = []
    if lights:
        lts.append(G.light("POINT", prefix + "_lf", (0, 0, (z_seat + 0.12) * s), energy=front_energy * s * s,
                           color="7FE4FF", size=0.05 * s))
        bz = (z_seat - 0.2) if back_z is None else back_z
        lts.append(G.light("POINT", prefix + "_lb", (0, 0, bz * s), energy=back_energy * s * s,
                           color="45CFFF", size=0.08 * s))
    return objs, lts


# ======================================================================= A — emblem
def needle_outline():
    """Meridian needle (compass-needle silhouette with a central boss), symmetric, closed, CCW."""
    hw, boss = 0.030, 0.205
    top = [(0.0, 0.705), (0.043, 0.622), (0.019, 0.556), (0.031, 0.531), (hw, 0.47)]
    yj = math.sqrt(boss * boss - hw * hw)
    a0 = math.atan2(yj, hw)
    arc = [(boss * math.cos(a0 - (2 * a0) * k / 24), boss * math.sin(a0 - (2 * a0) * k / 24)) for k in range(25)]
    right = top + arc + [(x, -y) for (x, y) in reversed(top)]
    right_r = [0.006, 0.012, 0.010, 0.004, 0.0] + [0.02] + [0.0] * 23 + [0.02] + [0.0, 0.004, 0.010, 0.012, 0.006]
    left = [(-x, y) for (x, y) in reversed(right[1:-1])]
    left_r = list(reversed(right_r[1:-1]))
    pts = right + left            # clockwise when seen from +Z -> reverse for CCW
    rr = right_r + left_r
    pts = list(reversed(pts))
    rr = list(reversed(rr))
    return G.fillet(pts, 0.0, segs=5, closed=True, radii=rr)


def emblem(s=1.0, glow=1.0, detail=True, lights=True, prefix="em", front_energy=1.2, back_energy=14.0,
           inner_ring=False, dial=False):
    """The Institute mark in brass, radius 0.505*s, facing +Z, back plane at z = -0.05*s.
    Returns dict(subject=[objs], cut=[objs for mono holdout], lights=[...])."""
    m = brass_set()
    parts, cut = [], []
    # ---- outer instrument ring
    sharp = [(0.505, -0.05), (0.505, 0.055), (0.496, 0.080), (0.468, 0.082), (0.460, 0.062), (0.457, 0.046),
             (0.418, 0.046), (0.412, 0.060), (0.398, 0.066), (0.387, 0.052), (0.387, -0.05)]
    radii = [0, 0.012, 0.010, 0.010, 0.004, 0.0015, 0.0015, 0.004, 0.006, 0.008, 0]
    ring = G.lathe(prefix + "_ring", scaled(G.fillet(sharp, 0, 5, radii=radii), s), segments=256, mat=m.aged)
    G.add_mat_where(ring, m.satin, lambda c, n: n.z > 0.97 and 0.416 * s < math.hypot(c.x, c.y) < 0.459 * s
                    and c.z < 0.05 * s)
    parts.append(ring)
    # ---- engraved scale on the satin dial band
    if detail:
        loops = []
        for k in range(72):
            a = math.radians(k * 5.0)
            if abs(math.cos(a)) < 0.10:
                continue
            ln, wd = (0.030, 0.0058) if k % 6 == 0 else ((0.021, 0.0042) if k % 3 == 0 else (0.013, 0.0029))
            rc = 0.453 - ln / 2
            loops.append(scaled(G.rect(rc * math.cos(a), rc * math.sin(a), ln, wd, a), s))
        ticks = G.inlay(prefix + "_ticks", loops, 0.0462 * s, m.eng)
        line = G.inlay(prefix + "_scale", [scaled(G.circle(0.4228, 256), s), scaled(G.circle(0.4208, 256), s)],
                       0.0462 * s, m.eng)
        parts += [ticks, line]
    # ---- inner ring (optional: busier, reads as a target at small sizes)
    ir = None if not inner_ring else G.fillet([(0.313, -0.01), (0.313, 0.03), (0.287, 0.03), (0.287, -0.01)], 0, 4,
                  radii=[0, 0.008, 0.008, 0])
    if ir:
        parts.append(G.lathe(prefix + "_iring", scaled(ir, s), segments=192, mat=m.aged))
    # ---- meridian needle with engraved centre line and two screws
    needle = G.solid2d(prefix + "_needle", [scaled(needle_outline(), s)], 0.06 * s, 0.016 * s, bevel_res=4,
                       mat=m.pol, z0=0.045 * s)
    parts.append(needle)
    if detail:
        zl = 0.1052 * s
        ll = [scaled(G.rect(0, sgn * (0.215 + 0.415) / 2, 0.005, 0.415 - 0.215), s) for sgn in (1, -1)]
        ll += [scaled(G.rect(0, sgn * 0.5, 0.004, 0.05), s) for sgn in (1, -1)]
        parts.append(G.inlay(prefix + "_mline", ll, zl, m.eng))
        for sgn in (1, -1):
            sc = G.lathe(prefix + "_screw", scaled(G.fillet([(0.017, 0.103), (0.017, 0.110), (0.0, 0.118)], 0, 4,
                                                              radii=[0, 0.006, 0]), s), segments=48, mat=m.pol)
            sc.data.transform(Matrix.Translation((0, sgn * 0.445 * s, 0)))
            slot = G.inlay(prefix + "_slot", [scaled(G.rect(0, sgn * 0.445, 0.026, 0.0045, 0.5 + sgn * 0.3), s)],
                           0.1185 * s, m.eng)
            parts += [sc, slot]
    # ---- crystal bezel (polished, knurled band)
    bz = G.fillet([(0.178, 0.085), (0.178, 0.150), (0.170, 0.174), (0.150, 0.178), (0.141, 0.166), (0.137, 0.12),
                   (0.137, 0.10)], 0, 5, radii=[0, 0.008, 0.008, 0.004, 0.004, 0, 0])
    parts.append(G.lathe(prefix + "_bezel", scaled(bz, s), segments=160, mat=m.pol))
    import lib_mech as L
    kn = L.lathe2(prefix + "_knurl", [(0.174 * s, 0.098 * s), (0.1815 * s, 0.103 * s, "k"),
                                      (0.1815 * s, 0.142 * s, "k"), (0.174 * s, 0.147 * s)],
                  segments=144, knurl=0.0045 * s, cap_bottom=False, cap_top=False)
    G.set_mat(kn, m.aged)
    G.shade(kn, 35.0)
    parts.append(kn)
    cut.append(kn)
    cobjs, lts = crystal_unit(prefix, s, 0.135, 0.137, m, glow=glow, lights=lights,
                              front_energy=front_energy, back_energy=back_energy)
    parts += cobjs
    if dial:
        # recessed guilloche enamel dial: the mark becomes a medallion (never mistaken for a letter O)
        d = G.lathe(prefix + "_dial", scaled([(0.392, -0.03), (0.392, 0.004), (0.0, 0.004)], s), segments=192,
                    mat=G.mat_enamel_dial("LG_Dial", scale=s))
        parts.append(d)
        cut.append(d)
    return {"subject": parts, "cut": cut, "lights": lts, "crystal": cobjs}


# ======================================================================= scenes
def studio_world(scale=1.0, cam_color=None):
    G.world_studio("06090A", 1.0, panels=[
        ((-0.6, 0.5, 0.65), 0.93, 0.78, "FFD6A2", 2.2 * scale),     # big warm softbox, upper left
        ((-0.15, 0.35, 0.92), 0.985, 0.955, "FFE8C8", 0.45 * scale),  # overhead strip
        ((0.85, 0.15, 0.30), 0.975, 0.90, "A6D6EE", 0.7 * scale),    # cool window, right
        ((0.2, -0.9, 0.35), 0.96, 0.85, "3A3028", 0.5 * scale),      # dim warm bounce, front
    ], floor="221A12", floor_strength=0.12, cam_color=cam_color)


def icon_A(job, draft):
    E = emblem(1.0, dial=True)
    subj = E["subject"]
    bg = []
    back = G.plane("A_backdrop", 8, 8, (0, 0, -0.17), mat=G.mat_backdrop("LG_Backdrop", "0F2D31", "091A1D"))
    bg.append(back)
    G.light("AREA", "A_key", (-1.5, 1.7, 2.1), (0, 0, 0), energy=340, color="FFD6A0", size=0.9)
    G.light("AREA", "A_rim", (1.5, 1.4, 0.45), (0, 0, 0.05), energy=80, color="FFE6C4", size=0.5)
    G.light("AREA", "A_fill", (1.4, -1.6, 1.3), (0, 0, 0), energy=6, color="9CC7DD", size=1.6)
    G.light("AREA", "A_soft", (-0.5, 0.9, 4.2), (0, 0, 0), energy=25, color="FFE9CC", size=2.6, size_y=0.45)
    studio_world()
    cam = G.camera((0.30, -0.62, 3.4), (0, 0, 0.03), lens=100, dof_target=(0, 0, 0.1), fstop=2.8)

    def after(cam):
        if job != "icon":
            return []
        dm = G.mat_dust("LG_Dust", "FFE2B8", 0.5)
        lit = lambda u, v: 0.15 + 0.85 * max(0.0, min(1.0, (0.5 - u + v) / 1.2))
        near = G.dust("A_dust", 16, (-0.95, -0.95, 0.15), (0.95, 0.95, 0.5), 0.002, 0.0045, seed=7, mat=dm,
                      weight=lambda p: lit(p.x, p.y))
        far = G.dust_frustum("A_bokeh", cam, 6, 0.5, 1.2, 0.003, 0.009, seed=11, mat=G.mat_dust("LG_Bokeh", "FFE2B8", 0.25),
                             weight=lambda u, v: lit(u, v) * (1.0 if max(abs(u), abs(v)) > 0.3 else 0.0))
        return [near, far]
    return {"subject": subj, "background": bg, "cut": E["cut"], "cam": cam, "after": after, "frac_icon": 0.86}


def wordmark_A(draft):
    m = brass_set()
    letters = G.mat_brass("LG_Letters", hi="F0CC84", lo="A47E40", rough=0.2, rough_var=0.08, crevice=0.55, bump=0.1)
    t1 = G.text_obj("w_mystery", "MYSTERY", 1.0, extrude=0.07, bevel=0.013, spacing=1.08, mat=letters)
    t2 = G.text_obj("w_room", "ROOM", 1.0, extrude=0.07, bevel=0.013, spacing=1.08, mat=letters)
    lo1, hi1 = G.bounds([t1])
    lo2, hi2 = G.bounds([t2])
    cap = hi1.y                       # cap height (M) ~ 0.63
    es = 1.36 * cap / 1.01
    E = emblem(es, glow=1.0, front_energy=4.0, back_energy=0.0, dial=True)
    gap = 0.20
    ex = hi1.x + gap + 0.505 * es
    for o in E["subject"]:
        o.data.transform(Matrix.Translation((ex, cap / 2, 0.05 * es)))
    for lt in E["lights"]:
        lt.location += Vector((ex, cap / 2, 0.05 * es))
    t2.data.transform(Matrix.Translation((ex + 0.505 * es + gap - lo2.x, 0, 0)))
    allobj = [t1, t2] + E["subject"]
    lo, hi = G.bounds(allobj)
    cx = (lo.x + hi.x) / 2
    sub = G.text_obj("w_sub", "THE FORGOTTEN INSTITUTE", 0.205, font=G.FONT_BOLD, extrude=0.02, bevel=0.0035,
                     spacing=1.42, align="CENTER", mat=letters)
    los, his = G.bounds([sub])
    sy = min(lo.y - 0.07, -0.30) - his.y
    sub.data.transform(Matrix.Translation((cx - (los.x + his.x) / 2, sy, 0)))
    los, his = G.bounds([sub])
    rules = []
    for sgn in (-1, 1):
        x0 = (los.x - 0.09) if sgn < 0 else (his.x + 0.09)
        x1 = (lo.x + 0.02) if sgn < 0 else (hi.x - 0.02)
        a, b = min(x0, x1), max(x0, x1)
        ym = (los.y + his.y) / 2
        bar = G.solid2d("w_rule", [[(a, ym - 0.0075), (b, ym - 0.0075), (b, ym + 0.0075), (a, ym + 0.0075)]],
                        0.022, 0.006, bevel_res=2, mat=m.pol)
        dx = x0
        dia = G.solid2d("w_dia", [[(dx - sgn * 0.035, ym), (dx, ym - 0.022), (dx + sgn * 0.035, ym),
                                   (dx, ym + 0.022)]], 0.03, 0.007, bevel_res=2, mat=m.pol)
        rules += [bar, dia]
    allobj += [sub] + rules
    return {"objs": allobj, "letters": [t1, t2, sub], "glow_at": (ex, cap / 2)}



# ======================================================================= B — keyhole escutcheon
def plate_outline():
    half = [(0.0, 0.512), (0.075, 0.482), (0.160, 0.448), (0.240, 0.398), (0.272, 0.318),
            (0.232, 0.240), (0.282, 0.130), (0.298, 0.010), (0.278, -0.110), (0.222, -0.196), (0.262, -0.276),
            (0.246, -0.372), (0.150, -0.438), (0.068, -0.466), (0.0, -0.492)]
    full = half + [(-x, y) for (x, y) in reversed(half[1:-1])]
    pts = G.catmull(full, 8, closed=True)
    pts = list(reversed(pts))          # half goes clockwise (top -> right -> bottom); make it CCW
    return pts


KH = dict(cx=0.0, cy=0.085, r=0.083, hw_top=0.034, hw_bot=0.058, slot=0.235)


def escutcheon(s=1.0, prefix="es", detail=True, glow=1.0, cover_on=False):
    """Ornate brass escutcheon: lobed cartouche plate, polished bead border with a row of pearls,
    engraved sunburst around a raised keyhole rim, two screws and a swung-aside drop cover.
    Lies on z=0 (door surface), faces +Z. Returns dict(subject, cut, keyhole)."""
    m = brass_set()
    parts, cut = [], []
    outline = plate_outline()
    kh = G.keyhole(KH["cx"], KH["cy"], KH["r"], KH["hw_top"], KH["hw_bot"], KH["slot"])
    plate = G.solid2d(prefix + "_plate", [scaled(outline, s), scaled(kh, s)], 0.05 * s, 0.02 * s, bevel_res=4,
                      mat=m.aged, z0=0.0)
    parts.append(plate)
    top = 0.05 * s
    o1 = G.offset_poly(outline, 0.028)
    o2 = G.offset_poly(outline, 0.050)
    border = G.solid2d(prefix + "_border", [scaled(o1, s), scaled(o2, s)], 0.022 * s, 0.0095 * s, bevel_res=3,
                       mat=m.pol, z0=top - 0.004 * s)
    parts.append(border)
    rim_o = G.offset_poly(kh, -0.024)
    rim = G.solid2d(prefix + "_rim", [scaled(rim_o, s), scaled(kh, s)], 0.024 * s, 0.0095 * s, bevel_res=3,
                    mat=m.pol, z0=top - 0.004 * s)
    parts.append(rim)
    if detail:
        # pearls along an inner line
        line = G.offset_poly(outline, 0.074)
        per = [0.0]
        for i in range(1, len(line) + 1):
            a, b = Vector(line[i - 1]), Vector(line[i % len(line)])
            per.append(per[-1] + (b - a).length)
        total = per[-1]
        npearl = int(total / 0.036)
        import bmesh
        bm = bmesh.new()
        for k in range(npearl):
            d = total * k / npearl
            i = max(j for j in range(len(per)) if per[j] <= d)
            a, b = Vector(line[i % len(line)]), Vector(line[(i + 1) % len(line)])
            t = (d - per[i]) / max(per[i + 1] - per[i], 1e-9)
            p = a.lerp(b, t)
            if abs(p.x) < 0.04 and abs(abs(p.y) - 0.37) < 0.05:      # leave room for the screws
                continue
            r = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.0105 * s)
            bmesh.ops.scale(bm, vec=(1, 1, 0.75), verts=r["verts"])
            bmesh.ops.translate(bm, vec=(p.x * s, p.y * s, top), verts=r["verts"])
        me = bpy.data.meshes.new(prefix + "_pearls")
        bm.to_mesh(me)
        bm.free()
        pearls = G.link(bpy.data.objects.new(prefix + "_pearls", me))
        G.set_mat(pearls, m.pol)
        G.shade(pearls, 180)
        parts.append(pearls)
        # engraved sunburst rays from the keyhole centre, clipped to the pearl line
        c = (KH["cx"], KH["cy"] - 0.03)
        clip = G.offset_poly(outline, 0.095)
        loops = []
        for k in range(40):
            a = math.pi / 2 + k * G.TAU / 40
            if math.sin(a) < -0.93:
                continue
            r0 = 0.155 if math.sin(a) > -0.6 else 0.20
            r1 = G.ray_poly(c, a, clip) - 0.006
            if k % 2:
                r1 = r0 + (r1 - r0) * 0.72
            if r1 - r0 < 0.02:
                continue
            w0, w1 = 0.011, 0.0035
            ca, sa = math.cos(a), math.sin(a)
            nx, ny = -sa, ca
            loops.append(scaled([(c[0] + ca * r0 + nx * w0 / 2, c[1] + sa * r0 + ny * w0 / 2),
                                 (c[0] + ca * r0 - nx * w0 / 2, c[1] + sa * r0 - ny * w0 / 2),
                                 (c[0] + ca * r1 - nx * w1 / 2, c[1] + sa * r1 - ny * w1 / 2),
                                 (c[0] + ca * r1 + nx * w1 / 2, c[1] + sa * r1 + ny * w1 / 2)], s))
        parts.append(G.inlay(prefix + "_rays", loops, top + 0.0003 * s, m.eng))
        inner_line = [scaled(G.offset_poly(outline, 0.056), s), scaled(G.offset_poly(outline, 0.061), s)]
        parts.append(G.inlay(prefix + "_line", inner_line, top + 0.0003 * s, m.eng))
        # screws
        for sy in (0.37, -0.37):
            sc = G.lathe(prefix + "_screw", scaled(G.fillet([(0.026, 0.0), (0.026, 0.008), (0.0, 0.019)], 0, 5,
                                                             radii=[0, 0.01, 0]), s), segments=48, mat=m.pol)
            sc.data.transform(Matrix.Translation((0, sy * s, top)))
            slot = G.inlay(prefix + "_slot", [scaled(G.rect(0, sy, 0.042, 0.0065, 0.35 if sy > 0 else -0.6), s)],
                           top + 0.0192 * s, m.eng)
            parts += [sc, slot]
        # drop cover, swung aside on its pivot above the keyhole
        piv = (0.0, 0.232)
        cov = G.catmull([(0.0, 0.03), (0.032, 0.0), (0.040, -0.09), (0.0, -0.20), (-0.040, -0.09), (-0.032, 0.0)],
                        8, closed=True)
        cov = list(reversed(cov)) if G.poly_area(cov) < 0 else cov
        cover = G.solid2d(prefix + "_cover", [scaled(cov, s)], 0.014 * s, 0.006 * s, bevel_res=3, mat=m.pol,
                          z0=0.0)
        rot = Matrix.Rotation(math.radians(78.0), 4, "Z")
        cover.data.transform(Matrix.Translation((piv[0] * s, piv[1] * s, top + 0.022 * s)) @ rot)
        pin = G.lathe(prefix + "_pin", scaled(G.fillet([(0.017, 0.0), (0.017, 0.006), (0.0, 0.014)], 0, 4,
                                                        radii=[0, 0.007, 0]), s), segments=32, mat=m.pol)
        pin.data.transform(Matrix.Translation((piv[0] * s, piv[1] * s, top + 0.034 * s)))
        if cover_on:
            parts += [cover, pin]
        else:
            bpy.data.objects.remove(cover, do_unlink=True)
            bpy.data.objects.remove(pin, do_unlink=True)
    return {"subject": parts, "cut": cut, "keyhole": kh}


def icon_B(job, draft):
    E = escutcheon(1.0)
    subj = E["subject"]
    kh = E["keyhole"]
    door_loop = [(-3, -3), (3, -3), (3, 3), (-3, 3)]
    khd = G.offset_poly(kh, -0.006)
    door = G.solid2d("B_door", [door_loop, khd], 0.12, 0.002, bevel_res=1,
                     mat=G.mat_enamel("LG_Enamel", color="14302A"), z0=-0.12)
    # light room behind the door
    room = G.plane("B_room", 3, 3, (0, 0, -0.9), mat=G.mat_glow_disc("LG_Room", hot="F2FDFF", cool="0FA4E8",
                                                                     strength=9.0, radius=0.9))
    room.visible_shadow = False
    D = Vector((0.78, -0.50, 0.72)).normalized()
    kc = Vector((KH["cx"], KH["cy"] - 0.06, 0.0))
    spot = G.light("SPOT", "B_beam", kc - D * 1.6, kc, energy=7000, color="7FDFFF", size=0.015, spot_deg=9,
                   blend=0.5)
    # haze only along the beam (a cone), so the shaft reads without fogging the whole frame
    haze = G.lathe("B_haze", [(0.0, 0.10), (0.16, 0.10), (0.75, 2.4), (0.0, 2.4)], segments=48,
                   mat=G.mat_volume("LG_Haze", 0.9, -0.1, 3.0), smooth_deg=180)
    q = Vector((0, 0, 1)).rotation_difference(D)
    haze.data.transform(Matrix.Translation(kc) @ q.to_matrix().to_4x4())
    haze.visible_shadow = False
    leak = G.light("POINT", "B_leak", (0, KH["cy"] - 0.05, 0.12), energy=1.4, color="6FDFFF", size=0.04)
    key = G.light("AREA", "B_key", (-1.4, 1.6, 1.5), (0, 0, 0), energy=260, color="FFD3A0", size=0.8)
    rim = G.light("AREA", "B_rim", (1.5, 1.2, 0.5), (0, 0, 0.05), energy=60, color="FFE6C4", size=0.5)
    recv = subj + [door]
    for lt in (key, leak):
        G.light_only(lt, recv)
    G.light_only(rim, subj)
    studio_world(0.7)
    cam = G.camera((-0.85, -0.32, 2.5), (0, 0, 0.02), lens=90, dof_target=(0, 0, 0.04), fstop=4.0)
    bg = [door, room, haze]

    def after(cam):
        if job not in ("icon", "bg"):
            return []
        import random as _r
        rnd = _r.Random(5)
        import bmesh
        bm = bmesh.new()
        ax1 = D.orthogonal().normalized()
        ax2 = D.cross(ax1).normalized()
        for k in range(110 if not draft else 60):
            t = rnd.uniform(0.08, 1.7)
            rad = (0.06 + 0.10 * t) * math.sqrt(rnd.random()) * 1.3
            ph = rnd.uniform(0, G.TAU)
            p = kc + D * t + ax1 * (rad * math.cos(ph)) + ax2 * (rad * math.sin(ph))
            r = rnd.uniform(0.0016, 0.0042) * (1.0 if rnd.random() > 0.15 else 1.8)
            q = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
            bmesh.ops.translate(bm, vec=p, verts=q["verts"])
        me = bpy.data.meshes.new("B_motes")
        bm.to_mesh(me)
        bm.free()
        mo = G.link(bpy.data.objects.new("B_motes", me))
        G.set_mat(mo, G.mat_dust("LG_Dust", "FFFFFF", 0.0))
        mo.visible_shadow = False
        return [mo]
    return {"subject": subj, "background": bg, "cut": E["cut"], "cam": cam, "after": after, "frac_icon": 0.80,
            "post": {"vignette": 0.5, "bloom": 0.9, "threshold": 1.0}}


def keyhole_O(o_lo, o_hi, z_front, prefix="ko"):
    """Fill the counter of the letter O with a dark recessed escutcheon disc holding a glowing keyhole."""
    cx, cy = (o_lo.x + o_hi.x) / 2, (o_lo.y + o_hi.y) / 2
    w, h = (o_hi.x - o_lo.x), (o_hi.y - o_lo.y)
    rx, ry = w * 0.36, h * 0.40
    ell = [(cx + rx * math.cos(G.TAU * i / 96), cy + ry * math.sin(G.TAU * i / 96)) for i in range(96)]
    k = h * 0.5
    kh = G.keyhole(cx, cy + k * 0.20, k * 0.22, k * 0.085, k * 0.15, k * 0.58, n=40, corner=k * 0.02)
    disc = G.solid2d(prefix + "_disc", [ell, kh], z_front * 0.55, z_front * 0.12, bevel_res=2,
                     mat=G.mat_enamel_dial("LG_Dial", scale=0.5), z0=0.0)
    glow = G.solid2d(prefix + "_glow", [kh], z_front * 0.3, 0.0005, bevel_res=0,
                     mat=G.mat_glow_disc("LG_KeyGlow", hot="F0FDFF", cool="18B8F0", strength=7.0, radius=k * 0.35),
                     z0=0.0)
    lt = G.light("POINT", prefix + "_l", (cx, cy, z_front * 1.6), energy=0.5, color="6FDFFF", size=0.03)
    return [disc, glow], lt


def wordmark_B(draft):
    m = brass_set()
    letters = G.mat_brass("LG_Letters", hi="F0CC84", lo="A47E40", rough=0.2, rough_var=0.08, crevice=0.55, bump=0.1)
    t = G.text_obj("w_title", "MYSTERY ROOM", 1.0, extrude=0.07, bevel=0.013, spacing=1.08, mat=letters)
    isl = G.split_islands(t)
    # islands sorted by x: M Y S T E R Y R O O M -> index 8 = first O of ROOM
    o_isl = isl[8][3]
    xs = []
    ys = []
    for i in o_isl:
        for vi in t.data.polygons[i].vertices:
            v = t.data.vertices[vi].co
            xs.append(v.x)
            ys.append(v.y)
    o_lo, o_hi = Vector((min(xs), min(ys), 0)), Vector((max(xs), max(ys), 0))
    ko, lt = keyhole_O(o_lo, o_hi, 0.07 + 0.026)
    lo, hi = G.bounds([t])
    cx = (lo.x + hi.x) / 2
    sub = G.text_obj("w_sub", "THE FORGOTTEN INSTITUTE", 0.205, font=G.FONT_BOLD, extrude=0.02, bevel=0.0035,
                     spacing=1.42, align="CENTER", mat=letters)
    los, his = G.bounds([sub])
    sub.data.transform(Matrix.Translation((cx - (los.x + his.x) / 2, lo.y - 0.13 - his.y, 0)))
    los, his = G.bounds([sub])
    rules = rule_pair(m, lo, hi, los, his)
    return {"objs": [t, sub] + ko + rules, "letters": [t, sub]}


def rule_pair(m, lo, hi, los, his):
    rules = []
    ym = (los.y + his.y) / 2
    for sgn in (-1, 1):
        x0 = (los.x - 0.09) if sgn < 0 else (his.x + 0.09)
        x1 = (lo.x + 0.02) if sgn < 0 else (hi.x - 0.02)
        a, b = min(x0, x1), max(x0, x1)
        bar = G.solid2d("w_rule", [[(a, ym - 0.0075), (b, ym - 0.0075), (b, ym + 0.0075), (a, ym + 0.0075)]],
                        0.022, 0.006, bevel_res=2, mat=m.pol)
        dia = G.solid2d("w_dia", [[(x0 - sgn * 0.035, ym), (x0, ym - 0.022), (x0 + sgn * 0.035, ym),
                                   (x0, ym + 0.022)]], 0.03, 0.007, bevel_res=2, mat=m.pol)
        rules += [bar, dia]
    return rules


# ======================================================================= C — Lumen key
def lumen_key(s=1.0, prefix="ky", detail=True, glow=1.0, front_energy=1.0, back_energy=0.0):
    """Antique brass key along +X: bow = Institute ring (instrument profile, engraved scale) crossed by the
    meridian needle running along the key axis, glowing crystal in a bezel at the bow centre, turned collar,
    shank with a mid bead, warded bit hanging toward -Y, domed tip. Bow centre at the origin; the key lies
    flat with its lowest point at z=0. Length ~1.70*s (x from -0.44 to 1.256)."""
    m = brass_set()
    parts, cut = [], []
    zc = 0.045                                    # key mid-plane height (lying flat)
    sharp = [(0.300, zc - 0.035), (0.300, zc + 0.012), (0.290, zc + 0.034), (0.266, zc + 0.036),
             (0.258, zc + 0.022), (0.255, zc + 0.016), (0.232, zc + 0.016), (0.228, zc + 0.026),
             (0.218, zc + 0.030), (0.210, zc + 0.018), (0.210, zc - 0.035)]
    radii = [0, 0.010, 0.008, 0.008, 0.003, 0.0012, 0.0012, 0.003, 0.005, 0.006, 0]
    bow = G.lathe(prefix + "_bow", scaled(G.fillet(sharp, 0, 5, radii=radii), s), segments=192, mat=m.aged)
    G.add_mat_where(bow, m.satin, lambda c, n: n.z > 0.97 and 0.231 * s < math.hypot(c.x, c.y) < 0.256 * s)
    # close the underside (flat back)
    back = G.lathe(prefix + "_bowback", scaled([(0.210, zc - 0.035), (0.300, zc - 0.035)], s), segments=192,
                   mat=m.aged)
    for p in back.data.polygons:
        p.flip()
    parts += [bow, back]
    if detail:
        loops = []
        for k in range(48):
            a = math.radians(k * 7.5)
            if abs(math.sin(a)) < 0.12:
                continue
            ln, wd = (0.018, 0.0045) if k % 4 == 0 else (0.010, 0.0026)
            rc = 0.2525 - ln / 2
            loops.append(scaled(G.rect(rc * math.cos(a), rc * math.sin(a), ln, wd, a), s))
        parts.append(G.inlay(prefix + "_ticks", loops, (zc + 0.0162) * s, m.eng))
    # meridian needle along X: finial beyond the bow (-X) to the collar (+X)
    hw = 0.024
    boss = 0.118
    xj = math.sqrt(boss * boss - hw * hw)
    a0 = math.atan2(hw, xj)
    left = [(-0.44, 0.0), (-0.375, 0.036), (-0.330, 0.016), (-0.312, 0.025), (-0.28, hw)]
    arc_top = [(-boss * math.cos(a0 + (math.pi - 2 * a0) * k / 20), boss * math.sin(a0 + (math.pi - 2 * a0) * k / 20))
               for k in range(21)]
    arc_top = [(x, y) for (x, y) in arc_top]
    right = [(0.33, hw), (0.33, -hw)]
    arc_bot = [(x, -y) for (x, y) in reversed(arc_top)]
    pts = left + arc_top + right + arc_bot + [(x, -y) for (x, y) in reversed(left[1:])]
    rr = [0.006, 0.010, 0.008, 0.003, 0.0] + [0.015] + [0.0] * 19 + [0.015] + [0.0, 0.0] + [0.015] + [0.0] * 19 + \
         [0.015] + [0.0, 0.003, 0.008, 0.010]
    pts = G.fillet(pts, 0.0, 5, closed=True, radii=rr[:len(pts)])
    if G.poly_area(pts) < 0:
        pts = list(reversed(pts))
    needle = G.solid2d(prefix + "_needle", [scaled(pts, s)], 0.05 * s, 0.014 * s, bevel_res=4, mat=m.pol,
                       z0=(zc - 0.012) * s)
    parts.append(needle)
    # crystal bezel at the bow centre
    bz = G.fillet([(0.104, zc + 0.030), (0.104, zc + 0.066), (0.098, zc + 0.082), (0.084, zc + 0.085),
                   (0.078, zc + 0.077), (0.076, zc + 0.05)], 0, 5, radii=[0, 0.006, 0.006, 0.003, 0.003, 0])
    parts.append(G.lathe(prefix + "_bezel", scaled(bz, s), segments=128, mat=m.pol))
    import lib_mech as L
    kn = L.lathe2(prefix + "_knurl", [(0.100 * s, (zc + 0.040) * s), (0.1065 * s, (zc + 0.043) * s, "k"),
                                      (0.1065 * s, (zc + 0.063) * s, "k"), (0.100 * s, (zc + 0.066) * s)],
                  segments=96, knurl=0.003 * s, cap_bottom=False, cap_top=False)
    G.set_mat(kn, m.aged)
    G.shade(kn, 35.0)
    parts.append(kn)
    cut.append(kn)
    gem = rose_gem(prefix + "_gem", 0.077 * s, (zc + 0.068) * s, (zc + 0.076) * s, 0.040 * s, 0.03 * s, n=12,
                   mat=G.mat_crystal("LG_Crystal", tint="9EE9FF", glow="1EC0FF", glow_strength=9.0 * glow / max(s, 1e-3)))
    gem.visible_shadow = False
    bed = G.lathe(prefix + "_bed", [(0.0, (zc + 0.040) * s), (0.078 * s, (zc + 0.040) * s)], segments=48,
                  mat=G.mat_glow_disc("LG_GlowBed", strength=3.2 * glow, radius=0.077 * s))
    bed.visible_shadow = False
    parts += [gem, bed]
    lts = [G.light("POINT", prefix + "_lf", (0, 0, (zc + 0.17) * s), energy=front_energy * s * s, color="7FE4FF",
                   size=0.03 * s)]
    if back_energy > 0:
        lts.append(G.light("POINT", prefix + "_lb", (0, 0, (zc + 0.02) * s), energy=back_energy * s * s,
                           color="45CFFF", size=0.03 * s))
    # collar + shank + tip, turned along X
    X = (1, 0, 0)
    import lib_devices as D
    prof = [(0.0, 0.31), (0.046, 0.31), (0.058, 0.322), (0.058, 0.348), (0.046, 0.360), (0.041, 0.374),
            (0.053, 0.389), (0.053, 0.408), (0.041, 0.422), (0.038, 0.436), (0.038, 0.76), (0.046, 0.768),
            (0.048, 0.785), (0.046, 0.802), (0.038, 0.81), (0.038, 1.20), (0.032, 1.232), (0.017, 1.252), (0.0, 1.256)]
    sh = D.revolve(prefix + "_shank", [(r * s, x * s) for (r, x) in prof], direction=X, loc=(0, 0, zc * s),
                   segments=48, mat="M_Brass_Polished")
    G.set_mat(sh, m.pol)
    G.shade(sh, 40.0)
    parts.append(sh)
    # warded bit hanging toward -Y
    bit = [(0.950, 0.0), (0.950, -0.300), (1.002, -0.300), (1.002, -0.236), (1.040, -0.236), (1.040, -0.300),
           (1.112, -0.300), (1.112, -0.205), (1.140, -0.205), (1.140, -0.300), (1.205, -0.300), (1.205, 0.0)]
    slot = [(1.071, -0.040), (1.083, -0.040), (1.083, -0.170), (1.071, -0.170)]
    bitp = G.fillet(bit, 0.0, 3, closed=True, radii=[0.0, 0.008, 0.004, 0.003, 0.003, 0.004, 0.004, 0.003, 0.003,
                                                      0.004, 0.008, 0.0])
    if G.poly_area(bitp) < 0:
        bitp = list(reversed(bitp))
    b = G.solid2d(prefix + "_bit", [scaled(bitp, s), scaled(slot, s)], 0.06 * s, 0.010 * s, bevel_res=3,
                  mat=m.pol, z0=(zc - 0.030) * s)
    parts.append(b)
    return {"subject": parts, "cut": cut, "lights": lts}


def icon_C(job, draft):
    K = lumen_key(1.0, front_energy=1.0)
    subj = K["subject"]
    ang = math.radians(-38.0)
    mid = Vector((0.40, -0.02, 0.0))
    R = Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-mid)
    for o in subj:
        o.data.transform(R)
    for lt in K["lights"]:
        lt.location = R @ lt.location
    bowc = R @ Vector((0, 0, 0))

    def dent(x, y):
        # soft trough under the key (velvet gives under the weight)
        p = Vector((x, y, 0))
        loc = Matrix.Rotation(-ang, 4, "Z") @ p + mid
        dy = abs(loc.y) if -0.35 < loc.x < 1.3 else 1.0
        if -0.32 < loc.x < 0.32:
            dy = max(0.0, math.hypot(loc.x, loc.y) - 0.30)
        return -0.012 * math.exp(-(dy / 0.06) ** 2)
    vel = G.cloth("C_velvet", 5, 5, 380 if not draft else 240, 0.05, 3, G.mat_velvet("LG_Velvet", "0A1D1D", "6DB5AA",
                                                                                     crush=0.55),
                  dent=dent, freq=(4.0, 9.0))
    vel.location.z = -0.004
    key = G.light("SPOT", "C_key", (-1.5, 0.9, 1.9), (0.1, -0.1, 0), energy=900, color="FFD3A0", size=0.25,
                  spot_deg=34, blend=0.8)
    rim = G.light("AREA", "C_rim", (0.5, 2.3, 0.45), (0, 0, 0.05), energy=380, color="FFE7CC", size=0.8)
    soft = G.light("AREA", "C_soft", (-0.3, -0.6, 3.6), (0, 0, 0), energy=14, color="FFE9CC", size=2.4, size_y=0.5)
    glowpool = G.light("POINT", "C_pool", (bowc.x, bowc.y, 0.17), energy=8.0, color="35C8FF", size=0.05)
    studio_world(0.6)
    cam = G.camera((0.25, -1.75, 2.75), (0, 0, 0.03), lens=70, dof_target=(bowc.x, bowc.y, 0.06), fstop=3.2)
    return {"subject": subj, "background": [vel], "cut": K["cut"], "cam": cam, "frac_icon": 0.84,
            "post": {"vignette": 0.5, "bloom": 0.9, "threshold": 1.0}}


def wordmark_C(draft):
    m = brass_set()
    letters = G.mat_brass("LG_Letters", hi="F0CC84", lo="A47E40", rough=0.2, rough_var=0.08, crevice=0.55, bump=0.1)
    t = G.text_obj("w_title", "MYSTERY ROOM", 1.0, extrude=0.07, bevel=0.013, spacing=1.08, mat=letters)
    lo, hi = G.bounds([t])
    width = hi.x - lo.x
    ks = width * 0.78 / 1.70
    K = lumen_key(ks, front_energy=1.2)
    for o in K["subject"]:
        o.data.transform(Matrix.Translation((0, 0, -0.012 * ks)))
    klo, khi = G.bounds(K["subject"])
    kx = (lo.x + hi.x) / 2 - (klo.x + khi.x) / 2
    ky = lo.y - 0.10 - khi.y
    for o in K["subject"]:
        o.data.transform(Matrix.Translation((kx, ky, 0)))
    for lt in K["lights"]:
        lt.location += Vector((kx, ky, -0.012 * ks))
    klo, khi = G.bounds(K["subject"])
    cx = (lo.x + hi.x) / 2
    sub = G.text_obj("w_sub", "THE FORGOTTEN INSTITUTE", 0.205, font=G.FONT_BOLD, extrude=0.02, bevel=0.0035,
                     spacing=1.42, align="CENTER", mat=letters)
    los, his = G.bounds([sub])
    sub.data.transform(Matrix.Translation((cx - (los.x + his.x) / 2, klo.y - 0.09 - his.y, 0)))
    return {"objs": [t, sub] + K["subject"], "letters": [t, sub]}


# ======================================================================= runners
def light_wordmark(lo, hi, cool_at=None):
    w, h = hi.x - lo.x, hi.y - lo.y
    c = (lo + hi) / 2
    card = G.plane("W_card", w * 1.5, h * 1.25, (c.x, c.y, 6.0),
                   mat=G.mat_reflector("LG_Card", [(0.0, 0.32), (0.30, 0.10), (0.52, 0.42), (0.78, 1.0), (1.0, 0.85)],
                                       axis=1, lo=-0.5, hi=0.5, strength=5.0, color="FFE6BE"))
    card.visible_camera = False
    card.visible_shadow = False
    G.light("AREA", "W_key", (c.x - w * 0.35, hi.y + h * 3.0, 2.4), (c.x, c.y, 0), energy=900, color="FFD7A6",
            size=w * 0.6)
    G.light("AREA", "W_rim", (c.x + w * 0.3, lo.y - h * 3.0, 1.2), (c.x, c.y, 0), energy=260, color="7FD8FF",
            size=w * 0.5)
    G.world("0B0D0D", 0.6, top="2A2620", top_strength=0.3)


def run_wordmark(V, opt):
    G.reset()
    draft = opt["draft"]
    W = 1000 if draft else 2400
    builder = {"A": wordmark_A}.get(V) or globals()["wordmark_" + V]
    G.scene_setup(W, 400, 24 if draft else int(opt["samples"] or 80), transparent=True)
    R = builder(draft)
    lo, hi = G.bounds(R["objs"])
    margin = 0.06 * (hi.x - lo.x)
    ow, oh = (hi.x - lo.x) + 2 * margin, (hi.y - lo.y) + 2 * margin
    H = int(round(W * oh / ow / 2)) * 2
    sc = bpy.context.scene
    sc.render.resolution_y = H
    c = (lo + hi) / 2
    G.camera((c.x, c.y, 20.0), (c.x, c.y, 0.0), ortho=ow)
    light_wordmark(lo, hi)
    out = opt["out"]
    exr = os.path.join(out, "_wordmark.exr")
    t = time.time()
    G.render_exr(exr)
    print(f"[logo] wordmark render {time.time() - t:.1f}s")
    G.post(exr, os.path.join(out, "wordmark.png"), transparent=True, threshold=1.1, intensity=0.8,
           bloom=((0.002, 0.5), (0.008, 0.35), (0.025, 0.2)), alpha_gain=1.0)
    os.remove(exr)


ICON_BUILDERS = {"A": icon_A}


def run_icon(V, job, opt):
    G.reset()
    draft = opt["draft"]
    res = {"icon": 1024, "fg": 432, "bg": 432, "mono": 432}[job]
    if draft:
        res = {"icon": 512, "fg": 216, "bg": 216, "mono": 216}[job]
    samples = int(opt["samples"] or (96 if job == "icon" else 64))
    if draft:
        samples = 20
    G.scene_setup(res, res, samples, transparent=(job == "fg"))
    S = (ICON_BUILDERS.get(V) or globals()["icon_" + V])(job, draft)
    cam = S["cam"]
    frac = S.get("frac_icon", 0.76) if job == "icon" else S.get("frac_adaptive", 0.60)
    G.frame(cam, S["subject"], frac, offset=S.get("offset", (0.0, 0.0)))
    if "after" in S:
        S["background"] += S["after"](cam)
    out = opt["out"]
    if job == "mono":
        white = [o for o in S["subject"] if o not in S["cut"] and o.type == "MESH"]
        G.mask_render(os.path.join(out, "monochrome.png"), white, S["cut"], res)
        return
    if job == "fg":
        for o in S["background"]:
            o.hide_render = True
    if job == "bg":
        for o in S["subject"]:
            o.visible_camera = False
    exr = os.path.join(out, f"_{job}.exr")
    t = time.time()
    G.render_exr(exr)
    print(f"[logo] {job} render {time.time() - t:.1f}s")
    name = {"icon": "icon_1024.png", "fg": "adaptive_fg.png", "bg": "adaptive_bg.png"}[job]
    pp = S.get("post", {})
    if job == "icon":
        G.post(exr, os.path.join(out, name), vignette=pp.get("vignette", 0.45), threshold=pp.get("threshold", 1.0),
               intensity=pp.get("bloom", 0.9))
    elif job == "fg":
        G.post(exr, os.path.join(out, name), transparent=True, threshold=pp.get("threshold", 1.0),
               intensity=pp.get("bloom", 0.9) * 0.8)
    else:
        G.post(exr, os.path.join(out, name), vignette=pp.get("vignette", 0.45), intensity=0.0)
    os.remove(exr)


def main():
    opt = args()
    os.makedirs(opt["out"], exist_ok=True)
    V = opt["variant"]
    for job in [j.strip() for j in opt["jobs"].split(",") if j.strip()]:
        t = time.time()
        if job == "wordmark":
            run_wordmark(V, opt)
        else:
            run_icon(V, job, opt)
        print(f"[logo] {V}/{job} done in {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
