"""lumen_shard.glb — a small Lumen crystal shard (5 collectibles in Lab 7, visible under UV).

Item model: origin at the centre of mass (the lead spawns it at floor spots with y = 0.02 and a random yaw).
It lies on its side: the lowest point is ~2 cm below the origin, so a spawn at y = 0.02 rests on the floor.
Single mesh `lumen_shard`, material M_Crystal, faceted, <= 300 tris.
    blender -b --factory-startup -P tools/blender/models/lumen_shard.py [-- --no-render]
"""
import math
import os
import random
import sys

import bmesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

rng = random.Random(7)


def crystal(name, length, radius, tip, axis, base, twist=0.0, jag=0.18):
    """Hexagonal quartz-like prism from `base` along `axis`: broken (jagged) foot, 6-facet pyramid tip."""
    bm = bmesh.new()
    ax = Vector(axis).normalized()
    q = Vector((0, 0, 1)).rotation_difference(ax)
    rot = q.to_matrix()
    ring0, ring1 = [], []
    for i in range(6):
        a = twist + i * math.pi / 3
        r = radius * rng.uniform(0.82, 1.12)
        p = Vector((r * math.cos(a), r * math.sin(a), 0.0))
        z0 = -radius * rng.uniform(0.0, jag * 4)                # jagged, broken foot
        z1 = length * rng.uniform(0.93, 1.0)
        ring0.append(bm.verts.new(Vector(base) + rot @ (p + Vector((0, 0, z0)))))
        ring1.append(bm.verts.new(Vector(base) + rot @ (p + Vector((0, 0, z1)))))
    off = Vector((rng.uniform(-0.25, 0.25) * radius, rng.uniform(-0.25, 0.25) * radius, length + tip))
    apex = bm.verts.new(Vector(base) + rot @ off)
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        bm.faces.new((ring1[i], ring1[j], apex))
    foot = bm.verts.new(Vector(base) + rot @ Vector((0.0, 0.0, -radius * 0.9)))
    for i in range(6):
        bm.faces.new((ring0[(i + 1) % 6], ring0[i], foot))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = M.bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = M.bpy.data.objects.new(name, me)
    M.bpy.context.scene.collection.objects.link(obj)
    M.assign(obj, "M_Crystal")
    return obj


def centre_of_mass(obj):
    me = obj.data
    me.calc_loop_triangles()
    vol, c = 0.0, Vector()
    for t in me.loop_triangles:
        a, b, d = (me.vertices[i].co for i in t.vertices)
        v = a.dot(b.cross(d)) / 6.0
        vol += v
        c += v * (a + b + d) / 4.0
    return c / vol if abs(vol) > 1e-12 else Vector()


def build():
    main = crystal("c0", 0.036, 0.0085, 0.013, (1.0, 0.0, 0.12), (-0.022, 0.0, 0.0), twist=0.2)
    br1 = crystal("c1", 0.022, 0.0062, 0.009, (0.8, 0.45, 0.35), (-0.018, 0.003, 0.001), twist=0.7)
    br2 = crystal("c2", 0.016, 0.0048, 0.007, (0.75, -0.55, 0.30), (-0.017, -0.003, 0.0), twist=1.1)
    sprig = crystal("c3", 0.009, 0.0034, 0.005, (0.55, 0.1, 0.85), (-0.011, 0.0, 0.004), twist=0.4, jag=0.08)
    shard = M.join([main, br1, br2, sprig], "lumen_shard")
    com = centre_of_mass(shard)
    shard.data.transform(Matrix.Translation(-com))
    zmin = min(v.co.z for v in shard.data.vertices)
    print(f"[lumen_shard] lowest point {zmin:.4f} m below the origin (centre of mass)")
    return shard


def qa_glass(mat):
    """QA render only (after export): show M_Crystal as clear cyan glass instead of the flat preview."""
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.75, 0.95, 1.0, 1.0)
    b.inputs["Alpha"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.55
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Emission Color"].default_value = (0.81, 0.96, 1.0, 1.0)
    b.inputs["Emission Strength"].default_value = 0.15


def main():
    M.reset_scene()
    L.ensure_materials()
    build()
    L.finish("lumen_shard", decals=[lambda: L.faceted(M.bpy.data.objects["lumen_shard"], 5.0)])
    if L.want_render():
        qa_glass(M.bpy.data.materials["M_Crystal"])
        zmin = min(v.co.z for v in M.bpy.data.objects["lumen_shard"].data.vertices)
        L.qa_render("lumen_shard", (0.09, -0.12, 0.07), (0.0, 0.0, 0.0), lens=60, floor_z=zmin, samples=32)
        L.qa_render("lumen_shard_2", (0.0, -0.06, 0.13), (0.0, 0.0, 0.0), lens=60, floor_z=zmin, samples=32)


main()
