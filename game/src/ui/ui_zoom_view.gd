class_name UIZoomView
extends Control
## A picture the player can zoom and pan: pinch (InputEventMagnifyGesture on phones), the mouse wheel on a
## desktop, and a double tap that toggles between "fit" and 2.5x around the tapped point. Drags pan the zoomed
## picture. The picture is drawn exactly as the asset is (clue art stays what the art shows), clipped to the view.

const MAX_ZOOM := 4.0
const TAP_ZOOM := 2.5
const DOUBLE_TAP_MS := 350

var texture: Texture2D:
	set(v):
		texture = v
		_img.texture = v
		_fit()

var _img: TextureRect
var _zoom := 1.0
var _base := Vector2.ZERO # the fitted picture size at zoom 1
var _pan := Vector2.ZERO
var _last_tap_ms := 0
var _last_tap_pos := Vector2.ZERO


func _init() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	_img = TextureRect.new()
	_img.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_img.stretch_mode = TextureRect.STRETCH_SCALE
	_img.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_img.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_img)
	resized.connect(_fit)


## Fits the whole picture into the view (zoom 1, centred).
func _fit() -> void:
	if texture == null or size.x <= 0.0 or size.y <= 0.0:
		return
	var ts := texture.get_size()
	var k := minf(size.x / ts.x, size.y / ts.y)
	_base = (ts * k).floor()
	_zoom = 1.0
	_pan = Vector2.ZERO
	_apply()


func _apply() -> void:
	var s := _base * _zoom
	# the picture may not leave the view: no pan while it fits, otherwise pan within its overhang
	var over := (s - size) * 0.5
	_pan.x = clampf(_pan.x, -maxf(over.x, 0.0), maxf(over.x, 0.0))
	_pan.y = clampf(_pan.y, -maxf(over.y, 0.0), maxf(over.y, 0.0))
	_img.size = s
	_img.position = ((size - s) * 0.5 + _pan).round()


## Zooms to `z` keeping the picture point under `p` (view coordinates) where it is.
func _zoom_at(p: Vector2, z: float) -> void:
	z = clampf(z, 1.0, MAX_ZOOM)
	if is_equal_approx(z, _zoom):
		return
	var centre := size * 0.5 + _pan
	var rel := (p - centre) / _zoom # offset of the touched point from the picture centre, in zoom-1 px
	_zoom = z
	_pan = p - size * 0.5 - rel * _zoom
	_apply()


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMagnifyGesture:
		_zoom_at((ev as InputEventMagnifyGesture).position, _zoom * (ev as InputEventMagnifyGesture).factor)
		accept_event()
	elif ev is InputEventPanGesture:
		_pan -= (ev as InputEventPanGesture).delta * 12.0
		_apply()
		accept_event()
	elif ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_at(mb.position, _zoom * 1.15)
			accept_event()
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_at(mb.position, _zoom / 1.15)
			accept_event()
	elif ev is InputEventScreenTouch:
		var st := ev as InputEventScreenTouch
		if st.pressed and st.index == 0:
			var now := Time.get_ticks_msec()
			if now - _last_tap_ms < DOUBLE_TAP_MS and st.position.distance_to(_last_tap_pos) < 60.0:
				_zoom_at(st.position, 1.0 if _zoom > 1.01 else TAP_ZOOM)
				_last_tap_ms = 0
			else:
				_last_tap_ms = now
				_last_tap_pos = st.position
			accept_event()
	elif ev is InputEventScreenDrag:
		if _zoom > 1.01:
			_pan += (ev as InputEventScreenDrag).relative
			_apply()
			accept_event()
