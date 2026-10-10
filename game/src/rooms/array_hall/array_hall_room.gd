class_name ArrayHallRoom
extends RoomBase
## Chapter 4 scene: the Array Hall, the unnumbered floor of the Institute. It assembles the hall from the models in
## docs/models/ch4.md (tables in ArrayHallData), draws only the zones a view needs (§1.3), routes taps to ArrayHallLogic and
## lets ArrayHallVisuals render the resulting state. A model that is not built yet is skipped (ModelUtil.spawn warns); its
## puzzle then has nothing to tap, which the QA playthrough reports.

## Render layer for meshes the reflection probes must not capture (glowing lamp glass), as in Chapters 2 and 3.
const NO_PROBE_LAYER := 1 << 19
const ALL_GROUPS := "HBPKRISTWElwt"
const DRAG_PX_PER_STEP := 26.0
const INTRO_SECONDS := 10.5

var visuals: ArrayHallVisuals
var tones: ArrayHallTones
var missing_models: Array[String] = []
var _cinematic := false
var _cull_nodes: Array[Node3D] = []
var _probes: Array[ReflectionProbe] = []
var _drawn := ALL_GROUPS
var _zone := ""
var _knob_acc := 0.0
var _drag_kind := ""
var _drag_model := ""
var _last_beam := 0
var _ring_sound_batch := -1
var _dirs: Dictionary = {}
var _hum_zone_loud := false
var _caption_seq := 0


func _ready() -> void:
	if GameState.logic == null or not GameState.logic is ArrayHallLogic:
		GameState.start_new("ch4")
	logic = GameState.logic
	GameState.in_game = true
	make_environment(Color("020407"), Color("3a4d5c"), 0.8, Color("070c12"), 0.003)
	env.glow_intensity = 0.42
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.25
	_build_models()
	_build_lights()
	build_camera()
	cam.far = 70.0
	_build_views()
	tones = ArrayHallTones.new()
	add_child(tones)
	visuals = ArrayHallVisuals.new(self)
	add_child(visuals)
	build_input()
	build_hud()
	add_child(PerfGuard.new())
	GameState.events.connect(_on_events)
	visuals.apply_state(false)
	DecalLoc.apply(self)
	Loc.language_changed.connect(_on_language_changed)
	var fresh := not capture_mode and _fresh_start()
	if fresh:
		visuals.gate_open = false
		visuals.intro_key = true
		visuals.apply_state(false)
	cam.go("lift_in" if fresh else start_view(), true)
	_music(l4().state["reversing"])
	if l4().state["power"]:
		tones.hum(true, -24.0, not l4().state["trust_strand"])
		tones.beat(int(l4().state["keeper"]), l4().note_target())
	if l4().state["night_undone"]:
		visuals.settle_rise(l4().ending_id())
	if fresh:
		hud.call("play_intro")
	elif not capture_mode and l4().state["night_undone"] and not l4().state["complete"]:
		_ending = true
		get_tree().create_timer(1.2).timeout.connect(func() -> void: hud.call("show_choice"))
	SceneManager.room_ready(self) # safe graphics before the first frame is drawn


func _exit_tree() -> void:
	GameState.in_game = false


func l4() -> ArrayHallLogic:
	return logic as ArrayHallLogic


## Where a continued game starts: the bridge (the hall's hub).
func start_view() -> String:
	return ArrayHallData.MAIN_ROOT


func _fresh_start() -> bool:
	var s := l4().state
	return not s["power"] and not s["booth_gate"] and not s["watch_gate"] and not (s["switches"] as Array).has(true) \
		and (s["taken"] as Dictionary).is_empty() and int(s["wheel"]) == ArrayHallLogic.FLASH_MINUTE


func _on_language_changed(_code: String) -> void:
	DecalLoc.refresh()
	DecalLoc.apply(self)


# ====================================================================== construction
func _build_models() -> void:
	for id: String in ArrayHallData.LAYOUT:
		var e: Array = ArrayHallData.LAYOUT[id]
		var n: Node3D = null
		if ResourceLoader.exists("res://assets/models/%s.glb" % e[0]):
			n = spawn(id, e[0], e[1], e[2], e[3], e[4])
		if n == null:
			if not missing_models.has(e[0]):
				missing_models.append(e[0])
			continue
		_finish_model(id, n)
		tag_cull(n, e[5])
	# the models that hang on another model's mount (they inherit its culling group)
	for id: String in ArrayHallData.MOUNTED:
		var e: Array = ArrayHallData.MOUNTED[id]
		var mount := part(e[1], e[2])
		var n: Node3D = null
		if mount and ResourceLoader.exists("res://assets/models/%s.glb" % e[0]):
			n = ModelUtil.spawn(e[0], mount, Transform3D.IDENTITY, "parts")
		if n == null:
			if not missing_models.has(e[0]):
				missing_models.append(e[0])
			continue
		_register(id, n, e[3])
		_finish_model(id, n)
	# the four mirror towers stand on their rings (the rings turn, the towers go with them)
	for k in 4:
		var mount := part("array_rings", "tower_mount_%d" % (k + 1))
		var id := "mirror_tower_%d" % (k + 1)
		var n: Node3D = null
		if mount and ResourceLoader.exists("res://assets/models/mirror_tower.glb"):
			n = ModelUtil.spawn("mirror_tower", mount, Transform3D.IDENTITY, "parts")
		if n == null:
			if not missing_models.has("mirror_tower"):
				missing_models.append("mirror_tower")
			continue
		_register(id, n, "tower_%d" % (k + 1))
		_finish_model(id, n)
	_tap_pads()
	_enclosure_taps()
	for extra in ArrayHallData.ECHO_MODELS:
		if not ResourceLoader.exists("res://assets/models/%s.glb" % extra):
			missing_models.append(extra)


func _register(id: String, n: Node3D, hotspot: String) -> void:
	n.name = id
	models[id] = n
	_roots[n] = id
	n.set_meta("hotspot", hotspot)
	tune_shadows(n)


## After a model is spawned: per-part hotspots, colliders that must not block taps, and shadows.
func _finish_model(id: String, n: Node3D) -> void:
	var parts: Dictionary = ArrayHallData.PART_HOTSPOT.get(id, {})
	for p: String in parts:
		_part_hotspot(part(id, p), parts[p])
	for mesh_name: String in ArrayHallData.NO_COLLIDER.get(id, []):
		var mi := part(id, mesh_name)
		if mi:
			for c in mi.get_children():
				if c is StaticBody3D:
					mi.remove_child(c)
					c.queue_free()
	for mi in ModelUtil.find_meshes(n):
		for prefix: String in ArrayHallData.NO_SHADOW_PREFIX:
			if str(mi.name).begins_with(prefix):
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Give one part (and only its own collider) a hotspot of its own.
func _part_hotspot(p: Node3D, hs: String) -> void:
	if p == null:
		return
	for c in p.get_children():
		if c is StaticBody3D:
			(c as StaticBody3D).set_meta("hotspot", hs)


## A tap pad around the small keys on the towers: a 0.2 m key is under 9 mm on a phone from the hatch view.
func _tap_pads() -> void:
	for id: String in ArrayHallData.TAP_PADS:
		var pads: Dictionary = ArrayHallData.TAP_PADS[id]
		for pn: String in pads:
			var n := part(id, pn)
			if n:
				var pad: Array = pads[pn]
				add_tap_area(n, pad[0], str(n.get_meta("hotspot", "")), pn, pad[1])


## The booth's and the watch room's glass takes no tap (the box and the lockers behind it must be reachable); a few opaque
## strips take the navigation tap instead.
func _enclosure_taps() -> void:
	# the two stair flights between the bridge and the lift bay
	var br := models.get("bridge") as Node3D
	if br:
		for sx: float in [-5.4, 5.4]:
			add_tap_area(br, Vector3(1.1, 1.6, 3.4), "stairs", "", Vector3(sx, 1.5, 16.4))
	var booth := models.get("booth") as Node3D
	if booth:
		add_tap_area(booth, Vector3(6.6, 0.6, 0.3), "booth", "", Vector3(0, 2.28, 1.1))
		add_tap_area(booth, Vector3(6.6, 0.3, 2.4), "booth", "", Vector3(0, 4.85, 0.1))
		add_tap_area(booth, Vector3(6.6, 2.0, 0.5), "booth", "", Vector3(0, 1.0, 0.9))
	var wr := models.get("watch_room") as Node3D
	if wr:
		add_tap_area(wr, Vector3(7.2, 0.62, 0.2), "watch", "", Vector3(0, 0.34, 1.2))
		add_tap_area(wr, Vector3(7.2, 0.75, 0.2), "watch", "", Vector3(0, 2.92, 1.2))
		add_tap_area(wr, Vector3(7.4, 0.15, 2.7), "watch", "", Vector3(0, 3.45, 0.0))


## Culling (§1.3): `groups` lists the zones a node belongs to; it is drawn while any of them is.
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


## Lights (§1.5): at most one shadowed light for the hall (the shaft), spots only for shadows; hidden zones' lights are
## off. The Core's glow is the key light of the whole hall. Lower-case groups are lamps of one view's own zone.
func _build_lights() -> void:
	var warm := Color("ffc993")
	var lumen := Color("bdf2ff")
	var s := l4().state
	var powered: bool = s["power"]
	_light("core_glow", "omni", Vector3(0.0, 4.1, 0.0), lumen, 2.0 if powered else 1.6, 13.0, "HKRIB")
	# a faint cold fill from above (no shadows): the rings, the floor and the walkways show their shapes in the dark
	var fill_dir := DirectionalLight3D.new()
	fill_dir.name = "hall_fill"
	fill_dir.light_color = Color("a9c4e0")
	fill_dir.light_energy = 0.28
	fill_dir.shadow_enabled = false
	fill_dir.rotation_degrees = Vector3(-62.0, 18.0, 0.0)
	add_child(fill_dir)
	lights["hall_fill"] = fill_dir
	for k in 4:
		var r: float = ArrayHallData.RING_RADIUS[k]
		_light("work_%d" % (k + 1), "omni", Vector3(0.0, 5.5, -r), warm, 1.0 if powered else 0.0, 7.5, "HKRIB")
	# the cold shaft down the oculus once the vent is open (the one shadowed light of the hall)
	_spot("shaft", Vector3(0.0, 12.2, 0.0), Vector3(0.0, 0.0, 0.0), 30.0, Color("d6e6ff"), 2.6 if powered else 0.0, 17.0, "HKRI", true)
	_spot("bridge_lamp", Vector3(0.0, 5.9, 13.5), Vector3(0.0, 3.5, 13.1), 70.0, warm, 1.7 if powered else 0.8, 7.0, "B", false)
	_light("panel_lamp", "omni", Vector3(0.0, 2.0, 12.6), Color("ffd29a"), 1.3, 3.2, "P")
	_light("sun_arc", "omni", Vector3(-12.4, 1.8, 0.0), Color("f2f8ff"), 0.0, 12.0, "S")
	_light("booth_lamp", "omni", _at("booth", "booth_lamp", Vector3(0.0, 4.25, -12.9)), Color("ffd7a0"), 1.1, 4.5, "t")
	_light("watch_lamp", "omni", _at("watch_room", "watch_lamp", Vector3(12.6, 2.95, 0.0)), Color("ffe0b4"), 1.1, 4.5, "w")
	_light("lift_lamp", "omni", _at("shell_lift4", "lift_light", Vector3(0.0, 5.8, 16.4)), Color("ffd29a"), 0.9, 8.0, "l")
	_light("lift_pass", "omni", Vector3(3.2, -3.0, 16.4), Color("ffcf8a"), 0.0, 6.0, "l")
	# a camera-following fill for close-ups (never shadowed, no hot spots on glass)
	var fill := OmniLight3D.new()
	fill.light_color = Color("ffe8cc")
	fill.light_energy = 0.0
	fill.omni_range = 2.6
	fill.omni_attenuation = 1.3
	fill.light_specular = 0.0
	add_child(fill)
	lights["focus_fill"] = fill
	# one reflection probe for the hall: the polished brass, the chrome mirrors and the glass tower get something to reflect
	var probe := ReflectionProbe.new()
	probe.size = Vector3(30.0, 13.0, 30.0)
	probe.position = Vector3(0.0, 6.0, 0.0)
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.interior = true
	probe.cull_mask = ~NO_PROBE_LAYER & 0xFFFFF
	probe.set_meta("cull", "H")
	add_child(probe)
	_probes.append(probe)
	var dust := DustMotes.create(Vector3(5.0, 4.0, 5.0), 110)
	dust.position = Vector3(0.0, 6.0, 0.0)
	add_child(dust)
	tag_cull(dust, "HI")


func _build_views() -> void:
	for id: String in ArrayHallData.VIEWS:
		var v: Array = ArrayHallData.VIEWS[id]
		cam.add_view(id, v[0], v[1], v[2], v[3])


# ====================================================================== culling (§1.3)
func groups_for(view: String) -> String:
	var v: Array = ArrayHallData.VIEWS.get(view, [])
	if v.is_empty():
		return ALL_GROUPS
	var g: String = v[4]
	if str(v[5]) != "" and bool(l4().state.get(v[5], false)):
		g += str(v[6])
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
	if visuals:
		visuals.refresh_presence()
	sync_colliders()


# ====================================================================== hooks
func main_root() -> String:
	return ArrayHallData.MAIN_ROOT


## True while a hotspot's zone is shut (the hall has no power yet): the tap then says why instead of moving the camera.
func _locked(hs: String) -> bool:
	if hs == "catwalk" or hs == "island" or hs.begins_with("gate_") or hs.begins_with("tower_") or hs == "collar" \
			or hs == "core" or hs == "drawer":
		return not l4().zone_open("floor")
	return false


func hotspot_view(hs: String) -> String:
	if _locked(hs):
		return "" # interact() says why
	if hs == "stairs":
		return "bridge" if ArrayHallData.zone_of(cam.current()) in ["lift", "panel"] else "lift"
	return ArrayHallData.HOTSPOT_VIEW.get(hs, "")


func deeper_views() -> Dictionary:
	return ArrayHallData.DEEPER


func view_caption(id: String) -> String:
	return ArrayHallData.CAPTION.get(id, "")


func use_target(hs: String, p: String) -> String:
	var sel := logic.selected
	match hs:
		"booth_gate", "watch_gate", "gate_1", "gate_2", "gate_3", "gate_4":
			return hs
		"core":
			return "cradle" if p in ["IA_cradle", "Item_lens"] else ""
		"desk":
			return "chronometer" if p == "IA_chronometer" else ""
		"post_station":
			return "post_canister" if p == "IA_post_canister" else ""
		"lift", "bridge", "stairs", "pier", "catwalk", "island", "apse", "booth", "watch", "chalk_lift", "chalk_panel", "board", "locker", "panel0", "wheels", \
		"collar", "drawer", "iris", "sun_pedestal", "gear_box":
			return "" # ways through and things to look at: with an item in hand the player still walks on / looks
	if hs.begins_with("tower_"):
		return ""
	return "_" if sel != "" else ""


func tap_special(p: String, _r: Dictionary) -> bool:
	if p.begins_with("Echo_"):
		var ev := l4().release_echo(p.substr(5))
		return not ev.has("nothing_happens")
	return false


func _on_drag_started(pos: Vector2) -> void:
	_drag_model = ""
	var hit := raycast(pos)
	if not hit.is_empty():
		_drag_model = str(resolve(hit)["model"])
	super(pos)


func drag_part_started(p: String) -> bool:
	_knob_acc = 0.0
	_drag_kind = ""
	if p in ["IA_keeper", "IA_feed", "IA_handwheel", "IA_post_dial", "IA_post_number"] or p.begins_with("IA_collar_digit_"):
		_drag_kind = p
	return _drag_kind != ""


func drag_part(rel: Vector2) -> void:
	var vertical := _drag_kind.begins_with("IA_collar_digit_")
	var amount := (-rel.y if vertical else rel.x - rel.y * 0.4)
	_knob_acc += amount / (DRAG_PX_PER_STEP * maxf(1.0, DisplayServer.screen_get_scale()))
	var steps := int(_knob_acc)
	if steps == 0:
		return
	_knob_acc -= steps
	_turn(_drag_kind, _drag_model, signi(steps))


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


## Which way a tap on a wheel turns it: the right half clockwise, the left half the other way.
func _side(r: Dictionary, n: Node3D) -> int:
	if n == null:
		return 1
	var a := cam.unproject_position(r.get("pos", n.global_position))
	var b := cam.unproject_position(n.global_position)
	if absf(a.x - b.x) < 2.0:
		return 1
	return 1 if a.x > b.x else -1


## The same for a digit wheel: the upper half rolls it up, the lower half down.
func _side_v(r: Dictionary, n: Node3D) -> int:
	if n == null:
		return 1
	var a := cam.unproject_position(r.get("pos", n.global_position))
	var b := cam.unproject_position(n.global_position)
	return 1 if a.y < b.y else -1


func interact(hs: String, p: String, r: Dictionary) -> void:
	var l := l4()
	if _locked(hs):
		_say("msg.c4_catwalk_locked")
		if hs == "catwalk":
			visuals.lamp_cage_shake()
		AudioManager.sfx("drawer_locked", -6.0, 0.7)
		return
	if p.begins_with("Item_"):
		_take_item(p.substr(5))
		return
	if hs.begins_with("tower_"):
		_interact_tower(int(hs.substr(6)), p)
		return
	if hs.begins_with("gate_"):
		_interact_gate(int(hs.substr(5)), p)
		return
	match hs:
		"chalk_lift", "chalk_panel":
			_say("doc4.chalk")
		"desk":
			_interact_desk(p, r)
		"wheels":
			_turn(p, str(r.get("model", "")), _side(r, part(str(r.get("model", "")), "IA_handwheel")))
		"panel0":
			_interact_panel(p)
		"catwalk":
			_interact_catwalk(p)
		"collar":
			_turn(p, "glass_tower", _side_v(r, part("glass_tower", p)))
		"core":
			_interact_core(p)
		"iris":
			_interact_iris(p)
		"sun_pedestal":
			_interact_sun(p, r)
		"apse":
			if not l.zone_open("apse") and cam.current() == "apse":
				_say("msg.c4_apse_dark")
		"booth_gate":
			if not (l.zone_open("booth")):
				_say("msg.c4_booth_locked")
				AudioManager.sfx("drawer_locked", -6.0, 0.8)
		"gear_box":
			_interact_box(p)
		"watch_gate":
			if not l.zone_open("watch"):
				_say("msg.c4_watch_locked")
				AudioManager.sfx("drawer_locked", -6.0, 0.8)
		"watch", "board":
			if not l.zone_open("watch"):
				_say("msg.c4_watch_locked")
		"locker":
			_interact_locker(p)
		"post_station":
			_interact_post(p, r)
		"lift", "bridge", "stairs", "pier":
			pass


## The pick-ups ("Item_<spot>").
func _take_item(spot: String) -> void:
	var l := l4()
	if spot == "lens":
		l.take_lens()
	elif l.can_take(spot):
		l.take(spot)
	else:
		l.take(spot) # the logic says why (a locker with no parcel is bare)


func _interact_tower(n: int, p: String) -> void:
	var l := l4()
	if p == "IA_key" or p == "Item_key":
		if cam.current() == "hatch_%d" % n:
			l.take("tower_%d" % n)
		else:
			_walk("hatch_%d" % n)
	elif cam.current() != "hatch_%d" % n:
		_walk("hatch_%d" % n)


func _interact_gate(n: int, p: String) -> void:
	var l := l4()
	if p == "IA_gate_%d" % n and not l.state["gates"][n - 1]:
		hud.call("message", tr("msg.c4_gate_locked") % ArrayHallLogic.ROMAN[n - 1])
		AudioManager.sfx("drawer_locked", -6.0, 0.9)


func _interact_catwalk(p: String) -> void:
	var l := l4()
	if p.begins_with("IA_hatch_"):
		var n := int(p.substr(9))
		var open: bool = int(l.state["rings"][n - 1]) == 0 or not l.state["tower_keys"][n - 1]
		if open:
			if cam.current() != "hatch_%d" % n:
				_walk("hatch_%d" % n)
		else:
			l.take("tower_%d" % n) # the key is out of reach: the logic says so
		return
	if cam.current() != "catwalk" and not cam.current().begins_with("hatch_"):
		_walk("catwalk")


func _interact_desk(p: String, r: Dictionary) -> void:
	var l := l4()
	match p:
		"IA_scrub":
			if l.state["reversing"]:
				l.wind_back()
			else:
				l.scrub()
		"IA_master_lever":
			l.lift_master()
		"IA_keeper":
			_turn(p, "keeper_knob", _side(r, part("keeper_knob", "IA_keeper")))
		"IA_chronometer":
			if cam.current() != "chronometer":
				_walk("chronometer")
		_:
			if cam.current() == "desk":
				_walk("chronometer")
			elif cam.current() != "chronometer":
				_walk("desk")


func _interact_panel(p: String) -> void:
	var l := l4()
	if p.begins_with("IA_switch_"):
		l.toggle_switch(int(p.substr(10)) - 1)
	elif p == "IA_main_lever":
		visuals.pull("panel0", "IA_main_lever", 25.0, Vector3.RIGHT, 0.35)
		l.pull_main()
	elif cam.current() != "panel0":
		_walk("panel0")


func _interact_core(p: String) -> void:
	var l := l4()
	if p == "IA_cradle":
		if not l.zone_open("tower"):
			_say("msg.c4_collar_shut")
		elif l.state["lens_seated"]:
			l.take_lens()
		else:
			_say("msg.c4_cradle_refused")
	elif cam.current() != "core" and l.zone_open("floor"):
		_walk("core")


func _interact_iris(p: String) -> void:
	var l := l4()
	if p.begins_with("IA_leaf_"):
		if not l.zone_open("apse"):
			_say("msg.c4_apse_dark")
			return
		l.lift_leaf(int(p.substr(8)) - 1)
	elif cam.current() != "iris":
		_walk("iris")


func _interact_sun(p: String, r: Dictionary) -> void:
	var l := l4()
	if not l.zone_open("apse"):
		_say("msg.c4_apse_dark")
		AudioManager.sfx("drawer_locked", -6.0, 0.8)
		return
	match p:
		"IA_feed":
			_turn(p, "sun_pedestal", _side(r, part("sun_pedestal", "IA_feed")))
		"IA_sun_lever":
			l.toggle_sun_lever()


func _interact_box(p: String) -> void:
	var l := l4()
	if not l.zone_open("booth"):
		_say("msg.c4_booth_locked")
		AudioManager.sfx("drawer_locked", -6.0, 0.8)
		return
	if p.begins_with("IA_knob_"):
		var i := int(p.substr(8)) - 1
		visuals.knob_turn(i)
		l.press_knob(i)
	elif p == "IA_box_log":
		_take_item("box_log")
	elif cam.current() != "gear_box":
		_walk("gear_box")


func _interact_locker(p: String) -> void:
	var l := l4()
	if not l.zone_open("watch"):
		_say("msg.c4_watch_locked")
		return
	if p == "IA_locker_17" or p == "":
		if cam.current() != "locker_17":
			_walk("locker_17")
		else:
			visuals.locker_open = not visuals.locker_open
			AudioManager.sfx("locker_open", -4.0, 0.9)
			visuals.apply_state(true)
			apply_culling(cam.current())
	elif p in ["IA_locker_note", "IA_locker_parcel"]:
		_take_item("locker_" + p.substr(10))


func _interact_post(p: String, r: Dictionary) -> void:
	var l := l4()
	if not l.zone_open("watch"):
		_say("msg.c4_watch_locked")
		return
	match p:
		"IA_post_dial":
			_turn(p, "post_station4", _side(r, part("post_station4", "IA_post_dial")))
		"IA_post_number":
			_turn(p, "post_station4", _side(r, part("post_station4", "IA_post_number")))
		"IA_post_send":
			l.send_post()
		"IA_post_canister":
			if l.state["canister"] != "":
				l.take("post_canister")
			else:
				_say("msg.c4_canister_empty")
		_:
			if cam.current() != "post_station":
				_walk("post_station")


## One click of a wheel, a knob or a dial (a tap on a side, or a step of a drag).
func _turn(p: String, model_id: String, dir: int) -> void:
	var l := l4()
	if p == "IA_handwheel":
		var i := int(model_id.substr(10)) - 1
		if i >= 0 and i < 4:
			l.turn_ring_wheel(i, dir)
	elif p == "IA_keeper":
		l.turn_keeper(dir)
	elif p == "IA_feed":
		l.turn_feed(-dir) # clockwise feeds the rods in: the gap closes
	elif p == "IA_post_dial":
		l.turn_post_dial(dir)
	elif p == "IA_post_number":
		l.turn_post_number(dir)
	elif p.begins_with("IA_collar_digit_"):
		l.turn_collar(int(p.substr(16)) - 1, dir)


# ====================================================================== per-frame
func _process(_delta: float) -> void:
	var fill: OmniLight3D = lights["focus_fill"]
	fill.global_position = cam.global_position + cam.global_basis * Vector3(0.12, 0.18, 0.05)


# ====================================================================== view changes
## Close-ups whose dark metal must be read (lock faces, the digit wheels, the dial) get a stronger camera fill.
const BRIGHT_CLOSEUPS: Array[String] = ["gate_1", "gate_2", "gate_3", "gate_4", "collar", "core", "drawer", "chronometer",
	"desk", "panel0", "gear_box", "booth_gate", "locker_17", "post_station", "sun_pedestal", "iris", "hatch_1", "hatch_2",
	"hatch_3", "hatch_4"]


func view_changed_hook(id: String) -> void:
	apply_culling(id)
	var fill: OmniLight3D = lights["focus_fill"]
	var e := 0.0 if cam.is_root() else (1.5 if id in BRIGHT_CLOSEUPS else 0.8)
	create_tween().tween_property(fill, "light_energy", e, 0.6)
	visuals.view_changed(id)
	_zone_mood(ArrayHallData.zone_of(id))
	if id == "core":
		l4().look("core")


const ZONE_AMBIENT := {"bridge": Color("22323f"), "lift": Color("2d2a26"), "panel": Color("2a2c2a"), "catwalk": Color("22323f"),
	"island": Color("1f3340"), "apse": Color("28302f"), "booth": Color("2c2a24"), "watch": Color("2a2e30")}


## Each zone has its own ambient tint (the Core's cold light on the island, the warm lamps of the booth).
func _zone_mood(zone: String) -> void:
	if zone == "" or zone == _zone:
		return
	_zone = zone
	if env:
		create_tween().tween_property(env, "ambient_light_color", ZONE_AMBIENT.get(zone, Color("22323f")), 1.2)


func _track(kind: String, names: Array) -> String:
	for n: String in names:
		if AudioManager.stream(kind, n) != null:
			return n
	return str(names[-1])


func _music(reversal: bool) -> void:
	var tracks := ["music_array_hall_reversal", "music_array_hall", "music_archive_finale"] if reversal \
		else ["music_array_hall", "music_archive"]
	AudioManager.music(_track("music", tracks), 4.0)


# ====================================================================== events -> feedback
func _on_events(ev: Array[String]) -> void:
	_ring_sound_batch = -1
	if ev.has("power_on"):
		visuals.begin_wake()
	if ev.has("snap_back"):
		visuals.snap_durations(true)
	for e in ev:
		_feedback(e)
	visuals.apply_state(true)
	apply_culling(cam.current())
	hud.call("set_caption", view_caption(cam.current()))
	var seq := ""
	for e in ["power_on", "snap_back", "reversal_begins", "night_undone", "tower_open", "iris_open", "hall_replays",
			"cage_open", "heart_open", "pawl_fitted", "box_open", "parcel_sent"]:
		if ev.has(e):
			seq = e
			break
	match seq:
		"power_on":
			_power_sequence()
		"snap_back":
			_snap_sequence()
		"reversal_begins":
			_reversal_sequence()
		"night_undone":
			_finale_rise()
		"tower_open":
			_tower_sequence(ev)
		"iris_open":
			_iris_sequence()
		"hall_replays":
			_replay_sequence(ev.has("guide_echo:strand"))
		"cage_open":
			_cage_sequence()
		"heart_open":
			_drawer_sequence()
		"pawl_fitted":
			_pawl_sequence()
		"box_open":
			_box_sequence()
		"parcel_sent":
			_parcel_sequence(ev.has("night_undone"))


const MESSAGES := {
	"gate_wrong_key": "msg.c4_gate_wrong_key", "lines_dead": "msg.c4_lines_dead", "hall_powered": "msg.c4_hall_powered",
	"switches_locked": "msg.c4_switches_locked", "box_is_open": "msg.c4_box_is_open", "rods_apart": "msg.c4_rods_apart",
	"arc_shorted": "msg.c4_arc_shorted", "arc_struck": "msg.c4_arc_struck", "arc_out": "msg.c4_arc_out",
	"sun_steady": "msg.c4_sun_steady", "sun_flicker": "msg.c4_sun_flicker", "sun_off": "msg.c4_sun_off",
	"leaf_pinned": "msg.c4_leaf_pinned", "iris_open": "msg.c4_iris_open", "wheels_dead": "msg.c4_wheels_dead",
	"replay_off": "msg.c4_replay_off", "replay_weak": "msg.c4_replay_weak", "chrono_locked": "msg.c4_chrono_locked",
	"tower_out_of_reach": "msg.c4_tower_out_of_reach", "key_wrong_gate": "msg.c4_key_wrong_gate",
	"collar_shut": "msg.c4_collar_shut", "cradle_refused": "msg.c4_cradle_refused", "cradle_full": "msg.c4_cradle_full",
	"lens_taken": "msg.c4_lens_taken", "desk_dead": "msg.c4_desk_dead", "keeper_off": "msg.c4_keeper_off",
	"master_held": "msg.c4_master_held", "held_fast": "msg.c4_held_fast", "station_dead": "msg.c4_station_dead",
	"canister_empty": "msg.c4_canister_empty", "canister_full": "msg.c4_canister_full",
	"canister_loaded": "msg.c4_canister_loaded", "post_no_receiver": "msg.c4_post_no_receiver",
	"post_returned": "msg.c4_post_returned", "locker_bare": "msg.c4_locker_bare", "keeper_on": "msg.c4_keeper_on",
	"nothing_happens": "msg.nothing", "reversal_begins": "msg.c4_reversal_begins",
}


func _feedback(e: String) -> void:
	var l := l4()
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
		"switch":
			AudioManager.sfx("switch_toggle", -2.0, 0.9)
			AudioManager.haptic(15)
		"gate_open":
			_say("msg.c4_gate_open")
			AudioManager.sfx("key_turn")
			AudioManager.sfx("grille_creak", -4.0, 0.9)
		"gear":
			AudioManager.sfx("gear_turn", -8.0, 1.0 + 0.06 * int(arg.get_slice(":", 0)))
		"box_open":
			AudioManager.sfx("box_open", -2.0)
			AudioManager.haptic(60)
		"sun_lever":
			AudioManager.sfx("switch_toggle", -2.0, 0.7)
		"gap":
			AudioManager.sfx("wheel_tick", -6.0, 0.8 + 0.05 * int(arg))
		"arc_shorted":
			AudioManager.sfx("breaker_trip", -6.0, 1.4)
			AudioManager.haptic(80)
			visuals.sparks(Vector3(-12.2, 1.8, 0.0))
			visuals.sun_flare(1.5)
		"arc_struck":
			hud.call("caption", tr("cap4.arc"), 3.0)
			AudioManager.sfx("projector_fire", -2.0, 1.3)
			AudioManager.sfx("power_on", -6.0, 1.5)
			AudioManager.haptic(120)
			visuals.sun_flare(5.0)
		"arc_out":
			AudioManager.sfx("shutter_slam", -10.0, 1.2)
			AudioManager.sfx("relay_click", -4.0, 0.6)
		"sun_steady":
			AudioManager.sfx("reveal", -10.0, 1.4)
		"leaf_up":
			var up := (s["iris_up"] as Array).count(true)
			AudioManager.sfx("vault_bolts", -6.0, 0.9 + 0.08 * up)
			AudioManager.haptic(30)
			if up == 1:
				hud.call("caption", tr("cap4.iris"), 3.0)
		"leaf_pinned":
			AudioManager.sfx("drawer_locked", -5.0, 1.2)
		"ring":
			if _ring_sound_batch < 0:
				_ring_sound_batch = 1
				AudioManager.sfx("vault_wheel", -2.0, 0.55)
				AudioManager.sfx("ring_turn", -8.0, 0.6)
				AudioManager.haptic(35)
				hud.call("caption", tr("cap4.rings"), 2.2)
		"beam":
			var k := int(arg)
			if k > 0:
				hud.call("message", tr("msg.c4_beam") % k)
				if k > _last_beam:
					tones.chime(k - 1)
			else:
				_say("msg.c4_beam_0")
			_last_beam = k
		"replay_on":
			AudioManager.sfx("crystal_record", -6.0, 0.8)
			if l.state["align_done"] and not e == "hall_replays":
				_say("msg.c4_replay_on")
		"replay_off":
			AudioManager.sfx("tape_garble", -12.0, 0.7)
		"replay":
			hud.call("message", tr("msg.c4_minute") % int(arg))
			tones.ratchet(3, false, -8.0)
			AudioManager.sfx("wheel_tick", -4.0, 0.8)
			visuals.core_pulse(0.5)
		"replay_sun_lit":
			visuals.sun_flare(6.0)
			AudioManager.sfx("projector_fire", -10.0, 1.2)
		"replay_rings_set":
			AudioManager.sfx("vault_wheel", -10.0, 0.5)
		"replay_keeper_on":
			tones.chord(-16.0)
		"replay_flash":
			visuals.core_pulse(1.6)
			AudioManager.sfx("projector_fire", -4.0, 0.7)
			AudioManager.haptic(60)
		"key_taken":
			AudioManager.sfx("key_lift", -2.0)
		"collar":
			AudioManager.sfx("collar_click", -3.0, 0.9 + 0.03 * int(arg.get_slice(":", 1)))
		"lens_seated":
			_say("msg.c4_lens_seated")
			AudioManager.sfx("lens_insert", -2.0)
			AudioManager.haptic(40)
		"mark_projected":
			AudioManager.sfx("crystal_record", -8.0, 1.2)
		"pawl_fitted":
			_say("msg.c4_pawl_fitted")
			AudioManager.sfx("item_combine", -2.0)
		"keeper":
			tones.beat(int(arg), l.note_target())
			AudioManager.sfx("collar_click", -10.0, 0.7 + 0.05 * int(arg))
		"beat":
			_say("msg.c4_beat_far" if int(arg) >= 4 else "msg.c4_beat_near")
		"wound":
			hud.call("message", tr("msg.c4_wound") % int(arg))
			tones.ratchet(5, true, -6.0)
			AudioManager.sfx("wheel_tick", -3.0, 0.6)
			AudioManager.haptic(50)
			visuals.core_pulse(1.0)
		"master_up":
			pass
		"snap_back":
			_say("msg.c4_snap_back")
		"post_dial", "post_number":
			AudioManager.sfx("wheel_tick", -4.0, 1.0 + 0.04 * int(arg))
		"canister_emptied":
			AudioManager.sfx("canister_thump", -8.0, 1.3)
		"parcel_sent":
			_say("msg.c4_parcel_sent")
			visuals.canister_send(false)
			AudioManager.sfx("tube_whoosh", -2.0, 0.9)
		"night_undone":
			_say("msg.c4_night_undone")
		"echo_released":
			AudioManager.sfx("reveal", 0.0, 1.2)
			hud.call("caption", tr("echo4." + arg), 4.5)
			hud.call("message", tr("msg.c4_echo_count") % (s["echoes"] as Array).size())
			visuals.release_echo(arg)
		"all_echoes":
			GameState.unlock_achievement("collect_ch4")
		"guide_echo":
			pass
		"forty_second_turns":
			hud.call("caption", tr("cap4.forty_second"), 5.0)
			AudioManager.sfx("reveal", -6.0, 1.5)
			visuals.forty_second_turns()
		"choice":
			visuals.choose_fx(arg)
		"solved":
			AudioManager.sfx("puzzle_solved", -5.0)
		"chapter_complete":
			hud.call("show_chapter_complete")
	if e == "post_returned" or e == "post_no_receiver":
		visuals.canister_send(true)
		AudioManager.sfx("tube_whoosh", -4.0, 0.8)
		get_tree().create_timer(0.9).timeout.connect(func() -> void: AudioManager.sfx("canister_thump", -4.0, 0.7))


# ====================================================================== sequences
func _busy(on: bool) -> void:
	_cinematic = on
	hud.call("set_busy", on)


## How long the HUD's intro waits for the descent before handing over control.
func opening_seconds() -> float:
	return INTRO_SECONDS


## Called by the HUD intro: the freight lift sinks past the last numbered floor, caged lamps pass upward, the hum grows; on
## arrival the key turns in the gate and it folds open on the dark hall, with the Core the only light.
func play_opening_camera() -> void:
	var bay: Array[Node3D] = []
	for n in ["bay_floor", "bay_walls", "bay_frame"]:
		var p := part("shell_lift4", n)
		if p:
			bay.append(p)
			p.visible = false
	visuals.gate_open = false
	visuals.intro_key = true
	visuals.apply_state(false)
	cam.go("lift_in", true)
	var pass_lamp := lights.get("lift_pass") as Light3D
	AudioManager.ambience("amb_power_hum", true, -14.0, 1.0)
	AudioManager.sfx("projector_charge", -10.0, 0.5)
	if pass_lamp:
		pass_lamp.position = Vector3(3.2, -3.0, 16.4)
		pass_lamp.light_energy = 2.4
		var tw := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		tw.tween_property(pass_lamp, "position", Vector3(3.2, 11.0, 16.4), 6.2)
		for k in 5:
			var lt := create_tween()
			lt.tween_interval(0.5 + 1.15 * k)
			lt.tween_property(pass_lamp, "light_energy", 0.4, 0.25)
			lt.tween_property(pass_lamp, "light_energy", 2.6, 0.25)
		await tw.finished
		pass_lamp.light_energy = 0.0
	else:
		await get_tree().create_timer(6.2).timeout
	for p in bay:
		p.visible = true
	sync_colliders()
	AudioManager.sfx("canister_thump", 0.0, 0.6)
	AudioManager.haptic(140)
	await get_tree().create_timer(0.7).timeout
	AudioManager.sfx("key_turn")
	visuals.intro_key = false
	visuals.gate_open = true
	visuals.apply_state(true)
	AudioManager.sfx("locker_open", -2.0, 0.7)
	await get_tree().create_timer(1.3).timeout
	cam.go("lift")
	visuals.core_pulse(0.6)


## Power: the relays clack under the bridge, work lamps wake ring by ring, high above the oculus shutter grinds open
## and a disc of light appears.
func _power_sequence() -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.5).timeout
	for k in 5:
		AudioManager.sfx("relay_click", -4.0, 0.9 + 0.06 * k)
		await get_tree().create_timer(0.16).timeout
	cam.go("bridge_up")
	hud.call("caption", tr("cap4.power"), 6.0)
	AudioManager.sfx("power_on", -2.0, 0.8)
	AudioManager.haptic(180)
	tones.hum(true, -24.0, not l4().state["trust_strand"])
	visuals.wake_work_lamps()
	await get_tree().create_timer(3.8).timeout
	AudioManager.sfx("vault_door_open", -4.0, 0.5)
	await get_tree().create_timer(3.6).timeout
	cam.go(back if back != "" and cam.views.has(back) else "bridge")
	await get_tree().create_timer(0.8).timeout
	_busy(false)


func _box_sequence() -> void:
	_busy(true)
	await get_tree().create_timer(1.8).timeout
	hud.call("caption", tr("msg.c4_box_open"), 4.0)
	await get_tree().create_timer(1.2).timeout
	_busy(false)


## The iris opens: a beam the width of a door crosses the hall to the outer ring, and stops there.
func _iris_sequence() -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.8).timeout
	cam.go("bridge")
	AudioManager.sfx("projector_fire", -3.0, 0.8)
	AudioManager.haptic(100)
	visuals.sun_flare(6.0)
	await get_tree().create_timer(3.4).timeout
	cam.go(back if cam.views.has(back) else "apse")
	await get_tree().create_timer(0.6).timeout
	_busy(false)


## The hall replays for the first time: the beam folds into the Core and forty-one figures of light stand on the floor,
## frozen at 03:17.
func _replay_sequence(strand_guide: bool) -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.8).timeout
	cam.go("bridge")
	visuals.core_pulse(1.4)
	AudioManager.sfx("crystal_record", -2.0, 0.6)
	AudioManager.haptic(120)
	tones.chord(-12.0)
	hud.call("caption", tr("cap4.replay"), 4.5)
	await get_tree().create_timer(4.6).timeout
	if strand_guide:
		cam.go("desk")
		hud.call("caption", tr("cap4.strand_desk"), 5.0)
		await get_tree().create_timer(4.4).timeout
	cam.go(back if cam.views.has(back) else "bridge")
	await get_tree().create_timer(0.8).timeout
	_busy(false)


func _cage_sequence() -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.6).timeout
	cam.go("island")
	AudioManager.sfx("vault_door_open", -4.0, 0.7)
	await get_tree().create_timer(3.0).timeout
	cam.go(back if cam.views.has(back) else "island")
	await get_tree().create_timer(0.5).timeout
	_busy(false)


## The collar opens: the glass panels sink into the floor and the Core stands bare. Trust Leyla: the forty-second light turns
## toward you. Leave path: Leyla steps out of the light and seats the lens you left for her.
func _tower_sequence(ev: Array[String]) -> void:
	_busy(true)
	await get_tree().create_timer(0.8).timeout
	cam.go("core")
	AudioManager.sfx("vault_door_open", -6.0, 0.6)
	AudioManager.haptic(140)
	visuals.core_pulse(1.0)
	await get_tree().create_timer(3.4).timeout
	if ev.has("leyla_echo_lens"):
		hud.call("caption", tr("cap4.leyla_lens"), 7.0)
		await visuals.leyla_seats_lens(5.0)
		AudioManager.sfx("lens_insert", -2.0)
		await _drawer_sequence_inner()
	await get_tree().create_timer(0.4).timeout
	_busy(false)


func _drawer_sequence() -> void:
	if _cinematic:
		return
	_busy(true)
	await _drawer_sequence_inner()
	_busy(false)


## The Core's light passes through the lens and the recorded mark falls on the drawer's face: it slides open.
func _drawer_sequence_inner() -> void:
	var back := cam.current()
	cam.go("drawer")
	visuals.core_pulse(1.0)
	AudioManager.sfx("crystal_record", -4.0, 1.1)
	await get_tree().create_timer(1.8).timeout
	AudioManager.sfx("drawer_open", -2.0, 0.8)
	await get_tree().create_timer(2.2).timeout
	cam.go("core" if back == "" or not cam.views.has(back) else back)
	await get_tree().create_timer(0.6).timeout


func _pawl_sequence() -> void:
	_busy(true)
	await get_tree().create_timer(1.6).timeout
	AudioManager.sfx("collar_click", -2.0, 0.6)
	await get_tree().create_timer(0.6).timeout
	_busy(false)


## The parcel leaves the canister: if the Night is already undone (never) nothing more; the sound goes up the tube.
func _parcel_sequence(_undone: bool) -> void:
	await get_tree().create_timer(0.1).timeout


## The reversal begins: the lever lifts and the frozen hall begins to move backwards.
func _reversal_sequence() -> void:
	_busy(true)
	var back := cam.current()
	_music(true)
	await get_tree().create_timer(0.9).timeout
	cam.go("bridge")
	AudioManager.sfx("vault_door_open", -3.0, 0.45)
	AudioManager.haptic(200)
	tones.swell(6.0, 98.0, -11.0)
	visuals.core_pulse(1.8)
	hud.call("caption", tr("msg.c4_reversal_begins"), 5.0)
	await get_tree().create_timer(4.4).timeout
	cam.go(back if cam.views.has(back) and not back.begins_with("lift") else "desk")
	await get_tree().create_timer(0.6).timeout
	_busy(false)


## Snap-back: every lever slams down, the rings grind back, the Sun relights, the figures freeze.
func _snap_sequence() -> void:
	_busy(true)
	var back := cam.current()
	await get_tree().create_timer(0.2).timeout
	cam.go("bridge")
	AudioManager.sfx("door_slam", 2.0, 0.6)
	AudioManager.sfx("shutter_slam", 0.0, 0.7)
	AudioManager.sfx("vault_wheel", -2.0, 0.45)
	AudioManager.haptic(220)
	hud.call("caption", tr("cap4.snap"), 3.0)
	visuals.core_pulse(2.0)
	visuals.sun_flare(6.0)
	_music(false)
	await get_tree().create_timer(2.4).timeout
	AudioManager.sfx("projector_fire", -4.0, 1.0)
	await get_tree().create_timer(1.0).timeout
	visuals.snap_durations(false)
	cam.go(back if cam.views.has(back) else "desk")
	await get_tree().create_timer(0.6).timeout
	_busy(false)


## The climax: the Night undone. The hall goes dark and forty-one lights rise from the Core through the oculus. The roll
## board's lamps go out one by one in the watch room. Then the choice.
func _finale_rise() -> void:
	_ending = true
	logic.select_item("")
	_busy(true)
	var ending := l4().ending_id()
	tones.hum(false)
	tones.beat(0, 0)
	AudioManager.music(_track("music", ["music_array_hall_end", "music_archive_finale"]), 3.0)
	hud.call("caption", tr("cap4.rise"), 4.0)
	await get_tree().create_timer(1.2).timeout
	visuals.start_rise(ending)
	cam.go("rise_core")
	tones.swell(8.0, 98.0, -9.0)
	AudioManager.haptic(250)
	for k in 8:
		tones.rise_note(k, -14.0)
		await get_tree().create_timer(0.55).timeout
	cam.go("rise_up")
	for k in 6:
		tones.rise_note(8 + k, -15.0)
		await get_tree().create_timer(0.85).timeout
	cam.go("watch")
	visuals.rise_lamps(0.1)
	await get_tree().create_timer(4.4).timeout
	if ending == "true":
		cam.go("rise_up")
		visuals.finale_phase()
		await get_tree().create_timer(9.5).timeout
	else:
		cam.go("finale")
		visuals.finale_phase()
		if ending == "keeper":
			tones.chord(-9.0)
		await get_tree().create_timer(7.0).timeout
	_busy(false)
	hud.call("show_choice")
