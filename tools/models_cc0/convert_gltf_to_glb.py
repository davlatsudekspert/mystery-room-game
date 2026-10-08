"""Blender (headless) conversion of a downloaded Poly Haven glTF into a game-ready .glb.

Run via tools/models_cc0/fetch_cc0_models.py, or directly:
    blender -b --factory-startup -P tools/models_cc0/convert_gltf_to_glb.py -- \
        --in <src.gltf> --out <dst.glb> --target-tris 8000 [--keep a,b] \
        [--move NAME=dx,dy,dz ...] [--drop NAME ...] [--smooth-angle 40] [--stats out.json]

Steps:
  * import glTF (vertices merged so the decimator sees connected surfaces)
  * optional: keep only objects whose name contains one of --keep, move objects (Blender
    Z-up metres) and drop an object onto whatever lies under it (e.g. a cup onto its saucer)
  * optional baked rotation (--rotate), then pivot normalisation (--pivot bottom|top|keep)
  * decimate (collapse) to --target-tris; objects under 300 tris are left untouched; decimated
    objects get fresh smooth-by-angle normals, untouched objects keep their authored normals
  * glass: Godot ignores KHR_materials_transmission and the source glass materials use an
    RGB JPG as base colour (alpha = 1), so glass would render opaque. Every BLEND/transmissive
    material whose name contains glass/lens gets a constant alpha (GLASS_ALPHA) instead
  * export one .glb, Y-up, textures embedded byte-for-byte in their original JPG format (1K)
  * patch the .glb JSON so materials using a Poly Haven ARM map also use its R channel as
    occlusionTexture (standard glTF ORM packing; the source files leave AO unused)
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

GLASS_ALPHA = 0.18
SMALL_OBJECT_TRIS = 300


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-tris", type=int, default=15000)
    ap.add_argument("--keep", default="")
    ap.add_argument("--move", action="append", default=[])
    ap.add_argument("--drop", action="append", default=[])
    ap.add_argument("--smooth-angle", type=float, default=40.0)
    ap.add_argument("--rotate", default="", help="rx,ry,rz degrees (Blender axes) applied to the whole prop")
    ap.add_argument("--pivot", choices=["bottom", "top", "keep"], default="bottom",
                    help="bottom: lowest point at y=0 (props that stand); top: highest point at y=0 (hanging props)")
    ap.add_argument("--stats", default="")
    return ap.parse_args(argv)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def tri_count(obj) -> int:
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def total_tris() -> int:
    return sum(tri_count(o) for o in mesh_objects())


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0] if objs else None


def apply_keep(keep: list[str]):
    if not keep:
        return
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and not any(k == o.name or k in o.name for k in keep):
            bpy.data.objects.remove(o, do_unlink=True)
    # drop empties that no longer have children
    for o in list(bpy.context.scene.objects):
        if o.type == "EMPTY" and not o.children:
            bpy.data.objects.remove(o, do_unlink=True)


def find(name: str):
    obj = bpy.context.scene.objects.get(name)
    if obj is None:
        raise SystemExit(f"object not found: {name}")
    return obj


def apply_moves(moves: list[str]):
    for spec in moves:
        name, vec = spec.split("=")
        d = Vector(float(v) for v in vec.split(","))
        find(name).location += d
    bpy.context.view_layer.update()


def drop_onto(name: str):
    """Lower/raise `name` so its lowest vertices rest on the surfaces below it."""
    obj = find(name)
    others = [o for o in mesh_objects() if o is not obj]
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    zmin = min(p.z for p in pts)
    low = [p for p in pts if p.z < zmin + 0.004]
    best = None
    for p in low[:: max(1, len(low) // 200)]:
        origin = Vector((p.x, p.y, p.z + 0.5))
        for o in others:
            inv = o.matrix_world.inverted()
            lo = inv @ origin
            ld = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
            hit, loc, _n, _i = o.ray_cast(lo, ld)
            if hit:
                wz = (o.matrix_world @ loc).z
                gap = p.z - wz
                best = gap if best is None else min(best, gap)
    if best is not None:
        obj.location.z -= best
        bpy.context.view_layer.update()


def smooth_by_angle(obj, angle_deg: float):
    select_only([obj])
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except RuntimeError:
        pass
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg), keep_sharp_edges=False)


def decimate(target: int, smooth_angle: float) -> list[str]:
    touched = []
    for _ in range(4):
        objs = mesh_objects()
        counts = {o.name: tri_count(o) for o in objs}
        total = sum(counts.values())
        if total <= target * 1.02:
            break
        fixed = sum(c for c in counts.values() if c < SMALL_OBJECT_TRIS)
        decim = total - fixed
        ratio = max(0.03, min(1.0, (target - fixed) / max(1, decim)))
        for o in objs:
            if counts[o.name] < SMALL_OBJECT_TRIS:
                continue
            if o.data.users > 1:
                o.data = o.data.copy()
            m = o.modifiers.new("cc0_decimate", "DECIMATE")
            m.decimate_type = "COLLAPSE"
            m.ratio = ratio
            m.use_collapse_triangulate = True
            select_only([o])
            bpy.ops.object.modifier_apply(modifier=m.name)
            if o.name not in touched:
                touched.append(o.name)
    for name in touched:
        smooth_by_angle(bpy.context.scene.objects[name], smooth_angle)
    return touched


def roots():
    return [o for o in bpy.context.scene.objects if o.parent is None]


def apply_rotation(spec: str):
    if not spec:
        return
    from mathutils import Euler
    rot = Euler([math.radians(float(v)) for v in spec.split(",")], "XYZ").to_matrix().to_4x4()
    for o in roots():
        o.matrix_world = rot @ o.matrix_world
    bpy.context.view_layer.update()


def apply_pivot(mode: str):
    """Move the whole prop vertically so the node origin is on its base (or its top)."""
    if mode == "keep":
        return
    lo, hi = scene_bbox()
    dz = -lo.z if mode == "bottom" else -hi.z
    for o in roots():
        o.location.z += dz
    bpy.context.view_layer.update()


def is_glass_name(mat_name: str, asset_id: str) -> bool:
    # Only look at the part after the asset id: "magnifying_glass_01" is the frame,
    # "magnifying_glass_01_lense" is the lens.
    n = mat_name.lower()
    if asset_id and n.startswith(asset_id.lower()):
        n = n[len(asset_id):]
    tokens = set(t for t in n.replace(".", "_").split("_") if t)
    return bool(tokens & {"glass", "lens", "lense"})


def fix_glass(asset_id: str) -> list[str]:
    fixed = []
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = next((nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        trans = bsdf.inputs.get("Transmission Weight")
        is_trans = trans is not None and (trans.is_linked or trans.default_value > 0.0)
        if not (is_glass_name(mat.name, asset_id) or is_trans):
            continue
        alpha = bsdf.inputs["Alpha"]
        for link in list(alpha.links):
            mat.node_tree.links.remove(link)
        alpha.default_value = GLASS_ALPHA
        rough = bsdf.inputs["Roughness"]
        if not rough.is_linked:
            rough.default_value = min(rough.default_value, 0.08)
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            pass
        fixed.append(mat.name)
    return fixed


def add_orm_occlusion(glb_path: str) -> list[str]:
    """Poly Haven ARM maps pack AO in R, roughness in G, metal in B (glTF ORM layout), but the
    source glTF never references the AO channel. Point occlusionTexture at the same texture so
    Godot gets baked AO for free. Only the JSON chunk of the .glb is rewritten."""
    import struct

    with open(glb_path, "rb") as f:
        data = f.read()
    magic, version, _length = struct.unpack("<4sII", data[:12])
    jlen, jtype = struct.unpack("<II", data[12:20])
    assert magic == b"glTF" and jtype == 0x4E4F534A
    gltf = json.loads(data[20:20 + jlen])
    rest = data[20 + jlen:]
    changed = []
    for mat in gltf.get("materials", []):
        mr = mat.get("pbrMetallicRoughness", {}).get("metallicRoughnessTexture")
        if mr is None or "occlusionTexture" in mat:
            continue
        tex = gltf["textures"][mr["index"]]
        img = gltf["images"][tex["source"]]
        if "_arm" in img.get("name", "").lower():
            occ = {"index": mr["index"]}
            if "texCoord" in mr:
                occ["texCoord"] = mr["texCoord"]
            mat["occlusionTexture"] = occ
            changed.append(mat["name"])
    if changed:
        js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        js += b" " * ((4 - len(js) % 4) % 4)
        body = struct.pack("<II", len(js), 0x4E4F534A) + js + rest
        with open(glb_path, "wb") as f:
            f.write(struct.pack("<4sII", magic, version, 12 + len(body)) + body)
    return changed


def scene_bbox():
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in mesh_objects():
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def main():
    a = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.src), merge_vertices=True)
    src_tris = total_tris()
    apply_keep([k for k in a.keep.split(",") if k])
    kept_tris = total_tris()
    apply_moves(a.move)
    for name in a.drop:
        drop_onto(name)
    touched = decimate(a.target_tris, a.smooth_angle)
    apply_rotation(a.rotate)
    apply_pivot(a.pivot)
    asset_id = os.path.splitext(os.path.basename(a.out))[0]
    glass = fix_glass(asset_id)
    tris = total_tris()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(a.out), export_format="GLB", export_image_format="AUTO",
        export_yup=True, export_apply=True, export_materials="EXPORT", export_texcoords=True,
        export_normals=True, export_animations=False, export_cameras=False, export_lights=False,
        export_extras=False, use_selection=False)
    occlusion = add_orm_occlusion(os.path.abspath(a.out))

    lo, hi = scene_bbox()
    size = hi - lo
    imgs = sorted({(i.name, tuple(i.size)) for i in bpy.data.images if i.size[0] > 0})
    stats = {
        "src_tris": src_tris,
        "kept_tris": kept_tris,
        "tris": tris,
        "decimated_objects": touched,
        "glass_materials_alpha": glass,
        "orm_occlusion_added": occlusion,
        "objects": {o.name: tri_count(o) for o in mesh_objects()},
        "materials": sorted({s.material.name for o in mesh_objects() for s in o.material_slots if s.material}),
        "images": [[n, list(s)] for n, s in imgs],
        # glTF / Godot axes: X = width, Y = height (up), Z = depth
        "dims_m": [round(size.x, 3), round(size.z, 3), round(size.y, 3)],
        "bbox_min_gltf": [round(lo.x, 3), round(lo.z, 3), round(-hi.y, 3)],
        "bbox_max_gltf": [round(hi.x, 3), round(hi.z, 3), round(-lo.y, 3)],
    }
    if a.stats:
        with open(a.stats, "w") as f:
            json.dump(stats, f, indent=1)
    print("CC0_STATS", json.dumps(stats))


main()
