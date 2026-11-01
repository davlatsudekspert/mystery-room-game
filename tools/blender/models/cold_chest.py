"""cold_chest.glb — the Meridian chest of the Cold Store (N6 "Chest rings"; reward: two blank crystals and the Cold Store note).

A galvanised double-walled cold box with riveted steel corner straps, two rope handles and a hinged lid. Three knurled
rotating rings on the front each carry the SIX drum symbols (sun, moon, star, triangle, circle, square: decal
`M_Decal_ChestRings`, symbol k at angle 90 - 60 k degrees clockwise from the top, the one at the top is the selected one).
Lid top: the Meridian emblem stencil (`M_Decal_SafeStencil`) and a blank brass plate (`M_Decal_ChestPlate`, the inscription
"turn one and its neighbour follows" is supplied by code/tr()). Language neutral: no text on the model.

Model space (Godot): front +Z, origin on the floor at the footprint centre. Size 0.90 w x 0.52 d x 0.62 h (closed).
Parts (identity rotation at rest, origin = pivot):
  chest_body     everything static (feet, shell, straps, hinge knuckles, front plate, bezels, hub caps, pointers, lining)
  IA_lid         pivot at the hinge axis (0, 0.50, -0.26); opens with a NEGATIVE angle about +X (front edge rises), -105 deg
  IA_ring_0..2   pivot at the ring centre (-0.26 | 0 | +0.26, 0.27, 0.277); turn about +Z. Symbol k reaches the TOP when the
                 ring is rotated by +60 k degrees about +Z (counter-clockwise as seen from the front), k = 0 sun .. 5 square
  crystal_mount_0|1  empties inside at (-0.14|0.14, 0.31, 0.00)  (blank crystals rest here)
  note_mount     empty at (0, 0.31, 0.15)   (the folded Cold Store note)
  light_chest    empty at (0, 0.44, 0.0)    (small cold glow when opened)
    blender -b --factory-startup -P tools/blender/models/cold_chest.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "cold_chest"
BUDGET = 6000
ARGS = M.main_guard()
W, D = 0.90, 0.52
Y0, Y1 = 0.04, 0.50           # body bottom / top
LID_H = 0.12
ZF = D / 2                      # front face z
RX = (-0.26, 0.0, 0.26)
RY = 0.27
R_RIM, R_FACE = 0.095, 0.088
RING_T = 0.030
GALV, DARK, IRON, PAINT = "M_Steel_Galv", "M_Steel_Dark", "M_Iron_Rust", "M_Enamel_Ice"


def body():
    o = []
    shell = gbox("shell", (-W / 2, Y0, -D / 2), (W / 2, Y1, D / 2), GALV, bevel=0.006)
    cav = gbox("cav", (-W / 2 + 0.045, 0.30, -D / 2 + 0.045), (W / 2 - 0.045, Y1 + 0.02, D / 2 - 0.045), GALV, bevel=0.0)
    M.boolean(shell, cav)
    o.append(shell)
    # felt lining of the cavity floor (cold-blue grey) with two recesses for the crystals and a note slot
    o.append(gbox("lining", (-W / 2 + 0.046, 0.295, -D / 2 + 0.046), (W / 2 - 0.046, 0.302, D / 2 - 0.046), "M_Fabric", bevel=0.0))
    for k, x in enumerate((-0.14, 0.14)):
        o.append(gcyl(f"sock{k}", 0.05, 0.004, (x, 0.302, 0.0), axis="y", verts=16, mat="M_Velvet", bevel=0.0))
    o.append(gbox("note_slot", (-0.07, 0.302, 0.10), (0.07, 0.304, 0.20), "M_Paper", bevel=0.0))
    # feet and a plinth rail
    for sx in (-1, 1):
        for sz in (-1, 1):
            o.append(gbox("foot", (sx * 0.36 - 0.045, 0.0, sz * 0.18 - 0.045), (sx * 0.36 + 0.045, Y0 + 0.004, sz * 0.18 + 0.045), DARK, bevel=0.004))
    # corner straps (vertical, riveted) and two horizontal bands round the body
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (W / 2), sz * (D / 2)
            xa, xb = sorted((cx, cx - sx * 0.05))
            za, zb = sorted((cz, cz - sz * 0.05))
            o.append(gbox("cs_f", (xa - (0.004 if sx < 0 else 0), Y0, min(cz, cz + sz * 0.004)),
                          (xb + (0.004 if sx > 0 else 0), Y1, max(cz, cz + sz * 0.004)), PAINT, bevel=0.001))
            o.append(gbox("cs_s", (min(cx, cx + sx * 0.004), Y0, za), (max(cx, cx + sx * 0.004), Y1, zb), PAINT, bevel=0.001))
    rv = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in (0.09, 0.20, 0.31, 0.42):
                rv.append((sx * (W / 2 - 0.025), y, sz * (D / 2 + 0.004)))
    o.append(X.rivets("rv_f", rv, 0.0075, "z", mat=IRON, segs=6))
    for y in (0.115, 0.445):
        o.append(gbox(f"band{y}", (-W / 2 - 0.004, y - 0.022, -D / 2 - 0.004), (W / 2 + 0.004, y + 0.022, D / 2 + 0.004), PAINT, bevel=0.002))
    # front plate (dark enamel) carrying the three ring bezels
    o.append(gbox("front_plate", (-W / 2 + 0.07, 0.115 + 0.022, ZF), (W / 2 - 0.07, 0.445 - 0.022, ZF + 0.006), "M_Steel_Dark", bevel=0.002))
    for k, x in enumerate(RX):
        o.append(glathe(f"bezel{k}", [(0.100, 0.0), (0.112, 0.0), (0.112, 0.016), (0.104, 0.020), (0.100, 0.020)], (x, RY, ZF + 0.006), axis="z",
                        segments=36, mat="M_Brass_Aged"))
        o.append(glathe(f"hub{k}", [(0.0, 0.0), (0.040, 0.0), (0.042, 0.020), (0.036, 0.040), (0.0, 0.046)], (x, RY, ZF + 0.006 + 0.0), axis="z",
                        segments=18, mat="M_Brass_Polished"))
        # fixed pointer wedge above the ring
        o.append(X.C.gpoly(f"ptr{k}", [(-0.012, 0.0), (0.012, 0.0), (0.0, -0.022)], 0.004,
                           X.C.gframe((x, RY + 0.128, ZF + 0.026), (1, 0, 0), (0, 1, 0)), mat="M_Enamel_Crimson", bevel=0.0))
    # rope handles on the sides: steel bar on two posts
    for sx in (-1, 1):
        x = sx * (W / 2)
        o.append(X.pipe(f"hd{sx}", [(x, 0.30, -0.10), (x + sx * 0.040, 0.30, -0.10), (x + sx * 0.040, 0.30, 0.10), (x, 0.30, 0.10)], 0.009,
                        mat=DARK, sides=8, fillet=0.012, flange_ends=False))
    # hinge knuckles at the back
    for x in (-0.30, 0.30):
        o.append(gcyl(f"hk{x}", 0.018, 0.10, (x - 0.05, Y1 + 0.0, -ZF - 0.0), axis="x", verts=10, mat=DARK, bevel=0.0))
        o.append(gbox(f"hkp{x}", (x - 0.05, Y1 - 0.060, -ZF - 0.020), (x + 0.05, Y1 + 0.0, -ZF), DARK, bevel=0.002))
    # latch hasp on the front centre top (static hasp plate, no function)
    o.append(gbox("hasp", (-0.035, Y1 - 0.075, ZF), (0.035, Y1 - 0.005, ZF + 0.008), "M_Brass_Aged", bevel=0.002))
    o.append(gcyl("hasp_pin", 0.012, 0.012, (0.0, Y1 - 0.04, ZF + 0.008), axis="z", verts=10, mat="M_Brass_Polished", bevel=0.0))
    return o


def lid():
    o = []
    top = Y1 + LID_H
    shell = gbox("lid_shell", (-W / 2 - 0.004, Y1, -D / 2 - 0.004), (W / 2 + 0.004, top, D / 2 + 0.006), GALV, bevel=0.01)
    cav = gbox("lid_cav", (-W / 2 + 0.040, Y1 - 0.01, -D / 2 + 0.040), (W / 2 - 0.040, top - 0.035, D / 2 - 0.030), GALV, bevel=0.0)
    M.boolean(shell, cav)
    o.append(shell)
    for x in (-0.30, 0.30):
        o.append(gbox(f"lstrap{x}", (x - 0.03, Y1 + 0.004, -D / 2 - 0.008), (x + 0.03, top + 0.004, D / 2 + 0.010), PAINT, bevel=0.002))
    o.append(gbox("lid_edge", (-W / 2 - 0.008, Y1, D / 2 - 0.004), (W / 2 + 0.008, Y1 + 0.020, D / 2 + 0.008), PAINT, bevel=0.002))
    # decal plates on top: stencil and brass plate
    o.append(K.quad_decal("stencil", (0.0, top + 0.0012, -0.075), (1, 0, 0), (0, 0, -1), 0.26, 0.26, "M_Decal_SafeStencil"))
    o.append(gbox("plate_bed", (-0.215, top, 0.075), (0.215, top + 0.003, 0.245), "M_Brass_Aged", bevel=0.001))
    o.append(K.quad_decal("lidplate", (0.0, top + 0.0042, 0.16), (1, 0, 0), (0, 0, -1), 0.40, 0.15, "M_Decal_ChestPlate"))
    rv = [(sx * (W / 2 - 0.045), top + 0.0, sz * 0.17 + 0.0) for sx in (-1, 1) for sz in (-1, 0.0, 1)]
    o.append(X.rivets("rv_l", [(x, top + 0.0, z) for x, _, z in rv], 0.0075, "y", mat=IRON, segs=6))
    o.append(K.frost_crust("frost_l", [((-0.41, top - 0.004, -0.21), 0.05, 0.005, "y"), ((0.38, top - 0.004, -0.22), 0.06, 0.005, "y"),
                                       ((0.0, top - 0.004, -0.250), 0.09, 0.004, "y")], seed=5, sides=6))
    # hinge leaves on the lid
    for x in (-0.30, 0.30):
        o.append(gbox(f"hl{x}", (x - 0.05, Y1 + 0.0, -ZF - 0.020), (x + 0.05, Y1 + 0.020, -ZF + 0.07), PAINT, bevel=0.002))
    return part("IA_lid", o, (0.0, Y1, -ZF))


def ring(k):
    x = RX[k]
    cz = ZF + 0.006 + 0.006 + RING_T / 2     # centre of the ring thickness (z), sits in the bezel
    o = []
    # knurled rim: 36-sided drum with alternate ridges
    prof = [(R_RIM - 0.004, -RING_T / 2), (R_RIM, -RING_T / 2 + 0.003), (R_RIM, RING_T / 2 - 0.003), (R_RIM - 0.004, RING_T / 2), (0.040, RING_T / 2),
            (0.040, -RING_T / 2)]
    o.append(glathe(f"rim{k}", prof, (x, RY, cz), axis="z", segments=36, mat="M_Steel_Dark", smooth=30))
    for j in range(18):
        a = 2 * math.pi * j / 18
        o.append(gcyl(f"kn{j}", 0.0032, RING_T - 0.006, (x + math.cos(a) * (R_RIM + 0.0008), RY + math.sin(a) * (R_RIM + 0.0008), cz - RING_T / 2 + 0.003),
                                    axis="z", verts=4, mat="M_Steel_Dark", bevel=0.0))
    o.append(K.disc_decal(f"face{k}", R_FACE, (x, RY, cz + RING_T / 2 + 0.0006), "z", "M_Decal_ChestRings", segs=36, r_in=0.040))
    return part(f"IA_ring_{k}", o, (x, RY, cz))


def main():
    X.begin()
    K.decal_alpha("M_Decal_SafeStencil", "meridian_stencil.png")
    X.decal("M_Decal_ChestRings", "chest_ring.png")
    X.decal("M_Decal_ChestPlate", "chest_plate.png")
    b = body()
    ia_lid = lid()
    rings = [ring(k) for k in range(3)]
    for k in range(2):
        mount(f"crystal_mount_{k}", (-0.14 + 0.28 * k, 0.31, 0.0))
    mount("note_mount", (0.0, 0.31, 0.15))
    mount("light_chest", (0.0, 0.44, 0.0))
    part("chest_body", [o for o in b if o is not None], (0, 0, 0))
    return ia_lid, rings


def pose(obj, ax, deg):
    X.C.pose_rot(obj, ax, deg)


if __name__ == "__main__":
    lid_o, rings = main()
    req = ["chest_body", "IA_lid", "IA_ring_0", "IA_ring_1", "IA_ring_2", "crystal_mount_0", "crystal_mount_1", "note_mount", "light_chest"]
    ex = {"IA_lid": (0.0, Y1, -ZF)}
    for k in range(3):
        ex[f"IA_ring_{k}"] = (RX[k], RY, ZF + 0.012 + RING_T / 2)
    errs = X.finish(NAME, req, ["IA_lid"] + [f"IA_ring_{k}" for k in range(3)], BUDGET, ex, show=["IA_lid", "IA_ring_1"])
    if X.want_render(ARGS):
        K.fix_pbr()
        COLD = [((1.0, 1.6, 1.4), 520, "D8EAFF", 0.4), ((-1.4, 0.9, 1.2), 260, "FFE9CC", 0.6), ((0.0, 1.8, -0.8), 300, "BFD8FF", 0.5)]
        X.qa_props(NAME, [("_closed", (0.55, 1.05, 1.55), (0.0, 0.32, 0.0), 38)], floor=True, world=0.4, lights=COLD)
        pose(lid_o, "x", -105.0)
        pose(rings[0], "z", 60.0 * 2)
        pose(rings[1], "z", 60.0 * 5)
        X.qa_props(NAME, [("_open", (0.35, 1.25, 1.35), (0.0, 0.34, 0.0), 40)], floor=True, world=0.4, lights=COLD)
