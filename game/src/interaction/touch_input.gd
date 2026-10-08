class_name TouchInput
extends Node
## Unifies touch (and mouse via emulate_touch_from_mouse) into tap / drag / pinch / two-finger-tap / hold.
## Only receives events the UI did not consume (_unhandled_input).

signal tapped(pos: Vector2)
signal dragged(relative: Vector2, pos: Vector2)
signal drag_started(pos: Vector2) # where the finger first touched, not where the drag threshold was crossed
signal drag_ended(pos: Vector2)
signal pinched(factor: float)
signal two_finger_tap

const TAP_MAX_MOVE := 14.0
const TAP_MAX_MS := 380

var _touches: Dictionary = {} # index -> {start: Vector2, pos: Vector2, t: int, moved: float}
var _pinch_dist := 0.0
var _multi := false
var _dragging := false
var enabled := true


func _unhandled_input(event: InputEvent) -> void:
	if not enabled:
		return
	var scale := _ui_scale()
	if event is InputEventScreenTouch:
		var e := event as InputEventScreenTouch
		if e.pressed:
			_touches[e.index] = {"start": e.position, "pos": e.position, "t": Time.get_ticks_msec(), "moved": 0.0}
			if _touches.size() == 2:
				_multi = true
				_pinch_dist = _two_dist()
		else:
			if not _touches.has(e.index):
				return
			var tch: Dictionary = _touches[e.index]
			_touches.erase(e.index)
			var dt := Time.get_ticks_msec() - int(tch["t"])
			if _multi:
				if _touches.is_empty():
					if dt < TAP_MAX_MS and float(tch["moved"]) < TAP_MAX_MOVE * scale:
						two_finger_tap.emit()
					_multi = false
			elif float(tch["moved"]) < TAP_MAX_MOVE * scale and dt < TAP_MAX_MS * 2:
				tapped.emit(e.position)
			if _dragging and _touches.is_empty():
				_dragging = false
				drag_ended.emit(e.position)
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		if not _touches.has(d.index):
			return
		var tch: Dictionary = _touches[d.index]
		tch["moved"] = float(tch["moved"]) + d.relative.length()
		tch["pos"] = d.position
		if _touches.size() >= 2:
			var nd := _two_dist()
			if _pinch_dist > 1.0 and nd > 1.0:
				pinched.emit(nd / _pinch_dist)
			_pinch_dist = nd
		elif not _multi:
			if not _dragging and float(tch["moved"]) >= TAP_MAX_MOVE * scale:
				_dragging = true
				drag_started.emit(tch["start"])
			if _dragging:
				dragged.emit(d.relative, d.position)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			pinched.emit(1.08)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			pinched.emit(1.0 / 1.08)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_RIGHT:
			two_finger_tap.emit()
	elif event is InputEventMagnifyGesture:
		pinched.emit((event as InputEventMagnifyGesture).factor)


func _two_dist() -> float:
	var ks := _touches.keys()
	if ks.size() < 2:
		return 0.0
	return (_touches[ks[0]]["pos"] as Vector2).distance_to(_touches[ks[1]]["pos"])


func _ui_scale() -> float:
	return maxf(1.0, DisplayServer.screen_get_scale())


func reset() -> void:
	_touches.clear()
	_multi = false
	_dragging = false
