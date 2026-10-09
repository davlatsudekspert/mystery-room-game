class_name RoomBase
extends Node3D
## Shared machinery for chapter rooms from Chapter 2 on:
## - spawning models with hotspots;
## - the view-stack camera and touch input;
## - raycast tap resolution that prefers the smallest interactive part;
## - reach and focus rules, using items on hotspots;
## - Android back handling and the HUD binding.
## A chapter room overrides the hooks in the "hooks" section and renders its logic state itself.
## (Chapter 1's Lab7Room predates this class and keeps its own copy of the same code.)

## Small props don't cast shadows: they are barely visible, and every caster costs a shadow pass on phones.
const SMALL_CASTER_M := 0.3
## A smaller interactive part wins over a bigger one if it lies at most this far behind the first hit.
const DEPTH_WINDOW_M := 0.18

var logic: RoomLogic
var models: Dictionary = {} # id -> Node3D
var _roots: Dictionary = {} # Node3D -> id
var cam: RoomCamera
var touch: TouchInput
var hud: Node
var lights: Dictionary = {}
var env: Environment
var capture_mode := false # set by QA capture scripts: no intro, no input
var _ending := false


# ====================================================================== hooks (override)
## The main free-look view; Back at this view opens the pause menu.
func main_root() -> String:
	return "hall"


## Camera view that belongs to a hotspot (tapping the hotspot from afar moves the camera there).
func hotspot_view(_hs: String) -> String:
	return ""


## view -> views "inside" it, from which the same hotspot is still directly operable.
func deeper_views() -> Dictionary:
	return {}


## Translation key for the title shown at a view (may depend on the state).
func view_caption(_view_id: String) -> String:
	return ""


## The logic target name for using the selected item on this hotspot/part ("" = not a target).
func use_target(_hs: String, _part: String) -> String:
	return ""


## Handle a tap on a hotspot that is within reach.
func interact(_hs: String, _part: String, _r: Dictionary) -> void:
	pass


## A tap that hit a part without a hotspot (shards, echoes, loose items). Return true if handled.
func tap_special(_part: String, _r: Dictionary) -> bool:
	return false


## Called when a drag starts on a part (for knobs/dials that can be dragged). Return true to capture it.
func drag_part_started(_part: String) -> bool:
	return false


## Captured drag movement (pixels).
func drag_part(_rel: Vector2) -> void:
	pass


# ====================================================================== construction helpers
func make_environment(bg: Color, ambient: Color, ambient_energy: float, fog_color: Color, fog_density: float) -> void:
	var we := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = bg
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = ambient
	env.ambient_light_energy = ambient_energy
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.1
	env.fog_enabled = fog_density > 0.0
	env.fog_light_color = fog_color
	env.fog_density = fog_density
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 0.92
	we.environment = env
	add_child(we)


func spawn(id: String, model: String, pos: Vector3, yaw: float, hotspot: String, mode: String) -> Node3D:
	var n := ModelUtil.spawn(model, self, Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)), pos), mode)
	if n == null:
		return null
	n.name = id
	models[id] = n
	_roots[n] = id
	n.set_meta("hotspot", hotspot)
	tune_shadows(n)
	return n


func tune_shadows(n: Node3D) -> void:
	for mi in ModelUtil.find_meshes(n):
		if mi.mesh == null:
			continue
		var sz := mi.mesh.get_aabb().size
		if maxf(sz.x, maxf(sz.y, sz.z)) < SMALL_CASTER_M:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func part(model_id: String, part_name: String) -> Node3D:
	return ModelUtil.find(models.get(model_id), part_name)


## A box-shaped tap target attached to `parent` (local coordinates).
func add_tap_area(parent: Node3D, size: Vector3, hotspot: String, part_name: String, offset: Vector3 = Vector3.ZERO) -> StaticBody3D:
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	cs.position = offset
	body.add_child(cs)
	body.set_meta("part", part_name)
	body.set_meta("hotspot", hotspot)
	parent.add_child(body)
	return body


## Show or hide a node together with its tap colliders.
func set_present(n: Node3D, on: bool) -> void:
	if n == null:
		return
	n.visible = on
	for body in n.find_children("*", "StaticBody3D", true, false):
		(body as StaticBody3D).collision_layer = 1 if on else 0


func build_camera() -> void:
	cam = RoomCamera.new()
	cam.near = 0.03
	cam.far = 40.0
	add_child(cam)
	cam.view_changed.connect(_on_view_changed)


func build_input() -> void:
	touch = TouchInput.new()
	add_child(touch)
	touch.tapped.connect(_on_tap)
	touch.dragged.connect(_on_drag)
	touch.drag_started.connect(_on_drag_started)
	touch.drag_ended.connect(func(_p: Vector2) -> void: _drag_captured = false)
	touch.pinched.connect(func(f: float) -> void: cam.zoom(f))
	touch.two_finger_tap.connect(go_back)


func build_hud() -> void:
	hud = (load("res://src/ui/hud.gd") as GDScript).new()
	add_child(hud)
	hud.call("bind", self)


# ====================================================================== back / navigation
## Android back / Escape: overlay → selected item → camera step back → other root → pause menu.
func handle_back() -> void:
	if hud.call("handle_back") or _ending:
		return
	if logic.selected != "":
		logic.select_item("")
		return
	if cam.is_root() and cam.current() == main_root():
		hud.call("show_pause")
		return
	go_back()


func go_back() -> void:
	if _ending:
		return
	if cam.is_root():
		if cam.current() != main_root():
			cam.go(main_root())
		return
	cam.back()


# ====================================================================== input
var _drag_captured := false


func _on_drag_started(pos: Vector2) -> void:
	_drag_captured = false
	if cam.transitioning:
		return
	var hit := raycast(pos)
	if not hit.is_empty():
		_drag_captured = drag_part_started(resolve(hit)["part"])


func _on_drag(rel: Vector2, _pos: Vector2) -> void:
	if _drag_captured:
		drag_part(rel)
		return
	cam.free_look(rel)


## Collects every hit along the tap ray and prefers the smallest interactive part within a short depth
## window behind the first surface, so small controls win over the coarse boxes of the furniture they sit on.
func raycast(screen: Vector2) -> Dictionary:
	var from := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var space := get_world_3d().direct_space_state
	var exclude: Array[RID] = []
	var hits: Array[Dictionary] = []
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(from, from + dir * 30.0)
		q.exclude = exclude
		var h := space.intersect_ray(q)
		if h.is_empty():
			break
		hits.append(h)
		exclude.append(h["rid"])
	if hits.is_empty():
		return {}
	var first_d := from.distance_to(hits[0]["position"])
	var best: Dictionary = hits[0]
	var best_vol := INF
	var best_d := INF
	for h in hits:
		var d := from.distance_to(h["position"])
		if d - first_d > DEPTH_WINDOW_M:
			break
		var col: Node = h["collider"]
		if str(col.get_meta("part", "")) == "":
			continue
		var vol := _collider_volume(col)
		if best_d == INF or (d - best_d < 0.03 and vol < best_vol):
			if best_d == INF:
				best_d = d
			best_vol = vol
			best = h
	return best


func _collider_volume(col: Node) -> float:
	for c in col.get_children():
		if c is CollisionShape3D and (c as CollisionShape3D).shape is BoxShape3D:
			var sz := ((c as CollisionShape3D).shape as BoxShape3D).size
			return sz.x * sz.y * sz.z
	return 1.0


## -> {"hotspot", "part", "model", "pos"}
func resolve(hit: Dictionary) -> Dictionary:
	var out := {"hotspot": "", "part": "", "model": "", "pos": hit.get("position", Vector3.ZERO)}
	var col: Node = hit.get("collider")
	if col == null:
		return out
	out["part"] = str(col.get_meta("part", ""))
	if col.has_meta("hotspot"):
		out["hotspot"] = str(col.get_meta("hotspot"))
	var n := col
	while n != null and n != self:
		if _roots.has(n):
			out["model"] = _roots[n]
			if out["hotspot"] == "":
				out["hotspot"] = str(n.get_meta("hotspot", ""))
			break
		n = n.get_parent()
	return out


func _on_tap(screen: Vector2) -> void:
	if cam.transitioning or _ending:
		return
	var hit := raycast(screen)
	if hit.is_empty():
		return
	var r := resolve(hit)
	var p: String = r["part"]
	var hs: String = r["hotspot"]
	if tap_special(p, r):
		return
	if hs == "":
		return
	if logic.selected != "" and not ItemDB.is_tool(logic.selected):
		var target := use_target(hs, p)
		if target != "" and in_reach(hs):
			var ev: Array = logic.call("use_item_on", logic.selected, target)
			if ev.has("nothing_happens"):
				hud.call("message", tr("msg.nothing"))
				AudioManager.ui("ui_error")
			else:
				logic.select_item("")
			return
	if not in_reach(hs):
		focus(hs)
		return
	interact(hs, p, r)


## A hotspot is directly operable from its own view or any deeper view of the same object.
func in_reach(hs: String) -> bool:
	var v := hotspot_view(hs)
	var cur := cam.current()
	if v == "" or cur == v:
		return true
	return (deeper_views().get(v, []) as Array).has(cur)


func focus(hs: String) -> void:
	var v := hotspot_view(hs)
	if v != "":
		cam.go(v)
		AudioManager.ui("ui_tap")


func _on_view_changed(id: String) -> void:
	hud.call("set_view", id, cam.is_root(), view_caption(id))
	view_changed_hook(id)


## Override for per-view lighting, visibility culling and reveals.
func view_changed_hook(_id: String) -> void:
	pass
