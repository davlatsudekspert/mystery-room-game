"""strand_cabinet.glb — Strand's lamp cabinet in the Director's Office (R7, puzzle N10: four digit wheels; reward: the spare projector lamp).

A tall mahogany cabinet with a dentil cornice: a double-door upper case (raised panels, brass pulls) with a brass lock plate in the
fixed transom band above the doors carrying FOUR digit wheels (the same 10-digit wheels as the Chapter 1 drawer), a brass card-holder beside the lock with
the label quad (the symbol the Plate Room negatives are matched with), a lower block of two drawers (decoration), a plinth. The case
is hollow behind the doors: a velvet-lined shelf holds the lamp at `lamp_mount`.

Model space (Godot): origin on the floor at the footprint centre, front +Z. Size 1.04 w x 0.46 d x 1.92 h (x +-0.52, z -0.23 .. 0.23).
Suggested placement: against the east wall of the office (2.9 - 0.23, 0, 0.3) ... see room_office `cabinet_mount`.
Parts (origin at the pivot, identity rotation at rest):
  cabinet_body     case, drawers, plinth, cornice, lock plate, label holder, velvet shelf (static)
  IA_door_l        left door, hinge on the left edge: origin (-0.485, 1.16, 0.243); opens with a NEGATIVE angle about +Y (-100 deg, toward the viewer)
  IA_door_r        right door, hinge on the right edge: origin (0.485, 1.16, 0.243); opens with a POSITIVE angle about +Y (+100 deg)
  IA_wheel_0..3    digit wheels, x = -0.105, -0.035, +0.035, +0.105 at (x, 1.64, 0.244): axle along X, digit k faces the viewer after
                   a rotation of +36 k degrees about +X; at rest digit 0 shows. Slot M_Decal_DrawerDigits
  cabinet_label    quad (0.115 x 0.082) centre (-0.33, 1.64, 0.2742), slot M_Decal_CabinetLabel (swap the image: the variant symbol)
  empties          lamp_mount (0, 1.0, 0.0) (where the projector lamp rests, base down), light_origin_cabinet (0, 1.0, 0.30)
    blender -b --factory-startup -P tools/blender/models/strand_cabinet.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, gquad, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "strand_cabinet"
BUDGET = 12000
ARGS = M.main_guard()
MAH, BRASS = "M_Wood_Mahogany", "M_Brass_Aged"
W, D, HT = 1.04, 0.46, 1.92
X0, X1, Z0, Z1 = -W / 2, W / 2, -D / 2, D / 2
DY0, DY1 = 0.82, 1.50                 # door opening (y); the transom band 1.50..1.80 above it is fixed (lock + label)
WX = [-0.105, -0.035, 0.035, 0.105]
WY, WZ, WR = 1.64, 0.244, 0.034


def build():
    X.begin()
    b = []
    # plinth + carcass (open front for the upper case: sides, back, top, bottom, shelf)
    b.append(gbox("plinth", (X0 - 0.015, 0.0, Z0 - 0.015), (X1 + 0.015, 0.09, Z1 + 0.015), MAH, bevel=0.008, seg=2))
    b.append(gbox("plinth_top", (X0 - 0.005, 0.09, Z0 - 0.005), (X1 + 0.005, 0.105, Z1 + 0.005), MAH, bevel=0.006))
    t = 0.025
    b.append(gbox("side_l", (X0, 0.105, Z0), (X0 + t, HT - 0.12, Z1), MAH, bevel=0.004))
    b.append(gbox("side_r", (X1 - t, 0.105, Z0), (X1, HT - 0.12, Z1), MAH, bevel=0.004))
    b.append(gbox("back", (X0 + t, 0.105, Z0), (X1 - t, HT - 0.12, Z0 + 0.02), "M_Wood_Panel", bevel=0.0))
    b.append(gbox("top_in", (X0 + t, DY1, Z0 + 0.02), (X1 - t, DY1 + 0.025, Z1 - 0.025), MAH, bevel=0.0))
    b.append(gbox("floor_in", (X0 + t, DY0 - 0.02, Z0 + 0.02), (X1 - t, DY0, Z1 - 0.02), MAH, bevel=0.0))
    # velvet shelf (the lamp rests here) with a cradle ring
    b.append(gbox("shelf", (X0 + t, 0.92, Z0 + 0.02), (X1 - t, 0.945, Z1 - 0.06), "M_Wood_Panel", bevel=0.0))
    b.append(gbox("velvet", (-0.14, 0.945, -0.10), (0.14, 0.952, 0.10), "M_Velvet", bevel=0.001))
    b.append(glathe("cradle", [(0.050, 0.0), (0.060, 0.0), (0.060, 0.016), (0.050, 0.016)], (0.0, 0.952, 0.0), axis="y", segments=18, mat=BRASS))
    # cornice: crown mouldings + a row of dentils on the front
    b.append(gbox("cor_a", (X0 - 0.03, HT - 0.12, Z0 - 0.03), (X1 + 0.03, HT - 0.06, Z1 + 0.03), MAH, bevel=0.007))
    b.append(gbox("cor_b", (X0 - 0.05, HT - 0.06, Z0 - 0.05), (X1 + 0.05, HT, Z1 + 0.05), MAH, bevel=0.009, seg=2))
    for i in range(23):
        x = X0 - 0.01 + i * 0.047
        b.append(gbox(f"dentil{i}", (x, HT - 0.115, Z1 + 0.03), (x + 0.026, HT - 0.075, Z1 + 0.046), MAH, bevel=0.0015))
    # mid rail + lower block with two drawers
    b.append(gbox("midrail", (X0, DY0 - 0.035, Z0), (X1, DY0, Z1 + 0.012), MAH, bevel=0.005))
    b.append(gbox("lower", (X0, 0.105, Z0), (X1, DY0 - 0.035, Z1), MAH, bevel=0.003))
    for i, (ya, yb) in enumerate(((0.14, 0.44), (0.47, 0.77))):
        b.append(gbox(f"drawer{i}", (X0 + 0.04, ya, Z1), (X1 - 0.04, yb, Z1 + 0.022), MAH, bevel=0.005, seg=2))
        b.append(gbox(f"drawer_pan{i}", (X0 + 0.09, ya + 0.04, Z1 + 0.022), (X1 - 0.09, yb - 0.04, Z1 + 0.030), MAH, bevel=0.004))
        b.append(gbox(f"pull{i}", (-0.07, (ya + yb) / 2 - 0.007, Z1 + 0.030), (0.07, (ya + yb) / 2 + 0.007, Z1 + 0.046), BRASS, bevel=0.004))
        for sx in (-1, 1):
            b.append(gcyl(f"pstud{i}{sx}", 0.006, 0.020, (sx * 0.07, (ya + yb) / 2, Z1 + 0.026), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
        b.append(gbox(f"keyhole{i}", (-0.004, (ya + yb) / 2 + 0.06, Z1 + 0.030), (0.004, (ya + yb) / 2 + 0.082, Z1 + 0.032), "M_Lacquer_Black", bevel=0.0))
    # fixed transom band above the doors: front panel with raised moulding, the lock plate with the four wheels, the label holder, a blank plaque
    b.append(gbox("transom", (X0 + t, DY1, Z1 - 0.004), (X1 - t, 1.80, Z1 + 0.026), MAH, bevel=0.004))
    b.append(gbox("transom_raise", (X0 + 0.06, DY1 + 0.03, Z1 + 0.026), (X1 - 0.06, 1.77, Z1 + 0.034), MAH, bevel=0.006, seg=2))
    py0, py1 = 1.575, 1.705
    zp = Z1 + 0.034
    lp = [gbox("lp_top", (-0.17, py1 - 0.045, zp), (0.17, py1, zp + 0.012), BRASS, bevel=0.003),
          gbox("lp_bot", (-0.17, py0, zp), (0.17, py0 + 0.045, zp + 0.012), BRASS, bevel=0.003),
          gbox("lp_l", (-0.17, py0 + 0.045, zp), (-0.138, py1 - 0.045, zp + 0.012), BRASS, bevel=0.003),
          gbox("lp_r", (0.138, py0 + 0.045, zp), (0.17, py1 - 0.045, zp + 0.012), BRASS, bevel=0.003),
          gbox("lp_back", (-0.14, py0 + 0.045, zp - 0.002), (0.14, py1 - 0.045, zp), "M_Lacquer_Black", bevel=0.0)]
    for sx in (-1, 1):
        for sy in (py0 + 0.022, py1 - 0.022):
            lp.append(gcyl(f"lp_screw{sx}{sy}", 0.005, 0.004, (sx * 0.154, sy, zp + 0.012), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    b += lp
    for xm in (-0.07, 0.0, 0.07):                      # dividers between the wheels
        b.append(gbox(f"wdiv{xm}", (xm - 0.0035, py0 + 0.045, zp), (xm + 0.0035, py1 - 0.045, zp + 0.011), BRASS, bevel=0.0))
    # label holder (left of the lock) and a blank maker's plaque (right)
    lx, ly = -0.33, 1.64
    b.append(gbox("lab_frame", (lx - 0.075, ly - 0.055, zp), (lx + 0.075, ly + 0.055, zp + 0.006), BRASS, bevel=0.003))
    b.append(gbox("lab_top", (lx - 0.075, ly + 0.047, zp + 0.006), (lx + 0.075, ly + 0.055, zp + 0.012), BRASS, bevel=0.002))
    b.append(gbox("lab_bot", (lx - 0.075, ly - 0.055, zp + 0.006), (lx + 0.075, ly - 0.047, zp + 0.012), BRASS, bevel=0.002))
    b.append(gbox("lab_l", (lx - 0.075, ly - 0.047, zp + 0.006), (lx - 0.067, ly + 0.047, zp + 0.012), BRASS, bevel=0.002))
    b.append(gbox("lab_r", (lx + 0.067, ly - 0.047, zp + 0.006), (lx + 0.075, ly + 0.047, zp + 0.012), BRASS, bevel=0.002))
    b.append(gbox("plaque", (0.26, 1.60, zp), (0.40, 1.68, zp + 0.005), BRASS, bevel=0.002))
    for sx in (0.27, 0.39):
        b.append(gcyl(f"plaque_s{sx}", 0.004, 0.004, (sx, 1.64, zp + 0.005), axis="z", verts=6, mat="M_Brass_Polished", bevel=0.0))
    X.decal("M_Decal_CabinetLabel", "cabinet_label.png")
    lab = gquad("cabinet_label", (lx, ly, zp + 0.0062), (1, 0, 0), (0, 1, 0), 0.115, 0.082, "M_Decal_CabinetLabel")
    # hinge knuckles on the outer edges of the doors
    for sx in (-1, 1):
        for y in (0.90, 1.16, 1.42):
            b.append(gcyl(f"hinge{sx}{y}", 0.009, 0.07, (sx * (X1 - 0.032), y - 0.035, Z1 + 0.012), axis="y", verts=8, mat=BRASS, bevel=0.0))
    # centre stile strip (where the doors meet)
    b.append(gbox("stile", (-0.006, DY0, Z1 + 0.026), (0.006, DY1, Z1 + 0.030), BRASS, bevel=0.0))
    mount("lamp_mount", (0.0, 0.952, 0.0))
    mount("light_origin_cabinet", (0.0, 1.0, 0.30))
    X.top(b, 4)
    body = part("cabinet_body", b, (0, 0, 0))
    lab = part("cabinet_label", [lab], (lx, ly, zp + 0.0062), presmooth=False)

    # doors: stiles/rails frame + raised panel, brass pull; left door built around x in [-0.485, -0.003]
    def door(side):
        sx = -1 if side == "l" else 1
        xa, xb = (X0 + 0.035, -0.002) if side == "l" else (0.002, X1 - 0.035)
        yb, yt = DY0 + 0.0, DY1
        zf = Z1 + 0.0
        o = [gbox("d_frame_a", (xa + 0.07, yb, zf), (xb - 0.07, yb + 0.07, zf + 0.026), MAH, bevel=0.003),
             gbox("d_frame_b", (xa + 0.07, yt - 0.07, zf), (xb - 0.07, yt, zf + 0.026), MAH, bevel=0.003),
             gbox("d_frame_c", (xa, yb, zf), (xa + 0.07, yt, zf + 0.026), MAH, bevel=0.005),
             gbox("d_frame_d", (xb - 0.07, yb, zf), (xb, yt, zf + 0.026), MAH, bevel=0.005),
             gbox("d_panel", (xa + 0.065, yb + 0.065, zf + 0.006), (xb - 0.065, yt - 0.065, zf + 0.020), MAH, bevel=0.004),
             gbox("d_raise", (xa + 0.10, yb + 0.10, zf + 0.020), (xb - 0.10, yt - 0.10, zf + 0.030), MAH, bevel=0.006, seg=2)]
        px = (xb - 0.05) if side == "l" else (xa + 0.05)
        o.append(gcyl("pull_stem", 0.007, 0.022, (px, 1.16, zf + 0.026), axis="z", verts=8, mat=BRASS, bevel=0.0))
        o.append(M.sphere("pull_knob", 0.016, loc=GV((px, 1.16, zf + 0.054)), segments=12, rings=6, mat="M_Brass_Polished"))
        hx = (X0 + 0.015) if side == "l" else (X1 - 0.015)
        return part("IA_door_" + side, o, (-0.485 if side == "l" else 0.485, 1.16, 0.243))

    dl, dr = door("l"), door("r")
    # wheels: AX along X, centred at (x, WY, WZ). combo_wheel is built in Blender coords: axle X, digit 0 faces local -Y = Godot +Z
    wheels = []
    for k, x in enumerate(WX):
        w = A.combo_wheel(f"IA_wheel_{k}", WR, 0.058, segments=30, rim_mat="M_Decal_DrawerDigits")
        w.location = (x, -WZ, WY)
        w = A.place(w, Matrix.Identity(4))
        w = part(f"IA_wheel_{k}", [w], (x, WY, WZ), presmooth=False)
        wheels.append(w)
    return body, dl, dr, wheels


if __name__ == "__main__":
    build()
    req = ["cabinet_body", "IA_door_l", "IA_door_r", "cabinet_label", "lamp_mount", "light_origin_cabinet"] + [f"IA_wheel_{k}" for k in range(4)]
    exp = {"IA_door_l": (-0.485, 1.16, 0.243), "IA_door_r": (0.485, 1.16, 0.243)}
    exp.update({f"IA_wheel_{k}": (WX[k], WY, WZ) for k in range(4)})
    errs = X.finish(NAME, req, ["IA_door_l", "IA_door_r", "cabinet_label"] + [f"IA_wheel_{k}" for k in range(4)], BUDGET, exp,
                    show=["cabinet_body", "IA_door_l", "IA_wheel_0"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (1.3, 1.5, 2.6), (0.0, 1.0, 0.0), 44), ("_lock", (0.0, 1.72, 0.85), (0.0, 1.64, 0.25), 30)], floor=True, world=0.2)
