"""book_lift_cage.glb — the wooden goods ("book") lift cage, floors -1 / 0 / +1 (puzzle N7 counterweight; Stage B).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §3/§7/§8 N7. A walnut-framed cage 1.30 w x 1.15 d x 2.05 h with brass-wire
lattice upper sides, panelled lower sides and floor, a scissor lattice gate on the front, a roof eye with two cables, a
cream enamel control plate inside the back wall (three brass push buttons with pictograms: flask, book, lamp), a "LOAD" plate
and, outside on the right, a horizontal counterweight rod with four weight stations where the cast weights hang.

Model space (Godot): front (the gate) +Z, origin on the cage floor at the centre.
Placement suggestion: inside the lift niche of the Pump Room, (-4.40, 0, -1.50), yaw +90 (front faces world +X, into the room).

Parts (own objects, origin at the pivot, identity rotation at rest):
  cage_body       frame, panels, lattice, floor, roof, cables, rod bracket, control plate (static)
  IA_gate         the scissor gate, pivot at its centre (0, 0.98, 0.585); slide along local X: closed = 0, open = -0.62
  IA_btn_flask / IA_btn_book / IA_btn_lamp   push buttons at (-0.10 / 0.15 / 0.40, 1.28, -0.545); press = -0.006 along local Z
  IA_hook         the counterweight rod + hook plate, pivot at (0.705, 1.30, 0.0)
  load_plate      enamel quad (M_Decal_LiftPlate, UV 0..1) on the back wall at (-0.30, 1.28, -0.549), 0.20 x 0.10
  load_mount      empty on the load plate (identity) where the code puts the number (Label3D or digit quad)
  hook_mount_0..3 empties at (0.74, 1.30, -0.36 / -0.12 / +0.12 / +0.36): the ring top of a hung weight sits here (identity rotation)
    blender -b --factory-startup -P tools/blender/models/book_lift_cage.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part, mount, gquad  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "book_lift_cage"
BUDGET = 9000
ARGS = M.main_guard()
HW, HD, H = 0.65, 0.575, 2.05
WAL, PAN, BR = "M_Wood_Walnut", "M_Wood_Panel", "M_Brass_Aged"
BTN = {"flask": -0.10, "book": 0.15, "lamp": 0.40}


def pictogram(kind, x, y, z):
    o = []
    if kind == "flask":
        o.append(X.gpoly("flask", [(-0.011, -0.012), (0.011, -0.012), (0.004, 0.004), (0.004, 0.014), (-0.004, 0.014), (-0.004, 0.004)],
                         0.0012, X.C.gframe((x, y, z), (1, 0, 0), (0, 1, 0)), mat="M_Lacquer_Black", bevel=0.0))
    elif kind == "book":
        o.append(X.gpoly("book", [(-0.013, -0.009), (0.0, -0.006), (0.013, -0.009), (0.013, 0.010), (0.0, 0.013), (-0.013, 0.010)],
                         0.0012, X.C.gframe((x, y, z), (1, 0, 0), (0, 1, 0)), mat="M_Lacquer_Black", bevel=0.0))
    else:
        o.append(X.gpoly("lamp", [(-0.003, -0.013), (0.003, -0.013), (0.003, -0.003), (0.011, 0.004), (0.0, 0.014), (-0.011, 0.004),
                                  (-0.003, -0.003)], 0.0012, X.C.gframe((x, y, z), (1, 0, 0), (0, 1, 0)), mat="M_Lacquer_Black", bevel=0.0))
    return o


def build():
    X.begin()
    b = []
    # floor + kick boards
    b.append(gbox("floor", (-HW, 0.04, -HD), (HW, 0.09, HD), PAN, bevel=0.002))
    b.append(gbox("floor_edge", (-HW - 0.01, 0.0, -HD - 0.01), (HW + 0.01, 0.05, HD + 0.01), BR, bevel=0.003))
    b.append(gbox("roof", (-HW, H - 0.07, -HD), (HW, H, HD), WAL, bevel=0.004))
    b.append(gbox("roof_cap", (-HW - 0.02, H - 0.02, -HD - 0.02), (HW + 0.02, H + 0.015, HD + 0.02), BR, bevel=0.003))
    # corner posts
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.append(gbox("post", (sx * HW - 0.035 * (1 if sx < 0 else -1) - 0.035, 0.0, sz * HD - 0.035),
                          (sx * HW - 0.035 * (1 if sx < 0 else -1) + 0.035, H, sz * HD + 0.035), WAL, bevel=0.004))
    # sides and back: wainscot panels to 0.90, mid rail, brass rod lattice above
    for nm, a0, a1, fixed, along in (("back", -HW, HW, -HD, "x"), ("left", -HD, HD, -HW, "z"), ("right", -HD, HD, HW, "z")):
        def bx(lo, hi, y0, y1, th=0.03, c=0.0):
            if along == "x":
                return gbox(nm, (lo, y0, fixed - th / 2 + c), (hi, y1, fixed + th / 2 + c), PAN, bevel=0.003)
            return gbox(nm, (fixed - th / 2 + c, y0, lo), (fixed + th / 2 + c, y1, hi), PAN, bevel=0.003)
        b.append(bx(a0 + 0.07, a1 - 0.07, 0.09, 0.90, 0.032))
        b.append(bx(a0 + 0.07, a1 - 0.07, 0.90, 0.95, 0.05))
        b.append(bx(a0 + 0.07, a1 - 0.07, H - 0.12, H - 0.07, 0.05))
        n = int((a1 - a0 - 0.14) / 0.085)
        for i in range(n + 1):
            u = a0 + 0.07 + i * (a1 - a0 - 0.14) / n
            if along == "x":
                b.append(gcyl("rod", 0.005, H - 0.12 - 0.95, (u, 0.95, fixed), axis="y", verts=6, mat=BR, bevel=0.0))
            else:
                b.append(gcyl("rod", 0.005, H - 0.12 - 0.95, (fixed, 0.95, u), axis="y", verts=6, mat=BR, bevel=0.0))
    # front frame: header and kick board; gate opening 1.18 wide
    b.append(gbox("front_head", (-HW + 0.07, H - 0.22, HD - 0.03), (HW - 0.07, H - 0.07, HD + 0.02), WAL, bevel=0.004))
    b.append(gbox("front_kick", (-HW + 0.07, 0.09, HD - 0.015), (HW - 0.07, 0.30, HD + 0.01), PAN, bevel=0.003))
    b.append(gbox("front_plate", (-0.10, H - 0.20, HD + 0.02), (0.10, H - 0.10, HD + 0.026), "M_Brass_Polished", bevel=0.001))
    b.append(X.C.gtext("front_txt", "B  -1  0  +1", 0.045, X.C.gframe((0.0, H - 0.15, HD + 0.027), (1, 0, 0), (0, 1, 0)), depth=0.0012,
                       mat="M_Lacquer_Black", resolution=1))
    # roof eye, two cables to the shaft top
    for sx in (-1, 1):
        b.append(gcyl("cable", 0.012, 1.4, (sx * 0.30, H + 0.015, 0.0), axis="y", verts=8, mat="M_Steel_Dark", bevel=0.0))
        b.append(gcyl("cable_thimble", 0.026, 0.05, (sx * 0.30, H + 0.015, 0.0), axis="y", verts=10, mat=BR, bevel=0.001))
    # control plate on the back wall (cream enamel) with the load plate and the three buttons
    b.append(gbox("ctl_plate", (-0.45, 1.15, -HD + 0.016), (0.55, 1.42, -HD + 0.026), "M_Steel_Cream", bevel=0.003))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.append(X.rivets("crv", [(0.05 + sx * 0.49, 1.285 + sy * 0.12, -HD + 0.026)], 0.0045, "z", mat=BR, segs=6))
    for kind, x in BTN.items():
        b.append(glathe(f"btn_ring_{kind}", [(0.0, 0.0), (0.030, 0.0), (0.030, 0.006), (0.024, 0.009), (0.0, 0.009)],
                        (x, 1.28, -HD + 0.026), axis="z", segments=16, mat=BR))
        b += pictogram(kind, x, 1.215, -HD + 0.0265)
    # gauge on the plate (floor indicator)
    gb, nd = X.gauge("lift_gauge", (-0.34, 1.28, -HD + 0.026), r=0.040, axis="z")
    b.append(gb)
    nd.name = "needle_lift"
    # counterweight rod bracket on the right side (outside): plate on the post, projecting rod along Z with end cap
    b.append(gbox("rod_plate", (HW + 0.0, 1.10, -0.50), (HW + 0.035, 1.50, 0.50), "M_Iron_Rust", bevel=0.004))
    for z in (-0.38, 0.38):
        b.append(gbox(f"rod_arm{z}", (HW + 0.03, 1.27, z - 0.02), (HW + 0.10, 1.33, z + 0.02), "M_Iron_Rust", bevel=0.003))
    # gate (IA): scissor lattice made of diagonal flat bars between two vertical stiles, brass finish
    gate = []
    gx0, gx1, gy0, gy1 = -0.58, 0.58, 0.10, 1.86
    gate.append(gbox("g_top", (gx0, gy1 - 0.04, HD - 0.02), (gx1, gy1, HD + 0.01), BR, bevel=0.002))
    gate.append(gbox("g_bot", (gx0, gy0, HD - 0.02), (gx1, gy0 + 0.04, HD + 0.01), BR, bevel=0.002))
    gate.append(gbox("g_l", (gx0, gy0, HD - 0.02), (gx0 + 0.04, gy1, HD + 0.01), BR, bevel=0.002))
    gate.append(gbox("g_r", (gx1 - 0.04, gy0, HD - 0.02), (gx1, gy1, HD + 0.01), BR, bevel=0.002))
    cols, rows = 6, 8
    cw = (gx1 - gx0) / cols
    rh = (gy1 - gy0) / rows
    # lattice as thin diagonal bars (rotated boxes)
    for r in range(rows):
        for c in range(cols):
            x0, y0 = gx0 + c * cw, gy0 + r * rh
            ln = math.hypot(cw, rh) * 0.93
            ang = math.atan2(rh, cw) * (1 if (r + c) % 2 == 0 else -1)
            bar = M.box("gdb", (ln, 0.008, 0.010), loc=G(x0 + cw / 2, y0 + rh / 2, HD - 0.004), rot=(0, -ang, 0), mat="M_Steel_Dark",
                        bevel=0.0, segments=1)
            gate.append(bar)
    ia_gate = part("IA_gate", gate, (0.0, 0.98, HD + 0.01))
    # buttons (IA)
    btns = {}
    for kind, x in BTN.items():
        o = glathe(f"btn_{kind}", [(0.0, 0.0), (0.020, 0.0), (0.022, 0.008), (0.018, 0.013), (0.0, 0.014)], (x, 1.28, -HD + 0.036),
                   axis="z", segments=14, mat="M_Enamel_Cream" if kind != "lamp" else "M_Enamel_Amber")
        btns[kind] = part(f"IA_btn_{kind}", [o], (x, 1.28, -HD + 0.036))
    # load plate + mount
    X.decal("M_Decal_LiftPlate", "lift_plate.png")
    lp = gquad("load_plate", (-0.185, 1.30, -HD + 0.0265), (1, 0, 0), (0, 1, 0), 0.20, 0.10, "M_Decal_LiftPlate")
    # (the gauge sits at -0.34; the plate moved to x -0.185 so both fit on the control plate)
    mount("load_mount", (-0.185, 1.30, -HD + 0.0275))
    # hook: rod + end cap + hook plate
    hook = [gcyl("rod", 0.014, 1.04, (HW + 0.105, 1.30, -0.52), axis="z", verts=10, mat="M_Steel_Dark", bevel=0.0),
            gcyl("rod_cap", 0.026, 0.020, (HW + 0.105, 1.30, 0.52), axis="z", verts=10, mat=BR, bevel=0.001)]
    for z in (-0.36, -0.12, 0.12, 0.36):
        hook.append(gcyl("station", 0.020, 0.006, (HW + 0.105, 1.30, z - 0.003), axis="z", verts=10, mat=BR, bevel=0.0))
    ia_hook = part("IA_hook", hook, (HW + 0.055, 1.30, 0.0))
    for i, z in enumerate((-0.36, -0.12, 0.12, 0.36)):
        mount(f"hook_mount_{i}", (HW + 0.105, 1.30 - 0.014, z))
    X.top(b)
    part("cage_body", b, (0, 0, 0))
    return ia_gate


def main():
    build()
    req = ["cage_body", "IA_gate", "IA_btn_flask", "IA_btn_book", "IA_btn_lamp", "IA_hook", "load_plate", "load_mount", "needle_lift",
           "hook_mount_0", "hook_mount_3"]
    expect = {"IA_gate": (0.0, 0.98, HD + 0.01), "IA_btn_flask": (-0.10, 1.28, -HD + 0.036), "IA_btn_book": (0.15, 1.28, -HD + 0.036),
              "IA_btn_lamp": (0.40, 1.28, -HD + 0.036)}
    errs = X.finish(NAME, req, [r for r in req if r != "load_plate"], BUDGET, expect, show=req[:6])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (2.4, 1.7, 3.0), (0.0, 0.95, 0.0), 48), ("_in", (0.2, 1.4, 1.6), (0.1, 1.2, -0.5), 55)], floor=True, world=0.15)


main()
