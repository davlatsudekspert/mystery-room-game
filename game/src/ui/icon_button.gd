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
var _mesh := UIMesh.new() # the bezel, the icon and the count's disc: one draw call
var _mesh_top := UIMesh.new() # over a picture: the "in hand" ring and the count's disc


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
	# Everything but a picture and the count's digits goes into one mesh, so a button is one draw call (it was 8 to
	# 15: each circle, antialiased arc and polygon below was its own; see UIMesh and docs/QUALITY_REPORT.md)
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
	_mesh.clear()
	_mesh.disc(c, r - 2.0, bg)
	_mesh.ring(c, r - 2.0, 1.5, ring)
	_mesh.ring(c, r - 7.0, 1.0, Color(ring, ring.a * 0.32)) # the bezel's inner ring
	var s := r * 0.42
	var w := maxf(2.5, r * 0.065)
	if picture != null:
		# the item in hand, kept square inside the bezel's inner ring
		_mesh.draw(self)
		var ts := picture.get_size()
		if ts.x > 0.0 and ts.y > 0.0:
			var box := (r - 9.0) * 1.42
			var k := minf(box / ts.x, box / ts.y)
			var ds := ts * k
			draw_texture_rect(picture, Rect2(c - ds * 0.5, ds), false)
		_mesh_top.clear()
		_mesh_top.ring(c, r - 2.0, maxf(2.0, w * 0.8), UITheme.BRASS_HI) # "in hand"
		_count_shape(_mesh_top, c, r)
		_mesh_top.draw(self)
		_count_text(c, r)
		return
	match icon_id:
		"back":
			_mesh.stroke(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), w, col)
		"next":
			_mesh.stroke(PackedVector2Array([c + Vector2(-s * 0.35, -s), c + Vector2(s * 0.55, 0), c + Vector2(-s * 0.35, s)]), w, col)
		"prev":
			_mesh.stroke(PackedVector2Array([c + Vector2(s * 0.35, -s), c + Vector2(-s * 0.55, 0), c + Vector2(s * 0.35, s)]), w, col)
		"pause":
			# a roman numeral II: two bars with serifs
			var bw := w * 1.25
			var sw := w * 0.85
			for x in [-s * 0.36, s * 0.36]:
				_mesh.line(c + Vector2(x, -s * 0.78), c + Vector2(x, s * 0.78), bw, col)
				_mesh.line(c + Vector2(x - s * 0.2, -s * 0.78), c + Vector2(x + s * 0.2, -s * 0.78), sw, col)
				_mesh.line(c + Vector2(x - s * 0.2, s * 0.78), c + Vector2(x + s * 0.2, s * 0.78), sw, col)
		"hint":
			_mesh.arc(c + Vector2(0, -s * 0.25), s * 0.62, deg_to_rad(140), deg_to_rad(400), w, col, 32)
			_mesh.line(c + Vector2(-s * 0.3, s * 0.45), c + Vector2(s * 0.3, s * 0.45), w, col)
			_mesh.line(c + Vector2(-s * 0.22, s * 0.75), c + Vector2(s * 0.22, s * 0.75), w, col)
			_mesh.line(c + Vector2(-s * 0.3, s * 0.2), c + Vector2(-s * 0.3, s * 0.45), w, col)
			_mesh.line(c + Vector2(s * 0.3, s * 0.2), c + Vector2(s * 0.3, s * 0.45), w, col)
		"inspect":
			_mesh.arc(c + Vector2(-s * 0.15, -s * 0.15), s * 0.55, 0, TAU, w, col, 32)
			_mesh.line(c + Vector2(s * 0.25, s * 0.25), c + Vector2(s * 0.8, s * 0.8), w * 1.3, col)
		"combine":
			_mesh.arc(c + Vector2(-s * 0.3, 0), s * 0.5, 0, TAU, w, col, 32)
			_mesh.arc(c + Vector2(s * 0.3, 0), s * 0.5, 0, TAU, w, col, 32)
		"close":
			_mesh.line(c + Vector2(-s * 0.6, -s * 0.6), c + Vector2(s * 0.6, s * 0.6), w, col)
			_mesh.line(c + Vector2(-s * 0.6, s * 0.6), c + Vector2(s * 0.6, -s * 0.6), w, col)
		"uv":
			_mesh.disc(c, s * 0.3, Color(UITheme.UV, 0.9))
			for k in 8:
				var a := TAU * k / 8.0
				_mesh.line(c + Vector2(cos(a), sin(a)) * s * 0.5, c + Vector2(cos(a), sin(a)) * s * 0.85, w * 0.8, col)
		"book":
			# draw_rect(…, false, w) strokes centred on the rectangle's edge, as four bars
			var br := Rect2(c - Vector2(s * 0.7, s * 0.85), Vector2(s * 1.4, s * 1.7)).grow(w * 0.5)
			_mesh.rect(Rect2(br.position, Vector2(br.size.x, w)), col)
			_mesh.rect(Rect2(br.position + Vector2(0, br.size.y - w), Vector2(br.size.x, w)), col)
			_mesh.rect(Rect2(br.position + Vector2(0, w), Vector2(w, br.size.y - 2.0 * w)), col)
			_mesh.rect(Rect2(br.position + Vector2(br.size.x - w, w), Vector2(w, br.size.y - 2.0 * w)), col)
			_mesh.line(c + Vector2(-s * 0.35, -s * 0.85), c + Vector2(-s * 0.35, s * 0.85), w, col)
		"bag":
			# a doctor's bag: the handle arc, a body that widens toward its base, the frame seam and the clasp
			var top := -s * 0.22
			var base := s * 0.86
			_mesh.arc(c + Vector2(0, top), s * 0.4, PI, TAU, w, col, 24)
			_mesh.stroke(PackedVector2Array([c + Vector2(-s * 0.74, top), c + Vector2(s * 0.74, top),
				c + Vector2(s * 0.95, base - s * 0.1), c + Vector2(s * 0.85, base), c + Vector2(-s * 0.85, base),
				c + Vector2(-s * 0.95, base - s * 0.1), c + Vector2(-s * 0.74, top)]), w, col)
			_mesh.line(c + Vector2(-s * 0.82, s * 0.16), c + Vector2(s * 0.82, s * 0.16), w * 0.7, col, true)
			var cl := c + Vector2(0, s * 0.16)
			_mesh.diamond(cl, s * 0.16, s * 0.16, col)
	_count_shape(_mesh, c, r)
	if badge != "":
		# a small gold dot on the bezel (the hint nudge)
		var bc := c + Vector2(r * 0.66, -r * 0.66)
		_mesh.disc(bc, r * 0.17, UITheme.INK)
		_mesh.disc(bc, r * 0.13, UITheme.BRASS_HI)
	_mesh.draw(self)
	_count_text(c, r)


## The brass disc at the bezel's upper right that carries the count (drawn over the icon or the picture).
func _count_shape(m: UIMesh, c: Vector2, r: float) -> void:
	if count <= 0:
		return
	var rad := _count_radius()
	var bc := c + Vector2(r * 0.7, -r * 0.7)
	m.disc(bc, rad + 2.0, UITheme.INK)
	m.disc(bc, rad, UITheme.BRASS_HI)


func _count_radius() -> float:
	var font := UITheme.caps_font(true, 0)
	var fs := UITheme.size(18)
	var tw := font.get_string_size(str(count), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	return maxf(fs * 0.62, tw * 0.5 + 6.0)


## The count's digits, over the disc.
func _count_text(c: Vector2, r: float) -> void:
	if count <= 0:
		return
	var font := UITheme.caps_font(true, 0)
	var fs := UITheme.size(18)
	var txt := str(count)
	var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var bc := c + Vector2(r * 0.7, -r * 0.7)
	var asc := font.get_ascent(fs)
	var desc := font.get_descent(fs)
	draw_string(font, Vector2(bc.x - tw * 0.5, bc.y + (asc - desc) * 0.5), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.INK)
