extends CanvasLayer
## In-game HUD for room chapters: inventory, item actions, hints, documents (with UV page), inspect view,
## captions/messages, pause, intro, finale choice and chapter-complete screen.

var room: Node3D
var logic: RoomLogic
var icons: ItemIcons

var _root: Control
var _top_caption: Label
var _message: Label
var _caption_line: Label
var _prompt: Label
var _back_btn: IconButton
var _hint_btn: IconButton
var _pause_btn: IconButton
var _inv_panel: PanelContainer
var _inv_box: HBoxContainer
var _inv_scroll: ScrollContainer
var _meter: PanelContainer
var _meter_bars: Array[ColorRect] = []
const INV_MAX_W := 1180.0 # wider inventories scroll sideways
var _act_inspect: IconButton
var _act_combine: IconButton
var _combine_mode := false
var _overlay: Control
var _msg_tween: Tween
var _cap_tween: Tween
var _busy := false
var _tips_shown: Dictionary = {}
var _last_progress_ms := 0


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
	Settings.changed.connect(func(k: String) -> void:
		if k == "text_scale":
			_root.theme = UITheme.build())
	SaveSystem.saved.connect(_on_saved)
	_refresh_inventory()
	_last_progress_ms = Time.get_ticks_msec()


# ====================================================================== layout
func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = UITheme.build()
	add_child(_root)
	var safe := _safe_margins()

	_pause_btn = IconButton.make("pause", 92)
	_place(_pause_btn, Control.PRESET_TOP_LEFT, Vector2(safe.x + 28, safe.y + 24))
	_pause_btn.pressed.connect(show_pause)
	_hint_btn = IconButton.make("hint", 92)
	_place(_hint_btn, Control.PRESET_TOP_RIGHT, Vector2(-(safe.z + 28 + 92), safe.y + 24))
	_hint_btn.pressed.connect(show_hint)

	_top_caption = _shadow_label(30)
	_top_caption.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_top_caption.offset_left = -560
	_top_caption.offset_right = 560
	_top_caption.offset_top = safe.y + 34
	_top_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_top_caption.add_theme_font_override("font", UITheme.display_font(true))
	_top_caption.add_theme_color_override("font_color", UITheme.BRASS_HI)
	_root.add_child(_top_caption)

	_caption_line = _shadow_label(24)
	_caption_line.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_caption_line.offset_left = -560
	_caption_line.offset_right = 560
	_caption_line.offset_top = safe.y + 92
	_caption_line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption_line.add_theme_color_override("font_color", Color(UITheme.CREAM, 0.85))
	_caption_line.modulate.a = 0.0
	_root.add_child(_caption_line)

	_message = _shadow_label(28)
	_message.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_message.offset_left = -720
	_message.offset_right = 720
	_message.offset_top = -(safe.w + 290)
	_message.offset_bottom = -(safe.w + 200)
	_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_message.modulate.a = 0.0
	_root.add_child(_message)

	_prompt = _shadow_label(24)
	_prompt.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.offset_left = -720
	_prompt.offset_right = 720
	_prompt.offset_top = -(safe.w + 196)
	_prompt.offset_bottom = -(safe.w + 160)
	_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt.add_theme_color_override("font_color", UITheme.BRASS_HI)
	_root.add_child(_prompt)

	_back_btn = IconButton.make("back", 104)
	_place(_back_btn, Control.PRESET_BOTTOM_LEFT, Vector2(safe.x + 28, -(safe.w + 28 + 104)))
	_back_btn.pressed.connect(func() -> void: room.call("go_back"))

	_inv_panel = PanelContainer.new()
	var sb := UITheme.panel_box(0.82, 18)
	sb.set_content_margin_all(12)
	_inv_panel.add_theme_stylebox_override("panel", sb)
	_inv_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_inv_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_inv_panel.offset_bottom = -(safe.w + 22)
	_inv_panel.offset_top = -(safe.w + 22 + 140)
	_root.add_child(_inv_panel)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	_inv_panel.add_child(row)
	_inv_scroll = ScrollContainer.new()
	_inv_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_inv_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_inv_scroll.custom_minimum_size = Vector2(0, 116)
	row.add_child(_inv_scroll)
	_inv_box = HBoxContainer.new()
	_inv_box.add_theme_constant_override("separation", 10)
	_inv_scroll.add_child(_inv_box)
	_act_inspect = IconButton.make("inspect", 104)
	_act_inspect.pressed.connect(func() -> void: show_inspect(logic.selected))
	row.add_child(_act_inspect)
	_act_combine = IconButton.make("combine", 104)
	_act_combine.pressed.connect(_toggle_combine)
	row.add_child(_act_combine)


func _place(c: Control, preset: int, offset: Vector2) -> void:
	c.set_anchors_preset(preset)
	c.position = Vector2.ZERO
	_root.add_child(c)
	c.set_anchors_and_offsets_preset(preset)
	c.offset_left = offset.x
	c.offset_top = offset.y
	c.offset_right = offset.x + c.custom_minimum_size.x
	c.offset_bottom = offset.y + c.custom_minimum_size.y


func _shadow_label(sz: int) -> Label:
	var l := UITheme.label("", sz)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 8)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## Safe-area insets (notches, rounded corners, home indicator) in viewport units: x=left y=top z=right w=bottom.
func _safe_margins() -> Vector4:
	var vp := get_viewport().get_visible_rect().size
	var screen := Vector2(DisplayServer.window_get_size())
	var safe := DisplayServer.get_display_safe_area()
	if screen.x <= 0 or safe.size.x <= 0:
		return Vector4.ZERO
	var k := vp / screen
	var left := float(safe.position.x) * k.x
	var top := float(safe.position.y) * k.y
	var right := (screen.x - float(safe.end.x)) * k.x
	var bottom := (screen.y - float(safe.end.y)) * k.y
	return Vector4(maxf(0, left), maxf(0, top), maxf(0, right), maxf(0, bottom))


# ====================================================================== inventory
func _refresh_inventory() -> void:
	for c in _inv_box.get_children():
		c.queue_free()
	if logic.inventory.is_empty():
		var l := UITheme.label("ui.inventory_empty", 22, UITheme.MUTED)
		l.custom_minimum_size = Vector2(360, 112)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_inv_box.add_child(l)
	for id in logic.inventory:
		_inv_box.add_child(_slot(id))
	var n := maxi(1, logic.inventory.size())
	_inv_scroll.custom_minimum_size.x = minf(n * 122.0 - 10.0, INV_MAX_W) if not logic.inventory.is_empty() else 360.0
	var has_sel := logic.selected != ""
	_act_inspect.visible = has_sel
	_act_combine.visible = has_sel and logic.inventory.size() > 1 and logic.selected != "uv_lamp"
	_act_combine.active = _combine_mode
	_update_prompt()


func _slot(id: String) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(112, 112)
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
		b.add_theme_font_size_override("font_size", UITheme.size(16))
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


# ====================================================================== feedback
func message(text: String, seconds: float = 2.8) -> void:
	_message.text = text
	if _msg_tween and _msg_tween.is_valid():
		_msg_tween.kill()
	_msg_tween = create_tween()
	_msg_tween.tween_property(_message, "modulate:a", 1.0, 0.18)
	_msg_tween.tween_interval(seconds)
	_msg_tween.tween_property(_message, "modulate:a", 0.0, 0.5)


func caption(text: String, seconds: float = 3.5) -> void:
	_caption_line.text = text
	if _cap_tween and _cap_tween.is_valid():
		_cap_tween.kill()
	_cap_tween = create_tween()
	_cap_tween.tween_property(_caption_line, "modulate:a", 1.0, 0.25)
	_cap_tween.tween_interval(seconds)
	_cap_tween.tween_property(_caption_line, "modulate:a", 0.0, 0.6)


func set_view(id: String, is_root: bool, caption_key: String) -> void:
	var main := str(room.call("main_root")) if room.has_method("main_root") else ""
	_back_btn.visible = not is_root or id == "darkroom" or (main != "" and id != main)
	set_caption(caption_key)


func set_caption(caption_key: String) -> void:
	# the key itself: the label auto-translates, so a language switch in the pause menu updates it too
	_top_caption.text = caption_key


func set_busy(b: bool) -> void:
	_busy = b
	_inv_panel.visible = not b
	_hint_btn.visible = not b
	_pause_btn.visible = not b
	_back_btn.visible = not b and _back_btn.visible
	_prompt.visible = not b
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


func _process(_delta: float) -> void:
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


func _center_panel(o: Control, min_size: Vector2) -> VBoxContainer:
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	o.add_child(center)
	var p := PanelContainer.new()
	p.custom_minimum_size = min_size
	center.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 20)
	p.add_child(v)
	return v


# ====================================================================== hints
func show_hint() -> void:
	_hint_btn.badge = ""
	var o := _open_overlay(0.55)
	var v := _center_panel(o, Vector2(980, 0))
	v.add_child(UITheme.title("ui.hint", 46))
	var lvl_label := UITheme.label("", 22, UITheme.MUTED)
	lvl_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(lvl_label)
	var text := UITheme.label("", 30)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.custom_minimum_size = Vector2(900, 120)
	v.add_child(text)
	var h := HBoxContainer.new()
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 16)
	var more := UITheme.button("ui.hint_more", 340)
	var close := UITheme.button("ui.close", 240)
	h.add_child(more)
	h.add_child(close)
	v.add_child(h)
	var show_next := func() -> void:
		var hint := GameState.next_hint()
		if hint.is_empty():
			return
		AudioManager.sfx("hint", -4.0)
		text.text = tr(hint["key"])
		lvl_label.text = tr("ui.hint_level") % int(hint["level"])
		more.disabled = int(hint["level"]) >= 3
	show_next.call()
	more.pressed.connect(show_next)
	close.pressed.connect(_close_overlay)


# ====================================================================== pause
func show_pause() -> void:
	var o := _open_overlay(0.6)
	var v := _center_panel(o, Vector2(620, 0))
	v.add_child(UITheme.title("ui.pause", 50))
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
		var c := CenterContainer.new()
		c.set_anchors_preset(Control.PRESET_FULL_RECT)
		o2.add_child(c)
		var sp := SettingsPanel.new()
		c.add_child(sp)
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
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 80
	h.offset_right = -80
	h.offset_top = 70
	h.offset_bottom = -70
	h.add_theme_constant_override("separation", 40)
	o.add_child(h)
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.custom_minimum_size = Vector2(880, 880)
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
	var desc_key := logic.item_desc_key(id)
	var d := UITheme.label(desc_key, 28)
	info.add_child(d)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
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


const NB_PAGES := 8


func _show_notebook(page: int) -> void:
	var l7 := logic as Lab7Logic # Leyla's notebook exists in Chapter 1 only
	if l7 == null:
		return
	var o := _open_overlay(0.82)
	var paper := _paper_panel(o)
	var v := paper.get_meta("vbox") as VBoxContainer
	var pg := clampi(page, 0, NB_PAGES - 1)
	var head := UITheme.label(tr("ui.page") % [pg + 1, NB_PAGES], 22, Color("6b5a44"))
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
		cipher.add_child(ink_line)
		var glyphs := HBoxContainer.new()
		glyphs.alignment = BoxContainer.ALIGNMENT_CENTER
		glyphs.add_theme_constant_override("separation", 40)
		for gid in ["sun", "wave", "spiral", "delta"]:
			var tr_ := TextureRect.new()
			tr_.texture = load("res://assets/ui/glyphs/%s.png" % gid)
			tr_.custom_minimum_size = Vector2(130, 130)
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
	var nav := HBoxContainer.new()
	nav.alignment = BoxContainer.ALIGNMENT_CENTER
	nav.add_theme_constant_override("separation", 40)
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
	var bottom := CenterContainer.new()
	bottom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	bottom.offset_top = -130
	bottom.offset_bottom = -20
	bottom.grow_horizontal = Control.GROW_DIRECTION_BOTH
	o.add_child(bottom)
	bottom.add_child(nav)


func _paper_panel(o: Control) -> Control:
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.offset_bottom = -110
	o.add_child(center)
	var paper := PanelContainer.new()
	var sb := StyleBoxTexture.new()
	sb.texture = load("res://assets/textures/decals/notebook_page.jpg")
	sb.content_margin_left = 110
	sb.content_margin_right = 70
	sb.content_margin_top = 60
	sb.content_margin_bottom = 60
	paper.add_theme_stylebox_override("panel", sb)
	paper.custom_minimum_size = Vector2(1080, 800)
	center.add_child(paper)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 18)
	paper.add_child(v)
	paper.set_meta("vbox", v)
	return paper


func _hand_label(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", UITheme.hand_font())
	l.add_theme_font_size_override("font_size", UITheme.size(44))
	l.add_theme_color_override("font_color", Color("2b2118"))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(880, 0)
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
	photo.custom_minimum_size = Vector2(300, 370)
	photo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	photo.rotation = deg_to_rad(-3)
	h.add_child(photo)
	var back := _hand_label(tr("doc.photo"))
	back.custom_minimum_size = Vector2(520, 0)
	h.add_child(back)
	_close_button_bottom(o)


func _show_evidence() -> void:
	var o := _open_overlay(0.82)
	var v := _center_panel(o, Vector2(1300, 0))
	v.add_child(UITheme.title("obj.evidence", 44))
	var grid := HBoxContainer.new()
	grid.alignment = BoxContainer.ALIGNMENT_CENTER
	grid.add_theme_constant_override("separation", 14)
	for k in 8:
		var p := TextureRect.new()
		p.texture = load("res://assets/textures/decals/photo_%d.jpg" % k)
		p.custom_minimum_size = Vector2(130, 160)
		p.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		p.rotation = deg_to_rad(randf_range(-4, 4))
		grid.add_child(p)
	v.add_child(grid)
	var t := UITheme.label("doc.evidence", 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(_close_overlay)
	var c := CenterContainer.new()
	c.add_child(close)
	v.add_child(c)


## A document that is a picture (badge, index card): shown large on the dimmed screen.
func _show_picture(path: String, size: Vector2) -> void:
	var o := _open_overlay(0.85)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.offset_bottom = -110
	o.add_child(c)
	var t := TextureRect.new()
	var lp := DecalLoc.localized_path(path)
	t.texture = load(lp) if ResourceLoader.exists(lp) else null
	t.custom_minimum_size = size
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
		var safe := _safe_margins()
		_meter.set_anchors_preset(Control.PRESET_TOP_RIGHT)
		_meter.offset_right = -(safe.z + 28)
		_meter.offset_left = -(safe.z + 28 + 250)
		_meter.offset_top = safe.y + 130
		_meter.offset_bottom = safe.y + 230
		_root.add_child(_meter)
		var v := VBoxContainer.new()
		_meter.add_child(v)
		var t := UITheme.label("item.pocket_receiver.name", 20, UITheme.MUTED)
		t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t)
		var h := HBoxContainer.new()
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_theme_constant_override("separation", 8)
		v.add_child(h)
		for i in 5:
			var bar := ColorRect.new()
			bar.custom_minimum_size = Vector2(30, 14 + 9 * i)
			bar.size_flags_vertical = Control.SIZE_SHRINK_END
			h.add_child(bar)
			_meter_bars.append(bar)
	_meter.visible = level >= 0
	for i in 5:
		_meter_bars[i].color = Color("7dff9a") if i < level else Color(1, 1, 1, 0.12)


func _close_button_bottom(o: Control) -> void:
	var bottom := CenterContainer.new()
	bottom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	bottom.offset_top = -130
	bottom.offset_bottom = -20
	bottom.grow_horizontal = Control.GROW_DIRECTION_BOTH
	o.add_child(bottom)
	var close := IconButton.make("close", 96)
	close.pressed.connect(_close_overlay)
	bottom.add_child(close)


# ====================================================================== intro
func play_intro() -> void:
	set_busy(true)
	var o := ColorRect.new()
	o.color = Color(0.03, 0.035, 0.04, 1.0)
	o.set_anchors_preset(Control.PRESET_FULL_RECT)
	o.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(o)
	var lbl := UITheme.title("", 44, false)
	lbl.add_theme_color_override("font_color", UITheme.CREAM)
	lbl.set_anchors_preset(Control.PRESET_FULL_RECT)
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.offset_left = 220
	lbl.offset_right = -220
	o.add_child(lbl)
	var tap := UITheme.label("ui.tap_to_continue", 22, UITheme.MUTED)
	tap.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	tap.offset_top = -110
	tap.offset_bottom = -60
	tap.offset_left = -400
	tap.offset_right = 400
	tap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
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
	room.call("play_opening_camera")
	if not own_impact:
		AudioManager.sfx("door_slam")
		AudioManager.sfx("maglock_release", -4.0, 0.8)
		AudioManager.haptic(120)
	var fade := create_tween()
	fade.tween_property(o, "color:a", 0.0, 1.6)
	await fade.finished
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
	var v := _center_panel(o, Vector2(maxf(1000.0, 420.0 * options.size() + 120.0), 0))
	var t := UITheme.label(logic.choice_prompt_key(), 32)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var h := HBoxContainer.new()
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 24)
	for opt: Array in options:
		var b := UITheme.button(opt[1], 380)
		b.pressed.connect(func() -> void:
			_close_overlay()
			logic.choose_ending(opt[0]))
		h.add_child(b)
	v.add_child(h)


func show_chapter_complete() -> void:
	set_busy(true)
	AudioManager.music("stinger_chapter_complete", 1.0)
	var o := _open_overlay(0.0)
	o.set_meta("locked", true)
	var tw := create_tween()
	tw.tween_property(o, "color:a", 0.9, 1.4)
	var v := _center_panel(o, Vector2(1200, 0))
	v.add_child(UITheme.label("ui.chapter_complete", 28, UITheme.MUTED))
	v.get_child(0).set("horizontal_alignment", HORIZONTAL_ALIGNMENT_CENTER)
	v.add_child(UITheme.title("chapter.%s.title" % GameState.chapter_id, 60))
	for line in logic.epilogue_keys():
		var l := UITheme.label(line, 26)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(l)
	var stats := HBoxContainer.new()
	stats.alignment = BoxContainer.ALIGNMENT_CENTER
	stats.add_theme_constant_override("separation", 36)
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
		col.custom_minimum_size = Vector2(230, 0) # labels wrap; without a width they collapse to one letter per line
		var a := UITheme.label(pair[0], 22, UITheme.MUTED)
		a.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var b := UITheme.label(pair[1], 34, UITheme.BRASS_HI)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(a)
		col.add_child(b)
		stats.add_child(col)
	v.add_child(stats)
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
			var cg := CenterContainer.new()
			cg.add_child(go)
			v.add_child(cg)
		else:
			var soon := UITheme.label("ui.to_be_continued" if not Chapters.get_chapter(next_id).get("released", false) else "ui.unlock_desc", 24, UITheme.MUTED)
			soon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(soon)
	var menu := UITheme.button("ui.main_menu", 420)
	menu.pressed.connect(func() -> void:
		AudioManager.stop_all_ambience()
		SceneManager.goto("res://src/ui/main_menu.tscn"))
	var c := CenterContainer.new()
	c.add_child(menu)
	v.add_child(c)
