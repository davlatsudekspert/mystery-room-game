"""evidence_board.glb — Leyla's evidence wall in the darkroom: cork board, staff photographs, newspaper
clippings about the 1979 "ventilation accident", a plan of the Array Hall, notes, pins and red string.

Model space (Blender, Z up): back plane at Y = 0, front toward -Y (Godot +Z). Origin = back-plane centre.
Overall 1.40 x 1.00 (oak frame 0.03), cork face at Y = -0.016. Place at Godot (-4.8, 1.5, -0.6),
rotation_degrees.y = 90 (front faces +X): x = -4.78 face, z in [-1.3, 0.1], y in [1.0, 2.0].
`photo_0` .. `photo_7`: paper planes, material M_Decal_Photos, each with its own 0..1 UV (u -> +X seen from
the front, v -> up; texture aspect 280 : 344, not mirrored). Use photo_k.jpg per card (material override).
Clippings/notes M_Paper, printed lines M_Fabric (ink), string M_String_Red, pins M_Brass_Aged / M_Enamel_Crimson.

Run: blender -b --factory-startup -P tools/blender/models/evidence_board.py [-- --no-render]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import mrlib as M  # noqa: E402
import lib_props as P  # noqa: E402

NAME = "evidence_board"
ARGS = M.main_guard()
M.reset_scene()
P.init_materials()
M.material("M_Enamel_Crimson", color="9A1C2B", rough=0.28)
rnd = random.Random(1411)

BW, BH = 1.40, 1.00
FR = 0.03
CORK_Y = -0.016
layer = [0]


def next_depth():
    layer[0] += 1
    return CORK_Y - 0.0006 - 0.00035 * layer[0]


# ---------------------------------------------------------------- board: cork panel + oak frame + backing
cork = M.box("cork", (BW - 2 * FR + 0.01, 0.01, BH - 2 * FR + 0.01), loc=(0, CORK_Y + 0.005, 0), mat="M_Cork", bevel=0.0)
backing = M.box("board_back", (BW - 0.01, 0.006, BH - 0.01), loc=(0, -0.003, 0), mat="M_Wood_Panel", bevel=0.0008, segments=1)
prof = [(0.0, 0.0), (0.0, 0.019), (0.003, 0.0235), (0.009, 0.025), (0.022, 0.025), (0.027, 0.0225), (FR, 0.0185), (FR, 0.0)]
frame = P.frame_sweep("frame", BW, BH, prof, mat="M_Wood_Panel")
board = M.join([cork, backing, frame], "board")


# ---------------------------------------------------------------- paper helpers
def sheet(name, w, h, mat, curl=0.004, nx=2, nz=3, seed=0):
    """Paper sheet centred at the origin in the XZ plane facing -Y, bottom corners lifting off the board.
    Returns (object, lift(x, z) -> lift toward -Y) so overlays can follow the curl."""
    r = random.Random(seed)
    lift_l, lift_r = r.uniform(0.3, 1.0) * curl, r.uniform(0.3, 1.0) * curl

    def lift(x, z):
        u = min(1.0, max(0.0, x / w + 0.5))
        v = min(1.0, max(0.0, z / h + 0.5))
        return (1 - v) ** 2 * (lift_l * (1 - u) ** 2 + lift_r * u ** 2)

    verts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            x, z = (i / nx - 0.5) * w, (j / nz - 0.5) * h
            verts.append((x, -lift(x, z), z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = P.mesh_obj(name, verts, faces, [mat])
    P.fix_normals(o)
    if o.data.polygons[0].normal.y > 0:
        o.data.flip_normals()
    if mat.startswith("M_Decal_"):
        M.planar_uv(o, axis="Y")
    return o, lift


def place(objs, x, z, angle_deg, depth):
    """Rotate a group built at the origin about the board normal and move it onto the board."""
    rot = Matrix.Rotation(math.radians(angle_deg), 4, "Y")
    for o in objs:
        o.data.transform(rot)
        o.location = (x, depth, z)


pins = []          # (world point of the pin head, kind)
static = []        # clippings, notes, strips, pins (joined later)


def pin(x, z, depth, kind="brass", name="pin"):
    """Push pin at (x, z): brass thumbtack (flat head) or crimson map pin (ball head)."""
    p = Vector((x, depth, z))
    if kind == "brass":
        o = P.lathe_axis(name, [(0.0, 0.0), (0.0062, 0.0), (0.0065, 0.0012), (0.0058, 0.0022), (0.0025, 0.0026), (0.0022, 0.006),
                                (0.0032, 0.0072), (0.0, 0.0082)], axis="Y", sign=-1, segments=10, mat="M_Brass_Aged", loc=p)
        head = p + Vector((0, -0.006, 0))
    else:
        o = P.lathe_axis(name, [(0.0, 0.0), (0.0009, 0.0), (0.0009, 0.004), (0.0042, 0.0062), (0.0048, 0.0095), (0.0034, 0.0125),
                                (0.0, 0.0135)], axis="Y", sign=-1, segments=10, mat="M_Enamel_Crimson", loc=p)
        head = p + Vector((0, -0.0035, 0))
    static.append(o)
    pins.append(head)
    return head


# ---------------------------------------------------------------- the staff photographs (photo_0..7)
PHW, PHH = 0.11, 0.11 * 344.0 / 280.0
photo_spots = [(-0.56, 0.27, -3), (-0.41, 0.285, 2), (-0.26, 0.262, -1.5), (-0.11, 0.28, 3.5),
               (-0.555, 0.04, 2.5), (-0.405, 0.025, -2), (-0.255, 0.045, 1), (-0.105, 0.03, -3.5)]
photo_pins = []
for k, (x, z, ang) in enumerate(photo_spots):
    d = next_depth()
    ph, _lift = sheet(f"photo_{k}", PHW, PHH, "M_Decal_Photos", curl=0.0035, seed=k)
    place([ph], x, z, ang, d)
    top = Vector((x, d, z)) + Matrix.Rotation(math.radians(ang), 3, "Y") @ Vector((0, 0, PHH / 2 - 0.012))
    photo_pins.append(pin(top.x, top.z, d - 0.0002, "brass", f"photo_pin{k}"))

# ---------------------------------------------------------------- newspaper clippings + notes + plan
def clipping(name, x, z, w, h, ang, rows, head=None, seed=1, curl=0.003):
    """Paper with fake printed/handwritten lines (ink strips follow the paper curl)."""
    d = next_depth()
    paper, lift = sheet(name, w, h, "M_Paper", curl=curl, seed=seed)
    txt = P.flat_text_strips(f"{name}_txt", -w / 2 + 0.01, h / 2 - 0.012, w - 0.02, rows, y=0.0, seed=seed * 7, headline=head)
    for v in txt.data.vertices:
        v.co.y = -lift(v.co.x, v.co.z) - 0.0004
    g = M.join([paper, txt], name)
    place([g], x, z, ang, d)
    static.append(g)
    return g, d


clip_a, da = clipping("clip_accident", 0.27, 0.2, 0.25, 0.3, 2.0, rows=34, head=(0.014, 2), seed=3)
clip_b, db = clipping("clip_column", 0.5, 0.18, 0.11, 0.27, -2.5, rows=42, seed=5)
clip_c, dc = clipping("clip_small", 0.21, -0.12, 0.15, 0.1, -4.0, rows=10, head=(0.009, 1), seed=9)
note_a, dn = clipping("note_1979", 0.03, 0.39, 0.12, 0.07, 3.0, rows=4, seed=11, curl=0.0015)
pin(0.27, 0.2 + 0.13, da - 0.0002, "red", "pin_clip_a")
pin(0.5, 0.18 + 0.12, db - 0.0002, "red", "pin_clip_b")
pin(0.21, -0.12 + 0.035, dc - 0.0002, "brass", "pin_clip_c")
pin(0.03, 0.41, dn - 0.0002, "red", "pin_note")

# plan of the Array Hall: blueprint-like sheet with drawn room outlines
d = next_depth()
plan_sheet, plan_lift = sheet("plan", 0.3, 0.22, "M_Paper", curl=0.004, seed=21)
plan = [plan_sheet]
lines = []
for (x0, z0, x1, z1) in ((-0.13, -0.09, 0.13, -0.09), (-0.13, 0.09, 0.13, 0.09), (-0.13, -0.09, -0.13, 0.09), (0.13, -0.09, 0.13, 0.09),
                         (-0.04, -0.09, -0.04, 0.03), (-0.04, 0.03, 0.13, 0.03), (0.05, 0.03, 0.05, 0.09), (-0.13, -0.02, -0.04, -0.02)):
    w = 0.0016
    if abs(z1 - z0) < 1e-6:
        lines.append(M.box("pl", (x1 - x0 + w, 0.0002, w), loc=((x0 + x1) / 2, -0.0004, z0), mat="M_Fabric", bevel=0.0))
    else:
        lines.append(M.box("pl", (w, 0.0002, z1 - z0 + w), loc=(x0, -0.0004, (z0 + z1) / 2), mat="M_Fabric", bevel=0.0))
ring_c = M.torus("plan_array", 0.03, 0.0012, loc=(0.085, -0.0004, -0.035), rot=(math.pi / 2, 0, 0), major_seg=20, minor_seg=3,
                 mat="M_Enamel_Crimson")
lines.append(ring_c)
for o in lines:
    M.apply_transform(o)
    for v in o.data.vertices:
        v.co.y += -plan_lift(v.co.x, v.co.z)
plan_g = M.join(plan + lines, "plan")
place([plan_g], 0.32, -0.27, 1.5, d)
static.append(plan_g)
pin(0.32 - 0.13, -0.27 + 0.09, d - 0.0002, "brass", "pin_plan_l")
pin(0.32 + 0.13, -0.27 + 0.09, d - 0.0002, "brass", "pin_plan_r")
plan_pin = pin(0.32 + 0.085, -0.27 - 0.035, d - 0.0002, "red", "pin_plan_array")

# handwritten index cards under the photos (names / dates) — ink strips, slightly askew
for k, (x, z, ang) in enumerate(((-0.48, -0.16, 2.0), (-0.2, -0.17, -1.5), (-0.36, -0.33, 1.0))):
    c, dcard = clipping(f"card{k}", x, z, 0.12, 0.075, ang, rows=4, seed=30 + k, curl=0.0015)
    pin(x, z + 0.025, dcard - 0.0002, "brass", f"pin_card{k}")

# staff list: 41 typed names, most struck through in red (the 41 who never left)
d = next_depth()
staff, staff_lift = sheet("staff_list", 0.14, 0.25, "M_Paper", curl=0.004, seed=51)
st_txt = P.flat_text_strips("staff_txt", -0.06, 0.112, 0.085, 41, row_h=0.0013, gap=0.0039, y=0.0, seed=52, headline=(0.006, 1))
strikes = []
r51 = random.Random(51)
zrow = 0.112 - 0.006 - 0.0039 * 0.9
for k in range(41):
    zc = zrow - k * (0.0013 + 0.0039) - 0.00065
    if r51.random() < 0.8:
        strikes.append(M.box(f"strike{k}", (0.07 + r51.uniform(-0.01, 0.015), 0.0002, 0.0007), loc=(-0.02, -0.0008, zc),
                             rot=(0, r51.uniform(-0.03, 0.03), 0), mat="M_String_Red", bevel=0.0))
for o in [st_txt] + strikes:
    M.apply_transform(o)
    for v in o.data.vertices:
        v.co.y += -staff_lift(v.co.x, v.co.z) - (0.0004 if o is st_txt else 0.0)
staff_g = M.join([staff, st_txt] + strikes, "staff_list")
place([staff_g], 0.02, -0.24, -1.2, d)
static.append(staff_g)
staff_pin = pin(0.02, -0.24 + 0.11, d - 0.0002, "red", "pin_staff")

# calendar leaf: NOVEMBER 1979, the 14th circled
d = next_depth()
cal, cal_lift = sheet("calendar", 0.15, 0.17, "M_Paper", curl=0.003, seed=61)
cl = [M.box("cal_head", (0.11, 0.0002, 0.012), loc=(0, -0.0004, 0.064), mat="M_Fabric", bevel=0.0),
      M.box("cal_year", (0.05, 0.0002, 0.006), loc=(0, -0.0004, 0.047), mat="M_Fabric", bevel=0.0)]
gx0, gx1, gz0, gz1 = -0.063, 0.063, -0.075, 0.035
for i in range(8):
    x = gx0 + (gx1 - gx0) * i / 7
    cl.append(M.box(f"cal_v{i}", (0.0007, 0.0002, gz1 - gz0), loc=(x, -0.0004, (gz0 + gz1) / 2), mat="M_Fabric", bevel=0.0))
for j in range(6):
    z = gz0 + (gz1 - gz0) * j / 5
    cl.append(M.box(f"cal_h{j}", (gx1 - gx0, 0.0002, 0.0007), loc=(0, -0.0004, z), mat="M_Fabric", bevel=0.0))
cw, chh = (gx1 - gx0) / 7, (gz1 - gz0) / 5
c14 = Vector((gx0 + cw * 2.5, -0.0006, gz1 - chh * 2.5))      # Wednesday 14 November 1979
cl.append(M.torus("cal_circle", 0.0105, 0.0009, loc=c14, rot=(math.pi / 2, 0, 0), major_seg=16, minor_seg=3, mat="M_String_Red"))
for o in cl:
    M.apply_transform(o)
    for v in o.data.vertices:
        v.co.y += -cal_lift(v.co.x, v.co.z)
cal_g = M.join([cal] + cl, "calendar")
place([cal_g], -0.555, -0.34, 2.5, d)
static.append(cal_g)
cal_pin = pin(-0.555, -0.34 + 0.075, d - 0.0002, "brass", "pin_calendar")

# ---------------------------------------------------------------- red string between the clues (taut, tiny sag)
def string(a, b, name):
    a, b = Vector(a), Vector(b)
    n = 6
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= 0.004 * math.sin(math.pi * t) * (a - b).length
        p.y = min(a.y, b.y) - 0.0004
        pts.append(p)
    static.append(P.tube(name, pts, 0.0011, sides=4, mat="M_String_Red", caps=False))


red_a = pins[len(photo_pins)]          # clipping A
string(photo_pins[1], red_a, "str0")
string(photo_pins[3], red_a, "str1")
string(photo_pins[6], red_a, "str2")
string(red_a, pins[len(photo_pins) + 1], "str3")      # -> column clipping
string(red_a, plan_pin, "str4")                        # -> the Array Hall
string(pins[len(photo_pins) + 3], photo_pins[2], "str5")  # note 14.XI.1979 -> photo
string(pins[len(photo_pins) + 2], plan_pin, "str6")
string(staff_pin, photo_pins[5], "str7")
string(staff_pin, red_a, "str8")
string(cal_pin, pins[len(photo_pins) + 3], "str9")

M.join(static, "evidence_items")
M.finalize(smooth_angle=40)
P.report(NAME)
P.export_lean(NAME)

if "--no-render" not in ARGS:
    P.render_threads(2)
    for k in range(8):   # QA only: each card shows its own photo_k.jpg (in Godot: material override per card)
        o = bpy.data.objects[f"photo_{k}"]
        o.data.materials.clear()
        o.data.materials.append(P.photo_preview_material(k))
    P.qa_box("qa_wall", (2.2, 0.04, 1.8), (0, 0.02, 0.0), colour="A39C8B")
    P.shots(NAME, [
        ("", (0.55, -1.9, 0.12), (0.0, 0.0, 0.0), 40),
        ("_2", (-0.12, -0.55, 0.2), (-0.3, 0.0, 0.12), 40),
    ], ARGS, samples=32)
