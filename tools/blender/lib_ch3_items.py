"""MYSTERY ROOM — Chapter 3 inventory-item helpers (build group G, docs/models/ch3.md section 9).

Builds on mrlib, lib_mech, lib_devices and lib_ch2_items (never edits them). The pipeline is the Chapter 2
item pipeline (lib_ch2_items): reset, build, finalize (box UVs + smoothing), optional post step (decal UVs,
resmoothing), move the centre of mass to the origin, export game/assets/models/<name>.glb, print the size /
bottom / tris in Godot axes, check the required part names (own objects, identity rotation) and run the
back-face check. Chapter 3 additions:
  * QA renders go to qa/blender/ch3/ (Cycles, <= 32 samples, <= 960 x 640, 2 threads);
  * the Chapter 3 decal slot M_Decal_EcgPaper (image from game/assets/textures/decals/ch3/ when it exists);
  * the exported GLB is re-read and its tris, surfaces (primitives = mesh x material) and material slots
    are checked against the section 13 budget (items: <= 3 surfaces, <= 2 materials unless the caller
    passes a documented exception);
  * check_glb_names (Godot import-hint suffixes) runs on the exported file;
  * symbols(): the shared Chapter 3 symbol outlines (tools/blender/lib_ch3_symbols.py, group A) when the
    library exists, else None (the caller then builds the geometry without the symbol inlays).

Conventions: metres, Blender Z-up; Godot = Blender (x, z, -y). Flat items lie in the Blender XY plane, hero
face up (+Z), top edge toward Blender +Y (= Godot -Z). Standing items face Blender -Y (= Godot +Z).
"""
from __future__ import annotations

import importlib
import json
import math
import os
import struct
import subprocess
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402

ROOT = M.ROOT
DECALS_CH3 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch3")
QA_SUB = "ch3"
C.QA_SUB = QA_SUB              # lib_ch2_items.shot() writes into qa/blender/<QA_SUB>/
TAU = 2.0 * math.pi

# Chapter 3 decal slots used by the items: slot -> (image in DECALS_CH3, fallback preview colour)
CH3_DECALS = {
    "M_Decal_EcgPaper": ("ecg_paper.png", "E8B4A0"),
}


def ensure_materials() -> None:
    C.ensure_materials()
    for slot, (fname, hx) in CH3_DECALS.items():
        if bpy.data.materials.get(slot) is not None:
            continue
        path = os.path.join(DECALS_CH3, fname)
        M.material(slot, color="FFFFFF" if os.path.exists(path) else hx, rough=0.8, metal=0.0,
                   image=path if os.path.exists(path) else "")


def symbols():
    """The shared symbol library (group A) or None while it is not on main yet."""
    try:
        return importlib.import_module("lib_ch3_symbols")
    except ImportError:
        return None


# ---------------------------------------------------------------- GLB checks
def glb_json(path: str) -> dict:
    with open(path, "rb") as fh:
        data = fh.read()
    n = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + n])


def glb_stats(path: str) -> dict:
    """tris, surfaces (= primitives, one per mesh x material), material names and node names of a GLB."""
    doc = glb_json(path)
    tris = surfaces = 0
    mats = set()
    per_mesh = {}
    for m in doc.get("meshes", []):
        mt = 0
        for prim in m["primitives"]:
            idx = prim.get("indices")
            acc = doc["accessors"][idx if idx is not None else prim["attributes"]["POSITION"]]
            mt += acc["count"] // 3
            surfaces += 1
            if "material" in prim:
                mats.add(doc["materials"][prim["material"]]["name"])
        per_mesh[m.get("name")] = mt
        tris += mt
    return {"tris": tris, "surfaces": surfaces, "materials": sorted(mats), "per_mesh": per_mesh,
            "nodes": [n.get("name") for n in doc.get("nodes", [])]}


def check_names(path: str) -> bool:
    res = subprocess.run([sys.executable if os.path.basename(sys.executable).startswith("python") else "python3",
                          os.path.join(ROOT, "tools", "blender", "check_glb_names.py"), path],
                         capture_output=True, text=True)
    print(f"[items3] check_glb_names: {res.stdout.strip()} (exit {res.returncode})")
    return res.returncode == 0


def budget_report(name: str, path: str, tri_budget: int, surf_budget: int = 3, mat_budget: int = 2) -> dict:
    st = glb_stats(path)
    ok_t = st["tris"] <= tri_budget
    ok_s = st["surfaces"] <= surf_budget
    ok_m = len(st["materials"]) <= mat_budget
    missing = [m for m in st["materials"] if not os.path.exists(os.path.join(ROOT, "game", "assets", "materials",
                                                                              m + ".tres"))]
    print(f"[items3] {name}.glb: tris={st['tris']} / {tri_budget} ({'OK' if ok_t else 'OVER'}), "
          f"surfaces={st['surfaces']} / {surf_budget} ({'OK' if ok_s else 'OVER'}), "
          f"materials={len(st['materials'])} / {mat_budget} {st['materials']} ({'OK' if ok_m else 'OVER'})")
    if missing:
        print(f"[items3] {name}.glb: material slots without a .tres yet: {missing}")
    print(f"[items3] {name}.glb: per mesh {st['per_mesh']}")
    return st


# ---------------------------------------------------------------- geometry helpers
def plate_xy(name: str, loops, thick: float, z0: float, mat: str, bevel: float = 0.0005,
             bevel_res: int = 0) -> bpy.types.Object:
    """curve_solid of 2D loops (even-odd) from z0 to z0 + thick, transform baked."""
    o = L.curve_solid(name, loops, thick, bevel=bevel, bevel_res=bevel_res, mat=mat)
    o.location = (0, 0, z0)
    M.apply_transform(o)
    return o


def rounded_poly(pts, r: float, n: int = 4):
    """Round every corner of a convex CCW polygon with radius r (n points per corner arc)."""
    out = []
    m = len(pts)
    for i in range(m):
        p0 = Vector(pts[i - 1])
        p1 = Vector(pts[i])
        p2 = Vector(pts[(i + 1) % m])
        a = (p0 - p1).normalized()
        b = (p2 - p1).normalized()
        ang = math.acos(max(-1.0, min(1.0, a.dot(b))))
        d = r / math.tan(ang / 2)
        t0 = p1 + a * d
        t1 = p1 + b * d
        bis = (a + b).normalized()
        c = p1 + bis * (r / math.sin(ang / 2))
        a0 = math.atan2(t0.y - c.y, t0.x - c.x)
        a1 = math.atan2(t1.y - c.y, t1.x - c.x)
        while a1 - a0 > math.pi:
            a1 -= TAU
        while a0 - a1 > math.pi:
            a1 += TAU
        for k in range(n + 1):
            t = a0 + (a1 - a0) * k / n
            out.append((c.x + r * math.cos(t), c.y + r * math.sin(t)))
    return out


def scale_loop(loop, s: float, cx: float = 0.0, cy: float = 0.0):
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for (x, y) in loop]


def hex_crystal(name: str, sections, mat: str = "M_Crystal", jitter=None, tip_offset=(0.0, 0.0),
                base_offset=(0.0, 0.0)) -> bpy.types.Object:
    """Closed hexagonal crystal along Blender +Z. sections: [(z, circumradius)] bottom -> top; a radius of 0
    at either end makes a pointed termination (6 facets meeting at an apex). Vertices sit at k x 60 deg, so a
    flat prism face looks at Blender -Y (Godot +Z, the item's front). jitter[k] scales vertex column k (a
    natural, slightly uneven crystal); tip_offset / base_offset shift the apexes in XY."""
    import bmesh
    jitter = jitter or [1.0] * 6
    bm = bmesh.new()
    rings = []
    for i, (z, r) in enumerate(sections):
        if r <= 1e-9:
            off = tip_offset if i == len(sections) - 1 else base_offset
            rings.append([bm.verts.new((off[0], off[1], z))])
            continue
        rings.append([bm.verts.new((r * jitter[k] * math.cos(math.radians(60 * k)),
                                    r * jitter[k] * math.sin(math.radians(60 * k)), z)) for k in range(6)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(6):
            k1 = (k + 1) % 6
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[k1]))
            elif len(b) == 1:
                bm.faces.new((a[k], b[0], a[k1])[::-1])
            else:
                bm.faces.new((a[k], a[k1], b[k1], b[k]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, mat)
    return obj


def seed_collar(name: str = "collar", mat: str = "M_Brass_Aged") -> bpy.types.Object:
    """The brass seed collar (shared by seed_crystal and nursery_crystal): a turned cup Ø 15 mm, 6.5 mm high,
    bottom at z = 0, with a bead under the lip and a shallow recess on top (floor z = COLLAR_SEAT) that holds
    the crystal."""
    prof = [(0.0, 0.0), (0.0062, 0.0), (0.0072, 0.0007), (0.0072, 0.0016), (0.0066, 0.0021),
            (0.0066, 0.0036), (0.0076, 0.0042), (0.0076, 0.0055), (0.0073, 0.0063), (0.0068, 0.0065),
            (0.0063, 0.0061), (0.0063, COLLAR_SEAT), (0.0, COLLAR_SEAT)]
    return L.lathe2(name, prof, segments=24, mat=mat, cap_bottom=False, cap_top=False)


COLLAR_SEAT = 0.0048          # floor of the collar's recess (Blender z), the crystal's base sits there
COLLAR_TOP = 0.0065


# ---------------------------------------------------------------- pipeline
POINTS: dict = {}            # QA_pt_<name> empties of the current build (Blender, after recentring)


def tidy_mesh_names() -> None:
    """Drop orphan mesh data left by joins and give every mesh its object's name (the GLB mesh names)."""
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.data.users == 1:
            o.data.name = o.name


def item_main(name: str, build_fn, shots=(), post=None, required=(), budget: int = 2500, surf_budget: int = 3,
              mat_budget: int = 2, extra_report=None, com_fn=None) -> None:
    """Chapter 3 item build (see the module doc). shots: [(suffix, cam_loc, target, lens[, pose_fn])] in Blender
    coordinates relative to the centred item; a dark floor is put under the item's lowest point. pose_fn()
    runs before its shot (QA only, after the export) and its pose stays for the following shots. com_fn() may
    return the centre of mass for items made of open sheets (paper), which centre_of_mass cannot weigh."""
    M.reset_scene()
    ensure_materials()
    build_fn()
    M.finalize()
    if post:
        post()
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    com = D.recentre(roots, com_fn() if com_fn else D.centre_of_mass(meshes))
    print(f"[items3] {name}: centre of mass moved to origin (was {tuple(round(c, 4) for c in com)})")
    POINTS.clear()
    M.refresh()
    for o in [o for o in bpy.context.scene.objects if o.name.startswith("QA_pt_")]:
        POINTS[o.name[6:]] = o.matrix_world.translation.copy()       # report points, never exported
        bpy.data.objects.remove(o, do_unlink=True)
    tidy_mesh_names()
    path = D.export(name)
    D.describe(name)
    C.summary(name, budget)
    C.require(required)
    budget_report(name, path, budget, surf_budget, mat_budget)
    check_names(path)
    if extra_report:
        extra_report()
    C.backface_check()
    if D.want_render() and shots:
        D.qa_tweak()
        lo, _ = D.bounds()
        for s in shots:
            suffix, cam, target, lens = s[:4]
            if len(s) > 4 and s[4] is not None:
                s[4]()
            C.shot(f"item_{name}{suffix}", cam, target, lens=lens, floor_z=lo.z - 0.0002, lights=C.LIGHTS,
                   samples=28, res=(800, 600))


def godot(p) -> tuple:
    """Blender point -> Godot tuple (rounded for printing)."""
    return (round(p[0], 4), round(p[2], 4), round(-p[1], 4))


def report_point(label: str, obj_name: str | None = None, point=None) -> None:
    """Print a named point (an object's origin or an explicit Blender point) in Godot model coordinates."""
    M.refresh()
    if obj_name is not None:
        p = bpy.data.objects[obj_name].matrix_world.translation
    else:
        p = Vector(point)
    print(f"[items3] point {label}: godot {godot(p)}")


def mat_x(deg: float) -> Matrix:
    return Matrix.Rotation(math.radians(deg), 4, "X")


# ---------------------------------------------------------------- Castell isolator keys (key_diamond ... key_square)
KEY_LEN = 0.085            # bow top -> blade tip
KEY_BOW_W = 0.034          # every bow is 34 mm across
KEY_BOW_T = 0.0030         # bow plate thickness
KEY_SHANK_R = 0.0060       # round shank Ø 12 mm
KEY_NECK = 0.0040          # neck between the bow and the collar
KEY_COLLAR = 0.0030
KEY_HOLE_R = 0.0016        # hanging hole Ø 3.2 mm
# per bow: (symbol height for a 34 mm width, emboss height, emboss centre dy, hole centre dy from the bow top,
#           corner radius) -- dy measured in Blender +Y (= toward the bow top)
KEY_BOWS = {
    "diamond": (KEY_BOW_W, 0.0140, -0.0020, 0.0070, 0.0026),
    "triangle": (KEY_BOW_W * math.sqrt(3.0) / 2.0, 0.0110, -0.0031, 0.0085, 0.0026),
    "circle": (KEY_BOW_W, 0.0150, -0.0025, 0.0055, 0.0),
    "square": (KEY_BOW_W, 0.0150, -0.0030, 0.0055, 0.0030),
}


def castell_key(kind: str, name: str):
    """A Castell-style trapped-key interlock key lying flat (hero face up = Blender +Z), the bow toward Blender +Y
    (Godot -Z), the blade toward Blender -Y (Godot +Z). Bow: a 3 mm brass plate shaped like the symbol (from
    lib_ch3_symbols, corners rounded), 34 mm across, the same symbol embossed (0.8 mm relief) on its face and a
    Ø 3.2 mm hanging hole near its top. Then a turned neck and collar, a round brass shank Ø 12 mm with a
    chamfered tip, and a flat dark-steel bit with two code cuts sticking out toward +X along the shank's end.
    Returns (root, info): root = the brass key (bow, emboss, shank), child `key_bit` (M_Steel_Dark);
    info holds Blender points: hole centre, collar face (where a lock face stops it), blade tip."""
    S = symbols()
    if S is None:
        raise RuntimeError("lib_ch3_symbols is not available: pull origin main first")
    h, he, edy, hdy, cr = KEY_BOWS[kind]
    outline = S.shapes(kind, h)[0][0]
    if cr > 0:
        outline = rounded_poly(outline, cr, 4)
        w = max(p[0] for p in outline) - min(p[0] for p in outline)
        outline = scale_loop(outline, KEY_BOW_W / w)        # rounding shrinks it: back to 34 mm across
    y0, y1 = min(p[1] for p in outline), max(p[1] for p in outline)
    bow_h = y1 - y0
    # bow top at Blender y = 0, the blade toward -y
    outline = [(x, y - y1) for (x, y) in outline]
    yc = -bow_h / 2
    if kind == "triangle":
        yc = -bow_h + bow_h / 3.0                      # incircle centre
    hole = L.circle(KEY_HOLE_R, 12, cx=0.0, cy=-hdy)
    bow = plate_xy(name, [outline, hole], KEY_BOW_T, -KEY_BOW_T / 2, "M_Brass_Aged", bevel=0.0006)
    emb = S.inlay("emboss", kind, he, depth=0.0008, mat="M_Brass_Aged", bevel=0.0003)
    ecx = 0.0
    ecy = yc + edy
    if kind == "triangle":                             # the emboss's incircle centre on the bow's
        ecy = yc + he / 6.0
    emb.data.transform(Matrix.Translation((ecx, ecy, KEY_BOW_T / 2 - 0.00005)))
    # neck, collar and shank along -Y
    yb = -bow_h                                        # bow bottom
    tip = -KEY_LEN
    r = KEY_SHANK_R
    prof = [(0.0, -0.0030), (0.0040, -0.0030), (0.0045, 0.0), (0.0045, KEY_NECK - 0.0008),
            (0.0060, KEY_NECK), (0.0072, KEY_NECK + 0.0006), (0.0072, KEY_NECK + KEY_COLLAR - 0.0006),
            (0.0066, KEY_NECK + KEY_COLLAR), (r, KEY_NECK + KEY_COLLAR + 0.0004),
            (r, -tip + yb - 0.0018), (r - 0.0014, -tip + yb), (0.0, -tip + yb)]
    shank = D.revolve("shank", prof, direction=(0, -1, 0), loc=(0, yb, 0), segments=16, mat="M_Brass_Aged",
                      up_hint=(0, 0, 1))
    # the flat steel bit: along the last 22 mm of the shank, out to x = 13 mm, two code cuts
    b0, b1 = tip + 0.0025, tip + 0.0245
    xo = r + 0.0068
    pts = [(r - 0.0015, b0), (xo, b0), (xo, b0 + 0.0050), (xo - 0.0030, b0 + 0.0050), (xo - 0.0030, b0 + 0.0085),
           (xo, b0 + 0.0085), (xo, b0 + 0.0140), (xo - 0.0045, b0 + 0.0140), (xo - 0.0045, b0 + 0.0170),
           (xo, b0 + 0.0170), (xo, b1 - 0.0015), (xo - 0.0015, b1), (r - 0.0015, b1)]
    bit = plate_xy("key_bit", [pts], 0.0024, -0.0012, "M_Steel_Dark", bevel=0.0003)
    root = M.join([bow, emb, shank], name)
    M.set_parent(bit, root)
    info = {"hole": Vector((0.0, -hdy, 0.0)), "collar": Vector((0.0, yb - KEY_NECK - KEY_COLLAR, 0.0)),
            "tip": Vector((0.0, tip, 0.0)), "bow_top": Vector((0.0, 0.0, 0.0)), "bow_h": bow_h}
    return root, info


def key_item(kind: str) -> None:
    """Build, export and QA one isolator key (key_<kind>.glb)."""
    name = f"key_{kind}"
    INFO.clear()

    def build():
        root, info = castell_key(kind, name)
        INFO.update(info)
        # empties only for the report (removed before export)
        for k in ("hole", "collar", "tip"):
            M.empty(f"QA_pt_{k}", loc=tuple(info[k]))
        return [root]

    def post():
        D.resmooth(bpy.data.objects[name], 32.0)

    def report():
        for k, p in POINTS.items():
            g = godot(p)
            hang = (g[0], round(-g[2], 4), g[1])          # Basis(X, +90 deg): (x, y, z) -> (x, -z, y)
            print(f"[items3] key {k}: natural pose godot {g}; hanging (mount basis +90 deg about X) {hang}")
        print(f"[items3] key bow height {INFO['bow_h']:.4f}")

    item_main(name, build, post=post, required=("key_bit",), budget=1200, extra_report=report, shots=[
        ("", (0.05, -0.12, 0.13), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.22), (0.0, -0.002, 0.0), 50),
    ])


INFO: dict = {}
