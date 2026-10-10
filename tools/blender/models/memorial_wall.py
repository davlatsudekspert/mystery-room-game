"""memorial_wall.glb — the Gallery's memorial on the drum's north arc (F, H3): a polished granite band with 42
sockets, one empty (the secret), and a brass pictogram band of 41 standing figures and one apart. Contract:
docs/models/ch3.md §8 memorial_wall (+ §1.3 socket 42, §2 memorial / socket_42 / secret views, §10 pose_kneel);
results: docs/models/ch3_f.md.

ROOM-COORDINATE model (§0): origin = the world origin, built in place on the drum's north arc (phi from north, clockwise
seen from above; phi > 0 is east = the viewer's right from the Gallery).

  memorial_wall      (static, M_Stone + M_Brass_Aged) the granite band phi -30 .. 30, face r 3.92, y 0.95 .. 1.95, with brass
                     trims; above it the pictogram band y 1.95 .. 2.15 (face r 3.935): 41 relief figures at 1.225 deg and
                     one apart at phi 28.5; 41 brass cups (6-sided, Ø 0.054, floor at the row height) on small ledges
  memorial_crystals  ONE mesh, M_Crystal: 41 hexagonal crystals 0.03 x 0.07 standing in the cups (every socket but
                     row 2, column 13); the code turns emission on for all at once
  IA_socket_42       the empty cup + ledge at row 2, column 13: the contract point (1.78, 1.15, -3.49) is the wall point at
                     the seat height (the cup stands 0.027 in front of it); origin there
  socket_42_ring     brass ring on the granite round the socket (code glow), origin at its centre
  socket_42_mount    empty at the cup floor + 0.0569 (a nursery_crystal's origin; its bottom is 0.0569 below), yaw -27 so +Z
                     faces the Gallery centre
  echo_kneel_mount   empty (1.49, 0, -3.02), yaw 153: Leyla 1998's pose_kneel palm meets the socket

Sockets: rows 0..2 (top -> bottom) at y 1.75 / 1.45 / 1.15, columns 0..13 at phi = -27 + c * 54 / 13; the cup axis is on
r 3.893.

    blender -b --factory-startup -P tools/blender/models/memorial_wall.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "memorial_wall"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 6, 3
STONE, BRASS, CRYSTAL = E.STONE, E.BRASS, E.CRYSTAL

R_FACE, R_WALL = 3.92, 4.0
BAND_Y0, BAND_Y1 = 0.95, 1.95
PICT_Y0, PICT_Y1, R_PICT = 1.95, 2.15, 3.935
PHI0, PHI1 = -30.0, 30.0
ROW_Y = [1.75, 1.45, 1.15]
COLS = 14
CUP_R = 0.027
R_CUP = R_FACE - CUP_R                              # the cup axis radius
CUP_FLOOR_ABOVE = 0.0                               # the cup floor = the row height
N_FIG = 41
FIG_PHI0, FIG_PHI1, FIG_APART = -27.0, 22.0, 28.5
FIG_H = 0.15
SOCKET_42 = (3.92 * math.sin(math.radians(27.0)), 1.15, -3.92 * math.cos(math.radians(27.0)))
SOCKET_42_MOUNT_Y = 1.15 + 0.0569
KNEEL = (1.49, 0.0, -3.02)
KNEEL_YAW = 153.0
N_ARC = 15


def phi_c(c):
    return -27.0 + c * 54.0 / 13.0


# ====================================================================== curved solids
def arc_solid(name, prof, a0, a1, n, mat, drop=()):
    """A prism swept round the Y axis: closed profile [(r, y)] between angles a0..a1 (from north, clockwise), end caps
    included; the profile edges listed in `drop` (edge k joins point k and k + 1) are left open (they lie against
    another solid)."""
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        rings.append([bm.verts.new((r * math.sin(a), y, -r * math.cos(a))) for (r, y) in prof])
    m = len(prof)
    side = {}
    for i in range(n):
        for k in range(m):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % m], rings[i + 1][(k + 1) % m], rings[i + 1][k]))
            side.setdefault(k, []).append(f)
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[n])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for k in drop:
        bmesh.ops.delete(bm, geom=[f for f in side[k] if f.is_valid], context="FACES")
    return K.obj_from_bm(name, bm, mat)


def bands():
    st, br = [], []
    st.append(arc_solid("granite", [(R_FACE, BAND_Y0), (R_WALL, BAND_Y0), (R_WALL, BAND_Y1), (R_FACE, BAND_Y1)], PHI0, PHI1, N_ARC, STONE,
                        drop=(1,)))
    st.append(arc_solid("pict_back", [(R_PICT, PICT_Y0), (R_WALL, PICT_Y0), (R_WALL, PICT_Y1), (R_PICT, PICT_Y1)], PHI0, PHI1, N_ARC, STONE,
                        drop=(0, 1)))
    for (y0, y1, rf) in ((BAND_Y0, BAND_Y0 + 0.014, R_FACE), (BAND_Y1 - 0.014, BAND_Y1, R_FACE), (PICT_Y1 - 0.014, PICT_Y1, R_PICT)):
        br.append(arc_solid("trim", [(rf + 0.006, y0), (rf - 0.011, y0), (rf - 0.011, y1), (rf + 0.006, y1)], PHI0, PHI1, N_ARC, BRASS, drop=(3,)))
    return st, br


# ====================================================================== figures
def figure_loops():
    head = [(0.0132 * math.cos(math.radians(30 + 60 * i)), 0.0585 + 0.0132 * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    body = [(-0.024, 0.038), (0.024, 0.038), (0.020, -0.010), (0.014, -0.075), (0.003, -0.075), (0.0, -0.015), (-0.003, -0.075),
            (-0.014, -0.075), (-0.020, -0.010)]
    return A.ccw(head), A.ccw(body)


def figure(phi, y_c, depth=0.008):
    head, body = figure_loops()
    m = E.polar_frame(R_PICT, phi, y_c)
    out = []
    for lp in (head, body):
        o = K.plate("fig", [lp], depth, z0=0.0, mat=BRASS, bevel=0.0, drop_bottom=True)
        o.data.transform(m)
        out.append(o)
    return out


def figures():
    out = []
    yc = (PICT_Y0 + PICT_Y1) / 2
    for i in range(N_FIG):
        out += figure(FIG_PHI0 + (FIG_PHI1 - FIG_PHI0) * i / (N_FIG - 1), yc)
    out += figure(FIG_APART, yc)
    return out


# ====================================================================== sockets
CUP_PROFILE = [(0.021, -0.012), (CUP_R, 0.012), (0.019, 0.012), (0.019, 0.0), (0.0, 0.0)]


def cup(name, phi, y_s, seg=6):
    """A 6-sided brass cup whose floor is at y_s, on its axis at radius R_CUP, standing on a ledge."""
    a = math.radians(phi)
    c = Vector((R_CUP * math.sin(a), 0.0, -R_CUP * math.cos(a)))
    o = K.glathe(name, CUP_PROFILE, (c.x, y_s, c.z), (0, 1, 0), seg, BRASS, phase=a, smooth=40.0, cap_bottom=False)
    return o


def ledge(name, phi, y_s):
    o = K.gbox(name, (-0.033, -0.024, 0.0), (0.033, -0.012, 0.062), BRASS, 0.0)
    o.data.transform(E.polar_frame(R_FACE, phi, y_s))
    return o


def sockets():
    br, cr = [], []
    for row, y in enumerate(ROW_Y):
        for c in range(COLS):
            if row == 2 and c == COLS - 1:
                continue
            ph = phi_c(c)
            br += [cup("cup", ph, y), ledge("ledge", ph, y)]
            a = math.radians(ph)
            cx, cz = R_CUP * math.sin(a), -R_CUP * math.cos(a)
            cr.append(E.hex_crystal("mcrystal", 0.0150, 0.070, (cx, y, cz), axis=(0, 1, 0), tip=0.0135, flat_top=True, phase=a))
    return br, cr


def socket_42():
    ph = 27.0
    cp = cup("IA_cup", ph, 1.15)
    lg = ledge("IA_ledge", ph, 1.15)
    return K.part("IA_socket_42", [cp, lg], pivot=SOCKET_42)


def socket_ring():
    ph = math.radians(27.0)
    r = R_FACE - 0.0015
    c = (r * math.sin(ph), 1.185, -r * math.cos(ph))
    n = (-math.sin(ph), 0.0, math.cos(ph))                     # toward the Gallery centre
    o = D.ring("socket_42_ring", 0.050, 0.058, 0.0, 0.003, c, n, 20, BRASS)
    return K.part("socket_42_ring", [o], pivot=c)


# ====================================================================== build
def build():
    M.reset_scene()
    E.ensure_materials()
    st, br = bands()
    sbr, cr = sockets()
    body = K.part(NAME, st + br + figures() + sbr, pivot=(0.0, 0.0, 0.0))
    crystals = K.part("memorial_crystals", cr, pivot=(0.0, 0.0, 0.0))
    s42 = socket_42()
    ring = socket_ring()
    mount = K.empty("socket_42_mount", (3.893 * math.sin(math.radians(27.0)), SOCKET_42_MOUNT_Y, -3.893 * math.cos(math.radians(27.0))),
                    (0.0, -27.0, 0.0))
    kneel = K.empty("echo_kneel_mount", KNEEL, (0.0, KNEEL_YAW, 0.0), size=0.1)
    K.to_blender()
    E.finalize()
    return dict(body=body, crystals=crystals, s42=s42, ring=ring, mount=mount, kneel=kneel)


def verify(path):
    req = [NAME, "memorial_crystals", "IA_socket_42", "socket_42_ring", "socket_42_mount", "echo_kneel_mount"]
    mount_pos = (3.893 * math.sin(math.radians(27.0)), SOCKET_42_MOUNT_Y, -3.893 * math.cos(math.radians(27.0)))
    expect = {NAME: (0, 0, 0), "memorial_crystals": (0, 0, 0), "IA_socket_42": SOCKET_42, "socket_42_mount": mount_pos,
              "echo_kneel_mount": KNEEL}
    errs = E.verify(path, required=req, identity=[NAME, "memorial_crystals", "IA_socket_42", "socket_42_ring"], expect=expect,
                    parents={n: None for n in req}, rot_expect={"socket_42_mount": (0.0, -27.0, 0.0), "echo_kneel_mount": (0.0, KNEEL_YAW, 0.0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in (NAME, "memorial_crystals", "IA_socket_42", "socket_42_ring"):
        lo, hi = E.bounds([n])
        print(f"{E.TAG} {n:18s} bounds {tuple(round(c, 3) for c in lo)} .. {tuple(round(c, 3) for c in hi)}")
    # the 41 crystals: 41 x 24 tris
    o = bpy.data.objects["memorial_crystals"]
    print(f"{E.TAG} memorial_crystals tris {sum(len(p.vertices) - 2 for p in o.data.polygons)} (41 crystals)")
    return errs


# ====================================================================== QA
def qa(parts, args):
    E.qa_begin()
    E.gallery_room(doors=True, array=True)
    K.override(parts["crystals"], K.glow("qa_mem_crystal", "CFF6FF", 1.6))
    km = next(o for o in bpy.data.objects if o.name == "echo_kneel_mount")
    sm = next(o for o in bpy.data.objects if o.name == "socket_42_mount")
    # 1 the memorial view (§2)
    if E.want(args, "1"):
        V = E.view("memorial")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME, V[0], V[1], V[2])
    # 2 the socket_42 view (§2), a nursery_crystal in the cup, the ring lit
    if E.want(args, "2"):
        D.attach("nursery_crystal", sm, "qa_nc_")
        nb = next((o for o in bpy.data.objects if o.name.startswith("qa_nc_crystal_body")), None)
        if nb is not None:
            K.override(nb, K.glow("qa_crystal", "CFF6FF", 3.0))
        K.override(parts["ring"], K.glow("qa_ring", "CFF6FF", 4.0))
        V = E.view("socket_42")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_2", V[0], V[1], V[2])
    # 3 the secret view (§2): Leyla 1998 kneeling at the socket
    if E.want(args, "3"):
        E.echo_pose("echo_leyla_1998", "pose_kneel", km, "qa_el_")
        V = E.view("secret")
        E.gallery_lights(V[0], fill=8.0, array_awake=True)
        E.shoot(NAME + "_3", V[0], V[1], V[2])
    # 4 hero: the empty socket, close, a little from the left
    if E.want(args, "4"):
        cam = (1.45, 1.30, -3.05)
        E.gallery_lights(cam, fill=8.0, array_awake=True)
        E.shoot(NAME + "_4", cam, (1.78, 1.2, -3.49), 34)


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
