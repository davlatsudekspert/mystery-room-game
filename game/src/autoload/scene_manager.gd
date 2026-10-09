extends Node
## Fade transitions between scenes and a global toast line (save feedback, notices).

signal scene_changed(path: String)

var _layer: CanvasLayer
var _fade: ColorRect
var _toast: Label
var _loading: Label
var _busy := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_layer = CanvasLayer.new()
	_layer.layer = 100
	add_child(_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0.055, 0.059, 0.071, 0.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_fade)
	_loading = Label.new()
	_loading.text = "ui.loading"
	_loading.set_anchors_preset(Control.PRESET_FULL_RECT)
	_loading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_loading.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_loading.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_loading.add_theme_color_override("font_color", Color("9d9482"))
	_loading.visible = false
	_layer.add_child(_loading)
	_toast = Label.new()
	_toast.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_toast.offset_top = 36
	_toast.offset_left = -400
	_toast.offset_right = 400
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_toast.modulate.a = 0.0
	_toast.add_theme_color_override("font_color", Color("EDE3CF"))
	_toast.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_toast.add_theme_constant_override("outline_size", 6)
	_toast.add_theme_font_size_override("font_size", 26)
	_layer.add_child(_toast)
	Settings.changed.connect(func(key: String) -> void:
		if key == "safe_graphics" and bool(Settings.get_value(key)):
			simplify_graphics(get_tree().current_scene, CrashGuard.MAX_LEVEL)) # off: from the next scene on


## Android back button/gesture (with application/config/quit_on_go_back off) and Escape on desktop go to
## the current scene's handle_back(); a scene without one ignores it, so "back" never quits by accident.
func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_dispatch_back()
	elif what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST:
		CrashGuard.paused()
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		CrashGuard.resumed()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and (event as InputEventKey).keycode == KEY_ESCAPE:
		_dispatch_back()
		get_viewport().set_input_as_handled()


func _dispatch_back() -> void:
	if _busy:
		return
	var scene := get_tree().current_scene
	if scene != null and scene.has_method("handle_back"):
		scene.call("handle_back")


func goto(path: String, fade_time: float = 0.45) -> void:
	if _busy:
		return
	_busy = true
	_fade.mouse_filter = Control.MOUSE_FILTER_STOP
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, fade_time)
	await tw.finished
	# Loading a room and drawing its first frames (a phone compiles the room's shaders on its first run) can take
	# seconds: say so on the black screen, and keep saying it until the new scene's first frames are drawn.
	_loading.add_theme_font_size_override("font_size", UITheme.size(28))
	_loading.visible = true
	await _frames_drawn(1)
	var stage := "load:" + path.get_file().get_basename()
	CrashGuard.mark(stage)
	get_tree().paused = false
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	# scenes that are not rooms: loaded and built (rooms mark "draw:" themselves in room_ready, before their
	# first frame is drawn, which happens before this await returns)
	if CrashGuard.stage() == stage:
		CrashGuard.mark("draw:" + path.get_file().get_basename())
	await get_tree().process_frame
	scene_changed.emit(path)
	await _frames_drawn(3)
	_loading.visible = false
	# the first seconds of a room (reflection probe capture, first shadow maps) still count as loading
	get_tree().create_timer(6.0).timeout.connect(func() -> void:
		if CrashGuard.stage() == "draw:" + path.get_file().get_basename():
			CrashGuard.mark("play:" + path.get_file().get_basename()))
	var tw2 := create_tween()
	tw2.tween_property(_fade, "color:a", 0.0, fade_time)
	await tw2.finished
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_busy = false


## Every room calls this at the end of its _ready. The scene change happens at the end of a frame and that
## frame is already drawn with the new room, so the safe level must be applied here, before the first draw.
func room_ready(room: Node) -> void:
	CrashGuard.mark("draw:" + str(room.scene_file_path.get_file().get_basename()))
	var level := CrashGuard.safe_level()
	if level > 0:
		simplify_graphics(room, level)


## Safe graphics (CrashGuard levels): the scene keeps every light and every puzzle effect, and drops the
## features most likely to fail on a phone's GPU driver, one group per level (see CrashGuard.MAX_LEVEL).
func simplify_graphics(scene: Node, level: int) -> void:
	if scene == null or level <= 0:
		return
	# 1: no MSAA (the room's own 3D view, and off-screen views such as inventory icons)
	if scene.is_inside_tree():
		scene.get_viewport().msaa_3d = Viewport.MSAA_DISABLED
	for vp in scene.find_children("*", "SubViewport", true, false):
		(vp as SubViewport).msaa_3d = Viewport.MSAA_DISABLED
	if level < 2:
		return
	# 2: no positional shadows, reflection probes (the ambient light is raised a little instead) or particles
	for l in scene.find_children("*", "Light3D", true, false):
		if l is OmniLight3D or l is SpotLight3D:
			(l as Light3D).shadow_enabled = false
	var probes := scene.find_children("*", "ReflectionProbe", true, false)
	for p in probes:
		(p as ReflectionProbe).visible = false
	if not probes.is_empty():
		for we in scene.find_children("*", "WorldEnvironment", true, false):
			var env := (we as WorldEnvironment).environment
			if env != null and not env.has_meta("safe_ambient"):
				env.set_meta("safe_ambient", true)
				env.ambient_light_energy *= 1.5
	for p in scene.find_children("*", "GPUParticles3D", true, false):
		(p as GPUParticles3D).emitting = false
		(p as GPUParticles3D).visible = false
	if level < 3:
		return
	# 3: no decals, glow or directional shadows
	for d in scene.find_children("*", "Decal", true, false):
		(d as Decal).visible = false
	for l in scene.find_children("*", "DirectionalLight3D", true, false):
		(l as Light3D).shadow_enabled = false
	for we in scene.find_children("*", "WorldEnvironment", true, false):
		var env := (we as WorldEnvironment).environment
		if env != null:
			env.glow_enabled = false


## Waits until `n` frames have been drawn (just `n` frames where nothing is drawn: headless tests).
func _frames_drawn(n: int) -> void:
	for _i in n:
		if DisplayServer.get_name() == "headless":
			await get_tree().process_frame
		else:
			await RenderingServer.frame_post_draw


func flash(color: Color, hold: float = 0.1, out: float = 0.8) -> void:
	_fade.color = Color(color, 0.0)
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", color.a, 0.08)
	tw.tween_interval(hold)
	tw.tween_property(_fade, "color:a", 0.0, out)
	tw.tween_callback(func() -> void: _fade.color = Color(0.055, 0.059, 0.071, 0.0))


func toast(text: String, seconds: float = 2.2) -> void:
	# sized and placed for this screen each time (text scale, safe area and cutout can change between toasts)
	_toast.add_theme_font_size_override("font_size", UITheme.size(26))
	_toast.add_theme_stylebox_override("normal", UITheme.caption_plate())
	var half := minf(400.0 * UITheme.wscale(), UITheme.usable_rect().size.x / 2.0)
	_toast.offset_left = -half
	_toast.offset_right = half
	_toast.offset_top = UITheme.safe_margins().y + 36
	_toast.text = text
	var tw := create_tween()
	tw.tween_property(_toast, "modulate:a", 1.0, 0.2)
	tw.tween_interval(seconds)
	tw.tween_property(_toast, "modulate:a", 0.0, 0.4)
