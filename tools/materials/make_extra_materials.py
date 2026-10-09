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
std("M_Decal_Photo_Leyla", {"roughness": 0.3, "metallic_specular": 0.6}, D + "photo_3.jpg")  # glossy 1970s print
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
# M_Cork is textured (procedural cork in tools/textures/fetch_textures.py)
std("M_String_Red", {"albedo_color": hexc("A0201C"), "roughness": 0.8})
std("M_Felt", {"albedo_color": hexc("3A3A3A"), "roughness": 1.0})
std("M_Echo_Fallback", {"albedo_color": hexc("CFF6FF", 0.3), "transparency": 1, "shading_mode": 0})
# props agent: shadow lock emblem, poster frame, banker's lamp, chalk, darkroom bottles
std("M_Decal_Emblem", {"transparency": 2, "alpha_scissor_threshold": 0.4, "roughness": 0.95}, D + "wall_emblem.png")
std("M_Lacquer_Black", {"albedo_color": hexc("141211"), "roughness": 0.32, "metallic_specular": 0.55})
std("M_Glass_Green", {"albedo_color": hexc("16472A"), "roughness": 0.07, "metallic_specular": 0.75, "rim_enabled": "true",
    "rim": 0.25, "rim_tint": 0.6})
std("M_Chalk", {"albedo_color": hexc("ECE6D6"), "roughness": 1.0})
std("M_Glass_Amber", {"albedo_color": hexc("5A2A0C", 0.82), "transparency": 1, "roughness": 0.08, "metallic_specular": 0.7})

# ---------------------------------------------------------------- Chapter 2 (Records Archive B)
# New slots of docs/models/ch2.md §0 and the M_Decal_* slots of §3–§6. Model UVs are world-scale
# (1 UV unit = 1 m), so tiling materials use uv1_scale = 1 / tile_m. Mobile renderer: plain
# StandardMaterial3D / ORMMaterial3D, at most albedo + normal + ORM. Tints of reused CC0 texture sets
# were computed once from the texture means (linear ratio target / mean) and are hard-coded so a
# re-run is deterministic.
TX = "res://assets/textures/"
D2 = D + "ch2/"


def orm(name, folder, tile_m, props=None, anisotropic=False):
    """ORMMaterial3D over game/assets/textures/<folder>/{albedo.jpg, normal.png, orm.jpg}
    (same layout as tools/textures/fetch_textures.py write_textured_tres)."""
    uv = f"{1.0 / tile_m:.4f}".rstrip("0").rstrip(".")
    lines = ['[gd_resource type="ORMMaterial3D" load_steps=4 format=3]', "",
             f'[ext_resource type="Texture2D" path="{TX}{folder}/albedo.jpg" id="1"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/normal.png" id="2"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/orm.jpg" id="3"]', "",
             "[resource]", f'resource_name = "{name}"', 'albedo_texture = ExtResource("1")',
             'orm_texture = ExtResource("3")', "metallic = 0", "roughness = 1.0", "normal_enabled = true",
             'normal_texture = ExtResource("2")', "ao_enabled = true", f"uv1_scale = Vector3({uv}, {uv}, {uv})"]
    for k, v in (props or {}).items():
        lines.append(f"{k} = {v}")
    if anisotropic:
        lines.append("texture_filter = 5")  # LINEAR_WITH_MIPMAPS_ANISOTROPIC: floors are seen at grazing angles
    open(os.path.join(OUT, name + ".tres"), "w").write("\n".join(lines) + "\n")


def tiled(name, folder, tile_m, props):
    """StandardMaterial3D reusing a texture set's albedo + normal with constant roughness (and a tint)."""
    uv = f"{1.0 / tile_m:.4f}".rstrip("0").rstrip(".")
    p = dict(props)
    p.update({"normal_enabled": "true", "normal_texture": 'ExtResource("2")',
              "uv1_scale": f"Vector3({uv}, {uv}, {uv})"})
    std(name, p, TX + folder + "/albedo.jpg", [("Texture2D", TX + folder + "/normal.png")])


# Linoleum: procedural set from tools/textures/make_decals_ch2.py; one repeat = 2 x 2 tiles of 0.30 m.
orm("M_Linoleum", "linoleum", 0.6, anisotropic=True)
# Institutional green eggshell paint over the plaster texture (plaster mean #ACAA98 -> #6F8C78).
tiled("M_Paint_Green", "plaster_wall", 2.0, {"albedo_color": hexc("A7D3CB"), "roughness": 0.6, "normal_scale": 0.7,
      "metallic_specular": 0.45})
# Cast concrete: the Concrete036 texture set of M_Stone (mean #87847B, close to the #8C8A84 target).
orm("M_Concrete", "stone", 1.0)
# Cream stove-enamel on steel: the M_Enamel_Cream set, tinted from #E4D6BD to #D8CFB4.
orm("M_Steel_Cream", "enamel_cream", 0.5, {"albedo_color": hexc("F2F6F3")})
std("M_Screen", {"albedo_color": hexc("E9E6DF"), "roughness": 0.95, "metallic_specular": 0.3})
std("M_Velvet", {"albedo_color": hexc("5A1420"), "roughness": 0.9, "metallic_specular": 0.35, "rim_enabled": "true",
    "rim": 0.45, "rim_tint": 0.35})
std("M_Film", {"transparency": 1, "albedo_color": hexc("3A2414", 0.9), "roughness": 0.25, "metallic_specular": 0.6})
std("M_Tape", {"albedo_color": hexc("4A2C1A"), "roughness": 0.35, "metallic_specular": 0.55})
# Archive-box board: the paper set tinted from #D1C2A4 to #9A7B55, with its stains.
tiled("M_Cardboard", "paper", 0.5, {"albedo_color": hexc("BDA387"), "roughness": 0.85, "normal_scale": 1.2})
std("M_Linen", {"albedo_color": hexc("8C7B5E"), "roughness": 0.8})

# Chapter 2 decals (images: tools/textures/make_decals_ch2.py, table: docs/models/ch2_decals.md).
SCISSOR = {"transparency": 2, "alpha_scissor_threshold": 0.5}
std("M_Decal_RoutingChart", {"roughness": 0.3, "metallic_specular": 0.6}, D2 + "routing_chart.png")
std("M_Decal_DestSymbols", dict(SCISSOR, roughness=0.32, metallic_specular=0.6), D2 + "dest_symbols.png")
std("M_Decal_Badge", {"roughness": 0.18, "metallic_specular": 0.6}, D2 + "badge.png")  # laminated
std("M_Decal_IndexCard", dict(SCISSOR, roughness=0.85), D2 + "index_card.png")       # notches are cut out (alpha 0)
std("M_Decal_RequestCard", {"roughness": 0.85}, D2 + "request_card.png")
std("M_Decal_FileCover", {"roughness": 0.8}, D2 + "file_cover.png")
for y in (1996, 1997, 1998):
    std(f"M_Decal_TapeLabel_{y}", dict(SCISSOR, roughness=0.75), D2 + f"tape_label_{y}.png")
for k in range(4):
    # sprocket holes are cut out; a faint self-glow keeps the frames readable on the light box
    std(f"M_Decal_FilmStrip_{k}", dict(SCISSOR, roughness=0.22, metallic_specular=0.6, emission_enabled="true",
        emission=hexc("FFF4E0"), emission_energy_multiplier=0.35, emission_operator=1,
        emission_texture='ExtResource("1")'), D2 + f"film_strip_{k}.png")
std("M_Decal_ReelCanLid", dict(SCISSOR, roughness=0.5, metallic_specular=0.55), D2 + "reel_can_lid.png")
std("M_Decal_SlideMark", {"transparency": 1, "roughness": 0.08, "metallic_specular": 0.7}, D2 + "slide_mark.png")
std("M_Decal_ArchiveRules", {"roughness": 0.85}, D2 + "archive_rules.jpg")
std("M_Decal_BoxLabels", {"roughness": 0.85}, D2 + "box_labels.jpg")

# ---------------------------------------------------------------- Chapter 3 (The Underground Facility, Level -2)
# New slots of docs/models/ch3.md §0 and the decals of §12 (images: tools/textures/make_decals_ch3.py; the tiling
# sets tile_glazed / rock / chequer are procedural and written by the same script). World-scale model UVs.
D3 = D + "ch3/"


def orm3(name, folder, tile_m, metallic=0, anisotropic=False):
    """Like orm() but with the metallic factor given (it multiplies the ORM blue channel)."""
    uv = f"{1.0 / tile_m:.4f}".rstrip("0").rstrip(".")
    lines = ['[gd_resource type="ORMMaterial3D" load_steps=4 format=3]', "",
             f'[ext_resource type="Texture2D" path="{TX}{folder}/albedo.jpg" id="1"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/normal.png" id="2"]',
             f'[ext_resource type="Texture2D" path="{TX}{folder}/orm.jpg" id="3"]', "",
             "[resource]", f'resource_name = "{name}"', 'albedo_texture = ExtResource("1")',
             'orm_texture = ExtResource("3")', f"metallic = {metallic}", "roughness = 1.0", "normal_enabled = true",
             'normal_texture = ExtResource("2")', "ao_enabled = true", f"uv1_scale = Vector3({uv}, {uv}, {uv})"]
    if anisotropic:
        lines.append("texture_filter = 5")
    open(os.path.join(OUT, name + ".tres"), "w").write("\n".join(lines) + "\n")


orm3("M_Tile_Glazed", "tile_glazed", 0.6)               # 0.15 m glazed tiles, 4 x 4 per repeat
orm3("M_Rock", "rock", 2.4)                             # dark wet fractured rock
orm3("M_Chequer", "chequer", 0.30, metallic=1, anisotropic=True)   # tread plate; metal 0.85 in the ORM map
std("M_Porcelain", {"albedo_color": hexc("5A3320"), "roughness": 0.15, "metallic_specular": 0.65,
    "clearcoat_enabled": "true", "clearcoat": 0.6, "clearcoat_roughness": 0.1})        # brown-glazed bushings
std("M_Shader_Quad", {"albedo_color": hexc("1A1F1E"), "roughness": 0.3})           # placeholder, code replaces it
for _sym in ("Sun", "Moon", "Star", "Triangle", "Circle", "Square", "Diamond"):
    std(f"M_Decal_Sym_{_sym}", dict(SCISSOR, roughness=0.4), D3 + f"sym_{_sym.lower()}.png")
std("M_Decal_InterlockPlate", {"roughness": 0.22, "metallic_specular": 0.6}, D3 + "interlock_plate.png")  # vitreous enamel
std("M_Decal_EcgPaper", {"roughness": 0.85}, D3 + "ecg_paper.png")
std("M_Decal_GrowthLog", {"roughness": 0.85}, D3 + "growth_log.png")      # DecalLoc swaps growth_log_ru / _uz
std("M_Decal_StrandNote", {"roughness": 0.85}, D3 + "strand_note.png")    # DecalLoc swaps strand_note_ru / _uz
std("M_Decal_StaffPhoto", {"roughness": 0.3, "metallic_specular": 0.6}, D2 + "film_frame_2.jpg")  # the 41 staff
print("extra materials written to", OUT)
