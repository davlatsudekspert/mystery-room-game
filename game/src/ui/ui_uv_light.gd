class_name UIUVLight
extends Control
## The UV lamp shining on a sheet of paper in the reader (Leyla's notebook, the UV page; owner feedback: the old
## flat violet rectangle looked cheap). A child of the sheet (a PanelContainer), drawn before the text so the ink
## stays on top; it draws over the whole sheet, beyond its own content rect, with uv_light.gdshader: a feathered
## violet pool over the written part of the sheet that is gone well inside its edges, a faint halo and fluorescing
## fibres. Ink that glows under it: glow_label() for text, glow_picture() for glyphs (uv_ink.gdshader).

const INK := Color("b4ffe4") # fluorescent ink: pale mint, ≥ 4.5:1 on the lit paper
const LIGHT_SHADER := preload("res://src/ui/uv_light.gdshader")
const INK_SHADER := preload("res://src/ui/uv_ink.gdshader")
const INSET := 0.14 # uv_ink.gdshader: the glyph is drawn this far inside its rect, the halo uses the margin

var paper: Control # the sheet the light falls on
var focus: Control # what the lamp is aimed at (the pool covers the sheet's middle; the writing is in it)
var strength := 1.0:
	set(v):
		strength = v
		(material as ShaderMaterial).set_shader_parameter("strength", v)


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := ShaderMaterial.new()
	m.shader = LIGHT_SHADER
	material = m


## Adds the light to `sheet` (under its content), aimed at `target`.
static func shine(sheet: Control, target: Control, start: float = 1.0) -> UIUVLight:
	var l := UIUVLight.new()
	l.paper = sheet
	l.focus = target
	sheet.add_child(l)
	sheet.move_child(l, 0)
	l.strength = start
	for c: Control in [sheet, target]:
		c.item_rect_changed.connect(l.queue_redraw)
	return l


func _draw() -> void:
	if not is_instance_valid(paper):
		return
	var xf := get_global_transform().affine_inverse()
	var sheet := Rect2(xf * paper.global_position, paper.size)
	if sheet.size.x < 1.0 or sheet.size.y < 1.0:
		return
	# the pool lights the middle of the sheet, where the writing is; its halo (1.25 × the radius) ends inside the
	# sheet, so no edge of the light is ever seen
	var m := material as ShaderMaterial
	m.set_shader_parameter("center", Vector2(0.5, 0.52))
	m.set_shader_parameter("radius", Vector2(0.4, 0.38))
	draw_rect(sheet, Color.WHITE)


## Text in fluorescent ink: pale mint with a soft glow (a translucent outline and a wider, fainter shadow halo).
static func glow_label(l: Label) -> void:
	var k := UIOrnament.scale_k()
	l.add_theme_color_override("font_color", INK)
	l.add_theme_color_override("font_outline_color", Color(0.62, 1.0, 0.86, 0.32))
	l.add_theme_constant_override("outline_size", int(round(5.0 * k)))
	l.add_theme_color_override("font_shadow_color", Color(0.55, 1.0, 0.85, 0.14))
	l.add_theme_constant_override("shadow_outline_size", int(round(18.0 * k)))
	l.add_theme_constant_override("shadow_offset_x", 0)
	l.add_theme_constant_override("shadow_offset_y", 0)


## A glyph in fluorescent ink: `side` is the glyph's own size; the rect grows so the halo has room around it.
static func glow_picture(tex: Texture2D, side: float) -> TextureRect:
	var t := TextureRect.new()
	t.texture = tex
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_SCALE
	t.custom_minimum_size = Vector2.ONE * roundf(side / (1.0 - 2.0 * INSET))
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := ShaderMaterial.new()
	m.shader = INK_SHADER
	m.set_shader_parameter("inset", INSET)
	t.material = m
	return t
