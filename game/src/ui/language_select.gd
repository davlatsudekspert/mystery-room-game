extends Control
## First launch: choose EN → RU → UZ. The same dark desk and gear box as the main menu behind the logo, the title
## with a soft gold shimmer, the prompt in all three languages, and the three languages as serif items with the
## menu's gold rule (MenuItem). The phone's own language is pre-highlighted (bold, its rule shown). Each row is a
## touch target of at least 9 mm. The entrance fades the backdrop in, then the logo, then the names one after another
## (none of that with Settings "reduce_motion").

const LOGO_SIZE := Vector2(700, 525)
const PROMPTS := {"en": "Choose your language", "ru": "Выберите язык", "uz": "Tilni tanlang"}
const SEP := 6.0
const LOGO_GAP := 6.0

var _bg: MenuBackground
var _left: VBoxContainer
var _logo: TextureRect
var _prompt: VBoxContainer
var _rows: VBoxContainer
var _cover: ColorRect
var _atmo: ColorRect
var _detected := "en"
## QA: pretend the phone's language is this one (the picker pre-highlights it).
var detected_override := ""
var _chosen := false
var _t := 0.0
var _safe_seen := Vector4.ZERO
var _safe_poll := 0.0
var _still := false


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_still = bool(Settings.get_value("reduce_motion"))
	_detected = detected_override if detected_override != "" else Loc.detect_device_language()
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
	_logo = TextureRect.new()
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_logo.item_rect_changed.connect(_update_atmosphere)
	var shim := ShaderMaterial.new()
	shim.shader = load("res://src/ui/language_shimmer.gdshader")
	_logo.material = shim
	_logo.texture = _logo_texture()
	_logo.tooltip_text = "MYSTERY ROOM"
	_left.add_child(_logo)
	var indent := MarginContainer.new() # the prompt lines start where the items' text does
	indent.add_theme_constant_override("margin_left", int(MenuItem.INDENT))
	indent.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_left.add_child(indent)
	_prompt = VBoxContainer.new()
	_prompt.add_theme_constant_override("separation", 0)
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	indent.add_child(_prompt)
	# the prompt in all three languages (EN → RU → UZ), small capitals, aligned with the items' text
	for code in Loc.SUPPORTED:
		var l := UITheme.label(PROMPTS[code], 24, UITheme.CREAM if code == _detected else UITheme.MUTED)
		l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		l.add_theme_font_override("font", UITheme.caps_font(false, 2))
		l.uppercase = true
		l.autowrap_mode = TextServer.AUTOWRAP_OFF
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_prompt.add_child(l)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 14)
	gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt.add_child(gap)
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", int(SEP))
	_left.add_child(_rows)
	for code in Loc.SUPPORTED:
		var b := MenuItem.new(Loc.NATIVE_NAMES[code], code == _detected)
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.pressed.connect(_choose.bind(code))
		_rows.add_child(b)
	CrashGuard.mark("language")
	_entrance()
	get_viewport().size_changed.connect(_layout)
	_layout()


func _logo_texture() -> Texture2D:
	var path := "res://assets/ui/logo/logo_%s.png" % _detected
	if not ResourceLoader.exists(path):
		path = "res://assets/ui/logo/logo_en.png"
	return load(path)


func _choose(code: String) -> void:
	if _chosen:
		return
	_chosen = true
	Loc.choose(code)
	SceneManager.goto("res://src/ui/main_menu.tscn")


func _entrance() -> void:
	if _still:
		return
	var sm := _atmo.material as ShaderMaterial
	_cover.color.a = 1.0
	_logo.modulate.a = 0.0
	sm.set_shader_parameter("glow", 0.0)
	for l in _prompt.get_children():
		(l as Control).modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_cover, "color:a", 0.0, 0.9).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_logo, "modulate:a", 1.0, 0.7).set_delay(0.15).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_method(func(v: float) -> void: sm.set_shader_parameter("glow", v), 0.0, 1.0, 0.8).set_delay(0.15)
	var i := 0
	for l in _prompt.get_children():
		tw.tween_property(l, "modulate:a", 1.0, 0.5).set_delay(0.55 + 0.1 * i).set_trans(Tween.TRANS_SINE)
		i += 1
	i = 0
	for c in _rows.get_children():
		(c as MenuItem).appear(0.95 + 0.12 * i, 0.5) # the three names fade up one after another
		i += 1


func _process(delta: float) -> void:
	_t += delta
	if not _still:
		(_logo.material as ShaderMaterial).set_shader_parameter("t", _t)
	_safe_poll += delta
	if _safe_poll >= 0.5:
		_safe_poll = 0.0
		if UITheme.safe_margins() != _safe_seen:
			_layout()


## The column inside the safe area (as the main menu's), the logo as large as the height allows, the box framed
## in the free space to its right.
func _layout() -> void:
	var safe := UITheme.safe_margins()
	_safe_seen = safe
	var u := UITheme.usable_rect()
	var canvas: Vector2 = UITheme.metrics()["canvas"]
	_left.offset_left = maxf(100.0, safe.x + 60.0)
	_left.offset_right = _left.offset_left + maxf(800.0, 520.0 * UITheme.wscale() + 40.0)
	_left.offset_top = u.position.y
	_left.offset_bottom = -(canvas.y - u.end.y)
	var avail := u.end.y - u.position.y
	# rows: at least a 9 mm touch target, airy enough for display type
	var row_h := maxf(UITheme.target(96), roundf(UITheme.size(MenuItem.SIZE_NORMAL) * 1.5))
	for b: Control in _rows.get_children():
		b.custom_minimum_size.y = row_h
		row_h = maxf(row_h, b.get_combined_minimum_size().y)
	var rows_h := 3.0 * row_h + 2.0 * SEP
	var prompt_h := _prompt.get_combined_minimum_size().y
	var logo_h := minf(avail - rows_h - prompt_h - LOGO_GAP, LOGO_SIZE.y)
	_logo.visible = logo_h >= 150.0
	if _logo.visible:
		_logo.custom_minimum_size = Vector2(logo_h * LOGO_SIZE.x / LOGO_SIZE.y, logo_h)
	var free_l := _left.offset_right
	var free_r := canvas.x - safe.z
	_bg.set_frame(Vector2((free_l + free_r) * 0.5 / canvas.x, 0.54), (free_r - free_l) / canvas.x * 0.72)
	_update_atmosphere()


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
