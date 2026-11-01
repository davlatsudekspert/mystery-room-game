#!/usr/bin/env python3
"""Godot materials for the Night Cell / hall decals (images from tools/textures/make_decals_ch2x_cell.py).
Slots: M_Decal_CellDrawing, M_Decal_FloorPlan (opaque), M_Decal_Sheet, M_Decal_TableMask (alpha: transparency + unshaded-ish)."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "materials")
D2X = "res://assets/textures/decals/ch2x/"


def write(name, lines):
    open(os.path.join(OUT, name + ".tres"), "w").write("\n".join(lines) + "\n")


def decal(nm, f, alpha=False, rough=0.8):
    lines = ['[gd_resource type="StandardMaterial3D" load_steps=2 format=3]', "",
             f'[ext_resource type="Texture2D" path="{D2X}{f}" id="1"]', "", "[resource]", f'resource_name = "{nm}"',
             'albedo_texture = ExtResource("1")', f"roughness = {rough}"]
    if alpha:
        lines += ["transparency = 1", "cull_mode = 2"]
    write(nm, lines)


decal("M_Decal_CellDrawing", "cell_drawing.png")
decal("M_Decal_FloorPlan", "floor_plan.png", rough=0.4)
decal("M_Decal_Sheet", "sheet_print.png", alpha=True, rough=0.25)
decal("M_Decal_TableMask", "table_mask.png", alpha=True)
print("cell materials written to", OUT)
