"""cold_door.glb — the insulated door between the Night Cell and the Cold Store (puzzles N2 thaw + N3 digits).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §3, §3b: "a frozen insulated door with a wheel lock and a coil"). A galvanised cold-room door,
0.836 x 2.06 x 0.11, in a steel-lined 0.25 m wall opening: pressed panel skin with rivet rows, a frosted porthole in a brass ring, a snowflake
enamel plate (a pictogram, no text), a rubber kick plate, two cast hinge straps, a vertical cam lever and a two-wheel digit lock
(two brass thumb-drums with the numerals 0-9 behind small windows, a lock lamp). Beside the frame a thermal plate carries a serpentine copper
heating coil (fed from above, ends at the cell ceiling y 2.70); glowing bands sit on the coil runs. Frost and icicles (`door_ice`) crust the
seam while the door is frozen.

Model space (Godot): origin at the centre of the opening, on the floor, on the ROOM-side (cell-side) wall plane; the wall occupies local z in
[-0.25, 0]; front +Z faces the cell. Opening 0.90 wide x 2.10 high (x -0.45..0.45). Placement in `room_cell`: (2.20, 0, 0.0), yaw -90 (the
east wall; local +Z then faces -X into the room, local +X points to world -Z... see docs/models/ch2_exp.md).

Parts:
  cold_door_frame   static: liner, architrave, stop with gasket, hinge knuckles, thermal plate and coil, feed pipe, threshold
  IA_cold_door      the leaf, origin = hinge axis at floor level (-0.44, 0, 0.0); opens toward the viewer with a NEGATIVE angle about +Y (-100 deg)
  IA_cold_handle    child of the leaf: vertical cam lever, pivot (0.335, 0.86, 0.040); rest = pointing up (locked), release = -90 deg about +Z (points right)
  IA_wheel_a        child of the leaf: left digit drum, pivot (0.245, 1.28, 0.012); digit k in front = rotate +36 deg * k about +X (digit k+1 sits above k)
  IA_wheel_b        child of the leaf: right digit drum, pivot (0.325, 1.28, 0.012), same convention
  lock_lamp         child of the leaf: jewel (M_Emissive_Red) at (0.285, 1.375, 0.056); the code changes its emission/colour
  coil_glow         static: glowing bands on the coil runs (M_Emissive_Warm), origin (-0.70, 1.10, 0.030); show while the pipes are hot
  door_ice          static: frost lumps on the seam and icicles under the head (M_Frost), origin (0, 1.05, 0.02); hide when thawed
  coil_mount        empty at the top of the coil feed (-0.70, 2.70, 0.03): the pipe from the ceiling attaches here (optional steam / drip fx)
  light_cold_door   empty (0.0, 2.0, 0.35): a cold fill light in front of the door

    blender -b --factory-startup -P tools/blender/models/cold_door.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, gtext, part, mount  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "cold_door"
BUDGET = 9000
ARGS = M.main_guard()
GALV, DARK, BRASS = "M_Steel_Galv", "M_Steel_Dark", "M_Brass_Aged"
HX = -0.44                       # hinge axis x
LX0, LX1, LY0, LY1, LZ0, LZ1 = -0.418, 0.418, 0.015, 2.075, -0.115, -0.005    # leaf box
WY = 1.28                        # lock height
WXA, WXB, WZ = 0.245, 0.325, 0.012
WR, WW = 0.040, 0.034           # drum radius / width


def frame():
    o = []
    # liner inside the wall opening (jambs + head), full wall depth
    o.append(gbox("liner_l", (-0.45, 0.0, -0.25), (-0.43, 2.10, 0.0), GALV, bevel=0.0))
    o.append(gbox("liner_r", (0.43, 0.0, -0.25), (0.45, 2.10, 0.0), GALV, bevel=0.0))
    o.append(gbox("liner_h", (-0.45, 2.08, -0.25), (0.45, 2.10, 0.0), GALV, bevel=0.0))
    # architrave (proud 12 mm on the cell side): steel flat bars with a rounded edge
    o.append(gbox("arch_l", (-0.585, 0.0, 0.0), (-0.45, 2.235, 0.014), GALV, bevel=0.004))
    o.append(gbox("arch_r", (0.45, 0.0, 0.0), (0.585, 2.235, 0.014), GALV, bevel=0.004))
    o.append(gbox("arch_h", (-0.45, 2.10, 0.0), (0.45, 2.235, 0.014), GALV, bevel=0.004))
    o.append(gbox("sill", (-0.60, 0.0, -0.25), (0.60, 0.02, 0.10), "M_Chequer", bevel=0.003))
    # stop with the black gasket (leaf closes against it), behind the leaf
    for nm, mn, mx in (("stop_l", (-0.43, 0.0, -0.135), (-0.40, 2.08, -0.115)), ("stop_r", (0.40, 0.0, -0.135), (0.43, 2.08, -0.115)),
                       ("stop_h", (-0.40, 2.05, -0.135), (0.40, 2.08, -0.115))):
        o.append(gbox(nm, mn, mx, DARK, bevel=0.0))
    for nm, mn, mx in (("gk_l", (-0.425, 0.0, -0.121), (-0.405, 2.07, -0.116)), ("gk_r", (0.405, 0.0, -0.121), (0.425, 2.07, -0.116)),
                       ("gk_h", (-0.405, 2.05, -0.121), (0.405, 2.07, -0.116))):
        o.append(gbox(nm, mn, mx, "M_Rubber", bevel=0.0))
    # hinge knuckles on the frame (two heavy barrels) with pins
    for y in (0.32, 1.78):
        o.append(gcyl(f"knuckle{y}", 0.024, 0.16, (HX - 0.004, y - 0.08, 0.0), axis="y", verts=12, mat=DARK, bevel=0.002))
        o.append(gbox(f"kn_blk{y}", (HX - 0.045, y - 0.08, -0.016), (HX - 0.004, y + 0.08, 0.014), DARK, bevel=0.003))
    # latch keeper on the right jamb
    o.append(gbox("keeper", (0.43, 0.82, -0.065), (0.47, 0.90, -0.045), DARK, bevel=0.003))
    # thermal plate with the serpentine heating coil on the wall left of the frame (x -0.88 .. -0.62)
    o.append(gbox("coil_plate", (-0.90, 0.30, 0.0), (-0.60, 1.95, 0.012), GALV, bevel=0.004))
    for y in (0.34, 1.91):
        for x in (-0.87, -0.63):
            o.append(gcyl(f"cp_bolt{x}{y}", 0.007, 0.006, (x, y, 0.012), axis="z", verts=6, mat=DARK, bevel=0.0))
    xs = [-0.84, -0.775, -0.71, -0.645]
    pts = []
    for i, x in enumerate(xs):
        y_a, y_b = (0.42, 1.82)
        if i % 2 == 0:
            pts += [(x, y_a, 0.030), (x, y_b, 0.030)]
        else:
            pts += [(x, y_b, 0.030), (x, y_a, 0.030)]
    o.append(X.pipe("coil", pts, 0.013, mat="M_Copper", sides=8, fillet=0.03, flange_ends=False))
    for x, y in zip(xs, [0.42, 1.82, 0.42, 1.82]):                    # pipe clips
        pass
    for y in (0.62, 1.12, 1.62):
        for x in xs:
            o.append(gbox(f"clip{x}{y}", (x - 0.016, y - 0.007, 0.020), (x + 0.016, y + 0.007, 0.034), DARK, bevel=0.0015))
    # feed from the ceiling down to the first run, and the return into the floor
    o.append(X.pipe("feed", [(-0.84, 1.82, 0.030), (-0.84, 1.95, 0.030), (-0.84, 2.70, 0.030)], 0.020, mat="M_Copper", sides=10, fillet=0.0, flange_ends=True,
                    flange_r=0.03, bolts=4, flange_mat=DARK))
    o.append(X.pipe("return", [(-0.645, 0.42, 0.030), (-0.645, 0.20, 0.030), (-0.645, 0.0, 0.030)], 0.013, mat="M_Copper", sides=8, flange_ends=False))
    o.append(gbox("valve_blk", (-0.885, 2.20, 0.006), (-0.795, 2.28, 0.054), DARK, bevel=0.003))
    return o


def leaf():
    o = []
    o.append(gbox("skin", (LX0, LY0, LZ0), (LX1, LY1, LZ1), GALV, bevel=0.012, seg=2))
    # pressed panel: a raised rectangle with a bevelled frame (front only)
    o.append(gbox("panel", (LX0 + 0.06, LY0 + 0.24, LZ1), (LX1 - 0.06, LY1 - 0.07, LZ1 + 0.010), GALV, bevel=0.005, seg=2))
    o.append(gbox("kick", (LX0 + 0.012, LY0, LZ1 - 0.001), (LX1 - 0.012, LY0 + 0.20, LZ1 + 0.008), "M_Rubber", bevel=0.003))
    for x in (-0.30, -0.10, 0.10, 0.30):
        o.append(gbox(f"kick_rib{x}", (x - 0.012, LY0 + 0.02, LZ1 + 0.008), (x + 0.012, LY0 + 0.18, LZ1 + 0.011), DARK, bevel=0.0))
    # porthole: brass ring + frosted glass (looks into the cold)
    pc = (0.0, 1.70, LZ1 + 0.010)
    o.append(glathe("port_ring", [(0.060, 0.0), (0.095, 0.0), (0.095, 0.020), (0.088, 0.027), (0.062, 0.027), (0.060, 0.020)], pc, axis="z", segments=24, mat=BRASS))
    o.append(glathe("port_glass", [(0.0, 0.016), (0.062, 0.016), (0.062, 0.020), (0.0, 0.020)], pc, axis="z", segments=24, mat="M_Glass_Frosted"))
    for k in range(8):
        a = 2 * math.pi * k / 8
        o.append(gcyl(f"port_bolt{k}", 0.0065, 0.008, (math.cos(a) * 0.078, 1.70 + math.sin(a) * 0.078, LZ1 + 0.037), axis="z", verts=6, mat=DARK, bevel=0.0))
    # snowflake enamel plate (pictogram)
    sc = (-0.16, WY, LZ1 + 0.010)
    o.append(gbox("snow_plate", (sc[0] - 0.075, sc[1] - 0.075, LZ1 + 0.010), (sc[0] + 0.075, sc[1] + 0.075, LZ1 + 0.016), "M_Enamel_Cobalt", bevel=0.004))
    return o


def leaf_flake(sc):
    """Snowflake: three bars crossing at 60 deg plus two barbs per arm, extruded in the Godot XY plane at z = sc[2]."""
    o = []
    fr = X.C.gframe((sc[0], sc[1], sc[2]), (1, 0, 0), (0, 1, 0))

    def bar(nm, cx, cy, ln, w, a):
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        pts = [(cx - ux * ln / 2 - vx * w / 2, cy - uy * ln / 2 - vy * w / 2), (cx + ux * ln / 2 - vx * w / 2, cy + uy * ln / 2 - vy * w / 2),
               (cx + ux * ln / 2 + vx * w / 2, cy + uy * ln / 2 + vy * w / 2), (cx - ux * ln / 2 + vx * w / 2, cy - uy * ln / 2 + vy * w / 2)]
        return X.C.gpoly(nm, pts, 0.002, fr, mat="M_Enamel_White", bevel=0.0)

    for k in range(3):
        a = k * math.pi / 3
        o.append(bar(f"snowbar{k}", 0.0, 0.0, 0.118, 0.0085, a))
    for k in range(6):                                                  # barbs: 2 per arm, at +-60 deg
        a = k * math.pi / 3
        for t, sgn in ((0.032, 1), (0.032, -1)):
            cx, cy = math.cos(a) * 0.036, math.sin(a) * 0.036
            o.append(bar(f"barb{k}{sgn}", cx, cy, 0.030, 0.006, a + sgn * math.pi / 3))
    return o


def leaf_hardware():
    o = []
    # two cast hinge straps from the knuckles across the front face
    for y in (0.32, 1.78):
        o.append(gbox(f"strap{y}", (HX - 0.004, y - 0.055, LZ1 - 0.002), (-0.05, y + 0.055, LZ1 + 0.012), DARK, bevel=0.004))
        o.append(gcyl(f"strap_eye{y}", 0.024, 0.11, (HX, y - 0.055, 0.0 - 0.0), axis="y", verts=12, mat=DARK, bevel=0.002))
        for x in (-0.30, -0.16, -0.06):
            o.append(gcyl(f"strap_bolt{y}{x}", 0.009, 0.007, (x, y, LZ1 + 0.012), axis="z", verts=6, mat=BRASS, bevel=0.0))
    # rivet rows on the panel border
    pts = []
    for x in [LX0 + 0.09 + i * 0.18 for i in range(5)]:
        pts += [(x, LY0 + 0.265, LZ1 + 0.010), (x, LY1 - 0.095, LZ1 + 0.010)]
    for y in [LY0 + 0.36 + i * 0.44 for i in range(4)]:
        pts += [(LX0 + 0.085, y, LZ1 + 0.010), (LX1 - 0.085, y, LZ1 + 0.010)]
    r = X.rivets("lrv", pts, 0.0065, "z", mat=GALV, segs=5)
    if r:
        o.append(r)
    # lock housing: back, sides and the front frame with two windows
    hx0, hx1, hy0, hy1 = 0.195, 0.375, WY - 0.060, WY + 0.062
    zf = LZ1 + 0.060
    o.append(gbox("lk_back", (hx0, hy0, LZ1 + 0.008), (hx1, hy1, LZ1 + 0.018), DARK, bevel=0.002))
    o.append(gbox("lk_top", (hx0, hy1 - 0.008, LZ1 + 0.008), (hx1, hy1, zf), DARK, bevel=0.002))
    o.append(gbox("lk_bot", (hx0, hy0, LZ1 + 0.008), (hx1, hy0 + 0.008, zf), DARK, bevel=0.002))
    o.append(gbox("lk_l", (hx0, hy0, LZ1 + 0.008), (hx0 + 0.008, hy1, zf), DARK, bevel=0.002))
    o.append(gbox("lk_r", (hx1 - 0.008, hy0, LZ1 + 0.008), (hx1, hy1, zf), DARK, bevel=0.002))
    wx = ((WXA - 0.021, WXA + 0.021), (WXB - 0.021, WXB + 0.021))
    o.append(gbox("lk_fr_t", (hx0, WY + 0.026, zf - 0.010), (hx1, hy1, zf), BRASS, bevel=0.002))
    o.append(gbox("lk_fr_b", (hx0, hy0, zf - 0.010), (hx1, WY - 0.026, zf), BRASS, bevel=0.002))
    o.append(gbox("lk_fr_l", (hx0, WY - 0.026, zf - 0.010), (wx[0][0], WY + 0.026, zf), BRASS, bevel=0.002))
    o.append(gbox("lk_fr_m", (wx[0][1], WY - 0.026, zf - 0.010), (wx[1][0], WY + 0.026, zf), BRASS, bevel=0.002))
    o.append(gbox("lk_fr_r", (wx[1][1], WY - 0.026, zf - 0.010), (hx1, WY + 0.026, zf), BRASS, bevel=0.002))
    # little index ticks above the windows
    for x in (WXA, WXB):
        o.append(gbox(f"idx{x}", (x - 0.0015, WY + 0.0275, zf - 0.0004), (x + 0.0015, WY + 0.040, zf + 0.0006), "M_Lacquer_Black", bevel=0.0))
    return o, zf


def drum(x, name):
    o = [gcyl(name + "_core", WR, WW, (x - WW / 2, WY, WZ), axis="x", verts=20, mat="M_Brass_Polished", bevel=0.0015)]
    for sx in (-1, 1):                                        # raised side flanges
        o.append(gcyl(f"{name}_fl{sx}", WR * 0.82, 0.003, (x + sx * (WW / 2 + 0.0015) - 0.0015, WY, WZ), axis="x", verts=20, mat=DARK, bevel=0.0))
    for d in range(10):                                       # numerals: digit d at +36 deg * d, upright, facing outward
        th = math.radians(36.0 * d)
        org = (x, WY + WR * math.sin(th) * 1.0, WZ + WR * math.cos(th))
        ex, ey = (1, 0, 0), (0, math.cos(th), -math.sin(th))
        o.append(gtext(f"{name}_n{d}", str(d), 0.022, X.C.gframe(org, ex, ey), depth=0.0012, font=X.FONT, mat="M_Lacquer_Black", resolution=1))
    return part(name, o, (x, WY, WZ))


def handle():
    piv = (0.335, 0.86, LZ1 + 0.035)
    o = [gcyl("hd_hub", 0.022, 0.030, (piv[0], piv[1], LZ1 + 0.0), axis="z", verts=16, mat=DARK, bevel=0.003),
         gcyl("hd_cap", 0.014, 0.014, (piv[0], piv[1], LZ1 + 0.030), axis="z", verts=12, mat="M_Chrome", bevel=0.002),
         gbox("hd_bar", (piv[0] - 0.011, piv[1] - 0.030, LZ1 + 0.022), (piv[0] + 0.011, piv[1] + 0.190, LZ1 + 0.044), "M_Chrome", bevel=0.005, seg=2),
         gcyl("hd_ball", 0.020, 0.040, (piv[0], piv[1] + 0.170, LZ1 + 0.018), axis="z", verts=14, mat=BAKE_MAT, bevel=0.004, r_top=0.017)]
    return part("IA_cold_handle", o, piv)


BAKE_MAT = "M_Bakelite"


def lamp(zf):
    j = glathe("lamp_j", [(0.0, 0.0), (0.0095, 0.0), (0.010, 0.003), (0.007, 0.008), (0.0, 0.009)], (0.285, WY + 0.0955 - 0.02, LZ1 + 0.018), axis="z", segments=12,
               mat="M_Emissive_Red")
    ring = glathe("lamp_r", [(0.0095, 0.0), (0.0135, 0.0), (0.0135, 0.004), (0.0095, 0.004)], (0.285, WY + 0.0955 - 0.02, LZ1 + 0.018), axis="z", segments=12,
                  mat="M_Chrome")
    return j, ring


def ice():
    o = []
    rnd = [0.37, 0.81, 0.12, 0.66, 0.94, 0.28, 0.55, 0.73, 0.19, 0.48, 0.88, 0.05]
    # lumps along the bottom seam and both sides of the leaf, frosted rims at the head
    for i in range(12):
        x = -0.40 + 0.073 * i
        r = 0.032 + 0.020 * rnd[i]
        o.append(Q.gsphere(f"ice_b{i}", r, (x, 0.04 + 0.01 * rnd[(i + 3) % 12], 0.006), (1.0, 0.6, 0.45), mat="M_Frost", segs=6, rings=4))
    for i in range(9):
        y = 0.35 + 0.19 * i
        r = 0.020 + 0.014 * rnd[(i + 5) % 12]
        o.append(Q.gsphere(f"ice_l{i}", r, (-0.446 + 0.0, y, 0.008), (0.5, 1.2, 0.7), mat="M_Frost", segs=6, rings=4))
        o.append(Q.gsphere(f"ice_r{i}", r, (0.446, y + 0.05, 0.008), (0.5, 1.2, 0.7), mat="M_Frost", segs=6, rings=4))
    for i in range(10):                                        # icicles hanging from the head
        x = -0.38 + 0.085 * i
        h = 0.07 + 0.09 * rnd[(i * 5) % 12]
        o.append(gcyl(f"icicle{i}", 0.012 + 0.006 * rnd[i], h, (x, 2.10 - h, 0.010), axis="y", verts=6, mat="M_Frost", bevel=0.0, r_top=0.002))
    o.append(gbox("ice_head", (-0.42, 2.075, 0.0), (0.42, 2.105, 0.020), "M_Frost", bevel=0.006))
    return o


def glow():
    o = []
    xs = [-0.84, -0.775, -0.71, -0.645]
    for i, x in enumerate(xs):
        for y in (0.60, 0.95, 1.30, 1.65):
            o.append(gcyl(f"gb{i}{y}", 0.0155, 0.040, (x, y, 0.030), axis="y", verts=8, mat="M_Emissive_Warm", bevel=0.0))
    return o


def build():
    X.begin()
    fr = frame()
    X.top(fr)
    lf = leaf()
    # the snowflake bars (in the XY plane)
    sc = (-0.16, WY, LZ1 + 0.0175)
    lf += leaf_flake(sc)
    hw, zf = leaf_hardware()
    lf += hw
    wa = drum(WXA, "IA_wheel_a")
    wb = drum(WXB, "IA_wheel_b")
    hd = handle()
    j, ring = lamp(zf)
    lamp_part = part("lock_lamp", [j], (0.285, WY + 0.0755, LZ1 + 0.018), presmooth=False)
    lf.append(ring)
    leaf_part = part("IA_cold_door", lf, (HX, 0.0, 0.0))
    for ch in (wa, wb, hd, lamp_part):
        X.C.parent(ch, leaf_part)
    ic = part("door_ice", ice(), (0.0, 1.05, 0.02), presmooth=False)
    cg = part("coil_glow", glow(), (-0.70, 1.10, 0.030), presmooth=False)
    mount("coil_mount", (-0.84, 2.70, 0.03))
    mount("light_cold_door", (0.0, 2.0, 0.35))
    part("cold_door_frame", fr, (0, 0, 0))
    return leaf_part


if __name__ == "__main__":
    build()
    req = ["cold_door_frame", "IA_cold_door", "IA_cold_handle", "IA_wheel_a", "IA_wheel_b", "lock_lamp", "coil_glow", "door_ice", "coil_mount", "light_cold_door"]
    errs = X.finish(NAME, req, ["IA_cold_door", "IA_cold_handle", "IA_wheel_a", "IA_wheel_b", "lock_lamp"], BUDGET,
                    {"IA_cold_door": (HX, 0.0, 0.0), "IA_wheel_a": (WXA, WY, WZ), "IA_wheel_b": (WXB, WY, WZ), "IA_cold_handle": (0.335, 0.86, LZ1 + 0.035)}, show=req)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.9, 1.5, 3.1), (-0.1, 1.15, 0.0), 44), ("_lock", (0.25, 1.28, 0.62), (0.28, 1.15, 0.0), 30), ("_coil", (-1.5, 1.4, 1.6), (-0.7, 1.2, 0.0), 40)],
                   floor=True, world=0.2)
