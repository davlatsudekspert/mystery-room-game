class_name IconButton
extends Button
## Round brass line-icon button drawn in code (crisp at any DPI, no texture assets): a dark translucent disc
## inside a hairline gold bezel (two rings), the icon in cream. Pressed or active, the disc fills with brass.
## icons: back, hint, pause (a roman-numeral "II"), inspect, combine, uv, close, next, prev, book, bag (the
## inventory: a doctor's bag with a handle, a frame seam and a clasp)
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
## A picture drawn inside the disc instead of the line icon (the bag shows the item in hand).
var picture: Texture2D:
	set(v):
		picture = v
		queue_redraw()
## A number on a small gold disc at the bezel (the bag: how many items it holds); 0 = none.
var count := 0:
	set(v):
		count = v
		queue_redraw()


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
	var lit := button_pressed or active
	var col := UITheme.INK if lit else UITheme.CREAM
	var bg := Color(UITheme.BRASS, 0.88) if lit else Color(0.025, 0.027, 0.033, 0.66)
	if is_hovered() and not lit:
		bg = Color(0.10, 0.09, 0.075, 0.82)
	var ring := Color(UITheme.BRASS, 0.85)
	if disabled:
		col = UITheme.MUTED
		ring = Color(UITheme.MUTED, 0.35)
	draw_circle(c, r - 2.0, bg)
	draw_arc(c, r - 2.0, 0.0, TAU, 64, ring, 1.5, true)
	draw_arc(c, r - 7.0, 0.0, TAU, 64, Color(ring, ring.a * 0.32), 1.0, true) # the bezel's inner ring
	var s := r * 0.42
	var w := maxf(2.5, r * 0.065)
	if picture != null:
		# the item in hand, kept square inside the bezel's inner ring
		var ts := picture.get_size()
		if ts.x > 0.0 and ts.y > 0.0:
			var box := (r - 9.0) * 1.42
			var k := minf(box / ts.x, box / ts.y)
			var ds := ts * k
			draw_texture_rect(picture, Rect2(c - ds * 0.5, ds), false)
		draw_arc(c, r - 2.0, 0.0, TAU, 64, UITheme.BRASS_HI, maxf(2.0, w * 0.8), true) # "in hand"
		_draw_count(c, r)
		return
	match icon_id:
		"back":
			draw_polyline(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), col, w, true)
		"next":
			draw_polyline(PackedVector2Array([c + Vector2(-s * 0.35, -s), c + Vector2(s * 0.55, 0), c + Vector2(-s * 0.35, s)]), col, w, true)
		"prev":
			draw_polyline(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), col, w, true)
		"pause":
			# a roman numeral II: two bars with serifs
			var bw := w * 1.25
			var sw := w * 0.85
			for x in [-s * 0.36, s * 0.36]:
				draw_line(c + Vector2(x, -s * 0.78), c + Vector2(x, s * 0.78), col, bw)
				draw_line(c + Vector2(x - s * 0.2, -s * 0.78), c + Vector2(x + s * 0.2, -s * 0.78), col, sw)
				draw_line(c + Vector2(x - s * 0.2, s * 0.78), c + Vector2(x + s * 0.2, s * 0.78), col, sw)
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
		"bag":
			# a doctor's bag: the handle arc, a body that widens toward its base, the frame seam and the clasp
			var top := -s * 0.22
			var base := s * 0.86
			draw_arc(c + Vector2(0, top), s * 0.4, PI, TAU, 24, col, w, true)
			draw_polyline(PackedVector2Array([c + Vector2(-s * 0.74, top), c + Vector2(s * 0.74, top),
				c + Vector2(s * 0.95, base - s * 0.1), c + Vector2(s * 0.85, base), c + Vector2(-s * 0.85, base),
				c + Vector2(-s * 0.95, base - s * 0.1), c + Vector2(-s * 0.74, top)]), col, w, true)
			draw_line(c + Vector2(-s * 0.82, s * 0.16), c + Vector2(s * 0.82, s * 0.16), col, w * 0.7, true)
			var cl := c + Vector2(0, s * 0.16)
			draw_colored_polygon(PackedVector2Array([cl + Vector2(-s * 0.16, 0), cl + Vector2(0, -s * 0.16),
				cl + Vector2(s * 0.16, 0), cl + Vector2(0, s * 0.16)]), col)
	_draw_count(c, r)
	if badge != "":
		# a small gold dot on the bezel (the hint nudge)
		var bc := c + Vector2(r * 0.66, -r * 0.66)
		draw_circle(bc, r * 0.17, UITheme.INK)
		draw_circle(bc, r * 0.13, UITheme.BRASS_HI)


## The count on a small brass disc at the bezel's upper right (drawn over the icon or the picture).
func _draw_count(c: Vector2, r: float) -> void:
	if count <= 0:
		return
	var font := UITheme.caps_font(true, 0)
	var fs := UITheme.size(18)
	var txt := str(count)
	var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var rad := maxf(fs * 0.62, tw * 0.5 + 6.0)
	var bc := c + Vector2(r * 0.7, -r * 0.7)
	draw_circle(bc, rad + 2.0, UITheme.INK)
	draw_circle(bc, rad, UITheme.BRASS_HI)
	var asc := font.get_ascent(fs)
	var desc := font.get_descent(fs)
	draw_string(font, Vector2(bc.x - tw * 0.5, bc.y + (asc - desc) * 0.5), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.INK)
