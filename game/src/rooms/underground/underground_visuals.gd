class_name UndergroundVisuals
extends Node
## Renders UndergroundLogic state onto the Chapter 3 models (docs/models/ch3.md): part poses, items in their places,
## lamps, the per-game evidence surfaces (§11), the echoes (§10), the 1979 loop in the port views (§2 M7) and the
## cinematic moments. Everything visible is derived from logic.state (plus a few purely visual flags such as the
## intro's gate), so a loaded save reproduces the scene. A model that is not built yet is simply skipped.

# ---------------------------------------------------------------- part motions (§3–§8)
const DOOR_SLIDE := 1.9
const GATE_FOLD := 0.15
const DRUM_STEP_DEG := -60.0
const HANDLE_PULL_DEG := 45.0
const LEVER_PULL_DEG := 50.0
const KNOB_STEP_DEG := -90.0
const OFFICE_DOOR_DEG := 100.0
const CASE_DIAL_DEG := -36.0
const CASE_LID_DEG := -100.0
const LOCK_OFF_DEG := -90.0
const WINDOW_OPEN_DEG := -100.0
const ISOLATOR_OFF_DEG := 90.0
const RACK_LOCK_SLIDE := -0.05
const STRIKER_DEG := 15.0
const HAMMER_DEG := 45.0
const BREAKER_DEG := 70.0
const AC_DOOR_DEG := -110.0
const PEG_STEP_DEG := -24.0
const START_LEVER_DEG := 60.0
const REMELT_PRESS := -0.006
const DRAWER_TRAVEL := 0.24
const PRISM_STEP_DEG := -12.0
const NUDGE_PRESS := -0.004
const CAMP_DOOR_SLIDE := -1.05
const SHUTTER_SLIDE := 0.58
const REC_KEY_DEG := -8.0
const VU_MAX_DEG := -70.0
const FREQ_DEG_AT_1 := 60.0
const FREQ_STEP_DEG := -30.0
const PORT_RING_DEG := -30.0
const METER_STEP_DEG := -15.0
const GROW_SECONDS := 8.0
# ---------------------------------------------------------------- the 1979 loop (§2 M7)
const LOOP_STEP := 2.5
const LOOP_FLICKER := 1.0
# ---------------------------------------------------------------- art
const DECALS := "res://assets/textures/decals/ch3/"
const SYMBOL_FILES: Array[String] = ["sym_sun", "sym_moon", "sym_star", "sym_triangle", "sym_circle", "sym_square"]
const WARM := Color("ffcf94")
const COLD := Color("e4f2ff")
const LUMEN := Color("cff6ff")
const AMBER := Color("ffaa3c")
const GREEN := Color("4dff7a")
const RED := Color("ff3b2f")
const BAND_COLOR := {1: Color(1.0, 0.25, 0.18), 2: Color(0.25, 1.0, 0.35), 4: Color(0.3, 0.45, 1.0)}

var room: Node3D
var logic: UndergroundLogic
var rest: Dictionary = {} # node -> rest Transform3D
## The entry gate stands open once the intro has arrived (the gates have no logic state, §15.3).
var gate_open := true
var intro_key := false # the entry key stands in its gate lock during the intro descent
var _tweens: Dictionary = {}
var _held: Dictionary = {} # key -> [item id, Node3D]
var _tubes: Dictionary = {} # meter reading -> IA_tube_<r>
var _hand_anchor: Node3D
var _meter_anchor: Node3D
var _meter_node: Node3D
var _mats: Dictionary = {} # name -> ShaderMaterial / material for evidence surfaces
var _textures: Dictionary = {}
var _echo_mat: ShaderMaterial
var _echoes: Dictionary = {} # id -> Node3D (kept echoes, the operator, Leyla's and Strand's figures)
var _fans: Array[MeshInstance3D] = []
var _fan_mat: StandardMaterial3D
var _arcs: Array[MeshInstance3D] = []
var _rising: MultiMeshInstance3D
var _rise_t := 0.0
var _view := ""
var _loop_port := ""
var _loop_t := 0.0
var _osc_amp := 0.0
var _osc_size := 0
var _recorder_playing := false
var _growing := false
var _drag_dir: Dictionary = {} # knob / turntable -> current tap direction (ping-pong between the end stops)


func _init(r: Node3D) -> void:
	room = r
	logic = r.get("logic")


func _ready() -> void:
	_record_rest()
	_echo_mat = ShaderMaterial.new()
	_echo_mat.shader = load("res://src/fx/echo.gdshader")
	_build_tubes()
	_build_hand()
	_build_evidence()
	_build_echoes()
	_build_fans()
	_build_arcs()
	_build_rising()
	_own_bulb_material()


# ====================================================================== lookups
func model(id: String) -> Node3D:
	return (room.get("models") as Dictionary).get(id)


func part(model_id: String, part_name: String) -> Node3D:
	return ModelUtil.find(model(model_id), part_name)


func _record_rest() -> void:
	for m: Node3D in (room.get("models") as Dictionary).values():
		_record(m)


func _record(n: Node) -> void:
	if n is Node3D and not rest.has(n):
		rest[n] = (n as Node3D).transform
	for c in n.get_children():
		if c is Node3D and not (c is StaticBody3D):
			_record(c)


func _tex(path: String) -> Texture2D:
	if not _textures.has(path):
		_textures[path] = load(path) if ResourceLoader.exists(path) else null
	return _textures[path]


func _cull_tag(n: Node3D, groups: String) -> void:
	room.call("tag_cull", n, groups)


# ====================================================================== construction
## The seven tubes: one spawn of choir_tube.glb, each IA_tube_<r> reparented to its place (§4).
func _build_tubes() -> void:
	if not ResourceLoader.exists("res://assets/models/choir_tube.glb"):
		return
	var tubes := ModelUtil.spawn("choir_tube", room, Transform3D.IDENTITY, "parts")
	if tubes == null:
		return
	for r in range(1, 8):
		var t := ModelUtil.find(tubes, "IA_tube_%d" % r)
		if t:
			_tubes[r] = t
	tubes.visible = false # only the container: the tubes are reparented to their places below


## In-hand anchors: the tube in hand hangs at the lower right, Strand's meter (while selected) at the lower left.
func _build_hand() -> void:
	var cam: Camera3D = room.get("cam")
	_hand_anchor = Node3D.new()
	_hand_anchor.name = "hand_tube"
	_hand_anchor.position = Vector3(0.2, -0.12, -0.5)
	_hand_anchor.rotation = Vector3(deg_to_rad(10.0), deg_to_rad(-20.0), deg_to_rad(62.0))
	cam.add_child(_hand_anchor)
	_meter_anchor = Node3D.new()
	_meter_anchor.name = "hand_meter"
	_meter_anchor.position = Vector3(-0.17, -0.11, -0.36)
	_meter_anchor.rotation = Vector3(deg_to_rad(8.0), deg_to_rad(18.0), 0.0)
	cam.add_child(_meter_anchor)


## The intro bulbs share M_Steel_Dark with the lamp cages (ch3_a.md): give them their own before glowing.
func _own_bulb_material() -> void:
	var b := part("shell_lift", "intro_bulbs") as MeshInstance3D
	if b == null or b.mesh == null:
		return
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("2b2620")
	m.emission_enabled = true
	m.emission = WARM
	m.emission_energy_multiplier = 3.0
	for i in b.mesh.get_surface_count():
		b.set_surface_override_material(i, m)


## Replace the surfaces of `mi` that carry `slot` (the Blender placeholder) with `mat`.
func _set_slot(mi: MeshInstance3D, slot: String, mat: Material) -> bool:
	if mi == null or mi.mesh == null or mat == null:
		return false
	var done := false
	for i in mi.mesh.get_surface_count():
		var src := mi.mesh.surface_get_material(i)
		if src != null and src.resource_name.begins_with(slot):
			mi.set_surface_override_material(i, mat)
			done = true
	return done


func _shader(path: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(path)
	return m


## Evidence surfaces (§11): every answer is drawn from this game's state, never baked.
func _build_evidence() -> void:
	# W3 the chalk staircase
	var stair := _shader("res://src/fx/stair_chalk.gdshader")
	stair.set_shader_parameter("grid", _tex(DECALS + "chalk_grid.png"))
	stair.set_shader_parameter("heights", PackedInt32Array(logic.choir_target()))
	_mats["stair"] = stair
	_set_slot(part("choir_rack", "stair_quad") as MeshInstance3D, "M_Shader_Quad", stair)
	# W4 step globes
	var globes := _shader("res://src/fx/step_globes.gdshader")
	# at the shader's default 2.6 the lit opal globes bloom to white blobs on a phone; 1.05 keeps them warm and clear
	globes.set_shader_parameter("energy", 1.05)
	_mats["globes"] = globes
	_set_slot(part("control_desk", "step_globes") as MeshInstance3D, "M_Enamel_Cream", globes)
	# E1 glyph panel, the open drawer's glyph, the log sketch
	var bits := PackedInt32Array()
	for g: Variant in logic.seed_glyphs():
		bits.append(_glyph_bits(str(g)))
	var panel := _shader("res://src/fx/hex_glyph.gdshader")
	panel.set_shader_parameter("bits", bits)
	panel.set_shader_parameter("grid", Vector2i(4, 3))
	panel.set_shader_parameter("style", 0)
	_mats["glyph_panel"] = panel
	_set_slot(part("seed_library", "glyph_panel") as MeshInstance3D, "M_Shader_Quad", panel)
	var open := _shader("res://src/fx/hex_glyph.gdshader")
	open.set_shader_parameter("grid", Vector2i(1, 1))
	open.set_shader_parameter("style", 0)
	_mats["glyph_open"] = open
	_set_slot(part("seed_library", "glyph_open") as MeshInstance3D, "M_Shader_Quad", open)
	var sketch := _shader("res://src/fx/hex_glyph.gdshader")
	var one := PackedInt32Array()
	one.append(_glyph_bits(logic.seed_sketch()))
	sketch.set_shader_parameter("bits", one)
	sketch.set_shader_parameter("grid", Vector2i(1, 1))
	sketch.set_shader_parameter("style", 1)
	_mats["sketch"] = sketch
	# E2 growth chart
	var chart := _shader("res://src/fx/growth_curve.gdshader")
	chart.set_shader_parameter("grid", _tex(DECALS + "growth_grid.png"))
	chart.set_shader_parameter("levels", _ivec3(logic.pegs_target()))
	_mats["chart"] = chart
	_set_slot(part("growth_chart", "chart_image") as MeshInstance3D, "M_Shader_Quad", chart)
	# E3 receptors
	for i in 3:
		var rec := _shader("res://src/fx/seal_receptor.gdshader")
		rec.set_shader_parameter("rim", int(logic.rims()[i]))
		rec.set_shader_parameter("sym_triangle", _tex(DECALS + "sym_triangle.png"))
		rec.set_shader_parameter("sym_circle", _tex(DECALS + "sym_circle.png"))
		rec.set_shader_parameter("sym_square", _tex(DECALS + "sym_square.png"))
		_mats["receptor_%d" % i] = rec
		_set_slot(part("seal_door", "receptor_%d" % i) as MeshInstance3D, "M_Shader_Quad", rec)
	# E4 oscillograph
	var osc := _shader("res://src/fx/osc_wave.gdshader")
	_mats["osc"] = osc
	_set_slot(part("oscillograph", "osc_screen") as MeshInstance3D, "M_Shader_Quad", osc)
	# H1 the ring symbols: one emissive decal per ring, from this game's drum target
	for r in 4:
		var q := part("array_below", "ring_sym_%d" % r) as MeshInstance3D
		var sm := StandardMaterial3D.new()
		sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		sm.alpha_scissor_threshold = 0.4
		sm.albedo_texture = _tex(DECALS + SYMBOL_FILES[int(logic.drum_target()[r])] + ".png")
		sm.albedo_color = LUMEN
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		_mats["ring_sym_%d" % r] = sm
		_set_slot(q, "M_Shader_Quad", sm)
	# H2 Strand's plate (engraved) and the live scope
	var plate := _shader("res://src/fx/lissajous.gdshader")
	plate.set_shader_parameter("fa", int(logic.freq_target()[0]))
	plate.set_shader_parameter("fb", int(logic.freq_target()[1]))
	plate.set_shader_parameter("mode", 0)
	plate.set_shader_parameter("aspect", 0.18 / 0.14)
	_mats["plate"] = plate
	_set_slot(part("gallery_console", "IA_strand_plate") as MeshInstance3D, "M_Shader_Quad", plate)
	var scope := _shader("res://src/fx/lissajous.gdshader")
	scope.set_shader_parameter("mode", 1)
	scope.set_shader_parameter("extent", 0.36)
	_mats["scope"] = scope
	_set_slot(part("gallery_console", "scope_screen") as MeshInstance3D, "M_Shader_Quad", scope)
	# the rings dim while the Array sleeps (own copies of the shared lumen material)
	for r in 4:
		var ring := part("array_below", "ring_%d" % r) as MeshInstance3D
		if ring and ring.mesh:
			var m := (ring.get_active_material(0) as BaseMaterial3D)
			if m:
				var u := m.duplicate() as BaseMaterial3D
				ring.set_surface_override_material(0, u)
				_mats["ring_%d" % r] = u
	# the drum symbols: cream enamel instead of the model's dark steel, or they vanish in the shrouded windows
	var cream := StandardMaterial3D.new()
	cream.albedo_color = Color(0.94, 0.9, 0.8)
	cream.roughness = 0.5
	cream.emission_enabled = true
	cream.emission = Color(1.0, 0.94, 0.8)
	cream.emission_energy_multiplier = 0.3
	for side: String in ["west", "east"]:
		for i in 4:
			_set_slot(part("door_" + side, "IA_drum_%d" % i) as MeshInstance3D, "M_Steel_Dark", cream)
	# the recorder's two piano keys: dark Bakelite on the dark leather body hid the raised ◀◀ / ▶ from the recorder view,
	# so they are ivory like piano keys, with a trace of emission against the dim camp
	var ivory := StandardMaterial3D.new()
	ivory.albedo_color = Color(0.9, 0.85, 0.7)
	ivory.roughness = 0.45
	ivory.emission_enabled = true
	ivory.emission = Color(1.0, 0.92, 0.75)
	ivory.emission_energy_multiplier = 0.2
	for key_name: String in ["IA_rec_rewind", "IA_rec_play"]:
		_set_slot(part("field_recorder", key_name) as MeshInstance3D, "M_Bakelite", ivory)


static func _glyph_bits(g: String) -> int:
	var b := 0
	for e in mini(6, g.length()):
		if g[e] == "1":
			b |= 1 << e
	return b


static func _ivec3(a: Array) -> Vector3i:
	return Vector3i(int(a[0]), int(a[1]), int(a[2]))


## Echo figures (§10): one instance per figure and place, each showing one pose; all start hidden.
func _build_echoes() -> void:
	for id: String in UndergroundData.ECHOES:
		var e: Array = UndergroundData.ECHOES[id]
		var mount := _echo_mount(id)
		var n := _make_echo(id, e[0], e[1], mount, e[2])
		if n:
			room.call("add_tap_area", n, Vector3(0.9, 1.7, 0.9), "", "Echo_" + id, Vector3(0, 0.85, 0))
	_make_echo("operator", "echo_operator", "pose_idle", Transform3D.IDENTITY, "C")
	_make_echo("leyla_touch", "echo_leyla_1998", "pose_touch_1", Transform3D.IDENTITY, "N")
	_make_echo("leyla_kneel", "echo_leyla_1998", "pose_kneel", _echo_mount("leyla_kneel"), "G")
	var so := _make_echo("strand_offer", "echo_strand_rail", "pose_offer", _echo_mount("strand_offer"), "G")
	var lo := _make_echo("leyla_offer", "echo_leyla_1998", "pose_offer", _echo_mount("leyla_offer"), "G")
	# their offerings: Strand's fork in his fist, Leyla's crystal on her palm
	if so:
		var fm := ModelUtil.find(so, "fork_mount")
		if fm:
			ModelUtil.spawn("strand_fork", fm, Transform3D.IDENTITY, "none")
	if lo:
		var cm := ModelUtil.find(lo, "crystal_mount")
		if cm:
			var c := ModelUtil.spawn("nursery_crystal", cm, Transform3D.IDENTITY, "none")
			_glow(c, true)


func _echo_mount(id: String) -> Transform3D:
	var mount: Node3D = null
	match id:
		"welder":
			mount = part("transformer_1", "echo_mount")
		"tech_a":
			mount = part("dead_0", "echo_mount")
		"tech_b":
			mount = part("dead_1", "echo_mount")
		"strand_rail":
			mount = part("shell_gallery", "echo_rail_mount")
		"strand_offer":
			mount = part("shell_gallery", "echo_strand_mount")
		"leyla_offer":
			mount = part("shell_gallery", "echo_leyla_mount")
		"leyla_kneel":
			mount = part("memorial_wall", "echo_kneel_mount")
	if mount and mount.is_inside_tree():
		return mount.global_transform
	var f: Array = UndergroundData.MOUNT_FALLBACK.get(id, [Vector3.ZERO, 0.0])
	return Transform3D(Basis(Vector3.UP, deg_to_rad(float(f[1]))), f[0])


func _make_echo(id: String, model_name: String, pose: String, xf: Transform3D, groups: String) -> Node3D:
	if not ResourceLoader.exists("res://assets/models/%s.glb" % model_name):
		return null
	var n: Node3D = room.call("spawn", "echo_" + id, model_name, xf.origin, 0.0, "", "none")
	if n == null:
		return null
	n.global_transform = xf
	var mat := _echo_mat.duplicate() as ShaderMaterial
	for mi in ModelUtil.find_meshes(n):
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_show_pose(n, pose)
	_cull_tag(n, groups)
	room.call("set_present", n, false)
	_echoes[id] = n
	return n


## Show one pose object of an echo GLB (poses are root-level meshes; their empties follow them).
func _show_pose(n: Node3D, pose: String) -> void:
	if n == null:
		return
	for c in n.get_children():
		if c is MeshInstance3D:
			(c as MeshInstance3D).visible = str(c.name) == pose
	n.set_meta("pose", pose)


func _set_echo(id: String, show: bool) -> void:
	var n: Node3D = _echoes.get(id)
	if n == null or bool(n.get_meta("present", false)) == show:
		return
	room.call("set_present", n, show)
	if show:
		_fade(n, 0.0, 0.85, 0.8)


func _echo_intensity(n: Node3D, v: float) -> void:
	for mi in ModelUtil.find_meshes(n):
		var m := mi.material_override as ShaderMaterial
		if m:
			m.set_shader_parameter("intensity", v)


func _fade(n: Node3D, from: float, to: float, dur: float) -> void:
	if n == null:
		return
	room.create_tween().tween_method(func(v: float) -> void: _echo_intensity(n, v), from, to, dur)


## The two prism fans: one mesh each, rebuilt from the prism positions (§11 E3).
func _build_fans() -> void:
	_fan_mat = StandardMaterial3D.new()
	_fan_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_fan_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_fan_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_fan_mat.vertex_color_use_as_albedo = true
	_fan_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_fan_mat.no_depth_test = false
	for k in 2:
		var mi := MeshInstance3D.new()
		mi.name = "fan_" + ["p", "q"][k]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.material_override = _fan_mat
		room.add_child(mi)
		_cull_tag(mi, "N")
		_fans.append(mi)


func _fan_origin(which: String) -> Vector3:
	var e := part("prism_bench", "fan_origin_" + which)
	if e:
		return e.global_position
	return Vector3(6.1 + (-0.28 if which == "p" else 0.28), 1.0, 0.28)


## Receptor i's fixed point (§1.3); out of range, the band falls on the door or the wall beside it.
func _receptor_point(idx: int) -> Vector3:
	if idx >= 0 and idx <= 2:
		return Vector3(UndergroundData.RECEPTOR_X[idx], UndergroundData.RECEPTOR_Y, UndergroundData.RECEPTOR_Z + 0.004)
	return Vector3(6.1 + 0.3 * (idx - 1), UndergroundData.RECEPTOR_Y, UndergroundData.RECEPTOR_Z - 0.06)


func _apply_fans() -> void:
	if _fans.is_empty():
		return
	var s := logic.state
	for k in 2:
		var which: String = ["p", "q"][k]
		var v := int(s["prism_" + which])
		var bands: Array[int] = UndergroundLogic.P_BANDS if which == "p" else UndergroundLogic.Q_BANDS
		var o := _fan_origin(which)
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for b in 3:
			var tgt := _receptor_point(v + b)
			var side := Vector3(0.05, 0, 0)
			var c: Color = BAND_COLOR[bands[b]]
			var tip := Color(c, 0.0)
			var end := Color(c, 0.55)
			st.set_color(tip)
			st.add_vertex(o)
			st.set_color(end)
			st.add_vertex(tgt - side)
			st.set_color(end)
			st.add_vertex(tgt + side)
		_fans[k].mesh = st.commit()


## The Jacob's-ladder arcs between each transformer's arc_base and arc_top (lit once the hall runs).
func _build_arcs() -> void:
	var sh: Shader = load("res://src/fx/jacob_arc.gdshader")
	for i in 3:
		var base := part("transformer_%d" % i, "arc_base")
		var top := part("transformer_%d" % i, "arc_top")
		if base == null or top == null:
			continue
		var mi := MeshInstance3D.new()
		var q := QuadMesh.new()
		var h := base.global_position.distance_to(top.global_position)
		q.size = Vector2(0.40, maxf(0.2, h))
		mi.mesh = q
		var m := ShaderMaterial.new()
		m.shader = sh
		m.set_shader_parameter("phase", 0.31 * i)
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		model("transformer_%d" % i).add_child(mi)
		mi.global_transform = Transform3D(model("transformer_%d" % i).global_basis, (base.global_position + top.global_position) * 0.5)
		mi.visible = false
		_arcs.append(mi)


## The 41 lights that rise up the shaft once the Array answers: one MultiMesh (§3 array_below).
func _build_rising() -> void:
	_rising = MultiMeshInstance3D.new()
	_rising.name = "rising_lights"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var sphere := SphereMesh.new()
	sphere.radius = 0.06
	sphere.height = 0.12
	sphere.radial_segments = 8
	sphere.rings = 4
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = LUMEN
	m.emission_enabled = true
	m.emission = LUMEN
	m.emission_energy_multiplier = 4.0
	sphere.material = m
	mm.mesh = sphere
	mm.instance_count = 41
	_rising.multimesh = mm
	_rising.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_rising.visible = false
	_rising.set_meta("present", false) # until the Array answers (set_present)
	room.add_child(_rising)
	_cull_tag(_rising, "GS")


# ====================================================================== items in places
func _held_item(key: String, item_id: String, mount: Node3D, show: bool, part_name: String = "") -> Node3D:
	var cur: Array = _held.get(key, [])
	var want := item_id if show else ""
	if not cur.is_empty() and (cur[0] != want or not is_instance_valid(cur[1])):
		if is_instance_valid(cur[1]):
			# leave the tree now: a node that is only queued for freeing keeps its name, and its replacement would be
			# renamed "Item_chamber2", which no hotspot or QA tap finds
			var old := cur[1] as Node3D
			if old.get_parent():
				old.get_parent().remove_child(old)
			old.queue_free()
		_held.erase(key)
		cur = []
	if want == "" or mount == null:
		return null
	if cur.is_empty():
		var n := ModelUtil.spawn(ItemDB.model_path(item_id), mount, Transform3D.IDENTITY, "none")
		if n == null:
			return null
		n.name = part_name if part_name != "" else "Held_" + key
		if part_name != "":
			_add_item_collider(n, part_name)
		ItemDress.apply(item_id, n, logic)
		if item_id == "nursery_crystal":
			_glow(n, true)
		_held[key] = [want, n]
		return n
	return cur[1]


func _add_item_collider(n: Node3D, part_name: String) -> void:
	var aabb := ItemIcons._aabb(n)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = (aabb.size + Vector3.ONE * 0.03).max(Vector3.ONE * 0.06)
	cs.shape = box
	cs.position = n.global_transform.affine_inverse() * aabb.get_center() if n.is_inside_tree() else aabb.get_center()
	body.add_child(cs)
	body.set_meta("part", part_name)
	n.add_child(body)


# ====================================================================== main entry
func apply_state(animated: bool) -> void:
	_apply_lift(animated)
	_apply_doors(animated)
	_apply_choir(animated)
	_apply_office(animated)
	_apply_cabinets(animated)
	_apply_desk(animated)
	_apply_rack(animated)
	_apply_gallery(animated)
	_apply_nursery(animated)
	_apply_camp(animated)
	_apply_fans()
	refresh_presence()


## Visibility and tap colliders of things that come and go (items, echoes). Called again after culling.
func refresh_presence() -> void:
	_apply_echoes()
	var meter_sel := logic.selected == "resonance_meter"
	if meter_sel and _meter_node == null:
		_meter_node = ModelUtil.spawn("resonance_meter", _meter_anchor, Transform3D.IDENTITY, "none")
		if _meter_node:
			_meter_node.name = "Hand_meter"
			_meter_node.scale = Vector3.ONE * 0.9
			for mi in ModelUtil.find_meshes(_meter_node):
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if _meter_node:
		_meter_node.visible = meter_sel


func _apply_lift(animated: bool) -> void:
	var entry := str(logic.state["entry"])
	var side := "west" if entry == "choir" else "east"
	for g: String in ["west", "east"]:
		var gate := part("freight_lift", "IA_gate_" + g)
		if gate == null:
			continue
		var base: Transform3D = rest.get(gate, gate.transform)
		var open := gate_open and g == side
		_to(gate, Transform3D(base.basis * Basis.from_scale(Vector3(1, 1, GATE_FOLD if open else 1.0)), base.origin), animated, 1.1)
	var key := "strand_key" if entry == "choir" else "leyla_key"
	_held_item("gate_key", key, part("freight_lift", "gate_key_mount_" + side), intro_key)
	_lamp(part("freight_lift", "cage_bulb"), true, WARM, 3.0)


func _apply_doors(animated: bool) -> void:
	var s := logic.state
	var sealed := logic.sealed_door()
	for side: String in ["west", "east"]:
		var id := "door_" + side
		var open: bool = s["door_%s_open" % side]
		_slide(part(id, "IA_blast_door"), Vector3(DOOR_SLIDE if open else 0.0, 0, 0), animated, 3.0)
		for i in 4:
			var v := int(s["drums"][i]) if side == sealed else 0
			_rot(part(id, "IA_drum_%d" % i), Vector3.RIGHT, DRUM_STEP_DEG * v, animated, 0.25)
		var lamp_on := open or (side == sealed and bool(s["gallery_awake"]))
		_lamp(part(id, "drum_lamp"), lamp_on, GREEN if open else AMBER, 2.5)


func _apply_choir(_animated: bool) -> void:
	var s := logic.state
	for k in 6:
		_lamp(part("shell_choir", "lamp_glass_%d" % k), true, WARM, 2.6)
	var running: bool = s["hall_started"]
	for i in 3:
		_lamp(part("transformer_%d" % i, "hum_lamp"), true, GREEN if running else RED, 2.0)
	for a in _arcs:
		a.visible = running


func _apply_office(animated: bool) -> void:
	var s := logic.state
	var taken: Dictionary = s["taken"]
	_rot(part("strand_office", "IA_office_door"), Vector3.UP, OFFICE_DOOR_DEG if s["office_open"] else 0.0, animated, 1.2)
	_held_item("office_key", "key_square", part("strand_office", "office_key_mount"), s["office_key"], "Item_office_key")
	_held_item("office_lamp", "ecg_strip", part("office_desk", "ecg_mount"), not taken.get("office_lamp", false), "Item_office_lamp")
	_held_item("office_letters", "strand_letters", part("office_desk", "letters_mount"), not taken.get("office_letters", false), "Item_office_letters")
	_lamp(part("office_desk", "office_bulb"), true, WARM, 3.0)
	for i in 3:
		_rot(part("meter_case", "IA_case_dial_%d" % i), Vector3.RIGHT, CASE_DIAL_DEG * int(s["case_wheels"][i]), animated, 0.2)
	_rot(part("meter_case", "case_lid"), Vector3.RIGHT, CASE_LID_DEG if s["case_open"] else 0.0, animated, 0.9)
	_held_item("meter_case", "resonance_meter", part("meter_case", "meter_mount"), not taken.get("meter_case", false), "Item_meter_case")


func _apply_cabinets(animated: bool) -> void:
	var s := logic.state
	for n in 3:
		var id := "cabinet_%d" % n
		if model(id) == null:
			continue
		var on: bool = s["iso"][n]
		_rot(part(id, "IA_isolator"), Vector3.BACK, 0.0 if on else ISOLATOR_OFF_DEG, animated, 0.35)
		_rot(part(id, "IA_lock"), Vector3.UP, 0.0 if on else LOCK_OFF_DEG, animated, 0.35)
		_rot(part(id, "IA_key_window"), Vector3.RIGHT, 0.0 if on else WINDOW_OPEN_DEG, animated, 0.5)
		_lamp(part(id, "iso_lamp"), true, GREEN if on else RED, 2.5)
		var cin: String = s["cab_in"][n]
		_held_item("cab_in_%d" % n, cin, part(id, "lock_key_mount"), cin != "", "Item_cab_in_%d" % n)
		_held_item("cab_held_%d" % n, UndergroundLogic.CABINET_HOLDS[n], part(id, "held_key_mount"), s["cab_held"][n],
			"Item_cab_held_%d" % n)
		# only the cabinet's own numeral and lock symbol
		for k in 3:
			var num := part(id, "num_%d" % (k + 1))
			if num:
				num.visible = k == n
		var own: String = UndergroundLogic.CABINET_TAKES[n].substr(4)
		for sym: String in ["diamond", "triangle", "circle", "square"]:
			var p := part(id, "lock_sym_" + sym)
			if p:
				p.visible = sym == own


func _apply_desk(animated: bool) -> void:
	var s := logic.state
	if _loop_port != "":
		return # the 1979 loop owns the desk while a port view is open
	for n in range(1, 6):
		_rot(part("control_desk", "IA_lever_%d" % n), Vector3.RIGHT, LEVER_PULL_DEG if int(s["levers"][n - 1]) == 1 else 0.0, animated, 0.3)
	_rot(part("control_desk", "IA_master_knob"), Vector3.BACK, KNOB_STEP_DEG * int(s["knob"]), animated, 0.3)
	_set_globes(int(s["step"]) if not s["hall_started"] else 5)
	_held_item("desk_hook", UndergroundLogic.DESK_KEY, part("control_desk", "desk_hook_mount"), s["desk_hook"], "Item_desk_hook")
	_lamp(part("control_desk", "desk_live_lamp"), logic.desk_live(), GREEN, 2.5)
	var tag := part("control_desk", "lockout_tag")
	if tag:
		tag.visible = not s["desk_armed"]


func _set_globes(lit: int) -> void:
	var g: ShaderMaterial = _mats.get("globes")
	if g:
		g.set_shader_parameter("lit", lit)


func _apply_rack(animated: bool) -> void:
	var s := logic.state
	var t: Array = s["tubes"]
	var hand := int(s["tube_hand"])
	for r: int in _tubes:
		var tube: Node3D = _tubes[r]
		var mount: Node3D = null
		var pos := t.find(r)
		if hand == r:
			mount = _hand_anchor
		elif pos >= 0 and pos < UndergroundLogic.SLOTS:
			mount = part("choir_rack", "slot_mount_%d" % pos)
		elif pos >= UndergroundLogic.SLOTS:
			mount = part("tube_bench", "bench_mount_%d" % (pos - UndergroundLogic.SLOTS))
		if mount == null:
			tube.visible = false
			continue
		tube.visible = true
		if tube.get_parent() != mount:
			tube.reparent(mount, false)
		_to(tube, Transform3D.IDENTITY, false, 0.0)
	_slide(part("choir_rack", "rack_lock"), Vector3(0, RACK_LOCK_SLIDE if s["choir_tuned"] else 0.0, 0), animated, 0.6)


func _apply_gallery(animated: bool) -> void:
	var s := logic.state
	var awake: bool = s["gallery_awake"]
	var array: bool = s["array_awake"]
	# asleep the rings are dormant glass (a cool grey tint, almost no emission); awake they glow but stay under the
	# glow threshold (1.1, RoomBase.make_environment), so only the answering Array blooms
	for r in 4:
		var m := _mats.get("ring_%d" % r) as BaseMaterial3D
		if m:
			# answering: a cyan glow, not flat white (2.2 on near-white glass clipped the rings and their symbols to white)
			m.emission = Color(0.25, 0.7, 1.0) if array else Color(0.8118, 0.9647, 1.0) # the library lumen: x1.5 clipped to white
			m.emission_energy_multiplier = 1.3 if array else (0.55 if awake else 0.15)
			m.albedo_color = Color(0.4, 0.75, 0.92) if array else (Color(0.55, 0.7, 0.78) if awake else Color(0.4, 0.48, 0.53))
		var sym := _mats.get("ring_sym_%d" % r) as BaseMaterial3D
		if sym:
			sym.albedo_color = Color(LUMEN, 1.0) * (1.0 if awake else 0.45)
	var up := (room.get("lights") as Dictionary).get("array_up") as Light3D
	if up:
		up.light_energy = 2.2 if array else (2.0 if awake else 1.0)
	for k in 5:
		_lamp(part("shell_gallery", "lamp_glass_%d" % k), true, Color("ffe6c4"), 2.2)
	# console
	for axis: String in ["x", "y"]:
		var v := int(s["freq_" + axis])
		_rot(part("gallery_console", "IA_knob_" + axis), Vector3.BACK, FREQ_DEG_AT_1 + FREQ_STEP_DEG * (v - 1), animated, 0.25)
	var scope: ShaderMaterial = _mats.get("scope")
	if scope:
		scope.set_shader_parameter("fa", int(s["freq_x"]))
		scope.set_shader_parameter("fb", int(s["freq_y"]))
		scope.set_shader_parameter("live", logic.scope_live())
	_lamp(part("gallery_console", "lamp_choir"), s["hall_started"], AMBER, 1.5)
	_lamp(part("gallery_console", "lamp_nursery"), s["shutter_open"], LUMEN, 1.5)
	var cradled: String = s["cradle"]
	_held_item("cradle", cradled, part("gallery_console", "cradle_mount"), cradled != "", "Item_cradle")
	_lamp(part("gallery_console", "cradle_ring"), cradled != "", LUMEN, 2.0)
	var choice: String = s["choice"]
	_held_item("choice", "strand_fork" if choice == "strand" else "nursery_crystal", part("gallery_console", "choice_mount"), choice != "")
	# memorial
	_lamp(part("memorial_wall", "memorial_crystals"), true, LUMEN, 1.7 if array else 0.7)
	_lamp(part("memorial_wall", "socket_42_ring"), s["secret"], LUMEN, 1.5)
	var sock: String = s["socket_42"]
	_held_item("socket_42", sock, part("memorial_wall", "socket_42_mount"), sock != "", "Item_socket_42")
	if _rising:
		room.call("set_present", _rising, array) # not .visible: zone culling rewrites that on every view change


func _apply_nursery(animated: bool) -> void:
	var s := logic.state
	for k in 5:
		_lamp(part("shell_nursery", "lamp_glass_%d" % k), true, COLD, 2.4)
	# autoclave
	_rot(part("autoclave", "IA_ac_door"), Vector3.UP, 0.0 if s["ac_closed"] else AC_DOOR_DEG, animated, 0.9)
	for i in 3:
		_rot(part("autoclave", "IA_peg_%d" % i), Vector3.RIGHT, PEG_STEP_DEG * (int(s["pegs"][i]) - 1), animated, 0.25)
	var item := {"seed": "seed_crystal", "clear": "nursery_crystal", "cloudy": "cloudy_crystal"}.get(str(s["chamber"]), "") as String
	var ch := _held_item("chamber", item, part("autoclave", "chamber_mount"), item != "", "Item_chamber")
	if ch and not _growing:
		var body := ModelUtil.find(ch, "crystal_body")
		if body:
			body.scale = Vector3.ONE
	var lamp_c := AMBER if _growing else (GREEN if s["chamber"] == "clear" else (RED if s["chamber"] == "cloudy" else Color.BLACK))
	_lamp(part("autoclave", "ac_lamp"), _growing or s["chamber"] in ["clear", "cloudy"], lamp_c, 2.5)
	_lamp(part("autoclave", "growth_window"), _growing or s["chamber"] == "clear", LUMEN, 0.9 if not _growing else 2.2)
	# growth log sketch (the log is spawned on the autoclave's log_mount)
	_set_slot(part("growth_log", "log_sketch") as MeshInstance3D, "M_Shader_Quad", _mats.get("sketch"))
	# seed library
	var open := int(s["seed_drawer"])
	var from := int(s["seed_from"])
	for i in 12:
		var d := part("seed_library", "IA_seed_drawer_%d" % i)
		if d == null:
			continue
		_slide(d, Vector3(0, 0, DRAWER_TRAVEL if open == i else 0.0), animated, 0.45)
		_held_item("seed_%d" % i, "seed_crystal", part("seed_library", "seed_mount_%d" % i), i != from, "Item_seed_%d" % i)
	var panel: ShaderMaterial = _mats.get("glyph_panel")
	if panel:
		panel.set_shader_parameter("hidden", open)
	_place_open_glyph(open)
	# prisms
	_rot(part("prism_bench", "IA_prism_p"), Vector3.UP, PRISM_STEP_DEG * int(s["prism_p"]), animated, 0.3)
	_rot(part("prism_bench", "IA_prism_q"), Vector3.UP, PRISM_STEP_DEG * int(s["prism_q"]), animated, 0.3)
	_lamp(part("prism_bench", "prism_lamp"), true, Color("fff4dc"), 3.0)
	# the seal
	_slide(part("seal_door", "IA_camp_door"), Vector3(CAMP_DOOR_SLIDE if s["camp_open"] else 0.0, 0, 0), animated, 2.2)
	var light := UndergroundLogic.receptor_light(int(s["prism_p"]), int(s["prism_q"]))
	for i in 3:
		var rec: ShaderMaterial = _mats.get("receptor_%d" % i)
		if rec:
			rec.set_shader_parameter("light", light[i])
			rec.set_shader_parameter("accepted", s["camp_open"])


## The open drawer's own glyph rides on its front (§6 glyph_open).
func _place_open_glyph(open: int) -> void:
	var g := part("seed_library", "glyph_open") as MeshInstance3D
	if g == null:
		return
	if open < 0:
		g.visible = false
		return
	var drawer := part("seed_library", "IA_seed_drawer_%d" % open)
	if drawer == null:
		g.visible = false
		return
	if g.get_parent() != drawer:
		g.reparent(drawer, false)
	var centre := g.mesh.get_aabb().get_center() if g.mesh else Vector3.ZERO
	g.transform = Transform3D(Basis.IDENTITY, Vector3(0, 0.02, 0.002) - centre)
	g.visible = true
	var m: ShaderMaterial = _mats.get("glyph_open")
	if m:
		var one := PackedInt32Array()
		one.append(_glyph_bits(str(logic.seed_glyphs()[open])))
		m.set_shader_parameter("bits", one)


func _apply_camp(animated: bool) -> void:
	var s := logic.state
	_lamp(part("leyla_camp", "camp_bulb"), true, WARM, 3.0)
	# the crystals hang in this game's order
	var frame: Array = logic.frame_sizes()
	for p in frame.size():
		var c := part("crystal_shutter", "IA_tcrystal_%d" % int(frame[p]))
		var mount := part("crystal_shutter", "frame_mount_%d" % p)
		if c and mount and c.get_parent() != mount:
			c.reparent(mount, false)
			c.transform = Transform3D.IDENTITY
			rest[c] = c.transform
	var open: bool = s["shutter_open"]
	_slide(part("crystal_shutter", "shutter_leaf_l"), Vector3(-SHUTTER_SLIDE if open else 0.0, 0, 0), animated, 1.8)
	_slide(part("crystal_shutter", "shutter_leaf_r"), Vector3(SHUTTER_SLIDE if open else 0.0, 0, 0), animated, 1.8)


# ====================================================================== echoes
func _apply_echoes() -> void:
	var s := logic.state
	var released: Array = s["echoes"]
	var mem := _view.ends_with("_mem")
	var in_port := ""
	if mem:
		in_port = _view.substr(5, 1).to_upper()
	for id: String in UndergroundData.ECHOES:
		var seen := false
		if not released.has(id):
			if mem:
				seen = logic.echo_visible(id, true) and _port_of(id) == in_port
			else:
				seen = logic.echo_visible(id)
		_set_echo(id, seen)
	var finale: bool = s["array_awake"]
	_set_echo("strand_offer", finale)
	_set_echo("leyla_offer", finale)
	if _loop_port == "":
		_set_echo("operator", false)


## Which crystal port keeps each echo's moment (§2: A the technicians, B the welder, C Strand at the rail).
static func _port_of(id: String) -> String:
	match id:
		"tech_a", "tech_b":
			return "A"
		"welder":
			return "B"
		"strand_rail":
			return "C"
	return ""


func release_echo(id: String) -> void:
	var n: Node3D = _echoes.get(id)
	if n == null:
		return
	room.call("set_present", n, true)
	_fade(n, 0.85, 0.0, 1.4)
	get_tree().create_timer(1.45).timeout.connect(func() -> void:
		room.call("set_present", n, false)
		refresh_presence())


func selection_changed(_id: String) -> void:
	refresh_presence()


## Leave path: Leyla, 1998, touches drawer i of the seed library and fades (§10).
func leyla_touch(i: int) -> void:
	var n: Node3D = _echoes.get("leyla_touch")
	var row := i / UndergroundLogic.SEED_COLUMNS
	var col := i % UndergroundLogic.SEED_COLUMNS
	var drawer := part("seed_library", "IA_seed_drawer_%d" % i) as MeshInstance3D
	if n:
		var mount := part("seed_library", "echo_touch_mount_%d" % col)
		if mount:
			n.global_transform = mount.global_transform
		else:
			# library-local (x_c + 0.40, 0, 0.87), facing the library (§6)
			var lib := Transform3D(Basis(Vector3.UP, deg_to_rad(-90.0)), Vector3(13.0, 0.0, -0.6))
			var x_c := (col - 1.5) * 0.33
			n.global_transform = lib * Transform3D(Basis(Vector3.UP, PI), Vector3(x_c + 0.40, 0.0, 0.87))
		_show_pose(n, "pose_touch_%d" % row)
		room.call("set_present", n, true)
		_fade(n, 0.0, 0.9, 1.0)
	AudioManager.sfx("reveal", -4.0, 0.85)
	await get_tree().create_timer(1.3).timeout
	if drawer:
		ModelUtil.set_emission(drawer, true, LUMEN, 1.2)
	await get_tree().create_timer(2.6).timeout
	_fade(n, 0.9, 0.0, 1.4)
	await get_tree().create_timer(1.4).timeout
	if n:
		room.call("set_present", n, false)
	await get_tree().create_timer(1.5).timeout
	if drawer:
		ModelUtil.set_emission(drawer, false)


## The secret: Leyla, 1998, kneels by the 42nd socket and lays her hand on it.
func leyla_kneel(seconds: float) -> void:
	var n: Node3D = _echoes.get("leyla_kneel")
	if n == null:
		await get_tree().create_timer(seconds).timeout
		return
	room.call("set_present", n, true)
	_fade(n, 0.0, 0.9, 1.2)
	await get_tree().create_timer(seconds - 1.4).timeout
	_fade(n, 0.9, 0.0, 1.4)
	await get_tree().create_timer(1.4).timeout
	room.call("set_present", n, false)


# ====================================================================== views
## The room tells the visuals which view is open: echoes seen through ports, the 1979 loop.
func view_changed(id: String) -> void:
	_view = id
	var port := ""
	if id in ["port_a", "port_b", "port_c"]:
		port = id.substr(5, 1).to_upper()
	if port != _loop_port:
		_loop_port = port
		_loop_t = 0.0
		if port == "":
			_set_echo("operator", false)
			apply_state(false)
	refresh_presence()


func _process(delta: float) -> void:
	if _loop_port != "":
		_play_loop(delta)
	if _rising and _rising.visible:
		_rise(delta)
	if _osc_amp > 0.0:
		_osc_amp = maxf(0.0, _osc_amp - delta * 0.35)
		var osc: ShaderMaterial = _mats.get("osc")
		if osc:
			osc.set_shader_parameter("amp", _osc_amp)
	if _recorder_playing:
		for r in ["reel_l", "reel_r"]:
			var reel := part("field_recorder", r)
			if reel:
				reel.rotate_object_local(Vector3.UP, -delta * 3.5)
		var vu := part("field_recorder", "rec_vu")
		if vu and rest.has(vu):
			var amp := 0.45 + 0.35 * sin(Time.get_ticks_msec() * 0.009) * sin(Time.get_ticks_msec() * 0.0023)
			vu.transform = Transform3D((rest[vu] as Transform3D).basis * Basis(Vector3.BACK, deg_to_rad(VU_MAX_DEG * clampf(amp, 0.0, 1.0))), (rest[vu] as Transform3D).origin)
	var arcs_on: bool = logic.state["hall_started"]
	if arcs_on:
		var flick := 0.8 + 0.4 * randf()
		var L: Dictionary = room.get("lights")
		var arc_light := L.get("arcs") as OmniLight3D
		if arc_light and arc_light.visible:
			arc_light.light_energy = 0.9 * flick


## The 1979 operator starts the hall in a loop, as port X saw it (§2 M7): step k pulls lever v_startup[k - 1]; the
## operator and the lever move only at the steps whose lever this port can see; the globes always show the step.
func _play_loop(delta: float) -> void:
	_loop_t += delta
	var slot := LOOP_STEP + LOOP_FLICKER
	var t := fmod(_loop_t, slot * 6.0)
	var k := int(t / slot) # 0..4 the levers, 5 the knob
	var within := t - k * slot
	var acting := within >= LOOP_FLICKER
	var seen: Array = UndergroundLogic.PORT_LEVERS.get(_loop_port, [])
	var order := logic.startup()
	_set_globes(mini(5, k + (1 if acting else 0)))
	var progress := clampf((within - LOOP_FLICKER - 0.6) / 0.6, 0.0, 1.0)
	for n in range(1, 6):
		var lever := part("control_desk", "IA_lever_%d" % n)
		if lever == null:
			continue
		var deg := 0.0
		if seen.has(n):
			var at := order.find(n)
			if at < k:
				deg = LEVER_PULL_DEG
			elif at == k and acting:
				deg = LEVER_PULL_DEG * progress
		_rot(lever, Vector3.RIGHT, deg, false, 0.0)
	var kd := 0.0
	if _loop_port == UndergroundLogic.KNOB_PORT and k == 5 and acting:
		kd = KNOB_STEP_DEG * UndergroundLogic.KNOB_TARGET * progress
	_rot(part("control_desk", "IA_master_knob"), Vector3.BACK, kd, false, 0.0)
	# the operator: only at the steps this port witnessed
	var op: Node3D = _echoes.get("operator")
	if op == null:
		return
	var lever_n := int(order[k]) if k < 5 else 0
	var show := (k < 5 and seen.has(lever_n)) or (k == 5 and _loop_port == UndergroundLogic.KNOB_PORT)
	if not show:
		if bool(op.get_meta("present", false)):
			room.call("set_present", op, false)
		return
	var mount := part("control_desk", "op_mount_%d" % lever_n if k < 5 else "op_mount_knob")
	if mount:
		op.global_transform = mount.global_transform
	elif model("control_desk"):
		var desk := model("control_desk").global_transform
		var x := (lever_n - 3) * 0.36 - 0.15 if k < 5 else 0.92
		op.global_transform = desk * Transform3D(Basis(Vector3.UP, PI), Vector3(x, 0, 0.62 if k < 5 else 0.47))
	var pose := "pose_knob" if k == 5 else ("pose_pull" if acting and progress > 0.5 else "pose_reach")
	if str(op.get_meta("pose", "")) != pose:
		_show_pose(op, pose)
	if not bool(op.get_meta("present", false)):
		room.call("set_present", op, true)
	var flicker := 0.85 if acting else (0.25 + 0.6 * randf())
	_echo_intensity(op, flicker)
	var lens := part("port_" + _loop_port.to_lower(), "IA_port_lens") as MeshInstance3D
	if lens:
		ModelUtil.set_emission(lens, true, LUMEN, 0.6 + 0.6 * absf(sin(_loop_t * 2.0)))


func _rise(delta: float) -> void:
	_rise_t += delta
	var mm := _rising.multimesh
	var bottom := Vector3(0, -30, 0)
	var top := Vector3(0, 2.6, 0)
	var c := part("array_below", "array_center")
	if c:
		bottom = c.global_position
	var rt := part("array_below", "rise_top")
	if rt:
		top = rt.global_position
	for i in 41:
		var f := fmod(_rise_t * 0.09 + i / 41.0, 1.0)
		var ang := i * 2.39996 + _rise_t * 0.4
		var r := lerpf(4.5, 0.9, f)
		var p := bottom.lerp(top, f) + Vector3(cos(ang) * r, 0, sin(ang) * r)
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * lerpf(1.6, 0.7, f)), p))


# ====================================================================== momentary motions and effects
func pull(model_id: String, part_name: String, deg: float, axis: Vector3 = Vector3.RIGHT, hold: float = 0.35) -> void:
	var p := part(model_id, part_name)
	if p == null:
		return
	_rot(p, axis, deg, true, 0.15)
	get_tree().create_timer(hold).timeout.connect(func() -> void: _rot(p, axis, 0.0, true, 0.3))


func press(model_id: String, part_name: String, depth: float) -> void:
	var p := part(model_id, part_name)
	if p == null:
		return
	_slide(p, Vector3(0, 0, depth), true, 0.06)
	get_tree().create_timer(0.16).timeout.connect(func() -> void: _slide(p, Vector3.ZERO, true, 0.12))


func strike() -> void:
	pull("choir_rack", "IA_hammer", HAMMER_DEG)
	pull("choir_rack", "striker", STRIKER_DEG, Vector3.RIGHT, 0.18)


func port_ring(port: String) -> void:
	var ring := part("port_" + port, "IA_port_ring")
	if ring:
		var cur := int(ring.get_meta("turns", 0)) + 1
		ring.set_meta("turns", cur)
		_rot(ring, Vector3.BACK, PORT_RING_DEG * cur, true, 0.3)


func breaker_trip() -> void:
	pull("control_desk", "breaker_flag", BREAKER_DEG, Vector3.RIGHT, 1.2)
	var origin := part("control_desk", "spark_origin")
	sparks(origin.global_position if origin else Vector3(-9.07, 1.4, 0.45))


## A short burst of sparks (CPU particles: off with safe graphics, never casting shadows).
func sparks(at: Vector3) -> void:
	if CrashGuard.safe_level() >= 2:
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 40
	p.lifetime = 0.7
	p.explosiveness = 0.9
	p.direction = Vector3(0, 1, 0)
	p.spread = 70.0
	p.initial_velocity_min = 1.2
	p.initial_velocity_max = 2.6
	p.gravity = Vector3(0, -6.0, 0)
	p.scale_amount_min = 0.5
	var q := QuadMesh.new()
	q.size = Vector2(0.012, 0.012)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.albedo_color = Color(1.0, 0.85, 0.5)
	q.material = m
	p.mesh = q
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	room.add_child(p)
	p.global_position = at
	p.emitting = true
	get_tree().create_timer(1.5).timeout.connect(p.queue_free)


## A crystal of the shutter rings: it swings a little and its waveform shows on the oscillograph.
func crystal_ring(size: int, swing: bool = true) -> void:
	var c := part("crystal_shutter", "IA_tcrystal_%d" % size)
	if c and swing:
		pull_node(c, Vector3.BACK, 7.0, 0.25)
	_osc_size = size
	_osc_amp = 1.0
	var osc: ShaderMaterial = _mats.get("osc")
	if osc:
		osc.set_shader_parameter("cycles", 2.0 + 2.0 * (5 - size))


func damp_crystals() -> void:
	_osc_amp = 0.0
	var osc: ShaderMaterial = _mats.get("osc")
	if osc:
		osc.set_shader_parameter("amp", 0.0)


func pull_node(n: Node3D, axis: Vector3, deg: float, hold: float) -> void:
	_rot(n, axis, deg, true, 0.12)
	get_tree().create_timer(hold).timeout.connect(func() -> void: _rot(n, axis, 0.0, true, 0.4))


func recorder(playing: bool) -> void:
	_recorder_playing = playing
	_rot(part("field_recorder", "IA_rec_play"), Vector3.RIGHT, REC_KEY_DEG if playing else 0.0, true, 0.1)
	if not playing:
		var vu := part("field_recorder", "rec_vu")
		if vu and rest.has(vu):
			_to(vu, rest[vu], true, 0.3)


## The meter's needle (in hand) swings to the reading and settles.
func meter_reading(r: int) -> void:
	if _meter_node == null:
		return
	var needle := ModelUtil.find(_meter_node, "needle")
	if needle == null:
		return
	if not rest.has(needle):
		rest[needle] = needle.transform
	var base: Transform3D = rest[needle]
	var tw := room.create_tween()
	for k in 4:
		var over := (r + (0.6 if k % 2 == 0 else -0.4) / (k + 1)) if k < 3 else float(r)
		tw.tween_property(needle, "transform", Transform3D(base.basis * Basis(Vector3.BACK, deg_to_rad(METER_STEP_DEG * over)), base.origin), 0.18)
	get_tree().create_timer(3.5).timeout.connect(func() -> void:
		if is_instance_valid(needle):
			_to(needle, base, true, 0.6))


## The crystal grows behind the autoclave glass in eight seconds (§6, ch3_g nursery_crystal).
func grow(clear: bool) -> void:
	_growing = true
	var lever := part("autoclave", "IA_start_lever")
	_rot(lever, Vector3.RIGHT, START_LEVER_DEG, true, 0.2)
	apply_state(true)
	var ch: Array = _held.get("chamber", [])
	var body: Node3D = ModelUtil.find(ch[1], "crystal_body") if not ch.is_empty() and is_instance_valid(ch[1]) else null
	if body:
		body.scale = Vector3.ONE * 0.15
		room.create_tween().tween_property(body, "scale", Vector3.ONE, GROW_SECONDS).set_trans(Tween.TRANS_SINE)
	AudioManager.sfx("projector_charge", -6.0, 0.7)
	await get_tree().create_timer(GROW_SECONDS).timeout
	_growing = false
	_rot(lever, Vector3.RIGHT, 0.0, true, 0.5)
	apply_state(true)
	if not clear:
		AudioManager.sfx("projector_fail", -6.0, 0.8)


# ====================================================================== helpers
func _rot(n: Node3D, axis: Vector3, deg: float, animated: bool, dur: float) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	_to(n, Transform3D(base.basis * Basis(axis.normalized(), deg_to_rad(deg)), base.origin), animated, dur)


func _slide(n: Node3D, offset: Vector3, animated: bool, dur: float = 0.5) -> void:
	if n == null:
		return
	if not rest.has(n):
		rest[n] = n.transform
	var base: Transform3D = rest[n]
	_to(n, Transform3D(base.basis, base.origin + base.basis * offset), animated, dur)


func _to(n: Node3D, target: Transform3D, animated: bool, dur: float) -> void:
	var k := str(n.get_instance_id())
	if _tweens.has(k) and (_tweens[k] as Tween).is_valid():
		(_tweens[k] as Tween).kill()
	if not animated or n.transform.is_equal_approx(target):
		n.transform = target
		return
	var from := n.transform
	var fq := from.basis.get_rotation_quaternion()
	var tq := target.basis.get_rotation_quaternion()
	var fs := from.basis.get_scale()
	var ts := target.basis.get_scale()
	var tw := room.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(t: float) -> void:
		if is_instance_valid(n):
			n.transform = Transform3D(Basis(fq.slerp(tq, t)) * Basis.from_scale(fs.lerp(ts, t)), from.origin.lerp(target.origin, t)), 0.0, 1.0, dur)
	_tweens[k] = tw


func _lamp(n: Node3D, on: bool, color: Color, energy: float = 3.0) -> void:
	if n is MeshInstance3D:
		var key := "%s:%s:%s:%.2f" % [n.get_instance_id(), on, color.to_html(), energy]
		if n.get_meta("lamp", "") == key:
			return
		n.set_meta("lamp", key)
		ModelUtil.set_emission(n as MeshInstance3D, on, color, energy)
		# a glowing lamp lining stays out of the reflection probe (Chapter 2's NO_PROBE_LAYER rule)
		(n as MeshInstance3D).layers = UndergroundRoom.NO_PROBE_LAYER if on else 1


## A grown crystal glows softly (its clear body only; the brass foot stays brass).
func _glow(n: Node3D, on: bool) -> void:
	if n == null:
		return
	var body := ModelUtil.find(n, "crystal_body") as MeshInstance3D
	var targets: Array[MeshInstance3D] = ModelUtil.find_meshes(n)
	if body:
		targets = [body]
	for mi in targets:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.81, 0.96, 1.0, 0.6)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.roughness = 0.05
		m.emission_enabled = on
		m.emission = LUMEN
		m.emission_energy_multiplier = 1.6
		mi.material_override = m if on else null
