"""bridge.glb — the operator's bridge of the Array Hall (Chapter 4, group A): a riveted plate-girder deck at y = 2.5
(x +-5.9, z 11.95 - 14.8) across the mouth of the south bay, a pier wall under it that carries Panel 0, two stair flights
along the bay walls, the north rail with the gate opening and four numeral plates for the handwheels, the rear rail
and the catwalk gate. Contract: docs/models/ch4.md section 3 bridge; results: docs/models/ch4_a.md.

Built in WORLD coordinates. Mesh objects:
  bridge_deck    M_Chequer    deck slab, 26 stair treads, 4 flat numeral-free plates are NOT here (see bridge_rail)
  bridge_frame   M_Steel_Dark front fascia girder (stiffeners, rivets), rear girder, cross beams, columns, rail posts,
                 stair stringers
  bridge_rail    M_Brass_Aged north rail (gate opening x +-0.55), side + rear rails, stair handrails, the four numeral
                 plates I..IV lying on the deck in front of the wheel mounts (numerals read upright from the south)
  bridge_paint   M_Steel_Painted the pier wall under the deck (x +-3.2, z 14.0 - 14.4) with raised panels
  catwalk_gate   M_Brass_Aged  lattice gate leaf 1.0 x 1.05, origin at the hinge (-0.55, 2.5, 11.95); closed = identity;
                 open = +95 deg about +Y (swings north onto the catwalk)
  empties        wheel_mount_1..4 (-3.6 / -2.2 / 2.2 / 3.6, 2.5, 12.45), desk_mount (0, 2.5, 13.15),
                 echo_mount_wheels_1/2 (-/+2.9, 2.5, 13.3) yaw 180, bridge_light (0, 5.9, 13.5)

    blender -b --factory-startup -P tools/blender/models/bridge.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, B, STEEL, BRASS, CHEQ, PAINT  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "bridge"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 10000, 7, 4
DECK = C.DECK_Y
X1, Z0, Z1 = C.BRIDGE_X, C.BRIDGE_Z0, C.BRIDGE_Z1       # 5.9, 11.95, 14.8
RAIL_Y = 3.55
WHEEL_X = (-3.6, -2.2, 2.2, 3.6)
STAIR_N = 14
RISE = DECK / STAIR_N
RUN = (C.BAY_BACK - 0.2 - Z1) / (STAIR_N - 1)            # 18.0 -> 14.8 over 13 treads
GATE_X0, GATE_X1 = -0.55, 0.55


def rod(a, b, r, mat, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    return K.gcyl("rod", r, 0.0, d.length, base=tuple(a), axis=tuple(d.normalized()), segments=segs, mat=mat, smooth=60.0)


# ====================================================================== deck + treads (chequer)
def deck_parts():
    out = [K.gbox("deck", (-X1, DECK - 0.06, Z0), (X1, DECK, Z1), CHEQ, 0.004)]
    for sx in (-1, 1):
        xa, xb = sorted((sx * 4.9, sx * 5.9))
        for k in range(1, STAIR_N):
            h = RISE * k
            zf = C.BAY_BACK - 0.2 - RUN * k                 # nosing (north edge) of tread k
            out.append(K.gbox("tread", (xa, h - 0.045, zf), (xb, h, zf + RUN + 0.02), CHEQ, 0.003))
    return out


# ====================================================================== steel frame
def frame_parts():
    out = []
    # front fascia plate girder: web, flanges, stiffeners, rivets
    out.append(K.gbox("fascia", (-X1, 1.55, Z0), (X1, DECK - 0.06, Z0 + 0.05), STEEL, 0.004))
    out.append(K.gbox("fascia_top", (-X1, DECK - 0.11, Z0 - 0.04), (X1, DECK - 0.06, Z0 + 0.14), STEEL, 0.004))
    out.append(K.gbox("fascia_bot", (-X1, 1.50, Z0 - 0.04), (X1, 1.55, Z0 + 0.14), STEEL, 0.004))
    for i in range(0, 13):
        x = -X1 + 0.35 + i * (2 * X1 - 0.7) / 12.0
        out.append(K.gbox("stiff", (x - 0.05, 1.55, Z0 - 0.045), (x + 0.05, DECK - 0.11, Z0), STEEL, 0.002))
    for i in range(0, 40):
        x = -X1 + 0.15 + i * (2 * X1 - 0.3) / 39.0
        out.append(K.rivet("rv", 0.02, (x, DECK - 0.15, Z0 - 0.045), normal=(0, 0, -1), mat=STEEL, segs=5))
        out.append(K.rivet("rv", 0.02, (x, 1.62, Z0 - 0.045), normal=(0, 0, -1), mat=STEEL, segs=5))
    # rear girder and cross beams under the deck
    out.append(K.gbox("rear_g", (-X1, 1.75, Z1 - 0.3), (X1, DECK - 0.06, Z1 - 0.24), STEEL, 0.004))
    out.append(K.gbox("rear_g_fl", (-X1, DECK - 0.11, Z1 - 0.42), (X1, DECK - 0.06, Z1 - 0.12), STEEL, 0.004))
    for i in range(0, 10):
        x = -X1 + 0.55 + i * (2 * X1 - 1.1) / 9.0
        out.append(K.gbox("xbeam", (x - 0.04, 2.15, Z0 + 0.05), (x + 0.04, DECK - 0.06, Z1 - 0.3), STEEL, 0.002))
    # columns: four on the front line, two at the rear corners
    for x in (-5.5, -3.3, 3.3, 5.5):
        out.append(K.gbox("col", (x - 0.2, 0.0, Z0 + 0.3 - 0.2), (x + 0.2, 1.50, Z0 + 0.3 + 0.2), STEEL, 0.01))
        out.append(K.gbox("col_base", (x - 0.3, 0.0, Z0 + 0.1), (x + 0.3, 0.1, Z0 + 0.5), STEEL, 0.006))
    for x in (-5.5, 5.5):
        out.append(K.gbox("col_r", (x - 0.2, 0.0, Z1 - 0.65), (x + 0.2, 1.75, Z1 - 0.25), STEEL, 0.01))
    # rail posts: north rail (gate posts at +-0.6), rear rail, short side rails
    xs = [-5.9 + 0.05 + i * 1.07 for i in range(0, 12)]
    for x in xs:
        if abs(x) < 0.9:
            continue
        out.append(K.gbox("post", (x - 0.035, DECK, Z0 + 0.015), (x + 0.035, RAIL_Y, Z0 + 0.085), STEEL, 0.003))
    for x in (-0.6, 0.6):
        out.append(K.gbox("gpost", (x - 0.06, DECK, Z0 - 0.01), (x + 0.06, RAIL_Y + 0.05, Z0 + 0.11), STEEL, 0.005))
    for x in [-4.85 + i * 1.2125 for i in range(0, 9)]:
        out.append(K.gbox("rpost", (x - 0.035, DECK, Z1 - 0.085), (x + 0.035, RAIL_Y, Z1 - 0.015), STEEL, 0.003))
    for sx in (-1, 1):
        out.append(K.gbox("spost", (sx * X1 - 0.035 + (-0.04 * sx), DECK, Z0 + 0.0), (sx * X1 + 0.035 + (-0.04 * sx), RAIL_Y, Z0 + 0.07), STEEL, 0.003))
    # stair stringers (inner side) + posts
    for sx in (-1, 1):
        xa, xb = sorted((sx * 4.9, sx * 4.9 - sx * 0.06))
        z_lo, z_hi = C.BAY_BACK - 0.2, Z1
        prof = [(z_lo, 0.0), (z_hi, DECK - 0.3), (z_hi, DECK + 0.02), (z_lo, 0.32)]
        out.append(B.prism_x("stringer", prof, xa, xb, STEEL))
        for k in range(0, 4):
            t = k / 3.0
            z = z_lo + (z_hi - z_lo) * t
            y = 0.32 + (DECK + 0.02 - 0.32) * t
            out.append(K.gbox("stpost", (sx * 4.93 - 0.03, y, z - 0.03), (sx * 4.93 + 0.03, y + 1.0 - 0.0, z + 0.03), STEEL, 0.002))
    return out


# ====================================================================== brass rails + numeral plates
def rail_parts():
    out = []
    # north rail: top + mid, either side of the gate opening
    for (xa, xb) in ((-X1, GATE_X0 - 0.05), (GATE_X1 + 0.05, X1)):
        out.append(rod((xa, RAIL_Y, Z0 + 0.05), (xb, RAIL_Y, Z0 + 0.05), 0.03, BRASS, 10))
        out.append(rod((xa, DECK + 0.55, Z0 + 0.05), (xb, DECK + 0.55, Z0 + 0.05), 0.02, BRASS, 8))
    # rear rail
    out.append(rod((-4.85, RAIL_Y, Z1 - 0.05), (4.85, RAIL_Y, Z1 - 0.05), 0.03, BRASS, 10))
    out.append(rod((-4.85, DECK + 0.55, Z1 - 0.05), (4.85, DECK + 0.55, Z1 - 0.05), 0.02, BRASS, 8))
    # short side rails where the deck leaves the bay walls
    for sx in (-1, 1):
        x = sx * (X1 - 0.02)
        out.append(rod((x, RAIL_Y, Z0 + 0.05), (x, RAIL_Y, 12.7), 0.03, BRASS, 10))
        out.append(rod((x, DECK + 0.55, Z0 + 0.05), (x, DECK + 0.55, 12.7), 0.02, BRASS, 8))
    # stair handrails (tube along the slope, 1.0 above the stringer top)
    for sx in (-1, 1):
        x = sx * 4.93
        out.append(rod((x, 0.32 + 1.0, C.BAY_BACK - 0.2), (x, DECK + 0.02 + 1.0, Z1), 0.03, BRASS, 10))
        out.append(rod((x, DECK + 1.02, Z1), (x, DECK + 1.02, Z1 - 0.15), 0.03, BRASS, 10))
    # numeral plates I..IV on the deck in front of the wheel mounts, numerals read upright from the south
    for i, x in enumerate(WHEEL_X):
        out.append(K.gbox("np", (x - 0.17, DECK, 12.80), (x + 0.17, DECK + 0.012, 13.00), BRASS, 0.003))
        num = C.N.roman_obj(f"num_{i + 1}", i + 1, 0.12, 0.006, BRASS)
        num.data.transform(Matrix.Rotation(math.radians(-90.0), 4, "X"))      # lie on the plate, top toward north
        num.data.transform(Matrix.Translation((x, DECK + 0.012, 12.90)))
        out.append(num)
    return out


# ====================================================================== pier wall (painted)
def paint_parts():
    out = [K.gbox("pier", (-3.2, 0.0, 14.0), (3.2, DECK - 0.06, 14.4), PAINT, 0.01)]
    out.append(K.gbox("pier_plinth", (-3.26, 0.0, 13.94), (3.26, 0.16, 14.0), PAINT, 0.006))
    out.append(K.gbox("pier_cap", (-3.26, DECK - 0.2, 13.94), (3.26, DECK - 0.06, 14.0), PAINT, 0.006))
    for (x0, x1) in ((-3.0, -1.25), (1.25, 3.0)):               # raised panels flanking Panel 0
        out.append(K.gbox("pier_pan", (x0, 0.35, 13.96), (x1, DECK - 0.4, 14.0), PAINT, 0.006))
    return out


# ====================================================================== the gate
def gate():
    """Lattice gate leaf in the rail opening, 1.0 wide x 1.05 high, hinged at (-0.55, 2.5, 11.95)."""
    px, py, pz = GATE_X0, DECK, Z0 + 0.05
    parts = []
    x0, x1 = px + 0.04, GATE_X1 - 0.03
    parts.append(K.gbox("g_top", (x0, py + 0.99, pz - 0.02), (x1, py + 1.05, pz + 0.02), BRASS, 0.003))
    parts.append(K.gbox("g_mid", (x0, py + 0.52, pz - 0.015), (x1, py + 0.56, pz + 0.015), BRASS, 0.002))
    parts.append(K.gbox("g_bot", (x0, py + 0.10, pz - 0.02), (x1, py + 0.16, pz + 0.02), BRASS, 0.003))
    parts.append(K.gbox("g_hinge", (px, py + 0.05, pz - 0.035), (px + 0.05, py + 1.05, pz + 0.035), BRASS, 0.003))
    parts.append(K.gbox("g_free", (x1 - 0.05, py + 0.05, pz - 0.03), (x1, py + 1.05, pz + 0.03), BRASS, 0.003))
    for i in range(1, 7):
        x = x0 + (x1 - x0) * i / 7.0
        parts.append(K.gbox("g_bar", (x - 0.012, py + 0.16, pz - 0.012), (x + 0.012, py + 0.99, pz + 0.012), BRASS, 0.0))
    parts.append(rod((x0 + 0.03, py + 0.16, pz), (x1 - 0.06, py + 0.99, pz), 0.012, BRASS, 6))
    parts.append(K.gbox("g_lock", (x1 - 0.13, py + 0.50, pz - 0.05), (x1 - 0.02, py + 0.66, pz + 0.05), BRASS, 0.004))
    parts.append(K.gcyl("g_lamp", 0.025, 0.0, 0.03, base=(x1 - 0.075, py + 0.68, pz), axis=(0, 1, 0), segments=8, mat=BRASS))
    return K.part("catwalk_gate", parts, pivot=(px, py, pz))


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    deck = C.merge("bridge_deck", deck_parts())
    frame = C.merge("bridge_frame", frame_parts())
    rail = C.merge("bridge_rail", rail_parts())
    paint = C.merge("bridge_paint", paint_parts())
    g = gate()
    for i, x in enumerate(WHEEL_X):
        K.empty(f"wheel_mount_{i + 1}", (x, DECK, 12.45))
    K.empty("desk_mount", (0.0, DECK, 13.15))
    K.empty("echo_mount_wheels_1", (-2.9, DECK, 13.3), rot_deg=(0.0, 180.0, 0.0))
    K.empty("echo_mount_wheels_2", (2.9, DECK, 13.3), rot_deg=(0.0, 180.0, 0.0))
    K.empty("bridge_light", (0.0, 5.9, 13.5))
    K.to_blender()
    C.finalize()
    return dict(deck=deck, frame=frame, rail=rail, paint=paint, gate=g)


def verify(path):
    req = ["bridge_deck", "bridge_frame", "bridge_rail", "bridge_paint", "catwalk_gate", "wheel_mount_1", "wheel_mount_2",
           "wheel_mount_3", "wheel_mount_4", "desk_mount", "echo_mount_wheels_1", "echo_mount_wheels_2", "bridge_light"]
    expect = {"catwalk_gate": (GATE_X0, DECK, Z0 + 0.05), "desk_mount": (0, DECK, 13.15), "wheel_mount_1": (-3.6, DECK, 12.45),
              "wheel_mount_4": (3.6, DECK, 12.45), "echo_mount_wheels_1": (-2.9, DECK, 13.3), "bridge_light": (0, 5.9, 13.5)}
    ident = [n for n in req if not n.startswith("echo_mount")]
    errs = C.verify(path, required=req, identity=ident, expect=expect, rot_expect={"echo_mount_wheels_1": (0, 180, 0)},
                    tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = C.bounds(["bridge_deck", "bridge_frame", "bridge_rail", "bridge_paint"])
    print(f"{C.TAG} bridge bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    C.qa_floor_nonormal("bridge_deck")
    C.qa_hall(shell=True, extra=[("shell_lift4", (0, 0, 0), 0.0), ("freight_lift", C.LIFT_POS, 0.0)])
    C.qa_floor_nonormal("qa_sh_hall_floor")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))
        if o.name.startswith("qa_freight_lift_IA_gate_") and o.type == "MESH" and "lock" not in o.name:
            o.scale = (1.0, 0.15, 1.0)
    core = M.sphere("qa_core", 0.6, loc=K.G(*C.CORE_C), segments=24, rings=12)
    K.override(core, K.glow("qa_core", "CFF6FF", 8.0))
    core.visible_shadow = False
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
        K.light("bay_lamp_w", "POINT", (-5.55, 3.4, 16.0), 1500.0, "FFC27A", radius=0.1)
        K.light("bay_lamp_e", "POINT", (5.55, 3.4, 16.0), 1500.0, "FFC27A", radius=0.1)
    if C.want(args, "1"):          # from the hall: the bridge across the bay mouth, the catwalk gate open
        K.pose_rot(parts["gate"], "y", 95.0)
        cam, tgt = (0.0, 1.7, 5.5), (0.0, 2.9, 13.2)
        lit(cam, 60.0, 0.14)
        C.shoot(NAME, cam, tgt, 62, samples=S, res=RES)
        K.pose_rot(parts["gate"], "y", -95.0)
    if C.want(args, "2"):          # the lift view (R): the east gate, the stair, the underside
        cam, tgt, fov = C.view("lift")
        lit(cam, 40.0, 0.12)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # on the deck, looking along the north rail (the bridge view's foreground)
        cam, tgt, fov = (-4.6, 3.7, 14.3), (0.0, 3.3, 12.0), 64
        lit(cam, 60.0, 0.16)
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
