class_name UIMesh
extends RefCounted
## Coloured triangles for ONE `CanvasItem.draw_mesh()` call.
##
## The always-visible HUD is made of round bezels, icon strokes, gradient bands and hairlines. Drawn with
## draw_circle / draw_arc / draw_polygon / draw_polyline each of those is its own draw call (an antialiased arc or
## polyline is three) because the 2D renderer only batches runs of rects, lines and one texture. The same shapes
## collected here are one mesh, so a bezel button or a banner costs a single call. Vertex colours carry the fills,
## the gradients and the antialiasing: a stroke has a 0.5 px ramp from its colour to alpha 0 on each side.
## Shapes are drawn in the order they were added (later over earlier), like consecutive draw_* calls.
##
## Measured with `tap_map --perf --hud-breakdown`; see docs/QUALITY_REPORT.md → HUD draw calls.

const FEATHER := 0.5 # px: the antialiasing ramp on each side of a stroke or disc edge
const MITER_LIMIT := 2.5 # a sharp corner's miter is at most this many half-widths long
const CIRCLE_SEGMENTS := 64

var _v := PackedVector2Array()
var _c := PackedColorArray()
var _i := PackedInt32Array()
var _mesh: ArrayMesh


func clear() -> void:
	_v.clear()
	_c.clear()
	_i.clear()


func is_empty() -> bool:
	return _i.is_empty()


func vertex_count() -> int:
	return _v.size()


func triangle_count() -> int:
	return _i.size() / 3


## Calls `ci.draw_mesh()` once with everything added so far (nothing when empty). Call from `_draw()`.
func draw(ci: CanvasItem) -> void:
	if _i.is_empty():
		return
	if _mesh == null:
		_mesh = ArrayMesh.new()
	else:
		_mesh.clear_surfaces()
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = _v
	arrays[Mesh.ARRAY_COLOR] = _c
	arrays[Mesh.ARRAY_INDEX] = _i
	_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	ci.draw_mesh(_mesh, null)


# ====================================================================== primitives
func _vert(p: Vector2, col: Color) -> int:
	_v.append(p)
	_c.append(col)
	return _v.size() - 1


func _tri(a: int, b: int, c: int) -> void:
	_i.append(a)
	_i.append(b)
	_i.append(c)


## A quad from its four corners in order, each with its own colour (a gradient between them).
func quad(a: Vector2, b: Vector2, c: Vector2, d: Vector2, ca: Color, cb: Color, cc: Color, cd: Color) -> void:
	var ia := _vert(a, ca)
	var ib := _vert(b, cb)
	var ic := _vert(c, cc)
	var id := _vert(d, cd)
	_tri(ia, ib, ic)
	_tri(ia, ic, id)


func rect(r: Rect2, col: Color) -> void:
	if r.size.x <= 0.0 or r.size.y <= 0.0:
		return
	quad(r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y), col, col, col, col)


## A horizontal gradient: `left` at the left edge, `right` at the right edge.
func gradient_rect(r: Rect2, left: Color, right: Color) -> void:
	if r.size.x <= 0.0 or r.size.y <= 0.0:
		return
	quad(r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y), left, right, right, left)


## A convex polygon in one colour (a fan from its first point), edges not antialiased.
func polygon(points: PackedVector2Array, col: Color) -> void:
	if points.size() < 3:
		return
	var first := _vert(points[0], col)
	var prev := _vert(points[1], col)
	for k in range(2, points.size()):
		var cur := _vert(points[k], col)
		_tri(first, prev, cur)
		prev = cur


func diamond(c: Vector2, dx: float, dy: float, col: Color) -> void:
	polygon(PackedVector2Array([c + Vector2(-dx, 0), c + Vector2(0, -dy), c + Vector2(dx, 0), c + Vector2(0, dy)]), col)


## A filled circle. `aa` adds the soft edge (the disc then reaches FEATHER beyond `radius` at alpha 0).
func disc(center: Vector2, radius: float, col: Color, aa: bool = false, segments: int = CIRCLE_SEGMENTS) -> void:
	if radius <= 0.0:
		return
	var core := maxf(radius - FEATHER, 0.0) if aa else radius
	var hub := _vert(center, col)
	var rim: Array[int] = []
	var outer: Array[int] = []
	var clear := Color(col, 0.0)
	for k in segments:
		var dir := Vector2.from_angle(TAU * k / segments)
		rim.append(_vert(center + dir * core, col))
		if aa:
			outer.append(_vert(center + dir * (core + 2.0 * FEATHER), clear))
	for k in segments:
		var n := (k + 1) % segments
		_tri(hub, rim[k], rim[n])
		if aa:
			_tri(rim[k], outer[k], outer[n])
			_tri(rim[k], outer[n], rim[n])


## A line of `width` px through `points`, butt ends, mitered corners. `aa` gives the soft edges of
## draw_polyline(…, antialiased = true); without it the edges are hard like draw_line's.
func stroke(points: PackedVector2Array, width: float, col: Color, closed: bool = false, aa: bool = true) -> void:
	var pts := PackedVector2Array()
	for p in points: # a repeated point has no direction
		if pts.is_empty() or pts[pts.size() - 1].distance_squared_to(p) > 0.000001:
			pts.append(p)
	if closed and pts.size() > 1 and pts[0].distance_squared_to(pts[pts.size() - 1]) <= 0.000001:
		pts.remove_at(pts.size() - 1)
	var n := pts.size()
	if n < 2 or width <= 0.0:
		return
	var h := width * 0.5
	var core := maxf(h - FEATHER, 0.0) if aa else h
	var edge := core + 2.0 * FEATHER if aa else h
	var clear := Color(col, 0.0)
	var per := 4 if aa else 2
	var first := _v.size()
	for k in n:
		var off := _offset(pts, k, closed)
		if aa:
			_vert(pts[k] + off * edge, clear)
			_vert(pts[k] + off * core, col)
			_vert(pts[k] - off * core, col)
			_vert(pts[k] - off * edge, clear)
		else:
			_vert(pts[k] + off * h, col)
			_vert(pts[k] - off * h, col)
	var segs := n if closed else n - 1
	for k in segs:
		var a := first + k * per
		var b := first + ((k + 1) % n) * per
		for s in per - 1:
			_tri(a + s, a + s + 1, b + s)
			_tri(a + s + 1, b + s + 1, b + s)


## The vector from the point at `k` to the stroke's left edge for a half-width of 1 (a miter at corners).
func _offset(p: PackedVector2Array, k: int, closed: bool) -> Vector2:
	var n := p.size()
	var has_prev := closed or k > 0
	var has_next := closed or k < n - 1
	var d0 := Vector2.ZERO
	var d1 := Vector2.ZERO
	if has_prev:
		d0 = (p[k] - p[(k - 1 + n) % n]).normalized()
	if has_next:
		d1 = (p[(k + 1) % n] - p[k]).normalized()
	if not has_prev:
		d0 = d1
	if not has_next:
		d1 = d0
	var n0 := Vector2(-d0.y, d0.x)
	var n1 := Vector2(-d1.y, d1.x)
	var m := n0 + n1
	if m.length_squared() < 0.0001:
		return n1 # a U-turn: no miter
	m = m.normalized()
	return m / maxf(m.dot(n0), 1.0 / MITER_LIMIT)


## draw_line(a, b, col, width): a butt-ended bar. Antialiased only when asked.
func line(a: Vector2, b: Vector2, width: float, col: Color, aa: bool = false) -> void:
	stroke(PackedVector2Array([a, b]), width, col, false, aa)


## draw_arc(center, radius, from, to, segments, col, width, true): the arc as a stroked polyline.
func arc(center: Vector2, radius: float, from_angle: float, to_angle: float, width: float, col: Color,
		segments: int = CIRCLE_SEGMENTS, aa: bool = true) -> void:
	var full := absf(to_angle - from_angle) >= TAU - 0.0001
	var pts := PackedVector2Array()
	var count := segments if full else segments + 1
	for k in count:
		pts.append(center + Vector2.from_angle(lerpf(from_angle, to_angle, float(k) / segments)) * radius)
	stroke(pts, width, col, full, aa)


## draw_arc over a full turn: a ring of `width` centred on `radius`.
func ring(center: Vector2, radius: float, width: float, col: Color, segments: int = CIRCLE_SEGMENTS) -> void:
	arc(center, radius, 0.0, TAU, width, col, segments)
