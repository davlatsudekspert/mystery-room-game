class_name HandLayer
extends Node3D
## Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md section 12, phase 1: the selected tool floats at the bottom right of the
## room camera ("floating item first", the glove comes after the first playtest). It is a child of the room camera, so it
## needs no second viewport; data-driven by HoldTable (an item without a row shows nothing); never blocks a tap (no
## colliders, nothing in the physics layer, no Control); keeps its own fixed field of view (it does not grow with the
## camera's magnify or pinch); hidden while an overlay or a banner is up, in the room's root view, with Settings
## "hands" off, and in safe graphics. The UV lamp's beam cone follows the finger; the mallet swings on strike().
## Budget: one item model (a few meshes) plus one cone mesh, no shadows, no lights.

const RISE_SECONDS := 0.35

var room: Node3D
var logic: RoomLogic
var cam: RoomCamera
var item_id := ""
var shown := false
var _holder: Node3D
var _model: Node3D
var _beam: MeshInstance3D
var _base_pos := Vector3.ZERO
var _base_rot := Vector3.ZERO
var _base_scale := 1.0
var _pointer := Vector2(-1, -1)
var _tween: Tween
var _t := 0.0
var _strike := 0.0
var _rise := 1.0 # 0 = below the frame, 1 = at rest
var _target_on := false
var _tool_last := ""


func _init(r: Node3D) -> void:
	room = r
	name = "HandLayer"


func _ready() -> void:
	logic = room.get("logic")
	cam = room.get("cam")
	_holder = Node3D.new()
	add_child(_holder)
	_beam = MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.01
	cone.bottom_radius = 0.22
	cone.height = 2.0
	cone.radial_segments = 20
	_beam.mesh = cone
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(0.55, 0.3, 1.0, 0.16)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	_beam.material_override = m
	_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_beam.visible = false
	add_child(_beam)
	GameState.events.connect(_on_events)
	Settings.changed.connect(func(_k: String) -> void: _refresh())
	_refresh()


func _input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch or ev is InputEventScreenDrag or ev is InputEventMouseMotion or ev is InputEventMouseButton:
		_pointer = (ev as InputEventMouse).position if ev is InputEventMouse else (ev as InputEventScreenDrag).position if ev is InputEventScreenDrag else (ev as InputEventScreenTouch).position


func _on_events(ev: Array[String]) -> void:
	for e in ev:
		if e.begins_with("selected"):
			_refresh()
			var tool_now := HoldTable.audio_tool(logic.selected) if logic.selected != "" else ""
			if tool_now != "" and tool_now != _tool_last:
				AudioManager.sfx("hand_equip_" + tool_now)
			elif tool_now == "" and _tool_last != "":
				AudioManager.sfx("hand_putaway_" + _tool_last)
			_tool_last = tool_now
		elif e.begins_with("item_added:"):
			var t := HoldTable.audio_tool(e.substr(11))
			if t != "":
				AudioManager.sfx("hand_pickup_" + t)
		elif e.begins_with("tap:") and HoldTable.row(item_id).get("strike", false):
			strike()


## The item in hand changed (or a setting did): rebuild the viewmodel.
func _refresh() -> void:
	var id: String = logic.selected if logic != null else ""
	var wanted := bool(Settings.get_value("hands")) and not bool(Settings.get_value("safe_graphics")) and HoldTable.has_hand(id)
	if wanted and id != item_id:
		_build(id)
	elif not wanted:
		item_id = ""
		if _model != null:
			_model.queue_free()
			_model = null
	_target_on = wanted
	if wanted:
		_rise = 0.0


func _build(id: String) -> void:
	item_id = id
	if _model != null:
		_model.queue_free()
	var row := HoldTable.row(id)
	_model = ModelUtil.spawn(str(row.get("model", ItemDB.model_path(id))), _holder, Transform3D.IDENTITY, "none")
	if _model == null:
		_target_on = false
		return
	for mi in ModelUtil.find_meshes(_model):
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ItemDress.apply(id, _model, logic)
	_base_pos = row["pos"]
	_base_rot = row["rot"]
	_base_scale = float(row.get("scale", 1.0))
	_model.scale = Vector3.ONE * _base_scale
	_model.rotation_degrees = _base_rot
	_rise = 0.0


## The mallet's swing (0.2 s); the room calls it when a tap rings a pipe.
func strike() -> void:
	_strike = 1.0


func _process(delta: float) -> void:
	var show_now := _target_on and _model != null and _may_show()
	if show_now != shown:
		shown = show_now
		visible = shown
	if not shown:
		return
	_t += delta
	_rise = minf(1.0, _rise + delta / RISE_SECONDS)
	_strike = maxf(0.0, _strike - delta / 0.2)
	var calm := bool(Settings.get_value("reduce_motion"))
	# the hand keeps its own field of view: scale about the camera by the ratio of the tangents
	var k := tan(deg_to_rad(cam.fov * 0.5)) / tan(deg_to_rad(HoldTable.REF_FOV * 0.5))
	var ease_up := 1.0 - pow(1.0 - _rise, 3.0)
	var sway := Vector3.ZERO if calm else Vector3(sin(_t * 0.9) * 0.004, sin(_t * 1.3) * 0.003, 0.0)
	_holder.position = (_base_pos + sway + Vector3(0.0, -0.3 * (1.0 - ease_up), 0.0)) * k
	_holder.scale = Vector3.ONE * k
	_model.rotation_degrees = _base_rot + Vector3(-55.0 * sin(_strike * PI), 0.0, 0.0)
	_update_beam(k)


func _update_beam(k: float) -> void:
	var row := HoldTable.row(item_id)
	var on := bool(row.get("beam", false)) and _pointer.x >= 0.0
	_beam.visible = on
	if not on:
		return
	var tip := _holder.position + Vector3(-0.02, 0.1, -0.12) * k
	var dir := cam.project_local_ray_normal(_pointer)
	var end := dir * 1.6
	var axis := (end - tip)
	if axis.length() < 0.01:
		_beam.visible = false
		return
	# a cone from the tip (narrow) to the end (wide): the cylinder's +y is the wide end after the flip
	var up := axis.normalized()
	var basis := Basis.looking_at(up, Vector3.UP) * Basis(Vector3.RIGHT, deg_to_rad(90.0))
	_beam.transform = Transform3D(basis.scaled(Vector3(1, axis.length() / 2.0, 1)), tip + axis * 0.5)


## Where the layer must not show: overlays, banners, the cinematics, the room's root view.
func _may_show() -> bool:
	var hud: Node = room.get("hud")
	if hud == null:
		return false
	if hud.get("_overlay") != null or bool(hud.get("_busy")) or bool(hud.get("_msg_on")):
		return false
	if cam.transitioning or cam.is_root():
		return false
	return true
