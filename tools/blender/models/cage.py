"""cage.glb — the round brass lattice cage round the Reliquary, with its four locked gates (Chapter 4, group D).
Contract: docs/models/ch4.md section 6 cage; results: docs/models/ch4_d.md.

ISLAND FRAME: placed at (0, 2.5, 0); origin = the island centre on the platform top. r 2.4, 3.0 high. Nodes:
  cage         M_Steel_Dark + M_Brass_Aged  the static cage: a steel base ring (y 0 .. 0.22), 20 steel posts every 15 deg (the four gate
               centres are open; the posts beside a gate are heavier door posts), brass lattice panels between the posts (two verticals,
               two rails at y 1.0 and 1.9, an X in each of three cells, rosettes at the crossings), brass lintels over the gates and
               a brass crown ring (y 2.80 .. 3.0) with finials
  IA_gate_1..4 M_Brass_Aged  the four gates at azimuth 180 (S, toward the catwalk) / 270 (W) / 0 (N) / 90 (E): a lattice leaf 1.24 wide,
               y 0.22 .. 2.55, with a lock plate (a brass numeral I..IV in relief over a keyhole) at the free edge.
               ORIGIN = the hinge axis at the leaf's left edge seen from outside (y = 0), identity at rest.
               OPEN = -95 deg about +Y (outward)
  gate_key_mount_1..4  empty, CHILD of IA_gate_n, at the keyhole (0.02 proud of the plate); the key stays there. Its frame: item -Z
               (the bow of a flat key) points OUTWARD along the gate's normal, item +Y up

    blender -b --factory-startup -P tools/blender/models/cage.py [-- --no-render] [--shots=1,2,...]
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
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, STEEL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "cage"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 12000, 6, 2
R = 2.4
H = 3.0
POST_DEG = 15.0
GATE_AZ = (180.0, 270.0, 0.0, 90.0)            # gate n is at GATE_AZ[n - 1]
HALF = 15.0                                    # a gate fills +-15 deg (door posts at +-15)
CHORD_Z = R * math.cos(math.radians(HALF))     # 2.318: the gate leaf plane (gate 1 frame, z = outward)
HALF_W = R * math.sin(math.radians(HALF))      # 0.621
LEAF_T = 0.04
Y0, Y1 = 0.22, 2.55                            # leaf bottom / top
LOCK_X, LOCK_Y = 0.40, 1.20                    # lock plate centre (gate 1 frame, x from the gate axis)
NUM_H = 0.15
KEY_DY = -0.12                                  # the keyhole centre below the lock plate centre
CELLS = (0.22, 1.0, 1.9, 2.8)                  # the horizontal lines of the lattice


def ang_gate(a):
    """Is azimuth a (deg) inside a gate opening?"""
    for g in GATE_AZ:
        d = abs((a - g + 180.0) % 360.0 - 180.0)
        if d < HALF - 1e-6:
            return True
    return False


def post_angles():
    out = []
    for k in range(24):
        a = POST_DEG * k
        if any(abs((a - g + 180.0) % 360.0 - 180.0) < 1e-6 for g in GATE_AZ):
            continue
        out.append(a)
    return out


def static_parts():
    steel, brass = bmesh.new(), bmesh.new()
    # --- posts (steel), door posts beside the gates are heavier; brass pyramid finials
    for a in post_angles():
        door = any(abs((a - g + 180.0) % 360.0 - HALF) < 1e-6 for g in GATE_AZ)
        t = 0.13 if door else 0.09
        X.bm_polar_box(steel, R - t / 2.0, R + t / 2.0, a, t, 0.18, 2.84, bottom=True)
        c = X.pol(R, a, 2.84)
        ap = X.pol(R, a, 2.84 + (0.16 if door else 0.11))
        base = []
        for (dr, dt) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            ar = math.radians(a)
            rad = Vector((math.sin(ar), 0.0, -math.cos(ar)))
            tan = Vector((math.cos(ar), 0.0, math.sin(ar)))
            p = Vector(c) + rad * (dr * t / 2.0 * 1.15) + tan * (dt * t / 2.0 * 1.15)
            base.append(brass.verts.new(p))
        apv = brass.verts.new(ap)
        for i in range(4):
            brass.faces.new((base[i], base[(i + 1) % 4], apv))
        brass.faces.new(list(reversed(base)))
    # --- lattice panels between consecutive posts (flat in the chord plane)
    for k in range(24):
        a0, a1 = POST_DEG * k, POST_DEG * (k + 1)
        mid = 0.5 * (a0 + a1)
        if ang_gate(mid):
            continue
        pl, pr = Vector(X.pol(R, a0)), Vector(X.pol(R, a1))
        ref = Vector(X.pol(1.0, mid))

        def at(t, y):
            p = pl + (pr - pl) * t
            return (p.x, y, p.z)
        # inner stile edge insets so bars end inside the posts
        for t in (1.0 / 3.0, 2.0 / 3.0):                                       # verticals
            X.bm_bar(brass, at(t, CELLS[0]), at(t, CELLS[-1]), 0.022, ref=tuple(ref))
        for y in (CELLS[1], CELLS[2]):                                         # rails
            X.bm_bar(brass, at(0.0, y), at(1.0, y), 0.034, ref=(0, 1, 0))
        for c in range(3):                                                     # X in each cell
            ya, yb = CELLS[c], CELLS[c + 1]
            X.bm_bar(brass, at(0.04, ya + 0.02), at(0.96, yb - 0.02), 0.018, ref=(0, 1, 0))
            X.bm_bar(brass, at(0.96, ya + 0.02), at(0.04, yb - 0.02), 0.018, ref=(0, 1, 0))
            # rosette where the X crosses
            ctr = at(0.5, 0.5 * (ya + yb))
            X.bm_boss(brass, (ctr[0] + ref.x * 0.012, ctr[1], ctr[2] + ref.z * 0.012), tuple(ref), 0.04, 0.014, sides=8)
        for y in (CELLS[1], CELLS[2]):                                         # rosettes where the verticals meet the rails
            for t in (1.0 / 3.0, 2.0 / 3.0):
                p = at(t, y)
                X.bm_boss(brass, (p[0] + ref.x * 0.016, p[1], p[2] + ref.z * 0.016), tuple(ref), 0.03, 0.012, sides=6)
    # --- over each gate: a lintel bar, a threshold plate and a fixed transom X (brass)
    for g in GATE_AZ:
        pl, pr = Vector(X.pol(R, g - HALF)), Vector(X.pol(R, g + HALF))
        ref = Vector(X.pol(1.0, g))

        def at(t, y):
            p = pl + (pr - pl) * t
            return (p.x, y, p.z)
        X.bm_bar(brass, at(0.0, Y1 + 0.03), at(1.0, Y1 + 0.03), 0.07, ref=(0, 1, 0))
        X.bm_bar(brass, at(0.0, 0.2), at(1.0, 0.2), 0.05, ref=(0, 1, 0))
        X.bm_bar(brass, at(0.05, Y1 + 0.06), at(0.95, CELLS[-1] - 0.02), 0.018, ref=(0, 1, 0))
        X.bm_bar(brass, at(0.95, Y1 + 0.06), at(0.05, CELLS[-1] - 0.02), 0.018, ref=(0, 1, 0))
    bmesh.ops.recalc_face_normals(brass, faces=list(brass.faces))
    bmesh.ops.recalc_face_normals(steel, faces=list(steel.faces))
    # --- base ring (steel) and crown ring (brass): revolved profiles
    bb = bmesh.new()
    X.bm_revolve(bb, [(R - 0.10, 0.0), (R + 0.16, 0.0), (R + 0.16, 0.10), (R + 0.10, 0.16), (R + 0.10, 0.22), (R - 0.10, 0.22),
                      (R - 0.10, 0.0)], 96, closed=True)
    X.fix_dir(bb, up=True)
    cb = bmesh.new()
    X.bm_revolve(cb, [(R - 0.12, 2.80), (R + 0.12, 2.80), (R + 0.12, 2.90), (R + 0.17, 2.92), (R + 0.17, 2.97), (R + 0.10, 3.0),
                      (R - 0.12, 3.0)], 96, closed=True)
    X.fix_dir(cb, up=True)
    objs = [K.obj_from_bm("c_steel", steel, STEEL), K.obj_from_bm("c_brass", brass, BRASS),
            K.obj_from_bm("c_base", bb, STEEL), K.obj_from_bm("c_crown", cb, BRASS)]
    # rivets along the base ring
    for i in range(48):
        a = math.radians(7.5 * i + 3.75)
        objs.append(K.rivet("rv", 0.016, ((R + 0.16) * math.sin(a), 0.05, -(R + 0.16) * math.cos(a)),
                            normal=(math.sin(a), 0.0, -math.cos(a)), mat=STEEL, segs=5))
    return objs


# ---------------------------------------------------------------------- the gates
def gate_parts(n):
    """Gate n built in the gate-1 frame (south, outward +Z) then turned onto its azimuth. Returns the object list."""
    bm = bmesh.new()
    zc = CHORD_Z
    zb, zf = zc - LEAF_T / 2.0, zc + LEAF_T / 2.0
    hx = HALF_W
    # stiles, rails
    X.bm_box(bm, (-hx, Y0, zb), (-hx + 0.065, Y1, zf), bottom=True)
    X.bm_box(bm, (hx - 0.065, Y0, zb), (hx, Y1, zf), bottom=True)
    X.bm_box(bm, (-hx, Y0, zb), (hx, Y0 + 0.07, zf), bottom=True)
    X.bm_box(bm, (-hx, Y1 - 0.07, zb), (hx, Y1, zf), bottom=True)
    X.bm_box(bm, (-hx, 1.38, zb), (hx, 1.42, zf), bottom=True)
    # verticals and X diagonals in the two cells
    for x in (-0.40, -0.22, -0.04, 0.14):
        X.bm_bar(bm, (x, Y0 + 0.07, zc), (x, Y1 - 0.07, zc), 0.022, ref=(1, 0, 0))
    for (ya, yb) in ((Y0 + 0.08, 1.37), (1.43, Y1 - 0.08)):
        X.bm_bar(bm, (-hx + 0.07, ya, zc), (hx - 0.07, yb, zc), 0.020, ref=(0, 1, 0))
        X.bm_bar(bm, (hx - 0.07, ya, zc), (-hx + 0.07, yb, zc), 0.020, ref=(0, 1, 0))
    # hinge barrels on the hinge edge
    for (y0, y1) in ((0.40, 0.62), (2.05, 2.27)):
        X.bm_bar(bm, (-hx - 0.012, y0, zc), (-hx - 0.012, y1, zc), 0.07, ref=(1, 0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    leaf = K.obj_from_bm("g_leaf", bm, BRASS)
    # lock plate with the keyhole punched through it, and the numeral in relief
    cx, cy, rr = 0.0, KEY_DY + 0.022, 0.017                           # keyhole: a round head over a tapered slot
    hole = [(-0.004, KEY_DY - 0.020), (0.004, KEY_DY - 0.020)]
    for i in range(15):
        t = math.radians(-40.0 + 260.0 * i / 14.0)
        hole.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    plate = K.plate("g_plate", [L.rounded_rect(0.30, 0.46, 0.04, n=4), hole], 0.03, z0=zf - 0.01, mat=BRASS, bevel=0.003,
                    loc=(LOCK_X, LOCK_Y, 0.0))
    num = C.N.roman_obj("g_num", n, NUM_H, depth=0.014, mat=BRASS)
    num.data.transform(Matrix.Translation((LOCK_X, LOCK_Y + 0.10, zf + 0.019)))
    out = [leaf, plate, num]
    yaw = -90.0 * (n - 1)
    for o in out:
        C.yaw_mesh(o, yaw)
    return out


def gate_hinge(n):
    return Matrix.Rotation(math.radians(-90.0 * (n - 1)), 3, "Y") @ Vector((-HALF_W, 0.0, CHORD_Z))


def key_mount(n):
    p = Vector((LOCK_X, LOCK_Y + KEY_DY + 0.022, CHORD_Z + 0.06))
    return Matrix.Rotation(math.radians(-90.0 * (n - 1)), 3, "Y") @ p


def build():
    M.reset_scene()
    C.ensure_materials()
    cage = C.merge("cage", static_parts())
    gates = []
    for n in (1, 2, 3, 4):
        gates.append(K.part(f"IA_gate_{n}", gate_parts(n), pivot=tuple(gate_hinge(n))))
        K.empty(f"gate_key_mount_{n}", tuple(key_mount(n)), rot_deg=(0.0, 180.0 - 90.0 * (n - 1), 0.0))
    K.to_blender()
    for n in (1, 2, 3, 4):
        K.parent(bpy.data.objects[f"gate_key_mount_{n}"], gates[n - 1])
    C.finalize()
    return dict(cage=cage, gates=gates)


def verify(path):
    req = ["cage"] + [f"IA_gate_{n}" for n in (1, 2, 3, 4)] + [f"gate_key_mount_{n}" for n in (1, 2, 3, 4)]
    ident = ["cage"] + [f"IA_gate_{n}" for n in (1, 2, 3, 4)]
    expect = {"cage": (0.0, 0.0, 0.0)}
    parents = {}
    rot = {}
    for n in (1, 2, 3, 4):
        expect[f"IA_gate_{n}"] = tuple(gate_hinge(n))
        expect[f"gate_key_mount_{n}"] = tuple(key_mount(n))
        parents[f"gate_key_mount_{n}"] = f"IA_gate_{n}"
        rot[f"gate_key_mount_{n}"] = (0.0, 180.0 - 90.0 * (n - 1), 0.0)
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents=parents, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ["cage", "IA_gate_1", "IA_gate_2"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_reliquary(skip=(NAME,), sprites=True)
    X.qa_place_island([parts["cage"]] + parts["gates"])
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
    if C.want(args, "1"):          # the island view
        cam, tgt, fov = C.view("island")
        lit(cam, 40.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # gate 1: the lock face, 1.8 m outside, eye 3.9 (glass case hidden)
        X.vis("qa_glass_tower_", False)
        cam, tgt, fov = (0.40, 3.9, CHORD_Z + 1.8), (LOCK_X, 2.5 + LOCK_Y, CHORD_Z), 46
        lit(cam, 60.0, 0.2)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # gate 2 open (-95 deg about +Y), seen from the north-west
        X.vis("qa_glass_tower_", True)
        K.pose_rot(parts["gates"][1], "y", -95.0)
        cam, tgt, fov = (-4.6, 3.6, -2.4), (-2.2, 3.4, 0.4), 56
        lit(cam, 60.0, 0.2)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)

def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
