extends Control
## Main menu: the 3D gear box backdrop (MenuBackground), the logo with a warm glow, Continue / New Game / Chapters /
## Settings as serif text items (MenuItem), store notices. A vignette and a dark gradient behind the column keep the
## text readable (menu_atmosphere.gdshader). The logo fades in, then the items one after another (none of that with
## Settings "reduce_motion"). Text and touch targets follow UITheme's screen-based sizing; the logo gives way when
## the items need the height.

var _menu: VBoxContainer
var _left: VBoxContainer
var _panel_host: Control # dialogs (settings, chapters, confirm) are centred inside the safe area in here
var _dim: ColorRect # darkens the menu behind an open panel
var _logo: TextureRect
var _gap: Control
var _ver: Label
var _bg: MenuBackground
var _atmo: ColorRect # vignette, column gradient and logo glow (canvas shader)
var _cover: ColorRect # black over the 3D at first, faded out by the entrance

const LOGO_SIZE := Vector2(700, 525)
const MENU_SEP := 6.0
const VER_GAP := 10.0 # between the version line and the column above it
const LOGO_GAP := 6.0

var _safe_seen := Vector4.ZERO
var _safe_poll := 0.0


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
	_bg = MenuBackground.new()
	vp.add_child(_bg)
	_cover = ColorRect.new()
	_cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cover.color = Color(0, 0, 0, 0)
	_cover.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_cover)
	_atmo = ColorRect.new()
	_atmo.set_anchors_preset(Control.PRESET_FULL_RECT)
	_atmo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://src/ui/menu_atmosphere.gdshader")
	sm.set_shader_parameter("glow", 1.0)
	_atmo.material = sm
	add_child(_atmo)
	_left = VBoxContainer.new()
	_left.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	_left.alignment = BoxContainer.ALIGNMENT_CENTER
	_left.add_theme_constant_override("separation", 0)
	add_child(_left)
	# The logo artwork carries the subtitle, so there is one image per language (tools/ui/make_logo_variants.py).
	_logo = TextureRect.new()
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_logo.item_rect_changed.connect(_update_atmosphere)
	_left.add_child(_logo)
	_update_logo()
	_gap = Control.new()
	_gap.custom_minimum_size = Vector2(0, LOGO_GAP) # the first item's row adds its own air above the text
	_left.add_child(_gap)
	_menu = VBoxContainer.new()
	_menu.add_theme_constant_override("separation", int(MENU_SEP))
	_left.add_child(_menu)
	# the small-caps line under the menu (where a title screen puts its copyright line); open panels cover it
	_ver = UITheme.label(_version_text(), 20, UITheme.MUTED)
	_ver.add_theme_font_override("font", _caps_font())
	_ver.uppercase = true
	_ver.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_ver.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	_ver.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_ver)
	_dim = ColorRect.new()
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.color = Color(0, 0, 0, 0.62)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim.visible = false
	add_child(_dim)
	_panel_host = Control.new()
	_panel_host.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_panel_host)
	_build_menu()
	_entrance()
	CrashGuard.mark("menu")
	if CrashGuard.switched_to_safe:
		CrashGuard.switched_to_safe = false
		SceneManager.toast(tr("msg.safe_graphics_on"), 6.0)
	AudioManager.music("music_menu", 3.0)
	Loc.language_changed.connect(_on_language_changed)
	Settings.changed.connect(_on_setting_changed)
	get_viewport().size_changed.connect(_layout)


func _version_text() -> String:
	var ver: String = tr("ui.version") % ProjectSettings.get_setting("application/config/version", "0.1.0")
	if Premium.tester_tools():
		# a tester's screenshot then says which renderer the phone ran (metal / vulkan / opengl3, mobile / gl_compatibility)
		ver += "  ·  %s %s" % [RenderingServer.get_current_rendering_driver_name(), RenderingServer.get_current_rendering_method()]
		if CrashGuard.previous != "":
			ver += "  ·  last stop: " + CrashGuard.previous # where the previous session ended without a clean pause
		if CrashGuard.safe_level() > 0:
			ver += "  ·  safe %d" % CrashGuard.safe_level()
	return ver


## Display serif with a little letter spacing, for the version line (shown in capitals).
func _caps_font() -> Font:
	var fv := FontVariation.new()
	fv.base_font = UITheme.display_font(false)
	fv.spacing_glyph = 2
	return fv


## The logo fades in (with its glow), the 3D scene comes up out of black, then the items rise in one after another
## (80 ms apart, all done in about a second). With Settings "reduce_motion" everything is simply there.
func _entrance() -> void:
	if bool(Settings.get_value("reduce_motion")):
		return
	var sm := _atmo.material as ShaderMaterial
	_cover.color.a = 1.0
	_logo.modulate.a = 0.0
	_ver.modulate.a = 0.0
	sm.set_shader_parameter("glow", 0.0)
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_cover, "color:a", 0.0, 0.9).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_logo, "modulate:a", 1.0, 0.5).set_delay(0.05).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_method(func(v: float) -> void: sm.set_shader_parameter("glow", v), 0.0, 1.0, 0.7).set_delay(0.05)
	var i := 0
	for c in _menu.get_children():
		(c as MenuItem).appear(0.3 + 0.08 * i)
		i += 1
	tw.tween_property(_ver, "modulate:a", 1.0, 0.4).set_delay(0.3 + 0.08 * i)


func _on_language_changed(_code: String) -> void:
	_update_logo()
	_ver.text = _version_text()
	_build_menu()


func _on_setting_changed(key: String) -> void:
	if key == "text_scale":
		theme = UITheme.build()
		UITheme.rescale(self)
		_build_menu()


func _update_logo() -> void:
	var path := "res://assets/ui/logo/logo_%s.png" % Loc.current()
	if not ResourceLoader.exists(path):
		path = "res://assets/ui/logo/logo_en.png"
	_logo.texture = load(path)
	_logo.tooltip_text = tr("game.title") + " — " + tr("game.subtitle")


func _process(delta: float) -> void:
	# a 180° turn (sensor_landscape) moves the camera cutout to the other side without resizing the window
	_safe_poll += delta
	if _safe_poll >= 0.5:
		_safe_poll = 0.0
		if UITheme.safe_margins() != _safe_seen:
			_layout()


## Places the menu column inside the safe area, sizes the logo to the height the items leave, puts the version
## line under the column, and frames the 3D box in the space right of the column.
func _layout() -> void:
	var safe := UITheme.safe_margins()
	_safe_seen = safe
	var u := UITheme.usable_rect()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	_left.offset_left = maxf(100.0, safe.x + 60.0)
	_left.offset_right = _left.offset_left + maxf(800.0, 520.0 * UITheme.wscale() + 40.0)
	_ver.offset_left = _left.offset_left + MenuItem.INDENT
	_ver.offset_right = _ver.offset_left
	_ver.offset_bottom = -(safe.w + 14.0)
	_ver.offset_top = _ver.offset_bottom
	var col_bottom := minf(u.end.y, canvas.y - safe.w - 14.0 - _ver.get_combined_minimum_size().y - VER_GAP)
	_left.offset_top = u.position.y
	_left.offset_bottom = -(canvas.y - col_bottom)
	var avail := col_bottom - u.position.y
	var n := _menu.get_child_count()
	# rows: a touch target at least, and airy enough for display type (1.5 em: on a phone the logo keeps its room)
	var btn_h := maxf(UITheme.target(78), roundf(UITheme.size(MenuItem.SIZE_NORMAL) * 1.5))
	for b: Control in _menu.get_children():
		b.custom_minimum_size.y = btn_h
		btn_h = maxf(btn_h, b.get_combined_minimum_size().y)
	var buttons := n * btn_h + maxf(0, n - 1) * MENU_SEP
	var logo_h := minf(avail - buttons - LOGO_GAP, LOGO_SIZE.y)
	# a short screen with large text: the logo gives way first, then the items' extra height (never below 7 mm)
	_logo.visible = logo_h >= 150.0
	_gap.visible = _logo.visible
	if _logo.visible:
		_logo.custom_minimum_size = Vector2(logo_h * LOGO_SIZE.x / LOGO_SIZE.y, logo_h)
	elif buttons > avail:
		var fit_h := maxf((avail - maxf(0, n - 1) * MENU_SEP) / maxf(1, n), UITheme.px_for_mm(7.0))
		for b: Control in _menu.get_children():
			b.custom_minimum_size.y = fit_h
	# the hero box: centred in the free space right of the column, about 70 % of its width
	var free_l := _left.offset_right
	var free_r := canvas.x - safe.z
	_bg.set_frame(Vector2((free_l + free_r) * 0.5 / canvas.x, 0.54), (free_r - free_l) / canvas.x * 0.72)
	_update_atmosphere()


## Points the overlay shader at the current layout: vignette on the box, gradient behind the column, glow behind
## the logo.
func _update_atmosphere() -> void:
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	if _atmo == null or canvas.x <= 0.0:
		return
	var sm := _atmo.material as ShaderMaterial
	var free_l := _left.offset_right
	var free_r := canvas.x - UITheme.safe_margins().z
	sm.set_shader_parameter("canvas", canvas)
	sm.set_shader_parameter("focus", Vector2((free_l + free_r) * 0.5 / canvas.x, 0.54))
	sm.set_shader_parameter("column_end", free_l / canvas.x + 0.05)
	var r := _logo.get_global_rect() if _logo.visible else Rect2(-canvas, Vector2.ONE)
	sm.set_shader_parameter("glow_center", r.get_center() / canvas)
	sm.set_shader_parameter("glow_radius", r.size * 0.62 / canvas)


func _build_menu() -> void:
	for c in _menu.get_children():
		_menu.remove_child(c)
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
	if not _mobile() and not OS.has_feature("web"):
		_add("ui.quit", func() -> void: get_tree().quit())
	_layout()


## Phones and tablets have no Quit item (the OS closes apps); neither has QA's phone emulation.
static func _mobile() -> bool:
	return OS.has_feature("mobile") or bool(Settings.emulate.get("mobile", false))


func _add(key: String, cb: Callable) -> void:
	# the first item is the most prominent one: Continue, or New Game when there is nothing to continue
	var b := MenuItem.new(key, _menu.get_child_count() == 0 and key in ["ui.continue", "ui.new_game"])
	b.pressed.connect(cb)
	_menu.add_child(b)


## Android back / Escape: closes an open panel, otherwise asks before quitting.
func handle_back() -> void:
	if _dim.visible:
		_clear_panel()
	else:
		_confirm("ui.quit_confirm", func() -> void: get_tree().quit())


func _new_game() -> void:
	SaveSystem.delete_game()
	if GameState.start_new("ch1"):
		_play("ch1")


func _play(chapter_id: String) -> void:
	if not playable(chapter_id):
		_show_chapters() # a save of a chapter this build cannot load (no scene yet, or unreleased): pick another
		return
	AudioManager.stop_music(1.5)
	var ch := Chapters.get_chapter(chapter_id)
	SceneManager.goto(ch["scene"])


## A chapter whose scene this build can load: it is released and has a scene. Continue on any other save (an
## unreleased chapter, such as Chapter 4 while its scene is built) opens the chapter list instead of loading "".
static func playable(chapter_id: String) -> bool:
	var ch := Chapters.get_chapter(chapter_id)
	var scene := str(ch.get("scene", ""))
	return bool(ch.get("released", false)) and scene != "" and ResourceLoader.exists(scene)


func _clear_panel() -> void:
	for c in _panel_host.get_children():
		c.queue_free()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim.visible = false


func _open_panel() -> void:
	_clear_panel()
	_panel_host.mouse_filter = Control.MOUSE_FILTER_STOP
	_dim.visible = true


func _show_settings() -> void:
	_open_panel()
	var sp := SettingsPanel.new()
	UITheme.safe_center(_panel_host).add_child(sp)
	sp.closed.connect(_clear_panel)


func _show_chapters() -> void:
	_open_panel()
	var d := UITheme.dialog(_panel_host, 1200, "ui.chapters", 50)
	var v: VBoxContainer = d["body"]
	v.add_theme_constant_override("separation", 14)
	for ch: Dictionary in Chapters.LIST:
		var row := HFlowContainer.new() # the button wraps under the title when the text is large
		row.add_theme_constant_override("h_separation", 18)
		row.add_theme_constant_override("v_separation", 8)
		row.alignment = FlowContainer.ALIGNMENT_END
		var text := VBoxContainer.new()
		text.add_theme_constant_override("separation", 0)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var num := UITheme.label(tr("chapter.label") % int(ch["number"]), 22, UITheme.MUTED)
		num.add_theme_font_override("font", UITheme.caps_font(false, 1))
		num.autowrap_mode = TextServer.AUTOWRAP_OFF
		text.add_child(num)
		var name := UITheme.label(ch["title"], 30)
		name.add_theme_font_override("font", UITheme.display_font(true))
		text.add_child(name)
		row.add_child(text)
		var state_key := "ui.coming_soon"
		var can := Premium.can_play(ch["id"])
		if can:
			state_key = "ui.completed" if GameState.is_chapter_completed(ch["id"]) else ("ui.free" if Chapters.is_free(ch["id"]) else "ui.play")
		# a released paid chapter the player does not own yet: "Unlock" opens the purchase screen when this build
		# has a store (release builds keep "Coming soon" while real payments are off)
		var buyable := not can and bool(ch.get("released", false)) and not Chapters.is_free(ch["id"]) and Premium.store_open()
		var b := UITheme.button("ui.play" if can else ("ui.buy" if buyable else state_key), 300)
		b.disabled = not can and not buyable
		if can:
			var id: String = ch["id"]
			b.pressed.connect(func() -> void:
				if GameState.saved_chapter() == id and GameState.continue_saved():
					_play(id)
				elif GameState.start_new(id):
					_play(id))
		elif buyable:
			b.pressed.connect(_show_purchase)
		row.add_child(b)
		v.add_child(row)
	var unlock := UITheme.label("ui.unlock_desc", 22, UITheme.MUTED)
	unlock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(unlock)
	var close := UITheme.button("ui.close", 260)
	close.pressed.connect(_clear_panel)
	(d["footer"] as Control).add_child(close)


## The purchase screen over the chapter list; closing it shows the list again (now with Play if it was bought).
func _show_purchase() -> void:
	_open_panel()
	var p := PurchasePanel.open(_panel_host)
	p.closed.connect(_show_chapters)


func _confirm(key: String, yes: Callable) -> void:
	_open_panel()
	var d := UITheme.dialog(_panel_host, 900)
	var l := UITheme.label(key, 30)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	(d["body"] as Control).add_child(l)
	var h: HFlowContainer = d["footer"]
	h.add_theme_constant_override("h_separation", 20)
	var y := UITheme.button("ui.yes", 240)
	y.pressed.connect(func() -> void:
		_clear_panel()
		yes.call())
	var n := UITheme.button("ui.no", 240)
	n.pressed.connect(_clear_panel)
	h.add_child(y)
	h.add_child(n)
