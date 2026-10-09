"""MYSTERY ROOM — Chapter 3 group A helpers (shell_choir, shell_gallery, shell_nursery, shell_lift, array_below,
freight_lift, blast_door). Contract: docs/models/ch3.md; measured results: docs/models/ch3_a.md.

Builds on mrlib / lib_mech / lib_arch / lib_props / lib_ch2_vault / lib_ch2_arch / lib_ch3_symbols (never edits them).

G-FRAME (as lib_ch2_vault): every script builds its geometry directly in GODOT axes inside Blender (Blender x, y, z
used as Godot x, y, z: y up, +z = south / the model front), so every number reads straight from ch3.md.
`to_blender()` converts the finished, unparented scene to Blender axes right before parenting and export.

  ensure_materials()        every slot group A uses (library, Chapter 2 and the new Chapter 3 slots) for QA previews
  gbox / glathe / gcyl ...  G-frame primitives (re-exported from lib_ch2_vault)
  arc_band / ring_wall ...  curved shell pieces (drums, rings, bell mouths) built from polar profiles
  wrap_x(obj, r)            bend a flat inlay (built facing +Z) onto a cylinder around local X (drum symbols)
  slice_y(obj, step)        add horizontal cuts so a wrapped mesh follows the curvature
  surfaces(path)            draw-call count of an exported GLB (mesh nodes x primitives) + material slots
  qa_*                      shared-machine Cycles settings, Godot-FOV cameras, zone lights, emissive overrides
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_props as P  # noqa: E402
import lib_ch2_vault as V  # noqa: E402
import lib_ch2_arch as C2  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402

ROOT = M.ROOT
TAG = "[ch3-a]"
QA_SUB = "ch3"
TAU = 2.0 * math.pi

# re-exports (G-frame primitives)
gbox, glathe, gcyl, plate, flat, rivet, hexbolt, screw = V.gbox, V.glathe, V.gcyl, V.plate, V.flat, V.rivet, V.hexbolt, V.screw
part, empty, to_blender, parent, axis_rot = V.part, V.empty, V.to_blender, V.parent, V.axis_rot
G = V.G

STEEL, PAINT, BRASS, BRASS_P = "M_Steel_Dark", "M_Steel_Painted", "M_Brass_Aged", "M_Brass_Polished"
CONC, STONE, GLASS, FROST = "M_Concrete", "M_Stone", "M_Glass", "M_Glass_Frosted"
ROCK, CHEQ, TILE, PORC, SHQ = "M_Rock", "M_Chequer", "M_Tile_Glazed", "M_Porcelain", "M_Shader_Quad"
GREEN, LINO, CREAM_STEEL, AMBER, LUMEN = "M_Paint_Green", "M_Linoleum", "M_Steel_Cream", "M_Enamel_Amber", "M_Emissive_Lumen"


# ====================================================================== materials
def ensure_materials() -> None:
    """Preview materials for every slot group A uses (call after mrlib.reset_scene)."""
    L.ensure_materials()
    C2.ensure_materials()          # M_Paint_Green / M_Concrete tinted sets, M_Linoleum (0.6 m), extra slots
    S.ensure_materials()           # Chapter 3 slots: tiles / rock / chequer sets, porcelain, shader quad, decals
    for name, (hx, rough, metal, alpha) in V.OTHER_SLOTS.items():
        if bpy.data.materials.get(name) is None:
            M.material(name, color=hx, rough=rough, metal=metal, alpha=alpha)
    for name in ("M_Steel_Cream", "M_Stone", "M_Glass", "M_Glass_Frosted", "M_Emissive_Lumen"):
        M.material(name)


# ====================================================================== geometry helpers (G-frame)
def obj_from_bm(name, bm, mat):
    o = M._new_obj(name, bm)
    M.assign(o, mat)
    return o


def polar(r, phi_deg, y=0.0):
    """World point at radius r, angle phi measured from NORTH (-Z) clockwise seen from above (toward +X)."""
    p = math.radians(phi_deg)
    return Vector((r * math.sin(p), y, -r * math.cos(p)))


def ring_wall(name, r, y0, y1, a0, a1, n, mat, inward=True, cap=False):
    """Vertical cylindrical wall piece of radius r between angles a0..a1 (degrees from north, clockwise), facing
    the centre (inward=True) or outward."""
    bm = bmesh.new()
    bot, top = [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        p = polar(r, a)
        bot.append(bm.verts.new((p.x, y0, p.z)))
        top.append(bm.verts.new((p.x, y1, p.z)))
    for i in range(n):
        f = (bot[i], bot[i + 1], top[i + 1], top[i])
        bm.faces.new(f if inward else tuple(reversed(f)))
    o = obj_from_bm(name, bm, mat)
    _orient(o, inward)
    return o


def _orient(o, inward):
    """Make the normals of a centred revolve point toward the Y axis (inward) or away from it."""
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        c = f.calc_center_median()
        radial = Vector((c.x, 0.0, c.z))
        if radial.length < 1e-6:
            continue
        d = f.normal.dot(radial)
        if (inward and d > 0) or (not inward and d < 0):
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()


def revolve(name, prof, a0, a1, n, mat, centre=(0.0, 0.0), closed=False, flip=False):
    """Revolve a 2D profile [(r, y)] about the vertical axis through (centre x, centre z), between angles a0..a1
    (degrees from north, clockwise). Faces follow the profile order; flip reverses them."""
    bm = bmesh.new()
    rings = []
    cx, cz = centre
    full = abs((a1 - a0) - 360.0) < 1e-6
    cnt = n if full else n + 1
    for (r, y) in prof:
        ring = []
        for i in range(cnt):
            a = math.radians(a0 + (a1 - a0) * i / n)
            ring.append(bm.verts.new((cx + r * math.sin(a), y, cz - r * math.cos(a))))
        rings.append(ring)
    rng = range(len(rings)) if closed else range(len(rings) - 1)
    for k in rng:
        ra, rb = rings[k], rings[(k + 1) % len(rings)]
        for i in range(n):
            j = (i + 1) % cnt
            f = (ra[i], ra[j], rb[j], rb[i])
            if (abs(ra[i].co.x - rb[i].co.x) + abs(ra[i].co.y - rb[i].co.y) + abs(ra[i].co.z - rb[i].co.z)) < 1e-9:
                continue
            try:
                bm.faces.new(tuple(reversed(f)) if flip else f)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    return obj_from_bm(name, bm, mat)


def quad(name, centre, u_axis, v_axis, w, h, mat, uv=(0.0, 0.0, 1.0, 1.0)):
    """G-frame quad facing u x v, UV 0..1 (u along u_axis, v along v_axis)."""
    c = Vector(centre)
    u = Vector(u_axis).normalized() * (w / 2)
    v = Vector(v_axis).normalized() * (h / 2)
    me = bpy.data.meshes.new(name)
    vs = [c - u - v, c + u - v, c + u + v, c - u + v]
    me.from_pydata([tuple(p) for p in vs], [], [(0, 1, 2, 3)])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    M.assign(o, mat)
    uvl = me.uv_layers.new(name="UVMap")
    u0, v0, u1, v1 = uv
    for li, (uu, vv) in zip(range(4), ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        uvl.data[li].uv = (uu, vv)
    return o


def slice_y(obj, step, y0=-1.0, y1=1.0) -> None:
    """Cut a mesh with planes y = k * step (local coords) so it can later be bent smoothly."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    k0, k1 = int(math.floor(y0 / step)), int(math.ceil(y1 / step))
    for k in range(k0, k1 + 1):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=(0, k * step, 0), plane_no=(0, 1, 0))
    bm.to_mesh(obj.data)
    bm.free()


def wrap_x(obj, r) -> None:
    """Bend a mesh built facing +Z around local X: (x, y, z) -> angle y / r on a cylinder of radius r + z."""
    for v in obj.data.vertices:
        x, y, z = v.co
        a = y / r
        rr = r + z
        v.co = (x, rr * math.sin(a), rr * math.cos(a))
    obj.data.update()


def symbol_inlay(name, kind, h, mat, depth=0.0):
    """lib_ch3_symbols inlay in local XY facing +Z (flat, or a low relief)."""
    return S.inlay(name, kind, h, depth=depth, mat=mat)


def mesh_tris(o) -> int:
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def delete_faces_where(obj, pred) -> None:
    """Delete faces whose (G-frame) centre / normal satisfy pred(c, n) — hidden backs, overlaps."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    dead = [f for f in bm.faces if pred(mw @ f.calc_center_median(), (mw.to_3x3() @ f.normal).normalized())]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def merge(name, objs):
    """Join without presmoothing (shell pieces), keeping per-part smooth flags already set."""
    objs = [o for o in objs if o is not None]
    o = M.join(objs, name) if len(objs) > 1 else objs[0]
    o.name = name
    o.data.name = name
    return o


def cut(target, cutter_objs) -> None:
    """Boolean-subtract one or more box cutters (deleted afterwards)."""
    for c in cutter_objs:
        M.boolean(target, c)


def wall_sweep(name, path, profile, mat, closed=True):
    """Sweep an open wall profile [(s, y)] (s > 0 = into the wall) along a horizontal path [(x, z)] traversed
    CLOCKWISE seen from above (so the faces look into the room); mitred corners."""
    n = len(path)
    P = [Vector((x, 0.0, z)) for x, z in path]
    up = Vector((0, 1, 0))
    bm = bmesh.new()
    cols = []
    for i in range(n):
        if closed or 0 < i < n - 1:
            t_in = (P[i] - P[i - 1]).normalized()
            t_out = (P[(i + 1) % n] - P[i]).normalized()
        elif i == 0:
            t_in = t_out = (P[1] - P[0]).normalized()
        else:
            t_in = t_out = (P[i] - P[i - 1]).normalized()
        n_in, n_out = up.cross(t_in), up.cross(t_out)
        m = (n_in + n_out)
        m = m.normalized() if m.length > 1e-6 else n_in
        k = 1.0 / max(0.25, m.dot(n_in))
        cols.append([bm.verts.new(P[i] + m * (s * k) + up * y) for (s, y) in profile])
    last = n if closed else n - 1
    for i in range(last):
        a, b = cols[i], cols[(i + 1) % n]
        for r in range(len(profile) - 1):
            bm.faces.new((a[r], b[r], b[r + 1], a[r + 1]))
    return obj_from_bm(name, bm, mat)


def flat_poly(name, outer, holes, y, mat, up=True):
    """Horizontal filled polygon (G-frame (x, z) loops, even-odd holes) at height y, facing up or down."""
    if up:
        loops = [[(x, -z) for (x, z) in lp] for lp in [outer] + list(holes)]
        o = L.flat_shape(name, loops, mat=mat)
        o.data.transform(Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    else:
        loops = [[(x, z) for (x, z) in lp] for lp in [outer] + list(holes)]
        o = L.flat_shape(name, loops, mat=mat)
        o.data.transform(Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    return o


def rock_panel(name, origin, u, v, w, h, nu, nv, amp, seed, mat="M_Rock", normal_sign=1.0):
    """Subdivided rectangle (origin + a u + b v, a in [0, w], b in [0, h]) displaced along its normal by random rock
    relief (edges kept flat); faces look along normal_sign * (u x v)."""
    import random
    rng = random.Random(seed)
    o, U, Vv = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
    nrm = U.cross(Vv) * normal_sign
    bm = bmesh.new()
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            d = 0.0 if i in (0, nu) or j in (0, nv) else rng.uniform(-amp, amp)
            row.append(bm.verts.new(o + U * (w * i / nu) + Vv * (h * j / nv) + nrm * d))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            f = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            bm.faces.new(f if normal_sign > 0 else tuple(reversed(f)))
    return obj_from_bm(name, bm, mat)


# ====================================================================== GLB facts
def glb_json(path):
    return V.glb_json(path)


def surfaces(path):
    """(draw calls = mesh-node primitives, material slots, {node: [materials]}) of an exported GLB."""
    doc = glb_json(path)
    mats = [m.get("name", "") for m in doc.get("materials", [])]
    per = {}
    count = 0
    for n in doc.get("nodes", []):
        if "mesh" in n:
            prims = doc["meshes"][n["mesh"]]["primitives"]
            count += len(prims)
            per[n.get("name", "")] = [mats[p["material"]] if "material" in p else "-" for p in prims]
    return count, len(mats), per


def glb_tris(path) -> int:
    doc = glb_json(path)
    acc = doc.get("accessors", [])
    t = 0
    for n in doc.get("nodes", []):
        if "mesh" in n:
            for prim in doc["meshes"][n["mesh"]]["primitives"]:
                t += acc[prim["indices"]]["count"] // 3
    return t


def facts(path, tri_budget, surf_budget, mat_budget=4) -> list:
    """Print and check tris / surfaces / material slots against the §13 budgets."""
    tris = glb_tris(path)
    surf, nmat, per = surfaces(path)
    errs = []
    print(f"{TAG} {os.path.basename(path)}: tris {tris} / {tri_budget}, surfaces {surf} / {surf_budget}, "
          f"materials {nmat} / {mat_budget}")
    for k, v in sorted(per.items()):
        print(f"{TAG}     {k:28s} {v}")
    if tris > tri_budget:
        errs.append(f"tris {tris} > {tri_budget}")
    if surf > surf_budget:
        errs.append(f"surfaces {surf} > {surf_budget}")
    if nmat > mat_budget:
        errs.append(f"materials {nmat} > {mat_budget}")
    return errs


def export(name: str) -> str:
    path = A.export_lean(name)
    V.check_names(path)
    return path


def report(label: str) -> int:
    return V.report(label)


# ====================================================================== QA
def qa_begin(bounces: int = 6) -> None:
    """Call AFTER export. Shared-machine render settings (2 threads) + Cycles-friendly glass."""
    os.makedirs(os.path.join(M.QA_DIR, QA_SUB), exist_ok=True)
    P.preview_tweak()
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b is None:
            continue
        if mat.name == "M_Glass_Dark":
            b.inputs["Alpha"].default_value = 1.0
        if mat.name == "M_Glass":
            b.inputs["Roughness"].default_value = 0.02
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    P.render_threads(2)
    sc.cycles.max_bounces = bounces
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.use_denoising = True


def lens_for_vfov(vfov_deg: float, res=(960, 640)) -> float:
    return V.lens_for_vfov(vfov_deg, res)


NO_LIGHTS = [((0, 0, 1), 0.0, "FFFFFF", 0.1)]


def shoot(name, cam, target, vfov=50.0, res=(960, 640), samples=32, world=0.03):
    """qa/blender/ch3/<name>.png from Godot camera/target points with the Godot vertical FOV (Cycles, <= 32
    samples, <= 960 x 640, 2 threads)."""
    sc = bpy.context.scene
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    return M.render_preview(f"{QA_SUB}/{name}", G(*cam), G(*target), lens=lens_for_vfov(vfov, res), res=res,
                            samples=min(samples, 32), world_strength=world, lights=NO_LIGHTS)


def light(name, kind, pos, energy, colour="FFE2C0", radius=0.05, target=None, spot_deg=None, blend=0.3):
    """QA light at a Godot position (aim at a Godot target). Never visible to the camera (Cycles draws sized point /
    spot / area lights as glowing shapes otherwise)."""
    lo = V.qa_light(name, kind, pos, energy, colour, radius, target, spot_deg, blend)
    lo.visible_camera = False
    lo.visible_transmission = False
    if name.startswith("fill"):            # the game's focus_fill has no specular (no hot spots on glass / enamel)
        lo.data.specular_factor = 0.0
        lo.visible_glossy = False          # ...and its sphere must not show up mirrored in glass
    return lo


def clear_lights() -> None:
    for o in [o for o in bpy.context.scene.objects if o.type == "LIGHT" and o.name.startswith("qa_")]:
        bpy.data.objects.remove(o, do_unlink=True)


def glow(name, colour="FFE8C0", strength=8.0):
    return V.glow_material(name, colour, strength, base=colour)


def override(obj, mat):
    return V.override_material(obj, mat)


def restore(obj, old) -> None:
    V.restore_material(obj, old)


def qa_import(name, pos=(0, 0, 0), yaw=0.0, prefix="qa_"):
    """Import a neighbouring GLB for a QA scene and swap its plain glTF materials (base factors only, the export is
    lean) for this scene's textured preview materials of the same slot name."""
    holder = V.qa_import(V.model_glb(name), pos, yaw, prefix=prefix)
    if holder is None:
        return None
    for o in bpy.data.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            base = m.name.split(".")[0]
            if base != m.name:
                if bpy.data.materials.get(base) is None:
                    M.material(base)
                slot.material = bpy.data.materials[base]
            elif base.startswith("M_") and not any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes):
                pass
    return holder


def qa_place(objs, pos, yaw_deg, name="qa_place"):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.location = G(*pos)
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    M.refresh()
    return root


def image_emitter(name, path, strength=2.0, tint=(1.0, 1.0, 1.0)):
    """QA-only unshaded-looking material from an image (alpha -> transparent): code-composed decals such as the
    Array ring symbols or the shader-quad previews."""
    img = bpy.data.images.load(path, check_existing=True)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.blend_type = "MULTIPLY"
    mixc.inputs["Factor"].default_value = 1.0
    a_in = next(i for i in mixc.inputs if i.name == "A" and i.type == "RGBA")
    b_in = next(i for i in mixc.inputs if i.name == "B" and i.type == "RGBA")
    nt.links.new(tex.outputs["Color"], a_in)
    b_in.default_value = (*tint, 1.0)
    nt.links.new(next(o for o in mixc.outputs if o.type == "RGBA"), em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def pose_rot(obj, axis, deg):
    V.pose_rot(obj, axis, deg)


def pose_slide(obj, vec):
    V.pose_slide(obj, vec)


def want(args, tag: str) -> bool:
    for a in args:
        if a.startswith("--shots="):
            return tag in a.split("=", 1)[1].split(",")
    return True
