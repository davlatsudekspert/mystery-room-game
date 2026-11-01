"""MYSTERY ROOM — helpers of the Cold Store (R4) models: room_cold, carriage_1..5, frost_window, cold_chest, film_can_1..4.

On top of lib_ch2x (never edits it). Godot coordinates, metres.
  disc_decal(...)     round decal disc (planar UV 0..1 over the bounding square) facing a Godot axis
  quad_decal(...)     rectangular decal quad with UV 0..1 or a sub-rectangle (atlas cell)
  ring_face(...)      flat annulus with planar UV over its OUTER bounding square (chest rings, 0..1)
  frost_crust(...)    rough white frost lumps (M_Porcelain) hugging a surface, deterministic
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
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import C, G, GV, gbox, gcyl, glathe, part, mount  # noqa: E402,F401

M.PREVIEW.update({
    "M_Decal_FrostPatch": ("E8F2F8", 0.9, 0.0, None, 0.8),
    "M_Enamel_Ice": ("C6D6E2", 0.45, 0.2, None, 1.0),
    "M_Emissive_Cold": ("D8EEFF", 0.4, 0.0, "D8EEFF", 1.0),
    "M_Decal_FrostSign": ("E2F0F8", 0.8, 0.0, None, 0.9),
    "M_Decal_CanLabel_1": ("C4A03C", 0.6, 0.0, None, 1.0),
    "M_Decal_CanLabel_2": ("5A82AA", 0.6, 0.0, None, 1.0),
    "M_Decal_CanLabel_3": ("A84634", 0.6, 0.0, None, 1.0),
    "M_Decal_CanLabel_4": ("78966E", 0.6, 0.0, None, 1.0),
    "M_Decal_ChestPlate": ("96784E", 0.45, 0.6, None, 1.0),
    "M_Decal_FrostPane": ("E4F0F6", 0.8, 0.0, None, 0.78),
})


def _uv_planar(bm, fn):
    lay = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for lp in f.loops:
            lp[lay].uv = fn(lp.vert.co)


def disc_decal(name: str, r: float, centre, axis: str, mat: str, segs: int = 28, r_in: float = 0.0):
    """Flat disc (annulus when r_in > 0) facing the Godot `axis`, UV 0..1 over the outer bounding square."""
    bm = bmesh.new()
    outer = [bm.verts.new((math.cos(2 * math.pi * i / segs) * r, math.sin(2 * math.pi * i / segs) * r, 0)) for i in range(segs)]
    if r_in > 0:
        inner = [bm.verts.new((math.cos(2 * math.pi * i / segs) * r_in, math.sin(2 * math.pi * i / segs) * r_in, 0)) for i in range(segs)]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    else:
        bm.faces.new(outer)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    _uv_planar(bm, lambda co: (co.x / (2 * r) + 0.5, co.y / (2 * r) + 0.5))
    o = A.obj_from_bm(name, bm, mat)
    C.aim(o, axis)
    o.data.transform(Matrix.Translation(GV(centre)))
    return o


def quad_decal(name: str, centre, u_axis, v_axis, w: float, h: float, mat: str, uv=None):
    return C.gquad(name, centre, u_axis, v_axis, w, h, mat, uv=uv)


def frost_crust(prefix: str, spots, mat="M_Porcelain", seed=1, sides=7):
    """spots: [(godot centre, radius, height, axis)] -> one object of low flattened lumps (hoarfrost)."""
    import random
    rnd = random.Random(seed)
    objs = []
    for i, (c, r, h, ax) in enumerate(spots):
        o = M.sphere(f"{prefix}{i}", 1.0, segments=sides, rings=4, mat=mat, scale=(r * rnd.uniform(0.8, 1.2), r * rnd.uniform(0.8, 1.2), h))
        A.place(o, Matrix.Identity(4))
        C.aim(o, ax)
        o.data.transform(Matrix.Translation(GV(c)))
        objs.append(o)
    return M.join(objs, prefix) if len(objs) > 1 else objs[0]


def retex() -> None:
    """After qa_import: swap imported plain materials (name.001) for the textured preview materials (same slot names)."""
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            base = m.name.split(".")[0]
            if base.startswith("M_"):
                o.data.materials[i] = M.material(base)


def qa_frost_material(wipe_band: int = -1, uv_tiles: float = 2.2) -> None:
    """QA only: make the M_Decal_FrostPane preview material show decals/ch2x/frost_tex.png (alpha = frost) and optionally wipe the
    band `wipe_band` (0 top, 1 middle, 2 bottom; -1 = fully frosted), emulating the game shader's wipe_mask."""
    mat = M.material("M_Decal_FrostPane")
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (uv_tiles, uv_tiles * 1.5, 1.0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(X.DECALS, "frost_tex.png"), check_existing=True)
    tex.extension = "REPEAT"
    tex.image.alpha_mode = "CHANNEL_PACKED"
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    alpha = tex.outputs["Alpha"]
    if wipe_band >= 0:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["UV"], sep.inputs["Vector"])
        sub = nt.nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = 1.0 - (wipe_band + 0.5) / 3.0
        nt.links.new(sep.outputs["Y"], sub.inputs[0])
        ab = nt.nodes.new("ShaderNodeMath")
        ab.operation = "ABSOLUTE"
        nt.links.new(sub.outputs["Value"], ab.inputs[0])
        rg = nt.nodes.new("ShaderNodeMapRange")
        rg.inputs["From Min"].default_value = 0.150
        rg.inputs["From Max"].default_value = 0.172
        nt.links.new(ab.outputs["Value"], rg.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(alpha, mul.inputs[0])
        nt.links.new(rg.outputs["Result"], mul.inputs[1])
        alpha = mul.outputs["Value"]
    nt.links.new(alpha, b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.65
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"


def decal_alpha(slot: str, fname: str) -> None:
    """QA only: decal slot whose PNG alpha drives the preview alpha (stencils, finger-writing)."""
    mat = X.decal(slot, fname)
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    if tex is None:
        return
    tex.image.alpha_mode = "CHANNEL_PACKED"
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"


def preview_glow() -> None:
    """QA: emission strengths of the cold emissive slots (the window glow, tube light)."""
    for n, st in (("M_Emissive_Cold", 5.0),):
        m = bpy.data.materials.get(n)
        if m and m.node_tree:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Emission Color"].default_value = M.hex_rgba("D8EEFF")
            b.inputs["Emission Strength"].default_value = st
