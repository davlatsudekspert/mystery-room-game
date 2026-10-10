"""lockers4.glb — the watch room's bank of 24 brass-fronted lockers (2 rows x 12); locker 17 is Leyla's (Chapter 4, group G; secret S1).
Contract: docs/models/ch4.md section 8 `lockers` — renamed `lockers4` because `lockers.glb` is the Chapter 2 archive's bank (docs/models/ch2.md; never overwrite it).
Results: docs/models/ch4_g.md.

LOCAL FRAME: origin = the floor at the centre of the BACK face (z = 0), front = +Z (placed at the watch room's `lockers_mount`). The bank is 2.88 w (x +-1.44) x 1.89 h x 0.47 d
(carcass 0.43 deep, doors at z 0.43 .. 0.45). Numbering: top row 1..12, bottom row 13..24, both left -> right seen from the front, column c (0..11) is at
x = -1.44 + 0.24 (c + 0.5). **Locker 17 = bottom row, 5th from the left: x -0.48 .. -0.24, y 0.10 .. 0.95** (the only hollow one).
Nodes:
  lockers4          M_Steel_Painted + M_Brass_Aged  the painted carcass (plinth, solid blocks round locker 17's cavity, the middle rail, a cornice) and the 23 other doors (brass,
                    0.236 x 0.842 x 0.02, a raised panel, the numeral in relief, a pull handle and a keyhole boss), locker 17's hollow compartment (walls, floor, ceiling, a shelf
                    at y 0.50)
  IA_locker_17      M_Brass_Aged  locker 17's door, the same design as its neighbours. ORIGIN = the hinge axis on the LEFT edge (-0.480, 0.525, 0.45), identity at rest;
                    OPEN = -105 deg about +Y (swings out toward the viewer)
  IA_locker_note    M_Brass_Aged  a shallow brass tray on the shelf for the folded note. ORIGIN = the tray's top centre (-0.36, 0.516, 0.22); child note_mount (identity)
  IA_locker_parcel  M_Brass_Aged  a shallow brass tray on the compartment floor for the parcel. ORIGIN = its top centre (-0.36, 0.121, 0.22); child parcel_mount, yaw 90:
                    the parcel (0.20 x 0.12) lies with its long side along Z

    blender -b --factory-startup -P tools/blender/models/lockers4.py [-- --no-render] [--shots=1,2]
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
from lib_ch4 import K, D, BRASS, PAINT  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "lockers4"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 6000, 8, 3
HALF = 1.44
COLW = 0.24
ROW_Y = ((0.10, 0.95), (1.00, 1.85))            # (bottom row, top row) cells: y0, y1
ZF, ZD = 0.43, 0.45                             # carcass front, door front
DOOR_GAP = 0.002
N17 = (0, 4)                                    # cell row 0 (the BOTTOM row, y 0.10 .. 0.95), column 4
CELL17_X = (-HALF + COLW * 4, -HALF + COLW * 5)   # -0.48, -0.24
HINGE = (CELL17_X[0] - 0.0, 0.525, ZD)
NOTE_C = (-0.36, 0.516, 0.22)
PARCEL_C = (-0.36, 0.121, 0.22)


def number_of(row_idx: int, col: int) -> int:
    """row_idx 0 = bottom cell row, 1 = top cell row. Top row = 1..12, bottom row = 13..24."""
    return (12 + col + 1) if row_idx == 0 else (col + 1)


def door_mesh(mb, x0, x1, y0, y1, no, hinge_left=True):
    """One brass door in booth-style G coordinates (flush front at ZD, 0.02 thick) into the MB."""
    xc = (x0 + x1) / 2.0
    mb.box((x0, y0, ZF), (x1, y1, ZD))                                                         # the slab
    mb.box((x0 + 0.022, y0 + 0.07, ZD), (x1 - 0.022, y1 - 0.15, ZD + 0.0045))                    # the raised panel
    # a vent: three slots near the top of the panel are skipped (budget); a pull handle near the free edge and a keyhole boss
    hx = x1 - 0.050
    ym = y0 + (y1 - y0) * 0.45
    mb.box((hx - 0.007, ym - 0.045, ZD + 0.0045), (hx + 0.007, ym + 0.045, ZD + 0.020))
    mb.boss((hx, ym + 0.085, ZD + 0.0045), (0, 0, 1), 0.010, 0.0035, sides=6)
    # the numeral on a small raised plate above the panel
    mb.box((xc - 0.050, y1 - 0.122, ZD), (xc + 0.050, y1 - 0.058, ZD + 0.0030))


def door_digits(no, x0, x1, y1):
    xc = (x0 + x1) / 2.0
    return F.digits(no, 0.044, 0.0016, BRASS, (xc, y1 - 0.090, ZD + 0.0030))


def carcass():
    p = F.MB(PAINT)
    (yb0, yb1), (yt0, yt1) = ROW_Y
    # plinth, middle rail, cornice
    p.box((-HALF + 0.04, 0.0, 0.02), (HALF - 0.04, 0.10, ZF - 0.02))
    # bottom row: solid blocks left and right of locker 17's cavity, the cavity walls
    c0, c1 = CELL17_X
    t = 0.012
    p.box((-HALF, yb0, 0.0), (c0, yb1, ZF))
    p.box((c1, yb0, 0.0), (HALF, yb1, ZF))
    p.box((c0, yb0, 0.0), (c0 + t, yb1, ZF))                                    # the cavity's left wall
    p.box((c1 - t, yb0, 0.0), (c1, yb1, ZF))
    p.box((c0 + t, yb0, 0.0), (c1 - t, yb0 + t, ZF))                            # floor
    p.box((c0 + t, yb1 - t, 0.0), (c1 - t, yb1, ZF))                            # ceiling
    p.box((c0 + t, yb0 + t, 0.0), (c1 - t, yb1 - t, t))                         # back
    p.box((c0 + t, 0.50 - 0.005, t), (c1 - t, 0.50 + 0.005, 0.40))              # the shelf (y 0.495 .. 0.505)
    p.box((-HALF, yb1, 0.0), (HALF, yt0, ZF))                                   # middle rail (full width, solid)
    p.box((-HALF, yt0, 0.0), (HALF, yt1, ZF))                                   # the top row (solid blocks behind the doors)
    p.box((-HALF - 0.02, yt1, -0.0), (HALF + 0.02, yt1 + 0.04, ZD + 0.02))      # the cornice
    p.box((-HALF - 0.01, yt1 + 0.04, 0.0), (HALF + 0.01, yt1 + 0.055, ZD + 0.01))
    # vertical divider lines in the face: thin painted ribs between the doors (so the gaps read), on both rows
    for k in range(1, 12):
        x = -HALF + COLW * k
        for (ya, yb) in ((yb0, yb1), (yt0, yt1)):
            if (ya == yb0) and k in (4, 5):
                continue
            p.box((x - 0.0025, ya, ZF), (x + 0.0025, yb, ZF + 0.012))
    return [p.obj("lockers_paint")]


def doors_static():
    b = F.MB(BRASS)
    digit_objs = []
    for ri, (y0, y1) in enumerate(ROW_Y):
        for c in range(12):
            if (ri, c) == N17:
                continue
            x0 = -HALF + COLW * c + DOOR_GAP
            x1 = -HALF + COLW * (c + 1) - DOOR_GAP
            door_mesh(b, x0, x1, y0 + 0.004, y1 - 0.004, number_of(ri, c))
            digit_objs += door_digits(number_of(ri, c), x0, x1, y1 - 0.004)
    return [b.obj("lockers_brass")] + digit_objs


def door17():
    b = F.MB(BRASS)
    x0, x1 = CELL17_X[0] + DOOR_GAP, CELL17_X[1] - DOOR_GAP
    y0, y1 = ROW_Y[0][0] + 0.004, ROW_Y[0][1] - 0.004
    door_mesh(b, x0, x1, y0, y1, 17)
    # two hinge knuckles on the left edge
    for yk in (y0 + 0.14, y1 - 0.14):
        b.cyl((CELL17_X[0] + 0.001, yk - 0.035, ZD - 0.006), (0, 1, 0), 0.0085, 0.07, segs=8)
    return [b.obj("door17")] + door_digits(17, x0, x1, y1)


def pad(name, centre, w, d, y_base, rim=0.004, t=0.0045):
    b = F.MB(BRASS)
    cx, cy, cz = centre
    b.box((cx - w / 2, y_base, cz - d / 2), (cx + w / 2, cy - 0.0015, cz + d / 2))
    for (a, bb) in (((cx - w / 2, cz - d / 2), (cx + w / 2, cz - d / 2 + rim)), ((cx - w / 2, cz + d / 2 - rim), (cx + w / 2, cz + d / 2)),
                    ((cx - w / 2, cz - d / 2 + rim), (cx - w / 2 + rim, cz + d / 2 - rim)), ((cx + w / 2 - rim, cz - d / 2 + rim), (cx + w / 2, cz + d / 2 - rim))):
        b.box((a[0], cy - 0.0015, a[1]), (bb[0], cy + 0.0035, bb[1]))
    return b.obj(name)


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("lockers4", carcass() + doors_static())
    door = K.part("IA_locker_17", door17(), pivot=HINGE)
    note = K.part("IA_locker_note", [pad("note_pad", NOTE_C, 0.14, 0.19, 0.505)], pivot=NOTE_C)
    parcel = K.part("IA_locker_parcel", [pad("parcel_pad", PARCEL_C, 0.17, 0.26, 0.112)], pivot=PARCEL_C)
    K.empty("note_mount", NOTE_C)
    K.empty("parcel_mount", PARCEL_C, rot_deg=(0.0, 90.0, 0.0))
    K.to_blender()
    K.parent(bpy.data.objects["note_mount"], note)
    K.parent(bpy.data.objects["parcel_mount"], parcel)
    C.finalize()
    return dict(body=body, door=door, note=note, parcel=parcel)


def verify(path):
    req = ["lockers4", "IA_locker_17", "IA_locker_note", "IA_locker_parcel", "note_mount", "parcel_mount"]
    ident = ["lockers4", "IA_locker_17", "IA_locker_note", "IA_locker_parcel"]
    expect = {"lockers4": (0.0, 0.0, 0.0), "IA_locker_17": HINGE, "IA_locker_note": NOTE_C, "IA_locker_parcel": PARCEL_C, "note_mount": NOTE_C, "parcel_mount": PARCEL_C}
    errs = C.verify(path, required=req, identity=ident, expect=expect, parents={"note_mount": "IA_locker_note", "parcel_mount": "IA_locker_parcel"},
                    rot_expect={"parcel_mount": (0.0, 90.0, 0.0)}, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in ["lockers4", "IA_locker_17", "IA_locker_note", "IA_locker_parcel"]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    M.material("M_Concrete")
    M.material("M_Paper")
    M.box("qa_wall", (4.4, 0.1, 3.0), loc=K.G(0.0, 1.5, -0.05), mat="M_Concrete")
    M.box("qa_floor", (4.4, 3.0, 0.05), loc=K.G(0.0, -0.025, 1.4), mat="M_Concrete")
    # QA proxies at the item mounts: the folded note (0.10 x 0.14 x 0.004) and the parcel (0.20 x 0.12 x 0.08, long side along Z)
    M.box("qa_note", (0.10, 0.14, 0.004), loc=K.G(NOTE_C[0], NOTE_C[1] + 0.002, NOTE_C[2]), mat="M_Paper")
    M.box("qa_parcel", (0.12, 0.20, 0.08), loc=K.G(PARCEL_C[0], PARCEL_C[1] + 0.04, PARCEL_C[2]), mat="M_Cardboard")
    SM = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, strength=1.0):
        K.clear_lights()
        K.light("key", "POINT", (-0.5, 2.4, 1.8), 330.0 * strength, "FFE2C0", radius=0.2)
        K.light("fill", "POINT", (1.8, 1.2, 2.4), 120.0 * strength, "BFD4FF", radius=0.3)
        K.light("rim", "POINT", (0.0, 1.6, 1.2), 80.0 * strength, "FFD9A0", radius=0.2)
    if C.want(args, "1"):          # the whole bank, the door closed
        for o in bpy.data.objects:
            if o.name.startswith("qa_note") or o.name.startswith("qa_parcel"):
                o.hide_render = True
        cam, tgt, fov = (0.0, 1.25, 4.2), (0.0, 0.95, 0.0), 40
        lit(cam)
        C.shoot(NAME, cam, tgt, fov, samples=SM, res=RES)
    if C.want(args, "2"):          # locker 17 open, the note and the parcel in their trays
        for o in bpy.data.objects:
            if o.name.startswith("qa_note") or o.name.startswith("qa_parcel"):
                o.hide_render = False
        K.pose_rot(parts["door"], "y", -105.0)
        cam, tgt, fov = (0.35, 1.45, 1.5), (-0.36, 0.45, 0.25), 40
        lit(cam)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=SM, res=RES)


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
    F.backface_check(label=NAME, res=400)
    qa(args, parts)


main()
