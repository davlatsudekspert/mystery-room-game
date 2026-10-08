class_name SettingsPanel
extends PanelContainer
## Reusable settings panel (main menu + pause): language (EN → RU → UZ), audio, text size,
## vibration, camera motion, restore purchases, delete progress.

signal closed

var _lang_buttons: Dictionary = {}
var _scale_buttons: Array[Button] = []


func _ready() -> void:
	theme = UITheme.build()
	custom_minimum_size = Vector2(980, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 18)
	add_child(v)
	v.add_child(UITheme.title("ui.settings", 50))
	# language — fixed order EN, RU, UZ; names are shown natively
	v.add_child(_row_label("ui.language"))
	var lh := HBoxContainer.new()
	lh.add_theme_constant_override("separation", 14)
	lh.alignment = BoxContainer.ALIGNMENT_CENTER
	for code in Loc.SUPPORTED:
		var b := UITheme.button(Loc.NATIVE_NAMES[code], 260)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.toggle_mode = true
		b.pressed.connect(func() -> void:
			Loc.choose(code)
			_refresh())
		lh.add_child(b)
		_lang_buttons[code] = b
	v.add_child(lh)
	v.add_child(_slider("ui.music", "music_volume"))
	v.add_child(_slider("ui.sfx", "sfx_volume"))
	v.add_child(_slider("ui.ambience", "ambience_volume"))
	v.add_child(_row_label("ui.text_size"))
	var sh := HBoxContainer.new()
	sh.alignment = BoxContainer.ALIGNMENT_CENTER
	sh.add_theme_constant_override("separation", 12)
	for sc in Settings.TEXT_SCALES:
		var b := UITheme.button("A", 120)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.toggle_mode = true
		b.add_theme_font_size_override("font_size", int(26 * sc))
		b.pressed.connect(func() -> void:
			Settings.set_value("text_scale", sc)
			_refresh())
		sh.add_child(b)
		_scale_buttons.append(b)
	v.add_child(sh)
	v.add_child(_toggle("ui.haptics", "haptics"))
	v.add_child(_toggle("ui.reduce_motion", "reduce_motion"))
	var bottom := HBoxContainer.new()
	bottom.alignment = BoxContainer.ALIGNMENT_CENTER
	bottom.add_theme_constant_override("separation", 16)
	var restore := UITheme.button("ui.restore", 460)
	restore.pressed.connect(func() -> void:
		Premium.restore_purchases()
		SceneManager.toast(tr("ui.restored")))
	bottom.add_child(restore)
	var close := UITheme.button("ui.close", 240)
	close.pressed.connect(func() -> void: closed.emit())
	bottom.add_child(close)
	v.add_child(bottom)
	_refresh()


func _row_label(key: String) -> Label:
	var l := UITheme.label(key, 26, UITheme.BRASS_HI)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


func _slider(key: String, setting: String) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 20)
	var l := UITheme.label(key, 26)
	l.custom_minimum_size = Vector2(330, 0)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	h.add_child(l)
	var s := HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.05
	s.value = float(Settings.get_value(setting))
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.custom_minimum_size = Vector2(0, 56)
	s.value_changed.connect(func(val: float) -> void: Settings.set_value(setting, val))
	h.add_child(s)
	return h


func _toggle(key: String, setting: String) -> Control:
	var h := HBoxContainer.new()
	var l := UITheme.label(key, 26)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	var b := UITheme.button("", 220)
	b.toggle_mode = true
	b.button_pressed = bool(Settings.get_value(setting))
	b.text = "ui.on" if b.button_pressed else "ui.off"
	b.toggled.connect(func(on: bool) -> void:
		Settings.set_value(setting, on)
		b.text = "ui.on" if on else "ui.off")
	h.add_child(b)
	return h


func _refresh() -> void:
	var cur := Loc.current()
	for code: String in _lang_buttons:
		(_lang_buttons[code] as Button).set_pressed_no_signal(code == cur)
	var sc := float(Settings.get_value("text_scale"))
	for i in _scale_buttons.size():
		_scale_buttons[i].set_pressed_no_signal(is_equal_approx(Settings.TEXT_SCALES[i], sc))
