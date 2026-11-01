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


orm("M_Iron_Rust", "iron_rust", 1.0, metallic=1)          # ORM blue channel carries the metal/rust mix
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
print("ch2x materials written to", OUT)
