#!/usr/bin/env python3
"""Godot decal materials of the upper floor of the Chapter 2 expansion (R5 Reading Gallery, R6 Plate Room, R7 Director's Office).
Images come from tools/textures/make_decals_ch2x_upper.py. The other slots used by those models already exist
(M_Wallpaper_Office, M_Emissive_Safelight, M_Acetate, M_Paint_Black, ...).
New slots: M_Decal_RollTags, M_Decal_CabinetLabel, M_Decal_Negatives, M_Decal_Prints."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "materials")
D2X = "res://assets/textures/decals/ch2x/"

for nm, f, rough in (("M_Decal_RollTags", "roll_tags.png", 0.35), ("M_Decal_CabinetLabel", "cabinet_label.png", 0.4),
                     ("M_Decal_Negatives", "negatives.png", 0.25), ("M_Decal_Prints", "print_proj.png", 0.5)):
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "",
             f'[ext_resource type="Texture2D" path="{D2X}{f}" id="1"]', "", "[resource]", f'resource_name = "{nm}"',
             'albedo_texture = ExtResource("1")', f"roughness = {rough}", "metallic_specular = 0.6"]
    open(os.path.join(OUT, nm + ".tres"), "w").write("\n".join(lines) + "\n")
print("ch2x upper materials written to", OUT)
