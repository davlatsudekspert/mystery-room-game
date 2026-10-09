"""MYSTERY ROOM — Chapter 2 inventory-item helpers (build group D2, `items2`).

Builds on mrlib, lib_mech and lib_devices (never edits them). Same pipeline as the Chapter 1 items
(lib_devices.item_main): reset, build, finalize (box UVs + smoothing), optional post step (decal UVs),
move the centre of mass to the origin, export game/assets/models/<name>.glb, QA renders.
Differences: QA renders go to qa/blender/ch2/, Cycles uses 2 fixed threads (shared machine), the
Chapter 2 material slots are created with their contract preview colours, decal slots load their
images from game/assets/textures/decals/ch2/ when they exist, and every build checks its required
part names (own objects, identity rotation at rest).

Conventions: metres, Blender Z-up; Godot = Blender (x, z, -y). Flat items are built lying in the
Blender XY plane with the hero face up (+Z) and their top edge toward Blender +Y (= Godot -Z), so the
70 deg inspect tilt (ItemDB.view_tilt) shows them upright. Standing items face Blender -Y (= Godot +Z).
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402

ROOT = M.ROOT
DECALS_CH2 = os.path.join(ROOT, "game", "assets", "textures", "decals", "ch2")
QA_SUB = "ch2"
TAU = 2.0 * math.pi

# Chapter 2 slots (docs/models/ch2.md section 0) plus library slots mrlib.PREVIEW does not know.
# name: (hex, roughness, metallic, alpha)
CH2_SLOTS = {
    "M_Velvet": ("5A1420", 0.9, 0.0, 1.0),
    "M_Film": ("3A2414", 0.25, 0.0, 0.9),
    "M_Tape": ("4A2C1A", 0.35, 0.0, 1.0),
    "M_Cardboard": ("9A7B55", 0.85, 0.0, 1.0),
    "M_Linen": ("8C7B5E", 0.8, 0.0, 1.0),
    "M_Steel_Cream": ("D8CFB4", 0.4, 0.1, 1.0),
    "M_Lacquer_Black": ("141211", 0.32, 0.0, 1.0),     # game/assets/materials/M_Lacquer_Black.tres
}

# decal slot -> image file in DECALS_CH2 (group F); (fallback preview colour, alpha-wired in QA)
DECALS = {
    "M_Decal_Badge": ("badge.png", "E6DCC4", False),
    "M_Decal_IndexCard": ("index_card.png", "E9DFC6", False),
    "M_Decal_RequestCard": ("request_card.png", "D9C495", False),
    "M_Decal_FileCover": ("file_cover.png", "CDB27A", False),
    "M_Decal_TapeLabel_1996": ("tape_label_1996.png", "E8DFC8", False),
    "M_Decal_SlideMark": ("slide_mark.png", "D8E0DC", True),
}


def decal_path(slot: str) -> str:
    return os.path.join(DECALS_CH2, DECALS[slot][0])


def ensure_materials() -> None:
    D.ensure_materials()
    for name, (hx, rough, metal, alpha) in CH2_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)
    for slot, (fname, hx, use_alpha) in DECALS.items():
        if bpy.data.materials.get(slot) is not None:
            continue
        path = os.path.join(DECALS_CH2, fname)
        if os.path.exists(path):
            mat = M.material(slot, color="FFFFFF", rough=0.6, metal=0.0, image=path)
            if use_alpha:
                nt = mat.node_tree
                tex = [n for n in nt.nodes if n.type == "TEX_IMAGE"][0]
                bsdf = nt.nodes["Principled BSDF"]
                if tex.image is not None and tex.image.channels == 4:
                    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
                    if hasattr(mat, "surface_render_method"):
                        mat.surface_render_method = "BLENDED"
        else:
            M.material(slot, color=hx, rough=0.6, metal=0.0, image="")


def have_decal(slot: str) -> bool:
    return os.path.exists(decal_path(slot))


# ---------------------------------------------------------------- geometry helpers
def mesh_from(name: str, verts, faces, mat: str) -> bpy.types.Object:
    return D.mesh(name, verts, faces, mat=mat)


def polygon_face(name: str, pts, z: float, mat: str, up: bool = True) -> bpy.types.Object:
    """Single n-gon (convex or star-shaped outline) in the plane z, facing +Z (or -Z)."""
    verts = [(x, y, z) for (x, y) in pts]
    face = list(range(len(pts)))
    obj = mesh_from(name, verts, [face], mat)
    n = obj.data.polygons[0].normal
    if (n.z < 0) == up:
        obj.data.flip_normals()
    return obj


def disc_face(name: str, r: float, n: int, z: float, mat: str, cx: float = 0.0, cy: float = 0.0,
              up: bool = True) -> bpy.types.Object:
    return polygon_face(name, L.circle(r, n, cx=cx, cy=cy), z, mat, up=up)


def uv_rect_all(obj, x0: float, x1: float, y0: float, y1: float, axis: str = "Z") -> None:
    """0..1 planar UVs for every face of obj over the rectangle [x0, x1] x [y0, y1] (mesh-local).
    axis Z: u from X, v from Y. axis Y (front plates facing -Y): u from X, v from Z."""
    L.planar_uv_rect(obj, x0, x1, y0, y1, axis=axis, material_prefix="")


def drop_cap(obj, z: float, up: bool = True, tol: float = 2e-6) -> None:
    """Delete the flat cap faces of obj lying in the plane z (normal +Z if up, else -Z)."""
    def pred(c, n):
        return abs(c.z - z) < tol and ((n.z > 0.99) if up else (n.z < -0.99))
    L.drop_faces(obj, lambda c, n: pred(c, n))


def bend_y(obj, y0: float, radius: float) -> None:
    """Curl a flat sheet (lying in z ~ 0) upward beyond y > y0 around an X-parallel axis."""
    for v in obj.data.vertices:
        if v.co.y > y0:
            s = v.co.y - y0
            a = s / radius
            z = v.co.z
            v.co.y = y0 + (radius - z) * math.sin(a)
            v.co.z = radius - (radius - z) * math.cos(a)
    obj.data.update()


def parent_all(children, parent) -> None:
    for c in children:
        M.set_parent(c, parent)


# ---------------------------------------------------------------- checks
def require(names) -> bool:
    """Every required part exists, is its own object, and is at an identity rotation / unit scale."""
    ok = True
    M.refresh()
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            print(f"[items2] MISSING part {nm}")
            ok = False
            continue
        q = o.matrix_local.to_quaternion()
        s = o.matrix_local.to_scale()
        ident = abs(abs(q.w) - 1.0) < 1e-6 and all(abs(c - 1.0) < 1e-6 for c in s)
        loc = o.matrix_world.translation
        g = (loc.x, loc.z, -loc.y)
        print(f"[items2] part {nm:14s} parent={o.parent.name if o.parent else '-':16s} "
              f"pivot(godot)=({g[0]:+.4f}, {g[1]:+.4f}, {g[2]:+.4f}) identity={'yes' if ident else 'NO'}")
        ok = ok and ident
    print(f"[items2] required parts: {'OK' if ok else 'FAILED'}")
    return ok


def godot_bounds():
    lo, hi = D.bounds()
    # Blender (x, y, z) -> Godot (x, z, -y)
    glo = Vector((lo.x, lo.z, -hi.y))
    ghi = Vector((hi.x, hi.z, -lo.y))
    return glo, ghi


def summary(name: str, budget: int = 2500) -> None:
    glo, ghi = godot_bounds()
    size = ghi - glo
    tris = M.tri_count()
    print(f"[items2] {name}: tris={tris} (budget {budget}: {'OK' if tris <= budget else 'OVER'}) "
          f"size godot(x,y,z)=({size.x:.4f}, {size.y:.4f}, {size.z:.4f}) bottom y={glo.y:+.4f} "
          f"min={tuple(round(c, 4) for c in glo)} max={tuple(round(c, 4) for c in ghi)}")


# ---------------------------------------------------------------- QA
def setup_threads() -> None:
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2


def shot(name: str, cam, target, lens: float = 50.0, floor_z: float | None = 0.0, samples: int = 28,
         res=(800, 600), lights=None, world: float = 0.25) -> str:
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    setup_threads()
    return D.shot(f"{QA_SUB}/{name}", cam, target, lens=lens, floor_z=floor_z, samples=samples, res=res,
                  lights=lights, world=world)


def item_main(name: str, build_fn, shots=(), post=None, required=(), budget: int = 2500) -> None:
    """shots: [(suffix, cam_loc, target, lens[, pose_fn])], Blender coordinates relative to the centred
    item; a floor is put under the item's lowest point. pose_fn() runs before its shot (QA only, after
    the export) and its pose stays for the following shots."""
    M.reset_scene()
    ensure_materials()
    build_fn()
    M.finalize()
    if post:
        post()
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    com = D.recentre(roots, D.centre_of_mass(meshes))
    print(f"[items2] {name}: centre of mass moved to origin (was {tuple(round(c, 4) for c in com)})")
    D.export(name)
    D.describe(name)
    summary(name, budget)
    require(required)
    if D.want_render() and shots:
        D.qa_tweak()
        lo, _ = D.bounds()
        for s in shots:
            suffix, cam, target, lens = s[:4]
            if len(s) > 4 and s[4] is not None:
                s[4]()
            shot(f"item_{name}{suffix}", cam, target, lens=lens, floor_z=lo.z - 0.0003)
