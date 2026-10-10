class_name UndergroundRoom
extends RoomBase
## Chapter 3 scene: Level −2 of the Institute — the Choir Hall, the Resonance Gallery, the Nursery with Leyla's camp
## and the freight lift. It assembles the level from the models in docs/models/ch3.md (tables in UndergroundData),
## draws only the zones a view needs (§1.4), routes taps to UndergroundLogic and lets UndergroundVisuals render the
## resulting state. A model that is not built yet is skipped (ModelUtil.spawn warns); its puzzle then has nothing to
## tap, which the QA playthrough reports.

## Render layer for meshes the reflection probes must not capture (glowing lamp glass), as in Chapter 2.
const NO_PROBE_LAYER := 1 << 19
const ALL_GROUPS := "CGSNKL"
const DRAG_PX_PER_STEP := 26.0
const INTRO_SECONDS := 7.6

var visuals: UndergroundVisuals
var tones: UndergroundTones
var missing_models: Array[String] = []
var _cinematic := false
var _cull_nodes: Array[Node3D] = []
var _probes: Array[ReflectionProbe] = []
var _portals: Dictionary = {} # portal empty name -> MeshInstance3D
var _drawn := ALL_GROUPS
var _zone := ""
var _frost: ColorRect
var _dirs: Dictionary = {} # knob / turntable -> tap direction (+1 / -1), turning back at the end stops
var _drag_kind := ""
var _knob_acc := 0.0
var _recording := 0 # playback generation of Leyla's recorder (a rewind restarts it)
## The brass rim of a crystal port framing the port views: in a port view the camera sits at the lens, so the
## port's own ring is behind it; tapping this rim (IA_port_ring) switches between now and the kept memory.
var eyepiece: Node3D


func _ready() -> void:
	if GameState.logic == null or not GameState.logic is UndergroundLogic:
		GameState.start_new("ch3")
	logic = GameState.logic
	GameState.in_game = true
	make_environment(Color("05070a"), Color("2c3434"), 0.42, Color("0f1a1c"), 0.010)
	_build_models()
	_build_lights()
	build_camera()
	cam.far = 48.0 # the Array lies 30 m below the glass floor
	_build_views()
	_build_portals()
	tones = UndergroundTones.new()
	add_child(tones)
	visuals = UndergroundVisuals.new(self)
	add_child(visuals)
	build_input()
	build_hud()
	add_child(PerfGuard.new())
	_build_frost()
	_build_eyepiece()
	GameState.events.connect(_on_events)
	visuals.apply_state(false)
	DecalLoc.apply(self)
	Loc.language_changed.connect(_on_language_changed)
	var fresh := not capture_mode and _fresh_start()
	if fresh:
		visuals.gate_open = false
		visuals.apply_state(false)
	cam.go(_lift_view() if fresh else start_view(), true)
	_music(false)
	if fresh:
		hud.call("play_intro")
	elif not capture_mode and l3().state["array_awake"] and not l3().state["complete"]:
		get_tree().create_timer(1.2).timeout.connect(func() -> void: hud.call("show_choice"))
	SceneManager.room_ready(self) # safe graphics before the first frame is drawn


func _exit_tree() -> void:
	GameState.in_game = false


func l3() -> UndergroundLogic:
	return logic as UndergroundLogic


## Where a continued game starts: the entry wing's hall.
func start_view() -> String:
	return "choir" if l3().state["entry"] == "choir" else "nursery"


func _lift_view() -> String:
	return "lift_w" if l3().state["entry"] == "choir" else "lift_e"


func _fresh_start() -> bool:
	var s := l3().state
	return (s["taken"] as Dictionary).is_empty() and s["desk_hook"] and int(s["seed_from"]) < 0 \
		and int(s["seed_drawer"]) < 0 and int(s["tube_hand"]) == 0 and not s["gallery_awake"] \
		and int(s["prism_p"]) == UndergroundLogic.PRISM_START and int(s["prism_q"]) == UndergroundLogic.PRISM_START \
		and (s["cab_in"] as Array).all(func(k: Variant) -> bool: return str(k) == "")


func _on_language_changed(_code: String) -> void:
	DecalLoc.refresh()
	DecalLoc.apply(self)


# ====================================================================== construction
func _build_models() -> void:
	for id: String in UndergroundData.LAYOUT:
		var e: Array = UndergroundData.LAYOUT[id]
		# a model that is not built yet is skipped quietly (listed once in missing_models, for the QA report)
		var n: Node3D = null
		if ResourceLoader.exists("res://assets/models/%s.glb" % e[0]):
			n = spawn(id, e[0], e[1], e[2], e[3], e[4])
		if n == null:
			if not missing_models.has(e[0]):
				missing_models.append(e[0])
			continue
		if UndergroundData.PITCH.has(id):
			n.basis = n.basis * Basis(Vector3.RIGHT, deg_to_rad(float(UndergroundData.PITCH[id])))
		tag_cull(n, e[5])
		var parts: Dictionary = UndergroundData.PART_HOTSPOT.get(id, {})
		for p: String in parts:
			_part_hotspot(part(id, p), parts[p])
		for mi in ModelUtil.find_meshes(n):
			for prefix: String in UndergroundData.NO_SHADOW_PREFIX:
				if str(mi.name).begins_with(prefix):
					mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# a part drawn with more groups than its model (§1.2 "camp_walls also K"): it leaves the model's subtree,
		# since a hidden parent would hide it, and carries its own tags
		var own: Dictionary = UndergroundData.PART_CULL.get(id, {})
		for p: String in own:
			var pn := part(id, p)
			if pn:
				pn.reparent(self, true)
				tag_cull(pn, own[p])
	# the growth log hangs on the working autoclave (§6): it belongs to the autoclave's hotspot
	var log_mount := part("autoclave", "log_mount")
	if log_mount and ResourceLoader.exists("res://assets/models/growth_log.glb"):
		var gl := ModelUtil.spawn("growth_log", log_mount, Transform3D.IDENTITY, "parts")
		if gl:
			models["growth_log"] = gl
			tune_shadows(gl)
		else:
			missing_models.append("growth_log")
	else:
		missing_models.append("growth_log")
	# the intro shaft only shows during the descent
	var shaft := part("shell_lift", "intro_shaft")
	if shaft:
		shaft.visible = false
	for extra in ["choir_tube", "echo_operator", "echo_welder", "echo_technicians", "echo_strand_rail",
			"echo_leyla_1998", "strand_fork"]:
		if not ResourceLoader.exists("res://assets/models/%s.glb" % extra):
			missing_models.append(extra)


## Give one part (and only its own collider) a hotspot of its own.
func _part_hotspot(p: Node3D, hs: String) -> void:
	if p == null:
		return
	for c in p.get_children():
		if c is StaticBody3D:
			(c as StaticBody3D).set_meta("hotspot", hs)


## Culling (§1.4): `groups` lists the zones a node belongs to; it is drawn while any of them is.
func tag_cull(n: Node3D, groups: String) -> void:
	if n == null:
		return
	n.set_meta("cull", groups)
	_cull_nodes.append(n)


## Presence (items, echoes) and culling both decide a node's visibility; taps follow what is visible.
func set_present(n: Node3D, on: bool) -> void:
	if n == null:
		return
	n.set_meta("present", on)
	n.visible = on and not bool(n.get_meta("culled", false))
	sync_colliders(n)


func sync_colliders(root: Node = self) -> void:
	for body in root.find_children("*", "StaticBody3D", true, false):
		var b := body as StaticBody3D
		b.collision_layer = 1 if b.is_visible_in_tree() else 0


func _light(id: String, kind: String, pos: Vector3, color: Color, energy: float, rng: float, groups: String) -> Light3D:
	var l: Light3D
	if kind == "spot":
		var s := SpotLight3D.new()
		s.spot_range = rng
		l = s
	else:
		var o := OmniLight3D.new()
		o.omni_range = rng
		o.omni_attenuation = 1.3
		l = o
	l.name = id
	l.light_color = color
	l.light_energy = energy
	l.shadow_enabled = false
	l.set_meta("base_energy", energy)
	add_child(l)
	l.global_position = pos
	lights[id] = l
	tag_cull(l, groups)
	return l


func _spot(id: String, from: Vector3, to: Vector3, angle: float, color: Color, energy: float, rng: float,
		groups: String, shadow: bool) -> SpotLight3D:
	var s := _light(id, "spot", from, color, energy, rng, groups) as SpotLight3D
	s.spot_angle = angle * 0.5
	s.spot_angle_attenuation = 0.9
	s.shadow_enabled = shadow
	var up := Vector3.FORWARD if absf((to - from).normalized().y) > 0.95 else Vector3.UP
	s.look_at_from_position(from, to, up)
	return s


func _at(model_id: String, empty: String, fallback: Vector3) -> Vector3:
	var e := part(model_id, empty)
	return e.global_position if e else fallback


## Lights (§1.5): at most one shadowed light per zone, always a spot cone; no omni shadows. Hidden zones' lights
## are off. Dust never casts shadows.
func _build_lights() -> void:
	var warm := Color("ffc993")
	var cool := Color("cfe4ff")
	var cold := Color("e2f0ff")
	var lumen := Color("bdf2ff")
	# Choir Hall
	_spot("key_choir", Vector3(-8.0, 5.6, 2.6), Vector3(-8.6, 0.0, -1.2), 55.0, warm, 2.6, 10.0, "C", true)
	# a wash over the three cabinet fronts and the plate (they read nearly black from the desk otherwise)
	_spot("cabinet_wash", Vector3(-8.3, 3.3, 2.2), Vector3(-8.3, 1.1, 3.9), 80.0, warm, 1.6, 4.5, "C", false)
	# the choir rack and the tube bench are black enamel against a dark wall: their hooks and slots vanished (rendered QA)
	_spot("rack_wash", Vector3(-8.5, 3.1, -1.1), Vector3(-8.5, 1.5, -4.0), 85.0, warm, 1.5, 5.5, "C", false)
	for k in 4:
		var fb: Vector3 = [Vector3(-12.3, 3.4, -3.88), Vector3(-7.4, 3.4, -3.88), Vector3(-11.6, 3.4, 3.88), Vector3(-7.4, 3.4, 3.88)][k]
		_light("work_%d" % k, "omni", _at("shell_choir", "light_choir_%d" % k, fb) + Vector3(0, -0.15, 0), warm, 1.1, 5.0, "C")
	_light("office_lamp", "omni", _at("office_desk", "office_light", Vector3(-12.65, 1.12, 2.45)), Color("ffcc8a"), 0.9, 2.5, "C")
	var arcs := _light("arcs", "omni", Vector3(-12.3, 3.0, -1.3), Color("aac8ff"), 0.0, 4.0, "C")
	arcs.light_specular = 0.6
	# Resonance Gallery
	_spot("key_gallery", Vector3(0.0, 4.4, 2.2), Vector3(0.0, 0.0, -1.4), 60.0, cool, 2.2, 9.0, "G", true)
	_spot("array_up", Vector3(0.0, -29.0, 0.0), Vector3(0.0, 5.0, 0.0), 40.0, lumen, 3.0, 35.0, "G", false)
	_light("sconce_0", "omni", _at("shell_gallery", "light_gallery_0", Vector3(3.072, 2.76, 2.151)), Color("ffe2b8"), 0.8, 4.0, "G")
	_light("sconce_1", "omni", _at("shell_gallery", "light_gallery_3", Vector3(-3.072, 2.76, 2.151)), Color("ffe2b8"), 0.8, 4.0, "G")
	# the key spot's cone ends short of the console (z 2.6) and the memorial arc (z -3.9): one unshadowed lamp over each,
	# or the console's dials and the stone figures read dark on a phone (docs/models/ch3_f.md, integration notes)
	_light("console_lamp", "omni", Vector3(0.0, 2.15, 3.5), Color("ffd9a8"), 1.5, 3.6, "G")
	_light("memorial_lamp", "omni", Vector3(0.0, 2.7, -1.6), Color("ffe0b8"), 2.0, 5.5, "G")
	# a shroud lamp in front of each drum lock: the drums sit 5 cm behind the plate, where no room light reaches
	for side: String in ["west", "east"]:
		var door := models.get("door_" + side) as Node3D
		var at := door.global_transform * Vector3(-1.16, 1.55, 0.58) if door else Vector3(-3.1 if side == "west" else 3.1, 1.55, 1.16 if side == "west" else -1.16)
		_light("drum_light_" + side, "omni", at, Color("ffd9a8"), 1.3, 1.1, "G")
	# Nursery
	_spot("key_nursery", Vector3(9.8, 3.9, 0.2), Vector3(9.8, 0.0, -3.4), 60.0, cold, 2.4, 8.0, "N", true)
	_light("fill_0", "omni", Vector3(6.8, 3.6, 1.2), cold, 0.9, 5.0, "N")
	_light("fill_1", "omni", Vector3(11.5, 3.6, 0.8), cold, 0.9, 5.0, "N")
	_spot("prism_lamp", Vector3(6.1, 1.0, 0.55), Vector3(6.1, 1.15, -1.0), 25.0, Color("fff2d8"), 1.2, 2.5, "N", false)
	# Leyla's camp and the lift
	_light("camp_lamp", "omni", _at("leyla_camp", "camp_light", Vector3(6.2, 2.45, -2.6)), Color("ffc27a"), 1.0, 3.0, "K")
	_light("cage_lamp", "omni", _at("freight_lift", "cage_light", Vector3(0.0, 2.36, 6.0)), Color("ffd29a"), 1.0, 3.0, "L")
	# the lobby beyond the cage: a lamp over each passage mouth, or the way out of the lift is a black hole
	_light("lobby_w", "omni", Vector3(-4.6, 2.8, 5.3), warm, 1.1, 6.0, "L")
	_light("lobby_e", "omni", Vector3(4.6, 2.8, 5.3), warm, 1.1, 6.0, "L")
	# a camera-following fill for close-ups (never shadowed, no hot spots on glass)
	var fill := OmniLight3D.new()
	fill.light_color = Color("ffe8cc")
	fill.light_energy = 0.0
	fill.omni_range = 2.4
	fill.omni_attenuation = 1.3
	fill.light_specular = 0.0
	add_child(fill)
	lights["focus_fill"] = fill
	# reflection probes, captured once per zone (their bounce light lifts the walls); glowing lamps stay out
	for z: Array in [["C", Vector3(-8.75, 3.0, 0.0), Vector3(9.0, 6.0, 8.6)], ["G", Vector3(0.0, 2.2, 0.0), Vector3(9.0, 4.5, 9.0)],
			["N", Vector3(8.75, 2.0, 0.0), Vector3(9.0, 4.0, 8.6)]]:
		var probe := ReflectionProbe.new()
		probe.size = z[2]
		probe.position = z[1]
		probe.update_mode = ReflectionProbe.UPDATE_ONCE
		probe.interior = true
		probe.cull_mask = ~NO_PROBE_LAYER & 0xFFFFF
		probe.set_meta("cull", z[0])
		add_child(probe)
		_probes.append(probe)
	var dust := DustMotes.create(Vector3(4.0, 2.4, 3.8), 140)
	dust.position = Vector3(-8.7, 2.6, 0.0)
	add_child(dust)
	tag_cull(dust, "C")


func _build_views() -> void:
	for id: String in UndergroundData.VIEWS:
		var v: Array = UndergroundData.VIEWS[id]
		cam.add_view(id, v[0], v[1], v[2], v[3])


## Portal cards (§1.4): an unshaded quad at the far end of an open tunnel, tinted with the hidden zone's light.
func _build_portals() -> void:
	for pid: String in UndergroundData.PORTALS:
		var p: Array = UndergroundData.PORTALS[pid]
		var mi := MeshInstance3D.new()
		mi.name = "card_" + pid
		var q := QuadMesh.new()
		q.size = p[4]
		mi.mesh = q
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.albedo_color = (p[5] as Color) * 0.32
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		var e := part(p[0], pid)
		if e:
			mi.global_transform = e.global_transform
		else:
			var f: Array = UndergroundData.PORTAL_FALLBACK[pid]
			mi.global_transform = Transform3D(Basis(Vector3.UP, deg_to_rad(float(f[1]))), f[0])
		mi.visible = false
		_portals[pid] = mi


func _build_eyepiece() -> void:
	eyepiece = Node3D.new()
	eyepiece.name = "eyepiece"
	cam.add_child(eyepiece)
	var r_in := 1.0
	var r_out := 3.4
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 64
	var inner := Color("2a2116")
	var lip := Color("8a6a36")
	var outer := Color("120e09")
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		for ring: Array in [[r_in, r_in * 1.06, lip, inner], [r_in * 1.06, r_out, inner, outer]]:
			var ra: float = ring[0]
			var rb: float = ring[1]
			var p0 := Vector3(cos(a0) * ra, sin(a0) * ra, 0)
			var p1 := Vector3(cos(a1) * ra, sin(a1) * ra, 0)
			var q0 := Vector3(cos(a0) * rb, sin(a0) * rb, 0)
			var q1 := Vector3(cos(a1) * rb, sin(a1) * rb, 0)
			for v: Array in [[p0, ring[2]], [q0, ring[3]], [q1, ring[3]], [p0, ring[2]], [q1, ring[3]], [p1, ring[2]]]:
				st.set_color(v[1])
				st.add_vertex(v[0])
	var mesh := st.commit()
	var mi := MeshInstance3D.new()
	mi.name = "IA_port_ring"
	mi.mesh = mesh
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true # the colours above are what the rim should show; read as linear they turn beige
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = true
	m.render_priority = 10
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	eyepiece.add_child(mi)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var shape := mesh.create_trimesh_shape()
	shape.backface_collision = true
	cs.shape = shape
	body.add_child(cs)
	body.set_meta("part", "IA_port_ring")
	mi.add_child(body)
	eyepiece.visible = false


## Frame a port view (or its memory) with the eyepiece rim: the opening just fits the view's height.
func _place_eyepiece(id: String) -> void:
	var port := ""
	if id.begins_with("port_") and id.length() >= 6:
		port = id.substr(0, 6)
	eyepiece.visible = port != ""
	if port == "":
		return
	var fov: float = UndergroundData.VIEWS[id][2]
	var d := 0.12
	var r := d * tan(deg_to_rad(fov * 0.5)) * 0.97
	eyepiece.transform = Transform3D(Basis.from_scale(Vector3.ONE * r), Vector3(0, 0, -d))
	for body in eyepiece.find_children("*", "StaticBody3D", true, false):
		body.set_meta("hotspot", port)


func _build_frost() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	_frost = ColorRect.new()
	_frost.set_anchors_preset(Control.PRESET_FULL_RECT)
	_frost.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := ShaderMaterial.new()
	m.shader = load("res://src/fx/port_frost.gdshader")
	_frost.material = m
	_frost.visible = false
	layer.add_child(_frost)


# ====================================================================== culling (§1.4)
func groups_for(view: String) -> String:
	var v: Array = UndergroundData.VIEWS.get(view, [])
	if v.is_empty():
		return ALL_GROUPS
	var g: String = v[4]
	if str(v[5]) != "" and bool(l3().state.get(v[5], false)):
		g += str(v[6])
	if _cinematic and view == "shutter" and l3().state["shutter_open"]:
		g += "GS"
	return g


static func _any(tags: String, drawn: String) -> bool:
	for c in tags:
		if drawn.contains(c):
			return true
	return false


func apply_culling(view: String) -> void:
	_drawn = groups_for(view)
	# safe graphics level 2+ (CrashGuard): no probes or particles, whatever the view draws
	var safe := CrashGuard.safe_level() >= 2
	for n in _cull_nodes:
		if not is_instance_valid(n):
			continue
		var tags := str(n.get_meta("cull", ""))
		var on := tags == "" or _any(tags, _drawn)
		n.set_meta("culled", not on)
		n.visible = bool(n.get_meta("present", true)) and on and not (safe and n is GPUParticles3D)
	for p in _probes:
		p.visible = not safe and _any(str(p.get_meta("cull", "")), _drawn)
	var s := l3().state
	for pid: String in _portals:
		var e: Array = UndergroundData.PORTALS[pid]
		var mi: MeshInstance3D = _portals[pid]
		mi.visible = _drawn.contains(e[1]) and bool(s[e[2]]) and not _drawn.contains(e[3])
	if visuals:
		visuals.refresh_presence()
	sync_colliders()


# ====================================================================== hooks
func main_root() -> String:
	if cam == null:
		return "choir"
	var z := UndergroundData.zone_of(cam.current())
	if z == "lift":
		return cam.current()
	return UndergroundData.ZONE_ROOT.get(z, start_view())


func hotspot_view(hs: String) -> String:
	var s := l3().state
	var zone := UndergroundData.zone_of(cam.current())
	match hs:
		"cabinet_0", "cabinet_1", "cabinet_2", "plate":
			if cam.is_root():
				return "switch_room"
			return "interlock_plate" if hs == "plate" else hs
		"door_west":
			return "blast_west_hall" if zone == "choir" else "blast_west"
		"door_east":
			return "" if zone == "nursery" else "blast_east"
		"office", "case":
			if not s["office_open"]:
				return "office_door"
			return "office" if hs == "office" else "meter_case"
		"camp", "recorder", "shutter":
			if not s["camp_open"] and not s["shutter_open"]:
				return "seal" # the camp is sealed: the way in is the seal
	return UndergroundData.HOTSPOT_VIEW.get(hs, "")


func deeper_views() -> Dictionary:
	return UndergroundData.DEEPER


func view_caption(id: String) -> String:
	return UndergroundData.CAPTION.get(id, "")


func use_target(hs: String, p: String) -> String:
	var sel := logic.selected
	match hs:
		"cabinet_0", "cabinet_1", "cabinet_2":
			return hs
		"office_door":
			return "office_door"
		"desk":
			return "desk_hook" if sel == UndergroundLogic.DESK_KEY else "_"
		"lift":
			if p.contains("west"):
				return "lift_gate_west"
			if p.contains("east"):
				return "lift_gate_east"
			return "lift_gate_west" if cam.current() == "lift_w" else "lift_gate_east"
		"autoclave":
			return "autoclave"
		"seed_library":
			return "seed_library"
		"console":
			return "cradle"
		"memorial":
			return "socket_42"
		"passage_w", "passage_e", "tunnel", "door_west", "door_east", "seal", "camp", "glass_floor", "plate", "chart":
			return "" # ways through and things to look at: with an item in hand the player still walks on / looks
	return "_" if sel != "" else ""


func tap_special(p: String, _r: Dictionary) -> bool:
	if p.begins_with("Echo_"):
		var id := p.substr(5)
		var via_port := cam.current().ends_with("_mem")
		var ev := l3().release_echo(id, via_port)
		return not ev.has("nothing_happens")
	if p.begins_with("IA_tube_"):
		var r := int(p.substr(8))
		if r == int(l3().state["tube_hand"]):
			# the tube in hand: the meter reads it, otherwise it simply rings
			if logic.selected == "resonance_meter":
				l3().measure_tube(-1)
			else:
				tones.tube(r)
			return true
	return false


func drag_part_started(p: String) -> bool:
	_knob_acc = 0.0
	_drag_kind = ""
	if p in ["IA_knob_x", "IA_knob_y"] and cam.current() in ["console", "scope", "cradle", "strand_plate"]:
		_drag_kind = p
	elif p in ["IA_prism_p", "IA_prism_q"] and cam.current() == "prisms":
		_drag_kind = p
	return _drag_kind != ""


func drag_part(rel: Vector2) -> void:
	_knob_acc += (rel.x - rel.y) / (DRAG_PX_PER_STEP * maxf(1.0, DisplayServer.screen_get_scale()))
	var steps := int(_knob_acc)
	if steps == 0:
		return
	_knob_acc -= steps
	match _drag_kind:
		"IA_knob_x":
			l3().turn_freq("x", signi(steps))
		"IA_knob_y":
			l3().turn_freq("y", signi(steps))
		"IA_prism_p":
			l3().turn_prism("p", signi(steps))
		"IA_prism_q":
			l3().turn_prism("q", signi(steps))


func go_back() -> void:
	if _ending or _cinematic:
		return
	if cam.is_root():
		if cam.current() != main_root():
			cam.go(main_root())
		return
	cam.back()


# ====================================================================== interactions
func _walk(view: String) -> void:
	cam.go(view)
	AudioManager.ui("ui_tap")


func _say(key: String) -> void:
	hud.call("message", tr(key))


func interact(hs: String, p: String, r: Dictionary) -> void:
	match hs:
		"passage_w", "passage_e":
			_interact_passage(hs.substr(8))
		"lift":
			_interact_lift(p)
		"rack":
			_interact_rack(p, r)
		"office_door":
			_interact_office_door(p)
		"office":
			_interact_office(p)
		"case":
			_interact_case(p)
		"desk":
			_interact_desk(p)
		"cabinet_0", "cabinet_1", "cabinet_2":
			_interact_cabinet(int(hs.substr(8)), p)
		"plate":
			pass
		"port_a", "port_b", "port_c":
			_interact_port(hs.substr(5), p)
		"door_west", "door_east":
			_interact_door(hs.substr(5), p)
		"glass_floor":
			if cam.current() != "glass_floor":
				cam.go("glass_floor")
		"tunnel":
			if not l3().state["shutter_open"]:
				_say("msg.c3_shutter_shut")
			elif UndergroundData.zone_of(cam.current()) == "gallery":
				_walk("camp")
			else:
				_walk("gallery_w")
		"console":
			_interact_console(p)
		"memorial":
			_interact_memorial(p)
		"autoclave":
			_interact_autoclave(p)
		"seed_library":
			_interact_library(p)
		"chart":
			pass
		"prisms":
			_interact_prisms(p)
		"seal":
			_interact_seal()
		"camp":
			if cam.current() != "camp":
				_walk("camp")
		"recorder":
			_interact_recorder(p)
		"shutter":
			_interact_shutter(p)


func _entry_side() -> String:
	return "w" if l3().state["entry"] == "choir" else "e"


func _interact_passage(side: String) -> void:
	var from_lift := UndergroundData.zone_of(cam.current()) == "lift"
	if side != _entry_side():
		_say("msg.c3_gate_shut")
		AudioManager.sfx("locker_rattle", -6.0, 0.7)
		return
	if from_lift:
		if visuals.gate_open:
			_walk("choir" if side == "w" else "nursery")
		else:
			_say("msg.c3_gate_shut")
	else:
		_walk(_lift_view())


func _interact_lift(p: String) -> void:
	var side := "w" if p.contains("west") else ("e" if p.contains("east") else _entry_side())
	if side == _entry_side() and visuals.gate_open and p.begins_with("IA_gate_") and not p.contains("lock"):
		_walk("choir" if side == "w" else "nursery")
		return
	_say("msg.c3_gate_shut" if side != _entry_side() else "obj3.lift")


func _rack_place(p: String) -> int:
	var s := l3().state
	if p.begins_with("IA_slot_"):
		return int(p.substr(8))
	if p.begins_with("IA_bench_"):
		return UndergroundLogic.SLOTS + int(p.substr(9))
	if p.begins_with("IA_tube_"):
		return (s["tubes"] as Array).find(int(p.substr(8)))
	return -1


func _interact_rack(p: String, r: Dictionary) -> void:
	var l := l3()
	var cur := cam.current()
	if p == "IA_hammer":
		visuals.strike()
		l.strike_hammer()
		return
	var place := _rack_place(p)
	if place < 0:
		# the bench or the rack's frame: step over to it, or closer to the chalk staircase
		var px: float = (r.get("pos", Vector3.ZERO) as Vector3).x
		if px > -8.1:
			if cur != "bench":
				_walk("bench")
		elif cur == "rack":
			_walk("rack_close")
		elif cur != "rack_close":
			_walk("rack")
		return
	if logic.selected == "resonance_meter":
		l.measure_tube(place)
	else:
		l.tap_tube(place)


func _interact_office_door(p: String) -> void:
	var l := l3()
	var s := l.state
	if p in ["IA_office_lock", "Item_office_key"] and s["office_key"] and not s["office_open"]:
		l.take_office_key()
		return
	if p in ["IA_office_lock", "Item_office_key"] and s["office_key"] and s["office_open"]:
		l.take_office_key() # trapped while the door stands open: the logic says so
		return
	l.toggle_office()


func _interact_office(p: String) -> void:
	var l := l3()
	var cur := cam.current()
	if p in ["Item_office_lamp", "IA_office_lamp", "office_bulb"]:
		if cur != "ecg_lamp":
			_walk("ecg_lamp")
		elif l.can_take("office_lamp"):
			l.take("office_lamp")
		return
	if p == "Item_office_letters" and l.can_take("office_letters"):
		l.take("office_letters")
		return
	if p == "IA_note":
		hud.call("show_document", "strand_note")
		return
	if cur != "office":
		_walk("office")


func _interact_case(p: String) -> void:
	var l := l3()
	if p.begins_with("IA_case_dial_"):
		l.turn_case_wheel(int(p.substr(13)), 1)
	elif p == "IA_case_latch":
		l.try_case()
	elif p == "Item_meter_case" and l.can_take("meter_case"):
		l.take("meter_case")
	elif l.state["case_open"] and l.can_take("meter_case"):
		l.take("meter_case")


func _interact_desk(p: String) -> void:
	var l := l3()
	if p.begins_with("IA_lever_"):
		l.pull_lever(int(p.substr(9)))
	elif p == "IA_master_knob":
		l.turn_knob(1)
	elif p in ["IA_desk_hook", "Item_desk_hook"]:
		if l.can_take("desk_hook"):
			l.take("desk_hook")
	elif not l.desk_live() and not l.state["hall_started"]:
		_say("msg.c3_desk_dead")


func _interact_cabinet(n: int, p: String) -> void:
	var l := l3()
	if p == "IA_isolator":
		l.turn_isolator(n)
	elif p in ["IA_lock", "Item_cab_in_%d" % n] or p.begins_with("lock_sym_"):
		l.take_cabinet_key(n, "in")
	elif p in ["IA_key_window", "Item_cab_held_%d" % n]:
		l.take_cabinet_key(n, "held")


func _interact_port(port: String, p: String) -> void:
	if p == "IA_port_ring":
		visuals.port_ring("port_" + port)
		AudioManager.sfx("collar_click", -3.0, 0.9)
		var mem := "port_%s_mem" % port
		if cam.current() == mem:
			cam.back()
		else:
			cam.go(mem)


func _interact_door(side: String, p: String) -> void:
	var l := l3()
	var s := l.state
	var open: bool = s["door_%s_open" % side]
	var zone := UndergroundData.zone_of(cam.current())
	if zone != "gallery":
		# the hall side: walk through when open
		if open:
			_walk("gallery" if side == "west" else "gallery_w")
		else:
			_say("msg.c3_door_sealed")
			AudioManager.sfx("drawer_locked", -6.0, 0.6)
		return
	var drum_part := p.begins_with("IA_drum") or p == "drum_lamp"
	if drum_part:
		var drum_view := "drum_" + side
		if cam.current() != drum_view:
			cam.go(drum_view)
		elif l.sealed_door() != side:
			_say("msg.c3_drum_dead")
		elif s["drum_open"]:
			pass
		elif p == "IA_drum_handle":
			visuals.pull("door_" + side, "IA_drum_handle", UndergroundVisuals.HANDLE_PULL_DEG)
			l.pull_drum_handle()
		elif p.begins_with("IA_drum_") and p.substr(8).is_valid_int():
			l.turn_drum(int(p.substr(8)), 1)
		return
	if open:
		_walk("choir" if side == "west" else "nursery")
	elif cam.current() != "blast_" + side:
		cam.go("blast_" + side)
	else:
		_say("msg.c3_door_sealed")


func _tap_dir(key: String, value: int, lo: int, hi: int) -> int:
	var d := int(_dirs.get(key, 1 if value < hi else -1))
	if value + d > hi or value + d < lo:
		d = -d
	_dirs[key] = d
	return d


func _interact_console(p: String) -> void:
	var l := l3()
	var s := l.state
	var cur := cam.current()
	if p in ["IA_knob_x", "IA_knob_y"]:
		var axis := p.substr(8)
		l.turn_freq(axis, _tap_dir(p, int(s["freq_" + axis]), UndergroundLogic.FREQ_MIN, UndergroundLogic.FREQ_MAX))
		return
	if p in ["IA_cradle", "cradle_ring", "cradle_mount", "Item_cradle"]:
		if s["cradle"] != "":
			l.take_from_cradle()
		elif cur != "cradle":
			cam.go("cradle")
		else:
			_say("msg.c3_cradle_empty")
		return
	if p == "IA_strand_plate":
		if cur != "strand_plate":
			cam.go("strand_plate")
		return
	if p == "scope_screen":
		if cur != "scope":
			cam.go("scope")
		return
	if cur != "console":
		cam.go("console")


func _interact_memorial(p: String) -> void:
	var l := l3()
	var s := l.state
	if p in ["IA_socket_42", "socket_42_ring", "socket_42_mount", "Item_socket_42"]:
		if cam.current() != "socket_42":
			cam.go("socket_42")
		elif s["socket_42"] != "":
			l.take_from_socket_42()
		elif not s["secret"]:
			_say("msg.c3_socket_dark")
		return
	if cam.current() != "memorial":
		cam.go("memorial")


func _interact_autoclave(p: String) -> void:
	var l := l3()
	var cur := cam.current()
	if p == "IA_ac_door" or p == "growth_window":
		l.toggle_autoclave()
	elif p == "Item_chamber":
		l.take("autoclave")
	elif p.begins_with("IA_peg_"):
		if cur != "cam_drum":
			cam.go("cam_drum")
		else:
			l.turn_peg(int(p.substr(7)), 1)
	elif p == "IA_start_lever":
		l.pull_start_lever()
	elif p == "IA_remelt":
		visuals.press("autoclave", "IA_remelt", UndergroundVisuals.REMELT_PRESS)
		l.remelt()
	elif p in ["IA_growth_log", "log_page", "log_sketch"]:
		if cur != "growth_log":
			cam.go("growth_log")
		else:
			hud.call("show_document", "growth_log")
	elif cur != "autoclave":
		cam.go("autoclave")


func _interact_library(p: String) -> void:
	var l := l3()
	var s := l.state
	if p.begins_with("IA_seed_drawer_"):
		l.open_seed_drawer(int(p.substr(15)))
	elif p.begins_with("Item_seed_"):
		var i := int(p.substr(10))
		if i == int(s["seed_drawer"]):
			l.take("seed_drawer")
		else:
			l.open_seed_drawer(i)
	elif cam.current() not in ["seed_library", "seed_drawer"]:
		cam.go("seed_library")


func _interact_prisms(p: String) -> void:
	var l := l3()
	var s := l.state
	match p:
		"IA_p_left", "IA_p_right", "IA_q_left", "IA_q_right":
			visuals.press("prism_bench", p, UndergroundVisuals.NUDGE_PRESS)
			l.turn_prism(p.substr(3, 1), -1 if p.ends_with("left") else 1)
		"IA_prism_p", "IA_prism_q":
			var w := p.substr(9)
			l.turn_prism(w, _tap_dir(p, int(s["prism_" + w]), UndergroundLogic.PRISM_MIN, UndergroundLogic.PRISM_MAX))
		_:
			if cam.current() != "prisms":
				cam.go("prisms")


func _interact_seal() -> void:
	if l3().state["camp_open"]:
		_walk("camp")
	elif cam.current() != "seal":
		cam.go("seal")
	else:
		_say("msg.c3_seal_dark")


func _interact_recorder(p: String) -> void:
	var l := l3()
	if cam.current() != "recorder":
		cam.go("recorder")
		return
	if p == "IA_rec_play":
		l.play_recorder()
	elif p == "IA_rec_rewind":
		if l.state["camp_open"]:
			visuals.pull("field_recorder", "IA_rec_rewind", UndergroundVisuals.REC_KEY_DEG, Vector3.RIGHT, 0.2)
			AudioManager.sfx("deck_eject", -6.0, 1.4)
			_play_recording()


func _interact_shutter(p: String) -> void:
	var l := l3()
	if p.begins_with("IA_tcrystal_"):
		if cam.current() != "shutter":
			cam.go("shutter")
			return
		var size := int(p.substr(12))
		l.tap_crystal(l.frame_sizes().find(size))
		return
	if l.state["shutter_open"]:
		_walk("gallery_w")
	elif cam.current() != "shutter":
		cam.go("shutter")


# ====================================================================== per-frame
func _process(_delta: float) -> void:
	var fill: OmniLight3D = lights["focus_fill"]
	fill.global_position = cam.global_position + cam.global_basis * Vector3(0.12, 0.18, 0.05)


# ====================================================================== view changes
## Close-ups whose dark metal must be read (drum symbols, lock faces, the cam drum, the socket) get a stronger
## camera fill: at 0.9 the east drum lock stayed near black in the rendered QA.
const BRIGHT_CLOSEUPS: Array[String] = ["drum_west", "drum_east", "cabinet_0", "cabinet_1", "cabinet_2", "meter_case",
	"cam_drum", "growth_log", "seed_drawer", "socket_42", "recorder", "interlock_plate"]


func view_changed_hook(id: String) -> void:
	apply_culling(id)
	var fill: OmniLight3D = lights["focus_fill"]
	var e := 0.0 if cam.is_root() or id.ends_with("_mem") else (1.5 if id in BRIGHT_CLOSEUPS else 0.9)
	create_tween().tween_property(fill, "light_energy", e, 0.6)
	_frost.visible = id.ends_with("_mem")
	_place_eyepiece(id)
	sync_colliders(eyepiece)
	visuals.view_changed(id)
	_zone_mood(UndergroundData.zone_of(id))
	if id == "seed_library":
		l3().look("seed_library")


const ZONE_AMBIENT := {"choir": Color("3a3226"), "gallery": Color("223438"), "nursery": Color("2c3a40"),
	"lift": Color("332c24")}
const ZONE_TONE := {"choir": ["amb_choir", "amb_power_hum"], "gallery": ["amb_gallery", "amb_archive"],
	"nursery": ["amb_nursery", "amb_lab_dark"], "lift": ["amb_lift", "amb_power_hum"]}


## Each zone has its own ambient tint and room tone (reusing earlier tracks until Chapter 3's exist).
func _zone_mood(zone: String) -> void:
	if zone == "" or zone == _zone:
		return
	var old := _zone
	_zone = zone
	if env:
		create_tween().tween_property(env, "ambient_light_color", ZONE_AMBIENT.get(zone, Color("2c3434")), 1.2)
	var want := _track("ambience", ZONE_TONE[zone])
	if old != "":
		var had := _track("ambience", ZONE_TONE[old])
		if had != want:
			AudioManager.ambience(had, false)
	AudioManager.ambience(want, true, -6.0 if zone != "choir" or not l3().state["hall_started"] else -2.0)


func _track(kind: String, names: Array) -> String:
	for n: String in names:
		if AudioManager.stream(kind, n) != null:
			return n
	return str(names[-1])


func _music(finale: bool) -> void:
	if finale:
		AudioManager.music(_track("music", ["music_underground_finale", "music_archive_finale"]), 2.0)
	else:
		AudioManager.music(_track("music", ["music_underground", "music_archive"]), 4.0)


# ====================================================================== events → feedback
func _on_events(ev: Array[String]) -> void:
	var seq := ""
	for e in ev:
		_feedback(e)
		if e in ["hall_started", "array_awake", "secret_echo"] or e.begins_with("grew:") or e == "shutter_open":
			seq = e if seq == "" else seq
	visuals.apply_state(true)
	apply_culling(cam.current())
	hud.call("set_caption", view_caption(cam.current()))
	match seq:
		"hall_started":
			_hall_start(ev.has("blast_door_open:west"))
		"shutter_open":
			_shutter_opens(ev.has("gallery_awake"))
		"array_awake":
			_array_wakes()
		"secret_echo":
			_secret()
	if seq.begins_with("grew:"):
		_grow(seq == "grew:clear")


const MESSAGES := {
	"office_locked": "msg.c3_office_locked", "office_opened": "msg.c3_office_open", "isolator_no_key": "msg.c3_isolator_no_key",
	"isolator_held_missing": "msg.c3_isolator_held_missing", "key_wrong_lock": "msg.c3_wrong_lock",
	"desk_live": "msg.c3_desk_live", "case_locked": "msg.c3_case_locked", "case_opened": "msg.c3_case_open",
	"rack_locked": "msg.c3_rack_locked", "choir_chord": "msg.c3_chord", "choir_discord": "msg.c3_discord",
	"hall_running": "msg.c3_hall_running", "desk_dead": "msg.c3_desk_dead", "breaker_trip": "msg.c3_breaker",
	"levers_dropped": "msg.c3_levers_dropped", "gallery_awake": "msg.c3_gallery_awake", "seed_in_play": "msg.c3_seed_in_play",
	"autoclave_shut": "msg.c3_autoclave_shut", "autoclave_not_closed": "msg.c3_autoclave_not_closed",
	"autoclave_empty": "msg.c3_autoclave_empty", "autoclave_full": "msg.c3_autoclave_full", "remelted": "msg.c3_remelted",
	"seal_open": "msg.c3_seal_open", "crystals_damped": "msg.c3_damped", "drum_wrong": "msg.c3_drum_wrong",
	"cradle_refused": "msg.c3_cradle_refused", "cradle_full": "msg.c3_cradle_full", "knobs_locked": "msg.c3_knobs_locked",
	"socket_dark": "msg.c3_socket_dark", "socket_refused": "msg.c3_socket_refused", "gate_wrong_key": "msg.c3_gate_wrong",
	"nothing_happens": "msg.nothing",
}


func _feedback(e: String) -> void:
	var l := l3()
	var s := l.state
	var name := e.get_slice(":", 0)
	var arg := e.get_slice(":", 1) if e.contains(":") else ""
	if MESSAGES.has(name) and name != "nothing_happens":
		_say(MESSAGES[name])
	match name:
		"item_added":
			AudioManager.sfx("item_pickup")
			AudioManager.haptic(15)
			hud.call("message", tr("ui.item_added") % tr(ItemDB.name_key(arg)))
		"selected":
			visuals.selection_changed(arg)
			apply_culling(cam.current())
		"key_trapped":
			_say("msg.c3_office_key_trapped" if s["office_open"] and s["office_key"] and cam.current() == "office_door" else "msg.c3_key_trapped")
			AudioManager.sfx("locker_rattle", -4.0, 1.1)
		"key_in", "key_back", "key_hung":
			AudioManager.sfx("key_turn", -2.0)
		"isolator_off", "isolator_on":
			AudioManager.sfx("breaker_on" if name == "isolator_on" else "relay_click", -1.0, 0.8)
			AudioManager.haptic(60)
			hud.call("caption", tr("cap3.isolator"), 2.5)
		"office_opened":
			AudioManager.sfx("door_open", -2.0)
		"office_closed":
			AudioManager.sfx("door_slam", -10.0, 1.2)
		"office_locked", "isolator_no_key", "isolator_held_missing", "key_wrong_lock", "case_locked", "drum_wrong":
			AudioManager.sfx("drawer_locked", -4.0, 0.9)
		"case_wheel", "drum", "peg", "freq", "prism", "knob":
			AudioManager.sfx("collar_click", -4.0, randf_range(0.95, 1.05))
		"case_opened":
			AudioManager.sfx("safe_open", -2.0)
		"tube_lifted", "tube_placed", "tube_swapped":
			var pos := int(arg)
			tones.tube(int(s["tube_hand"]) if name == "tube_lifted" else int(s["tubes"][pos]), -10.0)
		"meter":
			hud.call("message", tr("msg.c3_meter") % int(arg))
			tones.tube(int(arg), -8.0)
			visuals.meter_reading(int(arg))
		"choir_chord":
			visuals.strike()
			tones.chord(true)
			hud.call("caption", tr("cap3.chord"), 3.0)
		"choir_discord":
			tones.chord(false)
		"lever":
			AudioManager.sfx("switch_toggle", -2.0, 0.8)
		"counter":
			AudioManager.sfx("relay_click", -4.0, 1.0 + 0.05 * int(arg))
		"breaker_trip":
			AudioManager.sfx("breaker_trip")
			AudioManager.haptic(120)
			visuals.breaker_trip()
		"desk_live":
			AudioManager.sfx("power_on", -4.0)
		"blast_door_open":
			_say("msg.c3_blast_door")
			AudioManager.sfx("vault_door_open", -2.0, 0.8)
		"console_power":
			_say("msg.c3_power_" + arg)
			AudioManager.sfx("power_on", -4.0, 1.1)
		"seed_drawer":
			AudioManager.sfx("drawer_open", -4.0, 1.2)
			if int(arg) >= 0:
				prepare_view("seed_drawer")
				if cam.current() == "seed_drawer":
					cam.refresh()
				else:
					cam.go("seed_drawer")
			elif cam.current() == "seed_drawer":
				cam.go("seed_library")
		"seed_returned":
			_say("msg.c3_seed_returned")
		"leyla_echo":
			hud.call("caption", tr("cap3.leyla_echo"), 6.0)
			visuals.leyla_touch(int(arg))
		"autoclave_closed", "autoclave_opened":
			AudioManager.sfx("hatch_open", -6.0, 1.3)
		"autoclave_loaded", "autoclave_emptied", "crystal_cradled", "crystal_socketed", "cradle_emptied", "socket_emptied":
			AudioManager.sfx("lens_insert", -2.0)
		"remelted":
			hud.call("caption", tr("cap3.hiss"), 2.5)
			AudioManager.sfx("compressor_start", -8.0, 1.3)
		"receptors":
			AudioManager.sfx("slide_clunk", -8.0, 1.4)
		"seal_open":
			AudioManager.sfx("vault_bolts", -4.0, 1.2)
		"recorder_clicks", "recorder_play":
			_play_recording()
		"crystal_note":
			tones.crystal(int(arg))
			visuals.crystal_ring(int(arg))
		"crystals_damped":
			AudioManager.sfx("ledger_thump", -4.0, 1.3)
			visuals.damp_crystals()
		"shutter_open":
			_say("msg.c3_shutter")
		"knobs_locked", "hall_running":
			pass
		"echo_released":
			AudioManager.sfx("reveal", 0.0, 1.2)
			hud.call("caption", tr("echo3." + arg), 4.5)
			hud.call("message", tr("msg.c3_echo_count") % (s["echoes"] as Array).size())
			visuals.release_echo(arg)
		"all_echoes":
			GameState.unlock_achievement("echoes_of_the_deep")
		"gate_open":
			visuals.gate_open = true
			AudioManager.sfx("key_turn")
		"solved":
			AudioManager.sfx("puzzle_solved", -5.0)
		"chapter_complete":
			hud.call("show_chapter_complete")


## The seed_drawer view follows the open drawer: F_i + (−0.30, 0.36, 0) looking at F_i + (0.10, −0.04, 0) (§2).
func prepare_view(id: String) -> void:
	if id != "seed_drawer":
		return
	var i := maxi(0, int(l3().state["seed_drawer"]))
	var r := i / UndergroundLogic.SEED_COLUMNS
	var c := i % UndergroundLogic.SEED_COLUMNS
	var lib := models.get("seed_library") as Node3D
	var xf := lib.global_transform if lib else Transform3D(Basis(Vector3.UP, deg_to_rad(-90.0)), Vector3(13.0, 0.0, -0.6))
	var f := xf * Vector3((c - 1.5) * 0.33, 1.50 - 0.26 * r, 0.69)
	cam.add_view("seed_drawer", f + Vector3(-0.30, 0.36, 0.0), f + Vector3(0.10, -0.04, 0.0), 42.0)


# ====================================================================== sequences
func _busy(on: bool) -> void:
	_cinematic = on
	hud.call("set_busy", on)


## How long the HUD's intro waits for the descent before handing over control.
func opening_seconds() -> float:
	return INTRO_SECONDS


## Called by the HUD intro: the freight lift sinks through rock, caged lamps pass upward, the hum grows; on arrival
## the entry gate folds open.
func play_opening_camera() -> void:
	var shaft := part("shell_lift", "intro_shaft")
	var lobby: Array[Node3D] = []
	for n in ["lobby_floor", "lobby_walls", "lobby_ceiling", "lift_shaft", "IA_passage_w", "IA_passage_e"]:
		var p := part("shell_lift", n)
		if p:
			lobby.append(p)
			p.visible = false
	visuals.gate_open = false
	visuals.intro_key = true
	visuals.apply_state(false)
	cam.go(_lift_view(), true)
	AudioManager.ambience("amb_power_hum", true, -14.0, 1.0)
	AudioManager.sfx("projector_charge", -10.0, 0.5)
	if shaft:
		var base := shaft.position
		shaft.visible = true
		var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		tw.tween_property(shaft, "position", base + Vector3(0, 9.0, 0), 5.6)
		await tw.finished
		shaft.visible = false
		shaft.position = base
	else:
		await get_tree().create_timer(5.6).timeout
	for p in lobby:
		p.visible = true
	sync_colliders()
	AudioManager.sfx("canister_thump", 0.0, 0.6)
	AudioManager.haptic(140)
	await get_tree().create_timer(0.5).timeout
	AudioManager.sfx("key_turn")
	visuals.intro_key = false
	visuals.gate_open = true
	visuals.apply_state(true)
	AudioManager.sfx("locker_open", -2.0, 0.7)


## The hall starts: the Choir rings, the transformers wake and the arcs climb. On the first wing the west blast door
## then rolls open onto the Gallery.
func _hall_start(door: bool) -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.6).timeout
	cam.go("hall_start")
	tones.chord(true, -6.0)
	AudioManager.sfx("power_on", 0.0, 0.8)
	AudioManager.haptic(200)
	hud.call("caption", tr("cap3.chord"), 3.5)
	var arcs: OmniLight3D = lights.get("arcs")
	if arcs:
		create_tween().tween_property(arcs, "light_energy", 0.9, 1.5)
	AudioManager.ambience("amb_power_hum", true, -2.0, 3.0)
	await get_tree().create_timer(4.0).timeout
	if door:
		cam.go("blast_west_hall")
		await get_tree().create_timer(3.6).timeout
	cam.go(back if back != "" and not back.begins_with("port_") else "choir")
	await get_tree().create_timer(0.8).timeout
	_busy(false)


## Leyla's crystals open the shutter to the Gallery.
func _shutter_opens(first_wing: bool) -> void:
	_busy(true)
	await get_tree().create_timer(0.8).timeout
	cam.go("shutter")
	apply_culling("shutter")
	await get_tree().create_timer(2.6).timeout
	if first_wing:
		hud.call("caption", tr("msg.c3_gallery_awake"), 3.5)
	await get_tree().create_timer(1.2).timeout
	_busy(false)
	apply_culling(cam.current())


func _grow(clear: bool) -> void:
	_busy(true)
	cam.go("grow")
	hud.call("caption", tr("cap3.hiss"), 2.5)
	await visuals.grow(clear)
	_say("msg.c3_grew_clear" if clear else "msg.c3_grew_cloudy")
	await get_tree().create_timer(1.0).timeout
	cam.go("autoclave")
	_busy(false)


## The figure locks: 41 lights rise up the shaft, Strand and Leyla appear, and the choice is offered.
func _array_wakes() -> void:
	_ending = true
	logic.select_item("")
	_busy(true)
	_music(true)
	await get_tree().create_timer(1.0).timeout
	cam.go("array_rise")
	AudioManager.sfx("crystal_record", -2.0, 0.6)
	await get_tree().create_timer(5.0).timeout
	cam.go("finale")
	hud.call("caption", tr("cap3.echoes_appear"), 6.0)
	await get_tree().create_timer(6.0).timeout
	_busy(false)
	hud.call("show_choice")


func _secret() -> void:
	_busy(true)
	await get_tree().create_timer(0.6).timeout
	cam.go("secret")
	hud.call("caption", tr("cap3.secret"), 7.0)
	await visuals.leyla_kneel(7.0)
	cam.go("socket_42")
	_busy(false)


## Leyla's 1998 recording: her words as captions, then the four notes she taps on her crystals.
func _play_recording() -> void:
	_recording += 1
	var gen := _recording
	visuals.recorder(true)
	hud.call("caption", tr("cap3.recorder"), 2.0)
	AudioManager.sfx("tape_hiss", -10.0)
	await get_tree().create_timer(2.0).timeout
	var lines := tr("doc3.recorder").split(". ", false)
	for line in lines:
		if gen != _recording:
			return
		hud.call("caption", line.strip_edges() + ("" if line.ends_with(".") else "."), 3.0)
		await get_tree().create_timer(3.0).timeout
	for size: Variant in l3().melody():
		if gen != _recording:
			return
		tones.crystal(int(size), -6.0)
		visuals.crystal_ring(int(size), false)
		await get_tree().create_timer(0.9).timeout
	await get_tree().create_timer(0.8).timeout
	if gen == _recording:
		visuals.recorder(false)
