extends CanvasLayer
## In-game HUD for room chapters: inventory, item actions, hints, documents (with UV page), inspect view,
## captions/messages, pause, intro, finale choice and chapter-complete screen.
## Sizing follows UITheme (screen-based text scale × the player's text size, touch targets in mm, safe area);
## _layout() places everything and runs again when the window or the text size changes.

var room: Node3D
var logic: RoomLogic
var icons: ItemIcons

var _root: Control
var _top_plate: PanelContainer # view title
var _top_caption: Label
var _cap_plate: PanelContainer # caption / subtitle line under the title
var _caption_line: Label
var _msg_plate: PanelContainer # feedback message above the inventory
var _message: Label
var _prompt_plate: PanelContainer # "Use X on…" above the inventory
var _prompt: Label
var _back_btn: IconButton
var _hint_btn: IconButton
var _pause_btn: IconButton
var _inv_panel: PanelContainer
var _inv_box: HBoxContainer
var _inv_scroll: ScrollContainer
var _meter: PanelContainer
var _meter_bars: Array[ColorRect] = []
var _inv_max_w := 1180.0 # wider inventories scroll sideways (set by _layout from the screen width)
var _act_inspect: IconButton
var _act_combine: IconButton
var _combine_mode := false
var _overlay: Control
var _msg_tween: Tween
var _cap_tween: Tween
var _busy := false
var _back_wanted := false # the current view has somewhere to go back to (shown only while input is not locked)
var _tips_shown: Dictionary = {}
var _last_progress_ms := 0
var _safe_seen := Vector4.ZERO
var _safe_poll := 0.0

const PAD := UITheme.HUD_PAD # gap between HUD controls and the safe-area edge
const INV_SEP := 10


func bind(r: Node3D) -> void:
	room = r
	logic = r.get("logic")
	layer = 10
	icons = ItemIcons.new()
	icons.logic = logic
	add_child(icons)
	icons.icon_ready.connect(func(_id: String, _t: Texture2D) -> void: _refresh_inventory())
	_build()
	GameState.events.connect(_on_events)
	Settings.changed.connect(_on_setting_changed)
	Loc.language_changed.connect(_on_language_changed)
	get_viewport().size_changed.connect(_layout)
	SaveSystem.saved.connect(_on_saved)
	_refresh_inventory()
	_last_progress_ms = Time.get_ticks_msec()


func _on_setting_changed(key: String) -> void:
	if key != "text_scale":
		return
	_root.theme = UITheme.build()
	UITheme.rescale(_root)
	_layout()
	_refresh_inventory()


func _on_language_changed(_code: String) -> void:
	for p in [_top_plate, _msg_plate, _prompt_plate]:
		_fit_plate(p)
	_stack_top()


# ====================================================================== layout
func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = UITheme.build()
	add_child(_root)

	_pause_btn = IconButton.make("pause", 92)
	_root.add_child(_pause_btn)
	_pause_btn.pressed.connect(show_pause)
	_hint_btn = IconButton.make("hint", 92)
	_root.add_child(_hint_btn)
	_hint_btn.pressed.connect(show_hint)

	_top_plate = _plate(30, UITheme.BRASS_HI, false, UITheme.display_font(true))
	_top_caption = _top_plate.get_meta("label")
	_cap_plate = _plate(26, UITheme.CREAM, false) # subtitles are reading text: body size
	_caption_line = _cap_plate.get_meta("label")
	_cap_plate.modulate.a = 0.0
	_msg_plate = _plate(28, UITheme.CREAM, true)
	_message = _msg_plate.get_meta("label")
	_msg_plate.modulate.a = 0.0
	_prompt_plate = _plate(26, UITheme.BRASS_HI, true)
	_prompt = _prompt_plate.get_meta("label")

	_back_btn = IconButton.make("back", int(UITheme.HUD_BACK_PX))
	_root.add_child(_back_btn)
	_back_btn.pressed.connect(func() -> void: room.call("go_back"))

	_inv_panel = PanelContainer.new()
	var sb := UITheme.panel_box(0.82, 18)
	sb.set_content_margin_all(12)
	_inv_panel.add_theme_stylebox_override("panel", sb)
	_inv_panel.anchor_left = 0.5
	_inv_panel.anchor_right = 0.5
	_inv_panel.anchor_top = 1.0
	_inv_panel.anchor_bottom = 1.0
	_inv_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_inv_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_root.add_child(_inv_panel)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	_inv_panel.add_child(row)
	_inv_scroll = ScrollContainer.new()
	_inv_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_inv_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	row.add_child(_inv_scroll)
	_inv_box = HBoxContainer.new()
	_inv_box.add_theme_constant_override("separation", INV_SEP)
	_inv_scroll.add_child(_inv_box)
	_act_inspect = IconButton.make("inspect", 104)
	_act_inspect.pressed.connect(func() -> void: show_inspect(logic.selected))
	row.add_child(_act_inspect)
	_act_combine = IconButton.make("combine", 104)
	_act_combine.pressed.connect(_toggle_combine)
	row.add_child(_act_combine)
	_layout()


## A caption line on a dark plate: readable over any 3D frame (≥ 4.5:1 even over white), hugging its text.
func _plate(sz: int, color: Color, from_bottom: bool, font: Font = null) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UITheme.caption_plate())
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.anchor_left = 0.5
	p.anchor_right = 0.5
	p.anchor_top = 1.0 if from_bottom else 0.0
	p.anchor_bottom = p.anchor_top
	p.grow_horizontal = Control.GROW_DIRECTION_BOTH
	p.grow_vertical = Control.GROW_DIRECTION_BEGIN if from_bottom else Control.GROW_DIRECTION_END
	p.visible = false
	var l := UITheme.label("", sz, color)
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(l)
	p.set_meta("label", l)
	_root.add_child(p)
	return p


## Fits a plate to its (translated) text: one line when it fits `max_w`, otherwise wrapped at `max_w`.
func _fit_plate(p: PanelContainer) -> void:
	var l: Label = p.get_meta("label")
	var text := tr(l.text) if l.auto_translate_mode != Node.AUTO_TRANSLATE_MODE_DISABLED else l.text
	var max_w: float = p.get_meta("max_w", 1200.0)
	var inner := max_w - p.get_theme_stylebox("panel").get_minimum_size().x
	var w := l.get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, l.get_theme_font_size("font_size")).x + 4.0
	var font := l.get_theme_font("font")
	var fs := l.get_theme_font_size("font_size")
	var text_h := font.get_height(fs)
	if w <= inner:
		l.autowrap_mode = TextServer.AUTOWRAP_OFF
		l.custom_minimum_size.x = 0.0
	else:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = inner
		text_h = font.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, inner, fs).y
	p.set_meta("h", text_h + p.get_theme_stylebox("panel").get_minimum_size().y + 6.0)
	var y: float = p.get_meta("y", 0.0)
	# zero-width offsets at the anchor: the plate takes its minimum size and grows around the anchor point
	p.offset_left = 0.0
	p.offset_right = 0.0
	p.offset_top = y
	p.offset_bottom = y
	p.visible = text.strip_edges() != "" and not (p == _prompt_plate and _busy)


func _pin(c: Control, preset: int, offset: Vector2) -> void:
	c.set_anchors_preset(preset)
	c.offset_left = offset.x
	c.offset_top = offset.y
	c.offset_right = offset.x + c.custom_minimum_size.x
	c.offset_bottom = offset.y + c.custom_minimum_size.y


## Places every HUD element inside the safe area for the current screen and text size.
func _layout() -> void:
	if _root == null:
		return
	var safe := UITheme.safe_margins()
	_safe_seen = safe
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var side := maxf(safe.x, safe.z) # keep centred elements symmetric
	var cb := _pause_btn.custom_minimum_size.x
	_pin(_pause_btn, Control.PRESET_TOP_LEFT, Vector2(safe.x + PAD, safe.y + PAD))
	_pin(_hint_btn, Control.PRESET_TOP_RIGHT, Vector2(-(safe.z + PAD + cb), safe.y + PAD))
	var bd := _back_btn.custom_minimum_size.x
	_pin(_back_btn, Control.PRESET_BOTTOM_LEFT, Vector2(safe.x + PAD, -(safe.w + PAD + bd)))
	# top: view title between the corner buttons, caption line below the button row
	var top_w := canvas.x - 2.0 * (side + PAD + cb + 20.0)
	_top_plate.set_meta("max_w", minf(top_w, 1400.0 * UITheme.wscale()))
	var title_h := UITheme.display_font(true).get_height(UITheme.size(30)) + 14.0
	_top_plate.set_meta("y", safe.y + PAD + maxf(0.0, (cb - title_h) * 0.5))
	var meter_w := _meter.get_combined_minimum_size().x if _meter != null and _meter.visible else 0.0
	_cap_plate.set_meta("max_w", minf(canvas.x - 2.0 * (side + PAD + maxf(cb, meter_w) + 20.0), 1500.0 * UITheme.wscale()))
	# bottom: inventory bar, then the prompt and the message stacked above it
	var slot := UITheme.target(112, UITheme.SLOT_MM)
	var act := _act_inspect.custom_minimum_size.x
	var inv_h := maxf(slot, act) + 24.0
	_inv_panel.offset_bottom = -(safe.w + PAD)
	_inv_panel.offset_top = _inv_panel.offset_bottom - inv_h
	_inv_panel.offset_left = 0.0
	_inv_panel.offset_right = 0.0
	var bottom_w := canvas.x - 2.0 * (side + PAD + bd + 20.0) # clear of the back button on both sides
	_inv_max_w = maxf(slot, bottom_w - 2.0 * (act + 12.0) - 24.0)
	var text_w := UITheme.hud_text_width()
	var prompt_y := _inv_panel.offset_top - 10.0
	_prompt_plate.set_meta("max_w", text_w)
	_prompt_plate.set_meta("y", prompt_y)
	var prompt_h := UITheme.ui_font().get_height(UITheme.size(26)) + 16.0
	_msg_plate.set_meta("max_w", text_w)
	_msg_plate.set_meta("y", prompt_y - prompt_h - 10.0)
	for p in [_top_plate, _msg_plate, _prompt_plate]:
		_fit_plate(p)
	_stack_top()


## Caption line and receiver meter go below the corner buttons and below the view title, however many lines
## the title wrapped to (large text sizes).
func _stack_top() -> void:
	var safe := UITheme.safe_margins()
	var cb := _pause_btn.custom_minimum_size.x
	var y := safe.y + PAD + cb + 10.0
	if _top_plate.visible:
		y = maxf(y, float(_top_plate.get_meta("y", 0.0)) + float(_top_plate.get_meta("h", 0.0)) + 8.0)
	_cap_plate.set_meta("y", y)
	_fit_plate(_cap_plate)
	if _meter != null:
		_meter.offset_right = -(safe.z + PAD)
		_meter.offset_left = _meter.offset_right
		_meter.offset_top = y
		_meter.offset_bottom = _meter.offset_top


## Safe-area insets in viewport units: x=left y=top z=right w=bottom.
func _safe_margins() -> Vector4:
	return UITheme.safe_margins()


# ====================================================================== inventory
func _refresh_inventory() -> void:
	for c in _inv_box.get_children():
		c.queue_free() # (not remove_child: this runs inside a slot's own pressed signal)
	var slot := UITheme.target(112, UITheme.SLOT_MM)
	if logic.inventory.is_empty():
		var l := UITheme.label("ui.inventory_empty", 22, UITheme.MUTED)
		l.custom_minimum_size = Vector2(round(360 * UITheme.wscale()), slot)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_inv_box.add_child(l)
	for id in logic.inventory:
		_inv_box.add_child(_slot(id, slot))
	var n := maxi(1, logic.inventory.size())
	_inv_scroll.custom_minimum_size = Vector2(
		minf(n * (slot + INV_SEP) - INV_SEP, _inv_max_w) if not logic.inventory.is_empty() else round(360 * UITheme.wscale()), slot)
	var has_sel := logic.selected != ""
	_act_inspect.visible = has_sel
	_act_combine.visible = has_sel and logic.inventory.size() > 1 and logic.selected != "uv_lamp"
	_act_combine.active = _combine_mode
	_update_prompt()


func _slot(id: String, slot: float) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(slot, slot)
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = tr(ItemDB.name_key(id))
	var sel := id == logic.selected
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.1, 0.09, 0.08, 0.9) if not sel else Color(0.24, 0.19, 0.11, 0.95)
	sb.border_color = UITheme.BRASS_HI if sel else Color(UITheme.BRASS, 0.35)
	sb.set_border_width_all(3 if sel else 1)
	sb.set_corner_radius_all(12)
	for st in ["normal", "hover", "pressed"]:
		b.add_theme_stylebox_override(st, sb)
	var tex := icons.get_icon(id)
	if tex:
		var tr_ := TextureRect.new()
		tr_.texture = tex
		tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr_.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr_.set_anchors_preset(Control.PRESET_FULL_RECT)
		tr_.offset_left = 6
		tr_.offset_top = 6
		tr_.offset_right = -6
		tr_.offset_bottom = -6
		tr_.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(tr_)
	else:
		b.text = tr(ItemDB.name_key(id))
		b.clip_text = true
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.add_theme_font_size_override("font_size", UITheme.size(18))
	b.pressed.connect(func() -> void: _on_slot(id))
	return b


func _on_slot(id: String) -> void:
	AudioManager.ui("ui_tap")
	if _combine_mode and logic.selected != "" and id != logic.selected:
		_combine_mode = false
		logic.combine(logic.selected, id)
		_refresh_inventory()
		return
	_combine_mode = false
	if logic.selected == id:
		show_inspect(id)
	else:
		logic.select_item(id)
		_tip_once("use", "tut.use")
		if logic.has_item("uv_lamp_empty") and logic.has_item("battery_cell"):
			_tip_once("combine", "tut.combine")
	_refresh_inventory()


func _toggle_combine() -> void:
	_combine_mode = not _combine_mode
	_refresh_inventory()


func _update_prompt() -> void:
	if logic.selected == "":
		_prompt.text = ""
	elif _combine_mode:
		_prompt.text = tr("ui.combine_prompt") % tr(ItemDB.name_key(logic.selected))
	elif logic.selected == "uv_lamp":
		_prompt.text = tr("ui.uv_drag")
	else:
		_prompt.text = tr("ui.use_prompt") % tr(ItemDB.name_key(logic.selected))
	_fit_plate(_prompt_plate)


# ====================================================================== feedback
func message(text: String, seconds: float = 2.8) -> void:
	_message.text = text
	_fit_plate(_msg_plate)
	if _msg_tween and _msg_tween.is_valid():
		_msg_tween.kill()
	_msg_tween = create_tween()
	_msg_tween.tween_property(_msg_plate, "modulate:a", 1.0, 0.18)
	_msg_tween.tween_interval(seconds)
	_msg_tween.tween_property(_msg_plate, "modulate:a", 0.0, 0.5)


func caption(text: String, seconds: float = 3.5) -> void:
	_caption_line.text = text
	_fit_plate(_cap_plate)
	if _cap_tween and _cap_tween.is_valid():
		_cap_tween.kill()
	_cap_tween = create_tween()
	_cap_tween.tween_property(_cap_plate, "modulate:a", 1.0, 0.25)
	_cap_tween.tween_interval(seconds)
	_cap_tween.tween_property(_cap_plate, "modulate:a", 0.0, 0.6)


func set_view(id: String, is_root: bool, caption_key: String) -> void:
	var main := str(room.call("main_root")) if room.has_method("main_root") else ""
	_back_wanted = not is_root or id == "darkroom" or (main != "" and id != main)
	_back_btn.visible = _back_wanted and not _busy # cinematics (e.g. the intro's shutter shot) lock input
	set_caption(caption_key)


func set_caption(caption_key: String) -> void:
	# the key itself: the label auto-translates, so a language switch in the pause menu updates it too
	_top_caption.text = caption_key
	_fit_plate(_top_plate)
	_stack_top()


func set_busy(b: bool) -> void:
	_busy = b
	_inv_panel.visible = not b
	_hint_btn.visible = not b
	_pause_btn.visible = not b
	_back_btn.visible = not b and _back_wanted
	_prompt_plate.visible = not b and _prompt.text != ""
	(room.get("touch") as TouchInput).enabled = not b


func _on_saved() -> void:
	pass # autosave is frequent; feedback is shown on pause/quit instead to avoid noise


func _on_events(ev: Array[String]) -> void:
	for e in ev:
		if e.begins_with("item_added") or e.begins_with("item_removed") or e.begins_with("selected") or e.begins_with("combined"):
			_refresh_inventory()
		if e.begins_with("solved:") or e.begins_with("item_added"):
			_last_progress_ms = Time.get_ticks_msec()
		if e == "item_added:notebook":
			_tip_once("inventory", "tut.inventory")
		if e == "uv_revealed:notebook_page" and _overlay != null:
			pass


func _process(delta: float) -> void:
	# a 180° turn (sensor_landscape) moves the camera cutout to the other side without resizing the window
	_safe_poll += delta
	if _safe_poll >= 0.5:
		_safe_poll = 0.0
		var safe := UITheme.safe_margins()
		if safe != _safe_seen:
			_safe_seen = safe
			_layout()
	# gentle nudge toward hints after 4 minutes without progress (never automatic answers)
	if not _busy and Time.get_ticks_msec() - _last_progress_ms > 240000:
		_last_progress_ms = Time.get_ticks_msec()
		_hint_btn.badge = "!"
		_tip_once("hint", "tut.hint")


func _tip_once(id: String, key: String) -> void:
	if _tips_shown.has(id):
		return
	_tips_shown[id] = true
	caption(tr(key), 4.5)


# ====================================================================== overlays (shared)
func _open_overlay(dim: float = 0.72) -> Control:
	_close_overlay()
	var o := ColorRect.new()
	o.color = Color(0, 0, 0, dim)
	o.set_anchors_preset(Control.PRESET_FULL_RECT)
	o.mouse_filter = Control.MOUSE_FILTER_STOP
	o.theme = _root.theme
	_root.add_child(o)
	_overlay = o
	(room.get("touch") as TouchInput).enabled = false
	AudioManager.ui("ui_open")
	return o


## Back button: closes the open overlay (pause, inspect, notebook, hint...). The finale choice and the
## chapter-complete screen need an explicit answer, and cinematics/intro swallow it. -> true if consumed.
func handle_back() -> bool:
	if _overlay != null:
		if not bool(_overlay.get_meta("locked", false)):
			_close_overlay()
		return true
	return _busy


func _close_overlay() -> void:
	if _overlay != null:
		_overlay.queue_free()
		_overlay = null
		if not _busy:
			(room.get("touch") as TouchInput).enabled = true
		get_tree().paused = false


## Height of the bottom bar that holds the close / page buttons of documents.
func _bar_height() -> float:
	return UITheme.target(96) + 24.0


## A centred row at the bottom of an overlay, inside the safe area.
func _bottom_bar(o: Control) -> HBoxContainer:
	var safe := UITheme.safe_margins()
	var bottom := CenterContainer.new()
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_top = -(safe.w + _bar_height())
	bottom.offset_bottom = -safe.w
	bottom.offset_left = safe.x
	bottom.offset_right = -safe.z
	o.add_child(bottom)
	var nav := HBoxContainer.new()
	nav.alignment = BoxContainer.ALIGNMENT_CENTER
	nav.add_theme_constant_override("separation", 40)
	bottom.add_child(nav)
	return nav


## The screen area above the bottom bar, inside the safe area: a CenterContainer and its size.
func _above_bar(o: Control) -> CenterContainer:
	var safe := UITheme.safe_margins()
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.offset_left = safe.x + UITheme.MARGIN
	c.offset_right = -(safe.z + UITheme.MARGIN)
	c.offset_top = safe.y + UITheme.MARGIN
	c.offset_bottom = -(safe.w + _bar_height())
	o.add_child(c)
	return c


func _above_bar_size() -> Vector2:
	return UITheme.usable_rect().size - Vector2(0.0, _bar_height() - UITheme.MARGIN)


# ====================================================================== hints
func show_hint() -> void:
	_hint_btn.badge = ""
	var o := _open_overlay(0.55)
	var d := UITheme.dialog(o, 980, "ui.hint", 46)
	var v: VBoxContainer = d["body"]
	var lvl_label := UITheme.label("", 22, UITheme.MUTED)
	lvl_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(lvl_label)
	var text := UITheme.label("", 30)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.custom_minimum_size = Vector2(0, round(UITheme.size(30) * 2.8)) # two lines: the panel does not jump
	v.add_child(text)
	var h: HFlowContainer = d["footer"]
	var more := UITheme.button("ui.hint_more", 340)
	var close := UITheme.button("ui.close", 240)
	h.add_child(more)
	h.add_child(close)
	var show_next := func() -> void:
		var hint := GameState.next_hint()
		if hint.is_empty():
			return
		AudioManager.sfx("hint", -4.0)
		var args: Array = hint.get("args", [])
		text.text = tr(hint["key"]) % args if not args.is_empty() else tr(hint["key"])
		lvl_label.text = tr("ui.hint_level") % int(hint["level"])
		more.disabled = int(hint["level"]) >= 3
	show_next.call()
	more.pressed.connect(show_next)
	close.pressed.connect(_close_overlay)


# ====================================================================== pause
func show_pause() -> void:
	var o := _open_overlay(0.6)
	var d := UITheme.dialog(o, 620, "ui.pause", 50)
	var v: VBoxContainer = d["body"]
	v.add_theme_constant_override("separation", 16)
	(d["footer"] as Control).visible = false
	var ch := Chapters.get_chapter(GameState.chapter_id)
	var sub := UITheme.label((tr("chapter.label") % int(ch.get("number", 1))) + " · " + tr(str(ch.get("title", ""))), 24, UITheme.MUTED)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(sub)
	var resume := UITheme.button("ui.resume", 520)
	resume.pressed.connect(_close_overlay)
	v.add_child(resume)
	var notebook := UITheme.button("ui.notebook", 520)
	notebook.visible = logic.has_item("notebook")
	notebook.pressed.connect(func() -> void: show_document("notebook"))
	v.add_child(notebook)
	var settings := UITheme.button("ui.settings", 520)
	settings.pressed.connect(func() -> void:
		var o2 := _open_overlay(0.6)
		var sp := SettingsPanel.new()
		UITheme.safe_center(o2).add_child(sp)
		sp.closed.connect(show_pause))
	v.add_child(settings)
	var menu := UITheme.button("ui.main_menu", 520)
	menu.pressed.connect(func() -> void:
		if GameState.save_now():
			SceneManager.toast(tr("ui.saved"))
		_close_overlay()
		AudioManager.stop_all_ambience()
		SceneManager.goto("res://src/ui/main_menu.tscn"))
	v.add_child(menu)


# ====================================================================== inspect (3D item viewer)
func show_inspect(id: String) -> void:
	if id == "":
		return
	var o := _open_overlay(0.8)
	var safe := UITheme.safe_margins()
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = safe.x + 60
	h.offset_right = -(safe.z + 60)
	h.offset_top = safe.y + 40
	h.offset_bottom = -(safe.w + 40)
	h.add_theme_constant_override("separation", 40)
	o.add_child(h)
	var u := UITheme.usable_rect(40.0)
	var side := minf(880.0, minf(u.size.y, u.size.x * 0.45))
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.custom_minimum_size = Vector2(side, side)
	svc.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(svc)
	var vp := SubViewport.new()
	vp.own_world_3d = true
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	svc.add_child(vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("7d766a")
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	var we := WorldEnvironment.new()
	we.environment = env
	vp.add_child(we)
	var key := DirectionalLight3D.new()
	key.light_energy = 1.7
	key.light_color = Color("ffe1bd")
	vp.add_child(key)
	key.look_at_from_position(Vector3(1, 1.3, 1.4), Vector3.ZERO, Vector3.UP)
	var rim := DirectionalLight3D.new()
	rim.light_energy = 1.0
	rim.light_color = Color("a9c7ff")
	vp.add_child(rim)
	rim.look_at_from_position(Vector3(-1.4, 0.5, -1.0), Vector3.ZERO, Vector3.UP)
	var pivot := Node3D.new()
	vp.add_child(pivot)
	var cam := Camera3D.new()
	cam.fov = 32.0
	vp.add_child(cam)
	var model := ModelUtil.spawn(ItemDB.model_path(id), pivot, Transform3D.IDENTITY, "none")
	ItemDress.apply(id, model, logic)
	var radius := 0.1
	if model:
		model.rotation.x = deg_to_rad(ItemDB.view_tilt(id))
		var aabb := ItemIcons._aabb(model)
		model.position = -aabb.get_center()
		radius = maxf(0.02, aabb.size.length() * 0.5)
		if logic.item_glows(id):
			var gl := OmniLight3D.new()
			gl.light_color = Color("cff6ff")
			gl.light_energy = 2.0
			gl.omni_range = radius * 4.0
			pivot.add_child(gl)
	var dist := radius / sin(deg_to_rad(cam.fov * 0.5)) * 1.1
	cam.position = Vector3(0, 0, dist)
	cam.near = maxf(0.001, dist * 0.05)
	pivot.rotation = Vector3(deg_to_rad(15), deg_to_rad(-25), 0)
	svc.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventScreenDrag:
			var rel := (ev as InputEventScreenDrag).relative
			pivot.rotate_y(rel.x * 0.01)
			pivot.rotate_object_local(Vector3.RIGHT, rel.y * 0.01)
		elif ev is InputEventMouseButton and (ev as InputEventMouseButton).pressed:
			var mb := ev as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				cam.position.z = maxf(radius * 1.2, cam.position.z * 0.9)
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				cam.position.z = minf(dist * 2.0, cam.position.z * 1.1)
		elif ev is InputEventMagnifyGesture:
			cam.position.z = clampf(cam.position.z / (ev as InputEventMagnifyGesture).factor, radius * 1.2, dist * 2.0))
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.alignment = BoxContainer.ALIGNMENT_CENTER
	info.add_theme_constant_override("separation", 22)
	h.add_child(info)
	var t := UITheme.title(tr(ItemDB.name_key(id)), 52)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	info.add_child(t)
	var d := UITheme.label(logic.item_desc_key(id), 28)
	info.add_child(UITheme.scroll_fit(d, info, u.size.y)) # long descriptions scroll instead of pushing the buttons off
	var row := UITheme.button_row(16)
	row.alignment = FlowContainer.ALIGNMENT_BEGIN
	info.add_child(row)
	var doc := ItemDB.document(id)
	if doc != "":
		var read := UITheme.button("ui.read", 260)
		read.pressed.connect(func() -> void: show_document(doc))
		row.add_child(read)
	if logic.inventory.size() > 1 and id != "uv_lamp":
		var comb := UITheme.button("ui.combine", 300)
		comb.pressed.connect(func() -> void:
			logic.select_item(id)
			_combine_mode = true
			_close_overlay()
			_refresh_inventory())
		row.add_child(comb)
	var close := UITheme.button("ui.close", 240)
	close.pressed.connect(_close_overlay)
	row.add_child(close)


# ====================================================================== documents
func show_document(doc: String) -> void:
	match doc:
		"notebook":
			_show_notebook(0)
		"letter":
			_show_paper([tr("doc.letter")])
		"photo":
			_show_photo()
		"evidence":
			_show_evidence()
		"darkroom_note":
			_show_paper([tr("doc.darkroom_note")])
		"badge", "index_card":
			_show_picture("res://assets/textures/decals/ch2/%s.png" % doc, Vector2(1000, 630) if doc == "badge" else Vector2(1100, 660))
		"personnel_file":
			_show_paper([tr("doc2.file")])
		"tape_1996", "tape_1997", "tape_1998":
			var heard: bool = logic.state.has("clicks_heard") and (logic.state["clicks_heard"] as Array).has(doc)
			_show_paper([tr("doc2." + doc) if heard else tr("item.%s.desc" % doc)])
		"strand_letters":
			_show_paper([tr("doc3.diagnosis")])
		"strand_note":
			_show_paper([tr("doc3.note")])
		"growth_log":
			_show_paper([tr("doc3.growth_log")])


const NB_PAGES := 8


func _show_notebook(page: int) -> void:
	var l7 := logic as Lab7Logic # Leyla's notebook exists in Chapter 1 only
	if l7 == null:
		return
	var o := _open_overlay(0.82)
	var paper := _paper_panel(o)
	var v := paper.get_meta("vbox") as VBoxContainer
	var pg := clampi(page, 0, NB_PAGES - 1)
	var head := UITheme.label(tr("ui.page") % [pg + 1, NB_PAGES], 22, Color("4a3a28"))
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	v.add_child(head)
	var body := _hand_label(tr("doc.notebook.p%d" % (pg + 1)) if pg != 4 else "")
	v.add_child(body)
	if pg == 4:
		# the "blank" page: UV reveals Leyla's cipher
		var cipher := VBoxContainer.new()
		cipher.add_theme_constant_override("separation", 26)
		v.add_child(cipher)
		var ink_line := _hand_label(tr("doc.notebook.p5_uv"))
		ink_line.add_theme_color_override("font_color", Color("9cffd8"))
		# glowing ink on light paper is ~1.9:1 on its own; a dark halo keeps it legible
		ink_line.add_theme_color_override("font_outline_color", Color("1d0f3a"))
		ink_line.add_theme_constant_override("outline_size", 10)
		cipher.add_child(ink_line)
		var glyphs := HBoxContainer.new()
		glyphs.alignment = BoxContainer.ALIGNMENT_CENTER
		glyphs.add_theme_constant_override("separation", 40)
		for gid: Variant in l7.safe_glyphs(): # this game's cipher (docs/VARIANTS.md)
			var tr_ := TextureRect.new()
			tr_.texture = load("res://assets/ui/glyphs/%s.png" % gid)
			tr_.custom_minimum_size = Vector2.ONE * round(130 * UITheme.wscale())
			tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr_.modulate = Color("9cffd8")
			glyphs.add_child(tr_)
		cipher.add_child(glyphs)
		cipher.visible = l7.state["uv_page"]
		if not l7.state["uv_page"] and l7.has_uv():
			var uvb := IconButton.make("uv", 110)
			var c := CenterContainer.new()
			c.add_child(uvb)
			v.add_child(c)
			uvb.pressed.connect(func() -> void:
				l7.uv_reveal("notebook_page")
				var tint := ColorRect.new()
				tint.color = Color(0.45, 0.25, 1.0, 0.0)
				tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
				tint.set_anchors_preset(Control.PRESET_FULL_RECT)
				paper.add_child(tint)
				var tw := create_tween()
				tw.tween_property(tint, "color:a", 0.22, 0.25)
				cipher.visible = true
				cipher.modulate.a = 0.0
				tw.parallel().tween_property(cipher, "modulate:a", 1.0, 1.2)
				uvb.visible = false)
		elif l7.state["uv_page"]:
			var tint := ColorRect.new()
			tint.color = Color(0.45, 0.25, 1.0, 0.18)
			tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
			tint.set_anchors_preset(Control.PRESET_FULL_RECT)
			paper.add_child(tint)
	var nav := _bottom_bar(o)
	var prev := IconButton.make("prev", 96)
	prev.disabled = pg == 0
	prev.pressed.connect(func() -> void:
		AudioManager.sfx("page_turn", -4.0)
		_show_notebook(pg - 1))
	var next := IconButton.make("next", 96)
	next.disabled = pg == NB_PAGES - 1
	next.pressed.connect(func() -> void:
		AudioManager.sfx("page_turn", -4.0)
		_show_notebook(pg + 1))
	var close := IconButton.make("close", 96)
	close.pressed.connect(_close_overlay)
	nav.add_child(prev)
	nav.add_child(close)
	nav.add_child(next)


## A paper sheet sized to the screen (above the bottom bar, inside the safe area); its text scrolls when it is
## longer than the sheet (large text sizes).
func _paper_panel(o: Control) -> Control:
	var center := _above_bar(o)
	var avail := _above_bar_size()
	var ph := minf(avail.y, 980.0)
	var pw := minf(avail.x, maxf(1080.0, minf(1080.0 * UITheme.wscale(), ph * 1.45)))
	var k := pw / 1080.0
	var paper := PanelContainer.new()
	var sb := StyleBoxTexture.new()
	sb.texture = load("res://assets/textures/decals/notebook_page.jpg")
	sb.content_margin_left = round(110 * k)
	sb.content_margin_right = round(70 * k)
	sb.content_margin_top = round(56 * k)
	sb.content_margin_bottom = round(48 * k)
	paper.add_theme_stylebox_override("panel", sb)
	paper.custom_minimum_size = Vector2(pw, ph)
	center.add_child(paper)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	paper.add_child(scroll)
	# the theme's brass scroll bar disappears on paper: ink-brown instead
	var vb := scroll.get_v_scroll_bar()
	var grab := StyleBoxFlat.new()
	grab.bg_color = Color("4a3a28", 0.85)
	grab.set_corner_radius_all(6)
	grab.content_margin_left = 10
	var track := grab.duplicate() as StyleBoxFlat
	track.bg_color = Color("4a3a28", 0.15)
	vb.add_theme_stylebox_override("scroll", track)
	for st in ["grabber", "grabber_highlight", "grabber_pressed"]:
		vb.add_theme_stylebox_override(st, grab)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 18)
	scroll.add_child(v)
	paper.set_meta("vbox", v)
	return paper


func _hand_label(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", UITheme.hand_font())
	l.set_meta("ui_font_size", 44)
	l.add_theme_font_size_override("font_size", UITheme.size(44))
	l.add_theme_color_override("font_color", Color("2b2118"))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


func _show_paper(pages: Array) -> void:
	var o := _open_overlay(0.82)
	var paper := _paper_panel(o)
	var v := paper.get_meta("vbox") as VBoxContainer
	v.add_child(_hand_label(str(pages[0])))
	_close_button_bottom(o)


func _show_photo() -> void:
	var o := _open_overlay(0.82)
	var paper := _paper_panel(o)
	var v := paper.get_meta("vbox") as VBoxContainer
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 40)
	v.add_child(h)
	var photo := TextureRect.new()
	photo.texture = load("res://assets/textures/decals/photo_3.jpg")
	photo.custom_minimum_size = Vector2(300, 370) * UITheme.wscale()
	photo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	photo.rotation = deg_to_rad(-3)
	photo.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(photo)
	h.add_child(_hand_label(tr("doc.photo")))
	_close_button_bottom(o)


func _show_evidence() -> void:
	var o := _open_overlay(0.82)
	var d := UITheme.dialog(o, 1300, "obj.evidence", 44)
	var v: VBoxContainer = d["body"]
	var grid := UITheme.button_row(14)
	for k in 8:
		var p := TextureRect.new()
		p.texture = load("res://assets/textures/decals/photo_%d.jpg" % k)
		p.custom_minimum_size = Vector2(130, 160) * UITheme.wscale()
		p.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		p.rotation = deg_to_rad(randf_range(-4, 4))
		grid.add_child(p)
	v.add_child(grid)
	var t := UITheme.label("doc.evidence", 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(_close_overlay)
	(d["footer"] as Control).add_child(close)


## A document that is a picture (badge, index card): as large as the screen allows above the close button
## (up to 1.6x its design size), so its printed text is readable on a phone.
func _show_picture(path: String, design: Vector2) -> void:
	var o := _open_overlay(0.85)
	var c := _above_bar(o)
	var avail := _above_bar_size()
	var k := minf(1.6, minf(avail.x / design.x, avail.y / design.y))
	var t := TextureRect.new()
	var lp := DecalLoc.localized_path(path)
	t.texture = load(lp) if ResourceLoader.exists(lp) else null
	t.custom_minimum_size = (design * k).floor()
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	c.add_child(t)
	_close_button_bottom(o)


# ====================================================================== receiver meter (Chapter 2)
## Signal strength of Leyla's pocket receiver for the current view: 0..5 bars, -1 hides the meter.
func set_meter(level: int) -> void:
	if _meter == null:
		_meter = PanelContainer.new()
		var sb := UITheme.panel_box(0.8, 14)
		sb.set_content_margin_all(14)
		_meter.add_theme_stylebox_override("panel", sb)
		_meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_meter.anchor_left = 1.0
		_meter.anchor_right = 1.0
		_meter.grow_horizontal = Control.GROW_DIRECTION_BEGIN
		_meter.grow_vertical = Control.GROW_DIRECTION_END
		_root.add_child(_meter)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 8)
		_meter.add_child(v)
		var t := UITheme.label("item.pocket_receiver.name", 22, UITheme.MUTED)
		t.autowrap_mode = TextServer.AUTOWRAP_OFF
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t)
		var h := HBoxContainer.new()
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		var k := UITheme.size(20) / 20.0
		h.add_theme_constant_override("separation", int(round(8 * k)))
		v.add_child(h)
		for i in 5:
			var bar := ColorRect.new()
			bar.custom_minimum_size = Vector2(round(30 * k), round((14 + 9 * i) * k))
			bar.size_flags_vertical = Control.SIZE_SHRINK_END
			h.add_child(bar)
			_meter_bars.append(bar)
	_meter.visible = level >= 0
	for i in 5:
		_meter_bars[i].color = Color("7dff9a") if i < level else Color(1, 1, 1, 0.12)
	_layout() # the caption line keeps clear of the meter


func _close_button_bottom(o: Control) -> void:
	var nav := _bottom_bar(o)
	var close := IconButton.make("close", 96)
	close.pressed.connect(_close_overlay)
	nav.add_child(close)


# ====================================================================== intro
func play_intro() -> void:
	set_busy(true)
	var safe := UITheme.safe_margins()
	var o := ColorRect.new()
	o.color = Color(0.03, 0.035, 0.04, 1.0)
	o.set_anchors_preset(Control.PRESET_FULL_RECT)
	o.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(o)
	var lbl := UITheme.title("", 44, false)
	lbl.add_theme_color_override("font_color", UITheme.CREAM)
	lbl.set_anchors_preset(Control.PRESET_FULL_RECT)
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.offset_left = safe.x + 220
	lbl.offset_right = -(safe.z + 220)
	lbl.offset_top = safe.y + 40
	lbl.offset_bottom = -(safe.w + 140)
	o.add_child(lbl)
	var tap := UITheme.label("ui.tap_to_continue", 24, UITheme.MUTED)
	tap.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	tap.offset_top = -(safe.w + 120)
	tap.offset_bottom = -(safe.w + 50)
	tap.offset_left = -500 * UITheme.wscale()
	tap.offset_right = 500 * UITheme.wscale()
	tap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tap.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	o.add_child(tap)
	var own_impact := room.has_method("intro_impact") # Chapter 2+: the room plays its own opening beat
	if not own_impact:
		AudioManager.ambience("amb_lab_dark", true, -6.0, 3.0)
	for key in logic.intro_keys():
		lbl.text = tr(key)
		lbl.modulate.a = 0.0
		var tw := create_tween()
		tw.tween_property(lbl, "modulate:a", 1.0, 1.0)
		await _wait_tap_or(o, 6.0)
		var tw2 := create_tween()
		tw2.tween_property(lbl, "modulate:a", 0.0, 0.6)
		await tw2.finished
	# a room whose opening runs longer than the fade (Chapter 3's lift descent) keeps input locked until it ends
	var hold: float = float(room.call("opening_seconds")) if room.has_method("opening_seconds") else 0.0
	room.call("play_opening_camera")
	if not own_impact:
		AudioManager.sfx("door_slam")
		AudioManager.sfx("maglock_release", -4.0, 0.8)
		AudioManager.haptic(120)
	var fade := create_tween()
	fade.tween_property(o, "color:a", 0.0, 1.6)
	await fade.finished
	if hold > 1.6:
		await get_tree().create_timer(hold - 1.6).timeout
	o.queue_free()
	set_busy(false)
	if logic.intro_caption_key() != "":
		caption(tr(logic.intro_caption_key()))
	await get_tree().create_timer(1.2).timeout
	caption(tr("tut.look") + "  " + tr("tut.tap"), 5.0)


func _wait_tap_or(o: Control, seconds: float) -> void:
	var done := {"v": false}
	var cb := func(ev: InputEvent) -> void:
		if (ev is InputEventScreenTouch and (ev as InputEventScreenTouch).pressed) or (ev is InputEventMouseButton and (ev as InputEventMouseButton).pressed):
			done["v"] = true
	o.gui_input.connect(cb)
	var t := 0.0
	while not done["v"] and t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()
	o.gui_input.disconnect(cb)


# ====================================================================== finale
func show_choice() -> void:
	var o := _open_overlay(0.45)
	o.set_meta("locked", true)
	var options: Array = logic.choice_options()
	var d := UITheme.dialog(o, maxf(1000.0, 420.0 * options.size() + 120.0))
	var t := UITheme.label(logic.choice_prompt_key(), 32)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	(d["body"] as Control).add_child(t)
	var h: HFlowContainer = d["footer"]
	h.add_theme_constant_override("h_separation", 24)
	for opt: Array in options:
		var b := UITheme.button(opt[1], 380)
		b.pressed.connect(func() -> void:
			_close_overlay()
			logic.choose_ending(opt[0]))
		h.add_child(b)


func show_chapter_complete() -> void:
	set_busy(true)
	AudioManager.music("stinger_chapter_complete", 1.0)
	var o := _open_overlay(0.0)
	o.set_meta("locked", true)
	var tw := create_tween()
	tw.tween_property(o, "color:a", 0.9, 1.4)
	var d := UITheme.dialog(o, 1200)
	var v: VBoxContainer = d["body"]
	var head := UITheme.label("ui.chapter_complete", 28, UITheme.MUTED)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(head)
	v.add_child(UITheme.title("chapter.%s.title" % GameState.chapter_id, 60))
	for line in logic.epilogue_keys():
		var l := UITheme.label(line, 26)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(l)
	var stats := UITheme.button_row(36)
	var mins := int(GameState.play_time) / 60
	var secs := int(GameState.play_time) % 60
	var pairs: Array = [["ui.time", "%d:%02d" % [mins, secs]],
		["ui.puzzles", "%d / %d" % [logic.solved_count(), logic.puzzle_ids().size()]],
		["ui.hints_used", str(GameState.hints_used)]]
	var col_info: Array = logic.collectibles()
	if int(col_info[1]) > 0:
		pairs.append([col_info[2], "%d / %d" % [int(col_info[0]), int(col_info[1])]])
	for pair: Array in pairs:
		var col := VBoxContainer.new()
		col.custom_minimum_size = Vector2(round(230 * UITheme.wscale()), 0) # labels wrap; without a width they collapse
		var a := UITheme.label(pair[0], 22, UITheme.MUTED)
		a.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var b := UITheme.label(pair[1], 34, UITheme.BRASS_HI)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(a)
		col.add_child(b)
		stats.add_child(col)
	v.add_child(stats)
	var footer: HFlowContainer = d["footer"]
	var next_id := Chapters.next_of(GameState.chapter_id)
	if next_id != "":
		var next := UITheme.label("%s — %s" % [tr("chapter.label") % int(Chapters.get_chapter(next_id)["number"]), tr("chapter.%s.title" % next_id)], 30, UITheme.BRASS_HI)
		next.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		next.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(next)
		if Premium.can_play(next_id):
			var go := UITheme.button("ui.play", 420)
			go.pressed.connect(func() -> void:
				AudioManager.stop_all_ambience()
				if GameState.start_new(next_id):
					SceneManager.goto(Chapters.get_chapter(next_id)["scene"]))
			footer.add_child(go)
		else:
			var soon := UITheme.label("ui.to_be_continued" if not Chapters.get_chapter(next_id).get("released", false) else "ui.unlock_desc", 24, UITheme.MUTED)
			soon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(soon)
	var menu := UITheme.button("ui.main_menu", 420)
	menu.pressed.connect(func() -> void:
		AudioManager.stop_all_ambience()
		SceneManager.goto("res://src/ui/main_menu.tscn"))
	footer.add_child(menu)
