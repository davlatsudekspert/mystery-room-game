class_name ArrayHallVisuals
extends Node
## Renders ArrayHallLogic state onto the Chapter 4 models (docs/models/ch4.md and the measured pages ch4_a..ch4_h): part
## poses (switches, wheels, rings, hatches, gates, collar digits, the Sun's rods and iris, the box, the lockers), the
## per-game evidence surfaces (§10), the beam folded through the towers, the Core and its forty-one lights, the replay
## crowd, the kept echoes, the roll board and the cinematic moments (the reversal, the rise). Everything visible derives
## from logic.state (plus purely visual flags such as the intro's gate), so a loaded save reproduces the scene.
## A model that is not built yet is simply skipped.

# ---------------------------------------------------------------- part motions (docs/models/ch4.md §3..§8)
const SWITCH_UP_DEG := -40.0
const SWITCH_DOWN_DEG := 40.0
const MAIN_PULL_DEG := 60.0
const CATWALK_GATE_DEG := 95.0
const WHEEL_STEP_DEG := -45.0
const RING_STEP_DEG := -45.0
const HATCH_OPEN_DEG := -105.0
const CAGE_GATE_DEG := -95.0
const GLASS_SINK := -3.6
const COLLAR_STEP_DEG := -36.0
const DRAWER_TRAVEL := 0.55
const DRAWER_HOVER_UP := 0.42
const DRAWER_HOVER_FWD := 0.62
const FEED_STEP_DEG := -27.0
const NEEDLE_STEP_DEG := -11.0
const SUN_LEVER_ON_DEG := 50.0
const ROD_PER_GAP := 0.07
const LEAF_SLIDE := 0.95
const LEAF_Z := 0.012
const LID_OPEN_DEG := -110.0
const KNOB_STEP_DEG := -60.0
const GEAR_STEP_DEG := -60.0
const ORRERY_STEP_DEG := -45.0
const MASTER_UP_DEG := -80.0
const KEEPER_BASE_DEG := 135.0
const KEEPER_STEP_DEG := -22.5
const SCRUB_STEP_DEG := -45.0
const HAND_BASE_DEG := 140.0
const HAND_STEP_DEG := -40.0
const PLATE_CLOSE_DEG := 100.0
const LOCKER_OPEN_DEG := -105.0
const DIAL_STEP_DEG := -60.0
const NUMBER_STEP_DEG := -40.0
const SEND_PULL_DEG := 50.0
const CANISTER_KNOCK := 0.35
const GATE_FOLD := 0.15
const OSCULUS_SLIDE := 1.7
## The slope normal of the master desk (docs/models/ch4_b.md): the chronometer hand turns about it.
const DESK_NORMAL := Vector3(0.0, 0.7855, 0.6189)
const DECALS := "res://assets/textures/decals/"

const WARM := Color("ffcf94")
const COLD := Color("dcecff")
const LUMEN := Color("bdf2ff")
const AMBER := Color("ffaa3c")
const GREEN := Color("4dff7a")
const RED := Color("ff3b2f")
const WHITE := Color("fff6e6")
const GOLD := Color("ffd98a")
## Panel 0's four line lamps: LOCK amber, LIGHT white, ARRAY cyan, VENT green.
const LINE_COLORS: Array[Color] = [Color("ffaa3c"), Color("fff0d0"), Color("5fd8ff"), Color("5dff8a")]

var room: Node3D
var logic: ArrayHallLogic
var rest: Dictionary = {} # node -> rest Transform3D
## Purely visual state (not in the logic): the intro's gate, the locker's door, the knobs' own turns.
var gate_open := true
var intro_key := false
var locker_open := false
var _tweens: Dictionary = {}
var _held: Dictionary = {} # key -> [item id, Node3D]
var _mats: Dictionary = {}
var _textures: Dictionary = {}
var _wheel_deg: Array[float] = [0.0, 0.0, 0.0, 0.0] # the four handwheels' unwrapped angles (derived from the rings)
var _knob_deg: Array[float] = [0.0, 0.0, 0.0, 0.0] # Strand's box: the four knobs' unwrapped angles (derived from the gears)
var _scrub_deg := 0.0
var _hand_deg := 0.0
var _ring_dur := 0.9
var _view := ""
# the Core's lights and the finale
var _orbs: MultiMeshInstance3D
var _orb_t := 0.0
var _orb_mode := "orbit" # orbit | rise | settled
var _rise_t := 0.0
var _rise_ending := "dawn"
var _forty_second_turn := 0.0 # 0..1: the forty-second light has turned toward the player
var _core_pulse := 0.0
# the beam
var _beams: MultiMeshInstance3D
var _head_yaw: Array[float] = [0.0, 0.0, 0.0, 0.0]
var _beam_on := 0.0
# the replay crowd and the figures
var _crowd: MultiMeshInstance3D
var _named: MeshInstance3D
var _crowd_meshes: Array[Mesh] = []
var _named_meshes: Array[Mesh] = []
var _named_ids: Array = []
var _crowd_pos: Array[Vector2] = []
var _crowd_int := 0.0
var _crowd_m := 7.0
var _crowd_target_m := 7.0
var _echo_mat: ShaderMaterial
var _echoes: Dictionary = {} # figure id -> Node3D
var _ghost: Node3D
var _ghost_minute := -1
var _ghost_real := false
var _placeholder_figures: Array[String] = []
# the roll board
var _tags: MultiMeshInstance3D
var _lamps: MultiMeshInstance3D
var _lamp_lit: Array[float] = []
var _shaft: MeshInstance3D
var _mark: MeshInstance3D
var _mark_beam: MeshInstance3D
var _sun_flare := 0.0
var _frame := 0
var _wave: MeshInstance3D
var _wave_t := -1.0
var _wave_strength := 1.0
var _waking := false
## The room holds the lens and the drawer back for a moment while a cinematic stages them (Leyla's walk, the drawer view).
var defer_lens := false
var defer_drawer := false
var _fin_on := false
var _fin_t := 0.0
var _lamp_anim := false


func _init(r: Node3D) -> void:
	room = r
	logic = r.get("logic")


func _ready() -> void:
	_record_rest()
	_echo_mat = ShaderMaterial.new()
	_echo_mat.shader = load("res://src/fx/echo.gdshader")
	_build_evidence()
	_build_orbs()
	_build_beams()
	_build_crowd()
	_build_echoes()
	_build_board()
	_build_shaft()
	_build_mark()
	_build_wave()
	_init_wheel_angles()


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


func _shader(path: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(path)
	return m


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


func _l(id: String) -> Light3D:
	return (room.get("lights") as Dictionary).get(id) as Light3D


# ====================================================================== construction
## Evidence surfaces (§10): every answer is drawn from this game's state, never baked.
func _build_evidence() -> void:
	# the strip chart: the Night's pen marks, from v_night
	var chart := _shader("res://src/fx/array_chart.gdshader")
	_mats["chart"] = chart
	_set_slot(part("master_desk", "chart_paper") as MeshInstance3D, "M_Shader_Quad", chart)
	# the keeper's oscillograph: the beat envelope
	var osc := _shader("res://src/fx/array_osc.gdshader")
	_mats["osc"] = osc
	_set_slot(part("keeper_knob", "osc_screen") as MeshInstance3D, "M_Shader_Quad", osc)
	# the green band on the ammeter: rotated to the needle value 10 - gap_target
	var band := part("sun_pedestal", "ammeter_band") as Node3D
	if band:
		_rot(band, Vector3.BACK, NEEDLE_STEP_DEG * (10 - logic.gap_target()), false, 0.0)
	# Panel 0's traces: the junction dots where v_panel == 1
	var v: Array = logic.state["v_panel"]
	var lines := ["lock", "light", "array", "vent"]
	for s in ArrayHallLogic.SWITCHES:
		for ln in ArrayHallLogic.LINES:
			var t := part("panel0", "trace_%d_%s" % [s + 1, lines[ln]])
			if t:
				t.visible = int(v[s * ArrayHallLogic.LINES + ln]) == 1
	# the iris: the stacking heights from v_iris (rank 0 = top of the stack)
	var order: Array = logic.iris_order()
	for rank in order.size():
		var leaf := part("sun_iris", "IA_leaf_%d" % (int(order[rank]) + 1))
		if leaf and rest.has(leaf):
			var base: Transform3D = rest[leaf]
			base.origin.z = LEAF_Z * (5 - rank)
			rest[leaf] = base
			leaf.transform = base
	# the little Array: the towers of the orrery at the Night's marks, from v_align
	var al: Array = logic.align_target()
	for n in 4:
		var t := part("orrery", "orrery_tower_%d" % (n + 1))
		if t:
			_rot(t, Vector3.UP, ORRERY_STEP_DEG * int(al[n]), false, 0.0)
	# the tower's numeral plates: each tower shows its own numeral only
	for n in 4:
		for k in 4:
			var num := part("mirror_tower_%d" % (n + 1), "tower_numeral_%d" % (k + 1))
			if num:
				num.visible = k == n
	# the digit wheels, the keeper and the gear pointers start from the state
	# cream light for the pictograms and legends that vanish in the dark steel
	# (the post station's dial and number wheel stay as built)


## The Core's 42 lights (41 + Leyla's): one MultiMesh of soft billboards orbiting the crystal, three inclined bands.
func _build_orbs() -> void:
	_orbs = MultiMeshInstance3D.new()
	_orbs.name = "core_lights"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var q := QuadMesh.new()
	q.size = Vector2(0.20, 0.20)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.billboard_keep_scale = true
	m.vertex_color_use_as_albedo = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.albedo_texture = _radial_texture()
	m.no_depth_test = false
	q.material = m
	mm.mesh = q
	mm.instance_count = 42
	_orbs.multimesh = mm
	_orbs.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_orbs.custom_aabb = AABB(Vector3(-30, -2, -30), Vector3(60, 40, 60))
	room.add_child(_orbs)
	_cull_tag(_orbs, "I")
	for i in 42:
		mm.set_instance_color(i, Color(0.7, 0.95, 1.0, 0.0))
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(0, -50, 0)))


static func _radial_texture() -> GradientTexture2D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.18, 0.55, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.7), Color(1, 1, 1, 0.14), Color(1, 1, 1, 0)])
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	return t


## Five ribbon instances (Sun -> towers -> Core) as one MultiMesh of beam_segment.glb's mesh.
func _build_beams() -> void:
	if not ResourceLoader.exists("res://assets/models/beam_segment.glb"):
		return
	var holder := ModelUtil.spawn("beam_segment", room as Node3D, Transform3D.IDENTITY, "none")
	if holder == null:
		return
	var src := ModelUtil.find(holder, "beam_segment") as MeshInstance3D
	if src == null or src.mesh == null:
		holder.queue_free()
		return
	_beams = MultiMeshInstance3D.new()
	_beams.name = "beam_ribbons"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = src.mesh
	mm.instance_count = 5
	_beams.multimesh = mm
	_beams.material_override = _shader("res://src/fx/array_beam.gdshader")
	_beams.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_beams.custom_aabb = AABB(Vector3(-30, -2, -30), Vector3(60, 20, 60))
	room.add_child(_beams)
	_cull_tag(_beams, "R")
	holder.queue_free()
	for i in 5:
		mm.set_instance_color(i, Color(0, 0, 0, 0))
		mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3(0, -50, 0)))


## The 41 figures of the replay: 33 simple ones (one MultiMesh) and 8 detailed ones near the catwalk (one merged mesh),
## stood on five circles, each in three poses that change with the minute (docs/models/ch4.md §9).
const NAMED_TYPES: Array[String] = ["archivist", "clerk", "operator", "scientist_f", "scientist_m", "technician_f",
	"technician_m", "welder"]


func _build_crowd() -> void:
	var spots: Array[Vector2] = []
	for ring: Array in ArrayHallData.CROWD_RINGS:
		var r: float = ring[0]
		var n: int = ring[1]
		var free: Array[float] = _free_angles(r, n)
		for a in free:
			spots.append(Vector2(r * sin(deg_to_rad(a)), -r * cos(deg_to_rad(a))))
	_crowd_pos = spots
	# the 8 nearest the catwalk (south-centre) are the detailed ones
	var order: Array = range(spots.size())
	order.sort_custom(func(a: int, b: int) -> bool: return spots[a].distance_to(Vector2(0.0, 8.0)) < spots[b].distance_to(Vector2(0.0, 8.0)))
	var named_ids: Array = order.slice(0, 8)
	var crowd_ids: Array = []
	for i in order.size():
		if not named_ids.has(order[i]):
			crowd_ids.append(order[i])
	_crowd_meshes = _crowd_pose_meshes()
	_crowd = MultiMeshInstance3D.new()
	_crowd.name = "replay_crowd"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _crowd_meshes[0]
	mm.instance_count = crowd_ids.size()
	_crowd.multimesh = mm
	_crowd.material_override = _echo_mat
	_crowd.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_crowd.custom_aabb = AABB(Vector3(-16, -1, -16), Vector3(32, 4, 32))
	_crowd.set_meta("ids", crowd_ids)
	_named_ids = named_ids
	_named_meshes = _named_pose_meshes(named_ids)
	_named = MeshInstance3D.new()
	_named.name = "replay_named"
	_named.mesh = _named_meshes[0]
	_named.material_override = _echo_mat
	_named.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for n in [_crowd, _named]:
		room.add_child(n)
		_cull_tag(n, "R")
		n.visible = false
		n.set_meta("present", false)
	_place_crowd(7.0)


## The three poses of the crowd figure: echo_crowd's pose_a/b/c when built, else one simple standing figure.
func _crowd_pose_meshes() -> Array[Mesh]:
	var out: Array[Mesh] = []
	if ResourceLoader.exists("res://assets/models/echo_crowd.glb"):
		var holder := Node3D.new()
		room.add_child(holder)
		var inst := ModelUtil.spawn("echo_crowd", holder, Transform3D.IDENTITY, "none")
		if inst:
			for pn in ["pose_a", "pose_b", "pose_c"]:
				var mi := ModelUtil.find(inst, pn) as MeshInstance3D
				if mi and mi.mesh:
					out.append(mi.mesh)
		holder.queue_free()
	if out.size() < 3:
		out.clear()
		_placeholder_figures.append("echo_crowd")
		var fig := _placeholder_figure()
		out = [fig, fig, fig]
	return out


## The eight detailed figures, merged into one mesh per pose, each standing at its place facing the Core.
func _named_pose_meshes(ids: Array) -> Array[Mesh]:
	var out: Array[Mesh] = []
	var holder: Node3D = null
	var inst: Node3D = null
	if ResourceLoader.exists("res://assets/models/echo_named.glb"):
		holder = Node3D.new()
		room.add_child(holder)
		inst = ModelUtil.spawn("echo_named", holder, Transform3D.IDENTITY, "none")
	for pose in ["a", "b", "c"]:
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var any := false
		for k in ids.size():
			var p := _crowd_pos[int(ids[k])]
			var yaw := atan2(-p.x, -p.y)
			var xf := Transform3D(Basis(Vector3.UP, yaw), Vector3(p.x, 0.0, p.y))
			var src: Mesh = null
			if inst:
				var mi := ModelUtil.find(inst, "%s_%s" % [NAMED_TYPES[k % NAMED_TYPES.size()], pose]) as MeshInstance3D
				if mi:
					src = mi.mesh
			if src == null:
				src = _placeholder_figure()
			else:
				any = true
			st.append_from(src, 0, xf)
		if not any and not _placeholder_figures.has("echo_named"):
			_placeholder_figures.append("echo_named")
		out.append(st.commit())
	if holder:
		holder.queue_free()
	return out


var _placeholder_mesh: Mesh


## A simple standing figure of light (a capsule body, a head and two arms), used until the group-I models are built.
func _placeholder_figure() -> Mesh:
	if _placeholder_mesh:
		return _placeholder_mesh
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var body := CapsuleMesh.new()
	body.radius = 0.2
	body.height = 1.15
	body.radial_segments = 10
	body.rings = 3
	st.append_from(body, 0, Transform3D(Basis.IDENTITY, Vector3(0, 0.78, 0)))
	var head := SphereMesh.new()
	head.radius = 0.115
	head.height = 0.23
	head.radial_segments = 10
	head.rings = 5
	st.append_from(head, 0, Transform3D(Basis.IDENTITY, Vector3(0, 1.52, 0.01)))
	for sx: float in [-1.0, 1.0]:
		var arm := CapsuleMesh.new()
		arm.radius = 0.055
		arm.height = 0.62
		arm.radial_segments = 6
		arm.rings = 2
		st.append_from(arm, 0, Transform3D(Basis(Vector3.BACK, sx * deg_to_rad(10.0)), Vector3(sx * 0.27, 0.98, 0.0)))
	_placeholder_mesh = st.commit()
	return _placeholder_mesh


## The azimuths (degrees clockwise from north) for n figures on a circle, skipping the arcs kept free, spread evenly over
## the rest and staggered by the circle's index.
func _free_angles(radius: float, n: int) -> Array[float]:
	var arcs: Array = ArrayHallData.CROWD_FREE_ARCS
	var cands: Array[float] = []
	var a := 0.0
	while a < 360.0:
		var ok := true
		for arc: Array in arcs:
			var d := absf(fposmod(a - float(arc[0]) + 180.0, 360.0) - 180.0)
			var half: float = float(arc[1]) * (1.0 if radius > 11.0 else 0.8)
			if d < half:
				ok = false
		if ok:
			cands.append(a)
		a += 1.0
	var out: Array[float] = []
	if cands.is_empty():
		return out
	var stagger := fposmod(radius * 7.0, 5.0)
	for k in n:
		var idx := int(fposmod(float(k) * float(cands.size()) / float(n) + stagger, float(cands.size())))
		out.append(cands[idx])
	return out


## Crowd positions at chronometer minute `m` (7 = the frozen 03:17): each figure walks a little along its circle and the
## figures change pose with the minute.
func _place_crowd(m: float) -> void:
	_crowd_m = m
	var back := (7.0 - m) / 7.0
	var face_sun: bool = int(round(m)) == logic.m_sun()
	var pose := posmod(7 - int(round(m)), 3)
	if _crowd.multimesh.mesh != _crowd_meshes[pose]:
		_crowd.multimesh.mesh = _crowd_meshes[pose]
	if _named.mesh != _named_meshes[pose]:
		_named.mesh = _named_meshes[pose]
	var ids: Array = _crowd.get_meta("ids")
	var mm := _crowd.multimesh
	for k in ids.size():
		var i: int = ids[k]
		var p := _crowd_pos[i]
		var tangent := Vector2(-p.y, p.x).normalized()
		var sgn := 1.0 if (i % 2 == 0) else -1.0
		var drift := back * 0.85 * sgn * (0.7 + 0.3 * sin(float(i) * 1.7))
		var q := p + tangent * drift + p.normalized() * (sin(m * 1.3 + float(i)) * 0.05 * back)
		var look := Vector2(-q.x, -q.y)
		if face_sun and i % 3 != 0:
			look = Vector2(-13.0 - q.x, 0.0 - q.y)
		var yaw := atan2(look.x, look.y)
		var scale_y := 0.95 + 0.1 * float((i * 7) % 5) / 4.0
		mm.set_instance_transform(k, Transform3D(Basis(Vector3.UP, yaw) * Basis.from_scale(Vector3(1, scale_y, 1)),
			Vector3(q.x, 0.0, q.y)))


## Echo figures: the four kept echoes at their mounts (stand-ins from earlier chapters until group I is built), Leyla at the
## cradle and Strand's ghost at the master desk.
func _build_echoes() -> void:
	for eid: String in ArrayHallData.ECHOES:
		var e: Array = ArrayHallData.ECHOES[eid]
		var figures: Array = e[1]
		var pick := _pick_model(e[2], "echo_" + eid)
		for fi in figures.size():
			var fid: String = figures[fi]
			var poses := str(pick[1]).split("|")
			var pose_name: String = poses[mini(fi, poses.size() - 1)] if poses.size() > 0 else ""
			var n := _make_echo(fid, str(pick[0]), pose_name, _echo_mount(fid), e[0])
			if n:
				n.set_meta("kept", eid)
				room.call("register_echo_body", room.call("add_tap_area", n, Vector3(0.9, 1.7, 0.9), "", "Echo_" + eid, Vector3(0, 0.85, 0)))
	var lw := _pick_model(ArrayHallData.LEYLA_WALK, "echo_leyla_1998_lens")
	_make_echo("leyla_walk", str(lw[0]), str(lw[1]), Transform3D.IDENTITY, "I")
	var gh := _pick_model(ArrayHallData.STRAND_GHOST, "echo_strand_desk")
	_ghost_real = gh[0] == "echo_strand_desk"
	_ghost = _make_echo("strand_desk", str(gh[0]), str(gh[1]), _echo_mount("strand_desk"), "B")


## The first candidate model that is built; a later one is a stand-in, listed for the QA report under `wanted`.
func _pick_model(cands: Array, wanted: String) -> Array:
	for c: Array in cands:
		if ResourceLoader.exists("res://assets/models/%s.glb" % c[0]):
			if c != cands[0] and not _placeholder_figures.has(wanted):
				_placeholder_figures.append(wanted)
			return c
	if not _placeholder_figures.has(wanted):
		_placeholder_figures.append(wanted)
	return cands[-1]


func _echo_mount(fid: String) -> Transform3D:
	var e: Array = ArrayHallData.ECHO_MOUNTS.get(fid, ["", "", "B", Vector3.ZERO, 0.0])
	var mount: Node3D = part(e[0], e[1])
	if mount and mount.is_inside_tree():
		return mount.global_transform
	return Transform3D(Basis(Vector3.UP, deg_to_rad(float(e[4]))), e[3])


func _make_echo(fid: String, model_name: String, pose: String, xf: Transform3D, groups: String) -> Node3D:
	if not ResourceLoader.exists("res://assets/models/%s.glb" % model_name):
		return null
	var n: Node3D = room.call("spawn", "echo_" + fid, model_name, xf.origin, 0.0, "", "none")
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
	_echoes[fid] = n
	return n


## Show one pose object of an echo GLB (poses are root-level meshes; a single-pose GLB shows its body).
func _show_pose(n: Node3D, pose: String) -> void:
	if n == null:
		return
	var chosen := ""
	for cand in pose.split("|", false):
		for c in n.get_children():
			if c is MeshInstance3D and str(c.name) == cand and chosen == "":
				chosen = cand
	if chosen != "":
		for c in n.get_children():
			if c is MeshInstance3D:
				(c as MeshInstance3D).visible = str(c.name) == chosen
	n.set_meta("pose", pose)


func _set_echo(fid: String, show: bool, intensity: float = 0.85) -> void:
	var n: Node3D = _echoes.get(fid)
	if n == null or bool(n.get_meta("present", false)) == show:
		return
	room.call("set_present", n, show)
	if show:
		_fade(n, 0.0, intensity, 0.8)


func _echo_intensity(n: Node3D, v: float) -> void:
	for mi in ModelUtil.find_meshes(n):
		var m := mi.material_override as ShaderMaterial
		if m:
			m.set_shader_parameter("intensity", v)


func _fade(n: Node3D, from: float, to: float, dur: float) -> void:
	if n == null:
		return
	room.create_tween().tween_method(func(v: float) -> void:
		if is_instance_valid(n):
			_echo_intensity(n, v), from, to, dur)


## The roll board: the 41 tags and the 42 lamps as MultiMeshes of the prototypes (docs/models/ch4_g.md).
func _build_board() -> void:
	var board := model("roll_board")
	if board == null:
		return
	var tag := ModelUtil.find(board, "tag_proto") as MeshInstance3D
	var lamp := ModelUtil.find(board, "lamp_proto") as MeshInstance3D
	if tag and tag.mesh:
		_tags = MultiMeshInstance3D.new()
		_tags.name = "roll_tags"
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = tag.mesh
		mm.instance_count = ArrayHallData.BOARD_SLOTS - 1
		for i in mm.instance_count:
			mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, _slot_offset(i)))
		_tags.multimesh = mm
		_tags.position = tag.position
		var mt := tag.get_surface_override_material(0)
		if mt == null:
			mt = tag.mesh.surface_get_material(0)
		_tags.material_override = mt
		_tags.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		board.add_child(_tags)
		tag.visible = false
	if lamp and lamp.mesh:
		_lamps = MultiMeshInstance3D.new()
		_lamps.name = "roll_lamps"
		var mm2 := MultiMesh.new()
		mm2.transform_format = MultiMesh.TRANSFORM_3D
		mm2.use_colors = true
		mm2.mesh = lamp.mesh
		mm2.instance_count = ArrayHallData.BOARD_SLOTS
		for i in mm2.instance_count:
			mm2.set_instance_transform(i, Transform3D(Basis.IDENTITY, _slot_offset(i)))
			mm2.set_instance_color(i, Color(0, 0, 0, 1))
		_lamps.multimesh = mm2
		_lamps.position = lamp.position
		var sm := _shader("res://src/fx/array_lamp.gdshader")
		_lamps.material_override = sm
		_lamps.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		board.add_child(_lamps)
		lamp.visible = false
		_lamp_lit.clear()
		for i in ArrayHallData.BOARD_SLOTS:
			_lamp_lit.append(0.0)


static func _slot_offset(i: int) -> Vector3:
	return Vector3(ArrayHallData.BOARD_STEP.x * (i % ArrayHallData.BOARD_COLS),
		ArrayHallData.BOARD_STEP.y * (i / ArrayHallData.BOARD_COLS), 0.0)


## The shaft of cold daylight down the oculus: a faint cone from the vent to the island.
func _build_shaft() -> void:
	_shaft = MeshInstance3D.new()
	_shaft.name = "oculus_shaft"
	var c := CylinderMesh.new()
	c.top_radius = 1.45
	c.bottom_radius = 1.9
	c.height = 2.0
	c.radial_segments = 24
	c.rings = 1
	c.cap_top = false
	c.cap_bottom = false
	_shaft.mesh = c
	_shaft.scale = Vector3(1.0, 5.2, 1.0)
	_shaft.position = Vector3(0.0, 6.9, 0.0)
	var m := _shader("res://src/fx/array_shaft.gdshader")
	_shaft.material_override = m
	_mats["shaft"] = m
	_shaft.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	room.add_child(_shaft)
	_cull_tag(_shaft, "HI")


## The Institute's mark on the drawer's face and the cone of light that carries it from the lens (docs/models/ch4_d.md).
func _build_mark() -> void:
	var mount := part("cradle", "mark_mount")
	var pos := mount.global_position if mount else Vector3(0.0, 3.18, 0.705)
	_mark = MeshInstance3D.new()
	_mark.name = "projected_mark"
	var q := QuadMesh.new()
	q.size = Vector2(0.20, 0.20)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.albedo_texture = _tex(DECALS + "ch2/glyph_mark.png")
	m.albedo_color = Color(0.7, 0.95, 1.0, 0.9)
	m.disable_receive_shadows = true
	q.material = m
	_mark.mesh = q
	_mark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	room.add_child(_mark)
	_mark.global_position = pos + Vector3(0.0, 0.0, 0.012)
	_cull_tag(_mark, "I")
	_mark.visible = false
	_mark.set_meta("present", false)
	# the cone from the socket to the drawer face
	_mark_beam = MeshInstance3D.new()
	_mark_beam.name = "lens_cone"
	var cone := CylinderMesh.new()
	cone.top_radius = 0.035
	cone.bottom_radius = 0.10
	cone.height = 0.66
	cone.radial_segments = 12
	cone.rings = 1
	cone.cap_top = false
	cone.cap_bottom = false
	var cm := StandardMaterial3D.new()
	cm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	cm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	cm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	cm.albedo_color = Color(0.55, 0.9, 1.0, 0.16)
	cone.material = cm
	_mark_beam.mesh = cone
	_mark_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	room.add_child(_mark_beam)
	var top := Vector3(0.0, 3.82, 0.60)
	var bot := pos + Vector3(0.0, 0.0, 0.01)
	_mark_beam.global_position = (top + bot) * 0.5
	var dir := (bot - top).normalized()
	_mark_beam.global_basis = Basis(Quaternion(Vector3.UP, dir)) * Basis.from_scale(Vector3(1, (bot - top).length() / 0.66, 1))
	_cull_tag(_mark_beam, "I")
	_mark_beam.visible = false
	_mark_beam.set_meta("present", false)


## A ring of light that runs out across the floor from the Core: every minute the chronometer winds back, and the flash.
func _build_wave() -> void:
	_wave = MeshInstance3D.new()
	_wave.name = "time_wave"
	var q := QuadMesh.new()
	q.size = Vector2(2.0, 2.0)
	q.orientation = PlaneMesh.FACE_Y
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.80, 0.93, 0.975, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0), Color(1, 1, 1, 0.55), Color(1, 1, 1, 1.0), Color(1, 1, 1, 0)])
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 256
	t.height = 256
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = false
	m.albedo_texture = t
	m.albedo_color = Color(0.6, 0.9, 1.0, 1.0)
	q.material = m
	_wave.mesh = q
	_wave.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_wave.position = Vector3(0.0, 0.22, 0.0)
	room.add_child(_wave)
	_cull_tag(_wave, "R")
	_wave.visible = false
	_wave.set_meta("present", false)


## Sends a ring of light out from the Core across the floor (about 1.6 s).
func time_wave(strength: float = 1.0) -> void:
	_wave_t = 0.0
	_wave_strength = strength
	room.call("set_present", _wave, true)


func _init_wheel_angles() -> void:
	var w := _wheel_turns()
	for i in 4:
		_wheel_deg[i] = float(w[i]) * WHEEL_STEP_DEG
	var kn := _knob_presses()
	for i in 4:
		_knob_deg[i] = float(kn[i]) * KNOB_STEP_DEG
	_scrub_deg = SCRUB_STEP_DEG * float(logic.state["wheel"])
	_hand_deg = HAND_BASE_DEG + HAND_STEP_DEG * float(logic.state["wheel"])


## Knob i's presses (mod 6), derived from the gears: gear i = start + knob i + knob i-1 (a knob turns its gear and the next).
func _knob_presses() -> Array[int]:
	var out: Array[int] = [0, 0, 0, 0]
	var start: Array = logic.state["v_box"]
	var box: Array = logic.state["box"]
	var prev := 0
	for i in 4:
		out[i] = posmod(int(box[i]) - int(start[i]) - prev, ArrayHallLogic.GEAR_STEPS)
		prev = out[i]
	return out


## Wheel i's own turn count (mod 8), derived from the rings: ring i = start + wheel i + wheel i-1.
func _wheel_turns() -> Array[int]:
	var out: Array[int] = [0, 0, 0, 0]
	var start: Array = logic.state["v_rings"]
	var rings: Array = logic.state["rings"]
	var prev := 0
	for i in 4:
		out[i] = posmod(int(rings[i]) - int(start[i]) - prev, 8)
		prev = out[i]
	return out


# ====================================================================== items in places
func _held_item(key: String, item_id: String, mount: Node3D, show: bool, part_name: String = "",
		euler_deg: Vector3 = Vector3.ZERO, lift: float = 0.0) -> Node3D:
	var cur: Array = _held.get(key, [])
	var want := item_id if show else ""
	if not cur.is_empty() and (cur[0] != want or not is_instance_valid(cur[1])):
		if is_instance_valid(cur[1]):
			var old := cur[1] as Node3D
			if old.get_parent():
				old.get_parent().remove_child(old) # leave the tree now: a queued node keeps its name
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
		n.rotation_degrees = euler_deg
		n.position = Vector3(0.0, lift, 0.0)
		for mi in ModelUtil.find_meshes(n):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if part_name != "":
			_add_item_collider(n, part_name)
		ItemDress.apply(item_id, n, logic)
		_held[key] = [want, n]
		return n
	return cur[1]


## An item over the open drawer: lifted out of the tray and forward, clear of the digit housing, tilted toward the player.
func _hover(n: Node3D, extra: Vector3, euler_deg: Vector3, on: bool) -> void:
	if n == null or not on:
		return
	n.position = Vector3(extra.x, DRAWER_HOVER_UP, DRAWER_HOVER_FWD)
	n.rotation_degrees = euler_deg


func _add_item_collider(n: Node3D, part_name: String) -> void:
	var aabb := ItemIcons._aabb(n)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	var floor_size := 0.16 if part_name.begins_with("Item_heart_") else 0.06 # the three things over the drawer: a finger-sized box each
	box.size = (aabb.size + Vector3.ONE * 0.03).max(Vector3.ONE * floor_size)
	cs.shape = box
	cs.position = n.global_transform.affine_inverse() * aabb.get_center() if n.is_inside_tree() else aabb.get_center()
	body.add_child(cs)
	body.set_meta("part", part_name)
	n.add_child(body)


# ====================================================================== main entry
func apply_state(animated: bool) -> void:
	_apply_panel(animated)
	_apply_bridge(animated)
	_apply_desk(animated)
	_apply_rings(animated)
	_apply_island(animated)
	_apply_sun(animated)
	_apply_booth(animated)
	_apply_watch(animated)
	_apply_lights(animated)
	_apply_crowd(animated)
	refresh_presence()


## Visibility and tap colliders of things that come and go (items, echoes). Called again after culling.
func refresh_presence() -> void:
	_apply_echoes()
	var s := logic.state
	if _orbs:
		room.call("set_present", _orbs, true)
	if _mark:
		var on: bool = s["lens_seated"] and not defer_lens
		room.call("set_present", _mark, on)
		room.call("set_present", _mark_beam, on)
	_crowd_visibility()
	if _shaft:
		room.call("set_present", _shaft, s["power"])


func _apply_panel(animated: bool) -> void:
	var s := logic.state
	var sw: Array = s["switches"]
	for i in ArrayHallLogic.SWITCHES:
		_rot(part("panel0", "IA_switch_%d" % (i + 1)), Vector3.RIGHT, SWITCH_UP_DEG if sw[i] else SWITCH_DOWN_DEG, animated, 0.2)
	_rot(part("panel0", "IA_main_lever"), Vector3.RIGHT, MAIN_PULL_DEG if s["power"] else 0.0, animated, 0.5)
	var lines := logic.lines()
	var names := ["lamp_lock", "lamp_light", "lamp_array", "lamp_vent"]
	for k in 4:
		_lamp(part("panel0", names[k]), lines[k] == 1 or s["power"], LINE_COLORS[k], 3.2)


func _apply_bridge(animated: bool) -> void:
	var s := logic.state
	var gate := part("bridge", "catwalk_gate")
	_rot(gate, Vector3.UP, CATWALK_GATE_DEG if s["power"] else 0.0, animated, 1.6)
	# the freight lift's gates: only the arrival gate (east) opens, and only after the descent
	var east := part("freight_lift", "IA_gate_east")
	if east:
		var base: Transform3D = rest.get(east, east.transform)
		_to(east, Transform3D(base.basis * Basis.from_scale(Vector3(1, 1, GATE_FOLD if gate_open else 1.0)), base.origin), animated, 1.2)
	_held_item("lift_key", "strand_key" if s["entry"] == "strand" else "leyla_key",
		part("freight_lift", "gate_key_mount_east"), intro_key)
	_lamp(part("freight_lift", "cage_bulb"), true, WARM, 3.0)
	# oculus shutters: open from the moment the hall has power (VENT)
	var open: bool = s["power"]
	_slide(part("shell_hall", "oculus_shutter_a"), Vector3(-OSCULUS_SLIDE if open else 0.0, 0, 0), animated, 4.0)
	_slide(part("shell_hall", "oculus_shutter_b"), Vector3(OSCULUS_SLIDE if open else 0.0, 0, 0), animated, 4.0)
	# the wheel plates: each handwheel shows its own turn count
	var w := _wheel_turns()
	for i in 4:
		var cur := _wheel_deg[i]
		var base_deg := float(w[i]) * WHEEL_STEP_DEG
		# the nearest equivalent angle (period 360 degrees = 8 stops)
		var k := roundf((cur - base_deg) / 360.0)
		_wheel_deg[i] = base_deg + 360.0 * k
		_rot(part("handwheel_%d" % (i + 1), "IA_handwheel"), Vector3.BACK, _wheel_deg[i], animated, _ring_dur * 0.9)


func _apply_desk(animated: bool) -> void:
	var s := logic.state
	var wheel := int(s["wheel"])
	# the jog wheel and the hand: the nearest equivalent angles, forward through the gap on 03:17 -> 03:10
	var scrub_target := SCRUB_STEP_DEG * float(wheel)
	_scrub_deg = scrub_target + 360.0 * roundf((_scrub_deg - scrub_target) / 360.0)
	_rot(part("master_desk", "IA_scrub"), Vector3.RIGHT, _scrub_deg, animated, 0.25)
	var hand_target := HAND_BASE_DEG + HAND_STEP_DEG * float(wheel)
	_hand_deg = hand_target + 360.0 * roundf((_hand_deg - hand_target) / 360.0)
	var hand := part("master_desk", "chrono_hand")
	if hand and rest.has(hand):
		var base: Transform3D = rest[hand]
		_to(hand, Transform3D(Basis(DESK_NORMAL.normalized(), deg_to_rad(_hand_deg)) * base.basis, base.origin), animated, 0.35)
	# the back plate closes over the fitted pawl
	_rot(part("master_desk", "chrono_plate"), Vector3.RIGHT, PLATE_CLOSE_DEG if s["pawl_fitted"] else 0.0, animated, 0.6)
	_rot(part("master_lever", "IA_master_lever"), Vector3.RIGHT, MASTER_UP_DEG if s["master_up"] else 0.0, animated,
		0.7 if s["master_up"] else 0.25)
	_rot(part("keeper_knob", "IA_keeper"), Vector3.BACK, KEEPER_BASE_DEG + KEEPER_STEP_DEG * int(s["keeper"]), animated, 0.25)
	var chart: ShaderMaterial = _mats.get("chart")
	if chart:
		var n: Array = logic.night()
		chart.set_shader_parameter("sun_min", int(n[0]))
		chart.set_shader_parameter("rings_min", int(n[1]))
		chart.set_shader_parameter("keeper_min", int(n[2]))
		chart.set_shader_parameter("wheel", float(wheel))
	var osc: ShaderMaterial = _mats.get("osc")
	if osc:
		osc.set_shader_parameter("beat", float(absi(int(s["keeper"]) - logic.note_target())))
		osc.set_shader_parameter("probe", 1.0 if int(s["keeper"]) > 0 else 0.0)
		osc.set_shader_parameter("live", 1.0 if s["power"] else 0.0)
	# the pawl lies on its seat until the plate closes over it
	var seat := part("master_desk", "pawl_mount")
	_held_item("pawl_seat", "reverse_pawl", seat, s["pawl_fitted"])


func _apply_rings(animated: bool) -> void:
	var s := logic.state
	var rings: Array = s["rings"]
	for n in 4:
		var ring := part("array_rings", "ring_%d" % (n + 1))
		_rot(ring, Vector3.UP, RING_STEP_DEG * int(rings[n]), animated, _ring_dur)
		var tower_id := "mirror_tower_%d" % (n + 1)
		var key := part(tower_id, "IA_key")
		if key:
			key.visible = s["tower_keys"][n]
			room.call("sync_colliders", key)
		# the hatch lid stands open while the key can be reached (or has been taken): ring at mark 1
		var open: bool = int(rings[n]) == 0 or not s["tower_keys"][n]
		_rot(part("catwalk", "IA_hatch_%d" % (n + 1)), Vector3.RIGHT, HATCH_OPEN_DEG if open and s["power"] else 0.0, animated, 0.8)


func _apply_island(animated: bool) -> void:
	var s := logic.state
	var gates: Array = s["gates"]
	for n in 4:
		_rot(part("cage", "IA_gate_%d" % (n + 1)), Vector3.UP, CAGE_GATE_DEG if s["cage_open"] else 0.0, animated, 1.8)
		# the key stays in its gate's lock
		_held_item("gate_key_%d" % n, ArrayHallLogic.TOWER_KEYS[n], part("cage", "gate_key_mount_%d" % (n + 1)), gates[n],
			"", Vector3(0, 0, 0))
	for d in 4:
		_rot(part("glass_tower", "IA_collar_digit_%d" % (d + 1)), Vector3.RIGHT, COLLAR_STEP_DEG * int(s["collar"][d]), animated, 0.25)
	var glass := part("glass_tower", "tower_glass")
	_slide(glass, Vector3(0, GLASS_SINK if s["tower_open"] else 0.0, 0), animated, 3.2)
	var lens_shown: bool = s["lens_seated"] and not defer_lens
	_lamp(part("cradle", "cradle_ring"), lens_shown, LUMEN, 2.4)
	# the lens in its socket (Euler of the contract's lens_mount)
	_held_item("lens", "crystal_lens", part("cradle", "lens_mount"), lens_shown, "Item_lens")
	# the heart drawer
	var hopen: bool = s["heart_open"] and not defer_drawer
	_slide(part("heart_drawer", "IA_heart_drawer"), Vector3(0, 0, DRAWER_TRAVEL if hopen else 0.0), animated, 1.1)
	var taken: Dictionary = s["taken"]
	# the pads lie under the digit housing (no camera could see them): when the drawer is open the three things rise from
	# the velvet and hover in front of it, tilted to the player
	var hovering := hopen
	var watch := _held_item("heart_watch", "pocket_watch", part("heart_drawer", "watch_mount"), hopen and not taken.get("heart_watch", false),
		"Item_heart_watch", Vector3(-90, 0, 0), 0.0077)
	_hover(watch, Vector3(-0.07, 0.0, 0.0), Vector3(-35, 0, 0), hovering)
	var letter := _held_item("heart_letter", "strand_last_letter", part("heart_drawer", "letter_mount"), hopen and not taken.get("heart_letter", false),
		"Item_heart_letter", Vector3.ZERO, 0.005)
	_hover(letter, Vector3(0.0, 0.0, 0.0), Vector3(55, 0, 0), hovering)
	var pawl := _held_item("heart_pawl", "reverse_pawl", part("heart_drawer", "pawl_item_mount"), hopen and not taken.get("heart_pawl", false),
		"Item_heart_pawl", Vector3.ZERO, 0.006)
	_hover(pawl, Vector3(0.07, 0.0, 0.0), Vector3(55, 0, 0), hovering)
	_light_to("drawer_glow", 1.0 if hopen else 0.0, 1.4 if animated else 0.0)
	# the Core itself
	var light := part("core_crystal", "core_light") as MeshInstance3D
	if light:
		var e := 1.2
		if s["power"]:
			e = 2.0
		if logic.replay_live():
			e = 3.0
		if s["note_done"] and logic.keeper_on():
			e = 3.6
		if s["night_undone"]:
			e = 0.6
		ModelUtil.set_emission(light, true, LUMEN, e)


func _apply_sun(animated: bool) -> void:
	var s := logic.state
	var gap := int(s["gap"])
	_slide(part("sun_lamp", "rod_b"), Vector3(ROD_PER_GAP * gap, 0, 0), animated, 0.3)
	var arc := int(s["arc"])
	var glow := part("sun_lamp", "arc_glow") as MeshInstance3D
	if glow:
		_slide(glow, Vector3(0.035 * gap, 0, 0), animated, 0.3)
		var e := 0.0
		var c := WHITE
		match arc:
			ArrayHallLogic.ARC_SHORTED:
				e = 1.4
				c = Color("ff9a52")
			ArrayHallLogic.ARC_LIT:
				e = 3.2 if logic.sun_steady() else 2.4
				c = Color("f4f9ff")
		ModelUtil.set_emission(glow, e > 0.0, c, maxf(e, 0.1))
		glow.visible = e > 0.0
	# the pedestal
	_rot(part("sun_pedestal", "IA_feed"), Vector3.BACK, FEED_STEP_DEG * (ArrayHallLogic.GAP_START - gap), animated, 0.3)
	_rot(part("sun_pedestal", "ammeter_needle"), Vector3.BACK, NEEDLE_STEP_DEG * logic.needle(), animated, 0.4 if arc != 1 else 0.08)
	_rot(part("sun_pedestal", "IA_sun_lever"), Vector3.RIGHT, SUN_LEVER_ON_DEG if s["sun_lever"] else 0.0, animated, 0.3)
	# the iris: a lifted leaf slides out along its rail and latches
	var up: Array = s["iris_up"]
	for k in 6:
		var leaf := part("sun_iris", "IA_leaf_%d" % (k + 1))
		if leaf and rest.has(leaf):
			var base: Transform3D = rest[leaf]
			var a := deg_to_rad(60.0 * k)
			var off := Vector3(sin(a), cos(a), 0.0) * LEAF_SLIDE if up[k] else Vector3.ZERO
			_to(leaf, Transform3D(base.basis, base.origin + off), animated, 0.7)


func _apply_booth(animated: bool) -> void:
	var s := logic.state
	var open: bool = s["power"] or s["booth_gate"]
	var gate := part("booth", "IA_booth_gate")
	if gate and rest.has(gate):
		var base: Transform3D = rest[gate]
		_to(gate, Transform3D(base.basis * Basis.from_scale(Vector3(1, 1, GATE_FOLD if open else 1.0)), base.origin), animated, 1.2)
	_held_item("booth_key", "strand_key", part("booth", "booth_key_mount"), s["booth_gate"] and not s["power"])
	# Strand's box: the gears hold the pointers, the lid rises when the box is solved
	var box: Array = s["box"]
	var kn := _knob_presses()
	for k in 4:
		_rot(part("strand_box4", "gear_pointer_%d" % (k + 1)), Vector3.UP, GEAR_STEP_DEG * int(box[k]), animated, 0.3)
		var kt := float(kn[k]) * KNOB_STEP_DEG
		_knob_deg[k] = kt + 360.0 * roundf((_knob_deg[k] - kt) / 360.0)
		_rot(part("strand_box4", "IA_knob_%d" % (k + 1)), Vector3.BACK, _knob_deg[k], animated, 0.2)
	_rot(part("strand_box4", "IA_box_lid"), Vector3.RIGHT, LID_OPEN_DEG if s["box_open"] else 0.0, animated, 1.2)
	var orrery := part("orrery", "orrery") as Node3D
	var taken: Dictionary = s["taken"]
	_held_item("box_log", "strand_log", part("strand_box4", "log_mount"), s["box_open"] and not taken.get("box_log", false),
		"Item_box_log", Vector3.ZERO, 0.014)
	if orrery:
		orrery.visible = true


func _apply_watch(animated: bool) -> void:
	var s := logic.state
	var open: bool = s["power"] or s["watch_gate"]
	var gate := part("watch_room", "IA_watch_gate")
	if gate and rest.has(gate):
		var base: Transform3D = rest[gate]
		_to(gate, Transform3D(base.basis * Basis.from_scale(Vector3(GATE_FOLD if open else 1.0, 1, 1)), base.origin), animated, 1.2)
	_held_item("watch_key", "leyla_key", part("watch_room", "watch_key_mount"), s["watch_gate"] and not s["power"])
	var taken: Dictionary = s["taken"]
	var note_gone: bool = taken.get("locker_note", false)
	var parcel_gone: bool = taken.get("locker_parcel", false) or not s["secret"]
	var door_open: bool = locker_open or note_gone or taken.get("locker_parcel", false)
	_rot(part("lockers4", "IA_locker_17"), Vector3.UP, LOCKER_OPEN_DEG if door_open else 0.0, animated, 0.8)
	_held_item("locker_note", "leyla_note_1998", part("lockers4", "note_mount"), door_open and not note_gone, "Item_locker_note", Vector3.ZERO, 0.003)
	_held_item("locker_parcel", "leyla_parcel", part("lockers4", "parcel_mount"), door_open and not parcel_gone and s["secret"],
		"Item_locker_parcel", Vector3.ZERO, 0.04)
	# the post station
	_rot(part("post_station4", "IA_post_dial"), Vector3.BACK, DIAL_STEP_DEG * int(s["post_dial"]), animated, 0.3)
	_rot(part("post_station4", "IA_post_number"), Vector3.BACK, NUMBER_STEP_DEG * (int(s["post_number"]) - 1), animated, 0.3)
	var canister := part("post_station4", "IA_post_canister") as MeshInstance3D
	if canister:
		var loaded: bool = s["canister"] != ""
		ModelUtil.set_emission(canister, loaded, Color("9fe6ff"), 0.55)
	# the board: forty-one lamps, lit when the hall has power (the forty-second is Leyla's)
	_apply_board(animated)


## The roll board's lamps: 41 lit with the hall's power; the forty-second burns only when Leyla was trusted (the
## forty-second light of the Core). The finale puts them out one by one (rise_lamps).
func _apply_board(_animated: bool) -> void:
	if _lamps == null or _lamp_anim:
		return
	var s := logic.state
	var on: bool = s["power"]
	for i in ArrayHallData.BOARD_SLOTS:
		var lit := 0.0
		if on:
			lit = 1.0
			if i == 41 and s["trust_strand"]:
				lit = 0.0
		if s["night_undone"]:
			lit = 0.0
			if i == 41 and _rise_ending != "true":
				lit = 1.0
			if _rise_ending == "keeper" and i == 40:
				lit = 1.0
		_lamp_lit[i] = lit
	_write_lamps()


func _write_lamps() -> void:
	if _lamps == null:
		return
	var mm := _lamps.multimesh
	for i in ArrayHallData.BOARD_SLOTS:
		var base := GOLD if i == 41 else Color("ffe7b0")
		mm.set_instance_color(i, Color(base.r, base.g, base.b, _lamp_lit[i]))


func _apply_echoes() -> void:
	var s := logic.state
	var released: Array = s["echoes"]
	for eid: String in ArrayHallData.ECHOES:
		var e: Array = ArrayHallData.ECHOES[eid]
		var seen := not released.has(eid) and logic.echo_visible(eid) and not bool(s["night_undone"])
		for fid: String in e[1]:
			_set_echo(fid, seen)
	# Strand's ghost: at the desk (and where the Night took him) while the hall replays
	_place_ghost()


func release_echo(eid: String) -> void:
	var e: Array = ArrayHallData.ECHOES.get(eid, [])
	if e.is_empty():
		return
	for fid: String in e[1]:
		var n: Node3D = _echoes.get(fid)
		if n == null:
			continue
		room.call("set_present", n, true)
		_fade(n, 0.85, 0.0, 1.4)
		var node := n
		get_tree().create_timer(1.45).timeout.connect(func() -> void:
			if is_instance_valid(node):
				room.call("set_present", node, false)
			refresh_presence())


# ====================================================================== strand's ghost, the crowd, the lights
func _crowd_visibility() -> void:
	if _crowd == null:
		return
	var want: bool = _crowd_int > 0.01
	if bool(_crowd.get_meta("present", false)) != want:
		room.call("set_present", _crowd, want)
		room.call("set_present", _named, want)


## Strand's figure, at the minute the replay shows: reaching for the lever (03:17), the keeper (the Night's minutes), the
## handwheels or the Sun lever. His right hand (`grip_right`) meets the thing he reaches for.
func _place_ghost() -> void:
	if _ghost == null:
		return
	var s := logic.state
	var show: bool = (logic.replay_live() or s["reversing"]) and not s["night_undone"]
	var minute := int(s["wheel"])
	if show and minute != _ghost_minute:
		_ghost_minute = minute
		var group := "B"
		var pose := "pose_pull"
		var target := Vector3(1.28, 3.64, 13.49) # the master lever's grip
		var yaw := PI
		if minute == ArrayHallLogic.FLASH_MINUTE:
			pass
		elif minute == logic.m_keeper():
			pose = "pose_knob"
			target = Vector3(-1.12, 3.58, 13.41)
		elif minute == logic.m_rings():
			pose = "pose_reach"
			target = Vector3(-2.2, 3.8, 12.65)
		elif minute == logic.m_sun():
			pose = "pose_reach"
			group = "S"
			target = Vector3(-11.88, 0.99, 2.19)
			yaw = -PI * 0.5
		else:
			pose = "pose_idle"
		var grip := Vector3(-0.16, 1.14, 0.44)
		var gp := part("echo_strand_desk", "grip_right")
		if gp and _ghost_real:
			grip = gp.position
		var basis := Basis(Vector3.UP, yaw)
		var pos := target - basis * grip
		pos.y = 2.5 if group == "B" else 0.0
		_ghost.global_transform = Transform3D(basis, pos)
		_ghost.set_meta("cull", group)
		_show_pose(_ghost, pose)
	room.call("set_present", _ghost, show)
	if show:
		_echo_intensity(_ghost, 0.7 if logic.replay_live() else 0.4)


func _apply_crowd(animated: bool) -> void:
	var s := logic.state
	var target := 0.0
	if s["night_undone"]:
		target = 0.0
	elif s["reversing"] or logic.replay_live():
		target = 0.8
	elif logic.beam_out() and logic.home():
		target = 0.18 # the weak replay: the figures flicker and fade
	var m := float(s["wheel"])
	if animated:
		var from := _crowd_int
		room.create_tween().tween_method(func(v: float) -> void:
			_crowd_int = v
			_echo_mat.set_shader_parameter("intensity", v)
			_crowd_visibility(), from, target, 1.6 if target > from else 1.0)
		if absf(m - _crowd_target_m) > 0.01:
			var cm := _crowd_m
			room.create_tween().tween_method(func(v: float) -> void: _place_crowd(v), cm, m, 0.9)
	else:
		_crowd_int = target
		_echo_mat.set_shader_parameter("intensity", target)
		_place_crowd(m)
	_crowd_target_m = m


## The Core's key light and the hall lamps, from the state.
func _apply_lights(animated: bool) -> void:
	var s := logic.state
	var dur := 1.4 if animated else 0.0
	var core := 1.6
	if s["power"]:
		core = 2.0
	if logic.replay_live():
		core = 2.6
	if s["note_done"] and logic.keeper_on():
		core = 3.0
	if s["reversing"]:
		core = 3.2
	if s["night_undone"]:
		core = 0.35
	_light_to("core_glow", core, dur)
	# the work lamps dim minute by minute while time runs back, and go out when the Night is undone
	var f := 1.0
	if s["reversing"]:
		var span := float(maxi(1, ArrayHallLogic.FLASH_MINUTE - logic.first_minute()))
		f = 0.3 + 0.7 * clampf(float(int(s["wheel"]) - logic.first_minute()) / span, 0.0, 1.0)
	elif s["night_undone"]:
		f = 0.0
	if not _waking:
		for n in 4:
			_light_to("work_%d" % (n + 1), f if s["power"] else 0.0, dur)
	_light_to("shaft", (3.8 if s["night_undone"] else 2.6) if s["power"] else 0.0, dur * 2.0)
	_light_to("bridge_lamp", 1.7 if s["power"] else 0.7, dur)
	# the zone lamps of the apse, the booth and the watch room: dim until they have current (power, or the right key)
	_light_to("apse_lamp", 1.3 if s["power"] else 0.8, dur)
	_light_to("booth_lamp", 1.2 if (s["power"] or s["booth_gate"]) else 0.35, dur)
	_light_to("watch_lamp", 1.2 if (s["power"] or s["watch_gate"]) else 0.35, dur)
	var arc := int(s["arc"])
	var sun := 0.0
	match arc:
		ArrayHallLogic.ARC_SHORTED:
			sun = 0.8
		ArrayHallLogic.ARC_LIT:
			sun = 3.4 if logic.sun_steady() else 2.4
	_light_to("sun_arc", sun, dur * 0.4)
	var shaft: ShaderMaterial = _mats.get("shaft")
	if shaft:
		var v := (0.95 if s["night_undone"] else 0.55) if s["power"] else 0.0
		if animated:
			var cur: Variant = shaft.get_shader_parameter("strength")
			room.create_tween().tween_method(func(x: float) -> void: shaft.set_shader_parameter("strength", x),
				float(cur) if cur != null else 0.0, v, 4.0)
		else:
			shaft.set_shader_parameter("strength", v)


func _light_to(id: String, energy: float, dur: float) -> void:
	var l := _l(id)
	if l == null:
		return
	l.set_meta("base_energy", energy)
	if dur <= 0.0:
		l.light_energy = energy
	else:
		room.create_tween().tween_property(l, "light_energy", energy, dur)


## A lamp: emission on or off in a colour (a mesh with the library's lamp glass).
func _lamp(n: Node3D, on: bool, color: Color, energy: float = 3.0) -> void:
	if n is MeshInstance3D:
		var key := "%s:%s:%s:%.2f" % [n.get_instance_id(), on, color.to_html(), energy]
		if n.get_meta("lamp", "") == key:
			return
		n.set_meta("lamp", key)
		ModelUtil.set_emission(n as MeshInstance3D, on, color, energy)
		(n as MeshInstance3D).layers = ArrayHallRoom.NO_PROBE_LAYER if on else 1


# ====================================================================== per frame
func _process(delta: float) -> void:
	_frame += 1
	if _wave_t >= 0.0:
		_wave_t += delta
		var u := _wave_t / 1.7
		if u >= 1.0:
			_wave_t = -1.0
			room.call("set_present", _wave, false)
		else:
			var r := lerpf(1.5, 25.0, 1.0 - pow(1.0 - u, 2.0))
			_wave.scale = Vector3(r, 1.0, r)
			var mat := (_wave.mesh as QuadMesh).material as StandardMaterial3D
			mat.albedo_color = Color(0.6, 0.9, 1.0, _wave_strength * (1.0 - u) * 0.55)
	_orb_t += delta
	_animate_orbs(delta)
	_update_beams(delta)
	if _crowd_int > 0.01 and logic.beam_out() and not logic.aligned() and not logic.state["reversing"]:
		# the weak replay flickers
		_echo_mat.set_shader_parameter("intensity", _crowd_int * (0.35 + 0.65 * absf(sin(_orb_t * 17.0) * sin(_orb_t * 5.3))))
	# the arc burns unevenly until the needle sits in the green
	var sun := _l("sun_arc")
	if sun and sun.is_visible_in_tree():
		var arc := int(logic.state["arc"])
		var base := float(sun.get_meta("base_energy", 0.0))
		if arc == ArrayHallLogic.ARC_LIT and not logic.sun_steady():
			sun.light_energy = base * (0.55 + 0.45 * absf(sin(_orb_t * 31.0) * sin(_orb_t * 11.0)))
		elif arc == ArrayHallLogic.ARC_LIT:
			sun.light_energy = base * (1.0 + 0.04 * sin(_orb_t * 23.0)) + _sun_flare
		elif arc == ArrayHallLogic.ARC_SHORTED:
			sun.light_energy = base * (0.7 + 0.3 * sin(_orb_t * 60.0))
	# the Core breathes
	var core := _l("core_glow")
	if core and core.is_visible_in_tree():
		var base2 := float(core.get_meta("base_energy", 1.0))
		core.light_energy = base2 * (1.0 + 0.05 * sin(_orb_t * 1.7) + _core_pulse)
	if _core_pulse > 0.0:
		_core_pulse = maxf(0.0, _core_pulse - delta * 1.4)
	if _sun_flare > 0.0:
		_sun_flare = maxf(0.0, _sun_flare - delta * 3.0)


## The Core's lights: three inclined bands of 14 orbiting the crystal; in the finale they leave through the oculus.
func _animate_orbs(delta: float) -> void:
	if _orbs == null:
		return
	var s := logic.state
	var mm := _orbs.multimesh
	var centre := ArrayHallData.CORE_CENTRE
	var cc := part("core_crystal", "core_center")
	if cc:
		centre = cc.global_position
	var awake: bool = s["power"]
	var live := logic.replay_live()
	var rise := _orb_mode != "orbit"
	if rise:
		_rise_t += delta
		if _fin_on:
			_fin_t += delta
	var speed := 0.35 if not awake else (0.55 if not live else 0.9)
	for i in 42:
		var band := i / 14
		var j := i % 14
		var th := _orb_t * (speed + 0.06 * band) + float(j) * TAU / 14.0 + float(band) * 0.7
		var rad := 0.74 + 0.03 * sin(_orb_t * 1.3 + float(i))
		var local := Vector3(rad * cos(th), 0.0, rad * sin(th))
		local = Basis(Vector3.RIGHT, deg_to_rad(62.0)) * local
		local = Basis(Vector3.UP, deg_to_rad(120.0 * band)) * local
		var pos := centre + local
		var col := Color(0.62, 0.92, 1.0, 0.0)
		var sz := 1.0
		if i == 41:
			col = Color(1.0, 0.86, 0.5, 0.0)
			pos = centre + Vector3(0.3, 0.1, 0.55) + Vector3(0.05 * sin(_orb_t * 0.8), 0.08 * sin(_orb_t * 1.1), 0)
			sz = 1.25
		var brightness := 0.0
		if awake:
			brightness = 0.55 if not live else 0.85
			if s["note_done"] and logic.keeper_on():
				brightness = 1.0
		else:
			brightness = 0.4 # asleep: slow lights, dim
		if i == 41:
			# Leyla's light turns toward the player once (the Leyla path); the Strand path keeps it quiet
			var turn := _forty_second_turn
			pos = pos.lerp(centre + Vector3(0.0, 0.18, 1.02), turn)
			brightness = lerpf(brightness, 1.0, turn)
			sz = lerpf(sz, 1.6, turn)
		if rise:
			var rr := _rise_orb(i, pos, centre)
			pos = rr[0]
			brightness = float(rr[1])
			sz = float(rr[2])
		col.a = brightness
		mm.set_instance_color(i, col)
		mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ONE * sz), pos))


## One light's place during the rise: the forty-one leave one after another through the oculus. Returns
## [position, brightness, size]. `ending`: dawn (the forty-second stays, turns toward the player and looks up), keeper (one
## of the forty settles back into the Core), true (the forty-second rises last, pauses at the rim and looks back).
func _rise_orb(i: int, orbit_pos: Vector3, centre: Vector3) -> Array:
	var gap := 0.17
	var travel := 6.2
	if i == 41:
		var hover := centre + Vector3(0.3, 0.1, 0.55)
		if _rise_ending == "true":
			var ut := clampf(_fin_t / 9.0, 0.0, 1.0)
			if ut <= 0.0:
				return [hover, 0.95, 1.3]
			var up := smoothstep(0.0, 0.62, ut)
			var leave := smoothstep(0.8, 1.0, ut)
			var rad := lerpf(0.5, 0.18, up)
			var ang := ut * 6.0
			var q := Vector3(cos(ang) * rad, lerpf(hover.y, 12.0, up) + 3.0 * leave, sin(ang) * rad)
			return [q, 1.0 * (1.0 - smoothstep(0.93, 1.0, ut)), lerpf(1.4, 2.0, up)]
		var t := clampf(_fin_t / 5.0, 0.0, 1.0)
		var turn := smoothstep(0.25, 0.75, t)
		var p2 := hover.lerp(centre + Vector3(0.0, 0.15, 1.02), turn)
		p2.y += 0.5 * smoothstep(0.82, 1.0, t)
		return [p2, 0.9 + 0.1 * sin(_orb_t * 3.0), 1.5 + 0.3 * turn]
	var start := float(i) * gap + 0.5
	var u := clampf((_rise_t - start) / travel, 0.0, 1.0)
	if _rise_ending == "keeper" and i == 40:
		# settles back into the Core and hums
		var out := sin(clampf(u * 1.5, 0.0, 1.0) * PI) * 0.6
		var back := centre + Vector3(0, 0.6 * out, 0) + (orbit_pos - centre) * (1.0 - smoothstep(0.55, 1.0, u))
		return [back, 1.0, 1.35]
	if u <= 0.0:
		return [orbit_pos, 0.7, 1.0]
	var e := u * u * (3.0 - 2.0 * u)
	var a := float(i) * 2.39996 + _rise_t * 0.9
	var r := lerpf(0.75, 1.15, e) * (1.0 - 0.8 * smoothstep(0.6, 1.0, u))
	var y := lerpf(orbit_pos.y, 14.8, e)
	var p := Vector3(cos(a) * r, y, sin(a) * r)
	var fade := 1.0 - smoothstep(0.86, 1.0, u)
	return [p, 0.9 * fade, lerpf(1.0, 1.4, e) * (1.0 - 0.5 * smoothstep(0.9, 1.0, u))]


## Starts the rise of the lights (the Night undone): `ending` is dawn, keeper or true.
func begin_wake() -> void:
	_waking = true
	for n in 4:
		var l := _l("work_%d" % (n + 1))
		if l:
			l.light_energy = 0.0


## The finale view begins: the forty-second light turns toward the player (dawn, keeper) or rises last (true).
func finale_phase() -> void:
	_fin_on = true
	_fin_t = 0.0


## A loaded game after the Night was undone: the lights are gone, the forty-second stays (or is gone, true).
func settle_rise(ending: String) -> void:
	_rise_ending = ending
	_orb_mode = "rise"
	_rise_t = 100.0
	_fin_on = true
	_fin_t = 100.0


## After the choice: the lens taken leaves the Core dark; left in the cradle it keeps a soft glow.
func choose_fx(option: String) -> void:
	var dark := option == "take_lens"
	room.create_tween().tween_method(func(v: float) -> void:
		var l := _l("core_glow")
		if l:
			l.light_energy = v, 0.35, 0.05 if dark else 0.55, 3.0)


func start_rise(ending: String) -> void:
	_rise_ending = ending
	_orb_mode = "rise"
	_rise_t = 0.0


func rise_seconds() -> float:
	return 41.0 * 0.17 + 0.5 + 6.2 + (3.4 if _rise_ending == "true" else 0.0)


func rise_progress() -> float:
	return _rise_t


## The roll board's lamps go out one by one as the lights leave (the watch room's view of the finale).
func rise_lamps(per_lamp: float = 0.12) -> void:
	if _lamps == null:
		return
	_lamp_anim = true
	var limit := ArrayHallData.BOARD_SLOTS - 1
	if _rise_ending == "true":
		limit = ArrayHallData.BOARD_SLOTS
	elif _rise_ending == "keeper":
		limit = ArrayHallData.BOARD_SLOTS - 2 # forty go out, Strand's stays and so does the forty-second
	for i in limit:
		if _lamp_lit[i] > 0.0:
			_lamp_lit[i] = 0.0
			_write_lamps()
			AudioManager.sfx("relay_click", -18.0, 1.0 + 0.004 * i)
		await get_tree().create_timer(per_lamp).timeout
	_lamp_anim = false


## The work lamps wake ring by ring (the outer ring first), a few lamps of the hall coming on one after the other.
func wake_work_lamps() -> void:
	_waking = true
	for n in 4:
		var l := _l("work_%d" % (n + 1))
		if l:
			l.light_energy = 0.0
	for n in 4:
		var l := _l("work_%d" % (n + 1))
		if l:
			room.create_tween().tween_property(l, "light_energy", 1.0, 0.7)
		AudioManager.sfx("breaker_on", -14.0, 0.8 + 0.1 * n)
		await get_tree().create_timer(0.95).timeout
	_waking = false


## Leave path: Leyla, 1998, steps out of the Core, walks round the cradle's pedestal carrying the lens you left for her, seats
## it (the seat pose's palm is exactly at the cradle's socket) and fades. The two walk poses alternate while she moves.
const LEYLA_PATH: Array[Vector3] = [Vector3(-0.95, 2.5, -0.30), Vector3(-1.05, 2.5, 0.50), Vector3(-0.10, 2.5, 1.0766)]
const LEYLA_STRIDE_SECONDS := 0.35


func leyla_seats_lens(seconds: float) -> void:
	var n: Node3D = _echoes.get("leyla_walk")
	if n == null:
		await get_tree().create_timer(seconds).timeout
		return
	_carry_lens(n)
	var lens := _held.get("lens_carry", []) as Array
	var lens_nodes: Array = lens[1] if lens.size() > 1 else []
	var seg: Array[float] = []
	var total := 0.0
	for i in range(1, LEYLA_PATH.size()):
		var d := LEYLA_PATH[i].distance_to(LEYLA_PATH[i - 1])
		seg.append(d)
		total += d
	var walk := seconds * 0.62
	n.global_transform = Transform3D(Basis(Vector3.UP, atan2(LEYLA_PATH[1].x - LEYLA_PATH[0].x, LEYLA_PATH[1].z - LEYLA_PATH[0].z)), LEYLA_PATH[0])
	_show_pose(n, "pose_walk")
	room.call("set_present", n, true)
	_fade(n, 0.0, 0.9, 0.9)
	var tw := room.create_tween()
	tw.tween_method(func(t: float) -> void:
		if not is_instance_valid(n):
			return
		var at := t * total
		var i := 0
		while i < seg.size() - 1 and at > seg[i]:
			at -= seg[i]
			i += 1
		var f := clampf(at / maxf(seg[i], 0.001), 0.0, 1.0)
		var pos := LEYLA_PATH[i].lerp(LEYLA_PATH[i + 1], f)
		var dir := LEYLA_PATH[i + 1] - LEYLA_PATH[i]
		var yaw := atan2(dir.x, dir.z)
		if i == seg.size() - 1:
			yaw = lerp_angle(yaw, PI, smoothstep(0.4, 1.0, f)) # the last steps turn her to the cradle
		n.global_transform = Transform3D(Basis(Vector3.UP, yaw), pos)
		_show_pose(n, "pose_walk" if int(t * walk / LEYLA_STRIDE_SECONDS) % 2 == 0 else "pose_walk_b"), 0.0, 1.0, walk)
	await get_tree().create_timer(walk).timeout
	_show_pose(n, "pose_seat")
	n.global_transform = Transform3D(Basis(Vector3.UP, PI), LEYLA_PATH[-1])
	await get_tree().create_timer(seconds * 0.16).timeout
	defer_lens = false
	apply_state(true) # the lens stands in its socket as she takes her hand away
	for ln: Node3D in lens_nodes:
		ln.visible = false
	await get_tree().create_timer(seconds * 0.1).timeout
	_fade(n, 0.9, 0.0, seconds * 0.12)
	await get_tree().create_timer(seconds * 0.12).timeout
	room.call("set_present", n, false)
	for ln: Node3D in lens_nodes:
		ln.visible = true


## The lens on Leyla's palm in each of her three poses (an instance on each pose's empty, which turns up and down with it).
func _carry_lens(figure: Node3D) -> void:
	if _held.has("lens_carry"):
		return
	var nodes: Array = []
	for mount_name: String in ["lens_mount_walk", "lens_mount_walk_b", "lens_mount_seat"]:
		var mount := ModelUtil.find(figure, mount_name)
		if mount == null:
			continue
		var ln := ModelUtil.spawn(ItemDB.model_path("crystal_lens"), mount, Transform3D.IDENTITY, "none")
		if ln == null:
			continue
		for mi in ModelUtil.find_meshes(ln):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		nodes.append(ln)
	_held["lens_carry"] = ["lens_carry", nodes]


func forty_second_turns() -> void:
	room.create_tween().tween_method(func(v: float) -> void: _forty_second_turn = v, 0.0, 1.0, 1.8)
	get_tree().create_timer(4.5).timeout.connect(func() -> void:
		room.create_tween().tween_method(func(v: float) -> void: _forty_second_turn = v, 1.0, 0.0, 2.5))


func core_pulse(strength: float = 0.8) -> void:
	_core_pulse = strength


func sun_flare(strength: float = 4.0) -> void:
	_sun_flare = strength


# ====================================================================== the beam
func _tower_point(n: int) -> Vector3:
	var t := part("mirror_tower_%d" % (n + 1), "tower_head")
	if t:
		return t.global_position
	var p := int((logic.state["rings"] as Array)[n])
	return Basis(Vector3.UP, deg_to_rad(RING_STEP_DEG * p)) * Vector3(0, ArrayHallData.BEAM_Y, ArrayHallData.RING_RADIUS[n])


func _target_point(n: int) -> Vector3:
	var p := int((logic.align_target() as Array)[n])
	return Basis(Vector3.UP, deg_to_rad(RING_STEP_DEG * p)) * Vector3(0, ArrayHallData.BEAM_Y, ArrayHallData.RING_RADIUS[n])


func _update_beams(delta: float) -> void:
	if _beams == null:
		return
	var s := logic.state
	var mm := _beams.multimesh
	var out := logic.beam_out()
	var want := 1.0 if out else 0.0
	_beam_on = move_toward(_beam_on, want, delta * 2.2)
	for i in 5:
		mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3(0, -50, 0)))
	if _beam_on <= 0.005:
		_update_heads(delta, 0)
		return
	var k := logic.folded()
	var iris := ArrayHallData.SUN_IRIS
	var weak := out and not logic.aligned() and logic.home()
	var pts: Array = [] # [from, to, brightness, stub, width, flicker]
	var bright := _beam_on * (1.0 if not weak else 0.35)
	if weak:
		pts.append([iris, Vector3(-2.7, ArrayHallData.BEAM_Y, 0.0), bright * (0.5 + 0.5 * absf(sin(_orb_t * 13.0))), 0.0, 0.5, 0.6])
	elif k == 0:
		pts.append([iris, Vector3(-9.6, ArrayHallData.BEAM_Y, 0.0), bright, 1.0, 0.5, 0.0])
	else:
		var prev := iris
		for n in range(0, k):
			var tp := _tower_point(n)
			pts.append([prev, tp, bright, 0.0, [0.55, 0.38, 0.32, 0.30][n], 0.0])
			prev = tp
		if k < 4:
			var tgt := _target_point(k)
			pts.append([prev, prev.lerp(tgt, 0.42), bright, 1.0, 0.3, 0.0])
		else:
			pts.append([prev, ArrayHallData.CORE_CENTRE, bright, 0.0, 0.42, 0.0])
	for i in mini(pts.size(), 5):
		var seg: Array = pts[i]
		var a: Vector3 = seg[0]
		var b: Vector3 = seg[1]
		var len := a.distance_to(b)
		if len < 0.05:
			continue
		var basis := Basis.looking_at((b - a).normalized(), Vector3.UP if absf((b - a).normalized().y) < 0.95 else Vector3.RIGHT, true)
		var w: float = float(seg[4]) / 0.22
		basis = basis * Basis.from_scale(Vector3(w, w, len))
		mm.set_instance_transform(i, Transform3D(basis, a))
		mm.set_instance_color(i, Color(float(seg[2]), len / 40.0, float(seg[3]), float(seg[5])))
	_update_heads(delta, k)


## The mirror heads of the reached towers turn to the next fold; the others face outward.
func _update_heads(delta: float, k: int) -> void:
	var ring_yaw: Array[float] = [0.0, 0.0, 0.0, 0.0]
	for n in 4:
		ring_yaw[n] = deg_to_rad(RING_STEP_DEG * int((logic.state["rings"] as Array)[n]))
	for n in 4:
		var want := 0.0
		if _beam_on > 0.01 and n < k:
			var prev := ArrayHallData.SUN_IRIS if n == 0 else _tower_point(n - 1)
			var here := _tower_point(n)
			var nxt := ArrayHallData.CORE_CENTRE if n == 3 else (_tower_point(n + 1) if n + 1 < k else _target_point(n + 1))
			var din := (prev - here)
			din.y = 0.0
			var dout := (nxt - here)
			dout.y = 0.0
			var bis := din.normalized() + dout.normalized()
			if bis.length() > 0.001:
				want = atan2(bis.x, bis.z) - ring_yaw[n]
		_head_yaw[n] = lerp_angle(_head_yaw[n], want, clampf(delta * 5.0, 0.0, 1.0))
		var head := part("mirror_tower_%d" % (n + 1), "tower_head")
		if head:
			head.rotation.y = _head_yaw[n]


# ====================================================================== views
func view_changed(id: String) -> void:
	_view = id
	refresh_presence()


func selection_changed(_id: String) -> void:
	refresh_presence()


# ====================================================================== momentary motions
## Briefly turn a part and bring it back.
func pull(model_id: String, part_name: String, deg: float, axis: Vector3 = Vector3.RIGHT, hold: float = 0.35) -> void:
	var p := part(model_id, part_name)
	if p == null:
		return
	_rot(p, axis, deg, true, 0.15)
	get_tree().create_timer(hold).timeout.connect(func() -> void: _rot(p, axis, 0.0, true, 0.3))


## A knob dips when pressed (its turn itself follows the box's state, see _knob_presses); the turn tween that follows the
## logic's answer brings it back.
func knob_turn(i: int) -> void:
	var p := part("strand_box4", "IA_knob_%d" % (i + 1))
	if p == null or not rest.has(p):
		return
	var home: Vector3 = (rest[p] as Transform3D).origin
	p.position = home + p.basis * Vector3(0, 0, -0.012)
	get_tree().create_timer(0.4).timeout.connect(func() -> void:
		if is_instance_valid(p):
			p.position = home)


func lamp_cage_shake() -> void:
	var gate := part("bridge", "catwalk_gate")
	if gate == null or not rest.has(gate):
		return
	var base: Transform3D = rest[gate]
	var tw := room.create_tween()
	for k in 4:
		tw.tween_property(gate, "transform", Transform3D(base.basis * Basis(Vector3.UP, deg_to_rad(3.0 * (1 if k % 2 == 0 else -1))), base.origin), 0.05)
	tw.tween_property(gate, "transform", base, 0.06)


## The canister goes up the tube and (if it comes back) knocks back out.
func canister_send(returns: bool) -> void:
	var c := part("post_station4", "IA_post_canister")
	if c == null:
		return
	_rot(part("post_station4", "IA_post_send"), Vector3.RIGHT, SEND_PULL_DEG, true, 0.12)
	get_tree().create_timer(0.5).timeout.connect(func() -> void: _rot(part("post_station4", "IA_post_send"), Vector3.RIGHT, 0.0, true, 0.4))
	if returns:
		_slide(c, Vector3(0, 0, CANISTER_KNOCK), true, 0.3)
		get_tree().create_timer(1.0).timeout.connect(func() -> void: _slide(c, Vector3.ZERO, true, 0.5))
	else:
		_slide(c, Vector3(0, 0, -0.5), true, 0.4)


func snap_durations(on: bool) -> void:
	_ring_dur = 2.0 if on else 0.9


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
	q.size = Vector2(0.03, 0.03)
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
