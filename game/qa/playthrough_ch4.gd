extends Node
## Runtime QA for Chapter 4: loads the real Array Hall scene and plays the chapter through simulated taps on the 3D parts
## (raycast -> hotspot -> logic), like a player. The ArrayHallSolver decides each next action on a copy of the game (the
## Plan class below records what it does); the playthrough walks there (zone changes by tapping the hall's landmarks) and
## taps the part. A step falls back to a direct logic call only when the tap did not work; every fallback is reported with
## what the tap hit instead, and fallbacks for models that are not built yet are listed per puzzle.
## It also quits and continues twice: after the cage opens and in the middle of the reversal. The scene is rebuilt from the
## save (GameState.save_now / continue_saved, the main menu's Continue) and must show the same state and the same tappable
## parts.
## Run: xvfb-run -a godot --path game res://qa/playthrough_ch4.tscn -- --out=<dir> [--key=strand|leyla]
##        [--lens=take|leave] [--trust=strand|leyla] [--secret] [--seed=N] [--choice=take_lens|leave_lens] [--lang=ru]
##        [--quick] [--reload-every=N] [--intro] [--no-continue] [--speed=6] (game time runs N times faster: quick runs)
##        [--screen=phone61|tablet10] (render as that phone; needs QA_XVFB_ARGS="-screen 0 2400x1200x24")
## (through the render queue: tools/qa_run.sh --log=<file> -- res://qa/playthrough_ch4.tscn -- …)
## A quick logic-flow run without screenshots: godot --headless --path game res://qa/playthrough_ch4.tscn -- … --quick
## Exit code 0 = chapter completed with no failed step and no fallback (an unbuilt echo figure is reported, not a fallback).

const SCENE := "res://src/rooms/array_hall/array_hall.tscn"
const PHONE_MM_H := 68.6 ## the 19.5:9 test phone (phone61 in qa/tap_map.gd): 1080 px at 400 dpi
const MIN_TAP_MM := 9.0 ## the smallest tap target a thumb can hit reliably
## The views measured for the per-view budget (docs/models/ch4.md §11.2).
const PERF_VIEWS: Array[String] = ["lift", "bridge", "desk", "chronometer", "handwheels", "panel0", "catwalk", "hatch_1",
	"island", "gate_1", "collar", "core", "drawer", "apse", "sun_pedestal", "iris", "booth", "booth_gate", "gear_box",
	"watch", "locker_17", "post_station"]
## The first action of each puzzle: its evidence views are photographed first.
const EVIDENCE := {
	"toggle_switch": ["lift", "panel0"],
	"press_knob": ["booth", "gear_box"],
	"toggle_sun_lever": ["apse", "sun_pedestal"],
	"lift_leaf": ["iris"],
	"turn_ring_wheel": ["gear_box", "handwheels", "bridge"],
	"take:tower_1": ["catwalk", "hatch_1"],
	"turn_collar": ["chronometer", "island", "collar"],
	"take:heart_pawl": ["drawer", "chronometer"],
	"turn_keeper": ["desk"],
}
## Where a player taps to reach each root view from the bridge: [model, hotspot part]. (Panel 0 hangs below the lift bay's
## pier wall: bridge -> stairs -> lift -> pier -> panel0.)
const LANDMARK := {
	"lift": ["bridge", "stairs"],
	"catwalk": ["catwalk", "catwalk"],
	"apse": ["sun_lamp", "apse"],
	"booth": ["booth", "booth"],
	"watch": ["watch_room", "watch"],
}
## The root view each view belongs to.
const ROOT_OF := {
	"lift": "lift", "panel0": "lift", "lift_chalk": "lift", "bridge": "bridge", "desk": "bridge", "chronometer": "bridge",
	"handwheels": "bridge", "catwalk": "catwalk", "hatch_1": "catwalk", "hatch_2": "catwalk", "hatch_3": "catwalk",
	"hatch_4": "catwalk", "island": "island", "gate_1": "island", "gate_2": "island", "gate_3": "island",
	"gate_4": "island", "collar": "island", "core": "island", "drawer": "island", "apse": "apse", "sun_pedestal": "apse",
	"iris": "apse", "booth": "booth", "booth_gate": "booth", "gear_box": "booth", "watch": "watch", "locker_17": "watch",
	"post_station": "watch",
}


## The Chapter 4 logic that records every player action the solver makes ([method, args]), so one solver step on a copy of
## the game says what the player should do next.
class Plan extends ArrayHallLogic:
	var calls: Array = []

	func _rec(m: String, args: Array) -> void:
		calls.append([m, args])

	func toggle_switch(i: int) -> Array[String]:
		_rec("toggle_switch", [i])
		return super(i)

	func pull_main() -> Array[String]:
		_rec("pull_main", [])
		return super()

	func press_knob(i: int) -> Array[String]:
		_rec("press_knob", [i])
		return super(i)

	func take(spot: String) -> Array[String]:
		_rec("take", [spot])
		return super(spot)

	func toggle_sun_lever() -> Array[String]:
		_rec("toggle_sun_lever", [])
		return super()

	func turn_feed(delta: int) -> Array[String]:
		_rec("turn_feed", [delta])
		return super(delta)

	func lift_leaf(i: int) -> Array[String]:
		_rec("lift_leaf", [i])
		return super(i)

	func turn_ring_wheel(i: int, delta: int) -> Array[String]:
		_rec("turn_ring_wheel", [i, delta])
		return super(i, delta)

	func scrub() -> Array[String]:
		_rec("scrub", [])
		return super()

	func turn_collar(i: int, delta: int = 1) -> Array[String]:
		_rec("turn_collar", [i, delta])
		return super(i, delta)

	func take_lens() -> Array[String]:
		_rec("take_lens", [])
		return super()

	func turn_keeper(delta: int) -> Array[String]:
		_rec("turn_keeper", [delta])
		return super(delta)

	func lift_master() -> Array[String]:
		_rec("lift_master", [])
		return super()

	func wind_back() -> Array[String]:
		_rec("wind_back", [])
		return super()

	func turn_post_dial(delta: int) -> Array[String]:
		_rec("turn_post_dial", [delta])
		return super(delta)

	func turn_post_number(delta: int) -> Array[String]:
		_rec("turn_post_number", [delta])
		return super(delta)

	func send_post() -> Array[String]:
		_rec("send_post", [])
		return super()

	func use_item_on(item: String, target: String) -> Array[String]:
		_rec("use_item_on", [item, target])
		return super(item, target)

	func choose_ending(option: String) -> Array[String]:
		_rec("choose_ending", [option])
		return super(option)


var out_dir := "/tmp/ch4_playthrough"
var room: Node3D
var logic: ArrayHallLogic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0
var fallback_missing := 0
var missing_by_puzzle: Dictionary = {} # puzzle -> [labels]
var key_path := "leyla"
var lens_path := "leave"
var trust := "leyla"
var secret := false
var choice := "leave_lens"
var quick := false
var intro_check := false
var do_continue := true
var _events: Array[String] = []
var _evidence_done: Dictionary = {}
var _echoes_done := false
var _perf_done := false
var _continue_done := false
var _continue_mid_done := false
var reload_every := 0
var _steps_done := 0
var _reload_checks := 0
var _reload_failed := 0
var _sig_parts := 0
var _sizes: Dictionary = {} # "view model/part" -> Vector2: the tapped part's visible size in mm at phone61 scale
var _walks := 0
var _solved: Array[String] = []
var _early_done := false
var screen_spec := ""
var walk_only := false


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
		elif a.begins_with("--trust="):
			trust = a.substr(8)
		elif a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7))
		elif a.begins_with("--choice="):
			choice = a.substr(9)
		elif a == "--secret":
			secret = true
		elif a == "--quick":
			quick = true
		elif a == "--intro":
			intro_check = true
		elif a == "--no-continue":
			do_continue = false
		elif a == "--walk":
			walk_only = true
		elif a.begins_with("--reload-every="):
			reload_every = int(a.substr(15))
		elif a.begins_with("--screen="):
			screen_spec = a.substr(9)
		elif a.begins_with("--speed="):
			Engine.time_scale = clampf(float(a.substr(8)), 0.5, 12.0) # timers, tweens and cinematics run faster
	DirAccess.make_dir_recursive_absolute(out_dir)
	if screen_spec != "":
		await _apply_screen(screen_spec)
	if DisplayServer.get_name() == "headless":
		get_window().size = Vector2i(1920, 1080) # headless windows are square: frame the views like a phone
	# one save file per process: runs in parallel (the render queue runs two, quick runs more) must not load each other's
	SaveSystem.save_path = "user://qa_ch4_save_%d.json" % OS.get_process_id()
	SaveSystem.profile_path = "user://qa_ch4_profile_%d.json" % OS.get_process_id()
	GameState.profile = {"choices": {"ch2_key": key_path + "_key", "ch1_lens": lens_path + "_lens",
		"ch3_trust": trust, "ch3_true_ending": secret, "ch1_shards": 5 if secret else 0, "ch2_echoes": 3 if secret else 0,
		"ch3_echoes": 4 if secret else 0}}
	GameState.start_new("ch4")
	logic = GameState.logic
	GameState.events.connect(func(ev: Array[String]) -> void: _events.append_array(ev))
	var t0 := Time.get_ticks_msec()
	_build_room()
	await get_tree().process_frame
	await get_tree().process_frame
	_log("scene load+build: %d ms (software renderer; phones differ), viewport %s" % [Time.get_ticks_msec() - t0,
		str(get_viewport().get_visible_rect().size)])
	_log("path: Ch2 key %s, Ch1 lens %s, Ch3 trust %s, secret %s, seed %d, choice %s -> expected ending %s" % [key_path,
		lens_path, trust, secret, int(logic.state["seed"]), choice, _expected_ending()])
	var miss: Array = room.get("missing_models")
	_log("models not built yet: %s" % (", ".join(miss) if not miss.is_empty() else "none"))
	var placeholders: Array = (room.get("visuals") as Node).get("_placeholder_figures")
	_log("echo figures standing in (group I model not built or not used yet): %s" % (", ".join(placeholders) if not placeholders.is_empty() else "none"))
	_log("this game's answers: panel %s, box %s, gap %d, iris %s, rings %s -> %s, night %s, note %d" % [
		str(logic.panel_solution()), str(logic.state["v_box"]), logic.gap_target(), str(logic.iris_order()),
		str(logic.state["v_rings"]), str(logic.align_target()), str(logic.night()), logic.note_target()])
	await _settle(1.2)
	await run()


## Renders as the named phone (the same table as qa/tap_map.gd): the window takes its aspect, Settings.emulate gives the HUD
## its dpi and safe area. Needs an X server big enough (QA_XVFB_ARGS="-screen 0 2400x1200x24").
const SCREENS := {
	"phone61": {"size": Vector2i(2340, 1080), "dpi": 400.0, "insets": [120, 0, 0, 0]},
	"tablet10": {"size": Vector2i(2048, 1536), "dpi": 264.0, "insets": [0, 0, 0, 0]},
}


func _apply_screen(spec: String) -> void:
	if not SCREENS.has(spec):
		return
	var d: Dictionary = SCREENS[spec]
	var size: Vector2i = d["size"]
	var insets: Array = d["insets"]
	var win := get_window()
	win.size = size
	await _settle(0.3)
	if win.size != size:
		var k := minf(float(win.size.x) / size.x, float(win.size.y) / size.y)
		win.size = Vector2i(int(size.x * k), int(size.y * k))
		await _settle(0.3)
	var safe := Rect2i(int(insets[0]), int(insets[1]), size.x - int(insets[0]) - int(insets[2]), size.y - int(insets[1]) - int(insets[3]))
	Settings.set("emulate", {"size": size, "dpi": float(d["dpi"]), "safe": safe})
	print("screen %s: window %s, canvas %s" % [spec, str(win.size), str(get_viewport().get_visible_rect().size)])


func _expected_ending() -> String:
	if secret:
		return "true"
	return "keeper" if trust == "strand" else "dawn"


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
func wait_idle(limit: float = 90.0) -> void:
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
	if cam().current() != id:
		cam().go(id)
	await wait_cam() # also when already there: the camera may still be gliding back from a deeper view


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


## A point where a player taps the part: the middle of its bounds if that resolves to it, else the nearest visible spot.
## `bias` (0..1 each way) is where in the part's bounds a tap turns it one way (right half, upper half).
func _tap_point(model: String, part: String, bias: Vector2 = Vector2(0.5, 0.5)) -> Vector2:
	var n := node_of(model, part)
	if n == null:
		return Vector2(-1, -1)
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var vs := get_viewport().get_visible_rect().size
	var want := r.position + r.size * bias
	var sp := want
	if sp.x >= 0 and sp.y >= 0 and sp.x <= vs.x and sp.y <= vs.y and _resolves_to(sp, part):
		return sp
	var best := Vector2(-1, -1)
	var best_d := INF
	for gy in 11:
		for gx in 11:
			var p := r.position + r.size * Vector2(0.04 + 0.92 * gx / 10.0, 0.04 + 0.92 * gy / 10.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(want)
			if d < best_d and _resolves_to(p, part):
				best = p
				best_d = d
	return best


func _resolves_to(sp: Vector2, part: String) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return false
	var got := str(room.call("resolve", h)["part"])
	return got == part


func tap(model: String, part: String, bias: Vector2 = Vector2(0.5, 0.5)) -> bool:
	var sp := _tap_point(model, part, bias)
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
		if OS.get_environment("CH4_DBG") != "":
			var n := node_of(model, part)
			var r := _rect(n, part != "" and not part.begins_with("Item_"))
			var seen := {}
			for gy in 11:
				for gx in 11:
					var p := r.position + r.size * Vector2(gx / 10.0, gy / 10.0)
					var h: Dictionary = room.call("raycast", p)
					var k := "(none)"
					if not h.is_empty():
						var rr: Dictionary = room.call("resolve", h)
						k = "%s/%s/%s" % [rr["model"], rr["hotspot"], rr["part"]]
						var col := h.get("collider") as Node
						if col:
							k += " <%s/%s at %s>" % [col.get_parent().name, col.name, str(h.get("position", Vector3.ZERO))]
					seen[k] = int(seen.get(k, 0)) + 1
			_log("  DBG %s/%s rect %s visible %s present %s: %s" % [model, part, str(r), str(n.is_visible_in_tree()), str(n.get_meta("present", "-")), str(seen)])
		return "not visible / off-screen"
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return "nothing"
	var r: Dictionary = room.call("resolve", h)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


## The logic's whole state and inventory, to compare what a tap did with what the solver wanted.
static func _snap(l: RoomLogic) -> String:
	var st: Dictionary = l.state.duplicate()
	st.erase("looked_core") # the camera arriving at the Core sets it by itself (ArrayHallLogic.look)
	return var_to_str(st) + "|" + var_to_str(l.inventory)


func _expected(m: String, a: Array) -> String:
	var copy := ArrayHallLogic.new()
	copy.from_dict(logic.to_dict())
	copy.callv(m, a)
	return _snap(copy)


# ====================================================================== where each action is done
## The solver's action -> [view, model, part, item to select first, puzzle, tap bias].
func _target(m: String, a: Array) -> Array:
	var s := logic.state
	match m:
		"toggle_switch":
			return ["panel0", "panel0", "IA_switch_%d" % (int(a[0]) + 1), "", "power"]
		"pull_main":
			return ["panel0", "panel0", "IA_main_lever", "", "power"]
		"press_knob":
			return ["gear_box", "strand_box4", "IA_knob_%d" % (int(a[0]) + 1), "", "box"]
		"take":
			var spot := str(a[0])
			if spot.begins_with("tower_"):
				return ["hatch_%s" % spot.substr(6), "mirror_tower_%s" % spot.substr(6), "IA_key", "", "keys"]
			match spot:
				"box_log":
					return ["gear_box", "strand_box4", "Item_box_log", "", "box"]
				"heart_watch", "heart_letter", "heart_pawl":
					return ["drawer", "heart_drawer", "Item_" + spot, "", "pawl"]
				"locker_note", "locker_parcel":
					return ["locker_17", "lockers4", "Item_" + spot, "", "secret"]
				"post_canister":
					return ["post_station", "post_station4", "IA_post_canister", "", "secret"]
		"toggle_sun_lever":
			return ["sun_pedestal", "sun_pedestal", "IA_sun_lever", "", "sun"]
		"turn_feed":
			return ["sun_pedestal", "sun_pedestal", "IA_feed", "", "sun", Vector2(0.85 if int(a[0]) < 0 else 0.15, 0.5)]
		"lift_leaf":
			return ["iris", "sun_iris", "IA_leaf_%d" % (int(a[0]) + 1), "", "iris"]
		"turn_ring_wheel":
			return ["handwheels", "handwheel_%d" % (int(a[0]) + 1), "IA_handwheel", "", "align",
				Vector2(0.85 if int(a[1]) > 0 else 0.15, 0.5)]
		"scrub", "wind_back":
			return ["chronometer", "master_desk", "IA_scrub", "", "reversal" if s["reversing"] else "collar"]
		"turn_collar":
			return ["collar", "glass_tower", "IA_collar_digit_%d" % (int(a[0]) + 1), "", "collar",
				Vector2(0.5, 0.15 if int(a[1]) > 0 else 0.85)]
		"take_lens":
			return ["core", "cradle", "Item_lens", "", "lens"]
		"turn_keeper":
			return ["desk", "keeper_knob", "IA_keeper", "", "note", Vector2(0.85 if int(a[0]) > 0 else 0.15, 0.5)]
		"lift_master":
			return ["desk", "master_lever", "IA_master_lever", "", "reversal"]
		"turn_post_dial":
			return ["post_station", "post_station4", "IA_post_dial", "", "secret", Vector2(0.85 if int(a[0]) > 0 else 0.15, 0.5)]
		"turn_post_number":
			return ["post_station", "post_station4", "IA_post_number", "", "secret", Vector2(0.85 if int(a[0]) > 0 else 0.15, 0.5)]
		"send_post":
			return ["post_station", "post_station4", "IA_post_send", "", "secret"]
		"use_item_on":
			var item := str(a[0])
			var target := str(a[1])
			if target.begins_with("gate_"):
				return ["gate_" + target.substr(5), "cage", "IA_gate_" + target.substr(5), item, "cage"]
			match target:
				"cradle":
					return ["core", "cradle", "IA_cradle", item, "lens"]
				"chronometer":
					return ["chronometer", "master_desk", "IA_chronometer", item, "pawl"]
				"post_canister":
					return ["post_station", "post_station4", "IA_post_canister", item, "secret"]
				"booth_gate":
					return ["booth_gate", "booth", "IA_booth_gate", item, "early"]
				"watch_gate":
					return ["watch", "watch_room", "IA_watch_gate", item, "early"]
	return []


# ====================================================================== walking between zones
func _zone_root() -> String:
	return str(ROOT_OF.get(cam().current(), "bridge"))


## Taps a landmark of the hall: the first visible spot of the model whose hotspot is `hotspot`. A root view allows free
## look, so a player who does not see the landmark turns the view (to the left, to the right, behind) until it is there.
func _tap_landmark(model: String, hotspot: String) -> bool:
	if not (room.get("models") as Dictionary).has(model):
		return false
	var yaws: Array[float] = [0.0]
	if cam().is_root():
		yaws = [0.0, -45.0, 45.0, -90.0, 90.0, 180.0]
	for yaw in yaws:
		if cam().is_root():
			cam().yaw = yaw
			cam().call("_apply_free_look")
			await _settle(0.35)
		var best := _landmark_point(model, hotspot)
		if best.x >= 0:
			room.call("_on_tap", best)
			await _settle(0.5)
			return true
		if OS.get_environment("CH4_DBG") != "":
			_dbg_hist("%s/%s" % [model, hotspot])
	if cam().is_root():
		cam().yaw = 0.0
		cam().call("_apply_free_look")
	return false


## The spot nearest the screen's middle where a tap answers with `hotspot` of the model `model` (a scan of the whole
## screen, clear of the HUD's controls and the edges).
func _landmark_point(model: String, hotspot: String) -> Vector2:
	var vs := get_viewport().get_visible_rect().size
	var best := Vector2(-1, -1)
	var best_d := INF
	var centre := vs * 0.5
	var y := 150.0
	while y < vs.y - 170.0:
		var x := 220.0
		while x < vs.x - 220.0:
			var p := Vector2(x, y)
			var d := p.distance_to(centre)
			if d < best_d:
				var h: Dictionary = room.call("raycast", p)
				if not h.is_empty():
					var rr: Dictionary = room.call("resolve", h)
					if str(rr["hotspot"]) == hotspot and str(rr["model"]) == model:
						best = p
						best_d = d
			x += 30.0
		y += 30.0
	return best


## QA debugging (CH4_DBG=1): what a 21x21 grid of taps resolves to in the current view.
func _dbg_hist(tag: String) -> void:
	var vs := get_viewport().get_visible_rect().size
	var seen := {}
	for gy in 21:
		for gx in 21:
			var p2 := Vector2(vs.x * gx / 20.0, vs.y * gy / 20.0)
			var h2: Dictionary = room.call("raycast", p2)
			var k := "(none)"
			if not h2.is_empty():
				var r2: Dictionary = room.call("resolve", h2)
				k = "%s/%s" % [r2["model"], r2["hotspot"]]
			seen[k] = int(seen.get(k, 0)) + 1
	_log("  DBG %s view %s yaw %.0f pitch %.0f: %s" % [tag, cam().current(), cam().yaw, cam().pitch, str(seen)])


## Pressing Back, as the HUD's button does.
func _back() -> void:
	room.call("go_back")
	await wait_cam()


## Walk to the root view of `id`'s zone the way a player does: Back to the bridge, then tap the zone's landmark.
func _walk_to_root(root: String) -> void:
	for _hop in 3:
		if _zone_root() == root:
			return
		var guard := 0
		while cam().current() != "bridge" and guard < 5:
			guard += 1
			await _back()
		if root == "bridge":
			return
		await wait_idle()
		if root == "island":
			# the island is reached from the catwalk: the glass tower stands at its end
			await _walk_to_root("catwalk")
			var ok2 := await _tap_landmark("glass_tower", "island")
			await _settle(0.8)
			if ok2 and _zone_root() == "island":
				taps_ok += 1
				_walks += 1
			else:
				taps_fallback += 1
				_log("  fallback: walk catwalk -> island (no spot of glass_tower answers as «island» in the catwalk view)")
				cam().go("island")
				await _settle(0.9)
			return
		var lm: Array = LANDMARK[root]
		var ok := false
		if lm[1] == "stairs":
			ok = await _tap_stairs()
		else:
			ok = await _tap_landmark(lm[0], lm[1])
		await _settle(0.8)
		if ok and _zone_root() == root:
			taps_ok += 1
			_walks += 1
		else:
			var why := "no spot of %s answers as «%s» in the bridge view" % [lm[0], lm[1]]
			if not (room.get("models") as Dictionary).has(lm[0]):
				why = "model missing"
			taps_fallback += 1
			if not _count_missing(why, "walk", "walk to %s" % root, lm[0]):
				_log("  fallback: walk bridge -> %s (tap on %s/%s: %s)" % [root, lm[0], lm[1], why])
			cam().go(root)
			await _settle(0.9)
	if _zone_root() != root:
		cam().go(root)
		await _settle(0.9)


## The stairs down to the lift bay: the tap area on the stair flights at the bridge's back corners. A player turns round
## (free look) and looks down at them, to the left and to the right.
func _tap_stairs() -> bool:
	var c := cam()
	var vs := get_viewport().get_visible_rect().size
	var ok := false
	for look: Vector2 in [Vector2(90, -30), Vector2(-90, -30), Vector2(130, -35), Vector2(-130, -35), Vector2(60, -35), Vector2(-60, -35), Vector2(180, -35)]:
		c.yaw = look.x
		c.pitch = look.y
		c.call("_apply_free_look")
		await _settle(0.5)
		for gy in 11:
			for gx in 13:
				if ok:
					break
				var p := Vector2(vs.x * (0.12 + 0.76 * gx / 12.0), vs.y * (0.18 + 0.64 * gy / 10.0))
				var h: Dictionary = room.call("raycast", p)
				if h.is_empty():
					continue
				var rr: Dictionary = room.call("resolve", h)
				if str(rr["hotspot"]) == "stairs":
					room.call("_on_tap", p)
					ok = true
		if ok:
			break
		if OS.get_environment("CH4_DBG") != "":
			_dbg_hist("stairs")
	await _settle(0.5)
	if cam().current() == "bridge":
		c.yaw = 0.0
		c.pitch = 0.0
		c.call("_apply_free_look")
	return ok


## Walk to the view's zone, then go to the view (a player taps the object there).
func goto(id: String) -> void:
	var root: String = str(ROOT_OF.get(id, "bridge"))
	if root != _zone_root() or (id == "bridge" and cam().current() != "bridge"):
		await _walk_to_root(root)
	if id == "panel0" and cam().current() != "panel0":
		await _tap_pier()
	await view(id)


## From the lift bay: the pier wall under the bridge leads to Panel 0.
func _tap_pier() -> void:
	await view("lift")
	var ok := await _tap_landmark("bridge", "pier")
	if not ok:
		cam().yaw = 0.0
		cam().call("_apply_free_look")
	await _settle(0.8)
	if ok and cam().current() == "panel0":
		taps_ok += 1
		return
	taps_fallback += 1
	_log("  fallback: lift -> Panel 0 (the pier wall did not answer)")
	cam().go("panel0")
	await _settle(0.9)


## True when a failed tap is only because the model's GLB is not built yet (the room lists it in missing_models); a part
## that is missing from a built model is a wiring bug and is reported as a fallback.
func _unbuilt(why: String, model: String) -> bool:
	if why not in ["model missing", "part missing"]:
		return false
	var glb := model
	if ArrayHallData.LAYOUT.has(model):
		glb = str(ArrayHallData.LAYOUT[model][0])
	elif ArrayHallData.MOUNTED.has(model):
		glb = str(ArrayHallData.MOUNTED[model][0])
	elif model.begins_with("handwheel_"):
		glb = "handwheel"
	elif model.begins_with("mirror_tower_"):
		glb = "mirror_tower"
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
	# a new game begins in the lift (capture mode skips the intro: the room opens at the bridge)
	if intro_check and not quick:
		await _opening()
	if walk_only:
		await _walk_test()
		return
	cam().go("lift", true)
	await _settle(0.6)
	await shot("lift_arrival")
	if not quick:
		await _perf("lift")
		await shot("bay_chalk")
		await view("lift_chalk")
		await shot("lift_chalk")
		await view("bay_hero")
		await shot("bay_hero")
		await view("lift")
	await _early_gate()
	var guard := 0
	while not logic.is_complete() and guard < 2500:
		guard += 1
		if s["night_undone"]:
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
			if not ok or s["night_undone"]:
				break
			_steps_done += 1
			if do_continue and not _continue_done and logic.state["cage_open"]:
				_continue_done = true
				await _continue_check()
				s = logic.state
			elif do_continue and not _continue_mid_done and logic.state["reversing"] and int(logic.state["wheel"]) <= 5:
				_continue_mid_done = true
				await _continue_check("", true)
				s = logic.state
			elif reload_every > 0 and _steps_done % reload_every == 0:
				await _continue_check("mid-chapter after step %d (%s)" % [_steps_done, str(c[0])])
				s = logic.state
	if not logic.is_complete() and not s["night_undone"]:
		_log("✗ chapter not completed (stopped after %d planning rounds)" % guard)
	_finish()


## --walk: the zone changes alone (every root view and Panel 0 from the bridge, by taps), twice, in an odd order. Needs power
## for the catwalk and the island (the hall is powered by the solver's first steps).
func _walk_test() -> void:
	var s := logic.state
	for step in 3:
		ArrayHallSolver.step(logic, "leave_lens")
	await _settle(0.5)
	_log("power %s" % ["on" if s["power"] else "OFF"])
	if OS.get_environment("CH4_DBG") != "":
		var vs := get_viewport().get_visible_rect().size
		for gx in [0.3, 0.45, 0.5, 0.55, 0.7]:
			for gy in [0.2, 0.4, 0.6, 0.8]:
				var p2 := Vector2(vs.x * gx, vs.y * gy)
				var h2: Dictionary = room.call("raycast", p2)
				if h2.is_empty():
					continue
				var r2: Dictionary = room.call("resolve", h2)
				_log("  DBG centre-ish %s -> %s/%s/%s" % [str(p2), r2["model"], r2["hotspot"], r2.get("part", "")])
	for id in ["lift", "panel0", "apse", "booth", "watch", "catwalk", "island", "bridge", "island", "watch", "panel0", "bridge"]:
		var before := taps_fallback
		await goto(id)
		await wait_idle()
		_log("%s walk to %s: now at %s" % ["✓" if cam().current() == id and taps_fallback == before else "✗", id, cam().current()])
	_finish()


## The room's own opening (the lift sinks, the key turns, the gate folds open), shot twice.
func _opening() -> void:
	var t0 := Time.get_ticks_msec()
	room.call("play_opening_camera")
	await _settle(2.0)
	await shot("opening_descent")
	await _settle(6.4)
	await shot("opening_arrival")
	await wait_idle(30.0)
	_log("opening: %.1f s" % ((Time.get_ticks_msec() - t0) / 1000.0))


## Before power the carried key opens its own gate: Strand's the booth, Leyla's the watch room (the other zone stays shut).
func _early_gate() -> void:
	if _early_done:
		return
	_early_done = true
	var s := logic.state
	var strand: bool = s["entry"] == "strand"
	var item := "strand_key" if strand else "leyla_key"
	var target := "booth_gate" if strand else "watch_gate"
	var t := _target("use_item_on", [item, target])
	await goto(t[0])
	await wait_idle()
	if not quick:
		await shot("early_gate_" + target)
	await _do_use(["use_item_on", [item, target]], t)
	if not logic.state[target]:
		_log("✗ the %s did not open before power" % target)
	elif not quick:
		await shot("early_gate_open_" + target)
	# the watch room is open: the locker holds Leyla's note; the booth: the box is shut until the gears are right
	if not strand:
		await goto("locker_17")
		await _open_locker()
		var ok := await _do("take", ["locker_note"])
		if not ok:
			_log("✗ could not take Leyla's note from locker 17 before power")
		elif not quick:
			await shot("locker_note")
		if logic.state["secret"]:
			await _do("take", ["locker_parcel"])
	await view("lift")


func _open_locker() -> void:
	if logic.state["secret"] or not logic.state["taken"].get("locker_note", false):
		var door := node_of("lockers4", "IA_locker_17")
		if door != null and door.transform.basis.get_euler().y > -0.5:
			await tap("lockers4", "IA_locker_17")
			await _settle(1.0)


## The same "use an item" as _do, with the target already looked up.
func _do_use(c: Array, t: Array) -> void:
	logic.select_item(str(t[3]))
	await _settle(0.15)
	var before := _snap(logic)
	await tap(t[1], t[2])
	await _settle(0.25)
	await wait_idle()
	if _snap(logic) == before:
		var why := _hit(t[1], t[2])
		logic.callv(str(c[0]), c[1])
		taps_fallback += 1
		if not _count_missing(why, str(t[4]), "%s%s" % [c[0], str(c[1])], str(t[1])):
			_log("  fallback: %s%s (%s/%s, view %s, hit %s)" % [c[0], str(c[1]), t[1], t[2], cam().current(), why])
	else:
		taps_ok += 1
	logic.select_item("")


## A player quits here and taps Continue: the save is written, the scene freed and rebuilt from the save. The rebuilt scene
## must hold the same state, start on the bridge and show the same tappable parts. `label` != "" is the periodic check
## (--reload-every): it only reports a failure. `reversal` is the mid-reversal check (also reports a pass).
func _continue_check(label: String = "", reversal: bool = false) -> void:
	await wait_idle()
	await _settle(2.5) # cosmetic timers (the canister knocking back out, lamp sparks) are over: only the resting scene is compared
	var before := _snap(logic)
	var sig_before := await _stable_sig()
	var here := cam().current()
	if OS.get_environment("CH4_DBG") != "":
		var cn := node_of("post_station4", "IA_post_canister")
		if cn:
			_log("  DBG canister before reload: local %s, canister state '%s', parcel_sent %s" % [str(cn.transform.origin), str(logic.state["canister"]), str(logic.state["parcel_sent"])])
	var saved := GameState.save_now()
	room.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
	var loaded := saved and GameState.continue_saved()
	if not loaded:
		_log("✗ continue: the save could not be written or read back")
		GameState.logic = logic
	logic = GameState.logic
	GameState.events.connect(func(ev: Array[String]) -> void: _events.append_array(ev))
	_build_room()
	await get_tree().process_frame
	await get_tree().process_frame
	await _settle(1.2)
	await wait_idle()
	if OS.get_environment("CH4_DBG") != "":
		var cn2 := node_of("post_station4", "IA_post_canister")
		if cn2:
			_log("  DBG canister after reload: local %s" % str(cn2.transform.origin))
	var start := cam().current()
	var same := _snap(logic) == before
	var ok := loaded and same and start == str(room.call("start_view")) and not bool(room.call("_fresh_start"))
	var diff := ""
	if ok:
		var sig_after := await _stable_sig()
		if sig_after != sig_before:
			ok = false
			diff = _sig_diff(sig_before, sig_after)
	if label == "":
		_log(("✓ " if ok else "✗ ") + "continue%s: scene rebuilt from the save (state %s, opens at %s, %d tappable parts compared%s)" % [
			" mid-reversal (minute 03:1%d)" % int(logic.state["wheel"]) if reversal else " after the cage opened",
			"kept" if same else "DIFFERS", start, _sig_parts, diff])
		await shot("continue_" + ("reversal" if reversal else "cage"))
		if not ok:
			_reload_failed += 1
		await view(here if room.get("cam").views.has(here) else "bridge")
		return
	_reload_checks += 1
	if not ok:
		_reload_failed += 1
		_log("✗ continue %s: state %s, opens at %s%s" % [label, "kept" if same else "DIFFERS", start, diff])
	await view(here if room.get("cam").views.has(here) else "bridge")


## The signature once nothing moves any more.
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
	for v: String in ["lift", "bridge", "catwalk", "island", "apse", "booth", "watch"]:
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
	var copy := Plan.new()
	copy.from_dict(logic.to_dict())
	ArrayHallSolver.step(copy, choice)
	return copy.calls


## Evidence shots before a puzzle's first action, the kept echoes and the budget views before the reversal.
func _before(c: Array) -> void:
	var m := str(c[0])
	var key := m if m != "take" else "take:" + str(c[1][0])
	if (m == "lift_master") and not _echoes_done:
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
			await goto(v)
			await shot("evidence_" + v)


func _do(m: String, a: Array) -> bool:
	var t := _target(m, a)
	if t.is_empty():
		_log("  ✗ no tap known for %s%s" % [m, str(a)])
		logic.callv(m, a)
		taps_fallback += 1
		return true
	# a larger turn than one click is several taps
	var repeats := 1
	var step_args := a.duplicate()
	if m in ["turn_keeper", "turn_post_dial", "turn_post_number", "turn_feed"] and absi(int(a[0])) > 1:
		repeats = absi(int(a[0]))
		step_args = [signi(int(a[0]))]
		t = _target(m, step_args)
	if m == "take" and str(a[0]).begins_with("locker_"):
		await goto(str(t[0]))
		await _open_locker()
	for _k in repeats:
		var ok := await _do_one(m, step_args, t)
		if not ok:
			return false
	return true


func _do_one(m: String, a: Array, t: Array) -> bool:
	var label := "%s%s" % [m, str(a)]
	await goto(t[0])
	await wait_idle()
	if str(t[3]) != "":
		logic.select_item(t[3]) # a tap on the inventory slot
		await _settle(0.15)
	var before := _snap(logic)
	var expect := _expected(m, a)
	var bias: Vector2 = t[5] if t.size() > 5 else Vector2(0.5, 0.5)
	await tap(t[1], t[2], bias)
	await _settle(0.25)
	await wait_idle()
	var now := _snap(logic)
	if str(t[3]) != "" and logic.selected == str(t[3]):
		logic.select_item("") # still in hand: put it away as a player would
	if now == expect:
		taps_ok += 1
		return true
	if now == before:
		var why := _hit(t[1], t[2])
		logic.callv(m, a)
		taps_fallback += 1
		if not _count_missing(why, t[4], label, str(t[1])):
			_log("  fallback: %s (%s/%s, view %s, hit %s)" % [label, t[1], t[2], cam().current(), why])
		await wait_idle()
		return true
	taps_fallback += 1
	_log("  ✗ the tap did something else: %s (%s/%s, view %s, hit %s)" % [label, t[1], t[2], cam().current(), _hit(t[1], t[2])])
	return false


func _milestones() -> void:
	for e in _events:
		if e.begins_with("solved:"):
			_log("✓ solved %s" % e.substr(7))
			_solved.append(e.substr(7))
			if not quick:
				await shot("solved_" + e.substr(7))
		elif e in ["hall_replays", "replay_on", "replay_off", "reversal_begins", "snap_back", "night_undone", "lights_rise",
				"strand_stays", "forty_second_rises", "parcel_sent", "forty_second_turns", "leyla_echo_lens", "tower_open",
				"power_on", "iris_open", "cage_open", "box_open", "pawl_fitted"] \
				or e.begins_with("wound:") or e.begins_with("echo_released"):
			if not e.begins_with("wound:") or not quick:
				_log("  event %s" % e)
	_events.clear()


## The four kept echoes: while the hall replays (both paths) or, on the take path, while holding the crystal lens.
func _release_echoes() -> void:
	var places := {"tech_panel": "panel0", "tech_wheels": "bridge", "clerk_post": "watch", "leyla_lift": "lift_chalk"}
	for id: String in ArrayHallLogic.ECHOES:
		if (logic.state["echoes"] as Array).has(id):
			continue
		var visible_now := logic.echo_visible(id)
		var holding := false
		if not visible_now and logic.has_item("crystal_lens"):
			logic.select_item("crystal_lens")
			holding = true
		await goto(places[id])
		await _settle(0.8)
		var figure := ""
		for fid: String in (ArrayHallData.ECHOES[id] as Array)[1]:
			figure = fid
			break
		var n := node_of("echo_" + figure, "")
		if not quick:
			await shot("echo_" + id)
		var before := (logic.state["echoes"] as Array).size()
		if n and n.is_visible_in_tree():
			room.call("_on_tap", _echo_point(n))
			await _settle(0.5)
		if (logic.state["echoes"] as Array).size() > before:
			taps_ok += 1
			_log("✓ echo %s released" % id)
		else:
			taps_fallback += 1
			var why := "echo model missing" if n == null else ("hidden in this view (visible %s, culled %s)" % [str(n.is_visible_in_tree()),
				str(n.get_meta("culled", false))])
			_log("  fallback: echo %s (view %s, %s)" % [id, cam().current(), why])
			logic.release_echo(id)
		if holding:
			logic.select_item("")
		await wait_idle()


func _echo_point(n: Node3D) -> Vector2:
	var p := n.global_position + Vector3(0, 0.85, 0)
	return cam().unproject_position(p) if not cam().is_position_behind(p) else Vector2(-100, -100)


func _finale() -> void:
	if not quick:
		# the rise (41 lights through the oculus, the board going out) is a cinematic: a frame in each of its four camera moves
		for t: float in [3.0, 4.6, 5.4, 4.5]:
			await _settle(t)
			await shot("rise")
	await wait_idle(90.0)
	var hud: Node = room.get("hud")
	var w := 0
	while w < 160 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
	await shot("finale_choice")
	var ending := logic.ending_id()
	_log(("✓ " if ending == _expected_ending() else "✗ ") + "ending %s (expected %s)" % [ending, _expected_ending()])
	hud.call("_close_overlay")
	if not quick:
		await _perf("finale")
	room.set("_ending", false)
	logic.choose_ending(choice) # the choice overlay's button
	await _settle(2.5)
	await shot("chapter_complete")
	_log(("✓ " if logic.is_complete() else "✗ ") + "finale: %s -> chapter complete; epilogue lines: %s" % [choice,
		str(logic.epilogue_keys())])


func _finish() -> void:
	_log("taps through the 3D scene: %d (%d zone walks), logic fallbacks: %d (%d of them for models not built yet)" % [taps_ok,
		_walks, taps_fallback, fallback_missing])
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
	_log("assisted taps (TapAssist moved the tap onto a nearby small part): %d" % int(room.get("assisted_taps")))
	var f := FileAccess.open(out_dir + "/playthrough_ch4_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SaveSystem.profile_path))
	var ok: bool = logic.state["complete"] and not report.any(func(l: String) -> bool: return l.begins_with("✗"))
	var qa_exit: int = 0 if ok and taps_fallback == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
