"""MYSTERY ROOM logo / app-icon helpers (Blender 5.2, Cycles CPU).

Only used by tools/blender/logo/make_logo.py. Read-only use of mrlib / lib_mech (never edited).

  * Scenes are built Z-up with the subject lying in the XY plane facing +Z (camera above).
  * Renders go to a linear EXR first; post() adds a physically-motivated bloom in numpy and
    writes the PNG through the scene's AgX view transform (Image.save_render).
  * mask_render() swaps every material for flat white / holdout to get crisp monochrome icons.
"""
from __future__ import annotations

import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402

ROOT = M.ROOT
FONTS = os.path.join(ROOT, "game", "assets", "fonts")
FONT_BOLD = os.path.join(FONTS, "CormorantGaramond-Bold.ttf")
FONT_SEMI = os.path.join(FONTS, "CormorantGaramond-SemiBold.ttf")
TAU = 2.0 * math.pi


def lin(h: str, a: float = 1.0):
    return M.hex_rgba(h, a)


# ------------------------------------------------------------------ scene
def reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def scene_setup(w: int, h: int, samples: int, transparent: bool = False) -> bpy.types.Scene:
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.008
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    try:
        sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        sc.cycles.denoising_prefilter = "ACCURATE"
        sc.cycles.denoising_quality = "HIGH"
    except (AttributeError, TypeError):
        pass
    sc.cycles.max_bounces = 12
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.volume_bounces = 1
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 0.6
    sc.cycles.sample_clamp_direct = 0.0
    sc.cycles.sample_clamp_indirect = 6.0
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.filter_size = 1.2
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    sc.view_settings.exposure = 0.0
    return sc


def link(obj: bpy.types.Object) -> bpy.types.Object:
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ------------------------------------------------------------------ node helpers
def node(nt, kind: str, inputs: dict | None = None, **attrs):
    n = nt.nodes.new(kind)
    for k, v in attrs.items():
        setattr(n, k, v)
    for k, v in (inputs or {}).items():
        n.inputs[k].default_value = v
    return n


def mix_rgb(nt, fac, a, b, blend: str = "MIX"):
    """ShaderNodeMix in RGBA mode; fac/a/b may be sockets or constants. Returns the colour output."""
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    ins = [s for s in n.inputs if s.type == "RGBA"]
    fin = n.inputs["Factor"] if not isinstance(n.inputs["Factor"], list) else n.inputs[0]
    for sock, val in ((fin, fac), (ins[0], a), (ins[1], b)):
        if isinstance(val, bpy.types.NodeSocket):
            nt.links.new(val, sock)
        else:
            sock.default_value = val
    return [s for s in n.outputs if s.type == "RGBA"][0]


def math_node(nt, op: str, a, b=0.0, clamp: bool = False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for sock, val in ((n.inputs[0], a), (n.inputs[1], b)):
        if isinstance(val, bpy.types.NodeSocket):
            nt.links.new(val, sock)
        else:
            sock.default_value = val
    return n.outputs[0]


def map_range(nt, val, f0, f1, t0, t1, clamp: bool = True, interp: str = "LINEAR"):
    n = nt.nodes.new("ShaderNodeMapRange")
    n.clamp = clamp
    n.interpolation_type = interp
    nt.links.new(val, n.inputs["Value"])
    n.inputs["From Min"].default_value = f0
    n.inputs["From Max"].default_value = f1
    n.inputs["To Min"].default_value = t0
    n.inputs["To Max"].default_value = t1
    return n.outputs["Result"]


def noise(nt, vec, scale: float, detail: float = 6.0, rough: float = 0.55, out: str = "Fac"):
    n = node(nt, "ShaderNodeTexNoise", {"Scale": scale, "Detail": detail, "Roughness": rough})
    if vec is not None:
        nt.links.new(vec, n.inputs["Vector"])
    return n.outputs[out]


def new_mat(name: str):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m, None
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m, m.node_tree


# ------------------------------------------------------------------ materials
def mat_brass(name: str = "LG_Brass", hi: str = "E6C27C", lo: str = "8C6A34", patina: str = "2C2A1E",
              rough: float = 0.2, rough_var: float = 0.14, ao_dist: float = 0.03, crevice: float = 0.75,
              scale: float = 1.0, bump: float = 0.25, aniso: float = 0.0, radial: bool = False,
              verdigris: float = 0.25):
    """Aged brass: colour/roughness variation, darkened + rougher crevices (AO) with a hint of
    verdigris, fine hammered micro-bump and optional radial brushing (anisotropy)."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    bsdf = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord")
    obj_co = tc.outputs["Object"]
    big = noise(nt, obj_co, 3.0 / scale, 8.0, 0.6)
    var = map_range(nt, big, 0.3, 0.72, 0.0, 1.0)
    col = mix_rgb(nt, var, lin(lo), lin(hi))
    ao = node(nt, "ShaderNodeAmbientOcclusion", {"Distance": ao_dist * scale}, samples=8, only_local=True)
    cav = math_node(nt, "SUBTRACT", 1.0, ao.outputs["AO"], clamp=True)
    cav = map_range(nt, cav, 0.08, 0.7, 0.0, crevice)
    # verdigris speckle only in deep crevices
    vn = noise(nt, obj_co, 14.0 / scale, 4.0, 0.7)
    vmask = math_node(nt, "MULTIPLY", map_range(nt, vn, 0.45, 0.65, 0.0, verdigris), cav)
    pat = mix_rgb(nt, vmask, lin(patina), lin("3E6B5B"))
    col = mix_rgb(nt, cav, col, pat)
    nt.links.new(col, bsdf.inputs["Base Color"])
    rn = noise(nt, obj_co, 9.0 / scale, 5.0, 0.6)
    r = math_node(nt, "ADD", rough, map_range(nt, rn, 0.3, 0.7, -rough_var * 0.5, rough_var))
    r = math_node(nt, "ADD", r, math_node(nt, "MULTIPLY", cav, 0.45), clamp=True)
    nt.links.new(r, bsdf.inputs["Roughness"])
    metal = math_node(nt, "SUBTRACT", 1.0, math_node(nt, "MULTIPLY", cav, 0.55), clamp=True)
    nt.links.new(metal, bsdf.inputs["Metallic"])
    bsdf.inputs["Specular Tint"].default_value = lin("FFF0C8")
    if bump > 0:
        fine = noise(nt, obj_co, 160.0 / scale, 3.0, 0.5)
        scr = node(nt, "ShaderNodeTexWave", {"Scale": 40.0 / scale, "Distortion": 6.0, "Detail": 4.0},
                   wave_type="BANDS", bands_direction="DIAGONAL")
        nt.links.new(obj_co, scr.inputs["Vector"])
        h = math_node(nt, "ADD", fine, math_node(nt, "MULTIPLY", scr.outputs["Fac"], 0.15))
        b = node(nt, "ShaderNodeBump", {"Strength": bump, "Distance": 0.002 * scale})
        nt.links.new(h, b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    if aniso > 0:
        bsdf.inputs["Anisotropic"].default_value = aniso
        if radial:
            tg = node(nt, "ShaderNodeTangent", direction_type="RADIAL", axis="Z")
            nt.links.new(tg.outputs["Tangent"], bsdf.inputs["Tangent"])
    return m


def mat_flat(name: str, color: str, rough: float = 0.5, metal: float = 0.0, emission: str | None = None,
             strength: float = 0.0, sheen: float = 0.0, coat: float = 0.0):
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emission:
        b.inputs["Emission Color"].default_value = lin(emission)
        b.inputs["Emission Strength"].default_value = strength
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


def mat_engrave(name: str = "LG_Engrave"):
    """Black wax fill of engraved lines (slightly glossy so it never reads as a hole)."""
    return mat_flat(name, "17130D", rough=0.45, metal=0.0)


def mat_emit(name: str, color: str, strength: float):
    m, nt = new_mat(name)
    if nt is None:
        return m
    out = nt.nodes["Material Output"]
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = node(nt, "ShaderNodeEmission", {"Color": lin(color), "Strength": strength})
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def mat_glow_disc(name: str, hot: str = "F4FDFF", cool: str = "36C8F0", strength: float = 12.0,
                  radius: float = 1.0):
    """Radial emissive gradient (hot centre -> cyan edge) used behind crystals and in keyholes."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    out = nt.nodes["Material Output"]
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = node(nt, "ShaderNodeTexCoord")
    ln = node(nt, "ShaderNodeVectorMath", operation="LENGTH")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    comb = node(nt, "ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs[0], comb.inputs[0])
    nt.links.new(sep.outputs[1], comb.inputs[1])
    nt.links.new(comb.outputs[0], ln.inputs[0])
    t = map_range(nt, ln.outputs["Value"], 0.0, radius, 0.0, 1.0)
    col = mix_rgb(nt, t, lin(hot), lin(cool))
    s = map_range(nt, ln.outputs["Value"], 0.0, radius, strength, strength * 0.35, interp="SMOOTHSTEP")
    e = node(nt, "ShaderNodeEmission")
    nt.links.new(col, e.inputs["Color"])
    nt.links.new(s, e.inputs["Strength"])
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def mat_crystal(name: str = "LG_Crystal", tint: str = "D8F7FF", glow: str = "4FD6FF", glow_strength: float = 40.0,
                ior: float = 1.6):
    """Faceted Lumen crystal: clear glass surface + an emissive volume (light memory glowing inside)."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(tint)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = ior
    b.inputs["Metallic"].default_value = 0.0
    out = nt.nodes["Material Output"]
    if glow_strength > 0:
        v = node(nt, "ShaderNodeVolumePrincipled", {"Density": 0.0, "Emission Strength": glow_strength,
                                                     "Emission Color": lin(glow)})
        nt.links.new(v.outputs[0], out.inputs["Volume"])
    return m


def mat_velvet(name: str = "LG_Velvet", color: str = "0F2523", sheen_tint: str = "6FB9AC", scale: float = 1.0):
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord")
    n = noise(nt, tc.outputs["Object"], 2.0 / scale, 6.0, 0.6)
    col = mix_rgb(nt, map_range(nt, n, 0.3, 0.7, 0.0, 1.0), lin(color), lin("17312E"))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 1.0
    b.inputs["Sheen Roughness"].default_value = 0.35
    b.inputs["Sheen Tint"].default_value = lin(sheen_tint)
    b.inputs["Specular IOR Level"].default_value = 0.2
    fine = noise(nt, tc.outputs["Object"], 900.0 / scale, 2.0, 0.5)
    bp = node(nt, "ShaderNodeBump", {"Strength": 0.25, "Distance": 0.001 * scale})
    nt.links.new(fine, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_enamel(name: str = "LG_Enamel", color: str = "1C3A33", scale: float = 1.0):
    """Dark green door enamel over wood: soft grain telegraphing through the paint, satin coat, wear."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord")
    co = tc.outputs["Object"]
    mp = node(nt, "ShaderNodeMapping", {"Scale": (1.0, 9.0, 1.0)})
    nt.links.new(co, mp.inputs["Vector"])
    grain = node(nt, "ShaderNodeTexWave", {"Scale": 3.0 / scale, "Distortion": 9.0, "Detail": 6.0,
                                           "Detail Roughness": 0.7}, wave_type="RINGS")
    nt.links.new(mp.outputs[0], grain.inputs["Vector"])
    n = noise(nt, co, 4.0 / scale, 8.0, 0.6)
    col = mix_rgb(nt, map_range(nt, n, 0.3, 0.75, 0.0, 1.0), lin(color), lin("244A41"))
    col = mix_rgb(nt, math_node(nt, "MULTIPLY", grain.outputs["Fac"], 0.25), col, lin("12241F"))
    nt.links.new(col, b.inputs["Base Color"])
    r = map_range(nt, noise(nt, co, 6.0 / scale, 6.0, 0.6), 0.3, 0.7, 0.28, 0.5)
    nt.links.new(r, b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.25
    bp = node(nt, "ShaderNodeBump", {"Strength": 0.12, "Distance": 0.003 * scale})
    h = math_node(nt, "ADD", math_node(nt, "MULTIPLY", grain.outputs["Fac"], 0.6),
                  noise(nt, co, 300.0 / scale, 3.0, 0.5))
    nt.links.new(h, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_backdrop(name: str = "LG_Backdrop", color: str = "142A27", color2: str = "0F1F1D", scale: float = 1.0):
    """Painted plaster / felt backdrop: soft mottling, very matte."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord")
    co = tc.outputs["Object"]
    n = noise(nt, co, 1.6 / scale, 8.0, 0.62)
    col = mix_rgb(nt, map_range(nt, n, 0.32, 0.7, 0.0, 1.0), lin(color2), lin(color))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Specular IOR Level"].default_value = 0.25
    bp = node(nt, "ShaderNodeBump", {"Strength": 0.18, "Distance": 0.002 * scale})
    nt.links.new(noise(nt, co, 220.0 / scale, 4.0, 0.6), bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_volume(name: str = "LG_Haze", density: float = 0.2, anisotropy: float = 0.25, noise_scale: float = 0.0,
               color: str = "FFFFFF"):
    m, nt = new_mat(name)
    if nt is None:
        return m
    out = nt.nodes["Material Output"]
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = node(nt, "ShaderNodeVolumePrincipled", {"Density": density, "Anisotropy": anisotropy,
                                                 "Color": lin(color)})
    if noise_scale > 0:
        tc = node(nt, "ShaderNodeTexCoord")
        n = noise(nt, tc.outputs["Object"], noise_scale, 4.0, 0.55)
        d = map_range(nt, n, 0.35, 0.75, density * 0.25, density * 1.6)
        nt.links.new(d, v.inputs["Density"])
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    return m


def mat_reflector(name: str, stops, axis: int = 1, lo: float = -1.0, hi: float = 1.0, strength: float = 1.0,
                  color: str = "FFE7C2"):
    """Emissive card whose brightness follows a gradient along a local axis (stops = [(t, value)])
    — polished metal faces mirror it, which gives the classic gold-leaf gradient on flat letters."""
    m, nt = new_mat(name)
    if nt is None:
        return m
    out = nt.nodes["Material Output"]
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = node(nt, "ShaderNodeTexCoord")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    t = map_range(nt, sep.outputs[axis], lo, hi, 0.0, 1.0)
    ramp = node(nt, "ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = (stops[0][1],) * 3 + (1.0,)
    for (p, v) in stops[1:]:
        e = cr.elements.new(p)
        e.color = (v, v, v, 1.0)
    nt.links.new(t, ramp.inputs["Fac"])
    col = mix_rgb(nt, 1.0, ramp.outputs["Color"], lin(color), blend="MULTIPLY")
    e = node(nt, "ShaderNodeEmission", {"Strength": strength})
    nt.links.new(col, e.inputs["Color"])
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def mat_dust(name: str = "LG_Dust", emit: str = "FFE2B8", strength: float = 0.0):
    m, nt = new_mat(name)
    if nt is None:
        return m
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin("FFFFFF")
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Subsurface Weight"].default_value = 0.0
    if strength:
        b.inputs["Emission Color"].default_value = lin(emit)
        b.inputs["Emission Strength"].default_value = strength
    return m


def set_mat(obj, mat) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0


def add_mat_where(obj, mat, pred) -> int:
    """Assign `mat` to faces whose (centre, normal) satisfy pred (object space). Returns count."""
    names = [m.name for m in obj.data.materials if m]
    if mat.name not in names:
        obj.data.materials.append(mat)
        names.append(mat.name)
    idx = names.index(mat.name)
    n = 0
    for p in obj.data.polygons:
        if pred(p.center, p.normal):
            p.material_index = idx
            n += 1
    return n


# ------------------------------------------------------------------ world & lights
def world(color: str = "0B0E0E", strength: float = 1.0, top: str | None = None, top_strength: float = 0.0,
          cam_color: str | None = None):
    """Dark environment with an optional bright 'sky' toward +Z for reflections on polished faces.
    `cam_color` overrides what camera rays see (for opaque renders without a backdrop)."""
    w = bpy.data.worlds.new("LG_World")
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    out = nt.nodes["World Output"]
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = lin(color)
    bg.inputs["Strength"].default_value = strength
    shader = bg.outputs[0]
    if top:
        tc = node(nt, "ShaderNodeTexCoord")
        sep = node(nt, "ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        t = map_range(nt, sep.outputs[2], 0.2, 0.95, 0.0, 1.0, interp="SMOOTHSTEP")
        col = mix_rgb(nt, t, lin(color), lin(top))
        st = map_range(nt, sep.outputs[2], 0.2, 0.95, strength, top_strength, interp="SMOOTHSTEP")
        nt.links.new(col, bg.inputs["Color"])
        nt.links.new(st, bg.inputs["Strength"])
    if cam_color:
        lp = node(nt, "ShaderNodeLightPath")
        bg2 = node(nt, "ShaderNodeBackground", {"Color": lin(cam_color), "Strength": 1.0})
        mx = node(nt, "ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
        nt.links.new(shader, mx.inputs[1])
        nt.links.new(bg2.outputs[0], mx.inputs[2])
        shader = mx.outputs[0]
    nt.links.new(shader, out.inputs["Surface"])
    bpy.context.scene.world = w
    return w


def look_at(obj, target, up=(0, 0, 1)) -> None:
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def light(kind: str, name: str, loc, target=None, energy: float = 100.0, color: str = "FFFFFF",
          size: float = 0.5, size_y: float | None = None, spot_deg: float = 30.0, blend: float = 0.3,
          glossy: bool = True, shadow_soft: float | None = None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = lin(color)[:3]
    if kind == "AREA":
        if size_y is not None:
            ld.shape = "RECTANGLE"
            ld.size = size
            ld.size_y = size_y
        else:
            ld.shape = "DISK"
            ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size if shadow_soft is None else shadow_soft
    if kind == "SPOT":
        ld.spot_size = math.radians(spot_deg)
        ld.spot_blend = blend
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    ob.visible_glossy = glossy
    return ob


def camera(loc, target, lens: float = 50.0, ortho: float | None = None, dof_target=None, fstop: float = 8.0,
           sensor: float = 36.0):
    cd = bpy.data.cameras.new("LG_Cam")
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = "AUTO"
    if ortho is not None:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cd.clip_start = 0.01
    cd.clip_end = 200.0
    cam = link(bpy.data.objects.new("LG_Cam", cd))
    cam.location = loc
    look_at(cam, target)
    bpy.context.scene.camera = cam
    if dof_target is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(dof_target) - Vector(loc)).length
        cd.dof.aperture_fstop = fstop
        cd.dof.aperture_blades = 7
        cd.dof.aperture_rotation = math.radians(12)
    return cam


def projected_bbox(cam, objs):
    """Normalised (0..1) camera-frame bounds (u0, u1, v0, v1) of the objects' evaluated vertices."""
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    us, vs = [], []
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        step = max(1, len(me.vertices) // 20000)
        for v in me.vertices[::step]:
            p = world_to_camera_view(sc, cam, mw @ v.co)
            us.append(p.x)
            vs.append(p.y)
        ev.to_mesh_clear()
    return min(us), max(us), min(vs), max(vs)


def frame(cam, objs, frac: float, iters: int = 4, offset=(0.0, 0.0)) -> None:
    """Scale (lens / ortho scale) and shift the camera so the subject's larger projected extent is
    `frac` of the frame and its bbox is centred (+offset in frame fractions)."""
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / sc.render.resolution_y
    for _ in range(iters):
        u0, u1, v0, v1 = projected_bbox(cam, objs)
        w, h = (u1 - u0), (v1 - v0)
        # extents relative to the larger frame dimension
        if aspect >= 1:
            w_l, h_l = w, h / aspect
        else:
            w_l, h_l = w * aspect, h
        s = frac / max(w_l, h_l, 1e-6)
        if cam.data.type == "ORTHO":
            cam.data.ortho_scale /= s
        else:
            cam.data.lens *= s
        u0, u1, v0, v1 = projected_bbox(cam, objs)
        cu, cv = (u0 + u1) / 2 - 0.5 - offset[0], (v0 + v1) / 2 - 0.5 - offset[1]
        if aspect >= 1:
            cam.data.shift_x += cu
            cam.data.shift_y += cv / aspect
        else:
            cam.data.shift_x += cu * aspect
            cam.data.shift_y += cv


# ------------------------------------------------------------------ geometry helpers
def fillet(points, radius, segs: int = 4, closed: bool = False, radii=None):
    """Round the corners of a 2D polyline with circular arcs (premium bevelled profiles)."""
    out = []
    n = len(points)
    for i, p in enumerate(points):
        r = radii[i] if radii is not None else radius
        if (not closed and (i == 0 or i == n - 1)) or r <= 0:
            out.append(tuple(p))
            continue
        a, b, c = Vector(points[i - 1]), Vector(p), Vector(points[(i + 1) % n])
        v1, v2 = a - b, c - b
        l1, l2 = v1.length, v2.length
        if l1 < 1e-9 or l2 < 1e-9:
            out.append(tuple(p))
            continue
        v1.normalize()
        v2.normalize()
        ang = math.acos(max(-1.0, min(1.0, v1.dot(v2))))
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(tuple(p))
            continue
        t = r / math.tan(ang / 2)
        t = min(t, l1 * 0.48, l2 * 0.48)
        re = t * math.tan(ang / 2)
        p1, p2 = b + v1 * t, b + v2 * t
        bis = (v1 + v2).normalized()
        ctr = b + bis * (re / math.sin(ang / 2))
        a1 = math.atan2(p1.y - ctr.y, p1.x - ctr.x)
        a2 = math.atan2(p2.y - ctr.y, p2.x - ctr.x)
        sw = (a2 - a1 + math.pi) % TAU - math.pi
        for k in range(segs + 1):
            aa = a1 + sw * k / segs
            out.append((ctr.x + re * math.cos(aa), ctr.y + re * math.sin(aa)))
    return out


def lathe(name: str, profile, segments: int = 128, mat=None, smooth_deg: float = 50.0, phase: float = 0.0,
          close: bool = False):
    """Revolve [(r, z), ...] around Z. Traverse so the solid lies to the LEFT of the travel direction
    in the (r right, z up) plane (outer wall upward, top inward, inner wall downward)."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        rings.append([bm.verts.new((r * math.cos(phase + TAU * i / segments),
                                    r * math.sin(phase + TAU * i / segments), z)) for i in range(segments)])
    pairs = list(zip(rings[:-1], rings[1:]))
    if close:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    if mat is not None:
        set_mat(obj, mat)
    shade(obj, smooth_deg)
    return obj


def shade(obj, angle_deg: float = 40.0) -> None:
    """Smooth shading with sharp edges above angle_deg (angle 0 = flat facets)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = angle_deg > 0
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_face_angle(0) > thr:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


def solid2d(name: str, loops, depth: float, bevel: float, bevel_res: int = 3, mat=None, z0: float = 0.0,
            smooth_deg: float = 50.0, keep_size: bool = True):
    """Extruded 2D outline (outer + holes) with a rounded bevel, bottom at z0. Wraps lib_mech."""
    obj = L.curve_solid(name, loops, depth, bevel=bevel, bevel_res=bevel_res, keep_size=keep_size)
    obj.data.transform(Matrix.Translation((0, 0, z0)))
    if mat is not None:
        set_mat(obj, mat)
    shade(obj, smooth_deg)
    return obj


def inlay(name: str, loops, z: float, mat) -> bpy.types.Object:
    obj = L.flat_shape(name, loops)
    obj.data.transform(Matrix.Translation((0, 0, z)))
    set_mat(obj, mat)
    return obj


def rect(cx, cy, w, h, ang=0.0):
    c, s = math.cos(ang), math.sin(ang)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    return [(cx + x * c - y * s, cy + x * s + y * c) for (x, y) in pts]


def circle(r, n=48, cx=0.0, cy=0.0, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n)) for i in range(n)]


def transform(obj, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0) -> None:
    from mathutils import Euler
    obj.data.transform(Matrix.Translation(loc) @ Euler(rot, "XYZ").to_matrix().to_4x4() @
                       Matrix.Diagonal((scale, scale, scale, 1.0)))


def join(objs, name: str):
    return M.join(objs, name)


def text_obj(name: str, body: str, size: float, font: str = FONT_BOLD, extrude: float = 0.05,
             bevel: float = 0.012, bevel_res: int = 3, offset: float | None = None, spacing: float = 1.0,
             align: str = "LEFT", mat=None, resolution: int = 6):
    """Extruded + bevelled 3D text converted to a mesh (faces +Z, baseline at y=0, front at z=extrude+bevel)."""
    cu = bpy.data.curves.new(name + "_cu", "FONT")
    cu.body = body
    cu.size = size
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.extrude = extrude / 2.0
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    cu.offset = -bevel * 0.55 if offset is None else offset
    cu.space_character = spacing
    cu.align_x = align
    cu.resolution_u = resolution
    tmp = link(bpy.data.objects.new(name + "_tmp", cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.transform(Matrix.Translation((0, 0, extrude / 2.0 + bevel)))
    obj = link(bpy.data.objects.new(name, me))
    if mat is not None:
        set_mat(obj, mat)
    shade(obj, 35.0)
    return obj


def split_islands(obj):
    """Return lists of polygon indices per connected island, sorted by island centre x."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    seen = set()
    islands = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        isl = []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        xs = [v.co.x for i in isl for v in bm.faces[i].verts]
        islands.append((sum(xs) / len(xs), min(xs), max(xs), isl))
    bm.free()
    islands.sort(key=lambda t: t[0])
    return islands


def delete_faces(obj, indices) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in indices], context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def bounds(objs):
    bpy.context.view_layer.update()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return lo, hi


def dust(name: str, n: int, lo, hi, rmin: float, rmax: float, seed: int, mat, weight=None):
    """Tiny motes (icospheres) scattered in a box; `weight(p)` in 0..1 thins them out (e.g. outside a beam)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    placed = 0
    tries = 0
    while placed < n and tries < n * 50:
        tries += 1
        p = Vector([rnd.uniform(lo[i], hi[i]) for i in range(3)])
        if weight is not None and rnd.random() > weight(p):
            continue
        r = rmin * (rmax / rmin) ** (rnd.random() ** 2.2)
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        bmesh.ops.translate(bm, vec=p, verts=res["verts"])
        placed += 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    set_mat(obj, mat)
    shade(obj, 180.0)
    obj.visible_shadow = False
    return obj


def plane(name: str, w: float, h: float, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, subdiv: int = 0):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=max(1, subdiv), y_segments=max(1, subdiv), size=0.5)
    bmesh.ops.scale(bm, vec=(w, h, 1.0), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    obj.location = loc
    obj.rotation_euler = rot
    if mat is not None:
        set_mat(obj, mat)
    return obj


def cube(name: str, lo, hi, mat=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    s = [(hi[i] - lo[i]) for i in range(3)]
    bmesh.ops.scale(bm, vec=s, verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    if mat is not None:
        set_mat(obj, mat)
    return obj


def boolean_diff(target, cutter, delete: bool = True) -> None:
    mod = target.modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    M.apply_modifiers(target)
    if delete:
        bpy.data.objects.remove(cutter, do_unlink=True)


# ------------------------------------------------------------------ render + post
def render_exr(path: str) -> str:
    sc = bpy.context.scene
    s = sc.render.image_settings
    s.file_format = "OPEN_EXR"
    s.color_depth = "32"
    s.color_mode = "RGBA"
    s.exr_codec = "ZIP"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_px(path: str) -> np.ndarray:
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def _gauss_fft(img: np.ndarray, sigmas_weights) -> np.ndarray:
    """Sum of Gaussian blurs (sigma px, weight) of an (H, W, C) image via one FFT (zero padded)."""
    h, w, c = img.shape
    pad = int(3 * max(s for s, _ in sigmas_weights)) + 2
    H, W = h + 2 * pad, w + 2 * pad
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.rfftfreq(W)[None, :]
    f2 = fx * fx + fy * fy
    tf = np.zeros_like(f2)
    for s, wt in sigmas_weights:
        tf += wt * np.exp(-2.0 * (math.pi ** 2) * (s ** 2) * f2)
    out = np.empty_like(img)
    buf = np.zeros((H, W), dtype=np.float32)
    for ch in range(c):
        buf[:] = 0
        buf[pad:pad + h, pad:pad + w] = img[..., ch]
        res = np.fft.irfft2(np.fft.rfft2(buf) * tf, s=(H, W))
        out[..., ch] = res[pad:pad + h, pad:pad + w]
    return out


def post(exr: str, png: str, bloom=((0.004, 0.5), (0.015, 0.35), (0.05, 0.25)), threshold: float = 1.0,
         knee: float = 0.6, intensity: float = 1.0, vignette: float = 0.0, transparent: bool = False,
         tint=(0.75, 0.95, 1.0), alpha_gain: float = 1.0, view: str | None = None) -> str:
    """Bloom (sigmas as fractions of the image width) + optional vignette, then PNG via the view transform."""
    sc = bpy.context.scene
    px = load_px(exr)
    h, w, _ = px.shape
    rgb = px[..., :3]
    a = px[..., 3:4]
    if intensity > 0 and bloom:
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        x = np.maximum(lum - threshold + knee, 0.0)
        soft = np.where(lum > threshold + knee, lum - threshold, x * x / (4 * knee + 1e-6))
        bright = rgb * (soft / np.maximum(lum, 1e-5))[..., None]
        bright *= np.array(tint, dtype=np.float32)
        bl = _gauss_fft(bright, [(s * w, wt) for s, wt in bloom]) * intensity
        bl = np.maximum(bl, 0.0)
        rgb = rgb + bl
        if transparent:
            bl_l = bl @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
            a = np.clip(a + bl_l[..., None] * alpha_gain, 0.0, 1.0)
    if vignette > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / math.sqrt(2)
        v = 1.0 - vignette * np.clip((r - 0.35) / 0.65, 0, 1) ** 1.6
        rgb = rgb * v[..., None]
    out = np.concatenate([rgb, a], axis=2).astype(np.float32)
    img = bpy.data.images.new("LG_post", w, h, alpha=True, float_buffer=True)
    img.pixels.foreach_set(out.ravel())
    s = sc.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGBA" if transparent else "RGB"
    s.color_depth = "8"
    s.compression = 30
    old = sc.view_settings.view_transform
    if view:
        sc.view_settings.view_transform = view
    img.save_render(png, scene=sc)
    sc.view_settings.view_transform = old
    bpy.data.images.remove(img)
    print(f"[logo] wrote {png} ({w}x{h})")
    return png


def mask_render(path: str, white, cut, res: int, samples: int = 16) -> str:
    """Monochrome silhouette: `white` objects flat white, `cut` objects holdout, everything else hidden.
    Writes a white-on-transparent PNG (antialiased alpha)."""
    sc = bpy.context.scene
    wm = mat_emit("LG_MaskWhite", "FFFFFF", 1.0)
    hm, nt = new_mat("LG_MaskHold")
    if nt is not None:
        out = nt.nodes["Material Output"]
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        ho = node(nt, "ShaderNodeHoldout")
        nt.links.new(ho.outputs[0], out.inputs["Surface"])
    keep = set(o.name for o in white) | set(o.name for o in cut)
    for o in sc.objects:
        if o.type == "MESH" and o.name not in keep:
            o.hide_render = True
        if o.type == "LIGHT":
            o.hide_render = True
    for o in white + cut:
        m = wm if o in white else hm
        o.data.materials.clear()
        o.data.materials.append(m)
        for p in o.data.polygons:
            p.material_index = 0
        o.visible_camera = True
        o.hide_render = False
    cam = sc.camera
    cam.data.dof.use_dof = False
    world("000000", 0.0)
    sc.render.film_transparent = True
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = res
    exr = os.path.splitext(path)[0] + "_mask.exr"
    render_exr(exr)
    px = load_px(exr)
    a = np.clip(px[..., 3:4] * np.minimum(px[..., 0:1] * 1.0, 1.0) / np.maximum(px[..., 3:4], 1e-6), 0, 1)
    a = np.clip(px[..., 0:1], 0, 1)    # premultiplied white == coverage of white
    out = np.concatenate([a, a, a, a], axis=2).astype(np.float32)   # premultiplied white
    img = bpy.data.images.new("LG_mask", res, res, alpha=True, float_buffer=True)
    img.pixels.foreach_set(out.ravel())
    s = sc.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGBA"
    s.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    img.save_render(path, scene=sc)
    os.remove(exr)
    print(f"[logo] wrote {path} (mask)")
    return path
