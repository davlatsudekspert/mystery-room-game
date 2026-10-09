class_name MenuItem
extends Button
## A main-menu entry drawn as serif text with no box. Hover or press sweeps in a thin gold rule under the text,
## with a small diamond at its left end, and warms the text colour. The primary entry (Continue) is larger and
## bold, and shows its rule at rest. The whole row is the touch target; the menu's layout sets its height
## (at least UITheme.target(78)). `text` stays the translation key, like every other button.

const INDENT := 64.0 # canvas px from the row's left edge to the text; the rule's diamond sits left of the text
const DIAMOND_X := 20.0 # centre of the diamond from the row's left edge
const SIZE_NORMAL := 50 # design font sizes (UITheme.size)
const SIZE_PRIMARY := 60
const REST := Color("e9dfca")
const HOT := Color("f3cf8a")
const PRIMARY_REST := Color("efd29a")
const PRIMARY_HOT := Color("ffe3a8")
const RULE := Color("d9b46a")
const SLIDE_PX := 18.0 # the entrance rises this far

var primary := false
var _hl := 0.0 # highlight 0..1 (hover / press)
var _appear := 1.0 # entrance 0..1 (fade + rise)
var _style := StyleBoxEmpty.new()
var _hl_tween: Tween
var _hover_ok := not OS.has_feature("mobile") # a finger leaves the emulated mouse "hovering" after a tap


func _init(key: String = "", is_primary: bool = false) -> void:
	text = key
	primary = is_primary
	alignment = HORIZONTAL_ALIGNMENT_LEFT
	focus_mode = Control.FOCUS_NONE
	for s in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
		add_theme_stylebox_override(s, _style)
	add_theme_font_override("font", UITheme.display_font(primary))
	var sz := SIZE_PRIMARY if primary else SIZE_NORMAL
	set_meta("ui_font_size", sz) # UITheme.rescale() re-applies it when the player changes Text size
	add_theme_font_size_override("font_size", UITheme.size(sz))
	_apply()
	pressed.connect(func() -> void: AudioManager.ui("ui_tap"))
	mouse_entered.connect(func() -> void:
		if _hover_ok:
			_highlight(1.0))
	mouse_exited.connect(func() -> void:
		if not button_pressed:
			_highlight(0.0))
	button_down.connect(_highlight.bind(1.0))
	button_up.connect(func() -> void: _highlight(1.0 if _hover_ok and is_hovered() else 0.0))


## Entrance: fades in and rises into place after `delay` seconds.
func appear(delay: float, duration: float = 0.45) -> void:
	_set_appear(0.0)
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_method(_set_appear, 0.0, 1.0, duration).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _highlight(to: float) -> void:
	if _hl_tween != null and _hl_tween.is_valid():
		_hl_tween.kill()
	_hl_tween = create_tween()
	_hl_tween.tween_method(_set_hl, _hl, to, 0.22 if to > _hl else 0.35).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _set_hl(v: float) -> void:
	_hl = v
	_apply()


func _set_appear(v: float) -> void:
	_appear = v
	modulate.a = v
	_apply()


func _apply() -> void:
	var c := (PRIMARY_REST.lerp(PRIMARY_HOT, _hl) if primary else REST.lerp(HOT, _hl))
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		add_theme_color_override(k, c)
	# the entrance rise: shifting the top margin moves the text without fighting the VBox layout
	var rise := (1.0 - _appear) * SLIDE_PX
	_style.content_margin_left = INDENT
	_style.content_margin_right = 12.0
	_style.content_margin_top = 2.0 * rise
	_style.content_margin_bottom = 0.0
	queue_redraw()


func _draw() -> void:
	var sweep := 1.0 if primary else _hl
	var alpha := lerpf(0.55, 1.0, _hl) if primary else _hl
	if alpha <= 0.01 or sweep <= 0.01:
		return
	var font := get_theme_font("font")
	var fs := get_theme_font_size("font_size")
	var tw := font.get_string_size(tr(text), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var asc := font.get_ascent(fs)
	var desc := font.get_descent(fs)
	var top := _style.content_margin_top + (size.y - _style.content_margin_top - _style.content_margin_bottom - (asc + desc)) * 0.5
	var y := roundf(top + asc + desc * 0.75)
	var k := clampf(float(fs) / SIZE_NORMAL, 0.8, 1.8) # ornament scale follows the text size
	var th := maxf(1.5, roundf(1.6 * k))
	var x0 := DIAMOND_X
	var x_end := INDENT + tw * 1.25 + 24.0
	var x_tip := lerpf(x0 + 8.0 * k, x_end, ease(sweep, 0.6))
	# the rule: solid from the diamond to the middle of the word, then fading out to its right end
	var x_mid := minf(INDENT + tw * 0.55, x_tip)
	var col := Color(RULE, alpha)
	var clear := Color(RULE, 0.0)
	var dx := 7.0 * k
	if x_mid > x0 + dx:
		draw_rect(Rect2(x0 + dx, y - th * 0.5, x_mid - x0 - dx, th), col)
	if x_tip > x_mid:
		var pts := PackedVector2Array([Vector2(x_mid, y - th * 0.5), Vector2(x_tip, y - th * 0.5),
			Vector2(x_tip, y + th * 0.5), Vector2(x_mid, y + th * 0.5)])
		draw_polygon(pts, PackedColorArray([col, clear, clear, col]))
	# the diamond, with a short tail to its left (an arrow-like tip)
	var dy := 4.2 * k
	var dia := PackedVector2Array([Vector2(x0 - dx, y), Vector2(x0, y - dy), Vector2(x0 + dx, y), Vector2(x0, y + dy)])
	draw_colored_polygon(dia, Color(PRIMARY_HOT if primary else HOT, alpha))
	draw_rect(Rect2(x0 - dx - 7.0 * k, y - th * 0.35, 7.0 * k, th * 0.7), Color(RULE, alpha * 0.6))
