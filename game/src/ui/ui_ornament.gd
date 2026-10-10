class_name UIOrnament
extends Control
## Thin brass ornaments drawn in code (crisp at any dpi, no texture assets), the same language as the main
## menu's item rule: a horizontal rule that fades out toward both ends with a small diamond at its centre
## (under titles), a header rule that runs from a label to the right edge, or a vertical rule with small
## arrow tips (beside the inventory column). Scale follows the text size.

enum Kind { RULE, HEADER, VRULE }

var kind := Kind.RULE
var color := UITheme.BRASS
var alpha := 0.85
var thickness := 1.5
var diamond := true
var _mesh := UIMesh.new()


## A centred rule with a diamond, as wide as its container (or `width` px), `height` px tall.
static func rule(width: float = 0.0, height: float = 22.0) -> UIOrnament:
	var o := UIOrnament.new()
	o.kind = Kind.RULE
	o.custom_minimum_size = Vector2(width, height)
	o.size_flags_horizontal = Control.SIZE_EXPAND_FILL if width <= 0.0 else Control.SIZE_SHRINK_CENTER
	return o


## A hairline that continues a section header to the right.
static func header_rule(height: float = 10.0) -> UIOrnament:
	var o := UIOrnament.new()
	o.kind = Kind.HEADER
	o.alpha = 0.4
	o.thickness = 1.0
	o.custom_minimum_size = Vector2(0, height)
	o.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return o


## A vertical rule with arrow tips at both ends (the inventory column).
static func vrule(width: float = 14.0) -> UIOrnament:
	var o := UIOrnament.new()
	o.kind = Kind.VRULE
	o.custom_minimum_size = Vector2(width, 0)
	return o


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Ornament scale: grows with the body text, but slower.
static func scale_k() -> float:
	return clampf(1.0 + (float(UITheme.size(26)) / 26.0 - 1.0) * 0.6, 1.0, 1.8)


func _draw() -> void:
	# one mesh, one draw call (the diamond rule was 4 polygons and 2 circles, the vertical rule 7 calls)
	var m := _mesh
	m.clear()
	var k := scale_k()
	var th := maxf(1.0, roundf(thickness * k))
	var col := Color(color, alpha)
	var clear := Color(color, 0.0)
	match kind:
		Kind.RULE:
			var y := roundf(size.y * 0.5)
			var cx := roundf(size.x * 0.5)
			var dx := 6.0 * k
			var gap := (dx + 7.0 * k) if diamond else 0.0
			# solid near the diamond, fading out toward both ends
			var half := cx - gap
			m.gradient_rect(Rect2(cx - gap - half, y - th * 0.5, half, th), clear, col)
			m.gradient_rect(Rect2(cx + gap, y - th * 0.5, half, th), col, clear)
			if diamond:
				m.diamond(Vector2(cx, y), dx, 4.0 * k, Color(UITheme.BRASS_HI, alpha))
				# two small dots flanking the diamond
				m.disc(Vector2(cx - gap - 10.0 * k, y), 1.6 * k, Color(UITheme.BRASS_HI, alpha * 0.8), false, 16)
				m.disc(Vector2(cx + gap + 10.0 * k, y), 1.6 * k, Color(UITheme.BRASS_HI, alpha * 0.8), false, 16)
		Kind.HEADER:
			var y := roundf(size.y * 0.5)
			m.gradient_rect(Rect2(0, y - th * 0.5, size.x, th), col, Color(color, alpha * 0.25))
		Kind.VRULE:
			var x := roundf(size.x * 0.5)
			var tip := 9.0 * k
			var inset := tip + 4.0 * k
			if size.y > 2.0 * inset:
				m.rect(Rect2(x - th * 0.5, inset, th, size.y - 2.0 * inset), col)
			# arrow tips: a small chevron at each end
			var w := 4.5 * k
			var hi := Color(UITheme.BRASS_HI, alpha)
			m.stroke(PackedVector2Array([Vector2(x - w, tip), Vector2(x, 1.0), Vector2(x + w, tip)]), th, hi)
			m.stroke(PackedVector2Array([Vector2(x - w, size.y - tip), Vector2(x, size.y - 1.0), Vector2(x + w, size.y - tip)]), th, hi)
	m.draw(self)
