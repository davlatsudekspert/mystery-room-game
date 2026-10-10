extends CanvasLayer
## In-game HUD for room chapters, in the main menu's visual language (docs/UI_UX.md → HUD): centred banners
## (a small-caps serif title between gold flourishes over a thin rule, a subtitle below, on a soft dark band)
## for the view title, captions, messages, prompts and "item found"; the inventory in a bag (bottom left) whose
## tray, a column of slots beside a thin vertical gold rule, slides out above it; round bezel buttons (Back top
## left, Hint top right, Pause with a roman II bottom right); hints, documents (with UV page), the inspect view,
## pause, intro, finale choice and the chapter-complete screen as dialogs in the same style.
## Only buttons and slots take a tap: every container, rule, banner and picture lets it through to the room
## (blocked_rects() lists what does not).
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
var _bag_btn: IconButton # the inventory: opens and closes the tray (docs/UI_UX.md → Bag)
var _bag_open := false # the tray is out
var _closeup := false # the camera is at a close-up: the tray starts collapsed there
var _inv_tween: Tween
var _bag_tween: Tween
var _inv_drag := 0.0 # how far the finger has moved on a slot since it touched it (a drag scrolls the tray)
var _fly: FlyIcon # a found item on its way into the bag
var _msg_on := false # the message banner is showing (from message() until its fade-out starts)
var _cap_on := false # the same for the caption
var _msg_at := 0 # when each was shown: the newer of the two keeps its place when both do not fit
var _cap_at := 0
var _meter_label: Label

const PAD := UITheme.HUD_PAD # gap between HUD controls and the safe-area edge
const INV_SEP := 10
const ACTION_GAP := 12.0 # between the inventory rule and the item actions
const TRAY_SLIDE := 0.22 # seconds: the tray slides out of / back toward the left edge
const TRAY_SHIFT := 0.6 # of the tray's width: how far it slides


func bind(r: Node3D) -> void:
	room = r
	logic = r.get("logic")
	layer = 10
	icons = ItemIcons.new()
	icons.logic = logic
	add_child(icons)
	icons.icon_ready.connect(func(id: String, t: Texture2D) -> void:
		_refresh_inventory()
		if is_instance_valid(_fly) and _fly.item_id == id:
			_fly.tex = t
		if id == _found_id and _msg_plate != null:
			_msg_plate.set_icon(t)
			_arrange())
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
	_root = Control.new() # as large as the canvas (sized in _layout, so an emulated screen in tests and QA matches)
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
	_bag_btn = IconButton.make("bag", int(UITheme.HUD_BTN_PX))
	_bag_btn.tooltip_text = "ui.bag"
	_root.add_child(_bag_btn)
	_bag_btn.pressed.connect(func() -> void: set_bag_open(not _bag_open, true))
	_back_btn.name = "Back"
	_hint_btn.name = "Hint"
	_pause_btn.name = "Pause"
	_bag_btn.name = "Bag"

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

	# the bag's tray: a scrolling stack of slots, a vertical rule with arrow tips, the actions flyout. Only the
	# slots and the item actions take taps; the scroll box, the stack and the rule let them through (a drag on a
	# slot scrolls the stack itself, see _on_slot_input)
	_inv_panel = Control.new()
	_inv_panel.name = "Tray"
	_inv_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_inv_panel)
	_inv_scroll = ScrollContainer.new()
	_inv_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_inv_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_inv_scroll.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_inv_scroll.get_v_scroll_bar().mouse_filter = Control.MOUSE_FILTER_IGNORE # hidden; the finger scrolls
	_inv_scroll.get_h_scroll_bar().mouse_filter = Control.MOUSE_FILTER_IGNORE
	_inv_panel.add_child(_inv_scroll)
	_inv_box = VBoxContainer.new()
	_inv_box.add_theme_constant_override("separation", INV_SEP)
	_inv_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_inv_scroll.add_child(_inv_box)
	_inv_scroll.get_v_scroll_bar().value_changed.connect(func(_v: float) -> void: _place_actions())
	_inv_rule = UIOrnament.vrule(UITheme.HUD_RULE_W)
	_inv_panel.add_child(_inv_rule)
	_actions = HBoxContainer.new()
	_actions.add_theme_constant_override("separation", 6)
	_actions.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_actions.visible = false
	_inv_panel.add_child(_actions)
	_act_inspect = IconButton.make("inspect", 96)
	_act_inspect.pressed.connect(func() -> void: show_inspect(logic.selected))
	_actions.add_child(_act_inspect)
	_act_combine = IconButton.make("combine", 96)
	_act_combine.pressed.connect(_toggle_combine)
	_actions.add_child(_act_combine)
	_bag_open = bool(Settings.get_value("inventory_open"))
	_inv_panel.visible = _bag_open
	_layout()
	_quiet(_root)


## Containers, rules, banners, bars and pictures never take a tap: only buttons do, so a tap beside a slot or
## on a banner still reaches the room (on a touch screen any control that is not IGNORE swallows the touch).
static func _quiet(n: Node) -> void:
	if n is Control and not (n is BaseButton):
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for ch in n.get_children():
		_quiet(ch)


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
	_root.position = Vector2.ZERO
	_root.size = canvas
	var side := maxf(safe.x, safe.z) # keep centred elements symmetric
	var cb := _pause_btn.custom_minimum_size.x
	var bd := _back_btn.custom_minimum_size.x
	var corner := maxf(cb, bd)
	_pin(_back_btn, Control.PRESET_TOP_LEFT, Vector2(safe.x + PAD, safe.y + PAD))
	_pin(_hint_btn, Control.PRESET_TOP_RIGHT, Vector2(-(safe.z + PAD + cb), safe.y + PAD))
	_pin(_pause_btn, Control.PRESET_BOTTOM_RIGHT, Vector2(-(safe.z + PAD + cb), -(safe.w + PAD + cb)))
	_pin(_bag_btn, Control.PRESET_BOTTOM_LEFT, Vector2(safe.x + PAD, -(safe.w + PAD + cb)))
	# top: the view title between the corner buttons (centred on their row), the caption line below
	var top_w := canvas.x - 2.0 * (side + PAD + corner + 20.0)
	_top_plate.set_meta("max_w", minf(top_w, 1400.0 * UITheme.wscale()))
	_top_plate.set_meta("y", safe.y + PAD)
	_top_plate.set_meta("row_h", corner)
	# left: the bag's tray, from under the Back button down to just above the bag
	var col_top := safe.y + PAD + bd + 16.0
	var col_bottom := canvas.y - safe.w - PAD - cb - 16.0
	_inv_span = Rect2(safe.x + PAD, col_top, UITheme.hud_column_width(), col_bottom - col_top)
	_inv_panel.size = _inv_span.size
	if not (_inv_tween and _inv_tween.is_running()):
		_inv_panel.position = _tray_pos(_bag_open)
	# bottom centre: the prompt, with the message above it; both clear of the column and the pause button
	var text_w := UITheme.hud_text_width()
	_prompt_plate.set_meta("max_w", text_w)
	_prompt_plate.set_meta("from_bottom", true)
	_msg_plate.set_meta("max_w", text_w)
	_msg_plate.set_meta("from_bottom", true)
	_arrange()
	_inventory_geometry()


## (Older names: the banners are laid out together.)
func _stack_top() -> void:
	_arrange()


func _stack_bottom() -> void:
	_arrange()


## Lays the banners and the meter out so that nothing overlaps (a corner button, the bag, the open tray and its
## item actions, each other) at any text size on any screen shape, inside the safe area (docs/UI_UX.md → HUD
## layout; test_hud_layout.gd):
##   1. the meter (Chapter 2) under the Hint button;
##   2. the view title between the corner buttons, centred on their row, two lines at most (an ellipsis beyond);
##      a second line keeps clear of the meter (narrower), or the meter moves under the title;
##   3. the prompt at the bottom (two lines at most), the message above it at full width under the meter, or
##      narrower beside it, whichever shows more of it, cut to the lines that fit under the title;
##   4. the caption under the title, beside the meter (under it when beside is too narrow), cut to the lines that
##      fit above the message and the prompt.
## When the caption and the message cannot both keep a line, the older of them fades out (the newer line is the
## one the player is waiting for); one that cannot keep a line at all gives way.
func _arrange() -> void:
	if _root == null:
		return
	var safe := UITheme.safe_margins()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var corner := maxf(_pause_btn.custom_minimum_size.x, _back_btn.custom_minimum_size.x)
	var row_bottom := safe.y + PAD + corner + 10.0
	var gap := 10.0
	var cx := canvas.x * 0.5
	# 1. the meter, under the Hint button
	var mr := Rect2()
	if _meter != null:
		_fit_meter(canvas)
		var ms := _meter.get_combined_minimum_size()
		mr = Rect2(canvas.x - safe.z - PAD - ms.x, row_bottom, ms.x, ms.y)
		if not _meter.visible:
			mr = Rect2()
	var meter_half := mr.position.x - 20.0 - cx # half the width a centred banner has beside the meter
	# the prompt (fitted first: the meter may only move down as far as the prompt's top)
	var bottom := canvas.y - safe.w - PAD
	var text_w := UITheme.hud_text_width()
	_prompt_plate.max_sub_lines = 2
	_prompt_plate.set_meta("y", bottom)
	_prompt_plate.set_meta("max_w", text_w)
	_fit_plate(_prompt_plate)
	var low := canvas.y - safe.w - PAD - _pause_btn.custom_minimum_size.y - gap # the meter clears Pause
	if _prompt_plate.visible and mr.has_area() and _box(_prompt_plate).end.x > mr.position.x:
		low = minf(low, _prompt_plate.position.y - gap)
	# 2. the title (two lines at most); a second line keeps clear of the meter, or the meter moves down
	var top_w: float = _top_plate.get_meta("max_w", 1200.0)
	_top_plate.max_title_lines = 2
	_fit_plate(_top_plate)
	if mr.has_area() and _top_plate.visible and _box(_top_plate).intersects(mr.grow(gap)):
		# narrower, beside the meter, when the whole title still fits; otherwise the full width (which shows more
		# of it) and the meter moves under the title, if it still clears the prompt and the Pause button there
		var narrow := minf(top_w, 2.0 * meter_half)
		_top_plate.set_meta("max_w", narrow)
		_fit_plate(_top_plate)
		_top_plate.set_meta("max_w", top_w)
		if _top_plate.title_cut:
			_fit_plate(_top_plate)
			if _top_plate.position.y + _top_plate.size.y + gap + mr.size.y > low:
				_top_plate.set_meta("max_w", narrow) # no room under it: beside the meter, cut
				_fit_plate(_top_plate)
				_top_plate.set_meta("max_w", top_w)
		if _box(_top_plate).intersects(mr.grow(gap)):
			mr.position.y = _top_plate.position.y + _top_plate.size.y + gap
	if _meter != null:
		_meter.offset_right = -(safe.z + PAD)
		_meter.offset_left = _meter.offset_right
		_meter.offset_top = mr.position.y if mr.has_area() else row_bottom
		_meter.offset_bottom = _meter.offset_top
	var title_box := _box(_top_plate) if _top_plate.visible else Rect2(cx, safe.y + PAD, 0.0, 0.0)
	var tops: Array[Rect2] = [title_box]
	if mr.has_area():
		tops.append(mr)
	# 3. the prompt at the bottom (narrower only if the meter still reaches it), the message above it
	if mr.has_area() and _prompt_plate.visible and _box(_prompt_plate).intersects(mr.grow(gap)):
		_prompt_plate.set_meta("max_w", minf(text_w, 2.0 * meter_half))
		_fit_plate(_prompt_plate)
	var floor_y := bottom
	if _prompt_plate.visible:
		floor_y = _prompt_plate.position.y - gap
	var msg_full := 3 if _found_id != "" else 0
	# the message keeps clear of the item actions beside the open tray (they stay level with their slot)
	var msg_w := text_w
	if _bag_open and _actions.visible:
		var fly_right := _inv_span.position.x + _inv_rule.position.x + _inv_rule.size.x + ACTION_GAP + _actions.get_combined_minimum_size().x
		msg_w = minf(msg_w, maxf(200.0, 2.0 * (cx - fly_right - 20.0)))
	var widths: Array[float] = [msg_w]
	if mr.has_area() and meter_half * 2.0 < msg_w:
		widths.append(maxf(200.0, 2.0 * meter_half)) # beside the meter instead of under it
	var best_w := msg_w
	var best_score := -1.0
	for w in widths:
		_msg_plate.set_meta("max_w", w)
		_msg_plate.set_meta("y", floor_y)
		var ceiling := _below(tops, Vector2(cx - w * 0.5, cx + w * 0.5), safe.y + PAD) + gap
		_cut_to(_msg_plate, msg_full, ceiling)
		var score := float(_msg_plate.sub_lines) * w if _plate_fits(_msg_plate, ceiling) else -float(w) * 0.001
		if score > best_score + 1.0:
			best_score = score
			best_w = w
	_msg_plate.set_meta("max_w", best_w)
	var msg_ceiling := _below(tops, Vector2(cx - best_w * 0.5, cx + best_w * 0.5), safe.y + PAD) + gap
	_cut_to(_msg_plate, msg_full, msg_ceiling)
	if _msg_on and not _plate_fits(_msg_plate, msg_ceiling):
		_give_way(_msg_plate)
	var cap_floor := floor_y
	if _msg_on and _msg_plate.visible:
		cap_floor = _msg_plate.position.y - gap
	# 4. the caption: under the title, centred in the room left between the left and right controls; beside the
	# meter when that leaves a reasonable line, under it otherwise
	var left := safe.x + PAD + corner + 20.0
	if _bag_open:
		left = maxf(left, _inv_span.position.x + _inv_span.size.x + 20.0)
		if _actions.visible:
			left += ACTION_GAP + _actions.get_combined_minimum_size().x
	var right := canvas.x - safe.z - PAD - corner - 20.0
	if mr.has_area() and mr.position.x - 20.0 - left >= canvas.x * 0.3:
		right = minf(right, mr.position.x - 20.0)
	_cap_plate.set_meta("cx", (left + right) * 0.5)
	_cap_plate.set_meta("max_w", minf(right - left, 1500.0 * UITheme.wscale()))
	_cap_plate.set_meta("y", maxf(row_bottom, _below(tops, Vector2(left, right), row_bottom) + 6.0))
	_cut_to_floor(_cap_plate, cap_floor)
	if _cap_on and _caption_line.text != "" and not _plate_above(_cap_plate, cap_floor):
		if _msg_on and _msg_plate.visible and _cap_at >= _msg_at:
			_give_way(_msg_plate) # the caption is newer: the message makes room
			_cut_to_floor(_cap_plate, floor_y)
		if not _plate_above(_cap_plate, floor_y if not _msg_on else cap_floor):
			_give_way(_cap_plate)
	_place_actions()


func _box(p: Control) -> Rect2:
	return Rect2(p.position, p.size)


## The lowest bottom edge among `rects` that reach over the horizontal span `xs` (x = from, y = to), or `floor`.
static func _below(rects: Array[Rect2], xs: Vector2, floor: float) -> float:
	var y := floor
	for r in rects:
		if r.position.x < xs.y and r.end.x > xs.x:
			y = maxf(y, r.end.y)
	return y


## Fits a bottom-anchored banner with at most `full` subtitle lines (0 = all), then fewer while its top is above
## `ceiling` (one line at least).
func _cut_to(p: UIBanner, full: int, ceiling: float) -> void:
	p.max_sub_lines = full
	_fit_plate(p)
	while p.visible and p.position.y < ceiling and p.sub_lines > 1:
		p.max_sub_lines = p.sub_lines - 1
		_fit_plate(p)


## Fits a top-anchored banner, then with fewer subtitle lines while its bottom runs past `floor_y`.
func _cut_to_floor(p: UIBanner, floor_y: float) -> void:
	p.max_sub_lines = 0
	_fit_plate(p)
	while p.visible and p.position.y + p.size.y > floor_y and p.sub_lines > 1:
		p.max_sub_lines = p.sub_lines - 1
		_fit_plate(p)


func _plate_fits(p: UIBanner, ceiling: float) -> bool:
	return not p.visible or p.position.y >= ceiling - 0.5


func _plate_above(p: UIBanner, floor_y: float) -> bool:
	return not p.visible or p.position.y + p.size.y <= floor_y + 0.5


## A banner that has no room left fades out now (its line is over).
func _give_way(p: UIBanner) -> void:
	if p == _msg_plate:
		_msg_on = false
		if _msg_tween and _msg_tween.is_valid():
			_msg_tween.kill()
	elif p == _cap_plate:
		_cap_on = false
		if _cap_tween and _cap_tween.is_valid():
			_cap_tween.kill()
	if p.modulate.a > 0.0:
		var tw := create_tween()
		tw.tween_property(p, "modulate:a", 0.0, 0.2)
	p.set_meta("on", false)


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
	_actions.visible = has_sel and _bag_open
	_place_actions.call_deferred()
	_update_bag()
	_update_prompt()


## The slots stand at the bottom of the tray's span, just above the bag they came out of; they scroll when there
## are more than fit. The rule runs beside them with its arrow tips just beyond the first and the last slot.
func _inventory_geometry() -> void:
	var slot := UITheme.target(UITheme.HUD_SLOT_PX, UITheme.SLOT_MM)
	var n := maxi(1, logic.inventory.size())
	var content_h := n * slot + (n - 1) * INV_SEP
	var tip := 16.0 * UIOrnament.scale_k()
	var h := minf(content_h, _inv_span.size.y - 2.0 * tip)
	var y0 := roundf(_inv_span.size.y - tip - h)
	_inv_scroll.position = Vector2(0, y0)
	_inv_scroll.custom_minimum_size = Vector2(slot, h)
	_inv_scroll.size = Vector2(slot, h)
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
	var x := _inv_rule.position.x + _inv_rule.size.x + ACTION_GAP
	# level with the slot, but kept inside the tray's span, under a title that wraps over it and above the
	# banners at the bottom (in the tray's coordinates)
	var lo := 0.0
	var hi := _inv_span.size.y - sz.y
	var xs := Vector2(_inv_span.position.x + x, _inv_span.position.x + x + sz.x)
	for p: UIBanner in [_top_plate]:
		var r := _box(p)
		if p.visible and r.position.x < xs.y and r.end.x > xs.x:
			lo = maxf(lo, r.end.y + 8.0 - _inv_span.position.y)
	for p: UIBanner in [_prompt_plate, _msg_plate]:
		var r := _box(p)
		if p.visible and (p != _msg_plate or _msg_on) and r.position.x < xs.y and r.end.x > xs.x:
			hi = minf(hi, r.position.y - 8.0 - sz.y - _inv_span.position.y)
	_actions.position = Vector2(x, clampf(slot_y + (slot - sz.y) * 0.5, lo, maxf(lo, hi)))


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
		# no icon yet (the model is still rendering): the name, wrapped inside the square slot (a Label child, so
		# the slot never grows taller than wide)
		var nl := UITheme.label(tr(ItemDB.name_key(id)), 18)
		nl.set_anchors_preset(Control.PRESET_FULL_RECT)
		nl.offset_left = 6
		nl.offset_right = -6
		nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		nl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		nl.clip_text = true
		nl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		nl.max_lines_visible = 3
		nl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(nl)
	b.pressed.connect(func() -> void: _on_slot(id))
	b.gui_input.connect(_on_slot_input)
	return b


## A finger that moves on a slot scrolls the tray (the scroll box itself lets taps through to the room), and the
## press then does not count as a tap on the slot.
func _on_slot_input(ev: InputEvent) -> void:
	var dy := 0.0
	if ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_inv_drag = 0.0
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			dy = 60.0
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			dy = -60.0
	elif ev is InputEventMouseMotion and ((ev as InputEventMouseMotion).button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
		dy = (ev as InputEventMouseMotion).relative.y
		_inv_drag += absf(dy)
	if dy != 0.0:
		_inv_scroll.scroll_vertical = int(_inv_scroll.scroll_vertical - dy)


func _on_slot(id: String) -> void:
	if _inv_drag >= UITheme.px_for_mm(2.0):
		_inv_drag = 0.0
		return # the finger scrolled the tray
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
		var combine_tip := false
		if logic.has_item("uv_lamp_empty") and logic.has_item("battery_cell"):
			combine_tip = _tip_once("combine", "tut.combine")
		if _closeup and not combine_tip:
			_collapse_after_pick(id)
	_refresh_inventory()


## In a close-up the tray gets out of the way once an item is in hand: the player's next tap is on the room. The
## bag then shows the item.
func _collapse_after_pick(id: String) -> void:
	var tw := create_tween()
	tw.tween_interval(0.3)
	tw.tween_callback(func() -> void:
		if _closeup and _bag_open and logic.selected == id and not _combine_mode and _overlay == null:
			set_bag_open(false))


# ====================================================================== bag
## Opens or closes the tray with a short eased slide (a plain fade with Settings → Reduce camera motion).
## `by_player`: at a room view the choice is remembered (Settings "inventory_open"); in a close-up it lasts
## until the view changes, since close-ups always start with the tray in.
func set_bag_open(open: bool, by_player: bool = false) -> void:
	if by_player and not _closeup and bool(Settings.get_value("inventory_open")) != open:
		Settings.set_value("inventory_open", open)
	if open == _bag_open:
		return
	_bag_open = open
	if not open:
		_combine_mode = false
	_slide_tray()
	_refresh_inventory()
	_arrange() # the caption keeps clear of the tray only while it is out


func is_bag_open() -> bool:
	return _bag_open


## Where the tray rests when it is out, or where it slides in from (and back to).
func _tray_pos(out: bool) -> Vector2:
	return _inv_span.position if out else _inv_span.position - Vector2(_inv_span.size.x * TRAY_SHIFT, 0.0)


func _slide_tray() -> void:
	if _inv_tween and _inv_tween.is_valid():
		_inv_tween.kill()
	var reduce := bool(Settings.get_value("reduce_motion"))
	var to := _tray_pos(_bag_open)
	if _bag_open:
		if not _inv_panel.visible:
			_inv_panel.position = to if reduce else _tray_pos(false)
			_inv_panel.modulate.a = 0.0
		_inv_panel.visible = not _busy
	elif reduce:
		to = _inv_panel.position
	_inv_tween = create_tween().set_parallel(true)
	_inv_tween.tween_property(_inv_panel, "position", to, TRAY_SLIDE).set_trans(Tween.TRANS_CUBIC).set_ease(
		Tween.EASE_OUT if _bag_open else Tween.EASE_IN)
	_inv_tween.tween_property(_inv_panel, "modulate:a", 1.0 if _bag_open else 0.0, TRAY_SLIDE * (0.8 if _bag_open else 1.0))
	if not _bag_open:
		_inv_tween.chain().tween_callback(func() -> void: _inv_panel.visible = false)


## The bag is lit while the tray is out; with the tray in it shows the item in hand and how many items it holds.
func _update_bag() -> void:
	if _bag_btn == null:
		return
	_bag_btn.active = _bag_open
	_bag_btn.picture = icons.get_icon(logic.selected) if logic.selected != "" and not _bag_open else null
	_bag_btn.count = 0 if _bag_open else logic.inventory.size()


## The bag swells once (a found item has landed in it, or the tutorial points at it).
func _pulse_bag() -> void:
	if _bag_tween and _bag_tween.is_valid():
		_bag_tween.kill()
	_bag_btn.pivot_offset = _bag_btn.size * 0.5
	_bag_tween = create_tween()
	_bag_tween.tween_property(_bag_btn, "scale", Vector2.ONE * 1.16, 0.12).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_bag_tween.tween_property(_bag_btn, "scale", Vector2.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## A found item flies from its banner (or the screen's centre) along a gentle arc into the bag, which pulses once
## as it lands. With Reduce camera motion the bag only pulses.
func _fly_to_bag(id: String) -> void:
	if _busy or not _bag_btn.is_visible_in_tree() or not logic.has_item(id):
		return
	if _overlay != null:
		_pulse_bag() # a document or dialog is open: no flight across it (the bag under it still swells)
		return
	if bool(Settings.get_value("reduce_motion")):
		_pulse_bag()
		return
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var side := UITheme.target(110.0)
	var start := canvas * 0.5
	var ir := _msg_plate.icon_global_rect() if _found_id == id and _msg_plate.visible and _msg_plate.modulate.a > 0.5 else Rect2()
	if ir.size.x > 0.0:
		start = ir.get_center()
		side = ir.size.x
	var end := _bag_btn.get_global_rect().get_center()
	if is_instance_valid(_fly):
		_fly.queue_free()
	_fly = FlyIcon.new()
	_fly.item_id = id
	_fly.tex = icons.get_icon(id)
	_fly.size = Vector2(side, side)
	_fly.pivot_offset = _fly.size * 0.5
	_fly.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_fly)
	if _overlay != null:
		_root.move_child(_fly, _overlay.get_index()) # under an open document or dialog, never over it
	_fly.position = start - _fly.size * 0.5
	var ctrl := Vector2(lerpf(start.x, end.x, 0.3), minf(start.y, end.y) - canvas.y * 0.16) # the top of the arc
	var f := _fly
	var tw := create_tween()
	tw.tween_method(func(t: float) -> void:
		if not is_instance_valid(f):
			return
		var p := start.lerp(ctrl, t).lerp(ctrl.lerp(end, t), t)
		f.position = p - f.size * 0.5
		f.scale = Vector2.ONE * lerpf(1.0, 0.4, t)
		f.modulate.a = lerpf(1.0, 0.75, t), 0.0, 1.0, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(f.queue_free)
	tw.tween_callback(_pulse_bag)


## Every visible HUD control that takes a tap, so the room behind it cannot be tapped there: in viewport pixels
## (the canvas the room camera projects to, Camera3D.unproject_position()). Only buttons and slots take taps;
## a slot scrolled partly out of the tray counts with its visible part, and an open overlay covers the screen.
## The room camera frames close-ups so that their controls stay out of these rects (docs/UI_UX.md → Blocked
## rects). In a close-up the tray is in, so these are the four corner buttons.
func blocked_rects() -> Array[Rect2]:
	var out: Array[Rect2] = []
	if _root != null:
		_collect_blocked(_root, Rect2(), out)
	return out


func _collect_blocked(n: Node, clip: Rect2, out: Array[Rect2]) -> void:
	if n is CanvasItem and not (n as CanvasItem).visible:
		return
	if n is Control:
		var c := n as Control
		var r := c.get_global_rect()
		if c.mouse_filter != Control.MOUSE_FILTER_IGNORE:
			var shown := r if clip.size == Vector2.ZERO else r.intersection(clip)
			if shown.has_area():
				out.append(shown)
		if c.clip_contents:
			clip = r if clip.size == Vector2.ZERO else clip.intersection(r)
	for ch in n.get_children():
		_collect_blocked(ch, clip, out)


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
	_arrange() # the caption keeps clear of the prompt


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
	if _msg_tween and _msg_tween.is_valid():
		_msg_tween.kill()
	_msg_on = text.strip_edges() != ""
	_msg_at = Time.get_ticks_usec()
	_msg_plate.set_meta("on", _msg_on)
	_arrange()
	if not _msg_on:
		_msg_plate.modulate.a = 0.0
		return
	_msg_tween = create_tween()
	_msg_tween.tween_property(_msg_plate, "modulate:a", 1.0, 0.18)
	_msg_tween.tween_interval(seconds)
	_msg_tween.tween_callback(func() -> void:
		_msg_on = false
		_msg_plate.set_meta("on", false))
	_msg_tween.tween_property(_msg_plate, "modulate:a", 0.0, 0.5)


func caption(text: String, seconds: float = 3.5) -> void:
	_caption_line.text = text
	if _cap_tween and _cap_tween.is_valid():
		_cap_tween.kill()
	_cap_on = text.strip_edges() != ""
	_cap_at = Time.get_ticks_usec()
	_cap_plate.set_meta("on", _cap_on)
	_arrange()
	if not _cap_on:
		_cap_plate.modulate.a = 0.0
		return
	_cap_tween = create_tween()
	_cap_tween.tween_property(_cap_plate, "modulate:a", 1.0, 0.25)
	_cap_tween.tween_interval(seconds)
	_cap_tween.tween_callback(func() -> void:
		_cap_on = false
		_cap_plate.set_meta("on", false))
	_cap_tween.tween_property(_cap_plate, "modulate:a", 0.0, 0.6)


func set_view(id: String, is_root: bool, caption_key: String) -> void:
	var main := str(room.call("main_root")) if room.has_method("main_root") else ""
	_back_wanted = not is_root or id == "darkroom" or (main != "" and id != main)
	_back_btn.visible = _back_wanted and not _busy # cinematics (e.g. the intro's shutter shot) lock input
	# the bag: close-ups start with the tray in (the whole close-up is the puzzle); room views show it as the
	# player last left it there
	var was_closeup := _closeup
	_closeup = not is_root
	if _closeup:
		set_bag_open(false)
	elif was_closeup:
		set_bag_open(bool(Settings.get_value("inventory_open")))
	set_caption(caption_key)


func set_caption(caption_key: String) -> void:
	# the key itself: the label auto-translates, so a language switch in the pause menu updates it too
	_top_caption.text = caption_key
	_arrange()


func set_busy(b: bool) -> void:
	_busy = b
	_inv_panel.visible = not b and _bag_open
	_bag_btn.visible = not b
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
		if e.begins_with("item_added:"):
			var id := e.substr(11)
			if logic.inventory.size() == 1 and _tip_once("inventory", "tut.inventory"):
				_pulse_bag() # the first item: the tip says where the bag is
			var tw := create_tween() # the banner shows it first, then it flies into the bag
			tw.tween_interval(0.6)
			tw.tween_callback(_fly_to_bag.bind(id))
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


## Shows a tutorial line once per session. -> true when it was shown now.
func _tip_once(id: String, key: String) -> bool:
	if _tips_shown.has(id):
		return false
	_tips_shown[id] = true
	caption(tr(key), 4.5)
	return true


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


## Android back / Escape (SceneManager._dispatch_back() → room.handle_back(), which asks the HUD first). One press
## undoes one thing, the nearest first:
##   1. the open overlay: a document, a zoomed picture, the inspect view, a hint, pause or settings (settings
##      return to the pause menu and an enlarged photograph to the evidence board, as their Close buttons do);
##   2. the item in hand: Combine is left, then the item goes back into the bag;
##   3. the open tray folds into the bag.
## -> true when the press was used here. Only then does the room move the camera back, and at the room view
## open the pause menu. The finale choice and the chapter-complete screen need an explicit answer, and
## cinematics (the intro) swallow the press.
func consume_back() -> bool:
	if _overlay != null:
		if not bool(_overlay.get_meta("locked", false)):
			var back: Callable = _overlay.get_meta("back", Callable())
			if back.is_valid():
				back.call()
			else:
				_close_overlay()
		return true
	if _busy:
		return true
	if _combine_mode:
		_combine_mode = false
		_refresh_inventory()
		return true
	if logic.selected != "":
		logic.select_item("")
		_refresh_inventory()
		return true
	if _bag_open:
		set_bag_open(false, true)
		return true
	return false


## The older name of consume_back() (rooms and QA scripts call it).
func handle_back() -> bool:
	return consume_back()


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
## The hint ladder (owner feedback: hints "only help a little"): level 1 nudges, 2 says more, 3 is the answer.
## The current rung is "Hint N of 3" over its text; the earlier rungs stay above it, smaller and muted, so nothing
## said before is lost. The button names the next step: "Stronger hint (2/3)", then "Show the answer (3/3)"; it
## goes away at the answer. Asked again about the same goal, the dialog opens at the highest level reached.
func show_hint() -> void:
	_hint_btn.badge = ""
	var o := _open_overlay(0.55)
	var d := UITheme.dialog(o, 980, "ui.hint", 46)
	var v: VBoxContainer = d["body"]
	var ladder := VBoxContainer.new()
	ladder.add_theme_constant_override("separation", 18)
	v.add_child(ladder)
	var h: HFlowContainer = d["footer"]
	var more := UITheme.button("ui.hint_more", 560) # wide enough for "Show the answer (3/3)"
	var close := UITheme.button("ui.close", 240)
	h.add_child(more)
	h.add_child(close)
	var shown: Array[Dictionary] = GameState.shown_hints()
	if shown.is_empty():
		var first := GameState.next_hint()
		if not first.is_empty():
			shown.append(first)
			AudioManager.sfx("hint", -4.0)
	var render := func() -> void:
		for c in ladder.get_children():
			ladder.remove_child(c)
			c.queue_free()
		for i in shown.size():
			ladder.add_child(_hint_rung(shown[i], i == shown.size() - 1))
		var top := int(shown[-1]["level"]) if not shown.is_empty() else 3
		more.text = "ui.hint_more" if top <= 1 else "ui.hint_answer"
		more.disabled = top >= 3
		more.visible = top < 3
	render.call()
	more.pressed.connect(func() -> void:
		var hint := GameState.next_hint()
		if hint.is_empty():
			return
		AudioManager.sfx("hint", -4.0)
		if shown.is_empty() or int(hint["level"]) > int(shown[-1]["level"]):
			shown.append(hint)
		render.call()
		_scroll_to_end.call_deferred(v.get_parent() as ScrollContainer))
	close.pressed.connect(_close_overlay)
	_scroll_to_end.call_deferred(v.get_parent() as ScrollContainer) # reopened at a high level: the newest rung


## One rung of the hint ladder: "Hint N of 3" (or "… the answer") in small caps over its text; the current rung in
## full size (the heading in brass), an earlier one smaller and muted, under a hairline.
func _hint_rung(hint: Dictionary, current: bool) -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	var lvl := int(hint["level"])
	var head := UITheme.label(tr("ui.hint_level_answer") if lvl >= 3 else tr("ui.hint_level") % lvl, 22 if current else 20,
		UITheme.BRASS_HI if current else UITheme.MUTED)
	head.add_theme_font_override("font", UITheme.caps_font(current, 1))
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	head.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	box.add_child(head)
	var args: Array = hint.get("args", [])
	var text := UITheme.label(tr(hint["key"]) % args if not args.is_empty() else tr(hint["key"]), 30 if current else 24,
		UITheme.CREAM if current else UITheme.MUTED)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	box.add_child(text)
	if not current:
		var rule := UIOrnament.header_rule(12.0)
		rule.alpha = 0.3
		box.add_child(rule)
	box.set_meta("hint_level", lvl)
	return box


## Scrolls a dialog body to its end once its layout has settled (the newest hint is at the bottom).
func _scroll_to_end(s: ScrollContainer) -> void:
	if s == null:
		return
	for i in 2:
		await get_tree().process_frame
	if is_instance_valid(s):
		s.scroll_vertical = int(s.get_v_scroll_bar().max_value)


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
		o2.set_meta("back", show_pause) # Android back returns to the pause menu, as Close does
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
	if has_document(doc):
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
## The documents the reader can open (an item whose document is not listed here has no Read button).
const DOCUMENTS: Array[String] = ["notebook", "letter", "photo", "evidence", "darkroom_note", "badge", "index_card",
	"personnel_file", "tape_1996", "tape_1997", "tape_1998", "strand_letters", "strand_note", "growth_log", "poster",
	"chalkboard", "routing_chart"]


static func has_document(doc: String) -> bool:
	return DOCUMENTS.has(doc)


## Opens a document in the reader. An unknown id (a chapter's documents still to come) opens nothing.
func show_document(doc: String) -> void:
	if not has_document(doc):
		push_warning("HUD: no reader page for document «%s»" % doc)
		return
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
	var body: Control = _ink_label(tr("doc.notebook.p%d" % (pg + 1)) if pg != 4 else "")
	if pg == 3: # Panel 7: its four lamp icons stand beside the words (language-neutral, see _ink_icons)
		body = _ink_icons(tr("doc.notebook.p4"))
	v.add_child(body)
	if pg == 4:
		# the "blank" page: UV reveals Leyla's cipher
		var cipher := VBoxContainer.new()
		cipher.add_theme_constant_override("separation", 12)
		v.add_child(cipher)
		# the "blank" page: under the UV lamp Leyla's cipher glows on the paper (UIUVLight: a feathered violet
		# pool on the sheet, fluorescing fibres, glowing ink; no hard edge anywhere)
		var ink_line := _ink_label(tr("doc.notebook.p5_uv"))
		UIUVLight.glow_label(ink_line)
		cipher.add_child(ink_line)
		var glyphs := HBoxContainer.new()
		glyphs.alignment = BoxContainer.ALIGNMENT_CENTER
		glyphs.add_theme_constant_override("separation", 0) # the glow's margin spaces them
		for gid: Variant in l7.safe_glyphs(): # this game's cipher (docs/VARIANTS.md)
			glyphs.add_child(UIUVLight.glow_picture(load("res://assets/ui/glyphs/%s.png" % gid), round(90 * UITheme.wscale())))
		cipher.add_child(glyphs)
		cipher.visible = l7.state["uv_page"]
		if not l7.state["uv_page"] and l7.has_uv():
			var uvb := IconButton.make("uv", 110)
			var c := CenterContainer.new()
			c.add_child(uvb)
			v.add_child(c)
			uvb.pressed.connect(func() -> void:
				l7.uv_reveal("notebook_page")
				var light := UIUVLight.shine(paper, cipher, 0.0)
				cipher.visible = true
				cipher.modulate.a = 0.0
				var tw := create_tween()
				if not bool(Settings.get_value("reduce_motion")):
					# the tube strikes: a flicker, then the light settles
					tw.tween_property(light, "strength", 0.55, 0.07)
					tw.tween_property(light, "strength", 0.2, 0.06)
				tw.tween_property(light, "strength", 1.0, 0.5).set_ease(Tween.EASE_OUT)
				tw.parallel().tween_property(cipher, "modulate:a", 1.0, 1.2)
				uvb.visible = false)
		elif l7.state["uv_page"]:
			UIUVLight.shine(paper, cipher)
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


## Ink text with inline icons: each "{name}" in `text` becomes the glyph res://assets/ui/glyphs/<name>.png in ink
## colour, a bit taller than the letters (Leyla's notebook page 4 shows Panel 7's lamp icons next to the words, so
## the link between a word and a lamp does not depend on the translation).
func _ink_icons(text: String, sz: int = READ_PX) -> RichTextLabel:
	var l := RichTextLabel.new()
	l.bbcode_enabled = true
	l.fit_content = true
	l.scroll_active = false
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.add_theme_font_override("normal_font", UITheme.display_font(false))
	l.add_theme_font_size_override("normal_font_size", UITheme.size(sz))
	l.add_theme_color_override("default_color", INK)
	l.add_theme_constant_override("line_separation", 8)
	var re := RegEx.create_from_string("\\{(\\w+)\\}")
	var px := int(round(UITheme.size(sz) * 1.45))
	var out := ""
	var at := 0
	for m in re.search_all(text):
		out += text.substr(at, m.get_start() - at).replace("[", "[lb]")
		out += "[img=%d color=#%s]res://assets/ui/glyphs/%s.png[/img]" % [px, INK.to_html(false), m.get_string(1)]
		at = m.get_end()
	l.text = out + text.substr(at).replace("[", "[lb]")
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
	if back.is_valid():
		o.set_meta("back", back) # Android back reopens the view it came from, as Close does
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
		var t := UITheme.label("item.pocket_receiver.name", 20, UITheme.MUTED)
		t.add_theme_font_override("font", UITheme.caps_font(false, 1))
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t)
		_meter_label = t
		var h := HBoxContainer.new()
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		var k := UIOrnament.scale_k() # the bars are a picture: they grow with the ornaments, not with the text
		h.add_theme_constant_override("separation", int(round(8 * k)))
		v.add_child(h)
		for i in 5:
			var bar := ColorRect.new()
			bar.custom_minimum_size = Vector2(round(30 * k), round((14 + 9 * i) * k))
			bar.size_flags_vertical = Control.SIZE_SHRINK_END
			h.add_child(bar)
			_meter_bars.append(bar)
		_quiet(_meter)
		_meter.minimum_size_changed.connect(_arrange, CONNECT_DEFERRED) # its name wrapped: lay out again
	_meter.visible = level >= 0
	for i in 5:
		_meter_bars[i].color = Color("7dff9a") if i < level else Color(1, 1, 1, 0.12)
	_layout() # the caption line keeps clear of the meter


## The meter's name wraps (two lines at most) instead of making the meter wider than a quarter of the screen.
func _fit_meter(canvas: Vector2) -> void:
	if _meter_label == null:
		return
	var f := _meter_label.get_theme_font("font")
	var fs := _meter_label.get_theme_font_size("font_size")
	var text := _meter_label.atr(_meter_label.text)
	var w := f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4.0
	var bars := 0.0
	for b in _meter_bars:
		bars += b.custom_minimum_size.x + 8.0
	var word := 0.0 # never narrower than its longest word (a word is never broken)
	for part in text.split(" ", false):
		word = maxf(word, f.get_string_size(part, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4.0)
	var cap := maxf(maxf(bars, word), canvas.x * 0.24)
	_meter_label.autowrap_mode = TextServer.AUTOWRAP_OFF if w <= cap else TextServer.AUTOWRAP_WORD_SMART
	_meter_label.custom_minimum_size.x = minf(w, cap)


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
	lbl.offset_bottom = -(safe.w + 60 + ceilf(UITheme.caps_font(false, 2).get_height(UITheme.size(22))) + 40)
	o.add_child(lbl)
	# the largest display size at which the longest card still fits its rect (Extra large on a short screen)
	var avail_w := canvas.x - safe.x - safe.z - 320.0
	var avail_h := canvas.y - safe.y - safe.w - 100.0 - ceilf(UITheme.caps_font(false, 2).get_height(UITheme.size(22))) - 40.0
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
	# anchored by its bottom edge above the home indicator, as tall as its line (never growing into the inset)
	var tap_h := ceilf(UITheme.caps_font(false, 2).get_height(UITheme.size(22))) + 8.0
	tap.offset_bottom = -(safe.w + 50)
	tap.offset_top = tap.offset_bottom - tap_h
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


# ====================================================================== found item in flight
## A found item on its way into the bag: its icon on a soft brass glow (a brass glint while the icon renders).
class FlyIcon extends Control:
	var item_id := ""
	var tex: Texture2D:
		set(v):
			tex = v
			queue_redraw()

	func _draw() -> void:
		var c := size * 0.5
		var r := minf(size.x, size.y) * 0.5
		draw_circle(c, r * 0.95, Color(UITheme.BRASS_HI, 0.08))
		draw_circle(c, r * 0.7, Color(UITheme.BRASS_HI, 0.12))
		if tex != null:
			var ts := tex.get_size()
			var k := minf(r * 1.6 / ts.x, r * 1.6 / ts.y) if ts.x > 0.0 and ts.y > 0.0 else 1.0
			draw_texture_rect(tex, Rect2(c - ts * k * 0.5, ts * k), false)
		else:
			var d := r * 0.35
			draw_colored_polygon(PackedVector2Array([c + Vector2(-d, 0), c + Vector2(0, -d * 1.4), c + Vector2(d, 0),
				c + Vector2(0, d * 1.4)]), Color(UITheme.BRASS_HI, 0.95))
