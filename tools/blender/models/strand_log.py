"""strand_log.glb — Strand's log of the Night: a leather-bound field logbook (Chapter 4, group H; puzzle P2 `box_log`, the story's key document).

Dark leather boards (0.140 x 0.200, 3 mm) with a rounded spine carrying four raised bands, brass corner pieces, a brass frame line round the front cover, Strand's mark (a ring crossed by one
meridian) in brass relief at the centre, a brass clasp tab with a keyhole plate on the fore-edge, a cream page block with the page edges ridged on the three open sides and a leather
ribbon bookmark trailing from the tail. 0.140 x 0.200 x 0.025 m. Lies flat (cover up = Blender +Z = Godot +Y), the spine on the left (Blender -X), the head (top edge) toward Blender +Y
(= Godot -Z). Origin at the centre of mass. Slots: M_Leather, M_Paper, M_Brass_Aged (three: the documented exception of "<= 2 materials"; 3 surfaces).
    blender -b --factory-startup -P tools/blender/models/strand_log.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402
import lib_ch4_items as H  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "strand_log"
LEATHER, PAPER, BRASS = "M_Leather", "M_Paper", "M_Brass_Aged"
W, HT, T = 0.140, 0.200, 0.025
BT = 0.0030                       # board thickness
XS = -W / 2.0
SP_R = 0.0125                     # spine radius
SP_CX, SP_CZ = XS + 0.012, 0.0125


def boards():
    out = []
    loops = [L.rounded_rect(W, HT, 0.004, 3)]
    out.append(G.plate_xy("board_back", loops, BT, 0.0, LEATHER, bevel=0.0007))
    out.append(G.plate_xy("board_front", loops, BT, T - BT, LEATHER, bevel=0.0007))
    return out


def spine():
    bm = bmesh.new()
    ys = [-0.100, -0.0990]
    bands = (-0.072, -0.024, 0.024, 0.072)
    for c in bands:
        ys += [c - 0.0050, c - 0.0032, c + 0.0032, c + 0.0050]
    ys += [0.0990, 0.100]
    ys = sorted(set(ys))

    def radius(y):
        r = SP_R
        for c in bands:
            d = abs(y - c)
            if d <= 0.0032:
                r += 0.0016
            elif d < 0.0050:
                r += 0.0016 * (0.0050 - d) / (0.0050 - 0.0032)
        return r
    n = 12
    rows = []
    for y in ys:
        r = radius(y)
        row = []
        for i in range(n + 1):
            a = math.radians(90.0 + 180.0 * i / n)              # 90 deg (up, +Z) .. 270 (down) through 180 (-X)
            row.append(bm.verts.new((SP_CX + r * math.cos(a), y, SP_CZ + r * math.sin(a))))
        rows.append(row)
    for k in range(len(rows) - 1):
        for i in range(n):
            bm.faces.new((rows[k][i], rows[k + 1][i], rows[k + 1][i + 1], rows[k][i + 1]))
    for row in (rows[0], rows[-1]):                              # the half-disc ends and the open flat face on the pages' side
        bm.faces.new(row)
    for k in range(len(rows) - 1):                                 # the flat side facing the pages, strip by strip (so the shell is closed)
        bm.faces.new((rows[k][0], rows[k][-1], rows[k + 1][-1], rows[k + 1][0]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return [_obj("spine", bm, LEATHER)]


def _obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    return o


def pages():
    out = []
    x0, x1, y0, y1 = XS + 0.012, W / 2.0 - 0.0055, -HT / 2.0 + 0.0045, HT / 2.0 - 0.0045
    out.append(M.box("pages", (x1 - x0, y1 - y0, T - 2 * BT + 0.0008), loc=((x0 + x1) / 2.0, (y0 + y1) / 2.0, T / 2.0), mat=PAPER, bevel=0.0004, segments=1))
    # ridges on the fore-edge, the head and the tail: thin proud strips, the page edges
    k = 9
    zs = [BT + 0.0012 + (T - 2 * BT - 0.0024) * i / (k - 1) for i in range(k)]
    for z in zs:
        out.append(M.box("pe", (0.0009, y1 - y0 - 0.002, 0.0006), loc=(x1 + 0.00045, (y0 + y1) / 2.0, z), mat=PAPER, bevel=0.0, segments=1))
        out.append(M.box("pe", (x1 - x0 - 0.002, 0.0009, 0.0006), loc=((x0 + x1) / 2.0, y1 + 0.00045, z), mat=PAPER, bevel=0.0, segments=1))
        out.append(M.box("pe", (x1 - x0 - 0.002, 0.0009, 0.0006), loc=((x0 + x1) / 2.0, y0 - 0.00045, z), mat=PAPER, bevel=0.0, segments=1))
    return out


def brass():
    out = []
    z = T
    # corner pieces on the front board
    for sx in (-1, 1):
        for sy in (-1, 1):
            tri = [(sx * 0.0700, sy * 0.1000), (sx * 0.0700, sy * 0.0730), (sx * 0.0660, sy * 0.0730), (sx * 0.0420, sy * 0.1000)]
            out.append(G.plate_xy("corner", [tri], 0.0010, z, BRASS, bevel=0.0003))
            out.append(M.cylinder("rv", 0.0030, 0.0008, loc=(sx * 0.0630, sy * 0.0925, z + 0.0010 + 0.0004), mat=BRASS, verts=8, bevel=0.0))
    # a frame line round the cover
    outer = L.rounded_rect(0.1200, 0.1820, 0.003, 2)
    inner = list(reversed(L.rounded_rect(0.1170, 0.1790, 0.0025, 2)))
    out.append(G.plate_xy("frame", [outer, inner], 0.0006, z, BRASS, bevel=0.0))
    # Strand's mark at the centre
    out.append(G.plate_xy("mark", G.symbols().loops("mark", 0.074), 0.0014, z, BRASS, bevel=0.0))
    # the clasp: a tab from the fore-edge and a lock plate with a keyhole
    tab = [(0.0700, 0.0125), (0.0700, -0.0125), (0.0360, -0.0125), (0.0300, -0.0070), (0.0300, 0.0070), (0.0360, 0.0125)]
    out.append(G.plate_xy("clasp", [tab], 0.0010, z, BRASS, bevel=0.0003))
    plate = L.rounded_rect(0.0230, 0.0300, 0.0030, 3, 0.0460, 0.0)
    key = list(reversed(L.circle(0.0030, 10, cx=0.0460, cy=0.0030)))
    slot = list(reversed([(0.0446, 0.0020), (0.0474, 0.0020), (0.0480, -0.0090), (0.0440, -0.0090)]))
    out.append(G.plate_xy("lock", [plate, key], 0.0008, z + 0.0010, BRASS, bevel=0.0002))
    # the strap wrapping the fore-edge (a thin strip down the edge of the boards, 0.0005 proud)
    out.append(M.box("wrap", (0.0014, 0.025, T + 0.0010), loc=(W / 2.0 + 0.0007, 0.0, T / 2.0), mat=BRASS, bevel=0.0003, segments=1))
    return [o for o in out if o is not None]


def ribbon():
    # a leather ribbon from the tail edge of the pages, lying on the table toward -Y, slightly curved
    o = G.plate_xy("ribbon", [[(-0.0040, -0.0945), (0.0040, -0.0945), (0.0046, -0.1180), (0.0075, -0.1330), (0.0035, -0.1342), (-0.0004, -0.1215), (-0.0040, -0.1180)]], 0.0008,
                   BT, LEATHER, bevel=0.0001)
    return [o]


def build():
    parts = boards() + spine() + pages() + brass() + ribbon()
    root = M.join([p for p in parts], NAME)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 32.0), required=(), budget=2600, surf_budget=3, mat_budget=3, shots=[
        ("", (0.10, -0.20, 0.20), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.34), (0.0, -0.002, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
