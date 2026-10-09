class_name IconButton
extends Button
## Round brass line-icon button drawn in code (crisp at any DPI, no texture assets).
## icons: back, hint, pause, inspect, combine, uv, close, next, prev, gear
## The tappable rect is at least UITheme.TOUCH_MM on the physical screen; the drawn disc can be smaller
## (`visual`), so phones get thumb-sized targets without oversized icons.

var icon_id := "back":
	set(v):
		icon_id = v
		queue_redraw()
var badge := "":
	set(v):
		badge = v
		queue_redraw()
var active := false:
	set(v):
		active = v
		queue_redraw()
## Fraction of the rect covered by the drawn disc (1 = edge to edge).
var visual := 1.0


static func make(id: String, diameter: int = 96) -> IconButton:
	var b := IconButton.new()
	b.icon_id = id
	var hit := UITheme.target(diameter)
	b.custom_minimum_size = Vector2(hit, hit)
	b.visual = clampf(maxf(float(diameter), hit * 0.8) / hit, 0.5, 1.0)
	b.focus_mode = Control.FOCUS_NONE
	b.flat = true
	b.pressed.connect(func() -> void: AudioManager.ui("ui_tap"))
	return b


func _ready() -> void:
	# redraw on state changes only (it used to redraw every frame)
	for s: Signal in [mouse_entered, mouse_exited, button_down, button_up]:
		s.connect(queue_redraw)
	toggled.connect(func(_on: bool) -> void: queue_redraw())


func _draw() -> void:
	var r := minf(size.x, size.y) * 0.5 * visual
	var c := size * 0.5
	var col := UITheme.INK if button_pressed or active else UITheme.CREAM
	var bg := Color(UITheme.BRASS, 0.9) if (button_pressed or active) else Color(0.06, 0.065, 0.075, 0.82)
	if is_hovered() and not active:
		bg = Color(0.12, 0.11, 0.09, 0.92)
	if disabled:
		col = UITheme.MUTED
	draw_circle(c, r - 2, bg)
	draw_arc(c, r - 2, 0, TAU, 48, Color(UITheme.BRASS, 0.8), 2.5, true)
	var s := r * 0.42
	var w := maxf(3.0, r * 0.075)
	match icon_id:
		"back":
			draw_polyline(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), col, w, true)
		"next":
			draw_polyline(PackedVector2Array([c + Vector2(-s * 0.35, -s), c + Vector2(s * 0.55, 0), c + Vector2(-s * 0.35, s)]), col, w, true)
		"prev":
			draw_polyline(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), col, w, true)
		"pause":
			draw_line(c + Vector2(-s * 0.4, -s * 0.8), c + Vector2(-s * 0.4, s * 0.8), col, w * 1.3)
			draw_line(c + Vector2(s * 0.4, -s * 0.8), c + Vector2(s * 0.4, s * 0.8), col, w * 1.3)
		"hint":
			draw_arc(c + Vector2(0, -s * 0.25), s * 0.62, deg_to_rad(140), deg_to_rad(400), 32, col, w, true)
			draw_line(c + Vector2(-s * 0.3, s * 0.45), c + Vector2(s * 0.3, s * 0.45), col, w)
			draw_line(c + Vector2(-s * 0.22, s * 0.75), c + Vector2(s * 0.22, s * 0.75), col, w)
			draw_line(c + Vector2(-s * 0.3, s * 0.2), c + Vector2(-s * 0.3, s * 0.45), col, w)
			draw_line(c + Vector2(s * 0.3, s * 0.2), c + Vector2(s * 0.3, s * 0.45), col, w)
		"inspect":
			draw_arc(c + Vector2(-s * 0.15, -s * 0.15), s * 0.55, 0, TAU, 32, col, w, true)
			draw_line(c + Vector2(s * 0.25, s * 0.25), c + Vector2(s * 0.8, s * 0.8), col, w * 1.3)
		"combine":
			draw_arc(c + Vector2(-s * 0.3, 0), s * 0.5, 0, TAU, 32, col, w, true)
			draw_arc(c + Vector2(s * 0.3, 0), s * 0.5, 0, TAU, 32, col, w, true)
		"close":
			draw_line(c + Vector2(-s * 0.6, -s * 0.6), c + Vector2(s * 0.6, s * 0.6), col, w)
			draw_line(c + Vector2(-s * 0.6, s * 0.6), c + Vector2(s * 0.6, -s * 0.6), col, w)
		"uv":
			draw_circle(c, s * 0.3, Color(UITheme.UV, 0.9))
			for k in 8:
				var a := TAU * k / 8.0
				draw_line(c + Vector2(cos(a), sin(a)) * s * 0.5, c + Vector2(cos(a), sin(a)) * s * 0.85, col, w * 0.8)
		"book":
			draw_rect(Rect2(c - Vector2(s * 0.7, s * 0.85), Vector2(s * 1.4, s * 1.7)), col, false, w)
			draw_line(c + Vector2(-s * 0.35, -s * 0.85), c + Vector2(-s * 0.35, s * 0.85), col, w)
	if badge != "":
		draw_circle(c + Vector2(r * 0.68, -r * 0.68), r * 0.28, UITheme.DANGER)
