class_name UITheme
extends RefCounted
## Design tokens (docs/UI_UX.md, docs/ART_DIRECTION.md) and the generated Godot Theme.

const INK := Color("0e0f12")
const PANEL := Color(0.055, 0.06, 0.07, 0.9)
const BRASS := Color("c9a35e")
const BRASS_HI := Color("e3c27a")
const CREAM := Color("ede3cf")
const MUTED := Color("8a8172")
const DANGER := Color("b5523b")
const SUCCESS := Color("6fb39a")
const UV := Color("9c7bff")

const FONT_UI := "res://assets/fonts/NotoSans-Variable.ttf"
const FONT_DISPLAY := "res://assets/fonts/CormorantGaramond-SemiBold.ttf"
const FONT_DISPLAY_BOLD := "res://assets/fonts/CormorantGaramond-Bold.ttf"
const FONT_HAND := "res://assets/fonts/Caveat-Variable.ttf"

static var _cache: Dictionary = {}


static func scale() -> float:
	return float(Settings.get_value("text_scale"))


static func size(base: int) -> int:
	return int(round(base * scale()))


static func ui_font(weight: int = 500) -> Font:
	var key := "ui%d" % weight
	if not _cache.has(key):
		var fv := FontVariation.new()
		fv.base_font = load(FONT_UI)
		fv.variation_opentype = {"wght": weight}
		_cache[key] = fv
	return _cache[key]


static func display_font(bold: bool = false) -> Font:
	var key := "disp%d" % int(bold)
	if not _cache.has(key):
		var f: FontFile = load(FONT_DISPLAY_BOLD if bold else FONT_DISPLAY)
		var fv := FontVariation.new()
		fv.base_font = f
		fv.fallbacks = [load(FONT_UI)]
		_cache[key] = fv
	return _cache[key]


static func hand_font() -> Font:
	if not _cache.has("hand"):
		var fv := FontVariation.new()
		fv.base_font = load(FONT_HAND)
		fv.variation_opentype = {"wght": 500}
		fv.fallbacks = [load(FONT_UI)] # Caveat lacks ʻ (U+02BB) — Noto Sans covers it
		_cache["hand"] = fv
	return _cache["hand"]


static func panel_box(alpha: float = 0.9, radius: int = 14, border: float = 1.5) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(PANEL, alpha)
	sb.border_color = Color(BRASS, 0.55)
	sb.set_border_width_all(int(border))
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 12
	sb.set_content_margin_all(18)
	return sb


static func build() -> Theme:
	var t := Theme.new()
	t.default_font = ui_font(500)
	t.default_font_size = size(26)
	var btn := StyleBoxFlat.new()
	btn.bg_color = Color(0.07, 0.075, 0.085, 0.85)
	btn.border_color = Color(BRASS, 0.7)
	btn.set_border_width_all(2)
	btn.set_corner_radius_all(12)
	btn.content_margin_left = 26
	btn.content_margin_right = 26
	btn.content_margin_top = 14
	btn.content_margin_bottom = 14
	var hov := btn.duplicate() as StyleBoxFlat
	hov.border_color = BRASS_HI
	hov.bg_color = Color(0.12, 0.11, 0.09, 0.92)
	var prs := btn.duplicate() as StyleBoxFlat
	prs.bg_color = Color(BRASS, 0.85)
	var dis := btn.duplicate() as StyleBoxFlat
	dis.border_color = Color(MUTED, 0.4)
	dis.bg_color = Color(0.06, 0.06, 0.07, 0.6)
	t.set_stylebox("normal", "Button", btn)
	t.set_stylebox("hover", "Button", hov)
	t.set_stylebox("pressed", "Button", prs)
	t.set_stylebox("disabled", "Button", dis)
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", CREAM)
	t.set_color("font_hover_color", "Button", BRASS_HI)
	t.set_color("font_pressed_color", "Button", INK)
	t.set_color("font_disabled_color", "Button", MUTED)
	t.set_font_size("font_size", "Button", size(28))
	t.set_color("font_color", "Label", CREAM)
	t.set_stylebox("panel", "PanelContainer", panel_box())
	t.set_stylebox("panel", "Panel", panel_box())
	var slider_bg := StyleBoxFlat.new()
	slider_bg.bg_color = Color(MUTED, 0.35)
	slider_bg.set_corner_radius_all(4)
	slider_bg.content_margin_top = 4
	slider_bg.content_margin_bottom = 4
	var slider_fill := slider_bg.duplicate() as StyleBoxFlat
	slider_fill.bg_color = BRASS
	t.set_stylebox("slider", "HSlider", slider_bg)
	t.set_stylebox("grabber_area", "HSlider", slider_fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", slider_fill)
	return t


static func title(text: String, sz: int = 56, bold: bool = true) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", display_font(bold))
	l.add_theme_font_size_override("font_size", size(sz))
	l.add_theme_color_override("font_color", BRASS_HI)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func label(text: String, sz: int = 26, color: Color = CREAM) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size(sz))
	l.add_theme_color_override("font_color", color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func button(text: String, min_w: int = 320) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(min_w, 78)
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(func() -> void: AudioManager.ui("ui_tap"))
	return b
