"""freight_lift.glb — the freight lift cage at Level -2 with its two collapsible lattice gates and key locks.
Contract: docs/models/ch3.md §3 freight_lift (+ §1.1 lobby, §1.5 cage_lamp, §2 lift_w / lift_e); results:
docs/models/ch3_a.md.

Origin = the cage floor centre at lobby level, world (0, 0, 6.0), yaw 0. The cage floor is at local y 0.25; the
interior is local x, z ∈ [-1.1, 1.1].

  freight_cage (static)   deck, bridge ramps (1.0 long) down to the lobby at both gates, riveted panel walls north and
                          south (bars above 1.35 m), corner posts, roof frame at 2.6 with the hoist crosshead, sheave and
                          ropes, gate tracks and jambs, brass grab rails, brass level plates "−2" above both gates,
                          the bulb cage
  IA_gate_west / _east    collapsible lattice gates, origin at the north post (∓1.1, 0.25, -0.95), lattice +Z to +0.95,
                          2.1 high. Open = scale local Z to 0.15 about the origin.
  IA_gate_lock_west       brass lock box at (-1.0, 1.15, 0.92) with Strand's mark inlaid; gate_key_mount_west on its slot
  IA_gate_lock_east       brass lock box at (1.0, 1.15, 0.92) with Leyla's sign inlaid; gate_key_mount_east
  cage_bulb, cage_light   the frosted bulb (code emission) and its light empty

    blender -b --factory-startup -P tools/blender/models/freight_lift.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "freight_lift"
TRI_BUDGET, SURF_BUDGET = 7000, 10
STEEL, PAINT, BRASS, FROST = K.STEEL, K.PAINT, K.BRASS, K.FROST
FY = 0.25                      # cage floor
HW = 1.1                       # interior half width
ROOF = 2.6
GATE_Z0, GATE_Z1, GATE_H = -0.95, 0.95, 2.1
LOCK = {"west": (-1.0, 1.15, 0.92), "east": (1.0, 1.15, 0.92)}
LOCK_SIZE = (0.06, 0.15, 0.10)         # x, y, z
KEY_ABOVE = 0.036                      # key origin above the slot: the blade tip sits ~3 cm inside the lock
BULB = (0.0, 2.36, 0.0)
FOLD = 0.15


# ====================================================================== static cage
def cage():
    p = []
    # deck (y 0 .. 0.25) with a steel skirt and tread bars, ramps down to the lobby at both gates
    p.append(K.gbox("deck", (-HW - 0.05, 0.0, -HW - 0.05), (HW + 0.05, FY, HW + 0.05), STEEL, 0.01))
    for k in range(9):
        z = -0.88 + 0.22 * k
        p.append(K.gbox("tread", (-0.98, FY, z - 0.012), (0.98, FY + 0.008, z + 0.012), STEEL, 0.0))
    for sx in (-1, 1):
        x0, x1 = sx * (HW + 0.05), sx * (HW + 1.05)
        ramp = K.gbox("ramp", (-0.5, -0.025, -0.80), (0.5, 0.0, 0.80), STEEL, 0.006)
        ang = math.atan2(FY, 1.0)
        ramp.data.transform(Matrix.Translation(((x0 + x1) / 2, FY / 2, 0.0)) @ Matrix.Rotation(-sx * ang, 4, "Z"))
        p.append(ramp)
        for k in range(5):
            t = (k + 0.5) / 5
            x = x0 + (x1 - x0) * t
            y = FY * (1 - t)
            bar = K.gbox("rtread", (-0.012, 0.0, -0.72), (0.012, 0.008, 0.72), STEEL, 0.0)
            bar.data.transform(Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(-sx * ang, 4, "Z"))
            p.append(bar)
        # side curbs on the ramp
        for sz in (-1, 1):
            c = K.gbox("curb", (-0.5, 0.0, -0.02), (0.5, 0.05, 0.02), STEEL, 0.004)
            c.data.transform(Matrix.Translation(((x0 + x1) / 2, FY / 2, sz * 0.80)) @ Matrix.Rotation(-sx * ang, 4, "Z"))
            p.append(c)
    # corner posts (angles)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (HW + 0.02), sz * (HW + 0.02)
            p.append(K.gbox("post", (x - 0.04, 0.0, z - 0.04), (x + 0.04, ROOF + 0.08, z + 0.04), STEEL, 0.006))
    # north / south walls: lower riveted panel, bars above, rails
    for sz in (-1, 1):
        zi, zo = sz * HW, sz * (HW + 0.03)
        lo, hi = min(zi, zo), max(zi, zo)
        p.append(K.gbox("panel", (-HW + 0.03, FY, lo), (HW - 0.03, 1.35, hi), PAINT, 0.004))
        for y in (0.62, 1.00):
            p.append(K.gbox("stiff", (-HW + 0.03, y - 0.03, zi - sz * 0.015), (HW - 0.03, y + 0.03, zi), PAINT, 0.004))
        for y in (FY + 0.06, 1.29):
            for x in [-0.95 + 0.38 * k for k in range(6)]:
                p.append(K.rivet("prv", 0.008, (x, y, zi), normal=(0, 0, -sz), mat=PAINT, segs=5))
        p.append(K.gbox("prail", (-HW + 0.03, 1.33, lo - 0.01), (HW - 0.03, 1.39, hi + 0.01), PAINT, 0.006))
        p.append(K.gbox("mrail", (-HW + 0.03, 1.95, lo), (HW - 0.03, 1.99, hi), PAINT, 0.004))
        for k in range(13):
            x = -0.96 + 0.16 * k
            p.append(K.gcyl("bar", 0.011, 1.39, ROOF - 0.04, base=(x, 0.0, (zi + zo) / 2), axis=(0, 1, 0), segments=6,
                            mat=PAINT, caps=False))
        # brass grab rail on the inside
        zr = zi - sz * 0.07
        p.append(K.V.tube("grab", [(-0.85, 1.0, zi), (-0.85, 1.0, zr), (0.85, 1.0, zr), (0.85, 1.0, zi)], 0.016, sides=6,
                          mat=BRASS, fillet=0.05))
    # roof frame, lintels over the gates with the level plates, crosshead, sheave, ropes
    for sz in (-1, 1):
        p.append(K.gbox("roofz", (-HW - 0.06, ROOF - 0.05, sz * HW - 0.06), (HW + 0.06, ROOF + 0.08, sz * HW + 0.06), STEEL, 0.006))
    for sx in (-1, 1):
        p.append(K.gbox("roofx", (sx * HW - 0.06, ROOF - 0.05, -HW), (sx * HW + 0.06, ROOF + 0.08, HW), STEEL, 0.006))
        p.append(K.gbox("lintel", (sx * HW - 0.025, 2.38, -HW), (sx * HW + 0.025, ROOF - 0.05, HW), PAINT, 0.004))
        p += level_plate(sx)
        # gate tracks and jambs
        p.append(K.gbox("track", (sx * HW - 0.04, 2.36, -HW), (sx * HW + 0.04, 2.40, HW), STEEL, 0.003))
        p.append(K.gbox("btrack", (sx * HW - 0.03, FY, -HW + 0.05), (sx * HW + 0.03, FY + 0.02, HW - 0.05), STEEL, 0.002))
        for sz in (-1, 1):
            p.append(K.gbox("jamb", (sx * HW - 0.035, FY, sz * 1.0 - 0.03), (sx * HW + 0.035, 2.38, sz * 1.0 + 0.03), STEEL, 0.004))
    p.append(K.gbox("xhead", (-HW, ROOF + 0.08, -0.08), (HW, ROOF + 0.24, 0.08), STEEL, 0.008))
    for sx in (-1, 1):
        p.append(K.gbox("yoke", (sx * 0.08 - 0.02, ROOF + 0.24, -0.06), (sx * 0.08 + 0.02, 3.25, 0.06), STEEL, 0.004))
    sheave = K.glathe("sheave", [(0.05, -0.05), (0.33, -0.05), (0.34, -0.03), (0.30, 0.0), (0.34, 0.03), (0.33, 0.05),
                                 (0.05, 0.05)], (0.0, 3.0, 0.0), (1, 0, 0), 24, STEEL, smooth=40.0)
    p.append(sheave)
    p.append(K.gcyl("axle", 0.035, -0.12, 0.12, base=(0.0, 3.0, 0.0), axis=(1, 0, 0), segments=10, mat=STEEL))
    for sz in (-1, 1):
        p.append(K.gcyl("rope", 0.011, 0.0, 12.0 - 3.0, base=(0.0, 3.0, sz * 0.31), axis=(0, 1, 0), segments=5, mat=STEEL))
    # bulb cage (wire guard) under the crosshead
    bx, by, bz = BULB
    p.append(K.gcyl("lampholder", 0.03, 0.0, 0.08, base=(bx, by + 0.12, bz), axis=(0, 1, 0), segments=10, mat=STEEL))
    for y, r in ((by + 0.11, 0.075), (by - 0.02, 0.085)):
        ring = M.torus("cring", r, 0.004, major_seg=12, minor_seg=4, mat=STEEL)
        ring.data.transform(Matrix.Translation((bx, y, bz)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
        p.append(ring)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        pts = [(bx + 0.075 * math.cos(a), by + 0.11, bz + 0.075 * math.sin(a)),
               (bx + 0.088 * math.cos(a), by + 0.03, bz + 0.088 * math.sin(a)),
               (bx + 0.06 * math.cos(a), by - 0.10, bz + 0.06 * math.sin(a)), (bx, by - 0.13, bz)]
        p.append(K.V.tube("cwire", pts, 0.004, sides=4, mat=STEEL))
    return K.part("freight_cage", p)


def level_plate(sx):
    """Brass plate with raised dark-steel '−2' on the inside face of the lintel over gate sx (faces into the cage)."""
    x = sx * (HW - 0.025)
    out = []
    pl = K.plate("lvl", [L.rounded_rect(0.20, 0.13, 0.012, 3)], 0.004, mat=BRASS, bevel=0.0)
    txt = K.V.text("lvltxt", "−2", 0.085, (0.0, 0.0), 0.004, font=K.V.FONT_SANS_B, mat=STEEL, depth=0.002)
    ring = K.flat("lvlring", L.outline_ring(0.185, 0.115, 0.010, 0.004, 3), 0.0042, (0.0, 0.0), STEEL)
    for o in (pl, txt, ring):
        # plate faces +Z in its frame -> rotate to face -sx X (into the cage) on the lintel
        o.data.transform(Matrix.Translation((x, 2.49, 0.0)) @ Matrix.Rotation(math.radians(-90 * sx), 4, "Y"))
        out.append(o)
    for sz in (-1, 1):
        out.append(K.rivet("lvlrv", 0.006, (x - sx * 0.004, 2.49, sz * 0.085), normal=(-sx, 0, 0), mat=BRASS, segs=5))
    return out


# ====================================================================== gates
def strap(ln, t=0.006, w=0.012):
    """Open-ended flat bar along local Z (front, back and two edges: 8 tris)."""
    import bmesh
    bm = bmesh.new()
    pts = [(-t, -w, -ln / 2), (t, -w, -ln / 2), (t, w, -ln / 2), (-t, w, -ln / 2)]
    a = [bm.verts.new(p) for p in pts]
    b = [bm.verts.new((x, y, z + ln)) for (x, y, z) in pts]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.obj_from_bm("strap", bm, PAINT)


def gate(side):
    sx = -1 if side == "west" else 1
    x = sx * HW
    y0, y1 = FY + 0.02, FY + GATE_H
    n = 10
    zs = [GATE_Z0 + (GATE_Z1 - GATE_Z0) * k / n for k in range(n + 1)]
    parts = []
    for k, z in enumerate(zs):
        w = 0.035 if k in (0, n) else 0.022
        parts.append(K.gbox("picket", (x - 0.012, y0, z - w / 2), (x + 0.012, y1, z + w / 2), PAINT, 0.0))
    tiers = 3
    th = (y1 - y0 - 0.08) / tiers
    for t in range(tiers):
        ya, yb = y0 + 0.04 + th * t, y0 + 0.04 + th * (t + 1)
        for k in range(n):
            za, zb = zs[k], zs[k + 1]
            for (p0, p1) in (((za, ya), (zb, yb)), ((za, yb), (zb, ya))):
                d = Vector((0.0, p1[1] - p0[1], p1[0] - p0[0]))
                ln = d.length
                bar = strap(ln)
                ang = math.atan2(d.y, d.z)
                bar.data.transform(Matrix.Translation((x + sx * 0.016, (p0[1] + p1[1]) / 2, (p0[0] + p1[0]) / 2)) @
                                   Matrix.Rotation(-ang, 4, "X"))
                parts.append(bar)
    # top and bottom rails with roller hangers; the pull handle at the free end
    parts.append(K.gbox("grail", (x - 0.015, y1 - 0.03, GATE_Z0), (x + 0.015, y1, GATE_Z1), PAINT, 0.003))
    parts.append(K.gbox("grail", (x - 0.015, y0, GATE_Z0), (x + 0.015, y0 + 0.03, GATE_Z1), PAINT, 0.003))
    for z in (GATE_Z0 + 0.02, GATE_Z1 - 0.02):
        parts.append(K.gcyl("roller", 0.022, -0.012, 0.012, base=(x, y1 + 0.03, z), axis=(1, 0, 0), segments=8, mat=PAINT))
    xh = x - sx * 0.05
    parts.append(K.V.tube("handle", [(x - sx * 0.012, 1.05, GATE_Z1 - 0.03), (xh, 1.08, GATE_Z1 - 0.03),
                                     (xh, 1.32, GATE_Z1 - 0.03), (x - sx * 0.012, 1.35, GATE_Z1 - 0.03)], 0.012, sides=6,
                          mat=PAINT, fillet=0.02))
    return K.part(f"IA_gate_{side}", parts, pivot=(x, FY, GATE_Z0))


def gate_lock(side):
    cx, cy, cz = LOCK[side]
    sx = -1 if side == "west" else 1
    face = -sx                                         # the box front faces into the cage
    w, h, d = LOCK_SIZE
    parts = [K.gbox("lbox", (cx - w / 2, cy - h / 2, cz - d / 2), (cx + w / 2, cy + h / 2, cz + d / 2), BRASS, 0.008, 2)]
    # mounting bracket back to the post (south)
    parts.append(K.gbox("lbrk", (cx - 0.02, cy - 0.05, cz + d / 2), (cx + 0.02, cy + 0.05, 1.0 - 0.03), BRASS, 0.004))
    # key slot on the top: a raised escutcheon with a dark slot
    top = cy + h / 2
    parts.append(K.gbox("lesc", (cx - 0.022, top, cz - 0.03), (cx + 0.022, top + 0.006, cz + 0.03), BRASS, 0.002))
    slot = K.gbox("lslot", (cx - 0.004, top + 0.0062, cz - 0.022), (cx + 0.004, top + 0.0064, cz + 0.022), STEEL, 0.0)
    parts.append(slot)
    # the inlaid owner's mark on the front face
    kind = "mark" if side == "west" else "sign"
    sym = S.inlay("lsym", kind, 0.062, depth=0.0, mat=STEEL)
    ring = K.flat("lsymring", L.outline_ring(0.084, 0.084, 0.04, 0.003, 6), 0.0, (0.0, 0.0), STEEL)
    for o in (sym, ring):
        o.data.transform(Matrix.Translation((cx + face * (w / 2 + 0.0004), cy - 0.01, cz)) @
                         Matrix.Rotation(math.radians(90 * face), 4, "Y"))
        parts.append(o)
    o = K.part(f"IA_gate_lock_{side}", parts, pivot=(cx, cy, cz))
    return o, (cx, top + 0.0064 + KEY_ABOVE, cz)


def bulb():
    bx, by, bz = BULB
    g = K.glathe("bulb", [(0.0, -0.075), (0.03, -0.07), (0.05, -0.04), (0.052, -0.01), (0.04, 0.03), (0.018, 0.06),
                          (0.018, 0.10), (0.0, 0.10)], BULB, (0, 1, 0), 16, FROST, smooth=70.0)
    return K.part("cage_bulb", [g], pivot=BULB)


# ====================================================================== build / verify
def mount_basis(side):
    """Key standing blade down, bow up, bow face toward +X (west) / -X (east): item -Z -> +Y, item +Y -> face dir."""
    face = Vector((1, 0, 0)) if side == "west" else Vector((-1, 0, 0))
    ey = face
    ez = Vector((0, -1, 0))                 # item +Z (blade) points down
    ex = ey.cross(ez)
    return Matrix((ex, ey, ez)).transposed()


def build():
    M.reset_scene()
    K.ensure_materials()
    out = dict(cage=cage(), gate_w=gate("west"), gate_e=gate("east"), bulb=bulb())
    mounts = {}
    for side in ("west", "east"):
        lk, mp = gate_lock(side)
        out[f"lock_{side}"] = lk
        mounts[side] = mp
    K.empty("cage_light", BULB)
    for side in ("west", "east"):
        e = K.empty(f"gate_key_mount_{side}", mounts[side])
        e.rotation_euler = mount_basis(side).to_euler("XYZ")
    K.to_blender()
    for side in ("west", "east"):
        K.parent(bpy.data.objects[f"gate_key_mount_{side}"], out[f"lock_{side}"])
    A.finalize_uv()
    out["mounts"] = mounts
    return out


def verify(path, parts):
    req = ["freight_cage", "IA_gate_west", "IA_gate_east", "IA_gate_lock_west", "IA_gate_lock_east", "cage_bulb",
           "cage_light", "gate_key_mount_west", "gate_key_mount_east"]
    expect = {"IA_gate_west": (-HW, FY, GATE_Z0), "IA_gate_east": (HW, FY, GATE_Z0), "IA_gate_lock_west": LOCK["west"],
              "IA_gate_lock_east": LOCK["east"], "cage_light": BULB,
              "gate_key_mount_west": parts["mounts"]["west"], "gate_key_mount_east": parts["mounts"]["east"]}
    ident = [r for r in req if not r.startswith("gate_key_mount")]
    rot = {}
    for side in ("west", "east"):
        e = mount_basis(side).to_euler("XYZ")
        rot[f"gate_key_mount_{side}"] = tuple(math.degrees(a) for a in e)
    errs = K.V.verify_glb(path, required=req, identity=ident, expect=expect, rot_expect=rot,
                          parents={"gate_key_mount_west": "IA_gate_lock_west", "gate_key_mount_east": "IA_gate_lock_east"},
                          show=req)
    errs += K.facts(path, TRI_BUDGET, SURF_BUDGET)
    for side in ("west", "east"):
        b = mount_basis(side)
        print(f"{K.TAG} gate_key_mount_{side}: item -Z (bow) -> {tuple(round(c, 3) for c in b @ Vector((0, 0, -1)))}, "
              f"item +Y (face) -> {tuple(round(c, 3) for c in b @ Vector((0, 1, 0)))}, euler XYZ "
              f"{tuple(round(math.degrees(a), 1) for a in b.to_euler('XYZ'))}")
    return errs


# ====================================================================== QA
REST = {}


def pose(parts, west_open=False, east_open=False):
    for k in ("gate_w", "gate_e"):
        parts[k].matrix_basis = REST[k].copy()
    M.refresh()
    for k, o in (("gate_w", west_open), ("gate_e", east_open)):
        if o:
            g = parts[k]
            g.matrix_basis = g.matrix_basis @ Matrix.Diagonal((1.0, FOLD, 1.0, 1.0))   # Godot local Z = Blender -Y
    M.refresh()


def qa(parts, args):
    K.qa_begin(bounces=6)
    for k in ("gate_w", "gate_e"):
        REST[k] = parts[k].matrix_basis.copy()
    root = K.qa_place([o for o in bpy.context.scene.objects if o.parent is None and not o.name.startswith("qa")],
                      (0.0, 0.0, 6.0), 0.0)
    has_lobby = K.qa_import("shell_lift", (0, 0, 0), 0.0, prefix="qa_sl_") is not None
    if not has_lobby:
        K.V._qbox("qa_floor", (-6.6, -0.05, 4.7), (6.6, 0.0, 7.4), K.CHEQ)
        K.V._qbox("qa_wn", (-6.6, 0.0, 4.6), (6.6, 3.0, 4.7), K.CONC)
        K.V._qbox("qa_ws", (-6.6, 0.0, 7.4), (6.6, 3.0, 7.5), K.CONC)
    for o in list(bpy.data.objects):
        if o.name.startswith("qa_sl_intro"):
            o.hide_render = True
    keyp = os.path.join(M.MODELS_DIR, "key_strand.glb")
    if os.path.exists(keyp):
        K.V.attach(keyp, bpy.data.objects["gate_key_mount_west"], prefix="qa_key_")
    keyl = os.path.join(M.MODELS_DIR, "key_leyla.glb")
    if os.path.exists(keyl):
        K.V.attach(keyl, bpy.data.objects["gate_key_mount_east"], prefix="qa_keyl_")
    bulb_old = K.override(parts["bulb"], K.glow("qa_bulb", "FFE0B0", 12.0))

    def lights(cam=None):
        K.clear_lights()
        K.light("cage_lamp", "POINT", (0.0, 2.3, 6.0), 90.0, "FFD7A0", radius=0.05)
        K.light("lobby_w", "POINT", (-4.0, 2.6, 6.0), 120.0, "FFD7A0", radius=0.1)
        K.light("lobby_e", "POINT", (4.0, 2.6, 6.0), 120.0, "FFD7A0", radius=0.1)
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 8.0, "FFE2C2", radius=0.2)

    if K.want(args, "1"):        # lift_w (intro, Choir entry): west gate shut, Strand's key in its lock
        pose(parts)
        lights((0.5, 1.6, 6.4))
        K.shoot(NAME, (0.5, 1.6, 6.4), (-1.1, 1.35, 6.0), vfov=62)
    if K.want(args, "2"):        # lift_e: east gate open (folded), Leyla's key in its lock
        pose(parts, east_open=True)
        lights((-0.5, 1.6, 6.4))
        K.shoot(NAME + "_2", (-0.5, 1.6, 6.4), (1.1, 1.35, 6.0), vfov=62)
    if K.want(args, "3"):        # hero from the lobby, west gate open
        pose(parts, west_open=True)
        lights()
        K.shoot(NAME + "_3", (-4.6, 1.9, 7.1), (-0.4, 1.3, 5.9), vfov=58)
    if K.want(args, "4"):        # lock close-up (west): Strand's mark, the key standing in the slot
        pose(parts)
        cam = (-0.55, 1.35, 6.62)
        lights(cam)
        K.shoot(NAME + "_4", cam, (-1.0, 1.2, 6.92), vfov=40)
    K.restore(parts["bulb"], bulb_old)
    _ = root


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path, parts)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
