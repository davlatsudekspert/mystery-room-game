#!/usr/bin/env python3
"""Write Godot materials for decals, enamel colours, books, etc. that models reference by slot name.
(The CC0 textured base library is produced by tools/textures/fetch_textures.py.)"""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "materials")
os.makedirs(OUT, exist_ok=True)

def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return f"Color({r:.4f}, {g:.4f}, {b:.4f}, {a})"

def std(name, props, tex=None, extra_ext=None):
    ext = []
    if tex:
        ext.append(("Texture2D", tex, "1"))
    for i, (t, p) in enumerate(extra_ext or [], start=2):
        ext.append((t, p, str(i)))
    lines = [f'[gd_resource type="StandardMaterial3D" load_steps={len(ext) + 1} format=3]', ""]
    for t, p, i in ext:
        lines.append(f'[ext_resource type="{t}" path="{p}" id="{i}"]')
    if ext:
        lines.append("")
    lines.append("[resource]")
    lines.append(f'resource_name = "{name}"')
    if tex:
        lines.append('albedo_texture = ExtResource("1")')
    for k, v in props.items():
        lines.append(f"{k} = {v}")
    open(os.path.join(OUT, name + ".tres"), "w").write("\n".join(lines) + "\n")

D = "res://assets/textures/decals/"
std("M_Decal_DrawerDigits", {"metallic": 0.85, "roughness": 0.38}, D + "drawer_digits.png")
std("M_Decal_ClockFace", {"roughness": 0.12}, D + "clock_face.png")
std("M_Decal_PanelDiagram", {"roughness": 0.55}, D + "panel_diagram.jpg")
std("M_Decal_RadioDial", {"roughness": 0.2, "emission_enabled": "false", "emission": hexc("FFC27A"),
    "emission_energy_multiplier": 0.6, "emission_operator": 1, "emission_texture": 'ExtResource("1")'}, D + "radio_dial.jpg")
std("M_Decal_Chalkboard", {"roughness": 0.92}, D + "chalkboard.jpg")
std("M_Decal_Poster", {"roughness": 0.85}, D + "poster_resonance.jpg")
for c in ("Crimson", "Cobalt", "Green"):
    std(f"M_Decal_VialLabel_{c}", {"roughness": 0.85}, D + f"vial_label_{c.lower()}.png")
std("M_Decal_Photos", {"roughness": 0.6}, D + "photo_0.jpg")
std("M_Decal_Drawing", {"roughness": 0.9}, D + "childs_drawing.jpg")

for name, col in {"Crimson": "8E1B2A", "Amber": "C98A1E", "Green": "2F7A3A", "Cobalt": "1F3E9E",
                  "Violet": "5B2C8C", "White": "E8E2D4"}.items():
    std(f"M_Enamel_{name}", {"albedo_color": hexc(col), "roughness": 0.28, "metallic_specular": 0.6})

std("M_Emissive_MagicEye", {"albedo_color": hexc("1E3A26"), "roughness": 0.15, "emission_enabled": "false",
    "emission": hexc("6CFF8A"), "emission_energy_multiplier": 3.0})
LEATHER = "res://assets/textures/leather/"
for name, col in {"Red": "7A2420", "Green": "26402C", "Brown": "5A3A24", "Blue": "243A5A", "Black": "2A2522"}.items():
    std(f"M_Book_{name}", {"albedo_color": hexc(col), "roughness": 0.65, "normal_enabled": "true",
        "normal_texture": 'ExtResource("2")', "uv1_scale": "Vector3(3, 3, 3)"},
        LEATHER + "albedo.jpg", [("Texture2D", LEATHER + "normal.png")])
std("M_Book_Gold", {"albedo_color": hexc("E3C27A"), "metallic": 1.0, "roughness": 0.3})
FAB = "res://assets/textures/fabric/"
std("M_Grille_Fabric", {"albedo_color": hexc("B8A27A"), "roughness": 0.95, "uv1_scale": "Vector3(6, 6, 6)"},
    FAB + "albedo.jpg")
std("M_Cork", {"albedo_color": hexc("9C7650"), "roughness": 0.95})
std("M_String_Red", {"albedo_color": hexc("A0201C"), "roughness": 0.8})
std("M_Felt", {"albedo_color": hexc("3A3A3A"), "roughness": 1.0})
std("M_Echo_Fallback", {"albedo_color": hexc("CFF6FF", 0.3), "transparency": 1, "shading_mode": 0})
print("extra materials written to", OUT)
