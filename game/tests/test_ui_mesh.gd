extends TestBase
## UIMesh (src/ui/ui_mesh.gd): the HUD's bezels, icon strokes, bands and rules are collected into one mesh per
## control, so each costs one draw call (docs/QUALITY_REPORT.md → HUD draw calls). The geometry is checked here
## (headless has no renderer to count calls in); the calls themselves are measured by `tap_map --perf --hud-breakdown`.

const ICONS := ["back", "hint", "pause", "inspect", "combine", "uv", "close", "next", "prev", "book", "bag"]


static func _verts(m: UIMesh) -> PackedVector2Array:
	return m.get("_v")


static func _colors(m: UIMesh) -> PackedColorArray:
	return m.get("_c")


static func _indices(m: UIMesh) -> PackedInt32Array:
	return m.get("_i")


## Every index points at a vertex, triangles come whole, and every colour channel is a valid fraction.
func _sane(m: UIMesh, what: String) -> void:
	var n := m.vertex_count()
	var idx := _indices(m)
	check(idx.size() % 3 == 0, "%s: indices come in triangles" % what)
	var bad := 0
	for i in idx:
		if i < 0 or i >= n:
			bad += 1
	eq(bad, 0, "%s: indices out of range" % what)
	var cols := _colors(m)
	eq(cols.size(), n, "%s: one colour per vertex" % what)
	for c in cols:
		if c.a < 0.0 or c.a > 1.0 or c.r < 0.0 or c.r > 1.0:
			bad += 1
	eq(bad, 0, "%s: colours in range" % what)


func _bounds(m: UIMesh) -> Rect2:
	var vs := _verts(m)
	var r := Rect2(vs[0], Vector2.ZERO)
	for v in vs:
		r = r.expand(v)
	return r


func test_rect_and_gradient() -> void:
	var m := UIMesh.new()
	check(m.is_empty(), "a new mesh is empty")
	m.rect(Rect2(10, 20, 30, 5), Color.RED)
	eq(m.vertex_count(), 4, "a rect has four vertices")
	eq(m.triangle_count(), 2, "a rect is two triangles")
	m.gradient_rect(Rect2(0, 0, 100, 4), Color(1, 1, 1, 0.0), Color(1, 1, 1, 0.8))
	eq(m.triangle_count(), 4, "a gradient rect adds two triangles")
	var cols := _colors(m)
	eq(cols[4].a, 0.0, "the gradient starts clear at its left edge")
	check(is_equal_approx(cols[5].a, 0.8), "and reaches its colour at the right edge")
	_sane(m, "rect")
	m.rect(Rect2(0, 0, 0, 5), Color.RED)
	m.rect(Rect2(0, 0, 5, -1), Color.RED)
	eq(m.triangle_count(), 4, "an empty rect adds nothing")
	m.clear()
	check(m.is_empty(), "clear() empties it")


func test_ring_stays_within_its_band() -> void:
	var m := UIMesh.new()
	var c := Vector2(100, 100)
	m.ring(c, 44.0, 1.5, Color.WHITE)
	_sane(m, "ring")
	var lo := 1000.0
	var hi := 0.0
	for v in _verts(m):
		lo = minf(lo, v.distance_to(c))
		hi = maxf(hi, v.distance_to(c))
	var half := 0.75 + UIMesh.FEATHER
	check(lo >= 44.0 - half - 0.05, "the inner feather edge is %.2f px from the centre (>= %.2f)" % [lo, 44.0 - half])
	check(hi <= 44.0 + half + 0.05, "the outer feather edge is %.2f px from the centre (<= %.2f)" % [hi, 44.0 + half])
	# antialiased: a ramp to alpha 0 on each side of an opaque core
	var clear := 0
	var solid := 0
	for col in _colors(m):
		if col.a == 0.0:
			clear += 1
		elif col.a == 1.0:
			solid += 1
	eq(clear, solid, "as many feather vertices as core vertices")
	eq(m.vertex_count(), UIMesh.CIRCLE_SEGMENTS * 4, "four vertices per ring point")


func test_stroke_width_and_joins() -> void:
	var m := UIMesh.new()
	m.line(Vector2(0, 0), Vector2(100, 0), 6.0, Color.WHITE) # a hard-edged bar like draw_line
	var b := _bounds(m)
	check(is_equal_approx(b.size.y, 6.0) and is_equal_approx(b.size.x, 100.0), "a bar is 100 x 6 with butt ends, got %s" % str(b.size))
	eq(m.vertex_count(), 4, "a hard bar has no feather")
	var a := UIMesh.new()
	a.stroke(PackedVector2Array([Vector2(0, 0), Vector2(50, 0), Vector2(50, 50)]), 4.0, Color.WHITE)
	_sane(a, "chevron")
	var ab := _bounds(a)
	check(ab.size.x <= 50.0 + 2.0 + UIMesh.FEATHER + 0.01, "a 90 degree corner's miter stays within half a width: %s" % str(ab))
	var hair := UIMesh.new()
	hair.stroke(PackedVector2Array([Vector2(0, 0), Vector2(0, 0), Vector2(10, 0)]), 2.0, Color.WHITE)
	_sane(hair, "repeated point")
	eq(hair.vertex_count(), 8, "a repeated point is dropped")
	var u := UIMesh.new()
	u.stroke(PackedVector2Array([Vector2(0, 0), Vector2(10, 0), Vector2(0, 0)]), 2.0, Color.WHITE)
	_sane(u, "U-turn")
	for v in _verts(u):
		check(is_finite(v.x) and is_finite(v.y), "a U-turn makes no infinite miter")


func test_disc_polygon_arc() -> void:
	var m := UIMesh.new()
	m.disc(Vector2(10, 10), 20.0, Color.BLACK)
	eq(m.vertex_count(), UIMesh.CIRCLE_SEGMENTS + 1, "a hard disc is a fan")
	var b := _bounds(m)
	check(absf(b.size.x - 40.0) < 0.1, "the disc is 40 px wide, got %.2f" % b.size.x)
	m.clear()
	m.disc(Vector2.ZERO, 20.0, Color.BLACK, true)
	_sane(m, "soft disc")
	check(_bounds(m).size.x <= 41.01 and _bounds(m).size.x >= 40.9, "a soft disc reaches half a pixel past its radius")
	m.clear()
	m.diamond(Vector2(5, 5), 4.0, 2.0, Color.WHITE)
	eq(m.triangle_count(), 2, "a diamond is two triangles")
	m.clear()
	m.arc(Vector2.ZERO, 10.0, PI, TAU, 2.5, Color.WHITE, 24)
	_sane(m, "half arc")
	eq(m.vertex_count(), 25 * 4, "an open arc has segments + 1 points")
	m.clear()
	m.polygon(PackedVector2Array([Vector2.ZERO, Vector2(1, 0)]), Color.WHITE)
	check(m.is_empty(), "two points are not a polygon")


func test_empty_mesh_draws_nothing() -> void:
	var m := UIMesh.new()
	var host := Control.new()
	m.draw(host) # no surface, no draw command, no error
	host.free()
	check(m.is_empty(), "still empty")


## Every icon the HUD and its overlays use builds its mesh in every state, and the icon adds strokes to the bezel.
func test_icon_button_builds_one_mesh_per_state() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	await tree.process_frame # the runner is still inside the root's _ready: wait before adding to it
	var bezel := IconButton.new()
	bezel.size = Vector2(96, 96)
	bezel.icon_id = "none" # no icon: only the bezel
	tree.root.add_child(bezel)
	var buttons: Array[IconButton] = [bezel]
	for id: String in ICONS:
		var b := IconButton.make(id, 92)
		b.size = Vector2(96, 96)
		tree.root.add_child(b)
		buttons.append(b)
	await tree.process_frame
	await tree.process_frame
	var bezel_tris := (bezel.get("_mesh") as UIMesh).triangle_count()
	check(bezel_tris > 100, "the bezel alone is a disc and two rings (%d triangles)" % bezel_tris)
	for k in range(1, buttons.size()):
		var b := buttons[k]
		var m := b.get("_mesh") as UIMesh
		check(m.triangle_count() > bezel_tris, "%s draws its icon on the bezel (%d triangles)" % [b.icon_id, m.triangle_count()])
		_sane(m, b.icon_id)
		# the states the HUD uses: active (lit), disabled, a badge, a count
		b.active = true
		b.badge = "!"
		b.count = 12
		await tree.process_frame
		_sane(m, b.icon_id + " lit with badge and count")
		b.disabled = true
		await tree.process_frame
		_sane(m, b.icon_id + " disabled")
	# the item in hand: the bezel's mesh, the picture, then the ring and count in a second mesh
	var bag := buttons[buttons.size() - 1]
	bag.active = false
	bag.disabled = false
	bag.picture = ImageTexture.create_from_image(Image.create(8, 8, false, Image.FORMAT_RGBA8))
	bag.count = 3
	await tree.process_frame
	check((bag.get("_mesh_top") as UIMesh).triangle_count() > 0, "a picture in hand has its ring and count mesh")
	for b in buttons:
		b.queue_free()
	await tree.process_frame


## The banner's band, hairlines, flourishes and rule are one mesh that fits inside the banner.
func test_banner_ornaments_are_one_mesh() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	await tree.process_frame
	var b := UIBanner.new()
	b.setup(26, 26)
	tree.root.add_child(b)
	b.set_title("Laboratory bench")
	b.set_subtitle("A story caption under the view title")
	b.fit(1200.0)
	await tree.process_frame
	await tree.process_frame
	var m := b.get("_mesh") as UIMesh
	check(m.triangle_count() >= 10, "band, hairlines and rule: %d triangles" % m.triangle_count())
	_sane(m, "banner")
	var r := _bounds(m)
	check(r.position.x >= -0.01 and r.position.y >= -0.01 and r.end.x <= b.size.x + 0.01 and r.end.y <= b.size.y + 0.01,
		"the mesh stays inside the banner: %s in %s" % [str(r), str(b.size)])
	b.queue_free()
	await tree.process_frame
