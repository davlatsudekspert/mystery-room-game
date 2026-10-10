class_name UISegmented
extends HBoxContainer
## A segmented control: the options sit side by side in one hairline gold frame, and the chosen one is filled
## with a soft brass tint. Each option is a plain Button (its `text` is what the player and QA see), so it
## behaves like any other button; `chosen` carries the option's id.

signal chosen(id: Variant)

var _buttons: Array[Button] = []
var _ids: Array = []


func _init() -> void:
	add_theme_constant_override("separation", 0)


## Adds an option. `translate` false shows `text` as is (language names, "A"). `expand` shares the width.
func add_option(text: String, id: Variant, expand: bool = true, translate: bool = true, min_w: float = 0.0) -> Button:
	var b := Button.new()
	b.text = text
	b.toggle_mode = true
	b.focus_mode = Control.FOCUS_NONE
	if not translate:
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	b.custom_minimum_size = Vector2(min_w, UITheme.target(78))
	if expand:
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.button_group = null
	b.pressed.connect(func() -> void:
		select(id)
		AudioManager.ui("ui_tap")
		chosen.emit(id))
	_buttons.append(b)
	_ids.append(id)
	add_child(b)
	_restyle()
	return b


## Marks the option with this id as the chosen one, without emitting `chosen`.
func select(id: Variant) -> void:
	for i in _buttons.size():
		_buttons[i].set_pressed_no_signal(_ids[i] == id)


func buttons() -> Array[Button]:
	return _buttons


func _restyle() -> void:
	var n := _buttons.size()
	for i in n:
		var b := _buttons[i]
		var normal := StyleBoxFlat.new()
		normal.bg_color = Color(0.05, 0.052, 0.062, 0.6)
		normal.border_color = Color(UITheme.BRASS, 0.55)
		normal.set_border_width_all(1)
		if i > 0:
			normal.border_width_left = 0 # one hairline between neighbours, not two
		var rl := 4 if i == 0 else 0
		var rr := 4 if i == n - 1 else 0
		normal.corner_radius_top_left = rl
		normal.corner_radius_bottom_left = rl
		normal.corner_radius_top_right = rr
		normal.corner_radius_bottom_right = rr
		normal.content_margin_left = 16
		normal.content_margin_right = 16
		normal.content_margin_top = 6
		normal.content_margin_bottom = 6
		var hover := normal.duplicate() as StyleBoxFlat
		hover.bg_color = Color(0.10, 0.09, 0.075, 0.75)
		var pressed := normal.duplicate() as StyleBoxFlat
		pressed.bg_color = Color(UITheme.BRASS, 0.26)
		b.add_theme_stylebox_override("normal", normal)
		b.add_theme_stylebox_override("hover", hover)
		b.add_theme_stylebox_override("pressed", pressed)
		b.add_theme_stylebox_override("hover_pressed", pressed)
		b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
		b.add_theme_color_override("font_color", UITheme.CREAM)
		b.add_theme_color_override("font_hover_color", UITheme.BRASS_HI)
		b.add_theme_color_override("font_pressed_color", UITheme.BRASS_HI)
		b.add_theme_color_override("font_hover_pressed_color", UITheme.BRASS_HI)
