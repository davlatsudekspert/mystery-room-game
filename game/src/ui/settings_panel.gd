class_name SettingsPanel
extends PanelContainer
## Settings (main menu and pause): a dark panel with a hairline gold frame, the title in the display serif over
## a gold rule, and four sections under small-caps headers: LANGUAGE (segmented), SOUND (thin sliders with a
## readout), DISPLAY & COMFORT (text size segments, brightness, reduce camera motion) and OTHER (vibration,
## simplified graphics with a one-line description). Rows share one height (a full touch target) with the
## label on the left and the control on the right. Two columns when the panel is wide enough, otherwise one.
## Only the body scrolls, under soft edge fades, when the screen is short; the header and the footer (Restore
## purchases, Privacy policy, Close) never move and never overlap it.
## Text size previews live: the panel rebuilds itself at the new size. A language change re-translates in place.

signal closed

## Public privacy policy (Google Play and App Store also link to it).
const PRIVACY_URL := "https://sites.google.com/view/mysteryroom-privacy"
const DESIGN_W := 1500.0
const MIN_COL_W := 560.0 # design px per column; narrower than this and the sections stack in one column
const COL_GAP := 56.0
const LABEL_SIZE := 26
const HEADER_SIZE := 22
const DESC_SIZE := 20
const STATE_SIZE := 20
const FADE_H := 44.0

var _scroll: ScrollContainer
var _scroll_host: Control
var _content: Control
var _header: Control
var _footer: Control
var _fade_top: TextureRect
var _fade_bottom: TextureRect
var _lang_seg: UISegmented
var _scale_seg: UISegmented
var _lang_buttons: Dictionary = {} # code -> Button (QA presses them by their native name)
var _scale_buttons: Array[Button] = []
var _fit_queued := false


func _ready() -> void:
	_build()
	Settings.changed.connect(_on_setting_changed)
	Loc.language_changed.connect(_on_language_changed)


func _on_language_changed(_code: String) -> void:
	_refresh()
	_queue_fit()


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


# ====================================================================== build
func _build() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	_lang_buttons.clear()
	_scale_buttons.clear()
	theme = UITheme.build()
	add_theme_stylebox_override("panel", UITheme.panel_box(0.96, 6, 1.0))
	custom_minimum_size = Vector2(UITheme.panel_width(DESIGN_W), 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	add_child(v)
	# --- header: the title over a gold rule with a diamond
	_header = VBoxContainer.new()
	_header.add_theme_constant_override("separation", 0)
	_header.add_child(UITheme.title("ui.settings", 50))
	_header.add_child(UIOrnament.rule(0.0, 26.0))
	_header.add_child(_gap(10.0))
	v.add_child(_header)
	# --- body: the sections, in two columns when there is room, scrolling under edge fades when short
	_scroll_host = Control.new()
	_scroll_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_scroll_host)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER # the edge fades say "more below"
	_scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scroll_host.add_child(_scroll)
	var pad := MarginContainer.new() # a little air at the right edge of the columns
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_theme_constant_override("margin_right", 10)
	pad.add_theme_constant_override("margin_left", 2)
	_scroll.add_child(pad)
	_content = _columns()
	pad.add_child(_content)
	_fade_top = _fade(true)
	_fade_bottom = _fade(false)
	_scroll_host.add_child(_fade_top)
	_scroll_host.add_child(_fade_bottom)
	# --- footer: a hairline, then the actions; wraps onto two lines on a narrow screen instead of overflowing
	var foot := VBoxContainer.new()
	foot.add_theme_constant_override("separation", 0)
	foot.add_child(_gap(14.0))
	var line := ColorRect.new()
	line.color = UITheme.HAIRLINE
	line.custom_minimum_size = Vector2(0, 1)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	foot.add_child(line)
	foot.add_child(_gap(14.0))
	var actions := UITheme.button_row(28)
	var restore := UITheme.text_button("ui.restore")
	restore.pressed.connect(func() -> void:
		Premium.restore_purchases()
		SceneManager.toast(tr("ui.restored")))
	actions.add_child(restore)
	var privacy := UITheme.text_button("ui.privacy", UITheme.MUTED)
	privacy.pressed.connect(func() -> void: OS.shell_open(PRIVACY_URL))
	actions.add_child(privacy)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(func() -> void: closed.emit())
	actions.add_child(close)
	foot.add_child(actions)
	_footer = foot
	v.add_child(_footer)
	# the body takes what the screen leaves after the header and the footer
	_content.minimum_size_changed.connect(_queue_fit)
	_footer.minimum_size_changed.connect(_queue_fit)
	_header.minimum_size_changed.connect(_queue_fit)
	_scroll.get_v_scroll_bar().value_changed.connect(func(_v: float) -> void: _update_fades())
	_scroll.get_v_scroll_bar().changed.connect(_update_fades)
	resized.connect(_queue_fit)
	_refresh()
	_queue_fit()


func _draw() -> void:
	# a second, fainter hairline inside the frame (a double rule, like a plate)
	var inset := 6.0
	UITheme.inner_frame().draw(get_canvas_item(), Rect2(Vector2.ONE * inset, size - Vector2.ONE * inset * 2.0))


func _gap(h: float) -> Control:
	var g := Control.new()
	g.custom_minimum_size = Vector2(0, h)
	g.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return g


func _fade(top: bool) -> TextureRect:
	var t := TextureRect.new()
	var g := Gradient.new()
	var pc := Color(UITheme.PANEL_DARK, 0.96)
	g.colors = PackedColorArray([pc, Color(pc, 0.0)] if top else [Color(pc, 0.0), pc])
	g.offsets = PackedFloat32Array([0.0, 1.0])
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill_from = Vector2(0, 0)
	gt.fill_to = Vector2(0, 1)
	gt.width = 4
	gt.height = 64
	t.texture = gt
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_SCALE
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	t.set_anchors_preset(Control.PRESET_TOP_WIDE if top else Control.PRESET_BOTTOM_WIDE)
	var h := FADE_H * UIOrnament.scale_k()
	if top:
		t.offset_bottom = h
	else:
		t.offset_top = -h
	t.visible = false
	return t


## How many columns the panel's width allows.
static func column_count(panel_w: float) -> int:
	var inner := panel_w - 48.0 # panel_box content margins
	return 2 if inner >= 2.0 * MIN_COL_W * UITheme.wscale() + COL_GAP else 1


func _columns() -> Control:
	var sections: Array[Control] = [_section_language(), _section_sound(), _section_display(), _section_other()]
	if column_count(custom_minimum_size.x) == 2:
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", int(COL_GAP))
		h.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var left := VBoxContainer.new()
		left.add_theme_constant_override("separation", 0)
		left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var right := VBoxContainer.new()
		right.add_theme_constant_override("separation", 0)
		right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		left.add_child(sections[0])
		left.add_child(sections[1])
		right.add_child(sections[2])
		right.add_child(sections[3])
		h.add_child(left)
		h.add_child(right)
		return h
	var one := VBoxContainer.new()
	one.add_theme_constant_override("separation", 0)
	one.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for s in sections:
		one.add_child(s)
	return one


# ====================================================================== sections and rows
## A section: a small-caps header with a rule running to the right, then its rows with hairlines between them.
func _section(title_key: String, rows: Array[Control], first_gap: float = 6.0) -> Control:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	v.add_child(_gap(first_gap))
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 16)
	var l := UITheme.label(title_key, HEADER_SIZE, UITheme.BRASS)
	l.add_theme_font_override("font", UITheme.caps_font(true, 2))
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(l)
	var rule := UIOrnament.header_rule()
	rule.size_flags_vertical = Control.SIZE_FILL
	head.add_child(rule)
	v.add_child(head)
	v.add_child(_gap(4.0))
	for i in rows.size():
		v.add_child(rows[i])
		if i < rows.size() - 1:
			var hl := ColorRect.new()
			hl.color = UITheme.HAIRLINE
			hl.custom_minimum_size = Vector2(0, 1)
			hl.mouse_filter = Control.MOUSE_FILTER_IGNORE
			v.add_child(hl)
	v.add_child(_gap(18.0))
	return v


## A row: the label (and an optional muted description) on the left, the control on the right, one touch
## target tall.
func _row(label_key: String, control: Control, desc_key: String = "") -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 24)
	h.custom_minimum_size = Vector2(0, UITheme.target(78))
	var text := VBoxContainer.new()
	text.add_theme_constant_override("separation", 0)
	text.alignment = BoxContainer.ALIGNMENT_CENTER
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_FILL
	text.add_child(UITheme.label(label_key, LABEL_SIZE))
	if desc_key != "":
		text.add_child(UITheme.label(desc_key, DESC_SIZE, UITheme.MUTED))
	h.add_child(text)
	control.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(control)
	return h


func _section_language() -> Control:
	_lang_seg = UISegmented.new()
	_lang_seg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for code in Loc.SUPPORTED: # fixed order EN, RU, UZ; names are shown natively
		_lang_buttons[code] = _lang_seg.add_option(Loc.NATIVE_NAMES[code], code, true, false)
	_lang_seg.chosen.connect(func(code: Variant) -> void:
		Loc.choose(str(code))
		_refresh())
	var holder := MarginContainer.new() # the control fills the row width under its header
	holder.custom_minimum_size = Vector2(0, UITheme.target(78))
	holder.add_child(_lang_seg)
	return _section("ui.language", [holder], 0.0)


func _section_sound() -> Control:
	return _section("ui.sec_sound", [
		_row("ui.music", _slider("music_volume")),
		_row("ui.sfx", _slider("sfx_volume")),
		_row("ui.ambience", _slider("ambience_volume")),
	])


func _section_display() -> Control:
	# text size: each "A" is drawn at the size it gives on this screen
	_scale_seg = UISegmented.new()
	for sc in Settings.TEXT_SCALES:
		var b := _scale_seg.add_option("A", sc, false, false, roundf(84.0 * UITheme.wscale()))
		b.add_theme_font_size_override("font_size", UITheme.size(30, sc))
		_scale_buttons.append(b)
	_scale_seg.chosen.connect(func(sc: Variant) -> void:
		Settings.set_value("text_scale", float(sc))) # → changed → the panel rebuilds at the new size
	return _section("ui.sec_display", [
		_row("ui.text_size", _scale_seg),
		_row("ui.brightness", _slider("brightness", 0.7, 1.6)),
		_row("ui.reduce_motion", _toggle("reduce_motion")),
	], 0.0)


func _section_other() -> Control:
	return _section("ui.sec_other", [
		_row("ui.haptics", _toggle("haptics")),
		_row("ui.safe_graphics", _toggle("safe_graphics"), "ui.safe_graphics_desc"),
	])


## A thin slider with a percentage readout; the row height is the touch target.
func _slider(setting: String, min_v: float = 0.0, max_v: float = 1.0) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 16)
	var s := HSlider.new()
	s.min_value = min_v
	s.max_value = max_v
	s.step = 0.05
	s.value = float(Settings.get_value(setting))
	s.custom_minimum_size = Vector2(roundf(300.0 * UITheme.wscale()), UITheme.target(64, 8.0))
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.focus_mode = Control.FOCUS_NONE
	var readout := UITheme.label("", STATE_SIZE, UITheme.MUTED)
	readout.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	readout.autowrap_mode = TextServer.AUTOWRAP_OFF
	readout.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	readout.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	readout.add_theme_font_override("font", UITheme.caps_font(false, 0))
	readout.custom_minimum_size = Vector2(UITheme.caps_font(false, 0).get_string_size("160%", HORIZONTAL_ALIGNMENT_LEFT, -1, UITheme.size(STATE_SIZE)).x + 6.0, 0)
	var show := func(val: float) -> void: readout.text = "%d%%" % int(round(val * 100.0))
	show.call(s.value)
	s.value_changed.connect(func(val: float) -> void:
		Settings.set_value(setting, val)
		show.call(val))
	h.add_child(s)
	h.add_child(readout)
	return h


## A switch with its state in words beside it (colour is never the only cue).
func _toggle(setting: String) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	var state := UITheme.label("", STATE_SIZE, UITheme.MUTED)
	state.autowrap_mode = TextServer.AUTOWRAP_OFF
	state.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	state.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	state.add_theme_font_override("font", UITheme.caps_font(false, 1))
	# wide enough for the longer of On/Off in the current language, so the switch does not shift
	var f := UITheme.caps_font(false, 1)
	var fs := UITheme.size(STATE_SIZE)
	state.custom_minimum_size = Vector2(maxf(f.get_string_size(tr("ui.on"), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x,
		f.get_string_size(tr("ui.off"), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x) + 8.0, 0)
	var sw := UISwitch.new()
	var on := bool(Settings.get_value(setting))
	sw.set_on(on)
	state.text = "ui.on" if on else "ui.off"
	sw.toggled.connect(func(v: bool) -> void:
		Settings.set_value(setting, v)
		state.text = "ui.on" if v else "ui.off")
	h.add_child(state)
	h.add_child(sw)
	return h


# ====================================================================== fit and state
func _queue_fit() -> void:
	if _fit_queued:
		return
	_fit_queued = true
	_fit_body.call_deferred()


## The body is as tall as its content until the panel would exceed the usable screen height; then it scrolls.
func _fit_body() -> void:
	_fit_queued = false
	if not is_inside_tree() or _scroll_host == null or not is_instance_valid(_scroll_host):
		return
	var max_h := UITheme.usable_rect().size.y
	var others := get_combined_minimum_size().y - _scroll_host.custom_minimum_size.y
	var want := clampf(_content.get_combined_minimum_size().y, 0.0, maxf(0.0, max_h - others))
	if absf(_scroll_host.custom_minimum_size.y - want) > 0.5:
		_scroll_host.custom_minimum_size.y = want
	_update_fades()
	_update_fades.call_deferred() # once more after the scroll container has laid its content out


## Soft fades at the top and bottom of the body while there is content scrolled out of view on that side.
func _update_fades() -> void:
	if _scroll == null or not is_instance_valid(_scroll) or _fade_top == null or not is_instance_valid(_fade_top):
		return
	var hidden := _content.get_combined_minimum_size().y - _scroll_host.custom_minimum_size.y # px out of view
	var at := float(_scroll.scroll_vertical)
	_fade_top.visible = hidden > 1.0 and at > 1.0
	_fade_bottom.visible = hidden > 1.0 and at < hidden - 1.0


func _refresh() -> void:
	_lang_seg.select(Loc.current())
	var sc := float(Settings.get_value("text_scale"))
	for s in Settings.TEXT_SCALES:
		if is_equal_approx(s, sc):
			_scale_seg.select(s)
