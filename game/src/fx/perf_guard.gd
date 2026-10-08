class_name PerfGuard
extends Node
## Keeps the room playable on slower phones: watches the frame rate and steps the 3D render scale
## down (to 60 %) while it stays low, and slowly back up when there is headroom. The UI is never
## scaled. The chosen scale is remembered (Settings "render_scale") so the next launch starts there.
## Debug builds on phones also show a small FPS / scale readout for testers.
## Only active on mobile: desktop and the software-rendered QA runs keep full resolution.

const SAMPLE_S := 2.0
const LOW_FPS := 27.0
const HIGH_FPS := 55.0
const MIN_SCALE := 0.6
const STEP_DOWN := 0.1
const STEP_UP := 0.05

var active := false
var _t := 0.0
var _low := 0
var _high := 0
var _scale := 1.0
var _label: Label


func _ready() -> void:
	active = OS.has_feature("mobile") or "--perf-guard" in OS.get_cmdline_user_args()
	if not active:
		return
	_scale = clampf(float(Settings.get_value("render_scale")), MIN_SCALE, 1.0)
	_apply()
	if OS.is_debug_build():
		var layer := CanvasLayer.new()
		layer.layer = 90
		add_child(layer)
		_label = Label.new()
		_label.position = Vector2(24, 108)
		_label.add_theme_font_size_override("font_size", 18)
		_label.add_theme_color_override("font_color", Color(0.85, 0.95, 0.9, 0.85))
		_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
		_label.add_theme_constant_override("outline_size", 4)
		_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		layer.add_child(_label)


func _process(delta: float) -> void:
	if not active:
		return
	_t += delta
	if _label:
		_label.text = "FPS %d · 3D %d%%" % [Engine.get_frames_per_second(), roundi(_scale * 100.0)]
	if _t < SAMPLE_S:
		return
	_t = 0.0
	var fps := Engine.get_frames_per_second()
	if fps < LOW_FPS:
		_low += 1
		_high = 0
	elif fps > HIGH_FPS:
		_high += 1
		_low = 0
	else:
		_low = 0
		_high = 0
	if _low >= 2 and _scale > MIN_SCALE + 0.001:
		_scale = maxf(MIN_SCALE, _scale - STEP_DOWN)
		_low = 0
		_apply()
	elif _high >= 5 and _scale < 0.999:
		_scale = minf(1.0, _scale + STEP_UP)
		_high = 0
		_apply()


func _apply() -> void:
	var vp := get_viewport()
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = _scale
	if not is_equal_approx(float(Settings.get_value("render_scale")), _scale):
		Settings.set_value("render_scale", _scale)
