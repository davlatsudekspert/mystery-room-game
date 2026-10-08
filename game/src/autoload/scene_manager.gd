extends Node
## Fade transitions between scenes and a global toast line (save feedback, notices).

signal scene_changed(path: String)

var _layer: CanvasLayer
var _fade: ColorRect
var _toast: Label
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


## Android back button/gesture (with application/config/quit_on_go_back off) and Escape on desktop go to
## the current scene's handle_back(); a scene without one ignores it, so "back" never quits by accident.
func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_dispatch_back()


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
	get_tree().paused = false
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	await get_tree().process_frame
	scene_changed.emit(path)
	var tw2 := create_tween()
	tw2.tween_property(_fade, "color:a", 0.0, fade_time)
	await tw2.finished
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_busy = false


func flash(color: Color, hold: float = 0.1, out: float = 0.8) -> void:
	_fade.color = Color(color, 0.0)
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", color.a, 0.08)
	tw.tween_interval(hold)
	tw.tween_property(_fade, "color:a", 0.0, out)
	tw.tween_callback(func() -> void: _fade.color = Color(0.055, 0.059, 0.071, 0.0))


func toast(text: String, seconds: float = 2.2) -> void:
	_toast.text = text
	var tw := create_tween()
	tw.tween_property(_toast, "modulate:a", 1.0, 0.2)
	tw.tween_interval(seconds)
	tw.tween_property(_toast, "modulate:a", 0.0, 0.4)
