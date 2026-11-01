#!/usr/bin/env python3
"""Godot materials for the Chapter 2 expansion slots (tools/textures/make_textures_ch2x.py writes the texture sets).
Model UVs are world-scale (1 UV unit = 1 m), so uv1_scale = 1 / repeat_m. Mobile-safe: ORM or Standard materials only.
New slots: M_Iron_Rust, M_Wallpaper_Cell, M_Wool_Knit, M_Steel_Galv, M_Wallpaper_Office, M_Paint_Black, M_Frost,
M_Acetate, M_Emissive_Table, M_Emissive_Safelight."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "materials")
TX = "res://assets/textures/"


def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return f"Color({r:.4f}, {g:.4f}, {b:.4f}, {a})"


def write(name, lines):
    open(os.path.join(OUT, name + ".tres"), "w").write("\n".join(lines) + "\n")


def orm(name, folder, tile_m, metallic=0, extra=None):
    uv = f"{1.0 / tile_m:.4f}".rstrip("0").rstrip(".")
    lines = ['[gd_resource type="ORMMaterial3D" load_steps=4 format=3]', "",
             f'[ext_resource type="Texture2D" path="{TX}{folder}/albedo.jpg" id="1"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/normal.png" id="2"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/orm.jpg" id="3"]', "",
             "[resource]", f'resource_name = "{name}"', 'albedo_texture = ExtResource("1")',
             'orm_texture = ExtResource("3")', f"metallic = {metallic}", "roughness = 1.0", "normal_enabled = true",
             'normal_texture = ExtResource("2")', "ao_enabled = true", f"uv1_scale = Vector3({uv}, {uv}, {uv})"]
    lines += list((extra or {}).items()) and [f"{k} = {v}" for k, v in extra.items()]
    write(name, lines)


def std(name, props):
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=1 format=3]', "", "[resource]", f'resource_name = "{name}"']
    lines += [f"{k} = {v}" for k, v in props.items()]
    write(name, lines)


orm("M_Iron_Rust", "iron_rust", 1.0, metallic=0.7)        # painted wall: ORM blue channel carries a low metal value
orm("M_Wallpaper_Cell", "wallpaper_cell", 0.5)
orm("M_Wool_Knit", "wool_knit", 0.5)
orm("M_Steel_Galv", "steel_galv", 0.5, metallic=1)
orm("M_Wallpaper_Office", "wallpaper_office", 0.4, metallic=1)
std("M_Paint_Black", {"albedo_color": hexc("151716"), "roughness": 0.85, "metallic_specular": 0.3})
std("M_Frost", {"albedo_color": hexc("E4F0F6", 0.78), "transparency": 1, "roughness": 0.8, "metallic_specular": 0.5,
    "rim_enabled": "true", "rim": 0.3, "rim_tint": 0.5})
std("M_Acetate", {"albedo_color": hexc("C9B890", 0.34), "transparency": 1, "roughness": 0.18, "metallic_specular": 0.7})
std("M_Emissive_Table", {"albedo_color": hexc("EFE9D8"), "roughness": 0.4, "emission_enabled": "true",
    "emission": hexc("FFF1D0"), "emission_energy_multiplier": 1.6})
std("M_Emissive_Safelight", {"albedo_color": hexc("5A0A08"), "roughness": 0.3, "emission_enabled": "true",
    "emission": hexc("FF1A0E"), "emission_energy_multiplier": 2.4})
D2X = TX + "decals/ch2x/"
for nm, f in (("M_Decal_PipeDiagram", "pipe_diagram.png"), ("M_Decal_LiftPlate", "lift_plate.png")):
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "", f'[ext_resource type="Texture2D" path="{D2X}{f}" id="1"]', "", "[resource]", f'resource_name = "{nm}"', 'albedo_texture = ExtResource("1")', "roughness = 0.35", "metallic_specular = 0.6"]
    write(nm, lines)

# ---- R4 Cold Store (tools/textures/make_decals_cold.py writes the images) ----
std("M_Enamel_Ice", {"albedo_color": hexc("C6D6E2"), "roughness": 0.45, "metallic": 0.15, "metallic_specular": 0.5})
std("M_Emissive_Cold", {"albedo_color": hexc("D8EEFF"), "roughness": 0.4, "emission_enabled": "true",
    "emission": hexc("D8EEFF"), "emission_energy_multiplier": 1.5})
COLD_DECALS = (("M_Decal_ChestRings", "chest_ring.png", {}), ("M_Decal_ChestPlate", "chest_plate.png", {"metallic": 0.6}),
               ("M_Decal_CarriageTags", "carriage_tags.png", {}), ("M_Decal_PlanPlate", "plan_plate.png", {}),
               ("M_Decal_CanLabel_1", "can_label_1.png", {}), ("M_Decal_CanLabel_2", "can_label_2.png", {}),
               ("M_Decal_CanLabel_3", "can_label_3.png", {}), ("M_Decal_CanLabel_4", "can_label_4.png", {}))
for nm, f, extra in COLD_DECALS:
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "", f'[ext_resource type="Texture2D" path="{D2X}{f}" id="1"]', "", "[resource]",
             f'resource_name = "{nm}"', 'albedo_texture = ExtResource("1")', "roughness = 0.4", "metallic_specular = 0.6"] + [f"{k} = {v}" for k, v in extra.items()]
    write(nm, lines)
# alpha decals: stencil paint, finger-writing under the frost, hoar-frost patches on walls and floor (alpha blend, no shadows)
for nm, f, rough in (("M_Decal_SafeStencil", "meridian_stencil.png", 0.85), ("M_Decal_FrostSign", "frost_sign_0.png", 0.8),
                     ("M_Decal_FrostPatch", "frost_patch.png", 0.9)):
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "", f'[ext_resource type="Texture2D" path="{D2X}{f}" id="1"]', "", "[resource]",
             f'resource_name = "{nm}"', "transparency = 1", "cull_mode = 2", "shading_mode = 1" if nm == "M_Decal_FrostSign" else "shading_mode = 1",
             'albedo_texture = ExtResource("1")', f"roughness = {rough}"]
    write(nm, lines)
# the wipe-reveal frost pane (N5): ShaderMaterial, see game/assets/materials/frost_reveal.gdshader for the uniforms
write("M_Decal_FrostPane", ['[gd_resource type="ShaderMaterial" load_steps=3 format=3]', "",
      '[ext_resource type="Shader" path="res://assets/materials/frost_reveal.gdshader" id="1"]',
      f'[ext_resource type="Texture2D" path="{D2X}frost_tex.png" id="2"]', "", "[resource]", 'resource_name = "M_Decal_FrostPane"',
      'shader = ExtResource("1")', 'shader_parameter/frost_tex = ExtResource("2")'])
print("ch2x materials written to", OUT)
