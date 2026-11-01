class_name ArchiveKit
extends RefCounted
## Small scene helpers the Chapter 2 expansion's zone builders share (ArchiveCell, ArchiveCold; the Pump Room keeps its own
## copies). Static, no state: tweened part rotations, pick-up colliders, flat decal materials, lamps, procedural icons.


## Turns part `n` about `axis` by `deg` from its rest transform (remembered on first use), tweened on `owner`'s tree.
## `tweens` is the caller's own dictionary (instance id -> Tween) so a new call replaces a running one.
static func rot(owner: Node, tweens: Dictionary, n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float) -> void:
	if n == null:
		return
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	var base: Transform3D = n.get_meta("rest")
	var target := Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin)
	_go(owner, tweens, n, target, animated, dur)


## Turns part `n` to an absolute basis relative to its rest transform: `local` is applied on top of the rest basis.
## Unlike rot() this takes a Basis, so a compound turn (a sheet turned and flipped) tweens as one move.
static func pose(owner: Node, tweens: Dictionary, n: Node3D, local: Basis, offset: Vector3, animated: bool, dur: float) -> void:
	if n == null:
		return
	if not n.has_meta("rest"):
		n.set_meta("rest", n.transform)
	var base: Transform3D = n.get_meta("rest")
	_go(owner, tweens, n, Transform3D(base.basis * local, base.origin + offset), animated, dur)


static func _go(owner: Node, tweens: Dictionary, n: Node3D, target: Transform3D, animated: bool, dur: float) -> void:
	var k := n.get_instance_id()
	if tweens.has(k) and (tweens[k] as Tween).is_valid():
		(tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var tw := owner.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)), from.origin.lerp(target.origin, t)), 0.0, 1.0, dur)
	tweens[k] = tw


## A box collider around a small loose item (a pick-up): the item's meshes' bounds in its own space, padded.
static func item_body(item: Node3D, hotspot: String, part: String, pad: float = 0.05) -> StaticBody3D:
	var inv := item.global_transform.affine_inverse() if item.is_inside_tree() else Transform3D.IDENTITY
	var box := AABB()
	var first := true
	for mi in ModelUtil.find_meshes(item):
		var xf := inv * mi.global_transform if item.is_inside_tree() else mi.transform
		var a := xf * mi.get_aabb()
		box = a if first else box.merge(a)
		first = false
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = (box.size + Vector3.ONE * pad).max(Vector3.ONE * 0.1)
	cs.shape = shape
	cs.position = box.get_center()
	body.add_child(cs)
	body.set_meta("part", part)
	body.set_meta("hotspot", hotspot)
	item.add_child(body)
	return body


## Removes the tap colliders ModelUtil built on a mesh (decals, curtains and the like must never take a tap or block a ray).
static func drop_colliders(n: Node) -> void:
	if n == null:
		return
	for c in n.get_children():
		if c is StaticBody3D:
			n.remove_child(c)
			c.queue_free()


## Renames a part and the tap meta of its colliders (three sheets share the model's part names; each needs its own).
static func rename_part(n: Node3D, new_name: String) -> void:
	if n == null:
		return
	n.name = new_name
	for c in n.get_children():
		if c is StaticBody3D:
			c.set_meta("part", new_name)


## A flat, lit-by-itself decal material (paper in lamplight, a lit cell grid): no shadows, no lights needed.
static func decal_material(tex: Texture2D, alpha: bool, priority: int = 0, nearest: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	if alpha:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.render_priority = priority
	if nearest:
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	return m


static func quad(parent: Node3D, size: Vector2, pos: Vector3, mat: Material, nm: String) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = size
	mi.mesh = qm
	mi.material_override = mat
	mi.position = pos
	mi.name = nm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


static func omni(parent: Node3D, pos: Vector3, color: Color, energy: float, rng: float, atten: float = 1.0) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = color
	l.light_energy = energy
	l.omni_range = rng
	l.omni_attenuation = atten
	l.shadow_enabled = false
	l.position = pos
	parent.add_child(l)
	return l


## A PackedByteArray of cell flags (row-major, `cols` per row) as an RGBA image: `on` / `off` colours per cell, a thin gap.
static func cell_image(bits: PackedByteArray, cols: int, rows: int, px: int, on: Color, off: Color, gap: int = 1) -> Image:
	var img := Image.create(cols * px, rows * px, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for r in rows:
		for c in cols:
			var col := on if bits[r * cols + c] == 1 else off
			if col.a <= 0.0:
				continue
			img.fill_rect(Rect2i(c * px + gap, r * px + gap, px - 2 * gap, px - 2 * gap), col)
	return img


# ---------------------------------------------------------------------- procedural icons (no text, language neutral)
static func disc(img: Image, c: Vector2, r: float, col: Color) -> void:
	for y in range(maxi(0, int(c.y - r) - 1), mini(img.get_height(), int(c.y + r) + 2)):
		for x in range(maxi(0, int(c.x - r) - 1), mini(img.get_width(), int(c.x + r) + 2)):
			var d := Vector2(x, y).distance_to(c)
			if d <= r:
				var a := clampf(r - d, 0.0, 1.0)
				var old := img.get_pixel(x, y)
				img.set_pixel(x, y, old.lerp(col, a * col.a))


static func ring(img: Image, c: Vector2, r: float, w: float, col: Color, a0: float = 0.0, a1: float = TAU) -> void:
	for y in range(maxi(0, int(c.y - r) - 1), mini(img.get_height(), int(c.y + r) + 2)):
		for x in range(maxi(0, int(c.x - r) - 1), mini(img.get_width(), int(c.x + r) + 2)):
			var p := Vector2(x, y) - c
			var d := p.length()
			if d > r + 0.5 or d < r - w - 0.5:
				continue
			var ang := fposmod(p.angle(), TAU)
			if ang < a0 or ang > a1:
				continue
			var cover := clampf(minf(r - d, d - (r - w)) + 0.5, 0.0, 1.0)
			img.set_pixel(x, y, img.get_pixel(x, y).lerp(col, cover * col.a))


static func line(img: Image, a: Vector2, b: Vector2, w: float, col: Color) -> void:
	var lo := Vector2(minf(a.x, b.x) - w, minf(a.y, b.y) - w).floor().max(Vector2.ZERO)
	var hi := Vector2(maxf(a.x, b.x) + w, maxf(a.y, b.y) + w).ceil().min(Vector2(img.get_width() - 1, img.get_height() - 1))
	for y in range(int(lo.y), int(hi.y) + 1):
		for x in range(int(lo.x), int(hi.x) + 1):
			var p := Vector2(x, y)
			var d := Geometry2D.get_closest_point_to_segment(p, a, b).distance_to(p)
			if d <= w * 0.5 + 0.5:
				var cover := clampf(w * 0.5 + 0.5 - d, 0.0, 1.0)
				img.set_pixel(x, y, img.get_pixel(x, y).lerp(col, cover * col.a))


static func arrow_head(img: Image, tip: Vector2, dir: Vector2, size: float, col: Color) -> void:
	var n := dir.normalized()
	var side := Vector2(-n.y, n.x)
	line(img, tip, tip - n * size + side * size * 0.6, size * 0.34, col)
	line(img, tip, tip - n * size - side * size * 0.6, size * 0.34, col)
