"""Blender (headless) QA renders for the CC0 props.

    blender -b --factory-startup -P tools/models_cc0/render_qa.py -- \
        --out-dir <dir> [--size 512] [--samples 32] a.glb b.glb ...

Writes <dir>/<id>.png per prop (3/4 front view, neutral grey studio, Cycles CPU) and
<dir>/_lineup_desk.png and <dir>/_lineup_floor.png (props side by side at real scale on a
checker floor: 0.1 m squares for desk-scale props, 0.5 m squares for floor-scale props).
Each prop is rendered exactly as exported (no re-centering), so a prop that floats, sinks
or lies on its side shows up immediately against the floor plane.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--floor", default="", help="comma-separated ids of floor-scale props")
    ap.add_argument("glbs", nargs="+")
    return ap.parse_args(argv)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_render(w, h, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    world = bpy.data.worlds.new("QA_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.20, 0.20, 0.21, 1)
    bg.inputs["Strength"].default_value = 0.35
    sc.world = world


def grey_material(name, value, grid=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (value, value, value, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
    if grid:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        chk = nt.nodes.new("ShaderNodeTexChecker")
        chk.inputs["Scale"].default_value = 1.0
        chk.inputs["Color1"].default_value = (value, value, value, 1)
        chk.inputs["Color2"].default_value = (value * 0.8, value * 0.8, value * 0.8, 1)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (1.0 / (2 * grid), 1.0 / (2 * grid), 1.0)
        nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], chk.inputs["Vector"])
        nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def add_floor(size, grid=None, z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    floor = bpy.context.active_object
    floor.data.materials.append(grey_material("QA_Floor", 0.30, grid))
    return floor


def add_area(name, loc, target, size, energy):
    data = bpy.data.lights.new(name, "AREA")
    data.size = size
    data.energy = energy
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    d = Vector(target) - Vector(loc)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return obj


def bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def studio(center, radius):
    r = max(radius, 0.05)
    k = r / 0.5  # light energy scaled with prop size (area light falloff)
    add_area("Key", center + Vector((-2.2, -2.6, 2.6)) * r * 2, center, 2.5 * r * 2, 260 * k * k)
    add_area("Fill", center + Vector((2.8, -1.6, 1.2)) * r * 2, center, 3.0 * r * 2, 70 * k * k)
    add_area("Rim", center + Vector((0.5, 3.0, 2.4)) * r * 2, center, 2.0 * r * 2, 160 * k * k)


def camera(center, radius, azimuth_deg=-32, elev_deg=22, lens=50, ortho_scale=None, w=1, h=1):
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    az, el = math.radians(azimuth_deg), math.radians(elev_deg)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    if ortho_scale:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho_scale
        dist = radius * 4 + 2
    else:
        cam_data.lens = lens
        fov = 2 * math.atan(cam_data.sensor_width / (2 * lens))
        dist = radius / math.sin(fov / 2) * 1.08
    cam_data.clip_start = max(0.001, dist * 0.01)
    cam_data.clip_end = dist * 10
    cam.location = center + direction * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    a = parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    for glb in a.glbs:
        name = os.path.splitext(os.path.basename(glb))[0]
        reset()
        setup_render(a.size, a.size, a.samples)
        objs = import_glb(os.path.abspath(glb))
        lo, hi = bbox(objs)
        center = (lo + hi) / 2
        radius = (hi - lo).length / 2
        # floor under the lowest point (a hanging prop has its origin at the top)
        add_floor(max(radius * 40, 4), z=min(0.0, lo.z))
        studio(center, radius)
        camera(center, radius)
        render(os.path.join(a.out_dir, f"{name}.png"))
        print("QA_RENDERED", name)

    # real-scale line-ups: desk-scale props and floor-scale props (each rests on the floor)
    floor_ids = set(a.floor.split(","))
    large = [g for g in a.glbs if os.path.splitext(os.path.basename(g))[0] in floor_ids]
    small = [g for g in a.glbs if g not in large]
    for tag, group in (("_lineup_desk", small), ("_lineup_floor", large)):
        if group:
            lineup(group, os.path.join(a.out_dir, f"{tag}.png"), a.size * 2, a.size, a.samples)
            print("QA_RENDERED", tag)


def lineup(glbs, path, w, h, samples):
    reset()
    setup_render(w, h, samples)
    x = 0.0
    gap = 0.05
    all_objs = []
    for glb in glbs:
        objs = import_glb(os.path.abspath(glb))
        lo, hi = bbox(objs)
        shift = Vector((x - lo.x, 0, -lo.z))
        for o in [o for o in objs if o.parent is None]:
            o.location += shift
        bpy.context.view_layer.update()
        x += (hi.x - lo.x) + gap
        all_objs += objs
    lo, hi = bbox(all_objs)
    for o in [o for o in all_objs if o.parent is None]:
        o.location.x -= (lo.x + hi.x) / 2
    bpy.context.view_layer.update()
    lo, hi = bbox(all_objs)
    center = (lo + hi) / 2
    width, height = hi.x - lo.x, hi.z - lo.z
    grid = 0.1 if height < 0.8 else 0.5
    add_floor(60, grid=grid)
    studio(center, max(width, height) / 2)
    camera(center, width / 2, azimuth_deg=0, elev_deg=10,
           ortho_scale=max(width * 1.06, height * 1.3 * w / h))
    render(path)


main()
