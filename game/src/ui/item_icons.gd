class_name ItemIcons
extends Node
## Renders inventory icons from the 3D item models in an off-screen SubViewport (no hand-made icon art).

signal icon_ready(id: String, tex: Texture2D)

const SIZE := 192

var _vp: SubViewport
var _cam: Camera3D
var _pivot: Node3D
var _cache: Dictionary = {}
var _queue: Array[String] = []
var _busy := false
var logic: RoomLogic # optional: lets item variations (punched holes) follow the state


func _ready() -> void:
	_vp = SubViewport.new()
	_vp.size = Vector2i(SIZE, SIZE)
	_vp.transparent_bg = true
	_vp.own_world_3d = true
	_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_vp.msaa_3d = Viewport.MSAA_4X if CrashGuard.safe_level() == 0 else Viewport.MSAA_DISABLED
	add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("b3aa9b")
	env.ambient_light_energy = 1.1
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	_cam = Camera3D.new()
	_cam.fov = 30.0
	_vp.add_child(_cam)
	var key := DirectionalLight3D.new()
	key.light_energy = 2.4
	key.light_color = Color("ffe4c4")
	_vp.add_child(key)
	key.look_at_from_position(Vector3(1, 1.4, 1.2), Vector3.ZERO, Vector3.UP)
	var rim := DirectionalLight3D.new()
	rim.light_energy = 1.4
	rim.light_color = Color("a9c7ff")
	_vp.add_child(rim)
	rim.look_at_from_position(Vector3(-1.2, 0.6, -1.0), Vector3.ZERO, Vector3.UP)
	var fill := DirectionalLight3D.new()
	fill.light_energy = 0.9
	fill.light_color = Color("ffffff")
	_vp.add_child(fill)
	fill.look_at_from_position(Vector3(0, 0.2, 2.0), Vector3.ZERO, Vector3.UP)
	_pivot = Node3D.new()
	_vp.add_child(_pivot)


func get_icon(id: String) -> Texture2D:
	if _cache.has(id):
		return _cache[id]
	if not _queue.has(id):
		_queue.append(id)
		_pump()
	return null


func _pump() -> void:
	if _busy or _queue.is_empty():
		return
	_busy = true
	var id: String = _queue.pop_front()
	for c in _pivot.get_children():
		c.queue_free()
	var n := ModelUtil.spawn(ItemDB.model_path(id), _pivot, Transform3D.IDENTITY, "none")
	if n == null:
		_busy = false
		_pump()
		return # model not built yet: the slot shows the item's name instead
	if n != null:
		_pivot.rotation = Vector3.ZERO
		n.rotation.x = deg_to_rad(ItemDB.view_tilt(id))
		ItemDress.apply(id, n, logic)
		var aabb := _aabb(n)
		var radius := maxf(0.01, aabb.size.length() * 0.5)
		n.position = -aabb.get_center()
		_pivot.rotation = Vector3(deg_to_rad(18), deg_to_rad(-32), 0)
		var dist := radius / sin(deg_to_rad(_cam.fov * 0.5)) * 1.02
		_cam.position = Vector3(0, 0, dist)
		_cam.look_at(Vector3.ZERO, Vector3.UP)
		_cam.near = maxf(0.001, dist - radius * 2.0)
		_cam.far = dist + radius * 2.0
		if id == "uv_lamp":
			_tint(n, Color(0.75, 0.6, 1.0))
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := _vp.get_texture().get_image()
	var tex := ImageTexture.create_from_image(img)
	_cache[id] = tex
	icon_ready.emit(id, tex)
	_busy = false
	_pump()


func _tint(n: Node, c: Color) -> void:
	var l := OmniLight3D.new()
	l.light_color = c
	l.light_energy = 1.5
	l.omni_range = 1.0
	n.add_child(l)


static func _aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	for mi in ModelUtil.find_meshes(n):
		var a := mi.global_transform * mi.get_aabb() if mi.is_inside_tree() else mi.transform * mi.get_aabb()
		if first:
			out = a
			first = false
		else:
			out = out.merge(a)
	return out
