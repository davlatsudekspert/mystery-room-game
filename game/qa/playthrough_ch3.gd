extends Node
## Runtime QA for Chapter 3: loads the real Underground scene and plays the chapter through simulated taps on the
## 3D parts (raycast -> hotspot -> logic), like a player. The UndergroundSolver decides each next action on a copy of
## the game (qa/ch3_plan.gd records what it does); the playthrough walks there (zone changes by tapping passages,
## blast doors and tunnels) and taps the part. A step falls back to a direct logic call only when the tap did not
## work; every fallback is reported with what the tap hit instead, and fallbacks for models that are not built yet
## are listed per puzzle.
## After the first wing it also quits and continues: the scene is rebuilt from the save (GameState.save_now /
## continue_saved, the main menu's Continue) and must show the same state at the wing's hall.
## Run: xvfb-run -a godot --path game res://qa/playthrough_ch3.tscn -- --out=<dir> [--key=strand|leyla]
##        [--lens=take|leave] [--seed=N] [--secret] [--choice=strand|leyla] [--lang=ru] [--quick]
##        [--reload-every=N] (also quit and Continue after every N-th solver step, mid-wing: the rebuilt scene must show
##        the same state and the same tappable parts in all three zones)
##        [--logic-sweep] [--sweep-seeds=N] (no scene: random take / return / use actions interleaved with solver steps,
##        a save round trip after every step, and a completion check from each saved state, for both key paths)
## (through the render queue: tools/qa_run.sh --log=<file> -- res://qa/playthrough_ch3.tscn -- …)
## A quick logic-flow run without screenshots: godot --headless --path game res://qa/playthrough_ch3.tscn -- …
## Exit code 0 = chapter completed with no failed step and no fallback.

const Plan := preload("res://qa/ch3_plan.gd")
const SCENE := "res://src/rooms/underground/underground.tscn"
const PHONE_MM_H := 68.6 ## the 19.5:9 test phone (phone61 in qa/tap_map.gd): 1080 px at 400 dpi
const MIN_TAP_MM := 9.0 ## the smallest tap target a thumb can hit reliably
## The views measured for the per-view budget (docs/models/ch3.md §13.3), plus the zone roots.
const PERF_VIEWS: Array[String] = ["choir", "choir_s", "port_b", "desk", "rack", "gallery", "gallery_w", "glass_floor",
	"console", "nursery", "nursery_w", "autoclave", "seed_library", "prisms", "camp", "shutter", "lift_w", "lift_e"]
## The first action of each puzzle: its evidence views are photographed first.
const EVIDENCE := {
	"take:desk_hook": ["switch_room", "interlock_plate", "desk"],
	"turn_case_wheel": ["ecg_lamp", "meter_case"],
	"tap_tube": ["rack_close", "bench"],
	"pull_lever": ["port_a", "port_b", "port_c"],
	"open_seed_drawer": ["growth_log", "seed_library"],
	"turn_peg": ["chart", "cam_drum"],
	"turn_prism": ["seal", "prisms"],
	"tap_crystal": ["recorder", "shutter"],
	"turn_drum": ["glass_floor", "drum"],
	"turn_freq": ["strand_plate", "scope", "memorial"],
}

var out_dir := "/tmp/ch3_playthrough"
var room: Node3D
var logic: UndergroundLogic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0
var fallback_missing := 0
var missing_by_puzzle: Dictionary = {} # puzzle -> [labels]
var key_path := "strand"
var lens_path := "leave"
var secret := false
var choice := "leyla"
var quick := false
var _events: Array[String] = []
var _evidence_done: Dictionary = {}
var _echoes_done := false
var _perf_done := false
var _continue_done := false
var reload_every := 0
var sweep := false
var sweep_seeds := 12
var _steps_done := 0
var _reload_checks := 0
var _reload_failed := 0
var _sig_parts := 0
var _sizes: Dictionary = {} # "view model/part" -> Vector2: the tapped part's visible size in mm at phone61 scale


func _ready() -> void:
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		elif a.begins_with("--key="):
			key_path = a.substr(6)
		elif a.begins_with("--lens="):
			lens_path = a.substr(7)
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--choice="):
			choice = a.substr(9)
		elif a == "--secret":
			secret = true
		elif a == "--quick":
			quick = true
		elif a.begins_with("--reload-every="):
			reload_every = int(a.substr(15))
		elif a == "--logic-sweep":
			sweep = true
		elif a.begins_with("--sweep-seeds="):
			sweep_seeds = int(a.substr(14))
	DirAccess.make_dir_recursive_absolute(out_dir)
	if sweep:
		_logic_sweep()
		return
	if DisplayServer.get_name() == "headless":
		get_window().size = Vector2i(1920, 1080) # headless windows are square: frame the views like a phone
	# one save file per process: runs in parallel (the render queue runs two, quick runs more) must not load each other's
	SaveSystem.save_path = "user://qa_ch3_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_ch3_profile_%d.json" % OS.get_process_id()
	GameState.profile = {"choices": {"ch2_key": key_path + "_key", "ch1_lens": lens_path + "_lens",
		"ch1_shards": 5 if secret else 0, "ch2_echoes": 3 if secret else 0}}
	GameState.start_new("ch3")
	logic = GameState.logic
	GameState.events.connect(func(ev: Array[String]) -> void: _events.append_array(ev))
	var t0 := Time.get_ticks_msec()
	_build_room()
	await get_tree().process_frame
	await get_tree().process_frame
	_log("scene load+build: %d ms (software renderer; phones differ), viewport %s" % [Time.get_ticks_msec() - t0,
		str(get_viewport().get_visible_rect().size)])
	_log("path: Ch2 key %s, Ch1 lens %s, secret %s, seed %d, choice %s" % [key_path, lens_path, secret,
		int(logic.state["seed"]), choice])
	var miss: Array = room.get("missing_models")
	_log("models not built yet: %s" % (", ".join(miss) if not miss.is_empty() else "none"))
	_log("this game's answers: choir %s, startup %s, heart %s, seed drawer %d, curve %s, prism %s, melody %s, rings %s, freq %s" % [
		str(logic.choir_target()), str(logic.startup()), str(logic.case_code()), logic.seed_right(),
		str(logic.pegs_target()), str(logic.prism_target()), str(logic.melody()), str(logic.drum_target()),
		str(logic.freq_target())])
	await _settle(1.2)
	await run()


# ====================================================================== logic sweep (no scene)
const SoftlockTest := preload("res://tests/test_underground_no_softlock.gd")


## --logic-sweep: the solver's own player actions (one at a time, from qa/ch3_plan.gd) interleaved with random
## take / return / use actions, for both key paths and both lens paths with a per-game seed. After every action the
## save round trip must reproduce the state exactly and the invariants must hold; from every 4th state a copy made
## through the save must still be completable. Exit 0 = nothing failed.
func _logic_sweep() -> void:
	var helper := SoftlockTest.new()
	var rng := RandomNumberGenerator.new()
	var runs := 0
	var actions := 0
	var saves := 0
	var solves := 0
	var failures: Array[String] = []
	for sd in sweep_seeds:
		for pi in 4:
			var path := "strand" if pi % 2 == 0 else "leyla"
			var l := UndergroundLogic.new()
			l.setup_from_profile({"ch2_key": path + "_key", "ch1_lens": ("take" if pi < 2 else "leave") + "_lens",
				"ch1_shards": 5 if sd % 3 == 0 else 2, "ch2_echoes": 3})
			l.apply_seed(0 if sd == 0 else 1000 + sd * 17 + pi)
			rng.seed = 31000 + sd * 4 + pi
			runs += 1
			var tag := "%s/%s/seed %d" % [path, "take" if pi < 2 else "leave", int(l.state["seed"])]
			var guard := 0
			while not l.is_complete() and guard < 400 and failures.size() < 8:
				guard += 1
				var plan := Plan.new()
				plan.from_dict(l.to_dict())
				UndergroundSolver.step(plan, path)
				var calls: Array = plan.calls
				var take_n := rng.randi_range(1, maxi(1, calls.size()))
				for i in mini(take_n, calls.size()):
					if str(calls[i][0]) == "choose_ending":
						continue
					l.callv(str(calls[i][0]), calls[i][1])
					actions += 1
					var bad := _sweep_check(l, helper)
					if bad == "":
						saves += 1
						if actions % 4 == 0:
							var copy := UndergroundLogic.new()
							copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
							solves += 1
							if not UndergroundSolver.solve(copy, path):
								bad = "not completable from here; goal %s" % copy.hint_goal()
					if bad != "":
						failures.append("%s: %s after %s%s" % [tag, bad, str(calls[i][0]), str(calls[i][1])])
						break
				if failures.size() > 0 and failures[-1].begins_with(tag):
					break
				if rng.randi_range(0, 2) == 0: # an odd order: random takes, returns and uses, then the solver carries on
					for _k in rng.randi_range(1, 10):
						helper.random_action(l, rng)
						actions += 1
						var bad2 := _sweep_check(l, helper)
						if bad2 != "":
							failures.append("%s: %s after a random action" % [tag, bad2])
							break
					if failures.size() > 0 and failures[-1].begins_with(tag):
						break
			if not l.is_complete() and not (failures.size() > 0 and failures[-1].begins_with(tag)):
				failures.append("%s: not complete after %d rounds; goal %s" % [tag, guard, l.hint_goal()])
	_log("logic sweep: %d games, %d actions, %d save round trips, %d completion checks from saved states" % [
		runs, actions, saves, solves])
	for f in failures:
		_log("✗ " + f)
	var f2 := FileAccess.open(out_dir + "/playthrough_ch3_sweep_report.txt", FileAccess.WRITE)
	f2.store_string("\n".join(report) + "\n")
	var qa_exit := 0 if failures.is_empty() else 1
	print("QA_DONE exit=%d" % qa_exit)
	get_tree().quit(qa_exit)


## The invariants of the softlock test plus the save round trip; "" = fine.
func _sweep_check(l: UndergroundLogic, helper: Variant) -> String:
	var bad: String = helper.invariants(l)
	if bad != "":
		return "invariant: " + bad
	var copy := UndergroundLogic.new()
	copy.from_dict(JSON.parse_string(JSON.stringify(l.to_dict())))
	if JSON.stringify(copy.to_dict()) != JSON.stringify(l.to_dict()):
		return "save round trip differs"
	return ""


# ====================================================================== helpers
func _build_room() -> void:
	room = (load(SCENE) as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)


func _log(line: String) -> void:
	report.append(line)
	print(line)


func _settle(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		await get_tree().process_frame
		t += get_process_delta_time()


func _perf(label: String) -> void:
	await _settle(0.5)
	if DisplayServer.get_name() != "headless":
		await _settle(2.0) # the zone's probe captures over several frames on the software renderer
		await RenderingServer.frame_post_draw
	var rs := RenderingServer
	_log("perf[%s]: draw calls %d, primitives %d, objects %d (groups %s)" % [label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME), str(room.get("_drawn"))])


func shot(name: String) -> void:
	await _settle(0.3)
	if DisplayServer.get_name() == "headless": # logic-flow runs without a renderer: no pixels to save
		return
	await RenderingServer.frame_post_draw
	shot_n += 1
	var p := "%s/%02d_%s.png" % [out_dir, shot_n, name]
	get_viewport().get_texture().get_image().save_png(p)
	_log("shot %s" % p.get_file())


func cam() -> RoomCamera:
	return room.get("cam")


func busy() -> bool:
	return bool((room.get("hud") as Node).get("_busy")) or bool(room.get("_cinematic"))


## Cinematics lock input, and a tap during a camera move is dropped (RoomBase._on_tap): wait for both.
func wait_idle(limit: float = 60.0) -> void:
	var t := 0.0
	await _settle(0.2)
	while (busy() or cam().transitioning) and t < limit:
		await _settle(0.25)
		t += 0.25


func wait_cam() -> void:
	await _settle(0.3)
	var t := 0.0
	while cam().transitioning and t < 5.0:
		await _settle(0.1)
		t += 0.1
	await _settle(0.3)


func view(id: String) -> void:
	if id == "seed_drawer":
		room.call("prepare_view", id)
	if cam().current() != id:
		cam().go(id)
	await wait_cam() # also when already there: the camera may still be gliding back from a deeper view


## Where a player taps the eyepiece rim in a port view: the rim spans 0.97 to 3.3 half-heights from the centre
## (UndergroundRoom._place_eyepiece), so the point depends on the viewport's aspect (headless runs are square).
func _rim_point() -> Vector2:
	var vs := get_viewport().get_visible_rect().size
	var c := vs * 0.5
	var half_h := vs.y * 0.5
	var aspect := vs.x / vs.y
	if aspect >= 1.0:
		return Vector2(c.x - half_h * (0.97 + minf(aspect, 3.3)) * 0.5, c.y)
	return Vector2(c.x, c.y - half_h * 0.985)


func node_of(model: String, part: String) -> Node3D:
	var root: Node3D = (room.get("models") as Dictionary).get(model)
	if root == null:
		return null
	return root if part == "" else ModelUtil.find(root, part)


func _rect(n: Node3D, own_only: bool) -> Rect2:
	var meshes := ModelUtil.find_meshes(n)
	if own_only and n is MeshInstance3D:
		meshes = [n as MeshInstance3D]
	var r := Rect2()
	var first := true
	for mi in meshes:
		if not mi.is_visible_in_tree():
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				if own_only:
					return Rect2()
				continue
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _tap_point(model: String, part: String) -> Vector2:
	var n := node_of(model, part)
	if n == null:
		return Vector2(-1, -1)
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var vs := get_viewport().get_visible_rect().size
	var sp := r.get_center()
	if sp.x >= 0 and sp.y >= 0 and sp.x <= vs.x and sp.y <= vs.y and _resolves_to(sp, part):
		return sp
	# the middle of a part's bounds can be covered or empty (a lattice gate, a tunnel): a player taps where the part
	# is actually visible, so look for such a point, nearest the middle first
	var best := Vector2(-1, -1)
	var best_d := INF
	for gy in 9:
		for gx in 9:
			var p := r.position + r.size * Vector2(0.05 + 0.9 * gx / 8.0, 0.05 + 0.9 * gy / 8.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(r.get_center())
			if d < best_d and _resolves_to(p, part):
				best = p
				best_d = d
	return best


func _resolves_to(sp: Vector2, part: String) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return false
	var got := str(room.call("resolve", h)["part"])
	return got == part or (part.begins_with("Item_") and got == part)


func tap(model: String, part: String) -> bool:
	var sp := _tap_point(model, part)
	if sp.x < 0:
		return false
	_note_size(model, part)
	room.call("_on_tap", sp)
	await _settle(0.4)
	return true


## The part's visible size as a phone61 player sees it (1080 px = 68.6 mm tall): a tap target under 9 mm is a trip hazard.
func _note_size(model: String, part: String) -> void:
	var n := node_of(model, part)
	if n == null:
		return
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	var mm := r.size * (PHONE_MM_H / get_viewport().get_visible_rect().size.y)
	var key := "%s %s/%s" % [cam().current(), model, part]
	if not _sizes.has(key) or maxf(mm.x, mm.y) > maxf((_sizes[key] as Vector2).x, (_sizes[key] as Vector2).y):
		_sizes[key] = mm


func _hit(model: String, part: String) -> String:
	if not (room.get("models") as Dictionary).has(model):
		return "model missing"
	if node_of(model, part) == null:
		return "part missing"
	var sp := _tap_point(model, part)
	if sp.x < 0:
		return "not visible / off-screen"
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return "nothing"
	var r: Dictionary = room.call("resolve", h)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


## The logic's whole state and inventory, to compare what a tap did with what the solver wanted.
static func _snap(l: RoomLogic) -> String:
	return var_to_str(l.state) + "|" + var_to_str(l.inventory)


func _expected(m: String, a: Array) -> String:
	var copy := UndergroundLogic.new()
	copy.from_dict(logic.to_dict())
	copy.callv(m, a)
	return _snap(copy)


# ====================================================================== where each action is done
## The solver's action -> [view, model, part, item to select first, puzzle].
func _target(m: String, a: Array) -> Array:
	var s := logic.state
	var sealed := logic.sealed_door()
	match m:
		"take":
			match str(a[0]):
				"desk_hook":
					return ["desk", "control_desk", "Item_desk_hook", "", "interlock"]
				"office_lamp":
					return ["ecg_lamp", "office_desk", "Item_office_lamp", "", "heart"]
				"office_letters":
					return ["office", "office_desk", "Item_office_letters", "", "heart"]
				"meter_case":
					return ["meter_case", "meter_case", "Item_meter_case", "", "heart"]
				"seed_drawer":
					return ["seed_drawer", "seed_library", "Item_seed_%d" % int(s["seed_drawer"]), "", "seed"]
				"autoclave":
					return ["autoclave", "autoclave", "Item_chamber", "", "grow"]
		"turn_isolator":
			return ["cabinet_%d" % int(a[0]), "cabinet_%d" % int(a[0]), "IA_isolator", "", "interlock"]
		"take_cabinet_key":
			return ["cabinet_%d" % int(a[0]), "cabinet_%d" % int(a[0]), "IA_lock" if a[1] == "in" else "IA_key_window", "", "interlock"]
		"toggle_office":
			return ["office_door", "strand_office", "IA_office_door", "", "interlock"]
		"take_office_key":
			return ["office_door", "strand_office", "IA_office_lock", "", "restore"]
		"turn_case_wheel":
			return ["meter_case", "meter_case", "IA_case_dial_%d" % int(a[0]), "", "heart"]
		"tap_tube":
			# a place that holds a tube is tapped on the tube (it hangs in front of the slot's hook), an empty one on
			# the slot or bench place itself; both reach the same place (UndergroundRoom._rack_place)
			var pos := int(a[0])
			var r := int(s["tubes"][pos])
			if pos < UndergroundLogic.SLOTS:
				return ["rack", "choir_rack", "IA_slot_%d" % pos if r == 0 else "IA_tube_%d" % r, "", "choir"]
			return ["bench", "tube_bench", "IA_bench_%d" % (pos - UndergroundLogic.SLOTS) if r == 0 else "IA_tube_%d" % r, "", "choir"]
		"strike_hammer":
			return ["rack", "choir_rack", "IA_hammer", "", "choir"]
		"pull_lever":
			return ["desk", "control_desk", "IA_lever_%d" % int(a[0]), "", "startup"]
		"turn_knob":
			return ["desk", "control_desk", "IA_master_knob", "", "startup"]
		"open_seed_drawer":
			return ["seed_library", "seed_library", "IA_seed_drawer_%d" % int(a[0]), "", "seed"]
		"toggle_autoclave":
			return ["autoclave", "autoclave", "IA_ac_door", "", "grow"]
		"turn_peg":
			return ["cam_drum", "autoclave", "IA_peg_%d" % int(a[0]), "", "grow"]
		"pull_start_lever":
			return ["autoclave", "autoclave", "IA_start_lever", "", "grow"]
		"remelt":
			return ["autoclave", "autoclave", "IA_remelt", "", "grow"]
		"turn_prism":
			return ["prisms", "prism_bench", "IA_%s_%s" % [a[0], "left" if int(a[1]) < 0 else "right"], "", "prisms"]
		"tap_crystal":
			return ["shutter", "crystal_shutter", "IA_tcrystal_%d" % int(logic.frame_sizes()[int(a[0])]), "", "melody"]
		"turn_drum":
			return ["drum_" + sealed, "door_" + sealed, "IA_drum_%d" % int(a[0]), "", "rings"]
		"pull_drum_handle":
			return ["drum_" + sealed, "door_" + sealed, "IA_drum_handle", "", "rings"]
		"turn_freq":
			return ["console", "gallery_console", "IA_knob_" + str(a[0]), "", "resonance"]
		"take_from_cradle":
			return ["cradle", "gallery_console", "IA_cradle", "", "resonance"]
		"take_from_socket_42":
			return ["socket_42", "memorial_wall", "IA_socket_42", "", "secret"]
		"use_item_on":
			var item := str(a[0])
			var target := str(a[1])
			if target.begins_with("cabinet_"):
				var n := int(target.substr(8))
				var part := "IA_lock" if item == UndergroundLogic.CABINET_TAKES[n] else "IA_key_window"
				return [target, target, part, item, "interlock"]
			match target:
				"office_door":
					return ["office_door", "strand_office", "IA_office_lock", item, "interlock"]
				"desk_hook":
					return ["desk", "control_desk", "IA_desk_hook", item, "restore"]
				"seed_library":
					return ["seed_library", "seed_library", "IA_seed_drawer_%d" % maxi(0, int(s["seed_from"])), item, "seed"]
				"autoclave":
					return ["autoclave", "autoclave", "IA_ac_door", item, "grow"]
				"cradle":
					return ["console", "gallery_console", "IA_cradle", item, "resonance"]
				"socket_42":
					return ["socket_42", "memorial_wall", "IA_socket_42", item, "secret"]
	return []


# ====================================================================== walking between zones
## Ways between zones a player takes by tapping: [from zone, to zone, from view, model, part, arrival view, open?]
func _edges() -> Array:
	var s := logic.state
	var west: bool = s["entry"] == "choir"
	# back to the lift: the hall root views look away from the passage (a player turns with free-look, which the
	# QA does not do), so the way back starts from a view that frames the passage mouth
	return [
		["lift", "choir", "lift_w", "shell_lift", "IA_passage_w", "choir", west],
		["choir", "lift", "desk", "shell_lift", "IA_passage_w", "lift_w", west],
		["lift", "nursery", "lift_e", "shell_lift", "IA_passage_e", "nursery", not west],
		["nursery", "lift", "nursery_w", "shell_lift", "IA_passage_e", "lift_e", not west],
		["choir", "gallery", "blast_west_hall", "door_west", "IA_door_tunnel", "gallery", s["door_west_open"]],
		["gallery", "choir", "blast_west", "door_west", "IA_door_tunnel", "choir", s["door_west_open"]],
		["gallery", "nursery", "blast_east", "door_east", "IA_door_tunnel", "nursery", s["door_east_open"]],
		["nursery", "gallery", "nursery_w", "door_east", "IA_door_tunnel", "gallery_w", s["door_east_open"]],
		["gallery", "nursery", "gallery_w", "shell_gallery", "IA_tunnel_shutter", "camp", s["shutter_open"]],
		["nursery", "gallery", "shutter", "shell_gallery", "IA_tunnel_shutter", "gallery_w", s["shutter_open"]],
	]


func _zone() -> String:
	return UndergroundData.zone_of(cam().current())


## The first way to take from `here` towards `zone` (breadth-first over the open ways).
func _first_hop(here: String, zone: String) -> Array:
	var open: Array = _edges().filter(func(e: Array) -> bool: return bool(e[6]))
	var first := {here: []}
	var queue: Array[String] = [here]
	while not queue.is_empty():
		var z: String = queue.pop_front()
		for e: Array in open:
			if e[0] == z and not first.has(e[1]):
				first[e[1]] = e if z == here else first[z]
				queue.append(e[1])
	return first.get(zone, [])


func _walk_to(zone: String) -> void:
	for _hop in 4:
		var here := _zone()
		if here == zone:
			return
		var edge := _first_hop(here, zone)
		if edge.is_empty():
			break
		await view(edge[2])
		var ok := await tap(edge[3], edge[4])
		await _settle(1.0)
		if ok and _zone() == edge[1]:
			taps_ok += 1
			_log("  walk %s -> %s (%s)" % [here, edge[1], edge[4]])
		else:
			var why := _hit(edge[3], edge[4])
			taps_fallback += 1
			_count_missing(why, "walk", "walk %s -> %s" % [here, edge[1]], str(edge[3]))
			_log("  fallback: walk %s -> %s (%s/%s, view %s, hit %s)" % [here, edge[1], edge[3], edge[4], cam().current(), why])
			cam().go(edge[5])
			await _settle(0.9)
	if _zone() != zone:
		cam().go(UndergroundData.ZONE_ROOT.get(zone, "choir"))
		await _settle(0.9)


## Walk to the view's zone through the open ways, then go to the view (a player taps the object there).
func goto(id: String) -> void:
	var zone := UndergroundData.zone_of(id)
	if zone != "" and zone != _zone():
		await _walk_to(zone)
	await view(id)


## True when a failed tap is only because the model's GLB is not built yet (the room lists it in missing_models); a
## part that is missing from a built model is a wiring bug and is reported as a fallback.
func _unbuilt(why: String, model: String) -> bool:
	if why not in ["model missing", "part missing"]:
		return false
	var glb := model
	if UndergroundData.LAYOUT.has(model):
		glb = str(UndergroundData.LAYOUT[model][0])
	return glb in (room.get("missing_models") as Array)


## Counts a fallback caused by an unbuilt model; returns true then (nothing more to log).
func _count_missing(why: String, puzzle: String, label: String, model: String = "") -> bool:
	if not _unbuilt(why, model):
		return false
	fallback_missing += 1
	var l: Array = missing_by_puzzle.get(puzzle, [])
	l.append(label)
	missing_by_puzzle[puzzle] = l
	return true


# ====================================================================== the chapter
func run() -> void:
	var s := logic.state
	var lift := "lift_w" if s["entry"] == "choir" else "lift_e"
	# a new game begins in the lift (capture mode skips the intro and the room opens at the hall: step back in)
	cam().go(lift, true)
	await _settle(0.6)
	await shot("lift")
	if not quick:
		await _perf(lift)
	# out of the lift into the entry hall, by tapping the passage
	await _walk_to("choir" if s["entry"] == "choir" else "nursery")
	await shot("entry_hall")
	var guard := 0
	while not logic.is_complete() and guard < 2500:
		guard += 1
		if s["array_awake"]:
			await _finale()
			break
		var plan := _plan()
		if plan.is_empty():
			_log("✗ the solver has no move (state stuck)")
			break
		for c: Array in plan:
			if str(c[0]) == "choose_ending":
				break
			await _before(c)
			var ok := await _do(str(c[0]), c[1])
			await _milestones()
			if not ok or s["array_awake"]:
				break
			_steps_done += 1
			if not _continue_done and UndergroundSolver.wing_done(logic, s["entry"]):
				_continue_done = true
				await _continue_check()
				s = logic.state
			elif reload_every > 0 and _steps_done % reload_every == 0:
				await _continue_check("mid-wing after step %d (%s)" % [_steps_done, str(c[0])])
				s = logic.state
	if not logic.is_complete() and not s["array_awake"]:
		_log("✗ chapter not completed (stopped after %d planning rounds)" % guard)
	_finish()


## A player quits here and taps Continue: the save is written, the scene freed and rebuilt from the save. The
## rebuilt scene must hold the same state, start at the wing's hall (not in the lift) and keep the gate open.
## `label` != "" is the periodic mid-wing check (--reload-every): it also compares every tappable part of the three
## zones before and after, and only reports a failure.
func _continue_check(label: String = "") -> void:
	await wait_idle()
	var before := _snap(logic)
	var sig_before := ""
	if label != "":
		sig_before = await _stable_sig()
	var saved := GameState.save_now()
	room.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
	var loaded := saved and GameState.continue_saved()
	if not loaded:
		_log("✗ continue: the save could not be written or read back")
		GameState.logic = logic
	logic = GameState.logic
	_build_room()
	await get_tree().process_frame
	await get_tree().process_frame
	await _settle(1.2)
	await wait_idle()
	var start := cam().current()
	var same := _snap(logic) == before
	var gate: bool = (room.get("visuals") as Node).get("gate_open")
	var ok := loaded and same and start == str(room.call("start_view")) and gate and not bool(room.call("_fresh_start"))
	if label == "":
		_log(("✓ " if ok else "✗ ") + "continue: scene rebuilt from the save (state %s, opens at %s, gate %s)" % [
			"kept" if same else "DIFFERS", start, "open" if gate else "SHUT"])
		await shot("continue_" + start)
		return
	_reload_checks += 1
	var diff := ""
	if ok:
		var sig_after := await _stable_sig()
		if sig_after != sig_before:
			ok = false
			diff = _sig_diff(sig_before, sig_after)
	if not ok:
		_reload_failed += 1
		_log("✗ continue %s: state %s, opens at %s, gate %s%s" % [label, "kept" if same else "DIFFERS", start,
			"open" if gate else "SHUT", diff])


## The signature once nothing moves any more (a blast door slides for several seconds after the handle is pulled).
func _stable_sig() -> String:
	var sig := await _scene_sig()
	for _i in 12:
		await _settle(0.6)
		var again := await _scene_sig()
		if again == sig:
			return sig
		sig = again
	return sig


## Every tappable part the player can see (own collider on, visible in the tree), with its position and orientation,
## in each zone's root view (zone culling is per view, so the same views are used before and after a reload).
func _scene_sig() -> String:
	var here := cam().current()
	var lines: Array[String] = []
	for v: String in ["choir", "gallery", "nursery"]:
		cam().go(v, true)
		await _settle(0.35)
		for n in room.find_children("*", "StaticBody3D", true, false):
			var b := n as StaticBody3D
			if b.collision_layer == 0 or not b.is_visible_in_tree() or str(b.get_meta("part", "")) == "":
				continue
			var o := b.global_position
			var x := b.global_transform.basis.x
			lines.append("%s|%s|%d,%d,%d|%d,%d,%d" % [v, str(b.get_meta("part")), roundi(o.x * 100.0), roundi(o.y * 100.0),
				roundi(o.z * 100.0), roundi(x.x * 10.0), roundi(x.y * 10.0), roundi(x.z * 10.0)])
	if here != "":
		cam().go(here, true)
		await _settle(0.2)
	lines.sort()
	_sig_parts = lines.size()
	return "\n".join(lines)


func _sig_diff(a: String, b: String) -> String:
	var la := a.split("\n")
	var lb := b.split("\n")
	var only_a: Array[String] = []
	var only_b: Array[String] = []
	for l in la:
		if not lb.has(l):
			only_a.append(l)
	for l in lb:
		if not la.has(l):
			only_b.append(l)
	return " | parts changed by the reload: %d before-only %s, %d after-only %s" % [only_a.size(), str(only_a.slice(0, 3)),
		only_b.size(), str(only_b.slice(0, 3))]


func _plan() -> Array:
	var copy: Variant = Plan.new()
	copy.from_dict(logic.to_dict())
	UndergroundSolver.step(copy, choice)
	return copy.get("calls")


## Evidence shots before a puzzle's first action, the kept echoes and the budget views before the resonance.
func _before(c: Array) -> void:
	var m := str(c[0])
	var key := m if m != "take" else "take:" + str(c[1][0])
	if (m == "turn_freq" or (m == "use_item_on" and str(c[1][1]) == "cradle")) and not _echoes_done:
		_echoes_done = true
		await _release_echoes()
		if not quick and not _perf_done:
			_perf_done = true
			for v in PERF_VIEWS:
				await goto(v)
				await _perf(v)
	if EVIDENCE.has(key) and not _evidence_done.has(key):
		_evidence_done[key] = true
		if quick:
			return
		for v: String in EVIDENCE[key]:
			var vid := v if v != "drum" else "drum_" + logic.sealed_door()
			await goto(vid)
			if vid.begins_with("port_"):
				for k in 3: # the 1979 loop: a few moments of it
					await _settle(2.3)
					await shot("evidence_%s_%d" % [vid, k])
			else:
				await shot("evidence_" + vid)


func _do(m: String, a: Array) -> bool:
	var t := _target(m, a)
	if t.is_empty():
		_log("  ✗ no tap known for %s%s" % [m, str(a)])
		logic.callv(m, a)
		taps_fallback += 1
		return true
	var label := "%s%s" % [m, str(a)]
	await goto(t[0])
	await wait_idle()
	if str(t[3]) != "":
		logic.select_item(t[3]) # a tap on the inventory slot
		await _settle(0.15)
	var before := _snap(logic)
	var expect := _expected(m, a)
	await tap(t[1], t[2])
	await _settle(0.25)
	await wait_idle()
	var now := _snap(logic)
	if now == expect:
		taps_ok += 1
		return true
	if now == before:
		var why := _hit(t[1], t[2])
		var held: Dictionary = (room.get("visuals") as UndergroundVisuals)._held
		var info := "chamber %s, closed %s, held %s" % [str(logic.state.get("chamber")), str(logic.state.get("ac_closed")), str(held.get("chamber"))]
		logic.callv(m, a)
		taps_fallback += 1
		if not _count_missing(why, t[4], label, str(t[1])):
			_log("  fallback: %s (%s/%s, view %s, hit %s, %s)" % [label, t[1], t[2], cam().current(), why, info])
		await wait_idle()
		return true
	taps_fallback += 1
	_log("  ✗ the tap did something else: %s (%s/%s, view %s, hit %s)" % [label, t[1], t[2], cam().current(), _hit(t[1], t[2])])
	return false


func _milestones() -> void:
	for e in _events:
		if e.begins_with("solved:"):
			_log("✓ solved %s" % e.substr(7))
			if not quick:
				await shot("solved_" + e.substr(7))
		elif e in ["gallery_awake", "array_awake", "secret_echo", "hall_started", "seal_open", "shutter_open"] \
				or e.begins_with("blast_door_open") or e.begins_with("echo_released") or e.begins_with("leyla_echo"):
			_log("  event %s" % e)
	_events.clear()


## The four kept echoes: on the take path while holding a crystal in each echo's zone, on the leave path through
## the crystal ports' memory views (both work on the take path too).
func _release_echoes() -> void:
	var places := {"welder": ["choir", "port_b"], "tech_a": ["nursery", "port_a"], "tech_b": ["nursery", "port_a"],
		"strand_rail": ["gallery", "port_c"]}
	for id: String in UndergroundData.ECHOES:
		if (logic.state["echoes"] as Array).has(id):
			continue
		var p: Array = places[id]
		var crystal := ""
		for c in UndergroundLogic.CRYSTALS:
			if logic.has_item(c):
				crystal = c
		if lens_path == "take" and crystal != "":
			await goto(p[0])
			logic.select_item(crystal)
			await _settle(0.6)
		else:
			await goto(p[1])
			# in a port view the camera sits at the lens: the port's rim frames the view (the room's eyepiece)
			var rim := _rim_point()
			var ok := _resolves_to(rim, "IA_port_ring")
			if ok:
				room.call("_on_tap", rim)
			await _settle(1.0)
			if not ok or not cam().current().ends_with("_mem"):
				var hr: Dictionary = room.call("raycast", rim)
				var why := "nothing" if hr.is_empty() else str(room.call("resolve", hr)["part"])
				if not _count_missing(why, "echoes", "port ring " + p[1]):
					_log("  fallback: port ring %s (view %s, hit %s)" % [p[1], cam().current(), why])
				taps_fallback += 1
				cam().go(p[1] + "_mem")
				await _settle(1.0)
		await shot("echo_" + id)
		var n := node_of("echo_" + id, "")
		var before := (logic.state["echoes"] as Array).size()
		if n:
			room.call("_on_tap", _echo_point(n))
			await _settle(0.5)
		if (logic.state["echoes"] as Array).size() > before:
			taps_ok += 1
			_log("✓ echo %s released" % id)
		else:
			taps_fallback += 1
			_log("  fallback: echo %s (view %s, %s)" % [id, cam().current(), "echo model missing" if n == null else "tap missed"])
			logic.release_echo(id, cam().current().ends_with("_mem"))
		logic.select_item("")
		await wait_idle()
		if cam().current().ends_with("_mem"):
			cam().back()
			await wait_cam()


func _echo_point(n: Node3D) -> Vector2:
	var p := n.global_position + Vector3(0, 1.0, 0)
	return cam().unproject_position(p) if not cam().is_position_behind(p) else Vector2(-100, -100)


func _finale() -> void:
	await wait_idle(40.0)
	var hud: Node = room.get("hud")
	var w := 0
	while w < 160 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
	await shot("finale_choice")
	hud.call("_close_overlay")
	if not quick:
		await _perf("finale")
	await shot("finale_echoes")
	logic.choose_ending(choice) # the choice overlay's button
	await _settle(2.5)
	await shot("chapter_complete")
	_log(("✓ " if logic.is_complete() else "✗ ") + "finale: trust %s -> chapter complete" % choice)


func _finish() -> void:
	_log("taps through the 3D scene: %d, logic fallbacks: %d (%d of them for models not built yet)" % [taps_ok,
		taps_fallback, fallback_missing])
	if reload_every > 0:
		_log("%s reload checks (every %d steps, %d tappable parts compared each time): %d, failed: %d" % [
			"✓" if _reload_failed == 0 else "✗", reload_every, _sig_parts, _reload_checks, _reload_failed])
	var small: Array[String] = []
	for k: String in _sizes:
		var mm: Vector2 = _sizes[k]
		if maxf(mm.x, mm.y) < MIN_TAP_MM:
			small.append("%s %.1f x %.1f mm" % [k, mm.x, mm.y])
	small.sort()
	_log("tap targets (visible part, phone61 scale): %d, under %.0f mm on both sides: %d" % [_sizes.size(), MIN_TAP_MM, small.size()])
	for k in small:
		_log("  small: " + k)
	for p: String in missing_by_puzzle:
		var l: Array = missing_by_puzzle[p]
		_log("  waiting for models: %s — %d actions (e.g. %s)" % [p, l.size(), l[0]])
	var f := FileAccess.open(out_dir + "/playthrough_ch3_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SaveSystem.profile_path))
	var ok: bool = logic.state["complete"] and not report.any(func(l: String) -> bool: return l.begins_with("✗"))
	var qa_exit: int = 0 if ok and taps_fallback == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
