class_name CreditsScene
extends Control
## The end credits: slow, centred serif text rising over black, in the same style as the main menu (docs/CREDITS.md).
## Reusable: CreditsScene.play(after_scene) loads it (after the Chapter 4 finale; QA and Settings can too); when it
## ends or is skipped, it hands over to `after_scene` (the main menu by default) through SceneManager.goto, once.
## A tap or Back skips; with Settings "reduce_motion" the sections fade in and out one at a time instead of rising.
## The content is CreditsData: headings in the player's language, the names in Latin script.

const SCENE := "res://src/ui/credits_scene.tscn"
const MENU := "res://src/ui/main_menu.tscn"
const RISE_S := 46.0 # the whole rise, from the first line entering to the last line centred
const HOLD_S := 3.5 # the last line stays centred this long
const OUT_S := 1.6 # then the fade to black
const SKIP_FADE_S := 0.4
const PAGE_IN_S := 1.6
const PAGE_HOLD_S := 3.2
const PAGE_OUT_S := 1.2
const COL_W := 1100.0

## Where the credits hand over to (set by play()).
static var after_scene := MENU

## Replaced by tests to count the hand-over (default SceneManager.goto).
var goto_fn := Callable()

signal finished

var _col: VBoxContainer
var _clip: Control
var _hint: Label
var _veil: ColorRect
var _pages: Array[Control] = []
var _t := 0.0
var _y_start := 0.0
var _y_end := 0.0
var _rise := RISE_S
var _skip_t := -1.0
var _done := false
var _still := false
var _last: Control
var _measured := true


## Loads the credits; they return to `after` (a scene path) when they end.
static func play(after: String = MENU) -> void:
	after_scene = after
	SceneManager.goto(SCENE)


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_still = bool(Settings.get_value("reduce_motion"))
	var bg := ColorRect.new()
	bg.color = Color(0.016, 0.018, 0.022)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var glow := ColorRect.new() # a faint warm light behind the middle: the text never floats in flat black
	glow.set_anchors_preset(Control.PRESET_FULL_RECT)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://src/ui/menu_atmosphere.gdshader")
	sm.set_shader_parameter("column_dark", 0.0)
	sm.set_shader_parameter("glow", 1.0)
	sm.set_shader_parameter("focus", Vector2(0.5, 0.5))
	sm.set_shader_parameter("glow_center", Vector2(0.5, 0.5))
	sm.set_shader_parameter("glow_radius", Vector2(0.34, 0.42))
	sm.set_shader_parameter("vignette_inner", 0.45)
	sm.set_shader_parameter("canvas", UITheme.metrics()["canvas"])
	glow.material = sm
	add_child(glow)
	_clip = Control.new()
	_clip.set_anchors_preset(Control.PRESET_FULL_RECT)
	_clip.clip_contents = true
	_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_clip)
	_hint = UITheme.label("ui.tap_to_skip", 22, UITheme.MUTED)
	_hint.add_theme_font_override("font", UITheme.caps_font(false, 2))
	_hint.uppercase = true
	_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.autowrap_mode = TextServer.AUTOWRAP_OFF
	_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint.modulate.a = 0.0
	add_child(_hint)
	_veil = ColorRect.new()
	_veil.color = Color(0, 0, 0, 0)
	_veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	_veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_veil)
	_build()
	get_viewport().size_changed.connect(_build)
	AudioManager.music("music_menu", 3.0)
	CrashGuard.mark("credits")


func _block_label(b: Dictionary) -> Control:
	var text := str(b["text"])
	var l: Label
	match int(b["kind"]):
		CreditsData.Kind.TITLE:
			l = UITheme.title(text, 84, true)
		CreditsData.Kind.SUBTITLE:
			l = UITheme.label(text, 32, UITheme.BRASS)
			l.add_theme_font_override("font", UITheme.caps_font(false, 3))
			l.uppercase = true
		CreditsData.Kind.HEADING:
			l = UITheme.label(text, 24, UITheme.MUTED)
			l.add_theme_font_override("font", UITheme.caps_font(false, 3))
			l.uppercase = true
		CreditsData.Kind.NAME:
			l = UITheme.title(text, 54, false)
			l.add_theme_color_override("font_color", UITheme.CREAM)
		CreditsData.Kind.LINE:
			l = UITheme.title(text, 34, false)
			l.add_theme_color_override("font_color", UITheme.CREAM)
		CreditsData.Kind.THANKS:
			l = UITheme.title(text, 58, true)
		_:
			var g := Control.new()
			g.custom_minimum_size = Vector2(0, 90.0 * UITheme.wscale())
			g.mouse_filter = Control.MOUSE_FILTER_IGNORE
			return g
	l.add_theme_constant_override("line_spacing", 4)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


func _build() -> void:
	for c in _clip.get_children():
		_clip.remove_child(c)
		c.queue_free()
	_pages.clear()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var w := minf(COL_W * UITheme.wscale(), canvas.x - UITheme.safe_margins().x - UITheme.safe_margins().z - 80.0)
	var blocks := CreditsData.blocks()
	_last = null
	_measured = false
	if _still:
		# paged: each section (blocks up to a gap) is centred on its own and fades in and out
		var page: VBoxContainer = null
		for b in blocks:
			if int(b["kind"]) == CreditsData.Kind.GAP:
				page = null
				continue
			if page == null:
				page = _new_column(w, canvas)
				_clip.add_child(page)
				_pages.append(page)
			page.add_child(_block_label(b))
		for p in _pages:
			p.modulate.a = 0.0
		return
	_col = _new_column(w, canvas)
	_clip.add_child(_col)
	for b in blocks:
		var l := _block_label(b)
		_col.add_child(l)
		_last = l
	_col.position.y = canvas.y


func _new_column(w: float, canvas: Vector2) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", int(14.0 * UITheme.wscale()))
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.size = Vector2(w, 0)
	v.custom_minimum_size.x = w
	v.position = Vector2((canvas.x - w) * 0.5, canvas.y)
	return v


## Once the labels have wrapped to the column (a frame after building): where the column starts and ends.
func _measure() -> void:
	if _col == null or not is_instance_valid(_last):
		return
	_measured = true
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	_y_start = canvas.y + 30.0
	# the last line ends up centred on the screen
	var last_mid := _last.position.y + _last.size.y * 0.5
	_y_end = canvas.y * 0.5 - last_mid
	_col.position.y = _y_start + (_y_end - _y_start) * clampf(_t / _rise, 0.0, 1.0)


func _process(delta: float) -> void:
	if _done:
		return
	if not _measured:
		_measure()
		return # the first frame only lays the text out; the credits start from here
	_t += delta
	if _skip_t >= 0.0:
		_skip_t += delta
		_veil.color.a = clampf(_skip_t / SKIP_FADE_S, 0.0, 1.0)
		if _skip_t >= SKIP_FADE_S:
			_finish()
		return
	_hint.modulate.a = clampf((_t - 3.0) / 1.0, 0.0, 1.0) * (1.0 - clampf((_t - 11.0) / 1.5, 0.0, 1.0)) * 0.9
	if _still:
		_step_pages()
		return
	if _col != null:
		var k := clampf(_t / _rise, 0.0, 1.0)
		_col.position.y = _y_start + (_y_end - _y_start) * k # constant speed: slow and even
		var over := _t - _rise - HOLD_S
		if over > 0.0:
			_veil.color.a = clampf(over / OUT_S, 0.0, 1.0)
			if over >= OUT_S:
				_finish()


func _step_pages() -> void:
	var per := PAGE_IN_S + PAGE_HOLD_S + PAGE_OUT_S
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	var i := int(_t / per)
	if i >= _pages.size():
		_finish()
		return
	var lt := _t - i * per
	var a := 1.0
	if lt < PAGE_IN_S:
		a = lt / PAGE_IN_S
	elif lt > PAGE_IN_S + PAGE_HOLD_S:
		a = 1.0 - (lt - PAGE_IN_S - PAGE_HOLD_S) / PAGE_OUT_S
	var p := _pages[i]
	p.modulate.a = clampf(a, 0.0, 1.0)
	p.position.y = (canvas.y - p.size.y) * 0.5


func _gui_input(event: InputEvent) -> void:
	if (event is InputEventMouseButton or event is InputEventScreenTouch) and event.pressed:
		skip()


## Android back / Escape (SceneManager calls the scene's handle_back()).
func handle_back() -> void:
	skip()


func skip() -> void:
	if _skip_t < 0.0 and not _done:
		_skip_t = 0.0


func _finish() -> void:
	if _done:
		return
	_done = true
	finished.emit()
	if goto_fn.is_valid():
		goto_fn.call(after_scene)
	else:
		SceneManager.goto(after_scene)
