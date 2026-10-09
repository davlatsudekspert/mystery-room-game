class_name SettingsPanel
extends PanelContainer
## Reusable settings panel (main menu + pause): language (EN → RU → UZ), audio, text size,
## vibration, camera motion, restore purchases, delete progress.
## Two columns for landscape; the body scrolls when the screen is too short (large text on a small phone).
## Text size previews live: the panel rebuilds itself at the new size.

signal closed

## Public privacy policy (Google Play and App Store also link to it).
const PRIVACY_URL := "https://sites.google.com/view/mysteryroom-privacy"
const DESIGN_W := 1500.0

var _lang_buttons: Dictionary = {}
var _scale_buttons: Array[Button] = []
var _scroll: ScrollContainer


func _ready() -> void:
	_build()
	Settings.changed.connect(_on_setting_changed)
	Loc.language_changed.connect(_on_language_changed)


func _on_language_changed(_code: String) -> void:
	_refresh()


func _on_setting_changed(key: String) -> void:
	if key == "text_scale" and is_inside_tree():
		_rebuild.call_deferred() # deferred: the change comes from a button of this panel, mid-signal


func _rebuild() -> void:
	if not is_inside_tree():
		return
	var keep := _scroll.scroll_vertical if _scroll else 0
	_build()
	await get_tree().process_frame
	if is_instance_valid(_scroll):
		_scroll.scroll_vertical = keep


func _build() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	_lang_buttons.clear()
	_scale_buttons.clear()
	theme = UITheme.build()
	custom_minimum_size = Vector2(UITheme.panel_width(DESIGN_W), 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	add_child(v)
	var content := VBoxContainer.new() # everything but the footer scrolls when the screen is short
	content.add_theme_constant_override("separation", 14)
	content.add_child(UITheme.title("ui.settings", 50))
	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 48)
	var left := VBoxContainer.new()
	left.add_theme_constant_override("separation", 12)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(left)
	cols.add_child(right)
	content.add_child(cols)
	_scroll = UITheme.scroll_fit(content, self, UITheme.usable_rect().size.y)
	v.add_child(_scroll)
	# language — fixed order EN, RU, UZ; names are shown natively
	left.add_child(_row_label("ui.language"))
	var lh := UITheme.button_row(14)
	for code in Loc.SUPPORTED:
		var b := UITheme.button(Loc.NATIVE_NAMES[code], 200)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.toggle_mode = true
		b.pressed.connect(func() -> void:
			Loc.choose(code)
			_refresh())
		lh.add_child(b)
		_lang_buttons[code] = b
	left.add_child(lh)
	# text size: each "A" is drawn at the size it gives on this screen
	left.add_child(_row_label("ui.text_size"))
	var sh := UITheme.button_row(12)
	for sc in Settings.TEXT_SCALES:
		var b := UITheme.button("A", 110)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.toggle_mode = true
		b.remove_meta("ui_min_w")
		b.add_theme_font_size_override("font_size", UITheme.size(26, sc))
		b.pressed.connect(func() -> void:
			Settings.set_value("text_scale", sc)) # → changed → the panel rebuilds at the new size
		sh.add_child(b)
		_scale_buttons.append(b)
	left.add_child(sh)
	left.add_child(_toggle("ui.haptics", "haptics"))
	left.add_child(_toggle("ui.safe_graphics", "safe_graphics"))
	right.add_child(_slider("ui.music", "music_volume"))
	right.add_child(_slider("ui.sfx", "sfx_volume"))
	right.add_child(_slider("ui.ambience", "ambience_volume"))
	right.add_child(_slider("ui.brightness", "brightness", 0.7, 1.6))
	right.add_child(_toggle("ui.reduce_motion", "reduce_motion"))
	var bottom := UITheme.button_row(16)
	var restore := UITheme.button("ui.restore", 420)
	restore.pressed.connect(func() -> void:
		Premium.restore_purchases()
		SceneManager.toast(tr("ui.restored")))
	bottom.add_child(restore)
	var privacy := UITheme.button("ui.privacy", 380)
	privacy.flat = true
	privacy.add_theme_color_override("font_color", UITheme.BRASS_HI)
	privacy.pressed.connect(func() -> void: OS.shell_open(PRIVACY_URL))
	bottom.add_child(privacy)
	var close := UITheme.button("ui.close", 240)
	close.pressed.connect(func() -> void: closed.emit())
	bottom.add_child(close)
	v.add_child(bottom)
	# if the three do not fit on one line (large text), only Close stays pinned; the others scroll with the body
	var row_w := 0.0
	for b: Control in bottom.get_children():
		row_w += b.get_combined_minimum_size().x + 16.0
	if row_w - 16.0 > custom_minimum_size.x - 36.0:
		var extra := UITheme.button_row(16)
		for b: Control in [restore, privacy]:
			bottom.remove_child(b)
			extra.add_child(b)
		content.add_child(extra)
	_refresh()


func _row_label(key: String) -> Label:
	var l := UITheme.label(key, 26, UITheme.BRASS_HI)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


func _slider(key: String, setting: String, min_v: float = 0.0, max_v: float = 1.0) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 20)
	var l := UITheme.label(key, 26)
	l.custom_minimum_size = Vector2(round(280 * UITheme.wscale()), 0)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size_flags_vertical = Control.SIZE_FILL
	h.add_child(l) # wraps onto two lines rather than being cut off with "…"
	var s := HSlider.new()
	s.min_value = min_v
	s.max_value = max_v
	s.step = 0.05
	s.value = float(Settings.get_value(setting))
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.custom_minimum_size = Vector2(0, UITheme.target(64, 8.0)) # the whole row height is the touch target
	s.value_changed.connect(func(val: float) -> void: Settings.set_value(setting, val))
	h.add_child(s)
	return h


func _toggle(key: String, setting: String) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 20)
	var l := UITheme.label(key, 26)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size_flags_vertical = Control.SIZE_FILL
	h.add_child(l)
	var b := UITheme.button("", 200)
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
