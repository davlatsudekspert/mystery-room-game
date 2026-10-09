"""projection_screen.glb — wall-mounted cinema screen for Records Archive B (north wall, x = -2.5).

A matte screen 2.40 x 1.60 in a black felt masking border, a moulded walnut proscenium frame with slim
pilasters, a walnut roller box (pelmet) on top with brass end caps and a pull cord, crimson velvet drapes
tied back at the sides, and the brass crystal socket on a bracket under the frame.

Origin = the back centre on the floor (local z = 0 is the wall face, front +Z).
Placement: (-2.5, 0, -3.5), yaw 0 (docs/models/ch2.md §1).

Parts:
  screen_surface    own object, 2.40 x 1.60, origin at its centre (0, 1.90, 0.07), faces +Z, UV 0..1
                    (u left -> right, v bottom -> top), M_Screen. The code puts its projection shader on it.
  IA_screen_socket  brass cup (dia 0.09) with three claws, origin at the mouth centre (0, 0.92, 0.12), mouth +Z.
  socket_mount      empty at the mouth (0, 0.92, 0.12), identity: a lumen_crystal stands on edge, disc +Z.
  socket_ring       own object, thin brass ring around the mouth (origin at the mouth); the code makes it glow.
  screen_frame      static: frame, masking, pilasters, roller box, drapes, bracket.

    blender -b --factory-startup -P tools/blender/models/projection_screen.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_arch as C  # noqa: E402
from lib_ch2_arch import G, GV, gbox  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "projection_screen"
SW, SH, SY, SZ = 2.40, 1.60, 1.90, 0.07           # screen size, centre height, plane
MX, MT, MB = 1.26, 2.76, 1.06                      # masking outer edge: x +-MX, top MT, bottom MB
FW = 0.078                                         # frame width
PX = MX + FW                                       # pilaster inner edge
DRAPE_IN = PX + 0.08                               # drape inner edge (outside the pilasters)
RB_X = DRAPE_IN + 0.25                             # roller box half width (covers the drapes)
SOCK = (0.0, 0.92, 0.12)
WAL = "M_Wood_Walnut"
BRASS = "M_Brass_Aged"


def frame_profile():
    """Proscenium moulding: s outward from the masking edge, u out of the wall (t = 0.092)."""
    pts = [(0.0, 0.0), (0.0, 0.074), (0.004, 0.082)]
    pts += A.arc(0.014, 0.082, 0.010, 180, 90, 3)[1:]
    pts += [(0.030, 0.090), (0.046, 0.088)]
    pts += A.arc(0.046, 0.076, 0.012, 90, 0, 3)[1:]
    pts += [(0.060, 0.068), (0.066, 0.060), (FW, 0.056), (FW, 0.0)]
    return pts


def ring_between(name, outer, inner, z, mat):
    bm = bmesh.new()
    vo = [bm.verts.new(G(x, y, z)) for x, y in outer]
    vi = [bm.verts.new(G(x, y, z)) for x, y in inner]
    n = len(vo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    o = A.obj_from_bm(name, bm, mat)
    for p in o.data.polygons:
        if p.normal.dot(GV((0, 0, 1))) < 0:
            p.flip()
    return o


def drape(name, side):
    """Velvet drape hanging from under the pelmet, gathered by a tie-back at y 1.25, flaring to the floor.
    side = -1 (left, seen from the front) or +1 (right)."""
    rings = []
    levels = [(2.84, 0.24, 0.022), (2.45, 0.21, 0.020), (1.95, 0.14, 0.015), (1.25, 0.05, 0.007),
              (0.95, 0.09, 0.012), (0.55, 0.15, 0.018), (0.22, 0.19, 0.021), (0.02, 0.20, 0.022)]
    folds = 4
    nu = folds * 4
    for (y, w, amp) in levels:
        # the drape hugs the frame side: inner edge at the frame outer edge, outer edge further out
        x_in = DRAPE_IN
        x_c = side * (x_in + w / 2)
        ring = []
        for i in range(nu + 1):
            t = i / nu
            x = x_c + side * (t - 0.5) * w
            z = 0.075 + amp * math.sin(t * folds * 2 * math.pi) + 0.012
            ring.append(G(x, y, z))
        # back side (flat, against the wall) to close the shell
        for t in (1.0, 0.0):
            x = x_c + side * (t - 0.5) * w
            ring.append(G(x, y, 0.035))
        rings.append(ring)
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    m = len(vr[0])
    for i in range(len(vr) - 1):
        for j in range(m):
            k = (j + 1) % m
            bm.faces.new((vr[i][j], vr[i][k], vr[i + 1][k], vr[i + 1][j]))
    bm.faces.new(vr[0])
    bm.faces.new(list(reversed(vr[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A.obj_from_bm(name, bm, "M_Velvet")
    return A.hint(o, 70)


def build():
    M.reset_scene()
    C.ensure_materials()
    parts = []
    x0, x1, y0, y1 = -SW / 2, SW / 2, SY - SH / 2, SY + SH / 2
    # backing board (hidden) and masking border (matte black felt), slightly proud of the screen plane
    parts.append(gbox("backing", (-MX - 0.04, MB - 0.04, 0.0), (MX + 0.04, MT + 0.04, 0.04), "M_Wood_Panel"))
    outer = [(-MX, MB), (MX, MB), (MX, MT), (-MX, MT)]
    inner = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    parts.append(ring_between("masking", outer, inner, SZ + 0.003, "M_Felt"))
    # masking edge returns (so the border has thickness at the screen edge) + panel behind the screen
    for nm, mn, mx in (("mask_l", (x0 - 0.004, y0, 0.04), (x0, y1, SZ + 0.003)), ("mask_r", (x1, y0, 0.04), (x1 + 0.004, y1, SZ + 0.003)),
                       ("mask_b", (x0, y0 - 0.004, 0.04), (x1, y0, SZ + 0.003)), ("mask_t", (x0, y1, 0.04), (x1, y1 + 0.004, SZ + 0.003))):
        parts.append(gbox(nm, mn, mx, "M_Felt"))
    parts.append(gbox("mask_fill", (-MX, MB, 0.04), (MX, MT, SZ - 0.004), "M_Felt"))
    # proscenium frame (moulded walnut), swept clockwise so the profile runs outward
    rect = [G(-MX, MB, 0.0), G(-MX, MT, 0.0), G(MX, MT, 0.0), G(MX, MB, 0.0)]
    parts.append(A.sweep("frame", frame_profile(), rect, up=GV((0, 0, 1)), closed=True, mat=WAL))
    # slim pilasters either side with plinth + capital
    px = PX
    for s in (-1, 1):
        xa, xb = (s * px, s * (px + 0.07)) if s > 0 else (s * (px + 0.07), s * px)
        parts += [gbox(f"pil_shaft{s}", (xa, 0.90, 0.0), (xb, 2.80, 0.055), WAL, bevel=0.006),
                  gbox(f"pil_plinth{s}", (xa - 0.008, 0.82, 0.0), (xb + 0.008, 0.90, 0.066), WAL, bevel=0.006),
                  gbox(f"pil_cap{s}", (xa - 0.01, 2.80, 0.0), (xb + 0.01, 2.84, 0.07), WAL, bevel=0.006)]
        for k in range(2):      # two flutes as shallow inset strips (darker felt-like shadow lines)
            fx = (xa + xb) / 2 + (k - 0.5) * 0.026
            parts.append(gbox(f"pil_flute{s}{k}", (fx - 0.004, 0.97, 0.055), (fx + 0.004, 2.73, 0.0565), "M_Lacquer_Black"))
    # roller box / pelmet on top: walnut box with a moulded cornice and brass end caps
    rb_x = RB_X
    parts.append(gbox("roller_box", (-rb_x, 2.84, 0.0), (rb_x, 3.04, 0.165), WAL, bevel=0.012, seg=2))
    cor = [(0.0, 0.0), (0.0, -0.03), (0.012, -0.03), (0.018, -0.022), (0.022, -0.010), (0.028, -0.004), (0.028, 0.0)]
    parts.append(A.sweep("roller_cornice", cor, [G(-rb_x, 3.07, 0.0), G(-rb_x, 3.07, 0.165), G(rb_x, 3.07, 0.165), G(rb_x, 3.07, 0.0)],
                         mat=WAL))
    parts.append(gbox("roller_top", (-rb_x - 0.028, 3.04, 0.0), (rb_x + 0.028, 3.07, 0.193), WAL, bevel=0.006))
    for s in (-1, 1):
        parts.append(C.gcyl(f"roller_cap{s}", 0.055, 0.012, (s * rb_x, 2.94, 0.085), axis="x" if s > 0 else "-x", verts=16,
                            mat=BRASS, bevel=0.003))
        parts.append(C.gcyl(f"roller_knob{s}", 0.018, 0.02, (s * (rb_x + 0.012), 2.94, 0.085), axis="x" if s > 0 else "-x",
                            verts=12, mat=BRASS, bevel=0.003))
    # a slot under the pelmet with the screen's rolled top edge (brass batten)
    parts.append(gbox("batten", (-MX, 2.835, 0.05), (MX, 2.845, 0.10), BRASS, bevel=0.002))
    # pull cord with a turned walnut pull on the right
    cx = MX + 0.03
    parts.append(C.gtube("cord", [(cx, 2.84, 0.12), (cx, 2.18, 0.125)], 0.0025, sides=5, mat="M_Fabric"))
    parts.append(C.glathe("cord_pull", [(0.0, 0.0), (0.006, 0.002), (0.011, 0.012), (0.012, 0.024), (0.008, 0.036), (0.004, 0.044),
                                        (0.0, 0.046)], (cx, 2.135, 0.125), axis="y", segments=10, mat=WAL))
    # tied-back velvet drapes + brass tie-back hooks and cords
    for s in (-1, 1):
        parts.append(drape(f"drape{s}", s))
        hx = s * (DRAPE_IN + 0.025)
        parts.append(C.gtube(f"tieback{s}", [(hx - 0.04, 1.25, 0.09), (hx, 1.235, 0.12), (hx + 0.04, 1.25, 0.09)], 0.006, sides=6,
                             mat="M_Brass_Polished", fillet=0.02))
        parts.append(C.gcyl(f"tie_tassel{s}", 0.012, 0.05, (hx, 1.235, 0.12), axis="-y", verts=8, mat="M_Brass_Polished",
                            r_top=0.006, bevel=0.0))
    # socket bracket: mounting plate under the frame + curved brass arm down to the cup back
    sx, sy, sz = SOCK
    parts.append(gbox("bracket_plate", (-0.04, MB - FW - 0.004, 0.012), (0.04, MB - FW, 0.07), BRASS, bevel=0.0015))
    for xx in (-0.028, 0.028):
        parts.append(C.screw("bracket_screw", 0.004, (xx, MB - FW - 0.004, 0.045), (0, -1, 0), BRASS, 0))
    arm = C.gtube("bracket_arm", [(0.0, MB - FW - 0.004, 0.040), (0.0, 0.958, 0.044), (0.0, 0.94, 0.056), (0.0, sy + 0.016, sz - 0.052)],
                  0.0065, sides=8, mat=BRASS, fillet=0.012)
    parts.append(arm)
    parts.append(C.hint_torus("bracket_collar", G(sx, sy, sz - 0.052), 0.0175, 0.004, major_seg=16, minor_seg=5, mat=BRASS))
    parts.append(M.sphere("bracket_ball", 0.0095, loc=G(0.0, MB - FW - 0.010, 0.040), segments=10, rings=6, mat=BRASS))
    A.presmooth(parts)
    body = M.join(parts, "screen_frame")
    # screen surface
    surf = C.gquad("screen_surface", (0.0, SY, SZ), (1, 0, 0), (0, 1, 0), SW, SH, "M_Screen")
    M.set_origin(surf, G(0.0, SY, SZ))
    # socket cup (lathe along +z, h = 0 at the mouth): back boss, fluted body, flat scaled lip, crystal seat
    prof = [(0.0, -0.058), (0.014, -0.058), (0.022, -0.050), (0.034, -0.046), (0.0435, -0.033),
            (0.0455, -0.027), (0.0455, -0.011), (0.0445, -0.008), (0.0476, -0.004),
            (0.0470, 0.0), (0.0385, 0.0), (0.0360, -0.004), (0.0355, -0.011), (0.0, -0.014)]
    cup = M.lathe("sock_cup", prof, segments=24, mat=BRASS)
    for v in cup.data.vertices:          # flutes on the body band
        if -0.0275 < v.co.z < -0.0105:
            a = math.atan2(v.co.y, v.co.x)
            f = 1.0 - 0.028 * (0.5 + 0.5 * math.cos(12 * a))
            v.co.x *= f
            v.co.y *= f
    cup.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))   # local +Z -> Blender -Y (= Godot +z)
    cup.data.transform(Matrix.Translation(G(*SOCK)))
    A.hint(cup, 55)
    # scale ticks on the flat lip (12, every 30 deg; double at 12 o'clock)
    bm = bmesh.new()
    for i in range(12):
        a = math.radians(90 + 30 * i)
        d = Vector((math.cos(a), math.sin(a)))
        nrm = Vector((-d.y, d.x))
        hw = 0.0009 if i else 0.0016
        r0, r1 = 0.0395, 0.0458
        vs = [bm.verts.new(G(sx + p.x, sy + p.y, sz + 0.0004)) for p in
              (d * r0 - nrm * hw, d * r1 - nrm * hw, d * r1 + nrm * hw, d * r0 + nrm * hw)]
        bm.faces.new(vs)
    ticks = A.obj_from_bm("sock_ticks", bm, "M_Lacquer_Black")
    for pl in ticks.data.polygons:
        if pl.normal.dot(GV((0, 0, 1))) < 0:
            pl.flip()
    claws = []
    for k, ang in enumerate((30, 150, 270)):       # clear of the crystal's grip tab at 12 o'clock
        a = math.radians(ang)
        d = Vector((math.cos(a), math.sin(a)))
        pts = []
        for j in range(5):
            t = j / 4
            r = 0.0425 - 0.0145 * t
            z = 0.0095 * math.sin(t * math.pi * 0.62)
            pts.append((sx + d.x * r, sy + d.y * r, sz + z))
        claws.append(C.gtube(f"sock_claw{k}", pts, 0.0034, sides=6, mat="M_Brass_Polished"))
        tip = M.sphere(f"sock_claw_tip{k}", 0.0037, loc=GV(pts[-1]), segments=6, rings=4, mat="M_Brass_Polished")
        claws.append(A.hint(tip, 80))
    A.presmooth([cup, ticks] + claws)
    sock = M.join([cup, ticks] + claws, "IA_screen_socket")
    M.set_origin(sock, G(*SOCK))
    ring = C.hint_torus("socket_ring", G(*SOCK), 0.0492, 0.0026, major_seg=28, minor_seg=5)
    M.set_origin(ring, G(*SOCK))
    mnt = C.mount("socket_mount", SOCK)
    A.finalize_uv([body, sock, ring])
    A.grain_uv(body)
    C.report(NAME)
    return body, surf, sock, ring, mnt


def main():
    args = M.main_guard()
    body, surf, sock, ring, mnt = build()
    path = C.export(NAME)
    C.verify_glb(path, required=["screen_surface", "IA_screen_socket", "socket_mount", "socket_ring", "screen_frame"],
                 identity=["screen_surface", "IA_screen_socket", "socket_mount", "socket_ring"], budget=4000,
                 expect={"screen_surface": (0.0, SY, SZ), "IA_screen_socket": SOCK, "socket_mount": SOCK, "socket_ring": SOCK},
                 show=["screen_surface", "IA_screen_socket", "socket_mount", "socket_ring"])
    if "--no-render" in args:
        return
    sel = C.args_shots(args)
    C.qa_begin()
    own = [body, surf, sock, ring, mnt]
    C.qa_place(own, (-2.5, 0.0, -3.5), 0.0)
    C.qa_import(C.model_glb("room_archive"))
    for p in C.PENDANTS:
        C.qa_import(C.model_glb("archive_pendant"), p, 0.0)
    if C.want("hero", sel):
        C.qa_room_lights()
        C.shoot(NAME, (-0.9, 1.55, -1.2), (-2.4, 1.7, -3.45), vfov=56)
        C.qa_clear()
    if C.want("view", sel):          # in-game "screen" view
        C.qa_room_lights()
        C.shoot(NAME + "_view", (-2.5, 1.7, -0.5), (-2.5, 1.9, -3.45), vfov=56)
        C.qa_clear()
    # crystal in the socket (proxy if lumen_crystal.glb is missing) + glowing ring, socket view
    crystal = C.model_glb("lumen_crystal")
    held = None
    if os.path.exists(crystal):
        held = C.qa_import(crystal, (-2.5, SOCK[1], -3.5 + SOCK[2]), 0.0)
    else:
        held = M.cylinder("qa_crystal", 0.028, 0.006, loc=G(-2.5, SOCK[1], -3.5 + SOCK[2]), rot=(math.pi / 2, 0, 0), verts=24,
                          mat="M_Crystal", bevel=0.001)
    if C.want("socket", sel):
        C.qa_room_lights()
        C.shoot(NAME + "_socket", (-2.5, 1.2, -2.65), (-2.5, 0.92, -3.38), vfov=40)
        C.qa_clear()
    if C.want("glow", sel):
        rm = M.material("QA_ring_glow", color="CFF6FF", emission="CFF6FF", emission_strength=6.0)
        ring.data.materials.clear()
        ring.data.materials.append(rm)
        C.qa_room_lights(energy=40.0)
        C.shoot(NAME + "_socket_glow", (-2.32, 1.05, -2.95), (-2.5, 0.92, -3.38), vfov=36)
        C.qa_clear()
    _ = held


main()
