"""MYSTERY ROOM — Chapter 3 light-echo figures (build group H, docs/models/ch3.md section 10).

Built on lib_echo and lib_ch2_echoes (never edited). Chapter 3 figures differ from the Chapter 2 ones:
  * a GLB holds several root-level POSE objects (or several figures); the code shows one at a time;
  * each pose is ONE closed mesh: body, hands and head are boolean-unioned (no echo_head part);
  * contact points and prop mounts are given in the figure's own Godot frame (+Z forward, -X = the figure's
    right, origin between the feet); empties (torch_tip, fork_mount, crystal_mount) are children of their pose.

Build convention (as lib_echo / lib_ch2_echoes): Blender, Z up, the figure faces +Y, +X = the figure's RIGHT.
`turn` (L.turn_to_godot_front) rotates the finished mesh 180 deg about Z, so the GLB faces Godot +Z.
Godot figure point (x, y, z) -> build point (-x, z, y)   (g2b_fig / L.godot_to_build).

Helpers
  load_model(name)             import another model script as a module (faces, hair functions)
  coat_rings(table, z_hip, ...) the Chapter 2 coat ring tables re-based on a hip height (kneeling, jackets)
  coat_details(...)            collar, lapels, patch pockets, breast pocket, buttons on a coat loft
  bent_leg(...), shoe_on(...)   trouser leg through hip -> knee -> ankle; shoe flat or toes-down (kneeling)
  arm(...)                     shoulder -> elbow (IK) -> wrist sleeve with deltoid and wrist stub
  hand(...)                    lib_ch2_echoes.hand2 with the chirality handled; grip_wrist() places a fist
  make_pose(...)               finish_body + hand shells + head, one closed shell, turned to Godot front
  add_empty(...)               a contact empty (Godot figure coordinates) parented to its pose
  verify(...)                  GLB check: node names, M_Echo only, tris per pose and per file, name hints
  QA: clay / ghost / context renders of one pose at a time into qa/blender/ch3/
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_echo as E  # noqa: E402
import lib_ch2_echoes as L  # noqa: E402
import mrlib  # noqa: E402
from lib_echo import vec  # noqa: E402
import lib_ch3_items as G  # noqa: E402  (GLB stats / name check)

QA_DIR = os.path.join(mrlib.ROOT, "qa", "blender", "ch3")
L.QA_DIR = QA_DIR
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def load_model(name: str):
    spec = importlib.util.spec_from_file_location(f"echo3_src_{name}", os.path.join(MODELS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def g2b(p) -> Vector:
    """Godot figure-frame point -> build space."""
    return Vector((-p[0], p[2], p[1]))


def b2g(p) -> tuple:
    return (round(-p[0], 4), round(p[2], 4), round(p[1], 4))


# ------------------------------------------------------------------ coats (Chapter 2 ring tables)
# (z, rx_right, rx_left, ry_front, ry_back, power, dx, dy); man: scientist b (hip 0.93, neck 1.50),
# woman: scientist a (hip 0.86, neck 1.41)
MAN_COAT = [
    (0.480, 0.214, 0.212, 0.156, 0.150, 2.2, 0.010, 0.016),
    (0.580, 0.208, 0.207, 0.150, 0.146, 2.2, 0.008, 0.012),
    (0.700, 0.200, 0.200, 0.142, 0.140, 2.1, 0.004, 0.006),
    (0.820, 0.193, 0.193, 0.135, 0.134, 2.1, 0.0, 0.0),
    (0.920, 0.186, 0.186, 0.130, 0.130, 2.05, 0.0, 0.0),
    (1.010, 0.176, 0.176, 0.124, 0.118, 2.0, 0.0, 0.0),
    (1.090, 0.176, 0.176, 0.126, 0.114, 2.0, 0.0, 0.0),
    (1.170, 0.182, 0.182, 0.126, 0.114, 2.0, 0.0, 0.0),
    (1.250, 0.190, 0.190, 0.124, 0.118, 2.0, 0.0, 0.0),
    (1.330, 0.196, 0.196, 0.116, 0.120, 2.0, 0.0, 0.0),
    (1.390, 0.194, 0.194, 0.104, 0.112, 2.0, 0.0, 0.0),
    (1.432, 0.180, 0.180, 0.092, 0.098, 2.05, 0.0, 0.0),
    (1.466, 0.136, 0.136, 0.076, 0.082, 2.0, 0.0, 0.0),
    (1.498, 0.072, 0.072, 0.058, 0.060, 2.0, 0.0, 0.0),
]
MAN_HIP, MAN_NECK = 0.93, 1.50
WOMAN_COAT = [
    (0.430, 0.212, 0.210, 0.150, 0.156, 2.25, 0.008, 0.020),
    (0.520, 0.206, 0.203, 0.146, 0.152, 2.2, 0.010, 0.016),
    (0.640, 0.200, 0.196, 0.138, 0.145, 2.15, 0.010, 0.010),
    (0.760, 0.196, 0.190, 0.128, 0.139, 2.1, 0.008, 0.004),
    (0.850, 0.192, 0.184, 0.121, 0.133, 2.1, 0.004, 0.0),
    (0.930, 0.176, 0.172, 0.110, 0.118, 2.05, 0.0, 0.0),
    (0.995, 0.153, 0.154, 0.099, 0.098, 2.0, 0.0, 0.0),
    (1.065, 0.153, 0.154, 0.106, 0.092, 2.0, 0.0, 0.0),
    (1.135, 0.161, 0.162, 0.119, 0.090, 2.0, 0.0, 0.0),
    (1.205, 0.168, 0.168, 0.124, 0.092, 2.0, 0.0, 0.0),
    (1.258, 0.173, 0.172, 0.113, 0.096, 2.0, 0.0, 0.0),
    (1.300, 0.176, 0.175, 0.099, 0.094, 2.0, 0.0, 0.0),
    (1.340, 0.173, 0.173, 0.088, 0.088, 2.05, 0.0, 0.0),
    (1.370, 0.157, 0.157, 0.078, 0.080, 2.0, 0.0, 0.0),
    (1.396, 0.118, 0.118, 0.066, 0.070, 2.0, 0.0, 0.0),
    (1.418, 0.063, 0.063, 0.051, 0.054, 2.0, 0.0, 0.0),
]
WOMAN_HIP, WOMAN_NECK = 0.86, 1.41


def coat_rings(table, std_hip, std_neck, z_hip, z_neck, hem_dz=None, grow=0.0, hem_flare=0.0, legs_dy=None):
    """Re-base a ring table on a pose's hip / neck heights: rings below the hip shift with the hip, rings above
    it are stretched to the pose's neck (a leaning spine is shorter in z). hem_dz (< 0) cuts the coat at
    std_hip + hem_dz (a jacket). grow adds to every radius (outerwear bulk); hem_flare widens the lowest rings.
    legs_dy: an extra forward shift of the skirt rings (dy) for seated / crouched poses."""
    out = []
    lo = table[0][0]
    for r in table:
        z = r[0]
        if hem_dz is not None and z < std_hip + hem_dz - 1e-6:
            continue
        if z <= std_hip:
            nz = z_hip + (z - std_hip)
        else:
            nz = z_hip + (z - std_hip) * (z_neck - z_hip) / (std_neck - std_hip)
        fl = hem_flare * max(0.0, (std_hip - z) / max(std_hip - lo, 1e-6))
        g = grow if z < std_neck - 0.05 else grow * 0.3
        rr = list(r)
        rr[0] = nz
        for k in (1, 2, 3, 4):
            rr[k] = r[k] + g + fl
        while len(rr) < 8:
            rr.append(0.0)
        if legs_dy is not None and z < std_hip:
            rr[7] = rr[7] + legs_dy * (std_hip - z) / max(std_hip - lo, 1e-6)
        out.append(tuple(rr))
    return out


def coat_details(key, sp, tree, female=False, collar_r=0.066, collar_z=None, lapel=True, pockets=None,
                 breast=None, buttons=(), button_x=0.004, collar_width=None, stand_collar=False):
    """Collar, lapels, patch pockets, breast pocket and buttons hugging a coat loft (`tree` = its BVH)."""
    def chest(x, y, z):
        return sp.point(z, (x, y, 0))
    zc = collar_z if collar_z is not None else sp.z_neck - 0.03
    parts = []
    if stand_collar:
        c = sp.point(zc, (0, 0.0, 0))
        parts.append(E.loft(f"{key}_standcollar", [c + Vector((0, 0, -0.012)), c + Vector((0, 0, 0.045))],
                            [(collar_r + 0.012, collar_r + 0.004, collar_r + 0.016),
                             (collar_r + 0.002, collar_r - 0.004, collar_r + 0.008)],
                            side=tuple(sp.right(zc)), seg=24, sub=2, cap0=0.2, cap1=0.2))
    else:
        col = E.collar_band(f"{key}_collar", (0, 0, 0), collar_r, list(range(50, 315, 15)), height=0.020,
                            width=collar_width or (0.036 if female else 0.040), back_lift=0.012)
        E.transform_obj(col, Matrix.Translation(sp.point(zc, (0, 0, 0))) @ E.rot_z(sp.yaw_chest).to_4x4()
                        @ E.rot_x(-10).to_4x4())
        parts.append(col)
    if lapel:
        zt = zc + 0.004
        pts = [(0.050, zt), (0.068, zt - 0.053), (0.064, zt - 0.113), (0.040, zt - 0.183), (0.004, zt - 0.248)]
        w = [0.044, 0.060, 0.054, 0.032, 0.004]
        if not female:
            pts = [(x * 1.12, z) for (x, z) in pts]
            w = [v * 1.08 for v in w]
        for sx in (1, -1):
            parts.append(E.surface_slab(f"{key}_lapel{sx}", tree, [chest(sx * x, 0.14, z) for (x, z) in pts], w,
                                        thick=0.0042, side_sign=sx))
    if pockets is not None:
        px, pz0, pz1, pw = pockets
        for sx in (1, -1):
            parts.append(E.surface_slab(f"{key}_pocket{sx}", tree, [chest(sx * px, 0.16, pz0), chest(sx * px, 0.17, pz1)],
                                        [pw, pw + 0.01], thick=0.0042))
    if breast is not None:
        bx, bz0, bz1 = breast
        parts.append(E.surface_slab(f"{key}_breast", tree, [chest(bx, 0.15, bz0), chest(bx, 0.15, bz1)],
                                    [0.094, 0.098], thick=0.004))
    for i, z in enumerate(buttons):
        p = E.hug(tree, [chest(button_x, 0.16, z)], 0.0036)[0]
        parts.append(E.ellipsoid(f"{key}_button{i}", p, (0.009, 0.009, 0.009), seg=10, rings=6))
    return parts


# ------------------------------------------------------------------ legs and feet
def bent_leg(prefix, hip, knee, ankle, r_thigh=0.075, r_knee=0.060, r_shin=0.058, r_hem=0.060, hem_z=None,
             knee_cap=True, side=(1, 0, 0)):
    """A trouser leg through hip -> knee -> ankle (smooth bend), ending at a hem just above the shoe."""
    hp, kn, an = vec(hip), vec(knee), vec(ankle)
    d1 = (kn - hp)
    d2 = (an - kn)
    hem = an + d2.normalized() * -0.012 if hem_z is None else Vector((an.x, an.y, hem_z))
    pts = [hp - d1.normalized() * 0.03, hp + d1 * 0.45, kn - d1.normalized() * 0.045, kn + d2.normalized() * 0.05,
           kn + d2 * 0.55, hem]
    rads = [(r_thigh, r_thigh * 0.95), (r_thigh * 0.92, r_thigh * 0.9), (r_knee * 1.05, r_knee),
            (r_knee, r_knee * 0.98), (r_shin, r_shin * 0.95), (r_hem, r_hem * 0.96)]
    parts = [E.loft(prefix, pts, rads, side=side, seg=20, sub=3, cap0=0.4, cap1=0.25)]
    if knee_cap:
        nrm = (d1.normalized() - d2.normalized())
        nrm = nrm.normalized() if nrm.length > 1e-3 else Vector((0, 1, 0))
        parts.append(E.ellipsoid(prefix + "_knee", kn + nrm * 0.010, (r_knee * 0.95, r_knee * 0.95, r_knee * 0.95),
                                 seg=16, rings=10))
    return parts


def shoe_on(prefix, ankle_xy, yaw_deg, heel=0.012, scale=1.07, toe=1.0, toes_down=0.0, boot=False):
    """A shoe whose ankle is above (ankle_xy) on the floor. toes_down > 0 (deg) lifts the heel about the toe
    tip (a kneeling foot on its toes). Returns (parts, ankle point) in build space."""
    parts = L.shoe(prefix, (0.0, 0.0), 0.0, heel=heel, scale=scale, toe=toe)
    if boot:
        parts.append(E.limb(prefix + "_shaft", Vector((0, -0.005, 0.03)), Vector((0, -0.01, 0.16)),
                            [(0.052, 0.050), (0.050, 0.048), (0.048, 0.046)], seg=18, side=(1, 0, 0), cap1=0.3))
    ankle = Vector((0.0, 0.0, 0.085 * scale))
    m = Matrix.Identity(4)
    if toes_down > 0:
        tip = Vector((0.0, 0.160 * scale, 0.0))
        m = Matrix.Translation(tip) @ Matrix.Rotation(-math.radians(toes_down), 4, "X") @ Matrix.Translation(-tip)
    m = Matrix.Translation((ankle_xy[0], ankle_xy[1], 0.0)) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z") @ m
    for p in parts:
        E.transform_obj(p, m)
    # a turned (toes-down) shoe can dip under the floor at the toe: lift it back onto the floor
    low = min(v.co.z for p in parts for v in p.data.vertices)
    if low < 0.0:
        for p in parts:
            E.transform_obj(p, Matrix.Translation((0.0, 0.0, -low)))
        m = Matrix.Translation((0.0, 0.0, -low)) @ m
    return parts, m @ ankle


# ------------------------------------------------------------------ arms and hands
def arm(prefix, sh, wr, l1, l2, pole, r=(0.056, 0.053, 0.050, 0.047, 0.049, (0.027, 0.020), (0.048, 0.053, 0.048)),
        sp=None, side=1, cuff_gap=0.026):
    """Coat sleeve from the shoulder over an IK elbow to the cuff, plus a wrist stub. Returns (parts, elbow)."""
    el = E.ik2(sh, wr, l1, l2, pole)
    off = (sp.right(sh.z) * (0.006 * side) if sp is not None else Vector()) + Vector((0, 0, -0.010))
    sl, _cuff = L.sleeve(prefix, sh, el, wr, r_sh=r[0], r_up=r[1], r_el=r[2], r_fore=r[3], r_cuff=r[4],
                         cuff_len=0.026, wrist_r=r[5], deltoid=r[6], cuff_gap=cuff_gap, start_back=0.006,
                         deltoid_off=off)
    parts = []
    for p in sl:
        if p.name.endswith("_wrist"):
            bpy.data.objects.remove(p, do_unlink=True)
        else:
            parts.append(p)
    fdir = (vec(wr) - el).normalized()
    parts.append(E.limb(prefix + "_wstub", vec(wr) - fdir * 0.05, vec(wr) + fdir * 0.004, [r[5], (r[5][0] * 0.97, r[5][1] * 0.97)],
                        seg=14, side=(0, 0, 1)))
    return parts, el


def hand(prefix, wrist, F, N, right, curls, spread=None, thumb=None, scale=1.0, width=0.078, finger_r=0.0084):
    F = vec(F).normalized()
    N = L.ortho(N, F)
    T = L.ortho(F.cross(N) * (1.0 if right else -1.0), F)
    return L.hand2(prefix, vec(wrist), F, N, T, curls=curls, spread=spread, thumb=thumb, scale=scale, width=width,
                   finger_r=finger_r)


def grip_wrist(centre, F, N, scale=1.0, along=0.083, out=0.026):
    """Wrist position for a fist whose grip centre (the object held in the curled fingers) is `centre`."""
    F = vec(F).normalized()
    N = L.ortho(N, F)
    return vec(centre) - F * along * scale - N * out * scale


def flat_hand(prefix, palm_pt, F, N, right, scale=1.0, curl=1.0, spread=None, width=0.078, finger_r=0.0084):
    """A hand lying flat with its palm centre on a surface point `palm_pt`; N = out of the palm (into the
    surface), F = toward the fingertips. Returns (parts, wrist, info)."""
    F = vec(F).normalized()
    N = L.ortho(N, F)
    wr = vec(palm_pt) - F * 0.050 * scale - N * 0.017 * scale
    c = [(8 * curl, 12 * curl, 6 * curl), (8 * curl, 14 * curl, 6 * curl), (10 * curl, 16 * curl, 8 * curl),
         (12 * curl, 18 * curl, 8 * curl)]
    objs, info = hand(prefix, wr, F, N, right, c, spread=spread or [6, 1, -4, -10], scale=scale, width=width,
                      finger_r=finger_r)
    return objs, wr, info


def relaxed_hand(prefix, el, wr, right, scale=1.0, pron=8.0, bend=(0.0, 0.10, -0.05), curl=1.0):
    F = (vec(wr) - vec(el)).normalized()
    F = (F + Vector(bend)).normalized()
    N, T = L.arm_hand_frame(F, pron, right=right)
    c = [(14 * curl, 22 * curl, 12 * curl), (20 * curl, 28 * curl, 14 * curl), (24 * curl, 32 * curl, 16 * curl),
         (28 * curl, 36 * curl, 18 * curl)]
    return L.hand2(prefix, vec(wr), F, N, T, curls=c, spread=[3, 0, -2, -5], scale=scale, width=0.078, finger_r=0.0084)


# ------------------------------------------------------------------ assembly
def make_pose(name, parts, hands, head, tris, voxel=0.0036, folds=None, flutes=None, hand_sigma=0.04,
              late=None):
    """parts: closed shells of the body (coat, legs, sleeves, props); hands: [(parts, centre)];
    head: kwargs for lib_ch2_echoes.build_head (P, pivot, nd, yaw, pitch, roll, hair_fn, extras_fn, kernels,
    neck_r); tris: dict(body, hand, head). late: closed shells unioned after the decimation (thin props that
    the voxel grid would lose). Returns ONE closed shell in build space named `name`."""
    body = L.finish_body(parts, voxel=voxel, tris=tris["body"], hand_centres=[c for (_p, c) in hands],
                         hand_sigma=hand_sigma, folds_fn=folds, post_fn=flutes, name=name + "_body")
    shells = [L.hand_shell(hp, f"{name}_hand{i}", tris["hand"]) for i, (hp, _c) in enumerate(hands)]
    hd = dict(head)
    h = L.build_head(hd.pop("P"), hd.pop("pivot"), hd.pop("nd"), hd.pop("yaw"), hd.pop("pitch"), hd.pop("roll"),
                     hd.pop("hair_fn"), tris["head"], **hd)
    others = shells + [h] + (late or [])
    obj = L.bool_union(body, others, name)
    dropped = L.drop_small_islands(obj, min_verts=60)      # boolean crumbs (a few mm), never real parts
    if dropped:
        E.clean_mesh(obj)
        print(f"[echo3] {name}: dropped {dropped} boolean crumb island(s)")
    rep = E.mesh_report(obj)
    print(f"[echo3] {name}: {rep}")
    if rep["shells"] > 1:
        islands(obj)
    return obj


def islands(obj) -> None:
    """Print every connected island of a mesh (vertex count, bbox centre) to find a part that did not join."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    seen = set()
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            isl.append(x.co.copy())
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        lo = Vector((min(c.x for c in isl), min(c.y for c in isl), min(c.z for c in isl)))
        hi = Vector((max(c.x for c in isl), max(c.y for c in isl), max(c.z for c in isl)))
        print(f"[echo3]   island: {len(isl)} verts, bbox {tuple(round(c, 3) for c in lo)} .. {tuple(round(c, 3) for c in hi)}")
    bm.free()


def turn(obj) -> None:
    """Build space (faces +Y) -> export space (faces Godot +Z); M_Echo; smooth."""
    L.turn_to_godot_front([(obj, None)])
    E.finish_echo(obj)


def add_empty(name, pose_obj, godot_pt):
    """Contact empty at a Godot figure-frame point (identity rotation), child of its pose."""
    p = Vector((godot_pt[0], -godot_pt[2], godot_pt[1]))     # Godot -> Blender (export orientation)
    e = mrlib.empty(name, loc=tuple(p))
    mrlib.set_parent(e, pose_obj)
    return e


def verify(path, poses: dict, empties=(), file_budget=None) -> bool:
    """poses: {name: per-pose tri budget}. Checks the nodes, M_Echo only, tris, name hints."""
    st = G.glb_stats(path)
    doc = G.glb_json(path)
    ok = True
    names = st["nodes"]
    for n in list(poses) + list(empties):
        if n not in names:
            print(f"[echo3] MISSING node {n}")
            ok = False
    if st["materials"] != ["M_Echo"]:
        print(f"[echo3] materials {st['materials']} (expected only M_Echo)")
        ok = False
    # meshes by node
    for nd in doc["nodes"]:
        if "mesh" in nd:
            m = doc["meshes"][nd["mesh"]]
            t = st["per_mesh"].get(m.get("name"), 0)
            b = poses.get(nd.get("name"))
            flag = "" if b is None else (" OK" if t <= b else " OVER")
            print(f"[echo3] node {nd['name']}: {t} tris" + (f" / {b}{flag}" if b else ""))
            if b is not None and t > b:
                ok = False
            rot = nd.get("rotation", [0, 0, 0, 1])
            if max(abs(rot[0]), abs(rot[1]), abs(rot[2])) > 1e-4 or nd.get("translation", [0, 0, 0]) != [0, 0, 0] \
                    and max(abs(v) for v in nd.get("translation", [0, 0, 0])) > 1e-5:
                print(f"[echo3] node {nd['name']} is not at identity: {nd.get('translation')} {rot}")
                ok = False
    for e in empties:
        for i, nd in enumerate(doc["nodes"]):
            if nd.get("name") == e:
                par = [p["name"] for p in doc["nodes"] if i in p.get("children", [])]
                print(f"[echo3] empty {e}: translation {[round(v, 4) for v in nd.get('translation', [0, 0, 0])]} "
                      f"rotation {nd.get('rotation', [0, 0, 0, 1])} parent {par}")
    print(f"[echo3] file tris {st['tris']}" + (f" / {file_budget}" if file_budget else "") + f", surfaces {st['surfaces']}")
    if file_budget and st["tris"] > file_budget:
        ok = False
    ok = G.check_names(path) and ok
    print(f"[echo3] verify {'PASS' if ok else 'FAIL'} {os.path.basename(path)}")
    return ok


def contact_report(label, obj, godot_pt, radius=0.06) -> float:
    """Distance from a Godot figure-frame contact point to the pose's surface (export orientation)."""
    mrlib.refresh()
    p = Vector((godot_pt[0], -godot_pt[2], godot_pt[1]))
    tree = E.bvh(obj)
    loc, _n, _i, d = tree.find_nearest(p)
    near = sum(1 for v in obj.data.vertices if (obj.matrix_world @ v.co - p).length < radius)
    print(f"[echo3] contact {label} {tuple(godot_pt)}: nearest surface {d * 100:.1f} cm away, {near} vertices "
          f"within {radius * 100:.0f} cm")
    return d


# ------------------------------------------------------------------ QA
def solo(objs, keep):
    """Show only `keep` (render visibility) among `objs`."""
    for o in objs:
        o.hide_render = o not in keep
        for c in o.children:
            c.hide_render = o not in keep


def figure_lights(cam, target):
    return E.rim_lights(cam, target)


def clay(name, cam_g, target_g, lens=45.0, res=(480, 640), samples=24):
    return L.clay(name, L.g2b(*cam_g), L.g2b(*target_g), lens=lens, res=res, samples=samples)


def ghost(name, objs, cam_g, target_g, lens=45.0, res=(480, 640), samples=24):
    return L.ghost(name, objs, L.g2b(*cam_g), L.g2b(*target_g), lens=lens, res=res, samples=samples)


def fov_lens(fov_deg, res):
    fov = math.radians(fov_deg)
    aspect = res[0] / res[1]
    return (36.0 / aspect) / (2 * math.tan(fov / 2)) if aspect >= 1 else 36.0 / (2 * math.tan(fov / 2))


def context(name, objs, pose_obj, pos, yaw, build_ctx, cam_w, target_w, fov=50.0, res=(960, 640), samples=28,
            points=None):
    """The pose (ghost look) placed at world pos / yaw (Godot), inside a proxy context, seen from a game view."""
    return L.context_render(name, objs, pose_obj, pos, yaw, build_ctx, cam_w, target_w, lens_fov_deg=fov, res=res,
                            samples=samples, points=points)


def world_mount(base_pos, base_yaw, local, local_yaw):
    """A mount given in a model's local Godot frame -> world (pos, yaw). Rotation about +Y only."""
    a = math.radians(base_yaw)
    x, y, z = local
    wx = base_pos[0] + x * math.cos(a) + z * math.sin(a)
    wz = base_pos[2] - x * math.sin(a) + z * math.cos(a)
    return (wx, base_pos[1] + y, wz), base_yaw + local_yaw


def gaussian_w(centres, sigma):
    return L.gauss_w(centres, sigma)


def smooth01(t):
    return L.smooth01(t)


__all__ = ["E", "L", "mrlib", "np", "vec", "Vector", "Matrix"]
