extends Control
## Main menu: animated 3D background, Continue / New Game / Chapters / Settings, store notices.

var _menu: VBoxContainer
var _panel_host: CenterContainer


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.set_anchors_preset(Control.PRESET_FULL_RECT)
	svc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(svc)
	var vp := SubViewport.new()
	vp.own_world_3d = true
	svc.add_child(vp)
	vp.add_child(MenuBackground.new())
	var shade := ColorRect.new()
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0, 0, 0, 0.25)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	var left := VBoxContainer.new()
	left.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	left.offset_left = 120
	left.offset_right = 900
	left.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_theme_constant_override("separation", 16)
	add_child(left)
	var t := UITheme.title("game.title", 96)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	t.add_theme_constant_override("outline_size", 0)
	left.add_child(t)
	var rule := ColorRect.new()
	rule.color = Color(UITheme.BRASS, 0.8)
	rule.custom_minimum_size = Vector2(520, 2)
	rule.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	left.add_child(rule)
	var sub := UITheme.title("game.subtitle", 40, false)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	sub.add_theme_color_override("font_color", UITheme.CREAM)
	left.add_child(sub)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 40)
	left.add_child(gap)
	_menu = VBoxContainer.new()
	_menu.add_theme_constant_override("separation", 14)
	left.add_child(_menu)
	_panel_host = CenterContainer.new()
	_panel_host.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_panel_host)
	var ver := UITheme.label(tr("ui.version") % ProjectSettings.get_setting("application/config/version", "0.1.0"), 18, UITheme.MUTED)
	ver.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	ver.offset_left = -360
	ver.offset_top = -60
	ver.offset_right = -30
	ver.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(ver)
	_build_menu()
	AudioManager.music("music_menu", 3.0)
	Loc.language_changed.connect(func(_c: String) -> void: _build_menu())


func _build_menu() -> void:
	for c in _menu.get_children():
		c.queue_free()
	var saved := GameState.saved_chapter()
	if saved != "":
		_add("ui.continue", func() -> void:
			if GameState.continue_saved():
				_play(GameState.chapter_id))
	_add("ui.new_game", func() -> void:
		if saved != "":
			_confirm("ui.new_game_confirm", _new_game)
		else:
			_new_game())
	_add("ui.chapters", _show_chapters)
	_add("ui.settings", _show_settings)
	if not OS.has_feature("mobile") and not OS.has_feature("web"):
		_add("ui.quit", func() -> void: get_tree().quit())


func _add(key: String, cb: Callable) -> void:
	var b := UITheme.button(key, 520)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.pressed.connect(cb)
	_menu.add_child(b)


func _new_game() -> void:
	SaveSystem.delete_game()
	if GameState.start_new("ch1"):
		_play("ch1")


func _play(chapter_id: String) -> void:
	AudioManager.stop_music(1.5)
	var ch := Chapters.get_chapter(chapter_id)
	SceneManager.goto(ch["scene"])


func _clear_panel() -> void:
	for c in _panel_host.get_children():
		c.queue_free()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _show_settings() -> void:
	_clear_panel()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_STOP
	var sp := SettingsPanel.new()
	_panel_host.add_child(sp)
	sp.closed.connect(_clear_panel)


func _show_chapters() -> void:
	_clear_panel()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_STOP
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(1200, 0)
	_panel_host.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	p.add_child(v)
	v.add_child(UITheme.title("ui.chapters", 50))
	for ch: Dictionary in Chapters.LIST:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 18)
		var num := UITheme.label(tr("chapter.label") % int(ch["number"]), 24, UITheme.MUTED)
		num.custom_minimum_size = Vector2(170, 0)
		num.autowrap_mode = TextServer.AUTOWRAP_OFF
		row.add_child(num)
		var name := UITheme.label(ch["title"], 30)
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(name)
		var state_key := "ui.coming_soon"
		var can := Premium.can_play(ch["id"])
		if can:
			state_key = "ui.completed" if GameState.is_chapter_completed(ch["id"]) else ("ui.free" if Chapters.is_free(ch["id"]) else "ui.play")
		var b := UITheme.button(state_key if not can else "ui.play", 280)
		b.disabled = not can
		if can:
			var id: String = ch["id"]
			b.pressed.connect(func() -> void:
				if GameState.saved_chapter() == id and GameState.continue_saved():
					_play(id)
				elif GameState.start_new(id):
					_play(id))
		row.add_child(b)
		v.add_child(row)
	var unlock := UITheme.label("ui.unlock_desc", 22, UITheme.MUTED)
	unlock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(unlock)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(_clear_panel)
	var c := CenterContainer.new()
	c.add_child(close)
	v.add_child(c)


func _confirm(key: String, yes: Callable) -> void:
	_clear_panel()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_STOP
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(900, 0)
	_panel_host.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 24)
	p.add_child(v)
	var l := UITheme.label(key, 30)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(l)
	var h := HBoxContainer.new()
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 20)
	var y := UITheme.button("ui.yes", 240)
	y.pressed.connect(func() -> void:
		_clear_panel()
		yes.call())
	var n := UITheme.button("ui.no", 240)
	n.pressed.connect(_clear_panel)
	h.add_child(y)
	h.add_child(n)
	v.add_child(h)
