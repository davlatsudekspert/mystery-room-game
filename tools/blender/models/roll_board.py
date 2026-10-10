"""roll_board.glb — the watch room's roll board: 42 brass hooks and 42 lamp sockets, the 41 tags and 41 + 1 lamps are code MultiMeshes (Chapter 4, group G).
Contract: docs/models/ch4.md section 8 roll_board; results: docs/models/ch4_g.md.

LOCAL FRAME: origin = the floor under the board's centre, the board hangs on the back wall, front = +Z (the panel's back is at z = 0, its face at z = 0.03).
Board 2.40 w x 1.50 h (x +-1.2, y 0.25 .. 1.75), placed at the watch room's `board_mount`.
Slots: 3 rows of 14, slot i = row i // 14, col i % 14 at (-1.04 + 0.16 col, 1.28 - 0.30 row), hook tip centre z = 0.05; the 42nd slot (i = 41: row 2, col 13) is the Leyla slot
(an empty hook on a brass plaque with her sign: a crescent opening right and three dots).
Nodes:
  roll_board    M_Wood_Walnut + M_Brass_Aged  the walnut panel with a brass frame, header band with the Institute's mark, three hanging rails, a bottom ledge, 42 brass hooks
                (a plate on the panel + a square pin to z 0.07 with an upturned tip) and 42 hex lamp sockets 0.115 above each hook (the jewel sits in them), Leyla's plaque
  tag_proto     M_Enamel_Cream  a cream enamel tag 0.100 x 0.070 x 0.003 with a raised rim and a hanging hole. ORIGIN = the first slot's hook centre (-1.04, 1.28, 0.05) = the
                hole centre; the tag hangs below it (y -0.058 .. +0.012), identity. ONE tag per slot: instance k at (0.16 col, -0.30 row, 0) from the node
  lamp_proto    M_Glass_Dark  a jewel dome O 0.030, 10 mm high. ORIGIN = the same first-slot point; the mesh is baked 0.115 above it and 0.017 behind it (in its socket),
                so the SAME instance transform (0.16 col, -0.30 row, 0) places the lamp of slot k. 42 instances (slot 41 is the Leyla lamp)
  slot_origin   empty at (-1.04, 1.28, 0.05)

    blender -b --factory-startup -P tools/blender/models/roll_board.py [-- --no-render] [--shots=1,2]
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
import lib_mech as L  # noqa: E402
from lib_ch4 import K, D, BRASS, WALNUT, CREAM, GDARK  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "roll_board"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 5, 4
SLOT0 = (-1.04, 1.28, 0.05)
STEP = (0.16, -0.30)
COLS, ROWS = 14, 3
LAMP_DY, LAMP_DZ = 0.115, -0.017
FACE = 0.03
Y0, Y1 = 0.25, 1.75


def slot_pos(i: int):
    return (SLOT0[0] + STEP[0] * (i % COLS), SLOT0[1] + STEP[1] * (i // COLS), SLOT0[2])


def board_parts():
    w = F.MB(WALNUT)
    b = F.MB(BRASS)
    # panel, a plinth skirt and a back rail
    w.box((-1.20, Y0, 0.0), (1.20, Y1, FACE))
    w.box((-1.16, 0.0, 0.0), (1.16, Y0, 0.06))
    # raised walnut field panels (one per row band) so the board is not a flat sheet
    for (ya, yb) in ((1.43, 1.50), (0.55, 0.62), (0.48, 0.52)):
        w.box((-1.12, ya, FACE), (1.12, yb, FACE + 0.004))
    # brass frame: four strips, raised 12 mm; corner rosettes
    b.box((-1.22, Y0 - 0.02, 0.0), (1.22, Y0 + 0.04, 0.045))
    b.box((-1.22, Y1 - 0.04, 0.0), (1.22, Y1 + 0.02, 0.045))
    b.box((-1.22, Y0 + 0.04, 0.0), (-1.16, Y1 - 0.04, 0.045))
    b.box((1.16, Y0 + 0.04, 0.0), (1.22, Y1 - 0.04, 0.045))
    for sx in (-1, 1):
        for y in (Y0 + 0.01, Y1 - 0.01):
            b.boss((sx * 1.19, y, 0.045), (0, 0, 1), 0.026, 0.008, sides=8)
    # header band with the Institute's mark, and a bottom ledge with a lip
    b.box((-1.10, 1.52, FACE), (1.10, 1.66, FACE + 0.008))
    for sx in (-1, 1):
        for k in range(4):
            b.dome((sx * (0.96 - 0.07 * k), 1.59, FACE + 0.008), 0.009, 0.007, segs=5, normal=(0, 0, 1))
    b.box((-1.14, 0.40, FACE), (1.14, 0.45, 0.10))
    b.box((-1.14, 0.45, 0.092), (1.14, 0.49, 0.10))
    # three hanging rails (one above each row's hooks)
    for r in range(ROWS):
        y = SLOT0[1] + STEP[1] * r + 0.060
        b.box((-1.12, y - 0.004, FACE), (1.12, y + 0.004, FACE + 0.006))
    # hooks and lamp sockets for the 42 slots
    for i in range(COLS * ROWS):
        x, y, z = slot_pos(i)
        b.box((x - 0.011, y - 0.011, FACE), (x + 0.011, y + 0.011, FACE + 0.004))                    # the hook plate
        b.bar((x, y, FACE + 0.004), (x, y, z + 0.020), 0.0075, ref=(0, 1, 0))                         # the pin
        b.bar((x, y, z + 0.020), (x, y + 0.012, z + 0.020), 0.0075, ref=(0, 0, 1))                    # the upturned tip
        b.boss((x, y + LAMP_DY, FACE), (0, 0, 1), 0.0205 if i != 41 else 0.0245, 0.008, sides=6)     # the lamp socket
    # Leyla's plaque behind the 42nd hook: a brass plate 0.115 x 0.150 with her sign
    x, y, z = slot_pos(41)
    b.box((x - 0.060, y - 0.065, FACE), (x + 0.060, y + 0.155, FACE + 0.004))
    out = [w.obj("board_walnut"), b.obj("board_brass")]
    sign = K.plate("sign", C.S.loops("sign", 0.050), 0.0022, z0=FACE + 0.004, mat=BRASS, bevel=0.0003, drop_bottom=True, loc=(x, y - 0.020, 0.0))
    mark = MK.mark_solids(0.105, 0.004, BRASS, loc=(0.0, 1.59), z0=FACE + 0.008, name="mark")
    return out + [sign] + mark


def tag_parts():
    # the tag is built at the first slot (hole centre = SLOT0): 0.100 wide, y -0.058 .. +0.012 about the hole; the lower corners cut
    sx, sy, sz = SLOT0
    outline = [(-0.050, 0.012), (0.050, 0.012), (0.050, -0.050), (0.042, -0.058), (-0.042, -0.058), (-0.050, -0.050)]
    hole = list(reversed(L.circle(0.0055, 12)))
    base = K.plate("tag", [outline, hole], 0.003, z0=sz - 0.0015, mat=CREAM, bevel=0.0004, drop_bottom=False, loc=(sx, sy, 0.0))
    rim_out = [(-0.045, 0.007), (0.045, 0.007), (0.045, -0.047), (0.038, -0.053), (-0.038, -0.053), (-0.045, -0.047)]
    rim_in = [(-0.041, 0.003), (0.041, 0.003), (0.041, -0.043), (0.036, -0.049), (-0.036, -0.049), (-0.041, -0.043)]
    rim = K.plate("tagrim", [rim_out, list(reversed(rim_in))], 0.0014, z0=sz + 0.0015, mat=CREAM, bevel=0.0002, drop_bottom=True, loc=(sx, sy, 0.0))
    bar = K.plate("tagbar", [[(-0.030, -0.020), (0.030, -0.020), (0.030, -0.036), (-0.030, -0.036)]], 0.0012, z0=sz + 0.0015, mat=CREAM, bevel=0.0002,
                  drop_bottom=True, loc=(sx, sy, 0.0))
    return [base, rim, bar]


def lamp_parts():
    sx, sy, sz = SLOT0
    return [K.glathe("lamp", [(0.0150, 0.0), (0.0148, 0.0030), (0.0125, 0.0070), (0.0075, 0.0097), (0.0, 0.0105)], base=(sx, sy + LAMP_DY, FACE + 0.004),
                     axis=(0, 0, 1), segments=10, mat=GDARK, smooth=60.0, cap_bottom=True)]


def build():
    M.reset_scene()
    C.ensure_materials()
    body = C.merge("roll_board", board_parts())
    tag = K.part("tag_proto", tag_parts(), pivot=SLOT0)
    lamp = K.part("lamp_proto", lamp_parts(), pivot=SLOT0)
    K.empty("slot_origin", SLOT0)
    K.to_blender()
    return dict(body=body, tag=tag, lamp=lamp)


def finish(parts):
    C.finalize()


def verify(path):
    req = ["roll_board", "tag_proto", "lamp_proto", "slot_origin"]
    expect = {"roll_board": (0.0, 0.0, 0.0), "tag_proto": SLOT0, "lamp_proto": SLOT0, "slot_origin": SLOT0}
    errs = C.verify(path, required=req, identity=req[:3], expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    for n in req[:3]:
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    M.material("M_Concrete")
    M.box("qa_wall", (4.0, 0.1, 3.0), loc=K.G(0.0, 1.5, -0.05), mat="M_Concrete")
    M.box("qa_floor", (4.0, 4.0, 0.05), loc=K.G(0.0, -0.025, 1.0), mat="M_Wood_Walnut")
    tag, lamp = parts["tag"], parts["lamp"]
    glow = K.glow("qa_lamp_on", "FFD9A0", 7.0)
    for i in range(1, 42):
        if i < 41:
            t = tag.copy()
            t.location = K.G(*slot_pos(i)) - K.G(*slot_pos(0)) + tag.location
            bpy.context.scene.collection.objects.link(t)
        lp = lamp.copy()
        lp.location = K.G(*slot_pos(i)) - K.G(*slot_pos(0)) + lamp.location
        bpy.context.scene.collection.objects.link(lp)
        if i < 26 or i == 41:                                   # lit lamps (the finale puts them out one by one)
            K.override(lp, glow)
    K.override(lamp, glow)
    M.refresh()
    SM = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, strength=1.0):
        K.clear_lights()
        K.light("key", "POINT", (-0.8, 2.6, 1.6), 380.0 * strength, "FFE2C0", radius=0.2)
        K.light("fill", "POINT", (1.8, 1.4, 2.4), 160.0 * strength, "BFD4FF", radius=0.3)
        K.light("rim", "POINT", (0.2, 2.2, 0.9), 120.0 * strength, "FFD9A0", radius=0.2)
    if C.want(args, "1"):
        cam, tgt, fov = (0.0, 1.08, 3.1), (0.0, 1.0, 0.0), 40
        lit(cam)
        C.shoot(NAME, cam, tgt, fov, samples=SM, res=RES)
    if C.want(args, "2"):          # the Leyla slot and the lower right of the board
        cam, tgt, fov = (0.75, 0.95, 1.1), (0.88, 0.80, 0.05), 40
        lit(cam)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=SM, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    finish(parts)
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
