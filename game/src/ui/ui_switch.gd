class_name UISwitch
extends Button
## An on/off switch: a slim pill track with a round knob that slides to the right and turns the track gold when
## on. The hit rect is a full touch target (UITheme.target(78) tall); the drawn pill is smaller. `text` stays
## empty: the row's label says what it switches, and the row shows On/Off in words beside it.

var _t := 0.0 # knob position 0 (off) .. 1 (on), animated
var _tw: Tween


func _init() -> void:
	toggle_mode = true
	focus_mode = Control.FOCUS_NONE
	flat = true
	var h := UITheme.target(78)
	custom_minimum_size = Vector2(roundf(h * 1.15), h)
	var empty := StyleBoxEmpty.new()
	for s in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
		add_theme_stylebox_override(s, empty)
	toggled.connect(_on_toggled)
	pressed.connect(func() -> void: AudioManager.ui("ui_tap"))
	for s: Signal in [mouse_entered, mouse_exited, button_down, button_up]:
		s.connect(queue_redraw)


## Sets the state without emitting `toggled` (and without the slide animation).
func set_on(on: bool) -> void:
	set_pressed_no_signal(on)
	_t = 1.0 if on else 0.0
	queue_redraw()


func _on_toggled(on: bool) -> void:
	if _tw != null and _tw.is_valid():
		_tw.kill()
	_tw = create_tween()
	_tw.tween_method(func(v: float) -> void:
		_t = v
		queue_redraw(), _t, 1.0 if on else 0.0, 0.18).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _draw() -> void:
	var pill_h := clampf(roundf(size.y * 0.38), 26.0, 64.0)
	var pill_w := roundf(pill_h * 1.85)
	var c := size * 0.5
	var r := Rect2(c - Vector2(pill_w, pill_h) * 0.5, Vector2(pill_w, pill_h))
	var sb := StyleBoxFlat.new()
	sb.set_corner_radius_all(int(pill_h * 0.5))
	sb.bg_color = Color(0.09, 0.09, 0.1, 0.9).lerp(Color(UITheme.BRASS, 0.55), _t)
	sb.border_color = Color(UITheme.BRASS, 0.45).lerp(UITheme.BRASS_HI, _t)
	sb.set_border_width_all(1)
	if disabled:
		sb.bg_color = Color(0.08, 0.08, 0.09, 0.6)
		sb.border_color = Color(UITheme.MUTED, 0.3)
	sb.draw(get_canvas_item(), r)
	var kr := pill_h * 0.5 - 3.0
	var kx := lerpf(r.position.x + pill_h * 0.5, r.end.x - pill_h * 0.5, _t)
	var knob := Color(UITheme.MUTED, 1.0).lerp(UITheme.CREAM, _t)
	if disabled:
		knob = Color(UITheme.MUTED, 0.5)
	elif is_hovered():
		knob = knob.lightened(0.08)
	draw_circle(Vector2(kx, c.y), kr, knob)
	draw_arc(Vector2(kx, c.y), kr, 0.0, TAU, 32, Color(UITheme.BRASS_HI, 0.35 + 0.45 * _t), 1.0, true)
