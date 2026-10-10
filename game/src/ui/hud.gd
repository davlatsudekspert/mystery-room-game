extends CanvasLayer
## In-game HUD for room chapters, in the main menu's visual language (docs/UI_UX.md → HUD): centred banners
## (a small-caps serif title between gold flourishes over a thin rule, a subtitle below, on a soft dark band)
## for the view title, captions, messages, prompts and "item found"; the inventory as a column on the left
## beside a thin vertical gold rule; round bezel buttons (Back top left, Hint top right, Pause with a roman II
## bottom right); hints, documents (with UV page), the inspect view, pause, intro, finale choice and the
## chapter-complete screen as dialogs in the same style.
## Sizing follows UITheme (screen-based text scale × the player's text size, touch targets in mm, safe area);
## _layout() places everything and runs again when the window or the text size changes.

var room: Node3D
var logic: RoomLogic
var icons: ItemIcons

var _root: Control
var _top_plate: UIBanner # view title
var _top_caption: Label
var _cap_plate: UIBanner # caption / subtitle line under the title
var _caption_line: Label
var _msg_plate: UIBanner # feedback message, or the found item (icon, name, description), at the bottom
var _message: Label
var _prompt_plate: UIBanner # "Use X on…" at the bottom
var _prompt: Label
var _back_btn: IconButton
var _hint_btn: IconButton
var _pause_btn: IconButton
var _inv_panel: Control # the inventory column: slots, the vertical rule, the item actions beside the selection
var _inv_box: VBoxContainer
var _inv_scroll: ScrollContainer
var _inv_rule: UIOrnament
var _inv_span := Rect2() # where the column may be (set by _layout)
var _actions: HBoxContainer # inspect / combine, beside the selected slot
var _meter: PanelContainer
var _meter_bars: Array[ColorRect] = []
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
var _found_id := "" # the item the message banner announces (its icon may be rendered a moment later)

const PAD := UITheme.HUD_PAD # gap between HUD controls and the safe-area edge
const INV_SEP := 10
const ACTION_GAP := 12.0 # between the inventory rule and the item actions


func bind(r: Node3D) -> void:
	room = r
	logic = r.get("logic")
	layer = 10
	icons = ItemIcons.new()
	icons.logic = logic
	add_child(icons)
	icons.icon_ready.connect(func(id: String, t: Texture2D) -> void:
		_refresh_inventory()
		if id == _found_id and _msg_plate != null:
			_msg_plate.set_icon(t)
			_stack_bottom())
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
	_layout()


# ====================================================================== layout
func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = UITheme.build()
	add_child(_root)

	_back_btn = IconButton.make("back", int(UITheme.HUD_BACK_PX))
	_root.add_child(_back_btn)
	_back_btn.pressed.connect(func() -> void: room.call("go_back"))
	_hint_btn = IconButton.make("hint", int(UITheme.HUD_BTN_PX))
	_root.add_child(_hint_btn)
	_hint_btn.pressed.connect(show_hint)
	_pause_btn = IconButton.make("pause", int(UITheme.HUD_BTN_PX))
	_root.add_child(_pause_btn)
	_pause_btn.pressed.connect(show_pause)

	_top_plate = _plate(UITheme.HUD_TITLE_PX, 26, UITheme.CREAM) # small caps read large: body size keeps long names to two lines
	_top_caption = _top_plate.title_label
	_cap_plate = _plate(28, 26, UITheme.CREAM) # subtitles are reading text: body size
	_caption_line = _cap_plate.subtitle_label
	_cap_plate.modulate.a = 0.0
	_msg_plate = _plate(28, 28, UITheme.CREAM)
	_message = _msg_plate.subtitle_label
	_msg_plate.modulate.a = 0.0
	_prompt_plate = _plate(28, 26, UITheme.BRASS_HI)
	_prompt = _prompt_plate.subtitle_label

	# the inventory column: a scrolling stack of slots, a vertical rule with arrow tips, the actions flyout
	_inv_panel = Control.new()
	_inv_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_inv_panel)
	_inv_scroll = ScrollContainer.new()
	_inv_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_inv_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_inv_panel.add_child(_inv_scroll)
	_inv_box = VBoxContainer.new()
	_inv_box.add_theme_constant_override("separation", INV_SEP)
	_inv_scroll.add_child(_inv_box)
	_inv_scroll.get_v_scroll_bar().value_changed.connect(func(_v: float) -> void: _place_actions())
	_inv_rule = UIOrnament.vrule(UITheme.HUD_RULE_W)
	_inv_panel.add_child(_inv_rule)
	_actions = HBoxContainer.new()
	_actions.add_theme_constant_override("separation", 6)
	_actions.visible = false
	_inv_panel.add_child(_actions)
	_act_inspect = IconButton.make("inspect", 96)
	_act_inspect.pressed.connect(func() -> void: show_inspect(logic.selected))
	_actions.add_child(_act_inspect)
	_act_combine = IconButton.make("combine", 96)
	_act_combine.pressed.connect(_toggle_combine)
	_actions.add_child(_act_combine)
	_layout()


## A banner for one HUD line: the title in display small caps (`title_sz`), the subtitle in the body font.
func _plate(title_sz: int, sub_sz: int, sub_color: Color) -> UIBanner:
	var b := UIBanner.new()
	b.setup(title_sz, sub_sz, sub_color)
	b.visible = false
	_root.add_child(b)
	return b


## Fits a banner to its (translated) texts within its `max_w` and places it: centred on `cx` (the screen's
## centre by default), top edge at `y`, or bottom edge at `y` when `from_bottom`; `row_h` centres it on a
## button row.
func _fit_plate(p: UIBanner) -> void:
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	p.fit(float(p.get_meta("max_w", 1200.0)))
	var cx: float = p.get_meta("cx", canvas.x * 0.5)
	var y: float = p.get_meta("y", 0.0)
	var row_h: float = p.get_meta("row_h", 0.0)
	if bool(p.get_meta("from_bottom", false)):
		y -= p.size.y
	elif row_h > 0.0:
		y += maxf(0.0, (row_h - p.size.y) * 0.5)
	p.position = Vector2(roundf(cx - p.size.x * 0.5), roundf(y))
	p.visible = p.has_text() and not (p == _prompt_plate and _busy)


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
	var bd := _back_btn.custom_minimum_size.x
	var corner := maxf(cb, bd)
	_pin(_back_btn, Control.PRESET_TOP_LEFT, Vector2(safe.x + PAD, safe.y + PAD))
	_pin(_hint_btn, Control.PRESET_TOP_RIGHT, Vector2(-(safe.z + PAD + cb), safe.y + PAD))
	_pin(_pause_btn, Control.PRESET_BOTTOM_RIGHT, Vector2(-(safe.z + PAD + cb), -(safe.w + PAD + cb)))
	# top: the view title between the corner buttons (centred on their row), the caption line below
	var top_w := canvas.x - 2.0 * (side + PAD + corner + 20.0)
	_top_plate.set_meta("max_w", minf(top_w, 1400.0 * UITheme.wscale()))
	_top_plate.set_meta("y", safe.y + PAD)
	_top_plate.set_meta("row_h", corner)
	# left: the inventory column, from under the Back button down to the bottom safe edge
	var col_top := safe.y + PAD + bd + 16.0
	_inv_span = Rect2(safe.x + PAD, col_top, UITheme.hud_column_width(), canvas.y - safe.w - PAD - col_top)
	_inv_panel.position = _inv_span.position
	_inv_panel.size = _inv_span.size
	# bottom centre: the prompt, with the message above it; both clear of the column and the pause button
	var text_w := UITheme.hud_text_width()
	_prompt_plate.set_meta("max_w", text_w)
	_prompt_plate.set_meta("from_bottom", true)
	_msg_plate.set_meta("max_w", text_w)
	_msg_plate.set_meta("from_bottom", true)
	_fit_plate(_top_plate)
	_stack_bottom()
	_stack_top() # after the bottom: the caption keeps clear of the prompt and the message
	_inventory_geometry()


## Caption line and receiver meter go below the corner buttons and below the view title, however many lines
## the title wrapped to (large text sizes).
func _stack_top() -> void:
	var safe := UITheme.safe_margins()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var corner := maxf(_pause_btn.custom_minimum_size.x, _back_btn.custom_minimum_size.x)
	var row_bottom := safe.y + PAD + corner + 10.0
	var y := row_bottom
	if _top_plate.visible:
		y = maxf(y, _top_plate.position.y + _top_plate.size.y + 6.0)
	# the receiver meter (Chapter 2) hangs under the Hint button; the caption goes below it, never beside it
	if _meter != null:
		_meter.offset_right = -(safe.z + PAD)
		_meter.offset_left = _meter.offset_right
		_meter.offset_top = row_bottom
		_meter.offset_bottom = _meter.offset_top
		if _meter.visible:
			y = maxf(y, row_bottom + _meter.get_combined_minimum_size().y + 8.0)
	_cap_plate.set_meta("y", y)
	# sideways the caption keeps clear of the inventory column (and the inspect / combine flyout beside the
	# selected slot) on the left and the Hint button on the right; it is centred in what is left
	var left := _inv_span.position.x + _inv_span.size.x + 20.0
	if _actions.visible:
		left += ACTION_GAP + _actions.get_combined_minimum_size().x
	var right := canvas.x - safe.z - PAD - corner - 20.0
	_cap_plate.set_meta("cx", (left + right) * 0.5)
	_cap_plate.set_meta("max_w", minf(right - left, 1500.0 * UITheme.wscale()))
	# the caption may not run into the banners at the bottom: fewer lines (with an ellipsis) when it would
	var limit := canvas.y - safe.w - PAD - 10.0
	for p: UIBanner in [_prompt_plate, _msg_plate]:
		if p.visible and p.modulate.a > 0.05:
			limit = minf(limit, p.position.y - 10.0)
	_cap_plate.max_sub_lines = 0
	_fit_plate(_cap_plate)
	if _cap_plate.visible and _cap_plate.position.y + _cap_plate.size.y > limit:
		var f := _caption_line.get_theme_font("font")
		var fs := _caption_line.get_theme_font_size("font_size")
		var line_h := f.get_height(fs) + float(_caption_line.get_theme_constant("line_spacing"))
		var room := limit - y - 2.0 * UIBanner.PAD_Y * UIOrnament.scale_k() - 6.0
		_cap_plate.max_sub_lines = maxi(1, int(floor(room / line_h)))
		_fit_plate(_cap_plate)


## The prompt sits at the bottom safe edge; the message above it (or in its place while there is no prompt).
func _stack_bottom() -> void:
	var safe := UITheme.safe_margins()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var bottom := canvas.y - safe.w - PAD
	_prompt_plate.set_meta("y", bottom)
	_fit_plate(_prompt_plate)
	if _prompt_plate.visible:
		bottom = _prompt_plate.position.y - 10.0
	_msg_plate.set_meta("y", bottom)
	_fit_plate(_msg_plate)


## Safe-area insets in viewport units: x=left y=top z=right w=bottom.
func _safe_margins() -> Vector4:
	return UITheme.safe_margins()


# ====================================================================== inventory
func _refresh_inventory() -> void:
	for c in _inv_box.get_children():
		c.queue_free() # (not remove_child: this runs inside a slot's own pressed signal)
	var slot := UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM)
	if logic.inventory.is_empty():
		_inv_box.add_child(_empty_slot(slot))
	for id in logic.inventory:
		_inv_box.add_child(_slot(id, slot))
	_inventory_geometry()
	var has_sel := logic.selected != ""
	_act_inspect.visible = has_sel
	_act_combine.visible = has_sel and logic.inventory.size() > 1 and logic.selected != "uv_lamp"
	_act_combine.active = _combine_mode
	_actions.visible = has_sel
	_place_actions.call_deferred()
	_update_prompt()


## The slots, centred vertically in the column's span; they scroll when there are more than fit. The rule runs
## beside them with its arrow tips just beyond the first and the last slot.
func _inventory_geometry() -> void:
	var slot := UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM)
	var n := maxi(1, logic.inventory.size())
	var content_h := n * slot + (n - 1) * INV_SEP
	var h := minf(content_h, _inv_span.size.y)
	var y0 := roundf((_inv_span.size.y - h) * 0.5)
	_inv_scroll.position = Vector2(0, y0)
	_inv_scroll.custom_minimum_size = Vector2(slot, h)
	_inv_scroll.size = Vector2(slot, h)
	var tip := 16.0 * UIOrnament.scale_k()
	_inv_rule.position = Vector2(slot + UITheme.HUD_COL_GAP, y0 - tip)
	_inv_rule.size = Vector2(UITheme.HUD_RULE_W, h + 2.0 * tip)
	_inv_rule.queue_redraw()


## The inspect / combine buttons sit right of the rule, level with the selected slot (clamped to the column).
func _place_actions() -> void:
	if not is_instance_valid(_actions) or not _actions.visible:
		return
	var idx := logic.inventory.find(logic.selected)
	if idx < 0:
		_actions.visible = false
		return
	var slot := UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM)
	var slot_y := _inv_scroll.position.y + idx * (slot + INV_SEP) - _inv_scroll.scroll_vertical
	var sz := _actions.get_combined_minimum_size()
	_actions.size = sz
	_actions.position = Vector2(_inv_rule.position.x + _inv_rule.size.x + ACTION_GAP,
		clampf(slot_y + (slot - sz.y) * 0.5, 0.0, maxf(0.0, _inv_span.size.y - sz.y)))


func _slot_style(selected: bool, hover: bool = false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.17, 0.135, 0.075, 0.92) if selected else Color(0.04, 0.042, 0.05, 0.8)
	sb.border_color = UITheme.BRASS_HI if selected else Color(UITheme.BRASS, 0.85 if hover else 0.45)
	sb.set_border_width_all(2 if selected else 1)
	sb.set_corner_radius_all(10)
	return sb


## The placeholder shown while the pockets are empty: a faint slot frame where the items will appear.
func _empty_slot(slot: float) -> Control:
	var p := Panel.new()
	p.custom_minimum_size = Vector2(slot, slot)
	var sb := _slot_style(false)
	sb.bg_color.a = 0.45
	sb.border_color.a = 0.25
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.tooltip_text = tr("ui.inventory_empty")
	return p


func _slot(id: String, slot: float) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(slot, slot)
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = tr(ItemDB.name_key(id))
	var sel := id == logic.selected
	b.add_theme_stylebox_override("normal", _slot_style(sel))
	b.add_theme_stylebox_override("hover", _slot_style(sel, true))
	b.add_theme_stylebox_override("pressed", _slot_style(true))
	b.add_theme_stylebox_override("hover_pressed", _slot_style(true))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	var tex := icons.get_icon(id)
	if tex:
		var tr_ := TextureRect.new()
		tr_.texture = tex
		tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr_.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr_.set_anchors_preset(Control.PRESET_FULL_RECT)
		tr_.offset_left = 8
		tr_.offset_top = 8
		tr_.offset_right = -8
		tr_.offset_bottom = -8
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
	_stack_bottom()
	_stack_top() # the caption keeps clear of the prompt


# ====================================================================== feedback
## The item a "Found: X" message (room_base's item_added feedback) is about, or "".
func _found_item(text: String) -> String:
	for id: String in logic.inventory:
		if text == tr("ui.item_added") % tr(ItemDB.name_key(id)):
			return id
	return ""


## A message at the bottom. A found item gets the full banner: its icon, its name in small caps and its
## one-line description.
func message(text: String, seconds: float = 2.8) -> void:
	_found_id = _found_item(text)
	if _found_id != "":
		_msg_plate.set_title(tr(ItemDB.name_key(_found_id)))
		_msg_plate.set_icon(icons.get_icon(_found_id))
		_msg_plate.max_sub_lines = 3 # the full description is in Inspect; the banner stays a banner at Extra large
		_message.text = tr(logic.item_desc_key(_found_id))
		seconds = maxf(seconds, 4.5)
	else:
		_msg_plate.set_title("")
		_msg_plate.set_icon(null)
		_msg_plate.max_sub_lines = 0
		_message.text = text
	_message.modulate.a = 1.0 # (QA scripts blank the label itself to detect the next message as new)
	_stack_bottom()
	_yield_overlap(_cap_plate, _msg_plate)
	if _msg_tween and _msg_tween.is_valid():
		_msg_tween.kill()
	_msg_tween = create_tween()
	_msg_tween.tween_property(_msg_plate, "modulate:a", 1.0, 0.18)
	_msg_tween.tween_interval(seconds)
	_msg_tween.tween_property(_msg_plate, "modulate:a", 0.0, 0.5)


func caption(text: String, seconds: float = 3.5) -> void:
	_caption_line.text = text
	_stack_top()
	_yield_overlap(_msg_plate, _cap_plate)
	if _cap_tween and _cap_tween.is_valid():
		_cap_tween.kill()
	_cap_tween = create_tween()
	_cap_tween.tween_property(_cap_plate, "modulate:a", 1.0, 0.25)
	_cap_tween.tween_interval(seconds)
	_cap_tween.tween_property(_cap_plate, "modulate:a", 0.0, 0.6)


## Large text on a short screen: when the banner that is appearing (`newer`) would overlap one still showing
## (`older`), the older one fades out at once. The newer line is the one the player is waiting for.
func _yield_overlap(older: UIBanner, newer: UIBanner) -> void:
	if not older.visible or older.modulate.a <= 0.05 or not newer.visible:
		return
	if not Rect2(older.position, older.size).intersects(Rect2(newer.position, newer.size)):
		return
	var tw := create_tween()
	tw.tween_property(older, "modulate:a", 0.0, 0.2)
	if older == _cap_plate and _cap_tween and _cap_tween.is_valid():
		_cap_tween.kill()
	elif older == _msg_plate and _msg_tween and _msg_tween.is_valid():
		_msg_tween.kill()


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
	lvl_label.add_theme_font_override("font", UITheme.caps_font(false, 1))
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
	var d := UITheme.dialog(o, 620, "ui.pause", 46)
	var v: VBoxContainer = d["body"]
	v.add_theme_constant_override("separation", 10)
	(d["footer"] as Control).visible = false
	var ch := Chapters.get_chapter(GameState.chapter_id)
	var sub := UITheme.label((tr("chapter.label") % int(ch.get("number", 1))) + " · " + tr(str(ch.get("title", ""))), 22, UITheme.MUTED)
	sub.add_theme_font_override("font", UITheme.caps_font(false, 1))
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
	var side := UITheme.inspect_viewer_side() # smaller when the text is large: the words need the room
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.custom_minimum_size = Vector2(side, side)
	svc.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(svc)
	var vp := SubViewport.new()
	vp.own_world_3d = true
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X if CrashGuard.safe_level() == 0 else Viewport.MSAA_DISABLED
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
	info.add_theme_constant_override("separation", 18)
	h.add_child(info)
	var t := UITheme.title(tr(ItemDB.name_key(id)), 52)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	info.add_child(t)
	info.add_child(UIOrnament.header_rule(14.0)) # a gold rule running out from under the name
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
		var comb := UITheme.button("ui.combine", 320)
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
			_show_paper(tr("doc.letter"), _doc_title(doc))
		"photo":
			_show_photo()
		"evidence":
			_show_evidence()
		"darkroom_note":
			_show_paper(tr("doc.darkroom_note"), _doc_title(doc))
		"badge", "index_card":
			_show_picture("res://assets/textures/decals/ch2/%s.png" % doc, _doc_title(doc))
		"personnel_file":
			_show_paper(tr("doc2.file"), _doc_title(doc))
		"tape_1996", "tape_1997", "tape_1998":
			var heard: bool = logic.state.has("clicks_heard") and (logic.state["clicks_heard"] as Array).has(doc)
			_show_paper(tr("doc2." + doc) if heard else tr("item.%s.desc" % doc), _doc_title(doc))
		"strand_letters":
			_show_paper(tr("doc3.diagnosis"), _doc_title(doc))
		"strand_note":
			_show_paper(tr("doc3.note"), _doc_title(doc))
		"growth_log":
			_show_paper(tr("doc3.growth_log"), _doc_title(doc))
		# inscriptions in the rooms: a second tap on their close-up opens the art full size (exactly as painted)
		"poster":
			_show_picture("res://assets/textures/decals/poster_resonance.jpg", tr("obj.poster"))
		"chalkboard":
			_show_picture("res://assets/textures/decals/chalkboard.jpg", tr("obj.chalkboard"))
		"routing_chart":
			_show_picture("res://assets/textures/decals/ch2/routing_chart.png", tr("obj2.chart"), tr("msg.c2_chart_rule"))


## The (translated) name of the item that carries this document, or "" for a document that is not an item.
func _doc_title(doc: String) -> String:
	for id: String in ItemDB.ITEMS:
		if ItemDB.document(id) == doc:
			return tr(ItemDB.name_key(id))
	return ""


const NB_PAGES := 8


func _show_notebook(page: int) -> void:
	var l7 := logic as Lab7Logic # Leyla's notebook exists in Chapter 1 only
	if l7 == null:
		return
	var o := _open_overlay(0.82)
	var pg := clampi(page, 0, NB_PAGES - 1)
	var r := _reader(o, _doc_title("notebook"), tr("ui.page") % [pg + 1, NB_PAGES])
	var paper: Control = r["paper"]
	var v: VBoxContainer = r["vbox"]
	var body := _ink_label(tr("doc.notebook.p%d" % (pg + 1)) if pg != 4 else "")
	v.add_child(body)
	if pg == 4:
		# the "blank" page: UV reveals Leyla's cipher
		var cipher := VBoxContainer.new()
		cipher.add_theme_constant_override("separation", 26)
		v.add_child(cipher)
		var ink_line := _ink_label(tr("doc.notebook.p5_uv"))
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


# ====================================================================== reader (documents, notes, inscriptions)
const INK := Color("2b2118")
const INK_SOFT := Color("4a3a28")
const READ_PX := 40 # design size of reading text (display serif): about 5.8 mm em on a 6" phone at Normal


## A full-screen reader: a paper plate filling the safe area above the bottom bar, the title in small caps over
## a hairline (with `right`, e.g. the page number, at the right end), then a picture that can be pinched or
## double-tapped to zoom and/or text at reading size that scrolls when it is longer. Every document, note and
## inscription opens here (docs/UI_UX.md → Reader).
## -> {"paper": PanelContainer, "vbox": VBoxContainer (the scrolling text), "image": UIZoomView or null}
func _reader(o: Control, title: String, right: String = "", image: Texture2D = null, text_too: bool = true) -> Dictionary:
	var center := _above_bar(o)
	var avail := _above_bar_size()
	var paper := PanelContainer.new()
	var sb := StyleBoxTexture.new()
	sb.texture = load("res://assets/textures/decals/notebook_page.jpg")
	var k := clampf(avail.x / 1080.0, 1.0, 2.2)
	sb.content_margin_left = round(60 * k)
	sb.content_margin_right = round(48 * k)
	sb.content_margin_top = round(28 * k)
	sb.content_margin_bottom = round(28 * k)
	paper.add_theme_stylebox_override("panel", sb)
	paper.custom_minimum_size = avail
	center.add_child(paper)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	paper.add_child(v)
	if title != "" or right != "":
		var head := HBoxContainer.new()
		head.add_theme_constant_override("separation", 24)
		var t := UITheme.label(title, 24, INK_SOFT)
		t.add_theme_font_override("font", UITheme.caps_font(true, 2))
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		t.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		head.add_child(t)
		if right != "":
			var pr := UITheme.label(right, 22, INK_SOFT)
			pr.add_theme_font_override("font", UITheme.caps_font(false, 1))
			pr.autowrap_mode = TextServer.AUTOWRAP_OFF
			pr.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
			head.add_child(pr)
		v.add_child(head)
		var line := ColorRect.new()
		line.color = Color(INK_SOFT, 0.3)
		line.custom_minimum_size = Vector2(0, 1)
		line.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(line)
	var zoom: UIZoomView = null
	if image != null:
		zoom = UIZoomView.new()
		zoom.texture = image
		zoom.size_flags_vertical = Control.SIZE_EXPAND_FILL
		v.add_child(zoom)
		var hint := UITheme.label("ui.zoom_hint", 20, INK_SOFT)
		hint.add_theme_font_override("font", UITheme.caps_font(false, 1))
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(hint)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.visible = text_too
	v.add_child(scroll)
	# the theme's brass scroll bar disappears on paper: ink-brown instead
	var vb := scroll.get_v_scroll_bar()
	var grab := StyleBoxFlat.new()
	grab.bg_color = Color(INK_SOFT, 0.85)
	grab.set_corner_radius_all(6)
	grab.content_margin_left = 10
	var track := grab.duplicate() as StyleBoxFlat
	track.bg_color = Color(INK_SOFT, 0.15)
	vb.add_theme_stylebox_override("scroll", track)
	for st in ["grabber", "grabber_highlight", "grabber_pressed"]:
		vb.add_theme_stylebox_override(st, grab)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 18)
	scroll.add_child(body)
	return {"paper": paper, "vbox": body, "image": zoom, "scroll": scroll}


## Reading text: the display serif in ink on the paper, at reading size, wrapping (`sz` is the design size).
func _ink_label(text: String, sz: int = READ_PX) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", UITheme.display_font(false))
	l.set_meta("ui_font_size", sz)
	l.add_theme_font_size_override("font_size", UITheme.size(sz))
	l.add_theme_color_override("font_color", INK)
	l.add_theme_constant_override("line_spacing", 8)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


func _show_paper(text: String, title: String = "") -> void:
	var o := _open_overlay(0.82)
	var r := _reader(o, title)
	(r["vbox"] as VBoxContainer).add_child(_ink_label(text))
	_close_button_bottom(o)


func _show_photo() -> void:
	var o := _open_overlay(0.82)
	var r := _reader(o, _doc_title("photo"), "", load("res://assets/textures/decals/photo_3.jpg"))
	(r["vbox"] as VBoxContainer).add_child(_ink_label(tr("doc.photo")))
	_close_button_bottom(o)


## The evidence board: the eight photographs (a tap opens one full size) and the note under them.
func _show_evidence() -> void:
	var o := _open_overlay(0.82)
	var r := _reader(o, tr("obj.evidence"))
	var v: VBoxContainer = r["vbox"]
	var grid := UITheme.button_row(14)
	var ph := roundf(180.0 * UITheme.wscale())
	for k in 8:
		var tex: Texture2D = load("res://assets/textures/decals/photo_%d.jpg" % k)
		var b := Button.new()
		b.flat = true
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(roundf(ph * 0.82), ph)
		for st in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
			b.add_theme_stylebox_override(st, StyleBoxEmpty.new())
		var p := TextureRect.new()
		p.texture = tex
		p.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		p.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		p.set_anchors_preset(Control.PRESET_FULL_RECT)
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(p)
		b.pressed.connect(func() -> void: _show_zoom(tex, tr("obj.evidence"), _show_evidence))
		grid.add_child(b)
	v.add_child(grid)
	v.add_child(_ink_label(tr("doc.evidence")))
	_close_button_bottom(o)


## A picture full size (a document decal in the current language, an inscription), with a line of text under it
## when there is one.
func _show_picture(path: String, title: String = "", caption: String = "") -> void:
	var lp := DecalLoc.localized_path(path)
	var tex: Texture2D = load(lp) if ResourceLoader.exists(lp) else null
	_show_zoom(tex, title, Callable(), caption)


## A zoomable picture in the reader; `back` reopens the view it came from when it closes.
func _show_zoom(tex: Texture2D, title: String, back: Callable = Callable(), caption: String = "") -> void:
	var o := _open_overlay(0.85)
	var r := _reader(o, title, "", tex, caption != "")
	if caption != "":
		(r["vbox"] as VBoxContainer).add_child(_ink_label(caption, 32))
	var nav := _bottom_bar(o)
	var close := IconButton.make("close", 96)
	close.pressed.connect(func() -> void:
		if back.is_valid():
			back.call()
		else:
			_close_overlay())
	nav.add_child(close)


# ====================================================================== receiver meter (Chapter 2)
## Signal strength of Leyla's pocket receiver for the current view: 0..5 bars, -1 hides the meter.
func set_meter(level: int) -> void:
	if _meter == null:
		_meter = PanelContainer.new()
		var sb := UITheme.panel_box(0.9, 6)
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
		t.add_theme_font_override("font", UITheme.caps_font(false, 1))
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
## The chapter's opening cards: each line in the display serif between two gold rules on black, "Tap to
## continue" in small caps at the bottom. (QA reads the card text from the overlay's own Label children.)
func play_intro() -> void:
	set_busy(true)
	var safe := UITheme.safe_margins()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var o := ColorRect.new()
	o.color = Color(0.03, 0.035, 0.04, 1.0)
	o.set_anchors_preset(Control.PRESET_FULL_RECT)
	o.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(o)
	var lbl := UITheme.title("", 44, false)
	lbl.add_theme_color_override("font_color", UITheme.CREAM)
	lbl.set_anchors_preset(Control.PRESET_FULL_RECT)
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.offset_left = safe.x + 160
	lbl.offset_right = -(safe.z + 160)
	lbl.offset_top = safe.y + 40
	lbl.offset_bottom = -(safe.w + 150)
	o.add_child(lbl)
	# the largest display size at which the longest card still fits its rect (Extra large on a short screen)
	var avail_w := canvas.x - safe.x - safe.z - 320.0
	var avail_h := canvas.y - safe.y - safe.w - 190.0
	var fs := UITheme.size(44)
	var floor_fs := UITheme.size(26)
	var f := lbl.get_theme_font("font")
	for key in logic.intro_keys():
		while fs > floor_fs and f.get_multiline_string_size(tr(key), HORIZONTAL_ALIGNMENT_CENTER, avail_w, fs).y > avail_h * 0.78:
			fs = maxi(floor_fs, int(fs * 0.92))
	lbl.add_theme_font_size_override("font_size", fs)
	var rule_top := UIOrnament.rule(0.0, 24.0)
	var rule_bottom := UIOrnament.rule(0.0, 24.0)
	o.add_child(rule_top)
	o.add_child(rule_bottom)
	var tap := UITheme.label("ui.tap_to_continue", 22, UITheme.MUTED)
	tap.add_theme_font_override("font", UITheme.caps_font(false, 2))
	tap.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	tap.offset_top = -(safe.w + 120)
	tap.offset_bottom = -(safe.w + 50)
	var tap_half := minf(500.0 * UITheme.wscale(), (canvas.x - safe.x - safe.z) * 0.5 - 24.0) # never past the safe edges
	tap.offset_left = -tap_half
	tap.offset_right = tap_half
	tap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tap.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	o.add_child(tap)
	var own_impact := room.has_method("intro_impact") # Chapter 2+: the room plays its own opening beat
	if not own_impact:
		AudioManager.ambience("amb_lab_dark", true, -6.0, 3.0)
	for key in logic.intro_keys():
		lbl.text = tr(key)
		_intro_rules(lbl, rule_top, rule_bottom, canvas)
		lbl.modulate.a = 0.0
		rule_top.modulate.a = 0.0
		rule_bottom.modulate.a = 0.0
		var tw := create_tween().set_parallel(true)
		tw.tween_property(lbl, "modulate:a", 1.0, 1.0)
		tw.tween_property(rule_top, "modulate:a", 1.0, 1.2)
		tw.tween_property(rule_bottom, "modulate:a", 1.0, 1.2)
		await _wait_tap_or(o, 6.0)
		var tw2 := create_tween().set_parallel(true)
		tw2.tween_property(lbl, "modulate:a", 0.0, 0.6)
		tw2.tween_property(rule_top, "modulate:a", 0.0, 0.6)
		tw2.tween_property(rule_bottom, "modulate:a", 0.0, 0.6)
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


## Places the two rules just above and below the card's text block (which is centred in the label's rect).
func _intro_rules(lbl: Label, top: UIOrnament, bottom: UIOrnament, canvas: Vector2) -> void:
	var f := lbl.get_theme_font("font")
	var fs := lbl.get_theme_font_size("font_size")
	var w := lbl.offset_right - lbl.offset_left + canvas.x # the label's width (offsets are from both edges)
	var txt := f.get_multiline_string_size(lbl.text, HORIZONTAL_ALIGNMENT_CENTER, w, fs)
	var cy := (lbl.offset_top + canvas.y + lbl.offset_bottom) * 0.5
	var k := UIOrnament.scale_k()
	var rw := clampf(txt.x + 220.0 * k, 420.0, w)
	var gap := 34.0 * k
	for r: UIOrnament in [top, bottom]:
		r.size = Vector2(rw, 24.0)
		r.custom_minimum_size = r.size
		r.position.x = roundf((canvas.x - rw) * 0.5)
	top.position.y = roundf(cy - txt.y * 0.5 - gap - 24.0)
	bottom.position.y = roundf(cy + txt.y * 0.5 + gap)


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
	head.add_theme_font_override("font", UITheme.caps_font(false, 2))
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(head)
	v.add_child(UITheme.title("chapter.%s.title" % GameState.chapter_id, 60))
	v.add_child(UIOrnament.rule())
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
		a.add_theme_font_override("font", UITheme.caps_font(false, 1))
		a.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var b := UITheme.label(pair[1], 34, UITheme.BRASS_HI)
		b.add_theme_font_override("font", UITheme.display_font(true))
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
