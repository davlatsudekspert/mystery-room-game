extends Node
## Runtime QA for Chapter 2: loads the real Archive scene and plays the chapter through simulated taps on the
## 3D parts (raycast → hotspot → logic), like a player. A step falls back to a direct logic call only when the
## tap did not work, and every fallback is reported with what the tap hit instead.
## Run: xvfb-run -a godot --path game res://qa/playthrough_ch2.tscn -- --out=<dir> [--lens=take|leave] [--lang=ru]
##        [--seed=N] [--no-continue] (skip the quit-and-Continue checks before P5, P8 and P12)
## A quick logic-flow run without screenshots: godot --headless --path game res://qa/playthrough_ch2.tscn -- …
##        [--legacy] play the 1.0 chapter exactly as an old save does (the default while EXPANSION_SCENE_READY is false)
##        [--expansion[=1|2]] play a NEW expansion game (docs/CHAPTER2_EXPANSION.md): the lower and upper floors are played
##        at LOGIC level (ArchiveSolver) until the scene has their hotspots; see the TODO(scene) marks below
## Exit code 0 = chapter completed with no failed step and no fallback.

## TODO(scene): set to true when the scene has the expansion's rooms and hotspots; the default run then plays a new
## expansion game, and the logic-level steps below are replaced by taps one by one.
const EXPANSION_SCENE_READY := false

var out_dir := "/tmp/ch2_playthrough"
var exp_stage := 0 # 0 = the 1.0 chapter, 1/2 = a new expansion game of that stage
var room: Node3D
var logic: ArchiveLogic
var report: Array[String] = []
var shot_n := 0
var taps_ok := 0
var taps_fallback := 0
var taps_under_hud := 0 # taps whose point lies under a HUD control (a finger would hit the HUD, not the room)
var lens_path := "leave"
var _continue := true # --no-continue: no quit-and-Continue checks
var _continue_checks := 0
var _continue_failed := 0
var _seen: Array[String] = [] # every logic event since the run began (a tap that only makes a sound is checked by it)


func _ready() -> void:
	GameState.variant_seed = 0 # canonical answers unless --seed=N (players get a random seed per game)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		if a.begins_with("--lang="):
			TranslationServer.set_locale(a.substr(7))
		if a.begins_with("--lens="):
			lens_path = a.substr(7)
		if a.begins_with("--seed="):
			GameState.variant_seed = int(a.substr(7)) # this game's own answers (docs/VARIANTS.md)
		if a == "--store":
			GameState.qa_no_tips = true # store screenshots: no tip captions
		if a == "--no-continue":
			_continue = false
		if a == "--legacy":
			exp_stage = -1 # forced
		if a == "--expansion":
			exp_stage = 2
		if a.begins_with("--expansion="):
			exp_stage = clampi(int(a.substr(12)), 1, 2)
	if exp_stage == 0 and EXPANSION_SCENE_READY:
		exp_stage = maxi(ArchiveLogic.EXPANSION_STAGE, 1)
	if exp_stage < 0:
		exp_stage = 0
	DirAccess.make_dir_recursive_absolute(out_dir)
	SaveSystem.save_path = "user://qa_ch2_save.json"
	SaveSystem.profile_path = "user://qa_ch2_profile.json"
	GameState.profile = {"choices": {"ch1_lens": "take_lens" if lens_path == "take" else "leave_lens", "ch1_shards": 5}}
	GameState.start_new("ch2")
	GameState.events.connect(func(ev: Array[String]) -> void: _seen.append_array(ev))
	logic = GameState.logic
	var al := logic as ArchiveLogic
	if exp_stage == 0:
		al.make_legacy() # the old flow, whatever EXPANSION_STAGE says: the crystals are in the booth case, the lamp works
	else:
		al.begin_expansion(exp_stage)
		al.setup_from_profile(GameState.profile.get("choices", {}))
		al.apply_seed(int(al.state["seed"]))
	var t0 := Time.get_ticks_msec()
	await _load_room()
	_log("scene load+build: %d ms (software renderer; phones differ)" % (Time.get_ticks_msec() - t0))
	_log("path: Ch1 lens %s, shards 5; chapter flow: %s" % [lens_path, "1.0 (legacy)" if exp_stage == 0 else "expansion stage %d (new floors at logic level)" % exp_stage])
	await _settle(1.2)
	await _perf("hall")
	await run()


# ====================================================================== helpers
func _load_room() -> void:
	room = (load("res://src/rooms/archive/archive.tscn") as PackedScene).instantiate()
	room.set("capture_mode", true)
	get_tree().root.add_child.call_deferred(room)
	await get_tree().process_frame
	await get_tree().process_frame


## A player quits here and taps Continue: the save is written, the room freed and rebuilt from the save. The rebuilt
## room must hold the same state, open at the hall and show every tappable part where it was. The run then goes on
## in the rebuilt room, so the rest of the chapter is also played after a Continue. The caller takes the new
## `logic` for its later steps.
func _continue_check(label: String) -> void:
	if not _continue:
		return
	await wait_idle()
	logic.select_item("")
	var before := _snap()
	var sig_before := await _stable_sig()
	var saved := GameState.save_now()
	room.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame
	var loaded := saved and GameState.continue_saved()
	if not loaded:
		GameState.logic = logic
	logic = GameState.logic
	await _load_room()
	await _settle(1.2)
	await wait_idle()
	var start := cam().current()
	var same := _snap() == before
	var sig_after := await _stable_sig()
	var ok := loaded and same and start == "hall" and sig_after == sig_before
	_continue_checks += 1
	if not ok:
		_continue_failed += 1
	_log("%s continue %s: room rebuilt from the save (%s, state %s, opens at %s, %d tappable parts %s)%s" % [
		"✓" if ok else "✗", label, "loaded" if loaded else "NOT LOADED", "kept" if same else "DIFFERS", start,
		sig_before.count("\n") + 1, "unchanged" if sig_after == sig_before else "CHANGED",
		"" if sig_after == sig_before else _sig_diff(sig_before, sig_after)])
	cam().go("hall", true)
	await _settle(0.5)
	await shot("continue_" + label)


## What the save holds, by value (a new game's typed arrays load back untyped: same values, same game).
func _snap() -> String:
	return JSON.stringify(logic.to_dict(), "", true)


## Every tappable part (own collider on, visible in the tree) with its position and orientation, in each area's
## root view, once nothing moves any more (the booth door and the locker swing for a while).
func _stable_sig() -> String:
	var sig := await _scene_sig()
	for _i in 12:
		await _settle(0.6)
		var again := await _scene_sig()
		if again == sig:
			return sig
		sig = again
	return sig


func _scene_sig() -> String:
	var lines: Array[String] = []
	var where: Array[String] = ["hall", "west"]
	if logic.state["booth_open"]:
		where.append("booth")
	for v in where:
		cam().go(v, true)
		await _settle(0.35)
		for n in room.find_children("*", "StaticBody3D", true, false):
			var b := n as StaticBody3D
			if b.collision_layer == 0 or not b.is_visible_in_tree() or str(b.get_meta("part", "")) == "":
				continue
			var o := b.global_position
			var x := b.global_transform.basis.x
			if str(b.get_meta("part")).begins_with("Shard_"):
				x = Vector3.ZERO # a Lumen shard lies at a random angle each time the room is built: only where it is counts
			lines.append("%s|%s|%d,%d,%d|%d,%d,%d" % [v, str(b.get_meta("part")), roundi(o.x * 100.0), roundi(o.y * 100.0),
				roundi(o.z * 100.0), roundi(x.x * 10.0), roundi(x.y * 10.0), roundi(x.z * 10.0)])
	cam().go("hall", true)
	lines.sort()
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
	return " | before only: %s | after only: %s" % [str(only_a.slice(0, 4)), str(only_b.slice(0, 4))]


## Report line, also printed at once so a long or stuck run shows how far it got.
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
	var rs := RenderingServer
	_log("perf[%s]: draw calls %d, primitives %d, objects %d" % [label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])


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


func view(id: String) -> void:
	cam().go(id)
	await _settle(0.9)


func busy() -> bool:
	return bool((room.get("hud") as Node).get("_busy")) or bool(room.get("_cinematic"))


func wait_idle(limit: float = 40.0) -> void:
	var t := 0.0
	while busy() and t < limit:
		await _settle(0.25)
		t += 0.25


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
		if not mi.is_visible_in_tree() and not own_only: # an own-bounds part may be invisible and still tappable (dial holes)
			continue
		var ab := mi.get_aabb()
		for k in 8:
			var wp := mi.global_transform * ab.get_endpoint(k)
			if cam().is_position_behind(wp):
				if own_only:
					return Rect2()
				continue # a whole model seen from close up: frame the part of it in front of the camera
			var sp := cam().unproject_position(wp)
			if first:
				r = Rect2(sp, Vector2.ZERO)
				first = false
			else:
				r = r.expand(sp)
	return r


func _tap_point(model: String, part: String, frac: Vector2) -> Vector2:
	var n := node_of(model, part)
	if n == null:
		return Vector2(-1, -1)
	var r := _rect(n, part != "" and not part.begins_with("Item_"))
	if r.size == Vector2.ZERO:
		return Vector2(-1, -1)
	var sp := r.get_center() + frac * r.size * 0.5
	var vs := get_viewport().get_visible_rect().size
	if sp.x < 0 or sp.y < 0 or sp.x > vs.x or sp.y > vs.y:
		return Vector2(-1, -1)
	if frac != Vector2.ZERO or not part.begins_with("IA_") or _resolves_to(sp, part):
		return sp
	# The middle of a part's bounds can be covered or empty (a deep drawer seen from above, a card behind a tab):
	# a player taps where the part is actually visible, so look for such a point, nearest the middle first.
	var best := sp
	var best_d := INF
	for gy in 7:
		for gx in 7:
			var p := r.position + r.size * Vector2(0.1 + 0.8 * gx / 6.0, 0.1 + 0.8 * gy / 6.0)
			if p.x < 0 or p.y < 0 or p.x > vs.x or p.y > vs.y:
				continue
			var d := p.distance_to(r.get_center())
			if d < best_d and _resolves_to(p, part):
				best = p
				best_d = d
	return best


func _resolves_to(sp: Vector2, part: String) -> bool:
	var h: Dictionary = room.call("raycast", sp)
	return not h.is_empty() and str(room.call("resolve", h)["part"]) == part


func tap(model: String, part: String, frac: Vector2 = Vector2.ZERO) -> void:
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return
	_note_hud(sp, "%s/%s" % [model, part])
	room.call("_on_tap", sp)
	await _settle(0.4)


## The solver's taps go straight to the room, so a control under the HUD would still "work" here. Count the taps a
## finger could not make: the point lies inside one of HUD.blocked_rects().
func _note_hud(sp: Vector2, what: String) -> void:
	var hud: Node = room.get("hud")
	if hud == null or not hud.has_method("blocked_rects"):
		return
	for r: Rect2 in hud.call("blocked_rects"):
		if r.has_point(sp):
			taps_under_hud += 1
			_log("  ! tap under the HUD: %s at %d,%d (view %s)" % [what, int(sp.x), int(sp.y), cam().current()])
			return


func _hit(model: String, part: String, frac: Vector2) -> String:
	if node_of(model, part) == null:
		return "part missing"
	var sp := _tap_point(model, part, frac)
	if sp.x < 0:
		return "off-screen/behind camera"
	var h: Dictionary = room.call("raycast", sp)
	if h.is_empty():
		return "nothing"
	var r: Dictionary = room.call("resolve", h)
	return "%s/%s/%s" % [r["model"], r["hotspot"], r["part"]]


## Tap a part; succeed only if `cond` becomes true. Otherwise apply `fallback` (a logic call) and report it.
func act(model: String, part: String, cond: Callable, fallback: Callable, label: String = "", frac: Vector2 = Vector2.ZERO) -> void:
	if not cond.call():
		await tap(model, part, frac)
		await _settle(0.25)
	if cond.call():
		taps_ok += 1
	else:
		var why := _hit(model, part, frac)
		fallback.call()
		taps_fallback += 1
		_log("  fallback: %s (%s/%s, view %s, hit %s)" % [label if label != "" else part, model, part, cam().current(), why])


func step(label: String, ok: bool) -> void:
	_log(("✓ " if ok else "✗ ") + label)


func use(item: String) -> void:
	logic.select_item(item)
	await _settle(0.15)


# ====================================================================== the chapter
func run() -> void:
	var s := logic.state
	var L := logic
	await shot("hall_start")
	await view("west")
	await shot("west_root")
	# P1 catalogue: drawer 04, divider 1–, card 17
	await view("catalogue")
	await shot("catalogue")
	await act("card_catalogue", "IA_cat_drawer_4", func() -> bool: return int(s["cat_drawer"]) == 4, func() -> void: L.open_cat_drawer(4), "drawer 04")
	await _settle(0.8)
	await act("card_catalogue", "IA_divider_1", func() -> bool: return int(s["cat_group"]) == 1, func() -> void: L.pick_divider(1), "divider 1–")
	await _settle(0.5)
	await shot("catalogue_drawer_open")
	await act("card_catalogue", "IA_card_7", func() -> bool: return s["card_shown"], func() -> void: L.pull_card(7), "card 17")
	await act("card_catalogue", "IA_card_7", func() -> bool: return L.has_item("index_card"), func() -> void: L.take("index_card"), "take index card")
	step("P1 catalogue 04 / 1– / 17 → index card", L.has_item("index_card"))
	# P2 compressor: this game's valve setting (canonical A 1, B 2, C 2), read off the gauge marks
	await view("hall")
	await view("compressor")
	await shot("compressor_rest")
	var want: Array = L.valve_solution()
	for i in 3:
		for _k in int(want[i]):
			var v0 := int(s["valves"][i])
			await act("compressor_panel", "IA_valve_" + "abc"[i], func() -> bool: return int(s["valves"][i]) != v0 or s["pressure_ok"],
				func() -> void: L.turn_valve(i, 1), "valve " + "ABC"[i])
	await _settle(1.0)
	await shot("compressor_pressure_ok")
	step("P2 valves %s → pressure" % "-".join(want.map(func(x: Variant) -> String: return str(x))), s["pressure_ok"])
	# P3 punch the request card
	await view("hall")
	await view("station")
	await act("tube_station", "IA_card_tray", func() -> bool: return L.has_item("blank_card"), func() -> void: L.take("tray_card"), "blank card")
	await view("desk")
	await view("punch")
	await use("blank_card")
	await act("card_punch", "IA_punch_slot", func() -> bool: return s["card_in_punch"], func() -> void: L.use_item_on("blank_card", "punch"), "card into punch")
	for i in 8:
		if int(L.punch_code()[i]) == 1:
			await act("card_punch", "IA_punch_key_%d" % i, func() -> bool: return int(s["punch_keys"][i]) == 1, func() -> void: L.toggle_punch_key(i), "key %d" % (i + 1))
	await shot("punch_keys")
	await act("card_punch", "IA_punch_lever", func() -> bool: return L.has_item("request_card"), func() -> void: L.pull_punch_lever(), "punch lever")
	step("P3 punch %s → request card" % "".join(L.punch_code().map(func(b: Variant) -> String: return str(int(b)))), L.has_item("request_card") and s["request_ok"])
	# P4 dispatch to the stacks
	await view("hall")
	await view("station")
	await use("request_card")
	await act("tube_station", "IA_send_port", func() -> bool: return s["canister"] != "", func() -> void: L.use_item_on("request_card", "send_port"), "card into canister")
	for _guard in 12:
		if not (int(s["dest"]) != ArchiveLogic.DEST_STACKS):
			break
		var d0 := int(s["dest"])
		await act("tube_station", "IA_dest_dial", func() -> bool: return int(s["dest"]) != d0, func() -> void: L.step_dest(1), "destination dial")
	await shot("station_ready")
	await act("tube_station", "IA_send_lever", func() -> bool: return s["file_delivered"], func() -> void: L.send_canister(), "send lever")
	await _settle(2.0)
	await shot("canister_flight")
	await wait_idle()
	await view("station")
	await act("tube_station", "IA_receive_tray", func() -> bool: return bool(room.get("visuals").get("tray_open")), func() -> void: room.get("visuals").set("tray_open", true), "open receive tray")
	await _settle(0.5)
	await shot("station_file")
	await act("tube_station", "Item_canister_file", func() -> bool: return L.has_item("personnel_file"), func() -> void: L.take("canister_file"), "take file")
	await act("tube_station", "Item_canister_key", func() -> bool: return L.has_item("locker_key"), func() -> void: L.take("canister_key"), "take key")
	step("P4 dispatch → file + locker key", L.has_item("personnel_file") and L.has_item("locker_key"))
	# P5 locker 9
	await _continue_check("p5")
	L = logic
	s = L.state
	await view("hall")
	await view("lockers")
	await use("locker_key")
	await act("lockers", "IA_locker_9", func() -> bool: return s["locker_open"], func() -> void: L.use_item_on("locker_key", "locker_9"), "key on locker 9")
	await _settle(1.0)
	await view("locker9")
	await shot("locker9_open")
	await act("lockers", "Item_locker_receiver", func() -> bool: return L.has_item("pocket_receiver"), func() -> void: L.take("locker_receiver"), "take receiver")
	step("P5 locker 9 → receiver", L.has_item("pocket_receiver"))
	# P6 hunt with the receiver
	await use("pocket_receiver")
	await view("hall")
	await shot("receiver_hall")
	await view("west")
	await view("grille")
	await shot("receiver_grille")
	await act("vent_grille", "IA_grille", func() -> bool: return s["grille_open"], func() -> void: L.open_hiding_place("grille"), "grille")
	await _settle(0.8)
	await act("vent_grille", "Item_grille_reel", func() -> bool: return L.has_item("tape_1996"), func() -> void: L.take("grille_reel"), "reel 1996")
	await view("hall")
	await view("stacks")
	await view("ledger")
	await act("stacks_shelving", "IA_ledger", func() -> bool: return s["ledger_open"], func() -> void: L.open_hiding_place("ledger"), "ledger")
	await _settle(0.9)
	await shot("ledger_open")
	await act("stacks_shelving", "Item_ledger_reel", func() -> bool: return L.has_item("tape_1997"), func() -> void: L.take("ledger_reel"), "reel 1997")
	await view("hall")
	await view("hatch")
	await act("floor_hatch", "IA_hatch", func() -> bool: return s["hatch_open"], func() -> void: L.open_hiding_place("hatch"), "hatch")
	await _settle(1.2)
	await shot("hatch_open")
	await act("floor_hatch", "Item_hatch_reel", func() -> bool: return L.has_item("tape_1998"), func() -> void: L.take("hatch_reel"), "reel 1998")
	L.select_item("")
	step("P6 receiver hunt → 3 reels", L.has_item("tape_1996") and L.has_item("tape_1997") and L.has_item("tape_1998"))
	# P7 tape deck at 4.75
	await view("hall")
	await view("desk")
	await view("deck")
	for _guard in 12:
		if not (int(s["deck_speed"]) != ArchiveLogic.SPEED_RIGHT):
			break
		var sp0 := int(s["deck_speed"])
		await act("tape_deck", "IA_speed", func() -> bool: return int(s["deck_speed"]) != sp0, func() -> void: L.step_speed(1), "speed knob")
	for tape: String in ["tape_1996", "tape_1997", "tape_1998"]:
		await use(tape)
		await act("tape_deck", "", func() -> bool: return s["deck_tape"] == tape, func() -> void: L.use_item_on(tape, "deck"), "load " + tape)
		await act("tape_deck", "IA_play", func() -> bool: return (s["clicks_heard"] as Array).has(tape), func() -> void: L.play_tape(), "play " + tape)
		await _settle(3.0)
		await shot("deck_" + tape)
		await _settle(9.0)
	step("P7 three reels at 4.75 → clicks %s" % ", ".join((s["v_clicks"] as Array).map(func(c: Variant) -> String: return str(int(c)))), (s["clicks_heard"] as Array).size() == 3)
	# N1 Warm Wall, the Pump Room's N2, the Night Cell's N3 and the Cold Store's N4-N6 by real taps in the scene (hall east wall,
	# service door, mallet, manifold, pipe board, cell door, light table, cold door, cranks, frost window, chest).
	if logic.exp_active():
		await _n1_n2_taps()
		await _n3_n6_taps()
		step("N3-N6 lower floor by taps → chest open, crystals taken", logic.state["chest_open"] and L.has_item("crystal_blank_1") and L.has_item("crystal_blank_2"))
		await _back_to_hall()
		await _continue_check("lower")
		L = logic
		s = L.state
	# P8 booth dial 2-8-5
	await _continue_check("p8")
	L = logic
	s = L.state
	await view("hall")
	await view("booth_door")
	await view("dial")
	await shot("dial")
	for ch in L.booth_code():
		var d := int(ch)
		var n0 := str(s["dial_input"]).length()
		await act("booth_door", "IA_dial_hole_%d" % d, func() -> bool: return str(s["dial_input"]).length() != n0 or s["booth_open"],
			func() -> void: L.dial_digit(d), "dial %d" % d)
		await _settle(0.9)
	await wait_idle()
	await shot("booth_open")
	step("P8 dial %s → booth open" % L.booth_code(), s["booth_open"])
	# P9 splice by shadow length
	await view("booth")
	await shot("booth_root")
	await view("splicer")
	await shot("splicer_loose")
	for slot in 4:
		var f: int = int(L.splice_order()[slot])
		await act("film_splicer", "IA_frame_%d" % f, func() -> bool: return int(room.get("_held_frame")) == f or int(s["splice"][slot]) == f,
			func() -> void: room.set("_held_frame", f), "pick strip %d" % f)
		await act("film_splicer", "IA_slot_%d" % slot, func() -> bool: return int(s["splice"][slot]) == f, func() -> void: L.splice_put(f, slot), "slot %d" % slot)
	await _settle(0.8)
	await shot("splicer_done")
	await act("film_splicer", "Item_splicer_reel", func() -> bool: return L.has_item("film_reel"), func() -> void: L.take("splicer_reel"), "take film reel")
	step("P9 splice %s → reel" % " ".join(L.splice_order().map(func(f: Variant) -> String: return "f%d" % int(f))), L.has_item("film_reel"))
	# N7-N10 upper floor and the projector lamp (G2): by taps through the book lift, the Gallery, the Plate Room, the Office
	if logic.exp_stage() >= 2:
		await _n7_n10_taps()
		step("N7-N10 upper floor (taps) → projector lamp fitted", logic.state["lamp_ok"] and logic.state["print_ok"] and logic.state["cab_open"])
		await _back_to_hall()
	# P10 project, focus
	await view("projector")
	await use("film_reel")
	# with the reel selected, a tap anywhere on the projector threads it; the lever is the clearest spot in this view
	await act("film_projector", "IA_run_lever", func() -> bool: return s["reel_on_projector"], func() -> void: L.use_item_on("film_reel", "projector"), "thread reel")
	await act("film_projector", "IA_run_lever", func() -> bool: return s["projector_on"], func() -> void: L.toggle_projector(), "run lever")
	await _settle(4.0)
	await shot("film_frame")
	await _settle(14.0)
	await shot("film_sign_blurred")
	await wait_idle(60.0)
	await view("projector")
	for _guard in 12:
		if not (int(s["focus"]) != L.focus_sharp()):
			break
		var f0 := int(s["focus"])
		await act("film_projector", "IA_focus_ring", func() -> bool: return int(s["focus"]) != f0, func() -> void: L.turn_focus(1), "focus ring")
	step("P10 film seen, focus %d" % L.focus_sharp(), s["film_seen"] and L.is_sharp())
	# crystals from the lens case
	await view("booth")
	await view("lens_case")
	await act("lens_case", "IA_case_lid", func() -> bool: return bool(room.get("visuals").get("case_open")), func() -> void: room.get("visuals").set("case_open", true), "open lens case")
	await _settle(0.8)
	await shot("lens_case_open")
	if L.exp_active():
		# the new game's crystals came from the Cold Store chest (tapped in _n3_n6_taps), not from this case
		step("crystals from the Cold Store chest in the bag", L.has_item("crystal_blank_1") and L.has_item("crystal_blank_2"))
	else:
		await act("lens_case", "Item_case_crystal_1", func() -> bool: return L.has_item("crystal_blank_1"), func() -> void: L.take("case_crystal_1"), "crystal 1")
		await act("lens_case", "Item_case_crystal_2", func() -> bool: return L.has_item("crystal_blank_2"), func() -> void: L.take("case_crystal_2"), "crystal 2")
	# P11 record the sign at the screen socket
	await view("hall")
	await view("west")
	await view("screen")
	await shot("screen_sign_sharp")
	await view("socket")
	await use("crystal_blank_1")
	await act("projection_screen", "IA_screen_socket", func() -> bool: return s["sign_recorded"], func() -> void: L.use_item_on("crystal_blank_1", "screen_socket"), "blank crystal in socket")
	await _settle(1.0)
	await shot("socket_recorded")
	await act("projection_screen", "IA_screen_socket", func() -> bool: return L.has_item("crystal_sign"), func() -> void: L.take_from_socket(), "take sign crystal")
	step("P11 sign recorded", s["sign_recorded"] and L.has_item("crystal_sign"))
	# P11b (leave path): record Strand's mark with the slide projector
	if not s["has_lens"]:
		await view("hall")
		await view("booth_door")
		await view("booth")
		await view("projector")
		await act("film_projector", "IA_run_lever", func() -> bool: return not s["projector_on"], func() -> void: L.toggle_projector(), "projector off")
		await view("slides")
		await act("slide_cabinet", "IA_slide_drawer_2", func() -> bool: return int(s["slide_drawer"]) == 2, func() -> void: L.open_slide_drawer(2), "drawer ✦")
		await _settle(0.6)
		await shot("slides_drawer_open")
		await act("slide_cabinet", "Item_slide_mark", func() -> bool: return L.has_item("emblem_slide"), func() -> void: L.take("slide_mark"), "take slide")
		await view("slide_projector")
		await use("emblem_slide")
		await act("slide_projector", "IA_slide_gate", func() -> bool: return s["slide_in"], func() -> void: L.use_item_on("emblem_slide", "slide_projector"), "slide into gate")
		for _guard in 12:
			if not (int(s["slide_rot"]) % 2 != 0):
				break
			var r0 := int(s["slide_rot"])
			await act("slide_projector", "IA_slide_rot", func() -> bool: return int(s["slide_rot"]) != r0, func() -> void: L.rotate_slide(), "rotate slide")
		await act("slide_projector", "IA_slide_lamp", func() -> bool: return s["slide_on"], func() -> void: L.toggle_slide_lamp(), "slide lamp")
		await view("hall")
		await view("west")
		await view("screen")
		await shot("screen_mark")
		await view("socket")
		await use("crystal_blank_2")
		await act("projection_screen", "IA_screen_socket", func() -> bool: return s["mark_recorded"], func() -> void: L.use_item_on("crystal_blank_2", "screen_socket"), "second blank in socket")
		await act("projection_screen", "IA_screen_socket", func() -> bool: return L.has_item("crystal_mark"), func() -> void: L.take_from_socket(), "take mark crystal")
		step("P11b mark recorded", s["mark_recorded"])
	# optional echoes: hold a crystal and tap each one
	await view("hall")
	await use("crystal_sign")
	for id: String in ["stacks", "catalogue"]:
		var echo := node_of("echo_" + id, "")
		if echo:
			await view("west")
			await shot("echo_" + id)
			await act("echo_" + id, "", func() -> bool: return (s["echoes"] as Array).has(id), func() -> void: L.release_echo(id), "echo " + id)
	# P12 dual light lock
	await _continue_check("p12")
	L = logic
	s = L.state
	var mark := "crystal_lens" if s["has_lens"] else "crystal_mark"
	await view("hall")
	await view("vault")
	await shot("vault_closed")
	await view("vault_ports")
	await use(mark)
	await act("vault_door", "IA_port_left", func() -> bool: return s["port_left"] == mark, func() -> void: L.use_item_on(mark, "port_left"), "mark crystal left")
	await use("crystal_sign")
	await act("vault_door", "IA_port_right", func() -> bool: return s["port_right"] == "crystal_sign", func() -> void: L.use_item_on("crystal_sign", "port_right"), "sign crystal right")
	await shot("vault_ports_filled")
	for _guard in 12:
		if not (int(s["rot_left"]) % 4 != 0):
			break
		var a0 := int(s["rot_left"])
		await act("vault_door", "IA_collar_left", func() -> bool: return int(s["rot_left"]) != a0, func() -> void: L.turn_collar("rot_left"), "left collar")
	for _guard in 12:
		if not (int(s["rot_right"]) != L.vault_rot_target()):
			break
		var b0 := int(s["rot_right"])
		await act("vault_door", "IA_collar_right", func() -> bool: return int(s["rot_right"]) != b0, func() -> void: L.turn_collar("rot_right"), "right collar")
	for _guard in 12:
		if not (int(s["zoom_right"]) != L.vault_zoom_target() and not s["vault_unlocked"]):
			break
		var z0 := int(s["zoom_right"])
		await act("vault_door", "IA_zoom_right", func() -> bool: return int(s["zoom_right"]) != z0, func() -> void: L.turn_collar("zoom_right"), "zoom collar")
	await _settle(1.4)
	await shot("vault_overlay_locked_in")
	step("P12 overlay → vault unlocked", s["vault_unlocked"])
	await view("vault")
	for _i in ArchiveLogic.WHEEL_TURNS:
		var w0 := int(s["wheel"])
		await act("vault_door", "IA_vault_handle", func() -> bool: return int(s["wheel"]) != w0 or s["vault_open"], func() -> void: L.turn_wheel(), "vault wheel")
		await _settle(0.6)
	await _settle(3.5)
	await shot("vault_opening")
	var hud: Node = room.get("hud")
	var w := 0
	while w < 160 and hud.get("_overlay") == null:
		w += 1
		await _settle(0.25)
		if w == 18:
			await shot("vault_reel")
		if w == 38:
			await shot("vault_reel_42nd")
	await shot("finale_choice")
	# both keys get played across the two paths: Strand's on the take path, Leyla's on the leave path
	var key := "strand_key" if lens_path == "take" else "leyla_key"
	hud.call("_close_overlay")
	L.choose_ending(key)
	step("Finale: %s → chapter complete" % key, s["complete"] and s["choice"] == key)
	# the cliffhanger (ArchiveTeaser): the lift shaft, the recorder on black, the Chapter 3 card
	var teaser: ArchiveTeaser = room.get("teaser")
	var saw_shaft := false
	var last_beat := ""
	w = 0
	while w < 240 and not (teaser.card_open() and teaser.running and _card_ready(teaser)):
		w += 1
		await _settle(0.25)
		if cam().current() == "shaft" and not saw_shaft:
			saw_shaft = true
			await _settle(2.6)
			await shot("cliffhanger_shaft")
		if w == 110:
			await shot("cliffhanger_recorder")
		if teaser.beat != last_beat:
			last_beat = teaser.beat
			if last_beat == "pit_fade":
				await _settle(1.4)
				await shot("cliffhanger_pit_fade")
			elif last_beat == "pit_figure":
				await _settle(1.6)
				await shot("cliffhanger_pit_figure")
			elif last_beat == "pit_second":
				var dm: Variant = teaser.get("_dark_mat")
				var guard := 0
				while guard < 600 and dm is StandardMaterial3D and (dm as StandardMaterial3D).albedo_color.a < 0.85:
					guard += 1
					await get_tree().process_frame
				await shot("cliffhanger_pit_second")
				await _perf("pit")
			elif last_beat == "pit_out":
				await _settle(0.35)
				await shot("cliffhanger_pit_out")
	await _settle(2.4)
	await shot("cliffhanger_ch3_card")
	step("Cliffhanger: lift shaft, recorder, Chapter 3 card (%s)" % ArchiveTeaser.card_state(), saw_shaft and teaser.card_open())
	teaser.leave()
	await _settle(2.5)
	await shot("chapter_complete")
	step("Chapter 3 card → chapter card", hud.get("_overlay") != null)
	var still := AudioManager.looping_sfx() # the cliffhanger's tape hiss must have stopped with the tape
	step("No sound effect left looping (%s)" % ("none" if still.is_empty() else ", ".join(still)), still.is_empty())
	_finish()


## Turn the free-look camera (a drag, as a player does) until a part is near the middle of the screen: the doors of the new
## rooms are on the side walls of the root views.
func face_part(model: String, part: String) -> void:
	var n := node_of(model, part)
	if n == null or not n is MeshInstance3D:
		return
	var mi := n as MeshInstance3D
	var target := mi.global_transform * mi.get_aabb().get_center()
	var c := cam()
	var centre := get_viewport().get_visible_rect().size * 0.5
	var best := INF
	var best_yaw := c.yaw
	var best_pitch := c.pitch
	for yaw in range(-180, 180, 10):
		for pitch in [-20.0, -10.0, 0.0, 10.0, 20.0]:
			c.yaw = float(yaw)
			c.pitch = pitch
			c.call("_apply_free_look")
			if c.is_position_behind(target):
				continue
			var d := c.unproject_position(target).distance_to(centre)
			if d < best:
				best = d
				best_yaw = float(yaw)
				best_pitch = pitch
	c.yaw = best_yaw
	c.pitch = best_pitch
	c.call("_apply_free_look")
	await _settle(0.4)


## Tap a part and wait up to `secs` for `cond` (a ride, a door that swings before the room changes); else fall back.
func act_wait(model: String, part: String, cond: Callable, fallback: Callable, label: String, secs: float = 4.0, frac: Vector2 = Vector2.ZERO) -> void:
	if not cond.call():
		await tap(model, part, frac)
		var t := 0.0
		while t < secs and not cond.call():
			await _settle(0.25)
			t += 0.25
	if cond.call():
		taps_ok += 1
	else:
		var why := _hit(model, part, frac)
		fallback.call()
		taps_fallback += 1
		_log("  fallback: %s (%s/%s, view %s, hit %s)" % [label, model, part, cam().current(), why])
		await _settle(1.0)


## A tap at a point in the 3D scene (a tap volume that has no mesh: a hook on the board).
func tap_world(pos: Vector3, label: String, cond: Callable, fallback: Callable) -> void:
	var sp := cam().unproject_position(pos)
	if not cond.call():
		_note_hud(sp, label)
		room.call("_on_tap", sp)
		await _settle(0.5)
	if cond.call():
		taps_ok += 1
	else:
		fallback.call()
		taps_fallback += 1
		_log("  fallback: %s (view %s, hit %s)" % [label, cam().current(), str(room.call("resolve", room.call("raycast", sp)))])


func _zone_pos(room_id: String, local: Vector3) -> Vector3:
	return ((room.get("zones") as ArchiveZones).zones[room_id]["root"] as Node3D).global_position + local


## N7 to N10 and G2 as a player taps them (docs/CHAPTER2_EXPANSION.md): the Pump Room's weights and the book lift, the Gallery
## (the wedge, the counter's slips, the roll-call board, the key), the Plate Room (strip, zoom, focus), the Director's Office
## (the cabinet's wheels, the lamp), the spiral stair down, and the lamp fitted to the booth projector (dead before).
func _n7_n10_taps() -> void:
	var L := logic
	var s := L.state
	var gal := room.get("zones") as ArchiveZones
	# the Pump Room by the hall's east door
	await view("hall")
	await view("east_south")
	await act_wait("service_door", "IA_service_door", func() -> bool: return s["room"] == "pump", func() -> void: L.enter_room("pump"), "service door")
	await wait_idle()
	await _settle(0.6)
	# N7: hang the weights that balance the plate, look at the gauge, press the lamp button in the cage
	await view("lift_door")
	await shot("n7_lift_door")
	await view("lift_weights")
	await shot("n7_weights_empty")
	var want := ArchiveExpData.weights_for(L.lift_load())
	for i in 4:
		if int(want[i]) == 1:
			await act("lift_weight_%d" % i, "", func() -> bool: return int(s["weights"][i]) == 1 or s["lift_ok"], func() -> void: L.n7_toggle_weight(i), "weight %d" % ArchiveExpData.WEIGHTS[i])
			await _settle(0.6)
	await shot("n7_weights_hung")
	step("N7 weights %s → balanced at load %d" % [str(want), L.lift_load()], s["lift_ok"])
	await view("lift_panel")
	await shot("n7_lift_panel")
	await act_wait("pump_book_lift_cage", "IA_btn_lamp", func() -> bool: return s["room"] == "gallery", func() -> void: L.n7_call(1); L.enter_room("gallery"), "lamp button", 8.0)
	await wait_idle()
	await _settle(1.0)
	await shot("gallery_arrival")
	await _perf("gallery")
	# the wedge: pull the pin, the ladder falls, the spiral stair is open
	await view("wedge")
	await shot("gallery_wedge")
	await act("gallery_stair_wedge", "IA_wedge_pin", func() -> bool: return s["wedge_out"], func() -> void: L.pull_wedge(), "wedge pin")
	await _settle(2.4)
	await shot("gallery_wedge_out")
	# the counter: open the middle drawer, take the slips (they are pinned on the board)
	await view("gallery")
	await view("counter")
	await act("gallery_room_gallery", "IA_counter_drawer_1", func() -> bool: return bool(gal.builder("gallery").get("_drawer_open")[1]), func() -> void: gal.builder("gallery").get("_drawer_open")[1] = true, "slips drawer")
	await _settle(0.6)
	await shot("gallery_drawer")
	await act("gallery_room_gallery", "Item_counter_slips", func() -> bool: return L.has_item("roll_slips"), func() -> void: L.take("counter_slips"), "take slips")
	# N8: hang every tag where this game's slips put it (tap the tag, then its hook)
	await view("gallery")
	await view("board")
	await shot("gallery_board_slips")
	var board_root := (room.get("models") as Dictionary)["gallery_roll_call_board"] as Node3D
	for h in 6:
		var t := int(s["v_board"][h])
		await act("gallery_roll_call_board", "IA_tag_%d" % t, func() -> bool: return int(gal.builder("gallery").get("_held")) == t or (s["board"] as Array).find(t) == h, func() -> void: gal.builder("gallery").set("_held", t), "tag %d" % t)
		await tap_world(board_root.global_position + Vector3(-1.0 + 0.4 * h, 1.72, 0.05), "hook %d" % (h + 1), func() -> bool: return int(s["board"][h]) == t, func() -> void: L.n8_hang(t, h))
		await _settle(0.4)
	await _settle(1.0)
	await shot("gallery_board_done")
	step("N8 board %s → every slip agrees" % str(s["v_board"]), s["board_ok"])
	await act("gallery_roll_call_board", "Item_board_key", func() -> bool: return L.has_item("pass_key"), func() -> void: L.take("board_key"), "take pass key")
	# the Plate Room (plain door), N9: the strip, zoom and focus
	await view("gallery")
	await face_part("gallery_room_gallery", "IA_door_plate")
	await act_wait("gallery_room_gallery", "IA_door_plate", func() -> bool: return s["room"] == "plate", func() -> void: L.enter_room("plate"), "plate door")
	await wait_idle()
	await _settle(0.8)
	await shot("plate_arrival")
	await view("enlarger")
	await shot("plate_enlarger")
	var strip_i := int(s["v_strip"])
	await act("plate_strip_%d" % strip_i, "", func() -> bool: return int(s["en_strip"]) == strip_i, func() -> void: L.n9_load_strip(strip_i), "strip %d" % (strip_i + 1))
	await _settle(0.6)
	for _g in 8:
		if int(s["en_zoom"]) == int(s["v_zoom"]):
			break
		var z0 := int(s["en_zoom"])
		await act("plate_enlarger", "IA_zoom_knob", func() -> bool: return int(s["en_zoom"]) != z0, func() -> void: L.n9_zoom(1), "zoom knob")
	await shot("plate_print_blurred")
	for _g in 12:
		if int(s["en_focus"]) == int(s["v_pfocus"]):
			break
		var f0 := int(s["en_focus"])
		await act("plate_enlarger", "IA_focus_ring", func() -> bool: return int(s["en_focus"]) != f0, func() -> void: L.n9_focus(1), "focus ring")
	await _settle(0.8)
	await shot("plate_print_sharp")
	step("N9 strip %d, zoom %d, focus %d → staff print" % [strip_i + 1, int(s["v_zoom"]) + 1, int(s["v_pfocus"]) + 1], s["print_ok"] and L.has_item("staff_print"))
	# the Gallery again, and the Office door with the key
	await view("plate")
	await face_part("plate_room_plate", "IA_door_gallery")
	await act_wait("plate_room_plate", "IA_door_gallery", func() -> bool: return s["room"] == "gallery", func() -> void: L.enter_room("gallery"), "plate door back")
	await wait_idle()
	await _settle(0.6)
	await view("gallery")
	await face_part("gallery_room_gallery", "IA_door_office")
	await act_wait("gallery_room_gallery", "IA_door_office", func() -> bool: return s["room"] == "office", func() -> void: L.enter_room("office"), "office door (pass key)")
	await wait_idle()
	await _settle(0.8)
	await shot("office_arrival")
	# N10: the four wheels, the doors, the lamp
	await view("cabinet")
	await shot("office_cabinet")
	for i in 4:
		for _g in 10:
			if int(s["cab_wheels"][i]) == int(s["v_digits"][i]) or s["cab_open"]:
				break
			var w0 := int(s["cab_wheels"][i])
			await act("office_strand_cabinet", "IA_digit_%d" % i, func() -> bool: return int(s["cab_wheels"][i]) != w0 or s["cab_open"], func() -> void: L.n10_turn_wheel(i), "wheel %d" % (i + 1))
	await _settle(1.2)
	await shot("office_cabinet_open")
	step("N10 wheels %s → cabinet open" % "".join(L.cabinet_digits().map(func(d: Variant) -> String: return str(int(d)))), s["cab_open"])
	await act("office_strand_cabinet", "Item_cabinet_lamp", func() -> bool: return L.has_item("projector_lamp"), func() -> void: L.take("cabinet_lamp"), "take lamp")
	# back down the spiral stair (the wedge is out): the Office door, the Gallery, the stairwell
	await view("office")
	await face_part("office_room_office", "IA_door_gallery")
	await act_wait("office_room_office", "IA_door_gallery", func() -> bool: return s["room"] == "gallery", func() -> void: L.enter_room("gallery"), "office door back")
	await wait_idle()
	await _settle(0.6)
	await view("wedge")
	await act_wait("gallery_room_gallery", "stair_in", func() -> bool: return s["room"] == "hall", func() -> void: L.enter_room("hall"), "spiral stair down", 6.0)
	await wait_idle()
	await _settle(0.6)
	# G2: the projector's lamp is dead until the spare is fitted
	await view("booth")
	await view("projector")
	var n0 := _seen.size()
	await act("film_projector", "IA_run_lever", func() -> bool: return _seen.slice(n0).has("lamp_dead"), func() -> void: L.toggle_projector(), "lever with a dead lamp")
	await shot("projector_lamp_dead")
	await use("projector_lamp")
	await act("film_projector", "IA_run_lever", func() -> bool: return s["lamp_ok"], func() -> void: L.use_item_on("projector_lamp", "projector"), "fit the lamp")
	await _settle(1.0)
	await shot("projector_lamp_fitted")
	step("G2 dead lamp, then the spare fitted", s["lamp_ok"])


## Walks the player back into the hall (logic room + scene) after steps that played other rooms at logic level.
func _back_to_hall() -> void:
	await wait_idle()
	if logic.state["room"] != "hall":
		logic.enter_room("hall")
		await _settle(0.8)
		await wait_idle()
	cam().go("hall", true)
	await _settle(0.4)


## N1 and N2 as a player taps them (docs/CHAPTER2_EXPANSION.md): the receiver at the east wall, the panel that hides the
## door, the dial, the service door, the Pump Room (mallet, probe tap, the manifold's valves).
func _n1_n2_taps() -> void:
	var L := logic
	var s := L.state
	var v := int(s["v_panel"])
	# N1: the receiver in hand, the needle at the east wall, the panel, the dial 0417, the door
	await use("pocket_receiver")
	await view("hall")
	await view("east_south")
	await shot("n1_east_wall")
	await view("east_panel_" + "abc"[v])
	await shot("n1_panel")
	await act("service_door", "IA_cover_panel", func() -> bool: return s["panel_found"], func() -> void: L.n1_open_panel(v), "panel " + "ABC"[v])
	L.select_item("")
	await _settle(1.0)
	await view("east_dial")
	await shot("n1_dial")
	for ch in "0417":
		var d := int(ch)
		var n0 := _seen.size()
		await act("service_door", "IA_dial_hole_%d" % d, func() -> bool: return _seen.slice(n0).any(func(e: String) -> bool: return e.begins_with("dial_n1:")),
			func() -> void: L.n1_dial(d), "dial %d" % d)
		await _settle(0.7)
	step("N1 receiver, panel %s, dial 0417 → service door" % "ABC"[v], s["pump_open"])
	await _settle(1.2)
	await shot("n1_door_open")
	await view("east_south")
	await act("service_door", "IA_service_door", func() -> bool: return s["room"] == "pump", func() -> void: L.enter_room("pump"), "service door")
	await _settle(1.0)
	await wait_idle()
	await shot("pump_arrival")
	await _perf("pump")
	# N2: the mallet from the bench, a probe on a pipe, the manifold's valves
	await view("bench")
	await shot("pump_bench")
	await act("pump_room_pump", "Item_pump_mallet", func() -> bool: return L.has_item("mallet"), func() -> void: L.take("pump_mallet"), "mallet")
	await view("pipes")
	await shot("pump_pipes_dead")
	var n0 := _seen.size()
	await act("pump_pipe_run", "pipe_edge_0", func() -> bool: return _seen.slice(n0).any(func(e: String) -> bool: return e.begins_with("tap:")),
		func() -> void: L.n2_tap_pipe(0), "mallet on pipe 1")
	await view("manifold")
	await shot("pump_manifold")
	var sol: Array = L.pipe_solution()
	for i: int in sol:
		await act("pump_manifold_plate", "IA_valve_%d" % i, func() -> bool: return int(s["pipes"][i]) == 1 or s["thawed"],
			func() -> void: L.n2_toggle_valve(i), "valve %d" % (i + 1))
		await _settle(0.5)
	await _settle(1.0)
	await shot("pump_manifold_open")
	await view("pipes")
	await shot("pump_pipes_flow")
	step("N2 valves %s → coil warm (thawed)" % ",".join(sol.map(func(x: Variant) -> String: return str(int(x) + 1))), s["thawed"])


## Aims the camera at a point of a room (a temporary root view of that room) so a point-tap can reach it. In zone coordinates.
func _aim(room_id: String, from: Vector3, to: Vector3, fov: float = 62.0) -> void:
	var zones: ArchiveZones = room.get("zones")
	zones.register(room_id, ["qa_aim"], {}, {}, {})
	var o := (zones.zones[room_id]["root"] as Node3D).global_position
	cam().add_view("qa_aim", o + from, o + to, fov, true)
	cam().go("qa_aim", true)
	await _settle(0.5)


## Taps a point in a room (zone coordinates) the way the stair was tapped: project it and send the tap to the room.
func _tap_at(room_id: String, at: Vector3, label: String) -> void:
	var zones: ArchiveZones = room.get("zones")
	var o := (zones.zones[room_id]["root"] as Node3D).global_position
	var guard := 0
	while cam().transitioning and guard < 30: # a tap during a camera move is ignored, as for a player
		guard += 1
		await _settle(0.1)
	var sp := cam().unproject_position(o + at)
	_note_hud(sp, label)
	room.call("_on_tap", sp)
	await _settle(0.5)


## Ends a stroll through a zone's exits: taps the exit door of `room_id` and waits for the fade to the next room.
func _leave(room_id: String, from: Vector3, to: Vector3, at: Vector3, want_room: String, label: String) -> void:
	var L := logic
	await wait_idle()
	await _aim(room_id, from, to)
	await _tap_at(room_id, at, label)
	await _settle(0.8)
	await wait_idle()
	if L.state["room"] == want_room:
		taps_ok += 1
	else:
		taps_fallback += 1
		_log("  fallback: %s (hit %s)" % [label, str(room.call("resolve", room.call("raycast", cam().unproject_position(cam().global_position))))])
		L.enter_room(want_room)
		await _settle(1.0)
		await wait_idle()


## N3 to N6 as a player taps them: the Cell door (M2), the cloth, the light table (buttons, tabs, a sheet drag), the cold door's
## wheels, the Cold Store's cranks (the carriages roll), the plan, the frost window (a finger wipe and band taps), the chest rings,
## the two crystals; then back out through the Cell and the Pump Room to the hall.
func _n3_n6_taps() -> void:
	var L := logic
	var s := L.state
	var zones: ArchiveZones = room.get("zones")
	var hud: Node = room.get("hud")
	# the Cell door: the first look (moment M2), then in
	await view("pump")
	await act("pump_room_pump", "IA_door_cell", func() -> bool: return cam().current() == "cell_door", func() -> void: cam().go("cell_door"), "Cell door view")
	await _settle(1.5)
	await shot("pump_cell_door")
	await wait_idle()
	await act("pump_room_pump", "IA_door_cell", func() -> bool: return s["room"] == "cell", func() -> void: L.enter_room("cell"), "Cell door")
	await _settle(1.0)
	await wait_idle()
	await shot("cell_arrival")
	await _perf("cell")
	# the diary and the slip on the desk, read and closed again
	await view("desk")
	await shot("cell_desk")
	await tap("cell_cell_diary", "IA_cell_diary")
	await _settle(0.5)
	await shot("cell_diary_read")
	hud.call("consume_back")
	await _settle(0.3)
	# the cloth by the kettle
	await view("shelf")
	await shot("cell_shelf")
	await act("cell_wipe_cloth", "", func() -> bool: return L.has_item("wipe_cloth"), func() -> void: L.take("cell_cloth"), "cloth")
	# N3: flips first (the flip buttons), then quarter turns (the turn buttons); one sheet also by its tab and a drag
	await view("light_table")
	await shot("cell_light_table_start")
	await _perf("light_table")
	var tgt: Array = s["v_sheet_target"]
	for i in 3:
		var before := int(s["sheets"][2 * i + 1])
		if before != int(tgt[2 * i + 1]):
			if i == 2:
				await act("cell_acetate_sheet_c", "IA_flip_tab_2", func() -> bool: return int(s["sheets"][5]) != before, func() -> void: L.n3_flip_sheet(2), "flip tab of sheet 3")
			else:
				await act("cell_light_table", "IA_flipbtn_%d" % i, func() -> bool: return int(s["sheets"][2 * i + 1]) != before, func() -> void: L.n3_flip_sheet(i), "flip button %d" % i)
	for i in 3:
		var guard := 0
		while int(s["sheets"][2 * i]) != int(tgt[2 * i]) and guard < 4 and not s["cell_digits_ok"]:
			guard += 1
			var r0 := int(s["sheets"][2 * i])
			if i == 2 and guard == 1:
				# a drag sideways on sheet 3 turns it (the room's drag hook, with the finger inside the sheet)
				var spd: Vector2 = _tap_point("cell_acetate_sheet_c", "IA_sheet_2", Vector2.ZERO)
				room.set("drag_pos", spd)
				var cap := bool(room.call("drag_part_started", "IA_sheet_2"))
				room.call("drag_part", Vector2(40, 0))
				room.call("drag_part", Vector2(40, 0))
				await _settle(0.5)
				if cap and int(s["sheets"][4]) != r0:
					taps_ok += 1
					continue
				taps_fallback += 1
				_log("  fallback: sheet 3 drag (captured %s)" % str(cap))
				L.n3_turn_sheet(2)
				continue
			await act("cell_light_table", "IA_turn_%d" % i, func() -> bool: return int(s["sheets"][2 * i]) != r0, func() -> void: L.n3_turn_sheet(i), "turn button %d" % i)
	await _settle(2.2)
	await shot("cell_light_table_solved")
	step("N3 light table → digits %d%d" % [int(s["v_glyph"][0]), int(s["v_glyph"][1])], s["cell_digits_ok"])
	# the cold door: the wheels (a first tap steps in to them), then the handle and the doorway
	await view("cold_door")
	await shot("cell_cold_door_closed")
	for i in 2:
		var want := int(s["v_glyph"][i])
		var guard := 0
		while int(s["cold_wheels"][i]) != want and guard < 10:
			guard += 1
			var w0 := int(s["cold_wheels"][i])
			await act("cell_cold_door", "IA_wheel_" + "ab"[i], func() -> bool: return int(s["cold_wheels"][i]) != w0 or cam().current() == "cold_wheels" and guard == 1 and i == 0,
				func() -> void: L.cold_wheel(i), "cold wheel %d" % (i + 1))
			await _settle(0.3)
		if i == 0:
			await shot("cell_cold_wheels")
	await _settle(2.0)
	await shot("cell_cold_door_open")
	step("N3 wheels %d%d → the cold door opens (the coil is warm)" % [int(s["v_glyph"][0]), int(s["v_glyph"][1])], s["cold_open"])
	await view("cold_door")
	await _tap_at("cell", Vector3(2.15, 1.0, 0.0), "cold doorway")
	await _settle(1.2)
	await wait_idle()
	if s["room"] == "cold":
		taps_ok += 1
	else:
		taps_fallback += 1
		_log("  fallback: cold doorway (view %s)" % cam().current())
		L.enter_room("cold")
		await _settle(1.0)
		await wait_idle()
	await shot("cold_arrival")
	await _perf("cold")
	# N4: the plan, then the cranks until the aisle opens
	await view("plan")
	await shot("cold_plan")
	await _tap_at("cold", Vector3(3.74, 1.55, 0.915), "plan plate")
	await _settle(0.6)
	await shot("cold_plan_zoom")
	hud.call("consume_back")
	await _settle(0.3)
	await view("cranks")
	await shot("cold_cranks_start")
	await _perf("cranks")
	var steps_done := 0
	while not s["aisle"] and steps_done < 12:
		var route := L.aisle_route_from_here()
		if route.is_empty():
			break
		steps_done += 1
		var k := int(route[0][0])
		var want_slot := int((s["aisle_pos"] as Array)[k]) + int(route[0][1])
		var tries := 0
		while int((s["aisle_pos"] as Array)[k]) != want_slot and tries < 3 and not s["aisle"]:
			tries += 1 # a crank that clunks turns the other way on the next tap (docs/CHAPTER2_EXPANSION.md N4)
			await tap("cold_carriage_%d" % (k + 1), "IA_crank_%d" % k)
			await _settle(0.4)
		if int((s["aisle_pos"] as Array)[k]) == want_slot or s["aisle"]:
			taps_ok += 1
		else:
			taps_fallback += 1
			_log("  fallback: crank %d (view %s, hit %s)" % [k + 1, cam().current(), _hit("cold_carriage_%d" % (k + 1), "IA_crank_%d" % k, Vector2.ZERO)])
			L.n4_crank(k, int(route[0][1]))
		await _wait_rolled()
		if steps_done == 1:
			await shot("cold_cranks_rolling")
	await _wait_rolled()
	await wait_idle()
	await _settle(2.0)
	await shot("cold_aisle_open")
	step("N4 cranks (%d) → the aisle opens, the chest stands in it" % steps_done, s["aisle"])
	# N5: a finger wipe over the first band (drag hook), band taps for the other two
	await view("frost")
	await shot("cold_frost_start")
	await _perf("frost")
	var win: Node3D = node_of("cold_frost_window", "")
	var band_pts: Array[Vector2] = []
	for y: float in [0.4, 0.0, -0.4]:
		band_pts.append(cam().unproject_position(win.to_global(Vector3(0, y, 0.02))))
	var left := cam().unproject_position(win.to_global(Vector3(-0.3, 0.4, 0.02)))
	var right := cam().unproject_position(win.to_global(Vector3(0.3, 0.4, 0.02)))
	room.set("drag_pos", left)
	var captured := bool(room.call("drag_part_started", "IA_frost"))
	for pass_i in 6: # back and forth, as a finger would
		for t in 10:
			var p := left.lerp(right, float(t) / 9.0) if pass_i % 2 == 0 else right.lerp(left, float(t) / 9.0)
			p.y += (pass_i - 2.5) * 16.0
			room.set("drag_pos", p)
			room.call("drag_part", Vector2(12, 0))
			await get_tree().process_frame
	await _settle(0.8)
	await shot("cold_frost_wiped_band0")
	if captured and int(s["wiped"][0]) == 1:
		taps_ok += 1
	else:
		taps_fallback += 1
		_log("  fallback: frost finger wipe (captured %s, band share %s)" % [str(captured), str(zones.builder("cold").call("_band_clear_share", 0))])
		L.n5_wipe(0)
	for b in [1, 2]:
		var bb: int = b
		var sp: Vector2 = band_pts[bb]
		_note_hud(sp, "frost band %d" % bb)
		room.call("_on_tap", sp)
		await _settle(0.8)
		if int(s["wiped"][bb]) == 1:
			taps_ok += 1
		else:
			taps_fallback += 1
			_log("  fallback: frost band %d tap" % bb)
			L.n5_wipe(bb)
	await _settle(1.5)
	await shot("cold_frost_done")
	step("N5 frost wiped (drag + taps) → signs %s" % ",".join((s["v_symbols"] as Array).map(func(v: Variant) -> String: return str(int(v)))), s["frost_seen"] and L.has_item("frost_sketch"))
	# N6: the rings by their shortest route, the lid, the two crystals
	await view("chest")
	await shot("cold_chest_closed")
	await _perf("chest")
	var presses := ArchiveExpData.ring_route(s["rings"], L.chest_target())
	for ring_i: int in presses:
		var rv := int(s["rings"][ring_i])
		await act("cold_cold_chest", "IA_ring_%d" % ring_i, func() -> bool: return int(s["rings"][ring_i]) != rv or s["chest_open"],
			func() -> void: L.n6_turn_ring(ring_i), "ring %d" % (ring_i + 1))
		await _settle(0.35)
	await _settle(1.8)
	await shot("cold_chest_open")
	step("N6 rings (%d presses) → the chest opens" % presses.size(), s["chest_open"])
	for k in 2:
		var spot := "case_crystal_%d" % (k + 1)
		var item := "crystal_blank_%d" % (k + 1)
		await act("cold_cold_chest", "Item_" + spot, func() -> bool: return L.has_item(item), func() -> void: L.take(spot), "crystal %d" % (k + 1))
	await shot("cold_chest_empty")
	# back out: the Cold Store door, the Cell's doorway, the Pump Room's stair
	await _leave("cold", Vector3(0.0, 1.5, 2.2), Vector3(-3.72, 1.1, 2.2), Vector3(-3.72, 1.1, 2.2), "cell", "cold exit")
	await _leave("cell", Vector3(0.0, 1.5, -1.1), Vector3(-2.15, 1.05, -1.1), Vector3(-2.15, 1.05, -1.1), "pump", "cell exit")
	await view("pump")
	var c := cam()
	c.yaw = 180.0 # turn round to the south wall: the stair up to the hall
	c.pitch = 0.0
	c.call("_apply_free_look")
	await _settle(0.4)
	var zp: Vector3 = ((room.get("zones") as ArchiveZones).zones["pump"]["root"] as Node3D).global_position + Vector3(-1.7, 1.2, 2.75)
	var sp := c.unproject_position(zp)
	_note_hud(sp, "pump stair")
	room.call("_on_tap", sp)
	await _settle(1.2)
	await wait_idle()
	if s["room"] == "hall":
		taps_ok += 1
	else:
		taps_fallback += 1
		_log("  fallback: pump stair (hit %s)" % str(room.call("resolve", room.call("raycast", sp))))
		L.enter_room("hall")
		await _settle(1.0)
		await wait_idle()


## Waits until every carriage of the Cold Store has come to rest.
func _wait_rolled() -> void:
	var b: Object = (room.get("zones") as ArchiveZones).builder("cold")
	var t := 0.0
	while b != null and int(b.get("_rolling")) > 0 and t < 12.0:
		await _settle(0.25)
		t += 0.25


## The Chapter 3 card has its buttons (the cliffhanger's last beat).
func _card_ready(teaser: ArchiveTeaser) -> bool:
	var root: Variant = teaser.get("_root")
	return root is Control and is_instance_valid(root) and not (root as Control).find_children("*", "Button", true, false).is_empty()


func _finish() -> void:
	_log("taps through the 3D scene: %d, logic fallbacks: %d" % [taps_ok, taps_fallback])
	_log("taps under a HUD control: %d (window %dx%d)" % [taps_under_hud, get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y])
	_log("continue checks: %d, failed %d%s" % [_continue_checks, _continue_failed, "" if _continue else " (--no-continue)"])
	var f := FileAccess.open(out_dir + "/playthrough_ch2_report.txt", FileAccess.WRITE)
	f.store_string("\n".join(report) + "\n")
	SaveSystem.delete_game()
	var ok: bool = logic.state["complete"] and not report.any(func(l: String) -> bool: return l.begins_with("✗"))
	var qa_exit: int = 0 if ok and taps_fallback == 0 else 1
	print("QA_DONE exit=%d" % qa_exit) # tools/qa_run.sh: the run finished even if the process then hangs on exit
	get_tree().quit(qa_exit)
