extends Node3D
## Chapter 1 scene: assembles Laboratory 7 + the darkroom from models, owns lights/camera/input,
## routes taps to Lab7Logic and lets Lab7Visuals render the resulting state.

const BEAM_Y := 1.15
const UV_REVEAL_TIME := 0.35

## model -> [position, yaw degrees (front +Z = 0), hotspot id, collider mode]
const LAYOUT := {
	"room_lab7": [Vector3.ZERO, 0.0, "", "static"],
	"door_lab7": [Vector3(3.0, 0, 0.9), -90.0, "door", "parts"],
	"desk": [Vector3(-0.5, 0, -2.1), 0.0, "desk", "parts"],
	"chair": [Vector3(-0.35, 0, -1.3), 168.0, "", "parts"],
	"flip_clock": [Vector3(-1.0, 0.78, -2.25), 8.0, "clock", "parts"],
	"notebook": [Vector3(-0.28, 0.7934, -1.98), -12.0, "notebook", "parts"],
	"desk_lamp": [Vector3(-1.18, 0.78, -2.32), 25.0, "desk", "parts"],
	"filing_cabinet": [Vector3(-2.6, 0, -2.2), 0.0, "filing", "parts"],
	"bookshelf": [Vector3(-3.1, 0, -1.15), 90.0, "bookshelf", "parts"],
	"gear_box": [Vector3(-1.85, 0.545, -2.18), 0.0, "gearbox", "parts"],
	"chalkboard": [Vector3(-3.0, 1.0, 1.05), 90.0, "chalkboard", "parts"],
	"lumen_projector": [Vector3(-2.3, 0, 1.6), 90.0, "projector", "parts"],
	"lab_bench": [Vector3(-0.3, 0, 2.15), 180.0, "bench", "parts"],
	"radio": [Vector3(0.55, 0.92, 2.2), 180.0, "radio", "parts"],
	"poster_frame": [Vector3(-0.3, 1.9, 2.5), 180.0, "poster", "parts"],
	"wall_safe": [Vector3(2.2, 1.25, 2.5), 180.0, "safe", "parts"],
	"panel7": [Vector3(3.0, 1.45, -1.3), -90.0, "panel", "parts"],
	"coat_rack": [Vector3(2.35, 0, -2.25), -30.0, "coat", "parts"], # clear of Panel 7's open door as seen from the room
	"pendant_lamp": [Vector3(-0.6, 3.4, -0.6), 0.0, "", "none"],
	"mirror_stand": [Vector3(1.6, 0, 1.6), 0.0, "mirror_a", "parts"],
	"light_sensor": [Vector3(3.0, 1.15, 0.12), -90.0, "lock", "parts"],
	"evidence_board": [Vector3(-4.8, 1.5, -0.6), 90.0, "evidence", "parts"],
	"shadow_lock": [Vector3.ZERO, 0.0, "shadow", "parts"],
	"darkroom_props": [Vector3.ZERO, 0.0, "", "parts"],
}

## Extra instances of a model: id -> [model, position, yaw, hotspot]
const EXTRA := {
	"pendant_lamp_2": ["pendant_lamp", Vector3(1.2, 3.4, 0.8), 0.0, ""],
	"mirror_stand_b": ["mirror_stand", Vector3(1.6, 0, 0.12), 0.0, "mirror_b"],
	"cc_microscope": ["cc0/vintage_microscope/vintage_microscope", Vector3(-0.35, 0.92, 2.32), 200.0, "bench"],
	"cc_tea": ["cc0/tea_set_01/tea_set_01", Vector3(0.05, 0.78, -2.22), -20.0, "desk"],
	"cc_spectacles": ["cc0/round_spectacles/round_spectacles", Vector3(-0.62, 0.78, -1.92), 35.0, "desk"],
	"cc_magnifier": ["cc0/magnifying_glass_01/magnifying_glass_01", Vector3(-0.78, 0.78, -2.0), -60.0, "desk"],
	"cc_bust": ["cc0/marble_bust_01/marble_bust_01", Vector3(-2.6, 1.32, -2.25), 15.0, "filing"],
	"cc_multimeter": ["cc0/retro_multimeter/retro_multimeter", Vector3(2.55, 0, -0.85), -100.0, ""],
	"cc_kettle": ["cc0/vintage_electric_kettle/vintage_electric_kettle", Vector3(1.05, 1.47, -2.45), 30.0, "window"],
	"cc_compass": ["cc0/seadogs_compass/seadogs_compass", Vector3(1.85, 1.47, -2.42), -40.0, "window"],
	"cc_stool": ["cc0/metal_stool_02/metal_stool_02", Vector3(0.25, 0, 1.45), 20.0, ""],
	"cc_gasmask": ["cc0/old_gas_mask/old_gas_mask", Vector3(2.2, 1.7, -2.4), 0.0, "coat"],
	"cc_drawer": ["cc0/vintage_wooden_drawer_01/vintage_wooden_drawer_01", Vector3(-1.85, 0, -2.25), 0.0, ""],
}

## Hotspot -> camera view id (tapping the hotspot from elsewhere moves the camera here)
const HOTSPOT_VIEW := {
	"door": "door", "desk": "desk", "clock": "clock", "notebook": "desk", "filing": "filing",
	"bookshelf": "bookshelf", "gearbox": "gearbox", "chalkboard": "chalkboard", "projector": "projector",
	"bench": "bench", "radio": "radio", "poster": "poster", "safe": "safe", "panel": "panel", "coat": "coat",
	"mirror_a": "mirror_a", "mirror_b": "mirror_b", "lock": "lock", "evidence": "evidence",
	"shadow": "shadow", "window": "window", "vials": "vials", "radiator": "radiator",
}
const HOTSPOT_CAPTION := {
	"door": "obj.door", "desk": "obj.desk", "clock": "obj.clock", "filing": "obj.filing",
	"bookshelf": "obj.bookshelf", "gearbox": "obj.gearbox", "chalkboard": "obj.chalkboard",
	"projector": "obj.projector", "bench": "obj.bench", "radio": "obj.radio", "poster": "obj.poster_view",
	"safe": "obj.safe", "panel": "obj.panel", "coat": "obj.coat", "mirror_a": "obj.mirror_a",
	"mirror_b": "obj.mirror_b", "lock": "obj.lock", "evidence": "obj.evidence", "shadow": "obj.shadow",
	"window": "obj.window", "vials": "obj.vials", "drawer": "obj.drawer", "books": "obj.bookshelf",
	"emblem": "obj.emblem", "cabinet": "obj.cabinet", "darkroom": "obj.darkroom", "sculpture": "obj.shadow",
	"projector_rings": "obj.projector", "desk_side": "obj.desk",
	"radiator": "obj.radiator", "drawing": "obj.drawing",
}

const BOOKCASE_HINGE := Vector3(-2.74, 0.0, -1.15)
const SHARD_SPOTS := {
	"under_desk": Vector3(-0.7, 0.011, -2.22), "bookshelf_top": Vector3(-2.85, 2.16, -0.3),
	"radiator": Vector3(1.78, 0.05, -2.33), "coat_pocket": Vector3(2.12, 1.07, -2.08),
	"darkroom": Vector3(-4.55, 0.011, 0.15),
}

var logic: Lab7Logic
var models: Dictionary = {} # id -> Node3D
var _roots: Dictionary = {} # Node3D -> id
var cam: RoomCamera
var touch: TouchInput
var hud: Node
var visuals: Lab7Visuals
var lights: Dictionary = {}
var env: Environment
var uv_light: SpotLight3D
var _uv_aim := Vector2.ZERO
var _uv_dwell := 0.0
var _uv_target := ""
var _ending := false
var capture_mode := false # set by QA capture script: no intro, no input
var _darkroom_seen := false
var _shard_nodes: Dictionary = {} # shard id -> Node3D
var _knob_drag := false # a drag that started on the radio tuning knob turns it
var _knob_acc := 0.0


func _ready() -> void:
	if GameState.logic == null or not GameState.logic is Lab7Logic:
		GameState.start_new("ch1")
	logic = GameState.logic
	GameState.in_game = true
	CrashGuard.detail("environment")
	_build_environment()
	_build_models()
	CrashGuard.detail("lights")
	_build_lights()
	_build_views()
	_hinge_bookcase()
	_place_lights_from_models()
	CrashGuard.detail("visuals")
	visuals = Lab7Visuals.new(self)
	add_child(visuals)
	_build_input()
	CrashGuard.detail("hud")
	_build_hud()
	_frame_fitted() # with the HUD's own free area, now that it exists
	get_viewport().size_changed.connect(_on_viewport_resized)
	add_child(PerfGuard.new())
	GameState.events.connect(_on_events)
	visuals.apply_state(false)
	_update_shards()
	_update_lighting(false)
	cam.go("lab", true)
	AudioManager.music("music_lab", 4.0)
	AudioManager.ambience("amb_lab_dark", true, -2.0)
	if logic.state["power_on"]:
		AudioManager.ambience("amb_power_hum", true, -8.0)
	if not capture_mode and logic.state["taken"].is_empty() and logic.inventory.is_empty():
		Lab7Intro.start(self) # the rain, the key, the cards, the door; a tap skips (src/rooms/lab7/lab7_intro.gd)
	elif not capture_mode and logic.is_complete():
		_resume_completed()
	elif not capture_mode and logic.state["door_open"]:
		_resume_choice()
	SceneManager.room_ready(self) # safe graphics before the first frame is drawn


func _exit_tree() -> void:
	GameState.in_game = false
	RenderingServer.global_shader_parameter_set("uv_light_on", 0.0)


# ====================================================================== construction
func _build_environment() -> void:
	var we := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("0b0d10")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("26383a")
	env.ambient_light_energy = 0.5
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.glow_enabled = true
	# A soft halo on real light sources only: the old 0.6 / 0.05 / 1.1 bloomed every lit enamel and brass surface
	# into a white patch (lamp shades, the projector lens, the panel lamps) and washed the close-ups out.
	env.glow_intensity = 0.4
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.35
	env.fog_enabled = true
	env.fog_light_color = Color("1b2a2b")
	env.fog_density = 0.012
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 0.92
	we.environment = env
	add_child(we)
	_apply_brightness("brightness")
	Settings.changed.connect(_apply_brightness) # a bound method: disconnected automatically with the room


func _spawn(id: String, model: String, pos: Vector3, yaw: float, hotspot: String, mode: String) -> Node3D:
	var n := ModelUtil.spawn(model, self, Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)), pos), mode)
	if n == null:
		return null
	n.name = id
	models[id] = n
	_roots[n] = id
	n.set_meta("hotspot", hotspot)
	_tune_shadows(n)
	return n


## Small props don't cast shadows (barely visible, costly on phones: every caster is redrawn per shadow pass).
func _tune_shadows(n: Node3D) -> void:
	for mi in ModelUtil.find_meshes(n):
		if mi.mesh == null:
			continue
		var sz := mi.mesh.get_aabb().size
		if maxf(sz.x, maxf(sz.y, sz.z)) < 0.3:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _build_models() -> void:
	for id: String in LAYOUT:
		var e: Array = LAYOUT[id]
		_spawn(id, id, e[0], e[1], e[2], e[3])
	for id: String in EXTRA:
		var e: Array = EXTRA[id]
		_spawn(id, e[0], e[1], e[2], e[3], "parts" if e[3] != "" else "none")
	# echo figure (finale only)
	var echo := _spawn("echo_leyla", "echo_leyla_sitting", Vector3(-0.4, 0, -1.33), 0.0, "", "none")
	if echo:
		var mat := ShaderMaterial.new()
		mat.shader = load("res://src/fx/echo.gdshader")
		for mi in ModelUtil.find_meshes(echo):
			mi.material_override = mat
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		echo.visible = false
	_build_backdrop()
	_build_uv_ink()
	_build_shards()
	# The radiator is part of the static room shell: give it a tap target of its own, so the low view where the
	# Lumen shard hides between its feet can be reached by tapping it (docs/models/architecture.md, "Radiator").
	var radiator := Node3D.new()
	radiator.name = "radiator_tap"
	add_child(radiator)
	radiator.position = Vector3(1.5, 0.45, -2.37)
	radiator.set_meta("hotspot", "radiator")
	models["radiator_tap"] = radiator
	_roots[radiator] = "radiator_tap"
	_add_tap_area(radiator, Vector3(0.84, 0.7, 0.16), "radiator", "IA_radiator")
	_add_panel_tap_areas()
	var dust := DustMotes.create(Vector3(2.8, 1.5, 2.3), 140)
	dust.position = Vector3(0, 1.6, 0)
	add_child(dust)


func _build_backdrop() -> void:
	# Moonlit valley seen through the window (unshaded so it reads as the bright outside).
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(4.0, 3.0)
	q.mesh = qm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = load("res://assets/textures/decals/window_night.jpg")
	m.albedo_color = Color(0.85, 0.9, 1.0)
	q.material_override = m
	q.position = Vector3(1.5, 2.2, -4.2)
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(q)


func _uv_quad(id: String, tex: String, size: Vector2, pos: Vector3, normal_yaw: float, use_tex: bool = true) -> MeshInstance3D:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = size
	q.mesh = qm
	var m := ShaderMaterial.new()
	m.shader = load("res://src/fx/uv_ink.gdshader")
	if tex != "":
		m.set_shader_parameter("ink", load(tex))
	m.set_shader_parameter("use_texture", use_tex)
	q.material_override = m
	q.position = pos
	q.rotation.y = deg_to_rad(normal_yaw)
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	q.name = "UV_" + id
	add_child(q)
	return q


func _build_uv_ink() -> void:
	# Leyla's fluorescent circle + arrow on the desk's east side, around the rosette.
	var mark := _uv_quad("desk_mark", "res://assets/textures/decals/uv_desk_mark.png", Vector2(0.34, 0.34),
		Vector3(0.262, 0.52, -2.05), 90.0)
	mark.set_meta("uv_target", "desk_mark")
	_add_tap_area(mark, Vector3(0.05, 0.34, 0.34), "desk_side", "UV_desk_mark")


func _build_shards() -> void:
	var spots := SHARD_SPOTS
	for id: String in spots:
		var shard := ModelUtil.spawn("lumen_shard", self, Transform3D(Basis(Vector3.UP, randf() * TAU), spots[id]), "none")
		var node: Node3D = shard
		if node == null:
			var mi := MeshInstance3D.new()
			var pm := PrismMesh.new()
			pm.size = Vector3(0.03, 0.06, 0.03)
			mi.mesh = pm
			add_child(mi)
			mi.position = spots[id]
			node = mi
		var m := ShaderMaterial.new()
		m.shader = load("res://src/fx/uv_ink.gdshader")
		m.set_shader_parameter("use_texture", false)
		m.set_shader_parameter("ink_color", Color(0.75, 0.95, 1.0))
		m.set_shader_parameter("strength", 2.4)
		m.set_shader_parameter("cone_cos", 0.96)
		for mi in ModelUtil.find_meshes(node):
			mi.material_override = m
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.name = "Shard_" + id
		node.set_meta("shard", id)
		_shard_nodes[id] = node
		_add_tap_area(node, Vector3(0.12, 0.12, 0.12), "", "Shard_" + id, false)


func _add_tap_area(parent: Node3D, size: Vector3, hotspot: String, part: String, local: bool = true,
		offset: Vector3 = Vector3.ZERO) -> void:
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	body.add_child(cs)
	body.set_meta("part", part)
	body.set_meta("hotspot", hotspot)
	parent.add_child(body)
	if not local:
		body.position = Vector3.ZERO
	body.position += offset


## Panel 7's switches are 3 cm levers 11 cm apart and the breaker a 6 cm fork: from the close-up that shows the
## whole plate they are 1–2 mm wide on a phone. Each gets a tap area the width of its bay (the bakelite base, the
## numeral under it and the trace above) and the breaker one that covers its housing and the 0 / 1 plate, so a
## finger anywhere on a switch's bay works that switch (model space: x across the plate, y up, z out of it).
func _add_panel_tap_areas() -> void:
	var panel: Node3D = models.get("panel7")
	if panel == null:
		return
	for i in 5:
		var x := [-0.22, -0.11, 0.0, 0.11, 0.22][i] as float
		_add_tap_area(panel, Vector3(0.105, 0.17, 0.07), "panel", "IA_switch_%d" % i, false, Vector3(x, -0.085, 0.05))
	_add_tap_area(panel, Vector3(0.20, 0.17, 0.11), "panel", "IA_main_lever", false, Vector3(0.0, -0.275, 0.06))


func _build_lights() -> void:
	var moon := DirectionalLight3D.new()
	moon.light_color = Color("7fa7d9")
	moon.light_energy = 0.8
	moon.shadow_enabled = true
	moon.shadow_blur = 1.5
	moon.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	moon.directional_shadow_max_distance = 8.0
	add_child(moon)
	moon.look_at_from_position(Vector3(1.5, 4.5, -5.5), Vector3(0.3, 0.0, 0.6), Vector3.UP)
	lights["moon"] = moon

	var desk_lamp := OmniLight3D.new()
	desk_lamp.light_color = Color("ffb46b")
	desk_lamp.light_energy = 1.1
	desk_lamp.omni_range = 2.6
	desk_lamp.position = Vector3(-1.05, 1.18, -2.15)
	add_child(desk_lamp)
	lights["desk_lamp"] = desk_lamp

	var maglock := OmniLight3D.new()
	maglock.light_color = Color("ff3b2f")
	maglock.light_energy = 0.9
	maglock.omni_range = 1.8
	maglock.position = Vector3(2.85, 2.35, 0.9)
	add_child(maglock)
	lights["maglock"] = maglock

	for i in 2:
		var p := OmniLight3D.new()
		p.light_color = Color("ffc58a")
		p.light_energy = 0.0
		p.omni_range = 6.5
		p.omni_attenuation = 1.2
		p.position = [Vector3(-0.6, 2.45, -0.6), Vector3(1.2, 2.45, 0.8)][i]
		p.shadow_enabled = i == 0
		p.omni_shadow_mode = OmniLight3D.SHADOW_DUAL_PARABOLOID
		p.distance_fade_enabled = false
		add_child(p)
		lights["pendant_%d" % i] = p

	var red := OmniLight3D.new() # darkroom safelight, leaks around the bookcase once ARRAY is live
	red.light_color = Color("ff2a1a")
	red.light_energy = 0.0
	red.omni_range = 3.2
	red.position = Vector3(-4.0, 2.2, -0.6)
	add_child(red)
	lights["safelight"] = red

	var shadow_lamp := SpotLight3D.new()
	shadow_lamp.light_color = Color("fff1d6")
	shadow_lamp.light_energy = 0.0
	shadow_lamp.spot_range = 3.0
	shadow_lamp.spot_angle = 22.0
	shadow_lamp.shadow_enabled = true
	shadow_lamp.shadow_blur = 0.4
	add_child(shadow_lamp)
	shadow_lamp.look_at_from_position(Vector3(-4.0, 1.25, 0.12), Vector3(-4.0, 1.5, -1.6), Vector3.UP)
	lights["shadow_lamp"] = shadow_lamp

	var lumen := OmniLight3D.new()
	lumen.light_color = Color("cff6ff")
	lumen.light_energy = 0.0
	lumen.omni_range = 2.0
	lumen.position = Vector3(-1.95, BEAM_Y, 1.6)
	add_child(lumen)
	lights["lumen"] = lumen

	# Moonlight bouncing off the ceiling: before the power comes back it keeps the dark corners readable on a
	# dim phone screen (shapes, not detail); afterwards it fades to a faint cool rim under the pendants.
	var bounce := OmniLight3D.new()
	bounce.light_color = Color("8fb0d6")
	bounce.light_energy = 0.0
	bounce.omni_range = 6.5
	bounce.omni_attenuation = 0.9
	bounce.shadow_enabled = false
	bounce.position = Vector3(-0.4, 2.75, 0.5)
	add_child(bounce)
	lights["moon_bounce"] = bounce

	var fill := OmniLight3D.new()
	fill.light_color = Color("ffe2c2")
	fill.light_energy = 0.0
	fill.omni_range = 2.4
	fill.light_specular = 0.0 # a helper light: lift the shadows, never paint a hot spot on glossy enamel or glass
	fill.omni_attenuation = 1.3
	fill.shadow_enabled = false
	add_child(fill)
	lights["focus_fill"] = fill

	uv_light = SpotLight3D.new()
	uv_light.light_color = Color("7b4dff")
	uv_light.light_energy = 3.0
	uv_light.spot_range = 3.5
	uv_light.spot_angle = 11.0
	uv_light.visible = false
	add_child(uv_light)

	var probe := ReflectionProbe.new()
	probe.size = Vector3(6, 3.4, 5)
	probe.position = Vector3(0, 1.7, 0)
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.interior = true
	add_child(probe)


## Lamps sit exactly at the empties authored in Blender, so shadows/glows line up with the models.
func _place_lights_from_models() -> void:
	var sl := ModelUtil.find(models.get("shadow_lock"), "light_origin")
	var lamp: SpotLight3D = lights["shadow_lamp"]
	if sl:
		lamp.spot_angle = 14.0
		lamp.look_at_from_position(sl.global_position, Vector3(-4.0, 1.5, -1.585), Vector3.UP)
	var so := ModelUtil.find(models.get("shadow_lock"), "safelight_origin")
	if so:
		(lights["safelight"] as Light3D).global_position = so.global_position
	var dl := ModelUtil.find(models.get("desk_lamp"), "light_origin")
	if dl:
		(lights["desk_lamp"] as Light3D).global_position = dl.global_position + Vector3(0, -0.04, 0)
	# The sculpture's ring and rod are plain meshes (no IA_ collider): a tap on them fell through to the wall. A box
	# around each takes the tap; the smaller knob colliders still win where they overlap.
	for nm in ["sculpture_ring", "sculpture_rod"]:
		var mi := ModelUtil.find(models.get("shadow_lock"), nm) as MeshInstance3D
		if mi and mi.mesh:
			var ab := mi.mesh.get_aabb()
			var body := StaticBody3D.new()
			var cs := CollisionShape3D.new()
			var box := BoxShape3D.new()
			box.size = ab.size + Vector3.ONE * 0.02
			cs.shape = box
			cs.position = ab.get_center()
			body.add_child(cs)
			body.set_meta("part", nm)
			body.set_meta("hotspot", "shadow")
			mi.add_child(body)
	# per-card photographs on the evidence wall and the drying line
	for k in 8:
		var card := ModelUtil.find(models.get("evidence_board"), "photo_%d" % k) as MeshInstance3D
		if card:
			card.material_override = _photo_mat(k)
	for k in 4:
		var pr := ModelUtil.find(models.get("darkroom_props"), "print_%d" % k) as MeshInstance3D
		if pr:
			pr.material_override = _photo_mat((k + 4) % 8)


func _photo_mat(k: int) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = load("res://assets/textures/decals/photo_%d.jpg" % k)
	m.roughness = 0.55
	return m


## The bookcase swings INTO the lab about its front-north edge, keeping the darkroom clear.
func _hinge_bookcase() -> void:
	var shelf: Node3D = models.get("bookshelf")
	if shelf == null:
		return
	var pivot := Node3D.new()
	pivot.name = "BookcasePivot"
	add_child(pivot)
	pivot.global_position = BOOKCASE_HINGE
	shelf.reparent(pivot, true)
	models["bookshelf_pivot"] = pivot
	# the Lumen shard lying on top of the bookcase rides along when it swings open
	var shard: Node3D = _shard_nodes.get("bookshelf_top")
	if shard:
		shard.reparent(pivot, true)
	_frame_open_bookcase()


## The drawer close-up has two jobs: while the drawer is shut it frames the four code wheels close enough to turn with
## a finger (each wheel was ~4 mm wide on a phone from the old 0.8 m framing); once it slides open, the camera
## steps back so the whole drawer and what lies in it are in view.
func _frame_drawer() -> void:
	if logic.state["drawer_open"]:
		cam.add_view("drawer", Vector3(-0.5, 1.08, -1.12), Vector3(-0.5, 0.62, -1.78), 36.0)
	else:
		cam.add_view("drawer", Vector3(-0.5, 0.9, -1.4), Vector3(-0.5, 0.655, -1.78), 30.0)


## The safe close-up: the keypad fills the frame while the safe is shut (keys ~5 mm wide on a phone from the old
## framing); once the door swings open, the camera steps back to show the shelves inside.
func _frame_safe() -> void:
	if logic.state["safe_open"]:
		cam.add_view("safe", Vector3(2.2, 1.32, 1.72), Vector3(2.2, 1.25, 2.5), 40.0)
	else:
		cam.add_view("safe", Vector3(2.26, 1.3, 2.0), Vector3(2.26, 1.26, 2.5), 34.0)


## Panel 7's close-up shows the whole plate: the four icons above the lamps, the traces, the switches with their
## numerals, the main lever with its handle and the 0 / 1 plate. The plate is 0.60 × 0.80 m on the east wall; the
## camera stands square to it at the distance where all of it fits in the area the HUD leaves clear (below the
## title row, above the prompt, right of the inventory column), so a 20:9 phone with large text and a 4:3 tablet
## both see it whole. At 0.88 m the icons were cut off at the top and the handle sat under the HUD.
const PANEL_PLATE_CENTRE := Vector3(2.966, 1.45, -1.3) # the plate's front face
const PANEL_HALF := Vector2(0.33, 0.42) # half-size framed: the plate plus the cabinet's bezels

## Strand's poster (frame 0.544 × 0.751 m, centred on the south wall) is framed the same way: all of it, header to
## footer, between the title and the prompt, so the dots beside every symbol can be counted (the caption is one line).
const POSTER_CENTRE := Vector3(-0.3, 1.9, 2.49) # the paper
const POSTER_HALF := Vector2(0.28, 0.385)

func _frame_fitted() -> void:
	var free: Rect2 = cam.hud_free_rect(hud)
	var f: Dictionary = cam.fit_rect(PANEL_PLATE_CENTRE, Vector3.LEFT, PANEL_HALF.x, PANEL_HALF.y, 54.0, free, 0.04)
	cam.add_view("panel", f["pos"], f["target"], 54.0)
	f = cam.fit_rect(POSTER_CENTRE, Vector3.FORWARD, POSTER_HALF.x, POSTER_HALF.y, 44.0, free, 0.03)
	cam.add_view("poster", f["pos"], f["target"], 44.0)


## The screen's shape or the HUD's size changed (rotation, text size): close-ups fitted to the free area follow.
func _on_viewport_resized() -> void:
	_frame_fitted()
	_reframe("panel")
	_reframe("poster")


## A close-up whose framing depends on the state was just re-aimed: glide to the new framing if the player is in it.
func _reframe(view_id: String) -> void:
	if cam.current() == view_id:
		cam.refresh()


## Once the bookcase stands open, the views that looked at it frame the hidden doorway from a spot
## outside the swing arc (the "books" close-up sits inside it), and the shelf-top view follows the shelf.
func _frame_open_bookcase() -> void:
	if not logic.state["shelf_open"]:
		return
	cam.add_view("bookshelf", Vector3(-1.2, 1.45, 0.15), Vector3(-3.3, 1.2, -0.7), 60.0)
	cam.add_view("books", Vector3(-1.2, 1.45, 0.15), Vector3(-3.3, 1.2, -0.7), 60.0)
	var top := BOOKCASE_HINGE + Basis(Vector3.UP, deg_to_rad(Lab7Visuals.SHELF_OPEN_DEG)) * (SHARD_SPOTS["bookshelf_top"] - BOOKCASE_HINGE)
	cam.add_view("bookshelf_top", top + Vector3(0.45, 0.4, 0.55), top, 48.0)


## Only draw the darkroom while it can be seen (perf on phones; no occlusion culling needed).
func _update_room_visibility() -> void:
	var dark_visible: bool = logic.state["shelf_open"] or cam.current() in ["darkroom", "shadow", "emblem", "cabinet", "evidence", "darkroom_floor", "sculpture"]
	for id in ["shadow_lock", "darkroom_props", "evidence_board"]:
		var n: Node3D = models.get(id)
		if n:
			n.visible = dark_visible
	(lights["safelight"] as Light3D).visible = dark_visible or (logic.state["power_on"])


func _build_views() -> void:
	cam = RoomCamera.new()
	cam.near = 0.03
	cam.far = 30.0
	add_child(cam)
	var V := cam.add_view
	V.call("lab", Vector3(0.2, 1.55, 0.25), Vector3(0.0, 1.4, -2.5), 62.0, true)
	V.call("darkroom", Vector3(-3.3, 1.5, -0.55), Vector3(-4.8, 1.35, -0.75), 62.0, true)
	V.call("door", Vector3(1.55, 1.5, 0.75), Vector3(3.0, 1.25, 0.75), 56.0)
	V.call("lock", Vector3(2.35, 1.2, 0.12), Vector3(3.0, 1.15, 0.12), 34.0)
	V.call("desk", Vector3(-0.5, 1.48, -1.2), Vector3(-0.5, 0.8, -2.15), 52.0)
	_frame_drawer()
	V.call("clock", Vector3(-0.98, 1.0, -1.8), Vector3(-1.0, 0.84, -2.25), 30.0)
	V.call("desk_side", Vector3(0.95, 0.78, -1.85), Vector3(0.25, 0.55, -2.08), 42.0)
	V.call("under_desk", Vector3(-0.74, 0.5, -1.15), Vector3(-0.7, 0.02, -2.2), 55.0) # beside the chair, not under it
	V.call("filing", Vector3(-1.9, 1.55, -1.25), Vector3(-2.6, 1.0, -2.2), 50.0)
	V.call("bookshelf", Vector3(-1.35, 1.35, -0.6), Vector3(-2.74, 1.15, -0.6), 56.0)
	V.call("books", Vector3(-2.0, 1.0, -0.6), Vector3(-2.74, 0.9, -0.6), 44.0)
	V.call("gearbox", Vector3(-1.85, 1.02, -1.72), Vector3(-1.85, 0.6, -2.18), 38.0)
	V.call("bookshelf_top", Vector3(-2.15, 2.5, -0.55), Vector3(-2.9, 2.12, -0.5), 48.0)
	V.call("chalkboard", Vector3(-1.15, 1.55, 1.05), Vector3(-3.0, 1.5, 1.05), 50.0)
	V.call("projector", Vector3(-1.45, 1.45, 1.05), Vector3(-2.2, 1.12, 1.6), 46.0)
	V.call("projector_rings", Vector3(-2.22, 1.27, 1.2), Vector3(-2.22, 1.14, 1.6), 30.0)
	V.call("bench", Vector3(-0.3, 1.65, 1.15), Vector3(-0.3, 1.0, 2.25), 56.0)
	V.call("vials", Vector3(-0.9, 1.18, 1.62), Vector3(-0.9, 1.0, 2.12), 32.0)
	V.call("radio", Vector3(0.55, 1.22, 1.62), Vector3(0.55, 1.05, 2.22), 36.0)
	# 18 cm further back along the same line of sight: the tuning knob on the radio's front edge comes in from the
	# screen edge (tap_map --hud-check wants 6 mm) while the hatch and its valve socket stay as readable as before
	V.call("radio_hatch", Vector3(0.553, 1.685, 1.813), Vector3(0.54, 1.12, 2.23), 38.0)
	_frame_safe()
	_frame_fitted()
	V.call("coat", Vector3(1.5, 1.38, -1.7), Vector3(2.12, 1.07, -2.08), 52.0) # west of Panel 7's open door
	V.call("mirror_a", Vector3(0.95, 1.5, 1.05), Vector3(1.6, 1.15, 1.6), 46.0)
	V.call("mirror_b", Vector3(0.85, 1.45, 0.4), Vector3(1.6, 1.15, 0.12), 46.0)
	V.call("window", Vector3(1.5, 1.85, -1.55), Vector3(1.5, 2.0, -2.7), 56.0)
	V.call("radiator", Vector3(1.5, 0.95, -1.65), Vector3(1.6, 0.35, -2.45), 50.0)
	V.call("evidence", Vector3(-3.45, 1.5, -0.6), Vector3(-4.8, 1.5, -0.6), 56.0)
	# aimed lower so the sculpture's knobs sit above the prompt banner and 6 mm clear of the bottom edge; the emblem stays in view
	V.call("shadow", Vector3(-3.45, 1.6, 0.32), Vector3(-4.0, 1.12, -1.45), 56.0)
	V.call("sculpture", Vector3(-3.58, 1.3, -0.25), Vector3(-4.0, 1.08, -0.6), 40.0)
	V.call("emblem", Vector3(-4.0, 1.5, -0.98), Vector3(-4.0, 1.5, -1.6), 50.0)
	V.call("cabinet", Vector3(-3.95, 0.95, -0.95), Vector3(-4.0, 0.55, -1.58), 46.0)
	V.call("darkroom_floor", Vector3(-3.9, 0.9, -0.3), Vector3(-4.5, 0.0, 0.2), 55.0)
	V.call("echo", Vector3(0.35, 1.45, -0.55), Vector3(-0.45, 1.0, -1.85), 50.0)
	cam.view_changed.connect(_on_view_changed)


func _build_input() -> void:
	touch = TouchInput.new()
	add_child(touch)
	touch.tapped.connect(_on_tap)
	touch.dragged.connect(_on_drag)
	touch.drag_started.connect(_on_drag_started)
	touch.drag_ended.connect(func(_p: Vector2) -> void:
		_knob_drag = false
		cam.release())
	touch.pinched.connect(func(f: float) -> void: cam.zoom(f))
	touch.two_finger_tap.connect(go_back)


func _build_hud() -> void:
	hud = (load("res://src/ui/hud.gd") as GDScript).new()
	add_child(hud)
	hud.call("bind", self)


# ====================================================================== input
## Android back / Escape: overlay → selected item → camera step back → pause menu at the room view.
func handle_back() -> void:
	if hud.call("handle_back") or _ending:
		return
	if logic.selected != "":
		logic.select_item("")
		return
	if cam.is_root() and cam.current() == "lab":
		hud.call("show_pause")
		return
	go_back()


func go_back() -> void:
	if _ending:
		return
	if cam.current() == "darkroom":
		cam.go("lab")
		return
	if not cam.back() and cam.current() == "lab" and logic.selected != "":
		logic.select_item("")


const KNOB_PX_PER_STEP := 9.0 # drag distance per dial unit (≈ 1 cm on a phone)


func _on_drag_started(pos: Vector2) -> void:
	_knob_drag = false
	_knob_acc = 0.0
	if cam.transitioning or cam.current() not in ["radio", "radio_hatch"]:
		return
	var hit := _raycast(pos)
	if not hit.is_empty() and _resolve(hit)["part"] == "IA_tuning_knob":
		_knob_drag = true


func _on_drag(rel: Vector2, pos: Vector2) -> void:
	if _knob_drag:
		# right / up turns clockwise (higher frequency), like a real tuning knob
		_knob_acc += (rel.x - rel.y) / (KNOB_PX_PER_STEP * maxf(1.0, DisplayServer.screen_get_scale()))
		var steps := int(_knob_acc)
		if steps != 0:
			_knob_acc -= steps
			logic.step_dial(steps)
		return
	if logic.selected == "uv_lamp" and not cam.is_root():
		_uv_aim = pos
		return
	cam.free_look(rel)
	if logic.selected == "uv_lamp":
		_uv_aim = get_viewport().get_visible_rect().size * 0.5


func _raycast(screen: Vector2) -> Dictionary:
	## Collects every hit along the tap ray and prefers the smallest interactive part (IA_*, items,
	## shards) within a short depth window behind the first surface, so small controls (dial wheels,
	## knobs, keys) win over the coarse boxes of the furniture they sit on.
	var from := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var space := get_world_3d().direct_space_state
	var exclude: Array[RID] = []
	var hits: Array[Dictionary] = []
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(from, from + dir * 20.0)
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
		if d - first_d > 0.18:
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


## The same names RoomBase gives these, so the shared QA tools (qa/tap_map.gd) work on this room too.
func raycast(screen: Vector2) -> Dictionary:
	return _raycast(screen)


func resolve(hit: Dictionary) -> Dictionary:
	return _resolve(hit)


func _resolve(hit: Dictionary) -> Dictionary:
	## -> {"hotspot", "part", "model", "pos"}
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
	if logic.selected == "uv_lamp":
		_uv_aim = screen
	var hit := _raycast(screen)
	if hit.is_empty():
		return
	var r := _resolve(hit)
	var part: String = r["part"]
	var hs: String = r["hotspot"]
	if part.begins_with("Shard_"):
		_tap_shard(part.substr(6))
		return
	if hs == "":
		return
	# Using a selected item takes priority (except tools that are "worn", like the UV lamp).
	if logic.selected != "" and logic.selected != "uv_lamp":
		var target := _use_target(hs, part)
		if target != "" and _in_reach(hs):
			var ev := logic.use_item_on(logic.selected, target)
			if ev.has("nothing_happens"):
				hud.call("message", tr("msg.nothing"))
				AudioManager.ui("ui_error")
			else:
				logic.select_item("")
			return
	if not _in_reach(hs):
		_focus(hs)
		return
	_interact(hs, part, r)


func _in_reach(hotspot: String) -> bool:
	## A hotspot is directly operable from its own view or any deeper view of the same object.
	var v: String = HOTSPOT_VIEW.get(hotspot, "")
	var cur := cam.current()
	if v == "" or cur == v:
		return true
	var deeper := {
		"desk": ["drawer", "clock", "desk_side", "under_desk"], "bookshelf": ["books", "bookshelf_top"],
		"bench": ["vials", "radio", "radio_hatch"], "door": ["lock"], "shadow": ["emblem", "cabinet", "sculpture"],
		"projector": ["projector_rings"],
		"radio": ["radio_hatch"],
	}
	return (deeper.get(v, []) as Array).has(cur)


func _focus(hotspot: String) -> void:
	var v: String = HOTSPOT_VIEW.get(hotspot, "")
	if v != "":
		cam.go(v)
		AudioManager.ui("ui_tap")


func _use_target(hs: String, part: String) -> String:
	match hs:
		"desk":
			if part in ["IA_keyhole", "IA_secret_panel", "IA_compartment", "IA_rosette"] or cam.current() == "desk_side":
				return "desk_keyhole"
		"panel":
			return "panel_main"
		"radio":
			return "radio"
		"projector":
			return "projector"
		"shadow":
			return "emblem_socket"
		"mirror_b":
			return "mirror_stand_b"
	return "_"


# ====================================================================== interactions
func _interact(hs: String, part: String, r: Dictionary) -> void:
	var s := logic.state
	match hs:
		"door":
			if cam.current() == "lab":
				_focus("door")
			elif not s["door_open"]:
				hud.call("message", tr("msg.door_sealed"))
				AudioManager.sfx("drawer_locked", -6.0, 0.7)
		"lock":
			if cam.current() != "lock":
				cam.go("lock")
			elif not s["door_open"]:
				hud.call("message", tr("msg.lock_waits") if s["beam_on"] and logic.trace_beam()["end"] == "lock" else tr("msg.lock_dark"))
				AudioManager.ui("ui_tap")
		"notebook":
			if logic.can_take("notebook"):
				logic.take("notebook")
		"clock":
			if cam.current() != "clock":
				cam.go("clock")
			else:
				hud.call("message", tr("msg.clock_stopped"))
				AudioManager.sfx("wheel_tick", -8.0, 0.8)
		"desk":
			_interact_desk(part, r)
		"bookshelf":
			_interact_bookshelf(part, r)
		"gearbox":
			_interact_gearbox(part)
		"chalkboard", "poster", "filing", "window", "coat", "evidence", "radiator":
			if cam.current() != HOTSPOT_VIEW.get(hs, ""):
				_focus(hs)
			elif hs == "evidence":
				hud.call("show_document", "evidence")
			elif hs in ["poster", "chalkboard"]:
				hud.call("show_document", hs) # the inscription full size in the reader (pinch to zoom)
			else:
				# scenery in its own close-up: a short line instead of silence
				var line := {"chalkboard": "msg.chalkboard_dust", "poster": "msg.poster_table", "filing": "msg.filing_locked",
					"window": "obj.window", "coat": "msg.coat_pockets", "radiator": "obj.radiator"}[hs] as String
				hud.call("message", tr(line))
				if hs == "filing":
					AudioManager.sfx("drawer_locked", -14.0, 1.1)
				else:
					AudioManager.ui("ui_tap")
		"bench":
			_interact_bench(part)
		"radio":
			_interact_radio(part, r)
		"safe":
			_interact_safe(part)
		"panel":
			_interact_panel(part)
		"projector":
			_interact_projector(part)
		"mirror_a", "mirror_b":
			_interact_mirror(hs, part, r)
		"shadow":
			_interact_shadow(part)
		_:
			pass


func _interact_desk(part: String, r: Dictionary) -> void:
	var s := logic.state
	var cur := cam.current()
	if part.begins_with("IA_drawer_digit_"):
		if cur != "drawer":
			cam.go("drawer")
			return
		var i := int(part.substr(16))
		var wheel := ModelUtil.find(models.get("desk"), part)
		var up := true
		if wheel != null:
			up = (r["pos"] as Vector3).y >= wheel.global_position.y
		logic.step_drawer_wheel(i, 1 if up else -1)
		return
	if part == "IA_drawer_top" or part.begins_with("Item_drawer"):
		if cur != "drawer":
			cam.go("drawer")
		elif s["drawer_open"] and logic.can_take("drawer_lamp"):
			logic.take("drawer_lamp")
		elif not s["drawer_open"]:
			hud.call("message", tr("msg.drawer_locked"))
			AudioManager.sfx("drawer_locked")
		else:
			_empty_now()
		return
	if part in ["IA_rosette", "IA_secret_panel", "IA_keyhole", "IA_compartment", "UV_desk_mark"] or part.begins_with("Item_comp"):
		if cur != "desk_side":
			cam.go("desk_side")
			return
		if part == "IA_rosette":
			logic.press_rosette()
		elif s["compartment_open"]:
			for spot in ["compartment_handle", "compartment_photo"]:
				if logic.can_take(spot):
					logic.take(spot)
					return
			_empty_now()
		elif s["rosette"]:
			hud.call("message", tr("hint.key.1"))
		else:
			hud.call("message", tr("msg.desk_side"))
			AudioManager.ui("ui_tap")
		return
	if cur == "lab":
		cam.go("desk")
	elif cur == "desk":
		# tapped the desk body: the east side or the drawer area by hit position
		var p: Vector3 = r["pos"]
		if p.x > 0.15:
			cam.go("desk_side")
		elif p.y < 0.4:
			cam.go("under_desk")
		elif p.y < 0.76 and absf(p.x + 0.5) < 0.35:
			cam.go("drawer")
		else:
			# the desk top and what she left on it (tea set, spectacles, magnifier)
			hud.call("message", tr("msg.desk_clutter"))
			AudioManager.ui("ui_tap")
	elif cur == "drawer" and not s["drawer_open"]:
		# the desk around the locked drawer: answer instead of ignoring the tap
		hud.call("message", tr("msg.drawer_locked"))
		AudioManager.sfx("drawer_locked")
	elif cur in ["clock", "under_desk", "desk_side"]:
		hud.call("message", tr("msg.desk_clutter" if cur == "clock" else ("msg.desk_side" if cur == "desk_side" else "obj.desk")))
		AudioManager.ui("ui_tap")


func _interact_bookshelf(part: String, _r: Dictionary) -> void:
	var s := logic.state
	var cur := cam.current()
	if part.begins_with("IA_book_"):
		if cur != "books":
			cam.go("books")
			return
		if s["shelf_open"]:
			hud.call("message", tr("obj.bookshelf_open")) # the books are fixed now; the case itself has swung open
			AudioManager.ui("ui_tap")
			return
		var n := int(part.substr(8))
		logic.pull_book(n)
		return
	if s["shelf_open"] and cur in ["lab", "bookshelf"]:
		cam.go("darkroom")
		return
	if cur == "lab":
		cam.go("bookshelf")
	elif cur == "bookshelf":
		cam.go("books")
	else:
		# the shelves or the carcass in a close-up
		hud.call("message", tr("obj.bookshelf_open" if s["shelf_open"] else "obj.bookshelf"))
		AudioManager.ui("ui_tap")


## A container the player has already emptied: say so instead of ignoring the tap.
func _empty_now() -> void:
	hud.call("message", tr("msg.empty_now"))
	AudioManager.ui("ui_tap")


func _interact_gearbox(part: String) -> void:
	var s := logic.state
	if cam.current() != "gearbox":
		cam.go("gearbox")
		return
	if s["box_open"]:
		if logic.can_take("box_cell"):
			logic.take("box_cell")
		else:
			_empty_now()
		return
	if part.begins_with("IA_knob_") or part.begins_with("IA_gear_"):
		logic.press_gear(int(part.substr(part.length() - 1)))
	else:
		# the shut lid or the box body: it is locked, and the knobs below are what moves
		hud.call("message", tr("msg.box_locked"))
		AudioManager.sfx("drawer_locked", -10.0, 1.2)


func _interact_bench(part: String) -> void:
	if part.begins_with("IA_vial_") or part.begins_with("vial"):
		if cam.current() != "vials":
			cam.go("vials")
		else:
			hud.call("message", tr("obj.vials"))
			AudioManager.ui("ui_tap")
	elif cam.current() == "lab":
		cam.go("bench")
	else:
		hud.call("message", tr("msg.bench_glass"))
		AudioManager.ui("ui_tap")


func _interact_radio(part: String, r: Dictionary) -> void:
	if cam.current() not in ["radio", "radio_hatch"]:
		cam.go("radio")
		return
	var s := logic.state
	if part == "IA_tuning_knob":
		if logic.radio_status() == "dead":
			hud.call("message", tr("msg.radio_no_power") if not s["power_on"] else tr("msg.radio_needs_valve"))
		var knob := ModelUtil.find(models.get("radio"), part)
		var right := true
		if knob != null:
			right = cam.unproject_position(r["pos"]).x >= cam.unproject_position(knob.global_position).x
		logic.step_dial(2 if right else -2)
		return
	if part == "IA_radio_hatch" or part == "IA_valve_socket":
		if cam.current() != "radio_hatch":
			visuals.radio_hatch_open = true
			cam.go("radio_hatch")
		else:
			visuals.radio_hatch_open = not visuals.radio_hatch_open
		visuals.apply_state(true)
		if not s["valve_installed"]:
			hud.call("message", tr("msg.radio_needs_valve"))
		return
	if logic.radio_status() == "dead":
		hud.call("message", tr("msg.radio_dead"))


func _interact_safe(part: String) -> void:
	if cam.current() != "safe":
		cam.go("safe")
		return
	var s := logic.state
	if s["safe_open"]:
		for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
			if part == "Item_" + spot and logic.can_take(spot):
				logic.take(spot)
				return
		for spot in ["safe_key", "safe_lens", "safe_letter", "safe_valve"]:
			if logic.can_take(spot):
				logic.take(spot)
				return
		_empty_now()
		return
	if part.begins_with("IA_key_"):
		var k := part.substr(7)
		var map := {"clear": "C", "enter": "E"}
		logic.safe_press(map.get(k, k))
	else:
		# the door, its handle or the body: locked until the keypad says otherwise
		hud.call("message", tr("msg.safe_locked"))
		AudioManager.sfx("drawer_locked", -8.0, 0.9)


func _interact_panel(part: String) -> void:
	if cam.current() != "panel":
		cam.go("panel")
		return
	if part.begins_with("IA_switch_"):
		logic.toggle_switch(int(part.substr(10)))
	elif part == "IA_main_lever" or part == "main_handle":
		logic.toggle_main()
	else:
		# the lamps, the gauge or the plate: say what they are for
		hud.call("message", tr("msg.panel_lamps"))
		AudioManager.ui("ui_tap")


func _interact_projector(part: String) -> void:
	if cam.current() not in ["projector", "projector_rings"]:
		cam.go("projector")
		return
	var s := logic.state
	if part.begins_with("IA_ring_"):
		if cam.current() != "projector_rings":
			cam.go("projector_rings")
		else:
			logic.turn_ring(int(part.substr(8)))
	elif part == "IA_projector_lever":
		logic.pull_projector_lever()
	elif part in ["IA_lens_socket", "lens_installed"] and s["lens_at"] == "projector":
		logic.remove_lens()
	elif cam.current() == "projector":
		# the empty socket or the body: what the projector still lacks, or that it is running
		if not s["power_on"]:
			hud.call("message", tr("msg.projector_no_power"))
		elif s["lens_at"] != "projector":
			hud.call("message", tr("msg.projector_no_lens"))
		else:
			hud.call("caption", tr("cap.hum") if s["beam_on"] else tr("obj.projector"))
		AudioManager.ui("ui_tap")


func _interact_mirror(hs: String, part: String, r: Dictionary) -> void:
	if cam.current() != hs:
		cam.go(hs)
		return
	var which := 0 if hs == "mirror_a" else 1
	if which == 1 and not logic.state["mirror_b_mounted"]:
		hud.call("message", tr("obj.mirror_b"))
		return
	# One tap = one 45° click, always the same way: predictable on a phone (a left/right-half rule
	# flips as the mirror itself turns).
	logic.rotate_mirror(which, 1)


func _interact_shadow(part: String) -> void:
	var s := logic.state
	var cur := cam.current()
	if part == "IA_ring_knob" or part == "sculpture_ring":
		if cur != "sculpture":
			cam.go("sculpture")
		else:
			logic.turn_sculpture(0)
	elif part == "IA_rod_knob" or part == "sculpture_rod":
		if cur != "sculpture":
			cam.go("sculpture")
		else:
			logic.turn_sculpture(1)
	elif part in ["IA_emblem_socket", "socket_lens"]:
		if cur != "emblem" and cur != "shadow":
			cam.go("emblem")
		elif s["lens_at"] == "socket":
			logic.remove_lens()
		else:
			hud.call("message", tr("obj.emblem"))
	elif part == "IA_cabinet_door" or part.begins_with("Item_cabinet"):
		if cur != "cabinet":
			cam.go("cabinet")
		elif s["cabinet_open"] and logic.can_take("cabinet_mirror"):
			logic.take("cabinet_mirror")
		elif s["cabinet_open"]:
			_empty_now()
		elif not s["cabinet_open"]:
			hud.call("message", tr("obj.cabinet"))
			AudioManager.sfx("drawer_locked", -8.0, 1.1)
	elif cur == "darkroom":
		cam.go("shadow")
	elif cur == "shadow":
		cam.go("sculpture") # the sculpture's table or lamp: come closer to the two knobs
		AudioManager.ui("ui_tap")
	elif cur == "sculpture":
		hud.call("message", tr("obj.shadow"))
		AudioManager.ui("ui_tap")


func _tap_shard(id: String) -> void:
	if logic.selected != "uv_lamp":
		return
	var ev := logic.collect_shard(id)
	if ev.has("nothing_happens"):
		return


# ====================================================================== per-frame: UV torch
func _process(delta: float) -> void:
	var fill: OmniLight3D = lights["focus_fill"]
	fill.global_position = cam.global_position + cam.global_basis * Vector3(0.12, 0.18, 0.05)
	var uv_on := logic.selected == "uv_lamp" and not _ending
	uv_light.visible = uv_on
	RenderingServer.global_shader_parameter_set("uv_light_on", 1.0 if uv_on else 0.0)
	if not uv_on:
		_uv_dwell = 0.0
		return
	var vp := get_viewport().get_visible_rect().size
	if _uv_aim == Vector2.ZERO:
		_uv_aim = vp * 0.5
	var origin := cam.global_position + cam.global_basis * Vector3(0.08, -0.06, 0.0)
	var dir := cam.project_ray_normal(_uv_aim)
	uv_light.global_position = origin
	uv_light.look_at(origin + dir, Vector3.UP if absf(dir.y) < 0.98 else Vector3.FORWARD)
	RenderingServer.global_shader_parameter_set("uv_light_pos", origin)
	RenderingServer.global_shader_parameter_set("uv_light_dir", dir)
	# dwell on a UV target to reveal it
	var hit := _raycast(_uv_aim)
	var target := ""
	if not hit.is_empty():
		var col: Node = hit["collider"]
		var p: Node = col.get_parent() if col else null
		if p != null and p.has_meta("uv_target"):
			target = str(p.get_meta("uv_target"))
		elif str(col.get_meta("part", "")) == "IA_rosette" or cam.current() == "desk_side":
			target = "desk_mark"
	if target != "" and target == _uv_target:
		_uv_dwell += delta
		if _uv_dwell >= UV_REVEAL_TIME:
			logic.uv_reveal(target)
			_uv_dwell = -999.0
	else:
		_uv_target = target
		_uv_dwell = 0.0


# ====================================================================== events → feedback
func _view_caption(id: String) -> String:
	## Captions that describe a state ("bracket is empty", "sealed", "locked") follow the state.
	var s := logic.state
	if id == "mirror_b" and s["mirror_b_mounted"]:
		return "obj.mirror_a"
	if id == "door" and s["door_open"]:
		return "obj.door_open"
	if id == "cabinet" and s["cabinet_open"]:
		return "obj.cabinet_open"
	if id in ["bookshelf", "books"] and s["shelf_open"]:
		return "obj.bookshelf_open"
	return HOTSPOT_CAPTION.get(id, "")


func _on_view_changed(id: String) -> void:
	hud.call("set_view", id, cam.is_root(), _view_caption(id))
	var fill: OmniLight3D = lights["focus_fill"]
	var bright_views := ["bookshelf", "books", "projector", "chalkboard", "coat", "filing", "mirror_a", "mirror_b"]
	# a cream dial, glossy glass or the lock's pale eye 60 cm from the lens: the full fill clips them white
	var dim_views := ["radio", "radio_hatch", "poster", "lock"]
	var e := 0.0 if cam.is_root() else (1.5 if id in bright_views else (0.45 if id in dim_views else 1.0))
	create_tween().tween_property(fill, "light_energy", e, 0.6)
	# up close the poster's glass only veils the table (it reflects the pendant and lifts the ink to a 2:1 contrast)
	var glass: Node3D = ModelUtil.find(models.get("poster_frame"), "poster_glass")
	if glass != null:
		glass.visible = id != "poster"
	var in_dark := id in ["darkroom", "shadow", "emblem", "cabinet", "evidence", "darkroom_floor", "sculpture"]
	if id == "darkroom" and not _darkroom_seen:
		_darkroom_seen = true
		get_tree().create_timer(1.0).timeout.connect(func() -> void: hud.call("caption", tr("doc.darkroom_note"), 7.0))
	(lights["shadow_lamp"] as SpotLight3D).visible = in_dark
	_update_room_visibility()
	(lights["moon"] as DirectionalLight3D).shadow_enabled = not in_dark
	_uv_aim = get_viewport().get_visible_rect().size * 0.5


## The story nudge after the power returns ("a faint red glow around the bookcase"). Its caption sits under the title,
## which in Panel 7's close-up is exactly where the lamp icons are: it waits until the player steps away from the panel.
func _nudge_red_glow() -> void:
	if cam.current() == "panel":
		await cam.view_changed
		await get_tree().create_timer(0.8).timeout
	if not logic.state["shelf_open"]:
		hud.call("caption", tr("msg.red_glow"), 4.5)


func _on_events(ev: Array[String]) -> void:
	for e in ev:
		_feedback(e)
	visuals.apply_state(true)
	_update_room_visibility()
	_update_shards()
	hud.call("set_caption", _view_caption(cam.current()))


## Collected shards leave the room (also after loading a save); their tap areas go with them.
func _update_shards() -> void:
	var got: Array = logic.state["shards"]
	for id: String in _shard_nodes:
		var n: Node3D = _shard_nodes[id]
		var keep := not got.has(id)
		if n.visible != keep:
			n.visible = keep
			n.process_mode = Node.PROCESS_MODE_INHERIT if keep else Node.PROCESS_MODE_DISABLED
			for body in n.find_children("*", "StaticBody3D", true, false):
				(body as StaticBody3D).collision_layer = 1 if keep else 0


func _feedback(e: String) -> void:
	var name := e.get_slice(":", 0)
	var arg := e.get_slice(":", 1) if e.contains(":") else ""
	match name:
		"item_added":
			AudioManager.sfx("item_pickup")
			AudioManager.haptic(15)
			hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key(arg)))
		"drawer_wheel":
			AudioManager.sfx("wheel_tick", -3.0, randf_range(0.95, 1.05))
		"drawer_static", "box_static", "safe_static":
			AudioManager.sfx("wheel_tick", -12.0, 0.7) # a solved mechanism: it no longer moves, but it answers
		"beam_already_on":
			hud.call("caption", tr("cap.hum"))
		"drawer_opened":
			AudioManager.sfx("drawer_open")
			hud.call("message", tr("msg.drawer_opened"))
			_frame_drawer()
			_reframe("drawer")
		"gears":
			AudioManager.sfx("gear_turn", -2.0, randf_range(0.95, 1.05))
		"box_opened":
			AudioManager.sfx("box_open")
			hud.call("message", tr("msg.box_opened"))
		"combined":
			AudioManager.sfx("item_combine")
			if arg == "uv_lamp":
				hud.call("message", tr("msg.lamp_ready"))
		"combine_failed":
			AudioManager.ui("ui_error")
			hud.call("message", tr("msg.combine_failed"))
		"uv_revealed":
			AudioManager.sfx("reveal")
			hud.call("message", tr("msg.uv_page") if arg == "notebook_page" else tr("msg.uv_desk"))
		"safe_key":
			AudioManager.sfx("keypad_press", -2.0, randf_range(0.97, 1.03))
		"safe_cleared":
			AudioManager.sfx("keypad_press", -4.0, 0.8)
		"safe_denied":
			AudioManager.sfx("safe_denied")
			hud.call("message", tr("msg.safe_denied"))
			AudioManager.haptic(60)
		"safe_opened":
			AudioManager.sfx("safe_open")
			hud.call("message", tr("msg.safe_opened"))
			_frame_safe()
			_reframe("safe")
		"keyhole_revealed":
			AudioManager.sfx("secret_panel")
			hud.call("message", tr("msg.keyhole"))
		"rosette_click":
			AudioManager.sfx("rosette_press", -4.0)
		"compartment_opened":
			AudioManager.sfx("key_turn")
			hud.call("message", tr("msg.compartment"))
		"handle_installed":
			AudioManager.sfx("lens_insert", 0.0, 0.7)
			hud.call("message", tr("msg.handle_installed"))
		"switch":
			AudioManager.sfx("switch_toggle")
		"main_no_handle":
			hud.call("message", tr("msg.main_no_handle"))
			AudioManager.ui("ui_error")
		"main_on", "main_off":
			AudioManager.sfx("breaker_on", -4.0 if name == "main_on" else -8.0, 1.0 if name == "main_on" else 0.8)
		"breaker_tripped":
			AudioManager.sfx("breaker_trip")
			AudioManager.haptic(120)
			hud.call("message", tr("msg.breaker_tripped"))
			hud.call("caption", tr("cap.sparks"))
			SceneManager.flash(Color(1.0, 0.85, 0.6, 0.35), 0.03, 0.4)
		"power_restored":
			AudioManager.sfx("power_on")
			hud.call("message", tr("msg.power_restored"))
			_update_lighting(true)
			AudioManager.ambience("amb_power_hum", true, -8.0, 4.0)
			get_tree().create_timer(4.0).timeout.connect(_nudge_red_glow)
		"switches_locked":
			hud.call("message", tr("msg.switches_locked"))
		"main_locked":
			hud.call("message", tr("msg.main_locked"))
		"valve_installed":
			AudioManager.sfx("lens_insert")
			hud.call("message", tr("msg.valve_installed"))
		"dial":
			visuals.radio_tick()
		"radio_signal":
			hud.call("message", tr("msg.radio_signal"))
			var groups: Array = logic.beacon().map(func(n: Variant) -> String: return "•".repeat(int(n)))
			hud.call("caption", tr("cap.beacon") % " — ".join(groups))
			_array_answers()
		"book_pulled":
			AudioManager.sfx("rosette_press", -2.0, 0.85)
			visuals.tilt_book(int(arg))
		"shelf_opened":
			_frame_open_bookcase()
			if cam.current() == "books":
				cam.back() # to the re-framed "bookshelf" view, clear of the swinging case
			elif cam.current() == "bookshelf":
				cam.refresh()
			AudioManager.sfx("secret_panel", 2.0, 0.6)
			AudioManager.sfx("door_open", -6.0, 1.3)
			hud.call("message", tr("msg.shelf_opened"))
			AudioManager.haptic(80)
			_stage_bookcase_reveal()
		"shadow":
			AudioManager.sfx("ring_turn", -2.0, 0.8)
		"cabinet_opened":
			AudioManager.sfx("box_open", 0.0, 0.8)
			hud.call("message", tr("msg.cabinet_opened"))
		"lens_in_socket":
			AudioManager.sfx("lens_insert")
			hud.call("message", tr("msg.lens_in_socket"))
		"emblem_recorded":
			AudioManager.sfx("reveal", 2.0, 0.7)
			AudioManager.sfx("projector_fire", -10.0, 1.4)
			hud.call("message", tr("msg.emblem_recorded"))
			SceneManager.flash(Color(0.8, 0.96, 1.0, 0.45), 0.05, 0.9)
		"lens_in_projector":
			AudioManager.sfx("lens_insert")
			hud.call("message", tr("msg.lens_in_projector"))
		"lens_removed":
			AudioManager.sfx("lens_insert", -2.0, 1.2)
			hud.call("message", tr("msg.lens_removed"))
		"ring":
			AudioManager.sfx("ring_turn")
		"rings_locked":
			hud.call("message", tr("msg.rings_locked"))
		"projector_no_power":
			hud.call("message", tr("msg.projector_no_power"))
			AudioManager.sfx("switch_toggle", -6.0, 0.7)
		"projector_no_lens":
			hud.call("message", tr("msg.projector_no_lens"))
			AudioManager.sfx("switch_toggle", -6.0, 0.7)
		"projector_scatter":
			AudioManager.sfx("projector_charge", -4.0)
			AudioManager.sfx("projector_fail", -2.0)
			hud.call("message", tr("msg.projector_scatter"))
			visuals.scatter_flash()
		"beam_on":
			AudioManager.sfx("projector_charge")
			AudioManager.sfx("projector_fire", -3.0)
			hud.call("message", tr("msg.beam_on"))
			hud.call("caption", tr("cap.hum"))
		"beam_path":
			if arg == "mirror_back":
				hud.call("message", tr("msg.mirror_back"))
			_beam_progress()
		"lock_waits_for_sign":
			hud.call("message", tr("msg.lock_waits"))
		"mirror":
			AudioManager.sfx("ring_turn", -3.0, 0.7)
		"mirror_mounted":
			AudioManager.sfx("lens_insert", 0.0, 0.8)
			hud.call("message", tr("msg.mirror_mounted"))
		"door_unlocked":
			_play_ending()
		"shard_collected":
			AudioManager.sfx("reveal", 0.0, 1.3)
			hud.call("message", tr("ui.shard_found") % (logic.state["shards"] as Array).size())
		"all_shards":
			GameState.unlock_achievement("light_remembers")
		"solved":
			AudioManager.sfx("puzzle_solved", -5.0)
		"chapter_complete":
			hud.call("show_chapter_complete")
		"selected":
			if arg == "uv_lamp":
				AudioManager.sfx("uv_on", -4.0) # the HUD prompt already says "drag to shine"


func _update_lighting(animated: bool) -> void:
	var on: bool = logic.state["power_on"]
	var dur := 2.4 if animated else 0.0
	var targets := {
		"pendant_0": 2.2 if on else 0.0, "pendant_1": 1.7 if on else 0.0,
		"desk_lamp": 1.3 if on else 1.0, "safelight": 0.7 if on else 0.0,
		"shadow_lamp": 3.2 if on else 0.0, "moon_bounce": 0.12 if on else 0.55,
	}
	for k: String in targets:
		var l: Light3D = lights[k]
		if animated and k.begins_with("pendant"):
			var tw := create_tween()
			# relay-style flicker-in
			tw.tween_property(l, "light_energy", targets[k] * 0.6, 0.08)
			tw.tween_property(l, "light_energy", 0.0, 0.1)
			tw.tween_property(l, "light_energy", targets[k] * 0.8, 0.12)
			tw.tween_interval(0.15 + 0.3 * int(k.ends_with("1")))
			tw.tween_property(l, "light_energy", targets[k], dur * 0.5)
		elif animated:
			create_tween().tween_property(l, "light_energy", targets[k], dur)
		else:
			l.light_energy = targets[k]
	var amb := Color("2f3a38") if on else Color("2b4049")
	if animated:
		create_tween().tween_property(env, "ambient_light_energy", 0.55 if on else 0.75, dur)
	else:
		env.ambient_light_energy = 0.55 if on else 0.75
	env.ambient_light_color = amb
	visuals.set_power_emissives(on)


## When Strand's beacon is found, the Array "answers": every lamp in the lab stutters for a moment.
func _array_answers() -> void:
	for k in ["pendant_0", "pendant_1", "desk_lamp"]:
		var l: Light3D = lights[k]
		var base := l.light_energy
		var tw := create_tween()
		for i in 4:
			tw.tween_property(l, "light_energy", base * 0.15, 0.06)
			tw.tween_property(l, "light_energy", base * 1.25, 0.05)
		tw.tween_property(l, "light_energy", base, 0.3)
	AudioManager.sfx("projector_charge", -14.0, 0.6)


func play_opening_camera() -> void:
	## Called by the HUD intro: start facing the slammed door, then turn toward the moonlit desk.
	cam.go("door", true)
	await get_tree().create_timer(1.6).timeout
	cam.go("lab")


# ====================================================================== finale
func _play_ending() -> void:
	_ending = true
	logic.select_item("")
	hud.call("set_busy", true)
	AudioManager.sfx("projector_fire", 0.0, 0.9)
	await get_tree().create_timer(0.6).timeout
	SceneManager.flash(Color(0.85, 0.97, 1.0, 0.85), 0.15, 1.6)
	AudioManager.sfx("maglock_release")
	hud.call("message", tr("msg.door_unlocked"))
	visuals.apply_state(true)
	# 1979 flashback: warm room, Leyla's echo at the desk turns to look at you.
	cam.go("echo")
	var warm := create_tween().set_parallel(true)
	warm.tween_property(env, "ambient_light_color", Color("6a5034"), 1.2)
	warm.tween_property(env, "ambient_light_energy", 1.1, 1.2)
	warm.tween_property(lights["desk_lamp"], "light_energy", 2.6, 1.2)
	var echo: Node3D = models.get("echo_leyla")
	hud.call("caption", tr("outro.echo"))
	visuals.flashback_1979(true)
	if echo:
		echo.visible = true
		visuals.fade_echo(echo, 0.0, 1.0, 1.2)
		await get_tree().create_timer(1.8).timeout
		var head := ModelUtil.find(echo, "echo_head")
		if head:
			var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			tw.tween_property(head, "rotation:y", deg_to_rad(-55.0), 1.4)
		await get_tree().create_timer(2.4).timeout
		visuals.fade_echo(echo, 1.0, 0.0, 1.6)
	else:
		await get_tree().create_timer(3.0).timeout
	var cool := create_tween().set_parallel(true)
	cool.tween_property(env, "ambient_light_color", Color("2f3a38"), 1.6)
	cool.tween_property(env, "ambient_light_energy", 0.55, 1.6)
	cool.tween_property(lights["desk_lamp"], "light_energy", 1.3, 1.6)
	visuals.flashback_1979(false)
	await get_tree().create_timer(1.6).timeout
	cam.go("door")
	await get_tree().create_timer(0.7).timeout
	visuals.open_door()
	AudioManager.sfx("door_open")
	hud.call("caption", tr("cap.door"))
	_wake_corridor()
	await get_tree().create_timer(2.4).timeout
	hud.call("set_busy", false)
	hud.call("show_choice")


## Settings → Brightness scales the scene exposure (dark rooms on dim phone screens).
func _apply_brightness(key: String) -> void:
	if key == "brightness" and env != null:
		env.tonemap_exposure = float(Settings.get_value("brightness"))


# ====================================================================== reveals and the hand-off (docs/ENGAGEMENT.md)
## The bookcase swings: the darkroom's safelight flares red through the gap, a breath of dust rolls out into the lab
## and a draught is heard, so the chapter's mid-point reveal lands with light and sound, not only a line of text.
func _stage_bookcase_reveal() -> void:
	var red: OmniLight3D = lights["safelight"]
	var base := red.light_energy
	var tw := create_tween()
	tw.tween_property(red, "light_energy", 2.6, 0.45)
	tw.tween_property(red, "light_energy", maxf(base, 0.7), 1.6)
	var puff := DustMotes.create(Vector3(0.08, 0.9, 0.45), 90)
	puff.one_shot = true
	puff.explosiveness = 0.8
	puff.lifetime = 2.6
	puff.preprocess = 0.0
	var m := (puff.process_material as ParticleProcessMaterial).duplicate() as ParticleProcessMaterial
	m.direction = Vector3(1.0, 0.15, 0.1)
	m.spread = 35.0
	m.initial_velocity_min = 0.2
	m.initial_velocity_max = 0.55
	m.damping_min = 0.15
	m.damping_max = 0.3
	m.gravity = Vector3(0, -0.02, 0)
	puff.process_material = m
	add_child(puff)
	puff.global_position = Vector3(-2.95, 1.15, -0.6)
	puff.emitting = true
	get_tree().create_timer(3.5).timeout.connect(puff.queue_free)
	AudioManager.sfx("reveal", -6.0, 0.7)
	get_tree().create_timer(0.7).timeout.connect(func() -> void: hud.call("caption", tr("cap1.draught"), 3.5))


## The mirror stretch has one milestone a player can feel: the first time the first mirror sends the beam on to the
## second one, a bright tick and a caption mark it (the second mirror then still has to be turned). Shown once.
var _beam_reached_b := false


func _beam_progress() -> void:
	if _beam_reached_b or not logic.state["mirror_b_mounted"]:
		return
	var pts: PackedVector2Array = logic.trace_beam()["points"]
	if pts.size() >= 3 and pts[2].distance_to(Lab7Logic.MIRROR_B_POS) < 0.01:
		_beam_reached_b = true
		AudioManager.sfx("ring_turn", -2.0, 1.45)
		AudioManager.sfx("reveal", -10.0, 1.6)
		hud.call("caption", tr("cap1.beam_b"), 3.5)


## A save made after the finale choice (the player quit on the chapter card): show the open door and the chapter
## card again, with its Play button for Chapter 2, instead of a finished room with nothing left to do.
func _resume_completed() -> void:
	_ending = true
	_build_corridor()
	_corridor_lit(true)
	cam.go("door", true)
	await get_tree().create_timer(0.6).timeout
	hud.call("show_chapter_complete")


## A save made after the door opened but before the lens was taken or left (the player quit during the ending):
## the choice is offered again at the open door, instead of a finished room with no way to end the chapter.
func _resume_choice() -> void:
	_ending = true
	_build_corridor()
	_corridor_lit(true)
	cam.go("door", true)
	await get_tree().create_timer(0.6).timeout
	hud.call("show_choice")


## Beyond Lab 7's door: the corridor to Records Archive B (Chapter 2 starts at its far end). Built from primitives and
## the shared materials only when the door opens; until then the opening showed the flat fog colour.
const CORRIDOR_X0 := 3.2
const CORRIDOR_X1 := 12.0
const CORRIDOR_Z0 := -0.1
const CORRIDOR_Z1 := 1.9
const CORRIDOR_H := 2.7
const CORRIDOR_LAMPS := [5.0, 7.6, 10.2]
var _corridor: Node3D
var _corridor_bulbs: Array[StandardMaterial3D] = []
var _corridor_lights: Array[OmniLight3D] = []


func _cbox(size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = size
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_corridor.add_child(mi)
	return mi


func _tiled(path: String, scale: float) -> Material:
	var m := (load("res://assets/materials/%s.tres" % path) as BaseMaterial3D).duplicate() as BaseMaterial3D
	m.uv1_triplanar = true
	m.uv1_scale = Vector3.ONE * scale
	return m


func _build_corridor() -> void:
	if _corridor != null:
		return
	_corridor = Node3D.new()
	_corridor.name = "corridor"
	add_child(_corridor)
	var L := CORRIDOR_X1 - CORRIDOR_X0
	var cx := (CORRIDOR_X0 + CORRIDOR_X1) * 0.5
	var cz := (CORRIDOR_Z0 + CORRIDOR_Z1) * 0.5
	var W := CORRIDOR_Z1 - CORRIDOR_Z0
	var plaster := _tiled("M_Plaster_Wall", 0.8)
	var green := _tiled("M_Paint_Green", 0.8)
	_cbox(Vector3(L, 0.05, W), Vector3(cx, -0.025, cz), _tiled("M_Linoleum", 0.9))
	_cbox(Vector3(L, 0.05, W), Vector3(cx, CORRIDOR_H + 0.025, cz), _tiled("M_Ceiling", 0.8))
	for side in [-1.0, 1.0]:
		var z: float = cz + side * (W * 0.5 + 0.05)
		_cbox(Vector3(L, CORRIDOR_H, 0.1), Vector3(cx, CORRIDOR_H * 0.5, z), plaster)
		_cbox(Vector3(L, 1.25, 0.02), Vector3(cx, 0.625, z - side * 0.06), green) # institutional green to the dado
		_cbox(Vector3(L, 0.12, 0.03), Vector3(cx, 0.06, z - side * 0.075), load("res://assets/materials/M_Wood_Walnut.tres"))
	# the far end: double doors under an enamel sign and an amber emergency lamp
	_cbox(Vector3(0.1, CORRIDOR_H, W), Vector3(CORRIDOR_X1 + 0.05, CORRIDOR_H * 0.5, cz), plaster)
	var wood: Material = load("res://assets/materials/M_Wood_Panel.tres")
	var brass: Material = load("res://assets/materials/M_Brass_Aged.tres")
	for side in [-1.0, 1.0]:
		_cbox(Vector3(0.05, 2.1, 0.66), Vector3(CORRIDOR_X1 - 0.03, 1.05, cz + side * 0.34), wood)
		_cbox(Vector3(0.04, 0.03, 0.12), Vector3(CORRIDOR_X1 - 0.07, 1.05, cz + side * 0.08), brass)
	_cbox(Vector3(0.06, 0.08, 1.48), Vector3(CORRIDOR_X1 - 0.03, 2.14, cz), wood)
	var sign := _cbox(Vector3(0.02, 0.22, 0.96), Vector3(CORRIDOR_X1 - 0.07, 2.42, cz), load("res://assets/materials/M_Enamel_Green.tres"))
	sign.name = "archive_sign"
	var text := Label3D.new()
	text.text = "obj2.hall" # "Records Archive B": the sign translates with the language
	text.font = load(UITheme.FONT_DISPLAY_BOLD)
	text.font_size = 72
	text.pixel_size = 0.0011
	text.modulate = Color("efe6cf")
	text.outline_size = 0
	text.double_sided = false
	text.position = Vector3(CORRIDOR_X1 - 0.085, 2.42, cz)
	text.rotation.y = deg_to_rad(-90.0)
	_corridor.add_child(text)
	var amber := StandardMaterial3D.new()
	amber.albedo_color = Color(0.4, 0.25, 0.1)
	amber.emission_enabled = true
	amber.emission = Color("ff9a3c")
	amber.emission_energy_multiplier = 0.0
	_cbox(Vector3(0.05, 0.08, 0.16), Vector3(CORRIDOR_X1 - 0.05, 2.6, cz), amber)
	_corridor_bulbs.append(amber)
	var em := OmniLight3D.new()
	em.light_color = Color("ff9a3c")
	em.light_energy = 0.0
	em.omni_range = 3.2
	em.position = Vector3(CORRIDOR_X1 - 0.4, 2.45, cz)
	_corridor.add_child(em)
	_corridor_lights.append(em)
	# ceiling lamps, nearest first: enamel shade, bulb, and a light for the first and the last
	var shade: Material = load("res://assets/materials/M_Enamel_White.tres")
	for i in CORRIDOR_LAMPS.size():
		var x: float = CORRIDOR_LAMPS[i]
		var sh := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.05
		cyl.bottom_radius = 0.17
		cyl.height = 0.12
		cyl.radial_segments = 16
		sh.mesh = cyl
		sh.material_override = shade
		sh.position = Vector3(x, CORRIDOR_H - 0.32, cz)
		sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_corridor.add_child(sh)
		_cbox(Vector3(0.012, 0.26, 0.012), Vector3(x, CORRIDOR_H - 0.13, cz), load("res://assets/materials/M_Steel_Dark.tres"))
		var bulb := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = 0.045
		sp.height = 0.09
		bulb.mesh = sp
		var bm := StandardMaterial3D.new()
		bm.albedo_color = Color(0.35, 0.3, 0.25)
		bm.emission_enabled = true
		bm.emission = Color("ffc58a")
		bm.emission_energy_multiplier = 0.0
		bulb.material_override = bm
		bulb.position = Vector3(x, CORRIDOR_H - 0.4, cz)
		bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_corridor.add_child(bulb)
		_corridor_bulbs.append(bm)
		if i != 1:
			var p := OmniLight3D.new()
			p.light_color = Color("ffc58a")
			p.light_energy = 0.0
			p.omni_range = 4.2
			p.omni_attenuation = 1.3
			p.position = Vector3(x, CORRIDOR_H - 0.55, cz)
			_corridor.add_child(p)
			_corridor_lights.append(p)


## Lamps on (a loaded save) or off.
func _corridor_lit(on: bool) -> void:
	for m in _corridor_bulbs:
		m.emission_energy_multiplier = 2.0 if on else 0.0
	for l in _corridor_lights:
		l.light_energy = (0.9 if l.light_color.r8 == 0xff and l.light_color.g8 == 0x9a else 1.3) if on else 0.0


## The door swings open and the corridor lamps flicker on one by one, toward the archive's sign at the far end.
func _wake_corridor() -> void:
	_build_corridor()
	var order := [1, 2, 3, 0] # bulbs: the three ceiling lamps nearest first, then the amber lamp over the sign
	var light_of := {1: 1, 3: 2, 0: 0} # bulb index -> light index (the middle lamp has no light of its own)
	await get_tree().create_timer(0.5).timeout
	for k in order.size():
		var b: int = order[k]
		var m := _corridor_bulbs[b]
		var target := 2.0 if b != 0 else 1.6
		var tw := create_tween()
		tw.tween_property(m, "emission_energy_multiplier", target * 0.8, 0.05)
		tw.tween_property(m, "emission_energy_multiplier", 0.1, 0.07)
		tw.tween_property(m, "emission_energy_multiplier", target, 0.25)
		if light_of.has(b):
			var l := _corridor_lights[light_of[b]]
			create_tween().tween_property(l, "light_energy", 0.9 if b == 0 else 1.3, 0.35)
		AudioManager.sfx("switch_toggle", -10.0 - 2.0 * k, 0.8 - 0.05 * k)
		if k == 1:
			hud.call("caption", tr("cap1.corridor"), 3.2)
		await get_tree().create_timer(0.45).timeout

