"""watch_room.glb — the watch room: a glazed steel cabin on the hall's east side with a collapsible grille door, a low ceiling and the mounts for the roll board, the lockers and the post station
(Chapter 4, group G). Contract: docs/models/ch4.md section 8 watch_room; results: docs/models/ch4_g.md.

LOCAL FRAME: origin = the floor at the cabin's centre, front = +Z; placed at (12.7, 0, 0) with yaw -90 (front faces -X, into the hall; local +X = world +Z, local +Z = world -X). Interior x +-3.5,
z -1.2 (back, the hall wall side) .. +1.2 (the glazed front, world x 11.5), floor top y 0.03, ceiling y 3.30, roof 3.40.
Nodes:
  watch_room        M_Steel_Dark + M_Glass + M_Chequer + M_Brass_Aged  the cabin: chequer floor, steel side and back walls with panel frames, the ceiling with two beams and a lamp cage, the front
                    (z 1.2): a riveted dado 0.03 .. 0.65, glass between mullions (0.65 .. 2.55) on both sides of the doorway, the doorway frame (x +-0.60, y up to 2.40, a glass transom), a header
                    fascia 2.55 .. 3.3 with the Institute's mark and a brass cornice, the roof with a vent
  IA_watch_gate     M_Brass_Aged  the grille door in the doorway: a collapsible brass lattice (4 x 3 cells) between a hinge post at the left and the free end, with a lock box on the hinge post
                    (Leyla's sign inlaid, a key slot on top). ORIGIN = the hinge post (-0.54, 0.03, 1.2); the lattice runs along +X to x = +0.54. Closed = identity; OPEN = scale local **X** to 0.15
                    about the origin (the lattice folds against the post; the lock box sits on the origin plane and squashes flat, as the booth's)
    watch_key_mount child of IA_watch_gate on the slot, rotated +90 deg about X: item -Z (the bow) -> +Y, item +Y (the face) -> +Z
  empties: board_mount (-0.85, 0.03, -1.2), lockers_mount (2.00, 0.03, -1.2), post_mount (-2.95, 0.03, -1.2) (all identity: the fixtures' fronts face +Z), echo_mount_clerk_post (-2.95, 0.03, -0.35)
  rot (0, 180, 0): the clerk stands in front of the post station and faces it, watch_lamp (0, 2.95, 0.1)

    blender -b --factory-startup -P tools/blender/models/watch_room.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
import lib_ch4_fgh as F  # noqa: E402
import lib_ch4_mark as MK  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL, CHEQ, GLASS  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "watch_room"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 8000, 9, 4
HX = 3.5                       # half width
ZB, ZF = -1.2, 1.2
FLOOR, CEIL, ROOF = 0.03, 3.30, 3.40
DADO = 0.65                    # top of the dado (a low one: the hall camera at y 1.7 sees the board's lower row over it)
DOOR_X = 0.60
DOOR_TOP = 2.40
HINGE = (-0.54, FLOOR, ZF)
SLOT_TOP = 1.45
LEFT_MULL = [-2.775, -2.05, -1.325]
RIGHT_MULL = [1.325, 2.05, 2.775]


def steel_parts():
    s = F.MB(STEEL)
    # side and back walls (inner faces at z = ZB, x = +-HX), with raised panel frames
    s.box((-HX - 0.10, 0.0, ZB - 0.10), (HX + 0.10, FLOOR, ZF + 0.05))                     # the cabin's floor frame / sill
    s.box((-HX - 0.10, FLOOR, ZB - 0.10), (HX, CEIL, ZB))                                  # back wall
    s.box((-HX - 0.10, FLOOR, ZB), (-HX, CEIL, ZF))                                        # west side (local -X)
    s.box((HX, FLOOR, ZB), (HX + 0.10, CEIL, ZF))
    for k in range(7):                                                                      # back wall panel frames
        xa = -HX + 0.08 + k * 0.99
        for (x0, y0, x1, y1) in ((xa, 0.50, xa + 0.90, 0.54), (xa, 2.90, xa + 0.90, 2.94), (xa, 0.54, xa + 0.04, 2.90), (xa + 0.86, 0.54, xa + 0.90, 2.90)):
            s.box((x0, y0, ZB), (x1, y1, ZB + 0.012))
    for sx in (-1, 1):
        for k in range(2):
            za = ZB + 0.10 + k * 1.0
            for (z0, y0, z1, y1) in ((za, 0.50, za + 0.90, 0.54), (za, 2.90, za + 0.90, 2.94), (za, 0.54, za + 0.04, 2.90), (za + 0.86, 0.54, za + 0.90, 2.90)):
                s.box((sx * HX - (0.012 if sx > 0 else 0.0), y0, z0), (sx * HX + (0.0 if sx > 0 else 0.012), y1, z1))
    # ceiling slab with two beams and a lamp cage
    s.box((-HX - 0.10, CEIL, ZB - 0.10), (HX + 0.10, ROOF, ZF + 0.12))
    for x in (-1.75, 1.75):
        s.box((x - 0.05, CEIL - 0.14, ZB), (x + 0.05, CEIL, ZF))
        s.box((x - 0.10, CEIL - 0.16, ZB), (x + 0.10, CEIL - 0.14, ZF))
    s.cyl((0.0, CEIL, 0.1), (0, -1, 0), 0.02, 0.12, segs=8)
    for k in range(8):
        a = math.radians(45.0 * k)
        s.bar((0.0 + 0.09 * math.cos(a), CEIL - 0.15, 0.1 + 0.09 * math.sin(a)), (0.0 + 0.14 * math.cos(a), CEIL - 0.36, 0.1 + 0.14 * math.sin(a)), 0.012, ref=(0, 1, 0))
    s.cyl((0.0, CEIL - 0.37, 0.1), (0, 1, 0), 0.15, 0.025, segs=14)
    # roof: upstand parapet and a vent box with a stack
    for (a, b) in (((-HX - 0.10, ROOF, ZF + 0.08), (HX + 0.10, ROOF + 0.12, ZF + 0.12)), ((-HX - 0.10, ROOF, ZB - 0.10), (HX + 0.10, ROOF + 0.12, ZB - 0.06)),
                   ((-HX - 0.10, ROOF, ZB - 0.06), (-HX - 0.06, ROOF + 0.12, ZF + 0.08)), ((HX + 0.06, ROOF, ZB - 0.06), (HX + 0.10, ROOF + 0.12, ZF + 0.08))):
        s.box(a, b)
    s.box((1.6, ROOF, -0.6), (2.6, ROOF + 0.30, 0.2))
    s.cyl((-1.8, ROOF, -0.4), (0, 1, 0), 0.10, 0.50, segs=12)
    s.cyl((-1.8, ROOF + 0.50, -0.4), (0, 1, 0), 0.15, 0.05, segs=12)
    # the front: dado, mullions, doorway posts, transom, header fascia
    s.box((-HX - 0.10, FLOOR, ZF - 0.06), (-DOOR_X, DADO, ZF))
    s.box((DOOR_X, FLOOR, ZF - 0.06), (HX + 0.10, DADO, ZF))
    for (xa, xb) in ((-HX + 0.10, -DOOR_X - 0.1), (DOOR_X + 0.1, HX - 0.10)):
        n = 3
        w = (xb - xa) / n
        for k in range(n):
            x0, x1 = xa + k * w + 0.07, xa + (k + 1) * w - 0.07
            for (a0, b0, a1, b1) in ((x0, 0.07, x1, 0.10), (x0, 0.50, x1, 0.53), (x0, 0.10, x0 + 0.03, 0.50), (x1 - 0.03, 0.10, x1, 0.50)):
                s.box((a0, FLOOR + b0 - 0.0, ZF), (a1, FLOOR + b1, ZF + 0.012))
    for i in range(40):
        x = -3.45 + 0.1725 * i
        if abs(x) > DOOR_X + 0.14:
            s.dome((x, DADO - 0.05, ZF), 0.014, 0.011, segs=5, normal=(0, 0, 1))
    for x in LEFT_MULL + RIGHT_MULL:
        s.box((x - 0.035, DADO, ZF - 0.05), (x + 0.035, 2.55, ZF + 0.012))
    for x in (-HX + 0.05, HX - 0.05):
        s.box((x - 0.07, DADO, ZF - 0.07), (x + 0.07, 2.55, ZF + 0.02))
    s.box((-HX - 0.10, 2.55, ZF - 0.07), (HX + 0.10, CEIL, ZF + 0.02))                   # the header fascia
    for k in range(32):
        s.dome((-3.4 + 0.2194 * k, 2.62, ZF + 0.02), 0.013, 0.010, segs=5, normal=(0, 0, 1))
    s.box((-HX, 2.45, ZF - 0.02), (-DOOR_X + 0.0, 2.55, ZF + 0.012))
    # doorway: two posts and a lintel, a threshold bar; the transom glass is separate
    for sx in (-1, 1):
        s.box((sx * DOOR_X - 0.06, FLOOR, ZF - 0.07), (sx * DOOR_X + 0.06, 2.55, ZF + 0.025))
    s.box((-DOOR_X, DOOR_TOP, ZF - 0.06), (DOOR_X, DOOR_TOP + 0.06, ZF + 0.02))
    s.box((-DOOR_X, 0.0, ZF - 0.10), (DOOR_X, FLOOR + 0.02, ZF + 0.10))
    # the gate's track on the threshold and under the lintel
    s.box((-0.52, FLOOR + 0.02, ZF - 0.012), (0.56, FLOOR + 0.03, ZF + 0.012))
    # a lamp bracket over the door
    s.bar((0.0, DOOR_TOP + 0.08, ZF + 0.02), (0.0, DOOR_TOP + 0.08, ZF + 0.22), 0.03, ref=(1, 0, 0))
    s.cyl((0.0, DOOR_TOP + 0.08, ZF + 0.26), (0, 1, 0), 0.10, 0.12, segs=12, r2=0.06)
    return s.obj("watch_steel")


def glass_parts():
    g = F.MB(GLASS)
    for (xa, xb, mulls) in ((-HX, -DOOR_X, LEFT_MULL), (DOOR_X, HX, RIGHT_MULL)):
        edges = [xa + 0.12] + mulls + [xb - 0.06]
        if xa < 0:
            edges = [-HX + 0.12] + mulls + [-DOOR_X - 0.06]
        else:
            edges = [DOOR_X + 0.06] + mulls + [HX - 0.12]
        for k in range(len(edges) - 1):
            a, b = edges[k] + (0.035 if k > 0 else 0.0), edges[k + 1] - (0.035 if k < len(edges) - 2 else 0.0)
            g.box((a, DADO + 0.02, ZF - 0.014), (b, 2.53, ZF - 0.004))
    g.box((-DOOR_X + 0.06, DOOR_TOP + 0.07, ZF - 0.014), (DOOR_X - 0.06, 2.53, ZF - 0.004))   # the transom
    return g.obj("watch_glass")


def cheq_parts():
    c = F.MB(CHEQ)
    c.box((-HX, 0.0, ZB), (HX, FLOOR, ZF))
    return c.obj("watch_floor")


def brass_parts():
    b = F.MB(BRASS)
    # cornice under the roof and over the fascia, a brass band at the dado's top, picture rail along the walls
    b.box((-HX - 0.12, CEIL - 0.04, ZF + 0.0), (HX + 0.12, CEIL + 0.03, ZF + 0.10))
    b.box((-HX - 0.12, ROOF - 0.04, ZF + 0.04), (HX + 0.12, ROOF + 0.01, ZF + 0.14))
    b.box((-HX - 0.10, DADO, ZF - 0.06), (-DOOR_X, DADO + 0.04, ZF + 0.03))
    b.box((DOOR_X, DADO, ZF - 0.06), (HX + 0.10, DADO + 0.04, ZF + 0.03))
    b.box((-HX, 2.42, ZB), (HX, 2.46, ZB + 0.025))                                           # picture rail on the back wall
    for sx in (-1, 1):
        b.box((sx * HX - (0.025 if sx > 0 else 0.0), 2.42, ZB), (sx * HX + (0.0 if sx > 0 else 0.025), 2.46, ZF))
    # corner posts' brass caps at the front, kick plates at the doorway posts
    for sx in (-1, 1):
        b.box((sx * DOOR_X - 0.07, 2.55, ZF - 0.075), (sx * DOOR_X + 0.07, 2.58, ZF + 0.03))
    return [b.obj("watch_brass")]


def fascia_mark():
    """The Institute's mark on the header, relief 6 mm, in brass."""
    return MK.mark_solids(0.42, 0.006, BRASS, loc=(0.0, 2.93), z0=ZF + 0.02, name="mark")


def gate_parts():
    """IA_watch_gate in room-local coordinates (origin of the node = the hinge post)."""
    x0 = HINGE[0]
    z0 = ZF
    br = F.MB(BRASS)
    # the hinge post (0.10 x 0.10, 2.25 high) with a base plate, a cap, the lock box (the origin plane is x0) and a slot on top
    br.box((x0 - 0.06, FLOOR, z0 - 0.06), (x0 + 0.06, FLOOR + 0.03, z0 + 0.06))
    br.box((x0 - 0.045, FLOOR + 0.03, z0 - 0.045), (x0 + 0.045, 1.12, z0 + 0.045))
    br.box((x0 - 0.07, 1.12, z0 - 0.08), (x0 + 0.07, SLOT_TOP - 0.03, z0 + 0.08))        # the lock box (centred on the origin plane x0)
    br.box((x0 - 0.08, SLOT_TOP - 0.03, z0 - 0.09), (x0 + 0.08, SLOT_TOP, z0 + 0.09))
    br.box((x0 - 0.03, SLOT_TOP, z0 - 0.045), (x0 - 0.0035, SLOT_TOP + 0.022, z0 + 0.045))
    br.box((x0 + 0.0035, SLOT_TOP, z0 - 0.045), (x0 + 0.03, SLOT_TOP + 0.022, z0 + 0.045))
    br.box((x0 - 0.0035, SLOT_TOP, z0 - 0.045), (x0 + 0.0035, SLOT_TOP + 0.007, z0 + 0.045))
    br.box((x0 - 0.045, 1.12, z0 - 0.045), (x0 + 0.045, 2.30, z0 + 0.045))
    br.box((x0 - 0.06, 2.30, z0 - 0.06), (x0 + 0.06, 2.34, z0 + 0.06))
    # the lattice: rails top and bottom, an end stile, 4 x 3 cells of crossed bars with hex rosettes
    y_lo, y_hi = 0.20, 2.20
    xs0, xs1 = x0 + 0.05, 0.54
    br.bar((xs0, y_lo, z0), (xs1, y_lo, z0), 0.036, ref=(0, 0, 1))
    br.bar((xs0, y_hi, z0), (xs1, y_hi, z0), 0.036, ref=(0, 0, 1))
    br.bar((xs1, y_lo, z0), (xs1, y_hi, z0), 0.036, ref=(0, 0, 1))
    ncol, nrow = 4, 3
    cw = (xs1 - xs0) / ncol
    ch = (y_hi - y_lo) / nrow
    for r in range(1, nrow):
        br.bar((xs0, y_lo + ch * r, z0), (xs1, y_lo + ch * r, z0), 0.022, ref=(0, 0, 1))
    for r in range(nrow):
        for c in range(ncol):
            xa, xb = xs0 + cw * c, xs0 + cw * (c + 1)
            ya, yb = y_lo + ch * r, y_lo + ch * (r + 1)
            br.bar((xa, ya, z0), (xb, yb, z0), 0.020, ref=(0, 0, 1))
            br.bar((xa, yb, z0), (xb, ya, z0), 0.020, ref=(0, 0, 1))
            br.boss(((xa + xb) / 2.0, (ya + yb) / 2.0, z0), (0, 0, 1), 0.020, 0.010, sides=6)
            br.boss(((xa + xb) / 2.0, (ya + yb) / 2.0, z0), (0, 0, -1), 0.020, 0.010, sides=6)
    obj = br.obj("gate_main")
    sign = C.S.inlay("gate_sign", "sign", 0.11, depth=0.004, mat=BRASS, bevel=0.0004, loc=(x0, 1.30, z0 + 0.08))
    return [obj, sign]


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("watch_room", [steel_parts(), glass_parts(), cheq_parts()] + brass_parts() + fascia_mark())
    gate = K.part("IA_watch_gate", gate_parts(), pivot=HINGE)
    K.empty("board_mount", (-0.85, FLOOR, ZB))
    K.empty("lockers_mount", (2.00, FLOOR, ZB))
    K.empty("post_mount", (-2.95, FLOOR, ZB))
    K.empty("echo_mount_clerk_post", (-2.95, FLOOR, -0.35), rot_deg=(0.0, 180.0, 0.0))
    K.empty("watch_lamp", (0.0, 2.95, 0.1))
    K.empty("watch_key_mount", (HINGE[0], SLOT_TOP + 0.085, ZF), rot_deg=(90.0, 0.0, 0.0))
    K.to_blender()
    K.parent(bpy.data.objects["watch_key_mount"], gate)
    C.finalize()
    return dict(body=body, gate=gate)


def verify(path):
    req = ["watch_room", "IA_watch_gate", "watch_key_mount", "board_mount", "lockers_mount", "post_mount", "echo_mount_clerk_post", "watch_lamp"]
    expect = {"watch_room": (0.0, 0.0, 0.0), "IA_watch_gate": HINGE, "watch_key_mount": (HINGE[0], SLOT_TOP + 0.085, ZF), "board_mount": (-0.85, FLOOR, ZB),
              "lockers_mount": (2.00, FLOOR, ZB), "post_mount": (-2.95, FLOOR, ZB), "echo_mount_clerk_post": (-2.95, FLOOR, -0.35), "watch_lamp": (0.0, 2.95, 0.1)}
    errs = C.verify(path, required=req, identity=["watch_room", "IA_watch_gate", "board_mount", "lockers_mount", "post_mount", "watch_lamp"], expect=expect,
                    parents={"watch_key_mount": "IA_watch_gate"}, rot_expect={"watch_key_mount": (90.0, 0.0, 0.0), "echo_mount_clerk_post": (0.0, 180.0, 0.0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ["watch_room", "IA_watch_gate"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    root = K.qa_place([parts["body"], parts["gate"]], (12.7, 0.0, 0.0), -90.0, name="qa_watch_root")
    for nm, mount in (("roll_board", (-0.85, FLOOR, ZB)), ("lockers4", (2.00, FLOOR, ZB)), ("post_station4", (-2.95, FLOOR, ZB))):
        h = C.qa_import(nm, (0, 0, 0), 0.0, prefix=f"qa_{nm}_")
        if h is not None:
            h.parent = root
            h.location = K.G(*mount)
    key = C.qa_import("key_leyla", (0, 0, 0), 0.0, prefix="qa_key_")
    M.refresh()
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
        K.light("watch_lamp", "POINT", (12.7 - 0.1, 2.95, 0.0), 220.0, "FFD9A0", radius=0.1)
    if C.want(args, "1"):          # the contract view
        cam, tgt, fov = C.view("watch")
        lit(cam, 40.0, 1.0)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the gate: Leyla's key in the lock
        mount = bpy.data.objects["watch_key_mount"]
        if key is not None:
            key.parent = mount
            key.matrix_parent_inverse = Matrix.Identity(4)
            key.location = (0.0, 0.0, 0.0)
            key.rotation_euler = (0.0, 0.0, 0.0)
        M.refresh()
        cam, tgt, fov = (8.9, 1.7, -1.6), (11.5, 1.3, -0.5), 40
        lit(cam, 40.0, 1.0)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # inside, from the doorway: the three fixtures (the gate open)
        parts["gate"].scale = (0.15, 1.0, 1.0)
        M.refresh()
        cam, tgt, fov = (11.4, 1.6, 0.4), (13.6, 1.0, 0.2), 70
        lit(cam, 60.0, 1.0)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    F.shell_report(label=NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    F.backface_check(label=NAME)
    qa(args, parts)


main()
